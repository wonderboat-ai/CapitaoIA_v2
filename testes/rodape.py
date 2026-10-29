# -*- coding: utf-8 -*-
"""Capitão IA — teste do rodapé do capitao-dados.js (CapitaoAgora, CONTRATO-DADOS §1.23 e §4.1; C7). Sem rede, sem cota.

O rodapé refaz os prazos (agenda, tarefas da equipe, documentos, diário, abastecimentos e a série de 24 V) com a data do
aparelho no fuso America/Sao_Paulo, e é a única fonte do instante (`instante()`), da trava do ar e da água e das contagens.
Aqui, com o `Date` congelado por add_init_script (a página abre numa rota mínima que só carrega o capitao-dados.js):

- âncora, hoje e dia de bordo em 06:59:59, 07:00:01, 23:59 e 00:30, com o Intl e sem ele (reserva de −180 min); os prazos, as
  datas e o iso de cada lista contra uma conta independente em Python (datetime), a partir dos deslocamentos do gerador;
- 3 atrasadas e a agenda ordenada por dn; em 06:59:59 e 07:00:01, d06.d = ultima do epirb-teste, d09.d = emitido do laudo e
  d03.d = vence do gerador-rotor (dd/mm), e a d01 acima da d03;
- o port do status_prazo contra o do gerador (n de −5 a 200), o prazoDe/docDe do rodapé;
- idempotência (rebase 2× = 1×), listas iguais por referência (===) antes e depois do rebase de outro dia, nenhum null nem ''
  no D, o D.snapshot sem mudar (nem um byte) depois de rebases em vários dias, a paridade com a reserva do gerador (relógio
  congelado na REF: o D inteiro igual ao que o gerador gravou);
- as demais chaves do D (protocolos, embarcacao, equipamentos, guias, faq, consumo, equipe, drive…; replay, rota, historico e campos quando existirem)
  iguais, byte a byte, ao que o gerador gravou depois de rebases em +3, +40, −10 e 0 dias e com S1 e S2 abertas em outro dia, com dois rodapés
  mutantes que provam que a conferência falha (revisão do C7: só o D.snapshot era vigiado e o texto do SOS podia ser reescrito);
- a microtarefa do dia de bordo (com um D.replay.diaDeBordo de teste): entra por id, nas mesmas listas, com d01 = âncora + 1 s e
  d02 = âncora; com `simulacao = false` no fim do arquivo, nada entra; em /SOS-/ (S1, S2 e uma rota mínima), COM uma fonte de leitura
  à mão (um CapitaoReplay, um CapitaoTelemetria e um D.snapshot.quadro com posição), o instante é null, nada entra e nem D.simulacao nem
  D.replay são lidos nenhuma vez (getters que contam); fora do SOS a mesma fixture dá o instante (coletor, replay, reserva) e as leituras
  contam ≥ 1: sem isso o "null" do SOS passava por falta de fonte e não pela guarda /SOS-/ (revisão do C7);
- contagens() com o executado, as tarefas e as ações do diário do aparelho (e com JSON válido de outra forma, como '{}' onde se espera
  lista: vale como vazio e nunca zera as outras contas); a trava e o instante() nas três fontes (replay,
  coletor e a reserva do snapshot) com os números do §1.22 e do §1.23 (12:01:00): autonomia, faltam, desdeAbast, diesel_pct;
- os formatadores (arred, nb, mil, grau3, hora, coord, campo);
- nenhuma escrita no aparelho (§4.1: «não grava no localStorage nem cria linha no diário do aparelho»; revisão do C7): um contador em
  Storage.prototype (setItem, removeItem, clear: localStorage e sessionStorage) e em indexedDB.open, com a pilha de cada escrita, separa as
  do rodapé (pilha no capitao-dados.js) das da tela; 0 do rodapé na carga e no uso (rebase forçado em vários dias, contagens, trava,
  instante, prazoDe, docDe, fmt) na rota mínima, na A1, na S1, na S2 e na /SOS-teste.html, com o controle (a escrita do próprio teste entra no
  contador) e 10 mutantes que gravam (diário e executado do aparelho, sessionStorage, clear, indexedDB, a microtarefa, o instante, as contagens,
  a trava, o rebase forçado) que a conferência tem de acusar; mais a leitura estática do código do rodape.js;
- as telas com o rodapé (C1, C2, B1, G1, A1, G3, G4): "prazos a partir de" = hoje, sem "falta registrar" vazio, e a A1 sem a data do
  autoteste do EPIRB e da inspeção do sistema fixo (a validade deles só em Equipamentos, Leme e Documentos, CONTRATO §1.4);
- a G1 (web e app), com a nota fiscal do abastecimento tal como o C8 a entrega (pela microtarefa, a partir de replay.diaDeBordo):
  situação CONFERIDA, nunca SEM DADOS (CONTRATO §1.8), e sem o bloco FALTA REGISTRAR (revisão do C7);
- revisão do C8 (snapshot_sem_null): B2, F3 (app e web), A1, A2, E1 e G2 abrem com o dado gerado de verdade, sem [object Object] no texto nem nos
  `title`; a B2 diz «porão: BB 1,2 cm · BE 0,9 cm», as duas F3 «LANÇADA · 30 m» e a G2 tem as 3 linhas de abastecimento (07:00, 1.086 L);
  provado contra as três guardas de 1 linha tiradas (B2:158, F3-Web:222, F3:216), que antes não tinham teste;
- C8: o D que o gerador grava já traz o dia de bordo em replay.diaDeBordo (o arquivo tem `abastecimentos: []`, só d03–d09 no diário e
  7 documentos): a microtarefa o completa, e as listas e os prazos batem com a conta em Python sobre o próprio D gerado; a
  CapitaoAgora.nivel contra o port em Python (confere.nivel) nos 150 quadros do laço e nos casos de borda do §3.3 (paridade).

Uso (com o site servido em http://127.0.0.1:8765, na raiz do repositório):
    python -X utf8 testes/rodape.py
Navegador: Edge instalado (Playwright com channel="msedge"); troque CANAL para "chrome" se preferir.
"""
import importlib.util
import json
import os
import re
import sys
from datetime import date, datetime, time, timedelta, timezone

from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8765'
CANAL = 'msedge'
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BR = timezone(timedelta(hours=-3))
MARCA = '/* CapitaoAgora'   # o começo do rodapé no capitao-dados.js: o que entra antes dele roda antes dele
HTML = '<!doctype html><meta charset="utf-8"><title>rodape</title><script src="/capitao-dados.js"></script>'

spec = importlib.util.spec_from_file_location('gerar_demo', os.path.join(RAIZ, 'ferramentas', 'demo', 'gerar_demo.py'))
sys.path.insert(0, os.path.join(RAIZ, 'ferramentas', 'demo'))
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)
import confere as C  # noqa: E402  (o port em Python da nivel e do laço)

falhas = 0
total = 0


def ok(nome, cond, info=''):
    global falhas, total
    total += 1
    print(('OK    ' if cond else 'FALHA ') + nome + ('' if cond or info == '' else ' — ' + str(info)[:500]))
    if not cond:
        falhas += 1


# ——— contas independentes (Python) ———
def br(d):
    return d.strftime('%d/%m/%Y')


def dm(d):
    return d.strftime('%d/%m')


def dias(local):
    """(hoje, dia de bordo) no fuso: o dia de bordo começa às 07:00 (antes dela, o de ontem)."""
    hoje = local.date()
    return hoje, hoje if local >= datetime.combine(hoje, time(7, 0), BR) else hoje - timedelta(days=1)


def ms_de(local):
    return int(local.timestamp() * 1000)


# Fixture do dia de bordo (CONTRATO §1.8–§1.10) com números de teste (o D que o gerador grava já traz o replay.diaDeBordo de verdade desde o
# C8; esta fixture o troca por um mínimo, para os testes que contam com valores fixos): três abastecimentos de 07:00, d01 e d02 no topo e a nota fiscal.
DIA_DE_BORDO = """window.CapitaoDados.replay = { ancora_hora: '07:00', diaDeBordo: { dias: 3,
  abastecimento: { h: '07:00', litros: 1086, combustivel: 'diesel', local: 'posto da marina da base', st: 'CONFERIDO', nivelAntes: 29.6, nivelDepois: 97.5, nota: 'para a saída das 07:00' },
  documento: { id: 'nf-abast', n: 'Nota fiscal do abastecimento', cat: 'Notas', emitidoHa: 0, st: 'CONFERIDA', ref: 'ab-0', nota: 'abastecimento das 07:00', fonte: window.CapitaoDados.docsFonte },
  diario: [ { id: 'd01', diasAtras: 0, h: '07:00', sys: 'Navegação', tom: 'tele', who: 'Lucas', pend: false, t: 'Saída às 07:00 com 4 pessoas a bordo.' },
            { id: 'd02', diasAtras: 0, h: '07:00', sys: 'Combustível', tom: 'ok', who: 'Lucas', pend: false, ref: 'ab-0', t: 'Abastecimento de 1.086 L.' } ] } };"""
# Linhas "velhas" no arquivo (como o C7 as deixava): a microtarefa as substitui por id, sem duplicar.
TRANSICAO = """(function (D) { D.diario.unshift({ id: 'd01', diasAtras: 0, h: '07:00', sys: 'Navegação', tom: 'tele', who: 'Lucas', pend: false, t: 'Saída da base com 4 pessoas a bordo.' });
  D.documentos.push({ id: 'nf-abast', n: 'Nota fiscal do abastecimento', cat: 'Notas', emitidoHa: 14, st: 'CONFERIDA', nota: 'abastecimento antigo' }); })(window.CapitaoDados);"""
GETTER = """window.__lidas = 0; (function () { var v = window.CapitaoDados.simulacao; Object.defineProperty(window.CapitaoDados, 'simulacao',
  { get: function () { window.__lidas++; return v; }, set: function (x) { v = x; }, configurable: true, enumerable: true }); })();"""
