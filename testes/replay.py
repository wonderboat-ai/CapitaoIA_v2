# -*- coding: utf-8 -*-
"""Capitão IA — teste do motor da reprodução (capitao-replay.js; CONTRATO-DADOS §1.15–§1.17, §1.22–§1.24, §3, §6.5; PROMPT Fase 2). Sem cota.

O motor é a função pura `em(ms)` do instante absoluto (laço de 150 s + rota + contadores + alarmes), mais o relógio (`agora`, `fixar`), o tique de
1 s (eventos) e as séries do histórico. Aqui, no Chromium (Edge) com o site servido em 127.0.0.1:8765 e a rede cortada (o contexto aborta tudo o que
não for 127.0.0.1 ou unpkg.com; o unpkg só serve o React das telas de verdade):

- t de 0 a 149 (`quadro(t)`): todos os campos finitos, sem -0, com o número de casas do D.campos, e o quadro ⇔ catálogo nos dois sentidos;
- paridade Python × JS (§6.5): `quadro(t)` t = 0…149, uma amostra do dia, as 1.150 pontas das 575 emendas e as pontas da âncora, campo a campo
  contra `confere.em()` (o port que o gerador usa; o gerador não exporta os 150 quadros, então a conta é refeita aqui em Python, com a mesma
  fórmula e a partir do D.replay do capitao-dados.js); os 86.400 segundos do dia conferem com `--dia`. A paridade é EXATA, campo a campo: nem 1 unidade
  da última casa passa (um proa sem o ruído de 0,4° ou um COG fora por 0,5° mexem 1 unidade em alguns segundos, com `casas` 0 e 1, e a tolerância
  antiga os aceitava). Seno, cosseno, asen e atan2 do V8 e do CPython dão o mesmo resultado nesta máquina. Em outra máquina, se o libm derivar 1 ulp,
  `CAPITAO_TOL_TRIG=1` volta a aceitar 1 unidade da última casa SÓ nos campos TRIG, conta os usos no texto da conferência; nos mutantes a tolerância
  fica sempre desligada;
- emenda: o laço (|v(149) − v(0)| ≤ o maior passo de 1 s da volta, por campo do laço) e, no dia inteiro, as 575 emendas de 150 s fora da âncora
  (segundos consecutivos, `em(N·150 − 1 s)` × `em(N·150)`): nenhum campo numérico passa do maior passo de 1 s do dia, e destino, próximo ponto e ETA
  não mudam; a única descontinuidade é a virada das 07:00 (contadores, tanques e a rota que recomeça), com posição e COG contínuos;
- contadores sem voltar (`D.campos[c].sentido`), fora do par A − 1 s × A, que tem de saltar;
- alarme só na janela do gerador (99–116 s), sempre AVISO, com `desde` da janela; `alarmes()`, `janela()`; o cenário `aviso` nunca devolve
  crítico (com os limites adulterados, e também com a lista literal do gancho `capitao.replay.sobre`) e o `alarme-critico` devolve;
- as fronteiras das fases (`fase()` e `t()` em t = 0, 19, 20, 49, 50, 119, 120, 134, 135, 149 e em cada um dos 150 segundos) contra o D.replay.fases;
- paridade com DADO PLANTADO (§6.5): o vento verdadeiro cruzando o norte (o arco mais curto dos ângulos) e o diesel perto do piso (`diesel_piso_l`),
  injetados no D antes do replay e comparados com o `confere.em()` do mesmo D plantado;
- sincronia entre duas abas e entre dois aparelhos (o mesmo segundo dá o mesmo quadro) e a fase que continua pelo relógio ao trocar de página;
- `fixar('60')` = 12:01:00 (voltas_fixo), `fixar(60)`, '60@K', `fixar(null)`, `#replay=`, o localStorage `capitao.replay.fixo` e o `capitao.replay.sobre`
  (só com o instante fixado, só no instante fixado); o rodapé refaz os prazos para o dia do instante fixado (entre 00:00 e 07:00, "ontem 12:01");
- eventos: `capitao-telemetria` a cada 1 s alinhado ao segundo, pausado com document.hidden e com tique imediato na volta à frente;
  `capitao-alerta` (inicio, nivel, fim); `capitao-rebase` na virada das 07:00 e da meia-noite (com o Date congelado), inclusive na página que
  carregou OCULTA antes da virada e só depois voltou à frente; um timer só por página;
- isolamento: o replay não é o `CapitaoTelemetria`; `atual()` e `fonte()` (coletor real recente × replay × null); o D.snapshot nem um byte diferente;
  a âncora é a `CapitaoAgora.ancora` (a mesma, sem cópia); falha → null e o instante() cai no snapshot sem mutá-lo;
- a moldura em nós Text (P2B; PROMPT Fase 2 «Desempenho», CONTRATO §6.6): em 10 s de replay, a 360×640 nas telas de app e a 1440×900 nas web (3 telas por padrão: A2, A1 e E1; as
  30 com `--moldura`), o `<capitao-theme-toggle>` e o avatar são o mesmo nó (isSameNode), o foco do teclado fica no botão do tema, o `fit()` roda no máximo 2 vezes, nenhuma long task
  passa de 50 ms e nenhuma mutação childList entra na moldura (só troca de caractere dos textos que mudaram); com o instante fixado, 3 tiques não mexem em nada (nem um caractere ou
  atributo: só se escreve quando o valor mudou); a moldura mostra o `CapitaoMoldura.leitura()` do tique, e o estado montado aos poucos (LED que vira de verde para amarelo e volta,
  título e href do topo) é igual ao de uma moldura montada do zero naquele estado; Main, H2 e E1 só dão setState quando o texto exibido muda (o React.Component.prototype.setState
  contado: livre, nunca mais que um por tique; instante fixado, nenhum); 6 mutantes da P2B que esses testes têm de acusar;
- a API de alertas (capitao-alertas.js; P2C, F05; CONTRATO §1.24): a lista vem do `alarmes()` do replay e do catálogo `D.replay.alertas`, só dentro da janela de 99 a 116 s, um id por
  campo, com o nível, o limite e o valor da `CapitaoAgora.nivel` (a lista é exatamente os campos fora do normal, segundo a segundo, em 3 voltas do dia); crítico só no cenário
  `alarme-critico`, com a ordem (crítico antes de aviso, o mais antigo primeiro) e a contagem, e aviso → crítico → aviso no mesmo id, com valores plantados pelo gancho `sobre`; o
  formato do alerta e a cópia que ninguém mexe no D; anunciado UMA vez por id por sessão (`sessionStorage`, recarga, sessão nova, storage negado, cheio e com lixo, id inválido);
  acompanha o evento `capitao-alerta` e não emite o seu; modo real inerte (a flag lida a cada chamada, e mesmo com um replay que mente); lista suja do replay; nunca lança; sem efeito
  colateral (fala, janela, endereço, localStorage, diário); S1/S2 e rotas /SOS- sem a API; 4 telas de verdade; o código (sem avaliar limite, sem evento nem timer); o `ms` de ativos/porId/tocando/contagem/novos com o instante fixado do outro lado da janela (nos dois sentidos, sem depender do relógio real); 14 mutantes;
- S1/S2 (e uma rota /SOS-): sem CapitaoReplay, `CapitaoAgora.instante()` null, nenhum tique, nenhuma leitura de D.simulacao nem de D.replay;
- modo real inerte (`simulacao = false` no fim do capitao-dados.js, e a flag mudando com a página aberta): nada anda, `em()` null, nenhum evento;
- histórico: `serie()` das cinco janelas sem NaN, o último ponto = o quadro, o serrote do diesel = as linhas de abastecimento, a curva do ano do
  ar e da água (30 D e 1 A não saem retos), a trava de máx/mín do dia; `porFaixa()`, `resumo()` (≤ 300 letras, sem coordenadas, sem os termos do §3);
- D.replay PARCIAL (chave, rota, tanque, velocidade ou contador ausente; chave curta; ETA infinita): a tabela se recusa na carga (`ativo()` false, tudo null, nenhum tique, o
  `instante()` cai no snapshot) e, com o D em uso quebrado depois da carga, a guarda de cada saída (quadro, contadores, consumo por faixa, série) devolve null, nunca NaN/Infinity;
- nunca lança erro (argumentos absurdos, D quebrado, localStorage que lança); desempenho do `em()`; o código (sem lookbehind, sem snapshot, sem
  `window.CapitaoTelemetria =`); as 36 telas com o <script> no lugar certo, S1/S2 sem ele, e o CORE do sw.js.

Fica para as Fases 3 a 7 (depende do cérebro, das telas ou da IA, que a Fase 2 não toca):
- o mesmo texto de rpm, SOG e diesel na Main, A1, E1, HUD, `answer('telemetria')` e `## Navegação agora` (um instante só, `fixar('60')`);
- a ficha, a tendência de 30 s (`instante().tend`, que a Fase 3 monta), a trava do ar e da água nas telas (A1 × Main) e as séries nos gráficos;
- o grep final (SEM DADOS, SEM LEITURA, DEMO e demais rótulos nas respostas e nas telas), o `sim: true` nas linhas gravadas e o modo real do cérebro e da IA;
- a faixa de alerta, a lista da Ponte, a C3 viva, a E1 NAVEGANDO × FUNDEADO (P4F: verificar.py --so-p4f; aqui, o setState só quando o texto muda) e as rotas de alarmes do cérebro (Fases 3 e 4; a API que elas vão ler, o capitao-alertas.js, é da P2C e está coberta acima);
- o cérebro, a moldura e a E1 ainda dizem «ao vivo» / «coletor NMEA» sobre o quadro do replay e misturam o diesel do D.snapshot (estado transitório do
  CONTRATO §6.6, até a Fase 3 — VIVO generalizado e instante() — e a Fase 4: a P2B só trocou a mecânica da moldura, os textos e rótulos ficam para elas): lá entra a conferência de que nenhum texto diz «coletor NMEA»
  quando `CapitaoTelemetria.fonte()` é 'replay'.

Uso (com o site servido em http://127.0.0.1:8765, na raiz do repositório):
    python -X utf8 testes/replay.py            os testes de sempre (~5 min)
    python -X utf8 testes/replay.py --dia      mais a paridade dos 86.400 segundos do dia de bordo contra o confere.em() (~4 min a mais)
    python -X utf8 testes/replay.py --moldura mais o desempenho da moldura nas 30 telas que a importam (3 por vez, ~4 min a mais)
Navegador: Edge instalado (Playwright com channel="msedge"); troque CANAL para "chrome" se preferir.
"""
import copy
import json
import math
import os
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8765'
CANAL = 'msedge'
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BR = timezone(timedelta(hours=-3))
sys.path.insert(0, os.path.join(RAIZ, 'ferramentas', 'demo'))
import confere as C  # noqa: E402  (o port em Python do laço, da rota, dos contadores e da nivel: o que o gerador usa)

falhas = 0
total = 0
CAPTURA = None   # lista, no modo mutante: o ok() só anota o que falhou (o motor está quebrado de propósito)
MUT = None       # [(trecho, no lugar)] do capitao-replay.js servido ao navegador, no modo mutante
MUT_ARQ = None   # {arquivo: [(trecho, no lugar)]}: o mesmo para outros arquivos do site (a moldura, uma tela) nos mutantes da P2B


def ok(nome, cond, info=''):
    global falhas, total
    if CAPTURA is not None:
        if not cond:
            CAPTURA.append(nome)
        return
    total += 1
    print(('OK    ' if cond else 'FALHA ') + nome + ('' if cond or info == '' else ' — ' + str(info)[:600]))
    if not cond:
        falhas += 1


def le(arq):
    return open(os.path.join(RAIZ, arq), encoding='utf-8').read()


def carrega_dados():
    s = le('capitao-dados.js')
    i = s.index('window.CapitaoDados = ') + len('window.CapitaoDados = ')
    return json.JSONDecoder().raw_decode(s[i:])[0]


D = carrega_dados()
P = C.preparar(D)
VOLTA = D['replay']['duracao']
JANELA_INI = min(j['ini'] for j in D['replay']['janelas'])
JANELA_FIM = max(j['fim'] for j in D['replay']['janelas'])

# ——— páginas, rede e relógio ———
HTML = ('<!doctype html><meta charset="utf-8"><title>replay</title><script src="/capitao-dados.js"></script>'
        '<script src="/capitao-replay.js"></script><script src="/capitao-telemetria.js"></script>')
HTML_SEM_TELE = '<!doctype html><meta charset="utf-8"><title>replay</title><script src="/capitao-dados.js"></script><script src="/capitao-replay.js"></script>'
HTML_ANTES = ('<!doctype html><meta charset="utf-8"><title>replay</title><script src="/capitao-dados.js"></script>'
              '<script src="/capitao-telemetria.js"></script><script src="/capitao-replay.js"></script>')
# o que cada evento do motor registra (a hora real e a do Date da página, que o teste pode congelar)
GRAVA = """(function () { window.__ev = []; ['capitao-telemetria', 'capitao-alerta', 'capitao-rebase'].forEach(function (n) {
  window.addEventListener(n, function (e) { window.__ev.push({ n: n, t: Date.now(), p: performance.now(), d: e.detail }); }); });
  window.__conta = function (n) { return window.__ev.filter(function (e) { return e.n === n; }).length; }; })();"""
SESSAO = "(() => { const n = Date.now(); localStorage.setItem('capitao.sessao.v1', JSON.stringify({ u: 'lucas', em: n, exp: n + 3600e3 })); })()"
GETTER = """window.__lidas = 0; (function () { var v = window.CapitaoDados.simulacao; Object.defineProperty(window.CapitaoDados, 'simulacao',
  { get: function () { window.__lidas++; return v; }, set: function (x) { v = x; }, configurable: true, enumerable: true }); })();"""
GETTER_REPLAY = """window.__lidasReplay = 0; (function () { var v = window.CapitaoDados.replay; Object.defineProperty(window.CapitaoDados, 'replay',
  { get: function () { window.__lidasReplay++; return v; }, set: function (x) { v = x; }, configurable: true, enumerable: true }); })();"""
MARCA = '/* CapitaoAgora'   # o começo do rodapé no capitao-dados.js: o que entra antes dele roda antes dele


def congela(local):
    """Date congelado em `local` (window.__T0 em ms, que o teste move); o Intl real continua."""
    return ("(function () { var RD = Date; window.__T0 = %d; function FD() { var a = arguments; return a.length === 0 ? new RD(window.__T0) : new (Function.prototype.bind.apply(RD, [null].concat([].slice.call(a))))(); }"
            " FD.prototype = RD.prototype; FD.now = function () { return window.__T0; }; FD.UTC = RD.UTC; FD.parse = RD.parse; window.Date = FD; })();" % int(local.timestamp() * 1000))


def so_local(route):
    """Rede cortada: só o site (127.0.0.1) e o unpkg.com (o React das telas de verdade; a cópia local do shim, se houver, atende antes)."""
    h = urlparse(route.request.url).hostname or ''
    if h == '127.0.0.1' or h == 'unpkg.com' or h.endswith('.unpkg.com'):
        return route.fallback()
    return route.abort()


def abre(b, caminho='/replay.html', html=HTML, init='', antes='', depois='', local=None, sessao=False, viewport=None, espera='() => window.CapitaoAgora && window.CapitaoAgora.relogio'):
    """Contexto novo (localStorage limpo) com a rede cortada. `init` roda antes de qualquer script da página; `antes` entra no capitao-dados.js
    antes do rodapé e `depois` no fim dele (como a injeção do modo real); `html` é a página mínima das rotas que não são .dc.html."""
    ctx = b.new_context(service_workers='block', **({'viewport': viewport} if viewport else {}))
    ctx.add_init_script(GRAVA)
    if local is not None:
        ctx.add_init_script(congela(local))
    if sessao:
        ctx.add_init_script(SESSAO)
    if init:
        ctx.add_init_script(init)
    ctx.route('**/*', so_local)

    def dados(route):
        r = route.fetch()
        corpo = r.text()
        assert MARCA in corpo, 'o rodapé não está no capitao-dados.js'
        route.fulfill(response=r, body=corpo.replace(MARCA, antes + '\n' + MARCA, 1) + '\n' + depois)
    ctx.route('**/capitao-dados.js', dados)
    if MUT:
        def replay_mutante(route):
            r = route.fetch()
            corpo = r.text()
            for trecho, novo in MUT:
                corpo = corpo.replace(trecho, novo, 1)
            route.fulfill(response=r, body=corpo)
        ctx.route('**/capitao-replay.js', replay_mutante)
    def troca_em(trocas):   # uma função por arquivo (o Playwright passa (route, request) ao tratador: nada de argumento padrão)
        def mutante_arq(route):
            r = route.fetch()
            corpo = r.text()
            for trecho, novo in trocas:
                corpo = corpo.replace(trecho, novo, 1)
            route.fulfill(response=r, body=corpo)
        return mutante_arq
    for arq, trocas in (MUT_ARQ or {}).items():
        ctx.route('**/' + arq, troca_em(trocas))
    rota = caminho.split('#')[0]   # o endereço do pedido não leva o hash
    if rota.endswith('.html') and not rota.endswith('.dc.html'):
        ctx.route('**' + rota, lambda route: route.fulfill(body=html, content_type='text/html; charset=utf-8'))
    pg = ctx.new_page()
    pg.erros = []
    pg.on('pageerror', lambda e: pg.erros.append(str(e)))
    pg.goto(BASE + caminho)
    if espera:
        pg.wait_for_function(espera)
    return pg


def fecha(pg):
    pg.context.close()


# ——— 1. a volta de 150 s: campos finitos, casas, catálogo ———
VOLTA_JS = r"""() => {
  const R = window.CapitaoReplay, A = window.CapitaoAgora, cat = window.CapitaoDados.campos;
  let anc, ini, q, antes, depois, tentativas = 0;
  do {   // a volta pode virar no meio do laço de 150 chamadas (raro): refaz
    const a = Date.now(); anc = A.ancora(a); antes = Math.floor((Math.floor((a - anc) / 1000)) / 150);
    q = []; for (let t = 0; t < 150; t++) q.push(R.quadro(t));
    const d = Date.now(); depois = Math.floor((Math.floor((d - anc) / 1000)) / 150); tentativas++;
  } while (antes !== depois && tentativas < 4);
  ini = antes * 150;
  const problemas = [], casasOk = [];
  q.forEach((x, t) => {
    if (!x) { problemas.push('t=' + t + ' nulo'); return; }
    Object.keys(x).forEach((c) => {
      const v = x[c], d = cat[c];
      if (typeof v === 'number') {
        if (!Number.isFinite(v)) problemas.push(t + ':' + c + ' não finito');
        if (Object.is(v, -0)) problemas.push(t + ':' + c + ' -0');
        if (d && typeof d.casas === 'number' && Math.abs(v * Math.pow(10, d.casas) - Math.round(v * Math.pow(10, d.casas))) > 1e-6) casasOk.push(t + ':' + c + '=' + v);
      } else if (typeof v === 'string') { if (v === '') problemas.push(t + ':' + c + " vazio"); }
      else if (typeof v === 'boolean') { /* fixos */ }
      else if (c !== 'alarmes') problemas.push(t + ':' + c + ' tipo ' + typeof v);
    });
  });
  const chaves = new Set(), cats = Object.keys(cat);
  q.forEach((x) => x && Object.keys(x).forEach((c) => chaves.add(c)));
  return { anc, ini, q, problemas, casasOk, soNoQuadro: [...chaves].filter((c) => cats.indexOf(c) < 0), soNoCatalogo: cats.filter((c) => !chaves.has(c)),
           tipos: q[0] && { alarmes: Array.isArray(q[0].alarmes), simulado: 'simulado' in q[0] } };
}"""
TRIG = ('proa_graus', 'stw_nos', 'vento_aparente_nos', 'vento_aparente_angulo', 'leme_graus')   # derivados de sin, cos, asin, atan2 e hypot
TOL_TRIG = os.environ.get('CAPITAO_TOL_TRIG') == '1'   # só por escolha explícita (outra máquina com libm que deriva 1 ulp); o padrão é a paridade exata
TOL_USOS = []   # (contexto, campo, py, js) das diferenças de 1 unidade aceitas com CAPITAO_TOL_TRIG=1


def compara(js, py, nome_ctx):
    """Diferenças entre o quadro do JS e o do Python, campo a campo: [(contexto, campo, py, js)]. Exata: nem 1 unidade da última casa passa.
    Com CAPITAO_TOL_TRIG=1 (escolha explícita) e só nos campos TRIG, 1 unidade da última casa vai para TOL_USOS em vez de reprovar."""
    exatas = []
    for k in set(py) | set(js):
        a, b = py.get(k, '<falta>'), js.get(k, '<falta>')
        if a == b:
            continue
        if TOL_TRIG and k in TRIG and isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and abs(a - b) <= 1.0001 * 10 ** (-C.casas_de(D['campos'], k)):
            TOL_USOS.append((nome_ctx, k, a, b))
        else:
            exatas.append((nome_ctx, k, a, b))
    return exatas


def sufixo_tol():
    """Vazio no padrão (paridade exata); com CAPITAO_TOL_TRIG=1, diz quantas diferenças de 1 unidade foram aceitas até agora."""
    return ' [CAPITAO_TOL_TRIG=1: %d diferença(s) de 1 unidade aceitas até aqui]' % len(TOL_USOS) if TOL_TRIG else ''


