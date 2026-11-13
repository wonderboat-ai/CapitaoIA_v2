"""Teste de ponta a ponta da IA na nuvem nas telas de chat (Main e H2), com o Worker SIMULADO — não gasta cota.

Confere que a IA entra quando a resposta local não basta (SEM DADOS, trecho do guia, pergunta sobre o app — "Oque você faz?")
e nunca em resposta pronta ou só num "oi"; que o pedido leva a ficha de bordo (sem coordenadas) e o histórico da conversa;
que sem a CHAVE_APP no aparelho nada vai para a rede e a linha da fonte diz por quê (com o botão "Ativar IA na nuvem");
que erro do proxy mantém a resposta local com o motivo; que "SEM DADOS" da IA mantém o trecho do guia mas troca o SEM DADOS
genérico; que a resposta entra logo depois da pergunta dela; que na CONVERSA por voz a IA responde e a resposta dela é a
falada; que na CONVERSA a pergunta ouvida vai ao cérebro sem a pausa de 0,65 s e o VOZ→TEXTO a mantém; que link de fora
(#q=) não gasta a cota e link de dentro do app usa a IA; que o indicador some ao fim;
que a voz vai a 1,15x em toda fala (abertura, SOS e óleo) e os eventos "falando" levam o som; que o núcleo abre com os anéis
pintados no canvas (cor por estado, ∞ no centro, só reage ao som com som true), o HUD lê o quadro do instante e, em alerta, mostra só
a instrução do plotter, e o Esc encerra; e que o login não leva a chave do endereço para o ?next=.

    python -X utf8 testes/chat_ia.py        (sobe um servidor local próprio; o React vem do próprio site, assets/vendor)
"""
import functools
import http.server
import json
import os
import re
import sys
import threading
import time
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
# Fase 5 (decisão 5): onde a tela escreve «IA na nuvem» (sem diferença de caixa: o aviso grande sai em maiúsculas): cada folha do DOM com o texto, se é a linha da fonte («Fonte: …»), o botão de uma resposta
# (data-home=acao: «Ativar IA na nuvem») e o tamanho da letra — e o tamanho da letra do texto da resposta (a maior letra da mensagem), para a comparação «letra pequena»
ONDE_IA = """() => { const m = [...document.querySelectorAll('[data-home=msg][data-papel=bot]')].pop();
  return { texto: m ? Math.max(...[...m.querySelectorAll('*')].filter((e) => !e.children.length && (e.innerText || '').trim()).map((e) => parseFloat(getComputedStyle(e).fontSize))) : 0, bot: m ? m.innerText : '',
    onde: [...document.querySelectorAll('body *')].filter((e) => !e.children.length && !/^(SCRIPT|STYLE|TEMPLATE|NOSCRIPT)$/.test(e.tagName) && e.getClientRects().length && /ia na nuvem/i.test(e.innerText || '')).map((e) => ({ t: e.innerText.trim().slice(0, 600), fonte: /^Fonte:/.test(e.innerText.trim()), acao: !!e.closest('[data-home=acao]'), px: parseFloat(getComputedStyle(e).fontSize) })) }; }"""
