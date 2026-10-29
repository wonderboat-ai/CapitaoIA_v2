# -*- coding: utf-8 -*-
"""Capitão IA — conferência da Fase 1b: o SOS (S1 e S2) fora da simulação (PROMPT §2.1, §2.2; CONTRATO-DADOS §1.3, §6.2 "1b").

Sem login, com o localStorage vazio e também sem rede (--offline na rodada do verificar.py; aqui, o contexto com a rede cortada depois
da instalação do service worker). Em S1 (computador) e S2 (celular):

  * o innerText e os atributos (title, aria-label, alt, href) da tela fechada, com o roteiro MAYDAY aberto e com cada cartão aberto
    não casam: \\b\\d{9}\\b, coordenada (a R_COORD do gerador), os valores de snapshot.local e snapshot.estado, "SNAPSHOT", SOG/PROA
    com número, o registro, a base e o resto do dado gerado da embarcação, fabricante e modelo de equipamento, nem "SEM DADOS";
    não há link tel: (o telefone só existe se o proprietário o cadastrar no aparelho);
  * a tela diz "POSIÇÃO: LEIA NO PLOTTER" sem GPS; com a permissão e o GPS do aparelho, a posição em graus e minutos com ± precisão e
    hora; com precisão pior que 100 m, "PRECISÃO BAIXA" e nenhuma coordenada; o toque sem permissão não inventa posição;
  * F04: abrir a tela (e recarregar) não grava no diário; MAYDAY, MOB ou ligar grava 1 linha, 1× a cada 10 min, dizendo o que foi
    tocado; Seafire e EPIRB não gravam; a linha não leva `sim`, não leva SOG/rumo/ETA nem a posição do snapshot, da rota ou do replay
    (sem GPS contém "plotter" e nenhuma coordenada; com GPS, só a coordenada do aparelho);
  * nenhuma leitura de D.simulacao, D.snapshot, D.replay, D.rota, D.campos, D.equipamentos, D.guias nem de
    D.embarcacao.{registro, mmsi, base, modelo, fabricante} (um Proxy conta as leituras desde a carga do capitao-dados.js, também as do
    rodapé e as do cérebro que o SOS carrega); CapitaoTelemetria e CapitaoReplay não existem; CapitaoAgora.instante() é null;
  * o cérebro carregado no SOS tem o snapshot vazio (ficha e respostas sem o snapshot) e o D.snapshot fica igual ao do arquivo gerado
    (o rebase nunca o toca).

Uso (com o site servido em http://127.0.0.1:8765):
    python -m http.server 8765 --bind 127.0.0.1      (na raiz do repositório, em outro terminal)
    python testes/sos.py [--so-offline | --sem-offline] [-v]
Navegador: Edge instalado (Playwright com channel="msedge"); troque CANAL para "chrome" se preferir.
"""
import json
import os
import re
import sys
from playwright.sync_api import sync_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'ferramentas', 'demo'))
sys.path.insert(0, AQUI)
import confere  # noqa: E402  (barco_sos, R_COORD: as regras do gerador, uma só)
from verificar import TEXTOS_SOS, achados_texto_sos  # noqa: E402  (a leitura do texto e dos atributos: fechada, roteiro aberto, cada cartão aberto; e as regras)

BASE = 'http://127.0.0.1:8765/'
CANAL = 'msedge'
TELAS = (('S1-SOS-Web', 1440, 900, 'web · SOS'), ('S2-SOS-Mobile', 390, 844, 'app · SOS'))
CHAVE_DIARIO, CHAVE_SOS, CHAVE_EQUIPE = 'capitao.diario.v1', 'capitao.sos.v1', 'capitao.equipe.v1'
# O ponto do teste (Florianópolis): longe da posição de referência, do snapshot e da rota, para provar que a coordenada vem do aparelho.
GPS_LAT, GPS_LON = -27.5954, -48.5480
GPS_TXT = "27°35,72'S 048°32,88'W"   # graus e minutos, o formato que o semCoord reconhece (26°59,58'S 048°36,84'W)
FONE = '(47) 0000-0000'             # fictício: só o formato; o app guarda o telefone no aparelho (Equipe)
LEITURAS_PROIBIDAS = ['simulacao', 'snapshot', 'replay', 'rota', 'campos', 'equipamentos', 'guias']
EMBARCACAO_PROIBIDA = ['registro', 'mmsi', 'base', 'modelo', 'fabricante']

