# -*- coding: utf-8 -*-
"""Capitão IA — conferência dos dados gerados (CONTRATO-DADOS 1.1.0 §6.3), chamada pelo gerar_demo.py antes de gravar.

verifica() roda as asserções sobre o D, a base, o FAQ, as fontes do Drive e o texto dos arquivos gerados, e devolve as
violações de cada uma (caminho e motivo). São as da §6.3 e, no fim, as invariantes da coluna "Asserção do gerador" da §6.4 que
não têm nome lá (TERCEIROS, SEM_PREVISAO); as outras da §6.4 ficam na MMSI9 ("programe" perto de MMSI) e na SEM_INDICATIVO
(indicativo, HEX ID, telefone e lugar de salvatagem como campo, §0.2). Depois, a EMBARCACAO (§1.2, a do C4 da §6.2: os campos
completos, rotulo e motorizacao gerados dos campos, lotacao ≥ pessoasBordo) e, por último, a ESTABILIZADOR_12V (revisão 3 do C4,
§1.5 e §2.5: o Seakeeper 3 é de 12 V DC, e nenhum texto do estabilizador fala de energia AC) e a SEGURANCA_SEM_MODELO (revisão 7 do C5, trava
17: fabricante, modelo e validade do EPIRB e do Seafire, e lugar a bordo, fora das telas de Equipamentos, Documentos e Leme). A PROTOCOLOS (C6, §1.3) prende a
forma e a fonte única do D.protocolos, e a GRAFIA_SEAFIRE (revisão do C6, §1.3) a grafia «Seafire», sem hífen nem espaço, em todo valor, chave e nome de arquivo.
A FAQ (C11, §1.6) prende o faq-equipamentos.json: a forma, os 91 ids, a ligação de cada item com o trecho da base que ele cita (a fonte e os números), a herança do `seguranca`
e do rótulo, os cartões EM sem dado do barco e o glossário; as outras asserções de texto já leem o FAQ.
A REGISTRO cruza o registro com o
`numero` do documento de id "tie" (§1.8; revisão final do C4: na simulação, sem esse documento ela reprova; o C7 grava o TIE). Duas da §6.4 moram dentro de asserções da §6.3, sem nome novo: o «porão ≤ 5 cm» (§2.4) na
JANELA (porao_no_normal: o teto é o normal.ate do porão, sem número solto, também dentro de janela) e o lugar de salvatagem em
qualquer ordem (§2.2/§2.3) na LOCAL_VOCAB (salvatagem_e_lugar: a LOCAL_SEGURANCA da TERMOS só pega o equipamento antes do lugar).

confere() imprime o resumo e reprova o gerador (nada é gravado) se uma asserção estrutural falhar. Da varredura de termos
(RELATORIO), só cinco das oito regex ficam em relatório até o C12; a PESSOAIS, a DINHEIRO e a LOCAL_SEGURANCA (telefone, e-mail,
CPF/CNPJ, dinheiro e lugar de equipamento de salvatagem: travas §2.2 e §2.7, 0 ocorrência hoje) reprovam já, sem pendência
(TERMOS_JA_REPROVAM, em_relatorio()). As violações de hoje que dependem do dado do C8 estão congeladas por caminho na
PENDENTES, cada uma com o commit que a tira: qualquer outra reprova, e uma pendência que não ocorre mais também (o commit que
completa o dado tira a linha dela).

As listas privadas (CAPITAO_LISTAS_PRIVADAS) e a pasta do Avanti (CAPITAO_AVANTI) são opcionais e só dão CONTAGENS: nenhum
termo delas é impresso nem gravado.

Também ficam aqui os ports em Python que as asserções e o gerador usam, escritos como no JavaScript:
  - norm/pad/has, emergencia() e oleo() do capitao-brain.js, com a lista SOS ampliada da 1b (PROMPT §2.3);
  - SEGURANCA_PALAVRAS e segura() (§1.5), uma fonte só das listas;
  - o laço de 150 s (§3.2: chaves, ruído por hash e arredondamento), a CapitaoAgora.nivel (§3.3) e o em() inteiro (§1.22, §1.24: laço,
    rota, contadores, derivados e alarmes, PORT_ROTA, C8). A paridade com o JS é da Fase 2.
Sem lookbehind nas regex que vão para o JavaScript (estas ficam só no Python).
"""
import calendar
import csv
import datetime
import hashlib
import io
import json
import math
import os
import re
import unicodedata
from collections import Counter
from html import unescape

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROIBIDOS = os.path.join(RAIZ, 'testes', 'proibidos.json')     # cópia do termos.json (PROMPT §3): a fonte das 8 regex
RODAPE = os.path.join(AQUI, 'rodape.js')                       # rodapé do capitao-dados.js (§1.23), anexado pelo gerar_demo.py

# ——————————————————————————————— modo de cada asserção ———————————————————————————————
# §6.2 C3: as estruturais reprovam o gerador; só a varredura de termos fica em relatório (não reprova), até o C12.
RELATORIO = {'TERMOS': 'C12'}   # com a exceção do mmsiNota até a 1b (EXCECAO_TERMOS)
# ...mas só as cinco regex de rótulo (ROTULOS, AUTENTICIDADE, VAZIOS, VISIVEL, ANEXO). As três das travas do PROMPT §2.2 e §2.7
# (telefone, e-mail e CPF/CNPJ; dinheiro; lugar de equipamento de salvatagem) dão 0 em todo o dado de hoje e não têm pendência:
# reprovam já, em qualquer texto (a mesma coisa como CHAVE já reprovava na SEM_INDICATIVO). Revisão final do C3.
TERMOS_JA_REPROVAM = ('PESSOAIS', 'DINHEIRO', 'LOCAL_SEGURANCA')


def em_relatorio(nome, msg):
    """A violação `msg` da asserção `nome` só é relatada (não reprova o gerador)? A TERMOS é parcial: a regex de cada violação
    (o que vem antes do 1º ':' da mensagem) decide."""
    return nome in RELATORIO and not (nome == 'TERMOS' and msg.split(':', 1)[0] in TERMOS_JA_REPROVAM)
# Violações de hoje que dependem do dado do C8, congeladas por caminho (não pela asserção inteira): cada uma com o commit
# que completa o dado. Uma violação fora desta lista reprova o gerador; um padrão que não casa mais nada também, para a lista
# não esconder a volta do defeito (o commit que completa o dado tira a linha dele). Cada padrão vale para UMA violação: o texto
# exato, com '*' no lugar de um trecho: o «…» citado (o caminho, a regra e, na MMSI9, os dígitos ficam presos), um nome que não
# pode estar no repositório, ou uma contagem. Nas duas das listas privadas e da pasta do Avanti, a contagem é exata e o termo vai
# por número (#n) ou por assinatura (nunca o nome).
# O C5 completou equipamentos, modelos, guias e trechos (§1.4, §1.5): as pendências dele (NULO, MMSI9, AFIRMA_REAL,
# SEGURANCA_MARCADA, MODELOS_AVANTI, COLISAO_MODELOS, EQUIP e NOTA_ETIQUETA) saíram com o dado. O C6 completou o D.protocolos (§1.3):
# saíram o seafire/epirb None (NULO), o MMSI do roteiro (MMSI9) e o roteiro e o MOB de antes (PROTOCOLO_LIMPO). O C7 completou a agenda
# (14 tarefas com deslocamento, sistema e palavras), os documentos (o TIE com id e número), o diário, a equipe e as fontes com prazos
# relativos (§1.7–§1.9, §1.11, §5): saíram as pendências do NULO (documentos sem prazo omitem vence e dn), REGISTRO, TERCEIROS, IDS,
# AGENDA e FONTES_RELATIVAS.
PENDENTES = {}   # o C8 completou o snapshot (porao, ancora e o volante da leitura da pasta 05, §1.17): nenhuma pendência congelada
COMMITS_PENDENTES = ()   # o C4 completou a embarcação, o C5 os equipamentos e os guias, o C6 o D.protocolos, o C7 a agenda, os documentos, o diário e as fontes relativas e o C8 o snapshot, a rota e o replay
# Asserções que só rodam com uma fonte opcional do ambiente: sem ela, a pendência delas não é "velha".
OPCIONAIS = {'MODELOS_AVANTI': 'listas', 'COLISAO_MODELOS': 'avanti'}
# Única exceção da varredura de termos na Fase 1 (§1.2): sai na 1b, junto com o campo.
EXCECAO_TERMOS = {'embarcacao.mmsiNota': '1b'}
# Textos fixos (PROMPT §2.3, §3; CONTRATO §1.3, §1.4): a referência é daqui, nunca do dado que está sendo conferido. O rótulo é a
# EXCEÇÃO do §3 na varredura de termos; tirado do D, um termo posto no próprio rótulo sumiria de todo o dado.
ROTULO = 'procedimento padrão — confirmar com o protocolo de bordo'
NOTA = 'modelo, validade e acionamento: veja a etiqueta do equipamento'
# D.protocolos (§1.3, C6): a forma e os textos que o contrato fixa letra por letra. A referência é daqui, nunca do dado conferido
# (o ROTULO e a NOTA, acima, valem para as outras asserções). O roteiro leva o nome da embarcação na linha 1 e é o único campo que lê o D.
SALVATAGEM_TXT = ('Em perigo agora: SOS do app e VHF canal 16. Coletes: um por pessoa — conte as pessoas a bordo agora (lotação: veja a '
                  'placa de lotação). Balsa, coletes, boias, extintores e sinalizadores: no local da placa de salvatagem e do plano de '
                  'segurança de bordo — confira na saída.')   # PROMPT §2.3
PROTOCOLOS_TEXTOS = {
    'mmsiRadio': 'MMSI do rádio de bordo (etiqueta / Licença de Estação)', 'mmsiRotulo': 'MMSI (cadastro do app)',
    'indicativo': 'o da Licença de Estação (no rádio)',
    'plotter': 'POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER · PESSOAS: CONTE AGORA', 'hud': 'POSIÇÃO · LEIA NO PLOTTER',
    'salvatagem': SALVATAGEM_TXT,
    'panpan': ('Urgência sem perigo imediato de vida (pane, sem governo, alguém ferido sem risco de morte): PAN-PAN, PAN-PAN, PAN-PAN no '
               'canal 16, no mesmo formato da chamada MAYDAY.'),
    'dsc': ('O botão DISTRESS envia o alerta com a identificação programada no rádio: é o MMSI do rádio de bordo (etiqueta / Licença de '
            'Estação). Depois do alerta, faça o MAYDAY por voz no canal 16.'),
}
PROTOCOLOS_LISTAS = {'roteiro': 8, 'mob': 3, 'alagamento': 1, 'abandono': 1, 'oleo': 4}   # campo → quantidade de strings
PROTOCOLOS_BLOCOS = {'seafire': {'passos': 5}, 'epirb': {'passos': 4, 'teste': 2}}        # objeto → lista → quantidade (e a `nota`)
# As linhas do roteiro MAYDAY que não dependem do dado (a 2ª é o nome ×3; MMSI, posição e pessoas nunca são o número gerado, §2.2 do PROMPT).
ROTEIRO_FIXO = {0: 'MAYDAY, MAYDAY, MAYDAY', 2: 'MMSI — LEIA NA ETIQUETA DO RÁDIO (Licença de Estação)', 3: 'POSIÇÃO — LEIA NO PLOTTER AGORA',
                4: 'NATUREZA DO PERIGO: ________', 5: 'PESSOAS A BORDO: conte agora', 6: 'AUXÍLIO NECESSÁRIO: ________', 7: 'CÂMBIO'}
# Fonte única (§1.3): o D.protocolos e os guias de bordo dizem a mesma coisa. campo → [(guia em drive.arquivos, início do título da seção)];
# o texto do campo (listas juntas por espaço) tem de estar inteiro na seção. O g_ais §2 tem texto próprio (MMSI_RADIO, sem o DSC).
PROTOCOLOS_NOS_GUIAS = (
    ('mob', (('protocolo', 'Homem ao mar'),)),
    ('seafire.passos', (('protocolo', 'Incêndio'), ('g_seafire', '1 · '))),
    ('epirb.passos', (('protocolo', 'EPIRB'),)),
    ('epirb.passos[:3]', (('g_epirb', '1 · '),)),
    ('epirb.teste', (('g_epirb', '2 · '),)),
    ('epirb.passos[3]', (('g_epirb', '3 · '),)),
    ('alagamento', (('protocolo', 'Água entrando'), ('g_porao', '4 · '))),
    ('abandono', (('protocolo', 'Abandono'),)),
    ('oleo', (('g_motores', '4 · '),)),
    ('salvatagem', (('protocolo', 'Salvatagem'),)),
    ('panpan', (('protocolo', 'PAN-PAN'),)),
    ('dsc', (('protocolo', 'DSC'), ('g_eletronicos', '5 · '))),
)
# Mínimo do §1.5 (coluna seguranca: true da tabela dos guias): a marcação por palavra pode pegar mais seções, nunca menos. Chave
# de drive.arquivos → números de seção (no checklist, o título); None = todas. No FAQ (§1.6), os ids das mesmas seções e os EM.
MINIMO_SEGURANCA = {'g_motores': {'4'}, 'g_eletronicos': {'1', '5'}, 'g_porao': {'4'}, 'g_ais': {'2'}, 'g_seafire': None,
                    'g_epirb': None, 'checklist': {'Saída · antes de largar'}, 'protocolo': None}
# Revisão 4 do C5 (§1.5): o respostaBase do cérebro e a voz leem o trecho de segurança INTEIRO (até 1.500 letras, MAX_SEGURANCA do
# capitao-brain.js), para o rótulo do procedimento padrão e a nota da etiqueta não ficarem de fora; acima de 800 letras a fala passa de
# 1 minuto. Os trechos de hoje chegam a 560 (g_seafire §1 e o protocolo do Seafire).
SEGURANCA_MAX_LETRAS = 800
# Revisão 5 do C5 (§1.5): `ident` = palavras de acionamento do trecho de segurança (como a pessoa conta a situação que ele trata e o título
# não diz). O cérebro as conta na identidade do trecho; verbo de operação e nome de equipamento ou de sistema ali sequestrariam
# pergunta comum (foi o que a revisão 4 do C5 tirou do Seafire: "como desligar a ventilação", "como religar o gerador").
# Revisão 6 do C5: a lista fixa de 21 palavras deixava passar "caiu plotter", "caiu ligue", "caiu bateria"; o conjunto proibido agora sai do
# próprio dado (equipamentos, fontes, equips e títulos da base) mais a lista fixa, abaixo, que fica de piso.
IDENT_PROIBIDAS = set(('ligar desligar religar abrir fechar esfriar disparo disparou alarme alarmes sistema ventilação gerador motor motores bomba bombas porão óleo filtro água etiqueta '
                       'manutenção partida parada bateria baterias banco bancos carregador tensão pressão temperatura âncora guincho corrente piloto radar plotter plotters '
                       'ais vhf rádio rádios dsc epirb seafire baliza casco tanque tanques combustível diesel climatização estabilizador horímetro descarga').split())
# Raízes de verbo de operação (qualquer flexão: lig-ar, lig-ue, lig-ado, relig-ue): o "ligue", o "desligue" e o "abra" passavam.
IDENT_VERBOS_RAIZ = ('lig', 'deslig', 'relig', 'abr', 'fech', 'esfri', 'acion', 'dispar', 'inici', 'reinici', 'engat', 'recolh', 'lanc', 'fund', 'troc', 'substitu',
                     'verific', 'test', 'limp', 'inspecion', 'reset', 'ativ', 'desativ', 'cort', 'conect', 'desconect', 'trav', 'destrav', 'instal', 'regul', 'ajust',
                     'calibr', 'configur', 'parear', 'mant', 'carreg', 'descarreg')
IDENT_VERBOS_EXATOS = {'par', 'pare', 'parar', 'paro'}
# Pessoa em `ident`: nunca ("quantas pessoas a bordo?" é pergunta comum); a palavra de pessoa vai em `identCom`.
IDENT_PESSOA_PROIBIDA = {'pessoa', 'pessoas', 'alguem'}
# `identCom` (revisão 6 do C5): palavras de pessoa que destravam o `ident`. Lista fechada, sem acento.
IDENT_PESSOA_OK = {'pessoa', 'quem', 'alguem', 'gente', 'homem', 'mulher', 'tripulante', 'crianca', 'passageiro', 'marinheiro', 'filho', 'filha', 'menino', 'menina', 'amigo'}
# Palavra de `ident` que descreve queda ou vista ("o disjuntor caiu", "a vista do mar", "a temperatura do mar caiu"): só com `identCom`.
IDENT_EXIGE_PESSOA = {'caiu', 'cair', 'cai', 'queda', 'vista', 'mar'}
MINIMO_FAQ = re.compile(r'(?:EM|SF|EP)-\d+|MO-04|EL-01|EL-05|PO-04|AI-02|CK-03')
# Ocorrências permitidas na pasta do Avanti, por candidato (COLISAO_MODELOS; ok do proprietário, §8.2 ponto 9).
EXCECOES_MODELO = {'Seakeeper 3': 1}
# Port do em() (§1.14, §1.22, §1.24; C8): definido mais abaixo (PORT_ROTA = em). Um D com rota que o port não consegue rodar reprova a EMENDA_ROTA.

# O que o replay de uma simulação carrega (§1.16), fora o que a rota e o laço já exigem pelo catálogo.
REPLAY_CHAVES = ('duracao', 'passo', 'passo_chave', 'cenario', 'ancora_hora', 'voltas_fixo', 'velocidade_media_nos', 'fases', 'chaves', 'ruido', 'fixos',
                 'contadores_base', 'taxas_h', 'por_volta', 'por_dia', 'diesel_piso_l', 'limites', 'alertas', 'janelas', 'diaDeBordo')

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
EQUIP_SEGURANCA = ('epirb', 'seafire')   # fabricante, modelo e validade só em Equipamentos, Leme e Documentos (trava 17)
# Revisão 7 do C5 (SEGURANCA_SEM_MODELO): onde os nomes valem. Equipamentos, Documentos e Leme no D (o Leme lê a agenda e o agendaFalta;
# a AGENDA cuida do campo equip dela) e, nas fontes do Drive, o inventário, o controle de documentos e a agenda. Em todo o resto
# (guias, protocolo, base, FAQ, ficha, páginas de fonte) fabricante, modelo e validade do EPIRB e do Seafire não entram.
D_EQUIP_DOC_LEME = ('equipamentos', 'documentos', 'agenda', 'agendaFalta', 'agendaFonte')
FONTES_EQUIP_DOC_LEME = ('Inventário de bordo.csv', 'Controle de documentos.csv', 'Agenda preditiva.csv')
SECAO_SEAFIRE = 'Incêndio · Seafire'   # título da seção do protocolo (§1.5): único lugar, fora dessas telas, onde a palavra "Seafire" aparece
# Grafia do sistema fixo (CONTRATO §1.3, §8.2 decisão 3): «Seafire» em todo texto do dado e «seafire» em chave, id e texto normalizado
# (a do app desde a 1.0.0). Entre «Sea» e «fire»: nada (nem espaço, nem hífen de qualquer largura, nem NBSP, nem travessão, nem sublinhado,
# nem caractere invisível). A `sea[- ...]?fire` da LOCAL_SEGURANCA (termos.json) só prende o lugar do equipamento na frase: não prende a grafia.
SEAFIRE_GRAFIA = ('Seafire', 'seafire')
R_SEAFIRE = re.compile(r'sea[\s_\-\u00ad\u2010-\u2015\u2212\u200b-\u200d\u2060\ufeff]*fire', re.I)
# A única exceção: as `palavras` de busca de cada equipamento (F31) guardam o que o ditado e o teclado escrevem ("kamins", "vebasto", "sea fire"):
# é vocabulário de entrada, que o cérebro compara com a pergunta normalizada, nunca texto que o app mostra ou fala.
PALAVRAS_BUSCA = re.compile(r'equipamentos\[\d+\]\.palavras\[\d+\]')
GUIAS_DE_SEGURANCA = ('g_seafire', 'g_epirb', 'protocolo')   # guias inteiros de segurança (chaves de drive.arquivos)
FAQ_DE_SEGURANCA = re.compile(r'(?:EM|SF|EP)-\d+')
_MESES = 'janeiro|fevereiro|mar[çc]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro'
# data ou prazo de validade num texto de segurança: dd/mm, dd/mm/aaaa, aaaa-mm-dd, ano, nome de mês, ou "validade/vence…" com número perto
R_VALIDADE = re.compile(r'\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b|\b\d{4}-\d{2}-\d{2}\b|\b(?:19|20)\d{2}\b|\b(?:' + _MESES + r')\b'
                        r'|(?:venc\w*|v[aá]lid\w*|expir\w*)[^.!?;\n]{0,40}\d', re.I)
# §0.2: indicativo, HEX ID, telefone e lugar de equipamento de salvatagem não existem como campo (SEM_INDICATIVO). Pelas palavras
# do nome da chave (camelCase, '_' e '-' separam; sem acento): 'hexId' → hex, id, e pelas junções delas (palavras_juntas: 'WhatsApp'
# → whats, app, whatsapp, que a grafia da marca separa). O indicativo vale só em protocolos (o texto de
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
# Campo sem valor que virou texto num derivado ("None · 12,40 m · 2023", "2 × None QSB6.7 305 · eixo"): reprova nos dois modos.
R_SEM_VALOR = re.compile(r'(?<![A-Za-zÀ-ÿ])(?:None|null|undefined|NaN)(?![A-Za-zÀ-ÿ])')
ORIGEM_ROTULO = ('modelo', 'comprimento', 'ano')
# Unidades da barco_sos (dado da embarcação no SOS), no texto normalizado (norm: minúsculas, sem acento).
UN_SOS = {'m': r'(?:m|metros?)', 't': r'(?:t|toneladas?)', 'L': r'(?:l|litros?)'}


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


def desvio_em(H, campo, dias_atras):
    """Desvio do campo em unidades reais, a `dias_atras` dias de bordo (§1.13; port da interpolação do CapitaoReplay.serie, Fase 2): linear
    entre os pontos de `passo_dias` em `passo_dias` dias (d[0] a n·passo dias atrás … d[n−1] a passo dias atrás) e 0 na âncora de hoje."""
    s = H['desvios'][campo]
    d, n, passo = s['d'], H['n'], H['passo_dias']
    if dias_atras <= 0:
        return 0.0
    p = n - dias_atras / passo    # posição em d (d[n] seria hoje, 0)
    if p <= 0:
        return d[0] / s['escala']
    i = int(math.floor(p))
    a = d[i] if i < n else 0
    b = d[i + 1] if i + 1 < n else 0
    return (a + (b - a) * (p - i)) / s['escala']


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


