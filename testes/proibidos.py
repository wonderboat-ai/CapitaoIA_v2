# -*- coding: utf-8 -*-
"""Capitão IA — a lista única de termos (PROMPT §3) e o grep final (PROMPT Fase 7).

O que confere:
  1. arquivos: testes/proibidos.json e testes/proibidos-casos.json são cópia da fonte única
     (ferramentas/prompts/clone-avanti-1.1.0/termos.json e termos-casos.json); são 8 regex, cada uma com `src` e `flags`;
  2. regras de escrita: nenhuma fonte com lookbehind `(?<`; `\\w` só na PESSOAIS (e-mail), nunca para palavra em português;
     ROTULOS, VAZIOS e ANEXO sem a flag `i`;
  3. os casos (barra e passa) em Python e, no navegador, contra o CapitaoBrain.TERMOS — os dois têm de dar o mesmo;
  4. as mesmas fontes no cérebro (B.TERMOS_FONTES), no cliente da IA (as duas cópias, window.CapitaoIA.TERMOS_FONTES)
     e nos dois Workers (texto «CHAVE: { src: '…', flags: '…' }»);
  5. capitao-brain.js e capitao-ia.js (as duas cópias) sem `(?<` (iOS < 16.4: SyntaxError e o cérebro não carrega);
  6. o grep final: cada regex, com a flag dela, em cada linha dos arquivos publicados (lista em ARQUIVOS_GREP). Cada
     casamento cai numa de três classes:
       EXCEÇÃO      — a lista EXCECOES do PROMPT §3 (comentário de código, identificador, rótulo dos anexos, literal do
                      ramo `simulacao: false` com a guarda na mesma linha…);
       JUSTIFICADO  — fora da lista do PROMPT, com motivo escrito aqui (JUSTIFICADOS e PONTUAIS): é o «restante, com
                      arquivo:linha, que vai para a PARIDADE.md» (`--lista` imprime todos);
       RESTO        — nenhum dos dois: reprova, com arquivo:linha.
     A ferramenta de busca do editor (ripgrep) não serve: recusa o lookahead que VAZIOS e ANEXO usam.
  7. autoteste do grep: defeitos plantados (um rótulo na marcação, num texto de tela sem guarda, num dado gerado) têm de
     cair no RESTO, e o comentário, o identificador e o literal com guarda têm de cair na exceção.

Uso (não precisa do site servido: o navegador lê os arquivos desta árvore):
    python -X utf8 testes/proibidos.py              tudo (testes + grep final)
    python -X utf8 testes/proibidos.py --so-testes  sem o grep final
    python -X utf8 testes/proibidos.py --grep-final só o grep final (sem navegador)
    ... --lista                                     imprime também cada JUSTIFICADO, com arquivo:linha (para a PARIDADE.md)
    ... -v                                          imprime também cada conferência que passou
Sai com 1 se houver falha ou RESTO.
Navegador: Edge instalado (Playwright com channel="msedge").
"""
import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROIBIDOS = os.path.join(RAIZ, 'testes', 'proibidos.json')
CASOS = os.path.join(RAIZ, 'testes', 'proibidos-casos.json')
FONTE_UNICA = os.path.join(RAIZ, 'ferramentas', 'prompts', 'clone-avanti-1.1.0')
CANAL = 'msedge'
ORIGEM = 'https://capitao.teste/'   # origem de mentira: os arquivos saem desta árvore pelo `route` (nada vai à rede)

NOMES = ('ROTULOS', 'AUTENTICIDADE', 'DINHEIRO', 'PESSOAIS', 'LOCAL_SEGURANCA', 'VAZIOS', 'VISIVEL', 'ANEXO')
SEM_I = ('ROTULOS', 'VAZIOS', 'ANEXO')
FILTRO = ('ROTULOS', 'AUTENTICIDADE', 'DINHEIRO', 'PESSOAIS', 'LOCAL_SEGURANCA')   # as 5 do filtro de saída da IA (cliente e Workers)
WORKERS = ('integracoes/workers-ai/ia-worker/worker.js', 'integracoes/claude-api/ia-worker/worker.js')
CLIENTES = ('capitao-ia.js', 'integracoes/ia-cliente/capitao-ia.js')
SEM_LOOKBEHIND = ('capitao-brain.js',) + CLIENTES
SCRIPTS_CEREBRO = ('capitao-dados.js', 'capitao-replay.js', 'capitao-alertas.js', 'capitao-telemetria.js', 'capitao-brain.js')

FALHAS = []
FEITAS = []


def conta(nome, ok, extra=''):
    FEITAS.append(nome)
    if not ok:
        FALHAS.append(nome)
        print('FALHA', nome, str(extra)[:600])
    elif '-v' in sys.argv:
        print('ok   ', nome)
    return ok


def ler(p):
    with open(os.path.join(RAIZ, p), encoding='utf-8') as f:
        return f.read()