# Conta as leituras dos campos que o SOS não pode ler, desde a carga do capitao-dados.js (o set de window.CapitaoDados troca o objeto por um
# Proxy transparente). Cada leitura guarda o campo e de onde veio (os dois primeiros arquivos da pilha de chamadas).
CONTA_LEITURAS = """(() => {
  const PROIBIDAS = %s, EMB = %s;
  window.__leituras = [];
  const quem = () => (new Error().stack || '').split('\\n').slice(3, 5).map((l) => (l.match(/([^\\/ (]+\\.(?:js|html)):\\d+/) || [0, '?'])[1]).join(' < ');
  let real;
  Object.defineProperty(window, 'CapitaoDados', { configurable: true, get() { return real; }, set(v) {
    window.__dadosCru = v;   // a leitura do próprio teste (verificar.TEXTOS_SOS) vai por aqui e não conta como a do SOS
    real = new Proxy(v, { get(t, k, r) {
      if (typeof k === 'string' && PROIBIDAS.indexOf(k) >= 0) window.__leituras.push('D.' + k + ' ← ' + quem());
      const x = Reflect.get(t, k, r);
      if (k === 'embarcacao' && x && typeof x === 'object') return new Proxy(x, { get(t2, k2, r2) {
        if (typeof k2 === 'string' && EMB.indexOf(k2) >= 0) window.__leituras.push('D.embarcacao.' + k2 + ' ← ' + quem());
        return Reflect.get(t2, k2, r2);
      } });
      return x;
    } });
  } });
  // toque no tel: não navega (o Chromium sem protocolo para tel: ficaria esperando)
  document.addEventListener('click', (e) => { const a = e.target && e.target.closest && e.target.closest('a[href^="tel:"]'); if (a) e.preventDefault(); }, true);
})();""" % (json.dumps(LEITURAS_PROIBIDAS), json.dumps(EMBARCACAO_PROIBIDA))

PRONTA = "() => !!(document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0 && window.CapitaoBrain)"
# o D.snapshot do arquivo gerado, sem o rodapé (que roda depois da atribuição), contra o da página: o rebase nunca o toca
SNAPSHOT_IGUAL = """async () => {
  const antes = (window.__leituras || []).slice();   // a leitura do teste não conta como a do SOS
  const txt = await (await fetch('./capitao-dados.js', { cache: 'no-store' })).text(), corte = txt.indexOf('/* CapitaoAgora');
  const w = {}; new Function('window', corte > 0 ? txt.slice(0, corte) : txt)(w);
  const igual = JSON.stringify(w.CapitaoDados.snapshot) === JSON.stringify(window.CapitaoDados.snapshot);
  window.__leituras.splice(0, window.__leituras.length, ...antes);
  return { corte: corte > 0, igual: igual };
}"""
ESTADO = """() => ({
  diario: JSON.parse(localStorage.getItem('%s') || '[]'), sos: sessionStorage.getItem('%s'), url: location.pathname,
  telemetria: typeof window.CapitaoTelemetria, replay: typeof window.CapitaoReplay,
  instante: window.CapitaoAgora && window.CapitaoAgora.instante ? (window.CapitaoAgora.instante() === null ? 'null' : 'quadro') : 'sem CapitaoAgora',
  leituras: window.__leituras || [], online: navigator.onLine, texto: document.body.innerText, lenda: !!document.querySelector('[role="dialog"], #dc-root'),
  tel: [...document.querySelectorAll('a[href^="tel:"]')].map((a) => a.getAttribute('href')) })""" % (CHAVE_DIARIO, CHAVE_SOS)
# o cérebro do SOS (CapitaoBrain com o snapshot vazio): a ficha e as respostas não trazem o snapshot nem o MMSI gerado
CEREBRO = """() => { const antes = (window.__leituras || []).slice(), B = window.CapitaoBrain, D = window.CapitaoDados, S = D.snapshot || {}, tira = (a) => a.text + '\\n' + (a.src || '');
  const f = B.ficha('app'), r = ['telemetria', 'posição agora', 'roteiro do canal 16', 'emergência', 'onde fica o EPIRB?', 'onde fica o seafire'].map((q) => [q, tira(B.answer(q, { platform: 'app', commit: false }))]);
  window.__leituras.splice(0, window.__leituras.length, ...antes);   // a leitura do teste não conta como a do SOS
  return { ficha: f, respostas: r, snap: { local: S.local, estado: S.estado, quando: S.quando, gps: S.gps && S.gps.texto } }; }"""