# ——————————————————————————————— port do em() (§1.22, §1.24; C8) ———————————————————————————————
# O quadro de um segundo do dia de bordo (seg = segundos desde a âncora, 0…86.399): laço de 150 s (§3.2) + rota + contadores +
# derivados + alarmes. É o que o CapitaoReplay.em() faz no JavaScript (Fase 2; a paridade é testada lá). Função pura de `seg`: sem
# estado. As contas seguem o texto do contrato; o que ele deixa em aberto, decidido aqui:
#   - lat e lon andam em linha reta de ponto a ponto, pela fração x/mn da perna (as mn e o rumo de cada perna vêm de D.rota.pernas,
#     que o cliente não recalcula); a posição ao longo do circuito é s = distância percorrida × fator, módulo o circuito;
#   - o COG faz um arco de guinada de |Δ|/guinada_max_gps × nós de cruzeiro/3600 mn em volta de cada ponto, centrado nele (função de s);
#   - o destino, a distância ao destino e a ETA vêm da posição LINEARIZADA (seg × velocidade_media_nos), para o HH:MM não piscar na
#     volta; a distância ao destino é medida na posição de verdade e nunca fica negativa;
#   - a ETA arredonda ao minuto mais próximo (o HH:MM de uma chegada às 06:59:59,6 é 07:00, não 06:59);
#   - o desequilíbrio entre os dois tanques de diesel é de 3 L (diesel_bb_pct = (L/2 + 3)/capacidade do tanque).
ANCORA_REF_S = calendar.timegm((2026, 9, 26, 10, 0, 0))   # 07:00 de 26/09/2026 em America/Sao_Paulo (UTC−3): âncora de referência dos testes
DESEQUILIBRIO_DIESEL_L = 3


def _wrap(x):
    return ((x + 540) % 360) - 180


def mn_entre(a, b):
    """Distância em milhas náuticas entre dois pontos (lat, lon): plano local, com o cosseno da latitude média (a escala das pernas da rota)."""
    la = math.radians((a[0] + b[0]) / 2)
    return math.hypot((b[1] - a[1]) * 60 * math.cos(la), (b[0] - a[0]) * 60)


def rumo_entre(a, b):
    la = math.radians((a[0] + b[0]) / 2)
    return (math.degrees(math.atan2((b[1] - a[1]) * math.cos(la), b[0] - a[0])) + 360) % 360


