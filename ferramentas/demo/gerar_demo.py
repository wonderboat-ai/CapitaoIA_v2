# -*- coding: utf-8 -*-
"""Capitão IA — gerador dos dados de DEMONSTRAÇÃO (fictícios).

Um lugar só para os dados da embarcação de demonstração. Gera:
  1. capitao-dados.js          (raiz)  → window.CapitaoDados, lido pelo cérebro e pelas telas
  2. base-conhecimento.json    (raiz)  → trechos dos guias de bordo, busca BM25 do chat e da voz
  3. ferramentas/demo/fontes/          → os mesmos dados como arquivos de origem (Docs/Planilhas/JSON) enviados ao
                                         Google Drive › "Capitão IA v2" (pastas 01–07)

REGRAS
- Tudo aqui é FICTÍCIO e vai rotulado "DEMO" (decisão do proprietário, 26/09/2026: demonstração da plataforma para
  clientes e modelo para as próximas embarcações).
- Continua SEM DADOS o que o proprietário não informou: modelo de cada equipamento, fabricante/modelo e registro do
  barco, Seafire e EPIRB (procedimento, localização, validade). None = SEM DADOS.
- Nada copiado da Avanti Vessel (nomes, registro, MMSI, IDs, leituras, valores).
- Sem valores em dinheiro, CPF/CNPJ, telefones, e-mails ou nomes de terceiros — nem na demonstração (a mesma regra
  vale para o barco real que vier depois).
- Procedimentos de emergência: "procedimento padrão — confirmar com o protocolo de bordo" (decisão do proprietário).

Para a próxima embarcação: trocar os dados abaixo pelos reais (com a fonte de cada um) e rodar
    python ferramentas/demo/gerar_demo.py
"""
import csv
import io
import json
import os
from datetime import date, datetime

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FONTES = os.path.join(os.path.dirname(__file__), 'fontes')

REF = date(2026, 9, 26)          # data do snapshot: prazos D-n contados a partir dela
DRIVE = 'Drive › Capitão IA v2'
SELO = 'DEMO · DADOS FICTÍCIOS'
AVISO = ('Demonstração da plataforma Capitão IA: embarcação, leituras, agenda, documentos, diário, abastecimentos e guias '
         'de bordo são fictícios. Procedimentos de emergência são o padrão internacional, a confirmar com o protocolo de '
         'bordo. Modelos dos equipamentos, registro, Seafire e EPIRB: SEM DADOS.')

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
    'leiame': 'LEIA-ME — Capitão IA v2 (DEMO)',
    'g_gerador': 'Guia de bordo (DEMO) — Gerador Onan',
    'g_seakeeper': 'Guia de bordo (DEMO) — Estabilizador Seakeeper',
    'g_clima': 'Guia de bordo (DEMO) — Climatização',
    'g_eletronicos': 'Guia de bordo (DEMO) — Eletrônicos Garmin, áudio Fusion e VHF 315',
    'g_motores': 'Guia de bordo (DEMO) — Motores Volvo Penta',
    'checklist': 'Checklist de saída e chegada (DEMO)',
    'inventario': 'Inventário de bordo (DEMO)',
    'documentos': 'Controle de documentos (DEMO)',
    'agenda': 'Agenda preditiva (DEMO)',
    'diario': 'Diário de bordo (DEMO)',
    'snapshot': 'snapshot_demo_20260926_1012.json',
    'abast': 'Registro de abastecimento (DEMO)',
    'protocolo': 'Protocolo de emergência — procedimento padrão',
}


def onde(chave_pasta, chave_arq):
    return DRIVE + ' › ' + PASTAS[chave_pasta] + ' › ' + ARQ[chave_arq]


def d(s):
    return datetime.strptime(s, '%d/%m/%Y').date()


def dn(s):
    return (d(s) - REF).days


def coord(v, pos, neg, g):
    a = abs(v)
    gr = int(a)
    mi = (a - gr) * 60
    gtxt = ('%03d' % gr) if g == 3 else str(gr)
    return gtxt + '°' + ('%05.2f' % mi).replace('.', ',') + "'" + (neg if v < 0 else pos)


# ——————————————————————————————— EMBARCAÇÃO ———————————————————————————————
EMBARCACAO = {
    'nome': 'Capitão IA',
    'modelo': None,            # SEM DADOS (proprietário, 26/09/2026)
    'registro': None,          # SEM DADOS
    'proprietario': 'Lucas Araújo',
    'base': 'Balneário Camboriú (SC)',
    'fuso': 'America/Sao_Paulo',
    'mmsi': '710123456',
    'mmsiNota': 'fictício · demonstração',
    'indicativo': None,        # SEM DADOS
    'fonte': 'dados informados pelo proprietário (26/09/2026) · MMSI fictício de demonstração',
}

# Posição de referência para clima e maré: centro de Balneário Camboriú (fonte real, não inventada)
POSICAO_REF = {
    'lat': -26.99056, 'lon': -48.63472,
    'nome': 'Balneário Camboriú (centro)',
    'fonte': 'Open-Meteo Geocoding (GeoNames 3471039)',
}
# Pontos de mar para a maré (a grade de 8 km do modelo de mar trata a costa como terra; a API usa a célula de mar mais próxima)
MAR = [[-26.99056, -48.63472], [-26.995, -48.60], [-27.0, -48.55]]

