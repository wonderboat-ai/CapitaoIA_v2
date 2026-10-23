# -*- coding: utf-8 -*-
"""Capitão IA — teste do gerador de dados (CONTRATO-DADOS 1.1.0, §6.2 C3 e §6.3). Sem navegador, sem rede, sem cota.

- Determinismo: rodado com --saida numa pasta temporária, o gerador dá a árvore byte a byte (capitao-dados.js,
  base-conhecimento.json e ferramentas/demo/fontes/**); duas rodadas dão 0 diferença; nenhuma leitura do relógio do sistema.
  O teste nunca escreve na árvore de trabalho (confere o hash dos arquivos gerados antes e depois).
- Limpeza de fontes/: apaga só o que não gera mais, dentro da pasta, sem seguir link (o alvo de um link fica intacto) e sem
  gravar através de um link.
- confere(): cada asserção da §6.3 acusa uma amostra plantada (a violação nova aparece); as estruturais reprovam o gerador
  (main() devolve 1 e nada é gravado) e as em relatório não. Listas privadas e pasta do Avanti: só amostras sintéticas aqui.
- testes/proibidos.json e proibidos-casos.json são cópias iguais do termos.json e do termos-casos.json (PROMPT §3).

    python -X utf8 testes/gerador.py
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
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


def copias():
    print('Cópias das regex (PROMPT §3)')
    p = os.path.join(RAIZ, 'ferramentas', 'prompts', 'clone-avanti-1.1.0')
    for a, b in (('termos.json', 'proibidos.json'), ('termos-casos.json', 'proibidos-casos.json')):
        ok('testes/%s = %s' % (b, a), open(os.path.join(p, a), 'rb').read() == open(os.path.join(RAIZ, 'testes', b), 'rb').read())
    # As regex que o confere() compila (cada uma com a sua flag) dão os casos: o que barra casa a indicada; o que passa não casa
    # nenhuma (o ANEXO fica fora do "passa", como no termos-casos.json). O Edge e as cópias do cérebro são do proibidos.py (Fase 3).
    T = C.carrega_termos()
    casos = __import__('json').load(open(os.path.join(RAIZ, 'testes', 'proibidos-casos.json'), encoding='utf-8'))
    erros = ['%s não barra %r' % (k, s) for k, frases in casos['barra'].items() for s in frases if not T[k].search(s)]
    erros += ['%s barra %r' % (k, s) for s in casos['passa'] for k, r in T.items() if k != 'ANEXO' and r.search(s)]
    ok('as 8 regex no Python dão os %d casos' % (sum(len(v) for v in casos['barra'].values()) + len(casos['passa'])), not erros and len(T) == 8, erros[:3])


# ——————————————————————————————— amostras plantadas ———————————————————————————————
CONST = {'NOTA_ETIQUETA': G.NOTA_ETIQUETA, 'DIAS_MESES': G.DIAS_MESES}
ROTULO_FIM = C.cap(G.PROTOCOLOS['rotulo']) + '. ' + C.cap(G.NOTA_ETIQUETA) + '.'


def hoje():
    D = G.dados()
    return {'D': copy.deepcopy(D), 'B': copy.deepcopy(G.base_conhecimento()), 'F': G.gera_fontes(D), 'faq': None, 'rodape': None,
            'listas': None, 'avanti': None}


def verifica(k):
    return C.verifica(k['D'], k['B'], k['F'], G.saidas(k['D'], k['B']), k['faq'], k['rodape'], k['listas'], k['avanti'], CONST)


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
    'MODELOS_AVANTI': (lambda r: (lambda k: (k.update({'listas': {'valores.txt': ['zzq-termo-plantado'], 'modelos-avanti.txt': ['xx-nada']}}),
                                             mais_texto(k, ' ZZQ-termo-plantado.' if r else ''))[1])(hoje()), 'valores.txt: 1 linha'),
    'COLISAO_MODELOS': (lambda r: (lambda k: (k.update({'avanti': 'manual do modelo xp-900 de outro barco'}),
                                              poe(k['D']['equipamentos'], 0, modelo='XP-900' if r else 'XQ-901'), k)[2])(hoje()), "'XP-900': 1"),
    'FONTE_LIMITES': (lambda r: (lambda k: (k['D']['replay']['limites']['motor_be_arref_c']['critico'].update({'acima': 98 if r else 97}), k)[1])(com_replay(hoje())), 'sem os números'),
    'EQUIP': (lambda r: (lambda k: (poe(k['D']['equipamentos'], 0, qtd='2' if r else 2), k)[1])(equip_completo(hoje())), 'qtd não é número'),
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
    'NOTA_ETIQUETA': (lambda r: (lambda k: (poe(k['D']['equipamentos'], 7, nota=G.NOTA_ETIQUETA), poe(k['D']['equipamentos'], 8, nota='veja o manual' if r else G.NOTA_ETIQUETA), k)[2])(hoje()),
                      'equipamentos[seafire].nota'),
    'RODAPE_SNAPSHOT': (lambda r: (lambda k: (k.update({'rodape': RODAPE_OK.replace('return true;', 'D.snapshot.quadro = {}; return true;') if r else RODAPE_OK}), k)[1])(hoje()),
                        'rodape.js'),
    'FONTES_RELATIVAS': (lambda r: (lambda k: (k['F'].update({k['D']['drive']['pastas']['abast'] + '/Extra.csv': 'Data,Litros\n' + ('12/09/2026' if r else 'há 3 dias') + ',100\n'}), k)[1])(hoje()),
                         'Extra.csv'),
}


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


def amostras():
    print('confere(): uma amostra plantada por asserção (%d)' % len(C.NOMES))
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
        bom, mau = verifica(monta(False)), verifica(monta(True))
        novos = [m for m in mau[nome] if m not in bom[nome]]
        ok('%s: acusa a amostra plantada%s' % (nome, '' if nome not in C.RELATORIO else ' (em relatório até o %s)' % C.RELATORIO[nome]),
           len(mau[nome]) > len(bom[nome]) and any(espera in m for m in novos), {'novas': novos[:3], 'antes': len(bom[nome]), 'depois': len(mau[nome])})
    # Fixtures limpas: com o replay, a rota e o histórico mínimos, as asserções do laço não acusam nada a mais que o port do C8.
    k = com_historico(com_rota(hoje()))
    V = verifica(k)
    for n in ('JANELA', 'FIO', 'EMENDA', 'LIMITES_FORMA', 'FONTE_LIMITES', 'PISO', 'HORAS', 'ROTA', 'DIA_DE_BORDO', 'HISTORICO'):
        ok('%s: nada a acusar no replay mínimo coerente' % n, not V[n], V[n][:3])
    ok('EMENDA_ROTA: sem o port da rota (C8), um D com rota reprova', V['EMENDA_ROTA'] == ['emendas de 150 s da rota: falta o port do em() (C8)'], V['EMENDA_ROTA'])


def reprova(tmp):
    print('Estruturais reprovam o gerador; as em relatório não')
    D0 = G.dados

    def rodar(planta, pasta):
        G.dados = lambda: planta(copy.deepcopy(D0()))   # cópia: o D aponta para as listas do módulo (DIARIO, AGENDA…)
        try:
            with contextlib.redirect_stdout(io.StringIO()) as o, contextlib.redirect_stderr(io.StringIO()) as e:
                rc = G.main(['--saida', pasta])
        finally:
            G.dados = D0
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
    estruturais = [n for n in C.NOMES if n not in C.RELATORIO]
    ok('estruturais de hoje (%d): nenhuma acusa os dados gerados' % len(estruturais),
       not [n for n, v in verifica(hoje()).items() if v and n in estruturais])


def main():
    with tempfile.TemporaryDirectory(prefix='capitao-gerador-') as tmp:
        determinismo(tmp)
        limpeza(tmp)
        copias()
        amostras()
        reprova(tmp)
    print('\n%s — %d falha(s)' % ('OK' if not falhas else 'FALHOU', falhas))
    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main())