falhas = 0
total = 0
VERBOSO = '-v' in sys.argv


def confere_(nome, cond, extra=''):
    global falhas, total
    total += 1
    if not cond:
        falhas += 1
        print('FALHA', nome, extra if isinstance(extra, str) else json.dumps(extra, ensure_ascii=False)[:400])
    elif VERBOSO:
        print('ok   ', nome)


def abre(b, tela, largura, altura, geo=None, offline_depois=False, equipe=None):
    """Contexto novo (localStorage vazio, sem sessão de login) com o contador de leituras; devolve (contexto, página, erros)."""
    opcoes = {'viewport': {'width': largura, 'height': altura}}
    if geo:
        opcoes.update(geolocation=geo, permissions=['geolocation'])
    ctx = b.new_context(**opcoes)
    ctx.add_init_script(CONTA_LEITURAS)
    if equipe:
        ctx.add_init_script("try { if (!localStorage.getItem('%s')) localStorage.setItem('%s', %s); } catch (e) {}" % (CHAVE_EQUIPE, CHAVE_EQUIPE, json.dumps(json.dumps(equipe))))
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append(str(e)[:200]))
    pg.goto(BASE + tela + '.dc.html', wait_until='load', timeout=30000)
    pg.wait_for_function(PRONTA, timeout=20000)
    pg.wait_for_timeout(500)
    return ctx, pg, erros


def mayday(pg):
    pg.locator('button[aria-pressed]:not([aria-label])', has_text='MAYDAY').first.click()


def cartao(pg, i):
    pg.locator('button[aria-expanded]').nth(i).click()


def so_a_coordenada_do_aparelho(texto):
    """Casamentos da R_COORD que não são a coordenada do aparelho (GPS_TXT, escrita como o app escreve)."""
    return [m.group(0) for m in confere.R_COORD.finditer(texto.replace(GPS_TXT, ' '))]


def varredura(pg, tela, rotulo, E, equipamentos, snap, com_gps=False):
    """Texto e atributos de S1/S2 (fechada, roteiro aberto, cada cartão aberto): nada do dado gerado além do nome e nada de simulação.
    As regras são as do verificar.py (achados_texto_sos), a mesma conferência da matriz de telas e do --offline."""
    r = pg.evaluate(TEXTOS_SOS)
    txt = r['texto']
    n = '%s · %s' % (tela, rotulo)
    confere_(n + ': roteiro e os 4 cartões abriram e a tela voltou ao estado inicial', r['roteiro'] and r['cartoes'] == 4 and r['abertos'] == 4 and r['inicial'], (r['roteiro'], r['cartoes'], r['abertos'], r['inicial']))
    for regra, achados in achados_texto_sos(txt, E, equipamentos, snap, coord_aparelho=GPS_TXT if com_gps else None).items():
        confere_(n + (': nenhum(a) ' + regra if not (com_gps and regra == 'coordenada') else ': só a coordenada do aparelho'), not achados, achados[:3])
    confere_(n + ': diz que o MMSI é o do rádio de bordo, o procedimento padrão e "conte agora"',
             'MMSI do rádio de bordo (etiqueta / Licença de Estação)' in txt and 'PROCEDIMENTO PADRÃO — CONFIRMAR COM O PROTOCOLO DE BORDO' in txt.upper() and 'PESSOAS A BORDO: conte agora' in txt)
    confere_(n + ': Seafire e EPIRB com o procedimento padrão e a etiqueta (nada de modelo, validade ou lugar)',
             'veja a etiqueta do equipamento' in txt and 'Incêndio · Seafire' in txt and 'EPIRB' in txt)
    return txt