# a marca da janela de conversa em emergência (capitao-app.js): encerrada no fim de cada conferência que a abre (a janela vale por aba)
FECHA_JANELA = "() => { window.CapitaoEmergencia.marca(Date.now() - 1000); sessionStorage.removeItem('capitao.emergenciaAte'); }"
VOZ = '[aria-label="Falar — a pergunta é transcrita e respondida em texto e voz"]'  # VOZ (web) e VOZ→TEXTO (app)
# Microfone e voz de mentira para a CONVERSA: o reconhecedor "ouve" as frases de window.__falas (uma por vez) e a fala só
# registra o texto em window.__faladas. Os eventos do núcleo de voz ficam em window.__voz.
VOZ_FALSA = r"""(() => {
  // o <head> das telas roda o capitao-brain.js DUAS vezes e a 2ª cópia assume o window.CapitaoBrain: com a máquina carregada ela chega depois de a tela estar pronta (~200 ms) e leva embora a fala de mentira
  // posta na 1ª. O abre() espera as duas (window.__cerebros >= 2) antes de qualquer conferência mexer no B.speak.
  let B_; window.__cerebros = 0;
  Object.defineProperty(window, 'CapitaoBrain', { configurable: true, get() { return B_; }, set(v) { B_ = v; window.__cerebros++; } });
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
  window.__sint = [];
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

# O núcleo de anéis (Fase 5, F27: capitao-voz.js, canvas) é espiado a cada evento 'capitao-voz', DEPOIS de o núcleo tratar o evento
# (microtarefa): o estado dele (CapitaoVoz.nucleo().estado()) e o texto do HUD da direita ficam em window.__nucleo.
ESPIA_NUCLEO = r"""(() => {
  window.__nucleo = [];
  window.addEventListener('capitao-voz', (e) => {
    const d = e.detail || {};
    Promise.resolve().then(() => {
      try {
        const V = window.CapitaoVoz, n = V && V.nucleo ? V.nucleo().estado() : null, h = document.querySelector('.cpz .cpz-tr');
        if (n) window.__nucleo.push({ ev: d.estado, texto: d.texto || '', evAlerta: d.alerta, estado: n.estado, som: n.som, alerta: n.alerta, ligado: n.ligado, hud: h ? h.innerText : '' });
      } catch (x) {}
    });
  });
})()"""

# O canvas pintado de verdade: quadro(t) fixa o quadro do instante t e a amostra lê os pixels da caixa do palco — no anel graduado
# (0,90 a 0,98 do raio: só as marcas, na cor do estado) e no centro (o ∞ da marca, pixels claros e opacos sobre o disco escuro).
PINTURA_NUCLEO = r"""async () => {
  const ev = (d) => window.dispatchEvent(new CustomEvent('capitao-voz', { detail: d })), N = () => window.CapitaoVoz.nucleo(), out = {};
  const tela = () => document.querySelector('.cpz canvas.cpz-tela'), espera = (ms) => new Promise((r) => setTimeout(r, ms));
  const amostra = () => {
    const n = N().estado(), g = tela().getContext('2d'), k = n.razao, R = n.raio * k, x0 = Math.round(n.x * k), y0 = Math.round(n.y * k), L = Math.ceil(R) + 2;
    const im = g.getImageData(x0 - L, y0 - L, 2 * L, 2 * L).data;
    let anel = 0, r = 0, v = 0, b = 0, centro = 0;
    for (let y = 0; y < 2 * L; y++) for (let x = 0; x < 2 * L; x++) {
      const dx = x - L, dy = y - L, dist = Math.sqrt(dx * dx + dy * dy) / R, i = (y * 2 * L + x) * 4;
      if (dist > 0.9 && dist < 0.98 && im[i + 3] > 150) { anel++; r += im[i]; v += im[i + 1]; b += im[i + 2]; }
      if (Math.abs(dx) < 0.25 * R && Math.abs(dy) < 0.1 * R && im[i + 3] > 240 && im[i] + im[i + 1] + im[i + 2] > 300) centro++;
    }
    return { anel: anel, cor: anel ? [Math.round(r / anel), Math.round(v / anel), Math.round(b / anel)] : null, centro: centro };
  };
  ev({ estado: 'ouvindo', texto: '', alerta: false });
  await espera(450);
  out.vivo = N().estado();                                   // camada ligada: o laço (um requestAnimationFrame) roda e pinta
  N().quadro(1.6); out.ouvindo = amostra(); const u1 = tela().toDataURL();
  N().quadro(1.6); out.igual = tela().toDataURL() === u1;    // o mesmo instante dá o mesmo quadro
  N().quadro(2.9); out.muda = tela().toDataURL() !== u1;     // outro instante, outro quadro (os anéis giram)
  const q0 = N().estado().quadros; await espera(250); out.parado = N().estado().quadros === q0 && !N().estado().laco;   // quadro(t) deixa o núcleo parado
  ev({ estado: 'pensando', texto: 'x', segura: true }); N().quadro(1.6); out.pensando = amostra();
  ev({ estado: 'falando', texto: 'Gerador ligado.', som: false, alerta: false }); N().quadro(0.2); out.semSom = N().estado().energia;
  ev({ estado: 'pulso' }); out.pulsoSemSom = N().estado().energia;
  ev({ estado: 'falando', texto: 'Gerador ligado.', som: true, alerta: false }); N().quadro(0.2); out.comSom = N().estado().energia; out.falando = amostra();
  ev({ estado: 'pulso' }); out.pulsoComSom = N().estado().energia;
  ev({ estado: 'livre' }); out.livre = N().estado().energia;
  window.CapitaoVoz.esconde();
  const q1 = N().estado().quadros; await espera(350);
  out.escondida = { on: !!document.querySelector('.cpz.on'), laco: N().estado().laco, quadros: N().estado().quadros - q1, inerte: document.querySelector('.cpz').inert === true };
  out.rosto = !!window.CapitaoVoz.rosto;   // a API antiga saiu com o rosto
  return out;
}"""

# O HUD vivo: com a camada ligada lê o quadro do instante (CapitaoAgora: a fonte e os formatadores das telas) a cada 1 s, em nós Text; com
# `alerta` no evento ou com a janela de emergência valendo, só a instrução do plotter; com simulacao:false e sem leitura, o texto do modo real.
HUD_NUCLEO = r"""async () => {
  const ev = (d) => window.dispatchEvent(new CustomEvent('capitao-voz', { detail: d })), out = {}, espera = (ms) => new Promise((r) => setTimeout(r, ms));
  const A = window.CapitaoAgora, f = A.fmt.campo, D = window.CapitaoDados, caixa = () => document.querySelector('.cpz .cpz-tr'), hud = () => caixa().innerText;
  const esperado = () => { const I = A.instante(); return [I.hora, A.fmt.coord(I.q.lat, I.q.lon), 'SOG ' + f(I.q, 'sog_nos') + ' NÓS', 'RPM ' + f(I.q, 'motor_bb_rpm') + ' · ' + f(I.q, 'motor_be_rpm'), 'DIESEL ' + f(I.q, 'diesel_litros') + ' L (' + A.fmt.nb(I.calc.diesel_pct, 1) + ' %)'].join('\n'); };
  ev({ estado: 'ouvindo', texto: '', alerta: false });
  out.vivo = hud(); out.esperado = esperado();
  out.sog = 'SOG ' + f(A.instante().q, 'sog_nos') + ' NÓS'; out.diesel = out.esperado.split('\n')[4];
  out.pagina = document.getElementById('dc-root').innerText.replace(/\s+/g, ' ');
  // o tique: outro instante do replay → o HUD o mostra em até 1 s, sem evento de voz, trocando só o .data dos MESMOS nós
  const nos = [...caixa().childNodes]; let filhos = 0, dados = 0;
  const conta = (l) => l.forEach((m) => { if (m.type === 'childList') filhos++; else dados++; });
  const mo = new MutationObserver(conta); mo.observe(caixa(), { childList: true, subtree: true, characterData: true });
  window.CapitaoReplay.fixar('75');
  await espera(1300);
  out.depois = hud(); out.esperado2 = esperado(); conta(mo.takeRecords()); mo.disconnect();
  out.mesmosNos = caixa().childNodes.length === nos.length && [...caixa().childNodes].every((n, i) => n === nos[i]); out.filhos = filhos; out.dados = dados;
  window.CapitaoReplay.fixar('60');
  await espera(50);
  // alerta no evento (a resposta falada é de emergência), sem a janela
  ev({ estado: 'falando', texto: 'Emergência — abra o SOS.', som: true, alerta: true }); out.alerta = hud();
  ev({ estado: 'falando', texto: '2. Colete em todos.', som: true, alerta: false }); out.alertaSegue = hud();   // as outras linhas da MESMA fala
  ev({ estado: 'livre' }); ev({ estado: 'ouvindo', texto: '', alerta: false }); out.volta = hud(); out.esperado3 = esperado();
  // a janela de conversa em emergência valendo (CapitaoEmergencia), com o evento sem alerta
  window.CapitaoEmergencia.marca(); out.janela = hud();
  ev({ estado: 'falando', texto: 'Gerador ligado.', som: true, alerta: false }); out.janelaFala = hud();
  window.CapitaoEmergencia.zera(); out.semJanela = hud();
  // modo real (simulacao:false) e sem leitura nenhuma: o texto do modo real continua
  const q = D.snapshot.quadro; D.simulacao = false; delete D.snapshot.quadro;
  ev({ estado: 'ouvindo', texto: '', alerta: false }); out.real = hud();
  D.simulacao = true; D.snapshot.quadro = q;
  out.plotter = D.protocolos.hud;
  window.CapitaoVoz.esconde();
  return out;
}"""


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
                ctx.add_init_script(ESPIA_NUCLEO)
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

                def espera_pedido(antes, prazo=8.0):
                    # espera o PEDIDO chegar ao Worker simulado (não o relógio): a tela adia a pergunta em ~650 ms (setTimeout do ask) e o «Fonte:» da proposta do relato já está na tela, então
                    # espera_resposta() sozinho sairia antes do pedido (corrida: reprovava ~50% das vezes). Sem pedido no prazo, segue (a conferência que vem depois acusa).
                    t0 = time.time()
                    while len(estado['pedidos']) <= antes and time.time() - t0 < prazo:
                        pg.wait_for_timeout(50)

                def prepara(chave):
                    pg.goto(base + 'README.md')
                    pg.evaluate("(c) => { if (c) localStorage.setItem('capitao.ia.chave.v1', 'chave-de-teste'); else localStorage.removeItem('capitao.ia.chave.v1'); }", chave)

                def abre(chave=True, modo='ok'):
                    estado['modo'] = modo
                    prepara(chave)
                    pg.goto(base + tela + '.dc.html')
                    pg.wait_for_function(PRONTA, timeout=20000)
                    pg.wait_for_selector(campo, timeout=15000)
                    try:
                        pg.wait_for_function('() => window.__cerebros >= 2', timeout=8000)   # as duas cópias do cérebro (ver o VOZ_FALSA)
                    except Exception:
                        pass

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
                espera_pedido(antes)
                espera_resposta()
                ped = estado['pedidos'][-1] if len(estado['pedidos']) > antes else {}
                ok(tela + ': o botão «O que verificar?» do relato vai à IA (1 pedido, a pergunta pronta com o relato, a leitura de agora) sem navegar nem gravar no diário', len(estado['pedidos']) == antes + 1 and ped.get('pergunta', '').startswith('O que verificar') and 'desligou sozinho' in ped.get('pergunta', '') and bool(ped.get('contexto'))
                   and tela in pg.url and pg.evaluate("() => localStorage.getItem('capitao.diario.v1')") is None, ped.get('pergunta', '')[:80])
                # Fase 4 (P4G, revisão final 4ª rodada, trava 10): a pessoa que some, não volta ou não se acha é emergência LOCAL: com a chave ligada e o replay fixado em 60 s, a pergunta (a que foi nadar, a que sai de caiaque, a que
                # «não está aqui, estava na popa») não faz pedido nenhum ao Worker, abre com a instrução de segurança e não traz a situação de bordo (SOG, proa) que o fallback levava à IA
                for q in ('ela foi nadar e não voltou', 'o Pedro saiu de caiaque e não voltou', 'meu filho não está aqui, estava na popa agora há pouco', 'quem foi de caiaque não volta', 'um de nós sumiu', 'cadê o Pedro? ninguém vê',
              'o menino está nadando longe demais', 'meu filho está longe do barco', 'a Letícia ficou para trás na água', 'meu filho estava na popa e agora não está'):   # (os 3 da 5ª rodada, achado 7; os 4 últimos: 6ª rodada, achados 1 e 7)
                    t, n, _ = digita(q)
                    jan = pg.evaluate("() => window.CapitaoEmergencia.valendo()")
                    ok(tela + ': a pessoa perdida «%s» é emergência local: nenhum pedido ao Worker, a instrução de segurança, a janela de 15 min marcada e sem a situação de bordo' % q, n == 0 and 'Emergência' in t and TEXTO_IA not in t and 'Situação de bordo' not in t and jan, 'pedidos=%d · janela=%s · %s' % (n, jan, t[-200:]))
                    pg.evaluate("() => { window.CapitaoEmergencia.marca(Date.now() - 1000); sessionStorage.removeItem('capitao.emergenciaAte'); }")   # (a janela vale por aba: as conferências de baixo partem sem ela)
                # Fechamento do grupo home (P4G, 2ª instância; pendentes 1 e 7): a pessoa de um substantivo que NENHUMA lista conhece (o dono do barco, o técnico, as moças) ou escrita errada (sumio) ou vista na água (boiando) é emergência LOCAL pela
                # ESTRUTURA do cérebro: nenhum pedido ao Worker, a instrução de segurança, a janela marcada — e a pergunta de dado DEPOIS da água (o pendente 8) é a instrução do plotter, sem SOG, proa nem coordenada, sem pedido ao Worker
                # (2ª rodada de correção do fechamento: o sujeito SEM substantivo («os nossos», «dois»), a cabeça de 2 letras («minha vó», «o DJ»), o nome sem artigo («Tuca está boiando»), a queda sem destino («o grumete caiu») e o que a onda faz («a onda levou o Pedro»))
                for q in ('o dono do barco sumiu', 'meu filho sumio', 'avistei uma pessoa boiando', 'o técnico sumiu', 'as moças sumiram', 'os nossos sumiram', 'dois sumiram', 'o DJ sumiu', 'minha vó sumiu', 'Tuca está boiando', 'o grumete caiu', 'a onda levou o Pedro',
                          'o Marcão sumiu', 'o de óculos sumiu', 'vejo uma cabeça na água', 'foi nadar e não voltou', 'o Pedro foi mergulhar no sábado e não voltou',
                          'man overboard', 'vi o de óculos cair no mar', 'o bote virou com dois dentro'):   # (3ª rodada de correção, parte final: o inglês, o objeto de «vi» que cai, o bote que vira com gente dentro; antes: o apelido em -cão, o «o de óculos», a água sem verbo de queda, o sujeito oculto, a água que o sábado não derruba)
                    t, n, _ = digita(q)
                    jan = pg.evaluate("() => window.CapitaoEmergencia.valendo()")
                    ok(tela + ': a pessoa aberta «%s» é emergência local (a estrutura, não a lista): nenhum pedido ao Worker, a instrução de segurança, a janela de 15 min marcada e sem a situação de bordo' % q, n == 0 and 'Emergência' in t and TEXTO_IA not in t and 'Situação de bordo' not in t and jan, 'pedidos=%d · janela=%s · %s' % (n, jan, t[-200:]))
                    t, n, _ = digita('qual a posição?')
                    u = pg.evaluate("() => { const m = document.querySelectorAll('[data-home=msg][data-papel=bot]'); return m.length ? m[m.length - 1].innerText : ''; }")
                    ok(tela + ': depois de «%s», a pergunta «qual a posição?» é a instrução do plotter (a janela vale): nenhum pedido ao Worker, sem SOG, proa nem coordenada' % q, n == 0 and 'LEIA NO PLOTTER' in u and TEXTO_IA not in t and not re.search(r'\bSOG\b|\d+,\d+ nós|\bproa \d', u) and not confere.R_COORD.search(u), 'pedidos=%d · %s' % (n, u[-200:]))
                    pg.evaluate("() => { window.CapitaoEmergencia.marca(Date.now() - 1000); sessionStorage.removeItem('capitao.emergenciaAte'); }")
                # 6ª rodada: a REDE de pessoa — o que a rota sos não toma (o pronome, o nome com a escala, «na proa: falta o marinheiro», a contagem que não bate) nunca vai à IA nem a uma rota de dado: o fallback seguro (a instrução do SOS na 1ª linha,
                # sem a situação de bordo, sem a janela)
                for q in ('ele sumiu', 'o Pedro não está mais no barco', 'na proa: falta o marinheiro', 'somos oito mas só contei sete', 'o imediato não aparece', 'o cliente sumiu', 'o fiscal sumiu',
                          'não tem o Pedro a bordo', 'voltaram só três e eram quatro', 'perdemos os nossos', 'procurei valdemar no barco inteiro e nada', 'não tenho notícia do Pedro desde ontem',
                          'sem o supervisor a bordo', 'my son is missing', 'procuramos meu amigo'):   # (parte final: o «sem» + o sujeito aberto + o lugar de bordo, o inglês que só avisa de um sumiço, o possessivo da busca)
                    #   # (3ª rodada de correção: a ausência com a pessoa explícita, a contagem sem substantivo, o possuidor sem cabeça como objeto, o nome raro em minúscula)   # (os 2 últimos: a pessoa que também é item de dado — a ESPERA, 2ª rodada de correção do fechamento)
                    t, n, _ = digita(q)
                    jan = pg.evaluate("() => window.CapitaoEmergencia.valendo()")
                    # (a resposta é a ÚLTIMA mensagem do Capitão: a Main mostra a leitura de bordo — SOG, proa — no cabeçalho, fora da conversa)
                    u = pg.evaluate("() => { const m = document.querySelectorAll('[data-home=msg][data-papel=bot]'); return m.length ? m[m.length - 1].innerText : ''; }")
                    ok(tela + ': a pessoa da rede «%s» não vai à IA nem a uma rota de dado: o fallback seguro (a instrução do SOS, sem a situação de bordo nem coordenada, sem a janela)' % q, n == 0 and 'Se há pessoa no mar ou sumida' in u and TEXTO_IA not in t and 'Situação de bordo' not in u and not re.search(r'\bSOG\b|\d+,\d+ nós|\bproa \d', u) and not jan, 'pedidos=%d · janela=%s · %s' % (n, jan, u[-200:]))
                # 3ª rodada de correção do fechamento: a ROTINA que a rede tomava por socorro (o dado que «cai», a cidade, a milha, o que o outro disse) tem a resposta da rota (local, sem o Worker) e nunca a instrução do SOS nem a janela
                for q in ('a autonomia caiu depois do abastecimento?', 'falta diesel pra chegar em Itajaí?', 'quantas milhas faltam?', 'o Pedro disse que o motor não responde'):
                    t, n, _ = digita(q)
                    jan = pg.evaluate("() => window.CapitaoEmergencia.valendo()")
                    u = pg.evaluate("() => { const m = document.querySelectorAll('[data-home=msg][data-papel=bot]'); return m.length ? m[m.length - 1].innerText : ''; }")
                    ok(tela + ': a rotina «%s» tem a resposta da rota, no aparelho: nenhum pedido ao Worker, sem a instrução do SOS e sem a janela de 15 min' % q, n == 0 and 'Se há pessoa no mar ou sumida' not in u and 'Emergência' not in u and u.strip() != '' and not jan, 'pedidos=%d · janela=%s · %s' % (n, jan, u[-200:]))
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
                # (decisões 3 e 5: na simulação o «SEM DADOS» da IA é rótulo — o filtro de saída do cliente o barra, com a falha vazia — e a tela fica com a resposta local, sem o rótulo e sem motivo; a troca
                # do texto genérico pelo «SEM DADOS» da IA é do modo real e roda mais abaixo, na passada com simulacao:false)
                t, n, _ = digita('como se faz um nó lais de guia?', modo='semdados')
                ok(tela + ': simulação: o "SEM DADOS" da IA é barrado pelo filtro de saída: 1 pedido, a tela fica com a resposta local, sem o rótulo e sem motivo', n == 1 and FALLBACK_LOCAL in t and 'os trechos não respondem' not in t
                   and re.search(r'\bSEM DADOS\b', t) is None and 'IA na nuvem fora' not in t and pg.evaluate("() => window.CapitaoIA.falha()") == '', 'pedidos=%d · %s' % (n, t[-200:]))
                t, n, _ = digita('como ligar o gerador?', chave=False)
                ok(tela + ': sem a CHAVE_APP no aparelho nada vai para a rede (fica o trecho local)', n == 0 and TEXTO_IA not in t and 'PARTIDA' in t, 'pedidos=%d' % n)
                t, n, _ = digita('como se faz um nó lais de guia?', chave=False)
                ok(tela + ': sem a CHAVE_APP, a fonte diz "IA na nuvem desligada neste aparelho" e oferece "Ativar IA na nuvem"', n == 0 and 'IA na nuvem desligada neste aparelho' in t and pg.query_selector('a[href="#ia=ativar"]') is not None, t[-300:])
                # Fase 5 (decisão 5; PROMPT «Mudanças nos testes», linha 5): com a simulação (o capitao-dados.js como está) a falha OPERACIONAL da IA não vira aviso grande nem é falada: o motivo fica SÓ na linha da
                # fonte, em letra pequena, e o botão «Ativar IA na nuvem» continua na resposta. O texto de antes (o aviso grande, o motivo falado) roda mais abaixo, na passada com simulacao:false.
                def so_na_fonte(motivo, botao):
                    """O motivo aparece uma vez, na linha «Fonte: …» da última resposta, em letra menor que a do texto; fora dela, «IA na nuvem» só no botão da resposta (nenhum aviso grande)."""
                    o = pg.evaluate(ONDE_IA)
                    com = [x for x in o['onde'] if motivo in x['t']]
                    resto = [x for x in o['onde'] if not x['fonte'] and not x['acao']]
                    return (len(com) == 1 and com[0]['fonte'] and 0 < com[0]['px'] < o['texto'] and not resto and any(x['acao'] for x in o['onde']) == botao and 'IA NA NUVEM' not in o['bot']), o
                bom, o = so_na_fonte('IA na nuvem desligada neste aparelho', True)
                ok(tela + ': simulação: sem a CHAVE_APP não há aviso grande ("IA NA NUVEM NÃO ATIVADA…"): o motivo fica só na linha da fonte, em letra pequena, e o botão "Ativar IA na nuvem" continua',
                   pg.evaluate('() => window.CapitaoDados.simulacao') is True and 'IA NA NUVEM NÃO ATIVADA' not in t and bom, json.dumps(o['onde'], ensure_ascii=False)[:300])
                t, n, livre = digita('como ligar o gerador?', modo='erro')
                ok(tela + ': erro do proxy mantém a resposta local com o motivo (e o indicador some)', n == 1 and TEXTO_IA not in t and 'PARTIDA' in t and 'IA na nuvem fora agora' in t and livre, 'pedidos=%d' % n)
                bom, o = so_na_fonte('IA na nuvem fora agora', False)
                ok(tela + ': simulação: o erro do proxy não vira aviso: o motivo fica só na linha da fonte, em letra pequena', bom, json.dumps(o['onde'], ensure_ascii=False)[:300])
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

                # Fase 5 (decisão 5): na simulação a voz não fala a falha da IA (nem «não está ativada», nem o motivo do servidor): fala só a resposta local; o motivo fica na linha da fonte da conversa escrita, com o botão
                R_FALHA_FALADA = re.compile(r'IA na nuvem|não está ativada|Ativar IA|chave', re.I)
                f, n = conversa('o que você faz', chave=False)
                bom, o = so_na_fonte('IA na nuvem desligada neste aparelho', True)
                ok(tela + ': simulação: CONVERSA sem a chave: fala o que o Capitão faz (não repete a abertura) e NÃO fala da IA; nada vai para a rede; o motivo fica na linha da fonte, com o botão', n == 0 and len(f) >= 2 and f[1].startswith('Respondo sobre telemetria')
                   and not any(R_FALHA_FALADA.search(x) for x in f) and bom, json.dumps([f, o['onde']], ensure_ascii=False)[:400])
                f, n = conversa('Capitão, diagnóstico')
                ok(tela + ': CONVERSA: "Capitão, diagnóstico" fala se a IA está ligada e o resultado do teste da chave (sem gastar a cota)', n == 1 and len(f) >= 2 and 'IA na nuvem: LIGADA' in f[1] and 'Chave aceita pelo servidor' in f[1], json.dumps(f, ensure_ascii=False)[:300])
                f, n = conversa('como se faz um nó lais de guia', modo='erro')
                bom, o = so_na_fonte('IA na nuvem fora agora', False)
                ok(tela + ': simulação: CONVERSA com erro do servidor: a voz fala só a resposta local (não o motivo); o motivo fica na linha da fonte', n == 1 and len(f) >= 2 and f[1].strip() and not any(R_FALHA_FALADA.search(x) for x in f) and bom, json.dumps([f, o['onde']], ensure_ascii=False)[:400])

                # Contrato com o cliente da IA (Fase 6): a resposta filtrada (ou o 502 com `parou`) chega como null com a falha VAZIA: a tela fica com a resposta local, sem nota na linha da fonte, sem aviso e sem fala a mais
                NULA = "() => { const IA = window.CapitaoIA; window.__nulas = 0; IA.ativa = () => true; IA.perguntar = () => { window.__nulas++; return Promise.resolve(null); }; IA.falha = () => ''; }"
                abre()
                pg.evaluate(NULA)
                t, n, livre = envia('como ligar o gerador?')
                o = pg.evaluate(ONDE_IA)
                ok(tela + ': null com a falha vazia (resposta filtrada): fica a resposta local com a fonte dela, sem nota, sem aviso e sem botão (e o indicador some)', pg.evaluate('() => window.__nulas') == 1 and 'PARTIDA' in o['bot'] and 'Fonte: Guia de bordo' in o['bot'] and not o['onde'] and livre, json.dumps(o, ensure_ascii=False)[:300])
                abre()
                pg.evaluate(NULA)
                pg.evaluate("() => { window.__falas.push('como se faz um nó lais de guia'); const B = window.CapitaoBrain; B.speak = (t, fim) => { window.__faladas.push(t); setTimeout(() => fim && fim(), 80); return true; }; window.__local = B.falaCurta(B.answer('como se faz um nó lais de guia', { platform: 'web', commit: false })); }")
                pg.click(CONVERSA)
                try:
                    pg.wait_for_function('() => window.__faladas.length >= 2', timeout=20000)
                except Exception:
                    pass
                r = pg.evaluate('() => ({ f: window.__faladas, n: window.__nulas, local: window.__local })')
                pg.keyboard.press('Escape')
                ok(tela + ': CONVERSA: null com a falha vazia: a voz fala só a resposta local, nada sobre a IA', r['n'] == 1 and len(r['f']) >= 2 and r['f'][1] == r['local'] and not any(R_FALHA_FALADA.search(x) for x in r['f']), json.dumps(r, ensure_ascii=False)[:300])

                # A passada com simulacao:false (PROMPT «Mudanças nos testes», linhas 5 e 6): a rota acrescenta «window.CapitaoDados.simulacao = false;» ao fim do capitao-dados.js e o texto de antes vale inteiro —
                # o aviso grande sem a chave, a voz que diz que a IA não está ativada e o motivo do servidor falado
                def sem_simulacao(route):
                    corpo = open(os.path.join(RAIZ, 'capitao-dados.js'), encoding='utf-8').read() + '\nwindow.CapitaoDados.simulacao = false;\n'
                    return route.fulfill(status=200, content_type='text/javascript; charset=utf-8', body=corpo)
                pg.route('**/capitao-dados.js*', sem_simulacao)
                t, n, _ = digita('como se faz um nó lais de guia?', chave=False)
                ok(tela + ': simulacao:false: a rota de teste desliga a simulação na página (D.simulacao === false)', pg.evaluate('() => window.CapitaoDados.simulacao') is False)
                ok(tela + ': simulacao:false: sem a CHAVE_APP, a fonte diz "IA na nuvem desligada neste aparelho" e oferece "Ativar IA na nuvem"', n == 0 and 'IA na nuvem desligada neste aparelho' in t and pg.query_selector('a[href="#ia=ativar"]') is not None, t[-300:])
                ok(tela + ': simulacao:false: sem a CHAVE_APP, aviso grande na tela "IA NA NUVEM NÃO ATIVADA NESTE APARELHO"', 'IA NA NUVEM NÃO ATIVADA NESTE APARELHO' in t, t[-300:])
                t, n, livre = digita('como ligar o gerador?', modo='erro')
                ok(tela + ': simulacao:false: erro do proxy mantém a resposta local com o motivo (e o indicador some)', n == 1 and TEXTO_IA not in t and 'PARTIDA' in t and 'IA na nuvem fora agora' in t and livre, 'pedidos=%d' % n)
                t, n, _ = digita('como se faz um nó lais de guia?', modo='semdados')
                ok(tela + ': simulacao:false: "SEM DADOS" da IA troca o SEM DADOS genérico da tela', n == 1 and 'os trechos não respondem' in t and FALLBACK_LOCAL not in t, 'pedidos=%d · %s' % (n, t[-200:]))
                f, n = conversa('o que você faz', chave=False)
                ok(tela + ': simulacao:false: CONVERSA sem a chave: fala o que o Capitão faz (não repete a abertura) e que a IA não está ativada; nada vai para a rede', n == 0 and len(f) >= 2 and f[1].startswith('Respondo sobre telemetria') and 'não está ativada neste aparelho' in f[1], json.dumps(f, ensure_ascii=False)[:300])
                f, n = conversa('como se faz um nó lais de guia', modo='erro')
                ok(tela + ': simulacao:false: CONVERSA com erro do servidor: a voz fala o motivo ("IA na nuvem fora agora…")', n == 1 and len(f) >= 2 and 'IA na nuvem fora agora' in f[1], json.dumps(f, ensure_ascii=False)[:300])
                pg.unroute('**/capitao-dados.js*', sem_simulacao)

                # A marca da janela de conversa em emergência (trava 10; window.CapitaoEmergencia, capitao-app.js): «homem ao mar» no chat escrito e na CONVERSA deixa a marca valendo (15 min, no sessionStorage) — é ela que
                # a faixa global de alerta e o HUD leem para não mostrar a SOG —; nada vai à IA; o ENCERRAR da conversa a zera
                LE_MARCA = "() => { const E = window.CapitaoEmergencia; return { v: E.valendo(), falta: E.ate() - Date.now(), ss: sessionStorage.getItem('capitao.emergenciaAte') }; }"
                abre()
                m0 = pg.evaluate(LE_MARCA)
                t, n, _ = envia('homem ao mar')
                m = pg.evaluate(LE_MARCA)
                ok(tela + ': marca de emergência: «homem ao mar» no chat deixa a marca valendo (15 min, no sessionStorage), sem pedido ao Worker', m0['v'] is False and m['v'] is True and 14 * 60e3 < m['falta'] <= 15 * 60e3 and m['ss'] is not None and n == 0 and 'Emergência' in t, json.dumps([m0, m, n]))
                pg.evaluate(FECHA_JANELA)
                abre()
                pg.evaluate("() => { window.__falas.push('homem ao mar'); const B = window.CapitaoBrain; B.speak = (t, fim) => { window.__faladas.push(t); setTimeout(() => fim && fim(), 80); return true; }; }")
                antes = len(estado['pedidos'])
                m0 = pg.evaluate(LE_MARCA)
                pg.click(CONVERSA)
                try:
                    pg.wait_for_function('() => window.__faladas.length >= 2 && window.CapitaoEmergencia.valendo()', timeout=20000)
                except Exception:
                    pass
                m = pg.evaluate(LE_MARCA)
                f = pg.evaluate('() => window.__faladas')
                pg.keyboard.press('Escape')
                pg.wait_for_timeout(400)
                m2 = pg.evaluate(LE_MARCA)
                ok(tela + ': marca de emergência: «homem ao mar» falado na CONVERSA deixa a marca valendo (15 min), sem pedido ao Worker, e o ENCERRAR a zera', m0['v'] is False and m['v'] is True and 14 * 60e3 < m['falta'] <= 15 * 60e3 and len(estado['pedidos']) == antes
                   and len(f) >= 2 and 'Emergência' in f[1] and m2['v'] is False, json.dumps([m0, m, m2, f], ensure_ascii=False)[:300])
                pg.evaluate(FECHA_JANELA)

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

                # Voz a 1,15x em TODA fala (abertura e emergência), com o sinal de som para o núcleo, e o núcleo de anéis em canvas (Fase 5, F27):
                # CONVERSA "homem ao mar" com a fala de verdade do cérebro sobre o speechSynthesis de mentira. Sempre roda (o núcleo não vem à parte).
                abre()
                pg.evaluate(SINTESE_FALSA)
                pg.evaluate("() => { try { window.CapitaoEmergencia.zera(); } catch (e) {} window.__voz.length = 0; window.__nucleo.length = 0; window.__falas.push('homem ao mar'); }")   # (a janela vale por aba: sem a marca das conferências de antes)
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
                est = pg.evaluate("() => { const V = window.CapitaoVoz, n = V && V.nucleo ? V.nucleo() : null, c = document.querySelector('.cpz'), s = document.querySelector('.cpz .cpz-sos'); return { on: !!document.querySelector('.cpz.on'), tela: !!document.querySelector('.cpz canvas.cpz-tela'), palco: !!document.querySelector('.cpz .cpz-palco .cpz-btn'), fim: !!document.querySelector('.cpz .cpz-fim'), velho: !!document.querySelector('.cpz svg circle'), rosto: !!(V && V.rosto), api: !!(n && typeof n.quadro === 'function' && typeof n.estado === 'function'), e: n ? n.estado() : {}, papel: c ? c.getAttribute('role') : '', inerte: c ? c.inert : null, sos: s ? s.getAttribute('href') : '', sosTopo: s ? (() => { const r = s.getBoundingClientRect(), t = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return t === s; })() : false, reg: window.__nucleo }; }")
                e = est['e'] or {}
                ok(tela + ': o núcleo abre com os anéis no canvas em tela cheia (canvas.cpz-tela, .cpz-palco .cpz-btn, ENCERRAR, role=dialog, SOS por cima apontando para S1/S2), ∞ carregado, razão de pixels ≤ 2 e o laço ligado; sem SVG de anéis e sem o rosto',
                   est['on'] and est['tela'] and est['palco'] and est['fim'] and not est['velho'] and not est['rosto'] and est['api'] and est['papel'] == 'dialog' and est['inerte'] is False and re.search(r'S[12]-SOS-', est['sos'] or '') and est['sosTopo']
                   and e.get('simbolo') is True and 0 < (e.get('razao') or 0) <= 2 and e.get('laco') is True and e.get('ligado') is True, json.dumps({k: v for k, v in est.items() if k != 'reg'}, ensure_ascii=False)[:300])
                reg = est['reg'] or []
                ok(tela + ': o núcleo segue a conversa (falando, ouvindo, pensando) e recebe o som da voz (som true só com a voz tocando)', all(any(r['estado'] == x for r in reg) for x in ('falando', 'ouvindo', 'pensando')) and any(r['ev'] == 'falando' and r['som'] is True for r in reg) and any(r['ev'] == 'falando' and r['som'] is False for r in reg) and all(r['som'] is False for r in reg if r['estado'] != 'falando'), json.dumps([[r['ev'], r['estado'], r['som']] for r in reg], ensure_ascii=False)[:300])
                # HUD (CLAUDE.md 10): na abertura, o quadro do instante; ouvida a emergência (o alerta do evento) e com a janela aberta pela resposta, só a instrução do plotter
                ip = next((k for k, r in enumerate(reg) if r['ev'] == 'pensando'), len(reg))
                antes = [r['hud'] for r in reg[:ip] if r['ev'] == 'falando']
                depois = [r['hud'].strip() for r in reg[ip:] if r['ev'] in ('pensando', 'falando', 'ouvindo')]
                ruim = [h for h in depois if h != 'POSIÇÃO · LEIA NO PLOTTER' or confere.R_COORD.search(h) or confere.R_EMERG_PROTOCOLO.search(h) or confere.R_PESSOAS.search(h) or re.search(r'nós|\bmn\b|°|\d', h, re.I)]
                ok(tela + ': HUD da CONVERSA: na abertura mostra o quadro do instante (hora, SOG, rpm, diesel) e, da emergência ouvida em diante (alerta no evento e janela valendo), só «POSIÇÃO · LEIA NO PLOTTER» — nenhuma coordenada, nós, mn, rumo nem pessoas',
                   antes and all(re.match(r'\d\d:\d\d:\d\d\n', h) and 'SOG ' in h and ' NÓS' in h and 'RPM ' in h and 'DIESEL ' in h for h in antes) and len(depois) >= 3 and not ruim
                   and any(r['evAlerta'] is True for r in reg[ip:]) and all(r['evAlerta'] is False for r in reg[:ip] if r['ev'] == 'falando') and all(r['alerta'] is True for r in reg[ip:] if r['ev'] in ('pensando', 'falando')),
                   json.dumps({'antes': antes[:1], 'ruim': ruim[:2], 'n': len(depois)}, ensure_ascii=False)[:300])
                i = pg.evaluate('() => window.__voz.length')
                pg.keyboard.press('Escape')
                pg.wait_for_timeout(1200)
                fim = pg.evaluate("(i) => { const e = window.CapitaoVoz.nucleo().estado(); return { on: !!document.querySelector('.cpz.on'), depois: window.__voz.slice(i).map((x) => x.estado), est: e.estado, laco: e.laco, energia: e.energia, inerte: document.querySelector('.cpz').inert === true }; }", i)
                ok(tela + ': Esc encerra a conversa: o núcleo some (inerte), vai para "livre" com o laço parado e o microfone não volta', not fim['on'] and fim['inerte'] and fim['est'] == 'livre' and fim['laco'] is False and fim['energia'] == 0 and all(e == 'livre' for e in fim['depois']), json.dumps(fim, ensure_ascii=False))
                # Pressão de óleo (emergência) também a 1,15x
                pg.evaluate("() => { window.__sint.length = 0; const B = window.CapitaoBrain; B.speak(B.falaCurta(B.answer('a pressão de óleo caiu', { platform: 'web', commit: false }))); }")
                pg.wait_for_timeout(1500)
                sint = pg.evaluate('() => window.__sint')
                ok(tela + ': voz a 1,15x também no passo a passo da pressão de óleo', sint and all(abs((x['r'] or 0) - 1.15) < 1e-3 for x in sint), json.dumps(sint, ensure_ascii=False)[:300])

                # O núcleo pintado de verdade (Fase 5, F27): pixels no anel e no centro, uma cor por estado (ESCUTA ciano, PROCESSANDO violeta, RESPOSTA azul), o quadro(t) determinístico,
                # o espectro e o brilho só com som, 'livre' zera na hora, e a camada escondida não pinta. Eventos de mentira: nada é falado nem ouvido.
                pg.evaluate("() => { try { window.CapitaoBrain.stopSpeaking(); window.CapitaoVoz.esconde(); window.CapitaoEmergencia.zera(); } catch (e) {} }")
                pg.wait_for_timeout(300)
                pint = pg.evaluate(PINTURA_NUCLEO)
                perto = lambda a, b: bool(a) and all(abs(x - y) <= 14 for x, y in zip(a, b))
                o, pn, fa, vv = pint['ouvindo'], pint['pensando'], pint['falando'], pint['vivo']
                ok(tela + ': o canvas do núcleo é pintado de verdade: pixels no anel graduado e o ∞ no centro, nos três estados', all(x['anel'] >= 60 and x['centro'] >= 200 for x in (o, pn, fa)) and not pint['rosto'], json.dumps({'o': o, 'p': pn, 'f': fa}, ensure_ascii=False))
                ok(tela + ': cor por estado, as da marca: ESCUTA ciano #00F4FD, PROCESSANDO violeta #A22BFD, RESPOSTA azul #00A1FE', perto(o['cor'], (0, 244, 253)) and perto(pn['cor'], (162, 43, 253)) and perto(fa['cor'], (0, 161, 254)), json.dumps([o['cor'], pn['cor'], fa['cor']]))
                ok(tela + ': com a camada ligada o laço roda (um requestAnimationFrame pintando); quadro(t) é determinístico (mesmo t, mesmo quadro; outro t, outro quadro) e deixa o núcleo parado', vv['ligado'] and vv['laco'] and vv['quadros'] >= 3 and pint['igual'] and pint['muda'] and pint['parado'], json.dumps({'vivo': vv, 'igual': pint['igual'], 'muda': pint['muda'], 'parado': pint['parado']}, ensure_ascii=False)[:300])
                ok(tela + ': o espectro e o brilho só reagem à voz com som true (e ao pulso de cada palavra); "livre" zera na hora', pint['semSom'] < 0.15 and pint['pulsoSemSom'] == pint['semSom'] and pint['comSom'] > 0.3 and pint['pulsoComSom'] > pint['comSom'] and pint['livre'] == 0, json.dumps({k: pint[k] for k in ('semSom', 'pulsoSemSom', 'comSom', 'pulsoComSom', 'livre')}))
                esc_ = pint['escondida']
                ok(tela + ': camada escondida: inerte, sem laço e sem pintar nenhum quadro', not esc_['on'] and esc_['inerte'] and esc_['laco'] is False and esc_['quadros'] == 0, json.dumps(esc_))
                # O HUD vivo (Fase 5): o quadro do instante a cada 1 s, com a fonte e os formatadores das telas, em nós Text; em alerta, só a instrução do plotter
                h = pg.evaluate(HUD_NUCLEO)
                plot = 'POSIÇÃO · LEIA NO PLOTTER'
                ok(tela + ': HUD do núcleo: hora HH:MM:SS, posição, SOG, rpm e diesel do instante, com o texto dos formatadores das telas' + (' (o mesmo SOG e o mesmo diesel da faixa da Main)' if not movel else ''),
                   h['vivo'] == h['esperado'] and re.match(r'\d\d:\d\d:\d\d\n', h['vivo']) and (movel or (h['sog'] in h['pagina'] and h['diesel'] in h['pagina'])), json.dumps({'hud': h['vivo'], 'esperado': h['esperado']}, ensure_ascii=False)[:300])
                ok(tela + ': HUD do núcleo: lê o instante de novo em até 1 s (outro instante do replay, sem evento de voz) trocando só o .data dos mesmos nós Text (nenhuma mutação de filhos)',
                   h['depois'] == h['esperado2'] and h['depois'] != h['vivo'] and h['mesmosNos'] and h['filhos'] == 0 and h['dados'] >= 1, json.dumps({'depois': h['depois'], 'esperado': h['esperado2'], 'nos': h['mesmosNos'], 'filhos': h['filhos'], 'dados': h['dados']}, ensure_ascii=False)[:300])
                alertas = [h[k].strip() for k in ('alerta', 'alertaSegue', 'janela', 'janelaFala')]
                ruim = [x for x in alertas if x != plot or confere.R_COORD.search(x) or confere.R_EMERG_PROTOCOLO.search(x) or confere.R_PESSOAS.search(x) or re.search(r'nós|\bmn\b|°|\d', x, re.I)]
                ok(tela + ': HUD do núcleo em alerta (o evento com alerta, as outras linhas da mesma fala, a janela de emergência valendo): só «POSIÇÃO · LEIA NO PLOTTER», sem coordenada, nós, mn, rumo nem pessoas; sem alerta e sem janela, a leitura volta',
                   h['plotter'] == plot and not ruim and h['volta'] == h['esperado3'] and h['semJanela'] == h['esperado3'], json.dumps({'alertas': alertas, 'volta': h['volta'], 'semJanela': h['semJanela']}, ensure_ascii=False)[:300])
                ok(tela + ': HUD do núcleo com simulacao:false e sem leitura: o texto do modo real (POSIÇÃO · SEM LEITURA, sem número do replay)', re.match(r'\d\d:\d\d:\d\d\nPOSIÇÃO\nSEM LEITURA\s*$', h['real']) is not None, json.dumps(h['real'], ensure_ascii=False))

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
                # F30 (Fase 6; antes, P4H: o toque não chamava a IA): o toque numa pergunta do FAQ (#q=…&faq=<código>, de dentro do app, com a IA ligada) vai à IA 1 vez com o ITEM como 1º trecho ([1]: a fonte com o
                # código, o título e o texto do item), antes dos trechos do guia (B.buscaBase), e a resposta dela guarda as ações do item; de fora do app (sem referrer) fica o item local, sem pedido
                # (SK-03: a pergunta do item tem 3 trechos do guia — o pedido leva o item e 2 deles, nesta ordem; MO-02: nenhum trecho do guia — o item é o único trecho do pedido)
                def item_no_topo(ped, cod, q, guia=None):
                    tr = ped.get('trechos') or []
                    it = FAQ_ITENS[cod]
                    nb = pg.evaluate('(q) => window.CapitaoBrain.buscaBase(q, 3).length', q)   # quantos trechos do guia a pergunta tem (o cliente manda no máximo 3 trechos ao todo)
                    return (len(tr) == min(3, 1 + nb) and (guia is None or nb == guia) and tr[0].get('fonte', '').startswith('FAQ dos equipamentos ' + cod) and tr[0].get('secao') == it['titulo'] and it['resposta'][:60] in tr[0].get('texto', '')
                            and tr[0].get('faq') == cod   # (o código em `faq`: é ele que faz o Worker marcar o trecho 1 como item do FAQ e mandá-lo inteiro, com as linhas dos passos)
                            and all(x.get('fonte') and 'FAQ dos equipamentos' not in x['fonte'] and 'faq' not in x for x in tr[1:]))
                for cod, guia in (('SK-03', 3), ('MO-02', 0)):
                    t, n = por_link(FAQ_ITENS[cod]['pergunta'], interno=True, extra='&faq=' + cod)
                    ped = estado['pedidos'][-1] if n else {}
                    ok(tela + ': F30: o toque no FAQ (#q=…&faq=%s, de dentro do app, IA ligada) vai à IA 1 vez com o item como 1º trecho, antes dos %d trechos do guia, e mostra a resposta dela com a ação «Abrir %s no FAQ»' % (cod, guia, cod), n == 1 and item_no_topo(ped, cod, FAQ_ITENS[cod]['pergunta'], guia)
                       and ped.get('pergunta') == FAQ_ITENS[cod]['pergunta'] and TEXTO_IA in t and ('Abrir %s no FAQ' % cod) in t and not confere.R_COORD.search(json.dumps(ped, ensure_ascii=False)), 'pedidos=%d · %s' % (n, json.dumps([x.get('fonte') for x in ped.get('trechos') or []], ensure_ascii=False)[:300]))
                t, n = por_link(FAQ_ITENS['MO-02']['pergunta'], interno=False, extra='&faq=MO-02')
                ok(tela + ': F30: o mesmo link de fora do app (sem referrer) mostra o item com o código e a fonte e não gasta a cota', n == 0 and 'Fonte: FAQ dos equipamentos MO-02' in t and TEXTO_IA not in t, 'pedidos=%d · %s' % (n, t[-160:]))
                abre(True, 'ok')
                faq_pronto()
                t, n, _ = envia('sonda mostrando pouca profundidade')
                ped = estado['pedidos'][-1] if n else {}
                ok(tela + ': F30: a pergunta digitada que cai num item do FAQ (EL-08) também leva o item como 1º trecho', n == 1 and item_no_topo(ped, 'EL-08', 'sonda mostrando pouca profundidade') and TEXTO_IA in t, 'pedidos=%d · %s' % (n, json.dumps(ped.get('trechos'), ensure_ascii=False)[:300]))
                # o cartão de emergência (EM-xx) e o item de segurança NUNCA enviam pedido: o B.pedeIA barra os 9 cartões e todo item `seguranca`, e o toque de verdade (EM-06, o de salvatagem EM-09 e o do EPIRB EP-02) abre local
                barrados = pg.evaluate("""() => { const B = window.CapitaoBrain; return B.faqDados().itens.filter((it) => it.emerg || it.seguranca).map((it) => { const a = B.answer(it.pergunta, { platform: 'web', commit: false, faq: it.id });
                  return { id: it.id, faq: a.faq, pede: B.pedeIA(a, it.pergunta, {}) }; }); }""")
                pg.evaluate(FECHA_JANELA)
                ems = [x['id'] for x in barrados if x['id'].startswith('EM-')]
                ok(tela + ': F30: nenhum cartão de emergência (EM-01…09) nem item de segurança do FAQ pede a IA (B.pedeIA false nos %d itens)' % len(barrados), len(ems) == 9 and len(barrados) > 9 and all(x['faq'] == x['id'] and x['pede'] is False for x in barrados),
                   [x for x in barrados if x['pede'] is not False or x['faq'] != x['id']][:5])
                for cod in ('EM-06', 'EM-09', 'EP-02'):
                    t, n = por_link(FAQ_ITENS[cod]['pergunta'], interno=True, extra='&faq=' + cod)
                    ok(tela + ': F30: o toque no FAQ (#q=…&faq=%s, de dentro do app, IA ligada) mostra o item com o código e a fonte e não envia pedido nenhum ao Worker' % cod, n == 0 and ('Fonte: FAQ dos equipamentos ' + cod) in t and TEXTO_IA not in t, 'pedidos=%d · %s' % (n, t[-160:]))
                    pg.evaluate(FECHA_JANELA)
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