# ——————————————————————————————— EQUIPAMENTOS ———————————————————————————————
# Fabricantes informados pelo proprietário; modelos SEM DADOS (None).
EQUIPAMENTOS = [
    {'id': 'motores', 'nome': 'Motores', 'fabricante': 'Volvo Penta', 'modelo': None, 'qtd': '2', 'lados': 'BB e BE', 'guia': 'g_motores'},
    {'id': 'gerador', 'nome': 'Gerador', 'fabricante': 'Onan', 'modelo': None, 'qtd': '1', 'guia': 'g_gerador'},
    {'id': 'estabilizador', 'nome': 'Estabilizador giroscópico', 'fabricante': 'Seakeeper', 'modelo': None, 'qtd': '1', 'guia': 'g_seakeeper'},
    {'id': 'climatizacao', 'nome': 'Climatização', 'fabricante': None, 'modelo': None, 'qtd': 'SEM DADOS', 'guia': 'g_clima'},
    {'id': 'eletronicos', 'nome': 'Eletrônicos de navegação', 'fabricante': 'Garmin', 'modelo': None, 'qtd': 'SEM DADOS', 'guia': 'g_eletronicos'},
    {'id': 'audio', 'nome': 'Áudio', 'fabricante': 'Fusion', 'modelo': None, 'qtd': 'SEM DADOS', 'guia': 'g_eletronicos'},
    {'id': 'vhf', 'nome': 'Rádios VHF', 'fabricante': None, 'modelo': 'VHF 315', 'qtd': 'SEM DADOS', 'guia': 'g_eletronicos'},
    {'id': 'epirb', 'nome': 'EPIRB', 'fabricante': None, 'modelo': None, 'qtd': 'SEM DADOS', 'guia': None},
    {'id': 'seafire', 'nome': 'Sistema de incêndio', 'fabricante': 'Seafire', 'modelo': None, 'qtd': 'SEM DADOS', 'guia': None},
]
EQUIP_NOTA = 'Lista informada pelo proprietário (com "…": pode haver mais equipamentos). Modelos: SEM DADOS.'

# ——————————————————————————————— SNAPSHOT DO COLETOR (DEMO) ———————————————————————————————
GPS = {'lat': -26.9930, 'lon': -48.6140}
SNAPSHOT = {
    'quando': '26/09/2026 10:12', 'hora': '10:12', 'dia': '26/09', 'iso': '2026-09-26T10:12:00-03:00',
    'fonte': 'coletor NMEA (DEMO) · ' + ARQ['snapshot'],
    'estado': 'Fundeado', 'local': 'enseada de Balneário Camboriú',
    'gps': {'lat': GPS['lat'], 'lon': GPS['lon'], 'texto': coord(GPS['lat'], 'N', 'S', 2) + ' ' + coord(GPS['lon'], 'E', 'W', 3), 'satelites': 26},
    'sog': 0.1, 'proa': 71, 'profundidade': 7.4,
    'vento': 9.2, 'ventoDe': 58, 'pressao': 1017, 'ar': 22.6, 'agua': 20.1,
    'bat24': 27.42, 'bat12': 13.18,
    'tanques': {'agua': 68.5, 'cinzas': 21.0, 'negras': 34.5},
    'diesel': {'bb': 54.0, 'be': 52.0, 'litros': 848, 'capacidade': 1600, 'tanques': '2 × 800 L', 'hora': '26/09 09:31',
               'nota': 'última leitura com motores ligados'},
    'motores': {'hora': '26/09 09:31', 'estado': 'desligados desde 09:31', 'rpm': [700, 690], 'oleo': [3.4, 3.3],
                'arref': [79, 78], 'horimetro': [412.6, 409.8], 'marcha': 'neutro'},
    'gerador': {'estado': 'ligado desde 09:35', 'horas': 1236.4, 'hora': '26/09 10:12'},
    'seakeeper': {'estado': 'ligado', 'hora': '26/09 10:12'},
    'porao': None,    # SEM LEITURA: sem sensor de porão no barramento (DEMO)
    'ancora': None,   # SEM LEITURA: sem sensor de âncora
}
CONSUMO = {
    'cruzeiro': {'nos': 18, 'rpm': 2050, 'lph': 68}, 'lenta': {'lph': 6.2},
    'periodo': '01/08–26/09/2026', 'fonte': 'telemetria (DEMO) · taxa de combustível dos dois motores',
    'desdeAbast': {'litros': 192, 'desde': '12/09/2026', 'horas': '2,8 h de motor por lado'},
}
RESERVA = 0.10


def autonomia():
    litros = SNAPSHOT['diesel']['litros']
    h = litros * (1 - RESERVA) / CONSUMO['cruzeiro']['lph']
    return {'horas': round(h, 1), 'mn': int(round(h * CONSUMO['cruzeiro']['nos'])),
            'lenta': int(round(litros * (1 - RESERVA) / CONSUMO['lenta']['lph']))}


# Série 24 V · 7 dias (DEMO): mín/máx por dia — única série de histórico carregada
SERIE_24V = [
    {'d': '20/09', 'min': 26.1, 'max': 28.4}, {'d': '21/09', 'min': 26.0, 'max': 28.6}, {'d': '22/09', 'min': 25.9, 'max': 27.2},
    {'d': '23/09', 'min': 25.8, 'max': 27.0}, {'d': '24/09', 'min': 25.7, 'max': 28.5}, {'d': '25/09', 'min': 25.9, 'max': 27.1},
    {'d': '26/09', 'min': 26.0, 'max': 27.4},
]