# Leitura de teste para o SOS recusar (revisão do C7): enquanto não havia fonte nenhuma (sem CapitaoReplay, sem coletor, sem D.snapshot.quadro),
# o instante() era null em qualquer página e a guarda /SOS-/ nunca era posta à prova. Com as três fontes à mão, só a guarda devolve null.
# O D.replay vira um getter que conta (como a simulacao): em /SOS-/ ninguém o lê, nem o rodapé (a âncora do SOS é fixa, 07:00).
LEITURA = "{ timestamp_utc: '2026-10-27T15:01:00Z', lat: -26.99, lon: -48.61, sog_nos: 18.1, diesel_litros: 1333, temp_ar_externo_c: 22.6, temp_agua_c: 20.1 }"
FONTE_REPLAY = "window.CapitaoReplay = { agora: function () { return Date.now(); }, em: function () { return %s; }, t: function () { return 60; }, fase: function () { return { nome: 'cruzeiro', ini: 50, fim: 120 }; }, fixo: function () { return ''; } };" % LEITURA
FONTE_COLETOR = "window.CapitaoTelemetria = { atual: function () { return %s; } };" % LEITURA
FONTE_RESERVA = "window.CapitaoDados.snapshot.quadro = %s;" % LEITURA
GETTER_REPLAY = """window.__lidasReplay = 0; (function () { var v = window.CapitaoDados.replay; Object.defineProperty(window.CapitaoDados, 'replay',
  { get: function () { window.__lidasReplay++; return v; }, set: function (x) { v = x; }, configurable: true, enumerable: true }); })();"""
GUARDA = "window.__reserva = JSON.stringify(window.CapitaoDados); window.__snap0 = JSON.stringify(window.CapitaoDados.snapshot);"
# Revisão do C7: o que o rebase escreve (CONTRATO §4.1: derivados e deslocamentos que ele nunca reescreve). Toda OUTRA chave do D tem de sair do
# rebase byte a byte como o gerador a gravou, e não só o D.snapshot (o D.protocolos e o D.embarcacao são as duas entradas do SOS: S1/S2 leem
# só embarcacao.nome e protocolos). A fotografia é tirada antes do rodapé, chave por chave; as chaves de C8/C9 (replay, rota, historico, campos)
# entram sozinhas quando existirem, e NOMEADAS prende as que já existem (renomear uma não deixa a conferência vazia).
DERIVADAS = ('versao', 'agenda', 'tarefasEquipe', 'documentos', 'diario', 'abastecimentos', 'serie24v')
NOMEADAS = ('snapshot', 'protocolos', 'embarcacao', 'equipamentos', 'guias', 'faq', 'consumo', 'equipe', 'drive')
FOTO = "window.__foto = {}; (function () { var D = window.CapitaoDados; Object.keys(D).forEach(function (k) { window.__foto[k] = JSON.stringify(D[k]); }); })();"
# as chaves que mudaram em relação à fotografia (fora as derivadas) e as que o rebase acrescentou ao D
MUDOU = """(derivadas) => { const D = window.CapitaoDados, f = window.__foto;
  return { mudou: Object.keys(f).filter((k) => derivadas.indexOf(k) < 0 && JSON.stringify(D[k]) !== f[k]), novas: Object.keys(D).filter((k) => !(k in f)),
           chaves: Object.keys(f).filter((k) => derivadas.indexOf(k) < 0) }; }"""
# rebases em outros dias (forçados), como a virada das 07:00 ou da meia-noite com a página aberta; devolve o MUDOU de cada um
REBASES = """([derivadas, dias, mudou]) => { const A = window.CapitaoAgora, t = Date.now(), r = {}, m = eval(mudou);
  for (const k of dias) { A.rebase(t + k * 86400000, true); r[k] = m(derivadas); } return r; }"""
# Mutantes do rodapé: rebases que escrevem onde não devem. Os dois são idempotentes e só agem fora da REF (26/09/2026), como o que a revisão
# reproduziu: na REF o rodapé de verdade e o mutante dão o mesmo D, e só um rebase em outro dia mostra a diferença.
DIA_REF = (date(2026, 9, 26) - date(1970, 1, 1)).days
ALVO_MUTANTE = 'D.versao = br(hojeN);'
MUTANTE_SOS = ALVO_MUTANTE + (" if (hojeN !== %d && D.protocolos && D.embarcacao) { D.protocolos.mmsiRotulo = String(D.protocolos.mmsiRotulo).toUpperCase();"
                              " D.embarcacao.nome = String(D.embarcacao.nome).toUpperCase(); }" % DIA_REF)
MUTANTE_GUIAS = ALVO_MUTANTE + (" if (hojeN !== %d && D.guias) { for (var g in D.guias) { D.guias[g] = String(D.guias[g]).toUpperCase(); break; } }" % DIA_REF)
# Revisão do C7: contador de escritas no aparelho (§4.1). Cada escrita (setItem, removeItem e clear, de localStorage e de sessionStorage, e
# indexedDB.open) entra em window.__escritas com a operação, a chave e `dados`: true se a pilha passa pelo capitao-dados.js, onde o rodapé é
# anexado (a sessão, o tema e o resto das telas escrevem de outros arquivos e não contam como do rodapé; os testes de si mesmos também não).
ESCRITAS = """(function () { var reg = window.__escritas = [];
  function nota(op, chave) { var st = ''; try { st = new Error().stack || ''; } catch (e) {} reg.push({ op: op, chave: chave, dados: st.indexOf('capitao-dados.js') >= 0 }); }
  ['setItem', 'removeItem', 'clear'].forEach(function (op) { var o = Storage.prototype[op];
    Storage.prototype[op] = function (k) { nota(op, op === 'clear' ? null : String(k)); return o.apply(this, arguments); }; });
  if (window.IDBFactory) { var ob = IDBFactory.prototype.open; IDBFactory.prototype.open = function (n) { nota('indexedDB.open', String(n)); return ob.apply(this, arguments); }; } })();"""
# o uso de toda a API do rodapé que mexe com o aparelho ou com o D: rebase forçado em vários dias, contagens, trava, instante, prazoDe, docDe, fmt
USA = """([dias, quadro]) => { const A = window.CapitaoAgora, t = Date.now();
  A.rebase(t, true); for (const k of dias) A.rebase(t + k * 86400000, true); A.rebase(t, true);
  return { inst: !!A.instante(), contagens: A.contagens(), trava: A.trava(quadro), prazo: A.prazoDe(5), doc: A.docDe(5), campo: A.fmt.campo(quadro, 'sog_nos') }; }"""
DADOS_ESCRITAS = "() => window.__escritas.filter((e) => e.dados).map((e) => e.op + ':' + e.chave)"


def abre(b, local, intl=True, antes='', depois='', caminho='/rodape.html', sessao=False, tela=None, muta=None):
    """Página com o Date congelado em `local` (e sem Intl, se pedido). `antes` roda antes do rodapé e `depois` no fim do arquivo.
    `muta` = (trecho do rodape.js, trecho no lugar dele): o rodapé mutante dos testes que provam que a conferência falha (revisão do C7)."""
    ctx = b.new_context(service_workers='block', **({'viewport': {'width': 390, 'height': 844}, 'has_touch': True} if tela == 'app' else {}))
    ctx.add_init_script(ESCRITAS)   # antes de qualquer outro script da página (a sessão do `sessao`, o rodapé, as telas)
    ctx.add_init_script("(function () { var RD = Date; window.__T0 = %d; function FD() { var a = arguments; return a.length === 0 ? new RD(window.__T0) : new (Function.prototype.bind.apply(RD, [null].concat([].slice.call(a))))(); }"
                        " FD.prototype = RD.prototype; FD.now = function () { return window.__T0; }; FD.UTC = RD.UTC; FD.parse = RD.parse; window.Date = FD; %s })();"
                        % (ms_de(local), '' if intl else 'window.Intl = undefined;'))

    if sessao:   # depois do Date congelado: a sessão vale a partir do relógio da página
        ctx.add_init_script("(() => { const n = Date.now(); localStorage.setItem('capitao.sessao.v1', JSON.stringify({ u: 'lucas', em: n, exp: n + 3600e3 })); })()")

    def dados(route):
        r = route.fetch()
        corpo = r.text()
        assert MARCA in corpo, 'o rodapé não está no capitao-dados.js'
        if muta:
            assert corpo.count(muta[0]) == 1, 'o trecho do mutante não está (uma vez) no rodapé: ' + muta[0]
            corpo = corpo.replace(muta[0], muta[1], 1)
        route.fulfill(response=r, body=corpo.replace(MARCA, antes + '\n' + MARCA, 1) + '\n' + depois)
    ctx.route('**/capitao-dados.js', dados)
    if caminho.endswith('.html') and not caminho.endswith('.dc.html'):
        ctx.route('**' + caminho, lambda route: route.fulfill(body=HTML, content_type='text/html; charset=utf-8'))
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.goto(BASE + caminho)
    pg.wait_for_function('() => window.CapitaoAgora && window.CapitaoAgora.relogio')
    pg.wait_for_timeout(100)   # a microtarefa do dia de bordo
    pg.erros = erros
    return pg


ESTADO = """() => { const D = window.CapitaoDados, A = window.CapitaoAgora;
  return { relogio: A.relogio, versao: D.versao, agenda: D.agenda.map((t) => [t.id, t.ultima, t.vence, t.dn, t.st, t.rot, t.tom]),
    tarefas: D.tarefasEquipe.map((t) => [t.id, t.vence, t.dn, t.st, t.rot, t.tom]), docs: D.documentos.map((x) => [x.id, x.emitido, x.vence, x.dn, x.st]),
    diario: D.diario.map((x) => [x.id, x.d, x.iso]), abast: D.abastecimentos.map((a) => [a.id, a.diasAtras, a.d]), serie: D.serie24v.map((s) => s.d) }; }"""


