# -*- coding: utf-8 -*-
"""Capitão IA — conferência dos dados gerados (CONTRATO-DADOS 1.1.0 §6.3), chamada pelo gerar_demo.py antes de gravar.

verifica() roda as asserções sobre o D, a base, o FAQ, as fontes do Drive e o texto dos arquivos gerados, e devolve as
violações de cada uma (caminho e motivo). São as da §6.3 e, no fim, as invariantes da coluna "Asserção do gerador" da §6.4 que
não têm nome lá (TERCEIROS, SEM_PREVISAO); as outras da §6.4 ficam na MMSI9 ("programe" perto de MMSI) e na SEM_INDICATIVO
(indicativo, HEX ID, telefone e lugar de salvatagem como campo, §0.2). Por último, a EMBARCACAO (§1.2, a do C4 da §6.2: os campos
completos, rotulo e motorizacao gerados dos campos, lotacao ≥ pessoasBordo).

confere() imprime o resumo e reprova o gerador (nada é gravado) se uma asserção estrutural falhar. Só a varredura de termos
(RELATORIO) fica em relatório, até o C12. As violações de hoje que dependem do dado dos C5–C8 estão congeladas por caminho na
PENDENTES, cada uma com o commit que a tira: qualquer outra reprova, e uma pendência que não ocorre mais também (o commit que
completa o dado tira a linha dela).

As listas privadas (CAPITAO_LISTAS_PRIVADAS) e a pasta do Avanti (CAPITAO_AVANTI) são opcionais e só dão CONTAGENS: nenhum
termo delas é impresso nem gravado.

Também ficam aqui os ports em Python que as asserções e o gerador usam, escritos como no JavaScript:
  - norm/pad/has, emergencia() e oleo() do capitao-brain.js, com a lista SOS ampliada da 1b (PROMPT §2.3);
  - SEGURANCA_PALAVRAS e segura() (§1.5), uma fonte só das listas;
  - o laço de 150 s (§3.2: chaves, ruído por hash e arredondamento) e a CapitaoAgora.nivel (§3.3). A paridade com o JS é da
    Fase 2; a rota e os contadores do em() entram no C8 (PORT_ROTA).
Sem lookbehind nas regex que vão para o JavaScript (estas ficam só no Python).
"""
import hashlib
import json
import math
import os
import re
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROIBIDOS = os.path.join(RAIZ, 'testes', 'proibidos.json')     # cópia do termos.json (PROMPT §3): a fonte das 8 regex
RODAPE = os.path.join(AQUI, 'rodape.js')                       # rodapé do capitao-dados.js (§1.23; entra no C7)

# ——————————————————————————————— modo de cada asserção ———————————————————————————————
# §6.2 C3: as estruturais reprovam o gerador; só a varredura de termos fica em relatório (não reprova), até o C12.
RELATORIO = {'TERMOS': 'C12'}   # com a exceção do mmsiNota até a 1b (EXCECAO_TERMOS)
# Violações de hoje que dependem do dado dos C5–C8, congeladas por caminho (não pela asserção inteira): cada uma com o commit
# que completa o dado. Uma violação fora desta lista reprova o gerador; um padrão que não casa mais nada também, para a lista
# não esconder a volta do defeito (o commit que completa o dado tira a linha dele). Cada padrão vale para UMA violação: o texto
# exato, com '*' no lugar de um trecho: o «…» citado (o caminho, a regra e, na MMSI9, os dígitos ficam presos), um nome que não
# pode estar no repositório, ou a contagem de datas das 4 planilhas que o C7 refaz inteiras. Nas duas das listas privadas e da
# pasta do Avanti, a contagem é exata e o termo vai por número (#n) ou por assinatura (nunca o nome).
_AG = ('porao-teste', 'clima-filtro', 'gerador-rotor', 'casco-anodos', 'motores-oleo', 'gerador-revisao', 'seakeeper-anodo',
       'baterias', 'garmin-cartas', 'clima-revisao', 'motores-revisao')   # as 11 tarefas de hoje (C7: deslocamentos, sistema, palavras)
_ELETRONICOS = 'fontes/01 Manuais e guias de bordo/Guia de bordo — Eletrônicos *.html'   # o título traz o VHF antigo (C5)
_EQUIP = (('motores', 'modelo', "'2'"), ('gerador', 'modelo', "'1'"), ('estabilizador', 'modelo', "'1'"), ('climatizacao', 'fabricante modelo', None),
          ('eletronicos', 'modelo', None), ('audio', 'modelo', None), ('vhf', 'fabricante', None), ('epirb', 'fabricante modelo guia', None),
          ('seafire', 'modelo guia', None))   # o que falta em cada equipamento hoje e a qtd de texto de hoje (C5; None = 'SEM DADOS')
_SEG = 'base:trechos[%d] (*) casa a SEGURANCA_PALAVRAS sem seguranca: true'
# A frase de hoje do MMSI no guia de eletrônicos, nas 3 cópias ("o MMSI 710123456 é fictício; no barco real, programe o MMSI do
# registro"): sai no C5, com o g_eletronicos §5 de MMSI_RADIO.
_MMSI_C5 = ('faq.eletronicos.perguntas[3].passos[1].t', 'base:trechos[25].texto', _ELETRONICOS)
PENDENTES = {
    'NULO': {
        'C5': ['equipamentos[%d].%s: None' % (i, k) for i, ks in ((0, 'modelo'), (1, 'modelo'), (2, 'modelo'), (3, 'fabricante modelo'),
                                                                  (4, 'modelo'), (5, 'modelo'), (6, 'fabricante'), (7, 'fabricante modelo guia'),
                                                                  (8, 'modelo guia')) for k in ks.split()]
              + ['faq.%s.modelo: None' % f for f in ('gerador', 'estabilizador', 'eletronicos', 'climatizacao')]
              + ['base:trechos[%d].pag: None' % i for i in range(46)],   # §1.5: o pag: null sai do trecho
        'C6': ['protocolos.seafire: None', 'protocolos.epirb: None'],
        'C7': ['documentos[%d].%s: None' % (i, k) for i in (0, 6, 7) for k in ('vence', 'dn')],   # sem deslocamento: omitidos (§1.0)
        'C8': ['snapshot.porao: None', 'snapshot.ancora: None']   # §1.17 sem null; a leitura da pasta 05 é refeita (e renomeada)
              + ['fontes/05 Telemetria — coletor NMEA/Leitura do coletor NMEA — 26-09-2026 10h12.json:seakeeper_volante_%s: None' % k
                 for k in ('rpm', 'pct')],
    },
    'MMSI9': {'C5': [c + m for c in _MMSI_C5 for m in (': 710123456 «*»', ': "programe" perto de MMSI «*»')],
              'C6': ['protocolos.roteiro[2]: 710123456 «*»']},
    'AFIRMA_REAL': {'C5': [c + ': barco real «*»' for c in _MMSI_C5]},
    'TERCEIROS': {'C7': ["agenda.%s.quem: papel fora da lista fechada (§1.7): 'oficina Volvo Penta'" % i for i in ('motores-oleo', 'motores-revisao')]
                  + ["equipe.apoio[1].papel: papel fora da lista fechada (§1.11): 'Oficina Volvo Penta'"]},   # §1.7 e §1.11 (C7)
    'PROTOCOLO_LIMPO': {'C6': ['protocolos.roteiro[2]: regex de emergência [710123456] «*»',
                               'protocolos.mob[1]: fabricante ou modelo de equipamento [Garmin] «*»']},
    'SEGURANCA_MARCADA': {'C5': [_SEG % i for i in (0, 21, 25, 38, 40, 41, 42, 43, 44, 45)]
                          + ['base:trechos[31] (*) está no mínimo do §1.5 (g_motores) sem seguranca: true']},
    # Ocorrências exatas por termo e por arquivo (só com CAPITAO_LISTAS_PRIVADAS; hoje só o #1, o VHF antigo): outro termo da lista,
    # ou mais uma ocorrência do #1, em qualquer arquivo, reprova.
    'MODELOS_AVANTI': {'C5': ['modelos-avanti.txt #1: %s %d' % kv for kv in (
        ('base-conhecimento.json', 16), ('capitao-dados.js', 9), (_ELETRONICOS, 4),
        ('fontes/01 Manuais e guias de bordo/Inventário de bordo.csv', 4), ('fontes/02 Documentos/Controle de documentos.csv', 1))]},
    # Só com CAPITAO_AVANTI: o modelo de hoje do VHF, preso pela assinatura e pela contagem (outro modelo no lugar reprova).
    'COLISAO_MODELOS': {'C5': ['equipamentos[vhf] candidato 1 (c9f12c054d30): 95 na pasta do Avanti (permitido 0)']},
    'EQUIP': {'C5': ['equipamentos[%s].%s ausente' % (i, k) for i, ks, _ in _EQUIP for k in ks.split() if k != 'guia']
                    + ['equipamentos[%s].qtd não é número: %s' % (i, q or repr('SEM DADOS')) for i, _, q in _EQUIP]
                    + ['equipamentos[%s].guia fora de D.guias: None' % i for i, ks, _ in _EQUIP if 'guia' in ks.split()]},
    'NOTA_ETIQUETA': {'C5': ['equipamentos[epirb].nota ≠ NOTA_ETIQUETA', 'equipamentos[seafire].nota ≠ NOTA_ETIQUETA']},
    'IDS': {'C7': ['agenda.%s.sistema fora do vocabulário (ids de equipamentos, casco, tanques): None' % i for i in _AG]
            + ['diario.%s: pendência sem ref na agenda' % iso for iso in ('2026-09-24T17:10:00-03:00', '2026-09-20T11:05:00-03:00',
                                                                          '2026-09-05T10:00:00-03:00')]},
    'AGENDA': {'C7': [m % i for i in _AG for m in ('agenda.%s: ultimaHa + venceEm ≠ DIAS_MESES[meses]', 'agenda.%s.palavras vazias ou com palavra solta')]
               + ['agenda.porao-teste: seguranca só (e sempre) em epirb-teste, porao-teste, seafire-inspecao', 'agenda: 0 atrasadas (precisa de 3)']},
    'FONTES_RELATIVAS': {'C7': ['fontes/%s: * data(s) dd/mm/aaaa' % f for f in (
        '02 Documentos/Controle de documentos.csv', '03 Agenda de manutenção/Agenda preditiva.csv', '04 Diário de bordo/Diário de bordo.csv',
        '06 Abastecimento/Registro de abastecimento.csv')]},
}
COMMITS_PENDENTES = ('C5', 'C6', 'C7', 'C8')   # o C4 completou a embarcação (§1.2)
# Asserções que só rodam com uma fonte opcional do ambiente: sem ela, a pendência delas não é "velha".
OPCIONAIS = {'MODELOS_AVANTI': 'listas', 'COLISAO_MODELOS': 'avanti'}
# Única exceção da varredura de termos na Fase 1 (§1.2): sai na 1b, junto com o campo.
EXCECAO_TERMOS = {'embarcacao.mmsiNota': '1b'}
# Textos fixos (PROMPT §2.3, §3; CONTRATO §1.3, §1.4): a referência é daqui, nunca do dado que está sendo conferido. O rótulo é a
# EXCEÇÃO do §3 na varredura de termos; tirado do D, um termo posto no próprio rótulo sumiria de todo o dado.
ROTULO = 'procedimento padrão — confirmar com o protocolo de bordo'
NOTA = 'modelo, validade e acionamento: veja a etiqueta do equipamento'
# Mínimo do §1.5 (coluna seguranca: true da tabela dos guias): a marcação por palavra pode pegar mais seções, nunca menos. Chave
# de drive.arquivos → números de seção (no checklist, o título); None = todas. No FAQ (§1.6), os ids das mesmas seções e os EM.
MINIMO_SEGURANCA = {'g_motores': {'4'}, 'g_eletronicos': {'1', '5'}, 'g_porao': {'4'}, 'g_ais': {'2'}, 'g_seafire': None,
                    'g_epirb': None, 'checklist': {'Saída · antes de largar'}, 'protocolo': None}
MINIMO_FAQ = re.compile(r'(?:EM|SF|EP)-\d+|MO-04|EL-01|EL-05|PO-04|AI-02|CK-03')
# Ocorrências permitidas na pasta do Avanti, por candidato (COLISAO_MODELOS; ok do proprietário, §8.2 ponto 9).
EXCECOES_MODELO = {'Seakeeper 3': 1}
# Port da rota e dos contadores do em() (§1.14, §1.22; entra no C8). Sem ele, um D com rota reprova a EMENDA_ROTA.
PORT_ROTA = None

TAMANHO_KB = {'capitao-dados.js': 120, 'base-conhecimento.json': 80, 'faq-equipamentos.json': 100}   # KB = 1.024 bytes
DIAS_MESES_PADRAO = {1: 31, 6: 184, 12: 365}

# ——————————————————————————————— regex fixas das asserções ———————————————————————————————
R_MMSI9 = re.compile(r'\b\d{9}\b')
R_HEX15 = re.compile(r'\b[0-9A-F]{15}\b')
# Indicativo com os prefixos de rádio reais do Brasil (PP–PY e ZV–ZZ; PROMPT §2.2: nunca gerar), nos três formatos: o de
# radioamador do contrato (PY2ABC), o de estação de navio, 2 ou 3 letras e 4 dígitos (PU1234, PPA1234), e, depois da palavra
# "indicativo", qualquer código com o prefixo (o de 4 letras, PPXA). Solto, o de 4 letras casaria palavras em maiúsculas ("PUXE").
_PREFIXO_RADIO = r'(?:P[P-Y]|Z[V-Z])'
R_INDICATIVO = re.compile(r'\b' + _PREFIXO_RADIO + r'\d[A-Z]{2,3}\b|\b' + _PREFIXO_RADIO + r'[A-Z]?\d{4}\b'
                          r'|(?i:indicativo)[^.\n]{0,40}?\b' + _PREFIXO_RADIO + r'[A-Z0-9]{2,5}\b')
R_REGISTRO = re.compile(r'[A-Z]{3}-\d{2}-\d{4}')
R_PLACAS = (re.compile(r'\b[A-Z]{2,3}-?\d{4}\b'), re.compile(r'\b[A-Z]{3}\d[A-Z]\d{2}\b'))   # antiga, anterior a 1990 e Mercosul
R_HIN = re.compile(r'\b[A-Z]{3}[A-Z0-9]{5}[A-L]\d{3}\b')                          # código do fabricante + série + mês/ano
R_9A11 = re.compile(r'\b\d{9,11}\b')
# AFIRMA_REAL do §6.3, com rea(?:l|is) no lugar do reais? do contrato, que casava "reai(s)" e deixava passar o singular ("no barco
# real"): a trava §2.6 do PROMPT ganha. Com o fim de palavra, "realizado" e "oficina" continuam passando.
# O grupo 1 é a afirmação, sem o caractere do fim de palavra (vai na mensagem e prende a pendência).
R_AFIRMA = re.compile(r'(?:^|[^A-Za-zÀ-ÿ])((?:dados?|leituras?|barco|embarca[çc][ãa]o|navega[çc][ãa]o)\s+(?:\S+\s+){0,2}'
                      r'(?:rea(?:l|is)|verdadeir[A-Za-zÀ-ÿ]*|oficia(?:l|is)))(?![A-Za-zÀ-ÿ])', re.I)
