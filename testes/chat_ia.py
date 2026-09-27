"""Teste de ponta a ponta da IA na nuvem nas telas de chat (Main e H2), com o Worker SIMULADO — não gasta cota.

Confere que a IA entra quando a resposta local não basta (SEM DADOS, trecho do guia, pergunta sobre o app — "Oque você faz?")
e nunca em resposta pronta ou só num "oi"; que o pedido leva a ficha de bordo (sem coordenadas) e o histórico da conversa;
que sem a CHAVE_APP no aparelho nada vai para a rede e a linha da fonte diz por quê (com o botão "Ativar IA na nuvem");
que erro do proxy mantém a resposta local com o motivo; que "SEM DADOS" da IA mantém o trecho do guia mas troca o SEM DADOS
genérico; que a resposta entra logo depois da pergunta dela; que na CONVERSA por voz a IA responde e a resposta dela é a
falada; que link de fora (#q=) não gasta a cota e link de dentro do app usa a IA; que o indicador some ao fim;
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
FONTE_IA = 'Guia de bordo (DEMO) — Gerador Onan · 2 · Ligar · via IA na nuvem (Workers AI · llama-3.3-70b-instruct-fp8-fast)'
PRONTA = "() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0"
CONVERSA = '[aria-label="Conversa contínua por voz — sem tocar na tela"]'
# Microfone e voz de mentira para a CONVERSA: o reconhecedor "ouve" as frases de window.__falas (uma por vez) e a fala só
# registra o texto em window.__faladas. Os eventos do núcleo de voz ficam em window.__voz.
VOZ_FALSA = r"""(() => {
  window.__falas = []; window.__faladas = []; window.__voz = [];
  window.addEventListener('capitao-voz', (e) => window.__voz.push(e.detail));
  class SR {
    start() { const f = window.__falas.shift(); if (f) setTimeout(() => { if (this.onresult) this.onresult({ results: [[{ transcript: f }]] }); }, 60); }
    stop() {} abort() {}
  }
  window.SpeechRecognition = SR; window.webkitSpeechRecognition = SR;
})()"""


def versoes():
    """A mesma versão em todo lugar que a declara (o capitao-app.js recarrega se cérebro/cliente vierem de outra)."""
    ler = lambda p: open(os.path.join(RAIZ, p), encoding='utf-8').read()
    return {
        'capitao-auth.js': re.search(r"var VERSAO = \{ v: '([^']+)'", ler('capitao-auth.js')).group(1),
        'capitao-brain.js': re.search(r"var VERSAO = '([^']+)'", ler('capitao-brain.js')).group(1),
        'capitao-ia.js': re.search(r"var VERSAO = '([^']+)'", ler('capitao-ia.js')).group(1),
        'integracoes/ia-cliente/capitao-ia.js': re.search(r"var VERSAO = '([^']+)'", ler('integracoes/ia-cliente/capitao-ia.js')).group(1),
        'sw.js': re.search(r"const CACHE = 'capitao-site-v([^']+)'", ler('sw.js')).group(1),
        'README.md': re.search(r"\*\*Versão ([0-9.]+) ", ler('README.md')).group(1),
    }


VERSAO = versoes()['capitao-auth.js']


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
    vs = versoes()
    ok('mesma versão em auth, cérebro, cliente da IA (as duas cópias), sw.js e README (' + VERSAO + ')', len(set(vs.values())) == 1, vs)

    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel='msedge')
            for tela, movel, campo in (('H2-Home-Mobile', True, '#pergunta-m'), ('Main', False, '#pergunta')):
                ctx = b.new_context(viewport={'width': 390, 'height': 844} if movel else {'width': 1440, 'height': 900},
                                    user_agent=MOBILE_UA if movel else None, is_mobile=movel, has_touch=movel, service_workers='block')
                ctx.add_init_script(SESSAO)
                ctx.add_init_script(VOZ_FALSA)
                pg = ctx.new_page()
                erros = []
                pg.on('pageerror', lambda e: erros.append(str(e)[:200]))
                # erro de sintaxe na lógica da tela só aparece no console do runtime ("logic class eval FAILED")
                pg.on('console', lambda m: erros.append(m.text[:200]) if m.type == 'error' and 'FAILED' in m.text else None)
                estado = {'pedidos': [], 'modo': 'ok'}

                def rota(route):
                    req = route.request
                    cab = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type, X-Capitao-Chave', 'Access-Control-Allow-Methods': 'POST, OPTIONS'}
                    if req.method == 'OPTIONS':
                        return route.fulfill(status=204, headers=cab)
                    corpo = json.loads(req.post_data or '{}')
                    estado['pedidos'].append(corpo)
                    if not corpo.get('ficha') and not corpo.get('trechos') and not corpo.get('contexto'):
                        # como o Worker de verdade: sem fontes → 422 antes de chamar o modelo (é o teste da chave do diagnóstico)
                        return route.fulfill(status=422, content_type='application/json', headers=cab, body='{"erro":"sem fontes","motivo":"sem_fontes"}')
                    if estado['modo'] == 'erro':
                        return route.fulfill(status=503, content_type='application/json', headers=cab, body='{"erro":"cota grátis diária da IA esgotada"}')
                    texto = ('SEM DADOS — os trechos não respondem.\nFonte: nenhuma — a ficha, os trechos e a leitura enviados pelo app não respondem a pergunta'
                             if estado['modo'] == 'semdados' else TEXTO_IA + '\nFonte: Guia de bordo (DEMO) — Gerador Onan · 2 · Ligar')
                    return route.fulfill(status=200, content_type='application/json', headers=cab,
                                         body=json.dumps({'texto': texto, 'provedor': 'Workers AI', 'modelo': '@cf/meta/llama-3.3-70b-instruct-fp8-fast', 'parou': 'fim'}))
                pg.route(URL_ARQ.rstrip('/') + '**', rota)

                def espera_resposta():
                    try:
                        pg.wait_for_function("() => /Fonte:/.test(document.body.innerText)", timeout=15000)
                        pg.wait_for_function("() => !document.querySelector('[data-capitao-pensando]')", timeout=20000)
                    except Exception:
                        pass
                    pg.wait_for_timeout(600)

                def prepara(chave):
                    pg.goto(base + 'README.md')
                    pg.evaluate("(c) => { if (c) localStorage.setItem('capitao.ia.chave.v1', 'chave-de-teste'); else localStorage.removeItem('capitao.ia.chave.v1'); }", chave)

                def abre(chave=True, modo='ok'):
                    estado['modo'] = modo
                    prepara(chave)
                    pg.goto(base + tela + '.dc.html')
                    pg.wait_for_function(PRONTA, timeout=20000)
                    pg.wait_for_selector(campo, timeout=15000)

                def envia(q):
                    antes = len(estado['pedidos'])
                    pg.fill(campo, q)
                    pg.press(campo, 'Enter')
                    espera_resposta()
                    return pg.evaluate('() => document.body.innerText'), len(estado['pedidos']) - antes, pg.query_selector('[data-capitao-pensando]') is None

                def digita(q, chave=True, modo='ok'):
                    """Pergunta digitada no campo do chat (o caminho normal), numa conversa nova."""
                    abre(chave, modo)
                    return envia(q)

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
                ok(tela + ': resposta da IA na tela, com a fonte dela + "via IA na nuvem (Workers AI · llama-3.3-70b-instruct-fp8-fast)"', TEXTO_IA in t and FONTE_IA in t, t[-300:])
                ok(tela + ': indicador "consultando" some depois da resposta da IA', livre)
                ped = estado['pedidos'][-1] if estado['pedidos'] else {}
                f = ped.get('ficha', '')
                ok(tela + ': pedido leva a pergunta e trechos do guia do gerador', ped.get('pergunta') == 'como ligar o gerador?' and ped.get('trechos') and 'Gerador' in ped['trechos'][0].get('fonte', ''), json.dumps(ped, ensure_ascii=False)[:200])
                ok(tela + ': trecho do guia leva a ficha RESUMIDA (sobre o app, embarcação; sem telemetria nem coordenadas) e o histórico vazio', '## Sobre o app' in f and '## Ficha resumida' in f and '## Telemetria' not in f and 'DEMO' in f and "26°59" not in f and ped.get('historico') == [], len(f))
                t, n, _ = digita('quantas horas tem o gerador')
                ok(tela + ': resposta pronta (não base) não chama a IA', n == 0 and TEXTO_IA not in t, 'pedidos=%d' % n)
                t, n, _ = digita('oi')
                ok(tela + ': só um "oi" não chama a IA (saudação pronta)', n == 0 and 'Capitão IA online' in t, 'pedidos=%d' % n)
                t, n, _ = digita('Oque você faz?')
                ok(tela + ': "Oque você faz?" chama a IA', n == 1 and TEXTO_IA in t, 'pedidos=%d' % n)
                t, n, _ = digita('qual o calado do barco?')
                fc = estado['pedidos'][-1].get('ficha', '') if estado['pedidos'] else ''
                ok(tela + ': SEM DADOS local chama a IA com a ficha COMPLETA e mostra a resposta dela', n == 1 and TEXTO_IA in t and 'Não encontrei esse dado' not in t and '## Telemetria' in fc and '## Ficha resumida' not in fc and "26°59" not in fc, 'pedidos=%d ficha=%d' % (n, len(fc)))
                t, n, _ = digita('diagnóstico')
                ok(tela + ': "diagnóstico" mostra versões e estado e testa a chave no servidor sem gastar a cota (pedido sem fontes → 422)', n == 1 and 'Diagnóstico do Capitão IA neste aparelho' in t and 'LIGADA neste aparelho' in t and 'Chave aceita pelo servidor' in t and 'versões diferentes' not in t, 'pedidos=%d' % n)
                t, n, _ = digita('diagnóstico', chave=False)
                ok(tela + ': "diagnóstico" sem chave diz "DESLIGADA neste aparelho (sem chave)" e não vai para a rede', n == 0 and 'DESLIGADA neste aparelho (sem chave)' in t and 'Nenhuma chave guardada' in t, 'pedidos=%d' % n)
                t, n, _ = digita('qual o calado do barco?', modo='semdados')
                ok(tela + ': "SEM DADOS" da IA troca o SEM DADOS genérico da tela', n == 1 and 'os trechos não respondem' in t and 'Não encontrei esse dado' not in t, 'pedidos=%d' % n)
                t, n, _ = digita('como ligar o gerador?', chave=False)
                ok(tela + ': sem a CHAVE_APP no aparelho nada vai para a rede (fica o trecho local)', n == 0 and TEXTO_IA not in t and 'PARTIDA' in t, 'pedidos=%d' % n)
                t, n, _ = digita('qual o calado do barco?', chave=False)
                ok(tela + ': sem a CHAVE_APP, a fonte diz "IA na nuvem desligada neste aparelho" e oferece "Ativar IA na nuvem"', n == 0 and 'IA na nuvem desligada neste aparelho' in t and pg.query_selector('a[href="#ia=ativar"]') is not None, t[-300:])
                ok(tela + ': sem a CHAVE_APP, aviso grande na tela "IA NA NUVEM NÃO ATIVADA NESTE APARELHO"', 'IA NA NUVEM NÃO ATIVADA NESTE APARELHO' in t, t[-300:])
                t, n, livre = digita('como ligar o gerador?', modo='erro')
                ok(tela + ': erro do proxy mantém a resposta local com o motivo (e o indicador some)', n == 1 and TEXTO_IA not in t and 'PARTIDA' in t and 'IA na nuvem fora agora' in t and livre, 'pedidos=%d' % n)
                t, n, _ = digita('como ligar o gerador?', modo='semdados')
                ok(tela + ': "SEM DADOS" da IA mantém o trecho local com a fonte', n == 1 and 'PARTIDA' in t and 'Fonte: nenhuma' not in t, 'pedidos=%d' % n)

                # Histórico: a 2ª pergunta leva a 1ª e a resposta dela.
                abre()
                envia('como ligar o gerador?')
                t, n, _ = envia('e para desligar?')
                h = estado['pedidos'][-1].get('historico') if estado['pedidos'] else None
                ok(tela + ': a pergunta seguinte leva o histórico (pergunta e resposta anteriores)', n == 1 and h and len(h) == 2 and h[0] == {'papel': 'usuario', 'texto': 'como ligar o gerador?'} and h[1]['papel'] == 'capitao' and TEXTO_IA in h[1]['texto'], json.dumps(h, ensure_ascii=False)[:300])

                # Ordem: a resposta da IA (demorada) entra logo depois da pergunta dela, antes da pergunta seguinte.
                abre()
                pg.evaluate("() => { const IA = window.CapitaoIA; IA.ativa = () => true; IA.perguntar = (q) => new Promise((r) => setTimeout(() => r({ text: 'IA respondeu: ' + q, src: 'Fonte: teste · via IA na nuvem', key: 'ia', semDados: false }), 1800)); }")
                pg.fill(campo, 'qual o calado do barco?')
                pg.press(campo, 'Enter')
                pg.wait_for_timeout(300)
                pg.fill(campo, 'autonomia')
                pg.press(campo, 'Enter')
                espera_resposta()
                pg.wait_for_function("() => /IA respondeu: qual o calado/.test(document.body.innerText)", timeout=10000)
                t = pg.evaluate('() => document.body.innerText')
                i1, i2, i3 = t.find('IA respondeu: qual o calado do barco?'), t.find('\nautonomia\n'), t.find('≈ 11,2 h')
                ok(tela + ': resposta da IA entra logo depois da pergunta dela (ordem pergunta › resposta mantida)', -1 < i1 < i2 < i3, (i1, i2, i3))

                # CONVERSA por voz: a pergunta falada vai para a IA e a resposta falada é a da IA (o núcleo fica em PROCESSANDO).
                abre()
                pg.evaluate("() => { window.__falas.push('qual o calado do barco'); const B = window.CapitaoBrain; B.speak = (t, fim) => { window.__faladas.push(t); setTimeout(() => fim && fim(), 80); return true; }; }")
                antes = len(estado['pedidos'])
                pg.click(CONVERSA)
                try:
                    pg.wait_for_function('() => window.__faladas.length >= 2', timeout=20000)
                except Exception:
                    pass
                faladas = pg.evaluate('() => window.__faladas')
                segura = pg.evaluate("() => window.__voz.some((v) => v.estado === 'pensando' && v.segura)")
                ultimo = estado['pedidos'][-1] if len(estado['pedidos']) > antes else {}
                ok(tela + ': CONVERSA: a pergunta falada chama a IA e a resposta falada é a da IA', len(estado['pedidos']) - antes == 1 and ultimo.get('pergunta') == 'qual o calado do barco' and len(faladas) >= 2 and faladas[1] == TEXTO_IA, json.dumps(faladas, ensure_ascii=False)[:300])
                ok(tela + ': CONVERSA: o núcleo de voz fica em PROCESSANDO esperando a IA', segura)
                pg.keyboard.press('Escape')

                def conversa(q, chave=True, modo='ok'):
                    """Uma pergunta falada na CONVERSA (microfone e voz de mentira); devolve as falas e quantos pedidos saíram."""
                    abre(chave, modo)
                    pg.evaluate("(q) => { window.__falas.push(q); const B = window.CapitaoBrain; B.speak = (t, fim) => { window.__faladas.push(t); setTimeout(() => fim && fim(), 80); return true; }; }", q)
                    antes = len(estado['pedidos'])
                    pg.click(CONVERSA)
                    try:
                        pg.wait_for_function('() => window.__faladas.length >= 2', timeout=20000)
                    except Exception:
                        pass
                    f = pg.evaluate('() => window.__faladas')
                    pg.keyboard.press('Escape')
                    return f, len(estado['pedidos']) - antes

                f, n = conversa('o que você faz', chave=False)
                ok(tela + ': CONVERSA sem a chave: fala o que o Capitão faz (não repete a abertura) e que a IA não está ativada; nada vai para a rede', n == 0 and len(f) >= 2 and f[1].startswith('Respondo sobre telemetria') and 'não está ativada neste aparelho' in f[1], json.dumps(f, ensure_ascii=False)[:300])
                f, n = conversa('qual o calado do barco', modo='erro')
                ok(tela + ': CONVERSA com erro do servidor: a voz fala o motivo ("IA na nuvem fora agora…")', n == 1 and len(f) >= 2 and 'IA na nuvem fora agora' in f[1], json.dumps(f, ensure_ascii=False)[:300])

                # Versões misturadas (cérebro velho vindo do cache): o app recarrega sozinho uma vez e fica tudo na mesma versão.
                cont = {'n': 0}

                def cerebro_velho(route):
                    cont['n'] += 1
                    if cont['n'] <= 2:  # a tela pode pedir o cérebro 2 vezes (tag do helmet + whenBrain); cache velho serviria os dois
                        corpo = open(os.path.join(RAIZ, 'capitao-brain.js'), encoding='utf-8').read().replace("var VERSAO = '%s'" % VERSAO, "var VERSAO = '0.0.1'")
                        return route.fulfill(status=200, content_type='text/javascript; charset=utf-8', body=corpo)
                    return route.continue_()
                pg.route('**/capitao-brain.js*', cerebro_velho)
                prepara(True)
                pg.goto(base + tela + '.dc.html')
                try:
                    pg.wait_for_function("(v) => window.CapitaoBrain && window.CapitaoBrain.VERSAO === v && sessionStorage.getItem('capitao.recarga.v1') === v", arg=VERSAO, timeout=20000)
                except Exception:
                    pass
                v = pg.evaluate("() => [window.CapitaoBrain && window.CapitaoBrain.VERSAO, sessionStorage.getItem('capitao.recarga.v1')]")
                ok(tela + ': versões misturadas (cérebro velho do cache): recarrega sozinho uma vez e fica tudo em ' + VERSAO, v[0] == VERSAO and v[1] == VERSAO and cont['n'] >= 2, '%s pedidos do cérebro=%d' % (v, cont['n']))
                pg.unroute('**/capitao-brain.js*', cerebro_velho)

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