def compila(v):
    assert set(v['flags']) <= set('i'), 'flag fora do previsto: %r' % v['flags']
    return re.compile(v['src'], re.I if 'i' in v['flags'] else 0)


def carrega(caminho=PROIBIDOS):
    with open(caminho, encoding='utf-8') as f:
        T = json.load(f)
    return {k: v for k, v in T.items() if isinstance(v, dict) and 'src' in v}


# ——————————————————————————————— 1 a 5: a lista única ———————————————————————————————
def confere_arquivos(T):
    conta('lista: as 8 regex do §3 (ROTULOS, AUTENTICIDADE, DINHEIRO, PESSOAIS, LOCAL_SEGURANCA, VAZIOS, VISIVEL, ANEXO), cada uma com src e flags',
          sorted(T) == sorted(NOMES) and all(isinstance(v.get('src'), str) and v['src'] and isinstance(v.get('flags'), str) for v in T.values()), sorted(T))
    for nome, copia in (('termos.json', PROIBIDOS), ('termos-casos.json', CASOS)):
        fonte = os.path.join(FONTE_UNICA, nome)
        with open(fonte, encoding='utf-8') as a, open(copia, encoding='utf-8') as b:
            conta('lista: testes/%s é cópia da fonte única (%s)' % (os.path.basename(copia), nome), json.load(a) == json.load(b), nome)
    conta('escrita: nenhuma fonte usa lookbehind «(?<» (iOS < 16.4)', not [k for k, v in T.items() if '(?<' in v['src']], [k for k, v in T.items() if '(?<' in v['src']])
    conta('escrita: «\\w» só na PESSOAIS (o e-mail); palavra em português vai com [A-Za-zÀ-ÿ]', [k for k, v in T.items() if '\\w' in v['src']] == ['PESSOAIS'], [k for k, v in T.items() if '\\w' in v['src']])
    conta('escrita: ROTULOS, VAZIOS e ANEXO sem a flag «i»; as outras com ela', all((T[k]['flags'] == '') == (k in SEM_I) and T[k]['flags'] in ('', 'i') for k in T), {k: T[k]['flags'] for k in T})


def casos_python(T, casos):
    RX = {k: compila(v) for k, v in T.items()}
    nao_barra = [(k, s) for k, frases in casos['barra'].items() for s in frases if not RX[k].search(s)]
    passa = [(s, [k for k in RX if k != 'ANEXO' and RX[k].search(s)]) for s in casos['passa']]
    passa = [x for x in passa if x[1]]
    n = sum(len(v) for v in casos['barra'].values())
    conta('casos (Python): as %d frases da «barra» casam a regex indicada' % n, not nao_barra and sorted(casos['barra']) == sorted(NOMES), nao_barra[:4])
    conta('casos (Python): nenhuma das %d frases da «passa» casa regex alguma (fora a ANEXO: A CONFERIR / A CONFIRMAR é o rótulo dos anexos)' % len(casos['passa']), not passa, passa[:4])
    return {'barra': {k: [bool(RX[k].search(s)) for s in frases] for k, frases in casos['barra'].items()},
            'passa': [[k for k in NOMES if RX[k].search(s)] for s in casos['passa']]}


R_FONTE_JS = r"\n\s+%s: \{ src: '((?:[^'\\]|\\.)*)', flags: '([a-z]*)' \}"


def fontes_no_texto(s):
    """As fontes escritas num arquivo JS («CHAVE: { src: '…', flags: '…' }», a forma do CapitaoBrain.TERMOS_FONTES)."""
    out = {}
    for k in NOMES:
        m = re.search(R_FONTE_JS % k, s)
        if m:
            out[k] = {'src': m.group(1).replace('\\\\', '\\').replace("\\'", "'"), 'flags': m.group(2)}
    return out


def confere_fontes_texto(T, textos=None):
    """Os dois Workers (só rodam na Cloudflare: aqui, o texto). `textos`: {arquivo: conteúdo}, para o autoteste."""
    textos = textos if textos is not None else {p: ler(p) for p in WORKERS}
    ruins = []
    for p, s in textos.items():
        F = fontes_no_texto(s)
        if sorted(F) != sorted(FILTRO):
            ruins.append((p, 'chaves', sorted(F)))
        ruins += [(p, k) for k in F if F[k] != {'src': T[k]['src'], 'flags': T[k]['flags']}]
    return ruins


JS_CEREBRO = """([barra, passa, nomes]) => { const B = window.CapitaoBrain, T = B.TERMOS || {}, F = B.TERMOS_FONTES || {};
  return { fontes: Object.keys(F).map((k) => [k, F[k].src, F[k].flags]), regex: Object.keys(T).map((k) => [k, T[k] instanceof RegExp, T[k].source === new RegExp(F[k].src, F[k].flags).source, T[k].flags]),
    barra: Object.fromEntries(Object.keys(barra).map((k) => [k, barra[k].map((s) => !!(T[k] && new RegExp(T[k].source, T[k].flags).test(s)))])),
    passa: passa.map((s) => nomes.filter((k) => T[k] && new RegExp(T[k].source, T[k].flags).test(s))) }; }"""


