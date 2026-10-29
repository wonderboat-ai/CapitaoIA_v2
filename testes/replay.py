# -*- coding: utf-8 -*-
"""Capitão IA — teste do motor da reprodução (capitao-replay.js; CONTRATO-DADOS §1.15–§1.17, §1.22–§1.24, §3, §6.5; PROMPT Fase 2). Sem cota.

O motor é a função pura `em(ms)` do instante absoluto (laço de 150 s + rota + contadores + alarmes), mais o relógio (`agora`, `fixar`), o tique de
1 s (eventos) e as séries do histórico. Aqui, no Chromium (Edge) com o site servido em 127.0.0.1:8765 e a rede cortada (o contexto aborta tudo o que
não for 127.0.0.1 ou unpkg.com; o unpkg só serve o React das telas de verdade):

- t de 0 a 149 (`quadro(t)`): todos os campos finitos, sem -0, com o número de casas do D.campos, e o quadro ⇔ catálogo nos dois sentidos;
- paridade Python × JS (§6.5): `quadro(t)` t = 0…149, uma amostra do dia, as 1.152 pontas das 576 emendas e as pontas da âncora, campo a campo
  contra `confere.em()` (o port que o gerador usa), recalculado aqui em Python a partir do D.replay; os 86.400 segundos do dia conferem fora
  deste teste (dev). Seno, cosseno, asen e atan2 do V8 e do CPython podem diferir de 1 ulp: só nos campos derivados deles (TRIG) aceita-se 1 unidade
  da última casa, e o teste conta quantos usaram a tolerância;
- emenda: o laço (|v(149) − v(0)| ≤ o maior passo de 1 s da volta, por campo do laço) e, no dia inteiro, as 575 emendas de 150 s fora da âncora
  (segundos consecutivos, `em(N·150 − 1 s)` × `em(N·150)`): nenhum campo numérico passa do maior passo de 1 s do dia, e destino, próximo ponto e ETA
  não mudam; a única descontinuidade é a virada das 07:00 (contadores, tanques e a rota que recomeça), com posição e COG contínuos;
- contadores sem voltar (`D.campos[c].sentido`), fora do par A − 1 s × A, que tem de saltar;
- alarme só na janela do gerador (99–116 s), sempre AVISO, com `desde` da janela; `alarmes()`, `janela()`; o cenário `aviso` nunca devolve
  crítico (com os limites adulterados) e o `alarme-critico` devolve;
- sincronia entre duas abas e entre dois aparelhos (o mesmo segundo dá o mesmo quadro) e a fase que continua pelo relógio ao trocar de página;
- `fixar('60')` = 12:01:00 (voltas_fixo), `fixar(60)`, '60@K', `fixar(null)`, `#replay=`, o localStorage `capitao.replay.fixo` e o `capitao.replay.sobre`
  (só com o instante fixado, só no instante fixado); o rodapé refaz os prazos para o dia do instante fixado (entre 00:00 e 07:00, "ontem 12:01");
- eventos: `capitao-telemetria` a cada 1 s alinhado ao segundo, pausado com document.hidden e com tique imediato na volta à frente;
  `capitao-alerta` (inicio, nivel, fim); `capitao-rebase` na virada das 07:00 e da meia-noite (com o Date congelado); um timer só por página;
- isolamento: o replay não é o `CapitaoTelemetria`; `atual()` e `fonte()` (coletor real recente × replay × null); o D.snapshot nem um byte diferente;
  a âncora é a `CapitaoAgora.ancora` (a mesma, sem cópia); falha → null e o instante() cai no snapshot sem mutá-lo;
- S1/S2 (e uma rota /SOS-): sem CapitaoReplay, `CapitaoAgora.instante()` null, nenhum tique, nenhuma leitura de D.simulacao nem de D.replay;
- modo real inerte (`simulacao = false` no fim do capitao-dados.js, e a flag mudando com a página aberta): nada anda, `em()` null, nenhum evento;
- histórico: `serie()` das cinco janelas sem NaN, o último ponto = o quadro, o serrote do diesel = as linhas de abastecimento, a curva do ano do
  ar e da água (30 D e 1 A não saem retos), a trava de máx/mín do dia; `porFaixa()`, `resumo()` (≤ 300 letras, sem coordenadas, sem os termos do §3);
- nunca lança erro (argumentos absurdos, D quebrado, localStorage que lança); desempenho do `em()`; o código (sem lookbehind, sem snapshot, sem
  `window.CapitaoTelemetria =`); as 34 telas com o <script> no lugar certo, S1/S2 sem ele, e o CORE do sw.js.

Fica para as Fases 3 a 7 (depende do cérebro, das telas ou da IA, que a Fase 2 não toca):
- o mesmo texto de rpm, SOG e diesel na Main, A1, E1, HUD, `answer('telemetria')` e `## Navegação agora` (um instante só, `fixar('60')`);
- a ficha, a tendência de 30 s (`instante().tend`, que a Fase 3 monta), a trava do ar e da água nas telas (A1 × Main) e as séries nos gráficos;
- o grep final (SEM DADOS, SEM LEITURA, DEMO e demais rótulos nas respostas e nas telas), o `sim: true` nas linhas gravadas e o modo real do cérebro e da IA;
- o desempenho da moldura (o `<capitao-theme-toggle>` e o avatar não recriados, `fit()` ≤ 2 vezes, nenhuma long task > 50 ms em 10 s): é da P2B;
- a faixa de alerta, a C3 viva, a E1 NAVEGANDO × FUNDEADO e as rotas de alarmes do cérebro (P2C, Fases 3 e 4).

Uso (com o site servido em http://127.0.0.1:8765, na raiz do repositório):
    python -X utf8 testes/replay.py
Navegador: Edge instalado (Playwright com channel="msedge"); troque CANAL para "chrome" se preferir.
"""
import json
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