# ——————————————————————————————— AGENDA PREDITIVA (DEMO) ———————————————————————————————
AGENDA = [
    {'id': 'clima-filtro', 't': 'Limpeza do filtro de água salgada da climatização', 'equip': 'Climatização (fabricante SEM DADOS)', 'quem': 'marina', 'intervalo': 'mensal', 'ultima': '10/08/2026', 'vence': '10/09/2026'},
    {'id': 'porao-teste', 't': 'Teste das bombas de porão e alarmes', 'equip': 'Bombas de porão', 'quem': 'técnico', 'intervalo': 'mensal', 'ultima': '01/08/2026', 'vence': '01/09/2026'},
    {'id': 'gerador-rotor', 't': 'Inspeção do rotor (impeller) do gerador', 'equip': 'Gerador Onan', 'quem': 'técnico', 'intervalo': '12 meses', 'ultima': '24/09/2025', 'vence': '24/09/2026'},
    {'id': 'casco-anodos', 't': 'Limpeza de casco e troca de anodos', 'equip': 'Casco', 'quem': 'marina', 'intervalo': '6 meses', 'ultima': '05/04/2026', 'vence': '05/10/2026'},
    {'id': 'motores-oleo', 't': 'Troca de óleo e filtros dos motores', 'equip': 'Motores Volvo Penta', 'quem': 'oficina Volvo Penta', 'intervalo': '12 meses ou 450 h (o que vier antes)', 'ultima': '13/10/2025', 'vence': '13/10/2026', 'horas': {'limite': 450, 'atual': 412.6}},
    {'id': 'gerador-revisao', 't': 'Revisão do gerador: óleo e filtros', 'equip': 'Gerador Onan', 'quem': 'técnico', 'intervalo': '12 meses ou 1.300 h', 'ultima': '20/10/2025', 'vence': '20/10/2026', 'horas': {'limite': 1300, 'atual': 1236.4}},
    {'id': 'seakeeper-anodo', 't': 'Anodo do trocador de calor do estabilizador', 'equip': 'Estabilizador Seakeeper', 'quem': 'técnico', 'intervalo': '6 meses', 'ultima': '30/04/2026', 'vence': '31/10/2026'},
    {'id': 'baterias', 't': 'Verificação do banco de baterias e conexões', 'equip': 'Sistema elétrico 24 V / 12 V', 'quem': 'técnico', 'intervalo': '6 meses', 'ultima': '15/05/2026', 'vence': '15/11/2026'},
    {'id': 'garmin-cartas', 't': 'Atualização de cartas e software dos eletrônicos', 'equip': 'Eletrônicos Garmin', 'quem': 'Lucas', 'intervalo': '12 meses', 'ultima': '01/12/2025', 'vence': '01/12/2026'},
    {'id': 'clima-revisao', 't': 'Revisão anual da climatização', 'equip': 'Climatização (fabricante SEM DADOS)', 'quem': 'marina', 'intervalo': '12 meses', 'ultima': '21/12/2025', 'vence': '21/12/2026'},
    {'id': 'motores-revisao', 't': 'Revisão anual dos motores', 'equip': 'Motores Volvo Penta', 'quem': 'oficina Volvo Penta', 'intervalo': '12 meses', 'ultima': '16/01/2026', 'vence': '16/01/2027'},
]
AGENDA_FALTA = ['EPIRB: teste e validade da bateria — equipamento SEM DADOS',
                'Seafire: inspeção e validade da carga — SEM DADOS']


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


# ——————————————————————————————— DOCUMENTOS (DEMO) ———————————————————————————————
# Sem números de apólice/nota, sem valores, sem dados pessoais.
DOCUMENTOS = [
    {'n': 'Título de Inscrição da Embarcação (TIE)', 'cat': 'Registro', 'vence': None, 'st': 'SEM DADOS', 'nota': 'registro não informado'},
    {'n': 'Seguro da embarcação', 'cat': 'Seguro', 'vence': '15/10/2026', 'nota': 'apólice no Drive (DEMO)'},
    {'n': 'Licença de estação de rádio (VHF)', 'cat': 'Licenças', 'vence': '30/11/2026', 'nota': 'rádios VHF 315'},
    {'n': 'Laudo de vistoria anual', 'cat': 'Laudos', 'vence': '18/08/2027', 'nota': 'vistoria de 18/08/2026'},
    {'n': 'Garantia do estabilizador Seakeeper', 'cat': 'Garantias', 'vence': '20/03/2027', 'nota': 'modelo SEM DADOS'},
    {'n': 'Garantia dos eletrônicos Garmin', 'cat': 'Garantias', 'vence': '10/02/2027', 'nota': 'modelos SEM DADOS'},
    {'n': 'Certificado do EPIRB', 'cat': 'Segurança', 'vence': None, 'st': 'SEM DADOS', 'nota': 'EPIRB sem dados'},
    {'n': 'Nota fiscal de abastecimento · 12/09/2026', 'cat': 'Notas', 'vence': None, 'st': 'A CONFERIR', 'nota': 'foto no Drive (DEMO) · sem valores no app'},
]

# ——————————————————————————————— ABASTECIMENTOS (DEMO) ———————————————————————————————
ABASTECIMENTOS = [
    {'d': '12/09/2026', 'litros': 620, 'combustivel': 'diesel', 'local': 'posto da marina · Balneário Camboriú', 'st': 'CONFERIDO', 'nivelDepois': 65, 'nota': 'NF no Drive (DEMO)'},
    {'d': '02/08/2026', 'litros': 540, 'combustivel': 'diesel', 'local': 'posto da marina · Balneário Camboriú', 'st': 'CONFERIDO', 'nivelDepois': 71, 'nota': 'NF no Drive (DEMO)'},
]
REGRA_ABAST = 'abastecer antes de 25 % em qualquer tanque (regra de bordo DEMO)'

# ——————————————————————————————— DIÁRIO DE BORDO (DEMO) ———————————————————————————————
DIARIO = [
    {'d': '26/09', 'h': '09:31', 'iso': '2026-09-26T09:31:00-03:00', 'sys': 'Navegação', 'tom': 'tele', 'who': 'Lucas', 'pend': False,
     't': 'Fundeado na enseada de Balneário Camboriú após 1 h 10 min de navegação. Motores desligados; gerador e Seakeeper ligados.'},
    {'d': '26/09', 'h': '08:20', 'iso': '2026-09-26T08:20:00-03:00', 'sys': 'Navegação', 'tom': 'tele', 'who': 'Lucas', 'pend': False,
     't': 'Saída da base com 4 pessoas a bordo. Checklist de saída feito; teste das bombas de porão continua pendente.'},
    {'d': '24/09', 'h': '17:10', 'iso': '2026-09-24T17:10:00-03:00', 'sys': 'Manutenção', 'tom': 'warn', 'who': 'técnico', 'pend': True,
     't': 'Inspeção do rotor do gerador não feita no prazo — reagendar.'},
    {'d': '20/09', 'h': '11:05', 'iso': '2026-09-20T11:05:00-03:00', 'sys': 'Equipamentos', 'tom': 'accent', 'who': 'Lucas', 'pend': True,
     't': 'Climatização da cabine de proa com fluxo fraco. Suspeita: filtro de água salgada sujo (limpeza atrasada).'},
    {'d': '12/09', 'h': '15:40', 'iso': '2026-09-12T15:40:00-03:00', 'sys': 'Combustível', 'tom': 'ok', 'who': 'Lucas', 'pend': False,
     't': 'Abastecimento de 620 L de diesel no posto da marina; tanques em ≈ 65 %. NF no Drive.'},
    {'d': '05/09', 'h': '10:00', 'iso': '2026-09-05T10:00:00-03:00', 'sys': 'Segurança', 'tom': 'crit', 'who': 'técnico', 'pend': True,
     't': 'Teste das bombas de porão adiado por chuva.'},
    {'d': '28/08', 'h': '16:25', 'iso': '2026-08-28T16:25:00-03:00', 'sys': 'Eletrônicos', 'tom': 'accent', 'who': 'Lucas', 'pend': False,
     't': 'Cartas do plotter Garmin desatualizadas; atualização entra na agenda de dezembro.'},
    {'d': '18/08', 'h': '09:00', 'iso': '2026-08-18T09:00:00-03:00', 'sys': 'Documentos', 'tom': 'ok', 'who': 'Lucas', 'pend': False,
     't': 'Vistoria anual feita; laudo arquivado no Drive.'},
]