def no_navegador(T, casos, py):
    from playwright.sync_api import sync_playwright
    tipos = {'.js': 'application/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8', '.html': 'text/html; charset=utf-8'}

    def entrega(route):
        url = route.request.url
        if not url.startswith(ORIGEM):
            return route.abort('internetdisconnected')
        arq = os.path.normpath(os.path.join(RAIZ, url[len(ORIGEM):].split('?')[0].split('#')[0]))
        if not arq.startswith(RAIZ) or not os.path.isfile(arq):
            return route.fulfill(status=404, body='')
        with open(arq, 'rb') as f:
            route.fulfill(body=f.read(), content_type=tipos.get(os.path.splitext(arq)[1], 'application/octet-stream'))

    with sync_playwright() as p:
        b = p.chromium.launch(channel=CANAL, headless=True)
        ctx = b.new_context(service_workers='block')
        ctx.route('**/*', entrega)
        pg = ctx.new_page()
        erros = []
        pg.on('pageerror', lambda e: erros.append(str(e)))
        pg.goto(ORIGEM + 'testes/proibidos.json')
        for arq in SCRIPTS_CEREBRO:
            pg.add_script_tag(url=ORIGEM + arq)
        r = pg.evaluate(JS_CEREBRO, [casos['barra'], casos['passa'], list(NOMES)])
        conta('cérebro: B.TERMOS traz as 8 regex (RegExp) feitas das fontes de B.TERMOS_FONTES, com a flag de cada uma',
              sorted(k for k, *_ in r['regex']) == sorted(NOMES) and all(e and mesma and fl.replace('g', '') == T[k]['flags'] for k, e, mesma, fl in r['regex']), r['regex'])
        conta('cérebro: as fontes e as flags de B.TERMOS_FONTES são as do testes/proibidos.json', sorted(r['fontes']) == sorted([k, T[k]['src'], T[k]['flags']] for k in T),
              [k for k, s, f in r['fontes'] if k not in T or T[k]['src'] != s or T[k]['flags'] != f])
        conta('casos (navegador, CapitaoBrain.TERMOS): a «barra» inteira casa e a «passa» não casa (fora a ANEXO)',
              all(all(v) for v in r['barra'].values()) and not [x for x in r['passa'] if [k for k in x if k != 'ANEXO']],
              ([(k, casos['barra'][k][i]) for k, v in r['barra'].items() for i, ok in enumerate(v) if not ok][:3], [(casos['passa'][i], x) for i, x in enumerate(r['passa']) if [k for k in x if k != 'ANEXO']][:3]))
        conta('casos: o JavaScript e o Python dão o mesmo resultado em cada frase (barra e passa, as 8 regex)', r['barra'] == py['barra'] and r['passa'] == py['passa'],
              [(k, casos['barra'][k][i]) for k in py['barra'] for i in range(len(py['barra'][k])) if r['barra'].get(k, [])[i:i + 1] != [py['barra'][k][i]]][:3]
              + [(casos['passa'][i], r['passa'][i], py['passa'][i]) for i in range(len(py['passa'])) if r['passa'][i] != py['passa'][i]][:3])
        conta('cérebro: carregou sem erro de script', not erros, erros[:2])
        for cliente in CLIENTES:
            pc = ctx.new_page()
            errs = []
            pc.on('pageerror', lambda e, errs=errs: errs.append(str(e)))
            pc.goto(ORIGEM + 'testes/proibidos.json')
            pc.add_script_tag(url=ORIGEM + cliente)
            F = pc.evaluate("() => { const F = (window.CapitaoIA || {}).TERMOS_FONTES || {}; return Object.keys(F).map((k) => [k, F[k].src, F[k].flags]); }")
            conta('cliente (%s): window.CapitaoIA.TERMOS_FONTES traz as 5 regex do filtro de saída, iguais às do testes/proibidos.json' % cliente,
                  sorted(F) == sorted([k, T[k]['src'], T[k]['flags']] for k in FILTRO) and not errs, ([k for k, s, f in F if k not in T or T[k]['src'] != s or T[k]['flags'] != f], sorted(k for k, *_ in F), errs[:1]))
            pc.close()
        b.close()


def confere_fontes_e_lookbehind(T):
    ruins = confere_fontes_texto(T)
    conta('Workers (workers-ai e claude-api): as 5 regex do filtro de saída escritas no arquivo são as do testes/proibidos.json', not ruins, ruins)
    com = [p for p in SEM_LOOKBEHIND if '(?<' in ler(p)]
    conta('capitao-brain.js e capitao-ia.js (as duas cópias) sem «(?<»', not com, com)
    # defeito plantado: uma letra trocada na fonte de um Worker tem de aparecer
    s = ler(WORKERS[0])
    m = re.search(R_FONTE_JS % 'ROTULOS', s)
    planta = confere_fontes_texto(T, {WORKERS[0]: s[:m.start(1)] + 'X' + s[m.start(1):]}) if m else []
    conta('autoteste: uma letra a mais na fonte ROTULOS de um Worker é acusada', planta == [(WORKERS[0], 'ROTULOS')], planta)