# Coordenada em texto (PROMPT §2.8): graus-minutos com vírgula ou ponto; decimal com 4 ou mais casas, ou em par. Milhar do pt-BR
# (1.236,4 h · 1.600 L · 12.000 · "1.000, 1.500 rpm") fica de fora. Além das do §2.8, a forma do semCoord de hoje
# (capitao-brain.js: minutos inteiros com o apóstrofo e o hemisfério, 26°59'S), os segundos (26°59'35"), o "º" ordinal no lugar
# do grau e o par separado por vírgula quando o 1º número tem sinal (-26.993,-48.614: a linha típica de CSV).
R_COORD = re.compile(r"-?\d{1,3}\s*[°º]\s*\d{1,2}\s*[,.]\s*\d+\s*['′’]?\s*[NSEWLO]?"
                     r"|-?\d{1,3}\s*[°º]\s*\d{1,2}\s*['′’]\s*(?:[NSEWLO]|\d{1,2}(?:[,.]\d+)?\s*(?:[\"″”]|''|’’))"
                     r"|-?\d{1,3}[.,]\d{4,}(?!\d)|-?\d{1,3}[.,]\d{3,}\s*[;/]\s*-?\d{1,3}[.,]\d{3,}"
                     r"|-\d{1,3}[.,]\d{3,}\s*,\s*-?\d{1,3}[.,]\d{3,}")
# MMSI9 (§6.4, trava §2.2): nunca instrução de programar o MMSI. O verbo no imperativo, no infinitivo ou no gerúndio (o grupo 1
# ou o 2) na mesma frase que "MMSI", a até 80 letras; "programado(a)" descreve o rádio e passa (protocolos.dsc do §1.3).
_PROGRAMAR = r'(?<![A-Za-zÀ-ÿ])((?:re)?program(?:e|em|ar|ando|á-l[oa]|e-[oa])(?![A-Za-zÀ-ÿ]))'
R_PROGRAME_MMSI = re.compile(_PROGRAMAR + r'[^.!?;\n]{0,80}?\bMMSI\b|\bMMSI\b[^.!?;\n]{0,80}?' + _PROGRAMAR, re.I)
# A regex de emergência do PROMPT (Fase 7): nada de MMSI, último fix, distância, velocidade, posição, rumo, ETA nem pessoas.
R_EMERG = re.compile(r"710123456|último fix|\d+[.,]\d+\s*(?:mn|milhas?)|\d+[.,]?\d*\s*nós|°\s*\d{1,2}[,.]\d+\s*['′]"
                     r"|\b(?:rumo|proa|COG|HDG)\b[^\n]{0,12}\d{2,3}\s*°|\bETA\b|\b\d+\s+(?:pessoas\s+)?a bordo\b")
# Nos protocolos, a mesma regex sem distinguir maiúsculas: o roteiro do SOS é todo em maiúsculas ("ÚLTIMO FIX", "4 PESSOAS A BORDO").
R_EMERG_PROTOCOLO = re.compile(R_EMERG.pattern, re.I)
# Número de pessoas (§1.3; PROMPT §2.2: "PESSOAS A BORDO: conte agora", nunca o número gerado), também por extenso e na lotação.
_GENTE = r'(?:pessoas|tripulantes|passageiros)'
R_PESSOAS = re.compile(_GENTE + r'[^\n]{0,20}\d|\d+\s*' + _GENTE + r'|(?:^|[^A-Za-zÀ-ÿ])(?:dois|duas|tr[eê]s|quatro|cinco|seis|sete|oito'
                       r'|nove|dez|onze|doze)\s+' + _GENTE + r'|lota[çc][ãa]o[^\n]{0,20}\d', re.I)
# Tudo sem distinguir maiúsculas (o roteiro do SOS é em maiúsculas: "3,4 BAR", "1 MINUTO", "ULTIMO FIX").
R_PROTOCOLO = (
    ('" bar"', re.compile(r'(?:^|\s)bar(?![A-Za-zÀ-ÿ])', re.I)),
    ('"%"', re.compile('%')),
    ('"nós"', re.compile(r'(?:^|[^A-Za-zÀ-ÿ])nós(?![A-Za-zÀ-ÿ])', re.I)),
    ('"mn"', re.compile(r'(?:^|[^A-Za-zÀ-ÿ])mn(?![A-Za-zÀ-ÿ])', re.I)),
    ('graus', re.compile(r'°|(?:^|[^A-Za-zÀ-ÿ])graus?(?![A-Za-zÀ-ÿ])', re.I)),
    ('minutos', re.compile(r'\d+\s*(?:min|minutos?)(?![A-Za-zÀ-ÿ])', re.I)),
    ('número de pessoas', R_PESSOAS),
    ('último fix', re.compile(r'(?:^|[^A-Za-zÀ-ÿ])[uú]ltimo\s+fix(?![A-Za-zÀ-ÿ])', re.I)),   # também sem o acento
    ('regex de emergência', R_EMERG_PROTOCOLO),
)   # mais o lugar a bordo, montado da LOCAL_SEGURANCA do proibidos.json (lugar_a_bordo)
R_BOIA = re.compile(r'(?:^|[^A-Za-zÀ-ÿ])b[oó]ias?(?![A-Za-zÀ-ÿ])', re.I)   # também a grafia antiga "bóia"
R_KIT = re.compile(r'(?:^|[^A-Za-zÀ-ÿ])kits?(?![A-Za-zÀ-ÿ])', re.I)
R_DATA = re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b')
LOCAL_PECAS = re.compile(r'(?:estante técnica [1-3]|caixa de sobressalentes [A-C]|armário de ferramentas)')
ONDE_SENSORES = {'hard-top', 'mastro do radar', 'casco · meia-nau', 'meia-nau', 'praça de máquinas · centro', 'praça de máquinas',
                 'praça de máquinas · BB', 'praça de máquinas · BE', 'praça de máquinas · ré', 'meia-nau · BB', 'meia-nau · BE',
                 'painel do comando', 'popa', 'proa · guincho da âncora'}           # §1.19
SALVATAGEM_EM = ('epirb', 'seafire', 'balsa', 'colete', 'extintor', 'boia')        # nunca ponto de sensor nem peça (§1.19, §1.20)
CAMPOS_FASE1 = (   # PROMPT, Fase 1: os nomes do coletor de hoje mais os novos e os contadores
    'timestamp_utc', 'lat', 'lon', 'sog_nos', 'proa_graus', 'gps_satelites', 'profundidade_m', 'vento_verdadeiro_nos',
    'vento_verdadeiro_angulo', 'pressao_barometrica_hpa', 'temp_ar_externo_c', 'temp_agua_c', 'tanque_agua_pct',
    'tanque_cinzas_pct', 'tanque_negras_pct', 'bateria_0_tensao_v', 'bateria_2_tensao_v', 'seakeeper_ativo',
    'seakeeper_volante_rpm', 'seakeeper_volante_pct', 'gerador_horimetro_h',
    'cog_graus', 'stw_nos', 'motor_bb_rpm', 'motor_be_rpm', 'motor_bb_oleo_bar', 'motor_be_oleo_bar', 'motor_bb_arref_c',
    'motor_be_arref_c', 'motor_bb_carga_pct', 'motor_be_carga_pct', 'marcha', 'consumo_lph', 'diesel_bb_pct', 'diesel_be_pct',
    'gerador_ativo', 'gerador_kw', 'porao_bb_nivel', 'porao_be_nivel', 'bomba_porao_ciclos', 'ancora_estado', 'leme_graus',
    'piloto_rumo', 'ondas_m', 'estado', 'local', 'destino', 'eta', 'alarmes',
    'motor_bb_horimetro_h', 'motor_be_horimetro_h', 'diesel_litros', 'distancia_mn')
CAMPOS_F08_F33 = ('jogo_graus', 'caimento_graus', 'proa_graus', 'vento_verdadeiro_nos', 'vento_verdadeiro_angulo',
                  'vento_aparente_nos', 'vento_aparente_angulo', 'temp_ar_externo_c', 'pressao_barometrica_hpa')
ORIGENS = {'laço', 'rota', 'contador', 'derivado', 'fixo', 'relógio', 'janela'}
TIPOS_CHECKLIST = ('saida', 'chegada', 'abastecimento', 'fundeio')
SISTEMAS_EXTRA = {'casco', 'tanques'}
SEGURANCA_AGENDA = {'epirb-teste', 'seafire-inspecao', 'porao-teste'}
# §0.2: indicativo, HEX ID, telefone e lugar de equipamento de salvatagem não existem como campo (SEM_INDICATIVO). Pelas palavras
# do nome da chave (camelCase, '_' e '-' separam; sem acento): 'hexId' → hex, id. O indicativo vale só em protocolos (o texto de
# instrução); o lugar, só nos campos de vocabulário fechado (LOCAL_VOCAB), no lugar do próprio barco (o quadro) e no posto e nos
# prestadores, que não são equipamento.
CHAVES_IDENT = {'hex': 'HEX ID', 'hexid': 'HEX ID', 'uin': 'HEX ID', 'beacon': 'HEX ID', 'tel': 'telefone', 'telefone': 'telefone',
                'telefones': 'telefone', 'fone': 'telefone', 'fones': 'telefone', 'phone': 'telefone', 'celular': 'telefone',
                'whatsapp': 'telefone', 'ramal': 'telefone', 'email': 'e-mail', 'mail': 'e-mail', 'cpf': 'CPF/CNPJ', 'cnpj': 'CPF/CNPJ'}
CHAVES_LUGAR = {'local', 'locais', 'onde', 'localizacao', 'lugar', 'lugares'}
CHAVES_HORA = {'hora', 'horario', 'data', 'fuso'}   # 'hora_local' é a hora no fuso (a leitura da pasta 05), não lugar
LUGAR_PERMITIDO = re.compile(r'(?:sensores\.pontos\[\d+\]\.onde|pecas\[\d+\]\.local|abastecimentos\[\d+\]\.local'
                             r'|replay\.diaDeBordo\.abastecimento\.local|equipe\.apoio\[\d+\]\.onde|campos\.local|snapshot\.local'
                             r'|snapshot\.quadro\.local)')
# TERCEIROS (§6.4, trava §2.7; §1.7, §1.9, §1.11): papéis em lista fechada, nunca nome de terceiro. O quem da agenda, das tarefas da
# equipe e o who do diário: os papéis do §1.7 e o primeiro nome do proprietário (embarcacao.proprietario). Os prestadores: os 6
# papéis do §1.11.
PAPEIS_QUEM = ('marina', 'técnico', 'oficina de motores')
PAPEIS_APOIO = ('Marina da base', 'Oficina de motores diesel', 'Técnico de bordo', 'Técnico de eletrônicos', 'Técnico de refrigeração',
                'Posto de combustível')
# Documentos (§1.8): só o TIE tem número (= embarcacao.registro). Apólice, licença, laudo e nota fiscal sem número nem emissor.
CHAVES_DOC = {'numero', 'num', 'nr', 'apolice', 'nf', 'nfe', 'licenca', 'emissor', 'emitente', 'seguradora', 'fornecedor'}
R_NUM_DOC = re.compile(r'(?:^|[^A-Za-zÀ-ÿ])((?:ap[óo]lices?|notas? fisca(?:l|is)|NF-?e?|licen[çc]as?)(?:\s+d[eoa]s?\s+[A-Za-zÀ-ÿ]+){0,2}'
                       r'\s*(?:(?:n\.?\s?[º°]|n[úu]mero|nr\.?|#)\s*)?:?\s*\d[\d./-]{2,})', re.I)   # 3+ caracteres: "10 anos" passa
# SEM_PREVISAO (§6.4, trava §2.5): tempo e maré são do mundo real; nenhum campo de previsão ou de maré no D (o historico inclusive)
# nem nos JSON das fontes. O vento e o mar do quadro (a bordo agora) e o mar/posicaoRef (a posição de referência do Open-Meteo) ficam.
CHAVES_PREVISAO = {'mare', 'mares', 'tabua', 'preamar', 'baixamar', 'previsao', 'previsoes', 'previsto', 'prevista', 'previstos',
                   'previstas', 'forecast', 'tide', 'tides', 'boletim'}
# EMBARCACAO (§1.2; o C4 da §6.2): os campos do §1.2 com o tipo (o registro fica na REGISTRO e o indicativo na SEM_INDICATIVO).
# 'num' = número finito maior que zero; 'int' = inteiro maior que zero (bool não conta).
CAMPOS_EMBARCACAO = (('nome', str), ('fabricante', str), ('modelo', str), ('rotulo', str), ('motorizacao', str), ('ano', 'int'),
                     ('comprimento', 'num'), ('boca', 'num'), ('calado', 'num'), ('deslocamento', 'num'), ('lotacao', 'int'),
                     ('pessoasBordo', 'int'), ('tanques', dict), ('un', dict), ('proprietario', str), ('base', str), ('fuso', str),
                     ('mmsi', str), ('fonte', str))
UN_EMBARCACAO = {'comprimento': 'm', 'boca': 'm', 'calado': 'm', 'deslocamento': 't', 'lotacao': 'pessoas', 'pessoasBordo': 'pessoas'}
TANQUES_EMBARCACAO = ('diesel_l', 'diesel_n', 'agua_l', 'cinzas_l', 'negras_l')
R_MOTORIZACAO = re.compile(r'(\d+) × (\S.*?) · (\S.*)')
R_PESSOAS_BORDO = re.compile(r'(\d+) pessoas a bordo')


# ——————————————————————————————— port do cérebro (capitao-brain.js:12-13, :122-141) ———————————————————————————————
def norm(s):
    """String(s || '').toLowerCase().normalize('NFD') sem os acentos (U+0300–U+036F)."""
    s = unicodedata.normalize('NFD', str(s or '').lower())
    return ''.join(ch for ch in s if not '̀' <= ch <= 'ͯ')


def pad(s):
    """Frase normalizada com espaço nas pontas (palavra inteira = ' x ')."""
    return ' ' + re.sub(r'\s+', ' ', re.sub(r'[?!.,;:()"“”]+', ' ', norm(s))).strip() + ' '


def has(q, lista):
    return any(k in q for k in lista)


# Lista SOS do cérebro de hoje (capitao-brain.js:123-125) mais a ampliação da 1b (PROMPT §2.3). Uma fonte só: a partir da 1b, o
# cerebro.py confere que a do capitao-brain.js é igual a esta.
SOS = ['mayday', 'emergenc', 'incendio', ' fogo', 'homem ao mar', ' mob ', ' sos ', 'socorro', 'naufrag', 'caiu no mar', 'caiu ao mar',
       'caiu na agua', 'pessoa na agua', 'alguem na agua', 'crianca na agua', 'afogad', 'afogand',
       'afund', 'entrando agua', 'agua entrando', 'entrada de agua', 'alagad', 'alagand', 'inundad', 'inundand', 'abandon', 'colisao',
       'colidi', 'abalroa', 'encalh', 'explos',
       'vazamento de combustivel', 'vazando combustivel', 'vazamento de diesel', 'vazando diesel', 'vazamento de gas', 'vazando gas',
       'cheiro de combustivel', 'cheiro de diesel', 'cheiro de gas', 'cheiro de queimado',
       # 1b (PROMPT §2.3)
       'alagament', 'afogament', 'inundac', 'adernand', 'adernad', 'adernou', 'emborc', ' ferid', 'machuc', 'se feriu', 'sangra',
       'desmai', 'inconscien', 'infart', 'convuls', 'queimadura', 'choque eletric', 'agua no porao', 'porao cheio', 'porao enchendo',
       'bomba de porao nao para', 'barco virou', 'virou o barco', ' a deriva ', 'monoxido', 'alarme de gas']
