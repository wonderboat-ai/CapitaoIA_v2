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
    for rel in ('capitao-dados.js', 'base-conhecimento.json'):
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
    linhas = js[js.find('window.CapitaoDados = '):].split('\n')   # sem o comentário do cabeçalho
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
    return C.verifica(k['D'], k['B'], k['F'], G.saidas(k['D'], k['B']), k['faq'], k['rodape'], k['listas'], k['avanti'], k.get('const', CONST))


def com_replay(k):
    """O D de hoje com um replay mínimo e coerente (campos, chaves, limites, janela, contadores) e o guia das faixas na base."""
    D = k['D']
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
    k = com_replay(k)
    k['D']['rota'] = {
        'base': {'id': 'base', 'nome': 'Barra Sul', 'rel': 'da Barra Sul', 'perto': 'na saída da Barra Sul', 'prof_m': 8},
        'pontos': [{'id': 'cabras', 'nome': 'Ilha das Cabras', 'rel': 'da Ilha das Cabras', 'perto': 'ao largo da Ilha das Cabras', 'prof_m': 12}],
        'destino': {'id': 'cabras', 'nome': 'Ilha das Cabras', 'caminho': 'a caminho da Ilha das Cabras'},
        'volta': {'nome': 'Barra Sul (base)', 'caminho': 'a caminho da Barra Sul'},
        'pernas': [{'de': 'base', 'para': 'cabras', 'mn': 1.0, 'rumo': 50}, {'de': 'cabras', 'para': 'base', 'mn': 1.0, 'rumo': 230}],
        'distancia_mn': 2.0, 'circuitos_dia': 19, 'fator': 0.122, 'guinada_max_gps': 3}
    return k


def com_historico(k):
    k = com_replay(k)
    k['D']['historico'] = {
        'desvios': {'bateria_0_tensao_v': {'escala': 100, 'd': [0, 3, -6, 2]}},
        'sazonal': {'temp_ar_externo_c': {'escala': 10, 'd': [0] * 73}},
        'janelas': {'150S': {'passo_s': 1, 'n': 150}},
        'metricas': {'b24': ['bateria_0_tensao_v'], 'arref': ['motor_be_arref_c']}, 'so150': ['arref']}
    return k


def equip_completo(k):
    for e in k['D']['equipamentos']:
        e.update({'fabricante': e.get('fabricante') or 'Fabricante', 'modelo': 'Modelo 100', 'qtd': 1, 'guia': 'g_gerador'})
    return k