# ——————————————————————————————— EQUIPE E APOIO ———————————————————————————————
EQUIPE = {
    'perfis': [{'id': 'lucas', 'nome': 'Lucas Araújo', 'ini': 'LA', 'papel': 'proprietário', 'acesso': 'total'}],
    'apoio': [  # papéis, sem nomes nem telefones de terceiros
        {'id': 'marina', 'papel': 'Marina da base', 'onde': 'Balneário Camboriú', 'para': 'casco, filtros, vaga'},
        {'id': 'oficina', 'papel': 'Oficina Volvo Penta', 'onde': 'SEM DADOS', 'para': 'motores'},
        {'id': 'tecnico', 'papel': 'Técnico de bordo', 'onde': 'SEM DADOS', 'para': 'gerador, Seakeeper, elétrica, porão'},
        {'id': 'posto', 'papel': 'Posto de combustível', 'onde': 'marina da base', 'para': 'diesel'},
    ],
    'nota': 'Telefones: A CADASTRAR em Equipe (ficam só no aparelho).',
}

# ——————————————————————————————— GUIAS DE BORDO (DEMO) → base de conhecimento ———————————————————————————————
# Orientação operacional genérica, escrita para a embarcação de demonstração. Não substitui o manual do fabricante:
# cada guia manda confirmar no manual (modelo SEM DADOS).
GUIAS = {
    'g_gerador': {
        'titulo': ARQ['g_gerador'], 'pasta': 'manuais', 'equip': 'Gerador Onan (modelo SEM DADOS)',
        'secoes': [
            ('1 · Antes de ligar', 'Com o gerador parado, confira o nível de óleo e o líquido de arrefecimento. Abra a válvula de fundo da entrada de água salgada e confira se o filtro de água salgada está limpo. Ligue a ventilação do compartimento por alguns minutos se houver cheiro de combustível.'),
            ('2 · Ligar', 'No painel do gerador, pressione e segure PARTIDA até o motor pegar. Aguarde a tensão e a frequência estabilizarem no painel. Só depois transfira as cargas no quadro elétrico, uma de cada vez; ligue a climatização por último.'),
            ('3 · Água no escapamento', 'Com o gerador ligado, confira a saída de água pelo escapamento. Sem água saindo, desligue na hora: é sinal de falta de refrigeração (válvula de fundo fechada, filtro entupido ou rotor danificado).'),
            ('4 · Desligar', 'Retire as cargas no quadro elétrico. Deixe o gerador funcionar de 3 a 5 minutos sem carga para esfriar e pressione PARADA. Feche a válvula de fundo se o barco for ficar parado por vários dias.'),
            ('5 · Alarme de alta temperatura', 'Desligue o gerador. Verifique a válvula de fundo, o filtro de água salgada e o rotor (impeller). Nunca abra a tampa do arrefecimento com o motor quente. Registre o alarme no diário.'),
            ('6 · Alarme de baixa pressão de óleo', 'Desligue o gerador e confira o nível de óleo com ele parado. Se o nível estiver correto e o alarme voltar, não religue: chame o técnico de bordo.'),
            ('7 · Manutenção na agenda', 'Óleo e filtros: 12 meses ou 1.300 h (o que vier antes). Rotor (impeller): inspeção a cada 12 meses. Os intervalos oficiais estão no manual do fabricante — modelo SEM DADOS: confirmar.'),
            ('8 · Horímetro', 'O horímetro aparece no painel do gerador e na telemetria. No snapshot de demonstração de 26/09/2026 10:12: 1.236,4 h, gerador ligado desde 09:35.'),
        ],
    },
    'g_seakeeper': {
        'titulo': ARQ['g_seakeeper'], 'pasta': 'manuais', 'equip': 'Estabilizador Seakeeper (modelo SEM DADOS)',
        'secoes': [
            ('1 · Energia', 'O estabilizador precisa de energia AC para acelerar o volante: gerador ligado ou tomada do cais. Sem AC, o display avisa e o volante não acelera.'),
            ('2 · Ligar antes de sair', 'Ligue pelo display com antecedência: a estabilização só começa quando o volante chega à rotação de operação e o display indica pronto. O tempo de aceleração depende do modelo — SEM DADOS neste guia.'),
            ('3 · Estabilizar', 'O botão de estabilização liga e desliga o efeito sem parar o volante. Em manobra de marina, deixe a estabilização desligada se o display recomendar.'),
            ('4 · Desligar ao atracar', 'Desligue pelo display. O volante continua girando por muito tempo depois de desligado; mantenha a energia até o display indicar que parou.'),
            ('5 · Segurança', 'Nunca abra tampas nem faça manutenção com o volante girando. Confira no display que a rotação está em zero antes de qualquer serviço.'),
            ('6 · Alarmes', 'Anote o código mostrado no display e registre no diário com a hora. A tabela de códigos está no manual do fabricante — MANUAL NO DRIVE (não carregado na demonstração).'),
            ('7 · Manutenção na agenda', 'Anodo do trocador de calor: a cada 6 meses (agenda de demonstração). Outros itens: manual do fabricante, modelo SEM DADOS.'),
        ],
    },
    'g_clima': {
        'titulo': ARQ['g_clima'], 'pasta': 'manuais', 'equip': 'Climatização (fabricante e modelo SEM DADOS)',
        'secoes': [
            ('1 · Ligar', 'Confira a válvula de fundo aberta e o filtro de água salgada limpo. Com energia AC (gerador ou cais), ligue a bomba de água salgada no painel e depois o controle da cabine.'),
            ('2 · Modos e temperatura', 'No controle de cada cabine escolha frio, calor ou ventilação e ajuste a temperatura desejada. Com o gerador, ligue as cabines uma de cada vez.'),
            ('3 · Alarme de fluxo', 'Alarme de fluxo ou de alta pressão quase sempre é falta de água salgada: filtro sujo, válvula de fundo fechada ou bomba desligada. Desligue a unidade, limpe o filtro e religue.'),
            ('4 · Fluxo de ar fraco', 'Fluxo de ar fraco na cabine: limpe o filtro de ar da unidade daquela cabine. Se continuar, registre no diário e chame a marina.'),
            ('5 · Desligar', 'Desligue pelo controle das cabines e depois a bomba de água salgada. Ao deixar o barco, feche a válvula de fundo se a climatização não for usada.'),
            ('6 · Manutenção na agenda', 'Filtro de água salgada: limpeza mensal. Revisão anual pela marina. Fabricante e modelo SEM DADOS — confirmar intervalos no manual.'),
        ],
    },
    'g_eletronicos': {
        'titulo': ARQ['g_eletronicos'], 'pasta': 'manuais', 'equip': 'Eletrônicos Garmin · áudio Fusion · rádios VHF 315 (modelos SEM DADOS)',
        'secoes': [
            ('1 · Plotter Garmin: homem ao mar', 'Ao ver alguém cair na água, acione a função MOB do plotter Garmin: a posição fica marcada e o plotter mostra o rumo de volta. Veja também o protocolo de emergência.'),
            ('2 · Piloto automático', 'Deixe o piloto automático em espera (standby) antes de manobrar na marina e sempre que houver gente na água. Engate só em área livre, com a rota conferida no plotter.'),
            ('3 · Alarme de âncora', 'Ao fundear, ative o alarme de âncora no plotter e defina o raio conforme o cabo lançado e o espaço de giro. O barco não tem sensor de âncora: a posição do ferro fica SEM LEITURA.'),
            ('4 · Rádio VHF 315: escuta', 'Mantenha o canal 16 em escuta permanente. A dupla escuta acompanha o canal 16 e um canal de trabalho ao mesmo tempo.'),
            ('5 · Rádio VHF 315: DSC', 'O botão de socorro DSC (DISTRESS) só envia a identificação se o MMSI estiver programado no rádio. Na demonstração o MMSI 710123456 é fictício; no barco real, programe o MMSI do registro.'),
            ('6 · Áudio Fusion: Bluetooth', 'Para parear o celular: escolha a fonte Bluetooth no controle Fusion, deixe o aparelho visível e selecione o Fusion na lista de Bluetooth do celular. O volume é ajustado por zona.'),
            ('7 · Atualizações', 'Cartas e software dos eletrônicos Garmin: atualização anual (agenda de demonstração, dezembro).'),
        ],
    },
    'g_motores': {
        'titulo': ARQ['g_motores'], 'pasta': 'manuais', 'equip': 'Motores Volvo Penta (modelo SEM DADOS)',
        'secoes': [
            ('1 · Antes da partida', 'Com os motores parados e frios: nível de óleo, líquido de arrefecimento, correias, válvulas de fundo abertas, porão seco e ventilação do compartimento ligada por alguns minutos.'),
            ('2 · Partida', 'Dê a partida pelo painel. Logo depois confira a saída de água pelo escapamento e a pressão de óleo no painel dos dois motores.'),
            ('3 · Aquecimento', 'Deixe alguns minutos em marcha lenta antes de acelerar. Evite rotação alta com o motor frio.'),
            ('4 · Pressão de óleo baixa', 'Se a pressão de óleo cair ou o alarme acender: reduza para marcha lenta e observe; compare BB e BE no mesmo giro (só um lado baixo aponta o motor); com o motor parado, procure vazamento e confira o nível; persistindo, desligue o motor afetado, siga com o outro e chame a oficina Volvo Penta.'),
            ('5 · Temperatura alta', 'Reduza a rotação e confira a água no escapamento. Verifique o filtro de água salgada e o rotor. Se continuar subindo, desligue o motor afetado.'),
            ('6 · Parada', 'Deixe de 2 a 3 minutos em marcha lenta antes de desligar, para o motor esfriar por igual.'),
            ('7 · Manutenção na agenda', 'Troca de óleo e filtros: 12 meses ou 450 h (o que vier antes). Revisão anual pela oficina Volvo Penta. Intervalos oficiais: manual do fabricante — modelo SEM DADOS.'),
            ('8 · Horímetros', 'Horímetros na última leitura com motores ligados (26/09/2026 09:31, demonstração): BB 412,6 h · BE 409,8 h.'),
        ],
    },
    'checklist': {
        'titulo': ARQ['checklist'], 'pasta': 'manuais', 'equip': 'Checklist de bordo (DEMO)',
        'secoes': [
            ('Saída · 1 a 3', '1. Gerador: confira água no escapamento depois de ligar. 2. Estabilizador: ligue com antecedência (precisa de AC). 3. Climatização: filtro de água salgada limpo antes de ligar.'),
            ('Saída · 4 a 6', '4. Eletrônicos: plotter ligado, piloto em espera até sair da marina, VHF no canal 16. 5. Bombas de porão: acione cada uma manualmente e confira o alarme. 6. Diesel: ' + REGRA_ABAST + '.'),
            ('Saída · antes de largar', 'Confira coletes e boia à mão, pessoas a bordo contadas e anotadas no diário, previsão do tempo consultada. Amarração e fechamento: A CONFIRMAR (sem checklist oficial do estaleiro).'),
            ('Chegada', '1. Piloto em espera antes de manobrar. 2. Estabilizador: desligar ao atracar e manter energia até o volante parar. 3. Gerador: retirar cargas, esfriar e desligar. 4. Climatização: desligar e fechar válvula de fundo se o barco ficar parado. 5. Fechar a saída no diário: horas, consumo e pendências.'),
        ],
    },
    'protocolo': {
        'titulo': ARQ['protocolo'], 'pasta': 'protocolos', 'equip': 'Protocolo de emergência — procedimento padrão (confirmar com o protocolo de bordo)',
        'secoes': [
            ('MAYDAY · canal 16', 'Só em perigo grave e iminente. VHF canal 16 (156,800 MHz). Diga devagar: MAYDAY, MAYDAY, MAYDAY — AQUI É CAPITÃO IA, CAPITÃO IA, CAPITÃO IA — MMSI — POSIÇÃO (leia no plotter) — NATUREZA DO PERIGO — PESSOAS A BORDO — AUXÍLIO NECESSÁRIO — CÂMBIO. Repita até ter resposta. Procedimento padrão — confirmar com o protocolo de bordo.'),
            ('PAN-PAN · urgência', 'Urgência sem perigo imediato de vida (pane, sem governo, alguém ferido sem risco de morte): PAN-PAN, PAN-PAN, PAN-PAN no canal 16, no mesmo formato da chamada MAYDAY. Procedimento padrão — confirmar com o protocolo de bordo.'),
            ('DSC · botão de socorro', 'Nos rádios com DSC, o botão DISTRESS envia o alerta com o MMSI e a posição do GPS, se o MMSI estiver programado. Depois do alerta, faça a chamada MAYDAY por voz no canal 16.'),
            ('Homem ao mar', 'Grite HOMEM AO MAR e o lado (bombordo ou boreste). Jogue a boia ou qualquer objeto que flutue. Uma pessoa só aponta para quem caiu, sem perder de vista. Marque MOB no plotter. Volte devagar, com o motor em neutro perto da pessoa, por causa da hélice. Se perder de vista: MAYDAY no canal 16 com a posição da marca MOB. Procedimento padrão — confirmar com o protocolo de bordo.'),
            ('Incêndio · Seafire', 'SEM DADOS: localização, acionamento e tempo de espera do sistema Seafire não foram carregados. Enviar o manual ou o protocolo de bordo do Seafire.'),
            ('EPIRB', 'SEM DADOS: modelo, localização a bordo, forma de acionamento e validade da bateria do EPIRB não foram carregados.'),
        ],
    },
}
FONTE_GUIA = {k: g['titulo'] for k, g in GUIAS.items()}