# ——————————————————————————————— 6: o grep final ———————————————————————————————
# (PROMPT Fase 7 «Grep final»: os arquivos; fora o support.js e o deck-stage.js, gerados)
PADROES_GREP = ('*.dc.html', 'index.html', 'login.html', 'manifest.webmanifest', 'capitao-*.js', 'sw.js', 'capitao-dados.js', 'base-conhecimento.json', 'README.md', 'guia-rapido/*.html',
                # publicados depois de o plano ser escrito (a lista do plano não os tinha): o relatório (F24), a página dos dados do aparelho e o FAQ de equipamentos (F10)
                'relatorio.html', 'dados.html', 'faq-equipamentos.json')
FORA_GREP = ('support.js', 'deck-stage.js')
GERADOS = ('capitao-dados.js', 'base-conhecimento.json', 'faq-equipamentos.json')   # e ferramentas/demo/fontes/**: os dados gerados (o texto é dado de bordo, sem ramo nem guarda)


def arquivos_grep():
    arqs = set()
    for pad in PADROES_GREP:
        arqs.update(glob.glob(os.path.join(RAIZ, pad)))
    arqs.update(p for p in glob.glob(os.path.join(RAIZ, 'ferramentas', 'demo', 'fontes', '**'), recursive=True) if os.path.isfile(p))
    rel = sorted(os.path.relpath(p, RAIZ).replace(os.sep, '/') for p in arqs)
    return [p for p in rel if os.path.basename(p) not in FORA_GREP]


def gerado(arq):
    return arq in GERADOS or arq.startswith('ferramentas/demo/fontes/')


# Classe de cada caractere: 'c' código, 's' texto entre aspas (ou template), 'r' regex literal, 'k' comentário, 'h' marcação/texto visível/dado.
ANTES_REGEX = set('(,=:[!&|?{};+-*%<>~^')
PALAVRAS_REGEX = ('return', 'typeof', 'case', 'in', 'of', 'delete', 'void', 'throw', 'new', 'else', 'do')


def classes_js(s, ini=0, fim=None, out=None):
    fim = len(s) if fim is None else fim
    out = out if out is not None else ['c'] * len(s)
    i, pilha, ult, palavra = ini, [], '', ''

    def marca(a, b, c):
        for j in range(a, min(b, fim)):
            out[j] = c
    while i < fim:
        ch = s[i]
        nx = s[i + 1] if i + 1 < fim else ''
        if ch == '/' and nx == '/':
            j = s.find('\n', i, fim)
            j = fim if j < 0 else j
            marca(i, j, 'k')
            i = j
            continue
        if ch == '/' and nx == '*':
            j = s.find('*/', i + 2, fim)
            j = fim if j < 0 else j + 2
            marca(i, j, 'k')
            i = j
            continue
        if ch in '\'"':
            j = i + 1
            while j < fim and s[j] != ch and s[j] != '\n':
                j += 2 if s[j] == '\\' else 1
            marca(i, j + 1, 's')
            i, ult, palavra = j + 1, 'x', ''
            continue
        if ch == '`' or (ch == '}' and pilha and pilha[-1] == 0):
            if ch == '}':
                pilha.pop()
            j = i + 1
            while j < fim:
                if s[j] == '\\':
                    j += 2
                    continue
                if s[j] == '`' or (s[j] == '$' and j + 1 < fim and s[j + 1] == '{'):
                    break
                j += 1
            if j < fim and s[j] == '$':
                marca(i, j + 2, 's')
                pilha.append(0)
                i, ult, palavra = j + 2, '(', ''
                continue
            marca(i, j + 1, 's')
            i, ult, palavra = j + 1, 'x', ''
            continue
        if ch == '{' and pilha:
            pilha[-1] += 1
        elif ch == '}' and pilha:
            pilha[-1] -= 1
        if ch == '/' and (ult == '' or ult in ANTES_REGEX or palavra in PALAVRAS_REGEX):
            j, cls, ok = i + 1, False, False
            while j < fim and s[j] != '\n':
                if s[j] == '\\':
                    j += 2
                    continue
                if s[j] == '[':
                    cls = True
                elif s[j] == ']':
                    cls = False
                elif s[j] == '/' and not cls:
                    ok = True
                    break
                j += 1
            if ok:
                j += 1
                while j < fim and s[j].isalpha():
                    j += 1
                marca(i, j, 'r')
                i, ult, palavra = j, 'x', ''
                continue
        if not ch.isspace():
            if ch.isalnum() or ch in '_$':
                palavra = palavra + ch if i > ini and (s[i - 1].isalnum() or s[i - 1] in '_$') else ch
            else:
                palavra = ''
            ult = ch
        i += 1
    return out


