"""Teste de ponta a ponta da IA na nuvem nas telas de chat (Main e H2), com o Worker SIMULADO — não gasta cota.

Confere que a IA entra quando a resposta local não basta (SEM DADOS, trecho do guia, pergunta sobre o app — "Oque você faz?")
e nunca em resposta pronta ou só num "oi"; que o pedido leva a ficha de bordo (sem coordenadas) e o histórico da conversa;
que sem a CHAVE_APP no aparelho nada vai para a rede e a linha da fonte diz por quê (com o botão "Ativar IA na nuvem");
que erro do proxy mantém a resposta local com o motivo; que "SEM DADOS" da IA mantém o trecho do guia mas troca o SEM DADOS
genérico; que a resposta entra logo depois da pergunta dela; que na CONVERSA por voz a IA responde e a resposta dela é a
falada; que na CONVERSA a pergunta ouvida vai ao cérebro sem a pausa de 0,65 s e o VOZ→TEXTO a mantém; que link de fora
(#q=) não gasta a cota e link de dentro do app usa a IA; que o indicador some ao fim;
que a voz vai a 1,15x em toda fala (abertura, SOS e óleo) e os eventos "falando" levam o som; que o núcleo abre com o rosto
de partículas (canvas + CapitaoRosto) e o Esc encerra; e que o login não leva a chave do endereço para o ?next=.

    python -X utf8 testes/chat_ia.py        (sobe um servidor local próprio; o React vem do próprio site, assets/vendor)
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
# Fase 3 (P3D), PROMPT Fase 7 linha 3 (`:210`): a ficha que vai à IA não leva coordenada pela regex do §2.8 (graus-minutos e decimal; a mesma do cerebro.py e do gerador), e não a posição literal do snapshot
sys.path.insert(0, os.path.join(RAIZ, 'ferramentas', 'demo'))
import confere  # noqa: E402
URL_ARQ = re.search(r"var URL_PROXY = '([^']+)'", open(os.path.join(RAIZ, 'capitao-ia.js'), encoding='utf-8').read()).group(1)
# Fase 3 (P3B): o fallback local não diz mais «Não encontrei esse dado … SEM DADOS» (decisão 5); a conferência «a tela mostra a resposta da IA e não o texto local» passa a procurar o texto novo
FALLBACK_LOCAL = 'Isso não está nas fontes de bordo'
# Fase 4 (P4H, F6): o toque numa pergunta do FAQ dos equipamentos abre o chat com o código do item (#q=<pergunta>&faq=<código>)
FAQ_ITENS = {it['id']: it for it in json.load(open(os.path.join(RAIZ, 'faq-equipamentos.json'), encoding='utf-8'))['itens']}
SESSAO = "(() => { const n = Date.now(); localStorage.setItem('capitao.sessao.v1', JSON.stringify({ u: 'lucas', em: n, exp: n + 3600e3 })); })()"
# Fase 3 (P3A, PROMPT Fase 7 «Mudanças nos testes»: «:254 ("≈ 11,2 h") com o quadro congelado»): a autonomia da resposta lê o instante do
# replay. Congelado em 12:01:00 (fixar('60')), são 1.333 L menos a reserva de 10 %: 17,6 h a 18 nós (CapitaoAgora.instante().calc).
REPLAY_FIXO = "(() => { try { localStorage.setItem('capitao.replay.fixo', '60'); } catch (e) {} })()"
AUTONOMIA = '≈ 17,6 h'
MOBILE_UA = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Mobile Safari/537.36'
TEXTO_IA = 'Resposta simulada da IA: segure PARTIDA até o motor pegar.'
# Contrato C2: o título do guia perdeu o "(DEMO)" (Decisão 1.1.0, b); o Worker devolve a fonte do trecho que o app mandou.
FONTE_IA = 'Guia de bordo — Gerador Onan · 2 · Ligar · via IA na nuvem (Workers AI · llama-3.3-70b-instruct-fp8-fast)'
PRONTA = "() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0"
CONVERSA = '[aria-label="Conversa contínua por voz — sem tocar na tela"]'
VOZ = '[aria-label="Falar — a pergunta é transcrita e respondida em texto e voz"]'  # VOZ (web) e VOZ→TEXTO (app)
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

# Voz de verdade do cérebro (B.speak) sobre um speechSynthesis de mentira: guarda cada fala (texto e velocidade) em
# window.__sint e chama onstart → onboundary (palavra) → onend.
SINTESE_FALSA = r"""(() => {
  window.__sint = []; window.__estRosto = []; window.__somRosto = [];
  const ss = window.speechSynthesis;
  ss.cancel = () => {}; ss.pause = () => {}; ss.resume = () => {};
  ss.speak = (u) => {
    window.__sint.push({ t: u.text, r: u.rate });
    setTimeout(() => {
      if (u.onstart) u.onstart({});
      setTimeout(() => { if (u.onboundary) u.onboundary({ name: 'word' }); }, 40);
      setTimeout(() => { if (u.onend) u.onend({}); }, 180);
    }, 20);
  };
})()"""

# O rosto do núcleo (CapitaoRosto.criar) é espiado desde que o capitao-rosto.js chega — o capitao-voz.js já o cria escondido,
# com o app ocioso, antes da 1ª conversa: opções em window.__rostoOp, estados em window.__estRosto e o som em
# window.__somRosto.
ESPIA_ROSTO = r"""(() => {
  window.__estRosto = []; window.__somRosto = [];
  let R;
  Object.defineProperty(window, 'CapitaoRosto', { configurable: true, get() { return R; }, set(v) {
    R = v; if (!v || v.__espiado) return; v.__espiado = true;
    const criar = v.criar;
    v.criar = (tela, op) => {
      const r = criar(tela, op), est = r.estado, som = r.som;
      window.__rostoOp = op;
      r.estado = (n) => { window.__estRosto.push(n); return est(n); };
      r.som = (x) => { window.__somRosto.push(!!x); return som(x); };
      return r;
    };
  } });
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
                ctx.add_init_script(REPLAY_FIXO)
                ctx.add_init_script(VOZ_FALSA)
                ctx.add_init_script(ESPIA_ROSTO)
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
                             if estado['modo'] == 'semdados' else TEXTO_IA + '\nFonte: Guia de bordo — Gerador Onan · 2 · Ligar')  # sem "(DEMO)" desde o C2
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

                def por_link(q, interno, extra=''):
                    """Pergunta por link #q=: de fora (sem referrer) ou de dentro do app (referrer da mesma origem); `extra` vai depois da pergunta (&faq=<código>: o toque no FAQ)."""
                    estado['modo'] = 'ok'
                    prepara(True)
                    antes = len(estado['pedidos'])
                    alvo = base + tela + '.dc.html#q=' + urllib.parse.quote(q) + extra
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
                # 'DEMO' not in f: desde o C2 a ficha não leva o rótulo (Decisão 1.1.0, b); antes exigia 'DEMO' in f
                ok(tela + ': trecho do guia leva a ficha COMPLETA (a resumida tirava o dado pedido), sem coordenadas nem o rótulo DEMO, e o histórico vazio', '## Sobre o app' in f and '## Telemetria' in f and '## Manutenção' in f and '## Ficha resumida' not in f and 'DEMO' not in f and not confere.R_COORD.search(f) and ped.get('historico') == [], len(f))
                t, n, _ = digita('quantas horas tem o gerador')
                ok(tela + ': resposta pronta (não base) não chama a IA', n == 0 and TEXTO_IA not in t, 'pedidos=%d' % n)
                t, n, _ = digita('oi')
                ok(tela + ': só um "oi" não chama a IA (saudação pronta)', n == 0 and 'Capitão IA online' in t, 'pedidos=%d' % n)
                t, n, _ = digita('Oque você faz?')
                ok(tela + ': "Oque você faz?" chama a IA', n == 1 and TEXTO_IA in t, 'pedidos=%d' % n)
                # Fase 3 (P3E, F10): o FAQ dos equipamentos responde no chat o que nenhuma resposta pronta nem trecho do guia responde, com o código do item e a fonte. O item de segurança (CK-03)
                # fica no aparelho (nunca à IA); o item comum (EL-08) vai à IA como o trecho do guia e, sem a chave, mostra o item
                def faq_pronto():
                    pg.evaluate("() => window.CapitaoBrain.carregaFaq()")
                abre(True, 'ok'); faq_pronto()
                t, n, _ = envia('boletim da Marinha antes de sair')
                ok(tela + ': o item de segurança do FAQ (CK-03) responde no aparelho, com o código e a fonte, sem chamar a IA', n == 0 and 'FAQ dos equipamentos CK-03' in t and 'Antes de largar: um colete por pessoa' in t and TEXTO_IA not in t, 'pedidos=%d' % n)
                abre(True, 'ok'); faq_pronto()
                t, n, _ = envia('sonda mostrando pouca profundidade')
                ok(tela + ': o item comum do FAQ (EL-08) chama a IA 1 vez como o trecho do guia e mostra a resposta dela', n == 1 and TEXTO_IA in t, 'pedidos=%d' % n)
                abre(False, 'ok'); faq_pronto()
                t, n, _ = envia('sonda mostrando pouca profundidade')
                ok(tela + ': sem a CHAVE_APP o item do FAQ (EL-08) fica na tela, com o código e a fonte, e nada vai à rede', n == 0 and 'FAQ dos equipamentos EL-08' in t and 'Profundidade mínima de navegação' in t and TEXTO_IA not in t, 'pedidos=%d' % n)
                # Fase 3 (P3C), PROMPT Fase 7 «Mudanças nos testes»: o «calado» passou a ter dado (rota embarcacao, resposta local); o gatilho «sem resposta pronta → IA» é uma
                # pergunta de náutica geral sem rota (cai em fallback, pedeIA true). Vale em todos os usos abaixo (SEM DADOS da IA, sem chave, ordem da resposta, CONVERSA e erro).
                t, n, _ = digita('como se faz um nó lais de guia?')
                fc = estado['pedidos'][-1].get('ficha', '') if estado['pedidos'] else ''
                ok(tela + ': pergunta sem rota (fallback) chama a IA com a ficha COMPLETA e mostra a resposta dela', n == 1 and TEXTO_IA in t and FALLBACK_LOCAL not in t and '## Telemetria' in fc and '## Ficha resumida' not in fc and not confere.R_COORD.search(fc), 'pedidos=%d ficha=%d' % (n, len(fc)))
                # Fase 4 (P4G): o 3º argumento do IA.perguntar é a leitura de agora (B.resumoAgora, o instante da resposta; antes era '': o pedido só levava a ficha): com o replay fixado em 60 s é o resumo de 12:01:00,
                # sem coordenada, e o botão «O que verificar?» do relato manda a pergunta pronta à IA com ele (a tela escuta o link #capitao-relato-…, o cérebro o transforma na pergunta)
                resumo = pg.evaluate('() => window.CapitaoBrain.resumoAgora()')
                cx = estado['pedidos'][-1].get('contexto', '') if estado['pedidos'] else ''
                ok(tela + ': o pedido à IA leva a leitura de agora (3º argumento = B.resumoAgora: SOG e hora 12:01:00, sem coordenadas, ≤ 300 letras)', cx == resumo and re.search(r'SOG \d+,\d nós', cx) and '12:01:00' in cx and not confere.R_COORD.search(cx) and len(cx) <= 300, cx[:120])
                t, n, _ = digita('O gerador desligou sozinho duas vezes hoje de manhã quando ligamos o ar condicionado')
                antes = len(estado['pedidos'])
                pg.locator('a:has-text("O que verificar?")').last.click()
                espera_resposta()
                ped = estado['pedidos'][-1] if len(estado['pedidos']) > antes else {}
                ok(tela + ': o botão «O que verificar?» do relato vai à IA (1 pedido, a pergunta pronta com o relato, a leitura de agora) sem navegar nem gravar no diário', len(estado['pedidos']) == antes + 1 and ped.get('pergunta', '').startswith('O que verificar') and 'desligou sozinho' in ped.get('pergunta', '') and bool(ped.get('contexto'))
                   and tela in pg.url and pg.evaluate("() => localStorage.getItem('capitao.diario.v1')") is None, ped.get('pergunta', '')[:80])
                # Fase 3 (P3C): as rotas novas respondem no aparelho, na tela, sem chamar a IA nem mostrar o texto dela (o calado do cadastro, o fora do barco e a pergunta sobre os dados)
                # P3F (revisão): a pergunta pronta do botão «O que verificar?» do relato é a rota relatoVerifica: chama a IA (1 pedido), em vez de a resposta pronta do gerador que o relato já recebeu
                t, n, _ = digita('O que verificar e qual pode ser a causa: O gerador desligou sozinho duas vezes hoje de manhã quando ligamos o ar condicionado')
                ok(tela + ': O que verificar? (revisão P3F): a pergunta pronta do relato chama a IA (1 pedido, com o texto do relato) e mostra a resposta dela', n == 1 and TEXTO_IA in t and 'desligou sozinho duas vezes' in json.dumps(estado['pedidos'][-1], ensure_ascii=False), 'pedidos=%d' % n)
                t, n, _ = digita('qual o calado do barco?')
                cal = ('%.2f' % pg.evaluate('() => window.CapitaoDados.embarcacao.calado')).replace('.', ',')
                ok(tela + ': o calado tem dado: a rota embarcacao responde na tela, no aparelho, sem chamar a IA', n == 0 and ('O calado do barco é %s m' % cal) in t and TEXTO_IA not in t and FALLBACK_LOCAL not in t, 'pedidos=%d calado=%s' % (n, cal))
                t, n, _ = digita('qual o preço do dólar?')
                ok(tela + ': dinheiro e fora do barco (foraBarco) respondem no aparelho, sem IA e sem preço', n == 0 and 'Isso fica fora do barco.' in t and 'Situação de bordo agora' in t and TEXTO_IA not in t and not re.search(r'R\$|US\$|\d,\d\d\s*(?:reais|dólares)', t), 'pedidos=%d' % n)
                t, n, _ = digita('esses dados são reais?')
                ok(tela + ': a pergunta sobre os dados (sobreDados) é local: a frase padrão e a situação de bordo, sem IA', n == 0 and 'Esta é a embarcação de apresentação da plataforma Capitão IA' in t and 'Situação de bordo agora' in t and TEXTO_IA not in t, 'pedidos=%d' % n)
                # Fase 3 (P3G, F12/F15/F20/F26): o alarme pedido, a agenda, a pendência fechada pelo registro e o que o app faz respondem NO APARELHO, na tela, sem chamar a IA — mesmo com a chave
                # ligada. (Os botões Confirmar/Recusar/Desfazer das propostas são links #capitao-prop-…; a tela passa a escutá-los na Fase 4: aqui vale a frase digitada, «confirmar alarme», «sim», «desfazer».)
                t, n, _ = digita('me avise se a pressão do óleo do BB cair abaixo de 2 bar')
                ok(tela + ': o pedido de alarme (F12) é local: a proposta com a regra, o aviso só na tela e o Confirmar, sem IA e sem gravar', n == 0 and 'Posso criar este alarme: Pressão de óleo BB abaixo de 2,0 bar.' in t and 'Aviso só na tela do app' in t and TEXTO_IA not in t
                   and pg.evaluate("() => localStorage.getItem('capitao.alarmes.v1')") is None, 'pedidos=%d' % n)
                t, n, _ = envia('confirmar alarme')
                guardado = pg.evaluate("() => JSON.parse(localStorage.getItem('capitao.alarmes.v1') || '[]')")
                ok(tela + ': «confirmar alarme» grava a regra (1 linha usr_1) no aparelho, sem IA', n == 0 and 'Alarme criado: #1 Pressão de óleo BB abaixo de 2,0 bar.' in t and len(guardado) == 1 and guardado[0]['id'] == 'usr_1', 'pedidos=%d guardado=%s' % (n, guardado))
                t, n, _ = envia('meus alarmes')
                ok(tela + ': «meus alarmes» lista a regra com a leitura de agora e a hora, sem IA', n == 0 and '• #1 Pressão de óleo BB abaixo de 2,0 bar — agora ' in t and re.search(r'1 alarme pedido às \d\d:\d\d:\d\d', t) is not None, 'pedidos=%d' % n)
                t, n, _ = envia('apagar alarme #1')
                guardado = pg.evaluate("() => JSON.parse(localStorage.getItem('capitao.alarmes.v1') || '[]')")
                ok(tela + ': «apagar alarme #1» é uma linha NOVA (acao apaga): o registro tem 2 linhas, sem IA', n == 0 and 'Alarme #1 apagado' in t and [x.get('acao') for x in guardado] == ['apaga', None], 'pedidos=%d guardado=%s' % (n, guardado))
                t, n, _ = digita('agendar revisão do gerador para 15/11')
                ok(tela + ': «agendar … para 15/11» (F15) é a proposta local da tarefa da equipe, com a data e o prazo, sem IA e sem gravar a tarefa', n == 0 and 'Posso agendar na equipe: Revisão do gerador — vence 15/11/' in t and TEXTO_IA not in t and pg.evaluate("() => localStorage.getItem('capitao.tarefas.v1')") is None, 'pedidos=%d' % n)
                t, n, _ = envia('sim')
                tarefas = pg.evaluate("() => JSON.parse(localStorage.getItem('capitao.tarefas.v1') || '[]')")
                ok(tela + ': o «sim» logo depois grava a tarefa (vence AAAA-11-15) e 1 linha no diário, sem IA', n == 0 and 'Tarefa agendada: Revisão do gerador' in t and len(tarefas) == 1 and tarefas[0]['vence'].endswith('-11-15'), 'pedidos=%d tarefas=%s' % (n, tarefas))
                t, n, _ = envia('desfazer')
                ok(tela + ': «desfazer» tira a tarefa (a linha do diário é anulada por uma linha nova), sem IA', n == 0 and 'Desfeito: a tarefa saiu da agenda da equipe' in t and pg.evaluate("() => JSON.parse(localStorage.getItem('capitao.tarefas.v1') || '[]').length") == 0, 'pedidos=%d' % n)
                t, n, _ = digita('registre no diário que limpei o filtro de água salgada da climatização')
                ok(tela + ': o registro que conclui um serviço (F20/F15) fecha a pendência que cita e propõe o Executado, no aparelho, sem IA', n == 0 and 'Pendência fechada: Climatização da cabine de proa com fluxo fraco' in t and 'Proposta: marcar “Limpeza do filtro de água salgada da climatização” como executada na agenda.' in t and TEXTO_IA not in t, 'pedidos=%d' % n)
                t, n, _ = envia('desfazer')
                ok(tela + ': «desfazer» reabre a pendência com uma linha nova, sem IA', n == 0 and 'Desfeito: a pendência' in t and 'voltou a ficar aberta' in t, 'pedidos=%d' % n)
                t, n, _ = digita('o que você pode fazer?')
                ok(tela + ': «o que você pode fazer?» (F26) é a lista local do que o app faz — sem IA, mesmo com a chave ligada —, com a fonte e os exemplos', n == 0 and 'Sou o Capitão IA, o assistente de bordo. Posso:' in t and 'Fonte: funções do app Capitão IA' in t and TEXTO_IA not in t, 'pedidos=%d' % n)
                pg.evaluate("() => ['capitao.alarmes.v1', 'capitao.tarefas.v1', 'capitao.tickets.v1', 'capitao.diario.v1', 'capitao.executado.v1'].forEach((k) => localStorage.removeItem(k))")   # (o que este bloco gravou no aparelho de teste; as conferências de baixo partem do aparelho limpo)
                t, n, _ = digita('diagnóstico')
                ok(tela + ': "diagnóstico" mostra versões e estado e testa a chave no servidor sem gastar a cota (pedido sem fontes → 422)', n == 1 and 'Diagnóstico do Capitão IA neste aparelho' in t and 'LIGADA neste navegador' in t and 'Chave aceita pelo servidor' in t and 'versões diferentes' not in t, 'pedidos=%d' % n)
                t, n, _ = digita('diagnóstico', chave=False)
                ok(tela + ': "diagnóstico" sem chave diz "DESLIGADA neste navegador (sem chave)" e não vai para a rede', n == 0 and 'DESLIGADA neste navegador (sem chave)' in t and 'Nenhuma chave guardada' in t, 'pedidos=%d' % n)
                t, n, _ = digita('como se faz um nó lais de guia?', modo='semdados')
                ok(tela + ': "SEM DADOS" da IA troca o SEM DADOS genérico da tela', n == 1 and 'os trechos não respondem' in t and FALLBACK_LOCAL not in t, 'pedidos=%d' % n)
                t, n, _ = digita('como ligar o gerador?', chave=False)
                ok(tela + ': sem a CHAVE_APP no aparelho nada vai para a rede (fica o trecho local)', n == 0 and TEXTO_IA not in t and 'PARTIDA' in t, 'pedidos=%d' % n)
                t, n, _ = digita('como se faz um nó lais de guia?', chave=False)
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
                pg.fill(campo, 'como se faz um nó lais de guia?')
                pg.press(campo, 'Enter')
                pg.wait_for_timeout(300)
                pg.fill(campo, 'autonomia')
                pg.press(campo, 'Enter')
                espera_resposta()
                pg.wait_for_function("() => /IA respondeu: como se faz um nó lais/.test(document.body.innerText)", timeout=10000)
                t = pg.evaluate('() => document.body.innerText')
                i1, i2, i3 = t.find('IA respondeu: como se faz um nó lais de guia?'), t.find('\nautonomia\n'), t.find(AUTONOMIA)
                ok(tela + ': resposta da IA entra logo depois da pergunta dela (ordem pergunta › resposta mantida)', -1 < i1 < i2 < i3, (i1, i2, i3))

                # CONVERSA por voz: a pergunta falada vai para a IA e a resposta falada é a da IA (o núcleo fica em PROCESSANDO).
                abre()
                pg.evaluate("() => { window.__falas.push('como se faz um nó lais de guia'); const B = window.CapitaoBrain; B.speak = (t, fim) => { window.__faladas.push(t); setTimeout(() => fim && fim(), 80); return true; }; }")
                antes = len(estado['pedidos'])
                pg.click(CONVERSA)
                try:
                    pg.wait_for_function('() => window.__faladas.length >= 2', timeout=20000)
                except Exception:
                    pass
                faladas = pg.evaluate('() => window.__faladas')
                segura = pg.evaluate("() => window.__voz.some((v) => v.estado === 'pensando' && v.segura)")
                ultimo = estado['pedidos'][-1] if len(estado['pedidos']) > antes else {}
                ok(tela + ': CONVERSA: a pergunta falada chama a IA e a resposta falada é a da IA', len(estado['pedidos']) - antes == 1 and ultimo.get('pergunta') == 'como se faz um nó lais de guia' and len(faladas) >= 2 and faladas[1] == TEXTO_IA, json.dumps(faladas, ensure_ascii=False)[:300])
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
                f, n = conversa('Capitão, diagnóstico')
                ok(tela + ': CONVERSA: "Capitão, diagnóstico" fala se a IA está ligada e o resultado do teste da chave (sem gastar a cota)', n == 1 and len(f) >= 2 and 'IA na nuvem: LIGADA' in f[1] and 'Chave aceita pelo servidor' in f[1], json.dumps(f, ensure_ascii=False)[:300])
                f, n = conversa('como se faz um nó lais de guia', modo='erro')
                ok(tela + ': CONVERSA com erro do servidor: a voz fala o motivo ("IA na nuvem fora agora…")', n == 1 and len(f) >= 2 and 'IA na nuvem fora agora' in f[1], json.dumps(f, ensure_ascii=False)[:300])

                # P3F, F17: registrar pela CONVERSA. O pedido com o texto grava UMA linha e a voz confirma; o «tá bom» seguinte não grava. O pedido cortado pela pausa («registrar no diário que») pergunta o que
                # registrar, e a PRÓXIMA frase é a linha (o «tá bom» depois não). Nada vai para a rede (o registro é local).
                def conversa_seq(frases, n_falas):
                    abre(False)
                    pg.evaluate("(qs) => { qs.forEach((q) => window.__falas.push(q)); const B = window.CapitaoBrain; B.speak = (t, fim) => { window.__faladas.push(t); setTimeout(() => fim && fim(), 80); return true; }; window.__n0 = B.loadDiario().length; }", frases)
                    antes = len(estado['pedidos'])
                    pg.click(CONVERSA)
                    try:
                        pg.wait_for_function('(n) => window.__faladas.length >= n', arg=n_falas, timeout=25000)
                    except Exception:
                        pass
                    pg.wait_for_timeout(400)
                    r = pg.evaluate('() => ({ f: window.__faladas, linhas: window.CapitaoBrain.loadDiario().slice(0, window.CapitaoBrain.loadDiario().length - window.__n0).map((e) => e.t) })')
                    pg.keyboard.press('Escape')
                    return r, len(estado['pedidos']) - antes
                r, n = conversa_seq(['registre no diário que saímos da marina às sete', 'tá bom'], 3)
                ok(tela + ': CONVERSA (F17): «registre no diário que…» grava 1 linha com o texto, a voz confirma «Registrado no diário de bordo.» e o «tá bom» seguinte não grava', len(r['f']) >= 3 and r['f'][1] == 'Registrado no diário de bordo.' and r['linhas'] == ['Saímos da marina às sete'], json.dumps(r, ensure_ascii=False)[:400])
                r, n = conversa_seq(['registrar no diário que', 'bom dia'], 3)
                ok(tela + ': CONVERSA (revisão P3F): depois do «o que devo registrar?» a saudação não vira linha do diário (a espera acaba, nada gravado, nada na rede)', len(r['f']) >= 3 and r['f'][1] == 'O que devo registrar no diário?' and r['linhas'] == [] and n == 0, json.dumps([r, n], ensure_ascii=False)[:400])
                r, n = conversa_seq(['registrar no diário que', 'o gerador foi ligado às sete', 'tá bom'], 4)
                ok(tela + ': CONVERSA (F17): o pedido cortado pela pausa pergunta «O que devo registrar no diário?», a próxima frase vira a linha (1) e o «tá bom» depois não grava; nada vai para a rede', len(r['f']) >= 4 and r['f'][1] == 'O que devo registrar no diário?' and r['f'][2] == 'Registrado no diário de bordo.' and r['linhas'] == ['O gerador foi ligado às sete'] and n == 0, json.dumps([r, n], ensure_ascii=False)[:400])

                # P3F (revisão 3): a promessa do «o que devo registrar?» nunca fica no silêncio, e o adiamento não grava. Nada vai para a rede (o registro e o aviso são locais).
                r, n = conversa_seq(['registrar no diário que', 'sem ocorrências'], 3)
                ok(tela + ': CONVERSA (revisão 3 da P3F): depois do «o que devo registrar?», «sem ocorrências» vira a linha (1) e a voz confirma «Registrado no diário de bordo.»; nada na rede', len(r['f']) >= 3 and r['f'][2] == 'Registrado no diário de bordo.' and r['linhas'] == ['Sem ocorrências'] and n == 0, json.dumps([r, n], ensure_ascii=False)[:400])
                r, n = conversa_seq(['registrar no diário que', 'tô pensando aqui'], 3)
                ok(tela + ': CONVERSA (revisão 3 da P3F): a fala que não é nota nem pedido recebe «Não registrei isso…» na voz (não o silêncio, não a IA): 0 linhas, 0 pedidos', len(r['f']) >= 3 and r['f'][2] == 'Não registrei isso. Para registrar, diga registre no diário e o texto.' and r['linhas'] == [] and n == 0, json.dumps([r, n], ensure_ascii=False)[:400])
                r, n = conversa_seq(['registra depois'], 2)
                ok(tela + ': CONVERSA (revisão 3 da P3F): «registra depois» não grava (nem o resumo da telemetria): a voz diz «Certo, nada registrado agora.»; 0 linhas, 0 pedidos', len(r['f']) >= 2 and r['f'][1] == 'Certo, nada registrado agora.' and r['linhas'] == [] and n == 0, json.dumps([r, n], ensure_ascii=False)[:400])

                # Sem a pausa de 0,65 s na CONVERSA (paridade Avanti 1.21.2): a frase final do reconhecedor vai direto ao cérebro;
                # fora da conversa (VOZ→TEXTO) a pausa visual fica. Medido no navegador (performance.now), do fim do ditado à
                # chamada do B.answer com a frase: o piso do VOZ→TEXTO é o setTimeout de 0,65 s da tela, que nunca dispara antes
                # da hora (não depende da carga da máquina); o teto da conversa (200 ms) fica ~15× acima do que a tela leva (~10 ms).
                def atraso(botao):
                    abre()
                    pg.evaluate("""(q) => {
                      const B = window.CapitaoBrain, dit = B.ditado, ans = B.answer;
                      window.__tFim = null; window.__atraso = null; window.__falas.push(q);
                      B.speak = (t, fim) => { window.__faladas.push(t); setTimeout(() => fim && fim(), 80); return true; };
                      B.ditado = (o) => dit(Object.assign({}, o, { fim: (t) => { if (t && window.__tFim == null) window.__tFim = performance.now(); return o.fim(t); } }));
                      B.answer = function (p) { if (p === q && window.__tFim != null && window.__atraso == null) window.__atraso = performance.now() - window.__tFim; return ans.apply(this, arguments); };
                    }""", 'quantas horas tem o gerador')
                    pg.click(botao)
                    try:
                        pg.wait_for_function('() => window.__atraso != null', timeout=20000)
                        if botao == CONVERSA:
                            pg.wait_for_function('() => window.__faladas.length >= 2', timeout=10000)
                    except Exception:
                        pass
                    r = pg.evaluate('() => ({ ms: window.__atraso, faladas: window.__faladas })')
                    pg.keyboard.press('Escape')
                    return r
                rc, rv = atraso(CONVERSA), atraso(VOZ)
                ok(tela + ': CONVERSA: a pergunta ouvida vai ao cérebro sem a pausa de 0,65 s (< 200 ms do fim do ditado) e a resposta é falada', rc['ms'] is not None and rc['ms'] < 200 and len(rc['faladas']) >= 2 and 'gerador' in rc['faladas'][1].lower(), json.dumps(rc, ensure_ascii=False)[:300])
                ok(tela + ': VOZ→TEXTO (fora da conversa) mantém a pausa visual (≥ 600 ms do fim do ditado ao cérebro)', rv['ms'] is not None and rv['ms'] >= 600, json.dumps(rv, ensure_ascii=False)[:300])

                # Voz a 1,15x em TODA fala (abertura e emergência), com o sinal de som para o rosto, e o núcleo com o rosto de
                # partículas: CONVERSA "homem ao mar" com a fala de verdade do cérebro sobre o speechSynthesis de mentira.
                abre()
                try:
                    pg.wait_for_function('() => !!window.CapitaoRosto', timeout=15000)  # vem à parte, com o app ocioso
                except Exception:
                    pass
                tem_rosto = pg.evaluate('() => !!window.CapitaoRosto')
                ok(tela + ': capitao-rosto.js carregado à parte (com o app ocioso)', tem_rosto)
                if tem_rosto:
                    pg.evaluate(SINTESE_FALSA)
                    pg.evaluate("() => { window.__voz.length = 0; window.__falas.push('homem ao mar'); }")
                    pg.click(CONVERSA)
                    try:  # abertura falada, pergunta ouvida, SOS falado inteiro e o microfone de volta
                        pg.wait_for_function("() => { const v = window.__voz, i = v.findIndex((x) => x.estado === 'pensando'); return i >= 0 && v.slice(i).some((x) => x.estado === 'falando' && x.som === true) && v[v.length - 1].estado === 'ouvindo'; }", timeout=25000)
                    except Exception:
                        pass
                    pg.wait_for_timeout(300)
                    sint = pg.evaluate('() => window.__sint')
                    voz = pg.evaluate('() => window.__voz')
                    sos = pg.evaluate("() => { const B = window.CapitaoBrain; return B.route('homem ao mar') === 'sos' ? B.falavel(B.falaCurta(B.answer('homem ao mar', { platform: 'web', commit: false }))) : ''; }")
                    faladas_sos = ' '.join(x['t'] for x in sint[1:])
                    # a velocidade volta do navegador como float32 (1,1499999…); a abertura sai falável ("Capitão i a online")
                    ok(tela + ': voz a 1,15x em toda fala — abertura e emergência (SOS "homem ao mar" falado inteiro)', len(sint) >= 2 and all(abs((x['r'] or 0) - 1.15) < 1e-3 for x in sint) and sint[0]['t'].startswith('Capitão i a online') and sos and len(faladas_sos) >= len(sos) * 0.9, json.dumps(sint, ensure_ascii=False)[:300])
                    fal = [x.get('som') for x in voz if x.get('estado') == 'falando']
                    ok(tela + ': eventos "falando" levam o som (false antes de a voz começar, true no onstart, false no fim do bloco) e as palavras viram "pulso"', fal and all(isinstance(x, bool) for x in fal) and fal[0] is False and True in fal and fal[-1] is False and any(x.get('estado') == 'pulso' for x in voz), json.dumps(fal)[:300])
                    est = pg.evaluate("() => ({ on: !!document.querySelector('.cpz.on'), tela: !!document.querySelector('.cpz canvas.cpz-tela'), rosto: !!(window.CapitaoVoz.rosto && window.CapitaoVoz.rosto()), op: window.__rostoOp || null, est: window.__estRosto, som: window.__somRosto, palco: !!document.querySelector('.cpz .cpz-palco .cpz-btn'), velho: !!document.querySelector('.cpz svg circle') })")
                    op = est['op'] or {}
                    ok(tela + ': o núcleo abre com o canvas do rosto e o CapitaoRosto criado (dprMax 2, fpsMax 60, crescer 0,35), sem os anéis antigos', est['on'] and est['tela'] and est['rosto'] and est['palco'] and not est['velho'] and op.get('dprMax') == 2 and op.get('fpsMax') == 60 and op.get('crescer') == 0.35, json.dumps(est, ensure_ascii=False)[:300])
                    ok(tela + ': o rosto segue a conversa (falando, ouvindo, pensando) e recebe o som da voz', all(e in est['est'] for e in ('falando', 'ouvindo', 'pensando')) and True in est['som'] and False in est['som'], json.dumps(est, ensure_ascii=False)[:300])
                    i = pg.evaluate('() => window.__voz.length')
                    pg.keyboard.press('Escape')
                    pg.wait_for_timeout(1200)
                    fim = pg.evaluate("(i) => ({ on: !!document.querySelector('.cpz.on'), depois: window.__voz.slice(i).map((x) => x.estado), est: window.__estRosto.slice(-1)[0] })", i)
                    ok(tela + ': Esc encerra a conversa: o núcleo some, o rosto vai para "livre" e o microfone não volta', not fim['on'] and fim['est'] == 'livre' and all(e == 'livre' for e in fim['depois']), json.dumps(fim, ensure_ascii=False))
                    # Pressão de óleo (emergência) também a 1,15x
                    pg.evaluate("() => { window.__sint.length = 0; const B = window.CapitaoBrain; B.speak(B.falaCurta(B.answer('a pressão de óleo caiu', { platform: 'web', commit: false }))); }")
                    pg.wait_for_timeout(1500)
                    sint = pg.evaluate('() => window.__sint')
                    ok(tela + ': voz a 1,15x também no passo a passo da pressão de óleo', sint and all(abs((x['r'] or 0) - 1.15) < 1e-3 for x in sint), json.dumps(sint, ensure_ascii=False)[:300])

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
                # P4H (F6): o toque numa pergunta do FAQ (de dentro do app, com a IA ligada) responde com o item, o código e a fonte e NÃO chama a IA (a Fase 6 liga, com o item como trecho [1]);
                # o cartão de emergência (EM-06) abre local, sem nenhum pedido ao Worker
                for cod in ('MO-02', 'EM-06'):
                    t, n = por_link(FAQ_ITENS[cod]['pergunta'], interno=True, extra='&faq=' + cod)
                    ok(tela + ': o toque no FAQ (#q=…&faq=%s, de dentro do app, IA ligada) mostra o item com o código e a fonte e não chama a IA' % cod, n == 0 and ('Fonte: FAQ dos equipamentos ' + cod) in t and TEXTO_IA not in t, 'pedidos=%d · %s' % (n, t[-160:]))
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