def esperado(local):
    """O estado que o rebase tem de dar, calculado em Python só com os deslocamentos do gerador."""
    hoje, bordo = dias(local)
    ag = [[t['id'], br(hoje - timedelta(days=t['ultimaHa'])), br(hoje + timedelta(days=t['venceEm'])), t['venceEm'],
           G.status_prazo(t['venceEm'])['st'], G.status_prazo(t['venceEm'])['rot'], G.status_prazo(t['venceEm'])['tom']] for t in G.AGENDA]
    ag.sort(key=lambda x: (x[3], x[0]))
    te = [[t['id'], (hoje + timedelta(days=t['venceEm'])).isoformat(), t['venceEm'], G.status_prazo(t['venceEm'])['st'],
           G.status_prazo(t['venceEm'])['rot'], G.status_prazo(t['venceEm'])['tom']] for t in G.TAREFAS_EQUIPE]
    bordo_d = G.dados()['replay']['diaDeBordo']   # o que a microtarefa insere (replay.diaDeBordo)
    docs = []
    for x in list(G.DOCUMENTOS) + [bordo_d['documento']]:
        base = bordo if x['id'] == 'nf-abast' else hoje
        docs.append([x['id'], br(base - timedelta(days=x['emitidoHa'])) if 'emitidoHa' in x else None,
                     br(hoje + timedelta(days=x['venceEm'])) if 'venceEm' in x else None, x.get('venceEm'),
                     G.status_doc(x['venceEm']) if 'venceEm' in x else x['st']])
    linhas = list(bordo_d['diario']) + list(G.DIARIO)   # d01 e d02 no topo, depois o diário fixo
    seg = G.segundos_do_diario(linhas, lambda x: 'b' if x['id'] in G.BORDO_DIARIO else 'h')
    di = []
    for x, s_ in zip(linhas, seg):
        base = bordo if x['id'] in G.BORDO_DIARIO else hoje
        d = base - timedelta(days=x['diasAtras'])
        di.append([x['id'], dm(d), '%sT%s:%02d-03:00' % (d.isoformat(), x['h'], s_)])
    return {'versao': br(hoje), 'agenda': ag, 'tarefas': te, 'docs': docs, 'diario': di,
            'abast': [['ab-%d' % k, k, br(bordo - timedelta(days=k))] for k in range(bordo_d['dias'])],
            'serie': [dm(bordo - timedelta(days=s['diasAtras'])) for s in G.SERIE_24V]}


def limpa(estado):
    """O estado do JS sem os None do JSON onde o Python põe None (id de abastecimento, campos omitidos)."""
    e = json.loads(json.dumps(estado))
    e.pop('relogio', None)
    return e


def sem_nulos(x, caminho=''):
    """Os null, '', NaN e listas vazias do D (menos a lista de abastecimentos, que é a única que pode ser vazia no arquivo gerado)."""
    out = []
    if x is None:
        out.append(caminho)
    elif isinstance(x, str):
        if x == '':
            out.append(caminho + " = ''")
    elif isinstance(x, dict):
        for k, v in x.items():
            out += sem_nulos(v, caminho + '.' + k)
    elif isinstance(x, list):
        if not x and caminho != '.abastecimentos':
            out.append(caminho + ' = []')
        for i, v in enumerate(x):
            out += sem_nulos(v, '%s[%d]' % (caminho, i))
    return out


def relogio_e_listas(b):
    print('Relógio, âncora e prazos (Date congelado; com e sem Intl)')
    casos = [('06:59:59', datetime(2026, 10, 27, 6, 59, 59, tzinfo=BR), True), ('07:00:01', datetime(2026, 10, 27, 7, 0, 1, tzinfo=BR), True),
             ('23:59', datetime(2026, 10, 27, 23, 59, tzinfo=BR), True), ('00:30', datetime(2026, 10, 27, 0, 30, tzinfo=BR), True),
             ('06:59:59 sem Intl', datetime(2026, 10, 27, 6, 59, 59, tzinfo=BR), False), ('07:00:01 sem Intl', datetime(2026, 10, 27, 7, 0, 1, tzinfo=BR), False)]
    for nome, local, intl in casos:
        pg = abre(b, local, intl=intl)
        hoje, bordo = dias(local)
        e, esp = pg.evaluate(ESTADO), esperado(local)
        r = e['relogio']
        anc = datetime.combine(hoje if local >= datetime.combine(hoje, time(7, 0), BR) else hoje - timedelta(days=1), time(7, 0), BR)
        ok('%s: hoje %s, dia de bordo %s, âncora %s' % (nome, br(hoje), br(bordo), anc.strftime('%d/%m 07:00')),
           r['hoje'] == br(hoje) and r['diaBordo'] == br(bordo) and r['hojeIso'] == hoje.isoformat() and r['diaBordoIso'] == bordo.isoformat()
           and r['ancoraMs'] == ms_de(anc) and r['off'] == -180 and pg.evaluate('() => window.CapitaoAgora.assinatura') == br(hoje) + '|' + br(bordo), r)
        e = limpa(e)
        for k in ('versao', 'agenda', 'tarefas', 'docs', 'diario', 'serie'):
            ok('%s: %s igual à conta em Python' % (nome, k), e[k] == esp[k], [(a, b2) for a, b2 in zip(e[k], esp[k]) if a != b2][:3] if isinstance(e[k], list) else (e[k], esp[k]))
        ok('%s: abastecimentos ab-0…ab-2 com o d do dia de bordo' % nome, e['abast'] == esp['abast'], e['abast'])
        ag = e['agenda']
        ok('%s: 14 tarefas, 3 atrasadas, ordem por dn' % nome, len(ag) == 14 and sum(1 for t in ag if t[3] < 0) == 3 and [t[3] for t in ag] == sorted(t[3] for t in ag),
           [(t[0], t[3]) for t in ag])
        d = {x[0]: x for x in e['diario']}
        ids = {t[0]: t for t in ag}
        dc = {x[0]: x for x in e['docs']}
        ok('%s: d06.d = ultima do epirb-teste, d09.d = emitido do laudo, d03.d = vence do gerador-rotor (dd/mm)' % nome,
           d['d06'][1] == ids['epirb-teste'][1][:5] and d['d09'][1] == dc['laudo'][1][:5] and d['d03'][1] == ids['gerador-rotor'][2][:5],
           (d['d06'], ids['epirb-teste'], d['d09'], dc['laudo'], d['d03'], ids['gerador-rotor']))
        ok('%s: a d01 acima da d03 no diário (data e ordem)' % nome, [x[0] for x in e['diario']].index('d01') < [x[0] for x in e['diario']].index('d03') and d['d01'][2] > d['d03'][2],
           (d['d01'], d['d03']))
        ok('%s: sem erro de script' % nome, not pg.erros, pg.erros)
        pg.context.close()


def idempotencia(b):
    print('Idempotência, listas por referência, nulos, snapshot e paridade com a reserva')
    local = datetime(2026, 9, 26, 12, 0, tzinfo=BR)   # a REF do gerador
    pg = abre(b, local, antes=GUARDA)
    r = pg.evaluate("""() => { const D = window.CapitaoDados, A = window.CapitaoAgora, s0 = JSON.stringify(D), t = Date.now();
      const a = A.rebase(t), s1 = JSON.stringify(D), f = A.rebase(t, true), s2 = JSON.stringify(D);
      const refs = { agenda: D.agenda, diario: D.diario, documentos: D.documentos, abastecimentos: D.abastecimentos, tarefasEquipe: D.tarefasEquipe, serie24v: D.serie24v };
      const antes = JSON.stringify([D.agenda.map((x) => x.vence), D.diario.map((x) => x.iso)]);
      const snaps = [], dia = 86400000;
      for (const k of [3, 40, -10, 0]) { A.rebase(t + k * dia, true); snaps.push(JSON.stringify(D.snapshot) === window.__snap0); }
      const depois = JSON.stringify([D.agenda.map((x) => x.vence), D.diario.map((x) => x.iso)]);
      A.rebase(t + 3 * dia, true); const mudou = JSON.stringify([D.agenda.map((x) => x.vence), D.diario.map((x) => x.iso)]);
      // a única diferença entre o D que o gerador gravou (a reserva) e o de depois do rodapé é o dia de bordo que a microtarefa insere (§4.1)
      const sem = JSON.parse(s0); sem.abastecimentos = []; sem.diario = sem.diario.filter((x) => x.id !== 'd01' && x.id !== 'd02');
      sem.documentos = sem.documentos.filter((x) => x.id !== 'nf-abast');
      return { a, f, idem: s0 === s1 && s1 === s2, reserva: window.__reserva === JSON.stringify(sem), mesmos: Object.keys(refs).every((k) => D[k] === refs[k]), snaps,
               igual: antes === depois, mudou: mudou !== antes, d: JSON.parse(JSON.stringify(D)) }; }""")
    ok('rebase na REF: o D inteiro igual ao que o gerador gravou (reserva, byte a byte), fora o dia de bordo que a microtarefa insere', r['reserva'])
    ok('rebase 2× = 1×: o segundo devolve false, o forçado true, e o D não muda', r['a'] is False and r['f'] is True and r['idem'])
    ok('as listas do D são as mesmas (===) depois de rebases em outros dias; as datas mudam e voltam', r['mesmos'] and r['mudou'] and r['igual'])
    ok('o D.snapshot não muda (nem um byte) depois de rebases em +3, +40, −10 e 0 dias', all(r['snaps']), r['snaps'])
    nulos = sem_nulos(r['d'])
    ok('nenhum null, \'\' ou lista vazia no D depois do rebase e da microtarefa (o snapshot sem null desde o C8)', not nulos, nulos[:5])
    ok('sem erro de script', not pg.erros, pg.erros)
    pg.context.close()
    print('Port do status_prazo e do status dos documentos contra o do gerador')
    pg = abre(b, local)
    r = pg.evaluate("() => { const A = window.CapitaoAgora, o = []; for (let n = -5; n <= 200; n++) o.push([n, A.prazoDe(n), A.docDe(n)]); return o; }")
    errados = [(n, p, d) for n, p, d in r if p != G.status_prazo(n) or d['st'] != G.status_doc(n) or d['tom'] != G.status_prazo(n)['tom']]
    ok('prazoDe/docDe = status_prazo/status_doc do gerador, de −5 a 200 dias (%d casos)' % len(r), not errados, errados[:3])
    pg.context.close()