def trechos():
    out = []
    for k, g in GUIAS.items():
        for sec, txt in g['secoes']:
            out.append({'fonte': g['titulo'], 'pag': None, 'secao': sec, 'texto': txt, 'equip': g['equip']})
    return out


# FAQ por equipamento (telas F2–F5): passo a passo tirado dos guias de bordo (DEMO)
def faq():
    def passos(k, idx):
        g = GUIAS[k]
        return [{'n': str(i + 1), 't': g['secoes'][j][1], 'secao': g['secoes'][j][0]} for i, j in enumerate(idx)]
    return {
        'gerador': {'status': 'PRONTO', 'fonte': GUIAS['g_gerador']['titulo'], 'equip': 'Gerador Onan', 'modelo': None,
                    'perguntas': [
                        {'q': 'Como ligar o gerador?', 'passos': passos('g_gerador', [0, 1, 2])},
                        {'q': 'Como desligar o gerador?', 'passos': passos('g_gerador', [3])},
                        {'q': 'Alarme de alta temperatura', 'passos': passos('g_gerador', [4])},
                        {'q': 'Alarme de baixa pressão de óleo', 'passos': passos('g_gerador', [5])},
                        {'q': 'Quantas horas tem e quando revisar?', 'passos': passos('g_gerador', [7, 6])},
                    ]},
        'estabilizador': {'status': 'PRONTO', 'fonte': GUIAS['g_seakeeper']['titulo'], 'equip': 'Estabilizador Seakeeper', 'modelo': None,
                          'perguntas': [
                              {'q': 'Como ligar antes de sair?', 'passos': passos('g_seakeeper', [0, 1, 2])},
                              {'q': 'Como desligar ao atracar?', 'passos': passos('g_seakeeper', [3, 4])},
                              {'q': 'Apareceu um alarme', 'passos': passos('g_seakeeper', [5])},
                              {'q': 'Manutenção', 'passos': passos('g_seakeeper', [6])},
                          ]},
        'eletronicos': {'status': 'PRONTO', 'fonte': GUIAS['g_eletronicos']['titulo'], 'equip': 'Eletrônicos Garmin · Fusion · VHF 315', 'modelo': None,
                        'perguntas': [
                            {'q': 'Homem ao mar no plotter', 'passos': passos('g_eletronicos', [0])},
                            {'q': 'Piloto automático', 'passos': passos('g_eletronicos', [1])},
                            {'q': 'Alarme de âncora', 'passos': passos('g_eletronicos', [2])},
                            {'q': 'Rádio VHF 315: canal 16 e DSC', 'passos': passos('g_eletronicos', [3, 4])},
                            {'q': 'Parear o celular no áudio Fusion', 'passos': passos('g_eletronicos', [5])},
                        ]},
        'climatizacao': {'status': 'PRONTO', 'fonte': GUIAS['g_clima']['titulo'], 'equip': 'Climatização', 'modelo': None,
                         'perguntas': [
                             {'q': 'Como ligar a climatização?', 'passos': passos('g_clima', [0, 1])},
                             {'q': 'Alarme de fluxo', 'passos': passos('g_clima', [2])},
                             {'q': 'Ar fraco na cabine', 'passos': passos('g_clima', [3])},
                             {'q': 'Como desligar?', 'passos': passos('g_clima', [4])},
                         ]},
    }