# Rota salvatagem (PROMPT §2.3): ' boia ' sem as palavras de boia de sinalização; "extintor" só sem fogo (na rota) e sempre aqui.
SALVATAGEM = ['colete', 'salva-vida', 'salva vida', 'balsa', 'bote salva', 'boia circular', 'boia salva', 'sinalizador', 'foguete',
              'pirotecn', 'facho', 'salvatagem', 'equipamento de seguranca', 'equipamentos de seguranca', 'kit de seguranca', 'sobreviv',
              ' plb ', ' sart ']
BOIA_FORA = ['amarra', 'poita', 'canal', 'baliza', 'cardinal', 'luz']
SEGURANCA_EXTRA = ['epirb', 'radiobaliza', 'baliza', 'seafire', 'supressao', 'mayday', 'distress', ' dsc ', 'pan-pan', 'pan pan',
                   'homem ao mar']


def emergencia(q):
    """q já passado pelo pad(). Fumaça no escapamento é do motor, não SOS."""
    return has(q, SOS) or (has(q, ['fumaca']) and not has(q, ['escap']))


OLEO_QUEDA = re.compile(r' (?:baix|abaixo|cai |caiu|caind|cair|qued|alarm|alert|luz|acend|acesa|sem |zer|perd|despenc|sum|diminu|oscil'
                        r'|vermelh|fora d|nao esta |nao ta |saiu|menor|anormal)')
OLEO_SINAL = re.compile(r' (?:pressao|alarm|alert|luz|acend|acesa)')
OLEO_NEUTRO = re.compile(r' (?:qual|quais|quanto|quanta|como|normal|faixa|alta|alto|ok|esta boa|ta boa|esta bom|ta bom) ')
OLEO_TOPICO = re.compile(r'^ (?:e )?(?:a )?pressao d[eo] oleo(?: d[oa]s? motor(?:es)?)?(?: (?:de )?(?:bb|be|bombordo|boreste))? $')


def oleo(q):
    """1 = queda/alarme relatado; 2 = só pergunta de pressão; 0 = outro assunto (q já passado pelo pad())."""
    q = re.sub(r' oleo (?:diesel|combustivel)(?= )', ' diesel', q)
    if not has(q, [' oleo']) or has(q, ['barometr', 'atmosf', 'hpa', 'pneu', 'hidraul']):
        return 0
    if not OLEO_SINAL.search(q) and has(q, ['porao', 'vazament', 'vazand', 'pingand']):
        return 0
    if has(q, ['gerador', ' onan ']) and not has(q, ['motor']):
        return 0
    pressao = has(q, ['pressao'])
    if OLEO_QUEDA.search(q):
        return 1 if pressao or not has(q, ['troca']) else 0
    if not pressao:
        return 0
    return 2 if OLEO_NEUTRO.search(q) or OLEO_TOPICO.search(q) else 1


def salvatagem(q, extintor=True):
    boia = ' boia ' in q and not has(q, BOIA_FORA)
    return has(q, SALVATAGEM) or boia or (extintor and 'extintor' in q)


def segura(texto):
    """SEGURANCA_PALAVRAS (§1.5): SOS ampliada (com a fumaça), salvatagem (extintor com ou sem fogo) e EPIRB, Seafire, MAYDAY,
    DSC, PAN-PAN e homem ao mar. Trecho ou item que casa leva seguranca: true e nunca vai à IA."""
    q = pad(texto)
    return emergencia(q) or salvatagem(q) or has(q, SEGURANCA_EXTRA)


# ——————————————————————————————— port do laço (§3.2) e da nivel (§3.3) ———————————————————————————————
M32 = 0xFFFFFFFF


def h32(x):
    x &= M32
    x = (x ^ 0x9E3779B9) & M32
    x ^= x >> 16
    x = (x * 0x85EBCA6B) & M32
    x ^= x >> 13
    x = (x * 0xC2B2AE35) & M32
    x ^= x >> 16
    return x


def ruido(semente, t):
    """u(s, t) ∈ [−1, 1], periódico em t (o laço passa o segundo da volta)."""
    return h32(semente * 1000003 + t) / 4294967295 * 2 - 1


def arred(x, casas):
    """Como a tela mostra: floor(x·10^casas + 0,5) / 10^casas, com −0 → 0 (sem o round() do Python, que vai pelo par)."""
    p = 10 ** casas
    v = math.floor(x * p + 0.5) / p
    return 0.0 if v == 0 else v


def casas_de(campos, c):
    return (campos.get(c) or {}).get('casas', 0)


def laco_valor(R, campos, c, t):
    """Valor do campo c no segundo t (0…149) da volta: interpolação das chaves (o segmento 145 → 150 usa o t = 0), ruído e
    arredondamento pelas casas do D.campos; ângulo pelo arco menor e em [0, 360)."""
    ch = R['chaves'][c]
    passo = R.get('passo_chave', 5)
    k = t // passo
    f = (t - passo * k) / passo
    a, b = ch[k % len(ch)], ch[(k + 1) % len(ch)]
    ang = bool((campos.get(c) or {}).get('ang'))
    x = a + ((((b - a + 540) % 360) - 180) * f if ang else (b - a) * f)
    amp, sem = (R.get('ruido') or {}).get(c, [0, 0])
    if amp:
        x = x + amp * ruido(sem, t)
    x = arred(x, casas_de(campos, c))
    if ang:
        x = ((x % 360) + 360) % 360
    return 0.0 if x == 0 else x


def quadro_laco(R, campos, t):
    """Campos do laço e fixos no segundo t (a rota e os contadores do em() entram com o PORT_ROTA, no C8)."""
    q = {c: laco_valor(R, campos, c, t) for c in (R.get('chaves') or {})}
    q.update(R.get('fixos') or {})
    return q


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def nivel(limites, campos, campo, q):
    """CapitaoAgora.nivel(campo, q): {nivel, limite?, regime?} ou None (não avalia). Comparações estritas sobre o valor arredondado."""
    L = (limites or {}).get(campo)
    if not L:
        return None
    a = L.get('ativo_se')
    if a:
        x = q.get(a.get('campo'))
        if 'acima' in a:
            if not _num(x) or not arred(x, casas_de(campos, a['campo'])) > a['acima']:
                return None
        elif 'igual' in a:
            if type(x) is not type(a['igual']) or x != a['igual']:
                return None
    v = q.get(campo)
    if not _num(v):
        return None
    v = arred(v, casas_de(campos, campo))
    idx = None
    if 'regimes' in L:
        R = None
        for i, g in enumerate(L['regimes']):
            r = q.get(g.get('rpm_campo'))
            if not _num(r):
                continue
            r = arred(r, 0)
            if ('rpm_de' not in g or g['rpm_de'] <= r) and ('rpm_ate' not in g or r < g['rpm_ate']):
                R, idx = g, i
                break
        if R is None:
            return None
    else:
        R = L

    def fora(lim):
        if not lim:
            return None
        if 'abaixo' in lim and v < lim['abaixo']:
            return lim['abaixo']
        if 'acima' in lim and v > lim['acima']:
            return lim['acima']
        return None

    out = {'nivel': 'normal'}
    lc = fora(R.get('critico'))
    la = None if lc is not None else fora(R.get('aviso'))
    if lc is not None:
        out = {'nivel': 'critico', 'limite': lc}
    elif la is not None:
        out = {'nivel': 'aviso', 'limite': la}
    if idx is not None:
        out['regime'] = idx
    return out


def regime_de(L, nv):
    return L['regimes'][nv['regime']] if nv and 'regime' in nv else L


def limiares(R):
    return [R[k][kk] for k in ('normal', 'aviso', 'critico') if isinstance(R.get(k), dict)
            for kk in ('de', 'ate', 'abaixo', 'acima') if kk in R[k]]


# ——————————————————————————————— utilidades ———————————————————————————————
def junta(cam, k):
    if not cam:
        return str(k)
    return cam + str(k) if cam.endswith((':', '/')) else cam + '.' + str(k)


def textos(v, cam='', numeros=False):
    """(caminho, texto) de todo valor string, em profundidade. Com numeros, também as folhas numéricas (int e float, fora bool),
    pelo repr: é o texto que o serializador grava (MMSI9 e HEX15: nove dígitos guardados como número também contam)."""
    if isinstance(v, str):
        yield cam, v
    elif numeros and isinstance(v, (int, float)) and not isinstance(v, bool):
        yield cam, repr(v)
    elif isinstance(v, dict):
        for k, x in v.items():
            yield from textos(x, junta(cam, k), numeros)
    elif isinstance(v, (list, tuple)):
        for i, x in enumerate(v):
            yield from textos(x, '%s[%d]' % (cam, i), numeros)


def textos_fontes(F, numeros=False):
    """Fontes do Drive: CSV e HTML inteiros; JSON só nos valores string (número do JSON não entra), ou também nos números."""
    for rel, txt in sorted(F.items()):
        cam = 'fontes/' + rel
        if rel.endswith('.json'):
            yield from textos(json.loads(txt), cam + ':', numeros)
        else:
            yield cam, txt


def chaves_de(v, cam=''):
    """(caminho, chave) de toda chave de dicionário, em profundidade."""
    if isinstance(v, dict):
        for k, x in v.items():
            c = junta(cam, k)
            yield c, k
            yield from chaves_de(x, c)
    elif isinstance(v, (list, tuple)):
        for i, x in enumerate(v):
            yield from chaves_de(x, '%s[%d]' % (cam, i))


def palavras_chave(k):
    """Palavras do nome de uma chave, sem acento e em minúsculas: camelCase, '_', '-' e a troca letra/dígito separam
    ('hexId' → hex, id · 'telefone_marina' → telefone, marina · 'canal16' → canal, 16)."""
    return re.findall(r'[a-z]+|\d+', norm(re.sub(r'([a-zà-ÿ0-9])([A-Z])', r'\1 \2', str(k))))


def casado(m):
    """O texto casado, sem o caractere do fim de palavra que as regex sem lookbehind levam na frente ((?:^|[^A-Za-zÀ-ÿ]))."""
    s = m.group()
    if len(s) > 1 and not re.match(r'[0-9A-Za-zÀ-ÿ°%]', s[0]) and re.match(r'[0-9A-Za-zÀ-ÿ]', s[1]):
        s = s[1:]
    return s.strip()


def trecho(s, m, folga=30):
    i, j = max(0, m.start() - folga), min(len(s), m.end() + folga)
    return ('…' if i else '') + s[i:j].replace('\n', ' ') + ('…' if j < len(s) else '')


def cap(s):
    return s[:1].upper() + s[1:]


def secoes_html(txt):
    """[(título da seção, texto)] de uma página de fonte ('<h2>sec</h2><p>txt</p>'); o que vem antes do 1º <h2> é ''."""
    partes = re.split(r'<h2>(.*?)</h2>', txt)
    out = [('', partes[0])]
    for i in range(1, len(partes) - 1, 2):
        out.append((partes[i], partes[i + 1]))
    return out


def sem_tags(s):
    return re.sub(r'<[^>]+>', '', s).strip()


def ptbr(x):
    """Formas pt-BR de um número para procurar no texto do guia: 1.000 · 2,4 · 6,0 · 88."""
    out = set()
    x = float(x)
    if x.is_integer():
        i = int(x)
        out |= {str(i), '{:,}'.format(i).replace(',', '.')}
        out |= {s + ',0' for s in list(out)}
    else:
        s = repr(x)
        inteiro, dec = s.split('.')
        out |= {inteiro + ',' + dec, '{:,}'.format(int(inteiro)).replace(',', '.') + ',' + dec}
    return out


def tem_numero(texto, x):
    return any(re.search(r'(?<![\d.,])' + re.escape(c) + r'(?![\d]|[.,]\d)', texto) for c in ptbr(x))


# ——————————————————————————————— contexto ———————————————————————————————
class Ctx:
    def __init__(self, D, base, fontes, saidas, faq=None, rodape=None, listas=None, avanti=None, const=None):
        self.D, self.base, self.fontes, self.saidas = D, base or {}, fontes or {}, saidas or {}
        self.faq, self.rodape, self.listas, self.avanti = faq, rodape, listas, avanti
        self.const = const or {}
        self.simulacao = D.get('simulacao') is True
        self.termos = carrega_termos()
        self.lugar = lugar_a_bordo(self.termos)
        self.arq = (D.get('drive') or {}).get('arquivos') or {}
        self.pastas = (D.get('drive') or {}).get('pastas') or {}
        self.R = D.get('replay') if isinstance(D.get('replay'), dict) else None
        self.campos = D.get('campos') or {}
        self.limites = (self.R or {}).get('limites') or {}
        self.equip = [e for e in (D.get('equipamentos') or []) if isinstance(e, dict)]
        self.agenda = [t for t in (D.get('agenda') or []) if isinstance(t, dict)]
        self.trechos = [t for t in (self.base.get('trechos') or []) if isinstance(t, dict)]
        self.itens_faq = [i for i in ((faq or {}).get('itens') or []) if isinstance(i, dict)]
        self._laco = None

    def todos(self, numeros=False):
        """(caminho, texto) de todo valor string do D, da base, do FAQ e das fontes do Drive (com numeros, também os números)."""
        yield from textos(self.D, '', numeros)
        yield from textos(self.base, 'base:', numeros)
        if self.faq is not None:
            yield from textos(self.faq, 'faq:', numeros)
        yield from textos_fontes(self.fontes, numeros)

    def chaves(self):
        """(caminho, chave) de toda chave do D, da base, do FAQ e dos JSON das fontes do Drive (os mesmos prefixos do todos())."""
        yield from chaves_de(self.D, '')
        yield from chaves_de(self.base, 'base:')
        if self.faq is not None:
            yield from chaves_de(self.faq, 'faq:')
        for rel, txt in sorted(self.fontes.items()):
            if rel.endswith('.json'):
                yield from chaves_de(json.loads(txt), 'fontes/' + rel + ':')

    def laco(self):
        """Os 150 quadros do laço (campos do laço e fixos), calculados uma vez."""
        if self._laco is None:
            R = self.R or {}
            self._laco = [quadro_laco(R, self.campos, t) for t in range(R.get('duracao', 150))] if R.get('chaves') else []
        return self._laco

    def eq(self, i):
        return next((e for e in self.equip if e.get('id') == i), None)


def carrega_termos(caminho=PROIBIDOS):
    with open(caminho, encoding='utf-8') as f:
        T = json.load(f)
    return {k: re.compile(v['src'], re.I if 'i' in v['flags'] else 0) for k, v in T.items() if isinstance(v, dict) and 'src' in v}


