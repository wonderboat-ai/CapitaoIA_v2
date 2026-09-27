"""Teste de ponta a ponta da IA na nuvem nas telas de chat (Main e H2), com o Worker SIMULADO — não gasta cota.

Confere que a IA só entra quando a resposta local vem de um trecho do guia ('base'); que resposta pronta e SEM DADOS
não chamam a IA; que sem a CHAVE_APP no aparelho nada vai para a rede; que erro do proxy e "SEM DADOS" da IA mantêm a
resposta local; que link de fora (#q=) não gasta a cota e link de dentro do app usa a IA; que o indicador some ao fim;
e que o login não leva a chave do endereço para o ?next=.

    python -X utf8 testes/chat_ia.py        (sobe um servidor local próprio; precisa de internet para o React do unpkg)
"""
import functools
import http.server
import json
import os
import re
import sys
import threading
import urllib.parse

from playwright.sync_api import sync_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL_ARQ = re.search(r"var URL_PROXY = '([^']+)'", open(os.path.join(RAIZ, 'capitao-ia.js'), encoding='utf-8').read()).group(1)
SESSAO = "(() => { const n = Date.now(); localStorage.setItem('capitao.sessao.v1', JSON.stringify({ u: 'lucas', em: n, exp: n + 3600e3 })); })()"
MOBILE_UA = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Mobile Safari/537.36'
TEXTO_IA = 'Resposta simulada da IA: segure PARTIDA até o motor pegar.'
PRONTA = "() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0"


def mesmo_cliente():
    """capitao-ia.js (raiz) = integracoes/ia-cliente/capitao-ia.js, fora o comentário do topo e a linha da URL."""
    def corpo(p):
        s = open(os.path.join(RAIZ, p), encoding='utf-8').read()
        s = s[s.index('*/') + 2:]
        return re.sub(r"  var URL_PROXY = '[^']*';[^\n]*\n", '', s)
    return corpo('capitao-ia.js') == corpo('integracoes/ia-cliente/capitao-ia.js')