def so_o_derivado(b):
    """Revisão do C7. CONTRATO §4.1: o rebase NUNCA toca D.snapshot, D.protocolos, D.embarcacao, D.replay, D.rota, D.historico nem D.campos
    (nem nenhuma chave que ele não deriva). Só o D.snapshot era vigiado, e um rebase que reescrevesse o texto do SOS (D.protocolos,
    D.embarcacao) em qualquer dia fora da REF passava em tudo. Aqui a fotografia de cada chave não derivada, tirada antes do rodapé, tem de ser
    igual depois de rebases em +3, +40, −10 e 0 dias e depois de abrir S1 e S2 em outro dia; e dois rodapés mutantes (que escrevem no
    D.protocolos e no D.embarcacao, ou no D.guias, só fora da REF) provam que a conferência falha."""
    print('O rebase só escreve o que deriva: as demais chaves do D (protocolos, embarcacao…) iguais ao que o gerador gravou')
    local = datetime(2026, 9, 26, 12, 0, tzinfo=BR)   # a REF do gerador
    DIAS = [3, 40, -10, 0]
    pg = abre(b, local, antes=FOTO)
    r = pg.evaluate(REBASES, [list(DERIVADAS), DIAS, MUDOU])
    chaves = pg.evaluate(MUDOU, list(DERIVADAS))['chaves']
    ok('as chaves vigiadas incluem snapshot, protocolos, embarcacao, equipamentos, guias, faq, consumo, equipe e drive (%d no total)' % len(chaves),
       all(k in chaves for k in NOMEADAS) and not any(k in chaves for k in DERIVADAS), chaves)
    ok('REF + 3, + 40, − 10 e 0 dias: nenhuma chave não derivada muda (nem um byte) e o rebase não acrescenta chave ao D',
       all(r[str(k)]['mudou'] == [] and r[str(k)]['novas'] == [] for k in DIAS), {k: (v['mudou'], v['novas']) for k, v in r.items()})
    ok('sem erro de script', not pg.erros, pg.erros)
    pg.context.close()
    # S1 e S2 abertas em outro dia (27/10): a virada do dia roda no carregamento e de novo na hora (rebase forçado em +3 e −10 dias)
    outro = datetime(2026, 10, 27, 12, 0, tzinfo=BR)
    for nome, caminho in (('S1-SOS-Web', '/S1-SOS-Web.dc.html'), ('S2-SOS-Mobile', '/S2-SOS-Mobile.dc.html')):
        pg = abre(b, outro, antes=FOTO, caminho=caminho)
        pg.wait_for_timeout(800)
        carga = pg.evaluate(MUDOU, list(DERIVADAS))
        r = pg.evaluate(REBASES, [list(DERIVADAS), [3, -10], MUDOU])
        ok('%s aberta em 27/10/2026: o D.protocolos e o D.embarcacao (e o resto) saem do rebase como o gerador gravou, na carga e em +3 e −10 dias' % nome,
           carga['mudou'] == [] and carga['novas'] == [] and all(v['mudou'] == [] and v['novas'] == [] for v in r.values())
           and all(k in carga['chaves'] for k in NOMEADAS), (carga, r))
        pg.context.close()
    # os mutantes: a mesma conferência tem de acusar a chave escrita (sem isso ela poderia passar no vácuo)
    for nome, muta, quem in (('rebase que reescreve o D.protocolos e o D.embarcacao fora da REF', MUTANTE_SOS, ['protocolos', 'embarcacao']),
                             ('rebase que reescreve o D.guias fora da REF', MUTANTE_GUIAS, ['guias'])):
        pg = abre(b, local, antes=GUARDA + FOTO, muta=(ALVO_MUTANTE, muta))
        na_ref = pg.evaluate(MUDOU, list(DERIVADAS))['mudou']   # o mutante é inerte na REF: um teste que só rebaseasse na REF não o veria
        r = pg.evaluate(REBASES, [list(DERIVADAS), DIAS, MUDOU])
        snap = pg.evaluate("() => JSON.stringify(window.CapitaoDados.snapshot) === window.__snap0")   # e a conferência de antes (só o snapshot) passava
        ok('mutante (%s): na REF passa, em +3, +40 e −10 dias a conferência acusa %s, e o D.snapshot (a conferência antiga) continua igual' % (nome, ' e '.join(quem)),
           na_ref == [] and snap and all(sorted(r[str(k)]['mudou']) == sorted(quem) for k in (3, 40, -10)), (na_ref, snap, {k: v['mudou'] for k, v in r.items()}))
        pg.context.close()
    pg = abre(b, outro, antes=FOTO, caminho='/S1-SOS-Web.dc.html', muta=(ALVO_MUTANTE, MUTANTE_SOS))
    pg.wait_for_timeout(800)
    carga = pg.evaluate(MUDOU, list(DERIVADAS))
    ok('mutante na S1 aberta em 27/10/2026: o texto do SOS reescrito pelo rebase da carga é acusado (protocolos e embarcacao)',
       sorted(carga['mudou']) == ['embarcacao', 'protocolos'], carga['mudou'])
    pg.context.close()


def dia_de_bordo(b):
    print('Dia de bordo (microtarefa), simulacao = false e SOS')
    local = datetime(2026, 10, 27, 12, 0, tzinfo=BR)
    hoje, bordo = dias(local)
    LISTAS = """() => { const D = window.CapitaoDados; return { ab: D.abastecimentos.map((a) => [a.id || null, a.diasAtras, a.d, a.h || null, a.litros]),
      diario: D.diario.slice(0, 3).map((x) => [x.id, x.d, x.iso]), nf: D.documentos.filter((x) => x.id === 'nf-abast').map((x) => [x.ref || null, x.emitido, x.dn === undefined, x.vence === undefined, x.st]),
      ids: D.diario.map((x) => x.id), t0: D.diario[0].t, lidas: window.__lidas, lidasReplay: window.__lidasReplay, inst: window.CapitaoAgora.instante(),
      fontes: [!!window.CapitaoReplay, !!(window.CapitaoDados.snapshot && window.CapitaoDados.snapshot.quadro), !!(window.CapitaoTelemetria && window.CapitaoTelemetria.atual && window.CapitaoTelemetria.atual())], versao: D.versao, atrasadas: D.agenda.filter((t) => t.dn < 0).length }; }"""
    pg = abre(b, local, antes=DIA_DE_BORDO + GETTER)
    r = pg.evaluate(LISTAS)
    ok('simulacao true: ab-0…ab-2 em abastecimentos, com diasAtras 0, 1 e 2 e h 07:00', [a[0] for a in r['ab']] == ['ab-0', 'ab-1', 'ab-2'] and [a[1] for a in r['ab']] == [0, 1, 2]
       and all(a[3] == '07:00' and a[4] == 1086 for a in r['ab']), r['ab'])
    ok('as linhas de abastecimento com o d do dia de bordo (base dia de bordo)', [a[2] for a in r['ab']] == [br(bordo - timedelta(days=k)) for k in (0, 1, 2)], r['ab'])
    ok('d01 e d02 no topo do diário (d01 antes), sem duplicar; d01 = âncora + 1 s e d02 = âncora (07:00:00)',
       r['ids'][:3] == ['d01', 'd02', 'd03'] and len(r['ids']) == len(set(r['ids'])) and r['diario'][0][2] == '%sT07:00:01-03:00' % bordo.isoformat()
       and r['diario'][1][2] == '%sT07:00:00-03:00' % bordo.isoformat() and r['diario'][0][1] == dm(bordo), r['diario'])
    ok('a nota fiscal do dia de bordo entra por id (uma só, com ref ab-0 e o emitido do dia de bordo, sem vence nem dn)', r['nf'] == [['ab-0', br(bordo), True, True, 'CONFERIDA']], r['nf'])
    ok('fora do SOS a flag é lida (o getter conta ≥ 1: o teste do SOS vale) e, sem replay nem coletor, o instante é o da reserva (snapshot.quadro)',
       r['lidas'] >= 1 and r['inst'] is not None and r['inst']['fonte'] == 'snapshot', (r['lidas'], r['inst'] and r['inst']['fonte']))
    ok('sem erro de script', not pg.erros, pg.erros)
    pg.context.close()
    pg = abre(b, local, antes=TRANSICAO + DIA_DE_BORDO)
    r = pg.evaluate(LISTAS)
    ok('sobre linhas velhas no arquivo (d01 e a nota fiscal) a microtarefa substitui por id, sem duplicar, e ab-0…ab-2 vão para o topo',
       len(r['ids']) == len(set(r['ids'])) and r['ids'][0] == 'd01' and r['t0'].startswith('Saída às 07:00') and [a[0] for a in r['ab'][:3]] == ['ab-0', 'ab-1', 'ab-2'] and len(r['nf']) == 1
       and r['nf'][0][0] == 'ab-0', (r['ids'], r['ab'][:3], r['nf']))
    pg.context.close()
    pg = abre(b, local, antes=DIA_DE_BORDO, depois='window.CapitaoDados.simulacao = false;')
    r = pg.evaluate(LISTAS)
    ok('simulacao = false no fim do arquivo: nenhuma linha do dia de bordo (abastecimentos vazio, o diário começa na d03, sem nota fiscal)',
       r['ab'] == [] and r['ids'][0] == 'd03' and r['nf'] == [], (r['ab'], r['ids'][:3], r['nf']))
    ok('simulacao = false: o rebase roda (versão e atrasadas)', r['versao'] == br(hoje) and r['atrasadas'] == 3)
    pg.context.close()
    # Revisão do C7: com as três fontes de leitura à mão e o D.replay contado, o SOS tem de recusar todas. Só a guarda /SOS-/ do instante()
    # devolve null aqui (a mutação "sem a guarda" devolvia o replay, o coletor ou a reserva com posição); o controle fora do SOS usa a mesma fixture.
    fixture = DIA_DE_BORDO + GETTER + GETTER_REPLAY + FONTE_REPLAY + FONTE_RESERVA
    for nome, caminho, extra in (('S1-SOS-Web', '/S1-SOS-Web.dc.html', ''), ('S2-SOS-Mobile', '/S2-SOS-Mobile.dc.html', ''),
                                 ('rota mínima /SOS-teste.html', '/SOS-teste.html', FONTE_COLETOR)):
        pg = abre(b, local, antes=fixture + extra, caminho=caminho)
        pg.wait_for_timeout(800)
        r = pg.evaluate(LISTAS)
        ok('%s: as fontes de leitura estão à mão (replay, quadro de reserva%s) e o instante() é null' % (nome, ', coletor' if extra else ''),
           r['fontes'][:2] == [True, True] and (not extra or r['fontes'][2]) and r['inst'] is None, (r['fontes'], r['inst']))
        ok('%s: nenhuma linha do dia de bordo e nenhuma leitura de D.simulacao (%s) nem de D.replay (%s)' % (nome, r['lidas'], r['lidasReplay']),
           r['ab'] == [] and r['ids'][0] == 'd03' and r['nf'] == [] and r['lidas'] == 0 and r['lidasReplay'] == 0, (r['ab'][:2], r['ids'][:3], r['lidas'], r['lidasReplay']))
        ok('%s: o rebase roda (versão e 3 atrasadas)' % nome, r['versao'] == br(hoje) and r['atrasadas'] == 3)
        pg.context.close()
    pg = abre(b, local, antes=fixture + FONTE_COLETOR)
    r = pg.evaluate(LISTAS)
    ok('controle fora do SOS, com a mesma fixture: o instante() existe (coletor), D.simulacao e D.replay são lidos (≥ 1) e o dia de bordo entra',
       r['inst'] is not None and r['inst']['fonte'] == 'coletor' and r['lidas'] >= 1 and r['lidasReplay'] >= 1 and [a[0] for a in r['ab']] == ['ab-0', 'ab-1', 'ab-2'],
       (r['inst'] and r['inst']['fonte'], r['lidas'], r['lidasReplay'], r['ab'][:1]))
    ok('controle: sem o coletor o instante() vem do replay e, sem o replay, da reserva do D.snapshot.quadro',
       pg.evaluate("""() => { const A = window.CapitaoAgora, f = [];
         delete window.CapitaoTelemetria; window.__T0 += 1000; f.push(A.instante().fonte);
         delete window.CapitaoReplay; window.__T0 += 1000; f.push(A.instante().fonte); return f; }""") == ['replay', 'snapshot'])
    pg.context.close()