def lugar_a_bordo(termos):
    """Lugar a bordo nos protocolos (§1.3: "nenhuma string tem ... nome de lugar a bordo"), com a lista de lugares da própria
    LOCAL_SEGURANCA (uma fonte só, sem lista paralela, PROMPT §3). A LOCAL_SEGURANCA pede o equipamento antes do lugar, na mesma
    frase; aqui o lugar vale sozinho, em qualquer ordem."""
    src = termos['LOCAL_SEGURANCA'].pattern
    partes = src.split(r'[^.\n]{0,60}')
    if len(partes) != 2 or not partes[1].startswith('(?:'):
        raise SystemExit('confere.py: a LOCAL_SEGURANCA do proibidos.json mudou de forma (equipamento[^.\\n]{0,60}lugar); ajuste lugar_a_bordo()')
    return re.compile(r'(?:^|[^A-Za-zÀ-ÿ])' + partes[1], re.I)


# ——————————————————————————————— asserções (§6.3) ———————————————————————————————
def a_termos(X):
    rot = re.compile(re.escape(ROTULO), re.I)   # a EXCEÇÃO do §3 é o texto fixo, nunca o protocolos.rotulo do dado
    out = []
    for cam, s in X.todos():
        if cam in EXCECAO_TERMOS:
            continue
        s = rot.sub(' ', s)   # o rótulo do procedimento padrão é EXCEÇÃO do §3
        for k, r in X.termos.items():
            m = r.search(s)
            if m:
                out.append('%s: %s «%s»' % (k, cam, trecho(s, m)))
    return out


def a_nulo(X):
    out = []

    def anda(v, cam):
        if v is None:
            out.append(cam + ': None')
        elif isinstance(v, str):
            if v == '':
                out.append(cam + ": ''")
        elif isinstance(v, float):
            if not math.isfinite(v):
                out.append('%s: %r' % (cam, v))
            elif v == 0 and math.copysign(1, v) < 0:
                out.append(cam + ': -0')
        elif isinstance(v, dict):
            for k, x in v.items():
                anda(x, junta(cam, k))
        elif isinstance(v, (list, tuple)):
            if not v and cam != 'abastecimentos':   # a única lista vazia permitida (§1.0, §1.10)
                out.append(cam + ': lista vazia')
            for i, x in enumerate(v):
                anda(x, '%s[%d]' % (cam, i))
    anda(X.D, '')
    # Também os outros arquivos gerados que a IA e o buscaBase leem (§1.0, §1.5): a base, o FAQ e os JSON das fontes do Drive.
    anda(X.base, 'base:')
    if X.faq is not None:
        anda(X.faq, 'faq:')
    for rel, txt in sorted(X.fontes.items()):
        if rel.endswith('.json'):
            anda(json.loads(txt), 'fontes/' + rel + ':')
    return out


def a_simulacao_unica(X):
    js = X.saidas.get('capitao-dados.js', '')
    alvo = '"simulacao": ' + ('true' if X.simulacao else 'false')
    n, chaves = js.count(alvo), js.count('"simulacao":')
    out = [] if isinstance(X.D.get('simulacao'), bool) else ['simulacao não é bool']
    if n != 1 or chaves != 1:
        out.append('capitao-dados.js: %r %d vez(es), chave "simulacao" %d vez(es) (precisa de 1: o replay.py troca o texto)' % (alvo, n, chaves))
    return out


def a_tamanho(X):
    out = []
    for nome, kb in TAMANHO_KB.items():
        txt = X.saidas.get(nome)
        if txt is not None and len(txt.encode('utf-8')) > kb * 1024:
            out.append('%s: %.1f KB (orçamento %d KB)' % (nome, len(txt.encode('utf-8')) / 1024, kb))
    return out


def a_mmsi9(X):
    """Nove dígitos fora de embarcacao.mmsi (§0.3), em string ou em número, uma violação por ocorrência, com os dígitos: a
    pendência prende o caminho, o número e quantas vezes ele aparece. E nada de "programe" perto de MMSI (§6.4, trava §2.2), também
    uma por ocorrência, com o verbo."""
    out = ['%s: %s «%s»' % (cam, m.group(), trecho(s, m)) for cam, s in X.todos(numeros=True) if cam != 'embarcacao.mmsi'
           for m in R_MMSI9.finditer(s)]
    out += ['%s: "%s" perto de MMSI «%s»' % (cam, (m.group(1) or m.group(2)).lower(), trecho(s, m)) for cam, s in X.todos()
            for m in R_PROGRAME_MMSI.finditer(s)]
    return out


def a_registro(X):
    E = X.D.get('embarcacao') or {}
    r = E.get('registro')
    if r is None and not X.simulacao:
        return []   # modo real: None = SEM DADOS
    if not isinstance(r, str):
        return ['embarcacao.registro ausente (dado completo na simulação, §1.2)']
    out = []
    if not R_REGISTRO.fullmatch(r):
        out.append('embarcacao.registro fora do formato AAA-00-0000')
    for nome, rx in (('placa', R_PLACAS[0]), ('placa Mercosul', R_PLACAS[1]), ('HIN', R_HIN), ('9 a 11 dígitos', R_9A11), ('HEX ID', R_HEX15)):
        if rx.search(r) or rx.search(r.replace('-', '')):
            out.append('embarcacao.registro imita %s' % nome)
    if X.termos['PESSOAIS'].search(r):
        out.append('embarcacao.registro casa a PESSOAIS')
    tie = next((d for d in (X.D.get('documentos') or []) if isinstance(d, dict) and d.get('id') == 'tie'), None)
    if tie is not None and tie.get('numero') != r:
        out.append('documentos[tie].numero diferente de embarcacao.registro')
    return out


def a_hex15(X):
    """Como a MMSI9: string e número, uma violação por ocorrência."""
    return ['%s: %s «%s»' % (cam, m.group(), trecho(s, m)) for cam, s in X.todos(numeros=True) for m in R_HEX15.finditer(s)]


def a_sem_indicativo(X):
    """§0.2: indicativo, HEX ID, telefone e lugar de equipamento de salvatagem não existem como campo, em todo o D, a base, o FAQ e
    os JSON das fontes (o indicativo só como texto de instrução em protocolos; o lugar só nos caminhos da LUGAR_PERMITIDO). E
    nenhum indicativo com prefixo real no texto, uma violação por ocorrência."""
    out = []
    for c, k in X.chaves():
        ps = palavras_chave(k)
        if 'indicativo' in ps and not c.startswith('protocolos.'):
            out.append(c + ': chave indicativo fora de protocolos')
        tipo = next((CHAVES_IDENT[p] for p in ps if p in CHAVES_IDENT), None)
        if tipo:
            out.append('%s: chave de %s (§0.2: não existe como campo)' % (c, tipo))
        if CHAVES_LUGAR & set(ps) and not CHAVES_HORA & set(ps) and not LUGAR_PERMITIDO.fullmatch(c):
            out.append('%s: chave de lugar fora dos campos de vocabulário fechado, do lugar do barco, do posto e dos prestadores '
                       '(§0.2: lugar de equipamento de salvatagem não existe como campo)' % c)
    out += ['%s: %s «%s»' % (cam, m.group(), trecho(s, m)) for cam, s in X.todos() for m in R_INDICATIVO.finditer(s)]
    return out


def a_afirma_real(X):
    """Uma violação por ocorrência, com a afirmação casada: a pendência prende o caminho e o texto de hoje."""
    return ['%s: %s «%s»' % (cam, m.group(1), trecho(s, m)) for cam, s in X.todos() for m in R_AFIRMA.finditer(s)]


def a_terceiros(X):
    """§6.4, trava §2.7 (dinheiro e terceiros), sem nome na §6.3. Papéis em lista fechada, nunca nome de terceiro: o quem da agenda
    e das tarefas da equipe e o who do diário fixo e do dia de bordo (§1.7, §1.9), e o papel dos prestadores (§1.11). Documentos sem
    número de apólice, NF ou licença (§1.8: só o TIE tem número): nenhuma chave de número ou de emissor fora do documentos[tie].numero
    (= o registro, REGISTRO), e nenhum número logo depois de apólice, nota fiscal, NF ou licença em texto nenhum."""
    D, R, out = X.D, X.R or {}, []
    dono = str((D.get('embarcacao') or {}).get('proprietario') or '').split()
    quem = set(PAPEIS_QUEM) | set(dono[:1])
    dbo = R.get('diaDeBordo') if isinstance(R.get('diaDeBordo'), dict) else {}
    for nome, lista, k in (('agenda', X.agenda, 'quem'), ('tarefasEquipe', D.get('tarefasEquipe') or [], 'quem'),
                           ('diario', D.get('diario') or [], 'who'), ('replay.diaDeBordo.diario', dbo.get('diario') or [], 'who')):
        for i, x in enumerate(lista):
            if isinstance(x, dict) and x.get(k) not in quem:
                out.append('%s.%s.%s: papel fora da lista fechada (§1.7): %r' % (nome, x.get('id', x.get('iso', i)), k, x.get(k)))
    for i, a in enumerate(((D.get('equipe') or {}).get('apoio')) or []):
        if isinstance(a, dict) and a.get('papel') not in PAPEIS_APOIO:
            out.append('equipe.apoio[%d].papel: papel fora da lista fechada (§1.11): %r' % (i, a.get('papel')))
    docs = [('documentos[%d]' % i, d) for i, d in enumerate(D.get('documentos') or [])]
    if isinstance(dbo.get('documento'), dict):
        docs.append(('replay.diaDeBordo.documento', dbo['documento']))
    for cam, d in docs:
        if not isinstance(d, dict):
            continue
        for c, k in chaves_de(d, cam):
            if CHAVES_DOC & set(palavras_chave(k)) and not (c == cam + '.numero' and d.get('id') == 'tie'):
                out.append('%s: chave de número ou emissor de documento (§1.8: só o TIE tem número)' % c)
    out += ['%s: número de documento [%s] «%s»' % (cam, m.group(1), trecho(s, m)) for cam, s in X.todos() for m in R_NUM_DOC.finditer(s)]
    return out


def a_sem_previsao(X):
    """§6.4, trava §2.5 (tempo e maré são do mundo real), sem nome na §6.3: nenhum campo de previsão ou de maré no D (o historico,
    o catálogo de campos e o replay inclusive), na base, no FAQ e nos JSON das fontes."""
    return ['%s: campo de previsão ou maré (tempo e maré só do Open-Meteo real)' % c for c, k in X.chaves()
            if CHAVES_PREVISAO & set(palavras_chave(k))]


def _positivo(v, tipo):
    if isinstance(v, bool):
        return False
    if tipo == 'int':
        return isinstance(v, int) and v > 0
    if tipo == 'num':
        return isinstance(v, (int, float)) and math.isfinite(v) and v > 0
    return isinstance(v, tipo) and len(v) > 0


def a_embarcacao(X):
    """§1.2 (o C4 da §6.2), sem nome na §6.3. Na simulação, os campos do §1.2 completos e com o tipo; no modo real (§4.2), o que é
    None fica (SEM DADOS) e o resto confere igual. rotulo = "<modelo> · <comprimento com 2 casas> m · <ano>"; motorizacao no
    formato "<n> × <motor> · <transmissão>" e, quando equipamentos[motores] já tem fabricante, modelo e qtd numérica (C5), com eles;
    un com as unidades do §1.2, só de campos numéricos da embarcação; tanques com os 5 volumes, o de diesel igual à capacidade do
    snapshot; 1 ≤ pessoasBordo ≤ lotacao; e o número das linhas do diário fixo com "N pessoas a bordo" (a saída) = pessoasBordo."""
    E = X.D.get('embarcacao')
    if not isinstance(E, dict):
        return ['embarcacao ausente']
    out = []
    for k, tipo in CAMPOS_EMBARCACAO:
        if E.get(k) is None and not X.simulacao:
            continue   # modo real: None = SEM DADOS
        if not _positivo(E.get(k), tipo):
            out.append('embarcacao.%s ausente ou fora do tipo (dado completo na simulação, §1.2): %r' % (k, E.get(k)))
    n = lambda k: E.get(k) if _positivo(E.get(k), 'int') else None
    if n('lotacao') and n('pessoasBordo') and E['pessoasBordo'] > E['lotacao']:
        out.append('embarcacao: lotacao (%d) < pessoasBordo (%d)' % (E['lotacao'], E['pessoasBordo']))
    if all(_positivo(E.get(k), t) for k, t in (('modelo', str), ('comprimento', 'num'), ('ano', 'int'))):
        esperado = '%s · %s m · %d' % (E['modelo'], ('%.2f' % E['comprimento']).replace('.', ','), E['ano'])
        if isinstance(E.get('rotulo'), str) and E['rotulo'] != esperado:
            out.append('embarcacao.rotulo ≠ o gerado dos campos (%r)' % esperado)
    mot = E.get('motorizacao')
    if isinstance(mot, str) and mot:
        m = R_MOTORIZACAO.fullmatch(mot)
        if not m:
            out.append('embarcacao.motorizacao fora do formato "<n> × <motor> · <transmissão>": %r' % mot)
        eq = X.eq('motores') or {}
        if m and all(isinstance(eq.get(k), str) and eq.get(k) for k in ('fabricante', 'modelo')) and _positivo(eq.get('qtd'), 'int'):
            if (int(m.group(1)), m.group(2)) != (eq['qtd'], eq['fabricante'] + ' ' + eq['modelo']):
                out.append('embarcacao.motorizacao ≠ qtd, fabricante e modelo de equipamentos[motores]')
    un = E.get('un') if isinstance(E.get('un'), dict) else {}
    for k, u in UN_EMBARCACAO.items():
        if un.get(k) != u and not (E.get(k) is None and not X.simulacao):
            out.append('embarcacao.un.%s ≠ %r' % (k, u))
    for k in un:
        v = E.get(k)
        if k not in UN_EMBARCACAO or (v is not None and not _positivo(v, 'num')):
            out.append('embarcacao.un.%s: unidade de campo que não é número da embarcação' % k)
    T = E.get('tanques') if isinstance(E.get('tanques'), dict) else {}
    for k in TANQUES_EMBARCACAO:
        if T and not _positivo(T.get(k), 'num'):
            out.append('embarcacao.tanques.%s ausente ou fora do tipo: %r' % (k, T.get(k)))
    cap_ = ((X.D.get('snapshot') or {}).get('diesel') or {}).get('capacidade')
    if _num(cap_) and _positivo(T.get('diesel_l'), 'num') and cap_ != T['diesel_l']:
        out.append('embarcacao.tanques.diesel_l ≠ snapshot.diesel.capacidade')
    for i, x in enumerate(X.D.get('diario') or []):
        t = x.get('t') if isinstance(x, dict) else None
        for mm in R_PESSOAS_BORDO.finditer(t if isinstance(t, str) else ''):
            if n('pessoasBordo') and int(mm.group(1)) != E['pessoasBordo']:
                out.append('diario[%d]: %s pessoas a bordo ≠ embarcacao.pessoasBordo (%d)' % (i, mm.group(1), E['pessoasBordo']))
    return out


def partes_modelo(modelo):
    """Partes de um modelo (separadas por ' · ', ' e ' e ' + '); parte só com número ("16000 e 12000") herda o nome da anterior."""
    out, ant = [], ''
    for p in re.split(r' · | e | \+ ', modelo or ''):
        p = p.strip()
        if not p:
            continue
        if not re.search(r'[A-Za-zÀ-ÿ]', p) and ant:
            p = ' '.join(w for w in ant.split() if re.search(r'[A-Za-zÀ-ÿ]', w)) + ' ' + p
        out.append(p)
        ant = p
    return out