def _iso_utc(s):
    return datetime.datetime.fromtimestamp(s, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


_PORTS = {}


def preparar(D):
    """Constantes do em() para este D (séries de 150 s do laço, somas acumuladas e arcos da rota), guardadas pelo conteúdo dele."""
    R, rota, C = D['replay'], D['rota'], D['campos']
    chave = hashlib.sha1(json.dumps([R, rota, C, (D.get('consumo') or {}), (D.get('embarcacao') or {}).get('tanques')],
                                    sort_keys=True, default=str).encode('utf-8')).hexdigest()
    if chave in _PORTS:
        _PORTS[chave] = _PORTS.pop(chave)   # o mais recente por último
        return _PORTS[chave]
    n = R['duracao']
    Q = [quadro_laco(R, C, t) for t in range(n)]
    ger = (D.get('consumo') or {}).get('gerador_lph', 0)
    cumD, cumM = [0.0], [0.0]
    for q in Q:
        cumD.append(cumD[-1] + (q['consumo_lph'] + ger) / 3600)
        cumM.append(cumM[-1] + q['sog_nos'] / 3600)
    pernas = rota['pernas']
    g, nos = rota.get('guinada_max_gps') or 3, ((D.get('consumo') or {}).get('cruzeiro') or {}).get('nos', 18)
    arcos = []
    for i, p in enumerate(pernas):
        d = _wrap(p['rumo'] - pernas[i - 1]['rumo'])
        arcos.append((p['ini_mn'], d, abs(d) / g * nos / 3600, pernas[i - 1]['rumo']))
    tq = (D.get('embarcacao') or {}).get('tanques') or {}
    P = {'D': D, 'R': R, 'rota': rota, 'C': C, 'n': n, 'Q': Q, 'cumD': cumD, 'cumM': cumM, 'tot': rota['distancia_mn'], 'ida': rota['ida_mn'],
         'pontos': {p['id']: p for p in [rota['base']] + list(rota['pontos'])}, 'pernas': pernas, 'arcos': arcos,
         'alerta_de': {a['campo']: i for i, a in (R.get('alertas') or {}).items()},
         'tanque_l': tq.get('diesel_l', 0) / (tq.get('diesel_n') or 2), 'passos': None}
    while len(_PORTS) >= 6:   # poucos na memória: os testes plantam centenas de D, quase todos com a mesma rota e o mesmo replay
        _PORTS.pop(next(iter(_PORTS)))
    _PORTS[chave] = P
    return P


def _cog(P, s):
    """(COG em graus, graus por mn) na posição s do circuito (0 ≤ s < circuito): a perna, ou o arco de guinada em volta do ponto."""
    tot = P['tot']
    for ini, d, Lr, prev in P['arcos']:
        if Lr <= 0:
            continue
        for base in (ini, ini + tot, ini - tot):
            if abs(s - base) < Lr / 2:
                return (prev + d * ((s - base) + Lr / 2) / Lr) % 360, d / Lr
    for p in P['pernas']:
        if p['ini_mn'] <= s < p['ini_mn'] + p['mn']:
            return p['rumo'], 0.0
    return P['pernas'][-1]['rumo'], 0.0


def em(P, seg, ancora_s=ANCORA_REF_S, com_alarmes=True):
    """O quadro do segundo `seg` do dia de bordo, na ordem do D.campos (primeiro os campos do catálogo, depois o que sobrar). Sem
    alarmes (varredura do dia) o campo `alarmes` não é calculado."""
    R, rota, C, n = P['R'], P['rota'], P['C'], P['n']
    seg = int(seg)
    t, v = seg % n, seg // n
    q0 = P['Q'][t]
    cb, pv, tx = R['contadores_base'], R['por_volta'], R['taxas_h']
    cas = lambda c: casas_de(C, c)
    o = dict(q0)
    # contadores (valor = base + voltas · por_volta + soma parcial da tabela de 150 s; horímetros e tanques pelo relógio)
    diesel = cb['diesel_litros'] - (v * pv['diesel_l'] + P['cumD'][t])
    diesel = max(diesel, R['diesel_piso_l'])
    dist = cb['distancia_mn'] + v * pv['distancia_mn'] + P['cumM'][t]
    h = seg / 3600
    cont = {'diesel_litros': diesel, 'distancia_mn': dist}
    for c in ('motor_bb_horimetro_h', 'motor_be_horimetro_h', 'gerador_horimetro_h'):
        cont[c] = cb[c] + h
    for c, k in tx.items():
        cont[c] = cb[c] + k * h
    for c, x in cont.items():
        o[c] = arred(x, cas(c))
    cap = P['tanque_l']
    o['diesel_bb_pct'] = arred((diesel / 2 + DESEQUILIBRIO_DIESEL_L) / cap * 100, cas('diesel_bb_pct'))
    o['diesel_be_pct'] = arred((diesel / 2 - DESEQUILIBRIO_DIESEL_L) / cap * 100, cas('diesel_be_pct'))
    # rota: posição, perna e rumo
    tot, ida_mn = P['tot'], P['ida']
    s = dist * rota['fator']
    sm = s % tot
    pernas = P['pernas']
    i = next((k for k, p in enumerate(pernas) if sm < p['ini_mn'] + p['mn']), len(pernas) - 1)
    p = pernas[i]
    x = min(max(sm - p['ini_mn'], 0.0), p['mn'])
    a, b = P['pontos'][p['de']], P['pontos'][p['para']]
    f = x / p['mn']
    o['lat'] = arred(a['lat'] + (b['lat'] - a['lat']) * f, cas('lat'))
    o['lon'] = arred(a['lon'] + (b['lon'] - a['lon']) * f, cas('lon'))
    cog, gpm = _cog(P, sm)
    sog = q0['sog_nos']
    cor = rota['corrente']
    stw = sog - cor['nos'] * math.cos(math.radians(cog - cor['para_graus']))
    delta = math.degrees(math.asin(cor['nos'] * math.sin(math.radians(cor['para_graus'] - cog)) / stw))
    amp_p, sem_p = (R.get('ruido') or {}).get('proa_graus', [0, 0])
    amp_f, sem_f = (R.get('ruido') or {}).get('profundidade_m', [0, 0])
    proa = (cog - delta + amp_p * ruido(sem_p, seg)) % 360
    o['cog_graus'] = arred(cog, cas('cog_graus')) % 360
    o['proa_graus'] = arred(proa, cas('proa_graus')) % 360
    o['piloto_rumo'] = arred(p['rumo'], cas('piloto_rumo')) % 360
    o['stw_nos'] = arred(stw, cas('stw_nos'))
    taxa = gpm * sog / 3600   # graus por segundo
    o['leme_graus'] = arred(max(-25, min(25, 5 * taxa)) + q0['leme_graus'], cas('leme_graus'))
    o['profundidade_m'] = arred(a['prof_m'] + (b['prof_m'] - a['prof_m']) * f + amp_f * ruido(sem_f, seg), cas('profundidade_m'))
    # vento aparente (soma vetorial do vento verdadeiro com o movimento do barco; ângulo relativo à proa, + a boreste)
    tws, twd = q0['vento_verdadeiro_nos'], q0['vento_verdadeiro_angulo']
    ax = tws * math.sin(math.radians(twd + 180)) - sog * math.sin(math.radians(cog))
    ay = tws * math.cos(math.radians(twd + 180)) - sog * math.cos(math.radians(cog))
    o['vento_aparente_nos'] = arred(math.hypot(ax, ay), cas('vento_aparente_nos'))
    o['vento_aparente_angulo'] = arred(_wrap((math.degrees(math.atan2(ax, ay)) + 180) % 360 - proa), cas('vento_aparente_angulo'))
    # destino, distância, próximo ponto e ETA (posição linearizada: o HH:MM é constante em cada perna do circuito)
    vel = R['velocidade_media_nos']
    slin = seg * vel / 3600
    nc = math.floor(slin / tot + 1e-12)
    vai = (slin - nc * tot) < ida_mn
    sdest = nc * tot + (ida_mn if vai else tot)
    o['destino'] = rota['destino']['nome'] if vai else rota['volta']['nome']
    o['destino_mn'] = arred(max(0.0, sdest - s), cas('destino_mn'))
    o['wp_proximo'] = b['nome']
    o['wp_mn'] = arred(max(0.0, p['mn'] - x), cas('wp_mn'))
    ini_min = int(R.get('ancora_hora', '07:00')[:2]) * 60 + int(R.get('ancora_hora', '07:00')[3:])
    eta_min = int(math.floor(sdest / (vel / 3600) / 60 + 0.5))
    o['eta'] = '%02d:%02d' % (((ini_min + eta_min) // 60) % 24, (ini_min + eta_min) % 60)
    perto = a if x < p['mn'] - x else b
    id_destino = rota['destino']['id'] if vai else rota['base']['id']
    caminho = rota['destino']['caminho'] if vai else rota['volta']['caminho']
    o['local'] = perto['perto'] + (', chegando' if perto['id'] == id_destino else ', ' + caminho)
    o['timestamp_utc'] = _iso_utc(ancora_s + seg)
    res = {c: o[c] for c in C if c in o}
    res.update({c: x_ for c, x_ in o.items() if c not in res})
    # alarmes (a nivel nos valores mostrados; a janela do id dá o `desde` desta volta)
    if not com_alarmes:
        return res
    lim, por_campo, alertas = R.get('limites') or {}, P['alerta_de'], R.get('alertas') or {}
    alarmes = []
    for campo in lim:
        nv = nivel(lim, C, campo, res)
        if not nv or nv['nivel'] == 'normal':
            continue
        aid = por_campo.get(campo, campo)
        a_ = alertas.get(aid) or {}
        al = {'id': aid, 'nivel': nv['nivel']}
        if a_.get('sistema'):
            al['sistema'] = a_['sistema']
        if a_.get('lado'):
            al['lado'] = a_['lado']
        j = next((j for j in R.get('janelas') or [] if j.get('id') == aid and j.get('nivel') == nv['nivel'] and j['ini'] <= t <= j['fim']), None)
        al.update(campo=campo, valor=res[campo], limite=nv['limite'], desde=_iso_utc(ancora_s + v * n + (j['ini'] if j else t)))
        alarmes.append(al)
    res['alarmes'] = alarmes
    return res


PORT_ROTA = em


def deriva_janelas(R, C):
    """R.janelas (§1.16): para cada campo de R.limites, os trechos contínuos do laço em que a nivel não é «normal», no valor mostrado
    (mesmo nivel, mesmo nível de alarme); o id é o do alerta do campo. Ordenadas por início e campo. Só o laço e os fixos (a rota e os
    contadores nunca cruzam limite no cenário do gerador)."""
    por_campo = {a['campo']: i for i, a in (R.get('alertas') or {}).items()}
    Q = [quadro_laco(R, C, t) for t in range(R['duracao'])]
    out = []
    for campo in R.get('limites') or {}:
        nv = [(nivel(R['limites'], C, campo, q) or {}).get('nivel', 'normal') for q in Q]
        t = 0
        while t < len(Q):
            if nv[t] == 'normal':
                t += 1
                continue
            f = t
            while f + 1 < len(Q) and nv[f + 1] == nv[t]:
                f += 1
            out.append({'id': por_campo.get(campo, campo), 'campo': campo, 'nivel': nv[t], 'ini': t, 'fim': f})
            t = f + 1
    return sorted(out, key=lambda j: (j['ini'], j['campo']))


DISCRETOS = ('destino', 'wp_proximo', 'eta')   # o que não pode mudar na emenda de 150 s
CAMPOS_PASSO = ('lat', 'lon', 'cog_graus', 'proa_graus', 'piloto_rumo', 'profundidade_m', 'destino_mn', 'wp_mn', 'diesel_litros', 'distancia_mn',
                'motor_bb_horimetro_h', 'motor_be_horimetro_h', 'gerador_horimetro_h', 'tanque_agua_pct', 'tanque_cinzas_pct', 'tanque_negras_pct')
CAMPOS_ANGULO = ('cog_graus', 'proa_graus', 'piloto_rumo')


def hora_do_dia(R, seg):
    """HH:MM:SS (relógio de bordo) do segundo `seg` do dia de bordo, contado da `ancora_hora` do replay (07:00 se faltar)."""
    h, m = ((R or {}).get('ancora_hora') or '07:00').split(':')[:2]
    t = int(h) * 3600 + int(m) * 60 + int(seg)
    return '%02d:%02d:%02d' % ((t // 3600) % 24, (t % 3600) // 60, t % 60)


def varredura_dia(P):
    """Uma passada pelos segundos do dia de bordo (guardada em P): os eventos da rota (troca de ponto, de destino ou de ETA), o maior
    passo de 1 s de cada campo fora das emendas e dos eventos, o passo e os eventos em cada emenda de 150 s (N·150), o passo da virada
    (A − 1 s → A) e, nos campos de limite que o laço de 150 s não cobre (contador, tanque, profundidade: a rota e os contadores andam o
    dia inteiro), o nível de cada segundo pela `nivel` portada: `limites[campo]` = {nivel: (segundo, valor)} para o primeiro segundo em
    aviso e o primeiro em crítico, e `perto` = (segundo, valor, limite) do primeiro valor a menos de 0,05 de um limite do regime em vigor
    (JANELA e FIO, §6.3: «todo valor por segundo»)."""
    if P['passos'] is not None:
        return P['passos']
    n, dia = P['n'], P['n'] * P['R']['por_dia']['voltas']
    maximos, emendas, eventos = {c: 0.0 for c in CAMPOS_PASSO}, {}, []
    lim, C = P['R'].get('limites') or {}, P['C']
    dia_lim = [c for c in lim if c not in (P['R'].get('chaves') or {})]   # os de laço (periódicos em 150 s) são da a_janela e da a_fio
    niveis = {c: {'niveis': {}, 'perto': None} for c in dia_lim}
    # o que a `nivel` lê além do valor do campo (ativo_se e o rpm dos regimes): o resultado só muda quando o valor ou uma dessas entradas muda,
    # e só o primeiro segundo de cada resultado é guardado, então o segundo que repete a entrada anterior não precisa reavaliar (contador e
    # tanque mudam a cada dezenas de segundos; sem isto a varredura do dia custava 6 s a mais por D)
    dep = {c: [x for x in ([(lim[c].get('ativo_se') or {}).get('campo')] + [g.get('rpm_campo') for g in lim[c].get('regimes') or []]) if x] for c in dia_lim}
    visto = {}

    def limites_em(seg, q):
        for c in dia_lim:
            chave = (q.get(c),) + tuple(q.get(x) for x in dep[c])
            if visto.get(c) == chave:
                continue
            visto[c] = chave
            nv = nivel(lim, C, c, q)
            if nv is None:
                continue
            d = niveis[c]
            if nv['nivel'] != 'normal':
                d['niveis'].setdefault(nv['nivel'], (seg, q[c]))
            if d['perto'] is None:
                v = arred(q[c], casas_de(C, c))
                perto = [x for x in limiares(regime_de(lim[c], nv)) if round(abs(v - x), 9) < 0.05]
                if perto:
                    d['perto'] = (seg, v, perto[0])
    prev = em(P, 0, com_alarmes=False)
    limites_em(0, prev)
    for s in range(1, dia):
        cur = em(P, s, com_alarmes=False)
        limites_em(s, cur)
        ev = [k for k in DISCRETOS if cur[k] != prev[k]]
        passo = {c: _passo(cur[c], prev[c], c in CAMPOS_ANGULO) for c in CAMPOS_PASSO}
        if s % n == 0:
            emendas[s // n] = (passo, ev)
        elif ev:
            eventos.append((s, ev))
        else:
            for c, d in passo.items():
                maximos[c] = max(maximos[c], d)
        prev = cur
    a0, a1 = em(P, dia - 1, com_alarmes=False), em(P, 0, com_alarmes=False)
    P['passos'] = {'max': maximos, 'emendas': emendas, 'eventos': eventos, 'A': {c: _passo(a1[c], a0[c], c in CAMPOS_ANGULO) for c in CAMPOS_PASSO},
                   'limites': niveis}
    return P['passos']


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


def palavras_juntas(k):
    """palavras_chave(k) mais as junções de 2 e de 3 palavras vizinhas e a da chave inteira, sem repetir e na ordem: o camelCase
    separa o que a lista de chaves traz inteiro ('WhatsApp' → whats, app, whatsapp · 'baixa-mar' → baixamar · 'Hex_I_D' → hexid)."""
    ps = palavras_chave(k)
    juntas = [''.join(ps[i:j]) for i in range(len(ps)) for j in range(i + 2, min(i + 3, len(ps)) + 1)]
    return list(dict.fromkeys(ps + juntas + [''.join(ps)]))


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
        self.salvatagem = equip_salvatagem(self.termos)
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
        self._port = None

    def port(self):
        """(P, None) com o port do em() pronto para este D, ou (None, motivo) se faltar rota ou replay, ou o port não rodar."""
        if self._port is None:
            if not (isinstance(self.D.get('rota'), dict) and isinstance(self.R, dict) and self.R.get('chaves')):
                self._port = (None, 'sem D.rota ou sem D.replay.chaves')
            else:
                try:
                    P = preparar(self.D)
                    em(P, 0, com_alarmes=False)   # roda uma vez: um campo ou uma chave que falta aparece aqui
                    self._port = (P, None)
                except Exception as e:   # KeyError, TypeError, ZeroDivisionError…: o motivo vai na mensagem
                    self._port = (None, '%s: %s' % (type(e).__name__, e))
        return self._port

    def todos(self, numeros=False):
        """(caminho, texto) de todo valor string do D, da base, do FAQ e das fontes do Drive (com numeros, também os números)."""
        yield from textos(self.D, '', numeros)
        yield from textos(self.base, 'base:', numeros)
        if self.faq is not None:
            yield from textos(self.faq, 'faq:', numeros)
        yield from textos_fontes(self.fontes, numeros)

    def chaves(self):
        """(caminho, chave) de toda chave do D, da base, do FAQ e dos JSON das fontes do Drive (os mesmos prefixos do todos()) e,
        de cada CSV das fontes, a 1ª linha com conteúdo (linha em branco antes dela não esconde o cabeçalho): o cabeçalho de cada coluna
        é a chave da planilha que vai ao Drive ('fontes/<rel>:<coluna>')."""
        yield from chaves_de(self.D, '')
        yield from chaves_de(self.base, 'base:')
        if self.faq is not None:
            yield from chaves_de(self.faq, 'faq:')
        for rel, txt in sorted(self.fontes.items()):
            if rel.endswith('.json'):
                yield from chaves_de(json.loads(txt), 'fontes/' + rel + ':')
            elif rel.endswith('.csv'):
                for col in next((l for l in csv.reader(io.StringIO(txt)) if any(c.strip() for c in l)), []):
                    yield 'fontes/%s:%s' % (rel, col), col

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


def metades_local(termos):
    """As duas metades da LOCAL_SEGURANCA do proibidos.json, (equipamento, lugar), cada uma como grupo `(?:...)`: a regex pede o
    equipamento antes do lugar, na mesma frase, a até 60 caracteres. Uma fonte só das duas listas (PROMPT §3), sem lista paralela."""
    partes = termos['LOCAL_SEGURANCA'].pattern.split(r'[^.\n]{0,60}')
    if len(partes) != 2 or not all(p.startswith('(?:') and p.endswith(')') for p in partes):
        raise SystemExit('confere.py: a LOCAL_SEGURANCA do proibidos.json mudou de forma (equipamento[^.\\n]{0,60}lugar); ajuste metades_local()')
    return partes


def lugar_a_bordo(termos):
    """Lugar a bordo nos protocolos (§1.3: "nenhuma string tem ... nome de lugar a bordo"), com a lista de lugares da própria
    LOCAL_SEGURANCA. A LOCAL_SEGURANCA pede o equipamento antes do lugar, na mesma frase; aqui o lugar vale sozinho, em qualquer ordem."""
    return re.compile(r'(?:^|[^A-Za-zÀ-ÿ])' + metades_local(termos)[1], re.I)


def equip_salvatagem(termos):
    """Equipamento de salvatagem (a metade da frente da LOCAL_SEGURANCA, mais "salva-vidas" sozinho: "bote salva-vidas"), com o
    início de palavra de lugar_a_bordo(). Junto de lugar_a_bordo(), acha o par na mesma frase em qualquer ordem."""
    return re.compile(r'(?:^|[^A-Za-zÀ-ÿ])(?:' + metades_local(termos)[0] + r'|salva[- \u00a0\u2010-\u2014]?vidas?)', re.I)


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
    """§1.2 e §2.3. O formato do registro e o que ele não pode imitar (placa, HIN, 9 a 11 dígitos, HEX ID, PESSOAIS) e o cruzamento
    com o TIE: o registro é o `numero` do documento de `id` "tie" (§1.8). Na simulação, o registro preenchido exige esse
    documento (revisão final do C4: o TIE era procurado só quando já tinha `id`, e o dado de hoje, sem `id`, escapava do cruzamento
    sem nenhuma pendência); no modo real (§4.2), o TIE ausente não reprova, mas um TIE com `numero` diferente sim."""
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
    ties = [d for d in (X.D.get('documentos') or []) if isinstance(d, dict) and d.get('id') == 'tie']
    if len(ties) > 1:
        out.append('documentos: %d documentos com id "tie" (precisa de 1)' % len(ties))
    if not ties:
        if X.simulacao:
            out.append('documentos[tie] ausente: o TIE precisa de id "tie" e numero = embarcacao.registro (§1.2, §1.8)')
    elif ties[0].get('numero') is None:
        out.append('documentos[tie].numero ausente (= embarcacao.registro, §1.8)')
    elif ties[0]['numero'] != r:
        out.append('documentos[tie].numero diferente de embarcacao.registro')
    return out


def a_hex15(X):
    """Como a MMSI9: string e número, uma violação por ocorrência."""
    return ['%s: %s «%s»' % (cam, m.group(), trecho(s, m)) for cam, s in X.todos(numeros=True) for m in R_HEX15.finditer(s)]


def a_sem_indicativo(X):
    """§0.2: indicativo, HEX ID, telefone e lugar de equipamento de salvatagem não existem como campo, em todo o D, a base, o FAQ,
    os JSON das fontes e o cabeçalho de cada coluna dos CSV das fontes (o indicativo só como texto de instrução em protocolos; o
    lugar só nos caminhos da LUGAR_PERMITIDO e na coluna Local do registro de abastecimento, que é o posto). E
    nenhum indicativo com prefixo real no texto, uma violação por ocorrência."""
    out = []
    posto = 'fontes/%s/%s.csv:Local' % (X.pastas.get('abast'), X.arq.get('abast'))   # a coluna Local do abastecimento = o posto
    for c, k in X.chaves():
        ps = palavras_juntas(k)
        if 'indicativo' in ps and not c.startswith('protocolos.'):
            out.append(c + ': chave indicativo fora de protocolos')
        tipo = next((CHAVES_IDENT[p] for p in ps if p in CHAVES_IDENT), None)
        if tipo:
            out.append('%s: chave de %s (§0.2: não existe como campo)' % (c, tipo))
        if CHAVES_LUGAR & set(ps) and not CHAVES_HORA & set(ps) and not LUGAR_PERMITIDO.fullmatch(c) and c != posto:
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
            if CHAVES_DOC & set(palavras_juntas(k)) and not (c == cam + '.numero' and d.get('id') == 'tie'):
                out.append('%s: chave de número ou emissor de documento (§1.8: só o TIE tem número)' % c)
    out += ['%s: número de documento [%s] «%s»' % (cam, m.group(1), trecho(s, m)) for cam, s in X.todos() for m in R_NUM_DOC.finditer(s)]
    return out


def a_sem_previsao(X):
    """§6.4, trava §2.5 (tempo e maré são do mundo real), sem nome na §6.3: nenhum campo de previsão ou de maré no D (o historico,
    o catálogo de campos e o replay inclusive), na base, no FAQ, nos JSON das fontes e no cabeçalho de cada coluna dos CSV das fontes."""
    return ['%s: campo de previsão ou maré (tempo e maré só do Open-Meteo real)' % c for c, k in X.chaves()
            if CHAVES_PREVISAO & set(palavras_juntas(k))]


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
    snapshot; 1 ≤ pessoasBordo ≤ lotacao; e o número das linhas do diário fixo com "N pessoas a bordo" (a saída) = pessoasBordo.
    Revisão do C4 (modo real): rotulo e motorizacao nunca com "None" (ou null/NaN) no texto; campo de origem None ⇒ derivado None
    (rotulo presente com modelo, comprimento ou ano None é incoerência; no modo real, motorizacao presente com fabricante,
    modelo ou qtd de equipamentos[motores] None também — na simulação, esse None já reprova na NULO); no modo real, volume de
    tanque None também passa (SEM DADOS)."""
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
    for k in ('rotulo', 'motorizacao'):
        if isinstance(E.get(k), str) and R_SEM_VALOR.search(E[k]):
            out.append('embarcacao.%s com campo sem valor no texto (o derivado de um None é None): %r' % (k, E[k]))
    sem_origem = [k for k in ORIGEM_ROTULO if E.get(k) is None]
    if sem_origem:
        if E.get('rotulo') is not None:
            out.append('embarcacao.rotulo presente sem o campo de origem (%s None = SEM DADOS: o rotulo também é None)' % ', '.join(sem_origem))
    elif all(_positivo(E.get(k), t) for k, t in (('modelo', str), ('comprimento', 'num'), ('ano', 'int'))):
        esperado = '%s · %s m · %d' % (E['modelo'], ('%.2f' % E['comprimento']).replace('.', ','), E['ano'])
        if E.get('rotulo') != esperado:
            out.append('embarcacao.rotulo ≠ o gerado dos campos (%r)' % esperado)
    mot = E.get('motorizacao')
    eq = X.eq('motores') or {}
    if not X.simulacao and mot is not None and [k for k in ('fabricante', 'modelo', 'qtd') if k in eq and eq[k] is None]:
        out.append('embarcacao.motorizacao presente com equipamentos[motores] sem fabricante, modelo ou qtd (None = SEM DADOS: a '
                   'motorizacao também é None)')
    if isinstance(mot, str) and mot:
        m = R_MOTORIZACAO.fullmatch(mot)
        if not m:
            out.append('embarcacao.motorizacao fora do formato "<n> × <motor> · <transmissão>": %r' % mot)
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
        if T and not _positivo(T.get(k), 'num') and not (T.get(k) is None and not X.simulacao):   # modo real: None = SEM DADOS
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


def nomes_seguranca(fab, mod):
    """Nomes a mais do fabricante e do modelo de um equipamento de segurança (EPIRB e Seafire; trava 17: fabricante, modelo e
    validade só em Equipamentos, Leme e Documentos), além dos candidatos da candidatos_modelo():
      - cada palavra do fabricante e do modelo com 3 caracteres ou mais que não seja só número ("Ocean", "Signal", "SafeSea",
        "E100G", "300M"): o "FD 300M" também aparece como "a 300M" ou "o E100G";
      - o fabricante e cada parte do modelo sem o espaço e com o hífen no lugar ("OceanSignal", "FD300M", "FD-300M", "SafeSea-E100G").
    Só para estes dois: nos outros equipamentos uma palavra solta do modelo ("V2", "M37") casaria texto comum ("Capitão IA v2")."""
    out = []
    for texto in [fab] + partes_modelo(mod):
        palavras = [w for w in re.split(r'[\s\-\u00a0\u2010-\u2014/.,;:()+]+', texto or '') if w]
        out += [w for w in palavras if len(w) >= 3 and not re.fullmatch(r'[\d.,]+', w)]
        if len(palavras) > 1:
            out += [sep.join(palavras) for sep in ('', '-')]
    return out


def nomes_equip(X):
    """Fabricante e candidatos do modelo de cada equipamento gerado (para PROTOCOLO_LIMPO e AGENDA), pela mesma regra da
    candidatos_modelo() (§2.5): parte ou base com menos de 4 letras, ou sem dígito, vai com o fabricante na frente. Solta, a parte
    "V2" do Lewmar casava o "v2" de "Capitão IA v2" no protocolos.fonte do §1.3. Nos equipamentos de segurança (EQUIP_SEGURANCA, ou
    `seguranca`), também cada palavra e as juntas (nomes_seguranca)."""
    out = []
    for e in X.equip:
        fab = e.get('fabricante') if isinstance(e.get('fabricante'), str) else ''
        mod = e.get('modelo') if isinstance(e.get('modelo'), str) else ''
        mais = nomes_seguranca(fab, mod) if e.get('seguranca') is True or e.get('id') in EQUIP_SEGURANCA else []   # pelo id também: a marca `seguranca` não pode ser o que desliga a guarda
        for v in [fab] + candidatos_modelo(fab, mod) + mais:
            if v.strip() and (e.get('id'), v.strip()) not in out:
                out.append((e.get('id'), v.strip()))
    return out


def acha_nomes(s, nome):
    """Cada ocorrência do nome como palavra inteira, sem distinguir maiúsculas (o grupo 1 é o nome casado)."""
    return re.finditer(r'(?:^|[^A-Za-zÀ-ÿ0-9])(' + re.escape(nome) + r')(?![A-Za-zÀ-ÿ0-9])', s, re.I)


def _rx_texto(v):
    """Regex do texto v no texto normalizado (norm: sem acento e em minúsculas), como palavra inteira e com qualquer espaço."""
    return re.compile(r'(?<![a-z0-9])' + r'\s+'.join(re.escape(w) for w in norm(v).split()) + r'(?![a-z0-9])')


def _rx_numero(x, un):
    """Regex do número x seguido da unidade, no texto normalizado: vírgula ou ponto, zeros à direita opcionais e milhar com ou sem
    ponto (12,4 · 12,40 · 12.4 m; 1.600 · 1600 L)."""
    inteiro, dec = repr(float(x)).split('.')
    dec = dec.rstrip('0')
    i = '{:,}'.format(int(inteiro)).replace(',', r'\.?')
    return re.compile(r'(?<![\d.,])' + i + (r'[.,]' + dec + '0*' if dec else r'(?:[.,]0+)?') + r'\s*' + UN_SOS[un] + r'(?![a-z0-9])')


def barco_sos(E, numeros=True, base=True):
    """[(campo, regex)] do dado gerado da embarcação que o SOS nunca mostra (trava §2.1 do PROMPT: só o nome; CONTRATO §1.3: o SOS
    não lê D.embarcacao.{registro, mmsi, base, modelo, fabricante}), tirado do próprio D e procurado no texto normalizado (norm),
    sem distinguir maiúsculas nem acentos (o roteiro do SOS é em maiúsculas): o registro, com qualquer separador entre os grupos ou
    sem nenhum (CIA-23-0417, CIA 23 0417, CIA230417); o fabricante, o modelo e a marca (palavra de 4 letras ou mais do fabricante que
    também está no modelo: "Marévia"); o rotulo; a motorizacao e o motor dela ("Cummins QSB6.7 305" e a 1ª palavra, a marca, antes
    do C5 gravar o equipamentos[motores]); com base, a base, também sem a UF entre parênteses (a S1 escreve assim). Com numeros, o
    ano (sozinho) e os números com unidade: comprimento, boca, calado, deslocamento e os tanques. O MMSI fica na MMSI9 e as
    pessoas e a lotação na R_PESSOAS. Campo None (modo real, SEM DADOS) fica de fora."""
    E = E if isinstance(E, dict) else {}
    s = lambda k: E.get(k) if isinstance(E.get(k), str) and E.get(k).strip() else None
    out = []
    if s('registro'):
        grupos = re.findall(r'[a-z0-9]+', norm(E['registro']))
        if grupos:
            out.append(('registro', re.compile(r'(?<![a-z0-9])' + r'[^a-z0-9\n]{0,3}'.join(grupos) + r'(?![a-z0-9])')))
    for k in ('fabricante', 'modelo', 'rotulo', 'motorizacao'):
        if s(k):
            out.append((k, _rx_texto(E[k])))
    if s('fabricante') and s('modelo'):
        no_modelo = set(re.findall(r'[a-z0-9]+', norm(E['modelo'])))
        for w in re.findall(r'[a-z0-9]+', norm(E['fabricante'])):
            if len(re.sub(r'[^a-z]', '', w)) >= 4 and w in no_modelo:
                out.append(('marca', _rx_texto(w)))
    m = R_MOTORIZACAO.fullmatch(s('motorizacao') or '')
    if m:
        out.append(('motor', _rx_texto(m.group(2))))
        marca = m.group(2).split()[0]
        if len(re.sub(r'[^A-Za-zÀ-ÿ]', '', marca)) >= 4:
            out.append(('motor', _rx_texto(marca)))
    if base and s('base'):
        out.append(('base', _rx_texto(E['base'])))
        sem_uf = re.sub(r'\s*\(.*\)$', '', E['base'])
        if sem_uf != E['base'] and sem_uf.strip():
            out.append(('base', _rx_texto(sem_uf)))
    if numeros:
        if _positivo(E.get('ano'), 'int'):
            out.append(('ano', re.compile(r'(?<![\d.,])%d(?![\d])' % E['ano'])))
        un = E.get('un') if isinstance(E.get('un'), dict) else {}
        for k in ('comprimento', 'boca', 'calado', 'deslocamento'):
            if _positivo(E.get(k), 'num') and un.get(k) in UN_SOS:
                out.append((k, _rx_numero(E[k], un[k])))
        T = E.get('tanques') if isinstance(E.get('tanques'), dict) else {}
        vols = [(k, T.get(k)) for k in TANQUES_EMBARCACAO if k.endswith('_l')]
        if _positivo(T.get('diesel_l'), 'num') and _positivo(T.get('diesel_n'), 'int') and T['diesel_n'] > 1:
            vols.append(('diesel_l (cada tanque)', T['diesel_l'] / T['diesel_n']))   # 2 × 800 L
        for k, v in vols:
            if _positivo(v, 'num'):
                out.append(('tanques.' + k, _rx_numero(v, 'L')))
    return out


BARCO_SOS_EXIGIDO = ('registro', 'fabricante', 'modelo', 'rotulo', 'motorizacao')


def falta_barco_sos(E, simulacao):
    """Campos da embarcação que a conferência da tela do SOS (verificar.py) exige no D para valer. Na simulação (D.simulacao
    diferente de false; sem a chave, também), os cinco: sem algum deles a barco_sos não teria o que procurar e a tela passaria
    vazia. No modo real (simulacao false, CONTRATO §4.2), nenhum: None é SEM DADOS, como na a_embarcacao e na a_registro, e a
    conferência vale para o que estiver preenchido (a barco_sos ignora o campo vazio). Revisão 3 do C4: antes, a tela reprovava o
    modo real com modelo ou rotulo None, embora o SOS nunca mostre esses campos."""
    if simulacao is False:
        return []
    E = E if isinstance(E, dict) else {}
    return [k for k in BARCO_SOS_EXIGIDO if not (isinstance(E.get(k), str) and E[k].strip())]


def acha_barco(s, E, regras):
    """[(campo, texto casado, trecho)] de cada ocorrência das regras da barco_sos no texto s. O nome (o único dado do barco que o
    SOS mostra) sai do texto antes, para a marca no nome ("AQUI É <nome>") não contar."""
    t = norm(s)
    nome = norm(E.get('nome')) if isinstance(E, dict) and isinstance(E.get('nome'), str) else ''
    if nome.strip():
        t = t.replace(nome, ' ' * len(nome))
    o = s if len(s) == len(t) else t   # norm guarda o tamanho nas letras compostas; senão, o trecho sai do texto normalizado
    return [(campo, o[m.start():m.end()], trecho(o, m)) for campo, rx in regras for m in rx.finditer(t)]


def a_protocolo_limpo(X):
    """Cada regra uma violação por ocorrência, com o texto casado: a pendência prende o caminho, a regra e o texto de hoje (um 2º
    "ETA" ou "último fix" numa string que já é pendência reprova). Revisão 2 do C4: e nenhum dado gerado da embarcação além do nome
    (barco_sos: registro, fabricante, modelo, marca, rotulo, motorizacao, base, ano, dimensões e tanques), porque o protocolos é a
    única fonte do SOS (trava §2.1)."""
    P = X.D.get('protocolos')
    if P is None:
        return []
    return _regras_protocolo(X, textos(P, 'protocolos'))


def _regras_protocolo(X, pares):
    """As regras da PROTOCOLO_LIMPO sobre (caminho, texto): sem bar, %, nós, mn, graus, minutos, número de pessoas, último fix, a regex de
    emergência, lugar a bordo, fabricante ou modelo de equipamento e dado gerado da embarcação. Do D.protocolos (C6) e dos cartões EM do FAQ (C11)."""
    out = []
    nomes = []   # um nome por grafia: o "Garmin" dos plotters e do radar é uma ocorrência só no texto
    for _, n in nomes_equip(X):
        if n.lower() not in [x.lower() for x in nomes]:
            nomes.append(n)
    E = X.D.get('embarcacao') if isinstance(X.D.get('embarcacao'), dict) else {}
    barco = barco_sos(E)
    for cam, s in pares:
        for nome, rx in R_PROTOCOLO + (('lugar a bordo', X.lugar),):
            out += ['%s: %s [%s] «%s»' % (cam, nome, casado(m), trecho(s, m)) for m in rx.finditer(s)]
        achados = [m for n in nomes for m in acha_nomes(s, n)]
        for m in achados:   # uma violação por ocorrência: o nome dentro de outro ("Ocean" em "Ocean Signal", "300M" em "FD-300M") não conta duas vezes
            a, b = m.span(1)
            if not any(c <= a and b <= d and (c, d) != (a, b) for c, d in (x.span(1) for x in achados)):
                out.append('%s: fabricante ou modelo de equipamento [%s] «%s»' % (cam, m.group(1), trecho(s, m)))
        out += ['%s: dado gerado da embarcação (%s) [%s] «%s»' % (cam, campo, txt, tr) for campo, txt, tr in acha_barco(s, E, barco)]
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
    return out + salvatagem_e_lugar(X)


def salvatagem_e_lugar(X):
    """Trava §2.2/§2.3 (regra 9 do CLAUDE.md: nunca gerar lugar de equipamento de salvatagem), em qualquer ordem. A LOCAL_SEGURANCA
    da TERMOS pede o equipamento antes do lugar («Os coletes ficam no paiol de proa»); aqui vale a mesma frase em qualquer ordem
    («No paiol de proa ficam os coletes»), em todo texto do D, da base, do FAQ e das fontes do Drive (nas páginas HTML, cada tag
    separa a frase). As duas listas são as da LOCAL_SEGURANCA (equip_salvatagem() e lugar_a_bordo()). A frase genérica da
    salvatagem («no local da placa de salvatagem e do plano de segurança de bordo») não tem nome de lugar e passa sem exceção."""
    out = []
    for cam, s in X.todos():
        if cam.endswith('.html'):
            s = re.sub(r'<[^>]*>', '\n', s)
        for f in R_FRASE.split(s):
            a, b = X.salvatagem.search(f), X.lugar.search(f)
            if a and b:
                out.append('%s: equipamento de salvatagem e lugar a bordo na mesma frase [%s + %s] «%s»' % (cam, casado(a), casado(b), f.strip()[:140]))
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


# Revisão 3 do C4 (§1.5, §2.5): o Seakeeper 3 funciona só no banco de 12 V, em corrente contínua.
R_ESTAB = re.compile(r'estabiliz|seakeeper|giroscop')   # no texto normalizado (norm)
R_ENERGIA_AC = re.compile(r'(?<![A-Za-zÀ-ÿ0-9])(?:AC|CA)(?![A-Za-zÀ-ÿ0-9])|(?i:corrente|energia)\s+alternada')
R_FRASE = re.compile(r'(?<=[.;!?])\s+|\n+')


def a_estabilizador_12v(X):
    """Nenhum texto do estabilizador fala de energia AC ("AC", "CA", corrente ou energia alternada): o Seakeeper 3 é de 12 V DC,
    e o guia que manda ligar o gerador para ele acelerar denuncia o fictício para quem conhece o equipamento (revisão 3 do C4).
    Inteiros: o trecho e o item do FAQ cuja fonte ou equip é o estabilizador, e todo texto cujo caminho o cita (a página de fonte
    do guia, o D.faq.estabilizador, o snapshot.seakeeper). No resto, só a frase que cita o estabilizador: a climatização e o
    gerador continuam com a energia AC deles, e "Com energia AC (gerador ou cais)" do guia da climatização passa."""
    out = []
    inteiros = ['%s[%d].' % (pre, i) for pre, lista in (('base:trechos', X.trechos), ('faq:itens', X.itens_faq))
                for i, t in enumerate(lista) if R_ESTAB.search(norm(' '.join(str(t.get(k) or '') for k in ('fonte', 'equip'))))]
    for cam, s in X.todos():
        partes = [s] if R_ESTAB.search(norm(cam)) or cam.startswith(tuple(inteiros)) else \
            [f for f in R_FRASE.split(s) if R_ESTAB.search(norm(f))]
        for f in partes:
            out += ['%s: energia AC num texto do estabilizador [%s] «%s»' % (cam, m.group(), trecho(f, m)) for m in R_ENERGIA_AC.finditer(f)]
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
    """Cada limite aponta para um §n que existe na base e o texto dele tem os números em pt-BR. Antes do D.replay (C8), confere a
    constante LIMITES do gerador (C5: os guias já saem dela); depois, o D.replay.limites, que tem de ser a mesma constante."""
    out = []
    lims = X.limites
    const = X.const.get('LIMITES')
    if not lims and isinstance(const, dict):
        lims = const
    elif lims and isinstance(const, dict) and lims != const:
        out.append('replay.limites ≠ a constante LIMITES do gerador (uma fonte só, §3.3)')
    for c, L in lims.items():
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
    out += alertas_no_guia(X)
    dbo = (X.R or {}).get('diaDeBordo')
    if isinstance(dbo, dict):
        abs_ = {'ab-%d' % k for k in range(dbo.get('dias', 0))}
        for x in list(dbo.get('diario') or []) + ([dbo['documento']] if isinstance(dbo.get('documento'), dict) else []):
            if 'ref' in x and x['ref'] not in abs_:
                out.append('replay.diaDeBordo.%s.ref fora de ab-0…ab-%d: %r' % (x.get('id'), dbo.get('dias', 0) - 1, x['ref']))
    return out


def _palavras(t):
    return ' '.join(re.findall(r'\w+', t.lower()))


def alertas_no_guia(X):
    """replay.alertas (§1.16): o campo está no catálogo e em R.limites; a seção citada existe no guia de bordo (base) e traz inteiros, sem
    caixa nem pontuação, os passos do alerta; a fonte é «<título do guia> §n · <seção>» (ou «§ <seção>» no checklist, sem número); os dois
    alertas de óleo levam os passos de protocolos.oleo."""
    out = []
    guias = X.D.get('guias') or {}
    oleo = (X.D.get('protocolos') or {}).get('oleo')
    for aid, a in ((X.R or {}).get('alertas') or {}).items():
        if a.get('campo') not in X.campos or a.get('campo') not in X.limites:
            out.append('replay.alertas.%s.campo %r fora de D.campos ou de replay.limites' % (aid, a.get('campo')))
        passos = a.get('passos')
        if not (isinstance(passos, list) and passos and all(isinstance(p, str) and p.strip() for p in passos)):
            out.append('replay.alertas.%s.passos: lista de textos' % aid)
            continue
        if aid.startswith('oleo_') and isinstance(oleo, list) and passos != oleo:
            out.append('replay.alertas.%s.passos ≠ protocolos.oleo (§1.16)' % aid)
        tit = guias.get(a.get('guia'))
        if tit is None:
            out.append('replay.alertas.%s.guia fora de D.guias: %r' % (aid, a.get('guia')))
            continue
        sec = a.get('secao') or ''
        tr = next((t for t in X.trechos if t.get('fonte') == tit and t.get('secao') == sec), None)
        if tr is None:
            out.append('replay.alertas.%s: o guia %r não tem a seção %r' % (aid, tit, sec))
            continue
        texto = _palavras(tr.get('texto', ''))
        for p in passos:
            if _palavras(p) not in texto:
                out.append('replay.alertas.%s: o passo %r não está inteiro em %s · %s' % (aid, p, tit, sec))
        esperado = tit + (' §' + sec if sec[:1].isdigit() else ' § ' + sec)
        if a.get('fonte') != esperado:
            out.append('replay.alertas.%s.fonte %r ≠ %r' % (aid, a.get('fonte'), esperado))
    return out


POSICAO_CHAVES = {'lat', 'lon', 'lng', 'latitude', 'longitude'}


def _cabecalho_csv(txt):
    """As colunas da 1ª linha com conteúdo de um CSV das fontes (vírgula ou ponto e vírgula) e as demais linhas."""
    sep = ';' if ';' in txt.split('\n', 1)[0] else ','
    linhas = [l for l in csv.reader(io.StringIO(txt), delimiter=sep)]
    i = next((j for j, l in enumerate(linhas) if any(c.strip() for c in l)), None)
    return ([], []) if i is None else (linhas[i], linhas[i + 1:])


def posicao_nas_fontes(fontes):
    """Fontes do Drive com posição: JSON com chave lat/lon/latitude/longitude (em qualquer profundidade) ou CSV com coluna assim.
    §4.3: com SIMULACAO = False o repositório público não leva a posição do barco, nem na leitura nem na série da pasta 05."""
    out = []
    for rel, txt in sorted(fontes.items()):
        if rel.endswith('.json'):
            achou = sorted({k for _, k in chaves_de(json.loads(txt)) if norm(str(k)).strip() in POSICAO_CHAVES})
        elif rel.endswith('.csv'):
            achou = sorted({c for c in _cabecalho_csv(txt)[0] if norm(c).strip() in POSICAO_CHAVES})
        else:
            continue
        if achou:
            out.append('fontes/%s: traz %s' % (rel, ' e '.join(achou)))
    return out


def formato_sem_taxonomia(X):
    """Pasta 05: nenhuma planilha mostra a taxonomia interna do D.campos (coluna «Origem» nem um valor de ORIGENS numa célula): o
    Formato do quadro descreve o coletor NMEA, e laço, janela ou rota denunciariam que as leituras são geradas (CONTRATO §0, item 6)."""
    out, tele = [], (X.pastas.get('tele') or '\0') + '/'
    for rel, txt in sorted(X.fontes.items()):
        if not (rel.startswith(tele) and rel.endswith('.csv')):
            continue
        cab, corpo = _cabecalho_csv(txt)
        if any(norm(c).strip() == 'origem' for c in cab):
            out.append('fontes/%s: a coluna «Origem» mostra a taxonomia interna do D.campos' % rel)
        vistos = sorted({c.strip() for l in corpo for c in l if c.strip() in ORIGENS})
        if vistos:
            out.append('fontes/%s: o valor «%s» é da taxonomia interna do D.campos.origem' % (rel, '», «'.join(vistos)))
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
    # §1.15 e §6.3 («simulado fora»): o simulado: true do CapitaoTelemetria.atual() é marca, não leitura. Nem no catálogo nem, por
    # consequência das checagens de baixo, em replay.chaves/fixos/contadores_base nem em snapshot.quadro (ficariam fora de D.campos).
    if 'simulado' in C:
        out.append('campos.simulado: marca do atual(), não leitura; fica fora do catálogo (§1.15)')
    for c, d in C.items():
        if d.get('origem') not in ORIGENS:
            out.append('campos.%s.origem fora de %s: %r' % (c, sorted(ORIGENS), d.get('origem')))
        if (d.get('origem') == 'contador') != ('sentido' in d) or ('sentido' in d and d['sentido'] not in (1, -1)):
            out.append('campos.%s: sentido (+1/−1) em todo contador e só neles' % c)
    for grupo, origem in (('chaves', 'laço'), ('fixos', 'fixo'), ('contadores_base', 'contador')):
        if not R.get('chaves'):   # modo real (§4.3): o replay sai só com limites e alertas; o laço, os fixos e os contadores são da simulação
            break
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
    if X.simulacao and any(d.get('origem') in ('rota', 'derivado', 'relógio', 'janela') for d in C.values()):
        P, erro = X.port()
        if P is None:
            out.append('quadro ⇔ catálogo nos campos de rota, derivado, relógio e janela: o port do em() não rodou (%s)' % erro)
        else:
            q = PORT_ROTA(P, 0)
            out += ['em(): o quadro tem %s, que não está em D.campos' % c for c in q if c not in C]
            out += ['em(): o quadro não tem %s, que está em D.campos' % c for c in C if c not in q]
            out += ['replay sem %s (§1.16)' % c for c in REPLAY_CHAVES if c not in R]
    if isinstance(sq, dict):   # §1.17: pela nivel, todo campo do instante guardado dá normal ou não se avalia
        for c in X.limites:
            nv = nivel(X.limites, C, c, sq)
            if nv and nv['nivel'] != 'normal':
                out.append('snapshot.quadro.%s = %s: nivel %s (o instante guardado só tem campo normal ou que não se avalia)' % (c, sq.get(c), nv['nivel']))
    out += formato_sem_taxonomia(X)   # nos dois modos
    if not X.simulacao:   # §4.3: com SIMULACAO = False o gerador não emite rota, histórico simulado, dia de bordo nem a posição do barco
        if 'rota' in X.D or 'destinos' in X.D:
            out.append('modo real: D.rota e D.destinos só na simulação (§4.3)')
        out += ['modo real: replay.%s só na simulação (o replay sai só com limites e alertas, §4.3)' % k for k in (X.R or {}) if k not in ('limites', 'alertas')]
        if 'historico' in X.D:
            out.append('modo real: D.historico só na simulação (§4.3)')
        if 'serie24v' in X.D:
            out.append('modo real: D.serie24v só na simulação (§4.3: o mín/máx sai do laço e do histórico simulados)')
        if isinstance(sq, dict) and ('lat' in sq or 'lon' in sq):
            out.append('modo real: snapshot.quadro sem posição enquanto o repositório for público (§4.3)')
        gps = (X.D.get('snapshot') or {}).get('gps')   # §4.3: «emitir snapshot.gps» com posição também é a posição do barco (lat, lon e o texto delas)
        if isinstance(gps, dict) and {'lat', 'lon', 'texto'} & set(gps):
            out.append('modo real: snapshot.gps sem lat, lon nem texto enquanto o repositório for público (§4.3)')
        out += ['modo real: %s (as fontes do Drive vão sem posição enquanto o repositório for público, §4.3)' % m for m in posicao_nas_fontes(X.fontes)]
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


def e_porao(c):
    """Campo de nível do porão (porao_bb_nivel, porao_be_nivel: §1.15)."""
    return isinstance(c, str) and c.startswith('porao_') and c.endswith('_nivel')


def teto_porao(X, c):
    """Teto do normal do porão (cm): o `normal.ate` do campo, sem número solto (§3.3, g_porao §2). Vem do D.replay.limites e da
    constante LIMITES do gerador (a FONTE_LIMITES confere que são a mesma); o menor dos que existirem. None sem nenhum."""
    tetos = []
    for lims in (X.limites, X.const.get('LIMITES')):
        L = lims.get(c) if isinstance(lims, dict) else None
        normal = L.get('normal') if isinstance(L, dict) else None
        v = normal.get('ate') if isinstance(normal, dict) else None
        if _num(v):
            tetos.append(v)
    return min(tetos) if tetos else None


def porao_no_normal(X):
    """PROMPT §2.4 («nada de ... água no porão acima do normal») e a coluna «Asserção do gerador» da §6.4 («JANELA, SEM_EMERGENCIA;
    porão ≤ 5 cm»), sem número solto: o teto é o normal.ate do porão (teto_porao). A JANELA aceita o aviso dentro da janela, e o
    porão não pode: nenhum nível do porão passa do teto, nem nas chaves do replay, nem em nenhum segundo do laço (ruído e
    arredondamento incluídos), nem em replay.fixos, em snapshot.quadro ou em snapshot.porao (bb_cm, be_cm), e nenhuma janela é de
    porão. Um campo de porão sem teto em lugar nenhum também reprova (não há como conferir). Uma violação por (campo, origem)."""
    out = []
    R = X.R or {}
    snap = X.D.get('snapshot') if isinstance(X.D.get('snapshot'), dict) else {}
    quadro = snap.get('quadro') if isinstance(snap.get('quadro'), dict) else {}
    aninhado = snap.get('porao') if isinstance(snap.get('porao'), dict) else {}
    leituras = []   # (origem, caminho, campo, valor)
    for c, ch in (R.get('chaves') or {}).items():
        if e_porao(c) and isinstance(ch, list):
            leituras += [('chaves', 'replay.chaves.%s[%d]' % (c, i), c, v) for i, v in enumerate(ch)]
    leituras += [('fixos', 'replay.fixos.' + c, c, v) for c, v in (R.get('fixos') or {}).items() if e_porao(c)]
    for t, q in enumerate(X.laco()):
        leituras += [('laço', 'replay (laço), %s em t = %d' % (c, t), c, v) for c, v in q.items() if e_porao(c)]
    leituras += [('quadro', 'snapshot.quadro.' + c, c, v) for c, v in quadro.items() if e_porao(c)]
    leituras += [('aninhado', 'snapshot.porao.' + k, 'porao_%s_nivel' % k[:2], aninhado[k]) for k in ('bb_cm', 'be_cm') if k in aninhado]
    vistos = set()
    for origem, cam, c, v in leituras:
        teto = teto_porao(X, c)
        if teto is None:
            if (c, None) not in vistos:
                vistos.add((c, None))
                out.append('%s: sem normal.ate em D.replay.limites nem na constante LIMITES: sem o teto do normal (g_porao §2) não há como conferir o porão' % c)
        elif _num(v) and v > teto and (c, origem) not in vistos:
            vistos.add((c, origem))
            out.append('%s = %s: acima do normal (até %s cm); o replay não gera água no porão acima do normal, nem dentro de janela (PROMPT §2.4)' % (cam, v, teto))
    for j in R.get('janelas') if isinstance(R.get('janelas'), list) else []:
        if isinstance(j, dict) and e_porao(j.get('campo')):
            out.append('replay.janelas.%s: janela de porão (campo %s); o replay não gera água no porão acima do normal (PROMPT §2.4)' % (j.get('id'), j.get('campo')))
    return out


def a_janela(X):
    out = porao_no_normal(X)
    R = X.R
    if R is None or not R.get('chaves'):
        return out
    js = R.get('janelas')
    if not isinstance(js, list):
        return ['replay.janelas ausente (derivadas pelo gerador, §1.16)']
    por_id = {}
    for j in js:
        por_id.setdefault(j.get('id'), []).append(j)
        if j.get('ini', 0) <= 60 <= j.get('fim', -1):
            out.append('replay.janelas.%s cobre t = 60' % j.get('id'))
    # §6.3 JANELA: «cada janela ⊂ [95, 120] e ≥ 10 s». Só o cenário alarme-critico (§3.5) tem aviso → crítico → aviso no MESMO id: ali as
    # janelas do id têm de ser contíguas (a seguinte começa no segundo depois do fim da anterior) e a duração é a da união. No cenário aviso
    # (§3.4: «contínua, 18 s») a regra é por janela: uma janela partida em duas curtas (8 s + 3 s) não passa pela soma (revisão do C8).
    uniao = R.get('cenario') == 'alarme-critico'
    for i, g in por_id.items():
        g = sorted(g, key=lambda j: j.get('ini', -1))
        if uniao:
            for a, b in zip(g, g[1:]):
                if b.get('ini', -1) != a.get('fim', -2) + 1:
                    out.append('replay.janelas.%s: as janelas do mesmo id precisam ser contíguas (%s–%s e %s–%s)' % (i, a.get('ini'), a.get('fim'), b.get('ini'), b.get('fim')))
            blocos = [(g[0].get('ini', -1), g[-1].get('fim', -1))]
        else:
            blocos = [(j.get('ini', -1), j.get('fim', -1)) for j in g]
        for ini, fim in blocos:
            if not (95 <= ini <= fim <= 120 and fim - ini + 1 >= 10):
                out.append('replay.janelas.%s: precisa ficar em [95, 120] e durar ≥ 10 s (%s–%s)' % (i, ini, fim))
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
    # O dia de bordo inteiro (§6.3 «fora das janelas, todo valor por segundo dentro do normal»; PROMPT §2.4: o replay só gera o AVISO planejado).
    # O laço acima só cobre os 150 s: os contadores (diesel e os três tanques) e a profundidade da rota andam as 24 h, e uma taxa por hora mexida
    # (cinzas a 3,5 %/h passava de 80 % às 03:35) ou um tanque de partida alto não acusava nada. As janelas só existem para o laço
    # (deriva_janelas): contador e rota fora do normal em qualquer segundo reprovam.
    P, _ = X.port()
    if P is not None:
        for c, d in sorted(varredura_dia(P)['limites'].items()):
            for n in ('aviso', 'critico'):
                if n in d['niveis']:
                    seg, v = d['niveis'][n]
                    out.append('%s = %s às %s do dia de bordo (%s) fora das janelas' % (c, v, hora_do_dia(R, seg), n))
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
    # O dia de bordo inteiro (contador, tanque e profundidade; o laço de 150 s acima não os cobre): o primeiro segundo a menos de 0,05 de um limite.
    P, _ = X.port()
    if P is not None:
        for c, d in sorted(varredura_dia(P)['limites'].items()):
            if d['perto'] and c not in vistos:
                seg, v, lim = d['perto']
                out.append('%s = %s às %s do dia de bordo, a menos de 0,05 do limite %s' % (c, v, hora_do_dia(X.R, seg), lim))
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
    P, erro = X.port()
    if P is None:
        out.append('emendas de 150 s da rota: o port do em() não rodou (%s)' % erro)
        return out
    V = varredura_dia(P)
    n = P['n']
    hhmmss = lambda seg: hora_do_dia(X.R, seg)
    for N, (passo, ev) in sorted(V['emendas'].items()):
        if ev:   # nenhuma chegada (ponto, destino ou ETA) cai no par em(N·150 − 1 s) × em(N·150)
            out.append('emenda %d (%s): a chegada cai no par de segundos consecutivos (%s mudam)' % (N, hhmmss(N * n), ', '.join(ev)))
        for c, d in passo.items():
            if d - V['max'][c] > 1e-9:
                out.append('emenda %d (%s): %s salta %s, mais que o maior passo de 1 s do dia (%s)' % (N, hhmmss(N * n), c, round(d, 6), round(V['max'][c], 6)))
    # a virada em A (06:59:59 → 07:00:00): a posição, o rumo e a profundidade são contínuos; saltam só os contadores e os campos da rota que recomeça
    for c in ('lat', 'lon', 'cog_graus', 'profundidade_m'):
        if V['A'][c] - V['max'][c] > 1e-9:
            out.append('virada em A: %s salta %s, mais que o maior passo de 1 s do dia (%s)' % (c, round(V['A'][c], 6), round(V['max'][c], 6)))
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
        if not (_num(rota.get('fator')) and 0.9 <= rota['fator'] <= 1.0):
            out.append('rota.fator %r fora de [0,9; 1,0]: a posição anda no máximo o que o odômetro soma (§1.14)' % rota.get('fator'))
    # as pernas pré-calculadas (o cliente não as recalcula) são as dos pontos: ordem, distância, rumo, início, circuito e ida
    if len(pernas) != len(pts):
        out.append('rota.pernas: %d pernas para %d pontos' % (len(pernas), len(pts)))
    ini = 0.0
    for i, p in enumerate(pernas[:len(pts)]):
        a_, b_ = pts[i], pts[(i + 1) % len(pts)]
        if (p.get('de'), p.get('para')) != (a_.get('id'), b_.get('id')):
            out.append('rota.pernas[%d] vai de %r para %r, a ordem dos pontos pede %r para %r' % (i, p.get('de'), p.get('para'), a_.get('id'), b_.get('id')))
            continue
        pa, pb = (a_.get('lat'), a_.get('lon')), (b_.get('lat'), b_.get('lon'))
        if not all(_num(x) for x in pa + pb):
            out.append('rota.%s ou rota.%s sem lat e lon numéricos' % (a_.get('id'), b_.get('id')))
            continue
        if not _num(p.get('mn')) or abs(p['mn'] - mn_entre(pa, pb)) > 0.0005:
            out.append('rota.pernas[%d].mn %r ≠ a distância entre os pontos (%.4f)' % (i, p.get('mn'), mn_entre(pa, pb)))
        if not _num(p.get('rumo')) or abs(_wrap(p['rumo'] - rumo_entre(pa, pb))) > 0.01:
            out.append('rota.pernas[%d].rumo %r ≠ o rumo entre os pontos (%.2f)' % (i, p.get('rumo'), rumo_entre(pa, pb)))
        if not _num(p.get('ini_mn')) or abs(p['ini_mn'] - ini) > 0.0005:
            out.append('rota.pernas[%d].ini_mn %r ≠ a soma das pernas anteriores (%.4f)' % (i, p.get('ini_mn'), ini))
        ini += p.get('mn') or 0
    if not _num(rota.get('distancia_mn')) or abs(rota['distancia_mn'] - ini) > 0.001:
        out.append('rota.distancia_mn %r ≠ a soma das pernas (%.4f)' % (rota.get('distancia_mn'), ini))
    ida = next((p.get('ini_mn') for p in pernas if p.get('de') == (rota.get('destino') or {}).get('id')), None)
    if not _num(rota.get('ida_mn')) or ida is None or abs(rota['ida_mn'] - ida) > 0.0005:
        out.append('rota.ida_mn %r ≠ a distância da base ao destino (%r)' % (rota.get('ida_mn'), ida))
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
        P, _ = X.port()
        if P is not None and _num(cap_):   # litros e níveis = o salto do contador entre A − 1 s e A (o abastecimento é o próprio salto, às 07:00)
            dia = P['n'] * R['por_dia']['voltas']
            antes, depois = em(P, dia - 1, com_alarmes=False), em(P, 0, com_alarmes=False)
            if ab.get('litros') != depois['diesel_litros'] - antes['diesel_litros']:
                out.append('diaDeBordo.abastecimento.litros (%s) ≠ o salto do contador entre A − 1 s e A (%s → %s)' % (ab.get('litros'), antes['diesel_litros'], depois['diesel_litros']))
            if ab.get('nivelAntes') != arred(antes['diesel_litros'] / cap_ * 100, 1) or ab.get('nivelDepois') != arred(depois['diesel_litros'] / cap_ * 100, 1):
                out.append('diaDeBordo.abastecimento: nivelAntes/nivelDepois ≠ o diesel % de em(A − 1 s) e de em(A)')
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
    nomes_seg = {i: [n for j, n in nomes_equip(X) if j == i] for i in EQUIP_SEGURANCA}
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
        if any(next(acha_nomes(t.get('equip', ''), n), None) for n in nomes_seg.get(t.get('sistema'), [])):   # uma por tarefa
            out.append('agenda.%s.equip com fabricante ou modelo de equipamento de segurança' % i)
    atr = sum(1 for t in X.agenda if _num(t.get('venceEm')) and t['venceEm'] < 0)
    if atr != 3:
        out.append('agenda: %d atrasadas (precisa de 3)' % atr)
    return out


# HISTORICO (§1.13, §6.3). Janelas dos gráficos: o balde de cada uma é múltiplo de 150 s (e alinhado às 07:00), e passo_s × n é a duração dela.
DURACAO_JANELA_S = {'1D': 86400, '7D': 7 * 86400, '30D': 30 * 86400, '1A': 365 * 86400}
# Campos de grupo so150 que não são do laço mas derivam dele (§1.22: STW = SOG − corrente·cos(COG − rumo)): vão na mesma janela de 150 s da SOG
# (grupo `navegacao`, §1.13). Qualquer outro derivado (diesel_bb_pct, proa…) em so150 reprova.
SO150_DERIVADOS_DO_LACO = ('stw_nos',)
CRUZEIRO_CAMPOS = ('motor_bb_arref_c', 'motor_be_arref_c', 'motor_bb_oleo_bar', 'motor_be_oleo_bar')   # as quatro médias de cruzeiro da F11
TEMPERATURAS_CURVA = ('temp_ar_externo_c', 'temp_agua_c')   # ar e água: desvio do dia + curva do ano (a praça acompanha o ar)
CURVA_MIN_C = 4.0   # a curva do ano do ar e da água varia pelo menos isto de ponta a ponta (o contrato dá 9 e 7); 30 D e 1 A não saem retos
SERIE24V_TOL = 0.006   # V: o mín/máx da série 24 V vs o laço + o desvio do dia, com o arredondamento de 2 casas


def _inteiros(d, n=None):
    return isinstance(d, list) and (n is None or len(d) == n) and all(isinstance(x, int) and not isinstance(x, bool) for x in d)


def _media(v):
    return sum(v) / len(v)


def _obj(x):
    return x if isinstance(x, dict) else {}   # bloco fora da forma: a asserção acusa a falta, nunca levanta exceção


def _serie_ok(s):
    """Série {escala, d} bem formada (escala inteira positiva, d de inteiros, não vazia): a forma já reprovou nas outras, aqui só se confere o número."""
    return isinstance(s, dict) and isinstance(s.get('escala'), int) and not isinstance(s['escala'], bool) and s['escala'] > 0 and _inteiros(s.get('d')) and len(s['d']) > 0


def a_historico(X):
    H = X.D.get('historico')
    if not isinstance(H, dict):
        return [] if not X.simulacao else ['historico ausente na simulação (§1.13: desvios, curva do ano, médias de cruzeiro, janelas)']
    out = []
    met = {g: cs for g, cs in _obj(H.get('metricas')).items() if isinstance(cs, list)}
    # ——— forma (§1.13): tudo em inteiros com escala; os comprimentos acompanham n, o da tabela do ano e os dias de cruzeiro
    if H.get('fim') != 'ancora':
        out.append("historico.fim ≠ 'ancora' (o último dia guardado termina na âncora do dia de bordo atual)")
    passo, n = H.get('passo_dias'), H.get('n')
    if not (isinstance(passo, int) and isinstance(n, int) and not isinstance(passo, bool) and not isinstance(n, bool) and passo > 0 and n > 0):
        out.append('historico.passo_dias e historico.n precisam ser inteiros positivos')
        passo = n = 0
    elif passo * n < 366:
        out.append('historico: n × passo_dias (%d) não cobre os 366 dias do ano' % (passo * n))
    saz = _obj(H.get('sazonal'))
    if saz.get('passo_dias') is not None or saz.get('n') is not None:
        if (saz.get('passo_dias'), saz.get('n')) != (5, 73):
            out.append('historico.sazonal: passo_dias e n precisam ser 5 e 73 (a tabela do ano, 73 × 5 = 365 dias): %r e %r' % (saz.get('passo_dias'), saz.get('n')))
    else:
        out.append('historico.sazonal sem passo_dias e n')
    dias = _obj(H.get('cruzeiro')).get('dias')
    if not (isinstance(dias, int) and not isinstance(dias, bool) and dias > 0):
        out.append('historico.cruzeiro.dias precisa ser inteiro positivo')
        dias = 0
    for grupo, comp in (('desvios', n), ('sazonal', 73), ('cruzeiro', dias)):
        for c, s in _obj(H.get(grupo)).items():
            if not (isinstance(s, dict) and isinstance(s.get('d'), list)):
                continue
            e = s.get('escala')
            if not (isinstance(e, int) and not isinstance(e, bool) and e > 0):
                out.append('historico.%s.%s.escala precisa ser inteiro positivo' % (grupo, c))
            if not all(_num(x) for x in s['d']):
                out.append('historico.%s.%s com valor não finito' % (grupo, c))
            elif not _inteiros(s['d']):
                out.append('historico.%s.%s com valor não inteiro (valor real = d / escala)' % (grupo, c))
            if grupo != 'sazonal' and comp and len(s['d']) != comp:   # a curva do ano tem a mensagem própria («sem 73 pontos»)
                out.append('historico.%s.%s com %d pontos (precisa de %d)' % (grupo, c, len(s['d']), comp))
            if grupo == 'desvios' and len(set(s['d'])) < 2:
                out.append('historico.desvios.%s sem variação (a série de 30 D e 1 A sairia reta)' % c)
    out += ['historico.metricas.%s: %r fora de D.campos' % (g, c) for g, cs in met.items() for c in cs if c not in X.campos]
    if not (isinstance(H.get('fonte'), str) and H['fonte'].strip()):
        out.append('historico.fonte ausente')
    # ——— janelas dos gráficos
    jan = _obj(H.get('janelas'))
    if jan.get('150S') != {'passo_s': 1, 'n': 150}:
        out.append("historico.janelas['150S'] ≠ {passo_s: 1, n: 150}")
    for k, dur in DURACAO_JANELA_S.items():
        w = jan.get(k)
        if not (isinstance(w, dict) and isinstance(w.get('passo_s'), int) and isinstance(w.get('n'), int)):
            out.append('historico.janelas[%r] ausente ou fora da forma {passo_s, n}' % k)
        elif w['passo_s'] * w['n'] != dur or w['passo_s'] % 150:
            out.append('historico.janelas[%r] = %s: passo_s × n precisa dar %d s, com o balde múltiplo de 150 s' % (k, w, dur))
    # ——— so150: grupos só do laço (a volta se repete nas janelas longas); o resto precisa de desvio ou ser contador
    for g in H.get('so150') or []:
        if g not in met:
            out.append('historico.so150: %r fora das métricas' % g)
        elif any((X.campos.get(c) or {}).get('origem') != 'laço' and c not in SO150_DERIVADOS_DO_LACO for c in met[g]):
            out.append('historico.so150: %r tem campo fora do laço' % g)
    des = _obj(H.get('desvios'))
    for g, cs in met.items():
        if g in (H.get('so150') or []):
            continue
        for c in cs:
            org = (X.campos.get(c) or {}).get('origem')
            if org == 'laço' and c not in des and c != 'temp_praca_maquinas_c':   # a praça acompanha o ar externo (desvio + curva do ano)
                out.append('historico.metricas.%s: %s é do laço e não tem desvio (a janela longa sairia reta; só os grupos do laço ficam em so150)' % (g, c))
    for c in TEMPERATURAS_CURVA:
        if c in X.campos:
            for grupo in ('desvios', 'sazonal'):
                if not isinstance(_obj(H.get(grupo)).get(c), dict):
                    out.append('historico.%s sem %s (ar e água levam o desvio do dia e a curva do ano)' % (grupo, c))
    for c in CRUZEIRO_CAMPOS:
        if c in X.campos and not isinstance(_obj(H.get('cruzeiro')).get(c), dict):
            out.append('historico.cruzeiro sem %s (média de cruzeiro da F11)' % c)
    for c, s in saz.items():
        if isinstance(s, dict) and len(s['d'] if isinstance(s.get('d'), list) else []) != 73:
            out.append('historico.sazonal.%s sem 73 pontos' % c)
        elif isinstance(s, dict) and _inteiros(s.get('d')):
            ponta = (max(s['d']) - min(s['d'])) / (s.get('escala') or 1)
            dia_max, dia_min = 5 * s['d'].index(max(s['d'])), 5 * s['d'].index(min(s['d']))
            if ponta < CURVA_MIN_C:
                out.append('historico.sazonal.%s varia só %.1f °C no ano (a curva precisa de %.1f °C pelo menos: 30 D e 1 A sairiam retos)' % (c, ponta, CURVA_MIN_C))
            elif not ((dia_max >= 335 or dia_max <= 105) and 135 <= dia_min <= 285):   # verão de dez a mar, inverno de jun a set (hemisfério sul)
                out.append('historico.sazonal.%s: o máximo cai no dia %d e o mínimo no dia %d do ano (litoral de SC: máximo de dezembro a março, mínimo de junho a setembro)' % (c, dia_max, dia_min))
    # ——— nenhum valor cruza limite (desvios + laço; cruzeiro; praça + desvio do ar + curva); só as séries bem formadas (a forma reprovou acima)
    Q = X.laco()
    if Q:
        ar, sz = des.get('temp_ar_externo_c'), saz.get('temp_ar_externo_c')
        d_ar = max([x / ar['escala'] for x in ar['d']]) if _serie_ok(ar) else 0
        d_saz = (max(sz['d']) - min(sz['d'])) / sz['escala'] if _serie_ok(sz) else 0
        for c, s in des.items():
            if c not in Q[0] or not _serie_ok(s):
                continue
            vs = [q[c] for q in Q]
            dmin, dmax = min(s['d']) / s['escala'], max(s['d']) / s['escala']
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
        out += _cruzeiro(X, H, Q)
        out += _serie24v(X, H, Q)
    return out


def _cruzeiro(X, H, Q):
    """Médias de cruzeiro (F11): dentro do normal, com a folga de 0,05, no regime de cruzeiro; e o BE sobe em relação ao BB até o valor de hoje
    (média do laço na fase de cruzeiro), que é o que o achado «Motor BE N °C acima do BB em cruzeiro, subindo há 60 dias» conta."""
    out = []
    cz = _obj(H.get('cruzeiro'))
    for c in CRUZEIRO_CAMPOS:
        s = cz.get(c)
        if not (isinstance(s, dict) and _inteiros(s.get('d')) and isinstance(s.get('escala'), int) and s['escala'] > 0):
            continue
        for v in s['d']:
            x = v / s['escala']
            # em cruzeiro (2.050 rpm, motores girando): o óleo muda de regime com a rotação e o arrefecimento só vale com o motor ligado
            bom = all((nivel(X.limites, X.campos, c, {'motor_bb_rpm': 2050, 'motor_be_rpm': 2050, c: x + e}) or {}).get('nivel', 'normal') == 'normal'
                      for e in (-0.05, 0, 0.05))
            if not bom:
                out.append('historico.cruzeiro.%s: %s cruza o normal (ou fica a menos de 0,05 do limite)' % (c, x))
                break
    bb, be = cz.get('motor_bb_arref_c'), cz.get('motor_be_arref_c')
    fase = next((f for f in ((X.R or {}).get('fases') or []) if f.get('nome') == 'cruzeiro'), None)
    if fase and isinstance(bb, dict) and isinstance(be, dict) and _inteiros(bb.get('d')) and _inteiros(be.get('d')) and len(bb['d']) == len(be['d']) >= 30 \
            and Q and 'motor_be_arref_c' in Q[0] and 'motor_bb_arref_c' in Q[0]:
        seg = Q[fase['ini']:fase['fim']]
        hoje = _media([q['motor_be_arref_c'] for q in seg]) - _media([q['motor_bb_arref_c'] for q in seg])
        dif = [b / be['escala'] - a / bb['escala'] for a, b in zip(bb['d'], be['d'])]
        if _media(dif[-15:]) - _media(dif[:15]) < 0.5:
            out.append('historico.cruzeiro: o BE não sobe em relação ao BB (F11: «subindo há %d dias»): %.1f → %.1f °C' % (len(dif), _media(dif[:15]), _media(dif[-15:])))
        if not dif[-1] < hoje:
            out.append('historico.cruzeiro: ontem o BE estava %.1f °C acima do BB e hoje, pelo laço, %.1f (a série precisa subir até hoje)' % (dif[-1], hoje))
    return out


def _serie24v(X, H, Q):
    """serie24v (L, §1.13): 7 itens {diasAtras: 6…0, min, max, d}; o mín/máx de hoje é o da volta do banco de serviço, e os dos outros dias são o da
    volta mais o desvio do dia (o mesmo deslocamento nos dois); dentro do normal, com a folga de 0,05."""
    sv = X.D.get('serie24v')
    if not isinstance(sv, list) or not sv:
        return ['serie24v ausente na simulação (§1.13: 7 dias de mín/máx do banco de serviço)']
    if not all(isinstance(x, dict) for x in sv):
        return ['serie24v: cada dia precisa ser {diasAtras, min, max, d}']
    c = 'bateria_0_tensao_v'
    s = _obj(H.get('desvios')).get(c)
    n, passo = H.get('n'), H.get('passo_dias')
    if c not in Q[0] or not (isinstance(s, dict) and isinstance(n, int) and isinstance(passo, int) and passo > 0 and _inteiros(s.get('d'), n)
                             and isinstance(s.get('escala'), int) and s['escala'] > 0):
        return []   # sem o desvio de referência bem formado (a forma já reprovou acima), não há o que comparar
    out = []
    if [x.get('diasAtras') for x in sv] != list(range(6, -1, -1)):
        out.append('serie24v: diasAtras precisa ser 6…0 (7 dias): %r' % [x.get('diasAtras') for x in sv])
    vs = [q[c] for q in Q]
    nrm = (X.limites.get(c) or {}).get('normal') or {}
    for x in sv:
        if not (_num(x.get('min')) and _num(x.get('max')) and _num(x.get('diasAtras'))):
            out.append('serie24v[%s] sem min e max numéricos' % x.get('diasAtras'))
            continue
        dev = desvio_em(H, c, x['diasAtras'])
        if x['min'] >= x['max']:
            out.append('serie24v[%d]: min (%s) não é menor que max (%s)' % (x['diasAtras'], x['min'], x['max']))
        if abs(x['min'] - (min(vs) + dev)) > SERIE24V_TOL or abs(x['max'] - (max(vs) + dev)) > SERIE24V_TOL:
            out.append('serie24v[%d]: %s a %s ≠ o mín/máx da volta (%s a %s) mais o desvio do dia (%+.3f V)' % (x['diasAtras'], x['min'], x['max'], min(vs), max(vs), dev))
        if ('de' in nrm and x['min'] < nrm['de'] + 0.05 - 1e-9) or ('ate' in nrm and x['max'] > nrm['ate'] - 0.05 + 1e-9):
            out.append('serie24v[%d]: %s a %s cruza o normal (%s a %s V)' % (x['diasAtras'], x['min'], x['max'], nrm.get('de'), nrm.get('ate')))
    return out


def a_coord_texto(X):
    """Uma violação por ocorrência, como as outras de texto. A exceção do snapshot.gps.texto (§1.17: enquanto houver leitor) é só da simulação:
    no modo real o texto da posição do barco não sai (§4.3)."""
    return ['%s «%s»' % (cam, trecho(s, m)) for cam, s in X.todos() if (cam != 'snapshot.gps.texto' or not X.simulacao) for m in R_COORD.finditer(s)]


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


def a_seguranca_curta(X):
    return ['base:trechos[%d] (%s · %s): %d letras com seguranca (máximo %d: o cérebro lê o trecho inteiro, e a fala também)'
            % (i, t.get('fonte'), t.get('secao'), len(t.get('texto', '')), SEGURANCA_MAX_LETRAS)
            for i, t in enumerate(X.trechos) if t.get('seguranca') and len(t.get('texto', '')) > SEGURANCA_MAX_LETRAS]


def a_seguranca_sem_modelo(X):
    """Trava 17 (PROMPT §2.3; CONTRATO §1.4): fabricante, modelo e validade do EPIRB e do Seafire só em Equipamentos, Leme e Documentos.
    Revisão 7 do C5: a PROTOCOLO_LIMPO e a AGENDA só olhavam o D.protocolos e o campo equip da agenda; o nome, o modelo ou a validade
    escritos num guia, no protocolo, na base, no FAQ ou numa página de fonte passavam. Três regras:
      (1) fabricante e modelo (cada palavra e as formas juntas, nomes_seguranca) em todo texto do D, da base, do FAQ e das fontes, fora
          as telas acima (D_EQUIP_DOC_LEME, FONTES_EQUIP_DOC_LEME) e o título «Incêndio · Seafire» do protocolo (§1.5);
      (2) validade (R_VALIDADE: data, ano, mês, «vence em 180 dias») nos guias inteiros de segurança (g_seafire, g_epirb e o protocolo:
          trechos, itens EM/SF/EP do FAQ, páginas de fonte) e no D.protocolos: o prazo vem da agenda e do documento, que o rebase mantém;
      (3) lugar a bordo (a lista da LOCAL_SEGURANCA, em qualquer frase) nos mesmos guias: a LOCAL_VOCAB só pega o lugar na frase do
          equipamento («Fica no paiol de proa.» num guia do EPIRB passava)."""
    out = []
    ids = set(EQUIP_SEGURANCA) | {e.get('id') for e in X.equip if e.get('seguranca') is True}
    nomes = []
    for i, n in nomes_equip(X):
        if i in ids and n.lower() not in [x.lower() for x in nomes]:
            nomes.append(n)
    for cam, s in X.todos():
        if cam.split('.')[0].split('[')[0] in D_EQUIP_DOC_LEME or (cam.startswith('fontes/') and cam.endswith(FONTES_EQUIP_DOC_LEME)):
            continue
        t = s.replace(SECAO_SEAFIRE, ' ' * len(SECAO_SEAFIRE))
        achados = [m for n in nomes for m in acha_nomes(t, n)]
        for m in achados:   # uma violação por ocorrência: o nome dentro de outro («Ocean» em «Ocean Signal») não conta duas vezes
            a, b = m.span(1)
            if not any(c <= a and b <= d and (c, d) != (a, b) for c, d in (x.span(1) for x in achados)):
                out.append('%s: fabricante ou modelo de equipamento de segurança [%s] «%s»' % (cam, m.group(1), trecho(t, m)))

    def valida(cam, s, lugar=True):
        out.extend('%s: validade ou data num texto do EPIRB, do Seafire ou do protocolo [%s] «%s»' % (cam, casado(m), trecho(s, m)) for m in R_VALIDADE.finditer(s))
        if lugar:
            out.extend('%s: lugar a bordo num texto do EPIRB, do Seafire ou do protocolo [%s] «%s»' % (cam, casado(m), trecho(s, m)) for m in X.lugar.finditer(s))

    guias = {X.arq[k] for k in GUIAS_DE_SEGURANCA if X.arq.get(k)}
    for i, t in enumerate(X.trechos):
        if t.get('fonte') in guias:
            valida('base:trechos[%d] (%s · %s)' % (i, t.get('fonte'), t.get('secao')), ' '.join(str(t.get(k) or '') for k in ('fonte', 'secao', 'texto', 'equip')))
    for it in X.itens_faq:
        if FAQ_DE_SEGURANCA.fullmatch(str(it.get('id', ''))):
            for cam, s in textos(it, 'faq:%s' % it.get('id')):
                valida(cam, s)
    for rel, txt in sorted(X.fontes.items()):
        if any(rel.endswith('/' + g + '.html') for g in guias):
            valida('fontes/' + rel, re.sub(r'<[^>]*>', '\n', txt))
    for cam, s in textos(X.D.get('protocolos'), 'protocolos'):
        valida(cam, s, lugar=False)   # o lugar a bordo do protocolos é da PROTOCOLO_LIMPO
    return out


def palavras_de_nome(X):
    """Palavras (norm, 3 letras ou mais) que nomeiam equipamento ou sistema, tiradas do próprio dado: nome, fabricante, modelo e
    palavras de cada equipamento; fonte e equip de cada trecho da base; títulos dos guias; e o título de toda seção sem `ident` ("Ligar",
    "Partida", "Alarmes", "Manutenção na agenda"). O título de uma seção com `ident` fica de fora ("Homem ao mar" é dele)."""
    def toks(v):
        return {w for w in re.findall(r'[a-z0-9]+', norm(v)) if len(w) >= 3}
    out = set()
    for e in X.equip:
        for k in ('nome', 'fabricante', 'modelo'):
            out |= toks(e.get(k))
        for p in e.get('palavras') or []:
            out |= toks(p)
    for t in X.trechos:
        out |= toks(t.get('fonte')) | toks(t.get('equip'))
        if 'ident' not in t:
            out |= toks(t.get('secao'))
    for tit in ((X.D.get('guias') or {}).values()):
        out |= toks(tit)
    return out


def a_ident_base(X):
    """`ident` só em trecho com seguranca: de 1 a 6 palavras minúsculas de 3 letras ou mais, sem verbo de operação (qualquer flexão),
    sem nome de equipamento ou de sistema (os do dado e a lista fixa IDENT_PROIBIDAS) e sem "pessoa"/"alguém" (sem distinguir acento).
    `ident` com palavra de queda ou de vista ("caiu", "cair", "vista", "mar") pede `identCom`: de 1 a 8 palavras da lista fechada de pessoa
    (IDENT_PESSOA_OK); `identCom` sem `ident` não tem o que destravar. Sem isso o cérebro não nomeia o trecho pela situação (ou o nomeia
    por "o disjuntor caiu" e "tem vista para o mar")."""
    proibidas = {norm(w) for w in IDENT_PROIBIDAS} | palavras_de_nome(X)
    out = []
    for i, t in enumerate(X.trechos):
        onde = 'base:trechos[%d] (%s · %s)' % (i, t.get('fonte'), t.get('secao'))
        if 'identCom' in t and 'ident' not in t:
            out.append('%s: identCom sem ident' % onde)
        if 'ident' not in t:
            continue
        ident = t['ident']
        palavras = ident.split(' ') if isinstance(ident, str) else []
        if t.get('seguranca') is not True:
            out.append('%s: ident sem seguranca: true' % onde)
        if not (1 <= len(palavras) <= 6) or not all(re.fullmatch(r'[a-zà-ú]{3,}', w) for w in palavras):
            out.append('%s: ident precisa de 1 a 6 palavras minúsculas de 3 letras ou mais (%r)' % (onde, ident))
        nw = [norm(w) for w in palavras]
        ruins = sorted(w for w, n in zip(palavras, nw) if n in proibidas or n.startswith(IDENT_VERBOS_RAIZ) or n in IDENT_VERBOS_EXATOS)
        if ruins:
            out.append('%s: ident com verbo de operação ou nome de equipamento (%s)' % (onde, ', '.join(ruins)))
        pessoa = sorted(w for w, n in zip(palavras, nw) if n in IDENT_PESSOA_PROIBIDA)
        if pessoa:
            out.append('%s: ident com palavra de pessoa (%s); ela vai em identCom' % (onde, ', '.join(pessoa)))
        com = t.get('identCom')
        if com is None:
            queda = sorted(w for w, n in zip(palavras, nw) if n in IDENT_EXIGE_PESSOA)
            if queda:
                out.append('%s: ident com palavra de queda ou de vista (%s) sem identCom' % (onde, ', '.join(queda)))
            continue
        cw = com.split(' ') if isinstance(com, str) else []
        if not (1 <= len(cw) <= 8) or any(norm(w) not in IDENT_PESSOA_OK for w in cw):
            out.append('%s: identCom precisa de 1 a 8 palavras de pessoa da lista fechada (%r)' % (onde, com))
    return out


def a_nota_etiqueta(X):
    """As quatro notas são uma constante só (§1.4, §1.3): equipamentos[epirb|seafire].nota = protocolos.epirb|seafire.nota. Desde o
    C6 o protocolos.epirb e o protocolos.seafire existem (antes, só a primeira igualdade): sem o objeto ou sem a nota, reprova."""
    nota = NOTA
    out = []
    if X.const.get('NOTA_ETIQUETA', NOTA) != NOTA:   # a constante do gerador é o texto fixo do §1.4
        out.append('NOTA_ETIQUETA do gerador ≠ o texto do §1.4 (%r)' % NOTA)
    P = X.D.get('protocolos')
    for i in ('epirb', 'seafire'):
        e = X.eq(i)
        if e is not None and e.get('nota') != nota:
            out.append('equipamentos[%s].nota ≠ NOTA_ETIQUETA' % i)
        if isinstance(P, dict):
            p = P.get(i)
            if not isinstance(p, dict) or p.get('nota') != nota:
                out.append('protocolos.%s.nota ≠ NOTA_ETIQUETA' % i)
    return out


def _campo(P, caminho):
    """O texto de um campo do protocolos pelo caminho de PROTOCOLOS_NOS_GUIAS ('seafire.passos', 'epirb.passos[:3]', 'epirb.passos[3]'),
    com as listas juntas por espaço; None se faltar."""
    nome, _, fat = caminho.partition('[')
    v = P
    for k in nome.split('.'):
        v = v.get(k) if isinstance(v, dict) else None
    if fat:
        if not isinstance(v, list):
            return None
        try:
            v = v[_corte(fat[:-1])]
        except IndexError:
            return None
    if isinstance(v, list):
        return ' '.join(v) if all(isinstance(x, str) for x in v) else None
    return v if isinstance(v, str) else None


def _corte(txt):
    """'3' → 3; ':3' → slice(None, 3) (só estas duas formas, sem eval)."""
    if ':' in txt:
        a, _, b = txt.partition(':')
        return slice(int(a) if a else None, int(b) if b else None)
    return int(txt)


def a_protocolos(X):
    """A forma do D.protocolos (§1.3, C6): as chaves e os tipos, a quantidade de strings de cada lista, os textos que o contrato fixa
    (o MMSI_RADIO, o rótulo do MMSI, o indicativo, o plotter, o HUD, a salvatagem do PROMPT §2.3, o PAN-PAN e o DSC), o roteiro com o nome
    da embarcação (único dado gerado do SOS, §2.1) e o fim "conte agora", e a fonte única com os guias (PROTOCOLOS_NOS_GUIAS): cada
    texto do protocolos está inteiro na seção do guia que o repete; o guia ausente de drive.arquivos e a seção ausente da base reprovam."""
    P = X.D.get('protocolos')
    if not isinstance(P, dict):
        return ['protocolos ausente: a S1/S2 leem só embarcacao.nome e o D.protocolos (§1.3)']
    out = []
    esperadas = {'rotulo', 'fonte', 'canal16'} | set(PROTOCOLOS_TEXTOS) | set(PROTOCOLOS_LISTAS) | set(PROTOCOLOS_BLOCOS)
    out += ['protocolos.%s: chave que o §1.3 não tem' % k for k in P if k not in esperadas]
    for k in ('rotulo', 'fonte'):
        if not isinstance(P.get(k), str) or not P[k].strip():
            out.append('protocolos.%s: precisa de texto (§1.3)' % k)
    for k, fixo in PROTOCOLOS_TEXTOS.items():
        v = P.get(k)
        if not isinstance(v, str):
            out.append('protocolos.%s: precisa de texto (§1.3)' % k)
        elif v != fixo:
            out.append('protocolos.%s: diferente do texto do contrato (§1.3)' % k)
    for k, n in PROTOCOLOS_LISTAS.items():
        v = P.get(k)
        if not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v):
            out.append('protocolos.%s: precisa de uma lista de textos (§1.3)' % k)
        elif len(v) != n:
            out.append('protocolos.%s: %d texto(s), o §1.3 pede %d' % (k, len(v), n))
    for k, listas in PROTOCOLOS_BLOCOS.items():
        b = P.get(k)
        if not isinstance(b, dict):
            out.append('protocolos.%s: precisa de objeto com %s e nota (§1.3)' % (k, ' e '.join(listas)))
            continue
        out += ['protocolos.%s.%s: chave que o §1.3 não tem' % (k, c) for c in b if c not in set(listas) | {'nota'}]
        for c, n in listas.items():
            v = b.get(c)
            if not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v):
                out.append('protocolos.%s.%s: precisa de uma lista de textos (§1.3)' % (k, c))
            elif len(v) != n:
                out.append('protocolos.%s.%s: %d texto(s), o §1.3 pede %d' % (k, c, len(v), n))
        if not isinstance(b.get('nota'), str) or not b['nota'].strip():
            out.append('protocolos.%s.nota: precisa de texto (§1.3)' % k)
    c16 = P.get('canal16')
    if not isinstance(c16, dict) or set(c16) != {'canal', 'mhz', 'fonte'}:
        out.append('protocolos.canal16: precisa de {canal, mhz, fonte} (§1.3)')
    else:
        if c16['canal'] != '16' or c16['mhz'] != '156,800':
            out.append('protocolos.canal16: canal «16» em «156,800» MHz (§1.3)')
        if not isinstance(c16['fonte'], str) or not c16['fonte'].endswith(' · MAYDAY · canal 16') or not str(P.get('fonte', '')).startswith(c16['fonte'][:-len(' · MAYDAY · canal 16')]):
            out.append('protocolos.canal16.fonte: o título do protocolo, «MAYDAY» e «canal 16» (§1.3)')
    r = P.get('roteiro')
    if isinstance(r, list) and len(r) == PROTOCOLOS_LISTAS['roteiro'] and all(isinstance(x, str) for x in r):
        nome = ((X.D.get('embarcacao') or {}).get('nome') or '').upper()
        fixo = dict(ROTEIRO_FIXO)
        fixo[1] = 'AQUI É ' + ', '.join([nome] * 3)
        out += ['protocolos.roteiro[%d]: «%s», o §1.3 pede «%s»' % (i, r[i], t) for i, t in sorted(fixo.items()) if r[i] != t]
    # Fonte única: o texto do protocolos está inteiro na seção do guia que o repete. O guia ausente de drive.arquivos reprova, como a seção
    # ausente da base (§6.3: «a seção ausente reprova»): sem guia, o campo ficaria sem conferência de fonte única, em silêncio.
    for caminho, guias in PROTOCOLOS_NOS_GUIAS:
        txt = _campo(P, caminho)
        if txt is None:
            continue   # a forma já reprovou
        for chave, ini in guias:
            titulo = X.arq.get(chave)
            if not isinstance(titulo, str) or not titulo.strip():
                out.append('drive.arquivos.%s ausente (repete protocolos.%s, §1.3)' % (chave, caminho))
                continue
            sec = next((t for t in X.trechos if t.get('fonte') == titulo and str(t.get('secao', '')).startswith(ini)), None)
            if sec is None:
                out.append('base: %s · seção «%s…» ausente (repete protocolos.%s, §1.3)' % (titulo, ini, caminho))
            elif txt not in sec.get('texto', ''):
                out.append('base: %s · %s não repete protocolos.%s (fonte única, §1.3)' % (titulo, sec.get('secao'), caminho))
    # O roteiro MAYDAY falado (as linhas em branco sem o «: ________») está inteiro na seção MAYDAY do protocolo.
    if isinstance(P.get('roteiro'), list) and all(isinstance(x, str) for x in P['roteiro']):
        titulo = X.arq.get('protocolo')
        sec = next((t for t in X.trechos if t.get('fonte') == titulo and str(t.get('secao', '')).startswith('MAYDAY')), None)
        falado = ' — '.join(x.replace(': ________', '') for x in P['roteiro'])
        if not isinstance(titulo, str) or not titulo.strip():
            out.append('drive.arquivos.protocolo ausente (repete protocolos.roteiro, §1.3)')
        elif sec is None:
            out.append('base: %s · seção «MAYDAY…» ausente (repete protocolos.roteiro, §1.3)' % titulo)
        elif falado not in sec.get('texto', ''):
            out.append('base: %s · %s não repete protocolos.roteiro (fonte única, §1.3)' % (titulo, sec.get('secao')))
    return out


def grafias_seafire(s, pagina=False):
    """[(texto, casado)] das grafias do sistema fixo fora de «Seafire» e «seafire» em `s` (R_SEAFIRE: «Sea Fire», «Sea-Fire», «SEAFIRE»,
    «SeaFire»…). Numa página HTML, também no que o leitor vê (sem as tags e com as entidades): «Sea <b>fire</b>» e «Sea&nbsp;Fire» não
    casam no texto cru. A ocorrência que o cru já achou não conta duas vezes."""
    achados = [(s, m) for m in R_SEAFIRE.finditer(s) if m.group() not in SEAFIRE_GRAFIA]
    if pagina:
        visto = unescape(re.sub(r'<[^>]*>', '', s))
        ja = Counter(m.group() for _, m in achados)
        for m in R_SEAFIRE.finditer(visto):
            if m.group() in SEAFIRE_GRAFIA:
                continue
            if ja[m.group()] > 0:
                ja[m.group()] -= 1
            else:
                achados.append((visto, m))
    return achados


def a_grafia_seafire(X):
    """A grafia «Seafire» em todo dado (§1.3, «todas viram asserção»; decisão 3 do §8.2): nenhum valor string do D, da base, do FAQ e das
    fontes do Drive, nenhuma chave dessas mesmas peças (inclusive o cabeçalho dos CSV) e nenhum nome de arquivo das fontes escreve o sistema
    fixo de outro jeito: «Sea Fire», «Sea-Fire», «Sea_Fire», «SeaFire» ou «SEAFIRE». Uma violação por ocorrência. A única exceção são as
    `palavras` de busca dos equipamentos (PALAVRAS_BUSCA): é o que o ditado e o teclado escrevem, não texto do app."""
    out = []

    def acusa(cam, s, o_que, pagina=False):
        out.extend('%s: %s com a grafia «%s» do Seafire (§1.3: «Seafire», sem hífen nem espaço) «%s»' % (cam, o_que, m.group(), trecho(t, m))
                   for t, m in grafias_seafire(s, pagina))

    for cam, s in X.todos():
        if not PALAVRAS_BUSCA.fullmatch(cam):
            acusa(cam, s, 'texto', cam.startswith('fontes/') and cam.endswith('.html'))
    for cam, k in X.chaves():
        acusa(cam, k, 'chave')
    for rel in sorted(X.fontes):
        acusa('fontes/' + rel, rel, 'nome de arquivo')
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


# ——————————————————————————————— F08, F09, F12, F22 (C10; CONTRATO §1.18–§1.21) ———————————————————————————————
# A referência é daqui, nunca do dado conferido (como PROTOCOLOS_TEXTOS): os ids, os rótulos `c`, os ✓ automáticos e as faixas do contrato.
# Os textos `t` dos itens ficam só no gerador (a tabela do §1.18 os escreve por extenso, com a fonte de cada um no guia gerado).
CK_TIPOS = (   # §1.18: (id, l, aba, nome, sys); `l` é o rótulo da aba, `aba` a linha curta, `nome` o título da tela, `sys` a categoria do diário
    ('saida', 'Saída', 'antes de largar', 'Checklist de saída', 'Navegação'),
    ('chegada', 'Chegada', 'ao atracar', 'Checklist de chegada', 'Navegação'),
    ('abastecimento', 'Abastecimento', 'no posto', 'Checklist de abastecimento', 'Combustível'),
    ('fundeio', 'Fundeio', 'ao fundear', 'Checklist de fundeio', 'Navegação'))
CK_C = {   # id do item → `c` (o rótulo curto que entra na lista de pendentes do CONCLUIR)
    'saida': {'s01': 'previsão', 's02': 'alertas', 's03': 'motores frios', 's04': 'porão', 's05': 'diesel', 's06': 'tanques', 's07': 'baterias',
              's08': 'gerador', 's09': 'estabilizador', 's10': 'plotter e VHF', 's11': 'documentos', 's12': 'tarefas de segurança',
              's13': 'coletes e salvatagem', 's14': 'cabos e defensas'},
    'chegada': {'c01': 'piloto', 'c02': 'estabilizador', 'c03': 'motores', 'c04': 'gerador', 'c05': 'climatização', 'c06': 'porão',
                'c07': 'cabos e defensas', 'c08': 'diário'},
    'abastecimento': {'a01': 'motores', 'a02': 'gerador', 'a03': 'nível antes', 'a04': 'sem fumar', 'a05': 'bocal e tampa', 'a06': 'nível depois',
                      'a07': 'regra do diesel'},
    'fundeio': {'f01': 'profundidade', 'f02': 'corrente', 'f03': 'alarme de âncora', 'f04': 'deriva', 'f05': 'guincho', 'f06': 'maré e vento'}}
CK_AUTO = {   # id → (auto, parcial): o ✓ automático (§1.18); o que não está aqui não tem `auto` nem `parcial`
    's01': ('tempo', True), 's02': ('alertas', False), 's04': ('porao', True), 's05': ('diesel', False), 's06': ('tanques', False),
    's07': ('baterias', False), 's09': ('seakeeper', False), 's11': ('documentos', True), 's12': ('tarefas', False),
    'c02': ('seakeeperOff', False), 'c03': ('motoresOff', False), 'c04': ('geradorOff', False), 'c06': ('porao', False),
    'a01': ('motoresOff', False), 'a02': ('geradorOff', False), 'a03': ('diesel', False), 'f01': ('profundidade', False),
    'f04': ('deriva', False), 'f06': ('mare', False)}
# O `faq` é a seção do mesmo guia que a `fonte` (§1.18), menos s10 (EL-04: Rádio VHF, Eletrônicos §4) e s13 (EM-09: cartão de Salvatagem): por desenho, apontam para o cartão do assunto.
CK_FAQ = {'s03': 'MO-01', 's04': 'PO-03', 's07': 'EE-02', 's08': 'GE-03', 's09': 'SK-02', 's10': 'EL-04', 's13': 'EM-09', 'c01': 'EL-02',
          'c02': 'SK-04', 'c03': 'MO-06', 'c04': 'GE-04', 'c05': 'CL-05', 'a07': 'CK-05', 'f01': 'EL-08', 'f02': 'AN-01', 'f03': 'EL-03', 'f05': 'AN-03'}
CK_LINK = {'c08': 'G3-Diario', 'a06': 'G2-Abastecimento'}   # a tela do app (sem o -Web/-Mobile): o CONCLUIR e o item levam até ela
# Revisão do C10: a `fonte` de cada item (None = «boa prática», os 12 itens sem seção nos guias gerados) e os números que o `t` diz, na ordem em que
# aparecem (a tabela do §1.18: 25 % do diesel, 15 % da água doce e 80 % das servidas, 2 a 3 min, 3 a 5 vezes; os bancos de 24 V e 12 V e o canal 16).
# O gerador monta esses números das mesmas constantes que montam o guia; aqui eles ficam presos ao contrato e à seção que a `fonte` cita.
CK_FONTE = {   # id → (chave do guia em drive.arquivos, seção como está na base) ou None
    's01': ('checklist', 'Saída · antes de largar'), 's02': None, 's03': ('g_motores', '1 · Antes da partida'), 's04': ('g_porao', '3 · Teste mensal'),
    's05': ('checklist', 'Abastecimento'), 's06': ('checklist', 'Tanques'), 's07': ('g_eletrico', '2 · Faixas'),
    's08': ('g_gerador', '3 · Água no escapamento'), 's09': ('g_seakeeper', '2 · Ligar antes de sair'), 's10': ('checklist', 'Saída · 4 a 6'),
    's11': None, 's12': None, 's13': ('checklist', 'Saída · antes de largar'), 's14': None,
    'c01': ('g_eletronicos', '2 · Piloto automático'), 'c02': ('g_seakeeper', '4 · Desligar ao atracar'), 'c03': ('g_motores', '6 · Parada'),
    'c04': ('g_gerador', '4 · Desligar'), 'c05': ('g_clima', '5 · Desligar'), 'c06': ('g_porao', '2 · Faixas'), 'c07': None,
    'c08': ('checklist', 'Chegada'),
    'a01': None, 'a02': None, 'a03': None, 'a04': None, 'a05': None, 'a06': ('checklist', 'Abastecimento'), 'a07': ('checklist', 'Abastecimento'),
    'f01': ('g_eletronicos', '8 · Sonda'), 'f02': ('g_ancora', '1 · Lançar'), 'f03': ('g_eletronicos', '3 · Alarme de âncora'), 'f04': None,
    'f05': ('g_ancora', '3 · Recolher e travar'), 'f06': None}
CK_NUM = {'s05': ('25',), 's06': ('15', '80'), 's07': ('24', '12'), 's10': ('16',), 'c03': ('2', '3'), 'a07': ('25',), 'f02': ('3', '5')}   # o que não está aqui não tem número
CK_CHAVES = ('id', 'c', 't', 'fonte', 'auto', 'parcial', 'faq', 'link')
BOA_PRATICA = 'boa prática'

SENSORES_DESENHO = {'perfil': {'img': 'assets/sensores-perfil.svg', 'w': 1200, 'h': 360}, 'planta': {'img': 'assets/sensores-planta.svg', 'w': 1200, 'h': 420}}
SENSORES_REFERENCIA = {'popa_x': 0.04, 'proa_x': 0.95, 'quilha_y': 0.92, 'topo_y': 0.08, 'eixo_y': 0.5, 'meia_boca': 0.32}
SENSORES_IDS = ('gps', 'radar', 'meteo', 'sonda', 'inclinometro', 'estabilizador', 'praca', 'motor_bb', 'motor_be', 'gerador', 'diesel_bb', 'diesel_be',
                'agua', 'servidas', 'b24s', 'b24p', 'b12', 'porao_bb', 'porao_be', 'leme', 'guincho', 'dessal')   # n = 1…22; os 7 primeiros são do perfil
SENSORES_PERFIL = 7
BLOCO_FILEIRAS = {'web': {'cima': (0.05, 0.15), 'baixo': (0.85, 0.95)}, 'app': {'cima': (0.04, 0.13), 'baixo': (0.87, 0.96)}}   # `by`, na ordem de preferência
BLOCO_BX = (0.06, 0.94)   # `bx` = `x` limitado a este intervalo (quando cabe)
BLOCO_DIST = 0.10         # dois blocos da mesma fileira nunca a menos de 0,10


def sensor_xy(p, ref=SENSORES_REFERENCIA):
    """(x, y) do ponto pelas frações da `referencia` (§1.19): x = popa_x + l·(proa_x − popa_x); no perfil, y = quilha_y + a·(topo_y − quilha_y);
    na planta, y = eixo_y + b·meia_boca. Quatro casas."""
    x = ref['popa_x'] + p['l'] * (ref['proa_x'] - ref['popa_x'])
    y = (ref['quilha_y'] + p['a'] * (ref['topo_y'] - ref['quilha_y'])) if p['vista'] == 'perfil' else (ref['eixo_y'] + p['b'] * ref['meia_boca'])
    return round(x, 4), round(y, 4)


def blocos_sensores(pontos, plat):
    """{id: [bx, by, lado]} dos pontos de UMA vista, para a plataforma `plat` ('web' ou 'app') (§1.19). Os pontos entram em ordem de `x` (empate:
    pelo `n`); o `lado` alterna 'cima' e 'baixo' a partir de 'cima'; dentro do lado, o bloco vai na 1ª fileira em que fica a pelo menos 0,10
    do bloco anterior dessa fileira, com `bx` = `x` limitado a [0,06, 0,94]. Revisão do C10: com 4 fileiras de 0,10, cinco sensores do perfil
    (em 0,09 de largura) e dez da planta (em 0,18) não cabem com `bx` = `x`. Quando nenhuma fileira do lado cabe, o bloco anda para a direita só
    o necessário: vai para a fileira do lado que libera primeiro, a 0,10 do bloco anterior dela. Passando de 0,94, levanta ValueError (o gerador
    falha em vez de gravar blocos que se sobrepõem)."""
    fil, ultimo, out = BLOCO_FILEIRAS[plat], {}, {}
    for i, p in enumerate(sorted(pontos, key=lambda q: (q['x'], q['n']))):
        lado = 'cima' if i % 2 == 0 else 'baixo'
        bx = round(min(max(p['x'], BLOCO_BX[0]), BLOCO_BX[1]), 4)
        cabem = [by for by in fil[lado] if by not in ultimo.get(lado, {}) or round(bx - ultimo[lado][by], 4) >= BLOCO_DIST]
        if cabem:
            by = cabem[0]
        else:
            by = min(fil[lado], key=lambda f: ultimo[lado][f])
            bx = round(ultimo[lado][by] + BLOCO_DIST, 4)
            if bx > BLOCO_BX[1]:
                raise ValueError('sensores: sem lugar para o bloco de %s (%s, %s)' % (p['id'], plat, lado))
        ultimo.setdefault(lado, {})[by] = bx
        out[p['id']] = [bx, by, lado]
    return out


PECAS_IDS = tuple('p%02d' % i for i in range(1, 13))
PECAS_QTD = {'p03': (1, 2), 'p05': (0, 1)}   # a única BAIXA (1 de 2) e a única ZERO (0 de 1, a mesma falta do diário d03); as outras estão no mínimo ou acima
PECAS_CHAVES = ('id', 'n', 'qtd', 'min', 'local', 'tarefas', 'obs')

ALARMES_CHAVES = ('chave', 'max', 'histerese_s', 'nivel', 'fonte', 'metricas')
ALARMES_METRICA = ('id', 'campos', 'nome', 'palavras', 'un', 'casas', 'faixa', 'ops', 'motor')
FAIXAS_PEDIDAS = {   # campo → faixa aceita para o limite pedido (§1.21); a regra é a `faixa` própria, não o D.replay.limites
    'motor_bb_oleo_bar': (0.5, 6.0), 'motor_be_oleo_bar': (0.5, 6.0), 'motor_bb_arref_c': (60, 100), 'motor_be_arref_c': (60, 100),
    'motor_bb_rpm': (500, 2600), 'motor_be_rpm': (500, 2600), 'bateria_0_tensao_v': (22.0, 30.0), 'bateria_1_tensao_v': (22.0, 30.0),
    'bateria_2_tensao_v': (11.0, 15.0), 'profundidade_m': (1, 50), 'vento_verdadeiro_nos': (5, 50), 'sog_nos': (1, 30),
    'pressao_barometrica_hpa': (980, 1040), 'temp_agua_c': (10, 32), 'diesel_litros': (100, 1600), 'tanque_agua_pct': (5, 100),
    'tanque_cinzas_pct': (5, 100), 'tanque_negras_pct': (5, 100)}


def _f_checklists(X):
    """F09 (§1.18): os 4 tipos, os 35 itens com `c`, ✓ automático, FAQ e tela do contrato, a `fonte` de cada um (a da CK_FONTE: um §n que existe
    nos guias gerados ou «boa prática»), os números do `t` (os da CK_NUM, e cada um no texto da seção que a `fonte` cita) e a trava de lugar e de
    número de pessoas."""
    out, ck = [], X.D.get('checklists')
    if not isinstance(ck, dict):
        return ['checklists ausente (F09, §1.18)']
    if set(ck) != {'fonte', 'tipos', 'itens'}:
        out.append('checklists: chaves %s (precisa de fonte, tipos e itens)' % sorted(ck))
    if ck.get('fonte') != X.arq.get('checklist'):
        out.append('checklists.fonte %r ≠ o título do guia (drive.arquivos.checklist)' % ck.get('fonte'))
    if ck.get('tipos') != [dict(zip(('id', 'l', 'aba', 'nome', 'sys'), t)) for t in CK_TIPOS]:
        out.append('checklists.tipos ≠ os 4 do §1.18 (id, l, aba, nome, sys), nesta ordem')
    itens = ck.get('itens')
    if not (isinstance(itens, dict) and list(itens) == [t[0] for t in CK_TIPOS]):
        return out + ['checklists.itens: precisa dos 4 tipos %s, nesta ordem' % ', '.join(t[0] for t in CK_TIPOS)]
    secao = lambda t: ' §' + t['secao'] if str(t.get('secao'))[:1].isdigit() else ' § ' + str(t.get('secao'))   # «Guia §1 · Antes» · «Checklist § Chegada»
    fontes_ok = {BOA_PRATICA} | {str(t.get('fonte')) + secao(t) for t in X.trechos}
    texto_de = {str(t.get('fonte')) + secao(t): str(t.get('texto')) for t in X.trechos}   # o texto da seção que a `fonte` cita
    ref_fonte = lambda r: BOA_PRATICA if r is None else str(X.arq.get(r[0])) + (' §' + r[1] if r[1][:1].isdigit() else ' § ' + r[1])
    for tipo, ref in CK_C.items():
        lista = itens[tipo]
        if not (isinstance(lista, list) and all(isinstance(it, dict) for it in lista)):
            out.append('checklists.itens.%s não é uma lista de itens' % tipo)
            continue
        ids = [it.get('id') for it in lista]
        if ids != list(ref):
            out.append('checklists.itens.%s: ids %s ≠ %s' % (tipo, ids, list(ref)))
        for it in lista:
            i = it.get('id')
            cam = 'checklists.itens.%s.%s' % (tipo, i)
            if set(it) - set(CK_CHAVES):
                out.append('%s: chave fora da forma (%s)' % (cam, ', '.join(sorted(set(it) - set(CK_CHAVES)))))
            if it.get('c') != ref.get(i):
                out.append('%s.c %r ≠ %r (§1.18)' % (cam, it.get('c'), ref.get(i)))
            fonte = it.get('fonte')
            if fonte not in fontes_ok:
                out.append('%s.fonte %r não é um §n que existe nos guias gerados nem «%s»' % (cam, fonte, BOA_PRATICA))
            elif i in CK_FONTE and fonte != ref_fonte(CK_FONTE[i]):
                out.append('%s.fonte %r ≠ %r (a seção que diz o que o item diz, §1.18)' % (cam, fonte, ref_fonte(CK_FONTE[i])))
            if not (isinstance(it.get('t'), str) and it['t'].strip()):
                out.append('%s.t vazio' % cam)
            elif R_PESSOAS.search(it['t']):
                out.append('%s.t: número de pessoas no item «%s»' % (cam, it['t']))
            else:   # os números do texto: os do contrato, na ordem, e cada um no texto da seção que a `fonte` cita (nenhum com «boa prática»)
                nums = re.findall(r'\d+(?:,\d+)?', it['t'])
                esperados = CK_NUM.get(i, ())
                secao_txt = texto_de.get(fonte)
                if tuple(nums) != esperados:
                    out.append('%s.t: números %s ≠ %s do §1.18 («%s»)' % (cam, nums, list(esperados), it['t']))
                elif nums and secao_txt is None:
                    out.append('%s.t: números %s sem seção para conferir (fonte %r)' % (cam, nums, fonte))
                elif any(not tem_numero(secao_txt, float(n.replace(',', '.'))) for n in nums):
                    out.append('%s.t: número %s que o texto da seção citada na fonte não tem («%s»)' % (
                        cam, [n for n in nums if not tem_numero(secao_txt, float(n.replace(',', '.')))], it['t']))
            auto = CK_AUTO.get(i)
            esperado = (auto[0], True if auto[1] else None) if auto else (None, None)   # `parcial` só existe com o valor true
            if (it.get('auto'), it.get('parcial')) != esperado:
                out.append('%s: auto/parcial %r/%r ≠ %r/%r (tabela do §1.18; parcial só com o valor true)' % (cam, it.get('auto'), it.get('parcial'), *esperado))
            if it.get('faq') != CK_FAQ.get(i):
                out.append('%s.faq %r ≠ %r' % (cam, it.get('faq'), CK_FAQ.get(i)))
            if it.get('link') != CK_LINK.get(i):
                out.append('%s.link %r ≠ %r' % (cam, it.get('link'), CK_LINK.get(i)))
    return out


def _f_sensores(X):
    """F08 (§1.19): o desenho, a `referencia`, os 22 pontos com x/y pela fórmula, e o `bloco` de cada plataforma pela regra (a recontagem do
    contrato) e pelos invariantes soltos (lado alternado, fileira e `bx` dentro dos limites)."""
    out, sn = [], X.D.get('sensores')
    if not isinstance(sn, dict):
        return ['sensores ausente (F08, §1.19)']
    if set(sn) != {'perfil', 'planta', 'referencia', 'pontos'}:
        out.append('sensores: chaves %s (precisa de perfil, planta, referencia e pontos)' % sorted(sn))
    for v in ('perfil', 'planta'):
        if sn.get(v) != SENSORES_DESENHO[v]:
            out.append('sensores.%s %r ≠ %r (o desenho da Fase 4 segue este caminho e este tamanho)' % (v, sn.get(v), SENSORES_DESENHO[v]))
    if sn.get('referencia') != SENSORES_REFERENCIA:
        out.append('sensores.referencia ≠ a do §1.19')
    pontos = sn.get('pontos')
    if not (isinstance(pontos, list) and len(pontos) == len(SENSORES_IDS) and all(isinstance(p, dict) for p in pontos)):
        return out + ['sensores.pontos: precisa de %d pontos' % len(SENSORES_IDS)]
    for i, p in enumerate(pontos):
        cam, vista = 'sensores.pontos[%s]' % p.get('id', i), 'perfil' if i < SENSORES_PERFIL else 'planta'
        if p.get('n') != i + 1 or p.get('id') != SENSORES_IDS[i] or p.get('vista') != vista:
            out.append('%s: n/id/vista %r/%r/%r ≠ %d/%s/%s (§1.19)' % (cam, p.get('n'), p.get('id'), p.get('vista'), i + 1, SENSORES_IDS[i], vista))
        eixo = 'a' if vista == 'perfil' else 'b'
        lim = (0, 1) if vista == 'perfil' else (-1, 1)
        if set(p) != {'n', 'id', 'vista', 'l', eixo, 'x', 'y', 'rotulo', 'onde', 'campos', 'bloco'}:
            out.append('%s: chaves %s fora da forma da vista %s' % (cam, sorted(p), vista))
            continue
        if not (_num(p['l']) and 0 <= p['l'] <= 1 and _num(p[eixo]) and lim[0] <= p[eixo] <= lim[1]):
            out.append('%s: l/%s fora de %s' % (cam, eixo, lim))
            continue
        xy = sensor_xy(dict(p, vista=vista), sn.get('referencia') if isinstance(sn.get('referencia'), dict) and set(sn['referencia']) == set(SENSORES_REFERENCIA) else SENSORES_REFERENCIA)
        if (p['x'], p['y']) != xy:
            out.append('%s: (x, y) %r ≠ a fórmula da referencia %r' % (cam, (p['x'], p['y']), xy))
        for k in ('rotulo', 'onde'):
            if not (isinstance(p[k], str) and p[k].strip()):
                out.append('%s.%s vazio' % (cam, k))
        if not (isinstance(p['campos'], list) and p['campos'] and all(isinstance(c, str) for c in p['campos']) and len(set(p['campos'])) == len(p['campos'])):
            out.append('%s.campos: precisa de uma lista não vazia de campos sem repetição' % cam)
    por_vista = {v: [p for p in lista if _num(p.get('x')) and _num(p.get('n')) and isinstance(p.get('id'), str)]
                 for v, lista in (('perfil', pontos[:SENSORES_PERFIL]), ('planta', pontos[SENSORES_PERFIL:]))}   # pela posição na lista, não pelo `vista` gravado
    for plat in ('web', 'app'):
        for v, ps in por_vista.items():
            try:
                esperado = blocos_sensores(ps, plat)
            except (ValueError, TypeError, KeyError) as e:
                out.append('sensores.%s/%s: %s' % (v, plat, e))
                continue
            for k, p in enumerate(sorted(ps, key=lambda q: (q['x'], q['n']))):
                b = (p.get('bloco') or {}).get(plat) if isinstance(p.get('bloco'), dict) else None
                cam = 'sensores.pontos[%s].bloco.%s' % (p['id'], plat)
                if not (isinstance(b, list) and len(b) == 3 and _num(b[0]) and _num(b[1]) and b[2] in BLOCO_FILEIRAS[plat]):
                    out.append('%s: precisa de [bx, by, lado] com lado cima ou baixo (%r)' % (cam, b))
                    continue
                if b[2] != ('cima' if k % 2 == 0 else 'baixo'):
                    out.append('%s: lado %r não alterna (cima, baixo, … em ordem de x)' % (cam, b[2]))
                if b[1] not in BLOCO_FILEIRAS[plat][b[2]]:
                    out.append('%s: by %r fora das fileiras %s do lado %s' % (cam, b[1], BLOCO_FILEIRAS[plat][b[2]], b[2]))
                if not BLOCO_BX[0] <= b[0] <= BLOCO_BX[1] or b[0] < min(max(p['x'], BLOCO_BX[0]), BLOCO_BX[1]) - 1e-9:
                    out.append('%s: bx %r fora de [x limitado a %s, %s] (o bloco só anda para a direita, e só quando a fileira não cabe)' % (cam, b[0], BLOCO_BX[0], BLOCO_BX[1]))
                if b != esperado.get(p['id']):
                    out.append('%s: %r ≠ %r (a regra do §1.19 recontada)' % (cam, b, esperado.get(p['id'])))
    return out


def _f_pecas(X):
    """F22 (§1.20): 12 peças, sem código de fabricante (`pn`) nem preço, a única BAIXA e a única ZERO, `tarefas` na agenda (IDS)."""
    out, pecas = [], X.D.get('pecas')
    if pecas is None:
        return ['pecas ausente (F22, §1.20)']
    if not (isinstance(pecas, list) and len(pecas) == len(PECAS_IDS) and all(isinstance(p, dict) for p in pecas)):
        return ['pecas: precisa de %d peças (F22, §1.20)' % len(PECAS_IDS)]
    if [p.get('id') for p in pecas] != list(PECAS_IDS):
        out.append('pecas: ids %s ≠ %s' % ([p.get('id') for p in pecas], list(PECAS_IDS)))
    for p in pecas:
        cam = 'pecas.%s' % p.get('id')
        if set(p) - set(PECAS_CHAVES) or not {'id', 'n', 'qtd', 'min', 'local'} <= set(p):
            out.append('%s: chaves %s fora da forma (sem pn nem preço)' % (cam, sorted(p)))
        if not (isinstance(p.get('n'), str) and p['n'].strip()):
            out.append('%s.n vazio' % cam)
        q, m = p.get('qtd'), p.get('min')
        if not (type(q) is int and type(m) is int and q >= 0 and m >= 1):
            out.append('%s: qtd/min %r/%r (inteiros, qtd ≥ 0 e min ≥ 1)' % (cam, q, m))
        elif (q, m) != PECAS_QTD.get(p['id'], (q, m)) or (p['id'] not in PECAS_QTD and q < m):
            out.append('%s: qtd/min %r/%r (só p03 fica abaixo do mínimo, 1 de 2, e só p05 chega a zero, 0 de 1)' % (cam, q, m))
        if 'tarefas' in p and not (isinstance(p['tarefas'], list) and p['tarefas'] and all(isinstance(t, str) for t in p['tarefas'])):
            out.append('%s.tarefas: lista não vazia de ids da agenda' % cam)
    p05 = next((p for p in pecas if p.get('id') == 'p05'), {})
    if 'gerador-rotor' not in (p05.get('tarefas') or []):
        out.append('pecas.p05: o rotor do gerador em falta (d03) precisa da tarefa gerador-rotor')
    return out


def _f_alarmes(X):
    """F12 (§1.21): a lista fechada de 18 métricas, cada uma com a `faixa` do contrato (não o D.replay.limites), `un` e `casas` do D.campos,
    ops '<' e '>', `motor` só nos campos do motor; o nível é só `aviso`."""
    out, al = [], X.D.get('alarmesPedidos')
    if not isinstance(al, dict):
        return ['alarmesPedidos ausente (F12, §1.21)']
    if list(al) != list(ALARMES_CHAVES):
        out.append('alarmesPedidos: chaves %s ≠ %s' % (list(al), list(ALARMES_CHAVES)))
    if al.get('chave') != 'capitao.alarmes.v1' or al.get('max') != 10 or al.get('histerese_s') != 10:
        out.append('alarmesPedidos: chave/max/histerese_s %r/%r/%r ≠ capitao.alarmes.v1/10/10' % (al.get('chave'), al.get('max'), al.get('histerese_s')))
    if al.get('nivel') != 'aviso':
        out.append('alarmesPedidos.nivel %r ≠ aviso (o alarme pedido nunca vira crítico, §2.4)' % al.get('nivel'))
    if al.get('fonte') != 'alarme pedido no chat · avaliado neste aparelho':
        out.append('alarmesPedidos.fonte %r' % al.get('fonte'))
    ms = al.get('metricas')
    if not (isinstance(ms, list) and all(isinstance(m, dict) for m in ms)):
        return out + ['alarmesPedidos.metricas: lista de métricas']
    ids, usados = [m.get('id') for m in ms], []
    if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
        out.append('alarmesPedidos.metricas: ids repetidos ou vazios')
    for m in ms:
        cam = 'alarmesPedidos.%s' % m.get('id')
        if set(m) - set(ALARMES_METRICA) or not set(ALARMES_METRICA) - {'motor'} <= set(m):
            out.append('%s: chaves %s fora da forma' % (cam, sorted(m)))
        cs = m.get('campos')
        if not (isinstance(cs, list) and len(cs) == 1 and cs[0] in FAIXAS_PEDIDAS):
            out.append('%s.campos %r: um campo da lista fechada do §1.21' % (cam, cs))
            continue
        c = cs[0]
        usados.append(c)
        ref = FAIXAS_PEDIDAS[c]
        if not (isinstance(m.get('faixa'), list) and tuple(m['faixa']) == ref):
            out.append('%s.faixa %r ≠ %r (§1.21)' % (cam, m.get('faixa'), list(ref)))
        if m.get('ops') != ['<', '>']:
            out.append("%s.ops %r ≠ ['<', '>']" % (cam, m.get('ops')))
        if ('motor' in m and m['motor'] is not True) or (m.get('motor') is True) != c.startswith('motor_'):
            out.append('%s.motor %r (true só nos campos do motor: óleo, arrefecimento e rpm)' % (cam, m.get('motor')))
        d = X.campos.get(c) or {}
        if m.get('un') != d.get('un') or m.get('casas') != d.get('casas'):
            out.append('%s: un/casas %r/%r ≠ os do D.campos %r/%r' % (cam, m.get('un'), m.get('casas'), d.get('un'), d.get('casas')))
        if not (isinstance(m.get('nome'), str) and m['nome'].strip()):
            out.append('%s.nome vazio' % cam)
        ps = m.get('palavras')
        if not (isinstance(ps, list) and ps and all(isinstance(x, str) and x.strip() and x.strip() == norm(x).strip() for x in ps) and len(set(ps)) == len(ps)):
            out.append('%s.palavras: lista não vazia, sem repetição, minúsculas e sem acento' % cam)
    if sorted(usados) != sorted(FAIXAS_PEDIDAS):
        out.append('alarmesPedidos.metricas: os campos %s ≠ os 18 do §1.21' % sorted(usados))
    return out


def a_funcoes(X):
    """C10 (§1.18–§1.21): checklists (F09), sensores (F08), peças (F22) e alarmes pedidos (F12), os quatro nos dois modos."""
    return _f_checklists(X) + _f_sensores(X) + _f_pecas(X) + _f_alarmes(X)


# ——————————————————————————————— FAQ DOS EQUIPAMENTOS (C11, §1.6) ———————————————————————————————
# A referência é daqui, nunca do dado conferido (como a CK_FAQ): o topo, as chaves de um item, os 15 prefixos de guia, os 9 cartões EM
# (a ordem do contrato, não a da base: o EPIRB vem depois de abandono), os tipos de fonte e o glossário.
FAQ_TOPO = ('versao', 'total', 'secoes', 'itens', 'glossario')
FAQ_CHAVES = ('id', 'titulo', 'pergunta', 'variantes', 'resposta', 'passos', 'acao', 'atencao', 'senao', 'obs', 'fontes', 'secao', 'equip', 'emerg',
              'seguranca', 'ver')   # na ordem em que o gerador grava
FAQ_OBRIGATORIAS = ('id', 'titulo', 'pergunta', 'variantes', 'resposta', 'fontes', 'secao', 'equip', 'emerg')
FAQ_TEXTO = ('titulo', 'pergunta', 'resposta', 'acao', 'atencao', 'senao', 'obs', 'equip')   # os campos de texto simples (passos e variantes são listas)
# Sem o chip de confiabilidade nem os anexos do Avanti (decisão 8 do §8.2): nada disto existe, em nenhum nível.
FAQ_PROIBIDAS = {'conf', 'edicao', 'origem', 'selos', 'decisoes', 'limites', 'lacuna', 'lacunas', 'divergencias', 'invalidos', 'alertas'}
FAQ_TIPOS = ('Guia de bordo', 'Protocolo', 'Boa prática')   # nunca "Manual" nem "Foto"
FAQ_GUIAS = (('MO', 'g_motores'), ('GE', 'g_gerador'), ('SK', 'g_seakeeper'), ('CL', 'g_clima'), ('EL', 'g_eletronicos'), ('EE', 'g_eletrico'),
             ('DS', 'g_dessalinizador'), ('PO', 'g_porao'), ('AN', 'g_ancora'), ('PI', 'g_piloto'), ('RA', 'g_radar'), ('AI', 'g_ais'),
             ('SF', 'g_seafire'), ('EP', 'g_epirb'), ('CK', 'checklist'))   # prefixo → chave de drive.arquivos; id = prefixo + número da seção
FAQ_EM = (('EM-01', 'MAYDAY · canal 16'), ('EM-02', 'PAN-PAN'), ('EM-03', 'DSC'), ('EM-04', 'Homem ao mar'), ('EM-05', 'Incêndio · Seafire'),
          ('EM-06', 'Água entrando'), ('EM-07', 'Abandono'), ('EM-08', 'EPIRB'), ('EM-09', 'Salvatagem'))   # id → seção do protocolo
FAQ_GLOSSARIO = ('SOG', 'STW', 'COG', 'HDG', 'TWS', 'TWA', 'AWA', 'DPT', 'ETA', 'MOB', 'DSC', 'MMSI', 'EPIRB', 'BB/BE')
FAQ_GLOSSARIO_ROTULO = ('MOB', 'DSC')   # os termos de segurança levam o rótulo do procedimento padrão (o EPIRB, também a nota da etiqueta)
R_NUMERO = re.compile(r'\d+(?:[.,]\d+)*')   # 2.050 · 6,0 · 12 · 16: o número como o guia escreve
R_FONTE = re.compile(r'(.+?) §\s*(.+)')     # «<título> §<n> · <seção>» (numerada) ou «<título> § <seção>» (sem número)
# Revisão do C11 (a tela e a voz leem a `resposta` inteira): a frase do trecho de origem que escala («MAYDAY»), condiciona («e há fogo no motor»),
# proíbe («Não abra o acesso ao motor…», «Não desligue até o resgate», «Nunca abra a tampa…»), libera com cautela («e só então libere o acesso, com o
# extintor portátil à mão»), manda ventilar por «cheiro de combustível», manda usar o «SOS do app» ou limita o uso («Só em perigo grave e iminente»)
# não pode ficar só nos passos, na `atencao` ou no `senao`. Os «^» valem para a oração (ela abre com o Não/Nunca/Só em perigo, não o tem no meio).
# «MAYDAY, MAYDAY, MAYDAY» é o roteiro do EM-01, que a resposta diz em prosa e os passos repetem letra por letra.
R_ESCALA = re.compile(r'MAYDAY|há fogo|^(?:não|nunca)\b|\bsó então\b|cheiro de combustível|SOS do app|^só em perigo', re.I)
ROTEIRO_MAYDAY = 'MAYDAY, MAYDAY, MAYDAY'
# A ação que o trecho só manda fazer COM a condição («Se o sistema não disparou sozinho e há fogo no motor, use o disparo manual»): a condição vai junto
# dela em todo campo que a manda fazer (acao, passos, atencao, senao, obs), senão quem lê só o passo a passo ou a linha de ação descarrega o sistema fixo
# sem fogo. A ação é o fim da oração depois da vírgula («disparo manual»: as 2 últimas palavras) e a condição, a parte «há fogo no motor».
R_CONDICIONADA = re.compile(r'(?P<cond>há fogo[^,;:.]*),\s+(?P<acao>[^,;.]+)', re.I)
# Revisão do C11: os itens «boa prática» que o app avalia sozinho (✓ automático: alertas, documentos, tarefas de segurança, motores e gerador desligados,
# nível anotado, deriva, maré e vento). No checklist são o rótulo do ✓; no FAQ viram ordem de conferência, porque o mesmo texto solto afirma um estado
# que o dado de bordo desmente («Nenhuma tarefa de segurança atrasada» com o porao-teste atrasado; «Nenhum alerta ativo» com o AVISO do laço).
CK_ESTADO = tuple(i for i, f in CK_FONTE.items() if f is None and i in CK_AUTO)


def _norm_frase(txt):
    return re.sub(r'\s+', ' ', str(txt)).strip().lower()


def _frases(txt):
    return [c.strip() for c in re.split(r'(?<=[.!?])\s+(?=[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ])', str(txt)) if c.strip()]


def _clausulas(txt):
    """As frases de um trecho e, dentro delas, as orações separadas por «;» (o fim do trecho de segurança tem a escalada depois do ponto e vírgula)."""
    return [o.strip() for f in _frases(txt) for o in re.split(r';\s+', f) if o.strip()]


def _resolve_fonte(texto, por_trecho):
    """O trecho da base que uma fonte do FAQ cita (título do guia e seção), ou None."""
    m = R_FONTE.fullmatch(str(texto or ''))
    return por_trecho.get((m.group(1), m.group(2))) if m else None


def a_faq(X):
    """O faq-equipamentos.json (§1.6): a forma, os 91 ids (15 guias + 9 cartões EM) e a ligação de cada item com o trecho da base que ele cita.
    Sem o faq (os testes do D sozinho), nada a conferir. As regras de texto (8 regex, coordenada, grafia Seafire, calado, estabilizador de
    12 V, rótulo no fim de SF/EP/EM-09, `seguranca` pela SEGURANCA_PALAVRAS, fabricante e modelo do EPIRB e do Seafire, tamanho) são das
    outras asserções, que já leem o FAQ; aqui ficam as que só o FAQ tem:
      - topo {versao, total, secoes, itens, glossario}; `total` = itens; nenhuma chave de confiabilidade, edição, origem, selos, decisões,
        limites, lacunas, divergências, alertas nem inválidos, em nenhum nível;
      - ids únicos = EM-01…EM-09 + prefixo e número de cada seção dos guias; `secoes` {n, titulo, ids} partem os itens, e `secao` do item é o `n`;
      - item com as chaves do contrato na ordem, 3 variantes diferentes, fontes só dos 3 tipos, `emerg` só nos EM, `ver` com ids que existem;
      - a 1ª fonte é a seção da base daquele id (EM-n: a do protocolo), e todo número do item está no texto dessa seção (nada de número novo);
      - `seguranca` em todo item cujo trecho de origem tem; a resposta termina com o rótulo que o trecho termina e, com seguranca, tem até 800 letras;
      - a resposta mantém toda frase ou oração do trecho de origem que escala (MAYDAY), condiciona («há fogo»), proíbe («Não…», «Nunca…»), libera com
        cautela («só então»), manda ventilar («cheiro de combustível»), manda usar o «SOS do app» ou limita o uso («Só em perigo…»), não só os passos;
      - a ação que a base só manda fazer com condição («disparo manual» só com «há fogo no motor») leva a condição em resposta, acao, atencao, senao,
        obs e no passo a passo (no passo ou antes dele);
      - o checklist: nenhum texto do FAQ repete o item «boa prática» que o app avalia (CK_ESTADO): vira ordem de conferência, não afirmação de estado;
      - os cartões EM passam as regras do D.protocolos (sem bar, %, nós, graus, pessoas, lugar, fabricante, modelo nem dado do barco);
      - o glossário: os 14 termos, MMSI com o texto MMSI_RADIO e os de segurança com o rótulo."""
    Q = X.faq
    if Q is None:
        return []
    if not isinstance(Q, dict):
        return ['faq: não é um objeto']
    out = []
    if tuple(Q.keys()) != FAQ_TOPO:
        out.append('faq: chaves do topo %s (precisa de %s)' % (list(Q.keys()), list(FAQ_TOPO)))
    if not re.fullmatch(r'[0-9a-f]{8}', str(Q.get('versao'))):
        out.append('faq.versao: %r (8 hex do sha256 do conteúdo)' % (Q.get('versao'),))
    out += ['%s: chave de %s (§1.6: sem confiabilidade, edição, origem, selos, decisões, limites, lacunas, divergências, alertas nem inválidos)' % (c, k)
            for c, k in chaves_de(Q, 'faq:') if k in FAQ_PROIBIDAS]
    itens = Q.get('itens')
    if not isinstance(itens, list) or not itens:
        return out + ['faq.itens: lista vazia ou ausente']
    if Q.get('total') != len(itens) or not isinstance(Q.get('total'), int):
        out.append('faq.total: %r ≠ %d itens' % (Q.get('total'), len(itens)))
    por_trecho = {(t.get('fonte'), t.get('secao')): t for t in X.trechos}
    # As ações que a base só manda fazer com uma condição («há fogo no motor» → «disparo manual»), de qualquer trecho: {2 últimas palavras da ação: condição}.
    condicionadas = {}
    for t in X.trechos:
        for c in _clausulas(t.get('texto', '')):
            m = R_CONDICIONADA.search(c)
            if m:
                condicionadas[' '.join(_norm_frase(m.group('acao')).split()[-2:])] = _norm_frase(m.group('cond'))
    # ——— ids ———
    ids = [i.get('id') if isinstance(i, dict) else None for i in itens]
    out += ['faq.itens: id repetido %r' % i for i, n in Counter(ids).items() if n > 1]
    esperado, trecho_de = [], {}
    for iid, sec in FAQ_EM:
        esperado.append(iid)
        trecho_de[iid] = por_trecho.get((X.arq.get('protocolo'), sec))
    for pre, chave in FAQ_GUIAS:
        secoes = [t for t in X.trechos if t.get('fonte') == X.arq.get(chave)]
        for n, t in enumerate(secoes, 1):
            esperado.append('%s-%02d' % (pre, n))
            trecho_de[esperado[-1]] = t
    if set(ids) != set(esperado):
        out.append('faq.itens: ids ≠ os do contrato (%d esperados): faltam %s, sobram %s' % (
            len(esperado), sorted(set(esperado) - set(ids))[:6], sorted(set(ids) - set(esperado), key=str)[:6]))
    for iid, t in trecho_de.items():
        if t is None:
            out.append('faq:%s: o trecho de origem não existe na base' % iid)
    # ——— seções ———
    por_id = {i['id']: i for i in itens if isinstance(i, dict) and isinstance(i.get('id'), str)}
    grupos = Q.get('secoes')
    visto = []
    if not (isinstance(grupos, list) and grupos):
        out.append('faq.secoes: lista vazia ou ausente')
    else:
        for k, g in enumerate(grupos, 1):
            cam = 'faq.secoes[%d]' % (k - 1)
            if not (isinstance(g, dict) and tuple(g.keys()) == ('n', 'titulo', 'ids')):
                out.append('%s: precisa de {n, titulo, ids}' % cam)
                continue
            if g['n'] != k:
                out.append('%s.n: %r (precisa de %d: o filtro lê a seção por D.secoes[n − 1])' % (cam, g['n'], k))
            if not (isinstance(g['titulo'], str) and g['titulo'].strip()):
                out.append('%s.titulo vazio' % cam)
            if not (isinstance(g['ids'], list) and g['ids']):
                out.append('%s.ids: lista vazia' % cam)
                continue
            for iid in g['ids']:
                visto.append(iid)
                if iid in por_id and por_id[iid].get('secao') != k:
                    out.append('faq:%s.secao: %r (está em faq.secoes[%d], n = %d)' % (iid, por_id[iid].get('secao'), k - 1, k))
        if sorted(visto, key=str) != sorted(por_id, key=str) or len(visto) != len(set(visto)):
            out.append('faq.secoes: os ids das seções não partem os itens (cada item em uma seção só): faltam %s, sobram %s'
                       % (sorted(set(por_id) - set(visto))[:6], sorted(set(visto) - set(por_id), key=str)[:6]))
    # ——— itens ———
    titulos, perguntas = Counter(i.get('titulo') for i in itens if isinstance(i, dict)), Counter(i.get('pergunta') for i in itens if isinstance(i, dict))
    for it in itens:
        if not isinstance(it, dict):
            out.append('faq.itens: item que não é objeto')
            continue
        iid = str(it.get('id'))
        cam = 'faq:' + iid
        chaves = tuple(it.keys())
        if [k for k in FAQ_CHAVES if k in it] != list(chaves) or any(k not in FAQ_CHAVES for k in chaves):
            out.append('%s: chaves %s (permitidas, nesta ordem: %s)' % (cam, list(chaves), list(FAQ_CHAVES)))
        out += ['%s: falta a chave %s' % (cam, k) for k in FAQ_OBRIGATORIAS if k not in it]
        for k in FAQ_TEXTO:
            if k in it and not (isinstance(it[k], str) and it[k].strip()):
                out.append('%s.%s: %r (texto vazio; campo vazio é omitido)' % (cam, k, it[k]))
        v = it.get('variantes')
        if not (isinstance(v, list) and len(v) == 3 and all(isinstance(x, str) and x.strip() for x in v) and len(set(v)) == 3 and it.get('pergunta') not in v):
            out.append('%s.variantes: %r (3 maneiras de perguntar, diferentes entre si e da pergunta)' % (cam, v))
        if 'passos' in it and not (isinstance(it['passos'], list) and it['passos'] and all(isinstance(x, str) and x.strip() for x in it['passos'])):
            out.append('%s.passos: %r (lista de frases; sem passo a passo, a chave é omitida)' % (cam, it['passos']))
        if titulos[it.get('titulo')] > 1:
            out.append('%s.titulo repetido: %r' % (cam, it.get('titulo')))
        if perguntas[it.get('pergunta')] > 1:
            out.append('%s.pergunta repetida: %r' % (cam, it.get('pergunta')))
        if not isinstance(it.get('secao'), int) or isinstance(it.get('secao'), bool):
            out.append('%s.secao: %r (inteiro)' % (cam, it.get('secao')))
        if it.get('emerg') is not (iid.startswith('EM-')):
            out.append('%s.emerg: %r (verdadeiro só nos cartões EM)' % (cam, it.get('emerg')))
        if 'seguranca' in it and it['seguranca'] is not True:
            out.append('%s.seguranca: %r (só verdadeiro; senão a chave é omitida)' % (cam, it['seguranca']))
        if 'ver' in it:
            ver = it['ver']
            if not (isinstance(ver, list) and ver and len(set(ver)) == len(ver) and iid not in ver and all(x in por_id for x in ver)):
                out.append('%s.ver: %r (ids que existem, sem repetir nem citar o próprio)' % (cam, ver))
        fontes = it.get('fontes')
        if not (isinstance(fontes, list) and fontes and all(isinstance(f, dict) and tuple(f.keys()) == ('tipo', 'texto') for f in fontes)):
            out.append('%s.fontes: %r (lista de {tipo, texto})' % (cam, fontes))
            continue
        for j, f in enumerate(fontes):
            if f['tipo'] not in FAQ_TIPOS:
                out.append('%s.fontes[%d].tipo: %r (só %s)' % (cam, j, f['tipo'], ', '.join(FAQ_TIPOS)))
            if not (isinstance(f['texto'], str) and f['texto'].strip()):
                out.append('%s.fontes[%d].texto vazio' % (cam, j))
            elif f['tipo'] != 'Boa prática' and _resolve_fonte(f['texto'], por_trecho) is None:
                out.append('%s.fontes[%d]: %r não é uma seção da base (título do guia §seção)' % (cam, j, f['texto']))
        if fontes[0].get('tipo') == 'Boa prática':
            out.append('%s.fontes[0]: a 1ª fonte é a seção do guia ou do protocolo, não a boa prática' % cam)
        # ——— a ligação com a base: a 1ª fonte é o trecho daquele id ———
        t = trecho_de.get(iid)
        if t is None:
            continue
        citado = _resolve_fonte(fontes[0].get('texto'), por_trecho)
        if citado is not t:
            out.append('%s.fontes[0]: %r não é a seção do id (esperado: %s · %s)' % (cam, fontes[0].get('texto'), t.get('fonte'), t.get('secao')))
        permitidos = set()
        for f in fontes:
            c = _resolve_fonte(f.get('texto'), por_trecho)
            if c is not None:
                permitidos |= set(R_NUMERO.findall('%s %s' % (c.get('secao'), c.get('texto'))))
        for c, texto in textos(it, cam):
            if c.split('.')[-1].split('[')[0] in ('id', 'ver', 'fontes', 'equip', 'tipo', 'texto', 'secao') or '.fontes[' in c or '.ver[' in c or c == cam + '.equip':
                continue
            for n in R_NUMERO.findall(texto):
                if n not in permitidos:
                    out.append('%s: número %s que não está na seção citada (nada de número novo; vem do guia gerado) «%s»' % (c, n, texto[:90]))
        # ——— segurança e rótulo herdados do trecho ———
        if t.get('seguranca') is True and it.get('seguranca') is not True:
            out.append('%s: o trecho de origem tem seguranca: true e o item não (nada com seguranca vai à IA)' % cam)
        fim = next((f for f in (rotulo_fim(), cap(ROTULO) + '.') if str(t.get('texto', '')).rstrip().endswith(f)), None)
        if fim and not str(it.get('resposta', '')).rstrip().endswith(fim):
            out.append('%s: a resposta não termina com o rótulo que o trecho de origem termina «%s»' % (cam, fim[-60:]))
        if not fim and ROTULO.lower() in str(it.get('resposta', '')).lower():   # o rótulo abre frase com maiúscula no fim do texto
            out.append('%s: rótulo do procedimento padrão numa resposta cujo trecho de origem não o tem' % cam)
        # ——— a escalada e a condição do trecho ficam na resposta (e nos passos, quando o item tem) ———
        resp_n = _norm_frase(it.get('resposta', ''))
        for c in _clausulas(t.get('texto', '')):
            if R_ESCALA.search(c) and ('mayday' if ROTEIRO_MAYDAY in c else _norm_frase(c).rstrip('.!?;: ')) not in resp_n:
                out.append('%s.resposta: corta a frase do trecho de origem que escala ou condiciona «%s» (a tela e a voz leem a resposta inteira; ela mantém toda frase do trecho que escala, condiciona, proíbe ou libera com cautela)' % (cam, c[:90]))
        # ——— a ação condicionada vai com a condição em todo campo que a manda fazer (a F6 e a voz leem a linha de ação e o passo a passo, não só a resposta) ———
        for acao_c, cond_c in condicionadas.items():
            for campo in ('resposta', 'acao', 'atencao', 'senao', 'obs'):
                txt_c = _norm_frase(it.get(campo, ''))
                if acao_c in txt_c and cond_c not in txt_c:
                    out.append('%s.%s: manda fazer «%s» sem a condição «%s» do trecho de origem (a F6 e a voz leem este campo sozinho) «%s»' % (cam, campo, acao_c, cond_c, str(it[campo])[:90]))
            antes = ''   # no passo a passo a condição pode vir num passo anterior (a lista se lê em ordem)
            for k, passo in enumerate(it.get('passos') or []):
                antes += ' ' + _norm_frase(passo)
                if acao_c in _norm_frase(passo) and cond_c not in antes:
                    out.append('%s.passos[%d]: manda fazer «%s» sem a condição «%s» no passo nem antes dele «%s»' % (cam, k, acao_c, cond_c, str(passo)[:90]))
        if it.get('seguranca') is True and len(str(it.get('resposta', ''))) > SEGURANCA_MAX_LETRAS:   # como o trecho (SEGURANCA_CURTA): a tela e a voz leem a resposta inteira
            out.append('%s.resposta: %d letras com seguranca (máximo %d: a tela e a voz leem inteira, com o rótulo no fim)' % (cam, len(it['resposta']), SEGURANCA_MAX_LETRAS))
    # ——— o checklist no FAQ: ordem de conferência, não o estado que o app avalia ———
    estado = {_norm_frase(x['t']).rstrip('.'): x['id'] for lista in ((X.D.get('checklists') or {}).get('itens') or {}).values() if isinstance(lista, list)
              for x in lista if isinstance(x, dict) and x.get('id') in CK_ESTADO and isinstance(x.get('t'), str)}
    for it in itens:
        if isinstance(it, dict):
            for c, txt in textos(it, 'faq:%s' % it.get('id')):
                if c.split('.')[-1].split('[')[0] in ('id', 'ver', 'fontes', 'equip', 'tipo', 'texto', 'secao') or '.fontes[' in c or '.ver[' in c:
                    continue
                for f in _frases(txt):   # a frase inteira, letra por letra: a mesma palavra dentro de outra frase («motores e gerador desligados») não é a cópia
                    if _norm_frase(f).rstrip('.') in estado:
                        out.append('%s: repete o item %s do checklist, que o app avalia sozinho (✓ automático): no FAQ ele vira ordem de conferência, não a afirmação do estado «%s»' % (c, estado[_norm_frase(f).rstrip('.')], f[:90]))
    # ——— cartões EM: as regras do D.protocolos ———
    out += _regras_protocolo(X, [(c, s) for it in itens if isinstance(it, dict) and str(it.get('id', '')).startswith('EM-')
                                 for c, s in textos(it, 'faq:%s' % it.get('id')) if not re.search(r'\.(?:id|ver\[\d+\]|fontes\[\d+\]\.\w+|secao|equip)$', c)])
    # ——— glossário ———
    gl = Q.get('glossario')
    if not (isinstance(gl, list) and [g.get('termo') if isinstance(g, dict) else None for g in gl] == list(FAQ_GLOSSARIO)):
        out.append('faq.glossario: os termos precisam ser %s' % ', '.join(FAQ_GLOSSARIO))
    else:
        for g in gl:
            cam = 'faq.glossario.' + g['termo']
            if tuple(g.keys()) != ('termo', 'texto', 'fonte') or not all(isinstance(g[k], str) and g[k].strip() for k in g):
                out.append('%s: precisa de {termo, texto, fonte} com texto' % cam)
                continue
            if g['termo'] == 'MMSI' and PROTOCOLOS_TEXTOS['mmsiRadio'] not in g['texto']:
                out.append('%s.texto: sem o texto MMSI_RADIO (%s)' % (cam, PROTOCOLOS_TEXTOS['mmsiRadio']))
            if g['termo'] in FAQ_GLOSSARIO_ROTULO and not g['texto'].rstrip().endswith(cap(ROTULO) + '.'):
                out.append('%s.texto: sem o rótulo do procedimento padrão no fim' % cam)
            if g['termo'] == 'EPIRB' and not g['texto'].rstrip().endswith(rotulo_fim()):
                out.append('%s.texto: sem o rótulo e a nota da etiqueta no fim' % cam)
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
    ('ROTULO_SEGURANCA', a_rotulo_seguranca), ('SEGURANCA_CURTA', a_seguranca_curta), ('IDENT_BASE', a_ident_base), ('NOTA_ETIQUETA', a_nota_etiqueta),
    ('SEGURANCA_SEM_MODELO', a_seguranca_sem_modelo),
    ('PROTOCOLOS', a_protocolos),   # §1.3 (C6): a forma e a fonte única do D.protocolos
    ('GRAFIA_SEAFIRE', a_grafia_seafire),   # §1.3 (revisão do C6): «Seafire» sem hífen nem espaço em todo dado
    ('RODAPE_SNAPSHOT', a_rodape_snapshot),
    ('FONTES_RELATIVAS', a_fontes_relativas),
    # Invariantes da coluna "Asserção do gerador" da §6.4 sem nome na §6.3 (as outras de lá estão na MMSI9 e na SEM_INDICATIVO).
    ('TERCEIROS', a_terceiros), ('SEM_PREVISAO', a_sem_previsao),
    # §1.2 (o C4 da §6.2: "asserções do registro e de lotacao ≥ pessoasBordo"), sem nome na §6.3.
    ('EMBARCACAO', a_embarcacao),
    # Revisão 3 do C4 (§1.5, §2.5): o estabilizador é de 12 V DC; nenhum texto dele fala de energia AC.
    ('ESTABILIZADOR_12V', a_estabilizador_12v),
    # C10 (§1.18–§1.21): a forma e a referência do contrato dos checklists, sensores, peças e alarmes pedidos, sem nome na §6.3.
    ('FUNCOES', a_funcoes),
    # C11 (§1.6): o faq-equipamentos.json (F10): forma, ids, ligação com a base, números do guia, segurança, rótulo, cartões EM e glossário.
    ('FAQ', a_faq),
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
    """Separa as violações das asserções estruturais (fora da RELATORIO; na TERMOS, as três de TERMOS_JA_REPROVAM) pela PENDENTES. Cada padrão casa UMA violação.
    Devolve (novas, conhecidas, velhas): novas = {asserção: [violações fora das pendências]}, que reprovam; conhecidas =
    {asserção: {commit: n}}; velhas = [(asserção, commit, padrão)] que não casaram nada, que também reprovam (a lista não pode
    esconder a volta do defeito). As asserções de `inativas` (fonte opcional ausente) não têm pendência velha."""
    novas, conhecidas, velhas = {}, {}, []
    for nome, msgs in V.items():
        livres = [m for m in msgs if not em_relatorio(nome, m)]
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
    imprime('confere(): %d asserções · %d reprovam o gerador (mais %s, da TERMOS): %s' % (
        len(V), len(V) - len(RELATORIO), ', '.join(TERMOS_JA_REPROVAM),
        ('%d com falha (%s)' % (len(falhas), ', '.join(falhas))) if falhas else '0 falhas'))
    imprime('  pendências conhecidas, por caminho (cada uma até o commit que completa o dado): ' + (' · '.join(
        '%s %d (%s)' % (n, sum(c.values()), ' · '.join('%s %d' % kv for kv in sorted(c.items()))) for n, c in conhecidas.items()) or 'nenhuma'))
    partes = []
    for n, v in V.items():
        if n in RELATORIO:
            v = [m for m in v if em_relatorio(n, m)]   # na TERMOS, as de TERMOS_JA_REPROVAM saem daqui: reprovam
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
                    c = 'relatório' if em_relatorio(n, m) else pendente_de(n, m)
                    imprime('      ' + m + ('  [%s]' % c if c else '  [NOVA]'))
    if falhas:
        motivo = []
        for n in falhas:
            nv, vl = len(novas.get(n) or []), sum(1 for nn, _, _ in velhas if nn == n)
            motivo.append(n + ' ' + ' + '.join(x for x in ('%d nova(s)' % nv if nv else '', '%d pendência(s) velha(s)' % vl if vl else '') if x))
        raise ConfereFalhou('confere(): ' + ', '.join(motivo))
    return V