def sem_escrita_no_aparelho(b):
    """Revisão do C7. CONTRATO §4.1: o rodapé «não grava no localStorage nem cria linha no diário do aparelho», e a regra 14 do CLAUDE.md diz
    que o registro só cresce e que nenhuma chave capitao.* é apagada. O rodapé roda em toda página, na S1 e na S2 também: um removeItem do
    diário ou um setItem do executado na carga apagaria o registro de quem só abriu o SOS. O RODAPE_SNAPSHOT só vigia o D.snapshot e nada
    olhava o Storage (três mutantes sobreviviam). Aqui o contador do abre() separa as escritas do rodapé (pilha no capitao-dados.js)."""
    print('O rodapé não grava no aparelho (localStorage, sessionStorage, indexedDB): na carga, no uso e nos mutantes que gravam')
    local = datetime(2026, 10, 27, 12, 0, tzinfo=BR)
    fixture = DIA_DE_BORDO + GETTER + GETTER_REPLAY + FONTE_REPLAY + FONTE_RESERVA
    DIAS = [3, 40, -10, 0]
    for nome, caminho, antes, sessao in (('rota mínima, fora do SOS (o dia de bordo entra pela microtarefa)', '/rodape.html', fixture + FONTE_COLETOR, False),
                                         ('A1-Ponte-Web (tela de verdade, com sessão)', '/A1-Ponte-Web.dc.html', DIA_DE_BORDO, True),
                                         ('S1-SOS-Web', '/S1-SOS-Web.dc.html', fixture, False), ('S2-SOS-Mobile', '/S2-SOS-Mobile.dc.html', fixture, False),
                                         ('rota mínima /SOS-teste.html', '/SOS-teste.html', fixture + FONTE_COLETOR, False)):
        pg = abre(b, local, antes=antes, caminho=caminho, sessao=sessao)
        pg.wait_for_timeout(800)
        na_carga = pg.evaluate(DADOS_ESCRITAS)
        # a leitura do clima de hoje põe a trava para valer; a escrita é do teste (e conta no contador, sem ser do rodapé)
        pg.evaluate("() => localStorage.setItem('capitao.clima.v1', JSON.stringify({ em: Date.now(), dia: window.CapitaoAgora.relogio.hojeIso, max: 21, min: 15 }))")
        r = pg.evaluate(USA, [DIAS, QUADRO])
        no_uso = pg.evaluate(DADOS_ESCRITAS)
        pg.evaluate("() => { localStorage.setItem('x', '1'); localStorage.removeItem('x'); sessionStorage.setItem('x', '1'); localStorage.clear(); }")
        todas = pg.evaluate("() => window.__escritas.map((e) => e.op + ':' + e.chave + ':' + e.dados)")
        ok('%s: 0 escritas do rodapé na carga (a microtarefa e o 1º rebase incluídos)' % nome, na_carga == [], na_carga)
        ok('%s: 0 escritas do rodapé no uso (rebase forçado em +3, +40, −10 e 0 dias, contagens, trava, instante, prazoDe, docDe, fmt)' % nome,
           no_uso == [] and r['contagens']['atrasadas'] == 3 and r['trava']['temp_ar_externo_c'] == 21, (no_uso, r['contagens'], r['trava']))
        ok('%s: controle: as 4 escritas do próprio teste (setItem, removeItem, sessionStorage, clear) entram no contador e não são do rodapé' % nome,
           todas[-4:] == ['setItem:x:false', 'removeItem:x:false', 'setItem:x:false', 'clear:null:false'], todas[-5:])
        ok('%s: sem erro de script' % nome, not pg.erros, pg.erros)
        pg.context.close()
    # Mutantes: o rodapé de verdade com UMA escrita no aparelho, no ponto que o nome diz. A conferência de cima tem de acusar cada uma, com a
    # operação e a chave certas. Os da carga rodam também na S1 e na S2 (onde o estrago seria pior: apagar o diário de quem só abriu o SOS).
    MUTANTES = (
        ('removeItem do diário do aparelho na carga (S1)', '/S1-SOS-Web.dc.html', ALVO_MUTANTE, ALVO_MUTANTE + " localStorage.removeItem('capitao.diario.v1');",
         'removeItem:capitao.diario.v1'),
        ('setItem do executado do aparelho na carga (S2)', '/S2-SOS-Mobile.dc.html', ALVO_MUTANTE, ALVO_MUTANTE + " localStorage.setItem('capitao.executado.v1', '{}');",
         'setItem:capitao.executado.v1'),
        ('setItem em sessionStorage na carga', '/rodape.html', ALVO_MUTANTE, ALVO_MUTANTE + " sessionStorage.setItem('capitao.intencao', '1');", 'setItem:capitao.intencao'),
        ('localStorage.clear() na carga (/SOS-teste.html)', '/SOS-teste.html', ALVO_MUTANTE, ALVO_MUTANTE + " localStorage.clear();", 'clear:null'),
        ('indexedDB.open na carga', '/rodape.html', ALVO_MUTANTE, ALVO_MUTANTE + " indexedDB.open('capitao-teste');", 'indexedDB.open:capitao-teste'),
        ('linha "sim" no diário do aparelho pela microtarefa do dia de bordo', '/rodape.html', "if (D.simulacao === true) { insereDiaDeBordo(); rebase(Date.now(), true); }",
         "if (D.simulacao === true) { insereDiaDeBordo(); rebase(Date.now(), true); localStorage.setItem('capitao.diario.v1', '[{\"sim\":true,\"t\":\"x\"}]'); }",
         'setItem:capitao.diario.v1'),
        ('setItem da leitura do clima dentro do instante()', '/rodape.html', "try { clima = localStorage.getItem('capitao.clima.v1') || ''; } catch (e) {}",
         "try { clima = localStorage.getItem('capitao.clima.v1') || ''; localStorage.setItem('capitao.clima.v1', clima); } catch (e) {}", 'setItem:capitao.clima.v1'),
        ('setItem do diário dentro das contagens() (S2)', '/S2-SOS-Mobile.dc.html', "linhas = local('capitao.diario.v1', []), eq = [];",
         "linhas = (localStorage.setItem('capitao.diario.v1', '[]'), local('capitao.diario.v1', [])), eq = [];", 'setItem:capitao.diario.v1'),
        ('removeItem do clima dentro da trava() (S1)', '/S1-SOS-Web.dc.html', "var c = copia(q), v = local('capitao.clima.v1', null);",
         "var c = copia(q), v = (localStorage.removeItem('capitao.clima.v1'), local('capitao.clima.v1', null));", 'removeItem:capitao.clima.v1'),
        ('setItem só no rebase forçado (S2)', '/S2-SOS-Mobile.dc.html', "if (!forca && A.assinatura === assin) return false;",
         "if (!forca && A.assinatura === assin) return false; if (forca) localStorage.setItem('capitao.rebase', '1');", 'setItem:capitao.rebase'),
    )
    for nome, caminho, alvo, no_lugar, esperado in MUTANTES:
        pg = abre(b, local, antes=fixture, caminho=caminho, muta=(alvo, no_lugar))
        pg.wait_for_timeout(800)
        pg.evaluate(USA, [DIAS, QUADRO])
        lista = pg.evaluate(DADOS_ESCRITAS)
        ok('mutante (%s): a conferência acusa %s' % (nome, esperado), esperado in lista, lista)
        pg.context.close()
    # leitura estática do código (sem os comentários), de complemento: o contador de cima é a prova; o texto cai em alias
    cod = open(os.path.join(RAIZ, 'ferramentas', 'demo', 'rodape.js'), encoding='utf-8').read()
    cod = re.sub(r'/\*.*?\*/', '', cod, flags=re.S)
    cod = re.sub(r'(?m)(^|\s)//.*$', '', cod)
    achou = re.findall(r'\b(setItem|removeItem|clear|sessionStorage|indexedDB|cookie)\b', cod)
    ok('rodape.js: o código (sem os comentários) não tem setItem, removeItem, clear, sessionStorage, indexedDB nem cookie', not achou, achou)