def nomes_equip(X):
    """Fabricante e candidatos do modelo de cada equipamento gerado (para PROTOCOLO_LIMPO e AGENDA), pela mesma regra da
    candidatos_modelo() (§2.5): parte ou base com menos de 4 letras, ou sem dígito, vai com o fabricante na frente. Solta, a parte
    "V2" do Lewmar casava o "v2" de "Capitão IA v2" no protocolos.fonte do §1.3."""
    out = []
    for e in X.equip:
        fab = e.get('fabricante') if isinstance(e.get('fabricante'), str) else ''
        mod = e.get('modelo') if isinstance(e.get('modelo'), str) else ''
        for v in [fab] + candidatos_modelo(fab, mod):
            if v.strip() and (e.get('id'), v.strip()) not in out:
                out.append((e.get('id'), v.strip()))
    return out


def acha_nomes(s, nome):
    """Cada ocorrência do nome como palavra inteira, sem distinguir maiúsculas (o grupo 1 é o nome casado)."""
    return re.finditer(r'(?:^|[^A-Za-zÀ-ÿ0-9])(' + re.escape(nome) + r')(?![A-Za-zÀ-ÿ0-9])', s, re.I)


def a_protocolo_limpo(X):
    """Cada regra uma violação por ocorrência, com o texto casado: a pendência prende o caminho, a regra e o texto de hoje (um 2º
    "ETA" ou "último fix" numa string que já é pendência reprova)."""
    P = X.D.get('protocolos')
    if P is None:
        return []
    out = []
    nomes = []   # um nome por grafia: o "Garmin" dos plotters e do radar é uma ocorrência só no texto
    for _, n in nomes_equip(X):
        if n.lower() not in [x.lower() for x in nomes]:
            nomes.append(n)
    for cam, s in textos(P, 'protocolos'):
        for nome, rx in R_PROTOCOLO + (('lugar a bordo', X.lugar),):
            out += ['%s: %s [%s] «%s»' % (cam, nome, casado(m), trecho(s, m)) for m in rx.finditer(s)]
        for n in nomes:
            out += ['%s: fabricante ou modelo de equipamento [%s] «%s»' % (cam, m.group(1), trecho(s, m)) for m in acha_nomes(s, n)]
    return out


def a_local_vocab(X):
    out = []
    t_prot, t_ck = X.arq.get('protocolo'), X.arq.get('checklist')
    permitidas = {t_prot: {'Homem ao mar', 'Salvatagem'}, t_ck: {'Saída · antes de largar'}}
    # "boia" vale por origem: protocolos.mob, protocolos.salvatagem e o texto do checklist "Saída · antes de largar" (s13), em
    # qualquer cópia (trechos, páginas de fonte, cartões EM-04/EM-09 e o CK-03 do FAQ).
    s13 = set()
    for tipo, itens in (((X.D.get('checklists') or {}).get('itens')) or {}).items():
        for i, it in enumerate(itens or []):
            if isinstance(it, dict) and it.get('id') == 's13':
                s13.add('checklists.itens.%s[%d].' % (tipo, i))
    for cam, s in textos(X.D):
        if not R_BOIA.search(s):
            continue
        ok = cam.startswith(('protocolos.mob', 'protocolos.salvatagem')) or any(cam.startswith(p) for p in s13)
        m = re.match(r'faq\.(\w+)\.perguntas\[\d+\]\.passos\[(\d+)\]', cam)
        if m and not ok:   # D.faq (legado): passo tirado de uma seção permitida do protocolo ou do checklist
            fq = X.D['faq'][m.group(1)]
            for pq in fq.get('perguntas', []):
                for ps in pq.get('passos', []):
                    if ps.get('t') == s and ps.get('secao') in permitidas.get(fq.get('fonte'), ()):
                        ok = True
        if not ok:
            out.append('%s: "boia" fora da salvatagem, do homem ao mar e do checklist de saída' % cam)
    for i, t in enumerate(X.trechos):
        if any(R_BOIA.search(v) for v in t.values() if isinstance(v, str)) and t.get('secao') not in permitidas.get(t.get('fonte'), ()):
            out.append('base:trechos[%d] (%s · %s): "boia" fora de origem' % (i, t.get('fonte'), t.get('secao')))
    for it in X.itens_faq:
        if it.get('id') not in ('EM-04', 'EM-09', 'CK-03') and any(R_BOIA.search(s) for _, s in textos(it)):
            out.append('faq:%s: "boia" fora de origem' % it.get('id'))
    for rel, txt in X.fontes.items():
        if not R_BOIA.search(txt):
            continue
        tit = next((t for t in (t_prot, t_ck) if t and rel.endswith('/' + t + '.html')), None)
        for sec, corpo in secoes_html(txt):
            if R_BOIA.search(corpo) and (tit is None or sec not in permitidas[tit]):
                out.append('fontes/%s (%s): "boia" fora de origem' % (rel, sec or 'cabeçalho'))
    for chave in ('pecas', 'sensores', 'checklists'):
        for cam, s in textos(X.D.get(chave), chave):
            m = R_KIT.search(s)
            if m:
                out.append('%s: "kit" «%s»' % (cam, trecho(s, m)))
    for i, p in enumerate(((X.D.get('sensores') or {}).get('pontos')) or []):
        if isinstance(p, dict) and p.get('onde') not in ONDE_SENSORES:
            out.append('sensores.pontos[%d].onde fora do vocabulário fechado: %r' % (i, p.get('onde')))
    for i, p in enumerate(X.D.get('pecas') or []):
        if isinstance(p, dict) and not (isinstance(p.get('local'), str) and LOCAL_PECAS.fullmatch(p['local'])):
            out.append('pecas[%d].local fora do vocabulário fechado: %r' % (i, p.get('local')))
    return out


def no_minimo(X, t):
    """Chave de drive.arquivos do trecho, se a seção dele está no mínimo do §1.5 (MINIMO_SEGURANCA); senão None."""
    for k, secoes in MINIMO_SEGURANCA.items():
        if X.arq.get(k) and t.get('fonte') == X.arq[k]:
            sec = t.get('secao') or ''
            if secoes is None or sec in secoes or sec.split(' · ')[0] in secoes:
                return k
    return None


def a_seguranca_marcada(X):
    """Palavra da SEGURANCA_PALAVRAS em qualquer campo do trecho (fonte e equip inclusive: "Guia de bordo — EPIRB", "Sistema fixo
    de supressão de incêndio", "Protocolo de emergência") ou seção do mínimo do §1.5 ⇒ seguranca: true."""
    out = []
    for i, t in enumerate(X.trechos):
        if t.get('seguranca') is True:
            continue
        if segura(' '.join(str(t.get(k) or '') for k in ('fonte', 'equip', 'secao', 'texto'))):
            out.append('base:trechos[%d] (%s · %s) casa a SEGURANCA_PALAVRAS sem seguranca: true' % (i, t.get('fonte'), t.get('secao')))
        elif no_minimo(X, t):
            out.append('base:trechos[%d] (%s · %s) está no mínimo do §1.5 (%s) sem seguranca: true' % (i, t.get('fonte'), t.get('secao'), no_minimo(X, t)))
    for it in X.itens_faq:
        if it.get('seguranca') is True:
            continue
        if segura(' '.join(s for _, s in textos(it))):
            out.append('faq:%s casa a SEGURANCA_PALAVRAS sem seguranca: true' % it.get('id'))
        elif MINIMO_FAQ.fullmatch(str(it.get('id', ''))):
            out.append('faq:%s está no mínimo do §1.5/§1.6 sem seguranca: true' % it.get('id'))
    return out


def a_sem_salvatagem_em(X):
    out = []
    for i, p in enumerate(((X.D.get('sensores') or {}).get('pontos')) or []):
        for k in ('id', 'rotulo'):
            if isinstance(p, dict) and has(norm(p.get(k)), SALVATAGEM_EM):
                out.append('sensores.pontos[%d].%s: equipamento de salvatagem' % (i, k))
    for i, p in enumerate(X.D.get('pecas') or []):
        if isinstance(p, dict) and has(norm(p.get('n')), SALVATAGEM_EM):
            out.append('pecas[%d].n: peça de salvatagem' % i)
    return out


def a_calado_fora(X):
    out = ['base:trechos[%d] (%s · %s): "calado"' % (i, t.get('fonte'), t.get('secao'))
           for i, t in enumerate(X.trechos) if any('calado' in norm(s) for _, s in textos(t))]
    out += ['faq:%s: "calado"' % it.get('id') for it in X.itens_faq if any('calado' in norm(s) for _, s in textos(it))]
    return out


def saidas_texto(X):
    """Toda a saída do gerador, como texto: os arquivos da raiz e as fontes do Drive."""
    out = dict(X.saidas)
    out.update({'fontes/' + rel: txt for rel, txt in X.fontes.items()})
    return out


def a_modelos_avanti(X):
    """Ocorrências de cada termo das listas privadas em cada arquivo da saída, uma violação por par (termo, arquivo), com o
    número do termo na lista (#n) e a contagem: nenhum termo é impresso. Contar linhas não servia: o serializador põe cada lista
    numa linha só, e um 2º termo numa linha que já casava não mudava a conta."""
    if X.listas is None:
        return []
    out = []
    S = {k: v.lower() for k, v in saidas_texto(X).items()}
    for nome, termos in sorted(X.listas.items()):
        for i, t in enumerate(termos, 1):
            out += ['%s #%d: %s %d' % (nome, i, k, S[k].count(t)) for k in sorted(S) if t in S[k]]
    return out


def candidatos_modelo(fabricante, modelo):
    """Cada parte do modelo e a base dela (as duas primeiras palavras); parte ou base com menos de 4 letras ou sem dígito vai
    com o fabricante na frente ("Lewmar V2", "Raymarine Evolution"), §2.5."""
    out = []
    fab = (fabricante or '').strip()
    for p in partes_modelo(modelo):
        for c in (p, ' '.join(p.split()[:2])):
            if fab and (len(c) < 4 or not re.search(r'\d', c)) and not c.lower().startswith(fab.lower()):
                c = fab + ' ' + c
            if c not in out:
                out.append(c)
    return out


def a_colisao_modelos(X):
    out = []
    est = X.eq('estabilizador')
    if est and isinstance(est.get('nominal'), dict) and set(est['nominal']) != {'pct_estabiliza'}:
        out.append('equipamentos[estabilizador].nominal: só pct_estabiliza (sem número do fabricante, §2.5)')
    if X.avanti is None:
        return out
    for e in X.equip:
        if not isinstance(e.get('modelo'), str):
            continue
        for j, c in enumerate(candidatos_modelo(e.get('fabricante'), e['modelo']), 1):
            n = X.avanti.count(c.lower())
            if n > EXCECOES_MODELO.get(c, 0):   # só contagens: nem o texto da pasta do Avanti nem o candidato são impressos
                out.append('equipamentos[%s] candidato %d (%s): %d na pasta do Avanti (permitido %d)' % (
                    e.get('id'), j, assinatura(c), n, EXCECOES_MODELO.get(c, 0)))
    return out


def assinatura(texto):
    """12 hexas do SHA-256 do texto em minúsculas: prende a pendência ao candidato de hoje sem escrever o nome dele."""
    return hashlib.sha256(texto.lower().encode('utf-8')).hexdigest()[:12]


def a_fonte_limites(X):
    out = []
    for c, L in X.limites.items():
        f = L.get('fonte') if isinstance(L, dict) else None
        m = re.match(r'^(.*?)\s*§\s*(\d+)?\s*(?:·\s*)?(.*?)\s*$', f or '')
        if not m:
            out.append('limites.%s.fonte sem §: %r' % (c, f))
            continue
        tit, n, nome = m.group(1), m.group(2), m.group(3)
        tr = [t for t in X.trechos if t.get('fonte') == tit and (
            (t.get('secao') == n + ' · ' + nome) if n and nome else (t.get('secao', '').startswith(n + ' · ') if n else t.get('secao') == nome))]
        if not tr:
            out.append('limites.%s.fonte aponta para um § que não existe: %r' % (c, f))
            continue
        texto = tr[0].get('texto', '')
        nums = []
        for R in [L] + list(L.get('regimes') or []):
            nums += limiares(R) + [R[k] for k in ('rpm_de', 'rpm_ate') if k in R]
        faltam = [x for x in nums if not tem_numero(texto, x)]
        if faltam:
            out.append('limites.%s: %s sem os números %s' % (c, f, ', '.join(sorted({'/'.join(sorted(ptbr(x)))[:20] for x in faltam}))))
    return out


def a_equip(X):
    out = []
    guias = X.D.get('guias') or {}
    for i, e in enumerate(X.equip):
        for k in ('fabricante', 'modelo'):
            if not (isinstance(e.get(k), str) and e[k].strip()):
                out.append('equipamentos[%s].%s ausente' % (e.get('id', i), k))
        if not _num(e.get('qtd')):
            out.append('equipamentos[%s].qtd não é número: %r' % (e.get('id', i), e.get('qtd')))
        if e.get('guia') not in guias:
            out.append('equipamentos[%s].guia fora de D.guias: %r' % (e.get('id', i), e.get('guia')))
    return out