R_BLOCO = re.compile(r'<(script|style)\b([^>]*)>(.*?)</\1\s*>', re.S | re.I)


def classes_html(s):
    out = ['h'] * len(s)
    for m in re.finditer(r'<!--.*?-->', s, re.S):
        for j in range(m.start(), m.end()):
            out[j] = 'k'
    for m in R_BLOCO.finditer(s):
        a, b = m.start(3), m.end(3)
        if out[m.start()] == 'k' or 'json' in m.group(2).lower():
            continue
        for j in range(a, b):
            out[j] = 'c'
        if m.group(1).lower() == 'script':
            classes_js(s, a, b, out)
        else:
            for c in re.finditer(r'/\*.*?\*/', s[a:b], re.S):
                for j in range(a + c.start(), a + c.end()):
                    out[j] = 'k'
    return out


def classes(arq, s):
    if arq.endswith('.js'):
        return classes_js(s)
    if arq.endswith('.html'):
        return classes_html(s)
    return ['h'] * len(s)


def literal(linha, cl, p):
    """O texto entre aspas (classe 's') em que a posição `p` da linha cai, sem as aspas."""
    a = p
    while a > 0 and cl[a - 1] == 's':
        a -= 1
    b = p
    while b < len(linha) and cl[b] == 's':
        b += 1
    t = linha[a:b]
    return t[1:-1] if len(t) >= 2 and t[0] in '\'"`' and t[-1] == t[0] else t.strip('\'"`')


# A guarda do ramo `simulacao: false` (ou do caminho null) na MESMA linha do literal: o ternário do `sim`, o `falta()` das telas (devolve '—' com a simulação),
# a declaração do SD/SL, o `real ?` do gráfico, o `!sim()` do cérebro.
R_GUARDA = re.compile(r'\bsim\s*\?|!\s*sim\b|\bsm\s*\?|\bfalta\(|\b(?:SD|SL)\s*=\s*[\'"]|\breal\s*\?|\bD\.demo\b|simulacao\s*(?:===\s*false|!==\s*true)')
R_APARELHO = re.compile(r'neste navegador|armazenamento|cérebro indisponível')
FRASES_EXCECAO = ('procedimento padrão — confirmar com o protocolo de bordo', 'Previsão e maré: sem conexão agora')   # + a frase da sobreDados, lida do cérebro


def frases_excecao():
    m = re.search(r"var SOBRE_DADOS = '((?:[^'\\]|\\.)*)';", ler('capitao-brain.js'))
    return FRASES_EXCECAO + ((m.group(1),) if m else ())


