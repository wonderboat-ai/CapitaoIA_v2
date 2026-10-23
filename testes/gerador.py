# -*- coding: utf-8 -*-
"""Capitão IA — teste do gerador de dados (CONTRATO-DADOS 1.1.0, §6.2 C3 e §6.3). Sem navegador, sem rede, sem cota.

- Determinismo: rodado com --saida numa pasta temporária, o gerador dá a árvore byte a byte (capitao-dados.js,
  base-conhecimento.json e ferramentas/demo/fontes/**); duas rodadas dão 0 diferença; nenhuma leitura do relógio do sistema.
  O teste nunca escreve na árvore de trabalho (confere o hash dos arquivos gerados antes e depois).
- Limpeza de fontes/: apaga só o que não gera mais, dentro da pasta, sem seguir link (o alvo de um link fica intacto) e sem
  gravar através de um link.
- confere(): cada asserção da §6.3 acusa uma amostra plantada (a violação nova aparece), e mais as amostras extras dos achados
  da revisão do C3 (EXTRAS). Nas estruturais, a violação plantada fica fora das pendências congeladas (PENDENTES) e reprova o
  gerador (main() devolve 1 e nada é gravado); uma pendência que não ocorre mais também reprova; a varredura de termos
  (relatório até o C12) não reprova. Listas privadas e pasta do Avanti: só amostras sintéticas aqui, inclusive a troca do modelo
  de hoje do VHF (congelado) por outro da lista, que reprova (modelos_sinteticos).
- testes/proibidos.json e proibidos-casos.json são cópias iguais do termos.json e do termos-casos.json (PROMPT §3).

    python -X utf8 testes/gerador.py
"""
import contextlib
import copy
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