def a_ids(X):
    D, out = X.D, []
    ag = {t.get('id'): t for t in X.agenda}
    docs = {d.get('id') for d in (D.get('documentos') or []) if isinstance(d, dict)}
    sistemas = {e.get('id') for e in X.equip} | SISTEMAS_EXTRA
    ck = D.get('checklists')
    if isinstance(ck, dict):
        tipos = [t.get('id') for t in ck.get('tipos') or [] if isinstance(t, dict)]
        if tuple(tipos) != TIPOS_CHECKLIST:
            out.append('checklists.tipos: %r (precisa dos 4: %s)' % (tipos, ', '.join(TIPOS_CHECKLIST)))
        ids_faq = {it.get('id') for it in X.itens_faq}
        for tipo, itens in (ck.get('itens') or {}).items():
            for it in itens or []:
                if not (isinstance(it.get('c'), str) and it['c'].strip()):
                    out.append('checklists.itens.%s.%s sem c' % (tipo, it.get('id')))
                if 'faq' in it and X.faq is not None and it['faq'] not in ids_faq:
                    out.append('checklists.itens.%s.%s.faq fora do FAQ: %r' % (tipo, it.get('id'), it['faq']))
    for p in D.get('pecas') or []:
        for t in p.get('tarefas') or []:
            if t not in ag:
                out.append('pecas.%s.tarefas: %r fora da agenda' % (p.get('id'), t))
    pontos = ((D.get('sensores') or {}).get('pontos')) or []
    if pontos:
        usados = set()
        for p in pontos:
            for c in p.get('campos') or []:
                usados.add(c)
                if c not in X.campos:
                    out.append('sensores.%s.campos: %r fora de D.campos' % (p.get('id'), c))
        out += ['sensores: os campos não cobrem %r (F08/F33)' % c for c in CAMPOS_F08_F33 if c not in usados]
        filas = {}
        for p in pontos:
            for plat, b in (p.get('bloco') or {}).items():
                filas.setdefault((p.get('vista'), plat, b[1]), []).append((b[0], p.get('id')))
        for (vista, plat, by), bs in filas.items():
            bs.sort()
            for (x1, i1), (x2, i2) in zip(bs, bs[1:]):
                if x2 - x1 < 0.10 - 1e-9:
                    out.append('sensores: blocos %s e %s a menos de 0,10 na fileira %s/%s/%s' % (i1, i2, vista, plat, by))
    for m in ((D.get('alarmesPedidos') or {}).get('metricas')) or []:
        for c in m.get('campos') or []:
            if c not in X.campos:
                out.append('alarmesPedidos.%s.campos: %r fora de D.campos' % (m.get('id'), c))
        fx = m.get('faixa')
        if not (isinstance(fx, list) and len(fx) == 2 and _num(fx[0]) and _num(fx[1]) and fx[0] < fx[1]):
            out.append('alarmesPedidos.%s.faixa: %r' % (m.get('id'), fx))
    for nome, lista in (('agenda', X.agenda), ('tarefasEquipe', D.get('tarefasEquipe') or []),
                        ('replay.alertas', list(((X.R or {}).get('alertas') or {}).values()))):
        for t in lista:
            if t.get('sistema') not in sistemas:
                out.append('%s.%s.sistema fora do vocabulário (ids de equipamentos, casco, tanques): %r' % (nome, t.get('id', t.get('campo')), t.get('sistema')))
    for d in D.get('documentos') or []:
        if 'ref' in d and d['ref'] not in ag and d['ref'] not in docs:
            out.append('documentos.%s.ref inexistente: %r' % (d.get('id', d.get('n')), d['ref']))
    for e in D.get('diario') or []:
        if 'ref' in e and e['ref'] not in ag and e['ref'] not in docs:
            out.append('diario.%s.ref inexistente: %r' % (e.get('id', e.get('iso')), e['ref']))
        if e.get('pend'):
            ref = ag.get(e.get('ref'))
            if ref is None:
                out.append('diario.%s: pendência sem ref na agenda' % e.get('id', e.get('iso')))
            elif not e.get('palavras') or e.get('palavras') != ref.get('palavras'):
                out.append('diario.%s.palavras diferentes das da tarefa %s' % (e.get('id', e.get('iso')), ref.get('id')))
    dbo = (X.R or {}).get('diaDeBordo')
    if isinstance(dbo, dict):
        abs_ = {'ab-%d' % k for k in range(dbo.get('dias', 0))}
        for x in list(dbo.get('diario') or []) + ([dbo['documento']] if isinstance(dbo.get('documento'), dict) else []):
            if 'ref' in x and x['ref'] not in abs_:
                out.append('replay.diaDeBordo.%s.ref fora de ab-0…ab-%d: %r' % (x.get('id'), dbo.get('dias', 0) - 1, x['ref']))
    return out


def a_laco(X):
    R = X.R
    if R is None:
        return []
    out = []
    n = R.get('duracao', 150) // R.get('passo_chave', 5)
    for c, ch in (R.get('chaves') or {}).items():
        if not (isinstance(ch, list) and len(ch) == n and all(_num(x) for x in ch)):
            out.append('replay.chaves.%s: precisa de %d números finitos' % (c, n))
    C = X.campos
    for c, d in C.items():
        if d.get('origem') not in ORIGENS:
            out.append('campos.%s.origem fora de %s: %r' % (c, sorted(ORIGENS), d.get('origem')))
        if (d.get('origem') == 'contador') != ('sentido' in d) or ('sentido' in d and d['sentido'] not in (1, -1)):
            out.append('campos.%s: sentido (+1/−1) em todo contador e só neles' % c)
    for grupo, origem in (('chaves', 'laço'), ('fixos', 'fixo'), ('contadores_base', 'contador')):
        dados = set(R.get(grupo) or {})
        cat = {c for c, d in C.items() if d.get('origem') == origem}
        out += ['replay.%s.%s fora de D.campos com origem %s' % (grupo, c, origem) for c in sorted(dados - cat)]
        out += ['campos.%s (origem %s) sem valor em replay.%s' % (c, origem, grupo) for c in sorted(cat - dados)]
    out += ['campos: falta %s (PROMPT, Fase 1)' % c for c in CAMPOS_FASE1 if c not in C]
    sq = ((X.D.get('snapshot') or {}).get('quadro'))
    if isinstance(sq, dict):
        out += ['snapshot.quadro.%s fora de D.campos' % c for c in sq if c not in C]
        out += ['snapshot.quadro sem %s (só faltam os de origem rota ou janela)' % c for c, d in C.items()
                if c not in sq and d.get('origem') not in ('rota', 'janela')]
    if any(d.get('origem') in ('rota', 'derivado', 'relógio', 'janela') for d in C.values()) and PORT_ROTA is None:
        out.append('quadro ⇔ catálogo nos campos de rota, derivado, relógio e janela: falta o port do em() (C8)')
    return out


def a_limites_forma(X):
    out = []
    for c, L in X.limites.items():
        if '*' in c or c not in X.campos:
            out.append('limites.%s: chave com curinga ou fora de D.campos' % c)
            continue
        if 'regimes' in L and any(k in L for k in ('normal', 'aviso', 'critico')):
            out.append('limites.%s: com regimes, o topo não tem normal/aviso/critico' % c)
        a = L.get('ativo_se')
        if a is not None and not (isinstance(a, dict) and a.get('campo') in X.campos and (('acima' in a) != ('igual' in a))):
            out.append('limites.%s.ativo_se: precisa de campo do catálogo e de acima ou igual' % c)
        regs = L.get('regimes') or [L]
        for i, R in enumerate(regs):
            nrm, av = R.get('normal') or {}, R.get('aviso') or {}
            if not nrm:
                out.append('limites.%s[%d]: sem normal' % (c, i))
            if nrm.get('de') != av.get('abaixo') or nrm.get('ate') != av.get('acima'):
                out.append('limites.%s[%d]: o normal termina no aviso (de = abaixo, ate = acima)' % (c, i))
        out += casos_de_borda(X, c, L)
    return out


def casos_de_borda(X, c, L):
    """Casos de borda do §3.3 pelo port da nivel: valor = limite → normal; limite ± 1 unidade da última casa → o nível de fora;
    rpm 999 e 1.000 nos regimes; ativo_se desligado → None."""
    out, un = [], 10 ** -casas_de(X.campos, c)
    a = L.get('ativo_se') or {}
    regs = L.get('regimes') or [L]
    for i, R in enumerate(regs):
        q = {}
        if a.get('campo'):
            q[a['campo']] = a['acima'] + 1 if 'acima' in a else a.get('igual')
        if 'regimes' in L:
            q[R['rpm_campo']] = R['rpm_ate'] - 1 if 'rpm_ate' in R else R.get('rpm_de', 0)
            if a.get('campo') == R['rpm_campo'] and 'acima' in a and q[R['rpm_campo']] <= a['acima']:
                q[R['rpm_campo']] = a['acima'] + 1
        cr = R.get('critico') or {}

        def esperado(v):
            if ('abaixo' in cr and v < cr['abaixo']) or ('acima' in cr and v > cr['acima']):
                return 'critico'
            av = R.get('aviso') or {}
            return 'aviso' if ('abaixo' in av and v < av['abaixo']) or ('acima' in av and v > av['acima']) else 'normal'
        provas = []
        for k, sinal in (('de', -1), ('ate', +1)):
            if k in (R.get('normal') or {}):
                lim = R['normal'][k]
                provas += [lim, arred(lim + sinal * un, casas_de(X.campos, c))]
        for k, sinal in (('abaixo', -1), ('acima', +1)):
            if k in cr:
                provas += [cr[k], arred(cr[k] + sinal * un, casas_de(X.campos, c))]
        for v in provas:
            q2 = dict(q, **{c: v})
            nv = nivel(X.limites, X.campos, c, q2) or {}
            reg = i if 'regimes' in L else None
            if nv.get('nivel') != esperado(v) or nv.get('regime') != reg:
                out.append('limites.%s[%d]: nivel(%s) = %s (regime %s), esperado %s (regime %s)' % (
                    c, i, v, nv.get('nivel'), nv.get('regime'), esperado(v), reg))
    if a.get('campo') and 'acima' in a:
        q = {a['campo']: a['acima'], c: 0}
        for R in regs:
            if 'rpm_campo' in R and R['rpm_campo'] != a['campo']:
                q[R['rpm_campo']] = R.get('rpm_de', 0)
        if nivel(X.limites, X.campos, c, q) is not None:
            out.append('limites.%s: com %s = %s, nivel tem de ser None (não avalia)' % (c, a['campo'], a['acima']))
    return out


def a_janela(X):
    R = X.R
    if R is None or not R.get('chaves'):
        return []
    out = []
    js = R.get('janelas')
    if not isinstance(js, list):
        return ['replay.janelas ausente (derivadas pelo gerador, §1.16)']
    for j in js:
        if not (95 <= j.get('ini', -1) <= j.get('fim', -1) <= 120 and j['fim'] - j['ini'] + 1 >= 10):
            out.append('replay.janelas.%s: precisa ficar em [95, 120] e durar ≥ 10 s (%s–%s)' % (j.get('id'), j.get('ini'), j.get('fim')))
        if j.get('ini', 0) <= 60 <= j.get('fim', -1):
            out.append('replay.janelas.%s cobre t = 60' % j.get('id'))
    if not any(j.get('ini', 0) <= 105 <= j.get('fim', -1) for j in js):
        out.append('nenhuma janela cobre t = 105')
    vistos = set()
    for t, q in enumerate(X.laco()):
        for c in X.limites:
            if c not in q:
                continue
            nv = nivel(X.limites, X.campos, c, q)
            n = nv['nivel'] if nv else None
            dentro = [j for j in js if j.get('campo') == c and j.get('ini', 0) <= t <= j.get('fim', -1)]
            if n in ('aviso', 'critico') and not any(j.get('nivel') == n for j in dentro) and (c, n) not in vistos:
                vistos.add((c, n))
                out.append('%s = %s em t = %d (%s) fora das janelas' % (c, q[c], t, n))
            for j in dentro:
                if n != j.get('nivel') and (c, j.get('id'), 'j') not in vistos:
                    vistos.add((c, j.get('id'), 'j'))
                    out.append('replay.janelas.%s: em t = %d o nível é %s, não %s' % (j.get('id'), t, n, j.get('nivel')))
            if n == 'critico' and R.get('cenario') == 'aviso' and (c, 'crit') not in vistos:
                vistos.add((c, 'crit'))
                out.append('%s crítico em t = %d com o cenário aviso' % (c, t))
    return out


def a_fio(X):
    out, vistos = [], set()
    for t, q in enumerate(X.laco()):
        for c, L in X.limites.items():
            if c not in q or c in vistos:
                continue
            nv = nivel(X.limites, X.campos, c, q)
            if nv is None:
                continue
            v = arred(q[c], casas_de(X.campos, c))
            perto = [x for x in limiares(regime_de(L, nv)) if round(abs(v - x), 9) < 0.05]
            if perto:
                vistos.add(c)
                out.append('%s = %s em t = %d, a menos de 0,05 do limite %s' % (c, v, t, perto[0]))
    return out


def _passo(v1, v0, ang):
    d = abs(v1 - v0)
    return min(d, 360 - d) if ang else d


def a_emenda(X):
    Q = X.laco()
    if not Q:
        return []
    out = []
    for c in (X.R.get('chaves') or {}):
        ang = bool((X.campos.get(c) or {}).get('ang'))
        vs = [q[c] for q in Q]
        maior = max(_passo(vs[t + 1], vs[t], ang) for t in range(len(vs) - 1))
        if round(_passo(vs[-1], vs[0], ang) - maior, 9) > 0:
            out.append('%s: |v(%d) − v(0)| = %s > maior passo de 1 s (%s)' % (c, len(vs) - 1, round(_passo(vs[-1], vs[0], ang), 6), round(maior, 6)))
    return out


def a_emenda_rota(X):
    rota = X.D.get('rota')
    if not isinstance(rota, dict):
        return []
    out = []
    voltas = ((X.R or {}).get('por_dia') or {}).get('voltas', 576)
    if math.gcd(int(rota.get('circuitos_dia', 0)), int(voltas)) != 1:
        out.append('rota.circuitos_dia %r não é primo com as %d voltas do dia' % (rota.get('circuitos_dia'), voltas))
    if PORT_ROTA is None:
        out.append('emendas de 150 s da rota: falta o port do em() (C8)')
    return out


def a_piso(X):
    R = X.R
    if R is None or 'contadores_base' not in R:
        return []
    try:
        if R['contadores_base']['diesel_litros'] - R['por_dia']['diesel_l'] >= R['diesel_piso_l'] + 50:
            return []
    except (KeyError, TypeError):
        return ['replay: contadores_base.diesel_litros, por_dia.diesel_l e diesel_piso_l são obrigatórios']
    return ['diesel na âncora − consumo do dia < piso + 50 L: o piso agiria']


def a_horas(X):
    out = []
    R = X.R or {}
    base, pdia = R.get('contadores_base') or {}, R.get('por_dia') or {}
    for t in X.agenda:
        h = t.get('horas')
        if not isinstance(h, dict):
            continue
        cs = [c for c in h.get('campos') or [] if c in base]
        b = max(base[c] for c in cs) if cs else h.get('atual')
        dia = pdia.get('gerador_h' if any('gerador' in c for c in cs) else 'motor_h', 24) if cs else 24
        if not (_num(b) and _num(h.get('limite'))):
            out.append('agenda.%s.horas sem limite e base' % t.get('id'))
        elif not (h['limite'] - b >= 24 and h['limite'] - (b + dia) > 0):
            out.append('agenda.%s: folga de %.1f h na âncora (precisa de ≥ 24 h e de > 0 no fim do dia)' % (t.get('id'), h['limite'] - b))
    return out


def a_rota(X):
    rota = X.D.get('rota')
    if not isinstance(rota, dict):
        return []
    out = []
    pts = [rota.get('base') or {}] + list(rota.get('pontos') or [])
    calado = (X.D.get('embarcacao') or {}).get('calado')
    for p in pts:
        for k in ('nome', 'rel', 'perto'):
            if re.search(r'\d', str(p.get(k, ''))):
                out.append('rota.%s.%s com dígito' % (p.get('id'), k))
        if _num(calado) and not (_num(p.get('prof_m')) and p['prof_m'] >= calado + 4):
            out.append('rota.%s.prof_m abaixo do calado + 4 m' % p.get('id'))
    for k in ('destino', 'volta'):
        for kk in ('nome', 'caminho'):
            if re.search(r'\d', str((rota.get(k) or {}).get(kk, ''))):
                out.append('rota.%s.%s com dígito' % (k, kk))
    pernas = rota.get('pernas') or []
    g = rota.get('guinada_max_gps') or 3
    nos = (((X.D.get('consumo') or {}).get('cruzeiro')) or {}).get('nos', 18)

    def arco(a, b):
        d = abs(((b - a + 540) % 360) - 180)
        return d / g * nos / 3600
    for i, p in enumerate(pernas):
        ant, prox = pernas[i - 1], pernas[(i + 1) % len(pernas)]
        maior = max(arco(ant['rumo'], p['rumo']), arco(p['rumo'], prox['rumo']))
        if not p.get('mn', 0) > 2 * maior:
            out.append('rota.pernas[%d] (%s → %s): %.2f mn ≤ 2 × arco de guinada (%.2f)' % (i, p.get('de'), p.get('para'), p.get('mn', 0), maior))
    pdia = ((X.R or {}).get('por_dia') or {}).get('distancia_mn')
    if _num(pdia):
        a, b = rota.get('circuitos_dia', 0) * rota.get('distancia_mn', 0), pdia * rota.get('fator', 0)
        if abs(a - b) > max(0.2, 1e-3 * b):
            out.append('rota: circuitos_dia × distancia_mn (%.2f) ≠ por_dia × fator (%.2f)' % (a, b))
    return out