def main():
    class Quieto(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quieto, directory=RAIZ))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d/' % srv.server_address[1]
    res = []

    def ok(nome, cond, extra=''):
        res.append((nome, bool(cond), str(extra)[:300]))

    ok('capitao-ia.js da raiz é o mesmo cliente de integracoes/ia-cliente (só muda a URL)', mesmo_cliente())
    ok('URL do Worker no cliente publicado', URL_ARQ.startswith('https://capitao-ia.') and URL_ARQ.endswith('.workers.dev'), URL_ARQ)

    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel='msedge')
            for tela, movel, campo in (('H2-Home-Mobile', True, '#pergunta-m'), ('Main', False, '#pergunta')):
                ctx = b.new_context(viewport={'width': 390, 'height': 844} if movel else {'width': 1440, 'height': 900},
                                    user_agent=MOBILE_UA if movel else None, is_mobile=movel, has_touch=movel, service_workers='block')
                ctx.add_init_script(SESSAO)
                pg = ctx.new_page()
                erros = []
                pg.on('pageerror', lambda e: erros.append(str(e)[:200]))
                estado = {'pedidos': [], 'modo': 'ok'}

                def rota(route):
                    req = route.request
                    cab = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type, X-Capitao-Chave', 'Access-Control-Allow-Methods': 'POST, OPTIONS'}
                    if req.method == 'OPTIONS':
                        return route.fulfill(status=204, headers=cab)
                    estado['pedidos'].append(json.loads(req.post_data or '{}'))
                    if estado['modo'] == 'erro':
                        return route.fulfill(status=503, content_type='application/json', headers=cab, body='{"erro":"cota"}')
                    texto = ('SEM DADOS — os trechos não respondem.\nFonte: nenhuma — os trechos e a leitura enviados pelo app não respondem a pergunta'
                             if estado['modo'] == 'semdados' else TEXTO_IA + '\nFonte: Guia de bordo (DEMO) — Gerador Onan · 2 · Ligar')
                    return route.fulfill(status=200, content_type='application/json', headers=cab,
                                         body=json.dumps({'texto': texto, 'provedor': 'Workers AI', 'modelo': '@cf/meta/llama-3.3-70b-instruct-fp8-fast', 'parou': 'fim'}))
                pg.route(URL_ARQ.rstrip('/') + '**', rota)

                def espera_resposta():
                    try:
                        pg.wait_for_function("() => /Fonte:/.test(document.body.innerText)", timeout=15000)
                        pg.wait_for_function("() => !document.querySelector('[data-capitao-pensando]')", timeout=10000)
                    except Exception:
                        pass
                    pg.wait_for_timeout(600)

                def prepara(chave):
                    pg.goto(base + 'README.md')
                    pg.evaluate("(c) => { if (c) localStorage.setItem('capitao.ia.chave.v1', 'chave-de-teste'); else localStorage.removeItem('capitao.ia.chave.v1'); }", chave)

                def digita(q, chave=True, modo='ok'):
                    """Pergunta digitada no campo do chat (o caminho normal)."""
                    estado['modo'] = modo
                    prepara(chave)
                    antes = len(estado['pedidos'])
                    pg.goto(base + tela + '.dc.html')
                    pg.wait_for_function(PRONTA, timeout=20000)
                    pg.wait_for_selector(campo, timeout=15000)
                    pg.fill(campo, q)
                    pg.press(campo, 'Enter')
                    espera_resposta()
                    return pg.evaluate('() => document.body.innerText'), len(estado['pedidos']) - antes, pg.query_selector('[data-capitao-pensando]') is None

                def por_link(q, interno):
                    """Pergunta por link #q=: de fora (sem referrer) ou de dentro do app (referrer da mesma origem)."""
                    estado['modo'] = 'ok'
                    prepara(True)
                    antes = len(estado['pedidos'])
                    alvo = base + tela + '.dc.html#q=' + urllib.parse.quote(q)
                    if interno:
                        pg.evaluate('(u) => { location.href = u; }', alvo)  # sai do README.md (mesma origem) → referrer interno
                        pg.wait_for_url(re.compile(re.escape(tela)), timeout=15000)
                    else:
                        pg.goto(alvo)  # abrir o link direto, sem referrer (como vindo de outro site)
                    pg.wait_for_function(PRONTA, timeout=20000)
                    espera_resposta()
                    return pg.evaluate('() => document.body.innerText'), len(estado['pedidos']) - antes

                t, n, livre = digita('como ligar o gerador?')
                ok(tela + ': resposta do guia (base) chama a IA 1 vez', n == 1, 'pedidos=%d' % n)
                ok(tela + ': mensagem trocada pela resposta da IA, com a fonte "IA na nuvem (Workers AI · llama-3.3-70b-instruct-fp8-fast)"', TEXTO_IA in t and 'Fonte: IA na nuvem (Workers AI · llama-3.3-70b-instruct-fp8-fast)' in t, t[-300:])
                ok(tela + ': indicador "consultando" some depois da resposta da IA', livre)
                ped = estado['pedidos'][-1] if estado['pedidos'] else {}
                ok(tela + ': pedido leva a pergunta e trechos do guia do gerador', ped.get('pergunta') == 'como ligar o gerador?' and ped.get('trechos') and 'Gerador' in ped['trechos'][0].get('fonte', ''), json.dumps(ped, ensure_ascii=False)[:200])
                t, n, _ = digita('quantas horas tem o gerador')
                ok(tela + ': resposta pronta (não base) não chama a IA', n == 0 and TEXTO_IA not in t, 'pedidos=%d' % n)
                t, n, _ = digita('qual o calado do barco?')
                ok(tela + ': SEM DADOS local não chama a IA', n == 0 and 'SEM DADOS' in t, 'pedidos=%d' % n)
                t, n, _ = digita('como ligar o gerador?', chave=False)
                ok(tela + ': sem a CHAVE_APP no aparelho nada vai para a rede', n == 0 and TEXTO_IA not in t and 'PARTIDA' in t, 'pedidos=%d' % n)
                t, n, livre = digita('como ligar o gerador?', modo='erro')
                ok(tela + ': erro do proxy mantém a resposta local (e o indicador some)', n == 1 and TEXTO_IA not in t and 'PARTIDA' in t and livre, 'pedidos=%d' % n)
                t, n, _ = digita('como ligar o gerador?', modo='semdados')
                ok(tela + ': "SEM DADOS" da IA mantém o trecho local com a fonte', n == 1 and 'PARTIDA' in t and 'Fonte: nenhuma' not in t, 'pedidos=%d' % n)
                t, n = por_link('como ligar o gerador?', interno=False)
                ok(tela + ': link de fora (#q=, sem referrer) não chama a IA', n == 0 and 'PARTIDA' in t, 'pedidos=%d' % n)
                t, n = por_link('como ligar o gerador?', interno=True)
                ok(tela + ': link de dentro do app (#q=, referrer da mesma origem) usa a IA', n == 1 and TEXTO_IA in t, 'pedidos=%d' % n)
                ok(tela + ': sem erro de script', not erros, '; '.join(erros))
                ctx.close()
            # Sem sessão: o login não pode levar nada do #ia= para o ?next= (vai ao servidor e ao histórico).
            ctx = b.new_context(service_workers='block')
            pg = ctx.new_page()
            pg.goto(base + 'Main.dc.html#ia=ativar&q=gerador')
            pg.wait_for_timeout(1500)
            ok('login: #ia= não vai para o ?next= (o #q= continua)', 'login.html' in pg.url and 'ia%3D' not in pg.url and 'q%3Dgerador' in pg.url, pg.url.replace(base, '/'))
            ctx.close()
            b.close()
    finally:
        srv.shutdown()
    falhas = [r for r in res if not r[1]]
    for nome, bom, extra in res:
        print(('OK    ' if bom else 'FALHA ') + nome + ('' if bom else '  → ' + extra))
    print('%d conferências · %d falhas' % (len(res), len(falhas)))
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