def compara(js, py, nome_ctx):
    """Diferenças entre o quadro do JS e o do Python: (exatas, dentro da tolerância de 1 unidade da última casa nos derivados trigonométricos)."""
    exatas, tol = [], []
    for k in set(py) | set(js):
        a, b = py.get(k, '<falta>'), js.get(k, '<falta>')
        if a == b:
            continue
        if k in TRIG and isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and abs(a - b) <= 1.0001 * 10 ** (-C.casas_de(D['campos'], k)):
            tol.append((nome_ctx, k, a, b))
        else:
            exatas.append((nome_ctx, k, a, b))
    return exatas, tol


def a_volta(b):
    print('A volta de 150 s: campos finitos e paridade Python × JS (CONTRATO §6.5)')
    pg = abre(b)
    r = pg.evaluate(VOLTA_JS)
    ok('quadro(t), t de 0 a 149: 150 quadros, todos os campos finitos, sem -0, sem texto vazio', len(r['q']) == 150 and r['problemas'] == [], r['problemas'][:5])
    ok('cada número tem as casas do D.campos (o valor como a tela mostra)', r['casasOk'] == [], r['casasOk'][:5])
    ok('quadro ⇔ catálogo (D.campos) nos dois sentidos, e o simulado: true não está no em()', r['soNoQuadro'] == [] and r['soNoCatalogo'] == [] and r['tipos'] == {'alarmes': True, 'simulado': False},
       (r['soNoQuadro'], r['soNoCatalogo'], r['tipos']))
    anc_s = r['anc'] // 1000
    exatas, tol = [], []
    for t in range(VOLTA):
        e, a = compara(r['q'][t], C.em(P, r['ini'] + t, ancora_s=anc_s), 't=%d' % t)
        exatas += e
        tol += a
    ok('paridade: quadro(t) = confere.em() campo a campo, t = 0…149 (%d usaram a tolerância de 1 unidade nos derivados trigonométricos)' % len(tol), exatas == [], exatas[:4])
    # uma amostra do dia, as pontas das 576 emendas e as da âncora (segundos absolutos do dia de bordo)
    random.seed(7)
    segs = sorted(set(random.sample(range(150, 86400), 1200) + [n * 150 + d for n in range(1, 576) for d in (-1, 0)] + [0, 1, 86398, 86399]))
    js = pg.evaluate("""(segs) => { const R = window.CapitaoReplay, anc = window.CapitaoAgora.ancora(Date.now()), o = {};
      segs.forEach((s) => { o[s] = R.em(anc + s * 1000); }); return { anc, o }; }""", segs)
    exatas, tol = [], []
    for s in segs:
        e, a = compara(js['o'][str(s)], C.em(P, s, ancora_s=js['anc'] // 1000), 'seg=%d' % s)
        exatas += e
        tol += a
    ok('paridade: %d segundos do dia (amostra, as 1.150 pontas das emendas e as pontas da âncora) iguais ao confere.em() (%d na tolerância)' % (len(segs), len(tol)),
       exatas == [], exatas[:4])
    ok('timestamp_utc = o instante pedido (o segundo inteiro, ISO com Z)', js['o']['0']['timestamp_utc'] == datetime.fromtimestamp(js['anc'] // 1000, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
       js['o']['0']['timestamp_utc'])
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
  o.j10 = R.janela('arref_be', base + 10000); o.j99 = R.janela('arref_be', base + 99000); o.j98 = R.janela('arref_be', base + 98000); o.nada = R.janela('nao_existe', base);
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
    ok('janela() antes da janela da volta (t = 10 e 98) devolve a da volta anterior; id que não existe dá null',
       r['j10'] == {'ativo': False, 'desde': base - 150000 + 99000, 'ate': base - 150000 + 117000} and r['j98']['ativo'] is False and r['j98']['desde'] == base - 150000 + 99000
       and r['nada'] is None, (r['j10'], r['j98'], r['nada']))
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
  const le = () => ({ fixo: R.fixo(), agora: R.agora(), hora: A.fmt.hora(R.agora(), true), t: R.t(), fase: R.fase().nome, ls: localStorage.getItem('capitao.replay.fixo'),
                      relogio: A.relogio.ms, q: R.quadro(), inst: (() => { const i = A.instante(); return { fonte: i.fonte, hora: i.hora, seg: i.seg, rpm: A.fmt.campo(i.q, 'motor_bb_rpm') }; })() });
  window.__ev.length = 0;
  o.t60 = R.fixar('60'); o.s60 = le(); o.ev60 = window.__ev.map((e) => e.n);
  o.t60n = R.fixar(60); o.n60 = R.fixo();
  o.t60k = R.fixar('60@120'); o.k60 = R.fixo();
  o.t10 = R.fixar('60@10'); o.s10 = le();
  window.__ev.length = 0; o.t105 = R.fixar('105'); o.s105 = le(); o.ev105 = window.__ev.map((e) => e.n);
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
    print('O arquivo: sem lookbehind, sem snapshot, sem window.CapitaoTelemetria =; nas 34 telas e no CORE do sw.js')
    src = le('capitao-replay.js')
    codigo_ = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
    codigo_ = re.sub(r'(?m)^\s*//.*$|\s//\s.*$', '', codigo_)
    ok('sem lookbehind (?<…) (Safari antigo) e sem \\w para palavra em português', '(?<' not in src and '\\w' not in src)
    ok('o código (fora dos comentários) não menciona snapshot: nunca o lê, devolve nem muta', not re.search(r'snapshot', codigo_, re.I), re.findall(r'.{20}snapshot.{20}', codigo_, re.I)[:2])
    ok('nunca se registra como CapitaoTelemetria', not re.search(r'window\s*\.\s*CapitaoTelemetria\s*=|window\[\s*[\'"]CapitaoTelemetria', codigo_))
    ok('não escreve fora das duas chaves do replay (capitao.replay.fixo e .sobre) e só o fixo é gravado', set(re.findall(r"'(capitao\.[a-z.]+)'", codigo_)) == {'capitao.replay.fixo', 'capitao.replay.sobre'}
       and len(re.findall(r'setItem', codigo_)) == 1, set(re.findall(r"'(capitao\.[a-z.]+)'", codigo_)))
    ok('sem VERSAO própria (acompanha o capitao-dados.js)', 'VERSAO' not in codigo_)
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


# ——— 12. as telas de verdade ———
def telas(b):
    print('Telas de verdade (com sessão): o motor carrega, anda e não dá erro de script')
    for nome, vp in (('Main', {'width': 1440, 'height': 900}), ('A1-Ponte-Web', {'width': 1440, 'height': 900}), ('E1-Navegando-Gatilhos', {'width': 1440, 'height': 900}),
                     ('H2-Home-Mobile', {'width': 390, 'height': 844}), ('C3-Leme-Alerta', {'width': 390, 'height': 844}), ('Manual-Capitao-IA', {'width': 1440, 'height': 900})):
        pg = abre(b, caminho='/%s.dc.html' % nome, sessao=True, viewport=vp, espera='() => window.CapitaoReplay')
        pg.wait_for_timeout(1500)
        r = pg.evaluate("() => ({ obj: typeof window.CapitaoReplay, ativo: window.CapitaoReplay.ativo(), inst: window.CapitaoAgora.instante().fonte, n: window.__conta('capitao-telemetria'), t: window.CapitaoTelemetria ? window.CapitaoTelemetria.fonte() : 'sem' })")
        ok('%s: CapitaoReplay existe e anda (ativo, instante() do replay, %d tiques em 1,5 s%s)' % (nome, r['n'], '' if r['t'] == 'sem' else ', CapitaoTelemetria.fonte() = ' + r['t']),
           r['obj'] == 'object' and r['ativo'] and r['inst'] == 'replay' and r['n'] >= 1 and r['t'] in ('sem', 'replay'), r)
        ok('%s: sem erro de script' % nome, not pg.erros, pg.erros)
        fecha(pg)


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
]


def mutantes(b):
    global MUT, CAPTURA
    print('Mutantes do motor: cada defeito plantado tem de ser acusado pelo teste que cuida dele')
    src = le('capitao-replay.js')
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


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=CANAL, headless=True)
        a_volta(browser)
        o_dia(browser)
        a_alarmes(browser)
        sincronia(browser)
        a_fixar(browser)
        eventos_ritmo(browser)
        eventos_pausa(browser)
        eventos_timer(browser)
        eventos_alertas(browser)
        eventos_virada(browser)
        isolamento(browser)
        isolamento_falha(browser)
        no_sos(browser)
        modo_real_inicial(browser)
        modo_real_flag(browser)
        historico(browser)
        faixas_e_resumo(browser)
        nunca_lanca(browser)
        desempenho(browser)
        codigo()
        telas(browser)
        mutantes(browser)
        browser.close()
    print('%d conferências · %d falhas' % (total, falhas))
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