# EXCECOES (PROMPT §3) — (nome, o que é). A regra de cada uma está em `classifica`.
EXCECOES = (
    ('comentario', 'comentário de código'),
    ('identificador', 'identificador (D.snapshot, D.demo, simulacao, a chave "snapshot", o valor de `fonte` === \'snapshot\')'),
    ('anexo', 'A CONFERIR / A CONFIRMAR: o rótulo dos anexos (a ANEXO só vale nos dados gerados)'),
    ('ramo-real', 'literal do ramo `simulacao: false` (o `SD = \'SEM DADOS\'`), com a guarda na mesma linha'),
    ('frase', 'o rótulo do procedimento padrão, a frase da sobreDados e a de tempo e maré sem conexão'),
)
# JUSTIFICADOS — fora da lista do PROMPT, com motivo: é o «restante» que vai, com arquivo:linha, para a PARIDADE.md.
JUSTIFICADOS = (
    ('lista-de-termos', 'a própria lista de termos: as fontes das regex em TERMOS_FONTES (cérebro e cliente)'),
    ('rota', 'padrão de rota ou de filtro: regex literal do código, que lê a PERGUNTA de quem usa (nunca é texto mostrado)'),
    ('aparelho', 'aviso de recurso do aparelho («voz indisponível neste navegador», armazenamento): não é dado de bordo'),
    ('codigo', 'o casamento atravessa código (aspas, parêntese, operador): não é um texto'),
    ('historico', 'README: linha da tabela de versões 1.0.x (o que a versão antiga fazia)'),
    ('pontual', 'linha conferida uma a uma (PONTUAIS)'),
)
# PONTUAIS — (arquivo, regex, trecho que identifica a linha, motivo). Cada uma foi lida: o literal só sai no caminho null / ramo `simulacao: false`,
# com a guarda em outra linha; a tela e a resposta com a simulação são varridas no testes/verificar.py e no testes/cerebro.py (grupos rotulos, parcial e modos).
PONTUAIS = (
    ('capitao-brain.js', 'ROTULOS', "S.gps.texto : 'posição SEM LEITURA'", 'o SNAP da reserva (D.snapshot): só o ramo simulacao false o lê'),
    ('capitao-brain.js', 'ROTULOS', "text: 'SEM DADOS de maré agora", 'maré sem leitura no modo real (a guarda `sim()` está na linha de cima)'),
    ('capitao-brain.js', 'ROTULOS', "'Sem sensor de porão no barramento NMEA — SEM LEITURA.'", 'resposta de reserva do porão (caminho null)'),
    ('capitao-brain.js', 'ROTULOS', "'\\n• Porão ' + (po || 'SEM LEITURA')", 'telemetria de reserva (caminho null do porão e da âncora)'),
    ('capitao-brain.js', 'ROTULOS', "'Sem sensor de âncora na rede NMEA — SEM LEITURA do ferro.'", 'resposta de reserva da âncora (caminho null)'),
    ('capitao-brain.js', 'ROTULOS', "typeof q.seakeeper_ativo !== 'boolean' ? 'SEM LEITURA'", 'caminho null do quadro (o quadro gerado sempre traz o campo)'),
    ('capitao-brain.js', 'VISIVEL', "'telemetria (snapshot do coletor NMEA; ao vivo quando o coletor estiver ligado)", '«Sobre o app» do modo real (a guarda `sm ?` está na linha de cima)'),
    ('capitao-brain.js', 'VAZIOS', "erro: 'indisponivel'", 'código de erro interno (sem acento, nunca mostrado)'),
    ('capitao-brain.js', 'AUTENTICIDADE', "' fictici', ' demo ', ' demonstracao '", 'lista de palavras da rota sobreDados (lê a pergunta)'),
    ('capitao-brain.js', 'LOCAL_SEGURANCA', "|balsa|cais|pier|trapiche|marina)|n[ao] (?:proa|popa|flybridge", 'fonte de regex da rota de pessoa na água (lê a pergunta)'),
    ('F1-FAQ-Hub-Web.dc.html', 'AUTENTICIDADE', "a resposta é ' + SD + ' e aponta onde buscar — nada é inventado. '", 'a regra do FAQ no modo real (a guarda `sim ?` está na linha de cima)'),
    ('F1-FAQ-Hub.dc.html', 'AUTENTICIDADE', "a resposta é ' + SD + ' e aponta onde buscar — nada é inventado. '", 'a regra do FAQ no modo real (a guarda `sim ?` está na linha de cima)'),
    ('C4-Checklist-Mobile.dc.html', 'ROTULOS', "sem: ['SEM LEITURA', 'var(--cap-ink3", 'estado do item sem leitura do quadro (caminho null; o quadro gerado traz todos)'),
    ('C4-Checklist-Web.dc.html', 'ROTULOS', "sem: ['SEM LEITURA', 'var(--cap-ink3", 'estado do item sem leitura do quadro (caminho null; o quadro gerado traz todos)'),
    ('S1-SOS-Web.dc.html', 'VAZIOS', "' não cadastrado — abrir Equipe para cadastrar'", 'SOS fora da simulação: telefone de verdade, que só existe neste aparelho'),
    ('S2-SOS-Mobile.dc.html', 'VAZIOS', "' não cadastrado — abrir Equipe para cadastrar'", 'SOS fora da simulação: telefone de verdade, que só existe neste aparelho'),
)
R_TERMOS_FONTES = re.compile(r"^\s+[A-Z_]+: \{ src: '")
R_HISTORICO = re.compile(r'^\| 1\.0\.\d+ \|')


def classifica(arq, linha, cl, nome, m):
    """→ ('excecao' | 'justificado' | 'resto', regra). `cl`: a classe de cada caractere da linha."""
    a = m.start()
    while a < m.end() - 1 and not linha[a].strip():
        a += 1
    cs = set(cl[a:m.end()]) or {cl[a]}
    c = cl[a]
    if cs == {'k'}:
        return 'excecao', 'comentario'
    if nome == 'ANEXO':
        return ('resto', '') if gerado(arq) else ('excecao', 'anexo')
    if gerado(arq) and c == 's' and nome == 'VISIVEL' and literal(linha, cl, a).lower() == 'snapshot':
        return 'excecao', 'identificador'   # a chave "snapshot" do capitao-dados.js
    if gerado(arq) and c != 'c':
        return 'resto', ''   # dado gerado: nenhuma outra exceção
    if c == 'c' and cs <= {'c'}:
        return 'excecao', 'identificador'
    if len(cs) > 1:
        return 'justificado', 'codigo'
    if c == 'r':
        return 'justificado', 'rota'
    if c == 's':
        lit = literal(linha, cl, a)
        if nome == 'VISIVEL' and lit.lower() == 'snapshot':
            return 'excecao', 'identificador'
        if R_TERMOS_FONTES.search(linha) and arq in ('capitao-brain.js',) + CLIENTES:
            return 'justificado', 'lista-de-termos'
        for parq, pnome, trecho, _ in PONTUAIS:
            if parq == arq and pnome == nome and trecho in linha:
                return 'justificado', 'pontual'
        if nome == 'VAZIOS' and R_APARELHO.search(lit):
            return 'justificado', 'aparelho'
        if R_GUARDA.search(linha):
            return 'excecao', 'ramo-real'
        return 'resto', ''
    if arq == 'README.md' and R_HISTORICO.search(linha):
        return 'justificado', 'historico'
    return 'resto', ''