def cenario_frio(b, tela, largura, altura, origem, E, equipamentos, snap, rotulo):
    ctx, pg, erros = abre(b, tela, largura, altura)
    est = pg.evaluate(ESTADO)
    n = '%s · %s' % (tela, rotulo)
    confere_(n + ': abre sem login (a URL continua a do SOS)', est['url'].endswith(tela + '.dc.html'), est['url'])
    if rotulo.startswith('offline'):
        confere_(n + ': navigator.onLine falso', est['online'] is False, est['online'])
    confere_(n + ': F04 abrir a tela não grava nada no diário nem marca o sessionStorage', est['diario'] == [] and est['sos'] is None, (est['diario'], est['sos']))
    confere_(n + ': a tela fechada diz que MAYDAY, MOB ou ligar grava no diário e a posição é "LEIA NO PLOTTER"',
             'MAYDAY, MOB ou ligar grava no diário' in est['texto'] and 'POSIÇÃO: LEIA NO PLOTTER' in est['texto'], est['texto'][:300])
    confere_(n + ': o botão MOSTRAR GPS DO CELULAR está à vista', 'MOSTRAR GPS DO CELULAR' in est['texto'])
    confere_(n + ': CapitaoTelemetria e CapitaoReplay não existem e CapitaoAgora.instante() é null', est['telemetria'] == 'undefined' and est['replay'] == 'undefined' and est['instante'] == 'null', (est['telemetria'], est['replay'], est['instante']))
    confere_(n + ': nenhum link tel: com o aparelho vazio', est['tel'] == [], est['tel'])
    if tela.startswith('S1'):
        confere_(n + ': o rodapé da S1 diz "POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER" e o cabeçalho não tem a base', 'POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER' in est['texto'] and 'BALNEÁRIO' not in est['texto'].upper(), est['texto'][:200])
    pg.reload(wait_until='load')
    pg.wait_for_function(PRONTA, timeout=20000)
    pg.wait_for_timeout(500)
    est2 = pg.evaluate(ESTADO)
    confere_(n + ': F04 recarregar a tela também não grava', est2['diario'] == [] and est2['sos'] is None, est2['diario'])
    sn = pg.evaluate(SNAPSHOT_IGUAL)
    confere_(n + ': o D.snapshot é o do arquivo gerado (o rebase não o toca)', sn['corte'] and sn['igual'], sn)
    ce = pg.evaluate(CEREBRO)
    tudo = ce['ficha'] + '\n' + '\n'.join(t for _, t in ce['respostas'])
    dado = [k for k, v in ce['snap'].items() if isinstance(v, str) and v.strip() and v in tudo]
    confere_(n + ': o cérebro carregado no SOS não traz o snapshot (S vazio) na ficha nem nas respostas', not dado, dado)
    confere_(n + ': ... nem o MMSI gerado nas respostas de emergência', not [q for q, t in ce['respostas'] if '710123456' in t and q != 'telemetria'], [q for q, t in ce['respostas'] if '710123456' in t])
    # a varredura abre o roteiro e os cartões: a linha do MAYDAY e a do MOB passam a existir, depois da conferência da abertura
    varredura(pg, tela, rotulo, E, equipamentos, snap)
    est3 = pg.evaluate(ESTADO)
    confere_(n + ': nenhuma leitura de D.simulacao, D.snapshot, D.replay, D.rota, D.campos, D.equipamentos, D.guias nem de embarcacao.{registro, mmsi, base, modelo, fabricante}', est3['leituras'] == [], est3['leituras'][:6])
    confere_(n + ': sem erro de script', not erros, erros)
    # a ação gravou 1 linha só (a varredura abriu o roteiro e o MOB): F04, sem `sim`, com "plotter" e sem coordenada
    d = est3['diario']
    confere_(n + ': F04 MAYDAY e MOB abertos na mesma conferência = 1 linha só (1× a cada 10 min)', len(d) == 1, d)
    if d:
        l = d[0]
        confere_(n + ': a linha do SOS: origem %r, Segurança, sem `sim`, "MAYDAY" ou "MOB", "plotter", sem coordenada, sem SOG/rumo/ETA' % origem,
                 l.get('src') == origem and l.get('sys') == 'Segurança' and 'sim' not in l and re.search(r'\((?:MAYDAY|MOB)\)', l.get('t', '')) and 'plotter' in l.get('t', '')
                 and not confere.R_COORD.search(l.get('t', '')) and not re.search(r'\b(?:SOG|COG|ETA|rumo|proa)\b', l.get('t', ''), re.I), l)
    ctx.close()