# ——————————————————————————————— amostras plantadas ———————————————————————————————
CONST = {'NOTA_ETIQUETA': G.NOTA_ETIQUETA, 'DIAS_MESES': G.DIAS_MESES}
ROTULO_FIM = C.rotulo_fim()   # os textos fixos do confere.py (ROTULO e NOTA), nunca os do dado


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
    # (revisão 2 do C3) as duas contam por termo e por arquivo e não imprimem o termo: #n da lista e a assinatura do candidato
    'MODELOS_AVANTI': (lambda r: (lambda k: (k.update({'listas': {'valores.txt': ['zzq-termo-plantado'], 'modelos-avanti.txt': ['xx-nada']}}),
                                             mais_texto(k, ' ZZQ-termo-plantado.' if r else ''))[1])(hoje()), 'valores.txt #1: capitao-dados.js 1'),
    'COLISAO_MODELOS': (lambda r: (lambda k: (k.update({'avanti': 'manual do modelo xp-900 de outro barco'}),
                                              poe(k['D']['equipamentos'], 0, modelo='XP-900' if r else 'XQ-901'), k)[2])(hoje()),
                        'equipamentos[motores] candidato 1 (%s): 1 na pasta do Avanti' % C.assinatura('XP-900')),
    'FONTE_LIMITES': (lambda r: (lambda k: (k['D']['replay']['limites']['motor_be_arref_c']['critico'].update({'acima': 98 if r else 97}), k)[1])(com_replay(hoje())), 'sem os números'),
    # fabricante vazio nos motores: fora das pendências do C5 (a qtd de texto de todos é pendência de hoje; ela fica nas EXTRAS)
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
    # protocolos.seafire (None hoje, C6): a nota dos equipamentos já é pendência de hoje (C5)
    'NOTA_ETIQUETA': (lambda r: (lambda k: (k['D']['protocolos'].update({'seafire': {'nota': 'veja o manual' if r else C.NOTA}}), k)[1])(hoje()),
                      'protocolos.seafire.nota'),
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
    ('SEGURANCA_MARCADA', 'g_epirb §4 sem palavra da lista (só a fonte casa)', lambda r: com_trecho(dict(T_EPIRB, seguranca=True) if not r else T_EPIRB),
     'base:trechos[46] (Guia de bordo — EPIRB · 4 · Validade) casa'),
    ('SEGURANCA_MARCADA', 'g_seafire §3 sem palavra da lista (fonte e equip casam)', lambda r: com_trecho(dict(T_SEAFIRE, seguranca=True) if not r else T_SEAFIRE),
     '3 · Depois da descarga) casa'),
    ('SEGURANCA_MARCADA', 'seção do mínimo do §1.5 sem palavra (g_porao §4)',
     lambda r: com_trecho(dict(T_PORAO, seguranca=True) if not r else T_PORAO, {'g_porao': T_PORAO['fonte']}), 'no mínimo do §1.5 (g_porao)'),
    ('SEGURANCA_MARCADA', 'item do FAQ do mínimo (EP-04) sem palavra',
     lambda r: (lambda k: (k.update({'faq': {'itens': [dict({'id': 'EP-04', 'titulo': 'Validade', 'resposta': 'Confira a data. ' + ROTULO_FIM},
                                                           **({} if r else {'seguranca': True}))]}}), k)[1])(hoje()), 'faq:EP-04'),
    ('ROTULO_SEGURANCA', 'protocolos.rotulo diferente do texto fixo', lambda r: com_rotulo('procedimento padrão' if r else C.ROTULO), 'protocolos.rotulo'),
    ('TERMOS', 'termo posto no protocolos.rotulo é acusado e não apaga o resto (não cai de 101 para 29)',
     lambda r: com_rotulo('SEM DADOS' if r else C.ROTULO), 'ROTULOS: protocolos.rotulo'),
    ('TERMOS', 'rótulo trocado por "fictício" não apaga o "fictício" do diário',
     lambda r: com_rotulo('fictício', ' Valores fictícios.' if r else ''), 'AUTENTICIDADE: diario[0].t'),
    ('NOTA_ETIQUETA', 'constante do gerador diferente do texto do §1.4',
     lambda r: (lambda k: (k.update({'const': dict(CONST, NOTA_ETIQUETA='veja o manual' if r else C.NOTA)}), k)[1])(hoje()), 'NOTA_ETIQUETA do gerador'),
    # a qtd '2' dos motores é a pendência de hoje (C5); outro valor no mesmo caminho é violação nova
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
    ('MMSI9', '2º número de 9 dígitos numa string que já é pendência (base:trechos[25])',
     lambda r: (lambda k: (poe(k['B']['trechos'], 25, texto=k['B']['trechos'][25]['texto'] + (' Outro 987654321.' if r else '')), k)[1])(hoje()),
     'base:trechos[25].texto: 987654321'),
    ('MMSI9', 'o mesmo número de novo numa string que já é pendência',
     lambda r: (lambda k: (poe(k['B']['trechos'], 25, texto=k['B']['trechos'][25]['texto'] + (' MMSI 710123456.' if r else '')), k)[1])(hoje()),
     'base:trechos[25].texto: 710123456'),
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
    # NULO: também a base, o FAQ e os JSON das fontes (o pag: null de hoje é pendência do C5).
    ('NULO', "base com secao '' e equip null", lambda r: (lambda k: (poe(k['B']['trechos'], 3, **({'secao': '', 'equip': None} if r else {})), k)[1])(hoje()),
     "base:trechos[3].secao: ''"),
    ('NULO', 'null num JSON das fontes', lambda r: com_json(lambda j: j.update({'extra': None if r else 1})), ':extra: None'),
    ('NULO', 'lista vazia no FAQ', lambda r: (lambda k: (k.update({'faq': {'itens': [] if r else [{'id': 'EL-01'}]}}), k)[1])(hoje()), 'faq:itens: lista vazia'),
] + [
    # Revisão 3 do C3. AFIRMA_REAL e PROTOCOLO_LIMPO: uma violação por ocorrência; a pendência prende o texto casado de hoje, e
    # uma 2ª afirmação (ou um ETA) num caminho que já é pendência reprova.
    ('AFIRMA_REAL', '2ª afirmação na string que já é pendência (base:trechos[25])',
     lambda r: com_base(25, ' Os dados são reais e o barco é real.' if r else ''), 'base:trechos[25].texto: dados são reais'),
    ('AFIRMA_REAL', '2ª afirmação no passo do FAQ que já é pendência',
     lambda r: com_faq_passo(' A navegação é real.' if r else ''), 'faq.eletronicos.perguntas[3].passos[1].t: navegação é real'),
    ('AFIRMA_REAL', 'afirmação em outra seção da página do guia de eletrônicos (a página já é pendência)',
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
    ('MMSI9', '2º "programe" na string que já é pendência (base:trechos[25])',
     lambda r: com_base(25, ' Para programar o rádio, use o MMSI.' if r else ''), 'base:trechos[25].texto: "programar" perto de MMSI'),
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
    ('marca do motor (antes do C5)', 'mob', None, 'Motores Cummins em neutro.', 'motor', 'Cummins'),
    ('comprimento', 'mob', None, 'Barco de 12,4 m.', 'comprimento', '12,4 m'),
    ('boca por extenso', 'mob', None, 'Boca de 3,95 metros.', 'boca', '3,95 metros'),
    ('calado', 'mob', None, 'Calado 1,10 m.', 'calado', '1,10 m'),
    ('deslocamento', 'mob', None, 'Deslocamento de 10,4 t.', 'deslocamento', '10,4 t'),
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


def com_faq_passo(extra):
    """hoje() com `extra` no fim do passo do D.faq que já é pendência do C5 (o MMSI do guia de eletrônicos)."""
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
    por linha e o curinga no candidato da COLISAO_MODELOS deixavam passar (o modelo do Avanti chegava ao capitao-dados.js)."""
    print('MODELOS_AVANTI e COLISAO_MODELOS: o modelo de hoje congelado, e a troca (listas e pasta do Avanti sintéticas)')
    nomes = ('MODELOS_AVANTI', 'COLISAO_MODELOS')
    V0 = verifica(com_vhf('XP-900'))
    salvo = {n: C.PENDENTES[n] for n in nomes}
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
        C.PENDENTES.update(salvo)
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
    if nome in C.RELATORIO:
        modo, reprova = ' (em relatório até o %s)' % C.RELATORIO[nome], True
    else:
        livres = C.separa({nome: mau[nome]})[0].get(nome, [])
        modo, reprova = ' e reprova (fora das pendências)', any(espera in m for m in livres)
    ok('%s: acusa a amostra plantada%s%s' % (nome, o_que, modo),
       len(mau[nome]) > len(bom[nome]) and any(espera in m for m in novos) and reprova,
       {'novas': novos[:3], 'antes': len(bom[nome]), 'depois': len(mau[nome]), 'reprova': reprova})


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
    ok('MMSI9: o protocolos do §1.3 ("identificação programada no rádio: é o MMSI") passa',
       not [m for m in V['MMSI9'] if m.startswith('protocolos')], [m for m in V['MMSI9'] if m.startswith('protocolos')][:3])
    # Revisão 2 do C4 (barco_sos): o nome, o único dado do barco que o SOS mostra, não conta, nem com a marca dentro dele; número
    # vizinho dos da embarcação também não (1,15 m · 21,1 m · 112,4 m · 12,40 mm · 10,45 t · 20230). A regra da tela (verificar.py:
    # sem os números, porque o SOS mostra o clima real, e sem a base, que sai da S1 na 1b) não acusa o clima, a base nem o nome, e
    # acusa o registro, o fabricante, o modelo, a marca e o motor.
    k = protocolo('roteiro', 1, 'AQUI É MARÉVIA STAR, MARÉVIA STAR, MARÉVIA STAR')
    k['D']['embarcacao']['nome'] = 'Marévia Star'
    novos = [m for m in verifica(k)['PROTOCOLO_LIMPO'] if m not in V0_PL]
    ok('PROTOCOLO_LIMPO: o nome com a marca dentro ("AQUI É MARÉVIA STAR") não acusa', not novos, novos[:3])
    k = protocolo('mob', None, 'A 2 m da pessoa; 1,15 m; 21,1 m; 112,4 m; 12,40 mm; 10,45 t; 20230.')
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


def reprova(tmp):
    print('Estruturais reprovam o gerador (fora das pendências); a varredura de termos (relatório) não')
    D0, B0 = G.dados, G.base_conhecimento

    def rodar(planta, pasta, base=None):
        G.dados = lambda: planta(copy.deepcopy(D0()))   # cópia: o D aponta para as listas do módulo (DIARIO, AGENDA…)
        if base:
            G.base_conhecimento = lambda: base(copy.deepcopy(B0()))
        opcionais = {k: os.environ.pop(k) for k in ('CAPITAO_LISTAS_PRIVADAS', 'CAPITAO_AVANTI') if k in os.environ}   # como o roda()
        try:
            with contextlib.redirect_stdout(io.StringIO()) as o, contextlib.redirect_stderr(io.StringIO()) as e:
                rc = G.main(['--saida', pasta])
        finally:
            G.dados, G.base_conhecimento = D0, B0
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
    afirma = lambda B: (B['trechos'][25].update({'texto': B['trechos'][25]['texto'] + ' Os dados são reais e o barco é real.'}), B)[1]
    lugar = lambda D: (D['equipamentos'][7].update({'local': 'paiol de proa'}), D)[1]
    terceiro = lambda D: (D['agenda'][0].update({'quem': 'Carlos Pereira'}), D)[1]
    for nome, pl, n, base, o_que in (('NULO', nulo, 3, None, ''), ('EQUIP', lambda D: (D['equipamentos'][0].update({'fabricante': ''}), D)[1], 1, None, ''),
                                     ('MMSI9', mmsi_num, 1, None, ' (9 dígitos guardados como número)'),
                                     ('NULO', lambda D: D, 2, base_vazia, " (na base: secao '' e equip null)"),
                                     ('AFIRMA_REAL', lambda D: D, 2, afirma, ' (2 afirmações num trecho que já é pendência)'),
                                     ('SEM_INDICATIVO', lugar, 1, None, ' (equipamentos[epirb].local)'),
                                     ('TERCEIROS', terceiro, 1, None, ' (nome de terceiro no quem da agenda)')):
        p = os.path.join(tmp, 'r-%s-%d' % (nome, n))
        rc, saida = rodar(pl, p, base)
        ok('%s plantado fora das pendências%s: main() devolve 1 e não grava nada' % (nome, o_que),
           rc == 1 and not os.path.exists(p) and ('%s %d nova(s)' % (nome, n)) in saida, (rc, saida[-300:]))
    # C4: o registro (a amostra daqui até o C3) já vem preenchido e a pendência dele saiu; a amostra passa a ser um dado do C5
    # preenchido antes da hora (o modelo do FAQ do gerador), com o mesmo efeito.
    p4 = os.path.join(tmp, 'r4')
    rc, saida = rodar(lambda D: (D['faq']['gerador'].update({'modelo': 'QD 9'}), D)[1], p4)
    ok('pendência que não ocorre mais (o modelo do FAQ do gerador, do C5, preenchido antes da hora): main() devolve 1 e não grava nada',
       rc == 1 and not os.path.exists(p4) and 'NULO: pendência do C5 que não ocorre mais' in saida, (rc, saida[-300:]))
    # Com o modo por caminho, as estruturais de hoje têm violações, todas congeladas na PENDENTES (antes: nenhuma violação, porque
    # 14 delas estavam inteiras em relatório). As listas privadas e a pasta do Avanti não vão a este teste (OPCIONAIS).
    novas, conhecidas, velhas = C.separa(verifica(hoje()), set(C.OPCIONAIS))
    ok('dados de hoje: nenhuma violação estrutural fora das pendências e nenhuma pendência velha (%d congeladas)' % sum(
        sum(c.values()) for c in conhecidas.values()), not novas and not velhas, {'novas': novas, 'velhas': velhas[:3]})
    ok('PENDENTES: só asserções estruturais, e cada pendência com o commit que a tira (C5–C8; o C4 completou a embarcação)',
       all(n in C.NOMES and n not in C.RELATORIO and set(cs) <= set(C.COMMITS_PENDENTES) for n, cs in C.PENDENTES.items()))


def main():
    with tempfile.TemporaryDirectory(prefix='capitao-gerador-') as tmp:
        determinismo(tmp)
        limpeza(tmp)
        copias()
        amostras()
        modelos_sinteticos()
        reprova(tmp)
    print('\n%s — %d falha(s)' % ('OK' if not falhas else 'FALHOU', falhas))
    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main())