def varre(arq, s, RX, frases):
    """Cada casamento do arquivo: (arquivo, nº da linha, regex, casado, tipo, regra, trecho)."""
    cl = classes(arq, s)
    out, ini = [], 0
    for n, linha in enumerate(s.split('\n'), 1):
        lcl = cl[ini:ini + len(linha)]
        limpa = linha
        for f in frases:   # a frase de exceção sai antes (mesmo comprimento: as posições não andam)
            limpa = limpa.replace(f, ' ' * len(f))
        for nome, rx in RX.items():
            for m in rx.finditer(limpa):
                tipo, regra = classifica(arq, linha, lcl, nome, m)
                out.append((arq, n, nome, m.group(0).strip(), tipo, regra, linha[max(0, m.start() - 60):m.end() + 40].strip()))
        ini += len(linha) + 1
    return out


def dessincronia(arq, s):
    """Linha que começa por `//` (num .js ou num <script>) e NÃO ficou como comentário: o separador de classes perdeu o passo."""
    if not (arq.endswith('.js') or arq.endswith('.html')):
        return []
    cl = classes(arq, s)
    out, ini = [], 0
    for n, linha in enumerate(s.split('\n'), 1):
        t = linha.lstrip()
        if t.startswith('//') and cl[ini + len(linha) - len(t)] not in ('k', 'h'):
            out.append('%s:%d' % (arq, n))
        ini += len(linha) + 1
    return out


AUTOTESTE = (
    # (arquivo de mentira, conteúdo, regex, tipo esperado, regra esperada)
    ('X1-Tela.dc.html', '<div>SEM DADOS</div>', 'ROTULOS', 'resto', ''),
    ('X1-Tela.dc.html', '<div title="leitura fixa">x</div>', 'VISIVEL', 'resto', ''),
    ('X1-Tela.dc.html', '<!-- SEM DADOS só no modo real -->', 'ROTULOS', 'excecao', 'comentario'),
    ('X1-Tela.dc.html', '<script type="text/x-dc">\n// o snapshot DEMO\nconst a = 1;\n</script>', 'ROTULOS', 'excecao', 'comentario'),
    ('X1-Tela.dc.html', '<script type="text/x-dc">\nconst rot = \'Leitura SEM DADOS\';\n</script>', 'ROTULOS', 'resto', ''),
    ('X1-Tela.dc.html', '<script type="text/x-dc">\nconst rot = sim ? \'—\' : \'SEM DADOS\';\n</script>', 'ROTULOS', 'excecao', 'ramo-real'),
    ('X1-Tela.dc.html', '<script type="text/x-dc">\nconst t = \'os dados são fictícios\';\n</script>', 'AUTENTICIDADE', 'resto', ''),
    ('capitao-x.js', "var S = D.snapshot || {};", 'VISIVEL', 'excecao', 'identificador'),
    ('capitao-x.js', "var r = I.fonte === 'snapshot';", 'VISIVEL', 'excecao', 'identificador'),
    ('capitao-x.js', "var t = 'Faixa: snapshot das 10:12';", 'VISIVEL', 'resto', ''),
    ('capitao-x.js', "var t = 'valor a definir';", 'VAZIOS', 'resto', ''),
    ('capitao-x.js', "var t = 'Voz indisponível neste navegador';", 'VAZIOS', 'justificado', 'aparelho'),
    ('capitao-x.js', "var t = 'Leitura indisponível';", 'VAZIOS', 'resto', ''),
    ('capitao-x.js', "var u = 'https://exemplo.invalid/a'; var t = 'SEM LEITURA';", 'ROTULOS', 'resto', ''),
    ('capitao-x.js', "var t = /fictici|inventad/.test(q);", 'AUTENTICIDADE', 'justificado', 'rota'),
    ('capitao-dados.js', '  "nota": "SEM DADOS",', 'ROTULOS', 'resto', ''),
    ('capitao-dados.js', '  "nota": "A CONFIRMAR",', 'ANEXO', 'resto', ''),
    ('capitao-dados.js', '  "snapshot": {', 'VISIVEL', 'excecao', 'identificador'),
    ('base-conhecimento.json', '{"texto": "modelo n/d"}', 'VAZIOS', 'resto', ''),
    ('G1-Tela.dc.html', '<b>A CONFERIR</b>', 'ANEXO', 'excecao', 'anexo'),
    ('README.md', 'O app mostra SEM DADOS.', 'ROTULOS', 'resto', ''),
    ('README.md', '| 1.0.5 | 27/09/2026 | a IA responde no SEM DADOS |', 'ROTULOS', 'justificado', 'historico'),
    ('README.md', 'Emergência: procedimento padrão — confirmar com o protocolo de bordo.', None, None, None),
)