def cenario_acoes(b, tela, largura, altura, origem, rotulo):
    """F04 por ação, cada uma num contexto limpo: MAYDAY, MOB, ligar (1 linha dizendo o que foi tocado); Seafire e EPIRB, nenhuma; 10 min, sem duplicar."""
    n = '%s · %s' % (tela, rotulo)
    ctx, pg, erros = abre(b, tela, largura, altura)
    mayday(pg)
    pg.wait_for_function("() => JSON.parse(localStorage.getItem('%s') || '[]').length >= 1" % CHAVE_DIARIO, timeout=5000)
    est = pg.evaluate(ESTADO)
    confere_(n + ': F04 MAYDAY grava 1 linha dizendo "(MAYDAY)" e a tela diz que está gravado', len(est['diario']) == 1 and '(MAYDAY)' in est['diario'][0]['t'] and re.search(r'SOS \d\d:\d\d · gravado no diário de bordo', est['texto']), (est['diario'], est['texto'][:240]))
    cartao(pg, 1)
    pg.wait_for_timeout(500)
    confere_(n + ': F04 o MOB logo depois não duplica (a mesma janela de 10 min)', len(pg.evaluate(ESTADO)['diario']) == 1)
    pg.reload(wait_until='load')
    pg.wait_for_function(PRONTA, timeout=20000)
    pg.wait_for_timeout(500)
    est = pg.evaluate(ESTADO)
    confere_(n + ': F04 recarregar dentro dos 10 min mantém 1 linha e o aviso "gravado"', len(est['diario']) == 1 and re.search(r'SOS \d\d:\d\d · gravado no diário de bordo', est['texto']), (est['diario'], est['texto'][:200]))
    # passados os 10 min (a marca do sessionStorage velha), a próxima ação grava outra
    pg.evaluate("() => { const k = '%s', o = JSON.parse(sessionStorage.getItem(k)); o.em -= 11 * 60e3; sessionStorage.setItem(k, JSON.stringify(o)); }" % CHAVE_SOS)
    pg.reload(wait_until='load')
    pg.wait_for_function(PRONTA, timeout=20000)
    pg.wait_for_timeout(500)
    cartao(pg, 1)
    pg.wait_for_function("() => JSON.parse(localStorage.getItem('%s') || '[]').length >= 2" % CHAVE_DIARIO, timeout=5000)
    est = pg.evaluate(ESTADO)
    confere_(n + ': F04 depois de 10 min a ação grava outra linha (a nova diz "(MOB)", a mais nova primeiro)', len(est['diario']) == 2 and '(MOB)' in est['diario'][0]['t'] and '(MAYDAY)' in est['diario'][1]['t'], est['diario'])
    confere_(n + ': sem erro de script nas ações', not erros, erros)
    ctx.close()
    # MOB sozinho, num aparelho limpo
    ctx, pg, erros = abre(b, tela, largura, altura)
    cartao(pg, 1)
    pg.wait_for_function("() => JSON.parse(localStorage.getItem('%s') || '[]').length >= 1" % CHAVE_DIARIO, timeout=5000)
    d = pg.evaluate(ESTADO)['diario']
    confere_(n + ': F04 o MOB sozinho cria 1 linha dizendo "(MOB)"', len(d) == 1 and '(MOB)' in d[0]['t'] and d[0].get('src') == origem, d)
    ctx.close()
    # Seafire (cartão 2) e EPIRB (cartão 3): informam e não gravam
    ctx, pg, erros = abre(b, tela, largura, altura)
    cartao(pg, 2)
    pg.wait_for_timeout(500)
    t_sf = pg.evaluate('() => document.body.innerText')
    cartao(pg, 3)
    pg.wait_for_timeout(900)
    t_ep = pg.evaluate('() => document.body.innerText')
    est = pg.evaluate(ESTADO)
    confere_(n + ': F04 Seafire e EPIRB abertos não gravam nada (e mostram o procedimento padrão de protocolos)',
             est['diario'] == [] and est['sos'] is None and 'Não abra o acesso ao motor' in t_sf and 'Acione conforme a etiqueta do equipamento' in t_ep, (est['diario'], est['sos']))
    ctx.close()
    # ligar: com o telefone cadastrado no aparelho, o toque no tel: grava "(ligação para a marina da base)"
    ctx, pg, erros = abre(b, tela, largura, altura, equipe={'fones': {'marina': FONE}, 'convites': []})
    tel = pg.evaluate(ESTADO)['tel']
    confere_(n + ': o telefone cadastrado no aparelho vira o link tel: (só ele)', len(tel) == 1 and tel[0].startswith('tel:'), tel)
    if tel:
        pg.locator('a[href^="tel:"]').first.click()
        pg.wait_for_function("() => JSON.parse(localStorage.getItem('%s') || '[]').length >= 1" % CHAVE_DIARIO, timeout=5000)
        d = pg.evaluate(ESTADO)['diario']
        confere_(n + ': F04 ligar grava 1 linha dizendo "(ligação para a marina da base)"', len(d) == 1 and '(ligação para a marina da base)' in d[0]['t'] and 'sim' not in d[0], d)
    ctx.close()