def a_dia_de_bordo(X):
    R = X.R or {}
    dbo = R.get('diaDeBordo')
    out = []
    hora = R.get('ancora_hora', '07:00')
    linhas = list(X.D.get('diario') or [])
    if isinstance(dbo, dict):
        linhas += list(dbo.get('diario') or [])
        if any(isinstance(d, dict) and (d.get('cat') == 'Notas' or str(d.get('id', '')).startswith('nf')) for d in X.D.get('documentos') or []):
            out.append('documentos: a nota fiscal do abastecimento fica só em replay.diaDeBordo.documento')
        ab = dbo.get('abastecimento') or {}
        if ab.get('h') != hora:
            out.append('diaDeBordo.abastecimento.h ≠ ancora_hora')
        pdia = (R.get('por_dia') or {}).get('diesel_l')
        cap_ = ((X.D.get('embarcacao') or {}).get('tanques') or {}).get('diesel_l')
        base = (R.get('contadores_base') or {}).get('diesel_litros')
        if _num(pdia) and ab.get('litros') != math.floor(pdia + 0.5):
            out.append('diaDeBordo.abastecimento.litros ≠ round(por_dia.diesel_l)')
        if _num(pdia) and _num(cap_) and _num(base):
            if ab.get('nivelDepois') != arred(base / cap_ * 100, 1) or ab.get('nivelAntes') != arred((base - pdia) / cap_ * 100, 1):
                out.append('diaDeBordo.abastecimento: nivelAntes/nivelDepois fora do modelo de 24 h')
        ids = [x.get('id') for x in dbo.get('diario') or []]
        if ids[:2] != ['d01', 'd02']:
            out.append('diaDeBordo.diario: d01 antes da d02 (iso d01 = âncora + 1 s)')
        for x in dbo.get('diario') or []:
            if x.get('id') == 'd02' and x.get('h') != hora:
                out.append('d02.h ≠ ancora_hora')
            if x.get('id') == 'd01':
                m = re.search(r'(\d+) pessoas a bordo', x.get('t', ''))
                if not m or int(m.group(1)) != (X.D.get('embarcacao') or {}).get('pessoasBordo'):
                    out.append('d01: o número de pessoas a bordo ≠ embarcacao.pessoasBordo')
    for x in linhas:
        if x.get('diasAtras') == 0 and str(x.get('h', '99:99')) > hora:
            out.append('diário %s: diasAtras 0 depois da âncora (%s)' % (x.get('id'), x.get('h')))
    return out


def a_sem_emergencia(X):
    out = []
    R = X.R or {}
    fontes = [('diario', X.D.get('diario') or [], ('t',)), ('replay.diaDeBordo.diario', (R.get('diaDeBordo') or {}).get('diario') or [], ('t',)),
              ('agenda', X.agenda, ('t',))]
    for tipo, itens in ((((X.D.get('checklists') or {}).get('itens')) or {}).items()):
        fontes.append(('checklists.itens.' + tipo, itens or [], ('t', 'c')))
    for nome, lista, ks in fontes:
        for i, x in enumerate(lista):
            for k in ks:
                q = pad(x.get(k, ''))
                if emergencia(q) or oleo(q) == 1:
                    out.append('%s[%s].%s casa %s: %r' % (nome, x.get('id', i), k, 'emergencia()' if emergencia(q) else 'oleo() = 1', x.get(k)))
    return out


def a_agenda(X):
    out = []
    dias = DIAS_MESES_PADRAO   # a tabela fixa do §1.7 (31, 184, 365): a referência é daqui, nunca a do gerador conferido
    if X.const.get('DIAS_MESES', DIAS_MESES_PADRAO) != DIAS_MESES_PADRAO:
        out.append('DIAS_MESES do gerador ≠ o do §1.7 (%s)' % ', '.join('%d → %d' % kv for kv in sorted(DIAS_MESES_PADRAO.items())))
    nomes_seg = {i: [n for j, n in nomes_equip(X) if j == i] for i in ('epirb', 'seafire')}
    for t in X.agenda:
        i = t.get('id')
        if not (_num(t.get('ultimaHa')) and _num(t.get('venceEm')) and t.get('meses') in dias and t['ultimaHa'] + t['venceEm'] == dias[t['meses']]):
            out.append('agenda.%s: ultimaHa + venceEm ≠ DIAS_MESES[meses]' % i)
        ps = t.get('palavras')
        if not (isinstance(ps, list) and ps and all(isinstance(p, str) and len(p.split()) >= 2 for p in ps)):
            out.append('agenda.%s.palavras vazias ou com palavra solta' % i)
        if emergencia(pad(t.get('t', ''))):
            out.append('agenda.%s.t tem palavra da lista SOS' % i)
        if (t.get('seguranca') is True) != (i in SEGURANCA_AGENDA):
            out.append('agenda.%s: seguranca só (e sempre) em %s' % (i, ', '.join(sorted(SEGURANCA_AGENDA))))
        if str(i).startswith(('epirb', 'seafire')) and not (_num(t.get('venceEm')) and t['venceEm'] > 0):
            out.append('agenda.%s: tarefa de salvatagem atrasada' % i)
        for n in nomes_seg.get(t.get('sistema'), []):
            if next(acha_nomes(t.get('equip', ''), n), None):
                out.append('agenda.%s.equip com fabricante ou modelo de equipamento de segurança' % i)
    atr = sum(1 for t in X.agenda if _num(t.get('venceEm')) and t['venceEm'] < 0)
    if atr != 3:
        out.append('agenda: %d atrasadas (precisa de 3)' % atr)
    return out


def a_historico(X):
    H = X.D.get('historico')
    if not isinstance(H, dict):
        return []
    out = []
    for grupo in ('desvios', 'sazonal', 'cruzeiro'):
        for c, s in (H.get(grupo) or {}).items():
            if isinstance(s, dict) and 'd' in s and not all(_num(x) for x in s['d']):
                out.append('historico.%s.%s com valor não finito' % (grupo, c))
    met = H.get('metricas') or {}
    out += ['historico.metricas.%s: %r fora de D.campos' % (g, c) for g, cs in met.items() for c in cs if c not in X.campos]
    if (H.get('janelas') or {}).get('150S') != {'passo_s': 1, 'n': 150}:
        out.append("historico.janelas['150S'] ≠ {passo_s: 1, n: 150}")
    for g in H.get('so150') or []:
        if g not in met:
            out.append('historico.so150: %r fora das métricas' % g)
        elif any((X.campos.get(c) or {}).get('origem') != 'laço' for c in met[g]):
            out.append('historico.so150: %r tem campo fora do laço' % g)
    for c, s in ((H.get('sazonal') or {}).items()):
        if isinstance(s, dict) and len(s.get('d') or []) != 73:
            out.append('historico.sazonal.%s sem 73 pontos' % c)
    Q = X.laco()
    if Q:
        ar = (H.get('desvios') or {}).get('temp_ar_externo_c') or {}
        saz = ((H.get('sazonal') or {}).get('temp_ar_externo_c')) or {}
        d_ar = max([x / ar.get('escala', 1) for x in ar.get('d') or []] or [0])
        d_saz = (max(saz['d']) - min(saz['d'])) / saz.get('escala', 1) if saz.get('d') else 0
        for c, s in (H.get('desvios') or {}).items():
            if c not in Q[0] or not s.get('d'):
                continue
            vs = [q[c] for q in Q]
            dmin, dmax = min(s['d']) / s.get('escala', 1), max(s['d']) / s.get('escala', 1)
            nrm = (X.limites.get(c) or {}).get('normal') or {}
            if 'de' in nrm and min(vs) + dmin < nrm['de'] + 0.05 - 1e-9:
                out.append('historico.desvios.%s: o mínimo cruza o normal (%s)' % (c, nrm['de']))
            if 'ate' in nrm and max(vs) + dmax > nrm['ate'] - 0.05 + 1e-9:
                out.append('historico.desvios.%s: o máximo cruza o normal (%s)' % (c, nrm['ate']))
            if c == 'vento_verdadeiro_nos' and min(vs) + dmin < 0:
                out.append('historico.desvios.vento_verdadeiro_nos: vento negativo')
        pr = 'temp_praca_maquinas_c'
        ate = ((X.limites.get(pr) or {}).get('normal') or {}).get('ate')
        if pr in Q[0] and _num(ate) and max(q[pr] for q in Q) + d_ar + d_saz > ate - 0.05 + 1e-9:
            out.append('historico: praça de máquinas + desvio do ar cruza %s °C' % ate)
    return out


def a_coord_texto(X):
    """Uma violação por ocorrência, como as outras de texto."""
    return ['%s «%s»' % (cam, trecho(s, m)) for cam, s in X.todos() if cam != 'snapshot.gps.texto' for m in R_COORD.finditer(s)]


def rotulo_fim():
    """O fim dos textos de segurança (§1.5), com os textos fixos ROTULO e NOTA (nunca os do dado conferido)."""
    return cap(ROTULO) + '. ' + cap(NOTA) + '.'


def a_rotulo_seguranca(X):
    fim = rotulo_fim()
    out = []
    P = X.D.get('protocolos') or {}
    if 'rotulo' in P and P['rotulo'] != ROTULO:   # §1.3: o rótulo é a EXCEÇÃO do §3, letra por letra
        out.append('protocolos.rotulo ≠ o rótulo do procedimento padrão (EXCEÇÃO do §3, texto fixo)')
    guias = {X.arq[k] for k in ('g_seafire', 'g_epirb') if X.arq.get(k)}
    prot = X.arq.get('protocolo')
    for i, t in enumerate(X.trechos):
        if (t.get('fonte') in guias or (t.get('fonte') == prot and t.get('secao') == 'Salvatagem')) and not t.get('texto', '').rstrip().endswith(fim):
            out.append('base:trechos[%d] (%s · %s) sem o rótulo no fim' % (i, t.get('fonte'), t.get('secao')))
    for it in X.itens_faq:
        if str(it.get('id', '')).startswith(('SF-', 'EP-')) or it.get('id') == 'EM-09':
            if not str(it.get('resposta', '')).rstrip().endswith(fim):
                out.append('faq:%s sem o rótulo no fim da resposta' % it.get('id'))
    for rel, txt in X.fontes.items():
        g = next((t for t in guias if rel.endswith('/' + t + '.html')), None)
        p = prot and rel.endswith('/' + prot + '.html')
        if not (g or p):
            continue
        for sec, corpo in secoes_html(txt)[1:]:
            if (g or sec == 'Salvatagem') and not sem_tags(corpo).endswith(fim):
                out.append('fontes/%s (%s) sem o rótulo no fim' % (rel, sec))
    return out


def a_nota_etiqueta(X):
    nota = NOTA
    out = []
    if X.const.get('NOTA_ETIQUETA', NOTA) != NOTA:   # a constante do gerador é o texto fixo do §1.4
        out.append('NOTA_ETIQUETA do gerador ≠ o texto do §1.4 (%r)' % NOTA)
    for i in ('epirb', 'seafire'):
        e = X.eq(i)
        if e is not None and e.get('nota') != nota:
            out.append('equipamentos[%s].nota ≠ NOTA_ETIQUETA' % i)
        p = (X.D.get('protocolos') or {}).get(i)
        if isinstance(p, dict) and p.get('nota') != nota:
            out.append('protocolos.%s.nota ≠ NOTA_ETIQUETA' % i)
    return out


_RX_DEPOIS_DE = set('(,=:[!&|?{};+-*%<>~^')   # depois destes, '/' abre regex literal (senão é divisão)
_RX_PALAVRAS = {'return', 'typeof', 'case', 'do', 'else', 'in', 'of', 'new', 'delete', 'void', 'throw', 'instanceof', 'yield', 'await'}


def js_partes(js):
    """Varre o JavaScript do rodapé. Devolve (limpo, literais): limpo = o texto com os comentários trocados por espaços (quebras de
    linha e posições ficam); literais = [(ini, fim, tipo, conteúdo)] das strings ('…', "…": tipo 's', conteúdo sem as aspas), dos
    modelos (`…`, com os ${…} dentro: tipo 't') e das regex literais (/…/flags: tipo 'r'), que ficam intactos. Os comentários só
    saem fora dos literais: o '//' de 'https://' não apaga o resto da linha. Regex × divisão pelo token anterior."""
    out, lits, n = list(js), [], len(js)

    def apaga(a, b):
        for k in range(a, b):
            if out[k] != '\n':
                out[k] = ' '

    def string(i, q):   # i depois da aspa; devolve o índice depois da aspa de fecho (sem fecho: termina na linha)
        while i < n and js[i] != q and js[i] != '\n':
            i += 2 if js[i] == '\\' else 1
        return min(i + 1, n)

    def regex(i):   # i depois da 1ª barra; a barra dentro de [...] não fecha
        classe = False
        while i < n and js[i] != '\n':
            c = js[i]
            if c == '\\':
                i += 2
                continue
            if c == '/' and not classe:
                i += 1
                while i < n and (js[i].isalnum() or js[i] in '_$'):
                    i += 1
                return i
            classe = True if c == '[' else False if c == ']' else classe
            i += 1
        return i

    def modelo(i):   # i depois da crase
        while i < n:
            if js[i] == '\\':
                i += 2
            elif js[i] == '`':
                return i + 1
            elif js.startswith('${', i):
                i = codigo(i + 2, True)
            else:
                i += 1
        return n

    def codigo(i, chave):   # até o fim, ou até o '}' que fecha o ${…} de um modelo
        prof, ant = 0, ''
        while i < n:
            c = js[i]
            if c in ' \t\r\n':
                i += 1
            elif js.startswith('//', i) or js.startswith('/*', i):
                j = js.find('\n', i) if js[i + 1] == '/' else js.find('*/', i + 2)
                j = n if j < 0 else (j if js[i + 1] == '/' else j + 2)
                apaga(i, j)
                i = j
            elif c in '\'"`' or (c == '/' and (ant == '' or ant in _RX_DEPOIS_DE or ant in _RX_PALAVRAS)):
                j = string(i + 1, c) if c in '\'"' else modelo(i + 1) if c == '`' else regex(i + 1)
                tipo = {'`': 't', '/': 'r'}.get(c, 's')
                lits.append((i, j, tipo, js[i + 1:j - 1] if tipo == 's' else js[i:j]))
                i, ant = j, 'x'
            elif c.isalnum() or c in '_$':
                j = i
                while j < n and (js[j].isalnum() or js[j] in '_$'):
                    j += 1
                ant = js[i:j] if js[i:j] in _RX_PALAVRAS else 'x'
                i = j
            else:
                if chave and c == '}':
                    if prof == 0:
                        return i + 1
                    prof -= 1
                elif chave and c == '{':
                    prof += 1
                ant = c
                i += 1
        return n
    codigo(0, False)
    return ''.join(out), lits