def autoteste_grep(RX, frases):
    ruins = []
    for arq, s, nome, tipo, regra in AUTOTESTE:
        achados = varre(arq, s, RX, frases)
        if nome is None:
            if achados:
                ruins.append((arq, s, 'devia passar limpo', achados[0][2:6]))
            continue
        meus = [(a[4], a[5]) for a in achados if a[2] == nome]
        if meus != [(tipo, regra)]:
            ruins.append((arq, s, nome, 'esperado', (tipo, regra), 'veio', meus))
    conta('autoteste do grep: %d defeitos e exceções plantados caem na classe certa (rótulo na marcação, no texto sem guarda e no dado gerado = RESTO; comentário, identificador, anexo e literal com guarda = exceção)' % len(AUTOTESTE),
          not ruins, ruins[:3])


def grep_final(T, lista=False):
    RX = {k: compila(v) for k, v in T.items()}
    frases = frases_excecao()
    autoteste_grep(RX, frases)
    arqs = arquivos_grep()
    achados, fora = [], []
    for arq in arqs:
        try:
            s = ler(arq)
        except UnicodeDecodeError:
            continue   # binário dentro de ferramentas/demo/fontes (nenhum hoje)
        achados += varre(arq, s, RX, frases)
        fora += dessincronia(arq, s)
    conta('grep final: o separador de código, texto e comentário não perde o passo (toda linha que começa por «//» é comentário)', not fora, fora[:6])
    orfas = [(p[0], p[1], p[2][:50]) for p in PONTUAIS if not any(a[0] == p[0] and a[2] == p[1] and a[5] == 'pontual' and p[2] in ler(p[0]).split('\n')[a[1] - 1] for a in achados)]
    conta('grep final: toda linha da lista PONTUAIS ainda existe (o trecho está no arquivo e casa a regex)', not orfas, orfas)
    por = {}
    for a in achados:
        por.setdefault((a[4], a[5]), []).append(a)
    resto = por.get(('resto', ''), [])
    print('grep final: %d arquivos · %d casamentos · %d nas EXCECOES · %d justificados (PARIDADE) · %d de RESTO' % (
        len(arqs), len(achados), sum(len(v) for (t, _), v in por.items() if t == 'excecao'), sum(len(v) for (t, _), v in por.items() if t == 'justificado'), len(resto)))
    for nome, desc in EXCECOES:
        print('  EXCEÇÃO %-15s %4d  %s' % (nome, len(por.get(('excecao', nome), [])), desc))
    for nome, desc in JUSTIFICADOS:
        itens = por.get(('justificado', nome), [])
        print('  JUSTIFICADO %-15s %4d  %s' % (nome, len(itens), desc))
        if lista:
            motivos = {(p[0], p[1], p[2]): p[3] for p in PONTUAIS}
            for a in itens:
                motivo = next((mv for (pa, pn, pt), mv in motivos.items() if pa == a[0] and pn == a[2] and pt in ler(a[0]).split('\n')[a[1] - 1]), '') if nome == 'pontual' else ''
                print('      %s:%d %s «%s»%s' % (a[0], a[1], a[2], a[3], ' — ' + motivo if motivo else ''))
    if resto:
        por_arq = {}
        for a in resto:
            por_arq.setdefault(a[0], []).append(a)
        print('  RESTO (fora das EXCECOES e sem justificativa): %d casamentos em %d arquivos' % (len(resto), len(por_arq)))
        for arq in sorted(por_arq):
            print('    %s: %d — linhas %s' % (arq, len(por_arq[arq]), ', '.join(str(n) for n in sorted({a[1] for a in por_arq[arq]}))))
        for a in resto:
            print('    RESTO %s:%d %s «%s» …%s…' % (a[0], a[1], a[2], a[3], a[6]))
    return resto


def main():
    so_testes, so_grep, lista = '--so-testes' in sys.argv, '--grep-final' in sys.argv, '--lista' in sys.argv
    T = carrega()
    with open(CASOS, encoding='utf-8') as f:
        casos = json.load(f)
    resto = []
    if not so_grep:
        confere_arquivos(T)
        py = casos_python(T, casos)
        confere_fontes_e_lookbehind(T)
        no_navegador(T, casos, py)
    if not so_testes:
        resto = grep_final(T, lista)
    print('proibidos: %d conferências · %d falhas%s' % (len(FEITAS), len(FALHAS), '' if so_testes else ' · grep final: %d de resto' % len(resto)))
    sys.exit(1 if FALHAS or resto else 0)


if __name__ == '__main__':
    main()