def a_volta(b):
    print('A volta de 150 s: campos finitos e paridade Python × JS (CONTRATO §6.5)')
    pg = abre(b)
    r = pg.evaluate(VOLTA_JS)
    ok('quadro(t), t de 0 a 149: 150 quadros, todos os campos finitos, sem -0, sem texto vazio', len(r['q']) == 150 and r['problemas'] == [], r['problemas'][:5])
    ok('cada número tem as casas do D.campos (o valor como a tela mostra)', r['casasOk'] == [], r['casasOk'][:5])
    ok('quadro ⇔ catálogo (D.campos) nos dois sentidos, e o simulado: true não está no em()', r['soNoQuadro'] == [] and r['soNoCatalogo'] == [] and r['tipos'] == {'alarmes': True, 'simulado': False},
       (r['soNoQuadro'], r['soNoCatalogo'], r['tipos']))
    anc_s = r['anc'] // 1000
    exatas = []
    for t in range(VOLTA):
        exatas += compara(r['q'][t], C.em(P, r['ini'] + t, ancora_s=anc_s), 't=%d' % t)
    ok('paridade exata: quadro(t) = confere.em() campo a campo, t = 0…149, nenhuma diferença nem de 1 unidade da última casa' + sufixo_tol(), exatas == [], exatas[:4])
    # uma amostra do dia, as pontas das 576 emendas e as da âncora (segundos absolutos do dia de bordo)
    random.seed(7)
    segs = sorted(set(random.sample(range(150, 86400), 1200) + [n * 150 + d for n in range(1, 576) for d in (-1, 0)] + [0, 1, 86398, 86399]))
    js = pg.evaluate("""(segs) => { const R = window.CapitaoReplay, anc = window.CapitaoAgora.ancora(Date.now()), o = {};
      segs.forEach((s) => { o[s] = R.em(anc + s * 1000); }); return { anc, o }; }""", segs)
    exatas = []
    for s in segs:
        exatas += compara(js['o'][str(s)], C.em(P, s, ancora_s=js['anc'] // 1000), 'seg=%d' % s)
    ok('paridade exata: %d segundos do dia (amostra, as 1.150 pontas das emendas e as pontas da âncora) iguais ao confere.em()' % len(segs) + sufixo_tol(),
       exatas == [], exatas[:4])
    if '--dia' in sys.argv:   # opcional (~4 min): os 86.400 segundos do dia de bordo, em blocos, contra o confere.em()
        exatas, n = [], 0
        for ini in range(0, 86400, 3000):
            blocos = pg.evaluate("""([ini, fim]) => { const R = window.CapitaoReplay, anc = window.CapitaoAgora.ancora(Date.now()), o = [];
              for (let s = ini; s < fim; s++) o.push(R.em(anc + s * 1000)); return { anc, o }; }""", [ini, min(ini + 3000, 86400)])
            for k, q in enumerate(blocos['o']):
                exatas += compara(q, C.em(P, ini + k, ancora_s=blocos['anc'] // 1000), 'seg=%d' % (ini + k))
                n += 1
        ok('paridade exata (--dia): os %d segundos do dia de bordo iguais ao confere.em()' % n + sufixo_tol(), exatas == [] and n == 86400, exatas[:4])
    # contadores: contadoresEm(ms) são os campos de origem contador do quadro; o último segundo do dia = a base + o consumo do dia (§6.5)
    cont = [c for c, d in D['campos'].items() if d.get('origem') == 'contador']
    rc = pg.evaluate("""(cont) => { const R = window.CapitaoReplay, anc = window.CapitaoAgora.ancora(Date.now()), ms = anc + 1234 * 1000, e = R.em(ms), c = R.contadoresEm(ms), c2 = R.contadores(ms), fim = R.contadoresEm(anc + 86399 * 1000);
      return { chaves: Object.keys(c).sort(), iguais: cont.every((k) => c[k] === e[k] && c2[k] === e[k]), fim, ini: R.contadoresEm(anc), agora: Object.keys(R.contadores()).length }; }""", cont)
    ok('contadoresEm(ms) = os %d campos de origem contador do D.campos, com os mesmos valores do quadro; contadores() sem argumento é o de agora' % len(cont),
       rc['chaves'] == sorted(cont) and rc['iguais'] and rc['agora'] == len(cont), (rc['chaves'], cont))
    R_, base, dia = D['replay'], D['replay']['contadores_base'], D['replay']['por_dia']
    esperado = {'diesel_litros': base['diesel_litros'] - dia['diesel_l'], 'distancia_mn': base['distancia_mn'] + dia['distancia_mn'], 'motor_bb_horimetro_h': base['motor_bb_horimetro_h'] + dia['motor_h'],
                'motor_be_horimetro_h': base['motor_be_horimetro_h'] + dia['motor_h'], 'gerador_horimetro_h': base['gerador_horimetro_h'] + dia['gerador_h']}
    for c, k in R_['taxas_h'].items():
        esperado[c] = base[c] + k * 24
    ruim = {c: (rc['fim'][c], round(v, 3)) for c, v in esperado.items() if abs(rc['fim'][c] - v) > (1.0 if c == 'diesel_litros' else 0.15)}
    ok('contadoresEm(A + 576·150 s − 1 s) = a base + o consumo de um dia (por_dia; ±1 L e ±0,15 de arredondamento): diesel %s L, %s mn, horímetros %s h'
       % (rc['fim']['diesel_litros'], rc['fim']['distancia_mn'], rc['fim']['motor_bb_horimetro_h']), ruim == {}, ruim)
    ok('às 07:00:00 os contadores são os da base (1.560 L, 0 mn, horímetros e tanques de contadores_base)', all(rc['ini'][c] == C.arred(base[c], C.casas_de(D['campos'], c)) for c in base), rc['ini'])
    ok('a soma de 150 s da tabela = por_volta (diesel %.4f L e %.4f mn, 4 casas)' % (P['cumD'][150], P['cumM'][150]),
       abs(P['cumD'][150] - R_['por_volta']['diesel_l']) < 6e-5 and abs(P['cumM'][150] - R_['por_volta']['distancia_mn']) < 6e-5, (P['cumD'][150], P['cumM'][150], R_['por_volta']))
    ok('timestamp_utc = o instante pedido (o segundo inteiro, ISO com Z)', js['o']['0']['timestamp_utc'] == datetime.fromtimestamp(js['anc'] // 1000, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
       js['o']['0']['timestamp_utc'])
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)
    paridade_plantada(b)


# O dado de hoje não cobre dois comportamentos que o motor tem de ter: o único ângulo com chaves (vento verdadeiro, de 54 a 62) nunca cruza 360 e o diesel
# termina o dia em 473,8 L, acima do piso de 400 L. Aqui o D é plantado (as chaves do vento cruzam o norte várias vezes; a base do diesel fica a 5 L do piso)
# e o motor é comparado com o confere.em() do MESMO D plantado.
VENTO_CRUZA = [355, 357, 359, 1, 3, 5, 3, 1, 359, 357, 355, 353, 351, 349, 351, 353, 355, 357, 359, 1, 3, 5, 7, 9, 7, 5, 3, 1, 359, 357]


def paridade_plantada(b):
    print('Paridade com dado plantado: o vento cruzando o norte (arco mais curto) e o diesel no piso')
    ch = D['replay']['chaves']['vento_verdadeiro_angulo']
    piso = D['replay']['diesel_piso_l']
    assert len(VENTO_CRUZA) == len(ch) and D['campos']['vento_verdadeiro_angulo'].get('ang') is True
    D2 = copy.deepcopy(D)
    D2['replay']['chaves']['vento_verdadeiro_angulo'] = VENTO_CRUZA
    D2['replay']['contadores_base']['diesel_litros'] = piso + 5
    P2 = C.preparar(D2)
    inj = ('window.CapitaoDados.replay.chaves.vento_verdadeiro_angulo = %s; window.CapitaoDados.replay.contadores_base.diesel_litros = %s;'
           % (json.dumps(VENTO_CRUZA), piso + 5))
    pg = abre(b, depois=inj)
    segs = sorted(set(list(range(0, 700)) + [n * 150 + d for n in range(1, 40) for d in (-1, 0)] + [3000, 5000, 20000, 43200, 86398, 86399]))
    js = pg.evaluate("""(segs) => { const R = window.CapitaoReplay, anc = window.CapitaoAgora.ancora(Date.now()), o = {};
      segs.forEach((s) => { o[s] = R.em(anc + s * 1000); }); return { anc, o }; }""", segs)
    exatas = []
    for s in segs:
        exatas += compara(js['o'][str(s)], C.em(P2, s, ancora_s=js['anc'] // 1000), 'seg=%d' % s)
    ok('paridade exata com o D plantado: %d segundos (0…699, as emendas dos 40 primeiros laços e o resto do dia) iguais ao confere.em() do mesmo D' % len(segs) + sufixo_tol(),
       exatas == [], exatas[:4])
    vento = [js['o'][str(s)]['vento_verdadeiro_angulo'] for s in range(0, 150)]
    passo = [abs((vento[(i + 1) % 150] - vento[i] + 540) % 360 - 180) for i in range(150)]
    ok('o vento cruza o norte pelo arco mais curto: sempre em [0, 360), passa de 359 para 0 e o maior passo de 1 s é %.0f° (pelo arco longo seria ~40°)' % max(passo),
       all(0 <= v < 360 for v in vento) and any(v >= 358 for v in vento) and any(v <= 2 for v in vento) and max(passo) <= 6, (vento[8:20], max(passo)))
    dies = [js['o'][str(s)]['diesel_litros'] for s in segs]
    achou = next(i for i, d in enumerate(dies) if d == piso)
    ok('o diesel para no piso de %d L: começa em %s, nunca fica abaixo dele, chega nele pelo seg %d e continua nele no fim do dia (%s L)' % (piso, dies[0], segs[achou], dies[-1]),
       dies[0] == piso + 5 and min(dies) == piso and achou > 0 and all(d == piso for d in dies[achou:]) and dies[-1] == piso, (dies[:3], min(dies), dies[-3:]))
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


# ——— 1b. as fases pelo relógio, nas fronteiras ———
FASE_JS = r"""() => { const R = window.CapitaoReplay, A = window.CapitaoAgora, base = A.ancora(Date.now()) + 120 * 150 * 1000, o = { por: [] };
  for (let t = 0; t < 150; t++) { const ms = base + t * 1000, f = R.fase(ms); o.por.push({ t: R.t(ms), nome: f && f.nome, ini: f && f.ini, fim: f && f.fim }); }
  const prox = R.fase(base + 150 * 1000), ant = R.fase(base - 1000);
  o.prox = { t: R.t(base + 150 * 1000), nome: prox && prox.nome, ini: prox && prox.ini }; o.ant = { t: R.t(base - 1000), nome: ant && ant.nome, ini: ant && ant.ini };
  o.semArg = R.fase().nome === R.fase(Date.now()).nome; o.ruim = [R.fase('x'), R.fase(NaN), R.t('x')];
  return o; }"""


def a_fase(b):
    print('fase() e t() nas fronteiras das fases (D.replay.fases)')
    pg = abre(b)
    r = pg.evaluate(FASE_JS)
    fs = D['replay']['fases']

    def esperada(t):
        return next(f for f in fs if f['ini'] <= t < f['fim'])
    ruins = [(t, x) for t, x in enumerate(r['por']) if x['t'] != t or x['nome'] != esperada(t)['nome'] or x['ini'] != esperada(t)['ini'] or x['fim'] != esperada(t)['fim']]
    ok('fase() e t() batem com o D.replay.fases em cada um dos 150 segundos (fim exclusivo: t = %s mudam de fase)' % ', '.join(str(f['ini']) for f in fs[1:]), ruins == [], ruins[:3])
    borda = {t: r['por'][t]['nome'] for t in (0, 19, 20, 49, 50, 119, 120, 134, 135, 149)}
    ok('as fronteiras: 19 é %s e 20 é %s; 49 é %s e 50 é %s; 119 é %s e 120 é %s; 134 é %s e 135 é %s; 149 é %s'
       % (borda[19], borda[20], borda[49], borda[50], borda[119], borda[120], borda[134], borda[135], borda[149]),
       [borda[t] for t in (19, 20, 49, 50, 119, 120, 134, 135, 149)] == ['marcha lenta', 'aceleração', 'aceleração', 'cruzeiro', 'cruzeiro', 'redução', 'redução', 'marcha lenta', 'marcha lenta'], borda)
    ok('a volta seguinte recomeça em t = 0 (marcha lenta, ini 0) e o segundo antes dela é t = 149', r['prox'] == {'t': 0, 'nome': 'marcha lenta', 'ini': 0} and r['ant'] == {'t': 149, 'nome': 'marcha lenta', 'ini': 135}, (r['prox'], r['ant']))
    ok('fase() sem argumento é a de agora; argumento que não é instante devolve null', r['semArg'] is True and r['ruim'] == [None, None, None], r['ruim'])
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


# ——— 2. o dia inteiro: emendas, contadores, alarmes ———
DIA_JS = r"""() => {
  const R = window.CapitaoReplay, A = window.CapitaoAgora, D = window.CapitaoDados, cat = D.campos, anc = A.ancora(Date.now());
  const campos = Object.keys(cat).filter((c) => c !== 'alarmes' && c !== 'timestamp_utc');
  const ang = {}; campos.forEach((c) => { ang[c] = !!cat[c].ang; });
  const passo = (a, b, c) => (ang[c] ? Math.abs((((b - a + 540) % 360) + 360) % 360 - 180) : Math.abs(b - a));
  const disc = ['destino', 'wp_proximo', 'eta'], janelas = D.replay.janelas;
  const dentro = {}, emenda = {}, fixosMudaram = [], monotonia = [], discNaEmenda = [], alarmes = { fora: [], sem: [], nivel: {}, ids: {}, desdeErrado: [] };
  let prev = R.em(anc), maxLaco = {}, nulos = 0;
  const sentido = {}; campos.forEach((c) => { if (cat[c].sentido) sentido[c] = cat[c].sentido; });
  for (let s = 1; s < 86400; s++) {
    const cur = R.em(anc + s * 1000);
    if (!cur) { nulos++; continue; }
    const costura = s % 150 === 0, ev = disc.some((k) => cur[k] !== prev[k]);
    for (const c of campos) {
      if (typeof cur[c] !== 'number') continue;
      const p = passo(prev[c], cur[c], c);
      if (costura) { if (!(c in emenda) || p > emenda[c]) emenda[c] = p; }
      else if (!ev) { if (!(c in dentro) || p > dentro[c]) dentro[c] = p; }
    }
    if (costura && ev) discNaEmenda.push(s);
    if (costura) ['marcha', 'estado', 'ancora_estado'].forEach((k) => { if (cur[k] !== prev[k]) fixosMudaram.push(s + ':' + k); });
    for (const c in sentido) { if (sentido[c] * (cur[c] - prev[c]) < 0) monotonia.push(s + ':' + c); }
    // alarme só na janela do gerador
    const t = s % 150, naJanela = janelas.some((j) => j.ini <= t && t <= j.fim), n = cur.alarmes.length;
    if (naJanela && n !== 1) alarmes.sem.push(s);
    if (!naJanela && n !== 0) alarmes.fora.push(s);
    cur.alarmes.forEach((al) => {
      alarmes.nivel[al.nivel] = (alarmes.nivel[al.nivel] || 0) + 1; alarmes.ids[al.id] = (alarmes.ids[al.id] || 0) + 1;
      const j = janelas.find((x) => x.id === al.id && x.nivel === al.nivel && x.ini <= t && t <= x.fim);
      const desde = new Date(anc + (s - t + (j ? j.ini : t)) * 1000).toISOString().replace('.000Z', 'Z');
      if (al.desde !== desde || al.valor !== cur[al.campo]) alarmes.desdeErrado.push(s);
    });
    prev = cur;
  }
  // a virada das 07:00: A − 1 s × A
  const a0 = R.em(anc + 86399 * 1000), a1 = R.em(anc + 86400 * 1000);
  const virada = { passo: {}, d0: [a0.destino, a1.destino], eta: [a0.eta, a1.eta], wp: [a0.wp_proximo, a1.wp_proximo], t1: a1.timestamp_utc, a1d: a1.destino_mn };
  for (const c of campos) if (typeof a1[c] === 'number') virada.passo[c] = a1[c] - a0[c];
  // o laço: |v(149) − v(0)| ≤ o maior passo de 1 s da volta, nos campos do laço
  const laco = {}, q = []; for (let t = 0; t < 150; t++) q.push(R.em(anc + t * 1000));
  for (const c of campos) {
    if (cat[c].origem !== 'laço') continue;
    let mx = 0; for (let t = 0; t < 149; t++) mx = Math.max(mx, passo(q[t][c], q[t + 1][c], c));
    laco[c] = { emenda: passo(q[149][c], q[0][c], c), maior: mx };
  }
  return { nulos, dentro, emenda, fixosMudaram, monotonia, discNaEmenda, alarmes, virada, laco, sentido };
}"""


def o_dia(b):
    print('O dia de bordo inteiro (86.400 segundos): emendas de 150 s, a virada das 07:00, contadores e alarmes')
    pg = abre(b)
    r = pg.evaluate(DIA_JS)
    ok('os 86.400 segundos do dia de bordo dão quadro (nenhum null)', r['nulos'] == 0, r['nulos'])
    estoura = {c: (r['emenda'][c], r['dentro'].get(c, 0)) for c in r['emenda'] if r['emenda'][c] > r['dentro'].get(c, 0) + 1e-9}
    ok('as 575 emendas de 150 s (segundos consecutivos): nenhum campo numérico passa do maior passo de 1 s do dia (%d campos conferidos)' % len(r['emenda']), estoura == {}, estoura)
    ok('na emenda destino, próximo ponto e ETA não mudam, e marcha, estado e âncora também não', r['discNaEmenda'] == [] and r['fixosMudaram'] == [], (r['discNaEmenda'][:3], r['fixosMudaram'][:3]))
    ruins = {c: v for c, v in r['laco'].items() if v['emenda'] > v['maior'] + 1e-9}
    ok('o laço: |v(149) − v(0)| ≤ o maior passo de 1 s da volta, em cada campo do laço (%d campos)' % len(r['laco']), ruins == {} and len(r['laco']) > 20, ruins)
    ok('contadores sem voltar (D.campos[c].sentido, %d campos) em todo o dia, fora do par A − 1 s × A' % len(r['sentido']), r['monotonia'] == [] and len(r['sentido']) == 8, (r['monotonia'][:3], r['sentido']))
    v = r['virada']
    ok('a virada das 07:00 é a descontinuidade: o diesel volta a cheio, os horímetros e a distância recomeçam, os tanques de água e servidas também',
       v['passo']['diesel_litros'] > 1000 and v['passo']['distancia_mn'] < -300 and v['passo']['motor_bb_horimetro_h'] < -20 and v['passo']['tanque_agua_pct'] > 25
       and v['passo']['tanque_cinzas_pct'] < -20 and v['passo']['tanque_negras_pct'] < -15, v['passo'])
    ok('na virada a rota recomeça (destino Barra Sul → %s, ETA %s → %s) e a posição e o COG continuam contínuos' % (v['d0'][1], v['eta'][0], v['eta'][1]),
       v['d0'][0] == D['rota']['volta']['nome'] and v['d0'][1] == D['rota']['destino']['nome'] and v['eta'][0] == '07:00'
       and abs(v['passo']['lat']) <= r['dentro']['lat'] + 1e-9 and abs(v['passo']['lon']) <= r['dentro']['lon'] + 1e-9 and abs(v['passo']['cog_graus']) <= r['dentro']['cog_graus'] + 1e-9, v)
    al = r['alarmes']
    ok('alarme só na janela do gerador (%d–%d s de cada volta): uma por segundo dentro, nenhuma fora, ao longo do dia todo' % (JANELA_INI, JANELA_FIM), al['sem'] == [] and al['fora'] == [], (al['sem'][:3], al['fora'][:3]))
    ok('o alarme é sempre um AVISO (nunca crítico), do arref_be, e o `desde` é o começo da janela da volta', al['nivel'].keys() == {'aviso'} and list(al['ids']) == ['arref_be'] and al['desdeErrado'] == [],
       (al['nivel'], al['ids'], al['desdeErrado'][:3]))
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


# ——— 3. alarmes(), janela() e o cenário ———
ALARMES_JS = r"""() => {
  const R = window.CapitaoReplay, A = window.CapitaoAgora, D = window.CapitaoDados, anc = A.ancora(Date.now()), base = anc + 120 * 150 * 1000, o = {};
  o.a105 = R.alarmes(base + 105000); o.a60 = R.alarmes(base + 60000); o.igual = JSON.stringify(R.alarmes(base + 105000)) === JSON.stringify(R.em(base + 105000).alarmes);
  o.j105 = R.janela('arref_be', base + 105000); o.j116 = R.janela('arref_be', base + 116000); o.j117 = R.janela('arref_be', base + 117000);
  o.j10 = R.janela('arref_be', base + 10000); o.j99 = R.janela('arref_be', base + 99000); o.j98 = R.janela('arref_be', base + 98000); o.nada = R.janela('nao_existe', base); o.proto = [R.janela('constructor', base), R.janela('toString', base), R.janela('__proto__', base)];
  o.base = base; o.iso = (ms) => new Date(ms).toISOString();
  // adultera o limite do crítico (o gerador do cenário aviso não o emite): o cliente só avisa
  const L = D.replay.limites.motor_be_arref_c, antes = JSON.stringify(L), c0 = D.replay.cenario;
  L.critico = { acima: 85 };
  D.replay.cenario = 'aviso';
  const quadros = []; for (let t = 0; t < 150; t++) quadros.push(R.em(base + t * 1000).alarmes);
  o.avisoNiveis = [...new Set([].concat(...quadros).map((x) => x.nivel))]; o.avisoLimite105 = quadros[105][0] && quadros[105][0].limite;
  D.replay.cenario = 'alarme-critico';
  const q2 = R.em(base + 105000).alarmes; o.critico105 = q2[0] && [q2[0].nivel, q2[0].limite];
  D.replay.cenario = c0; L.critico = JSON.parse(antes).critico;
  if (L.critico === undefined) delete L.critico;
  o.restaurado = JSON.stringify(L) === antes;
  return o;
}"""


def a_alarmes(b):
    print('Alarmes: alarmes(), janela() e o cenário aviso (nunca crítico)')
    pg = abre(b)
    r = pg.evaluate(ALARMES_JS)
    base = r['base']
    a = r['a105'][0]
    ok('alarmes(): em t = 105 um AVISO do arref_be (motores, BE, 89,6 °C, limite 88) e em t = 60 nenhum; igual ao em().alarmes',
       len(r['a105']) == 1 and a['id'] == 'arref_be' and a['nivel'] == 'aviso' and a['sistema'] == 'motores' and a['lado'] == 'be' and a['campo'] == 'motor_be_arref_c'
       and a['valor'] == 89.6 and a['limite'] == 88 and r['a60'] == [] and r['igual'], r['a105'])
    ok('janela(): ativa em 99 e em 105 (desde o segundo 99, ate null) e em 116; em 117 já normalizada (ate = 117 s)',
       r['j105'] == {'ativo': True, 'desde': base + 99000, 'ate': None} and r['j99']['ativo'] is True and r['j116']['ativo'] is True and r['j116']['ate'] is None
       and r['j117'] == {'ativo': False, 'desde': base + 99000, 'ate': base + 117000}, (r['j105'], r['j116'], r['j117']))
    ok('janela() antes da janela da volta (t = 10 e 98) devolve a da volta anterior; id que não existe (ou \'constructor\', \'toString\') dá null',
       r['j10'] == {'ativo': False, 'desde': base - 150000 + 99000, 'ate': base - 150000 + 117000} and r['j98']['ativo'] is False and r['j98']['desde'] == base - 150000 + 99000
       and r['nada'] is None and r['proto'] == [None, None, None], (r['j10'], r['j98'], r['nada'], r['proto']))
    ok('cenário aviso, mesmo com o limite do crítico adulterado (acima de 85): nunca devolve crítico, e o limite do alarme é o do aviso (88)',
       r['avisoNiveis'] == ['aviso'] and r['avisoLimite105'] == 88, (r['avisoNiveis'], r['avisoLimite105']))
    ok('cenário alarme-critico (só no gerador; aqui adulterado): o crítico passa, com o limite dele', r['critico105'] == ['critico', 85], r['critico105'])
    ok('o teste devolveu os limites como estavam', r['restaurado'] is True)
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


# ——— 4. o relógio: sincronia entre abas, fixar, #replay, localStorage, sobre ———
LEITURA_T = """() => { const R = window.CapitaoReplay, A = window.CapitaoAgora, now = Date.now(), anc = A.ancora(now);
  return { now, anc, t: R.t(now), esperado: Math.floor((now - anc) / 1000) % 150, agora: R.agora(), fase: R.fase(now).nome }; }"""


def sincronia(b):
    print('Sincronia: a fase pelo relógio, duas abas, dois aparelhos e a troca de página')
    ctx = b.new_context(service_workers='block')
    ctx.add_init_script(GRAVA)
    ctx.route('**/*', so_local)
    for nome in ('replay', 'replay2'):
        ctx.route('**/' + nome + '.html', lambda route: route.fulfill(body=HTML, content_type='text/html; charset=utf-8'))
    a, b2 = ctx.new_page(), ctx.new_page()
    a.goto(BASE + '/replay.html')
    b2.goto(BASE + '/replay2.html')
    for p in (a, b2):
        p.wait_for_function('() => window.CapitaoReplay && window.CapitaoReplay.ativo()')
    r = a.evaluate(LEITURA_T)
    ok('t(ms) é o segundo da volta pelo relógio (âncora de 07:00, voltas de 150 s): fase %s, t = %d' % (r['fase'], r['t']), r['t'] == r['esperado'] and abs(r['agora'] - r['now']) < 50, r)
    ok('a âncora de 07:00 cai numa fronteira de 150 s do relógio absoluto: t = floor(Date.now()/1000) % 150 (a fase não depende de aparelho nem de fuso)',
       r['t'] == (r['now'] // 1000) % 150 and (r['anc'] // 1000) % 150 == 0, (r['t'], (r['now'] // 1000) % 150, (r['anc'] // 1000) % 150))
    ms = a.evaluate("() => Math.floor(Date.now() / 1000) * 1000 + 1000")   # um segundo à frente: os dois leem o mesmo
    qa, qb = a.evaluate("(ms) => JSON.stringify(window.CapitaoReplay.em(ms))", ms), b2.evaluate("(ms) => JSON.stringify(window.CapitaoReplay.em(ms))", ms)
    ok('duas abas (duas páginas do mesmo aparelho) leem o mesmo quadro no mesmo instante', qa == qb and qa != 'null', qa[:80])
    ctx2 = b.new_context(service_workers='block')
    ctx2.route('**/*', so_local)
    ctx2.route('**/replay.html', lambda route: route.fulfill(body=HTML, content_type='text/html; charset=utf-8'))
    c = ctx2.new_page()
    c.goto(BASE + '/replay.html')
    c.wait_for_function('() => window.CapitaoReplay && window.CapitaoReplay.ativo()')
    qc = c.evaluate("(ms) => JSON.stringify(window.CapitaoReplay.em(ms))", ms)
    ok('outro aparelho (contexto novo, nenhum dado em comum) lê o mesmo quadro no mesmo instante', qc == qa, '')
    # nas leituras ao vivo, as duas abas ficam no mesmo segundo (ou no vizinho): lê as duas e compara o timestamp
    ts = []
    for _ in range(3):
        ts.append((a.evaluate("() => window.CapitaoReplay.quadro().timestamp_utc"), b2.evaluate("() => window.CapitaoReplay.quadro().timestamp_utc")))
    ok('ao vivo, quadro() das duas abas: o mesmo segundo ou o vizinho', all(abs(datetime.fromisoformat(x.replace('Z', '+00:00')).timestamp() - datetime.fromisoformat(y.replace('Z', '+00:00')).timestamp()) <= 1 for x, y in ts), ts)
    t_antes = a.evaluate("() => window.CapitaoReplay.t()")
    a.goto(BASE + '/replay2.html')
    a.wait_for_function('() => window.CapitaoReplay && window.CapitaoReplay.ativo()')
    r = a.evaluate(LEITURA_T)
    ok('trocar de página não volta ao segundo 0: a fase continua pelo relógio (antes %d, depois %d)' % (t_antes, r['t']), r['t'] == r['esperado'] and r['t'] != 0 or r['esperado'] == 0, (t_antes, r))
    ctx.close()
    ctx2.close()


FIXAR_JS = r"""() => {
  const R = window.CapitaoReplay, A = window.CapitaoAgora, D = window.CapitaoDados, anc = A.ancora(Date.now()), o = {};
  // a chamada SEM argumento lê o instante fixado: contadores(), janela(id) e porFaixa() iguais às de contadoresEm/janela/porFaixa do fixo(), e diferentes das do relógio
  const J = JSON.stringify, semArg = () => { const T = R.fixo(), jn = R.janela('arref_be'); return { cont: R.contadores() !== null && J(R.contadores()) === J(R.contadoresEm(T)),
    jan: jn !== null && J(jn) === J(R.janela('arref_be', T)), ativa: jn && jn.ativo, faixa: R.porFaixa() !== null && J(R.porFaixa()) === J(R.porFaixa(T)),
    real: J(R.contadoresEm(Date.now())) !== J(R.contadoresEm(T)) && J(R.porFaixa(Date.now())) !== J(R.porFaixa(T)) }; };
  const le = () => ({ fixo: R.fixo(), agora: R.agora(), hora: A.fmt.hora(R.agora(), true), t: R.t(), fase: R.fase().nome, ls: localStorage.getItem('capitao.replay.fixo'),
                      relogio: A.relogio.ms, q: R.quadro(), inst: (() => { const i = A.instante(); return { fonte: i.fonte, hora: i.hora, seg: i.seg, rpm: A.fmt.campo(i.q, 'motor_bb_rpm') }; })() });
  window.__ev.length = 0;
  o.t60 = R.fixar('60'); o.s60 = le(); o.ev60 = window.__ev.map((e) => e.n); o.sem60 = semArg();
  o.t60n = R.fixar(60); o.n60 = R.fixo();
  o.t60k = R.fixar('60@120'); o.k60 = R.fixo();
  o.t10 = R.fixar('60@10'); o.s10 = le(); o.sem10 = semArg();
  window.__ev.length = 0; o.t105 = R.fixar('105'); o.s105 = le(); o.ev105 = window.__ev.map((e) => e.n); o.sem105 = semArg();
  o.q105 = R.quadro(105); o.q60 = R.quadro(60); o.emT = JSON.stringify(R.em(R.fixo())) === JSON.stringify(R.quadro());
  o.qt = JSON.stringify(R.quadro(30)) === JSON.stringify(R.em(R.fixo() - 75000));
  o.ruim = [R.fixar('abc'), R.fixar({}), R.fixar(NaN), R.fixar(Infinity), R.fixar('60@'), R.fixar(1e12), R.fixar('9@99999999')]; o.depoisRuim = R.fixo();
  o.semArg = R.fixar();
  window.__ev.length = 0; o.solta = R.fixar(null); o.sSolta = { fixo: R.fixo(), ls: localStorage.getItem('capitao.replay.fixo'), dif: Math.abs(R.agora() - Date.now()), relogio: Math.abs(A.relogio.ms - Date.now()), ev: window.__ev.map((e) => e.n) };
  o.anc = anc;
  return o;
}"""


def a_fixar(b):
    print('fixar(): 12:01:00 (voltas_fixo), \'60@K\', fixar(null), localStorage e o rodapé')
    pg = abre(b)
    r = pg.evaluate(FIXAR_JS)
    T60 = r['anc'] + (D['replay']['voltas_fixo'] * VOLTA + 60) * 1000
    s = r['s60']
    ok('fixar(\'60\') = âncora + %d voltas + 60 s = 12:01:00 (devolve o instante em ms; fixo(), agora() e a hora da âncora)' % D['replay']['voltas_fixo'],
       r['t60'] == T60 and s['fixo'] == T60 and s['agora'] == T60 and s['hora'] == '12:01:00' and s['q']['timestamp_utc'] == datetime.fromtimestamp(T60 / 1000, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
       (r['t60'], T60, s['hora']))
    ok('fixado: t() = 60, fase cruzeiro, localStorage \'capitao.replay.fixo\' = \'60\' e o rodapé refeito para o instante (relogio.ms = T)',
       s['t'] == 60 and s['fase'] == 'cruzeiro' and s['ls'] == '60' and s['relogio'] == T60, (s['t'], s['fase'], s['ls'], s['relogio'] - T60))
    ok('fixado em 60, o CapitaoAgora.instante() é do replay às 12:01:00 (seg 60) e lê o mesmo rpm que o quadro',
       s['inst'] == {'fonte': 'replay', 'hora': '12:01:00', 'seg': 60, 'rpm': '2.049'}, s['inst'])
    q = s['q']
    ok('os números do §1.22 em 12:01:00: rpm 2.049 / 2.038, SOG 18,1, diesel 1.333 L, 65,1 mn, horímetros 417,6 / 414,8 / 1.241,4, tanques 86 / 15 / 9,5, ETA 12:03, sem alarme',
       q['motor_bb_rpm'] == 2049 and q['motor_be_rpm'] == 2038 and q['sog_nos'] == 18.1 and q['diesel_litros'] == 1333 and q['distancia_mn'] == 65.1
       and (q['motor_bb_horimetro_h'], q['motor_be_horimetro_h'], q['gerador_horimetro_h']) == (417.6, 414.8, 1241.4)
       and (q['tanque_agua_pct'], q['tanque_cinzas_pct'], q['tanque_negras_pct']) == (86, 15, 9.5) and q['eta'] == '12:03' and q['alarmes'] == [], q)
    ok('fixar() emite \'capitao-rebase\' e já um tique (\'capitao-telemetria\'), na hora', r['ev60'].count('capitao-rebase') == 1 and 'capitao-telemetria' in r['ev60'], r['ev60'])
    ok('fixar(60) (número) = fixar(\'60\') = fixar(\'60@%d\')' % D['replay']['voltas_fixo'], r['t60n'] == T60 and r['n60'] == T60 and r['t60k'] == T60 and r['k60'] == T60)
    T10 = r['anc'] + (10 * VOLTA + 60) * 1000
    ok('fixar(\'60@10\') = âncora + 10 voltas + 60 s = 07:26:00 e o localStorage guarda \'60@10\'', r['t10'] == T10 and r['s10']['hora'] == '07:26:00' and r['s10']['ls'] == '60@10', (r['s10']['hora'], r['s10']['ls']))
    s = r['s105']
    ok('fixar(\'105\') = 12:01:45: o AVISO do arref_be (89,6 °C) desde 12:01:39, e o evento \'capitao-alerta\' de início',
       s['hora'] == '12:01:45' and s['q']['motor_be_arref_c'] == 89.6 and len(s['q']['alarmes']) == 1 and s['q']['alarmes'][0]['desde'] == datetime.fromtimestamp((r['anc'] + (D['replay']['voltas_fixo'] * VOLTA + 99) * 1000) / 1000, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
       and 'capitao-alerta' in r['ev105'], (s['hora'], s['q']['alarmes'], r['ev105']))
    ok('quadro(t) com o instante fixado: a volta fixada (contadores e rota dela); quadro() = em(fixo()); quadro(30) = em(T − 75 s)', r['emT'] is True and r['qt'] is True and r['q105'] == r['s105']['q'], (r['emT'], r['qt']))
    ok('fixado, contadores(), janela(id) e porFaixa() SEM argumento leem o instante fixado (iguais às chamadas com fixo(); o relógio daria outro dia) em 12:01:00, 07:26:00 e 12:01:45; a janela do arref_be está ativa só às 12:01:45',
       all(r[k]['cont'] and r[k]['jan'] and r[k]['faixa'] for k in ('sem60', 'sem10', 'sem105')) and sum(1 for k in ('sem60', 'sem10', 'sem105') if r[k]['real']) >= 2
       and r['sem105']['ativa'] is True and r['sem60']['ativa'] is False and r['sem10']['ativa'] is False, (r['sem60'], r['sem10'], r['sem105']))
    ok('fixar com argumento inválido (\'abc\', {}, NaN, Infinity, \'60@\', 1e12, \'9@99999999\') não muda nada e não lança; fixar() sem argumento devolve o fixo atual',
       all(x is None for x in r['ruim']) and r['depoisRuim'] == r['t105'] and r['semArg'] == r['t105'], (r['ruim'], r['depoisRuim'], r['semArg']))
    ok('fixar(null) solta: fixo() null, a chave do localStorage some, agora() volta ao relógio, o rodapé refaz com Date.now() e sai \'capitao-rebase\'',
       r['solta'] is None and r['sSolta']['fixo'] is None and r['sSolta']['ls'] is None and r['sSolta']['dif'] < 100 and r['sSolta']['relogio'] < 100 and 'capitao-rebase' in r['sSolta']['ev'], r['sSolta'])
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)

    print('Congelamento na carga: localStorage, #replay=<s> (vale só nesta carga) e o gancho \'sobre\'')
    LE = """() => { const R = window.CapitaoReplay, A = window.CapitaoAgora; return { fixo: R.fixo(), hora: R.fixo() === null ? null : A.fmt.hora(R.fixo(), true), ls: localStorage.getItem('capitao.replay.fixo'), anc: A.ancora(Date.now()),
      q: R.quadro(), ev: window.__ev.map((e) => e.n + (e.n === 'capitao-alerta' ? ':' + e.d.fase : '')) }; }"""
    pg = abre(b, init="localStorage.setItem('capitao.replay.fixo', '60@120');")
    r = pg.evaluate(LE)
    ok('localStorage \'capitao.replay.fixo\' = \'60@120\' na carga: fixado em 12:01:00, sem alarme', r['hora'] == '12:01:00' and r['q']['alarmes'] == [], r)
    fecha(pg)
    pg = abre(b, init="localStorage.setItem('capitao.replay.fixo', '105');")
    r = pg.evaluate(LE)
    ok('localStorage \'105\' na carga: 12:01:45 e o alarme que já está ativo conta como início (\'capitao-alerta\' inicio no 1º tique da página)', r['hora'] == '12:01:45' and 'capitao-alerta:inicio' in r['ev'], r)
    fecha(pg)
    pg = abre(b, caminho='/replay.html#replay=105', init="localStorage.setItem('capitao.replay.fixo', '60');")
    r = pg.evaluate(LE)
    ok('#replay=105 ganha do localStorage, vale só nesta carga: o localStorage continua \'60\'', r['hora'] == '12:01:45' and r['ls'] == '60', r)
    fecha(pg)
    pg = abre(b, caminho='/replay.html#replay=60@10')
    r = pg.evaluate(LE)
    ok('#replay=60@10 = 07:26:00 e não vai para o localStorage', r['hora'] == '07:26:00' and r['ls'] is None, r)
    fecha(pg)
    pg = abre(b, caminho='/replay.html#replay=sair', init="localStorage.setItem('capitao.replay.fixo', '60');")
    r = pg.evaluate(LE)
    ok('#replay=sair solta o instante e limpa a chave', r['fixo'] is None and r['ls'] is None, r)
    fecha(pg)
    pg = abre(b, caminho='/replay.html#replay=xx')
    r = pg.evaluate(LE)
    ok('#replay=xx (inválido) é ignorado: o replay anda pelo relógio', r['fixo'] is None, r)
    fecha(pg)
    SOBRE = json.dumps({'sog_nos': 0, 'estado': 'Fundeado', 'alarmes': []})
    pg = abre(b, init="localStorage.setItem('capitao.replay.sobre', %s);" % json.dumps(SOBRE))
    r = pg.evaluate("() => ({ sog: window.CapitaoReplay.quadro().sog_nos, estado: window.CapitaoReplay.quadro().estado })")
    ok('\'capitao.replay.sobre\' sem o instante fixado não faz nada (nunca age no uso normal)', r['sog'] > 0 and r['estado'] == 'Navegando', r)
    r = pg.evaluate("""() => { const R = window.CapitaoReplay, A = window.CapitaoAgora; const T = R.fixar('105');
      return { q: R.quadro(), i: A.instante().q.estado, em: R.em(T), outro: R.em(T + 1000), idem: JSON.stringify(R.em(T)) === JSON.stringify(R.quadro()) }; }""")
    ok('com o instante fixado o \'sobre\' entra no quadro (SOG 0, Fundeado, sem alarme, mesmo a 12:01:45) e o instante() lê o mesmo',
       r['q']['sog_nos'] == 0 and r['q']['estado'] == 'Fundeado' and r['q']['alarmes'] == [] and r['i'] == 'Fundeado' and r['idem'], r['q'])
    ok('o \'sobre\' vale só no instante fixado: um segundo depois o quadro é o do replay', r['outro']['sog_nos'] > 0 and r['outro']['estado'] == 'Navegando', r['outro']['sog_nos'])
    fecha(pg)
    # a lista literal do 'sobre' também obedece ao cenário: fora do 'alarme-critico' nunca sai crítico (decisão c), nem em alarmes(), nem no quadro, nem no evento
    crit = {'id': 'arref_be', 'nivel': 'critico', 'campo': 'motor_be_arref_c', 'valor': 120, 'limite': 100, 'desde': 'x'}
    SOBRE_CRIT = json.dumps({'alarmes': [crit, dict(crit, id='arref_bb', nivel='CRITICO'), 7, None, 'x']})
    LE_CRIT = """() => { const R = window.CapitaoReplay, fases = (n) => window.__ev.filter((e) => e.n === n).map((e) => e.d.fase + ':' + e.d.alarme.id + ':' + e.d.alarme.nivel);
      const T = R.fixo(); return { cen: window.CapitaoDados.replay.cenario, fixo: T !== null, al: R.alarmes(), q: R.quadro().alarmes, em: R.em(T).alarmes, tele: window.__ev.filter((e) => e.n === 'capitao-telemetria').map((e) => e.d.alarmes),
        alertas: fases('capitao-alerta') }; }"""
    pg = abre(b, init="localStorage.setItem('capitao.replay.fixo', '60'); localStorage.setItem('capitao.replay.sobre', %s);" % json.dumps(SOBRE_CRIT))
    pg.wait_for_timeout(300)
    r = pg.evaluate(LE_CRIT)
    niveis = [x['nivel'] for x in r['al'] + r['q'] + r['em']] + [x['nivel'] for t in r['tele'] for x in (t or [])] + [a.split(':')[2] for a in r['alertas']]
    ok('\'sobre\' com alarme crítico (e \'CRITICO\') e cenario \'aviso\': alarmes(), quadro(), em() e o evento \'capitao-alerta\' só têm AVISO; os itens que não são objeto saem',
       r['cen'] == 'aviso' and r['fixo'] and niveis != [] and set(niveis) == {'aviso'} and [x['id'] for x in r['al']] == ['arref_be', 'arref_bb'] and r['al'] == r['q'] == r['em']
       and r['alertas'] == ['inicio:arref_be:aviso', 'inicio:arref_bb:aviso'], r)
    fecha(pg)
    pg = abre(b, init="localStorage.setItem('capitao.replay.fixo', '60'); localStorage.setItem('capitao.replay.sobre', %s);" % json.dumps(SOBRE_CRIT),
              depois="window.CapitaoDados.replay.cenario = 'alarme-critico';")
    pg.wait_for_timeout(300)
    r = pg.evaluate(LE_CRIT)
    ok('controle: no cenario \'alarme-critico\' (só no gerador; aqui injetado) o crítico do \'sobre\' passa, e o \'CRITICO\' escrito à mão também segue como veio',
       r['cen'] == 'alarme-critico' and [x['nivel'] for x in r['al']] == ['critico', 'CRITICO'] and r['alertas'] == ['inicio:arref_be:critico', 'inicio:arref_bb:CRITICO'], r)
    fecha(pg)
    # entre 00:00 e 07:00 o instante congelado é "ontem 12:01" e os prazos acompanham (CONTRATO §4.1)
    madrugada = datetime(2026, 10, 27, 3, 0, tzinfo=BR)
    pg = abre(b, local=madrugada)
    r = pg.evaluate("""() => { const R = window.CapitaoReplay, A = window.CapitaoAgora, antes = { hoje: A.relogio.hoje, anc: A.ancora(Date.now()) }; const T = R.fixar('60');
      return { antes, T, hora: A.fmt.hora(T, true), relogio: A.relogio, versao: window.CapitaoDados.versao, anc: A.ancora(T), atrasadas: window.CapitaoDados.agenda.filter((t) => t.dn < 0).length }; }""")
    ontem = datetime(2026, 10, 26, 12, 1, tzinfo=BR)
    ok('às 03:00 de 27/10, fixar(\'60\') é ontem 12:01:00 (26/10) e o rodapé refaz hoje = 26/10/2026, versão 26/10/2026',
       r['T'] == int(ontem.timestamp() * 1000) and r['hora'] == '12:01:00' and r['antes']['hoje'] == '27/10/2026' and r['relogio']['hoje'] == '26/10/2026' and r['versao'] == '26/10/2026', r)
    fecha(pg)


# ——— 5. eventos ———
def eventos_ritmo(b):
    print('Eventos: capitao-telemetria a cada 1 s, alinhado ao segundo')
    pg = abre(b)
    pg.wait_for_timeout(300)
    pg.evaluate("() => { window.__ev.length = 0; }")
    pg.wait_for_timeout(3500)
    ev = pg.evaluate("() => window.__ev.filter((e) => e.n === 'capitao-telemetria').map((e) => [e.t, e.p, e.d.timestamp_utc, e.d.simulado])")
    ok('\'capitao-telemetria\' a cada 1 s: 3 ou 4 eventos em 3,5 s (%d)' % len(ev), 3 <= len(ev) <= 4, ev)
    inter = [ev[i + 1][1] - ev[i][1] for i in range(len(ev) - 1)]
    ok('os intervalos são de 1 s (900 a 1.150 ms): %s' % [round(x) for x in inter], all(900 <= x <= 1150 for x in inter), inter)
    ok('alinhados ao segundo (o milissegundo do relógio de cada evento fica nos primeiros 250 ms do segundo)', all(e[0] % 1000 < 250 for e in ev), [e[0] % 1000 for e in ev])
    ok('o detail é o quadro do segundo do evento (timestamp_utc do mesmo segundo) com simulado: true', all(e[3] is True and abs(datetime.fromisoformat(e[2].replace('Z', '+00:00')).timestamp() - e[0] / 1000) < 1.0 for e in ev), ev[:2])
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


def eventos_pausa(b):
    print('Eventos: pausa com document.hidden e tique imediato na volta à frente')
    pg = abre(b)
    pg.wait_for_timeout(300)
    pg.evaluate(r"""() => { window.__oculto = true;
      Object.defineProperty(document, 'hidden', { configurable: true, get: () => !!window.__oculto });
      document.dispatchEvent(new Event('visibilitychange')); window.__ev.length = 0; return true; }""")
    pg.wait_for_timeout(2400)
    parado = pg.evaluate("() => window.__conta('capitao-telemetria')")
    ok('com document.hidden o motor não emite nenhum evento (2,4 s: %d)' % parado, parado == 0, parado)
    r = pg.evaluate(r"""() => { window.__oculto = false; window.__ev.length = 0; document.dispatchEvent(new Event('visibilitychange')); return window.__conta('capitao-telemetria'); }""")
    ok('na volta à frente o tique é imediato (já dentro do visibilitychange)', r == 1, r)
    pg.wait_for_timeout(1300)
    seguiu = pg.evaluate("() => window.__conta('capitao-telemetria')")
    ok('e depois segue a cada 1 s', 2 <= seguiu <= 3, seguiu)
    fecha(pg)


def eventos_timer(b):
    print('Eventos: um timer só por página')
    pg = abre(b)
    pg.wait_for_timeout(300)
    pg.evaluate("() => { delete window.CapitaoReplay; }")
    pg.add_script_tag(url=BASE + '/capitao-replay.js')
    pg.evaluate("() => { window.__ev.length = 0; }")
    pg.wait_for_timeout(3300)
    n = pg.evaluate("() => window.__conta('capitao-telemetria')")
    ok('um timer só por página: o arquivo carregado de novo na mesma página não dobra os tiques (%d em 3,3 s)' % n, 2 <= n <= 4, n)
    fecha(pg)


def eventos_alertas(b):
    print('Eventos: capitao-alerta (inicio, nivel, fim)')
    pg = abre(b)
    r = pg.evaluate(r"""() => { const R = window.CapitaoReplay, f = (n) => window.__ev.filter((e) => e.n === n).map((e) => (e.d.fase || '') + ':' + (e.d.alarme ? e.d.alarme.id + ':' + e.d.alarme.nivel : ''));
      R.fixar('60'); window.__ev.length = 0;
      R.fixar('105'); const inicio = f('capitao-alerta'); window.__ev.length = 0;
      R.fixar('105'); const repete = f('capitao-alerta'); window.__ev.length = 0;
      const D = window.CapitaoDados, L = D.replay.limites.motor_be_arref_c; L.critico = { acima: 85 }; D.replay.cenario = 'alarme-critico';
      R.fixar('105'); const nivel = f('capitao-alerta'); L.critico = undefined; delete L.critico; D.replay.cenario = 'aviso'; window.__ev.length = 0;
      R.fixar('125'); const fim = f('capitao-alerta'); window.__ev.length = 0;
      R.fixar('60'); const nada = f('capitao-alerta');
      return { inicio, repete, nivel, fim, nada }; }""")
    ok('\'capitao-alerta\': inicio ao entrar no AVISO (arref_be), nada ao repetir o mesmo, nivel quando ele sobe, fim ao sair (com o último alarme conhecido)',
       r['inicio'] == ['inicio:arref_be:aviso'] and r['repete'] == [] and r['nivel'] == ['nivel:arref_be:critico'] and r['fim'] == ['fim:arref_be:critico'] and r['nada'] == [], r)
    fecha(pg)


def eventos_virada(b):
    print('Eventos: capitao-rebase na virada das 07:00 e da meia-noite (Date congelado, que o teste move)')
    for nome, de, para, chave in (('as 07:00', datetime(2026, 10, 27, 6, 59, 58, 900000, tzinfo=BR), datetime(2026, 10, 27, 7, 0, 0, 600000, tzinfo=BR), 'diaBordo'),
                                  ('a meia-noite', datetime(2026, 10, 27, 23, 59, 58, 900000, tzinfo=BR), datetime(2026, 10, 28, 0, 0, 0, 600000, tzinfo=BR), 'hoje')):
        pg = abre(b, local=de)
        antes = pg.evaluate("() => ({ r: window.CapitaoAgora.relogio, ab: window.CapitaoDados.abastecimentos[0].d, versao: window.CapitaoDados.versao })")
        pg.wait_for_timeout(1300)
        sem = pg.evaluate("() => window.__conta('capitao-rebase')")
        pg.evaluate("(ms) => { window.__T0 = ms; }", int(para.timestamp() * 1000))
        pg.wait_for_timeout(1600)
        depois = pg.evaluate("() => ({ r: window.CapitaoAgora.relogio, ab: window.CapitaoDados.abastecimentos[0].d, versao: window.CapitaoDados.versao, n: window.__conta('capitao-rebase') })")
        pg.wait_for_timeout(1300)
        mais = pg.evaluate("() => window.__conta('capitao-rebase')")
        ok('virada %s com a página aberta: \'capitao-rebase\' uma vez, só na virada (antes %d, depois %d, 1,3 s depois %d)' % (nome, sem, depois['n'], mais), sem == 0 and depois['n'] == 1 and mais == 1, (sem, depois['n'], mais))
        ok('virada %s: o rodapé refez o relógio (%s de %s para %s)%s' % (nome, chave, antes['r'][chave], depois['r'][chave], ', os abastecimentos e a versão' if chave == 'hoje' else ' e os abastecimentos'),
           antes['r'][chave] != depois['r'][chave] and (chave == 'hoje' and antes['versao'] != depois['versao'] or chave == 'diaBordo' and antes['ab'] != depois['ab']), (antes, depois))
        ok('virada %s: sem erro de script' % nome, not pg.erros, pg.erros)
        fecha(pg)


OCULTA = "window.__oculto = true; Object.defineProperty(document, 'hidden', { configurable: true, get: () => !!window.__oculto });"


def eventos_virada_oculta(b):
    print('Eventos: a página que carrega OCULTA antes da virada e só depois volta à frente também rebaseia')
    de = datetime(2026, 10, 27, 6, 55, 0, tzinfo=BR)
    for nome, init, para, vira in (('carregada oculta às 06:55, visível às 07:10', OCULTA, datetime(2026, 10, 27, 7, 10, 0, tzinfo=BR), True),
                                   ('carregada visível às 06:55 e vista às 07:10 (controle)', '', datetime(2026, 10, 27, 7, 10, 0, tzinfo=BR), True),
                                   ('carregada oculta às 06:55, visível às 06:58 (sem virada)', OCULTA, datetime(2026, 10, 27, 6, 58, 0, tzinfo=BR), False)):
        pg = abre(b, local=de, init=init)
        pg.wait_for_timeout(1500)
        antes = pg.evaluate("() => ({ diaBordo: window.CapitaoAgora.relogio.diaBordo, n: window.__conta('capitao-rebase'), tele: window.__conta('capitao-telemetria') })")
        pg.evaluate("(ms) => { window.__T0 = ms; window.__oculto = false; document.dispatchEvent(new Event('visibilitychange')); }", int(para.timestamp() * 1000))
        pg.wait_for_timeout(1600)
        depois = pg.evaluate("() => ({ diaBordo: window.CapitaoAgora.relogio.diaBordo, ab: window.CapitaoDados.abastecimentos[0].d, n: window.__conta('capitao-rebase'), hora: window.CapitaoAgora.instante().hora })")
        ok('%s: diaBordo %s → %s, \'capitao-rebase\' %d → %d' % (nome, antes['diaBordo'], depois['diaBordo'], antes['n'], depois['n']),
           antes['diaBordo'] == '26/10/2026' and depois['diaBordo'] == ('27/10/2026' if vira else '26/10/2026') and depois['n'] - antes['n'] == (1 if vira else 0)
           and (init == '' or antes['tele'] == 0), (antes, depois))
        ok('%s: sem erro de script' % nome, not pg.erros, pg.erros)
        fecha(pg)


# ——— 6. isolamento ———
def isolamento(b):
    print('Isolamento: o replay não é o CapitaoTelemetria; atual() e fonte(); o D.snapshot; a âncora; falha → null')
    for nome, html in (('replay antes do capitao-telemetria.js', HTML), ('replay depois do capitao-telemetria.js', HTML_ANTES)):
        pg = abre(b, html=html)
        r = pg.evaluate(r"""() => { const R = window.CapitaoReplay, T = window.CapitaoTelemetria, snap0 = JSON.stringify(window.CapitaoDados.snapshot), a = T.atual();
          const antes = JSON.stringify(window.CapitaoDados.snapshot);
          R.fixar('105'); R.quadro(); R.em(Date.now()); R.serie('sog_nos', '150S'); R.resumo(); T.atual(); window.CapitaoAgora.instante(); R.fixar(null);
          return { distintos: R !== T, tele: Object.keys(T).sort(), chavesR: Object.keys(R).sort(), ativa: T.ativa(), simulado: a && a.simulado === true, fonte: T.fonte(), inst: window.CapitaoAgora.instante().fonte,
                   snap: antes === snap0 && JSON.stringify(window.CapitaoDados.snapshot) === snap0, urlProxy: T.ativa() }; }""")
        ok('%s: dois globais distintos; ativa() = proxy real (false); atual() = quadro do replay com simulado: true; fonte() = \'replay\'; instante() = replay' % nome,
           r['distintos'] and r['ativa'] is False and r['simulado'] and r['fonte'] == 'replay' and r['inst'] == 'replay', r)
        ok('%s: nenhum nome do CapitaoTelemetria no replay (ativa, atual, posicao, hora, busca, coord), nenhum do replay no outro' % nome,
           not set(r['chavesR']) & {'ativa', 'atual', 'posicao', 'hora', 'busca', 'coord', 'idade'} and 'fonte' in r['tele'] and 'em' not in r['tele'], (r['chavesR'], r['tele']))
        ok('%s: o D.snapshot nem um byte diferente depois de fixar, ler, ticar e soltar' % nome, r['snap'], '')
        ok('%s: sem erro de script' % nome, not pg.erros, pg.erros)
        fecha(pg)
    # o coletor real (URL de teste do próprio workers.dev e a chave, como a telemetria já aceita) vale enquanto a leitura for recente
    agora = datetime.now(timezone.utc)
    recente = {'timestamp_utc': (agora - timedelta(seconds=30)).strftime('%Y-%m-%dT%H:%M:%SZ'), 'sog_nos': 3.3, 'lat': -26.99, 'lon': -48.61, 'diesel_litros': 777}
    velha = dict(recente, timestamp_utc=(agora - timedelta(minutes=20)).strftime('%Y-%m-%dT%H:%M:%SZ'))
    for nome, leitura, fonte, inst in (('leitura recente do coletor', recente, 'coletor', 'coletor'), ('leitura de 20 min (velha)', velha, 'replay', 'replay')):
        pg = abre(b, init=("localStorage.setItem('capitao.telemetria.url.v1', 'https://capitao-telemetria.teste.workers.dev'); localStorage.setItem('capitao.telemetria.chave.v1', 'k');"
                           "localStorage.setItem('capitao.telemetria.ultima.v1', %s);" % json.dumps(json.dumps(leitura))))
        r = pg.evaluate("() => { const T = window.CapitaoTelemetria, a = T.atual(); return { ativa: T.ativa(), fonte: T.fonte(), sim: a && a.simulado === true, sog: a && a.sog_nos, inst: window.CapitaoAgora.instante().fonte }; }")
        ok('%s (proxy ativo): ativa() é true, fonte() = \'%s\', o instante() lê %s%s' % (nome, fonte, inst, '' if fonte == 'coletor' else ' (cai no replay, com simulado: true)'),
           r['ativa'] is True and r['fonte'] == fonte and r['inst'] == inst and (r['sim'] is (fonte == 'replay')) and (fonte != 'coletor' or r['sog'] == 3.3), r)
        fecha(pg)
    pg = abre(b, html=HTML_SEM_TELE)
    r = pg.evaluate("() => ({ tele: typeof window.CapitaoTelemetria, inst: window.CapitaoAgora.instante().fonte, hora: window.CapitaoAgora.instante().hora })")
    ok('tela sem o capitao-telemetria.js: o instante() lê o replay direto (CapitaoReplay.em)', r['tele'] == 'undefined' and r['inst'] == 'replay', r)
    # a âncora é a CapitaoAgora.ancora, a mesma função: trocar a propriedade muda o que o replay lê (sem cópia)
    r = pg.evaluate(r"""() => { const A = window.CapitaoAgora, R = window.CapitaoReplay, orig = A.ancora, ms = Date.now(); let n = 0, saiu = [];
      const q0 = R.em(ms); A.ancora = function (x) { n++; return orig(x) - 150000 * 4; };
      const q1 = R.em(ms); const n1 = n; A.ancora = orig;
      return { n1, mesmo: A.ancora === orig, q0: q0.timestamp_utc, q1: q1.timestamp_utc, d: q1.diesel_litros - q0.diesel_litros }; }""")
    ok('âncora única: o replay chama a CapitaoAgora.ancora da hora (n = %d); com a âncora 4 voltas atrás o quadro avança 4 voltas (o diesel cai)' % r['n1'], r['n1'] >= 1 and r['mesmo'] and r['d'] < 0, r)
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


def isolamento_falha(b):
    print('Falha: o D.replay quebrado devolve null (nunca o snapshot), o instante() cai no snapshot e o snapshot não muda')
    pg = abre(b, html=HTML_SEM_TELE)
    pg.wait_for_timeout(1100)   # o instante() é guardado por segundo: um segundo novo, para ele reler as fontes
    r = pg.evaluate(r"""() => { const D = window.CapitaoDados, R = window.CapitaoReplay, snap0 = JSON.stringify(D.snapshot), ok0 = D.replay;
      D.replay = { duracao: 150 }; const o = { em: R.em(Date.now()), q: R.quadro(), c: R.contadoresEm(Date.now()), al: R.alarmes(), s: R.serie('sog_nos', '150S'), r: R.resumo(), ativo: R.ativo() };
      const inst = window.CapitaoAgora.instante(); o.inst = inst && inst.fonte; o.snap = JSON.stringify(D.snapshot) === snap0; o.semAlarmes = inst && inst.q && !('alarmes' in inst.q);
      D.replay = ok0; o.volta = R.ativo() && !!R.quadro(); return o; }""")
    ok('D.replay quebrado: em/quadro/contadoresEm/alarmes/serie/resumo devolvem null (nunca o D.snapshot), ativo() é false, o instante() cai no snapshot e o snapshot não muda; consertado, volta',
       all(r[k] is None for k in ('em', 'q', 'c', 'al', 's', 'r')) and r['ativo'] is False and r['inst'] == 'snapshot' and r['snap'] and r['volta'], r)
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


# ——— 7. SOS: o motor não existe ———
def no_sos(b, so_s1=False):
    print('S1/S2 e rotas /SOS-: sem CapitaoReplay, instante() null, nenhum tique, nenhuma leitura de D.simulacao nem de D.replay')
    for nome, caminho in (('S1-SOS-Web', '/S1-SOS-Web.dc.html'), ('S2-SOS-Mobile', '/S2-SOS-Mobile.dc.html'))[:1 if so_s1 else 2]:
        pg = abre(b, caminho=caminho, antes=GETTER + GETTER_REPLAY)
        pg.wait_for_timeout(2300)
        r = pg.evaluate("() => ({ replay: typeof window.CapitaoReplay, tele: typeof window.CapitaoTelemetria, inst: window.CapitaoAgora.instante(), n: window.__conta('capitao-telemetria'), lidas: window.__lidas, lidasReplay: window.__lidasReplay })")
        ok('%s: CapitaoReplay e CapitaoTelemetria não existem, instante() é null, nenhum tique em 2,3 s, D.simulacao e D.replay nunca lidos' % nome,
           r == {'replay': 'undefined', 'tele': 'undefined', 'inst': None, 'n': 0, 'lidas': 0, 'lidasReplay': 0}, r)
        pg.add_script_tag(url=BASE + '/capitao-replay.js')
        r = pg.evaluate("() => ({ replay: typeof window.CapitaoReplay, inst: window.CapitaoAgora.instante(), lidas: window.__lidas, lidasReplay: window.__lidasReplay })")
        ok('%s: nem o arquivo carregado à força define o CapitaoReplay, e nada é lido' % nome, r == {'replay': 'undefined', 'inst': None, 'lidas': 0, 'lidasReplay': 0}, r)
        ok('%s: sem erro de script' % nome, not pg.erros, pg.erros)
        fecha(pg)
    if so_s1:
        return
    pg = abre(b, caminho='/SOS-teste.html', antes=GETTER + GETTER_REPLAY)
    pg.wait_for_timeout(2300)
    r = pg.evaluate("() => ({ replay: typeof window.CapitaoReplay, tele: typeof window.CapitaoTelemetria, atual: window.CapitaoTelemetria && window.CapitaoTelemetria.atual(), inst: window.CapitaoAgora.instante(), n: window.__conta('capitao-telemetria'), lidas: window.__lidas, lidasReplay: window.__lidasReplay })")
    ok('rota mínima /SOS-teste.html com o replay e o telemetria no <head>: replay não definido, atual() null, instante() null, nenhum tique, nenhuma leitura',
       r['replay'] == 'undefined' and r['atual'] is None and r['inst'] is None and r['n'] == 0 and r['lidas'] == 0 and r['lidasReplay'] == 0, r)
    fecha(pg)
    pg = abre(b, antes=GETTER + GETTER_REPLAY)
    r = pg.evaluate("() => ({ replay: typeof window.CapitaoReplay, lidas: window.__lidas, lidasReplay: window.__lidasReplay, inst: window.CapitaoAgora.instante().fonte })")
    ok('controle fora do SOS (a mesma página com outro nome): o replay existe e lê D.simulacao e D.replay (≥ 1), o instante() é do replay', r['replay'] == 'object' and r['lidas'] >= 1 and r['lidasReplay'] >= 1 and r['inst'] == 'replay', r)
    fecha(pg)


# ——— 8. modo real inerte ———
INERTE_JS = r"""() => { const R = window.CapitaoReplay, T = window.CapitaoTelemetria, D = window.CapitaoDados, ms = Date.now();
  const nomes = ['em', 'quadro', 'contadores', 'contadoresEm', 'alarmes', 'janela', 'fase', 'resumo', 'serie', 'porFaixa', 't'], o = {};
  o.valores = nomes.map((n) => { try { return [n, n === 'serie' ? R.serie('sog_nos', '150S') : n === 'janela' ? R.janela('arref_be') : n === 'contadoresEm' || n === 'em' ? R[n](ms) : R[n]()]; } catch (e) { return [n, 'LANÇOU ' + e]; } })
    .filter((x) => x[1] !== null);
  o.ativo = R.ativo(); o.dur = R.DURACAO; o.fixar = R.fixar(60); o.fixo = R.fixo(); o.ls = localStorage.getItem('capitao.replay.fixo'); o.agora = Math.abs(R.agora() - ms) < 100;
  o.atual = T.atual(); o.fonte = T.fonte(); const i = window.CapitaoAgora.instante(); o.inst = i && i.fonte; o.snapQ = !!(D.snapshot && D.snapshot.quadro);
  o.rebaseSnap = o.inst === 'snapshot';
  return o; }"""


def modo_real_inicial(b):
    print('Modo real inerte: simulacao = false não anda, não dispara, não cai no atual()')
    pg = abre(b, depois='window.CapitaoDados.simulacao = false;')
    pg.wait_for_timeout(2500)
    r = pg.evaluate(INERTE_JS)
    ok('simulacao = false: o objeto existe mas está inerte (ativo() false, DURACAO 150) e em/quadro/contadores/alarmes/janela/fase/resumo/serie/porFaixa/t devolvem null',
       r['valores'] == [] and r['ativo'] is False and r['dur'] == 150, r['valores'])
    ok('simulacao = false: fixar(60) não fixa nada e não escreve no localStorage; agora() é o relógio', r['fixar'] is None and r['fixo'] is None and r['ls'] is None and r['agora'], (r['fixar'], r['fixo'], r['ls']))
    ok('simulacao = false: nenhum evento em 2,5 s, CapitaoTelemetria.atual() e fonte() null, e o instante() vem do D.snapshot.quadro',
       pg.evaluate("() => window.__conta('capitao-telemetria') + window.__conta('capitao-alerta') + window.__conta('capitao-rebase')") == 0 and r['atual'] is None and r['fonte'] is None and r['inst'] == 'snapshot' and r['snapQ'],
       (r['atual'], r['fonte'], r['inst']))
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


def modo_real_flag(b):
    print('Modo real: a flag é lida a cada chamada (a página aberta liga e desliga o motor)')
    pg = abre(b)
    pg.wait_for_timeout(1300)
    pg.evaluate("() => { window.CapitaoDados.simulacao = false; window.__ev.length = 0; }")
    pg.wait_for_timeout(2400)
    parou = pg.evaluate("() => ({ n: window.__conta('capitao-telemetria'), em: window.CapitaoReplay.em(Date.now()), ativo: window.CapitaoReplay.ativo(), atual: window.CapitaoTelemetria.atual() })")
    ok('a flag desligada com a página aberta: os tiques param (0 em 2,4 s), em() null, ativo() false, atual() null', parou == {'n': 0, 'em': None, 'ativo': False, 'atual': None}, parou)
    pg.evaluate("() => { window.CapitaoDados.simulacao = true; window.CapitaoReplay.quadro(); }")
    pg.wait_for_timeout(2400)
    voltou = pg.evaluate("() => ({ n: window.__conta('capitao-telemetria'), ativo: window.CapitaoReplay.ativo(), q: !!window.CapitaoReplay.quadro() })")
    ok('ligada de novo, a primeira chamada da API religa o tique (o imediato e 2 a 3 depois, em 2,4 s)', 3 <= voltou['n'] <= 4 and voltou['ativo'] and voltou['q'], voltou)
    fecha(pg)


# ——— 9. histórico: serie(), porFaixa(), resumo() ———
SERIE_JS = r"""() => {
  const R = window.CapitaoReplay, A = window.CapitaoAgora, D = window.CapitaoDados, H = D.historico, o = { ruins: [], ultimos: [], n: {}, cobertas: 0 };
  R.fixar('60');
  const q = R.quadro(), jan = Object.keys(H.janelas), so150 = [].concat(...H.so150.map((g) => H.metricas[g]));
  const todos = [].concat(...Object.values(H.metricas));
  for (const c of todos) for (const j of jan) {
    const s = R.serie(c, j);
    if (j !== '150S' && so150.indexOf(c) >= 0) { if (s !== null) o.ruins.push(c + ' ' + j + ' devia ser null'); continue; }
    if (!s) { o.ruins.push(c + ' ' + j + ' null'); continue; }
    o.cobertas++; o.n[j] = s.length;
    if (s.length !== H.janelas[j].n) o.ruins.push(c + ' ' + j + ' n=' + s.length);
    for (let i = 0; i < s.length; i++) {
      const p = s[i];
      if (![p.ms, p.v, p.min, p.max].every(Number.isFinite)) { o.ruins.push(c + ' ' + j + ' NaN em ' + i); break; }
      if (p.v < p.min - 1e-9 || p.v > p.max + 1e-9) { o.ruins.push(c + ' ' + j + ' v fora de min/max em ' + i); break; }
      if (i && p.ms <= s[i - 1].ms) { o.ruins.push(c + ' ' + j + ' ms fora de ordem'); break; }
    }
    const u = s[s.length - 1];
    if (u.v !== q[c] || u.ms !== R.agora()) o.ultimos.push(c + ' ' + j + ': ' + u.v + ' × ' + q[c]);
  }
  const mm = (c, j) => { const s = R.serie(c, j); return { min: Math.min(...s.map((p) => p.v)), max: Math.max(...s.map((p) => p.v)), ult: s[s.length - 1].v }; };
  o.ar = { d1: mm('temp_ar_externo_c', '1D'), d30: mm('temp_ar_externo_c', '30D'), a1: mm('temp_ar_externo_c', '1A') };
  o.agua = { d30: mm('temp_agua_c', '30D'), a1: mm('temp_agua_c', '1A') };
  o.praca = mm('temp_praca_maquinas_c', '1A');
  // a serie do diesel de 7 dias: o serrote das linhas de abastecimento (1.560 L às 07:00, 474 L às 06:59:59)
  const sd = R.serie('diesel_litros', '7D'); o.diesel = { max: Math.max(...sd.map((p) => p.max)), min: Math.min(...sd.map((p) => p.min)), ab: D.abastecimentos.slice(0, 3).map((a) => [a.nivelAntes, a.nivelDepois, a.litros]), cap: D.embarcacao.tanques.diesel_l };
  // a trava: com a máx/mín de hoje do clima, o último ponto do ar e da água é o valor preso e a série acompanha
  localStorage.setItem('capitao.clima.v1', JSON.stringify({ em: Date.now(), dia: A.relogio.hojeIso, max: 19, min: 15 }));
  const ar = R.serie('temp_ar_externo_c', '30D'), ag = R.serie('temp_agua_c', '1A'), ag150 = R.serie('temp_agua_c', '150S');
  o.trava = { arUlt: ar[ar.length - 1].v, agUlt: ag[ag.length - 1].v, ag150: ag150[ag150.length - 1].v, inst: A.instante().q.temp_agua_c, instAr: A.instante().q.temp_ar_externo_c, arSemTrava: o.ar.d30.ult,
              prim: ar[0].v, degrau: Math.abs(ar[ar.length - 1].v - ar[ar.length - 2].v) };
  localStorage.removeItem('capitao.clima.v1');
  o.invalidos = [R.serie('nao_existe', '7D'), R.serie('sog_nos', 'XX'), R.serie('bateria_0_tensao_v', '7D', 'x'), R.serie(), R.serie('local', '150S')];
  // o ms: uma serie em outro instante termina nele
  const outro = R.agora() - 3600e3, s3 = R.serie('bateria_0_tensao_v', '1D', outro); o.outro = s3[s3.length - 1].ms === Math.floor(outro / 1000) * 1000;
  return o;
}"""


def historico(b):
    print('Histórico: serie() das cinco janelas, o serrote do diesel, a curva do ano e a trava do ar e da água')
    pg = abre(b)
    r = pg.evaluate(SERIE_JS)
    ok('serie(): %d combinações de campo × janela sem NaN, no tamanho de D.historico.janelas, em ordem de tempo, com v entre min e max; grupos só do laço só na janela \'150S\'' % r['cobertas'],
       r['ruins'] == [] and r['cobertas'] > 40, r['ruins'][:5])
    ok('o último ponto de cada série é o quadro de agora (v = o campo do quadro, ms = agora): 150S, 1D, 7D, 30D e 1A', r['ultimos'] == [], r['ultimos'][:5])
    ok('150 pontos na janela de 150 s, 96 / 168 / 120 / 365 nas outras', r['n'] == {'150S': 150, '1D': 96, '7D': 168, '30D': 120, '1A': 365}, r['n'])
    ar, ag = r['ar'], r['agua']
    ok('a curva do ano: o ar varia %.1f °C em 1 A (de %.1f a %.1f) e %.1f °C em 30 D; a água %.1f °C em 1 A: nenhuma série longa sai reta' % (ar['a1']['max'] - ar['a1']['min'], ar['a1']['min'], ar['a1']['max'], ar['d30']['max'] - ar['d30']['min'], ag['a1']['max'] - ag['a1']['min']),
       ar['a1']['max'] - ar['a1']['min'] >= 4 and ar['d30']['max'] - ar['d30']['min'] >= 1 and ag['a1']['max'] - ag['a1']['min'] >= 3 and ag['d30']['max'] - ag['d30']['min'] >= 0.3, r['ar'])
    ok('a praça de máquinas acompanha o ar (curva do ano) e nunca passa de 60 °C (%.0f a %.0f)' % (r['praca']['min'], r['praca']['max']), r['praca']['max'] <= 60 - 0.05 and r['praca']['max'] - r['praca']['min'] >= 4, r['praca'])
    d = r['diesel']
    ab = d['ab'][0]
    ok('o serrote do diesel em 7 dias: o cheio de %d L (%s %% das linhas de abastecimento) e o fundo de %d L (%s %%)' % (d['max'], ab[1], d['min'], ab[0]),
       abs(d['max'] - ab[1] / 100 * d['cap']) <= 1 and abs(d['min'] - ab[0] / 100 * d['cap']) <= 1.5, d)
    t = r['trava']
    ok('trava do ar e da água: com a máx/mín de hoje 15–19 °C o último ponto do ar (30 D) e o da água (1 A e 150 s) são o valor preso, iguais ao do instante(), e a série acompanha sem degrau',
       t['arUlt'] == 19 and t['agUlt'] == 19 and t['ag150'] == 19 and t['inst'] == 19 and t['instAr'] == 19 and t['degrau'] < 1.5, t)
    ok('serie() com campo ou janela que não existem, ms inválido, sem argumento ou de texto devolve null', all(x is None for x in r['invalidos']), r['invalidos'])
    ok('serie(c, j, ms) termina no segundo de ms', r['outro'] is True)
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


FAIXAS_JS = r"""() => { const R = window.CapitaoReplay, A = window.CapitaoAgora, D = window.CapitaoDados, base = A.ancora(Date.now()), o = { desde: [] };
  for (const [v, t] of [[0, 0], [0, 75], [120, 60], [300, 149], [575, 120]]) {
    const ms = base + (v * 150 + t) * 1000, f = R.porFaixa(ms), c = R.contadoresEm(ms);
    o.desde.push({ v, t, litros: f.reduce((a, x) => a + x.litros + x.gerador_litros, 0), usado: D.replay.contadores_base.diesel_litros - c.diesel_litros, horas: f.reduce((a, x) => a + x.horas, 0), h: (v * 150 + t) / 3600 });
  }
  o.f = R.porFaixa(base); o.motoresVolta = D.replay.por_volta.motores_l; o.faixas = D.consumo.faixas.length;
  const rs = R.resumo(base + 75000); o.resumo = rs; o.r105 = (() => { R.fixar('105'); return R.resumo(); })(); o.rNulo = R.resumo('x');
  return o; }"""


def faixas_e_resumo(b):
    print('porFaixa() e resumo()')
    pg = abre(b)
    r = pg.evaluate(FAIXAS_JS)
    f = r['f']
    ok('porFaixa(): uma entrada por faixa de D.consumo.faixas (%d), os segundos somam a volta (150 s) e o consumo por volta soma o dos motores (por_volta.motores_l)' % r['faixas'],
       len(f) == r['faixas'] == 5 and sum(x['seg'] for x in f) == 150 and abs(sum(x['litros_volta'] for x in f) - r['motoresVolta']) < 0.003, f)
    ok('porFaixa(): marcha lenta ~6 L/h, cruzeiro ~68 L/h (a média dos dois motores a cada segundo da tabela de 150 s)', 5.5 <= f[0]['lph'] <= 8 and 66 <= f[4]['lph'] <= 69, [(x['nome'], x['lph']) for x in f])
    ruim = [x for x in r['desde'] if abs(x['litros'] - x['usado']) > 1.0 or abs(x['horas'] - x['h']) > 0.01]
    ok('porFaixa() desde a âncora: litros dos motores + gerador = o diesel gasto dos contadores (±1 L) e as horas somam o tempo (5 instantes)', ruim == [], ruim)
    ok('resumo(): uma linha com hora, SOG, rpm, óleo, arrefecimento e diesel; ≤ 300 letras; em 12:01:45 leva o AVISO do arref_be', len(r['resumo']) <= 300 and re.search(r'\d\d:\d\d:\d\d', r['resumo'])
       and 'SOG' in r['resumo'] and 'rpm' in r['resumo'] and 'diesel' in r['resumo'] and 'AVISO: Temperatura do motor BE' in r['r105'] and 'limite 88 °C' in r['r105'] and len(r['r105']) <= 300, (r['resumo'], r['r105']))
    ok('resumo() sem coordenadas, posição relativa nem destino (graus-minutos, decimais com 4 casas, "mn da", "a caminho")', not re.search(r"\d°\s?\d|-?\d{1,3}[.,]\d{4,}|\bmn\b|caminho|chegando|ao largo|Barra Sul|Estaleirinho", r['resumo'] + r['r105']), r['resumo'])
    p = json.load(open(os.path.join(RAIZ, 'testes', 'proibidos.json'), encoding='utf-8'))
    achados = []
    for nome in ('ROTULOS', 'AUTENTICIDADE', 'DINHEIRO', 'PESSOAIS', 'LOCAL_SEGURANCA', 'VAZIOS', 'VISIVEL'):
        rx = re.compile(p[nome]['src'], re.I if 'i' in p[nome]['flags'] else 0)
        for txt in (r['resumo'], r['r105']):
            if rx.search(txt):
                achados.append((nome, txt))
    ok('resumo() não casa nenhuma das regex de termos proibidos (PROMPT §3: ROTULOS, AUTENTICIDADE, DINHEIRO, PESSOAIS, LOCAL_SEGURANCA, VAZIOS, VISIVEL)', achados == [], achados)
    ok('resumo(\'x\') devolve null', r['rNulo'] is None)
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


# ——— 10. nunca lança ———
LANCA_JS = r"""() => {
  const R = window.CapitaoReplay, nomes = ['ativo', 'agora', 't', 'em', 'quadro', 'contadores', 'contadoresEm', 'alarmes', 'janela', 'fase', 'resumo', 'serie', 'porFaixa', 'fixo'];
  const lixo = [undefined, null, NaN, Infinity, -Infinity, -1, 0, 1e300, -1e300, 'x', '', ' ', '60@', '@60', '--1', {}, [], true, function () {}, Symbol('s'), new Date(NaN), { valueOf() { throw new Error('boom'); } }];
  const lancou = []; let chamadas = 0;
  for (const n of nomes) for (const a of lixo) for (const b of [undefined, 'x', 1e300, {}]) {
    for (const args of [[a], [a, b], [a, b, a]]) { chamadas++; try { R[n].apply(R, args); } catch (e) { lancou.push(n + '(' + String(typeof a) + ') ' + e); } }
  }
  for (const a of lixo) { chamadas++; try { R.fixar(a); } catch (e) { lancou.push('fixar ' + e); } }
  R.fixar(null);
  return { lancou: lancou.slice(0, 5), chamadas, fixo: R.fixo(), q: !!R.quadro() };
}"""


def nunca_lanca(b):
    print('Nunca lança erro: argumentos absurdos, localStorage que lança, CapitaoAgora sem peças')
    pg = abre(b)
    r = pg.evaluate(LANCA_JS)
    ok('%d chamadas com argumentos absurdos (undefined, NaN, Infinity, 1e300, texto, objeto, Symbol, valueOf que lança…): nenhuma lançou erro e o replay segue andando' % r['chamadas'],
       r['lancou'] == [] and r['q'] and r['fixo'] is None, r)
    r = pg.evaluate(r"""() => { const R = window.CapitaoReplay, A = window.CapitaoAgora, orig = A.nivel, o = {};
      A.nivel = function () { throw new Error('quebrou'); }; try { o.al = R.alarmes(); o.em = R.em(Date.now()); o.tique = true; } catch (e) { o.lancou = String(e); }
      A.nivel = orig; return o; }""")
    ok('a CapitaoAgora.nivel que lança: alarmes() e em() devolvem null sem lançar (o instante() cai no snapshot)', 'lancou' not in r and r['al'] is None and r['em'] is None, r)
    r = pg.evaluate(r"""() => { const A = window.CapitaoAgora, R = window.CapitaoReplay, ancora = A.ancora; A.ancora = function () { return NaN; };
      const o = { em: R.em(Date.now()), q: R.quadro(), t: R.t(), c: R.contadoresEm(Date.now()) }; A.ancora = ancora; return o; }""")
    ok('a CapitaoAgora.ancora que devolve NaN: em/quadro/t/contadoresEm devolvem null', all(v is None for v in r.values()), r)
    fecha(pg)
    pg = abre(b, init="Storage.prototype.getItem = function () { throw new Error('sem armazenamento'); }; Storage.prototype.setItem = function () { throw new Error('sem armazenamento'); }; Storage.prototype.removeItem = function () { throw new Error('sem armazenamento'); };",
              caminho='/replay.html#replay=60')
    r = pg.evaluate("() => { const R = window.CapitaoReplay; let a, b; try { a = R.fixar('105'); b = R.fixar(null); } catch (e) { return { lancou: String(e) }; } return { a: typeof a, b, q: !!R.quadro(), hora: window.CapitaoAgora.fmt.hora(R.agora(), true) }; }")
    ok('localStorage que lança em todo getItem/setItem/removeItem: o replay carrega, fixa e solta sem lançar (#replay=60 vale na carga; a chave simplesmente não é guardada)',
       'lancou' not in r and r['a'] == 'number' and r['b'] is None and r['q'] and not pg.erros, (r, pg.erros))
    fecha(pg)


# ——— 10b. D.replay parcial: null, nunca NaN, Infinity nem texto vazio ———
# Cada buraco entra no capitao-dados.js antes do replay carregar (`depois=`): a tabela se recusa na carga (ativo() false), tudo devolve null e o instante() cai
# no D.snapshot (que o motor nunca devolve). Os de depois da carga mexem no D em uso (o objeto é o mesmo) e só a guarda de cada saída os pega.
PARCIAIS = [
    ('sem replay.chaves', 'delete window.CapitaoDados.replay.chaves;'),
    ('sem chaves.sog_nos (o SOG alimenta a distância, a rota e o vento aparente)', 'delete window.CapitaoDados.replay.chaves.sog_nos;'),
    ('sem chaves.consumo_lph (o diesel)', 'delete window.CapitaoDados.replay.chaves.consumo_lph;'),
    ('sem chaves.leme_graus', 'delete window.CapitaoDados.replay.chaves.leme_graus;'),
    ('sem chaves.vento_verdadeiro_nos (o vento aparente)', 'delete window.CapitaoDados.replay.chaves.vento_verdadeiro_nos;'),
    ('sem chaves.motor_bb_rpm (campo do catálogo sem chave: nenhum NaN, só um campo a menos)', 'delete window.CapitaoDados.replay.chaves.motor_bb_rpm;'),
    ('chaves.sog_nos com 20 quadros-chave em vez de 30 (finitos, mas a volta não fecha)', 'window.CapitaoDados.replay.chaves.sog_nos.length = 20;'),
    ('chaves.sog_nos com um valor que não é número', "window.CapitaoDados.replay.chaves.sog_nos[7] = 'x';"),
    ('sem contadores_base.diesel_litros', 'delete window.CapitaoDados.replay.contadores_base.diesel_litros;'),
    ('sem velocidade_media_nos', 'delete window.CapitaoDados.replay.velocidade_media_nos;'),
    ('velocidade_media_nos = 0 (a ETA seria infinita: texto não vazio, mas inválido)', 'window.CapitaoDados.replay.velocidade_media_nos = 0;'),
    ('sem rota.fator', 'delete window.CapitaoDados.rota.fator;'),
    ('sem rota.distancia_mn', 'delete window.CapitaoDados.rota.distancia_mn;'),
    ('sem rota.corrente', 'delete window.CapitaoDados.rota.corrente;'),
    ('perna que aponta para um ponto que não existe', "window.CapitaoDados.rota.pernas[0].para = 'nenhum';"),
    ("ponto da rota sem o campo `perto` (o local seria o texto «undefined, chegando»: texto não vazio, mas inválido)", 'delete window.CapitaoDados.rota.base.perto;'),
    ('sem embarcacao.tanques (os percentuais do diesel dariam Infinity)', 'delete window.CapitaoDados.embarcacao.tanques;'),
]
LE_PARCIAL = r"""() => { const R = window.CapitaoReplay, T = window.CapitaoTelemetria, ms = Date.now(), nul = (x) => x === null;
  return { ativo: R.ativo(), q: nul(R.quadro()), q60: nul(R.quadro(60)), em: nul(R.em(ms)), c: nul(R.contadores()), ce: nul(R.contadoresEm(ms)), al: nul(R.alarmes()), f: nul(R.fase()),
    t: nul(R.t()), r: nul(R.resumo()), s: nul(R.serie('sog_nos', '150S')) && nul(R.serie('bateria_0_tensao_v', '1D')), pf: nul(R.porFaixa()), fixar: nul(R.fixar('60')), fixo: nul(R.fixo()),
    atual: nul(T.atual()), fonte: nul(T.fonte()), inst: window.CapitaoAgora.instante().fonte, tele: window.__conta('capitao-telemetria') }; }"""
# depois da carga: o D em uso fica incompleto (a tabela já existe); só a guarda de cada saída pega. Cada caso diz o que tem de ser null e o que segue vivo.
POS_CARGA = [
    ('rota.fator apagado: o quadro, o resumo e a série (que leem o quadro) dão null; os contadores e o consumo por faixa não dependem da rota e seguem', 'delete D.rota.fator;',
     {'em': True, 'r': True, 's': True, 'cont': False, 'pf': False}),
    ('contadores_base.motor_bb_horimetro_h apagado: os contadores, o quadro e a série dão null (contadoresEm tem a guarda própria)', 'delete D.replay.contadores_base.motor_bb_horimetro_h;',
     {'em': True, 'cont': True, 's': True}),
    ("consumo.gerador_lph = texto: o consumo por faixa dá null e o quadro segue", "D.consumo.gerador_lph = 'x';", {'pf': True, 'em': False, 'cont': False, 's': False}),
    ('historico.n apagado: a série das janelas longas dá null (NaN no desvio) e o quadro segue', 'delete D.historico.n;', {'s': True, 'em': False, 'cont': False, 'pf': False}),
]
LE_POS = r"""(mut) => { const D = window.CapitaoDados, R = window.CapitaoReplay; R.quadro(); (new Function('D', mut))(D);
  const ms = Date.now(), nul = (x) => x === null; return { em: nul(R.em(ms)), q: nul(R.quadro()), r: nul(R.resumo()), cont: nul(R.contadores()), s: nul(R.serie('bateria_0_tensao_v', '1D')), pf: nul(R.porFaixa()), ativo: R.ativo() }; }"""


def d_parcial(b):
    print('D.replay parcial: tabela recusada (ativo() false), tudo null, o instante() cai no snapshot; e, depois da carga, a guarda de cada saída')
    for i, (nome, inj) in enumerate(PARCIAIS):
        pg = abre(b, depois=inj)
        if i == 0:
            pg.wait_for_timeout(1300)   # inerte: nem o tique de 1 s sai
        r = pg.evaluate(LE_PARCIAL)
        nulos = [k for k in ('q', 'q60', 'em', 'c', 'ce', 'al', 'f', 't', 'r', 's', 'pf', 'fixar', 'fixo', 'atual', 'fonte') if r[k] is not True]
        ok('D.replay parcial — %s: ativo() false; quadro/quadro(60)/em/contadores/alarmes/fase/t/resumo/serie/porFaixa/fixar/atual/fonte = null; o instante() cai no snapshot; nenhum tique' % nome,
           r['ativo'] is False and nulos == [] and r['inst'] == 'snapshot' and r['tele'] == 0 and not pg.erros, (r, pg.erros))
        fecha(pg)
    for nome, mut, esperado in POS_CARGA:
        pg = abre(b)
        r = pg.evaluate(LE_POS, mut)
        ok('depois da carga — %s' % nome, r['ativo'] is True and all(r[k] is v for k, v in esperado.items()) and not pg.erros, (r, pg.erros))
        fecha(pg)

# ——— 11. desempenho e código ———
def desempenho(b):
    print('Desempenho do em() e das séries')
    pg = abre(b)
    r = pg.evaluate("""() => { const R = window.CapitaoReplay, anc = window.CapitaoAgora.ancora(Date.now()); let t0 = performance.now();
      for (let i = 0; i < 10000; i++) R.em(anc + (i * 7919 % 86400) * 1000);
      const em = performance.now() - t0; t0 = performance.now();
      for (const j of ['150S', '1D', '7D', '30D', '1A']) R.serie('bateria_0_tensao_v', j);
      R.serie('diesel_litros', '1A'); R.serie('temp_ar_externo_c', '1A');
      return { em, series: performance.now() - t0 }; }""")
    ok('10.000 chamadas do em() em %.0f ms (%.1f µs cada): O(1), a tabela de 150 s só na carga' % (r['em'], r['em'] / 10), r['em'] < 3000, r['em'])
    ok('as cinco janelas, o diesel e o ar em 1 A em %.0f ms' % r['series'], r['series'] < 500, r['series'])
    fecha(pg)


def codigo():
    print('O arquivo: sem lookbehind, sem snapshot, sem window.CapitaoTelemetria =; nas 36 telas e no CORE do sw.js')
    src = le('capitao-replay.js')
    codigo_ = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
    codigo_ = re.sub(r'(?m)^\s*//.*$|\s//\s.*$', '', codigo_)
    ok('sem lookbehind (?<…) (Safari antigo) e sem \\w para palavra em português', '(?<' not in src and '\\w' not in src)
    ok('o código (fora dos comentários) não menciona snapshot: nunca o lê, devolve nem muta', not re.search(r'snapshot', codigo_, re.I), re.findall(r'.{20}snapshot.{20}', codigo_, re.I)[:2])
    ok('nunca se registra como CapitaoTelemetria', not re.search(r'window\s*\.\s*CapitaoTelemetria\s*=|window\[\s*[\'"]CapitaoTelemetria', codigo_))
    ok('não escreve fora das duas chaves do replay (capitao.replay.fixo e .sobre) e só o fixo é gravado', set(re.findall(r"'(capitao\.[a-z.]+)'", codigo_)) == {'capitao.replay.fixo', 'capitao.replay.sobre'}
       and len(re.findall(r'setItem', codigo_)) == 1, set(re.findall(r"'(capitao\.[a-z.]+)'", codigo_)))
    ok('sem VERSAO própria (acompanha o capitao-dados.js)', 'VERSAO' not in codigo_)
    ok('só emite evento: nada que troque de tela, abra janela, fale, grave o diário ou chame o SOS/C3 (location, window.open, speechSynthesis, capitao-voz, addDiario, markExec, sos)',
       not re.search(r'location\s*(\.\s*(href|assign|replace|reload)|=)|window\s*\.\s*open|speechSynthesis|capitao-voz|addDiario|markExec|S1-SOS|S2-SOS|C3-Leme|history\s*\.\s*(push|replace)State', codigo_),
       re.findall(r'.{15}(?:location|window\s*\.\s*open|speechSynthesis|addDiario|SOS|C3-Leme).{15}', codigo_)[:3])
    sw = le('sw.js')
    m = re.search(r'const TELAS = \[(.*?)\];', sw, re.S)
    telas = re.findall(r"'([^']+)'", m.group(1))
    ok('sw.js: ./capitao-replay.js no CORE, logo depois do capitao-dados.js', "'./capitao-dados.js', './capitao-replay.js'," in sw)
    erradas, sem_sos = [], []
    for t in telas:
        h = le(t + '.dc.html')
        if t.startswith(('S1-', 'S2-')):
            if 'capitao-replay' in h or 'capitao-telemetria' in h:
                sem_sos.append(t)
            continue
        i, j, k = h.find('<script src="./capitao-dados.js">'), h.find('<script src="./capitao-replay.js">'), h.find('<script src="./support.js">')
        if h.count('capitao-replay.js') != 1 or not (0 <= i < j < k):
            erradas.append(t)
    ok('as %d telas fora do SOS têm o <script src="./capitao-replay.js"> uma vez, logo depois do capitao-dados.js e antes do support.js' % (len(telas) - 2), erradas == [], erradas)
    ok('S1 e S2 não carregam o capitao-replay.js nem o capitao-telemetria.js', sem_sos == [], sem_sos)
    fora = [a for a in ('index.html', 'login.html', 'dados.html') if 'capitao-replay' in le(a)]
    ok('index.html, login.html e dados.html (fora das TELAS: não leem o quadro) não carregam o motor', fora == [], fora)


# ——— 11b. a moldura em nós Text e o setState só ao mudar (P2B; PROMPT Fase 2 «Desempenho», CONTRATO §6.6) ———
# O disparo de 1 s do motor só é barato se a moldura (cabeçalho, faixa e topo do app) trocar o TEXTO dos nós que já tem (noTexto.data = valor), e só quando
# o valor mudou. Refazer o innerHTML a cada tique recria o <capitao-theme-toggle> e o avatar (o foco do teclado se perde), dispara o fit() do capitao-app.js
# (o MutationObserver de childList) e enche a página de mutações. Main, H2 e E1 só dão setState quando o texto exibido muda.
# Instrumentação (init script, antes de qualquer script da página): PerformanceObserver 'longtask', contagem das execuções do fit() (o requestAnimationFrame
# da função de nome `fit`), dos tiques do motor e das chamadas do setState do React (o React.Component.prototype.setState, que o __setLogicState do support.js
# chama a cada setState de uma tela; o window.React é um acessor que troca o método no 1º get com o Component pronto).
MOLDURA_JS = """(function () {
  window.__lt = []; window.__fit = 0; window.__sets = 0; window.__ticks = 0;
  try { new PerformanceObserver(function (l) { l.getEntries().forEach(function (e) { window.__lt.push({ ini: e.startTime, dur: e.duration }); }); }).observe({ type: 'longtask', buffered: true }); } catch (e) {}
  var raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = function (cb) { return raf(cb && cb.name === 'fit' ? function (t) { window.__fit++; return cb(t); } : cb); };
  window.addEventListener('capitao-telemetria', function () { window.__ticks++; });
  var ouv = new Set(), add = window.addEventListener, rem = window.removeEventListener;   // os ouvintes do tique em uso (viva/morta da moldura não podem vazar)
  window.addEventListener = function (tp, f, o) { if (tp === 'capitao-telemetria') ouv.add(f); return add.call(this, tp, f, o); };
  window.removeEventListener = function (tp, f, o) { if (tp === 'capitao-telemetria') ouv.delete(f); return rem.call(this, tp, f, o); };
  window.__ouvintes = function () { return ouv.size; };
  var R, pronto = false;   // o UMD do React 18 faz `factory(global.React = {})`: o acessor recebe o objeto vazio, que só se enche depois; o setState se troca no 1º get com o Component pronto
  function troca() { if (pronto || !R || !R.Component) return; pronto = true; var P = R.Component.prototype, o = P.setState; P.setState = function () { window.__sets++; return o.apply(this, arguments); }; }
  Object.defineProperty(window, 'React', { configurable: true, get: function () { troca(); return R; }, set: function (v) { R = v; } });
})();"""
ESPERA_MOLDURA = "() => document.querySelector('capitao-theme-toggle button') && window.CapitaoReplay"
MOLDURA_SEL = 'capitao-cabecalho,capitao-faixa,capitao-topo-app'
# começa a medir: guarda os nós, põe o foco no botão do tema e liga o observador de mutações
MOLDURA_INICIA = """() => {
  const q = (s) => document.querySelector(s), mold = Array.from(document.querySelectorAll('%s'));
  const tog = q('capitao-theme-toggle'), btn = tog && tog.querySelector('button'), ava = q('capitao-cabecalho a[aria-label^="Perfil"], capitao-topo-app a[aria-label^="Perfil"]');
  const m = window.__m = { tog, btn, ava, mold, ini: performance.now(), child: 0, dados: 0, texto0: mold.map((e) => e.innerText).join('|') };
  if (btn) btn.focus();
  window.__fit = 0; window.__ticks = 0; window.__sets = 0;
  m.mo = new MutationObserver((rs) => rs.forEach((r) => { if (!mold.some((e) => e.contains(r.target))) return; if (r.type === 'childList') m.child++; else m.dados++; }));
  m.mo.observe(document.body, { childList: true, subtree: true, characterData: true });
  return { n: mold.length, tags: mold.map((e) => e.tagName.toLowerCase()), foco: document.activeElement === btn };
}""" % MOLDURA_SEL
MOLDURA_FIM = """() => {
  const m = window.__m, q = (s) => document.querySelector(s), lt = window.__lt.filter((e) => e.ini >= m.ini).map((e) => Math.round(e.dur));
  m.mo.disconnect();
  return { tog: !!m.tog && m.tog.isConnected && m.tog.isSameNode(q('capitao-theme-toggle')), ava: !!m.ava && m.ava.isConnected && m.ava.isSameNode(q('capitao-cabecalho a[aria-label^="Perfil"], capitao-topo-app a[aria-label^="Perfil"]')),
    foco: !!m.btn && document.activeElement === m.btn, fit: window.__fit, ticks: window.__ticks, lt, child: m.child, dados: m.dados,
    mudou: m.texto0 !== Array.from(document.querySelectorAll('%s')).map((e) => e.innerText).join('|'), erros: window.__erros || [] };
}""" % MOLDURA_SEL
# o texto da moldura no instante do tique (o ouvinte do teste roda depois do da moldura) contra o leitura() dela
MOLDURA_TEXTO = """() => new Promise((res) => { window.addEventListener('capitao-telemetria', function f() { window.removeEventListener('capitao-telemetria', f);
  const L = window.CapitaoMoldura.leitura(), txt = (s) => Array.from(document.querySelectorAll(s)).map((e) => e.innerText).join('\\n'), led = document.querySelector('capitao-topo-app [role=img]');
  res({ L, cab: txt('capitao-cabecalho'), faixa: txt('capitao-faixa'), rotulo: led ? led.getAttribute('aria-label') : null, titulo: led ? led.title : null }); }); })"""
# instante fixado: o quadro não muda, então 3 tiques não podem mexer em nada da moldura (nem um caractere, atributo ou nó)
MOLDURA_PARADA = """() => { const m = window.__m; m.parada = 0; m.mo2 = new MutationObserver((rs) => { m.parada += rs.length; });
  m.mold.forEach((e) => m.mo2.observe(e, { childList: true, subtree: true, characterData: true, attributes: true })); window.__ticks = 0; return true; }"""


def telas_moldura():
    """As 36 telas que importam a moldura (todas menos Main, H2, C3, Manual e S1/S2; 30 até a P4C, que trouxe A4 e A5, 34 com a P4E, que trouxe a C4 web e app, e 36 com a P4H, que trouxe a F6 web e app), com a largura do $preview: 1440 = web (1440×900), o resto = app (360×640)."""
    out = []
    for arq in sorted(f for f in os.listdir(RAIZ) if f.endswith('.dc.html')):
        h = le(arq)
        if not re.search(r'component-from-global-scope="capitao-(cabecalho|faixa|topo-app)"', h):
            continue
        w = int(re.search(r'\$preview.{0,12}?width.{0,6}?(\d+)', h).group(1))
        out.append((arq[:-len('.dc.html')], 1440 if w >= 1000 else 360, 900 if w >= 1000 else 640))
    return out


def moldura_lote(b, itens, segundos=10):
    """Abre todas as telas do lote ao mesmo tempo (um contexto cada), deixa 3,5 s assentar e mede `segundos` s de replay."""
    pgs = [(nome, abre(b, caminho='/%s.dc.html' % nome, sessao=True, init=MOLDURA_JS, viewport={'width': w, 'height': h}, espera=ESPERA_MOLDURA)) for nome, w, h in itens]
    pgs[0][1].wait_for_timeout(3500)
    ini = {nome: pg.evaluate(MOLDURA_INICIA) for nome, pg in pgs}
    pgs[0][1].wait_for_timeout(segundos * 1000)
    fim = {nome: pg.evaluate(MOLDURA_FIM) for nome, pg in pgs}
    txt = {nome: pg.evaluate(MOLDURA_TEXTO) for nome, pg in pgs}
    for nome, pg in pgs:   # parado: o instante fixado em 60 s; o 1º tique já atualiza, os 3 seguintes não podem mudar nada
        pg.evaluate("() => { window.CapitaoReplay.fixar(60); }")
    pgs[0][1].wait_for_timeout(1700)
    for nome, pg in pgs:
        pg.evaluate(MOLDURA_PARADA)
    pgs[0][1].wait_for_timeout(3300)
    parada = {nome: pg.evaluate("() => ({ n: window.__m.parada, ticks: window.__ticks })") for nome, pg in pgs}
    erros = {nome: list(pg.erros) for nome, pg in pgs}
    for nome, pg in pgs:
        fecha(pg)
    return {nome: dict(ini=ini[nome], fim=fim[nome], txt=txt[nome], parada=parada[nome], erros=erros[nome]) for nome, _, _ in itens}


def confere_moldura(nome, w, r, segundos=10):
    ini, fim, txt, parada = r['ini'], r['fim'], r['txt'], r['parada']
    rot = '%s (%d×%d)' % (nome, w, 900 if w >= 1000 else 640)
    ok('%s: a moldura tem %s e o motor tiquetou (%d tiques em %d s)' % (rot, '+'.join(ini['tags']), fim['ticks'], segundos), ini['n'] >= 1 and fim['ticks'] >= segundos - 2, (ini, fim['ticks']))
    ok('%s: o <capitao-theme-toggle> é o mesmo nó (isSameNode, ainda conectado) do início ao fim' % rot, fim['tog'], fim)
    ok('%s: o avatar é o mesmo nó do início ao fim' % rot, fim['ava'], fim)
    ok('%s: o foco do teclado fica no botão do tema (activeElement)' % rot, ini['foco'] and fim['foco'], (ini, fim))
    ok('%s: o fit() roda no máximo 2 vezes em %d s (rodou %d)' % (rot, segundos, fim['fit']), fim['fit'] <= 2, fim['fit'])
    ok('%s: nenhuma long task passa de 50 ms (%s)' % (rot, ('maior ' + str(max(fim['lt'])) + ' ms em ' + str(len(fim['lt']))) if fim['lt'] else '0 long tasks'), all(d <= 50 for d in fim['lt']), fim['lt'])
    ok('%s: nenhuma mutação childList dentro da moldura em %d s (só texto: %d trocas de caractere)' % (rot, segundos, fim['dados']), fim['child'] == 0, fim)
    ok('%s: a moldura acompanha o motor (o texto mudou em %d s ou é o rótulo do minuto)' % (rot, segundos), fim['mudou'] or w < 1000, fim)
    L = txt['L']
    if w >= 1000:
        faltam = [f for f in L['faixa'] if f[0] + ' ' + f[1] not in txt['faixa']]
        ok('%s: a faixa mostra o leitura() do tique, item a item (%d itens) e o cabeçalho a posição e o rótulo' % (rot, len(L['faixa'])),
           not faltam and L['pos'] in txt['cab'] and L['rotulo'] in txt['cab'], (faltam, L['pos'], L['rotulo'], txt['cab'][:200]))
    else:
        ok('%s: o rótulo do LED (aria-label e title) é o leitura() do tique: «%s»' % (rot, L['rotulo']), txt['rotulo'] == L['rotulo'] and txt['titulo'] == L['rotulo'], txt)
    ok('%s: com o instante fixado, 3 tiques não mexem em nada da moldura (0 mutações; tiques: %d)' % (rot, parada['ticks']), parada['n'] == 0 and parada['ticks'] >= 3, parada)
    ok('%s: sem erro de script' % rot, not r['erros'], r['erros'])


def moldura(b):
    todas = '--moldura' in sys.argv
    so = [x for x in os.environ.get('MOLDURA_TELAS', '').split(',') if x]   # (P4E) só estas telas, para medir uma tela nova sem rodar as 36 (a contagem das 36 fica de fora)
    itens = [t for t in telas_moldura() if t[0] in so] if so else telas_moldura() if todas else [t for t in telas_moldura() if t[0] in ('A2-Ponte-Mobile', 'A1-Ponte-Web', 'E1-Navegando-Gatilhos')]
    print('Moldura em nós Text, em 10 s de replay (%s)' % ('as %d telas com moldura' % len(itens) if todas else '3 telas: A2 em 360×640, A1 em 1440×900 e E1; todas as 30 com --moldura'))
    if todas and not so:
        ok('são 36 as telas que importam a moldura (A1–A5, B1–B3, C1, C2, C4, E1, E2, F1–F6, G1–G4 e H3, web e app)', len(itens) == 36, [t[0] for t in itens])
    larg = {n: w for n, w, _ in itens}
    for i in range(0, len(itens), 3):   # 3 telas por vez: abre ao mesmo tempo, mas sem passar dos núcleos da máquina (a long task mede a tela, não a fila)
        lote = itens[i:i + 3]
        for nome, r in moldura_lote(b, lote).items():
            confere_moldura(nome, larg[nome], r)


# O estado montado aos poucos (tiques, LED que vira de verde para amarelo e volta, D.demo que nunca põe selo, título e href do topo) tem de ser IGUAL ao de uma moldura montada do zero naquele estado:
# o innerHTML (sem o marcador data-cpm) e o style do elemento. O instante fica fixado em 60 s para o quadro não mudar entre as duas montagens.
MOLDURA_ESTADOS = """async () => {
  const D = window.CapitaoDados, M = window.CapitaoMoldura, sel = 'capitao-cabecalho,capitao-faixa,capitao-topo-app', limpa = (h) => h.replace(/ data-cpm="[^"]*"/g, '');
  const tog = document.querySelector('capitao-theme-toggle'), caixa = document.createElement('div'), out = [];
  caixa.style.cssText = 'position:fixed;left:-9999px;top:0;width:1440px'; document.body.appendChild(caixa);
  const confere = (rot) => { const r = { rot, vivo: M.leitura().vivo, tags: {} }; document.querySelectorAll(sel).forEach((real) => {
      const tag = real.tagName.toLowerCase(), f = document.createElement(tag); ['titulo', 'voltar'].forEach((a) => { if (real.hasAttribute(a)) f.setAttribute(a, real.getAttribute(a)); });
      caixa.appendChild(f);
      const a = limpa(real.innerHTML), b = limpa(f.innerHTML); let i = 0; while (i < a.length && a[i] === b[i]) i++;
      r.tags[tag] = a === b && real.getAttribute('style') === f.getAttribute('style') ? 'igual' : 'difere em ' + i + ': «' + a.slice(Math.max(0, i - 40), i + 80) + '» × «' + b.slice(Math.max(0, i - 40), i + 80) + '»';
      const led = real.querySelector('[role=img]'); r.demo = r.demo || /DEMO/.test(real.innerText); r.texto = (r.texto || '') + real.innerText + (led ? ' ' + led.getAttribute('aria-label') : ''); caixa.removeChild(f); });
    r.mesmoToggle = tog.isConnected && tog.isSameNode(document.querySelector('capitao-theme-toggle')); out.push(r); };
  const avisa = () => window.dispatchEvent(new CustomEvent('capitao-sessao'));
  await new Promise((r) => setTimeout(r, 1300)); confere('replay (ao vivo)');
  D.simulacao = false; avisa(); confere('sem replay (leitura fixa)');
  D.demo = true; D.aviso = 'aviso de teste'; avisa(); confere('leitura fixa com D.demo');
  D.simulacao = true; avisa(); confere('replay com D.demo');
  D.demo = false; delete D.aviso; avisa(); confere('replay sem D.demo');
  const snap = D.snapshot; D.snapshot = null; D.simulacao = false; avisa(); confere('sem dado nenhum (sem replay e sem snapshot)');
  D.snapshot = snap; D.simulacao = true; avisa(); confere('de volta ao replay');
  const topo = document.querySelector('capitao-topo-app');
  if (topo) { topo.setAttribute('titulo', 'Outro título'); topo.setAttribute('voltar', 'A1-Ponte-Web.dc.html'); confere('título e href do topo trocados'); out[out.length - 1].topo = { texto: topo.innerText, href: topo.querySelector('a[aria-label=Voltar]').getAttribute('href') }; }
  // ouvintes: ligar e desligar várias instâncias (e religar a mesma) não pode vazar nem duplicar
  const n0 = window.__ouvintes(), ouv = { n0 }, f1 = document.createElement('capitao-faixa'), f2 = document.createElement('capitao-faixa'), c1 = document.createElement('capitao-cabecalho');
  caixa.appendChild(f1); caixa.appendChild(f2); caixa.appendChild(c1); ouv.tres = window.__ouvintes();
  caixa.removeChild(f2); ouv.duas = window.__ouvintes(); caixa.removeChild(f1); caixa.removeChild(c1); ouv.zero = window.__ouvintes();
  caixa.appendChild(f1); ouv.religada = window.__ouvintes(); const L = M.leitura(); ouv.textoReligada = f1.innerText.indexOf(L.faixa[0][0] + ' ' + L.faixa[0][1]) >= 0;
  caixa.removeChild(f1); ouv.fim = window.__ouvintes(); out.push({ ouv });
  document.body.removeChild(caixa); return out;
}"""


def moldura_estados(b):
    print('Moldura: o estado montado aos poucos é igual ao montado do zero (replay, última leitura, D.demo sem selo, título do topo)')
    for nome, w, h in (('A1-Ponte-Web', 1440, 900), ('A2-Ponte-Mobile', 360, 640)):
        pg = abre(b, caminho='/%s.dc.html' % nome, sessao=True, init=MOLDURA_JS + "\ntry { localStorage.setItem('capitao.replay.fixo', '60'); } catch (e) {}", viewport={'width': w, 'height': h}, espera=ESPERA_MOLDURA)
        pg.wait_for_timeout(2500)
        for e in pg.evaluate(MOLDURA_ESTADOS):
            if 'ouv' in e:
                o = e['ouv']
                ok('%s: ouvintes do tique: 3 instâncias ligadas somam 3, desligadas voltam a %d, religar uma soma 1 (e ela mostra a faixa), no fim %d (sem vazar nem duplicar)' % (nome, o['n0'], o['fim']),
                   o['tres'] == o['n0'] + 3 and o['duas'] == o['n0'] + 2 and o['zero'] == o['n0'] and o['religada'] == o['n0'] + 1 and o['fim'] == o['n0'] and (o['textoReligada'] or w < 1000), o)
                continue
            rot = '%s · %s' % (nome, e['rot'])
            ok('%s: %s' % (rot, ' · '.join('%s %s' % (t, 'igual' if v == 'igual' else 'DIFERE') for t, v in e['tags'].items())), all(v == 'igual' for v in e['tags'].values()), e['tags'])
            ok('%s: o <capitao-theme-toggle> continua o mesmo nó' % rot, e['mesmoToggle'], e)
            if e['rot'] == 'replay (ao vivo)':
                ok('%s: LED ao vivo, sem selo DEMO' % rot, e['vivo'] is True and not e['demo'], e)
            if e['rot'] == 'sem replay (leitura fixa)':
                ok('%s: LED de leitura fixa (vivo false), sem selo' % rot, e['vivo'] is False and not e['demo'], e)
            if e['rot'] in ('leitura fixa com D.demo', 'replay com D.demo'):   # Fase 4 (P4B): a moldura não tem mais o selo DEMO (PROMPT §1, decisão b): D.demo e D.aviso não escrevem nada
                ok('%s: D.demo e D.aviso não põem selo nenhum (o texto da moldura não diz DEMO)' % rot, e['demo'] is False, e)
            if e['rot'] == 'replay sem D.demo':
                ok('%s: sem selo DEMO' % rot, e['demo'] is False, e)
            if e['rot'].startswith('sem dado nenhum'):
                ok('%s: sem dado, o texto mostra «—» ou SEM DADOS e nunca NaN, undefined nem [object' % rot, ('—' in e['texto'] or 'SEM DADOS' in e['texto']) and not re.search(r'NaN|undefined|\[object', e['texto']), e['texto'])
            if e['rot'].startswith('título'):
                ok('%s: o título e o voltar do topo acompanham os atributos' % rot, e['topo']['texto'].split('\n')[0].strip() == 'Outro título' and e['topo']['href'] == 'A1-Ponte-Web.dc.html', e['topo'])
        ok('%s: sem erro de script' % nome, not pg.erros, pg.erros)
        fecha(pg)


# ——— a moldura lê o QUADRO do instante (P4B; PROMPT Fase 4 «capitao-moldura.js», CONTRATO §1.22–§1.23) ———
# Diesel, estado, local, posição e hora (com segundos) da moldura são os do quadro do instante fixado, não os do D.snapshot de 26/09, e o texto dela não carrega
# nenhum rótulo do §3 (nem «Snapshot», «DEMO», «SEM DADOS»). O esperado é refeito aqui em Python (o port `confere.em`), com as casas do D.campos, não lido da tela.
MOLDURA_QUADRO_JS = """() => { const A = window.CapitaoAgora, R = window.CapitaoReplay, T = (s) => Array.from(document.querySelectorAll(s)).map((e) => e.innerText).join('\\n');
  const led = document.querySelector('capitao-topo-app [role=img]'), pil = document.querySelector('[data-cpm=pilula]'), ms = R.agora();
  return { ms, anc: A.ancora(ms), cab: T('capitao-cabecalho'), faixa: T('capitao-faixa'), led: led ? led.getAttribute('aria-label') + '|' + led.title : '', pil: pil ? pil.title : '',
    faixa_dica: (document.querySelector('capitao-faixa [data-cpm=estado]') || { title: '' }).title }; }"""


def br_num(x, casas, mil=False):
    """O número como a tela mostra (floor(x·10^c + 0,5)), em pt-BR, com o ponto de milhar se `mil`."""
    v = C.arred(x, casas)
    s = ('%.*f' % (casas, abs(v))).replace('.', ',')
    if mil:
        i, _, dec = s.partition(',')
        s = '{:,}'.format(int(i)).replace(',', '.') + (',' + dec if dec else '')
    return ('-' if v < 0 else '') + s


def graus_min(v, pos, neg, g):
    """O `grausMin` do CapitaoAgora (59,995′ já é o grau seguinte): 26°59,46'S / 048°36,71'W."""
    a = abs(v)
    gr = math.floor(a)
    mi = math.floor((a - gr) * 6000 + 0.5) / 100
    if mi >= 60:
        gr, mi = gr + 1, 0
    return str(gr).zfill(g) + '°' + ('0' if mi < 10 else '') + ('%.2f' % mi).replace('.', ',') + "'" + (neg if v < 0 else pos)


def moldura_esperada(q, hora):
    """O texto que a moldura tem de mostrar para o quadro `q` do replay (diesel em litros e %, estado e local, posição e hora)."""
    cap = D['embarcacao']['tanques']['diesel_l']
    return {'faixa': ['SOG %s NÓS' % br_num(q['sog_nos'], 1), 'PROA %03d°' % (math.floor(((q['proa_graus'] % 360) + 360) % 360 + 0.5) % 360), 'VENTO %s NÓS' % br_num(q['vento_verdadeiro_nos'], 1),
                      '24 V %s V' % br_num(q['bateria_0_tensao_v'], 2), 'ÁGUA DOCE %s %%' % br_num(q['tanque_agua_pct'], 1),
                      'DIESEL %s L (%s %%)' % (br_num(q['diesel_litros'], 0, True), br_num(C.arred(q['diesel_litros'] / cap * 100, 1), 1))],
            'estado': ('%s · %s' % (q['estado'], re.sub(r'^enseada de ', '', q['local'], flags=re.I))).upper(), 'hora': hora + ' · AO VIVO',   # (dois nós: só o estado e o local encolhem; a hora nunca é cortada)
            'cab_estado': '%s · %s' % (q['estado'], q['local']), 'pos': graus_min(q['lat'], 'N', 'S', 2) + ' ' + graus_min(q['lon'], 'E', 'W', 3),
            'emb': 'Embarcação %s · registro %s' % (D['embarcacao']['nome'], D['embarcacao']['registro']), 'rotulo': 'Ao vivo · ' + hora}


TELAS_MOLDURA_QUADRO = (('A1-Ponte-Web', 1440, 900), ('C1-Leme-Web', 1440, 900), ('A2-Ponte-Mobile', 390, 844), ('G3-Diario-Mobile', 390, 844))


def moldura_quadro(b, fixos=('60', '105')):
    print('Moldura: diesel, estado, local, posição e hora vêm do quadro do instante (60 s e 105 s), sem rótulo do §3')
    termos = C.carrega_termos()
    for nome, w, h in TELAS_MOLDURA_QUADRO:
        for fixo in fixos:
            pg = abre(b, caminho='/%s.dc.html' % nome, sessao=True, init="try { localStorage.setItem('capitao.replay.fixo', '%s'); } catch (e) {}" % fixo, viewport={'width': w, 'height': h}, espera=ESPERA_MOLDURA)
            pg.wait_for_timeout(1500)
            r = pg.evaluate(MOLDURA_QUADRO_JS)
            erros = list(pg.erros)
            fecha(pg)
            q = C.em(P, (r['ms'] - r['anc']) // 1000, ancora_s=r['anc'] // 1000)   # o segundo do dia de bordo (desde a âncora de 07:00)
            hora = datetime.fromtimestamp(r['ms'] / 1000, BR).strftime('%H:%M:%S')
            e = moldura_esperada(q, hora)
            rot = '%s (%d×%d, instante %s s = %s)' % (nome, w, h, fixo, hora)
            if w >= 1000:
                faltam = [x for x in e['faixa'] if x not in r['faixa']]
                ok('%s: a faixa mostra os valores do quadro (SOG, PROA, VENTO, 24 V, ÁGUA DOCE e DIESEL em litros e %%): %s' % (rot, ' · '.join(e['faixa'])), not faltam, (faltam, r['faixa']))
                ok('%s: o estado e o local da faixa são os do quadro («%s») e a hora do instante com «AO VIVO» vem inteira, em nó próprio: «%s»' % (rot, e['estado'], e['hora']),
                   e['estado'] in r['faixa'] and e['hora'] in r['faixa'].split('\n') and e['estado'] == r['faixa_dica'], (e['estado'], e['hora'], r['faixa'][-160:], r['faixa_dica']))
                ok('%s: o cabeçalho mostra a embarcação e o registro, o estado e o local do quadro, a posição e «%s»' % (rot, e['rotulo']),
                   all(x in r['cab'] for x in (e['emb'], e['cab_estado'], e['pos'], e['rotulo'])), (e, r['cab']))
                ok('%s: a dica da pílula não fala de snapshot, coletor desligado nem leitura fixa' % rot, r['pil'] == 'Telemetria ao vivo — atualiza a cada segundo', r['pil'])
            else:
                ok('%s: o rótulo do LED (aria-label e title) é «%s», com os segundos do instante' % (rot, e['rotulo']), r['led'] == e['rotulo'] + '|' + e['rotulo'], r['led'])
            achados = [(k, m.group(0)) for k, rx in termos.items() if k in ('ROTULOS', 'AUTENTICIDADE', 'VAZIOS', 'VISIVEL') for m in rx.finditer('\n'.join([r['cab'], r['faixa'], r['led'], r['pil']]))]
            ok('%s: nenhum termo do §3 (ROTULOS, AUTENTICIDADE, VAZIOS, VISIVEL) na moldura' % rot, not achados, achados)
            ok('%s: sem erro de script' % rot, not erros, erros)


# ——— a faixa global de alerta (P4B; capitao-app.js; PROMPT Fase 4 «Faixa global de alerta»; PARIDADE F05) ———
# Nas telas de verdade (A1 na web e A2 no app): some em 60 s e aparece em 105 s empurrando a prancheta (sem cobri-la) e volta ao normal; viva (relógio deslocado para a janela do alarme) o
# texto troca sem mutação childList e sem fit() por segundo; o crítico (só plantado, no cenário alarme-critico injetado) vem primeiro, vermelho, assertivo, com «+N»; o alarme pedido
# no chat (capitao.alarmes.v1) entra na lista, sempre AVISO, e leva à lista da Ponte; a CONVERSA aberta cala as regiões do leitor de tela mas a faixa fica; nunca fala, nunca grava, não tem timer.
ESPIA_FALA_JS = "(() => { window.__falas = 0; try { const o = speechSynthesis.speak.bind(speechSynthesis); speechSynthesis.speak = function () { window.__falas++; return o.apply(this, arguments); }; } catch (e) {} })();"
FAIXA_LE = """() => { const f = document.getElementById('capitao-faixa-alertas'), st = document.getElementById('capitao-faixa-status'), an = document.getElementById('capitao-faixa-anuncio'), lk = f && f.querySelector('a');
  const art = [...document.querySelectorAll('#dc-root [style*="width: 1440px"],#dc-root [style*="width: 390px"],#dc-root [style*="width: 2380px"]')].find((c) => /px$/.test(c.style.width) && parseFloat(c.style.height) >= 600);
  const r = f ? f.getBoundingClientRect() : null, p = art ? art.getBoundingClientRect() : null;
  return { existe: !!f, oculta: f ? f.hidden : null, nivel: f ? f.getAttribute('data-nivel') : null, texto: f ? f.innerText : '', href: lk ? lk.getAttribute('href') : null, aria: lk ? lk.getAttribute('aria-label') : null,
    fim: r ? r.bottom : 0, topoArt: p ? p.top : null, fundo: f ? getComputedStyle(f).backgroundColor : '', status: st ? st.textContent : null, anuncio: an ? an.textContent : null,
    falas: window.__falas || 0, fit: window.__fit, ticks: window.__ticks, registro: Object.keys(localStorage).filter((k) => /^capitao\\.(diario|executado|tickets|tarefas)\\.v1$/.test(k)) }; }"""
VP_WEB, VP_APP = {'width': 1440, 'height': 900}, {'width': 390, 'height': 844}
ARREF_BE = {'id': 'arref_be', 'nivel': 'aviso', 'sistema': 'motores', 'lado': 'be', 'campo': 'motor_be_arref_c', 'valor': 91.2, 'limite': 88}
ARREF_BB = {'id': 'arref_bb', 'nivel': 'aviso', 'sistema': 'motores', 'lado': 'bb', 'campo': 'motor_bb_arref_c', 'valor': 90.4, 'limite': 88}


def abre_faixa(b, nome, vp, fixo=None, sobre=None, critico=False, pedidos=None, deslocamento=None, extra=''):
    init = MOLDURA_JS + ESPIA_FALA_JS + extra
    if fixo: init += "try { localStorage.setItem('capitao.replay.fixo', '%s'); } catch (e) {}" % fixo
    if sobre is not None: init += "localStorage.setItem('capitao.replay.sobre', %s);" % json.dumps(json.dumps(sobre))
    if pedidos is not None: init += "localStorage.setItem('capitao.alarmes.v1', %s);" % json.dumps(json.dumps(pedidos))
    if deslocamento is not None: init += "(() => { const o = Date.now.bind(Date); Date.now = () => o() + %d; })();" % deslocamento
    pg = abre(b, caminho='/%s.dc.html' % nome, sessao=True, init=init, depois="window.CapitaoDados.replay.cenario = 'alarme-critico';" if critico else '', viewport=vp, espera=ESPERA_MOLDURA)
    pg.wait_for_timeout(1800)
    return pg


def desloca_para(fase_ms):
    """O deslocamento do relógio (ms) que põe a página na fase `fase_ms` (ms desde a âncora de 07:00, mod 150 s) quando ela carrega."""
    agora = datetime.now(BR)
    anc = agora.replace(hour=7, minute=0, second=0, microsecond=0)
    if agora < anc: anc -= timedelta(days=1)
    return (fase_ms - int((agora - anc).total_seconds() * 1000)) % (VOLTA * 1000)


def vermelho(rgb):
    c = [int(x) for x in re.findall(r'\d+', rgb or '')[:3]]
    return len(c) == 3 and c[0] > 150 and c[0] > c[1] + 80 and c[0] > c[2] + 80


def faixa_global(b):
    print('Faixa global de alerta (capitao-app.js): aparece e some com o alarme, empurra a prancheta, crítico plantado, alarme pedido, CONVERSA aberta, nunca fala nem grava')
    for nome, vp in (('A1-Ponte-Web', VP_WEB), ('A2-Ponte-Mobile', VP_APP)):
        rot = '%s (%d×%d)' % (nome, vp['width'], vp['height'])
        ponte = 'A2-Ponte-Mobile.dc.html#alertas' if vp['width'] < 1000 else 'A1-Ponte-Web.dc.html#alertas'
        # 1. 60 s → 105 s → 60 s no mesmo documento
        pg = abre_faixa(b, nome, vp, fixo='60')
        a = pg.evaluate(FAIXA_LE)
        ok('%s: em 60 s (cruzeiro, sem alarme) não há faixa visível' % rot, not a['existe'] or a['oculta'], a)
        top0 = a['topoArt']
        pg.evaluate("() => { window.__fit = 0; window.CapitaoReplay.fixar(105); }")
        pg.wait_for_timeout(1600)
        c = pg.evaluate(FAIXA_LE)
        al = pg.evaluate("() => { const x = window.CapitaoAlertas.ativos()[0]; return { id: x.id, texto: x.texto, hora: x.hora, detalhe: x.detalhe, nivel: x.nivel }; }")
        ok('%s: ao entrar na janela do alarme (105 s) a faixa aparece com o AVISO «%s», «desde %s» e «ABRIR ›»' % (rot, al['texto'], al['hora']),
           c['existe'] and not c['oculta'] and c['nivel'] == 'aviso' and al['texto'] in c['texto'] and ('desde ' + al['hora']) in c['texto'] and 'ABRIR' in c['texto'] and 'AVISO' in c['texto'], (c, al))
        ok('%s: ABRIR leva a %s (o aria-label do link repete o alerta)' % (rot, al['detalhe']), c['href'] == al['detalhe'] == 'C3-Leme-Alerta.dc.html#alarme=arref_be' and al['texto'] in (c['aria'] or ''), (c['href'], c['aria']))
        ok('%s: a faixa empurra a prancheta (começa em %s, a faixa termina em %s) e o fit() rodou no máximo 2 vezes (rodou %s)' % (rot, c['topoArt'], round(c['fim'], 1), c['fit']),
           c['topoArt'] is not None and c['topoArt'] >= c['fim'] - 0.5 and c['fim'] >= 44 and c['fit'] <= 2, c)
        ok('%s: não é crítico (sem o cenário alarme-critico): fundo da faixa não é vermelho e a região assertiva fica vazia' % rot, not vermelho(c['fundo']) and not c['anuncio'], c)
        ok('%s: nunca fala (speechSynthesis.speak 0 vez) e não grava no registro (sem diário, Executado, tickets nem tarefas)' % rot, c['falas'] == 0 and c['registro'] == [], c)
        ok('%s: o leitor de tela é avisado uma vez pela região educada (role=status), com o AVISO' % rot, bool(c['status']) and al['texto'] in c['status'] and 'Aviso' in c['status'], c['status'])
        # instante fixado: o quadro não muda, então 3 tiques não podem mexer em nada da faixa (nem um caractere, atributo ou nó: só se escreve quando o valor mudou)
        pg.evaluate("""() => { const f = document.getElementById('capitao-faixa-alertas'); window.__par = 0; window.__mof = new MutationObserver((rs) => { window.__par += rs.length; });
          window.__mof.observe(f, { childList: true, subtree: true, characterData: true, attributes: true }); window.__ticks = 0; }""")
        pg.wait_for_timeout(3300)
        par = pg.evaluate("() => { window.__mof.disconnect(); return { n: window.__par, ticks: window.__ticks }; }")
        ok('%s: com o instante fixado em 105 s, 3 tiques não mexem em nada da faixa (0 mutações; tiques: %d)' % (rot, par['ticks']), par['n'] == 0 and par['ticks'] >= 3, par)
        pg.evaluate("() => { window.__fit = 0; window.CapitaoReplay.fixar(60); }")
        pg.wait_for_timeout(1600)
        d_ = pg.evaluate(FAIXA_LE)
        ok('%s: ao sair da janela a faixa some e a prancheta volta ao lugar de antes (%s → %s)' % (rot, c['topoArt'], d_['topoArt']), d_['oculta'] and abs(d_['topoArt'] - top0) <= 1 and d_['fit'] <= 2, (d_, top0))
        ok('%s: sem erro de script' % rot, not pg.erros, pg.erros)
        fecha(pg)
        # 2. viva: o relógio deslocado para 100,4 s da volta (o alarme dura até 116 s): o texto troca por segundo, sem childList na faixa e sem fit() a cada tique
        pg = abre_faixa(b, nome, vp, deslocamento=desloca_para(100400))
        pg.evaluate("""() => { const f = document.getElementById('capitao-faixa-alertas'); window.__fx = { ini: f ? f.innerText : null, child: 0, dados: 0, textos: new Set() };
          if (f) { const m = window.__fx; new MutationObserver((rs) => rs.forEach((r) => { if (r.type === 'childList') m.child++; else if (r.type === 'characterData') m.dados++; })).observe(f, { childList: true, subtree: true, characterData: true }); }
          window.__fit = 0; window.__ticks = 0; window.addEventListener('capitao-telemetria', () => { const e = document.getElementById('capitao-faixa-alertas'); if (e && !e.hidden) window.__fx.textos.add(e.innerText); }); }""")
        pg.wait_for_timeout(7000)
        v = pg.evaluate("() => ({ fx: { ini: window.__fx.ini, child: window.__fx.child, dados: window.__fx.dados, n: window.__fx.textos.size }, fit: window.__fit, ticks: window.__ticks, f: document.getElementById('capitao-faixa-alertas') && !document.getElementById('capitao-faixa-alertas').hidden })")
        ok('%s: ao vivo (%d tiques em 7 s), a faixa já estava aberta e o texto trocou %d vezes: sem mutação childList na faixa (só caracteres: %d) e o fit() rodou no máximo 2 vezes (%d)' % (rot, v['ticks'], v['fx']['n'], v['fx']['dados'], v['fit']),
           v['f'] and v['fx']['ini'] and v['ticks'] >= 5 and v['fx']['n'] >= 2 and v['fx']['child'] == 0 and v['fx']['dados'] >= 1 and v['fit'] <= 2, v)
        ok('%s: sem erro de script (ao vivo)' % rot, not pg.erros, pg.erros)
        fecha(pg)
        # 3. crítico (plantado no cenário alarme-critico injetado) e aviso mais novo: crítico primeiro, vermelho, «+1», região assertiva
        crit = dict(ARREF_BE, nivel='critico', valor=96.4, limite=92, desde='2026-11-09T14:59:00Z')
        pg = abre_faixa(b, nome, vp, fixo='60', critico=True, sobre={'alarmes': [dict(ARREF_BB, desde='2026-11-09T14:58:00Z'), crit]})
        c = pg.evaluate(FAIXA_LE)
        ok('%s: com um AVISO mais antigo e um CRÍTICO plantados, o crítico vem primeiro: «CRÍTICO», fundo vermelho, «+1», o outro some da frase' % rot,
           c['existe'] and not c['oculta'] and c['nivel'] == 'critico' and 'CRÍTICO' in c['texto'] and 'Temperatura do motor BE: 96,4 °C' in c['texto'] and '+1' in c['texto'] and 'BB' not in c['texto'] and vermelho(c['fundo']), c)
        ok('%s: o crítico novo sai uma vez na região assertiva (role=alert), com «e mais 1 alerta», e a região educada fica calada' % rot,
           (c['anuncio'] or '').startswith('Alerta crítico: Temperatura do motor BE') and 'E mais 1 alerta' in c['anuncio'] and not c['status'] and c['falas'] == 0, c)
        ok('%s: sem erro de script (crítico)' % rot, not pg.erros, pg.erros)
        fecha(pg)
        # 4. ordem entre avisos: o mais antigo primeiro
        pg = abre_faixa(b, nome, vp, fixo='60', sobre={'alarmes': [dict(ARREF_BE, desde='2026-11-09T14:59:30Z'), dict(ARREF_BB, desde='2026-11-09T14:58:00Z')]})
        c = pg.evaluate(FAIXA_LE)
        ok('%s: dois AVISOS: o mais antigo (BB) vem primeiro e a faixa diz «+1»' % rot, c['existe'] and 'Temperatura do motor BB' in c['texto'] and '+1' in c['texto'] and c['nivel'] == 'aviso', c)
        fecha(pg)
        # 5. alarme pedido no chat (a Fase 3: capitao.alarmes.v1): AVISO, desdeTxt do cérebro, leva à lista da Ponte; sem começo conhecido vai para o fim
        ped = [{'id': 'usr_1', 'campo': 'motor_bb_arref_c', 'op': '>', 'limite': 80, 'iso': '2026-11-09T10:00:00-03:00', 'who': 'Lucas', 'sim': True}]
        pg = abre_faixa(b, nome, vp, fixo='60', pedidos=ped)
        c = pg.evaluate(FAIXA_LE)
        pa = pg.evaluate("() => window.CapitaoBrain.alarmesPedidosAtivos().map((x) => ({ id: x.id, texto: x.texto, desdeTxt: x.desdeTxt, nivel: x.nivel, detalhe: x.detalhe }))")
        ok('%s: o alarme pedido no chat (#1, arrefecimento BB acima de 80 °C) está ativo em 60 s e a faixa o mostra como AVISO, com o desdeTxt do cérebro e «ABRIR» → %s' % (rot, ponte),
           len(pa) == 1 and pa[0]['detalhe'] == '' and c['existe'] and not c['oculta'] and c['nivel'] == 'aviso' and pa[0]['texto'] in c['texto'] and pa[0]['desdeTxt'] in c['texto'] and c['href'] == ponte, (c, pa))
        pg.evaluate("() => { window.CapitaoReplay.fixar(105); }")
        pg.wait_for_timeout(1600)
        c = pg.evaluate(FAIXA_LE)
        pa = pg.evaluate("() => window.CapitaoBrain.alarmesPedidosAtivos().map((x) => ({ texto: x.texto, desdeTxt: x.desdeTxt, desdeMs: x.desdeMs }))")
        primeiro = pa[0]['texto'] if pa and pa[0]['desdeMs'] is not None and pa[0]['desdeMs'] < pg.evaluate("() => window.CapitaoAlertas.ativos()[0].desdeMs") else None
        ok('%s: em 105 s, com o alarme do replay e o pedido juntos, a faixa diz «+1» e começa pelo mais antigo (o pedido, que começou antes: %s)' % (rot, pa[0]['desdeTxt'] if pa else '?'),
           primeiro is not None and primeiro in c['texto'] and '+1' in c['texto'] and c['href'] == ponte, (c, pa))
        fecha(pg)
        ped2 = [{'id': 'usr_2', 'campo': 'pressao_barometrica_hpa', 'op': '<', 'limite': 1040, 'iso': '2026-11-09T10:00:00-03:00', 'who': 'Lucas', 'sim': True}]
        pg = abre_faixa(b, nome, vp, fixo='105', pedidos=ped2)
        c = pg.evaluate(FAIXA_LE)
        pa = pg.evaluate("() => window.CapitaoBrain.alarmesPedidosAtivos().map((x) => ({ texto: x.texto, desdeTxt: x.desdeTxt, desdeMs: x.desdeMs }))")
        ok('%s: o alarme pedido que vale há mais de 160 s não tem começo conhecido («%s»): vai para o fim, atrás do alarme do replay (que dá a faixa e a ABRIR → C3)' % (rot, pa[0]['desdeTxt'] if pa else '?'),
           pa and pa[0]['desdeMs'] is None and 'há mais de' in pa[0]['desdeTxt'] and 'Temperatura do motor BE' in c['texto'] and '+1' in c['texto'] and c['href'].startswith('C3-Leme-Alerta'), (c, pa))
        fecha(pg)
        # 6. CONVERSA aberta: a faixa fica (visível), a região do leitor de tela cala; fechada a conversa, ela diz
        pg = abre_faixa(b, nome, vp, fixo='60')
        pg.evaluate("() => { const x = document.createElement('div'); x.className = 'cpz on'; x.id = 'cpz-teste'; document.body.appendChild(x); window.CapitaoReplay.fixar(105); }")
        pg.wait_for_timeout(1600)
        c = pg.evaluate(FAIXA_LE)
        ok('%s: com a CONVERSA aberta (.cpz.on) a faixa aparece e as duas regiões do leitor de tela ficam caladas' % rot, c['existe'] and not c['oculta'] and not c['status'] and not c['anuncio'], c)
        pg.evaluate("() => { document.getElementById('cpz-teste').remove(); window.dispatchEvent(new CustomEvent('capitao-sessao')); }")
        pg.wait_for_timeout(500)
        c2 = pg.evaluate(FAIXA_LE)
        ok('%s: fechada a conversa, a região educada diz o aviso que ficou calado' % rot, bool(c2['status']) and 'Aviso' in c2['status'], c2)
        fecha(pg)


# ——— a faixa e a janela de conversa em emergência (P4B, revisão; CLAUDE.md 10; capitao-brain.js › almNavJan) ———
# O alarme pedido de velocidade (SOG) é medida de navegação: dentro dos 15 min da conversa em emergência o limite e a leitura dela não aparecem — nem no texto da faixa, nem no aria-label do link, nem
# nas regiões do leitor de tela. A marca da janela é UMA só, `window.CapitaoEmergencia` (capitao-app.js, sessionStorage `capitao.emergenciaAte`): as telas de conversa a gravam, a faixa global a lê e
# passa `{ emergencia: true }` a B.alarmesPedidosAtivos (ela não tem a tela de conversa por perto). Sem a marca o texto traz a velocidade com número (o controle que prova que o teste enxerga o vazamento).
PED_SOG = [{'id': 'usr_1', 'campo': 'sog_nos', 'op': '>', 'limite': 2, 'iso': '2026-11-09T10:00:00-03:00', 'who': 'Lucas', 'sim': True}]
FRASE_NAV = 'velocidade, com limite e leitura no plotter'
CHAVE_EMERG = 'capitao.emergenciaAte'


def vazou_sog(c, sog):
    """Onde o texto da faixa (visível, aria-label ou regiões do leitor de tela) deixa a leitura da SOG, o limite (2,0) ou a unidade."""
    campos = {'texto': c['texto'], 'aria': c['aria'] or '', 'status': c['status'] or '', 'anuncio': c['anuncio'] or ''}
    return {k: v for k, v in campos.items() if sog in v or '2,0' in v or 'nós' in v}


def faixa_emergencia(b):
    print('Faixa global × janela de conversa em emergência: o alarme pedido de velocidade sai sem limite nem leitura enquanto a marca vale (CapitaoEmergencia)')
    for nome, vp in (('A1-Ponte-Web', VP_WEB), ('A2-Ponte-Mobile', VP_APP)):
        rot = '%s (%d×%d)' % (nome, vp['width'], vp['height'])
        # 1. controle e marca ligada com a página aberta; zera() devolve a leitura
        pg = abre_faixa(b, nome, vp, fixo='60', pedidos=PED_SOG)
        sog = pg.evaluate("() => window.CapitaoAgora.instante().q.sog_nos.toFixed(1).replace('.', ',')")
        c = pg.evaluate(FAIXA_LE)
        ok('%s: controle, sem a marca: a faixa diz o alarme pedido de velocidade COM a leitura (%s nós) e o limite (2,0 nós)' % (rot, sog), c['existe'] and not c['oculta'] and sog in c['texto'] and '2,0' in c['texto'] and sog in (c['status'] or ''), c)
        e0 = pg.evaluate("() => ({ obj: typeof window.CapitaoEmergencia, v: window.CapitaoEmergencia && window.CapitaoEmergencia.valendo(), ate: window.CapitaoEmergencia && window.CapitaoEmergencia.ate() })")
        ok('%s: a marca existe (window.CapitaoEmergencia) e começa sem valer' % rot, e0['obj'] == 'object' and e0['v'] is False and e0['ate'] == 0, e0)
        pg.evaluate("() => window.CapitaoEmergencia.marca()")
        pg.wait_for_timeout(350)   # o evento 'capitao-emergencia' refaz a faixa na hora (não espera o tique de 1 s)
        c = pg.evaluate(FAIXA_LE)
        m = pg.evaluate("() => ({ v: window.CapitaoEmergencia.valendo(), falta: window.CapitaoEmergencia.ate() - Date.now(), ss: sessionStorage.getItem('%s'), ls: Object.keys(localStorage).filter((k) => /emerg/i.test(k)) })" % CHAVE_EMERG)
        ok('%s: marca() liga a janela por 15 min (valendo, faltam %.0f s), guarda o fim no sessionStorage e nada no localStorage' % (rot, m['falta'] / 1000), m['v'] and 880e3 <= m['falta'] <= 900.5e3 and (m['ss'] or '').isdigit() and m['ls'] == [], m)
        ok('%s: com a marca valendo a faixa diz «%s» e não deixa nenhuma leitura da SOG, o limite nem «nós» (texto, aria-label, região educada e região assertiva): %s' % (rot, FRASE_NAV, vazou_sog(c, sog) or 'limpo'),
           FRASE_NAV in c['texto'] and not vazou_sog(c, sog) and FRASE_NAV in (c['aria'] or ''), (c, vazou_sog(c, sog)))
        ok('%s: com a marca valendo a faixa continua AVISO, sem fala e sem registro' % rot, c['nivel'] == 'aviso' and c['falas'] == 0 and c['registro'] == [], c)
        pg.evaluate("() => window.CapitaoEmergencia.zera()")
        pg.wait_for_timeout(350)
        c = pg.evaluate(FAIXA_LE)
        ok('%s: zera() fecha a janela (NOVA e ENCERRAR) e a faixa volta a dizer a leitura (%s nós)' % (rot, sog), sog in c['texto'] and not pg.evaluate("() => window.CapitaoEmergencia.valendo()") and pg.evaluate("() => sessionStorage.getItem('%s')" % CHAVE_EMERG) is None, c)
        pg.evaluate("() => window.CapitaoEmergencia.marca(Date.now() + 3600e3)")
        ate = pg.evaluate("() => window.CapitaoEmergencia.ate() - Date.now()")
        ok('%s: a janela nunca passa de 15 min (marca com 1 h pedida: faltam %.0f s)' % (rot, ate / 1000), ate <= 900.5e3, ate)
        ok('%s: sem erro de script' % rot, not pg.erros, pg.erros)
        fecha(pg)
        # 2. a marca já valia ao abrir a página (a janela atravessa a navegação, pela aba): nenhuma região do leitor de tela chega a dizer a SOG
        pg = abre_faixa(b, nome, vp, fixo='60', pedidos=PED_SOG, extra="try { sessionStorage.setItem('%s', String(Date.now() + 600e3)); } catch (e) {}" % CHAVE_EMERG)
        c = pg.evaluate(FAIXA_LE)
        ok('%s: com a marca já valendo ao abrir a página, a faixa, o aria-label e a região educada (que anuncia o aviso uma vez) não trazem a SOG: %s' % (rot, vazou_sog(c, sog) or 'limpo'),
           c['existe'] and not c['oculta'] and FRASE_NAV in c['texto'] and FRASE_NAV in (c['status'] or '') and not vazou_sog(c, sog), (c, vazou_sog(c, sog)))
        fecha(pg)
        # 3. a janela acaba pelo relógio de verdade: sem o evento de zerar, o próximo tique volta à leitura
        pg = abre_faixa(b, nome, vp, fixo='60', pedidos=PED_SOG, extra="try { sessionStorage.setItem('%s', String(Date.now() + 2500)); } catch (e) {}" % CHAVE_EMERG)
        c = pg.evaluate(FAIXA_LE)
        ok('%s: marca que vence em 2,5 s: no começo a faixa ainda não diz a SOG' % rot, FRASE_NAV in c['texto'] and sog not in c['texto'], c)
        pg.wait_for_timeout(2600)
        c = pg.evaluate(FAIXA_LE)
        ok('%s: vencida a janela, o tique seguinte devolve a leitura (%s nós) à faixa' % (rot, sog), sog in c['texto'] and '2,0' in c['texto'], c)
        fecha(pg)
        # 4. a marca que estava lá antes da faixa dizer a SOG: a região educada guardava o texto com a leitura e a janela a esvazia
        pg = abre_faixa(b, nome, vp, fixo='60', pedidos=PED_SOG)
        antes = pg.evaluate(FAIXA_LE)
        pg.evaluate("() => window.CapitaoEmergencia.marca()")
        pg.wait_for_timeout(350)
        c = pg.evaluate(FAIXA_LE)
        ok('%s: a região educada já tinha dito a SOG (%s): ao abrir a janela ela é esvaziada, sem anunciar nada novo' % (rot, 'sim' if sog in (antes['status'] or '') else 'NÃO'), sog in (antes['status'] or '') and not (c['status'] or '').strip() and not (c['anuncio'] or '').strip(), (antes['status'], c))
        fecha(pg)


def codigo_faixa():
    print('O código da faixa global (capitao-app.js): sem timer, sem fala, sem registro, sem troca de tela; dentro das exclusões')
    src = le('capitao-app.js')
    i, j = src.index('// ——— Faixa global de alerta'), src.index('// Versões misturadas')
    blo = re.sub(r'/\*.*?\*/', '', src[i:j], flags=re.S)
    blo = re.sub(r'(?m)^\s*//.*$|\s//\s.*$', '', blo)
    ok('o bloco da faixa não tem setInterval, setTimeout nem requestAnimationFrame (acompanha os eventos do replay)', not re.search(r'setInterval|setTimeout|requestAnimationFrame', blo), re.findall(r'.{15}(?:setInterval|setTimeout).{15}', blo)[:2])
    ok('nunca fala, grava, troca de tela nem abre o SOS ou a C3 sozinha (speechSynthesis, speak, localStorage.setItem, addDiario, location.href/assign/replace/reload, window.open)',
       not re.search(r'speechSynthesis|\.speak\(|localStorage\s*\.\s*setItem|addDiario|markExec|location\s*(\.\s*(href|assign|replace|reload)|=)|window\s*\.\s*open|history\s*\.\s*(push|replace)State', blo), re.findall(r'.{15}(?:speak|setItem|location|window\s*\.\s*open).{15}', blo)[:3])
    ok('a faixa só nasce onde há a API de alertas e a tela não é S1/S2, o Manual nem a C3 (temFaixa)', "!/^(Manual-|C3-|S[12]-SOS-)/.test(ARQ)" in blo and '!!window.CapitaoAlertas' in blo and "!/SOS-/.test(location.pathname)" in blo and r"/\.dc\.html$/.test(ARQ)" in blo)
    ok('os textos entram em nós Text (data) e os atributos só mudam quando o valor muda (nenhum innerHTML com dado; textContent só no <style> e nas duas regiões do leitor de tela)',
       "t.data !== v) t.data = v" in blo and not re.search(r'innerHTML\s*=\s*[^;]*(?:a\.texto|a\.desdeTxt|texto)', blo) and set(re.findall(r'(\w+)\.textContent', blo)) == {'st', 'fxAlerta', 'fxStatus'}, set(re.findall(r'(\w+)\.textContent', blo)))
    ok('só a prancheta já desenhada (art()) e o fit() reservam a altura da faixa (topo()), e o capitao-topo junta os pedidos num schedule()', "var tp = topo();" in src and "+ tp;" in src and "addEventListener('capitao-topo', schedule)" in src)


# Main, H2 e E1 se redesenham a cada setState (o __setLogicState do support.js sempre troca o __v): só dão setState quando o texto exibido muda.
GATING_TELAS = (('Main', 1440, 900), ('H2-Home-Mobile', 390, 844), ('E1-Navegando-Gatilhos', 360, 640),
                ('A1-Ponte-Web', 1440, 900), ('A2-Ponte-Mobile', 390, 844), ('A4-Sensores-Web', 1440, 900), ('A5-Sensores-Mobile', 390, 844),   # (P4C: a Ponte e o mapa de sensores)
                ('B1-Carta-Web', 1440, 900), ('B2-Carta-Mobile', 390, 844),   # (P4D: a Gestão e os Sistemas)
                ('E2-Navegando-Sintoma', 390, 844, '#sis=motores'),   # (P4F: a triagem, com o sistema dos motores aberto: a leitura de agora é o texto que anda; o 4º item é o endereço)
                ('F2-FAQ-Estabilizador-Web', 1440, 900), ('F3-FAQ-Eletronicos', 390, 844), ('F4-FAQ-Gerador-Web', 1440, 900), ('F5-FAQ-Climatizacao', 390, 844))   # (P4H: o estado a bordo dos FAQs; uma por número, web ou app)


def gating(b, telas=GATING_TELAS, livre_ms=8000):
    print('Main, H2, E1, E2, A1, A2, A4, A5, B1, B2 e F2 a F5: setState só quando o texto exibido muda')
    pgs = [(t[0], abre(b, caminho='/%s.dc.html%s' % (t[0], t[3] if len(t) > 3 else ''), sessao=True, init=MOLDURA_JS, viewport={'width': t[1], 'height': t[2]}, espera="() => window.CapitaoReplay && window.__ticks >= 1"))
           for t in telas]
    pgs[0][1].wait_for_timeout(3500)
    for nome, pg in pgs:
        pg.evaluate("() => { window.__sets = 0; window.__ticks = 0; }")
    pgs[0][1].wait_for_timeout(livre_ms)
    livre = {nome: pg.evaluate("() => ({ sets: window.__sets, ticks: window.__ticks })") for nome, pg in pgs}
    for nome, pg in pgs:
        pg.evaluate("() => { window.CapitaoReplay.fixar(60); }")
    pgs[0][1].wait_for_timeout(1800)
    for nome, pg in pgs:
        pg.evaluate("() => { window.__sets = 0; window.__ticks = 0; }")
    pgs[0][1].wait_for_timeout(3300)
    for nome, pg in pgs:
        f = pg.evaluate("""() => { const v = window.CapitaoTelemetria.atual(), nb = (x) => x.toFixed(1).replace('.', ','), t = document.body.innerText, rpm = window.CapitaoAgora.fmt.campo(v, 'motor_bb_rpm');
          return { sets: window.__sets, ticks: window.__ticks, sog: nb(v.sog_nos), temSog: t.indexOf(nb(v.sog_nos)) >= 0, rpm: rpm, temRpm: t.indexOf(rpm) >= 0 }; }""")
        l = livre[nome]
        ok('%s: livre, %d setState em %d tiques (nunca mais que um por tique)' % (nome, l['sets'], l['ticks']), l['ticks'] >= livre_ms // 1000 - 2 and l['sets'] <= l['ticks'], l)
        if nome.startswith('H2'):
            ok('%s: livre, nenhum setState (o único texto vindo do motor é o LED, que não muda)' % nome, l['sets'] == 0, l)
        ok('%s: com o instante fixado, %d tiques e nenhum setState (o texto exibido não mudou)' % (nome, f['ticks']), f['ticks'] >= 3 and f['sets'] == 0, f)
        if not nome.startswith(('H2', 'A5', 'B1', 'B2', 'E2', 'F')):   # (a H2 e a A5 não mostram o SOG: a A5 mostra os valores dos sensores, conferidos no verificar.py › teste_sensores; a E2 mostra a rotação dos motores; os FAQs, a hora do instante)
            ok('%s: a tela mostra o SOG do instante fixado (%s nós): não deixou de se atualizar' % (nome, f['sog']), f['temSog'], f)
        if nome.startswith(('B1', 'B2', 'E2')):   # (P4D: a Gestão e os Sistemas mostram a rotação dos motores, não o SOG; P4F: a triagem, com os motores abertos, também)
            ok('%s: a tela mostra a rotação do BB do instante fixado (%s rpm): não deixou de se atualizar' % (nome, f['rpm']), f['temRpm'], f)
        if nome[0] == 'F' and nome[1] in '2345':   # (P4H: o estado a bordo dos FAQs mostra a hora do instante fixado)
            ok('%s: a tela mostra a hora do instante fixado (12:01:00): não deixou de se atualizar' % nome, pg.evaluate("() => document.body.innerText.indexOf('Telemetria ao vivo · 12:01:00') >= 0"), f)
        ok('%s: sem erro de script' % nome, not pgs[[n for n, _ in pgs].index(nome)][1].erros, pgs[[n for n, _ in pgs].index(nome)][1].erros)
    for nome, pg in pgs:
        fecha(pg)


# P4G: a virada do dia de bordo (o evento 'capitao-rebase' do motor) na Home. Os prazos dos cartões (a tarefa do rotor atrasada, o chip do CONSOLE) só se refazem quando o dia vira; a Main e a H2 só dão setState
# se o texto que exibem a partir deles mudou. Com o instante fixado e o prazo igual, 5 viradas não redesenham nada; com a tarefa executada (Executado), 1 redesenho e o cartão sem o atraso.
HOME_REBASE = (('Main', 1440, 900), ('H2-Home-Mobile', 390, 844))
EXEC_ROTOR = '{"gerador-rotor": {"iso": "2026-11-10T09:00:00-03:00", "t": "09:00", "sim": true}}'
LE_ROTOR = """() => ({ sets: window.__sets, txt: document.body.innerText, titulos: [...document.querySelectorAll('[data-home=cartao]')].map((e) => e.title), chips: [...document.querySelectorAll('[data-home=chip]')].map((e) => e.innerText.trim()) })"""


def home_rebase(b, telas=HOME_REBASE):
    print('Main e H2: a virada do dia de bordo (capitao-rebase) só redesenha quando o prazo exibido muda')
    for nome, w, h in telas:
        pg = abre(b, caminho='/%s.dc.html' % nome, sessao=True, init=MOLDURA_JS, viewport={'width': w, 'height': h}, espera="() => window.CapitaoReplay && window.__ticks >= 1")
        pg.evaluate("() => { window.CapitaoReplay.fixar(60); }")
        pg.wait_for_timeout(2500)
        pg.evaluate("() => { window.__sets = 0; for (let i = 0; i < 5; i++) window.dispatchEvent(new CustomEvent('capitao-rebase', { detail: { ms: Date.now() } })); }")
        pg.wait_for_timeout(600)
        r = pg.evaluate(LE_ROTOR)
        ok('%s: 5 viradas do dia com o prazo igual não redesenham nada (%d setState)' % (nome, r['sets']), r['sets'] == 0, r)
        antes_rotor = ('ROTOR · 2 D' in r['txt']) if nome == 'Main' else any('rotor em atraso' in t for t in r['titulos'])
        ok('%s: o rotor aparece em atraso antes do Executado (o teste vale)' % nome, antes_rotor, r['chips'] if nome == 'Main' else r['titulos'])
        # aba escondida (document.hidden, só durante a chamada, que é síncrona: o motor segue o relógio de verdade): a virada do dia não dá setState nem com o prazo mudado (o Executado volta ao que era no fim da chamada)
        sets_escondida = pg.evaluate("""(ex) => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
          try { localStorage.setItem('capitao.executado.v1', ex); window.__sets = 0; window.dispatchEvent(new CustomEvent('capitao-rebase', { detail: { ms: Date.now() } })); return window.__sets; }
          finally { localStorage.removeItem('capitao.executado.v1'); delete document.hidden; } }""", EXEC_ROTOR)
        ok('%s: com a aba escondida a virada do dia não dá setState (%d), mesmo com o prazo mudado' % (nome, sets_escondida), sets_escondida == 0, sets_escondida)
        # de volta à frente, logo depois de um tique (o próximo vem só 1 s depois: nenhum tique redesenha dentro da janela de 150 ms, então quem atualiza o cartão é a virada do dia)
        pg.evaluate("() => new Promise((res) => { const f = () => { window.removeEventListener('capitao-telemetria', f); res(true); }; window.addEventListener('capitao-telemetria', f); })")
        pg.evaluate("(ex) => { localStorage.setItem('capitao.executado.v1', ex); window.__sets = 0; window.dispatchEvent(new CustomEvent('capitao-rebase', { detail: { ms: Date.now() } })); }", EXEC_ROTOR)
        pg.wait_for_timeout(150)
        r = pg.evaluate(LE_ROTOR)
        depois_rotor = ('ROTOR' in r['txt']) if nome == 'Main' else any('rotor em atraso' in t for t in r['titulos'])
        ok('%s: com o rotor executado a virada do dia redesenha uma vez (%d setState) em até 150 ms e o cartão sai do atraso' % (nome, r['sets']), r['sets'] == 1 and not depois_rotor, r)
        ok('%s: sem erro de script' % nome, not pg.erros, pg.erros)
        fecha(pg)


# ——— 12. as telas de verdade ———
def telas(b):
    print('Telas de verdade (com sessão): o motor carrega, anda e não dá erro de script')
    for nome, vp in (('Main', {'width': 1440, 'height': 900}), ('A1-Ponte-Web', {'width': 1440, 'height': 900}), ('E1-Navegando-Gatilhos', {'width': 1440, 'height': 900}),
                     ('H2-Home-Mobile', {'width': 390, 'height': 844}), ('C3-Leme-Alerta', {'width': 390, 'height': 844}), ('Manual-Capitao-IA', {'width': 1440, 'height': 900}),
                     ('A2-Ponte-Mobile', {'width': 390, 'height': 844}), ('A4-Sensores-Web', {'width': 1440, 'height': 900}), ('A5-Sensores-Mobile', {'width': 390, 'height': 844}),
                     ('B1-Carta-Web', {'width': 1440, 'height': 900}), ('B2-Carta-Mobile', {'width': 390, 'height': 844}), ('B3-Carta-Resposta', {'width': 390, 'height': 844}),   # (P4D: a Carta)
                     ('E2-Navegando-Sintoma', {'width': 390, 'height': 844})):   # (P4F: a triagem)
        pg = abre(b, caminho='/%s.dc.html' % nome, sessao=True, viewport=vp, espera='() => window.CapitaoReplay')
        pg.wait_for_timeout(1500)
        r = pg.evaluate("() => ({ obj: typeof window.CapitaoReplay, ativo: window.CapitaoReplay.ativo(), inst: window.CapitaoAgora.instante().fonte, n: window.__conta('capitao-telemetria'), t: window.CapitaoTelemetria ? window.CapitaoTelemetria.fonte() : 'sem' })")
        ok('%s: CapitaoReplay existe e anda (ativo, instante() do replay, %d tiques em 1,5 s%s)' % (nome, r['n'], '' if r['t'] == 'sem' else ', CapitaoTelemetria.fonte() = ' + r['t']),
           r['obj'] == 'object' and r['ativo'] and r['inst'] == 'replay' and r['n'] >= 1 and r['t'] in ('sem', 'replay'), r)
        ok('%s: sem erro de script' % nome, not pg.erros, pg.erros)
        fecha(pg)


# ——— 12b. a API de alertas (capitao-alertas.js; P2C, F05; CONTRATO §1.16 e §1.24) ———
# A página mínima carrega o dados, o replay e os alertas na ordem das telas (o alertas logo depois do replay).
HTML_ALERTAS = ('<!doctype html><meta charset="utf-8"><title>alertas</title><script src="/capitao-dados.js"></script><script src="/capitao-replay.js"></script>'
                '<script src="/capitao-alertas.js"></script><script src="/capitao-telemetria.js"></script>')
ESPERA_AL = '() => window.CapitaoAlertas && window.CapitaoAgora && window.CapitaoAgora.relogio'
CHAVE_ANUNCIADOS = 'capitao.alertas.anunciados'
CHAVES_ALERTA = {'id', 'nivel', 'rotulo', 'cor', 'rgb', 'sistema', 'lado', 'campo', 'titulo', 'valor', 'limite', 'un', 'valorTxt', 'limiteTxt', 'texto', 'desde', 'desdeMs', 'hora', 'seg',
                 'guia', 'secao', 'fonte', 'passos', 'detalhe'}


def abre_al(b, **kw):
    kw.setdefault('html', HTML_ALERTAS)
    kw.setdefault('espera', ESPERA_AL)
    return abre(b, **kw)


def init_fixo(x='105', sobre=None):
    """Script de página que congela o instante (e, se houver, planta valores no quadro pelo gancho 'sobre')."""
    s = "localStorage.setItem('capitao.replay.fixo', %s);" % json.dumps(x)
    if sobre is not None:
        s += " localStorage.setItem('capitao.replay.sobre', %s);" % json.dumps(json.dumps(sobre))
    return s


ALERTAS_VOLTA_JS = r"""() => {
  const R = window.CapitaoReplay, A = window.CapitaoAgora, AL = window.CapitaoAlertas, lim = window.CapitaoDados.replay.limites, anc = A.ancora(Date.now()), o = { voltas: [] };
  for (const K of [0, 120, 575]) {   // a 1ª volta do dia (07:00), uma do meio e a última
    const base = anc + K * 150 * 1000, v = { K, itens: [] };
    for (let t = 0; t < 150; t++) {
      const ms = base + t * 1000, l = AL.ativos(ms), q = R.em(ms), alm = R.alarmes(ms), c = AL.contagem(ms), tc = AL.tocando(ms), p = l.length ? AL.porId(l[0].id, ms) : null;
      const fora = Object.keys(lim).filter((cp) => { const n = A.nivel(cp, q); return n && n.nivel !== 'normal'; }).sort();
      v.itens.push({ t, ids: l.map((x) => x.id), niveis: l.map((x) => x.nivel), campos: l.map((x) => x.campo).sort(), fora,
        nivelPelaAgora: l.every((x) => { const n = A.nivel(x.campo, q); return !!n && n.nivel === x.nivel && n.limite === x.limite && q[x.campo] === x.valor; }),
        igualAoReplay: l.length === alm.length && l.every((x) => { const a = alm.find((y) => y.id === x.id); return !!a && a.nivel === x.nivel && a.valor === x.valor && a.limite === x.limite && a.desde === x.desde
          && a.campo === x.campo && a.sistema === x.sistema && (a.lado || '') === (x.lado || ''); }),
        tc: tc && tc.id, p: p && p.id === l[0].id, c });
    }
    o.voltas.push(v);
  }
  return o;
}"""

ALERTAS_ITEM_JS = r"""() => {
  const R = window.CapitaoReplay, AL = window.CapitaoAlertas, T = R.fixar('105'), a = AL.ativos()[0], b = AL.porId('arref_be'), c = AL.tocando(), d = AL.ativos(T), copia = JSON.parse(JSON.stringify(a));
  a.passos.push('x'); a.passos[0] = 'trocado'; a.titulo = 'x'; a.nivel = 'critico';
  const depois = AL.ativos()[0], cat = window.CapitaoDados.replay.alertas.arref_be;
  return { T, a: copia, chaves: Object.keys(copia).sort(), igual: [b, c, d[0]].every((x) => JSON.stringify(x) === JSON.stringify(copia)), n: d.length,
    semAlias: JSON.stringify(depois) === JSON.stringify(copia) && cat.passos.length === copia.passos.length && cat.passos[0] === copia.passos[0] && cat.titulo === copia.titulo };
}"""


def a_alertas_volta(b):
    print('Alertas: só dentro da janela do alarme, um id por campo, nível pela CapitaoAgora.nivel, igual ao alarmes() do replay')
    pg = abre_al(b)
    r = pg.evaluate(ALERTAS_VOLTA_JS)
    dentro = set(range(JANELA_INI, JANELA_FIM + 1))
    ids_catalogo = D['replay']['alertas']
    ok('3 voltas do dia (a 1ª, a 121ª e a última): ativos() tem alerta exatamente nos segundos %d a %d da janela do gerador, e fora dela é []' % (JANELA_INI, JANELA_FIM),
       all({i['t'] for i in v['itens'] if i['ids']} == dentro and all(i['ids'] == [] for i in v['itens'] if i['t'] not in dentro) for v in r['voltas']),
       [sorted({i['t'] for i in v['itens'] if i['ids']})[:3] for v in r['voltas']])
    ok('dentro da janela o alerta é um só, o arref_be (campo motor_be_arref_c); tocando() é ele e porId() acha o mesmo; fora, tocando() é null',
       all(i['ids'] == ['arref_be'] and i['campos'] == ['motor_be_arref_c'] and i['tc'] == 'arref_be' and i['p'] is True for v in r['voltas'] for i in v['itens'] if i['t'] in dentro)
       and all(i['tc'] is None for v in r['voltas'] for i in v['itens'] if i['t'] not in dentro), None)
    ok('um id por campo em todos os 450 segundos (sem id repetido) e o catálogo D.replay.alertas tem um id por campo, o mesmo conjunto de campos do D.replay.limites',
       all(len(set(i['ids'])) == len(i['ids']) for v in r['voltas'] for i in v['itens'])
       and len({a['campo'] for a in ids_catalogo.values()}) == len(ids_catalogo) and {a['campo'] for a in ids_catalogo.values()} == set(D['replay']['limites']),
       (len(ids_catalogo), len(D['replay']['limites'])))
    ok('o nível, o limite e o valor de cada alerta são os da CapitaoAgora.nivel sobre o mesmo quadro, em todos os 450 segundos; com o cenário aviso nenhum é crítico',
       all(i['nivelPelaAgora'] for v in r['voltas'] for i in v['itens']) and all(n == 'aviso' for v in r['voltas'] for i in v['itens'] for n in i['niveis']),
       [(v['K'], i['t']) for v in r['voltas'] for i in v['itens'] if not i['nivelPelaAgora']][:3])
    ok('a lista é exatamente os campos que a nivel() põe fora do normal (nem a mais, nem a menos), segundo a segundo',
       all(i['campos'] == i['fora'] for v in r['voltas'] for i in v['itens']), [(v['K'], i['t'], i['campos'], i['fora']) for v in r['voltas'] for i in v['itens'] if i['campos'] != i['fora']][:3])
    ok('cada alerta é o alarme do replay (id, nivel, campo, sistema, lado, valor, limite e desde iguais ao alarmes() do mesmo instante)', all(i['igualAoReplay'] for v in r['voltas'] for i in v['itens']))
    ok('contagem(): total 1, aviso 1, crítico 0, maior \'aviso\' dentro da janela; zeros e maior null fora',
       all(i['c'] == {'total': 1, 'aviso': 1, 'critico': 0, 'maior': 'aviso'} for v in r['voltas'] for i in v['itens'] if i['t'] in dentro)
       and all(i['c'] == {'total': 0, 'aviso': 0, 'critico': 0, 'maior': None} for v in r['voltas'] for i in v['itens'] if i['t'] not in dentro))
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)

    print('Alertas: o conteúdo de cada alerta (catálogo + alarme), em 12:01:45')
    pg = abre_al(b)
    r = pg.evaluate(ALERTAS_ITEM_JS)
    cat = D['replay']['alertas']['arref_be']
    ini = r['T'] - 6000
    a = r['a']
    esperado = {'id': 'arref_be', 'nivel': 'aviso', 'rotulo': 'AVISO', 'sistema': 'motores', 'lado': 'be', 'campo': 'motor_be_arref_c', 'titulo': cat['titulo'], 'valor': 89.6, 'limite': 88, 'un': '°C',
                'valorTxt': '89,6 °C', 'limiteTxt': '88 °C', 'texto': cat['titulo'] + ': 89,6 °C (acima de 88 °C)', 'desdeMs': ini,
                'desde': datetime.fromtimestamp(ini / 1000, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'hora': datetime.fromtimestamp(ini / 1000, BR).strftime('%H:%M:%S'), 'seg': 6,
                'guia': cat['guia'], 'secao': cat['secao'], 'fonte': cat['fonte'], 'passos': cat['passos'], 'detalhe': 'C3-Leme-Alerta.dc.html#alarme=arref_be'}
    dif = {k: (a.get(k), v) for k, v in esperado.items() if a.get(k) != v}
    ok('fixado em 12:01:45: título, valor 89,6 °C acima de 88 °C, início 12:01:39 há 6 s, guia, seção, fonte e passos do catálogo, link para a C3 (#alarme=arref_be)', dif == {}, dif)
    ok('as cores são os tokens do tema (--cap-warn e --cap-rgb) e o rótulo é AVISO; a lista de chaves do alerta é a do contrato (lado só quando se aplica)',
       a['cor'] == 'var(--cap-warn, #f0a63a)' and a['rgb'] == 'var(--cap-warn-rgb, 240,166,58)' and set(r['chaves']) == CHAVES_ALERTA, (a['cor'], set(r['chaves']) ^ CHAVES_ALERTA))
    ok('ativos(), ativos(fixo), porId() e tocando() devolvem o mesmo alerta, e o texto, a hora e os passos não têm os termos proibidos (coordenada nem existe: as chaves são só as do contrato)',
       r['igual'] and r['n'] == 1 and not re.search(r'simula|demo|fict[ií]cio|roteiro|la[cç]o|150 s|snapshot', a['texto'] + a['hora'] + ' '.join(a['passos']), re.I), r['n'])
    ok('quem recebe o alerta recebe uma cópia: mexer nos passos, no título ou no nível não mexe no D.replay.alertas nem no alerta seguinte', r['semAlias'] is True)
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


def a_alertas_varios(b):
    print('Alertas: vários ao mesmo tempo (valores plantados): um id por campo, ordem e nível; aviso → crítico → aviso no mesmo id')
    plantado = {'diesel_litros': 100, 'tanque_agua_pct': 10, 'porao_bb_nivel': 12, 'bateria_2_tensao_v': 11.0, 'motor_bb_oleo_bar': 0.5}
    JS = r"""() => { const R = window.CapitaoReplay, A = window.CapitaoAgora, AL = window.CapitaoAlertas, q = R.quadro(), l = AL.ativos(), lim = {};
      l.forEach((x) => { lim[x.id] = x.limite; });
      return { cen: window.CapitaoDados.replay.cenario, ids: l.map((x) => x.id), niveis: l.map((x) => x.nivel), rot: l.map((x) => x.rotulo), lim,
        nv: l.map((x) => { const n = A.nivel(x.campo, q); return n && n.nivel; }), nvLim: l.map((x) => { const n = A.nivel(x.campo, q); return n && n.limite; }),
        campoDoCatalogo: l.every((x) => window.CapitaoDados.replay.alertas[x.id].campo === x.campo), c: AL.contagem(), tc: AL.tocando() && AL.tocando().id,
        semLado: l.filter((x) => !('lado' in x)).map((x) => x.id), lado: l.filter((x) => 'lado' in x).map((x) => x.id + ':' + x.lado),
        texto: Object.fromEntries(l.map((x) => [x.id, x.texto])), cor: Object.fromEntries(l.map((x) => [x.id, x.cor])) }; }"""
    pg = abre_al(b, init=init_fixo('105', plantado))
    r = pg.evaluate(JS)
    ok('cenário aviso, 5 valores plantados (e o arref_be da janela): 6 alertas, todos AVISO; o mais antigo (arref_be, 12:01:39) primeiro e os demais por id',
       r['cen'] == 'aviso' and r['ids'] == ['arref_be', 'agua', 'b12', 'diesel', 'oleo_bb', 'porao_bb'] and set(r['niveis']) == {'aviso'} and set(r['rot']) == {'AVISO'}, r)
    ok('o crítico que a nivel() acha nos plantados (diesel, porão, óleo, 12 V) vira AVISO no cenário aviso, com o limite do aviso (400 L, 5 cm, 2,4 bar, 12,2 V); o resto é o nível da nivel()',
       r['nv'] == ['aviso', 'aviso', 'critico', 'critico', 'critico', 'critico'] and r['lim'] == {'arref_be': 88, 'agua': 15, 'b12': 12.2, 'diesel': 400, 'oleo_bb': 2.4, 'porao_bb': 5}, (r['nv'], r['lim']))
    ok('contagem() com 6 avisos: total 6, aviso 6, crítico 0, maior \'aviso\'; tocando() é o arref_be', r['c'] == {'total': 6, 'aviso': 6, 'critico': 0, 'maior': 'aviso'} and r['tc'] == 'arref_be', (r['c'], r['tc']))
    ok('o id é do catálogo e o campo dele é o do alerta; lado só nos motores/porão com lado (BB/BE), e o texto leva o valor e o limite como a tela mostra',
       r['campoDoCatalogo'] and sorted(r['semLado']) == ['agua', 'b12', 'diesel'] and sorted(r['lado']) == ['arref_be:be', 'oleo_bb:bb', 'porao_bb:bb']
       and r['texto']['diesel'] == 'Diesel a bordo: 100 L (abaixo de 400 L)' and r['texto']['agua'] == 'Tanque de água doce: 10,0 % (abaixo de 15 %)'
       and r['texto']['porao_bb'].endswith(': 12,0 cm (acima de 5 cm)'), r['texto'])
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)

    pg = abre_al(b, init=init_fixo('105', plantado), depois="window.CapitaoDados.replay.cenario = 'alarme-critico';")
    r = pg.evaluate(JS)
    ok('cenário alarme-critico (só no gerador; aqui injetado): o crítico passa — b12, diesel, oleo_bb e porao_bb (por id) antes dos avisos arref_be (o mais antigo) e agua',
       r['cen'] == 'alarme-critico' and r['ids'] == ['b12', 'diesel', 'oleo_bb', 'porao_bb', 'arref_be', 'agua'] and r['niveis'] == ['critico'] * 4 + ['aviso'] * 2
       and r['rot'] == ['CRÍTICO'] * 4 + ['AVISO'] * 2, r)
    ok('no cenário crítico o nível e o limite de cada alerta são os da CapitaoAgora.nivel, sem rebaixar', r['niveis'] == r['nv'] and [r['lim'][i] for i in r['ids']] == r['nvLim'], (r['niveis'], r['nv']))
    ok('contagem() = total 6, aviso 2, crítico 4, maior \'critico\'; tocando() é o primeiro crítico (b12); a cor do crítico é --cap-crit e a do aviso --cap-warn',
       r['c'] == {'total': 6, 'aviso': 2, 'critico': 4, 'maior': 'critico'} and r['tc'] == 'b12'
       and r['cor']['b12'] == 'var(--cap-crit, #ff3b30)' and r['cor']['agua'] == 'var(--cap-warn, #f0a63a)', (r['c'], r['tc'], r['cor']))
    r = pg.evaluate(r"""() => { const AL = window.CapitaoAlertas, set = (v) => { localStorage.setItem('capitao.replay.sobre', JSON.stringify({ diesel_litros: v })); const a = AL.porId('diesel'); return a && [a.nivel, a.id, a.rotulo]; };
      return [set(300), set(100), set(300), set(500)]; }""")
    ok('o mesmo id muda de nível com o valor: diesel aviso (300 L) → crítico (100 L) → aviso (300 L) → sem alerta (500 L)',
       r == [['aviso', 'diesel', 'AVISO'], ['critico', 'diesel', 'CRÍTICO'], ['aviso', 'diesel', 'AVISO'], None], r)
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


def a_alertas_uma_vez(b):
    print('Alertas: anunciados uma vez por id por sessão (sessionStorage, sempre em try/catch), com o estado exposto pela API')
    JS = r"""() => { const R = window.CapitaoReplay, AL = window.CapitaoAlertas, o = {};
      o.antes = [AL.anunciado('arref_be'), AL.novos().map((x) => x.id)];
      o.a1 = AL.anunciar('arref_be'); o.a2 = AL.anunciar('arref_be');
      o.depois = [AL.anunciado('arref_be'), AL.novos().map((x) => x.id), AL.ativos().map((x) => x.id)];
      o.chave = sessionStorage.getItem('capitao.alertas.anunciados');
      o.ruins = [AL.anunciar('nao_existe'), AL.anunciar('constructor'), AL.anunciar('__proto__'), AL.anunciar('toString'), AL.anunciar(5), AL.anunciar(null), AL.anunciar(''), AL.anunciar({}), AL.anunciar(['arref_be']),
        AL.anunciado('nao_existe'), AL.anunciado('constructor'), AL.anunciado(7), AL.anunciado(undefined)];
      o.chaveRuins = sessionStorage.getItem('capitao.alertas.anunciados');
      R.fixar('60'); o.fora = [AL.ativos().length, AL.anunciado('arref_be'), AL.anunciar('arref_be')];
      R.fixar('105'); o.volta = [AL.anunciar('arref_be'), AL.novos().length, AL.anunciado('arref_be')];
      o.outro = [AL.anunciar('agua'), AL.anunciar('agua'), AL.anunciado('agua')];
      o.fim = sessionStorage.getItem('capitao.alertas.anunciados');
      return o; }"""
    pg = abre_al(b, init=init_fixo('105'))
    r = pg.evaluate(JS)
    ok('1ª vez: anunciado() false e novos() com o arref_be; anunciar() true uma vez e false na seguinte; depois anunciado() true, novos() vazio e o alerta segue ativo',
       r['antes'] == [False, ['arref_be']] and r['a1'] is True and r['a2'] is False and r['depois'] == [True, [], ['arref_be']], r)
    ok('o estado fica no sessionStorage \'%s\' = {"arref_be": true}' % CHAVE_ANUNCIADOS, json.loads(r['chave']) == {'arref_be': True}, r['chave'])
    ok('id que não existe, \'constructor\', \'__proto__\', \'toString\', número, null, vazio e objeto: anunciar() false, anunciado() false, o sessionStorage não muda e nada lança',
       r['ruins'] == [False] * 13 and r['chaveRuins'] == r['chave'], (r['ruins'], r['chaveRuins']))
    ok('sair da janela (12:01:00) e voltar (12:01:45) não anuncia de novo: anunciado() continua true, anunciar() false e novos() vazio',
       r['fora'] == [0, True, False] and r['volta'] == [False, 0, True], (r['fora'], r['volta']))
    ok('outro id do catálogo (agua) anuncia uma vez e entra no mesmo mapa', r['outro'] == [True, False, True] and json.loads(r['fim']) == {'arref_be': True, 'agua': True}, (r['outro'], r['fim']))
    ok('sem erro de script', not pg.erros, pg.erros)
    pg.reload()
    pg.wait_for_function(ESPERA_AL)
    r = pg.evaluate("() => { const AL = window.CapitaoAlertas; return { a: AL.anunciado('arref_be'), n: AL.novos().length, again: AL.anunciar('arref_be'), chave: sessionStorage.getItem('capitao.alertas.anunciados') }; }")
    ok('depois de recarregar a página (mesma sessão do navegador): o arref_be segue anunciado, novos() vazio e anunciar() false', r['a'] is True and r['n'] == 0 and r['again'] is False and json.loads(r['chave']) == {'arref_be': True, 'agua': True}, r)
    fecha(pg)
    pg = abre_al(b, init=init_fixo('105'))   # contexto novo = sessão nova (aba nova, sessionStorage vazio)
    r = pg.evaluate("() => { const AL = window.CapitaoAlertas; return [AL.anunciado('arref_be'), AL.anunciar('arref_be')]; }")
    ok('numa sessão nova (contexto novo, sessionStorage vazio) o arref_be volta a ser anunciável: false e depois true', r == [False, True], r)
    fecha(pg)

    # sessionStorage negado, cheio ou com lixo: a API não lança e segue funcionando
    NEGADO = "Object.defineProperty(window, 'sessionStorage', { get() { throw new Error('negado'); }, configurable: true });"
    pg = abre_al(b, init=init_fixo('105') + NEGADO)
    r = pg.evaluate("() => { const AL = window.CapitaoAlertas; try { return [AL.anunciado('arref_be'), AL.anunciar('arref_be'), AL.anunciar('arref_be'), AL.anunciado('arref_be'), AL.novos().length, AL.ativos().length]; } catch (e) { return String(e); } }")
    ok('sessionStorage que lança no acesso: anunciar() true uma vez e false depois (vale a memória da página), anunciado() true, novos() vazio, sem lançar', r == [False, True, False, True, 0, 1], r)
    ok('sessionStorage negado: sem erro de script', not pg.erros, pg.erros)
    fecha(pg)
    CHEIO = ("const si = Storage.prototype.setItem; Storage.prototype.setItem = function (k, v) { if (k === 'capitao.alertas.anunciados') throw new Error('cheio'); return si.apply(this, arguments); };")
    pg = abre_al(b, init=init_fixo('105') + CHEIO)
    r = pg.evaluate("() => { const AL = window.CapitaoAlertas; return [AL.anunciar('arref_be'), AL.anunciar('arref_be'), AL.anunciado('arref_be'), sessionStorage.getItem('capitao.alertas.anunciados')]; }")
    ok('sessionStorage que não grava (cheio): anunciar() true uma vez e false depois, pela memória da página; nada foi gravado', r == [True, False, True, None], r)
    fecha(pg)
    for lixo, esperado in (('["arref_be"]', 'lista'), ('[1,2', 'JSON quebrado'), ('"arref_be"', 'texto'), ('null', 'null'), ('{"arref_be":"sim","agua":true}', 'valor que não é true')):
        pg = abre_al(b, init=init_fixo('105') + "sessionStorage.setItem('capitao.alertas.anunciados', %s);" % json.dumps(lixo))
        r = pg.evaluate("() => { const AL = window.CapitaoAlertas; return [AL.anunciado('arref_be'), AL.anunciado('agua'), AL.anunciar('arref_be'), AL.anunciar('arref_be')]; }")
        ok('sessionStorage com lixo (%s: %s) vale como vazio, sem lançar: arref_be não está anunciado, anunciar() true e depois false%s' % (esperado, lixo, ' (agua true segue anunciado)' if 'agua' in lixo else ''),
           r == [False, 'agua' in lixo, True, False], r)
        fecha(pg)


def a_alertas_ms(b):
    """O parâmetro `ms` (CONTRATO §1.24) de ativos, porId, tocando, contagem e novos. O instante fica FIXADO e o `ms` aponta para o outro lado da janela: sem o `ms` a API
    olha o instante fixado, com ele olha o `ms`. Em nenhum dos dois sentidos o resultado pode vir do relógio real (a janela de 99 a 116 s cobre ~12 % do ciclo)."""
    print('Alertas: o ms de ativos(), porId(), tocando(), contagem() e novos() vale o instante pedido, nos dois sentidos, com o instante fixado do outro lado da janela')
    JS = r"""(delta) => { const R = window.CapitaoReplay, AL = window.CapitaoAlertas, fx = R.agora(), ms = fx + delta, ids = (l) => l.map((x) => x.id), nenhum = { total: 0, aviso: 0, critico: 0, maior: null };
      const a = AL.porId('arref_be', ms), t = AL.tocando(ms), semMs = AL.porId('arref_be');
      return { fx, ms, fixo: R.fixo(),
        semMs: { ativos: ids(AL.ativos()), porId: semMs && semMs.id, tocando: AL.tocando() && AL.tocando().id, contagem: AL.contagem(), novos: ids(AL.novos()) },
        comMs: { ativos: ids(AL.ativos(ms)), porId: a && [a.id, a.nivel, a.seg], tocando: t && t.id, contagem: AL.contagem(ms), novos: ids(AL.novos(ms)), outro: AL.porId('agua', ms) },
        nenhum };
    }"""
    pg = abre_al(b, init=init_fixo('60'))   # fixado em 12:01:00, fora da janela; o ms é 12:01:45, dentro dela (o arref_be começou em 12:01:39: seg 6)
    r = pg.evaluate(JS, 45000)
    ok('instante fixado em 12:01:00 (fora da janela): sem ms nada está ativo (ativos [], porId e tocando null, contagem zerada, novos [])',
       r['fixo'] == r['fx'] and r['semMs'] == {'ativos': [], 'porId': None, 'tocando': None, 'contagem': r['nenhum'], 'novos': []}, (r['fixo'], r['fx'], r['semMs']))
    ok('com ms = 12:01:45 (dentro da janela) o arref_be está ativo: ativos(ms), porId(id, ms) (aviso, há 6 s), tocando(ms), contagem(ms) total 1 e novos(ms); outro id (agua) continua null',
       r['comMs'] == {'ativos': ['arref_be'], 'porId': ['arref_be', 'aviso', 6], 'tocando': 'arref_be', 'contagem': {'total': 1, 'aviso': 1, 'critico': 0, 'maior': 'aviso'}, 'novos': ['arref_be'], 'outro': None}, r['comMs'])
    r2 = pg.evaluate("() => { const AL = window.CapitaoAlertas, ids = (l) => l.map((x) => x.id), ms = window.CapitaoReplay.agora() + 45000; return { anuncia: AL.anunciar('arref_be'), novosMs: ids(AL.novos(ms)), ativosMs: ids(AL.ativos(ms)), novos: ids(AL.novos()) }; }")
    ok('depois de anunciar(), novos(ms) fica vazio e ativos(ms) segue com o arref_be (anunciar não depende do instante: vale pelo id do catálogo)',
       r2 == {'anuncia': True, 'novosMs': [], 'ativosMs': ['arref_be'], 'novos': []}, r2)
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)

    pg = abre_al(b, init=init_fixo('105'))   # fixado em 12:01:45, dentro da janela; o ms é 12:01:00, fora dela
    r = pg.evaluate(JS, -45000)
    ok('instante fixado em 12:01:45 (dentro da janela): sem ms o arref_be está ativo (ativos, porId, tocando, contagem e novos)',
       r['semMs'] == {'ativos': ['arref_be'], 'porId': 'arref_be', 'tocando': 'arref_be', 'contagem': {'total': 1, 'aviso': 1, 'critico': 0, 'maior': 'aviso'}, 'novos': ['arref_be']}, r['semMs'])
    ok('com ms = 12:01:00 (fora da janela) nada está ativo: ativos(ms) [], porId(id, ms) e tocando(ms) null, contagem(ms) zerada, novos(ms) []',
       r['comMs'] == {'ativos': [], 'porId': None, 'tocando': None, 'contagem': r['nenhum'], 'novos': [], 'outro': None}, r['comMs'])
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


def a_alertas_eventos(b):
    print('Alertas: a API acompanha o evento \'capitao-alerta\' do replay (não há evento próprio)')
    pg = abre_al(b)
    r = pg.evaluate(r"""() => { const R = window.CapitaoReplay, AL = window.CapitaoAlertas, vistos = [];
      R.fixar('60');   // sai do que o relógio real tenha acabado de emitir (a página pode ter carregado dentro da janela)
      window.addEventListener('capitao-alerta', (e) => { const t = AL.tocando(); vistos.push({ fase: e.detail.fase, id: e.detail.alarme.id, naApi: !!AL.porId(e.detail.alarme.id), total: AL.contagem().total, tocando: t && t.id }); });
      R.fixar('105'); R.fixar('105'); R.fixar('125'); return vistos; }""")
    ok('inicio do arref_be: no mesmo instante a API já tem o alerta (porId, total 1, tocando); fim: a API já não tem (porId false, total 0, tocando null); nenhum outro evento',
       r == [{'fase': 'inicio', 'id': 'arref_be', 'naApi': True, 'total': 1, 'tocando': 'arref_be'}, {'fase': 'fim', 'id': 'arref_be', 'naApi': False, 'total': 0, 'tocando': None}], r)
    r = pg.evaluate("() => ({ proprios: window.__ev.filter((e) => /alertas/.test(e.n)).length, nomes: [...new Set(window.__ev.map((e) => e.n))] })")
    ok('a API não emite evento nenhum (só os do replay: capitao-telemetria, capitao-alerta e capitao-rebase)', r['proprios'] == 0 and set(r['nomes']) <= {'capitao-telemetria', 'capitao-alerta', 'capitao-rebase'}, r)
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


def a_alertas_sem_efeito(b):
    print('Alertas: nunca fala, grava, abre janela nem troca de tela; só escreve no sessionStorage, na chave dos anunciados')
    pg = abre_al(b, init=init_fixo('105'))
    r = pg.evaluate(r"""() => { const AL = window.CapitaoAlertas, cont = { fala: 0, abre: 0, push: 0, replace: 0 }, ps = history.pushState, rs = history.replaceState, wo = window.open;
      try { speechSynthesis.speak = function () { cont.fala++; }; } catch (e) {}
      window.open = function () { cont.abre++; return null; };
      history.pushState = function () { cont.push++; return ps.apply(history, arguments); }; history.replaceState = function () { cont.replace++; return rs.apply(history, arguments); };
      const ls = () => JSON.stringify(Object.assign({}, localStorage)), antes = ls(), href = location.href, tit = document.title, nos = document.body ? document.body.childElementCount : 0;
      AL.ativo(); AL.ativos(); AL.porId('arref_be'); AL.tocando(); AL.contagem(); AL.novos(); AL.anunciar('arref_be'); AL.anunciar('agua'); AL.anunciado('arref_be');
      return { cont, ls: ls() === antes, href: location.href === href, titulo: document.title === tit, nos: (document.body ? document.body.childElementCount : 0) === nos, ss: Object.keys(sessionStorage), diario: localStorage.getItem('capitao.diario.v1') }; }""")
    ok('usar toda a API não fala (speechSynthesis.speak), não abre janela, não troca de endereço (pushState, replaceState, href), não mexe no título nem no corpo da página',
       r['cont'] == {'fala': 0, 'abre': 0, 'push': 0, 'replace': 0} and r['href'] and r['titulo'] and r['nos'], r)
    ok('não grava no localStorage (o diário nem existe) e o único sessionStorage escrito é o dos anunciados', r['ls'] and r['diario'] is None and r['ss'] == [CHAVE_ANUNCIADOS], r)
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


STUB_JS = r"""(alarmes) => { window.CapitaoReplay = { ativo: () => true, agora: () => Date.now(), alarmes: () => alarmes }; return window.CapitaoAlertas.ativos().map((x) => [x.id, x.nivel, x.titulo, x.passos.length]); }"""


def a_alertas_real(b):
    print('Alertas: modo real inerte (simulacao = false), com a flag lida a cada chamada, mesmo com um replay que mente')
    INERTE = r"""() => { const AL = window.CapitaoAlertas;
      return { ativo: AL.ativo(), ativos: AL.ativos(), ativos150: AL.ativos(Date.now()), porId: AL.porId('arref_be'), tocando: AL.tocando(), contagem: AL.contagem(), novos: AL.novos(), anunciado: AL.anunciado('arref_be'),
        anunciar: AL.anunciar('arref_be'), ss: Object.keys(sessionStorage), nivel: Object.keys(AL.NIVEL) }; }"""
    pg = abre_al(b, depois='window.CapitaoDados.simulacao = false;')
    r = pg.evaluate(INERTE)
    ok('simulacao = false: ativo() false, ativos() [], porId() e tocando() null, contagem() zerada, novos() [], anunciado() e anunciar() false, nada gravado no sessionStorage',
       r['ativo'] is False and r['ativos'] == [] and r['ativos150'] == [] and r['porId'] is None and r['tocando'] is None and r['contagem'] == {'total': 0, 'aviso': 0, 'critico': 0, 'maior': None}
       and r['novos'] == [] and r['anunciado'] is False and r['anunciar'] is False and r['ss'] == [] and r['nivel'] == ['aviso', 'critico'], r)
    alarme = {'id': 'arref_be', 'nivel': 'aviso', 'sistema': 'motores', 'lado': 'be', 'campo': 'motor_be_arref_c', 'valor': 89.6, 'limite': 88, 'desde': '2026-10-29T15:01:39Z'}
    r = pg.evaluate(STUB_JS, [alarme])
    ok('simulacao = false com um CapitaoReplay que diz estar ativo e devolve um alarme: a API continua inerte (a flag é lida por ela mesma, não só pelo replay) e anunciar() não grava',
       r == [] and pg.evaluate("() => [window.CapitaoAlertas.anunciar('arref_be'), Object.keys(sessionStorage)]") == [False, []], r)
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)
    pg = abre_al(b, init=init_fixo('105'))
    pg.evaluate("() => { window.CapitaoDados.simulacao = false; }")
    r = pg.evaluate(INERTE)
    ok('a flag desligada com a página aberta: a API fica inerte na próxima chamada', r['ativo'] is False and r['ativos'] == [] and r['tocando'] is None and r['anunciar'] is False and r['ss'] == [], r)
    r = pg.evaluate("() => { window.CapitaoDados.simulacao = true; const AL = window.CapitaoAlertas; return [AL.ativo(), AL.ativos().map((x) => x.id), AL.tocando() && AL.tocando().id]; }")
    ok('ligada de novo, a API volta sozinha (sem recarregar): o arref_be de 12:01:45', r == [True, ['arref_be'], 'arref_be'], r)
    fecha(pg)


def a_alertas_replay_mentiroso(b):
    print('Alertas: o que o replay devolve passa por filtro (id repetido, nível desconhecido, item que não é objeto, alerta fora do catálogo)')
    base = {'sistema': 'motores', 'lado': 'be', 'campo': 'motor_be_arref_c', 'valor': 89.6, 'limite': 88, 'desde': '2026-10-29T15:01:39Z'}
    pg = abre_al(b)
    sujo = [None, 7, 'x', [], {}, {'id': 5, 'nivel': 'aviso'}, {'id': '', 'nivel': 'aviso'}, dict(base, id='arref_be', nivel='normal'), dict(base, id='arref_be', nivel='constructor'), dict(base, id='arref_be', nivel='toString'),
            dict(base, id='arref_be', nivel='aviso')]
    r = pg.evaluate(STUB_JS, sujo)
    ok('lista suja do replay (null, número, texto, vazio, id que não é texto, nível normal/constructor/toString): só o aviso válido sobra, com título e passos do catálogo',
       r == [['arref_be', 'aviso', D['replay']['alertas']['arref_be']['titulo'], len(D['replay']['alertas']['arref_be']['passos'])]], r)
    pg2 = abre_al(b)
    for ordem in ('aviso,critico', 'critico,aviso'):
        niveis = ordem.split(',')
        r = pg2.evaluate(STUB_JS, [dict(base, id='arref_be', nivel=n) for n in niveis])
        ok('o mesmo id duas vezes na lista do replay (%s): fica um só, o mais grave (crítico)' % ordem, [x[:2] for x in r] == [['arref_be', 'critico']], r)
    r = pg2.evaluate(STUB_JS, [dict(base, id='zzz', nivel='aviso', desde='x'), dict(base, id='arref_be', nivel='aviso')])
    ok('alarme fora do catálogo não some (o catálogo é detalhe, não filtro): entra depois do que tem início válido', [x[:2] for x in r] == [['arref_be', 'aviso'], ['zzz', 'aviso']], r)
    r = pg2.evaluate(r"""() => { const AL = window.CapitaoAlertas, z = AL.porId('zzz'); return { titulo: z.titulo, passos: z.passos, seg: z.seg, desdeMs: z.desdeMs, hora: z.hora, anuncia: AL.anunciar('zzz'), de_novo: AL.anunciar('zzz') }; }""")
    ok('o alerta fora do catálogo tem o título do campo, passos [], desde inválido (desdeMs null, hora vazia, seg 0) e pode ser anunciado uma vez (id ativo agora)',
       r == {'titulo': D['campos']['motor_be_arref_c']['rotulo'], 'passos': [], 'seg': 0, 'desdeMs': None, 'hora': '', 'anuncia': True, 'de_novo': False}, r)
    r = pg2.evaluate(STUB_JS, [dict(base, id='__proto__', nivel='aviso')])
    r2 = pg2.evaluate("() => { const AL = window.CapitaoAlertas; return [AL.anunciar('__proto__'), AL.anunciar('__proto__'), AL.anunciado('__proto__'), AL.porId('__proto__') !== null, JSON.parse(sessionStorage.getItem('capitao.alertas.anunciados')).hasOwnProperty('__proto__')]; }")
    ok('um id \'__proto__\' vindo do replay é chave comum (nada de protótipo): sai na lista, anunciar() true e depois false, e fica gravado no mapa', [x[:2] for x in r] == [['__proto__', 'aviso']] and r2 == [True, False, True, True, True], (r, r2))
    ok('sem erro de script', not pg.erros and not pg2.erros, pg.erros + pg2.erros)
    fecha(pg)
    fecha(pg2)


LANCA_AL_JS = r"""() => {
  const AL = window.CapitaoAlertas, nomes = ['ativo', 'ativos', 'porId', 'tocando', 'contagem', 'anunciado', 'anunciar', 'novos'];
  const lixo = [undefined, null, NaN, Infinity, -Infinity, -1, 0, 1e300, 'x', '', {}, [], true, function () {}, Symbol('s'), new Date(NaN), { valueOf() { throw new Error('boom'); } }, { toString() { throw new Error('boom'); } }];
  const lancou = []; let chamadas = 0;
  for (const n of nomes) for (const a of lixo) for (const b of lixo) { chamadas++; try { AL[n](a, b); } catch (e) { lancou.push(n + ' ' + e); } }
  return { lancou: lancou.slice(0, 5), chamadas, ok: AL.ativos().length };
}"""


def a_alertas_nunca_lanca(b):
    print('Alertas: nunca lança erro (argumentos absurdos, dado e peças quebrados)')
    pg = abre_al(b, init=init_fixo('105'))
    r = pg.evaluate(LANCA_AL_JS)
    ok('%d chamadas com argumentos absurdos (undefined, NaN, Infinity, 1e300, texto, objeto, Symbol, valueOf que lança…): nenhuma lançou e a API segue dando o alerta' % r['chamadas'], r['lancou'] == [] and r['ok'] == 1, r)
    r = pg.evaluate(r"""() => { const AL = window.CapitaoAlertas, R = window.CapitaoReplay, A = window.CapitaoAgora, D = window.CapitaoDados, o = {}, tenta = (n, g) => { try { o[n] = g(); } catch (e) { o[n] = 'LANÇOU ' + e; } };
      const al = R.alarmes; R.alarmes = function () { throw new Error('quebrou'); }; tenta('alarmesLanca', () => [AL.ativos(), AL.tocando(), AL.contagem().total]); R.alarmes = al;
      const fm = A.fmt; A.fmt = undefined; tenta('semFmt', () => { const x = AL.ativos()[0]; return [x.valorTxt, x.hora, x.texto]; }); A.fmt = fm;
      const cat = D.replay.alertas; D.replay.alertas = undefined; tenta('semCatalogo', () => { const x = AL.ativos()[0]; return [x.id, x.titulo, x.passos.length]; }); D.replay.alertas = cat;
      const cp = D.campos; D.campos = undefined; tenta('semCampos', () => { const x = AL.ativos(); return x.length; }); D.campos = cp;
      tenta('normal', () => AL.ativos().length); return o; }""")
    ok('replay.alarmes() que lança: ativos() [], tocando() null, contagem() zerada, sem lançar', r['alarmesLanca'] == [[], None, 0], r['alarmesLanca'])
    ok('CapitaoAgora.fmt ausente: o alerta sai com o número cru e sem a hora (o texto é o que dá), sem lançar',
       isinstance(r['semFmt'], list) and r['semFmt'][0] == '89.6 °C' and r['semFmt'][1] == '' and r['semFmt'][2].startswith('Temperatura do motor BE: 89.6 °C (acima de 88 °C)'), r['semFmt'])
    ok('D.replay.alertas ausente: o alerta sai com o rótulo do campo e sem passos; D.campos ausente: não lança', isinstance(r['semCatalogo'], list) and r['semCatalogo'][2] == 0 and not isinstance(r['semCampos'], str) and r['normal'] == 1, (r['semCatalogo'], r['semCampos']))
    ok('sem erro de script', not pg.erros, pg.erros)
    fecha(pg)


def a_alertas_sos(b, so_s1=False):
    print('S1/S2 e rotas /SOS-: sem CapitaoAlertas, nenhuma leitura de D.simulacao nem de D.replay')
    for nome, caminho in (('S1-SOS-Web', '/S1-SOS-Web.dc.html'), ('S2-SOS-Mobile', '/S2-SOS-Mobile.dc.html'))[:1 if so_s1 else 2]:
        pg = abre(b, caminho=caminho, antes=GETTER + GETTER_REPLAY)
        pg.wait_for_timeout(1500)
        r = pg.evaluate("() => ({ alertas: typeof window.CapitaoAlertas, replay: typeof window.CapitaoReplay, lidas: window.__lidas, lidasReplay: window.__lidasReplay })")
        ok('%s: CapitaoAlertas não existe (a tela nem carrega o arquivo), D.simulacao e D.replay nunca lidos' % nome, r['alertas'] == 'undefined' and r['replay'] == 'undefined' and r['lidas'] == 0 and r['lidasReplay'] == 0, r)
        pg.add_script_tag(url=BASE + '/capitao-alertas.js')
        r = pg.evaluate("() => ({ alertas: typeof window.CapitaoAlertas, lidas: window.__lidas, lidasReplay: window.__lidasReplay })")
        ok('%s: nem o arquivo carregado à força define o CapitaoAlertas, e nada é lido' % nome, r == {'alertas': 'undefined', 'lidas': 0, 'lidasReplay': 0}, r)
        ok('%s: sem erro de script' % nome, not pg.erros, pg.erros)
        fecha(pg)
    if so_s1:
        return
    pg = abre(b, caminho='/SOS-teste.html', html=HTML_ALERTAS, antes=GETTER + GETTER_REPLAY, espera='() => window.CapitaoAgora && window.CapitaoAgora.relogio')
    pg.wait_for_timeout(1500)
    r = pg.evaluate("() => ({ alertas: typeof window.CapitaoAlertas, replay: typeof window.CapitaoReplay, lidas: window.__lidas, lidasReplay: window.__lidasReplay })")
    ok('rota mínima /SOS-teste.html com o replay e os alertas no <head>: nenhum dos dois é definido e nada é lido', r == {'alertas': 'undefined', 'replay': 'undefined', 'lidas': 0, 'lidasReplay': 0}, r)
    fecha(pg)
    pg = abre(b, html=HTML_ALERTAS, antes=GETTER + GETTER_REPLAY, espera=ESPERA_AL)
    r = pg.evaluate("() => { const AL = window.CapitaoAlertas; AL.ativos(); return { alertas: typeof AL, lidas: window.__lidas, lidasReplay: window.__lidasReplay }; }")
    ok('controle fora do SOS (a mesma página com outro nome): a API existe e lê D.simulacao e D.replay (≥ 1) quando usada', r['alertas'] == 'object' and r['lidas'] >= 1 and r['lidasReplay'] >= 1, r)
    fecha(pg)


def a_alertas_telas(b):
    print('Alertas nas telas de verdade (com sessão, instante fixado em #replay=105): a API existe e dá o alerta; sem erro de script')
    for nome, vp in (('A1-Ponte-Web', {'width': 1440, 'height': 900}), ('H2-Home-Mobile', {'width': 390, 'height': 844}), ('C3-Leme-Alerta', {'width': 390, 'height': 844}), ('Manual-Capitao-IA', {'width': 1440, 'height': 900})):
        pg = abre(b, caminho='/%s.dc.html#replay=105' % nome, sessao=True, viewport=vp, espera='() => window.CapitaoAlertas')
        pg.wait_for_timeout(1200)
        r = pg.evaluate("() => { const AL = window.CapitaoAlertas, t = AL.tocando(); return { ativo: AL.ativo(), id: t && t.id, nivel: t && t.nivel, total: AL.contagem().total, replay: typeof window.CapitaoReplay, url: location.pathname }; }")
        ok('%s: CapitaoAlertas existe e dá o AVISO do arref_be às 12:01:45 (total 1); a tela não trocou de endereço' % nome,
           r['ativo'] and r['id'] == 'arref_be' and r['nivel'] == 'aviso' and r['total'] == 1 and r['url'] == '/%s.dc.html' % nome, r)
        ok('%s: sem erro de script' % nome, not pg.erros, pg.erros)
        fecha(pg)


def codigo_alertas():
    print('O arquivo capitao-alertas.js: sem lookbehind, sem snapshot, sem avaliar limite, sem evento nem timer; nas 36 telas e no CORE do sw.js')
    src = le('capitao-alertas.js')
    cod = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
    cod = re.sub(r'(?m)^\s*//.*$|\s//\s.*$', '', cod)
    ok('sem lookbehind (?<…) e sem \\w para palavra em português', '(?<' not in src and '\\w' not in src)
    ok('o código (fora dos comentários) não menciona snapshot: nunca o lê', not re.search(r'snapshot', cod, re.I), re.findall(r'.{20}snapshot.{20}', cod, re.I)[:2])
    ok('não depende do capitao-brain.js nem do CapitaoTelemetria, e não se registra como CapitaoTelemetria ou CapitaoReplay',
       not re.search(r'CapitaoBrain|capitao-brain|CapitaoTelemetria|window\s*\.\s*CapitaoReplay\s*=', cod), re.findall(r'.{15}(?:CapitaoBrain|CapitaoTelemetria).{15}', cod)[:2])
    ok('não avalia limite: não lê D.replay.limites nem chama a CapitaoAgora.nivel (o nível vem do alarmes() do replay, que já usou a nivel)', not re.search(r'limites|\.\s*nivel\s*\(|A\.nivel|CapitaoAgora\s*\.\s*nivel', cod), re.findall(r'.{15}limites.{15}', cod)[:2])
    ok('sem evento nem timer próprios (addEventListener, dispatchEvent, CustomEvent, setTimeout, setInterval): o replay basta', not re.search(r'addEventListener|dispatchEvent|CustomEvent|setTimeout|setInterval|requestAnimationFrame|MutationObserver', cod))
    ok('só emite dado: nada que troque de tela, abra janela, fale, grave o diário ou chame o SOS (location=, window.open, speechSynthesis, capitao-voz, addDiario, markExec, S1/S2-SOS, history.pushState)',
       not re.search(r'location\s*(\.\s*(href|assign|replace|reload)|=)|window\s*\.\s*open|speechSynthesis|capitao-voz|addDiario|markExec|S1-SOS|S2-SOS|history\s*\.\s*(push|replace)State|document\s*\.\s*(write|createElement|body)', cod),
       re.findall(r'.{15}(?:location|window\s*\.\s*open|speechSynthesis|addDiario|SOS).{15}', cod)[:3])
    ok('escreve só no sessionStorage, uma chamada de setItem, na chave dos anunciados; não toca o localStorage', len(re.findall(r'setItem', cod)) == 1 and re.findall(r"'(capitao\.[a-z.]+)'", cod) == [CHAVE_ANUNCIADOS]
       and 'localStorage' not in cod and 'removeItem' not in cod, (re.findall(r'setItem', cod), re.findall(r"'(capitao\.[a-z.]+)'", cod)))
    ok('sem VERSAO própria (acompanha o capitao-dados.js)', 'VERSAO' not in cod)
    ok('sai em /SOS- antes de definir qualquer coisa, e a flag D.simulacao é lida só dentro de ativo() (a cada chamada), nunca na carga',
       re.search(r"EM_SOS = /SOS-/\.test\(location\.pathname\)", cod) is not None and 'if (EM_SOS || window.CapitaoAlertas) return;' in cod and cod.count('simulacao') == 1
       and re.search(r'function ativo\(\) \{[^}]*simulacao === true', cod) is not None)
    sw = le('sw.js')
    ok('sw.js: ./capitao-alertas.js no CORE, logo depois do ./capitao-replay.js', "'./capitao-replay.js', './capitao-alertas.js'," in sw)
    m = re.search(r'const TELAS = \[(.*?)\];', sw, re.S)
    telas_ = re.findall(r"'([^']+)'", m.group(1))
    erradas, sem_sos = [], []
    for t in telas_:
        h = le(t + '.dc.html')
        if t.startswith(('S1-', 'S2-')):
            if 'capitao-alertas' in h:
                sem_sos.append(t)
            continue
        i, j, k, f = h.find('<script src="./capitao-dados.js">'), h.find('<script src="./capitao-replay.js">'), h.find('<script src="./capitao-alertas.js">'), h.find('<script src="./support.js">')
        if h.count('capitao-alertas.js') != 1 or not (0 <= i < j < k < f) or not re.search(r'<script src="\./capitao-replay\.js"></script>\r?\n<script src="\./capitao-alertas\.js"></script>', h):
            erradas.append(t)
    ok('as %d telas fora do SOS têm o <script src="./capitao-alertas.js"> uma vez, na linha seguinte ao capitao-replay.js (depois do capitao-dados.js e antes do support.js)' % (len(telas_) - 2), erradas == [], erradas)
    ok('S1 e S2 não carregam o capitao-alertas.js', sem_sos == [], sem_sos)
    fora = [a for a in ('index.html', 'login.html', 'dados.html') if 'capitao-alertas' in le(a)]
    ok('index.html, login.html e dados.html (fora das TELAS: não leem alerta) não carregam a API', fora == [], fora)


# P2C: defeitos plantados no capitao-alertas.js; cada um tem de ser acusado pelo teste que cuida dele.
MUTANTES_AL = [
    ('a saída em /SOS- removida (o S1 carregado à força passaria a ter CapitaoAlertas)', [("if (EM_SOS || window.CapitaoAlertas) return;", "if (window.CapitaoAlertas) return;")], lambda b: a_alertas_sos(b, so_s1=True)),
    ('o D.simulacao ignorado na própria API (um replay que mente alimentaria o modo real)', [("return !!(d && d.simulacao === true && d.replay && R && R.ativo());", "return !!(d && d.replay && R && R.ativo());")], a_alertas_real),
    ('a lista sem o filtro de nível desconhecido (\'normal\', \'constructor\' derrubariam a lista inteira)', [(" || !dono(NIVEL, al.nivel)) continue;", ") continue;")], a_alertas_replay_mentiroso),
    ('o id repetido sem escolher o mais grave (o último vence)', [("if (!dono(por, al.id) || NIVEL[a.nivel].peso > NIVEL[por[al.id].nivel].peso) por[al.id] = a;", "por[al.id] = a;")], a_alertas_replay_mentiroso),
    ('a ordem invertida (aviso antes de crítico)', [("return NIVEL[y.nivel].peso - NIVEL[x.nivel].peso ||", "return NIVEL[x.nivel].peso - NIVEL[y.nivel].peso ||")], a_alertas_varios),
    ('os passos sem cópia (quem recebe o alerta mexeria no catálogo do D)', [("a.passos = e && Array.isArray(e.passos) ? e.passos.slice() : [];", "a.passos = e && Array.isArray(e.passos) ? e.passos : [];")], a_alertas_volta),
    ('anunciar() sem conferir se já foi anunciado (anunciaria toda vez)', [("if (!ativo() || !conhecido(id) || anunciado(id)) return false;", "if (!ativo() || !conhecido(id)) return false;")], a_alertas_uma_vez),
    ('anunciar() sem conferir o id (qualquer texto entraria no sessionStorage)', [("if (!ativo() || !conhecido(id) || anunciado(id)) return false;", "if (!ativo() || typeof id !== 'string' || anunciado(id)) return false;")], a_alertas_uma_vez),
    ('sem a memória da página quando o sessionStorage nega (a faixa anunciaria a cada tique)', [("catch (e) { memoria[id] = true; }", "catch (e) {}")], a_alertas_uma_vez),
    ('o limite do alerta tirado do valor em vez do alarme (a nivel() deixaria de ser a fonte)', [("a.valor = al.valor; a.limite = al.limite;", "a.valor = al.valor; a.limite = al.valor;")], a_alertas_volta),
    # o parâmetro `ms`: cada função que o repassa a ativos() tem de ser acusada SEM depender do relógio real (a_alertas_ms fixa o instante do outro lado da janela)
    ('porId() sem repassar o ms (olharia o instante fixado/agora em vez do pedido)', [("if (typeof id !== 'string') return null;\n      var l = ativos(ms), i;", "if (typeof id !== 'string') return null;\n      var l = ativos(), i;")], a_alertas_ms),
    ('novos() sem repassar o ms (a lista dos não anunciados sairia do instante errado)', [("return ativos(ms).filter(function (a) { return !anunciado(a.id); });", "return ativos().filter(function (a) { return !anunciado(a.id); });")], a_alertas_ms),
    ('tocando() sem repassar o ms (a faixa mostraria o alerta do instante errado)', [("return ativos(ms)[0] || null;", "return ativos()[0] || null;")], a_alertas_ms),
    ('contagem() sem repassar o ms (o total sairia do instante errado)', [("var l = ativos(ms), i;\n      for (i = 0; i < l.length; i++) { o.total++;", "var l = ativos(), i;\n      for (i = 0; i < l.length; i++) { o.total++;")], a_alertas_ms),
]


def mutantes_alertas(b):
    global MUT_ARQ, CAPTURA
    print('Mutantes da API de alertas (P2C): cada defeito plantado tem de ser acusado pelo teste que cuida dele')
    src = le('capitao-alertas.js')
    for nome, trocas, teste in MUTANTES_AL:
        faltam = [x for x, _ in trocas if src.count(x) != 1]
        if faltam:
            ok('mutante «%s»: o trecho está uma vez no capitao-alertas.js' % nome, False, faltam)
            continue
        MUT_ARQ, CAPTURA, caiu = {'capitao-alertas.js': trocas}, [], ''
        sai = sys.stdout
        try:
            sys.stdout = open(os.devnull, 'w')
            try:
                teste(b)
            except Exception as e:   # aqui um erro do próprio teste NÃO conta como acusação (esconderia um erro de código do teste): reprova
                caiu = 'o teste caiu: %s' % str(e).splitlines()[0][:160]
        finally:
            sys.stdout.close()
            sys.stdout = sai
            achados, MUT_ARQ, CAPTURA = CAPTURA, None, None
        ok('mutante: %s — acusado (%d conferência(s) falham)' % (nome, len(achados)), len(achados) > 0 and not caiu, caiu or achados)


# ——— 13. mutantes: o teste acusa o motor quebrado ———
# Cada mutante troca um trecho do capitao-replay.js servido ao navegador; o teste que cuida daquilo tem de falhar (senão ele poderia passar no vácuo).
MUTANTES = [
    ('o laço sem o ruído por hash (a paridade com o gerador acusa)', [("if (r && r[0]) x = x + r[0] * ruido(r[1], t);", "")], a_volta),
    ('o rebaixamento do crítico fora do cenário alarme-critico removido (o cenário aviso devolveria crítico)',
     [("if (nv.nivel === 'critico' && !critico) nv = rebaixa(lim[campo], nv, res[campo]);", "")], a_alarmes),
    ('a distância de cada volta contada 3× (a posição salta em toda emenda de 150 s)', [("cb.distancia_mn + v * pv.distancia_mn + p.cumM[t]", "cb.distancia_mn + v * pv.distancia_mn * 3 + p.cumM[t]")], o_dia),
    ('o tique emitindo com document.hidden', [("      if (!document.hidden) {\n        var ms = agoraMs()", "      if (true) {\n        var ms = agoraMs()")], eventos_pausa),
    ('o timer da cópia velha vivo (a geração e o clearTimeout global tirados)',
     [("function atual() { return window.__capitaoReplayGen === meu; }", "function atual() { return true; }"), ("clearTimeout(timer); clearTimeout(window.__capitaoReplayTimer);", "clearTimeout(timer);")], eventos_timer),
    ('a saída em /SOS- removida (o S1 passaria a ter CapitaoReplay)', [("if (EM_SOS || window.CapitaoReplay) return;", "if (window.CapitaoReplay) return;")], lambda b: no_sos(b, so_s1=True)),
    ('o D.simulacao ignorado (o modo real andaria)', [("if (!d || d.simulacao !== true || !d.replay", "if (!d || !d.replay")], modo_real_inicial),
    ('em() que devolve o D.snapshot.quadro quando falha', [("function em(ms) { try { return quadroEm(ms, true); }", "function em(ms) { try { return quadroEm(ms, true) || window.CapitaoDados.snapshot.quadro; }")], isolamento_falha),
    ('a proa sem o ruído de 0,4° (só mexe 1 unidade em alguns segundos: a paridade exata acusa, a tolerância de 1 unidade não acusava)',
     [("var proa = pmod(cog - delta + rp[0] * ruido(rp[1], seg), 360);", "var proa = pmod(cog - delta, 360);")], a_volta),
    ('o vento aparente com o COG fora por 0,5° (1 unidade da última casa em alguns segundos: a tolerância de 1 unidade não acusava)',
     [("sog * Math.cos(cog * RAD);\n    o.vento_aparente_nos", "sog * Math.cos((cog + 0.5) * RAD);\n    o.vento_aparente_nos")], a_volta),
    ('a interpolação dos ângulos sem o arco mais curto (o vento que cruza o norte daria a volta ao contrário)',
     [("(pmod(b - a + 540, 360) - 180) * f", "(b - a) * f")], a_volta),
    ('o piso do diesel removido (o dia acabaria abaixo da reserva)',
     [("Math.max(cb.diesel_litros - (v * pv.diesel_l + p.cumD[t]), R.diesel_piso_l || 0)", "cb.diesel_litros - (v * pv.diesel_l + p.cumD[t])")], a_volta),
    ('a fronteira das fases inclusiva (t = 20, 50, 120 e 135 cairiam na fase anterior)',
     [("fs[i].ini <= t && t < fs[i].fim", "fs[i].ini <= t && t <= fs[i].fim")], a_fase),
    ('o gancho \'sobre\' sem a trava do cenário (a lista literal levaria o crítico)',
     [("if (p.R.cenario !== 'alarme-critico') a.nivel = 'aviso';", "")], a_fixar),
    ('a virada comparada só com o tique visível anterior (a página que carregou oculta não rebasearia)',
     [("if (ls(function () { return Ag().rebase(ms); })) emite('capitao-rebase', { ms: ms });",
       "var anc0 = ancoraDe(ms); if (window.__ultAnc != null && anc0 !== window.__ultAnc) { ls(function () { Ag().rebase(ms); }); emite('capitao-rebase', { ms: ms }); } window.__ultAnc = anc0;")],
     eventos_virada_oculta),
    ('contadores() sem argumento no relógio em vez do instante fixado (o "faltam N h" das tarefas leria o dia real)',
     [("function contadores(ms) { ms = msDe(ms);", "function contadores(ms) { ms = ms === undefined || ms === null ? Date.now() : ms;")], a_fixar),
    ('janela() sem argumento no relógio em vez do instante fixado (o NORMALIZADO da C3 leria o dia real)',
     [("      ms = msDe(ms);\n      if (!p || ms === null) return null;\n      G = Object", "      ms = ms === undefined || ms === null ? Date.now() : ms;\n      if (!p || ms === null) return null;\n      G = Object")], a_fixar),
    ('porFaixa() sem argumento no relógio em vez do instante fixado (o consumo por faixa leria o dia real)',
     [("      ms = msDe(ms);\n      if (!p || !fs || ms === null) return null;", "      ms = ms === undefined || ms === null ? Date.now() : ms;\n      if (!p || !fs || ms === null) return null;")], a_fixar),
    ('a prova de vida da tabela removida (o D parcial montaria a tabela e só a guarda de cada saída pegaria o NaN, com ativo() true)', [("return prova(p) ? p : null;", "return p;")], d_parcial),
    ('os 30 quadros-chave por campo não conferidos (chave curta: finita, mas a volta não fecha)', [("|| R.chaves[ch[i]].length !== nChave) return null;", ") return null;")], d_parcial),
    ('a ETA HH:MM fora da prova (velocidade 0 dá ETA infinita: texto não vazio, inválido)', [("textoRuim(o) || !/^\\d\\d:\\d\\d$/.test(o.eta)", "textoRuim(o)")], d_parcial),
    ('o texto «undefined»/«NaN» fora da prova (o local da rota sairia como «undefined, chegando»)',
     [("|| textoRuim(o) ||", "||")], d_parcial),
    ('o quadro sem a guarda de número finito (NaN/Infinity sairiam do em() e do quadro())', [("    if (!sadio(res)) return null;\n", "")], d_parcial),
    ('os contadores sem a guarda de número finito', [("return sadio(v) ? v : null;", "return v;")], d_parcial),
    ('o consumo por faixa sem a guarda de número finito', [("for (i = 0; i < out.length; i++) if (!sadio(out[i])) return null;\n", "")], d_parcial),
    ('a série das janelas longas sem a guarda de ponto finito', [("      return pontosOk(pts);\n    } catch (e) { return null; }", "      return pts;\n    } catch (e) { return null; }")], d_parcial),
]


# P2B: os mesmos defeitos plantados na moldura e nas telas; cada um tem de ser acusado pelo teste de desempenho (uma tela só, janela curta).
A2 = ('A2-Ponte-Mobile', 360, 640)
MUTANTES_ARQ = [
    ('a moldura escrevendo o nó de texto sem comparar (o mesmo valor também gera mutação de caractere)', 'capitao-moldura.js',
     [("function poe(t, v) { if (t.data !== v) t.data = v; }", "function poe(t, v) { t.data = v; }")], 'moldura'),
    ('a moldura escrevendo o atributo sem comparar (o aria-label do LED a cada tique)', 'capitao-moldura.js',
     [("function atr(e, k, v) { if (e.getAttribute(k) !== v) e.setAttribute(k, v); }", "function atr(e, k, v) { e.setAttribute(k, v); }")], 'moldura'),
    ('o tique refazendo o HTML da moldura (o botão do tema e o avatar recriados, o fit() a cada segundo)', 'capitao-moldura.js',
     [("el._on = function () { el.atualiza(); };", "el._on = function () { if (el.monta) el.monta(leitura()); el.atualiza(); };")], 'moldura'),
    ('o LED trocado a cada tique em vez de só quando vira', 'capitao-moldura.js',
     [("if (this._vivo !== L.vivo) { this._vivo = L.vivo; troca(n.led.firstElementChild, led(L.vivo, 7)); }", "{ this._vivo = L.vivo; troca(n.led.firstElementChild, led(L.vivo, 7)); }")], 'moldura'),
    # P4B: o texto da moldura vem do quadro do instante, e o selo e a dica não carregam rótulo (acusados por moldura_quadro)
    ('o diesel da faixa do D.snapshot (848 L de 26/09) em vez do quadro', 'capitao-moldura.js',
     [("var litros = f(q, 'diesel_litros')", "var litros = f(d.snapshot.quadro, 'diesel_litros')")], 'quadro'),
    ('o estado e o local da moldura do D.snapshot em vez do quadro', 'capitao-moldura.js',
     [("estado: typeof q.estado === 'string' && q.estado ? q.estado : falta(SD), local: typeof q.local === 'string' ? q.local : '',", "estado: (d.snapshot || {}).estado, local: (d.snapshot || {}).local,")], 'quadro'),
    ('a posição da moldura do D.snapshot (26°59,58\'S) em vez do quadro', 'capitao-moldura.js',
     [("pos: typeof q.lat === 'number' && typeof q.lon === 'number' && cf ? cf(q.lat, q.lon) : falta(SL),", "pos: ((d.snapshot || {}).gps || {}).texto,")], 'quadro'),
    ('a hora do rótulo sem os segundos (o instante tem HH:MM:SS)', 'capitao-moldura.js',
     [("rotulo: sentenca(I.selo && I.selo.texto) ||", "rotulo: sentenca('AO VIVO · ' + I.hhmm) ||")], 'quadro'),
    ('a dica da pílula de volta com DEMO (rótulo proibido)', 'capitao-moldura.js',
     [("var TIT_VIVO = 'Telemetria ao vivo — atualiza a cada segundo'", "var TIT_VIVO = 'Telemetria ao vivo DEMO — atualiza a cada segundo'")], 'quadro'),
    # P4B: a faixa global de alerta (capitao-app.js), acusada por faixa_global
    ('a faixa nunca aparece (o hidden não sai)', 'capitao-app.js',
     [("if (faixa.hidden) faixa.hidden = false;", "")], 'faixa'),
    ('a faixa não reserva a altura no topo (a prancheta fica por baixo dela)', 'capitao-app.js',
     [("return Math.max(0, Math.ceil(e.getBoundingClientRect().bottom));", "return 0;")], 'faixa'),
    ('o nó de texto da faixa escrito sem comparar (mutação de caractere a cada tique)', 'capitao-app.js',
     [("function fxEscreve(t, v) { if (t.data !== v) t.data = v; }", "function fxEscreve(t, v) { t.data = v; }")], 'faixa'),
    ('ABRIR leva sempre à lista da Ponte, nunca à C3', 'capitao-app.js',
     [("function fxDestino(a) { return a ? (a.detalhe || ponte()) : ponte(); }", "function fxDestino(a) { return ponte(); }")], 'faixa'),
    ('o aviso antes do crítico na ordem da faixa', 'capitao-app.js',
     [("return fxPeso(y.nivel) - fxPeso(x.nivel) ||", "return fxPeso(x.nivel) - fxPeso(y.nivel) ||")], 'faixa'),
    ('a CONVERSA aberta não cala as regiões do leitor de tela', 'capitao-app.js',
     [("    if (conversaAberta()) return;   // (antes do fxNovos: o que ficou calado continua novo e é dito quando a conversa fechar)\n", "")], 'faixa'),
    ('a faixa fala o alerta (speechSynthesis) sem gesto', 'capitao-app.js',
     [("fxFalado = 's' + sig; fxStatus.textContent = ''; fxStatus.textContent = msg;", "fxFalado = 's' + sig; fxStatus.textContent = ''; fxStatus.textContent = msg; try { speechSynthesis.speak(new SpeechSynthesisUtterance(msg)); } catch (e) {}")], 'faixa'),
    ('o alarme pedido sem começo conhecido na frente (desdeMs null como 0 em vez do fim)', 'capitao-app.js',
     [("var dx = x.desdeMs === null ? Infinity : x.desdeMs, dy = y.desdeMs === null ? Infinity : y.desdeMs;\n    return fxPeso", "var dx = x.desdeMs === null ? 0 : x.desdeMs, dy = y.desdeMs === null ? 0 : y.desdeMs;\n    return fxPeso")], 'faixa'),
    ('a faixa não passa a marca da janela de emergência ao cérebro (a SOG sai com número)', 'capitao-app.js',
     [("B.alarmesPedidosAtivos(undefined, { emergencia: emergenciaValendo() })", "B.alarmesPedidosAtivos()")], 'emerg'),
    ('a marca não avisa a faixa (sem o evento capitao-emergencia)', 'capitao-app.js',
     [("'capitao-sessao', 'capitao-emergencia'].forEach", "'capitao-sessao'].forEach")], 'emerg'),
    ('a região educada guarda o texto de antes da janela (com a SOG)', 'capitao-app.js',
     [("      if (fxStatus) fxStatus.textContent = '';\n      if (fxAlerta) fxAlerta.textContent = '';\n", "")], 'emerg'),
    ('a janela sem teto de 15 min', 'capitao-app.js',
     [("Math.min(ate, t + JANELA)", "ate")], 'emerg'),
    ('a janela que não vence pelo relógio', 'capitao-app.js',
     [("function valendo() { return le() > Date.now(); }", "function valendo() { return le() > 0; }")], 'emerg'),
    ('a Main dando setState a cada tique, sem comparar o texto da faixa', 'Main.dc.html',
     [("if (k !== this._leitK) this.setState({ vivo: k });", "this.setState({ vivo: k });")], 'gating'),
    ('a H2 dando setState a cada tique, sem comparar o LED', 'H2-Home-Mobile.dc.html',
     [("if (k !== this._vivoK) this.setState({ vivo: k });", "this.setState({ vivo: k });")], 'gating'),
    # P4C: a Ponte e o mapa de sensores só dão setState quando o texto exibido muda
    ('a A1 dando setState a cada tique, sem comparar o texto', 'A1-Ponte-Web.dc.html',
     [("    if (k === this._k) return;\n    this._k = k; this._din = d; this._fresco = true;", "    this._k = k; this._din = d; this._fresco = true;")], 'gating'),
    ('a A2 dando setState a cada tique, sem comparar o texto', 'A2-Ponte-Mobile.dc.html',
     [("    if (k === this._k) return;\n    this._k = k; this._din = d; this._fresco = true;", "    this._k = k; this._din = d; this._fresco = true;")], 'gating'),
    ('a A4 dando setState a cada tique, sem comparar o texto', 'A4-Sensores-Web.dc.html',
     [("    if (k === this._k) return;\n    this._k = k; this._din = d; this._fresco = true;", "    this._k = k; this._din = d; this._fresco = true;")], 'gating'),
    ('a A5 dando setState a cada tique, sem comparar o texto', 'A5-Sensores-Mobile.dc.html',
     [("    if (k === this._k) return;\n    this._k = k; this._din = d; this._fresco = true;", "    this._k = k; this._din = d; this._fresco = true;")], 'gating'),
    # P4D: a Gestão e os Sistemas só dão setState quando o texto exibido muda
    ('a B1 dando setState a cada tique, sem comparar o texto', 'B1-Carta-Web.dc.html',
     [("    if (k === this._k) return;\n    this._k = k; this._din = d; this._fresco = true;", "    this._k = k; this._din = d; this._fresco = true;")], 'gating'),
    ('a B2 dando setState a cada tique, sem comparar o texto', 'B2-Carta-Mobile.dc.html',
     [("    if (k === this._k) return;\n    this._k = k; this._din = d; this._fresco = true;", "    this._k = k; this._din = d; this._fresco = true;")], 'gating'),
    # P4F: o Modo navegação só dá setState quando o texto exibido muda (E1 e E2 são CRLF: o trecho é de uma linha só, que o corpo servido casa)
    ('a E1 dando setState a cada tique, sem comparar o texto', 'E1-Navegando-Gatilhos.dc.html',
     [("if (!forca && k === this._k) return;", "")], 'gating'),
    ('a E2 dando setState a cada tique, sem comparar a leitura de agora', 'E2-Navegando-Sintoma.dc.html',
     [("if (k === this._refK) return;", "")], 'gating'),
    # P4H: o estado a bordo dos FAQs (F2 a F5) só dá setState quando o texto exibido muda (cada mutante na tela que o gating mede)
    ('a F2 dando setState a cada tique, sem comparar o texto', 'F2-FAQ-Estabilizador-Web.dc.html',
     [("if (k !== this._bk) { this._bk = k; this.setState({ vivo: k }); }", "{ this._bk = k; this.setState({ vivo: k }); }")], 'gating'),
    ('a F3 dando setState a cada tique, sem comparar o texto', 'F3-FAQ-Eletronicos.dc.html',
     [("if (k !== this._bk) { this._bk = k; this.setState({ vivo: k }); }", "{ this._bk = k; this.setState({ vivo: k }); }")], 'gating'),
    ('a F4 dando setState a cada tique, sem comparar o texto', 'F4-FAQ-Gerador-Web.dc.html',
     [("if (k !== this._bk) { this._bk = k; this.setState({ vivo: k }); }", "{ this._bk = k; this.setState({ vivo: k }); }")], 'gating'),
    ('a F5 dando setState a cada tique, sem comparar o texto', 'F5-FAQ-Climatizacao.dc.html',
     [("if (k !== this._bk) { this._bk = k; this.setState({ vivo: k }); }", "{ this._bk = k; this.setState({ vivo: k }); }")], 'gating'),
    # P4G: a Home só dá setState na virada do dia quando o prazo exibido muda (Main e H2 são LF)
    ('a Main dando setState a cada virada do dia, sem comparar o texto exibido', 'Main.dc.html',
     [("if (k !== this._leitK) this.setState({ vivo: k });", "this.setState({ vivo: k });")], 'home_rebase'),
    ('a Main sem ouvir a virada do dia (só a telemetria)', 'Main.dc.html',
     [("['capitao-telemetria', 'capitao-rebase'].forEach((ev) => window.addEventListener(ev, this._onTele));", "['capitao-telemetria'].forEach((ev) => window.addEventListener(ev, this._onTele));")], 'home_rebase'),
    ('a H2 dando setState a cada virada do dia, sem comparar os cartões', 'H2-Home-Mobile.dc.html',
     [("if (k !== this._cartK) this.setState({ cart: k });", "this.setState({ cart: k });")], 'home_rebase'),
    ('a H2 sem ouvir a virada do dia', 'H2-Home-Mobile.dc.html',
     [("    window.addEventListener('capitao-rebase', this._onReb);\n", "")], 'home_rebase'),
    ('a Main redesenhando com a aba escondida (sem o document.hidden)', 'Main.dc.html',
     [("this._onTele = () => { if (document.hidden) return; const k = JSON.stringify(this.leitura());", "this._onTele = () => { const k = JSON.stringify(this.leitura());")], 'home_rebase'),
    ('a H2 redesenhando a virada do dia com a aba escondida (sem o document.hidden)', 'H2-Home-Mobile.dc.html',
     [("this._onReb = () => { if (document.hidden) return; const k = this.chaveCartoes();", "this._onReb = () => { const k = this.chaveCartoes();")], 'home_rebase'),
]


def mutantes_arq(b):
    global MUT_ARQ, CAPTURA
    print('Mutantes da moldura e das telas (P2B): cada defeito plantado tem de ser acusado pelo teste de desempenho')
    for nome, arq, trocas, qual in MUTANTES_ARQ:
        src = le(arq)
        faltam = [x for x, _ in trocas if src.count(x) != 1]
        if faltam:
            ok('mutante «%s»: o trecho está uma vez no %s' % (nome, arq), False, faltam)
            continue
        MUT_ARQ, CAPTURA, caiu = {arq: trocas}, [], ''
        sai = sys.stdout
        try:
            sys.stdout = open(os.devnull, 'w')
            try:
                if qual == 'moldura':
                    for n_, r_ in moldura_lote(b, [A2], segundos=5).items():
                        confere_moldura(n_, A2[1], r_, segundos=5)
                elif qual == 'quadro':
                    moldura_quadro(b, fixos=('60',))
                elif qual == 'faixa':
                    faixa_global(b)
                elif qual == 'emerg':
                    faixa_emergencia(b)
                elif qual == 'home_rebase':
                    home_rebase(b, telas=[t_ for t_ in HOME_REBASE if t_[0].split('-')[0] == arq.split('-')[0].split('.')[0]])
                else:
                    gating(b, telas=[t_ for t_ in GATING_TELAS if t_[0].split('-')[0] == arq.split('-')[0].split('.')[0]], livre_ms=4000)
            except Exception as e:   # aqui um erro do próprio teste NÃO conta como acusação (esconderia um erro de código do teste): reprova
                caiu = 'o teste caiu: %s' % str(e).splitlines()[0][:160]
        finally:
            sys.stdout.close()
            sys.stdout = sai
            achados, MUT_ARQ, CAPTURA = CAPTURA, None, None
        ok('mutante: %s — acusado (%d conferência(s) falham)' % (nome, len(achados)), len(achados) > 0 and not caiu, caiu or achados)


def mutantes(b):
    global MUT, CAPTURA, TOL_TRIG
    print('Mutantes do motor: cada defeito plantado tem de ser acusado pelo teste que cuida dele (paridade sempre exata, sem a tolerância do CAPITAO_TOL_TRIG)')
    src = le('capitao-replay.js')
    tol_antes, TOL_TRIG = TOL_TRIG, False   # a tolerância opcional nunca esconde um defeito plantado
    for nome, trocas, teste in MUTANTES:
        faltam = [t for t, _ in trocas if src.count(t) != 1]
        if faltam:
            ok('mutante «%s»: o trecho está uma vez no capitao-replay.js' % nome, False, faltam)
            continue
        MUT, CAPTURA = trocas, []
        sai = sys.stdout
        try:
            sys.stdout = open(os.devnull, 'w')
            try:
                teste(b)
            except Exception as e:   # o defeito derrubou o próprio teste: também é uma forma de acusar
                CAPTURA.append('o teste caiu: %s' % str(e).splitlines()[0][:120])
        finally:
            sys.stdout.close()
            sys.stdout = sai
            achados, MUT, CAPTURA = CAPTURA, None, None
        ok('mutante: %s — acusado (%d conferência(s) falham)' % (nome, len(achados)), len(achados) > 0, achados)
    TOL_TRIG = tol_antes


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=CANAL, headless=True)
        a_volta(browser)
        a_fase(browser)
        o_dia(browser)
        a_alarmes(browser)
        sincronia(browser)
        a_fixar(browser)
        eventos_ritmo(browser)
        eventos_pausa(browser)
        eventos_timer(browser)
        eventos_alertas(browser)
        eventos_virada(browser)
        eventos_virada_oculta(browser)
        isolamento(browser)
        isolamento_falha(browser)
        no_sos(browser)
        modo_real_inicial(browser)
        modo_real_flag(browser)
        historico(browser)
        faixas_e_resumo(browser)
        nunca_lanca(browser)
        d_parcial(browser)
        desempenho(browser)
        moldura(browser)
        moldura_estados(browser)
        moldura_quadro(browser)
        faixa_global(browser)
        faixa_emergencia(browser)
        gating(browser)
        home_rebase(browser)
        codigo()
        codigo_faixa()
        telas(browser)
        a_alertas_volta(browser)
        a_alertas_varios(browser)
        a_alertas_uma_vez(browser)
        a_alertas_ms(browser)
        a_alertas_eventos(browser)
        a_alertas_sem_efeito(browser)
        a_alertas_real(browser)
        a_alertas_replay_mentiroso(browser)
        a_alertas_nunca_lanca(browser)
        a_alertas_sos(browser)
        a_alertas_telas(browser)
        codigo_alertas()
        mutantes(browser)
        mutantes_arq(browser)
        mutantes_alertas(browser)
        browser.close()
    print('%d conferências · %d falhas' % (total, falhas))
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