def contagens(b):
    print('contagens()')
    local = datetime(2026, 10, 27, 12, 0, tzinfo=BR)
    hoje = local.date()
    pg = abre(b, local)
    C = lambda: pg.evaluate("() => window.CapitaoAgora.contagens()")
    ok('geradas: 3 atrasadas, 6 em 30 dias (4 da agenda e 2 da equipe), 3 em 60, 2 em 90, 2 em dia; 2 tarefas da equipe; 2 documentos vencem em 90 dias; 3 pendências',
       C() == {'atrasadas': 3, 'd30': 6, 'd60': 3, 'd90': 2, 'emDia': 2, 'docsVencidos': 0, 'docsVencem90': 2, 'pendencias': 3, 'tarefasEquipe': 2}, C())
    pg.evaluate("""() => localStorage.setItem('capitao.executado.v1', JSON.stringify({ 'porao-teste': { d: '27/10' }, g02: { d: '27/10' } }))""")
    c = C()
    ok('executadas não contam (porao-teste e a g02)', c['atrasadas'] == 2 and c['d30'] == 5 and c['tarefasEquipe'] == 1, c)
    pg.evaluate("""([a, b]) => localStorage.setItem('capitao.tarefas.v1', JSON.stringify([{ id: 'g91', n: 'x', vence: a }, { id: 'g92', n: 'y', vence: b }]))""",
                [(hoje + timedelta(days=2)).isoformat(), (hoje - timedelta(days=1)).isoformat()])
    c = C()
    ok('as tarefas do aparelho entram pela data (uma a vencer, uma atrasada)', c['atrasadas'] == 3 and c['d30'] == 6 and c['tarefasEquipe'] == 3, c)
    pg.evaluate("""() => { localStorage.removeItem('capitao.executado.v1'); localStorage.removeItem('capitao.tarefas.v1');
      localStorage.setItem('capitao.diario.v1', JSON.stringify([{ acao: 'resolve', alvo: 'd03', iso: 't2' }, { pend: true, iso: 'X1' }])); }""")
    ok('uma pendência do aparelho abre (X1) e a ação resolve fecha a d03: 3', C()['pendencias'] == 3, C())
    pg.evaluate("""() => localStorage.setItem('capitao.diario.v1', JSON.stringify([{ acao: 'reabre', alvo: 'd03', iso: 't4' }, { acao: 'resolve', alvo: 'X2', iso: 't3' }, { pend: true, iso: 'X2' },
      { acao: 'resolve', alvo: 'd03', iso: 't2' }, { pend: true, iso: 'X1' }]))""")
    ok('vale a última ação por alvo: d03 reaberta (3) + X1 aberta; X2 resolvida: 4', C()['pendencias'] == 4, C())
    pg.evaluate("""() => localStorage.setItem('capitao.diario.v1', '{ não é json')""")
    ok('registro do aparelho ilegível: conta só as geradas, sem erro', C()['pendencias'] == 3 and not pg.erros, (C(), pg.erros))
    # Revisão do C7: JSON VÁLIDO de outra forma ('{}' onde se espera lista; lista, texto ou número onde se espera mapa) valia como
    # registro e lançava no forEach/reverse; o catch externo engolia e a conta voltava zerada (docsVencem90, pendencias e tarefasEquipe 0)
    geradas = {'atrasadas': 3, 'd30': 6, 'd60': 3, 'd90': 2, 'emDia': 2, 'docsVencidos': 0, 'docsVencem90': 2, 'pendencias': 3, 'tarefasEquipe': 2}
    for chave in ('capitao.tarefas.v1', 'capitao.diario.v1', 'capitao.executado.v1'):
        for valor in ('{}', '[]', '"abc"', '5', 'true', 'null'):
            pg.evaluate("() => localStorage.clear()")
            pg.evaluate("([k, v]) => localStorage.setItem(k, v)", [chave, valor])
            c = C()
            # '{}' em executado é o mapa vazio e '[]' em tarefas/diário é a lista vazia: o próprio vazio; os outros são forma errada
            ok('%s = %s: conta só as geradas (nada zera em silêncio)' % (chave, valor), c == geradas and not pg.erros, (c, pg.erros))
    pg.evaluate("() => { localStorage.clear(); localStorage.setItem('capitao.tarefas.v1', '{}'); localStorage.setItem('capitao.diario.v1', '\"x\"'); localStorage.setItem('capitao.executado.v1', '[1]'); }")
    ok('os três registros de forma errada ao mesmo tempo: as geradas', C() == geradas, C())
    pg.evaluate("""([a]) => { localStorage.clear(); localStorage.setItem('capitao.diario.v1', '{}');
      localStorage.setItem('capitao.tarefas.v1', JSON.stringify([{ id: 'g91', n: 'x', vence: a }])); }""", [(hoje + timedelta(days=2)).isoformat()])
    c = C()
    ok('diário de forma errada não apaga a conta das tarefas do aparelho (g91 entra, as pendências geradas ficam)', c['tarefasEquipe'] == 3 and c['d30'] == 7 and c['pendencias'] == 3, c)
    pg.evaluate("""() => { localStorage.clear(); localStorage.setItem('capitao.clima.v1', '[1]'); }""")
    pg.evaluate(FONTES, QUADRO)
    ok('clima salvo de forma errada (lista) não prende o ar nem a água e não lança erro',
       pg.evaluate("() => { const i = window.CapitaoAgora.instante(); return i && i.q.temp_ar_externo_c === 22.6 && i.q.temp_agua_c === 20.1; }") and not pg.erros, pg.erros)
    pg.context.close()


QUADRO = {'timestamp_utc': '2026-10-27T15:01:00Z', 'sog_nos': 18.1, 'stw_nos': 17.9, 'motor_bb_rpm': 2049, 'motor_be_rpm': 2038, 'diesel_litros': 1333,
          'motor_bb_horimetro_h': 417.6, 'motor_be_horimetro_h': 414.8, 'gerador_horimetro_h': 1241.4, 'temp_ar_externo_c': 22.6, 'temp_agua_c': 20.1}
FONTES = """(q) => { const A = window.CapitaoAgora; window.__q = q; window.CapitaoReplay = { agora: () => Date.now(), em: () => window.__q, t: () => 60,
  fase: () => ({ nome: 'cruzeiro', ini: 50, fim: 120 }), fixo: () => '60' }; }"""


def instante_e_trava(b):
    print('instante() e a trava do ar e da água (§1.22 e §1.23, 12:01:00)')
    local = datetime(2026, 10, 27, 12, 1, 0, tzinfo=BR)
    hoje, bordo = dias(local)
    pg = abre(b, local, antes=DIA_DE_BORDO)
    pg.evaluate(FONTES, QUADRO)
    # O instante é guardado por segundo (e pela leitura do clima): cada cenário avança o relógio congelado em 1 s.
    I = lambda avanca=True: pg.evaluate("(av) => { if (av) window.__T0 += 1000; const i = window.CapitaoAgora.instante(); return i && JSON.parse(JSON.stringify(i)); }", avanca)
    clima = lambda mx, mn, dia=hoje.isoformat(): pg.evaluate("([mx, mn, dia]) => localStorage.setItem('capitao.clima.v1', JSON.stringify({ em: Date.now(), dia, max: mx, min: mn }))", [mx, mn, dia])
    i = I(False)
    ok('replay: fonte, hora, hhmm, seg, fase, fonteTxt e selo', i['fonte'] == 'replay' and i['hora'] == '12:01:00' and i['hhmm'] == '12:01' and i['seg'] == 60 and i['fase']['nome'] == 'cruzeiro'
       and i['fonteTxt'] == 'telemetria ao vivo · 12:01:00' and i['selo'] == {'tom': 'ok', 'texto': 'AO VIVO · 12:01:00'}, i)
    ok('calc: autonomia 17,6 h · 318 mn · 194 h em marcha lenta, faltam 32,4 h e 58,6 h, desde o abastecimento 227 L, diesel 83,3 %',
       i['calc']['autonomia'] == {'horas': 17.6, 'mn': 318, 'lenta': 194} and i['calc']['faltam'] == {'motores-oleo': 32.4, 'gerador-revisao': 58.6}
       and i['calc']['desdeAbast'] == {'litros': 227, 'desde': br(bordo), 'h': '07:00'} and i['calc']['diesel_pct'] == 83.3, i['calc'])
    ok('sem leitura do clima de hoje, o ar e a água ficam como vieram (22,6 e 20,1)', i['q']['temp_ar_externo_c'] == 22.6 and i['q']['temp_agua_c'] == 20.1, i['q'])
    clima(21, 15)
    q = I()['q']
    ok('com {dia: hoje, max: 21, min: 15}: ar 21,0 (preso) e água 20,1 (dentro)', q['temp_ar_externo_c'] == 21 and q['temp_agua_c'] == 20.1, q)
    clima(19, 15)
    q = I()['q']
    ok('com {max: 19, min: 15}: ar 19,0 e água 19,0 (os dois presos)', q['temp_ar_externo_c'] == 19 and q['temp_agua_c'] == 19, q)
    clima(19, 15, (hoje - timedelta(days=1)).isoformat())
    ok('leitura de ontem: nada muda', I()['q']['temp_ar_externo_c'] == 22.6)
    clima(19, 15)
    ok('o quadro de origem não é mutado (a trava devolve cópia)', pg.evaluate("() => window.__q.temp_ar_externo_c === 22.6 && window.__q.temp_agua_c === 20.1"))
    ok('instante() devolve o mesmo objeto no mesmo segundo (guardado) e um novo no segundo seguinte',
       pg.evaluate("() => { const a = window.CapitaoAgora.instante(), b = window.CapitaoAgora.instante(); window.__T0 += 1000; return a === b && window.CapitaoAgora.instante() !== a; }"))
    pg.evaluate("() => { window.CapitaoDados.simulacao = false; }")
    ok('com simulacao false o quadro não é preso', I()['q']['temp_ar_externo_c'] == 22.6 and I()['q']['temp_agua_c'] == 20.1)
    pg.evaluate("() => { window.CapitaoDados.simulacao = true; }")
    pg.evaluate("() => { window.CapitaoTelemetria = { atual: () => Object.assign({}, window.__q, { simulado: true }) }; }")
    ok('CapitaoTelemetria.atual() com simulado: true vale como replay (e é presa)', I()['fonte'] == 'replay' and I()['q']['temp_ar_externo_c'] == 19, I())
    pg.evaluate("() => { window.CapitaoTelemetria = { atual: () => Object.assign({}, window.__q) }; }")
    i = I()
    ok('coletor real (sem simulado): fonte coletor, "coletor NMEA · ao vivo 12:01:SS" e a leitura nunca é presa (22,6)',
       i['fonte'] == 'coletor' and i['fonteTxt'] == 'coletor NMEA · ao vivo ' + i['hora'] and i['hora'].startswith('12:01:') and i['q']['temp_ar_externo_c'] == 22.6 and 'seg' not in i, i)
    pg.evaluate("() => { delete window.CapitaoTelemetria; delete window.CapitaoReplay; }")
    ok('sem replay nem coletor, o instante é o do D.snapshot.quadro que o gerador grava (C8): fonte snapshot, 848 L, ÚLTIMA LEITURA 26/09 10:12',
       (lambda i: i['fonte'] == 'snapshot' and i['q']['diesel_litros'] == 848 and i['selo']['texto'] == 'ÚLTIMA LEITURA · 26/09 10:12')(I()), pg.erros)
    pg.evaluate("() => { delete window.CapitaoDados.snapshot.quadro; }")
    ok('sem nenhuma fonte (nem quadro de reserva): null, sem erro', I() is None and not pg.erros, pg.erros)
    pg.evaluate("""() => { window.CapitaoDados.snapshot.quadro = { timestamp_utc: '2026-09-26T13:12:00Z', diesel_litros: 848, temp_ar_externo_c: 22.6, temp_agua_c: 20.1 }; }""")
    i = I()
    ok('reserva do D.snapshot.quadro: fonte snapshot, hora 10:12:00 do fuso, "leitura de 26/09 10:12" e selo ÚLTIMA LEITURA',
       i['fonte'] == 'snapshot' and i['hora'] == '10:12:00' and i['fonteTxt'] == 'coletor NMEA · leitura de 26/09 10:12'
       and i['selo'] == {'tom': 'warn', 'texto': 'ÚLTIMA LEITURA · 26/09 10:12'} and i['q']['temp_ar_externo_c'] == 19, i)
    ok('a reserva não é mutada pelo instante (o ar do quadro continua 22,6)', pg.evaluate("() => window.CapitaoDados.snapshot.quadro.temp_ar_externo_c === 22.6"))
    ok('sem erro de script', not pg.erros, pg.erros)
    pg.context.close()
    pg = abre(b, local)
    i = pg.evaluate("() => { const i = window.CapitaoAgora.instante(); return i && JSON.parse(JSON.stringify(i)); }")
    ok('sem replay e sem coletor, o instante vem da reserva do D.snapshot.quadro do C8 (fonte snapshot, ÚLTIMA LEITURA 26/09 10:12, sem erro)',
       i and i['fonte'] == 'snapshot' and i['selo'] == {'tom': 'warn', 'texto': 'ÚLTIMA LEITURA · 26/09 10:12'} and i['q']['diesel_litros'] == 848 and not pg.erros, (i, pg.erros))
    pg.context.close()