PROTOCOLOS = {
    'rotulo': 'procedimento padrão — confirmar com o protocolo de bordo',
    'fonte': ARQ['protocolo'] + ' · ' + DRIVE + ' › ' + PASTAS['protocolos'],
    'canal16': {'canal': '16', 'mhz': '156,800', 'fonte': 'canal 16 e MMSI informados pelo proprietário (MMSI fictício de demonstração)'},
    'roteiro': ['MAYDAY, MAYDAY, MAYDAY', 'AQUI É CAPITÃO IA, CAPITÃO IA, CAPITÃO IA', 'MMSI 710123456 (FICTÍCIO · DEMONSTRAÇÃO)',
                'POSIÇÃO — LEIA NO PLOTTER AGORA', 'NATUREZA DO PERIGO: ________', 'PESSOAS A BORDO: ________',
                'AUXÍLIO NECESSÁRIO: ________', 'CÂMBIO'],
    'mob': [
        'Grite HOMEM AO MAR e o lado (bombordo ou boreste). Jogue a boia ou qualquer objeto que flutue.',
        'Uma pessoa só aponta para quem caiu, sem perder de vista. Marque MOB no plotter Garmin.',
        'Volte devagar, com o motor em neutro perto da pessoa (hélice). Se perder de vista: MAYDAY no canal 16 com a posição da marca MOB.',
    ],
    'seafire': None,   # SEM DADOS
    'epirb': None,     # SEM DADOS
}