def poe(lista, i, **kw):
    lista[i] = dict(lista[i], **kw)


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
    'AGENDA': (lambda r: (lambda k: (k['D']['agenda'].append({'id': 'seafire-inspecao', 't': 'Inspeção anual do sistema fixo de supressão', 'sistema': 'seafire',
                                                               'meses': 12, 'ultimaHa': 370 if r else 360, 'venceEm': -5 if r else 5,
                                                               'palavras': ['inspecao do seafire'], 'seguranca': True, 'equip': 'Sistema fixo'}), k)[1])(hoje()),
               'tarefa de salvatagem atrasada'),
    'HISTORICO': (lambda r: (lambda k: (k['D']['historico']['desvios']['bateria_0_tensao_v'].update({'d': [0, -400] if r else [0, -6]}), k)[1])(com_historico(hoje())), 'o mínimo cruza'),
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
    # C5: antes do D.replay (C8), a FONTE_LIMITES confere a constante LIMITES do gerador contra os guias; depois, as duas são uma só.
    ('FONTE_LIMITES', 'constante LIMITES (C5) com número que o guia não tem',
     lambda r: (lambda k: (k.update({'const': dict(CONST, LIMITES=limites_com(('motor_bb_arref_c', 'critico', 'acima'), 98 if r else 97))}), k)[1])(hoje()),
     'limites.motor_bb_arref_c: Guia de bordo — Motores Cummins §9 · Faixas de operação sem os números'),
    ('FONTE_LIMITES', 'constante LIMITES (C5) apontando para um § que não existe',
     lambda r: (lambda k: (k.update({'const': dict(CONST, LIMITES=limites_com(('gerador_kw', 'fonte'),
                                                                           G.ARQ['g_gerador'] + (' §12 · Carga' if r else ' §9 · Potência e carga')))}), k)[1])(hoje()),
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
     lambda r: (lambda k: (k['D']['agenda'][0].setdefault('palavras', []).append('inspecao do sea fire' if r else 'inspecao do seafire'), k)[1])(hoje()),
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


def planta(nome, o_que, monta, espera):
    """A amostra plantada aparece como violação nova; numa estrutural, fora das pendências congeladas (reprova o gerador)."""
    bom, mau = verifica(monta(False)), verifica(monta(True))
    novos = [m for m in mau[nome] if m not in bom[nome]]
    achados = [m for m in novos if espera in m]
    if achados and all(C.em_relatorio(nome, m) for m in achados):   # na TERMOS, cada regex decide (PESSOAIS, DINHEIRO e LOCAL_SEGURANCA reprovam)
        modo, reprova = ' (em relatório até o %s)' % C.RELATORIO[nome], True
    else:
        livres = C.separa({nome: mau[nome]})[0].get(nome, [])
        modo, reprova = ' e reprova (fora das pendências)', any(espera in m for m in livres)
    ok('%s: acusa a amostra plantada%s%s' % (nome, o_que, modo),
       len(mau[nome]) > len(bom[nome]) and any(espera in m for m in novos) and reprova,
       {'novas': novos[:3], 'antes': len(bom[nome]), 'depois': len(mau[nome]), 'reprova': reprova})


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


def registro_tie(V0):
    """Revisão final do C4: a REGISTRO cruza o registro com o numero do documento de id "tie" (§1.2, §1.8). O TIE de hoje não tem id
    (o C7 o regrava) e o cruzamento nunca rodava: o registro preenchido ao lado de "SEM DADOS: TIE" no mesmo dado não reprovava
    nada, e o C7 podia esquecer o id ou o número sem que a PENDENTES o obrigasse. Na simulação, a falta do documento é a violação
    congelada do C7; o TIE certo sem tirar a linha da PENDENTES e o TIE errado reprovam (os dois pelo main(), em reprova())."""
    reg = G.EMBARCACAO['registro']
    ausente = [m for m in V0['REGISTRO'] if m.startswith('documentos[tie] ausente')]
    novas, conhecidas, velhas = C.separa({'REGISTRO': V0['REGISTRO']})
    ok('REGISTRO: o TIE de hoje (sem id) é a única violação, congelada na PENDENTES do C7',
       V0['REGISTRO'] == ausente and len(ausente) == 1 and not novas and not velhas and conhecidas == {'REGISTRO': {'C7': 1}},
       (V0['REGISTRO'], novas, velhas, conhecidas))

    def tie(**campos):
        """O dado de hoje com o 1º documento (o TIE) mudado: o valor None tira a chave."""
        k = hoje()
        k['D']['documentos'][0].update({c: v for c, v in campos.items() if v is not None})
        for c, v in campos.items():
            if v is None:
                k['D']['documentos'][0].pop(c, None)
        return k
    for o_que, k, trecho, nova in (
            ('numero = o registro, sem id (o C7 esquece o id)', tie(numero=reg), 'documentos[tie] ausente', False),
            ('numero diferente do registro, sem id', tie(numero='CIA-99-9999'), 'documentos[tie] ausente', False),
            ('id "tie" e numero diferente do registro', tie(id='tie', numero='CIA-99-9999'), 'documentos[tie].numero diferente', True),
            ('id "tie" e sem numero (o C7 esquece o número)', tie(id='tie', numero=None), 'documentos[tie].numero ausente', True)):
        V = verifica(k)['REGISTRO']
        livres = C.separa({'REGISTRO': V})[0].get('REGISTRO', [])
        ok('REGISTRO: TIE com %s acusa%s' % (o_que, ' e reprova (fora das pendências)' if nova else ' (é a pendência do C7)'),
           any(trecho in m for m in V) and bool(livres) == nova, (V, livres))
    V = verifica(tie(id='tie', numero=reg))['REGISTRO']
    velhas = C.separa({'REGISTRO': V})[2]
    ok('REGISTRO: TIE com id "tie" e numero = o registro (o que o C7 grava) não acusa, e a pendência do C7 fica velha',
       not V and [(n, c) for n, c, _ in velhas] == [('REGISTRO', 'C7')], (V, velhas))
    k = tie(id='tie', numero=reg)
    k['D']['documentos'].append(dict(k['D']['documentos'][0]))
    V = verifica(k)['REGISTRO']
    ok('REGISTRO: dois documentos com id "tie" acusam (o 2º não esconde o 1º)', any('2 documentos com id "tie"' in m for m in V), V)
    k = hoje()
    k['D']['documentos'] = [d for d in k['D']['documentos'] if 'TIE' not in d['n']]
    V = verifica(k)['REGISTRO']
    ok('REGISTRO: sem documento de TIE nenhum acusa o mesmo (ausente)', V == ausente, V)
    # Modo real (§4.2): o TIE ausente não reprova (o proprietário pode ter só o registro); o numero diferente, sim; registro None = SEM DADOS
    k = hoje()
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
    demonstração em título, nome de arquivo ou fonte; a leitura da pasta 05 só soma serie e formato no C8."""
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
    ok('drive.arquivos: os 14 guias, o checklist, o protocolo e os 7 arquivos do §1.5 (serie e formato entram no C8), com o título do §1.5',
       len(guias) == 14 and set(arq) - guias - {'serie', 'formato'} == set(fixos) and all(arq[c] == t for c, t in fixos.items())
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
    print('confere(): uma amostra plantada por asserção (%d) e as %d extras da revisão' % (len(C.NOMES), len(EXTRAS)))
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
    ok('EMENDA_ROTA: sem o port da rota (C8), um D com rota reprova', V['EMENDA_ROTA'] == ['emendas de 150 s da rota: falta o port do em() (C8)'], V['EMENDA_ROTA'])


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
    # C4: o registro (a amostra daqui até o C3) já vem preenchido e a pendência dele saiu; depois, o modelo do FAQ do gerador (C5) e o
    # protocolos.seafire (C6), que os commits preencheram. Desde o C6 a amostra é um dado do C8 preenchido antes da hora (o
    # snapshot.porao, que o C8 deixa sem null: só a pendência fica velha), com o mesmo efeito.
    p4 = os.path.join(tmp, 'r4')
    rc, saida = rodar(lambda D: (D['snapshot'].update({'porao': {'estado': 'seco', 'hora': D['snapshot']['hora']}}), D)[1], p4)
    ok('pendência que não ocorre mais (o snapshot.porao, do C8, preenchido antes da hora): main() devolve 1 e não grava nada',
       rc == 1 and not os.path.exists(p4) and 'NULO: pendência do C8 que não ocorre mais' in saida, (rc, saida[-300:]))
    # Revisão final do C4: o TIE com id e numero certos (o que o C7 grava) sem tirar a pendência REGISTRO do C7 reprova (a pendência
    # não ocorre mais); com o numero errado, a violação nova também reprova. Em nenhum dos dois o main() grava.
    reg = D0()['embarcacao']['registro']
    for i, (o_que, campos, espera) in enumerate((('id "tie" e numero = o registro, sem tirar a linha da PENDENTES', {'id': 'tie', 'numero': reg},
                                                  'REGISTRO: pendência do C7 que não ocorre mais'),
                                                 ('id "tie" e numero errado', {'id': 'tie', 'numero': 'CIA-99-9999'}, 'REGISTRO 1 nova(s)'))):
        p = os.path.join(tmp, 'r-tie-%d' % i)
        rc, saida = rodar(lambda D, c=campos: (D['documentos'][0].update(c), D)[1], p)
        ok('REGISTRO: TIE com %s: main() devolve 1 e não grava nada' % o_que, rc == 1 and not os.path.exists(p) and espera in saida, (rc, saida[-300:]))
    # Com o modo por caminho, as estruturais de hoje têm violações, todas congeladas na PENDENTES (antes: nenhuma violação, porque
    # 14 delas estavam inteiras em relatório). As listas privadas e a pasta do Avanti não vão a este teste (OPCIONAIS).
    novas, conhecidas, velhas = C.separa(verifica(hoje()), set(C.OPCIONAIS))
    ok('dados de hoje: nenhuma violação estrutural fora das pendências e nenhuma pendência velha (%d congeladas)' % sum(
        sum(c.values()) for c in conhecidas.values()), not novas and not velhas, {'novas': novas, 'velhas': velhas[:3]})
    ok('PENDENTES: só asserções estruturais, e cada pendência com o commit que a tira (C7–C8; o C4 completou a embarcação, o C5, '
       'os equipamentos e os guias e o C6, o D.protocolos)',
       all(n in C.NOMES and n not in C.RELATORIO and set(cs) <= set(C.COMMITS_PENDENTES) for n, cs in C.PENDENTES.items())
       and C.COMMITS_PENDENTES == ('C7', 'C8') and not any('C6' in cs for cs in C.PENDENTES.values()))


def main():
    with tempfile.TemporaryDirectory(prefix='capitao-gerador-') as tmp:
        determinismo(tmp)
        limpeza(tmp)
        copias()
        palavras()
        rotulos_c2()
        amostras()
        porao_e_lugar()
        seguranca_sem_modelo()
        grafia_seafire()
        modelos_sinteticos()
        reprova(tmp)
    print('\n%s — %d falha(s)' % ('OK' if not falhas else 'FALHOU', falhas))
    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main())
