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
também para a varredura de termos (as 8 regex do termos.json; a única exceção é o campo embarcacao.mmsiNota, até a 1b). Opcionais, só com contagens: CAPITAO_LISTAS_PRIVADAS (pasta com valores.txt e
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
    'mmsiNota': 'fictício · demonstração',   # sai na 1b (a F3 passa a ler protocolos.mmsiRotulo e protocolos.mmsiRadio)
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
        'titulo': ARQ['g_motores'], 'pasta': 'manuais', 'equip': equip_de('motores'), 'seg': {'4'},
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
        ],
    },
    'g_gerador': {
        'titulo': ARQ['g_gerador'], 'pasta': 'manuais', 'equip': equip_de('gerador'),
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
        ],
    },
    'g_eletrico': {
        'titulo': ARQ['g_eletrico'], 'pasta': 'manuais', 'equip': equip_de('eletrico'),
        'secoes': [
            ('1 · Bancos', 'Oito baterias AGM de 12 V em três bancos: serviço de 24 V (4), partida dos motores de 24 V (2) e banco de 12 V (2 em paralelo), que alimenta a eletrônica de 12 V e o estabilizador. O carregador de bordo repõe os três bancos.'),
            ('2 · Faixas', texto_faixas_baterias()),
            ('3 · Verificação', 'Confira as tensões no painel e na telemetria antes de sair. Bornes limpos e apertados; verificação dos bancos e das conexões a cada 6 meses, conforme a agenda de manutenção.'),
        ],
    },
    'g_dessalinizador': {
        'titulo': ARQ['g_dessalinizador'], 'pasta': 'manuais', 'equip': equip_de('dessalinizador'),
        'secoes': [
            ('1 · Ligar', 'Abra a válvula de fundo do dessalinizador e confira o pré-filtro limpo. Ligue pelo painel do dessalinizador, com o banco de serviço carregado; a pressão sobe sozinha.'),
            ('2 · Produção', 'Produção nominal: %s L/h. Descarte a água dos primeiros minutos depois de ligar e confira a salinidade no painel antes de mandar a água para o tanque.' % br(_eq('dessalinizador')['nominal']['lph'])),
            ('3 · Desligar e lavar', 'Desligue pelo painel: o ciclo termina com a lavagem com água doce. Feche a válvula de fundo se o barco for ficar parado.'),
            ('4 · Manutenção', 'Pré-filtros: troca conforme a agenda de manutenção. Barco parado por muito tempo: conservação da membrana pelo técnico de bordo.'),
        ],
    },
    'g_porao': {
        'titulo': ARQ['g_porao'], 'pasta': 'manuais', 'equip': equip_de('porao'), 'seg': {'4'},
        'secoes': [
            ('1 · Funcionamento', 'Duas bombas automáticas de 24 V, uma em BB e outra em BE, cada uma com sensor de nível. O painel mostra o nível do poço e conta os ciclos de cada bomba.'),
            ('2 · Faixas', texto_faixas_porao()),
            ('3 · Teste mensal', 'Uma vez por mês, acione cada bomba no manual, confira a saída pelo casco e o alarme do painel e registre o teste no diário.'),
            ('4 · Água entrando', TXT_ALAGAMENTO[0]),
        ],
    },
    'g_ancora': {
        'titulo': ARQ['g_ancora'], 'pasta': 'manuais', 'equip': equip_de('ancora'),
        'secoes': [
            ('1 · Lançar', 'Com o barco parado sobre o ponto escolhido, lance pelo controle do guincho e dê ré devagar até a âncora unhar. Lance de %s vezes a profundidade.' % de_a(LANCE_ANCORA_VEZES)),
            ('2 · Contador de corrente', 'O contador mostra os metros de corrente lançados no controle do guincho. Confira a marca antes de ativar o alarme de âncora no plotter.'),
            ('3 · Recolher e travar', 'Recolha devagar, com o motor aliviando a corrente. Com a âncora no lugar, trave a corrente e desligue o guincho no disjuntor.'),
            ('4 · Manutenção', 'Lave o guincho com água doce depois do uso e confira a corrente e o destorcedor uma vez por ano.'),
        ],
    },
    'g_piloto': {
        'titulo': ARQ['g_piloto'], 'pasta': 'manuais', 'equip': equip_de('piloto'),
        'secoes': [
            ('1 · Engatar', 'Engate o piloto no controle do posto de comando, com o rumo conferido no plotter e área livre à frente.'),
            ('2 · Espera ao manobrar', 'Em manobra, na marina e diante de qualquer risco a bordo, deixe o piloto em espera (standby).'),
            ('3 · Assumir no timão', 'Para assumir, aperte espera e governe pelo timão. O piloto comanda a direção hidráulica por uma bomba própria.'),
            ('4 · Alarmes', 'Alarme de desvio de rumo ou da direção: assuma no timão, ponha em espera e confira o rumo no plotter. Registre no diário com a hora.'),
        ],
    },
    'g_radar': {
        'titulo': ARQ['g_radar'], 'pasta': 'manuais', 'equip': equip_de('radar'),
        'secoes': [
            ('1 · Ligar e transmitir', 'Ligue o radar pelo plotter e espere o aquecimento; depois toque em transmitir. Na marina, deixe em espera.'),
            ('2 · Zona de guarda', 'Defina a zona de guarda em volta do barco: o plotter avisa quando um alvo entra nela.'),
            ('3 · Neblina e noite', 'Com neblina ou à noite, mantenha o radar transmitindo, reduza a velocidade e confira os alvos com o AIS no plotter.'),
            ('4 · Segurança', 'Não fique perto do domo com o radar transmitindo e não abra o domo com ele ligado.'),
        ],
    },
    'g_ais': {
        'titulo': ARQ['g_ais'], 'pasta': 'manuais', 'equip': equip_de('ais'), 'seg': {'2'},
        'secoes': [
            ('1 · Alvos no plotter', 'Os alvos do AIS aparecem no plotter com nome, rumo e velocidade. Toque no alvo para ver a menor distância de passagem prevista.'),
            ('2 · Identificação', 'O AIS transmite a identificação programada no transponder; o MMSI é o do rádio de bordo (etiqueta / Licença de Estação).'),
            ('3 · Modo silencioso', 'No modo silencioso o transponder só recebe e não transmite a posição do barco. Use só quando necessário e volte a transmitir ao sair.'),
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
FAQ_GUIAS = (('MO', 'g_motores'), ('GE', 'g_gerador'), ('SK', 'g_seakeeper'), ('CL', 'g_clima'), ('EL', 'g_eletronicos'), ('EE', 'g_eletrico'),
             ('DS', 'g_dessalinizador'), ('PO', 'g_porao'), ('AN', 'g_ancora'), ('PI', 'g_piloto'), ('RA', 'g_radar'), ('AI', 'g_ais'),
             ('SF', 'g_seafire'), ('EP', 'g_epirb'), ('CK', 'checklist'))
# Os 9 cartões: EM-n ↔ a seção do protocolo (a ordem do contrato, não a da base: o EPIRB vem depois de abandono).
FAQ_EM = (('EM-01', 'MAYDAY · canal 16'), ('EM-02', 'PAN-PAN'), ('EM-03', 'DSC'), ('EM-04', 'Homem ao mar'), ('EM-05', 'Incêndio · Seafire'),
          ('EM-06', 'Água entrando'), ('EM-07', 'Abandono'), ('EM-08', 'EPIRB'), ('EM-09', 'Salvatagem'))
FAQ_SECOES = (('Emergência', ('EM',)), ('Motores', ('MO',)), ('Gerador e energia', ('GE', 'EE')), ('Estabilizador', ('SK',)),
              ('Climatização, água e porão', ('CL', 'DS', 'PO')), ('Eletrônicos e rádios', ('EL',)),
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
    # ——— Sistema elétrico ———
    'EE-01': _f('Bancos de baterias', 'Quantas baterias tem o barco e como estão ligadas?',
                ['bancos de 24 V e 12 V', 'banco de partida dos motores', 'carregador de bordo'], [0, 1], p=[], ver=('EE-02', 'SK-01')),
    'EE-02': _f('Faixas de tensão das baterias', 'Qual a tensão normal dos bancos de baterias?',
                ['tensão baixa nas baterias', 'faixa do banco de 12 V', 'banco de serviço de 24 V'], [0, 1], p=[], se=2, ver=('EE-03', 'CK-01')),
    'EE-03': _f('Verificação das baterias', 'Quando verifico as baterias?',
                ['conferir as tensões antes de sair', 'bornes das baterias', 'verificação dos bancos a cada 6 meses'], [0, 1], p=[]),
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
    # ——— Bombas de porão ———
    'PO-01': _f('Como funcionam as bombas de porão', 'As bombas de porão ligam sozinhas?',
                ['sensor de nível do porão', 'ciclos das bombas de porão', 'bombas automáticas de BB e BE'], [0, 1], p=[], ver=('PO-02', 'PO-03')),
    'PO-02': _f('Nível normal do porão', 'Qual o nível normal de água no porão?',
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
    # ——— AIS ———
    'AI-01': _f('Alvos do AIS no plotter', 'Como vejo os outros barcos pelo AIS?',
                ['alvos do AIS', 'distância de passagem prevista', 'nome, rumo e velocidade dos alvos'], [0], p=[1]),
    'AI-02': _f('Identificação do AIS', 'Que identificação o AIS transmite?',
                ['MMSI do AIS', 'transponder classe B', 'identificação do barco no AIS'], [0], p=[]),
    'AI-03': _f('AIS em modo silencioso', 'O que faz o modo silencioso do AIS?',
                ['transponder só recebendo', 'AIS sem transmitir a posição', 'voltar a transmitir o AIS'], [0, 1], p=[], at=1),
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
                ['sistema fixo descarregou', 'quando abrir o acesso ao motor', 'recarga do sistema fixo'],
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
    for k, g in GUIAS.items():
        h = ['<h1>' + g['titulo'] + '</h1>', '<p><b>' + g['equip'] + '</b></p>', '<p><i>' + g.get('nota', NOTA_GUIA) + '</i></p>']
        for sec, txt in g['secoes']:
            h.append('<h2>' + sec + '</h2><p>' + txt + '</p>')
        F[PASTAS[g['pasta']] + '/' + g['titulo'] + '.html'] = '\n'.join(h)
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