def cenario_gps(b, tela, largura, altura, origem, rotulo):
    """Posição = GPS do aparelho: com a permissão já concedida lê sozinho; precisão pior que 100 m, sem coordenada; sem permissão, o toque não inventa."""
    n = '%s · %s' % (tela, rotulo)
    ctx, pg, erros = abre(b, tela, largura, altura, geo={'latitude': GPS_LAT, 'longitude': GPS_LON, 'accuracy': 12})
    pg.wait_for_function("() => /GPS DO CELULAR/.test(document.body.innerText)", timeout=8000)
    txt = pg.evaluate('() => document.body.innerText')
    confere_(n + ': permissão concedida lê o GPS sozinho: "GPS DO CELULAR %s ± 12 m às HH:MM — confira no plotter"' % GPS_TXT,
             re.search(r"GPS DO CELULAR %s ± 12 m às \d\d:\d\d — confira no plotter" % re.escape(GPS_TXT), txt), txt[:300])
    confere_(n + ': ... e o botão passa a ATUALIZAR GPS DO CELULAR', 'ATUALIZAR GPS DO CELULAR' in txt)
    varredura(pg, tela, rotulo + ' com GPS', *dados_barco(pg), com_gps=True)
    est = pg.evaluate(ESTADO)
    d = est['diario']
    confere_(n + ': a linha gravada leva só a coordenada do aparelho (nunca a do snapshot, da rota ou do replay)',
             len(d) == 1 and GPS_TXT in d[0]['t'] and '± 12 m' in d[0]['t'] and not so_a_coordenada_do_aparelho(d[0]['t']) and 'sim' not in d[0], d)
    confere_(n + ': nenhuma leitura proibida do D com o GPS', est['leituras'] == [], est['leituras'][:4])
    ctx.close()
    # precisão baixa: nenhuma coordenada, "LEIA NO PLOTTER", e a linha do diário também sem coordenada
    ctx, pg, erros = abre(b, tela, largura, altura, geo={'latitude': GPS_LAT, 'longitude': GPS_LON, 'accuracy': 350})
    pg.wait_for_function("() => /PRECISÃO BAIXA/.test(document.body.innerText)", timeout=8000)
    txt = pg.evaluate('() => document.body.innerText')
    confere_(n + ': precisão 350 m: "PRECISÃO BAIXA (± 350 m) — LEIA NO PLOTTER", sem coordenada', 'PRECISÃO BAIXA (± 350 m) — LEIA NO PLOTTER' in txt and not confere.R_COORD.search(txt), txt[:300])
    mayday(pg)
    pg.wait_for_function("() => JSON.parse(localStorage.getItem('%s') || '[]').length >= 1" % CHAVE_DIARIO, timeout=5000)
    d = pg.evaluate(ESTADO)['diario']
    confere_(n + ': ... e a linha do diário diz "precisão baixa" e "plotter", sem coordenada', len(d) == 1 and 'precisão baixa' in d[0]['t'] and 'plotter' in d[0]['t'] and not confere.R_COORD.search(d[0]['t']), d)
    ctx.close()
    # sem permissão: o toque no botão não inventa posição
    ctx, pg, erros = abre(b, tela, largura, altura)
    pg.get_by_text('MOSTRAR GPS DO CELULAR').first.click()
    pg.wait_for_timeout(1500)
    txt = pg.evaluate('() => document.body.innerText')
    confere_(n + ': sem permissão, o toque em MOSTRAR GPS DO CELULAR deixa "POSIÇÃO: LEIA NO PLOTTER" (nenhuma coordenada)', 'POSIÇÃO: LEIA NO PLOTTER' in txt and not confere.R_COORD.search(txt), txt[:300])
    mayday(pg)
    pg.wait_for_function("() => JSON.parse(localStorage.getItem('%s') || '[]').length >= 1" % CHAVE_DIARIO, timeout=5000)
    d = pg.evaluate(ESTADO)['diario']
    confere_(n + ': ... e a linha do diário diz "posição: ler no plotter"', len(d) == 1 and 'posição: ler no plotter' in d[0]['t'] and not confere.R_COORD.search(d[0]['t']), d)
    ctx.close()