# ——————————————————————————————— SAÍDA ———————————————————————————————
def dados():
    ag = []
    for t in AGENDA:
        n = dn(t['vence'])
        x = dict(t)
        x['dn'] = n
        x.update(status_prazo(n))
        if 'horas' in t:
            x['horas'] = dict(t['horas'], faltam=round(t['horas']['limite'] - t['horas']['atual'], 1))
        x['fonte'] = ARQ['agenda']
        ag.append(x)
    ag.sort(key=lambda t: t['dn'])
    docs = []
    for doc in DOCUMENTOS:
        x = dict(doc)
        if doc.get('vence'):
            n = dn(doc['vence'])
            x['dn'] = n
            x['st'] = 'VENCIDO' if n < 0 else ('VENCE EM ' + str(n) + ' D' if n <= 90 else 'EM DIA')
        else:
            x['dn'] = None
        x['fonte'] = ARQ['documentos']
        docs.append(x)
    return {
        'versao': REF.strftime('%d/%m/%Y'),
        'demo': True, 'selo': SELO, 'aviso': AVISO,
        'embarcacao': EMBARCACAO, 'posicaoRef': POSICAO_REF, 'mar': MAR,
        'drive': {'raiz': DRIVE, 'pastas': PASTAS, 'arquivos': ARQ},
        'equipamentos': EQUIPAMENTOS, 'equipNota': EQUIP_NOTA,
        'snapshot': SNAPSHOT, 'consumo': CONSUMO, 'reserva': RESERVA, 'autonomia': autonomia(), 'serie24v': SERIE_24V,
        'agenda': ag, 'agendaFalta': AGENDA_FALTA, 'agendaFonte': ARQ['agenda'] + ' · ' + DRIVE + ' › ' + PASTAS['agenda'],
        'documentos': docs, 'docsFonte': ARQ['documentos'] + ' · ' + DRIVE + ' › ' + PASTAS['docs'],
        'abastecimentos': ABASTECIMENTOS, 'abastFonte': ARQ['abast'] + ' · ' + DRIVE + ' › ' + PASTAS['abast'], 'regraAbast': REGRA_ABAST,
        'diario': DIARIO, 'diarioFonte': ARQ['diario'] + ' · ' + DRIVE + ' › ' + PASTAS['diario'],
        'equipe': EQUIPE,
        'faq': faq(), 'guias': FONTE_GUIA,
        'protocolos': PROTOCOLOS,
    }


def escreve(caminho, texto):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, 'w', encoding='utf-8', newline='\n') as f:
        f.write(texto)


def gera_js(D):
    cab = ('/* Capitão IA — dados da embarcação (GERADO por ferramentas/demo/gerar_demo.py — não editar à mão).\n'
           '   ' + SELO + ': ' + AVISO + '\n'
           '   null = SEM DADOS (ou SEM LEITURA, em sensor). Cada grupo traz a fonte (arquivo no ' + DRIVE + '). */\n')
    return cab + 'window.CapitaoDados = ' + json.dumps(D, ensure_ascii=False, indent=1) + ';\n'


def gera_base():
    return json.dumps({
        'versao': REF.strftime('%Y-%m-%d'),
        'aviso': SELO + ' — trechos dos guias de bordo de demonstração (' + DRIVE + '). Orientação genérica: não substitui o '
                 'manual do fabricante (modelos SEM DADOS). Sem documentos pessoais, fiscais ou contratuais.',
        'trechos': trechos(),
    }, ensure_ascii=False, indent=1) + '\n'


def csv_txt(cab, linhas):
    b = io.StringIO()
    w = csv.writer(b, lineterminator='\n')
    w.writerow(cab)
    for l in linhas:
        w.writerow(['' if v is None else v for v in l])
    return b.getvalue()


def sd(v):
    return 'SEM DADOS' if v is None else v


