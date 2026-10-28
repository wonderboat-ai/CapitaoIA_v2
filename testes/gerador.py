# -*- coding: utf-8 -*-
"""Capitão IA — teste do gerador de dados (CONTRATO-DADOS 1.1.0, §6.2 C3 e §6.3). Sem navegador, sem rede, sem cota.

- Determinismo: rodado com --saida numa pasta temporária, o gerador dá a árvore byte a byte (capitao-dados.js,
  base-conhecimento.json e ferramentas/demo/fontes/**); duas rodadas dão 0 diferença; nenhuma leitura do relógio do sistema.
  O teste nunca escreve na árvore de trabalho (confere o hash dos arquivos gerados antes e depois).
- Limpeza de fontes/: apaga só o que não gera mais, dentro da pasta, sem seguir link (o alvo de um link fica intacto) e sem
  gravar através de um link. Link em qualquer pasta do caminho (fontes -> ../.., ferramentas -> uma pasta da saída…): o gerador
  recusa antes de gravar ou apagar qualquer coisa (revisão final: antes, a limpeza apagava o capitao-dados.js recém-gravado).
- confere(): cada asserção da §6.3 acusa uma amostra plantada (a violação nova aparece), e mais as amostras extras dos achados
  da revisão do C3 (EXTRAS). Nas estruturais, a violação plantada fica fora das pendências congeladas (PENDENTES) e reprova o
  gerador (main() devolve 1 e nada é gravado); uma pendência que não ocorre mais também reprova; a varredura de termos
  (relatório até o C12) não reprova. Listas privadas e pasta do Avanti: só amostras sintéticas aqui, inclusive a troca de um
  modelo congelado (como o do VHF antigo, até o C5) por outro da lista, que reprova (modelos_sinteticos).
- C5 (CONTRATO §1.4, §1.5, §3.3): 16 equipamentos, 16 guias e 91 trechos; a constante LIMITES confere com os §n dos guias
  (FONTE_LIMITES, antes do D.replay do C8); os textos de emergência do gerador são os do §1.3; EPIRB e Seafire com a nota da
  etiqueta e sem fabricante nem modelo nos trechos.
- C6 (CONTRATO §1.3): o D.protocolos completo (18 campos, seafire e epirb com a nota da etiqueta), igual letra por letra ao texto do
  contrato (PROTOCOLOS_C6); a asserção PROTOCOLOS acusa cada defeito de forma, texto fixo e fonte única com os guias; as pendências
  do C6 saíram da PENDENTES (a pendência velha de hoje é a do C8).
- C7 (CONTRATO §1.7–§1.9, §1.11, §1.23, §4.1, §5): agenda de 14 tarefas, tarefas da equipe, documentos (o TIE com id e numero), diário fixo,
  equipe e fontes do Drive com prazos relativos (deslocamentos + reserva contada da REF); as pendências do C7 saíram da PENDENTES (só o
  C8 fica) e o rodapé de verdade (rodape.js) é anexado sem mudança ao capitao-dados.js e passa a RODAPE_SNAPSHOT (rodape_real()). O
  comportamento do rodapé, no navegador, é do testes/rodape.py.
- Revisão do C7 (C7_REV): o C7 tirou da PENDENTES as linhas AGENDA, IDS e FONTES_RELATIVAS, e com elas a prova de que essas regras (e as do
  NULO e do DIA_DE_BORDO sobre as listas novas) reprovam. Agora cada uma tem amostra plantada ISOLADA (planta(..., so_uma=True): a única
  violação nova da regra), 28 no total, e a de salvatagem atrasada da AGENDA troca a tarefa que existe (antes acrescentava um 2º id).
- Revisão do C6 (CONTRATO §1.3, «todas viram asserção»): a GRAFIA_SEAFIRE prende «Seafire» (sem hífen, espaço nem outra caixa) em todo valor, chave e
  nome de arquivo do D, da base, do FAQ e das fontes; a única exceção são as `palavras` de busca dos equipamentos («sea fire», o ditado). 27 amostras
  plantadas (12 grafias, a base inteira com «Sea Fire», chaves, CSV, JSON, FAQ, HTML com entidade e tag, nome de arquivo) e grafia_seafire().
- C2 (CONTRATO §1.1, §1.2, §1.3, §1.5, §1.10): rótulos fora dos títulos e das fontes. rotulos_c2() prende o resultado com o texto
  do contrato: drive.arquivos, os quatro *Fonte, embarcacao.fonte, canal16.fonte e regraAbast, o aviso e a versao (8 hex do
  sha256) da base, as fontes do Drive (nome e texto sem DEMO, snapshot, fictício nem demonstração) e o LEIA-ME sem a regra
  antiga, sem data e sem ID.
- Revisão final do C3: da varredura de termos, PESSOAIS, DINHEIRO e LOCAL_SEGURANCA reprovam já (travas §2.2 e §2.7); a
  SEM_INDICATIVO e a SEM_PREVISAO também leem o cabeçalho das colunas dos CSV das fontes (a 1ª linha com conteúdo), comparando
  também as palavras vizinhas juntas (palavras_juntas: "WhatsApp" = whats + app, "Baixa-mar"); a PROTOCOLO_LIMPO e a AGENDA proíbem
  cada palavra e as formas juntas do fabricante e do modelo do EPIRB e do Seafire (trava 17).
- Revisão do C3 (porao_e_lugar): o porão ≤ 5 cm da §6.4 vive na JANELA (teto = normal.ate, sem número solto, também dentro de janela
  de aviso, no laço com ruído, em replay.fixos, snapshot.quadro e snapshot.porao) e o lugar de salvatagem em qualquer ordem na
  LOCAL_VOCAB (D, base, FAQ e páginas de fonte; «No paiol de proa ficam os coletes» passava fora de protocolos).
- C8 (CONTRATO §1.14–§1.17, §1.22, §3, §4.1; c8_rota_e_replay): rota (pontos, pernas, 19 circuitos, fator ≤ 1), D.campos (66), D.replay (28 chaves,
  ruído, fixos, contadores, limites, 21 alertas, janelas derivadas, dia de bordo), consumo, destinos e snapshot sem null; o em() portado contra os números do
  §1.22 (12:01:00, 12:01:45, a virada 06:59:59 → 07:00:00); as 575 emendas de 150 s sem chegada e o cenário alarme-critico; as asserções novas com amostras
  plantadas (C8_PLANTAS) e a PENDENTES vazia.
- Revisão do C8 (§4.3, §0 item 6): com SIMULACAO = False a leitura da pasta 05 também sai sem lat/lon (antes lia o SNAPSHOT cru) e a LACO acusa
  chave ou coluna de posição em qualquer fonte do Drive (c8_real: o D e as fontes de verdade do modo real, com a posição plantada); o Formato do
  quadro do coletor não mostra mais a coluna Origem (a taxonomia interna do D.campos) e a LACO acusa essa coluna e os valores de ORIGENS numa
  planilha da pasta 05.
- C10 (CONTRATO §1.18–§1.21; c10_funcoes): checklists (4 tipos, 35 itens com `c`, ✓ automático, FAQ, `fonte` (a da CK_FONTE: um §n que existe ou «boa prática»)
  e os números do `t` (os da CK_NUM, vindos das mesmas constantes do guia e cada um no texto da seção citada)),
  sensores (22 pontos, x/y pela fórmula, `bloco` das duas plataformas), peças (12, a única BAIXA e a única ZERO) e alarmes pedidos (18 métricas,
  `faixa` própria, nível só aviso), nos dois modos; a asserção FUNCOES (forma e referência do contrato) e as regras que o C10 ativou (IDS,
  NULO, SEM_EMERGENCIA, SEM_SALVATAGEM_EM, LOCAL_VOCAB, TERMOS) com amostras plantadas.
- C11 (CONTRATO §1.6; c11_faq): faq-equipamentos.json (F10) — 91 itens (82 seções dos guias e do checklist, MO-01…CK-07, e os 9 cartões EM-01…09 do protocolo), 9 seções, glossário de
  14 termos, sem conf, edição nem anexos do Avanti; a 1ª fonte de cada item é o trecho da base do id e todo número do item está nele; EM, SF, EP e CK-03 com seguranca e o rótulo do
  procedimento padrão no fim; a asserção FAQ e as outras que leem o FAQ (TERMOS, NULO, TAMANHO, COORD_TEXTO, GRAFIA_SEAFIRE, CALADO_FORA, ESTABILIZADOR_12V, LOCAL_VOCAB, ROTULO_SEGURANCA,
  SEGURANCA_MARCADA, SEGURANCA_SEM_MODELO, IDS…) com amostras plantadas, e o main() que reprova o FAQ com defeito (sem gravar nada).
  Revisão do C11: a resposta dos cartões e dos itens de segurança mantém a frase do trecho que escala (MAYDAY) ou condiciona («e há fogo no motor»)
  — a asserção FAQ reprova a resposta que a corta (EM-04, EM-05, EM-08, SF-01, SF-03, EP-01, EL-05 e PO-04 foram corrigidos) — e os itens do checklist
  «boa prática» que o app avalia entram no FAQ como ordem de conferência (FAQ_CK_ORDEM), nunca como o estado («Nenhuma tarefa de segurança atrasada»).
- testes/proibidos.json e proibidos-casos.json são cópias iguais do termos.json e do termos-casos.json (PROMPT §3).

    python -X utf8 testes/gerador.py
"""
import contextlib
import copy
import csv
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(RAIZ, 'ferramentas', 'demo')
GERADOR = os.path.join(DEMO, 'gerar_demo.py')
FONTES_REL = os.path.join('ferramentas', 'demo', 'fontes')
sys.path.insert(0, DEMO)
import confere as C  # noqa: E402

spec = importlib.util.spec_from_file_location('gerar_demo', GERADOR)
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

falhas = 0


def ok(nome, cond, info=''):
    global falhas
    print(('  ok    ' if cond else '  FALHA ') + nome + ('' if cond or info == '' else ' — ' + str(info)[:400]))
    if not cond:
        falhas += 1


def arvore(pasta):
    """{caminho relativo: bytes} dos arquivos gerados numa pasta de saída."""
    out = {}
    for rel in ('capitao-dados.js', 'base-conhecimento.json', 'faq-equipamentos.json'):
        p = os.path.join(pasta, rel)
        if os.path.isfile(p):
            out[rel] = open(p, 'rb').read()
    raiz = os.path.join(pasta, FONTES_REL)
    for topo, _, arqs in os.walk(raiz):
        for a in arqs:
            p = os.path.join(topo, a)
            out[os.path.relpath(p, pasta).replace(os.sep, '/')] = open(p, 'rb').read()
    return out


def hash_arvore(pasta):
    return {k: hashlib.sha256(v).hexdigest() for k, v in arvore(pasta).items()}


def roda(saida, *extra):
    env = {k: v for k, v in os.environ.items() if k not in ('CAPITAO_LISTAS_PRIVADAS', 'CAPITAO_AVANTI')}
    return subprocess.run([sys.executable, '-X', 'utf8', GERADOR, '--saida', saida] + list(extra), capture_output=True, text=True,
                          encoding='utf-8', env=env)


def determinismo(tmp):
    print('Determinismo e --saida')
    antes = hash_arvore(RAIZ)
    g1, g2 = os.path.join(tmp, 'g1'), os.path.join(tmp, 'g2')
    r1, r2 = roda(g1), roda(g2)
    ok('o gerador roda com --saida (código 0)', r1.returncode == 0 and r2.returncode == 0, (r1.stderr or r1.stdout)[-400:])
    a, b, t = arvore(g1), arvore(g2), arvore(RAIZ)
    ok('duas rodadas: 0 diferença', a == b, sorted(set(a) ^ set(b)) or [k for k in a if a[k] != b.get(k)])
    ok('--saida = árvore de trabalho, byte a byte (%d arquivos)' % len(t), a == t,
       {'só na saída': sorted(set(a) - set(t)), 'só na árvore': sorted(set(t) - set(a)), 'diferentes': [k for k in a if k in t and a[k] != t[k]]})
    ok('o teste não escreveu na árvore de trabalho', hash_arvore(RAIZ) == antes)
    fonte = open(GERADOR, encoding='utf-8').read() + open(os.path.join(DEMO, 'confere.py'), encoding='utf-8').read()
    relogio = re.findall(r'\b(?:datetime\.now|date\.today|datetime\.today|utcnow|time\.time|time\.localtime|time\.gmtime|time\.strftime)\b', fonte)
    ok('nenhuma leitura do relógio do sistema no gerador', not relogio, relogio)
    js = a.get('capitao-dados.js', b'').decode('utf-8')
    # C7: o rodapé (CapitaoAgora, código indentado) vem depois dos dados; o serializador é só dos dados, até o comentário do rodapé
    linhas = js[js.find('window.CapitaoDados = '):js.find('/* CapitaoAgora')].split('\n')   # sem o comentário do cabeçalho
    ok('serializador compacto: dicionários indentados até a profundidade 2, o resto numa linha',
       all(not l.startswith('   ') for l in linhas) and ' "embarcacao": {' in js and '\n  "nome": "Capitão IA",' in js and '\n "agenda": [{' in js,
       [l[:80] for l in linhas if l.startswith('   ')][:3])


def limpeza(tmp):
    print('Limpeza de fontes/')
    s = os.path.join(tmp, 'g3')
    roda(s)
    F = os.path.join(s, FONTES_REL)
    velho = os.path.join(F, '01 Manuais e guias de bordo', 'Guia antigo (DEMO).html')
    pasta_velha = os.path.join(F, '99 Pasta antiga', 'dado.csv')
    outro = os.path.join(s, 'ferramentas', 'demo', 'outro.txt')
    for p in (velho, pasta_velha, outro):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w').write('x')
    fora = os.path.join(tmp, 'fora')
    os.makedirs(os.path.join(fora, 'pasta'), exist_ok=True)
    sentinelas = {n: os.path.join(fora, n) for n in ('alvo.txt', 'alvo2.txt', os.path.join('pasta', 'dentro.txt'))}
    for p in sentinelas.values():
        open(p, 'w').write('intacto')
    leia = os.path.join(F, G.ARQ['leiame'] + '.html')
    links = True
    try:
        os.symlink(sentinelas['alvo.txt'], os.path.join(F, 'link-para-fora.txt'))
        os.symlink(os.path.join(fora, 'pasta'), os.path.join(F, 'pasta-link'))
        os.remove(leia)
        os.symlink(sentinelas['alvo2.txt'], leia)
    except (OSError, NotImplementedError):
        links = False
    r = roda(s)
    ok('o gerador roda (código 0)', r.returncode == 0, r.stderr[-300:])
    ok('apaga o arquivo que não gera mais', not os.path.exists(velho))
    ok('apaga a pasta que ficou vazia', not os.path.exists(os.path.dirname(pasta_velha)))
    ok('não toca fora de fontes/', os.path.isfile(outro))
    ok('árvore gerada igual à da 1ª rodada', arvore(s) == arvore(os.path.join(tmp, 'g1')))
    if not links:
        print('  (links simbólicos indisponíveis neste sistema: conferências de link puladas)')
        return
    ok('link para fora: só a entrada sai, o alvo fica', not os.path.lexists(os.path.join(F, 'link-para-fora.txt')) and open(sentinelas['alvo.txt']).read() == 'intacto')
    ok('link de pasta: não segue (o que está dentro do alvo fica)', not os.path.lexists(os.path.join(F, 'pasta-link'))
       and open(sentinelas[os.path.join('pasta', 'dentro.txt')]).read() == 'intacto')
    ok('não grava através de um link no lugar de um arquivo gerado', not os.path.islink(leia) and open(sentinelas['alvo2.txt']).read() == 'intacto'
       and open(leia, encoding='utf-8').read() == G.gera_fontes(G.dados())[G.ARQ['leiame'] + '.html'])
    # Pasta do caminho que é link para fora: o gerador recusa antes do 1º arquivo (nada pela metade, nada fora).
    s4, fora4 = os.path.join(tmp, 'g4'), os.path.join(tmp, 'fora4')
    os.makedirs(os.path.join(s4, FONTES_REL), exist_ok=True)
    os.makedirs(fora4, exist_ok=True)
    os.symlink(fora4, os.path.join(s4, FONTES_REL, G.PASTAS['docs']))
    r = roda(s4)
    ok('pasta de fontes/ que é link para fora: recusa sem gravar nada', r.returncode != 0 and not os.listdir(fora4)
       and not os.path.exists(os.path.join(s4, 'capitao-dados.js')), (r.returncode, r.stderr[-200:]))
    link_na_saida(tmp)


def conteudo(pasta):
    """{caminho relativo: bytes} de tudo o que está numa pasta (arquivos e links, sem seguir link; um link vira 'link -> alvo')."""
    out = {}
    for topo, pastas, arqs in os.walk(pasta, followlinks=False):
        for n in arqs + [p for p in pastas if os.path.islink(os.path.join(topo, p))]:
            c = os.path.join(topo, n)
            out[os.path.relpath(c, pasta)] = ('link -> ' + os.readlink(c)).encode() if os.path.islink(c) else open(c, 'rb').read()
    return out


def link_na_saida(tmp):
    """Revisão final do C3: um link no caminho de fontes/ que aponta para DENTRO da pasta de saída (o link para fora já tem teste).
    Antes, `fontes -> ../..` fazia o gerador gravar as fontes na raiz da saída e a limpeza apagar o capitao-dados.js recém-gravado,
    o que não é fonte gerada (e, na raiz do repositório, o .env e o testes/saida-ultima.json). Agora o gerador recusa antes de
    gravar ou apagar qualquer coisa (sem_link), em alvo() e em limpa_fontes()."""
    print('Link no caminho de fontes/ para dentro da saída')
    def monta(nome, ligacoes):
        """saida com a árvore sentinela e os links pedidos; devolve a pasta."""
        s = os.path.join(tmp, 'lk-' + nome)
        for rel, txt in (('capitao-dados.js', 'ANTIGO dados'), ('base-conhecimento.json', 'ANTIGA base'), ('.env', 'segredo'),
                         (os.path.join('testes', 'saida-ultima.json'), '{}'), (os.path.join('dados', 'sentinela.txt'), 'intacto'),
                         (os.path.join('dados', 'sub', 'outra.txt'), 'intacta'), (os.path.join('real', 'demo', 'fontes', 'velho.txt'), 'velho')):
            os.makedirs(os.path.dirname(os.path.join(s, rel)), exist_ok=True)
            open(os.path.join(s, rel), 'w').write(txt)
        for rel, alvo_link in ligacoes:
            c = os.path.join(s, rel)
            os.makedirs(os.path.dirname(c), exist_ok=True)
            os.symlink(alvo_link, c)
        return s
    try:
        casos = [('fontes -> ../.. (a raiz da saída)', monta('raiz', [(FONTES_REL, os.path.join('..', '..'))])),
                 ('fontes -> ../../dados (pasta da saída com outros arquivos)', monta('dados', [(FONTES_REL, os.path.join('..', '..', 'dados'))])),
                 ('ferramentas -> real (uma pasta acima de fontes/)', monta('acima', [('ferramentas', 'real')])),
                 ('ferramentas/demo -> ../real/demo', monta('demo', [(os.path.join('ferramentas', 'demo'), os.path.join('..', 'real', 'demo'))]))]
    except (OSError, NotImplementedError):
        print('  (links simbólicos indisponíveis neste sistema: conferências de link puladas)')
        return
    for nome, s in casos:
        antes = conteudo(s)
        r = roda(s)
        ok('%s: recusa (código != 0), diz que é link e não grava nem apaga nada' % nome,
           r.returncode != 0 and 'link' in r.stderr and conteudo(s) == antes,
           (r.returncode, r.stderr[-200:], sorted(set(conteudo(s)) ^ set(antes))))
        try:   # direto na limpeza, com "nada é gerado" (o pior caso: tudo o que está no alvo do link seria apagado se ele fosse seguido)
            G.limpa_fontes(s, {})
            recusou = False
        except SystemExit:
            recusou = True
        ok('%s: limpa_fontes() recusa sozinha e não apaga nada' % nome, recusou and conteudo(s) == antes, sorted(set(conteudo(s)) ^ set(antes)))
        try:
            G.alvo(s, os.path.join(FONTES_REL, G.PASTAS['docs'], 'x.csv'))
            recusou = False
        except SystemExit:
            recusou = True
        ok('%s: alvo() recusa o caminho que passa pelo link' % nome, recusou)
    # Sem link no caminho, a mesma árvore sentinela grava normalmente e o que não é do gerador fica como estava.
    s = monta('sem-link', [])
    r = roda(s)
    ok('sem link no caminho: grava (código 0) e não toca no que não é do gerador', r.returncode == 0 and arvore(s) == arvore(os.path.join(tmp, 'g1'))
       and open(os.path.join(s, '.env')).read() == 'segredo' and open(os.path.join(s, 'dados', 'sentinela.txt')).read() == 'intacto'
       and open(os.path.join(s, 'real', 'demo', 'fontes', 'velho.txt')).read() == 'velho', (r.returncode, r.stderr[-200:]))


def copias():
    print('Cópias das regex (PROMPT §3)')
    p = os.path.join(RAIZ, 'ferramentas', 'prompts', 'clone-avanti-1.1.0')
    for a, b in (('termos.json', 'proibidos.json'), ('termos-casos.json', 'proibidos-casos.json')):
        ok('testes/%s = %s' % (b, a), open(os.path.join(p, a), 'rb').read() == open(os.path.join(RAIZ, 'testes', b), 'rb').read())
    # As regex que o confere() compila (cada uma com a sua flag) dão os casos: o que barra casa a indicada; o que passa não casa
    # nenhuma (o ANEXO fica fora do "passa", como no termos-casos.json). O Edge e as cópias do cérebro são do proibidos.py (Fase 3).
    T = C.carrega_termos()
    casos = json.load(open(os.path.join(RAIZ, 'testes', 'proibidos-casos.json'), encoding='utf-8'))
    erros = ['%s não barra %r' % (k, s) for k, frases in casos['barra'].items() for s in frases if not T[k].search(s)]
    erros += ['%s barra %r' % (k, s) for s in casos['passa'] for k, r in T.items() if k != 'ANEXO' and r.search(s)]
    ok('as 8 regex no Python dão os %d casos' % (sum(len(v) for v in casos['barra'].values()) + len(casos['passa'])), not erros and len(T) == 8, erros[:3])
    # Revisão final do C3: cada uma das 8 regex está num dos dois modos (reprova já / relatório até o C12); uma regex nova no
    # termos.json não fica sem classe (o padrão de em_relatorio() é o relatório, que não reprova).
    relat = {'ROTULOS', 'AUTENTICIDADE', 'VAZIOS', 'VISIVEL', 'ANEXO'}
    ok('TERMOS: PESSOAIS, DINHEIRO e LOCAL_SEGURANCA reprovam já; ROTULOS, AUTENTICIDADE, VAZIOS, VISIVEL e ANEXO ficam em relatório (as 8 do termos.json)',
       set(T) == relat | set(C.TERMOS_JA_REPROVAM) and not relat & set(C.TERMOS_JA_REPROVAM) and len(C.TERMOS_JA_REPROVAM) == 3
       and all(C.em_relatorio('TERMOS', k + ': x') for k in relat) and not any(C.em_relatorio('TERMOS', k + ': x') for k in C.TERMOS_JA_REPROVAM)
       and not C.em_relatorio('NULO', 'ROTULOS: x'), sorted(T))


# ——————————————————————————————— amostras plantadas ———————————————————————————————
CONST = {'NOTA_ETIQUETA': G.NOTA_ETIQUETA, 'DIAS_MESES': G.DIAS_MESES, 'LIMITES': G.LIMITES}   # as constantes que o gerador passa (C5: LIMITES)
ROTULO_FIM = C.rotulo_fim()   # os textos fixos do confere.py (ROTULO e NOTA), nunca os do dado
# O trecho do g_epirb §1 · Acionar: onde as amostras da trava 17 (SEGURANCA_SEM_MODELO) entram.
T_EPIRB1 = next(i for i, t in enumerate(G.base_conhecimento()['trechos']) if t['fonte'] == G.ARQ['g_epirb'] and t['secao'].startswith('1 · '))
# O trecho do DSC (g_eletronicos §5, MMSI_RADIO desde o C5): onde as amostras de MMSI e de afirmação entram.
T_DSC = next(i for i, t in enumerate(G.base_conhecimento()['trechos']) if t['fonte'] == G.ARQ['g_eletronicos'] and t['secao'].startswith('5 · '))


def hoje():
    D = G.dados()
    return {'D': copy.deepcopy(D), 'B': copy.deepcopy(G.base_conhecimento()), 'F': G.gera_fontes(D), 'faq': None, 'rodape': None,
            'listas': None, 'avanti': None}


def verifica(k):
    # o FAQ da amostra (ou {} sem FAQ): o saidas() não recalcula o de hoje sobre uma base plantada (que pode estar sem trecho)
    return C.verifica(k['D'], k['B'], k['F'], G.saidas(k['D'], k['B'], {} if k['faq'] is None else k['faq']), k['faq'], k['rodape'], k['listas'], k['avanti'], k.get('const', CONST))


def com_replay(k):
    """O D de hoje com um replay mínimo e coerente (campos, chaves, limites, janela, contadores) e o guia das faixas na base."""
    D = k['D']
    D['snapshot'] = {c: v for c, v in D['snapshot'].items() if c not in ('porao', 'quadro')}   # o replay mínimo não tem os limites do porão (§2.4)
    D['embarcacao'].update({'calado': 1.1, 'pessoasBordo': 4, 'tanques': {'diesel_l': 1600}})
    D['documentos'] = [d for d in D['documentos'] if d.get('cat') != 'Notas']   # a nota fiscal vai para o dia de bordo
    D['campos'] = {
        'motor_be_rpm': {'rotulo': 'Motor BE', 'un': 'rpm', 'casas': 0, 'origem': 'laço', 'mil': True},
        'motor_be_arref_c': {'rotulo': 'Arrefecimento BE', 'un': '°C', 'casas': 1, 'origem': 'laço'},
        'motor_be_oleo_bar': {'rotulo': 'Óleo BE', 'un': 'bar', 'casas': 1, 'origem': 'laço'},
        'vento_verdadeiro_angulo': {'rotulo': 'Vento de', 'un': '°', 'casas': 0, 'origem': 'laço', 'ang': True},
        'bateria_0_tensao_v': {'rotulo': 'Serviço 24 V', 'un': 'V', 'casas': 2, 'origem': 'laço'},
        'gerador_kw': {'rotulo': 'Gerador', 'un': 'kW', 'casas': 1, 'origem': 'laço'},
        'gerador_ativo': {'rotulo': 'Gerador ligado', 'un': 'liga/desliga', 'casas': 0, 'origem': 'fixo'},
        'diesel_litros': {'rotulo': 'Diesel', 'un': 'L', 'casas': 0, 'origem': 'contador', 'sentido': -1},
        'motor_be_horimetro_h': {'rotulo': 'Horímetro BE', 'un': 'h', 'casas': 1, 'origem': 'contador', 'sentido': 1},
    }
    fonte9, fonte2 = 'Guia de bordo — Teste §9 · Faixas de operação', 'Guia de bordo — Teste §2 · Faixas'
    oleo = [{'rpm_campo': 'motor_be_rpm', 'rpm_ate': 1000, 'normal': {'de': 1.0, 'ate': 6.0}, 'aviso': {'abaixo': 1.0, 'acima': 6.0}, 'critico': {'abaixo': 0.6}},
            {'rpm_campo': 'motor_be_rpm', 'rpm_de': 1000, 'normal': {'de': 2.4, 'ate': 6.0}, 'aviso': {'abaixo': 2.4, 'acima': 6.0}, 'critico': {'abaixo': 1.4}}]
    D['replay'] = {
        'duracao': 150, 'passo': 1, 'passo_chave': 5, 'cenario': 'aviso', 'ancora_hora': '07:00',
        'chaves': {'motor_be_rpm': [2040] * 30, 'motor_be_arref_c': [78.0] * 19 + [86.2, 89.0, 89.6, 89.6, 89.0, 85.8] + [78.0] * 5,
                   'motor_be_oleo_bar': [3.8] * 30, 'vento_verdadeiro_angulo': [358, 0, 2, 4, 2, 0] * 5,
                   'bateria_0_tensao_v': [27.8] * 30, 'gerador_kw': [6.0] * 30},
        'ruido': {'bateria_0_tensao_v': [0.02, 1110], 'gerador_kw': [0.1, 1111]},
        'fixos': {'gerador_ativo': True}, 'contadores_base': {'diesel_litros': 1560, 'motor_be_horimetro_h': 409.8},
        'por_dia': {'voltas': 576, 'diesel_l': 1086.2, 'distancia_mn': 311.5, 'motor_h': 24, 'gerador_h': 24}, 'diesel_piso_l': 400,
        'limites': {
            'motor_be_arref_c': {'un': '°C', 'fonte': fonte9, 'normal': {'ate': 88}, 'aviso': {'acima': 88}, 'critico': {'acima': 97},
                                 'ativo_se': {'campo': 'motor_be_rpm', 'acima': 0}},
            'motor_be_rpm': {'un': 'rpm', 'fonte': fonte9, 'normal': {'ate': 2600}, 'aviso': {'acima': 2600}},
            'motor_be_oleo_bar': {'un': 'bar', 'fonte': fonte9, 'regimes': oleo, 'ativo_se': {'campo': 'motor_be_rpm', 'acima': 0}},
            'bateria_0_tensao_v': {'un': 'V', 'fonte': fonte2, 'normal': {'de': 24.4, 'ate': 29.4}, 'aviso': {'abaixo': 24.4, 'acima': 29.4},
                                   'critico': {'abaixo': 23.6}},
            'gerador_kw': {'un': 'kW', 'fonte': fonte9, 'normal': {'ate': 8.1}, 'aviso': {'acima': 8.1}, 'ativo_se': {'campo': 'gerador_ativo', 'igual': True}},
        },
        'janelas': [{'id': 'arref_be', 'campo': 'motor_be_arref_c', 'nivel': 'aviso', 'ini': 99, 'fim': 116}],
        'diaDeBordo': {'dias': 3, 'abastecimento': {'h': '07:00', 'litros': 1086, 'nivelAntes': 29.6, 'nivelDepois': 97.5},
                       'documento': {'id': 'nf-abast', 'ref': 'ab-0'},
                       'diario': [{'id': 'd01', 'diasAtras': 0, 'h': '07:00', 't': 'Saída às 07:00 com 4 pessoas a bordo.'},
                                  {'id': 'd02', 'diasAtras': 0, 'h': '07:00', 'ref': 'ab-0', 't': 'Abastecimento de 1.086 L de diesel.'}]},
    }
    # C5: o D.replay.limites é a constante LIMITES do gerador (FONTE_LIMITES confere as duas); aqui, a do replay mínimo.
    k['const'] = dict(k.get('const', CONST), LIMITES=D['replay']['limites'])
    k['B']['trechos'] += [
        {'fonte': 'Guia de bordo — Teste', 'secao': '9 · Faixas de operação', 'equip': 'Teste',
         'texto': 'Rotação: até 2.600 rpm. Pressão de óleo: abaixo de 1.000 rpm, normal de 1,0 a 6,0 bar; a partir de 1.000 rpm, normal de 2,4 '
                  'a 6,0 bar. Crítico abaixo de 0,6 bar ou de 1,4 bar. Arrefecimento: normal até 88 °C; crítico acima de 97 °C. Gerador: aviso '
                  'acima de 8,1 kW.'},
        {'fonte': 'Guia de bordo — Teste', 'secao': '2 · Faixas', 'equip': 'Teste', 'texto': 'Banco de 24 V: normal de 24,4 a 29,4 V; crítico abaixo de 23,6 V.'},
    ]
    return k


def com_rota(k):
    """O replay mínimo com uma rota mínima coerente (2 pontos, 2 pernas pré-calculadas, 19 circuitos, fator em [0,9; 1,0]); o port do em() não
    roda nela (o replay mínimo não tem por_volta, fases nem o resto), e as asserções da rota não acusam nada."""
    k = com_replay(k)
    a, b = (-26.9985, -48.6160), (-26.9985, -48.4710)   # ~7,7 mn: 19 circuitos de 2 pernas = ~295 mn, o fator de 311,5 mn/dia fica em [0,9; 1,0]
    mn, ida, volta = round(C.mn_entre(a, b), 4), round(C.rumo_entre(a, b), 2), round(C.rumo_entre(b, a), 2)
    dist = round(2 * mn, 4)
    k['D']['rota'] = {
        'base': {'id': 'base', 'nome': 'Barra Sul', 'rel': 'da Barra Sul', 'perto': 'na saída da Barra Sul', 'lat': a[0], 'lon': a[1], 'prof_m': 8},
        'pontos': [{'id': 'cabras', 'nome': 'Ilha das Cabras', 'rel': 'da Ilha das Cabras', 'perto': 'ao largo da Ilha das Cabras', 'lat': b[0], 'lon': b[1], 'prof_m': 12}],
        'destino': {'id': 'cabras', 'nome': 'Ilha das Cabras', 'caminho': 'a caminho da Ilha das Cabras'},
        'volta': {'nome': 'Barra Sul (base)', 'caminho': 'a caminho da Barra Sul'},
        'pernas': [{'de': 'base', 'para': 'cabras', 'mn': mn, 'rumo': ida, 'ini_mn': 0.0}, {'de': 'cabras', 'para': 'base', 'mn': mn, 'rumo': volta, 'ini_mn': mn}],
        'distancia_mn': dist, 'ida_mn': mn, 'circuitos_dia': 19, 'fator': round(19 * dist / 311.5, 6), 'guinada_max_gps': 3,
        'corrente': {'nos': 0.3, 'para_graus': 200}}
    return k


def serie24v_do(D):
    """A serie24v (L, §1.13) do D mínimo: mín/máx da volta da bateria_0 + o desvio do dia (a fórmula do gerador, para a fixture não depender da série de hoje)."""
    R, c = D['replay'], 'bateria_0_tensao_v'
    vs = [C.quadro_laco(R, D['campos'], t)[c] for t in range(R['duracao'])]
    return [{'diasAtras': x, 'min': C.arred(min(vs) + C.desvio_em(D['historico'], c, x), 2), 'max': C.arred(max(vs) + C.desvio_em(D['historico'], c, x), 2),
             'd': G.dia_ddmm(-x)} for x in range(6, -1, -1)]


def com_historico(k):
    """O replay mínimo (com_replay) com um histórico mínimo e BEM FORMADO (C9, §1.13: 183 desvios, a curva do ano de 73 pontos, 60 dias de
    cruzeiro, as janelas do contrato) e a série 24 V coerente com ele. Só o campo do catálogo mínimo (bateria_0, BE) tem série."""
    k = com_replay(k)
    D = k['D']
    D['historico'] = {
        'fim': 'ancora', 'passo_dias': 2, 'n': 183,
        'desvios': {'bateria_0_tensao_v': {'escala': 100, 'd': ([0, 3, -6, 2] * 46)[:183]}},
        'sazonal': {'passo_dias': 5, 'n': 73, 'temp_ar_externo_c': {'escala': 10, 'd': G.sazonal_tabela(4.5, 15)}},
        'cruzeiro': {'dias': 60, 'motor_be_arref_c': {'escala': 10, 'd': [830] * 60}, 'motor_be_oleo_bar': {'escala': 100, 'd': [380] * 60}},
        'janelas': copy.deepcopy(G.JANELAS_HIST),
        'metricas': {'b24': ['bateria_0_tensao_v'], 'arref': ['motor_be_arref_c']}, 'so150': ['arref'],
        'fonte': 'coletor NMEA de bordo · histórico'}
    D['serie24v'] = serie24v_do(D)
    return k


def equip_completo(k):
    for e in k['D']['equipamentos']:
        e.update({'fabricante': e.get('fabricante') or 'Fabricante', 'modelo': 'Modelo 100', 'qtd': 1, 'guia': 'g_gerador'})
    return k


def poe(lista, i, **kw):
    lista[i] = dict(lista[i], **kw)


def por_id(lista, i):
    """O item de `lista` com esse id (levanta se não existe: a amostra que perde o alvo falha alto, não passa em silêncio)."""
    return next(x for x in lista if x.get('id') == i)


SEM = object()   # em muda(): tira a chave (None é valor: o NULO precisa dele)


def muda(k, lista, i, **kw):
    """hoje() com o item `i` de D[lista] mudado; o valor SEM tira a chave. Devolve k."""
    x = por_id(k['D'][lista], i)
    for c, v in kw.items():
        if v is SEM:
            x.pop(c, None)
        else:
            x[c] = v
    return k


RODAPE_OK = ("(function () { try {\n  var D = window.CapitaoDados, A = window.CapitaoAgora = {};\n"
             "  A.instante = function () { if (/SOS-/.test(location.pathname)) return null; var q = D.snapshot && D.snapshot.quadro;"
             " return q ? { q: q, fonte: 'snapshot' } : null; };\n  A.rebase = function (ms) { return true; };\n} catch (e) {} })();\n")


def mais_texto(k, txt):
    poe(k['D']['diario'], 0, t=k['D']['diario'][0]['t'] + txt)
    return k


# nome → (monta(ruim) → contexto, trecho esperado numa violação nova)
def com_ident(ident, com='pessoa quem', **resto):
    """hoje() com um trecho de segurança de teste que traz `ident` e `identCom` (None: sem identCom)."""
    k = hoje()
    t = {'fonte': 'Guia de bordo — Teste', 'secao': '1 · Teste', 'equip': 'Teste', 'seguranca': True, 'texto': 'Passo curto.', 'ident': ident}
    if com is not None:
        t['identCom'] = com
    t.update(resto)
    k['B']['trechos'].append(t)
    return k


AMOSTRAS = {
    'TERMOS': (lambda r: mais_texto(hoje(), ' (DEMO)' if r else ''), 'ROTULOS: diario[0].t'),
    'NULO': (lambda r: (lambda k: (k['D']['embarcacao'].update({'apelido': '' if r else 'CIA'}), k)[1])(hoje()), "embarcacao.apelido: ''"),
    'SIMULACAO_UNICA': (lambda r: (lambda k: (k['D']['embarcacao'].update({'simulacao': True}) if r else None, k)[1])(hoje()), '2 vez(es)'),
    # sobra em palavras curtas: uma sequência longa sem espaço deixaria as regex dos termos quadráticas (minutos)
    'TAMANHO': (lambda r: (lambda k: (k['D'].update({'sobra': 'abc ' * (33000 if r else 3)}), k)[1])(hoje()), 'capitao-dados.js'),
    'MMSI9': (lambda r: mais_texto(hoje(), ' Código 123456789.' if r else ''), 'diario[0].t'),
    'REGISTRO': (lambda r: (lambda k: (k['D']['embarcacao'].update({'registro': 'ABC-1234' if r else 'CIA-23-0417'}), k)[1])(hoje()), 'imita placa'),
    'HEX15': (lambda r: mais_texto(hoje(), ' ID 1D0F2A3B4C5D6E7.' if r else ''), 'diario[0].t'),
    'SEM_INDICATIVO': (lambda r: mais_texto(hoje(), ' Indicativo PU2ABC.' if r else ''), 'diario[0].t'),
    'AFIRMA_REAL': (lambda r: mais_texto(hoje(), ' Os dados são reais.' if r else ''), 'diario[0].t'),
    'PROTOCOLO_LIMPO': (lambda r: (lambda k: (k['D']['protocolos']['mob'].append('Pressão de 3,4 bar no motor.' if r else 'Confira o plotter.'), k)[1])(hoje()), 'protocolos.mob[3]'),
    'LOCAL_VOCAB': (lambda r: mais_texto(hoje(), ' Boia de reserva conferida.' if r else ''), 'diario[0].t'),
    'SEGURANCA_MARCADA': (lambda r: (lambda k: (k['B']['trechos'].append({'fonte': 'Guia de bordo — Teste', 'secao': '1 · Teste', 'equip': 'Teste',
                                                                          'texto': 'Extintor portátil à mão.' if r else 'Filtro limpo.'}), k)[1])(hoje()), '1 · Teste'),
    'SEM_SALVATAGEM_EM': (lambda r: (lambda k: (k['D'].update({'pecas': [{'id': 'p01', 'n': 'Colete salva-vidas' if r else 'Filtro de óleo', 'qtd': 1, 'min': 1,
                                                                          'local': 'estante técnica 1'}]}), k)[1])(hoje()), 'pecas[0].n'),
    'CALADO_FORA': (lambda r: (lambda k: (k['B']['trechos'].append({'fonte': 'Guia de bordo — Teste', 'secao': '1 · Teste', 'equip': 'Teste',
                                                                    'texto': 'O calado é de 1,1 m.' if r else 'Sonda ligada.'}), k)[1])(hoje()), '"calado"'),
    # (revisão 2 do C3) as duas contam por termo e por arquivo e não imprimem o termo: #n da lista e a assinatura do candidato
    'MODELOS_AVANTI': (lambda r: (lambda k: (k.update({'listas': {'valores.txt': ['zzq-termo-plantado'], 'modelos-avanti.txt': ['xx-nada']}}),
                                             mais_texto(k, ' ZZQ-termo-plantado.' if r else ''))[1])(hoje()), 'valores.txt #1: capitao-dados.js 1'),
    'COLISAO_MODELOS': (lambda r: (lambda k: (k.update({'avanti': 'manual do modelo xp-900 de outro barco'}),
                                              poe(k['D']['equipamentos'], 0, modelo='XP-900' if r else 'XQ-901'), k)[2])(hoje()),
                        'equipamentos[motores] candidato 1 (%s): 1 na pasta do Avanti' % C.assinatura('XP-900')),
    'FONTE_LIMITES': (lambda r: (lambda k: (k['D']['replay']['limites']['motor_be_arref_c']['critico'].update({'acima': 98 if r else 97}), k)[1])(com_replay(hoje())), 'sem os números'),
    # fabricante vazio nos motores (o C5 completou os 16 equipamentos do §1.4; a qtd que não é número fica nas EXTRAS)
    'EQUIP': (lambda r: (lambda k: (poe(k['D']['equipamentos'], 0, fabricante='') if r else None, k)[1])(hoje()), 'equipamentos[motores].fabricante ausente'),
    'IDS': (lambda r: (lambda k: (k['D'].update({'pecas': [{'id': 'p01', 'n': 'Filtro', 'qtd': 1, 'min': 1, 'local': 'estante técnica 1',
                                                           'tarefas': ['nao-existe' if r else 'motores-oleo']}]}), k)[1])(hoje()), 'fora da agenda'),
    'LACO': (lambda r: (lambda k: (k['D']['replay']['chaves'].update({'motor_be_rpm': [2040] * (29 if r else 30)}), k)[1])(com_replay(hoje())), 'replay.chaves.motor_be_rpm'),
    'LIMITES_FORMA': (lambda r: (lambda k: (k['D']['replay']['limites']['motor_be_arref_c']['normal'].update({'ate': 87 if r else 88}), k)[1])(com_replay(hoje())), 'o normal termina no aviso'),
    'JANELA': (lambda r: (lambda k: (k['D']['replay']['janelas'][0].update({'ini': 90 if r else 99}), k)[1])(com_replay(hoje())), 'precisa ficar em [95, 120]'),
    'FIO': (lambda r: (lambda k: (k['D']['replay']['chaves'].update({'motor_be_rpm': [2600 if r else 2040] + [2040] * 29}), k)[1])(com_replay(hoje())), 'a menos de 0,05 do limite'),
    'EMENDA_ROTA': (lambda r: (lambda k: (k['D']['rota'].update({'circuitos_dia': 18 if r else 19}), k)[1])(com_rota(hoje())), 'não é primo'),
    'PISO': (lambda r: (lambda k: (k['D']['replay'].update({'diesel_piso_l': 500 if r else 400}), k)[1])(com_replay(hoje())), 'o piso agiria'),
    'HORAS': (lambda r: (lambda k: (k['D']['agenda'][[t['id'] for t in k['D']['agenda']].index('motores-oleo')]['horas'].update({'limite': 430 if r else 450}), k)[1])(hoje()), 'agenda.motores-oleo'),
    'ROTA': (lambda r: (lambda k: (k['D']['rota']['pontos'][0].update({'nome': 'Ponto 2' if r else 'Ilha das Cabras'}), k)[1])(com_rota(hoje())), 'com dígito'),
    'DIA_DE_BORDO': (lambda r: (lambda k: (k['D']['replay']['diaDeBordo']['abastecimento'].update({'h': '06:45' if r else '07:00'}), k)[1])(com_replay(hoje())), 'ancora_hora'),
    'SEM_EMERGENCIA': (lambda r: mais_texto(hoje(), ' Bomba de porão não para.' if r else ''), 'emergencia()'),
    # Revisão do C7: troca a tarefa que já existe (antes, acrescentava um 2º `seafire-inspecao`, com o id repetido e uma 4ª atrasada) e põe
    # o gerador-rotor em dia no lugar, para ficarem as 3 atrasadas: a amostra acusa só a regra da salvatagem (a C7_REV a repete e exige 1 só)
    'AGENDA': (lambda r: (lambda k: (muda(k, 'agenda', 'seafire-inspecao', ultimaHa=370, venceEm=-5) if r else None,
                                     muda(k, 'agenda', 'gerador-rotor', ultimaHa=360, venceEm=5) if r else None, k)[2])(hoje()),
               'tarefa de salvatagem atrasada'),
    # C9: a fixture com_historico é bem formada (183 pontos), então a amostra troca UM ponto do desvio (antes trocava a lista inteira por [0, -400])
    'HISTORICO': (lambda r: (lambda k: (k['D']['historico']['desvios']['bateria_0_tensao_v']['d'].__setitem__(1, -400 if r else 3), k)[1])(com_historico(hoje())), 'o mínimo cruza'),
    'COORD_TEXTO': (lambda r: mais_texto(hoje(), " Fundeado em 26°59,6'S." if r else ''), 'diario[0].t'),
    'ROTULO_SEGURANCA': (lambda r: (lambda k: (k['D']['drive']['arquivos'].update({'g_epirb': 'Guia de bordo — EPIRB'}),
                                               k['B']['trechos'].append({'fonte': 'Guia de bordo — EPIRB', 'secao': '1 · Acionar', 'equip': 'EPIRB', 'seguranca': True,
                                                                         'texto': 'Só em perigo grave e iminente.' + ('' if r else ' ' + ROTULO_FIM)}), k)[2])(hoje()),
                         'sem o rótulo no fim'),
    # (revisão 4 do C5) o trecho de segurança é lido inteiro pelo cérebro e pela fala: até 800 letras
    'SEGURANCA_CURTA': (lambda r: (lambda k: (k['B']['trechos'].append({'fonte': 'Guia de bordo — Teste', 'secao': '1 · Teste', 'equip': 'Teste', 'seguranca': True,
                                                                        'texto': ('Passo curto. ' * (80 if r else 5)).strip()}), k)[1])(hoje()),
                        '(máximo 800'),
    # (revisão 5 do C5) `ident`: as palavras de acionamento do trecho de segurança não levam verbo de operação nem nome de equipamento
    # (revisão 6 do C5: nem de queda sem `identCom`; as amostras das outras palavras estão nas EXTRAS, com com_ident())
    'IDENT_BASE': (lambda r: com_ident('caiu desligar' if r else 'caiu cair'), 'ident com verbo de operação ou nome de equipamento (desligar)'),
    # a nota dos equipamentos de segurança é a NOTA_ETIQUETA desde o C5 e a do protocolos.seafire e do epirb, desde o C6
    'NOTA_ETIQUETA': (lambda r: (lambda k: (k['D']['protocolos']['seafire'].update({'nota': 'veja o manual' if r else C.NOTA}), k)[1])(hoje()),
                      'protocolos.seafire.nota'),
    # (C6) o D.protocolos do §1.3: a salvatagem do PROMPT §2.3 é letra por letra
    'PROTOCOLOS': (lambda r: (lambda k: (k['D']['protocolos'].update({'salvatagem': k['D']['protocolos']['salvatagem'].replace('um por pessoa', 'dois por pessoa') if r
                                                                      else k['D']['protocolos']['salvatagem']}), k)[1])(hoje()),
                   'protocolos.salvatagem: diferente do texto do contrato'),
    # (revisão do C6) §1.3: «Seafire», sem hífen nem espaço, em todo dado (as variantes e os lugares estão nas EXTRAS)
    'GRAFIA_SEAFIRE': (lambda r: mais_texto(hoje(), ' O Sea Fire fica pronto.' if r else ' O Seafire fica pronto.'),
                       'diario[0].t: texto com a grafia «Sea Fire» do Seafire'),
    'RODAPE_SNAPSHOT': (lambda r: (lambda k: (k.update({'rodape': RODAPE_OK.replace('return true;', 'D.snapshot.quadro = {}; return true;') if r else RODAPE_OK}), k)[1])(hoje()),
                        'rodape.js'),
    'FONTES_RELATIVAS': (lambda r: (lambda k: (k['F'].update({k['D']['drive']['pastas']['abast'] + '/Extra.csv': 'Data,Litros\n' + ('12/09/2026' if r else 'há 3 dias') + ',100\n'}), k)[1])(hoje()),
                         'Extra.csv'),
    # (revisão 3 do C3) as invariantes da §6.4 sem nome na §6.3: papéis em lista fechada e nenhum campo de previsão ou maré
    'TERCEIROS': (lambda r: (lambda k: (poe(k['D']['agenda'], 0, quem='Carlos Pereira' if r else 'técnico'), k)[1])(hoje()),
                  "agenda.porao-teste.quem: papel fora da lista fechada (§1.7): 'Carlos Pereira'"),
    'SEM_PREVISAO': (lambda r: (lambda k: (k['D'].update({'mare' if r else 'marRef': {'alta': '10:12', 'baixa': '16:30'}}), k)[1])(hoje()),
                     'mare: campo de previsão ou maré'),
    # (C4) a embarcação do §1.2: lotacao ≥ pessoasBordo
    'EMBARCACAO': (lambda r: (lambda k: (k['D']['embarcacao'].update({'lotacao': 3 if r else 12}), k)[1])(hoje()),
                   'embarcacao: lotacao (3) < pessoasBordo (4)'),
    # (revisão 7 do C5) trava 17: o modelo do EPIRB num guia (g_epirb §1) passava no gerador; só o D.protocolos e a agenda eram conferidos
    'SEGURANCA_SEM_MODELO': (lambda r: no_trecho('g_epirb', '1 · ', ' O modelo é o Ocean Signal SafeSea E100G.' if r else ' Confira a etiqueta do equipamento.'),
                             'base:trechos[%d].texto: fabricante ou modelo de equipamento de segurança [Ocean Signal]' % T_EPIRB1),
    # (C10) a forma e a referência do contrato dos checklists, sensores, peças e alarmes pedidos: a faixa do óleo de 0,5–6,0 bar passa a 0,5–7,0
    'FUNCOES': (lambda r: (lambda k: (por_id(k['D']['alarmesPedidos']['metricas'], 'oleo_bb').update({'faixa': [0.5, 7.0 if r else 6.0]}), k)[1])(hoje()),
                'alarmesPedidos.oleo_bb.faixa'),
    # (revisão 3 do C4) o Seakeeper 3 é de 12 V DC: o g_seakeeper §1 de antes ("Sem AC, o display avisa…") reprova
    'ESTABILIZADOR_12V': (lambda r: com_trecho({'fonte': G.GUIAS['g_seakeeper']['titulo'], 'secao': '1 · Teste', 'equip': 'Estabilizador Seakeeper',
                                                'texto': 'Sem AC, o display avisa e o volante não acelera.' if r else 'Com o banco de 12 V carregado.'}),
                          'energia AC num texto do estabilizador [AC]'),
}


def protocolo(campo, i, txt):
    """hoje() com protocolos.<campo>[i] = txt (i None: acrescenta)."""
    k = hoje()
    lista = k['D']['protocolos'][campo]
    if i is None:
        lista.append(txt)
    else:
        lista[i] = txt
    return k


def com_trecho(t, arquivos=None):
    k = hoje()
    k['D']['drive']['arquivos'].update(arquivos or {})
    k['B']['trechos'].append(t)
    return k


def com_rotulo(rot, diario=''):
    k = mais_texto(hoje(), diario)
    k['D']['protocolos']['rotulo'] = rot
    return k


# O protocolos do CONTRATO-DADOS §1.3 (o texto que o C6 grava): as regras da PROTOCOLO_LIMPO não podem reprová-lo.
PROTOCOLOS_C6 = {
    'rotulo': C.ROTULO, 'fonte': 'Protocolo de emergência — procedimento padrão · Drive › Capitão IA v2 › 07 Protocolos de emergência',
    'mmsiRadio': 'MMSI do rádio de bordo (etiqueta / Licença de Estação)', 'mmsiRotulo': 'MMSI (cadastro do app)',
    'indicativo': 'o da Licença de Estação (no rádio)', 'plotter': 'POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER · PESSOAS: CONTE AGORA',
    'hud': 'POSIÇÃO · LEIA NO PLOTTER',
    'canal16': {'canal': '16', 'mhz': '156,800', 'fonte': 'Protocolo de emergência — procedimento padrão · MAYDAY · canal 16'},
    'roteiro': ['MAYDAY, MAYDAY, MAYDAY', 'AQUI É CAPITÃO IA, CAPITÃO IA, CAPITÃO IA', 'MMSI — LEIA NA ETIQUETA DO RÁDIO (Licença de Estação)',
                'POSIÇÃO — LEIA NO PLOTTER AGORA', 'NATUREZA DO PERIGO: ________', 'PESSOAS A BORDO: conte agora', 'AUXÍLIO NECESSÁRIO: ________',
                'CÂMBIO'],
    'mob': ['Grite HOMEM AO MAR e o lado (bombordo ou boreste). Jogue a boia ou qualquer objeto que flutue.',
            'Uma pessoa só aponta para quem caiu, sem perder de vista. Marque MOB no plotter.',
            'Volte devagar, com o motor em neutro perto da pessoa (hélice). Se perder de vista: MAYDAY no canal 16 com a posição da marca MOB '
            'lida no plotter.'],
    'seafire': {'passos': ['Fogo no motor ou alarme do sistema fixo: desligue motores e gerador e corte a ventilação do motor.',
                           'Se o sistema não disparou sozinho e há fogo no motor, use o disparo manual.',
                           'Não abra o acesso ao motor depois da descarga: espere o tempo indicado na etiqueta do sistema e o motor esfriar.',
                           'Fogo pequeno fora do motor: extintor portátil na base das chamas, de costas para a saída.',
                           'Fogo que não apaga: MAYDAY no canal 16 e prepare o abandono.'], 'nota': C.NOTA},
    'epirb': {'passos': ['Só em perigo grave e iminente, depois do MAYDAY (ou sem rádio).',
                         'Acione conforme a etiqueta do equipamento e deixe a antena para cima, com céu aberto.',
                         'Leve o EPIRB para a balsa ou mantenha-o flutuando preso por um cabo. Não desligue até o resgate.',
                         'Disparo por engano: desligue e avise no canal 16.'],
              'teste': ['Teste da baliza (EPIRB): faça o autoteste conforme a etiqueta. O teste não envia alerta.',
                        'Confira na etiqueta a validade da bateria e do disparador hidrostático.'], 'nota': C.NOTA},
    'alagamento': ['Água entrando: ligue as bombas de porão no manual, procure a entrada (válvulas de fundo, mangueiras, eixos) e feche o que '
                   'puder. Água subindo mesmo assim: MAYDAY no canal 16.'],
    'abandono': ['Abandono: só quando não houver como manter o barco. Antes, MAYDAY no canal 16. Coletes em todos; leve o EPIRB e o VHF '
                 'portátil; embarque na balsa sem pular na água.'],
    'oleo': ['Reduza para marcha lenta e confira o manômetro agora.', 'Compare BB e BE no mesmo giro: só um lado baixo aponta o motor.',
             'Com o motor parado, procure vazamento e confira o nível de óleo na vareta.',
             'Se continuar baixa, desligue o motor afetado, siga com o outro e chame a oficina dos motores.'],
    'salvatagem': 'Em perigo agora: SOS do app e VHF canal 16. Coletes: um por pessoa — conte as pessoas a bordo agora (lotação: veja a placa '
                  'de lotação). Balsa, coletes, boias, extintores e sinalizadores: no local da placa de salvatagem e do plano de segurança de '
                  'bordo — confira na saída.',
    'panpan': 'Urgência sem perigo imediato de vida (pane, sem governo, alguém ferido sem risco de morte): PAN-PAN, PAN-PAN, PAN-PAN no canal '
              '16, no mesmo formato da chamada MAYDAY.',
    'dsc': 'O botão DISTRESS envia o alerta com a identificação programada no rádio: é o MMSI do rádio de bordo (etiqueta / Licença de '
           'Estação). Depois do alerta, faça o MAYDAY por voz no canal 16.',
}
T_EPIRB = {'fonte': 'Guia de bordo — EPIRB', 'secao': '4 · Validade', 'equip': 'EPIRB',
           'texto': 'Confira a data da bateria e do disparador hidrostático. ' + ROTULO_FIM}
T_SEAFIRE = {'fonte': 'Guia de bordo — Sistema fixo de incêndio', 'secao': '3 · Depois da descarga', 'equip': 'Sistema fixo de supressão de incêndio',
             'texto': 'Não abra o acesso ao motor antes do tempo da etiqueta. ' + ROTULO_FIM}
T_PORAO = {'fonte': 'Guia de bordo — Bombas de porão Rule', 'secao': '4 · Teste', 'equip': 'Bombas de porão Rule Rule 2000 (24 V)',
           'texto': 'Ligue as bombas no manual e confira a descarga.'}
# O texto de hoje onde a amostra do dado da embarcação entra (roteiro[1]: troca; mob: acrescenta, e o bom acrescenta este).
BOM_SOS = {'roteiro': 'AQUI É CAPITÃO IA, CAPITÃO IA, CAPITÃO IA', 'mob': 'Confira o plotter.'}
# Amostras extras dos achados da revisão do C3: (asserção, o que mostra, monta(ruim) → contexto, trecho esperado numa violação nova)
EXTRAS = [
    ('PROTOCOLO_LIMPO', 'número de pessoas no roteiro', lambda r: protocolo('roteiro', 5, 'PESSOAS A BORDO: 4' if r else 'PESSOAS A BORDO: conte agora'),
     'protocolos.roteiro[5]: número de pessoas'),
    ('PROTOCOLO_LIMPO', 'roteiro em maiúsculas: "4 PESSOAS A BORDO"', lambda r: protocolo('roteiro', 5, '4 PESSOAS A BORDO' if r else 'PESSOAS A BORDO: conte agora'),
     'protocolos.roteiro[5]: regex de emergência'),
    ('PROTOCOLO_LIMPO', 'pessoas por extenso', lambda r: protocolo('roteiro', 5, 'QUATRO PESSOAS A BORDO' if r else 'PESSOAS A BORDO: conte agora'),
     'protocolos.roteiro[5]: número de pessoas'),
    ('PROTOCOLO_LIMPO', 'roteiro em maiúsculas: "ÚLTIMO FIX"', lambda r: protocolo('roteiro', 3, 'ÚLTIMO FIX 07:31' if r else 'POSIÇÃO — LEIA NO PLOTTER AGORA'),
     'protocolos.roteiro[3]: regex de emergência'),
    ('PROTOCOLO_LIMPO', 'lotação com número', lambda r: protocolo('mob', None, 'Lotação: 12.' if r else 'Confira a placa de lotação.'),
     'protocolos.mob[3]: número de pessoas'),
    ('PROTOCOLO_LIMPO', 'tripulantes com número', lambda r: protocolo('mob', None, '3 tripulantes no convés.' if r else 'Confira o plotter.'),
     'protocolos.mob[3]: número de pessoas'),
    ('PROTOCOLO_LIMPO', 'roteiro em maiúsculas: "3,4 BAR"', lambda r: protocolo('roteiro', 4, 'PRESSÃO 3,4 BAR' if r else 'NATUREZA DO PERIGO: ________'),
     'protocolos.roteiro[4]: " bar"'),
    ('PROTOCOLO_LIMPO', 'minuto no singular', lambda r: protocolo('mob', None, 'Espere 1 minuto.' if r else 'Espere a indicação.'),
     'protocolos.mob[3]: minutos'),
    ('PROTOCOLO_LIMPO', '"ULTIMO FIX" sem o acento', lambda r: protocolo('roteiro', 3, 'ULTIMO FIX' if r else 'POSIÇÃO — LEIA NO PLOTTER AGORA'),
     'protocolos.roteiro[3]: último fix'),
] + [('PROTOCOLO_LIMPO', 'lugar a bordo: %r' % frase, (lambda f: lambda r: protocolo('mob', None, f if r else 'Confira o plotter.'))(frase),
      'protocolos.mob[3]: lugar a bordo') for frase in (
    'Pegue o extintor na praça de máquinas.', 'Coletes no paiol de proa.', 'Leve o EPIRB da cabine do comandante.',
    'Balsa no flybridge: solte e jogue.', 'Na popa, solte a balsa.')] + [
    # C5: a base tem os 91 trechos do §1.5, e o plantado entra no fim (antes, no índice 46)
    ('SEGURANCA_MARCADA', 'g_epirb §4 sem palavra da lista (só a fonte casa)', lambda r: com_trecho(dict(T_EPIRB, seguranca=True) if not r else T_EPIRB),
     'base:trechos[%d] (Guia de bordo — EPIRB · 4 · Validade) casa' % len(G.base_conhecimento()['trechos'])),
    ('SEGURANCA_MARCADA', 'g_seafire §3 sem palavra da lista (fonte e equip casam)', lambda r: com_trecho(dict(T_SEAFIRE, seguranca=True) if not r else T_SEAFIRE),
     '3 · Depois da descarga) casa'),
    ('SEGURANCA_MARCADA', 'seção do mínimo do §1.5 sem palavra (g_porao §4)',
     lambda r: com_trecho(dict(T_PORAO, seguranca=True) if not r else T_PORAO, {'g_porao': T_PORAO['fonte']}), 'no mínimo do §1.5 (g_porao)'),
    ('SEGURANCA_MARCADA', 'item do FAQ do mínimo (EP-04) sem palavra',
     lambda r: (lambda k: (k.update({'faq': {'itens': [dict({'id': 'EP-04', 'titulo': 'Validade', 'resposta': 'Confira a data. ' + ROTULO_FIM},
                                                           **({} if r else {'seguranca': True}))]}}), k)[1])(hoje()), 'faq:EP-04'),
    ('ROTULO_SEGURANCA', 'protocolos.rotulo diferente do texto fixo', lambda r: com_rotulo('procedimento padrão' if r else C.ROTULO), 'protocolos.rotulo'),
    # C5: antes do D.replay (C8), a FONTE_LIMITES conferia a constante LIMITES do gerador contra os guias; desde o C8 as duas são uma só (a amostra muda as duas).
    ('FONTE_LIMITES', 'LIMITES com número que o guia não tem (a constante do gerador e o D.replay.limites, que são uma só desde o C8)',
     lambda r: com_limites(limites_com(('motor_bb_arref_c', 'critico', 'acima'), 98 if r else 97)),
     'limites.motor_bb_arref_c: Guia de bordo — Motores Cummins §9 · Faixas de operação sem os números'),
    ('FONTE_LIMITES', 'LIMITES apontando para um § que não existe',
     lambda r: com_limites(limites_com(('gerador_kw', 'fonte'), G.ARQ['g_gerador'] + (' §12 · Carga' if r else ' §9 · Potência e carga'))),
     'limites.gerador_kw.fonte aponta para um § que não existe'),
    ('FONTE_LIMITES', 'D.replay.limites diferente da constante LIMITES do gerador',
     lambda r: (lambda k: (k.update({'const': CONST if r else dict(CONST, LIMITES=k['D']['replay']['limites'])}), k)[1])(com_replay(hoje())),
     'replay.limites ≠ a constante LIMITES do gerador'),
    ('TERMOS', 'termo posto no protocolos.rotulo é acusado e não apaga o resto (não cai de 101 para 29)',
     lambda r: com_rotulo('SEM DADOS' if r else C.ROTULO), 'ROTULOS: protocolos.rotulo'),
    ('TERMOS', 'rótulo trocado por "fictício" não apaga o "fictício" do diário',
     lambda r: com_rotulo('fictício', ' Valores fictícios.' if r else ''), 'AUTENTICIDADE: diario[0].t'),
    ('NOTA_ETIQUETA', 'constante do gerador diferente do texto do §1.4',
     lambda r: (lambda k: (k.update({'const': dict(CONST, NOTA_ETIQUETA='veja o manual' if r else C.NOTA)}), k)[1])(hoje()), 'NOTA_ETIQUETA do gerador'),
    # desde o C5 a qtd é número em todos (antes, a qtd '2' de texto dos motores era pendência): None é violação nova
    ('EQUIP', 'qtd que não é número, num caminho com pendência', lambda r: (lambda k: (poe(k['D']['equipamentos'], 0, qtd=None if r else 2), k)[1])(equip_completo(hoje())),
     'equipamentos[motores].qtd não é número: None'),
] + [
    # Revisão 2 do C3. RODAPE_SNAPSHOT: só a leitura D.snapshot.quadro e o valor fonte: 'snapshot', dentro de instante() e depois da
    # guarda; os comentários saem sem cortar dentro de string ('https://' não apaga o resto da linha).
    ('RODAPE_SNAPSHOT', o_que, (lambda a, b: lambda r: (lambda k: (k.update({'rodape': rodape(a if r else '', b if r else '')}), k)[1])(hoje()))(a, b),
     espera) for o_que, a, b, espera in (
        ("D['snapshot'].quadro = {} dentro de instante()", "D['snapshot'].quadro = {};", '', 'rodape.js:2 cita snapshot fora das formas aceitas'),
        ('D.snapshot.quadro.alarmes.push(1) dentro de instante()', 'D.snapshot.quadro.alarmes.push(1);', '', 'rodape.js:2 escreve em D.snapshot'),
        ('var s = D.snapshot; s.quadro = {} dentro de instante()', 'var s = D.snapshot; s.quadro = {};', '', 'rodape.js:2 cita snapshot fora das formas aceitas'),
        ("'https://x' e D.snapshot.quadro = {} na mesma linha, fora de instante()", '', "var u = 'https://x'; D.snapshot.quadro = {};",
         'rodape.js:3 escreve em D.snapshot'),
        ('modelo `${D.snapshot.quadro}` dentro de instante()', 'var t = `q=${D.snapshot.quadro}`;', '', 'rodape.js:2 cita snapshot fora das formas aceitas'),
        ('Object.assign(D.snapshot.quadro, …) dentro de instante()', 'Object.assign(D.snapshot.quadro, {rpm: 1});', '', 'rodape.js:2 escreve em D.snapshot'))] + [
    ('RODAPE_SNAPSHOT', 'leitura antes da guarda /SOS-/', lambda r: (lambda k: (k.update({'rodape': RODAPE_OK.replace(
        'if (/SOS-/', 'var p = D.snapshot.quadro; if (/SOS-/') if r else RODAPE_OK}), k)[1])(hoje()), 'antes da guarda /SOS-/'),
    # MMSI9 e HEX15: número também conta (pelo repr), e cada ocorrência conta (um 2º MMSI numa string com pendência reprova).
    ('MMSI9', '9 dígitos guardados como número', lambda r: (lambda k: (k['D']['embarcacao'].update({'mmsiExtra': 123456789 if r else 12345}), k)[1])(hoje()),
     'embarcacao.mmsiExtra: 123456789'),
    ('MMSI9', '710123456 como número no snapshot', lambda r: (lambda k: (k['D']['snapshot'].update({'mmsi': 710123456 if r else 7101}), k)[1])(hoje()),
     'snapshot.mmsi: 710123456'),
    # C5: o trecho do DSC (g_eletronicos §5) é o MMSI_RADIO, sem número; até o C5 a frase antiga dele era pendência.
    ('MMSI9', '9 dígitos no trecho do DSC (MMSI_RADIO, sem número desde o C5)',
     lambda r: com_base(T_DSC, ' Outro 987654321.' if r else ''), 'base:trechos[%d].texto: 987654321' % T_DSC),
    ('MMSI9', 'o MMSI do cadastro no trecho do DSC',
     lambda r: com_base(T_DSC, ' MMSI 710123456.' if r else ''), 'base:trechos[%d].texto: 710123456' % T_DSC),
    ('MMSI9', 'número de 9 dígitos num JSON das fontes', lambda r: com_json(lambda j: j.update({'mmsi': 710123456 if r else 7101})), ':mmsi: 710123456'),
    ('HEX15', '15 dígitos guardados como número', lambda r: (lambda k: (k['D']['snapshot'].update({'id': 123456789012345 if r else 1234}), k)[1])(hoje()),
     'snapshot.id: 123456789012345'),
    ('HEX15', 'duas ocorrências na mesma string', lambda r: mais_texto(hoje(), ' ID 1D0F2A3B4C5D6E7 e 1D0F2A3B4C5D6E8.' if r else ' ID 1D0F2A3B4C5D6E7.'),
     'diario[0].t: 1D0F2A3B4C5D6E8'),
    # AGENDA: a referência é a tabela fixa do §1.7, nunca a constante do gerador conferido.
    ('AGENDA', 'DIAS_MESES do gerador diferente do §1.7',
     lambda r: (lambda k: (k.update({'const': dict(CONST, DIAS_MESES={1: 30, 6: 183, 12: 365} if r else dict(G.DIAS_MESES))}), k)[1])(hoje()),
     'DIAS_MESES do gerador ≠ o do §1.7'),
    ('AGENDA', 'tarefa coerente só com a constante trocada (20 + 10 com 1 mês = 30)',
     lambda r: (lambda k: (k.update({'const': dict(CONST, DIAS_MESES={1: 30, 6: 183, 12: 365} if r else dict(G.DIAS_MESES))}),
                           k['D']['agenda'].append({'id': 'nova', 'meses': 1, 'ultimaHa': 20 if r else 21, 'venceEm': 10}), k)[2])(hoje()),
     'agenda.nova: ultimaHa + venceEm ≠ DIAS_MESES[meses]'),
    # NULO: também a base, o FAQ e os JSON das fontes (o pag: null saiu dos trechos no C5).
    ('NULO', "base com secao '' e equip null", lambda r: (lambda k: (poe(k['B']['trechos'], 3, **({'secao': '', 'equip': None} if r else {})), k)[1])(hoje()),
     "base:trechos[3].secao: ''"),
    ('NULO', 'null num JSON das fontes', lambda r: com_json(lambda j: j.update({'extra': None if r else 1})), ':extra: None'),
    ('NULO', 'lista vazia no FAQ', lambda r: (lambda k: (k.update({'faq': {'itens': [] if r else [{'id': 'EL-01'}]}}), k)[1])(hoje()), 'faq:itens: lista vazia'),
] + [
    # Revisão 3 do C3. AFIRMA_REAL e PROTOCOLO_LIMPO: uma violação por ocorrência; a pendência prende o texto casado de hoje, e
    # uma 2ª afirmação (ou um ETA) num caminho que já é pendência reprova.
    # C5: a frase antiga do MMSI ("no barco real, programe…") saiu das 3 cópias; a afirmação plantada nelas reprova.
    ('AFIRMA_REAL', 'afirmação no trecho do DSC (base)',
     lambda r: com_base(T_DSC, ' Os dados são reais e o barco é real.' if r else ''), 'base:trechos[%d].texto: dados são reais' % T_DSC),
    ('AFIRMA_REAL', 'afirmação no passo do DSC do FAQ de eletrônicos',
     lambda r: com_faq_passo(' A navegação é real.' if r else ''), 'faq.eletronicos.perguntas[3].passos[1].t: navegação é real'),
    ('AFIRMA_REAL', 'afirmação em outra seção da página do guia de eletrônicos',
     lambda r: com_eletronicos('<h2>9 · Extra</h2><p>Os dados do barco são reais.</p>' if r else '<h2>9 · Extra</h2><p>Confira o plotter.</p>'),
     '.html: barco são reais'),
    ('PROTOCOLO_LIMPO', '"ETA" no roteiro[2], que já é pendência (710123456)',
     lambda r: protocolo('roteiro', 2, hoje()['D']['protocolos']['roteiro'][2] + (' · ETA' if r else '')), 'protocolos.roteiro[2]: regex de emergência [ETA]'),
    ('PROTOCOLO_LIMPO', 'modelo curto com o fabricante na frente ("Lewmar V2", §2.5), com os equipamentos do §1.4',
     lambda r: (lambda k: (k['D']['protocolos']['mob'].append('Guincho Lewmar V2 pronto.' if r else 'Guincho pronto.'), k)[1])(com_equip_c5(hoje())),
     'protocolos.mob[3]: fabricante ou modelo de equipamento [Lewmar V2]'),
    # COORD_TEXTO: a forma do semCoord de hoje (minutos inteiros com o hemisfério), os segundos, o "º" e o par de CSV com sinal.
] + [('COORD_TEXTO', 'coordenada %r' % c, (lambda c: lambda r: mais_texto(hoje(), (' Fundeado em %s.' % c) if r else ''))(c), 'diario[0].t')
     for c in ("26°59'S 048°36'W", '26°59\'35" S', "26º59,6'S", '-26.993,-48.614')] + [
    # SEM_INDICATIVO: indicativo de estação de navio (2 letras e 4 dígitos), e o de 4 letras depois da palavra "indicativo".
    ('SEM_INDICATIVO', 'indicativo de navio PU1234 (sem a palavra "indicativo")', lambda r: mais_texto(hoje(), ' Chamada de teste da PU1234.' if r else ''),
     'diario[0].t: PU1234'),
    ('SEM_INDICATIVO', 'indicativo de navio PS7612', lambda r: mais_texto(hoje(), ' Rádio PS7612 testado.' if r else ''), 'diario[0].t: PS7612'),
    ('SEM_INDICATIVO', 'indicativo de 4 letras depois de "indicativo"', lambda r: mais_texto(hoje(), ' Indicativo de chamada: PPXA.' if r else ''),
     'Indicativo de chamada: PPXA'),
    # §0.2: HEX ID, telefone e lugar de equipamento de salvatagem não existem como campo.
    ('SEM_INDICATIVO', 'lugar do EPIRB como campo (equipamentos[epirb].local)',
     lambda r: (lambda k: (poe(k['D']['equipamentos'], 7, **({'local': 'paiol de proa'} if r else {})), k)[1])(hoje()), 'equipamentos[7].local: chave de lugar'),
    ('SEM_INDICATIVO', 'onde num item do checklist', lambda r: (lambda k: (k['D'].update({'checklists': {'itens': {'saida': [
        dict({'id': 's13', 't': 'Coletes conferidos.', 'c': 'coletes'}, **({'onde': 'cabine de proa'} if r else {}))]}}}), k)[1])(hoje()),
     'checklists.itens.saida[0].onde: chave de lugar'),
    ('SEM_INDICATIVO', 'HEX ID como campo', lambda r: (lambda k: (poe(k['D']['equipamentos'], 7, **({'hexId': 'cadastrar'} if r else {})), k)[1])(hoje()),
     'equipamentos[7].hexId: chave de HEX ID'),
    ('SEM_INDICATIVO', 'telefone como campo', lambda r: (lambda k: (poe(k['D']['equipe']['apoio'], 0, **({'telefone': 'cadastrar'} if r else {})), k)[1])(hoje()),
     'equipe.apoio[0].telefone: chave de telefone'),
    ('SEM_INDICATIVO', 'telefone como campo num JSON das fontes', lambda r: com_json(lambda j: j.update({'telefone_marina' if r else 'marina': 'x'})),
     ':telefone_marina: chave de telefone'),
    # MMSI9: nada de "programe" perto de MMSI (§6.4), também sem o número e num caminho que já é pendência.
    ('MMSI9', '"programe o MMSI" sem o número', lambda r: mais_texto(hoje(), ' Programe o MMSI no rádio.' if r else ''), 'diario[0].t: "programe" perto de MMSI'),
    ('MMSI9', '"programar" perto de MMSI no trecho do DSC',
     lambda r: com_base(T_DSC, ' Para programar o rádio, use o MMSI.' if r else ''), 'base:trechos[%d].texto: "programar" perto de MMSI' % T_DSC),
    # TERCEIROS: papéis em lista fechada; só o TIE tem número.
    ('TERCEIROS', 'nome de terceiro no papel do prestador',
     lambda r: (lambda k: (poe(k['D']['equipe']['apoio'], 0, papel='João da Silva (marina)' if r else 'Marina da base'), k)[1])(hoje()),
     "equipe.apoio[0].papel: papel fora da lista fechada (§1.11): 'João da Silva (marina)'"),
    ('TERCEIROS', 'nome de terceiro no who do diário', lambda r: (lambda k: (poe(k['D']['diario'], 0, who='Carlos' if r else 'técnico'), k)[1])(hoje()),
     "who: papel fora da lista fechada (§1.7): 'Carlos'"),
    ('TERCEIROS', 'número de apólice como campo', lambda r: (lambda k: (poe(k['D']['documentos'], 1, **({'numero': 'apólice 01.23.456'} if r else {})), k)[1])(hoje()),
     'documentos[1].numero: chave de número ou emissor'),
    ('TERCEIROS', 'número de apólice no texto', lambda r: (lambda k: (poe(k['D']['documentos'], 1, nota='apólice nº 01.23.456 no Drive' if r else 'apólice no Drive'), k)[1])(hoje()),
     'documentos[1].nota: número de documento [apólice nº 0'),
    ('TERCEIROS', 'número da NF no diário', lambda r: mais_texto(hoje(), ' NF 4512 conferida.' if r else ' NF conferida.'), 'diario[0].t: número de documento [NF 4'),
    # SEM_PREVISAO: nem no historico, nem no catálogo de campos, nem nos JSON das fontes.
    ('SEM_PREVISAO', 'grupo de maré no historico', lambda r: (lambda k: (k['D']['historico']['metricas'].update({'mare' if r else 'b24b': ['bateria_0_tensao_v']}), k)[1])(com_historico(hoje())),
     'historico.metricas.mare: campo de previsão'),
    ('SEM_PREVISAO', 'campo de maré no catálogo', lambda r: (lambda k: (k['D']['campos'].update({'mare_altura_m' if r else 'ondas_m': {'rotulo': 'x', 'un': 'm', 'casas': 1, 'origem': 'fixo'}}),
                                                                       k['D']['replay']['fixos'].update({'mare_altura_m' if r else 'ondas_m': 1.0}), k)[2])(com_replay(hoje())),
     'campos.mare_altura_m: campo de previsão'),
    ('SEM_PREVISAO', 'previsão num JSON das fontes', lambda r: com_json(lambda j: j.update({'previsao_vento_nos' if r else 'vento_nos': 12})), ':previsao_vento_nos: campo de previsão'),
] + [
    # C4 (§1.2): os campos completos e com o tipo, rotulo e motorizacao gerados dos campos, unidades, tanques e as pessoas do diário.
    ('EMBARCACAO', 'calado ausente', lambda r: com_embarcacao(calado=None if r else 1.1), 'embarcacao.calado ausente ou fora do tipo'),
    ('EMBARCACAO', 'ano como texto', lambda r: com_embarcacao(ano='2023' if r else 2023), 'embarcacao.ano ausente ou fora do tipo'),
    ('EMBARCACAO', 'pessoas a bordo zero', lambda r: com_embarcacao(pessoasBordo=0 if r else 4), 'embarcacao.pessoasBordo ausente ou fora do tipo'),
    ('EMBARCACAO', 'rotulo que não sai dos campos', lambda r: com_embarcacao(rotulo='Marévia 40 HT · 12,4 m · 2023' if r else 'Marévia 40 HT · 12,40 m · 2023'),
     'embarcacao.rotulo ≠ o gerado dos campos'),
    ('EMBARCACAO', 'motorizacao fora do formato', lambda r: com_embarcacao(motorizacao='Cummins QSB6.7 305' if r else '2 × Cummins QSB6.7 305 · eixo'),
     'embarcacao.motorizacao fora do formato'),
    ('EMBARCACAO', 'motorizacao diferente do equipamentos[motores] do §1.4 (C5)',
     lambda r: (lambda k: (k['D']['embarcacao'].update({'motorizacao': '2 × Cummins QSB6.7 380 · eixo' if r else '2 × Cummins QSB6.7 305 · eixo'}), k)[1])(motores_c5()),
     'embarcacao.motorizacao ≠ qtd, fabricante e modelo de equipamentos[motores]'),
    ('EMBARCACAO', 'unidade trocada', lambda r: com_embarcacao(un=dict(hoje()['D']['embarcacao']['un'], boca='pés' if r else 'm')), 'embarcacao.un.boca ≠'),
    ('EMBARCACAO', 'unidade de campo que não existe', lambda r: com_embarcacao(un=dict(hoje()['D']['embarcacao']['un'], **({'pontal': 'm'} if r else {}))),
     'embarcacao.un.pontal: unidade de campo que não é número'),
    ('EMBARCACAO', 'tanque de diesel diferente da capacidade do snapshot',
     lambda r: com_embarcacao(tanques=dict(hoje()['D']['embarcacao']['tanques'], diesel_l=1500 if r else 1600)), 'embarcacao.tanques.diesel_l ≠ snapshot.diesel.capacidade'),
    ('EMBARCACAO', 'tanque sem volume', lambda r: com_embarcacao(tanques=dict(hoje()['D']['embarcacao']['tanques'], agua_l=0 if r else 400)),
     'embarcacao.tanques.agua_l ausente ou fora do tipo'),
    ('EMBARCACAO', 'pessoas a bordo no diário diferente de pessoasBordo', lambda r: mais_texto(hoje(), ' Saída com 6 pessoas a bordo.' if r else ''),
     'diario[0]: 6 pessoas a bordo ≠ embarcacao.pessoasBordo (4)'),
    # Revisão do C4 (modo real, §0.12 e §4.3): o derivado de um None é None; "None" no texto e rotulo sem o campo de origem reprovam.
    ('EMBARCACAO', 'rotulo com "None" no texto (modo real)', lambda r: em_modo_real(modelo=None, rotulo='None · 12,40 m · 2023' if r else None),
     "embarcacao.rotulo com campo sem valor no texto (o derivado de um None é None): 'None · 12,40 m · 2023'"),
    ('EMBARCACAO', 'rotulo presente sem o campo de origem (modo real)',
     lambda r: em_modo_real(comprimento=None, rotulo='Marévia 40 HT · 12,40 m · 2023' if r else None),
     'embarcacao.rotulo presente sem o campo de origem (comprimento None'),
    ('EMBARCACAO', 'motorizacao com "None" no texto', lambda r: com_embarcacao(motorizacao='2 × None QSB6.7 305 · eixo' if r else '2 × Cummins QSB6.7 305 · eixo'),
     "embarcacao.motorizacao com campo sem valor no texto (o derivado de um None é None): '2 × None QSB6.7 305 · eixo'"),
    ('EMBARCACAO', 'motorizacao presente com os motores sem modelo (modo real)',
     lambda r: (lambda k: (poe(k['D']['equipamentos'], 0, modelo=None), k)[1])(em_modo_real(motorizacao='2 × Cummins QSB6.7 305 · eixo' if r else None)),
     'embarcacao.motorizacao presente com equipamentos[motores] sem fabricante, modelo ou qtd'),
] + [('PROTOCOLO_LIMPO', 'dado gerado da embarcação: %s' % o_que, (lambda c, i, t: lambda r: protocolo(c, i, t if r else BOM_SOS[c]))(c, i, t),
      'protocolos.%s[%d]: dado gerado da embarcação (%s) [%s]' % (c, 1 if c == 'roteiro' else 3, campo, casado))
     for o_que, c, i, t, campo, casado in (
    # Revisão 2 do C4 (trava §2.1; CONTRATO §1.3): o protocolos é a única fonte do SOS, e nenhum dado gerado da embarcação além do
    # nome entra nele (confere.barco_sos, tirada do próprio D), sem distinguir maiúsculas nem acentos. Antes, só o número de pessoas
    # e a lotação reprovavam: o registro, o fabricante, o modelo, o rotulo e a motorizacao no roteiro e no MOB davam 0 violações.
    ('registro no roteiro', 'roteiro', 1, 'AQUI É CAPITÃO IA · REGISTRO CIA-23-0417', 'registro', 'CIA-23-0417'),
    ('registro com espaços', 'roteiro', 1, 'REGISTRO CIA 23 0417', 'registro', 'CIA 23 0417'),
    ('registro sem separador', 'roteiro', 1, 'REGISTRO CIA230417', 'registro', 'CIA230417'),
    ('fabricante em maiúsculas', 'roteiro', 1, 'MARÉVIA 40 HT, ESTALEIRO MARÉVIA', 'fabricante', 'ESTALEIRO MARÉVIA'),
    ('modelo sem o acento', 'roteiro', 1, 'AQUI É MAREVIA 40 HT', 'modelo', 'MAREVIA 40 HT'),
    ('marca depois do nome', 'roteiro', 1, 'AQUI É CAPITÃO IA — MARÉVIA', 'marca', 'MARÉVIA'),
    ('rotulo', 'roteiro', 1, 'Marévia 40 HT · 12,40 m · 2023', 'rotulo', 'Marévia 40 HT · 12,40 m · 2023'),
    ('motorizacao no MOB', 'mob', None, '(2 × Cummins QSB6.7 305 · eixo)', 'motorizacao', '2 × Cummins QSB6.7 305 · eixo'),
    ('marca do motor', 'mob', None, 'Motores Cummins em neutro.', 'motor', 'Cummins'),
    ('comprimento', 'mob', None, 'Barco de 12,4 m.', 'comprimento', '12,4 m'),
    ('boca por extenso', 'mob', None, 'Boca de 3,95 metros.', 'boca', '3,95 metros'),
    ('calado', 'mob', None, 'Calado 1,10 m.', 'calado', '1,10 m'),
    # (fechamento do C5: o deslocamento passou de 10,4 t a 9,3 t para caber no Seakeeper 3 nas duas leituras de "tons"; o dado de hoje manda)
    ('deslocamento', 'mob', None, 'Deslocamento de 9,3 t.', 'deslocamento', '9,3 t'),
    ('ano', 'mob', None, 'Barco de 2023.', 'ano', '2023'),
    ('base sem a UF', 'mob', None, 'Base: Balneário Camboriú.', 'base', 'Balneário Camboriú'),
    ('base sem acento, em maiúsculas', 'roteiro', 1, 'BASE BALNEARIO CAMBORIU (SC)', 'base', 'BALNEARIO CAMBORIU (SC)'),
    ('tanque de diesel', 'mob', None, 'Diesel: 1.600 L.', 'tanques.diesel_l', '1.600 L'),
    ('cada tanque de diesel', 'mob', None, 'Tanque BB de 800 litros.', 'tanques.diesel_l (cada tanque)', '800 litros'))] + [
    # Revisão 3 do C4: fora do guia do estabilizador, a frase que o cita (o checklist de antes, o diário, com "CA" também); onde o
    # caminho o cita, o texto inteiro, mesmo a frase sem a palavra (o passo do D.faq.estabilizador e a página de fonte do guia).
    ('ESTABILIZADOR_12V', 'frase do checklist ("precisa de AC")',
     lambda r: com_trecho({'fonte': G.GUIAS['checklist']['titulo'], 'secao': 'Saída · teste', 'equip': 'Checklist de bordo',
                           'texto': '1. Gerador: confira a água. 2. Estabilizador: ligue com antecedência%s. 3. Climatização: filtro limpo.'
                                    % (' (precisa de AC)' if r else '')}),
     'energia AC num texto do estabilizador [AC] «… com antecedência (precisa de AC).»'),
    ('ESTABILIZADOR_12V', 'frase do diário com "CA"', lambda r: mais_texto(hoje(), ' Seakeeper ligado na energia CA do cais.' if r else ''),
     'diario[0].t: energia AC num texto do estabilizador [CA]'),
    ('ESTABILIZADOR_12V', 'passo do D.faq.estabilizador sem a palavra',
     lambda r: com_estab_faq(' Ligue a corrente alternada antes.' if r else ''),
     'faq.estabilizador.perguntas[0].passos[0].t: energia AC num texto do estabilizador [corrente alternada]'),
    ('ESTABILIZADOR_12V', 'página de fonte do guia, frase sem a palavra',
     lambda r: com_estab_fonte(' <p>Sem AC, o volante não acelera.</p>' if r else ''),
     'Guia de bordo — Estabilizador Seakeeper.html: energia AC num texto do estabilizador [AC]')]


def com_limites(lim):
    """hoje() com a constante LIMITES do gerador e o D.replay.limites trocados por `lim` (desde o C8 as duas são uma só)."""
    k = hoje()
    k['D']['replay']['limites'] = lim
    k['const'] = dict(CONST, LIMITES=lim)
    return k


def limites_com(caminho, valor):
    """Cópia da constante LIMITES do gerador com um valor trocado (caminho = (campo, chave, …))."""
    L = copy.deepcopy(G.LIMITES)
    x = L
    for k in caminho[:-1]:
        x = x[k]
    x[caminho[-1]] = valor
    return L


def com_estab_faq(extra):
    """hoje() com `extra` no fim do 1º passo do D.faq.estabilizador."""
    k = hoje()
    k['D']['faq']['estabilizador']['perguntas'][0]['passos'][0]['t'] += extra
    return k


def com_estab_fonte(extra):
    """hoje() com `extra` no fim da página de fonte do guia do estabilizador (fontes do Drive)."""
    k = hoje()
    rel = next(r for r in k['F'] if r.endswith('/' + G.GUIAS['g_seakeeper']['titulo'] + '.html'))
    k['F'][rel] += extra
    return k


def com_nota_equipe(txt):
    """hoje() com `txt` na nota da equipe (D.equipe.nota)."""
    k = hoje()
    k['D']['equipe']['nota'] = txt
    return k


def com_fonte_final(sufixo, extra):
    """hoje() com `extra` no fim da página de fonte do Drive cujo nome termina em `sufixo`."""
    k = hoje()
    rel = next(r for r in sorted(k['F']) if r.endswith(sufixo))
    k['F'][rel] += extra
    return k


def com_coluna(sufixo, coluna, valor=''):
    """hoje() com uma coluna nova (o cabeçalho e o valor em toda linha) no CSV das fontes do Drive cujo nome termina em `sufixo`."""
    k = hoje()
    rel = next(r for r in sorted(k['F']) if r.endswith(sufixo))
    linhas = list(csv.reader(io.StringIO(k['F'][rel])))
    saida = io.StringIO()
    csv.writer(saida, lineterminator='\n').writerows(l + [coluna if i == 0 else valor] for i, l in enumerate(linhas))
    k['F'][rel] = saida.getvalue()
    return k


# Revisão final do C3. A TERMOS inteira em relatório deixava passar telefone, e-mail, CPF, dinheiro e lugar de equipamento de
# salvatagem escritos como TEXTO (as travas §2.2 e §2.7 do PROMPT): só valia o mesmo dado como chave. A PESSOAIS, a DINHEIRO e a
# LOCAL_SEGURANCA dão 0 em todo o dado de hoje e reprovam já; as outras cinco regex continuam em relatório até o C12.
EXTRAS += [
    ('TERMOS', 'telefone no texto da equipe (PESSOAIS)', lambda r: com_nota_equipe('Marina: (47) 99812-3456.' if r else 'Marina: contato só no aparelho.'),
     'PESSOAIS: equipe.nota'),
    ('TERMOS', 'e-mail no diário (PESSOAIS)', lambda r: mais_texto(hoje(), ' Contato: oficina@exemplo.com.br.' if r else ''), 'PESSOAIS: diario[0].t'),
    ('TERMOS', 'CPF no diário (PESSOAIS)', lambda r: mais_texto(hoje(), ' CPF 123.456.789-09.' if r else ''), 'PESSOAIS: diario[0].t'),
    ('TERMOS', 'CNPJ numa página de fonte do Drive (PESSOAIS)', lambda r: com_fonte_final('Controle de documentos.csv', '\nX,Y,,,CNPJ 12.345.678/0001-95\n' if r else '\n'),
     'PESSOAIS: fontes/02 Documentos/Controle de documentos.csv'),
    ('TERMOS', 'dinheiro no diário (DINHEIRO)', lambda r: mais_texto(hoje(), ' Gasto R$ 3.450,00 no abastecimento.' if r else ''), 'DINHEIRO: diario[0].t'),
    ('TERMOS', 'preço num trecho da base (DINHEIRO)', lambda r: com_base(T_DSC, ' O preço do rádio é 1.200 reais.' if r else ''), 'DINHEIRO: base:trechos[%d].texto' % T_DSC),
    ('TERMOS', 'lugar do EPIRB no nome do equipamento (LOCAL_SEGURANCA)',
     lambda r: (lambda k: (poe(k['D']['equipamentos'], 7, nome='EPIRB — fica no paiol de proa' if r else 'EPIRB'), k)[1])(hoje()), 'LOCAL_SEGURANCA: equipamentos[7].nome'),
    ('TERMOS', 'lugar dos coletes no diário (LOCAL_SEGURANCA)', lambda r: mais_texto(hoje(), ' Coletes guardados no armário da cabine de proa.' if r else ''),
     'LOCAL_SEGURANCA: diario[0].t'),
    ('TERMOS', 'lugar da balsa numa página de fonte do Drive (LOCAL_SEGURANCA)', lambda r: com_fonte_final('Checklist de bordo.html', '<p>A balsa fica na popa.</p>' if r else ''),
     'LOCAL_SEGURANCA: fontes/01 Manuais e guias de bordo/Checklist de bordo.html'),
]


# C6 (CONTRATO §1.3): a asserção PROTOCOLOS acusa cada defeito do D.protocolos (forma, texto fixo, fonte única com os guias). Cada
# amostra muda uma coisa só; a versão boa (r falso) é o dado de hoje, sem violação nova.
def com_proto(muda=None, base=None):
    """hoje() com muda(D.protocolos) e base(B) aplicados."""
    k = hoje()
    if muda:
        muda(k['D']['protocolos'])
    if base:
        base(k['B'])
    return k


def sem_trecho(chave, sec):
    """base(B) que tira o trecho `sec` (começo do título) do guia `chave`."""
    def f(B):
        B['trechos'] = [t for t in B['trechos'] if not (t['fonte'] == G.ARQ[chave] and t['secao'].startswith(sec))]
    return f


def sem_guia(chave, so_arquivos=False):
    """hoje() sem o guia `chave` em drive.arquivos; sem `so_arquivos`, o guia inteiro some também de D.guias, dos trechos da base e das
    páginas de fonte do Drive (nenhum equipamento aponta para o guia `protocolo`: nada mais o prende)."""
    k = hoje()
    titulo = k['D']['drive']['arquivos'].pop(chave)
    if not so_arquivos:
        k['D']['guias'].pop(chave, None)
        k['B']['trechos'] = [t for t in k['B']['trechos'] if t['fonte'] != titulo]
        for rel in [r for r in k['F'] if r.endswith('/' + titulo + '.html')]:
            k['F'].pop(rel)
    return k


EXTRAS += [
    ('PROTOCOLOS', 'o D sem o protocolos', lambda r: (lambda k: (k['D'].pop('protocolos') if r else None, k)[1])(hoje()), 'protocolos ausente'),
    ('PROTOCOLOS', 'seafire null (o de antes do C6)', lambda r: com_proto(lambda P: P.update({'seafire': None}) if r else None),
     'protocolos.seafire: precisa de objeto'),
    ('PROTOCOLOS', 'epirb null (o de antes do C6)', lambda r: com_proto(lambda P: P.update({'epirb': None}) if r else None),
     'protocolos.epirb: precisa de objeto'),
    ('PROTOCOLOS', 'chave que o contrato não tem', lambda r: com_proto(lambda P: P.update({'telefone': 'x'}) if r else None),
     'protocolos.telefone: chave que o §1.3 não tem'),
    ('PROTOCOLOS', 'chave a mais no seafire', lambda r: com_proto(lambda P: P['seafire'].update({'modelo': 'x'}) if r else None),
     'protocolos.seafire.modelo: chave que o §1.3 não tem'),
    ('PROTOCOLOS', 'roteiro de 7 linhas', lambda r: com_proto(lambda P: P['roteiro'].pop() if r else None),
     'protocolos.roteiro: 7 texto(s), o §1.3 pede 8'),
    ('PROTOCOLOS', 'roteiro com outro nome de embarcação', lambda r: com_proto(lambda P: P['roteiro'].__setitem__(1, 'AQUI É OUTRO, OUTRO, OUTRO') if r else None),
     'protocolos.roteiro[1]: «AQUI É OUTRO, OUTRO, OUTRO»'),
    ('PROTOCOLOS', 'roteiro com a linha das pessoas em branco (a de antes do C6)',
     lambda r: com_proto(lambda P: P['roteiro'].__setitem__(5, 'PESSOAS A BORDO: ________') if r else None), 'protocolos.roteiro[5]: «PESSOAS A BORDO: ________»'),
    ('PROTOCOLOS', 'roteiro com o MMSI do cadastro (o de antes do C6)',
     lambda r: com_proto(lambda P: P['roteiro'].__setitem__(2, 'MMSI 710123456') if r else None), 'protocolos.roteiro[2]: «MMSI 710123456»'),
    ('PROTOCOLOS', 'seafire com 4 passos', lambda r: com_proto(lambda P: P['seafire']['passos'].pop() if r else None),
     'protocolos.seafire.passos: 4 texto(s), o §1.3 pede 5'),
    ('PROTOCOLOS', 'epirb sem o teste', lambda r: com_proto(lambda P: P['epirb'].pop('teste') if r else None),
     'protocolos.epirb.teste: precisa de uma lista de textos'),
    ('PROTOCOLOS', 'seafire sem a nota', lambda r: com_proto(lambda P: P['seafire'].pop('nota') if r else None),
     'protocolos.seafire.nota: precisa de texto'),
    ('PROTOCOLOS', 'passo vazio no MOB', lambda r: com_proto(lambda P: P['mob'].__setitem__(1, '') if r else None),
     'protocolos.mob: precisa de uma lista de textos'),
    ('PROTOCOLOS', 'canal 16 com o MHz em ponto', lambda r: com_proto(lambda P: P['canal16'].update({'mhz': '156.800' if r else '156,800'})),
     'protocolos.canal16: canal «16» em «156,800» MHz'),
    ('PROTOCOLOS', 'canal 16 sem a fonte', lambda r: com_proto(lambda P: P['canal16'].pop('fonte') if r else None),
     'protocolos.canal16: precisa de {canal, mhz, fonte}'),
    ('PROTOCOLOS', 'MMSI do rádio mudado', lambda r: com_proto(lambda P: P.update({'mmsiRadio': 'MMSI do rádio' if r else P['mmsiRadio']})),
     'protocolos.mmsiRadio: diferente do texto do contrato'),
    ('PROTOCOLOS', 'rótulo do MMSI de antes (F3)', lambda r: com_proto(lambda P: P.update({'mmsiRotulo': 'MMSI da embarcação (DSC)' if r else P['mmsiRotulo']})),
     'protocolos.mmsiRotulo: diferente do texto do contrato'),
    ('PROTOCOLOS', 'indicativo gerado', lambda r: com_proto(lambda P: P.update({'indicativo': 'PU2ABC' if r else P['indicativo']})),
     'protocolos.indicativo: diferente do texto do contrato'),
    ('PROTOCOLOS', 'HUD sem o campo', lambda r: com_proto(lambda P: P.pop('hud') if r else None), 'protocolos.hud: precisa de texto'),
    ('PROTOCOLOS', 'plotter sem as pessoas', lambda r: com_proto(lambda P: P.update({'plotter': 'POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER' if r else P['plotter']})),
     'protocolos.plotter: diferente do texto do contrato'),
    # fonte única: o texto do D e o do guia dizem a mesma coisa
    ('PROTOCOLOS', 'MOB do D diferente do protocolo da base', lambda r: com_proto(lambda P: P['mob'].__setitem__(0, P['mob'][0] + (' Agora.' if r else ''))),
     'Protocolo de emergência — procedimento padrão · Homem ao mar não repete protocolos.mob'),
    ('PROTOCOLOS', 'passos do Seafire do D diferentes do g_seafire §1',
     lambda r: com_proto(lambda P: P['seafire']['passos'].__setitem__(0, P['seafire']['passos'][0] + (' Agora.' if r else ''))),
     'Guia de bordo — Sistema fixo de incêndio · 1 · Em caso de fogo não repete protocolos.seafire.passos'),
    ('PROTOCOLOS', 'óleo do D diferente do g_motores §4', lambda r: com_proto(lambda P: P['oleo'].__setitem__(3, P['oleo'][3] + (' Já.' if r else ''))),
     'não repete protocolos.oleo'),
    ('PROTOCOLOS', 'DSC do g_eletronicos §5 sem o texto do D', lambda r: com_proto(None, lambda B: [t.update({'texto': 'O botão DISTRESS envia o alerta.'}) if r and t['fonte'] == G.ARQ['g_eletronicos']
                                                                                                    and t['secao'].startswith('5 · ') else None for t in B['trechos']]),
     'não repete protocolos.dsc'),
    ('PROTOCOLOS', 'trecho da seção MAYDAY fora da base', lambda r: com_proto(None, sem_trecho('protocolo', 'MAYDAY') if r else None),
     'seção «MAYDAY…» ausente'),
    ('PROTOCOLOS', 'g_epirb sem a seção 1', lambda r: com_proto(None, sem_trecho('g_epirb', '1 · ') if r else None), 'seção «1 · …» ausente'),
    ('PROTOCOLOS', 'MAYDAY falado da base diferente do roteiro', lambda r: com_proto(lambda P: P['roteiro'].__setitem__(7, 'CÂMBIO' + (' FINAL' if r else ''))),
     'não repete protocolos.roteiro'),
    # revisão do C6: o guia ausente de drive.arquivos reprova (a seção ausente de um guia que existe já reprovava; o guia inteiro sumia em silêncio)
    ('PROTOCOLOS', 'guia protocolo removido por inteiro (arquivos, D.guias, base e fontes): o MOB perde a fonte única',
     lambda r: sem_guia('protocolo') if r else hoje(), 'drive.arquivos.protocolo ausente (repete protocolos.mob, §1.3)'),
    ('PROTOCOLOS', 'guia protocolo removido por inteiro: o roteiro MAYDAY falado perde a fonte única',
     lambda r: sem_guia('protocolo') if r else hoje(), 'drive.arquivos.protocolo ausente (repete protocolos.roteiro, §1.3)'),
    ('PROTOCOLOS', 'guia protocolo só fora de drive.arquivos (base e D.guias intactos)',
     lambda r: sem_guia('protocolo', True) if r else hoje(), 'drive.arquivos.protocolo ausente (repete protocolos.salvatagem, §1.3)'),
    ('PROTOCOLOS', 'g_epirb só fora de drive.arquivos (base e D.guias intactos)',
     lambda r: sem_guia('g_epirb', True) if r else hoje(), 'drive.arquivos.g_epirb ausente (repete protocolos.epirb.teste, §1.3)'),
    ('PROTOCOLOS', 'g_seafire só fora de drive.arquivos (base e D.guias intactos)',
     lambda r: sem_guia('g_seafire', True) if r else hoje(), 'drive.arquivos.g_seafire ausente (repete protocolos.seafire.passos, §1.3)'),
    ('PROTOCOLOS', 'g_porao só fora de drive.arquivos (base e D.guias intactos)',
     lambda r: sem_guia('g_porao', True) if r else hoje(), 'drive.arquivos.g_porao ausente (repete protocolos.alagamento, §1.3)'),
    ('PROTOCOLOS', 'g_motores só fora de drive.arquivos (base e D.guias intactos)',
     lambda r: sem_guia('g_motores', True) if r else hoje(), 'drive.arquivos.g_motores ausente (repete protocolos.oleo, §1.3)'),
    ('PROTOCOLOS', 'g_eletronicos só fora de drive.arquivos (base e D.guias intactos)',
     lambda r: sem_guia('g_eletronicos', True) if r else hoje(), 'drive.arquivos.g_eletronicos ausente (repete protocolos.dsc, §1.3)'),
]


# Revisão do C6 (§1.3, «todas viram asserção»): a regra «Grafia Seafire em todo dado» não tinha asserção. «Sea Fire» no lugar de «Seafire» em todos
# os trechos da base e «Sea-Fire» no nome do sistema ou numa nota passavam em todas as asserções (a `sea[- ...]?fire` da LOCAL_SEGURANCA só prende o
# lugar do equipamento na frase). A GRAFIA_SEAFIRE varre todo valor string do D, da base, do FAQ e das fontes, toda chave (o cabeçalho dos CSV
# também) e todo nome de arquivo das fontes. A única exceção são as `palavras` de busca dos equipamentos («sea fire» é o que o ditado escreve).
I_SEAFIRE = next(i for i, e in enumerate(G.dados()['equipamentos']) if e['id'] == 'seafire')
T_SECAO_SEAFIRE = next(i for i, t in enumerate(G.base_conhecimento()['trechos']) if t['secao'].endswith('Seafire'))   # «Incêndio · Seafire» (§1.5)
GRAFIAS_RUINS = ('Sea Fire', 'Sea-Fire', 'sea fire', 'SEAFIRE', 'SeaFire', 'Sea  Fire', 'Sea\u00a0Fire', 'Sea\u2011Fire', 'Sea\u2014Fire', 'Sea_Fire',
                 'Sea\u200bFire', 'Sea\u00adFire')   # espaço duplo, NBSP, hífen que não quebra, travessão, sublinhado, espaço de largura zero e hífen suave


def seafire_nos_trechos(grafia):
    """hoje() com «Seafire» trocado por `grafia` em todo campo texto de todos os trechos da base (o caso do revisor do C6)."""
    k = hoje()
    for t in k['B']['trechos']:
        for c, v in t.items():
            if isinstance(v, str):
                t[c] = v.replace('Seafire', grafia)
    return k


def com_fonte_nova(rel, txt):
    """hoje() com um arquivo a mais nas fontes do Drive (`rel` é o nome dentro de ferramentas/demo/fontes)."""
    k = hoje()
    k['F'][rel] = txt
    return k


EXTRAS += [('GRAFIA_SEAFIRE', 'texto do diário com %r' % v, (lambda v: lambda r: mais_texto(hoje(), (' O %s fica pronto.' % v) if r else ' O Seafire fica pronto.'))(v),
            'diario[0].t: texto com a grafia «%s» do Seafire' % v) for v in GRAFIAS_RUINS] + [
    ('GRAFIA_SEAFIRE', 'o título da seção do protocolo e todos os trechos da base com «Sea Fire» (o caso do revisor)',
     lambda r: seafire_nos_trechos('Sea Fire' if r else 'Seafire'), 'base:trechos[%d].secao: texto com a grafia «Sea Fire»' % T_SECAO_SEAFIRE),
    ('GRAFIA_SEAFIRE', 'o fabricante do equipamento seafire com «Sea Fire»',
     lambda r: (lambda k: (poe(k['D']['equipamentos'], I_SEAFIRE, fabricante='Sea Fire' if r else 'Seafire'), k)[1])(hoje()),
     'equipamentos[%d].fabricante: texto com a grafia «Sea Fire»' % I_SEAFIRE),
    ('GRAFIA_SEAFIRE', 'o nome do sistema com «Sea-Fire»',
     lambda r: (lambda k: (poe(k['D']['equipamentos'], I_SEAFIRE, nome='Sistema Sea-Fire' if r else 'Sistema fixo de supressão de incêndio'), k)[1])(hoje()),
     'equipamentos[%d].nome: texto com a grafia «Sea-Fire»' % I_SEAFIRE),
    ('GRAFIA_SEAFIRE', '«Sea-Fire» numa nota solta (equipNota)',
     lambda r: (lambda k: (k['D'].update({'equipNota': k['D']['equipNota'] + (' O Sea-Fire está em dia.' if r else ' O Seafire está em dia.')}), k)[1])(hoje()),
     'equipNota: texto com a grafia «Sea-Fire»'),
    ('GRAFIA_SEAFIRE', 'palavras da agenda com «sea fire» (a exceção é só das palavras de busca dos equipamentos)',
     # C7: a agenda já traz as `palavras` (antes o setdefault criava a lista): a amostra troca a 1ª
     lambda r: (lambda k: (k['D']['agenda'][0]['palavras'].__setitem__(0, 'inspecao do sea fire' if r else 'inspecao do seafire'), k)[1])(hoje()),
     'agenda[0].palavras[0]: texto com a grafia «sea fire»'),
    ('GRAFIA_SEAFIRE', 'chave «Sea-Fire» no D', lambda r: (lambda k: (k['D']['embarcacao'].update({'Sea-Fire' if r else 'seafire': 'x'}), k)[1])(hoje()),
     'embarcacao.Sea-Fire: chave com a grafia «Sea-Fire»'),
    ('GRAFIA_SEAFIRE', 'chave «seaFire» na base', lambda r: (lambda k: (k['B']['trechos'][0].update({'seaFire' if r else 'seafire': True}), k)[1])(hoje()),
     'base:trechos[0].seaFire: chave com a grafia «seaFire»'),
    ('GRAFIA_SEAFIRE', 'cabeçalho «Sea Fire» num CSV das fontes', lambda r: com_coluna('Inventário de bordo.csv', 'Sea Fire' if r else 'Seafire'),
     'Inventário de bordo.csv:Sea Fire: chave com a grafia «Sea Fire»'),
    ('GRAFIA_SEAFIRE', 'célula «Sea Fire» num CSV das fontes', lambda r: com_fonte_final('Inventário de bordo.csv', '\nX,Sea Fire\n' if r else '\n'),
     'Inventário de bordo.csv: texto com a grafia «Sea Fire»'),
    ('GRAFIA_SEAFIRE', '«Sea-Fire» num JSON das fontes', lambda r: com_json(lambda j: j.update({'extra': 'Sea-Fire' if r else 'Seafire'})),
     ':extra: texto com a grafia «Sea-Fire»'),
    ('GRAFIA_SEAFIRE', 'item do FAQ com «Sea Fire»',
     lambda r: (lambda k: (k.update({'faq': {'itens': [{'id': 'SF-01', 'titulo': 'Disparo do %s' % ('Sea Fire' if r else 'Seafire'), 'resposta': 'Veja o guia.'}]}}), k)[1])(hoje()),
     'faq:itens[0].titulo: texto com a grafia «Sea Fire»'),
    ('GRAFIA_SEAFIRE', 'página de fonte com «Sea&nbsp;Fire» (a entidade vira NBSP na tela)',
     lambda r: com_eletronicos('<h2>9 · Teste</h2><p>O %s dispara.</p>' % ('Sea&nbsp;Fire' if r else 'Seafire')), 'html: texto com a grafia «Sea\u00a0Fire» do Seafire'),
    ('GRAFIA_SEAFIRE', 'página de fonte com «Sea <b>fire</b>» (a tag no meio some na tela)',
     lambda r: com_eletronicos('<h2>9 · Teste</h2><p>O %s dispara.</p>' % ('Sea <b>fire</b>' if r else 'Seafire')), 'html: texto com a grafia «Sea fire» do Seafire'),
    ('GRAFIA_SEAFIRE', 'nome de arquivo das fontes com «Sea Fire»',
     lambda r: com_fonte_nova('01 Manuais e guias de bordo/Guia de bordo — %s.html' % ('Sea Fire' if r else 'Seafire'), '<h1>Guia</h1>'),
     'Guia de bordo — Sea Fire.html: nome de arquivo com a grafia «Sea Fire»'),
]

def com_tarefa_seguranca(sistema, equip):
    """hoje() com a tarefa de salvatagem do `sistema` (epirb-teste ou seafire-inspecao), em dia, com `equip` no campo equip."""
    k = hoje()
    meses, ultima, vence = (1, 18, 13) if sistema == 'epirb' else (12, 360, 5)
    k['D']['agenda'].append({'id': 'epirb-teste' if sistema == 'epirb' else 'seafire-inspecao', 't': 'Teste do dispositivo', 'sistema': sistema, 'meses': meses,
                             'ultimaHa': ultima, 'venceEm': vence, 'palavras': ['teste do dispositivo'], 'seguranca': True, 'equip': equip})
    return k


def mob_sem_marca(frase):
    """hoje() com a frase no fim do protocolos.mob e os 16 equipamentos do §1.4 SEM a marca `seguranca`: a guarda do EPIRB e do Seafire
    vale pelo id, não pela marca que o próprio dado carrega."""
    k = com_equip_c5(hoje())
    k['D']['protocolos']['mob'].append(frase)
    return k


# Revisão final do C3. PROTOCOLO_LIMPO e AGENDA só proibiam o fabricante, o modelo inteiro e as duas primeiras palavras dele: um
# pedaço do modelo do EPIRB e do Seafire ("SafeSea", "E100G", "FD-300M", "FD300M") passava no protocolos (que o S1/S2 lê) e no equip
# da agenda (trava 17). Para esses dois equipamentos, cada palavra do fabricante e do modelo (3 caracteres ou mais, que não seja
# só número) e as formas juntas, sem espaço e com hífen. Os outros equipamentos ficam na regra de §2.5: o "V2" solto casaria o "v2"
# de "Capitão IA v2" do protocolos.fonte.
EXTRAS += [
    ('PROTOCOLO_LIMPO', 'pedaço do modelo do EPIRB: "SafeSea"', lambda r: protocolo('mob', None, 'Acione o SafeSea conforme a etiqueta.' if r else 'Acione o EPIRB conforme a etiqueta.'),
     'protocolos.mob[3]: fabricante ou modelo de equipamento [SafeSea]'),
    ('PROTOCOLO_LIMPO', 'pedaço do modelo do EPIRB: "E100G"', lambda r: protocolo('mob', None, 'Leve o E100G para a balsa.' if r else 'Leve o EPIRB para a balsa.'),
     'protocolos.mob[3]: fabricante ou modelo de equipamento [E100G]'),
    ('PROTOCOLO_LIMPO', 'modelo do Seafire com hífen no lugar do espaço: "FD-300M"', lambda r: protocolo('mob', None, 'Dispare o FD-300M no manual.' if r else 'Dispare o sistema fixo no manual.'),
     'protocolos.mob[3]: fabricante ou modelo de equipamento [FD-300M]'),
    ('PROTOCOLO_LIMPO', 'modelo do Seafire sem o espaço: "FD300M"', lambda r: protocolo('mob', None, 'Dispare o FD300M no manual.' if r else 'Dispare o sistema fixo no manual.'),
     'protocolos.mob[3]: fabricante ou modelo de equipamento [FD300M]'),
    ('PROTOCOLO_LIMPO', 'fabricante do EPIRB sem o espaço: "OceanSignal"', lambda r: protocolo('mob', None, 'Ligue para a OceanSignal.' if r else 'Ligue para o fabricante.'),
     'protocolos.mob[3]: fabricante ou modelo de equipamento [OceanSignal]'),
    ('PROTOCOLO_LIMPO', 'palavra do fabricante do EPIRB: "Signal"', lambda r: protocolo('mob', None, 'O Signal está ligado.' if r else 'O sinal está ligado.'),
     'protocolos.mob[3]: fabricante ou modelo de equipamento [Signal]'),
    ('PROTOCOLO_LIMPO', 'pedaço do modelo do EPIRB sem a marca `seguranca` no dado (vale pelo id)', lambda r: mob_sem_marca('Acione o SafeSea.' if r else 'Acione o EPIRB.'),
     'protocolos.mob[3]: fabricante ou modelo de equipamento [SafeSea]'),
    ('AGENDA', 'equip do EPIRB com pedaço do modelo: "SafeSea"', lambda r: com_tarefa_seguranca('epirb', 'EPIRB SafeSea' if r else 'EPIRB'),
     'agenda.epirb-teste.equip com fabricante ou modelo de equipamento de segurança'),
    ('AGENDA', 'equip do EPIRB com pedaço do modelo: "E100G"', lambda r: com_tarefa_seguranca('epirb', 'EPIRB E100G' if r else 'EPIRB'),
     'agenda.epirb-teste.equip com fabricante ou modelo de equipamento de segurança'),
    ('AGENDA', 'equip do EPIRB com o fabricante, uma violação só ("Ocean Signal")', lambda r: com_tarefa_seguranca('epirb', 'EPIRB Ocean Signal' if r else 'EPIRB'),
     'agenda.epirb-teste.equip com fabricante ou modelo de equipamento de segurança'),
    ('AGENDA', 'equip do Seafire com o modelo sem o espaço: "FD300M"', lambda r: com_tarefa_seguranca('seafire', 'Sistema fixo FD300M' if r else 'Sistema fixo'),
     'agenda.seafire-inspecao.equip com fabricante ou modelo de equipamento de segurança'),
    ('AGENDA', 'equip do Seafire com o modelo com hífen: "FD-300M"', lambda r: com_tarefa_seguranca('seafire', 'Sistema fixo FD-300M' if r else 'Sistema fixo'),
     'agenda.seafire-inspecao.equip com fabricante ou modelo de equipamento de segurança'),
]


# Revisão do C7 (CONTRATO §1.7–§1.9, §6.2 C7, §6.3). O C7 tirou da PENDENTES as linhas AGENDA, IDS e FONTES_RELATIVAS: o dado real congelado
# ali era a prova de que as regras reprovam, e nenhuma amostra plantada ficou no lugar. Sem elas, uma regressão em confere.py (palavra solta,
# conta das 3 atrasadas, sistema fora do vocabulário, ref do diário ou do documento, pendência sem ref ou com palavras diferentes, diasAtras 0
# depois da âncora, documento sem prazo com null ou '') não seria vista por teste algum. Cada amostra é ISOLADA: planta(..., so_uma=True) exige
# que ela seja a única violação nova da regra (nenhuma se apoia em outra mensagem). A r=False é o dado de hoje, que não acusa nada.
def planta_c7(lista, i, **kw):
    """monta(r): hoje() com D[lista][i] mudado por `kw` quando r (SEM tira a chave)."""
    return lambda r: muda(hoje(), lista, i, **kw) if r else hoje()


def com_dia_de_bordo_8h20(r):
    """O D com um replay mínimo e a d01 do dia de bordo (a do replay, que a microtarefa insere) às 08:20, com diasAtras 0."""
    k = com_replay(hoje())
    if r:
        k['D']['replay']['diaDeBordo']['diario'][0]['h'] = '08:20'
    return k


def com_csv_na_pasta(pasta, nome, txt):
    k = hoje()
    k['F'][k['D']['drive']['pastas'][pasta] + '/' + nome] = txt
    return k


def com_nf(**kw):
    """hoje() com a nota fiscal do dia de bordo (replay.diaDeBordo.documento, onde ela mora desde o C8) mudada por `kw`."""
    return lambda r: (lambda k: (k['D']['replay']['diaDeBordo']['documento'].update(kw) if r else None, k)[1])(hoje())


def com_d01_8h20(r):
    """hoje() com uma linha do diário fixo (a d03) em diasAtras 0 às 08:20: depois da âncora das 07:00."""
    return muda(hoje(), 'diario', 'd03', diasAtras=0, h='08:20') if r else hoje()
C7_REV = [
    ('AGENDA', 'palavra solta (uma palavra só nas `palavras`)', planta_c7('agenda', 'casco-anodos', palavras=['rotor']), 'agenda.casco-anodos.palavras vazias ou com palavra solta'),
    ('AGENDA', 'palavras vazias', planta_c7('agenda', 'casco-anodos', palavras=[]), 'agenda.casco-anodos.palavras vazias ou com palavra solta'),
    ('AGENDA', 'ultimaHa + venceEm fora da tabela (6 meses = 184)', planta_c7('agenda', 'casco-anodos', ultimaHa=170), 'agenda.casco-anodos: ultimaHa + venceEm ≠ DIAS_MESES[meses]'),
    ('AGENDA', 'só 2 atrasadas (a do porão em dia)', planta_c7('agenda', 'porao-teste', ultimaHa=26, venceEm=5), 'agenda: 2 atrasadas (precisa de 3)'),
    ('AGENDA', '4 atrasadas (a limpeza do casco vencida)', planta_c7('agenda', 'casco-anodos', ultimaHa=186, venceEm=-2), 'agenda: 4 atrasadas (precisa de 3)'),
    ('AGENDA', 'seguranca numa tarefa que não é de salvatagem', planta_c7('agenda', 'casco-anodos', seguranca=True), 'agenda.casco-anodos: seguranca só (e sempre) em'),
    ('AGENDA', 'a tarefa do porão sem seguranca', planta_c7('agenda', 'porao-teste', seguranca=SEM), 'agenda.porao-teste: seguranca só (e sempre) em'),
    ('AGENDA', 'palavra da lista SOS no `t`', planta_c7('agenda', 'casco-anodos', t='Incêndio no casco'), 'agenda.casco-anodos.t tem palavra da lista SOS'),
    ('AGENDA', 'salvatagem atrasada (o seafire-inspecao vencido, as 3 atrasadas mantidas)', AMOSTRAS['AGENDA'][0], 'agenda.seafire-inspecao: tarefa de salvatagem atrasada'),
    ('IDS', 'sistema da agenda fora do vocabulário', planta_c7('agenda', 'casco-anodos', sistema='xyz'), 'agenda.casco-anodos.sistema fora do vocabulário'),
    ('IDS', 'sistema da tarefa da equipe fora do vocabulário', planta_c7('tarefasEquipe', 'g01', sistema='xyz'), 'tarefasEquipe.g01.sistema fora do vocabulário'),
    ('IDS', 'ref do diário que não existe', planta_c7('diario', 'd04', ref='nao-existe'), "diario.d04.ref inexistente: 'nao-existe'"),
    ('IDS', 'ref do documento que não existe', planta_c7('documentos', 'seguro', ref='nao-existe'), "documentos.seguro.ref inexistente: 'nao-existe'"),
    ('IDS', 'pendência do diário sem ref na agenda', planta_c7('diario', 'd03', ref=SEM), 'diario.d03: pendência sem ref na agenda'),
    ('IDS', 'pendência com palavras diferentes das da tarefa', planta_c7('diario', 'd03', palavras=['x y']), 'diario.d03.palavras diferentes das da tarefa gerador-rotor'),
    ('IDS', 'pendência sem palavras', planta_c7('diario', 'd05', palavras=SEM), 'diario.d05.palavras diferentes das da tarefa clima-filtro'),
    ('DIA_DE_BORDO', 'uma linha do diário fixo (d03) às 08:20 com diasAtras 0 (depois da âncora das 07:00)', com_d01_8h20,
     'diário d03: diasAtras 0 depois da âncora (08:20)'),
    ('DIA_DE_BORDO', 'a d01 do dia de bordo (replay.diaDeBordo.diario) às 08:20 com diasAtras 0', com_dia_de_bordo_8h20, 'diário d01: diasAtras 0 depois da âncora (08:20)'),
    ('NULO', 'dn None num documento', planta_c7('documentos', 'seguro', dn=None), '].dn: None'),
    ('NULO', "vence '' num documento", planta_c7('documentos', 'licenca', vence=''), "].vence: ''"),
    ('NULO', 'a nota fiscal do dia de bordo (documento sem prazo) com dn None', com_nf(dn=None), 'replay.diaDeBordo.documento.dn: None'),
    ('NULO', "a nota fiscal do dia de bordo (documento sem prazo) com vence ''", com_nf(vence=''), "replay.diaDeBordo.documento.vence: ''"),
    ('NULO', "iso '' numa linha do diário fixo", planta_c7('diario', 'd03', iso=''), "].iso: ''"),
]
for _pasta in ('docs', 'agenda', 'diario', 'abast'):   # as quatro pastas da regra, uma a uma (a regra lê só estas)
    C7_REV.append(('FONTES_RELATIVAS', 'data dd/mm/aaaa num CSV da pasta «%s»' % _pasta,
                   (lambda p: lambda r: com_csv_na_pasta(p, 'Extra.csv', 'Data,Valor\n' + ('12/09/2026' if r else 'há 3 dias') + ',1\n'))(_pasta),
                   'Extra.csv: 1 data(s) dd/mm/aaaa'))
C7_REV.append(('FONTES_RELATIVAS', 'data no cabeçalho de um CSV (a 1ª linha)',
               lambda r: com_csv_na_pasta('diario', 'Extra.csv', ('Data 26/09/2026' if r else 'Data') + ',Valor\n1,2\n'), 'Extra.csv: 1 data(s) dd/mm/aaaa'))


# Revisão final do C3. A SEM_INDICATIVO e a SEM_PREVISAO só olhavam as chaves do JSON: o cabeçalho de uma coluna de CSV das fontes
# do Drive (Local, Telefone, HEX ID, Indicativo, Maré prevista) passava, e a planilha vai para o Drive. Agora a 1ª linha de cada
# CSV é chave ('fontes/<rel>:<coluna>'); a única coluna liberada é a Local do registro de abastecimento (o posto).
_INV, _ABA = 'Inventário de bordo.csv', 'Registro de abastecimento.csv'
EXTRAS += [
    ('SEM_INDICATIVO', 'coluna Local (lugar do EPIRB) no inventário', lambda r: com_coluna(_INV, 'Local' if r else 'Observação extra', 'hard-top' if r else ''),
     'fontes/01 Manuais e guias de bordo/Inventário de bordo.csv:Local: chave de lugar'),
    ('SEM_INDICATIVO', 'coluna Telefone no inventário', lambda r: com_coluna(_INV, 'Telefone' if r else 'Observação extra', 'ver no aparelho' if r else ''),
     'Inventário de bordo.csv:Telefone: chave de telefone'),
    ('SEM_INDICATIVO', 'coluna HEX ID no inventário', lambda r: com_coluna(_INV, 'HEX ID' if r else 'Observação extra', 'cadastrar' if r else ''),
     'Inventário de bordo.csv:HEX ID: chave de HEX ID'),
    ('SEM_INDICATIVO', 'coluna Indicativo no inventário', lambda r: com_coluna(_INV, 'Indicativo' if r else 'Observação extra', 'ver licença' if r else ''),
     'Inventário de bordo.csv:Indicativo: chave indicativo fora de protocolos'),
    ('SEM_INDICATIVO', 'coluna E-mail (com acento e parênteses) numa planilha de documentos', lambda r: com_coluna('Controle de documentos.csv', 'E-mail (marina)' if r else 'Observação extra', 'x' if r else ''),
     'Controle de documentos.csv:E-mail (marina): chave de e-mail'),
    ('SEM_PREVISAO', 'coluna Maré prevista (m) no inventário', lambda r: com_coluna(_INV, 'Maré prevista (m)' if r else 'Observação extra', '1,2' if r else ''),
     'fontes/01 Manuais e guias de bordo/Inventário de bordo.csv:Maré prevista (m): campo de previsão ou maré'),
    ('SEM_PREVISAO', 'coluna Previsão do tempo no abastecimento', lambda r: com_coluna(_ABA, 'Previsão do tempo' if r else 'Observação extra', 'bom' if r else ''),
     'Registro de abastecimento.csv:Previsão do tempo: campo de previsão ou maré'),
]


def com_linha_em_branco(sufixo, coluna):
    """hoje() com a coluna nova no CSV `sufixo` e uma linha em branco ANTES do cabeçalho."""
    k = com_coluna(sufixo, coluna, 'x')
    rel = next(r for r in sorted(k['F']) if r.endswith(sufixo))
    k['F'][rel] = '\n' + k['F'][rel]
    return k


# Revisão final do C3, 2ª rodada. A grafia da marca, "WhatsApp", o camelCase separa em whats + app: a chave não casava com a
# 'whatsapp' da CHAVES_IDENT (só "Whatsapp" e "whatsapp" reprovavam), e a coluna do CSV herdava a brecha. A palavras_juntas()
# compara também as palavras vizinhas juntas e a chave inteira (também 'Baixa-mar' → baixamar). E a linha em branco antes do
# cabeçalho de um CSV não esconde mais as colunas dele.
EXTRAS += [
    ('SEM_INDICATIVO', 'coluna WhatsApp (grafia da marca) no inventário', lambda r: com_coluna(_INV, 'WhatsApp' if r else 'Observação extra', 'ver no aparelho' if r else ''),
     'Inventário de bordo.csv:WhatsApp: chave de telefone'),
    ('SEM_INDICATIVO', 'coluna "Whats App" (duas palavras) no inventário', lambda r: com_coluna(_INV, 'Whats App' if r else 'Observação extra', 'ver no aparelho' if r else ''),
     'Inventário de bordo.csv:Whats App: chave de telefone'),
    ('SEM_INDICATIVO', 'chave whatsApp (camelCase) nos prestadores',
     lambda r: (lambda k: (poe(k['D']['equipe']['apoio'], 0, **({'whatsApp': 'cadastrar'} if r else {})), k)[1])(hoje()), 'equipe.apoio[0].whatsApp: chave de telefone'),
    ('SEM_INDICATIVO', 'chave WhatsApp numa lista de JSON das fontes', lambda r: com_json(lambda j: j.update({'WhatsApp_marina' if r else 'marina': 'x'})),
     ':WhatsApp_marina: chave de telefone'),
    ('SEM_PREVISAO', 'coluna "Baixa-mar (m)" (duas palavras que a lista traz juntas) no inventário',
     lambda r: com_coluna(_INV, 'Baixa-mar (m)' if r else 'Observação extra', '0,2' if r else ''), 'Inventário de bordo.csv:Baixa-mar (m): campo de previsão ou maré'),
    ('SEM_INDICATIVO', 'coluna Telefone depois de uma linha em branco no CSV', lambda r: com_linha_em_branco(_INV, 'Telefone' if r else 'Observação extra'),
     'Inventário de bordo.csv:Telefone: chave de telefone'),
]


def com_simulado(r):
    """Revisão do C3 (achado do LACO): o `simulado` que o atual() acrescenta é marca, não leitura (§1.15, «simulado fora»). Antes,
    se o C8 o pusesse no catálogo e em replay.fixos, as asserções passavam. O bom não planta nada."""
    k = com_replay(hoje())
    if r:
        k['D']['campos']['simulado'] = {'rotulo': 'Simulado', 'un': 'liga/desliga', 'casas': 0, 'origem': 'fixo'}
        k['D']['replay']['fixos']['simulado'] = True
    return k


# Revisão do C3 (LACO): o `simulado` fora do catálogo. Em campos (com o valor em replay.fixos, a forma que antes passava) e, sem
# o catálogo, só em replay.fixos (a checagem de grupos já o acusava: o dado fora de D.campos).
EXTRAS += [
    ('LACO', 'simulado no catálogo D.campos (com o valor em replay.fixos)', com_simulado, 'campos.simulado: marca do atual(), não leitura'),
    ('LACO', 'simulado só em replay.fixos, fora do catálogo',
     lambda r: (lambda k: (k['D']['replay']['fixos'].update({'simulado': True}) if r else None, k)[1])(com_replay(hoje())),
     'replay.fixos.simulado fora de D.campos com origem fixo'),
]


def com_porao(chaves=None, limites=True, janela=None, fixos=None, quadro=None, aninhado=None, ruido=None, const=None):
    """com_replay() com o porão BB no catálogo, nas chaves (30 valores) e, com `limites`, o BB e o BE no D.replay.limites (o teto do
    normal é o normal.ate, e o texto do guia de teste tem os números). `const`: a constante LIMITES que o confere recebe (padrão: a do replay)."""
    k = com_replay(hoje())
    D = k['D']
    D['campos']['porao_bb_nivel'] = {'rotulo': 'Porão BB', 'un': 'cm', 'casas': 1, 'origem': 'laço'}
    D['replay']['chaves']['porao_bb_nivel'] = chaves or [1.2] * 30
    if ruido:
        D['replay']['ruido']['porao_bb_nivel'] = ruido
    if limites:
        for lado in ('bb', 'be'):
            D['replay']['limites']['porao_%s_nivel' % lado] = {'un': 'cm', 'fonte': 'Guia de bordo — Teste §9 · Faixas de operação', 'normal': {'ate': 5},
                                                              'aviso': {'acima': 5}, 'critico': {'acima': 10}}
        k['B']['trechos'][-2]['texto'] += ' Porão: normal até 5 cm; aviso acima de 5 cm; crítico acima de 10 cm.'
    if janela:
        D['replay']['janelas'].append(janela)
    if fixos:
        D['replay']['fixos'].update(fixos)
    if quadro is not None:
        D['snapshot']['quadro'] = quadro
    if aninhado is not None:
        D['snapshot']['porao'] = aninhado
    if const is not None:
        k['const'] = dict(k['const'], LIMITES=const)
    return k


# Rampa de 4,0 a 7,0 cm e de volta (chaves 19…23, t = 95…115): o porão passa de 5 cm de t = 97 a t = 113, dentro de uma janela de aviso.
PORAO_ALTO = [1.2] * 19 + [4.0, 7.0, 7.0, 7.0, 4.0] + [1.2] * 6
JANELA_PORAO = {'id': 'porao_bb', 'campo': 'porao_bb_nivel', 'nivel': 'aviso', 'ini': 97, 'fim': 113}

# Revisão do C3 (JANELA, §6.4 «porão ≤ 5 cm»): o porão acima do normal passava em todas as asserções, até dentro de uma janela de
# aviso com os limites e o guia coerentes (a JANELA aceita o aviso dentro da janela). O teto é o normal.ate (D.replay.limites e a
# constante LIMITES do gerador), sem número solto.
EXTRAS += [
    ('JANELA', 'porão com 12 cm nas chaves, sem entrada em replay.limites (o teto vem da constante LIMITES do gerador)',
     lambda r: com_porao([12.0 if r else 1.2] * 30, limites=False, const=G.LIMITES), 'replay.chaves.porao_bb_nivel[0] = 12.0: acima do normal (até 5 cm)'),
    ('JANELA', 'porão de 7 cm numa janela de aviso, com limites e guia coerentes (as chaves)',
     lambda r: com_porao(PORAO_ALTO if r else None, janela=JANELA_PORAO if r else None), 'replay.chaves.porao_bb_nivel[20] = 7.0: acima do normal'),
    ('JANELA', 'porão de 7 cm numa janela de aviso (o segundo do laço, t = 97)',
     lambda r: com_porao(PORAO_ALTO if r else None, janela=JANELA_PORAO if r else None), 'replay (laço), porao_bb_nivel em t = 97 = 5.2: acima do normal'),
    ('JANELA', 'janela de porão (campo porao_bb_nivel) mesmo com os valores no normal',
     lambda r: com_porao(janela=JANELA_PORAO if r else None), 'replay.janelas.porao_bb: janela de porão'),
    ('JANELA', 'campo de porão sem teto: nem em replay.limites nem na constante LIMITES',
     lambda r: com_porao(limites=not r), 'porao_bb_nivel: sem normal.ate'),
    ('JANELA', 'o ruído passa o porão de 5 cm com as chaves em 4,9 (só o laço acusa)',
     lambda r: com_porao([4.9 if r else 4.0] * 30, ruido=[0.3, 1112]), 'replay (laço), porao_bb_nivel em t = '),
    ('JANELA', 'porão acima do normal em replay.fixos (o lado BE)',
     lambda r: com_porao(fixos={'porao_be_nivel': 7.0 if r else 1.0}), 'replay.fixos.porao_be_nivel = 7.0: acima do normal'),
    ('JANELA', 'porão acima do normal em snapshot.quadro',
     lambda r: com_porao(quadro={'porao_bb_nivel': 6.1 if r else 1.1}), 'snapshot.quadro.porao_bb_nivel = 6.1: acima do normal'),
    ('JANELA', 'porão acima do normal no snapshot.porao aninhado (be_cm)',
     lambda r: com_porao(aninhado={'bb_cm': 1.2, 'be_cm': 7.5 if r else 0.9, 'ciclos_h': 0}), 'snapshot.porao.be_cm = 7.5: acima do normal'),
]


# Revisão 6 do C5: o IDENT_BASE barrava só 21 palavras ("caiu plotter", "caiu ligue", "caiu bateria", "caiu garmin" passavam). O conjunto
# proibido sai do dado (equipamentos, fontes, equips e títulos da base) mais os verbos com flexão, e "pessoa"/"alguém" vão em identCom.
IDENT_RUINS = ['plotter', 'ligue', 'desligue', 'abra', 'bateria', 'garmin', 'cummins', 'âncora', 'piloto', 'epirb', 'vhf', 'seakeeper', 'climatização',
               'bombas', 'guincho', 'manutenção', 'partida', 'radar', 'raymarine', 'fusion', 'schenker', 'webasto', 'lewmar', 'victron', 'religue', 'esfrie']
EXTRAS += [('IDENT_BASE', 'ident com «caiu %s»' % w, (lambda w: lambda r: com_ident('caiu ' + w if r else 'caiu cair'))(w),
            'ident com verbo de operação ou nome de equipamento (%s)' % w) for w in IDENT_RUINS]
EXTRAS += [
    ('IDENT_BASE', 'ident com «pessoa» (a palavra de pessoa vai em identCom)', lambda r: com_ident('caiu pessoa' if r else 'caiu cair'),
     'ident com palavra de pessoa (pessoa)'),
    ('IDENT_BASE', 'ident com «alguém»', lambda r: com_ident('caiu alguém' if r else 'caiu cair'), 'ident com palavra de pessoa (alguém)'),
    ('IDENT_BASE', 'ident de queda («caiu») sem identCom: «o disjuntor caiu» nomearia o trecho', lambda r: com_ident('caiu cair', com=None if r else 'pessoa'),
     'ident com palavra de queda ou de vista (cair, caiu) sem identCom'),
    ('IDENT_BASE', 'ident com «vista» sem identCom: «tem vista para o mar»', lambda r: com_ident('pane vista', com=None if r else 'pessoa'),
     'ident com palavra de queda ou de vista (vista) sem identCom'),
    ('IDENT_BASE', 'identCom sem ident', lambda r: com_ident('pane governo', com='pessoa') if not r else (lambda k: (k['B']['trechos'].append(
        {'fonte': 'Guia de bordo — Teste', 'secao': '2 · Teste', 'equip': 'Teste', 'seguranca': True, 'texto': 'Passo curto.', 'identCom': 'pessoa'}), k)[1])(hoje()),
     'identCom sem ident'),
    ('IDENT_BASE', 'identCom com palavra fora da lista de pessoa', lambda r: com_ident('caiu cair', com='pessoa plotter' if r else 'pessoa quem'),
     'identCom precisa de 1 a 8 palavras de pessoa da lista fechada'),
    ('IDENT_BASE', 'identCom vazio', lambda r: com_ident('caiu cair', com='' if r else 'pessoa'), 'identCom precisa de 1 a 8 palavras de pessoa da lista fechada'),
]

def com_lugar(onde, txt):
    """hoje() com `txt` (equipamento de salvatagem e lugar na mesma frase) no diário, num trecho da base, num item do FAQ ou numa
    página de fonte do Drive."""
    k = hoje()
    if onde == 'diario':
        return mais_texto(k, txt)
    if onde == 'base':
        k['B']['trechos'].append({'fonte': 'Guia de bordo — Teste', 'secao': '1 · Teste', 'equip': 'Teste', 'texto': txt})
    elif onde == 'faq':
        k['faq'] = {'itens': [{'id': 'XX-01', 'titulo': 'Teste', 'resposta': txt}]}
    else:
        rel = next(r for r in sorted(k['F']) if r.endswith('Checklist de bordo.html'))
        k['F'][rel] += '<p>' + txt + '</p>'
    return k


# Revisão do C3 (LOCAL_VOCAB): a LOCAL_SEGURANCA da TERMOS pede o equipamento antes do lugar; a ordem inversa («No paiol de proa
# ficam os coletes») passava em todas as asserções fora de protocolos. Em qualquer ordem, em todo texto (D, base, FAQ e fontes).
BOM_LUGAR = ' Os coletes foram conferidos na saída.'
for _onde in ('diario', 'base', 'faq', 'fonte'):
    for _txt in ('No paiol de proa ficam os coletes.', 'Na popa fica a balsa.', 'Sob o banco do cockpit, o extintor.'):
        EXTRAS.append(('LOCAL_VOCAB', 'equipamento de salvatagem e lugar na mesma frase, ordem inversa (%s: «%s»)' % (_onde, _txt),
                       lambda r, o=_onde, t=_txt: com_lugar(o, t if r else BOM_LUGAR), 'equipamento de salvatagem e lugar a bordo na mesma frase'))
EXTRAS.append(('LOCAL_VOCAB', 'a forma direta («Os coletes ficam no paiol de proa»): a TERMOS e a LOCAL_VOCAB acusam',
               lambda r: com_lugar('diario', ' Os coletes ficam no paiol de proa.' if r else BOM_LUGAR), '[colete + paiol]'))


def em_modo_real(**kw):
    """hoje() no modo real (simulacao False), com os campos da embarcação trocados (None fica como None: SEM DADOS)."""
    k = hoje()
    k['D']['simulacao'] = False
    k['D']['embarcacao'].update(kw)
    return k


def com_embarcacao(**kw):
    """hoje() com os campos da embarcação trocados (None apaga o campo)."""
    k = hoje()
    E = k['D']['embarcacao']
    for c, v in kw.items():
        if v is None:
            E.pop(c, None)
        else:
            E[c] = v
    return k


def motores_c5():
    """hoje() com os equipamentos do §1.4 (C5), com os 2 motores."""
    k = com_equip_c5(hoje())
    poe(k['D']['equipamentos'], 0, qtd=2)
    return k


def rodape(dentro, fora):
    """Rodapé mínimo em 3 linhas: instante() com a guarda e a leitura aceita (linha 2), mais `dentro` logo depois da guarda e
    `fora` na linha 3, fora de instante()."""
    return ("(function () { try { var D = window.CapitaoDados, A = window.CapitaoAgora = {};\n"
            "  A.instante = function () { if (/SOS-/.test(location.pathname)) return null; %s var q = D.snapshot && D.snapshot.quadro;"
            " return q ? { q: q, fonte: 'snapshot' } : null; };\n  A.rebase = function (ms) { %s return true; };\n} catch (e) {} })();\n") % (dentro, fora)


def com_json(muda):
    """hoje() com o 1º JSON das fontes do Drive (a leitura da pasta 05) mudado por muda(dict)."""
    k = hoje()
    rel = next(r for r in sorted(k['F']) if r.endswith('.json'))
    j = json.loads(k['F'][rel])
    muda(j)
    k['F'][rel] = json.dumps(j, ensure_ascii=False)
    return k


def com_base(i, extra):
    """hoje() com `extra` no fim do texto do trecho i da base."""
    k = hoje()
    poe(k['B']['trechos'], i, texto=k['B']['trechos'][i]['texto'] + extra)
    return k


def no_trecho(chave, sec, extra):
    """hoje() com `extra` no fim do texto do trecho `sec` (começo do título) do guia `chave` (g_epirb, g_seafire, protocolo)."""
    k = hoje()
    i = next(i for i, t in enumerate(k['B']['trechos']) if t['fonte'] == G.ARQ[chave] and t['secao'].startswith(sec))
    poe(k['B']['trechos'], i, texto=k['B']['trechos'][i]['texto'] + extra)
    return k


def com_faq_passo(extra):
    """hoje() com `extra` no fim do passo do DSC do D.faq de eletrônicos (o g_eletronicos §5, MMSI_RADIO desde o C5)."""
    k = hoje()
    p = k['D']['faq']['eletronicos']['perguntas'][3]['passos'][1]
    p['t'] += extra
    return k


def com_eletronicos(html):
    """hoje() com `html` (uma seção nova) no fim da página de fonte do guia de eletrônicos."""
    k = hoje()
    rel = next(r for r in sorted(k['F']) if '/Guia de bordo — Eletrônicos' in r)
    k['F'][rel] += html
    return k


# Os 16 equipamentos do CONTRATO-DADOS §1.4 (o que o C5 grava): fabricante e modelo, para a PROTOCOLO_LIMPO.
EQUIP_C5 = [('motores', 'Cummins', 'QSB6.7 305'), ('gerador', 'Onan', 'QD 9'), ('estabilizador', 'Seakeeper', 'Seakeeper 3'),
            ('climatizacao', 'Webasto', 'FCF Platinum 16000 e 12000'), ('eletronicos', 'Garmin', 'GPSMAP 1243xsv'), ('audio', 'Fusion', 'MS-UD755'),
            ('vhf', 'Icom', 'IC-M510 e IC-M37'), ('epirb', 'Ocean Signal', 'SafeSea E100G'), ('seafire', 'Seafire', 'FD 300M'),
            ('dessalinizador', 'Schenker', 'Zen 30'), ('porao', 'Rule', 'Rule 2000 (24 V)'), ('ancora', 'Lewmar', 'V2 · contador AA150'),
            ('piloto', 'Raymarine', 'Evolution EV-1 · ACU-400'), ('radar', 'Garmin', 'GMR 24 xHD3'), ('ais', 'em-trak', 'B954'),
            ('eletrico', 'Victron Energy', 'AGM Super Cycle 12 V 230 Ah')]


def com_equip_c5(k):
    k['D']['equipamentos'] = [{'id': i, 'nome': i, 'fabricante': f, 'modelo': m, 'qtd': 1, 'guia': 'g_motores'} for i, f, m in EQUIP_C5]
    return k

# Listas privadas e pasta do Avanti sintéticas (os termos de verdade nunca entram no repositório).
LISTAS_SINT = {'valores.txt': ['zzq-valor-sintetico'], 'modelos-avanti.txt': ['xp-900', 'yq-77']}
AVANTI_SINT = 'manual do rádio xp-900; folheto do yq-77; nota do xp-900'


def com_vhf(modelo, obs=None):
    k = hoje()
    k.update({'listas': LISTAS_SINT, 'avanti': AVANTI_SINT})
    eq = k['D']['equipamentos']
    poe(eq, [e['id'] for e in eq].index('vhf'), modelo=modelo, **({'obs': obs} if obs else {}))
    return k


def modelos_sinteticos():
    """Achado da revisão 2 do C3: com o modelo de hoje do VHF congelado na PENDENTES (aqui, um da lista sintética), outro modelo da
    lista no lugar, um 2º termo na mesma linha do capitao-dados.js ou mais uma ocorrência do mesmo termo reprovam. Antes, a conta
    por linha e o curinga no candidato da COLISAO_MODELOS deixavam passar (o modelo do Avanti chegava ao capitao-dados.js).
    Desde o C5 o VHF antigo saiu e as duas asserções não têm pendência: o teste congela a amostra só durante a conferência."""
    print('MODELOS_AVANTI e COLISAO_MODELOS: o modelo de hoje congelado, e a troca (listas e pasta do Avanti sintéticas)')
    nomes = ('MODELOS_AVANTI', 'COLISAO_MODELOS')
    V0 = verifica(com_vhf('XP-900'))
    salvo = {n: C.PENDENTES.get(n) for n in nomes}   # C5: nenhuma pendência das duas (None)
    try:
        for n in nomes:
            C.PENDENTES[n] = {'C5': list(V0[n])}   # como o VHF de hoje: cada violação, com a contagem exata
        novas, _, velhas = C.separa({n: V0[n] for n in nomes})
        ok('o modelo de hoje, congelado, passa (%d pendências)' % sum(len(V0[n]) for n in nomes), all(V0[n] for n in nomes) and not novas and not velhas,
           (novas, velhas))
        for o_que, k, quais in (('outro modelo da lista no lugar do de hoje', com_vhf('YQ-77'), nomes),
                                ('2º termo da lista no obs, na mesma linha do capitao-dados.js', com_vhf('XP-900', 'Reserva: YQ-77.'), nomes[:1]),
                                ('mais uma ocorrência do termo de hoje', com_vhf('XP-900', 'Reserva: XP-900.'), nomes[:1])):
            V = verifica(k)
            novas, _, velhas = C.separa({n: V[n] for n in nomes})
            ok('%s: %s reprova' % (' e '.join(quais), o_que), all(n in novas for n in quais), {'novas': novas, 'velhas': velhas})
    finally:
        for n, v in salvo.items():
            if v is None:
                C.PENDENTES.pop(n, None)
            else:
                C.PENDENTES[n] = v
    sai = ' '.join(m for n in nomes for m in V0[n]).lower()
    ok('nenhum termo das listas nem candidato impresso nas violações', not any(t in sai for t in LISTAS_SINT['modelos-avanti.txt']), sai[:200])


def laco_que_segura(R, campos, c, t):
    """Port defeituoso: o segmento 145 → 150 fica parado na última chave (o certo é ir para a do t = 0)."""
    ch = R['chaves'][c]
    k = t // 5
    a, b = ch[k], ch[min(k + 1, len(ch) - 1)]
    f = (t - 5 * k) / 5
    ang = bool((campos.get(c) or {}).get('ang'))
    x = a + ((((b - a + 540) % 360) - 180) * f if ang else (b - a) * f)
    x = C.arred(x, C.casas_de(campos, c))
    return ((x % 360) + 360) % 360 if ang else x


def planta(nome, o_que, monta, espera, so_uma=False):
    """A amostra plantada aparece como violação nova; numa estrutural, fora das pendências congeladas (reprova o gerador). Com `so_uma`
    (revisão do C7), é também a ÚNICA violação nova da regra: a amostra isolada não se apoia em outra mensagem da mesma regra."""
    bom, mau = verifica(monta(False)), verifica(monta(True))
    novos = [m for m in mau[nome] if m not in bom[nome]]
    achados = [m for m in novos if espera in m]
    if achados and all(C.em_relatorio(nome, m) for m in achados):   # na TERMOS, cada regex decide (PESSOAIS, DINHEIRO e LOCAL_SEGURANCA reprovam)
        modo, reprova = ' (em relatório até o %s)' % C.RELATORIO[nome], True
    else:
        livres = C.separa({nome: mau[nome]})[0].get(nome, [])
        modo, reprova = ' e reprova (fora das pendências)', any(espera in m for m in livres)
    ok('%s: acusa a amostra plantada%s%s%s' % (nome, o_que, modo, ' (uma violação só)' if so_uma else ''),
       len(mau[nome]) > len(bom[nome]) and any(espera in m for m in novos) and reprova and (not so_uma or len(novos) == 1),
       {'novas': novos[:3], 'antes': len(bom[nome]), 'depois': len(mau[nome]), 'reprova': reprova})


def rodape_real():
    """C7 (CONTRATO §1.23, §4.1, §6.3 RODAPE_SNAPSHOT): o rodapé de verdade, o ferramentas/demo/rodape.js, é anexado sem mudança ao
    fim do capitao-dados.js e passa a RODAPE_SNAPSHOT (só lê D.snapshot.quadro, dentro de instante() e depois da guarda /SOS-/);
    sem a guarda, ou com uma escrita no D.snapshot, a asserção acusa e o gerador reprovaria. O comportamento (relógio, rebase, SOS)
    é do testes/rodape.py, no navegador."""
    print('C7: o rodape.js real')
    real = C.le_rodape()
    k = hoje()
    js = G.gera_js(k['D'])
    ok('o capitao-dados.js termina com o rodape.js, sem mudança, depois dos dados e do comentário de abertura do rodapé',
       real is not None and js.endswith(';\n' + real) and real.startswith('/* CapitaoAgora') and js.count('/* CapitaoAgora') == 1, (len(js), len(real or '')))
    k['rodape'] = real
    ok('RODAPE_SNAPSHOT: o rodape.js real passa', not verifica(k)['RODAPE_SNAPSHOT'], verifica(k)['RODAPE_SNAPSHOT'][:3])
    ok('SIMULACAO_UNICA e TAMANHO: com o rodapé, o "simulacao": true aparece uma vez e o arquivo cabe no orçamento (120 KB)',
       not verifica(k)['SIMULACAO_UNICA'] and not verifica(k)['TAMANHO'] and len(js.encode('utf-8')) < 120 * 1024, len(js.encode('utf-8')))
    guarda = "if (/SOS-/.test(location.pathname)) return null;"
    ok('o rodape.js tem a guarda /SOS-/ no instante() e a da microtarefa (antes de ler D.simulacao)',
       real.count(guarda) == 1 and real.index(guarda) < real.index('D.snapshot &&') and real.count('if (/SOS-/.test(location.pathname)) return;') == 1
       and real.index('if (/SOS-/.test(location.pathname)) return;') < real.rindex('D.simulacao === true'), 'guardas')
    for o_que, ruim, espera in (
            ('sem a guarda /SOS-/ no instante()', real.replace(guarda, ''), 'antes da guarda /SOS-/'),
            ('com uma escrita no D.snapshot.quadro', real.replace("var q = o.fonte", "D.snapshot.quadro.lat = 0; var q = o.fonte"), 'escreve em D.snapshot'),
            ('com o D.snapshot lido fora do instante()', real.replace('rebase(Date.now());', 'var s = D.snapshot; rebase(Date.now());'), 'fora das formas aceitas')):
        k['rodape'] = ruim
        V = verifica(k)['RODAPE_SNAPSHOT']
        ok('RODAPE_SNAPSHOT: o rodape.js %s acusa (%s)' % (o_que, espera), any(espera in m for m in V), V[:3])


def palavras():
    print('palavras_juntas(): o camelCase e o hífen não escondem a chave da lista (CHAVES_IDENT, CHAVES_PREVISAO)')
    for chave, junta in (('WhatsApp', 'whatsapp'), ('whatsApp', 'whatsapp'), ('Whats App', 'whatsapp'), ('whats_app_marina', 'whatsapp'),
                         ('Hex_I_D', 'hexid'), ('e_mail', 'email'), ('Baixa-mar (m)', 'baixamar'), ('Pré-amar', 'preamar')):
        ps = C.palavras_juntas(chave)
        ok('palavras_juntas(%r) tem %r' % (chave, junta), junta in ps, ps)
    ps = C.palavras_juntas('telefone_marina')
    ok('palavras_juntas: as palavras vêm primeiro, sem repetição ("telefone_marina")', ps[:2] == ['telefone', 'marina'] and len(ps) == len(set(ps)), ps)
    ok('palavras_juntas: chave de uma palavra só = a própria palavra', C.palavras_juntas('local') == ['local'], C.palavras_juntas('local'))
    ok('palavras_juntas: as palavras de palavras_chave continuam todas lá',
       all(set(C.palavras_chave(k)) <= set(C.palavras_juntas(k)) for k in ('hexId', 'canal16', 'hora_local', 'Maré prevista (m)')))


def sem_tie():
    k = hoje()
    k['D']['documentos'] = [d for d in k['D']['documentos'] if d.get('id') != 'tie']
    return k


def registro_tie(V0):
    """Revisão final do C4: a REGISTRO cruza o registro com o numero do documento de id "tie" (§1.2, §1.8). Antes do C7 o TIE não
    tinha id e a falta do documento era a violação congelada do C7; o C7 grava id "tie" e numero = o registro e tira a linha da
    PENDENTES: agora o TIE certo não acusa nada, e o id esquecido, o número esquecido ou errado e o TIE a menos reprovam direto
    (fora das pendências; os dois últimos pelo main(), em reprova())."""
    reg = G.EMBARCACAO['registro']
    ausente = [m for m in verifica(sem_tie())['REGISTRO'] if m.startswith('documentos[tie] ausente')]
    novas, conhecidas, velhas = C.separa({'REGISTRO': V0['REGISTRO']})
    ok('REGISTRO: o TIE de hoje (id "tie", numero = o registro) não acusa, e a PENDENTES não tem mais o REGISTRO (a pendência do C7 saiu)',
       not V0['REGISTRO'] and not novas and not velhas and 'REGISTRO' not in conhecidas and 'REGISTRO' not in C.PENDENTES,
       (V0['REGISTRO'], novas, velhas, conhecidas))
    d = hoje()['D']['documentos'][0]
    ok('C7 (§1.8): o 1º documento é o TIE, com id "tie", numero = embarcacao.registro, vence e emitido relativos',
       d['id'] == 'tie' and d['numero'] == reg == G.EMBARCACAO['registro'] and d['venceEm'] == 646 and d['emitidoHa'] == 1180, d)

    def tie(**campos):
        """O dado de hoje com o 1º documento (o TIE) mudado: o valor None tira a chave."""
        k = hoje()
        k['D']['documentos'][0].update({c: v for c, v in campos.items() if v is not None})
        for c, v in campos.items():
            if v is None:
                k['D']['documentos'][0].pop(c, None)
        return k
    for o_que, k, trecho in (
            ('numero = o registro, sem id (esquece o id)', tie(id=None), 'documentos[tie] ausente'),
            ('numero diferente do registro, sem id', tie(id=None, numero='CIA-99-9999'), 'documentos[tie] ausente'),
            ('id "tie" e numero diferente do registro', tie(numero='CIA-99-9999'), 'documentos[tie].numero diferente'),
            ('id "tie" e sem numero (esquece o número)', tie(numero=None), 'documentos[tie].numero ausente')):
        V = verifica(k)['REGISTRO']
        livres = C.separa({'REGISTRO': V})[0].get('REGISTRO', [])
        ok('REGISTRO: TIE com %s acusa e reprova (fora das pendências)' % o_que, any(trecho in m for m in V) and bool(livres), (V, livres))
    k = hoje()
    k['D']['documentos'].append(dict(k['D']['documentos'][0]))
    V = verifica(k)['REGISTRO']
    ok('REGISTRO: dois documentos com id "tie" acusam (o 2º não esconde o 1º)', any('2 documentos com id "tie"' in m for m in V), V)
    ok('REGISTRO: sem documento de TIE nenhum acusa o mesmo (ausente)', len(ausente) == 1, ausente)
    # Modo real (§4.2): o TIE ausente não reprova (o proprietário pode ter só o registro); o numero diferente, sim; registro None = SEM DADOS
    k = tie(id=None)
    k['D']['simulacao'] = False
    V = verifica(k)['REGISTRO']
    ok('REGISTRO: no modo real, registro preenchido e TIE sem id não reprova', not V, V)
    k['D']['documentos'][0].update({'id': 'tie', 'numero': 'CIA-99-9999'})
    V = verifica(k)['REGISTRO']
    ok('REGISTRO: no modo real, TIE com numero diferente acusa', any('numero diferente' in m for m in V), V)
    k = hoje()
    k['D']['simulacao'] = False
    k['D']['embarcacao']['registro'] = None
    V = verifica(k)['REGISTRO']
    ok('REGISTRO: no modo real, registro None (SEM DADOS) não reprova', not V, V)


def rotulos_c2():
    """C2 (CONTRATO §1.1, §1.2, §1.3, §1.5, §1.10): rótulos fora dos títulos e das fontes. Prende o resultado no dado gerado, com o
    texto do contrato (não com as constantes do gerador): os títulos de drive.arquivos, os quatro *Fonte, as fontes soltas
    (embarcacao, canal16, regraAbast), o aviso e a versao da base, as fontes do Drive e o LEIA-ME. Sem DEMO, snapshot, fictício nem
    demonstração em título, nome de arquivo ou fonte; a pasta 05 soma a série de 150 s e o formato do quadro no C8."""
    print('C2: rótulos fora dos títulos e das fontes (§1.5)')
    k = hoje()
    D, B, F = k['D'], k['B'], k['F']
    arq, raiz = D['drive']['arquivos'], 'Drive › Capitão IA v2'
    rot = re.compile(r'\bDEMO\b|(?i:snapshot|fictíc|demonstra)')   # DEMO só em maiúsculas: "gerar_demo.py" e o id "demo" são outra coisa
    guias = {c for c in arq if c.startswith('g_')}
    fixos = {'leiame': 'LEIA-ME — Capitão IA v2', 'checklist': 'Checklist de bordo', 'inventario': 'Inventário de bordo',
             'documentos': 'Controle de documentos', 'agenda': 'Agenda preditiva', 'diario': 'Diário de bordo',
             'abast': 'Registro de abastecimento', 'snapshot': 'Leitura do coletor NMEA — 26-09-2026 10h12.json',
             'protocolo': 'Protocolo de emergência — procedimento padrão'}
    fixos.update({'serie': 'Série do coletor NMEA — 150 s.csv', 'formato': 'Formato do quadro do coletor.csv'})   # C8 (§1.5)
    ok('drive.arquivos: os 14 guias, o checklist, o protocolo e os 9 arquivos do §1.5 (a série de 150 s e o formato do quadro entram no C8), com o título do §1.5',
       len(guias) == 14 and set(arq) - guias == set(fixos) and all(arq[c] == t for c, t in fixos.items())
       and all(arq[c].startswith('Guia de bordo — ') for c in guias), sorted(set(arq) - set(fixos) - guias))
    ok('drive.arquivos: nenhum título com DEMO, snapshot, fictício nem demonstração (o "snapshot" é só a chave)',
       not [t for t in arq.values() if rot.search(t)], [t for t in arq.values() if rot.search(t)])
    ok('D.guias, D.faq.*.fonte, agenda, documentos e trechos da base citam só títulos de drive.arquivos',
       set(D['guias'].values()) <= set(arq.values()) and {f['fonte'] for f in D['faq'].values()} <= set(arq.values())
       and {t['fonte'] for t in D['agenda'] + D['documentos']} <= set(arq.values()) and {t['fonte'] for t in B['trechos']} <= set(arq.values()),
       sorted({t['fonte'] for t in B['trechos']} - set(arq.values()))[:3])
    ok('os quatro *Fonte do §1.1: "<título> · Drive › Capitão IA v2 › <pasta>"',
       (D['agendaFonte'], D['docsFonte'], D['abastFonte'], D['diarioFonte']) == (
           'Agenda preditiva · %s › 03 Agenda de manutenção' % raiz, 'Controle de documentos · %s › 02 Documentos' % raiz,
           'Registro de abastecimento · %s › 06 Abastecimento' % raiz, 'Diário de bordo · %s › 04 Diário de bordo' % raiz),
       (D['agendaFonte'], D['docsFonte'], D['abastFonte'], D['diarioFonte']))
    ok('embarcacao.fonte, protocolos.canal16.fonte e regraAbast: o texto do contrato (§1.2, §1.3, §1.10)',
       D['embarcacao']['fonte'] == 'cadastro da embarcação no app (proprietário)'
       and D['protocolos']['canal16']['fonte'] == 'Protocolo de emergência — procedimento padrão · MAYDAY · canal 16'
       and D['regraAbast'] == 'abastecer antes de 25 % do total dos tanques, 400 L de 1.600 L (Checklist de bordo § Abastecimento)',
       (D['embarcacao']['fonte'], D['protocolos']['canal16']['fonte'], D['regraAbast']))
    fontes = [D['embarcacao']['fonte'], D['posicaoRef']['fonte'], D['snapshot']['fonte'], D['consumo']['fonte'], D['protocolos']['fonte'],
              D['protocolos']['canal16']['fonte'], D['regraAbast'], D['equipNota'], D['agendaFonte'], D['docsFonte'], D['abastFonte'],
              D['diarioFonte'], *(e['fonte'] for e in D['equipamentos']), *(t['fonte'] for t in D['agenda'] + D['documentos'])]
    ok('nenhuma fonte do D com DEMO, snapshot (no texto), fictício nem demonstração (a leitura do coletor é "coletor NMEA · leitura de …")',
       not [f for f in fontes if rot.search(f)], [f for f in fontes if rot.search(f)])
    def textos(v):
        """Todo valor string do D (as chaves não contam: "demo": false é a flag)."""
        if isinstance(v, str):
            yield v
        elif isinstance(v, dict):
            for x in v.values():
                yield from textos(x)
        elif isinstance(v, list):
            for x in v:
                yield from textos(x)
    ok('D inteiro: nenhum valor com a palavra DEMO (títulos, fontes e as notas "no Drive" das listas de hoje)',
       not [t for t in textos(D) if re.search(r'\bDEMO\b', t)], [t for t in textos(D) if re.search(r'\bDEMO\b', t)][:3])
    # A base: versao = 8 hex do sha256 do conteúdo (muda com o texto, não com a data), aviso neutro e equip sem rótulo.
    ok('base: aviso do §1.5 e versao = 8 hex (não a data)',
       B['aviso'] == 'Trechos dos guias de bordo da embarcação Capitão IA (Drive › Capitão IA v2). Sem documentos pessoais, fiscais ou contratuais.'
       and re.fullmatch(r'[0-9a-f]{8}', B['versao']) and list(B)[:2] == ['versao', 'aviso'], (B['versao'], list(B)))
    corpo = {'aviso': B['aviso'], 'trechos': B['trechos']}
    ok('base: a versao é o sha256 do aviso e dos trechos (pelo serializa(), sem a versao)',
       B['versao'] == hashlib.sha256(G.serializa(corpo).encode('utf-8')).hexdigest()[:8] and B['versao'] == G.base_conhecimento()['versao'], B['versao'])
    t0 = G.trechos
    try:
        G.trechos = lambda: [dict(t, texto=t['texto'] + ' ') if i == 0 else t for i, t in enumerate(t0())]
        v2 = G.base_conhecimento()['versao']
    finally:
        G.trechos = t0
    ok('base: mudar uma letra de um trecho muda a versao', v2 != B['versao'] and re.fullmatch(r'[0-9a-f]{8}', v2), (B['versao'], v2))
    ok('base: nenhum trecho com rótulo na fonte, na seção, no equip nem no texto',
       not [t['fonte'] for t in B['trechos'] if any(rot.search(t.get(c) or '') for c in ('fonte', 'secao', 'equip', 'texto'))], B['trechos'][0]['fonte'])
    # As fontes do Drive: nome de arquivo e texto sem rótulo, na pasta do §1.5, e o LEIA-ME sem a regra antiga, sem data e sem ID.
    ok('fontes/**: nenhum nome de arquivo nem texto com DEMO, snapshot, fictício nem demonstração',
       not [r for r, t in F.items() if rot.search(r) or rot.search(t)], [r for r, t in F.items() if rot.search(r) or rot.search(t)][:3])
    nomes = {os.path.splitext(r.split('/')[-1])[0] for r in F}
    titulos = {os.path.splitext(t)[0] if t.endswith(('.json', '.csv')) else t for t in arq.values()}
    ok('fontes/**: um arquivo para cada título de drive.arquivos, com o nome dele (+ .html, .csv ou .json) e nenhum outro', nomes == titulos,
       sorted(nomes ^ titulos)[:3])
    leia = F[arq['leiame'] + '.html']
    antiga = re.compile(r'Nada inventado|SEM DADOS|SEM LEITURA|MANUAL NO DRIVE|A CONFERIR|A CONFIRMAR|\d{2}/\d{2}/\d{4}|drive\.google|docs\.google|[A-Za-z0-9_-]{25,}')
    ok('LEIA-ME: sem a regra antiga (SEM DADOS, MANUAL NO DRIVE…), sem data, sem link nem ID do Drive e com o procedimento padrão',
       not antiga.search(leia) and C.ROTULO in leia and arq['leiame'] in leia, antiga.findall(leia)[:3])


# Revisão 7 do C5 (trava 17, PROMPT §2.3): fabricante, modelo e validade do EPIRB e do Seafire só em Equipamentos, Leme e Documentos.
# Antes, a PROTOCOLO_LIMPO (o D.protocolos) e a AGENDA (o campo equip) eram as únicas guardas: o modelo, a validade ou o lugar escritos
# num guia, no protocolo, na base, no FAQ ou numa página de fonte passavam. A SEGURANCA_SEM_MODELO olha tudo, menos as telas que podem.
SSM = 'SEGURANCA_SEM_MODELO'
MOD = 'fabricante ou modelo de equipamento de segurança'
VAL = 'validade ou data num texto do EPIRB, do Seafire ou do protocolo'
LUG = 'lugar a bordo num texto do EPIRB, do Seafire ou do protocolo'
EXTRAS += [
    (SSM, 'modelo do Seafire no g_seafire §3: «Sistema Seafire FD 300M»', lambda r: no_trecho('g_seafire', '3 · ', ' Sistema Seafire FD 300M.' if r else ' Veja a etiqueta.'),
     MOD + ' [FD 300M]'),
    (SSM, 'modelo do Seafire no trecho «Incêndio · Seafire» do protocolo', lambda r: no_trecho('protocolo', 'Incêndio', ' Modelo FD 300M da Seafire.' if r else ' Veja a etiqueta.'),
     MOD + ' [FD 300M]'),
    (SSM, 'modelo do EPIRB na Salvatagem do protocolo', lambda r: no_trecho('protocolo', 'Salvatagem', ' EPIRB SafeSea E100G.' if r else ' Veja a etiqueta.'),
     MOD + ' [SafeSea E100G]'),
    (SSM, 'pedaço do modelo do EPIRB no g_epirb §3: «SafeSea»', lambda r: no_trecho('g_epirb', '3 · ', ' Modelo SafeSea.' if r else ' Veja a etiqueta.'), MOD + ' [SafeSea]'),
    (SSM, 'fabricante do Seafire no g_seafire §1', lambda r: no_trecho('g_seafire', '1 · ', ' Fabricante Seafire.' if r else ' Veja a etiqueta.'), MOD + ' [Seafire]'),
    (SSM, 'forma junta do modelo: «FD-300M» num trecho de outro guia (o resto da base também vale)',
     lambda r: com_base(T_DSC, ' Use o FD-300M.' if r else ''), MOD + ' [FD-300M]'),
    (SSM, 'fabricante do EPIRB numa página de fonte do Drive (g_epirb)',
     lambda r: com_fonte_final('Guia de bordo — EPIRB.html', '<p>Fabricante Ocean Signal.</p>' if r else ''), 'fontes/01 Manuais e guias de bordo/Guia de bordo — EPIRB.html: ' + MOD + ' [Ocean Signal]'),
    (SSM, 'modelo do EPIRB numa página de fonte que não é de segurança (checklist)',
     lambda r: com_fonte_final('Checklist de bordo.html', '<p>EPIRB E100G.</p>' if r else ''), 'fontes/01 Manuais e guias de bordo/Checklist de bordo.html: ' + MOD + ' [E100G]'),
    (SSM, 'a palavra «Seafire» no diário (só o título «Incêndio · Seafire» do protocolo vale)', lambda r: mais_texto(hoje(), ' Seafire conferido.' if r else ''),
     'diario[0].t: ' + MOD + ' [Seafire]'),
    (SSM, 'modelo do EPIRB no FAQ de segurança (EP-04)',
     lambda r: (lambda k: (k.update({'faq': {'itens': [{'id': 'EP-04', 'titulo': 'Validade', 'resposta': ('Modelo SafeSea. ' if r else 'Confira a data. ') + ROTULO_FIM, 'seguranca': True}]}}), k)[1])(hoje()),
     'faq:itens[0].resposta: ' + MOD + ' [SafeSea]'),
    (SSM, 'validade no FAQ de segurança (EP-04): «Validade 03/2028»',
     lambda r: (lambda k: (k.update({'faq': {'itens': [{'id': 'EP-04', 'titulo': 'Validade', 'resposta': ('Validade 03/2028. ' if r else 'Confira a data. ') + ROTULO_FIM, 'seguranca': True}]}}), k)[1])(hoje()),
     'faq:EP-04.resposta: ' + VAL),
    (SSM, 'modelo do EPIRB no D.protocolos (junto da PROTOCOLO_LIMPO)', lambda r: protocolo('mob', None, 'Acione o SafeSea.' if r else 'Acione o EPIRB.'), 'protocolos.mob[3]: ' + MOD + ' [SafeSea]'),
    (SSM, 'validade com data no g_epirb §4: «Validade 12/03/2027»', lambda r: no_trecho('g_epirb', '4 · ', ' Validade 12/03/2027.' if r else ' Veja a etiqueta.'), VAL),
    (SSM, 'validade com data no g_seafire §4: «Válido até 30/11/2027»', lambda r: no_trecho('g_seafire', '4 · ', ' Válido até 30/11/2027.' if r else ' Veja a etiqueta.'), VAL),
    (SSM, 'validade em dias no g_epirb §4: «Vence em 180 dias»', lambda r: no_trecho('g_epirb', '4 · ', ' Vence em 180 dias.' if r else ' Veja a etiqueta.'), VAL),
    (SSM, 'validade por mês e ano no g_epirb §4: «março de 2028»', lambda r: no_trecho('g_epirb', '4 · ', ' Validade: março de 2028.' if r else ' Veja a etiqueta.'), VAL),
    (SSM, 'validade só com o mês e o ano em número: «válida até 03/2028»', lambda r: no_trecho('g_epirb', '4 · ', ' Bateria válida até 03/2028.' if r else ' Veja a etiqueta.'), VAL),
    (SSM, 'validade no protocolo: «vence em 2027»', lambda r: protocolo('mob', None, 'O EPIRB vence em 2027.' if r else 'Acione o EPIRB.'), 'protocolos.mob[3]: ' + VAL),
    (SSM, 'validade numa página de fonte do protocolo', lambda r: com_fonte_final('Protocolo de emergência — procedimento padrão.html', '<p>Validade 12/03/2027.</p>' if r else ''),
     'fontes/07 Protocolos de emergência/Protocolo de emergência — procedimento padrão.html: ' + VAL),
    (SSM, 'lugar do EPIRB sem o equipamento na frase: «Fica no paiol de proa»', lambda r: no_trecho('g_epirb', '2 · ', ' Fica no paiol de proa.' if r else ' Veja a etiqueta.'), LUG),
    (SSM, 'lugar numa página de fonte do g_seafire: «Fica na praça de máquinas»', lambda r: com_fonte_final('Guia de bordo — Sistema fixo de incêndio.html', '<p>Fica na praça de máquinas.</p>' if r else ''),
     'fontes/01 Manuais e guias de bordo/Guia de bordo — Sistema fixo de incêndio.html: ' + LUG),
]


def seguranca_sem_modelo():
    print('Revisão 7 do C5 (trava 17): fabricante, modelo e validade do EPIRB e do Seafire só em Equipamentos, Leme e Documentos')
    bom = len(verifica(hoje())[SSM])
    ok('SEGURANCA_SEM_MODELO: o dado de hoje não acusa nada (o título «Incêndio · Seafire» do protocolo, o inventário e os equipamentos valem)', bom == 0, verifica(hoje())[SSM][:3])
    # o que pode: Equipamentos (D.equipamentos), Documentos (D.documentos), Leme (D.agenda) e os CSV do inventário, dos documentos e da agenda
    k = hoje()
    poe(k['D']['equipamentos'], 7, nota=k['D']['equipamentos'][7].get('nota', '') + ' SafeSea E100G, Ocean Signal.')
    k['D']['documentos'].append({'id': 'doc-teste', 'nome': 'Certificado do EPIRB SafeSea E100G', 'vence': '12/03/2027'})
    k['D']['agenda'].append({'id': 'x', 't': 'Teste do EPIRB SafeSea', 'sistema': 'epirb'})
    for sufixo, extra in (('Inventário de bordo.csv', '\nEPIRB,Ocean Signal,SafeSea E100G\n'), ('Controle de documentos.csv', '\nCertificado SafeSea E100G,12/03/2027\n'),
                          ('Agenda preditiva.csv', '\nTeste do EPIRB SafeSea\n')):
        rel = next(r for r in sorted(k['F']) if r.endswith(sufixo))
        k['F'][rel] += extra
    V = verifica(k)[SSM]
    ok('SEGURANCA_SEM_MODELO: fabricante, modelo e validade em Equipamentos, Documentos e Leme (D e CSV do inventário, dos documentos e da agenda) não acusam', not V, V[:3])
    # a validade e o lugar só valem nos guias inteiros de segurança: «a cada 12 meses» e a «praça de máquinas» dos outros guias passam
    V = verifica(no_trecho('g_motores', '7 · ', ' Revisão em março de 2028, na praça de máquinas.'))[SSM]
    ok('SEGURANCA_SEM_MODELO: a validade e o lugar de um guia que não é de segurança (g_motores §7) não acusam', len(V) == bom, V[:3])
    # o protocolo de hoje (C6) e os 16 equipamentos (C5) juntos passam
    k = com_equip_c5(hoje())
    k['D']['protocolos'] = copy.deepcopy(PROTOCOLOS_C6)
    V = verifica(k)[SSM]
    ok('SEGURANCA_SEM_MODELO: o protocolos do §1.3 (C6) com os equipamentos do §1.4 passa', not V, V[:3])
    # a guarda vale pelo id, não pela marca `seguranca` que o dado carrega
    k = mob_sem_marca('Acione o SafeSea.')
    V = verifica(k)[SSM]
    ok('SEGURANCA_SEM_MODELO: vale pelo id (epirb, seafire), também sem a marca `seguranca` nos equipamentos', any('[SafeSea]' in m for m in V), V[:3])


def amostras():
    print('confere(): uma amostra plantada por asserção (%d), as %d extras da revisão e as %d isoladas da revisão do C7' % (len(C.NOMES), len(EXTRAS), len(C7_REV)))
    faltam = [n for n in C.NOMES if n not in AMOSTRAS and n != 'EMENDA']
    ok('toda asserção da §6.3 tem amostra', not faltam, faltam)
    for nome in C.NOMES:
        if nome == 'EMENDA':
            k = com_replay(hoje())
            limpo = verifica(k)['EMENDA']
            orig = C.laco_valor
            C.laco_valor = laco_que_segura
            try:
                ruim = verifica(k)['EMENDA']
            finally:
                C.laco_valor = orig
            ok('EMENDA: acusa o laço que não fecha (port plantado com o segmento 145 → 150 parado)', not limpo and ruim, (limpo, ruim))
            continue
        if nome not in AMOSTRAS:
            continue
        monta, espera = AMOSTRAS[nome]
        planta(nome, '', monta, espera)
    for nome, o_que, monta, espera in EXTRAS:
        planta(nome, ' — ' + o_que, monta, espera)
    for nome, o_que, monta, espera in C7_REV:
        planta(nome, ' — C7: ' + o_que, monta, espera, so_uma=True)
    # a FONTES_RELATIVAS lê só as pastas 02, 03, 04 e 06: a data da 05 (a leitura de 26/09 fica até a Fase 3, §6.6) e a do inventário não acusam
    for pasta in ('tele', 'manuais'):
        V = verifica(com_csv_na_pasta(pasta, 'Extra.csv', 'Data,Valor\n12/09/2026,1\n'))['FONTES_RELATIVAS']
        ok('FONTES_RELATIVAS: uma data num CSV da pasta «%s» (fora das quatro da regra) não acusa' % pasta, not V, V[:2])
    # Revisão do C6: sem o guia `protocolo`, os 9 campos que ele repete reprovam um a um (antes, nenhum reprovava e os 9 perdiam a fonte única)
    V = verifica(sem_guia('protocolo'))['PROTOCOLOS']
    campos = ('mob', 'seafire.passos', 'epirb.passos', 'alagamento', 'abandono', 'salvatagem', 'panpan', 'dsc', 'roteiro')
    ok('PROTOCOLOS: sem o guia protocolo, os 9 campos que ele repete reprovam um a um (drive.arquivos ausente, §1.3), e só eles',
       len(V) == 9 and all(any(m == 'drive.arquivos.protocolo ausente (repete protocolos.%s, §1.3)' % c for m in V) for c in campos), V[:3])
    V0_PL = verifica(hoje())['PROTOCOLO_LIMPO']
    k = hoje()
    k['D']['protocolos'] = copy.deepcopy(PROTOCOLOS_C6)
    ok('PROTOCOLO_LIMPO: o protocolos do §1.3 (o texto do C6) passa nas regras novas', not verifica(k)['PROTOCOLO_LIMPO'], verifica(k)['PROTOCOLO_LIMPO'][:3])
    # Revisão 3 do C3: com os 16 equipamentos do §1.4 (C5), o "V2" do Lewmar não casa o "v2" de "Capitão IA v2" do protocolos.fonte.
    k = com_equip_c5(hoje())
    k['D']['protocolos'] = copy.deepcopy(PROTOCOLOS_C6)
    V = verifica(k)
    ok('PROTOCOLO_LIMPO: o protocolos do §1.3 com os equipamentos do §1.4 passa (0 violações)', not V['PROTOCOLO_LIMPO'], V['PROTOCOLO_LIMPO'][:3])
    # C5: os textos de emergência que os guias repetem (g_motores §4, g_porao §4, g_eletronicos §5, g_seafire, g_epirb e o
    # protocolo) são constantes do gerador desde o C5; são os do §1.3, letra por letra (o C6 monta o D.protocolos com elas).
    P6 = PROTOCOLOS_C6
    ok('textos de emergência do gerador (C5, C6) = os do §1.3', (G.TXT_ROTEIRO, G.TXT_MOB, G.TXT_SEAFIRE, G.TXT_EPIRB, G.TXT_EPIRB_TESTE, G.TXT_ALAGAMENTO,
                                                                G.TXT_ABANDONO, G.TXT_OLEO, G.TXT_SALVATAGEM, G.TXT_PANPAN, G.TXT_DSC, G.MMSI_RADIO, G.ROTULO,
                                                                G.MMSI_ROTULO, G.TXT_INDICATIVO, G.TXT_PLOTTER, G.TXT_HUD, G.NOTA_ETIQUETA)
       == (P6['roteiro'], P6['mob'], P6['seafire']['passos'], P6['epirb']['passos'], P6['epirb']['teste'], P6['alagamento'], P6['abandono'],
           P6['oleo'], P6['salvatagem'], P6['panpan'], P6['dsc'], P6['mmsiRadio'], P6['rotulo'],
           P6['mmsiRotulo'], P6['indicativo'], P6['plotter'], P6['hud'], P6['seafire']['nota']))
    # C6: o D.protocolos que o gerador grava é o do §1.3, letra por letra (PROTOCOLOS_C6 é a cópia do contrato, escrita aqui à mão, não
    # lida do gerador), com os 18 campos na ordem da tabela, sem nada a mais. A salvatagem é a do PROMPT §2.3.
    Dp = hoje()['D']['protocolos']
    ok('C6 (§1.3): o D.protocolos do gerador = o texto do contrato, letra por letra (18 campos, mesma ordem)',
       Dp == P6 and list(Dp) == ['rotulo', 'fonte', 'mmsiRadio', 'mmsiRotulo', 'indicativo', 'plotter', 'hud', 'canal16', 'roteiro', 'mob', 'seafire',
                                 'epirb', 'alagamento', 'abandono', 'oleo', 'salvatagem', 'panpan', 'dsc'], [k for k in Dp if Dp.get(k) != P6.get(k)])
    ok('C6 (§1.3): seafire e epirb deixam de ser null: passos e nota da etiqueta (NOTA_ETIQUETA); o epirb leva também o teste',
       Dp['seafire'] == {'passos': P6['seafire']['passos'], 'nota': C.NOTA} and Dp['epirb'] == {'passos': P6['epirb']['passos'], 'teste': P6['epirb']['teste'], 'nota': C.NOTA}
       and len(Dp['seafire']['passos']) == 5 and len(Dp['epirb']['passos']) == 4)
    ok('C6 (§1.3): o roteiro tem o MMSI do rádio (etiqueta), a posição no plotter e "PESSOAS A BORDO: conte agora"; o MOB sem marca',
       Dp['roteiro'][2] == 'MMSI — LEIA NA ETIQUETA DO RÁDIO (Licença de Estação)' and Dp['roteiro'][5] == 'PESSOAS A BORDO: conte agora'
       and 'último fix' not in ' '.join(Dp['roteiro']).lower() and 'Garmin' not in ' '.join(Dp['mob']) and '710123456' not in json.dumps(Dp),
       Dp['roteiro'])
    ok('C6 (§1.3): a salvatagem é o texto fixo do PROMPT §2.3, igual ao do confere.py e ao da cópia do contrato', Dp['salvatagem'] == C.SALVATAGEM_TXT == P6['salvatagem'])
    B0 = G.base_conhecimento()
    secoes = {}
    for t in B0['trechos']:
        secoes.setdefault(t['fonte'], []).append(t['secao'])
    ok('C5 (§1.4, §1.5): 16 equipamentos, 16 guias (um para cada equipamento), 91 trechos e o g_gerador §2 · Ligar no lugar',
       len(G.EQUIPAMENTOS) == 16 and len(G.FONTE_GUIA) == 16 and len(B0['trechos']) == 91 and all(e['guia'] in G.FONTE_GUIA for e in G.EQUIPAMENTOS)
       and secoes[G.ARQ['g_gerador']][1] == '2 · Ligar' and [len(secoes[G.ARQ[k]]) for k in ('g_motores', 'g_seafire', 'g_epirb', 'checklist', 'protocolo')] == [10, 4, 4, 7, 9],
       (len(G.EQUIPAMENTOS), len(G.FONTE_GUIA), len(B0['trechos'])))
    # Revisão 4 do C5: o passo a passo do Seafire fica só no §1 (os 5 passos do protocolo, letra por letra) e no §3 (o que dizer depois do
    # disparo). O §2 é só o disparo manual e não tem as palavras que casavam perguntas comuns ("disparou", "depois", "esfriar", "abra",
    # "acesso"); o §3 não manda "esfriar" nem "abrir". O g_motores §6 diz "Depois de navegar" (3 das 4 palavras de "como esfriar o motor
    # depois de navegar"). O cerebro.py confere o efeito no navegador.
    sf = {t['secao']: t['texto'] for t in B0['trechos'] if t['fonte'] == G.ARQ['g_seafire']}
    s1, s2, s3 = (sf[k].lower() for k in ('1 · Em caso de fogo', '2 · Disparo manual', '3 · Depois da descarga'))
    ok('revisão 4 do C5: g_seafire §1 = os 5 passos do protocolo; "não abra o acesso ao motor" só no §1 e no §3',
       sf['1 · Em caso de fogo'].startswith(' '.join(G.TXT_SEAFIRE)) and 'não abra o acesso ao motor' in s1 and 'não abra o acesso ao motor' in s3
       and 'não abra' not in s2 and 'acesso' not in s2, (s2[:120],))
    ok('revisão 4 do C5: g_seafire §2 sem "disparou", "depois" nem "esfriar"; §3 sem "esfriar" nem "abrir", com os motores, o gerador e a ventilação desligados',
       not [w for w in ('disparou', 'depois', 'esfri') if w in s2] and not [w for w in ('esfri', ' abrir', 'ao abrir') if w in s3]
       and 'motores, gerador e ventilação desligados' in s3 and 'disparou ou descarregou' in s3, (s2[:120], s3[:160]))
    ok('revisão 4 do C5: g_motores §6 começa com "Depois de navegar"',
       next(t['texto'] for t in B0['trechos'] if t['fonte'] == G.ARQ['g_motores'] and t['secao'] == '6 · Parada').startswith('Depois de navegar'))
    V5 = verifica(hoje())
    ok('FONTE_LIMITES: a constante LIMITES do gerador confere com os §n dos guias (0 violações, %d limites)' % len(G.LIMITES), not V5['FONTE_LIMITES'] and len(G.LIMITES) == 21,
       V5['FONTE_LIMITES'][:3])
    # Revisão do C5: a regra do diesel e a do volante são as da LIMITES, escritas igual no texto. Diesel: sobre o total dos tanques,
    # como o diesel_litros (25 % de um tanque de 800 L seriam 200 L), nunca "em qualquer tanque". Volante: no ponto de estabilização
    # do Seakeeper 3 ou acima (cerca de 85 % da rotação de operação no manual do fabricante; os 60 % de antes contradiziam a folha).
    LD, LV = G.LIMITES['diesel_litros'], G.LIMITES['seakeeper_volante_pct']
    abast = dict(G.GUIAS['checklist']['secoes'])['Abastecimento']
    total = '%s L de %s L' % (G.br(LD['aviso']['abaixo']), G.br(G.TANQUES['diesel_l']))
    ok('regra do diesel sobre o total dos tanques, igual no checklist, no regraAbast e no LIMITES (%s)' % total,
       LD['aviso']['abaixo'] == G.TANQUES['diesel_l'] * G.DIESEL_AVISO_PCT // 100 and total in abast and total in G.REGRA_ABAST
       and 'do total' in abast and 'do total' in G.REGRA_ABAST and 'qualquer tanque' not in abast + G.REGRA_ABAST, (abast, G.REGRA_ABAST))
    ok('volante do estabilizador: a regra do guia (nominal), o normal e o aviso da LIMITES são o mesmo número, a partir de 85 %',
       G._eq('estabilizador')['nominal']['pct_estabiliza'] == LV['normal']['de'] == LV['aviso']['abaixo'] >= 85, LV)
    ok('equipamentos de segurança (EPIRB e Seafire): nota = NOTA_ETIQUETA e nenhum fabricante ou modelo no equip, na fonte e no texto dos trechos',
       all(e.get('nota') == C.NOTA for e in G.EQUIPAMENTOS if e.get('seguranca')) and not [
           t for t in B0['trechos'] for e in G.EQUIPAMENTOS if e.get('seguranca') for n in [e['fabricante']] + C.candidatos_modelo(e['fabricante'], e['modelo'])
           if any(next(C.acha_nomes(t[k], n), None) for k in ('fonte', 'equip', 'texto'))]
       and [e['id'] for e in G.EQUIPAMENTOS if e.get('seguranca')] == ['epirb', 'seafire'])
    # Revisão final do C3 (trava 17): o que continua passando, de propósito. Os outros equipamentos ficam na regra do §2.5 (parte solta
    # do modelo, como "M37" e "Evolution", não conta; "IC-M37", "Icom" e "Lewmar V2" contam), o "v2" de "Capitão IA v2" no
    # protocolos.fonte não acusa o "V2" do Lewmar, e uma frase com o nome inteiro do EPIRB dá UMA violação (não uma por palavra).
    for frase in ('Piloto Evolution em espera.', 'Use o M37 portátil.', 'Gerado pelo Capitão IA v2.', 'Acione o sinal do EPIRB.'):
        k = com_equip_c5(hoje())
        k['D']['protocolos'] = copy.deepcopy(PROTOCOLOS_C6)
        k['D']['protocolos']['mob'].append(frase)
        ok('PROTOCOLO_LIMPO: %r passa (regra do §2.5 para os outros equipamentos)' % frase, not verifica(k)['PROTOCOLO_LIMPO'], verifica(k)['PROTOCOLO_LIMPO'][:2])
    for frase in ('Dispare o FD 300M no manual.', 'Acione o SafeSea E100G agora.', 'Fabricante: Ocean Signal.'):
        k = hoje()
        k['D']['protocolos'] = copy.deepcopy(PROTOCOLOS_C6)
        k['D']['protocolos']['mob'].append(frase)
        v = verifica(k)['PROTOCOLO_LIMPO']
        ok('PROTOCOLO_LIMPO: %r dá uma violação só por ocorrência' % frase, len([m for m in v if 'fabricante ou modelo' in m]) == 1, v[:4])
    v = [m for m in verifica(com_tarefa_seguranca('epirb', 'EPIRB Ocean Signal SafeSea E100G'))['AGENDA'] if 'epirb-teste.equip' in m]
    ok('AGENDA: o equip com o fabricante e o modelo inteiros dá uma violação por tarefa (não uma por palavra)', len(v) == 1, v)
    ok('SEM_INDICATIVO e SEM_PREVISAO: o cabeçalho dos CSV de hoje passa, com a coluna Local do registro de abastecimento (o posto) e sem o resto',
       not V['SEM_INDICATIVO'] and not V['SEM_PREVISAO'] and any(c.endswith('Registro de abastecimento.csv:Local') for c, _ in C.Ctx(
           hoje()['D'], G.base_conhecimento(), hoje()['F'], {}).chaves()), (V['SEM_INDICATIVO'][:2], V['SEM_PREVISAO'][:2]))
    ok('MMSI9: o protocolos do §1.3 ("identificação programada no rádio: é o MMSI") passa',
       not [m for m in V['MMSI9'] if m.startswith('protocolos')], [m for m in V['MMSI9'] if m.startswith('protocolos')][:3])
    # Revisão 2 do C4 (barco_sos): o nome, o único dado do barco que o SOS mostra, não conta, nem com a marca dentro dele; número
    # vizinho dos da embarcação também não (1,15 m · 21,1 m · 112,4 m · 12,40 mm · 9,35 t · 20230). A regra da tela (verificar.py:
    # sem os números, porque o SOS mostra o clima real, e sem a base, que sai da S1 na 1b) não acusa o clima, a base nem o nome, e
    # acusa o registro, o fabricante, o modelo, a marca e o motor.
    k = protocolo('roteiro', 1, 'AQUI É MARÉVIA STAR, MARÉVIA STAR, MARÉVIA STAR')
    k['D']['embarcacao']['nome'] = 'Marévia Star'
    novos = [m for m in verifica(k)['PROTOCOLO_LIMPO'] if m not in V0_PL]
    ok('PROTOCOLO_LIMPO: o nome com a marca dentro ("AQUI É MARÉVIA STAR") não acusa', not novos, novos[:3])
    k = protocolo('mob', None, 'A 2 m da pessoa; 1,15 m; 21,1 m; 112,4 m; 12,40 mm; 9,35 t; 20230.')
    novos = [m for m in verifica(k)['PROTOCOLO_LIMPO'] if m not in V0_PL]
    ok('PROTOCOLO_LIMPO: número vizinho dos da embarcação não acusa', not novos, novos[:3])
    E = hoje()['D']['embarcacao']
    tela = C.barco_sos(E, numeros=False, base=False)
    achou = lambda t: sorted({c for c, _, _ in C.acha_barco(t, E, tela)})
    ok('barco_sos da tela (verificar.py): o nome, a base (até a 1b) e o clima real não acusam',
       not achou('AQUI É CAPITÃO IA · BALNEÁRIO CAMBORIÚ · ondas 1,1 m · 22 °C · 2023'), achou('AQUI É CAPITÃO IA · BALNEÁRIO CAMBORIÚ · ondas 1,1 m · 22 °C · 2023'))
    ok('barco_sos da tela: registro, fabricante, modelo, marca e motor acusam',
       achou('ESTALEIRO MARÉVIA · MAREVIA 40 HT · cia 23 0417 · CUMMINS') == ['fabricante', 'marca', 'modelo', 'motor', 'registro'],
       achou('ESTALEIRO MARÉVIA · MAREVIA 40 HT · cia 23 0417 · CUMMINS'))
    # Revisão 3 do C4 (problemas_barco_sos do verificar.py): na simulação, modelo e rotulo None tiram o valor da conferência da tela
    # (falta_barco_sos os acusa; sem a chave simulacao, também); no modo real (simulacao false, §4.2), None é SEM DADOS e nada falta,
    # nem com todos os campos None, e o que existe segue acusando (o modelo ausente não acusa nem derruba a marca, que precisa dele).
    sem = dict(E, modelo=None, rotulo=None)
    ok('falta_barco_sos: o dado gerado de hoje tem os cinco campos (a conferência da tela vale)',
       C.falta_barco_sos(E, True) == [] and C.falta_barco_sos(E, False) == [], (C.falta_barco_sos(E, True), C.falta_barco_sos(E, False)))
    ok('falta_barco_sos: na simulação, modelo e rotulo None reprovam a conferência (com simulacao ausente também)',
       C.falta_barco_sos(sem, True) == ['modelo', 'rotulo'] and C.falta_barco_sos(sem, None) == ['modelo', 'rotulo'],
       (C.falta_barco_sos(sem, True), C.falta_barco_sos(sem, None)))
    ok('falta_barco_sos: no modo real, modelo e rotulo None (SEM DADOS) não reprovam, nem com todos os campos None',
       C.falta_barco_sos(sem, False) == [] and C.falta_barco_sos({k: None for k in C.BARCO_SOS_EXIGIDO}, False) == [],
       (C.falta_barco_sos(sem, False), C.falta_barco_sos({k: None for k in C.BARCO_SOS_EXIGIDO}, False)))
    tela_real = C.barco_sos(sem, numeros=False, base=False)
    texto_real = 'ESTALEIRO MARÉVIA · MAREVIA 40 HT · cia 23 0417 · CUMMINS'
    ok('barco_sos no modo real (modelo e rotulo None): o fabricante, o motor e o registro presentes seguem acusando',
       sorted({c for c, _, _ in C.acha_barco(texto_real, sem, tela_real)}) == ['fabricante', 'motor', 'registro'],
       sorted({c for c, _, _ in C.acha_barco(texto_real, sem, tela_real)}))
    # O que não pode reprovar (revisão 3): milhar do pt-BR e ângulos (COORD_TEXTO), palavras em maiúsculas com os prefixos de rádio
    # (SEM_INDICATIVO), o número do TIE (TERCEIROS) e a hora local da leitura da pasta 05 (já nos dados de hoje).
    V0 = verifica(hoje())
    for nome, o_que, k in (
            ('COORD_TEXTO', 'milhar do pt-BR, temperatura e rumo', mais_texto(hoje(), ' 1.236,4 h · 1.600 L · 2.050 rpm · 12.000 · rotações de 1.000, 1.500 e '
                                                                              '2.000 rpm · 26 °C · rumo 230° · 1º de outubro.')),
            ('SEM_INDICATIVO', 'PUXE e PROA em maiúsculas', mais_texto(hoje(), ' PUXE A ALAVANCA. PROA LIVRE. PRAÇA OK.')),
            ('TERCEIROS', 'documentos[tie].numero = o registro', (lambda k: (k['D']['documentos'].append({'id': 'tie', 'n': 'TIE', 'numero': 'CIA-23-0417'}), k)[1])(hoje())),
            ('TERCEIROS', 'nota fiscal sem número', mais_texto(hoje(), ' Nota fiscal de abastecimento · 12/09/2026 conferida; apólice no Drive.')),
            ('MMSI9', 'o texto do g_ais §2 do §1.5 ("identificação programada no transponder")', mais_texto(hoje(), ' O AIS transmite a '
             'identificação programada no transponder; o MMSI é o do rádio de bordo (etiqueta / Licença de Estação).')),
            # Revisão 3 do C4: a energia AC da climatização e do gerador, numa frase sem o estabilizador, e o modelo do piloto (ACU-400)
            # ou "CAÇA" numa frase com ele não acusam; o g_seakeeper §1 e o checklist novos (banco de 12 V) também não.
            ('ESTABILIZADOR_12V', 'AC da climatização e do gerador, ACU-400 e CAÇA', mais_texto(hoje(), ' Climatização com energia AC do gerador. '
             'Estabilizador e piloto Evolution ACU-400 ligados. SEAKEEPER EM CAÇA DE ONDA.')),
            ('ESTABILIZADOR_12V', 'o g_seakeeper §1 e o checklist de saída do §1.5', com_trecho({'fonte': G.GUIAS['g_seakeeper']['titulo'],
             'secao': '1 · Energia', 'equip': 'Estabilizador Seakeeper', 'texto': G.GUIAS['g_seakeeper']['secoes'][0][1]
             + ' ' + G.GUIAS['checklist']['secoes'][0][1]}))):
        novos = [m for m in verifica(k)[nome] if m not in V0[nome]]
        ok('%s: %s não acusa' % (nome, o_que), not novos, novos[:3])
    ok('SEM_INDICATIVO: a hora_local da leitura da pasta 05 não é lugar', not [m for m in V0['SEM_INDICATIVO'] if 'hora_local' in m])
    # C4 (§1.2): a embarcação gerada passa; com os equipamentos do §1.4 (C5), a motorizacao confere com os motores; no modo real
    # (§4.2), o que é None (SEM DADOS) não reprova.
    ok('EMBARCACAO: a embarcação gerada passa (0 violações)', not V0['EMBARCACAO'], V0['EMBARCACAO'][:3])
    registro_tie(V0)
    ok('ESTABILIZADOR_12V: a saída de hoje passa (0 violações), com o g_seakeeper §1 no banco de 12 V',
       not V0['ESTABILIZADOR_12V'] and '12 V' in G.GUIAS['g_seakeeper']['secoes'][0][1], V0['ESTABILIZADOR_12V'][:3])
    V = verifica(motores_c5())['EMBARCACAO']
    ok('EMBARCACAO: a motorizacao gerada confere com o equipamentos[motores] do §1.4 (2 × Cummins QSB6.7 305)', not V, V[:3])
    # Revisão do C4: o teste antigo punha None nos campos DEPOIS da geração e deixava o rotulo antigo ("Marévia 40 HT · …"), sem
    # passar pela derivação; com SIMULACAO = False e um campo de origem None, o gerador gravava "None · 12,40 m · 2023" e
    # "2 × None QSB6.7 305 · eixo", ou parava com TypeError na importação (comprimento ou diesel None). Agora o modo real usa as
    # mesmas funções do gerador (rotulo_de, motorizacao_de, tanques_de), e os valores gerados saem delas.
    ok('EMBARCACAO: rotulo, motorizacao e o texto dos tanques do snapshot saem de rotulo_de, motorizacao_de e tanques_de',
       (G.EMBARCACAO['rotulo'], G.EMBARCACAO['motorizacao'], G.SNAPSHOT['diesel']['tanques'])
       == (G.rotulo_de(G.EMBARCACAO), G.motorizacao_de(G.MOTOR), G.tanques_de(G.TANQUES))
       == ('Marévia 40 HT · 12,40 m · 2023', '2 × Cummins QSB6.7 305 · eixo', '2 × 800 L'),
       (G.EMBARCACAO['rotulo'], G.EMBARCACAO['motorizacao'], G.SNAPSHOT['diesel']['tanques']))
    try:
        sem = [G.rotulo_de(dict(G.EMBARCACAO, **{c: None})) for c in C.ORIGEM_ROTULO]
        sem += [G.motorizacao_de(dict(G.MOTOR, **{c: None})) for c in G.MOTOR]
        sem += [G.tanques_de(dict(G.TANQUES, **{c: None})) for c in ('diesel_l', 'diesel_n')]
    except Exception as e:   # o TypeError da importação (comprimento ou diesel None)
        sem = ['%s: %s' % (type(e).__name__, e)]
    ok('EMBARCACAO: com um campo de origem None (modo real), o derivado é None (nunca "None" no texto nem TypeError)',
       sem and all(x is None for x in sem), sem)
    k = hoje()
    k['D']['simulacao'] = False
    E = k['D']['embarcacao']
    E.update({'fabricante': None, 'modelo': None, 'registro': None, 'calado': None, 'comprimento': None})
    E.update({'rotulo': G.rotulo_de(E), 'motorizacao': G.motorizacao_de(dict(G.MOTOR, fabricante=None))})
    V = verifica(k)['EMBARCACAO']
    ok('EMBARCACAO: no modo real, None (SEM DADOS) não reprova, com rotulo e motorizacao derivados pelo gerador (None)',
       not V and E['rotulo'] is None and E['motorizacao'] is None, (V[:3], E['rotulo'], E['motorizacao']))
    # Fixtures limpas: com o replay, a rota e o histórico mínimos, as asserções do laço não acusam nada a mais que o port do C8.
    k = com_historico(com_rota(hoje()))
    V = verifica(k)
    for n in ('JANELA', 'FIO', 'EMENDA', 'LIMITES_FORMA', 'FONTE_LIMITES', 'PISO', 'HORAS', 'ROTA', 'DIA_DE_BORDO', 'HISTORICO'):
        ok('%s: nada a acusar no replay mínimo coerente' % n, not V[n], V[n][:3])
    ok('EMENDA_ROTA: uma rota que o port do em() não consegue rodar (a rota mínima, sem pernas, ini_mn nem corrente) reprova com o motivo',
       len(V['EMENDA_ROTA']) == 1 and V['EMENDA_ROTA'][0].startswith('emendas de 150 s da rota: o port do em() não rodou ('), V['EMENDA_ROTA'])


def porao_e_lugar():
    print('Revisão do C3: porão ≤ teto do normal (JANELA) e salvatagem + lugar na mesma frase em qualquer ordem (LOCAL_VOCAB)')
    V = verifica(com_porao())
    ok('JANELA: o porão no normal (1,2 cm, com o teto de 5 cm em replay.limites) não acusa nada', not V['JANELA'], V['JANELA'][:3])
    V = verifica(com_porao(quadro={'porao_bb_nivel': 5.0}, aninhado={'bb_cm': 5.0, 'be_cm': 0.9, 'ciclos_h': 0}, fixos={'porao_be_nivel': 5.0}))
    ok('JANELA: o porão no teto (5,0 cm, comparação estrita como a nivel()) não acusa', not V['JANELA'], V['JANELA'][:3])
    ok('o teto do porão do gerador é o normal.ate do guia (g_porao §2: 5 cm), nos dois lados',
       [G.LIMITES[c]['normal']['ate'] for c in ('porao_bb_nivel', 'porao_be_nivel')] == [5, 5])
    # O que não é acusado: a frase genérica da salvatagem (sem nome de lugar), o lugar sem equipamento e as tags da página de fonte, que
    # separam a frase (cada <p> é uma frase).
    bom = {n: len(v) for n, v in verifica(hoje()).items()}
    termos = C.carrega_termos()
    equip, lugar = C.equip_salvatagem(termos), C.lugar_a_bordo(termos)
    pares = [f for f in C.R_FRASE.split(G.TXT_SALVATAGEM) if equip.search(f) and lugar.search(f)]
    ok('LOCAL_VOCAB: a frase genérica da salvatagem («no local da placa de salvatagem…») tem equipamento e nenhum lugar: passa sem exceção',
       equip.search(G.TXT_SALVATAGEM) and not lugar.search(G.TXT_SALVATAGEM) and not pares, pares)
    for o_que, k in (('lugar sem equipamento', com_lugar('diario', ' Confira o paiol de proa antes de sair.')),
                     ('equipamento numa tag e lugar na seguinte (páginas de fonte)', com_lugar('fonte', 'Coletes</p><p>Paiol de proa'))):
        ok('LOCAL_VOCAB: %s não acusa' % o_que, len(verifica(k)['LOCAL_VOCAB']) == bom['LOCAL_VOCAB'], verifica(k)['LOCAL_VOCAB'][:2])


def grafia_seafire():
    print('Revisão do C6: a grafia «Seafire» em todo dado (GRAFIA_SEAFIRE)')
    k = hoje()
    V0 = verifica(k)['GRAFIA_SEAFIRE']
    eq = k['D']['equipamentos'][I_SEAFIRE]
    ok('GRAFIA_SEAFIRE: o dado de hoje passa (0 violações), com «Seafire» no fabricante, «seafire» no id e «sea fire» só nas palavras de busca (ditado)',
       not V0 and eq['fabricante'] == 'Seafire' and eq['id'] == 'seafire' and 'sea fire' in eq['palavras'], (V0[:3], eq['fabricante'], eq['palavras']))
    novos = lambda k_: [m for m in verifica(k_)['GRAFIA_SEAFIRE'] if m not in V0]
    n = novos(mais_texto(hoje(), ' O Seafire e o id seafire-inspecao ficam em dia; o seafire normalizado também.'))
    ok('GRAFIA_SEAFIRE: «Seafire» e «seafire» passam em qualquer texto', not n, n[:3])
    n = novos(mais_texto(hoje(), ' Veja o sea, o fire e o mar. Fire não vale; sea. Fire! Mar de fogo.'))
    ok('GRAFIA_SEAFIRE: «sea» e «fire» separados por pontuação ou por outra palavra não acusam', not n, n[:3])
    n = novos(com_eletronicos('<h2>9 · Teste</h2><p>O Sea Fire dispara.</p>'))
    ok('GRAFIA_SEAFIRE: «Sea Fire» numa página HTML conta uma vez só (o texto cru e o que o leitor vê são a mesma ocorrência)', len(n) == 1, n[:3])
    n = novos(mais_texto(hoje(), ' O Sea Fire e o Sea-Fire ficam em dia.'))
    ok('GRAFIA_SEAFIRE: duas ocorrências na mesma string dão duas violações (uma por ocorrência)',
       len([m for m in n if m.startswith('diario[0].t:')]) == 2, n[:4])
    # A mensagem diz o caminho, a grafia achada e o trecho; a regex do confere.py é uma só para o valor, a chave e o nome de arquivo.
    n = novos(mais_texto(hoje(), ' O Sea-Fire fica pronto.'))
    ok('GRAFIA_SEAFIRE: a mensagem tem o caminho, a grafia achada e o trecho',
       any(m.startswith('diario[0].t: texto com a grafia «Sea-Fire» do Seafire (§1.3: «Seafire», sem hífen nem espaço) «') and 'Sea-Fire fica pronto' in m for m in n), n[:2])


def reprova(tmp):
    print('Estruturais reprovam o gerador (fora das pendências); a varredura de termos (relatório) não')
    D0, B0 = G.dados, G.base_conhecimento

    F0 = G.gera_fontes

    def rodar(planta, pasta, base=None, fontes=None):
        G.dados = lambda: planta(copy.deepcopy(D0()))   # cópia: o D aponta para as listas do módulo (DIARIO, AGENDA…)
        if base:
            G.base_conhecimento = lambda: base(copy.deepcopy(B0()))
        if fontes:
            G.gera_fontes = lambda D: fontes(dict(F0(D)))
        opcionais = {k: os.environ.pop(k) for k in ('CAPITAO_LISTAS_PRIVADAS', 'CAPITAO_AVANTI') if k in os.environ}   # como o roda()
        try:
            with contextlib.redirect_stdout(io.StringIO()) as o, contextlib.redirect_stderr(io.StringIO()) as e:
                rc = G.main(['--saida', pasta])
        finally:
            G.dados, G.base_conhecimento, G.gera_fontes = D0, B0, F0
            os.environ.update(opcionais)
        return rc, o.getvalue() + e.getvalue()
    coord = lambda D: (D['diario'][0].update({'t': D['diario'][0]['t'] + " Em 26°59,6'S."}), D)[1]
    termo = lambda D: (D['diario'][0].update({'t': D['diario'][0]['t'] + ' (DEMO)'}), D)[1]
    p1, p2 = os.path.join(tmp, 'r1'), os.path.join(tmp, 'r2')
    rc, saida = rodar(coord, p1)
    ok('COORD_TEXTO plantada: main() devolve 1 e não grava nada', rc == 1 and not os.path.exists(p1) and 'COORD_TEXTO' in saida, (rc, saida[-300:]))
    rc, saida = rodar(termo, p2)
    ok('TERMOS plantado (relatório até o C12): main() devolve 0 e grava', rc == 0 and os.path.isfile(os.path.join(p2, 'capitao-dados.js')), (rc, saida[-300:]))
    nan = lambda D: (D['snapshot'].update({'sog': float('nan')}), D)[1]
    p3 = os.path.join(tmp, 'r3')
    rc, saida = rodar(nan, p3)
    ok('NaN no D: main() devolve 1 e não grava nada (o serializador recusa)', rc == 1 and not os.path.exists(p3) and 'não finito' in saida, (rc, saida[-300:]))
    # Achado da revisão do C3: com a asserção inteira em relatório, um null ou um vazio novo do C4–C7 passava (main() devolvia 0).
    def nulo(D):
        D['embarcacao']['fonte'] = None
        D['diario'][0]['t'] = ''
        D['agenda'][0]['quem'] = None
        return D
    # Revisão 2 do C3: o MMSI guardado como número e o null/vazio na base também reprovam (antes, main() devolvia 0 e gravava).
    mmsi_num = lambda D: (D['documentos'][2].update({'mmsi': 710123456}), D)[1]
    base_vazia = lambda B: (B['trechos'][3].update({'secao': '', 'equip': None}), B)[1]
    # Revisão 3 do C3: a 2ª afirmação num trecho que já é pendência, o lugar do EPIRB como campo e o nome de terceiro no quem
    # (antes, main() devolvia 0 e gravava).
    afirma = lambda B: (B['trechos'][T_DSC].update({'texto': B['trechos'][T_DSC]['texto'] + ' Os dados são reais e o barco é real.'}), B)[1]
    lugar = lambda D: (D['equipamentos'][7].update({'local': 'paiol de proa'}), D)[1]
    terceiro = lambda D: (D['agenda'][0].update({'quem': 'Carlos Pereira'}), D)[1]
    seafire_ruim = lambda D: (D['equipamentos'][I_SEAFIRE].update({'nome': 'Sistema Sea-Fire'}), D)[1]   # revisão do C6 (§1.3): a grafia «Seafire»
    # Revisão final do C3: as três regex da TERMOS que reprovam já (travas §2.2 e §2.7), uma a uma, com o texto num campo do D, na
    # base e numa página de fonte do Drive (antes, a TERMOS inteira em relatório: main() devolvia 0 e gravava).
    fone = lambda D: (D['equipe'].update({'nota': 'Marina: (47) 99812-3456.'}), D)[1]
    dinheiro = lambda D: (D['diario'][0].update({'t': D['diario'][0]['t'] + ' Gasto R$ 3.450,00 no abastecimento.'}), D)[1]
    lugar_epirb = lambda D: (D['equipamentos'][7].update({'nome': 'EPIRB — fica no paiol de proa'}), D)[1]
    preco_base = lambda B: (B['trechos'][T_DSC].update({'texto': B['trechos'][T_DSC]['texto'] + ' O preço do rádio é 1.200 reais.'}), B)[1]
    def email_fonte(F):
        rel = next(r for r in sorted(F) if r.endswith('Checklist de bordo.html'))
        F[rel] += '<p>Escreva para oficina@exemplo.com.br.</p>'
        return F
    def coluna_fonte(sufixo, coluna):
        def f(F):
            rel = next(r for r in sorted(F) if r.endswith(sufixo))
            linhas = list(csv.reader(io.StringIO(F[rel])))
            saida = io.StringIO()
            csv.writer(saida, lineterminator='\n').writerows(l + [coluna if j == 0 else 'x'] for j, l in enumerate(linhas))
            F[rel] = saida.getvalue()
            return F
        return f
    for i, (nome, pl, n, base, o_que, *fontes) in enumerate((('NULO', nulo, 3, None, ''), ('TERMOS', fone, 1, None, ' (PESSOAIS: telefone no texto da equipe)'),
                                     ('TERMOS', lambda D: D, 1, None, ' (PESSOAIS: e-mail numa página de fonte do Drive)', email_fonte),
                                     ('TERMOS', dinheiro, 1, None, ' (DINHEIRO: valor em reais no diário)'),
                                     ('TERMOS', lambda D: D, 1, preco_base, ' (DINHEIRO: preço na base)'),
                                     ('TERMOS', lugar_epirb, 1, None, ' (LOCAL_SEGURANCA: lugar do EPIRB no nome)'),
                                     ('SEM_INDICATIVO', lambda D: D, 1, None, ' (coluna Telefone no CSV do inventário)', coluna_fonte('Inventário de bordo.csv', 'Telefone')),
                                     ('SEM_PREVISAO', lambda D: D, 1, None, ' (coluna Maré prevista no CSV do abastecimento)', coluna_fonte('Registro de abastecimento.csv', 'Maré prevista (m)')),
                                     ('SEM_INDICATIVO', lambda D: D, 1, None, ' (coluna WhatsApp no CSV do inventário)', coluna_fonte('Inventário de bordo.csv', 'WhatsApp')),
                                     ('EQUIP', lambda D: (D['equipamentos'][0].update({'fabricante': ''}), D)[1], 1, None, ''),
                                     ('MMSI9', mmsi_num, 1, None, ' (9 dígitos guardados como número)'),
                                     ('NULO', lambda D: D, 2, base_vazia, " (na base: secao '' e equip null)"),
                                     ('AFIRMA_REAL', lambda D: D, 2, afirma, ' (2 afirmações no trecho do DSC)'),
                                     ('SEM_INDICATIVO', lugar, 1, None, ' (equipamentos[epirb].local)'),
                                     ('TERCEIROS', terceiro, 1, None, ' (nome de terceiro no quem da agenda)'),
                                     ('GRAFIA_SEAFIRE', seafire_ruim, 1, None, ' (Sea-Fire no nome do equipamento seafire)'))):
        p = os.path.join(tmp, 'r-%s-%d-%d' % (nome, n, i))
        rc, saida = rodar(pl, p, base, fontes[0] if fontes else None)
        ok('%s plantado fora das pendências%s: main() devolve 1 e não grava nada' % (nome, o_que),
           rc == 1 and not os.path.exists(p) and ('%s %d nova(s)' % (nome, n)) in saida, (rc, saida[-300:]))
    # Pendência que não ocorre mais: o C8 tirou as últimas da PENDENTES (o snapshot sem null); a amostra põe uma pendência sintética (que o dado
    # de hoje não tem) e o main() reprova, sem gravar nada (a lista não pode esconder a volta do defeito).
    p4 = os.path.join(tmp, 'r4')
    pend0, commits0 = C.PENDENTES, C.COMMITS_PENDENTES
    C.PENDENTES, C.COMMITS_PENDENTES = {'NULO': {'C8': ['snapshot.porao: None']}}, ('C8',)
    try:
        rc, saida = rodar(lambda D: D, p4)
    finally:
        C.PENDENTES, C.COMMITS_PENDENTES = pend0, commits0
    ok('pendência que não ocorre mais (uma linha da PENDENTES que o dado já não tem): main() devolve 1 e não grava nada',
       rc == 1 and not os.path.exists(p4) and 'NULO: pendência do C8 que não ocorre mais' in saida, (rc, saida[-300:]))
    # Revisão final do C4, atualizada no C7 (o TIE certo já está no dado e a linha da PENDENTES saiu): o id esquecido ou o numero
    # errado do TIE reprova o main() como violação nova; em nenhum dos dois o main() grava.
    def tie_campos(D, c):
        for k, v in c.items():
            D['documentos'][0].pop(k, None) if v is None else D['documentos'][0].update({k: v})
        return D
    for i, (o_que, campos) in enumerate((('sem o id "tie" (o TIE sem id)', {'id': None}), ('id "tie" e numero errado', {'numero': 'CIA-99-9999'}),
                                         ('id "tie" e sem numero', {'numero': None}))):
        p = os.path.join(tmp, 'r-tie-%d' % i)
        rc, saida = rodar(lambda D, c=campos: tie_campos(D, c), p)
        ok('REGISTRO: TIE %s: main() devolve 1 e não grava nada' % o_que, rc == 1 and not os.path.exists(p) and 'REGISTRO 1 nova(s)' in saida, (rc, saida[-300:]))
    # Com o modo por caminho, as estruturais de hoje têm violações, todas congeladas na PENDENTES (antes: nenhuma violação, porque
    # 14 delas estavam inteiras em relatório). As listas privadas e a pasta do Avanti não vão a este teste (OPCIONAIS).
    novas, conhecidas, velhas = C.separa(verifica(hoje()), set(C.OPCIONAIS))
    ok('dados de hoje: nenhuma violação estrutural fora das pendências e nenhuma pendência velha (%d congeladas)' % sum(
        sum(c.values()) for c in conhecidas.values()), not novas and not velhas and not conhecidas, {'novas': novas, 'velhas': velhas[:3]})
    ok('PENDENTES: vazia desde o C8 (o C4 completou a embarcação, o C5, os equipamentos e os guias, o C6, o D.protocolos, o C7, a agenda, os documentos, o diário '
       'e as fontes relativas e o C8, o snapshot, a rota e o replay), e nenhum commit pendente', C.PENDENTES == {} and C.COMMITS_PENDENTES == ())


# ——————————————————————————————— C8 (CONTRATO §1.14–§1.17, §1.22, §3, §4.1) ———————————————————————————————
# Os valores do §1.22 que não dependem da rota (o laço, os contadores e os tanques, em 12:01:00 e 12:01:45) e os da virada (07:00:00 e 06:59:59):
# a referência é daqui (copiada do contrato), nunca do gerador.
S60, S105 = 120 * 150 + 60, 120 * 150 + 105   # fixar('60') = 12:01:00 e fixar('105') = 12:01:45
C8_LACO_60 = {'sog_nos': 18.1, 'motor_bb_rpm': 2049, 'motor_be_rpm': 2038, 'motor_bb_oleo_bar': 3.9, 'motor_be_oleo_bar': 3.8, 'motor_bb_arref_c': 82.0,
              'motor_be_arref_c': 82.1, 'motor_bb_carga_pct': 62, 'motor_be_carga_pct': 61, 'consumo_lph': 68.0, 'diesel_litros': 1333, 'diesel_bb_pct': 83.7,
              'diesel_be_pct': 82.9, 'distancia_mn': 65.1, 'motor_bb_horimetro_h': 417.6, 'motor_be_horimetro_h': 414.8, 'gerador_kw': 6.4,
              'gerador_horimetro_h': 1241.4, 'seakeeper_volante_rpm': 8426, 'seakeeper_volante_pct': 100, 'bateria_0_tensao_v': 27.79, 'bateria_1_tensao_v': 27.95,
              'bateria_2_tensao_v': 13.69, 'tanque_agua_pct': 86.0, 'tanque_cinzas_pct': 15.0, 'tanque_negras_pct': 9.5, 'porao_bb_nivel': 1.1,
              'porao_be_nivel': 0.9, 'ondas_m': 0.8, 'vento_verdadeiro_nos': 11.3, 'vento_verdadeiro_angulo': 59, 'pressao_barometrica_hpa': 1017.1,
              'temp_ar_externo_c': 22.6, 'temp_agua_c': 20.1, 'temp_praca_maquinas_c': 46, 'jogo_graus': 0.5, 'caimento_graus': 3.1, 'leme_graus': 0.3,
              'gps_satelites': 18, 'ais_alvos': 4, 'estado': 'Navegando', 'marcha': 'avante', 'alarmes': []}
C8_LACO_105 = {'sog_nos': 18.0, 'motor_bb_rpm': 2049, 'motor_be_rpm': 2036, 'motor_bb_arref_c': 81.9, 'motor_be_arref_c': 89.6, 'diesel_litros': 1332,
               'diesel_bb_pct': 83.6, 'diesel_be_pct': 82.9, 'distancia_mn': 65.3, 'gerador_kw': 6.2, 'seakeeper_volante_rpm': 8416, 'bateria_0_tensao_v': 27.8,
               'bateria_1_tensao_v': 27.97, 'porao_bb_nivel': 1.2, 'vento_verdadeiro_nos': 9.8, 'vento_verdadeiro_angulo': 54, 'jogo_graus': 0.3, 'caimento_graus': 3.2,
               'leme_graus': 0.2}
C8_ALARME_105 = {'id': 'arref_be', 'nivel': 'aviso', 'sistema': 'motores', 'lado': 'be', 'campo': 'motor_be_arref_c', 'valor': 89.6, 'limite': 88,
                 'desde': '2026-09-26T15:01:39Z'}
C8_A_ANTES = {'diesel_litros': 474, 'distancia_mn': 311.5, 'motor_bb_horimetro_h': 436.6, 'motor_be_horimetro_h': 433.8, 'gerador_horimetro_h': 1260.4,
              'tanque_agua_pct': 63.2, 'tanque_cinzas_pct': 41.6, 'tanque_negras_pct': 26.6, 'destino': 'Barra Sul (base)', 'destino_mn': 0.0, 'eta': '07:00'}
C8_A_DEPOIS = {'diesel_litros': 1560, 'distancia_mn': 0.0, 'motor_bb_horimetro_h': 412.6, 'motor_be_horimetro_h': 409.8, 'gerador_horimetro_h': 1236.4,
               'tanque_agua_pct': 92.0, 'tanque_cinzas_pct': 8.0, 'tanque_negras_pct': 5.0, 'destino': 'Estaleirinho', 'wp_proximo': 'Ilha das Cabras'}
C8_REGRAS = ('LACO', 'LIMITES_FORMA', 'JANELA', 'FIO', 'EMENDA', 'EMENDA_ROTA', 'PISO', 'HORAS', 'ROTA', 'DIA_DE_BORDO', 'IDS', 'NULO', 'FONTE_LIMITES',
             'SEM_EMERGENCIA', 'COORD_TEXTO', 'TAMANHO', 'RODAPE_SNAPSHOT', 'FONTES_RELATIVAS')


def c8_muda(caminho, valor=SEM):
    """hoje() com D[...caminho] trocado (SEM apaga a chave): a planta das asserções da rota e do replay."""
    def monta(r):
        k = hoje()
        if r:
            x = k['D']
            for c in caminho[:-1]:
                x = x[c]
            if valor is SEM:
                x.pop(caminho[-1], None)
            else:
                x[caminho[-1]] = valor
        return k
    return monta


def c8_com(fn):
    """hoje() mexido por fn(D) quando r."""
    def monta(r):
        k = hoje()
        if r:
            fn(k['D'])
        return k
    return monta


def c8_escala_ponteiro(D):
    """Troca o fator da rota pelo MENOR desvio (6 casas, dentro de [0,9; 1,0]) que põe uma chegada a ponto exatamente num par de segundos de uma emenda
    N·150: o cruzamento da distância percorrida × fator com o início de uma perna (m circuitos + ini_mn) cai entre N·150 − 1 s e N·150. Revisão do C8: o
    antigo `fator × 1,0001` era calibrado para a rota de antes da revisão da Ilha das Cabras (caía na emenda 72, 10:00:00) e, com a rota refeita, não cai em
    emenda nenhuma; a conta agora acompanha a rota, e a amostra continua a ser a única violação da chegada."""
    R, rota = D['replay'], D['rota']
    P = C.preparar(D)
    tot, fator = rota['distancia_mn'], rota['fator']
    base, volta = R['contadores_base']['distancia_mn'], R['por_volta']['distancia_mn']
    inicios = [p['ini_mn'] for p in rota['pernas']] + [tot]
    melhor = None
    for N in range(1, R['por_dia']['voltas']):
        depois = base + N * volta                                          # distância em N·150 s
        antes = base + (N - 1) * volta + P['cumM'][R['duracao'] - 1]       # distância em N·150 − 1 s
        for m in range(rota['circuitos_dia'] + 1):
            for x in inicios:
                B = m * tot + x
                if B <= 0:
                    continue
                f = math.ceil(B / depois * 1e6) / 1e6
                if 0.9 <= f <= 1.0 and f < B / antes and (melhor is None or abs(f / fator - 1) < melhor[0]):
                    melhor = (abs(f / fator - 1), f)
    rota['fator'] = melhor[1]



def c8_alerta(aid, **kw):
    return c8_com(lambda D: D['replay']['alertas'][aid].update(kw))


def c8_pernas(i, **kw):
    return c8_com(lambda D: D['rota']['pernas'][i].update(kw))


POSICAO_KEYS = {'lat', 'lon'}


def c8_real(fn, alvo='F'):
    """O D e as fontes de verdade no modo real (SIMULACAO False no gerador), com fn(F) quando r (ou fn(D), com alvo='D'): a planta da posição nas
    fontes do Drive e em snapshot.gps (§4.3)."""
    def monta(r):
        sim0 = G.SIMULACAO
        try:
            G.SIMULACAO = False
            k = hoje()
        finally:
            G.SIMULACAO = sim0
        if r:
            fn(k[alvo])
        return k
    return monta


def c8_critico(fn):
    """O D e as fontes do cenário alarme-critico (§3.5; a constante CENARIO do gerador), com fn(D) quando r: a planta das janelas do mesmo id."""
    def monta(r):
        cen0 = G.CENARIO
        try:
            G.CENARIO = 'alarme-critico'
            k = hoje()
        finally:
            G.CENARIO = cen0
        if r:
            fn(k['D'])
        return k
    return monta


def c8_chave(campo, i, valor, janelas=True):
    """fn(D): a chave i (t = 5·i) do campo trocada no replay; as janelas derivadas de novo, como o gerador as deriva das chaves (JANELA, §1.16)."""
    def f(D):
        R = D['replay']
        R['chaves'][campo][i] = valor
        if janelas:
            R['janelas'] = C.deriva_janelas(R, D['campos'])
    return f


def c8_fonte(sufixo, fn):
    """hoje() com o texto da fonte que termina em `sufixo` trocado por fn(texto) quando r."""
    def monta(r):
        k = hoje()
        if r:
            rel = next(x for x in k['F'] if x.endswith(sufixo))
            k['F'][rel] = fn(k['F'][rel])
        return k
    return monta


def c8_leitura(k_F):
    rel = next(x for x in k_F if x.endswith('.json') and 'Leitura do coletor NMEA' in x)
    j = json.loads(k_F[rel])
    j.update({'lat': -26.993, 'lon': -48.614})
    k_F[rel] = json.dumps(j, ensure_ascii=False, indent=1) + '\n'


def c8_serie_com_posicao(k_F):
    k_F[next(x for x in k_F if x.endswith('.json') and 'Leitura do coletor NMEA' in x).rsplit('/', 1)[0] + '/Série com posição.csv'] = 'Hora;Latitude;Longitude\n07:00;-26,99;-48,61\n'


C8_PLANTAS = [
    ('LACO', 'leitura da pasta 05 com lat e lon no modo real (§4.3)', c8_real(c8_leitura), 'modo real: fontes/05 Telemetria — coletor NMEA/Leitura do coletor NMEA'),
    ('LACO', 'série da pasta 05 com colunas Latitude e Longitude no modo real (§4.3)', c8_real(c8_serie_com_posicao), 'Série com posição.csv: traz Latitude e Longitude'),
    ('LACO', 'coluna Origem no Formato do quadro do coletor',
     c8_fonte('Formato do quadro do coletor.csv', lambda t: t.replace('Casas decimais,Contador,Observação', 'Casas decimais,Origem,Contador,Observação', 1)),
     'a coluna «Origem» mostra a taxonomia interna'),
    ('LACO', 'valor da taxonomia interna (laço) numa célula do Formato do quadro',
     c8_fonte('Formato do quadro do coletor.csv', lambda t: t.replace('sog_nos,Velocidade sobre o fundo (SOG),nós,1,,', 'sog_nos,Velocidade sobre o fundo (SOG),nós,1,,laço', 1)),
     'o valor «laço» é da taxonomia interna'),
    ('LACO', 'campo do catálogo que o quadro do em() não tem (xyz)', c8_com(lambda D: D['campos'].update({'xyz': {'rotulo': 'Xyz', 'un': 'x', 'casas': 0, 'origem': 'rota'}})),
     'em(): o quadro não tem xyz, que está em D.campos'),
    ('LACO', 'campo do quadro fora do catálogo (wp_mn tirado de D.campos)', c8_com(lambda D: D['campos'].pop('wp_mn')), 'em(): o quadro tem wp_mn, que não está em D.campos'),
    ('LACO', 'snapshot.quadro com o porão em aviso (7 cm)', c8_com(lambda D: D['snapshot']['quadro'].update({'porao_bb_nivel': 7.0})),
     'snapshot.quadro.porao_bb_nivel = 7.0: nivel aviso'),
    ('LACO', 'replay sem as fases (§1.16)', c8_muda(('replay', 'fases')), 'replay sem fases (§1.16)'),
    ('LACO', 'rota e destinos com simulacao false (§4.3)', c8_muda(('simulacao',), False), 'modo real: D.rota e D.destinos só na simulação'),
    ('LACO', 'replay inteiro com simulacao false (§4.3)', c8_muda(('simulacao',), False), 'modo real: replay.chaves só na simulação'),
    ('LACO', 'posição no snapshot.quadro com simulacao false (§4.3)', c8_muda(('simulacao',), False), 'modo real: snapshot.quadro sem posição'),
    ('EMENDA_ROTA', 'uma chegada ao ponto numa emenda de 150 s (o fator da rota pelo menor desvio que a põe no par)', c8_com(c8_escala_ponteiro),
     'a chegada cai no par de segundos consecutivos (wp_proximo mudam)'),
    ('EMENDA_ROTA', 'contador que salta na emenda (a distância por volta dobrada)', c8_com(lambda D: D['replay']['por_volta'].update({'distancia_mn': 1.0816})), 'distancia_mn salta'),
    ('EMENDA_ROTA', 'a virada em A com a posição saltando (o mesmo fator trocado)', c8_com(c8_escala_ponteiro), 'virada em A: lat salta'),
    ('EMENDA_ROTA', 'circuitos_dia 20 (não é primo com as 576 voltas)', c8_muda(('rota', 'circuitos_dia'), 20), 'rota.circuitos_dia 20 não é primo com as 576 voltas do dia'),
    ('EMENDA_ROTA', 'rota sem pernas (o port do em() não roda)', c8_muda(('rota', 'pernas'), []), 'emendas de 150 s da rota: o port do em() não rodou'),
    ('ROTA', 'perna com a distância errada', c8_pernas(2, mn=3.5), 'rota.pernas[2].mn 3.5 ≠ a distância entre os pontos'),
    ('ROTA', 'perna com o rumo errado', c8_pernas(3, rumo=90.0), 'rota.pernas[3].rumo 90.0 ≠ o rumo entre os pontos'),
    ('ROTA', 'perna com o início errado', c8_pernas(4, ini_mn=7.0), 'rota.pernas[4].ini_mn 7.0 ≠ a soma das pernas anteriores'),
    ('ROTA', 'ida_mn errado', c8_muda(('rota', 'ida_mn'), 7.0), 'rota.ida_mn 7.0 ≠ a distância da base ao destino'),
    ('ROTA', 'distancia_mn diferente da soma das pernas', c8_muda(('rota', 'distancia_mn'), 15.0), 'rota.distancia_mn 15.0 ≠ a soma das pernas'),
    ('ROTA', 'fator acima de 1 (a posição andaria mais que o odômetro)', c8_muda(('rota', 'fator'), 1.02), 'rota.fator 1.02 fora de [0,9; 1,0]'),
    ('ROTA', 'perna de ordem trocada (de/para)', c8_pernas(1, de='laranjeiras'), 'rota.pernas[1] vai de'),
    ('ROTA', 'nome de ponto com dígito', c8_com(lambda D: D['rota']['pontos'][0].update({'nome': 'Ilha 2'})), 'rota.cabras.nome com dígito'),
    ('IDS', 'passo de alerta que o guia não tem', c8_com(lambda D: D['replay']['alertas']['arref_be']['passos'].__setitem__(0, 'Chame o rebocador.')),
     "replay.alertas.arref_be: o passo 'Chame o rebocador.' não está inteiro em"),
    ('IDS', 'alerta com seção que o guia não tem', c8_alerta('gerador', secao='12 · Carga'), "replay.alertas.gerador: o guia 'Guia de bordo — Gerador Onan' não tem a seção '12 · Carga'"),
    ('IDS', 'alerta com a fonte errada', c8_alerta('b12', fonte='Guia de bordo — Sistema elétrico 24 V e 12 V §9 · Faixas'), 'replay.alertas.b12.fonte'),
    ('IDS', 'alerta com guia fora de D.guias', c8_alerta('praca', guia='g_xyz'), "replay.alertas.praca.guia fora de D.guias: 'g_xyz'"),
    ('IDS', 'alerta de óleo com passos diferentes de protocolos.oleo', c8_alerta('oleo_be', passos=['Reduza para marcha lenta e confira o manômetro agora.']),
     'replay.alertas.oleo_be.passos ≠ protocolos.oleo'),
    ('IDS', 'alerta com campo fora do catálogo', c8_alerta('agua', campo='tanque_xyz'), "replay.alertas.agua.campo 'tanque_xyz' fora de D.campos ou de replay.limites"),
    ('DIA_DE_BORDO', 'litros diferentes do salto do contador entre A − 1 s e A', c8_com(lambda D: D['replay']['diaDeBordo']['abastecimento'].update({'litros': 1090})),
     'litros (1090) ≠ o salto do contador entre A − 1 s e A'),
    ('DIA_DE_BORDO', 'nivelDepois fora do modelo de 24 h', c8_com(lambda D: D['replay']['diaDeBordo']['abastecimento'].update({'nivelDepois': 96.0})),
     'nivelAntes/nivelDepois ≠ o diesel % de em(A − 1 s) e de em(A)'),
    ('NULO', 'snapshot.porao None (a pendência do C8 acabou)', c8_muda(('snapshot', 'porao'), None), 'snapshot.porao: None'),
    ('NULO', 'snapshot.ancora None', c8_muda(('snapshot', 'ancora'), None), 'snapshot.ancora: None'),
    # Revisão do C8 (JANELA, §6.3 «cada janela ⊂ [95, 120] e ≥ 10 s»): o C8 tinha afrouxado a regra para a UNIÃO das janelas do mesmo id (para caber
    # o aviso → crítico → aviso do §3.5), e um aviso partido em duas janelas curtas passava pela soma. No cenário aviso a regra é por janela; no
    # alarme-critico, janelas contíguas e a duração da união.
    ('JANELA', 'aviso partido em duas janelas curtas (o BE a 85,0 °C em t = 110: 99–106 = 8 s e 114–116 = 3 s; a união 99–116 passava)',
     c8_com(c8_chave('motor_be_arref_c', 22, 85.0)), 'precisa ficar em [95, 120] e durar ≥ 10 s (99–106)'),
    ('JANELA', 'aviso partido em 10 s + 4 s (o BE a 87,4 °C em t = 110: só a 2ª janela, 113–116, é curta)',
     c8_com(c8_chave('motor_be_arref_c', 22, 87.4)), 'precisa ficar em [95, 120] e durar ≥ 10 s (113–116)', True),
    ('JANELA', 'alarme-critico com o óleo BB voltando ao normal em t = 110 (as janelas do mesmo id deixam de ser contíguas: 106–108 e 112–114)',
     c8_critico(c8_chave('motor_bb_oleo_bar', 22, 3.0)), 'as janelas do mesmo id precisam ser contíguas (106–108 e 112–114)', True),
    # Revisão do C8 (JANELA e FIO, §6.3 «todo valor por segundo»): as duas só varriam os 150 s do laço, e os contadores (diesel e os três tanques) e a
    # profundidade da rota andam as 24 h do dia de bordo. Uma taxa por hora, um tanque de partida ou um ponto da rota mexidos passavam sem acusar nada
    # (o dado de hoje estava limpo, mas nada o segurava). Agora a varredura do dia (varredura_dia) avalia a nivel portada em cada segundo.
    ('JANELA', 'tanque de cinzas a 3,5 %/h (passa de 80 % às 03:35 do dia de bordo, sem janela)', c8_muda(('replay', 'taxas_h', 'tanque_cinzas_pct'), 3.5),
     'tanque_cinzas_pct = 80.1 às 03:35:09 do dia de bordo (aviso) fora das janelas', True),
    ('JANELA', 'tanque de água a -4,0 %/h (desce de 15 % às 02:15 e chega a negativo)', c8_muda(('replay', 'taxas_h', 'tanque_agua_pct'), -4.0),
     'tanque_agua_pct = 14.9 às 02:15:46 do dia de bordo (aviso) fora das janelas', True),
    ('JANELA', 'tanque de negras saindo da âncora com 75 % (passa de 80 % no meio da manhã)', c8_muda(('replay', 'contadores_base', 'tanque_negras_pct'), 75),
     'tanque_negras_pct = 80.1 às 12:36:40 do dia de bordo (aviso) fora das janelas', True),
    ('JANELA', 'diesel saindo da âncora com 600 L e piso de 100 L (cruza 400 L e depois 160 L: aviso e crítico)',
     c8_com(lambda D: (D['replay']['contadores_base'].__setitem__('diesel_litros', 600), D['replay'].__setitem__('diesel_piso_l', 100))),
     'diesel_litros = 399.0 às 11:26:03 do dia de bordo (aviso) fora das janelas'),
    ('JANELA', 'ponto da rota a 2,5 m de profundidade (a sonda desce de 3,0 m na perna)', c8_com(lambda D: D['rota']['pontos'][0].__setitem__('prof_m', 2.5)),
     'profundidade_m = 2.8 às 07:04:02 do dia de bordo (aviso) fora das janelas', True),
    ('FIO', 'diesel chegando ao piso de 400 L (1.560 → 900 L na âncora: o contador encosta no limite às 18:01)', c8_muda(('replay', 'contadores_base', 'diesel_litros'), 900),
     'diesel_litros = 400.0 às 18:01:58 do dia de bordo, a menos de 0,05 do limite 400', True),
    ('FIO', 'tanque de cinzas fechando o dia em 80,0 % (46,38 % na âncora: o último minuto encosta no limite sem passar)',
     c8_muda(('replay', 'contadores_base', 'tanque_cinzas_pct'), 46.38), 'tanque_cinzas_pct = 80.0 às 06:58:43 do dia de bordo, a menos de 0,05 do limite 80', True),
    # Revisão do C8 (§4.3 «o gerador recusa snapshot.gps enquanto o repositório for público»): a LACO só olhava o snapshot.quadro e as fontes.
    ('LACO', 'snapshot.gps com lat e lon no modo real (§4.3)', c8_real(lambda D: D['snapshot']['gps'].update({'lat': -26.993, 'lon': -48.614}), 'D'),
     'modo real: snapshot.gps sem lat, lon nem texto', True),
    ('LACO', 'snapshot.gps.texto no modo real (§4.3)', c8_real(lambda D: D['snapshot']['gps'].update({'texto': "26°59,58'S 048°36,84'W"}), 'D'),
     'modo real: snapshot.gps sem lat, lon nem texto', True),
    ('COORD_TEXTO', 'snapshot.gps.texto no modo real (a exceção do §1.17 é só da simulação)', c8_real(lambda D: D['snapshot']['gps'].update({'texto': "26°59,58'S 048°36,84'W"}), 'D'),
     'snapshot.gps.texto'),   # uma violação por ocorrência: a latitude e a longitude do texto são duas
]


def c8_rota_e_replay():
    print('C8 (CONTRATO §1.14–§1.17, §1.22, §3): rota, replay, campos, alertas, dia de bordo e snapshot sem null')
    k = hoje()
    D, R, rota, cam = k['D'], k['D']['replay'], k['D']['rota'], k['D']['campos']
    V = verifica(k)
    ok('o dado de hoje não acusa nada nas asserções do laço, da rota, do dia de bordo e do snapshot (%s)' % ', '.join(C8_REGRAS[:6] + ('…',)),
       all(not V[n] for n in C8_REGRAS), {n: V[n][:2] for n in C8_REGRAS if V[n]})
    ok('PENDENTES vazia: o snapshot sem null (porao e ancora objetos, volante com número) tirou as 4 pendências do C8',
       C.PENDENTES == {} and isinstance(D['snapshot']['porao'], dict) and isinstance(D['snapshot']['ancora'], dict)
       and D['snapshot']['seakeeper']['volante_rpm'] == 8420 and D['snapshot']['gerador']['kw'] == 5.6)
    # ——— a forma do §1.15 e do §1.16
    ok('D.campos: 66 campos, ordem do §1.22, origem em 7 valores, sentido só (e sempre) nos 8 contadores (+1 em horímetros, distância e servidas; −1 em diesel e água)',
       len(cam) == 66 and list(cam)[:3] == ['timestamp_utc', 'lat', 'lon'] and list(cam)[-3:] == ['wp_mn', 'eta', 'alarmes'] and set(c['origem'] for c in cam.values()) == C.ORIGENS
       and {c for c, d in cam.items() if 'sentido' in d} == set(R['contadores_base'])
       and {c: d['sentido'] for c, d in cam.items() if 'sentido' in d} == {'motor_bb_horimetro_h': 1, 'motor_be_horimetro_h': 1, 'gerador_horimetro_h': 1, 'distancia_mn': 1,
                                                                          'tanque_cinzas_pct': 1, 'tanque_negras_pct': 1, 'diesel_litros': -1, 'tanque_agua_pct': -1}
       and 'simulado' not in cam, (len(cam), sorted(set(c['origem'] for c in cam.values()))))
    ok('D.replay: duracao 150, passo 1, passo_chave 5, cenario aviso, ancora_hora 07:00, voltas_fixo 120, 5 fases, 28 chaves de 30 quadros, 11 fixos, 8 contadores_base, 3 taxas',
       [R[c] for c in ('duracao', 'passo', 'passo_chave', 'cenario', 'ancora_hora', 'voltas_fixo')] == [150, 1, 5, 'aviso', '07:00', 120] and len(R['fases']) == 5
       and len(R['chaves']) == 28 and all(len(v) == 30 for v in R['chaves'].values()) and len(R['fixos']) == 11 and len(R['contadores_base']) == 8 and len(R['taxas_h']) == 3
       and [f['nome'] for f in R['fases']] == ['marcha lenta', 'aceleração', 'cruzeiro', 'redução', 'marcha lenta'] and R['limites'] == G.LIMITES, list(R))
    ok('D.replay.ruido: [amplitude, semente] de cada chave (sementes 1100 + a posição) e da proa e da profundidade (1201 e 1202)',
       all(R['ruido'][c] == [G.AMPLITUDE_RUIDO[c], 1100 + i] for i, c in enumerate(G.ORDEM_LACO)) and R['ruido']['proa_graus'] == [0.4, 1201] and R['ruido']['profundidade_m'] == [0.2, 1202])
    ok('D.replay.por_volta e por_dia: 1,8857 L (1,7899 + 0,0958) e 0,5408 mn por volta; 576 voltas = 1.086,2 L e 311,5 mn por dia; 1.560 − 1.086,2 ≥ o piso (400) + 50',
       R['por_volta'] == {'diesel_l': 1.8857, 'motores_l': 1.7899, 'gerador_l': 0.0958, 'distancia_mn': 0.5408, 'motor_h': 0.041667, 'gerador_h': 0.041667}
       and R['por_dia'] == {'voltas': 576, 'diesel_l': 1086.2, 'distancia_mn': 311.5, 'motor_h': 24, 'gerador_h': 24} and R['diesel_piso_l'] == 400, (R['por_volta'], R['por_dia']))
    ok('D.replay.janelas derivadas pelo gerador: uma só, arref_be (motor_be_arref_c) em aviso de 99 a 116 s',
       R['janelas'] == [{'id': 'arref_be', 'campo': 'motor_be_arref_c', 'nivel': 'aviso', 'ini': 99, 'fim': 116}], R['janelas'])
    # Revisão do C8: JANELA e FIO varrem as 24 h do dia de bordo (varredura_dia) nos 5 campos de limite que o laço de 150 s não cobre; hoje todos no normal
    P, erro_p = C.Ctx(D, {}, {}, {}).port()
    dia = C.varredura_dia(P)['limites'] if P else {}
    ok('JANELA e FIO varrem o dia de bordo inteiro (86.400 s) em diesel_litros, profundidade_m e nos três tanques: nenhum aviso nem crítico, nenhum valor a menos de 0,05 de um limite',
       sorted(dia) == ['diesel_litros', 'profundidade_m', 'tanque_agua_pct', 'tanque_cinzas_pct', 'tanque_negras_pct']
       and all(not d['niveis'] and d['perto'] is None for d in dia.values()) and R['duracao'] * R['por_dia']['voltas'] == 86400, (erro_p, dia))
    al = R['alertas']
    ok('D.replay.alertas: 21 ids do §1.16, cada um com campo, sistema, título, guia, seção, passos e fonte; óleo = protocolos.oleo; arref_be com os 3 passos do §5',
       list(al) == ['arref_bb', 'arref_be', 'oleo_bb', 'oleo_be', 'rpm_bb', 'rpm_be', 'carga_bb', 'carga_be', 'praca', 'b24s', 'b24p', 'b12', 'porao_bb', 'porao_be', 'profundidade',
                    'diesel', 'gerador', 'seakeeper', 'agua', 'cinzas', 'negras'] and all(set(a) >= {'campo', 'sistema', 'titulo', 'guia', 'secao', 'passos', 'fonte'} for a in al.values())
       and al['oleo_bb']['passos'] == al['oleo_be']['passos'] == D['protocolos']['oleo'] and len(al['arref_be']['passos']) == 3
       and al['arref_be']['fonte'] == 'Guia de bordo — Motores Cummins §5 · Temperatura alta' and al['arref_be']['lado'] == 'be' and 'lado' not in al['praca'], list(al))
    # Revisão do C8: os passos do alerta de porão (aviso e crítico) mandam procurar a entrada de água e escalar para o SOS do app, como o
    # protocolos.alagamento; sem número, MMSI nem posição; o trecho do guia que os repete (§2 · Faixas) leva seguranca: true e nunca vai à IA.
    pp = al['porao_bb']['passos']
    t_porao2 = next(t for t in k['B']['trechos'] if t['fonte'] == G.ARQ['g_porao'] and t['secao'].startswith('2 · '))
    ok('D.replay.alertas.porao_bb/porao_be: os mesmos passos, com «procure a entrada de água» e a escalada «use o SOS do app», sem dígito; o §2 · Faixas do guia leva seguranca e os passos inteiros',
       pp == al['porao_be']['passos'] and any(p.lower().startswith('procure a entrada') for p in pp) and any('alagamento' in p and 'SOS do app' in p for p in pp)
       and not any(re.search(r'\d', p) for p in pp) and t_porao2.get('seguranca') is True and all(C._palavras(p) in C._palavras(t_porao2['texto']) for p in pp),
       (pp, t_porao2))
    ok('D.consumo: lenta 5 nós · 700 rpm · 6,2 L/h, máxima 26 nós · 2.600 rpm · 111 L/h, gerador 2,3 L/h, 5 faixas de rpm, margem de manobra de 60 L e a fonte do guia §10',
       D['consumo']['lenta'] == {'nos': 5, 'rpm': 700, 'lph': 6.2} and D['consumo']['maxima'] == {'nos': 26, 'rpm': 2600, 'lph': 111} and D['consumo']['gerador_lph'] == 2.3
       and [f['nome'] for f in D['consumo']['faixas']] == ['marcha lenta', 'deslocamento', 'transição', 'planeio', 'cruzeiro'] and D['consumo']['margemManobra_l'] == 60
       and D['consumo']['fonte'] == 'Guia de bordo — Motores Cummins §10 · Consumo', D['consumo'])
    # ——— a rota (§1.14, §2.6)
    ids = [rota['base']['id']] + [p['id'] for p in rota['pontos']]
    ok('D.rota: base + 7 pontos na ordem do circuito, 8 pernas pré-calculadas (mn, rumo, ini_mn), destino Estaleirinho, 19 circuitos e fator ≤ 1',
       ids == ['base', 'cabras', 'laranjeiras', 'taquaras', 'estaleirinho', 'pinho', 'laranjeiras_v', 'cabras_v'] and len(rota['pernas']) == 8 and rota['circuitos_dia'] == 19
       and rota['destino']['id'] == 'estaleirinho' and 0.9 <= rota['fator'] <= 1.0 and rota['guinada_max_gps'] == 3 and rota['corrente'] == {'nos': 0.3, 'para_graus': 200}
       and abs(rota['distancia_mn'] - sum(p['mn'] for p in rota['pernas'])) < 1e-3, (rota['distancia_mn'], rota['fator']))
    ok('D.destinos: Ilha das Cabras, Ponta das Laranjeiras, Taquaras e Estaleirinho, com a distância pela rota a partir da base',
       [d['nome'] for d in D['destinos']] == ['Ilha das Cabras', 'Ponta das Laranjeiras', 'Taquaras', 'Estaleirinho']
       and [d['mn'] for d in D['destinos']] == sorted(d['mn'] for d in D['destinos']) and D['destinos'][-1]['mn'] == round(rota['ida_mn'], 1), D['destinos'])
    # Revisão do C8: os dois pontos «Ilha das Cabras» tinham ido a 1,6 mn da ilha (a distância de terra é do portão manual, sem teste automático, §2.6);
    # aqui só o NOME: a ilha (polígono 127530 da costa GSHHG cheia, centro -26,9903 / -48,6270) a menos de 1,2 mn de cada ponto que a nomeia.
    ilha = (-26.9903, -48.6270)
    dist_ilha = {p['id']: C.mn_entre(ilha, (p['lat'], p['lon'])) for p in rota['pontos'] if p['nome'] == 'Ilha das Cabras'}
    ok('D.rota: os dois pontos «Ilha das Cabras» ficam ao largo dela (menos de 1,2 mn do centro da ilha: %s)' % {i: round(d, 2) for i, d in dist_ilha.items()},
       sorted(dist_ilha) == ['cabras', 'cabras_v'] and all(d < 1.2 for d in dist_ilha.values()), dist_ilha)
    ok('as coordenadas só em campo numérico (rota e quadro): nenhum texto do D, da base e das fontes tem lat/lon (a única exceção é snapshot.gps.texto)',
       not V['COORD_TEXTO'], V['COORD_TEXTO'][:2])
    # ——— o em() portado contra os números do §1.22 (laço, contadores e tanques; a rota é a do portão manual)
    P = C.preparar(D)
    q60, q105 = C.em(P, S60), C.em(P, S105)
    difs = {c: (q60.get(c), v) for c, v in C8_LACO_60.items() if q60.get(c) != v}
    difs.update({c + '@105': (q105.get(c), v) for c, v in C8_LACO_105.items() if q105.get(c) != v})
    ok('em(): 12:01:00 e 12:01:45 = os valores do §1.22 (laço, contadores e tanques: %d campos), com o AVISO do BE só em t = 105' % (len(C8_LACO_60) + len(C8_LACO_105)),
       not difs and q60['alarmes'] == [] and q105['alarmes'] == [C8_ALARME_105], difs)
    # Revisão do C8 (Ilha das Cabras): com os pontos «Ilha das Cabras» e «Laranjeiras» refeitos no portão (a ilha a 0,9 mn, não a 1,6), a última perna
    # do circuito ficou mais curta e, às 12:01:00, o ponto nomeado mais perto é o cabras_v: o `local` é o `perto` dele, com o caminho da barra.
    # A ETA (12:03) e o destino não mudam.
    ok('em(): o timestamp, o estado e a ETA: 12:01:00 → 15:01:00Z; a chegada à base às 12:03 (última perna do circuito, a caminho da barra, ao largo da ilha)',
       q60['timestamp_utc'] == '2026-09-26T15:01:00Z' and q60['destino'] == 'Barra Sul (base)' and q60['eta'] == '12:03' and q105['eta'] == '12:03'
       and q60['local'] == 'ao largo da Ilha das Cabras, a caminho da Barra Sul' and q60['wp_proximo'] == 'Barra Sul (saída do Rio Camboriú)', {c: q60[c] for c in ('destino', 'eta', 'local', 'wp_proximo')})
    a0, a1 = C.em(P, 86399), C.em(P, 0)
    ok('em(): a virada 06:59:59 → 07:00:00: 474 L (29,6 %), 311,5 mn, horímetros 436,6 · 433,8 · 1.260,4, tanques 63,2 · 41,6 · 26,6, destino a 0,0 mn e ETA 07:00',
       all(a0[c] == v for c, v in C8_A_ANTES.items()), {c: (a0[c], v) for c, v in C8_A_ANTES.items() if a0[c] != v})
    ok('em(): às 07:00:00 o dia recomeça: 1.560 L (97,5 %), horímetros 412,6 · 409,8 · 1.236,4, tanques 92 · 8 · 5, destino Estaleirinho e o próximo ponto Ilha das Cabras; a posição é a da base',
       all(a1[c] == v for c, v in C8_A_DEPOIS.items()) and (a1['lat'], a1['lon']) == (rota['base']['lat'], rota['base']['lon']), {c: (a1[c], v) for c, v in C8_A_DEPOIS.items() if a1[c] != v})
    ok('em(): o quadro tem exatamente os campos do D.campos (66) e nenhum valor None nem NaN', list(q60) == list(cam) and not [c for c, v in q60.items() if v is None or v != v], list(q60)[:3])
    # ——— as 575 emendas e a virada em A (EMENDA_ROTA): nenhuma chegada cai no par de segundos consecutivos
    VD = C.varredura_dia(P)
    folga = min(min(s % 150, 150 - s % 150) for s, _ in VD['eventos'])
    ok('EMENDA_ROTA: %d chegadas e trocas de destino no dia (151 pontos e 37 destinos), nenhuma numa das 575 emendas de 150 s (menor folga: %d s) e os passos de 1 s nelas dentro do maior do dia'
       % (len(VD['eventos']), folga), len(VD['eventos']) >= 180 and folga >= 1 and not V['EMENDA_ROTA'] and len(VD['emendas']) == 575, (len(VD['eventos']), folga))
    # ——— o dia de bordo (§1.8–§1.10)
    B = R['diaDeBordo']
    ok('replay.diaDeBordo: 3 dias, abastecimento das 07:00 (1.086 L, 29,6 → 97,5 %), a nota fiscal CONFERIDA com ref ab-0 e d01 e d02 (4 pessoas a bordo; 1.086 L)',
       B['dias'] == 3 and B['abastecimento']['h'] == '07:00' and B['abastecimento']['litros'] == 1086 and (B['abastecimento']['nivelAntes'], B['abastecimento']['nivelDepois']) == (29.6, 97.5)
       and B['documento'] == {'id': 'nf-abast', 'n': 'Nota fiscal do abastecimento', 'cat': 'Notas', 'emitidoHa': 0, 'st': 'CONFERIDA', 'ref': 'ab-0',
                              'nota': 'abastecimento das 07:00 · sem valores no app', 'fonte': D['docsFonte']}
       and [x['id'] for x in B['diario']] == ['d01', 'd02'] and '4 pessoas a bordo' in B['diario'][0]['t'] and '1.086 L de diesel' in B['diario'][1]['t']
       and '97,5 %' in B['diario'][1]['t'] and B['diario'][1]['ref'] == 'ab-0', B['abastecimento'])
    ok('o arquivo gerado não traz o dia de bordo: abastecimentos [], diário só d03–d09, 7 documentos sem a nota fiscal (a microtarefa do rodapé insere, só com simulacao: true)',
       D['abastecimentos'] == [] and [x['id'] for x in D['diario']] == ['d03', 'd04', 'd05', 'd06', 'd07', 'd08', 'd09'] and len(D['documentos']) == 7
       and not any(d['cat'] == 'Notas' for d in D['documentos']))
    # ——— o snapshot sem null (§1.17)
    sq = D['snapshot']['quadro']
    ok('snapshot.quadro: 59 campos do catálogo (sem piloto, destino, distância e ETA, próximo ponto nem alarmes), Fundeado, motores parados, 848 L = (54 + 52) × 8, ancora_estado lançada',
       len(sq) == 59 and not {'piloto_rumo', 'destino', 'destino_mn', 'wp_proximo', 'wp_mn', 'eta', 'alarmes'} & set(sq) and sq['estado'] == 'Fundeado' and sq['marcha'] == 'neutro'
       and sq['motor_bb_rpm'] == sq['motor_be_rpm'] == 0 and sq['diesel_litros'] == (sq['diesel_bb_pct'] + sq['diesel_be_pct']) * 8 == 848 and sq['ancora_estado'] == 'lançada'
       and sq['seakeeper_volante_rpm'] == 8420, (len(sq), sorted(set(cam) - set(sq))))
    ok('o D.snapshot.quadro e o aninhado dizem o mesmo (horímetros, tanques, porão, vento, ar, água, satélites, posição)',
       (sq['motor_bb_horimetro_h'], sq['motor_be_horimetro_h'], sq['gerador_horimetro_h']) == (412.6, 409.8, 1236.4)
       and (sq['tanque_agua_pct'], sq['tanque_cinzas_pct'], sq['tanque_negras_pct']) == tuple(D['snapshot']['tanques'][c] for c in ('agua', 'cinzas', 'negras'))
       and (sq['porao_bb_nivel'], sq['porao_be_nivel']) == (D['snapshot']['porao']['bb_cm'], D['snapshot']['porao']['be_cm']) and sq['vento_verdadeiro_nos'] == D['snapshot']['vento']
       and (sq['lat'], sq['lon']) == (D['snapshot']['gps']['lat'], D['snapshot']['gps']['lon']) and sq['gps_satelites'] == D['snapshot']['gps']['satelites'])
    # ——— as fontes do Drive (pasta 05, 06, 04)
    F = k['F']
    serie = next(t for r, t in F.items() if r.endswith('Série do coletor NMEA — 150 s.csv'))
    linhas = serie.strip().split('\n')
    formato = next(t for r, t in F.items() if r.endswith('Formato do quadro do coletor.csv'))
    ok('pasta 05: a série de 150 s (t_s 0–149 + os 28 campos do laço, sem data, lat nem lon) e o formato do quadro (um campo por linha, 66)',
       len(linhas) == 151 and linhas[0].split(';') == ['t_s'] + [c for c in cam if c in R['chaves']] and linhas[1].split(';')[0] == '0' and linhas[150].split(';')[0] == '149' and all(len(l.split(';')) == 29 for l in linhas)
       and not {'lat', 'lon', 'timestamp_utc'} & set(linhas[0].split(';')) and len(formato.strip().split('\n')) == 67
       # revisão do C8: sem a coluna Origem (laço, rota, janela… é a taxonomia interna do D.campos; o coletor NMEA real não a tem)
       and formato.startswith('Campo,Rótulo,Unidade,Casas decimais,Contador,Observação\n') and not (set(C.ORIGENS) & {c for l in formato.split('\n') for c in l.split(',')}), linhas[:2])
    aba = next(t for r, t in F.items() if r.endswith('Registro de abastecimento.csv'))
    dia = next(t for r, t in F.items() if r.endswith('Diário de bordo.csv'))
    ok('pastas 06 e 04: o abastecimento tem os 3 dias de bordo (0, 1 e 2) com 1.086 L e o diário traz a d01 e a d02 do dia de bordo antes das fixas',
       len(aba.strip().split('\n')) == 4 and aba.count('1.086') == 3 and '\n0,07:00,' in aba and dia.split('\n')[1].startswith('0,07:00,Navegação') and dia.split('\n')[2].startswith('0,07:00,Combustível'), (aba[:200], dia[:300]))
    # revisão do C8 (nivelDepois): o CSV do abastecimento em pt-BR nos dois números da linha, litros «1.086» e nível «97,5» (o nível saía «97.5» ao lado de «1.086»)
    linhas_aba = list(csv.reader(io.StringIO(aba)))
    ok('pasta 06: cada linha do abastecimento traz litros «1.086» e nível depois «97,5» (pt-BR nos dois), sem «97.5»',
       len(linhas_aba) == 4 and all(len(l) == 8 for l in linhas_aba) and all((l[2], l[5]) == ('1.086', '97,5') for l in linhas_aba[1:]) and '97.5' not in aba, linhas_aba[:2])
    # ——— plantas
    for nome, o_que, monta, espera, *so in C8_PLANTAS:
        planta(nome, ' — C8: ' + o_que, monta, espera, so_uma=bool(so and so[0]))
    # ——— modo real: o gerador não emite rota, destinos, o replay inteiro nem a posição do quadro (§4.3)
    sim0 = G.SIMULACAO
    try:
        G.SIMULACAO = False
        Dr = G.dados()
        Fr = G.gera_fontes(Dr)
        Vr = C.verifica(Dr, G.base_conhecimento(), Fr, G.saidas(Dr, G.base_conhecimento()), None, None, None, None, CONST)
    finally:
        G.SIMULACAO = sim0
    ok('SIMULACAO = False: o D sai sem rota, destinos, chaves, janelas nem dia de bordo (replay só com limites e alertas), o snapshot.quadro sem lat/lon e nenhuma violação estrutural',
       'rota' not in Dr and 'destinos' not in Dr and list(Dr['replay']) == ['limites', 'alertas'] and 'lat' not in Dr['snapshot']['quadro'] and 'lat' not in Dr['snapshot']['gps']
       and Dr['simulacao'] is False and not {n: v for n, v in Vr.items() if v and n != 'TERMOS'}, {n: v[:2] for n, v in Vr.items() if v and n != 'TERMOS'})
    # Revisão do C8: o D já saía sem posição no modo real, mas a leitura da pasta 05 (arquivo do repositório público) levava lat/lon do SNAPSHOT cru
    leitura_r = next((json.loads(t) for r, t in Fr.items() if r.endswith('.json') and 'Leitura do coletor NMEA' in r), None)
    leitura_s = next(json.loads(t) for r, t in k['F'].items() if r.endswith('.json') and 'Leitura do coletor NMEA' in r)
    ok('SIMULACAO = False: a leitura da pasta 05 sai sem lat/lon (o resto igual à da simulação), nenhuma fonte do Drive tem chave nem coluna de posição, e a série e o formato do quadro não são emitidos',
       leitura_r is not None and not POSICAO_KEYS & set(leitura_r) and {c: v for c, v in leitura_s.items() if c not in ('lat', 'lon')} == leitura_r
       and POSICAO_KEYS <= set(leitura_s) and not C.posicao_nas_fontes(Fr) and not [r for r in Fr if r.endswith('Série do coletor NMEA — 150 s.csv') or r.endswith('Formato do quadro do coletor.csv')],
       (leitura_r, C.posicao_nas_fontes(Fr)))
    ok('SIMULACAO = True: a leitura da pasta 05 continua com lat e lon numéricos (§1.17), a série vai sem posição e nenhuma planilha da pasta 05 mostra a taxonomia interna',
       isinstance(leitura_s['lat'], float) and isinstance(leitura_s['lon'], float) and not C.formato_sem_taxonomia(C.Ctx(D, {}, k['F'], {}))
       and not [m for m in C.posicao_nas_fontes(k['F']) if 'Leitura' not in m], C.formato_sem_taxonomia(C.Ctx(D, {}, k['F'], {})))
    # ——— o cenário alarme-critico (§3.5): só mudando a constante; o óleo BB ganha aviso → crítico → aviso dentro de 95–120 s
    cen0 = G.CENARIO
    try:
        G.CENARIO = 'alarme-critico'
        Dc = G.dados()
        Vc = C.verifica(Dc, G.base_conhecimento(), G.gera_fontes(Dc), G.saidas(Dc, G.base_conhecimento()), None, None, None, None, CONST)
    finally:
        G.CENARIO = cen0
    jc = [(j['id'], j['nivel'], j['ini'], j['fim']) for j in Dc['replay']['janelas']]
    ok('cenário alarme-critico (desligado): o óleo BB cai a 1,1 bar (aviso → crítico → aviso, id oleo_bb), o aviso do BE continua e nenhuma asserção estrutural reprova',
       Dc['replay']['cenario'] == 'alarme-critico' and [j[1] for j in jc if j[0] == 'oleo_bb'] == ['aviso', 'critico', 'aviso'] and ('arref_be', 'aviso', 99, 116) in jc
       and all(95 <= j[2] and j[3] <= 120 for j in jc) and not {n: v for n, v in Vc.items() if v and n != 'TERMOS'}, (jc, {n: v[:2] for n, v in Vc.items() if v and n != 'TERMOS'}))
    ok('o cenário aviso (o de hoje) não emite nada do crítico: nenhuma janela crítica e nenhum óleo abaixo de 2,4 bar a partir de 1.000 rpm',
       not [j for j in R['janelas'] if j['nivel'] == 'critico'] and min(R['chaves']['motor_bb_oleo_bar']) >= 2.8)


# ——————————————————————————————— C9: histórico (CONTRATO §1.13) ———————————————————————————————
C9_DESVIOS = {'vento_verdadeiro_nos': (10, 40), 'pressao_barometrica_hpa': (10, 70), 'bateria_0_tensao_v': (100, 6), 'bateria_1_tensao_v': (100, 6),
              'bateria_2_tensao_v': (100, 6), 'temp_ar_externo_c': (10, 15), 'temp_agua_c': (10, 4)}   # campo: (escala, pico do contrato em d)
C9_METRICAS = {'b24': ['bateria_0_tensao_v', 'bateria_1_tensao_v'], 'b12': ['bateria_2_tensao_v'], 'tanques': ['tanque_agua_pct', 'tanque_cinzas_pct', 'tanque_negras_pct'],
               'vento': ['vento_verdadeiro_nos'], 'pressao': ['pressao_barometrica_hpa'], 'diesel': ['diesel_litros'],
               'temperaturas': ['temp_praca_maquinas_c', 'temp_ar_externo_c', 'temp_agua_c'], 'motores': ['motor_bb_rpm', 'motor_be_rpm'],
               'oleo': ['motor_bb_oleo_bar', 'motor_be_oleo_bar'], 'arref': ['motor_bb_arref_c', 'motor_be_arref_c'], 'navegacao': ['sog_nos', 'stw_nos'],
               'consumo': ['consumo_lph']}   # a literal do §1.13, escrita de novo aqui (nunca lida do gerador)
C9_JANELAS = {'150S': {'passo_s': 1, 'n': 150}, '1D': {'passo_s': 900, 'n': 96}, '7D': {'passo_s': 3600, 'n': 168}, '30D': {'passo_s': 21600, 'n': 120},
              '1A': {'passo_s': 86400, 'n': 365}}


def c9_d():
    """O D de hoje (cópia funda), sem fontes nem base: para as plantas leves da HISTORICO (a asserção roda sozinha, em milissegundos)."""
    return copy.deepcopy(G.dados())


def c9_ctx(D):
    return C.Ctx(D, {}, {}, {})


def c9_planta(o_que, muda, espera, so_uma=False):
    """HISTORICO: a amostra plantada aparece como violação nova (e, com `so_uma`, é a ÚNICA). A HISTORICO é estrutural: reprova o gerador."""
    bom, D = C.a_historico(c9_ctx(c9_d())), c9_d()
    muda(D)
    novos = [m for m in C.a_historico(c9_ctx(D)) if m not in bom]
    ok('HISTORICO: acusa a amostra plantada — C9: %s%s' % (o_que, ' (uma violação só)' if so_uma else ''),
       any(espera in m for m in novos) and (not so_uma or len(novos) == 1) and 'HISTORICO' not in C.RELATORIO, {'novas': novos[:3]})


def c9_hist(D):
    return D['historico']


def c9_d_de(campo, i, valor):
    return lambda D: D['historico']['desvios'][campo]['d'].__setitem__(i, valor)


def c9_serie(D, i, **kw):
    D['serie24v'][i].update(kw)


def c9_historico():
    print('C9 (CONTRATO §1.13): histórico (desvios, curva do ano, cruzeiro, janelas) e a série 24 V')
    k = hoje()
    D = k['D']
    H = D['historico']
    V = verifica(k)
    ok('o dado de hoje não acusa nada na HISTORICO, na TAMANHO nem na NULO, e a PENDENTES continua vazia',
       not V['HISTORICO'] and not V['TAMANHO'] and not V['NULO'] and C.PENDENTES == {}, {n: V[n][:2] for n in ('HISTORICO', 'TAMANHO', 'NULO') if V[n]})
    ok('a forma do §1.13: fim «ancora», um desvio a cada 2 dias (n = 183: de 366 a 2 dias atrás), os 7 campos de desvio e a fonte',
       list(H) == ['fim', 'passo_dias', 'n', 'desvios', 'sazonal', 'cruzeiro', 'janelas', 'metricas', 'so150', 'fonte'] and H['fim'] == 'ancora'
       and (H['passo_dias'], H['n']) == (2, 183) and list(H['desvios']) == list(C9_DESVIOS) and H['fonte'] == 'coletor NMEA de bordo · histórico', list(H))
    ok('cada desvio: inteiros, 183 pontos, a escala do contrato (10, 10, 100 ×3, 10, 10) e o pico exatamente na amplitude (±40 = 4 nós, ±70 = 7 hPa, ±6 = 0,06 V, ±15 = 1,5 °C, ±4 = 0,4 °C)',
       all(s['escala'] == C9_DESVIOS[c][0] and len(s['d']) == 183 and all(type(x) is int for x in s['d']) and max(abs(x) for x in s['d']) == C9_DESVIOS[c][1]
           and len(set(s['d'])) > 8 for c, s in H['desvios'].items()), {c: (s['escala'], len(s['d']), min(s['d']), max(s['d'])) for c, s in H['desvios'].items()})
    sz = H['sazonal']
    ok('a curva do ano: passo de 5 dias, 73 pontos, ar ±4,5 °C (máximo em meados de janeiro, mínimo em meados de julho) e água ±3,5 °C (fevereiro e agosto), em décimos',
       (sz['passo_dias'], sz['n']) == (5, 73) and list(sz) == ['passo_dias', 'n', 'temp_ar_externo_c', 'temp_agua_c']
       and max(sz['temp_ar_externo_c']['d']) == 45 and min(sz['temp_ar_externo_c']['d']) == -45 and max(sz['temp_agua_c']['d']) == 35 and min(sz['temp_agua_c']['d']) == -35
       and 5 * sz['temp_ar_externo_c']['d'].index(45) in range(5, 25) and 5 * sz['temp_ar_externo_c']['d'].index(-45) in range(170, 215)
       and 5 * sz['temp_agua_c']['d'].index(35) in range(30, 60) and 5 * sz['temp_agua_c']['d'].index(-35) in range(200, 240)
       and all(len(sz[c]['d']) == 73 for c in ('temp_ar_externo_c', 'temp_agua_c')), {c: sz[c]['d'][:6] for c in ('temp_ar_externo_c', 'temp_agua_c')})
    ok('a curva do ano fecha o ciclo (o ponto 73 seria o 1º de janeiro de novo): a diferença entre o último e o primeiro ponto é um passo da curva, sem salto',
       all(abs(sz[c]['d'][0] - sz[c]['d'][-1]) <= 3 for c in ('temp_ar_externo_c', 'temp_agua_c')), {c: (sz[c]['d'][0], sz[c]['d'][-1]) for c in ('temp_ar_externo_c', 'temp_agua_c')})
    cz = H['cruzeiro']
    ok('o cruzeiro (F11): 60 dias, BB em 82,0 ± 0,2 °C, BE subindo de ~82,4 a ~83,9 °C e o óleo ao redor de 3,9 e 3,8 bar',
       cz['dias'] == 60 and list(cz) == ['dias', 'motor_bb_arref_c', 'motor_be_arref_c', 'motor_bb_oleo_bar', 'motor_be_oleo_bar']
       and all(len(cz[c]['d']) == 60 and all(type(x) is int for x in cz[c]['d']) for c in list(cz)[1:]) and (cz['motor_bb_arref_c']['escala'], cz['motor_bb_oleo_bar']['escala']) == (10, 100)
       and 818 <= min(cz['motor_bb_arref_c']['d']) and max(cz['motor_bb_arref_c']['d']) <= 822 and 823 <= cz['motor_be_arref_c']['d'][0] <= 826
       and 837 <= cz['motor_be_arref_c']['d'][-1] <= 840 and 387 <= min(cz['motor_bb_oleo_bar']['d']) and max(cz['motor_bb_oleo_bar']['d']) <= 393
       and 377 <= min(cz['motor_be_oleo_bar']['d']) and max(cz['motor_be_oleo_bar']['d']) <= 383, {c: (cz[c]['d'][0], cz[c]['d'][-1]) for c in list(cz)[1:]})
    Q = [C.quadro_laco(D['replay'], D['campos'], t) for t in range(150)]
    f = next(x for x in D['replay']['fases'] if x['nome'] == 'cruzeiro')
    mb, me = [sum(q[c] for q in Q[f['ini']:f['fim']]) / (f['fim'] - f['ini']) for c in ('motor_bb_arref_c', 'motor_be_arref_c')]
    ok('o achado da F11 (§1.13): hoje, pelo laço na fase de cruzeiro, o BE está 2,5 °C acima do BB (84,5 contra 82,0), e a série sobe até ontem sem passar de hoje',
       round(me, 1) == 84.5 and round(mb, 1) == 82.0 and round(me - mb, 1) == 2.5 and (cz['motor_be_arref_c']['d'][-1] - cz['motor_bb_arref_c']['d'][-1]) / 10 < me - mb, (me, mb))
    ok('as janelas e os grupos do contrato, escritos de novo aqui: 150S (1 s × 150), 1D (900 s × 96), 7D, 30D, 1A, os 12 grupos de métricas e os 5 grupos só do laço (so150)',
       H['janelas'] == C9_JANELAS and H['metricas'] == C9_METRICAS and H['so150'] == ['motores', 'oleo', 'arref', 'navegacao', 'consumo'], H['janelas'])
    ok('todo campo das métricas está no D.campos e nenhum grupo é de maré nem de previsão (tempo e maré são sempre os reais)',
       all(c in D['campos'] for cs in H['metricas'].values() for c in cs) and not [g for g in H['metricas'] if 'mare' in g or 'previs' in g], '')
    # ——— a série 24 V (L): mín/máx da volta + o desvio do dia, calculado à mão aqui (sem C.desvio_em)
    sv, d = D['serie24v'], H['desvios']['bateria_0_tensao_v']['d']
    vs = [q['bateria_0_tensao_v'] for q in Q]
    vmin, vmax = min(vs), max(vs)
    dev = {0: 0, 1: d[182] / 2, 2: d[182], 3: (d[181] + d[182]) / 2, 4: d[181], 5: (d[180] + d[181]) / 2, 6: d[180]}   # centésimos de volt, 1 a 7 dias atrás
    ok('serie24v: 7 dias (6…0) com o mín/máx da volta do banco de serviço (27,28 a 27,82 V) mais o desvio do dia (os pontos de 2 em 2 dias e a média dos vizinhos), e o d de cada dia',
       [x['diasAtras'] for x in sv] == list(range(6, -1, -1)) and (vmin, vmax) == (27.28, 27.82) and (sv[-1]['min'], sv[-1]['max']) == (27.28, 27.82)
       and all(abs(x['min'] - (vmin + dev[x['diasAtras']] / 100)) <= 0.0051 and abs(x['max'] - (vmax + dev[x['diasAtras']] / 100)) <= 0.0051 for x in sv)
       and [x['d'] for x in sv] == [G.dia_ddmm(-x) for x in range(6, -1, -1)] and len({x['min'] for x in sv}) >= 3, (sv, dev))
    ok('serie24v: a semana varia (mín e máx andam juntos, 0,04 V de ponta a ponta) e fica dentro do normal do banco (24,4 a 29,4 V)',
       max(x['max'] for x in sv) - min(x['max'] for x in sv) >= 0.03 and all(24.45 <= x['min'] < x['max'] <= 29.35 for x in sv), sv)
    # ——— a interpolação de referência (o port que o cliente da Fase 2 repete): d[0] a 366 dias, d[182] a 2 dias, 0 hoje, linear entre os pontos
    e = H['desvios']['temp_ar_externo_c']['escala']
    da = H['desvios']['temp_ar_externo_c']['d']
    ok('desvio_em: 0 hoje (o último ponto de toda série é o quadro), d[182] a 2 dias, a metade a 1 dia, d[0] a 366 dias, a média dos dois primeiros a 365 e o primeiro além do ano',
       all(C.desvio_em(H, c, 0) == 0 and C.desvio_em(H, c, -3) == 0 for c in H['desvios']) and C.desvio_em(H, 'temp_ar_externo_c', 2) == da[182] / e
       and C.desvio_em(H, 'temp_ar_externo_c', 1) == da[182] / e / 2 and C.desvio_em(H, 'temp_ar_externo_c', 366) == da[0] / e
       and C.desvio_em(H, 'temp_ar_externo_c', 365) == (da[0] + da[1]) / 2 / e and C.desvio_em(H, 'temp_ar_externo_c', 500) == da[0] / e
       and C.desvio_em(H, 'temp_ar_externo_c', 3) == (da[181] + da[182]) / 2 / e, '')
    ok('o histórico é determinístico (duas chamadas dão o mesmo dado; o relógio do sistema o determinismo() já confere)',
       G.historico_dados() == G.historico_dados() == H, '')
    js = G.gera_js(D)
    bloco = len(json.dumps(H, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
    print('        capitao-dados.js: %.1f KB (orçamento 120 KB) · historico: %.1f KB · serie24v: %d bytes' % (
        len(js.encode('utf-8')) / 1024, bloco / 1024, len(json.dumps(sv, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))))
    ok('TAMANHO: o capitao-dados.js com o histórico continua abaixo do orçamento de 120 KB (o plano B do §5, histórico em arquivo à parte, não entra)',
       len(js.encode('utf-8')) <= 120 * 1024 and 4 * 1024 <= bloco <= 12 * 1024, (len(js), bloco))
    # ——— plantas (HISTORICO, leves: a asserção roda sozinha sobre o D alterado)
    c9_planta('historico ausente na simulação', lambda D: D.pop('historico'), 'historico ausente na simulação')
    c9_planta('fim diferente de «ancora»', lambda D: D['historico'].update({'fim': 'hoje'}), "historico.fim ≠ 'ancora'", True)
    c9_planta('n × passo_dias que não cobre o ano (n = 100 e os desvios cortados em 100)',
              lambda D: (D['historico'].update({'n': 100}), [s.update({'d': s['d'][:100]}) for s in D['historico']['desvios'].values()]), 'não cobre os 366 dias')
    c9_planta('desvio com 182 pontos (n = 183)', lambda D: D['historico']['desvios']['vento_verdadeiro_nos']['d'].pop(), 'desvios.vento_verdadeiro_nos com 182 pontos (precisa de 183)', True)
    c9_planta('desvio com valor não inteiro (1,5 em vez de 15)', c9_d_de('temp_ar_externo_c', 7, 1.5), 'desvios.temp_ar_externo_c com valor não inteiro', True)
    c9_planta('desvio sem variação (tudo 0: o gráfico de 30 D e 1 A sairia reto)', lambda D: D['historico']['desvios']['pressao_barometrica_hpa'].update({'d': [0] * 183}),
              'desvios.pressao_barometrica_hpa sem variação')
    c9_planta('escala zero', lambda D: D['historico']['desvios']['temp_agua_c'].update({'escala': 0}), 'desvios.temp_agua_c.escala precisa ser inteiro positivo')
    # (revisão do C9, §6.3 «sem NaN», «métricas ⊂ D.campos», «so150 ⊂ grupos de métricas»): as três checagens do confere.py tinham a linha e nenhuma planta
    c9_planta('NaN num desvio', c9_d_de('vento_verdadeiro_nos', 5, float('nan')), 'com valor não finito', True)
    c9_planta('métrica fora do catálogo (xyz no grupo vento)', lambda D: D['historico']['metricas']['vento'].append('xyz'), "'xyz' fora de D.campos", True)
    c9_planta('so150 com grupo que não existe (zzz)', lambda D: D['historico']['so150'].append('zzz'), "'zzz' fora das métricas", True)
    c9_planta('curva do ano com 72 pontos', lambda D: D['historico']['sazonal']['temp_agua_c']['d'].pop(), 'sazonal.temp_agua_c sem 73 pontos')
    c9_planta('curva do ano do ar plana (30 D e 1 A sairiam retos)', lambda D: D['historico']['sazonal']['temp_ar_externo_c'].update({'d': [0] * 72 + [1]}), 'varia só 0.1 °C no ano')
    c9_planta('curva do ano do hemisfério norte (máximo em meados de julho)',
              lambda D: D['historico']['sazonal']['temp_ar_externo_c'].update({'d': G.sazonal_tabela(4.5, 196)}), 'litoral de SC', True)
    c9_planta('janela de 7 dias com 100 baldes de uma hora (passa de 4 dias)', lambda D: D['historico']['janelas']['7D'].update({'n': 100}),
              "janelas['7D'] = {'passo_s': 3600, 'n': 100}: passo_s × n precisa dar 604800 s", True)
    c9_planta('janela de 30 dias com balde de 25.920 s (não é múltiplo de 150 s)', lambda D: D['historico']['janelas']['30D'].update({'passo_s': 25920, 'n': 100}),
              "janelas['30D']", True)
    c9_planta('janela de 150 s trocada', lambda D: D['historico']['janelas'].update({'150S': {'passo_s': 5, 'n': 30}}), "janelas['150S']", True)
    c9_planta('janela de 1 dia tirada', lambda D: D['historico']['janelas'].pop('1D'), "janelas['1D'] ausente", True)
    c9_planta('grupo só do laço com campo derivado que não é o STW (diesel_bb_pct em «navegacao»)', lambda D: D['historico']['metricas']['navegacao'].append('diesel_bb_pct'),
              "so150: 'navegacao' tem campo fora do laço", True)
    c9_planta('grupo só do laço com campo de contador (diesel_litros em «consumo»)', lambda D: D['historico']['metricas']['consumo'].append('diesel_litros'),
              "so150: 'consumo' tem campo fora do laço", True)
    c9_planta('grupo de métricas do laço fora do so150 e sem desvio (o vento sem desvio)', lambda D: D['historico']['desvios'].pop('vento_verdadeiro_nos'),
              'vento_verdadeiro_nos é do laço e não tem desvio', True)
    c9_planta('a água sem a curva do ano', lambda D: D['historico']['sazonal'].pop('temp_agua_c'), 'historico.sazonal sem temp_agua_c', True)
    c9_planta('o ar sem o desvio do dia', lambda D: D['historico']['desvios'].pop('temp_ar_externo_c'), 'historico.desvios sem temp_ar_externo_c')
    c9_planta('cruzeiro sem a média do óleo BE', lambda D: D['historico']['cruzeiro'].pop('motor_be_oleo_bar'), 'historico.cruzeiro sem motor_be_oleo_bar', True)
    c9_planta('cruzeiro do BB acima do normal (90,0 °C)', lambda D: D['historico']['cruzeiro']['motor_bb_arref_c']['d'].__setitem__(10, 900),
              'historico.cruzeiro.motor_bb_arref_c: 90.0 cruza o normal', True)
    c9_planta('cruzeiro do óleo BE abaixo do normal de cruzeiro (2,0 bar)', lambda D: D['historico']['cruzeiro']['motor_be_oleo_bar']['d'].__setitem__(5, 200),
              'historico.cruzeiro.motor_be_oleo_bar: 2.0 cruza o normal', True)
    c9_planta('cruzeiro do BE em 88,0 °C (no limite de 88: a menos de 0,05)', lambda D: D['historico']['cruzeiro']['motor_be_arref_c']['d'].__setitem__(30, 880),
              'historico.cruzeiro.motor_be_arref_c: 88.0 cruza o normal', True)
    c9_planta('BE sem subir em relação ao BB (a série plana em 82,4 °C)', lambda D: D['historico']['cruzeiro']['motor_be_arref_c'].update({'d': [824] * 60}),
              'o BE não sobe em relação ao BB', True)
    c9_planta('BE acima de hoje já ontem (84,9 °C contra 84,5 pelo laço)', lambda D: D['historico']['cruzeiro']['motor_be_arref_c']['d'].__setitem__(59, 849),
              'ontem o BE estava', True)
    c9_planta('bateria de partida com desvio de +5 V (o máximo passa de 29,4 V)', c9_d_de('bateria_1_tensao_v', 3, 500), 'historico.desvios.bateria_1_tensao_v: o máximo cruza o normal (29.4)', True)
    c9_planta('vento negativo (desvio de −20 nós)', c9_d_de('vento_verdadeiro_nos', 3, -200), 'vento negativo', True)
    c9_planta('praça de máquinas com o desvio do ar de +12 °C (46 + 12 + 9 passa de 60 °C)', c9_d_de('temp_ar_externo_c', 5, 120), 'praça de máquinas + desvio do ar cruza 60', False)
    c9_planta('serie24v ausente', lambda D: D.pop('serie24v'), 'serie24v ausente na simulação')
    c9_planta('serie24v com um dia que não é objeto (a asserção acusa, não levanta exceção)', lambda D: D['serie24v'].__setitem__(2, None), 'serie24v: cada dia precisa ser', True)
    c9_planta('desvios fora da forma (uma lista no lugar do objeto)', lambda D: D['historico'].update({'desvios': []}), 'historico.desvios sem temp_ar_externo_c')
    c9_planta('serie24v com 6 dias', lambda D: D['serie24v'].pop(0), 'serie24v: diasAtras precisa ser 6…0', False)
    c9_planta('serie24v com min igual a max', lambda D: c9_serie(D, 6, min=27.28, max=27.28), 'serie24v[0]: min (27.28) não é menor que max (27.28)', False)
    c9_planta('serie24v com o mín/máx de hoje trocado (a série antiga: 26,0 a 27,4 V)', lambda D: c9_serie(D, 6, min=26.0, max=27.4), 'serie24v[0]: 26.0 a 27.4 ≠ o mín/máx da volta', True)
    c9_planta('serie24v fora do normal do banco (máx 29,9 V)', lambda D: c9_serie(D, 3, min=29.3, max=29.9), 'cruza o normal (24.4 a 29.4 V)', False)
    # ——— a fixture mínima (replay mínimo + histórico mínimo bem formado) não acusa nada, e a série 24 V dela confere com a fórmula
    Vm = verifica(com_historico(com_rota(hoje())))
    ok('a fixture mínima (com_historico) não acusa nada na HISTORICO: forma completa, série 24 V da própria fixture', not Vm['HISTORICO'], Vm['HISTORICO'][:3])
    # ——— modo real (§4.3): sem histórico nem série 24 V (o mín/máx saem do laço e do histórico simulados), e nada estrutural acusa
    sim0 = G.SIMULACAO
    try:
        G.SIMULACAO = False
        Dr = G.dados()
        Vr = C.verifica(Dr, G.base_conhecimento(), G.gera_fontes(Dr), G.saidas(Dr, G.base_conhecimento()), None, None, None, None, CONST)
    finally:
        G.SIMULACAO = sim0
    ok('SIMULACAO = False: o D sai sem historico nem serie24v (SEM DADOS nos leitores) e a HISTORICO não acusa a falta',
       'historico' not in Dr and 'serie24v' not in Dr and not Vr['HISTORICO'] and not Vr['LACO'], (Vr['HISTORICO'][:2], Vr['LACO'][:2]))
    planta('LACO', ' — C9: histórico simulado no modo real (§4.3)', c8_real(lambda D: D.update({'historico': G.historico_dados()}), 'D'), 'modo real: D.historico só na simulação')
    planta('LACO', ' — C9: série 24 V simulada no modo real (§4.3)', c8_real(lambda D: D.update({'serie24v': [{'diasAtras': 0, 'min': 27.2, 'max': 27.8, 'd': '26/09'}]}), 'D'),
           'modo real: D.serie24v só na simulação')


# ——————————————————————————————— C10: checklists, sensores, peças e alarmes pedidos (CONTRATO §1.18–§1.21) ———————————————————————————————
C10_ITENS = {'saida': 14, 'chegada': 8, 'abastecimento': 7, 'fundeio': 6}


def c10_ck(D, i):
    """O item `i` do checklist (em qualquer tipo)."""
    return next(x for lista in D['checklists']['itens'].values() for x in lista if x['id'] == i)


def c10_sn(D, i):
    return next(p for p in D['sensores']['pontos'] if p['id'] == i)


def c10_pc(D, i):
    return next(p for p in D['pecas'] if p['id'] == i)


def c10_al(D, i):
    return next(m for m in D['alarmesPedidos']['metricas'] if m['id'] == i)


C10_CTX = {}


def c10_base():
    """A base e as fontes de hoje, geradas uma vez: as asserções leves leem os trechos (a `fonte` do item) e, nas de texto, as fontes."""
    if not C10_CTX:
        D = G.dados()
        B = G.base_conhecimento()
        C10_CTX.update(B=B, F=G.gera_fontes(D))
    return C10_CTX


def c10_planta(regra, fn, o_que, muda, espera, so_uma=False, faq=None):
    """A asserção `fn` (a função da `regra` no confere.py, sozinha sobre o D alterado) acusa a amostra plantada como violação NOVA (com `so_uma`,
    a única). É a prova leve de cada checagem: a rodada completa (verifica) custa segundos por amostra e as estruturais reprovam o gerador."""
    c = c10_base()
    bom, D = fn(C.Ctx(copy.deepcopy(G.dados()), c['B'], c['F'], {}, faq)), copy.deepcopy(G.dados())
    muda(D)
    novos = [m for m in fn(C.Ctx(D, c['B'], c['F'], {}, faq)) if m not in bom]
    ok('%s: acusa a amostra plantada — C10: %s%s' % (regra, o_que, ' (uma violação só)' if so_uma else ''),
       any(espera in m for m in novos) and (not so_uma or len(novos) == 1) and (regra in C.RELATORIO) == (regra == 'TERMOS'), {'novas': novos[:3]})


def c10_funcoes():
    print('C10 (CONTRATO §1.18–§1.21): checklists (F09), sensores (F08), peças (F22) e alarmes pedidos (F12)')
    k = hoje()
    D = k['D']
    V = verifica(k)
    ok('o dado de hoje não acusa nada na FUNCOES, na IDS, na NULO, na SEM_EMERGENCIA, na SEM_SALVATAGEM_EM, na LOCAL_VOCAB nem na TAMANHO',
       not any(V[n] for n in ('FUNCOES', 'IDS', 'NULO', 'SEM_EMERGENCIA', 'SEM_SALVATAGEM_EM', 'LOCAL_VOCAB', 'TAMANHO')),
       {n: V[n][:2] for n in ('FUNCOES', 'IDS', 'NULO', 'SEM_EMERGENCIA', 'SEM_SALVATAGEM_EM', 'LOCAL_VOCAB', 'TAMANHO') if V[n]})
    # ——— checklists (§1.18)
    ck = D['checklists']
    ok('checklists: a fonte é o título do guia, os 4 tipos (id, l, aba, nome, sys) na ordem do contrato e 14 + 8 + 7 + 6 itens',
       ck['fonte'] == 'Checklist de bordo' and [t['id'] for t in ck['tipos']] == ['saida', 'chegada', 'abastecimento', 'fundeio']
       and ck['tipos'][2] == {'id': 'abastecimento', 'l': 'Abastecimento', 'aba': 'no posto', 'nome': 'Checklist de abastecimento', 'sys': 'Combustível'}
       and {t: len(v) for t, v in ck['itens'].items()} == C10_ITENS and sum(C10_ITENS.values()) == 35, {t: len(v) for t, v in ck['itens'].items()})
    ok('checklists: s01 e s04 e s11 são parciais; o s12 é sobre a agenda (`tarefas`); tempo e maré (s01, f06) são `auto`; o resto do ✓ automático da tabela do §1.18 (19 itens)',
       [x['id'] for t in ck['itens'].values() for x in t if x.get('parcial')] == ['s01', 's04', 's11'] and c10_ck(D, 's12')['auto'] == 'tarefas'
       and c10_ck(D, 's01')['auto'] == 'tempo' and c10_ck(D, 'f06')['auto'] == 'mare' and sum(1 for t in ck['itens'].values() for x in t if 'auto' in x) == 19,
       [(x['id'], x.get('auto')) for t in ck['itens'].values() for x in t if 'auto' in x])
    ok('checklists: o s09 (estabilizador) não cita minutos do fabricante; o s13 é a frase do guia (coletes, "conte as pessoas a bordo agora") e a única com "boia"',
       'min' not in c10_ck(D, 's09')['t'] and c10_ck(D, 's13')['t'].startswith('Coletes: um por pessoa — conte as pessoas a bordo agora;')
       and [x['id'] for t in ck['itens'].values() for x in t if 'boia' in x['t'].lower()] == ['s13'], c10_ck(D, 's09')['t'])
    ok('checklists: a fonte do item é o §n do guia que diz o que ele diz (s03 → Motores §1, s07 → elétrico §2, c03 → Motores §6, f02 → Guincho §1) ou «boa prática»; o s05 e o a07, o Abastecimento do checklist',
       c10_ck(D, 's03')['fonte'] == 'Guia de bordo — Motores Cummins §1 · Antes da partida'
       and c10_ck(D, 's07')['fonte'] == 'Guia de bordo — Sistema elétrico 24 V e 12 V §2 · Faixas' and c10_ck(D, 'c03')['fonte'] == 'Guia de bordo — Motores Cummins §6 · Parada'
       and c10_ck(D, 'f02')['fonte'] == 'Guia de bordo — Guincho e corrente Lewmar §1 · Lançar' and c10_ck(D, 's05')['fonte'] == c10_ck(D, 'a07')['fonte'] == 'Checklist de bordo § Abastecimento'
       and sum(1 for t in ck['itens'].values() for x in t if x['fonte'] == 'boa prática') == 12, [x['id'] for t in ck['itens'].values() for x in t if x['fonte'] == 'boa prática'])
    ok('checklists: os itens do FAQ (17) e as duas telas (c08 → diário, a06 → Abastecimento) do contrato; os demais não têm `faq` nem `link`',
       sum(1 for t in ck['itens'].values() for x in t if 'faq' in x) == 17 and c10_ck(D, 'a07')['faq'] == 'CK-05' and c10_ck(D, 's13')['faq'] == 'EM-09'
       and c10_ck(D, 'c08')['link'] == 'G3-Diario' and c10_ck(D, 'a06')['link'] == 'G2-Abastecimento'
       and sum(1 for t in ck['itens'].values() for x in t if 'link' in x) == 2, '')
    # ——— sensores (§1.19)
    sn = D['sensores']
    ok('sensores: o desenho (caminho e tamanho que a Fase 4 segue), a referencia e 22 pontos (7 no perfil, 15 na planta), n de 1 a 22',
       sn['perfil'] == {'img': 'assets/sensores-perfil.svg', 'w': 1200, 'h': 360} and sn['planta'] == {'img': 'assets/sensores-planta.svg', 'w': 1200, 'h': 420}
       and sn['referencia'] == {'popa_x': 0.04, 'proa_x': 0.95, 'quilha_y': 0.92, 'topo_y': 0.08, 'eixo_y': 0.5, 'meia_boca': 0.32}
       and [p['n'] for p in sn['pontos']] == list(range(1, 23)) and sum(1 for p in sn['pontos'] if p['vista'] == 'perfil') == 7, '')
    gps, mbb = c10_sn(D, 'gps'), c10_sn(D, 'motor_bb')
    ok('sensores: x e y pela fórmula, contados à mão aqui (antena GPS: l 0,55, a 0,95 → 0,5405 e 0,122; motor BB: l 0,25, b −0,40 → 0,2675 e 0,372)',
       (gps['x'], gps['y']) == (0.5405, 0.122) and (mbb['x'], mbb['y']) == (0.2675, 0.372) and 'b' not in gps and 'a' not in mbb, (gps, mbb))
    ok('sensores: a estação meteorológica (vento verdadeiro e aparente, ar, pressão) e o inclinômetro (jogo, caimento, proa = roll, pitch, yaw) do contrato',
       c10_sn(D, 'meteo')['campos'] == ['vento_verdadeiro_nos', 'vento_verdadeiro_angulo', 'vento_aparente_nos', 'vento_aparente_angulo', 'temp_ar_externo_c', 'pressao_barometrica_hpa']
       and c10_sn(D, 'inclinometro')['campos'] == ['jogo_graus', 'caimento_graus', 'proa_graus'], '')
    blocos = [(p['vista'], plat, b[1]) for p in sn['pontos'] for plat, b in p['bloco'].items()]
    ok('sensores: as fileiras do contrato (web: 0,05 e 0,15 em cima, 0,85 e 0,95 embaixo; app: 0,04 e 0,13, 0,87 e 0,96), o lado alterna e bx fica em [0,06, 0,94]',
       {(plat, b[1]) for p in sn['pontos'] for plat, b in p['bloco'].items()} == {('web', 0.05), ('web', 0.15), ('web', 0.85), ('web', 0.95),
                                                                                  ('app', 0.04), ('app', 0.13), ('app', 0.87), ('app', 0.96)}
       and all(0.06 <= b[0] <= 0.94 for p in sn['pontos'] for b in p['bloco'].values()) and len(blocos) == 44, '')
    # o contrato fixa bx = x, o que 5 sensores do perfil (em 0,09 de largura) e 10 da planta (em 0,18) não comportam em 4 fileiras de 0,10: o bloco anda para a direita só o necessário
    move = [(p['id'], plat) for p in sn['pontos'] for plat, b in p['bloco'].items() if b[0] > min(max(p['x'], 0.06), 0.94) + 1e-9]
    ok('sensores: onde 4 fileiras não comportam bx = x, o bloco anda para a direita só o necessário (nunca para a esquerda): %d dos 44 blocos; o resto fica em bx = x' % len(move),
       0 < len(move) < 22 and all(c10_sn(D, i)['bloco'][pl][0] - c10_sn(D, i)['x'] < 0.15 for i, pl in move), move)
    ok('sensores: a regra recontada aqui (blocos_sensores, por plataforma e por vista) dá o bloco gravado em cada ponto, e o gps anda de 0,5405 para 0,5495 (a 0,10 do estabilizador, na mesma fileira)',
       all(c10_sn(D, i)['bloco'][pl] == b for pl in ('web', 'app') for v in ('perfil', 'planta')
           for i, b in C.blocos_sensores([p for p in sn['pontos'] if p['vista'] == v], pl).items()) and gps['bloco']['web'] == [0.5495, 0.85, 'baixo'], gps['bloco'])
    # ——— peças (§1.20)
    ok('pecas: 12 peças, p01 a p12, sem código de fabricante (pn) nem preço; só a p03 está abaixo do mínimo (1 de 2) e só a p05 chega a zero (0 de 1, a falta do diário d03)',
       [p['id'] for p in D['pecas']] == ['p%02d' % i for i in range(1, 13)] and not any({'pn', 'preco', 'valor'} & set(p) for p in D['pecas'])
       and [p['id'] for p in D['pecas'] if p['qtd'] < p['min']] == ['p03', 'p05'] and [p['id'] for p in D['pecas'] if p['qtd'] == 0] == ['p05']
       and c10_pc(D, 'p05')['tarefas'] == ['gerador-rotor'], '')
    ok('pecas: o `local` é de vocabulário fechado e as `tarefas` existem na agenda; a p10 e a p12 não têm tarefa (a chave é omitida, nunca vazia)',
       all(C.LOCAL_PECAS.fullmatch(p['local']) for p in D['pecas']) and all(t in {a['id'] for a in D['agenda']} for p in D['pecas'] for t in p.get('tarefas', []))
       and 'tarefas' not in c10_pc(D, 'p10') and 'tarefas' not in c10_pc(D, 'p12'), '')
    # ——— alarmes pedidos (§1.21)
    al = D['alarmesPedidos']
    ok('alarmesPedidos: chave capitao.alarmes.v1, no máximo 10, histerese de 10 s, nível só aviso e a fonte do contrato',
       (al['chave'], al['max'], al['histerese_s'], al['nivel'], al['fonte']) == ('capitao.alarmes.v1', 10, 10, 'aviso', 'alarme pedido no chat · avaliado neste aparelho'), list(al))
    ok('alarmesPedidos: 18 métricas, as faixas do contrato escritas de novo aqui (óleo 0,5–6,0 · arrefecimento 60–100 · rpm 500–2.600 · 24 V 22–30 · 12 V 11–15 · profundidade 1–50 · '
       'vento 5–50 · SOG 1–30 · pressão 980–1.040 · água do mar 10–32 · diesel 100–1.600 · tanques 5–100) e `motor` só no óleo, no arrefecimento e na rpm',
       [(m['id'], m['faixa']) for m in al['metricas']] == [
           ('oleo_bb', [0.5, 6.0]), ('oleo_be', [0.5, 6.0]), ('arref_bb', [60, 100]), ('arref_be', [60, 100]), ('rpm_bb', [500, 2600]), ('rpm_be', [500, 2600]),
           ('b24s', [22.0, 30.0]), ('b24p', [22.0, 30.0]), ('b12', [11.0, 15.0]), ('profundidade', [1, 50]), ('vento', [5, 50]), ('sog', [1, 30]),
           ('pressao', [980, 1040]), ('agua_mar', [10, 32]), ('diesel', [100, 1600]), ('agua', [5, 100]), ('cinzas', [5, 100]), ('negras', [5, 100])]
       and [m['id'] for m in al['metricas'] if m.get('motor')] == ['oleo_bb', 'oleo_be', 'arref_bb', 'arref_be', 'rpm_bb', 'rpm_be'], [m['id'] for m in al['metricas']])
    ok('alarmesPedidos: a regra é a `faixa` própria, não o D.replay.limites (o vento, a SOG, a pressão e a água do mar não têm limite no replay); nome, un e casas saem do D.campos',
       all(m['campos'][0] not in D['replay']['limites'] for m in al['metricas'] if m['id'] in ('vento', 'sog', 'pressao', 'agua_mar'))
       and all((m['nome'], m['un'], m['casas']) == (D['campos'][m['campos'][0]]['rotulo'], D['campos'][m['campos'][0]]['un'], D['campos'][m['campos'][0]]['casas']) for m in al['metricas']), '')
    # ——— nos dois modos, determinístico e dentro do orçamento
    js = G.gera_js(D)
    print('        capitao-dados.js: %.1f KB (orçamento 120 KB) · checklists %.1f KB · sensores %.1f KB · pecas %.1f KB · alarmesPedidos %.1f KB' % (
        (len(js.encode('utf-8')) / 1024,) + tuple(len(json.dumps(D[c], ensure_ascii=False, separators=(',', ':')).encode('utf-8')) / 1024
                                                  for c in ('checklists', 'sensores', 'pecas', 'alarmesPedidos'))))
    ok('TAMANHO: o capitao-dados.js com os quatro blocos continua abaixo do orçamento de 120 KB (o plano B do §5, checklists e sensores em arquivo à parte, não entra)',
       len(js.encode('utf-8')) <= 120 * 1024, len(js))
    ok('os quatro blocos são determinísticos (duas chamadas dão o mesmo dado)',
       G.checklists_dados() == G.checklists_dados() == D['checklists'] and G.sensores_dados() == G.sensores_dados() == D['sensores']
       and G.alarmes_pedidos_dados() == G.alarmes_pedidos_dados() == D['alarmesPedidos'], '')
    sim0 = G.SIMULACAO
    try:
        G.SIMULACAO = False
        Dr = G.dados()
        Vr = C.verifica(Dr, G.base_conhecimento(), G.gera_fontes(Dr), G.saidas(Dr, G.base_conhecimento()), None, None, None, None, CONST)
    finally:
        G.SIMULACAO = sim0
    ok('SIMULACAO = False: os quatro blocos continuam (checklists, sensores, peças e alarmes pedidos não dependem da navegação simulada) e a FUNCOES não acusa nada',
       all(c in Dr for c in ('checklists', 'sensores', 'pecas', 'alarmesPedidos')) and not Vr['FUNCOES'] and not Vr['IDS'], (Vr['FUNCOES'][:2], Vr['IDS'][:2]))
    # ——— revisão do C10: os números do `t` saem das constantes do guia e do LIMITES (coerência por construção, §0.10) e a FUNCOES os prende
    ok('checklists: c03 e f02 dizem o mesmo número que a seção do guia que a `fonte` cita (as duas saem de PARADA_MOTORES_MIN e LANCE_ANCORA_VEZES)',
       '%s minutos' % G.de_a(G.PARADA_MOTORES_MIN) in dict(G.GUIAS['g_motores']['secoes'])['6 · Parada'] and c10_ck(D, 'c03')['t'] == 'Motores 2 a 3 min em marcha lenta antes de desligar.'
       and '%s vezes' % G.de_a(G.LANCE_ANCORA_VEZES) in dict(G.GUIAS['g_ancora']['secoes'])['1 · Lançar'] and c10_ck(D, 'f02')['t'] == 'Corrente: lance de 3 a 5 vezes a profundidade.',
       (c10_ck(D, 'c03')['t'], c10_ck(D, 'f02')['t']))
    c0 = (G.DIESEL_AVISO_PCT, G.PARADA_MOTORES_MIN, G.LANCE_ANCORA_VEZES, G.LIMITES['tanque_agua_pct']['aviso']['abaixo'], G.LIMITES['tanque_cinzas_pct']['aviso']['acima'])
    try:
        G.DIESEL_AVISO_PCT, G.PARADA_MOTORES_MIN, G.LANCE_ANCORA_VEZES = 30, (4, 5), (6, 8)
        G.LIMITES['tanque_agua_pct']['aviso']['abaixo'], G.LIMITES['tanque_cinzas_pct']['aviso']['acima'] = 20, 90
        mexido = G.checklists_dados()
    finally:
        G.DIESEL_AVISO_PCT, G.PARADA_MOTORES_MIN, G.LANCE_ANCORA_VEZES = c0[:3]
        G.LIMITES['tanque_agua_pct']['aviso']['abaixo'], G.LIMITES['tanque_cinzas_pct']['aviso']['acima'] = c0[3:]
    dm = copy.deepcopy(D)
    dm['checklists'] = mexido
    novos = [m for m in C.a_funcoes(C.Ctx(dm, c10_base()['B'], c10_base()['F'], {}, None)) if '.t: números' in m]
    ok('checklists: o `t` de s05, s06, a07, c03 e f02 acompanha a constante (30 %, 20 % e 90 %, 4 a 5 min, 6 a 8 vezes) e a FUNCOES acusa os cinco contra o contrato',
       c10_ck(dm, 's05')['t'] == 'Diesel acima de 30 % em cada tanque.' and c10_ck(dm, 's06')['t'] == 'Água doce acima de 20 %; servidas abaixo de 90 %.'
       and c10_ck(dm, 'a07')['t'] == 'Diesel acima de 30 % em cada tanque antes de sair.' and c10_ck(dm, 'c03')['t'] == 'Motores 4 a 5 min em marcha lenta antes de desligar.'
       and c10_ck(dm, 'f02')['t'] == 'Corrente: lance de 6 a 8 vezes a profundidade.' and len(novos) == 5
       and (G.DIESEL_AVISO_PCT, G.PARADA_MOTORES_MIN, G.LANCE_ANCORA_VEZES) == c0[:3] and G.checklists_dados() == D['checklists'], novos[:3])
    # ——— plantas (FUNCOES, leves)
    f = C.a_funcoes
    cp = lambda o, m, e, u=False: c10_planta('FUNCOES', f, o, m, e, u)
    cp('tipos do checklist fora de ordem', lambda D: D['checklists']['tipos'].reverse(), 'checklists.tipos ≠ os 4 do §1.18', True)
    cp('checklist sem o tipo fundeio', lambda D: D['checklists']['itens'].pop('fundeio'), 'checklists.itens: precisa dos 4 tipos', True)
    cp('fonte do checklist que não é o título do guia', lambda D: D['checklists'].update({'fonte': 'Checklist'}), 'checklists.fonte', True)
    cp('item s14 a menos', lambda D: D['checklists']['itens']['saida'].pop(), 'checklists.itens.saida: ids', True)
    cp('item c09 a mais', lambda D: D['checklists']['itens']['chegada'].append(dict(c10_ck(D, 'c07'), id='c09')), 'checklists.itens.chegada: ids')
    cp('rótulo `c` trocado (s05 «combustível»)', lambda D: c10_ck(D, 's05').update({'c': 'combustível'}), 'checklists.itens.saida.s05.c', True)
    cp('texto vazio', lambda D: c10_ck(D, 's02').update({'t': ' '}), 'checklists.itens.saida.s02.t vazio', True)
    cp('número de pessoas no item', lambda D: c10_ck(D, 's14').update({'t': 'Leve 4 pessoas a bordo.'}), 'número de pessoas no item', True)
    cp('fonte que não existe (§11 do guia dos motores)', lambda D: c10_ck(D, 's03').update({'fonte': 'Guia de bordo — Motores Cummins §11 · Inventado'}), 's03.fonte', True)
    cp('«boa prática» sem o acento', lambda D: c10_ck(D, 's14').update({'fonte': 'boa pratica'}), 's14.fonte', True)
    cp('fonte vazia', lambda D: c10_ck(D, 's14').update({'fonte': ''}), 's14.fonte', True)
    # revisão do C10: o texto do item e a `fonte` presos ao contrato (CK_NUM, CK_FONTE) e à seção citada; antes, só a existência da fonte era conferida
    cp('s06 com «acima de 50 %» (o guia diz 15 %)', lambda D: c10_ck(D, 's06').update({'t': 'Água doce acima de 50 %; servidas abaixo de 80 %.'}),
       'checklists.itens.saida.s06.t: números', True)
    cp('s06 com os dois números trocados (80 % e 15 %)', lambda D: c10_ck(D, 's06').update({'t': 'Água doce acima de 80 %; servidas abaixo de 15 %.'}),
       'checklists.itens.saida.s06.t: números', True)
    cp('s05 com «40 %» (o guia diz 25 %)', lambda D: c10_ck(D, 's05').update({'t': 'Diesel acima de 40 % em cada tanque.'}), 'checklists.itens.saida.s05.t: números', True)
    cp('a07 com «40 %»', lambda D: c10_ck(D, 'a07').update({'t': 'Diesel acima de 40 % em cada tanque antes de sair.'}), 'checklists.itens.abastecimento.a07.t: números', True)
    cp('f02 com «7 a 9 vezes» (o guia diz 3 a 5)', lambda D: c10_ck(D, 'f02').update({'t': 'Corrente: lance de 7 a 9 vezes a profundidade.'}),
       'checklists.itens.fundeio.f02.t: números', True)
    cp('c03 com «10 min» (o guia diz 2 a 3)', lambda D: c10_ck(D, 'c03').update({'t': 'Motores 10 min em marcha lenta antes de desligar.'}),
       'checklists.itens.chegada.c03.t: números', True)
    cp('número num item que não tem (s14 com 5 min)', lambda D: c10_ck(D, 's14').update({'t': 'Cabos e defensas recolhidos em 5 min.'}),
       'checklists.itens.saida.s14.t: números', True)
    cp('s08 com a fonte de outro guia que existe (Climatização §5)', lambda D: c10_ck(D, 's08').update({'fonte': 'Guia de bordo — Climatização Webasto §5 · Desligar'}),
       'checklists.itens.saida.s08.fonte', True)
    cp('s03 com «boa prática» (o item tem seção, Motores §1)', lambda D: c10_ck(D, 's03').update({'fonte': 'boa prática'}), 'checklists.itens.saida.s03.fonte', True)
    cp('s14 com a fonte de um guia (sem seção no guia)', lambda D: c10_ck(D, 's14').update({'fonte': 'Guia de bordo — Motores Cummins §6 · Parada'}),
       'checklists.itens.saida.s14.fonte', True)
    cp('a07 com a fonte dos Tanques (a seção que existe, mas não tem o 25 %)', lambda D: c10_ck(D, 'a07').update({'fonte': 'Checklist de bordo § Tanques'}),
       'checklists.itens.abastecimento.a07.fonte')
    cp('✓ automático fora da tabela (s10 «tempo»)', lambda D: c10_ck(D, 's10').update({'auto': 'tempo'}), 'checklists.itens.saida.s10: auto/parcial', True)
    cp('`parcial: false` gravado (a chave só existe com true)', lambda D: c10_ck(D, 's02').update({'parcial': False}), 'checklists.itens.saida.s02: auto/parcial', True)
    cp('s04 sem a marca parcial', lambda D: c10_ck(D, 's04').pop('parcial'), 'checklists.itens.saida.s04: auto/parcial', True)
    cp('s11 sem o auto', lambda D: (c10_ck(D, 's11').pop('auto'), c10_ck(D, 's11').pop('parcial')), 'checklists.itens.saida.s11: auto/parcial', True)
    cp('faq trocado (s03 «MO-02»)', lambda D: c10_ck(D, 's03').update({'faq': 'MO-02'}), 'checklists.itens.saida.s03.faq', True)
    cp('faq que o contrato não dá (s14)', lambda D: c10_ck(D, 's14').update({'faq': 'MO-01'}), 'checklists.itens.saida.s14.faq', True)
    cp('link da tela com o sufixo (G3-Diario-Web)', lambda D: c10_ck(D, 'c08').update({'link': 'G3-Diario-Web'}), 'checklists.itens.chegada.c08.link', True)
    cp('chave fora da forma no item (onde)', lambda D: c10_ck(D, 's14').update({'onde': 'convés'}), 'chave fora da forma (onde)', True)
    cp('desenho do perfil em outro caminho', lambda D: D['sensores']['perfil'].update({'img': 'assets/outro.svg'}), 'sensores.perfil', True)
    cp('referência do desenho mudada', lambda D: D['sensores']['referencia'].update({'popa_x': 0.05}), 'sensores.referencia ≠ a do §1.19')
    cp('21 pontos', lambda D: D['sensores']['pontos'].pop(), 'sensores.pontos: precisa de 22 pontos', True)
    cp('ponto com o n trocado', lambda D: c10_sn(D, 'gps').update({'n': 2}), 'sensores.pontos[gps]: n/id/vista')
    cp('x fora da fórmula', lambda D: c10_sn(D, 'gps').update({'x': 0.55}), 'sensores.pontos[gps]: (x, y)')
    cp('y fora da fórmula', lambda D: c10_sn(D, 'motor_bb').update({'y': 0.4}), 'sensores.pontos[motor_bb]: (x, y)', True)
    cp('ponto do perfil na planta', lambda D: c10_sn(D, 'praca').update({'vista': 'planta'}), 'sensores.pontos[praca]: n/id/vista')
    cp('ponto da planta com `a`', lambda D: c10_sn(D, 'motor_bb').update({'a': 0.3}), 'sensores.pontos[motor_bb]: chaves')
    cp('l fora de 0 a 1', lambda D: c10_sn(D, 'leme').update({'l': 1.5}), 'sensores.pontos[leme]: l/b fora de')
    cp('rótulo vazio', lambda D: c10_sn(D, 'leme').update({'rotulo': ''}), 'sensores.pontos[leme].rotulo vazio', True)
    cp('ponto sem campos', lambda D: c10_sn(D, 'leme').update({'campos': []}), 'sensores.pontos[leme].campos', True)
    cp('campo repetido no ponto', lambda D: c10_sn(D, 'leme').update({'campos': ['leme_graus', 'leme_graus']}), 'sensores.pontos[leme].campos', True)
    cp('lado que não alterna (praça «baixo»)', lambda D: c10_sn(D, 'praca')['bloco']['web'].__setitem__(2, 'baixo'), 'sensores.pontos[praca].bloco.web: lado')
    cp('fileira fora das do lado (app by 0,5)', lambda D: c10_sn(D, 'praca')['bloco']['app'].__setitem__(1, 0.5), 'sensores.pontos[praca].bloco.app: by 0.5 fora das fileiras')
    cp('bloco à esquerda do ponto (gps bx 0,5)', lambda D: c10_sn(D, 'gps')['bloco']['web'].__setitem__(0, 0.5), 'sensores.pontos[gps].bloco.web: bx')
    cp('bloco além de 0,94 (guincho 0,97)', lambda D: c10_sn(D, 'guincho')['bloco']['web'].__setitem__(0, 0.97), 'sensores.pontos[guincho].bloco.web: bx')
    cp('bloco que a regra não dá (praça bx +0,0001)', lambda D: c10_sn(D, 'praca')['bloco']['app'].__setitem__(0, 0.2676),
       'sensores.pontos[praca].bloco.app: [0.2676, 0.04, \'cima\'] ≠', True)
    cp('bloco sem o lado', lambda D: c10_sn(D, 'praca')['bloco'].update({'web': [0.2675, 0.05]}), 'sensores.pontos[praca].bloco.web: precisa de [bx, by, lado]', True)
    cp('11 peças', lambda D: D['pecas'].pop(), 'pecas: precisa de 12 peças', True)
    cp('peças fora de ordem', lambda D: D['pecas'].reverse(), 'pecas: ids')
    cp('código de fabricante na peça (pn)', lambda D: c10_pc(D, 'p01').update({'pn': 'X-100'}), 'pecas.p01: chaves', True)
    cp('preço na peça', lambda D: c10_pc(D, 'p01').update({'preco': 10}), 'pecas.p01: chaves', True)
    cp('peça abaixo do mínimo fora da p03 (p01 com 1)', lambda D: c10_pc(D, 'p01').update({'qtd': 1}), 'pecas.p01: qtd/min 1/2', True)
    cp('p03 no mínimo (a única BAIXA deixa de ser)', lambda D: c10_pc(D, 'p03').update({'qtd': 2}), 'pecas.p03: qtd/min 2/2', True)
    cp('quantidade negativa', lambda D: c10_pc(D, 'p10').update({'qtd': -1}), 'pecas.p10: qtd/min -1/2', True)
    cp('quantidade fracionária', lambda D: c10_pc(D, 'p10').update({'qtd': 2.5}), 'pecas.p10: qtd/min 2.5/2', True)
    cp('quantidade booleana', lambda D: c10_pc(D, 'p10').update({'qtd': True}), 'pecas.p10: qtd/min True/2', True)
    cp('p05 sem a tarefa do rotor do gerador', lambda D: c10_pc(D, 'p05').update({'tarefas': ['baterias']}), 'pecas.p05: o rotor do gerador', True)
    cp('tarefas vazia', lambda D: c10_pc(D, 'p01').update({'tarefas': []}), 'pecas.p01.tarefas', True)
    cp('nome da peça vazio', lambda D: c10_pc(D, 'p01').update({'n': ''}), 'pecas.p01.n vazio', True)
    cp('nível do alarme pedido «critico»', lambda D: D['alarmesPedidos'].update({'nivel': 'critico'}), 'alarmesPedidos.nivel', True)
    cp('teto de 11 alarmes', lambda D: D['alarmesPedidos'].update({'max': 11}), 'alarmesPedidos: chave/max/histerese_s', True)
    cp('chave do aparelho trocada', lambda D: D['alarmesPedidos'].update({'chave': 'capitao.alarme.v1'}), 'alarmesPedidos: chave/max/histerese_s', True)
    cp('fonte do alarme pedido trocada', lambda D: D['alarmesPedidos'].update({'fonte': 'alarme'}), 'alarmesPedidos.fonte', True)
    cp('chaves do topo fora de ordem', lambda D: D.update({'alarmesPedidos': dict(reversed(list(D['alarmesPedidos'].items())))}), 'alarmesPedidos: chaves')
    cp('faixa do óleo ampliada (0,5–7,0)', lambda D: c10_al(D, 'oleo_bb').update({'faixa': [0.5, 7.0]}), 'alarmesPedidos.oleo_bb.faixa', True)
    cp('faixa do vento ampliada (5–60)', lambda D: c10_al(D, 'vento').update({'faixa': [5, 60]}), 'alarmesPedidos.vento.faixa', True)
    cp('faixa invertida', lambda D: c10_al(D, 'sog').update({'faixa': [30, 1]}), 'alarmesPedidos.sog.faixa', True)
    cp('só o operador «<»', lambda D: c10_al(D, 'sog').update({'ops': ['<']}), 'alarmesPedidos.sog.ops', True)
    cp('óleo sem `motor`', lambda D: c10_al(D, 'oleo_bb').pop('motor'), 'alarmesPedidos.oleo_bb.motor', True)
    cp('`motor` no vento', lambda D: c10_al(D, 'vento').update({'motor': True}), 'alarmesPedidos.vento.motor', True)
    cp('`motor: false` na rpm', lambda D: c10_al(D, 'rpm_bb').update({'motor': False}), 'alarmesPedidos.rpm_bb.motor', True)
    cp('unidade diferente do D.campos', lambda D: c10_al(D, 'diesel').update({'un': 'l'}), 'alarmesPedidos.diesel: un/casas', True)
    cp('casas diferentes do D.campos', lambda D: c10_al(D, 'oleo_be').update({'casas': 2}), 'alarmesPedidos.oleo_be: un/casas', True)
    cp('palavra com acento e maiúscula', lambda D: c10_al(D, 'agua').update({'palavras': ['Água doce']}), 'alarmesPedidos.agua.palavras', True)
    cp('palavras vazias', lambda D: c10_al(D, 'agua').update({'palavras': []}), 'alarmesPedidos.agua.palavras', True)
    cp('palavra repetida', lambda D: c10_al(D, 'agua').update({'palavras': ['agua doce', 'agua doce']}), 'alarmesPedidos.agua.palavras', True)
    cp('17 métricas', lambda D: D['alarmesPedidos']['metricas'].pop(), 'alarmesPedidos.metricas: os campos', True)
    cp('métrica com 2 campos', lambda D: c10_al(D, 'agua').update({'campos': ['tanque_agua_pct', 'tanque_cinzas_pct']}), 'alarmesPedidos.agua.campos')
    cp('campo fora da lista fechada', lambda D: c10_al(D, 'agua').update({'campos': ['tanque_xpto_pct']}), 'alarmesPedidos.agua.campos')
    cp('nome da métrica vazio', lambda D: c10_al(D, 'agua').update({'nome': ''}), 'alarmesPedidos.agua.nome vazio', True)
    cp('ids repetidos nas métricas', lambda D: c10_al(D, 'negras').update({'id': 'cinzas'}), 'alarmesPedidos.metricas: ids repetidos', True)
    cp('chave fora da forma na métrica', lambda D: c10_al(D, 'agua').update({'lado': 'bb'}), 'alarmesPedidos.agua: chaves', True)
    cp('checklists ausente', lambda D: D.pop('checklists'), 'checklists ausente')
    cp('sensores ausente', lambda D: D.pop('sensores'), 'sensores ausente')
    cp('pecas ausente', lambda D: D.pop('pecas'), 'pecas ausente')
    cp('alarmesPedidos ausente', lambda D: D.pop('alarmesPedidos'), 'alarmesPedidos ausente')
    # ——— plantas das outras regras que o C10 ativa (cada uma sobre a sua função, leve)
    ids = lambda o, m, e, u=True: c10_planta('IDS', C.a_ids, o, m, e, u)
    c = c10_base()
    faq_ok = {'itens': [{'id': i} for i in sorted(set(C.CK_FAQ.values()))]}
    faq_sem = {'itens': [{'id': i} for i in sorted(set(C.CK_FAQ.values()) - {'MO-01'})]}
    bom = [m for m in C.a_ids(C.Ctx(copy.deepcopy(G.dados()), c['B'], c['F'], {}, faq_ok)) if 'checklists' in m]
    mau = [m for m in C.a_ids(C.Ctx(copy.deepcopy(G.dados()), c['B'], c['F'], {}, faq_sem)) if 'checklists' in m]
    ok('IDS: com o FAQ que tem os 17 ids do checklist nada acusa; sem o MO-01, o s03 acusa «faq fora do FAQ» (uma violação só)',
       not bom and len(mau) == 1 and 'checklists.itens.saida.s03.faq fora do FAQ' in mau[0], (bom[:2], mau[:2]))
    ids('peça com a tarefa fora da agenda', lambda D: c10_pc(D, 'p01').update({'tarefas': ['nao-existe']}), 'pecas.p01.tarefas')
    ids('sensor com o campo fora do D.campos', lambda D: c10_sn(D, 'leme').update({'campos': ['leme_graus', 'leme_xpto']}), "sensores.leme.campos: 'leme_xpto' fora de D.campos")
    ids('sensores que não cobrem o caimento (F08)', lambda D: c10_sn(D, 'inclinometro').update({'campos': ['jogo_graus', 'proa_graus']}),
        "sensores: os campos não cobrem 'caimento_graus' (F08/F33)")
    ids('alarme pedido com o campo fora do D.campos', lambda D: c10_al(D, 'agua').update({'campos': ['tanque_xpto_pct']}), 'alarmesPedidos.agua.campos')
    ids('faixa do alarme pedido invertida', lambda D: c10_al(D, 'sog').update({'faixa': [30, 1]}), 'alarmesPedidos.sog.faixa')
    ids('dois blocos da mesma fileira a menos de 0,10 (gps junto do radar)', lambda D: c10_sn(D, 'gps')['bloco']['web'].__setitem__(1, 0.15) or
        c10_sn(D, 'gps')['bloco']['web'].__setitem__(2, 'cima') or c10_sn(D, 'gps')['bloco']['web'].__setitem__(0, 0.52), 'sensores: blocos')
    c10_planta('NULO', C.a_nulo, 'quantidade da peça nula', lambda D: c10_pc(D, 'p01').update({'qtd': None}), 'pecas[0].qtd', True)
    c10_planta('NULO', C.a_nulo, 'lista de tarefas vazia na peça', lambda D: c10_pc(D, 'p01').update({'tarefas': []}), 'pecas[0].tarefas', True)
    c10_planta('NULO', C.a_nulo, 'texto vazio no item do checklist', lambda D: c10_ck(D, 's14').update({'t': ''}), 'checklists.itens.saida[13].t', True)
    c10_planta('NULO', C.a_nulo, 'faixa nula no alarme pedido', lambda D: c10_al(D, 'sog').update({'faixa': None}), 'alarmesPedidos.metricas[11].faixa', True)
    c10_planta('SEM_EMERGENCIA', C.a_sem_emergencia, 'item do checklist com incêndio no texto', lambda D: c10_ck(D, 's14').update({'t': 'Incêndio a bordo: saia.'}),
               'checklists.itens.saida[s14].t casa emergencia()', True)
    c10_planta('SEM_EMERGENCIA', C.a_sem_emergencia, 'item do checklist com mayday no rótulo `c`', lambda D: c10_ck(D, 's14').update({'c': 'mayday'}),
               'checklists.itens.saida[s14].c casa emergencia()', True)
    c10_planta('SEM_EMERGENCIA', C.a_sem_emergencia, 'item do checklist com a queda da pressão do óleo (oleo() = 1)', lambda D: c10_ck(D, 'c03').update({'t': 'Pressão de óleo caiu: reduza.'}),
               'checklists.itens.chegada[c03].t casa oleo() = 1', True)
    c10_planta('SEM_SALVATAGEM_EM', C.a_sem_salvatagem_em, 'ponto de sensor «EPIRB»', lambda D: c10_sn(D, 'leme').update({'rotulo': 'EPIRB'}), 'sensores.pontos[19].rotulo', True)
    c10_planta('SEM_SALVATAGEM_EM', C.a_sem_salvatagem_em, 'id de sensor «balsa»', lambda D: c10_sn(D, 'leme').update({'id': 'balsa'}), 'sensores.pontos[19].id', True)
    c10_planta('SEM_SALVATAGEM_EM', C.a_sem_salvatagem_em, 'peça «Extintor portátil»', lambda D: c10_pc(D, 'p12').update({'n': 'Extintor portátil'}), 'pecas[11].n', True)
    c10_planta('SEM_SALVATAGEM_EM', C.a_sem_salvatagem_em, 'peça «Colete»', lambda D: c10_pc(D, 'p12').update({'n': 'Colete salva-vidas'}), 'pecas[11].n', True)
    c10_planta('LOCAL_VOCAB', C.a_local_vocab, '«kit» na peça', lambda D: c10_pc(D, 'p11').update({'n': 'Kit de fusíveis de 24 V'}), 'pecas[10].n: "kit"', True)
    c10_planta('LOCAL_VOCAB', C.a_local_vocab, '«kit» no item do checklist', lambda D: c10_ck(D, 's14').update({'t': 'Kit de cabos e defensas recolhido.'}), 'checklists.itens.saida[13].t: "kit"', True)
    c10_planta('LOCAL_VOCAB', C.a_local_vocab, '«kit» no ponto do sensor', lambda D: c10_sn(D, 'leme').update({'rotulo': 'Kit do leme'}), 'sensores.pontos[19].rotulo: "kit"', True)
    c10_planta('LOCAL_VOCAB', C.a_local_vocab, '`onde` do sensor fora do vocabulário fechado', lambda D: c10_sn(D, 'leme').update({'onde': 'paiol de proa'}),
               'sensores.pontos[19].onde fora do vocabulário fechado', True)
    c10_planta('LOCAL_VOCAB', C.a_local_vocab, '`local` da peça fora do vocabulário fechado', lambda D: c10_pc(D, 'p01').update({'local': 'paiol de proa'}),
               'pecas[0].local fora do vocabulário fechado', True)
    c10_planta('LOCAL_VOCAB', C.a_local_vocab, '«boia» num item do checklist que não é o s13', lambda D: c10_ck(D, 's14').update({'t': 'Boia e cabos recolhidos.'}),
               'checklists.itens.saida[13].t: "boia" fora', True)
    c10_planta('TERMOS', C.a_termos, 'rótulo «(DEMO)» num item do checklist', lambda D: c10_ck(D, 's14').update({'t': 'Cabos recolhidos (DEMO).'}),
               'ROTULOS: checklists.itens.saida[13].t')
    c10_planta('TERMOS', C.a_termos, 'rótulo «SEM DADOS» na peça', lambda D: c10_pc(D, 'p12').update({'n': 'Escova SEM DADOS'}), 'ROTULOS: pecas[11].n')
    c10_planta('COORD_TEXTO', C.a_coord_texto, 'coordenada no texto do item do checklist', lambda D: c10_ck(D, 's14').update({'t': "Fundeado em 26°59,6'S."}),
               'checklists.itens.saida[13].t', True)


# ——————————————————————————————— C11: faq-equipamentos.json (F10, CONTRATO §1.6) ———————————————————————————————
C11_CTX = {}


def c11_base():
    """O D, a base, as fontes e o FAQ de hoje, gerados uma vez; cada amostra trabalha numa cópia (c11_planta)."""
    if not C11_CTX:
        D = G.dados()
        B = G.base_conhecimento()
        C11_CTX.update(D=D, B=B, F=G.gera_fontes(D), Q=G.faq_equipamentos(B))
    return C11_CTX


def hoje_faq(muda=None):
    """hoje() com o FAQ de verdade (e `muda(k)` por cima): o verifica() completo lê o FAQ junto de tudo o mais."""
    k = hoje()
    k['faq'] = copy.deepcopy(G.faq_equipamentos(k['B']))
    if muda:
        muda(k)
    return k


def faq_it(Q, i):
    return por_id(Q['itens'], i)


def c11_ix(i):
    """Índice do item no `itens` (o caminho das mensagens do TERMOS, do COORD_TEXTO e do NULO é faq:itens[n])."""
    return next(n for n, x in enumerate(c11_base()['Q']['itens']) if x['id'] == i)


def c11_planta(regra, o_que, muda, espera, so_uma=False):
    """A asserção `regra` (sozinha, sobre o D, a base, as fontes e o FAQ de hoje) acusa a amostra plantada como violação NOVA (com `so_uma`, a
    única). `muda(D, B, Q)` mexe nas cópias. É a prova leve de cada checagem do FAQ; a rodada completa fica no hoje_faq() e no main()."""
    c = c11_base()
    fn = dict(C.ASSERCOES)[regra]

    def ctx(planta):
        D, B, Q = copy.deepcopy(c['D']), copy.deepcopy(c['B']), copy.deepcopy(c['Q'])
        if planta:
            muda(D, B, Q)
        return C.Ctx(D, B, c['F'], {'faq-equipamentos.json': G.gera_faq(Q)}, Q)
    bom = fn(ctx(False))
    novos = [m for m in fn(ctx(True)) if m not in bom]
    ok('%s: acusa a amostra plantada — C11: %s%s' % (regra, o_que, ' (uma violação só)' if so_uma else ''),
       any(espera in m for m in novos) and (not so_uma or len(novos) == 1), {'novas': novos[:3], 'espera': espera})


def c11_faq(tmp):
    print('C11 (CONTRATO §1.6): faq-equipamentos.json (F10) — 82 itens dos guias e do checklist, 9 cartões EM, glossário; sem conf nem anexos do Avanti')
    c = c11_base()
    Q, D, B = c['Q'], c['D'], c['B']
    itens = Q['itens']
    P = D['protocolos']
    # ——— o dado de hoje ———
    Vf = verifica(hoje_faq())
    novas, _, velhas = C.separa(Vf, set(C.OPCIONAIS))
    ok('o FAQ de hoje não acusa nada em nenhuma das %d asserções (a FAQ, a TERMOS, a SEGURANCA_MARCADA, o rótulo, a trava 17, a grafia, o tamanho…)' % len(C.NOMES),
       not novas and not velhas, {n: v[:2] for n, v in novas.items()} or velhas)
    ok('o arquivo gerado tem o topo {versao, total, secoes, itens, glossario}, a versao de 8 hex do sha256 do conteúdo e total = itens = 91',
       list(Q) == ['versao', 'total', 'secoes', 'itens', 'glossario'] and Q['total'] == len(itens) == 91
       and Q['versao'] == hashlib.sha256(G.serializa({k: v for k, v in Q.items() if k != 'versao'}).encode('utf-8')).hexdigest()[:8], list(Q))
    ok('o gerador é determinístico: duas rodadas dão o mesmo FAQ, e o texto gravado = gera_faq() (versao nova quando o texto muda)',
       G.faq_equipamentos(B) == Q and G.gera_faq(Q) == G.saidas(D, B, Q)['faq-equipamentos.json'] and G.gera_faq(Q).endswith('}\n'))
    kb = len(G.gera_faq(Q).encode('utf-8')) / 1024
    ok('tamanho: %.1f KB (orçamento do contrato: 100 KB; estimativa 55–70 KB, com 91 itens e o glossário)' % kb, 40 < kb <= 100, kb)
    # ——— ids, seções e a ligação com a base ———
    prefixos = {'EM': 9, 'MO': 10, 'GE': 9, 'SK': 8, 'CL': 6, 'EL': 8, 'EE': 3, 'DS': 4, 'PO': 4, 'AN': 4, 'PI': 4, 'RA': 4, 'AI': 3, 'SF': 4, 'EP': 4, 'CK': 7}
    ids = [x['id'] for x in itens]
    ok('91 ids únicos: EM-01…09, MO-01…10, GE-01…09, SK-01…08, CL-01…06, EL-01…08, EE-01…03, DS-01…04, PO-01…04, AN, PI, RA 01…04, AI-01…03, SF e EP 01…04, CK-01…07',
       len(set(ids)) == 91 and {p: sum(1 for i in ids if i.startswith(p + '-')) for p in prefixos} == prefixos
       and all(re.fullmatch(r'[A-Z]{2}-\d{2}', i) for i in ids) and sum(prefixos.values()) == 91, {p: sum(1 for i in ids if i.startswith(p + '-')) for p in prefixos})
    ok('cada seção de guia ou do checklist vira um item (82) e as 9 do protocolo os cartões EM (a base tem 91 trechos): a 1ª fonte de cada item é o trecho do id',
       len(B['trechos']) == 91 and sum(1 for i in ids if not i.startswith('EM-')) == 82
       and all(sum(1 for t in B['trechos'] if t['fonte'] == D['drive']['arquivos'][k]) == prefixos[p]
               for p, k in (('MO', 'g_motores'), ('GE', 'g_gerador'), ('SK', 'g_seakeeper'), ('CL', 'g_clima'), ('EL', 'g_eletronicos'), ('EE', 'g_eletrico'),
                            ('DS', 'g_dessalinizador'), ('PO', 'g_porao'), ('AN', 'g_ancora'), ('PI', 'g_piloto'), ('RA', 'g_radar'), ('AI', 'g_ais'),
                            ('SF', 'g_seafire'), ('EP', 'g_epirb'), ('CK', 'checklist'))),
       len(B['trechos']))
    ok('9 seções {n, titulo, ids}: n = posição (D.secoes[n − 1]), os ids partem os itens e `secao` do item é o n; a 1ª é a Emergência com os 9 cartões',
       [s['n'] for s in Q['secoes']] == list(range(1, 10)) and [len(s['ids']) for s in Q['secoes']] == [9, 10, 12, 8, 14, 8, 15, 8, 7]
       and Q['secoes'][0]['titulo'] == 'Emergência' and Q['secoes'][0]['ids'] == ['EM-%02d' % n for n in range(1, 10)]
       and all(x['secao'] == s['n'] for s in Q['secoes'] for i in s['ids'] for x in [faq_it(Q, i)]), [(s['n'], s['titulo'], len(s['ids'])) for s in Q['secoes']])
    ok('os itens vêm na ordem das seções (EM primeiro), cada item na chave do contrato e na ordem do contrato, sem chave de confiabilidade nem anexo',
       ids == [i for s in Q['secoes'] for i in s['ids']] and all(list(x) == [k for k in C.FAQ_CHAVES if k in x] for x in itens)
       and not any(k in C.FAQ_PROIBIDAS for _, k in C.chaves_de(Q, 'faq:')), [x['id'] for x in itens if list(x) != [k for k in C.FAQ_CHAVES if k in x]])
    ok('o item: 3 variantes diferentes, `emerg` só nos 9 EM, passos e demais campos omitidos quando vazios, títulos e perguntas únicos',
       all(len(x['variantes']) == 3 == len(set(x['variantes'])) for x in itens) and [x['id'] for x in itens if x['emerg']] == ['EM-%02d' % n for n in range(1, 10)]
       and len({x['titulo'] for x in itens}) == 91 == len({x['pergunta'] for x in itens})
       and all(x.get('passos', ['x']) for x in itens) and sum(1 for x in itens if 'passos' not in x) > 0)
    tipos = {f['tipo'] for x in itens for f in x['fontes']}
    ok('fontes[].tipo ∈ {Guia de bordo, Protocolo, Boa prática}: nenhuma «Manual» nem «Foto»; os cartões EM citam o protocolo e os itens do checklist sem seção, a boa prática',
       tipos == {'Guia de bordo', 'Protocolo', 'Boa prática'} and all([f['tipo'] for f in faq_it(Q, 'EM-%02d' % n)['fontes']] == ['Protocolo'] for n in range(1, 10))
       and [x['id'] for x in itens if any(f['tipo'] == 'Boa prática' for f in x['fontes'])] == ['CK-03', 'CK-04', 'CK-05', 'CK-07'], tipos)
    # ——— segurança, rótulo e os cartões de emergência ———
    seg = {x['id'] for x in itens if x.get('seguranca')}
    minimo = {'EM-%02d' % n for n in range(1, 10)} | {'SF-%02d' % n for n in range(1, 5)} | {'EP-%02d' % n for n in range(1, 5)} | {'MO-04', 'EL-01', 'EL-05', 'PO-04', 'AI-02', 'CK-03'}
    ok('seguranca: true nos EM, SF, EP, CK-03 e nas outras seções do mínimo do §1.5 (MO-04, EL-01, EL-05, PO-04, AI-02) e no CK-05 (extintor), mais o GE-01 (cheiro de combustível) e o PO-02 (alagamento): 26 itens',
       minimo <= seg and {'CK-05', 'GE-01', 'PO-02'} <= seg and len(seg) == 26 and all(x.get('seguranca') in (None, True) for x in itens), sorted(seg ^ minimo))
    base_seg = {(t['fonte'], t['secao']) for t in B['trechos'] if t.get('seguranca')}
    ok('nenhum trecho de segurança da base tem item sem seguranca: o item herda o trecho (nada com seguranca vai à IA, F30)',
       all(x.get('seguranca') or (lambda m: (m.group(1), m.group(2)))(C.R_FONTE.fullmatch(x['fontes'][0]['texto'])) not in base_seg for x in itens))
    fim = C.rotulo_fim()
    ok('EM, SF, EP e a Salvatagem terminam com o rótulo do procedimento padrão (EM-05, EM-08, EM-09, SF e EP também com a nota da etiqueta) e só eles',
       all(faq_it(Q, i)['resposta'].endswith(fim) for i in ['EM-05', 'EM-08', 'EM-09'] + ['SF-%02d' % n for n in range(1, 5)] + ['EP-%02d' % n for n in range(1, 5)])
       and all(faq_it(Q, 'EM-%02d' % n)['resposta'].endswith(C.cap(C.ROTULO) + '.') for n in (1, 2, 3, 4, 6, 7))
       and sorted(x['id'] for x in itens if C.ROTULO.lower() in x['resposta'].lower()) == sorted(['EM-%02d' % n for n in range(1, 10)] + ['SF-%02d' % n for n in range(1, 5)]
                                                                                              + ['EP-%02d' % n for n in range(1, 5)]))
    ok('os cartões EM repetem o D.protocolos: PAN-PAN, DSC (MMSI_RADIO) e Salvatagem letra por letra; o roteiro, o MOB, o fogo e o EPIRB são os passos; só o procedimento padrão',
       faq_it(Q, 'EM-02')['resposta'] == P['panpan'] + ' ' + C.cap(C.ROTULO) + '.' and faq_it(Q, 'EM-03')['resposta'] == P['dsc'] + ' ' + C.cap(C.ROTULO) + '.'
       and P['mmsiRadio'] in faq_it(Q, 'EM-03')['resposta'] and P['mmsiRadio'] in faq_it(Q, 'EM-01')['resposta'] and faq_it(Q, 'EM-09')['resposta'] == P['salvatagem'] + ' ' + fim
       and faq_it(Q, 'EM-01')['passos'] == P['roteiro'] and faq_it(Q, 'EM-04')['passos'] == P['mob'] and faq_it(Q, 'EM-05')['passos'] == P['seafire']['passos']
       and faq_it(Q, 'EM-08')['passos'] == P['epirb']['passos'] and faq_it(Q, 'EM-06')['resposta'].startswith(P['alagamento'][0])
       and faq_it(Q, 'EM-07')['resposta'].startswith(P['abandono'][0]) and ' '.join(faq_it(Q, 'EM-09')['passos']) == P['salvatagem'])
    ok('SF e EP sem fabricante, modelo nem validade: `equip` = «Sistema fixo de supressão de incêndio» / «EPIRB»; nenhum texto do FAQ cita «Ocean Signal», «SafeSea», «FD 300M» nem «Seafire» fora do título do protocolo',
       {x['equip'] for x in itens if x['id'].startswith('SF-')} == {'Sistema fixo de supressão de incêndio'} and {x['equip'] for x in itens if x['id'].startswith('EP-')} == {'EPIRB'}
       and not [m for m in Vf['SEGURANCA_SEM_MODELO'] if m.startswith('faq:')] and not [m for m in Vf['GRAFIA_SEAFIRE'] if m.startswith('faq:')])
    # ——— ligação com o checklist e o glossário ———
    ck = D['checklists']['itens']
    com_faq = [(x, x['faq']) for t in ck.values() for x in t if 'faq' in x]
    ok('os 17 `faq` do checklist existem no FAQ e, fora s10 (EL-04) e s13 (EM-09), apontam para a seção que a `fonte` do item cita',
       len(com_faq) == 17 and all(f in ids for _, f in com_faq)
       and all(faq_it(Q, f)['fontes'][0]['texto'] == x['fonte'] for x, f in com_faq if x['id'] not in ('s10', 's13')) and dict((x['id'], f) for x, f in com_faq)['s13'] == 'EM-09',
       [(x['id'], f, x['fonte']) for x, f in com_faq if f not in ids or (x['id'] not in ('s10', 's13') and faq_it(Q, f)['fontes'][0]['texto'] != x['fonte'])])
    gl = Q['glossario']
    ok('glossário: SOG, STW, COG, HDG, TWS, TWA, AWA, DPT, ETA, MOB, DSC, MMSI, EPIRB e BB/BE, cada um {termo, texto, fonte}; MMSI com o texto MMSI_RADIO (nunca o número); MOB, DSC e EPIRB com o rótulo',
       [g['termo'] for g in gl] == ['SOG', 'STW', 'COG', 'HDG', 'TWS', 'TWA', 'AWA', 'DPT', 'ETA', 'MOB', 'DSC', 'MMSI', 'EPIRB', 'BB/BE'] and all(list(g) == ['termo', 'texto', 'fonte'] for g in gl)
       and P['mmsiRadio'] in next(g for g in gl if g['termo'] == 'MMSI')['texto'] and not re.search(r'\d{9}', ' '.join(g['texto'] for g in gl))
       and all(next(g for g in gl if g['termo'] == t)['texto'].endswith(C.cap(C.ROTULO) + '.') for t in ('MOB', 'DSC')) and next(g for g in gl if g['termo'] == 'EPIRB')['texto'].endswith(fim))
    # ——— revisão do C11: a escalada e a condição ficam na resposta; o checklist entra como ordem de conferência ———
    resp_ = lambda i: faq_it(Q, i)['resposta']
    ok('revisão do C11: a resposta de segurança mantém o que escala ou condiciona, e não só nos passos (EM-04, EM-05, EM-08, SF-01, SF-03, EP-01, EL-05 e PO-04)',
       'Se perder de vista: MAYDAY no canal 16' in resp_('EM-04')
       and all('sozinho e há fogo no motor, use o disparo manual' in resp_(i) and 'Fogo que não apaga: MAYDAY no canal 16' in resp_(i) for i in ('EM-05', 'SF-01'))
       and 'Fogo pequeno fora do motor: extintor portátil' in resp_('SF-01')
       and resp_('EM-08').startswith('Só em perigo grave e iminente, depois do MAYDAY (ou sem rádio).')
       and resp_('EP-01').startswith('Só em perigo grave e iminente, depois do MAYDAY (ou sem rádio).')
       and 'Se o fogo voltar, MAYDAY no canal 16' in resp_('SF-03') and 'Depois do alerta, faça o MAYDAY por voz no canal 16' in resp_('EL-05')
       and 'Água entrando: ligue as bombas de porão' in resp_('PO-04') and 'Água subindo mesmo assim: MAYDAY no canal 16' in resp_('PO-04')
       and resp_('PO-04') == faq_it(Q, 'EM-06')['resposta'][:len(resp_('PO-04'))] and max(len(x['resposta']) for x in itens if x.get('seguranca')) <= C.SEGURANCA_MAX_LETRAS,
       [i for i in ('EM-04', 'EM-05', 'EM-08', 'SF-01', 'SF-03', 'EP-01', 'EL-05', 'PO-04') if not C.R_ESCALA.search(resp_(i))])
    # ——— 2ª revisão do C11: proibição, cautela, ventilação, SOS do app e a ação condicionada ———
    frase = lambda i, f: f.lower() in resp_(i).lower()   # o EM-08 diz «…e leve o EPIRB…» no meio da frase
    ok('2ª revisão do C11: a resposta mantém a proibição «Não abra o acesso ao motor depois da descarga…» (EM-05, SF-01), «Não desligue até o resgate» (EM-08, EP-01), '
       '«Nunca abra a tampa do arrefecimento…» (MO-05, GE-05) e a cautela «e só então libere o acesso, com o extintor portátil à mão» (SF-03)',
       all(frase(i, 'Não abra o acesso ao motor depois da descarga: espere o tempo indicado na etiqueta do sistema e o motor esfriar.') for i in ('EM-05', 'SF-01'))
       and all(frase(i, 'Leve o EPIRB para a balsa ou mantenha-o flutuando preso por um cabo.') and frase(i, 'Não desligue até o resgate.') for i in ('EM-08', 'EP-01'))
       and all(frase(i, 'Nunca abra a tampa do arrefecimento com o motor quente.') for i in ('MO-05', 'GE-05'))
       and frase('SF-03', 'não abra o acesso ao motor; espere o tempo indicado na etiqueta do sistema e só então libere o acesso, com o extintor portátil à mão'),
       {i: resp_(i)[:120] for i in ('EM-05', 'SF-01', 'EM-08', 'EP-01', 'MO-05', 'GE-05', 'SF-03')})
    ok('2ª revisão do C11: a resposta do GE-01 manda ventilar «se houver cheiro de combustível», a do PO-02 manda usar o SOS do app no alagamento e a do EM-01 abre com «Só em perigo grave e iminente»',
       frase('GE-01', 'Ligue a ventilação do compartimento por alguns minutos se houver cheiro de combustível.')
       and frase('PO-02', 'Nível subindo com a bomba ligada ou água entrando é alagamento: use o SOS do app.') and resp_('EM-01').startswith('Só em perigo grave e iminente. ')
       and faq_it(Q, 'EM-01')['atencao'] == 'Só em perigo grave e iminente.')
    ok('2ª revisão do C11: a linha de ação do EP-01 diz «(ou sem rádio)» como a do EM-08, e as respostas de segurança seguem até %d letras (a maior: %d)' % (
        C.SEGURANCA_MAX_LETRAS, max(len(x['resposta']) for x in itens if x.get('seguranca'))),
       faq_it(Q, 'EP-01')['acao'] == faq_it(Q, 'EM-08')['acao'] == 'Só em perigo grave e iminente, depois do MAYDAY (ou sem rádio).'
       and max(len(x['resposta']) for x in itens if x.get('seguranca')) <= C.SEGURANCA_MAX_LETRAS)
    sf2, em5 = faq_it(Q, 'SF-02'), faq_it(Q, 'EM-05')
    cond = 'há fogo no motor'
    ok('2ª revisão do C11: o disparo manual só aparece com a condição «e há fogo no motor» — SF-02 (resposta, linha de ação e último passo), EM-05 (passo 2) e SF-01; '
       'nenhum campo de nenhum item manda usá-lo sem ela',
       cond in sf2['resposta'] and cond in sf2['acao'] and cond in sf2['passos'][2] and 'disparo manual' in sf2['passos'][2] and cond in em5['passos'][1]
       and sf2['acao'].startswith('Só se o sistema não acionou sozinho e há fogo no motor:')
       and not [m for m in C.a_faq(C.Ctx(D, B, c['F'], {}, Q)) if 'manda fazer' in m]
       and sorted(x['id'] for x in itens if 'disparo manual' in ' '.join(str(v) for k, v in x.items() if k not in ('variantes', 'ver'))) == ['EM-05', 'SF-01', 'SF-02'],
       sorted(x['id'] for x in itens if 'disparo manual' in ' '.join(str(v) for k, v in x.items() if k not in ('variantes', 'ver'))))

    def condicao_antes(Q_):
        # a condição num passo ANTERIOR ao do disparo manual vale (a lista se lê em ordem); o passo sozinho, não
        x = faq_it(Q_, 'SF-02')
        x['passos'] = ['Só se o sistema não acionou sozinho e há fogo no motor.', 'Desligue motores e gerador.', 'Corte a ventilação do motor.', 'Use o disparo manual.']
        return [m for m in C.a_faq(C.Ctx(D, B, c['F'], {}, Q_)) if 'manda fazer' in m]
    Qc = copy.deepcopy(Q)
    ok('2ª revisão do C11 (sem falso positivo): com a condição num passo antes de «Use o disparo manual.», a asserção FAQ não acusa', condicao_antes(Qc) == [], condicao_antes(Qc))
    ordem = {x['id']: x for lista in ck.values() for x in lista}
    ok('revisão do C11: CK-03, CK-04, CK-05 e CK-07 trazem os itens «boa prática» do checklist com verbo de ordem (FAQ_CK_ORDEM, os 12), nunca o texto do ✓ que o app avalia '
       '(«Nenhuma tarefa de segurança atrasada», «Nenhum alerta ativo no painel», «Motores desligados»…)',
       set(G.FAQ_CK_ORDEM) == {i for i, f in C.CK_FONTE.items() if f is None} and len(G.FAQ_CK_ORDEM) == 12
       and all(G.FAQ_CK_ORDEM[i] != ordem[i]['t'] for i in C.CK_ESTADO) and len(C.CK_ESTADO) == 8
       and faq_it(Q, 'CK-03')['obs'] == ' '.join(G.FAQ_CK_ORDEM[i] for i in ('s02', 's11', 's12', 's14')) and faq_it(Q, 'CK-04')['obs'] == G.FAQ_CK_ORDEM['c07']
       and faq_it(Q, 'CK-05')['obs'] == ' '.join(G.FAQ_CK_ORDEM[i] for i in ('a01', 'a02', 'a03', 'a05')) and faq_it(Q, 'CK-05')['atencao'] == G.FAQ_CK_ORDEM['a04']
       and faq_it(Q, 'CK-07')['obs'] == ' '.join(G.FAQ_CK_ORDEM[i] for i in ('f04', 'f06'))
       and not [i for i in C.CK_ESTADO for x in itens for k in ('resposta', 'acao', 'atencao', 'senao', 'obs') if ordem[i]['t'] in x.get(k, '')],
       {i: faq_it(Q, i).get('obs') for i in ('CK-03', 'CK-04', 'CK-05', 'CK-07')})
    ok('revisão do C11: a "afirmação de estado" que os dados desmentem não está no FAQ: a agenda tem a tarefa de segurança atrasada (porao-teste) e o FAQ manda conferir, não diz que não há',
       any(a.get('id') == 'porao-teste' and a.get('seguranca') and a.get('st') == 'ATRASADA' for a in D['agenda']) and 'Nenhuma tarefa de segurança atrasada' not in G.gera_faq(Q)
       and 'Confira na agenda se há tarefa de segurança atrasada.' in faq_it(Q, 'CK-03')['obs'])
    # ——— o gerador ———
    antigo = G.FAQ_TEXTOS['CK-05']['ob']
    G.FAQ_TEXTOS['CK-05']['ob'] = ('ck', 's03')   # o s03 tem seção nos guias (g_motores §1): só os de «boa prática» entram assim
    try:
        G.faq_equipamentos(B)
        recusou = False
    except SystemExit as e:
        recusou = 'boa prática' in str(e)
    finally:
        G.FAQ_TEXTOS['CK-05']['ob'] = antigo
    ok('o gerador recusa citar no FAQ o item do checklist que tem seção nos guias (só os de «boa prática» entram como obs ou atenção)', recusou)
    sem_dsc = dict(B, trechos=[t for t in B['trechos'] if not (t['fonte'] == D['drive']['arquivos']['protocolo'] and t['secao'] == 'DSC')])
    ok('o gerador não cai com a base sem um trecho (a asserção FAQ acusa): sem a seção DSC do protocolo, o EM-03 sai com a base e o FAQ acusa «o trecho de origem não existe»',
       any('faq:EM-03: o trecho de origem não existe' in m for m in C.a_faq(C.Ctx(D, sem_dsc, c['F'], {}, G.faq_equipamentos(sem_dsc)))))
    # ——— amostras plantadas: a FAQ ———
    def it(Q_, i):
        return faq_it(Q_, i)

    def resp(i, velho, novo=''):
        """Amostra da revisão do C11: a resposta de `i` com `velho` trocado por `novo` (o `velho` tem de estar lá: a amostra nunca é vazia)."""
        def muda_resp(D_, B_, Q_):
            x = it(Q_, i)
            assert velho in x['resposta'], (i, velho)
            x['resposta'] = x['resposta'].replace(velho, novo, 1)
        return muda_resp

    def com_obs(i, extra):
        """Amostra da revisão do C11: o `obs` de `i` com a frase do checklist `extra` (o texto do item do checklist que o app avalia, como era antes)."""
        return lambda D_, B_, Q_: it(Q_, i).update({'obs': it(Q_, i)['obs'] + ' ' + extra})
    A = [
        ('chave `conf` num item (o chip de confiabilidade do Avanti)', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'conf': 'alta'}), 'chave de conf'),
        ('chave `lacuna` num item', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'lacuna': 'falta o manual'}), 'chave de lacuna'),
        ('chave `edicao` no topo', lambda D_, B_, Q_: Q_.update({'edicao': '02/10/2026'}), 'chave de edicao'),
        ('anexo `lacunas` no topo', lambda D_, B_, Q_: Q_.update({'lacunas': [{'equip': 'x', 'texto': 'y', 'onde': 'z'}]}), 'chave de lacunas'),
        ('anexo `divergencias` no topo', lambda D_, B_, Q_: Q_.update({'divergencias': []}), 'chave de divergencias'),
        ('anexo `alertas` no topo', lambda D_, B_, Q_: Q_.update({'alertas': []}), 'chave de alertas'),
        ('anexo `invalidos` no topo', lambda D_, B_, Q_: Q_.update({'invalidos': []}), 'chave de invalidos'),
        ('`origem`, `selos`, `decisoes` e `limites` no topo', lambda D_, B_, Q_: Q_.update({'origem': 'x', 'selos': ['y'], 'decisoes': ['z'], 'limites': ['w']}), 'chave de selos'),
        ('versao que não é o hash de 8 hex', lambda D_, B_, Q_: Q_.update({'versao': 'v1'}), 'faq.versao'),
        ('total errado', lambda D_, B_, Q_: Q_.update({'total': 281}), 'faq.total: 281 ≠ 91 itens'),
        ('id repetido', lambda D_, B_, Q_: it(Q_, 'MO-02').update({'id': 'MO-01'}), 'id repetido'),
        ('id fora do contrato', lambda D_, B_, Q_: it(Q_, 'MO-10').update({'id': 'MO-11'}), 'ids ≠ os do contrato'),
        ('`secao` do item fora da seção em que está', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'secao': 3}), 'faq:MO-01.secao: 3'),
        ('`n` da seção fora da posição', lambda D_, B_, Q_: Q_['secoes'][2].update({'n': 7}), 'faq.secoes[2].n'),
        ('item que sai de todas as seções', lambda D_, B_, Q_: Q_['secoes'][1]['ids'].remove('MO-05'), 'não partem os itens'),
        ('2 variantes', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'variantes': it(Q_, 'MO-01')['variantes'][:2]}), 'faq:MO-01.variantes'),
        ('variante igual à pergunta', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'variantes': [it(Q_, 'MO-01')['pergunta']] + it(Q_, 'MO-01')['variantes'][1:]}), 'faq:MO-01.variantes'),
        ('passos vazio (a chave se omite)', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'passos': []}), 'faq:MO-01.passos'),
        ('título repetido', lambda D_, B_, Q_: it(Q_, 'MO-02').update({'titulo': it(Q_, 'MO-01')['titulo']}), 'titulo repetido'),
        ('pergunta repetida', lambda D_, B_, Q_: it(Q_, 'MO-02').update({'pergunta': it(Q_, 'MO-01')['pergunta']}), 'pergunta repetida'),
        ('`emerg` num item que não é EM', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'emerg': True}), 'faq:MO-01.emerg'),
        ('cartão EM sem `emerg`', lambda D_, B_, Q_: it(Q_, 'EM-01').update({'emerg': False}), 'faq:EM-01.emerg'),
        ('`seguranca` falso', lambda D_, B_, Q_: it(Q_, 'EM-01').update({'seguranca': False}), 'faq:EM-01.seguranca'),
        ('`ver` com id que não existe', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'ver': ['XX-99']}), 'faq:MO-01.ver'),
        ('`ver` que cita o próprio item', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'ver': ['MO-01']}), 'faq:MO-01.ver'),
        ('fonte do tipo «Manual»', lambda D_, B_, Q_: it(Q_, 'MO-01')['fontes'][0].update({'tipo': 'Manual'}), "fontes[0].tipo: 'Manual'"),
        ('fonte do tipo «Foto»', lambda D_, B_, Q_: it(Q_, 'MO-01')['fontes'].append({'tipo': 'Foto', 'texto': 'Boa prática'}), "fontes[1].tipo: 'Foto'"),
        ('fonte com seção que não existe na base', lambda D_, B_, Q_: it(Q_, 'MO-01')['fontes'].append({'tipo': 'Guia de bordo', 'texto': 'Guia de bordo — Motores Cummins §99 · Nada'}),
         'não é uma seção da base'),
        ('1ª fonte de outro id', lambda D_, B_, Q_: it(Q_, 'MO-01')['fontes'][0].update({'texto': it(Q_, 'MO-02')['fontes'][0]['texto']}), 'não é a seção do id'),
        ('1ª fonte que é a boa prática', lambda D_, B_, Q_: it(Q_, 'CK-03')['fontes'].reverse(), 'a 1ª fonte é a seção do guia'),
        ('item sem fontes', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'fontes': []}), 'faq:MO-01.fontes'),
        ('número novo num passo (7 vezes)', lambda D_, B_, Q_: it(Q_, 'MO-02')['passos'].append('Repita 7 vezes.'), 'número 7 que não está na seção citada'),
        ('número novo com milhar (2.600 rpm no gerador)', lambda D_, B_, Q_: it(Q_, 'GE-02').update({'acao': 'Segure até 2.600 rpm.'}), 'número 2.600'),
        ('número novo numa variante', lambda D_, B_, Q_: it(Q_, 'MO-08')['variantes'].__setitem__(0, 'horímetro a cada 500 h'), 'número 500'),
        ('item de segurança sem `seguranca` (o trecho tem)', lambda D_, B_, Q_: it(Q_, 'MO-04').pop('seguranca'), 'nada com seguranca vai à IA'),
        ('cartão EM-02 sem o rótulo no fim', lambda D_, B_, Q_: it(Q_, 'EM-02').update({'resposta': P['panpan']}), 'a resposta não termina com o rótulo'),
        ('rótulo numa resposta cujo trecho não o tem', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'resposta': it(Q_, 'MO-01')['resposta'] + ' ' + C.cap(C.ROTULO) + '.'}), 'rótulo do procedimento padrão numa resposta'),
        ('resposta de segurança com mais de 800 letras', lambda D_, B_, Q_: it(Q_, 'EM-02').update({'resposta': P['panpan'] + ' ' + 'Repita a chamada. ' * 50 + C.cap(C.ROTULO) + '.'}),
         'letras com seguranca (máximo 800'),
        ('EM com minutos', lambda D_, B_, Q_: it(Q_, 'EM-06')['passos'].append('Espere 5 minutos.'), 'faq:EM-06.passos[3]: minutos'),
        ('EM com pressão em bar', lambda D_, B_, Q_: it(Q_, 'EM-06').update({'atencao': 'Pressão de 3,4 bar.'}), 'faq:EM-06.atencao: " bar"'),
        ('EM com número de pessoas', lambda D_, B_, Q_: it(Q_, 'EM-01')['passos'].__setitem__(5, 'PESSOAS A BORDO: 4'), 'faq:EM-01.passos[5]: número de pessoas'),
        ('EM com lugar a bordo', lambda D_, B_, Q_: it(Q_, 'EM-09').update({'obs': 'Coletes no paiol de proa.'}), 'faq:EM-09.obs: lugar a bordo'),
        ('EM com o registro da embarcação', lambda D_, B_, Q_: it(Q_, 'EM-04').update({'obs': 'Registro %s.' % D_['embarcacao']['registro']}), 'faq:EM-04.obs: dado gerado da embarcação (registro)'),
        ('EM com a posição na pergunta', lambda D_, B_, Q_: it(Q_, 'EM-01').update({'pergunta': 'Chamada de socorro a 3 mn da costa?'}), 'faq:EM-01.pergunta'),
        ('glossário sem um termo', lambda D_, B_, Q_: Q_['glossario'].pop(2), 'faq.glossario: os termos precisam ser'),
        ('MMSI do glossário sem o texto MMSI_RADIO', lambda D_, B_, Q_: next(g for g in Q_['glossario'] if g['termo'] == 'MMSI').update({'texto': 'Identificação do rádio.'}), 'sem o texto MMSI_RADIO'),
        ('MOB do glossário sem o rótulo', lambda D_, B_, Q_: next(g for g in Q_['glossario'] if g['termo'] == 'MOB').update({'texto': 'Homem ao mar.'}), 'glossario.MOB.texto: sem o rótulo'),
        ('EPIRB do glossário sem a nota da etiqueta', lambda D_, B_, Q_: next(g for g in Q_['glossario'] if g['termo'] == 'EPIRB').update({'texto': 'Radiobaliza. ' + C.cap(C.ROTULO) + '.'}),
         'glossario.EPIRB.texto: sem o rótulo e a nota da etiqueta'),
        # ——— revisão do C11: a resposta (lida inteira pela tela e pela voz) mantém a frase que escala (MAYDAY) ou condiciona («e há fogo no motor») ———
        ('EM-04 (homem ao mar) sem «Se perder de vista: MAYDAY…» na resposta',
         resp('EM-04', ' Se perder de vista: MAYDAY no canal 16 com a posição da marca MOB lida no plotter.'), 'faq:EM-04.resposta: corta a frase do trecho de origem que escala ou condiciona «Se perder de vista'),
        ('EM-05 (incêndio) sem a condição «e há fogo no motor» antes do disparo manual',
         resp('EM-05', 'sozinho e há fogo no motor,', 'sozinho,'), 'faq:EM-05.resposta: corta a frase do trecho de origem que escala ou condiciona «Se o sistema não disparou sozinho e há fogo'),
        ('EM-05 sem «Fogo que não apaga: MAYDAY…»', resp('EM-05', ' Fogo que não apaga: MAYDAY no canal 16 e prepare o abandono.'),
         'faq:EM-05.resposta: corta a frase do trecho de origem que escala ou condiciona «Fogo que não apaga'),
        ('SF-01 sem a condição «e há fogo no motor» (descarregaria o sistema só pelo alarme)', resp('SF-01', 'sozinho e há fogo no motor,', 'sozinho,'),
         'faq:SF-01.resposta: corta a frase do trecho de origem que escala ou condiciona «Se o sistema não disparou sozinho e há fogo'),
        ('SF-01 sem «Fogo que não apaga: MAYDAY…»', resp('SF-01', ' Fogo que não apaga: MAYDAY no canal 16 e prepare o abandono.'),
         'faq:SF-01.resposta: corta a frase do trecho de origem que escala ou condiciona «Fogo que não apaga'),
        ('SF-03 sem «se o fogo voltar, MAYDAY…» (a oração depois do ponto e vírgula)', resp('SF-03', ' Se o fogo voltar, MAYDAY no canal 16.'),
         'faq:SF-03.resposta: corta a frase do trecho de origem que escala ou condiciona «se o fogo voltar, MAYDAY'),
        ('EM-08 (EPIRB) sem «Só em perigo grave e iminente, depois do MAYDAY»', resp('EM-08', 'Só em perigo grave e iminente, depois do MAYDAY (ou sem rádio). '),
         'faq:EM-08.resposta: corta a frase do trecho de origem que escala ou condiciona «Só em perigo grave e iminente'),
        ('EP-01 sem «Só em perigo grave e iminente, depois do MAYDAY»', resp('EP-01', 'Só em perigo grave e iminente, depois do MAYDAY (ou sem rádio). '),
         'faq:EP-01.resposta: corta a frase do trecho de origem que escala ou condiciona «Só em perigo grave e iminente'),
        ('PO-04 só com a 1ª frase (sem «Água subindo mesmo assim: MAYDAY…»)', resp('PO-04', ' Água subindo mesmo assim: MAYDAY no canal 16.'),
         'faq:PO-04.resposta: corta a frase do trecho de origem que escala ou condiciona «Água subindo mesmo assim'),
        ('EM-06 sem «Água subindo mesmo assim: MAYDAY…»', resp('EM-06', ' Água subindo mesmo assim: MAYDAY no canal 16.'),
         'faq:EM-06.resposta: corta a frase do trecho de origem que escala ou condiciona «Água subindo mesmo assim'),
        ('EL-05 (DISTRESS) sem «Depois do alerta, faça o MAYDAY por voz»', resp('EL-05', ' Depois do alerta, faça o MAYDAY por voz no canal 16.'),
         'faq:EL-05.resposta: corta a frase do trecho de origem que escala ou condiciona «Depois do alerta, faça o MAYDAY'),
        ('EM-01 (roteiro) sem a palavra MAYDAY na resposta', resp('EM-01', 'fale MAYDAY três vezes', 'fale três vezes'),
         'faq:EM-01.resposta: corta a frase do trecho de origem que escala ou condiciona «Diga devagar'),
        # ——— 2ª revisão do C11: a proibição, a cautela de liberar, a ventilação e o SOS do app também ficam na resposta; a ação condicionada leva a condição ———
        ('EM-01 (MAYDAY) sem «Só em perigo grave e iminente.» na resposta', resp('EM-01', 'Só em perigo grave e iminente. '),
         'faq:EM-01.resposta: corta a frase do trecho de origem que escala ou condiciona «Só em perigo grave e iminente.'),
        ('EM-05 sem «Não abra o acesso ao motor depois da descarga…»', resp('EM-05', ' Não abra o acesso ao motor depois da descarga: espere o tempo indicado na etiqueta do sistema e o motor esfriar.'),
         'faq:EM-05.resposta: corta a frase do trecho de origem que escala ou condiciona «Não abra o acesso ao motor depois da descarga'),
        ('SF-01 sem «Não abra o acesso ao motor depois da descarga…»', resp('SF-01', ' Não abra o acesso ao motor depois da descarga: espere o tempo indicado na etiqueta do sistema e o motor esfriar.'),
         'faq:SF-01.resposta: corta a frase do trecho de origem que escala ou condiciona «Não abra o acesso ao motor depois da descarga'),
        ('SF-03 sem «não abra o acesso ao motor» (a oração entre «;»)', resp('SF-03', ' e não abra o acesso ao motor;', ';'),
         'faq:SF-03.resposta: corta a frase do trecho de origem que escala ou condiciona «não abra o acesso ao motor»'),
        ('SF-03 sem «e só então libere o acesso, com o extintor portátil à mão»', resp('SF-03', ' e só então libere o acesso, com o extintor portátil à mão'),
         'faq:SF-03.resposta: corta a frase do trecho de origem que escala ou condiciona «espere o tempo indicado na etiqueta do sistema e só então'),
        ('EM-08 (EPIRB) sem «Não desligue até o resgate.» (a resposta traz só «Disparo por engano: desligue…»)', resp('EM-08', ' Não desligue até o resgate.'),
         'faq:EM-08.resposta: corta a frase do trecho de origem que escala ou condiciona «Não desligue até o resgate.'),
        ('EP-01 sem «Não desligue até o resgate.»', resp('EP-01', ' Não desligue até o resgate.'),
         'faq:EP-01.resposta: corta a frase do trecho de origem que escala ou condiciona «Não desligue até o resgate.'),
        ('GE-01 sem a ventilação «se houver cheiro de combustível»', resp('GE-01', ' Ligue a ventilação do compartimento por alguns minutos se houver cheiro de combustível.'),
         'faq:GE-01.resposta: corta a frase do trecho de origem que escala ou condiciona «Ligue a ventilação do compartimento'),
        ('PO-02 sem «é alagamento: use o SOS do app»', resp('PO-02', ' Nível subindo com a bomba ligada ou água entrando é alagamento: use o SOS do app.'),
         'faq:PO-02.resposta: corta a frase do trecho de origem que escala ou condiciona «nível subindo com a bomba ligada'),
        ('MO-05 sem «Nunca abra a tampa do arrefecimento com o motor quente.»', resp('MO-05', ' Nunca abra a tampa do arrefecimento com o motor quente.'),
         'faq:MO-05.resposta: corta a frase do trecho de origem que escala ou condiciona «Nunca abra a tampa'),
        ('GE-05 sem «Nunca abra a tampa do arrefecimento com o motor quente.»', resp('GE-05', ' Nunca abra a tampa do arrefecimento com o motor quente.'),
         'faq:GE-05.resposta: corta a frase do trecho de origem que escala ou condiciona «Nunca abra a tampa'),
        ('SF-02 com a linha de ação sem a condição (só «disparo manual»)', lambda D_, B_, Q_: it(Q_, 'SF-02').update({'acao': 'Motores e gerador desligados, ventilação cortada e disparo manual.'}),
         'faq:SF-02.acao: manda fazer «disparo manual» sem a condição «há fogo no motor»'),
        ('SF-02 com o último passo «Use o disparo manual.» e nenhum passo antes com a condição', lambda D_, B_, Q_: it(Q_, 'SF-02')['passos'].__setitem__(2, 'Use o disparo manual.'),
         'faq:SF-02.passos[2]: manda fazer «disparo manual» sem a condição «há fogo no motor»'),
        ('EM-05 com o passo do disparo manual sem a condição', lambda D_, B_, Q_: it(Q_, 'EM-05')['passos'].__setitem__(1, 'Use o disparo manual.'),
         'faq:EM-05.passos[1]: manda fazer «disparo manual» sem a condição «há fogo no motor»'),
        ('EM-05 com o disparo manual na `atencao`, sem a condição', lambda D_, B_, Q_: it(Q_, 'EM-05').update({'atencao': 'Use o disparo manual.'}),
         'faq:EM-05.atencao: manda fazer «disparo manual» sem a condição «há fogo no motor»'),
        ('SF-01 com a resposta mandando o disparo manual sem a condição', resp('SF-01', 'se o sistema não disparou sozinho e há fogo no motor, use o disparo manual', 'use o disparo manual'),
         'faq:SF-01.resposta: manda fazer «disparo manual» sem a condição «há fogo no motor»'),
        # ——— revisão do C11: o checklist entra como ordem de conferência, nunca como o estado que o app avalia ———
        ('CK-03 com «Nenhuma tarefa de segurança atrasada.» (o porao-teste está atrasado na agenda)', com_obs('CK-03', 'Nenhuma tarefa de segurança atrasada.'),
         'faq:CK-03.obs: repete o item s12 do checklist'),
        ('CK-03 com «Nenhum alerta ativo no painel.» (o laço tem AVISO)', com_obs('CK-03', 'Nenhum alerta ativo no painel.'), 'faq:CK-03.obs: repete o item s02 do checklist'),
        ('CK-03 com «Documentos em dia (TIE, seguro, Licença de Estação).»', com_obs('CK-03', 'Documentos em dia (TIE, seguro, Licença de Estação).'),
         'faq:CK-03.obs: repete o item s11 do checklist'),
        ('CK-05 com «Motores desligados.» (estado atual com o barco navegando)', com_obs('CK-05', 'Motores desligados.'), 'faq:CK-05.obs: repete o item a01 do checklist'),
        ('CK-05 com «Nível de diesel anotado antes.»', com_obs('CK-05', 'Nível de diesel anotado antes.'), 'faq:CK-05.obs: repete o item a03 do checklist'),
        ('CK-07 com «Maré e vento conferidos (previsão da Marinha).»', com_obs('CK-07', 'Maré e vento conferidos (previsão da Marinha).'), 'faq:CK-07.obs: repete o item f06 do checklist'),
        ('CK-07 com «Motores em neutro e deriva conferida.»', com_obs('CK-07', 'Motores em neutro e deriva conferida.'), 'faq:CK-07.obs: repete o item f04 do checklist'),
    ]
    for o_que, muda_, espera in A:
        c11_planta('FAQ', o_que, muda_, espera)
    c11_planta('FAQ', 'a repetição da pergunta de outro item é a única violação nova', lambda D_, B_, Q_: it(Q_, 'MO-02').update({'pergunta': it(Q_, 'MO-01')['pergunta']}),
               'pergunta repetida', so_uma=False)
    # ——— amostras plantadas: as outras asserções, agora sobre o FAQ ———
    ix = c11_ix
    B1 = [
        ('TERMOS', 'rótulo «DEMO» na resposta', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'resposta': it(Q_, 'MO-01')['resposta'] + ' (DEMO)'}), 'ROTULOS: faq:itens[%d].resposta' % ix('MO-01')),
        ('TERMOS', 'selo «SEM DADOS» no passo', lambda D_, B_, Q_: it(Q_, 'GE-02')['passos'].append('SEM DADOS'), 'ROTULOS: faq:itens[%d].passos[3]' % ix('GE-02')),
        ('TERMOS', '«os dados são fictícios» (AUTENTICIDADE)', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'obs': 'Os dados são fictícios.'}), 'AUTENTICIDADE: faq:itens[%d].obs' % ix('MO-01')),
        ('TERMOS', 'preço (DINHEIRO)', lambda D_, B_, Q_: it(Q_, 'MO-07').update({'obs': 'Custa R$ 1.200.'}), 'DINHEIRO: faq:itens[%d].obs' % ix('MO-07')),
        ('TERMOS', 'telefone (PESSOAIS)', lambda D_, B_, Q_: it(Q_, 'CL-04').update({'senao': 'Ligue para (47) 99999-0000.'}), 'PESSOAIS: faq:itens[%d].senao' % ix('CL-04')),
        ('TERMOS', 'equipamento de salvatagem com lugar (LOCAL_SEGURANCA)', lambda D_, B_, Q_: it(Q_, 'CK-03').update({'obs': 'Os coletes ficam no paiol de proa.'}),
         'LOCAL_SEGURANCA: faq:itens[%d].obs' % ix('CK-03')),
        ('TERMOS', '«n/d» (VAZIOS)', lambda D_, B_, Q_: it(Q_, 'MO-08').update({'obs': 'n/d'}), 'VAZIOS: faq:itens[%d].obs' % ix('MO-08')),
        ('TERMOS', 'selo A CONFERIR (ANEXO)', lambda D_, B_, Q_: it(Q_, 'MO-08').update({'obs': 'A CONFERIR'}), 'ANEXO: faq:itens[%d].obs' % ix('MO-08')),
        ('NULO', 'campo vazio num item (`acao` vazia)', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'acao': ''}), "faq:itens[%d].acao: ''" % ix('MO-01')),
        ('NULO', 'lista vazia no item (`ver` vazio)', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'ver': []}), 'faq:itens[%d].ver: lista vazia' % ix('MO-01')),
        ('NULO', 'null no item', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'obs': None}), 'faq:itens[%d].obs: None' % ix('MO-01')),
        ('TAMANHO', 'FAQ acima de 100 KB', lambda D_, B_, Q_: Q_.update({'sobra': 'abc ' * 30000}), 'faq-equipamentos.json'),
        ('COORD_TEXTO', 'coordenada em graus e minutos no passo', lambda D_, B_, Q_: it(Q_, 'GE-02')['passos'].append("Fundeado em 26°59,6'S."), 'faq:itens[%d].passos[3]' % ix('GE-02')),
        ('GRAFIA_SEAFIRE', '«Sea Fire» no título', lambda D_, B_, Q_: it(Q_, 'SF-01').update({'titulo': 'Disparo do Sea Fire'}), 'faq:itens[%d].titulo' % ix('SF-01')),
        ('GRAFIA_SEAFIRE', 'chave com «sea_fire»', lambda D_, B_, Q_: it(Q_, 'SF-01').update({'sea_fire': 'x'}), 'sea_fire'),
        ('CALADO_FORA', '«calado» no passo (até a Fase 3)', lambda D_, B_, Q_: it(Q_, 'EL-08')['passos'].append('Confira o calado.'), 'faq:EL-08: "calado"'),
        ('ESTABILIZADOR_12V', 'energia AC num passo do estabilizador', lambda D_, B_, Q_: it(Q_, 'SK-02')['passos'].append('Ligue com energia AC.'), 'energia AC num texto do estabilizador'),
        ('LOCAL_VOCAB', '«boia» num item fora do EM-04, EM-09 e CK-03', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'obs': 'Jogue a boia.'}), 'faq:MO-01: "boia" fora de origem'),
        ('LOCAL_VOCAB', 'lugar de salvatagem em qualquer ordem', lambda D_, B_, Q_: it(Q_, 'CK-03').update({'obs': 'No paiol de proa ficam os coletes.'}), 'equipamento de salvatagem e lugar a bordo na mesma frase'),
        ('ROTULO_SEGURANCA', 'SF-01 sem o rótulo no fim da resposta', lambda D_, B_, Q_: it(Q_, 'SF-01').update({'resposta': 'Desligue motores e gerador.'}), 'faq:SF-01 sem o rótulo no fim da resposta'),
        ('ROTULO_SEGURANCA', 'EM-09 só com o rótulo, sem a nota da etiqueta', lambda D_, B_, Q_: it(Q_, 'EM-09').update({'resposta': P['salvatagem'] + ' ' + C.cap(C.ROTULO) + '.'}), 'faq:EM-09 sem o rótulo no fim da resposta'),
        ('SEGURANCA_MARCADA', 'item com a palavra «extintor» sem seguranca', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'obs': 'Extintor à mão.'}), 'faq:MO-01 casa a SEGURANCA_PALAVRAS sem seguranca'),
        ('SEGURANCA_MARCADA', 'CK-03 sem seguranca (o mínimo do §1.5/§1.6)', lambda D_, B_, Q_: it(Q_, 'CK-03').pop('seguranca'), 'faq:CK-03'),
        ('SEGURANCA_MARCADA', 'EM-05 sem seguranca', lambda D_, B_, Q_: it(Q_, 'EM-05').pop('seguranca'), 'faq:EM-05'),
        ('SEGURANCA_MARCADA', 'SF-04 sem seguranca', lambda D_, B_, Q_: it(Q_, 'SF-04').pop('seguranca'), 'faq:SF-04'),
        ('SEGURANCA_MARCADA', 'EP-02 sem seguranca', lambda D_, B_, Q_: it(Q_, 'EP-02').pop('seguranca'), 'faq:EP-02'),
        ('SEGURANCA_SEM_MODELO', 'modelo do EPIRB num passo de outro item', lambda D_, B_, Q_: it(Q_, 'MO-01')['passos'].append('Confira o SafeSea.'), 'fabricante ou modelo de equipamento de segurança [SafeSea]'),
        ('SEGURANCA_SEM_MODELO', 'fabricante do EPIRB no EP-01', lambda D_, B_, Q_: it(Q_, 'EP-01').update({'obs': 'Fabricante Ocean Signal.'}), 'fabricante ou modelo de equipamento de segurança [Ocean Signal]'),
        ('SEGURANCA_SEM_MODELO', 'validade (data) no EP-04', lambda D_, B_, Q_: it(Q_, 'EP-04').update({'obs': 'Vence em 03/2028.'}), 'validade ou data num texto do EPIRB'),
        ('SEGURANCA_SEM_MODELO', 'lugar a bordo no SF-02', lambda D_, B_, Q_: it(Q_, 'SF-02').update({'obs': 'O acesso fica na praça de máquinas.'}), 'lugar a bordo num texto do EPIRB'),
        ('SEM_INDICATIVO', 'chave de telefone no item', lambda D_, B_, Q_: it(Q_, 'CL-04').update({'telefone': 'x'}), 'chave de telefone'),
        ('SEM_INDICATIVO', 'indicativo no texto', lambda D_, B_, Q_: it(Q_, 'EL-04').update({'obs': 'Indicativo PU2ABC.'}), 'PU2ABC'),
        ('MMSI9', 'nove dígitos no item', lambda D_, B_, Q_: it(Q_, 'EL-05').update({'obs': 'MMSI 710123456.'}), 'faq:itens[%d].obs' % ix('EL-05')),
        ('AFIRMA_REAL', '«os dados são reais»', lambda D_, B_, Q_: it(Q_, 'MO-01').update({'obs': 'Os dados são reais.'}), 'faq:itens[%d].obs' % ix('MO-01')),
        ('IDS', 'faq do checklist que não existe no FAQ', lambda D_, B_, Q_: Q_['itens'].remove(it(Q_, 'MO-01')), 'checklists.itens.saida.s03.faq fora do FAQ'),
    ]
    for regra, o_que, muda_, espera in B1:
        c11_planta(regra, o_que, muda_, espera)
    # ——— o gerador reprova (main() devolve 1 e não grava nada) ———
    def rodar_faq(muda_, pasta):
        orig = G.faq_equipamentos
        G.faq_equipamentos = lambda B_=None: (lambda Q_: (muda_(Q_), Q_)[1])(copy.deepcopy(orig(B_)))
        opcionais = {k: os.environ.pop(k) for k in ('CAPITAO_LISTAS_PRIVADAS', 'CAPITAO_AVANTI') if k in os.environ}
        try:
            with contextlib.redirect_stdout(io.StringIO()) as o, contextlib.redirect_stderr(io.StringIO()) as e:
                rc = G.main(['--saida', pasta])
        finally:
            G.faq_equipamentos = orig
            os.environ.update(opcionais)
        return rc, o.getvalue() + e.getvalue()
    for n_, (nome, muda_, esperado) in enumerate((('número novo num passo', lambda Q_: it(Q_, 'MO-02')['passos'].append('Repita 7 vezes.'), 'FAQ'),
                                                  ('chave `conf` no item', lambda Q_: it(Q_, 'MO-01').update({'conf': 'alta'}), 'FAQ'),
                                                  ('EM-01 sem seguranca (SEGURANCA_MARCADA)', lambda Q_: it(Q_, 'EM-01').pop('seguranca'), 'SEGURANCA_MARCADA'),
                                                  ('EM-04 sem a escalada «Se perder de vista: MAYDAY…» na resposta (revisão do C11)',
                                                   lambda Q_: it(Q_, 'EM-04').update({'resposta': it(Q_, 'EM-04')['resposta'].replace(' Se perder de vista: MAYDAY no canal 16 com a posição da marca MOB lida no plotter.', '')}), 'FAQ'),
                                                  ('SF-02 com a linha de ação do disparo manual sem a condição (2ª revisão do C11)',
                                                   lambda Q_: it(Q_, 'SF-02').update({'acao': 'Use o disparo manual.'}), 'FAQ'),
                                                  ('EP-01 sem «Não desligue até o resgate.» na resposta (2ª revisão do C11)',
                                                   lambda Q_: it(Q_, 'EP-01').update({'resposta': it(Q_, 'EP-01')['resposta'].replace(' Não desligue até o resgate.', '')}), 'FAQ'),
                                                  ('CK-03 com o texto do ✓ «Nenhuma tarefa de segurança atrasada.» (revisão do C11)',
                                                   lambda Q_: it(Q_, 'CK-03').update({'obs': it(Q_, 'CK-03')['obs'] + ' Nenhuma tarefa de segurança atrasada.'}), 'FAQ'),
                                                  ('preço no item (a DINHEIRO reprova já; a TERMOS em relatório, não)',
                                                   lambda Q_: it(Q_, 'MO-01').update({'resposta': it(Q_, 'MO-01')['resposta'] + ' Custa R$ 9,90.'}), 'TERMOS'),
                                                  ('«DEMO» no item (relatório: não reprova, grava)', None, None))):
        if muda_ is None:   # o relatório da TERMOS não reprova: main() devolve 0 e grava
            pasta = os.path.join(tmp, 'faq-%d' % n_)
            rc, saida = rodar_faq(lambda Q_: it(Q_, 'MO-01').update({'resposta': it(Q_, 'MO-01')['resposta'] + ' (DEMO)'}), pasta)
            ok('FAQ plantado (%s): main() devolve 0 e grava (a varredura de termos fica em relatório até o C12)' % nome,
               rc == 0 and os.path.isfile(os.path.join(pasta, 'faq-equipamentos.json')), (rc, saida[-300:]))
            continue
        pasta = os.path.join(tmp, 'faq-%d' % n_)
        rc, saida = rodar_faq(muda_, pasta)
        ok('FAQ plantado (%s): main() devolve 1 e não grava nada (%s)' % (nome, esperado), rc == 1 and not os.path.exists(pasta) and esperado in saida, (rc, saida[-300:]))
    pasta = os.path.join(tmp, 'faq-bom')
    rc, saida = rodar_faq(lambda Q_: None, pasta)
    ok('o FAQ de hoje, sem mudança: main() devolve 0 e grava o faq-equipamentos.json igual ao de G.faq_equipamentos()',
       rc == 0 and open(os.path.join(pasta, 'faq-equipamentos.json'), encoding='utf-8').read() == G.gera_faq(Q), (rc, saida[-300:]))


AMOSTRAS['FAQ'] = (lambda r: hoje_faq(lambda k: faq_it(k['faq'], 'MO-02').update({'pergunta': faq_it(k['faq'], 'MO-01')['pergunta']}) if r else None),
                   'faq:MO-02.pergunta repetida')   # C11: o FAQ de hoje, com a pergunta do MO-01 também no MO-02


def main():
    with tempfile.TemporaryDirectory(prefix='capitao-gerador-') as tmp:
        determinismo(tmp)
        limpeza(tmp)
        copias()
        palavras()
        rotulos_c2()
        rodape_real()
        amostras()
        porao_e_lugar()
        seguranca_sem_modelo()
        grafia_seafire()
        c8_rota_e_replay()
        c9_historico()
        c10_funcoes()
        c11_faq(tmp)
        modelos_sinteticos()
        reprova(tmp)
    print('\n%s — %d falha(s)' % ('OK' if not falhas else 'FALHOU', falhas))
    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main())