# Formas de snapshot aceitas no rodapé (§6.3, §6.4): a leitura D.snapshot.quadro (também guardada: D.snapshot && D.snapshot.quadro),
# sem nada depois que escreva ou desça (=, op=, ++, --, '.', '?.', '['), e o valor fonte: 'snapshot'.
R_SNAP_LEITURA = re.compile(r'D\s*\.\s*snapshot\s*(?:&&\s*D\s*\.\s*snapshot\s*)?\.\s*quadro(?![\w$])')
R_SNAP_DEPOIS = re.compile(r'\s*(?:\?\.|\.|\[|=(?!=)|\*\*=|<<=|>>>?=|&&=|\|\|=|\?\?=|[-+*/%&|^]=|\+\+|--)')
R_SNAP_ANTES = re.compile(r'(?:(?:^|[^\w$])delete\s*|\+\+\s*|--\s*|(?:^|[^\w$])(?:assign|defineProperty|defineProperties|setPrototypeOf|freeze|seal'
                          r'|preventExtensions|set|deleteProperty)\s*\(\s*)$')
# Escrita (para o motivo): snapshot com membros e uma atribuição, ++/--, um método que muda o objeto, ou delete/assign antes.
R_SNAP_ESCRITA = re.compile(r'(?:\s*(?:\??\.\s*[\w$]+|\[[^\]]*\]))*\s*(?:=(?!=)|\*\*=|<<=|>>>?=|&&=|\|\|=|\?\?=|[-+*/%&|^]=|\+\+|--'
                            r'|\.\s*(?:push|pop|shift|unshift|splice|sort|reverse|fill|copyWithin)\s*\()')


def a_rodape_snapshot(X):
    """O rodapé nunca escreve no D.snapshot (§2.1 do PROMPT; trava 17). Cada 'snapshot' do código (fora dos comentários) tem de
    ser uma das duas formas aceitas, dentro de instante() e depois da guarda /SOS-/. Qualquer outra, mesmo só leitura (um alias
    como `var s = D.snapshot`, D['snapshot'], um modelo ou uma regex com o nome), reprova."""
    js = X.rodape
    if js is None:
        return []
    limpo, lits = js_partes(js)
    dentro = [False] * len(limpo)
    for a, b, _, _ in lits:
        for k in range(a, b):
            dentro[k] = True
    corpo = None
    for m in re.finditer(r'function\s+instante\s*\(|instante\s*[:=]\s*(?:function\b[^(]*)?\(|(?:^|[\s,{])instante\s*\([^)]*\)\s*\{', limpo):
        if dentro[m.start()]:
            continue
        i = next((k for k in range(m.end() - 1, len(limpo)) if limpo[k] == '{' and not dentro[k]), None)
        if i is None:
            break
        prof, j = 0, i
        for j in range(i, len(limpo)):
            if not dentro[j]:
                prof += {'{': 1, '}': -1}.get(limpo[j], 0)
                if prof == 0:
                    break
        corpo = (i, j)
        break
    guarda = next((b for a, b, t, v in lits if t == 'r' and v.startswith('/SOS-/') and corpo and corpo[0] < a < corpo[1]), None)
    out, vistos = [], set()
    for s in re.finditer(r'snapshot', limpo):
        p = s.start()
        if p in vistos:
            continue
        lit = [l for l in lits if l[0] <= p < l[1]]   # mais de um: string dentro do ${…} de um modelo
        linha = limpo.count('\n', 0, p) + 1
        aqui = trecho(limpo, s, 40)
        forma = None
        if lit:
            a, _, t, v = lit[0]
            if len(lit) == 1 and t == 's' and v == 'snapshot' and re.search(r'(?:^|[^\w$])fonte\s*:\s*$', limpo[:a]):
                forma = 'valor'
        else:
            mb = re.search(r'(?:^|[^\w$.])(D\s*\.\s*)$', limpo[:p])
            a = p - len(mb.group(1)) if mb else p
            ml = R_SNAP_LEITURA.match(limpo, a) if mb else None
            if ml and not R_SNAP_DEPOIS.match(limpo, ml.end()) and not R_SNAP_ANTES.search(limpo[:a]):
                forma = 'leitura'
                vistos.update(x.start() + a for x in re.finditer(r'snapshot', ml.group()))
            elif R_SNAP_ESCRITA.match(limpo, s.end()) or R_SNAP_ANTES.search(limpo[:a]):
                out.append('rodape.js:%d escreve em D.snapshot «%s»' % (linha, aqui))
                continue
        if forma is None:
            out.append("rodape.js:%d cita snapshot fora das formas aceitas (a leitura D.snapshot.quadro e o valor fonte: 'snapshot') «%s»"
                       % (linha, aqui))
        elif not (corpo and guarda is not None and guarda <= p < corpo[1]):
            out.append('rodape.js:%d cita snapshot fora de instante() ou antes da guarda /SOS-/ «%s»' % (linha, aqui))
    return out


def a_fontes_relativas(X):
    pastas = [X.pastas.get(k) for k in ('docs', 'agenda', 'diario', 'abast') if X.pastas.get(k)]
    out = []
    for rel, txt in sorted(X.fontes.items()):
        if rel.endswith('.csv') and rel.split('/')[0] in pastas:
            n = len(R_DATA.findall(txt))
            if n:
                out.append('fontes/%s: %d data(s) dd/mm/aaaa' % (rel, n))
    return out


ASSERCOES = [
    ('TERMOS', a_termos), ('NULO', a_nulo), ('SIMULACAO_UNICA', a_simulacao_unica), ('TAMANHO', a_tamanho), ('MMSI9', a_mmsi9),
    ('REGISTRO', a_registro), ('HEX15', a_hex15), ('SEM_INDICATIVO', a_sem_indicativo), ('AFIRMA_REAL', a_afirma_real),
    ('PROTOCOLO_LIMPO', a_protocolo_limpo), ('LOCAL_VOCAB', a_local_vocab), ('SEGURANCA_MARCADA', a_seguranca_marcada),
    ('SEM_SALVATAGEM_EM', a_sem_salvatagem_em), ('CALADO_FORA', a_calado_fora), ('MODELOS_AVANTI', a_modelos_avanti),
    ('COLISAO_MODELOS', a_colisao_modelos), ('FONTE_LIMITES', a_fonte_limites), ('EQUIP', a_equip), ('IDS', a_ids),
    ('LACO', a_laco), ('LIMITES_FORMA', a_limites_forma), ('JANELA', a_janela), ('FIO', a_fio), ('EMENDA', a_emenda),
    ('EMENDA_ROTA', a_emenda_rota), ('PISO', a_piso), ('HORAS', a_horas), ('ROTA', a_rota), ('DIA_DE_BORDO', a_dia_de_bordo),
    ('SEM_EMERGENCIA', a_sem_emergencia), ('AGENDA', a_agenda), ('HISTORICO', a_historico), ('COORD_TEXTO', a_coord_texto),
    ('ROTULO_SEGURANCA', a_rotulo_seguranca), ('NOTA_ETIQUETA', a_nota_etiqueta), ('RODAPE_SNAPSHOT', a_rodape_snapshot),
    ('FONTES_RELATIVAS', a_fontes_relativas),
    # Invariantes da coluna "Asserção do gerador" da §6.4 sem nome na §6.3 (as outras de lá estão na MMSI9 e na SEM_INDICATIVO).
    ('TERCEIROS', a_terceiros), ('SEM_PREVISAO', a_sem_previsao),
    # §1.2 (o C4 da §6.2: "asserções do registro e de lotacao ≥ pessoasBordo"), sem nome na §6.3.
    ('EMBARCACAO', a_embarcacao),
]
NOMES = [n for n, _ in ASSERCOES]


# ——————————————————————————————— listas privadas e pasta do Avanti (opcionais; só contagens) ———————————————————————————————
def listas_privadas(env=None):
    """{arquivo: [termos em minúsculas]} de CAPITAO_LISTAS_PRIVADAS, ou None sem a variável."""
    pasta = (env if env is not None else os.environ).get('CAPITAO_LISTAS_PRIVADAS')
    if not pasta:
        return None
    out = {}
    for nome in ('valores.txt', 'modelos-avanti.txt'):
        caminho = os.path.join(pasta, nome)
        if not os.path.isfile(caminho):
            raise SystemExit('CAPITAO_LISTAS_PRIVADAS: falta %s na pasta indicada' % nome)
        with open(caminho, encoding='utf-8') as f:
            out[nome] = [l.strip().lower() for l in f if l.strip()]
    return out


def texto_avanti(env=None):
    """Texto (minúsculas) dos arquivos de texto da pasta do Avanti de CAPITAO_AVANTI, fora CLAUDE.md, .claude/ e .git/. Só leitura."""
    pasta = (env if env is not None else os.environ).get('CAPITAO_AVANTI')
    if not pasta:
        return None
    if not os.path.isdir(pasta):
        raise SystemExit('CAPITAO_AVANTI: a pasta indicada não existe')
    partes = []
    for raiz, dirs, arqs in os.walk(pasta):
        dirs[:] = sorted(d for d in dirs if d not in ('.claude', '.git'))
        for a in sorted(arqs):
            if a == 'CLAUDE.md':
                continue
            try:
                with open(os.path.join(raiz, a), 'rb') as f:
                    b = f.read()
            except OSError:
                continue
            if b'\0' in b[:8192]:
                continue   # binário
            partes.append(b.decode('utf-8', 'ignore').lower())
    return '\n'.join(partes)


# ——————————————————————————————— execução ———————————————————————————————
def verifica(D, base, fontes, saidas, faq=None, rodape=None, listas=None, avanti=None, const=None):
    """{nome da asserção: [violações]} — todas as asserções, sem reprovar nada."""
    X = Ctx(D, base, fontes, saidas, faq, rodape, listas, avanti, const)
    return {nome: f(X) for nome, f in ASSERCOES}


class ConfereFalhou(Exception):
    pass


def le_rodape():
    if not os.path.isfile(RODAPE):
        return None
    with open(RODAPE, encoding='utf-8') as f:
        return f.read()


def resumo_termos(msgs):
    por = {}
    for m in msgs:
        k = m.split(':', 1)[0]
        por[k] = por.get(k, 0) + 1
    return ' · '.join('%s %d' % (k, v) for k, v in sorted(por.items()))


def padrao(p):
    """Padrão da PENDENTES → regex do texto inteiro da violação ('*' = qualquer trecho)."""
    return re.compile('.*'.join(re.escape(x) for x in p.split('*')), re.S)


def separa(V, inativas=()):
    """Separa as violações das asserções estruturais (fora da RELATORIO) pela PENDENTES. Cada padrão casa UMA violação.
    Devolve (novas, conhecidas, velhas): novas = {asserção: [violações fora das pendências]}, que reprovam; conhecidas =
    {asserção: {commit: n}}; velhas = [(asserção, commit, padrão)] que não casaram nada, que também reprovam (a lista não pode
    esconder a volta do defeito). As asserções de `inativas` (fonte opcional ausente) não têm pendência velha."""
    novas, conhecidas, velhas = {}, {}, []
    for nome, msgs in V.items():
        if nome in RELATORIO:
            continue
        livres = list(msgs)
        for commit, ps in (PENDENTES.get(nome) or {}).items():
            for p in ps:
                rx = padrao(p)
                k = next((j for j, m in enumerate(livres) if rx.fullmatch(m)), None)
                if k is None:
                    if nome not in inativas:
                        velhas.append((nome, commit, p))
                    continue
                livres.pop(k)
                c = conhecidas.setdefault(nome, {})
                c[commit] = c.get(commit, 0) + 1
        if livres:
            novas[nome] = livres
    return novas, conhecidas, velhas


def pendente_de(nome, m):
    """O commit da PENDENTES cujo padrão casa a violação m (para o --detalhe), ou None."""
    return next((c for c, ps in (PENDENTES.get(nome) or {}).items() for p in ps if padrao(p).fullmatch(m)), None)


def confere(D, base, fontes, saidas, faq=None, const=None, detalhe=False, imprime=print, env=None):
    """Roda verifica() com o rodapé e as fontes opcionais do ambiente, imprime o resumo e levanta ConfereFalhou se uma
    asserção estrutural tiver violação fora da PENDENTES ou se uma pendência não ocorrer mais. A RELATORIO só relata."""
    listas, avanti = listas_privadas(env), texto_avanti(env)
    V = verifica(D, base, fontes, saidas, faq, le_rodape(), listas, avanti, const)
    inativas = {n for n, f in OPCIONAIS.items() if {'listas': listas, 'avanti': avanti}[f] is None}
    novas, conhecidas, velhas = separa(V, inativas)
    falhas = sorted(set(novas) | {n for n, _, _ in velhas}, key=NOMES.index)
    imprime('confere(): %d asserções · %d reprovam o gerador: %s' % (
        len(V), len(V) - len(RELATORIO), ('%d com falha (%s)' % (len(falhas), ', '.join(falhas))) if falhas else '0 falhas'))
    imprime('  pendências conhecidas, por caminho (cada uma até o commit que completa o dado): ' + (' · '.join(
        '%s %d (%s)' % (n, sum(c.values()), ' · '.join('%s %d' % kv for kv in sorted(c.items()))) for n, c in conhecidas.items()) or 'nenhuma'))
    partes = []
    for n, v in V.items():
        if n in RELATORIO:
            extra = ': ' + resumo_termos(v) if n == 'TERMOS' and v else ''
            partes.append('%s %d (até o %s%s)' % (n, len(v), RELATORIO[n], extra))
    imprime('  em relatório: ' + ' · '.join(partes))
    imprime('  listas privadas: %s · pasta do Avanti: %s' % (
        'sem CAPITAO_LISTAS_PRIVADAS (não conferido)' if listas is None else
        ' · '.join('%s %d termos' % (k, len(t)) for k, t in sorted(listas.items())) + ' · MODELOS_AVANTI %d violação(ões)' % len(V['MODELOS_AVANTI']),
        'sem CAPITAO_AVANTI (não conferido)' if avanti is None else 'COLISAO_MODELOS %d violação(ões)' % len(V['COLISAO_MODELOS'])))
    for n in falhas:
        if novas.get(n):
            imprime('  · %s: %d violação(ões) fora das pendências:' % (n, len(novas[n])))
            for m in novas[n]:
                imprime('      ' + m)
        for nn, c, p in velhas:
            if nn == n:
                imprime('  · %s: pendência do %s que não ocorre mais (tire a linha da PENDENTES): %s' % (n, c, p))
    if detalhe:
        for n, v in V.items():
            if v:
                imprime('  · %s (todas):' % n)
                for m in v:
                    c = 'relatório' if n in RELATORIO else pendente_de(n, m)
                    imprime('      ' + m + ('  [%s]' % c if c else '  [NOVA]'))
    if falhas:
        motivo = []
        for n in falhas:
            nv, vl = len(novas.get(n) or []), sum(1 for nn, _, _ in velhas if nn == n)
            motivo.append(n + ' ' + ' + '.join(x for x in ('%d nova(s)' % nv if nv else '', '%d pendência(s) velha(s)' % vl if vl else '') if x))
        raise ConfereFalhou('confere(): ' + ', '.join(motivo))
    return V