def dados_barco(pg):
    """(E, equipamentos, snapshot) do capitao-dados.js, lidos por fora do Proxy (a leitura não conta como do SOS)."""
    r = pg.evaluate("""async () => { const txt = await (await fetch('./capitao-dados.js', { cache: 'no-store' })).text(), corte = txt.indexOf('/* CapitaoAgora');
      const w = {}; new Function('window', corte > 0 ? txt.slice(0, corte) : txt)(w); const D = w.CapitaoDados;
      return { E: D.embarcacao, equip: D.equipamentos, snap: D.snapshot }; }""")
    return r['E'], r['equip'], r['snap']


def cenario_offline(b, tela, largura, altura, origem, E, equipamentos, snap):
    """1ª visita com internet (o service worker instala), depois sem rede: as mesmas conferências, também a ação."""
    ctx = b.new_context(viewport={'width': largura, 'height': altura})
    ctx.add_init_script(CONTA_LEITURAS)
    pg = ctx.new_page()
    pg.goto(BASE + tela + '.dc.html', wait_until='load', timeout=30000)
    try:
        pg.wait_for_function("() => navigator.serviceWorker && navigator.serviceWorker.controller", timeout=30000)
    except Exception:
        confere_(tela + ' · offline: o service worker instalou em 30 s', False)
        ctx.close()
        return
    pg.wait_for_timeout(1500)
    ctx.set_offline(True)
    pg.close()
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append(str(e)[:200]))
    pg.goto(BASE + tela + '.dc.html', wait_until='load', timeout=30000)
    pg.wait_for_function(PRONTA, timeout=20000)
    pg.wait_for_timeout(500)
    est = pg.evaluate(ESTADO)
    n = tela + ' · offline'
    confere_(n + ': abre sem rede e sem login (navigator.onLine falso)', est['online'] is False and est['url'].endswith(tela + '.dc.html'), (est['online'], est['url']))
    confere_(n + ': nada gravado ao abrir; CapitaoAgora.instante() é null; nenhuma leitura proibida', est['diario'] == [] and est['instante'] == 'null' and est['leituras'] == [], (est['diario'], est['instante'], est['leituras'][:3]))
    varredura(pg, tela, 'offline', E, equipamentos, snap)
    est = pg.evaluate(ESTADO)
    confere_(n + ': a ação (roteiro MAYDAY e MOB) grava 1 linha, sem `sim`, com "plotter"', len(est['diario']) == 1 and 'sim' not in est['diario'][0] and 'plotter' in est['diario'][0]['t'], est['diario'])
    confere_(n + ': sem erro de script e nenhuma leitura proibida do D', not erros and est['leituras'] == [], (erros, est['leituras'][:3]))
    ctx.close()


def main():
    so_offline = '--so-offline' in sys.argv
    sem_offline = '--sem-offline' in sys.argv
    with sync_playwright() as p:
        b = p.chromium.launch(channel=CANAL, headless=True)
        # o dado que o SOS não pode mostrar, lido do arquivo gerado (por fora do Proxy)
        pg = b.new_page()
        pg.goto(BASE + 'base-conhecimento.json')
        pg.add_script_tag(url=BASE + 'capitao-dados.js')
        E, equipamentos, snap = pg.evaluate("() => ({ E: window.CapitaoDados.embarcacao, equip: window.CapitaoDados.equipamentos, snap: window.CapitaoDados.snapshot })").values()
        pg.close()
        for tela, largura, altura, origem in TELAS:
            if not so_offline:
                cenario_frio(b, tela, largura, altura, origem, E, equipamentos, snap, 'online, aparelho vazio')
                cenario_acoes(b, tela, largura, altura, origem, 'ações')
                cenario_gps(b, tela, largura, altura, origem, 'GPS do aparelho')
            if not sem_offline:
                cenario_offline(b, tela, largura, altura, origem, E, equipamentos, snap)
        b.close()
    print('SOS fora da simulação: %d conferências · %d falhas' % (total, falhas))
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