def formatadores(b):
    print('Formatadores e fuso')
    pg = abre(b, datetime(2026, 10, 27, 12, 0, tzinfo=BR))
    pg.evaluate("""() => { window.CapitaoDados.campos = { x: { casas: 1, mil: true }, y: { casas: 0 }, z: { casas: 0, ang: true } }; }""")
    r = pg.evaluate("""() => { const f = window.CapitaoAgora.fmt, A = window.CapitaoAgora;
      return { arred: [f.arred(1.25, 1), f.arred(-0.04, 1), f.arred(2.675, 2), f.arred(0.5, 0)], nb: [f.nb(1017.1, 1, true), f.nb(-0.04, 1), f.nb(1333, 0, true), f.nb(83.3125, 1), f.nb(12.5, 0), f.nb(null, 1), f.nb(NaN, 1)],
        mil: [f.mil(1236.4), f.mil(2049)], g3: [f.grau3(59), f.grau3(-1), f.grau3(359.6), f.grau3(5), f.grau3(null)],
        hora: [f.hora(Date.UTC(2026, 9, 27, 15, 1, 5)), f.hora(Date.UTC(2026, 9, 27, 15, 1, 5), true), f.hora(Date.UTC(2026, 9, 27, 2, 59, 59), true)],
        coord: [f.coord(-26.993, -48.614), f.coord(-26.99999, -48.99999), f.coord(10.5, 5.25)],
        campo: [f.campo({ x: 1017.14 }, 'x'), f.campo({ y: 2049.4 }, 'y'), f.campo({ z: 59 }, 'z'), f.campo({}, 'x'), f.campo({ marcha: 'avante' }, 'marcha'), f.campo(null, 'x'), f.campo({ q: 7.26 }, 'q')],
        off: A.off(Date.UTC(2026, 9, 27, 12)), fuso: A.fuso }; }""")
    ok('arred: floor(x·10^c + 0,5)/10^c, sem -0', r['arred'] == [1.3, 0, 2.68, 1], r['arred'])
    ok('nb: vírgula, milhar com ponto, null para o que não é número', r['nb'] == ['1.017,1', '0,0', '1.333', '83,3', '13', None, None], r['nb'])
    ok('mil e grau3', r['mil'] == ['1.236', '2.049'] and r['g3'] == ['059', '359', '000', '005', None], (r['mil'], r['g3']))
    ok('hora no fuso (UTC−3), com e sem segundos; a virada do dia UTC', r['hora'] == ['12:01', '12:01:05', '23:59:59'], r['hora'])
    ok('coord: graus e minutos com vírgula; 59,995′ já é o grau seguinte', r['coord'] == ["26°59,58'S 048°36,84'W", "27°00,00'S 049°00,00'W", "10°30,00'N 005°15,00'E"], r['coord'])
    ok('campo: pelo catálogo (casas, mil, ang); texto como veio; null se falta; sem catálogo, inteiro', r['campo'] == ['1.017,1', '2049', '059', None, 'avante', None, '7'], r['campo'])
    ok('fuso e deslocamento (America/Sao_Paulo, −180 min)', r['fuso'] == 'America/Sao_Paulo' and r['off'] == -180, (r['fuso'], r['off']))
    ok('sem erro de script', not pg.erros, pg.erros)
    pg.context.close()


def casos_nivel(D):
    """(campo, q) para a paridade da nivel: os 150 quadros do laço (cada campo com limite) e os casos de borda do §3.3 de cada limite (valor =
    limite → o normal; limite ± 1 unidade da última casa → o nível de fora; rpm 999 e 1.000 nos regimes do óleo; o ativo_se desligado → null)."""
    R, cam = D['replay'], D['campos']
    out = [(c, C.quadro_laco(R, cam, t)) for t in range(R['duracao']) for c in R['limites']]
    for campo, L in R['limites'].items():
        un = 10 ** -C.casas_de(cam, campo)
        a = L.get('ativo_se') or {}
        for Rg in L.get('regimes') or [L]:
            base = {}
            if a.get('campo'):
                base[a['campo']] = a['acima'] + 1 if 'acima' in a else a['igual']
            if 'rpm_campo' in Rg:
                base[Rg['rpm_campo']] = Rg['rpm_ate'] - 1 if 'rpm_ate' in Rg else Rg.get('rpm_de', 0)
                if a.get('campo') == Rg['rpm_campo'] and 'acima' in a and base[Rg['rpm_campo']] <= a['acima']:
                    base[Rg['rpm_campo']] = a['acima'] + 1
            for k in ('normal', 'aviso', 'critico'):
                for lim in (Rg.get(k) or {}).values():
                    for v in (lim, lim - un, lim + un):
                        out.append((campo, dict(base, **{campo: round(v, 6)})))
        for rpm in (0, 999, 1000):   # a fronteira dos regimes e o motor parado
            for Rg in L.get('regimes') or []:
                out.append((campo, {Rg['rpm_campo']: rpm, campo: 3.0}))
        if a.get('campo'):
            off = a['acima'] if 'acima' in a else (not a['igual'])   # ativo_se desligado: não avalia
            out.append((campo, {a['campo']: off, campo: 0}))
        out.append((campo, {}))   # campo ausente: não avalia
        out.append((campo, {campo: None}))
    return out


def paridade_nivel(b):
    print('CapitaoAgora.nivel() contra o port em Python (confere.nivel): nos 150 quadros do laço e nos casos de borda do §3.3')
    D = G.dados()
    casos = casos_nivel(D)
    pg = abre(b, datetime(2026, 10, 27, 12, 0, tzinfo=BR))
    js = pg.evaluate("(casos) => casos.map(([c, q]) => window.CapitaoAgora.nivel(c, q))", casos)
    py = [C.nivel(D['replay']['limites'], D['campos'], c, q) for c, q in casos]
    difs = [(c, q, a, e) for (c, q), a, e in zip(casos, js, py) if json.loads(json.dumps(a)) != json.loads(json.dumps(e))]
    n_av = sum(1 for e in py if e and e['nivel'] == 'aviso')
    ok('nivel(): JS = Python em %d casos (%d avisos, %d sem avaliação, %d normais)' % (len(casos), n_av, sum(1 for e in py if e is None), sum(1 for e in py if e and e['nivel'] == 'normal')),
       not difs and len(casos) > 3000 and n_av > 0, difs[:3])
    # a janela do AVISO de arrefecimento do BE, pelo JS, nos valores do laço: 99 a 116 s (CONTRATO §3.4)
    jan = [t for t in range(D['replay']['duracao']) if (pg.evaluate("(q) => window.CapitaoAgora.nivel('motor_be_arref_c', q)", C.quadro_laco(D['replay'], D['campos'], t)) or {}).get('nivel') == 'aviso']
    ok('nivel(): motor_be_arref_c em aviso de 99 a 116 s (18 s contínuos), pelo JS', jan == list(range(99, 117)), jan)
    ok('nivel(): campo sem limite, quadro ausente e valor que não é número dão null', pg.evaluate(
        "() => { const n = window.CapitaoAgora.nivel; return [n('lat', { lat: 1 }), n('motor_be_arref_c', null), n('motor_be_arref_c', { motor_be_rpm: 2000, motor_be_arref_c: 'x' })]; }") == [None, None, None])
    ok('sem erro de script', not pg.erros, pg.erros)
    pg.context.close()
    # Em /SOS-/ a nivel não lê o replay (nenhuma leitura de D.replay)
    pg = abre(b, datetime(2026, 10, 27, 12, 0, tzinfo=BR), antes=GETTER_REPLAY, caminho='/SOS-teste.html')
    r = pg.evaluate("() => [window.CapitaoAgora.nivel('motor_be_arref_c', { motor_be_rpm: 2000, motor_be_arref_c: 95 }), window.__lidasReplay]")
    ok('em /SOS-/ a nivel devolve null e nunca lê o D.replay', r == [None, 0], r)
    pg.context.close()


