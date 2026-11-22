# -*- coding: utf-8 -*-
"""Capitão IA — gerador dos dados da embarcação.

Um lugar só para os dados da embarcação. Gera:
  1. capitao-dados.js          (raiz)  → window.CapitaoDados, lido pelo cérebro e pelas telas
  2. base-conhecimento.json    (raiz)  → trechos dos guias de bordo, busca BM25 do chat e da voz
  3. faq-equipamentos.json     (raiz)  → FAQ dos equipamentos (F10): um item por seção dos guias e cartões de emergência (CONTRATO §1.6)
  4. ferramentas/demo/fontes/          → os mesmos dados como arquivos de origem (Docs/Planilhas/JSON) enviados ao
                                         Google Drive › "Capitão IA v2" (pastas 01–07)

REGRAS (Decisão do proprietário 1.1.0 · modo simulação; ver o CLAUDE.md)
- SIMULACAO = True: dados completos da embarcação de apresentação, sem selo nem rótulo (DEMO, SEM DADOS, SEM LEITURA,
  MANUAL NO DRIVE, A CONFERIR/A CONFIRMAR). O rodapé gerado faz o rebase dos prazos e o capitao-replay.js lê D.replay.
  Nenhum texto gerado afirma nem nega que os dados são reais (a frase da sobreDados fica no cérebro).
- SIMULACAO = False (próxima embarcação): só dado com fonte; None = SEM DADOS. O gerador recusa replay além de limites
  e alertas, rota, histórico simulado e dia de bordo e, enquanto o repositório for público, a posição do barco.
- Nunca gerados: indicativo, HEX ID, telefone, lugar de equipamento de salvatagem.
- Nada copiado da Avanti Vessel (nomes, modelos, registro, MMSI, IDs, leituras, valores, textos).
- Sem valores em dinheiro, CPF/CNPJ, telefones, e-mails ou nomes de terceiros — nem na simulação (a mesma regra
  vale para o barco real que vier depois).
- Procedimentos de emergência: "procedimento padrão — confirmar com o protocolo de bordo" (decisão do proprietário).

Para a próxima embarcação: SIMULACAO = False, trocar os dados abaixo pelos reais (com a fonte de cada um) e rodar
    python ferramentas/demo/gerar_demo.py

Uso: python -X utf8 ferramentas/demo/gerar_demo.py [--saida <pasta>] [--detalhe]
  --saida    pasta onde gravar (padrão: a raiz do repositório); o teste usa uma pasta temporária e compara byte a byte.
  --detalhe  lista cada violação das asserções, com o commit da pendência ou [NOVA].
Antes de gravar, confere() (ferramentas/demo/confere.py, CONTRATO-DADOS §6.3) roda as asserções: uma com violação fora das
pendências congeladas (PENDENTES), ou com uma pendência que não ocorre mais, reprova o gerador e nada é gravado. Desde o C12 isso vale
também para a varredura de termos (as 8 regex do termos.json, sem exceção de campo desde a 1b). Opcionais, só com contagens: CAPITAO_LISTAS_PRIVADAS (pasta com valores.txt e
modelos-avanti.txt) e CAPITAO_AVANTI (pasta do Avanti, só leitura). Determinístico: nenhuma data ou hora do sistema.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
import unicodedata
from datetime import date, timedelta

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)   # vale também com python -I
from confere import (ConfereFalhou, arred, blocos_sensores, confere, deriva_janelas, desvio_em, mn_entre, quadro_laco, rumo_entre, textos,  # noqa: E402
                     ruido, segura, sensor_xy)   # segura: a SEGURANCA_PALAVRAS do §1.5, uma fonte só; blocos_sensores e sensor_xy: a regra do §1.19, uma só

RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
FONTES_REL = os.path.join('ferramentas', 'demo', 'fontes')   # as fontes do Drive, dentro da pasta de saída

REF = date(2026, 9, 26)          # data do snapshot: prazos D-n contados a partir dela
DRIVE = 'Drive › Capitão IA v2'
SIMULACAO = True                 # Decisão 1.1.0: embarcação de apresentação com navegação simulada (False = dados reais)
# Sem selo nem aviso (decisão b): nenhum campo de selo no D, e títulos, fontes, base e LEIA-ME sem rótulo.

PASTAS = {
    'manuais': '01 Manuais e guias de bordo',
    'docs': '02 Documentos',
    'agenda': '03 Agenda de manutenção',
    'diario': '04 Diário de bordo',
    'tele': '05 Telemetria — coletor NMEA',
    'abast': '06 Abastecimento',
    'protocolos': '07 Protocolos de emergência',
}
ARQ = {
    'leiame': 'LEIA-ME — Capitão IA v2',
    # Os 16 guias de bordo (CONTRATO §1.5): "Guia de bordo — <Equipamento> <Fabricante>"; os de segurança sem fabricante.
    'g_motores': 'Guia de bordo — Motores Cummins',
    'g_gerador': 'Guia de bordo — Gerador Onan',
    'g_seakeeper': 'Guia de bordo — Estabilizador Seakeeper',
    'g_clima': 'Guia de bordo — Climatização Webasto',
    'g_eletronicos': 'Guia de bordo — Eletrônicos Garmin, áudio Fusion e rádios Icom',
    'g_eletrico': 'Guia de bordo — Sistema elétrico 24 V e 12 V',
    'g_dessalinizador': 'Guia de bordo — Dessalinizador Schenker',
    'g_porao': 'Guia de bordo — Bombas de porão Rule',
    'g_ancora': 'Guia de bordo — Guincho e corrente Lewmar',
    'g_piloto': 'Guia de bordo — Piloto automático Raymarine',
    'g_radar': 'Guia de bordo — Radar Garmin',
    'g_ais': 'Guia de bordo — AIS em-trak',
    'g_seafire': 'Guia de bordo — Sistema fixo de incêndio',
    'g_epirb': 'Guia de bordo — EPIRB',
    'checklist': 'Checklist de bordo',
    'inventario': 'Inventário de bordo',
    'documentos': 'Controle de documentos',
    'agenda': 'Agenda preditiva',
    'diario': 'Diário de bordo',
    'snapshot': 'Leitura do coletor NMEA — 26-09-2026 10h12.json',
    'serie': 'Série do coletor NMEA — 150 s.csv',
    'formato': 'Formato do quadro do coletor.csv',
    'abast': 'Registro de abastecimento',
    'protocolo': 'Protocolo de emergência — procedimento padrão',
}
ARQ['g_vhf'] = ARQ['g_eletronicos']  # VHF é o mesmo guia/arquivo de origem do g_eletronicos; só muda o agrupamento dentro do app (FAQ_GUIAS)


def onde(chave_pasta, chave_arq):
    return DRIVE + ' › ' + PASTAS[chave_pasta] + ' › ' + ARQ[chave_arq]


def fonte_da_secao(guia, secao):
    """«Guia de bordo — Motores Cummins §5 · Temperatura alta» (seção numerada) ou «Checklist de bordo § Abastecimento» (sem número)."""
    return ARQ[guia] + (' §' + secao if secao[:1].isdigit() else ' § ' + secao)


def coord(v, pos, neg, g):
    a = abs(v)
    gr = int(a)
    mi = (a - gr) * 60
    gtxt = ('%03d' % gr) if g == 3 else str(gr)
    return gtxt + '°' + ('%05.2f' % mi).replace('.', ',') + "'" + (neg if v < 0 else pos)


# ——————————————————————————————— EMBARCAÇÃO ———————————————————————————————
# Decisão (e), CONTRATO-DADOS §1.2 e §2.1–§2.4: marca do barco fictícia e sem colisão (Estaleiro Marévia), registro que não imita
# identificador real (AAA-00-0000: nem inscrição numérica, placa, HIN, MMSI, telefone, CPF/CNPJ ou HEX ID), dimensões de 40 pés.
# O registro nunca vai para S1/S2 (trava §2.1); a lotação e as pessoas a bordo nunca vão para salvatagem, SOS nem roteiro. O
# indicativo não existe como campo (§0.2): o texto de instrução é o protocolos.indicativo (C6).
MOTOR = {'qtd': 2, 'fabricante': 'Cummins', 'modelo': 'QSB6.7 305', 'transmissao': 'eixo'}   # §2.2 (o equipamentos[motores] lê daqui no C5)
TANQUES = {'diesel_l': 1600, 'diesel_n': 2, 'agua_l': 400, 'cinzas_l': 100, 'negras_l': 100}   # 2 × 800 L de diesel (§2.1)


def num_br(x, casas):
    return ('%.*f' % (casas, x)).replace('.', ',')


# Textos derivados de campos (rotulo, motorizacao e o texto dos tanques do snapshot): com um campo de origem None (SEM DADOS no
# modo real, §4.3 e §0.12), o derivado também é None — nunca "None" no texto nem TypeError na importação. Na simulação, o None
# reprova na EMBARCACAO e na NULO do confere().
def falta(*vals):
    return any(v is None for v in vals)


def rotulo_de(E):
    """§1.2: "<modelo> · <comprimento com 2 casas> m · <ano>"; None se faltar um dos três."""
    if falta(E.get('modelo'), E.get('comprimento'), E.get('ano')):
        return None
    return '%s · %s m · %d' % (E['modelo'], num_br(E['comprimento'], 2), E['ano'])


def motorizacao_de(M):
    """§1.2: "<qtd> × <fabricante> <modelo> · <transmissão>"; None se faltar um dos quatro."""
    if falta(*(M.get(k) for k in ('qtd', 'fabricante', 'modelo', 'transmissao'))):
        return None
    return '%d × %s %s · %s' % (M['qtd'], M['fabricante'], M['modelo'], M['transmissao'])


def tanques_de(T):
    """O texto "<n> × <litros de cada um> L" do diesel no snapshot; None sem o número de tanques ou o volume."""
    if falta(T.get('diesel_n'), T.get('diesel_l')) or not T['diesel_n']:
        return None
    return '%d × %d L' % (T['diesel_n'], T['diesel_l'] // T['diesel_n'])


EMBARCACAO = {
    'nome': 'Capitão IA',
    'fabricante': 'Estaleiro Marévia',
    'modelo': 'Marévia 40 HT',
    'rotulo': None,         # gerado dos campos (rotulo_de, abaixo)
    'motorizacao': None,    # gerado do MOTOR (motorizacao_de, abaixo)
    'ano': 2023,
    'registro': 'CIA-23-0417',   # = documentos[tie].numero (C7)
    # m · m · m (eixo e hélices) · t métricas carregado (9,3 t, leve cerca de 7,3 t). O Seakeeper 3 cobre "até cerca de 10,5 tons" (a página
    # do fabricante não diz qual tonelada): lida como tonelada curta, 10,5 t curtas = 21.000 lb = cerca de 9,5 t métricas, e 9,3 t cabe nas
    # duas leituras (revisão do fechamento do C5, CONTRATO §2.1 e §8.2, item 9; era 10,4 t, que só cabia na leitura métrica)
    'comprimento': 12.4, 'boca': 3.95, 'calado': 1.1, 'deslocamento': 9.3,
    'lotacao': 12, 'pessoasBordo': 4,
    'tanques': dict(TANQUES),
    'un': {'comprimento': 'm', 'boca': 'm', 'calado': 'm', 'deslocamento': 't', 'lotacao': 'pessoas', 'pessoasBordo': 'pessoas'},
    'proprietario': 'Lucas Araújo',
    'base': 'Balneário Camboriú (SC)',
    'fuso': 'America/Sao_Paulo',
    'mmsi': '710123456',
    'fonte': 'cadastro da embarcação no app (proprietário)',
}
EMBARCACAO['rotulo'] = rotulo_de(EMBARCACAO)
EMBARCACAO['motorizacao'] = motorizacao_de(MOTOR)

# Posição de referência para clima e maré: centro de Balneário Camboriú (fonte real, não inventada)
POSICAO_REF = {
    'lat': -26.99056, 'lon': -48.63472,
    'nome': 'Balneário Camboriú (centro)',
    'fonte': 'Open-Meteo Geocoding (GeoNames 3471039)',
}
# Pontos de mar para a maré (a grade de 8 km do modelo de mar trata a costa como terra; a API usa a célula de mar mais próxima)
MAR = [[-26.99056, -48.63472], [-26.995, -48.60], [-27.0, -48.55]]

# ——————————————————————————————— EQUIPAMENTOS ———————————————————————————————
# CONTRATO §1.4 e §2.5 (decisão e): os fabricantes informados pelo proprietário (menos o dos motores, §2.2), modelos reais e
# atuais do porte de 40 pés, nenhum das listas privadas e contagem 0 por substring na pasta do Avanti (COLISAO_MODELOS; exceção
# só do Seakeeper 3, com o ok do §8.2: cobre 10,5–12,5 m e até cerca de 10,5 tons, só 12 V DC; o barco tem 9,3 t métricas).
# - id = o sistema (vocabulário fechado de agenda, tarefas e alertas: estes ids mais casco e tanques).
# - palavras: fabricante, modelo, nome comum e erros prováveis do ditado; palavra que cabe dentro de outra vai com espaço.
# - nominal: só números públicos do fabricante (o do estabilizador é só a regra do guia, sem rotação nem minutos do fabricante).
# - EPIRB e Seafire: seguranca, com a nota NOTA_ETIQUETA no lugar de fabricante e modelo fora de Equipamentos, Leme e Documentos;
#   validade = o id do documento ou da tarefa que guarda o prazo (C7).
NOTA_ETIQUETA = 'modelo, validade e acionamento: veja a etiqueta do equipamento'   # EPIRB e Seafire (§1.3, §1.4; protocolos no C6)
FONTE_INVENTARIO = 'Inventário de bordo · ' + DRIVE + ' › ' + PASTAS['manuais']
# Revisão do C5: o Seakeeper 3 estabiliza a partir de cerca de 85 % da rotação de operação (7.185 de 8.450 rpm no manual de operação do
# fabricante, "spool-up time to stabilization"); a regra antiga de 60 % contradizia a folha pública. É a regra do guia (§2, §6 e §8) e o
# aviso da LIMITES, com "cerca de" no texto; a rotação e os minutos do fabricante continuam fora (contagem 0 de "85 %" no contexto do
# estabilizador na pasta do Avanti, conferida só por contagem).
SEAKEEPER_ESTABILIZA_PCT = 85
EQUIPAMENTOS = [
    {'id': 'motores', 'nome': 'Motores', 'fabricante': MOTOR['fabricante'], 'modelo': MOTOR['modelo'], 'qtd': MOTOR['qtd'], 'lados': 'BB e BE',
     'guia': 'g_motores', 'palavras': ['cummins', 'kamins', 'comins', 'qsb', 'motor', 'motores'],
     'nominal': {'potencia_cv': 305, 'rpm_max': 2600, 'rpm_cruzeiro': 2050, 'rpm_lenta': 700, 'transmissao': MOTOR['transmissao']}},
    {'id': 'gerador', 'nome': 'Gerador', 'fabricante': 'Onan', 'modelo': 'QD 9', 'qtd': 1, 'guia': 'g_gerador',
     'palavras': [' onan ', 'gerador', 'qd 9', 'qd nove'], 'nominal': {'kw': 9, 'hz': 60, 'rpm': 1800}},
    {'id': 'estabilizador', 'nome': 'Estabilizador giroscópico', 'fabricante': 'Seakeeper', 'modelo': 'Seakeeper 3', 'qtd': 1, 'guia': 'g_seakeeper',
     'palavras': ['seakeeper', 'sikiper', 'giroscopio', 'estabilizador'], 'nominal': {'pct_estabiliza': SEAKEEPER_ESTABILIZA_PCT}},
    {'id': 'climatizacao', 'nome': 'Climatização', 'fabricante': 'Webasto', 'modelo': 'FCF Platinum 16000 e 12000', 'qtd': 3, 'guia': 'g_clima',
     'palavras': ['webasto', 'vebasto', 'fcf', 'platinum', 'climatizacao', 'ar condicionado'], 'nominal': {'btu_h_total': 40000}},
    {'id': 'eletronicos', 'nome': 'Plotters', 'fabricante': 'Garmin', 'modelo': 'GPSMAP 1243xsv', 'qtd': 2, 'guia': 'g_eletronicos',
     'palavras': ['garmin', 'gpsmap', 'plotter', 'plotters', 'chartplotter']},
    {'id': 'audio', 'nome': 'Áudio', 'fabricante': 'Fusion', 'modelo': 'MS-UD755', 'qtd': 1, 'guia': 'g_eletronicos',
     'palavras': ['fusion', 'audio', ' som ', 'bluetooth'], 'nominal': {'zonas': 2}},
    {'id': 'vhf', 'nome': 'Rádios VHF', 'fabricante': 'Icom', 'modelo': 'IC-M510 e IC-M37', 'qtd': 2, 'guia': 'g_eletronicos',
     'palavras': ['vhf', 'radio vhf', 'icom', 'canal 16']},
    {'id': 'epirb', 'nome': 'EPIRB', 'fabricante': 'Ocean Signal', 'modelo': 'SafeSea E100G', 'qtd': 1, 'guia': 'g_epirb',
     'palavras': ['epirb', 'radiobaliza', 'baliza', 'ipirb'], 'validade': 'doc-epirb', 'seguranca': True, 'nota': NOTA_ETIQUETA},
    {'id': 'seafire', 'nome': 'Sistema fixo de supressão de incêndio', 'fabricante': 'Seafire', 'modelo': 'FD 300M', 'qtd': 1, 'guia': 'g_seafire',
     'palavras': ['seafire', 'sea fire', 'sistema de incendio', 'supressao'], 'validade': 'seafire-inspecao', 'seguranca': True, 'nota': NOTA_ETIQUETA},
    {'id': 'dessalinizador', 'nome': 'Dessalinizador', 'fabricante': 'Schenker', 'modelo': 'Zen 30', 'qtd': 1, 'guia': 'g_dessalinizador',
     'palavras': ['schenker', 'shenker', 'zen 30', 'dessalinizador', 'osmose'], 'nominal': {'lph': 30}},
    {'id': 'porao', 'nome': 'Bombas de porão', 'fabricante': 'Rule', 'modelo': 'Rule 2000 (24 V)', 'qtd': 2, 'lados': 'BB e BE', 'guia': 'g_porao',
     'palavras': [' rule ', 'bomba de porao', 'bombas de porao', 'porao']},
    {'id': 'ancora', 'nome': 'Guincho e contador de corrente', 'fabricante': 'Lewmar', 'modelo': 'V2 · contador AA150', 'qtd': 1, 'guia': 'g_ancora',
     'palavras': ['lewmar', 'leumar', 'guincho', 'ancora', 'contador de corrente', 'molinete'], 'nominal': {'corrente_m': 60}},
    {'id': 'piloto', 'nome': 'Piloto automático', 'fabricante': 'Raymarine', 'modelo': 'Evolution EV-1 · ACU-400', 'qtd': 1, 'guia': 'g_piloto',
     'palavras': ['raymarine', 'reimarine', 'evolution', 'piloto automatico', 'piloto']},
    {'id': 'radar', 'nome': 'Radar', 'fabricante': 'Garmin', 'modelo': 'GMR 24 xHD3', 'qtd': 1, 'guia': 'g_radar',
     'palavras': ['radar', 'gmr', 'xhd3', 'domo']},
    {'id': 'ais', 'nome': 'AIS (classe B)', 'fabricante': 'em-trak', 'modelo': 'B954', 'qtd': 1, 'guia': 'g_ais',
     'palavras': [' ais ', 'em-trak', 'emtrak', 'transponder']},
    # O 16º, que a B2 pede: 3 bancos; o de 12 V (as 2 em paralelo) alimenta a eletrônica de 12 V e o estabilizador (12 V DC, §2.5).
    {'id': 'eletrico', 'nome': 'Baterias (24 V e 12 V)', 'fabricante': 'Victron Energy', 'modelo': 'AGM Super Cycle 12 V 230 Ah', 'qtd': 8, 'guia': 'g_eletrico',
     'palavras': ['victron', 'vitron', 'bateria', 'baterias', 'banco de baterias', ' agm '],
     'nominal': {'bancos': [{'id': 'servico', 'v': 24, 'n': 4, 'campo': 'bateria_0_tensao_v'}, {'id': 'partida', 'v': 24, 'n': 2, 'campo': 'bateria_1_tensao_v'},
                            {'id': 'eletronica', 'v': 12, 'n': 2, 'campo': 'bateria_2_tensao_v'}]}},
]
for _e in EQUIPAMENTOS:
    _e['fonte'] = FONTE_INVENTARIO
# Fica até a Fase 4 reescrever F1–F5 (que mostram "Fonte: " + equipNota), com texto neutro (§1.4).
EQUIP_NOTA = 'Inventário de bordo · %d equipamentos · %s › %s' % (len(EQUIPAMENTOS), DRIVE, PASTAS['manuais'])

# ——————————————————————————————— SNAPSHOT DO COLETOR ———————————————————————————————
GPS = {'lat': -26.9930, 'lon': -48.6140}
SNAPSHOT = {
    'quando': '26/09/2026 10:12', 'hora': '10:12', 'dia': '26/09', 'iso': '2026-09-26T10:12:00-03:00',
    'fonte': 'coletor NMEA · leitura de 26/09/2026 10:12',
    'estado': 'Fundeado', 'local': 'enseada de Balneário Camboriú',
    'gps': {'lat': GPS['lat'], 'lon': GPS['lon'], 'texto': coord(GPS['lat'], 'N', 'S', 2) + ' ' + coord(GPS['lon'], 'E', 'W', 3), 'satelites': 26},
    'sog': 0.1, 'proa': 71, 'profundidade': 7.4,
    'vento': 9.2, 'ventoDe': 58, 'pressao': 1017, 'ar': 22.6, 'agua': 20.1,
    'bat24': 27.42, 'bat12': 13.18,
    'tanques': {'agua': 68.5, 'cinzas': 21.0, 'negras': 34.5},
    'diesel': {'bb': 54.0, 'be': 52.0, 'litros': 848, 'capacidade': TANQUES['diesel_l'],
               'tanques': tanques_de(TANQUES), 'hora': '26/09 09:31',
               'nota': 'última leitura com motores ligados'},
    'motores': {'hora': '26/09 09:31', 'estado': 'desligados desde 09:31', 'rpm': [700, 690], 'oleo': [3.4, 3.3],
                'arref': [79, 78], 'horimetro': [412.6, 409.8], 'marcha': 'neutro'},
    'gerador': {'estado': 'ligado desde 09:35', 'horas': 1236.4, 'kw': 5.6, 'hora': '26/09 10:12'},
    'seakeeper': {'estado': 'ligado', 'volante_rpm': 8420, 'volante_pct': 100, 'hora': '26/09 10:12'},
    'porao': {'bb_cm': 1.2, 'be_cm': 0.9, 'ciclos_h': 0},      # §1.17: sem null; os leitores de texto têm a guarda do objeto
    'ancora': {'estado': 'lançada', 'cabo_m': 30},             # o enum do quadro (ancora_estado), coerente com o fundeio
}
# O mesmo instante no formato plano do quadro (§1.17): é o que CapitaoAgora.instante() acha com fonte 'snapshot' (nunca em S1/S2). Motores
# parados (rpm 0, neutro, Fundeado); sem destino, ETA, próximo ponto, piloto nem alarmes (origem rota ou janela; ausência = sem alarme).
SNAPSHOT['quadro'] = {
    'timestamp_utc': '2026-09-26T13:12:00Z', 'lat': GPS['lat'], 'lon': GPS['lon'], 'cog_graus': 71, 'proa_graus': SNAPSHOT['proa'], 'leme_graus': 0,
    'sog_nos': SNAPSHOT['sog'], 'stw_nos': 0.3, 'profundidade_m': SNAPSHOT['profundidade'],
    'motor_bb_rpm': 0, 'motor_be_rpm': 0, 'motor_bb_oleo_bar': 0, 'motor_be_oleo_bar': 0, 'motor_bb_arref_c': 54, 'motor_be_arref_c': 53,
    'motor_bb_carga_pct': 0, 'motor_be_carga_pct': 0, 'marcha': 'neutro', 'consumo_lph': 0,
    'diesel_litros': SNAPSHOT['diesel']['litros'], 'diesel_bb_pct': SNAPSHOT['diesel']['bb'], 'diesel_be_pct': SNAPSHOT['diesel']['be'],
    'distancia_mn': 11.6, 'motor_bb_horimetro_h': SNAPSHOT['motores']['horimetro'][0], 'motor_be_horimetro_h': SNAPSHOT['motores']['horimetro'][1],
    'gerador_ativo': True, 'gerador_kw': SNAPSHOT['gerador']['kw'], 'gerador_horimetro_h': SNAPSHOT['gerador']['horas'],
    'seakeeper_ativo': True, 'seakeeper_volante_rpm': SNAPSHOT['seakeeper']['volante_rpm'], 'seakeeper_volante_pct': SNAPSHOT['seakeeper']['volante_pct'],
    'bateria_0_tensao_v': SNAPSHOT['bat24'], 'bateria_1_tensao_v': 27.2, 'bateria_2_tensao_v': SNAPSHOT['bat12'],
    'tanque_agua_pct': SNAPSHOT['tanques']['agua'], 'tanque_cinzas_pct': SNAPSHOT['tanques']['cinzas'], 'tanque_negras_pct': SNAPSHOT['tanques']['negras'],
    'porao_bb_nivel': SNAPSHOT['porao']['bb_cm'], 'porao_be_nivel': SNAPSHOT['porao']['be_cm'], 'bomba_porao_ciclos': SNAPSHOT['porao']['ciclos_h'],
    'ancora_estado': SNAPSHOT['ancora']['estado'], 'ondas_m': 0.5,
    'vento_verdadeiro_nos': SNAPSHOT['vento'], 'vento_verdadeiro_angulo': SNAPSHOT['ventoDe'], 'vento_aparente_nos': SNAPSHOT['vento'], 'vento_aparente_angulo': -13,
    'pressao_barometrica_hpa': SNAPSHOT['pressao'], 'temp_ar_externo_c': SNAPSHOT['ar'], 'temp_agua_c': SNAPSHOT['agua'], 'temp_praca_maquinas_c': 38,
    'jogo_graus': 0.6, 'caimento_graus': 0.4, 'gps_satelites': SNAPSHOT['gps']['satelites'], 'climatizacao_ativa': True,
    'dessalinizador_ativo': False, 'radar_ativo': False, 'ais_alvos': 3, 'estado': SNAPSHOT['estado'], 'local': 'na ' + SNAPSHOT['local'],
}
# §1.12: o consumo dos dois motores por regime e o do gerador (que gira 24 h); a fonte é o guia §10, o mesmo texto de texto_consumo_motores().
# `periodo` e `desdeAbast` são (L): a forma e os valores de hoje, até a Fase 3 (o cérebro de hoje os lê).
CONSUMO = {
    'cruzeiro': {'nos': 18, 'rpm': 2050, 'lph': 68}, 'lenta': {'nos': 5, 'rpm': 700, 'lph': 6.2}, 'maxima': {'nos': 26, 'rpm': 2600, 'lph': 111},
    'gerador_lph': 2.3,
    'faixas': [{'rpm_de': 600, 'rpm_ate': 1000, 'nome': 'marcha lenta'}, {'rpm_de': 1000, 'rpm_ate': 1500, 'nome': 'deslocamento'},
               {'rpm_de': 1500, 'rpm_ate': 1800, 'nome': 'transição'}, {'rpm_de': 1800, 'rpm_ate': 2000, 'nome': 'planeio'},
               {'rpm_de': 2000, 'rpm_ate': 2600, 'nome': 'cruzeiro'}],
    'fonte': 'Guia de bordo — Motores Cummins §10 · Consumo', 'margemManobra_l': 60,
    'periodo': '01/08–26/09/2026',
    'desdeAbast': {'litros': 192, 'desde': '12/09/2026', 'horas': '2,8 h de motor por lado'},
}
RESERVA = 0.10


def autonomia():
    litros = SNAPSHOT['diesel']['litros']
    h = litros * (1 - RESERVA) / CONSUMO['cruzeiro']['lph']
    return {'horas': round(h, 1), 'mn': int(round(h * CONSUMO['cruzeiro']['nos'])),
            'lenta': int(round(litros * (1 - RESERVA) / CONSUMO['lenta']['lph']))}


# ——————————————————————————————— PRAZOS RELATIVOS (CONTRATO §1.0, §1.7–§1.9, §4.1) ———————————————————————————————
# O gerador emite deslocamentos (venceEm, ultimaHa, emitidoHa, diasAtras) e grava como reserva os derivados contados da REF
# (26/09/2026; hoje = dia de bordo = REF). O rodapé do capitao-dados.js (rodape.js) refaz esses derivados com a data do aparelho,
# no fuso America/Sao_Paulo; se ele falhar, as telas mostram as datas da REF. Os derivados de reserva e os do rodapé são o mesmo
# cálculo (o teste de paridade congela o relógio na REF e compara). Os deslocamentos são positivos para o passado (ultimaHa,
# emitidoHa, diasAtras) e com sinal para o futuro (venceEm negativo = atrasado).
FUSO_REF = '-03:00'   # Brasília não tem horário de verão desde 2019; o rodapé lê o fuso do aparelho


def dia_br(dias):
    """'dd/mm/aaaa' de REF + dias (negativo = passado)."""
    return (REF + timedelta(days=dias)).strftime('%d/%m/%Y')


def dia_ddmm(dias):
    return (REF + timedelta(days=dias)).strftime('%d/%m')


def dia_iso(dias):
    return (REF + timedelta(days=dias)).isoformat()


def iso_local(dias_atras, h, seg=0):
    """'AAAA-MM-DDTHH:MM:SS-03:00' da hora de parede h do dia REF − dias_atras."""
    return '%sT%s:%02d%s' % (dia_iso(-dias_atras), h, seg, FUSO_REF)


def status_doc(n):
    return 'VENCIDO' if n < 0 else ('VENCE EM %d D' % n if n <= 90 else 'EM DIA')


def segundos_do_diario(linhas, base):
    """Linhas do mesmo dia e da mesma hora na mesma base: a de cima (mais nova) ganha 1 s a mais, para o iso seguir a ordem do
    array (d01 = âncora + 1 s, d02 = âncora; CONTRATO §1.9). Igual ao porSegundos() do rodape.js."""
    chave = [(base(x), x['diasAtras'], x['h']) for x in linhas]
    return [chave.count(k) - chave[:i + 1].count(k) for i, k in enumerate(chave)]


# Série 24 V · 7 dias: mín/máx por dia do banco de serviço (L até a Fase 4). `diasAtras` conta do dia de bordo; o rebase escreve o `d` (dd/mm).
# Só os dias ficam aqui: o mín/máx de cada um é o da volta de 150 s do laço + o desvio do dia do histórico (serie24v_dados, §1.13).
SERIE_24V = [{'diasAtras': k} for k in range(6, -1, -1)]

# ——————————————————————————————— AGENDA PREDITIVA ———————————————————————————————
# CONTRATO §1.7: 14 tarefas (os ids de hoje ficam: as telas e o capitao.executado.v1 usam o id; entram epirb-teste, motores-rotor e
# seafire-inspecao). `sistema` ∈ ids de equipamentos ∪ {casco, tanques}; `quem` = papel, nunca nome de terceiro; `palavras` = frases
# normalizadas (como o norm() do cérebro) que ligam um texto à tarefa, cada uma com 2+ palavras. Nenhum `t` tem palavra da lista SOS
# (o Seafire é "sistema fixo de supressão" no `t`). `ultimaHa + venceEm` = DIAS_MESES[meses]. 3 atrasadas, nenhuma de salvatagem.
# Folga das horas: 37,4 h (óleo) e 63,6 h (gerador) na âncora; 13,4 h e 39,6 h às 06:59:59 (asserção HORAS).
DIAS_MESES = {1: 31, 6: 184, 12: 365}   # intervalo da agenda em dias (§1.7)
AGENDA = [
    {'id': 'porao-teste', 't': 'Teste das bombas de porão e alarmes', 'curto': 'TESTE', 'equip': 'Bombas de porão Rule 2000', 'sistema': 'porao',
     'quem': 'técnico', 'intervalo': 'mensal', 'meses': 1, 'ultimaHa': 56, 'venceEm': -25, 'seguranca': True,
     'palavras': ['bombas de porao', 'bomba de porao', 'teste das bombas']},
    {'id': 'clima-filtro', 't': 'Limpeza do filtro de água salgada da climatização', 'curto': 'FILTRO', 'equip': 'Climatização Webasto FCF Platinum',
     'sistema': 'climatizacao', 'quem': 'marina', 'intervalo': 'mensal', 'meses': 1, 'ultimaHa': 47, 'venceEm': -16,
     'palavras': ['filtro de agua salgada', 'filtro da climatizacao', 'filtro do ar condicionado', 'filtro do ar-condicionado']},
    {'id': 'gerador-rotor', 't': 'Inspeção do rotor (impeller) do gerador', 'curto': 'ROTOR', 'equip': 'Gerador Onan QD 9', 'sistema': 'gerador',
     'quem': 'técnico', 'intervalo': '12 meses', 'meses': 12, 'ultimaHa': 367, 'venceEm': -2,
     'palavras': ['rotor do gerador', 'impeller do gerador', 'rotor impeller do gerador']},
    {'id': 'casco-anodos', 't': 'Limpeza de casco e troca de anodos', 'curto': 'ANODOS', 'equip': 'Casco', 'sistema': 'casco', 'quem': 'marina',
     'intervalo': '6 meses', 'meses': 6, 'ultimaHa': 175, 'venceEm': 9,
     'palavras': ['limpeza de casco', 'limpeza do casco', 'anodos do casco', 'troca de anodos']},
    {'id': 'epirb-teste', 't': 'Autoteste do EPIRB e validade conferida na etiqueta', 'curto': 'AUTOTESTE', 'equip': 'EPIRB', 'sistema': 'epirb',
     'quem': 'Lucas', 'intervalo': 'mensal', 'meses': 1, 'ultimaHa': 18, 'venceEm': 13, 'seguranca': True,
     'palavras': ['autoteste do epirb', 'teste do epirb', 'teste da baliza', 'autoteste da baliza']},
    {'id': 'motores-oleo', 't': 'Troca de óleo e filtros dos motores', 'curto': 'ÓLEO', 'equip': 'Motores Cummins QSB6.7 305', 'sistema': 'motores',
     'quem': 'oficina de motores', 'intervalo': '12 meses ou 450 h (o que vier antes)', 'meses': 12, 'ultimaHa': 348, 'venceEm': 17,
     'horas': {'limite': 450, 'campos': ['motor_bb_horimetro_h', 'motor_be_horimetro_h'], 'atual': 412.6},   # vale o maior dos dois
     'palavras': ['oleo dos motores', 'oleo do motor', 'filtros dos motores']},
    {'id': 'gerador-revisao', 't': 'Revisão do gerador: óleo e filtros', 'curto': 'REVISÃO', 'equip': 'Gerador Onan QD 9', 'sistema': 'gerador',
     'quem': 'técnico', 'intervalo': '12 meses ou 1.300 h', 'meses': 12, 'ultimaHa': 341, 'venceEm': 24,
     'horas': {'limite': 1300, 'campos': ['gerador_horimetro_h'], 'atual': 1236.4},
     'palavras': ['revisao do gerador', 'oleo do gerador', 'filtros do gerador']},
    {'id': 'seakeeper-anodo', 't': 'Anodo do trocador de calor do estabilizador', 'curto': 'ANODO', 'equip': 'Estabilizador Seakeeper 3',
     'sistema': 'estabilizador', 'quem': 'técnico', 'intervalo': '6 meses', 'meses': 6, 'ultimaHa': 149, 'venceEm': 35,
     'palavras': ['anodo do estabilizador', 'anodo do seakeeper', 'anodo do trocador']},
    {'id': 'motores-rotor', 't': 'Troca do rotor da bomba de água salgada dos motores', 'curto': 'ROTOR', 'equip': 'Motores Cummins QSB6.7 305',
     'sistema': 'motores', 'quem': 'oficina de motores', 'intervalo': '12 meses', 'meses': 12, 'ultimaHa': 324, 'venceEm': 41,
     'palavras': ['rotor da bomba de agua salgada', 'rotor dos motores', 'impeller dos motores', 'rotor do motor']},
    {'id': 'baterias', 't': 'Verificação do banco de baterias e conexões', 'curto': 'VERIFICAÇÃO', 'equip': 'Baterias Victron Energy (24 V e 12 V)',
     'sistema': 'eletrico', 'quem': 'técnico', 'intervalo': '6 meses', 'meses': 6, 'ultimaHa': 134, 'venceEm': 50,
     'palavras': ['banco de baterias', 'conexoes das baterias', 'verificacao das baterias']},
    {'id': 'garmin-cartas', 't': 'Atualização de cartas e software dos eletrônicos', 'curto': 'CARTAS', 'equip': 'Plotters Garmin GPSMAP 1243xsv',
     'sistema': 'eletronicos', 'quem': 'Lucas', 'intervalo': '12 meses', 'meses': 12, 'ultimaHa': 299, 'venceEm': 66,
     'palavras': ['cartas do plotter', 'cartas nauticas', 'atualizacao das cartas', 'software dos eletronicos']},
    {'id': 'clima-revisao', 't': 'Revisão anual da climatização', 'curto': 'REVISÃO', 'equip': 'Climatização Webasto FCF Platinum',
     'sistema': 'climatizacao', 'quem': 'marina', 'intervalo': '12 meses', 'meses': 12, 'ultimaHa': 279, 'venceEm': 86,
     'palavras': ['revisao da climatizacao', 'revisao do ar condicionado']},
    {'id': 'motores-revisao', 't': 'Revisão anual dos motores', 'curto': 'REVISÃO', 'equip': 'Motores Cummins QSB6.7 305', 'sistema': 'motores',
     'quem': 'oficina de motores', 'intervalo': '12 meses', 'meses': 12, 'ultimaHa': 253, 'venceEm': 112,
     'palavras': ['revisao dos motores', 'revisao anual dos motores']},
    {'id': 'seafire-inspecao', 't': 'Inspeção anual do sistema fixo de supressão', 'curto': 'INSPEÇÃO', 'equip': 'Sistema fixo de supressão de incêndio',
     'sistema': 'seafire', 'quem': 'técnico', 'intervalo': '12 meses', 'meses': 12, 'ultimaHa': 225, 'venceEm': 140, 'seguranca': True,
     'palavras': ['inspecao do sistema fixo', 'sistema fixo de supressao', 'inspecao do seafire']},
]
# F15 (CONTRATO §1.7): tarefas da equipe geradas; o rebase escreve vence ('AAAA-MM-DD', a forma do capitao.tarefas.v1), dn, st, rot, tom.
TAREFAS_EQUIPE = [
    {'id': 'g01', 'n': 'Revisar mangueiras do dessalinizador', 'venceEm': 20, 'quem': 'técnico', 'meses': 6, 'sistema': 'dessalinizador', 'origem': 'equipe'},
    {'id': 'g02', 'n': 'Lavar o convés e o hard-top', 'venceEm': 5, 'quem': 'marina', 'meses': 1, 'sistema': 'casco', 'origem': 'equipe'},
]


def status_prazo(n):
    if n < 0:
        return {'st': 'ATRASADA', 'rot': 'ATRASADA · ' + str(-n) + ' D', 'tom': 'crit'}
    if n <= 30:
        return {'st': 'D-30', 'rot': 'D-' + str(n), 'tom': 'warn'}
    if n <= 60:
        return {'st': 'D-60', 'rot': 'D-' + str(n), 'tom': 'tele'}
    if n <= 90:
        return {'st': 'D-90', 'rot': 'D-' + str(n), 'tom': 'accent'}
    return {'st': 'EM DIA', 'rot': 'D-' + str(n), 'tom': 'ok'}


# ——————————————————————————————— DOCUMENTOS ———————————————————————————————
# CONTRATO §1.8. Sem valores, sem apólice, licença nem emissor: só o TIE tem número (= embarcacao.registro). A nota fiscal do
# abastecimento das 07:00 fica em replay.diaDeBordo.documento (C8) e a microtarefa do rodapé a insere por id, só na simulação: sem
# prazo, o `st` CONFERIDA é dela e o rebase omite vence, dn e o st de prazo; `emitido` na base dia de bordo.
DOCUMENTOS = [
    {'id': 'tie', 'n': 'Título de Inscrição da Embarcação (TIE)', 'cat': 'Registro', 'venceEm': 646, 'emitidoHa': 1180, 'numero': EMBARCACAO['registro'],
     'nota': 'renovação a cada 5 anos'},
    {'id': 'seguro', 'n': 'Seguro da embarcação', 'cat': 'Seguro', 'venceEm': 19, 'emitidoHa': 346, 'nota': 'apólice guardada a bordo e no Drive'},
    {'id': 'licenca', 'n': 'Licença de Estação de rádio (VHF)', 'cat': 'Licenças', 'venceEm': 65, 'nota': 'rádios VHF fixo e portátil'},
    {'id': 'laudo', 'n': 'Laudo de vistoria anual', 'cat': 'Laudos', 'venceEm': 326, 'emitidoHa': 39, 'nota': 'laudo arquivado no Drive'},
    {'id': 'gar-estab', 'n': 'Garantia do estabilizador', 'cat': 'Garantias', 'venceEm': 175, 'nota': 'Seakeeper 3'},
    {'id': 'gar-eletr', 'n': 'Garantia dos eletrônicos', 'cat': 'Garantias', 'venceEm': 137, 'nota': 'plotters e radar Garmin'},
    {'id': 'doc-epirb', 'n': 'Certificado do EPIRB (bateria e disparador hidrostático)', 'cat': 'Segurança', 'venceEm': 540,
     'nota': 'validade conferida também na etiqueta do equipamento'},
]

# ——————————————————————————————— ABASTECIMENTOS ———————————————————————————————
# CONTRATO §1.10: o arquivo gerado leva `abastecimentos: []` (a única lista vazia permitida): as 3 linhas do dia de bordo (ab-0…ab-2, às 07:00,
# no salto do contador) vêm de replay.diaDeBordo pela microtarefa do rodapé, só com simulacao: true. As duas linhas antigas (620 L e
# 540 L) saíram: contavam outra rotina que a dos contadores.

# ——————————————————————————————— DIÁRIO DE BORDO ———————————————————————————————
# CONTRATO §1.9: o diário fixo (d03–d09, na base hoje); o rebase escreve `d` e `iso`. Nada descreve emergência (asserção SEM_EMERGENCIA).
# Pendências abertas: d03, d05, d07; cada uma leva `palavras` = as da tarefa do `ref` (uma fonte só; é por elas que um registro novo
# cita a pendência). `diasAtras 0 ⇒ h ≤ 07:00`. d01 (a saída) e d02 (o abastecimento das 07:00) são do dia de bordo: ficam em
# replay.diaDeBordo.diario (C8) e a microtarefa do rodapé as põe no topo, só na simulação.
DIARIO = [
    {'id': 'd03', 'diasAtras': 2, 'h': '17:10', 'sys': 'Manutenção', 'tom': 'warn', 'who': 'técnico', 'pend': True, 'ref': 'gerador-rotor',
     't': 'Inspeção do rotor do gerador não feita no prazo — reagendar; rotor de reserva em falta no estoque.'},
    {'id': 'd04', 'diasAtras': 3, 'h': '19:30', 'sys': 'Motores', 'tom': 'accent', 'who': 'Lucas', 'pend': False, 'ref': 'motores-rotor',
     't': 'Motor BE 1 a 2 °C acima do BB em cruzeiro nos últimos dias, com picos acima de 88 °C — acompanhar; rotor da bomba de água salgada dos motores na agenda.'},
    {'id': 'd05', 'diasAtras': 6, 'h': '11:05', 'sys': 'Equipamentos', 'tom': 'accent', 'who': 'Lucas', 'pend': True, 'ref': 'clima-filtro',
     't': 'Climatização da cabine de proa com fluxo fraco. Suspeita: filtro de água salgada sujo (limpeza atrasada).'},
    {'id': 'd06', 'diasAtras': 18, 'h': '08:30', 'sys': 'Segurança', 'tom': 'ok', 'who': 'Lucas', 'pend': False, 'ref': 'epirb-teste',
     't': 'Autoteste do EPIRB feito: luz de teste conforme a etiqueta.'},
    {'id': 'd07', 'diasAtras': 21, 'h': '10:00', 'sys': 'Segurança', 'tom': 'crit', 'who': 'técnico', 'pend': True, 'ref': 'porao-teste',
     't': 'Teste das bombas de porão adiado por chuva.'},
    {'id': 'd08', 'diasAtras': 29, 'h': '16:25', 'sys': 'Eletrônicos', 'tom': 'accent', 'who': 'Lucas', 'pend': False, 'ref': 'garmin-cartas',
     't': 'Cartas do plotter desatualizadas; a atualização está na agenda.'},
    {'id': 'd09', 'diasAtras': 39, 'h': '09:00', 'sys': 'Documentos', 'tom': 'ok', 'who': 'Lucas', 'pend': False, 'ref': 'laudo',
     't': 'Vistoria anual feita; laudo arquivado no Drive.'},
]
BORDO_DIARIO = ('d01', 'd02')   # linhas do diário contadas no dia de bordo (as outras, em hoje); a mesma lista do rodape.js (hoje só em diaDeBordo)

# ——————————————————————————————— EQUIPE E APOIO ———————————————————————————————
# CONTRATO §1.11: papéis em lista fechada, sem nome de pessoa ou empresa e sem telefone; nenhum papel diz "autorizada <marca>". `para` e
# `servico` têm o mesmo texto até a Fase 4. Os ids antigos (marina, oficina, tecnico, posto) ficam: os telefones do aparelho usam o id.
EQUIPE = {
    'perfis': [{'id': 'lucas', 'nome': 'Lucas Araújo', 'ini': 'LA', 'papel': 'proprietário', 'acesso': 'total'}],
    'apoio': [
        {'id': 'marina', 'papel': 'Marina da base', 'onde': 'Balneário Camboriú (SC)', 'para': 'casco, filtros, vaga', 'servico': 'casco, filtros, vaga'},
        {'id': 'oficina', 'papel': 'Oficina de motores diesel', 'onde': 'atende na marina da base', 'para': 'motores e gerador', 'servico': 'motores e gerador'},
        {'id': 'tecnico', 'papel': 'Técnico de bordo', 'onde': 'atende na marina da base', 'para': 'estabilizador, elétrica, porão', 'servico': 'estabilizador, elétrica, porão'},
        {'id': 'eletronica', 'papel': 'Técnico de eletrônicos', 'onde': 'atende na marina da base', 'para': 'plotters, rádios, piloto, radar, AIS', 'servico': 'plotters, rádios, piloto, radar, AIS'},
        {'id': 'refrigeracao', 'papel': 'Técnico de refrigeração', 'onde': 'atende na marina da base', 'para': 'climatização, dessalinizador', 'servico': 'climatização, dessalinizador'},
        {'id': 'posto', 'papel': 'Posto de combustível', 'onde': 'na marina da base', 'para': 'diesel', 'servico': 'diesel'},
    ],
    'nota': 'Telefones: ficam só no aparelho (Equipe).',
}


# Derivados de reserva (CONTRATO §1.0): o que o rodapé reescreve, contado da REF. Cada função devolve cópias, na ordem de chaves do contrato.
AGENDA_FONTE = ARQ['agenda'] + ' · ' + DRIVE + ' › ' + PASTAS['agenda']
DOCS_FONTE = ARQ['documentos'] + ' · ' + DRIVE + ' › ' + PASTAS['docs']


def agenda_dados():
    ag = []
    for t in AGENDA:
        n = t['venceEm']
        x = dict(t)
        if 'horas' in t:
            x['horas'] = dict(t['horas'], faltam=round(t['horas']['limite'] - t['horas']['atual'], 1))
        x['fonte'] = ARQ['agenda']   # o título em drive.arquivos (a asserção da C2); a fonte completa é a agendaFonte, que as telas leem
        x['ultima'] = dia_br(-t['ultimaHa'])
        x['vence'] = dia_br(n)
        x['dn'] = n
        x.update(status_prazo(n))
        ag.append(x)
    ag.sort(key=lambda t: (t['dn'], t['id']))   # como o rebase: por dn, depois por id
    return ag


def tarefas_equipe_dados():
    out = []
    for t in TAREFAS_EQUIPE:
        x = dict(t)
        x['vence'] = dia_iso(t['venceEm'])
        x['dn'] = t['venceEm']
        x.update(status_prazo(t['venceEm']))
        out.append(x)
    return out


def documentos_dados():
    docs = []
    for doc in DOCUMENTOS:
        x = dict(doc)
        x['fonte'] = ARQ['documentos']   # idem: o título; a fonte completa é a docsFonte
        if 'venceEm' in doc:   # sem prazo (a nota fiscal), vence, dn e o st de prazo ficam de fora (nunca null)
            n = doc['venceEm']
            x['vence'] = dia_br(n)
            x['dn'] = n
            x['st'] = status_doc(n)
        if 'emitidoHa' in doc:
            x['emitido'] = dia_br(-doc['emitidoHa'])
        docs.append(x)
    return docs


def diario_dados():
    seg = segundos_do_diario(DIARIO, lambda x: 'b' if x['id'] in BORDO_DIARIO else 'h')
    out = []
    for x, s in zip(DIARIO, seg):
        y = dict(x)
        pend_ref = next((t for t in AGENDA if t['id'] == x.get('ref')), None)
        if x['pend']:
            y['palavras'] = list(pend_ref['palavras'])   # uma fonte só (§1.9)
        y['d'] = dia_ddmm(-x['diasAtras'])
        y['iso'] = iso_local(x['diasAtras'], x['h'], s)
        out.append(y)
    return out


def abastecimentos_dados():
    return []   # §1.10: as linhas do dia de bordo entram pela microtarefa do rodapé (replay.diaDeBordo), nunca no arquivo gerado


def serie24v_dados():
    """serie24v (L, §1.13): 7 itens {diasAtras: 6…0, min, max, d} = mín/máx da volta do banco de serviço (bateria_0_tensao_v) + o desvio do
    dia (o do histórico, interpolado entre os pontos de 2 em 2 dias até 0 hoje). Só na simulação (dados() a chama lá): o mín/máx sai do laço e do
    histórico simulados, que o modo real não emite (§4.3); sem a série, o leitor cai no «série não gravada»."""
    R, _, campos = replay_dados()
    vs = [quadro_laco(R, campos, t)['bateria_0_tensao_v'] for t in range(R['duracao'])]
    H = historico_dados()
    out = []
    for x in SERIE_24V:
        dev = desvio_em(H, 'bateria_0_tensao_v', x['diasAtras'])
        out.append(dict(x, min=arred(min(vs) + dev, 2), max=arred(max(vs) + dev, 2), d=dia_ddmm(-x['diasAtras'])))
    return out


# ——————————————————————————————— FAIXAS E LIMITES (CONTRATO §3.3) ———————————————————————————————
# Uma constante só (LIMITES): os textos dos guias que citam faixa saem daqui, formatados em pt-BR, e cada limite aponta para o §n
# do guia de bordo gerado que tem os números (FONTE_LIMITES; trava §2.10: nunca manual de fabricante com página inventada). O
# D.replay.limites do C8 é esta mesma constante. São regra de bordo do Capitão, mais conservadora que os alarmes do próprio
# equipamento, e não coincidem com as do Avanti (conferido no contrato). Forma fechada, uma chave por campo do quadro (sem
# curinga): un, fonte, normal?, aviso?, critico?, regimes? (o topo fica sem normal/aviso/critico), ativo_se?. O normal termina
# exatamente no limite do aviso.
F_MOTORES = ARQ['g_motores'] + ' §9 · Faixas de operação'
F_GERADOR = ARQ['g_gerador'] + ' §9 · Potência e carga'
F_SEAKEEPER = ARQ['g_seakeeper'] + ' §8 · Faixas'
F_ELETRICO = ARQ['g_eletrico'] + ' §2 · Faixas'
F_PORAO = ARQ['g_porao'] + ' §2 · Faixas'
F_SONDA = ARQ['g_eletronicos'] + ' §8 · Sonda'
F_ABAST = ARQ['checklist'] + ' § Abastecimento'
F_TANQUES = ARQ['checklist'] + ' § Tanques'
DIESEL_AVISO_PCT = 25            # abastecer antes de 25 % (a regra do checklist)
# Os números que o guia e o item do checklist dizem juntos saem de uma constante só (revisão do C10, §0.10): o texto do guia e o `t` do item
# (c03, f02, s05, s06, a07) são montados dela, e a FUNCOES (confere.py) confere que cada número do `t` está na seção que a `fonte` cita.
PARADA_MOTORES_MIN = (2, 3)      # minutos em marcha lenta antes de desligar os motores (g_motores §6; checklist c03)
LANCE_ANCORA_VEZES = (3, 5)      # lance de corrente, em vezes a profundidade (g_ancora §1; checklist f02)
LENTA_RPM = (650, 750)           # faixa de marcha lenta do guia (o laço anda em 700/695 rpm)
ARREF_CRUZEIRO_C = (80, 85)      # arrefecimento em cruzeiro, motor aquecido
CONSUMO_MAX_LPH = 111            # dois motores na rotação máxima: cerca de 2 × 55,6 L/h (folha do fabricante)
GERADOR_CLIMA_KW = (5.5, 6.5)    # carga do gerador com a climatização ligada (o laço anda entre 5,6 e 6,4 kW)


def _limites_motor(lado):
    rpm = 'motor_%s_rpm' % lado
    return {
        'motor_%s_oleo_bar' % lado: {'un': 'bar', 'fonte': F_MOTORES, 'regimes': [
            {'rpm_campo': rpm, 'rpm_ate': 1000, 'normal': {'de': 1.0, 'ate': 6.0}, 'aviso': {'abaixo': 1.0, 'acima': 6.0}, 'critico': {'abaixo': 0.6}},
            {'rpm_campo': rpm, 'rpm_de': 1000, 'normal': {'de': 2.4, 'ate': 6.0}, 'aviso': {'abaixo': 2.4, 'acima': 6.0}, 'critico': {'abaixo': 1.4}}],
            'ativo_se': {'campo': rpm, 'acima': 0}},
        'motor_%s_arref_c' % lado: {'un': '°C', 'fonte': F_MOTORES, 'normal': {'ate': 88}, 'aviso': {'acima': 88}, 'critico': {'acima': 97},
                                    'ativo_se': {'campo': rpm, 'acima': 0}},
        rpm: {'un': 'rpm', 'fonte': F_MOTORES, 'normal': {'ate': 2600}, 'aviso': {'acima': 2600}},
        'motor_%s_carga_pct' % lado: {'un': '%', 'fonte': F_MOTORES, 'normal': {'ate': 90}, 'aviso': {'acima': 90}, 'ativo_se': {'campo': rpm, 'acima': 0}},
    }


def _bateria(de, ate, critico):
    return {'un': 'V', 'fonte': F_ELETRICO, 'normal': {'de': de, 'ate': ate}, 'aviso': {'abaixo': de, 'acima': ate}, 'critico': {'abaixo': critico}}


DIESEL_AVISO_L = TANQUES['diesel_l'] * DIESEL_AVISO_PCT // 100     # 400 L
DIESEL_RESERVA_L = int(round(TANQUES['diesel_l'] * RESERVA))         # 160 L (reserva técnica de 10 %)
LIMITES = {}
LIMITES.update(_limites_motor('bb'))
LIMITES.update(_limites_motor('be'))
LIMITES.update({
    'temp_praca_maquinas_c': {'un': '°C', 'fonte': F_MOTORES, 'normal': {'ate': 60}, 'aviso': {'acima': 60}},
    'bateria_0_tensao_v': _bateria(24.4, 29.4, 23.6),   # serviço 24 V
    'bateria_1_tensao_v': _bateria(24.4, 29.4, 23.6),   # partida 24 V
    'bateria_2_tensao_v': _bateria(12.2, 14.7, 11.8),   # 12 V (eletrônica e estabilizador)
    'porao_bb_nivel': {'un': 'cm', 'fonte': F_PORAO, 'normal': {'ate': 5}, 'aviso': {'acima': 5}, 'critico': {'acima': 10}},
    'porao_be_nivel': {'un': 'cm', 'fonte': F_PORAO, 'normal': {'ate': 5}, 'aviso': {'acima': 5}, 'critico': {'acima': 10}},
    'profundidade_m': {'un': 'm', 'fonte': F_SONDA, 'normal': {'de': 3.0}, 'aviso': {'abaixo': 3.0}, 'critico': {'abaixo': 2.0}},
    'diesel_litros': {'un': 'L', 'fonte': F_ABAST, 'normal': {'de': DIESEL_AVISO_L}, 'aviso': {'abaixo': DIESEL_AVISO_L}, 'critico': {'abaixo': DIESEL_RESERVA_L}},
    'gerador_kw': {'un': 'kW', 'fonte': F_GERADOR, 'normal': {'ate': 8.1}, 'aviso': {'acima': 8.1}, 'ativo_se': {'campo': 'gerador_ativo', 'igual': True}},
    'seakeeper_volante_pct': {'un': '%', 'fonte': F_SEAKEEPER, 'normal': {'de': SEAKEEPER_ESTABILIZA_PCT}, 'aviso': {'abaixo': SEAKEEPER_ESTABILIZA_PCT},
                              'ativo_se': {'campo': 'seakeeper_ativo', 'igual': True}},
    'tanque_agua_pct': {'un': '%', 'fonte': F_TANQUES, 'normal': {'de': 15}, 'aviso': {'abaixo': 15}},
    'tanque_cinzas_pct': {'un': '%', 'fonte': F_TANQUES, 'normal': {'ate': 80}, 'aviso': {'acima': 80}},
    'tanque_negras_pct': {'un': '%', 'fonte': F_TANQUES, 'normal': {'ate': 80}, 'aviso': {'acima': 80}},
})


# Passos dos alertas (D.replay.alertas, §1.16): frases do próprio guia de bordo, na seção que o alerta cita (fonte única). As seções
# que já têm o procedimento (g_motores §4 e §5) entram como estão; nas que só trazem a faixa, o texto do guia ganha uma frase com os
# mesmos passos (cadeia()). A IDS confere que cada passo está inteiro na seção citada.
PASSOS_ARREF = ['Reduza para marcha lenta e confira a saída de água pelo escapamento.',
                'Sem água no escapamento ou com a temperatura ainda subindo: desligue o motor afetado e siga com o outro.',
                'Com o motor parado, feche a válvula de fundo e confira o filtro de água salgada e o rotor da bomba de água salgada.']
PASSOS_ROTACAO = ['Reduza o giro para o cruzeiro.', 'Confira o painel dos dois motores.', 'Registre no diário com a hora.']
PASSOS_PRACA = ['Reduza o giro para o cruzeiro.', 'Confira a ventilação da praça de máquinas.', 'Registre no diário com a hora.']
PASSOS_BATERIA = ['Confira o carregador de bordo ligado ao gerador ou ao cais.', 'Confira os bornes limpos e apertados.',
                  'Registre a tensão e a hora no diário.']
# Revisão do C8: os três passos de antes só mandavam ligar a bomba e anotar no diário, sem a entrada de água nem a escalada que o resto do app trata
# como padrão (protocolos.alagamento: «procure a entrada… Água subindo mesmo assim: MAYDAY»). O aviso (acima de 5 cm) e o crítico (acima de 10 cm)
# valem igual. Sem MMSI nem posição; a frase do SOS casa a SEGURANCA_PALAVRAS (alagamento, SOS), então o trecho do guia §2 leva seguranca: true e
# nunca vai à IA (trecho_seguro).
PASSOS_PORAO = ['Confirme a bomba ligada pelo sensor de nível.', 'Acione a bomba no manual.', 'Procure a entrada de água.',
                'Nível subindo com a bomba ligada ou água entrando é alagamento: use o SOS do app.', 'Registre o nível e a hora no diário.']
PASSOS_SONDA = ['Reduza a velocidade.', 'Confira a carta no plotter.', 'Mude de rumo para águas mais fundas.']
PASSOS_DIESEL = ['Abasteça antes da próxima saída.', 'Confira a autonomia no app.', 'Registre os litros e o nível no app depois de abastecer.']
PASSOS_GERADOR = ['Retire cargas no quadro elétrico, uma de cada vez.', 'Deixe a climatização por último.', 'Registre no diário com a hora.']
PASSOS_VOLANTE = ['Confira o banco de 12 V e o carregador.', 'Espere a indicação do display.', 'Anote a mensagem do display no diário com a hora.']
PASSOS_AGUA = ['Complete a água doce na marina.', 'Confira o nível no app.', 'Registre no diário com a hora.']
PASSOS_SERVIDAS = ['Esvazie as servidas na marina.', 'Confira o nível no app.', 'Registre no diário com a hora.']


def cadeia(prefixo, passos):
    """Frase do guia com os passos de um alerta: «Prefixo: passo um; passo dois; passo três.» (cada passo sem o ponto final, a 1ª letra
    minúscula). A IDS compara sem caixa nem pontuação, por isso o passo do alerta é a frase inteira do guia."""
    return prefixo + ': ' + '; '.join(x[0].lower() + x[1:].rstrip('.') for x in passos) + '.'


def br(x):
    """Número como o guia escreve (pt-BR): 1.000 · 2.600 · 2,4 · 6,0 · 88. O float guarda a casa decimal (6.0 → "6,0")."""
    if isinstance(x, int) and not isinstance(x, bool):
        return '{:,}'.format(x).replace(',', '.')
    inteiro, dec = repr(float(x)).split('.')
    return '{:,}'.format(int(inteiro)).replace(',', '.') + ',' + dec


def de_a(faixa):
    """Faixa como o guia escreve: (2, 3) → «2 a 3»."""
    return '%s a %s' % (br(faixa[0]), br(faixa[1]))


def _eq(i):
    return next(e for e in EQUIPAMENTOS if e['id'] == i)


# Revisão do C5: a regra é sobre o total dos dois tanques, como o LIMITES['diesel_litros'] (aviso abaixo de 400 L): 25 % de um tanque de
# 800 L seriam 200 L, e "em qualquer tanque" mandava abastecer com 200 L num tanque e 800 L no outro (1.000 L), sem aviso no limite.
REGRA_ABAST = 'abastecer antes de %s %% do total dos tanques, %s L de %s L (%s)' % (
    br(DIESEL_AVISO_PCT), br(DIESEL_AVISO_L), br(TANQUES['diesel_l']), F_ABAST)


def texto_faixas_motores():
    lenta, alta = LIMITES['motor_bb_oleo_bar']['regimes']
    ar, rpm = LIMITES['motor_bb_arref_c'], LIMITES['motor_bb_rpm']
    corte = br(lenta['rpm_ate'])
    return ('Faixas de operação (motor aquecido). Rotação: marcha lenta %s a %s rpm; cruzeiro %s rpm (%s nós); até %s rpm. '
            'Pressão de óleo: abaixo de %s rpm, normal de %s a %s bar; a partir de %s rpm, normal de %s a %s bar. '
            'Aviso abaixo do normal ou acima de %s bar. Crítico abaixo de %s bar (abaixo de %s rpm) ou de %s bar (a partir de %s rpm). '
            'Líquido de arrefecimento: normal até %s °C (em cruzeiro, %s a %s °C); aviso acima de %s °C; crítico acima de %s °C. '
            'Carga: aviso acima de %s %%. Praça de máquinas: aviso acima de %s °C.') % (
        br(LENTA_RPM[0]), br(LENTA_RPM[1]), br(CONSUMO['cruzeiro']['rpm']), br(CONSUMO['cruzeiro']['nos']), br(rpm['normal']['ate']),
        corte, br(lenta['normal']['de']), br(lenta['normal']['ate']), corte, br(alta['normal']['de']), br(alta['normal']['ate']),
        br(alta['aviso']['acima']), br(lenta['critico']['abaixo']), corte, br(alta['critico']['abaixo']), corte,
        br(ar['normal']['ate']), br(ARREF_CRUZEIRO_C[0]), br(ARREF_CRUZEIRO_C[1]), br(ar['aviso']['acima']), br(ar['critico']['acima']),
        br(LIMITES['motor_bb_carga_pct']['aviso']['acima']), br(LIMITES['temp_praca_maquinas_c']['aviso']['acima'])) + ' ' + cadeia(
            'Rotação ou carga acima do normal', PASSOS_ROTACAO) + ' ' + cadeia('Praça de máquinas acima do normal', PASSOS_PRACA)


def texto_consumo_motores():
    n = _eq('motores')['nominal']
    return ('Consumo dos dois motores: cerca de %s L/h em marcha lenta (%s rpm, 5 nós), %s L/h em cruzeiro (%s rpm, %s nós) e %s L/h '
            'na rotação máxima.') % (br(CONSUMO['lenta']['lph']), br(n['rpm_lenta']), br(CONSUMO['cruzeiro']['lph']),
                                     br(CONSUMO['cruzeiro']['rpm']), br(CONSUMO['cruzeiro']['nos']), br(CONSUMO_MAX_LPH))


def texto_potencia_gerador():
    n, kw = _eq('gerador')['nominal'], LIMITES['gerador_kw']['aviso']['acima']
    return ('Potência nominal %s kW (%s Hz, %s rpm). Carga: normal até %s kW; aviso acima de %s kW (%s %% da nominal). Com a '
            'climatização ligada, o normal é %s a %s kW. %s') % (br(n['kw']), br(n['hz']), br(n['rpm']), br(kw), br(kw),
                                                              br(int(round(kw / n['kw'] * 100))), br(GERADOR_CLIMA_KW[0]), br(GERADOR_CLIMA_KW[1]),
                                                              cadeia('Carga acima do normal', PASSOS_GERADOR))


def texto_faixas_volante():
    return 'Volante: estabiliza a partir de cerca de %s %% da rotação de operação; aviso abaixo de %s %% (sem estabilização). %s' % (
        br(_eq('estabilizador')['nominal']['pct_estabiliza']), br(LIMITES['seakeeper_volante_pct']['aviso']['abaixo']),
        cadeia('Volante abaixo do normal', PASSOS_VOLANTE))


def texto_faixas_baterias():
    def banco(L):
        return 'normal de %s a %s V; aviso abaixo de %s V ou acima de %s V; crítico abaixo de %s V' % (
            br(L['normal']['de']), br(L['normal']['ate']), br(L['aviso']['abaixo']), br(L['aviso']['acima']), br(L['critico']['abaixo']))
    return 'Bancos de 24 V (serviço e partida): %s. Banco de 12 V: %s. %s' % (banco(LIMITES['bateria_0_tensao_v']), banco(LIMITES['bateria_2_tensao_v']),
                                                                              cadeia('Tensão fora do normal', PASSOS_BATERIA))


def texto_faixas_porao():
    L = LIMITES['porao_bb_nivel']
    return ('Nível normal no poço das bombas: até %s cm; aviso acima de %s cm; crítico acima de %s cm. As bombas ligam sozinhas pelo '
            'sensor de nível. %s') % (br(L['normal']['ate']), br(L['aviso']['acima']), br(L['critico']['acima']), cadeia('Nível acima do normal', PASSOS_PORAO))


def texto_sonda():
    L = LIMITES['profundidade_m']
    return 'Profundidade mínima de navegação: %s m na sonda (aviso abaixo de %s m; crítico abaixo de %s m). %s' % (
        br(L['normal']['de']), br(L['aviso']['abaixo']), br(L['critico']['abaixo']), cadeia('Profundidade abaixo do mínimo', PASSOS_SONDA))


def texto_abastecimento():
    L = LIMITES['diesel_litros']
    return ('Diesel: abastecer antes de %s %% do total dos tanques (%s L de %s L); reserva técnica de %s %% (%s L). Depois de abastecer, '
            'registre os litros e o nível no app. %s') % (br(DIESEL_AVISO_PCT), br(L['aviso']['abaixo']), br(TANQUES['diesel_l']),
                                                          br(int(round(RESERVA * 100))), br(L['critico']['abaixo']),
                                                          cadeia('Diesel abaixo do aviso', PASSOS_DIESEL))


def texto_tanques():
    return ('Tanques: água doce, aviso abaixo de %s %%; águas cinzas e negras, aviso acima de %s %%. Na marina, antes da saída: água '
            'completada e servidas esvaziadas. %s %s') % (br(LIMITES['tanque_agua_pct']['aviso']['abaixo']), br(LIMITES['tanque_cinzas_pct']['aviso']['acima']),
                                                          cadeia('Água doce abaixo do aviso', PASSOS_AGUA), cadeia('Servidas acima do aviso', PASSOS_SERVIDAS))


# ——————————————————————————————— TEXTOS DE EMERGÊNCIA (CONTRATO §1.3) ———————————————————————————————
# Fonte única dos textos do procedimento padrão: os guias que os repetem (g_motores §4, g_porao §4, g_eletronicos §5, g_ais §2,
# g_seafire, g_epirb e o protocolo) saem daqui desde o C5, e o D.protocolos do C6 é montado com eles. Sem bar, %, nós, mn, graus,
# posição, lugar a bordo, número de pessoas, tempo em minutos, fabricante nem modelo (PROTOCOLO_LIMPO). Grafia "Seafire".
ROTULO = 'procedimento padrão — confirmar com o protocolo de bordo'   # EXCEÇÃO do §3 do PROMPT (rótulo de segurança)
MMSI_RADIO = 'MMSI do rádio de bordo (etiqueta / Licença de Estação)'  # trava §2.2: no MAYDAY, no DSC e no AIS, nunca o número
TXT_ROTEIRO = ['MAYDAY, MAYDAY, MAYDAY', 'AQUI É ' + ', '.join([EMBARCACAO['nome'].upper()] * 3),
               'MMSI — LEIA NA ETIQUETA DO RÁDIO (Licença de Estação)', 'POSIÇÃO — LEIA NO PLOTTER AGORA', 'NATUREZA DO PERIGO: ________',
               'PESSOAS A BORDO: conte agora', 'AUXÍLIO NECESSÁRIO: ________', 'CÂMBIO']
TXT_MOB = ['Grite HOMEM AO MAR e o lado (bombordo ou boreste). Jogue a boia ou qualquer objeto que flutue.',
           'Uma pessoa só aponta para quem caiu, sem perder de vista. Marque MOB no plotter.',
           'Volte devagar, com o motor em neutro perto da pessoa (hélice). Se perder de vista: MAYDAY no canal 16 com a posição da marca '
           'MOB lida no plotter.']
TXT_SEAFIRE = ['Fogo no motor ou alarme do sistema fixo: desligue motores e gerador e corte a ventilação do motor.',
               'Se o sistema não disparou sozinho e há fogo no motor, use o disparo manual.',
               'Não abra o acesso ao motor depois da descarga: espere o tempo indicado na etiqueta do sistema e o motor esfriar.',
               'Fogo pequeno fora do motor: extintor portátil na base das chamas, de costas para a saída.',
               'Fogo que não apaga: MAYDAY no canal 16 e prepare o abandono.']
TXT_EPIRB = ['Só em perigo grave e iminente, depois do MAYDAY (ou sem rádio).',
             'Acione conforme a etiqueta do equipamento e deixe a antena para cima, com céu aberto.',
             'Leve o EPIRB para a balsa ou mantenha-o flutuando preso por um cabo. Não desligue até o resgate.',
             'Disparo por engano: desligue e avise no canal 16.']
TXT_EPIRB_TESTE = ['Teste da baliza (EPIRB): faça o autoteste conforme a etiqueta. O teste não envia alerta.',
                   'Confira na etiqueta a validade da bateria e do disparador hidrostático.']
TXT_ALAGAMENTO = ['Água entrando: ligue as bombas de porão no manual, procure a entrada (válvulas de fundo, mangueiras, eixos) e feche o '
                  'que puder. Água subindo mesmo assim: MAYDAY no canal 16.']
TXT_ABANDONO = ['Abandono: só quando não houver como manter o barco. Antes, MAYDAY no canal 16. Coletes em todos; leve o EPIRB e o VHF '
                'portátil; embarque na balsa sem pular na água.']
TXT_OLEO = ['Reduza para marcha lenta e confira o manômetro agora.', 'Compare BB e BE no mesmo giro: só um lado baixo aponta o motor.',
            'Com o motor parado, procure vazamento e confira o nível de óleo na vareta.',
            'Se continuar baixa, desligue o motor afetado, siga com o outro e chame a oficina dos motores.']
TXT_SALVATAGEM = ('Em perigo agora: SOS do app e VHF canal 16. Coletes: um por pessoa — conte as pessoas a bordo agora (lotação: veja a '
                  'placa de lotação). Balsa, coletes, boias, extintores e sinalizadores: no local da placa de salvatagem e do plano de '
                  'segurança de bordo — confira na saída.')   # PROMPT §2.3, letra por letra
TXT_PANPAN = ('Urgência sem perigo imediato de vida (pane, sem governo, alguém ferido sem risco de morte): PAN-PAN, PAN-PAN, PAN-PAN no '
              'canal 16, no mesmo formato da chamada MAYDAY.')
TXT_DSC = ('O botão DISTRESS envia o alerta com a identificação programada no rádio: é o ' + MMSI_RADIO + '. Depois do alerta, faça o '
           'MAYDAY por voz no canal 16.')
# Rótulos de tela do SOS e da conversa em emergência (PROMPT §2.2): quem lê é a 1b (S1/S2, F3) e a Fase 3 (cérebro); aqui só o texto.
MMSI_ROTULO = 'MMSI (cadastro do app)'                     # no lugar de "MMSI da embarcação (DSC)" na F3: o número é o do cadastro, não o do rádio
TXT_INDICATIVO = 'o da Licença de Estação (no rádio)'     # o indicativo nunca é gerado (prefixos PP–PY e ZV–ZZ são reais)
TXT_PLOTTER = 'POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER · PESSOAS: CONTE AGORA'   # troca do emergenciaAte e do resumoAgora() do SOS
TXT_HUD = 'POSIÇÃO · LEIA NO PLOTTER'                       # HUD da CONVERSA com alerta: true


def cap(s):
    return s[:1].upper() + s[1:]


FIM_ROTULO = cap(ROTULO) + '.'
FIM_SEGURANCA = FIM_ROTULO + ' ' + cap(NOTA_ETIQUETA) + '.'   # fim de todo texto de g_seafire, g_epirb e da Salvatagem (§1.5)


def fim_seguro(*frases):
    return ' '.join(frases) + ' ' + FIM_SEGURANCA


def roteiro_falado():
    return ' — '.join(r.replace(': ________', '') for r in TXT_ROTEIRO)


# ——————————————————————————————— GUIAS DE BORDO → base de conhecimento ———————————————————————————————
# Orientação de operação escrita para a embarcação, por seção (§n). Sem "calado" até a Fase 3 (CALADO_FORA), sem número do
# snapshot, sem código numérico de alarme, capacidade de óleo, torque ou especificação de fluido; o estabilizador só no banco de
# 12 V (ESTABILIZADOR_12V); os números de faixa saem da LIMITES. "seg" é o mínimo de seguranca do §1.5 (True = todas as seções;
# um conjunto = os números de seção ou os títulos); a marcação pela SEGURANCA_PALAVRAS (segura) pode pegar mais, nunca menos.
def equip_de(*ids):
    """"<nome> <fabricante> <modelo>" de cada equipamento (o fabricante não se repete quando o modelo já começa por ele); os de
    segurança só pelo nome, sem fabricante nem modelo (§1.5)."""
    out = []
    for i in ids:
        e = _eq(i)
        if e.get('seguranca'):
            out.append(e['nome'])
        else:
            fab = '' if e['modelo'].lower().startswith(e['fabricante'].lower()) else e['fabricante'] + ' '
            out.append(e['nome'] + ' ' + fab + e['modelo'])
    return ' · '.join(out)


NOTA_GUIA = 'Guia de bordo da embarcação: orientação de operação, não substitui o manual do fabricante.'
NOTA_PROTOCOLO = 'Procedimento padrão internacional, não é o protocolo de bordo: confirmar com o protocolo da embarcação.'
GUIAS = {
    'g_motores': {
        'titulo': ARQ['g_motores'], 'pasta': 'manuais', 'equip': equip_de('motores'), 'seg': {'4', '18'},
        'secoes': [
            ('1 · Antes da partida', 'Com os motores parados e frios: nível de óleo na vareta, líquido de arrefecimento, correias, válvulas de fundo abertas, porão seco e ventilação da praça de máquinas ligada por alguns minutos.'),
            ('2 · Partida', 'Dê a partida pelo painel, um motor de cada vez, com a marcha em neutro. Logo depois confira a saída de água pelo escapamento e a pressão de óleo no painel dos dois motores.'),
            ('3 · Aquecimento', 'Deixe alguns minutos em marcha lenta antes de acelerar. Evite rotação alta com o motor frio e suba o giro aos poucos.'),
            ('4 · Pressão de óleo baixa', ' '.join(TXT_OLEO)),
            # Revisão 3 do C5: sem água de refrigeração, desliga na hora (o escapamento molhado superaquece); filtro e rotor só com o motor
            # parado e a válvula de fundo fechada, como o g_gerador §3 e §5. É o trecho do AVISO de arrefecimento do laço (§3.1).
            ('5 · Temperatura alta', 'Reduza para marcha lenta e confira a saída de água pelo escapamento. Sem água no escapamento ou com a temperatura ainda subindo: desligue o motor afetado e siga com o outro. Com o motor parado, feche a válvula de fundo e confira o filtro de água salgada e o rotor da bomba de água salgada. Nunca abra a tampa do arrefecimento com o motor quente.'),
            # Revisão 4 do C5: "Depois de navegar" faz de "como esfriar o motor depois de navegar" a pergunta deste trecho (3 das 4 palavras).
            ('6 · Parada', 'Depois de navegar, deixe de %s minutos em marcha lenta antes de desligar, para o motor esfriar por igual.' % de_a(PARADA_MOTORES_MIN)),
            # Revisão 3 do C11: 450 h e 1.300 h são a marca do horímetro (a agenda tem faltam = limite − atual), não o intervalo entre trocas: dito como "ao chegar a … no horímetro".
            ('7 · Manutenção na agenda', 'Troca de óleo e filtros: 12 meses ou ao chegar a 450 h no horímetro (o que vier antes). Rotor da bomba de água salgada: a cada 12 meses. Revisão anual pela oficina de motores.'),
            ('8 · Horímetros', 'Os horímetros de BB e BE aparecem no painel dos motores e na telemetria.'),
            ('9 · Faixas de operação', texto_faixas_motores()),
            ('10 · Consumo', texto_consumo_motores()),
            ('11 · Faixas de rotação: da marcha lenta ao cruzeiro', 'Os motores trabalham em cinco faixas de rotação. Marcha lenta, de 600 a 1.000 rpm: manobra e aquecimento, com o motor perto de 700 rpm, cerca de 5 nós e 6,2 L/h nos dois motores. Deslocamento, de 1.000 a 1.500 rpm: navegação lenta, com o casco ainda em deslocamento. Transição, de 1.500 a 1.800 rpm: passagem do deslocamento para o planeio. Planeio, de 1.800 a 2.000 rpm: o casco já plana. Cruzeiro, de 2.000 a 2.600 rpm: a referência é 2.050 rpm, cerca de 18 nós e 68 L/h nos dois motores. Máxima: 2.600 rpm, cerca de 26 nós e 111 L/h nos dois motores; acima disso a rotação está acima do normal. Aumente o giro por etapas, sem acelerar de uma vez, e use rotação alta só depois que a temperatura de arrefecimento estabilizar.'),
            ('12 · O que conferir durante a navegação', 'Olhe os painéis dos dois motores em intervalos regulares e compare BB com BE no mesmo giro: rotação, pressão de óleo, temperatura de arrefecimento e carga devem ser parecidas; uma diferença que cresce com o tempo é o primeiro sinal de problema. Pressão de óleo: de 2,4 a 6,0 bar a partir de 1.000 rpm; abaixo de 2,4 bar é aviso e abaixo de 1,4 bar é crítico. Temperatura de arrefecimento: normal até 88 °C; acima disso é aviso e acima de 97 °C é crítico. Carga e rotação: aviso com carga acima de 90 % ou rotação acima de 2.600 rpm. Praça de máquinas: aviso acima de 60 °C. Na ronda pela praça de máquinas, procure óleo, água ou combustível pingando, ruídos novos e, com a saída do escapamento visível, confira a água saindo; mantenha mãos e roupas longe das correias e dos eixos. Anote no diário qualquer diferença entre os lados, com a rotação e a hora: um lado diferente do outro, mesmo dentro da faixa, merece registro.'),
            ('13 · Conferir o nível de óleo e do líquido de arrefecimento', 'Confira os dois níveis nos dois motores, parados e frios, antes da partida, e complete só com o produto que o manual do fabricante especifica. Com o motor parado há alguns minutos e o barco nivelado, retire a vareta, limpe com um pano, encaixe até o fim e retire de novo: o nível deve ficar entre as marcas de mínimo e máximo. Se faltar óleo, complete aos poucos e releia a vareta; nunca passe da marca de máximo. Líquido de arrefecimento: com o motor frio, confira o nível no reservatório de expansão ou, se o motor não tiver reservatório, no bocal de enchimento. Não abra a tampa do arrefecimento com o motor quente: o líquido sai sob pressão. Compare BB e BE: se um motor pede óleo ou líquido com frequência bem maior que o outro, avise a oficina de motores. Tipo e quantidade de óleo e de líquido: só pelo manual do fabricante.'),
            ('14 · Motor não pega na partida', 'Com as manetes em neutro e o painel ligado, sem alarme aceso, a pressão de óleo deve subir logo após a partida: abaixo de 1.000 rpm o normal é de 1,0 a 6,0 bar. Compare os dois painéis ao repetir no outro motor: rotação, pressão de óleo e temperatura devem ser parecidas. Sem pressão de óleo poucos segundos depois da partida, desligue o motor e não insista. Se o motor não pegar, espere um pouco entre as tentativas e confira o banco de partida (24,4 a 29,4 V), o diesel nos tanques e o filtro separador.'),
            ('15 · Sem água saindo pelo escapamento do motor', 'O escapamento molhado é refrigerado pela mesma água salgada que refrigera o motor; sem água saindo, motor e escapamento superaquecem rápido. Se estiver navegando, desligue o motor afetado e siga com o outro. Com o motor parado, feche a válvula de fundo da água salgada antes de abrir qualquer peça do circuito, abra e limpe o filtro de água salgada (algas, plástico e sujeira são causas comuns) e confira o rotor da bomba de água salgada: palhetas gastas, trincadas ou faltando pedem troca. Se faltar pedaço do rotor, procure-o no circuito de água antes de religar; na dúvida, chame a oficina de motores. Monte tudo, abra a válvula de fundo, confira que não há vazamento no filtro e religue: confirme a água saindo pelo escapamento logo após a partida, e desligue de novo se não sair. Não ligue o motor com a válvula de fundo fechada: o rotor trabalha a seco e se danifica.'),
            ('16 · Motor perdendo rotação ou sem força', 'Queda de rotação sem mexer na manete aponta falta de combustível, carga excessiva ou o motor se protegendo de outro problema; o teste em neutro separa o motor da hélice e do eixo. Compare BB e BE: veja se a queda é em um motor só e se a carga mostrada está alta ou baixa, e olhe o painel por alarme de temperatura ou de pressão de óleo (motores eletrônicos podem limitar a potência para se proteger). Em local seguro, passe para neutro e acelere só um pouco: se a rotação sobe sem esforço, o problema está na carga (cabo, rede ou sujeira na hélice) ou no eixo; se a rotação também cai em neutro, suspeite de combustível (nível nos tanques, água no filtro separador e filtros sujos). Com o motor parado, drene a água do filtro separador de combustível, com um recipiente embaixo, e veja se o diesel que sai está limpo. Com o motor ainda sem força, siga devagar com o outro motor e chame a oficina de motores. Não acelere forte em neutro; motor que perde força de repente, ou volta a perder, é assunto da oficina de motores.'),
            ('17 · Vibração anormal nos motores ou no eixo', 'Vibração nova costuma vir da hélice, do eixo, dos suportes do motor ou de um cilindro trabalhando mal; veja em que rotação ela aparece e se é de um lado só. Anote a rotação em que a vibração aparece e se ela é de um lado só (BB ou BE) ou dos dois: um lado só aponta o motor, o eixo ou a hélice daquele lado. Saia da faixa de rotação em que vibra e evite manter o motor nela. Em local seguro, passe para neutro e acelere com cuidado: se a vibração some, o problema está na hélice, no eixo ou no alinhamento; se continua, no motor ou nos coxins. Com o motor parado, confira se os coxins e os parafusos de fixação do motor estão firmes. Hélice com cabo, rede ou deformada, e alinhamento do eixo, pedem inspeção com o barco fora da água ou por mergulhador, sempre com os motores desligados. Evite manter a rotação em que o barco vibra forte: a vibração desgasta eixo, suportes e motor. Antes de alguém entrar na água perto das hélices, desligue os motores.'),
            ('18 · Fumaça no escapamento: o que a cor indica', 'A cor da fumaça do escapamento dá uma pista do problema: fumaça branca na partida a frio é comum; a que persiste com o motor aquecido merece atenção. Note de qual motor sai e em que rotação, e confira os painéis. Preta: mistura rica, carga alta — reduza a rotação e confira casco, hélices e filtro de ar. Azulada: óleo na combustão — confira o nível de óleo e avise a oficina se o consumo estiver alto. Branca persistente: diesel não queimado ou água na combustão — com o motor parado, drene o filtro separador e chame a oficina. Perda de força ou barulho diferente: reduza a rotação e chame a oficina. Registre no diário a cor, o lado, a rotação e a hora. Fumaça fora do escapamento, na praça de máquinas ou nas cabines, não é diagnóstico: siga o protocolo de bordo.'),
            ('19 · Filtro separador de água do combustível', 'O filtro separador retém água e sujeira do diesel antes do motor; confira antes de sair e drene a água acumulada — a troca do elemento está ligada à revisão anual dos motores. Com o motor parado, olhe o filtro separador e veja se há água ou sujeira acumulada na parte de baixo; se houver água, drene pelo dreno do filtro, com um recipiente embaixo, até sair só diesel. Não deixe o diesel cair no porão nem na água: recolha tudo e descarte como resíduo. Muita água, ou água que volta logo depois de drenar, indica diesel contaminado: avise a oficina de motores. Peça a troca do elemento na revisão anual, ou antes, se a rotação cair com carga ou o motor perder força. Depois de abrir o sistema de combustível, retire o ar da linha pelo procedimento do manual do fabricante; na dúvida, deixe com a oficina de motores. Só abra o sistema de combustível com o motor parado e frio.'),
            ('20 · Rotor (impeller) da bomba de água salgada dos motores', 'O rotor de borracha empurra a água salgada que refrigera o motor e se desgasta com o uso; a troca é prevista a cada 12 meses, feita pela oficina de motores. Observe os sinais de rotor gasto: temperatura de arrefecimento subindo, pouca água no escapamento ou pingos na tampa da bomba. Para inspecionar, desligue o motor e feche a válvula de fundo da água salgada, abra a tampa da bomba, retire o rotor e procure palhetas gastas, trincadas, achatadas ou faltando; se faltar pedaço, procure no circuito de água antes de religar. Encaixe o rotor girando-o no sentido de giro da bomba, para as palhetas se dobrarem do jeito certo, e lubrifique como o manual do fabricante indica. Feche a tampa com junta em bom estado, abra a válvula de fundo, confira que não há vazamento, dê a partida e confirme a água saindo pelo escapamento. Rotor nunca pode trabalhar a seco: não ligue o motor com a válvula de fundo fechada. Pela agenda, a troca é da oficina de motores; com a bomba aberta, deixe o painel desligado.'),
            ('21 · Inspeção periódica: correias, mangueiras e anodos', 'Além dos níveis, vale uma inspeção visual regular nas correias, mangueiras, braçadeiras e anodos, sempre com o motor parado e frio: peças gastas avisam antes de falhar. Correias: procure trincas, fiapos, partes brilhantes ou ressecadas, pressione com o dedo no meio do vão para ver se não cedem demais e troque ao primeiro sinal de desgaste, com uma sobressalente a bordo. Mangueiras e braçadeiras: procure ressecamento, rachaduras, inchaço, braçadeira enferrujada ou frouxa e marcas de óleo ou de sal seco em volta das conexões (sal cristalizado indica pingo de água salgada). Anodos de sacrifício (zinco, alumínio ou magnésio, conforme a água) corroem no lugar das peças de metal: confira o desgaste e troque o que estiver muito consumido. Os anodos do casco e do eixo são trocados com a limpeza do casco, a cada 6 meses pela agenda; peça à marina. Confira também a fixação do motor, os coxins e o escapamento: parafusos firmes e sem folga. Inspecione só com o motor parado e frio; com o motor ligado, mantenha mãos e roupas longe das correias.'),
        ],
    },
    'g_gerador': {
        'titulo': ARQ['g_gerador'], 'pasta': 'manuais', 'equip': equip_de('gerador'), 'seg': {'18'},
        'secoes': [
            ('1 · Antes de ligar', 'Com o gerador parado, confira o nível de óleo e o líquido de arrefecimento. Abra a válvula de fundo da entrada de água salgada e confira se o filtro de água salgada está limpo. Ligue a ventilação do compartimento por alguns minutos se houver cheiro de combustível.'),
            # §2 fica no 1º lugar do buscaBase para "como ligar o gerador?" (FONTE_IA do chat_ia.py): mantém "PARTIDA" e "gerador".
            ('2 · Ligar', 'No painel do gerador, pressione e segure PARTIDA até o motor pegar. Aguarde a tensão e a frequência estabilizarem no painel. Só depois transfira as cargas no quadro elétrico, uma de cada vez; ligue a climatização por último.'),
            ('3 · Água no escapamento', 'Com o gerador ligado, confira a saída de água pelo escapamento. Sem água saindo, desligue na hora: é sinal de falta de refrigeração (válvula de fundo fechada, filtro entupido ou rotor danificado).'),
            ('4 · Desligar', 'Retire as cargas no quadro elétrico. Deixe o gerador funcionar de 3 a 5 minutos sem carga para esfriar e pressione PARADA. Feche a válvula de fundo se o barco for ficar parado por vários dias.'),
            ('5 · Alarme de alta temperatura', 'Desligue o gerador. Verifique a válvula de fundo, o filtro de água salgada e o rotor (impeller). Nunca abra a tampa do arrefecimento com o motor quente. Registre o alarme no diário.'),
            ('6 · Alarme de baixa pressão de óleo', 'Desligue o gerador e confira o nível de óleo com ele parado. Se o nível estiver correto e o alarme voltar, não religue: chame o técnico de bordo.'),
            ('7 · Manutenção na agenda', 'Óleo e filtros: 12 meses ou ao chegar a 1.300 h no horímetro (o que vier antes). Rotor (impeller): inspeção a cada 12 meses e troca quando estiver gasto.'),
            ('8 · Horímetro', 'O horímetro aparece no painel do gerador e na telemetria.'),
            ('9 · Potência e carga', texto_potencia_gerador()),
            ('10 · Se o gerador não pegar',
             'Se o motor do gerador não pegar na partida, espere um pouco entre as tentativas e confira o nível de óleo, o diesel nos '
             'tanques e a tensão do banco de baterias que alimenta a partida do gerador. Não ligue o gerador com a válvula de fundo da '
             'água salgada fechada: o rotor da bomba trabalha a seco e se danifica.'),
            ('11 · Desligar: nunca com carga nem com o cais junto',
             'Em parada normal, nunca desligue o gerador com carga ligada: retire as cargas no quadro elétrico e deixe-o esfriar sem '
             'carga antes de pressionar PARADA. Só em alarme (sem água no escapamento ou temperatura alta) desligue na hora, mesmo com '
             'carga. Ao passar para a energia do cais, retire as cargas e desligue o gerador antes: nunca deixe as duas fontes ligadas '
             'ao mesmo tempo. Anote o horímetro do gerador no diário ao fim do uso.'),
            ('12 · Distribuição de cargas',
             'O gerador entrega 9 kW a 60 Hz, com carga normal até 8,1 kW; acima disso é aviso. Antes de ligar uma carga, veja no '
             'painel ou no app a potência já em uso. Ligue as cargas no quadro elétrico uma de cada vez, esperando a tensão e a '
             'frequência estabilizarem entre elas, e deixe a climatização por último, porque ela pesa muito na carga. Cargas com motor '
             'ou compressor, como bombas e a própria climatização, puxam mais corrente na partida do que depois de funcionando; cargas '
             'de aquecimento elétrico, se houver, também pesam muito e não devem se somar à climatização. Se a carga passar de 8,1 kW, '
             'retire cargas no quadro, uma de cada vez.'),
            ('13 · Sobrecarga: o que fazer',
             'O aviso de carga do gerador de 9 kW começa acima de 8,1 kW; a sobrecarga derruba a tensão e a frequência e pode desarmar '
             'o disjuntor ou parar o motor. Retire cargas no quadro elétrico, uma de cada vez, começando pelas dispensáveis (desligue a '
             'climatização se a carga continuar alta) e acompanhe o painel até a carga voltar para abaixo de 8,1 kW. Se o disjuntor '
             'desarmou, retire as cargas do quadro antes de rearmar e só então religue as cargas uma a uma, com intervalo, sem somar as '
             'maiores de uma vez; não rearme o disjuntor com as cargas ainda ligadas. Se o gerador parou por sobrecarga, retire todas '
             'as cargas antes de religá-lo e espere a tensão e a frequência estabilizarem. Registre no diário a hora e a carga que '
             'causou o aviso.'),
            ('14 · Desligou sozinho ou perdeu rotação',
             'O gerador desliga sozinho quando uma proteção atua (pressão de óleo baixa ou temperatura alta) ou quando falta '
             'combustível ou água de refrigeração; o painel costuma indicar o motivo. Retire todas as cargas no quadro elétrico antes '
             'de qualquer tentativa de religar; se ele só perdeu rotação e continua ligado, veja se estabiliza sem carga. Anote a '
             'mensagem ou o código do painel e a hora, antes de limpar o alarme, e confira o nível de óleo e do líquido de '
             'arrefecimento, a válvula de fundo aberta, o filtro de água salgada limpo e o diesel nos tanques. Corrigida a causa, '
             'religue sem carga, espere a tensão e a frequência estabilizarem e volte as cargas uma a uma; se parar de novo, ou se o '
             'alarme de temperatura ou de pressão de óleo voltar, não religue: chame o técnico de bordo. Nunca abra a tampa do '
             'arrefecimento com o gerador quente. Registre no diário a hora, a mensagem do painel e as cargas que estavam ligadas.'),
            ('15 · Tensão ou frequência fora da faixa',
             'A frequência nominal do gerador é 60 Hz, com o motor a 1.800 rpm: quando a rotação cai, a frequência cai junto. Tensão e '
             'frequência instáveis costumam vir de sobrecarga ou de falha de combustível. Retire as cargas no quadro e veja a tensão e '
             'a frequência com o gerador sem carga; a frequência deve ficar em 60 Hz e a tensão no valor da placa do gerador. Se '
             'estiver normal sem carga e cair ao ligar uma carga, a causa é sobrecarga ou partida de carga pesada: retire cargas e '
             'religue uma a uma. Se continuar fora da faixa sem carga, não ligue no gerador carregadores nem equipamentos sensíveis, '
             'pois tensão ou frequência fora da faixa pode danificar esses aparelhos. Observe se a rotação oscila ou o motor falha, e '
             'confira o diesel nos tanques e, se houver filtro separador do gerador, a água acumulada nele. Não mexa por conta própria '
             'em ajuste de rotação, regulador ou tensão: a regulagem é do técnico de bordo. Se estabilizar, volte as cargas uma a uma e '
             'acompanhe o painel. Registre no diário a hora, os valores lidos de tensão e frequência e as cargas ligadas.'),
            ('16 · Óleo: nível, troca e alarme',
             'Confira o nível de óleo com o gerador parado, antes de ligar: com o gerador parado há alguns minutos e o barco nivelado, '
             'retire a vareta, limpe, encaixe de novo e leia entre as marcas de mínimo e máximo, completando só até a marca de máximo '
             'com o óleo que o manual do fabricante especifica. Procure óleo no compartimento em volta do gerador: pingos indicam '
             'vazamento. A troca de óleo e filtros vence aos 12 meses ou ao chegar a 1.300 h no horímetro, o que vier antes; acompanhe '
             'o horímetro do gerador no painel e na telemetria e combine a troca com o técnico de bordo antes do prazo vencer. Alarme '
             'de baixa pressão de óleo: desligue o gerador, confira o nível com ele parado e, se estiver correto e o alarme voltar, não '
             'religue. Depois da troca ou da complementação, confira o nível e procure vazamento com o gerador ligado e depois de '
             'parado.'),
            ('17 · Rotor (impeller): inspeção e troca',
             'O rotor da bomba de água salgada garante a refrigeração do gerador: sem água no escapamento, desligue na hora. A agenda '
             'prevê inspeção a cada 12 meses e troca quando estiver gasto, com o técnico de bordo. Para inspecionar: desligue o gerador '
             'e o painel dele, para não haver partida acidental, feche a válvula de fundo da água salgada do gerador, abra a tampa da '
             'bomba, retire o rotor e procure palhetas gastas, trincadas, achatadas ou faltando. Se faltar pedaço, procure no circuito '
             'de água antes de religar; na dúvida, chame o técnico de bordo. Encaixe o rotor girando-o no sentido de giro da bomba, '
             'para as palhetas se dobrarem do jeito certo, e lubrifique como o manual do fabricante indica. Feche a tampa com junta em '
             'bom estado, abra a válvula de fundo e confira que não há vazamento, ligue o gerador e confirme a água saindo pelo '
             'escapamento. Registre a inspeção ou a troca no diário e confira se há rotor sobressalente a bordo.'),
            ('18 · Ventilação do compartimento',
             'O gerador precisa de ar para queimar o combustível e para não esquentar o compartimento. Antes de ligar, deixe a '
             'ventilação do compartimento ligada por alguns minutos; se o compartimento ficou fechado por muito tempo, abra o acesso e '
             'deixe o ar renovar antes da partida. Com cheiro de combustível no compartimento, ventile bem e procure a origem antes de '
             'dar a partida. Mantenha as entradas e saídas de ar livres, sem pano, caixa nem outro objeto encostado nas grades, e '
             'confira a saída do escapamento do gerador sem obstrução. Os gases do escapamento são tóxicos: nunca deixe o gerador '
             'ligado com a saída obstruída ou com gases entrando nas cabines.'),
        ],
    },
    'g_seakeeper': {
        'titulo': ARQ['g_seakeeper'], 'pasta': 'manuais', 'equip': equip_de('estabilizador'),
        'secoes': [
            ('1 · Energia', 'O estabilizador é alimentado pelo banco de 12 V. Para acelerar o volante, mantenha o banco carregado, com o carregador ligado ao gerador ou ao cais. Com tensão baixa no 12 V, o display avisa e o volante não acelera.'),
            ('2 · Ligar antes de sair', 'Ligue pelo display com antecedência, com o banco de 12 V carregado (carregador ligado ao gerador ou ao cais). O volante estabiliza a partir de cerca de %s %% da rotação de operação; o display mostra a rotação e indica quando a estabilização está disponível. Espere a indicação antes de sair.' % br(_eq('estabilizador')['nominal']['pct_estabiliza'])),
            ('3 · Estabilizar', 'O botão de estabilização liga e desliga o efeito sem parar o volante. Em manobra de marina, deixe a estabilização desligada se o display recomendar.'),
            ('4 · Desligar ao atracar', 'Desligue pelo display. O volante continua girando por muito tempo depois de desligado; mantenha o banco de 12 V ligado até o display indicar que parou.'),
            ('5 · Segurança', 'Nunca abra tampas nem faça manutenção com o volante girando. Confira no display que a rotação está em zero antes de qualquer serviço.'),
            # Mensagens do display e o que fazer, sem código numérico (§8.2 ponto 1: código inventado de modelo real é vedado, §2.10).
            ('6 · Alarmes', 'Mensagens do display e o que fazer: tensão baixa no 12 V (ligue o carregador ao gerador ou ao cais); arrefecimento do estabilizador (confira a bomba e a válvula de fundo); temperatura alta (desligue e chame o técnico); volante abaixo de %s %% (sem estabilização até o volante acelerar). O display mostra a mensagem e o código: anote no diário com a hora.' % br(LIMITES['seakeeper_volante_pct']['aviso']['abaixo'])),
            ('7 · Manutenção na agenda', 'Anodo do trocador de calor: a cada 6 meses. Revisão anual pelo técnico de bordo.'),
            ('8 · Faixas', texto_faixas_volante()),
            ('9 · Tempo de aceleração do volante',
             'O volante leva algum tempo para chegar à rotação de trabalho; quem indica a hora de sair é o display, não um tempo '
             'fixo. Ligue o estabilizador pelo display com antecedência, com o carregador ligado ao gerador ou ao cais e o banco de '
             '12 V na faixa normal, de 12,2 a 14,7 V, e acompanhe no display a rotação do volante subindo. A estabilização só fica '
             'disponível a partir de cerca de 85 % da rotação de operação: espere a indicação do display antes de sair. Se o volante '
             'não acelerar ou o display avisar tensão baixa, confira o banco de 12 V e o carregador.'),
            ('10 · Ativar e desativar a estabilização',
             'O botão de estabilização liga e desliga o efeito sem parar o volante, que segue girando; ative só quando o display '
             'indicar que a estabilização está disponível. Em manobra de marina, desative a estabilização se o display recomendar: '
             'o efeito volta quando for ativado de novo. O botão de estabilização não para o volante; para isso, desligue o '
             'estabilizador pelo display.'),
            ('11 · Desligar e esperar o volante parar',
             'O volante continua girando por muito tempo depois de desligado: quem diz que ele parou é o display, não o relógio. '
             'Ao atracar, desligue o estabilizador pelo display e mantenha o banco de 12 V ligado enquanto o volante gira, sem '
             'cortar a energia antes da hora. Considere o equipamento parado só quando o display indicar a rotação em zero; só '
             'então desligue a energia do estabilizador ou faça qualquer serviço.'),
            ('12 · Alarme de tensão baixa no banco de 12 V',
             'O estabilizador é alimentado pelo banco de 12 V, normal de 12,2 a 14,7 V; com tensão baixa, o display avisa e o '
             'volante não acelera. Leia a tensão no painel ou na telemetria: abaixo de 12,2 V é aviso e abaixo de 11,8 V é crítico. '
             'Ligue o carregador de bordo ao gerador ou ao cais para repor o banco e confira os bornes limpos e apertados. Se a '
             'tensão não subir com o carregador ligado, mantenha o estabilizador desligado e chame o técnico de bordo.'),
            ('13 · Alarme de arrefecimento ou temperatura alta',
             'Duas mensagens do display tratam da refrigeração do estabilizador: arrefecimento, que pede conferir a bomba e a '
             'válvula de fundo, e temperatura alta, que pede desligar e chamar o técnico. Na mensagem de arrefecimento, confira a '
             'válvula de fundo do estabilizador aberta e a bomba funcionando; se a mensagem continuar, trate como temperatura alta. '
             'Na mensagem de temperatura alta, desligue o estabilizador pelo display, mantenha o banco de 12 V ligado até o volante '
             'parar e chame o técnico de bordo; não religue antes de achar a causa.'),
            ('14 · Volante abaixo de 85 %',
             'O estabilizador só atua com o volante a partir de cerca de 85 % da rotação de operação; abaixo disso, o aviso indica '
             'que ainda não há estabilização. Se o estabilizador acabou de ser ligado, espere: o volante ainda está acelerando. Se '
             'o volante já estava pronto e a rotação caiu, confira o banco de 12 V e o carregador; se não voltar a acelerar, '
             'desligue o estabilizador pelo display e chame o técnico de bordo.'),
            ('15 · Manutenção: volante parado antes do serviço',
             'O anodo do trocador de calor vence a cada 6 meses; a revisão anual é feita pelo técnico de bordo. Combine os dois com '
             'antecedência. Antes de qualquer serviço, desligue o estabilizador e espere o display indicar a rotação em zero, '
             'mantendo o banco de 12 V ligado até o volante parar. Depois do serviço, ligue o estabilizador e confira no display '
             'que não há mensagem de alarme.'),
        ],
    },
    'g_clima': {
        'titulo': ARQ['g_clima'], 'pasta': 'manuais', 'equip': equip_de('climatizacao'),
        'secoes': [
            ('1 · Ligar', 'Confira a válvula de fundo aberta e o filtro de água salgada limpo. Com energia AC no quadro elétrico, ligue a bomba de água salgada no painel e depois o controle da cabine.'),
            ('2 · Modos e temperatura', 'No controle de cada ambiente escolha frio, calor ou ventilação e ajuste a temperatura desejada. A unidade de 16.000 BTU/h atende o salão e as duas de 12.000 BTU/h, as cabines; ligue uma de cada vez para não sobrecarregar o quadro.'),
            ('3 · Alarme de fluxo', 'Alarme de fluxo ou de alta pressão quase sempre é falta de água salgada: filtro sujo, válvula de fundo fechada ou bomba desligada. Desligue a unidade, limpe o filtro e religue.'),
            ('4 · Fluxo de ar fraco', 'Fluxo de ar fraco na cabine: limpe o filtro de ar da unidade daquela cabine. Se continuar, registre no diário e chame a marina.'),
            ('5 · Desligar', 'Desligue pelo controle das cabines e depois a bomba de água salgada. Ao deixar o barco, feche a válvula de fundo se a climatização não for usada.'),
            ('6 · Manutenção na agenda', 'Filtro de água salgada: limpeza mensal. Revisão anual pela marina.'),
            ('7 · Como funciona: circulação de água salgada',
             'As três unidades Webasto trocam calor com a água do mar: a bomba de água salgada puxa a água pela válvula de '
             'fundo, ela passa pelo filtro e pelas unidades e sai pelo casco. Confira esse fluxo pela descarga no casco, que '
             'deve sair firme e contínua; jato fraco ou intermitente indica pouca água chegando à unidade. Sem esse fluxo, a '
             'unidade para por proteção; não insista em religar antes de resolver a causa do fluxo.'),
            ('8 · Ligar: a ordem completa',
             'A climatização só recebe comando depois que a energia AC está estável (gerador ligado com tensão estável ou '
             'cabo de cais conectado) e a água salgada circula; seguir essa ordem evita alarme de fluxo e sobrecarga no '
             'quadro elétrico. Confira a válvula de fundo aberta e a tampa do filtro de água salgada bem fechada, ligue a '
             'bomba de água salgada no painel e espere o jato contínuo na descarga do casco. Feche portas e escotilhas do '
             'ambiente para o ar climatizado não escapar, ligue o controle do salão ou de uma cabine, escolha o modo e '
             'ajuste a temperatura e a velocidade do ventilador. Espere a unidade partir e estabilizar antes de ligar a '
             'unidade seguinte; não ligue o controle de nenhuma unidade com a bomba de água salgada desligada. Com o '
             'gerador, a climatização entra por último, depois das outras cargas.'),
            ('9 · Trocar de modo: frio, calor ou ventilação',
             'Em frio a unidade resfria, em calor aquece e em ventilação só circula o ar, sem esfriar nem aquecer e '
             'gastando bem menos energia. Ao trocar de modo pelo controle do ambiente, espere a unidade responder: o '
             'compressor pode levar alguns minutos para partir de novo. Confira no controle se o modo escolhido ficou '
             'ativo e se o ar de saída mudou.'),
            ('10 · Ajustar a temperatura e o ventilador',
             'A temperatura ajustada é a meta da cabine, não a do ar que sai da unidade; metas muito distantes da '
             'temperatura ambiente fazem a unidade trabalhar sem parar. No controle da cabine, escolha a meta perto do '
             'conforto desejado e a velocidade do ventilador: mais alta para esfriar mais rápido, mais baixa para dormir '
             'com menos ruído. Espere alguns minutos antes de ajustar de novo, pois o ambiente demora a responder; fechar '
             'cortinas e escotilhas ajuda a unidade a manter a meta com menos esforço. Cada ambiente tem o próprio '
             'controle: ajuste só o da unidade que atende aquela cabine ou o salão.'),
            ('11 · Climatização no gerador ou no cabo de cais',
             'A unidade de 16.000 BTU/h do salão e as duas de 12.000 BTU/h das cabines pesam na energia AC, seja o gerador '
             'de 9 kW ou o cabo de cais. Ligue as unidades sempre depois das outras cargas do quadro elétrico, uma de cada '
             'vez: a partida do compressor pode causar queda de tensão e desarmar o disjuntor, tanto no gerador quanto no '
             'cais. Acompanhe a carga no painel do gerador: o aviso dispara acima de 8,1 kW, e com a climatização ligada o '
             'normal fica entre 5,5 e 6,5 kW. Com a carga acima do aviso, retire cargas no quadro elétrico, uma de cada '
             'vez, até voltar ao normal.'),
            ('12 · Alarme de fluxo: o que verificar',
             'O alarme indica que a água salgada não passa pela unidade com a vazão necessária, e a unidade se protege '
             'parando; a causa quase sempre está no filtro, na válvula de fundo ou na bomba, não no aparelho. Desligue o '
             'controle da unidade em alarme para ela não trabalhar sem água, confira a bomba ligada no painel e a válvula '
             'de fundo aberta e olhe a descarga no casco: jato fraco, intermitente ou ausente confirma a falta de fluxo. '
             'Não force novas partidas com o alarme ativo: a unidade só volta a trabalhar com a água circulando. Se o '
             'alarme voltar depois de limpar o filtro, desligue, registre no diário a unidade e a hora e chame a marina.'),
            ('13 · Limpar o filtro de água salgada',
             'O filtro retém algas, lodo e cracas antes da bomba e das unidades; a agenda prevê a limpeza mensal, a cargo '
             'da marina, mas o alarme de fluxo antes do prazo também pede essa limpeza. Desligue os controles de todas as '
             'unidades, espere o ventilador parar, desligue a bomba de água salgada e só então feche a válvula de fundo '
             'antes de abrir qualquer tampa. Abra a tampa do filtro, retire a tela e lave em água doce, tirando lodo, '
             'algas e cracas; confira a tela sem furos nem deformação e o anel de vedação da tampa, e troque o que estiver '
             'danificado. Recoloque a tela, feche a tampa com firmeza, abra a válvula de fundo e confira que a tampa não '
             'pinga; ligue a bomba, confirme o jato contínuo na descarga do casco e só então ligue os controles. Nunca '
             'abra o filtro com a válvula de fundo aberta: a água do mar sai pela tampa. Registre a limpeza do filtro no '
             'diário.'),
            ('14 · O ar liga, mas a cabine não esfria',
             'Cabine quente com a unidade ligada tem poucas causas comuns: modo ou meta errados, ar bloqueado, falta de '
             'água salgada ou energia fraca; confira na ordem mais simples até a mais trabalhosa. No controle, confirme o '
             'modo frio e a meta abaixo da temperatura atual da cabine, feche escotilhas e portas do ambiente e veja se o '
             'ventilador não está em velocidade baixa. Limpe o filtro de ar da unidade e libere as grades de entrada e de '
             'saída do ar; confirme o jato firme na descarga do casco e, se estiver fraco, siga o procedimento do alarme '
             'de fluxo. Confira no painel se a energia AC está estável e se o disjuntor da unidade está ligado; havendo '
             'gelo ou muita condensação na unidade, passe para ventilação até derreter e revise o filtro de ar. Não abra '
             'a unidade nem mexa no circuito de refrigeração: isso é serviço da marina. Persistindo a falha, registre no '
             'diário a cabine, a hora e o que foi conferido, e chame a marina.'),
            ('15 · Limpar o filtro de ar da unidade',
             'O filtro de ar fica na entrada de cada unidade e junta poeira, fiapos e pelos; entupido, deixa sair pouco '
             'ar, a cabine esfria mal e a serpentina pode formar gelo. Desligue o controle da unidade daquela cabine, '
             'abra o acesso ao filtro (grade ou painel de acesso) e puxe o filtro; aspire a poeira ou lave em água doce '
             'com sabão neutro e deixe secar por completo antes de recolocar. Recoloque o filtro e a grade, ligue o '
             'controle e compare o fluxo de ar na saída. Nunca ligue a unidade sem o filtro de ar: a poeira vai para a '
             'serpentina. Persistindo o fluxo fraco, registre no diário a cabine e a hora e chame a marina.'),
            ('16 · Preparar a climatização para deixar o barco parado',
             'Desligue na ordem inversa da partida: primeiro as unidades, depois a bomba de água salgada; com o barco '
             'parado por vários dias, feche a válvula de fundo para não deixar o circuito aberto ao mar. Se for deixar o '
             'barco fechado, rode as unidades só em ventilação por alguns minutos para secar a umidade interna antes de '
             'desligar cada cabine e o salão. Espere o ventilador parar e só então desligue a bomba de água salgada no '
             'painel; a bomba não pode puxar sem água. Com a bomba desligada, feche a válvula de fundo se a climatização '
             'não for usada nos próximos dias e confira a tampa do filtro de água salgada bem fechada. Registre no diário '
             'qualquer alarme ou comportamento estranho durante o uso.'),
        ],
    },
    'g_eletronicos': {
        'titulo': ARQ['g_eletronicos'], 'pasta': 'manuais', 'equip': equip_de('eletronicos', 'audio', 'vhf'), 'seg': {'1', '5'},
        'secoes': [
            ('1 · Plotter: homem ao mar', 'Ao ver alguém cair na água, acione a função MOB do plotter: a posição fica marcada e o plotter mostra o rumo de volta. Siga o protocolo de emergência (homem ao mar).'),
            ('2 · Piloto automático', 'Deixe o piloto automático em espera (standby) antes de manobrar na marina e diante de qualquer risco a bordo. Engate só em área livre, com a rota conferida no plotter.'),
            ('3 · Alarme de âncora', 'Ao fundear, ative o alarme de âncora no plotter e defina o raio conforme a corrente lançada. O contador de corrente mostra os metros lançados no controle do guincho.'),
            ('4 · Rádio VHF: escuta', 'Mantenha o canal 16 em escuta permanente no rádio fixo. A dupla escuta acompanha o canal 16 e um canal de trabalho ao mesmo tempo. Deixe o rádio portátil carregado e pronto para uso.'),
            ('5 · Rádio VHF: DSC', TXT_DSC),
            ('6 · Áudio Fusion: Bluetooth', 'Para parear o celular: escolha a fonte Bluetooth no controle Fusion, deixe o aparelho visível e selecione o Fusion na lista de Bluetooth do celular. O volume é ajustado por zona.'),
            ('7 · Atualizações', 'Cartas e software dos plotters, do radar e do áudio: atualização anual, conforme a agenda de manutenção.'),
            ('8 · Sonda', texto_sonda()),
            ('9 · Plotter: gestos e barra de menu',
             'O plotter é operado por toque na tela, com gestos para mover e dar zoom na carta, e por uma barra de menu fixa na parte de baixo '
             'da tela. Na barra de menu: um ícone marca um waypoint na posição atual, outro abre a navegação até um ponto (Go To, Route To ou '
             'Auto Guidance), e outro volta à tela inicial ou abre as opções da tela aberta. Para travar a tela e evitar toques por engano, use '
             'a opção de travar no menu; um ícone de cadeado aparece para destravar.'),
            ('10 · Plotter: atalhos fixados',
             'A categoria de favoritos reúne os recursos usados com frequência, como uma carta ou um medidor, para abrir em um só toque a '
             'partir da tela inicial; os atalhos fixados podem ser reorganizados ou removidos a qualquer momento. Um plotter que já vem com '
             'atalhos definidos pelo estaleiro nessa categoria não permite editá-los.'),
            ('11 · Plotter: páginas combinadas e SmartMode',
             'O plotter permite montar telas próprias: uma página combinada junta funções em janelas fixas na mesma tela, e um layout do tipo '
             'SmartMode agrupa telas pensadas para uma atividade, como cruzeiro ou atracação. Numa estação com mais de um display, o nome e o '
             'símbolo do layout SmartMode aparecem em todos os displays; o resto da personalização vale só para o display em uso.'),
            ('12 · Plotter: ActiveCaptain',
             'O ActiveCaptain é o aplicativo que liga o celular ao plotter para baixar ou comprar cartas, atualizar o software, transferir '
             'waypoints e rotas entre os dois, e planejar a viagem. As informações enviadas por outros usuários na comunidade ActiveCaptain '
             'não têm precisão garantida pelo fabricante.'),
            ('13 · Plotter: ActiveCaptain por Wi-Fi',
             'A ligação por Wi-Fi entre o celular e o plotter é o que permite ao ActiveCaptain transferir cartas, software e dados do usuário. '
             'No plotter, ative a rede Wi-Fi do ActiveCaptain e defina um nome e uma senha para ela; no celular, instale o aplicativo '
             'ActiveCaptain e aproxime-o a até 32 m do plotter para conectar pela rede Wi-Fi criada. Formatar o cartão de memória do '
             'ActiveCaptain apaga os dados salvos nele; copie waypoints e rotas para a memória interna do plotter antes de formatar.'),
            ('14 · Plotter: notificações por Bluetooth',
             'Com o Bluetooth do celular pareado ao plotter pelo ActiveCaptain, chamadas e mensagens do celular aparecem em um aviso rápido na '
             'tela do plotter; aproxime os dois aparelhos a até 10 m para parear. Não leia nem responda notificações enquanto estiver no '
             'comando da embarcação.'),
            ('15 · Plotter: tipos de carta e vistas 3D',
             'O plotter mostra a carta de navegação padrão, uma carta de pesca com destaque para o relevo do fundo, e vistas em três dimensões '
             '(3D), de cima e por detrás do barco ou submersa, com alvos da sonda em esferas coloridas. A carta de pesca, as vistas 3D e o '
             'sombreamento do relevo só aparecem em áreas cobertas por cartas premium.'),
            ('16 · Plotter: camadas da carta',
             'O menu de camadas da carta liga e desliga grupos de informação, como fotos de satélite, pontos de serviço em terra, sinalizações '
             'náuticas e os dados de outras embarcações; algumas camadas só funcionam com cartas premium ou com um acessório conectado, como '
             'um receptor de AIS. Nele também se ajusta a linha de rumo e a trilha do próprio barco, e se mostra ou esconde waypoints, limites '
             'e trilhas salvos.'),
            ('17 · Plotter: zoom e medir distância',
             'O zoom da carta é feito com dois dedos na tela: pince para afastar e espalhe para aproximar. Para medir, toque num ponto e '
             'escolha a ferramenta de medir; um alfinete marca a posição atual e a distância e o ângulo até o cursor aparecem no canto da '
             'tela, e um novo ponto de referência pode ser escolhido para medir de novo.'),
            ('18 · Plotter: informações de um local',
             'Ao tocar num ponto ou objeto da carta, o plotter deixa criar um waypoint ali ou abrir mais informações do local, como maré, '
             'corrente, dados astronômicos, notas da carta ou serviços próximos.'),
            ('19 · Plotter: detalhes de uma sinalização',
             'Marcas de navegação, luzes e obstruções indicadas na carta podem ser tocadas para abrir o nome e os detalhes de cada uma, também numa vista em 3D.'),
            ('20 · Plotter: marcar um waypoint',
             'Um waypoint grava uma posição para visitar depois: pode ser a posição atual do barco, um ponto escolhido direto na carta, ou um '
             'ponto definido por coordenada, ou por distância e direção a partir de uma referência.'),
            ('21 · Plotter: editar e apagar waypoint',
             'Um waypoint salvo pode ter o nome, o símbolo, a posição, a profundidade ou o comentário alterados, e pode ser apagado, um por '
             'vez ou todos de uma vez, quando não for mais necessário.'),
            ('22 · Plotter: Go To, Route To ou Auto Guidance',
             'O plotter chega a um destino de três formas: em linha reta direto ao ponto (Go To), por uma linha reta com curvas marcadas à mão '
             'para desviar de obstáculos (Route To), ou por um caminho já calculado pelo próprio plotter, desviando de terra e de obstáculos '
             'conhecidos (Auto Guidance, disponível só com cartas premium compatíveis, em algumas áreas). Para o piloto automático seguir o '
             'caminho sozinho, a rota precisa ser de Auto Guidance.'),
            ('23 · Plotter: ir direto e parar a navegação',
             'Depois de escolher um destino na carta ou pela busca, o plotter traça uma linha direta até ele; uma linha fina no meio dela '
             'mostra o rumo corrigido, se o barco saiu da rota. A navegação pode ser interrompida a qualquer momento, pela opção de parar a '
             'navegação. A linha direta pode passar sobre terra ou água rasa: confira visualmente antes de seguir.'),
            ('24 · Plotter: rota com curvas',
             'Uma rota junta vários pontos de curva entre a partida e o destino, para desviar de obstáculos no caminho; pode ser criada já '
             'para navegar, sem salvar, ou salva para usar depois e editar mais tarde. Uma rota aceita até 250 curvas.'),
            ('25 · Plotter: seguir por Auto Guidance',
             'O Auto Guidance calcula um caminho sugerido até o destino a partir dos dados da carta, como profundidade e obstáculos '
             'conhecidos; revise o caminho antes de seguir. Um trecho laranja indica cautela, perto dos limites configurados; um trecho '
             'vermelho listrado indica um trecho possivelmente inseguro; um trecho cinza indica que o plotter não conseguiu calcular aquele '
             'trecho com segurança, e é preciso escolher outro caminho ali. As linhas do Auto Guidance são uma referência geral, não uma '
             'garantia de água livre: confira sempre os sinais de navegação e as condições da água antes de seguir.'),
            ('26 · Plotter: símbolos de alvo AIS',
             'Cada embarcação rastreada pelo AIS aparece na carta como um triângulo apontando para o rumo em que se move, e muda de símbolo '
             'conforme o estado do alvo: selecionado, ativado (maior, com linha de rumo), ou com a transmissão perdida (um X verde, ou '
             'vermelho se o alvo já estava marcado como alvo perigoso). Um alvo perigoso pisca com aviso sonoro e visual; depois de '
             'confirmado, fica um triângulo vermelho fixo com a linha de rumo.'),
            ('27 · Plotter: acompanhar um alvo AIS',
             'Um alvo AIS pode ser ativado para acompanhar o rumo e a velocidade dele na carta; a aproximação mais próxima prevista entre as '
             'duas embarcações e o tempo até ela aparecem junto ao alvo ativado. Pode ser desativado quando não for mais preciso acompanhar.'),
            ('28 · Plotter: alarme de zona de segurança (AIS)',
             'O alarme de zona de segurança avisa quando uma embarcação rastreada por AIS entra num raio definido ao redor do barco, ou está '
             'prevista para entrar dentro de um tempo escolhido; com um radar na mesma rede, os alvos de radar também podem entrar nessa '
             'zona. É um apoio à atenção da tripulação, que pode não avisar a tempo em toda situação, e precisa do som do plotter ligado.'),
            ('29 · Plotter: sinalização náutica por AIS',
             'Além das marcas e luzes comuns da carta, o plotter mostra sinalizações transmitidas por AIS, com símbolos próprios para o tipo real (ou '
             'sintético) e para o tipo virtual; aparecem só quando o plotter está ligado a um rádio AIS compatível. Toque no símbolo para ver '
             'o nome e mais informações.'),
            ('30 · Áudio Fusion: fonte',
             'A fonte é o que o Fusion toca: rádio, Bluetooth, USB ou entrada auxiliar, conforme as que estiverem disponíveis no barco. Baixe '
             'o volume antes de trocar de fonte, porque cada uma pode tocar mais alto que a anterior, e confirme no visor qual ficou ativa '
             'antes de subir o volume de novo.'),
            ('31 · Áudio Fusion: volume por zona',
             'O Fusion toca em duas zonas de som, cada uma com o volume próprio; ajuste a zona em que você está sem mexer na outra. Mantenha '
             'o volume baixo o bastante para ouvir o rádio VHF e os alarmes do barco.'),
            ('32 · Áudio Fusion: reconectar Bluetooth',
             'Depois do primeiro pareamento, o celular conecta ao Fusion com poucos toques: escolha a fonte Bluetooth no Fusion e toque nele '
             'na lista de aparelhos pareados do celular. Só um celular transmite o som por vez; com mais de um celular por perto, desconecte '
             'ou pause os outros.'),
            ('33 · Áudio Fusion: silenciar',
             'O mudo corta o som do Fusion sem trocar a fonte nem mexer no volume, e sem desligar o aparelho; acione de novo para voltar ao '
             'mesmo nível. Para silenciar só uma zona, baixe o volume dela ao mínimo em vez de usar o mudo.'),
            ('34 · Áudio Fusion: problema no Bluetooth',
             'Falha de Bluetooth no Fusion costuma vir de distância, obstáculo, outro aparelho conectado ou um pareamento antigo. Aproxime o '
             'celular e tire o que houver de metal ou anteparo entre os dois; desligue e ligue o Bluetooth do celular e escolha de novo a '
             'fonte Bluetooth no Fusion; se persistir, apague o Fusion da lista de aparelhos do celular e pareie de novo, com o Fusion '
             'visível. Se nenhum celular conectar, desligue e ligue o Fusion pelo controle; se mesmo assim persistir, chame o técnico.'),
            ('35 · Áudio Fusion: sem som',
             'Com o Fusion ligado e sem som, as causas mais comuns são o mudo ativo, o volume da zona em zero, a fonte errada ou o volume '
             'baixo no celular conectado; confira nessa ordem antes de desconfiar do aparelho. Sem som em nenhuma fonte nem zona, com o mudo '
             'desativado e o visor aceso, o problema pode estar no amplificador, na fiação ou nas caixas: chame o técnico.'),
            ('36 · Áudio Fusion: problema na fonte',
             'Cada fonte do Fusion falha de um jeito: o rádio chia por sinal fraco ou pela antena; o USB não toca por mau contato ou por '
             'formato de arquivo; a entrada auxiliar fica baixa quando o volume do aparelho de origem está baixo. Som falhando ao ligar '
             'cargas grandes, como bombas ou guincho, pode ser a tensão do banco que alimenta o Fusion: chame o técnico.'),
            ('37 · Sonda: ganho e sensibilidade',
             'O ganho (ou sensibilidade) da sonda controla a intensidade dos ecos na tela: baixo demais perde o fundo e os peixes, alto demais '
             'cobre a tela de ruído. Aumente até o fundo aparecer com uma linha nítida e contínua, reduza se a tela ficar cheia de pontos de '
             'ruído, e reajuste ao mudar de profundidade, velocidade ou tipo de fundo.'),
            ('38 · Sonda: faixa de profundidade',
             'A faixa de profundidade define até onde a tela da sonda mostra a coluna de água; no modo automático ela segue sozinha, e no '
             'modo manual precisa ser ajustada para o fundo aparecer na parte de baixo da tela. Em mudanças rápidas de profundidade, '
             'acompanhe e corrija a faixa manualmente; volte ao automático em navegação com profundidade variável e sem tempo de ajustar.'),
            ('39 · Sonda: leitura do fundo',
             'A espessura e a intensidade da linha de fundo na sonda indicam, em termos gerais, se o fundo é mais duro (como rocha ou areia '
             'compacta) ou mais mole (como lama ou vegetação): uma linha fina e clara tende a fundo mole, e uma linha grossa e forte, com uma '
             'segunda marca abaixo (eco duplo), tende a fundo duro. É uma indicação geral, não uma confirmação exata do tipo de fundo: '
             'compare com a carta náutica.'),
            ('40 · Sonda: ruído e interferência',
             'Bolhas, turbulência perto do transdutor e interferência elétrica de outros equipamentos podem sujar a imagem da sonda com '
             'ruído, sobretudo em alta velocidade. Reduza a velocidade e o ganho até o ruído de turbulência diminuir, sem perder o fundo, e '
             'ative o filtro de interferência, se o equipamento tiver essa função. Ruído constante e elétrico nem sempre se resolve só pelo '
             'painel: registre no diário e peça revisão do transdutor e das conexões ao técnico de bordo.'),
            ('41 · Sonda: alarme de água rasa',
             'O alarme de água rasa avisa quando a profundidade fica menor que um limite definido por você, com tempo de reagir antes que o '
             'casco toque o fundo. Defina o limite com margem acima da profundidade que o casco exige, ative o som ou o aviso na tela, e '
             'reavalie o limite ao trocar de área de navegação ou de condição de maré.'),
            ('42 · Sonda: alarme de fundeio',
             'O alarme de fundeio marca a posição do barco no momento em que a âncora é lançada e avisa se o barco se deslocar além de um '
             'raio definido, indicando que a âncora pode estar garrando. Defina o raio considerando o comprimento de corrente ou cabo '
             'lançado, confirme que o alarme está ativo antes de deixar o posto de comando sem vigilância e, se ele disparar, volte ao posto '
             'de comando e confira a posição e a profundidade antes do próximo passo.'),
        ],
    },
    'g_vhf': {
        'titulo': ARQ['g_eletronicos'], 'pasta': 'manuais', 'equip': equip_de('vhf'), 'seg': {'33', '34'},
        'secoes': [
            ('1 · Ligar e desligar', 'O IC-M510 liga e desliga pelo botão giratório CH/ENT/PWR, mantido por cerca de 1 segundo. Ao ligar, com o MMSI cadastrado ele aparece na tela; sem MMSI cadastrado, o rádio dá três bips e mostra a mensagem para cadastrar o MMSI — um cadastro de uma vez, que depois um revendedor ou distribuidor Icom pode alterar —, e fica sem chamada DSC. Depois de ligar, ajuste o volume em VOL e o squelch em SQL e confira o canal em que o rádio está. Confira o conector do microfone bem rosqueado, no sentido horário, para manter a vedação contra água.'),
            ('2 · Volume e squelch', 'O controle VOL regula o volume e o SQL define o squelch, o nível mínimo de sinal para liberar o áudio. Ajuste o squelch no ponto em que o chiado de fundo acaba de sumir: squelch alto corta sinais fracos e squelch baixo deixa o chiado constante. Som abafado mesmo com o volume bom pode ser água na grade do alto-falante: use o AquaQuake, sem o alto-falante externo ligado.'),
            ('3 · Trocar de canal', 'No IC-M510, troque o canal pressionando as teclas de subir e descer, ou girando CH/ENT, até chegar ao canal desejado; o número e o nome do canal aparecem por um instante na tela, com 3 ou 4 dígitos (01A ou 1001) conforme o ajuste de Channel Display. No microfone, as mesmas teclas de subir e descer também trocam de canal: em Menu > Settings > Radio > FAV on MIC, ON faz o microfone passar só pelos favoritos, e OFF, por todos.'),
            ('4 · Canal 16 e canal de chamada', 'A tecla 16/C leva direto ao canal 16, usado no primeiro contato com outra estação; mantida por 1 segundo, leva ao canal de chamada do grupo em uso (ícone CALL), reservado a conversas de lazer e que pode ser trocado em Menu > Settings > Radio > Call Channel. Para voltar ao canal anterior, use a tecla de software CH/WX (ou CH). Fora de outro canal, mantenha o rádio no canal 16; operando em outro canal, use a dupla ou a tripla escuta para conferi-lo.'),
            ('5 · Transmitir: uso do PTT', 'No IC-M510, para falar segure a tecla PTT do microfone, espere cerca de 1 segundo e fale em voz normal, a 5 ou 10 cm da boca; para ouvir, solte. O rádio corta a transmissão depois de 5 minutos seguidos (o Time-out Timer). Nunca transmita sem a antena conectada.'),
            ('6 · Potência alta e baixa', 'O IC-M510 transmite com 25 W (potência alta) ou 1 W (potência baixa); a troca é feita pela tecla H/L do microfone ou pela tecla de software HI/LO, e o ícone 25W ou 1W mostra o nível em uso. Alguns canais só aceitam baixa potência ou só recebem, por norma — não é defeito do rádio.'),
            ('7 · Grupo de canais', 'Os canais vêm em grupos pré-programados — USA, INT (internacional), CAN (Canadá), e DSC ou ATIS conforme a versão —, escolhidos em Menu > Settings > Radio > Channel Group; o grupo em uso define a lista de canais, os favoritos e o canal de chamada, e aparece como ícone (USA, INT ou CAN) na tela de operação.'),
            ('8 · Canais favoritos', 'Os canais favoritos (ícone de estrela) são os que a varredura e o microfone podem percorrer — a varredura exige pelo menos 2 marcados para iniciar; cada grupo de canais tem os seus, e alguns já vêm marcados de fábrica conforme a versão do rádio. Marque ou desmarque pela tecla de software FAV★, ou use Menu > Settings > Radio > Favorite CH para marcar todos, limpar todos ou voltar ao padrão; em FAV on MIC, ON faz as teclas de subir e descer do microfone passarem só pelos favoritos.'),
            ('9 · Varredura (scan)', 'A varredura (scan) percorre os canais favoritos — marque pelo menos 2 para ela iniciar — e é escolhida em Menu > Settings > Radio > Scan Type: Normal Scan não confere o canal 16 a menos que ele seja favorito, e Priority Scan (SCAN 16 na tela) o confere de tempos em tempos. Com sinal recebido, a varredura pausa até ele sumir ou retoma em 5 segundos, conforme o Scan Timer; na prioritária, sinal em outro canal faz a varredura virar dupla escuta até o sinal acabar; a versão holandesa (NLD) do rádio não tem a varredura.'),
            ('10 · Dupla e tripla escuta', 'A dupla escuta (DUAL 16) confere o canal 16 de tempos em tempos enquanto o rádio opera em outro canal; a tripla (TRI 16) confere o canal 16 e o canal de chamada, ligadas em Menu > Settings > Radio > Dual/Tri-Watch. Com sinal no canal 16, soa um bip, o 16 pisca na tela e a escuta pausa nele até o sinal acabar. Fora de outro canal, mantenha o canal 16 em escuta; a versão holandesa (NLD) do rádio não tem a dupla nem a tripla escuta.'),
            ('11 · DSC: o que é e o que precisa', 'No IC-M510, a chamada seletiva digital (DSC) chama uma estação, um grupo ou todos os navios pelo canal 70; a conversa segue depois num canal de voz combinado. O rádio só faz chamadas DSC com o MMSI cadastrado — sem ele, as teclas de software da DSC não aparecem. Antes de chamar, ajuste CH 70 SQL Level em Menu > Settings > DSC (de 1 a 10, ou Open); pressione Other DSC para montar a chamada (individual, em grupo, a todos os navios, teste ou, em algumas versões, pedido de posição), escolhendo o tipo em Msg Type, o destino em Address e o canal de voz em Channel. A chamada só chega a estações dentro do alcance do rádio.'),
            ('12 · DSC: cadastrar IDs', 'O rádio guarda até 75 IDs individuais e 25 IDs de grupo, com nome de até 10 caracteres, para chamar sem digitar o número toda vez; no ID individual o primeiro dígito vai de 1 a 9, e no ID de grupo é fixo em 0. Cadastre, edite ou apague pelas teclas Add, Edit e Delete em Menu > Settings > DSC > Individual ID (ou Group ID).'),
            ('13 · Posição e hora sem GPS', 'Sem dados de GPS, digite a posição e a hora UTC em Menu > Settings > DSC > Position Input; a entrada manual só funciona sem GPS válido e dura 23,5 horas ou até desligar o rádio, e depois de 4 horas sem atualização o símbolo de interrogação pisca no lugar da posição e da hora. Para a tela mostrar a hora local, informe a diferença para UTC em Menu > Settings > Configuration > UTC Offset (de -14:00 a +14:00).'),
            ('14 · DSC: chamada individual', 'A chamada individual vai só para a estação escolhida: pressione Other DSC, em Msg Type escolha Individual, em Address a estação (ou Manual Input para digitar o ID) e em Channel o canal de voz; se o canal 70 estiver ocupado, o rádio espera liberar para enviar. Ao pressionar Call aparecem Transmitting Individual Call e depois Waiting for ACK. Com a resposta Able to comply, o alarme soa — pressione Alarm OFF — e o rádio vai ao canal escolhido; com Unable to comply, pressione Alarm OFF, Close Window, STBY e OK.'),
            ('15 · DSC: receber uma chamada', 'Ao receber uma chamada DSC individual, em grupo ou a todos os navios, o rádio soa um alarme e mostra o tipo (Received INDV Call, Received Group Call ou Received All Ship Call); pressione Alarm OFF para silenciá-lo. Chamada individual com Individual ACK em Manual: pressione Able para confirmar na hora, ou Accept para ver os dados e escolher ACK Able, ACK Unable ou ACK New CH. Chamada em grupo ou a todos os navios: por padrão o rádio vai ao canal combinado após 10 segundos (use Pause e Resume para suspender e retomar a contagem); pressione Ignore para descartar (fica no DSC Log) ou Hold para manter em espera.'),
            ('16 · DSC: chamada em grupo ou a todos', 'A chamada em grupo atinge só o grupo escolhido; a chamada a todos os navios (All Ships) avisa todas as embarcações com DSC ao alcance. Pressione Other DSC, em Msg Type escolha Group ou All Ships, o destino em Address (ou a categoria Routine, para recado comum, nas chamadas a todos os navios) e o canal de voz em Channel; pressione Call e, se o canal 70 estiver ocupado, o rádio espera liberar. Ao terminar uma chamada a todos os navios, pressione STBY e depois OK.'),
            ('17 · DSC: chamada de teste', 'A chamada de teste confere se a DSC funciona com outra estação, em geral sem conversa: pressione Other DSC, em Msg Type escolha Test e o destino em Address, e pressione Call; se o canal 70 estiver ocupado, o rádio espera liberar. A confirmação soa um alarme (Alarm OFF e Close Window) e fica no DSC Log. Sem outra estação, o autoteste (Self Check Test, em Menu > Settings > DSC) compara dentro do rádio o sinal DSC enviado com o recebido, e mostra OK quando conferem. Nos canais exclusivos da DSC e nos de chamada de segurança, a chamada de teste deve ser evitada; se for inevitável, diga que é teste.'),
            ('18 · DSC: pedir a posição de outra estação', 'O pedido de posição pergunta onde está uma estação, com a resposta chegando por DSC; é função da versão dos EUA do rádio e depende da pré-configuração do revendedor. Pressione Other DSC, em Msg Type escolha Position (ou Polling, para só saber se a estação está ao alcance) e o destino em Address; pressione Call e, com a resposta (Waiting for ACK), pressione Alarm OFF e Close Window para ler a posição.'),
            ('19 · DSC: responder a um pedido de posição', 'Ao receber um pedido de posição (Received POS Request), o rádio soa um alarme; com Position ACK em Manual, pressione Able ou Unable para responder na hora, ou Accept e depois ACK Able (com posição e hora) ou ACK Unable (sem elas) e Call para enviar. A resposta com posição depende de o rádio ter posição válida — GPS ou digitada; em Position ACK Auto, o rádio responde sozinho.'),
            ('20 · DSC: resposta automática (Auto ACK)', 'Por padrão o rádio confirma sozinho as chamadas DSC recebidas (Auto ACK); em Menu > Settings > DSC > Auto ACK, ajuste Individual ACK (Auto Able, Auto Unable ou Manual), Position ACK, Polling ACK e Test ACK. Para a troca de canal, CH Auto Switch define se o rádio vai sozinho ao canal da chamada depois de 10 segundos (Accept after 10 sec), ignora a chamada nesse prazo (Ignore after 10 sec) ou espera a decisão a cada chamada (Manual).'),
            ('21 · DSC: registro de chamadas (DSC Log)', 'O DSC Log guarda as chamadas DSC recebidas (até 50 comuns) e as enviadas (até 30); o ícone de mensagem não lida pisca na tela quando chega uma chamada nova. Abra pela tecla de software DSC Log (ou Menu > DSC Log), escolha Received Call Log ou Transmitted Call Log, e selecione um registro para ver os detalhes (INFO), apagá-lo (Delete) ou salvar o MMSI como ID individual ou de grupo.'),
            ('22 · DSC: alarmes (Alarm Status)', 'O menu Alarm Status (Menu > Settings > DSC > Alarm Status) liga ou desliga o alarme de cada tipo de chamada DSC recebida — Safety, Routine, Warning, Discrete e outros. O Warning soa se nenhum MMSI foi cadastrado, se a posição digitada à mão passa de 23,5 horas sem atualização, se a posição não chega em 10 minutos depois de ligar o rádio, ou deixa de ser atualizada por 10 minutos ou por 4 horas; o Discrete soa quando chega uma chamada de prioridade menor enquanto o rádio recebe outra, de prioridade maior. Pressione Alarm OFF para silenciar um alarme de chamada.'),
            ('23 · Luz da tela e modo noite', 'A luz de fundo da tela e das teclas tem 7 níveis, mais OFF (só no modo Dia), ajustados pela tecla de software Backlight ou em Menu > Settings > Configuration > Backlight. O modo Dia mostra cores; o modo Noite, para operação noturna, usa preto e vermelho.'),
            ('24 · Bip das teclas', 'O Key Beep (Menu > Settings > Configuration > Key Beep) define se as teclas dão um bip a cada toque: ON mantém o bip e OFF deixa a operação silenciosa. Se nenhuma tecla faz bip, a causa mais provável é a opção estar em OFF.'),
            ('25 · Travar as teclas do microfone', 'A trava do microfone (Microphone Lock) bloqueia todas as teclas, menos o PTT, para evitar troca de canal ou de função por toque acidental; liga e desliga pelo mesmo procedimento: com o rádio desligado, segure H/L e, sem soltar, segure PWR por 1 segundo para ligar. Com a trava ativa, até a tecla 16/C do microfone fica travada — destrave antes de precisar dela.'),
            ('26 · Redução de ruído', 'O Noise Cancel (Menu > Settings > Configuration > Noise Cancel) reduz o ruído aleatório do sinal recebido (RX, em OFF, Low, Mid ou High) e do transmitido (TX, ON ou OFF), com ajuste próprio para cada lado.'),
            ('27 · Sem posição ou hora na tela', 'NO POSITION e NO TIME aparecem sem antena GPS conectada nem entrada manual; o símbolo de interrogação piscando indica GPS inválido ou 4 horas desde a última entrada manual, e a última posição válida fica retida por 23,5 horas. Confira a antena GPS e os fios NMEA, e veja em Menu > GPS Info a posição, a data, a hora, a velocidade (SOG) e o rumo (COG) em uso; sem GPS, digite posição e hora UTC em Menu > Settings > DSC > Position Input, e ligue o SBAS em Menu > Settings > Configuration > GPS para melhorar a precisão, se a versão tiver a opção.'),
            ('28 · Ligação por NMEA (GPS, AIS, plotter)', "O rádio recebe posição e AIS por NMEA 0183 (Menu > Settings > NMEA > NMEA 0183, 4800 bps para GPS externo e 38400 bps para AIS externo) ou por NMEA 2000 (escolhendo o dispositivo da rede, Auto ou Not used); com os dois conectados, vale o NMEA 2000, e um GPS externo tem prioridade sobre o GPS interno do rádio. Para o rádio entregar as chamadas DSC recebidas a um plotter compatível, ajuste DSC Data Output (All Stations, Stations List ou OFF) em Menu > Settings > DSC."),
            ('29 · AIS: de onde vêm os alvos', 'No IC-M510, o rádio mostra alvos AIS vindos de um receptor interno (só em algumas versões) ou de um AIS externo ligado por NMEA 0183 (sentença VDM, a 38400 bps) ou NMEA 2000; havendo os dois, o externo tem prioridade. O AIS mostra nome, posição, rumo e velocidade de outras embarcações para ajudar a evitar colisão — Class A é exigido dos navios sujeitos à convenção SOLAS, e muitas embarcações não obrigadas, inclusive de lazer, escolhem o Class B.'),
            ('30 · AIS: ver os alvos', 'A tela Plotter mostra o barco no centro e os alvos AIS em volta, com escala (Range) de 0,125 a 36 milhas náuticas; Target Details traz nome, classe, posição, rumo, velocidade, CPA e TCPA do alvo. As listas Target e Friends ordenam por distância, e a Danger pode ordenar por CPA ou TCPA (tecla Sort); a Target List mostra até 200 alvos e as listas atualizam a cada 5 segundos. Para marcar um alvo como amigo (até 100), use Friend; para limitar o que o plotter mostra, ajuste Target Display em Menu > Settings > AIS.'),
            ('31 · AIS: alarme de colisão', 'O rádio soa um alarme quando um alvo AIS fica mais próximo que o CPA e chega em menos tempo que o TCPA ajustados em Menu > Settings > AIS > CPA/TCPA (CPA de 0,01 a 6,00 NM, TCPA de 1 a 60 minutos); alvos abaixo dos dois valores entram na Danger List. Deixe Alarm em ON para Approach (alvo se aproximando) e Lost (alvo de risco que sumiu), e Audible Alarm em ON para o alarme soar; para o próprio transponder não virar alvo de risco, cadastre o ID em Menu > Settings > AIS > ID Blocking (até 10).'),
            ('32 · Alarme de fundeio (Anchor Watch)', 'O Anchor Watch soa um alarme se o barco fundeado derivar além do raio definido em Menu > Settings > Navigation > Anchor watch (Range, de 0,01 a 6,00 NM); o plotter do rádio mostra o círculo vermelho no ponto de partida e o círculo tracejado no raio do alarme, e a tela avisa Exceeded anchor radius! se o barco passar dele. Precisa de GPS válido no rádio — posição digitada à mão não acompanha o movimento do barco.'),
            ('33 · Rádio não liga ou não responde', 'No IC-M510, rádio que não liga costuma ter conexão de alimentação ruim ou fusível queimado: confira o cabo na fonte de energia e o fusível do cabo (10 A e 250 V no manual), e troque por outro da mesma especificação só depois de corrigir a causa. O rádio usa 13,8 V CC (faixa de 11,7 a 15,9 V CC), negativo à massa — nunca ligue a um banco de 24 V. Rádio ligado mas sem responder: desligue e ligue de novo; se continuar sem funcionar, procure o revendedor Icom.'),
            ('34 · Pouco alcance ou sem comunicação', 'Sensibilidade baixa, com só sinais fortes audíveis, ou comunicação que não se estabelece, indica antena com defeito ou conector do cabo coaxial em curto ou cortado. Antes, descarte squelch alto demais, abaixando-o até o ponto limiar. Com o rádio desligado, inspecione a antena e o conector; havendo defeito, providencie o conserto e reconecte o cabo ao conector de antena do rádio. Não transmita enquanto a antena estiver desconectada.'),
            ('35 · Água no alto-falante e limpeza', 'Água na grade do alto-falante abafa o som; segure a tecla de software AquaQuake (ou Menu > AquaQuake) para o cone vibrar e expulsar a água, por no máximo 10 segundos mesmo que você continue segurando. Depois de água salgada, lave o rádio e o microfone com água doce e seque antes de operar. O conector de alimentação e os fios NMEA e de áudio externo, na traseira, pedem cuidado: eles não têm a mesma proteção contra água. Na limpeza comum, use pano macio, sem benzina, álcool ou outros solventes fortes.'),
            ('36 · Portátil: carregar', 'O IC-M37 (portátil) roda na bateria própria, sem usar a energia do barco, e por isso precisa sair carregado: desligue e seque o rádio, com atenção aos contatos, antes de encaixá-lo no carregador do próprio aparelho. Espere o indicador mostrar carga completa antes de retirá-lo, e confirme o nível de bateria no visor; carregue antes de cada saída, mesmo que o rádio tenha ficado desligado.'),
            ('37 · Portátil: trocar de canal', 'O portátil fica em um canal por vez, mostrado no visor; mude pelas teclas de canal e volte ao canal 16 pelo atalho do próprio rádio. Ouça o canal por alguns segundos antes de transmitir e, para conversar, combine antes um canal de trabalho — o canal 16 é só para a chamada inicial e a escuta.'),
            ('38 · Portátil: potência alta e baixa', 'O portátil transmite em potência alta ou baixa (alguns modelos têm um nível intermediário): a alta alcança mais longe e gasta mais bateria, e a baixa serve para distâncias curtas, poupa bateria e atrapalha menos outros usuários. Use potência baixa em conversa curta, como entre barcos próximos ou com a marina ao lado; use a alta quando a outra estação estiver longe, ou quando ela não responder em potência baixa, e volte para a baixa depois, para poupar bateria. O alcance do portátil é bem menor que o do rádio fixo, por ter antena menor e mais baixa; alguns canais só transmitem em baixa potência por norma.'),
            ('39 · Portátil: flutuação e água', 'Alguns rádios portáteis marítimos flutuam e resistem à água, mas só com a bateria e as tampas bem encaixadas — confirme no manual do fabricante o que o seu modelo suporta. Use a cordinha de pulso nas manobras de borda; se cair na água, recupere sem se arriscar nem se debruçar na borda, porque mesmo um modelo que flutua pode ser levado pelo vento e pela correnteza. Se o manual indicar resistência à água, depois de água salgada enxágue com água doce, com as tampas fechadas, e seque com pano macio. Se entrou água: desligue, seque por fora, tire a bateria e deixe secar em lugar ventilado. O rádio só deve ser ligado ou recarregado com o interior seco; se funcionar mal, chame o técnico.'),
            ('40 · Portátil: pronto antes de sair', 'O portátil só ajuda se estiver pronto: confira a carga no visor, a antena bem presa e sem trincas, e as tampas e vedações no lugar; ajuste volume e silenciador para ouvir sem chiado forte. Faça um teste curto com o rádio fixo, no mesmo canal de trabalho livre e em potência baixa, falando em um e ouvindo no outro — nunca no canal 16; terminado o teste, volte os dois ao canal 16: o fixo em escuta permanente e o portátil carregado e seco.'),
            ('41 · Portátil: silenciador e volume', 'O silenciador (squelch) corta o chiado quando não há sinal: alto demais, corta também vozes fracas; baixo demais, deixa o chiado constante — ajuste-o junto com o volume. Com ninguém falando no canal, ajuste o volume para um nível confortável, sem encostar o rádio no ouvido; reduza o silenciador até ouvir o chiado de fundo e aumente aos poucos até ele cessar. Se perder vozes distantes, reduza um pouco o silenciador. Chiado que volta toda hora: afaste o rádio de fontes de ruído, como carregadores e telas, e teste de novo. Sem som nenhum: confira a bateria, o volume, o canal e se o rádio não está em varredura ou dupla escuta.'),
        ],
    },
    'g_eletrico': {
        'titulo': ARQ['g_eletrico'], 'pasta': 'manuais', 'equip': equip_de('eletrico'),
        'secoes': [
            ('1 · Bancos', 'Oito baterias AGM de 12 V em três bancos: serviço de 24 V (4), partida dos motores de 24 V (2) e banco de 12 V (2 em paralelo), que alimenta a eletrônica de 12 V e o estabilizador. O carregador de bordo repõe os três bancos.'),
            ('2 · Faixas', texto_faixas_baterias()),
            ('3 · Verificação', 'Confira as tensões no painel e na telemetria antes de sair. Bornes limpos e apertados; verificação dos bancos e das conexões a cada 6 meses, conforme a agenda de manutenção.'),
            ('4 · Separação dos bancos de baterias',
             'A separação em três bancos protege a partida dos motores: o consumo da casa de bordo não descarrega o banco de partida, e o '
             'estabilizador e a eletrônica de 12 V têm banco próprio. As oito baterias são Victron AGM Super Cycle, de 12 V e 230 Ah cada: '
             'quatro formam o banco de serviço de 24 V, duas o banco de partida de 24 V e duas, em paralelo, o banco de 12 V. O carregador '
             'de bordo repõe os três bancos quando ligado ao gerador ou ao cais, e cada banco tem a própria faixa de tensão no painel e na '
             'telemetria. Os três bancos têm limites diferentes: não compare a tensão de 24 V com a de 12 V. Confira os três antes de sair: '
             'um banco fora da faixa não é compensado pelos outros.'),
            ('5 · Ler a tensão no painel e na telemetria',
             'O painel e a telemetria mostram a tensão de cada banco: serviço de 24 V, partida de 24 V e banco de 12 V. A faixa normal é de '
             '24,4 a 29,4 V nos bancos de 24 V e de 12,2 a 14,7 V no banco de 12 V. A tensão é o sinal mais rápido do estado das baterias, mas '
             'muda com as cargas ligadas e com o carregador: com ele ligado, ela sobe em relação ao repouso; sem ele, cai com o uso das cargas. '
             'Para avaliar a carga das baterias, leia com o carregador desligado há algum tempo e com poucas cargas ligadas, e leia de novo '
             'depois de alguns minutos para ver se a tensão sobe, se mantém ou cai. Leitura isolada diz pouco: observe a tendência, e anote no '
             'diário qualquer banco fora da faixa, com a tensão e a hora.'),
            ('6 · Tensão baixa no banco de baterias',
             'Aviso abaixo de 24,4 V nos bancos de 24 V e de 12,2 V no de 12 V; crítico abaixo de 23,6 V e de 11,8 V. Tensão baixa significa '
             'banco descarregado ou consumo acima do que o carregador repõe. Veja no painel qual banco está baixo (serviço de 24 V, partida de '
             '24 V ou 12 V) e desligue o que não for necessário nele; no banco de partida, evite partidas repetidas dos motores. Confirme o '
             'carregador de bordo ligado ao gerador ou ao cais e ligue o gerador, se preciso, para recarregar. Olhe os bornes do banco: limpos '
             'e sem cabo frouxo. Se achar corrosão ou folga, chame o técnico. Acompanhe a tensão subir no painel: depois de carregar, ela deve '
             'voltar à faixa normal. Se o banco não sobe, ou cai logo depois de desligar o carregador, chame o técnico: a bateria pode estar no '
             'fim da vida. Banco de partida baixo pode não dar partida nos motores: recarregue antes de sair. No nível crítico, evite novas '
             'descargas: cada descarga profunda reduz a vida das baterias AGM. Registre a tensão e a hora no diário.'),
            ('7 · Tensão alta no banco de baterias',
             'O aviso aparece acima de 29,4 V nos bancos de 24 V e acima de 14,7 V no de 12 V. Pode ser só o fim normal de uma carga forte ou '
             'falha de regulagem do carregador ou do alternador; o que diferencia é a persistência. Veja qual banco passou do limite e se o '
             'carregador de bordo ou os motores estão ligados, e espere alguns minutos com ele ligado: no fim da carga, a tensão deve baixar '
             'sozinha para a faixa normal. Se a tensão continuar acima do limite, desligue a alimentação AC do carregador de bordo e observe a '
             'queda; se o aviso só aparecer com os motores ligados, suspeite do alternador e anote o horário e o giro. Se precisou desligar o '
             'carregador, não o ligue de novo até o técnico conferir o ajuste dele para baterias AGM. Tensão acima do limite por muito tempo '
             'danifica as baterias AGM e pode passar do que os equipamentos de 12 V toleram. Bateria muito quente, estufada ou com cheiro '
             'forte: desligue o carregador, ventile o compartimento e chame o técnico. Registre no diário o banco, a tensão e a hora.'),
            ('8 · Carregar os bancos de baterias',
             'O carregador de bordo repõe os três bancos com energia AC do gerador ou do cais. Carregar com regularidade, sem esperar o aviso '
             'de tensão baixa, preserva as baterias AGM. Garanta energia AC no quadro (gerador ligado e estável ou cabo de cais conectado) e '
             'confirme o carregador de bordo ligado e sem indicação de falha. Acompanhe a tensão dos três bancos no painel: ela deve subir em '
             'relação ao repouso. Continue carregando até as tensões ficarem estáveis dentro da faixa normal. Depois de muito uso do '
             'estabilizador e da eletrônica, recarregue o banco de 12 V antes de ligar o estabilizador de novo. Sem energia AC do gerador ou do '
             'cais, o carregador de bordo não recarrega os bancos. Registre no diário se algum banco demorou mais que o normal para carregar.'),
            ('9 · Cuidados com as baterias AGM',
             'As baterias AGM Super Cycle são seladas e não precisam de água, mas sofrem com descarga profunda, carga mal regulada e bornes '
             'frouxos; poucos hábitos prolongam a vida do banco. Recarregue ao primeiro aviso de tensão baixa e evite chegar ao nível crítico, '
             'com o carregador de bordo no perfil para baterias AGM (peça ao técnico para conferir o ajuste). Olhe os bornes de vez em quando: '
             'limpos, secos e sem cabo frouxo; limpeza e aperto das conexões ficam com o técnico. Não abra as baterias nem complete água: elas '
             'são seladas. Troque as baterias de um mesmo banco em conjunto, sem misturar nova com velha, e mantenha o compartimento seco e '
             'ventilado, com as baterias bem presas contra o balanço. Evite deixar o barco parado por muito tempo sem carregador: o banco se '
             'descarrega sozinho. Só o técnico mexe nos cabos e bornes dos bancos, com as cargas e o carregador desligados.'),
            ('10 · Verificação semestral dos bancos e das conexões',
             'A agenda pede a verificação dos bancos e das conexões a cada 6 meses, pelo técnico. Antes de cada saída, vale a conferência '
             'rápida das tensões no painel e do aspecto dos bornes: confira as tensões dos três bancos e se estão dentro da faixa, e olhe os '
             'bornes (sem pó branco ou azulado de corrosão, sem cabo frouxo e sem sinais de aquecimento). Confira as baterias firmes nos '
             'suportes; caixa estufada, rachada ou com líquido pede o técnico antes de carregar. A cada 6 meses, peça ao técnico a verificação '
             'completa: aperto das conexões e tensão de cada bateria do banco. Confira que o jogo de fusíveis de 24 V de reposição está a '
             'bordo. Só o técnico aperta ou retira cabos dos bancos, com as cargas e o carregador desligados. Registre a verificação e as '
             'tensões no diário.'),
        ],
    },
    'g_dessalinizador': {
        'titulo': ARQ['g_dessalinizador'], 'pasta': 'manuais', 'equip': equip_de('dessalinizador'),
        'secoes': [
            ('1 · Ligar', 'Abra a válvula de fundo do dessalinizador e confira o pré-filtro limpo. Ligue pelo painel do dessalinizador, com o banco de serviço carregado; a pressão sobe sozinha.'),
            ('2 · Produção', 'Produção nominal: %s L/h. Descarte a água dos primeiros minutos depois de ligar e confira a salinidade no painel antes de mandar a água para o tanque.' % br(_eq('dessalinizador')['nominal']['lph'])),
            ('3 · Desligar e lavar', 'Desligue pelo painel: o ciclo termina com a lavagem com água doce. Feche a válvula de fundo se o barco for ficar parado.'),
            ('4 · Manutenção', 'Pré-filtros: troca conforme a agenda de manutenção. Barco parado por muito tempo: conservação da membrana pelo técnico de bordo.'),
            ('5 · Água para produzir',
             ('O dessalinizador faz água doce do mar por osmose reversa. Escolha água limpa para produzir, longe de marinas, de saídas de '
              'esgoto e de manchas de óleo ou combustível. Antes de ligar, confira a tensão do banco de serviço no painel, normal de %s a '
              '%s V. Nunca ligue com a válvula de fundo fechada: a bomba de alta pressão não pode trabalhar sem água. Depois da partida, '
              'observe mangueiras e conexões; qualquer pingo ou ruído de ar pede desligar e revisar antes de continuar.') % (
                br(LIMITES['bateria_0_tensao_v']['normal']['de']), br(LIMITES['bateria_0_tensao_v']['normal']['ate']))),
            ('6 · Tempo de produção e nível do tanque',
             ('Antes de começar, confira no app o nível do tanque de água doce; o aviso é abaixo de %s %%. Para estimar o tempo de '
              'produção, divida os litros que faltam no tanque de %s L pelos %s L/h produzidos. Ao completar o tanque, desligue pelo '
              'painel para o ciclo de lavagem rodar, sem cortar a energia. Registre no diário as horas de produção e o nível do tanque '
              'no início e no fim.') % (
                br(LIMITES['tanque_agua_pct']['aviso']['abaixo']), br(TANQUES['agua_l']), br(_eq('dessalinizador')['nominal']['lph']))),
            ('7 · Salinidade alta',
             'O painel mostra a salinidade da água produzida durante toda a produção, não só na partida. Leitura estável dentro do '
             'limite do fabricante é água boa; leitura alta ou subindo aponta problema na membrana, nas vedações ou na água captada: '
             'mantenha essa água no descarte, sem mandar para o tanque. Antes de suspeitar da membrana, confira se a água captada está '
             'limpa e se o pré-filtro está limpo; se a salinidade continuar alta, registre no diário e chame o técnico de bordo. Água '
             'com salinidade alta que chegou ao tanque: avise o técnico de bordo antes de usá-la.'),
            ('8 · Lavagem ao desligar',
             'Água do mar parada na membrana deixa sal e cria limo; por isso o desligamento sempre termina com a lavagem com água doce. '
             'Desligue pelo painel do dessalinizador, nunca pelo disjuntor, e não interrompa o ciclo nem corte a energia no meio da '
             'lavagem: a água do mar fica parada na membrana. Água com cloro danifica a membrana: confirme com o técnico de bordo a '
             'água usada na lavagem. Terminada a lavagem, observe mangueiras e conexões, sem pingos nem manchas de sal, e registre no '
             'diário as horas produzidas e o nível do tanque.'),
            ('9 · Produção abaixo do normal',
             ('A produção nominal é de %s L/h, mas cai com pré-filtro sujo, água fria, tensão baixa no banco de serviço (abaixo de %s V '
              'é aviso) ou ar nas mangueiras de captação. Confira a válvula de fundo totalmente aberta, o pré-filtro, a tensão no '
              'painel e bolhas na linha de captação antes de suspeitar da membrana; uma queda pequena com água do mar mais fria é '
              'normal. Não tente compensar a produção baixa mexendo na pressão do sistema. Se a produção continuar baixa com tudo '
              'conferido, registre no diário e chame o técnico de bordo.') % (
                br(_eq('dessalinizador')['nominal']['lph']), br(LIMITES['bateria_0_tensao_v']['aviso']['abaixo']))),
            ('10 · Troca dos pré-filtros',
             'Os pré-filtros protegem a bomba e a membrana da sujeira; elemento sujo derruba a produção e força o equipamento, e a '
             'troca vem antes do intervalo da agenda se a produção cair. Para trocar: desligue pelo painel, espere a lavagem terminar, '
             'feche a válvula de fundo e deixe o equipamento sem energia durante o serviço. Abra devagar o alojamento do pré-filtro, '
             'porque pode haver pressão residual; retire o elemento usado, limpe o alojamento e instale o elemento novo, sempre do '
             'mesmo tipo e do mesmo grau de filtragem do original, com o anel de vedação limpo e bem assentado. Use sempre elemento do '
             'mesmo tipo: um filtro mais fino ou mais grosso muda a vazão e a proteção da membrana. Feche o alojamento, abra a válvula '
             'de fundo, ligue pelo painel e procure vazamentos nos primeiros minutos; registre a troca no diário e reponha o elemento '
             'no estoque de sobressalentes.'),
            ('11 · Conservação da membrana',
             'A membrana não pode secar nem ficar parada com água do mar; por isso, para uma parada longa, a conservação é serviço do '
             'técnico de bordo, com o produto e o procedimento do fabricante. Antes da parada, termine o uso com o ciclo completo de '
             'lavagem com água doce e, com o equipamento parado, mantenha a válvula de fundo do dessalinizador fechada. Não use '
             'produto químico na membrana por conta própria: cada fabricante define o produto e o prazo. Registre no diário a data da '
             'conservação e quem a fez; para voltar a produzir, siga a orientação do técnico e descarte a água do início.'),
        ],
    },
    'g_porao': {
        'titulo': ARQ['g_porao'], 'pasta': 'manuais', 'equip': equip_de('porao'), 'seg': {'4', '6', '7', '8'},
        'secoes': [
            ('1 · Funcionamento', 'Duas bombas automáticas de 24 V, uma em BB e outra em BE, cada uma com sensor de nível. O painel mostra o nível do poço e conta os ciclos de cada bomba.'),
            ('2 · Faixas', texto_faixas_porao()),
            ('3 · Teste mensal', 'Uma vez por mês, acione cada bomba no manual, confira a saída pelo casco e o alarme do painel e registre o teste no diário.'),
            ('4 · Água entrando', TXT_ALAGAMENTO[0]),
            ('5 · Automático ou manual', 'No automático, o sensor de nível comanda a bomba; no manual, ela funciona por comando seu, sem depender do '
             'sensor. A posição de uso normal é o automático. Use o manual só para testar ou esgotar o poço: confirme a '
             'saída de água pelo casco e devolva ao automático depois. Bomba esquecida no manual descarrega as baterias e '
             'pode se danificar trabalhando a seco.'),
            ('6 · Alarme de nível alto', 'O aviso de nível no porão aparece acima de 5 cm; acima de 10 cm é crítico. Veja no painel qual poço passou '
             'do normal, BB ou BE, e se o nível está subindo, estável ou baixando. Acima de 10 cm, ou subindo mesmo com a '
             'bomba ligada, pare este roteiro e siga o protocolo de bordo. Confirme a bomba daquele lado ligada; se '
             'estiver parada, passe para o manual e confirme a saída de água pelo casco. Com o nível de volta ao normal, '
             'devolva a bomba ao automático, procure a origem da água (chuva, lavagem do convés, mangueiras e conexões) e '
             'registre no diário o poço, o nível máximo e a hora.'),
            ('7 · Bomba que não parte', 'A bomba não parte no automático, no manual ou nos dois. Nível no painel acima de 10 cm, ou subindo: pare '
             'este roteiro e siga o protocolo de bordo antes de continuar. Passe a bomba para o manual: se ela partir, o '
             'defeito está no sensor de nível ou no comando do automático; se zumbir sem girar, desligue-a na hora e só '
             'destrave com o disjuntor desligado. Sem partir no manual, confira o disjuntor ou o fusível da bomba e a '
             'tensão dos bancos de 24 V no painel — abaixo de 24,4 V pode faltar força. Com o disjuntor desligado, '
             'confira o conector e os fios, procurando corrosão ou fio solto, e registre o defeito no diário com a hora.'),
            ('8 · Bomba que não desliga', 'Ciclos demais ou bomba ligada sem intervalo têm duas causas: sensor de nível enganado (preso ou sujo) ou '
             'água chegando aos poucos ao poço. Leia no painel o nível dessa bomba e o contador de ciclos: ciclos demais '
             'em pouco tempo pedem atenção mesmo com o nível normal. Com o nível acima de 5 cm, trate como alarme de '
             'nível e busque a origem da água; se o nível subir mesmo com a bomba ligada, pare este roteiro e siga o '
             'protocolo de bordo. Com o nível normal e muitos ciclos, procure água entrando aos poucos (mangueiras, '
             'conexões, drenos e pingos) e, com a bomba desligada no disjuntor, limpe o sensor de nível — se for do tipo '
             'flutuador, confira se ele se move livremente. Registre no diário os ciclos e o nível; chame o técnico se o '
             'problema voltar.'),
            ('9 · Limpeza do sensor', 'Óleo, lodo e fiapos travam o sensor de nível e entopem a entrada da bomba, e aí ela não parte ou não para. '
             'Aproveite o teste mensal para olhar o poço e o sensor. Desligue a bomba no disjuntor antes de limpar, para '
             'ela não partir sozinha. Retire os detritos soltos do poço e limpe o sensor de nível; se for do tipo '
             'flutuador, mova-o com a mão — ele deve subir e descer livremente, sem prender em fios ou mangueiras. Limpe a entrada '
             'da bomba, sem forçar a peça, e confira cabos e conectores, sem corrosão nem isolamento rachado. Religue o '
             'disjuntor, teste a bomba no manual, devolva ao automático e registre a limpeza no diário.'),
        ],
    },
    'g_ancora': {
        'titulo': ARQ['g_ancora'], 'pasta': 'manuais', 'equip': equip_de('ancora'),
        'secoes': [
            ('1 · Lançar', 'Com o barco parado sobre o ponto escolhido, lance pelo controle do guincho e dê ré devagar até a âncora unhar. Lance de %s vezes a profundidade.' % de_a(LANCE_ANCORA_VEZES)),
            ('2 · Contador de corrente', 'O contador mostra os metros de corrente lançados no controle do guincho. Confira a marca antes de ativar o alarme de âncora no plotter.'),
            ('3 · Recolher e travar', 'Recolha devagar, com o motor aliviando a corrente. Com a âncora no lugar, trave a corrente e desligue o guincho no disjuntor.'),
            ('4 · Manutenção', 'Lave o guincho com água doce depois do uso e confira a corrente e o destorcedor uma vez por ano.'),
            ('5 · Calcular o lance',
             'Escolha um fundo de areia ou lama, com espaço de giro livre de outros barcos, e leia a profundidade na sonda antes de lançar. '
             'Calcule o lance, de %s vezes a profundidade contando a altura da proa, e confirme que cabe na corrente do barco, que tem %s m. '
             'Ligue o disjuntor do guincho, solte a trava e, com o barco parado sobre o ponto escolhido, lance pelo controle do guincho '
             'acompanhando os metros no contador. Perto do lance calculado, dê ré bem devagar para a âncora unhar e a corrente esticar, pare '
             'o guincho e trave a corrente. Ative o alarme de âncora no plotter e registre no diário a hora e a profundidade. Com vento forte, '
             'lance mais corrente; em fundo de pedra a âncora segura mal. Mantenha mãos, pés e cabos longe da corrente e do guincho em movimento.'
             % (de_a(LANCE_ANCORA_VEZES), br(_eq('ancora')['nominal']['corrente_m']))),
            ('6 · Conferir o contador',
             'O contador mostra, no controle do guincho, os metros de corrente lançados; a corrente do barco tem %s m. Com a âncora no rolete '
             'o contador deve marcar zero; se não marcar, chame o técnico antes de fundear. Ao lançar, leia os metros no controle e pare ao '
             'chegar ao lance calculado, de %s vezes a profundidade da sonda, e confirme a leitura final antes de ativar o alarme de âncora '
             'no plotter. Ao recolher, acompanhe a leitura baixando e reduza o ritmo quando a âncora se aproximar do rolete. Anote no diário '
             'os metros lançados junto com a profundidade.'
             % (br(_eq('ancora')['nominal']['corrente_m']), de_a(LANCE_ANCORA_VEZES))),
            ('7 · Recolher sem forçar',
             'O guincho recolhe a corrente, mas quem alivia o esforço é o motor, aproximando o barco da âncora; recolher devagar protege o '
             'guincho, a corrente e a proa. Ligue os motores em neutro e desative o alarme de âncora no plotter antes de começar a recolher. '
             'Ligue o disjuntor do guincho, deixe-o assumir a carga da corrente antes de abrir a trava, e recolha pelo controle em trechos '
             'curtos, aproximando o barco da âncora com o motor para a corrente ficar mole. Acompanhe o contador e a corrente entrando: ela '
             'deve subir sem arrastar o barco. Com a âncora solta do fundo, termine de recolher e lave a lama com água doce; com a âncora '
             'assentada no rolete, feche a trava da corrente e desligue o disjuntor do guincho. Não use o guincho para puxar o barco contra '
             'o vento ou a correnteza: o esforço pesado danifica o motor do guincho.'),
            ('8 · Travar e desligar o guincho',
             'A trava segura a carga da corrente no lugar do guincho, que não foi feito para sustentar o esforço do fundeio, e impede que a '
             'corrente corra sozinha com o barco no mar. Com a âncora unhada, pare o guincho, feche a trava da corrente e solte um pouco de '
             'corrente pelo guincho até a trava assumir a carga. Confira a trava bem fechada e firme na corrente, com a carga nela, e '
             'desligue o guincho no disjuntor para ninguém acioná-lo por engano. Para recolher, ligue o disjuntor, deixe o guincho assumir a '
             'carga antes de abrir a trava; com a âncora no rolete, feche a trava de novo e desligue o disjuntor antes de navegar. Nunca '
             'deixe o barco preso à âncora só pelo guincho, nem navegue com a trava aberta.'),
            ('9 · Âncora garrando',
             'Âncora que garra deixa o barco andar com o vento ou a correnteza mesmo fundeado; os sinais são o alarme de âncora do plotter, '
             'a posição saindo do raio e a corrente vibrando ou dando trancos. Confirme no plotter se a posição saiu do raio e para onde o '
             'barco está indo, chame a tripulação e ligue os motores em neutro para poder manobrar se precisar sair do local. Com espaço '
             'livre e corrente sobrando, aumente o lance e espere a âncora unhar de novo; se o barco continuar arrastando, recolha a âncora '
             'e refunde em outro ponto, com fundo melhor e mais espaço, e confira de novo o raio do alarme no plotter. Registre no diário a '
             'hora, o vento, a profundidade e o lance usado. Perto de pedras, de outros barcos ou da praia, não espere a âncora segurar: '
             'recolha e afaste-se com os motores.'),
            ('10 · Guincho sem força ou sem resposta',
             'Guincho que não responde costuma ter o disjuntor desligado, o controle com defeito, tensão baixa nos bancos, a trava fechada '
             'ou carga demais; confira nessa ordem antes de chamar o técnico. Confirme o disjuntor do guincho ligado; se tiver desarmado, '
             'rearme uma única vez. Confira a trava da corrente: fechada, ela segura a corrente e o guincho não recolhe; abra-a só com o '
             'guincho ligado e o barco aliviado pelo motor. Com o disjuntor desligado, olhe o cabo e o conector do controle: botão preso, '
             'cabo danificado ou conector úmido impedem o comando; depois religue e teste. Confira no painel se os bancos de baterias estão '
             'na faixa normal; tensão baixa deixa o guincho lento ou sem força. Se o guincho desligou por sobrecarga, deixe esfriar e alivie '
             'a carga aproximando o barco da âncora com o motor. Se nada resolver, registre no diário o sintoma e a hora e chame o técnico, '
             'sem forçar o guincho. Não rearme o disjuntor várias vezes: ele desarma para proteger o motor e a fiação.'),
            ('11 · Vistoria anual da corrente',
             'Sal e lama corroem o guincho e a corrente: desligue o disjuntor antes de qualquer serviço no guincho, na trava ou nos '
             'conectores, e lave tudo com água doce depois de cada uso, tirando lama e sal. Olhe o guincho e a trava, procurando ferrugem, '
             'folgas e parafusos soltos. Uma vez por ano, inspecione a corrente elo a elo (ferrugem em escamas, deformação ou desgaste pedem '
             'troca), confira o destorcedor e as manilhas, com os pinos firmes e travados, sem folga nem ferrugem, e confira os cabos e '
             'conectores elétricos do guincho, sem corrosão e bem fixos. Confira também se o contador de corrente marca de acordo com a '
             'corrente lançada. Registre a vistoria anual e as peças trocadas no diário.'),
        ],
    },
    'g_piloto': {
        'titulo': ARQ['g_piloto'], 'pasta': 'manuais', 'equip': equip_de('piloto'),
        'secoes': [
            ('1 · Engatar', 'Engate o piloto no controle do posto de comando, com o rumo conferido no plotter e área livre à frente.'),
            ('2 · Espera ao manobrar', 'Em manobra, na marina e diante de qualquer risco a bordo, deixe o piloto em espera (standby).'),
            ('3 · Assumir no timão', 'Para assumir, aperte espera e governe pelo timão. O piloto comanda a direção hidráulica por uma bomba própria.'),
            ('4 · Alarmes', 'Alarme de desvio de rumo ou da direção: assuma no timão, ponha em espera e confira o rumo no plotter. Registre no diário com a hora.'),
            ('5 · Modos do piloto', 'O piloto governa de um jeito diferente em cada modo: em espera (standby) o timão é seu e o piloto fica inativo, sem atuar no rumo; em automático (auto) ele mantém o rumo que a proa tinha ao engatar; em trilha (track) segue a rota ativa do plotter, se o plotter enviar a rota ao piloto; em vento (wind), nos pilotos que têm esse modo, mantém um ângulo fixo em relação ao vento, comum em veleiros e a confirmar com o técnico se existe neste barco. Troque de modo pelo controle do posto de comando e confira no visor o modo ativo. Em qualquer modo, o piloto não enxerga barcos, marcas de navegação nem águas rasas: a vigia continua sendo sua.'),
            ('6 · Engatar com segurança', 'Ao engatar, o piloto trava o rumo que a proa tem naquele instante: engate com o barco estável, apontado para onde você quer ir e com água livre à frente, nunca em curva nem com o leme muito virado. Confira o controle ligado e sem alarme nem mensagem, mantenha a proa no rumo desejado com velocidade e leme estáveis por alguns segundos, confira o rumo no plotter e a área à frente livre de barcos, marcas de navegação, redes de pesca e águas rasas, e engate pelo controle do posto de comando, com a mão perto do timão. Observe o barco logo depois: o rumo deve se manter; se ele guinar ou oscilar muito, volte à espera e assuma o timão, e mantenha a vigia conferindo o rumo de tempos em tempos.'),
            ('7 · Mudar o rumo em automático', 'Com o piloto engatado, mude o rumo pelas teclas de ajuste do controle, para bombordo ou boreste, em toques curtos e correções leves, sem pressa; para curvas fechadas ou para desviar de algo, assuma o timão em vez de ajustar, e não gire o timão com o piloto engatado. Antes de qualquer curva, olhe ao redor, avise a tripulação e veja no plotter o que há no novo rumo: raso, obstáculo, rede ou outro barco; espere o barco completar a curva antes de dar outro ajuste e confira o novo rumo no controle e no plotter.'),
            ('8 · Modo trilha (seguir a rota)', 'Em trilha (track), o piloto governa para seguir a rota ativa do plotter; depende de o plotter enviar os dados da rota ao piloto, e esse modo precisa ser confirmado com o técnico neste barco. Antes de engatar, ative a rota no plotter e confira o traçado inteiro: terra, rasos, redes e barcos fundeados fora do caminho. Engate com o barco no rumo do primeiro trecho e em água livre, escolha o modo trilha e confira se o piloto aceitou a rota, sem mensagem de erro, antes de tirar a mão do timão; em cada ponto da rota, fique pronto para confirmar a curva pelo controle, se ele pedir, ou para assumir o timão se o barco não virar. O piloto segue a linha da rota e não desvia de barcos nem de obstáculos, então a vigia continua sua; se o modo trilha não ligar, use automático e corrija o rumo à mão, e para sair da trilha, ponha em espera e assuma o timão.'),
            ('9 · Devolver o comando ao timão', 'Para devolver o governo ao timão, ponha o piloto em espera pelo controle; faça isso com folga, e não no último momento, para sentir o leme antes de precisar dele, e não force o timão com o piloto engatado. Segure o timão com firmeza antes de mexer no controle, pressione a tecla de espera (standby) no posto de comando, gire o timão um pouco para os dois lados e confirme que o barco responde normalmente, e avise a tripulação que o piloto está em espera. Se o piloto saiu sozinho do automático, mantenha o rumo no timão e leia a mensagem do controle antes de engatar de novo.'),
            ('10 · Piloto na marina e em manobra', 'O piloto não enxerga nada e foi feito para manter rumo em velocidade de viagem; em marina, canal estreito, fundeio e atracação, deixe-o em espera e governe pelo timão e pelas manetes, sem voltar ao automático. Na saída, mantenha-o em espera até passar o canal da marina e chegar à água livre, e só então engate, com a rota conferida no plotter e sem barcos, marcas de navegação ou águas rasas à frente. Na chegada, ponha o piloto em espera com folga, antes do canal de acesso ou da área de manobra; com barcos e píeres por perto, não confie no piloto, porque ele não desvia de nada.'),
            ('11 · Alarme de desvio de rumo', 'O alarme de desvio de rumo toca quando o barco se afasta do rumo ajustado além do limite programado no piloto; a causa pode ser mar, vento, corrente ou falha do piloto, então primeiro governe, depois investigue. Assuma o timão, ponha o piloto em espera pelo controle e silencie o alarme depois de ter o barco governado; compare o rumo que o barco faz no plotter com o que você queria seguir e procure a causa provável (mar de través, vento forte, corrente ou mudança de velocidade). Se foi o mar ou o vento, siga à mão ou reduza a velocidade e só engate de novo com o barco estável; se o alarme voltar sem causa visível, siga à mão e chame o técnico, e registre no diário a hora e o que estava acontecendo. Alarme repetido pode apontar problema no sensor de rumo, na bomba ou na energia: não insista em engatar.'),
            ('12 · Sensor de rumo', 'O piloto usa o sensor de rumo (uma bússola eletrônica) para saber para onde a proa aponta; se o rumo dele diverge muito do plotter ou da bússola, ou o alarme do sensor soa, não confie no piloto. Ponha o piloto em espera e governe pelo timão; compare o rumo do piloto com o da bússola magnética, se houver, lembrando que o rumo sobre o fundo do plotter difere da proa com corrente e vento. Diferença grande: procure o que desvia o sensor, como ímãs, ferramentas de ferro, caixas de som, celulares ou cabos de corrente forte perto dele, e confira a alimentação do piloto (disjuntor armado e tensão do banco que o alimenta, no app). Rumo ainda errado ou alarme persistente: não recalibre por conta própria e chame o técnico, e registre no diário a hora e o rumo mostrado por cada instrumento.'),
            ('13 · Alarme da bomba ou da direção', 'A bomba do piloto comanda a direção hidráulica; alarme de bomba ou de direção indica que o piloto talvez não consiga mover o leme, então assuma o timão antes de tudo. Assuma o timão, ponha o piloto em espera e gire o timão de leve para os dois lados para ver se o barco responde normalmente; com o timão normal, confira o disjuntor do piloto e a tensão do banco que o alimenta. Com o barco parado ou com outra pessoa no timão, procure vazamento de óleo na bomba e nas mangueiras da direção e olhe o nível do reservatório hidráulico; não complete o óleo da direção sem saber o tipo indicado pelo técnico ou pelo fabricante. Alarme de bomba que volta, ruído estranho ou odor de superaquecimento: mantenha o piloto em espera e chame o técnico, e registre no diário a hora e a mensagem do controle. Timão duro, folgado ou sem resposta: reduza a velocidade e siga o protocolo de bordo.'),
            ('14 · Quando o piloto não engata', 'O piloto recusa engatar ou sai do automático quando falta energia, dado de rumo ou comando da bomba, ou quando há alarme ativo; leia a mensagem do controle antes de tentar de novo. Mantenha o barco em marcha reta, assuma o timão e deixe o piloto em espera; confira a energia (disjuntor do piloto armado e tensão do banco que o alimenta, no app), com outra pessoa no timão se precisar sair do posto, e confira se o controle está ligado, com o visor aceso, lendo a mensagem: ela indica se o motivo é alarme, falta de dado ou falha de equipamento. Trate primeiro o alarme ativo, porque com alarme em curso o piloto pode se recusar a engatar, e tente engatar de novo em automático, com o barco estável e água livre à frente. Se continuar sem engatar ou soltar de novo, siga à mão, registre a mensagem e a hora no diário e chame o técnico; se o piloto soltar de repente, o barco pode guinar, então assuma o timão na hora.'),
            ('15 · Calibração', 'A calibração ajusta o sensor de rumo e a resposta do leme ao barco; é feita pelo técnico, em água aberta e livre de tráfego, seguindo o manual do fabricante. Chame o técnico se o rumo do piloto não bate com a bússola, se o barco serpenteia em automático, depois de reparo na direção, ou depois de instalar, perto do sensor de rumo, qualquer equipamento com ímã, ferro ou corrente forte; anote no diário os sintomas, a data e o rumo mostrado pelo piloto, pela bússola e pelo plotter. Enquanto espera o técnico, não mexa nos ajustes do piloto: ajuste errado piora o governo. Não recalibre navegando nem na marina: o procedimento pede condições controladas; combine o serviço para um dia de mar calmo e, depois dele, teste em água livre, engatando, mudando o rumo e voltando à espera.'),
        ],
    },
    'g_radar': {
        'titulo': ARQ['g_radar'], 'pasta': 'manuais', 'equip': equip_de('radar'),
        'secoes': [
            ('1 · Ligar e transmitir', 'Ligue o radar pelo plotter e espere o aquecimento; depois toque em transmitir. Na marina, deixe em espera.'),
            ('2 · Zona de guarda', 'Defina a zona de guarda em volta do barco: o plotter avisa quando um alvo entra nela.'),
            ('3 · Neblina e noite', 'Com neblina ou à noite, mantenha o radar transmitindo, reduza a velocidade e confira os alvos com o AIS no plotter.'),
            ('4 · Segurança', 'Não fique perto do domo com o radar transmitindo e não abra o domo com ele ligado.'),
            ('5 · Aquecimento',
             'Todo radar marítimo exige um tempo de aquecimento entre ligar e transmitir: o equipamento fica em espera (standby) até estar '
             'pronto, sem emitir sinal. Toque em transmitir (transmit) somente depois do aquecimento terminar. Radar de magnetron tem '
             'aquecimento mais longo que o de estado sólido (semicondutor); o tempo exato depende do fabricante. Na marina ou em trajetos '
             'curtos, mantenha o radar em espera e ligue a transmissão só ao navegar.'),
            ('6 · Ganho',
             'O ganho (gain) controla a intensidade dos ecos mostrados na tela do radar. Ganho baixo perde alvos fracos; ganho em excesso '
             'cobre a tela de ruído. No modo automático (auto gain) o próprio radar ajusta; no modo manual (manual gain), aumente o ganho '
             'até os alvos conhecidos aparecerem com nitidez e reduza aos poucos até o ruído de fundo (speckle) quase desaparecer da tela. '
             'Repita o ajuste quando o mar, a chuva ou a distância dos alvos mudar.'),
            ('7 · Alcance',
             'O alcance (range) define até que distância a tela do radar mostra ecos. Alcance curto detalha o entorno próximo; alcance '
             'longo mostra alvos e costa mais distantes, com menos detalhe. Os anéis de alcance (range rings) marcam distâncias fixas a '
             'partir do barco: em área de tráfego, prefira um alcance curto para distinguir alvos próximos entre si; em mar aberto, use um '
             'alcance maior para antecipar tráfego e costa à frente.'),
            ('8 · Interferência das ondas',
             'Ondas próximas ao barco geram ecos que poluem o centro da tela do radar. O ajuste de interferência do mar (sea clutter) '
             'reduz esse ruído sem apagar alvos reais. Aumente o ajuste até o ruído das ondas diminuir e pare de aumentar assim que alvos '
             'pequenos e próximos ainda estiverem visíveis. Clutter em excesso também apaga alvos reais próximos ao barco; ajuste com '
             'cautela e confira visualmente. Refaça o ajuste quando o estado do mar mudar.'),
            ('9 · Interferência da chuva',
             'Células de chuva aparecem no radar como manchas que podem esconder outros alvos. O ajuste de interferência de chuva (rain '
             'clutter ou FTC) reduz essas manchas na imagem. Aumente o ajuste até a mancha perder intensidade e confira se alvos sólidos '
             'dentro ou perto da área de chuva continuam visíveis. Reduzir demais a interferência de chuva pode esconder um alvo real '
             'dentro da célula de chuva. Volte o ajuste ao normal depois que a chuva passar.'),
            ('10 · Zona de guarda: forma e teste',
             'A zona de guarda é uma área demarcada ao redor do barco no radar, com o formato de anel completo ou de setor voltado para '
             'um lado e alcance mínimo e máximo ajustável. O equipamento soa um alarme quando um eco entra nela — útil para vigilância em '
             'fundeio ou com o piloto automático engatado. Teste a zona com um alvo conhecido antes de confiar nela sem vigilância visual. '
             'A zona de guarda não substitui a vigilância visual e por VHF; é um apoio, não garante detectar todo tipo de alvo.'),
            ('11 · Visibilidade reduzida: velocidade e alvos fracos',
             'Reduza a velocidade com visibilidade reduzida para ter tempo de reagir a um alvo detectado, e ajuste ganho e interferência '
             '(clutter) para a condição do momento, já que chuva e mar mudam a imagem. Acompanhe a tela com atenção constante. Nem todo '
             'alvo reflete bem o sinal do radar (embarcações pequenas ou de madeira); isso não dispensa a vigilância visual e auditiva '
             'possível.'),
            ('12 · Overlay na carta',
             'O overlay sobrepõe a imagem ao vivo do radar à carta eletrônica no plotter, permitindo comparar o que o radar detecta com a '
             'costa e os pontos da carta. Use a sobreposição para conferir se a posição do barco na carta está coerente com os ecos reais. '
             'O contorno do radar pode não coincidir exatamente com a carta por maré, vegetação ou carta desatualizada; use como apoio, '
             'não como prova única de posição.'),
            ('13 · Segurança da antena transmitindo',
             'A antena do radar emite energia de radiofrequência enquanto transmite. Ficar muito próximo da área irradiada ou abrir a '
             'estrutura com o radar ligado expõe a pessoa a essa energia. Antes de qualquer serviço perto da antena ou domo, coloque o '
             'radar em espera (standby) ou desligue-o, e avise outras pessoas a bordo antes de ligar a transmissão se alguém estiver '
             'perto. A distância mínima de segurança é definida pelo fabricante do equipamento; siga a etiqueta ou o manual do radar '
             'instalado. Nunca abra o domo ou a estrutura da antena com o radar transmitindo.'),
        ],
    },
    'g_ais': {
        'titulo': ARQ['g_ais'], 'pasta': 'manuais', 'equip': equip_de('ais'), 'seg': {'2'},
        'secoes': [
            ('1 · Alvos no plotter', 'Os alvos do AIS aparecem no plotter com nome, rumo e velocidade. Toque no alvo para ver a menor distância de passagem prevista.'),
            ('2 · Identificação', 'O AIS transmite a identificação programada no transponder; o MMSI é o do rádio de bordo (etiqueta / Licença de Estação).'),
            ('3 · Modo silencioso', 'No modo silencioso o transponder só recebe e não transmite a posição do barco. Use só quando necessário e volte a transmitir ao sair.'),
            ('4 · O que o AIS faz', 'O AIS classe B transmite a posição, o rumo e a velocidade deste barco para quem estiver por perto e recebe os mesmos dados de quem tiver AIS, que aparecem no plotter como alvos. Funciona por rádio VHF, em linha de visada: o alcance é limitado pelo horizonte. O classe B transmite com menos potência e, em geral, com menos prioridade do que o classe A dos navios, com alcance menor. Só aparece quem estiver com o AIS ligado: embarcações pequenas e barcos de pesca costumam não aparecer. O AIS complementa a vigia e o radar; não substitui nenhum dos dois.'),
            ('5 · Ler os alvos: CPA e TCPA', 'Cada alvo do AIS é um barco com o aparelho ligado; o símbolo mostra a posição e o rumo dele. Ao tocar no alvo, o plotter abre os dados: nome, rumo, velocidade e a menor distância de passagem prevista (CPA), com o tempo até ela (TCPA). Compare o rumo e a velocidade do alvo com os seus para ver se os trajetos se cruzam: CPA pequeno e TCPA curto pedem atenção. Confirme com a vista e o radar e aja cedo, reduzindo ou mudando o rumo pelas regras de navegação. Depois de mudar de rumo, reveja o alvo: a previsão se atualiza com o movimento dos dois barcos.'),
            ('6 · Modo silencioso: quando usar', 'Use o modo silencioso só com o barco parado, em local sem tráfego e com motivo claro, como privacidade na marina. Ative e desative pelo comando instalado pelo técnico — confirme com ele onde fica — e registre no diário a hora em que ativou. Antes de largar, volte ao normal e confirme pelo indicador do aparelho que ele voltou a transmitir. Navegando, em neblina, à noite ou em canal de tráfego, mantenha o AIS transmitindo.'),
            ('7 · Sem alvos no AIS', 'Sem alvos pode ser só falta de tráfego com AIS por perto, ou falha de alimentação, antena, ligação com o plotter ou ajuste da carta: confira em ordem, do mais simples ao mais difícil. Em enseadas e fora de rotas de navios pode haver poucos barcos com AIS ao alcance. Confira se o AIS está ligado, com o disjuntor armado e o indicador de funcionamento aceso, e se a camada e a fonte de AIS estão habilitadas nos ajustes do plotter. Sem posição de GPS no plotter, os alvos e os alarmes de aproximação podem não funcionar. Confira também a antena e o cabo do AIS: conectores firmes e sem corrosão. Há barcos à vista e continua sem alvo: registre no diário e chame o técnico de bordo.'),
            ('8 · Alvo sem nome, aos saltos ou que some', 'O nome e o tamanho do barco chegam com menos frequência do que a posição, e o alvo de classe B atualiza mais devagar do que o de classe A: por isso um alvo pode chegar só com um número, andar aos saltos ou sumir e voltar por um tempo. Alvo só com número: espere alguns minutos, porque o nome costuma chegar depois da posição. Alvo que some e volta costuma ser sinal no limite do alcance ou o barco passando atrás de terra ou de construções; se ficar parado sem se atualizar, trate a posição como antiga e confirme com a vista e o radar. Nenhum alvo ganha nome mesmo depois de muito tempo: registre no diário e chame o técnico de bordo.'),
        ],
    },
    'g_seafire': {
        'titulo': ARQ['g_seafire'], 'pasta': 'manuais', 'equip': equip_de('seafire'), 'seg': True, 'nota': NOTA_PROTOCOLO,
        'secoes': [
            # Revisão do C5: cada seção que a busca traz ao topo depois do disparo leva o "não abra o acesso ao motor" e o desligamento de
            # motores, gerador e ventilação (revisão 3: o motor ligado aspira o agente e a ventilação o dilui). Revisão 4: isso fica só
            # no §1 (os 5 passos do protocolo) e no §3, que diz "disparou"/"descarregou", as palavras do relato. O §2 é só o disparo manual
            # (sem "disparou", "depois" nem "esfriar") e o §3 não repete o "ao abrir" nem o "motor esfriar": repetidos nas três seções,
            # esses passos casavam perguntas comuns ("como religar o gerador depois de desligar", "como abrir o motor", "como esfriar o
            # motor depois de navegar") e, por serem de segurança, barravam a IA (cerebro.py, revisão 4).
            ('1 · Em caso de fogo', fim_seguro(*TXT_SEAFIRE)),
            ('2 · Disparo manual', fim_seguro('Se o sistema não acionou sozinho e há fogo no motor, use o disparo manual, com motores e gerador '
                                              'desligados e a ventilação do motor cortada.')),
            ('3 · Depois da descarga', fim_seguro('Depois do disparo do sistema (disparou ou descarregou, sozinho ou no disparo manual): confirme '
                                                  'motores, gerador e ventilação desligados; não abra o acesso ao motor; espere o tempo indicado '
                                                  'na etiqueta do sistema e só então libere o acesso, com o extintor portátil à mão; se o fogo '
                                                  'voltar, MAYDAY no canal 16. Registre no diário e chame o técnico de bordo para a recarga.')),
            ('4 · Inspeção anual', fim_seguro('Inspeção do sistema fixo e da carga a cada 12 meses, pelo técnico de bordo, conforme a agenda de manutenção.')),
        ],
    },
    'g_epirb': {
        'titulo': ARQ['g_epirb'], 'pasta': 'manuais', 'equip': equip_de('epirb'), 'seg': True, 'nota': NOTA_PROTOCOLO,
        'secoes': [
            ('1 · Acionar', fim_seguro(*TXT_EPIRB[:3])),
            ('2 · Teste da baliza', fim_seguro(*TXT_EPIRB_TESTE)),
            ('3 · Disparo por engano', fim_seguro(TXT_EPIRB[3])),
            ('4 · Validade', fim_seguro('Validade da bateria e do disparador hidrostático: veja a etiqueta do equipamento e o certificado em Documentos.')),
        ],
    },
    'checklist': {
        'titulo': ARQ['checklist'], 'pasta': 'manuais', 'equip': 'Checklist de bordo', 'seg': {'Saída · antes de largar'},
        'secoes': [
            ('Saída · 1 a 3', '1. Gerador: confira água no escapamento depois de ligar. 2. Estabilizador: ligue com antecedência, com o banco de 12 V carregado. 3. Climatização: filtro de água salgada limpo antes de ligar.'),
            ('Saída · 4 a 6', '4. Eletrônicos: plotter ligado, piloto em espera até sair da marina, VHF no canal 16. 5. Bombas de porão: acione cada uma manualmente e confira o alarme. 6. Diesel: ' + REGRA_ABAST + '.'),
            ('Saída · antes de largar', 'Coletes: um por pessoa — conte as pessoas a bordo agora; balsa, boia e extintores conforme a placa de salvatagem. Previsão do dia consultada (vento e mar) — confira o boletim da Marinha antes de sair.'),
            ('Chegada', '1. Piloto em espera antes de manobrar. 2. Estabilizador: desligar ao atracar e manter o banco de 12 V ligado até o volante parar. 3. Gerador: retirar cargas, esfriar e desligar. 4. Climatização: desligar e fechar válvula de fundo se o barco ficar parado. 5. Fechar a saída no diário: horas, consumo e pendências.'),
            ('Abastecimento', texto_abastecimento()),
            ('Tanques', texto_tanques()),
            ('Fundeio', '1. Fundo de areia ou lama, com espaço de giro livre de outros barcos. 2. Lance com o barco parado e dê ré devagar até a âncora unhar. 3. Alarme de âncora ativado no plotter. 4. Registre no diário a hora e a profundidade.'),
        ],
    },
    'protocolo': {
        'titulo': ARQ['protocolo'], 'pasta': 'protocolos', 'equip': 'Protocolo de emergência — procedimento padrão (confirmar com o protocolo de bordo)',
        'seg': True, 'nota': NOTA_PROTOCOLO,
        'secoes': [
            ('MAYDAY · canal 16', 'Só em perigo grave e iminente. VHF canal 16 (156,800 MHz). Diga devagar: ' + roteiro_falado() + '. Repita até ter resposta. ' + FIM_ROTULO),
            ('PAN-PAN', TXT_PANPAN + ' ' + FIM_ROTULO),
            ('DSC', TXT_DSC + ' ' + FIM_ROTULO),
            ('Homem ao mar', ' '.join(TXT_MOB) + ' ' + FIM_ROTULO),
            ('Incêndio · Seafire', fim_seguro(*TXT_SEAFIRE)),
            ('EPIRB', fim_seguro(*TXT_EPIRB)),
            ('Água entrando', TXT_ALAGAMENTO[0] + ' ' + FIM_ROTULO),
            ('Abandono', TXT_ABANDONO[0] + ' ' + FIM_ROTULO),
            ('Salvatagem', fim_seguro(TXT_SALVATAGEM)),
        ],
    },
}
FONTE_GUIA = {k: g['titulo'] for k, g in GUIAS.items()}

# Palavras de acionamento (revisão 5 do C5; CONTRATO §1.5): como a pessoa conta a situação que o trecho de segurança trata e que o
# título não diz. O cérebro as conta na identidade do trecho (buscaBase: só entra o trecho de segurança que a pergunta nomeia); sem elas,
# "pessoa caiu da lancha" e "barco sem governo", com as palavras do próprio trecho, iam à IA, porque a identidade era só a fonte, o
# equipamento e o título ("Homem ao mar", "PAN-PAN"). Chave: guia → seção (o número ou o título, como no "seg") → palavras. Só emergência
# descrita por quem a vê; nada de verbo de operação ("desligar", "abrir") nem de palavra de equipamento, que sequestram pergunta comum.
# Revisão 6 do C5: "caiu" também é disjuntor, energia e sinal ("o plotter caiu, como resolver" devolvia o protocolo de homem ao mar e
# barrava a IA). As palavras de quem cai valem só junto de uma palavra de pessoa na pergunta (`identCom`, IDENT_PESSOA): "pessoa caiu da
# lancha", "perdemos de vista quem caiu", "pessoa ao mar" nomeiam; "o disjuntor caiu" e "tem vista para o mar" não. A tupla é
# (ident, identCom); a string é só `ident` (pane e governo não dependem de pessoa). "mar" entra aqui e não na identidade pelo título
# ("mar" sozinho é o estado do mar, a vista, a temperatura da água): ver IDENT_GENERICAS do cérebro.
# A palavra de pessoa só destrava a identidade: a cobertura da busca (2 palavras e 60 % da pergunta no texto do trecho) segue valendo, e
# "alguém caiu", "tripulante ao mar" e "criança ao mar" ainda vão à IA: a lista SOS do §2.3 do PROMPT não os tem; ficam assim até o ok do
# proprietário aos tokens do CONTRATO §8.2, item 11, que a 1b leva para a lista (revisão 7 do C5).
IDENT_PESSOA = 'pessoa quem alguém gente homem tripulante criança'
IDENT_ACIONAMENTO = {
    'protocolo': {'Homem ao mar': ('caiu cair queda vista mar', IDENT_PESSOA), 'PAN-PAN': 'pane governo ferido urgência'},
    'g_eletronicos': {'1': ('caiu cair queda', IDENT_PESSOA)},
}


def trecho_seguro(g, sec, t):
    """seguranca do trecho (§1.5): o mínimo do guia ("seg") ou a SEGURANCA_PALAVRAS em qualquer campo (fonte e equip inclusive)."""
    seg = g.get('seg')
    if seg is True or (seg and (sec in seg or sec.split(' · ')[0] in seg)):
        return True
    return segura(' '.join(t[k] for k in ('fonte', 'equip', 'secao', 'texto')))


def trechos():
    out = []
    for chave, g in GUIAS.items():
        for sec, txt in g['secoes']:
            t = {'fonte': g['titulo'], 'secao': sec, 'texto': txt, 'equip': g['equip']}
            if trecho_seguro(g, sec, t):
                t['seguranca'] = True
            ident = IDENT_ACIONAMENTO.get(chave, {})
            if sec in ident or sec.split(' · ')[0] in ident:
                palavras = ident.get(sec) or ident[sec.split(' · ')[0]]
                if isinstance(palavras, tuple):
                    t['ident'], t['identCom'] = palavras
                else:
                    t['ident'] = palavras
            out.append(t)
    return out


# FAQ por equipamento (telas F2–F5, legado até a Fase 4): passo a passo tirado das mesmas seções dos guias de bordo. Os títulos
# do FAQ de eletrônicos mantêm "Rádio VHF" e "áudio Fusion": é por eles que a F1 abre a pergunta certa (palavras, §1.4).
def faq():
    def passos(k, idx):
        g = GUIAS[k]
        return [{'n': str(i + 1), 't': g['secoes'][j][1], 'secao': g['secoes'][j][0]} for i, j in enumerate(idx)]
    return {
        'gerador': {'status': 'PRONTO', 'fonte': GUIAS['g_gerador']['titulo'], 'equip': 'Gerador Onan', 'modelo': _eq('gerador')['modelo'],
                    'perguntas': [
                        {'q': 'Como ligar o gerador?', 'passos': passos('g_gerador', [0, 1, 2])},
                        {'q': 'Como desligar o gerador?', 'passos': passos('g_gerador', [3])},
                        {'q': 'Alarme de alta temperatura', 'passos': passos('g_gerador', [4])},
                        {'q': 'Alarme de baixa pressão de óleo', 'passos': passos('g_gerador', [5])},
                        {'q': 'Quantas horas tem e quando revisar?', 'passos': passos('g_gerador', [7, 6])},
                    ]},
        'estabilizador': {'status': 'PRONTO', 'fonte': GUIAS['g_seakeeper']['titulo'], 'equip': 'Estabilizador Seakeeper', 'modelo': _eq('estabilizador')['modelo'],
                          'perguntas': [
                              {'q': 'Como ligar antes de sair?', 'passos': passos('g_seakeeper', [0, 1, 2])},
                              {'q': 'Como desligar ao atracar?', 'passos': passos('g_seakeeper', [3, 4])},
                              {'q': 'Apareceu um alarme', 'passos': passos('g_seakeeper', [5])},
                              {'q': 'Manutenção', 'passos': passos('g_seakeeper', [6])},
                          ]},
        'eletronicos': {'status': 'PRONTO', 'fonte': GUIAS['g_eletronicos']['titulo'], 'equip': 'Eletrônicos Garmin · Fusion · Icom',
                        'modelo': ' · '.join([_eq('eletronicos')['modelo'], _eq('audio')['modelo'], _eq('vhf')['modelo'].split(' e ')[0]]),
                        'perguntas': [
                            {'q': 'Homem ao mar no plotter', 'passos': passos('g_eletronicos', [0])},
                            {'q': 'Piloto automático', 'passos': passos('g_eletronicos', [1])},
                            {'q': 'Alarme de âncora', 'passos': passos('g_eletronicos', [2])},
                            {'q': 'Rádio VHF: canal 16 e DSC', 'passos': passos('g_eletronicos', [3, 4])},
                            {'q': 'Parear o celular no áudio Fusion', 'passos': passos('g_eletronicos', [5])},
                        ]},
        'climatizacao': {'status': 'PRONTO', 'fonte': GUIAS['g_clima']['titulo'], 'equip': 'Climatização Webasto',
                         'modelo': ' '.join(_eq('climatizacao')['modelo'].split()[:2]),
                         'perguntas': [
                             {'q': 'Como ligar a climatização?', 'passos': passos('g_clima', [0, 1])},
                             {'q': 'Alarme de fluxo', 'passos': passos('g_clima', [2])},
                             {'q': 'Ar fraco na cabine', 'passos': passos('g_clima', [3])},
                             {'q': 'Como desligar?', 'passos': passos('g_clima', [4])},
                         ]},
    }


# ——————————————————————————————— FAQ DOS EQUIPAMENTOS (faq-equipamentos.json, F10; CONTRATO §1.6) ———————————————————————————————
# Arquivo próprio na raiz, gerado aqui e lido pelo cérebro e pela F6 nas Fases 3 e 4 (fora do CORE do sw.js até lá). Um item por seção
# dos 15 guias e do checklist (82: id = prefixo do guia + número da seção, MO-01…CK-07) e os 9 cartões de emergência EM-01…EM-09 do
# protocolo (91 no total). Do Avanti vem só a forma; o texto é do Capitão e sai dos guias gerados:
#   - passo a passo, atenção e "se não" são frases da própria seção (índice na lista de frases) ou recortes dela, nunca número novo
#     (a asserção FAQ confere que todo número do item está no trecho da base que ele cita);
#   - titulo, pergunta, variantes (as 3 maneiras de perguntar), acao e resposta são escritos aqui, sem dado que a seção não tenha;
#   - sem confiabilidade (conf), edição, origem, selos, decisões, lacunas, divergências, alertas, inválidos nem limites: todo item vem do
#     guia de bordo gerado, um nível só não informa nada (decisão 8 do §8.2). Fica só o glossário;
#   - seguranca: true no item cujo trecho de origem tem, ou cujo texto casa a SEGURANCA_PALAVRAS (nada com seguranca vai à IA, F30);
#   - EM, SF e EP só com o procedimento padrão rotulado, sem fabricante, modelo, validade, posição, pessoas nem lugar (§1.6).
#   - a `resposta` (que a tela e a voz leem inteira) mantém, do trecho de origem, toda frase que condiciona ou escala («e há fogo no motor»,
#     «Se perder de vista: MAYDAY…»): a asserção FAQ reprova a resposta que corta uma frase com MAYDAY ou «há fogo»;
#   - os itens do checklist sem seção nos guias entram como ordem de conferência (FAQ_CK_ORDEM), nunca como o estado que o app avalia.
FAQ_GUIAS = (('MO', 'g_motores'), ('GE', 'g_gerador'), ('SK', 'g_seakeeper'), ('CL', 'g_clima'), ('EL', 'g_eletronicos'),
             ('VH', 'g_vhf'), ('EE', 'g_eletrico'),
             ('DS', 'g_dessalinizador'), ('PO', 'g_porao'), ('AN', 'g_ancora'), ('PI', 'g_piloto'), ('RA', 'g_radar'), ('AI', 'g_ais'),
             ('SF', 'g_seafire'), ('EP', 'g_epirb'), ('CK', 'checklist'))
# Os 9 cartões: EM-n ↔ a seção do protocolo (a ordem do contrato, não a da base: o EPIRB vem depois de abandono).
FAQ_EM = (('EM-01', 'MAYDAY · canal 16'), ('EM-02', 'PAN-PAN'), ('EM-03', 'DSC'), ('EM-04', 'Homem ao mar'), ('EM-05', 'Incêndio · Seafire'),
          ('EM-06', 'Água entrando'), ('EM-07', 'Abandono'), ('EM-08', 'EPIRB'), ('EM-09', 'Salvatagem'))
FAQ_SECOES = (('Emergência', ('EM',)), ('Motores', ('MO',)), ('Gerador e energia', ('GE', 'EE')), ('Estabilizador', ('SK',)),
              ('Climatização, água e porão', ('CL', 'DS', 'PO')), ('Eletrônicos e rádios', ('EL', 'VH')),
              ('Fundeio, piloto, radar e AIS', ('AN', 'PI', 'RA', 'AI')), ('Incêndio e EPIRB', ('SF', 'EP')), ('Checklists', ('CK',)))
# fontes[].tipo: «Guia de bordo» (a seção do guia ou do checklist), «Protocolo» (a seção do protocolo) e «Boa prática» (item do checklist sem seção nos guias);
# nunca «Manual» nem «Foto»: não há manual do fabricante nem foto em dado de bordo (a asserção FAQ confere os três).
# A 2ª fonte dos itens que repetem o texto de uma seção do protocolo (a D.protocolos é a fonte única; PROTOCOLOS_NOS_GUIAS do confere.py).
FAQ_PROTOCOLO = {'SF-01': 'Incêndio · Seafire', 'EP-01': 'EPIRB', 'EP-03': 'EPIRB', 'EL-05': 'DSC', 'PO-04': 'Água entrando'}
FAQ_BOA_PRATICA = 'Checklist de bordo · itens sem seção nos guias de bordo (boa prática)'
FAQ_AGENDA = 'Datas e situação de cada tarefa: veja a agenda de manutenção do app.'
# Os itens do checklist «sem seção nos guias» (boa prática) como o FAQ os diz. No checklist (D.checklists) são o rótulo de um ✓ que o app avalia
# («Nenhum alerta ativo no painel.»); solto no FAQ, o mesmo texto vira uma afirmação sobre o estado do barco que o dado de bordo pode desmentir
# (o laço tem AVISO, a agenda tem a tarefa de segurança atrasada). Aqui cada um é uma ordem de conferência ou de ação, com verbo; o a04 já é ordem.
FAQ_CK_ORDEM = {
    's02': 'Confira que não há alerta ativo no painel.',
    's11': 'Confira que os documentos estão em dia (TIE, seguro, Licença de Estação).',
    's12': 'Confira na agenda se há tarefa de segurança atrasada.',
    's14': 'Recolha cabos e defensas depois de largar.',
    'c07': 'Deixe cabos e defensas prontos antes de atracar.',
    'a01': 'Desligue os motores.',
    'a02': 'Desligue o gerador.',
    'a03': 'Anote o nível de diesel antes.',
    'a04': 'Sem fumar a bordo; extintor portátil à mão.',
    'a05': 'Use o bocal certo (diesel) e feche a tampa do tanque depois.',
    'f04': 'Deixe os motores em neutro e confira se o barco está derivando.',   # «confira a deriva» casaria a SOS « a deriva »: seguranca no CK-07
    'f06': 'Confira a maré e o vento (previsão da Marinha).',
}
FAQ_EQUIP_EM = {'EM-01': 'Rádios VHF', 'EM-02': 'Rádios VHF', 'EM-03': 'Rádios VHF', 'EM-04': 'Plotters', 'EM-05': 'Sistema fixo de supressão de incêndio',
                'EM-06': 'Bombas de porão', 'EM-07': 'Protocolo de emergência', 'EM-08': 'EPIRB', 'EM-09': 'Salvatagem'}


def _f(t, q, v, r, a=None, p=None, at=None, se=None, ob=None, ver=(), eq=None):
    """A especificação de um item: titulo, pergunta, as 3 variantes, resposta, acao e o resto. r, at, se e ob: texto, índice de frase da
    seção ou lista deles (juntos por espaço); ('ck', ids…) = o item do checklist como ordem (FAQ_CK_ORDEM). p: None = as frases que r, at e se não usaram,
    [] = sem passo a passo, ou a lista de frases (índice ou texto)."""
    return dict(t=t, q=q, v=list(v), r=r, a=a, p=p, at=at, se=se, ob=ob, ver=tuple(ver), eq=eq)


FAQ_TEXTOS = {
    # ——— Emergência: cartões EM (o texto é o do D.protocolos; o rótulo do procedimento padrão vem no fim da resposta) ———
    'EM-01': _f('MAYDAY: pedido de socorro pelo rádio', 'Como faço um pedido de socorro (MAYDAY) pelo rádio?',
                ['chamada de socorro no canal 16', 'o que falar no MAYDAY', 'como chamar socorro no VHF'],
                'Só em perigo grave e iminente. No canal 16 do VHF, fale MAYDAY três vezes e o nome da embarcação três vezes; depois o MMSI do '
                'rádio de bordo (etiqueta / Licença de Estação), a posição lida no plotter, a natureza do perigo, as pessoas a bordo (conte agora) '
                'e o auxílio necessário. Termine com CÂMBIO e repita até ter resposta.',
                a='VHF no canal 16: MAYDAY três vezes, depois o roteiro.', p=list(TXT_ROTEIRO), at='Só em perigo grave e iminente.',
                se='Sem resposta: repita a chamada até ter resposta.', ver=('EM-03', 'EM-04', 'EL-04')),
    'EM-02': _f('PAN-PAN: urgência sem perigo imediato de vida', 'Quando uso o PAN-PAN em vez do MAYDAY?',
                ['diferença entre PAN-PAN e MAYDAY', 'pane sem governo: que chamada faço', 'chamada de urgência no canal 16'],
                TXT_PANPAN, a='Canal 16: PAN-PAN três vezes, no mesmo formato do MAYDAY.',
                p=['PAN-PAN, PAN-PAN, PAN-PAN no canal 16.', 'Siga o mesmo formato da chamada MAYDAY.'], ver=('EM-01',)),
    'EM-03': _f('Alerta DSC de socorro pelo rádio', 'Como mando o alerta DSC de socorro pelo rádio?',
                ['botão DISTRESS do rádio VHF', 'identificação do rádio no alerta de socorro', 'depois do botão DISTRESS, o que faço'],
                TXT_DSC, a='Depois do alerta, faça o MAYDAY por voz no canal 16.',
                p=['O botão DISTRESS envia o alerta com a identificação programada no rádio.', 'Depois do alerta, faça o MAYDAY por voz no canal 16.'],
                ver=('EM-01', 'EL-05')),
    'EM-04': _f('Homem ao mar (MOB)', 'O que faço quando alguém cai na água?',
                ['pessoa caiu do barco', 'homem ao mar: primeiros passos', 'como recuperar quem caiu'],
                'Grite HOMEM AO MAR e o lado, jogue a boia ou qualquer objeto que flutue, aponte sem perder de vista e marque MOB no plotter. '
                'Volte devagar, com o motor em neutro perto da pessoa. Se perder de vista: MAYDAY no canal 16 com a posição da marca MOB lida no plotter.',
                a='Grite HOMEM AO MAR, jogue a boia e aponte sem perder de vista.', p=list(TXT_MOB), ver=('EL-01', 'EM-01')),
    'EM-05': _f('Incêndio a bordo', 'O que faço se houver fogo a bordo?',
                ['fogo no motor', 'alarme do sistema fixo de incêndio', 'como usar o extintor portátil no fogo'],
                'Fogo no motor ou alarme do sistema fixo: desligue motores e gerador, corte a ventilação do motor e, se o sistema não disparou '
                'sozinho e há fogo no motor, use o disparo manual. Não abra o acesso ao motor depois da descarga: espere o tempo indicado na '
                'etiqueta do sistema e o motor esfriar. Fogo pequeno fora do motor: extintor portátil na base das chamas, de costas para a saída. '
                'Fogo que não apaga: MAYDAY no canal 16 e prepare o abandono.',
                a='Desligue motores e gerador e corte a ventilação do motor.', p=list(TXT_SEAFIRE), ver=('SF-01', 'SF-03', 'EM-01')),
    'EM-06': _f('Água entrando no barco', 'O que faço se estiver entrando água?',
                ['alagamento no porão', 'a bomba de porão não dá conta', 'nível do porão subindo'],
                TXT_ALAGAMENTO[0], a='Ligue as bombas de porão no manual e procure a entrada de água.',
                p=['Ligue as bombas de porão no manual.', 'Procure a entrada (válvulas de fundo, mangueiras, eixos) e feche o que puder.',
                   'Água subindo mesmo assim: MAYDAY no canal 16.'], ver=('PO-04', 'PO-02', 'EM-01')),
    'EM-07': _f('Abandono do barco', 'Quando e como abandono o barco?',
                ['preciso abandonar o barco', 'ordem de abandono', 'o que levar para a balsa'],
                TXT_ABANDONO[0], a='Antes de abandonar, MAYDAY no canal 16.',
                p=['Só abandone quando não houver como manter o barco.', 'Antes, MAYDAY no canal 16.', 'Coletes em todos.',
                   'Leve o EPIRB e o VHF portátil.', 'Embarque na balsa sem pular na água.'], ver=('EM-01', 'EM-08', 'EM-09')),
    'EM-08': _f('EPIRB (radiobaliza): acionar', 'Quando e como aciono o EPIRB?',
                ['como disparar a radiobaliza', 'acionar a baliza de emergência', 'EPIRB em perigo grave'],
                'Só em perigo grave e iminente, depois do MAYDAY (ou sem rádio). Acione conforme a etiqueta do equipamento, com a antena para cima '
                'e céu aberto, e leve o EPIRB para a balsa ou mantenha-o flutuando preso por um cabo. Não desligue até o resgate. Disparo por engano: '
                'desligue e avise no canal 16.',
                a='Só em perigo grave e iminente, depois do MAYDAY (ou sem rádio).', p=list(TXT_EPIRB), ver=('EP-01', 'EP-03', 'EM-01')),
    'EM-09': _f('Salvatagem: coletes, balsa e extintores', 'Onde estão os coletes, a balsa e os extintores?',
                ['equipamentos de salvatagem do barco', 'quantos coletes preciso levar', 'onde ficam os sinalizadores'],
                TXT_SALVATAGEM, a='Em perigo agora: SOS do app e VHF canal 16.',
                p=['Em perigo agora: SOS do app e VHF canal 16.', 'Coletes: um por pessoa — conte as pessoas a bordo agora (lotação: veja a placa de lotação).',
                   'Balsa, coletes, boias, extintores e sinalizadores: no local da placa de salvatagem e do plano de segurança de bordo — confira na saída.'],
                ver=('CK-03', 'EM-07')),
    # ——— Motores ———
    'MO-01': _f('Antes de dar a partida nos motores', 'O que olho nos motores antes da partida?',
                ['verificação antes da partida do motor', 'motor frio: o que olhar primeiro', 'checar o motor antes de ligar'],
                'Com os motores parados e frios, confira o nível de óleo na vareta, o líquido de arrefecimento, as correias, as válvulas de fundo '
                'abertas e o porão seco, e deixe a ventilação da praça de máquinas ligada por alguns minutos.',
                a='Com os motores frios: óleo, arrefecimento, correias e válvulas de fundo.',
                p=['Nível de óleo na vareta.', 'Líquido de arrefecimento.', 'Correias.', 'Válvulas de fundo abertas.', 'Porão seco.',
                   'Ventilação da praça de máquinas ligada por alguns minutos.'], ver=('MO-02', 'CK-01')),
    'MO-02': _f('Dar a partida nos motores', 'Como ligo os motores?',
                ['dar partida no motor', 'partida dos dois motores pelo painel', 'ligar o motor de bombordo e o de boreste'],
                'Dê a partida pelo painel, um motor de cada vez, com a marcha em neutro, e logo depois confira a saída de água pelo escapamento '
                'e a pressão de óleo no painel dos dois motores.',
                a='Partida pelo painel, um motor de cada vez, com a marcha em neutro.', ver=('MO-01', 'MO-03', 'MO-04')),
    'MO-03': _f('Aquecer os motores', 'Preciso aquecer o motor antes de acelerar?',
                ['motor frio: posso acelerar', 'tempo de aquecimento do motor', 'marcha lenta antes de acelerar'],
                ['Sim: deixe alguns minutos em marcha lenta antes de acelerar.', 1], a='Alguns minutos em marcha lenta antes de acelerar.',
                p=[0], at=1, ver=('MO-02', 'MO-09')),
    'MO-04': _f('Pressão de óleo baixa no motor', 'O que faço se a pressão de óleo cair?',
                ['alarme de pressão de óleo no motor', 'manômetro de óleo baixo', 'motor sem pressão de óleo'],
                'Reduza para marcha lenta e confira o manômetro; compare BB e BE no mesmo giro, porque só um lado baixo aponta o motor. Se '
                'continuar baixa, desligue o motor afetado, siga com o outro e chame a oficina dos motores.',
                a='Reduza para marcha lenta e confira o manômetro agora.', ver=('MO-09', 'MO-05')),
    'MO-05': _f('Temperatura alta no motor', 'O motor esquentou demais, o que faço?',
                ['alarme de temperatura do motor', 'arrefecimento do motor subindo', 'motor superaquecendo'],
                'Reduza para marcha lenta e confira a saída de água pelo escapamento. Se não sair água ou a temperatura continuar subindo, '
                'desligue o motor afetado e siga com o outro. Nunca abra a tampa do arrefecimento com o motor quente.',
                a='Marcha lenta e saída de água pelo escapamento.', p=[0, 2], at=3, se=1, ver=('MO-09', 'GE-05')),
    'MO-06': _f('Desligar os motores depois de navegar', 'Quanto tempo deixo o motor em marcha lenta antes de desligar?',
                ['esfriar o motor antes de parar', 'posso desligar o motor logo ao chegar', 'marcha lenta antes de desligar'],
                'Depois de navegar, de %s minutos em marcha lenta, para o motor esfriar por igual.' % de_a(PARADA_MOTORES_MIN),
                a='De %s minutos em marcha lenta antes de desligar.' % de_a(PARADA_MOTORES_MIN), p=[0], ver=('CK-04', 'MO-03')),
    'MO-07': _f('Manutenção dos motores na agenda', 'Quando é a próxima troca de óleo e do rotor dos motores?',
                ['troca de óleo e filtros do motor', 'prazo de troca do rotor da bomba de água salgada', 'revisão anual dos motores'],
                [0, 1, 2], p=[], ob=FAQ_AGENDA),
    'MO-08': _f('Horímetros dos motores', 'Onde vejo as horas de uso dos motores?',
                ['horímetro dos motores de BB e BE', 'quantas horas têm os motores', 'horas de motor na telemetria'], [0], p=[]),
    'MO-09': _f('Faixas de operação dos motores', 'Quais são os valores normais de rotação, óleo e temperatura dos motores?',
                ['faixa normal do motor', 'limites de pressão de óleo e arrefecimento', 'rotação de cruzeiro dos motores'],
                [0, 1, 2, 3, 4, 5, 6, 7], p=[], se=[8, 9]),
    'MO-10': _f('Consumo de diesel dos motores', 'Quanto os motores gastam de diesel por hora?',
                ['consumo em marcha lenta e em cruzeiro', 'litros por hora dos dois motores', 'gasto de combustível na rotação máxima'],
                [0], p=[], ver=('CK-05',)),
    'MO-11': _f('Faixas de rotação dos motores: da marcha lenta ao cruzeiro', 'Quais são as faixas de rotação dos motores e para que serve cada uma?',
                ['zonas de rotação do motor', 'rpm de deslocamento, transição e planeio', 'quando o casco sai do deslocamento e entra no planeio'],
                'Os motores trabalham em cinco faixas de rotação. Marcha lenta, de 600 a 1.000 rpm: manobra e aquecimento, com o motor perto de 700 rpm, cerca de 5 nós e 6,2 L/h nos dois motores. Deslocamento, de 1.000 a 1.500 rpm: navegação lenta, com o casco ainda em deslocamento. Transição, de 1.500 a 1.800 rpm: passagem do deslocamento para o planeio. Planeio, de 1.800 a 2.000 rpm: o casco já plana. Cruzeiro, de 2.000 a 2.600 rpm: a referência é 2.050 rpm, cerca de 18 nós e 68 L/h nos dois motores. Máxima: 2.600 rpm, cerca de 26 nós e 111 L/h nos dois motores; acima disso a rotação está acima do normal. Aumente o giro por etapas, sem acelerar de uma vez, e use rotação alta só depois que a temperatura de arrefecimento estabilizar.',
                a='Marcha lenta, deslocamento, transição, planeio e cruzeiro, até 2.600 rpm.', p=['Marcha lenta, de 600 a 1.000 rpm: manobra e aquecimento (perto de 700 rpm, 5 nós, 6,2 L/h).', 'Deslocamento, de 1.000 a 1.500 rpm.', 'Transição, de 1.500 a 1.800 rpm.', 'Planeio, de 1.800 a 2.000 rpm.', 'Cruzeiro, de 2.000 a 2.600 rpm (referência 2.050 rpm, 18 nós, 68 L/h).', 'Máxima: 2.600 rpm, 26 nós, 111 L/h.'], at='Os consumos valem para os dois motores juntos.', ver=('MO-09', 'MO-10')),
    'MO-12': _f('O que conferir nos motores durante a navegação', 'O que devo conferir nos motores enquanto navego?',
                ['ronda pela praça de máquinas', 'comparar o motor BB com o BE', 'pressão de óleo e temperatura normais em cruzeiro'],
                'Olhe os painéis dos dois motores em intervalos regulares e compare BB com BE no mesmo giro: rotação, pressão de óleo, temperatura de arrefecimento e carga devem ser parecidas; uma diferença que cresce com o tempo é o primeiro sinal de problema. Pressão de óleo: de 2,4 a 6,0 bar a partir de 1.000 rpm; abaixo de 2,4 bar é aviso e abaixo de 1,4 bar é crítico. Temperatura de arrefecimento: normal até 88 °C; acima disso é aviso e acima de 97 °C é crítico. Carga e rotação: aviso com carga acima de 90 % ou rotação acima de 2.600 rpm. Praça de máquinas: aviso acima de 60 °C. Na ronda pela praça de máquinas, procure óleo, água ou combustível pingando, ruídos novos e, com a saída do escapamento visível, confira a água saindo; mantenha mãos e roupas longe das correias e dos eixos. Anote no diário qualquer diferença entre os lados, com a rotação e a hora: um lado diferente do outro, mesmo dentro da faixa, merece registro.',
                a='Compare BB e BE no mesmo giro: rotação, óleo, temperatura e carga.', p=['Compare BB e BE: rotação, pressão de óleo, temperatura e carga devem ser parecidas no mesmo giro.', 'Pressão de óleo normal: de 2,4 a 6,0 bar a partir de 1.000 rpm.', 'Temperatura de arrefecimento normal: até 88 °C.', 'Carga e rotação: aviso com carga acima de 90 % ou rotação acima de 2.600 rpm.', 'Praça de máquinas: aviso acima de 60 °C.', 'Na ronda, procure óleo, água ou combustível pingando e ruídos novos.', 'Anote no diário qualquer diferença entre os lados, com a rotação e a hora.'], at='Mantenha mãos e roupas longe das correias e dos eixos na ronda com os motores ligados.', ver=('MO-09', 'MO-04', 'MO-05')),
    'MO-13': _f('Conferir o nível de óleo e do líquido de arrefecimento', 'Como confiro o nível de óleo e do líquido de arrefecimento do motor?',
                ['vareta de óleo do motor', 'completar o líquido de arrefecimento', 'até onde posso completar o óleo'],
                'Confira os dois níveis nos dois motores, parados e frios, antes da partida, e complete só com o produto que o manual do fabricante especifica. Com o motor parado há alguns minutos e o barco nivelado, retire a vareta, limpe com um pano, encaixe até o fim e retire de novo: o nível deve ficar entre as marcas de mínimo e máximo. Se faltar óleo, complete aos poucos e releia a vareta; nunca passe da marca de máximo. Líquido de arrefecimento: com o motor frio, confira o nível no reservatório de expansão ou, se o motor não tiver reservatório, no bocal de enchimento. Não abra a tampa do arrefecimento com o motor quente: o líquido sai sob pressão. Compare BB e BE: se um motor pede óleo ou líquido com frequência bem maior que o outro, avise a oficina de motores. Tipo e quantidade de óleo e de líquido: só pelo manual do fabricante.',
                a='Vareta para o óleo; reservatório de expansão para o arrefecimento, com o motor frio.', p=['Com o motor parado e frio, retire a vareta, limpe e encaixe até o fim.', 'Retire de novo e leia: o nível deve ficar entre as marcas de mínimo e máximo.', 'Se faltar óleo, complete aos poucos e releia a vareta.', 'Líquido de arrefecimento: confira no reservatório de expansão (ou no bocal de enchimento), com o motor frio.', 'Compare BB e BE: um lado pedindo muito mais óleo ou líquido que o outro é assunto da oficina de motores.'], at='Não abra a tampa do arrefecimento com o motor quente: o líquido sai sob pressão.', se='Nunca passe da marca de máximo na vareta; tipo e quantidade, só pelo manual do fabricante.', ver=('MO-01', 'MO-05')),
    'MO-14': _f('Motor não pega na partida', 'O motor não pega, o que faço?',
                ['motor não liga', 'não dá partida no motor', 'partida sem sucesso no painel'],
                'Com as manetes em neutro e o painel ligado, sem alarme aceso, a pressão de óleo deve subir logo após a partida: abaixo de 1.000 rpm o normal é de 1,0 a 6,0 bar. Compare os dois painéis ao repetir no outro motor: rotação, pressão de óleo e temperatura devem ser parecidas. Sem pressão de óleo poucos segundos depois da partida, desligue o motor e não insista. Se o motor não pegar, espere um pouco entre as tentativas e confira o banco de partida (24,4 a 29,4 V), o diesel nos tanques e o filtro separador.',
                a='Espere um pouco entre as tentativas e confira o banco de partida, o diesel e o filtro separador.', p=['A pressão de óleo deve subir logo após a partida: abaixo de 1.000 rpm, normal de 1,0 a 6,0 bar.', 'Compare os dois painéis: rotação, pressão de óleo e temperatura devem ser parecidas.', 'Sem pressão de óleo poucos segundos depois da partida, desligue o motor.', 'Motor que não pega: espere um pouco entre as tentativas.', 'Confira o banco de partida (24,4 a 29,4 V), o diesel nos tanques e o filtro separador.'], at='Sem pressão de óleo poucos segundos depois da partida, não insista: desligue o motor.', ver=('MO-02', 'MO-04')),
    'MO-15': _f('Sem água saindo pelo escapamento do motor', 'Não sai água pelo escapamento do motor, o que faço?',
                ['escapamento sem água', 'falta de refrigeração no motor', 'escapamento seco depois da partida'],
                'O escapamento molhado é refrigerado pela mesma água salgada que refrigera o motor; sem água saindo, motor e escapamento superaquecem rápido. Se estiver navegando, desligue o motor afetado e siga com o outro. Com o motor parado, feche a válvula de fundo da água salgada antes de abrir qualquer peça do circuito, abra e limpe o filtro de água salgada (algas, plástico e sujeira são causas comuns) e confira o rotor da bomba de água salgada: palhetas gastas, trincadas ou faltando pedem troca. Se faltar pedaço do rotor, procure-o no circuito de água antes de religar; na dúvida, chame a oficina de motores. Monte tudo, abra a válvula de fundo, confira que não há vazamento no filtro e religue: confirme a água saindo pelo escapamento logo após a partida, e desligue de novo se não sair. Não ligue o motor com a válvula de fundo fechada: o rotor trabalha a seco e se danifica.',
                a='Com o motor parado, feche a válvula de fundo e confira o filtro e o rotor da bomba de água salgada.', p=['Se estiver navegando, desligue o motor afetado e siga com o outro.', 'Com o motor parado, feche a válvula de fundo da água salgada.', 'Abra e limpe o filtro de água salgada.', 'Confira o rotor da bomba de água salgada: palhetas gastas, trincadas ou faltando pedem troca.', 'Monte tudo, abra a válvula de fundo e confira que não há vazamento no filtro.', 'Religue e confirme a água saindo pelo escapamento; se não sair, desligue de novo.'], at='Não ligue o motor com a válvula de fundo fechada: o rotor trabalha a seco e se danifica.', ver=('MO-05', 'MO-20')),
    'MO-16': _f('Motor perdendo rotação ou sem força', 'O motor está perdendo rotação, o que pode ser?',
                ['motor sem força', 'motor não acelera como antes', 'rpm caindo sem eu mexer na manete'],
                'Queda de rotação sem mexer na manete aponta falta de combustível, carga excessiva ou o motor se protegendo de outro problema; o teste em neutro separa o motor da hélice e do eixo. Compare BB e BE: veja se a queda é em um motor só e se a carga mostrada está alta ou baixa, e olhe o painel por alarme de temperatura ou de pressão de óleo (motores eletrônicos podem limitar a potência para se proteger). Em local seguro, passe para neutro e acelere só um pouco: se a rotação sobe sem esforço, o problema está na carga (cabo, rede ou sujeira na hélice) ou no eixo; se a rotação também cai em neutro, suspeite de combustível (nível nos tanques, água no filtro separador e filtros sujos). Com o motor parado, drene a água do filtro separador de combustível, com um recipiente embaixo, e veja se o diesel que sai está limpo. Com o motor ainda sem força, siga devagar com o outro motor e chame a oficina de motores. Não acelere forte em neutro; motor que perde força de repente, ou volta a perder, é assunto da oficina de motores.',
                a='Compare BB e BE e teste em neutro para separar carga/hélice de combustível.', p=['Compare BB e BE: veja se a queda é num motor só e como está a carga.', 'Olhe o painel por alarme de temperatura ou de pressão de óleo.', 'Em local seguro, passe para neutro e acelere só um pouco.', 'Rotação sobe sem esforço: o problema está na carga, na hélice ou no eixo.', 'Rotação também cai em neutro: suspeite de combustível (nível, água no separador, filtros sujos).', 'Com o motor parado, drene o filtro separador e veja se o diesel que sai está limpo.', 'Com o motor ainda sem força, siga devagar com o outro e chame a oficina de motores.'], at='Não acelere forte em neutro.', se='Motor que perde força de repente, ou volta a perder, é assunto da oficina de motores.', ver=('MO-19', 'MO-04')),
    'MO-17': _f('Vibração anormal nos motores ou no eixo', 'O barco está vibrando em certa rotação, o que pode ser?',
                ['vibração no motor ou no eixo', 'trepidação em certo giro', 'vibração de um lado só do barco'],
                'Vibração nova costuma vir da hélice, do eixo, dos suportes do motor ou de um cilindro trabalhando mal; veja em que rotação ela aparece e se é de um lado só. Anote a rotação em que a vibração aparece e se ela é de um lado só (BB ou BE) ou dos dois: um lado só aponta o motor, o eixo ou a hélice daquele lado. Saia da faixa de rotação em que vibra e evite manter o motor nela. Em local seguro, passe para neutro e acelere com cuidado: se a vibração some, o problema está na hélice, no eixo ou no alinhamento; se continua, no motor ou nos coxins. Com o motor parado, confira se os coxins e os parafusos de fixação do motor estão firmes. Hélice com cabo, rede ou deformada, e alinhamento do eixo, pedem inspeção com o barco fora da água ou por mergulhador, sempre com os motores desligados. Evite manter a rotação em que o barco vibra forte: a vibração desgasta eixo, suportes e motor. Antes de alguém entrar na água perto das hélices, desligue os motores.',
                a='Anote a rotação e o lado; teste em neutro para separar hélice/eixo de motor/coxins.', p=['Anote a rotação em que a vibração aparece e se é de um lado só ou dos dois.', 'Saia da faixa de rotação em que vibra.', 'Em local seguro, passe para neutro e acelere com cuidado.', 'Vibração que some em neutro: hélice, eixo ou alinhamento.', 'Vibração que continua em neutro: motor ou coxins.', 'Com o motor parado, confira coxins e parafusos de fixação.', 'Hélice, eixo e alinhamento: inspeção com o barco fora da água ou por mergulhador, com os motores desligados.'], at='Evite manter a rotação em que o barco vibra forte: desgasta eixo, suportes e motor.', se='Antes de alguém entrar na água perto das hélices, desligue os motores.', ver=('MO-16',)),
    'MO-18': _f('Fumaça no escapamento: o que a cor indica', 'Está saindo fumaça pelo escapamento do motor, o que é?',
                ['fumaça preta no escapamento', 'fumaça branca ou azul no escapamento', 'cor da fumaça do escapamento do motor'],
                'A cor da fumaça do escapamento dá uma pista do problema: fumaça branca na partida a frio é comum; a que persiste com o motor aquecido merece atenção. Note de qual motor sai e em que rotação, e confira os painéis. Preta: mistura rica, carga alta — reduza a rotação e confira casco, hélices e filtro de ar. Azulada: óleo na combustão — confira o nível de óleo e avise a oficina se o consumo estiver alto. Branca persistente: diesel não queimado ou água na combustão — com o motor parado, drene o filtro separador e chame a oficina. Perda de força ou barulho diferente: reduza a rotação e chame a oficina. Registre no diário a cor, o lado, a rotação e a hora. Fumaça fora do escapamento, na praça de máquinas ou nas cabines, não é diagnóstico: siga o protocolo de bordo.',
                a='Preta: mistura rica. Azulada: óleo na combustão. Branca persistente: diesel não queimado ou água.', p=['Veja se a fumaça sai de um motor só ou dos dois, e em que rotação.', 'Confira temperatura, pressão de óleo e rotação nos painéis.', 'Fumaça preta: reduza a rotação e confira casco, hélices e filtro de ar.', 'Fumaça azulada: confira o nível de óleo e avise a oficina se o consumo estiver alto.', 'Fumaça branca que persiste com o motor quente: com o motor parado, drene o filtro separador e chame a oficina.', 'Com perda de força ou barulho diferente: reduza a rotação e chame a oficina.', 'Registre no diário a cor, o lado, a rotação e a hora.'], at='Fumaça fora do escapamento, na praça de máquinas ou nas cabines, não é diagnóstico: siga o protocolo de bordo.'),
    'MO-19': _f('Filtro separador de água do combustível', 'Como dreno a água do filtro separador de combustível?',
                ['filtro de combustível com água', 'diesel contaminado no motor', 'drenar o separador antes de sair'],
                'O filtro separador retém água e sujeira do diesel antes do motor; confira antes de sair e drene a água acumulada — a troca do elemento está ligada à revisão anual dos motores. Com o motor parado, olhe o filtro separador e veja se há água ou sujeira acumulada na parte de baixo; se houver água, drene pelo dreno do filtro, com um recipiente embaixo, até sair só diesel. Não deixe o diesel cair no porão nem na água: recolha tudo e descarte como resíduo. Muita água, ou água que volta logo depois de drenar, indica diesel contaminado: avise a oficina de motores. Peça a troca do elemento na revisão anual, ou antes, se a rotação cair com carga ou o motor perder força. Depois de abrir o sistema de combustível, retire o ar da linha pelo procedimento do manual do fabricante; na dúvida, deixe com a oficina de motores. Só abra o sistema de combustível com o motor parado e frio.',
                a='Com o motor parado, drene pelo dreno do filtro até sair só diesel.', p=['Olhe o filtro separador e veja se há água ou sujeira acumulada.', 'Havendo água, drene pelo dreno do filtro, com um recipiente embaixo.', 'Nunca deixe o diesel cair no porão nem na água: recolha tudo e descarte como resíduo.', 'Muita água, ou água que volta logo depois de drenar: diesel contaminado, avise a oficina.', 'Troca do elemento: na revisão anual, ou antes, se a rotação cair com carga.', 'Depois de abrir o sistema, retire o ar da linha pelo procedimento do manual do fabricante.'], at='Não deixe o diesel cair no porão nem na água: recolha tudo e descarte como resíduo.', se='Só abra o sistema de combustível com o motor parado e frio.', ver=('MO-16',)),
    'MO-20': _f('Rotor (impeller) da bomba de água salgada dos motores', 'Quando troco o rotor da bomba de água salgada dos motores?',
                ['impeller dos motores gasto', 'rotor da bomba de água do mar', 'como trocar o rotor da bomba de água salgada'],
                'O rotor de borracha empurra a água salgada que refrigera o motor e se desgasta com o uso; a troca é prevista a cada 12 meses, feita pela oficina de motores. Observe os sinais de rotor gasto: temperatura de arrefecimento subindo, pouca água no escapamento ou pingos na tampa da bomba. Para inspecionar, desligue o motor e feche a válvula de fundo da água salgada, abra a tampa da bomba, retire o rotor e procure palhetas gastas, trincadas, achatadas ou faltando; se faltar pedaço, procure no circuito de água antes de religar. Encaixe o rotor girando-o no sentido de giro da bomba, para as palhetas se dobrarem do jeito certo, e lubrifique como o manual do fabricante indica. Feche a tampa com junta em bom estado, abra a válvula de fundo, confira que não há vazamento, dê a partida e confirme a água saindo pelo escapamento. Rotor nunca pode trabalhar a seco: não ligue o motor com a válvula de fundo fechada. Pela agenda, a troca é da oficina de motores; com a bomba aberta, deixe o painel desligado.',
                a='A cada 12 meses, pela oficina de motores; sinais de desgaste antes disso pedem inspeção.', p=['Sinais de rotor gasto: arrefecimento subindo, pouca água no escapamento ou pingos na tampa da bomba.', 'Para inspecionar, desligue o motor e feche a válvula de fundo.', 'Abra a tampa, retire o rotor e procure palhetas gastas, trincadas, achatadas ou faltando.', 'Se faltar pedaço, procure no circuito de água antes de religar.', 'Encaixe o rotor no sentido de giro da bomba e lubrifique como o manual do fabricante indica.', 'Feche a tampa, abra a válvula de fundo, dê a partida e confirme a água saindo pelo escapamento.'], at='Rotor nunca pode trabalhar a seco: não ligue o motor com a válvula de fundo fechada.', se='Pela agenda, a troca é da oficina de motores; com a bomba aberta, deixe o painel desligado.', ver=('MO-15', 'MO-07')),
    'MO-21': _f('Inspeção periódica: correias, mangueiras e anodos', 'O que inspeciono nos motores de tempos em tempos?',
                ['correia do motor gasta', 'anodos de zinco do eixo', 'mangueiras e braçadeiras do motor'],
                'Além dos níveis, vale uma inspeção visual regular nas correias, mangueiras, braçadeiras e anodos, sempre com o motor parado e frio: peças gastas avisam antes de falhar. Correias: procure trincas, fiapos, partes brilhantes ou ressecadas, pressione com o dedo no meio do vão para ver se não cedem demais e troque ao primeiro sinal de desgaste, com uma sobressalente a bordo. Mangueiras e braçadeiras: procure ressecamento, rachaduras, inchaço, braçadeira enferrujada ou frouxa e marcas de óleo ou de sal seco em volta das conexões (sal cristalizado indica pingo de água salgada). Anodos de sacrifício (zinco, alumínio ou magnésio, conforme a água) corroem no lugar das peças de metal: confira o desgaste e troque o que estiver muito consumido. Os anodos do casco e do eixo são trocados com a limpeza do casco, a cada 6 meses pela agenda; peça à marina. Confira também a fixação do motor, os coxins e o escapamento: parafusos firmes e sem folga. Inspecione só com o motor parado e frio; com o motor ligado, mantenha mãos e roupas longe das correias.',
                a='Correias, mangueiras, braçadeiras e anodos, visual, com o motor parado e frio.', p=['Correias: procure trincas, partes brilhantes ou ressecadas; troque ao primeiro sinal de desgaste.', 'Mangueiras e braçadeiras: procure ressecamento, rachaduras, inchaço ou braçadeira frouxa.', 'Anodos de sacrifício: confira o desgaste e troque o que estiver muito consumido.', 'Anodos do casco e do eixo: trocados com a limpeza do casco, a cada 6 meses.', 'Confira a fixação do motor, os coxins e o escapamento.'], at='Inspecione só com o motor parado e frio.', se='Com o motor ligado, mantenha mãos e roupas longe das correias.', ver=('MO-07',)),
    # ——— Gerador ———
    'GE-01': _f('Antes de ligar o gerador', 'O que olho no gerador antes de ligar?',
                ['verificação do gerador antes da partida', 'gerador parado: o que checar', 'óleo e filtro de água salgada do gerador'],
                'Com o gerador parado, confira o nível de óleo e o líquido de arrefecimento, abra a válvula de fundo da entrada de água salgada e '
                'veja se o filtro de água salgada está limpo. Ligue a ventilação do compartimento por alguns minutos se houver cheiro de combustível.',
                a='Óleo, arrefecimento, válvula de fundo aberta e filtro limpo.', ver=('GE-02', 'CK-01')),
    'GE-02': _f('Ligar o gerador', 'Como ligo o gerador?',
                ['dar partida no gerador', 'passar as cargas para o gerador', 'ligar a climatização depois do gerador'],
                'No painel do gerador, segure PARTIDA até o motor pegar e espere a tensão e a frequência estabilizarem; só depois transfira as '
                'cargas, uma de cada vez, e ligue a climatização por último.',
                a='Segure PARTIDA no painel do gerador até o motor pegar.', ver=('GE-01', 'GE-03', 'GE-04')),
    'GE-03': _f('Água no escapamento do gerador', 'Como sei se o gerador está refrigerando?',
                ['gerador sem água no escapamento', 'saída de água do gerador', 'falta de refrigeração do gerador'],
                'Com o gerador ligado, a água tem de sair pelo escapamento. Sem água saindo, desligue na hora.',
                a='Sem água saindo pelo escapamento, desligue o gerador na hora.', p=[0], se=1, ver=('GE-05', 'CK-01')),
    'GE-04': _f('Desligar o gerador', 'Como desligo o gerador?',
                ['parar o gerador', 'retirar a carga e esfriar o gerador', 'fechar a válvula de fundo do gerador'],
                'Retire as cargas no quadro elétrico, deixe o gerador de 3 a 5 minutos sem carga para esfriar e pressione PARADA.',
                a='Retire as cargas, deixe esfriar e pressione PARADA.', ver=('GE-02', 'CK-04')),
    'GE-05': _f('Alarme de alta temperatura do gerador', 'O gerador deu alarme de temperatura alta, o que faço?',
                ['gerador esquentando', 'alarme de temperatura no gerador', 'gerador superaquecido'],
                'Desligue o gerador, verifique a válvula de fundo, o filtro de água salgada e o rotor (impeller) e registre o alarme no diário. '
                'Nunca abra a tampa do arrefecimento com o motor quente.',
                a='Desligue o gerador.', p=[0, 1, 3], at=2, ver=('GE-03', 'MO-05')),
    'GE-06': _f('Alarme de baixa pressão de óleo do gerador', 'O gerador deu alarme de pressão de óleo, o que faço?',
                ['gerador sem pressão de óleo', 'alarme de óleo no gerador', 'nível de óleo do gerador'],
                'Desligue o gerador e confira o nível de óleo com ele parado. Se o nível estiver correto e o alarme voltar, não religue e chame '
                'o técnico de bordo.',
                a='Desligue o gerador e confira o nível de óleo com ele parado.', p=[0], se=1),
    'GE-07': _f('Manutenção do gerador na agenda', 'Quando é a próxima troca de óleo e a inspeção do rotor do gerador?',
                ['troca de óleo e filtros do gerador', 'inspeção do rotor (impeller)', 'revisão do gerador na agenda'],
                [0, 1], p=[], ob=FAQ_AGENDA),
    'GE-08': _f('Horímetro do gerador', 'Onde vejo as horas de uso do gerador?',
                ['horas do gerador', 'quantas horas tem o gerador', 'horímetro do gerador na telemetria'], [0], p=[]),
    'GE-09': _f('Potência e carga do gerador', 'Quanta carga o gerador aguenta?',
                ['potência nominal do gerador', 'carga normal com a climatização ligada', 'carga acima do normal no gerador'],
                [0, 1, 2], p=[], se=3, ver=('GE-02',)),
    'GE-10': _f('Gerador não pega na partida', 'O gerador não pega, o que confiro?',
                ['gerador não liga', 'partida do gerador falhando', 'motor do gerador não pega'],
                'Se o motor do gerador não pegar na partida, espere um pouco entre as tentativas e confira o nível de óleo, o diesel '
                'nos tanques e a tensão do banco de baterias que alimenta a partida do gerador. Não ligue o gerador com a válvula de '
                'fundo da água salgada fechada: o rotor da bomba trabalha a seco e se danifica.',
                a='Espere entre as tentativas e confira óleo, diesel e a bateria de partida.',
                p=['Espere um pouco entre as tentativas de partida.', 'Confira o nível de óleo e o diesel nos tanques.',
                   'Confira a tensão do banco de baterias que alimenta a partida do gerador.'],
                at='Não ligue o gerador com a válvula de fundo fechada: o rotor da bomba trabalha a seco e se danifica.',
                ver=('GE-01', 'GE-02')),
    'GE-11': _f('Cuidados ao desligar o gerador', 'Posso desligar o gerador com carga ligada?',
                ['desligar o gerador com carga ligada', 'passar para a energia do cais', 'horímetro do gerador no diário'],
                'Em parada normal, nunca desligue o gerador com carga ligada: retire as cargas no quadro elétrico e deixe-o esfriar '
                'sem carga antes de pressionar PARADA. Só em alarme (sem água no escapamento ou temperatura alta) desligue na hora, '
                'mesmo com carga. Ao passar para a energia do cais, retire as cargas e desligue o gerador antes: nunca deixe as duas '
                'fontes ligadas ao mesmo tempo. Anote o horímetro do gerador no diário ao fim do uso.',
                a='Retire as cargas antes de desligar; nunca ligue as duas fontes (cais e gerador) juntas.',
                p=['Retire as cargas antes de pressionar PARADA; nunca desligue o gerador com carga ligada, salvo em alarme.',
                   'Ao ligar a energia do cais, desligue o gerador antes: nunca deixe as duas fontes ligadas juntas.',
                   'Anote o horímetro do gerador no diário ao fim do uso.'],
                at='Nunca desligue o gerador com carga ligada, exceto em alarme (sem água no escapamento ou temperatura alta).',
                ver=('GE-04',)),
    'GE-12': _f('Distribuição de cargas no gerador', 'Em que ordem ligo as cargas no gerador?',
                ['posso ligar a climatização e o resto ao mesmo tempo', 'qual é o limite de carga do gerador antes do aviso',
                 'o que posso ligar no gerador'],
                'O gerador entrega 9 kW a 60 Hz, com carga normal até 8,1 kW; acima disso é aviso. Antes de ligar uma carga, veja no '
                'painel ou no app a potência já em uso. Ligue as cargas no quadro elétrico uma de cada vez, esperando a tensão e a '
                'frequência estabilizarem entre elas, e deixe a climatização por último, porque ela pesa muito na carga. Cargas com '
                'motor ou compressor, como bombas e a própria climatização, puxam mais corrente na partida do que depois de '
                'funcionando; cargas de aquecimento elétrico, se houver, também pesam muito e não devem se somar à climatização. Se a '
                'carga passar de 8,1 kW, retire cargas no quadro, uma de cada vez.',
                a='Ligue as cargas uma de cada vez e deixe a climatização por último.',
                p=['Veja no painel ou no app a potência já em uso antes de ligar uma carga.',
                   'Ligue as cargas uma de cada vez e espere a tensão e a frequência estabilizarem.',
                   'Deixe a climatização por último.', 'Se a carga passar de 8,1 kW, retire cargas no quadro, uma de cada vez.'],
                at='Motor, compressor e climatização puxam mais corrente na partida do que depois de funcionando; cargas de '
                   'aquecimento pesam tanto quanto a climatização.',
                ver=('GE-09', 'GE-13')),
    'GE-13': _f('Sobrecarga do gerador', 'O disjuntor do gerador desarmou, e agora?',
                ['carga do gerador acima de 8,1 kW', 'gerador sobrecarregado: consequências', 'quais cargas tiro primeiro'],
                'O aviso de carga do gerador de 9 kW começa acima de 8,1 kW; a sobrecarga derruba a tensão e a frequência e pode '
                'desarmar o disjuntor ou parar o motor. Retire cargas no quadro elétrico, uma de cada vez, começando pelas '
                'dispensáveis (desligue a climatização se a carga continuar alta) e acompanhe o painel até a carga voltar para abaixo '
                'de 8,1 kW. Se o disjuntor desarmou, retire as cargas do quadro antes de rearmar e só então religue as cargas uma a '
                'uma, com intervalo, sem somar as maiores de uma vez; não rearme o disjuntor com as cargas ainda ligadas. Se o gerador '
                'parou por sobrecarga, retire todas as cargas antes de religá-lo e espere a tensão e a frequência estabilizarem. '
                'Registre no diário a hora e a carga que causou o aviso.',
                a='Retire cargas até voltar para abaixo de 8,1 kW; religue uma a uma, com intervalo.',
                p=['Retire cargas dispensáveis no quadro elétrico, uma de cada vez; desligue a climatização se a carga continuar '
                   'alta.', 'Acompanhe o painel até a carga voltar para abaixo de 8,1 kW.',
                   'Se o disjuntor desarmou, retire as cargas do quadro antes de rearmar; não rearme com as cargas ainda ligadas.',
                   'Religue as cargas uma a uma, com intervalo, sem somar as maiores de uma vez.',
                   'Registre no diário a hora e a carga que causou o aviso.'],
                at='Não rearme o disjuntor do gerador com as cargas ainda ligadas.',
                ver=('GE-12', 'GE-09')),
    'GE-14': _f('Gerador desligou sozinho ou perdeu rotação', 'O gerador caiu sozinho, o que faço?',
                ['por que o gerador desligou', 'o gerador está perdendo rotação', 'posso religar o gerador depois que ele desligou'],
                'O gerador desliga sozinho quando uma proteção atua (pressão de óleo baixa ou temperatura alta) ou quando falta '
                'combustível ou água de refrigeração; o painel costuma indicar o motivo. Retire todas as cargas no quadro elétrico '
                'antes de qualquer tentativa de religar; se ele só perdeu rotação e continua ligado, veja se estabiliza sem carga. '
                'Anote a mensagem ou o código do painel e a hora, antes de limpar o alarme, e confira o nível de óleo e do líquido de '
                'arrefecimento, a válvula de fundo aberta, o filtro de água salgada limpo e o diesel nos tanques. Corrigida a causa, '
                'religue sem carga, espere a tensão e a frequência estabilizarem e volte as cargas uma a uma; se parar de novo, ou se '
                'o alarme de temperatura ou de pressão de óleo voltar, não religue: chame o técnico de bordo. Nunca abra a tampa do '
                'arrefecimento com o gerador quente. Registre no diário a hora, a mensagem do painel e as cargas que estavam ligadas.',
                a='Retire as cargas, identifique a causa pelo painel e só religue sem carga.',
                p=['Retire todas as cargas no quadro elétrico antes de religar.',
                   'Anote a mensagem ou o código do painel e a hora, antes de limpar o alarme.',
                   'Confira óleo, arrefecimento, válvula de fundo, filtro de água salgada e diesel nos tanques.',
                   'Corrigida a causa, religue sem carga e volte as cargas uma a uma.',
                   'Se parar de novo ou o alarme voltar, não religue: chame o técnico de bordo.',
                   'Registre no diário a hora, a mensagem do painel e as cargas ligadas.'],
                at='Nunca abra a tampa do arrefecimento com o gerador quente.',
                se='Se parar de novo, ou se o alarme de temperatura ou de pressão de óleo voltar, não religue: chame o técnico de '
                   'bordo.',
                ver=('GE-05', 'GE-06', 'MO-05')),
    'GE-15': _f('Tensão ou frequência do gerador fora da faixa', 'A frequência do gerador está diferente de 60 Hz, o que é?',
                ['a tensão do gerador está oscilando, o que faço', 'posso ligar a eletrônica com a tensão fora da faixa',
                 'por que a frequência cai quando ligo uma carga'],
                'A frequência nominal do gerador é 60 Hz, com o motor a 1.800 rpm: quando a rotação cai, a frequência cai junto. '
                'Tensão e frequência instáveis costumam vir de sobrecarga ou de falha de combustível. Retire as cargas no quadro e '
                'veja a tensão e a frequência com o gerador sem carga; a frequência deve ficar em 60 Hz e a tensão no valor da placa '
                'do gerador. Se estiver normal sem carga e cair ao ligar uma carga, a causa é sobrecarga ou partida de carga pesada: '
                'retire cargas e religue uma a uma. Se continuar fora da faixa sem carga, não ligue no gerador carregadores nem '
                'equipamentos sensíveis, pois tensão ou frequência fora da faixa pode danificar esses aparelhos. Observe se a rotação '
                'oscila ou o motor falha, e confira o diesel nos tanques e, se houver filtro separador do gerador, a água acumulada '
                'nele. Não mexa por conta própria em ajuste de rotação, regulador ou tensão: a regulagem é do técnico de bordo. Se '
                'estabilizar, volte as cargas uma a uma e acompanhe o painel. Registre no diário a hora, os valores lidos de tensão e '
                'frequência e as cargas ligadas.',
                a='Confira sem carga: a frequência deve ficar em 60 Hz; fora da faixa, não ligue equipamentos sensíveis.',
                p=['Retire as cargas e veja a tensão e a frequência com o gerador sem carga.',
                   'Se normal sem carga e cair ao ligar uma carga, retire cargas e religue uma a uma.',
                   'Se continuar fora da faixa sem carga, não ligue carregadores nem equipamentos sensíveis.',
                   'Confira o diesel nos tanques e o filtro separador, se houver.',
                   'Não mexa por conta própria em ajuste de rotação, regulador ou tensão: chame o técnico de bordo.',
                   'Registre no diário a hora, os valores lidos e as cargas ligadas.'],
                at='Tensão ou frequência fora da faixa pode danificar carregadores e equipamentos sensíveis.',
                se='Se continuar fora da faixa sem carga, não ligue carregadores nem equipamentos sensíveis: chame o técnico de '
                   'bordo.',
                ver=('GE-02', 'GE-09')),
    'GE-16': _f('Óleo do gerador: nível, troca e alarme', 'Quando troco o óleo do gerador?',
                ['como confiro o óleo do gerador', 'alarme de pressão de óleo do gerador', 'quantas horas faltam para a revisão do '
                 'gerador'],
                'Confira o nível de óleo com o gerador parado, antes de ligar: com o gerador parado há alguns minutos e o barco '
                'nivelado, retire a vareta, limpe, encaixe de novo e leia entre as marcas de mínimo e máximo, completando só até a '
                'marca de máximo com o óleo que o manual do fabricante especifica. Procure óleo no compartimento em volta do gerador: '
                'pingos indicam vazamento. A troca de óleo e filtros vence aos 12 meses ou ao chegar a 1.300 h no horímetro, o que '
                'vier antes; acompanhe o horímetro do gerador no painel e na telemetria e combine a troca com o técnico de bordo antes '
                'do prazo vencer. Alarme de baixa pressão de óleo: desligue o gerador, confira o nível com ele parado e, se estiver '
                'correto e o alarme voltar, não religue. Depois da troca ou da complementação, confira o nível e procure vazamento '
                'com o gerador ligado e depois de parado.',
                a='Confira o nível parado; troque aos 12 meses ou 1.300 h no horímetro, o que vier antes.',
                p=['Com o gerador parado e o barco nivelado, retire a vareta, limpe, encaixe de novo e leia entre as marcas de mínimo '
                   'e máximo.', 'Complete só até a marca de máximo, com o óleo que o manual do fabricante especifica.',
                   'Procure óleo no compartimento em volta do gerador: pingos indicam vazamento.',
                   'Troque o óleo e os filtros aos 12 meses ou ao chegar a 1.300 h no horímetro, o que vier antes.',
                   'Alarme de baixa pressão de óleo: desligue o gerador e confira o nível com ele parado; se estiver correto e o '
                   'alarme voltar, não religue.',
                   'Depois da troca ou da complementação, confira o nível e procure vazamento com o gerador ligado e depois de '
                   'parado.'],
                at='Se o alarme de pressão de óleo voltar com o nível correto, não religue: chame o técnico de bordo.',
                ver=('GE-06', 'GE-07', 'GE-08')),
    'GE-17': _f('Rotor (impeller) do gerador', 'Como sei se o rotor do gerador está gasto?',
                ['quando inspeciono o rotor do gerador', 'como troco o rotor (impeller) do gerador',
                 'por que o gerador não joga água no escapamento'],
                'O rotor da bomba de água salgada garante a refrigeração do gerador: sem água no escapamento, desligue na hora. A '
                'agenda prevê inspeção a cada 12 meses e troca quando estiver gasto, com o técnico de bordo. Para inspecionar: '
                'desligue o gerador e o painel dele, para não haver partida acidental, feche a válvula de fundo da água salgada do '
                'gerador, abra a tampa da bomba, retire o rotor e procure palhetas gastas, trincadas, achatadas ou faltando. Se faltar '
                'pedaço, procure no circuito de água antes de religar; na dúvida, chame o técnico de bordo. Encaixe o rotor girando-o '
                'no sentido de giro da bomba, para as palhetas se dobrarem do jeito certo, e lubrifique como o manual do fabricante '
                'indica. Feche a tampa com junta em bom estado, abra a válvula de fundo e confira que não há vazamento, ligue o '
                'gerador e confirme a água saindo pelo escapamento. Registre a inspeção ou a troca no diário e confira se há rotor '
                'sobressalente a bordo.',
                a='Inspecione a cada 12 meses e troque quando as palhetas estiverem gastas, com o técnico de bordo.',
                p=['Desligue o gerador e o painel, para não haver partida acidental, e feche a válvula de fundo da água salgada do '
                   'gerador.', 'Abra a tampa da bomba, retire o rotor e procure palhetas gastas, trincadas, achatadas ou faltando.',
                   'Se faltar pedaço, procure no circuito de água antes de religar; na dúvida, chame o técnico de bordo.',
                   'Encaixe o rotor girando-o no sentido de giro da bomba e lubrifique como o manual do fabricante indica.',
                   'Feche a tampa com junta em bom estado, abra a válvula de fundo e confira que não há vazamento.',
                   'Ligue o gerador, confirme a água saindo pelo escapamento e registre a inspeção ou a troca no diário.'],
                at='O rotor não pode trabalhar a seco: nunca ligue o gerador com a válvula de fundo fechada.',
                se='Se faltar pedaço do rotor, procure-o no circuito de água antes de religar; na dúvida, chame o técnico de bordo.',
                ver=('GE-03', 'GE-07')),
    'GE-18': _f('Ventilação do compartimento do gerador', 'Por que ligo a ventilação antes do gerador?',
                ['o compartimento do gerador está quente, o que confiro', 'posso tapar as grades de ventilação',
                 'gases do escapamento do gerador'],
                'O gerador precisa de ar para queimar o combustível e para não esquentar o compartimento. Antes de ligar, deixe a '
                'ventilação do compartimento ligada por alguns minutos; se o compartimento ficou fechado por muito tempo, abra o '
                'acesso e deixe o ar renovar antes da partida. Com cheiro de combustível no compartimento, ventile bem e procure a '
                'origem antes de dar a partida. Mantenha as entradas e saídas de ar livres, sem pano, caixa nem outro objeto '
                'encostado nas grades, e confira a saída do escapamento do gerador sem obstrução. Os gases do escapamento são '
                'tóxicos: nunca deixe o gerador ligado com a saída obstruída ou com gases entrando nas cabines.',
                a='Ventile o compartimento antes de ligar e mantenha a saída do escapamento sempre livre.',
                p=['Antes de ligar, deixe a ventilação do compartimento ligada por alguns minutos.',
                   'Se o compartimento ficou fechado por muito tempo, abra o acesso e deixe o ar renovar antes da partida.',
                   'Com cheiro de combustível no compartimento, ventile bem e procure a origem antes de dar a partida.',
                   'Mantenha as entradas e saídas de ar livres e confira a saída do escapamento sem obstrução.'],
                at='Os gases do escapamento são tóxicos: nunca deixe o gerador ligado com a saída obstruída ou com gases entrando '
                   'nas cabines.',
                ver=('GE-01', 'GE-03')),
    # ——— Estabilizador (só o banco de 12 V, em corrente contínua) ———
    'SK-01': _f('Energia do estabilizador', 'De onde o estabilizador tira energia?',
                ['alimentação do Seakeeper', 'banco de 12 V do estabilizador', 'volante que não acelera'],
                [0], p=[1], se=2, ver=('SK-02', 'SK-06', 'EE-01')),
    'SK-02': _f('Ligar o estabilizador antes de sair', 'Como ligo o estabilizador antes de sair?',
                ['ligar o Seakeeper', 'esperar o estabilizador ficar pronto', 'rotação do volante no display'],
                'Ligue pelo display com antecedência, com o banco de 12 V carregado, e espere a indicação de que a estabilização está disponível '
                'antes de sair.',
                a='Ligue pelo display com antecedência e espere a indicação.', ver=('SK-01', 'SK-08', 'CK-01')),
    'SK-03': _f('Ligar e desligar a estabilização', 'Posso desligar o efeito do estabilizador sem parar o volante?',
                ['botão de estabilização', 'estabilizador na manobra de marina', 'desligar só a estabilização'], [0, 1], p=[]),
    'SK-04': _f('Desligar o estabilizador ao atracar', 'Como desligo o estabilizador ao chegar?',
                ['parar o Seakeeper', 'volante ainda girando depois de desligar', 'quando desligo o banco de 12 V'],
                'Desligue pelo display e mantenha o banco de 12 V ligado até o display indicar que o volante parou.',
                a='Desligue pelo display e mantenha o banco de 12 V ligado.', ver=('SK-05', 'CK-04')),
    'SK-05': _f('Segurança com o volante do estabilizador', 'Posso mexer no estabilizador com o volante girando?',
                ['manutenção do estabilizador', 'abrir tampas do Seakeeper', 'conferir que o volante parou'], [0, 1], p=[1]),
    'SK-06': _f('Alarmes e mensagens do estabilizador', 'O estabilizador mostrou uma mensagem de alarme, o que faço?',
                ['mensagem no display do Seakeeper', 'estabilizador com temperatura alta', 'tensão baixa no estabilizador'],
                [0], p=[1], ver=('SK-01', 'SK-08')),
    'SK-07': _f('Manutenção do estabilizador na agenda', 'Quando faço a manutenção do estabilizador?',
                ['anodo do trocador de calor', 'revisão anual do Seakeeper', 'troca do anodo do estabilizador'], [0, 1], p=[], ob=FAQ_AGENDA),
    'SK-08': _f('Faixa do volante do estabilizador', 'A partir de que rotação o estabilizador estabiliza?',
                ['rotação do volante do Seakeeper', 'volante abaixo do normal', 'quando o estabilizador começa a funcionar'],
                [0], p=[], se=1, ver=('SK-02', 'SK-06')),
    'SK-09': _f('Tempo de aceleração do volante do estabilizador', 'Quanto tempo o volante leva para acelerar?',
                ['Como sei que o estabilizador está pronto?', 'O volante não acelera, o que confiro?',
                 'Quanto tempo demora até a estabilização ficar disponível?'],
                'O volante leva algum tempo para chegar à rotação de trabalho; quem indica a hora de sair é o display, não um tempo '
                'fixo. Ligue o estabilizador pelo display com antecedência, com o carregador ligado ao gerador ou ao cais e o banco '
                'de 12 V na faixa normal, de 12,2 a 14,7 V, e acompanhe no display a rotação do volante subindo. A estabilização só '
                'fica disponível a partir de cerca de 85 % da rotação de operação: espere a indicação do display antes de sair. Se '
                'o volante não acelerar ou o display avisar tensão baixa, confira o banco de 12 V e o carregador.',
                a='Ligue com antecedência; é o display, não o relógio, que indica a hora de sair.',
                p=['Confirme o carregador ligado ao gerador ou ao cais e o banco de 12 V na faixa normal, de 12,2 a 14,7 V.',
                   'Ligue o estabilizador pelo display, com antecedência, antes de sair.',
                   'Acompanhe no display a rotação do volante subindo até a estabilização ficar disponível, a partir de cerca de 85 %.',
                   'Se o volante não acelerar ou o display avisar tensão baixa, confira o banco de 12 V e o carregador.'],
                at='Com tensão baixa no banco de 12 V, o volante não acelera.', ver=('SK-01', 'SK-02')),
    'SK-10': _f('Ativar e desativar a estabilização sem parar o volante',
                'Qual é a diferença entre desligar a estabilização e desligar o estabilizador?',
                ['Como ativo a estabilização depois de o volante acelerar?', 'Devo manter o estabilizador ativo na manobra de marina?',
                 'O botão de estabilização para o volante?'],
                'O botão de estabilização liga e desliga o efeito sem parar o volante, que segue girando; ative só quando o display '
                'indicar que a estabilização está disponível. Em manobra de marina, desative a estabilização se o display '
                'recomendar: o efeito volta quando for ativado de novo. O botão de estabilização não para o volante; para isso, '
                'desligue o estabilizador pelo display.',
                a='O botão liga e desliga o efeito; só o display para o volante de vez.',
                p=['Confirme no display que a estabilização está disponível antes de ativar o efeito.',
                   'Pressione o botão de estabilização para ativar; pressione de novo para desativar, sem parar o volante.',
                   'Em manobra de marina, desative a estabilização se o display recomendar.',
                   'Para parar o volante de vez, desligue o estabilizador pelo display, não só o botão de estabilização.'],
                at='Desligar só a estabilização não para o volante: ele continua girando.', ver=('SK-03', 'SK-09', 'SK-11')),
    'SK-11': _f('Desligar e esperar o volante parar', 'Quando posso cortar a energia do estabilizador?',
                ['O volante ainda gira depois de desligar, é normal?', 'Quanto tempo o volante demora para parar?',
                 'Como sei que o volante já parou de girar?'],
                'O volante continua girando por muito tempo depois de desligado: quem diz que ele parou é o display, não o relógio. '
                'Ao atracar, desligue o estabilizador pelo display e mantenha o banco de 12 V ligado enquanto o volante gira, sem '
                'cortar a energia antes da hora. Considere o equipamento parado só quando o display indicar a rotação em zero; só '
                'então desligue a energia do estabilizador ou faça qualquer serviço.',
                a='Desligue pelo display e mantenha o banco de 12 V ligado até a rotação chegar a zero.',
                p=['Ao atracar, desligue o estabilizador pelo display.',
                   'Mantenha o banco de 12 V ligado enquanto o volante gira; não corte a energia antes da hora.',
                   'Considere o equipamento parado só quando o display indicar a rotação em zero.',
                   'Só então desligue a energia do estabilizador ou faça qualquer serviço.'],
                ver=('SK-04', 'SK-05')),
    'SK-12': _f('Alarme de tensão baixa no banco de 12 V do estabilizador', 'O estabilizador avisou tensão baixa, o que faço?',
                ['Por que o volante do estabilizador não acelera?', 'O que fazer quando o banco de 12 V está fraco?',
                 'Qual é a tensão normal do banco de 12 V do estabilizador?'],
                'O estabilizador é alimentado pelo banco de 12 V, normal de 12,2 a 14,7 V; com tensão baixa, o display avisa e o '
                'volante não acelera. Leia a tensão no painel ou na telemetria: abaixo de 12,2 V é aviso e abaixo de 11,8 V é '
                'crítico. Ligue o carregador de bordo ao gerador ou ao cais para repor o banco e confira os bornes limpos e '
                'apertados. Se a tensão não subir com o carregador ligado, mantenha o estabilizador desligado e chame o técnico de '
                'bordo.',
                a='Ligue o carregador ao gerador ou ao cais para repor o banco de 12 V.',
                p=['Leia a tensão do banco de 12 V no painel ou na telemetria: abaixo de 12,2 V é aviso e abaixo de 11,8 V é crítico.',
                   'Ligue o carregador de bordo ao gerador ou ao cais para repor o banco.',
                   'Confira os bornes do banco de 12 V limpos e apertados.',
                   'Com a tensão normalizada, espere a indicação do display antes de acelerar o volante.',
                   'Se a tensão não subir com o carregador ligado, mantenha o estabilizador desligado e chame o técnico de bordo.'],
                at='Abaixo de 11,8 V é crítico: não acelere o volante até recuperar o banco.', ver=('SK-01', 'SK-06')),
    'SK-13': _f('Alarme de arrefecimento ou temperatura alta do estabilizador',
                'O estabilizador deu alarme de temperatura alta, o que faço?',
                ['Apareceu mensagem de arrefecimento no estabilizador, e agora?', 'O que confiro quando o estabilizador esquenta?',
                 'Posso continuar usando o estabilizador com a mensagem de arrefecimento?'],
                'Duas mensagens do display tratam da refrigeração do estabilizador: arrefecimento, que pede conferir a bomba e a '
                'válvula de fundo, e temperatura alta, que pede desligar e chamar o técnico. Na mensagem de arrefecimento, confira '
                'a válvula de fundo do estabilizador aberta e a bomba funcionando; se a mensagem continuar, trate como temperatura '
                'alta. Na mensagem de temperatura alta, desligue o estabilizador pelo display, mantenha o banco de 12 V ligado até '
                'o volante parar e chame o técnico de bordo; não religue antes de achar a causa.',
                a='Arrefecimento: confira a bomba e a válvula de fundo. Temperatura alta: desligue e chame o técnico.',
                p=['Anote a mensagem do display e a hora, antes de limpar o alarme.',
                   'Mensagem de arrefecimento: confira a válvula de fundo do estabilizador aberta e a bomba funcionando.',
                   'Se a mensagem de arrefecimento continuar, trate como temperatura alta.',
                   'Mensagem de temperatura alta: desligue o estabilizador pelo display, mantenha o banco de 12 V ligado até o '
                   'volante parar e chame o técnico de bordo.',
                   'Não religue antes de achar a causa; se a mensagem voltar, deixe o estabilizador desligado e chame o técnico.'],
                ver=('SK-06', 'SK-05')),
    'SK-14': _f('Volante do estabilizador abaixo de 85 %', 'O que significa volante abaixo de 85 %?',
                ['Por que o estabilizador não está estabilizando?', 'O volante caiu de rotação, o que faço?',
                 'O estabilizador acabou de ligar e não estabiliza, é normal?'],
                'O estabilizador só atua com o volante a partir de cerca de 85 % da rotação de operação; abaixo disso, o aviso '
                'indica que ainda não há estabilização. Se o estabilizador acabou de ser ligado, espere: o volante ainda está '
                'acelerando. Se o volante já estava pronto e a rotação caiu, confira o banco de 12 V e o carregador; se não voltar '
                'a acelerar, desligue o estabilizador pelo display e chame o técnico de bordo.',
                a='Abaixo de 85 % da rotação de operação, ainda não há estabilização.',
                p=['Leia no display a rotação do volante e a mensagem que acompanha o aviso.',
                   'Se o estabilizador acabou de ser ligado, espere o volante acelerar: a estabilização só fica disponível depois.',
                   'Se o volante já estava pronto e a rotação caiu, confira o banco de 12 V e o carregador.',
                   'Se o volante não voltar a acelerar, desligue o estabilizador pelo display e chame o técnico de bordo.'],
                ver=('SK-08', 'SK-06', 'SK-09')),
    'SK-15': _f('Manutenção do estabilizador: volante parado antes do serviço',
                'O que faço antes de qualquer serviço no estabilizador?',
                ['Quando troco o anodo do estabilizador?', 'Quem faz a manutenção do estabilizador?',
                 'Posso abrir o estabilizador com o volante girando?'],
                'O anodo do trocador de calor vence a cada 6 meses; a revisão anual é feita pelo técnico de bordo. Combine os dois '
                'com antecedência. Antes de qualquer serviço, desligue o estabilizador e espere o display indicar a rotação em '
                'zero, mantendo o banco de 12 V ligado até o volante parar. Depois do serviço, ligue o estabilizador e confira no '
                'display que não há mensagem de alarme.',
                a='Agende o anodo (6 meses) e a revisão anual; antes do serviço, volante parado.',
                p=['Consulte na agenda a data do anodo do trocador de calor, que vence a cada 6 meses.',
                   'Combine o anodo e a revisão anual com o técnico de bordo antes do vencimento.',
                   'Antes do serviço, desligue o estabilizador e espere o display indicar a rotação em zero.',
                   'Mantenha o banco de 12 V ligado até o volante parar.',
                   'Depois do serviço, ligue o estabilizador e confira no display que não há mensagem de alarme.',
                   'Registre no diário a data do serviço e o que foi trocado.'],
                ver=('SK-07', 'SK-05')),
    # ——— Climatização ———
    'CL-01': _f('Ligar a climatização', 'Como ligo o ar-condicionado?',
                ['ligar a climatização', 'ligar o ar da cabine', 'bomba de água salgada da climatização'],
                'Confira a válvula de fundo aberta e o filtro de água salgada limpo; com energia AC no quadro elétrico, ligue a bomba de água '
                'salgada no painel e depois o controle da cabine.',
                a='Válvula de fundo aberta, filtro limpo, bomba e depois o controle.', ver=('CL-03', 'CL-05', 'CK-01')),
    'CL-02': _f('Modos e temperatura da climatização', 'Como escolho frio, calor ou ventilação?',
                ['ajustar a temperatura da cabine', 'unidades de 16.000 e 12.000 BTU/h', 'ligar uma unidade de cada vez'], [0, 1], p=[], at=1),
    'CL-03': _f('Alarme de fluxo da climatização', 'A climatização deu alarme de fluxo ou de alta pressão, o que faço?',
                ['alarme de água salgada na climatização', 'ar-condicionado desligou por alarme', 'filtro de água salgada sujo'],
                [0], a='Desligue a unidade, limpe o filtro e religue.', p=[1], ver=('CL-01', 'CL-06')),
    'CL-04': _f('Pouco ar saindo na cabine', 'O ar da cabine está fraco, o que faço?',
                ['fluxo de ar fraco', 'limpar o filtro de ar da cabine', 'unidade da cabine com pouco ar'],
                [0], a='Limpe o filtro de ar da unidade daquela cabine.', p=[], se=1),
    'CL-05': _f('Desligar a climatização', 'Como desligo a climatização?',
                ['desligar o ar-condicionado', 'desligar a bomba de água salgada da climatização', 'fechar a válvula de fundo ao deixar o barco'],
                'Desligue pelo controle das cabines e depois a bomba de água salgada; ao deixar o barco, feche a válvula de fundo se a '
                'climatização não for usada.',
                a='Desligue as cabines e depois a bomba de água salgada.', ver=('CK-04',)),
    'CL-06': _f('Manutenção da climatização na agenda', 'Quando limpo o filtro de água salgada da climatização?',
                ['limpeza mensal do filtro', 'revisão anual da climatização', 'filtro de água salgada do ar-condicionado'],
                [0, 1], p=[], ob=FAQ_AGENDA),
    'CL-07': _f('Como a climatização usa a água salgada', 'Por que a climatização depende da água salgada circulando?',
                ['para que serve a válvula de fundo da climatização', 'por que preciso ligar a bomba antes do ar-condicionado',
                 'jato fraco na descarga do ar-condicionado'],
                'As três unidades Webasto trocam calor com a água do mar: a bomba de água salgada puxa a água pela válvula '
                'de fundo, ela passa pelo filtro e pelas unidades e sai pelo casco. Confira esse fluxo pela descarga no '
                'casco, que deve sair firme e contínua; jato fraco ou intermitente indica pouca água chegando à unidade. '
                'Sem esse fluxo, a unidade para por proteção; não insista em religar antes de resolver a causa do fluxo.',
                a='Confira a descarga no casco: o jato deve sair firme e contínuo.',
                p=['Confira a válvula de fundo aberta e o filtro de água salgada limpo, com a tampa bem fechada.',
                   'Ligue a bomba de água salgada antes de ligar o controle de qualquer cabine.',
                   'Olhe a descarga no casco: o jato deve sair firme e contínuo.',
                   'Com o jato fraco ou intermitente, desligue as unidades e procure a causa antes de religar.'],
                at='Sem esse fluxo, a unidade para por proteção; não insista em religar antes de resolver a causa do fluxo.',
                ver=('CL-01', 'CL-12')),
    'CL-08': _f('Ordem completa para ligar a climatização',
                'Qual é a ordem certa para ligar a climatização, da energia ao controle da cabine?',
                ['ligar o ar com o gerador ou no cabo de cais', 'fechar portas antes de ligar o ar-condicionado',
                 'esperar uma unidade estabilizar antes da próxima'],
                'A climatização só recebe comando depois que a energia AC está estável (gerador ligado com tensão estável '
                'ou cabo de cais conectado) e a água salgada circula; seguir essa ordem evita alarme de fluxo e '
                'sobrecarga no quadro elétrico. Confira a válvula de fundo aberta e a tampa do filtro de água salgada bem '
                'fechada, ligue a bomba de água salgada no painel e espere o jato contínuo na descarga do casco. Feche '
                'portas e escotilhas do ambiente para o ar climatizado não escapar, ligue o controle do salão ou de uma '
                'cabine, escolha o modo e ajuste a temperatura e a velocidade do ventilador. Espere a unidade partir e '
                'estabilizar antes de ligar a unidade seguinte; não ligue o controle de nenhuma unidade com a bomba de '
                'água salgada desligada. Com o gerador, a climatização entra por último, depois das outras cargas.',
                a='Energia AC estável e água salgada circulando antes do controle da cabine; uma unidade por vez.',
                p=['Confirme energia AC no quadro: gerador ligado com tensão estável ou cabo de cais conectado.',
                   'Confira a válvula de fundo aberta e a tampa do filtro de água salgada bem fechada.',
                   'Ligue a bomba de água salgada e espere o jato contínuo na descarga do casco.',
                   'Feche portas e escotilhas do ambiente, ligue o controle e escolha o modo.',
                   'Ajuste a temperatura e a velocidade do ventilador.',
                   'Espere a unidade estabilizar antes de ligar a unidade seguinte.'],
                at='Não ligue o controle de nenhuma unidade com a bomba de água salgada desligada; com o gerador, a '
                   'climatização entra por último.',
                ver=('CL-01', 'CL-11')),
    'CL-09': _f('Diferença entre frio, calor e ventilação',
                'Qual a diferença entre os modos frio, calor e ventilação da climatização?',
                ['usar só o ventilador do ar-condicionado', 'aquecer a cabine com a climatização',
                 'compressor demora para voltar ao trocar de modo'],
                'Em frio a unidade resfria, em calor aquece e em ventilação só circula o ar, sem esfriar nem aquecer e '
                'gastando bem menos energia. Ao trocar de modo pelo controle do ambiente, espere a unidade responder: o '
                'compressor pode levar alguns minutos para partir de novo. Confira no controle se o modo escolhido ficou '
                'ativo e se o ar de saída mudou.',
                a='Escolha frio, calor ou ventilação no controle do ambiente e espere o compressor responder.', p=[],
                ver=('CL-02', 'CL-10')),
    'CL-10': _f('Meta de temperatura e velocidade do ventilador',
                'A temperatura que ajusto no controle é a do ar que sai da unidade?',
                ['ajustar a temperatura da cabine', 'velocidade do ventilador para dormir',
                 'esperar antes de mudar a temperatura de novo'],
                'A temperatura ajustada é a meta da cabine, não a do ar que sai da unidade; metas muito distantes da '
                'temperatura ambiente fazem a unidade trabalhar sem parar. No controle da cabine, escolha a meta perto '
                'do conforto desejado e a velocidade do ventilador: mais alta para esfriar mais rápido, mais baixa para '
                'dormir com menos ruído. Espere alguns minutos antes de ajustar de novo, pois o ambiente demora a '
                'responder; fechar cortinas e escotilhas ajuda a unidade a manter a meta com menos esforço. Cada '
                'ambiente tem o próprio controle: ajuste só o da unidade que atende aquela cabine ou o salão.',
                a='Ajuste a meta de temperatura da cabine e a velocidade do ventilador no controle do ambiente.', p=[],
                at='Metas muito distantes da temperatura ambiente fazem a unidade trabalhar sem parar; espere alguns '
                   'minutos antes de ajustar de novo.',
                ver=('CL-02', 'CL-09')),
    'CL-11': _f('Carga da climatização no gerador ou no cais',
                'Posso ligar todos os ares-condicionados ao mesmo tempo no gerador?',
                ['climatização puxando o gerador', 'carga do ar-condicionado no cabo de cais',
                 'disjuntor desarma com o ar-condicionado ligado'],
                'A unidade de 16.000 BTU/h do salão e as duas de 12.000 BTU/h das cabines pesam na energia AC, seja o '
                'gerador de 9 kW ou o cabo de cais. Ligue as unidades sempre depois das outras cargas do quadro elétrico, '
                'uma de cada vez: a partida do compressor pode causar queda de tensão e desarmar o disjuntor, tanto no '
                'gerador quanto no cais. Acompanhe a carga no painel do gerador: o aviso dispara acima de 8,1 kW, e com '
                'a climatização ligada o normal fica entre 5,5 e 6,5 kW. Com a carga acima do aviso, retire cargas no '
                'quadro elétrico, uma de cada vez, até voltar ao normal.',
                a='No gerador ou no cabo de cais, ligue as unidades uma de cada vez, sempre depois das outras cargas.',
                p=['Ligue as unidades sempre depois das outras cargas do quadro elétrico, uma de cada vez.',
                   'No gerador ou no cabo de cais, espere o compressor de uma unidade partir antes de ligar a próxima.',
                   'Acompanhe a carga no painel do gerador: o aviso dispara acima de 8,1 kW.',
                   'Com a carga acima do aviso, retire cargas no quadro elétrico, uma de cada vez, até voltar ao '
                   'normal.'],
                ver=('GE-09', 'CL-01')),
    'CL-12': _f('Verificar o alarme de fluxo antes de religar',
                'O alarme de fluxo ou de alta pressão voltou depois que liguei de novo, o que verifico?',
                ['bomba ligada mas alarme continua', 'jato fraco na descarga com alarme de fluxo',
                 'alarme de fluxo depois de limpar o filtro'],
                'O alarme indica que a água salgada não passa pela unidade com a vazão necessária, e a unidade se '
                'protege parando; a causa quase sempre está no filtro, na válvula de fundo ou na bomba, não no '
                'aparelho. Desligue o controle da unidade em alarme para ela não trabalhar sem água, confira a bomba '
                'ligada no painel e a válvula de fundo aberta e olhe a descarga no casco: jato fraco, intermitente ou '
                'ausente confirma a falta de fluxo. Não force novas partidas com o alarme ativo: a unidade só volta a '
                'trabalhar com a água circulando. Se o alarme voltar depois de limpar o filtro, desligue, registre no '
                'diário a unidade e a hora e chame a marina.',
                a='Desligue a unidade em alarme, confira a bomba e a válvula de fundo e olhe a descarga no casco.',
                p=['Desligue o controle da unidade em alarme.',
                   'Confira a bomba de água salgada ligada no painel e a válvula de fundo aberta.',
                   'Olhe a descarga no casco: jato fraco, intermitente ou ausente confirma a falta de fluxo.',
                   'Sem fluxo depois de limpar o filtro, desligue, registre no diário e chame a marina.'],
                at='Não force novas partidas com o alarme ativo: a unidade só volta a trabalhar com a água circulando.',
                ver=('CL-03', 'CL-13', 'CL-01')),
    'CL-13': _f('Limpar o filtro de água salgada passo a passo', 'Como limpo o filtro de água salgada da climatização?',
                ['abrir a tampa do filtro com a válvula de fundo aberta', 'trocar o anel de vedação do filtro',
                 'religar a bomba depois de limpar o filtro'],
                'O filtro retém algas, lodo e cracas antes da bomba e das unidades; a agenda prevê a limpeza mensal, a '
                'cargo da marina, mas o alarme de fluxo antes do prazo também pede essa limpeza. Desligue os controles '
                'de todas as unidades, espere o ventilador parar, desligue a bomba de água salgada e só então feche a '
                'válvula de fundo antes de abrir qualquer tampa. Abra a tampa do filtro, retire a tela e lave em água '
                'doce, tirando lodo, algas e cracas; confira a tela sem furos nem deformação e o anel de vedação da '
                'tampa, e troque o que estiver danificado. Recoloque a tela, feche a tampa com firmeza, abra a válvula '
                'de fundo e confira que a tampa não pinga; ligue a bomba, confirme o jato contínuo na descarga do casco '
                'e só então ligue os controles. Nunca abra o filtro com a válvula de fundo aberta: a água do mar sai '
                'pela tampa. Registre a limpeza do filtro no diário.',
                a='Desligue tudo, feche a válvula de fundo, lave a tela do filtro em água doce e só então reabra e '
                  'religue.',
                p=['Desligue os controles de todas as unidades, espere o ventilador parar e desligue a bomba de água '
                   'salgada.',
                   'Feche a válvula de fundo antes de abrir qualquer tampa.',
                   'Abra a tampa, retire a tela e lave em água doce; confira a tela e o anel de vedação e troque o que '
                   'estiver danificado.',
                   'Recoloque a tela, feche a tampa, abra a válvula de fundo e confira que não pinga.',
                   'Ligue a bomba, confirme o jato contínuo e só então ligue os controles; registre a limpeza no '
                   'diário.'],
                at='Nunca abra o filtro com a válvula de fundo aberta: a água do mar sai pela tampa.',
                ob=FAQ_AGENDA, ver=('CL-06', 'CL-12', 'CL-03')),
    'CL-14': _f('Ar-condicionado ligado sem esfriar a cabine',
                'O ar-condicionado está ligado, mas a cabine não esfria, o que confiro?',
                ['ar-condicionado liga mas sai ar quente', 'cabine demora para esfriar',
                 'gelo na unidade do ar-condicionado'],
                'Cabine quente com a unidade ligada tem poucas causas comuns: modo ou meta errados, ar bloqueado, '
                'falta de água salgada ou energia fraca; confira na ordem mais simples até a mais trabalhosa. No '
                'controle, confirme o modo frio e a meta abaixo da temperatura atual da cabine, feche escotilhas e '
                'portas do ambiente e veja se o ventilador não está em velocidade baixa. Limpe o filtro de ar da '
                'unidade e libere as grades de entrada e de saída do ar; confirme o jato firme na descarga do casco e, '
                'se estiver fraco, siga o procedimento do alarme de fluxo. Confira no painel se a energia AC está '
                'estável e se o disjuntor da unidade está ligado; havendo gelo ou muita condensação na unidade, passe '
                'para ventilação até derreter e revise o filtro de ar. Não abra a unidade nem mexa no circuito de '
                'refrigeração: isso é serviço da marina. Persistindo a falha, registre no diário a cabine, a hora e o '
                'que foi conferido, e chame a marina.',
                a='Confira modo e meta, portas e filtro de ar, depois a água salgada e a energia, da causa mais '
                  'simples à mais trabalhosa.',
                p=['Confirme o modo frio e a meta abaixo da temperatura atual da cabine.',
                   'Feche escotilhas e portas do ambiente e confira a velocidade do ventilador.',
                   'Limpe o filtro de ar e libere as grades de entrada e saída do ar.',
                   'Confirme o jato firme na descarga do casco; se estiver fraco, siga o procedimento do alarme de '
                   'fluxo.',
                   'Confira a energia AC estável e o disjuntor da unidade ligado.',
                   'Com gelo ou muita condensação, passe para ventilação até derreter e revise o filtro de ar.'],
                at='Não abra a unidade nem mexa no circuito de refrigeração: isso é serviço da marina.',
                se='Persistindo a falha, registre no diário a cabine, a hora e o que foi conferido, e chame a marina.',
                ver=('CL-04', 'CL-12', 'CL-15')),
    'CL-15': _f('Limpar o filtro de ar da unidade', 'Como limpo o filtro de ar da unidade de climatização?',
                ['ar fraco saindo da cabine', 'filtro de ar sujo da unidade', 'gelo na serpentina por falta de limpeza'],
                'O filtro de ar fica na entrada de cada unidade e junta poeira, fiapos e pelos; entupido, deixa sair '
                'pouco ar, a cabine esfria mal e a serpentina pode formar gelo. Desligue o controle da unidade daquela '
                'cabine, abra o acesso ao filtro (grade ou painel de acesso) e puxe o filtro; aspire a poeira ou lave '
                'em água doce com sabão neutro e deixe secar por completo antes de recolocar. Recoloque o filtro e a '
                'grade, ligue o controle e compare o fluxo de ar na saída. Nunca ligue a unidade sem o filtro de ar: a '
                'poeira vai para a serpentina. Persistindo o fluxo fraco, registre no diário a cabine e a hora e chame '
                'a marina.',
                a='Desligue a unidade, retire o filtro de ar, lave e deixe secar por completo antes de recolocar.',
                p=['Desligue o controle da unidade daquela cabine.',
                   'Abra o acesso ao filtro de ar e puxe o filtro.',
                   'Aspire a poeira ou lave o filtro em água doce com sabão neutro e deixe secar por completo.',
                   'Recoloque o filtro e a grade e compare o fluxo de ar na saída.'],
                at='Nunca ligue a unidade sem o filtro de ar: a poeira vai para a serpentina.',
                se='Persistindo o fluxo fraco, registre no diário a cabine e a hora e chame a marina.',
                ver=('CL-04', 'CL-14')),
    'CL-16': _f('Preparar a climatização antes de deixar o barco',
                'Preciso fazer algo na climatização antes de deixar o barco parado por vários dias?',
                ['secar a umidade da cabine antes de fechar o barco', 'ordem para desligar a climatização',
                 'a bomba de água salgada não pode puxar sem água'],
                'Desligue na ordem inversa da partida: primeiro as unidades, depois a bomba de água salgada; com o '
                'barco parado por vários dias, feche a válvula de fundo para não deixar o circuito aberto ao mar. Se '
                'for deixar o barco fechado, rode as unidades só em ventilação por alguns minutos para secar a '
                'umidade interna antes de desligar cada cabine e o salão. Espere o ventilador parar e só então '
                'desligue a bomba de água salgada no painel; a bomba não pode puxar sem água. Com a bomba desligada, '
                'feche a válvula de fundo se a climatização não for usada nos próximos dias e confira a tampa do '
                'filtro de água salgada bem fechada. Registre no diário qualquer alarme ou comportamento estranho '
                'durante o uso.',
                a='Desligue as unidades, depois a bomba, e feche a válvula de fundo se não for usar nos próximos dias.',
                p=['Rode as unidades só em ventilação por alguns minutos para secar a umidade interna, se for deixar '
                   'o barco fechado.',
                   'Desligue o controle de cada cabine e do salão.',
                   'Espere o ventilador parar e só então desligue a bomba de água salgada.',
                   'Feche a válvula de fundo se a climatização não for usada nos próximos dias e confira a tampa do '
                   'filtro bem fechada.'],
                at='Espere o ventilador parar e só então desligue a bomba de água salgada: ela não pode puxar sem '
                   'água.',
                ver=('CL-05', 'CK-04')),
    # ——— Eletrônicos e rádios ———
    'EL-01': _f('Marcar homem ao mar no plotter', 'Como marco um homem ao mar no plotter?',
                ['função MOB do plotter', 'alguém caiu na água: o que faço no plotter', 'rumo de volta para quem caiu'],
                [0], a='Acione a função MOB do plotter.', p=[1], ver=('EM-04',), eq=equip_de('eletronicos')),
    'EL-02': _f('Piloto automático: espera e engate', 'Quando deixo o piloto automático em espera?',
                ['piloto em standby', 'engatar o piloto automático', 'piloto ao manobrar na marina'],
                [0, 1], p=[0, 1], ver=('PI-01', 'PI-02', 'CK-04'), eq=equip_de('piloto')),
    'EL-03': _f('Alarme de âncora no plotter', 'Como ativo o alarme de âncora?',
                ['raio do alarme de âncora', 'ativar o alarme ao fundear', 'contador de corrente e alarme de âncora'],
                'Ative o alarme de âncora no plotter ao fundear e defina o raio conforme a corrente lançada.',
                a='Ative o alarme no plotter e defina o raio pela corrente lançada.', ver=('AN-02', 'CK-07'), eq=equip_de('eletronicos')),
    'EL-04': _f('Rádio VHF: escuta do canal 16', 'Qual canal fica em escuta no rádio VHF?',
                ['escuta permanente do canal 16', 'dupla escuta do VHF', 'rádio portátil carregado'],
                'Mantenha o canal 16 em escuta permanente no rádio fixo; a dupla escuta acompanha o canal 16 e um canal de trabalho ao mesmo tempo.',
                a='Rádio fixo em escuta permanente no canal 16.', ver=('EL-05', 'CK-02'), eq=equip_de('vhf')),
    'EL-05': _f('Rádio VHF: botão DISTRESS (DSC)', 'Para que serve o botão DISTRESS do rádio?',
                ['alerta DSC do rádio VHF', 'identificação do rádio no alerta de socorro', 'depois do botão DISTRESS, o que faço'],
                [0, 1], a='Depois do DISTRESS, faça o MAYDAY por voz no canal 16.', p=[1], ver=('EM-03', 'EM-01'), eq=equip_de('vhf')),
    'EL-06': _f('Áudio Fusion: parear o celular', 'Como pareio o celular no som do barco?',
                ['Bluetooth do Fusion', 'conectar o celular ao áudio', 'volume por zona do áudio'],
                'No controle Fusion, escolha a fonte Bluetooth, deixe o celular visível e selecione o Fusion na lista de Bluetooth do celular.',
                a='Fonte Bluetooth no controle Fusion e Fusion na lista do celular.',
                p=['Escolha a fonte Bluetooth no controle Fusion.', 'Deixe o aparelho visível.', 'Selecione o Fusion na lista de Bluetooth do celular.'],
                ob=1, eq=equip_de('audio')),
    'EL-07': _f('Atualização de cartas e software', 'Com que frequência atualizo as cartas e o software dos plotters?',
                ['atualização anual dos plotters', 'software do radar e do áudio', 'cartas náuticas do plotter'], [0], p=[], eq=equip_de('eletronicos')),
    'EL-08': _f('Profundidade mínima na sonda', 'Qual a profundidade mínima para navegar?',
                ['alarme de profundidade da sonda', 'água rasa: o que faço', 'sonda mostrando pouca profundidade'],
                [0, 1], a='Abaixo do mínimo: reduza a velocidade, confira a carta e mude de rumo.',
                p=['Reduza a velocidade.', 'Confira a carta no plotter.', 'Mude de rumo para águas mais fundas.'], ver=('CK-07',), eq=equip_de('eletronicos')),
    'EL-09': _f('Gestos na tela e barra de menu do plotter', 'Como eu mexo na tela do plotter (zoom, arrastar, selecionar)?',
                ['ícones da barra de menu', 'travar a tela do plotter', 'abrir Go To, Route To ou Auto Guidance'],
                'O plotter é operado por toque na tela, com gestos para mover e dar zoom na carta, e por uma barra de menu fixa na parte de baixo '
                'da tela. Na barra de menu: um ícone marca um waypoint na posição atual, outro abre a navegação até um ponto (Go To, Route To ou '
                'Auto Guidance), e outro volta à tela inicial ou abre as opções da tela aberta. Para travar a tela e evitar toques por engano, use '
                'a opção de travar no menu; um ícone de cadeado aparece para destravar.',
                a='Toque para selecionar, arraste para mover e pince ou espalhe os dedos para o zoom.',
                p=['Toque para selecionar; arraste para mover a carta.',
                   'Pince os dedos para afastar o zoom e espalhe para aproximar.',
                   'Na barra de menu: waypoint na posição atual, navegação até um ponto, tela inicial e opções.',
                   'Para travar a tela, use a opção de travar no menu; toque no cadeado para destravar.'],
                eq=equip_de('eletronicos')),
    'EL-10': _f('Fixar e reorganizar atalhos no plotter', 'Como eu deixo a carta de navegação de um toque na tela inicial do plotter?',
                ['remover um atalho fixado', 'mudar a ordem dos atalhos', 'atalhos definidos pelo estaleiro'],
                'A categoria de favoritos reúne os recursos usados com frequência, como uma carta ou um medidor, para abrir em um só toque a '
                'partir da tela inicial; os atalhos fixados podem ser reorganizados ou removidos a qualquer momento. Um plotter que já vem com '
                'atalhos definidos pelo estaleiro nessa categoria não permite editá-los.',
                a='Mantenha o dedo sobre o recurso e escolha fixar; os atalhos fixados abrem em um toque.',
                p=['Abra a categoria do recurso que você quer fixar.',
                   'Mantenha o dedo sobre o recurso até abrir o menu e escolha fixar.',
                   'Os atalhos fixados ficam numa categoria própria, acessível em um toque.',
                   'Para tirar ou reorganizar um atalho, mantenha o dedo sobre ele e escolha a opção correspondente.'],
                eq=equip_de('eletronicos')),
    'EL-11': _f('Páginas combinadas e layout SmartMode no plotter', 'Como eu crio uma tela com várias funções juntas no plotter?',
                ['layout SmartMode para cruzeiro ou atracação', 'apagar uma página combinada', 'SmartMode em mais de um display'],
                'O plotter permite montar telas próprias: uma página combinada junta funções em janelas fixas na mesma tela, e um layout do tipo '
                'SmartMode agrupa telas pensadas para uma atividade, como cruzeiro ou atracação. Numa estação com mais de um display, o nome e o '
                'símbolo do layout SmartMode aparecem em todos os displays; o resto da personalização vale só para o display em uso.',
                a='Monte uma página combinada com janelas fixas, ou um layout SmartMode para uma atividade.',
                p=['Para uma página combinada, escolha as janelas e a função de cada uma e dê um nome à página.',
                   'Para um layout SmartMode, escolha o nome, o símbolo e quantas funções aparecem em cada parte da tela.',
                   'Para apagar uma página combinada, mantenha o dedo sobre ela e confirme a exclusão.'],
                eq=equip_de('eletronicos')),
    'EL-12': _f('Para que serve o ActiveCaptain no plotter', 'O que o aplicativo ActiveCaptain faz no plotter?',
                ['atualizar cartas pelo ActiveCaptain', 'transferir waypoints pelo celular', 'comunidade ActiveCaptain'],
                'O ActiveCaptain é o aplicativo que liga o celular ao plotter para baixar ou comprar cartas, atualizar o software, transferir '
                'waypoints e rotas entre os dois, e planejar a viagem. As informações enviadas por outros usuários na comunidade ActiveCaptain '
                'não têm precisão garantida pelo fabricante.',
                p=[], eq=equip_de('eletronicos'), ver=('EL-13', 'EL-14')),
    'EL-13': _f('Conectar o celular ao plotter por Wi-Fi (ActiveCaptain)', 'Como eu conecto o celular ao plotter para usar o ActiveCaptain?',
                ['distância do celular até o plotter no ActiveCaptain', 'cartão de memória do ActiveCaptain', 'senha da rede Wi-Fi do plotter'],
                'A ligação por Wi-Fi entre o celular e o plotter é o que permite ao ActiveCaptain transferir cartas, software e dados do usuário. '
                'No plotter, ative a rede Wi-Fi do ActiveCaptain e defina um nome e uma senha para ela; no celular, instale o aplicativo '
                'ActiveCaptain e aproxime-o a até 32 m do plotter para conectar pela rede Wi-Fi criada. Formatar o cartão de memória do '
                'ActiveCaptain apaga os dados salvos nele; copie waypoints e rotas para a memória interna do plotter antes de formatar.',
                a='Ative a rede Wi-Fi do ActiveCaptain no plotter e conecte o celular a até 32 m.',
                p=['No plotter, ative a rede Wi-Fi do ActiveCaptain com um nome e uma senha.',
                   'No celular, instale o aplicativo ActiveCaptain.',
                   'Aproxime o celular a até 32 m do plotter e conecte pela rede Wi-Fi criada.',
                   'Antes de formatar o cartão de memória do ActiveCaptain, copie waypoints e rotas para a memória interna do plotter.'],
                eq=equip_de('eletronicos'), ver=('EL-12', 'EL-14')),
    'EL-14': _f('Notificações do celular na tela do plotter', 'Como eu recebo chamadas e mensagens do celular na tela do plotter?',
                ['parear o celular por Bluetooth no plotter', 'distância para parear a notificação no plotter', 'desligar os avisos de notificação do plotter'],
                'Com o Bluetooth do celular pareado ao plotter pelo ActiveCaptain, chamadas e mensagens do celular aparecem em um aviso rápido na '
                'tela do plotter; aproxime os dois aparelhos a até 10 m para parear. Não leia nem responda notificações enquanto estiver no '
                'comando da embarcação.',
                a='Pareie o celular por Bluetooth a até 10 m e escolha as notificações no celular.',
                p=['No plotter, ative as notificações inteligentes do ActiveCaptain.',
                   'Ligue o Bluetooth do celular e aproxime os dois aparelhos a até 10 m para parear.',
                   'No celular, escolha quais notificações aparecem no plotter.'],
                eq=equip_de('eletronicos'), ver=('EL-12', 'EL-13')),
    'EL-15': _f('Tipos de carta e vistas 3D do plotter', 'Quais tipos de carta o plotter oferece?',
                ['diferença entre carta de navegação e carta de pesca', 'vista submersa em 3D do fundo', 'cartas premium no plotter'],
                'O plotter mostra a carta de navegação padrão, uma carta de pesca com destaque para o relevo do fundo, e vistas em três dimensões '
                '(3D), de cima e por detrás do barco ou submersa, com alvos da sonda em esferas coloridas. A carta de pesca, as vistas 3D e o '
                'sombreamento do relevo só aparecem em áreas cobertas por cartas premium.',
                p=[], eq=equip_de('eletronicos')),
    'EL-16': _f('Camadas da carta: mostrar ou esconder informações no plotter', 'Como eu escondo ou mostro informações na carta do plotter?',
                ['camadas que precisam de cartas premium', 'mostrar waypoints e trilhas salvas', 'ajustar a trilha do barco na carta'],
                'O menu de camadas da carta liga e desliga grupos de informação, como fotos de satélite, pontos de serviço em terra, sinalizações '
                'náuticas e os dados de outras embarcações; algumas camadas só funcionam com cartas premium ou com um acessório conectado, como '
                'um receptor de AIS. Nele também se ajusta a linha de rumo e a trilha do próprio barco, e se mostra ou esconde waypoints, limites '
                'e trilhas salvos.',
                a='Ligue ou desligue cada grupo de informação no menu de camadas da carta.',
                p=['Abra o menu de camadas de uma carta.',
                   'Ligue ou desligue fotos de satélite, pontos de serviço, sinalizações náuticas e os dados de outras embarcações.',
                   'Ajuste a linha de rumo e a trilha do barco.',
                   'Mostre ou esconda waypoints, limites e trilhas salvos.'],
                eq=equip_de('eletronicos')),
    'EL-17': _f('Dar zoom e medir distância na carta do plotter', 'Como eu meço a distância entre dois pontos na carta?',
                ['zoom com os dedos na carta', 'alfinete de medição do plotter', 'mudar o ponto de referência da medição'],
                'O zoom da carta é feito com dois dedos na tela: pince para afastar e espalhe para aproximar. Para medir, toque num ponto e '
                'escolha a ferramenta de medir; um alfinete marca a posição atual e a distância e o ângulo até o cursor aparecem no canto da '
                'tela, e um novo ponto de referência pode ser escolhido para medir de novo.',
                a='Pince ou espalhe os dedos para o zoom; toque e escolha medir para ver distância e ângulo.',
                p=['Pince os dedos para afastar o zoom; espalhe para aproximar.',
                   'Toque num ponto da carta e escolha a ferramenta de medir.',
                   'Leia a distância e o ângulo no canto da tela.',
                   'Para medir a partir de outro ponto, mova o cursor até lá e defina a nova referência.'],
                eq=equip_de('eletronicos')),
    'EL-18': _f('Ver informações de um local na carta', 'Como eu vejo informações de maré ou corrente de um ponto da carta?',
                ['criar um waypoint direto na carta', 'serviços próximos marcados na carta', 'dados astronômicos de um ponto da carta'],
                'Ao tocar num ponto ou objeto da carta, o plotter deixa criar um waypoint ali ou abrir mais informações do local, como maré, '
                'corrente, dados astronômicos, notas da carta ou serviços próximos.',
                a='Toque num ponto da carta para criar um waypoint ou ver maré, corrente e serviços do local.',
                p=['Toque num local ou objeto da carta.',
                   'Para criar um waypoint ali, escolha a opção de waypoint.',
                   'Para ver mais dados, abra as informações do local: maré, corrente, dados astronômicos, notas da carta ou serviços próximos.'],
                eq=equip_de('eletronicos')),
    'EL-19': _f('Ver detalhes de uma sinalização marcada na carta', 'Como eu vejo os detalhes de uma luz ou sinalização marcada na carta?',
                ['detalhes de uma obstrução na carta', 'sinalização náutica na vista 3D', 'nome de uma marca de navegação na carta'],
                'Marcas de navegação, luzes e obstruções indicadas na carta podem ser tocadas para abrir o nome e os detalhes de cada uma, também numa vista em 3D.',
                a='Toque no símbolo na carta (ou na vista 3D) e escolha o nome para ver os detalhes.',
                p=['Toque no símbolo da marca de navegação, da luz ou da obstrução, na carta ou numa vista 3D.',
                   'Escolha o nome que aparece na lista.',
                   'Leia os detalhes mostrados.'],
                eq=equip_de('eletronicos')),
    'EL-20': _f('Marcar um waypoint no plotter', 'Como eu marco a posição atual do barco como um waypoint?',
                ['criar waypoint por coordenada', 'waypoint por distância e direção', 'waypoint em um ponto da carta'],
                'Um waypoint grava uma posição para visitar depois: pode ser a posição atual do barco, um ponto escolhido direto na carta, ou um '
                'ponto definido por coordenada, ou por distância e direção a partir de uma referência.',
                a='Marque a posição atual, ou crie um waypoint pela carta, por coordenada ou por distância e direção.',
                p=['Para marcar a posição atual, use a opção de marcar em qualquer tela.',
                   'Para criar em outro local, abra a lista de waypoints e escolha criar um novo.',
                   'Escolha criar pela carta, por coordenada, ou por distância e direção a partir de um ponto de referência.'],
                eq=equip_de('eletronicos'), ver=('EL-21',)),
    'EL-21': _f('Editar, mover ou apagar um waypoint salvo', 'Como eu mudo o nome ou a posição de um waypoint salvo?',
                ['apagar todos os waypoints salvos', 'mover um waypoint para outra posição', 'lista de waypoints salvos no plotter'],
                'Um waypoint salvo pode ter o nome, o símbolo, a posição, a profundidade ou o comentário alterados, e pode ser apagado, um por '
                'vez ou todos de uma vez, quando não for mais necessário.',
                a='Escolha o waypoint salvo para editar, mover ou apagar; dá para apagar todos de uma vez.',
                p=['Abra a lista de waypoints salvos.',
                   'Para editar, escolha o waypoint e altere nome, símbolo, posição, profundidade ou comentário.',
                   'Para mover, escolha a nova posição: coordenada, ponto na carta, posição atual do barco, ou distância e direção.',
                   'Para apagar, escolha o waypoint e confirme; para apagar todos de uma vez, use a opção de apagar todos os waypoints.'],
                eq=equip_de('eletronicos'), ver=('EL-20',)),
    'EL-22': _f('Go To, Route To ou Auto Guidance: qual usar', 'Qual a diferença entre Go To, Route To e Auto Guidance no plotter?',
                ['plotter desviar de obstáculos sozinho', 'piloto automático seguir uma rota sozinho', 'Auto Guidance só em cartas premium'],
                'O plotter chega a um destino de três formas: em linha reta direto ao ponto (Go To), por uma linha reta com curvas marcadas à mão '
                'para desviar de obstáculos (Route To), ou por um caminho já calculado pelo próprio plotter, desviando de terra e de obstáculos '
                'conhecidos (Auto Guidance, disponível só com cartas premium compatíveis, em algumas áreas). Para o piloto automático seguir o '
                'caminho sozinho, a rota precisa ser de Auto Guidance.',
                p=[], eq=equip_de('eletronicos'), ver=('EL-23', 'EL-25')),
    'EL-23': _f('Ir direto a um ponto e parar a navegação', 'Como eu paro a navegação no meio do caminho?',
                ['linha direta até um destino no plotter', 'rumo corrigido ao sair da rota', 'linha do Go To sobre terra ou água rasa'],
                'Depois de escolher um destino na carta ou pela busca, o plotter traça uma linha direta até ele; uma linha fina no meio dela '
                'mostra o rumo corrigido, se o barco saiu da rota. A navegação pode ser interrompida a qualquer momento, pela opção de parar a '
                'navegação. A linha direta pode passar sobre terra ou água rasa: confira visualmente antes de seguir.',
                a='Escolha o destino e siga a linha direta; use parar a navegação para interromper.',
                p=['Escolha um destino na carta ou pela busca.',
                   'Siga a linha direta até o destino, observando visualmente água livre e obstáculos.',
                   'Se sair da rota, a linha fina no meio mostra o rumo corrigido.',
                   'Para parar, use a opção de parar a navegação.'],
                eq=equip_de('eletronicos'), ver=('EL-22',)),
    'EL-24': _f('Criar e salvar uma rota com curvas', 'Como eu crio uma rota com curvas para desviar de obstáculos?',
                ['salvar uma rota no plotter', 'editar as curvas de uma rota salva', 'limite de curvas de uma rota'],
                'Uma rota junta vários pontos de curva entre a partida e o destino, para desviar de obstáculos no caminho; pode ser criada já '
                'para navegar, sem salvar, ou salva para usar depois e editar mais tarde. Uma rota aceita até 250 curvas.',
                a='Marque as curvas na ordem do percurso; a rota aceita até 250 curvas e pode ser salva.',
                p=['Toque em cada curva, na ordem do percurso, para marcar a rota.',
                   'Para navegar já, sem salvar, basta seguir a rota marcada.',
                   'Para salvar, dê um nome à rota; para editar depois, abra a lista de rotas salvas.',
                   'Uma rota aceita até 250 curvas.'],
                eq=equip_de('eletronicos'), ver=('EL-22', 'EL-25')),
    'EL-25': _f('Seguir um caminho por Auto Guidance', 'O que significam as cores da linha no Auto Guidance?',
                ['Auto Guidance garante água livre', 'ativar o Auto Guidance até um destino', 'trecho cinza do Auto Guidance'],
                'O Auto Guidance calcula um caminho sugerido até o destino a partir dos dados da carta, como profundidade e obstáculos '
                'conhecidos; revise o caminho antes de seguir. Um trecho laranja indica cautela, perto dos limites configurados; um trecho '
                'vermelho listrado indica um trecho possivelmente inseguro; um trecho cinza indica que o plotter não conseguiu calcular aquele '
                'trecho com segurança, e é preciso escolher outro caminho ali. As linhas do Auto Guidance são uma referência geral, não uma '
                'garantia de água livre: confira sempre os sinais de navegação e as condições da água antes de seguir.',
                a='Revise o caminho sugerido; cores diferentes na linha indicam cautela ou um trecho inseguro.',
                p=['Escolha o destino e peça o caminho por Auto Guidance.',
                   'Revise o caminho sugerido antes de seguir.',
                   'Siga a linha, desviando de terra e água rasa por observação visual.',
                   'Trecho laranja: cautela; trecho vermelho listrado: possivelmente inseguro; trecho cinza: escolha outro caminho ali.'],
                eq=equip_de('eletronicos'), ver=('EL-22', 'EL-24')),
    'EL-26': _f('O que os símbolos de alvo AIS mostram na carta', 'O que significa cada símbolo de alvo AIS na carta?',
                ['alvo AIS com transmissão perdida', 'triângulo vermelho de alvo perigoso', 'alvo AIS ativado na carta'],
                'Cada embarcação rastreada pelo AIS aparece na carta como um triângulo apontando para o rumo em que se move, e muda de símbolo '
                'conforme o estado do alvo: selecionado, ativado (maior, com linha de rumo), ou com a transmissão perdida (um X verde, ou '
                'vermelho se o alvo já estava marcado como alvo perigoso). Um alvo perigoso pisca com aviso sonoro e visual; depois de '
                'confirmado, fica um triângulo vermelho fixo com a linha de rumo.',
                p=[], eq=equip_de('eletronicos'), ver=('EL-27', 'EL-28')),
    'EL-27': _f('Ativar e acompanhar um alvo AIS', 'Como eu ativo um alvo AIS para acompanhar na carta?',
                ['tempo até a aproximação de um alvo AIS', 'desativar um alvo AIS acompanhado', 'ver dados de um alvo AIS na carta'],
                'Um alvo AIS pode ser ativado para acompanhar o rumo e a velocidade dele na carta; a aproximação mais próxima prevista entre as '
                'duas embarcações e o tempo até ela aparecem junto ao alvo ativado. Pode ser desativado quando não for mais preciso acompanhar.',
                a='Ative o alvo AIS para ver a aproximação mais próxima prevista e o tempo até ela.',
                p=['Abra a lista de alvos AIS e escolha a embarcação.',
                   'Ative o alvo para acompanhar o rumo e a velocidade dele na carta.',
                   'Leia a aproximação mais próxima prevista e o tempo até ela, junto ao alvo.',
                   'Desative quando não precisar mais acompanhar.'],
                eq=equip_de('eletronicos'), ver=('EL-26', 'AI-01')),
    'EL-28': _f('Alarme de zona de segurança para alvos AIS', 'Como eu ativo o alarme de zona de segurança para embarcações próximas?',
                ['alarme também para alvos de radar', 'raio do alarme de aproximação do AIS', 'som do plotter para o alarme de AIS'],
                'O alarme de zona de segurança avisa quando uma embarcação rastreada por AIS entra num raio definido ao redor do barco, ou está '
                'prevista para entrar dentro de um tempo escolhido; com um radar na mesma rede, os alvos de radar também podem entrar nessa '
                'zona. É um apoio à atenção da tripulação, que pode não avisar a tempo em toda situação, e precisa do som do plotter ligado.',
                a='Ative o alarme e escolha o raio (e o tempo de antecedência) ao redor do barco.',
                p=['Ative o alarme de zona de segurança para alvos AIS.',
                   'Escolha o raio ao redor do barco e, se quiser, o tempo de antecedência do aviso.',
                   'Com radar na mesma rede, inclua também os alvos de radar.',
                   'Deixe o som do plotter ligado para o alarme avisar.'],
                eq=equip_de('eletronicos'), ver=('EL-26', 'EL-27')),
    'EL-29': _f('Sinalização náutica por AIS (ATONs) na carta', 'Como eu vejo sinalizações náuticas transmitidas por AIS na carta?',
                ['símbolo de marca virtual por AIS', 'plotter precisa de rádio AIS para mostrar sinalização', 'ver informações de uma sinalização marcada'],
                'Além das marcas e luzes comuns da carta, o plotter mostra sinalizações transmitidas por AIS, com símbolos próprios para o tipo real (ou '
                'sintético) e para o tipo virtual; aparecem só quando o plotter está ligado a um rádio AIS compatível. Toque no símbolo para ver '
                'o nome e mais informações.',
                a='Ative a camada de sinalização náutica e toque no símbolo para ver o nome e os detalhes.',
                p=['Ative a camada de sinalização náutica (navaids) na carta.',
                   'Toque no símbolo para ver o nome e mais informações.',
                   'Um tipo de símbolo é para sinalização real (ou sintética) e outro para sinalização virtual.'],
                eq=equip_de('eletronicos'), ver=('EL-19',)),
    'EL-30': _f('Trocar a fonte de som do Fusion', 'Como eu troco a fonte do som do barco?',
                ['colocar o rádio FM no Fusion', 'tocar música do pendrive no Fusion', 'mudar de Bluetooth para o rádio'],
                'A fonte é o que o Fusion toca: rádio, Bluetooth, USB ou entrada auxiliar, conforme as que estiverem disponíveis no barco. Baixe '
                'o volume antes de trocar de fonte, porque cada uma pode tocar mais alto que a anterior, e confirme no visor qual ficou ativa '
                'antes de subir o volume de novo.',
                a='Baixe o volume, troque a fonte pelo controle e confirme no visor antes de subir o volume.',
                p=['Ligue o Fusion pelo controle.',
                   'Baixe o volume antes de trocar de fonte.',
                   'Troque a fonte pelo controle até aparecer a desejada (rádio, Bluetooth, USB ou auxiliar).',
                   'Confirme a fonte no visor antes de subir o volume.'],
                eq=equip_de('audio')),
    'EL-31': _f('Ajustar o volume de cada zona do Fusion', 'Como eu ajusto o volume de cada zona do Fusion?',
                ['uma zona do Fusion sem som', 'quantas zonas o Fusion tem', 'volume alto demais para ouvir o VHF'],
                'O Fusion toca em duas zonas de som, cada uma com o volume próprio; ajuste a zona em que você está sem mexer na outra. Mantenha '
                'o volume baixo o bastante para ouvir o rádio VHF e os alarmes do barco.',
                a='Ajuste o volume de cada zona separadamente, sem mexer na outra.',
                p=['Escolha no controle a zona que quer ajustar.',
                   'Ajuste o volume dessa zona sem mexer na outra.',
                   'Para quase silenciar uma zona, baixe o volume dela ao mínimo.',
                   'Mantenha o volume baixo o bastante para ouvir o rádio VHF e os alarmes.'],
                eq=equip_de('audio'), ver=('EL-35',)),
    'EL-32': _f('Reconectar o celular ao Fusion já pareado', 'O celular já pareado não conecta sozinho ao Fusion, o que faço?',
                ['tocar música do celular no Fusion', 'dois celulares no Fusion ao mesmo tempo', 'primeira vez pareando o celular no Fusion'],
                'Depois do primeiro pareamento, o celular conecta ao Fusion com poucos toques: escolha a fonte Bluetooth no Fusion e toque nele '
                'na lista de aparelhos pareados do celular. Só um celular transmite o som por vez; com mais de um celular por perto, desconecte '
                'ou pause os outros.',
                a='Escolha a fonte Bluetooth no Fusion e toque nele na lista de pareados do celular.',
                p=['Ligue o Bluetooth do celular, perto do Fusion.',
                   'No Fusion, escolha a fonte Bluetooth.',
                   'No celular, toque no Fusion na lista de aparelhos já pareados.',
                   'Com mais de um celular por perto, desconecte ou pause os outros: só um transmite por vez.'],
                eq=equip_de('audio'), ver=('EL-34',)),
    'EL-33': _f('Silenciar o Fusion sem desligar', 'Como eu silencio o som do barco sem desligar o Fusion?',
                ['voltar o som depois do mudo', 'mudo desliga o Fusion', 'silenciar uma zona só'],
                'O mudo corta o som do Fusion sem trocar a fonte nem mexer no volume, e sem desligar o aparelho; acione de novo para voltar ao '
                'mesmo nível. Para silenciar só uma zona, baixe o volume dela ao mínimo em vez de usar o mudo.',
                a='Acione o mudo para cortar o som sem desligar; acione de novo para voltar ao mesmo nível.',
                p=['Acione o mudo pelo controle do Fusion.',
                   'Confirme no visor que o mudo ficou ativo.',
                   'Acione de novo para voltar ao mesmo volume.',
                   'Para silenciar só uma zona, baixe o volume dela ao mínimo.'],
                eq=equip_de('audio')),
    'EL-34': _f('Celular não conecta ou o som do Bluetooth corta', 'Por que o Bluetooth do Fusion não conecta?',
                ['som do celular cortando no Fusion', 'Fusion não aparece na lista de Bluetooth', 'apagar e refazer o pareamento do Fusion'],
                'Falha de Bluetooth no Fusion costuma vir de distância, obstáculo, outro aparelho conectado ou um pareamento antigo. Aproxime o '
                'celular e tire o que houver de metal ou anteparo entre os dois; desligue e ligue o Bluetooth do celular e escolha de novo a '
                'fonte Bluetooth no Fusion; se persistir, apague o Fusion da lista de aparelhos do celular e pareie de novo, com o Fusion '
                'visível. Se nenhum celular conectar, desligue e ligue o Fusion pelo controle; se mesmo assim persistir, chame o técnico.',
                a='Aproxime os aparelhos, refaça o pareamento com o Fusion visível e, se persistir, chame o técnico.',
                p=['Aproxime o celular e tire obstáculos de metal entre os dois.',
                   'Desligue e ligue o Bluetooth do celular; escolha de novo a fonte Bluetooth no Fusion.',
                   'Desconecte outros aparelhos Bluetooth do celular.',
                   'Apague o Fusion da lista do celular e pareie de novo, com o Fusion visível.',
                   'Teste com outro celular; se nenhum conectar, desligue e ligue o Fusion e, se persistir, chame o técnico.'],
                eq=equip_de('audio'), ver=('EL-32',)),
    'EL-35': _f('Fusion ligado e sem som', 'O som do barco liga, mas não toca. O que faço?',
                ['uma zona do Fusion sem som', 'celular conectado sem som no Fusion', 'Fusion mudo sem eu saber'],
                'Com o Fusion ligado e sem som, as causas mais comuns são o mudo ativo, o volume da zona em zero, a fonte errada ou o volume '
                'baixo no celular conectado; confira nessa ordem antes de desconfiar do aparelho. Sem som em nenhuma fonte nem zona, com o mudo '
                'desativado e o visor aceso, o problema pode estar no amplificador, na fiação ou nas caixas: chame o técnico.',
                a='Confira mudo, volume da zona e a fonte ativa; sem solução, chame o técnico.',
                p=['Confira se o mudo está ativo e desative.',
                   'Suba o volume da zona em que quer ouvir: cada zona tem o volume próprio.',
                   'Confirme a fonte ativa no visor.',
                   'Em Bluetooth, confira se o celular está conectado, tocando e com o volume dele acima do mínimo.',
                   'Desligue e ligue o Fusion pelo controle e teste de novo; sem som em nada, chame o técnico.'],
                eq=equip_de('audio'), ver=('EL-31', 'EL-34')),
    'EL-36': _f('Problemas de fonte: rádio, USB e entrada auxiliar', 'Por que o rádio FM do barco chia?',
                ['pendrive que não toca no Fusion', 'som baixo pela entrada auxiliar', 'som falhando ao ligar outros equipamentos'],
                'Cada fonte do Fusion falha de um jeito: o rádio chia por sinal fraco ou pela antena; o USB não toca por mau contato ou por '
                'formato de arquivo; a entrada auxiliar fica baixa quando o volume do aparelho de origem está baixo. Som falhando ao ligar '
                'cargas grandes, como bombas ou guincho, pode ser a tensão do banco que alimenta o Fusion: chame o técnico.',
                a='Cada fonte falha de um jeito diferente; teste a causa mais comum de cada uma antes de chamar o técnico.',
                p=['Rádio chiando: mude de estação e confira a antena.',
                   'USB que não toca: encaixe bem o conector, teste outro pendrive e um formato comum de música.',
                   'Entrada auxiliar baixa: suba o volume do aparelho de origem.',
                   'Som falhando ao ligar cargas grandes: confira a tensão do banco que alimenta o Fusion e chame o técnico.'],
                eq=equip_de('audio'), ver=('EL-35',)),
    'EL-37': _f('Ajustar o ganho e a sensibilidade da sonda', 'Como deixo a imagem da sonda mais clara?',
                ['sonda não mostra o fundo', 'diferença entre ganho e sensibilidade', 'tela da sonda cheia de pontos'],
                'O ganho (ou sensibilidade) da sonda controla a intensidade dos ecos na tela: baixo demais perde o fundo e os peixes, alto demais '
                'cobre a tela de ruído. Aumente até o fundo aparecer com uma linha nítida e contínua, reduza se a tela ficar cheia de pontos de '
                'ruído, e reajuste ao mudar de profundidade, velocidade ou tipo de fundo.',
                a='Aumente o ganho até o fundo ficar nítido; reduza se a tela ficar cheia de ruído.',
                p=['Abra o ajuste de ganho (ou sensibilidade) da sonda.',
                   'Aumente até o fundo aparecer com uma linha nítida e contínua.',
                   'Reduza aos poucos se a tela ficar cheia de ruído.',
                   'Reajuste ao mudar de profundidade, velocidade ou tipo de fundo.'],
                eq=equip_de('eletronicos'), ver=('EL-38', 'EL-40')),
    'EL-38': _f('Ajustar a faixa de profundidade da sonda', 'Por que o fundo não aparece na tela da sonda?',
                ['faixa automática ou manual na sonda', 'sonda perde o fundo em mudança rápida', 'escala de profundidade da sonda'],
                'A faixa de profundidade define até onde a tela da sonda mostra a coluna de água; no modo automático ela segue sozinha, e no '
                'modo manual precisa ser ajustada para o fundo aparecer na parte de baixo da tela. Em mudanças rápidas de profundidade, '
                'acompanhe e corrija a faixa manualmente; volte ao automático em navegação com profundidade variável e sem tempo de ajustar.',
                a='Ajuste a faixa no modo manual para o fundo aparecer na tela, ou deixe no automático.',
                p=['No modo manual, ajuste a faixa para o fundo aparecer na parte de baixo da tela.',
                   'Em mudança rápida de profundidade, corrija a faixa manualmente.',
                   'Volte ao modo automático quando não houver tempo de ajustar.'],
                eq=equip_de('eletronicos'), ver=('EL-37',)),
    'EL-39': _f('Interpretar fundo duro ou mole na sonda', 'Como saber se o fundo é de areia ou de lama pela sonda?',
                ['eco duplo na tela da sonda', 'sonda garante o tipo de fundo', 'linha de fundo muda de espessura'],
                'A espessura e a intensidade da linha de fundo na sonda indicam, em termos gerais, se o fundo é mais duro (como rocha ou areia '
                'compacta) ou mais mole (como lama ou vegetação): uma linha fina e clara tende a fundo mole, e uma linha grossa e forte, com uma '
                'segunda marca abaixo (eco duplo), tende a fundo duro. É uma indicação geral, não uma confirmação exata do tipo de fundo: '
                'compare com a carta náutica.',
                p=[], eq=equip_de('eletronicos')),
    'EL-40': _f('Reduzir ruído e interferência na sonda', 'Por que a sonda fica com ruído em velocidade alta?',
                ['filtro de interferência da sonda', 'bolhas no transdutor da sonda', 'ruído elétrico constante na sonda'],
                'Bolhas, turbulência perto do transdutor e interferência elétrica de outros equipamentos podem sujar a imagem da sonda com '
                'ruído, sobretudo em alta velocidade. Reduza a velocidade e o ganho até o ruído de turbulência diminuir, sem perder o fundo, e '
                'ative o filtro de interferência, se o equipamento tiver essa função. Ruído constante e elétrico nem sempre se resolve só pelo '
                'painel: registre no diário e peça revisão do transdutor e das conexões ao técnico de bordo.',
                a='Reduza a velocidade e o ganho; ruído elétrico constante pede revisão do técnico de bordo.',
                p=['Reduza a velocidade e veja se o ruído diminui.',
                   'Reduza o ganho até o ruído de turbulência diminuir, sem perder o fundo.',
                   'Ative o filtro de interferência, se o equipamento tiver essa função.',
                   'Ruído constante e elétrico: registre no diário e peça revisão ao técnico de bordo.'],
                eq=equip_de('eletronicos'), ver=('EL-37',)),
    'EL-41': _f('Configurar o alarme de água rasa na sonda', 'Como configuro o alarme de água rasa na sonda?',
                ['margem do alarme de profundidade mínima', 'alarme de profundidade e a maré', 'aviso antes do casco tocar o fundo'],
                'O alarme de água rasa avisa quando a profundidade fica menor que um limite definido por você, com tempo de reagir antes que o '
                'casco toque o fundo. Defina o limite com margem acima da profundidade que o casco exige, ative o som ou o aviso na tela, e '
                'reavalie o limite ao trocar de área de navegação ou de condição de maré.',
                a='Defina o limite do alarme com margem sobre a profundidade que o casco exige.',
                p=['Abra o alarme de água rasa no menu da sonda.',
                   'Defina o limite com margem acima da profundidade que o casco exige.',
                   'Ative o som ou o aviso na tela.',
                   'Reavalie o limite ao trocar de área ou de maré.'],
                eq=equip_de('eletronicos'), ver=('EL-38',)),
    'EL-42': _f('Configurar o alarme de fundeio (âncora garrando)', 'Como configuro o alarme de fundeio no plotter?',
                ['raio do alarme de âncora garrando', 'alarme avisa se a âncora garrar', 'o que fazer se o alarme de fundeio disparar'],
                'O alarme de fundeio marca a posição do barco no momento em que a âncora é lançada e avisa se o barco se deslocar além de um '
                'raio definido, indicando que a âncora pode estar garrando. Defina o raio considerando o comprimento de corrente ou cabo '
                'lançado, confirme que o alarme está ativo antes de deixar o posto de comando sem vigilância e, se ele disparar, volte ao posto '
                'de comando e confira a posição e a profundidade antes do próximo passo.',
                a='Ative o alarme ao fundear e defina o raio pelo comprimento de corrente lançado.',
                p=['Com a âncora fundeada e o barco estabilizado, ative o alarme de fundeio.',
                   'Defina o raio considerando o comprimento de corrente ou cabo lançado.',
                   'Confirme que o alarme está ativo antes de deixar o posto de comando sem vigilância.',
                   'Se disparar, volte ao posto de comando e confira a posição e a profundidade.'],
                eq=equip_de('eletronicos'), ver=('EL-03',)),
    # ——— Rádios VHF Icom (fixo IC-M510) ———
    'VH-01': _f('Ligar e desligar o rádio VHF IC-M510', 'Como ligo o rádio VHF?',
                ['Como desligo o rádio Icom?', "O rádio pede 'Register your MMSI' ao ligar, o que significa?", 'Qual botão liga o IC-M510?'],
                'O IC-M510 liga e desliga pelo botão giratório CH/ENT/PWR, mantido por cerca de 1 segundo.',
                p=['Confira o conector do microfone bem rosqueado, no sentido horário, para manter a vedação contra água.',
                   'Segure o botão giratório CH/ENT/PWR por cerca de 1 segundo para ligar.',
                   'Com MMSI cadastrado, ele aparece na tela; sem MMSI, o rádio dá três bips e pede o cadastro, e fica sem chamada DSC.',
                   'Ajuste o volume em VOL e o squelch em SQL.', 'Para desligar, segure o mesmo botão por cerca de 1 segundo.'],
                at='O cadastro do MMSI vale uma vez; depois, um revendedor ou distribuidor Icom pode alterá-lo.',
                ver=('VH-02', 'VH-04', 'EL-04')),
    'VH-02': _f('Ajustar volume e squelch do rádio VHF', 'Como ajusto o volume do rádio VHF?',
                ['Para que serve o squelch?', 'O rádio está mudo, não sai som, o que faço?', 'Como ajusto o squelch do rádio?'],
                'O VOL regula o volume e o SQL define o squelch, o nível mínimo de sinal que o rádio exige para liberar o áudio.',
                p=['Gire VOL para ajustar o volume.', 'Gire SQL para ajustar o squelch no ponto em que o chiado de fundo acaba de sumir.',
                   'Pouco ou nenhum som: abaixe o squelch até esse ponto e confira o volume.',
                   'Som abafado com o volume bom: pode ser água na grade do alto-falante — use o AquaQuake, sem o alto-falante externo ligado.'],
                at='Squelch alto demais esconde os sinais fracos de outras estações.',
                ver=('VH-01', 'VH-35', 'VH-41')),
    'VH-03': _f('Trocar de canal no rádio VHF IC-M510', 'Como mudo de canal no VHF?',
                ['Como troco o canal pelo microfone?', 'Por que o canal aparece como 1001 ou 01A?', 'O microfone só passa por alguns canais, por quê?'],
                'Troque o canal pressionando as teclas de subir e descer, ou girando CH/ENT, até chegar ao canal desejado; o número e o nome aparecem por um instante na tela.',
                p=['Pressione as teclas de subir e descer, ou gire CH/ENT, até o canal desejado.',
                   'Confira o número e o nome do canal, exibidos por instantes na tela.',
                   'No microfone, as mesmas teclas de subir e descer também trocam de canal.',
                   'Para o microfone passar só pelos favoritos, ligue FAV on MIC em Menu > Settings > Radio; em OFF, ele passa por todos os canais.'],
                at='O número do canal pode aparecer com 3 ou 4 dígitos (01A ou 1001), conforme o ajuste de Channel Display.',
                se='Alguns canais são só de recepção ou de baixa potência.',
                ver=('VH-04', 'VH-08')),
    'VH-04': _f('Canal 16 e canal de chamada: como selecionar', 'Como vou para o canal 16 no rádio?',
                ['Como seleciono o canal de chamada?', 'Como volto ao canal em que estava depois do 16?', 'Como mudo o canal de chamada?'],
                'A tecla 16/C leva direto ao canal 16; mantida por 1 segundo, leva ao canal de chamada do grupo em uso (ícone CALL).',
                p=['Pressione 16/C, no rádio ou no microfone, para ir direto ao canal 16.',
                   'Segure 16/C por 1 segundo para ir ao canal de chamada.',
                   'Para voltar ao canal anterior, use a tecla de software CH/WX (ou CH).',
                   'Para trocar o canal de chamada, abra Menu > Settings > Radio > Call Channel e escolha o canal.'],
                at='Fora de outro canal, mantenha o rádio no canal 16; operando em outro, use a dupla ou a tripla escuta para conferi-lo.',
                ver=('VH-03', 'VH-10', 'EL-04')),
    'VH-05': _f('Transmitir e receber: uso do PTT no IC-M510', 'Como falo no rádio VHF?',
                ['Por que a transmissão cortou depois de alguns minutos?', 'A que distância devo segurar o microfone?', 'Qual botão uso para transmitir?'],
                'Para falar, segure a tecla PTT do microfone; para ouvir, solte. Nunca transmita sem a antena conectada.',
                p=['Escolha o canal da conversa.', 'Segure PTT: o ícone de transmissão aparece na tela.',
                   'Espere cerca de 1 segundo e fale em voz normal, com o microfone a 5 a 10 cm da boca.', 'Solte PTT para voltar a receber.'],
                at='O rádio corta a transmissão depois de 5 minutos seguidos (Time-out Timer).',
                ver=('VH-01', 'VH-06')),
    'VH-06': _f('Alternar entre potência alta e baixa de transmissão', 'Como troco a potência do rádio VHF?',
                ['Por que não consigo transmitir em potência alta?', 'Quantos watts o IC-M510 transmite?', 'O que significa o ícone 25W ou 1W?'],
                'O IC-M510 transmite com 25 W (alta) ou 1 W (baixa); a troca é feita por H/L no microfone ou pela tecla de software HI/LO.',
                p=['Pressione H/L no microfone, ou a tecla de software HI/LO, para alternar a potência.',
                   'Confira o ícone 25W (alta) ou 1W (baixa) na área de informações da tela.',
                   'Sem transmitir em potência alta: confira se o rádio está em baixa e pressione HI/LO.',
                   'Se continuar, troque de canal: alguns só aceitam baixa potência ou só recebem, por norma.'],
                ver=('VH-05', 'VH-37')),
    'VH-07': _f('Escolher o grupo de canais (USA, INT, CAN)', 'Como mudo o grupo de canais do rádio?',
                ['O que significa USA, INT e CAN no rádio?', 'Os canais do rádio mudaram, por quê?', 'escolher entre USA, INT e CAN'],
                'Os canais vêm em grupos pré-programados — USA, INT (internacional), CAN (Canadá), e DSC ou ATIS conforme a versão —, que definem a lista de canais, os favoritos e o canal de chamada.',
                p=['Abra Menu > Settings > Radio > Channel Group.', 'Escolha o grupo e confirme.',
                   'Confira o ícone do grupo (USA, INT ou CAN) na tela de operação.'],
                at='Escolha o grupo que vale para a área onde o barco opera; os grupos disponíveis dependem da versão do rádio.',
                ver=('VH-08', 'VH-09')),
    'VH-08': _f('Marcar canais favoritos (FAV) no rádio VHF', 'Como marco um canal como favorito?',
                ['Como limpo todos os favoritos?', 'Como volto os favoritos ao padrão?', 'Por que o microfone só passa por alguns canais?'],
                'Os canais favoritos são os que a varredura e o microfone podem percorrer; marque ou desmarque pela tecla de software FAV★.',
                p=['Escolha o grupo em Menu > Settings > Radio > Channel Group.',
                   'Selecione o canal e pressione a tecla de software FAV★ para marcar; pressione de novo para desmarcar.',
                   'Para marcar todos, limpar todos ou voltar ao padrão, abra Menu > Settings > Radio > Favorite CH.',
                   'Em FAV on MIC, ON faz as teclas de subir e descer do microfone passarem só pelos favoritos.'],
                at='A varredura percorre só os canais favoritos: marque pelo menos 2 para ela iniciar.',
                ver=('VH-07', 'VH-09')),
    'VH-09': _f('Varredura (scan) normal e prioritária: como usar', 'Como faço o scan dos canais no VHF?',
                ['Qual a diferença entre varredura normal e prioritária?', 'O scan não inicia, o que faço?', 'Como paro a varredura?'],
                'A varredura percorre os canais favoritos; a normal não confere o canal 16 a menos que seja favorito, e a prioritária (SCAN 16) o confere de tempos em tempos.',
                p=['Marque pelo menos 2 canais favoritos e ajuste o squelch para receber bem.',
                   'Escolha o tipo em Menu > Settings > Radio > Scan Type: Normal Scan ou Priority Scan.',
                   'Pressione a tecla de software Scan para iniciar; SCAN ou SCAN 16 aparece na tela.',
                   'Com sinal recebido, a varredura pausa até ele sumir ou retoma em 5 segundos, conforme o Scan Timer.',
                   'Para parar, pressione Scan de novo.'],
                at='É preciso ter pelo menos 2 canais favoritos para a varredura iniciar; não existe na versão holandesa (NLD) do rádio.',
                ver=('VH-08', 'VH-10')),
    'VH-10': _f('Dupla e tripla escuta: como ligar e a diferença', 'Como ligo a dupla escuta no VHF?',
                ['Qual a diferença entre dupla e tripla escuta?', 'Como monitoro o canal 16 enquanto uso outro canal?', 'Como cancelo a dupla escuta?'],
                'A dupla escuta (DUAL 16) confere o canal 16 de tempos em tempos enquanto você opera em outro canal; a tripla (TRI 16) confere o canal 16 e o canal de chamada.',
                p=['Escolha o modo em Menu > Settings > Radio > Dual/Tri-Watch: Dualwatch ou Tri-watch.',
                   'Escolha o canal de trabalho e pressione a tecla Dual Watch (ou TRI Watch) para iniciar.',
                   'Com sinal no canal 16, soa um bip, o 16 pisca e a escuta pausa nele até o sinal acabar.',
                   'Para cancelar, pressione Dual Watch (ou TRI Watch) de novo.'],
                at='Fora de outro canal, mantenha o canal 16 em escuta.',
                ver=('VH-04', 'VH-09', 'EL-04')),
    'VH-11': _f('DSC no IC-M510: como funciona e o que é preciso', 'O que é DSC no rádio VHF?',
                ['Para que serve o canal 70?', 'Por que não aparecem as teclas de DSC no rádio?', 'Que tipos de chamada DSC o IC-M510 faz?'],
                'A chamada seletiva digital (DSC) chama uma estação, um grupo ou todos os navios pelo canal 70; a conversa segue depois num canal de voz combinado. O rádio só faz chamadas DSC com o MMSI cadastrado.',
                p=['Confira se o MMSI está cadastrado: sem ele, as teclas de software da DSC não aparecem.',
                   'Ajuste CH 70 SQL Level em Menu > Settings > DSC antes de chamar.',
                   'Pressione Other DSC e escolha o tipo em Msg Type, o destino em Address e o canal de voz em Channel.',
                   'Em chamada individual, espere a confirmação: Able to comply (pode atender) ou Unable to comply (não pode).',
                   'Consulte depois as chamadas no DSC Log.'],
                at='A chamada só chega a estações dentro do alcance do rádio.',
                ver=('VH-12', 'VH-14', 'EL-05', 'EM-03')),
    'VH-12': _f('Cadastrar IDs de chamada individual e de grupo', 'Como cadastro o MMSI de outro barco no rádio?',
                ['Como crio um grupo para chamadas DSC?', 'Como apago um ID da lista?', 'Por que o rádio não aceita o ID?'],
                'O rádio guarda até 75 IDs individuais e 25 IDs de grupo, com nome de até 10 caracteres, para chamar sem digitar o número toda vez.',
                p=['Abra Menu > Settings > DSC > Individual ID (ou Group ID) e pressione Add.',
                   'Digite o número do ID e confirme; pressione Next e digite o nome, com até 10 caracteres.',
                   'Pressione Finish para salvar; o nome aparece na lista.',
                   'Para apagar, selecione o ID e pressione Delete e depois OK; para corrigir, use Edit.'],
                at='No ID individual, o primeiro dígito vai de 1 a 9; no ID de grupo, o primeiro dígito é fixo em 0.',
                ver=('VH-11', 'VH-21')),
    'VH-13': _f('Informar posição e hora à mão (sem GPS válido)', 'Como coloco a posição manualmente no rádio?',
                ['Como acerto a hora do rádio?', 'O rádio mostra NO POSITION, o que faço?', 'Por que o símbolo de interrogação pisca no lugar da posição?'],
                'Sem dados de GPS, digite a posição e a hora UTC em Menu > Settings > DSC > Position Input; a entrada dura 23,5 horas ou até desligar o rádio.',
                p=['Abra Menu > Settings > DSC > Position Input.', 'Digite a latitude, a longitude e a hora UTC.',
                   'Pressione Finish para salvar; o rádio volta à tela DSC.',
                   'Para a tela mostrar a hora local, informe a diferença para UTC em Menu > Settings > Configuration > UTC Offset.'],
                at='Depois de 4 horas da entrada manual, o símbolo de interrogação pisca no lugar da posição e da hora; refaça a entrada. A entrada manual fica bloqueada enquanto houver GPS válido.',
                ver=('VH-27', 'VH-32')),
    'VH-14': _f('Fazer uma chamada DSC individual para outra estação', 'Como faço uma chamada DSC para outro barco?',
                ["O que significa 'Waiting for ACK'?", "O que faço quando a resposta é 'Unable to comply'?", 'Como chamo uma estação sem digitar o número?'],
                'A chamada individual vai só para a estação escolhida; a conversa começa depois que ela responde Able to comply e o rádio troca para o canal de voz combinado.',
                p=['Pressione Other DSC.',
                   'Em Msg Type escolha Individual; em Address, a estação da lista ou Manual Input para digitar o ID; em Channel, o canal de voz.',
                   'Pressione Call: aparecem Transmitting Individual Call e depois Waiting for ACK.',
                   'Com Able to comply, pressione Alarm OFF e depois Close Window; segure PTT para falar.',
                   'Com Unable to comply: pressione Alarm OFF, Close Window, STBY e OK.'],
                at='Sem MMSI cadastrado o rádio não faz chamada DSC; se o canal 70 estiver ocupado, o rádio espera liberar para enviar.',
                ver=('VH-11', 'VH-15')),
    'VH-15': _f('Receber uma chamada DSC: o que fazer ao soar o alarme', 'O rádio tocou um alarme de chamada DSC, o que faço?',
                ['Como aceito uma chamada individual?', 'Como recuso ou ignoro uma chamada DSC?', 'O rádio trocou de canal sozinho, por quê?'],
                'Ao receber uma chamada DSC, o rádio soa um alarme e mostra o tipo da chamada; silencie com Alarm OFF e escolha entre ignorar, segurar ou aceitar.',
                p=['Pressione Alarm OFF para silenciar o alarme.',
                   'Chamada individual: pressione Able para confirmar na hora, ou Accept para ver os dados e escolher a resposta (ACK Able, ACK Unable ou ACK New CH).',
                   'Chamada em grupo ou a todos os navios: por padrão o rádio vai ao canal combinado após 10 segundos; use Pause e Resume para suspender e retomar a contagem.',
                   'Pressione Ignore para descartar a chamada, que fica no DSC Log, ou Hold para mantê-la em espera.'],
                at='Por padrão o rádio confirma sozinho as chamadas individuais (Auto ACK); a escolha da resposta só aparece com Individual ACK em Manual.',
                ver=('VH-14', 'VH-20')),
    'VH-16': _f('Chamada DSC em grupo ou a todos os navios', 'Como faço uma chamada DSC para um grupo de barcos?',
                ['Como mando uma chamada a todos os navios?', 'Onde escolho a categoria da chamada a todos os navios?', 'Como encerro a chamada a todos os navios?'],
                'A chamada em grupo atinge só o grupo escolhido; a chamada a todos os navios (All Ships) avisa todas as embarcações com DSC ao alcance.',
                p=['Pressione Other DSC.', 'Em Msg Type, escolha Group ou All Ships.',
                   'Grupo: escolha o grupo cadastrado em Address. Todos os navios: escolha Routine em Category para recado comum.',
                   'Em Channel, escolha o canal de voz e pressione Call.',
                   'Ao terminar uma chamada a todos os navios, pressione STBY e depois OK.'],
                at='A categoria define a prioridade do aviso a todos os navios: as outras opções são de prioridade maior que Routine; não as use em recado comum.',
                ver=('VH-11', 'VH-17')),
    'VH-17': _f('Enviar uma chamada de teste DSC', 'Como testo a DSC do rádio?',
                ['Como faço uma chamada de teste para outro barco?', 'Como sei se o rádio está enviando DSC direito?', 'O que é o Self Check Test?'],
                'A chamada de teste confere se a DSC funciona com outra estação; sem outra estação, o Self Check Test compara, dentro do rádio, o sinal DSC enviado com o recebido.',
                p=['Pressione Other DSC, escolha Test em Msg Type e a estação em Address.',
                   'Pressione Call; se o canal 70 estiver ocupado, o rádio espera liberar.',
                   'Na confirmação, o alarme soa: pressione Alarm OFF e Close Window; a chamada fica no DSC Log.',
                   'Autoteste: abra Menu > Settings > DSC > Self Check Test; aparece OK quando o sinal enviado e o recebido conferem.'],
                at='Evite fazer chamada de teste nos canais exclusivos da DSC e nos de chamada de segurança; se for inevitável, diga que é teste.',
                ver=('VH-11', 'VH-21')),
    'VH-18': _f('Pedir a posição de outra estação por DSC', 'Como peço a posição de outro barco pelo rádio?',
                ['O que é o Polling no rádio VHF?', 'Não aparece Position em Msg Type, por quê?', 'Como leio a posição que o outro barco enviou?'],
                'O pedido de posição pergunta onde está uma estação, com a resposta chegando por DSC; é função da versão dos EUA do rádio e depende da pré-configuração do revendedor.',
                p=['Pressione Other DSC, escolha Position em Msg Type (ou Polling, para só saber se a estação está ao alcance).',
                   'Escolha a estação em Address e pressione Call.', 'Na resposta, pressione Alarm OFF e Close Window.',
                   'Role a tela para ler a posição da estação.'],
                at='Se Position não aparecer em Msg Type, a versão ou a configuração do rádio não tem a função.',
                ver=('VH-19', 'VH-11')),
    'VH-19': _f('Responder a um pedido de posição (enviar a sua posição)', 'Alguém pediu minha posição, como respondo?',
                ['Como envio minha posição pelo rádio?', 'Como faço o rádio responder pedidos de posição sozinho?', "O que significa 'Received POS Request'?"],
                'Ao receber um pedido de posição, o rádio soa um alarme e mostra Received POS Request; com Position ACK em Manual, você escolhe responder com ou sem posição.',
                p=['Pressione Alarm OFF para silenciar o alarme.',
                   'Pressione Able (pode atender) ou Unable (não pode) para responder na hora, ou Accept para ver os dados.',
                   'Pressione ACK Able para responder com posição e hora, ou ACK Unable para responder sem elas, e Call para enviar.',
                   'Para o rádio responder sozinho, ajuste Position ACK em Menu > Settings > DSC > Auto ACK.'],
                at='A resposta com posição depende de o rádio ter posição válida: GPS ou posição digitada.',
                ver=('VH-18', 'VH-20')),
    'VH-20': _f('Resposta automática (Auto ACK) e troca de canal na DSC', 'Como faço o rádio responder sozinho às chamadas DSC?',
                ['Por que o rádio trocou de canal sozinho?', 'Como desligo a resposta automática?', 'O que é o CH Auto Switch?'],
                'Por padrão o rádio confirma sozinho as chamadas DSC recebidas (Auto ACK); os ajustes de Menu > Settings > DSC > Auto ACK definem quando a confirmação e a troca de canal são automáticas ou manuais.',
                p=['Abra Menu > Settings > DSC > Auto ACK.',
                   'Em Individual ACK, escolha Auto (Able), Auto (Unable) ou Manual; o mesmo em Position ACK, Polling ACK e Test ACK.',
                   'Para a troca de canal, abra Menu > Settings > DSC > CH Auto Switch.',
                   'Escolha Accept after 10 sec (vai sozinho ao canal após 10 segundos), Ignore after 10 sec (ignora a chamada nesse prazo) ou Manual (decide a cada chamada).'],
                at='A resposta de posição e o Polling ACK existem só em parte das versões do rádio.',
                ver=('VH-15', 'VH-19')),
    'VH-21': _f('Consultar o registro de chamadas DSC (DSC Log)', 'Onde vejo as chamadas DSC que recebi?',
                ['Como vejo o histórico de chamadas do rádio?', 'Como apago um registro do DSC Log?', 'Como salvo o MMSI de quem me chamou?'],
                'O DSC Log guarda as chamadas DSC recebidas (até 50 comuns) e as enviadas (até 30).',
                p=['Pressione a tecla de software DSC Log, ou abra Menu > DSC Log.',
                   'Escolha Received Call Log (recebidas) ou Transmitted Call Log (enviadas).',
                   'Selecione um registro e pressione INFO para ver os detalhes.',
                   'Pressione Delete para apagar, ou MMSI para salvar o código como ID individual (nas enviadas, também como ID de grupo).'],
                ver=('VH-12', 'VH-15')),
    'VH-22': _f('Alarmes DSC do rádio: o que cada um avisa (Alarm Status)', 'Por que o rádio apita falando de posição?',
                ['Como desligo o alarme de uma chamada rotineira?', 'O que é o alarme Warning do rádio?', 'Como silencio o alarme do rádio?'],
                'O menu Alarm Status liga ou desliga o alarme de cada tipo de chamada DSC recebida; o Warning avisa de problemas do próprio rádio com o MMSI e com a posição.',
                p=['Abra Menu > Settings > DSC > Alarm Status.', 'Escolha o tipo (Safety, Routine, Warning, Discrete e outros) e defina ON ou OFF.',
                   'O Warning soa se nenhum MMSI foi cadastrado, ou se a posição (digitada ou do GPS) não chega ou não é atualizada a tempo.',
                   'O Discrete soa quando chega uma chamada de prioridade menor enquanto o rádio recebe outra, de prioridade maior.',
                   'Pressione Alarm OFF para silenciar um alarme de chamada.'],
                at='Deixe Safety e Warning em ON: avisam de chamadas de segurança e da falta de MMSI ou de posição no rádio.',
                ver=('VH-13', 'VH-20')),
    # ——— Rádios VHF Icom (telas, luz, ruído, GPS/NMEA/AIS, âncora, falhas) ———
    'VH-23': _f('Ajustar a luz da tela e o modo dia/noite', 'Como diminuo a luz da tela do rádio?',
                ['Como ligo o modo noite no VHF?', 'Como ajusto o contraste da tela do rádio?', 'Como apago a luz de fundo?'],
                'A luz de fundo tem 7 níveis, mais OFF (só no modo Dia); o modo Dia mostra cores e o modo Noite usa preto e vermelho.',
                p=['Pressione a tecla de software Backlight, ou abra Menu > Settings > Configuration > Backlight.',
                   'Ajuste o brilho entre os 7 níveis e OFF.', 'Escolha Day (cores) ou Night (preto e vermelho).'],
                at='OFF da luz de fundo só existe no modo Dia; o contraste só existe no microfone de comando opcional — o rádio fixo ajusta brilho e o modo Dia/Noite.',
                ver=('VH-24',)),
    'VH-24': _f('Ligar ou desligar o bip das teclas (Key Beep)', 'Como desligo o bip das teclas do rádio?',
                ['O rádio não faz bip ao apertar as teclas, por quê?', 'Como volto o bip do rádio?', 'ligar e desligar o Key Beep'],
                'O Key Beep define se as teclas dão um bip a cada toque; ON mantém o bip e OFF deixa a operação silenciosa.',
                p=['Abra Menu > Settings > Configuration > Key Beep.', 'Escolha ON (bip a cada tecla) ou OFF (silencioso).'],
                at='O Key Beep só controla o bip das teclas; os alarmes do rádio têm ajustes próprios.',
                ver=('VH-23',)),
    'VH-25': _f('Travar as teclas do microfone (Microphone Lock)', 'Como travo as teclas do rádio?',
                ['Como destravo o microfone do VHF?', 'O microfone não troca de canal, está travado?', 'Como evito mudar de canal sem querer?'],
                'A trava do microfone (Microphone Lock) bloqueia todas as teclas, menos o PTT, para evitar troca de canal ou de função por toque acidental.',
                p=['Segure PWR por 1 segundo para desligar o rádio.',
                   'Com o rádio desligado, segure H/L no microfone e, sem soltar, segure PWR por 1 segundo para ligar.',
                   'Com a trava ativa, só o PTT responde no microfone.', 'Para destravar, repita os dois primeiros passos.'],
                at='Com a trava ativa, até a tecla 16/C do microfone fica travada: destrave antes de precisar dela.',
                ver=('VH-04',)),
    'VH-26': _f('Reduzir ruído do áudio (Noise Cancel)', 'Como reduzo o ruído do rádio?',
                ['Para que serve o Noise Cancel?', 'Como melhoro o áudio recebido no VHF?', 'reduzir ruído na transmissão'],
                'O Noise Cancel reduz o ruído aleatório do sinal recebido (RX) e do transmitido (TX), com ajuste próprio para cada lado.',
                p=['Abra Menu > Settings > Configuration > Noise Cancel.', 'Em RX, escolha OFF, Low, Mid ou High para reduzir o ruído recebido.',
                   'Em TX, escolha ON ou OFF para reduzir o ruído transmitido.'],
                at='O ajuste vale separadamente para recepção e para transmissão: configure os dois.',
                ver=('VH-02',)),
    'VH-27': _f('Sem posição ou hora na tela: NO POSITION, NO TIME ou o símbolo de interrogação', 'Por que o rádio mostra NO POSITION?',
                ['O GPS do rádio não pega, o que verifico?', 'Por que o símbolo de interrogação pisca no lugar da posição e da hora?', 'Como vejo a posição, a velocidade e o rumo no rádio?'],
                'NO POSITION e NO TIME aparecem sem antena GPS conectada nem entrada manual; o símbolo de interrogação piscando indica GPS inválido ou 4 horas desde a entrada manual.',
                p=['Confira se a antena GPS está bem conectada e se os fios NMEA estão firmes.', 'Confira se o rádio tem vista livre para o céu.',
                   'Abra Menu > GPS Info para ver a posição, a data, a hora, a velocidade (SOG) e o rumo (COG) em uso.',
                   'Sem GPS, digite posição e hora UTC em Menu > Settings > DSC > Position Input.',
                   'Para melhorar a precisão, ligue o SBAS em Menu > Settings > Configuration > GPS, se a versão tiver a opção.'],
                at='A última posição fica retida por 23,5 horas; depois aparece NO POSITION. GLONASS e SBAS podem não estar disponíveis em todas as versões.',
                ver=('VH-13', 'VH-28')),
    'VH-28': _f('Ligar o rádio ao GPS, ao AIS e ao plotter por NMEA', 'Como ligo o rádio ao GPS externo?',
                ['Como o rádio recebe o AIS?', 'Que velocidade uso na NMEA 0183 para o AIS?', 'Como faço o rádio mandar a posição das chamadas DSC ao plotter?'],
                'O rádio recebe posição e AIS por NMEA 0183 ou por NMEA 2000, e pode repassar as chamadas DSC recebidas a um equipamento de navegação.',
                p=['NMEA 0183: em Menu > Settings > NMEA > NMEA 0183, use 4800 bps para GPS externo e 38400 bps para AIS externo.',
                   'NMEA 2000: em Menu > Settings > NMEA > NMEA 2000, escolha o dispositivo da rede, Auto ou Not used.',
                   'Com os dois conectados, vale o NMEA 2000; para usar o 0183, escolha Not used no NMEA 2000.',
                   'Um GPS externo tem prioridade sobre o GPS interno do rádio.',
                   'Para entregar as chamadas DSC a um plotter compatível, ajuste DSC Data Output em Menu > Settings > DSC.'],
                at='Se o rádio já recebe GPS e AIS, não altere velocidade nem dispositivo: a mudança pode cortar a recepção.',
                ver=('VH-27', 'VH-29')),
    'VH-29': _f('AIS no IC-M510: de onde vêm os alvos e o que mostram', 'O rádio mostra os barcos AIS ao redor?',
                ['De onde o rádio tira os dados de AIS?', 'O que é AIS Class A e Class B?', 'Por que o rádio não mostra nenhum alvo AIS?'],
                'O rádio mostra alvos AIS vindos de um receptor interno (só em algumas versões) ou de um AIS externo ligado por NMEA; o AIS mostra nome, posição, rumo e velocidade de outras embarcações para ajudar a evitar colisão.',
                p=['Sem receptor AIS interno, os alvos vêm de um AIS externo ligado por NMEA.',
                   'Por NMEA 0183, o AIS externo entra como sentença VDM, a 38400 bps.',
                   'Veja os alvos em Menu > AIS (Target List, Danger List, Friends List) ou na tela Plotter.',
                   'Class A é exigido dos navios sujeitos à convenção SOLAS; muitas embarcações não obrigadas escolhem o Class B.',
                   'Havendo AIS interno e externo, o externo tem prioridade.'],
                at='O rádio só mostra alvos AIS se tiver receptor interno ou receber o AIS por NMEA.',
                ver=('VH-28', 'VH-30', 'AI-01')),
    'VH-30': _f('Ver alvos AIS no plotter e nas listas do rádio', 'Como vejo os barcos AIS na tela do rádio?',
                ['Como mudo a escala do plotter do rádio?', 'Como vejo os detalhes de um barco AIS?', 'Como marco um barco como amigo?'],
                'A tela Plotter mostra o barco no centro e os alvos AIS em volta; as listas Target, Danger e Friends trazem os mesmos alvos ordenados por distância, CPA/TCPA ou marcados como amigos.',
                p=['Pressione DISP e escolha Plotter (ou Menu > AIS > Plotter); use Range para a escala, de 0,125 a 36 milhas náuticas.',
                   'Use Target Select para escolher o alvo mais próximo ou o mais distante, e Target Details para ver seus dados.',
                   'Para as listas, abra Menu > AIS e escolha Target List, Danger List ou Friends List; a Target List mostra até 200 alvos.',
                   'Na lista ou nos detalhes, Friend marca o alvo como amigo (até 100).',
                   'Para limitar o plotter, ajuste Target Display em Menu > Settings > AIS.'],
                at='O conteúdo dos detalhes depende dos dados recebidos do alvo.',
                ver=('VH-29', 'VH-31')),
    'VH-31': _f('Alarme de colisão AIS (CPA/TCPA): ajustar e silenciar', 'Como ajusto o alarme de colisão AIS do rádio?',
                ['O alarme de colisão não toca, o que faço?', 'Como silencio o alarme de aproximação?', 'Como evito que o próprio barco apareça como alvo de risco?'],
                'O rádio soa um alarme quando um alvo AIS fica mais próximo que o CPA e chega em menos tempo que o TCPA ajustados; alvos abaixo dos dois valores entram na Danger List.',
                p=['Abra Menu > Settings > AIS > CPA/TCPA.',
                   'Deixe Alarm em ON para Approach (aproximação) e Lost (alvo de risco que sumiu), e Audible Alarm em ON para o alarme soar.',
                   'Defina o CPA (0,01 a 6,00 NM) e o TCPA (1 a 60 minutos).', 'Para silenciar, pressione qualquer tecla.',
                   'Para o próprio transponder não virar alvo de risco, cadastre o ID em Menu > Settings > AIS > ID Blocking (até 10).'],
                at='Embarcação fundeada ou à deriva pode distorcer o CPA e o TCPA; o ajuste Slow Warn trata esse caso. Mantenha o alarme de aproximação ligado.',
                ver=('VH-30', 'VH-32')),
    'VH-32': _f('Alarme de fundeio do rádio (Anchor Watch)', 'Como ativo o alarme de âncora no rádio?',
                ['Como paro o alarme de fundeio do rádio?', 'Como mudo o raio do alarme de âncora do rádio?', "O que significa 'Exceeded anchor radius'?"],
                'O Anchor Watch soa um alarme se o barco fundeado derivar além do raio definido; o plotter do rádio mostra o ponto de partida e o raio do alarme.',
                p=['Confirme que o rádio tem GPS válido, com posição na tela.',
                   'Ajuste Audible Alarm e o raio (Range, de 0,01 a 6,00 NM) em Menu > Settings > Navigation > Anchor watch.',
                   'Pressione a tecla de software Anchor (ou Menu > Navigation > Start Anchor Watch) para iniciar.',
                   'Se o barco passar do raio, a tela mostra Exceeded anchor radius!.', 'Para parar, pressione Stop Anchor e confirme.'],
                at='Posição digitada à mão não acompanha o movimento do barco: para vigiar a deriva, o rádio precisa de GPS válido.',
                ver=('VH-27', 'EL-03', 'AN-02')),
    # ——— Rádios VHF Icom (falha, limpeza e rádio portátil) ———
    'VH-33': _f('Rádio não liga ou não responde: o que verificar', 'O rádio VHF não liga, o que verifico?',
                ['Qual fusível o IC-M510 usa?', 'O rádio travou e não responde, como reinicio?', 'Posso ligar o rádio no banco de 24 V?'],
                'Rádio que não liga costuma ter conexão de alimentação ruim ou fusível queimado; rádio ligado mas travado se resolve desligando e ligando de novo.',
                p=['Confira a conexão do cabo de alimentação no rádio e na fonte de energia.',
                   'Confira a alimentação: 13,8 V CC, na faixa de 11,7 a 15,9 V CC, com negativo à massa — nunca ligue a um banco de 24 V.',
                   'Confira o fusível do cabo de alimentação (10 A e 250 V no manual); se queimou, corrija a causa antes de trocar por outro da mesma especificação.',
                   'Rádio ligado mas sem responder: desligue e ligue de novo.', 'Se continuar sem funcionar, procure o revendedor Icom.'],
                at='O fusível fica no cabo de alimentação que acompanha o rádio.',
                ver=('VH-01', 'VH-34')),
    'VH-34': _f('Só ouço sinais fortes ou não consigo comunicar', 'Por que o rádio só pega estações muito fortes?',
                ['O rádio não comunica com ninguém, o que verifico?', 'Como sei se a antena do VHF está com defeito?', 'squelch alto bloqueando sinais fracos'],
                'Sensibilidade baixa, com só sinais fortes audíveis, ou comunicação que não se estabelece, indica antena com defeito ou conector do cabo coaxial em curto ou cortado; antes, descarte squelch alto demais. Não transmita enquanto a antena estiver desconectada.',
                p=['Confira se o squelch não está alto demais: abaixe-o até o ponto limiar e confira o volume.',
                   'Com o rádio desligado, inspecione a antena e o conector do cabo coaxial.',
                   'Havendo defeito, providencie o conserto e reconecte o cabo ao conector de antena do rádio.'],
                at='Transmitir sem antena pode danificar o rádio.',
                ver=('VH-02', 'VH-33')),
    'VH-35': _f('Água no alto-falante: AquaQuake e limpeza do rádio', 'O som do rádio está abafado, o que faço?',
                ['Como tiro a água do alto-falante do VHF?', 'Como limpo o rádio?', 'Como lavo o rádio depois de molhar com água do mar?'],
                'Água na grade do alto-falante abafa o som; o AquaQuake faz o cone vibrar e expulsa a água, por no máximo 10 segundos.',
                p=['Pressione a tecla de software AquaQuake (ou Menu > AquaQuake) e segure; solte para desligar.',
                   'Confira o conector do microfone bem rosqueado, para manter a vedação.',
                   'Depois de água salgada, lave o rádio e o microfone com água doce e seque antes de operar.',
                   'Não molhe o conector de alimentação nem os fios NMEA e de áudio externo na traseira.',
                   'Na limpeza comum, use pano macio, sem benzina, álcool ou outros solventes fortes.'],
                at='Não use o AquaQuake com alto-falante externo conectado.',
                ver=('VH-02', 'VH-41')),
    'VH-36': _f('Como carregar o rádio portátil IC-M37', 'Como carrego o rádio VHF portátil?',
                ['Quando devo carregar o portátil?', 'Posso carregar o rádio molhado?', 'A bateria do portátil descarrega rápido, o que faço?'],
                'O portátil roda na bateria própria, sem usar a energia do barco: carregue com o rádio seco, no carregador do próprio aparelho.',
                p=['Desligue o rádio e seque-o, com atenção aos contatos da bateria e do carregador.',
                   'Encaixe-o no carregador do próprio aparelho.', 'Espere o indicador mostrar carga completa antes de retirá-lo, e confirme o nível no visor.',
                   'Carregue antes de cada saída, mesmo que o rádio tenha ficado desligado.'],
                at='Não carregue o rádio nem a bateria molhados; bateria que não segura a carga está no fim da vida e deve ser trocada por uma do fabricante.',
                ver=('VH-40', 'VH-38')),
    'VH-37': _f('Como mudar de canal no rádio portátil', 'Como mudo de canal no VHF portátil?',
                ['Como volto ao canal 16 no portátil?', 'O que é canal de trabalho?', 'Por que não converso no canal 16?'],
                'O portátil fica em um canal por vez; mude pelas teclas de canal e volte ao canal 16 pelo atalho do próprio rádio.',
                p=['Veja no visor o canal ativo.', 'Use as teclas de canal até o número desejado e confirme no visor.',
                   'Ouça o canal por alguns segundos antes de transmitir; se estiver em uso, espere ou escolha outro.',
                   'Para voltar ao canal 16, use o atalho do canal 16 do rádio.'],
                at='O canal 16 é para a chamada inicial e a escuta: a conversa segue em outro canal de trabalho.',
                ver=('VH-04', 'VH-36')),
    'VH-38': _f('Potência alta ou baixa no rádio portátil', 'Como mudo a potência do rádio portátil?',
                ['Quando uso potência alta no VHF?', 'Por que a bateria do portátil acaba rápido?', 'O portátil alcança tão longe quanto o rádio fixo?'],
                'O portátil transmite em potência alta ou baixa; a alta alcança mais longe e gasta mais bateria, e a baixa serve para distâncias curtas e poupa bateria.',
                p=['Veja no visor qual potência está ativa.', 'Troque pela tecla ou pelo ajuste do rádio antes de falar.',
                   'Use potência baixa em conversa curta, como entre barcos próximos ou com a marina ao lado.',
                   'Use potência alta quando a outra estação estiver longe ou não responder em baixa, e volte à baixa depois.'],
                at='O alcance do portátil é bem menor que o do rádio fixo: a antena é menor e fica mais baixa. Alguns canais só transmitem em potência baixa por norma.',
                ver=('VH-06', 'VH-37')),
    'VH-39': _f('O portátil flutua e resiste à água? Cuidados após molhar', 'O rádio portátil flutua?',
                ['Deixei o portátil cair na água, o que faço?', 'Posso lavar o rádio portátil com água doce?', 'Molhou o portátil, posso carregar?'],
                'Alguns rádios portáteis marítimos flutuam e resistem à água, mas só com a bateria e as tampas bem encaixadas; confirme no manual do fabricante o que o seu modelo suporta.',
                p=['Antes de sair, confira a bateria bem encaixada e as tampas e vedações no lugar.', 'Use a cordinha de pulso nas manobras de borda.',
                   'Se cair na água, recupere sem se arriscar nem se debruçar na borda.',
                   'Se o manual indicar resistência à água, depois de água salgada enxágue com água doce, com as tampas fechadas, e seque com pano macio.',
                   'Se entrou água: desligue, seque por fora, tire a bateria e deixe secar em lugar ventilado; só ligue ou carregue com o rádio seco por dentro.'],
                at='Tampa solta ou vedação ressecada tira a proteção contra água; sem confirmação no manual de que o modelo flutua e resiste à água, não o enxágue — só seque com pano.',
                ver=('VH-35', 'VH-40')),
    'VH-40': _f('Como deixar o rádio portátil pronto antes de sair', 'O que confiro no rádio portátil antes de sair?',
                ['Como testo o portátil com o rádio fixo?', 'O portátil está pronto para uso?', 'Posso testar o rádio no canal 16?'],
                'O portátil só ajuda se estiver pronto: confira a carga, a antena, as tampas e vedações, o volume e o silenciador, e faça um teste curto com o rádio fixo.',
                p=['Veja o nível de bateria no visor; carregue se não estiver cheia.', 'Confira a antena bem presa e sem trincas, e as tampas e vedações no lugar.',
                   'Ajuste o volume e o silenciador para ouvir sem chiado forte.',
                   'Ponha o portátil e o rádio fixo no mesmo canal de trabalho livre, em potência baixa, e fale em um e ouça no outro.',
                   'Terminado o teste, volte os dois ao canal 16: o fixo em escuta permanente e o portátil carregado e seco.'],
                at='Não faça o teste no canal 16: use um canal de trabalho livre e seja breve.',
                ver=('VH-36', 'VH-10', 'VH-04')),
    'VH-41': _f('Chiado no portátil ou sem ouvir: silenciador e volume', 'O rádio portátil só chia, o que faço?',
                ['Como ajusto o silenciador?', 'Não ouço ninguém no portátil.', 'Para que serve o squelch?'],
                'O silenciador (squelch) corta o chiado quando não há sinal: alto demais, corta também vozes fracas; baixo demais, deixa o chiado constante.',
                p=['Com ninguém falando no canal, ajuste o volume a um nível confortável.',
                   'Reduza o silenciador até ouvir o chiado de fundo, depois aumente aos poucos até ele cessar.',
                   'Se perder vozes distantes, reduza um pouco o silenciador.',
                   'Chiado que volta toda hora: afaste o rádio de fontes de ruído, como carregadores e telas.',
                   'Sem som nenhum: confira a bateria, o volume, o canal e se o rádio não está em varredura ou dupla escuta.'],
                ver=('VH-02', 'VH-39')),
    # ——— Sistema elétrico ———
    'EE-01': _f('Bancos de baterias', 'Quantas baterias tem o barco e como estão ligadas?',
                ['bancos de 24 V e 12 V', 'banco de partida dos motores', 'carregador de bordo'], [0, 1], p=[], ver=('EE-02', 'SK-01')),
    'EE-02': _f('Faixas de tensão das baterias', 'Qual a tensão normal dos bancos de baterias?',
                ['tensão baixa nas baterias', 'faixa do banco de 12 V', 'banco de serviço de 24 V'], [0, 1], p=[], se=2, ver=('EE-03', 'CK-01')),
    'EE-03': _f('Verificação das baterias', 'Quando verifico as baterias?',
                ['conferir as tensões antes de sair', 'bornes das baterias', 'verificação dos bancos a cada 6 meses'], [0, 1], p=[]),
    'EE-04': _f('Separação dos três bancos de baterias', 'Por que os bancos de baterias são separados?',
                ['qual banco alimenta o estabilizador', 'para que serve o banco de partida', 'diferença entre banco de serviço e banco de partida'],
                'A separação em três bancos protege a partida dos motores: o consumo da casa de bordo não descarrega o banco de partida, e o '
                'estabilizador e a eletrônica de 12 V têm banco próprio. As oito baterias são Victron AGM Super Cycle, de 12 V e 230 Ah cada: '
                'quatro formam o banco de serviço de 24 V, duas o banco de partida de 24 V e duas, em paralelo, o banco de 12 V. O carregador '
                'de bordo repõe os três bancos quando ligado ao gerador ou ao cais, e cada banco tem a própria faixa de tensão no painel e na '
                'telemetria. Os três bancos têm limites diferentes: não compare a tensão de 24 V com a de 12 V. Confira os três antes de sair: '
                'um banco fora da faixa não é compensado pelos outros.',
                a='Três bancos separados: serviço, partida e 12 V, cada um com a própria faixa.',
                p=['Identifique o banco de serviço de 24 V, com quatro baterias: abastece o serviço de bordo em 24 V, como o dessalinizador.',
                   'Identifique o banco de partida de 24 V, com duas baterias: reservado à partida dos motores.',
                   'Identifique o banco de 12 V, com duas baterias em paralelo: alimenta a eletrônica de 12 V e o estabilizador.',
                   'Lembre que o carregador de bordo repõe os três bancos quando está ligado ao gerador ou ao cais.',
                   'Leia no painel e na telemetria a tensão de cada banco, cada um com a própria faixa de aviso.',
                   'Confira os três bancos antes de sair: um banco fora da faixa não é compensado pelos outros.'],
                at='Os três bancos têm limites diferentes: não compare a tensão de 24 V com a de 12 V.',
                ver=('EE-01', 'EE-05', 'SK-01')),
    'EE-05': _f('Ler a tensão das baterias no painel e na telemetria', 'Como leio a tensão das baterias no painel e na telemetria?',
                ['tensão normal dos bancos de 24 V e 12 V', 'a tensão dentro da faixa quer dizer que a bateria está carregada',
                 'por que a tensão muda quando o gerador liga'],
                'O painel e a telemetria mostram a tensão de cada banco: serviço de 24 V, partida de 24 V e banco de 12 V. A faixa normal é de '
                '24,4 a 29,4 V nos bancos de 24 V e de 12,2 a 14,7 V no banco de 12 V. A tensão é o sinal mais rápido do estado das baterias, '
                'mas muda com as cargas ligadas e com o carregador: com ele ligado, ela sobe em relação ao repouso; sem ele, cai com o uso das '
                'cargas. Para avaliar a carga das baterias, leia com o carregador desligado há algum tempo e com poucas cargas ligadas, e leia '
                'de novo depois de alguns minutos para ver se a tensão sobe, se mantém ou cai. Leitura isolada diz pouco: observe a tendência, '
                'e anote no diário qualquer banco fora da faixa, com a tensão e a hora.',
                a='Compare a leitura com a faixa do banco e observe a tendência.',
                p=['Abra a leitura de baterias no painel ou na telemetria e identifique os três bancos.',
                   'Compare cada leitura com a faixa do banco: de 24,4 a 29,4 V nos de 24 V e de 12,2 a 14,7 V no de 12 V.',
                   'Note se o carregador está ligado: com ele a tensão sobe em relação ao repouso; sem ele, cai com o uso das cargas.',
                   'Para avaliar a carga das baterias, leia com o carregador desligado há algum tempo e com poucas cargas ligadas.',
                   'Leia de novo depois de alguns minutos para ver se a tensão sobe, se mantém ou cai.',
                   'Anote no diário qualquer banco fora da faixa, com a tensão e a hora.'],
                at='Leitura isolada diz pouco: observe a tendência e a situação, se está carregando, em repouso ou com carga.',
                ver=('EE-02', 'EE-04', 'EE-06')),
    'EE-06': _f('Tensão baixa no banco de baterias', 'O que faço se a tensão de um banco de baterias estiver baixa?',
                ['alarme de tensão baixa na bateria', 'o banco de 24 V está abaixo de 24,4 V', 'o banco de 12 V está abaixo de 12,2 V'],
                'Aviso abaixo de 24,4 V nos bancos de 24 V e de 12,2 V no de 12 V; crítico abaixo de 23,6 V e de 11,8 V. Tensão baixa significa '
                'banco descarregado ou consumo acima do que o carregador repõe. Veja no painel qual banco está baixo (serviço de 24 V, partida '
                'de 24 V ou 12 V) e desligue o que não for necessário nele; no banco de partida, evite partidas repetidas dos motores. Confirme '
                'o carregador de bordo ligado ao gerador ou ao cais e ligue o gerador, se preciso, para recarregar. Olhe os bornes do banco: '
                'limpos e sem cabo frouxo. Se achar corrosão ou folga, chame o técnico. Acompanhe a tensão subir no painel: depois de carregar, '
                'ela deve voltar à faixa normal. Se o banco não sobe, ou cai logo depois de desligar o carregador, chame o técnico: a bateria '
                'pode estar no fim da vida. Banco de partida baixo pode não dar partida nos motores: recarregue antes de sair. No nível crítico, '
                'evite novas descargas: cada descarga profunda reduz a vida das baterias AGM. Registre a tensão e a hora no diário.',
                a='Veja qual banco está baixo, desligue cargas não essenciais e confirme o carregador ligado.',
                p=['Veja no painel qual banco está baixo: serviço de 24 V, partida de 24 V ou 12 V.',
                   'Desligue o que não for necessário no banco afetado; no banco de partida, evite partidas repetidas dos motores.',
                   'Confirme o carregador de bordo ligado ao gerador ou ao cais e ligue o gerador, se preciso, para recarregar.',
                   'Olhe os bornes do banco: limpos e sem cabo frouxo. Se achar corrosão ou folga, chame o técnico.',
                   'Acompanhe a tensão subir no painel: depois de carregar, ela deve voltar à faixa normal.',
                   'Se o banco não sobe, ou cai logo depois de desligar o carregador, chame o técnico: a bateria pode estar no fim da vida.',
                   'Registre a tensão e a hora no diário.'],
                at='Banco de partida baixo pode não dar partida nos motores: recarregue antes de sair. No nível crítico, evite novas descargas: '
                   'cada descarga profunda reduz a vida das baterias AGM.',
                ver=('EE-02', 'EE-05', 'EE-08')),
    'EE-07': _f('Tensão alta no banco de baterias', 'A tensão de um banco de baterias está alta, o que faço?',
                ['aviso de tensão alta na bateria', 'o banco de 24 V passou de 29,4 V', 'o banco de 12 V passou de 14,7 V'],
                'O aviso aparece acima de 29,4 V nos bancos de 24 V e acima de 14,7 V no de 12 V. Pode ser só o fim normal de uma carga forte ou '
                'falha de regulagem do carregador ou do alternador; o que diferencia é a persistência. Veja qual banco passou do limite e se o '
                'carregador de bordo ou os motores estão ligados, e espere alguns minutos com ele ligado: no fim da carga, a tensão deve baixar '
                'sozinha para a faixa normal. Se a tensão continuar acima do limite, desligue a alimentação AC do carregador de bordo e observe '
                'a queda; se o aviso só aparecer com os motores ligados, suspeite do alternador e anote o horário e o giro. Se precisou desligar '
                'o carregador, não o ligue de novo até o técnico conferir o ajuste dele para baterias AGM. Tensão acima do limite por muito '
                'tempo danifica as baterias AGM e pode passar do que os equipamentos de 12 V toleram. Bateria muito quente, estufada ou com '
                'cheiro forte: desligue o carregador, ventile o compartimento e chame o técnico. Registre no diário o banco, a tensão e a hora.',
                a='Confira se é o fim normal de uma carga forte; se a tensão não baixar, chame o técnico.',
                p=['Veja qual banco passou do limite e se o carregador de bordo ou os motores estão ligados.',
                   'Espere alguns minutos com o carregador ligado: no fim da carga, a tensão deve baixar sozinha para a faixa normal.',
                   'Se a tensão continuar acima do limite, desligue a alimentação AC do carregador de bordo e observe a queda.',
                   'Se o aviso só aparecer com os motores ligados, suspeite do alternador e anote o horário e o giro.',
                   'Registre no diário o banco, a tensão e a hora.',
                   'Se precisou desligar o carregador, não o ligue de novo até o técnico conferir o ajuste dele para baterias AGM.'],
                at='Tensão acima do limite por muito tempo danifica as baterias AGM e pode passar do que os equipamentos de 12 V toleram. '
                   'Bateria muito quente, estufada ou com cheiro forte: desligue o carregador, ventile o compartimento e chame o técnico.',
                ver=('EE-02', 'EE-06', 'EE-08')),
    'EE-08': _f('Carregar os bancos de baterias', 'Como carrego os bancos de baterias do barco?',
                ['o carregador de bordo funciona com o gerador', 'como sei que as baterias terminaram de carregar', 'como recarrego o banco de 12 V'],
                'O carregador de bordo repõe os três bancos com energia AC do gerador ou do cais. Carregar com regularidade, sem esperar o '
                'aviso de tensão baixa, preserva as baterias AGM. Garanta energia AC no quadro (gerador ligado e estável ou cabo de cais '
                'conectado) e confirme o carregador de bordo ligado e sem indicação de falha. Acompanhe a tensão dos três bancos no painel: ela '
                'deve subir em relação ao repouso. Continue carregando até as tensões ficarem estáveis dentro da faixa normal. Depois de muito '
                'uso do estabilizador e da eletrônica, recarregue o banco de 12 V antes de ligar o estabilizador de novo. Sem energia AC do '
                'gerador ou do cais, o carregador de bordo não recarrega os bancos. Registre no diário se algum banco demorou mais que o normal '
                'para carregar.',
                a='Energia AC do gerador ou do cais, com o carregador de bordo ligado.',
                p=['Garanta energia AC no quadro: gerador ligado e estável ou cabo de cais conectado.',
                   'Confirme que o carregador de bordo está ligado e sem indicação de falha.',
                   'Acompanhe a tensão dos três bancos no painel: ela deve subir em relação ao repouso e ficar dentro da faixa normal.',
                   'Deixe carregar até as tensões estabilizarem dentro da faixa normal.',
                   'Depois de muito uso do estabilizador e da eletrônica, recarregue o banco de 12 V antes de ligar o estabilizador de novo.',
                   'Registre no diário se algum banco demorou mais que o normal para carregar.'],
                at='Sem energia AC do gerador ou do cais, o carregador de bordo não recarrega os bancos.',
                ver=('EE-06', 'EE-07', 'SK-01', 'GE-02')),
    'EE-09': _f('Cuidados com as baterias AGM', 'Que cuidados as baterias AGM precisam no dia a dia?',
                ['preciso colocar água nas baterias AGM', 'como faço as baterias do barco durarem mais',
                 'posso misturar bateria nova com velha no mesmo banco'],
                'As baterias AGM Super Cycle são seladas e não precisam de água, mas sofrem com descarga profunda, carga mal regulada e bornes '
                'frouxos; poucos hábitos prolongam a vida do banco. Recarregue ao primeiro aviso de tensão baixa e evite chegar ao nível '
                'crítico, com o carregador de bordo no perfil para baterias AGM (peça ao técnico para conferir o ajuste). Olhe os bornes de vez '
                'em quando: limpos, secos e sem cabo frouxo; limpeza e aperto das conexões ficam com o técnico. Não abra as baterias nem '
                'complete água: elas são seladas. Troque as baterias de um mesmo banco em conjunto, sem misturar nova com velha, e mantenha o '
                'compartimento seco e ventilado, com as baterias bem presas contra o balanço. Evite deixar o barco parado por muito tempo sem '
                'carregador: o banco se descarrega sozinho. Só o técnico mexe nos cabos e bornes dos bancos, com as cargas e o carregador '
                'desligados.',
                a='Baterias seladas: sem água, sem descarga profunda e sem bornes frouxos.',
                p=['Recarregue ao primeiro aviso de tensão baixa e evite chegar ao nível crítico.',
                   'Use o carregador de bordo com perfil para baterias AGM; peça ao técnico para conferir o ajuste.',
                   'Olhe os bornes de vez em quando: limpos, secos e sem cabo frouxo; limpeza e aperto das conexões ficam com o técnico.',
                   'Não abra as baterias nem complete água: elas são seladas.',
                   'Troque as baterias de um mesmo banco em conjunto, sem misturar nova com velha.',
                   'Mantenha o compartimento seco e ventilado e as baterias bem presas contra o balanço.',
                   'Evite deixar o barco parado por muito tempo sem carregador: o banco se descarrega sozinho.'],
                at='Só o técnico mexe nos cabos e bornes dos bancos, com as cargas e o carregador desligados.',
                ver=('EE-06', 'EE-10')),
    'EE-10': _f('Verificação semestral dos bancos de baterias', 'Quando e como verifico os bancos de baterias e as conexões?',
                ['revisão das baterias a cada 6 meses', 'o que o técnico confere na verificação das baterias', 'como vejo se os bornes estão com corrosão'],
                'A agenda pede a verificação dos bancos e das conexões a cada 6 meses, pelo técnico. Antes de cada saída, vale a conferência '
                'rápida das tensões no painel e do aspecto dos bornes: confira as tensões dos três bancos e se estão dentro da faixa, e olhe os '
                'bornes (sem pó branco ou azulado de corrosão, sem cabo frouxo e sem sinais de aquecimento). Confira as baterias firmes nos '
                'suportes; caixa estufada, rachada ou com líquido pede o técnico antes de carregar. A cada 6 meses, peça ao técnico a '
                'verificação completa: aperto das conexões e tensão de cada bateria do banco. Confira que o jogo de fusíveis de 24 V de '
                'reposição está a bordo. Só o técnico aperta ou retira cabos dos bancos, com as cargas e o carregador desligados. Registre a '
                'verificação e as tensões no diário.',
                a='Tensões e bornes antes de sair; verificação completa do técnico a cada 6 meses.',
                p=['Antes de sair, confira as tensões dos três bancos e se estão dentro da faixa.',
                   'Olhe os bornes: sem pó branco ou azulado de corrosão, sem cabo frouxo e sem sinais de aquecimento.',
                   'Confira as baterias firmes nos suportes; caixa estufada, rachada ou com líquido pede o técnico antes de carregar.',
                   'A cada 6 meses, peça ao técnico a verificação completa: aperto das conexões e tensão de cada bateria do banco.',
                   'Confira que o jogo de fusíveis de 24 V de reposição está a bordo.',
                   'Registre a verificação e as tensões no diário.'],
                at='Só o técnico aperta ou retira cabos dos bancos, com as cargas e o carregador desligados.',
                ver=('EE-03', 'EE-09')),
    # ——— Dessalinizador ———
    'DS-01': _f('Ligar o dessalinizador', 'Como ligo o dessalinizador?',
                ['fazer água doce a bordo', 'dessalinizador: válvula de fundo e pré-filtro', 'ligar o dessalinizador pelo painel'],
                'Abra a válvula de fundo do dessalinizador, confira o pré-filtro limpo e ligue pelo painel, com o banco de serviço carregado; a '
                'pressão sobe sozinha.',
                a='Válvula de fundo aberta, pré-filtro limpo e liga pelo painel.', ver=('DS-02', 'DS-03')),
    'DS-02': _f('Produção do dessalinizador', 'Quanta água o dessalinizador faz por hora?',
                ['produção nominal em litros por hora', 'salinidade da água produzida', 'água dos primeiros minutos'],
                [0], p=['Descarte a água dos primeiros minutos depois de ligar.', 'Confira a salinidade no painel antes de mandar a água para o tanque.']),
    'DS-03': _f('Desligar e lavar o dessalinizador', 'Como desligo o dessalinizador?',
                ['lavagem com água doce no fim do ciclo', 'desligar o dessalinizador pelo painel', 'dessalinizador com o barco parado'], [0], p=[1]),
    'DS-04': _f('Manutenção do dessalinizador', 'Quando troco os pré-filtros do dessalinizador?',
                ['pré-filtros do dessalinizador', 'conservação da membrana', 'dessalinizador parado por muito tempo'], [0, 1], p=[]),
    'DS-05': _f('Água para produzir no dessalinizador', 'Posso fazer água doce na marina?',
                ['Como ligo o dessalinizador?', 'O que confiro antes de fazer água doce?', 'Como faço água doce no barco?'],
                ('O dessalinizador faz água doce do mar por osmose reversa. Escolha água limpa para produzir, longe de marinas, de saídas de '
                 'esgoto e de manchas de óleo ou combustível. Antes de ligar, confira a tensão do banco de serviço no painel, normal de %s a '
                 '%s V. Nunca ligue com a válvula de fundo fechada: a bomba de alta pressão não pode trabalhar sem água. Depois da partida, '
                 'observe mangueiras e conexões; qualquer pingo ou ruído de ar pede desligar e revisar antes de continuar.') % (
                    br(LIMITES['bateria_0_tensao_v']['normal']['de']), br(LIMITES['bateria_0_tensao_v']['normal']['ate'])),
                a='Água limpa, longe de marinas e de esgoto, com a válvula de fundo aberta antes de ligar.',
                p=['Escolha água limpa, longe de marinas, esgoto e manchas de óleo ou combustível.',
                   'Confira a tensão do banco de serviço antes de ligar.',
                   'Abra a válvula de fundo e só depois ligue pelo painel.',
                   'Observe mangueiras e conexões depois da partida; pingo ou ruído de ar pede desligar e revisar.'],
                at='Nunca ligue com a válvula de fundo fechada: a bomba de alta pressão não pode trabalhar sem água.',
                ver=('DS-01', 'DS-06', 'EE-02')),
    'DS-06': _f('Tempo de produção e nível do tanque de água', 'Quanto tempo leva para encher o tanque com o dessalinizador?',
                ['Quando mando a água do dessalinizador para o tanque?', 'Quanta água o dessalinizador produz por hora?',
                 'O que confiro no tanque antes de ligar o dessalinizador?'],
                ('Antes de começar, confira no app o nível do tanque de água doce; o aviso é abaixo de %s %%. Para estimar o tempo de '
                 'produção, divida os litros que faltam no tanque de %s L pelos %s L/h produzidos. Ao completar o tanque, desligue pelo '
                 'painel para o ciclo de lavagem rodar, sem cortar a energia. Registre no diário as horas de produção e o nível do tanque '
                 'no início e no fim.') % (
                    br(LIMITES['tanque_agua_pct']['aviso']['abaixo']), br(TANQUES['agua_l']), br(_eq('dessalinizador')['nominal']['lph'])),
                a='Divida os litros que faltam no tanque pelos %s L/h de produção.' % br(_eq('dessalinizador')['nominal']['lph']),
                p=['Confira o nível do tanque de água doce no app (aviso abaixo de 15 %).',
                   'Estime o tempo: litros que faltam, de um tanque de 400 L, divididos por 30 L/h.',
                   'Ao completar o tanque, desligue pelo painel para a lavagem rodar, sem cortar a energia.',
                   'Registre no diário as horas de produção e o nível do tanque.'],
                ver=('DS-02', 'DS-05', 'DS-07')),
    'DS-07': _f('Salinidade alta no dessalinizador', 'Como sei se a água do dessalinizador está boa?',
                ['A água do dessalinizador está salgada, o que faço?', 'O que significa salinidade alta no painel do dessalinizador?',
                 'Por que a salinidade subiu durante a produção?'],
                'O painel mostra a salinidade da água produzida durante toda a produção, não só na partida. Leitura estável dentro do '
                'limite do fabricante é água boa; leitura alta ou subindo aponta problema na membrana, nas vedações ou na água captada: '
                'mantenha essa água no descarte, sem mandar para o tanque. Antes de suspeitar da membrana, confira se a água captada está '
                'limpa e se o pré-filtro está limpo; se a salinidade continuar alta, registre no diário e chame o técnico de bordo. Água '
                'com salinidade alta que chegou ao tanque: avise o técnico de bordo antes de usá-la.',
                a='Leitura estável é água boa; leitura alta ou subindo, mantenha a água no descarte.',
                p=['Leia a salinidade no painel durante toda a produção, não só na partida.',
                   'Compare com o limite do fabricante antes de mandar a água ao tanque.',
                   'Com leitura alta ou subindo, mantenha a água no descarte.',
                   'Confira a água captada e o pré-filtro antes de suspeitar da membrana.',
                   'Se continuar alta, registre no diário e chame o técnico de bordo.'],
                at='Água com salinidade alta que chegou ao tanque: avise o técnico de bordo antes de usá-la.',
                ver=('DS-06', 'DS-08')),
    'DS-08': _f('Lavagem ao desligar o dessalinizador', 'Posso desligar o dessalinizador no meio da lavagem?',
                ['Preciso lavar o dessalinizador depois de usar?', 'Por que não posso cortar a energia na lavagem?',
                 'Posso usar água com cloro na lavagem do dessalinizador?'],
                'Água do mar parada na membrana deixa sal e cria limo; por isso o desligamento sempre termina com a lavagem com água doce. '
                'Desligue pelo painel do dessalinizador, nunca pelo disjuntor, e não interrompa o ciclo nem corte a energia no meio da '
                'lavagem: a água do mar fica parada na membrana. Água com cloro danifica a membrana: confirme com o técnico de bordo a '
                'água usada na lavagem. Terminada a lavagem, observe mangueiras e conexões, sem pingos nem manchas de sal, e registre no '
                'diário as horas produzidas e o nível do tanque.',
                a='Desligue pelo painel, nunca pelo disjuntor, e não interrompa a lavagem nem corte a energia.',
                p=['Desligue pelo painel do dessalinizador, nunca pelo disjuntor.',
                   'Espere o ciclo de lavagem com água doce terminar, sem interromper.',
                   'Confirme com o técnico de bordo a água usada na lavagem (sem cloro).',
                   'Observe mangueiras e conexões e registre no diário as horas e o nível do tanque.'],
                at='Água com cloro danifica a membrana: confirme com o técnico de bordo a água usada na lavagem.',
                ver=('DS-03', 'DS-11')),
    'DS-09': _f('Produção abaixo do normal no dessalinizador', 'O que derruba a produção do dessalinizador?',
                ['Por que o dessalinizador está fazendo pouca água?', 'O dessalinizador não chega a 30 litros por hora, é normal?',
                 'Posso aumentar a pressão para compensar a produção baixa?'],
                ('A produção nominal é de %s L/h, mas cai com pré-filtro sujo, água fria, tensão baixa no banco de serviço (abaixo de %s V '
                 'é aviso) ou ar nas mangueiras de captação. Confira a válvula de fundo totalmente aberta, o pré-filtro, a tensão no '
                 'painel e bolhas na linha de captação antes de suspeitar da membrana; uma queda pequena com água do mar mais fria é '
                 'normal. Não tente compensar a produção baixa mexendo na pressão do sistema. Se a produção continuar baixa com tudo '
                 'conferido, registre no diário e chame o técnico de bordo.') % (
                    br(_eq('dessalinizador')['nominal']['lph']), br(LIMITES['bateria_0_tensao_v']['aviso']['abaixo'])),
                a='Confira válvula, pré-filtro, tensão do banco e ar nas mangueiras antes de suspeitar da membrana.',
                p=['Confirme a válvula de fundo totalmente aberta.',
                   'Confira o pré-filtro e troque o elemento se estiver sujo.',
                   'Confira a tensão do banco de serviço no painel.',
                   'Procure vazamentos e bolhas de ar nas mangueiras de captação.',
                   'Se continuar baixa, registre no diário e chame o técnico de bordo.'],
                at='Não tente compensar a produção baixa mexendo na pressão do sistema.',
                ver=('DS-02', 'DS-05', 'DS-10')),
    'DS-10': _f('Troca do pré-filtro do dessalinizador', 'Como troco o pré-filtro do dessalinizador?',
                ['O pré-filtro do dessalinizador está sujo, o que faço?', 'Posso usar qualquer filtro no lugar do original?',
                 'Preciso desligar a energia para trocar o pré-filtro?'],
                'Os pré-filtros protegem a bomba e a membrana da sujeira; elemento sujo derruba a produção e força o equipamento, e a '
                'troca vem antes do intervalo da agenda se a produção cair. Para trocar: desligue pelo painel, espere a lavagem terminar, '
                'feche a válvula de fundo e deixe o equipamento sem energia durante o serviço. Abra devagar o alojamento do pré-filtro, '
                'porque pode haver pressão residual; retire o elemento usado, limpe o alojamento e instale o elemento novo, sempre do '
                'mesmo tipo e do mesmo grau de filtragem do original, com o anel de vedação limpo e bem assentado. Use sempre elemento do '
                'mesmo tipo: um filtro mais fino ou mais grosso muda a vazão e a proteção da membrana. Feche o alojamento, abra a válvula '
                'de fundo, ligue pelo painel e procure vazamentos nos primeiros minutos; registre a troca no diário e reponha o elemento '
                'no estoque de sobressalentes.',
                a='Desligue, espere a lavagem, feche a válvula de fundo e troque pelo mesmo tipo de elemento, sem energia.',
                p=['Desligue pelo painel, espere a lavagem terminar, feche a válvula de fundo e deixe sem energia.',
                   'Abra devagar o alojamento: pode haver pressão residual.',
                   'Retire o elemento usado e limpe o alojamento.',
                   'Instale o elemento novo, do mesmo tipo e grau de filtragem, com o anel de vedação bem assentado.',
                   'Feche o alojamento, abra a válvula de fundo, ligue pelo painel e procure vazamentos.',
                   'Registre a troca no diário e reponha o elemento no estoque de sobressalentes.'],
                at='Use sempre elemento do mesmo tipo: um filtro mais fino ou mais grosso muda a vazão e a proteção da membrana.',
                ver=('DS-04', 'DS-09')),
    'DS-11': _f('Conservar a membrana com o barco parado', 'O que faço com o dessalinizador se o barco ficar parado muito tempo?',
                ['Preciso conservar a membrana do dessalinizador?', 'Quem faz a conservação da membrana?',
                 'Posso usar qualquer produto químico na membrana?'],
                'A membrana não pode secar nem ficar parada com água do mar; por isso, para uma parada longa, a conservação é serviço do '
                'técnico de bordo, com o produto e o procedimento do fabricante. Antes da parada, termine o uso com o ciclo completo de '
                'lavagem com água doce e, com o equipamento parado, mantenha a válvula de fundo do dessalinizador fechada. Não use '
                'produto químico na membrana por conta própria: cada fabricante define o produto e o prazo. Registre no diário a data da '
                'conservação e quem a fez; para voltar a produzir, siga a orientação do técnico e descarte a água do início.',
                a='Termine com o ciclo completo de lavagem, feche a válvula de fundo e chame o técnico de bordo.',
                p=['Antes da parada, termine o uso com o ciclo completo de lavagem com água doce.',
                   'Chame o técnico de bordo para conservar a membrana conforme o manual do fabricante.',
                   'Mantenha a válvula de fundo fechada enquanto o equipamento estiver parado.',
                   'Registre no diário a data da conservação e quem a fez.',
                   'Para voltar a produzir, siga a orientação do técnico e descarte a água do início.'],
                at='Não use produto químico na membrana por conta própria: cada fabricante define o produto e o prazo.',
                ver=('DS-04', 'DS-08')),
    # ——— Bombas de porão ———
    'PO-01': _f('Como funcionam as bombas de porão', 'As bombas de porão ligam sozinhas?',
                ['sensor de nível do porão', 'ciclos das bombas de porão', 'bombas automáticas de BB e BE'], [0, 1], p=[], ver=('PO-02', 'PO-03')),
    'PO-02': _f('Nível normal do porão', 'Qual o nível normal do porão?',   # sem «água no porão»: a frase é da lista SOS (relato) e abriria a resposta de emergência (revisão da 1b)
                ['nível do poço das bombas', 'alarme de nível do porão', 'porão acima do normal'],
                [0, 1, 'Nível subindo com a bomba ligada ou água entrando é alagamento: use o SOS do app.'], p=[], se=2, ver=('PO-04', 'EM-06')),
    'PO-03': _f('Teste mensal das bombas de porão', 'Como testo as bombas de porão?',
                ['acionar a bomba de porão no manual', 'teste mensal do porão', 'alarme do painel do porão'],
                'Uma vez por mês, acione cada bomba no manual e registre o teste no diário.',
                p=['Acione cada bomba no manual.', 'Confira a saída pelo casco e o alarme do painel.', 'Registre o teste no diário.'], ver=('PO-01', 'CK-02')),
    'PO-04': _f('Água entrando: bombas de porão', 'Entrou água no barco, o que faço?',
                ['alagamento no porão', 'água subindo no porão', 'bomba de porão sem dar conta'],
                [0, 1], p=['Ligue as bombas de porão no manual.', 'Procure a entrada (válvulas de fundo, mangueiras, eixos) e feche o que puder.', 1],
                ver=('EM-06', 'PO-02')),
    'PO-05': _f('Bomba de porão no automático ou no manual', 'Qual a diferença entre automático e manual na bomba de porão?',
                ['chave da bomba no painel', 'esgotar o porão pelo manual', 'bomba esquecida no manual'],
                'No automático, o sensor de nível comanda a bomba; no manual, ela funciona por comando seu, sem depender do '
                'sensor. A posição de uso normal é o automático. Use o manual só para testar ou esgotar o poço: confirme a '
                'saída de água pelo casco e devolva ao automático depois. Bomba esquecida no manual descarrega as baterias e '
                'pode se danificar trabalhando a seco.',
                a='Uso normal: as duas bombas no automático.',
                p=['Use o manual só para testar ou esgotar o poço.',
                   'Confirme a saída de água pelo casco e devolva a bomba ao automático depois.',
                   'Ao sair do barco, confira as duas bombas no automático.'],
                ver=('PO-01', 'PO-03')),
    'PO-06': _f('Alarme de nível alto no porão', 'O alarme de nível do porão apareceu, o que confiro?',
                ['nível acima de 5 cm no porão', 'nível crítico do porão', 'poço BB ou BE acima do normal'],
                'O aviso de nível no porão aparece acima de 5 cm; acima de 10 cm é crítico. Veja no painel qual poço passou '
                'do normal, BB ou BE, e se o nível está subindo, estável ou baixando. Acima de 10 cm, ou subindo mesmo com a '
                'bomba ligada, pare este roteiro e siga o protocolo de bordo. Confirme a bomba daquele lado ligada; se '
                'estiver parada, passe para o manual e confirme a saída de água pelo casco. Com o nível de volta ao normal, '
                'devolva a bomba ao automático, procure a origem da água (chuva, lavagem do convés, mangueiras e conexões) e '
                'registre no diário o poço, o nível máximo e a hora.',
                a='Acima de 10 cm, ou subindo com a bomba ligada: siga o protocolo de bordo.',
                p=['Veja qual poço passou do normal, BB ou BE, e se o nível está subindo, estável ou baixando.',
                   'Acima de 10 cm, ou subindo mesmo com a bomba ligada: siga o protocolo de bordo.',
                   'Confirme a bomba daquele lado ligada; se parada, passe para o manual e confirme a saída pelo casco.',
                   'Com o nível normal de novo, procure a origem da água: chuva, lavagem do convés, mangueiras e conexões.',
                   'Registre no diário o poço, o nível máximo e a hora.'],
                ver=('PO-02', 'PO-04', 'PO-07', 'PO-08')),
    'PO-07': _f('Bomba de porão que não parte', 'A bomba de porão não liga, o que faço?',
                ['bomba de porão não liga', 'bomba zumbindo sem girar', 'disjuntor ou fusível da bomba de porão'],
                'A bomba não parte no automático, no manual ou nos dois. Nível no painel acima de 10 cm, ou subindo: pare '
                'este roteiro e siga o protocolo de bordo antes de continuar. Passe a bomba para o manual: se ela partir, o '
                'defeito está no sensor de nível ou no comando do automático; se zumbir sem girar, desligue-a na hora e só '
                'destrave com o disjuntor desligado. Sem partir no manual, confira o disjuntor ou o fusível da bomba e a '
                'tensão dos bancos de 24 V no painel — abaixo de 24,4 V pode faltar força. Com o disjuntor desligado, '
                'confira o conector e os fios, procurando corrosão ou fio solto, e registre o defeito no diário com a hora.',
                a='Nível subindo ou acima de 10 cm: siga o protocolo de bordo; senão, teste no manual.',
                p=['Confira se a bomba está no automático ou no manual, e não desligada.',
                   'Passe para o manual: se partir, o defeito está no sensor de nível ou no comando do automático.',
                   'Bomba zumbindo sem girar: desligue-a na hora; só destrave com o disjuntor desligado.',
                   'Sem partir no manual, confira o disjuntor ou o fusível da bomba.',
                   'Confira no painel a tensão dos bancos de 24 V: abaixo de 24,4 V pode faltar força para a bomba.',
                   'Com o disjuntor desligado, confira o conector e os fios, procurando corrosão ou fio solto.',
                   'Registre o defeito no diário com a hora e chame o técnico.'],
                ver=('PO-06', 'PO-08', 'EE-02')),
    'PO-08': _f('Bomba de porão que não desliga', 'Por que a bomba de porão liga toda hora?',
                ['bomba de porão ligando toda hora', 'contador de ciclos da bomba', 'sensor de nível preso ou sujo'],
                'Ciclos demais ou bomba ligada sem intervalo têm duas causas: sensor de nível enganado (preso ou sujo) ou '
                'água chegando aos poucos ao poço. Leia no painel o nível dessa bomba e o contador de ciclos: ciclos demais '
                'em pouco tempo pedem atenção mesmo com o nível normal. Com o nível acima de 5 cm, trate como alarme de '
                'nível e busque a origem da água; se o nível subir mesmo com a bomba ligada, pare este roteiro e siga o '
                'protocolo de bordo. Com o nível normal e muitos ciclos, procure água entrando aos poucos (mangueiras, '
                'conexões, drenos e pingos) e, com a bomba desligada no disjuntor, limpe o sensor de nível — se for do tipo '
                'flutuador, confira se ele se move livremente. Registre no diário os ciclos e o nível; chame o técnico se o '
                'problema voltar.',
                a='Nível acima de 5 cm: trate como alarme; nível normal com muitos ciclos: suspeite do sensor.',
                p=['Leia no painel o nível dessa bomba e o contador de ciclos.',
                   'Com o nível acima de 5 cm, trate como alarme de nível e busque a origem da água.',
                   'Com o nível normal e muitos ciclos, procure água entrando aos poucos: mangueiras, conexões, drenos e pingos.',
                   'Passe a bomba para o manual e de volta ao automático: se ligar de novo sem o nível subir, suspeite do sensor.',
                   'Com a bomba desligada no disjuntor, limpe o sensor de nível; se for do tipo flutuador, confira se ele se move livremente.',
                   'Registre no diário os ciclos e o nível; chame o técnico se o problema voltar.'],
                ver=('PO-06', 'PO-07')),
    'PO-09': _f('Limpeza do sensor de nível do porão', 'Como limpo o sensor de nível da bomba de porão?',
                ['limpar o sensor de nível do porão', 'entrada da bomba entupida', 'sensor tipo flutuador travado'],
                'Óleo, lodo e fiapos travam o sensor de nível e entopem a entrada da bomba, e aí ela não parte ou não para. '
                'Aproveite o teste mensal para olhar o poço e o sensor. Desligue a bomba no disjuntor antes de limpar, para '
                'ela não partir sozinha. Retire os detritos soltos do poço e limpe o sensor de nível; se for do tipo '
                'flutuador, mova-o com a mão — ele deve subir e descer livremente, sem prender em fios ou mangueiras. Limpe a entrada '
                'da bomba, sem forçar a peça, e confira cabos e conectores, sem corrosão nem isolamento rachado. Religue o '
                'disjuntor, teste a bomba no manual, devolva ao automático e registre a limpeza no diário.',
                a='Disjuntor desligado antes de limpar o sensor e a entrada da bomba.',
                p=['Desligue a bomba no disjuntor antes de limpar, para ela não partir sozinha.',
                   'Retire os detritos soltos do poço e limpe o sensor de nível.',
                   'Sensor tipo flutuador: mova-o com a mão — deve subir e descer livremente, sem prender em fios ou mangueiras.',
                   'Limpe a entrada da bomba sem forçar a peça; confira cabos e conectores, sem corrosão nem isolamento rachado.',
                   'Religue o disjuntor, teste a bomba no manual, devolva ao automático e registre a limpeza no diário.'],
                ver=('PO-03', 'PO-07')),
    # ——— Guincho e âncora ———
    'AN-01': _f('Lançar a âncora', 'Como lanço a âncora?',
                ['fundear com o guincho', 'quanto de corrente lançar', 'dar ré até a âncora unhar'],
                'Com o barco parado sobre o ponto escolhido, lance pelo controle do guincho e dê ré devagar até a âncora unhar, com corrente de '
                '%s vezes a profundidade.' % de_a(LANCE_ANCORA_VEZES),
                a='Barco parado, lance pelo guincho e dê ré devagar até unhar.', ver=('AN-02', 'EL-03', 'CK-07')),
    'AN-02': _f('Contador de corrente', 'Como sei quantos metros de corrente lancei?',
                ['marca do contador de corrente', 'metros de corrente no controle do guincho', 'contador do guincho antes do alarme de âncora'],
                [0], p=[1], ver=('AN-01', 'EL-03')),
    'AN-03': _f('Recolher a âncora e travar a corrente', 'Como recolho a âncora?',
                ['içar a âncora', 'travar a corrente', 'desligar o guincho no disjuntor'],
                'Recolha devagar, com o motor aliviando a corrente; com a âncora no lugar, trave a corrente e desligue o guincho no disjuntor.',
                ver=('CK-04',)),
    'AN-04': _f('Manutenção do guincho', 'Que cuidado o guincho precisa depois do uso?',
                ['lavar o guincho com água doce', 'corrente e destorcedor', 'conferência anual do guincho'], [0], p=[]),
    'AN-05': _f('Calcular o lance de corrente para fundear', 'Quanta corrente devo lançar?',
                ['Como calculo o lance pela profundidade?', 'Como uso o guincho para fundear?', 'Quando dou ré depois de lançar a âncora?'],
                'Calcule o lance, de %s vezes a profundidade contando a altura da proa, e confirme que cabe na corrente do barco, que tem %s m. '
                'Escolha fundo de areia ou lama, com espaço de giro livre de outros barcos, e leia a profundidade na sonda antes de lançar. '
                'Ligue o disjuntor do guincho, solte a trava e, com o barco parado sobre o ponto escolhido, lance pelo controle do guincho '
                'acompanhando os metros no contador. Perto do lance calculado, dê ré bem devagar para a âncora unhar e a corrente esticar, pare '
                'o guincho, trave a corrente, ative o alarme no plotter e registre a hora e a profundidade no diário. Com vento forte, lance '
                'mais corrente; em fundo de pedra a âncora segura mal. Mantenha mãos, pés e cabos longe da corrente e do guincho em movimento.'
                % (de_a(LANCE_ANCORA_VEZES), br(_eq('ancora')['nominal']['corrente_m'])),
                a='Calcule o lance pela profundidade e confira que cabe na corrente do barco.',
                p=['Escolha fundo de areia ou lama, com espaço de giro livre de outros barcos, e leia a profundidade na sonda.',
                   'Calcule o lance: %s vezes a profundidade, contando a altura da proa, e confirme que cabe na corrente do barco.' % de_a(LANCE_ANCORA_VEZES),
                   'Ligue o disjuntor do guincho, solte a trava da corrente e confira o contador antes de lançar.',
                   'Com o barco parado sobre o ponto escolhido, lance pelo controle do guincho, acompanhando os metros no contador.',
                   'Perto do lance calculado, dê ré bem devagar para a âncora unhar e a corrente esticar.',
                   'Pare o guincho e trave a corrente.',
                   'Ative o alarme de âncora no plotter e registre no diário a hora e a profundidade.'],
                ver=('AN-01', 'AN-06', 'CK-07')),
    'AN-06': _f('Conferir o contador de corrente antes de fundear', 'Como confiro o lance pelo contador?',
                ['Quantos metros de corrente o barco tem?', 'O contador volta a marcar zero com a âncora no rolete?',
                 'Como uso o contador para saber quanto falta recolher?'],
                'Leia os metros de corrente lançados no controle do guincho; a corrente do barco tem %s m. Ao lançar, pare ao chegar ao lance '
                'calculado, de %s vezes a profundidade da sonda, e confirme a leitura final antes de ativar o alarme de âncora no plotter. Com '
                'a âncora no rolete, o contador deve marcar zero: se não marcar, chame o técnico antes de fundear. Ao recolher, acompanhe a '
                'leitura baixando e reduza o ritmo quando a âncora se aproximar do rolete, e anote no diário os metros lançados junto com a '
                'profundidade.' % (br(_eq('ancora')['nominal']['corrente_m']), de_a(LANCE_ANCORA_VEZES)),
                a='Leia os metros no controle do guincho e confira com a profundidade da sonda.',
                p=['Com a âncora no rolete, o contador deve marcar zero; se não marcar, chame o técnico antes de fundear.',
                   'Ao lançar, leia os metros no controle do guincho e pare ao chegar ao lance calculado.',
                   'Compare a leitura com a profundidade da sonda para confirmar a proporção de %s vezes.' % de_a(LANCE_ANCORA_VEZES),
                   'Antes de ativar o alarme de âncora no plotter, confirme a leitura final do contador e anote-a.',
                   'Ao recolher, acompanhe a leitura baixando e reduza o ritmo quando a âncora se aproximar do rolete.',
                   'Anote no diário os metros lançados junto com a profundidade.'],
                ver=('AN-01', 'AN-05')),
    'AN-07': _f('Recolher a âncora sem forçar o guincho', 'Posso recolher a âncora só com o guincho?',
                ['Como uso o motor para ajudar a recolher a âncora?', 'O que faço antes de recolher a âncora?',
                 'Por que não posso puxar o barco contra o vento só com o guincho?'],
                'O guincho recolhe a corrente, mas quem alivia o esforço é o motor, aproximando o barco da âncora; recolher devagar protege o '
                'guincho, a corrente e a proa. Ligue os motores em neutro e desative o alarme de âncora no plotter antes de recolher, ligue o '
                'disjuntor do guincho e deixe-o assumir a carga da corrente antes de abrir a trava. Recolha pelo controle em trechos curtos, '
                'aproximando o barco da âncora com o motor para a corrente ficar mole e subir sem arrastar o barco; com a âncora solta do '
                'fundo, lave a lama com água doce e, com ela assentada no rolete, feche a trava e desligue o disjuntor. Não use o guincho para '
                'puxar o barco contra o vento ou a correnteza: o esforço pesado danifica o motor do guincho.',
                a='Disjuntor ligado, o guincho assume a carga e o motor aproxima o barco da âncora.',
                p=['Ligue os motores, em neutro, e deixe-os prontos para aliviar a corrente.',
                   'Desative o alarme de âncora no plotter antes de começar a recolher.',
                   'Ligue o disjuntor do guincho e deixe-o assumir a carga da corrente antes de abrir a trava.',
                   'Recolha pelo controle do guincho, em trechos curtos, aproximando o barco da âncora com o motor para a corrente ficar mole.',
                   'Acompanhe o contador e a corrente entrando: ela deve subir sem arrastar o barco.',
                   'Com a âncora solta do fundo, termine de recolher e lave a lama com água doce.',
                   'Com a âncora assentada no rolete, feche a trava da corrente e desligue o disjuntor do guincho.'],
                at='Não use o guincho para puxar o barco contra o vento ou a correnteza: o esforço pesado danifica o motor do guincho.',
                ver=('AN-03', 'AN-08')),
    'AN-08': _f('Travar a corrente e desligar o guincho no disjuntor', 'Por que travar a corrente depois de fundear?',
                ['Preciso desligar o guincho no disjuntor?', 'Quando solto a trava da corrente?', 'Como travo a corrente da âncora?'],
                'A trava segura a carga da corrente no lugar do guincho, que não foi feito para sustentar o esforço do fundeio, e impede que a '
                'corrente corra sozinha com o barco no mar. Com a âncora unhada, pare o guincho, feche a trava da corrente e solte um pouco de '
                'corrente pelo guincho até a trava assumir a carga, com a carga nela, bem firme. Desligue o guincho no disjuntor para ninguém '
                'acioná-lo por engano. Para recolher, ligue o disjuntor, deixe o guincho assumir a carga antes de abrir a trava; com a âncora '
                'no rolete, feche a trava de novo e desligue o disjuntor antes de navegar. Nunca deixe o barco preso à âncora só pelo guincho, '
                'nem navegue com a trava aberta.',
                a='Pare o guincho, feche a trava e só depois desligue o disjuntor.',
                p=['Com a âncora unhada, pare o guincho.',
                   'Feche a trava da corrente e solte um pouco de corrente pelo guincho até a trava assumir a carga.',
                   'Confira a trava bem fechada e firme na corrente, com a carga nela, não no guincho.',
                   'Desligue o guincho no disjuntor para ninguém acioná-lo por engano.',
                   'Para recolher, ligue o disjuntor, deixe o guincho assumir a carga antes de abrir a trava.',
                   'Com a âncora no rolete, feche a trava de novo e desligue o disjuntor antes de navegar.'],
                at='Nunca deixe o barco preso à âncora só pelo guincho, nem navegue com a trava aberta.',
                ver=('AN-03', 'AN-07')),
    'AN-09': _f('A âncora não segura (garrando)', 'A âncora está garrando, o que faço?',
                ['Como sei que a âncora não está segurando?', 'Quando devo aumentar o lance de corrente?',
                 'O que faço quando a âncora não unha no fundo?'],
                'Âncora que garra deixa o barco andar com o vento ou a correnteza mesmo fundeado; os sinais são o alarme de âncora do plotter, '
                'a posição saindo do raio e a corrente vibrando ou dando trancos. Confirme no plotter se a posição saiu do raio e para onde o '
                'barco está indo, chame a tripulação e ligue os motores em neutro para poder manobrar. Com espaço livre e corrente sobrando, '
                'aumente o lance e espere a âncora unhar de novo; se o barco continuar arrastando, recolha a âncora e refunde em outro ponto, '
                'com fundo melhor e mais espaço, e confira de novo o raio do alarme no plotter. Registre no diário a hora, o vento, a '
                'profundidade e o lance usado. Perto de pedras, de outros barcos ou da praia, não espere a âncora segurar: recolha e afaste-se '
                'com os motores.',
                a='Confira a posição no plotter; se estiver garrando, recolha e refunde em outro ponto.',
                p=['Confirme no plotter se a posição saiu do raio de alarme e para onde o barco está indo.',
                   'Chame a tripulação e ligue os motores, em neutro, para poder manobrar se precisar sair do local.',
                   'Se houver espaço livre e corrente sobrando, aumente o lance e espere a âncora unhar de novo.',
                   'Se o barco continuar arrastando, recolha a âncora e refunde em outro ponto, com fundo melhor e mais espaço.',
                   'Depois de refundear, confira de novo o raio do alarme de âncora no plotter.',
                   'Registre no diário a hora, o vento, a profundidade e o lance usado.'],
                at='Perto de pedras, de outros barcos ou da praia, não espere a âncora segurar: recolha e afaste-se com os motores.',
                ver=('AN-05', 'EL-03')),
    'AN-10': _f('O guincho não responde ou está fraco', 'O guincho da âncora não liga, o que confiro?',
                ['Por que o guincho está lento ou sem força?', 'O disjuntor do guincho desarma, o que pode ser?',
                 'O que confiro antes de chamar o técnico do guincho?'],
                'Guincho que não responde costuma ter o disjuntor desligado, o controle com defeito, tensão baixa nos bancos, a trava fechada '
                'ou carga demais; confira nessa ordem antes de chamar o técnico. Confirme o disjuntor do guincho ligado; se tiver desarmado, '
                'rearme uma única vez. Confira a trava da corrente: fechada, ela segura a corrente e o guincho não recolhe. Com o disjuntor '
                'desligado, olhe o cabo e o conector do controle, pois botão preso, cabo danificado ou conector úmido impedem o comando; '
                'confira também no painel se os bancos de baterias estão na faixa normal, porque tensão baixa deixa o guincho lento ou sem '
                'força. Se o guincho desligou por sobrecarga, deixe esfriar e alivie a carga aproximando o barco da âncora com o motor. Não '
                'rearme o disjuntor várias vezes: ele desarma para proteger o motor e a fiação.',
                a='Disjuntor, trava, controle, baterias e carga: confira nessa ordem antes do técnico.',
                p=['Confirme o disjuntor do guincho ligado; se tiver desarmado, rearme uma única vez.',
                   'Confira a trava da corrente: fechada, ela segura a corrente e o guincho não recolhe; abra-a só com o guincho ligado e o '
                   'barco aliviado pelo motor.',
                   'Com o disjuntor desligado, olhe o cabo e o conector do controle: botão preso, cabo danificado ou conector úmido impedem o '
                   'comando. Depois religue e teste.',
                   'Confira no painel se os bancos de baterias estão na faixa normal; tensão baixa deixa o guincho lento ou sem força.',
                   'Se o guincho desligou por sobrecarga, deixe esfriar e alivie a carga aproximando o barco da âncora com o motor.',
                   'Se nada resolver, registre no diário o sintoma e a hora e chame o técnico, sem forçar o guincho.'],
                at='Não rearme o disjuntor várias vezes: ele desarma para proteger o motor e a fiação.',
                ver=('AN-04', 'AN-11')),
    'AN-11': _f('Vistoria anual da corrente e do guincho', 'Quando confiro a corrente e o destorcedor?',
                ['Quando troco a corrente da âncora?', 'Que manutenção o guincho da âncora precisa?',
                 'Como sei se a corrente está desgastada ou enferrujada?'],
                'Sal e lama corroem o guincho e a corrente: lave tudo com água doce depois de cada uso, tirando lama e sal, e olhe o guincho e '
                'a trava, procurando ferrugem, folgas e parafusos soltos. Desligue o disjuntor do guincho antes de qualquer serviço no guincho, '
                'na trava ou nos conectores. Uma vez por ano, inspecione a corrente elo a elo (ferrugem em escamas, deformação ou desgaste '
                'pedem troca), confira o destorcedor e as manilhas, com os pinos firmes e travados, sem folga nem ferrugem, e confira os cabos '
                'e conectores elétricos do guincho, sem corrosão e bem fixos. Confira também se o contador de corrente marca de acordo com a '
                'corrente lançada e registre a vistoria anual e as peças trocadas no diário.',
                a='Lave com água doce depois do uso e faça a vistoria da corrente uma vez por ano.',
                p=['Desligue o disjuntor do guincho antes de qualquer serviço no guincho, na trava ou nos conectores.',
                   'Depois do uso, lave o guincho, a corrente e a âncora com água doce, tirando lama e sal.',
                   'Olhe o guincho e a trava, procurando ferrugem, folgas e parafusos soltos.',
                   'Uma vez por ano, inspecione a corrente elo a elo: ferrugem em escamas, deformação ou desgaste pedem troca.',
                   'Confira o destorcedor e as manilhas: pinos firmes e travados, sem folga nem ferrugem.',
                   'Confira os cabos e conectores elétricos do guincho: sem corrosão e bem fixos.',
                   'Confira se o contador de corrente marca de acordo com a corrente lançada, e registre a vistoria anual e as peças trocadas '
                   'no diário.'],
                ver=('AN-04', 'AN-10')),
    # ——— Piloto automático ———
    'PI-01': _f('Engatar o piloto automático', 'Como engato o piloto automático?',
                ['ligar o piloto Raymarine', 'piloto no posto de comando', 'engatar com o rumo conferido no plotter'],
                'Engate o piloto no controle do posto de comando, com o rumo conferido no plotter e área livre à frente.',
                a='Rumo conferido no plotter e área livre à frente.',
                p=['Engate o piloto no controle do posto de comando.', 'Confira o rumo no plotter.', 'Confira que a área à frente está livre.'],
                ver=('PI-02', 'EL-02')),
    'PI-02': _f('Piloto em espera ao manobrar', 'Quando deixo o piloto em espera?',
                ['piloto em standby', 'piloto na marina', 'piloto em situação de risco'], [0], p=[]),
    'PI-03': _f('Assumir o leme no timão', 'Como assumo o leme com o piloto ligado?',
                ['sair do piloto automático', 'governar pelo timão', 'direção hidráulica do piloto'], [0], p=[], ob=1),
    'PI-04': _f('Alarmes do piloto automático', 'O piloto deu alarme de desvio de rumo, o que faço?',
                ['desvio de rumo do piloto', 'alarme da direção hidráulica', 'piloto alarmando'], [0], p=[1]),
    'PI-05': _f('Modos do piloto automático', 'Quais são os modos do piloto automático?',
                ['diferença entre espera e automático', 'o que faz o modo trilha', 'para que serve o modo vento'],
                'O piloto governa de um jeito diferente em cada modo: em espera (standby) o timão é seu e o piloto fica inativo, sem atuar no rumo; em automático (auto) ele mantém o rumo que a proa tinha ao engatar; em trilha (track) segue a rota ativa do plotter, se o plotter enviar a rota ao piloto; em vento (wind), nos pilotos que têm esse modo, mantém um ângulo fixo em relação ao vento, comum em veleiros e a confirmar com o técnico se existe neste barco. Troque de modo pelo controle do posto de comando e confira no visor o modo ativo. Em qualquer modo, o piloto não enxerga barcos, marcas de navegação nem águas rasas: a vigia continua sendo sua.',
                a='Troque de modo pelo controle e confira o modo no visor.',
                p=['Espera (standby): o timão é seu e o piloto fica inativo, sem atuar no rumo. Use ao sair, ao chegar, em manobra e sempre que quiser o leme na mão.',
                   'Automático (auto): mantém o rumo que a proa tinha ao engatar. Use em água livre, em linha reta e com a vigia mantida.',
                   'Trilha (track): segue a rota ativa do plotter, se o plotter enviar a rota ao piloto. Confira o trajeto antes.',
                   'Vento (wind): mantém um ângulo fixo em relação ao vento, nos pilotos que têm esse modo. Confirme com o técnico se existe neste barco.',
                   'Troque de modo pelo controle do posto de comando e confira no visor o modo ativo.'],
                at='O piloto não enxerga barcos, marcas de navegação nem águas rasas: em qualquer modo, a vigia continua sendo sua.',
                ver=('PI-06', 'PI-08', 'EL-02')),
    'PI-06': _f('Passo a passo para engatar o piloto', 'O que confiro antes de engatar o piloto?',
                ['travar o rumo ao engatar', 'engatar o piloto em curva', 'mão perto do timão ao engatar'],
                'Ao engatar, o piloto trava o rumo que a proa tem naquele instante: engate com o barco estável, apontado para onde você quer ir e com água livre à frente, nunca em curva nem com o leme muito virado. Confira o controle ligado e sem alarme nem mensagem, mantenha a proa no rumo desejado com velocidade e leme estáveis por alguns segundos, confira o rumo no plotter e a área à frente livre de barcos, marcas de navegação, redes de pesca e águas rasas, e engate pelo controle do posto de comando, com a mão perto do timão. Observe o barco logo depois: o rumo deve se manter; se ele guinar ou oscilar muito, volte à espera e assuma o timão, e mantenha a vigia conferindo o rumo de tempos em tempos.',
                a='Barco estável, rumo apontado e área livre à frente.',
                p=['Confira que o controle do piloto está ligado e sem alarme nem mensagem.',
                   'Aponte a proa para o rumo desejado e mantenha velocidade e leme estáveis por alguns segundos.',
                   'Confira o rumo no plotter e a área à frente livre de barcos, marcas de navegação, redes de pesca e águas rasas.',
                   'Engate em automático pelo controle do posto de comando, com a mão perto do timão.',
                   'Observe o barco logo depois de engatar: o rumo deve se manter; se ele guinar ou oscilar muito, volte à espera e assuma o timão.',
                   'Mantenha a vigia e confira o rumo de tempos em tempos.'],
                at='Não engate em curva nem com o leme muito virado: estabilize o barco antes.',
                ver=('PI-01', 'PI-09', 'EL-02')),
    'PI-07': _f('Mudar o rumo com o piloto engatado', 'Como mudo o rumo com o piloto ligado?',
                ['curva com o piloto automático', 'ajustar o rumo sem desengatar', 'curva fechada com o piloto'],
                'Com o piloto engatado, mude o rumo pelas teclas de ajuste do controle, para bombordo ou boreste, em toques curtos e correções leves, sem pressa; para curvas fechadas ou para desviar de algo, assuma o timão em vez de ajustar, e não gire o timão com o piloto engatado. Antes de qualquer curva, olhe ao redor, avise a tripulação e veja no plotter o que há no novo rumo: raso, obstáculo, rede ou outro barco; espere o barco completar a curva antes de dar outro ajuste e confira o novo rumo no controle e no plotter.',
                a='Teclas de ajuste, em toques curtos; curva fechada: assuma o timão.',
                p=['Olhe ao redor e avise a tripulação antes de qualquer curva.',
                   'Veja no plotter o que há no novo rumo: raso, obstáculo, rede ou outro barco. Se houver algo perto, assuma o timão em vez de ajustar.',
                   'Use as teclas de ajuste de rumo do controle, para bombordo ou boreste, em toques curtos e correções leves, sem pressa.',
                   'Espere o barco completar a curva antes de dar outro ajuste.',
                   'Confira o novo rumo no controle e no plotter.'],
                at='Para mudar o rumo, use o controle ou assuma o timão: não gire o timão com o piloto engatado.',
                ver=('PI-06', 'PI-08', 'PI-09')),
    'PI-08': _f('Piloto em modo trilha, seguindo a rota', 'Como faço o piloto seguir a rota do plotter?',
                ['piloto virando nos pontos da rota', 'piloto não aceita a rota do plotter', 'sair do modo trilha'],
                'Em trilha (track), o piloto governa para seguir a rota ativa do plotter; depende de o plotter enviar os dados da rota ao piloto, e esse modo precisa ser confirmado com o técnico neste barco. Antes de engatar, ative a rota no plotter e confira o traçado inteiro: terra, rasos, redes e barcos fundeados fora do caminho. Engate com o barco no rumo do primeiro trecho e em água livre, escolha o modo trilha e confira se o piloto aceitou a rota, sem mensagem de erro, antes de tirar a mão do timão; em cada ponto da rota, fique pronto para confirmar a curva pelo controle, se ele pedir, ou para assumir o timão se o barco não virar. O piloto segue a linha da rota e não desvia de barcos nem de obstáculos, então a vigia continua sua; se o modo trilha não ligar, use automático e corrija o rumo à mão, e para sair da trilha, ponha em espera e assuma o timão.',
                a='Rota conferida no plotter, piloto em trilha, com a mão perto do timão.',
                p=['Ative a rota no plotter e confira o traçado inteiro: terra, rasos, redes e barcos fundeados fora do caminho.',
                   'Com o barco no rumo do primeiro trecho e em água livre, engate o piloto e escolha o modo trilha pelo controle.',
                   'Confira se o piloto aceitou a rota, sem mensagem de erro, antes de tirar a mão do timão.',
                   'Em cada ponto da rota, fique pronto para confirmar a curva pelo controle, se ele pedir, ou para assumir o timão se o barco não virar.',
                   'Mantenha a vigia: o piloto segue a linha da rota e não desvia de barcos nem de obstáculos.',
                   'Para sair da trilha, ponha em espera e assuma o timão.'],
                at='Trilha só funciona com plotter e piloto trocando dados de rota: se o modo não liga, use automático e corrija o rumo à mão. Confira a rota inteira antes de cada saída; o piloto não sabe o que há no caminho.',
                ver=('PI-05', 'PI-06', 'PI-09')),
    'PI-09': _f('Assumir o timão com o piloto engatado', 'Como assumo o timão com o piloto ligado?',
                ['devolver o governo ao timão', 'o piloto soltou sozinho', 'girar o timão com o piloto automático'],
                'Para devolver o governo ao timão, ponha o piloto em espera pelo controle; faça isso com folga, e não no último momento, para sentir o leme antes de precisar dele, e não force o timão com o piloto engatado. Segure o timão com firmeza antes de mexer no controle, pressione a tecla de espera (standby) no posto de comando, gire o timão um pouco para os dois lados e confirme que o barco responde normalmente, e avise a tripulação que o piloto está em espera. Se o piloto saiu sozinho do automático, mantenha o rumo no timão e leia a mensagem do controle antes de engatar de novo.',
                a='Segure o timão, aperte espera no controle e confirme a resposta do leme.',
                p=['Segure o timão com firmeza antes de mexer no controle.',
                   'Pressione a tecla de espera (standby) no controle do posto de comando.',
                   'Gire o timão um pouco para os dois lados e confirme que o barco responde normalmente.',
                   'Governe pelo timão e avise a tripulação que o piloto está em espera.',
                   'Se o piloto saiu sozinho do automático, mantenha o rumo no timão e leia a mensagem do controle antes de engatar de novo.'],
                at='Não force o timão com o piloto engatado: ponha em espera primeiro.',
                ver=('PI-06', 'PI-02', 'PI-14')),
    'PI-10': _f('Piloto em espera na marina e em manobra', 'Por que deixar o piloto em espera para manobrar?',
                ['piloto automático na marina', 'quando engatar depois de sair da marina', 'piloto em espera ao chegar'],
                'O piloto não enxerga nada e foi feito para manter rumo em velocidade de viagem; em marina, canal estreito, fundeio e atracação, deixe-o em espera e governe pelo timão e pelas manetes, sem voltar ao automático. Na saída, mantenha-o em espera até passar o canal da marina e chegar à água livre, e só então engate, com a rota conferida no plotter e sem barcos, marcas de navegação ou águas rasas à frente. Na chegada, ponha o piloto em espera com folga, antes do canal de acesso ou da área de manobra; com barcos e píeres por perto, não confie no piloto, porque ele não desvia de nada.',
                a='Em marina, canal e manobra: piloto em espera, governo pelo timão e pelas manetes.',
                p=['Na saída, mantenha o piloto em espera e governe pelo timão e pelas manetes até passar o canal da marina e chegar à água livre.',
                   'Só então engate: com a rota conferida no plotter e sem barcos, marcas de navegação ou águas rasas à frente.',
                   'Na chegada, ponha o piloto em espera com folga, antes do canal de acesso ou da área de manobra.',
                   'Em toda aproximação, manobra e atracação, governe pelo timão e pelas manetes, sem voltar ao automático.'],
                at='Com barcos e píeres por perto, não confie no piloto: ele não desvia de nada.',
                ver=('PI-02', 'PI-09', 'CK-04')),
    'PI-11': _f('Alarme de desvio de rumo do piloto', 'O piloto apitou desvio de rumo, o que faço?',
                ['silenciar o alarme do piloto', 'alarme de desvio de rumo', 'engatar de novo depois do alarme'],
                'O alarme de desvio de rumo toca quando o barco se afasta do rumo ajustado além do limite programado no piloto; a causa pode ser mar, vento, corrente ou falha do piloto, então primeiro governe, depois investigue. Assuma o timão, ponha o piloto em espera pelo controle e silencie o alarme depois de ter o barco governado; compare o rumo que o barco faz no plotter com o que você queria seguir e procure a causa provável (mar de través, vento forte, corrente ou mudança de velocidade). Se foi o mar ou o vento, siga à mão ou reduza a velocidade e só engate de novo com o barco estável; se o alarme voltar sem causa visível, siga à mão e chame o técnico, e registre no diário a hora e o que estava acontecendo. Alarme repetido pode apontar problema no sensor de rumo, na bomba ou na energia: não insista em engatar.',
                a='Assuma o timão, ponha em espera, silencie o alarme e investigue a causa.',
                p=['Assuma o timão e ponha o piloto em espera pelo controle.',
                   'Silencie o alarme pelo controle depois de ter o barco governado.',
                   'Compare o rumo que o barco faz no plotter com o que você queria seguir.',
                   'Procure a causa provável: mar de través, vento forte, corrente ou mudança de velocidade.',
                   'Se foi o mar ou o vento, siga à mão ou reduza a velocidade e só engate de novo com o barco estável.',
                   'Se o alarme voltar sem causa visível, siga à mão e chame o técnico.',
                   'Registre no diário a hora e o que estava acontecendo.'],
                at='Alarme repetido pode apontar problema no sensor de rumo, na bomba ou na energia: não insista em engatar.',
                ver=('PI-12', 'PI-13', 'PI-09')),
    'PI-12': _f('Rumo do piloto errado ou alarme do sensor', 'O rumo do piloto não bate com o plotter, o que faço?',
                ['sensor de rumo do piloto', 'interferência no sensor de rumo', 'quem corrige o sensor de rumo'],
                'O piloto usa o sensor de rumo (uma bússola eletrônica) para saber para onde a proa aponta; se o rumo dele diverge muito do plotter ou da bússola, ou o alarme do sensor soa, não confie no piloto. Ponha o piloto em espera e governe pelo timão; compare o rumo do piloto com o da bússola magnética, se houver, lembrando que o rumo sobre o fundo do plotter difere da proa com corrente e vento. Diferença grande: procure o que desvia o sensor, como ímãs, ferramentas de ferro, caixas de som, celulares ou cabos de corrente forte perto dele, e confira a alimentação do piloto (disjuntor armado e tensão do banco que o alimenta, no app). Rumo ainda errado ou alarme persistente: não recalibre por conta própria e chame o técnico, e registre no diário a hora e o rumo mostrado por cada instrumento.',
                a='Em espera, governe pelo timão e compare o rumo com a bússola e o plotter.',
                p=['Ponha o piloto em espera e governe pelo timão.',
                   'Compare o rumo do piloto com o da bússola magnética, se houver; o rumo sobre o fundo do plotter difere da proa com corrente e vento.',
                   'Diferença grande: procure o que desvia o sensor, como ímãs, ferramentas de ferro, caixas de som, celulares ou cabos de corrente forte perto dele.',
                   'Confira a alimentação do piloto: disjuntor armado e tensão do banco que o alimenta, no app.',
                   'Rumo ainda errado ou alarme persistente: não recalibre por conta própria e chame o técnico.',
                   'Registre no diário a hora e o rumo mostrado por cada instrumento.'],
                at='Quem recalibra é o técnico: ajuste errado piora o governo.',
                ver=('PI-11', 'PI-15', 'PI-09')),
    'PI-13': _f('Alarme da bomba ou da direção do piloto', 'O piloto deu alarme de bomba, o que faço?',
                ['direção hidráulica falhou com o piloto ligado', 'timão duro depois do alarme do piloto', 'leme não se move com alarme do piloto'],
                'A bomba do piloto comanda a direção hidráulica; alarme de bomba ou de direção indica que o piloto talvez não consiga mover o leme, então assuma o timão antes de tudo. Assuma o timão, ponha o piloto em espera e gire o timão de leve para os dois lados para ver se o barco responde normalmente; com o timão normal, confira o disjuntor do piloto e a tensão do banco que o alimenta. Com o barco parado ou com outra pessoa no timão, procure vazamento de óleo na bomba e nas mangueiras da direção e olhe o nível do reservatório hidráulico; não complete o óleo da direção sem saber o tipo indicado pelo técnico ou pelo fabricante. Alarme de bomba que volta, ruído estranho ou odor de superaquecimento: mantenha o piloto em espera e chame o técnico, e registre no diário a hora e a mensagem do controle. Timão duro, folgado ou sem resposta: reduza a velocidade e siga o protocolo de bordo.',
                a='Assuma o timão, ponha em espera e confira se o leme responde normalmente.',
                p=['Assuma o timão e ponha o piloto em espera.',
                   'Gire o timão de leve para os dois lados e veja se o barco responde normalmente.',
                   'Com o timão normal, confira o disjuntor do piloto e a tensão do banco que o alimenta.',
                   'Com o barco parado ou com outra pessoa no timão, procure vazamento de óleo na bomba e nas mangueiras da direção e olhe o nível do reservatório hidráulico.',
                   'Alarme de bomba que volta, ruído estranho ou odor de superaquecimento: mantenha o piloto em espera e chame o técnico.',
                   'Registre no diário a hora e a mensagem do controle.'],
                at='Timão duro, folgado ou sem resposta: reduza a velocidade e siga o protocolo de bordo. Não complete o óleo da direção sem saber o tipo indicado pelo técnico ou pelo fabricante.',
                ver=('PI-11', 'PI-12', 'PI-09')),
    'PI-14': _f('O piloto não engata ou desengata sozinho', 'O piloto não engata, o que verifico?',
                ['piloto desliga sozinho', 'controle do piloto apagou', 'piloto não entra em automático'],
                'O piloto recusa engatar ou sai do automático quando falta energia, dado de rumo ou comando da bomba, ou quando há alarme ativo; leia a mensagem do controle antes de tentar de novo. Mantenha o barco em marcha reta, assuma o timão e deixe o piloto em espera; confira a energia (disjuntor do piloto armado e tensão do banco que o alimenta, no app), com outra pessoa no timão se precisar sair do posto, e confira se o controle está ligado, com o visor aceso, lendo a mensagem: ela indica se o motivo é alarme, falta de dado ou falha de equipamento. Trate primeiro o alarme ativo, porque com alarme em curso o piloto pode se recusar a engatar, e tente engatar de novo em automático, com o barco estável e água livre à frente. Se continuar sem engatar ou soltar de novo, siga à mão, registre a mensagem e a hora no diário e chame o técnico; se o piloto soltar de repente, o barco pode guinar, então assuma o timão na hora.',
                a='Confira energia, alarme ativo e a mensagem do controle antes de tentar de novo.',
                p=['Mantenha o barco em marcha reta, assuma o timão e deixe o piloto em espera.',
                   'Confira a energia, com outra pessoa no timão se precisar sair do posto: disjuntor do piloto armado e tensão do banco que o alimenta, no app.',
                   'Confira se o controle está ligado, com o visor aceso, e leia a mensagem: ela indica se o motivo é alarme, falta de dado ou falha de equipamento.',
                   'Trate primeiro o alarme ativo; com alarme em curso o piloto pode se recusar a engatar.',
                   'Tente engatar de novo em automático, com o barco estável e água livre à frente.',
                   'Se continuar sem engatar ou soltar de novo, siga à mão, registre a mensagem e a hora no diário e chame o técnico.'],
                at='Se o piloto soltar de repente, o barco pode guinar: assuma o timão na hora.',
                ver=('PI-06', 'PI-09', 'PI-11')),
    'PI-15': _f('Calibração do piloto automático', 'Quando o piloto precisa de calibração?',
                ['piloto serpenteia em automático', 'calibrar o sensor de rumo', 'testar o piloto depois do serviço'],
                'A calibração ajusta o sensor de rumo e a resposta do leme ao barco; é feita pelo técnico, em água aberta e livre de tráfego, seguindo o manual do fabricante. Chame o técnico se o rumo do piloto não bate com a bússola, se o barco serpenteia em automático, depois de reparo na direção, ou depois de instalar, perto do sensor de rumo, qualquer equipamento com ímã, ferro ou corrente forte; anote no diário os sintomas, a data e o rumo mostrado pelo piloto, pela bússola e pelo plotter. Enquanto espera o técnico, não mexa nos ajustes do piloto: ajuste errado piora o governo. Não recalibre navegando nem na marina: o procedimento pede condições controladas; combine o serviço para um dia de mar calmo e, depois dele, teste em água livre, engatando, mudando o rumo e voltando à espera.',
                a='Chame o técnico; não ajuste nem recalibre por conta própria.',
                p=['Chame o técnico se o rumo do piloto não bate com a bússola, se o barco serpenteia em automático ou depois de reparo na direção.',
                   'Chame também depois de instalar, perto do sensor de rumo, qualquer equipamento com ímã, ferro ou corrente forte.',
                   'Anote no diário os sintomas, a data e o rumo mostrado pelo piloto, pela bússola e pelo plotter.',
                   'Enquanto espera o técnico, não mexa nos ajustes do piloto: ajuste errado piora o governo.',
                   'Combine o serviço para um dia de mar calmo, com água aberta e livre de tráfego.',
                   'Depois do serviço, teste em água livre: engate, mude o rumo e volte à espera.'],
                at='Não recalibre navegando nem na marina: o procedimento pede condições controladas.',
                ver=('PI-12', 'PI-11')),
    # ——— Radar ———
    'RA-01': _f('Ligar o radar e transmitir', 'Como ligo o radar?',
                ['transmitir com o radar', 'ligar o radar pelo plotter', 'radar em espera na marina'], [0], p=[1]),
    'RA-02': _f('Zona de guarda do radar', 'Como defino a zona de guarda do radar?',
                ['alerta de alvo no radar', 'zona de guarda em volta do barco', 'radar avisando alvo próximo'], [0], p=[]),
    'RA-03': _f('Radar com neblina ou à noite', 'Como uso o radar na neblina?',
                ['radar à noite', 'conferir alvos com o AIS', 'reduzir a velocidade na neblina'],
                'Mantenha o radar transmitindo, reduza a velocidade e confira os alvos com o AIS no plotter.',
                p=['Mantenha o radar transmitindo.', 'Reduza a velocidade.', 'Confira os alvos com o AIS no plotter.']),
    'RA-04': _f('Segurança com o domo do radar', 'Posso chegar perto do radar transmitindo?',
                ['domo do radar ligado', 'abrir o domo do radar', 'cuidados com o radar transmitindo'], [0], p=[]),
    'RA-05': _f('Aquecimento do radar: magnetron e estado sólido', 'Quanto tempo leva o aquecimento do radar?',
                ['radar em espera sem transmitir', 'diferença entre magnetron e estado sólido', 'tempo de aquecimento antes de transmitir'],
                'Todo radar marítimo exige um tempo de aquecimento entre ligar e transmitir: o equipamento fica em espera (standby) até '
                'estar pronto, sem emitir sinal. Toque em transmitir (transmit) somente depois do aquecimento terminar. Radar de magnetron '
                'tem aquecimento mais longo que o de estado sólido (semicondutor); o tempo exato depende do fabricante. Na marina ou em '
                'trajetos curtos, mantenha o radar em espera e ligue a transmissão só ao navegar.',
                a='Ligue o radar e espere o aquecimento terminar antes de transmitir.',
                p=['Ligue o radar e aguarde o equipamento entrar no modo de espera (standby).',
                   'Observe o tempo de aquecimento indicado na tela antes de transmitir.',
                   'Selecione transmitir (transmit) somente depois do aquecimento terminar.',
                   'Na marina ou em trajetos curtos, mantenha o radar em espera e ligue a transmissão só ao navegar.'],
                at='Radar de magnetron tem aquecimento mais longo que o de estado sólido (semicondutor); o tempo exato depende do fabricante.',
                ver=('RA-01',)),
    'RA-06': _f('Ajustar o ganho da imagem de radar', 'Como deixo a imagem do radar mais nítida?',
                ['ganho automático e manual do radar', 'ruído de fundo na tela do radar', 'alvo fraco que não aparece no radar'],
                'O ganho (gain) controla a intensidade dos ecos mostrados na tela do radar. Ganho baixo perde alvos fracos; ganho em '
                'excesso cobre a tela de ruído. No modo automático (auto gain) o próprio radar ajusta; no modo manual (manual gain), '
                'aumente o ganho até os alvos conhecidos aparecerem com nitidez e reduza aos poucos até o ruído de fundo (speckle) quase '
                'desaparecer da tela. Repita o ajuste quando o mar, a chuva ou a distância dos alvos mudar.',
                a='No modo manual, aumente o ganho até os alvos aparecerem com nitidez e reduza até o ruído de fundo quase desaparecer.',
                p=['Abra o ajuste de ganho (gain) no painel ou menu de configuração do radar.',
                   'Escolha o modo automático (auto gain), ajustado pelo próprio radar, ou o manual (manual gain), ajustado por você.',
                   'No modo manual, aumente o ganho até os alvos conhecidos aparecerem com nitidez.',
                   'Reduza aos poucos até o ruído de fundo (speckle) quase desaparecer da tela.',
                   'Repita o ajuste quando o mar, a chuva ou a distância dos alvos mudar.'],
                ver=('RA-08', 'RA-09')),
    'RA-07': _f('Ajustar o alcance da imagem de radar', 'Qual alcance devo usar no radar perto da costa?',
                ['anéis de alcance na tela do radar', 'alcance curto e alcance longo', 'escala de distância do radar'],
                'O alcance (range) define até que distância a tela do radar mostra ecos. Alcance curto detalha o entorno próximo; alcance '
                'longo mostra alvos e costa mais distantes, com menos detalhe. Os anéis de alcance (range rings) marcam distâncias fixas a '
                'partir do barco: em área de tráfego, prefira um alcance curto para distinguir alvos próximos entre si; em mar aberto, use '
                'um alcance maior para antecipar tráfego e costa à frente.',
                a='Alcance curto para manobra e tráfego próximo; alcance maior para visão geral em mar aberto.',
                p=['Selecione o alcance adequado à situação: curto para manobra e tráfego próximo, longo para visão geral.',
                   'Leia os anéis de alcance na tela: cada anel marca uma distância fixa a partir do barco.',
                   'Em área de tráfego, prefira um alcance curto para distinguir alvos próximos entre si.',
                   'Em mar aberto, use um alcance maior para antecipar tráfego e costa à frente.'],
                ver=('RA-06',)),
    'RA-08': _f('Reduzir a interferência do mar (sea clutter)', 'Como tirar o ruído de ondas da tela do radar?',
                ['sea clutter perto do barco', 'tela do radar suja perto do barco', 'ruído de mar agitado no radar'],
                'Ondas próximas ao barco geram ecos que poluem o centro da tela do radar. O ajuste de interferência do mar (sea clutter) '
                'reduz esse ruído sem apagar alvos reais. Aumente o ajuste até o ruído das ondas diminuir e pare de aumentar assim que '
                'alvos pequenos e próximos ainda estiverem visíveis. Clutter em excesso também apaga alvos reais próximos ao barco; ajuste '
                'com cautela e confira visualmente. Refaça o ajuste quando o estado do mar mudar.',
                a='Aumente o sea clutter até o ruído das ondas diminuir, sem apagar alvos pequenos e próximos.',
                p=['Abra o ajuste de interferência do mar (sea clutter) no menu de configuração do radar.',
                   'Aumente o ajuste até o ruído das ondas próximas diminuir.',
                   'Pare de aumentar assim que alvos pequenos e próximos ainda estiverem visíveis.',
                   'Refaça o ajuste quando o estado do mar mudar.'],
                at='Clutter em excesso também apaga alvos reais próximos ao barco; ajuste com cautela e confira visualmente.',
                ver=('RA-06', 'RA-09')),
    'RA-09': _f('Reduzir a interferência da chuva (rain clutter)', 'Como reduzir a mancha de chuva na tela do radar?',
                ['rain clutter e FTC do radar', 'mancha de chuva escondendo alvo', 'radar em chuva forte'],
                'Células de chuva aparecem no radar como manchas que podem esconder outros alvos. O ajuste de interferência de chuva '
                '(rain clutter ou FTC) reduz essas manchas na imagem. Aumente o ajuste até a mancha perder intensidade e confira se alvos '
                'sólidos dentro ou perto da área de chuva continuam visíveis. Reduzir demais a interferência de chuva pode esconder um '
                'alvo real dentro da célula de chuva. Volte o ajuste ao normal depois que a chuva passar.',
                a='Aumente o rain clutter (FTC) até a mancha de chuva perder intensidade, sem esconder alvos sólidos.',
                p=['Abra o ajuste de interferência de chuva (rain clutter ou FTC) no menu de configuração do radar.',
                   'Aumente o ajuste até a mancha de chuva na tela perder intensidade.',
                   'Confira se alvos sólidos dentro ou perto da área de chuva continuam visíveis.',
                   'Volte o ajuste ao normal depois que a chuva passar.'],
                at='Reduzir demais a interferência de chuva pode esconder um alvo real dentro da célula de chuva.',
                ver=('RA-06', 'RA-08')),
    'RA-10': _f('Forma e teste da zona de guarda do radar', 'Posso vigiar só um lado do barco com o radar?',
                ['anel ou setor na zona de guarda', 'testar a zona de guarda com um alvo', 'zona de guarda não substitui vigilância'],
                'A zona de guarda é uma área demarcada ao redor do barco no radar, com o formato de anel completo ou de setor voltado '
                'para um lado e alcance mínimo e máximo ajustável. O equipamento soa um alarme quando um eco entra nela — útil para '
                'vigilância em fundeio ou com o piloto automático engatado. Teste a zona com um alvo conhecido antes de confiar nela sem '
                'vigilância visual. A zona de guarda não substitui a vigilância visual e por VHF; é um apoio, não garante detectar todo '
                'tipo de alvo.',
                a='Escolha anel ou setor, ajuste o alcance mínimo e máximo e teste a zona com um alvo conhecido.',
                p=['Defina o formato da área de vigilância: anel completo ao redor do barco ou setor voltado para um lado.',
                   'Ajuste o alcance mínimo e máximo da zona conforme a distância que quer vigiar.',
                   'Ative o alarme da zona e confirme o aviso sonoro ou na tela.',
                   'Teste a zona de guarda com um alvo conhecido antes de confiar nela sem vigilância visual.'],
                at='A zona de guarda não substitui a vigilância visual e por VHF; é um apoio, não garante detectar todo tipo de alvo.',
                ver=('RA-02',)),
    'RA-11': _f('Velocidade e alvos fracos com visibilidade reduzida', 'O radar detecta qualquer tipo de embarcação?',
                ['reduzir a velocidade navegando por radar', 'alvo de madeira no radar', 'vigilância visual além do radar'],
                'Reduza a velocidade com visibilidade reduzida para ter tempo de reagir a um alvo detectado, e ajuste ganho e '
                'interferência (clutter) para a condição do momento, já que chuva e mar mudam a imagem. Acompanhe a tela com atenção '
                'constante. Nem todo alvo reflete bem o sinal do radar (embarcações pequenas ou de madeira); isso não dispensa a '
                'vigilância visual e auditiva possível.',
                a='Reduza a velocidade e ajuste ganho e clutter conforme a condição; mantenha a vigilância visual e auditiva possível.',
                p=['Mantenha o radar transmitindo durante toda a navegação com visibilidade reduzida.',
                   'Reduza a velocidade para ter tempo de reagir a um alvo detectado.',
                   'Ajuste ganho e interferência (clutter) para a condição do momento, já que chuva e mar mudam a imagem.',
                   'Acompanhe a tela com atenção constante, já que alvos pequenos ou de madeira refletem pouco sinal.'],
                at='Nem todo alvo reflete bem o sinal do radar (embarcações pequenas ou de madeira); isso não dispensa a vigilância '
                   'visual e auditiva possível.',
                ver=('RA-03',)),
    'RA-12': _f('Overlay do radar na carta eletrônica', 'O que é overlay de radar?',
                ['sobrepor o radar à carta eletrônica', 'contorno da costa no radar e na carta', 'overlay substitui a carta eletrônica'],
                'O overlay sobrepõe a imagem ao vivo do radar à carta eletrônica no plotter, permitindo comparar o que o radar detecta '
                'com a costa e os pontos da carta. Use a sobreposição para conferir se a posição do barco na carta está coerente com os '
                'ecos reais. O contorno do radar pode não coincidir exatamente com a carta por maré, vegetação ou carta desatualizada; '
                'use como apoio, não como prova única de posição.',
                a='Ative a sobreposição no plotter e compare o contorno do radar com o traçado da carta.',
                p=['Ative a sobreposição (overlay) do radar sobre a carta no plotter.',
                   'Compare o contorno da costa mostrado pelo radar com o traçado da carta eletrônica.',
                   'Use a sobreposição para conferir se a posição do barco na carta está coerente com os ecos reais.'],
                at='O contorno do radar pode não coincidir exatamente com a carta por maré, vegetação ou carta desatualizada; use como '
                   'apoio, não como prova única de posição.'),
    'RA-13': _f('Segurança com a antena do radar transmitindo', 'Por que preciso desligar o radar antes de fazer serviço perto da antena?',
                ['radiofrequência da antena do radar', 'desligar o radar antes de limpar a antena', 'domo do radar e exposição à radiação'],
                'A antena do radar emite energia de radiofrequência enquanto transmite. Ficar muito próximo da área irradiada ou abrir a '
                'estrutura com o radar ligado expõe a pessoa a essa energia. Antes de qualquer serviço perto da antena ou domo, coloque o '
                'radar em espera (standby) ou desligue-o, e avise outras pessoas a bordo antes de ligar a transmissão se alguém estiver '
                'perto. A distância mínima de segurança é definida pelo fabricante do equipamento; siga a etiqueta ou o manual do radar '
                'instalado. Nunca abra o domo ou a estrutura da antena com o radar transmitindo.',
                a='Antes de qualquer serviço perto da antena, coloque o radar em espera ou desligue-o.',
                p=['Antes de qualquer serviço perto da antena ou domo, coloque o radar em espera (standby) ou desligue-o.',
                   'Não permaneça parado bem próximo e à frente da antena enquanto o radar estiver transmitindo.',
                   'Não abra a estrutura (domo ou array) do radar com o equipamento ligado.',
                   'Avise outras pessoas a bordo antes de ligar a transmissão se alguém estiver perto da antena.'],
                at='A distância mínima de segurança é definida pelo fabricante do equipamento; siga a etiqueta ou o manual do radar '
                   'instalado. Nunca abra o domo ou a estrutura da antena com o radar transmitindo.',
                ver=('RA-04',)),
    # ——— AIS ———
    'AI-01': _f('Alvos do AIS no plotter', 'Como vejo os outros barcos pelo AIS?',
                ['alvos do AIS', 'distância de passagem prevista', 'nome, rumo e velocidade dos alvos'], [0], p=[1]),
    'AI-02': _f('Identificação do AIS', 'Que identificação o AIS transmite?',
                ['MMSI do AIS', 'transponder classe B', 'identificação do barco no AIS'], [0], p=[]),
    'AI-03': _f('AIS em modo silencioso', 'O que faz o modo silencioso do AIS?',
                ['transponder só recebendo', 'AIS sem transmitir a posição', 'voltar a transmitir o AIS'], [0, 1], p=[], at=1),
    'AI-04': _f('O que o AIS faz e não faz', 'O que o AIS faz?',
                ['Qual a diferença entre AIS classe A e classe B?', 'Os outros barcos me veem pelo AIS?', 'O AIS substitui o radar?'],
                'O AIS classe B transmite a posição, o rumo e a velocidade deste barco para quem estiver por perto e recebe os mesmos dados de quem tiver AIS, que aparecem no plotter como alvos. Funciona por rádio VHF, em linha de visada: o alcance é limitado pelo horizonte. O classe B transmite com menos potência e, em geral, com menos prioridade do que o classe A dos navios, com alcance menor. Só aparece quem estiver com o AIS ligado: embarcações pequenas e barcos de pesca costumam não aparecer. O AIS complementa a vigia e o radar; não substitui nenhum dos dois.',
                p=[], ver=('AI-01', 'AI-02')),
    'AI-05': _f('Leitura dos alvos do AIS (CPA e TCPA)', 'Como leio os dados de um alvo do AIS no plotter?',
                ['O que significa CPA no plotter?', 'Como sei se vou cruzar com aquele barco?', 'O que o plotter mostra quando toco num alvo do AIS?'],
                'Cada alvo do AIS é um barco com o aparelho ligado; o símbolo mostra a posição e o rumo dele. Ao tocar no alvo, o plotter abre os dados: nome, rumo, velocidade e a menor distância de passagem prevista (CPA), com o tempo até ela (TCPA). Compare o rumo e a velocidade do alvo com os seus para ver se os trajetos se cruzam: CPA pequeno e TCPA curto pedem atenção. Confirme com a vista e o radar e aja cedo, reduzindo ou mudando o rumo pelas regras de navegação. Depois de mudar de rumo, reveja o alvo: a previsão se atualiza com o movimento dos dois barcos.',
                a='Toque no alvo: nome, rumo, velocidade, CPA e TCPA.',
                p=['Toque no alvo para abrir os dados: nome, rumo, velocidade, CPA e TCPA.',
                   'Compare o rumo e a velocidade do alvo com os seus para ver se os trajetos se cruzam.',
                   'CPA pequeno e TCPA curto: confirme com a vista e o radar e aja cedo, reduzindo ou mudando o rumo.',
                   'Depois de mudar de rumo, reveja o alvo: a previsão se atualiza.'],
                at='Os dados vêm do rádio do outro barco e podem estar atrasados ou errados: confirme com a vista.',
                ver=('AI-01', 'RA-03')),
    'AI-06': _f('Quando usar o modo silencioso do AIS', 'Quando posso usar o AIS em silencioso?',
                ['Como volto a transmitir no AIS?', 'Com o AIS em silencioso, ainda vejo os outros barcos?', 'Preciso registrar quando uso o modo silencioso?'],
                'Use o modo silencioso só com o barco parado, em local sem tráfego e com motivo claro, como privacidade na marina. Ative e desative pelo comando instalado pelo técnico — confirme com ele onde fica — e registre no diário a hora em que ativou. Antes de largar, volte ao normal e confirme pelo indicador do aparelho que ele voltou a transmitir. Navegando, em neblina, à noite ou em canal de tráfego, mantenha o AIS transmitindo.',
                a='Use só com o barco parado; volte a transmitir antes de largar.',
                p=['Ative e desative pelo comando de modo silencioso que o técnico instalou; confirme com ele onde fica.',
                   'Registre no diário a hora em que ativou o modo silencioso.',
                   'Antes de largar, volte ao modo normal e confirme pelo indicador que o aparelho voltou a transmitir.'],
                at='Em silencioso, o seu barco some do AIS dos outros barcos, que não recebem o alerta de aproximação.',
                ver=('AI-03',)),
    'AI-07': _f('Sem alvos do AIS no plotter', 'Por que não aparecem barcos no AIS do plotter?',
                ['O AIS não recebe nada, o que verifico?', 'Como sei se o AIS está funcionando?', 'O modo silencioso impede de ver os alvos?'],
                'Sem alvos pode ser só falta de tráfego com AIS por perto, ou falha de alimentação, antena, ligação com o plotter ou ajuste da carta: confira em ordem, do mais simples ao mais difícil. Em enseadas e fora de rotas de navios pode haver poucos barcos com AIS ao alcance. Confira se o AIS está ligado, com o disjuntor armado e o indicador de funcionamento aceso, e se a camada e a fonte de AIS estão habilitadas nos ajustes do plotter. Sem posição de GPS no plotter, os alvos e os alarmes de aproximação podem não funcionar. Confira também a antena e o cabo do AIS: conectores firmes e sem corrosão. Há barcos à vista e continua sem alvo: registre no diário e chame o técnico de bordo.',
                a='Confira do mais simples ao mais difícil: tráfego por perto, depois alimentação, antena e ajustes do plotter.',
                p=['Em enseadas e fora de rotas de navios, pode haver poucos barcos com AIS ao alcance — não é falha.',
                   'Confira se o AIS está ligado, com o disjuntor armado e o indicador de funcionamento aceso.',
                   'No plotter, confira a camada de AIS ligada e a fonte de AIS habilitada nos ajustes.',
                   'Confira se o plotter tem posição de GPS: sem ela, os alvos e os alarmes de aproximação podem não funcionar.',
                   'Confira a antena e o cabo do AIS: conectores firmes e sem corrosão.'],
                at='O modo silencioso só para de transmitir: a recepção continua, então ele não explica a falta de alvos.',
                ver=('AI-06',)),
    'AI-08': _f('Alvo do AIS sem nome, aos saltos ou que some', 'Por que o alvo do AIS aparece sem nome?',
                ['Por que o alvo do AIS some e volta?', 'O alvo do AIS está parado, será que travou?', 'O que é alvo perdido no AIS?'],
                'O nome e o tamanho do barco chegam com menos frequência do que a posição, e o alvo de classe B atualiza mais devagar do que o de classe A: por isso um alvo pode chegar só com um número, andar aos saltos ou sumir e voltar por um tempo. Alvo só com número: espere alguns minutos, porque o nome costuma chegar depois da posição. Alvo que some e volta costuma ser sinal no limite do alcance ou o barco passando atrás de terra ou de construções; se ficar parado sem se atualizar, trate a posição como antiga e confirme com a vista e o radar. Nenhum alvo ganha nome mesmo depois de muito tempo: registre no diário e chame o técnico de bordo.',
                p=['Alvo só com número: espere alguns minutos — o nome costuma chegar depois da posição.',
                   'Alvo que anda aos saltos: é normal num alvo de classe B, que atualiza menos vezes do que os navios de classe A.',
                   'Alvo que some e volta: sinal no limite do alcance, ou o barco passando atrás de terra ou de construções.',
                   'Alvo parado que não se atualiza: trate a posição como antiga e confirme com a vista e o radar.'],
                at='O nome é digitado por cada barco e pode estar errado ou em branco.',
                ver=('AI-07',)),
    # ——— Sistema fixo de incêndio (só o procedimento padrão; a resposta termina com o rótulo e a nota da etiqueta) ———
    'SF-01': _f('Fogo a bordo: sistema fixo de incêndio', 'O que faço em caso de fogo no motor?',
                ['alarme do sistema fixo de incêndio', 'fogo no motor', 'quando usar o extintor portátil'],
                'Fogo no motor ou alarme do sistema fixo: desligue motores e gerador, corte a ventilação do motor e, se o sistema não disparou '
                'sozinho e há fogo no motor, use o disparo manual. Não abra o acesso ao motor depois da descarga: espere o tempo indicado na '
                'etiqueta do sistema e o motor esfriar. Fogo pequeno fora do motor: extintor portátil na base das chamas, de costas para a saída. '
                'Fogo que não apaga: MAYDAY no canal 16 e prepare o abandono.',
                a='Desligue motores e gerador e corte a ventilação do motor.', ver=('EM-05', 'SF-02', 'SF-03')),
    'SF-02': _f('Disparo manual do sistema fixo', 'Como uso o disparo manual do sistema fixo?',
                ['sistema fixo não disparou sozinho', 'acionar o disparo manual de incêndio', 'disparo manual com o motor desligado'],
                [0], a='Só se o sistema não acionou sozinho e há fogo no motor: motores e gerador desligados, ventilação cortada e disparo manual.',
                p=['Desligue motores e gerador.', 'Corte a ventilação do motor.', 'Se o sistema não acionou sozinho e há fogo no motor, use o disparo manual.'],
                ver=('SF-01', 'SF-03')),
    'SF-03': _f('Depois do disparo do sistema fixo', 'O sistema fixo disparou, o que faço depois?',
                ['sistema fixo descarregou', 'quando abrir o acesso ao motor depois do disparo', 'recarga do sistema fixo'],
                'Depois do disparo, confirme motores, gerador e ventilação desligados e não abra o acesso ao motor; espere o tempo indicado na '
                'etiqueta do sistema e só então libere o acesso, com o extintor portátil à mão. Se o fogo voltar, MAYDAY no canal 16.',
                a='Não abra o acesso ao motor: espere o tempo da etiqueta do sistema.',
                p=['Confirme motores, gerador e ventilação desligados.', 'Não abra o acesso ao motor.',
                   'Espere o tempo indicado na etiqueta do sistema e só então libere o acesso, com o extintor portátil à mão.',
                   'Se o fogo voltar, MAYDAY no canal 16.', 1], ver=('SF-01', 'EM-05')),
    'SF-04': _f('Inspeção anual do sistema fixo', 'Quando inspeciono o sistema fixo de incêndio?',
                ['inspeção do sistema e da carga', 'revisão anual do sistema fixo', 'técnico de bordo e o sistema fixo'], [0], p=[]),
    # ——— EPIRB ———
    'EP-01': _f('Acionar o EPIRB', 'Como aciono o EPIRB?',
                ['disparar a radiobaliza', 'EPIRB: antena para cima e céu aberto', 'levar o EPIRB para a balsa'],
                'Só em perigo grave e iminente, depois do MAYDAY (ou sem rádio). Acione conforme a etiqueta do equipamento, com a antena para '
                'cima e céu aberto. Leve o EPIRB para a balsa ou mantenha-o flutuando preso por um cabo. Não desligue até o resgate.',
                a='Só em perigo grave e iminente, depois do MAYDAY (ou sem rádio).', ver=('EM-08', 'EP-03')),
    'EP-02': _f('Teste da baliza (EPIRB)', 'Como testo o EPIRB?',
                ['autoteste da radiobaliza', 'o teste do EPIRB envia alerta', 'bateria e disparador hidrostático'],
                'Faça o autoteste conforme a etiqueta; o teste não envia alerta.',
                p=['Faça o autoteste conforme a etiqueta.', 2], ver=('EP-04',)),
    'EP-03': _f('EPIRB disparado por engano', 'Disparei o EPIRB sem querer, o que faço?',
                ['baliza disparou por engano', 'desligar o EPIRB disparado', 'avisar no canal 16 depois do disparo'],
                'Desligue o EPIRB e avise no canal 16.', p=['Desligue o EPIRB.', 'Avise no canal 16.'], ver=('EP-01', 'EM-08')),
    'EP-04': _f('Validade do EPIRB', 'Onde vejo a validade do EPIRB?',
                ['validade da bateria da radiobaliza', 'disparador hidrostático', 'certificado do EPIRB'],
                'A validade da bateria e do disparador hidrostático está na etiqueta do equipamento e no certificado em Documentos.',
                p=[], ver=('EP-02',)),
    # ——— Checklists (o texto é o da seção do checklist; os itens sem seção nos guias entram como boa prática) ———
    'CK-01': _f('Checklist de saída: gerador, estabilizador e climatização', 'O que confiro antes de sair: gerador, estabilizador e climatização?',
                ['checklist de saída, itens 1 a 3', 'água no escapamento do gerador na saída', 'filtro de água salgada antes de ligar a climatização'],
                'Antes de sair: água no escapamento depois de ligar o gerador, estabilizador ligado com antecedência e filtro de água salgada '
                'limpo antes de ligar a climatização.',
                ver=('GE-03', 'SK-02', 'CL-01')),
    'CK-02': _f('Checklist de saída: eletrônicos, porão e diesel', 'O que confiro antes de sair: eletrônicos, porão e diesel?',
                ['checklist de saída, itens 4 a 6', 'plotter, piloto e VHF antes de sair', 'bombas de porão e diesel antes de largar'],
                'Antes de sair: plotter ligado, piloto em espera até sair da marina, VHF no canal 16, bombas de porão testadas no manual e '
                'diesel acima do aviso.',
                ver=('EL-04', 'PO-03', 'CK-05')),
    'CK-03': _f('Checklist de saída: coletes, previsão e salvatagem', 'O que confiro antes de largar: coletes, balsa e previsão do dia?',
                ['coletes, balsa e extintores antes de sair', 'previsão do dia antes de largar', 'boletim da Marinha antes de sair'],
                'Antes de largar: um colete por pessoa (conte as pessoas a bordo agora), balsa, boia e extintores conforme a placa de '
                'salvatagem, e a previsão do dia consultada.',
                ob=('ck', 's02', 's11', 's12', 's14'), ver=('EM-09', 'EM-07')),
    'CK-04': _f('Checklist de chegada', 'O que faço ao chegar na marina?',
                ['fechar a saída no diário', 'desligar estabilizador, gerador e climatização ao atracar', 'checklist ao atracar'],
                'Ao chegar: piloto em espera antes de manobrar, estabilizador desligado com o banco de 12 V ligado até o volante parar, gerador '
                'sem cargas e desligado, climatização desligada e a saída fechada no diário.',
                ob=('ck', 'c07'), ver=('SK-04', 'GE-04', 'CL-05', 'MO-06')),
    'CK-05': _f('Checklist de abastecimento', 'Quando devo abastecer e o que registro?',
                ['regra do diesel', 'reserva técnica de diesel', 'abastecer antes de 25 %'],
                [0, 1], p=[1], at=('ck', 'a04'), se=2, ob=('ck', 'a01', 'a02', 'a03', 'a05'), ver=('MO-10', 'CK-06')),
    'CK-06': _f('Checklist de tanques', 'Quando completo a água e esvazio as servidas?',
                ['água doce abaixo do aviso', 'tanques de águas cinzas e negras', 'servidas acima do aviso'], [0, 1], p=[2, 3], se=[2, 3], ver=('CK-01',)),
    'CK-07': _f('Checklist de fundeio', 'O que confiro ao fundear?',
                ['checklist ao fundear', 'alarme de âncora e diário no fundeio', 'fundo de areia ou lama'],
                'Ao fundear: fundo de areia ou lama, com espaço de giro; lance com o barco parado, dê ré devagar até a âncora unhar, ative o '
                'alarme de âncora no plotter e registre a hora e a profundidade no diário.',
                ob=('ck', 'f04', 'f06'), ver=('AN-01', 'EL-03')),
}

# Glossário (F10): termo, texto e a fonte (onde o app usa o termo). Os da telemetria citam o formato do quadro do coletor (pasta 05); os de
# segurança levam o rótulo do procedimento padrão, e o MMSI o texto MMSI_RADIO (nunca o número).
FAQ_TELE = ARQ['formato'] + ' · ' + DRIVE + ' › ' + PASTAS['tele']
FAQ_GLOSSARIO = (
    ('SOG', 'Velocidade sobre o fundo (Speed Over Ground): a velocidade do barco em relação ao fundo, medida pelo GPS.', FAQ_TELE),
    ('STW', 'Velocidade na água (Speed Through Water): a velocidade do barco em relação à água.', FAQ_TELE),
    ('COG', 'Rumo sobre o fundo (Course Over Ground): o rumo que o barco faz em relação ao fundo, medido pelo GPS.', FAQ_TELE),
    ('HDG', 'Proa (Heading): para onde aponta a proa do barco, em graus.', FAQ_TELE),
    ('TWS', 'Velocidade do vento verdadeiro (True Wind Speed): o vento sobre a água, sem o movimento do barco.', FAQ_TELE),
    ('TWA', 'Ângulo do vento verdadeiro (True Wind Angle): de onde vem o vento verdadeiro em relação à proa, positivo a boreste. O quadro do coletor traz o '
            'vento verdadeiro como direção em relação ao norte verdadeiro (TWD); o TWA é essa direção menos a proa.', FAQ_TELE),
    ('AWA', 'Ângulo do vento aparente (Apparent Wind Angle): de onde vem o vento sentido a bordo, em relação à proa; positivo a boreste.', FAQ_TELE),
    ('DPT', 'Profundidade (Depth): a profundidade sob o barco, medida pela sonda.', FAQ_TELE),
    ('ETA', 'Chegada prevista (Estimated Time of Arrival): a hora local em que o barco deve chegar ao destino.', FAQ_TELE),
    ('MOB', 'Homem ao mar (Man Overboard): a marca que o plotter grava para quem caiu na água. ' + FIM_ROTULO,
     fonte_da_secao('g_eletronicos', '1 · Plotter: homem ao mar')),
    ('DSC', 'Chamada seletiva digital (Digital Selective Calling): o alerta do rádio VHF, enviado pelo botão DISTRESS. Depois do alerta, faça '
            'o MAYDAY por voz no canal 16. ' + FIM_ROTULO, fonte_da_secao('protocolo', 'DSC')),
    ('MMSI', MMSI_RADIO + ': a identificação do rádio no alerta DSC e no AIS.', fonte_da_secao('protocolo', 'DSC')),
    ('EPIRB', 'Radiobaliza de emergência (Emergency Position-Indicating Radio Beacon): só em perigo grave e iminente, depois do MAYDAY (ou sem '
              'rádio). ' + FIM_SEGURANCA, fonte_da_secao('g_epirb', '1 · Acionar')),
    ('BB/BE', 'Bombordo (BB) e boreste (BE): o lado esquerdo e o lado direito do barco, de quem olha para a proa.',
     fonte_da_secao('g_motores', '8 · Horímetros')),
)


def frases(txt):
    """As frases de uma seção de guia (o passo a passo do FAQ). No checklist ("1. Gerador: … 2. Estabilizador: …") cada item é uma frase,
    sem o número; o número só separa depois de um ponto ou de um parêntese ("canal 16. 5. Bombas" não parte em "canal" e "16.")."""
    if re.match(r'\d+\. ', txt):
        return [re.sub(r'^\d+\.\s+', '', p) for p in re.split(r'(?<=[.)])\s+(?=\d+\.\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ])', txt)]
    return re.split(r'(?<=[.!?])\s+(?=[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ])', txt)


def _sem_fim(txt):
    """(texto sem o rótulo do fim, o rótulo): o fim de segurança (rótulo e nota da etiqueta), o do rótulo só, ou nenhum (§1.5)."""
    for fim in (FIM_SEGURANCA, FIM_ROTULO):
        if txt.endswith(' ' + fim):
            return txt[:-len(fim) - 1], fim
    return txt, ''


def _faq_texto(x, fr, ck):
    """Campo do FAQ: o texto, a frase de índice N da seção, ('ck', ids…) = os itens do checklist como ordem (FAQ_CK_ORDEM), ou uma lista deles (juntos por espaço)."""
    if x is None:
        return None
    if isinstance(x, int):
        return fr[x]
    if isinstance(x, str):
        return x
    if x and x[0] == 'ck':
        return ' '.join(FAQ_CK_ORDEM[ck[i]['id']] for i in x[1:])
    return ' '.join(_faq_texto(i, fr, ck) for i in x)


def _indices(x):
    """Os índices de frase que um campo usa (r, at, se): o que sobra vira passo a passo quando p é None."""
    if isinstance(x, int):
        return {x}
    if isinstance(x, (list, tuple)) and not (x and x[0] == 'ck'):
        return {i for i in x if isinstance(i, int)}
    return set()


def faq_equipamentos(B=None):
    """CONTRATO §1.6: {versao, total, secoes, itens, glossario}. A versao são os 8 primeiros hex do sha256 do conteúdo (como a da base):
    muda quando o texto muda, nunca com a data. Os itens saem na ordem das seções do FAQ (EM primeiro); a base entra só para herdar o
    `seguranca` do trecho de origem."""
    B = base_conhecimento() if B is None else B
    trecho = {(t['fonte'], t['secao']): t for t in B['trechos']}
    ck = {x['id']: x for lista in checklists_dados()['itens'].values() for x in lista}
    por_id = {}
    for iid, sec in FAQ_EM:
        spec = FAQ_TEXTOS[iid]
        t = trecho.get((ARQ['protocolo'], sec), {})   # trecho que falta na base: a asserção FAQ acusa (o gerador não cai)
        _, fim = _sem_fim(t.get('texto', ''))
        por_id[iid] = (spec, [], t, fim, [('Protocolo', fonte_da_secao('protocolo', sec))], FAQ_EQUIP_EM[iid], True)
    for prefixo, chave in FAQ_GUIAS:
        g = GUIAS[chave]
        for n, (sec, txt) in enumerate(g['secoes'], 1):
            iid = '%s-%02d' % (prefixo, n)
            corpo, fim = _sem_fim(txt)
            spec = FAQ_TEXTOS[iid]
            fontes = [('Guia de bordo', fonte_da_secao(chave, sec))]
            if iid in FAQ_PROTOCOLO:
                fontes.append(('Protocolo', fonte_da_secao('protocolo', FAQ_PROTOCOLO[iid])))
            usa_ck = [i for k in ('r', 'at', 'se', 'ob') for i in (spec[k][1:] if isinstance(spec[k], tuple) and spec[k][:1] == ('ck',) else ())]
            for i in usa_ck:
                if ck[i]['fonte'] != BOA_PRATICA:
                    raise SystemExit('gerador: %s cita o item %s do checklist, que tem seção nos guias (só os de «boa prática» entram assim)' % (iid, i))
            if usa_ck:
                fontes.append(('Boa prática', FAQ_BOA_PRATICA))
            por_id[iid] = (spec, frases(corpo), trecho.get((g['titulo'], sec), {}), fim, fontes, spec['eq'] or g['equip'], False)
    itens, secoes = [], []
    for k, (titulo, prefixos) in enumerate(FAQ_SECOES, 1):
        ids = [i for p in prefixos for i in por_id if i.startswith(p + '-')]
        secoes.append({'n': k, 'titulo': titulo, 'ids': ids})
        for iid in ids:
            spec, fr, t, fim, fontes, equip, em = por_id[iid]
            r = _faq_texto(spec['r'], fr, ck)
            usados = _indices(spec['r']) | _indices(spec['at']) | _indices(spec['se'])
            if spec['p'] is None:
                p = [fr[i] for i in range(len(fr)) if i not in usados]
            else:
                p = [_faq_texto(x, fr, ck) for x in spec['p']]
            it = {'id': iid, 'titulo': spec['t'], 'pergunta': spec['q'], 'variantes': spec['v'], 'resposta': r + (' ' + fim if fim else '')}
            if p:
                it['passos'] = p
            for chave_it, campo in (('acao', 'a'), ('atencao', 'at'), ('senao', 'se'), ('obs', 'ob')):
                v = _faq_texto(spec[campo], fr, ck)
                if v:
                    it[chave_it] = v
            it.update({'fontes': [{'tipo': tp, 'texto': tx} for tp, tx in fontes], 'secao': k, 'equip': equip, 'emerg': em})
            ver = list(spec['ver'])
            if t.get('seguranca') or segura(' '.join(x for _, x in textos(dict(it, ver=ver)))):   # a leitura da SEGURANCA_MARCADA: todo texto do item, ids e fontes inclusive
                it['seguranca'] = True
            if ver:
                it['ver'] = ver
            itens.append(it)
    corpo = {'total': len(itens), 'secoes': secoes, 'itens': itens,
             'glossario': [{'termo': a, 'texto': b, 'fonte': c} for a, b, c in FAQ_GLOSSARIO]}
    return dict({'versao': hashlib.sha256(serializa(corpo).encode('utf-8')).hexdigest()[:8]}, **corpo)


def gera_faq(Q=None):
    return serializa(faq_equipamentos() if Q is None else Q) + '\n'


# D.protocolos (CONTRATO §1.3, C6): a fonte única do SOS (S1/S2), do roteiro, dos cartões EM e da página EMERGÊNCIA do Guia. Montado só
# com as constantes TXT_* acima, as mesmas dos guias g_seafire, g_epirb e protocolo (um texto, uma fonte). Sem nada do dado gerado da
# embarcação além do nome (o roteiro lê EMBARCACAO['nome']): nada de registro, MMSI, base, fabricante ou modelo (PROTOCOLO_LIMPO).
# EPIRB e Seafire: só o procedimento padrão e a NOTA_ETIQUETA; fabricante, modelo e validade ficam em Equipamentos, Leme e Documentos.
# Os leitores (S1/S2, F3, cérebro) mudam na 1b; até lá a S1/S2 ainda lê rotulo, fonte, roteiro e mob.
PROTOCOLOS = {
    'rotulo': ROTULO,
    'fonte': ARQ['protocolo'] + ' · ' + DRIVE + ' › ' + PASTAS['protocolos'],
    'mmsiRadio': MMSI_RADIO,
    'mmsiRotulo': MMSI_ROTULO,
    'indicativo': TXT_INDICATIVO,
    'plotter': TXT_PLOTTER,
    'hud': TXT_HUD,
    'canal16': {'canal': '16', 'mhz': '156,800', 'fonte': ARQ['protocolo'] + ' · MAYDAY · canal 16'},
    'roteiro': list(TXT_ROTEIRO),
    'mob': list(TXT_MOB),
    'seafire': {'passos': list(TXT_SEAFIRE), 'nota': NOTA_ETIQUETA},
    'epirb': {'passos': list(TXT_EPIRB), 'teste': list(TXT_EPIRB_TESTE), 'nota': NOTA_ETIQUETA},
    'alagamento': list(TXT_ALAGAMENTO),
    'abandono': list(TXT_ABANDONO),
    'oleo': list(TXT_OLEO),
    'salvatagem': TXT_SALVATAGEM,
    'panpan': TXT_PANPAN,
    'dsc': TXT_DSC,
}


# ——————————————————————————————— ROTA, CAMPOS E REPLAY (CONTRATO §1.14–§1.16, §1.22, §2.6, §3) ———————————————————————————————
# Só na simulação (SIMULACAO = True): com False o gerador não emite rota, histórico simulado nem dia de bordo e o replay sai só com
# limites e alertas (§4.3). O laço de 150 s, a rota e os contadores são função pura do segundo do dia de bordo (confere.em(), o port do
# CapitaoReplay.em() da Fase 2); os números abaixo (chaves, ruído, fixos, bases dos contadores) são o que o contrato fixa.
CENARIO = 'aviso'          # decisão (c): o crítico fica desligado; 'alarme-critico' só mudando esta constante (§3.5)
ANCORA_HORA = '07:00'      # a âncora do dia de bordo, no fuso da embarcação
CIRCUITOS_DIA = 19         # primo com as 576 voltas do dia (§1.14): nenhuma chegada cai numa emenda de 150 s
VOLTAS_DIA = 576           # 86.400 s / 150 s
DIAS_DE_BORDO = 3          # abastecimentos do dia de bordo na lista (§1.10)

# Rota (§2.6): pontos de mar aberto da Interpraias, SÓ para a navegação simulada (nunca no SOS). Portão manual do C8: cada ponto e cada
# perna foram conferidos contra a costa de resolução cheia (GSHHG, com as ilhas pequenas) e contra a máscara global de ~1 km, com folga
# mínima de 0,40 mn de terra (a base, na barra do rio, é a única que toca terra). O contrato partia de pontos que cortavam a Ponta das
# Laranjeiras (a perna base → Ilha das Cabras e as duas de volta da Ilha das Cabras passavam por terra): a saída da barra é para o norte,
# por fora da ponta. Revisão do C8: os dois pontos «Ilha das Cabras» tinham ido tão ao largo (1,6 mn do polígono da ilha na costa cheia;
# a ilha fica a ~0,25 km da Praia Central) que o nome mentia; agora ficam a 0,9–1,0 mn dela, a leste, e a Ponta das Laranjeiras (ida e volta) sobe
# para o norte para as pernas passarem a ≥ 0,50 mn da costa de Laranjeiras. Circuito 16,17 mn, fator 0,9866 (19 circuitos, ≤ 1).
# (id, nome, rel, perto, lat, lon, prof_m).
PONTOS_ROTA = [
    ('base', 'Barra Sul (saída do Rio Camboriú)', 'da Barra Sul', 'na saída da Barra Sul', -26.9985, -48.6160, 8),
    ('cabras', 'Ilha das Cabras', 'da Ilha das Cabras', 'ao largo da Ilha das Cabras', -26.9838, -48.6100, 12),
    ('laranjeiras', 'Ponta das Laranjeiras', 'da Ponta das Laranjeiras', 'ao largo da Ponta das Laranjeiras', -26.9820, -48.5680, 16),
    ('taquaras', 'Taquaras', 'de Taquaras', 'ao largo de Taquaras', -27.0320, -48.5540, 19),
    ('estaleirinho', 'Estaleirinho', 'do Estaleirinho', 'ao largo do Estaleirinho', -27.0620, -48.5530, 21),
    ('pinho', 'Praia do Pinho', 'da Praia do Pinho', 'ao largo da Praia do Pinho', -27.0450, -48.5430, 22),
    ('laranjeiras_v', 'Laranjeiras', 'de Laranjeiras', 'ao largo de Laranjeiras', -26.9810, -48.5740, 18),
    ('cabras_v', 'Ilha das Cabras', 'da Ilha das Cabras', 'ao largo da Ilha das Cabras', -26.9850, -48.6084, 13),
]
ROTA_DESTINO = {'id': 'estaleirinho', 'nome': 'Estaleirinho', 'caminho': 'a caminho do Estaleirinho'}
ROTA_VOLTA = {'nome': 'Barra Sul (base)', 'caminho': 'a caminho da Barra Sul'}
CORRENTE = {'nos': 0.3, 'para_graus': 200}   # STW e proa (§1.22)


# Quadros-chave do laço (§3.1), de 5 em 5 s, t = 0…145 (o segmento 145 → 150 usa o t = 0). Os valores intermediários saem da
# interpolação e do ruído por hash (§3.2). A ordem das chaves é a da semente do ruído (1100 + posição, fixa).
ORDEM_LACO = ['motor_bb_rpm', 'motor_be_rpm', 'sog_nos', 'consumo_lph', 'motor_bb_oleo_bar', 'motor_be_oleo_bar', 'motor_bb_arref_c',
              'motor_be_arref_c', 'motor_bb_carga_pct', 'motor_be_carga_pct', 'gerador_kw', 'bateria_0_tensao_v', 'bateria_1_tensao_v',
              'bateria_2_tensao_v', 'ondas_m', 'vento_verdadeiro_nos', 'vento_verdadeiro_angulo', 'pressao_barometrica_hpa',
              'temp_ar_externo_c', 'temp_agua_c', 'porao_bb_nivel', 'porao_be_nivel', 'seakeeper_volante_rpm', 'seakeeper_volante_pct',
              'jogo_graus', 'caimento_graus', 'temp_praca_maquinas_c', 'leme_graus']
# Amplitude do ruído por campo (§3.2); a semente de cada um é 1100 + a posição em ORDEM_LACO.
AMPLITUDE_RUIDO = {'motor_bb_rpm': 6, 'motor_be_rpm': 6, 'sog_nos': 0.1, 'consumo_lph': 0, 'motor_bb_oleo_bar': 0.03, 'motor_be_oleo_bar': 0.03,
                   'motor_bb_arref_c': 0.1, 'motor_be_arref_c': 0.1, 'motor_bb_carga_pct': 0.6, 'motor_be_carga_pct': 0.6, 'gerador_kw': 0.1,
                   'bateria_0_tensao_v': 0.02, 'bateria_1_tensao_v': 0.02, 'bateria_2_tensao_v': 0.01, 'ondas_m': 0.05,
                   'vento_verdadeiro_nos': 0.4, 'vento_verdadeiro_angulo': 2, 'pressao_barometrica_hpa': 0.05, 'temp_ar_externo_c': 0,
                   'temp_agua_c': 0, 'porao_bb_nivel': 0.1, 'porao_be_nivel': 0.1, 'seakeeper_volante_rpm': 12, 'seakeeper_volante_pct': 0,
                   'jogo_graus': 0.3, 'caimento_graus': 0.1, 'temp_praca_maquinas_c': 0.2, 'leme_graus': 0.4}
SEMENTE_PROA, SEMENTE_PROF = 1201, 1202   # ruído da rota (proa e profundidade): usa o segundo absoluto, porque a rota não é periódica em 150 s
VOLANTE_RPM = 8420    # abaixo da rotação nominal do Seakeeper 3 (8.450 rpm na folha pública do fabricante); com o ruído de 12 rpm: 8.408 a 8.432


def _kf(pares):
    d = dict(pares)
    assert sorted(d) == list(range(0, 150, 5)), sorted(set(range(0, 150, 5)) - set(d))
    return [d[t] for t in range(0, 150, 5)]


def _sem_menos_zero(v):
    return v + 0.0 if isinstance(v, float) else v   # −0,0 + 0,0 = 0,0: nunca −0 no dado


def chaves_laco():
    T = list(range(0, 150, 5))
    lenta, cruz = 700, 2050
    rpm = _kf([(0, lenta), (5, lenta), (10, lenta + 5), (15, lenta), (20, lenta + 10), (25, 1100), (30, 1400), (35, 1650), (40, 1850), (45, 1980)]
              + [(t, cruz) for t in range(50, 121, 5)] + [(125, 1450), (130, 950), (135, lenta + 10), (140, lenta + 5), (145, lenta)])
    K = {'motor_bb_rpm': rpm, 'motor_be_rpm': [r - (10 if r > 1000 else 5) for r in rpm]}
    sog = {700: 5.0, 705: 5.0, 710: 5.1, 1100: 7.6, 1400: 10.0, 1650: 12.6, 1850: 15.0, 1980: 16.9, 2050: 18.0, 1450: 10.4, 950: 6.6}
    lph = {700: 6.2, 705: 6.3, 710: 6.4, 1100: 14.0, 1400: 24.0, 1650: 36.0, 1850: 48.0, 1980: 60.0, 2050: 68.0, 1450: 26.0, 950: 10.5}
    K['sog_nos'] = [sog[r] for r in rpm]
    K['consumo_lph'] = [lph[r] for r in rpm]

    def oleo(r, b):
        return b if r <= 720 else round(b + (r - 700) / 1350 * 1.1, 2)
    K['motor_bb_oleo_bar'] = [oleo(r, 2.8) for r in rpm]
    K['motor_be_oleo_bar'] = [oleo(r, 2.7) for r in rpm]
    if CENARIO == 'alarme-critico':   # §3.5: óleo BB em 95/100/105/110/115/120 s, no regime de cruzeiro (aviso abaixo de 2,4; crítico abaixo de 1,4)
        for t, x in zip(range(95, 121, 5), (3.0, 1.2, 1.1, 1.1, 1.2, 3.0)):
            K['motor_bb_oleo_bar'][t // 5] = x
    arref = [round(78 + (r - 700) / 1350 * 4.0, 1) if r > 720 else 78.0 for r in rpm]
    bb = [arref[(i - 1) % 30] for i in range(30)]   # o líquido esfria e esquenta com atraso de uma chave
    K['motor_bb_arref_c'] = bb
    be = list(bb)
    for t, x in [(95, 86.2), (100, 89.0), (105, 89.6), (110, 89.6), (115, 89.0), (120, 85.8), (125, 82.0)]:   # o AVISO do BE (§3.4: janela de 99 a 116 s)
        be[t // 5] = x
    K['motor_be_arref_c'] = be
    K['motor_bb_carga_pct'] = [10 if r <= 720 else round(10 + (r - 700) / 1350 * 52) for r in rpm]
    K['motor_be_carga_pct'] = [max(0, c - 1) for c in K['motor_bb_carga_pct']]
    K['gerador_kw'] = _kf([(t, round(6.0 + 0.3 * math.sin(t / 150 * 2 * math.pi * 3), 1)) for t in T])
    K['bateria_0_tensao_v'] = [round(27.30 + (r - 700) / 1350 * 0.50, 2) for r in rpm]
    K['bateria_1_tensao_v'] = [round(27.40 + (r - 700) / 1350 * 0.55, 2) for r in rpm]
    K['bateria_2_tensao_v'] = [round(13.55 + (r - 700) / 1350 * 0.15, 2) for r in rpm]
    K['ondas_m'] = [0.7 if x < 10 else 0.8 for x in K['sog_nos']]
    K['vento_verdadeiro_nos'] = _kf([(t, round(10.5 + 1.2 * math.sin(t / 150 * 2 * math.pi), 1)) for t in T])
    K['vento_verdadeiro_angulo'] = _kf([(t, round(58 + 4 * math.sin(t / 150 * 2 * math.pi)) % 360) for t in T])
    K['pressao_barometrica_hpa'] = [1017.1] * 30
    K['temp_ar_externo_c'] = [22.6] * 30
    K['temp_agua_c'] = [20.1] * 30
    K['porao_bb_nivel'] = [1.2] * 30
    K['porao_be_nivel'] = [0.9] * 30
    K['seakeeper_volante_rpm'] = [VOLANTE_RPM] * 30
    K['seakeeper_volante_pct'] = [100] * 30
    K['jogo_graus'] = _kf([(t, round(0.6 * math.sin(t / 150 * 2 * math.pi * 3), 1)) for t in T])
    cai = {0: 0.8, 5: 0.8, 10: 0.8, 15: 0.8, 20: 0.9, 25: 2.6, 30: 4.8, 35: 5.1, 40: 4.4, 45: 3.6, 125: 2.4, 130: 1.2, 135: 0.9, 140: 0.8, 145: 0.8}
    K['caimento_graus'] = _kf([(t, cai.get(t, 3.2)) for t in T])
    pr = [41 if r <= 720 else round(41 + (r - 700) / 1350 * 5) for r in rpm]
    K['temp_praca_maquinas_c'] = [pr[(i - 2) % 30] for i in range(30)]
    K['leme_graus'] = [0.0] * 30   # a base do leme é 0 ± o ruído (0,4°); a rota soma 5 × a taxa de guinada (confere.em)
    assert list(K) == ORDEM_LACO
    return {c: [_sem_menos_zero(x) for x in K[c]] for c in ORDEM_LACO}


FIXOS = {'marcha': 'avante', 'estado': 'Navegando', 'gerador_ativo': True, 'seakeeper_ativo': True, 'ancora_estado': 'recolhida',
         'bomba_porao_ciclos': 0, 'gps_satelites': 18, 'climatizacao_ativa': True, 'dessalinizador_ativo': False, 'radar_ativo': True, 'ais_alvos': 4}
CONTADORES_BASE = {'motor_bb_horimetro_h': 412.6, 'motor_be_horimetro_h': 409.8, 'gerador_horimetro_h': 1236.4, 'diesel_litros': 1560,
                   'distancia_mn': 0, 'tanque_agua_pct': 92, 'tanque_cinzas_pct': 8, 'tanque_negras_pct': 5}   # na âncora (07:00)
TAXAS_H = {'tanque_agua_pct': -1.2, 'tanque_cinzas_pct': 1.4, 'tanque_negras_pct': 0.9}   # por hora desde a âncora
FASES = [{'ini': 0, 'fim': 20, 'nome': 'marcha lenta'}, {'ini': 20, 'fim': 50, 'nome': 'aceleração'}, {'ini': 50, 'fim': 120, 'nome': 'cruzeiro'},
         {'ini': 120, 'fim': 135, 'nome': 'redução'}, {'ini': 135, 'fim': 150, 'nome': 'marcha lenta'}]


def _c(rotulo, origem, un=None, casas=None, **extra):
    d = {'rotulo': rotulo}
    if un is not None:
        d['un'] = un
    if casas is not None:
        d['casas'] = casas
    d['origem'] = origem
    d.update(extra)
    return d


# Catálogo único do quadro (§1.15, §1.22), na ordem do contrato: uma entrada por campo; `casas` é a fonte única do arredondamento.
# `sentido` só (e sempre) nos contadores; `mil` = milhar do pt-BR; `ang` = ângulo de 0 a 360 (3 dígitos na tela).
CAMPOS = {
    'timestamp_utc': _c('Hora da leitura (UTC)', 'relógio'),
    'lat': _c('Latitude', 'rota', '°', 5), 'lon': _c('Longitude', 'rota', '°', 5),
    'cog_graus': _c('Rumo sobre o fundo (COG)', 'rota', '°', 0, ang=True),
    'proa_graus': _c('Proa', 'derivado', '°', 0, ang=True),
    'piloto_rumo': _c('Rumo do piloto automático', 'rota', '°', 0, ang=True),
    'leme_graus': _c('Leme', 'laço', '°', 1, desc='bombordo negativo, boreste positivo'),
    'sog_nos': _c('Velocidade sobre o fundo (SOG)', 'laço', 'nós', 1),
    'stw_nos': _c('Velocidade na água (STW)', 'derivado', 'nós', 1),
    'profundidade_m': _c('Profundidade', 'rota', 'm', 1),
    'motor_bb_rpm': _c('Rotação do motor BB', 'laço', 'rpm', 0, mil=True), 'motor_be_rpm': _c('Rotação do motor BE', 'laço', 'rpm', 0, mil=True),
    'motor_bb_oleo_bar': _c('Pressão de óleo BB', 'laço', 'bar', 1), 'motor_be_oleo_bar': _c('Pressão de óleo BE', 'laço', 'bar', 1),
    'motor_bb_arref_c': _c('Arrefecimento do motor BB', 'laço', '°C', 1), 'motor_be_arref_c': _c('Arrefecimento do motor BE', 'laço', '°C', 1),
    'motor_bb_carga_pct': _c('Carga do motor BB', 'laço', '%', 0), 'motor_be_carga_pct': _c('Carga do motor BE', 'laço', '%', 0),
    'marcha': _c('Marcha', 'fixo'),
    'consumo_lph': _c('Consumo dos dois motores', 'laço', 'L/h', 1),
    'diesel_litros': _c('Diesel a bordo', 'contador', 'L', 0, sentido=-1, mil=True),
    'diesel_bb_pct': _c('Tanque de diesel BB', 'derivado', '%', 1), 'diesel_be_pct': _c('Tanque de diesel BE', 'derivado', '%', 1),
    'distancia_mn': _c('Distância percorrida no dia de bordo', 'contador', 'mn', 1, sentido=1),
    'motor_bb_horimetro_h': _c('Horímetro do motor BB', 'contador', 'h', 1, sentido=1, mil=True),
    'motor_be_horimetro_h': _c('Horímetro do motor BE', 'contador', 'h', 1, sentido=1, mil=True),
    'gerador_ativo': _c('Gerador ligado', 'fixo', 'liga/desliga', 0), 'gerador_kw': _c('Carga do gerador', 'laço', 'kW', 1),
    'gerador_horimetro_h': _c('Horímetro do gerador', 'contador', 'h', 1, sentido=1, mil=True),
    'seakeeper_ativo': _c('Estabilizador ligado', 'fixo', 'liga/desliga', 0),
    'seakeeper_volante_rpm': _c('Volante do estabilizador', 'laço', 'rpm', 0, mil=True),
    'seakeeper_volante_pct': _c('Volante do estabilizador', 'laço', '%', 0),
    'bateria_0_tensao_v': _c('Banco de serviço de 24 V', 'laço', 'V', 2), 'bateria_1_tensao_v': _c('Banco de partida de 24 V', 'laço', 'V', 2),
    'bateria_2_tensao_v': _c('Banco de 12 V', 'laço', 'V', 2),
    'tanque_agua_pct': _c('Tanque de água doce', 'contador', '%', 1, sentido=-1), 'tanque_cinzas_pct': _c('Tanque de águas cinzas', 'contador', '%', 1, sentido=1),
    'tanque_negras_pct': _c('Tanque de águas negras', 'contador', '%', 1, sentido=1),
    'porao_bb_nivel': _c('Nível do porão BB', 'laço', 'cm', 1), 'porao_be_nivel': _c('Nível do porão BE', 'laço', 'cm', 1),
    'bomba_porao_ciclos': _c('Ciclos das bombas de porão na última hora', 'fixo', 'ciclos', 0),
    'ancora_estado': _c('Âncora', 'fixo'),
    'ondas_m': _c('Ondas', 'laço', 'm', 1),
    'vento_verdadeiro_nos': _c('Vento verdadeiro', 'laço', 'nós', 1),
    'vento_verdadeiro_angulo': _c('Vento verdadeiro (de onde vem)', 'laço', '°', 0, ang=True, desc='em relação ao norte verdadeiro'),
    'vento_aparente_nos': _c('Vento aparente', 'derivado', 'nós', 1),
    'vento_aparente_angulo': _c('Vento aparente (em relação à proa)', 'derivado', '°', 0, desc='de -180 a 180; positivo a boreste'),
    'pressao_barometrica_hpa': _c('Pressão atmosférica', 'laço', 'hPa', 1, mil=True),
    'temp_ar_externo_c': _c('Temperatura do ar', 'laço', '°C', 1), 'temp_agua_c': _c('Temperatura da água', 'laço', '°C', 1),
    'temp_praca_maquinas_c': _c('Temperatura da praça de máquinas', 'laço', '°C', 0),
    'jogo_graus': _c('Jogo (balanço de bordo a bordo)', 'laço', '°', 1), 'caimento_graus': _c('Caimento (inclinação de proa a popa)', 'laço', '°', 1),
    'gps_satelites': _c('Satélites do GPS', 'fixo', 'satélites', 0),
    'climatizacao_ativa': _c('Climatização ligada', 'fixo', 'liga/desliga', 0), 'dessalinizador_ativo': _c('Dessalinizador ligado', 'fixo', 'liga/desliga', 0),
    'radar_ativo': _c('Radar transmitindo', 'fixo', 'liga/desliga', 0), 'ais_alvos': _c('Alvos do AIS', 'fixo', 'alvos', 0),
    'estado': _c('Estado', 'fixo'),
    'local': _c('Onde está', 'rota'),
    'destino': _c('Destino', 'rota'), 'destino_mn': _c('Distância ao destino', 'rota', 'mn', 1),
    'wp_proximo': _c('Próximo ponto da rota', 'rota'), 'wp_mn': _c('Distância ao próximo ponto', 'rota', 'mn', 1),
    'eta': _c('Chegada prevista (hora local)', 'rota'),
    'alarmes': _c('Alarmes ativos', 'janela'),
}

# Alertas (§1.16): um id por campo com limite; o nível sai de LIMITES. (id, campo, sistema, lado, título, guia, seção, passos).
ALERTAS_DEF = [
    ('arref_bb', 'motor_bb_arref_c', 'motores', 'bb', 'Temperatura do motor BB', 'g_motores', '5 · Temperatura alta', PASSOS_ARREF),
    ('arref_be', 'motor_be_arref_c', 'motores', 'be', 'Temperatura do motor BE', 'g_motores', '5 · Temperatura alta', PASSOS_ARREF),
    ('oleo_bb', 'motor_bb_oleo_bar', 'motores', 'bb', 'Pressão de óleo do motor BB', 'g_motores', '4 · Pressão de óleo baixa', TXT_OLEO),
    ('oleo_be', 'motor_be_oleo_bar', 'motores', 'be', 'Pressão de óleo do motor BE', 'g_motores', '4 · Pressão de óleo baixa', TXT_OLEO),
    ('rpm_bb', 'motor_bb_rpm', 'motores', 'bb', 'Rotação do motor BB', 'g_motores', '9 · Faixas de operação', PASSOS_ROTACAO),
    ('rpm_be', 'motor_be_rpm', 'motores', 'be', 'Rotação do motor BE', 'g_motores', '9 · Faixas de operação', PASSOS_ROTACAO),
    ('carga_bb', 'motor_bb_carga_pct', 'motores', 'bb', 'Carga do motor BB', 'g_motores', '9 · Faixas de operação', PASSOS_ROTACAO),
    ('carga_be', 'motor_be_carga_pct', 'motores', 'be', 'Carga do motor BE', 'g_motores', '9 · Faixas de operação', PASSOS_ROTACAO),
    ('praca', 'temp_praca_maquinas_c', 'motores', None, 'Temperatura da praça de máquinas', 'g_motores', '9 · Faixas de operação', PASSOS_PRACA),
    ('b24s', 'bateria_0_tensao_v', 'eletrico', None, 'Banco de serviço de 24 V', 'g_eletrico', '2 · Faixas', PASSOS_BATERIA),
    ('b24p', 'bateria_1_tensao_v', 'eletrico', None, 'Banco de partida de 24 V', 'g_eletrico', '2 · Faixas', PASSOS_BATERIA),
    ('b12', 'bateria_2_tensao_v', 'eletrico', None, 'Banco de 12 V', 'g_eletrico', '2 · Faixas', PASSOS_BATERIA),
    ('porao_bb', 'porao_bb_nivel', 'porao', 'bb', 'Nível do porão BB', 'g_porao', '2 · Faixas', PASSOS_PORAO),
    ('porao_be', 'porao_be_nivel', 'porao', 'be', 'Nível do porão BE', 'g_porao', '2 · Faixas', PASSOS_PORAO),
    ('profundidade', 'profundidade_m', 'eletronicos', None, 'Profundidade', 'g_eletronicos', '8 · Sonda', PASSOS_SONDA),
    ('diesel', 'diesel_litros', 'tanques', None, 'Diesel a bordo', 'checklist', 'Abastecimento', PASSOS_DIESEL),
    ('gerador', 'gerador_kw', 'gerador', None, 'Carga do gerador', 'g_gerador', '9 · Potência e carga', PASSOS_GERADOR),
    ('seakeeper', 'seakeeper_volante_pct', 'estabilizador', None, 'Volante do estabilizador', 'g_seakeeper', '8 · Faixas', PASSOS_VOLANTE),
    ('agua', 'tanque_agua_pct', 'tanques', None, 'Tanque de água doce', 'checklist', 'Tanques', PASSOS_AGUA),
    ('cinzas', 'tanque_cinzas_pct', 'tanques', None, 'Tanque de águas cinzas', 'checklist', 'Tanques', PASSOS_SERVIDAS),
    ('negras', 'tanque_negras_pct', 'tanques', None, 'Tanque de águas negras', 'checklist', 'Tanques', PASSOS_SERVIDAS),
]


def alertas_dados():
    out = {}
    for aid, campo, sistema, lado, titulo, guia, secao, passos in ALERTAS_DEF:
        a = {'campo': campo, 'sistema': sistema}
        if lado:
            a['lado'] = lado
        a.update({'titulo': titulo, 'guia': guia, 'secao': secao, 'passos': list(passos), 'fonte': fonte_da_secao(guia, secao)})
        out[aid] = a
    return out


def rota_dados(por_volta_mn):
    """D.rota (§1.14): pernas pré-calculadas (o cliente não recalcula distância), circuito, ida, fator e a conta dos 19 circuitos."""
    pts = [{'id': i, 'nome': n, 'rel': r, 'perto': pe, 'lat': la, 'lon': lo, 'prof_m': pr} for i, n, r, pe, la, lo, pr in PONTOS_ROTA]
    pernas, ini = [], 0.0
    for k, a in enumerate(pts):
        b = pts[(k + 1) % len(pts)]
        mn = arred(mn_entre((a['lat'], a['lon']), (b['lat'], b['lon'])), 4)
        pernas.append({'de': a['id'], 'para': b['id'], 'mn': mn, 'rumo': arred(rumo_entre((a['lat'], a['lon']), (b['lat'], b['lon'])), 2),
                       'ini_mn': arred(ini, 4)})
        ini += mn
    dist = arred(ini, 4)
    ida = next(p['ini_mn'] for p in pernas if p['de'] == ROTA_DESTINO['id'])
    return {
        'fonte': 'Plano de navegação de bordo · Barra Sul ⇄ Estaleirinho',
        'base': pts[0], 'pontos': pts[1:], 'destino': dict(ROTA_DESTINO), 'volta': dict(ROTA_VOLTA), 'pernas': pernas,
        'distancia_mn': dist, 'ida_mn': ida, 'circuitos_dia': CIRCUITOS_DIA,
        'fator': arred(CIRCUITOS_DIA * dist / (VOLTAS_DIA * por_volta_mn), 6),   # fecha os 19 circuitos: a posição está na base às 06:59:59
        'guinada_max_gps': 3, 'corrente': dict(CORRENTE)}


def destinos_dados(rota):
    ini = {p['de']: p['ini_mn'] for p in rota['pernas']}
    ordem = [('cabras', 'Ilha das Cabras'), ('laranjeiras', 'Ponta das Laranjeiras'), ('taquaras', 'Taquaras'), ('estaleirinho', 'Estaleirinho')]
    return [{'id': i, 'nome': n, 'mn': arred(ini[i], 1)} for i, n in ordem]


_REPLAY = {}


def replay_dados():
    """(replay, rota, campos) do D, calculados uma vez por cenário (o laço de 150 s, as janelas e a rota não mudam entre as chamadas)."""
    chave = (CENARIO, SIMULACAO, CIRCUITOS_DIA)
    if chave not in _REPLAY:
        _REPLAY.clear()
        _REPLAY[chave] = _replay_dados()
    return _REPLAY[chave]


def _replay_dados():
    campos = {c: dict(d) for c, d in CAMPOS.items()}
    alertas = alertas_dados()
    R = {'duracao': 150, 'passo': 1, 'passo_chave': 5, 'cenario': CENARIO, 'ancora_hora': ANCORA_HORA, 'voltas_fixo': 120}
    chaves = chaves_laco()
    R['chaves'] = chaves
    R['ruido'] = {c: [AMPLITUDE_RUIDO[c], 1100 + ORDEM_LACO.index(c)] for c in ORDEM_LACO}
    R['ruido']['proa_graus'] = [0.4, SEMENTE_PROA]
    R['ruido']['profundidade_m'] = [0.2, SEMENTE_PROF]
    R['fixos'] = dict(FIXOS)
    Q = [quadro_laco(R, campos, t) for t in range(150)]
    ger = CONSUMO['gerador_lph']
    pv = {'diesel_l': arred(sum(q['consumo_lph'] + ger for q in Q) / 3600, 4), 'motores_l': arred(sum(q['consumo_lph'] for q in Q) / 3600, 4),
          'gerador_l': arred(ger * 150 / 3600, 4), 'distancia_mn': arred(sum(q['sog_nos'] for q in Q) / 3600, 4),
          'motor_h': arred(150 / 3600, 6), 'gerador_h': arred(150 / 3600, 6)}
    rota = rota_dados(pv['distancia_mn'])
    R.update({'velocidade_media_nos': arred(CIRCUITOS_DIA * rota['distancia_mn'] / 24, 4), 'fases': [dict(f) for f in FASES]})
    R['contadores_base'] = dict(CONTADORES_BASE)
    R['taxas_h'] = dict(TAXAS_H)
    R['por_volta'] = pv
    R['por_dia'] = {'voltas': VOLTAS_DIA, 'diesel_l': arred(VOLTAS_DIA * pv['diesel_l'], 1), 'distancia_mn': arred(VOLTAS_DIA * pv['distancia_mn'], 1),
                    'motor_h': 24, 'gerador_h': 24}
    R['diesel_piso_l'] = DIESEL_AVISO_L
    R['limites'] = LIMITES
    R['alertas'] = alertas
    R['janelas'] = deriva_janelas(R, campos)
    R['diaDeBordo'] = dia_de_bordo(R)
    return R, rota, campos


def dia_de_bordo(R):
    """replay.diaDeBordo (§1.8–§1.10): o que a microtarefa do rodapé insere só com simulacao: true (abastecimento das 07:00 × 3 dias, d01, d02
    e a nota fiscal). Litros = o salto do contador na virada (por_dia); nível antes/depois = o diesel % de A − 1 s e de A."""
    litros = int(math.floor(R['por_dia']['diesel_l'] + 0.5))
    base = R['contadores_base']['diesel_litros']
    antes, depois = arred((base - R['por_dia']['diesel_l']) / TANQUES['diesel_l'] * 100, 1), arred(base / TANQUES['diesel_l'] * 100, 1)
    return {
        'dias': DIAS_DE_BORDO,
        'abastecimento': {'h': ANCORA_HORA, 'litros': litros, 'combustivel': 'diesel', 'local': 'posto da marina da base', 'st': 'CONFERIDO',
                          'nivelAntes': antes, 'nivelDepois': depois, 'nota': 'para a saída das %s · nota fiscal conferida (Documentos)' % ANCORA_HORA},
        'documento': {'id': 'nf-abast', 'n': 'Nota fiscal do abastecimento', 'cat': 'Notas', 'emitidoHa': 0, 'st': 'CONFERIDA', 'ref': 'ab-0',
                      'nota': 'abastecimento das %s · sem valores no app' % ANCORA_HORA, 'fonte': DOCS_FONTE},
        'diario': [
            {'id': 'd01', 'diasAtras': 0, 'h': ANCORA_HORA, 'sys': 'Navegação', 'tom': 'tele', 'who': 'Lucas', 'pend': False,
             't': 'Saída da Barra Sul às %s com %d pessoas a bordo: passeio Barra Sul ⇄ Estaleirinho pela Interpraias. Checklist de saída feito; '
                  'o teste das bombas de porão continua pendente.' % (ANCORA_HORA, EMBARCACAO['pessoasBordo'])},
            {'id': 'd02', 'diasAtras': 0, 'h': ANCORA_HORA, 'sys': 'Combustível', 'tom': 'ok', 'who': 'Lucas', 'pend': False, 'ref': 'ab-0',
             't': 'Abastecimento de %s L de diesel no posto da marina da base para a saída das %s, com água completada e servidas esvaziadas; '
                  'tanques de diesel em %s %%.' % (br(litros), ANCORA_HORA, num_br(depois, 1))}]}


# ——————————————————————————————— HISTÓRICO (CONTRATO §1.13) ———————————————————————————————
# Só na simulação (com SIMULACAO = False o gerador não emite histórico simulado, §4.3). Cada dia de bordo repete o modelo de 24 h (o laço de
# 150 s e os contadores), e os baldes dos gráficos são múltiplos de 150 s alinhados às 07:00; então o gerador guarda só o que NÃO é laço nem
# contador: o desvio lento de tempo e baterias em relação a hoje (um a cada 2 dias, de 366 dias atrás até 2 dias atrás; hoje = 0, e o cliente
# interpola linearmente até 0 na âncora), a curva do ano do ar e da água (tabela por dia do calendário, em relação à média do ano) e as médias
# de cruzeiro da F11. Tudo em inteiros com escala (valor real = d / escala), sem Math.sin no cliente. O último ponto de qualquer série é o quadro
# de hoje (desvio 0). Sem maré nem previsão (trava §2.5): tempo e maré são sempre os reais.
HIST_PASSO_DIAS, HIST_N = 2, 183              # d[0] = 366 dias atrás … d[182] = 2 dias atrás
SAZONAL_PASSO_DIAS, SAZONAL_N = 5, 73         # 1º de janeiro = índice 0; 73 × 5 = 365 dias
CRUZEIRO_DIAS = 60                            # d[0] = 60 dias atrás … d[59] = ontem
HIST_SEMENTE = 2000                           # sementes do ruído por hash (h32), fora das do laço (1100 + n) e da rota (1201, 1202)
# (campo, escala, amplitude real, oitavas (período em pontos de 2 dias, peso), semente): as amplitudes são as do contrato (±4 nós, ±7 hPa,
# ±0,06 V, ±1,5 °C no ar e ±0,4 °C na água); a série é normalizada para chegar exatamente à amplitude.
DESVIOS_DEF = [
    ('vento_verdadeiro_nos', 10, 4.0, ((4, 1.0), (2, 0.7), (1, 0.4)), 1),
    ('pressao_barometrica_hpa', 10, 7.0, ((6, 1.0), (3, 0.5)), 2),
    ('bateria_0_tensao_v', 100, 0.06, ((6, 1.0), (3, 0.7), (1, 0.3)), 22),   # semente escolhida: a semana da série 24 V (serie24v) varia 0,04 V
    ('bateria_1_tensao_v', 100, 0.06, ((7, 1.0), (3, 0.6), (1, 0.3)), 4),
    ('bateria_2_tensao_v', 100, 0.06, ((5, 1.0), (2, 0.6), (1, 0.3)), 5),
    ('temp_ar_externo_c', 10, 1.5, ((5, 1.0), (2, 0.6)), 6),
    ('temp_agua_c', 10, 0.4, ((12, 1.0), (4, 0.5)), 7),
]
# (campo, amplitude real, dia do calendário do máximo): ar +4,5 °C em meados de janeiro e −4,5 °C em meados de julho; água +3,5 °C em meados de
# fevereiro e −3,5 °C em meados de agosto (litoral de SC, hemisfério sul).
SAZONAL_DEF = [('temp_ar_externo_c', 4.5, 15), ('temp_agua_c', 3.5, 45)]
JANELAS_HIST = {'150S': {'passo_s': 1, 'n': 150}, '1D': {'passo_s': 900, 'n': 96}, '7D': {'passo_s': 3600, 'n': 168},
                '30D': {'passo_s': 21600, 'n': 120}, '1A': {'passo_s': 86400, 'n': 365}}
METRICAS_HIST = {'b24': ['bateria_0_tensao_v', 'bateria_1_tensao_v'], 'b12': ['bateria_2_tensao_v'],
                 'tanques': ['tanque_agua_pct', 'tanque_cinzas_pct', 'tanque_negras_pct'], 'vento': ['vento_verdadeiro_nos'],
                 'pressao': ['pressao_barometrica_hpa'], 'diesel': ['diesel_litros'],
                 'temperaturas': ['temp_praca_maquinas_c', 'temp_ar_externo_c', 'temp_agua_c'],
                 'motores': ['motor_bb_rpm', 'motor_be_rpm'], 'oleo': ['motor_bb_oleo_bar', 'motor_be_oleo_bar'],
                 'arref': ['motor_bb_arref_c', 'motor_be_arref_c'], 'navegacao': ['sog_nos', 'stw_nos'], 'consumo': ['consumo_lph']}
SO150_HIST = ['motores', 'oleo', 'arref', 'navegacao', 'consumo']   # grupos só do laço: nas janelas longas a volta se repete e a linha sairia reta
# Cruzeiro (F11): médias por dia de bordo. BB estável em 82,0 ± 0,2 °C; BE sobe de 82,4 a 83,9 °C em 60 dias (hoje, 84,5 pelo laço com os picos,
# 2,5 °C acima do BB); óleo ao redor do de hoje (3,9 e 3,8 bar). (escala, centro real, amplitude real, semente); no BE o centro é (início, fim) da subida.
CRUZEIRO_BB_ARREF, CRUZEIRO_BE_ARREF = (10, 82.0, 0.2, 11), (10, (82.4, 83.9), 0.1, 12)
CRUZEIRO_OLEO = {'motor_bb_oleo_bar': (100, 3.90, 0.03, 13), 'motor_be_oleo_bar': (100, 3.80, 0.03, 14)}


def _meio(x):
    return int(math.floor(x + 0.5))   # arredonda a metade para cima (sem o round() do Python, que vai pelo par)


def _suave(semente, n, oitavas):
    """n pontos em [−1, 1]: ruído de valor em oitavas ((período em pontos, peso), …), com suavização entre as âncoras (h32 do confere:
    determinístico, sem relógio nem Math.sin); normalizado para o pico dar exatamente ±1."""
    pesos = sum(p for _, p in oitavas)
    v = []
    for i in range(n):
        t = 0.0
        for o, (per, peso) in enumerate(oitavas):
            j, r = divmod(i, per)
            f = r / per
            a, b = ruido(semente * 10 + o, j), ruido(semente * 10 + o, j + 1)
            t += peso * (a + (b - a) * f * f * (3 - 2 * f))
        v.append(t / pesos)
    m = max(abs(x) for x in v) or 1
    return [x / m for x in v]


def sazonal_tabela(amp, dia_pico):
    """A curva do ano em décimos de grau, a cada SAZONAL_PASSO_DIAS dias do calendário (índice 0 = 1º de janeiro), com o máximo em dia_pico."""
    return [_meio(amp * 10 * math.cos(2 * math.pi * (SAZONAL_PASSO_DIAS * i - dia_pico) / 365)) for i in range(SAZONAL_N)]


def cruzeiro_dados():
    n = CRUZEIRO_DIAS
    bb_e, be_e = CRUZEIRO_BB_ARREF, CRUZEIRO_BE_ARREF
    ruido_bb, ruido_be = _suave(HIST_SEMENTE + bb_e[3], n, ((4, 1.0), (1, 0.6))), _suave(HIST_SEMENTE + be_e[3], n, ((4, 1.0), (1, 0.6)))
    de, ate = be_e[1]
    out = {'dias': n,
           'motor_bb_arref_c': {'escala': bb_e[0], 'd': [_meio(bb_e[0] * (bb_e[1] + bb_e[2] * ruido_bb[i])) for i in range(n)]},
           'motor_be_arref_c': {'escala': be_e[0], 'd': [_meio(be_e[0] * (de + (ate - de) * i / (n - 1) + be_e[2] * ruido_be[i])) for i in range(n)]}}
    for campo, (esc, centro, amp, sem) in CRUZEIRO_OLEO.items():
        r = _suave(HIST_SEMENTE + sem, n, ((5, 1.0), (1, 0.5)))
        out[campo] = {'escala': esc, 'd': [_meio(esc * (centro + amp * r[i])) for i in range(n)]}
    return out


def historico_dados():
    """D.historico (§1.13), na ordem do contrato. Determinístico (nenhuma data nem aleatório do sistema)."""
    desvios = {}
    for campo, esc, amp, oit, sem in DESVIOS_DEF:
        desvios[campo] = {'escala': esc, 'd': [_meio(esc * amp * x) for x in _suave(HIST_SEMENTE + sem, HIST_N, oit)]}
    sazonal = {'passo_dias': SAZONAL_PASSO_DIAS, 'n': SAZONAL_N}
    for campo, amp, pico in SAZONAL_DEF:
        sazonal[campo] = {'escala': 10, 'd': sazonal_tabela(amp, pico)}
    return {'fim': 'ancora', 'passo_dias': HIST_PASSO_DIAS, 'n': HIST_N, 'desvios': desvios, 'sazonal': sazonal, 'cruzeiro': cruzeiro_dados(),
            'janelas': {k: dict(v) for k, v in JANELAS_HIST.items()}, 'metricas': {k: list(v) for k, v in METRICAS_HIST.items()},
            'so150': list(SO150_HIST), 'fonte': 'coletor NMEA de bordo · histórico'}


# ——————————————————————————————— CHECKLISTS, SENSORES, PEÇAS E ALARMES PEDIDOS (CONTRATO §1.18–§1.21) ———————————————————————————————
# F09 (checklists guiados), F08 (sensores sobre o desenho), F22 (peças e estoque) e F12 (alarmes pedidos no chat). Só a FORMA vem do Avanti 1.24.0
# (id, c, t, fonte, auto, parcial, faq, link; ponto com bloco; peça com qtd e mínimo; métrica com faixa): o conteúdo é do Capitão. Os ids, os
# rótulos `c`, o ✓ automático, o FAQ, as faixas e a fórmula do bloco têm a referência no confere.py (asserção FUNCOES); aqui ficam os textos.
BOA_PRATICA = 'boa prática'   # fonte do item que não tem seção nos guias gerados (procedimento comum de marinharia, sem número)
CK_TIPOS = [   # `l` = rótulo da aba, `aba` = a linha curta embaixo, `nome` = o título da tela, `sys` = a categoria da linha que o CONCLUIR grava no diário
    {'id': 'saida', 'l': 'Saída', 'aba': 'antes de largar', 'nome': 'Checklist de saída', 'sys': 'Navegação'},
    {'id': 'chegada', 'l': 'Chegada', 'aba': 'ao atracar', 'nome': 'Checklist de chegada', 'sys': 'Navegação'},
    {'id': 'abastecimento', 'l': 'Abastecimento', 'aba': 'no posto', 'nome': 'Checklist de abastecimento', 'sys': 'Combustível'},
    {'id': 'fundeio', 'l': 'Fundeio', 'aba': 'ao fundear', 'nome': 'Checklist de fundeio', 'sys': 'Navegação'},
]


def _ck(i, c, t, fonte, auto=None, parcial=False, faq=None, link=None):
    """Item do checklist na ordem de chaves do contrato; o que não se aplica é omitido (nunca null)."""
    it = {'id': i, 'c': c, 't': t, 'fonte': fonte}
    for k, v in (('auto', auto), ('parcial', True if parcial else None), ('faq', faq), ('link', link)):
        if v is not None:
            it[k] = v
    return it


def _fs(guia, secao):
    """«Guia de bordo — … §n · título» (seção numerada) ou «Checklist de bordo § título»; a seção tem de existir no guia (asserção FUNCOES)."""
    return fonte_da_secao(guia, secao)


# Os textos que a tabela do §1.18 abrevia ficam por extenso. O s05 e o a07 dizem «em cada tanque» (a tabela do contrato, e o ✓ mostra os dois lados);
# a regra do guia (§ Abastecimento) e o alerta de diesel são sobre o total dos tanques: dois tanques acima de 25 % já cumprem a do guia.
def checklists_dados():
    """D.checklists (§1.18): 4 tipos, 14 + 8 + 7 + 6 itens."""
    CK, ELE, ANC = 'checklist', 'g_eletronicos', 'g_ancora'
    itens = {
        'saida': [
            _ck('s01', 'previsão', 'Previsão do dia consultada (vento e mar) — confira o boletim da Marinha antes de sair.',
                _fs(CK, 'Saída · antes de largar'), 'tempo', True),
            _ck('s02', 'alertas', 'Nenhum alerta ativo no painel.', BOA_PRATICA, 'alertas'),
            _ck('s03', 'motores frios', 'Óleo, arrefecimento, correias e válvulas de fundo conferidos com os motores frios.',
                _fs('g_motores', '1 · Antes da partida'), faq='MO-01'),
            _ck('s04', 'porão', 'Porão seco e bombas testadas no manual.', _fs('g_porao', '3 · Teste mensal'), 'porao', True, 'PO-03'),
            _ck('s05', 'diesel', 'Diesel acima de %s %% em cada tanque.' % br(DIESEL_AVISO_PCT), _fs(CK, 'Abastecimento'), 'diesel'),
            _ck('s06', 'tanques', 'Água doce acima de %s %%; servidas abaixo de %s %%.' % (
                br(LIMITES['tanque_agua_pct']['aviso']['abaixo']), br(LIMITES['tanque_cinzas_pct']['aviso']['acima'])), _fs(CK, 'Tanques'), 'tanques'),
            _ck('s07', 'baterias', 'Bancos de 24 V e 12 V dentro da faixa.', _fs('g_eletrico', '2 · Faixas'), 'baterias', faq='EE-02'),
            _ck('s08', 'gerador', 'Gerador ligado: água saindo pelo escapamento.', _fs('g_gerador', '3 · Água no escapamento'), faq='GE-03'),
            _ck('s09', 'estabilizador', 'Estabilizador ligado com antecedência (o display indica quando está pronto).',
                _fs('g_seakeeper', '2 · Ligar antes de sair'), 'seakeeper', faq='SK-02'),
            _ck('s10', 'plotter e VHF', 'Plotter ligado, piloto em espera e VHF no canal 16.', _fs(CK, 'Saída · 4 a 6'), faq='EL-04'),
            _ck('s11', 'documentos', 'Documentos em dia (TIE, seguro, Licença de Estação).', BOA_PRATICA, 'documentos', True),
            _ck('s12', 'tarefas de segurança', 'Nenhuma tarefa de segurança atrasada.', BOA_PRATICA, 'tarefas'),
            _ck('s13', 'coletes e salvatagem', 'Coletes: um por pessoa — conte as pessoas a bordo agora; balsa, boia e extintores conforme a placa de salvatagem.',
                _fs(CK, 'Saída · antes de largar'), faq='EM-09'),
            _ck('s14', 'cabos e defensas', 'Cabos e defensas recolhidos depois de largar.', BOA_PRATICA),
        ],
        'chegada': [
            _ck('c01', 'piloto', 'Piloto em espera antes de manobrar.', _fs(ELE, '2 · Piloto automático'), faq='EL-02'),
            _ck('c02', 'estabilizador', 'Estabilizador desligado ao atracar; energia até o volante parar.', _fs('g_seakeeper', '4 · Desligar ao atracar'),
                'seakeeperOff', faq='SK-04'),
            _ck('c03', 'motores', 'Motores %s min em marcha lenta antes de desligar.' % de_a(PARADA_MOTORES_MIN), _fs('g_motores', '6 · Parada'), 'motoresOff',
                faq='MO-06'),
            _ck('c04', 'gerador', 'Gerador sem cargas, alguns minutos para esfriar e desligado.', _fs('g_gerador', '4 · Desligar'), 'geradorOff', faq='GE-04'),
            _ck('c05', 'climatização', 'Climatização desligada e válvula de fundo fechada se o barco ficar parado.', _fs('g_clima', '5 · Desligar'), faq='CL-05'),
            _ck('c06', 'porão', 'Porão conferido: nível normal e bombas no automático.', _fs('g_porao', '2 · Faixas'), 'porao'),
            _ck('c07', 'cabos e defensas', 'Cabos e defensas prontos antes de atracar.', BOA_PRATICA),
            _ck('c08', 'diário', 'Saída fechada no diário: horas, consumo e pendências.', _fs(CK, 'Chegada'), link='G3-Diario'),
        ],
        'abastecimento': [
            _ck('a01', 'motores', 'Motores desligados.', BOA_PRATICA, 'motoresOff'),
            _ck('a02', 'gerador', 'Gerador desligado.', BOA_PRATICA, 'geradorOff'),
            _ck('a03', 'nível antes', 'Nível de diesel anotado antes.', BOA_PRATICA, 'diesel'),
            _ck('a04', 'sem fumar', 'Sem fumar a bordo; extintor portátil à mão.', BOA_PRATICA),
            _ck('a05', 'bocal e tampa', 'Bocal certo (diesel) e tampa do tanque fechada depois.', BOA_PRATICA),
            _ck('a06', 'nível depois', 'Nível depois anotado em Abastecimento.', _fs(CK, 'Abastecimento'), link='G2-Abastecimento'),
            _ck('a07', 'regra do diesel', 'Diesel acima de %s %% em cada tanque antes de sair.' % br(DIESEL_AVISO_PCT), _fs(CK, 'Abastecimento'), faq='CK-05'),
        ],
        'fundeio': [
            _ck('f01', 'profundidade', 'Profundidade conferida na sonda.', _fs(ELE, '8 · Sonda'), 'profundidade', faq='EL-08'),
            _ck('f02', 'corrente', 'Corrente: lance de %s vezes a profundidade.' % de_a(LANCE_ANCORA_VEZES), _fs(ANC, '1 · Lançar'), faq='AN-01'),
            _ck('f03', 'alarme de âncora', 'Alarme de âncora ativado no plotter, com o raio.', _fs(ELE, '3 · Alarme de âncora'), faq='EL-03'),
            _ck('f04', 'deriva', 'Motores em neutro e deriva conferida.', BOA_PRATICA, 'deriva'),
            _ck('f05', 'guincho', 'Guincho desligado e trava da corrente.', _fs(ANC, '3 · Recolher e travar'), faq='AN-03'),
            _ck('f06', 'maré e vento', 'Maré e vento conferidos (previsão da Marinha).', BOA_PRATICA, 'mare'),
        ],
    }
    return {'fonte': ARQ['checklist'], 'tipos': [dict(t) for t in CK_TIPOS], 'itens': itens}


# F08 (§1.19): n, id, vista, l, a (perfil) ou b (planta), rótulo, onde (vocabulário fechado, sem «boia») e os campos do quadro que o ponto mostra.
# l = 0 na popa e 1 na proa; a = 0 na quilha e 1 no topo; b = −1 em BB e +1 em BE. Nenhum ponto é equipamento de salvatagem nem de incêndio.
SENSORES_DEF = [
    (1, 'gps', 'perfil', 0.55, 0.95, 'Antena GPS', 'hard-top', ['gps_satelites']),
    (2, 'radar', 'perfil', 0.52, 1.0, 'Radar', 'mastro do radar', ['radar_ativo']),
    (3, 'meteo', 'perfil', 0.48, 1.0, 'Estação meteorológica', 'mastro do radar',
     ['vento_verdadeiro_nos', 'vento_verdadeiro_angulo', 'vento_aparente_nos', 'vento_aparente_angulo', 'temp_ar_externo_c', 'pressao_barometrica_hpa']),
    (4, 'sonda', 'perfil', 0.62, 0.05, 'Sonda', 'casco · meia-nau', ['profundidade_m', 'temp_agua_c']),
    (5, 'inclinometro', 'perfil', 0.50, 0.35, 'Inclinômetro', 'meia-nau', ['jogo_graus', 'caimento_graus', 'proa_graus']),
    (6, 'estabilizador', 'perfil', 0.45, 0.20, 'Estabilizador', 'praça de máquinas · centro', ['seakeeper_volante_rpm', 'seakeeper_volante_pct']),
    (7, 'praca', 'perfil', 0.25, 0.30, 'Praça de máquinas', 'praça de máquinas', ['temp_praca_maquinas_c']),
    (8, 'motor_bb', 'planta', 0.25, -0.40, 'Motor BB', 'praça de máquinas · BB',
     ['motor_bb_rpm', 'motor_bb_oleo_bar', 'motor_bb_arref_c', 'motor_bb_carga_pct', 'motor_bb_horimetro_h']),
    (9, 'motor_be', 'planta', 0.25, 0.40, 'Motor BE', 'praça de máquinas · BE',
     ['motor_be_rpm', 'motor_be_oleo_bar', 'motor_be_arref_c', 'motor_be_carga_pct', 'motor_be_horimetro_h']),
    (10, 'gerador', 'planta', 0.18, 0.0, 'Gerador', 'praça de máquinas · ré', ['gerador_kw', 'gerador_horimetro_h']),
    (11, 'diesel_bb', 'planta', 0.38, -0.60, 'Tanque de diesel BB', 'meia-nau · BB', ['diesel_bb_pct']),
    (12, 'diesel_be', 'planta', 0.38, 0.60, 'Tanque de diesel BE', 'meia-nau · BE', ['diesel_be_pct']),
    (13, 'agua', 'planta', 0.60, 0.0, 'Tanque de água doce', 'meia-nau', ['tanque_agua_pct']),
    (14, 'servidas', 'planta', 0.70, 0.30, 'Tanques de servidas', 'meia-nau · BE', ['tanque_cinzas_pct', 'tanque_negras_pct']),
    (15, 'b24s', 'planta', 0.30, -0.15, 'Banco de serviço 24 V', 'praça de máquinas · BB', ['bateria_0_tensao_v']),
    (16, 'b24p', 'planta', 0.30, 0.15, 'Banco de partida 24 V', 'praça de máquinas · BE', ['bateria_1_tensao_v']),
    (17, 'b12', 'planta', 0.55, 0.20, 'Banco 12 V', 'painel do comando', ['bateria_2_tensao_v']),
    (18, 'porao_bb', 'planta', 0.22, -0.25, 'Sensor de nível do porão BB', 'praça de máquinas · BB', ['porao_bb_nivel']),
    (19, 'porao_be', 'planta', 0.22, 0.25, 'Sensor de nível do porão BE', 'praça de máquinas · BE', ['porao_be_nivel', 'bomba_porao_ciclos']),
    (20, 'leme', 'planta', 0.04, 0.0, 'Leme', 'popa', ['leme_graus', 'piloto_rumo']),
    (21, 'guincho', 'planta', 0.95, 0.0, 'Guincho e contador de corrente', 'proa · guincho da âncora', ['ancora_estado']),
    (22, 'dessal', 'planta', 0.33, 0.20, 'Dessalinizador', 'praça de máquinas · BE', ['dessalinizador_ativo']),
]


SENSORES_IMG = {'perfil': {'img': 'assets/sensores-perfil.svg', 'w': 1200, 'h': 360}, 'planta': {'img': 'assets/sensores-planta.svg', 'w': 1200, 'h': 420}}
SENSORES_REF = {'popa_x': 0.04, 'proa_x': 0.95, 'quilha_y': 0.92, 'topo_y': 0.08, 'eixo_y': 0.5, 'meia_boca': 0.32}   # frações do desenho; o da Fase 4 as segue


def sensores_dados():
    """D.sensores (§1.19): o desenho (caminho e tamanho; o desenho da Fase 4 segue a `referencia`), os 22 pontos com x, y e o bloco das duas plataformas."""
    pontos = []
    for n, i, vista, l, ab, rotulo, ond, campos in SENSORES_DEF:
        p = {'n': n, 'id': i, 'vista': vista, 'l': l, 'a' if vista == 'perfil' else 'b': ab}
        p['x'], p['y'] = sensor_xy(p, SENSORES_REF)
        p.update({'rotulo': rotulo, 'onde': ond, 'campos': list(campos)})
        pontos.append(p)
    blocos = {plat: {v: blocos_sensores([p for p in pontos if p['vista'] == v], plat) for v in ('perfil', 'planta')} for plat in ('web', 'app')}
    for p in pontos:
        p['bloco'] = {plat: blocos[plat][p['vista']][p['id']] for plat in ('web', 'app')}
    return {'perfil': dict(SENSORES_IMG['perfil']), 'planta': dict(SENSORES_IMG['planta']), 'referencia': dict(SENSORES_REF), 'pontos': pontos}


# F22 (§1.20): sem código de fabricante (um `pn` inventado de fabricante real leva à compra errada) e sem preço; `local` de vocabulário fechado
# (estante técnica 1–3, caixa de sobressalentes A–C, armário de ferramentas); nenhuma peça de salvatagem. A BAIXA (p03) e a ZERO (p05, a falta do diário d03).
PECAS = [
    {'id': 'p01', 'n': 'Filtro de óleo do motor', 'qtd': 4, 'min': 2, 'local': 'estante técnica 1', 'tarefas': ['motores-oleo']},
    {'id': 'p02', 'n': 'Filtro de combustível (separador de água) dos motores', 'qtd': 4, 'min': 2, 'local': 'estante técnica 1', 'tarefas': ['motores-revisao']},
    {'id': 'p03', 'n': 'Rotor (impeller) da bomba de água salgada dos motores', 'qtd': 1, 'min': 2, 'local': 'caixa de sobressalentes A', 'tarefas': ['motores-rotor']},
    {'id': 'p04', 'n': 'Correia do alternador', 'qtd': 2, 'min': 1, 'local': 'caixa de sobressalentes A', 'tarefas': ['motores-revisao']},
    {'id': 'p05', 'n': 'Rotor (impeller) do gerador', 'qtd': 0, 'min': 1, 'local': 'caixa de sobressalentes B', 'tarefas': ['gerador-rotor']},
    {'id': 'p06', 'n': 'Filtro de óleo do gerador', 'qtd': 2, 'min': 1, 'local': 'estante técnica 2', 'tarefas': ['gerador-revisao']},
    {'id': 'p07', 'n': 'Anodo do trocador de calor do estabilizador', 'qtd': 2, 'min': 1, 'local': 'caixa de sobressalentes B', 'tarefas': ['seakeeper-anodo']},
    {'id': 'p08', 'n': 'Jogo de anodos do eixo e do casco', 'qtd': 1, 'min': 1, 'local': 'estante técnica 3', 'tarefas': ['casco-anodos']},
    {'id': 'p09', 'n': 'Tela do filtro de água salgada da climatização', 'qtd': 1, 'min': 1, 'local': 'caixa de sobressalentes C', 'tarefas': ['clima-filtro']},
    {'id': 'p10', 'n': 'Pré-filtro do dessalinizador', 'qtd': 2, 'min': 2, 'local': 'caixa de sobressalentes C'},
    {'id': 'p11', 'n': 'Jogo de fusíveis de 24 V', 'qtd': 1, 'min': 1, 'local': 'armário de ferramentas', 'tarefas': ['baterias']},
    {'id': 'p12', 'n': 'Escova do limpador do para-brisa', 'qtd': 2, 'min': 1, 'local': 'armário de ferramentas'},
]

# F12 (§1.21): a lista fechada de métricas que o chat aceita em «me avise se…». A regra é a `faixa` própria de cada métrica (a referência está no
# confere.py: FAIXAS_PEDIDAS), não o D.replay.limites: vento, SOG, pressão e a água do mar não têm limite de alarme no guia. `nome`, `un` e `casas` saem do D.campos.
# `palavras`: o que o ditado e o teclado escrevem, sem acento e em minúsculas (palavra que cabe dentro de outra vai com espaço, ' sog '). A palavra
# sem o lado vale nos dois motores: o pedido sem «BB» nem «BE» abre um alarme para cada um (Fase 3).
ALARMES_PEDIDOS_DEF = [   # (id, campo, faixa [mín, máx], palavras, motor)
    ('oleo_bb', 'motor_bb_oleo_bar', (0.5, 6.0),
     ['pressao do oleo', 'pressao de oleo', 'oleo do motor', 'oleo bb', 'oleo do bb', 'oleo de bombordo', 'oleo do motor bb', 'oleo do motor de bombordo'], True),
    ('oleo_be', 'motor_be_oleo_bar', (0.5, 6.0),
     ['pressao do oleo', 'pressao de oleo', 'oleo do motor', 'oleo be', 'oleo do be', 'oleo de boreste', 'oleo do motor be', 'oleo do motor de boreste'], True),
    ('arref_bb', 'motor_bb_arref_c', (60, 100),
     ['arrefecimento', 'temperatura do motor', 'temperatura de arrefecimento', 'arrefecimento bb', 'arrefecimento do bb', 'arrefecimento de bombordo',
      'temperatura do motor bb', 'temperatura do motor de bombordo', 'temperatura do bb'], True),
    ('arref_be', 'motor_be_arref_c', (60, 100),
     ['arrefecimento', 'temperatura do motor', 'temperatura de arrefecimento', 'arrefecimento be', 'arrefecimento do be', 'arrefecimento de boreste',
      'temperatura do motor be', 'temperatura do motor de boreste', 'temperatura do be'], True),
    ('rpm_bb', 'motor_bb_rpm', (500, 2600),
     ['rotacao', 'rpm', 'giro do motor', 'rotacao bb', 'rotacao do bb', 'rotacao de bombordo', 'rpm bb', 'rpm do bb', 'giro do bb'], True),
    ('rpm_be', 'motor_be_rpm', (500, 2600),
     ['rotacao', 'rpm', 'giro do motor', 'rotacao be', 'rotacao do be', 'rotacao de boreste', 'rpm be', 'rpm do be', 'giro do be'], True),
    ('b24s', 'bateria_0_tensao_v', (22.0, 30.0), ['banco de servico', 'bateria de servico', 'tensao de servico', 'bateria de 24'], False),
    ('b24p', 'bateria_1_tensao_v', (22.0, 30.0), ['banco de partida', 'bateria de partida', 'tensao de partida', 'bateria de 24'], False),
    ('b12', 'bateria_2_tensao_v', (11.0, 15.0), ['banco de 12', 'bateria de 12', 'banco da eletronica', 'bateria da eletronica'], False),
    ('profundidade', 'profundidade_m', (1, 50), ['profundidade', 'sonda', 'fundo raso'], False),
    ('vento', 'vento_verdadeiro_nos', (5, 50), ['vento', 'rajada', 'vento verdadeiro'], False),
    ('sog', 'sog_nos', (1, 30), ['velocidade', ' sog ', 'velocidade sobre o fundo'], False),
    ('pressao', 'pressao_barometrica_hpa', (980, 1040), ['pressao atmosferica', 'pressao barometrica', 'barometro', ' hpa '], False),
    ('agua_mar', 'temp_agua_c', (10, 32), ['temperatura da agua', 'agua do mar', 'temperatura do mar'], False),
    ('diesel', 'diesel_litros', (100, 1600), ['diesel', 'combustivel', 'nivel de diesel', 'litros de diesel'], False),
    ('agua', 'tanque_agua_pct', (5, 100), ['agua doce', 'tanque de agua', 'nivel de agua'], False),
    ('cinzas', 'tanque_cinzas_pct', (5, 100), ['aguas cinzas', 'agua cinza', 'cinzas', 'servidas'], False),
    ('negras', 'tanque_negras_pct', (5, 100), ['aguas negras', 'agua negra', 'negras', 'servidas'], False),
]


def alarmes_pedidos_dados():
    """D.alarmesPedidos (§1.21): a chave do aparelho, o teto de 10, a histerese de 10 s, nível só aviso e as 18 métricas, cada uma com a sua faixa."""
    ms = []
    for i, campo, (lo, hi), palavras, motor in ALARMES_PEDIDOS_DEF:
        d = CAMPOS[campo]
        m = {'id': i, 'campos': [campo], 'nome': d['rotulo'], 'palavras': list(palavras), 'un': d['un'], 'casas': d['casas'], 'faixa': [lo, hi], 'ops': ['<', '>']}
        if motor:
            m['motor'] = True
        ms.append(m)
    return {'chave': 'capitao.alarmes.v1', 'max': 10, 'histerese_s': 10, 'nivel': 'aviso', 'fonte': 'alarme pedido no chat · avaliado neste aparelho', 'metricas': ms}


# ——————————————————————————————— SAÍDA ———————————————————————————————
def snapshot_dados():
    """O snapshot (L, §1.17). Com SIMULACAO = False o repositório público não leva a posição do barco (§4.3): sai a lat/lon do quadro e do gps."""
    if SIMULACAO:
        return SNAPSHOT
    s = dict(SNAPSHOT)
    s['quadro'] = {k: v for k, v in SNAPSHOT['quadro'].items() if k not in ('lat', 'lon')}
    s['gps'] = {k: v for k, v in SNAPSHOT['gps'].items() if k in ('satelites',)}
    return s


def dados():
    R, rota, campos = replay_dados()
    D = {
        'versao': REF.strftime('%d/%m/%Y'),
        'simulacao': SIMULACAO, 'demo': False,
        'embarcacao': EMBARCACAO, 'posicaoRef': POSICAO_REF, 'mar': MAR,
        'drive': {'raiz': DRIVE, 'pastas': PASTAS, 'arquivos': ARQ},
        'equipamentos': EQUIPAMENTOS, 'equipNota': EQUIP_NOTA, 'campos': campos,
        'snapshot': snapshot_dados(), 'consumo': CONSUMO, 'reserva': RESERVA, 'autonomia': autonomia(),
    }
    if SIMULACAO:   # §4.3: com SIMULACAO = False não há rota, destinos, histórico simulado nem dia de bordo, e o replay sai só com limites e alertas
        D.update({'destinos': destinos_dados(rota), 'rota': rota, 'replay': R, 'historico': historico_dados(),
                  'serie24v': serie24v_dados()})   # serie24v (L): o mín/máx sai do laço e do histórico simulados; sem simulação não há série (SEM DADOS)
    else:
        D['replay'] = {'limites': R['limites'], 'alertas': R['alertas']}
    D.update({
        'agenda': agenda_dados(), 'agendaFonte': AGENDA_FONTE, 'tarefasEquipe': tarefas_equipe_dados(),
        'documentos': documentos_dados(), 'docsFonte': DOCS_FONTE,
        'abastecimentos': abastecimentos_dados(), 'abastFonte': ARQ['abast'] + ' · ' + DRIVE + ' › ' + PASTAS['abast'], 'regraAbast': REGRA_ABAST,
        'diario': diario_dados(), 'diarioFonte': ARQ['diario'] + ' · ' + DRIVE + ' › ' + PASTAS['diario'],
        'equipe': EQUIPE,
        'faq': faq(), 'guias': FONTE_GUIA,
        'protocolos': PROTOCOLOS,
        'checklists': checklists_dados(), 'sensores': sensores_dados(), 'pecas': [dict(p) for p in PECAS], 'alarmesPedidos': alarmes_pedidos_dados(),   # C10: nos dois modos
    })
    return D


def serializa(v, nivel=0):
    """Serializador compacto (§1.0): dicionários indentados até a profundidade 2, listas e o resto numa linha, chaves na ordem
    do código e float pelo repr do Python. NaN e infinito não saem (allow_nan=False)."""
    if isinstance(v, dict) and v and nivel < 2:
        pad = ' ' * (nivel + 1)
        itens = [pad + json.dumps(k, ensure_ascii=False) + ': ' + serializa(x, nivel + 1) for k, x in v.items()]
        return '{\n' + ',\n'.join(itens) + '\n' + ' ' * nivel + '}'
    return json.dumps(v, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def rodape():
    """O rodapé do capitao-dados.js (CapitaoAgora, §1.23 e §4.1), anexado sem mudança: ferramentas/demo/rodape.js."""
    with open(os.path.join(AQUI, 'rodape.js'), encoding='utf-8', newline='') as f:
        return f.read().replace('\r\n', '\n')


def gera_js(D):
    cab = ('/* Capitão IA — dados da embarcação (GERADO por ferramentas/demo/gerar_demo.py — não editar à mão).\n'
           '   Cada grupo traz a fonte (arquivo no ' + DRIVE + '). Na leitura, null = SEM DADOS (ou SEM LEITURA, em sensor). */\n')
    corpo = serializa(D).replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')   # separadores de linha quebram JS antigo
    return cab + 'window.CapitaoDados = ' + corpo + ';\n' + rodape()


def base_conhecimento():
    """CONTRATO §1.5: {versao, aviso, trechos}. A versao são os 8 primeiros hex do sha256 do conteúdo (aviso + trechos, pelo
    serializa(), sem a própria versao): muda quando o texto muda, nunca com a data, e não depende do relógio do sistema."""
    corpo = {
        'aviso': ('Trechos dos guias de bordo da embarcação ' + EMBARCACAO['nome'] + ' (' + DRIVE + '). Sem documentos pessoais, '
                  'fiscais ou contratuais.'),
        'trechos': trechos(),
    }
    return dict({'versao': hashlib.sha256(serializa(corpo).encode('utf-8')).hexdigest()[:8]}, **corpo)


def gera_base(B=None):
    return serializa(base_conhecimento() if B is None else B) + '\n'


def saidas(D, B, Q=None):
    """Arquivos da raiz: caminho relativo → texto. Q = o FAQ dos equipamentos (None: o de hoje, calculado com a base B)."""
    return {'capitao-dados.js': gera_js(D), 'base-conhecimento.json': gera_base(B),
            'faq-equipamentos.json': gera_faq(faq_equipamentos(B) if Q is None else Q)}


def dentro(caminho, pasta):
    caminho, pasta = os.path.normcase(caminho), os.path.normcase(pasta)
    return caminho == pasta or caminho.startswith(pasta.rstrip(os.sep) + os.sep)


def chave_rel(rel):
    """Caminho relativo comparável: barras '/' e NFC (o macOS antigo devolve os nomes acentuados em NFD)."""
    return unicodedata.normalize('NFC', rel.replace(os.sep, '/'))


def eh_link(caminho):
    """Link simbólico ou junção do Windows (sem seguir): é link mesmo quando o alvo não existe mais."""
    return os.path.islink(caminho) or getattr(os.path, 'isjunction', lambda p: False)(caminho)


def sem_link(saida, rel_pasta):
    """SystemExit se algum componente de <saida>/<rel_pasta>, a partir da pasta de saída, for link (aponte para onde apontar,
    inclusive para dentro da própria saída). A pasta de saída em si é escolha de quem chama (--saida) e entra pelo realpath;
    dali para baixo nenhum link é seguido: um link no caminho levaria a gravação, ou a limpeza, para outro lugar da saída
    (fontes -> ../.. apagava o capitao-dados.js recém-gravado) ou para fora dela."""
    if os.path.isabs(rel_pasta):
        raise SystemExit('gerador: %s sairia da pasta de saída; nada foi gravado' % rel_pasta)
    base = os.path.realpath(saida)
    atual = base
    for parte in os.path.normpath(rel_pasta).split(os.sep):
        if parte in ('', os.curdir):
            continue
        if parte == os.pardir:
            raise SystemExit('gerador: %s sairia da pasta de saída; nada foi gravado' % rel_pasta)
        atual = os.path.join(atual, parte)
        if eh_link(atual):
            raise SystemExit('gerador: %s é um link no caminho de %s; nada foi gravado nem apagado' % (os.path.relpath(atual, base), rel_pasta))
        if not os.path.lexists(atual):
            return   # o resto ainda não existe: não há o que seguir


def alvo(saida, rel):
    """<saida>/<rel>, ou SystemExit se a pasta dele tiver link em algum componente (sem_link) ou, pelo realpath, sair da
    pasta de saída. O próprio arquivo pode ser um link: escreve() o troca por arquivo, sem gravar no alvo do link."""
    caminho = os.path.join(saida, rel)
    sem_link(saida, os.path.dirname(rel))
    if not dentro(os.path.realpath(os.path.dirname(caminho)), os.path.realpath(saida)):
        raise SystemExit('gerador: %s sairia da pasta de saída; nada foi gravado' % rel)
    if os.path.isdir(caminho) and not eh_link(caminho):
        raise SystemExit('gerador: %s é uma pasta, não um arquivo; nada foi gravado' % rel)
    return caminho


def escreve(saida, rel, texto):
    """Grava <saida>/<rel>; nunca fora da pasta de saída nem por um link de pasta (alvo(), conferido antes de criar qualquer
    pasta) e nunca através de um link: um link no lugar do arquivo é apagado (o alvo fica intacto) e vira arquivo."""
    caminho = alvo(saida, rel)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    if eh_link(caminho):
        apaga_entrada(caminho)
    with open(caminho, 'w', encoding='utf-8', newline='\n') as f:
        f.write(texto)


def apaga_entrada(cam):
    """Apaga o arquivo ou o link (nunca o alvo). No Windows, link de pasta só sai com rmdir."""
    try:
        os.unlink(cam)
    except OSError:
        if not os.path.islink(cam):
            raise
        os.rmdir(cam)


def limpa_fontes(saida, gerados):
    """Apaga em <saida>/ferramentas/demo/fontes/ só o que o gerador não gera mais. Recusa (SystemExit, nada apagado) se
    ferramentas/, demo/ ou fontes/ for link (sem_link): seguir o link apagaria o que estiver no alvo, inclusive o capitao-dados.js
    recém-gravado. Dentro de fontes/ nenhum link é seguido: um link velho vira só a entrada apagada, nunca o alvo; o caminho
    percorrido é conferido pelo realpath, e as pastas que ficarem vazias saem. Devolve os caminhos apagados (relativos a fontes/)."""
    sem_link(saida, FONTES_REL)
    raiz = os.path.join(os.path.realpath(saida), FONTES_REL)
    if not os.path.isdir(raiz):
        return []
    gerados = {chave_rel(g) for g in gerados}
    apagados = []
    for topo, pastas, arqs in os.walk(raiz, topdown=False, followlinks=False):
        if eh_link(topo) or os.path.normcase(os.path.realpath(topo)) != os.path.normcase(os.path.normpath(topo)):
            continue   # link no caminho (o walk não desce em link; o realpath pega também a junção do Windows): nunca percorrido
        for nome in sorted(arqs) + sorted(p for p in pastas if eh_link(os.path.join(topo, p))):
            cam = os.path.join(topo, nome)
            rel = chave_rel(os.path.relpath(cam, raiz))
            if rel not in gerados:
                apaga_entrada(cam)
                apagados.append(rel)
        for p in pastas:
            cam = os.path.join(topo, p)
            if not eh_link(cam) and os.path.isdir(cam) and not os.listdir(cam):
                os.rmdir(cam)
    return sorted(apagados)


def csv_txt(cab, linhas, sep=','):
    b = io.StringIO()
    w = csv.writer(b, lineterminator='\n', delimiter=sep)
    w.writerow(cab)
    for l in linhas:
        w.writerow(['' if v is None else v for v in l])
    return b.getvalue()


def sd(v):
    return 'SEM DADOS' if v is None else v


def limite_h(t):
    """'450 h' · '1.300 h' (milhar do pt-BR): um número solto logo depois do prazo (",24,1300") casaria a regex de coordenada da COORD_TEXTO."""
    h = t.get('horas')
    return ('{:,}'.format(h['limite']).replace(',', '.') + ' h') if h else None


COL_DIA_BORDO = 'Dia de bordo (0 = hoje; o dia de bordo começa às 07:00)'   # cabeçalho dos CSV do diário e do abastecimento (§5)


def gera_fontes(D):
    F = {}
    # g_vhf reaproveita o título/arquivo-fonte de g_eletronicos (mesmo manual; só o agrupamento do FAQ é separado, em FAQ_GUIAS):
    # acrescenta as seções ao <h1> que o primeiro guia daquele arquivo já abriu, em vez de sobrescrever (senão um dos dois
    # guias desaparece deste export, embora base-conhecimento.json/faq-equipamentos.json não tenham esse problema).
    guias_html = {}
    for k, g in GUIAS.items():
        chave = PASTAS[g['pasta']] + '/' + g['titulo'] + '.html'
        if chave not in guias_html:
            guias_html[chave] = ['<h1>' + g['titulo'] + '</h1>', '<p><b>' + g['equip'] + '</b></p>', '<p><i>' + g.get('nota', NOTA_GUIA) + '</i></p>']
        for sec, txt in g['secoes']:
            guias_html[chave].append('<h2>' + sec + '</h2><p>' + txt + '</p>')
    for chave, h in guias_html.items():
        F[chave] = '\n'.join(h)
    F[PASTAS['manuais'] + '/' + ARQ['inventario'] + '.csv'] = csv_txt(   # o inventário é a fonte da tela Equipamentos (§1.4)
        ['Equipamento', 'Fabricante', 'Modelo', 'Quantidade', 'Lados', 'Guia de bordo'],
        [[e['nome'], sd(e['fabricante']), sd(e['modelo']), e['qtd'], e.get('lados'), FONTE_GUIA.get(e['guia'], 'SEM DADOS')] for e in EQUIPAMENTOS])
    # Fontes com prazos relativos (§5): nenhuma data absoluta (o app mostra datas recalculadas para hoje e cita estes arquivos como
    # "Fonte:"; uma planilha com as datas da REF contaria outra história) e nenhuma coluna de situação (quem calcula é o app).
    F[PASTAS['docs'] + '/' + ARQ['documentos'] + '.csv'] = csv_txt(
        ['Documento', 'Categoria', 'Emitido há (dias)', 'Vence em (dias, contados de hoje no app)', 'Número', 'Observação'],
        [[x['n'], x['cat'], x.get('emitidoHa'), x.get('venceEm'), x.get('numero'), x['nota']] for x in DOCUMENTOS])
    F[PASTAS['agenda'] + '/' + ARQ['agenda'] + '.csv'] = csv_txt(
        ['Tarefa', 'Equipamento', 'Responsável', 'Intervalo', 'Última (há N dias)', 'Vence em (dias; negativo = atrasada)', 'Limite de horas'],
        [[t['t'], t['equip'], t['quem'], t['intervalo'], t['ultimaHa'], t['venceEm'], limite_h(t)] for t in AGENDA])
    R = D.get('replay') or {}
    bordo = R.get('diaDeBordo') or {}
    F[PASTAS['diario'] + '/' + ARQ['diario'] + '.csv'] = csv_txt(   # as linhas do dia de bordo (0) e depois o diário fixo
        [COL_DIA_BORDO, 'Hora', 'Sistema', 'Registro', 'Quem', 'Pendência'],
        [[e['diasAtras'], e['h'], e['sys'], e['t'], e['who'], 'ABERTA' if e['pend'] else ''] for e in list(bordo.get('diario') or []) + DIARIO])
    ab = bordo.get('abastecimento')
    F[PASTAS['abast'] + '/' + ARQ['abast'] + '.csv'] = csv_txt(   # um por dia de bordo (0, 1 e 2): a lista que a microtarefa do rodapé monta
        [COL_DIA_BORDO, 'Hora', 'Litros', 'Combustível', 'Local', 'Nível depois (%)', 'Situação', 'Observação'],
        # pt-BR nos dois números: litros «1.086» e nível «97,5» (o csv_txt cita o que tem vírgula); o nível cru saía «97.5» ao lado de «1.086»
        [[k, ab['h'], br(ab['litros']), ab['combustivel'], ab['local'], num_br(ab['nivelDepois'], 1), ab['st'], ab['nota']] for k in range(bordo.get('dias', 0))] if ab else [])
    s = snapshot_dados()   # não o SNAPSHOT cru: com SIMULACAO = False a leitura da pasta 05 também sai sem lat/lon (§4.3; é arquivo do repositório público)
    pos = {'lat': s['gps']['lat'], 'lon': s['gps']['lon']} if 'lat' in s['gps'] else {}
    F[PASTAS['tele'] + '/' + ARQ['snapshot']] = json.dumps({
        'timestamp_utc': '2026-09-26T13:12:00Z', **pos, 'sog_nos': s['sog'],
        'proa_graus': s['proa'], 'gps_satelites': s['gps']['satelites'], 'profundidade_m': s['profundidade'],
        'vento_verdadeiro_nos': s['vento'], 'vento_verdadeiro_angulo': s['ventoDe'], 'pressao_barometrica_hpa': s['pressao'],
        'temp_ar_externo_c': s['ar'], 'temp_agua_c': s['agua'], 'tanque_agua_pct': s['tanques']['agua'],
        'tanque_cinzas_pct': s['tanques']['cinzas'], 'tanque_negras_pct': s['tanques']['negras'],
        'bateria_0_tensao_v': s['bat24'], 'bateria_2_tensao_v': s['bat12'], 'seakeeper_ativo': True,
        'seakeeper_volante_rpm': s['seakeeper']['volante_rpm'], 'seakeeper_volante_pct': s['seakeeper']['volante_pct'],
        'motores_ultima_leitura_ligados': {'hora_local': '2026-09-26T09:31:00-03:00', 'rpm': s['motores']['rpm'], 'oleo_bar': s['motores']['oleo'],
                                           'arrefecimento_c': s['motores']['arref'], 'horimetro_h': s['motores']['horimetro'],
                                           'diesel_pct': [s['diesel']['bb'], s['diesel']['be']]},
        'gerador_horimetro_h': s['gerador']['horas'],
    }, ensure_ascii=False, indent=1) + '\n'
    if R.get('chaves'):   # a série de 150 s do laço (sem data e sem posição) e o formato do quadro, ambos a partir do D.campos (§1.15, §6.2 C8)
        C_ = D['campos']
        cols = [c for c in C_ if c in R['chaves']]
        Q = [quadro_laco(R, C_, t) for t in range(R['duracao'])]
        # Ponto e vírgula e vírgula decimal (o CSV do pt-BR): com vírgula entre as colunas, um número curto seguido de um inteiro de 4 dígitos
        # («5.7,8429») casaria a regex de coordenada da COORD_TEXTO.
        F[PASTAS['tele'] + '/' + ARQ['serie']] = csv_txt(
            ['t_s'] + cols, [[t] + [('%.*f' % (C_[c].get('casas', 0), Q[t][c])).replace('.', ',') for c in cols] for t in range(R['duracao'])], sep=';')
        F[PASTAS['tele'] + '/' + ARQ['formato']] = csv_txt(
            ['Campo', 'Rótulo', 'Unidade', 'Casas decimais', 'Contador', 'Observação'],   # sem a coluna Origem: é a taxonomia interna do gerador (laço, rota, janela…), não do coletor
            [[c, d['rotulo'], d.get('un'), d.get('casas'), {1: 'sobe', -1: 'desce'}.get(d.get('sentido')),
              d.get('desc') or ('ângulo de 0 a 360 graus' if d.get('ang') else None)] for c, d in C_.items()])
    F[ARQ['leiame'] + '.html'] = '\n'.join([
        '<h1>' + ARQ['leiame'] + '</h1>',
        '<p>Esta pasta é a fonte de dados do app Capitão IA (site estático): guias de bordo, '
        'documentos, agenda de manutenção, diário, telemetria, abastecimento e protocolos de emergência. Cada resposta do app cita o '
        'arquivo daqui de onde veio o dado.</p>',
        '<h2>Pastas</h2><ul>' + ''.join('<li><b>' + v + '</b></li>' for v in PASTAS.values()) + '</ul>',
        '<h2>Regras</h2><ul><li>Procedimentos de emergência: ' + PROTOCOLOS['rotulo'] + ' (pasta ' + PASTAS['protocolos'] + ').</li>'
        '<li>Datas relativas: o app conta os prazos a partir de hoje e o diário a partir do dia de bordo, que começa às 07:00.</li>'
        '<li>Não publicar contratos, notas fiscais, título de propriedade, CPF/CNPJ, telefones, e-mails, valores, nomes de terceiros, chaves ou link público de arquivo com a posição do barco.</li>'
        '<li>Esta pasta é privada. Não compartilhar por link público.</li></ul>',
        '<p>Gerado por ferramentas/demo/gerar_demo.py (repositório wonderboat-ai/CapitaoIA_v2).</p>',
    ])
    return F


def main(argv=None):
    ap = argparse.ArgumentParser(description='Gera capitao-dados.js, base-conhecimento.json, faq-equipamentos.json e as fontes do Drive.')
    ap.add_argument('--saida', default=RAIZ, help='pasta onde gravar (padrão: a raiz do repositório)')
    ap.add_argument('--detalhe', action='store_true', help='lista cada violação, com o commit da pendência ou [NOVA]')
    a = ap.parse_args(argv)
    for s in (sys.stdout, sys.stderr):   # console do Windows sem -X utf8: um "≠" vira escape em vez de derrubar o gerador
        try:
            s.reconfigure(errors='backslashreplace')
        except (AttributeError, ValueError):
            pass
    saida = os.path.abspath(a.saida)
    D = dados()
    B = base_conhecimento()
    Q = faq_equipamentos(B)
    F = gera_fontes(D)
    try:
        S = saidas(D, B, Q)
    except ValueError as e:   # serializa() recusa NaN e infinito: nada é gravado
        print('gerador: valor não finito no D ou na base (%s); nada foi gravado' % e, file=sys.stderr)
        return 1
    try:   # antes de gravar: com uma asserção falhando (a varredura de termos também, desde o C12), nada sai
        confere(D, B, F, S, Q, const={'NOTA_ETIQUETA': NOTA_ETIQUETA, 'DIAS_MESES': DIAS_MESES, 'LIMITES': LIMITES}, detalhe=a.detalhe)
    except ConfereFalhou as e:
        print(e, file=sys.stderr)
        return 1
    grava = list(S.items()) + [(os.path.join(FONTES_REL, rel), txt) for rel, txt in F.items()]
    for rel, _ in grava:   # todos os caminhos conferidos antes do 1º arquivo: um link para fora não deixa gravação pela metade
        alvo(saida, rel)
    for rel, txt in grava:
        escreve(saida, rel, txt)
    apagados = limpa_fontes(saida, F)
    au = autonomia()
    print('capitao-dados.js · base-conhecimento.json (%d trechos) · faq-equipamentos.json (%d itens) · %d fontes em %s'
          % (len(B['trechos']), Q['total'], len(F), FONTES_REL.replace(os.sep, '/')))
    for rel in apagados:   # na raiz do repositório: tirar com git rm (ou git add -A) no mesmo commit
        print('  apagada (não é mais gerada): fontes/' + rel)
    print('agenda: %d tarefas, %d atrasadas · autonomia %.1f h / %d mn' % (len(D['agenda']), sum(1 for t in D['agenda'] if t['dn'] < 0), au['horas'], au['mn']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