def gera_fontes(D):
    F = {}
    rod = '<p><i>' + SELO + ' — ' + AVISO + '</i></p>'
    for k, g in GUIAS.items():
        nota = ('Procedimento padrão internacional, não é o protocolo de bordo: confirmar com o protocolo da embarcação.'
                if k == 'protocolo' else 'Guia de bordo de demonstração: orientação genérica, não substitui o manual do fabricante.')
        h = ['<h1>' + g['titulo'] + '</h1>', '<p><b>' + g['equip'] + '</b></p>', '<p><i>' + nota + '</i></p>']
        for sec, txt in g['secoes']:
            h.append('<h2>' + sec + '</h2><p>' + txt + '</p>')
        h.append(rod)
        F[PASTAS[g['pasta']] + '/' + g['titulo'] + '.html'] = '\n'.join(h)
    F[PASTAS['manuais'] + '/' + ARQ['inventario'] + '.csv'] = csv_txt(
        ['Equipamento', 'Fabricante', 'Modelo', 'Quantidade', 'Guia de bordo'],
        [[e['nome'], sd(e['fabricante']), sd(e['modelo']), e['qtd'], FONTE_GUIA.get(e['guia'], 'SEM DADOS') if e['guia'] else 'SEM DADOS'] for e in EQUIPAMENTOS])
    F[PASTAS['docs'] + '/' + ARQ['documentos'] + '.csv'] = csv_txt(
        ['Documento', 'Categoria', 'Validade', 'Situação em 26/09/2026', 'Observação'],
        [[x['n'], x['cat'], sd(x.get('vence')), x['st'], x['nota']] for x in D['documentos']])
    F[PASTAS['agenda'] + '/' + ARQ['agenda'] + '.csv'] = csv_txt(
        ['Tarefa', 'Equipamento', 'Responsável', 'Intervalo', 'Última', 'Vence', 'Prazo em 26/09/2026'],
        [[t['t'], t['equip'], t['quem'], t['intervalo'], t['ultima'], t['vence'], t['rot']] for t in D['agenda']] +
        [[f, '', '', '', '', '', 'SEM DADOS'] for f in AGENDA_FALTA])
    F[PASTAS['diario'] + '/' + ARQ['diario'] + '.csv'] = csv_txt(
        ['Data', 'Hora', 'Sistema', 'Registro', 'Quem', 'Pendência'],
        [[e['d'] + '/2026', e['h'], e['sys'], e['t'], e['who'], 'ABERTA' if e['pend'] else ''] for e in DIARIO])
    F[PASTAS['abast'] + '/' + ARQ['abast'] + '.csv'] = csv_txt(
        ['Data', 'Litros', 'Combustível', 'Local', 'Nível depois (%)', 'Situação', 'Observação'],
        [[a['d'], a['litros'], a['combustivel'], a['local'], a['nivelDepois'], a['st'], a['nota']] for a in ABASTECIMENTOS])
    s = SNAPSHOT
    F[PASTAS['tele'] + '/' + ARQ['snapshot']] = json.dumps({
        '_aviso': SELO + ' — leitura fictícia do coletor NMEA, só para demonstração.',
        'timestamp_utc': '2026-09-26T13:12:00Z', 'lat': s['gps']['lat'], 'lon': s['gps']['lon'], 'sog_nos': s['sog'],
        'proa_graus': s['proa'], 'gps_satelites': s['gps']['satelites'], 'profundidade_m': s['profundidade'],
        'vento_verdadeiro_nos': s['vento'], 'vento_verdadeiro_angulo': s['ventoDe'], 'pressao_barometrica_hpa': s['pressao'],
        'temp_ar_externo_c': s['ar'], 'temp_agua_c': s['agua'], 'tanque_agua_pct': s['tanques']['agua'],
        'tanque_cinzas_pct': s['tanques']['cinzas'], 'tanque_negras_pct': s['tanques']['negras'],
        'bateria_0_tensao_v': s['bat24'], 'bateria_2_tensao_v': s['bat12'], 'seakeeper_ativo': True,
        'seakeeper_volante_rpm': None, 'seakeeper_volante_pct': None,
        'motores_ultima_leitura_ligados': {'hora_local': '2026-09-26T09:31:00-03:00', 'rpm': s['motores']['rpm'], 'oleo_bar': s['motores']['oleo'],
                                           'arrefecimento_c': s['motores']['arref'], 'horimetro_h': s['motores']['horimetro'],
                                           'diesel_pct': [s['diesel']['bb'], s['diesel']['be']]},
        'gerador_horimetro_h': s['gerador']['horas'],
    }, ensure_ascii=False, indent=1) + '\n'
    F[ARQ['leiame'] + '.html'] = '\n'.join([
        '<h1>' + ARQ['leiame'] + '</h1>',
        '<p><b>' + SELO + '.</b> ' + AVISO + '</p>',
        '<p>Esta pasta é a fonte de dados da demonstração do Capitão IA (site estático). Cada resposta do app cita o arquivo daqui de onde veio o dado.</p>',
        '<h2>Pastas</h2><ul>' + ''.join('<li><b>' + v + '</b></li>' for v in PASTAS.values()) + '</ul>',
        '<h2>Regras</h2><ul><li>Nada inventado no app: sem fonte → SEM DADOS; sensor ausente → SEM LEITURA; manual existe e passo a passo não confirmado → MANUAL NO DRIVE; foto ou nota → A CONFERIR / A CONFIRMAR.</li>'
        '<li>Não publicar contratos, notas fiscais, título de propriedade, CPF/CNPJ, telefones, e-mails, valores, nomes de terceiros, chaves ou link público de arquivo com a posição do barco.</li>'
        '<li>Esta pasta é privada. Não compartilhar por link público.</li></ul>',
        '<p>Gerado por ferramentas/demo/gerar_demo.py (repositório wonderboat-ai/CapitaoIA_v2) em 26/09/2026.</p>',
    ])
    return F


def main():
    D = dados()
    escreve(os.path.join(RAIZ, 'capitao-dados.js'), gera_js(D))
    escreve(os.path.join(RAIZ, 'base-conhecimento.json'), gera_base())
    for rel, txt in gera_fontes(D).items():
        escreve(os.path.join(FONTES, rel), txt)
    a = autonomia()
    print('capitao-dados.js · base-conhecimento.json (%d trechos) · fontes em ferramentas/demo/fontes' % len(trechos()))
    print('agenda: %d tarefas, %d atrasadas · autonomia %.1f h / %d mn' % (len(D['agenda']), sum(1 for t in D['agenda'] if t['dn'] < 0), a['horas'], a['mn']))


if __name__ == '__main__':
    main()