def telas(b):
    print('Telas com o rodapé (Date congelado em 27/10/2026 12:00): "prazos a partir de" = hoje e a falta de registro que saiu')
    local = datetime(2026, 10, 27, 12, 0, tzinfo=BR)
    for tela, app, desde in (('C1-Leme-Web', False, 'prazos contados a partir de 27/10/2026'), ('C2-Leme-Mobile', True, 'prazos a partir de 27/10/2026'),
                             ('B1-Carta-Web', False, 'prazos contados a partir de 27/10/2026'), ('G1-Documentos-Web', False, 'prazos contados a partir de 27/10/2026'),
                             ('G1-Documentos-Mobile', True, 'prazos a partir de 27/10/2026'), ('A1-Ponte-Web', False, None), ('G3-Diario-Web', False, None),
                             ('G4-Equipe-Web', False, None)):
        pg = abre(b, local, caminho='/%s.dc.html' % tela, sessao=True, tela='app' if app else None)
        pg.wait_for_timeout(1800)
        txt = pg.evaluate("() => document.body.innerText")
        ok('%s: sem erro de script' % tela, not pg.erros, pg.erros)
        if desde:
            ok('%s: "%s"' % (tela, desde), desde in txt, [l for l in txt.split('\n') if 'a partir de' in l][:2])
        ruins = [x for x in ('Falta registrar: .', 'FALTA REGISTRAR · nada', 'falta registrar: nada', 'SEM DADOS: .', '[object Object]') if x in txt]
        ok('%s: sem "falta registrar" vazio (a agendaFalta saiu) nem [object Object]' % tela, not ruins and (not tela.startswith(('C1', 'C2')) or 'FALTA REGISTRAR' not in txt), ruins)
        if tela.startswith('C1'):
            ok('%s: as 14 tarefas, com o autoteste do EPIRB e a inspeção do sistema fixo' % tela, '14 tarefas' in txt, [l for l in txt.split('\n') if 'tarefas' in l][:2])
        if tela.startswith('C2'):
            ok('%s: as 3 atrasadas (porão, filtro da climatização, rotor do gerador) com as datas de hoje' % tela,
               all(x in txt for x in ('vence 02/10/2026', 'vence 11/10/2026', 'vence 25/10/2026')) and '25 dias atrás' in txt, txt[:300])
        if tela == 'B1-Carta-Web':
            ok('B1-Carta-Web: a linha da manutenção sem "falta registrar: nada"', '14 tarefas' in txt, [l for l in txt.split('\n') if 'tarefas' in l][:2])
        if tela == 'A1-Ponte-Web':
            # revisão do C7: o "O que vence" lista a agenda inteira e escrevia "vence 09/11" (autoteste do EPIRB, +13) e "vence 16/03" (inspeção do
            # sistema fixo, +140) na linha e na dica; a data deles só em Equipamentos, Leme e Documentos (§1.4); o chip D-n e a nota da etiqueta ficam
            todo = pg.evaluate("() => [document.body.innerText].concat([...document.querySelectorAll('[title]')].map((e) => e.getAttribute('title'))).join('\\n')")
            ok('A1-Ponte-Web: o autoteste do EPIRB e a inspeção do sistema fixo sem a data (linha e dica), com o D-13 e o D-140',
               not any(x in todo for x in ('09/11', '16/03')) and 'EPIRB' in txt and 'D-13' in txt and 'D-140' in txt, [l for l in todo.split('\n') if 'EPIRB' in l or 'supress' in l][:4])
            ok('A1-Ponte-Web: a dica das duas linhas leva a nota da etiqueta', todo.count('modelo, validade e acionamento: veja a etiqueta do equipamento') == 2,
               todo.count('modelo, validade e acionamento: veja a etiqueta do equipamento'))
        pg.context.close()
    # Revisão do C7: a nota fiscal do abastecimento (sem prazo, st CONFERIDA, CONTRATO §1.8) caía no grupo SEM DADOS da G1: situação e validade
    # "SEM DADOS", "1 SEM DADOS" no resumo e o bloco FALTA REGISTRAR com a nota. Decisão (b): nenhum selo em dado de bordo. Duas formas: o arquivo
    # gerado de antes do C8 (a nota em documentos) e a do C8 (a nota entra pela microtarefa, junto com ab-0 e d01/d02): hoje só a segunda existe.
    NF = """() => {
      const nome = 'Nota fiscal do abastecimento', outros = ['Seguro da embarcação', 'Licença de Estação', 'Laudo de vistoria', 'Garantia do estabilizador', 'Certificado do EPIRB'];
      return [...document.querySelectorAll('*')].filter((x) => x.children.length === 0 && x.textContent.trim() === nome).map((e) => {
        while (e.parentElement && !outros.some((o) => e.parentElement.innerText.includes(o))) e = e.parentElement;   // a linha: o maior bloco que só tem esta nota
        return e.innerText; }); }"""
    for tela, app in (('G1-Documentos-Web', False), ('G1-Documentos-Mobile', True)):
        for modo, antes in (('nota fiscal pela microtarefa, do replay.diaDeBordo gerado', ''),):
            pg = abre(b, local, antes=antes, caminho='/%s.dc.html' % tela, sessao=True, tela='app' if app else None)
            pg.wait_for_timeout(1800)
            linhas, txt = pg.evaluate(NF), pg.evaluate("() => document.body.innerText")
            ok('%s (%s): a linha da nota fiscal diz CONFERIDA, sem SEM DADOS na situação nem na validade' % (tela, modo),
               len(linhas) >= 1 and any('CONFERIDA' in l for l in linhas) and not any('SEM DADOS' in l for l in linhas), linhas)
            ok('%s (%s): nenhum documento SEM DADOS (resumo e filtro com 0) e sem o bloco FALTA REGISTRAR' % (tela, modo),
               'FALTA REGISTRAR' not in txt and not re.search(r'[1-9]\d*\s+SEM DADOS', txt), [l for l in txt.split('\n') if 'SEM DADOS' in l or 'FALTA' in l][:3])
            ok('%s (%s): sem erro de script' % (tela, modo), not pg.erros, pg.erros)
            pg.context.close()
    snapshot_sem_null(b, local)


# Revisão do C8 (linha C8 do §6.2: «sem [object Object]; G2 com as 3 linhas»). O snapshot sem null deu OBJETO ao porão ({bb_cm, be_cm, ciclos_h}) e à
# âncora ({estado, cabo_m}); a B2 escrevia 'porão: ' + S.porao e as duas F3 String(S.ancora) ([object Object] na tela). As três guardas de 1 linha
# (B2:158, F3-Web:222, F3:216) entraram sem teste: tirá-las não acusava nada (53 verificações do verificar.py, 0 falhas). Aqui cada leitor abre com o
# dado gerado de verdade e o texto da tela e os `title` não têm [object Object]; o valor certo aparece (o objeto virou texto, não sumiu).
TITULOS = "() => document.body.innerText + '\\n' + [...document.querySelectorAll('[title]')].map((e) => e.getAttribute('title')).join('\\n')"
SNAPSHOT_TELAS = (   # (tela, app, o que a tela tem de mostrar[, o que não pode aparecer em texto nem em title])
    ('B2-Carta-Mobile', True, ('porão: BB 1,2 cm · BE 0,9 cm',)),
    ('F3-FAQ-Eletronicos', True, ('Posição do ferro (âncora)', 'LANÇADA · 30 m')),
    ('F3-FAQ-Eletronicos-Web', False, ('Posição do ferro (âncora)', 'LANÇADA · 30 m')),
    ('A1-Ponte-Web', False, ('BB 1,2 · BE 0,9 cm', 'lançada · 30 m'), ('Nenhum sensor',)),   # A1:328-329 já tratavam objeto no valor mas a dica fixa dizia «Nenhum sensor» ao lado de «na rede»
    ('A2-Ponte-Mobile', True, ()),
    ('E1-Navegando-Gatilhos', False, ()),
    ('G2-Abastecimento-Web', False, ('3 registros', '27/10/2026', '26/10/2026', '25/10/2026', '97,5 %'), ('97.5',)),   # revisão do C8 (nivelDepois): o nível depois do abastecimento é 97,5 (float); as telas concatenavam o número cru («97.5 %»)
    ('G2-Abastecimento-Mobile', True, ('97,5 %',), ('97.5',)),
    ('B1-Carta-Web', False, ('1.086 L diesel · ≈ 97,5 % depois',), ('97.5',)),
)


# Revisão do C8 (A1): o chip Porão e o Âncora do Mapa de sensores trocaram de «SEM LEITURA» para «na rede» quando o snapshot ganhou o objeto, mas a dica (`title`) era
# fixa na linha («Nenhum sensor de porão na rede no snapshot»), ao lado de «na rede» e de um ponto verde; o chip também perdia o valor. O teste olhava só o
# [object Object] e não via a contradição. Aqui cada chip: o valor no texto, a dica sem «Nenhum sensor».
CHIPS_A1 = """() => [...document.querySelectorAll('[title]')].filter((e) => /^(Porão|Âncora)\\b/.test(e.innerText.trim())).map((e) => [e.innerText.replace(/\\s+/g, ' ').trim(), e.getAttribute('title')])"""


def snapshot_sem_null(b, local):
    for tela, app, deve, *resto in SNAPSHOT_TELAS:
        pg = abre(b, local, caminho='/%s.dc.html' % tela, sessao=True, tela='app' if app else None)
        pg.wait_for_timeout(1800)
        todo = pg.evaluate(TITULOS)
        ok('%s: sem erro de script' % tela, not pg.erros, pg.erros)
        ok('%s: sem [object Object] no texto nem nos title' % tela, '[object Object]' not in todo, [l for l in todo.split('\n') if 'object' in l][:3])
        if deve:
            falta = [x for x in deve if x not in todo]
            ok('%s: mostra %s' % (tela, ' · '.join(deve)), not falta, falta)
        if resto and resto[0]:
            tem = [x for x in resto[0] if x in todo]
            ok('%s: sem %s no texto nem nos title' % (tela, ' · '.join('«%s»' % x for x in resto[0])), not tem, [l for l in todo.split('\n') if any(x in l for x in tem)][:3])
        if tela == 'A1-Ponte-Web':
            chips = pg.evaluate(CHIPS_A1)
            ok('%s: os chips Porão e Âncora mostram o valor (BB 1,2 · BE 0,9 cm; lançada · 30 m) e a dica não diz «Nenhum sensor»' % tela,
               len(chips) == 2 and 'BB 1,2 · BE 0,9 cm' in chips[0][0] and 'lançada · 30 m' in chips[1][0] and not any('Nenhum sensor' in t for _, t in chips)
               and all(' na rede · ' in t for _, t in chips), chips)
        if tela.startswith('G2'):   # as 3 linhas de abastecimento do dia de bordo (ab-0…ab-2): 07:00, 1.086 L cada, a nota fiscal conferida (§1.9, §1.10)
            litros = '\n1.086 L\n' if not app else ' · 1.086 L\n'   # a web põe os litros numa coluna; o app, na linha «27/10/2026 · 1.086 L»
            ok('%s: as 3 linhas do histórico, cada uma com 1.086 L e a saída das 07:00' % tela,
               todo.count('para a saída das 07:00 · nota fiscal conferida (Documentos)') == 3 and todo.count(litros) >= 3,
               (todo.count('para a saída das 07:00 · nota fiscal conferida (Documentos)'), todo.count(litros)))
        pg.context.close()


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel=CANAL, headless=True)
        relogio_e_listas(b)
        idempotencia(b)
        so_o_derivado(b)
        dia_de_bordo(b)
        sem_escrita_no_aparelho(b)
        contagens(b)
        instante_e_trava(b)
        formatadores(b)
        paridade_nivel(b)
        telas(b)
        b.close()
    print('%d conferências · %d falhas' % (total, falhas))
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
