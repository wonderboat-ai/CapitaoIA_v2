# -*- coding: utf-8 -*-
"""Capitão IA — teste do cérebro (roteamento, fonte em toda resposta, SEM DADOS sem fonte, registro só com comando).
Vento e rajada do dia (paridade Avanti 1.24.0): com a leitura do cabeçalho salva neste aparelho (capitao-clima.js, Open-Meteo
real — aqui uma cópia fixa no localStorage, sem rede), o clima, o "seguro para sair?" e a ficha da IA trazem o vento previsto com
a fonte e a hora (o mar segue SEM DADOS); sem leitura do dia (ou sem o capitao-clima.js), SEM DADOS e nenhum vento inventado. O vento
não muda a decisão, nem forte (45/60 nós): o app não tem limite de vento com fonte. "Rajada" só vai para o clima em pergunta de
previsão: no relato de equipamento ("a âncora garrou com a rajada") e no limite do barco, a rota do equipamento ou a IA.

Uso (com o site servido em http://127.0.0.1:8765):
    python -m http.server 8765 --bind 127.0.0.1      (na raiz do repositório, em outro terminal)
    python testes/cerebro.py
Navegador: Edge instalado (Playwright com channel="msedge"); troque CANAL para "chrome" se preferir.
"""
import calendar
import datetime
import json
import os
import re
import sys
from playwright.sync_api import sync_playwright

# A 1b prende as listas de emergência do cérebro às do gerador (ferramentas/demo/confere.py: SOS, SALVATAGEM, BOIA_FORA, EPIRB), que também
# marcam o `seguranca` dos trechos e dos itens do FAQ, e as 8 regex do termos.json sobre as respostas de emergência.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ferramentas', 'demo'))
import confere  # noqa: E402

BASE = 'http://127.0.0.1:8765/'
CANAL = 'msedge'

# (pergunta, chave esperada)
CASOS = [
    ('', 'saudacao'), ('oi, bom dia', 'saudacao'),
    ('MAYDAY, homem ao mar!', 'sos'), ('tem fogo na praça de máquinas', 'sos'), ('está entrando água no casco', 'sos'),
    ('fumaça no escapamento do motor', 'motores'),
    ('pressão de óleo baixa no motor BB', 'oleo'), ('qual a pressão do óleo?', 'oleoLeitura'), ('alarme de óleo acendeu', 'oleo'),
    ('Registre no diário: saída com 4 pessoas', 'diario'), ('vou registrar no diário depois', 'diarioLer'),
    ('não registre isso', 'fallback'), ('é seguro sair hoje?', 'seguro'), ('para onde vamos hoje?', 'destinos'),
    ('próximas manutenções', 'manutencao'), ('autonomia', 'autonomia'), ('maré agora', 'mare'), ('clima e vento', 'clima'),
    ('roteiro do canal 16', 'canal16'), ('checklist de saída', 'checklist'), ('checklist de chegada', 'checklistChegada'),
    ('consumo de diesel', 'consumo'), ('nível dos tanques', 'tanques'), ('quem chamar da equipe?', 'contatos'),
    ('pendências abertas', 'anomalias'), ('bombas de porão', 'porao'), ('como ligar o gerador?', 'base'),
    ('quantas horas tem o gerador', 'gerador'), ('posição agora', 'posicao'), ('documentos vencendo', 'docsvenc'),
    # Revisão do C7: o botão "Perguntar sobre" da G1 (web e app) pergunta "Situação e vencimento do documento: <nome>". Com o doc-epirb ("Certificado
    # do EPIRB…") a pergunta caía na rota `epirb`; é papelada, e `epirb` é das chaves que ligam a conversa em emergência na Fase 3.
    ('Situação e vencimento do documento: Certificado do EPIRB (bateria e disparador hidrostático)', 'docsvenc'),
    ('horímetros', 'horimetros'), ('estabilizador Seakeeper', 'estabilizador'), ('climatização', 'climatizacao'),
    ('alarme de fluxo da climatização', 'base'), ('plotter garmin', 'eletronicos'), ('parear bluetooth no fusion', 'base'),
    ('dessalinizador', 'dessalinizador'), ('bateria 24 v', 'eletrico'), ('onde fica o EPIRB?', 'epirb'), ('onde fica o seafire', 'seafire'),
    ('âncora garrando?', 'ancora'), ('manual do gerador', 'gerador'), ('guias de bordo', 'manual'), ('diário de bordo', 'diarioLer'),
    # Fase 3 (P3C), PROMPT Fase 7 linha 3 (`:33`/`:47`): «qual o preço do dólar?» e «quem ganhou o jogo ontem» são a rota foraBarco (§2.7), local, sem IA
    ('qual o preço do dólar?', 'foraBarco'), ('quem ganhou o jogo ontem', 'foraBarco'),
    ('motores volvo penta', 'motores'), ('Telemetria agora', 'telemetria'), ('como está o barco?', 'telemetria'), ('troca do rotor do gerador', 'base'),
    ('Oque você faz?', 'saudacao'), ('o que vc sabe fazer?', 'saudacao'), ('quem é vc?', 'saudacao'), ('como você funciona?', 'saudacao'),
    ('pra que serve esse app?', 'saudacao'),
    ('diagnóstico', 'diagnostico'), ('status da IA', 'diagnostico'), ('a IA está ligada?', 'diagnostico'), ('teste da IA', 'diagnostico'),
    ('qual o diagnóstico do gerador?', 'gerador'),
    # 1.0.7: 'funciONANdo' não é o gerador Onan; diagnóstico com vocativo, 'por favor' e a forma negativa
    ('a IA não está funcionando', 'diagnostico'), ('Capitão, diagnóstico', 'diagnostico'), ('diagnóstico, por favor', 'diagnostico'),
    ('rode o diagnóstico', 'diagnostico'), ('qual é o status da IA?', 'diagnostico'), ('a IA na nuvem está ligada?', 'diagnostico'),
    ('o motor BB não está funcionando', 'motores'), ('luz do óleo acesa no BB, ainda funcionando', 'oleo'), ('o gerador onan tá ligado?', 'gerador'),
    ('vai ter rajada hoje?', 'clima'), ('como estão as rajadas?', 'clima'), ('rajadas?', 'clima'),
    # "rajada" em relato de equipamento ou no limite do barco: a rota do equipamento ou a IA, nunca a previsão do dia
    ('a âncora garrou com a rajada', 'ancora'), ('a rajada quebrou a antena do VHF', 'canal16'), ('o motor BB apagou na rajada', 'motores'),
    ('seakeeper desligou na rajada', 'estabilizador'), ('o gerador desligou com a rajada', 'gerador'),
    ('o piloto automático não segura com rajada', 'eletronicos'), ('o motor apagou na rajada hoje', 'motores'),
    ('a rajada rasgou o toldo', 'fallback'), ('qual a rajada máxima que o barco aguenta?', 'fallback'),
    # "hoje"/"agora" sozinhos não fazem de "rajada" uma pergunta de previsão: relato e pessoa em risco seguem a IA (revisão da F13)
    # 1b: «adernou» entrou na lista SOS (PROMPT §2.3); o que o caso protege continua (relato com «rajada» nunca vira a previsão do dia, `clima`).
    # Revisão da 1b: «rajada derrubou alguém no mar» era `fallback` (IA na nuvem), caso antigo da F13 que contradizia a trava «emergência local,
    # nunca na IA» (§2.3): pessoa no mar é `sos`, ainda sem previsão (nunca `clima`)
    ('pegamos uma rajada agora e o barco adernou', 'sos'), ('rajada derrubou alguém no mar agora', 'sos'),
    ('a rajada de hoje arrancou o toldo', 'fallback'), ('há rajada forte entrando, o que faço?', 'fallback'),
    ('quanto tempo dura uma rajada?', 'fallback'), ('tem rajada hoje?', 'clima'), ('qual a previsão de rajada para amanhã?', 'clima'),
    # C5 (CONTRATO §6.2): com os 91 trechos dos 16 guias, pergunta fora do barco continua sem trecho (nenhum guia tem "lais")
    ('como se faz um nó lais de guia?', 'fallback'),
    # Revisão do C5: trecho de segurança no topo (g_epirb, g_seafire, protocolo §DSC) responde local e não vai à IA (PEDE_IA False,
    # PROMPT §2.3); "supressão" é a rota seafire (§2.3); as perguntas dos cartões da F1 ao chat (Seafire, AIS e guincho, CONTRATO §1.4)
    # caem na chave do equipamento ou no guia, nunca no SOS, no roteiro MAYDAY (canal16) nem na maré.
    # 1b: o sistema fixo («sistema fixo», «descarga do sistema», «depois do disparo»…) é a rota `seafire`, com os passos de protocolos.seafire
    ('teste da baliza', 'base'), ('como acionar o disparo manual do sistema fixo?', 'seafire'), ('supressão', 'seafire'), ('botão distress', 'base'),
    # Revisão 2 do C5: o cartão do guincho perguntava "guincho da âncora Lewmar", que caía na resposta pronta "ancora" (com a posição
    # do snapshot e o texto antigo do §3): agora pergunta o procedimento e cai no g_ancora. Radar e piloto: a resposta pronta dos
    # eletrônicos não fala deles; a pergunta de procedimento cai no guia de cada um (CONTRATO §1.4).
    ('sistema fixo de supressão', 'seafire'), ('transponder em-trak', 'base'), ('como lançar com o guincho Lewmar', 'base'),
    ('como ligar o radar Garmin', 'base'), ('como engatar o piloto automático Raymarine', 'base'),
    # Revisão 2 do C5: saudação com assunto de segurança (o g_epirb §2 no topo do buscaBase, que a tela manda à IA) fica no aparelho;
    # depois do disparo do sistema fixo, o trecho do topo manda não abrir o acesso ao motor (nunca o "use o disparo manual").
    ('como você me ajuda com o teste da baliza?', 'saudacao'), ('o que você sabe sobre o teste da baliza?', 'saudacao'),
    # 1b (CONTRATO §6.2, «os casos do disparo passam à chave seafire»): os mesmos casos, agora na rota `seafire`, que traz o «não abra o acesso ao
    # motor» e o desligamento de motores, gerador e ventilação (ver a verificação «1b: depois do disparo…» mais abaixo)
    ('o que fazer depois do disparo do sistema fixo', 'seafire'), ('o sistema fixo disparou', 'seafire'), ('o sistema fixo descarregou', 'seafire'),
    ('alarme do sistema fixo', 'seafire'),
    # Revisão 3 do C5: pergunta genérica sobre os equipamentos volta ao fallback (a IA responde com o "## Equipamentos" da ficha).
    # O rótulo e a nota da etiqueta, no fim de todo trecho de segurança, punham o g_epirb §4 no topo e barravam a IA; o índice
    # da busca não os conta mais (o texto do trecho fica igual).
    ('quais equipamentos tem a bordo?', 'fallback'), ('equipamentos do barco', 'fallback'), ('modelo dos equipamentos', 'fallback'),
    # Revisão 4 do C5: o passo a passo do Seafire (desligue motores e gerador, corte a ventilação, não abra o acesso ao motor, depois da
    # descarga, espere o motor esfriar) casava perguntas comuns, mostrava o procedimento de incêndio e, por ser de segurança, barrava a IA.
    # O trecho de segurança só entra se a pergunta nomeia o assunto dele (fonte, equipamento ou título); o g_seafire §2 e §3 não repetem
    # mais o passo a passo. As perguntas comuns voltam à resposta pronta, ao guia certo ou à IA, como antes do C5.
    ('como religar o gerador depois de desligar', 'gerador'), ('como abrir o motor', 'motores'), ('como abrir o gerador', 'gerador'),
    ('como abrir o acesso ao motor', 'motores'), ('posso abrir o acesso ao motor para conferir o óleo', 'motores'),
    ('como abrir a ventilação', 'fallback'), ('como desligar a ventilação', 'fallback'), ('como ligar a ventilação depois de desligar', 'fallback'),
    ('como religar a ventilação depois de desligar', 'fallback'), ('o alarme disparou', 'fallback'), ('como desligar o sistema', 'fallback'),
    ('como religar o motor depois de desligar', 'base'), ('quando trocar o óleo do motor?', 'base'),
    ('como esfriar o motor', 'base'), ('como esfriar o motor depois de navegar', 'base'), ('como esfriar o motor depois de navegar rápido', 'base'),
    # o que continua local: a pergunta nomeia o assunto (o sistema fixo, a baliza, o DSC)
    ('o sistema descarregou', 'seafire'), ('o sistema fixo disparou sozinho', 'seafire'), ('distress', 'base'), ('como usar o botão distress', 'base'),
    # Revisão 5 do C5: a resposta pronta de equipamento (GENERICAS) só cede ao trecho do guia quando ele é do assunto perguntado
    # (trechoServe: guia do equipamento, nome que a pergunta diz, algo além do nome). Com os 91 trechos, "como ligar o plotter" trazia o
    # "Ligar e transmitir" do radar, "como ligar o sistema de som" o §1 dos bancos de bateria, "como funciona o sistema elétrico" o §3 de
    # verificação. Voltam à resposta pronta, como antes do C5. Quando outro dos 3 primeiros trechos é do assunto, vale ele (o trecho dos
    # motores no "alarme de temperatura do motor", o dos alarmes do Seakeeper): "como ligar o carregador" sai do §2 do Seakeeper para o §1
    # do g_eletrico, que cita o carregador e é do mesmo guia da resposta pronta.
    ('como ligar o plotter', 'eletronicos'), ('como ligar o sistema de som', 'audio'), ('como ligar o sistema de áudio', 'audio'),
    ('como funciona o sistema elétrico', 'eletrico'), ('como está o sistema elétrico', 'eletrico'), ('como funciona o sistema de baterias', 'eletrico'),
    ('como desligar o sistema elétrico', 'eletrico'), ('como desligar o piloto', 'eletronicos'), ('como desligar a bomba', 'porao'),
    ('como esfriar a climatização', 'climatizacao'),
    ('como ligar o carregador', 'base'), ('como ligar o carregador de bateria', 'base'), ('alarme de temperatura do motor', 'base'),
    ('seakeeper temperatura alta', 'base'), ('trocar o filtro do ar condicionado', 'base'),
    # o que continua no trecho do guia: "ar" é palavra da busca ("como ligar o ar" achava o "Ligar e transmitir" do radar porque o filtro
    # de tamanho tirava o "ar" e sobrava só "ligar"); "ar condicionado" vale pela climatização; o alarme de âncora é do plotter (§3)
    ('como ligar o ar', 'base'), ('como ligar o ar condicionado', 'base'), ('como desligar o ar', 'base'), ('substituir filtro de ar', 'base'),
    ('como funciona o piloto automático', 'base'), ('alarme de âncora', 'base'), ('como fundear', 'base'),
    # Revisão 5 do C5: o trecho do protocolo que descreve uma situação (homem ao mar, PAN-PAN) também é nomeado pelas palavras com que
    # a pessoa a conta (`ident`: caiu, vista, pane, governo…). Antes da revisão 4 o trecho vinha de qualquer palavra dele; depois, só
    # pelo título, e estas perguntas, com as palavras do próprio trecho, iam à IA. ("ferido" também é do PAN-PAN, mas a 1b manda
    # ` ferid` para o SOS: fica de fora daqui para o caso não mudar de chave.)
    # 1b: «caiu da lancha» entrou na lista SOS (a revisão do C5 mediu «pessoa caiu da lancha» indo à IA): a chave passa de `base` a `sos`, ainda local
    # 1b, quarta revisão: «a pessoa que caiu» e «quem caiu» também são pessoa na água (a revisão mediu «ninguém consegue ver a pessoa que caiu» indo à IA): a chave passa de `base` a
    # `sos`, ainda local. O trecho do protocolo segue sendo o topo da busca (a verificação das revisões 5 e 6 do C5 abaixo confere a identidade dele pelo buscaBase).
    ('pessoa caiu da lancha', 'sos'), ('não vejo a pessoa que caiu', 'sos'), ('perdemos de vista quem caiu', 'sos'),
    ('sem governo', 'base'), ('barco sem governo', 'base'), ('pane no barco', 'base'),
    # as palavras de acionamento não abrem o trecho em pergunta comum: o assunto da pergunta tem de ser o do trecho
    # (P3C: «quantas pessoas a bordo» ganhou a rota `pessoas`, pedida pelo PROMPT Fase 3 «Rotas novas»; o que o caso protege continua: a palavra «pessoa» não abre o trecho do protocolo)
    ('o parafuso caiu', 'fallback'), ('quantas pessoas a bordo', 'pessoas'), ('a pessoa da marina', 'fallback'), ('o governo federal', 'fallback'),
    # Revisão 6 do C5: (1) "bomba" sozinha é a de porão; com o nome de outra bomba (água salgada, rotor, impeller, climatização, gerador, óleo…)
    # a pergunta vai ao guia do equipamento, e não à resposta pronta do porão ("Teste de bombas de porão… SEM LEITURA"), que a rota 'porao'
    # dava a toda "bomba" e que o trechoServe (FAMILIA.porao) deixava como resposta; (2) "bateria de partida" é o banco de baterias
    # (g_eletrico §1), não a partida do motor; "bateria do motor" e o motor que não pega seguem os motores; (3) "caiu" também é disjuntor,
    # energia e sinal: só a pessoa que caiu abre o protocolo de homem ao mar (identCom); (4) "manual" e "mar" sozinhos não nomeiam o
    # Disparo manual nem o Homem ao mar. A seção mostrada de cada uma está na verificação "revisão 6 do C5", mais abaixo.
    ('como trocar o rotor da bomba de água salgada', 'base'), ('quando trocar o rotor da bomba de água salgada', 'base'),
    ('como trocar o impeller da bomba de água salgada', 'base'), ('rotor da bomba', 'base'), ('como inspecionar o rotor da bomba', 'base'),
    ('alarme da bomba de água salgada', 'base'), ('como ligar a bomba de água salgada', 'base'), ('como desligar a bomba de água salgada', 'base'),
    ('como ligar a bomba da climatização', 'base'), ('como desligar a bomba da climatização', 'base'), ('como trocar o rotor da bomba do gerador', 'base'),
    ('como trocar a bomba de óleo', 'base'), ('a bomba de circulação', 'fallback'),
    # (revisão 7: "como ligar as bombas de porão" já não traz o §4 "Água entrando" ao topo; fica a resposta pronta do porão, local como antes)
    # (1b: «testar» é sinônimo de «teste» (PROMPT §2.3) só junto de baliza/EPIRB, para «como testar a baliza?». A 1ª versão da 1b o fazia em toda
    # pergunta e «como testar as bombas de porão» saía da resposta pronta (local) para o g_porao §3 e para a IA; a revisão restringiu o sinônimo ao
    # contexto da baliza e a pergunta voltou à resposta pronta do porão, como antes da 1b)
    ('bombas de porão', 'porao'), ('como testar as bombas de porão', 'porao'), ('como testar a bomba de porão', 'porao'), ('como ligar as bombas de porão', 'porao'),
    ('como trocar a bateria de partida', 'base'), ('como verificar a bateria de partida', 'base'), ('bateria de partida', 'eletrico'),
    ('o motor não pega, a bateria de partida está fraca', 'motores'),
    ('o disjuntor caiu, qual o procedimento', 'fallback'), ('a bateria caiu, procedimento', 'eletrico'), ('o gerador caiu, procedimento', 'gerador'),
    ('o plotter caiu, como resolver', 'eletronicos'), ('o motor caiu, como resolver', 'motores'), ('a conexão do plotter caiu, procedimento', 'eletronicos'),
    ('a energia caiu', 'fallback'), ('o wifi caiu', 'fallback'), ('a tensão caiu', 'eletrico'), ('caiu a chave no mar', 'fallback'),
    ('onde fica o manual do motor', 'manual'), ('como acho o manual do motor', 'manual'), ('onde fica o manual', 'manual'),
    # (a temperatura do mar que «caiu» é relato, não a pergunta da leitura da água: continua na IA, como antes da P3C)
    ('tem vista para o mar?', 'fallback'), ('qual a vista do mar', 'fallback'), ('a temperatura do mar caiu', 'fallback'),
    # 1b, quarta revisão: «pessoa ao mar» é o mesmo que «homem ao mar», «criança ao mar» e «tripulante ao mar» (todos `sos`): a base não abre a janela de emergência da Fase 3
    # (`sos`, `oleo`, `canal16`, `epirb`, `seafire`), e a pessoa na água é a emergência que mais precisa dela. Local nos dois casos (PEDE_IA False).
    ('pessoa ao mar', 'sos'),
    # as quatro perguntas de religar depois do disparo e o alarme de âncora ficam no trecho de segurança / no plotter (seção na verificação)
    ('como religar o gerador depois que o sistema fixo disparou', 'seafire'), ('como ligar o gerador depois do disparo do sistema fixo', 'seafire'),
    ('o sistema fixo disparou, como religo o gerador?', 'seafire'), ('como abrir o motor depois que o sistema fixo disparou', 'seafire'),
    # Revisão 7 do C5 (achados da revisão 6). (1) A identidade do trecho de segurança num guia MISTO (o §4 dos motores e do porão, o §1 e o §5
    # dos eletrônicos, o §2 do AIS, o checklist) é só o título dele, sem o nome do equipamento: o equip do g_eletronicos traz Garmin, Fusion e
    # Icom, e "onde fica o plotter", "como ver o radar" ou "como ver o garmin" abriam o §1 "Plotter: homem ao mar" (e "onde fica o motor", o
    # §4 da pressão de óleo), com `seguranca`, e barravam a IA. Agora vão à resposta pronta ou ao guia certo (a verificação "revisão 7" mais
    # abaixo confere que nenhum traz trecho de segurança); o título ainda nomeia ("pressão de óleo baixa", "água entrando", "DSC").
    ('onde fica o plotter', 'base'), ('como ver o radar', 'eletronicos'), ('como ver o garmin', 'eletronicos'), ('como ver o icom', 'fallback'),
    ('como ver o fusion', 'audio'), ('como ver o som', 'audio'), ('como ver o áudio', 'audio'), ('onde fica o motor', 'motores'),
    ('como ver os navios no radar', 'eletronicos'), ('como ver o radar no plotter', 'base'), ('como ver a posição no plotter', 'base'),
    ('como ver o motor no garmin', 'eletronicos'), ('como ver o gerador no garmin', 'gerador'),
    # Fechamento do C5: a guarda de sinônimo do nome() no trechoServe ("ar" e "condicionado" são a "climatização", "som" é o "Fusion") não
    # tinha caso: sem ela, a palavra do nome do equipamento valia como assunto e a pergunta de lugar abria um trecho qualquer do guia (o
    # mutante que tirava a guarda sobrevivia). Com os três casos, ele morre; a resposta pronta fica no aparelho, como antes do C5.
    ('onde fica o ar condicionado', 'climatizacao'), ('onde fica o ar-condicionado', 'climatizacao'), ('onde fica o som', 'audio'),
    ('como funciona a identificação do transponder', 'base'), ('o que fazer antes de largar', 'base'),
    # (2) "bomba de esgoto" é a de esgotamento do porão: relato de água a bordo, local (a rota 'porao'), não a nuvem. As outras bombas com
    # guia seguem o guia ou a rota do assunto (cada palavra do OUTRA_BOMBA tem um caso aqui); sem guia (pressurização, circulação, lavagem), IA.
    ('a bomba de esgoto não para', 'porao'), ('a bomba de esgoto está enchendo de água', 'porao'), ('bomba de esgoto', 'porao'),
    ('bomba do estabilizador', 'estabilizador'), ('alarme da bomba do seakeeper', 'base'), ('bomba do piloto automático', 'eletronicos'),
    ('bomba hidráulica', 'base'), ('a bomba do gerador', 'gerador'), ('bomba do dessalinizador', 'dessalinizador'),
    ('como ligar a bomba do dessalinizador', 'base'), ('bomba de pressurização', 'fallback'), ('a bomba de circulação não funciona', 'fallback'),
    ('bomba de lavagem', 'fallback'), ('como funciona a bomba de porão', 'base'),
    # (3) as palavras genéricas da identidade (IDENT_GENERICAS) não nomeiam o trecho de segurança: "em caso de…" não é o Seafire "Em caso de
    # fogo", "procedimento padrão"/"protocolo de bordo"/"confirmar" não são o protocolo de emergência, "depois" não é o "Depois da descarga"
    ('em caso de alarme', 'fallback'), ('em caso de falha do motor', 'motores'), ('qual o procedimento padrão', 'fallback'),
    ('qual o protocolo de bordo', 'fallback'), ('confirmar com o protocolo de bordo', 'fallback'), ('confirmar protocolo', 'fallback'),
    # ——— 1b (PROMPT §2.3, trava «emergência local, nunca na IA»; CONTRATO §8.2 item 11): as frases que a revisão do C5 mediu indo à IA na nuvem
    # (fallback, PEDE_IA True) entram na lista SOS — e na SEGURANCA_PALAVRAS do gerador, a mesma lista (conferida mais abaixo). «tem gente na água»
    # caía no g_piloto (a regra do piloto em espera). Cada uma é `sos` e fica no aparelho.
    ('caiu do barco', 'sos'), ('caiu da lancha', 'sos'), ('tem gente na água', 'sos'), ('gente na água', 'sos'), ('homem na água', 'sos'),
    ('tripulante na água', 'sos'), ('pessoa na água', 'sos'), ('pulou do barco', 'sos'), ('perdemos de vista na água', 'sos'),
    ('entrou água no motor', 'sos'), ('entrou água', 'sos'), ('estamos fazendo água', 'sos'), ('o barco bateu em uma pedra', 'sos'),
    ('bateu em outro barco', 'sos'), ('perdi o leme', 'sos'), ('o leme quebrou', 'sos'), ('o eixo quebrou', 'sos'), ('quebrou o eixo', 'sos'),
    ('a mangueira estourou', 'sos'),
    # o subconjunto do §8.2 item 11 (sem «sem governo», que pegaria «sem governo federal», nem «água subindo», que pegaria a temperatura da água)
    ('alguém caiu', 'sos'), ('caiu alguém', 'sos'), ('a criança caiu', 'sos'), ('o tripulante caiu', 'sos'), ('tripulante ao mar', 'sos'),
    ('criança ao mar', 'sos'), ('alguém ao mar', 'sos'), ('alguém foi ao mar', 'sos'), ('perdi o governo', 'sos'), ('perdemos o governo', 'sos'),
    ('estamos sem governo', 'sos'), ('o leme travou', 'sos'),
    # a baliza que disparou e o disparador hidrostático são do EPIRB (rota `epirb`), não da lista SOS: o nome do certificado do EPIRB
    # («…disparador hidrostático») é a pergunta do botão da G1, que tem de continuar `docsvenc`
    ('a baliza disparou', 'epirb'), ('o que é o disparador hidrostático?', 'epirb'), ('como testar a baliza?', 'base'), ('onde fica a baliza', 'base'),
    # o que NÃO vira SOS: o «caiu» das coisas, a vista do mar, o piloto em espera, o «bateu» do horário, o governo federal, a temperatura da água
    ('o disjuntor caiu', 'fallback'), ('tem vista para o mar', 'fallback'), ('o piloto em espera', 'eletronicos'),
    ('bateu o horário do abastecimento', 'autonomia'), ('sem governo federal', 'fallback'), ('a temperatura da água está subindo', 'base'),
    # ——— 1b, revisão da revisão (achados da revisão do commit 57d7ce4) ———
    # (1) «bateu em» é batida só com coisa dura ou com «um/uma/outro/outra/algo» e «num/numa»; «bateu em <número ou unidade>» é leitura, nunca SOS
    # (antes, ' bateu em ' pegava a pressão do óleo, o consumo, o tanque e o horímetro, e a Fase 3 ligaria a janela de emergência a cada um)
    ('batemos em uma pedra', 'sos'), ('o barco bateu numa pedra', 'sos'), ('bateu num banco de areia', 'sos'), ('bateu na pedra', 'sos'),
    ('o barco bateu no cais', 'sos'), ('bati em um tronco', 'sos'),
    ('a pressão do óleo bateu em 3 bar', 'oleo'), ('o consumo bateu em 40 litros por hora', 'consumo'), ('o tanque bateu em 50%', 'tanques'),
    ('o horímetro bateu em 1000 horas', 'horimetros'), ('quando o gerador bateu em 1200 horas', 'gerador'), ('a temperatura bateu em 90 graus', 'fallback'),
    ('o relógio bateu em meia noite', 'fallback'), ('o vento bateu em 20 nós', 'clima'), ('a bateria bateu em 12 volts', 'eletrico'),
    ('o horário bateu em 10h', 'fallback'), ('a conta bateu em 500', 'fallback'), ('o consumo bateu em um litro por hora', 'consumo'),
    ('a onda bateu no casco', 'fallback'),
    # (2) pessoa no mar, a água entrando e o governo, nas formas vizinhas das pedidas (iam à IA): sos, local
    ('tem alguém no mar', 'sos'), ('tem gente no mar', 'sos'), ('um tripulante está no mar', 'sos'), ('pessoa no mar', 'sos'), ('criança no mar', 'sos'),
    ('caiu pro mar', 'sos'), ('alguém pulou na água', 'sos'), ('meu filho está na água', 'sos'), ('perdemos um tripulante', 'sos'),
    ('entrou muita água no barco', 'sos'), ('a água entrou no casco', 'sos'), ('estamos tomando água', 'sos'), ('o barco está tomando água', 'sos'),
    ('perdemos o leme', 'sos'), ('o leme não responde', 'sos'), ('o eixo partiu', 'sos'),
    # (3) as perguntas e variantes do FAQ de segurança (a verificação do FAQ, mais abaixo, percorre todas): queda, alagamento, disparo manual
    ('O que faço quando alguém cai na água?', 'sos'), ('alguém cai na água', 'sos'), ('cai gente do barco', 'sos'), ('rumo de volta para quem caiu', 'sos'),
    ('o passageiro caiu', 'sos'), ('marinheiro na água', 'sos'), ('vítima na água', 'sos'), ('alguém foi jogado ao mar', 'sos'), ('sumiu um tripulante', 'sos'),
    ('perdi de vista o meu filho', 'sos'), ('a gente caiu na água', 'sos'),
    ('nível do porão subindo', 'sos'), ('água subindo no porão', 'sos'), ('a bomba de porão não dá conta', 'sos'), ('bomba de porão sem dar conta', 'sos'),
    ('a bomba do porão não para', 'sos'), ('disparo manual com o motor desligado', 'seafire'), ('quando abrir o acesso ao motor depois do disparo', 'seafire'),
    ('ele está sangrando muito', 'sos'),
    # (4) o que NÃO vira SOS (as formas vizinhas das de cima, de rotina): a gente, pro mar, sangrar o diesel, coletei, bálsamo, o nível normal do porão
    ('a gente cai fora do porto às 10h', 'fallback'), ('vamos pro mar amanhã', 'fallback'), ('como sangrar o combustível do motor', 'autonomia'),
    ('sangrando o ar do sistema', 'fallback'), ('sangra o ar da bomba', 'porao'), ('Qual o nível normal do porão?', 'porao'),
    ('o motor está tomando água do mar', 'motores'), ('o passageiro perdeu o voo', 'fallback'), ('o mar está calmo hoje', 'fallback'),
    # (5) rota seafire: o «sistema … disparou» e «descarreg…» só com âncora de incêndio; o alarme do porão, o Seakeeper, o arrefecimento, o vaso, as compras não
    ('o sistema de bombas de porão disparou', 'porao'), ('o sistema do porão disparou', 'porao'), ('o sistema de alarme do porão disparou', 'sos'),  # 1b (revisão 3): o alarme do porão que disparou é relato de alagamento, não o Seafire nem a rota do porão
    ('o sistema do seakeeper disparou o alarme', 'estabilizador'), ('o gerador descarregou', 'gerador'),
    ('o alarme do sistema de arrefecimento disparou', 'fallback'), ('o sistema hidráulico disparou o alarme de pressão', 'fallback'),
    ('o sistema do guincho disparou', 'fallback'), ('o sistema de esgoto disparou', 'fallback'), ('o sistema de alarme disparou', 'fallback'),
    ('alarme de sistema disparou', 'fallback'), ('o sistema de arrefecimento disparou', 'fallback'), ('o sistema de navegação disparou', 'fallback'),
    ('o sistema de direção disparou', 'fallback'), ('o sistema de ancoragem disparou', 'fallback'), ('descarregar as compras do barco', 'fallback'),
    ('descarreguei os cartões', 'fallback'), ('depois da descarga do vaso sanitário', 'fallback'), ('depois da descarga do banheiro', 'base'),
    ('o sistema disparou', 'seafire'), ('o sistema da casa de máquinas disparou', 'seafire'), ('o sistema descarregou depois do incêndio', 'sos'),
    ('o sistema da bomba disparou', 'porao'), ('o sistema da âncora disparou', 'ancora'), ('o sistema do motor disparou', 'motores'),
    ('o motor descarregou', 'motores'), ('o sistema do gerador disparou', 'gerador'), ('o sistema do estabilizador descarregou', 'estabilizador'),
    ('o sistema de extinção disparou', 'seafire'), ('quanto esperar para abrir o motor depois da descarga', 'seafire'),
    ('depois da descarga no compartimento do motor', 'seafire'), ('abrir o acesso depois da descarga', 'seafire'),
    # (6) rota salvatagem: a boia de nível (porão, tanque, bomba), a de ancoragem, «coletei» e «bálsamo» não são salvatagem
    ('a boia do porão está travada', 'porao'), ('a boia da bomba de porão não sobe', 'porao'), ('a boia de nível da bomba', 'porao'),
    ('boia de nível do tanque', 'tanques'), ('a boia do tanque de combustível', 'autonomia'), ('a boia de ancoragem', 'fallback'),
    ('coletei os dados', 'fallback'), ('o bálsamo', 'fallback'), ('jogue a boia na água', 'salvatagem'), ('onde ficam os coletes', 'salvatagem'),
    # Seafire depois do disparo: «sistema fixo», «descarga do sistema», «depois do disparo», «descarreg…», «depois da descarga», «disparou o sistema» e
    # «sistema … disparou»; a bateria que descarregou, o disjuntor e o som que disparou não são o Seafire
    ('disparou o sistema da casa de máquinas', 'seafire'), ('quanto tempo esperar para abrir a praça de máquinas depois da descarga', 'seafire'),
    ('o sistema fixo da praça de máquinas', 'seafire'), ('a bateria descarregou', 'eletrico'), ('o disjuntor do sistema elétrico disparou', 'eletrico'),
    ('o sistema de som disparou o alarme', 'audio'),
    # salvatagem (PROMPT §2.3): resposta fixa, sem lugar e sem número de pessoas; «extintor» com fogo é SOS; a boia de sinalização não é salvatagem
    ('onde ficam os coletes?', 'salvatagem'), ('quantos coletes salva-vidas tem?', 'salvatagem'), ('como usar a balsa', 'salvatagem'),
    ('sinalizadores vencidos?', 'salvatagem'), ('onde fica o extintor', 'salvatagem'), ('onde fica a boia circular', 'salvatagem'),
    ('quais equipamentos de segurança tem a bordo?', 'salvatagem'), ('extintor com fogo na cozinha', 'sos'), ('luz da boia', 'fallback'),
    ('boia de amarração', 'fallback'),
    # MMSI do rádio de bordo em todo texto de rádio: o número do cadastro do app não sai nestas respostas (verificação «1b: emergência…»)
    # (P3C: a pergunta do MMSI ganhou a rota `mmsi`: a 1ª linha manda usar o MMSI da etiqueta do rádio, a 2ª diz o do cadastro do app; a verificação «1b» confere as duas linhas)
    ('qual o MMSI do barco?', 'mmsi'),
    # ——— 1b, segunda revisão (achados da revisão do commit 13de688): a regex de emergência vem de LISTA POSITIVA, não de «qualquer coisa menos unidade» ———
    # (1) «bateu em um/uma/num/numa <qualquer coisa>» era SOS (a 6ª regex só excluía a unidade): leitura, pico, valor, limite, recorde e média são telemetria
    ('o consumo bateu em um valor alto', 'consumo'), ('a temperatura bateu em um pico de 90 graus', 'fallback'), ('a pressão do óleo bateu em um patamar baixo', 'oleo'),
    ('o vento bateu em um pico de 30 nós', 'clima'), ('a bateria bateu em um mínimo de 24 volts', 'eletrico'), ('o horímetro bateu em uma marca de 1200 horas', 'horimetros'),
    ('a rotação bateu em um limite', 'motores'), ('o nível do tanque bateu num valor baixo', 'tanques'), ('bateu num limite', 'fallback'),
    ('o consumo bateu num recorde', 'consumo'), ('o motor bateu num limite de horas', 'motores'), ('o gerador bateu numa média alta', 'gerador'),
    ('bateu num valor', 'fallback'), ('a pressão bateu num valor alto', 'fallback'), ('bateu num pico', 'fallback'),
    # o «bateu forte / em cheio / em mim» de quem não é o barco, e o que bate no fundo ou no banco sem ser casco nem sandbank
    ('o motor bateu forte', 'motores'), ('o preço bateu em cheio', 'foraBarco'), ('a previsão bateu em cheio', 'clima'), ('a vela bateu forte', 'fallback'),
    ('o vento bateu forte', 'clima'), ('o vento bateu em mim', 'clima'), ('o ponteiro bateu no fundo', 'fallback'), ('o nível do tanque bateu no fundo', 'tanques'),
    ('o pix bateu no banco', 'fallback'), ('o dinheiro bateu no banco', 'fallback'), ('a vela bateu no mastro', 'fallback'), ('o sino bateu', 'fallback'),
    ('o relógio bateu 12 horas', 'fallback'),
    # (2) a colisão em que a própria lancha é atingida, e a batida com outro barco, o casco e «nós» (iam à IA)
    ('batemos na lancha ao lado', 'sos'), ('a lancha bateu na nossa popa', 'sos'), ('alguém bateu no nosso barco', 'sos'), ('bateram no nosso barco', 'sos'),
    ('bateram no nosso casco', 'sos'), ('bateu em mim', 'sos'), ('bateu em cheio na pedra', 'sos'), ('bateu em cheio', 'sos'), ('bateu forte no casco', 'sos'),
    ('um barco bateu em nós', 'sos'), ('bateram em nós', 'sos'), ('bateu na gente', 'sos'), ('o outro barco bateu na gente', 'sos'), ('bateu no nosso barco', 'sos'),
    ('bateu no casco', 'sos'), ('bateu no barco', 'sos'), ('bateu forte', 'sos'), ('batemos', 'sos'), ('bateu de lado', 'sos'), ('bateu na proa', 'sos'),
    ('um jet ski bateu em nós', 'sos'), ('bati com o barco numa pedra', 'sos'), ('raspamos numa pedra', 'sos'), ('estamos batendo nas pedras', 'sos'),
    ('acabamos de bater numa pedra', 'sos'), ('um barco nos abalroou', 'sos'), ('fomos abalroados', 'sos'), ('fomos atingidos por outro barco', 'sos'),
    ('tocou o fundo', 'sos'), ('tocamos o fundo', 'sos'), ('ele bateu a cabeça no mastro', 'sos'),
    # (3) casco, leme, eixo, hélice e mangueira nas formas-espelho das pedidas (iam à IA ou à rota do equipamento)
    ('furou o casco', 'sos'), ('rombo no casco', 'sos'), ('casco rachou', 'sos'), ('o casco está furado', 'sos'), ('rachadura no casco', 'sos'),
    ('quebrou o leme', 'sos'), ('leme quebrado', 'sos'), ('sem leme', 'sos'), ('o eixo do motor quebrou', 'sos'), ('a hélice quebrou', 'sos'), ('perdemos a hélice', 'sos'),
    ('estourou a mangueira', 'sos'), ('estourou uma mangueira', 'sos'), ('a mangueira de água salgada estourou', 'sos'), ('a mangueira do escapamento estourou', 'sos'),
    ('a mangueira de combustível estourou', 'sos'), ('a mangueira do motor estourou', 'sos'), ('a mangueira de água estourou', 'sos'), ('a mangueira soltou', 'sos'),
    ('rompeu a mangueira', 'sos'), ('a mangueira furou', 'sos'),
    ('a mangueira de lavagem estourou', 'fallback'), ('a mangueira do chuveiro soltou', 'fallback'), ('validade das mangueiras', 'fallback'),
    # (4) água a bordo: o barco fazendo ou tomando água e a água que começa a entrar; o equipamento que «faz água» e a água doce não
    ('o barco está fazendo muita água', 'sos'), ('a lancha começou a fazer água', 'sos'), ('começou a entrar água no barco', 'sos'), ('está começando a entrar água', 'sos'),
    ('o barco começou a tomar água', 'sos'), ('a água está subindo no barco', 'sos'), ('tem água dentro do barco', 'sos'), ('a água entrou no casco', 'sos'),
    ('estou fazendo água', 'sos'), ('estou tomando água', 'fallback'), ('estou fazendo água doce', 'tanques'),
    ('o dessalinizador está fazendo água', 'dessalinizador'), ('dessalinizador fazendo água doce', 'tanques'), ('o dessalinizador está fazendo água potável', 'dessalinizador'),
    ('o ar condicionado está fazendo água', 'climatizacao'), ('o ar-condicionado está fazendo água no chão', 'climatizacao'), ('estou fazendo agua quente', 'fallback'),
    ('fazendo água potável', 'fallback'), ('a geladeira está fazendo água', 'fallback'), ('a água entrou no tanque de água doce', 'tanques'),
    ('entrou água no tanque de água doce', 'tanques'), ('entrou água no ouvido', 'fallback'), ('por onde a água entra no motor?', 'motores'),
    # (5) pessoa na água ou fora do barco, em número ou por parentesco
    ('caíram na água', 'sos'), ('dois caíram do barco', 'sos'), ('caímos do barco', 'sos'), ('meu marido caiu na água', 'sos'), ('tem um cara na água', 'sos'),
    ('o pai caiu na água', 'sos'), ('perdi de vista o meu marido', 'sos'), ('o Capitão IA caiu', 'fallback'), ('meu pai no mar pescando', 'fallback'),
    # (6) ferimento: sangramento, sangrar, sangue e hemorragia (o sangramento técnico, do ar, do combustível, das linhas, segue local por outra rota)
    ('ele não para de sangrar', 'sos'), ('como estancar um sangramento', 'sos'), ('sangramento no braço', 'sos'), ('ele tem um sangramento forte', 'sos'),
    ('um sangramento no pé', 'sos'), ('sangrou o dedo', 'sos'), ('muito sangue', 'sos'), ('hemorragia', 'sos'), ('sangue na mão', 'sos'), ('dor no peito', 'sos'),
    ('como sangrar o ar do sistema de combustível', 'autonomia'), ('sangrar o filtro de diesel', 'autonomia'), ('sangramento do ar da bomba de combustível', 'autonomia'),
    ('sangramento do respiro do tanque', 'tanques'), ('sangrando o bico injetor', 'fallback'), ('doação de sangue', 'fallback'), ('mantenha o sangue frio', 'fallback'),
    # (7) fogo sem a palavra «fogo»: chamas, labaredas, faísca, curto-circuito, cheiro de plástico ou fio queimado, choque no painel (a rota do motor ou a do quadro
    # elétrico respondia «sem alarme»); queimar óleo ou combustível, lâmpada queimada e a chama do fogão não são
    ('chamas no motor', 'sos'), ('queimando o motor', 'sos'), ('tem chamas na cozinha', 'sos'), ('labaredas', 'sos'), ('cheiro de plástico queimado', 'sos'),
    ('curto circuito no painel', 'sos'), ('choque no painel', 'sos'), ('faíscas no quadro elétrico', 'sos'), ('cheiro de fio queimado', 'sos'),
    ('o painel está fumegando', 'sos'), ('ele levou um choque', 'sos'), ('a tomada está dando choque', 'sos'),
    ('o motor está queimando óleo', 'base'), ('estamos queimando 40 litros por hora', 'consumo'), ('lâmpada queimada', 'fallback'), ('a chama do fogão está azul', 'fallback'),
    ('choque térmico', 'fallback'), ('o preço deu um choque', 'foraBarco'), ('rombo no orçamento', 'fallback'),
    ('fomos abordados pela Marinha', 'fallback'), ('fomos atingidos por uma rajada', 'fallback'),
    # ——— 1b, terceira revisão (achados da revisão do commit 0285bba): as formas curtas e as formas com «está/tá» que iam à IA ou à resposta de rotina ———
    # (1) «fazendo água» sem sujeito: quem está em pânico digita a forma curta. A guarda do equipamento (geladeira, dessalinizador, ar-condicionado…) olha só o sujeito do verbo
    ('fazendo água', 'sos'), ('fazendo agua!', 'sos'), ('tá fazendo água', 'sos'), ('ta fazendo agua', 'sos'), ('está fazendo água', 'sos'), ('ele tá fazendo água', 'sos'),
    ('ela está fazendo água', 'sos'), ('fazendo água, o que faço?', 'sos'), ('tá fazendo água demais', 'sos'),
    ('fazendo água potável', 'fallback'), ('fazendo água doce', 'tanques'), ('fazendo água na boca', 'fallback'), ('o bebedouro está fazendo água', 'fallback'),
    ('a máquina de gelo está fazendo água', 'fallback'), ('o dessalinizador do barco está fazendo água', 'dessalinizador'), ('o ar está fazendo água', 'base'),
    # (2) a guarda não vale para a frase inteira: quem relata alagamento cita o que molhou (celular, geladeira, filtro, gelo)
    ('entrou água no barco e molhou o celular', 'sos'), ('entrou água no barco e a geladeira parou', 'sos'), ('entrou água no barco, o filtro de água está encharcado', 'sos'),
    ('estamos fazendo água e a geladeira parou', 'sos'), ('o barco está fazendo água e o gelo acabou', 'sos'), ('a água subiu muito rápido no barco e o celular molhou', 'sos'),
    ('a geladeira parou, estamos fazendo água', 'sos'), ('o ar condicionado parou e estamos fazendo água', 'sos'), ('o dessalinizador parou e o barco está fazendo água', 'sos'),
    ('entrou água na bota', 'fallback'), ('a temperatura da água subindo no barco', 'base'),
    # (3) a água a bordo nas formas comuns: «está entrando», «não para de entrar», «enchendo/cheio de água»
    ('a água está entrando', 'sos'), ('a água tá entrando', 'sos'), ('a água está entrando pelo casco', 'sos'), ('a água está entrando no casco', 'sos'), ('a água não para de entrar', 'sos'),
    ('não para de entrar água', 'sos'), ('o barco está enchendo de água', 'sos'), ('o barco está cheio de água', 'sos'), ('barco cheio de água', 'sos'), ('lancha encheu de água', 'sos'),
    ('a cabine está cheia de água', 'sos'), ('o barco está cheio de água doce', 'tanques'),
    # (4) o relato do porão com «está/tá», a bomba que não para e o alarme que disparou (PROMPT §2.2: vai para sos, com o passo a passo); a pergunta neutra segue a rota do porão
    ('o porão está cheio de água', 'sos'), ('a água está subindo no porão', 'sos'), ('a água está entrando no porão', 'sos'), ('o porão está enchendo', 'sos'),
    ('o nível do porão está subindo', 'sos'), ('bombas de porão não param', 'sos'), ('a bomba de porão não está dando conta', 'sos'), ('o porão está cheio', 'sos'),
    ('o porão tá cheio', 'sos'), ('o alarme do porão disparou', 'sos'), ('alarme de porão', 'sos'), ('o alarme de porão tocou', 'sos'), ('disparou o alarme do porão', 'sos'),
    ('o alarme do porão está tocando', 'sos'), ('alarme da bomba de porão soou', 'sos'),
    ('como testo as bombas de porão', 'porao'), ('testar o alarme de porão', 'base'), ('como funciona o alarme do porão', 'base'), ('o que fazer quando o alarme do porão tocar', 'base'),
    ('alarme do painel do porão', 'base'), ('a bomba de porão não está ligando', 'porao'), ('a água do tanque acabou', 'tanques'),
    # (5) o eixo com palavras no meio e a baliza do EPIRB que disparou, ativou ou foi acionada (a «baliza» sozinha é sinalização)
    ('o eixo da hélice de bombordo quebrou agora mesmo', 'sos'), ('o eixo do motor de boreste quebrou', 'sos'),
    ('a baliza do barco disparou sozinha', 'epirb'), ('a baliza ativou', 'epirb'), ('a baliza foi acionada', 'epirb'), ('a baliza disparou sozinha', 'epirb'),
    # 1b, quarta revisão: a baliza de canal é sinalização, não o EPIRB. O sinônimo baliza→epirb (PROMPT §2.3) e o «canal» fechavam os 60 % da busca no «Disparo por engano: desligue e avise
    # no canal 16» (de segurança: trecho no topo barra a IA, que sabe de balizamento); agora, com palavra de sinalização e sem palavra só do EPIRB, a busca não traz o guia do EPIRB.
    ('baliza cardinal', 'fallback'), ('a baliza de canal', 'fallback'), ('o eixo estava bom quando o barco partiu', 'fallback'), ('o eixo da hélice está ok', 'fallback'),
    # (6) «tocou o fundo»: o barco toca o fundo (SOS); a âncora, o ferro, a poita e a sonda tocam o fundo no fundeio (rotina)
    ('a âncora tocou o fundo', 'ancora'), ('a âncora tocou no fundo', 'ancora'), ('quando a âncora tocou no fundo quantos metros de cabo eu solto?', 'ancora'),
    ('o ferro já tocou no fundo', 'ancora'), ('a poita tocou o fundo', 'fallback'), ('a sonda tocou o fundo', 'fallback'), ('o mergulhador tocou o fundo', 'fallback'),
    ('a âncora raspou numa pedra', 'ancora'), ('a âncora esbarrou numa pedra', 'ancora'),
    ('o barco tocou o fundo', 'sos'), ('a quilha tocou o fundo', 'sos'), ('o barco raspou numa pedra', 'sos'),
    # (7) a guarda da mangueira de uso também é local: a de combustível que estoura e molha a pia é emergência; a de lavagem e a do ar-condicionado não
    ('a mangueira de combustível estourou e molhou a pia', 'sos'), ('a mangueira de água salgada soltou e o chuveiro parou', 'sos'),
    ('rompeu a mangueira do escapamento, a geladeira desligou', 'sos'), ('a mangueira de lavagem estourou e a pia entupiu', 'fallback'),
    # (8) o leme e a baliza com uma palavra a mais, a água que entra no presente, quem pula do barco e o «homem» (a PESSOA tinha «homens?», que não pega «homem»)
    ('o leme do barco quebrou', 'sos'), ('o leme da lancha travou agora', 'sos'), ('perdi totalmente o leme', 'sos'), ('o leme está com folga', 'fallback'),
    ('o leme do barco precisa de graxa', 'fallback'), ('como ajustar o leme', 'fallback'),
    ('ele pulou da lancha', 'sos'), ('pulou da lancha', 'sos'), ('caiu um homem do barco', 'sos'), ('o homem caiu na água', 'sos'), ('o homem da marina chegou', 'fallback'),
    ('entra água pelo casco', 'sos'), ('entra água no tanque de água doce', 'tanques'),
    ('disparou a baliza', 'epirb'), ('disparou a baliza do barco', 'epirb'), ('acionei a baliza', 'epirb'),
    # ——— 1b, quarta revisão (achados da revisão do commit a237ba8): a vizinhança das frases pedidas que ainda ia à IA na nuvem (fallback, PEDE_IA True) ou à resposta de rotina ———
    # (1) perigo, água a bordo, encalhe e batida que vem aí
    ('estamos em perigo', 'sos'), ('estou em perigo', 'sos'), ('estamos em perigo de vida', 'sos'), ('risco de vida', 'sos'), ('corremos risco de vida', 'sos'),
    ('preciso de ajuda urgente', 'sos'), ('preciso urgente de ajuda', 'sos'), ('estamos perdidos no mar', 'sos'),
    ('o barco está pegando água', 'sos'), ('estamos pegando água', 'sos'), ('tá entrando muita água', 'sos'), ('está entrando muita água no barco', 'sos'),
    ('vamos bater', 'sos'), ('vamos bater numa pedra', 'sos'), ('o barco raspou no fundo', 'sos'), ('encostamos numa pedra', 'sos'), ('estamos em cima de uma pedra', 'sos'),
    # (2) pessoa na água ou perdida de vista, na ordem «perdi X de vista» e com «foi ao mar»
    ('mulher ao mar', 'sos'), ('o marinheiro foi ao mar', 'sos'), ('tripulante foi ao mar', 'sos'), ('meu amigo foi ao mar', 'sos'), ('ele se afogou', 'sos'),
    ('perdi o mergulhador de vista', 'sos'), ('perdi meu amigo de vista', 'sos'), ('perdemos a mulher de vista', 'sos'), ('perdi a pessoa de vista', 'sos'),
    ('perdemos o homem de vista', 'sos'), ('ninguém consegue ver a pessoa que caiu', 'sos'),
    # (3) saúde: respiração, coração, fratura, corte, engasgo, queimadura, ser atingido por um cabo
    ('ele parou de respirar', 'sos'), ('ela não respira', 'sos'), ('ele não está respirando', 'sos'), ('ela não está respirando', 'sos'), ('ataque cardíaco a bordo', 'sos'),
    ('parada cardíaca', 'sos'), ('enfarte', 'sos'), ('fratura exposta', 'sos'), ('corte profundo no braço', 'sos'), ('cortou a mão feio', 'sos'), ('quebrou o braço', 'sos'),
    ('ele está engasgado', 'sos'), ('queimou a mão no escapamento', 'sos'), ('pessoa passando mal no barco', 'sos'), ('cabo estourou e acertou alguém', 'sos'),
    ('prendeu a mão no cabo', 'sos'),
    # (4) fogo sem a palavra e explosão
    ('tem chama no painel', 'sos'), ('tem chama na cozinha', 'sos'), ('explodiu o motor', 'sos'),
    # (5) governo, propulsão, leme, hélice e eixo
    ('o leme emperrou', 'sos'), ('leme preso', 'sos'), ('o leme caiu', 'sos'), ('o leme saiu', 'sos'), ('perda de governo', 'sos'), ('o barco não obedece ao leme', 'sos'),
    ('perdemos a propulsão', 'sos'), ('sem propulsão', 'sos'), ('estamos sem propulsão e sem governo', 'sos'), ('estamos sem controle', 'sos'), ('hélice quebrada', 'sos'),
    ('a hélice enroscou numa rede', 'sos'), ('o eixo soltou', 'sos'), ('os dois motores pararam e estamos indo para as pedras', 'sos'), ('vento nos levando para as pedras', 'sos'),
    # (6) combustível e gás, na ordem inversa das frases que já estavam na lista
    ('o diesel está vazando', 'sos'), ('tem diesel vazando', 'sos'), ('combustível vazando', 'sos'), ('tem diesel vazando no porão', 'sos'), ('tem combustível no porão', 'sos'),
    ('diesel no porão', 'sos'), ('vazamento no tanque de diesel', 'sos'), ('o tanque de diesel está vazando', 'sos'), ('gás vazando', 'sos'), ('cheiro forte de gás', 'sos'),
    # (7) o alarme de nível do porão que disparou é relato de alagamento (sos), não a rotina do porão
    ('o alarme de nível do porão disparou', 'sos'), ('o alarme de nível do porão está tocando', 'sos'), ('o alarme do painel do porão disparou', 'sos'),
    ('disparou o alarme de nível do porão', 'sos'), ('o alarme disparou no porão', 'sos'),
    # o que NÃO vira SOS (a rotina ao lado: o «caiu» das coisas, o motor que engasga, o tanque de água doce, a conversa)
    ('o motor engasgou', 'motores'), ('cortou a energia', 'fallback'), ('queimou o fusível', 'fallback'), ('quebrou o braço do guincho', 'fallback'),
    ('vamos bater um papo', 'fallback'), ('tem chama no fogão?', 'fallback'), ('o tanque de água doce está vazando', 'tanques'), ('o tanque está vazando', 'tanques'),
    ('zona de perigo da carta', 'fallback'), ('trocar a hélice', 'fallback'), ('o leme está pesado', 'fallback'), ('estamos indo para as pedras de Cabeçudas', 'fallback'),
    ('estou pegando água no cais', 'fallback'), ('perdi o controle remoto', 'fallback'), ('estamos sem controle remoto', 'fallback'), ('os dois motores desligaram', 'motores'),
    ('por que a baliza do canal está piscando?', 'fallback'), ('a baliza do canal está apagada', 'fallback'), ('baliza lateral verde', 'fallback'),
    ('a baliza de entrada da barra está apagada', 'fallback'),
]
# As chaves de emergência (§2.3 do PROMPT): nunca vão à IA na nuvem, qualquer que seja a pergunta
CHAVES_LOCAIS = ('sos', 'epirb', 'seafire', 'salvatagem', 'canal16', 'oleo')
# IA na nuvem (quando a tela chama a IA, com o aparelho ativado): SEM DADOS, trecho do guia e pergunta sobre o app — nunca
# emergência, óleo, registro no diário, resposta pronta ou só um cumprimento.
PEDE_IA = {
    'Oque você faz?': True, 'o que vc sabe fazer?': True, 'como ligar o gerador?': True, 'qual o preço do dólar?': False, 'não registre isso': True,
    '': False, 'oi, bom dia': False, 'MAYDAY, homem ao mar!': False, 'pressão de óleo baixa no motor BB': False,
    'Registre no diário: saída com 4 pessoas': False, 'autonomia': False, 'é seguro sair hoje?': False, 'diagnóstico': False,
    'a IA não está funcionando': False, 'qual a rajada máxima que o barco aguenta?': True,
    # revisão do C5: base com trecho de segurança no topo (o respostaBase marca a.seguranca) e a rota seafire ficam no aparelho
    'teste da baliza': False, 'como acionar o disparo manual do sistema fixo?': False, 'supressão': False, 'botão distress': False,
    # (revisão 7: a pergunta do cartão do AIS deixou de trazer o §2 "Identificação", de segurança, ao topo: o topo é o §3 do guia do AIS, sem
    # `seguranca`, e a IA responde a partir dele)
    'transponder em-trak': True,
    # revisão 2 do C5: o 1º trecho do buscaBase de segurança barra a IA qualquer que seja a chave (aqui, a saudação)
    'como você me ajuda com o teste da baliza?': False, 'o que você sabe sobre o teste da baliza?': False,
    'o que fazer depois do disparo do sistema fixo': False, 'o sistema fixo disparou': False,
    'como lançar com o guincho Lewmar': True, 'como ligar o radar Garmin': True, 'como engatar o piloto automático Raymarine': True,
    # revisão 3 do C5: como antes do C5 (fallback com a IA)
    'quais equipamentos tem a bordo?': True, 'equipamentos do barco': True, 'modelo dos equipamentos': True,
    # revisão 4 do C5: pergunta comum sem trecho de segurança no topo vai à IA (ou fica na resposta pronta, como antes do C5)
    'como religar o gerador depois de desligar': False, 'como abrir o motor': False, 'como abrir o gerador': False,
    'como abrir o acesso ao motor': False, 'posso abrir o acesso ao motor para conferir o óleo': False,
    'como abrir a ventilação': True, 'como desligar a ventilação': True, 'como ligar a ventilação depois de desligar': True,
    'como religar a ventilação depois de desligar': True, 'o alarme disparou': True, 'como desligar o sistema': True,
    'como religar o motor depois de desligar': True, 'quando trocar o óleo do motor?': True,
    'como esfriar o motor': True, 'como esfriar o motor depois de navegar': True, 'como esfriar o motor depois de navegar rápido': True,
    'o sistema descarregou': False, 'o sistema fixo disparou sozinho': False, 'distress': False, 'como usar o botão distress': False,
    # revisão 5 do C5: resposta pronta fica no aparelho; o trecho do guia vai à IA; o protocolo de homem ao mar e de PAN-PAN, não
    'como ligar o plotter': False, 'como ligar o sistema de som': False, 'como ligar o sistema de áudio': False, 'como funciona o sistema elétrico': False,
    'como desligar a bomba': False, 'como ligar o carregador': True, 'como ligar o carregador de bateria': True,
    'alarme de temperatura do motor': True, 'seakeeper temperatura alta': True, 'trocar o filtro do ar condicionado': True,
    'como ligar o ar': True, 'como ligar o ar condicionado': True, 'como desligar o ar': True, 'substituir filtro de ar': True,
    'como funciona o piloto automático': True, 'alarme de âncora': True,
    'pessoa caiu da lancha': False, 'não vejo a pessoa que caiu': False, 'perdemos de vista quem caiu': False,
    'sem governo': False, 'barco sem governo': False, 'pane no barco': False,
    'o parafuso caiu': True, 'quantas pessoas a bordo': False, 'a pessoa da marina': True, 'o governo federal': True,
    # revisão 6 do C5: o trecho do guia (outra bomba, bateria de partida) vai à IA; a resposta pronta e o protocolo de pessoa ao mar, não;
    # o disjuntor, a energia e a vista do mar são conversa comum (IA); o trecho de segurança nomeado barra a IA
    'como trocar o rotor da bomba de água salgada': True, 'quando trocar o rotor da bomba de água salgada': True, 'rotor da bomba': True,
    'alarme da bomba de água salgada': True, 'como ligar a bomba da climatização': True, 'como trocar o rotor da bomba do gerador': True,
    'a bomba de circulação': True, 'bombas de porão': False, 'como ligar as bombas de porão': False,
    'como trocar a bateria de partida': True, 'bateria de partida': False,
    'o disjuntor caiu, qual o procedimento': True, 'a bateria caiu, procedimento': False, 'o plotter caiu, como resolver': False,
    'a energia caiu': True, 'o wifi caiu': True, 'caiu a chave no mar': True,
    'onde fica o manual do motor': False, 'tem vista para o mar?': True, 'qual a vista do mar': True, 'a temperatura do mar caiu': True,
    'pessoa ao mar': False,
    'como religar o gerador depois que o sistema fixo disparou': False, 'o sistema fixo disparou, como religo o gerador?': False,
    # revisão 7 do C5: a resposta pronta e a bomba de esgoto (rota 'porao') ficam no aparelho; o trecho do guia e a pergunta sem resposta vão à IA
    'onde fica o plotter': True, 'como ver o radar': False, 'como ver o garmin': False, 'como ver o icom': True, 'como ver o fusion': False,
    'como ver o som': False, 'como ver o áudio': False, 'onde fica o motor': False, 'como ver os navios no radar': False,
    'como ver o radar no plotter': True, 'como ver a posição no plotter': True, 'como ver o motor no garmin': False,
    'como ver o gerador no garmin': False, 'como funciona a identificação do transponder': False, 'o que fazer antes de largar': False,
    # (fechamento do C5: a resposta pronta da climatização e do áudio, não a IA)
    'onde fica o ar condicionado': False, 'onde fica o ar-condicionado': False, 'onde fica o som': False,
    'a bomba de esgoto não para': False, 'a bomba de esgoto está enchendo de água': False, 'bomba de esgoto': False,
    'bomba do estabilizador': False, 'alarme da bomba do seakeeper': True, 'bomba do piloto automático': False, 'bomba hidráulica': True,
    'a bomba do gerador': False, 'bomba do dessalinizador': False, 'como ligar a bomba do dessalinizador': True, 'bomba de pressurização': True,
    'a bomba de circulação não funciona': True, 'bomba de lavagem': True, 'como funciona a bomba de porão': True,
    'em caso de alarme': True, 'em caso de falha do motor': False, 'qual o procedimento padrão': True, 'qual o protocolo de bordo': True,
    'confirmar com o protocolo de bordo': True, 'confirmar protocolo': True,
    # 1b: emergência, EPIRB, Seafire, salvatagem e canal 16 nunca vão à IA; o que não é emergência continua indo
    'caiu do barco': False, 'tem gente na água': False, 'entrou água no motor': False, 'o barco bateu em uma pedra': False, 'perdi o leme': False,
    'o eixo quebrou': False, 'a mangueira estourou': False, 'alguém caiu': False, 'estamos sem governo': False, 'o leme travou': False,
    'a baliza de canal': True, 'baliza do canal': True, 'a baliza do canal está apagada': True,
    'a baliza disparou': False, 'o que é o disparador hidrostático?': False, 'como testar a baliza?': False, 'onde fica a baliza': False,
    'o disjuntor caiu': True, 'tem vista para o mar': True, 'sem governo federal': True, 'a temperatura da água está subindo': True,
    'disparou o sistema da casa de máquinas': False, 'quanto tempo esperar para abrir a praça de máquinas depois da descarga': False,
    'onde ficam os coletes?': False, 'sinalizadores vencidos?': False, 'onde fica o extintor': False, 'extintor com fogo na cozinha': False,
    'qual o MMSI do barco?': False, 'luz da boia': True, 'boia de amarração': True,
}
# 1b, terceira revisão: toda frase nova do bloco acima que espera chave de emergência (sos, epirb…) fica no aparelho (PEDE_IA False), e a rotina ao lado vai à IA
# só quando é conversa de fallback (trava §2.3: emergência local, nunca na nuvem)
_REV3 = CASOS[[q for q, _ in CASOS].index('fazendo água'):]
PEDE_IA.update({q: False for q, k in _REV3 if k in CHAVES_LOCAIS})
PEDE_IA.update({q: True for q in ('cortou a energia', 'queimou o fusível', 'quebrou o braço do guincho', 'vamos bater um papo', 'tem chama no fogão?', 'zona de perigo da carta',
                                  'trocar a hélice', 'o leme está pesado', 'estamos indo para as pedras de Cabeçudas', 'estou pegando água no cais', 'perdi o controle remoto',
                                  'estamos sem controle remoto', 'por que a baliza do canal está piscando?', 'a baliza do canal está apagada', 'baliza lateral verde',
                                  'a baliza de entrada da barra está apagada')})
# as respostas de dado de bordo que leem o quadro (uma pergunta de cada, todas em CASOS)
FONTE_DO_INSTANTE = ['Telemetria agora', 'posição agora', 'nível dos tanques', 'clima e vento', 'bateria 24 v', 'estabilizador Seakeeper', 'motores volvo penta',
                     'qual a pressão do óleo?', 'horímetros', 'é seguro sair hoje?', 'âncora garrando?', 'autonomia', 'quantas horas tem o gerador',
                     'consumo de diesel', 'checklist de saída', 'para onde vamos hoje?', 'bombas de porão']
PEDE_IA.update({'fazendo água potável': True, 'fazendo água na boca': True, 'o bebedouro está fazendo água': True, 'a máquina de gelo está fazendo água': True,
                'baliza cardinal': True, 'a poita tocou o fundo': True, 'a sonda tocou o fundo': True, 'o mergulhador tocou o fundo': True,
                'o eixo estava bom quando o barco partiu': True, 'o eixo da hélice está ok': True, 'entrou água na bota': True})

# revisão da P3B (3ª): a «corrente» da âncora (a amarra, em metros no contador do guincho) vai para a rota `ancora`, antes da maré; a de maré, a correnteza e a da bateria seguem as suas
ROTAS_CORRENTE = [('quantos metros de corrente?', 'ancora'), ('quanta corrente tem lançada?', 'ancora'), ('metros de corrente lançados', 'ancora'), ('quanto de corrente está na água?', 'ancora'),
                  ('corrente no contador do guincho', 'ancora'), ('a corrente está forte?', 'mare'), ('corrente de maré agora', 'mare'), ('quanta corrente tem na maré?', 'mare'),
                  ('qual a correnteza?', 'mare'), ('qual a corrente da bateria?', 'eletrico')]
CASOS = CASOS + ROTAS_CORRENTE

# Fase 3, P3C (PROMPT Fase 3 «Rotas novas», §2.3, §2.6, §2.7; Fase 7 «Testes novos e acréscimos › cerebro.py»): as perguntas das rotas novas e as que elas não podem roubar.
# (pergunta, chave, vai à IA?). As rotas novas respondem no aparelho (PEDE_IA False); a pergunta de guia ou de relato que elas deixam passar segue como antes.
ROTAS_P3C = [
    # posição: «onde estamos», «rumo», «COG», «quantos nós»
    ('onde estamos?', 'posicao', False), ('qual o rumo?', 'posicao', False), ('qual o COG?', 'posicao', False), ('quantos nós estamos fazendo?', 'posicao', False), ('qual o rumo sobre o fundo?', 'posicao', False),
    # profundidade (só a leitura: o alarme, a mínima e o relato seguem o guia ou a IA)
    # Fase 3 (P3E, F10): «sonda mostrando pouca profundidade» é uma variante literal do item EL-08 do FAQ (água rasa): sem resposta pronta nem trecho do guia, o chat responde pelo item
    # (faqEquip, ainda com PEDE_IA true: não é de segurança); antes era `fallback`. Nunca é a leitura calma da profundidade (o que o caso protege).
    ('qual a profundidade?', 'profundidade', False), ('qual a profundidade aqui?', 'profundidade', False), ('quanto fundo tem aqui?', 'profundidade', False), ('leituras da profundidade', 'profundidade', False),
    ('profundidade mínima na sonda', 'base', True), ('qual a profundidade mínima para navegar?', 'base', True), ('alarme de profundidade da sonda', 'base', True), ('sonda mostrando pouca profundidade', 'faqEquip', True),
    ('como instalar o transdutor de profundidade', 'fallback', True), ('profundidade mínima para fundear', 'ancora', False),
    # ETA, distância e waypoint; «quanto falta» só junto de chegar, chegada, destino, waypoint, ponto, ETA ou o nome de um ponto da rota
    ('qual a hora de chegada?', 'eta', False), ('quanto falta para chegar?', 'eta', False), ('quanto falta para o destino?', 'eta', False), ('qual o próximo waypoint?', 'eta', False), ('qual a distância até o destino?', 'eta', False),
    ('quanto falta para o Estaleirinho?', 'eta', False), ('qual o ETA?', 'eta', False), ('quantas milhas percorremos hoje?', 'eta', False), ('que horas chegamos?', 'eta', False), ('distância percorrida hoje', 'eta', False),
    ('quanto falta para a troca de óleo?', 'horimetros', False), ('quanto falta para a revisão do gerador?', 'gerador', False), ('quanto falta para o diesel acabar', 'autonomia', False),
    ('quantas milhas de alcance tem o barco?', 'autonomia', False), ('previsão de chegada do técnico da oficina', 'checklistChegada', False),
    # alarmes ativos (o «alarme de <equipamento>», o «alarme disparou» e o «em caso de alarme» seguem as rotas deles)
    ('tem algum alarme ativo?', 'alarmes', False), ('existe algum alarme ativo no barco?', 'alarmes', False), ('quais alarmes estão ativos?', 'alarmes', False), ('tem algum alerta?', 'alarmes', False),
    ('o alarme está tocando', 'alarmes', False), ('alarmes ativos', 'alarmes', False), ('tem alerta de tempestade?', 'fallback', True), ('é seguro sair com o alarme ativo?', 'seguro', False),
    # estado do mar (a bordo), temperatura da água do mar e do motor
    ('como está o estado do mar?', 'ondas', False), ('qual a altura das ondas?', 'ondas', False), ('previsão de ondas amanhã', 'clima', False), ('as ondas bateram no casco', 'fallback', True),
    ('qual a temperatura da água?', 'temperaturaAgua', False), ('temperatura do mar', 'temperaturaAgua', False),
    ('qual a temperatura do motor?', 'arrefecimento', False), ('temperatura dos motores', 'arrefecimento', False), ('como está a temperatura do motor?', 'arrefecimento', False), ('como está o arrefecimento?', 'arrefecimento', False),
    ('qual a temperatura da água do motor?', 'arrefecimento', False), ('temperatura alta no motor BE', 'base', True),
    # como está a navegação / situação agora; pessoas a bordo
    ('como está a navegação?', 'navegacao', False), ('situação agora', 'navegacao', False), ('como estamos?', 'navegacao', False), ('como estamos de diesel?', 'autonomia', False),
    ('quantas pessoas estão a bordo?', 'pessoas', False), ('temos 6 pessoas a bordo', 'fallback', True),
    # embarcação (calado, comprimento, dimensões, lotação, modelo, registro)
    ('qual o calado do barco?', 'embarcacao', False), ('qual o comprimento?', 'embarcacao', False), ('dimensões do barco', 'embarcacao', False), ('qual a lotação?', 'embarcacao', False), ('qual o modelo do barco?', 'embarcacao', False),
    ('qual o registro do barco?', 'embarcacao', False), ('qual o número do registro do barco?', 'embarcacao', False), ('a lotação do barco é 12?', 'embarcacao', False), ('qual o registro de hoje?', 'fallback', True),
    ('qual o deslocamento do Seakeeper?', 'estabilizador', False),
    # mmsi (o MMSI da etiqueta do rádio; o do cadastro só na 2ª linha) e AIS (rota própria, antes do canal 16)
    ('meu MMSI', 'mmsi', False), ('qual o MMSI?', 'mmsi', False), ('MMSI da licença de estação', 'mmsi', False), ('qual o numero do MMSI do rádio?', 'mmsi', False),
    ('quantos alvos no AIS?', 'ais', False), ('tem AIS?', 'ais', False), ('AIS', 'ais', False), ('AIS em modo silencioso', 'base', True), ('Identificação do AIS', 'base', False), ('quantos alvos tem no radar?', 'eletronicos', False),
    # sobreDados (§2.6) e o que NÃO cai nela
    ('esses dados são reais?', 'sobreDados', False), ('isso é simulado?', 'sobreDados', False), ('o barco existe?', 'sobreDados', False), ('isso é real?', 'sobreDados', False), ('é de verdade?', 'sobreDados', False),
    ('a posição é real?', 'sobreDados', False), ('o alarme é real?', 'sobreDados', False), ('os números são reais?', 'sobreDados', False), ('isso é uma simulação?', 'sobreDados', False),
    ('quanto custa o diesel em reais?', 'autonomia', False), ('qual a velocidade real do barco?', 'posicao', False), ('qual o vento real no barco agora?', 'clima', False), ('como realizar a troca de óleo do barco?', 'base', True),
    ('existe alguma pendência no barco?', 'anomalias', False), ('qual o consumo real do barco?', 'consumo', False), ('dados em tempo real', 'fallback', True), ('a bateria do barco é real?', 'eletrico', False),
    ('quanto custa isso, é de verdade?', 'foraBarco', False), ('qual o preço de uma lancha?', 'foraBarco', False),
    # o que as rotas novas não podem roubar (PROMPT Fase 3: «checklist de chegada», «alarme de óleo acendeu», «temperatura hoje», «alarme de fluxo da climatização»)
    ('o alarme disparou', 'fallback', True), ('alarme de fluxo da climatização', 'base', True), ('alarme de temperatura do motor', 'base', True), ('a temperatura da água está subindo', 'base', True),
    ('checklist de chegada', 'checklistChegada', False), ('alarme de óleo acendeu', 'oleo', False), ('temperatura hoje', 'clima', False),
    # foraBarco (§2.7)
    ('qual a cotação do euro?', 'foraBarco', False), ('notícias de hoje', 'foraBarco', False), ('quem vai ganhar a eleição?', 'foraBarco', False), ('preço do bitcoin', 'foraBarco', False), ('oi, qual o preço do dólar?', 'foraBarco', False),
    ('quanto está o dólar hoje?', 'foraBarco', False), ('o euro subiu?', 'foraBarco', False),
]
CASOS = CASOS + [(q, k) for q, k, _ in ROTAS_P3C]
PEDE_IA.update({q: ia for q, k, ia in ROTAS_P3C})

# Revisão da P3C: o que as rotas novas roubavam das que já respondiam certo (a chave e o PEDE_IA são os de ANTES da P3C, salvo onde o PROMPT pede a rota nova).
ROTAS_P3C_REV = [
    # «situação atual/agora de <assunto>» é do assunto; só a frase inteira é a navegação
    ('situação atual do gerador', 'gerador', False), ('situação atual dos documentos', 'docsvenc', False), ('situação atual da manutenção', 'manutencao', False), ('situação agora dos tanques', 'tanques', False),
    ('qual a situação atual do barco?', 'navegacao', False), ('situação de bordo', 'navegacao', False), ('qual é a situação atual?', 'navegacao', False), ('como está a navegação do piloto automático?', 'base', True),
    # o cadastro do barco não responde pelo comprimento, o fabricante, a ficha, o ano e a lotação de OUTRA coisa a bordo
    ('quem fabricou o motor', 'motores', False), ('ficha técnica do motor', 'motores', False), ('ano de fabricação do motor', 'motores', False), ('qual o comprimento da corrente da âncora', 'ancora', False),
    ('qual o comprimento da amarra', 'fallback', True), ('comprimento do cabo de reboque', 'fallback', True), ('quem fabricou o guincho', 'fallback', True), ('lotação do tender', 'fallback', True),
    ('quantas pessoas cabem no bote', 'fallback', True), ('qual o comprimento da sonda', 'fallback', True), ('quantas pessoas cabem no barco', 'embarcacao', False), ('qual a lotação máxima da lancha', 'embarcacao', False),
    ('qual o tamanho do barco', 'embarcacao', False), ('qual a largura do barco', 'embarcacao', False), ('quantas pessoas cabem?', 'embarcacao', False), ('quantos a bordo?', 'pessoas', False),
    # a temperatura do motor é a dos motores principais: a do gerador, do Seakeeper e da climatização é do equipamento
    ('arrefecimento do gerador', 'gerador', False), ('arrefecimento do Seakeeper', 'estabilizador', False), ('arrefecimento da climatização', 'climatizacao', False), ('como está o arrefecimento do gerador?', 'base', True),
    ('qual a temperatura do motor do gerador', 'base', True), ('temperatura do motor do Seakeeper', 'base', True), ('temperatura da água do arrefecimento', 'arrefecimento', False), ('temperatura da água do Seakeeper', 'base', True),
    # o alarme que SOA não é «nenhum alarme ativo»; com o lugar ou o equipamento, a rota dele; o resgate que se espera não é o ETA da rota
    ('o alarme soando', 'alarmes', False), ('qual alarme está tocando', 'alarmes', False), ('alarmes tocando na cabine', 'climatizacao', False), ('alarme ativo no Seakeeper', 'base', True),
    ('quanto falta para chegar o resgate', 'fallback', True), ('estamos esperando o resgate, que horas chega', 'fallback', True), ('quando chega o resgate', 'fallback', True),
    # o ETA/waypoint e a profundidade não são o guia do plotter, o porão, o consumo, o fundeio nem o relato de falha do sensor
    ('como criar um waypoint no plotter', 'eletronicos', False), ('como criar um waypoint?', 'fallback', True), ('como marcar um waypoint no plotter?', 'eletronicos', False),
    ('quantas milhas por litro faz o barco', 'fallback', True), ('quantas milhas percorremos por litro?', 'fallback', True), ('quantas milhas por galão', 'fallback', True), ('quantas milhas por hora estamos fazendo', 'posicao', False),
    ('quantas milhas tem de Camboriú a Itajaí', 'fallback', True), ('quantas milhas faltam para chegar?', 'eta', False), ('qual a profundidade do porão', 'porao', False),
    ('onde fica o transdutor de profundidade', 'fallback', True), ('o ecobatímetro está com defeito', 'fallback', True), ('quanto de corrente para essa profundidade?', 'ancora', False),
    ('a âncora aguenta que profundidade?', 'ancora', False), ('qual a profundidade de fundeio?', 'base', True), ('qual a profundidade máxima do fundeio', 'base', True), ('o sensor de profundidade não funciona', 'fallback', True),
    ('o ecobatímetro está com erro', 'fallback', True), ('profundidade zerada na sonda', 'base', True), ('o transdutor de profundidade quebrou', 'fallback', True), ('o sensor de profundidade está desligado', 'fallback', True),
    ('a sonda mostra profundidade errada', 'fallback', True), ('qual a profundidade do canal', 'fallback', True), ('profundidade da marina', 'fallback', True),
    # foraBarco não engole a reversora (câmbio), o balanço (jogo) nem a bolsa estanque; o dinheiro e o esporte seguem fora do barco
    ('o câmbio está duro', 'fallback', True), ('o câmbio não engata', 'fallback', True), ('a marcha não entra, problema no câmbio', 'fallback', True), ('problema no câmbio', 'fallback', True),
    ('câmbio, desligo', 'fallback', True), ('troca de câmbio', 'fallback', True), ('o barco está com muito jogo', 'fallback', True), ('qual o jogo do barco agora', 'fallback', True),
    ('quantos graus de jogo?', 'fallback', True), ('jogo de ferramentas', 'fallback', True), ('bolsa de gelo', 'fallback', True),
    ('câmbio do dia', 'foraBarco', False), ('câmbio hoje', 'foraBarco', False), ('qual o câmbio do dólar hoje', 'foraBarco', False), ('tem jogo hoje?', 'foraBarco', False), ('a bolsa subiu hoje', 'foraBarco', False),
    ('bolsa de valores', 'foraBarco', False),
    # a temperatura do mar que caiu é relato; a água fria é a leitura
    ('a água do mar está fria', 'temperaturaAgua', False), ('a temperatura da água caiu', 'base', True),
    # sobreDados: «real»/«de verdade» como medida não é a pergunta sobre os dados; a lancha, o app e o Capitão IA são
    ('qual o diesel real do barco?', 'autonomia', False), ('qual a profundidade real do barco?', 'profundidade', False), ('qual o calado real do barco?', 'embarcacao', False),
    ('quanto diesel tem de verdade no barco?', 'autonomia', False), ('qual o estado real do barco', 'fallback', True), ('existe um app de verdade para barcos?', 'fallback', True),
    ('o app é em tempo real?', 'fallback', True), ('os dados são em tempo real?', 'fallback', True), ('o vento é verdadeiro ou aparente?', 'clima', False), ('o rumo é verdadeiro ou magnético?', 'fallback', True),
    ('a lancha é real?', 'sobreDados', False), ('você é real?', 'sobreDados', False), ('o Capitão IA é real?', 'sobreDados', False), ('você é uma IA de verdade?', 'sobreDados', False),
    ('vocês simulam os dados?', 'sobreDados', False), ('esse barco existe de verdade?', 'sobreDados', False), ('a velocidade é real?', 'sobreDados', False), ('o consumo é real?', 'sobreDados', False),
    ('o diesel é real?', 'sobreDados', False), ('o gerador é de verdade?', 'gerador', False),
    ('qual o deslocamento do Seakeeper do barco?', 'estabilizador', False), ('qual o comprimento da âncora do barco', 'ancora', False), ('quantas milhas faltam até o limite de alcance?', 'autonomia', False),
    ('não estou vendo a profundidade', 'fallback', True), ('a temperatura do mar caiu', 'fallback', True),
]
CASOS = CASOS + [(q, k) for q, k, _ in ROTAS_P3C_REV]
PEDE_IA.update({q: ia for q, k, ia in ROTAS_P3C_REV})

# Revisão 2 da P3C. (1) A sobreDados (§2.6) é a pergunta direta sobre a autenticidade, em qualquer jeito natural de perguntar: o verbo e o «real» com até 3 palavras no meio, o nome dos dados («dados reais?»),
# a ordem invertida, «o que é real aqui?», «estamos navegando de verdade?», «está simulado?», «é uma demo?», «é só uma simulação?», «isso é fake?»; a medida («diesel real», «tempo real», «em reais», «o vento é
# verdadeiro?») e o dinheiro não são ela. (2) A pergunta do MMSI que tem outro assunto junto fica com a rota dele (EPIRB, Seafire, rádio, vencimento). (3) A leitura calma só responde a pergunta neutra: o relato com
# número ou estado vai ao guia ou à IA. (4) A pergunta mista com o EPIRB, o Seafire, o canal 16, o PAN-PAN ou o DSC é do equipamento.
SOBRE_DADOS_SIM = [
    'são dados reais?', 'dados reais?', 'você usa dados reais?', 'vocês usam dados reais?', 'isso são dados reais?', 'esses são dados reais?', 'o app usa dados reais?', 'o app mostra dados reais?',
    'esses dados são reais, certo?', 'os dados são de fato reais?', 'os dados são reais de verdade?', 'são números de verdade?', 'são valores reais?', 'isso é um dado real?', 'é uma navegação real?', 'é uma viagem real?',
    'estamos navegando de verdade?', 'o barco está navegando de verdade?', 'você está simulando?', 'são reais esses dados?', 'são reais os dados?', 'está simulado?', 'é uma demo?', 'o que é real aqui?',
    'são leituras reais?', 'são dados de verdade?', 'esse app usa dados reais?', 'o app está conectado a um barco real?', 'é um simulador?', 'é só uma simulação?', 'estamos em uma simulação?',
    'esses dados são falsos?', 'isso é fake?', 'isso é real ou simulado?', 'isso é real ou não?', 'essa viagem é de verdade?', 'o app é de verdade?', 'as leituras são reais mesmo?', 'os dados do barco são reais, né?',
    'tudo isso é real?', 'é tudo de mentira?', 'os dados foram inventados?', 'são dados fictícios?', 'é uma demonstração?', 'os números são de verdade?', 'a navegação é real?', 'é real mesmo?', 'é de mentira?',
    'isso é inventado?', 'a velocidade de 18 nós é real?', 'são 12 leituras reais?', 'você usa dados reais, né?', 'o app usa dados reais mesmo?', 'os dados são reais ou é teste?',
    # revisão 3: «estar»/«tá»/«tão» no lugar de «ser», e a cauda «ou não», «não é?», «ou é real?»
    'os dados estão reais?', 'os números estão reais?', 'isso tá real?', 'tá real isso?', 'essas leituras tão reais?', 'é real ou não?', 'é real, não é?', 'é real não?', 'é simulado ou é real?',
    'os dados estavam reais?', 'isso está de verdade?', 'é simulado ou real?', 'os dados são reais, não é?', 'os dados são reais não?', 'os dados são de fato reais, não é?', 'os dados são de fato reais não?']
ROTAS_P3C_REV2 = [(q, 'sobreDados', False) for q in SOBRE_DADOS_SIM] + [
    # a medida, o dinheiro e o outro sentido de «real»/«verdadeiro»/«falso» não são a pergunta sobre os dados
    ('quanto de diesel é real?', 'autonomia', False), ('o vento é verdadeiro?', 'clima', False), ('o vento é real?', 'clima', False), ('o rumo é verdadeiro?', 'posicao', False),
    ('a velocidade é verdadeira ou aparente?', 'posicao', False), ('o ângulo do vento é verdadeiro ou aparente?', 'clima', False), ('qual é o norte verdadeiro?', 'fallback', True), ('qual é a velocidade real?', 'posicao', False),
    ('isso é o consumo real?', 'consumo', False), ('o valor está em reais?', 'fallback', True), ('os valores são em reais?', 'fallback', True), ('qual a velocidade verdadeira do vento?', 'clima', False),
    ('o alarme falso do porão', 'base', True), ('tem alarme falso?', 'fallback', True), ('qual o dado real da profundidade?', 'fallback', True), ('mostre os dados reais do consumo', 'consumo', False),
    ('quais são os valores reais?', 'fallback', True), ('quantas milhas reais percorremos?', 'fallback', True), ('rumo verdadeiro', 'posicao', False), ('vento real', 'clima', False),
    # a pergunta mista com o canal 16 é do equipamento (o PROMPT §2.6 não a tira do equipamento: a segurança vence)
    ('canal 16, os dados são reais?', 'canal16', False), ('pan-pan, o app é real?', 'canal16', False), ('DSC, esses dados são reais?', 'canal16', False),
    # o MMSI com outro assunto junto fica com a rota dele; o número do cadastro só na 2ª linha da rota mmsi
    ('o EPIRB usa o MMSI do barco?', 'epirb', False), ('o MMSI está cadastrado no EPIRB?', 'epirb', False), ('qual o MMSI do EPIRB?', 'epirb', False), ('o EPIRB está registrado no MMSI do barco?', 'epirb', False),
    ('o EPIRB tem MMSI?', 'epirb', False), ('MMSI do EPIRB e HEX ID', 'epirb', False), ('qual o MMSI da baliza?', 'epirb', False),
    ('como fazer um pan-pan com o MMSI?', 'canal16', False), ('pan pan e MMSI', 'canal16', False), ('tenho que mandar pan pan, MMSI?', 'canal16', False), ('DSC distress MMSI', 'canal16', False),
    ('como usar o botão DISTRESS do rádio com o MMSI', 'canal16', False), ('botão vermelho DSC e MMSI', 'canal16', False), ('teste do DSC com MMSI', 'canal16', False),
    ('o MMSI do rádio está programado para o DSC?', 'canal16', False), ('qual o MMSI e o canal 16?', 'canal16', False), ('o motor parou, qual o MMSI?', 'canal16', False),
    ('qual o MMSI da licença de estação e quando vence?', 'docsvenc', False), ('qual o MMSI e a validade da licença?', 'docsvenc', False), ('o MMSI vence?', 'docsvenc', False),
    ('qual o MMSI do Seafire?', 'seafire', False), ('o sistema fixo disparou, qual o MMSI?', 'seafire', False), ('o alarme disparou, qual o MMSI?', 'mmsi', False),
    ('qual o MMSI e o indicativo do barco?', 'mmsi', False), ('como programar o MMSI no rádio?', 'mmsi', False), ('qual o MMSI cadastrado?', 'mmsi', False), ('MMSI do transponder AIS', 'mmsi', False),
    # a pergunta mista do AIS com o roteiro de rádio é do rádio; o AIS sozinho segue a rota dele
    ('pan-pan, o que é o AIS?', 'canal16', False), ('teste do DSC, o que é o AIS?', 'canal16', False), ('botão DISTRESS, qual o ETA?', 'base', False),
    # a pergunta neutra continua com a leitura (a lista de palavras neutras não é estreita demais)
    ('qual a temperatura do motor esquerdo?', 'arrefecimento', False), ('quais as temperaturas do motor?', 'arrefecimento', False), ('capitão, qual a temperatura do motor?', 'arrefecimento', False),
    ('qual a temperatura do motor Cummins?', 'arrefecimento', False), ('qual a profundidade neste momento?', 'profundidade', False), ('quanto de água tem sob a quilha?', 'profundidade', False),
    ('qual a leitura do ecobatímetro?', 'profundidade', False), ('como está a profundidade?', 'profundidade', False), ('tem ondas?', 'ondas', False), ('como está o mar?', 'ondas', False),
    ('a água do mar está quente?', 'temperaturaAgua', False), ('qual a temperatura do mar agora?', 'temperaturaAgua', False),
    # a profundidade (a leitura do ecobatímetro) não é a da âncora, do transdutor, da corrente, do rio, da marina nem o relato de que a sonda falha
    ('qual a profundidade da âncora?', 'ancora', False), ('qual a profundidade do transdutor?', 'fallback', True), ('profundidade da corrente', 'mare', False), ('a profundidade falha', 'base', True),
    ('a profundidade funciona?', 'fallback', True), ('não vejo a profundidade', 'fallback', True), ('qual a profundidade do rio?', 'fallback', True), ('qual a profundidade da marina?', 'fallback', True),
    ('qual a profundidade do canal?', 'fallback', True), ('qual a profundidade do fundeio?', 'base', True),
]
CASOS = CASOS + [(q, k) for q, k, _ in ROTAS_P3C_REV2]
PEDE_IA.update({q: ia for q, k, ia in ROTAS_P3C_REV2})

# Revisão 3 da P3C. (1) O número do cadastro (710123456) só vai à pergunta NEUTRA do MMSI; perto de «colocar», «digitar», «cadastrar», do rádio, do VHF, do AIS, do DSC ou do plotter, em qualquer flexão do verbo, só o da etiqueta.
# (2) A leitura calma de cada rota nova (posição, ETA, alarmes, pessoas, navegação, embarcação) só responde a pergunta neutra: o relato de falha, o imperativo do plotter, o lugar fora da rota e a definição seguem a rota do
# equipamento, o guia ou a IA, como antes da P3C. (3) «Falso» e «fake» com alarme, alerta, sensor ou GPS são o falso alarme, nunca a autenticidade. (4) «Quem venceu/ganhou…» é de fora do barco. (5) Pedido de socorro que a lista
# SOS não pega («isso é real, preciso de ajuda», «isso não é um teste», «estamos em risco») é a rota sos; a frase de apresentação nunca responde a quem pede ajuda.
ROTAS_P3C_REV3 = [
    # MMSI: sempre a rota mmsi (a 1ª linha manda usar o da etiqueta do rádio); o número do cadastro some das perguntas de pôr o MMSI no aparelho (propriedade abaixo)
    ('como coloco o MMSI no rádio?', 'mmsi', False), ('coloque o MMSI no rádio', 'mmsi', False), ('digite o MMSI', 'mmsi', False), ('altere o MMSI do rádio', 'mmsi', False), ('como altero o MMSI?', 'mmsi', False),
    ('como cadastrar o MMSI no rádio?', 'mmsi', False), ('como atualizo o MMSI do VHF', 'mmsi', False), ('como habilito o MMSI no AIS?', 'mmsi', False), ('que MMSI eu coloco no rádio?', 'mmsi', False),
    ('qual MMSI eu digito no rádio?', 'mmsi', False), ('qual MMSI eu insiro no rádio?', 'mmsi', False), ('qual o MMSI para cadastrar no rádio?', 'mmsi', False), ('como cadastro o MMSI no rádio?', 'mmsi', False),
    ('qual MMSI devo usar no rádio?', 'mmsi', False), ('MMSI do barco para o plotter', 'mmsi', False), ('MMSI do AIS', 'mmsi', False), ('qual o MMSI da embarcação?', 'mmsi', False),
    # posição: «rumo» e «quantos nós» são palavras inteiras, e a definição de COG, SOG ou milha não é a leitura
    ('quantos nossos tripulantes tem?', 'fallback', True), ('rumores do porto', 'fallback', True), ('quantos nós tem uma milha náutica?', 'fallback', True), ('o que significa COG?', 'fallback', True),
    ('o que é SOG?', 'fallback', True), ('qual o rumo magnético?', 'fallback', True), ('quantos nós?', 'posicao', False), ('qual o rumo atual?', 'posicao', False), ('qual o COG atual?', 'posicao', False),
    # ETA e waypoint: o imperativo do plotter, o lugar fora da rota e o conceito não são a chegada da rota; o nome de um ponto da rota é
    ('crie um waypoint aqui', 'fallback', True), ('marque um waypoint', 'fallback', True), ('qual a distância até Itajaí?', 'fallback', True), ('quando chegamos em Itajaí?', 'fallback', True),
    ('distância até a costa', 'fallback', True), ('o que é ETA?', 'fallback', True), ('o ETA não atualiza', 'fallback', True), ('o waypoint sumiu', 'fallback', True), ('o ETA está certo?', 'fallback', True),
    ('o que é a lotação do barco?', 'fallback', True), ('o plotter perdeu o waypoint', 'eletronicos', False), ('o plotter não calcula o ETA', 'eletronicos', False), ('como está o ETA?', 'eta', False), ('quantas milhas por hora?', 'posicao', False),
    ('quantas milhas faltam para a Ilha das Cabras?', 'eta', False), ('quanto falta para a Barra Sul?', 'eta', False), ('qual a distância até a Ponta das Laranjeiras?', 'eta', False),
    # relato de falha + palavra da rota nova: a rota do equipamento, o guia ou a IA, nunca a leitura calma
    ('o motor parou, qual o ETA?', 'motores', False), ('a bomba de porão parou, quantas pessoas a bordo?', 'porao', False), ('o barco está inclinando, quais alarmes ativos?', 'fallback', True),
    ('a âncora garrou, quando chegamos?', 'ancora', False), ('o rádio não funciona, qual o ETA?', 'canal16', False), ('o COG está errado', 'fallback', True), ('o barco está desviando do rumo', 'fallback', True),
    ('estamos fora do rumo', 'fallback', True),
    # sobreDados: «falso» com alarme, alerta, sensor ou GPS é o falso alarme; «alarme de <coisa>» é o equipamento
    ('esse alarme é falso?', 'fallback', True), ('o alerta é falso?', 'fallback', True), ('isso é um alarme falso?', 'fallback', True), ('o sensor de profundidade é falso?', 'fallback', True),
    ('o alarme é falso?', 'fallback', True), ('o alarme de temperatura é real?', 'base', True), ('os dados são falsos?', 'sobreDados', False),
    # fora do barco: «quem venceu/ganhou» não é a agenda de manutenção
    ('quem venceu o jogo ontem?', 'foraBarco', False), ('quem venceu o campeonato?', 'foraBarco', False), ('quem venceu?', 'foraBarco', False), ('quem venceu a eleição?', 'foraBarco', False),
    ('quem ganhou o campeonato?', 'foraBarco', False), ('quem ganhou a copa?', 'foraBarco', False), ('quem ganhou?', 'foraBarco', False), ('quem venceu a regata?', 'foraBarco', False), ('o filtro venceu?', 'manutencao', False),
    # pedido de socorro que a lista SOS não pega: a rota sos (local, sem IA); a rotina ao lado segue como antes
    ('isso é real, preciso de ajuda', 'sos', False), ('isso não é um teste, é real', 'sos', False), ('quero saber se isso é real: estamos em risco', 'sos', False), ('estamos em risco', 'sos', False),
    ('estamos em risco, qual a posição?', 'sos', False), ('preciso de ajuda, qual o ETA?', 'sos', False), ('preciso de ajuda, quantas pessoas a bordo?', 'sos', False), ('preciso de ajuda, qual a posição?', 'sos', False),
    ('isso não é um teste', 'sos', False), ('é sério, preciso de ajuda', 'sos', False), ('o barco está em risco', 'sos', False), ('corremos risco', 'sos', False), ('não é um teste, onde estamos?', 'sos', False),
    ('preciso de ajuda para trocar o óleo', 'saudacao', True), ('preciso de ajuda com o diário', 'diarioLer', False), ('os dados são reais? preciso de ajuda', 'saudacao', True),
    ('estamos em risco de chuva?', 'clima', False), ('o filtro está em risco de entupir?', 'fallback', True),
]
CASOS = CASOS + [(q, k) for q, k, _ in ROTAS_P3C_REV3]
PEDE_IA.update({q: ia for q, k, ia in ROTAS_P3C_REV3})

# Revisão 4 da P3C. (1) «preço» é palavra inteira: «preconizado» e «precoce» são de bordo, não de dinheiro. (2) A frase de apresentação só responde à pergunta sobre os dados e mais nada (lista branca): o «preciso», o «é sério» e o
# «é urgente» dentro da pergunta continuam sendo ela; o relato de falha ou de perigo junto dela segue a rota dele. (3) «Correr risco» em toda flexão e o pedido de ajuda no plural ou sem complemento são socorro (rota sos).
# (4) O AIS só responde a pergunta neutra do status; «o AIS parou» segue o guia ou a IA. (5) A chegada responde a «quando chegamos?», «já chegamos?», «em quanto tempo chegamos?»; «quanto tempo falta?» sozinho segue não sendo a
# chegada. (6) A profundidade responde «quanto de fundo tem?», «qual o fundo?», «sonda»; a válvula de fundo não. (7) A 1ª linha de «quanto falta para a troca de óleo?» diz o quanto falta; a de «o vento a bordo agora» é o vento do quadro.
SOBRE_DADOS_SIM_REV4 = [
    'preciso saber se isso é real', 'eu preciso saber se os dados são reais', 'precisamos saber se o barco é de verdade', 'preciso confirmar: esses dados são simulados?', 'é sério, isso é real?',
    'é sério que isso é uma simulação?', 'isso é real? é urgente', 'urgente: os dados são reais?', 'os dados são simulados? preciso para o relatório', 'esses dados são reais? preciso decidir se saio',
    'quero saber se os dados são reais', 'queria saber se isso é real', 'gostaria de saber se o barco é de verdade', 'isso é um ambiente de demonstração?', 'isso não é real, né?', 'estes dados são verdadeiros?']
ROTAS_P3C_REV4 = [(q, 'sobreDados', False) for q in SOBRE_DADOS_SIM_REV4] + [
    # «preço» com fronteira de palavra: o intervalo preconizado e o desgaste precoce são de bordo (guia ou IA), não de dinheiro
    ('qual o intervalo de troca preconizado pelo fabricante?', 'fallback', True), ('desgaste precoce do rotor', 'fallback', True), ('o desgaste precoce do impeller', 'fallback', True),
    ('falha precoce do alternador', 'fallback', True), ('qual a pressão preconizada dos pneus do bote?', 'fallback', True), ('corrosão precoce no casco', 'fallback', True),
    ('o filtro está com desgaste precoce', 'fallback', True), ('como evitar falha precoce da hélice', 'fallback', True), ('o que fazer com desgaste precoce das buchas', 'fallback', True),
    ('quais os preços?', 'foraBarco', False), ('qual o preço do dólar?', 'foraBarco', False), ('preço do bitcoin', 'foraBarco', False), ('qual o preço do diesel hoje?', 'autonomia', False),
    # a sobreDados não responde a relato de falha ou de perigo (lista branca): a rota do assunto, o guia ou a IA
    ('o motor parou, os dados são reais?', 'motores', False), ('tem muita água no barco, isso é real?', 'fallback', True), ('o bote virou, isso é real?', 'fallback', True),
    ('estamos perdidos, isso é real?', 'fallback', True), ('vamos morrer, isso é real?', 'fallback', True), ('pelo amor de Deus, isso é real?', 'fallback', True),
    ('a situação é grave, os dados são reais?', 'fallback', True), ('tem um problema grave a bordo, isso é real?', 'fallback', True), ('a água está subindo, isso é real?', 'base', False),
    ('o alarme não para, isso é real?', 'fallback', True), ('não tem mais diesel, os dados são reais?', 'autonomia', False),
    # socorro: correr risco em toda flexão (com o «de <perigo de bordo>»), o pedido de ajuda no plural ou sem complemento; a rotina e o menu ficam como antes
    ('estamos correndo risco', 'sos', False), ('o barco corre risco', 'sos', False), ('a lancha corre risco de vida', 'sos', False), ('estamos correndo risco de afundar', 'sos', False),
    ('o barco corre risco de encalhar', 'sos', False), ('corremos risco de morrer', 'sos', False), ('corremos risco de alagar', 'sos', False), ('o barco corre risco de virar', 'sos', False),
    ('estamos correndo risco de chuva', 'clima', False), ('o filtro corre risco de entupir', 'fallback', True),
    ('me ajudem', 'sos', False), ('ajudem', 'sos', False), ('alguém me ajuda', 'sos', False), ('alguém me ajude', 'sos', False), ('pelo amor de Deus, ajuda', 'sos', False),
    ('ajuda', 'saudacao', True), ('alguém me ajuda a trocar o óleo', 'saudacao', True), ('pelo amor de Deus, qual a temperatura do motor?', 'base', True),
    # AIS: só a pergunta neutra do status; o relato de falha segue o guia ou a IA, nunca a contagem de alvos
    ('qual o transponder do AIS?', 'base', True), ('o AIS não funciona', 'fallback', True), ('o AIS parou', 'fallback', True), ('o AIS está desligado', 'fallback', True), ('o AIS apagou', 'fallback', True), ('o AIS está com falha', 'fallback', True),
    ('sem sinal do AIS', 'fallback', True), ('o AIS não está recebendo nada', 'fallback', True), ('o AIS está ligado?', 'ais', False), ('qual a situação do AIS?', 'ais', False), ('o AIS está funcionando?', 'ais', False),
    # a chegada em todo jeito natural de perguntar (e o que continua fora dela)
    ('quando chegamos?', 'eta', False), ('quando vamos chegar?', 'eta', False), ('quando a gente chega?', 'eta', False), ('vamos chegar a que horas?', 'eta', False), ('em quanto tempo chegamos?', 'eta', False),
    ('falta muito para chegar?', 'eta', False), ('já chegamos?', 'eta', False), ('estamos chegando?', 'eta', False), ('quanto falta pra base?', 'eta', False), ('quanto falta pra marina?', 'eta', False),
    ('quando chegamos na Barra Sul?', 'eta', False), ('quantas milhas já navegamos?', 'eta', False),
    ('quanto tempo falta?', 'fallback', True), ('falta muito?', 'base', True), ('quanto falta para a base de dados?', 'fallback', True),
    ('em que rumo estamos?', 'posicao', False), ('tem onda?', 'ondas', False), ('como estamos indo?', 'navegacao', False),
    # a profundidade no jeito de bordo (e a válvula de fundo, o fundo do casco e o relato da sonda, que não são ela)
    ('quanto de fundo tem aqui?', 'profundidade', False), ('quanto de fundo tem?', 'profundidade', False), ('qual o fundo?', 'profundidade', False), ('fundo', 'profundidade', False), ('sonda', 'profundidade', False),
    ('tem pouco fundo?', 'profundidade', False), ('tem muito fundo aqui?', 'profundidade', False), ('feche a válvula de fundo', 'base', True), ('fundo do casco', 'fallback', True),
    ('a sonda marca 2 metros', 'base', True),
    # as horas que faltam (a troca de óleo dos motores); o filtro de água salgada, a revisão anual e o rotor do gerador são de outra tarefa
    ('quanto falta para trocar o filtro?', 'horimetros', False), ('quanto falta para a troca do óleo do motor?', 'horimetros', False), ('falta muito para a troca de óleo?', 'horimetros', False),
    ('quanto falta para trocar o filtro de água salgada?', 'base', True), ('quanto falta para a revisão anual dos motores?', 'motores', False), ('quanto falta para o rotor do gerador?', 'base', True),
    # o vento a bordo (e o relato do vento forte, que segue a previsão primeiro)
    ('qual o vento a bordo agora?', 'clima', False), ('qual o vento aparente?', 'clima', False), ('o vento está forte agora', 'clima', False), ('qual o vento hoje?', 'clima', False),
]
CASOS = CASOS + [(q, k) for q, k, _ in ROTAS_P3C_REV4]
PEDE_IA.update({q: ia for q, k, ia in ROTAS_P3C_REV4})

# O relato com número ou estado NÃO é a pergunta da leitura: nenhuma destas perguntas pode voltar «dentro da faixa normal», «Profundidade de 10,8 m», «Ondas de 0,8 m» nem a água do mar a 20 °C
# (trava 10: relato de falha sem leitura calma). Vão ao guia, ao fallback, à IA ou à rota do assunto (não importa qual; importa que não seja a leitura).
RELATOS_P3C = [
    'a temperatura do motor está em 110', 'temperatura do motor 110 graus', 'temperatura do motor chegou a 105 °C', 'temperatura do motor BB 112', 'a temperatura do motor está no vermelho',
    'o ponteiro da temperatura do motor está no vermelho', 'a temperatura do motor está estourando', 'temperatura do motor passou de 100', 'temperatura do motor crítica', 'temperatura do motor perigosa',
    'temperatura do motor preocupante', 'temperatura do motor elevada', 'o arrefecimento parou', 'arrefecimento falhou', 'arrefecimento sem água', 'perdi o arrefecimento', 'sem arrefecimento', 'arrefecimento apitando',
    'a sonda marca 2 metros de profundidade', 'a profundidade está em 1,5 metros', 'profundidade 1 metro', 'profundidade caindo', 'a profundidade está diminuindo', 'a profundidade está caindo rápido', 'profundidade zero',
    'as ondas estão com 4 metros', 'ondas de 3 metros batendo forte', 'as ondas estão batendo forte', 'o mar está muito agitado', 'a água do mar está a 12 graus', 'a temperatura da água está em 30 graus', 'temperatura do mar 35 graus']
LEITURAS_P3C = ('arrefecimento', 'profundidade', 'ondas', 'temperaturaAgua')
NAO_ETA = ['quanto falta?', 'quanto falta', 'quanto tempo falta?', 'quantas milhas?', 'o que falta?']
# A pergunta mista com o equipamento de segurança: (cabeça, chave dela sozinha) × a cauda de dado, nas duas ordens, tem de dar a chave da cabeça
MISTAS_CABECAS = [('acionar o EPIRB', 'epirb'), ('onde fica o EPIRB', 'epirb'), ('disparar o Seafire', 'seafire'), ('sistema de supressão', 'seafire'), ('o sistema fixo disparou', 'seafire'), ('canal 16', 'canal16'),
                  ('pan-pan', 'canal16'), ('fazer um pan pan', 'canal16'), ('teste do DSC', 'canal16'), ('botão DISTRESS do DSC', 'canal16')]
MISTAS_CAUDAS = ['quantas pessoas a bordo?', 'qual o ETA?', 'quanto falta para chegar?', 'qual a profundidade?', 'quais alarmes ativos?', 'como está o estado do mar?', 'qual a temperatura da água?', 'qual a temperatura do motor?',
                 'como está a navegação?', 'qual o calado do barco?', 'situação agora', 'qual o comprimento do barco?', 'o que é o AIS?', 'os dados são reais?', 'qual o MMSI?',
                 # (P3E, revisão) o checklist (que traz a velocidade do quadro), a lista de tendências e o estoque de peças também não tomam a pergunta do equipamento de segurança
                 'checklist de fundeio', 'checklist de saída', 'quais as tendências?', 'tem peça sobressalente?',
                 # (P3E, revisão 4) o checklist de abastecimento e o de chegada, e o diesel (a rota da autonomia os tomava, com «a 18 nós»)
                 'checklist de abastecimento', 'checklist de chegada', 'quanto diesel temos?']


def main():
    falhas = 0
    with sync_playwright() as p:
        b = p.chromium.launch(channel=CANAL, headless=True)
        pg = b.new_page()
        erros = []
        pg.on('pageerror', lambda e: erros.append(str(e)))
        pg.goto(BASE + 'base-conhecimento.json')  # mesma origem, sem a porta de login
        # Fase 3 (PROMPT Fase 3 «Instante», Fase 7 «Mudanças nos testes»): a página é a da Main e da H2 (dados, replay, telemetria, cérebro) com o
        # instante congelado em 12:01:00 (fixar('60')): os números são os mesmos em toda a execução. O replay anda com a flag lida a cada chamada.
        for arq in ('capitao-dados.js', 'capitao-replay.js', 'capitao-alertas.js', 'capitao-telemetria.js'):   # a ordem do <head> da Main e da H2
            pg.add_script_tag(url=BASE + arq)
        pg.evaluate("() => window.CapitaoReplay.fixar('60')")
        pg.add_script_tag(url=BASE + 'capitao-brain.js')
        pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); })")
        res = pg.evaluate("""(casos) => { const B = window.CapitaoBrain; localStorage.clear();
          return casos.map(([q, k]) => { const a = B.answer(q, { platform: 'app' }); return { q, esperado: k, key: a.key, src: a.src, text: a.text, curta: B.falaCurta(a), ia: B.pedeIA(a, q) }; }); }""", CASOS)
        diario = pg.evaluate("() => window.CapitaoBrain.loadDiario().length")
        for r in res:
            ok = r['key'] == r['esperado']
            fonte = bool(r['src']) and r['src'].startswith('Fonte')
            # Fase 3 (P3B), PROMPT Fase 7 linha 3 (`:71`): invertida. O fallback não diz SEM DADOS nem «Não encontrei esse dado» (decisão 3 e 5); a pergunta de bordo nunca cai nele
            semdados = r['key'] != 'fallback' or ('SEM DADOS' not in r['text'] and 'Não encontrei esse dado' not in r['text'])
            ia = r['q'] not in PEDE_IA or r['ia'] == PEDE_IA[r['q']]
            # trava §2.3 (revisão da 1b): caso que espera chave de emergência fica no aparelho, esteja ou não no PEDE_IA
            ia = ia and (r['esperado'] not in CHAVES_LOCAIS or r['ia'] is False)
            if not (ok and fonte and semdados and ia):
                falhas += 1
                print('FALHA', json.dumps({k: r[k] for k in ('q', 'esperado', 'key', 'ia', 'src')}, ensure_ascii=False))
        print('%d perguntas · %d falhas · linhas gravadas no diário: %d (esperado: 1, só o comando explícito)' % (len(res), falhas, diario))
        if diario != 1:
            falhas += 1
        # Ficha de bordo que vai para a IA: todos os blocos, sem o rótulo DEMO, sem coordenadas e cabendo no proxy.
        f = pg.evaluate("() => window.CapitaoBrain.ficha('app')")
        fmax = pg.evaluate("() => window.CapitaoBrain.FICHA_MAX")
        # Fase 3 (P3D), PROMPT Fase 7 linha 3 (`:81-82`): «## Navegação agora» logo depois de «## Agora» e «## Emergência» perto do topo (o corte do cliente é pelo fim);
        # a lista está na ORDEM da ficha, e a ordem é conferida abaixo
        blocos = ['## Agora', '## Navegação agora', '## Emergência', '## Sobre o app', '## Embarcação', '## Equipamentos', '## Telemetria', '## Manutenção', '## Peças', '## Horímetros', '## Autonomia e consumo',
                  '## Documentos', '## Pendências', '## Diário de bordo', '## Equipe e contatos', '## Clima e maré', '## Guias de bordo']
        faltam = [x for x in blocos if x not in f]
        titulos_f = re.findall(r'^## (.*)$', f, re.M)
        ordem_f = [t for t in titulos_f if '## ' + t in blocos]
        coord = [m.group(0) for m in [confere.R_COORD.search(f)] if m]   # Fase 3 (P3B), PROMPT Fase 7 linha 3 (`:84`): a regex do §2.8 (graus-minutos e decimal), não a lista literal do snapshot
        voz = pg.evaluate("() => window.CapitaoBrain.falaCurta({ key: 'ia', text: 'Sou o Capitão IA.\\nRespondo sobre telemetria, manutenção e documentos, sempre com a fonte.\\n• item\\nFonte: Sobre o app' })")
        x = pg.evaluate("""() => { const B = window.CapitaoBrain, r = (q) => { const a = B.answer(q, { platform: 'app', commit: false }); return { a, f: B.ficha('app', q, a), voz: B.falaCurta(a) }; };
            const meta = r('Oque você faz?'), base = r('Quando foi a última troca de óleo do motor?'), sd = r('como se faz um nó lais de guia?'), oi = r('oi'), dg = r('diagnóstico');   // Fase 3 (P3C), PROMPT Fase 7 «Mudanças nos testes»: o «calado» passa a ter dado (rota embarcacao); o gatilho vira uma pergunta de náutica geral sem rota
            const func = r('como você funciona?'), seguro = r('o que você sabe sobre o seguro?');
            return { metaF: meta.f, baseK: base.a.key, baseF: base.f, sdF: sd.f, sdK: sd.a.key, funcF: func.f, seguroK: seguro.a.key, seguroF: seguro.f, metaVoz: meta.voz, oiVoz: oi.voz,
                     dgTexto: dg.a.text, dgSrc: dg.a.src, dgVoz: dg.voz, dgHref: (dg.a.actions[0] || {}).href, versao: B.VERSAO }; }""")
        guias = pg.evaluate("() => window.CapitaoDados.guias || {}")
        # "Seakeeper Seakeeper 3": fabricante seguido do modelo que já começa por ele (revisão do C5; o fabMod tira, como o equip_de)
        rep = pg.evaluate("""() => (window.CapitaoDados.equipamentos || []).filter((e) => e.fabricante && e.modelo
            && e.modelo.toLowerCase().indexOf(e.fabricante.toLowerCase()) === 0).map((e) => e.fabricante + ' ' + e.modelo)""")
        repetidos = [(r['q'], x) for r in res for x in rep if x.lower() in (r['text'] + '\n' + r['curta']).lower()]
        topo = pg.evaluate("""() => { const B = window.CapitaoBrain, h = (q) => (B.buscaBase(q, 1)[0] || {}).d || {};
            const a = h('como ligar o gerador?'), b = h('Quando foi a última troca de óleo do motor?'), c = h('troca do rotor do gerador');
            return [[a.fonte, a.secao], [b.fonte, b.secao], c.fonte]; }""")
        # Revisão 2 do C5: as perguntas dos cartões do guincho, do radar e do piloto (F1) trazem o guia do próprio equipamento ao topo;
        # depois do disparo do sistema fixo, o trecho do topo tem o "não abra o acesso ao motor" (qualquer seção do g_seafire, menos a
        # inspeção); o guincho não mostra a posição; a resposta "guias de bordo" lista todos os guias, sem SEM DADOS.
        # Revisão 3 do C5: o topo depois do disparo também manda desligar motores, gerador e ventilação (o 1º passo do agente limpo);
        # a pergunta genérica sobre os equipamentos não traz o g_epirb nem o protocolo ao topo; a temperatura alta dos motores (o
        # AVISO de arrefecimento do laço) manda desligar o motor afetado antes de mexer no filtro e no rotor.
        rev2 = pg.evaluate("""() => { const B = window.CapitaoBrain, D = window.CapitaoDados, h = (q) => (B.buscaBase(q, 1)[0] || {}).d || {};
            const cartoes = [['como lançar com o guincho Lewmar', 'g_ancora'], ['como ligar o radar Garmin', 'g_radar'],
              ['como engatar o piloto automático Raymarine', 'g_piloto']].filter(([q, g]) => h(q).fonte !== D.guias[g]).map(([q]) => q);
            const disparo = ['o que fazer depois do disparo do sistema fixo', 'o sistema fixo disparou', 'o sistema fixo disparou sozinho',
              'o sistema fixo descarregou', 'o sistema descarregou', 'alarme do sistema fixo'].filter((q) => { const t = (h(q).texto || '').toLowerCase();
                return t.indexOf('não abra o acesso ao motor') === -1 || !/desligue motores|motores, gerador e ventilação/.test(t); });
            const generica = ['quais equipamentos tem a bordo?', 'equipamentos do barco', 'modelo dos equipamentos', 'que equipamentos o barco tem?',
              'qual o modelo do equipamento?'].filter((q) => [D.guias.g_epirb, D.guias.protocolo].indexOf(h(q).fonte) !== -1);
            const temp = ['temperatura alta no motor BE', 'sem água no escapamento motores Cummins — como resolver?'].filter((q) => { const x = h(q), t = x.texto || '';
              return x.fonte !== D.guias.g_motores || !(t.indexOf('desligue o motor afetado') !== -1 && t.indexOf('desligue o motor afetado') < t.indexOf('filtro de água salgada')); });
            const g = B.answer('como lançar com o guincho Lewmar', { platform: 'app', commit: false }), m = B.answer('Quais guias de bordo estão carregados?', { platform: 'app', commit: false });
            const faltam = Object.keys(D.guias).filter((k) => m.text.indexOf(D.guias[k].replace(/^Guia de bordo — /, '')) === -1);
            return { cartoes, disparo, generica, temp, guincho: g.text, manualK: m.key, manualSD: /SEM DADOS|não informad/.test(m.text), faltam }; }""")
        # Revisão 4 do C5: (a) pergunta comum nunca traz trecho de segurança ao topo nem à resposta (g_seafire, protocolo, g_motores §4…);
        # (b) a troca de óleo vai para a agenda (§7) e o esfriar do motor, para a parada (§6); (c) o trecho de segurança sai inteiro na
        # tela e na voz, com o rótulo do procedimento padrão (e a nota da etiqueta, no Seafire e no EPIRB) no fim: o corte de 480 letras
        # tirava os dois do §1 do Seafire (560 letras) e a nota do §3 (492), e a voz parava na 2ª frase; (d) "botão distress" continua
        # local (o "distress" é o DSC do título).
        rev4 = pg.evaluate("""([rot, nota]) => { const B = window.CapitaoBrain, D = window.CapitaoDados, h = (q) => (B.buscaBase(q, 1)[0] || {}).d || {};
            const resp = (q) => B.answer(q, { platform: 'app', commit: false });
            const comuns = ['como religar o gerador depois de desligar', 'como religar o motor depois de desligar', 'como religar os motores depois de desligar',
              'como abrir o motor', 'como abrir o gerador', 'como abrir a ventilação', 'como desligar a ventilação', 'como ligar a ventilação depois de desligar',
              'como religar a ventilação depois de desligar', 'quando trocar o óleo do motor?', 'como esfriar o motor depois de navegar',
              'como esfriar o motor depois de navegar rápido', 'como esfriar o motor', 'posso abrir o acesso ao motor para conferir o óleo',
              'como abrir o acesso ao motor', 'devo abrir o motor depois de navegar', 'o alarme disparou', 'como desligar o sistema',
              'corte a ventilação', 'espere o tempo da etiqueta', 'como abrir o compartimento do motor'].filter((q) => resp(q).seguranca || h(q).seguranca);
            const oleo = ['quando trocar o óleo do motor?', 'qual o intervalo de troca de óleo do motor?', 'Quando foi a última troca de óleo do motor?']
              .filter((q) => { const x = h(q); return x.fonte !== D.guias.g_motores || x.secao !== '7 · Manutenção na agenda'; });
            const esfriar = ['como esfriar o motor', 'como esfriar o motor depois de navegar', 'como esfriar o motor depois de navegar rápido']
              .filter((q) => { const x = h(q); return x.fonte !== D.guias.g_motores || x.secao !== '6 · Parada'; });
            const dsc = ['botão distress', 'como usar o botão distress', 'distress'].filter((q) => !resp(q).seguranca);
            // (1b: as perguntas do sistema fixo passaram à rota `seafire`, conferida inteira na verificação «1b: seafire» abaixo; ficam as que
            // seguem no trecho de segurança da base)
            const inteira = ['teste da baliza', 'botão distress', 'como testar a baliza?'].map((q) => { const a = resp(q), x = h(q), t = (x.texto || '').replace(/\\s+/g, ' ').trim();
                const comNota = [D.guias.g_seafire, D.guias.g_epirb].indexOf(x.fonte) !== -1, fim = comNota ? rot + ' ' + nota : rot;
                return { q, seg: !!a.seguranca, tela: a.text.split('\\n')[0] === t, voz: B.falaCurta(a) === t, fim: t.slice(-fim.length) === fim, letras: t.length }; })
              .filter((r) => !(r.seg && r.tela && r.voz && r.fim));
            // depois do disparo, a voz também diz "não abra o acesso ao motor" e manda desligar motores, gerador e ventilação
            const falaDisparo = ['o sistema fixo disparou', 'o sistema fixo descarregou', 'o sistema descarregou', 'o que fazer depois do disparo do sistema fixo', 'alarme do sistema fixo']
              .filter((q) => { const f = B.falaCurta(resp(q)).toLowerCase(); return f.indexOf('não abra o acesso ao motor') === -1 || !/desligue motores|motores, gerador e ventilação/.test(f); });
            return { comuns, oleo, esfriar, dsc, inteira, falaDisparo }; }""", ['Procedimento padrão — confirmar com o protocolo de bordo.', 'Modelo, validade e acionamento: veja a etiqueta do equipamento.'])
        # Revisão 5 do C5: (a) o topo da busca de "como ligar o ar" é a Climatização §1 · Ligar (o "ar" entra na busca; "ar condicionado" não
        # puxa o §4 "Fluxo de ar fraco"); (b) a pergunta de homem ao mar e de PAN-PAN traz o trecho do protocolo, com seguranca, na tela;
        # (c) a resposta pronta que o trecho de OUTRO equipamento tomaria fica, e a que o trecho do próprio guia responde bem cede a ele
        # (o piloto no g_eletronicos §2, o alarme de âncora no §3).
        rev5 = pg.evaluate("""() => { const B = window.CapitaoBrain, D = window.CapitaoDados, h = (q) => (B.buscaBase(q, 1)[0] || {}).d || {};
            const resp = (q) => B.answer(q, { platform: 'app', commit: false });
            const clima = ['como ligar o ar', 'como ligar o ar condicionado', 'como desligar o ar'].map((q) => [q, h(q).fonte === D.guias.g_clima, h(q).secao])
              .filter(([q, ok]) => !ok).map(([q, ok, sec]) => q + ' → ' + sec);
            const climaSec = [h('como ligar o ar').secao, h('como desligar o ar').secao];
            // (1b, quarta revisão: «a pessoa que caiu» e «quem caiu» passaram a `sos`; o buscaBase segue nomeando o trecho do protocolo, que é o que esta verificação protege, e a resposta é local)
            const protocolo = (qs, sec, chaves) => qs.filter((q) => { const a = resp(q), x = h(q); return !(((a.key === 'base' && a.seguranca) || (chaves || []).indexOf(a.key) !== -1) && x.fonte === D.guias.protocolo && x.secao === sec); });
            // (1b: «pessoa caiu da lancha» saiu desta lista: «caiu da lancha» é da lista SOS e a chave passou a `sos`, ver as verificações «1b» abaixo)
            const mob = protocolo(['não vejo a pessoa que caiu', 'perdemos de vista quem caiu', 'perdi a pessoa de vista', 'a pessoa que caiu sumiu'], 'Homem ao mar', ['sos']);
            const pan = protocolo(['sem governo', 'barco sem governo', 'pane no barco'], 'PAN-PAN');
            const guia = ['como funciona o piloto automático', 'alarme de âncora'].map((q) => h(q).fonte === D.guias.g_eletronicos);
            // o trecho mostrado é do guia do equipamento perguntado (a.ref começa pela fonte), não o do topo da busca, que era de outro
            const certo = [['alarme de temperatura do motor', 'g_motores'], ['seakeeper temperatura alta', 'g_seakeeper'], ['trocar o filtro do ar condicionado', 'g_clima'],
              ['como ligar o carregador', 'g_eletrico'], ['como ligar o carregador de bateria', 'g_eletrico']]
              .filter(([q, g]) => { const a = resp(q); return a.key !== 'base' || String(a.ref).indexOf(D.guias[g]) !== 0; }).map(([q]) => q);
            return { clima, climaSec, mob, pan, guia, certo }; }""")
        # Revisão 6 do C5: a seção MOSTRADA (a.ref = fonte · §seção; o topo do buscaBase pode ser de outro guia, que o trechoServe pula) de
        # cada pergunta que a revisão 5 do C5 perdia ou deixava sem trava: a bomba que não é de porão no guia do equipamento; a bateria de
        # partida nos bancos; depois do disparo do sistema fixo, o §3 do Seafire (com seguranca: sem ele, o gerador/motores respondiam
        # com a resposta pronta); o alarme de âncora e o "como fundear" no plotter (g_eletronicos §3), não no contador de corrente nem no
        # recolher do guincho; "ar condicionado" na Climatização §1 e §3 (o "ar" solto puxava o §4 "Fluxo de ar fraco"); pessoa ao mar no protocolo.
        rev6 = pg.evaluate("""() => { const B = window.CapitaoBrain, D = window.CapitaoDados, h = (q) => (B.buscaBase(q, 1)[0] || {}).d || {};
            const resp = (q) => B.answer(q, { platform: 'app', commit: false });
            const onde = (qs, g, sec, seg) => qs.filter((q) => { const a = resp(q); return !(a.key === 'base' && a.ref === D.guias[g] + ' · §' + sec && !!a.seguranca === !!seg); })
              .map((q) => q + ' → ' + resp(q).key + ' ' + resp(q).ref);
            return {
              rotor: onde(['como trocar o rotor da bomba de água salgada', 'quando trocar o rotor da bomba de água salgada', 'como trocar o impeller da bomba de água salgada',
                'rotor da bomba', 'como inspecionar o rotor da bomba'], 'g_motores', '7 · Manutenção na agenda'),
              alarme: onde(['alarme da bomba de água salgada'], 'g_clima', '3 · Alarme de fluxo'),
              ligar: onde(['como ligar a bomba de água salgada', 'como ligar a bomba da climatização'], 'g_clima', '1 · Ligar'),
              desligar: onde(['como desligar a bomba de água salgada', 'como desligar a bomba da climatização'], 'g_clima', '5 · Desligar'),
              gerador: onde(['como trocar o rotor da bomba do gerador'], 'g_gerador', '7 · Manutenção na agenda'),
              bancos: onde(['como trocar a bateria de partida', 'como verificar a bateria de partida'], 'g_eletrico', '1 · Bancos'),
              // 1b: depois do disparo do sistema fixo a chave é `seafire` (os passos de protocolos.seafire: desligar motores, gerador e ventilação, e
              // «não abra o acesso ao motor»), não mais o trecho §3 da base; o trecho do topo da busca (rev2) continua sendo o §3 do g_seafire
              disparo: ['como religar o gerador depois que o sistema fixo disparou', 'como ligar o gerador depois do disparo do sistema fixo',
                'o sistema fixo disparou, como religo o gerador?', 'como abrir o motor depois que o sistema fixo disparou']
                .filter((q) => { const a = resp(q); return !(a.key === 'seafire' && a.text.indexOf('Não abra o acesso ao motor') !== -1 && !a.seguranca); }).map((q) => q + ' → ' + resp(q).key),
              ancora: onde(['alarme de âncora', 'como fundear'], 'g_eletronicos', '3 · Alarme de âncora'),
              arLigar: onde(['como ligar o ar condicionado'], 'g_clima', '1 · Ligar'),
              arFiltro: onde(['trocar o filtro do ar condicionado'], 'g_clima', '3 · Alarme de fluxo'),
              // 1b, quarta revisão: «pessoa ao mar» é `sos` (local, com os passos do MOB); o buscaBase segue nomeando o trecho do protocolo, que é o que esta verificação protege
              mar: ['pessoa ao mar', 'pessoa ao mar, o que faço'].filter((q) => { const a = resp(q), x = h(q); return !((a.key === 'sos' || (a.key === 'base' && a.seguranca)) && x.fonte === D.guias.protocolo && x.secao === 'Homem ao mar' && x.seguranca); })
                .map((q) => q + ' → ' + resp(q).key + ' ' + h(q).secao) }; }""")
        # Revisão 7 do C5: (a) pergunta que só diz o nome do equipamento (plotter, radar, Garmin, Icom, Fusion, som, áudio, motor) nunca traz
        # trecho de segurança ao topo nem à resposta, e o que vai ao guia ou à IA não é barrado por `seguranca`; (b) num guia misto o título
        # do trecho de segurança ainda o nomeia (a pressão de óleo baixa, a água entrando, o DSC, a identificação do AIS, o "antes de largar");
        # (c) a seção MOSTRADA das perguntas de bomba que a revisão 6 deixava sem teste (dessalinizador, porão, estabilizador).
        rev7 = pg.evaluate("""() => { const B = window.CapitaoBrain, D = window.CapitaoDados, h = (q) => (B.buscaBase(q, 1)[0] || {}).d || {};
            const resp = (q) => B.answer(q, { platform: 'app', commit: false });
            const nome = ['onde fica o plotter', 'como ver o radar', 'como ver o garmin', 'como ver o icom', 'como ver o fusion', 'como ver o som', 'como ver o áudio',
              'onde fica o motor', 'como ver os navios no radar', 'como ver os barcos no radar', 'como ver a água no radar', 'como ver o radar no plotter',
              'como ver a posição no plotter', 'como ver o motor no garmin', 'como ver o gerador no garmin',
              'onde fica o ar condicionado', 'onde fica o ar-condicionado', 'onde fica o som']
              .filter((q) => { const a = resp(q); return a.seguranca || h(q).seguranca || ((a.key === 'base' || a.key === 'fallback') && !B.pedeIA(a, q)); });
            // palavra genérica da identidade (IDENT_GENERICAS: caso, depois, antes, padrão, protocolo, confirmar…) sozinha não nomeia o trecho de segurança
            const generica = ['e depois', 'o que fazer depois', 'quanto tempo depois', 'antes', 'o que fazer antes', 'em caso de alarme', 'em caso de falha do motor',
              'o que fazer em caso de alarme', 'qual o procedimento padrão', 'qual o protocolo de bordo', 'confirmar com o protocolo de bordo', 'confirmar protocolo']
              .filter((q) => { const a = resp(q); return a.seguranca || h(q).seguranca || ((a.key === 'base' || a.key === 'fallback') && !B.pedeIA(a, q)); });
            // "bomba" com o nome de outra bomba (OUTRA_BOMBA) não é a resposta pronta do porão; a de esgoto e a "bomba" sozinha são
            const outra = ['como trocar o impeller da bomba', 'trocar o impelidor da bomba', 'a bomba de arrefecimento', 'a bomba de refrigeração', 'a bomba de resfriamento',
              'a bomba de circulação', 'a bomba do ar condicionado', 'a bomba da climatização', 'a bomba de água salgada', 'o rotor da bomba', 'a bomba do onan',
              'a bomba do gerador', 'a bomba do motor', 'a bomba do giroscópio', 'a bomba do estabilizador', 'a bomba do seakeeper', 'a bomba do piloto automático',
              'a bomba hidráulica', 'a bomba do dessalinizador', 'a bomba de lavagem', 'a bomba de pressão', 'a bomba de pressurização', 'a bomba de óleo']
              .filter((q) => resp(q).key === 'porao');
            const bilge = ['a bomba de esgoto não para', 'bomba de esgoto', 'a bomba de esgoto está enchendo de água', 'a bomba não para', 'como desligar a bomba', 'bombas de porão']
              .filter((q) => resp(q).key !== 'porao' || B.pedeIA(resp(q), q));
            const titulo = [['pressão de óleo baixa no motor', 'g_motores', '4 · Pressão de óleo baixa'], ['rádio VHF dsc', 'g_eletronicos', '5 · Rádio VHF: DSC'],
              ['identificação do AIS', 'g_ais', '2 · Identificação'], ['água entrando no porão', 'g_porao', '4 · Água entrando'],
              ['o que fazer antes de largar', 'checklist', 'Saída · antes de largar']]
              .filter(([q, g, sec]) => !(h(q).fonte === D.guias[g] && h(q).secao === sec && h(q).seguranca)).map(([q]) => q);
            const onde = (qs, g, sec) => qs.filter((q) => { const a = resp(q); return !(a.key === 'base' && a.ref === D.guias[g] + ' · §' + sec && !a.seguranca); })
              .map((q) => q + ' → ' + resp(q).key + ' ' + resp(q).ref);
            return { nome, generica, outra, bilge, titulo, dessal: onde(['como ligar a bomba do dessalinizador'], 'g_dessalinizador', '1 · Ligar'),
              porao: onde(['como funciona a bomba de porão'], 'g_porao', '1 · Funcionamento'),
              estab: onde(['alarme da bomba do seakeeper'], 'g_seakeeper', '6 · Alarmes') }; }""")
        for nome, cond, extra in [
            ('revisão 7 do C5: pergunta que só diz o nome do equipamento (plotter, radar, Garmin, Icom, Fusion, som, áudio, motor) sem trecho de segurança no topo nem na resposta, e sem barrar a IA',
             not rev7['nome'], rev7['nome']),
            ('revisão 7 do C5: palavra genérica da identidade (caso, depois, antes, padrão, protocolo, confirmar) sozinha não abre trecho de segurança nem barra a IA',
             not rev7['generica'], rev7['generica']),
            ('revisão 7 do C5: "bomba" com o nome de outra bomba (rotor, impeller, arrefecimento, climatização, gerador, motor, giroscópio, estabilizador, piloto, dessalinizador, óleo…) não é a resposta pronta do porão',
             not rev7['outra'], rev7['outra']),
            ('revisão 7 do C5: "bomba de esgoto" e "a bomba não para" seguem a rota do porão, no aparelho, sem IA', not rev7['bilge'], rev7['bilge']),
            ('revisão 7 do C5: num guia misto o título ainda nomeia o trecho de segurança (pressão de óleo baixa, DSC, identificação do AIS, água entrando, antes de largar)',
             not rev7['titulo'], rev7['titulo']),
            ('revisão 7 do C5: "como ligar a bomba do dessalinizador", "como funciona a bomba de porão" e "alarme da bomba do seakeeper" mostram a seção do guia (§1 Ligar, §1 Funcionamento, §6 Alarmes)',
             not (rev7['dessal'] or rev7['porao'] or rev7['estab']), (rev7['dessal'], rev7['porao'], rev7['estab'])),
            ('revisão 6 do C5: a bomba de água salgada, o rotor e o impeller vão ao g_motores §7 e à Climatização (§3 alarme, §1 ligar, §5 desligar), e a do gerador ao g_gerador §7, não à resposta pronta do porão',
             not (rev6['rotor'] or rev6['alarme'] or rev6['ligar'] or rev6['desligar'] or rev6['gerador']),
             (rev6['rotor'], rev6['alarme'], rev6['ligar'], rev6['desligar'], rev6['gerador'])),
            ('revisão 6 do C5: "como trocar/verificar a bateria de partida" vai ao g_eletrico §1 · Bancos, não à resposta pronta dos motores', not rev6['bancos'], rev6['bancos']),
            ('revisão 6 do C5 (1b: rota seafire): depois do disparo do sistema fixo, religar o gerador ou abrir o motor traz os passos do Seafire ("não abra o acesso ao motor"), sem IA, não a resposta pronta',
             not rev6['disparo'], rev6['disparo']),
            ('revisão 6 do C5: "alarme de âncora" e "como fundear" mostram o g_eletronicos §3 (alarme no plotter), não o contador de corrente nem o recolher do guincho', not rev6['ancora'], rev6['ancora']),
            ('revisão 6 do C5: "como ligar o ar condicionado" é a Climatização §1 e "trocar o filtro do ar condicionado" o §3 (o "ar" solto puxava o §4 "Fluxo de ar fraco")',
             not (rev6['arLigar'] or rev6['arFiltro']), (rev6['arLigar'], rev6['arFiltro'])),
            ('revisão 6 do C5: "pessoa ao mar" nomeia o protocolo de homem ao mar na busca, com seguranca (o "mar" sozinho não nomeia, o identCom "pessoa" sim), e a resposta é local (sos)', not rev6['mar'], rev6['mar']),
            ('revisão 5 do C5: "como ligar o ar", "…o ar condicionado" e "…desligar o ar" têm a Climatização no topo (§1 Ligar e §5 Desligar)',
             not rev5['clima'] and rev5['climaSec'] == ['1 · Ligar', '5 · Desligar'], (rev5['clima'], rev5['climaSec'])),
            ('revisão 5 do C5: homem ao mar e PAN-PAN escritos com as palavras do trecho (caiu, vista, governo, pane) trazem o protocolo, com seguranca, e não vão à IA',
             not rev5['mob'] and not rev5['pan'], (rev5['mob'], rev5['pan'])),
            ('revisão 5 do C5: o piloto automático e o alarme de âncora continuam no g_eletronicos (§2 e §3), e não na resposta pronta', all(rev5['guia']), rev5['guia']),
            ('revisão 5 do C5: o trecho mostrado é do guia do equipamento perguntado (motores, Seakeeper, climatização, sistema elétrico), não o de outro equipamento que vinha antes na busca',
             not rev5['certo'], rev5['certo']),
            ('ficha resumida SÓ para pergunta pura sobre o app ("Oque você faz?", "como você funciona?"; sem telemetria, < 4 mil letras)', '## Ficha resumida' in x['metaF'] and '## Telemetria' not in x['metaF'] and len(x['metaF']) < 4000 and '## Ficha resumida' in x['funcF'], (len(x['metaF']), len(x['funcF']))),
            ('trecho do guia ("última troca de óleo do motor?") leva a ficha COMPLETA, com a agenda', x['baseK'] == 'base' and '## Manutenção' in x['baseF'] and '## Ficha resumida' not in x['baseF'], (x['baseK'], len(x['baseF']))),
            ('pergunta sobre o app COM assunto ("o que você sabe sobre o seguro?") leva a ficha COMPLETA, com os documentos', x['seguroK'] == 'saudacao' and '## Documentos' in x['seguroF'] and '## Ficha resumida' not in x['seguroF'], (x['seguroK'], len(x['seguroF']))),
            ('diagnóstico numa tela sem o cliente da IA: a voz diz onde a IA fica e o botão leva à tela inicial', x['dgVoz'].startswith('Nesta tela a IA na nuvem não é carregada') and x['dgHref'] == 'H2-Home-Mobile.dc.html#ia=ativar', (x['dgVoz'], x['dgHref'])),
            ('ficha completa para a pergunta sem resposta pronta (fallback, a IA responde)', x['sdK'] == 'fallback' and '## Telemetria' in x['sdF'] and '## Ficha resumida' not in x['sdF'], (x['sdK'], len(x['sdF']))),
            ('voz de "Oque você faz?" sem a IA diz o que o Capitão faz (não repete a abertura)', x['metaVoz'].startswith('Respondo sobre telemetria') and x['oiVoz'] == 'Capitão IA online. Que precisa?', (x['metaVoz'][:60], x['oiVoz'])),
            ('diagnóstico local: versões, internet, fonte "este aparelho"', 'Diagnóstico do Capitão IA neste aparelho' in x['dgTexto'] and 'cérebro ' + x['versao'] in x['dgTexto'] and x['dgSrc'].startswith('Fonte: este aparelho'), x['dgTexto'][:200]),
            ('ficha com todos os blocos', not faltam, faltam),
            ('ficha (P3D): «## Navegação agora» logo depois de «## Agora» e «## Emergência» perto do topo (3º bloco, nos primeiros 2.500 letras), os blocos na ordem do PROMPT',
             titulos_f[:3] == ['Agora', 'Navegação agora', 'Emergência'] and 0 <= f.find('## Emergência') < 2500 and ordem_f == [b[3:] for b in blocos], (titulos_f[:4], f.find('## Emergência'), ordem_f)),
            ('ficha sem coordenadas do barco', not coord, coord),
            # Decisão 1.1.0 (b), contrato C2: títulos e fontes sem "(DEMO)", então a ficha não leva mais o rótulo. A exigência de
            # SEM DADOS sai junto: volta invertida na Fase 3 (nenhum SEM DADOS na ficha com simulacao: true).
            # Fase 3 (P3B), PROMPT Fase 7 linha 3 (`:101`), invertida: «ficha com rótulo DEMO e SEM DADOS» virou ficha SEM DEMO, SEM DADOS, SEM LEITURA, MANUAL NO DRIVE, fictício nem simulado
            ('ficha sem o rótulo DEMO', 'DEMO' not in f, [l for l in f.split('\n') if 'DEMO' in l][:3]),
            ('ficha sem DEMO, SEM DADOS, SEM LEITURA, MANUAL NO DRIVE, fictício nem simulado (nem as regex ROTULOS, AUTENTICIDADE, VAZIOS e VISIVEL do §3)',
             not [n for n in ('ROTULOS', 'AUTENTICIDADE', 'VAZIOS', 'VISIVEL') if RX[n].search(f)] and not re.search(r'SEM DADOS|SEM LEITURA|MANUAL NO DRIVE|fict[ií]ci|simulad', f),
             [(n, RX[n].search(f).group(0)) for n in ('ROTULOS', 'AUTENTICIDADE', 'VAZIOS', 'VISIVEL') if RX[n].search(f)] + re.findall(r'.{20}(?:SEM DADOS|SEM LEITURA|MANUAL NO DRIVE).{20}', f)[:4]),
            # Fase 3 (P3B), PROMPT Fase 7 linha 3 (`:102`): o teto de 10.000 sobe para o do proxy (12.000), porque o «Sobre o app» e a telemetria completos passaram de 10.000 (10.351).
            # P3D (revisão): esta página NÃO carrega o capitao-clima.js (a ficha mede 11,3 mil, com o «## Clima e maré» na frase curta «sem conexão»); no app de verdade, com a previsão e a maré,
            # ela passa de 11.500 e a decisão (i) manda 16.000. A regra do teto (16.000 acima de ~11.500) é cobrada no grupo ficha, que mede COM a previsão, a maré e o diário do aparelho;
            # aqui a ficha só tem de caber no teto exposto em B.FICHA_MAX, que nunca é menor que os 12.000 do cliente.
            ('ficha entre 3.000 e o teto da ficha (B.FICHA_MAX, de 12.000 a 16.000; a regra da decisão (i) está no grupo ficha, medida com a previsão e a maré)', 3000 <= len(f) <= fmax and fmax in (12000, 16000), (len(f), fmax)),
            ('voz da resposta da IA: 1ª frase curta + a seguinte, sem a fonte', voz == 'Sou o Capitão IA. Respondo sobre telemetria, manutenção e documentos, sempre com a fonte.', voz),
            # C5 (CONTRATO §1.5): com os 91 trechos, o g_gerador §2 · Ligar continua o 1º trecho de "como ligar o gerador?" (é a fonte
            # do FONTE_IA do chat_ia.py); a troca de óleo do motor sai da agenda dos motores e a do rotor, do gerador.
            ('C5: 1º trecho de "como ligar o gerador?" = g_gerador §2 · Ligar; óleo do motor no g_motores §7; rotor do gerador no g_gerador',
             topo == [[guias.get('g_gerador'), '2 · Ligar'], [guias.get('g_motores'), '7 · Manutenção na agenda'], guias.get('g_gerador')], topo),
            ('revisão do C5: nenhuma resposta (nem a fala) repete o fabricante antes do modelo que começa por ele ("Seakeeper Seakeeper 3")',
             bool(rep) and not repetidos, (rep, repetidos[:3])),
            ('revisão 2 do C5: guincho, radar e piloto da F1 no guia de cada um; depois do disparo, "não abra o acesso ao motor" no topo (e, desde a revisão 3, o desligamento de motores, gerador e ventilação)',
             not rev2['cartoes'] and not rev2['disparo'], (rev2['cartoes'], rev2['disparo'])),
            ('revisão 3 do C5: pergunta genérica sobre os equipamentos sem o g_epirb nem o protocolo no topo; temperatura alta dos motores desliga antes do filtro',
             not rev2['generica'] and not rev2['temp'], (rev2['generica'], rev2['temp'])),
            ('revisão 4 do C5: pergunta comum (religar o gerador, abrir o motor, desligar a ventilação, esfriar o motor, alarme que disparou…) sem trecho de segurança no topo nem na resposta',
             not rev4['comuns'], rev4['comuns']),
            ('revisão 4 do C5: "quando trocar o óleo do motor?" vai para o g_motores §7 (agenda), não para o §4 (pressão baixa); "como esfriar o motor (depois de navegar)" para o §6 (parada)',
             not rev4['oleo'] and not rev4['esfriar'], (rev4['oleo'], rev4['esfriar'])),
            ('revisão 4 do C5: "botão distress" e "distress" continuam locais (trecho de segurança do DSC)', not rev4['dsc'], rev4['dsc']),
            ('revisão 4 do C5: o trecho de segurança sai inteiro na tela e na voz, com o rótulo (e a nota da etiqueta no Seafire e no EPIRB) no fim',
             not rev4['inteira'], rev4['inteira']),
            ('revisão 4 do C5: depois do disparo do sistema fixo, a voz diz "não abra o acesso ao motor" e manda desligar motores, gerador e ventilação',
             not rev4['falaDisparo'], rev4['falaDisparo']),
            ('revisão 2 do C5: a pergunta do cartão do guincho não mostra a posição do barco',
             not confere.R_COORD.search(rev2['guincho']), rev2['guincho'][:200]),
            ('revisão 2 do C5: "guias de bordo" lista os 16 guias do D.guias, sem SEM DADOS nem "modelos não informados"',
             rev2['manualK'] == 'manual' and not rev2['manualSD'] and not rev2['faltam'], (rev2['manualK'], rev2['manualSD'], rev2['faltam'])),
        ]:
            if not cond:
                falhas += 1
                print('FALHA', nome, extra)
        print('ficha de bordo: %d letras' % len(f))
        if '-v' in sys.argv:
            print(f)
        # Fase 3 (P3A): com o quadro do replay (fonte `replay`), nenhuma resposta (texto, fonte nem fala) diz «coletor NMEA», e toda resposta de dado de bordo
        # traz a fonte do instante («telemetria ao vivo · 12:01:00»); a resposta não fica presa ao snapshot de 26/09 nem ao coletor (§6.6, último ponto)
        por_q = {r['q']: r for r in res}
        # (a frase padrão da sobreDados, P3C, fala do coletor NMEA da embarcação do cliente: a única resposta que pode dizê-lo)
        coletor = [r['q'] for r in res if r['key'] != 'sobreDados' and 'coletor NMEA' in r['text'] + '\n' + r['src'] + '\n' + r['curta']]
        falhas += conta('instante (P3A): com o quadro do replay nenhuma resposta diz «coletor NMEA» (texto, fonte ou fala)', not coletor, (len(coletor), coletor[:6]))
        sem_fonte = [q for q in FONTE_DO_INSTANTE if 'telemetria ao vivo · 12:01:00' not in por_q[q]['src']]
        falhas += conta('instante (P3A): a fonte das respostas de dado de bordo é a do instante («telemetria ao vivo · 12:01:00»)', not sem_fonte, (len(sem_fonte), [(q, por_q[q]['src'][:90]) for q in sem_fonte][:6]))
        # (o texto fixo «motores desligados», «sem alarme» e «Telemetria ao vivo desligada» das respostas é da reescrita das respostas, P3B; aqui, data e estado do snapshot)
        # (o período do consumo observado, 01/08–26/09/2026, é história do barco, não o instante do snapshot: sai antes da conferência)
        presas = [q for q in FONTE_DO_INSTANTE if re.search(r'26/09|undeado', por_q[q]['text'].replace('01/08–26/09/2026', ''))]
        falhas += conta('instante (P3A): nenhuma resposta de dado de bordo fica presa ao snapshot de 26/09 (data nem «fundeado»)', not presas, (len(presas), presas[:6]))
        falhas += agenda_sem_falta(pg)
        falhas += emergencia_1b(pg, res)
        falhas += faq_de_seguranca(pg)
        falhas += perguntas_da_g1(pg)
        falhas += consumo_sem_abastecimentos(b)
        # sem o capitao-clima.js (página acima): previsão SEM DADOS, nenhum vento previsto inventado
        sem = {r['q']: r for r in res}
        # Fase 3 (P3B, §2.5): a frase «Previsão e maré: sem conexão agora … confira o boletim da Marinha antes de sair» no lugar do SEM DADOS da 1.0.9
        for q in ('clima e vento', 'é seguro sair hoje?'):
            t = sem[q]['text']
            if 'Previsão e maré: sem conexão agora' not in t or 'boletim da Marinha antes de sair' not in t or 'SEM DADOS' in t or 'vento até' in t or 'rajadas até' in t:
                falhas += 1
                print('FALHA sem previsão carregada, %r inventou vento ou perdeu a frase do §2.5: %s' % (q, t[:200]))
        falhas += vento_do_dia(b)
        falhas += ficha_com_clima(b)
        falhas += instante_3a(b)
        if erros:
            falhas += 1
            print('ERROS DE SCRIPT:', erros)
        if '-v' in sys.argv:
            for r in res:
                print('\n## ' + r['q'] + ' → ' + r['key'] + '\n' + r['text'] + '\n' + r['src'] + '\n[voz] ' + r['curta'])
        b.close()
    sys.exit(1 if falhas else 0)


# ——————————————————————————————— 1b: emergência do cérebro (PROMPT §2.2, §2.3; CONTRATO §1.3, §1.5, §1.8, §6.2 «1b») ———————————————————————————————
# As respostas de emergência (sos, oleo, canal16, epirb, seafire, salvatagem e o diário com alerta) leem só o D.protocolos: o MMSI é o do rádio
# de bordo (nunca o número do cadastro), o indicativo é o da Licença de Estação, o Seafire e o EPIRB são o procedimento padrão com a etiqueta do
# equipamento (sem fabricante, modelo, validade nem lugar), e nenhuma traz posição, rumo, SOG, ETA, pessoas a bordo, leitura do quadro, SEM DADOS
# nem "último fix". As listas SOS, salvatagem, boia e EPIRB do cérebro são as do gerador (ferramentas/demo/confere.py), que marcam o `seguranca` dos
# trechos e dos itens do FAQ: uma fonte de verdade por lista, sem cópia que divirja.
EM_PERGUNTAS = {
    'sos': 'MAYDAY, homem ao mar!', 'oleo': 'pressão de óleo baixa no motor BB', 'canal16': 'roteiro do canal 16', 'rmmsi': 'qual o MMSI do barco?',
    'epirb': 'onde fica o EPIRB?', 'seafire': 'onde fica o seafire', 'disparo': 'o sistema fixo disparou', 'salvatagem': 'onde ficam os coletes?',
    'queda': 'tem gente na água', 'diario': 'registre no diário: homem ao mar',
}
EM_JS = """(qs) => { const B = window.CapitaoBrain, D = window.CapitaoDados, out = {};
  Object.keys(qs).forEach((k) => { const a = B.answer(qs[k], { platform: 'app', commit: false }); out[k] = { key: a.key, text: a.text, src: a.src, fala: B.falaCurta(a), ia: B.pedeIA(a, qs[k]) }; });
  const doc = (D.documentos || []).filter((d) => d.id === 'doc-epirb')[0] || {}, g1 = 'Situação e vencimento do documento: ' + (doc.n || ''),
    docs = B.answer('documentos vencendo', { platform: 'app', commit: false }), g1r = B.answer(g1, { platform: 'app', commit: false }), f = B.ficha('app', 'o que você sabe sobre o seguro?', null),
    eq = (D.equipamentos || []).filter((e) => e.seguranca).map((e) => ({ id: e.id, fabricante: e.fabricante, modelo: e.modelo, nota: e.nota })),
    bloco = (t) => { const i = f.indexOf('## ' + t); return i < 0 ? '' : f.slice(i, f.indexOf('\\n## ', i + 5) < 0 ? undefined : f.indexOf('\\n## ', i + 5)); };
  out.doc = { vence: doc.vence, n: doc.n, id: doc.id, docs: docs.text, g1: { key: g1r.key, text: g1r.text }, ficha: f, equipamentos: bloco('Equipamentos'), embarcacao: bloco('Embarcação'), emergencia: bloco('Emergência') };
  out.eq = eq; out.P = D.protocolos; out.listas = B.LISTAS;
  out.mmsi = D.embarcacao.mmsi;
  return out; }"""
EM_EMERG = """(ps) => { const B = window.CapitaoBrain; return ps.map((p) => [p, B.emergencia(p)]); }"""


# as palavras que a BOIA_FORA tem de ter: as seis do PROMPT §2.3 e as da revisão da 1b (a boia de nível do porão e do tanque, o sensor e a chave de boia, a de ancoragem)
BOIA_FORA_ESPERADA = ['amarra', 'poita', 'canal', 'baliza', 'cardinal', 'luz', 'nivel', 'porao', 'bomba', 'tanque', 'vaso', 'sanitario', 'combustivel', 'sensor', 'chave', 'ancor', 'fundei']


def emergencia_1b(pg, res):
    falhas = 0
    x = pg.evaluate(EM_JS, EM_PERGUNTAS)
    P, L = x['P'], x['listas']
    T = confere.carrega_termos()
    rot = re.compile(re.escape(confere.ROTULO), re.I)
    chaves = ('sos', 'oleo', 'canal16', 'rmmsi', 'epirb', 'seafire', 'disparo', 'salvatagem', 'queda', 'diario')
    esperadas = {'sos': 'sos', 'oleo': 'oleo', 'canal16': 'canal16', 'rmmsi': 'mmsi', 'epirb': 'epirb', 'seafire': 'seafire', 'disparo': 'seafire',
                 'salvatagem': 'salvatagem', 'queda': 'sos', 'diario': 'diario'}
    erros = []
    for k in chaves:
        r = x[k]
        txt = r['text'] + '\n' + r['fala']
        if r['key'] != esperadas[k]: erros.append('%s: chave %s' % (k, r['key']))
        if r['ia']: erros.append('%s: vai à IA' % k)
        if k == 'rmmsi':
            # P3C (CLAUDE.md 8, PROMPT §2.2): a rota `mmsi` é o único lugar de resposta onde o número do cadastro aparece, na 2ª linha («Cadastro do app: MMSI …»), nunca na 1ª nem na fala;
            # o resto da conferência (SEM DADOS, coordenada, leitura do quadro, as 8 regex) vale para ela como para as outras, com essa frase tirada
            segunda = 'Cadastro do app: MMSI %s.' % x['mmsi']
            ls = r['text'].split('\n')
            if len(ls) != 2 or ls[1] != segunda or str(x['mmsi']) in ls[0] or str(x['mmsi']) in r['fala']: erros.append('%s: o número do cadastro só na 2ª linha (%r)' % (k, ls))
            txt = txt.replace(segunda, ' ')
        elif '710123456' in txt or str(x['mmsi']) in txt: erros.append('%s: traz o número do cadastro do MMSI' % k)
        for rx, nome in ((re.compile(r'SEM DADOS|SEM LEITURA|último fix|snapshot|SNAPSHOT'), 'SEM DADOS/último fix/snapshot'), (confere.R_COORD, 'coordenada'),
                         (confere.R_EMERG_PROTOCOLO, 'MMSI/posição/rumo/ETA/pessoas (R_EMERG)'), (re.compile(r'\d\s*bar\b|\d\s*%|\d+\s*(?:rpm|°C)'), 'leitura do quadro')):
            m = rx.search(rot.sub(' ', txt))
            if m: erros.append('%s: %s «%s»' % (k, nome, m.group(0)))
        # as 8 regex do termos.json (menos a ANEXO) sobre o texto, com o rótulo do procedimento padrão (EXCEÇÃO do §3) tirado
        for nome, rx in T.items():
            if nome == 'ANEXO': continue
            m = rx.search(rot.sub(' ', txt))
            if m: erros.append('%s: %s «%s»' % (k, nome, m.group(0)))
    falhas += conta('1b: respostas de emergência (sos, oleo, canal16, mmsi, epirb, seafire, disparo, salvatagem, queda, diário com alerta): chave certa, no aparelho, sem o MMSI gerado, sem SEM DADOS, sem último fix, sem coordenada, sem leitura do quadro, nas 8 regex do termos.json', not erros, erros)
    # 1ª linha = a instrução de segurança; MMSI do rádio; indicativo da Licença; etiqueta do equipamento
    mm, ind, nota, rotulo = P['mmsiRadio'], P['indicativo'], P['seafire']['nota'], P['rotulo']
    l1 = lambda k: x[k]['text'].split('\n')[0]
    falhas += conta('1b: sos e canal16 abrem com a instrução e dizem o MMSI do rádio de bordo (etiqueta / Licença de Estação); canal16 o indicativo da Licença de Estação e o roteiro do protocolos, sem "SEM DADOS"',
                    l1('sos').startswith('Emergência — abra o SOS.') and mm in x['sos']['text'] and l1('canal16').startswith('Em perigo grave e iminente: MAYDAY no canal 16')
                    and mm in x['canal16']['text'] and ind in x['canal16']['text'] and ' — '.join(P['roteiro']) in x['canal16']['text'] and l1('rmmsi') == 'No MAYDAY e no DSC, use o MMSI da etiqueta do rádio (Licença de Estação).' and 'SEM DADOS' not in x['canal16']['text'],
                    (l1('sos'), l1('canal16'), x['canal16']['text'][:300]))
    falhas += conta('1b: sos traz a nota da etiqueta ("modelo, validade e acionamento: veja a etiqueta do equipamento") e os passos do MOB do protocolos; o diário com alerta traz os passos com o MMSI do rádio',
                    nota in x['sos']['text'] and all(m in x['sos']['text'] for m in P['mob']) and 'Se a emergência é agora: abra o SOS.' in x['diario']['text'] and mm in x['diario']['text'],
                    (x['sos']['text'][-300:], x['diario']['text'][-300:]))
    ep, sf = P['epirb']['passos'], P['seafire']['passos']
    falhas += conta('1b: epirb e seafire: todos os passos do protocolos, o rótulo do procedimento padrão e a etiqueta do equipamento; voz inteira (FALA_INTEIRA); 1ª linha é o primeiro passo',
                    all(t in x['epirb']['text'] for t in ep[1:]) and (ep[0][0].lower() + ep[0][1:]) in x['epirb']['text'] and all(t in x['seafire']['text'] for t in sf) and rotulo in x['epirb']['text'] and rotulo in x['seafire']['text']
                    and nota.capitalize() in x['epirb']['text'] and nota.capitalize() in x['seafire']['text'] and x['epirb']['fala'] == x['epirb']['text'] and x['seafire']['fala'] == x['seafire']['text']
                    and l1('epirb').startswith('EPIRB — ' + ep[0][0].lower() + ep[0][1:]) and l1('seafire') == 'Seafire — ' + sf[0], (x['epirb']['text'][:200], x['seafire']['text'][:200]))
    falhas += conta('1b: depois do disparo do sistema fixo (rota seafire): "não abra o acesso ao motor" e desligar motores, gerador e ventilação, na tela e na voz; o Seafire não traz fabricante, modelo, validade nem lugar',
                    all(t in x['disparo']['text'] and t in x['disparo']['fala'] for t in ('Não abra o acesso ao motor', 'desligue motores e gerador e corte a ventilação')) and x['disparo']['key'] == 'seafire', x['disparo']['text'][:200])
    falhas += conta('1b: oleo: os 4 passos do protocolos.oleo, sem leitura do quadro (nada de bar, rpm, snapshot nem "motores desligados"); a leitura fica no oleoLeitura',
                    all(t in x['oleo']['text'] for t in P['oleo']) and 'confira o manômetro agora' in x['oleo']['text'] and not re.search(r'snapshot|motores desligados|\d\s*bar', x['oleo']['text']), x['oleo']['text'])
    falhas += conta('1b: salvatagem: o texto fixo do protocolos, igual, na tela e na voz inteira; sem número de pessoas e sem lugar (paiol, armário, proa, popa)',
                    x['salvatagem']['text'].startswith(P['salvatagem']) and x['salvatagem']['fala'] == P['salvatagem'] and not re.search(r'paiol|arm[aá]rio|cabine|\bproa\b|\bpopa\b', x['salvatagem']['text'], re.I),
                    (x['salvatagem']['text'], x['salvatagem']['fala']))
    # 1b (revisão 3, PROMPT §2.2 «Diário com alerta»): o pedido «posição e hora, <alerta>» (ramo `junto` do ANSWERS.diario) também NÃO usa o resumoAgora(): a linha gravada e a
    # resposta levam a hora, «posição: ler no plotter» e os passos, sem coordenada, SOG, proa, snapshot nem leitura do quadro (antes gravava o resumo inteiro com a posição do barco)
    dj = pg.evaluate("""() => { const B = window.CapitaoBrain; localStorage.clear();
      return ['registre no diário a posição, tem fogo no motor', 'anote posição e hora, pressão de óleo baixa no motor BB', 'registre no diário posição e hora, homem ao mar'].map((q) => {
        const antes = B.loadDiario().length, a = B.answer(q, { platform: 'app' }), l = B.loadDiario();
        return { q, key: a.key, text: a.text, src: a.src, ia: B.pedeIA(a, q), novas: l.length - antes, linha: l.length > antes ? l[0].t : '' }; }); }""")
    err_dj = []
    for r in dj:
        txt = r['text'] + '\n' + r['linha']
        if r['key'] != 'diario' or r['ia'] or r['novas'] != 1: err_dj.append('%s: chave %s, ia %s, linhas novas %s' % (r['q'], r['key'], r['ia'], r['novas']))
        if 'posição: ler no plotter' not in r['linha'] or 'osição: ler no plotter' not in r['text']: err_dj.append('%s: sem «posição: ler no plotter» na linha e na resposta' % r['q'])
        for rx, nome in ((confere.R_COORD, 'coordenada'), (re.compile(r'SOG|\bproa\b|snapshot|SNAPSHOT|SEM DADOS|SEM LEITURA|motores desligados|\d\s*rpm|\d\s*bar\b|banco 24|vento'), 'leitura do quadro')):
            m = rx.search(txt)
            if m: err_dj.append('%s: %s «%s»' % (r['q'], nome, m.group(0)))
        if 'tem fogo' in r['q'] or 'homem ao mar' in r['q']:
            if mm not in r['text'] or 'Se a emergência é agora: abra o SOS.' not in r['text']: err_dj.append('%s: sem a instrução do SOS e o MMSI do rádio' % r['q'])
        else:
            if not all(t in r['text'] for t in P['oleo']): err_dj.append('%s: sem os passos de pressão de óleo' % r['q'])
    falhas += conta('1b (revisão 3): diário com alerta no ramo «posição e hora, <alerta>» (fogo, homem ao mar, pressão de óleo): a linha gravada e a resposta não trazem coordenada, SOG, proa nem leitura do quadro; levam «posição: ler no plotter» e os passos', not err_dj and len(dj) == 3, err_dj or dj)
    # as listas do cérebro são as do gerador (uma fonte de verdade por lista), e o port da emergencia() dá o mesmo resultado
    iguais = [(n, a, b) for n, a, b in (('SOS', L['SOS'], confere.SOS), ('SOS_REGEX', L['SOS_REGEX'], confere.SOS_REGEX_FONTES), ('SALVATAGEM', L['SALVATAGEM'], confere.SALVATAGEM),
                                          ('BOIA_FORA', L['BOIA_FORA'], confere.BOIA_FORA), ('EPIRB', L['EPIRB'], confere.EPIRB),
                                          ('EPIRB_REGEX', [L['EPIRB_REGEX']], [confere.EPIRB_REGEX])) if a != b]
    falhas += conta('1b: as listas SOS, as frases com contexto (SOS_REGEX, texto a texto), salvatagem, boia fora, EPIRB e a regex da baliza do cérebro são iguais às do gerador (confere.py), na mesma ordem', not iguais,
                    [(n, [t for t in a if t not in b], [t for t in b if t not in a]) for n, a, b in iguais])
    fora = [t for t in confere.SOS + confere.SALVATAGEM + confere.EPIRB if not confere.segura(t.strip())]
    falhas += conta('1b: toda palavra da lista SOS, da salvatagem e do EPIRB faz o gerador marcar `seguranca` (a SEGURANCA_PALAVRAS é a mesma lista)', not fora, fora)
    qs = [q for q, _ in CASOS] + ['o sistema de som disparou o alarme', 'o disjuntor caiu', 'a água subindo no porão', 'o barco bateu em 3 nós', 'quanto custa a diária']
    ps = [confere.pad(q) for q in qs]
    dif = [(p, a) for p, a in pg.evaluate(EM_EMERG, ps) if bool(a) != bool(confere.emergencia(p))]
    falhas += conta('1b: a emergencia() do cérebro e a do gerador dão o mesmo resultado nas %d perguntas dos casos' % len(ps), not dif, dif[:5])
    # papelada do EPIRB sem a data (CONTRATO §1.8): docsvenc, a pergunta da G1 do certificado e a ficha dizem a etiqueta, nunca a data
    d = x['doc']
    falhas += conta('1b: docsvenc, a pergunta da G1 do certificado do EPIRB e a ficha não trazem a data do doc-epirb e dizem "veja a etiqueta do equipamento"',
                    d['vence'] and d['vence'] not in d['docs'] and d['vence'] not in d['g1']['text'] and d['vence'] not in d['ficha'] and d['g1']['key'] == 'docsvenc'
                    and nota in d['docs'] and nota in d['g1']['text'], (d['vence'], d['docs'][-260:]))
    ide = [e for e in x['eq'] if e['id'] in ('epirb', 'seafire')]
    nomes = [t for e in ide for t in (e['fabricante'], e['modelo']) if t and t != 'Seafire']
    falhas += conta('1b: a ficha (## Equipamentos) mostra a nota da etiqueta no lugar de fabricante e modelo do EPIRB e do Seafire; ## Embarcação diz o MMSI do cadastro do app e o indicativo da Licença; ## Emergência tem o MMSI do rádio e não o número',
                    len(ide) == 2 and not [t for t in nomes if t in d['equipamentos']] and d['equipamentos'].count(nota) == 2 and 'MMSI ' + x['mmsi'] + ' (cadastro do app)' in d['embarcacao']
                    and 'indicativo: ' + ind in d['embarcacao'] and mm in d['emergencia'] and x['mmsi'] not in d['emergencia'], (nomes, d['equipamentos'][:300], d['embarcacao'][-200:]))
    # a ficha de hoje + cada resposta de emergência do TERMOS: o mesmo conjunto de regex já foi aplicado acima; aqui a ficha inteira, sem o número do MMSI fora de ## Embarcação
    fora_emb = d['ficha'].replace(d['embarcacao'], ' ')
    falhas += conta('1b: o número do MMSI do cadastro só aparece em ## Embarcação da ficha', x['mmsi'] not in fora_emb, [l for l in fora_emb.split('\n') if x['mmsi'] in l][:2])
    # Cada palavra de unidade do «bateu em um/uma/num/numa <unidade>» e cada palavra da BOIA_FORA tem a sua prova (uma palavra tirada da lista tem de reprovar
    # aqui, não só nas frases dos casos): a leitura nunca é batida; a boia de nível, de ancoragem, do porão e do tanque nunca é salvatagem
    unidades = ['bar', 'litro', 'litros', 'milhão', 'grau', 'graus', 'volt', 'volts', 'hora', 'horas', 'minuto', 'minutos', 'segundo', 'segundos', 'dia', 'dias',
                'metro', 'metros', 'nós', 'onda', 'ondas', 'marola', 'rajada', 'rajadas']
    ps = [confere.pad('o contador bateu %s %s' % (art, u)) for u in unidades for art in ('em um', 'em uma', 'num', 'numa')]
    batidas = [p for p, a in pg.evaluate(EM_EMERG, ps) if a]
    controle = [p for p, a in pg.evaluate(EM_EMERG, [confere.pad(q) for q in ('o barco bateu em uma pedra', 'bateu num banco de areia', 'bateu em outro barco')]) if not a]
    falhas += conta('1b (revisão): «bateu em um/uma/num/numa <unidade, onda ou rajada>» nunca é emergência (%d frases) e a batida em pedra, banco e outro barco é' % len(ps), not batidas and not controle, (batidas[:3], controle))
    falhas += grades_2a_revisao(pg)
    falhas += grades_4a_revisao(pg)
    boias = pg.evaluate("""(ws) => { const B = window.CapitaoBrain; return ws.map((w) => [w, B.answer('a boia ' + w + ' está travada', { platform: 'app', commit: false }).key]).concat([['', B.answer('a boia está travada', { platform: 'app', commit: false }).key]]); }""", BOIA_FORA_ESPERADA)
    ruins = [(w, k) for w, k in boias if (k == 'salvatagem') != (w == '')]
    faltam = [w for w in BOIA_FORA_ESPERADA if w not in L['BOIA_FORA']]
    falhas += conta('1b (revisão): cada palavra da BOIA_FORA (as da PROMPT §2.3 e as da revisão: boia de nível, porão, bomba, tanque, vaso, sensor, chave, âncora) tira a «boia» da salvatagem (%d palavras) e a «boia» sozinha continua sendo salvatagem' % len(BOIA_FORA_ESPERADA),
                    not ruins and not faltam, (ruins, faltam))
    print('1b: emergência do cérebro: %d falhas' % falhas)
    return falhas


# Segunda revisão da 1b: a regex de emergência vem de lista positiva. Cada grade combina o que a frase tem de variar e prova os dois lados (o que é emergência
# e o que é leitura, equipamento ou outro assunto): uma palavra tirada de uma lista reprova aqui, não só nas frases soltas dos CASOS.
def grades_2a_revisao(pg):
    falhas = 0
    nao_barco = ['o consumo', 'a temperatura', 'a pressão do óleo', 'o vento', 'a bateria', 'o horímetro', 'a rotação', 'o nível do tanque', 'o motor', 'o gerador',
                 'a tensão', 'o contador', 'o preço', 'a previsão', 'o sensor', 'a onda', 'a chuva', 'o sol', 'a porta', 'a vela', 'o ponteiro']
    abstratos = ['valor', 'pico', 'patamar', 'recorde', 'limite', 'marca', 'mínimo', 'máximo', 'nível', 'ponto', 'meta', 'média', 'total', 'número', 'degrau', 'teto',
                 'piso', 'regime', 'ritmo', 'estado', 'modo', 'padrão', 'alvo', 'índice', 'intervalo', 'platô']
    barcos = ['o barco', 'a lancha', 'o iate', 'o veleiro', 'um barco', 'uma lancha', 'outro barco', 'a lancha ao lado', 'o jet ski', 'o outro barco', 'alguém', 'a gente']
    # (nome, frases, é emergência?)
    G = [
        ('«bateu em um/uma/num/numa <valor, pico, limite…>»', ['%s bateu %s %s' % (sj, art, a) for sj in nao_barco[:12] for a in abstratos
                                                                for art in ('em um', 'em uma', 'num', 'numa')], False),
        ('«bateu forte / em cheio / de lado / em mim / na gente» com sujeito que não é o barco (motor, preço, vento, onda, vela…)',
         ['%s bateu %s' % (sj, f) for sj in nao_barco for f in ('forte', 'em cheio', 'de lado', 'em mim', 'na gente', 'em nós')], False),
        ('«bateu no casco / no fundo / no banco» com sujeito de onda, vento, nível, ponteiro, pix ou dinheiro',
         ['%s bateu %s' % (sj, f) for sj in ('a onda', 'as ondas', 'o vento', 'a rajada', 'a marola', 'o nível do tanque', 'o ponteiro', 'o pix', 'o dinheiro', 'o pagamento')
          for f in ('no casco', 'no fundo', 'no banco', 'na proa')], False),
        ('«bateu forte / de lado / em cheio / em nós / na gente / no casco» com o barco, outra lancha ou «alguém» de sujeito, e a primeira pessoa («batemos», «bati»)',
         ['%s bateu %s' % (sj, f) for sj in barcos for f in ('forte', 'de lado', 'em cheio', 'em nós', 'na gente', 'em mim', 'no casco', 'na proa')]
         + ['batemos', 'bati', 'batemos forte', 'bati de lado', 'batemos em cheio', 'bati com o barco numa pedra', 'batemos com o casco numa pedra'], True),
        ('o equipamento que «faz água» (dessalinizador, geladeira, ar-condicionado, freezer, chuveiro) e a água doce, quente ou potável',
         ['%s %s' % (sj, f) for sj in ('o dessalinizador', 'a geladeira', 'o ar condicionado', 'o freezer', 'o chuveiro', 'o ar-condicionado do barco')
          for f in ('está fazendo água', 'faz água', 'começou a fazer água', 'está fazendo água doce')]
         + ['estou fazendo água quente', 'estamos fazendo água potável', 'o barco está fazendo água doce', 'o barco tomou água doce no píer', 'estou tomando água',
            'estou fazendo água quente para o café'], False),
        ('o barco ou «nós» fazendo, tomando ou começando a deixar entrar água',
         ['%s %s' % (sj, f) for sj in ('o barco', 'a lancha', 'o iate', 'o casco', 'estamos') for f in ('está fazendo água', 'começou a fazer água', 'está fazendo muita água', 'está tomando água',
                                                                                                            'começou a tomar água')]
         + ['começou a entrar água no barco', 'entrou água no motor', 'a água entrou no casco', 'fazendo água pelo casco', 'fazendo água no porão', 'estou fazendo água',
            'estou fazendo muita água'], True),
        ('sangramento técnico (o ar, o combustível, o filtro, as linhas, o sistema, a bomba, o bico, o freio)',
         ['%s %s' % (v, o) for v in ('sangrar', 'sangrando', 'sangra', 'sangrou') for o in ('o ar', 'o combustível', 'o filtro', 'as linhas',
          'o sistema', 'a bomba', 'o circuito', 'o racor', 'o bico injetor', 'o freio', 'o ar do sistema de combustível', 'o diesel', 'o óleo')]
         + ['sangramento %s' % o for o in ('do ar', 'do combustível', 'do filtro', 'das linhas', 'do sistema', 'da bomba', 'do circuito', 'do racor', 'do bico injetor', 'do freio',
                                         'do ar do sistema de combustível', 'do diesel', 'do óleo')]
         + ['como sangrar o motor', 'sangrar o ar do circuito de arrefecimento', 'passo a passo para sangrar o sistema hidráulico'], False),
        ('ferimento: sangrando, sangrou, sangramento, não para de sangrar, sangue e hemorragia',
         ['ele está sangrando', 'ela sangrou muito', 'sangrou o dedo', 'sangrando na cabeça', 'o braço sangra', 'sangramento no braço', 'sangramento forte', 'não para de sangrar',
          'continua sangrando', 'parou de sangrar', 'sangrar muito', 'muito sangue', 'tem sangue no chão', 'hemorragia', 'ele teve uma hemorragia'], True),
        ('água doce, olhos, ouvido, bota, celular ou tanque de água que «recebem» água: não é água entrando no casco',
         ['entrou água no ouvido', 'entrou água no olho', 'entrou água na bota', 'entrou água no celular', 'entrou água no tanque de água doce', 'a água entrou no tanque de água potável',
          'a água do ar condicionado entrou na cabine', 'a água entra pelo filtro de água salgada', 'entrou água na geladeira'], False),
        ('mangueira que estoura, solta, rompe ou fura (menos a de lavagem, do chuveiro e do ar-condicionado)',
         [f % m for f in ('a mangueira %s estourou', 'a mangueira %s soltou', 'rompeu a mangueira %s', 'a mangueira %s furou', 'estourou a mangueira %s') for m in ('', 'do motor', 'de combustível', 'de água salgada', 'do escapamento')]
         , True),
        ('a mangueira de uso (lavagem, chuveiro, pia, ar-condicionado)',
         ['a mangueira de lavagem estourou', 'a mangueira do chuveiro soltou', 'a mangueira da pia furou', 'a mangueira do ar condicionado soltou', 'a mangueira de lavar o convés rompeu'], False),
        # 1b (revisão 3): as guardas de água são LOCAIS (presas ao verbo), não da frase inteira
        ('relato de alagamento que cita o que molhou ou parou (celular, geladeira, filtro, gelo, pia, chuveiro, dessalinizador, ar-condicionado)',
         [f % x for f in ('entrou água no barco e %s', 'estamos fazendo água e %s', 'o barco está fazendo água e %s', 'a água está entrando e %s', 'o porão está cheio e %s',
                          '%s, estamos fazendo água', '%s e entrou água no barco')
          for x in ('molhou o celular', 'a geladeira parou', 'o filtro de água encharcou', 'o gelo acabou', 'a pia entupiu', 'o chuveiro parou', 'o dessalinizador desligou',
                    'o ar condicionado caiu', 'o freezer desarmou')], True),
        ('o equipamento que «faz água» é o sujeito do verbo (bebedouro, purificador, máquina de gelo, torneira, pia, ralo, sanitário, ar): rotina, não alagamento',
         ['%s %s' % (sj, f) for sj in ('o bebedouro', 'o purificador', 'a máquina de gelo', 'a torneira', 'a pia', 'o ralo', 'o sanitário', 'o ar', 'o freezer', 'o frigobar',
                                       'o dessalinizador do barco', 'o ar condicionado da cabine do barco')
          for f in ('está fazendo água', 'tá fazendo água', 'faz água', 'começou a fazer água', 'ainda está fazendo água')], False),
        ('«fazendo água» que não é o casco: água doce, quente, potável, mineral, para o café, na boca, de coco',
         ['fazendo água %s' % x for x in ('doce', 'quente', 'potável', 'mineral', 'gelada', 'para o café', 'com gelo', 'na boca', 'de coco', 'na pia', 'no chuveiro')], False),
        ('«fazendo água» sem sujeito (a forma curta de quem está em pânico)',
         ['fazendo água', 'tá fazendo água', 'ta fazendo agua', 'está fazendo água', 'ele tá fazendo água', 'ela está fazendo água', 'fazendo muita água', 'tá fazendo água demais',
          'fazendo água pelo casco', 'fazendo água no porão', 'fazendo água!'], True),
        ('o relato do porão com «está/tá» (cheio, enchendo, subindo, alagando), a água que sobe ou entra no porão, a bomba que não para e o alarme que disparou',
         ['o porão %s %s' % (a, b) for a in ('está', 'tá', 'continua', 'ficou') for b in ('cheio', 'enchendo', 'alagando', 'subindo')]
         + ['a água %s %s no porão' % (a, b) for a in ('está', 'tá', 'vem') for b in ('subindo', 'entrando', 'enchendo')]
         + ['a bomba de porão %s' % x for x in ('não para', 'não está dando conta', 'não dá conta', 'está ligada direto', 'não desliga')]
         + ['as bombas de porão %s' % x for x in ('não param', 'não estão dando conta', 'estão funcionando sem parar')]
         + ['%s %s' % (a, b) for a in ('o alarme do porão', 'o alarme de porão', 'o alarme da bomba de porão') for b in ('disparou', 'tocou', 'soou', 'acendeu', 'está tocando', 'tá soando')]
         + ['alarme do porão', 'alarme de porão', 'disparou o alarme do porão'], True),
        ('o porão e o alarme em pergunta ou rotina (nível normal, testar o alarme, como funciona, alarme do painel, bomba que não liga, luz do porão)',
         ['qual o nível normal do porão', 'testar o alarme de porão', 'como funciona o alarme do porão', 'o que fazer quando o alarme do porão tocar', 'alarme do painel do porão',
          'alarme de nível do porão', 'a bomba de porão não está ligando', 'a luz do porão acendeu', 'o alarme do porão está ligado?', 'o alarme do porão está ativado',
          'como testo as bombas de porão', 'nível do porão normal'], False),
        ('o barco que toca o fundo (sos) e a âncora, o ferro, a poita, a corrente e a sonda que tocam o fundo no fundeio (rotina)',
         ['o barco tocou o fundo', 'a quilha tocou o fundo', 'tocamos o fundo', 'tocou no fundo', 'a lancha tocou no fundo', 'a hélice tocou o fundo'], True),
        ('a âncora, o ferro, a poita, o chumbo e a sonda que tocam o fundo ou raspam numa pedra',
         ['%s %s' % (sj, v) for sj in ('a âncora', 'o ferro', 'a poita', 'o chumbo', 'a sonda', 'o prumo', 'o mergulhador') for v in ('tocou o fundo', 'tocou no fundo', 'raspou numa pedra', 'esbarrou numa pedra')]
         + ['quando a âncora tocou no fundo, quantos metros de cabo eu solto?', 'o ferro já tocou no fundo'], False),
        ('o eixo e o leme com palavras no meio do relato (quebrou, partiu, travou)',
         ['o eixo %s quebrou' % x for x in ('da hélice', 'da hélice de bombordo', 'do motor de boreste', 'do barco', 'da hélice de bombordo agora mesmo', 'principal')]
         + ['o leme %s' % x for x in ('do barco quebrou', 'da lancha travou agora', 'quebrou de vez', 'partiu', 'travou')]
         + ['perdi totalmente o leme', 'perdemos o governo'], True),
        ('fogo sem a palavra «fogo»',
         ['chamas no motor', 'tem chamas na cozinha', 'labaredas', 'uma chama no painel', 'faíscas no quadro', 'o cabo faiscou', 'curto circuito', 'curto-circuito no painel',
          'cheiro de plástico queimado', 'cheiro de fio queimado', 'queimando o painel', 'o motor está queimando', 'o painel está queimando', 'choque no painel',
          'ele levou um choque', 'a tomada está dando choque', 'o painel está fumegando'], True),
        ('queimar óleo ou combustível, lâmpada queimada, chama do fogão, choque térmico e choque de preço',
         ['o motor está queimando óleo', 'estamos queimando 40 litros por hora', 'queimando muito diesel', 'lâmpada queimada', 'a chama do fogão está azul', 'choque térmico',
          'o preço deu um choque', 'o fusível queimou', 'o motor de partida queimou'], False),
    ]
    todas = [confere.pad(q) for _, qs, _ in G for q in qs]
    r = {p: a for p, a in pg.evaluate(EM_EMERG, todas)}
    for nome, qs, esperado in G:
        ruins = [q for q in qs if bool(r[confere.pad(q)]) != esperado]
        falhas += conta('1b (revisão 2): %s: %s (%d frases)' % (nome, 'é emergência' if esperado else 'não é emergência', len(qs)), not ruins, ruins[:6])
    dif = [q for _, qs, _ in G for q in qs if bool(r[confere.pad(q)]) != bool(confere.emergencia(confere.pad(q)))]
    falhas += conta('1b (revisão 2): a emergencia() do cérebro e a do gerador dão o mesmo resultado nas %d frases das grades' % len(todas), not dif, dif[:6])
    return falhas


# Quarta revisão da 1b (achados da revisão do commit a237ba8): as mesmas grades por classe, agora com a vizinhança das frases pedidas (perigo, água a bordo, encalhe,
# pessoa na água, saúde, fogo, governo e propulsão, combustível e gás, alarme do porão). Cada grade prova os dois lados: a frase de emergência abre o `sos` e a de rotina ao
# lado (o motor que engasga, o tanque de água doce, a conversa, o controle remoto) não. Uma palavra tirada de uma lista ou uma guarda tirada de uma regex reprova aqui.
def grades_4a_revisao(pg):
    falhas = 0
    G = [
        ('perigo, risco de vida e pedido de ajuda urgente', ['estamos em perigo', 'estou em perigo', 'estamos em perigo de vida', 'risco de vida', 'corremos risco de vida',
         'perigo de morte', 'risco de morte', 'preciso de ajuda urgente', 'preciso urgente de ajuda', 'socorro urgente', 'estamos perdidos no mar'], True),
        ('perigo e risco que não são de vida (carta, clima, navegação noturna)', ['zona de perigo da carta', 'perigo isolado no canal', 'qual o perigo de navegar à noite',
         'qual o risco de chuva hoje', 'a tarefa é urgente', 'manutenção urgente do gerador'], False),
        ('água a bordo: «pegando água», «entrando muita água»', ['o barco está pegando água', 'a lancha pegou água', 'estamos pegando água', 'tá entrando muita água',
         'está entrando muita água no barco', 'está entrando bastante água', 'entrando muita água'], True),
        ('pegar água do cais, do tanque ou para o gelo', ['estou pegando água no cais', 'estamos pegando água doce', 'estamos pegando água para o gelo', 'pegando água mineral',
         'vou pegar água no tanque'], False),
        ('encalhe, fundo, pedra e batida que vem aí', ['vamos bater', 'vamos bater!', 'vamos bater numa pedra', 'vamos bater no cais', 'vamos bater em outro barco', 'ai vamos bater',
         'o barco raspou no fundo', 'raspamos no fundo', 'encostamos no fundo', 'encostamos numa pedra', 'raspou numa laje', 'estamos em cima de uma pedra', 'ficamos numa laje',
         'estamos sobre uma pedra', 'prestes a colidir', 'quase encalhar'], True),
        ('bater papo, foto, martelo ou recorde; a âncora, o ferro e o mergulhador que raspam ou encostam no fundo', ['vamos bater um papo', 'vamos bater uma foto', 'vamos bater o martelo',
         'vamos bater o recorde', 'a âncora raspou no fundo', 'a sonda raspou no fundo', 'o mergulhador encostou no fundo', 'a poita encostou no fundo', 'a corrente encostou no fundo',
         'estamos nos corais', 'estamos num recife de coral'], False),
        ('pessoa ao mar, perdida de vista, afogada ou «a pessoa que caiu»', ['mulher ao mar', 'pessoa ao mar', 'criança ao mar', 'o marinheiro foi ao mar', 'tripulante foi ao mar',
         'meu amigo foi ao mar', 'o pai foi ao mar', 'ele se afogou', 'ela se afogou', 'dois se afogaram', 'perdi o mergulhador de vista', 'perdi meu amigo de vista',
         'perdemos a mulher de vista', 'perdi a pessoa de vista', 'perdemos o homem de vista', 'perdi o meu marido de vista', 'ninguém consegue ver a pessoa que caiu',
         'não vejo o amigo que caiu', 'não vejo quem caiu'], True),
        ('perder de vista o barco, a marina ou o celular; ir ao mar', ['perdi o celular de vista', 'perdemos o barco de vista', 'perdemos a marina de vista', 'a pessoa da marina foi embora',
         'vamos ao mar amanhã', 'o barco foi ao mar', 'a gente foi ao mar ontem'], False),
        ('saúde: respirar, coração, fratura, corte, queimadura, engasgo, mal-estar e quem foi atingido', ['ele parou de respirar', 'ela não respira', 'ele não está respirando',
         'a pessoa não respira', 'ele ainda não respira', 'meu filho não respira', 'ataque cardíaco a bordo', 'ataque cardíaco', 'parada cardíaca', 'enfarte', 'ele teve um enfarte',
         'fratura exposta', 'corte profundo no braço', 'cortou a mão feio', 'ela cortou o pé', 'quebrou o braço', 'ela quebrou a perna', 'o braço está quebrado', 'ele está engasgado',
         'a criança está engasgada', 'ele engasgou com a comida', 'queimou a mão no escapamento', 'queimei a mão', 'pessoa passando mal no barco', 'ele passou mal', 'hipotermia',
         'cabo estourou e acertou alguém', 'o cabo atingiu um tripulante', 'prendeu a mão no cabo', 'esmagou o dedo', 'dificuldade para respirar', 'ele está inconsciente'], True),
        ('o motor que engasga, o tanque que não respira, cortar a energia ou o combustível, queimar fusível, lâmpada ou motor, quebrar uma peça, o braço do guincho',
         ['o motor engasgou', 'o motor está engasgando', 'o respiro do tanque não respira', 'o tanque não respira', 'cortou a energia', 'cortou o motor', 'cortou o combustível',
          'queimou o fusível', 'a lâmpada queimou', 'queimou o motor de partida', 'quebrou o suporte da tela', 'quebrou a tampa do tanque', 'quebrou o braço do guincho',
          'quebrou o braço do limpador', 'esmagou a lata', 'atingiu a meta', 'acertou o rumo', 'acertou a posição', 'prendeu o cabo na cleat'], False),
        ('fogo sem a palavra e explosão', ['tem chama no painel', 'tem chama na cozinha', 'temos chama no motor', 'chama no painel', 'chama na praça de máquinas', 'vi um barco com chama no casco',
         'explodiu o motor', 'vai explodir', 'explosão no motor'], True),
        ('chama do fogão, de vela ou de isqueiro', ['tem chama no fogão?', 'a chama do fogão está azul', 'tem chama de vela', 'a chama do isqueiro', 'sem chama no fogareiro'], False),
        ('leme, hélice e eixo que emperram, soltam, enroscam ou caem; perda de governo ou de propulsão; barco que não obedece ou está sem controle; motores que pararam; deriva para as pedras',
         ['o leme emperrou', 'leme preso', 'o leme caiu', 'o leme saiu', 'o leme do barco falhou', 'perda de governo', 'perda de propulsão', 'perdemos a propulsão', 'sem propulsão',
          'estamos sem propulsão e sem governo', 'o barco não obedece ao leme', 'o barco não governa', 'estamos sem controle', 'o barco está sem controle', 'a lancha ficou fora de controle',
          'hélice quebrada', 'a hélice enroscou', 'a hélice enroscou numa rede', 'a hélice travou', 'o eixo soltou', 'o eixo travou', 'perdemos os dois motores', 'perdi a direção',
          'os dois motores pararam', 'os 2 motores apagaram', 'ambos os motores falharam', 'vento nos levando para as pedras', 'a correnteza está nos levando para as pedras',
          'a maré está nos jogando contra as rochas', 'estamos derivando'], True),
        ('leme pesado ou com folga, hélice a trocar, eixo lubrificado, controle remoto, um motor desligado, a corrente que leva para o sul, as pedras de passeio',
         ['o leme está pesado', 'o leme está com folga', 'trocar a hélice', 'a hélice está limpa', 'a hélice nova chegou', 'o eixo está lubrificado', 'estamos sem controle remoto',
          'perdi o controle remoto', 'perdi o controle do ar', 'o ar está sem controle remoto', 'perdemos o sinal do GPS', 'os dois motores desligaram', 'os motores estão desligados',
          'a corrente nos leva para o sul', 'estamos indo para as pedras de Cabeçudas', 'o vento está forte'], False),
        ('combustível e gás que vazam (a ordem inversa) ou estão no porão', ['o diesel está vazando', 'tem diesel vazando', 'combustível vazando', 'o combustível está vazando',
         'tem diesel vazando no porão', 'tem combustível no porão', 'diesel no porão', 'combustível no porão', 'vazamento no tanque de diesel', 'vazamento na linha de combustível',
         'o tanque de diesel está vazando', 'o tanque de combustível está furado', 'gás vazando', 'o gás está vazando', 'cheiro forte de gás', 'cheiro muito forte de diesel',
         'cheiro estranho de combustível', 'cheiro de gasolina'], True),
        ('o tanque de água doce que vaza, o diesel no tanque, o consumo, o gás do fogão, o preço do combustível', ['o tanque de água doce está vazando', 'o tanque de água está vazando',
         'diesel no tanque', 'o consumo de diesel está alto', 'o gás do fogão acabou', 'quanto custa o combustível no cais', 'como sangrar o combustível do motor', 'o cheiro do café'], False),
        ('o alarme de nível do porão que disparou ou está tocando (até 3 palavras entre «alarme» e «porão»)', ['o alarme de nível do porão disparou', 'o alarme de nível do porão está tocando',
         'o alarme do painel do porão disparou', 'o alarme da bomba de porão soou', 'disparou o alarme de nível do porão', 'tocou o alarme do painel do porão', 'o alarme disparou no porão',
         'o alarme tocou no porão'], True),
        ('o alarme do porão em pergunta ou rotina (ativado, ligado, testar, como funciona, qual)', ['o alarme do porão está ativado', 'o alarme de nível do porão está ligado?',
         'testar o alarme de nível do porão', 'como funciona o alarme do painel do porão', 'qual o alarme de nível do porão', 'como testo o alarme do painel do porão'], False),
    ]
    todas = [confere.pad(q) for _, qs, _ in G for q in qs]
    r = {p: a for p, a in pg.evaluate(EM_EMERG, todas)}
    for nome, qs, esperado in G:
        ruins = [q for q in qs if bool(r[confere.pad(q)]) != esperado]
        falhas += conta('1b (quarta revisão): %s: %s (%d frases)' % (nome, 'é emergência' if esperado else 'não é emergência', len(qs)), not ruins, ruins[:6])
    dif = [q for _, qs, _ in G for q in qs if bool(r[confere.pad(q)]) != bool(confere.emergencia(confere.pad(q)))]
    falhas += conta('1b (quarta revisão): a emergencia() do cérebro e a do gerador dão o mesmo resultado nas %d frases das grades' % len(todas), not dif, dif[:6])
    # as frases de emergência da grade abrem no aparelho: a chave é `sos` e a IA não é chamada (a trava §2.3, na ponta que o usuário toca)
    pos = [q for _, qs, e in G if e for q in qs]
    resp = pg.evaluate("""(qs) => { const B = window.CapitaoBrain; return qs.map((q) => { const a = B.answer(q, { platform: 'app', commit: false }); return [q, a.key, B.pedeIA(a, q)]; }); }""", pos)
    ruins = [(q, k, ia) for q, k, ia in resp if k != 'sos' or ia]
    falhas += conta('1b (quarta revisão): as %d frases de emergência das grades abrem a resposta `sos` e não vão à IA' % len(pos), not ruins, ruins[:6])
    # PROMPT §2.2: o relato de água a bordo, de porão e de abandono vai para `sos` COM o passo a passo (protocolos.alagamento / abandono), antes da ordem geral; o resto, não
    sos = pg.evaluate("""() => { const B = window.CapitaoBrain, P = window.CapitaoDados.protocolos, out = {};
      ['o barco está pegando água', 'tá entrando muita água', 'o porão está cheio', 'o alarme de nível do porão disparou', 'a bomba de porão não para', 'furou o casco',
       'preciso abandonar o barco', 'vamos abandonar o barco, o porão está cheio', 'tem diesel no porão', 'cheiro forte de gás', 'alguém caiu na água',
       'MAYDAY, homem ao mar!', 'tem fogo no motor', 'ele parou de respirar']
        .forEach((q) => { const a = B.answer(q, { platform: 'app', commit: false }); out[q] = { key: a.key, text: a.text, fala: B.falaCurta(a), l1: a.text.split('\\n')[0] }; });
      const pp = B.answer('como faço um PAN-PAN?', { platform: 'app', commit: false }), c16 = B.answer('roteiro do canal 16', { platform: 'app', commit: false });
      return { out, alag: P.alagamento[0], aband: P.abandono[0], panpan: P.panpan, pp: { key: pp.key, text: pp.text }, c16: { key: c16.key, text: c16.text } }; }""")
    O = sos['out']
    com_alag = ['o barco está pegando água', 'tá entrando muita água', 'o porão está cheio', 'o alarme de nível do porão disparou', 'a bomba de porão não para', 'furou o casco',
                'vamos abandonar o barco, o porão está cheio']
    com_aband = ['preciso abandonar o barco', 'vamos abandonar o barco, o porão está cheio']
    ruins = []
    for q, o in O.items():
        if o['key'] != 'sos': ruins.append('%s: chave %s' % (q, o['key']))
        if not o['l1'].startswith('Emergência — abra o SOS.'): ruins.append('%s: 1ª linha %r' % (q, o['l1']))
        if (sos['alag'] in o['text']) != (q in com_alag): ruins.append('%s: %s o passo do alagamento' % (q, 'sem' if q in com_alag else 'com'))
        if (sos['aband'] in o['text']) != (q in com_aband): ruins.append('%s: %s o passo do abandono' % (q, 'sem' if q in com_aband else 'com'))
        if q in com_alag + com_aband and (sos['alag'] in o['text'] or sos['aband'] in o['text']) and o['text'].index('Ordem (') < max(o['text'].find(sos['alag']), o['text'].find(sos['aband'])):
            ruins.append('%s: o passo do relato vem depois da ordem geral' % q)
        if confere.R_COORD.search(o['text']) or re.search(r'SEM DADOS|snapshot|\d\s*(?:bar|rpm|°C)', o['text']): ruins.append('%s: coordenada, SEM DADOS ou leitura do quadro' % q)
    falhas += conta('1b (quarta revisão): o relato de água a bordo, do porão, do casco e de abandono abre o `sos` com o passo do protocolos (alagamento, abandono) logo depois da instrução, antes da '
                    'ordem geral; combustível no porão, gás, pessoa na água, fogo e saúde não levam o passo do alagamento (não se bombeia diesel); nada de coordenada nem leitura do quadro',
                    not ruins and len(O) == 14, ruins)
    # a baliza de sinalização não é o EPIRB (achado da revisão: «por que a baliza do canal está piscando?» devolvia o «Disparo por engano… avise no canal 16» e barrava a IA): com palavra de
    # sinalização e sem palavra só do EPIRB a busca não traz o guia do EPIRB nem a seção EPIRB do protocolo; com «teste», «onde fica», «epirb» ou «autoteste», traz
    bal = pg.evaluate("""() => { const B = window.CapitaoBrain, f = (q) => B.buscaBase(q, 3).map((x) => x.d.fonte + ' · ' + x.d.secao);
      return { sinal: ['por que a baliza do canal está piscando?', 'baliza do canal', 'a baliza do canal está piscando', 'baliza cardinal', 'luz da baliza', 'a baliza de entrada da barra', 'o teste da baliza do canal', 'teste da luz da baliza'].map((q) => [q, f(q)]),
               epirb: ['teste da baliza', 'como testar a baliza?', 'onde fica a baliza', 'a baliza do epirb', 'autoteste da baliza no canal 16', 'epirb no canal 16'].map((q) => [q, f(q)[0] || '']) }; }""")
    ruins = [(q, t) for q, t in bal['sinal'] if [x for x in t if 'EPIRB' in x]] + [(q, t) for q, t in bal['epirb'] if not t.startswith('Guia de bordo — EPIRB')]
    falhas += conta('1b (quarta revisão): baliza de sinalização (canal, cardinal, luz, barra, piscando) não traz o EPIRB na busca; teste, «onde fica», epirb e autoteste da baliza trazem', not ruins, ruins)
    # protocolos.panpan é lido: a rota do canal 16 (onde «PAN-PAN» cai) o traz inteiro, no lugar da frase solta
    falhas += conta('1b (quarta revisão): «PAN-PAN» e o roteiro do canal 16 trazem o protocolos.panpan, inteiro, e o roteiro MAYDAY continua', sos['pp']['key'] == 'canal16' and sos['panpan'] in sos['pp']['text']
                    and sos['panpan'] in sos['c16']['text'] and ' — '.join(PROTOCOLOS_ROTEIRO(pg)) in sos['c16']['text'], (sos['pp']['key'], sos['pp']['text'][-200:]))
    return falhas


def PROTOCOLOS_ROTEIRO(pg):
    return pg.evaluate("() => window.CapitaoDados.protocolos.roteiro")


def conta(nome, cond, extra=''):
    if cond:
        return 0
    print('FALHA', nome, extra)
    return 1


def ficha_com_clima(b):
    """A ficha da página do app de verdade: com o capitao-clima.js e a leitura do dia e a maré salvas (o bloco «## Clima e maré» inteiro), no relógio de agora. Decisão (i) do CLAUDE.md:
    passando de ~11.500 letras o teto exposto em B.FICHA_MAX é 16.000. (A página do main() não carrega o capitao-clima.js e mede menos; o grupo ficha mede os 2.454 instantes.)"""
    pg = pagina(b, clima=True)
    try:
        r = pg.evaluate("""() => { const B = window.CapitaoBrain, q = 'como se faz um nó lais de guia?', f = B.ficha('app', q, B.answer(q, { platform: 'app', commit: false }));
          return { n: f.length, max: B.FICHA_MAX, clima: f.indexOf('ECMWF via Open-Meteo, lida às') > 0 && f.indexOf('Maré agora') > 0 }; }""")
    finally:
        pg.ctx.close()
    return conta('ficha com a previsão e a maré: o bloco «Clima e maré» inteiro, entre 3.000 e B.FICHA_MAX, e a decisão (i) (16.000 se passa de ~11.500, senão 12.000)',
                 r['clima'] and 3000 <= r['n'] <= r['max'] and r['max'] == (16000 if r['n'] > 11500 else 12000) and r['n'] > 11500, r)


# Revisão da 1b: o FAQ de segurança (faq-equipamentos.json) pergunta do jeito do cartão, e o cartão tem de abrir no aparelho. O C5 só media as frases que a
# revisão lhe passou; esta percorre a `pergunta` e as `variantes` de TODOS os itens de emergência e de segurança do FAQ (cartões EM, MO-04, PO-04, EL-01,
# EL-05, SF e EP): chave de segurança (sos, epirb, seafire, salvatagem, canal16, oleo, ou um trecho `base` com seguranca) e nunca a IA (§2.3).
# Os itens de segurança de rotina (GE-01, PO-02, AI-02, CK-03, CK-05) só perguntam o que a tela do FAQ pergunta: a `pergunta` não vai à IA e não casa a lista
# SOS (PO-02 perguntava «nível normal de água no porão», frase da lista SOS, e abriria a resposta de emergência). Uma pergunta de rotina nunca é emergência.
FAQ_SEGURANCA = ('MO-04', 'PO-04', 'EL-01', 'EL-05', 'SF-01', 'SF-02', 'SF-03', 'SF-04', 'EP-01', 'EP-02', 'EP-03', 'EP-04')   # além dos `emerg` (EM-01…EM-09)
FAQ_ROTINA_SEGURA = ('GE-01', 'PO-02', 'AI-02', 'CK-03', 'CK-05')
# a `pergunta` que é emergência de propósito, fora os `emerg`: alagamento, homem ao mar, fogo no motor e a inspeção do «sistema fixo de incêndio» (a palavra
# «incêndio» é da lista SOS desde antes da 1b; a Fase 3 decide se a pergunta de inspeção abre a janela de emergência)
FAQ_PERGUNTA_EMERGENCIA = ('PO-04', 'EL-01', 'SF-01', 'SF-04')
FAQ_JS = """(qs) => { const B = window.CapitaoBrain;
  return qs.map((q) => { const a = B.answer(q, { platform: 'app', commit: false }); return { q, key: a.key, seg: !!a.seguranca, ia: B.pedeIA(a, q) }; }); }"""


def faq_de_seguranca(pg):
    falhas = 0
    faq = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'faq-equipamentos.json'), encoding='utf-8'))['itens']
    em = [i for i in faq if i.get('emerg')] + [i for i in faq if i['id'] in FAQ_SEGURANCA]
    qs = [(i['id'], q) for i in em for q in [i['pergunta']] + i.get('variantes', [])]
    r = pg.evaluate(FAQ_JS, [q for _, q in qs])
    ruins = [(iid, x['q'], x['key'], x['ia']) for (iid, _), x in zip(qs, r) if not ((x['key'] in CHAVES_LOCAIS or (x['key'] == 'base' and x['seg'])) and x['ia'] is False)]
    falhas += conta('1b (revisão): a pergunta e as variantes dos %d itens de emergência e segurança do FAQ (%d frases) abrem no aparelho: chave de segurança ou trecho com seguranca, nunca a IA'
                    % (len(em), len(qs)), len(em) >= 20 and not ruins, ruins)
    rot = [i for i in faq if i['id'] in FAQ_ROTINA_SEGURA]
    rr = pg.evaluate(FAQ_JS, [i['pergunta'] for i in rot])
    emerg = dict(pg.evaluate(EM_EMERG, [confere.pad(i['pergunta']) for i in faq]))
    ruins = [(i['id'], x['key'], x['ia']) for i, x in zip(rot, rr) if x['ia'] is not False or x['key'] in ('sos', 'oleo')]
    falhas += conta('1b (revisão): a pergunta dos itens de segurança de rotina (GE-01, PO-02, AI-02, CK-03, CK-05) fica no aparelho e não abre a resposta de emergência (sos nem óleo)', len(rot) == 5 and not ruins, ruins)
    dentro = sorted(i['id'] for i in faq if not i.get('emerg') and emerg[confere.pad(i['pergunta'])])
    falhas += conta('1b (revisão): fora os cartões `emerg`, só %s têm a `pergunta` na lista SOS (a pergunta de rotina nunca é emergência: PO-02 é «nível normal do porão»)' % ', '.join(FAQ_PERGUNTA_EMERGENCIA),
                    set(dentro) <= set(FAQ_PERGUNTA_EMERGENCIA), dentro)
    print('FAQ de segurança (pergunta e variantes no aparelho): %d falhas' % falhas)
    return falhas


# Revisão do C7 (CONTRATO §1.7, §6.2): o D.agendaFalta saiu do dado gerado e a resposta `manutencao` (que é também o bloco `## Manutenção` da
# ficha da IA) ganhou a guarda de 1 linha: sem a lista, nada de "Falta registrar: ." (sem a guarda a frase saía vazia nas duas, e a ficha ia a
# 9.420 letras). Só o rodape.py (que lê o innerText das telas) cobria as outras guardas do C7; o texto do cérebro nunca aparece nelas.
# O controle com a lista cheia prova que a guarda cala só o vazio e a frase continua quando há o que registrar.
FALTA = """() => { const B = window.CapitaoBrain, D = window.CapitaoDados, tinha = Object.prototype.hasOwnProperty.call(D, 'agendaFalta'), antigo = D.agendaFalta;
  const r = () => { const a = B.answer('próximas manutenções', { platform: 'app', commit: false }); return { key: a.key, text: a.text, ficha: B.ficha('app') }; };
  const o = { tinha };
  try {
    delete D.agendaFalta; o.gerado = r();
    D.agendaFalta = []; o.vazia = r();
    D.agendaFalta = ['Marca do guincho: SEM DADOS']; o.cheia = r();
  } finally { if (tinha) D.agendaFalta = antigo; else delete D.agendaFalta; }
  return o; }"""


def agenda_sem_falta(pg):
    falhas = 0
    x = pg.evaluate(FALTA)
    vazio = re.compile(r'Falta registrar: ?\.')
    frase = 'Falta registrar: Marca do guincho: SEM DADOS.'
    for nome, cond, extra in [
        ('revisão do C7: o dado gerado não traz o D.agendaFalta', not x['tinha'], x['tinha']),
        ('revisão do C7: sem o D.agendaFalta, a resposta de manutenção e a ficha não dizem "Falta registrar"', x['gerado']['key'] == 'manutencao'
         and 'Falta registrar' not in x['gerado']['text'] and 'Falta registrar' not in x['gerado']['ficha'], (x['gerado']['key'], x['gerado']['text'][-120:])),
        ('revisão do C7: com o D.agendaFalta vazio a guarda segue calada (nada de "Falta registrar: ." na resposta nem na ficha)',
         not vazio.search(x['vazia']['text']) and not vazio.search(x['vazia']['ficha']) and 'Falta registrar' not in x['vazia']['text'] + x['vazia']['ficha'],
         x['vazia']['text'][-120:]),
        ('revisão do C7: com algo a registrar a frase continua, na resposta e na ficha', frase in x['cheia']['text'] and frase in x['cheia']['ficha'], x['cheia']['text'][-160:]),
        ('revisão do C7: a resposta sem o D.agendaFalta é igual à com a lista vazia (a guarda não muda o resto)',
         x['gerado']['text'] == x['vazia']['text'], (len(x['gerado']['text']), len(x['vazia']['text']))),
    ]:
        if not cond:
            falhas += 1
            print('FALHA', nome, extra)
    print('agenda sem "Falta registrar" vazio: %d falhas' % falhas)
    return falhas


# Leitura salva do cabeçalho (capitao.clima.v1) como o capitao-clima.js grava: dia no fuso do barco, em = 2 h atrás. 48° = NE.
SEMEIA = """(c) => { const f = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' });
  c.dia = f.format(new Date(Date.now() + c.desloca)); delete c.desloca; c.em = Date.now() - 2 * 3600e3;
  localStorage.setItem('capitao.clima.v1', JSON.stringify(c)); window.dispatchEvent(new StorageEvent('storage', { key: 'capitao.clima.v1' }));
  return new Intl.DateTimeFormat('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(c.em)); }"""
RESPOSTAS = """() => { const B = window.CapitaoBrain, r = (q) => { const a = B.answer(q, { platform: 'app', commit: false }); return { key: a.key, text: a.text, src: a.src, voz: B.falaCurta(a), acoes: a.actions || [] }; };
  const f = B.ficha('app', 'como está o tempo?', null); const i = f.indexOf('## Clima e maré');
  return { clima: r('clima e vento'), rajada: r('vai ter rajada hoje?'), seguro: r('é seguro sair hoje?'), ficha: f, bloco: i < 0 ? '' : f.slice(i, f.indexOf('\\n## ', i + 5)) }; }"""
VENTO = 'vento até 12 nós de nordeste, rajadas até 19 nós'
# Fase 3 (P3B): o mar da previsão não é SEM DADOS na simulação (decisão 3): o app não tem previsão de ondas e diz isso, com o «confira a previsão da Marinha antes de sair»
MAR = ' · ondas: o app não tem previsão de mar — confira a previsão da Marinha antes de sair.'
# palavras de um limite de vento que o app não tem (nenhuma fonte dá um limite para "seguro para sair")
LIMITE = ('não é seguro', 'nao e seguro', 'não saia', 'acima de', 'acima do limite', 'limite de vento', 'forte demais', 'perigoso', 'evite sair', 'não recomend')


def vento_do_dia(b):
    """Previsão do cabeçalho no chat e na ficha. A página não tem o <capitao-hora-clima>: o capitao-clima.js não busca nada."""
    falhas = 0
    ctx = b.new_context()
    ctx.route('https://*.open-meteo.com/**', lambda rt: rt.abort('internetdisconnected'))
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.goto(BASE + 'base-conhecimento.json')
    for arq in ('capitao-dados.js', 'capitao-clima.js', 'capitao-brain.js'):
        pg.add_script_tag(url=BASE + arq)
    hora = pg.evaluate(SEMEIA, {'desloca': 0, 'max': 27.4, 'min': 18.2, 'vento': 12.3, 'raj': 19.4, 'dir': 48, 'modelo': 'ECMWF'})
    com = pg.evaluate(RESPOSTAS)
    fonte = 'ECMWF via Open-Meteo, lida às ' + hora
    hora_r = pg.evaluate(SEMEIA, {'desloca': 0, 'max': 27.4, 'min': 18.2, 'vento': 12.3, 'raj': 21.2, 'rajModelo': 'Open-Meteo', 'dir': 48, 'modelo': 'ECMWF'})
    raj = pg.evaluate(RESPOSTAS)
    hora_f = pg.evaluate(SEMEIA, {'desloca': 0, 'max': 27.4, 'min': 18.2, 'vento': 45, 'raj': 60, 'dir': 225, 'modelo': 'ECMWF'})  # vento forte: 225° = SW
    forte = pg.evaluate(RESPOSTAS)
    pg.evaluate(SEMEIA, {'desloca': 0, 'max': 27.4, 'min': 18.2, 'modelo': 'ECMWF'})  # leitura do dia sem o vento
    semv = pg.evaluate(RESPOSTAS)
    pg.evaluate(SEMEIA, {'desloca': 0, 'max': 27.4, 'min': 18.2, 'vento': 12.3, 'dir': 48, 'modelo': 'ECMWF'})  # leitura do dia sem a rajada (nem do melhor modelo)
    semr = pg.evaluate(RESPOSTAS)
    pg.evaluate("() => { window.CapitaoDados.simulacao = false; }")   # decisão 6: com simulacao false a regra «Nada inventado» volta, e o que a leitura não traz é SEM DADOS
    semr_real = pg.evaluate(RESPOSTAS)
    pg.evaluate(SEMEIA, {'desloca': 0, 'max': 27.4, 'min': 18.2, 'modelo': 'ECMWF'})
    semv_real = pg.evaluate(RESPOSTAS)
    pg.evaluate("() => { window.CapitaoDados.simulacao = true; }")
    hora_s = pg.evaluate(SEMEIA, {'desloca': -86400e3, 'max': 30, 'min': 20, 'vento': 25, 'raj': 33, 'dir': 180, 'modelo': 'ECMWF'})  # só a de ontem
    sem = pg.evaluate(RESPOSTAS)
    windy = [x for x in com['clima']['acoes'] if x.get('ext') and x.get('href', '').startswith('https://www.windy.com/')]
    linha1 = lambda r: r['text'].split('\n')[0]
    tudo = lambda r: [r['clima']['text'], r['clima']['src'], r['clima']['voz'], r['seguro']['text'], r['seguro']['src'], r['seguro']['voz'], r['bloco']]   # texto, fonte, fala e ficha
    for nome, cond, extra in [
        ('clima com a previsão: 1ª linha (a falada) com máx/mín, vento, rajada, direção, fonte e hora', linha1(com['clima']).startswith('Hoje em Balneário Camboriú: máx 27° · mín 18° · ' + VENTO) and fonte in linha1(com['clima']) and VENTO in com['clima']['voz'], linha1(com['clima'])),
        ('clima: fonte com o modelo e a hora da leitura; toque abre o windy.com (nova aba)', ('previsão ' + fonte) in com['clima']['src'] and len(windy) == 1, (com['clima']['src'], com['clima']['acoes'])),
        ('"vai ter rajada hoje?" responde com a rajada prevista', com['rajada']['key'] == 'clima' and 'rajadas até 19 nós' in com['rajada']['text'], com['rajada']['key']),
        ('seguro para sair: vento previsto com fonte e hora, ondas sem previsão no app + "confira a previsão da Marinha antes de sair"', (VENTO + MAR) in com['seguro']['text'] and fonte in com['seguro']['text'] and ('previsão ' + fonte) in com['seguro']['src'], com['seguro']['text'][-260:]),
        ('seguro para sair: o vento previsto não muda a decisão (sem limite de vento inventado)', linha1(com['seguro']) == linha1(sem['seguro']), (linha1(com['seguro']), linha1(sem['seguro']))),
        ('seguro para sair com vento forte (45/60 kn): a previsão aparece com a fonte, a decisão não muda e nenhum limite é inventado', ('vento até 45 nós de sudoeste, rajadas até 60 nós' + MAR) in forte['seguro']['text'] and ('lida às ' + hora_f) in forte['seguro']['text'] and linha1(forte['seguro']) == linha1(sem['seguro']) and linha1(forte['seguro']).startswith('Sim, com ') and not [x for x in LIMITE if x in forte['seguro']['text'].lower()], (linha1(forte['seguro']), [x for x in LIMITE if x in forte['seguro']['text'].lower()])),
        # Fase 3 (revisão da P3B; PROMPT §3, decisão 3): com simulacao true a leitura do dia que vem sem o vento ou sem a rajada (o Open-Meteo não trouxe) não escreve SEM DADOS no
        # clima, no seguro para sair, na fala nem na ficha da IA: só não diz o que a leitura não tem. Nada inventado: nenhum vento nem rajada que a leitura não traga.
        ('leitura do dia sem o vento: seguro com «sem previsão de vento nesta leitura» (nada inventado, sem SEM DADOS) e ondas sem previsão no app', ('sem previsão de vento nesta leitura' + MAR) in semv['seguro']['text'] and 'vento até' not in semv['seguro']['text'] and linha1(semv['seguro']) == linha1(sem['seguro']), semv['seguro']['text'][-200:]),
        ('leitura do dia sem o vento: clima, seguro, ficha e fala (simulacao true) não casam ROTULOS nem VAZIOS e não inventam vento', not [n for n in ('ROTULOS', 'VAZIOS') for t in tudo(semv) if RX[n].search(t)] and 'sem previsão de vento nesta leitura' in semv['clima']['text'] and 'sem previsão de vento nesta leitura' in semv['bloco'] and all('vento até' not in t and 'rajadas até' not in t for t in tudo(semv)), (semv['clima']['text'][:200], semv['bloco'][:200])),
        ('leitura do dia sem a rajada: o vento sem «rajadas» (clima, seguro, ficha e fala), sem SEM DADOS e sem rajada inventada', not [n for n in ('ROTULOS', 'VAZIOS') for t in tudo(semr) if RX[n].search(t)] and 'rajada' not in ' '.join(tudo(semr)).lower() and linha1(semr['clima']).startswith('Hoje em Balneário Camboriú: máx 27° · mín 18° · vento até 12 nós de nordeste (previsão ') and ('vento até 12 nós de nordeste' + MAR) in semr['seguro']['text'] and 'vento até 12 nós de nordeste' in semr['clima']['voz'], (linha1(semr['clima']), semr['seguro']['text'][-200:])),
        # com simulacao false volta a regra «Nada inventado» (decisão 6): o que a leitura não traz é SEM DADOS
        ('simulacao false, leitura do dia sem o vento: vento SEM DADOS no clima, no seguro e na ficha (a regra «Nada inventado» volta)', 'vento SEM DADOS' in linha1(semv_real['clima']) and ('vento SEM DADOS' + ' · mar (ondas): SEM DADOS no app') in semv_real['seguro']['text'] and 'vento SEM DADOS' in semv_real['bloco'] and 'sem previsão de vento nesta leitura' not in semv_real['clima']['text'] + semv_real['seguro']['text'], (linha1(semv_real['clima']), semv_real['seguro']['text'][-200:])),
        ('simulacao false, leitura do dia sem a rajada: «rajadas SEM DADOS» no clima, no seguro e na ficha', 'vento até 12 nós de nordeste, rajadas SEM DADOS' in linha1(semr_real['clima']) and 'vento até 12 nós de nordeste, rajadas SEM DADOS' in semr_real['seguro']['text'] and 'rajadas SEM DADOS' in semr_real['bloco'], (linha1(semr_real['clima']), semr_real['seguro']['text'][-200:])),
        ('ficha da IA: vento previsto com fonte e hora, sem limite inventado e sem coordenadas', VENTO in com['bloco'] and fonte in com['bloco'] and 'não tem limite de vento' in com['bloco'] and not confere.R_COORD.search(com['ficha']) and 'windy.com/' not in com['ficha'], com['bloco'][:300]),
        ('rajada que o ECMWF não trouxe: vem do melhor modelo do Open-Meteo, dito na resposta', 'rajadas até 21 nós (rajada do melhor modelo do Open-Meteo; o ECMWF não trouxe)' in raj['clima']['text'] and ('lida às ' + hora_r) in raj['clima']['text'], linha1(raj['clima'])),
        # Fase 3 (P3B, §2.5): sem a leitura de hoje, a frase do §2.5 com a hora da última leitura salva (a de ontem) no lugar do SEM DADOS
        ('só a leitura de ontem: clima, seguro e ficha com a frase do §2.5 («última às HH:MM») e nenhum vento previsto', all('vento até' not in x and 'rajadas até' not in x for x in (sem['clima']['text'], sem['seguro']['text'], sem['bloco'])) and linha1(sem['clima']) == 'Previsão e maré: sem conexão agora (última às ' + hora_s + ') — confira o boletim da Marinha antes de sair.' and 'Previsão e maré: sem conexão agora (última às ' + hora_s + ') — confira o boletim da Marinha antes de sair.' in sem['seguro']['text'] and 'Previsão e maré: sem conexão agora' in sem['bloco'] and 'SEM DADOS' not in sem['clima']['text'] + sem['seguro']['text'] + sem['bloco'] and not sem['clima']['acoes'][1:], (linha1(sem['clima']), sem['bloco'][:160])),
        ('previsão sem erro de script', not erros, erros),
    ]:
        if not cond:
            falhas += 1
            print('FALHA', nome, extra)
    print('vento do dia: %d falhas' % falhas)
    if '-v' in sys.argv:
        print('\n## clima\n' + com['clima']['text'] + '\n' + com['clima']['src'] + '\n## seguro\n' + com['seguro']['text'] + '\n' + com['seguro']['src'] + '\n' + com['bloco'])
    ctx.close()
    return falhas


# Revisão do C7 (CONTRATO §1.4, §1.8): o botão "Perguntar sobre: <documento>" da G1 (G1-Documentos-Web.dc.html:263 e Mobile:209) pergunta
# 'Situação e vencimento do documento: ' + o nome. O C7 criou o doc-epirb ("Certificado do EPIRB (bateria e disparador hidrostático)") e a pergunta
# dele ia para a rota `epirb`. Hoje isso mostrava a resposta velha do EPIRB (SEM DADOS) em vez do status do documento; na Fase 3 as chaves `sos`,
# `oleo`, `canal16`, `epirb` e `seafire` ligam o `emergenciaAte` (conversa em emergência por 15 min, IA desligada, posição trocada): um toque na
# papelada abriria o modo emergência. Regra do contrato (§1.4): nenhuma pergunta de botão cai numa chave de emergência. Aqui: a pergunta de CADA
# documento do D, escrita como a G1 a escreve, dá `docsvenc` e não vai à IA. Ficam para a 1b o filtro do `docsvenc` (a nota da etiqueta no lugar
# da data do doc-epirb, §6.6) e o teste de que a resposta não liga o `emergenciaAte` (a marca não existe antes da Fase 3).
EMERGENCIA = ('sos', 'oleo', 'canal16', 'epirb', 'seafire')
G1_PERGUNTAS = """() => { const B = window.CapitaoBrain, D = window.CapitaoDados;
  return D.documentos.map((x) => { const q = 'Situação e vencimento do documento: ' + x.n, a = B.answer(q, { platform: 'app', commit: false });
    return { id: x.id, q, key: a.key, ia: B.pedeIA(a, q), src: a.src, tela: B.answer(q, { platform: 'web', commit: false }).key }; }); }"""


# C8 (CONTRATO §1.10, §6.2): o arquivo gerado leva `abastecimentos: []` e a microtarefa do rodapé insere ab-0…ab-2 só com simulacao: true.
# Com `simulacao = false` acrescentado ao fim do capitao-dados.js (a injeção do teste do modo real), nenhuma linha do dia de bordo entra, nenhuma
# nota fiscal do abastecimento aparece e o `consumo` do cérebro (e o `## Autonomia e consumo` da ficha) não escrevem «Abastecimentos registrados: .».
def acrescenta(extra):
    """Handler do page.route que entrega o capitao-dados.js com `extra` no fim (a injeção do teste do modo real)."""
    def entrega(route):
        r = route.fetch()
        route.fulfill(response=r, body=r.text() + extra)
    return entrega


def consumo_sem_abastecimentos(b):
    falhas = 0
    achados = {}
    for modo, extra in (('simulacao true', ''), ('simulacao false injetado', ';window.CapitaoDados.simulacao = false;')):
        pg = b.new_page()
        pg.route('**/capitao-dados.js', acrescenta(extra))
        pg.goto(BASE + 'base-conhecimento.json')
        pg.add_script_tag(url=BASE + 'capitao-dados.js')
        pg.add_script_tag(url=BASE + 'capitao-brain.js')
        pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); })")
        achados[modo] = pg.evaluate("""() => { localStorage.clear(); const B = window.CapitaoBrain, D = window.CapitaoDados, a = B.answer('consumo de diesel', { platform: 'app', commit: false }),
          f = B.ficha('app');
          return { key: a.key, text: a.text, src: a.src, ab: D.abastecimentos.length, nf: D.documentos.filter((x) => x.id === 'nf-abast').length,
                   ids: D.diario.slice(0, 2).map((x) => x.id), bloco: f.slice(f.indexOf('## Autonomia e consumo'), f.indexOf('## Documentos')), docs: D.documentos.length }; }""")
        pg.close()
    sim, real = achados['simulacao true'], achados['simulacao false injetado']
    for nome, cond, extra in [
        ('C8: com simulacao true entram as 3 linhas de abastecimento do dia de bordo, a nota fiscal, e d01 e d02 no topo do diário',
         sim['ab'] == 3 and sim['nf'] == 1 and sim['ids'] == ['d01', 'd02'] and sim['docs'] == 8, sim),
        ('C8: com simulacao true a resposta `consumo` e a ficha listam os 3 abastecimentos (1.086 L cada) e a fonte do guia §10',
         sim['key'] == 'consumo' and sim['text'].count('1.086 L') == 3 and 'Abastecimentos registrados: ' in sim['text'] and 'Guia de bordo — Motores Cummins §10 · Consumo' in sim['src']
         and sim['bloco'].count('1.086 L') == 3, (sim['text'][-200:], sim['src'])),
        ('C8: com simulacao = false injetado, nenhuma linha de abastecimento, nenhuma nota fiscal e o diário começa na d03',
         real['ab'] == 0 and real['nf'] == 0 and real['ids'][0] == 'd03' and real['docs'] == 7, real),
        ('C8: com simulacao = false, o `consumo` e a ficha não escrevem «Abastecimentos registrados: .» (a guarda do cérebro) e o resto da resposta fica igual',
         real['key'] == 'consumo' and 'Abastecimentos registrados' not in real['text'] and 'Abastecimentos registrados' not in real['bloco'] and not re.search(r'\.\s*\.', real['text'])
         and real['text'] == sim['text'].split('\nAbastecimentos registrados')[0], (real['text'][-200:], real['bloco'][-200:])),
    ]:
        if not cond:
            falhas += 1
            print('FALHA', nome, extra)
    print('consumo sem abastecimentos (simulacao false): %d falhas' % falhas)
    return falhas


def perguntas_da_g1(pg):
    falhas = 0
    r = pg.evaluate(G1_PERGUNTAS)
    ruins = [(x['id'], x['key'], x['tela']) for x in r if x['key'] != 'docsvenc' or x['tela'] != 'docsvenc']
    em_emergencia = [x['id'] for x in r if x['key'] in EMERGENCIA]
    for nome, cond, extra in [
        ('revisão do C7: o D tem os documentos da G1 (pelo menos 7, com o doc-epirb)', len(r) >= 7 and 'doc-epirb' in [x['id'] for x in r], [x['id'] for x in r]),
        ('revisão do C7: "Situação e vencimento do documento: <nome>" de cada documento da G1 dá docsvenc (app e web)', not ruins, ruins),
        ('revisão do C7: nenhuma pergunta da G1 cai numa chave que liga a conversa em emergência (sos, oleo, canal16, epirb, seafire)', not em_emergencia, em_emergencia),
        ('revisão do C7: a pergunta da G1 não vai à IA e traz a fonte', all(x['ia'] is False and (x['src'] or '').startswith('Fonte') for x in r),
         [(x['id'], x['ia'], x['src']) for x in r if x['ia'] is not False or not (x['src'] or '').startswith('Fonte')]),
    ]:
        if not cond:
            falhas += 1
            print('FALHA', nome, extra)
    print('perguntas da G1 (documentos): %d falhas' % falhas)
    return falhas


# ——————————————— Fase 3, P3A: o instante do cérebro ———————————————
# (PROMPT Fase 3 «Instante»; CONTRATO §1.23 instante(), §1.24 «Cérebro (Fase 3)», §6.5 «Um instante só» e «Tendência», §6.6 último ponto)
# Um instante por pergunta: B.instante() é o objeto do §1.23 (CapitaoAgora.instante() mais `tend` e `txt`), congelado no começo de answer, ficha,
# answerAttachment, resumoAgora e addDiario e solto num finally. A resposta local, a ficha e o contexto que vai à IA (resumoAgora(a)) enxergam o MESMO
# instante; duas perguntas seguidas em segundos diferentes veem instantes diferentes; em /SOS-/ não há instante (nem o resumo); com simulacao false
# (ou sem replay) o cérebro é o de antes da 1.1.0 (D.snapshot, fonte «snapshot»). A fonte de uma resposta com quadro do replay é a `fonteTxt` do
# instante, nunca «coletor NMEA».
# uma pergunta de cada chave do PROMPT §2.2 (sos, canal16, epirb, seafire, salvatagem, o MMSI, que tem a rota `mmsi` desde a P3C, e o `oleo`: queda ou alarme), tirada dos CASOS
PERGUNTAS_2_2 = ['MAYDAY, homem ao mar!', 'roteiro do canal 16', 'onde fica o EPIRB?', 'onde fica o seafire', 'jogue a boia na água', 'qual o MMSI do barco?',
                'alarme de óleo acendeu', 'pressão de óleo baixa no motor BB']   # (as duas últimas: `oleo`, relato de falha sem leitura do quadro, PROMPT §2.2)
CHAVES_2_2 = ['sos', 'canal16', 'epirb', 'seafire', 'salvatagem', 'mmsi', 'oleo', 'oleo']   # a chave de cada pergunta acima (P3C: o MMSI tem a rota `mmsi`; antes respondia na canal16)
CHAVES_EMERGENCIA = ('sos', 'oleo', 'canal16', 'epirb', 'seafire', 'salvatagem', 'mmsi')   # as chaves cuja resposta não leva o instante (CLAUDE.md 10; PROMPT §2.2, §2.3)
CHAVES_INSTANTE = ('ms', 'q', 'fonte', 'fonteTxt', 'selo', 'hora', 'hhmm', 'seg', 'fase', 'calc', 'tend', 'txt')
CHAVES_TXT = ('hora', 'sog', 'stw', 'rumo', 'proa', 'piloto', 'leme', 'prof', 'rpm', 'oleo', 'arref', 'carga', 'consumo', 'diesel', 'dieselLados', 'distancia',
              'horimetros', 'gerador', 'seakeeper', 'b24', 'b12', 'tanques', 'porao', 'ancora', 'vento', 'ventoAp', 'ondas', 'pressao', 'ar', 'agua', 'praca',
              'inclinacao', 'local', 'destino', 'wp', 'eta', 'alarmes', 'relativa', 'autonomia', 'desdeAbast', 'tend', 'resumo', 'resumoSemPosicao')
# a tendência dos últimos 30 s (§1.23): 12:01:00 e 12:01:45 (fixar('60') e fixar('105'))
TEND_60 = {'motor_bb_rpm': 644, 'motor_be_rpm': 648, 'motor_bb_oleo_bar': 0.5, 'motor_be_oleo_bar': 0.5, 'motor_bb_arref_c': 2.9, 'motor_be_arref_c': 2.8, 'sog_nos': 8.1, 'diesel_litros': -0.5}
TEND_105 = {'motor_bb_rpm': -4, 'motor_be_rpm': -8, 'motor_bb_oleo_bar': 0, 'motor_be_oleo_bar': 0, 'motor_bb_arref_c': 0, 'motor_be_arref_c': 7.5, 'sog_nos': 0, 'diesel_litros': -0.6}
TXT_TEND_60 = 'últimos 30 s: rpm BB +644 · BE +648 · óleo +0,5 / +0,5 bar · arrefecimento +2,9 / +2,8 °C · SOG +8,1 nós · diesel −0,5 L'
TXT_TEND_105 = 'últimos 30 s: rpm BB −4 · BE −8 · óleo 0,0 / 0,0 bar · arrefecimento 0,0 / +7,5 °C · SOG 0,0 nós · diesel −0,6 L'
# as fontes de leitura que o SOS tem de recusar (as mesmas do testes/rodape.py): um replay, um coletor e um D.snapshot.quadro à mão
LEITURA_SOS = "{ timestamp_utc: '2026-10-27T15:01:00Z', lat: -26.99, lon: -48.61, sog_nos: 18.1, diesel_litros: 1333, temp_ar_externo_c: 22.6, temp_agua_c: 20.1, estado: 'Navegando' }"
FONTES_SOS = {
    'replay': ";window.CapitaoReplay = { agora: function () { return Date.now(); }, em: function () { return %s; }, t: function () { return 60; }, fase: function () { return { nome: 'cruzeiro', ini: 50, fim: 120 }; }, fixo: function () { return ''; } };" % LEITURA_SOS,
    'coletor': ";window.CapitaoTelemetria = { atual: function () { return %s; } };" % LEITURA_SOS,
    'reserva': ";window.CapitaoDados.snapshot.quadro = %s;" % LEITURA_SOS,
}
# as chaves do D que o SOS nunca lê (CONTRATO §6.5, último ponto do SOS): cada uma vira um getter que conta, instalado depois da fonte de leitura e antes do cérebro
LEIDAS_SOS = ('simulacao', 'replay', 'snapshot', 'rota', 'campos')
GETTERS_SOS = """window.__lidas = {}; (function () { var D = window.CapitaoDados; %s.forEach(function (k) { if (!(k in D)) return; var v = D[k]; window.__lidas[k] = 0;
  Object.defineProperty(D, k, { get: function () { window.__lidas[k]++; return v; }, set: function (x) { v = x; }, configurable: true, enumerable: true }); }); })();""" % json.dumps(list(LEIDAS_SOS))
INSTANTES_RESUMO = ('0@0', '10@0', '20@0', '29@0', '60', '105', '120', '149@575')
SEM_SIMULACAO = ';window.CapitaoDados.simulacao = false;'
# o relógio da página parado em `ms` (Date.now e new Date() sem argumento). O `## Agora` da ficha da reserva (simulacao false ou sem replay) usa o minuto do relógio, e duas
# páginas de uma comparação passam pelo virar do minuto de vez em quando (≈ 0,5 % de cada par): o teste do modo real as para DE PROPÓSITO em minutos diferentes
# (18:09:59,9 e 18:10:00,1 de 02/11/2026 em Brasília), e a comparação tira o bloco do relógio
VIRADA_DO_MINUTO = 1793653799900
RELOGIO = """;(function () { var RD = Date, T = %d; function FD() { var a = [].slice.call(arguments); if (!(this instanceof FD)) return new RD(T).toString();
  return a.length ? new (Function.prototype.bind.apply(RD, [null].concat(a)))() : new RD(T); }
  FD.prototype = RD.prototype; FD.now = function () { return T; }; FD.UTC = RD.UTC; FD.parse = RD.parse; window.Date = FD; })();"""


def relogio(ms):
    return RELOGIO % ms


def sem_agora(ficha):
    """(ficha sem o bloco «## Agora», o bloco): o relógio da ficha é do aparelho e muda entre duas páginas; o resto é o que se compara."""
    m = re.search(r'## Agora\n(.*?)\n\n', ficha, re.S)
    return (ficha.replace(m.group(0), '', 1) if m else ficha), (m.group(1) if m else None)


def agora_ok(bloco):
    return bool(bloco) and re.search(r'\d\d/\d\d/\d{4}, \d\d:\d\d \(horário de Brasília\)', bloco) is not None
HTML_SOS = '<!doctype html><meta charset="utf-8"><title>SOS</title>'


# a ordem do <head> da Main e da H2 (o capitao-alertas.js entra entre o replay e a telemetria); SEM_ALERTAS prova o ramo de reserva do cérebro (tela sem o script)
SCRIPTS = ('capitao-dados.js', 'capitao-replay.js', 'capitao-alertas.js', 'capitao-telemetria.js', 'capitao-brain.js')
SCRIPTS_SEM_ALERTAS = ('capitao-dados.js', 'capitao-replay.js', 'capitao-telemetria.js', 'capitao-brain.js')


# A leitura do dia e a maré que o capitao-clima.js grava no app de verdade (capitao.clima.v1 e capitao.mare.v1), plantadas ANTES do script dele: a ficha da IA fica com o bloco «## Clima e maré»
# inteiro (e não com a frase curta «sem conexão» que a página sem ele diz). Mesma forma do SEMEIA (dia no fuso do barco, `em` 2 h atrás, 48° = NE) e a série horária de 48 pontos.
SEMENTE_CLIMA = """
;(function () { try { var f = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' }), t0 = Math.floor(Date.now() / 3600e3) * 3600e3 - 6 * 3600e3, serie = [], k;
  for (k = 0; k < 48; k++) serie.push([t0 + k * 3600e3, Math.round(40 * Math.sin(k / 2)) / 100]);
  localStorage.setItem('capitao.clima.v1', JSON.stringify({ dia: f.format(new Date()), em: Date.now() - 2 * 3600e3, max: 27.4, min: 18.2, vento: 12.3, raj: 21.2, dir: 48, modelo: 'ECMWF' }));
  localStorage.setItem('capitao.mare.v1', JSON.stringify({ em: Date.now() - 3600e3, serie: serie })); } catch (e) {} })();
"""


def pagina(b, extra='', scripts=SCRIPTS, caminho='base-conhecimento.json', fixo='60', muta=None, relogio_ms=None, clima=False, aborta=()):
    """Página da Main e da H2 (dados, replay, alertas, telemetria, cérebro) com o instante fixado em `fixo`. `extra` é acrescentado ao fim do capitao-dados.js (a
    injeção do teste do modo real e as fontes de leitura do SOS). `muta` = (trecho, troca): o cérebro mutante dos testes que provam que a conferência
    acusa. Em `caminho` com /SOS-/ a página é vazia e o replay de verdade sai sozinho. `relogio_ms`: o relógio do aparelho parado nesse instante ANTES de qualquer
    script (o rodapé do capitao-dados.js já refaz os prazos nele). `clima`: a página da Main e da H2 de verdade, com o capitao-clima.js e a leitura do dia e a maré salvas
    (a rede do Open-Meteo fica fora: a leitura é a plantada)."""
    if clima:
        extra = extra + SEMENTE_CLIMA
        scripts = tuple(a for a in scripts if a != 'capitao-clima.js')
        k = scripts.index('capitao-brain.js') if 'capitao-brain.js' in scripts else len(scripts)
        scripts = scripts[:k] + ('capitao-clima.js',) + scripts[k:]
    ctx = b.new_context(service_workers='block')
    for padrao in aborta:   # arquivos que a página nem chega a pedir (a rede cortada ANTES do cérebro carregar): `aborta=('**/faq-equipamentos.json',)`
        ctx.route(padrao, lambda rt: rt.abort('internetdisconnected'))
    if clima:
        ctx.route('https://*.open-meteo.com/**', lambda rt: rt.abort('internetdisconnected'))
    ctx.route('**/capitao-dados.js', acrescenta(extra))
    if caminho.endswith('.html'):
        ctx.route('**/' + caminho, lambda rt: rt.fulfill(body=HTML_SOS, content_type='text/html; charset=utf-8'))
    if muta:
        def entrega(route):
            r = route.fetch()
            corpo = r.text()
            assert corpo.count(muta[0]) == 1, 'o trecho do mutante não está (uma vez) no cérebro: ' + muta[0]
            route.fulfill(response=r, body=corpo.replace(muta[0], muta[1], 1))
        ctx.route('**/capitao-brain.js', entrega)
    pg = ctx.new_page()
    pg.erros = []
    pg.on('pageerror', lambda e: pg.erros.append(str(e)))
    pg.goto(BASE + caminho)
    if relogio_ms is not None:
        pg.add_script_tag(content=relogio(relogio_ms))
    for arq in scripts:
        if arq == 'capitao-brain.js' and fixo is not None:
            pg.evaluate("(x) => { if (window.CapitaoReplay) window.CapitaoReplay.fixar(x); }", fixo)
        pg.add_script_tag(url=BASE + arq)
    pg.ctx = ctx
    return pg


# B.instante() nos dois instantes do contrato (§1.22, §1.23): o objeto, o texto único (rpm, sog, diesel), a tendência
JS_FORMA = """([qs, fontes]) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, out = {};
  const forma = (x) => { R.fixar(x); const i = B.instante(); return i && { chaves: Object.keys(i), fonte: i.fonte, hora: i.hora, hhmm: i.hhmm, seg: i.seg, fase: i.fase && i.fase.nome,
    fonteTxt: i.fonteTxt, selo: i.selo, tend: i.tend, txt: i.txt, rpm: i.q.motor_bb_rpm, ms: i.ms }; };
  out.a60 = forma('60'); out.a105 = forma('105');
  const op = { platform: 'app', commit: false };
  out.aut105 = B.answer('autonomia', op).text; out.con105 = B.answer('consumo de diesel', op).text; R.fixar('60');
  out.horimetros = B.answer('horímetros', op).text; out.autonomia = B.answer('autonomia', op).text; out.gerador = B.answer('quantas horas tem o gerador', op).text;
  out.manutencao = B.answer('próximas manutenções', op).text; out.tanques = B.answer('nível dos tanques', op).text; out.consumo = B.answer('consumo de diesel', op).text;
  out.emerg = qs.map((q) => { const a = B.answer(q, op); return [q, a.key, a.src, a.text, B.falaCurta(a)]; });
  out.fontes = fontes.map((q) => [q, B.answer(q, op).src]);
  return out; }"""

# um instante por pergunta: quantas leituras do CapitaoAgora cada chamada externa faz, o relógio que anda no meio (a ficha e o contexto da MESMA pergunta
# ficam no instante dela, a pergunta seguinte lê outro), a exceção que solta o instante e o '## Agora' no mesmo instante da telemetria
JS_UMA = """() => { const B = window.CapitaoBrain, R = window.CapitaoReplay, A = window.CapitaoAgora, out = {};
  let n = 0; const orig = A.instante; A.instante = function () { n++; return orig.apply(this, arguments); };
  const c = (f) => { n = 0; const r = f(); return [n, r]; };
  const op = { platform: 'app', commit: false };
  R.fixar('60');
  const [nA, a] = c(() => B.answer('é seguro sair hoje?', op)), [nF, f] = c(() => B.ficha('app', 'telemetria', null)), [nR, r] = c(() => B.resumoAgora());
  const [nX, x] = c(() => B.answerAttachment('foto', { name: 'a.jpg', size: 2048 }, op)), [nI, i] = c(() => B.instante());
  out.leituras = { answer: nA, ficha: nF, resumo: nR, anexo: nX, instante: nI };
  const a1 = B.answer('telemetria', op), v1 = B.answer('nível dos tanques', op);
  R.fixar('0@121');                                   // 12:02:30: o relógio andou depois da resposta
  const [nF2, f2] = c(() => B.ficha('app', 'telemetria', a1)), [nR2, r2] = c(() => B.resumoAgora(a1));
  const a2 = B.answer('telemetria', op), f3 = B.ficha('app', 'telemetria', a2), r3 = B.resumoAgora();
  const bloco = (f) => f.slice(f.indexOf('## Telemetria'), f.indexOf('## Manutenção')), agora = (f) => f.slice(f.indexOf('## Agora'), f.indexOf('\\n\\n## ', f.indexOf('## Agora')));   // (P3D: só o bloco «## Agora»; o «## Navegação agora» e a emergência vêm depois dele e antes do «## Sobre o app»)
  out.mesmo = { vivo: v1.src, a1: a1.src, f2: bloco(f2), g2: agora(f2), r2, nF2, nR2, a2: a2.src, f3: bloco(f3), g3: agora(f3), r3 };
  R.fixar('60'); const x1 = B.answerAttachment('foto', { name: 'b.jpg', size: 1024 }, op); R.fixar('0@121');   // o anexo leva o instante dele, como a resposta
  const [nFx, fx] = c(() => B.ficha('app', 'telemetria', x1));
  out.anexo = { n: nFx, b: bloco(fx), g: agora(fx) };
  let lancou = false; R.fixar('60');
  try { B.answer('x', { get platform() { throw new Error('x'); } }); } catch (e) { lancou = true; }
  const b1 = B.answer('telemetria', op); R.fixar('0@121'); const b2 = B.answer('telemetria', op); R.fixar('60');
  out.solta = { lancou, b1: b1.src, b2: b2.src, depois: B.instante().hora };
  A.instante = orig; return out; }"""

# o resumo do diário e do contexto: ≤ 300 letras e sem coordenadas em vários instantes (a virada das 07:00 e a janela do AVISO incluídas)
JS_RESUMO = """(xs) => { const B = window.CapitaoBrain, R = window.CapitaoReplay;
  return xs.map((x) => { R.fixar(x); const i = B.instante(); return { x, hora: i.hora, local: i.q.local, resumo: B.resumoAgora(), sem: B.resumoAgora({ semPosicao: true }), lat: i.q.lat, lon: i.q.lon }; }); }"""

# a virada das 07:00: a tendência perde o diesel nos 30 s depois da âncora (o abastecimento atravessa a janela) e nada quebra, em 07:00:10, 06:59:59 e nos dois lados da fronteira
JS_VIRADA = """(xs) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false };
  return xs.map((x) => { R.fixar(x); const i = B.instante(), t = ['telemetria', 'autonomia', 'horímetros', 'consumo de diesel', 'posição agora', 'é seguro sair hoje?', 'tanques']
      .map((q) => B.answer(q, op).text).concat(B.ficha('app'), B.resumoAgora(), Object.keys(i.txt).map((k) => String(i.txt[k])));
    return { x, hora: i.hora, tend: i.tend, txtTend: i.txt.tend, texto: t.join('\\n') }; }); }"""

# o SOS: sem instante em nenhuma das três fontes (replay, coletor, D.snapshot.quadro à mão); o resumo é o plotter; a linha do SOS não leva quadro
JS_SOS = """(qs) => { const B = window.CapitaoBrain, D = window.CapitaoDados, A = window.CapitaoAgora;
  const e = B.addDiario({ t: 'MAYDAY teste', src: 'web · SOS · MAYDAY' }), op = { platform: 'app', commit: false };
  const todas = qs.map((q) => { const a = B.answer(q, op); return a.text + '\\n' + a.src + '\\n' + B.falaCurta(a); });   // UMA pergunta de CADA chave de ANSWERS na página do SOS (revisão da P3B: oleoLeitura, porão e destinos liam D.replay e D.rota)
  const r = { b: B.instante(), a: A.instante(), resumo: B.resumoAgora(), sem: B.resumoAgora({ semPosicao: true }), plotter: D.protocolos.plotter, entrada: e, guardada: B.loadDiario()[0], n: qs.length,
              texto: [B.answer('telemetria', op).text, B.answer('posição agora', op).text, B.answer('é seguro sair hoje?', op).text, B.ficha('app'), B.ficha('app', 'telemetria', B.answer('telemetria', op))].concat(todas).join('\\n') };
  r.lidas = Object.assign({}, window.__lidas); return r; }"""

# modo real: as respostas de TODAS as perguntas, a ficha e o instante (comparados com a página sem replay, igual a antes da 1.1.0)
JS_REAL = """(casos) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, i = B.instante();
  return { respostas: casos.map(([q]) => { const a = B.answer(q, { platform: 'app', commit: false }); return [q, a.key, a.text, a.src, B.falaCurta(a)]; }),
           ficha: B.ficha('app'), resumo: B.resumoAgora(), sem: B.resumoAgora({ semPosicao: true }), estado: B.DADOS.snapshot.estado, local: B.DADOS.snapshot.local,
           fonte: i && i.fonte, tend: i && i.tend, txt: i && !!i.txt, replayAtivo: !!(R && R.ativo()) }; }"""


def confere_instante(b, muta=None, grupos=('forma', 'uma', 'resumo', 'virada', 'sos', 'real', 'alarmes', 'aninhadas', 'transicao', 'coletor', 'falha', 'parcial', 'numeros', 'ligados', 'coordenada', 'marca', 'emerg',
                                                    'rotulos', 'modos', 'prazos', 'tempo', 'textos', 'estados', 'rotas', 'p3c', 'p3c_dados', 'ficha', 'semcoord', 'termos', 'voz', 'preditiva', 'pecas', 'checklist', 'faq', 'cabecas', 'rev5', 'p3f_registro', 'p3f_tickets')):
    """Devolve a lista dos problemas do instante do cérebro (vazia = tudo certo). Com `muta`, o cérebro é o mutante: a lista tem de vir NÃO vazia."""
    ruins = []
    ped = lambda nome, ok, extra='': ruins.append('%s %s' % (nome, str(extra)[:300])) if not ok else None
    for g in grupos:
        try:
            GRUPOS_3A[g](b, muta, ped)
        except Exception as e:   # um erro do navegador (B.instante inexistente, script quebrado) é problema, não queda do teste
            ruins.append('%s: %s' % (g, str(e).strip().split('\n')[0][:200]))
    return ruins


def grupo_forma(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        f = pg.evaluate(JS_FORMA, [PERGUNTAS_2_2, FONTE_DO_INSTANTE])
        for rot, i, tend, txt_tend, hora, seg in (('12:01:00', f['a60'], TEND_60, TXT_TEND_60, '12:01:00', 60), ('12:01:45', f['a105'], TEND_105, TXT_TEND_105, '12:01:45', 105)):
            if not i:
                ped('forma %s: B.instante() nulo' % rot, False)
                continue
            ped('forma %s: chaves do §1.23' % rot, set(CHAVES_INSTANTE) <= set(i['chaves']), sorted(set(CHAVES_INSTANTE) - set(i['chaves'])))
            ped('forma %s: fonte replay, hora, segundo e fase' % rot, i['fonte'] == 'replay' and i['hora'] == hora and i['seg'] == seg and i['fase'] == 'cruzeiro', (i['fonte'], i['hora'], i['seg'], i['fase']))
            ped('forma %s: fonteTxt «telemetria ao vivo · hora» e selo AO VIVO, sem coletor NMEA' % rot, i['fonteTxt'] == 'telemetria ao vivo · ' + hora and i['selo']['texto'] == 'AO VIVO · ' + hora and 'coletor' not in i['fonteTxt'], (i['fonteTxt'], i['selo']))
            ped('forma %s: tendência dos últimos 30 s (§1.23)' % rot, i['tend'] == tend, i['tend'])
            ped('forma %s: txt.tend' % rot, i['txt'] and i['txt']['tend'] == txt_tend, i['txt'] and i['txt']['tend'])
            ped('forma %s: txt com as 43 chaves do §1.23, todas texto não vazio, sem NaN, undefined nem null' % rot,
                i['txt'] and all(isinstance(i['txt'].get(k), str) and i['txt'][k].strip() and not re.search(r'NaN|undefined|null', i['txt'][k]) for k in CHAVES_TXT),
                [k for k in CHAVES_TXT if not (i['txt'] and isinstance(i['txt'].get(k), str) and i['txt'][k].strip())])
        sem_fonte = [q for q, src in f['fontes'] if 'telemetria ao vivo · 12:01:00' not in src]
        ped('forma: toda resposta de dado de bordo (%d perguntas) cita a fonte do instante («telemetria ao vivo · 12:01:00»)' % len(f['fontes']), not sem_fonte and len(f['fontes']) == len(FONTE_DO_INSTANTE), sem_fonte)
        ped('forma: horímetros — «faltam» sai do instante (32,4 h dos motores e 58,6 h do gerador às 12:01:00), não da agenda (37,4 h e 63,6 h)', 'faltam 32,4 h' in f['horimetros'] and 'faltam 58,6 h' in f['gerador'] and '37,4' not in f['horimetros'], (f['horimetros'][-160:], f['gerador'][-80:]))
        ped('forma: autonomia — horas e milhas do instante (≈ 17,6 h · ≈ 318 mn, calc.autonomia), não as do snapshot (11,2 h)', '≈ 17,6 h · ≈ 318 mn a 18 nós' in f['autonomia'] and '11,2' not in f['autonomia'], f['autonomia'][:160])
        # (a data do abastecimento anda com o dia de hoje; os litros e a hora da âncora são os do instante)
        ped('forma: «desde o abastecimento» da autonomia e do consumo vem do calc do instante (≈ 227 L desde as 07:00 às 12:01:00, ≈ 228 L às 12:01:45), não da agenda (≈ 192 L)',
            re.search(r'Consumido desde o abastecimento de \d\d/\d\d: ≈ 227 L \(desde as 07:00\)', f['autonomia']) and re.search(r'\nDesde o abastecimento de \d\d/\d\d: ≈ 227 L \(desde as 07:00\)', f['consumo'])
            and re.search(r'abastecimento de \d\d/\d\d: ≈ 228 L \(desde as 07:00\)', f['aut105']) and re.search(r'abastecimento de \d\d/\d\d: ≈ 228 L \(desde as 07:00\)', f['con105']) and '192' not in f['autonomia'] + f['consumo'],
            (f['autonomia'][-110:], f['consumo'][-170:], f['aut105'][-80:]))
        ped('forma: manutenção — o «faltam» da troca de óleo sai do instante (32,4 h), não da agenda (37,4 h)', 'faltam 32,4 h' in f['manutencao'] and '37,4' not in f['manutencao'], f['manutencao'][-120:])
        ped('forma: tanques — a hora da leitura do diesel é a do instante (leitura · 12:01:00)', 'leitura · 12:01:00' in f['tanques'], f['tanques'][-80:])
        # as chaves do §2.2 e o `oleo` (relato de falha: só os passos, a leitura fica no oleoLeitura) não leem o quadro: nem a fonte do instante (telemetria, ao vivo,
        # a hora) na fonte, no texto ou na fala (a 10 do CLAUDE.md)
        emerg = [(q, k, src) for q, k, src, texto, fala in f['emerg'] if re.search(r'telemetria|ao vivo|coletor|\b12:0\d', src + ' ' + texto + ' ' + fala, re.I)]
        ped('forma: sos, canal16, epirb, seafire, salvatagem, MMSI e óleo (queda ou alarme) não citam o instante na fonte, no texto nem na fala', not emerg and [k for q, k, *_ in f['emerg']] == CHAVES_2_2, (emerg, [k for q, k, *_ in f['emerg']]))
        # PROMPT §3 (a lista única): a fonte, o selo e o texto do instante não casam nenhuma das regex (as 8 do termos.json, menos o ANEXO). Vale também
        # para o «ao vivo» da fonte do replay: o §6.6 do contrato diz «sem coletor NMEA nem ao vivo», o §1.23 «telemetria ao vivo · hora»; nenhuma regex pega «ao vivo»
        for rot, i in (('12:01:00', f['a60']), ('12:01:45', f['a105'])):
            if i and i['txt']:
                texto = '\n'.join([i['fonteTxt'], i['selo']['texto']] + [v for v in i['txt'].values() if isinstance(v, str)])
                achados = [(n, m.group(0)) for n, rx in confere.carrega_termos().items() if n != 'ANEXO' for m in [rx.search(texto)] if m]
                ped('forma %s: fonte, selo e txt do instante fora das regex do termos.json' % rot, not achados, achados)
        a, c = f['a60'], f['a105']
        if a and a['txt']:
            ped('forma: o texto único do §1.23 (rpm, sog, diesel) é o do contrato', (a['txt']['rpm'], a['txt']['sog'], a['txt']['diesel']) == ('BB 2.049 · BE 2.038 rpm', '18,1 nós', '1.333 L (83,3 %)'), (a['txt']['rpm'], a['txt']['sog'], a['txt']['diesel']))
            ped('forma: a posição relativa (só com a simulação) vem da rota gerada', a['txt']['relativa'] == 'a 0,5 mn da Barra Sul, chegando', a['txt']['relativa'])
            ped('forma: sem alarme em 12:01:00', 'nenhum alarme' in a['txt']['alarmes'], a['txt']['alarmes'])
        if c and c['txt']:
            ped('forma: o AVISO de 12:01:45 está no txt.alarmes, com o título do catálogo', 'Temperatura do motor BE' in c['txt']['alarmes'] and '89,6' in c['txt']['alarmes'], c['txt']['alarmes'])
    finally:
        pg.ctx.close()


def grupo_uma(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        u = pg.evaluate(JS_UMA)
        ped('uma: cada chamada externa lê o instante 1 vez (answer, ficha sem resposta, resumoAgora, answerAttachment e instante)',
            u['leituras'] == {'answer': 1, 'ficha': 1, 'resumo': 1, 'anexo': 1, 'instante': 1}, u['leituras'])
        m = u['mesmo']
        ped('uma: a ficha e o resumo da MESMA pergunta ficam no instante dela (12:01:00) mesmo com o relógio em 12:02:30, sem ler o instante de novo',
            '12:01:00' in m['a1'] and '12:01:00' in m['f2'] and '12:02:30' not in m['f2'] and '12:01:00' in m['r2'] and '12:02:30' not in m['r2'] and m['nF2'] == 0 and m['nR2'] == 0, (m['a1'], m['nF2'], m['nR2'], m['r2'][-60:]))
        ped('uma: a fonte das respostas é a do instante («telemetria ao vivo · 12:01:00»), nunca «coletor NMEA», na resposta pronta e na do VIVO', m['a1'] == 'Fonte: telemetria ao vivo · 12:01:00' and m['vivo'] == m['a1'] and 'coletor' not in m['a2'], (m['a1'], m['vivo'], m['a2']))
        ped('uma: o «## Agora» da ficha do mesmo instante diz a hora dele (12:01), não a do relógio', re.search(r'\b12:01\b', m['g2']) and not re.search(r'\b12:02\b', m['g2']), m['g2'])
        ped('uma: a pergunta seguinte (outro segundo) vê o instante novo na resposta, na ficha, no «## Agora» e no resumo',
            '12:02:30' in m['a2'] and '12:02:30' in m['f3'] and '12:02:30' in m['r3'] and re.search(r'\b12:02\b', m['g3']), (m['a2'], m['g3'], m['r3'][-60:]))
        ped('uma: a ficha da resposta de um anexo fica no instante dele (12:01:00, sem ler o instante de novo), como a da resposta de texto',
            u['anexo']['n'] == 0 and '12:01:00' in u['anexo']['b'] and '12:02:30' not in u['anexo']['b'] and re.search(r'\b12:01\b', u['anexo']['g']) and not re.search(r'\b12:02\b', u['anexo']['g']), u['anexo'])
        s = u['solta']
        ped('uma: a exceção solta o instante (a pergunta seguinte lê o relógio, não o da que falhou)', s['lancou'] and '12:01:00' in s['b1'] and '12:02:30' in s['b2'] and s['depois'] == '12:01:00', s)
    finally:
        pg.ctx.close()


def grupo_resumo(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        for r in pg.evaluate(JS_RESUMO, list(INSTANTES_RESUMO)):
            ped('resumo %s: até 300 letras, com a hora do instante' % r['x'], 0 < len(r['resumo']) <= 300 and 0 < len(r['sem']) <= 300 and r['hora'] in r['resumo'] and r['hora'] in r['sem'], (len(r['resumo']), len(r['sem'])))
            ped('resumo %s: sem coordenadas (graus-minutos e decimal, §2.8)' % r['x'], not confere.R_COORD.search(r['resumo']) and not confere.R_COORD.search(r['sem']), (r['resumo'], r['sem']))
            ped('resumo %s: o resumo leva o local (nome do lugar) e o «sem posição» não' % r['x'], r['local'] in r['resumo'] and r['local'].split(', ')[0] not in r['sem'], (r['local'], r['sem']))
            ped('resumo %s: nenhuma latitude nem longitude em número' % r['x'], not re.search(r'26[.,]\d|48[.,]\d', r['resumo']), r['resumo'])
    finally:
        pg.ctx.close()


def grupo_virada(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        vs = {v['x']: v for v in pg.evaluate(JS_VIRADA, ['10@0', '149@575', '29@0', '30@0', '60'])}
        for x in ('10@0', '29@0'):
            v = vs[x]
            ped('virada %s: a tendência sai sem o diesel (o abastecimento atravessa os 30 s), com rpm, óleo, arrefecimento e SOG' % x,
                v['tend'] and 'diesel_litros' not in v['tend'] and all(k in v['tend'] for k in ('motor_bb_rpm', 'motor_be_oleo_bar', 'motor_bb_arref_c', 'sog_nos')) and 'diesel' not in v['txtTend'] and 'rpm' in v['txtTend'], (v['tend'], v['txtTend']))
        for x in ('30@0', '60', '149@575'):
            v = vs[x]
            ped('virada %s: na fronteira (30 s depois da âncora), depois dela e em 06:59:59 (a janela inteira no mesmo dia de bordo) a tendência tem o diesel' % x, v['tend'] and 'diesel_litros' in v['tend'] and 'diesel' in v['txtTend'], (v['tend'], v['txtTend']))
        for x, v in vs.items():
            ped('virada %s: respostas, ficha, resumo e textos do instante sem NaN, undefined nem null' % x, not re.search(r'NaN|undefined|\bnull\b', v['texto']), re.findall(r'.{30}(?:NaN|undefined|\bnull\b).{20}', v['texto'])[:2])
    finally:
        pg.ctx.close()


def grupo_sos(b, muta, ped):
    for nome, extra in FONTES_SOS.items():
        pg = pagina(b, extra=extra + GETTERS_SOS, scripts=('capitao-dados.js', 'capitao-brain.js'), caminho='SOS-cerebro.html', fixo=None, muta=muta)
        try:
            s = pg.evaluate(JS_SOS, list(PERGUNTA_CHAVE.values()))
            ped('sos (%s): nenhuma leitura de D.simulacao, D.replay, D.snapshot, D.rota nem D.campos (carga, instante, resumo, diário, ficha e uma resposta de CADA chave de ANSWERS)' % nome,
                {'simulacao', 'replay', 'snapshot', 'rota'} <= set(s['lidas']) and s['n'] == len(PERGUNTA_CHAVE) and all(v == 0 for v in s['lidas'].values()), (s['n'], s['lidas']))
            ped('sos (%s): o resumo sem posição também é o do plotter' % nome, s['sem'] == s['plotter'], s['sem'])
            ped('sos (%s): o instante do cérebro é nulo, como o do rodapé' % nome, s['b'] is None and s['a'] is None, (s['b'], s['a']))
            ped('sos (%s): o resumo é o do plotter, sem quadro' % nome, s['resumo'] == s['plotter'] and 'LEIA NO PLOTTER' in s['resumo'], s['resumo'])
            ped('sos (%s): a linha do diário é só a do SOS (nada de quadro, resumo, posição nem sim)' % nome,
                set(s['entrada'].keys()) == {'d', 't', 'iso', 'sys', 'tone', 'who', 'src'} and 'sim' not in s['guardada'] and s['entrada']['t'] == 'MAYDAY teste', (sorted(s['entrada'].keys()), s['guardada']))
            ped('sos (%s): nenhuma resposta do cérebro leva a leitura da fonte (SOG, diesel, ar, posição)' % nome, not re.search(r'18,1|1\.333|22,6|26[.,]99|26°59|48[.,]61', s['texto']), s['texto'][:200])
        finally:
            pg.ctx.close()


def resumo_real(ped, nome, r):
    """Sem quadro vivo, B.resumoAgora() (o do diário e o do contexto da IA) vem do D.snapshot: até 300 letras, nunca coordenada (§2.8, os dois modos);
    com {semPosicao: true} (as exceções da decisão (g)) também não leva o lugar."""
    ped('real (%s): o resumo tem até 300 letras, com o instante do snapshot, e não leva coordenada (graus-minutos nem decimal)' % nome,
        0 < len(r['resumo']) <= 300 and 0 < len(r['sem']) <= 300 and not confere.R_COORD.search(r['resumo']) and not confere.R_COORD.search(r['sem']) and '26/09/2026 10:12' in r['resumo'] and '26/09/2026 10:12' in r['sem']
        and not re.search(r'26[.,°]\d|48[.,°]\d', r['resumo'] + r['sem']), (len(r['resumo']), len(r['sem']), r['resumo']))
    ped('real (%s): o resumo leva o lugar e o «sem posição» não leva (só o estado)' % nome, r['local'] in r['resumo'] and r['local'] not in r['sem'] and r['estado'] in r['sem'] and r['sem'] != r['resumo'], (r['local'], r['sem']))


def grupo_real(b, muta, ped):
    casos = [[q, k] for q, k in CASOS]
    sem = pagina(b, extra=SEM_SIMULACAO + relogio(VIRADA_DO_MINUTO), scripts=('capitao-dados.js', 'capitao-brain.js'), fixo=None, muta=muta)
    com = pagina(b, extra=SEM_SIMULACAO + relogio(VIRADA_DO_MINUTO + 200), muta=muta)
    try:
        for pg in (sem, com):
            pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); })")
        x, y = sem.evaluate(JS_REAL, casos), com.evaluate(JS_REAL, casos)
        ped('real: com simulacao false o replay não anda e o instante é a reserva (D.snapshot), sem tendência nem texto do quadro', y['fonte'] == 'snapshot' and y['tend'] is None and not y['replayAtivo'], (y['fonte'], y['tend'], y['replayAtivo']))
        dif = [r[0] for r, s in zip(x['respostas'], y['respostas']) if r != s]
        fx, ax = sem_agora(x['ficha']); fy, ay = sem_agora(y['ficha'])
        ped('real: as %d respostas (texto, fonte e fala) e a ficha (fora do relógio do «## Agora») são os de antes (iguais aos da página sem o replay)' % len(casos),
            not dif and fx == fy and x['resumo'] == y['resumo'] and x['sem'] == y['sem'], dif[:3])
        ped('real: a ficha abre com o «## Agora» (dia e hora de Brasília) nas duas páginas', agora_ok(ax) and agora_ok(ay), (ax, ay))
        resumo_real(ped, 'simulacao false', y)
        tel = [r[2] for r in y['respostas'] if r[1] == 'telemetria']
        # sem o CapitaoAgora (o rodapé do capitao-dados.js falhou ou a tela não o tem): a reserva, fonte `snapshot`, e as respostas são as da página sem replay
        sa = pagina(b, extra=';delete window.CapitaoAgora;' + relogio(VIRADA_DO_MINUTO), scripts=('capitao-dados.js', 'capitao-brain.js'), fixo=None, muta=muta)
        sr = pagina(b, extra=relogio(VIRADA_DO_MINUTO + 200), scripts=('capitao-dados.js', 'capitao-brain.js'), fixo=None, muta=muta)
        try:
            for pg in (sa, sr):
                pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); })")
            ja, jr = sa.evaluate(JS_REAL, casos), sr.evaluate(JS_REAL, casos)
            ped('real: sem o CapitaoAgora o instante do cérebro é a reserva (fonte snapshot, nunca nulo fora do SOS)', ja['fonte'] == 'snapshot' and ja['txt'] is False, (ja['fonte'], ja['txt']))
            dif2 = [r[0] for r, s in zip(ja['respostas'], jr['respostas']) if r != s]
            fa, aa = sem_agora(ja['ficha']); fr, ar = sem_agora(jr['ficha'])
            ped('real: sem o CapitaoAgora as respostas e a ficha (fora do relógio do «## Agora») são as de antes da 1.1.0', not dif2 and fa == fr and agora_ok(aa) and agora_ok(ar), (dif2[:3], aa, ar))
            resumo_real(ped, 'sem o CapitaoAgora', ja)
            resumo_real(ped, 'tela sem replay', jr)
        finally:
            sa.ctx.close(); sr.ctx.close()
        ped('real: o cérebro do modo real segue no snapshot de 26/09 («Snapshot de 26/09/2026 10:12», fundeado)', tel and '26/09/2026 10:12' in tel[0] and 'undeado' in y['resumo'], (tel[:1], y['resumo'][:120]))
    finally:
        sem.ctx.close(); com.ctx.close()

# o texto único do alarme (§1.23): o da CapitaoAlertas («rótulo: título: valor (acima de limite)»), o mesmo com ou sem o script na tela
ALARMES = {'60': 'nenhum alarme ativo', '100': 'AVISO: Temperatura do motor BE: 89,0 °C (acima de 88 °C)', '105': 'AVISO: Temperatura do motor BE: 89,6 °C (acima de 88 °C)',
           '115': 'AVISO: Temperatura do motor BE: 89,0 °C (acima de 88 °C)', '120': 'nenhum alarme ativo'}
JS_ALARMES = """(xs) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, AL = window.CapitaoAlertas, out = { alertas: !!AL };
  let chamadas = 0, msAl = null;
  if (AL) { const orig = AL.ativos; AL.ativos = function (m) { chamadas++; msAl = m; return orig.apply(this, arguments); }; }
  out.xs = xs.map((x) => { R.fixar(x); chamadas = 0; msAl = null; const i = B.instante(); return { x, ms: i.ms, alarmes: i.txt.alarmes, resumo: i.txt.resumo, chamadas, msAl }; });
  return out; }"""
ALERTAS_FALSO = ";window.CapitaoAlertas = { ativos: function (ms) { return [{ rotulo: 'CRÍTICO', texto: 'Teste X ' + ms }]; } };"
ALERTAS_QUE_LANCA = ";window.CapitaoAlertas = { ativos: function () { throw new Error('alertas'); } };"


def grupo_alarmes(b, muta, ped):
    # a página da Main e da H2 (com o capitao-alertas.js): a fonte é a CapitaoAlertas, com o ms do instante; a reserva (tela sem o script) diz o mesmo texto
    for nome, kw in (('com o capitao-alertas.js', {}), ('sem o capitao-alertas.js (reserva)', {'scripts': SCRIPTS_SEM_ALERTAS})):
        pg = pagina(b, muta=muta, **kw)
        try:
            r = pg.evaluate(JS_ALARMES, list(ALARMES))
            ped('alarmes (%s): o script está (ou não) na tela como se espera' % nome, r['alertas'] == (not kw), r['alertas'])
            for x in r['xs']:
                ped('alarmes (%s) %s: txt.alarmes é exatamente «%s»' % (nome, x['x'], ALARMES[x['x']]), x['alarmes'] == ALARMES[x['x']], x['alarmes'])
                if x['alarmes'] != 'nenhum alarme ativo':
                    ped('alarmes (%s) %s: o resumo (diário e contexto da IA) leva o alarme e tem até 300 letras' % (nome, x['x']), ALARMES[x['x']] in x['resumo'] and len(x['resumo']) <= 300, (len(x['resumo']), x['resumo']))
                if r['alertas']:
                    ped('alarmes (%s) %s: o cérebro pergunta à CapitaoAlertas uma vez, com o ms do instante' % (nome, x['x']), x['chamadas'] == 1 and x['msAl'] == x['ms'], (x['chamadas'], x['msAl'], x['ms']))
        finally:
            pg.ctx.close()
    # a CapitaoAlertas manda: o que ela devolve é o texto (e o ms é o do instante); se ela lança, vale o quadro, com o mesmo molde
    pg = pagina(b, extra=ALERTAS_FALSO, muta=muta)
    try:
        r = pg.evaluate(JS_ALARMES, ['105'])['xs'][0]
        ped('alarmes (alertas falso): txt.alarmes é o que a CapitaoAlertas devolve, chamada com o ms do instante', r['alarmes'] == 'CRÍTICO: Teste X %d' % r['ms'] and 'CRÍTICO: Teste X' in r['resumo'], (r['alarmes'], r['ms']))
    finally:
        pg.ctx.close()
    pg = pagina(b, extra=ALERTAS_QUE_LANCA, muta=muta)
    try:
        r = pg.evaluate(JS_ALARMES, ['105'])['xs'][0]
        ped('alarmes (alertas que lança): o cérebro não quebra e usa os alarmes do quadro, no mesmo molde', r['alarmes'] == ALARMES['105'], r['alarmes'])
    finally:
        pg.ctx.close()
    alarmes_sem_campo(b, muta, ped)


# revisão da P3B (3ª): um coletor que NÃO reporta o campo `alarmes` não tem alarme para dizer: «nenhum alarme ativo» sem dado é a afirmação perigosa. Com a simulação a cláusula some das respostas
# (motores, óleo, seguro, telemetria); sem ela a regra «Nada inventado» (sensor ausente → SEM LEITURA). «nenhum alarme ativo» só com a lista vazia que o coletor manda.
JS_SEM_ALARMES = """([sim, tipo]) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false };
  R.fixar('60'); const q = Object.assign({}, R.em(R.agora())); delete q.simulado;
  if (tipo === 'sem') delete q.alarmes; else if (tipo === 'vazio') q.alarmes = []; else q.alarmes = [{ id: 'arref_be', nivel: 'aviso', sistema: 'motores', lado: 'be', campo: 'motor_be_arref_c', valor: 89.6, limite: 88, desde: '2026-10-27T15:01:00Z' }];
  window.CapitaoTelemetria = { atual: () => q }; window.CapitaoDados.simulacao = sim;
  const i = B.instante(), t = (k) => B.answer(k, op);
  return { fonte: i.fonte, alarmes: i.txt.alarmes === undefined ? null : i.txt.alarmes, resumo: i.txt.resumo, mot: t('motores').text, oleo: t('qual a pressão do óleo?').text, seguro: t('é seguro sair hoje?').text, tele: t('Telemetria agora').text }; }"""


def alarmes_sem_campo(b, muta, ped):
    for sim in (True, False):
        rot = 'simulacao %s' % ('true' if sim else 'false')
        r = {}
        for tipo in ('sem', 'vazio', 'um'):
            pg = pagina(b, muta=muta)
            try:
                r[tipo] = pg.evaluate(JS_SEM_ALARMES, [sim, tipo])
            finally:
                pg.ctx.close()
        s = r['sem']
        tudo = lambda x: x['mot'] + '\n' + x['oleo'] + '\n' + x['seguro'] + '\n' + x['tele']
        ped('alarmes (coletor sem o campo `alarmes`, %s): o instante é do coletor e txt.alarmes não existe (nunca «nenhum alarme ativo»), nem no resumo' % rot,
            s['fonte'] == 'coletor' and s['alarmes'] is None and 'nenhum' not in s['resumo'], (s['fonte'], s['alarmes'], s['resumo'][-120:]))
        ped('alarmes (coletor sem o campo `alarmes`, %s): nenhuma resposta diz «nenhum alarme ativo» nem tem «undefined»' % rot, 'nenhum alarme' not in tudo(s) and 'undefined' not in tudo(s), tudo(s)[:300])
        clausulas = [' · alarmes: ' in s['mot'], ' · alarmes: ' in s['oleo'], ' · alarmes: ' in s['seguro'], '\n• Alarmes: ' in s['tele']]
        if sim:
            ped('alarmes (coletor sem o campo `alarmes`, simulacao true): a cláusula dos alarmes some dos motores, do óleo, do seguro e da telemetria (nada de SEM LEITURA)',
                not any(clausulas) and 'SEM LEITURA' not in tudo(s) and 'Alarmes' not in s['tele'], (clausulas, s['tele'][-160:]))
        else:
            ped('alarmes (coletor sem o campo `alarmes`, simulacao false): a regra «Nada inventado» volta: «alarmes: SEM LEITURA» nos motores, no óleo, no seguro e na telemetria',
                all(clausulas) and ' · alarmes: SEM LEITURA.' in s['mot'] and ' · alarmes: SEM LEITURA.' in s['oleo'] and ' · alarmes: SEM LEITURA.' in s['seguro'] and s['tele'].count('• Alarmes: SEM LEITURA') == 1,
                (clausulas, s['mot'][:120], s['tele'][-120:]))
        v = r['vazio']
        ped('alarmes (coletor com a lista vazia, %s): «nenhum alarme ativo» é do coletor que reporta (controle)' % rot,
            v['alarmes'] == 'nenhum alarme ativo' and ' · alarmes: nenhum alarme ativo.' in v['mot'] and '• Alarmes: nenhum alarme ativo' in v['tele'], (v['alarmes'], v['mot'][:120]))
        u = r['um']
        ped('alarmes (coletor com um alarme, %s): o alarme do quadro dele sai nos motores, no seguro e na telemetria' % rot,
            u['alarmes'] == ALARMES['105'] and ALARMES['105'] in u['mot'] and ALARMES['105'] in u['seguro'] and ALARMES['105'] in u['tele'], (u['alarmes'], u['mot'][:200]))


# chamadas aninhadas (answer → addDiario → …): UMA leitura do instante por pergunta, mesmo com o relógio andando 10 s depois de cada leitura
JS_ANINHADAS = """() => { const B = window.CapitaoBrain, R = window.CapitaoReplay, A = window.CapitaoAgora, out = {};
  let n = 0, seg = 60; const orig = A.instante;
  A.instante = function () { n++; const r = orig.apply(this, arguments); seg += 10; R.fixar(String(seg)); return r; };
  const roda = (nome, f) => { localStorage.clear(); n = 0; seg = 60; R.fixar('60'); const r = f(); out[nome] = { n, r }; };
  const op = { platform: 'app', commit: true };
  roda('registro', () => B.answer('Registre no diário: saída com 4 pessoas', op).text);
  roda('resumo', () => { const a = B.answer('Registre no diário o resumo da navegação de agora e confirme.', op); return [a.text, a.src, B.loadDiario()[0].t]; });
  roda('anexo', () => B.answerAttachment('foto', { name: 'a.jpg', size: 2048 }, op).text);
  roda('video', () => B.answerAttachment('video', { name: 'a.mp4', size: 2048 }, op).text);
  roda('diarioAdd', () => B.addDiario({ t: 'teste', src: 'teste' }).t);
  A.instante = orig; R.fixar('60'); return out; }"""


def grupo_aninhadas(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        u = pg.evaluate(JS_ANINHADAS)
        ped('aninhadas: cada pergunta (registro, resumo, foto, vídeo, addDiario) lê o instante UMA vez, mesmo com o relógio andando', {k: v['n'] for k, v in u.items()} == {'registro': 1, 'resumo': 1, 'anexo': 1, 'video': 1, 'diarioAdd': 1}, {k: v['n'] for k, v in u.items()})
        txt = ' '.join(u['resumo']['r'])
        ped('aninhadas: a resposta do resumo, a fonte e a linha do diário ficam no instante da pergunta (12:01:00), não no de uma segunda leitura (12:01:10)',
            '12:01:00' in u['resumo']['r'][0] and '12:01:00' in u['resumo']['r'][1] and '12:01:00' in u['resumo']['r'][2] and '12:01:10' not in txt and '12:01:20' not in txt, u['resumo']['r'])
    finally:
        pg.ctx.close()


# vivo → reserva → vivo na MESMA página (D.simulacao vira false e volta): o cérebro refaz S, AUT e CON de cada instante, sem sobra do anterior
JS_TRANSICAO = """() => { const B = window.CapitaoBrain, R = window.CapitaoReplay, D = window.CapitaoDados, op = { platform: 'app', commit: false }, out = {};
  R.fixar('60');
  const le = () => ({ aut: B.answer('autonomia', op).text, hor: B.answer('horímetros', op).text, con: B.answer('consumo de diesel', op).text, tel: B.answer('telemetria', op).text,
                      src: B.answer('autonomia', op).src, fonte: B.instante().fonte });
  out.vivo1 = le(); D.simulacao = false; out.reserva = le(); D.simulacao = true; out.vivo2 = le();
  return out; }"""


def grupo_transicao(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        t = pg.evaluate(JS_TRANSICAO)
        v1, rs, v2 = t['vivo1'], t['reserva'], t['vivo2']
        ped('transição: ao vivo, com a flag ligada', v1['fonte'] == 'replay' and '≈ 17,6 h' in v1['aut'] and 'faltam 32,4 h' in v1['hor'] and '≈ 227 L' in v1['con'] and 'ao vivo' in v1['src'], (v1['fonte'], v1['aut'][:60], v1['src']))
        ped('transição: com simulacao false a MESMA página volta ao D.snapshot (11,2 h, 37,4 h, 192 L, 26/09 10:12), sem sobra do quadro vivo',
            rs['fonte'] == 'snapshot' and '≈ 11,2 h' in rs['aut'] and '17,6' not in rs['aut'] and 'faltam 37,4 h' in rs['hor'] and '32,4' not in rs['hor'] and '≈ 192 L' in rs['con'] and '227' not in rs['con'] + rs['aut']
            and '26/09/2026 10:12' in rs['tel'] and 'ao vivo' not in rs['src'], (rs['fonte'], rs['aut'][:90], rs['hor'][-60:], rs['con'][-120:], rs['tel'][:50], rs['src']))
        ped('transição: com a flag de volta, as respostas voltam a ser as do instante', v2['aut'] == v1['aut'] and v2['hor'] == v1['hor'] and v2['con'] == v1['con'] and v2['tel'] == v1['tel'] and v2['src'] == v1['src'], (v2['aut'][:60], v1['aut'][:60]))
    finally:
        pg.ctx.close()


# um coletor de verdade (quadro sem `simulado`): a fonte dele («coletor NMEA · ao vivo hora»), sem tendência (o histórico é do replay) e os números DELE
JS_COLETOR = """() => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false }, out = {};
  R.fixar('60');
  const q = Object.assign({}, R.em(R.agora()), { sog_nos: 7.3, diesel_litros: 900, diesel_bb_pct: 56.2, diesel_be_pct: 56.3 }); delete q.simulado;
  window.CapitaoTelemetria = { atual: () => q };
  const i = B.instante();
  out.i = { fonte: i.fonte, fonteTxt: i.fonteTxt, tend: i.tend === undefined ? null : i.tend, txtTend: i.txt.tend === undefined ? null : i.txt.tend, selo: i.selo.texto };
  out.r = ['Telemetria agora', 'posição agora', 'autonomia', 'nível dos tanques', 'clima e vento', 'consumo de diesel', 'horímetros', 'estabilizador Seakeeper'].map((k) => { const a = B.answer(k, op); return [k, a.text, a.src]; });
  // 12:01:45: o replay tem o AVISO da temperatura do motor BE (CapitaoAlertas), o quadro do coletor não traz alarme nenhum: o texto é o do quadro dele
  R.fixar('105'); const q2 = Object.assign({}, R.em(R.agora()), { alarmes: [] }); delete q2.simulado; window.CapitaoTelemetria = { atual: () => q2 };
  const j = B.instante(); out.alarmes = { fonte: j.fonte, txt: j.txt.alarmes, resumo: j.txt.resumo };
  // a posição relativa («a 0,5 mn da Barra Sul») é só da simulação: um coletor com a flag desligada não a leva, mesmo com wp_proximo no quadro
  R.fixar('60'); const q3 = Object.assign({}, R.em(R.agora())); delete q3.simulado; window.CapitaoDados.simulacao = false; window.CapitaoTelemetria = { atual: () => q3 };
  const k = B.instante(); out.relativa = { fonte: k.fonte, rel: k.txt.relativa === undefined ? null : k.txt.relativa, wp: q3.wp_proximo };
  window.CapitaoDados.simulacao = true;
  return out; }"""


def grupo_coletor(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        c = pg.evaluate(JS_COLETOR)
        i = c['i']
        ped('coletor: o instante é do coletor, com a fonte «coletor NMEA · ao vivo hora» e sem tendência (o histórico é só do replay)',
            i['fonte'] == 'coletor' and i['fonteTxt'] == 'coletor NMEA · ao vivo 12:01:00' and i['tend'] is None and i['txtTend'] is None, i)
        r = {k: (t, s) for k, t, s in c['r']}
        ped('coletor: toda resposta de dado de bordo cita a fonte do coletor e nenhuma a do replay', all('coletor NMEA · ao vivo 12:01:00' in s and 'telemetria ao vivo' not in s for k, (t, s) in r.items()), [(k, s[:70]) for k, (t, s) in r.items() if 'coletor NMEA · ao vivo 12:01:00' not in s])
        ped('coletor: o alarme é o do quadro dele (nenhum), não o da CapitaoAlertas, que é a do replay', c['alarmes']['fonte'] == 'coletor' and c['alarmes']['txt'] == 'nenhum alarme ativo' and 'AVISO' not in c['alarmes']['resumo'], c['alarmes'])
        ped('coletor: sem a simulação (flag desligada) o quadro do coletor não leva a posição relativa à rota', c['relativa']['fonte'] == 'coletor' and c['relativa']['wp'] and c['relativa']['rel'] is None, c['relativa'])
        ped('coletor: os números são os do quadro dele (SOG 7,3, 900 L), não os do replay (18,1; 1.333 L)', 'SOG 7,3' in r['posição agora'][0] and '≈ 900 L' in r['autonomia'][0] and '1.333' not in r['autonomia'][0] + r['nível dos tanques'][0] and '900 L' in r['Telemetria agora'][0], (r['posição agora'][0][:90], r['autonomia'][0][:150]))
    finally:
        pg.ctx.close()


# a recarrega() lança (aqui, o formatador de coordenadas): o instante VIVO não pode ficar valendo com os dados do snapshot de volta
JS_FALHA = """() => { const B = window.CapitaoBrain, R = window.CapitaoReplay, A = window.CapitaoAgora, op = { platform: 'app', commit: false }, out = {};
  R.fixar('60'); const orig = A.fmt.coord; A.fmt.coord = function () { throw new Error('coord'); };
  try {
    out.r = ['posição agora', 'autonomia', 'Telemetria agora', 'nível dos tanques', 'horímetros', 'clima e vento'].map((k) => { const a = B.answer(k, op); return [k, a.text, a.src]; });
    out.ficha = B.ficha('app', 'telemetria', null); out.resumo = B.resumoAgora();
  } finally { A.fmt.coord = orig; }
  out.depois = B.answer('autonomia', op).text;
  return out; }"""


def grupo_falha(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        f = pg.evaluate(JS_FALHA)
        r = {k: (t, s) for k, t, s in f['r']}
        # (P3B: o «Telemetria ao vivo desligada» fixo saiu do texto da resposta `telemetria`; a conferência vale para o texto inteiro, sem tirar nada)
        presos = [k for k, (t, s) in r.items() if re.search(r'ao vivo|12:01', t + ' ' + s)]
        ped('falha: se a recarrega lança, nenhuma resposta (texto nem fonte) diz «ao vivo» nem leva a hora do instante com dado de 26/09', not presos and '≈ 11,2 h' in r['autonomia'][0] and '26°59' in r['posição agora'][0], (presos, r['posição agora'][1], r['autonomia'][1][:60]))
        # (P3B: o resumo da reserva termina em «leitura de 26/09/2026 10:12», não em «snapshot»: a palavra é da lista VISIVEL do §3)
        ped('falha: a ficha e o resumo do mesmo caso também voltam ao snapshot', '12:01:00' not in f['resumo'] and '26/09/2026 10:12' in f['resumo'] and 'snapshot' not in f['resumo'] and 'ao vivo ·' not in f['ficha'] and '12:01:00' not in f['ficha'], (f['resumo'][-80:]))
        ped('falha: passada a falha, a pergunta seguinte volta ao instante', '≈ 17,6 h' in f['depois'], f['depois'][:60])
    finally:
        pg.ctx.close()


# modo real com um coletor de quadro PARCIAL (GPS, vento, tanques; nada de motor, gerador, Seakeeper nem diesel): sensor ausente não vira «desligado»,
# nem leva a autonomia do snapshot de 26/09 com a fonte do coletor (decisão 6: com simulacao false volta a regra «Nada inventado»)
JS_PARCIAL = """(casos) => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false };
  window.CapitaoTelemetria = { atual: () => ({ timestamp_utc: '2026-11-02T15:01:00Z', lat: -26.99, lon: -48.61, sog_nos: 0.2, gps_satelites: 11, vento_verdadeiro_nos: 9.5, vento_verdadeiro_angulo: 120,
                                               tanque_agua_pct: 80, tanque_cinzas_pct: 10, tanque_negras_pct: 12, gerador_horimetro_h: 1240.5, motor_bb_horimetro_h: 417.6, motor_be_horimetro_h: 414.8 }) };
  const i = B.instante(), periodo = B.DADOS.consumo.periodo;
  return { fonte: i.fonte, fonteTxt: i.fonteTxt, periodo, r: casos.map(([q]) => { const a = B.answer(q, op); return [q, a.key, a.text.split(periodo).join(''), a.src.split(periodo).join('')]; }) }; }"""
DADO_DE_BORDO = ['motores volvo penta', 'Telemetria agora', 'quantas horas tem o gerador', 'estabilizador Seakeeper', 'autonomia', 'é seguro sair hoje?', 'para onde vamos hoje?',
                 'consumo de diesel', 'nível dos tanques', 'horímetros', 'posição agora', 'clima e vento', 'bateria 24 v', 'âncora garrando?']


def grupo_parcial(b, muta, ped):
    pg = pagina(b, extra=SEM_SIMULACAO, muta=muta)
    try:
        pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); })")
        x = pg.evaluate(JS_PARCIAL, [[q, k] for q, k in CASOS])
        ped('parcial: o instante é o do coletor', x['fonte'] == 'coletor' and x['fonteTxt'].startswith('coletor NMEA · ao vivo '), (x['fonte'], x['fonteTxt']))
        r = {q: (k, t, s) for q, k, t, s in x['r']}
        # (o «desligado» fixo de oleoLeitura e de «Telemetria ao vivo desligada» é do texto da resposta, que a P3B reescreve: aqui só o que vem do dado)
        sem_dado = [(q, re.findall(r'.{0,40}(?:desligad[oa]s?|11,2|202 mn|≈ 192 L|26/09).{0,30}', t)[:2]) for q, (k, t, s) in r.items()
                    if q in DADO_DE_BORDO and re.search(r'desligad[oa]s?|11,2|202 mn|≈ 192 L|26/09', t.replace('Telemetria ao vivo desligada', ''))]
        ped('parcial: sensor ausente não vira «desligado», nem sai a autonomia de 11,2 h, os 192 L ou a data 26/09 do snapshot nas respostas de dado de bordo', not sem_dado, sem_dado[:4])
        quebradas = [(q, re.findall(r'.{0,30}(?:undefined|NaN|\bnull\b|sEM DADOS).{0,20}', t + ' | ' + s)[:1]) for q, (k, t, s) in r.items() if re.search(r'undefined|NaN|\bnull\b|sEM DADOS', t + ' ' + s)]
        ped('parcial: nenhuma das %d respostas tem undefined, NaN, null nem «sEM DADOS»' % len(r), not quebradas, quebradas[:4])
        ped('parcial: o que o coletor tem aparece (SOG, vento, tanques) e o que falta é SEM DADOS ou SEM LEITURA',
            '9,5' in r['clima e vento'][1] and '80' in r['nível dos tanques'][1] and 'SEM' in r['autonomia'][1] and 'SEM' in r['motores volvo penta'][1] and ('SEM LEITURA' in r['estabilizador Seakeeper'][1] or 'SEM DADOS' in r['estabilizador Seakeeper'][1]),
            (r['autonomia'][1][:130], r['motores volvo penta'][1][:100], r['estabilizador Seakeeper'][1][:100]))
    finally:
        pg.ctx.close()



# Os números das respostas de dado de bordo são os do quadro do instante (S, M, G, DI, T e SNAP são refeitos do quadro a cada pergunta): cada resposta é
# comparada com o `txt` e o `calc` do MESMO instante (o texto único do §1.23), em 12:01:00, 12:01:45 e 06:59:59 (a conta do abastecimento passa de 1.000 L)
JS_NUMEROS = """([xs, qs]) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false };
  return xs.map((x) => { R.fixar(x); const i = B.instante();
    return { x, hora: i.hora, txt: i.txt, calc: i.calc, sat: i.q.gps_satelites, volante: i.q.seakeeper_volante_rpm,
             r: qs.map((p) => { const a = B.answer(p, op); return [p, a.text, a.src]; }) }; }); }"""
PERGUNTAS_NUMEROS = ['Telemetria agora', 'é seguro sair hoje?', 'motores volvo penta', 'quantas horas tem o gerador', 'horímetros', 'nível dos tanques', 'posição agora',
                     'clima e vento', 'bateria 24 v', 'estabilizador Seakeeper', 'qual a pressão do óleo?', 'autonomia', 'consumo de diesel']
INSTANTES_NUMEROS = ('60', '105', '149@575')


def em_ordem(texto, partes):
    """A 1ª das `partes` que não aparece no texto depois da anterior (None = todas, na ordem): um par trocado de lugar (ar e água, vento e rumo) é acusado."""
    pos = 0
    for x in partes:
        k = texto.find(x, pos)
        if k < 0:
            return x
        pos = k + len(x)
    return None


def nums(s):
    return re.findall(r'\d[\d.]*(?:,\d+)?', s)


def esperados_numeros(x):
    """Para cada pergunta, os pedaços (na ordem) que o `txt` e o `calc` do instante põem na resposta. Os rótulos são os mínimos: o número só vale ao lado do dele."""
    t, c = x['txt'], x['calc']
    sog, prof, ar, agua = nums(t['sog'])[0], t['prof'], t['ar'], t['agua']
    b24, b12 = nums(t['b24'])[0], t['b12']
    litros = nums(t['diesel'])[0]
    ger_h = re.search(r'([\d.]+,\d) h', t['gerador']).group(1)
    hbb, hbe = re.search(r'motor BB ([\d.]+,\d) h', t['horimetros']).group(1), re.search(r'motor BE ([\d.]+,\d) h', t['horimetros']).group(1)
    agua_doce, cinzas, negras = re.search(r'água doce ([\d,]+) % · cinzas ([\d,]+) % · negras ([\d,]+) %', t['tanques']).groups()
    motores = 'Motores ligados — ' + t['rpm'] + ' · óleo ' + t['oleo'] + ' · arrefecimento ' + t['arref']
    oleo_bb, oleo_be, arr_bb, arr_be = nums(t['oleo'])[0], nums(t['oleo'])[1], nums(t['arref'])[0], nums(t['arref'])[1]
    return {
        'Telemetria agora': [x['hora'], 'SOG ' + sog, t['proa'], 'profundidade ' + prof, t['vento'], 'ar ' + ar, 'mar ' + agua, '24 V ' + b24 + ' V', '12 V ' + b12, 'Tanques: ' + t['tanques'],
                             'Diesel ' + t['dieselLados'], '≈ ' + litros + ' L de', motores, 'Gerador ligado · ' + ger_h + ' h'],
        'é seguro sair hoje?': [x['hora'], 'vento ' + t['vento'], str(x['sat']) + ' satélites', 'banco 24 V ' + b24 + ' V', 'Diesel ≈ ' + litros + ' L (' + t['dieselLados'], '≈ ' + nums(t['autonomia'])[0] + ' h a 18 nós', motores],
        'motores volvo penta': [motores, 'Horímetros BB ' + hbb + ' h · BE ' + hbe + ' h'],
        'quantas horas tem o gerador': [x['hora'], ger_h + ' h'],
        'horímetros': [x['hora'], 'motor BB ' + hbb + ' h', 'motor BE ' + hbe + ' h', 'gerador ' + ger_h + ' h'],
        'nível dos tanques': ['água doce ' + agua_doce + ' %', 'águas cinzas ' + cinzas + ' %', 'águas negras ' + negras + ' %', 'diesel: ' + t['dieselLados'], '≈ ' + litros + ' L de'],
        'posição agora': ['SOG ' + sog, 'proa ' + t['proa'], 'profundidade ' + prof, 'ao vivo ' + x['hora']],
        'clima e vento': [x['hora'], 'vento verdadeiro ' + t['vento'], 'ar ' + ar, 'água ' + agua],
        'bateria 24 v': ['banco 24 V ' + b24 + ' V', 'banco 12 V ' + b12, x['hora']],
        'estabilizador Seakeeper': ['LIGADO', 'volante', x['hora']],
        'qual a pressão do óleo?': [oleo_bb, oleo_be, t['rpm'], arr_bb, arr_be],
        'autonomia': ['≈ ' + nums(t['autonomia'])[0] + ' h · ≈ ' + nums(t['autonomia'])[1] + ' mn', '≈ ' + litros + ' L de', t['dieselLados'], '≈ %s h' % c['autonomia']['lenta'], '≈ ' + nums(t['desdeAbast'])[0] + ' L (desde as 07:00)'],
        'consumo de diesel': ['≈ ' + nums(t['desdeAbast'])[0] + ' L (desde as 07:00)'],
    }


def grupo_numeros(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        xs = pg.evaluate(JS_NUMEROS, [list(INSTANTES_NUMEROS), PERGUNTAS_NUMEROS])
        for x in xs:
            esp = esperados_numeros(x)
            r = {p: (tx, sr) for p, tx, sr in x['r']}
            for p in PERGUNTAS_NUMEROS:
                falta = em_ordem(r[p][0], esp[p])
                ped('numeros %s «%s»: os números e a hora são os do instante, cada um ao lado do seu rótulo e na ordem' % (x['x'], p), falta is None, (falta, r[p][0][:260]))
            # o Seakeeper mostra o volante do quadro (com ou sem o ponto de milhar)
            ped('numeros %s: o volante do Seakeeper é o do quadro (%s rpm)' % (x['x'], x['volante']), str(x['volante']) in r['estabilizador Seakeeper'][0].replace('.', ''), r['estabilizador Seakeeper'][0][:90])
            # «desde o abastecimento»: com milhar quando passa de 999 L (a autonomia e o consumo escrevem como o txt do instante e como a linha dos abastecimentos)
            lit = nums(x['txt']['desdeAbast'])[0]
            ped('numeros %s: «desde o abastecimento» da autonomia e do consumo é «≈ %s L», o mesmo número do txt do instante e do calc' % (x['x'], lit),
                'Consumido desde o abastecimento de' in r['autonomia'][0] and ': ≈ %s L (' % lit in r['autonomia'][0] and '\nDesde o abastecimento de' in r['consumo de diesel'][0] and ': ≈ %s L (' % lit in r['consumo de diesel'][0]
                and lit.replace('.', '') == str(x['calc']['desdeAbast']['litros']), (lit, r['autonomia'][0][-80:], r['consumo de diesel'][0][-130:]))
        # um instante com mais de 1.000 L desde o abastecimento está entre os que o teste varre (o defeito era só de 04:30 às 07:00)
        ped('numeros: os instantes varridos incluem um com mais de 999 L desde o abastecimento', any(x['calc']['desdeAbast']['litros'] > 999 for x in xs), [x['calc']['desdeAbast']['litros'] for x in xs])
    finally:
        pg.ctx.close()


# o estado dos motores vem dos DOIS motores (um só ligado é «ligados»; nenhum, «desligados»): coletor de verdade, com o quadro à mão
JS_LIGADOS = """() => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false };
  R.fixar('60'); const base = R.em(R.agora());
  // (o rodapé guarda o instante por segundo: um segundo novo para cada quadro do coletor)
  return [[0, 700], [700, 0], [0, 0]].map(([bb, be], k) => { R.fixar(String(61 + k)); const q = Object.assign({}, base, { motor_bb_rpm: bb, motor_be_rpm: be }); delete q.simulado; window.CapitaoTelemetria = { atual: () => q };
    return { bb, be, fonte: B.instante().fonte, tel: B.answer('Telemetria agora', op).text, mot: B.answer('motores volvo penta', op).text }; }); }"""


def grupo_ligados(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        for x in pg.evaluate(JS_LIGADOS):
            quer = 'ligados' if x['bb'] or x['be'] else 'desligados'
            ped('ligados BB %s / BE %s: o instante é do coletor e os motores estão «%s» na telemetria e na resposta dos motores' % (x['bb'], x['be'], quer),
                x['fonte'] == 'coletor' and ('Motores %s —' % quer) in x['tel'] and ('Motores %s —' % quer) in x['mot'], (x['fonte'], x['tel'][-200:], x['mot'][:200]))
    finally:
        pg.ctx.close()


# nenhuma resposta de uma chave que não mostra a posição leva coordenada (graus-minutos NEM decimal, em par ou isolada: regex do §2.8, a mesma do gerador), em texto,
# fonte, fala e ficha, em vários instantes. A posição, a telemetria e a âncora a mostram na tela do app (decisão (g)). O milhar do rpm ("2.049/2.038 rpm") já foi lido como par.
CHAVES_COM_POSICAO = ('posicao', 'telemetria', 'ancora')
JS_COORDENADA = """([xs, casos]) => { const B = window.CapitaoBrain, R = window.CapitaoReplay;
  return xs.map((x) => { R.fixar(x); const r = casos.map(([q]) => { const a = B.answer(q, { platform: 'app', commit: false }); return [q, a.key, a.text, a.src, B.falaCurta(a)]; });
    return { x, r, ficha: B.ficha('app'), resumo: B.resumoAgora(), sem: B.resumoAgora({ semPosicao: true }) }; }); }"""


def grupo_coordenada(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); })")
        for x in pg.evaluate(JS_COORDENADA, [['60', '105', '0@10', '149@575'], [[q, k] for q, k in CASOS]]):
            ruins = [(q, k, m.group(0)) for q, k, tx, sr, fala in x['r'] if k not in CHAVES_COM_POSICAO for m in [confere.R_COORD.search(tx + '\n' + sr + '\n' + fala)] if m]
            ped('coordenada %s: nenhuma das %d respostas (texto, fonte e fala) fora da posição, da telemetria e da âncora leva coordenada' % (x['x'], len(x['r'])), not ruins and len(x['r']) == len(CASOS), ruins[:4])
            ped('coordenada %s: a ficha e o resumo não levam coordenada' % x['x'], not confere.R_COORD.search(x['ficha']) and not confere.R_COORD.search(x['resumo']) and not confere.R_COORD.search(x['sem']),
                [m.group(0) for s in (x['ficha'], x['resumo'], x['sem']) for m in [confere.R_COORD.search(s)] if m])
    finally:
        pg.ctx.close()


# o instante da resposta (`_inst`, lido pela ficha e pelo resumo da MESMA pergunta) tem o quadro com lat e lon: fora do JSON, das chaves e da cópia
# (as coordenadas não saem do aparelho, nos dois modos). O objeto é legível por quem o conhece, e só por ele.
JS_MARCA = """(casos) => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }, out = [];
  const olha = (nome, a) => out.push({ nome, inst: !!a._inst, chaves: Object.keys(a), json: JSON.stringify(a), copia: Object.assign({}, a)._inst !== undefined, espalha: ({ ...a })._inst !== undefined,
                                        clone: (() => { try { return JSON.stringify(structuredClone(a)); } catch (e) { return 'erro'; } })(), dentro: '_inst' in Object.assign({}, a), forin: (() => { const k = []; for (const x in a) k.push(x); return k; })() });
  casos.forEach((q) => olha(q, B.answer(q, op)));
  olha('anexo', B.answerAttachment('foto', { name: 'a.jpg', size: 2048 }, op));
  return out; }"""
PERGUNTAS_MARCA = ['telemetria', 'posição agora', 'autonomia', 'é seguro sair hoje?', 'MAYDAY, homem ao mar!']


def grupo_marca(b, muta, ped):
    for nome, kw in (('replay', {}), ('modo real', {'extra': SEM_SIMULACAO})):
        pg = pagina(b, muta=muta, **kw)
        try:
            for o in pg.evaluate(JS_MARCA, PERGUNTAS_MARCA):
                ped('marca (%s) «%s»: o instante da resposta (_inst) fica fora das chaves, do for-in, do JSON, da cópia e do clone' % (nome, o['nome']),
                    '_inst' not in o['chaves'] and '_inst' not in o['forin'] and '_inst' not in o['json'] and not re.search(r'"(?:lat|lon|q|ms)"\s*:', o['json']) and not o['copia'] and not o['espalha'] and not o['dentro'] and '_inst' not in o['clone'],
                    (o['chaves'], o['json'][:120]))
                if o['nome'] != 'MAYDAY, homem ao mar!':
                    ped('marca (%s) «%s»: o objeto ainda é legível pela ficha (a._inst existe)' % (nome, o['nome']), o['inst'], o['inst'])
                else:   # a resposta de emergência não leva o instante: a ficha e o resumo dela não leem o quadro (grupo emerg), e o `_inst` tem lat e lon
                    ped('marca (%s) «%s»: a resposta do SOS não leva o instante (_inst)' % (nome, o['nome']), not o['inst'], o['inst'])
        finally:
            pg.ctx.close()



# A API da resposta de emergência (CLAUDE.md 10; PROMPT §2.2): `B.answer` de uma chave de emergência não leva o instante (`_inst` tem o quadro e a posição) e o
# `resumoAgora(a)` e a `ficha(p, q, a)` que recebem essa resposta não leem o quadro, nem com o relógio andando depois da resposta (12:02:30). Os chamadores
# (a IA, o diário, a CONVERSA) não precisam lembrar da trava: a API a cumpre. Uma resposta de dado de bordo segue com o instante dela (o controle).
JS_EMERG = """(qs) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, D = window.CapitaoDados, op = { platform: 'app', commit: false };
  const titulos = (f) => (f.match(/^## .*$/mg) || []).map((t) => t.slice(3));
  const um = (q) => { R.fixar('60'); const a = B.answer(q, op); R.fixar('0@121');
    const r = B.resumoAgora(a), f = B.ficha('app', q, a), x = B.resumoAgora({ key: a.key }), y = B.ficha('app', q, { key: a.key });
    R.fixar('60'); return { q, key: a.key, inst: a._inst !== undefined, json: JSON.stringify(a), resumo: r, ficha: f, titulos: titulos(f), resumoMao: x, fichaMao: y }; };
  const out = { emerg: qs.map(um), plotter: D.protocolos.plotter };
  R.fixar('60'); const t = B.answer('telemetria', op); R.fixar('0@121');
  out.controle = { key: t.key, inst: t._inst !== undefined, resumo: B.resumoAgora(t), ficha: B.ficha('app', 'telemetria', t), titulos: titulos(B.ficha('app', 'telemetria', t)) };
  R.fixar('60'); out.sem = { resumo: B.resumoAgora(), ficha: B.ficha('app'), titulos: titulos(B.ficha('app')) };
  return out; }"""
QUADRO_DA_FICHA = ('Telemetria', 'Horímetros', 'Autonomia e consumo')   # os blocos da ficha que leem o quadro do instante (navegação, motores, diesel)
NAVEGACAO = re.compile(r'\bSOG\b|\bproa \d|\d rpm|Motores (?:ligados|desligados)|\bETA\b|Snapshot de \d|Leitura de \d')   # (P3B: a telemetria da reserva abre com «Leitura de 26/09/2026 10:12», não «Snapshot de»)


def grupo_emerg(b, muta, ped):
    for nome, kw in (('replay', {}), ('modo real', {'extra': SEM_SIMULACAO})):
        pg = pagina(b, muta=muta, **kw)
        try:
            e = pg.evaluate(JS_EMERG, PERGUNTAS_2_2)
            ped('emerg (%s): as perguntas cobrem sos, canal16, epirb, seafire, salvatagem e oleo' % nome,
                [r['key'] for r in e['emerg']] == CHAVES_2_2 and all(r['key'] in CHAVES_EMERGENCIA for r in e['emerg']), [r['key'] for r in e['emerg']])
            for r in e['emerg']:
                rot = 'emerg (%s) «%s» (%s)' % (nome, r['q'], r['key'])
                ped(rot + ': a resposta não leva o instante (_inst com o quadro e a posição)', not r['inst'] and not re.search(r'"(?:lat|lon|q|ms|hora)"\s*:', r['json']), r['json'][:120])
                for rotulo, resumo in (('resumoAgora(a)', r['resumo']), ('resumoAgora({ key })', r['resumoMao'])):
                    ped(rot + ': %s é a instrução do plotter, sem quadro (nem com o relógio andando)' % rotulo,
                        resumo == e['plotter'] and 'LEIA NO PLOTTER' in resumo and not NAVEGACAO.search(resumo) and not confere.R_COORD.search(resumo), resumo[:160])
                for rotulo, ficha, titulos in (('ficha(p, q, a)', r['ficha'], r['titulos']), ('ficha(p, q, { key })', r['fichaMao'], None)):
                    ts = titulos if titulos is not None else re.findall(r'^## (.*)$', ficha, re.M)
                    ped(rot + ': %s sai sem os blocos do quadro (Telemetria, Horímetros, Autonomia e consumo) e sem navegação, e segue com o resto' % rotulo,
                        not set(QUADRO_DA_FICHA) & set(ts) and not NAVEGACAO.search(ficha) and not confere.R_COORD.search(ficha)
                        and {'Agora', 'Embarcação', 'Manutenção', 'Emergência'} <= set(ts), (ts, NAVEGACAO.search(ficha) and NAVEGACAO.search(ficha).group(0)))
            # o controle: uma resposta de dado de bordo segue com o instante e com o quadro (a trava é só das chaves de emergência)
            c = e['controle']
            ped('emerg (%s): o controle (telemetria) leva o instante, o resumo do quadro e os blocos do quadro na ficha' % nome,
                c['key'] == 'telemetria' and c['inst'] and c['resumo'] != e['plotter'] and ('SOG' in c['resumo'] or nome == 'modo real') and set(QUADRO_DA_FICHA) <= set(c['titulos']) and bool(NAVEGACAO.search(c['ficha'])), (c['key'], c['inst'], c['resumo'][:80], c['titulos']))
            ped('emerg (%s): sem resposta, resumoAgora() e ficha() seguem completos (o quadro)' % nome,
                e['sem']['resumo'] != e['plotter'] and set(QUADRO_DA_FICHA) <= set(e['sem']['titulos']), (e['sem']['resumo'][:80], e['sem']['titulos']))
        finally:
            pg.ctx.close()


# ——————————————— Fase 3, P3B: as respostas sem rótulo ———————————————
# (PROMPT Fase 3 «Reescrever toda resposta com rótulo» e «Fallback»; decisões 3, 5 e 6; §2.5 tempo e maré reais; (g) as exceções do «toda resposta com dado»)
# Com simulacao true nenhuma resposta (texto, fonte nem fala) diz SEM DADOS, SEM LEITURA, MANUAL NO DRIVE, DEMO, «fictício», «simulado» nem «snapshot»: o dado vem do
# instante (quadro do replay) e a hora dele está na resposta. Com simulacao false a regra «Nada inventado» fica intacta (o caminho null → SEM DADOS / SEM LEITURA).
RX = confere.carrega_termos()
# a pergunta de exemplo de CADA chave de ANSWERS (o cérebro exporta B.CHAVES; uma chave nova sem exemplo reprova o teste)
PERGUNTA_CHAVE = {
    'saudacao': 'oi', 'diario': 'Registre no diário o resumo da navegação de agora e confirme.', 'seguro': 'é seguro sair hoje?', 'destinos': 'para onde vamos hoje?', 'manutencao': 'próximas manutenções',
    'autonomia': 'autonomia', 'mare': 'maré agora', 'clima': 'clima e vento', 'canal16': 'roteiro do canal 16', 'checklist': 'checklist de saída',
    'checklistChegada': 'checklist de chegada', 'consumo': 'consumo de diesel', 'tanques': 'nível dos tanques', 'contatos': 'quem chamar da equipe?', 'anomalias': 'pendências abertas',
    'porao': 'bombas de porão', 'gerador': 'quantas horas tem o gerador', 'telemetria': 'Telemetria agora', 'posicao': 'posição agora', 'docsvenc': 'documentos vencendo',
    'horimetros': 'horímetros', 'motores': 'motores', 'estabilizador': 'estabilizador Seakeeper', 'climatizacao': 'climatização', 'eletronicos': 'plotter garmin', 'audio': 'áudio fusion',
    'dessalinizador': 'dessalinizador', 'eletrico': 'bateria 24 v', 'epirb': 'onde fica o EPIRB?', 'seafire': 'onde fica o seafire', 'salvatagem': 'onde ficam os coletes?',
    'sos': 'MAYDAY, homem ao mar!', 'oleo': 'pressão de óleo baixa no motor BB', 'oleoLeitura': 'qual a pressão do óleo?', 'ancora': 'âncora garrando?', 'manual': 'guias de bordo',
    'diarioLer': 'diário de bordo', 'diagnostico': 'diagnóstico', 'fallback': 'como se faz um nó lais de guia?',
    # P3C: as rotas novas
    'sobreDados': 'esses dados são reais?', 'foraBarco': 'qual o preço do dólar?', 'mmsi': 'qual o MMSI do barco?', 'profundidade': 'qual a profundidade?', 'eta': 'qual a hora de chegada?',
    'alarmes': 'tem algum alarme ativo?', 'arrefecimento': 'qual a temperatura do motor?', 'ondas': 'como está o estado do mar?', 'temperaturaAgua': 'qual a temperatura da água?',
    'navegacao': 'como está a navegação?', 'pessoas': 'quantas pessoas a bordo?', 'embarcacao': 'qual o calado do barco?', 'ais': 'quantos alvos no AIS?',
    # P3E: as tendências (F11)
    'preditiva': 'quais as tendências?', 'pecas': 'quais peças temos a bordo?',
    'checklistFundeio': 'checklist de fundeio', 'checklistAbastecimento': 'checklist de abastecimento',
}
# as chaves cuja resposta não traz a hora do instante: emergência (nada do quadro), diagnóstico (do aparelho) e a saudação.
# Fase 3 (P3E, F09): os checklists saíram daqui — o item conferido pelo quadro muda com o instante («item conferido muda com o replay», PARIDADE F09), então a resposta traz a hora e os números dele
SEM_HORA = ('sos', 'oleo', 'salvatagem', 'epirb', 'seafire', 'canal16', 'mmsi', 'diagnostico', 'saudacao')
# as respostas cujos números mudam de 12:01:00 para 12:01:45 (vento, SOG, rpm, arrefecimento, volante, tensão, nível do porão, distância do destino, diesel)
MUDAM = ('telemetria', 'seguro', 'motores', 'oleoLeitura', 'clima', 'eletrico', 'estabilizador', 'gerador', 'posicao', 'tanques', 'porao', 'destinos', 'ancora', 'consumo', 'autonomia',
         'profundidade', 'eta', 'alarmes', 'arrefecimento', 'navegacao', 'sobreDados', 'foraBarco', 'preditiva',
         'checklist', 'checklistChegada', 'checklistFundeio', 'checklistAbastecimento')   # (P3C: a profundidade, a chegada, os alarmes, o arrefecimento e a navegação mudam de 12:01:00 para 12:01:45; a frase padrão e o «fora do barco» levam a situação de bordo)
VARREDURA = ('ROTULOS', 'AUTENTICIDADE', 'VAZIOS', 'VISIVEL', 'DINHEIRO')
# revisão da P3B (2ª): as DUAS linhas que o atalho do diário grava (o resumo sozinho e a nota com «posição e hora») ficam para sempre no registro (o diário só cresce): sem DEMO na fonte nem no texto com a
# simulação; com simulacao false e a flag antiga, o (DEMO) de antes na fonte
JS_DIARIO_ATALHO = """() => { const B = window.CapitaoBrain, op = { platform: 'app' };
  B.answer('Registre no diário o resumo da navegação de agora e confirme.', op); B.answer('registre no diário a posição e a hora, saída com 4 pessoas', op);
  return B.loadDiario().map((e) => ({ t: e.t, src: e.src, sys: e.sys })); }"""
JS_ROTULOS = """([xs, qs]) => { const B = window.CapitaoBrain, R = window.CapitaoReplay;
  return { chaves: B.CHAVES || null, r: xs.map((x) => { R.fixar(x); const i = B.instante();
    return { x, hora: i.hora, consumo: i.txt.consumo, aut: i.calc && i.calc.autonomia, r: Object.keys(qs).map((k) => { const a = B.answer(qs[k], { platform: 'app', commit: false }); return [k, a.key, a.text, a.src, B.falaCurta(a)]; }) }; }) }; }"""


def sem_hora(s):
    return re.sub(r'\d\d:\d\d:\d\d', '', s)


def varre_rotulos(ped, nome, out, completo=True):
    """Cada resposta do `out` (uma pergunta por chave, em cada instante): nenhuma das regex do §3 (ROTULOS, AUTENTICIDADE, VAZIOS, VISIVEL, DINHEIRO) no texto, na fonte nem na fala."""
    ruins = []
    for x in out['r']:
        for k, chave, texto, fonte, fala in x['r']:
            for n in VARREDURA:
                m = RX[n].search(texto + '\n' + fonte + '\n' + fala)
                if m:
                    ruins.append('%s %s %s «%s»' % (x['x'], k, n, m.group(0)))
    ped('%s: nenhuma das %d respostas (texto, fonte e fala), em %d instantes, casa ROTULOS, AUTENTICIDADE, VAZIOS, VISIVEL nem DINHEIRO' % (nome, len(PERGUNTA_CHAVE), len(out['r'])), not ruins, '%d: %s' % (len(ruins), ruins[:6]))


def grupo_rotulos(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        out = pg.evaluate(JS_ROTULOS, [['60', '105'], PERGUNTA_CHAVE])
        ped('rotulos: o cérebro exporta B.CHAVES e toda chave de ANSWERS tem a sua pergunta de exemplo (e a pergunta cai na chave)',
            out['chaves'] is not None and sorted(out['chaves']) == sorted(PERGUNTA_CHAVE) and all(c == k for x in out['r'] for k, c, *_ in x['r']),
            (out['chaves'] and sorted(set(out['chaves']) ^ set(PERGUNTA_CHAVE)), [(k, c) for k, c, *_ in out['r'][0]['r'] if c != k]))
        varre_rotulos(ped, 'rotulos', out)
        a, c = out['r']
        sem = []
        for (k, ka, ta, sa, fa), (_, kc, tc, sc, fc) in zip(a['r'], c['r']):
            if k in SEM_HORA:
                continue
            if not (a['hora'] in ta + sa and c['hora'] in tc + sc and re.search(r'\d', ta) and re.search(r'\d', tc)):
                sem.append(k)
        ped('rotulos: toda resposta de dado de bordo (fora %s) traz número e a hora do instante (12:01:00 e 12:01:45)' % ', '.join(SEM_HORA), not sem, sem)
        igual = [k for (k, _, ta, sa, _), (_, _, tc, sc, _) in zip(a['r'], c['r']) if k in MUDAM and sem_hora(ta + sa) == sem_hora(tc + sc)]
        ped('rotulos: os números mudam entre 12:01:00 e 12:01:45 onde devem (%s)' % ', '.join(MUDAM), not igual, igual)
        # revisão da P3B: o consumo e a autonomia são os do instante (txt.consumo e calc.autonomia, recalculados), em 12:01:00 e em 12:01:45; nenhum valor fixo no código
        ruins = []
        for x in out['r']:
            por = {k: t for k, _, t, _, _ in x['r']}
            if ('Consumo agora (%s): %s nos dois motores.' % (x['hora'], x['consumo'])) not in por['consumo']:
                ruins.append((x['hora'], 'consumo', x['consumo'], por['consumo'][:90]))
            quer = '≈ %s h · ≈ %d mn a ' % (('%.1f' % x['aut']['horas']).replace('.', ','), x['aut']['mn'])
            if quer not in por['autonomia']:
                ruins.append((x['hora'], 'autonomia', quer, por['autonomia'][:90]))
        ped('rotulos: o consumo agora e a autonomia (horas e milhas) da resposta são os do instante (txt.consumo e calc.autonomia), nos dois instantes', not ruins, ruins)
        fixas = [k for (k, _, ta, sa, _), (_, _, tc, sc, _) in zip(a['r'], c['r']) if k in SEM_HORA and ta != tc]
        ped('rotulos: a emergência, o diagnóstico e a saudação não mudam com o instante (os checklists mudam: F09)', not fixas, fixas)
    finally:
        pg.ctx.close()
    # a flag antiga (D.demo, D.selo, D.aviso) não põe rótulo em resposta nenhuma com simulacao true
    pg = pagina(b, muta=muta, extra=";window.CapitaoDados.demo = true; window.CapitaoDados.selo = 'DEMO'; window.CapitaoDados.aviso = 'dados fictícios';")
    try:
        out = pg.evaluate(JS_ROTULOS, [['60'], PERGUNTA_CHAVE])
        varre_rotulos(ped, 'rotulos (D.demo, D.selo e D.aviso ligados com simulacao true)', out)
        ficha = pg.evaluate("() => window.CapitaoBrain.ficha('app')")
        ped('rotulos (D.demo ligado com simulacao true): a ficha não diz DEMO nem o aviso', 'DEMO' not in ficha and 'fictícios' not in ficha, [l for l in ficha.split('\n') if 'DEMO' in l or 'fictícios' in l][:3])
        linhas = pg.evaluate(JS_DIARIO_ATALHO)
        ruim = [(l['src'], l['t'][:60]) for l in linhas if any(RX[n].search(l['src'] + '\n' + l['t']) for n in ('ROTULOS', 'VISIVEL')) or 'DEMO' in l['src'] + l['t']]
        ped('rotulos (D.demo ligado com simulacao true): as duas linhas gravadas pelo atalho do diário (resumo e «posição e hora») ficam sem DEMO e sem rótulo na fonte e no texto',
            len(linhas) == 2 and {l['src'] for l in linhas} == {'atalho · telemetria', 'chat · voz/texto · telemetria'} and not ruim, (ruim, linhas and [l['src'] for l in linhas]))
    finally:
        pg.ctx.close()
    # com simulacao false a regra antiga volta inteira: D.demo ligado põe o (DEMO) de antes na fonte
    pg = pagina(b, muta=muta, extra=SEM_SIMULACAO + ";window.CapitaoDados.demo = true;")
    try:
        t = pg.evaluate("() => { const a = window.CapitaoBrain.answer('Telemetria agora', { platform: 'app', commit: false }); return a.src + '\\n' + a.text; }")
        ped('rotulos (simulacao false com D.demo): o (DEMO) de antes volta (a regra «Nada inventado» fica intacta)', 'DEMO' in t, t[:160])
        linhas = pg.evaluate(JS_DIARIO_ATALHO)
        ped('rotulos (simulacao false com D.demo): as duas linhas do atalho do diário voltam a levar o (DEMO) na fonte',
            len(linhas) == 2 and {l['src'] for l in linhas} == {'atalho · telemetria (DEMO)', 'chat · voz/texto · telemetria (DEMO)'}, [l['src'] for l in linhas])
    finally:
        pg.ctx.close()


# decisão 6: com simulacao false o cérebro lê o D.snapshot e mantém o caminho null → SEM DADOS / SEM LEITURA, mesmo que hoje nada seja null
NULOS = (";(function () { var D = window.CapitaoDados; D.snapshot.porao = {}; delete D.snapshot.ancora; D.destinos = [];"
         " D.equipamentos.forEach(function (e) { if (e.id === 'motores') delete e.modelo; if (e.id === 'climatizacao') delete e.fabricante; if (e.id === 'dessalinizador') e.id = 'x'; }); })();")
JS_MODOS = """(qs) => { const B = window.CapitaoBrain; const out = {};
  Object.keys(qs).forEach((k) => { const a = B.answer(qs[k], { platform: 'app', commit: false }); out[k] = [a.key, a.text, a.src]; });
  out.ficha = B.ficha('app'); return out; }"""
PERGUNTAS_MODOS = {'porao': 'bombas de porão', 'ancora': 'âncora garrando?', 'motores': 'motores', 'climatizacao': 'climatização', 'dessalinizador': 'dessalinizador',
                   'destinos': 'para onde vamos hoje?', 'seguro': 'é seguro sair hoje?', 'mare': 'maré agora', 'clima': 'clima e vento', 'telemetria': 'Telemetria agora',
                   'fallback': 'como se faz um nó lais de guia?', 'contatos': 'quem chamar da equipe?', 'saudacao': 'oi'}


def grupo_modos(b, muta, ped):
    pg = pagina(b, muta=muta, extra=SEM_SIMULACAO + NULOS)
    try:
        r = pg.evaluate(JS_MODOS, PERGUNTAS_MODOS)
        t = lambda k: r[k][1]
        for nome, cond, extra in [
            ('modos (simulacao false): a bomba de porão sem leitura é SEM LEITURA', r['porao'][0] == 'porao' and 'SEM LEITURA' in t('porao'), t('porao')[:160]),
            ('modos (simulacao false): a âncora sem leitura é SEM LEITURA', r['ancora'][0] == 'ancora' and 'SEM LEITURA' in t('ancora'), t('ancora')[:160]),
            ('modos (simulacao false): o modelo que falta no dado é «modelo SEM DADOS» (motores)', 'modelo SEM DADOS' in t('motores'), t('motores')[:160]),
            ('modos (simulacao false): o fabricante que falta é SEM DADOS (climatização)', 'SEM DADOS' in t('climatizacao').split('\n')[0], t('climatizacao')[:160]),
            ('modos (simulacao false): o dessalinizador que não consta é SEM DADOS', 'SEM DADOS' in t('dessalinizador') and 'não consta na lista de equipamentos' in t('dessalinizador'), t('dessalinizador')[:160]),
            ('modos (simulacao false): sem destino cadastrado, SEM DADOS de rotas', 'SEM DADOS de rotas' in t('destinos'), t('destinos')[:160]),
            ('modos (simulacao false): sem a previsão carregada o seguro para sair diz SEM DADOS, como antes', 'Sem previsão de vento e mar carregada (SEM DADOS) — confira a previsão da Marinha antes de sair.' in t('seguro'), t('seguro')[-260:]),
            ('modos (simulacao false): sem a previsão e sem a maré, a regra antiga (SEM DADOS de maré, Previsão do dia: SEM DADOS)',
             'SEM DADOS de maré agora' in t('mare') and 'Previsão do dia: SEM DADOS' in t('clima'), (t('mare')[:100], t('clima')[:100])),
            ('modos (simulacao false): a telemetria segue na última leitura do coletor (26/09/2026 10:12), com o porão e a âncora SEM LEITURA do dado que falta',
             '26/09/2026 10:12' in t('telemetria') and 'Porão SEM LEITURA' in t('telemetria') and 'âncora SEM LEITURA' in t('telemetria'), t('telemetria')[-200:]),
            ('modos (simulacao false): o fallback também não diz SEM DADOS (a pergunta fora do barco)', r['fallback'][0] == 'fallback' and 'SEM DADOS' not in t('fallback') and 'Não encontrei esse dado' not in t('fallback'), t('fallback')[:160]),
            ('modos (simulacao false): a ficha traz o SEM DADOS do dado que falta', 'SEM DADOS' in r['ficha'] or 'SEM LEITURA' in r['ficha'], len(r['ficha'])),
        ]:
            ped(nome, cond, extra)
        sobre = r['ficha'][r['ficha'].find('## Sobre o app'):r['ficha'].find('## Embarcação')]
        # revisão da P3B (decisão 6): com simulacao false o «Sobre o app» que vai para a IA volta ao da 1.0.9: a regra da casa «Nada inventado», o snapshot do coletor, e nada de
        # «embarcação de apresentação», «roteiro» nem «mudam a cada segundo»
        ped('modos (simulacao false): o «Sobre o app» da ficha volta a «Regra da casa: nada inventado» (SEM DADOS, SEM LEITURA, A CONFERIR / A CONFIRMAR), sem a frase de sobreDados',
            'Regra da casa: nada inventado' in sobre and 'sem fonte = SEM DADOS; sensor ausente = SEM LEITURA' in sobre and SOBRE_DADOS not in sobre and 'apresentação' not in sobre and 'roteiro' not in sobre and 'a cada segundo' not in sobre, sobre[-420:])
        ped('modos (simulacao false): o «Sobre o app» fala do snapshot do coletor (ao vivo só com o coletor ligado), sem «telemetria ao vivo do coletor», e responde «com a fonte»',
            'telemetria (snapshot do coletor NMEA; ao vivo quando o coletor estiver ligado)' in sobre and 'telemetria ao vivo' not in sobre and 'que responde sempre com a fonte.' in sobre and 'destinos e hora de chegada' not in sobre, sobre[:700])
        ped('modos (simulacao false): a saudação não fala de telemetria ao vivo', 'Respondo sobre telemetria, manutenção' in t('saudacao') and 'ao vivo' not in t('saudacao'), t('saudacao'))
        ped('modos (simulacao false): os contatos abrem a situação com «Última situação de bordo:» (a leitura do coletor, não o quadro vivo)', 'Última situação de bordo: ' in t('contatos') and 'Situação de bordo agora' not in t('contatos'), t('contatos')[-300:])
    finally:
        pg.ctx.close()
    # os dados de verdade do snapshot (sem os nulos): a âncora lançada com o contador de corrente lido, no modo real
    pg = pagina(b, muta=muta, extra=SEM_SIMULACAO)
    try:
        r = pg.evaluate(JS_MODOS, {'ancora': 'âncora garrando?', 'telemetria': 'Telemetria agora'})
        ped('modos (simulacao false, dados do snapshot): a âncora lançada diz os metros de corrente do contador do guincho, na âncora e na telemetria',
            r['ancora'][1].startswith('Âncora lançada, com 30 m de corrente no contador do guincho — leitura de ') and 'âncora lançada, 30 m de corrente' in r['telemetria'][1] and 'SEM LEITURA' not in r['ancora'][1], (r['ancora'][1][:160], r['telemetria'][1][-200:]))
    finally:
        pg.ctx.close()
    # os mesmos nulos com simulacao true: o texto vem do quadro do replay (porão, âncora, destino, previsão) e só o que o dado de cadastro não tem segue SEM DADOS
    pg = pagina(b, muta=muta, extra=NULOS)
    try:
        r = pg.evaluate(JS_MODOS, PERGUNTAS_MODOS)
        t = lambda k: r[k][1]
        ped('modos (simulacao true, os mesmos nulos): porão, âncora e destino saem do quadro, sem SEM LEITURA nem SEM DADOS de rotas',
            'SEM' not in t('porao') + t('ancora') + t('destinos') and 'BB 1,1 cm' in t('porao'), (t('porao')[:120], t('ancora')[:120], t('destinos')[:120]))
        ped('modos (simulacao true, os mesmos nulos): o modelo que falta no cadastro continua SEM DADOS (o caminho null não se apaga)', 'modelo SEM DADOS' in t('motores'), t('motores')[:160])
    finally:
        pg.ctx.close()
    modos_cruzeiro(b, muta, ped)


def modos_cruzeiro(b, muta, ped):
    """revisão da P3B (2ª): o consumo de cruzeiro (nós e L/h do guia dos motores §10) que falta no dado. Nunca «undefined nós» nem «NaN»: com simulacao true o trecho «a N nós (L/h)» some;
    com simulacao false (regra «Nada inventado») o número é SEM DADOS, no cabeçalho e em cada destino."""
    NULO = ';window.CapitaoDados.consumo.cruzeiro = null;'
    JS = "() => { const a = window.CapitaoBrain.answer('para onde vamos hoje?', { platform: 'app', commit: false }); return { key: a.key, text: a.text, src: a.src }; }"
    for rotulo, extra, scripts, fixo, real in (('simulacao true, com o replay (em rota)', NULO, SCRIPTS, '60', False),
                                               ('simulacao true, sem o replay (o alcance)', NULO, ('capitao-dados.js', 'capitao-brain.js'), None, False),
                                               ('simulacao false', SEM_SIMULACAO + NULO, SCRIPTS, '60', True)):
        pg = pagina(b, muta=muta, extra=extra, scripts=scripts, fixo=fixo)
        try:
            d = pg.evaluate(JS)
            t = d['text']
            ped('modos (cruzeiro null, %s): destinos responde sem «undefined» nem «NaN» e lista os 4 destinos' % rotulo,
                d['key'] == 'destinos' and not re.search(r'undefined|NaN', t + d['src']) and len(re.findall(r'^\d\. ', t, re.M)) == 4, t[:400])
            if real:
                ped('modos (cruzeiro null, %s): SEM DADOS nos nós e nos L/h do cabeçalho e o tempo e o diesel de cada destino' % rotulo,
                    'a SEM DADOS nós (SEM DADOS L/h), só ida' in t and 'h a SEM DADOS nós, reserva' in t and t.count(' · tempo SEM DADOS · diesel SEM DADOS') == 4, t[:500])
            else:
                ped('modos (cruzeiro null, %s): o trecho «a N nós (L/h)» some, sem SEM DADOS e sem tempo nem diesel inventados' % rotulo,
                    'Destinos a partir da Barra Sul, só ida:' in t and 'SEM DADOS' not in t and not re.search(r' nós|L/h| min\b|≈ \d+ L\b', t), t[:500])
        finally:
            pg.ctx.close()


# prazos em tempo de execução: o dn de cada tarefa e de cada documento sai da data de vencimento contra o dia do instante (no fuso do barco), não do dn
# que o dado traz; a tarefa executada (capitao.executado.v1) sai da lista; a tarefa de um equipamento de segurança (EPIRB, Seafire) vai sem data (nota da etiqueta)
JS_PRAZOS = """() => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }, r = (q) => B.answer(q, op);
  return { man: r('próximas manutenções').text, docs: r('documentos vencendo').text, seguro: r('é seguro sair hoje?').text, anom: r('pendências abertas').text, ficha: B.ficha('app'),
           chk: r('checklist de saída').text, ia: B.instante().ms }; }"""
EXECUTA = """() => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }; B.markExec('porao-teste');
  return { man: B.answer('próximas manutenções', op).text, seguro: B.answer('é seguro sair hoje?', op).text, anom: B.answer('pendências abertas', op).text,
           chk: B.answer('checklist de saída', op).text, porao: B.answer('bombas de porão', op).text }; }"""


def numeros_de_prazo(texto):
    """(atrasos, prazos): os «em atraso há N dias» e os «D-N» da resposta, na ordem."""
    return [int(x) for x in re.findall(r'em atraso há (\d+) dias?', texto)], [int(x) for x in re.findall(r'\bD-(\d+)\b', texto)]


DOC_VENCIDO = ";window.CapitaoDados.documentos.push({ id: 'lic-teste', n: 'Licença vencida de teste', cat: 'Licenças', vence: '01/01/2026', st: 'VENCIDO' });"


def grupo_prazos(b, muta, ped):
    DIAS = 3
    base = pagina(b, extra=DOC_VENCIDO, muta=muta, scripts=('capitao-dados.js', 'capitao-brain.js'), fixo=None)
    desl = pagina(b, extra=DOC_VENCIDO, muta=muta, scripts=('capitao-dados.js', 'capitao-brain.js'), fixo=None)
    try:
        agora = desl.evaluate("() => Date.now()")
        # o relógio do aparelho anda 3 dias DEPOIS da carga (o rodapé não refaz os prazos): quem lê o dn do dado fica no dia da carga
        desl.add_script_tag(content=relogio(agora + DIAS * 86400000))
        x, y = base.evaluate(JS_PRAZOS), desl.evaluate(JS_PRAZOS)
        ax, px = numeros_de_prazo(x['man']); ay, py = numeros_de_prazo(y['man'])
        ped('prazos: a manutenção tem 3 atrasadas e prazos D-n na página sem o relógio deslocado (controle)', len(ax) == 3 and len(px) >= 2, (ax, px))
        ped('prazos: 3 dias depois da carga cada atraso cresce 3 dias e cada D-n cai 3 dias (o dn é contado do dia do instante, não do dado)',
            ay == [n + DIAS for n in ax] and py == [n - DIAS for n in px], (ax, ay, px, py))
        dx, dy = numeros_de_prazo(x['docs']), numeros_de_prazo(y['docs'])
        ped('prazos: os documentos também (Seguro D-n cai 3 dias)', dx[1] and dy[1] == [n - DIAS for n in dx[1]], (dx, dy))
        ped('prazos: a lista de atrasadas da manutenção, da ficha e do seguro para sair têm o mesmo número de atrasos na página deslocada',
            numeros_de_prazo(y['ficha'])[0][:3] == ay and len(numeros_de_prazo(y['seguro'])[0]) == 3 and numeros_de_prazo(y['seguro'])[0] == ay, (numeros_de_prazo(y['seguro']), ay))
        # Fase 3 (P3E, F09): o checklist de saída passou a ser o do D.checklists (sem o item da climatização): o atraso que ele conta é o da tarefa de SEGURANÇA atrasada (o teste das bombas de
        # porão, no item das tarefas de segurança e, com o quadro vivo, também no do porão), e continua contado do dia do instante
        pz, cx, cy = numeros_de_prazo(x['seguro'])[0][0], numeros_de_prazo(x['chk'])[0], numeros_de_prazo(y['chk'])[0]   # (o porão vem primeiro no seguro para sair)
        ped('prazos: o checklist de saída (itens do porão e das tarefas de segurança) conta o atraso do dia do instante',
            cx and cy and set(cx) == {pz} and set(cy) == {pz + DIAS} and len(cx) == len(cy), (cx, cy, pz))
        # a tarefa do EPIRB (equipamento de segurança): sem a data nem o D-n, com a nota da etiqueta
        for nome, t in (('manutenção', x['man']), ('ficha', x['ficha'])):
            ep = [l for l in t.split('\n') if 'Autoteste do EPIRB e validade' in l]
            ped('prazos (%s): a tarefa do EPIRB vai sem a data e sem o D-n, com a nota da etiqueta do equipamento' % nome,
                len(ep) == 1 and not re.search(r'\d\d/\d\d|\bD-\d', ep[0]) and 'veja a etiqueta do equipamento' in ep[0], ep)
        ped('prazos: a tarefa que não é de equipamento de segurança leva a data (limpeza de casco: D-n · dd/mm)', re.search(r'D-\d+ · \d\d/\d\d — Limpeza de casco', x['man']) is not None, x['man'][-300:])
        # revisão da P3B: a primeira ressalva é a de segurança (o porão) enquanto o teste está atrasado; o Executado tira a frase
        ped('prazos: o seguro para sair diz «a primeira é de segurança» com o teste do porão atrasado', 'a primeira é de segurança.' in x['seguro'].split('\n')[0], x['seguro'].split('\n')[0])
        # o documento vencido (a data no passado): «VENCIDO há N dias» contado do dia do instante, e cresce 3 dias na página deslocada
        vx, vy = re.findall(r'Licença vencida de teste — 01/01/2026 \(VENCIDO há (\d+) dias\)', x['docs']), re.findall(r'Licença vencida de teste — 01/01/2026 \(VENCIDO há (\d+) dias\)', y['docs'])
        ped('prazos: o documento vencido diz «VENCIDO há N dias» contado do dia do instante (3 dias depois, N + 3)', len(vx) == 1 and len(vy) == 1 and int(vx[0]) > 300 and int(vy[0]) == int(vx[0]) + DIAS, (vx, vy, x['docs'][:300]))
        # Executado: sai das atrasadas e dos números do seguro, do checklist e das pendências
        e = base.evaluate(EXECUTA)
        ped('prazos (Executado): a tarefa executada sai da lista (2 atrasadas, não 3), do seguro e do checklist; a pergunta do porão diz que foi executada',
            numeros_de_prazo(e['man'])[0] and len(numeros_de_prazo(e['man'])[0]) == 2 and 'Atrasadas (2)' in e['man'] and 'Teste das bombas' not in e['man']
            and len(numeros_de_prazo(e['seguro'])[0]) == 2 and 'Atrasadas na agenda: 2' in e['anom'] and 'executado' in e['porao'], (e['man'][:120], e['anom'][-60:], e['porao'][:120]))
        ped('prazos (Executado): depois do teste do porão o seguro para sair não diz mais «a primeira é de segurança» (as ressalvas que sobram, 2 atrasadas e a previsão, não são de segurança)',
            'a primeira é de segurança' not in e['seguro'] and e['seguro'].startswith('Sim, com 3 ressalvas.'), e['seguro'][:140])
    finally:
        base.ctx.close(); desl.ctx.close()
    prazos_executado(b, muta, ped)
    prazos_absolutos(b, muta, ped)
    prazos_tudo_executado(b, muta, ped)
    prazos_seguranca(b, muta, ped)


# revisão da P3B (3ª): todas as tarefas atrasadas marcadas como Executado: a manutenção diz «Nenhuma tarefa atrasada às HH:MM:SS.» (o ramo que nenhuma outra pergunta exercia), as pendências contam 0 e o
# seguro para sair fica com a única ressalva que sobra (a previsão), no singular e sem «a primeira é de segurança»
JS_TUDO_EXEC = """() => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }, r = (q) => B.answer(q, op), antes = r('próximas manutenções').text.split('\\n')[0];
  ['porao-teste', 'clima-filtro', 'gerador-rotor'].forEach((id) => B.markExec(id));
  const seg = r('é seguro sair hoje?'); return { antes, hora: B.instante().hora, man: r('próximas manutenções').text, seguro: seg.text, fala: B.falaCurta(seg), anom: r('pendências abertas').text, chk: r('checklist de saída').text }; }"""


def prazos_tudo_executado(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        x = pg.evaluate(JS_TUDO_EXEC)
        ped('prazos (tudo Executado, controle): antes de marcar a manutenção lista 3 atrasadas', x['antes'].startswith('Atrasadas (3) às '), x['antes'])
        ped('prazos (tudo Executado): a manutenção diz «Nenhuma tarefa atrasada às %s.», sem lista de atrasadas' % x['hora'], x['man'].startswith('Nenhuma tarefa atrasada às %s.\nPróximas:' % x['hora']) and 'Atrasadas (' not in x['man'], x['man'][:160])
        ped('prazos (tudo Executado): as pendências contam 0 atrasadas e o checklist não cita atraso', 'Atrasadas na agenda: 0' in x['anom'] and 'em atraso' not in x['chk'], (x['anom'][-60:], x['chk'][:200]))
        ok, n_lidas, n_mais, n = confere_fala_seguro(x['seguro'], x['fala'])
        ped('prazos (tudo Executado): o seguro para sair fica com 1 ressalva (a previsão), no singular, sem «a primeira é de segurança», e a fala fecha a conta',
            x['seguro'].startswith('Sim, com 1 ressalva.\n') and 'primeira é de segurança' not in x['seguro'] and ok and n == 1 and n_lidas == 1 and n_mais == 0, (x['seguro'][:100], x['fala']))
    finally:
        pg.ctx.close()


# a tarefa de um equipamento de segurança que cai num prazoTxt (aqui o anodo do estabilizador passa a ser do EPIRB): o prazo é a nota da etiqueta, nunca «D-n · dd/mm»
SEG_ANODO = ";window.CapitaoDados.agenda.forEach(function (t) { if (t.id === 'seakeeper-anodo') t.sistema = 'epirb'; });"


def prazos_seguranca(b, muta, ped):
    for nome, extra, quer in (('tarefa comum (controle)', '', False), ('tarefa de equipamento de segurança', SEG_ANODO, True)):
        pg = pagina(b, muta=muta, extra=extra)
        try:
            e = pg.evaluate("() => window.CapitaoBrain.answer('estabilizador Seakeeper', { platform: 'app', commit: false }).text")
            linha = [l for l in e.split('\n') if l.startswith('Anodo do trocador de calor')]
            ped('prazos (anodo do estabilizador como %s): %s' % (nome, 'sem a data nem o D-n, com a nota da etiqueta' if quer else 'D-n · dd/mm'),
                len(linha) == 1 and (re.search(r'D-\d|\d\d/\d\d', linha[0]) is None and 'veja a etiqueta do equipamento' in linha[0] if quer else re.search(r': D-\d+ · \d\d/\d\d\.$', linha[0]) is not None), linha)
        finally:
            pg.ctx.close()


# revisão da P3B (2ª): a troca de óleo, a revisão do gerador e a inspeção do rotor marcadas como Executado (Leme) saem das respostas dos motores, dos horímetros e do gerador:
# nada de «Próxima troca…», de «ou 450 h — faltam 32,4 h» nem de «(executado em …)» de um ciclo que já acabou; o texto concorda com o gênero da tarefa («troca … executada»)
JS_EXEC = """() => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }, r = (q) => B.answer(q, op).text, tudo = () => ({ mot: r('motores'), hor: r('horímetros'), ger: r('quantas horas tem o gerador'), man: r('próximas manutenções') });
  const antes = tudo(); ['motores-oleo', 'gerador-revisao', 'gerador-rotor'].forEach((id) => B.markExec(id)); return { antes, depois: tudo() }; }"""
EXEC_EM = r'executad[oa] em \d\d/\d\d às \d\d:\d\d'


def prazos_executado(b, muta, ped):
    pg = pagina(b, muta=muta, scripts=('capitao-dados.js', 'capitao-brain.js'), fixo=None)
    try:
        x = pg.evaluate(JS_EXEC)
        a, d = x['antes'], x['depois']
        ped('prazos (Executado, controle): sem execução os motores, os horímetros e o gerador dizem a próxima troca, o «ou 450 h» e o «faltam … h»',
            'troca de óleo D-' in a['mot'] and ' ou 450 h' in a['mot'] and 'Próxima troca de óleo dos motores: ' in a['hor'] and 'faltam' in a['hor'] and 'Revisão (óleo e filtros): ' in a['ger'] and 'faltam' in a['ger'],
            (a['mot'][-200:], a['hor'][-260:], a['ger'][-200:]))
        ped('prazos (Executado): os motores dizem «troca de óleo executada em dd/mm às hh:mm.» (feminino), sem o prazo nem o «ou 450 h» do ciclo que acabou',
            re.search(r'troca de óleo ' + EXEC_EM.replace('executad[oa]', 'executada') + r'\.\n', d['mot']) is not None and ' ou 450 h' not in d['mot'] and 'D-' not in d['mot'].split('Horímetros')[1].split('\n')[0],
            d['mot'][-260:])
        ped('prazos (Executado): os horímetros dizem «Troca de óleo dos motores: executada em …» e «Revisão do gerador: executada em …», sem «Próxima troca», sem «faltam» e sem «(executado em …)»',
            re.search(r'\nTroca de óleo dos motores: ' + EXEC_EM.replace('executad[oa]', 'executada') + r'\.', d['hor']) is not None
            and re.search(r'\nRevisão do gerador: ' + EXEC_EM.replace('executad[oa]', 'executada') + r'\.', d['hor']) is not None
            and 'Próxima troca' not in d['hor'] and 'faltam' not in d['hor'] and '(executad' not in d['hor'], d['hor'][-300:])
        ped('prazos (Executado): o gerador diz «Inspeção do rotor (impeller) do gerador: executada em …» e «Revisão (óleo e filtros): executada em …», sem «faltam» nem o prazo antigo',
            re.search(r'Inspeção do rotor \(impeller\) do gerador: ' + EXEC_EM.replace('executad[oa]', 'executada') + r'\.', d['ger']) is not None
            and re.search(r'Revisão \(óleo e filtros\): ' + EXEC_EM.replace('executad[oa]', 'executada') + r'\.', d['ger']) is not None and 'faltam' not in d['ger'] and '1.300 h' not in d['ger'], d['ger'][-300:])
        ped('prazos (Executado): a manutenção também não lista a troca de óleo, a revisão nem o rotor executados (nem o «Óleo e filtros dos motores: … faltam»)',
            'Óleo e filtros dos motores' not in d['man'] and 'Troca de óleo e filtros' not in d['man'] and 'rotor (impeller)' not in d['man'], d['man'][:300])
    finally:
        pg.ctx.close()


# revisão da P3B (2ª): o VALOR ABSOLUTO do prazo e o fuso. Dois instantes em que o dia do barco difere do dia UTC (e do do relógio): (1) o relógio em 02/11/2026 23:30 em Brasília, quando o dia
# UTC já é 03/11; (2) o relógio em 02/11 12:00 com o replay em 149@575 (06:59:59 de 03/11): o instante do cérebro (B.instante().ms) é de outro dia que o Date.now(). Cada «em atraso há N»,
# cada «D-n · dd/mm» e cada «VENCIDO há N» é o dn que o rodapé gravou no dado (venceEm, do dia do barco) — e o documento vencido em 01/01/2026 diz o número do calendário
RELOGIO_23H30 = calendar.timegm((2026, 11, 3, 2, 30, 0)) * 1000    # 02/11/2026 23:30 em Brasília (UTC-3)
RELOGIO_12H00 = calendar.timegm((2026, 11, 2, 15, 0, 0)) * 1000    # 02/11/2026 12:00 em Brasília
JS_PRAZOS_ABS = """() => { const B = window.CapitaoBrain, D = window.CapitaoDados, A = window.CapitaoAgora, op = { platform: 'app', commit: false }, r = (q) => B.answer(q, op).text;
  const seg = (t) => { const e = D.equipamentos.filter((x) => x.id === t.sistema)[0]; return !!(e && e.seguranca); };
  const i = B.instante();
  return { hoje: A.relogio.hoje, utc: new Date().toISOString().slice(0, 10), hora: i && i.hora, segDocs: D.equipamentos.filter((e) => e.seguranca).map((e) => e.validade),
    agenda: D.agenda.map((t) => ({ id: t.id, t: t.t, equip: t.equip, quem: t.quem, dn: t.dn, vence: t.vence, seg: seg(t), seguranca: t.seguranca === true })), docs: D.documentos.map((d) => ({ id: d.id, n: d.n, dn: typeof d.dn === 'number' ? d.dn : null, vence: d.vence })),
    man: r('próximas manutenções'), docsT: r('documentos vencendo'), seguro: r('é seguro sair hoje?'), chk: r('checklist de saída') }; }"""


def esperados_de_prazo(x):
    """(linhas da manutenção, linhas dos documentos, atrasos): o que a página tem de dizer, calculado do dn que o rodapé gravou no dado (independente do cérebro)."""
    ag = sorted(x['agenda'], key=lambda t: (t['dn'], t['id']))
    atras = [t for t in ag if t['dn'] < 0]
    prox = [t for t in ag if t['dn'] >= 0][:3]
    nota = 'modelo, validade e acionamento: veja a etiqueta do equipamento'
    linhas = ['• %s · %s — em atraso há %d %s (%s)' % (t['t'], t['equip'], -t['dn'], 'dia' if t['dn'] == -1 else 'dias', t['quem']) for t in atras]
    linhas += [('• %s (%s) — %s' % (t['t'], t['quem'], nota)) if t['seg'] else ('• D-%d · %s — %s (%s)' % (t['dn'], t['vence'][:5], t['t'], t['quem'])) for t in prox]
    docs = ['• %s — %s (%s)' % (d['n'], d['vence'], ('VENCIDO há %d %s' % (-d['dn'], 'dia' if d['dn'] == -1 else 'dias')) if d['dn'] < 0 else 'D-%d' % d['dn'])
            for d in x['docs'] if d['dn'] is not None and d['dn'] <= 90 and d['id'] not in x['segDocs']]
    return linhas, docs, atras


def confere_absolutos(ped, nome, x, hoje, utc, vencido):
    linhas, docs, atras = esperados_de_prazo(x)
    pos = [x['man'].find(l) for l in linhas]
    ped('prazos (%s): o fuso do teste é o esperado (rodapé em %s, relógio UTC em %s) e há 3 atrasadas e prazos D-n' % (nome, hoje, utc),
        x['hoje'] == hoje and x['utc'] == utc and len(atras) == 3 and len(linhas) == 6, (x['hoje'], x['utc'], len(atras), len(linhas)))
    ped('prazos (%s): cada atrasada e cada próxima da manutenção traz EXATAMENTE o dn do dado (em atraso há N · D-n · dd/mm), na ordem' % nome,
        all(p >= 0 for p in pos) and pos == sorted(pos) and ('Atrasadas (%d)' % len(atras)) in x['man'], [l for l, p in zip(linhas, pos) if p < 0] or x['man'][:300])
    atraso = lambda t: [int(n) for n in re.findall(r'em atraso há (\d+) dias?', t)]
    seg_ord = [t for t in atras if t['id'] == 'porao-teste'] + [t for t in atras if t['id'] != 'porao-teste']   # a ressalva de segurança (o porão) vem primeiro
    # Fase 3 (P3E, F09): o checklist de saída passou a ser o do D.checklists: o atraso que ele conta é o da tarefa de segurança (o porão), no item das tarefas de segurança (e no do porão com o quadro vivo)
    chk_ord = [t for t in atras if t['seguranca']]
    ped('prazos (%s): o seguro para sair (o porão primeiro) e o checklist de saída (itens do porão e das tarefas de segurança) contam os atrasos do dado' % nome,
        atraso(x['seguro']) == [-t['dn'] for t in seg_ord] and chk_ord and atraso(x['chk']) and set(atraso(x['chk'])) == {-t['dn'] for t in chk_ord}, (atraso(x['seguro']), atraso(x['chk']), [-t['dn'] for t in seg_ord], [-t['dn'] for t in chk_ord]))
    ped('prazos (%s): cada documento que vence em até 90 dias traz o vencimento e o D-n do dado' % nome, all(l in x['docsT'] for l in docs) and len(docs) >= 2, [l for l in docs if l not in x['docsT']] or x['docsT'][:300])
    ped('prazos (%s): o documento vencido em 01/01/2026 diz «VENCIDO há %d dias» (a conta do calendário: %s)' % (nome, vencido, hoje),
        ('Licença vencida de teste — 01/01/2026 (VENCIDO há %d dias)' % vencido) in x['docsT'], re.findall(r'Licença vencida[^\n]*', x['docsT']))


def prazos_absolutos(b, muta, ped):
    # (1) o fuso: 23:30 em Brasília de 02/11 (UTC já em 03/11), sem replay (o instante é o Date.now())
    pg = pagina(b, extra=DOC_VENCIDO, muta=muta, scripts=('capitao-dados.js', 'capitao-brain.js'), fixo=None, relogio_ms=RELOGIO_23H30)
    try:
        x = pg.evaluate(JS_PRAZOS_ABS)
        confere_absolutos(ped, 'fuso: 23:30 de 02/11, UTC em 03/11', x, '02/11/2026', '2026-11-03', (datetime.date(2026, 11, 2) - datetime.date(2026, 1, 1)).days)
    finally:
        pg.ctx.close()
    # (2) o instante do cérebro: o replay em 149@575 (06:59:59 de 03/11) com o relógio em 02/11 12:00: o dia do B.instante().ms não é o do Date.now()
    pg = pagina(b, extra=DOC_VENCIDO, muta=muta, fixo='149@575', relogio_ms=RELOGIO_12H00)
    try:
        x = pg.evaluate(JS_PRAZOS_ABS)
        ped('prazos (replay em 149@575): o instante do cérebro é 06:59:59', x['hora'] == '06:59:59', x['hora'])
        confere_absolutos(ped, 'replay 149@575: 06:59:59 de 03/11, relógio em 02/11', x, '03/11/2026', '2026-11-02', (datetime.date(2026, 11, 3) - datetime.date(2026, 1, 1)).days)
    finally:
        pg.ctx.close()


# tempo e maré são do mundo real (§2.5): sem conexão e sem leitura salva, a frase do §2.5 e a situação de bordo sem posição (decisão (g)); com a leitura de hoje, a previsão
SEM_CONEXAO = 'Previsão e maré: sem conexão agora'
BOLETIM = 'confira o boletim da Marinha antes de sair.'
JS_TEMPO = """() => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }, r = (q) => { const a = B.answer(q, op); return { key: a.key, text: a.text, src: a.src, fala: B.falaCurta(a) }; };
  return { clima: r('clima e vento'), mare: r('maré agora'), seguro: r('é seguro sair hoje?'), sem: B.resumoAgora({ semPosicao: true }), ficha: B.ficha('app'), hora: B.instante().hora }; }"""


def grupo_tempo(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        t = pg.evaluate(JS_TEMPO)
        for k in ('clima', 'mare', 'seguro'):
            tx = t[k]['text']
            ped('tempo (%s): sem conexão e sem leitura salva a frase do §2.5, sem «última às» e sem SEM DADOS' % k,
                SEM_CONEXAO + ' — ' + BOLETIM in tx and '(última às' not in tx and 'SEM DADOS' not in tx and 'SEM DADOS' not in t[k]['fala'], tx[:260])
        for k in ('clima', 'mare'):
            ped('tempo (%s): a frase do §2.5 abre a resposta (é a 1ª linha, a falada) e a situação de bordo sem posição, com a hora, vem logo depois' % k,
                t[k]['text'].split('\n')[0] == SEM_CONEXAO + ' — ' + BOLETIM and t['sem'] in t[k]['text'] and t['hora'] in t['sem'] and t[k]['fala'].startswith(SEM_CONEXAO), (t[k]['text'][:300], t['sem']))
        ped('tempo (mare): a maré mantém «modelo, não é a tábua oficial da Marinha (DHN)»', 'não é a tábua oficial da Marinha (DHN)' in t['mare']['text'], t['mare']['text'])
        ped('tempo (seguro): a ressalva da previsão diz «confira o boletim da Marinha antes de sair» e o vento do quadro vai como «a bordo agora», não na decisão',
            BOLETIM in t['seguro']['text'] and 'a bordo agora' in t['seguro']['text'], t['seguro']['text'][:420])
        ped('tempo: a ficha (Clima e maré) usa a mesma frase, sem SEM DADOS', SEM_CONEXAO in t['ficha'] and '## Clima e maré' in t['ficha'], t['ficha'][t['ficha'].find('## Clima'):][:300])
    finally:
        pg.ctx.close()
    # a última leitura salva, com a hora dela (a leitura de ontem: sem a previsão de hoje, «última às HH:MM»), e a maré salva
    ctx = b.new_context()
    ctx.route('https://*.open-meteo.com/**', lambda rt: rt.abort('internetdisconnected'))
    if muta:   # o cérebro mutante também aqui (o mesmo desvio da pagina())
        def entrega(route):
            r = route.fetch()
            corpo = r.text()
            assert corpo.count(muta[0]) == 1, 'o trecho do mutante não está (uma vez) no cérebro: ' + muta[0]
            route.fulfill(response=r, body=corpo.replace(muta[0], muta[1], 1))
        ctx.route('**/capitao-brain.js', entrega)
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.goto(BASE + 'base-conhecimento.json')
    try:
        for arq in ('capitao-dados.js', 'capitao-replay.js', 'capitao-alertas.js', 'capitao-telemetria.js', 'capitao-clima.js'):
            pg.add_script_tag(url=BASE + arq)
        pg.evaluate("() => window.CapitaoReplay.fixar('60')")
        pg.add_script_tag(url=BASE + 'capitao-brain.js')
        hora = pg.evaluate(SEMEIA, {'desloca': -86400e3, 'max': 30, 'min': 20, 'vento': 25, 'raj': 33, 'dir': 180, 'modelo': 'ECMWF'})
        t = pg.evaluate(JS_TEMPO)
        for k in ('clima', 'mare', 'seguro'):
            ped('tempo (%s): só a leitura de ontem: «(última às %s)» na frase do §2.5' % (k, hora), SEM_CONEXAO + ' (última às ' + hora + ') — ' + BOLETIM in t[k]['text'], t[k]['text'][:260])
        # a leitura de hoje: a previsão real na 1ª linha do clima e no seguro para sair, e as ondas sem previsão no app (nunca SEM DADOS, nunca o vento do quadro na decisão)
        pg.evaluate(SEMEIA, {'desloca': 0, 'max': 27.4, 'min': 18.2, 'vento': 12.3, 'raj': 19.4, 'dir': 48, 'modelo': 'ECMWF'})
        t = pg.evaluate(JS_TEMPO)
        ped('tempo (clima com a leitura de hoje): a previsão real abre a resposta (máx, mín, vento, rajada) e não há a frase de «sem conexão»',
            t['clima']['text'].startswith('Hoje em Balneário Camboriú: máx 27° · mín 18° · vento até 12 nós de nordeste, rajadas até 19 nós') and SEM_CONEXAO not in t['clima']['text'] and 'SEM DADOS' not in t['clima']['text'], t['clima']['text'][:260])
        ped('tempo (seguro com a leitura de hoje): a previsão real e as ondas «o app não tem previsão de mar», sem SEM DADOS e sem a frase de «sem conexão»',
            ('rajadas até 19 nós' + MAR) in t['seguro']['text'] and SEM_CONEXAO not in t['seguro']['text'] and 'SEM DADOS' not in t['seguro']['text'], t['seguro']['text'][-300:])
        # revisão da P3B (decisão 3, PROMPT §3): a leitura do dia que vem SEM A RAJADA ou SEM O VENTO (o Open-Meteo não trouxe) não escreve SEM DADOS com simulacao true — nem no clima, no seguro,
        # na fala nem na ficha da IA —; com simulacao false volta a regra «Nada inventado» (rajadas SEM DADOS · vento SEM DADOS)
        bloco_clima = lambda f: f[f.find('## Clima e maré'):f.find('\n## ', f.find('## Clima e maré') + 5)]
        for rot, c, quer, real in (('sem a rajada', {'desloca': 0, 'max': 27.4, 'min': 18.2, 'vento': 12.3, 'dir': 48, 'modelo': 'ECMWF'}, 'vento até 12 nós de nordeste', 'vento até 12 nós de nordeste, rajadas SEM DADOS'),
                                   ('sem o vento', {'desloca': 0, 'max': 27.4, 'min': 18.2, 'modelo': 'ECMWF'}, 'sem previsão de vento nesta leitura', 'vento SEM DADOS')):
            pg.evaluate(SEMEIA, dict(c))
            t = pg.evaluate(JS_TEMPO)
            todos = [t[k][c2] for k in ('clima', 'seguro') for c2 in ('text', 'src', 'fala')] + [bloco_clima(t['ficha'])]
            ruim = [n for n in ('ROTULOS', 'VAZIOS') for x in todos if RX[n].search(x)]
            ped('tempo (leitura do dia %s, simulacao true): clima, seguro, fala e ficha dizem «%s» sem SEM DADOS e sem inventar a parte que falta' % (rot, quer),
                not ruim and quer in t['clima']['text'] and quer in t['seguro']['text'] and quer in bloco_clima(t['ficha']) and quer in t['clima']['fala'] + t['clima']['text'].split('\n')[0]
                and (rot != 'sem a rajada' or 'rajada' not in ' '.join(todos).lower()) and (rot != 'sem o vento' or all('vento até' not in x for x in todos)), (ruim, t['clima']['text'][:200]))
            pg.evaluate("() => { window.CapitaoDados.simulacao = false; }")
            t = pg.evaluate(JS_TEMPO)
            ped('tempo (leitura do dia %s, simulacao false): a regra «Nada inventado» volta, «%s» no clima, no seguro e na ficha' % (rot, real),
                real in t['clima']['text'] and real in t['seguro']['text'] and real in bloco_clima(t['ficha']), (t['clima']['text'][:200], t['seguro']['text'][-200:]))
            pg.evaluate("() => { window.CapitaoDados.simulacao = true; }")
        # maré salva (série de hora em hora em volta de agora): a maré do modelo, sem «Corrente: SEM DADOS»
        pg.evaluate("""() => { const t0 = Math.floor(Date.now() / 3600e3) * 3600e3, s = []; for (let h = -3; h <= 30; h++) s.push([t0 + h * 3600e3, 0.3 + 0.2 * Math.sin(h / 2)]);
          localStorage.setItem('capitao.mare.v1', JSON.stringify({ em: Date.now() - 600e3, serie: s })); }""")
        pg.reload()
        for arq in ('capitao-dados.js', 'capitao-replay.js', 'capitao-alertas.js', 'capitao-telemetria.js', 'capitao-clima.js'):
            pg.add_script_tag(url=BASE + arq)
        pg.evaluate("() => window.CapitaoReplay.fixar('60')")
        pg.add_script_tag(url=BASE + 'capitao-brain.js')
        m = pg.evaluate("() => { const a = window.CapitaoBrain.answer('maré agora', { platform: 'app', commit: false }); return { text: a.text, src: a.src, fala: window.CapitaoBrain.falaCurta(a) }; }")
        ped('tempo (mare com a maré salva): maré do modelo com as próximas horas, sem a frase de «sem conexão», sem «Corrente: SEM DADOS», e o modelo não é a tábua da Marinha',
            m['text'].startswith('Maré agora ') and 'Próximas horas:' in m['text'] and SEM_CONEXAO not in m['text'] and 'SEM DADOS' not in m['text'] + m['fala'] and 'não a tábua oficial da Marinha' in m['text'], m['text'][:300])
        # revisão da P3B (3ª): a maré é REAL (§2.5, decisão 12): a hora na fonte é a da leitura salva («lida às HH:MM», como a previsão do clima), nunca a do instante do replay («consultado às 12:01:00»)
        lida = pg.evaluate("() => { const v = JSON.parse(localStorage.getItem('capitao.mare.v1')); return new Intl.DateTimeFormat('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(v.em)); }")
        ped('tempo (mare com a maré salva): a fonte diz a hora da leitura salva («lida às %s»), sem o carimbo do replay (nenhum «consultado às» nem HH:MM:SS na fonte)' % lida,
            m['src'].endswith(' · lida às ' + lida) and 'consultado' not in m['src'] and not re.search(r'\d\d:\d\d:\d\d', m['src']), m['src'])
        pg.evaluate("() => { window.CapitaoDados.simulacao = false; }")
        m = pg.evaluate("() => { const a = window.CapitaoBrain.answer('maré agora', { platform: 'app', commit: false }); return { text: a.text, src: a.src }; }")
        ped('tempo (mare com a maré salva, simulacao false): a fonte volta a ser a de antes (sem a hora da leitura), a regra «Nada inventado» fica intacta', 'lida às' not in m['src'] and 'consultado' not in m['src'] and m['text'].startswith('Maré agora '), m['src'])
        pg.evaluate("() => { window.CapitaoDados.simulacao = true; }")
        ped('tempo: sem erro de script', not erros, erros)
    finally:
        ctx.close()


# as demais respostas: o texto sai do dado (fabricante, modelo, horas da agenda, guias, rota), nunca de um estado fixo no código
JS_TEXTOS = """() => { const B = window.CapitaoBrain, D = window.CapitaoDados, op = { platform: 'app', commit: false }, r = (q) => B.answer(q, op), i = B.instante();
  const f = B.ficha('app'), sobre = f.slice(f.indexOf('## Sobre o app'), f.indexOf('## Embarcação'));
  return { tx: i.txt, motores: r('motores').text, oleoL: r('qual a pressão do óleo?').text, clima: r('climatização').text, eletr: r('plotter garmin').text, audio: r('áudio fusion').text,
    dessal: r('dessalinizador').text, docs: r('documentos vencendo').text, contatos: r('quem chamar da equipe?').text, destinos: r('para onde vamos hoje?'), ancora: r('âncora garrando?'),
    porao: r('bombas de porão').text, chk: r('checklist de saída').text, saud: r('oi').text, fallback: r('como se faz um nó lais de guia?'), foto: B.answerAttachment('foto', { name: 'a.jpg', size: 2048 }, { platform: 'app' }).text,
    video: B.answerAttachment('video', { name: 'a.mp4', size: 4096 }, { platform: 'app' }).text, sobre, sobreDados: B.SOBRE_DADOS || null, estab: r('estabilizador Seakeeper').text,
    convite: (B.linkConvite('Ana', '+55 47 99999-0000', 'total') || {}).href || '', cons: r('consumo de diesel').text, aut: r('autonomia').text, hor: r('horímetros').text,
    consSrc: r('consumo de diesel').src, autSrc: r('autonomia').src, zonas: ((D.equipamentos.filter((e) => e.id === 'audio')[0] || {}).nominal || {}).zonas, anodo: (D.agenda.filter((t) => t.id === 'seakeeper-anodo')[0] || {}).t,
    consFonte: D.consumo.fonte, consPeriodo: D.consumo.periodo, epirbDoc: D.documentos.filter((d) => d.id === 'doc-epirb')[0] || null,
    diaMotor: D.diario.filter((x) => x.ref === 'clima-filtro').map((x) => x.d + '|' + x.t), eqs: D.equipamentos.map((e) => [e.id, e.fabricante, e.modelo]), ficha: f,
    seguranca: D.equipamentos.filter((e) => e.seguranca).map((e) => ({ id: e.id, nome: e.nome, fabricante: e.fabricante, modelo: e.modelo, palavras: e.palavras || [] })),
    reg: D.replay.limites.motor_bb_oleo_bar.regimes[1], reserva: D.reserva, margem: D.consumo.margemManobra_l, nos: D.consumo.cruzeiro.nos, lph: D.consumo.cruzeiro.lph, dest: D.destinos, prof: i.q.profundidade_m }; }"""
# o alarme ativo (12:01:45: AVISO de arrefecimento) e o crítico de um coletor de verdade: o «seguro para sair» diz «Sim» com a ressalva, e «Não» com o crítico
JS_ALARME_SEGURO = """() => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false }, out = {};
  R.fixar('105'); const a105 = B.answer('é seguro sair hoje?', op); out.aviso = a105.text; out.avisoFala = B.falaCurta(a105);
  R.fixar('60'); const a60 = B.answer('é seguro sair hoje?', op); out.normal = a60.text; out.normalFala = B.falaCurta(a60); const q = Object.assign({}, R.em(R.agora()), { alarmes: [{ id: 'oleo_bb', nivel: 'critico', sistema: 'motores', lado: 'bb', campo: 'motor_bb_oleo_bar', valor: 0.5, limite: 1.4, desde: '2026-10-27T15:01:00Z' }] }); delete q.simulado;
  window.CapitaoTelemetria = { atual: () => q }; R.fixar('61'); out.critico = B.answer('é seguro sair hoje?', op).text; return out; }"""
JS_TELE = """() => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false }, out = {};
  ['60', '105'].forEach((x) => { R.fixar(x); const i = B.instante(); out[x] = { text: B.answer('Telemetria agora', op).text, alarmes: i.txt.alarmes, tend: i.txt.tend }; }); R.fixar('60'); return out; }"""


def confere_fala_seguro(texto, fala):
    """(ok, listadas, mais, n): a fala do «seguro para sair» lê as primeiras ressalvas e diz quantas ficaram na tela; listadas + mais = o n do «com n ressalvas»."""
    m = re.match(r'Sim, com (\d+) ressalvas?', texto)
    if not m or ': ' not in fala:
        return False, 0, 0, None
    partes = fala[fala.index(': ') + 2:].rstrip('.').split('; ')
    mais = 0
    if partes[-1].startswith('e mais '):
        k = re.fullmatch(r'e mais (\d+) (ressalvas?) na tela', partes[-1])   # «e mais 1 ressalva na tela» / «e mais 3 ressalvas na tela»: o plural concorda com o número
        if not k or (k.group(2) == 'ressalva') != (k.group(1) == '1'):
            return False, len(partes) - 1, 0, int(m.group(1))
        mais = int(k.group(1))
        partes = partes[:-1]
    return len(partes) + mais == int(m.group(1)), len(partes), mais, int(m.group(1))


SOBRE_DADOS = ('Esta é a embarcação de apresentação da plataforma Capitão IA: as leituras seguem o roteiro de navegação e mudam a cada segundo. '
               'Numa embarcação do cliente, os mesmos painéis leem o coletor NMEA de bordo.')
# o cadastro trocado para provar que o texto sai do dado: outro fabricante e outro modelo dos motores, o limite de horas da troca de óleo
TROCA_DADO = (";(function () { var D = window.CapitaoDados; D.equipamentos.forEach(function (e) { if (e.id === 'motores') { e.fabricante = 'Zeta'; e.modelo = 'Z9 400'; } });"
              " D.agenda.forEach(function (t) { if (t.id === 'motores-oleo') t.horas.limite = 500; }); })();")


def juizo_destinos(texto, destinos, litros, reserva, margem, nos, lph):
    """Os destinos que NÃO têm o tempo, o diesel (a `nos` nós e `lph` L/h do guia) e o juízo da ida e volta contra o diesel a bordo menos a reserva e a margem de manobra."""
    util = litros * (1 - reserva) - margem
    ruins = []
    for k, d in enumerate(destinos):
        h = d['mn'] / nos; l = int(h * lph + 0.5); m = re.search(r'%d\. %s — ≈ [\d,]+ mn · ≈ (?:(\d+) h )?(\d+) min · ≈ (\d+) L; ida e volta ≈ (\d+) L — (cabe no diesel a bordo|pede abastecer antes)' % (k + 1, re.escape(d['nome'])), texto)
        if not m or int(m.group(3)) != l or int(m.group(4)) != 2 * l or (m.group(5) == 'cabe no diesel a bordo') != (2 * l <= util):
            ruins.append((d['nome'], l, 2 * l, util, m and m.groups()))
    return ruins


def grupo_textos(b, muta, ped):
    pg = pagina(b, muta=muta, extra=TROCA_DADO)
    try:
        x = pg.evaluate(JS_TEXTOS)
        ped('textos: os motores saem do cadastro (fabricante e modelo trocados no dado aparecem; nenhum «Volvo Penta» fixo na resposta, no óleo nem na fala)',
            'Motores Zeta Z9 400' in x['motores'] and 'Volvo' not in x['motores'] + x['oleoL'] and 'Penta' not in x['motores'] + x['oleoL'], x['motores'][:200])
        ped('textos: o limite de horas da troca de óleo vem da agenda (500 h trocado no dado; nenhum «450 h» fixo)', '500 h' in x['motores'] and '450' not in x['motores'] + x['hor'], (x['motores'][-200:], x['hor'][-120:]))
        ped('textos: os motores dizem o estado e a hora do instante e os alarmes do quadro (nenhum «sem alarme» fixo)',
            x['tx']['hora'] in x['motores'] and 'sem alarme' not in x['motores'].lower() + x['oleoL'].lower() and x['tx']['alarmes'] in x['motores'], x['motores'][:260])
        ped('textos: a pressão do óleo (pergunta neutra) é a leitura do quadro de agora: pressão e rpm do instante, nenhuma «última leitura com motores ligados»',
            x['tx']['oleo'] in x['oleoL'] and x['tx']['rpm'] in x['oleoL'] and x['tx']['hora'] in x['oleoL'] and 'desligados' not in x['oleoL'] and 'última leitura' not in x['oleoL'], x['oleoL'][:300])
        ped('textos: a climatização leva fabricante e modelo do cadastro e o registro do diário da própria tarefa (nenhum «desde 20/09» fixo)',
            'Climatização Webasto FCF Platinum' in x['clima'] and '20/09' not in x['clima'] and bool(x['diaMotor']) and x['diaMotor'][0].split('|')[0] in x['clima'], (x['clima'][:300], x['diaMotor']))
        # Fase 3 (P3E, F09): o checklist de saída é o do D.checklists; o «item 7» de antes é o s13 (a salvatagem) e o s01 (a previsão), cada um com a fonte do guia
        ped('textos: o checklist de saída traz o item da salvatagem (13: coletes, um por pessoa; balsa, boia e extintores conforme a placa de salvatagem) e o da previsão (1: confira o boletim da Marinha antes de sair), com a fonte, sem lugar de equipamento e sem A CONFIRMAR',
            '13. • Coletes: um por pessoa — conte as pessoas a bordo agora; balsa, boia e extintores conforme a placa de salvatagem. (Checklist de bordo § Saída · antes de largar · FAQ EM-09)' in x['chk'] and '1. • Previsão do dia consultada (vento e mar) — confira o boletim da Marinha antes de sair' in x['chk']
            and not RX['LOCAL_SEGURANCA'].search(x['chk']) and 'A CONFIRMAR' not in x['chk'], x['chk'][-420:])
        ped('textos: os contatos abrem a situação de bordo com «Situação de bordo agora:» (o quadro está vivo)', ('Situação de bordo agora: ' + x['tx']['resumoSemPosicao']) in x['contatos'] and 'Última situação de bordo' not in x['contatos'], x['contatos'][-300:])
        ped('textos: a saudação fala da telemetria ao vivo (simulacao true)', 'Respondo sobre telemetria ao vivo, manutenção' in x['saud'], x['saud'])
        ped('textos: os eletrônicos citam o guia do piloto e o do radar (Raymarine, Garmin GMR) e a atualização de cartas pelo prazo (nenhum «diário 28/08» fixo)',
            'Guia de bordo — Piloto automático Raymarine' in x['eletr'] and 'Guia de bordo — Radar Garmin' in x['eletr'] and 'GMR 24 xHD3' in x['eletr'] and '28/08' not in x['eletr'] and re.search(r'D-\d+ · \d\d/\d\d', x['eletr']) is not None, x['eletr'][:420])
        reg = x['reg']
        faixa = 'Faixa normal: de %s a %s bar a partir de %s rpm' % (str(reg['normal']['de']).replace('.', ','), ('%.1f' % reg['normal']['ate']).replace('.', ','), '1.000')
        ped('textos: a pressão do óleo traz a faixa normal do guia dos motores §9 (do D.replay.limites: %s)' % faixa, faixa in x['oleoL'] and 'Guia de bordo — Motores Cummins §9' in x['oleoL'], x['oleoL'][-300:])
        # o juízo da ida e volta contra o diesel a bordo menos a reserva e a margem de manobra; o tempo e o diesel de cada destino pelos 18 nós e os 68 L/h do guia
        litros = int(nums(x['tx']['diesel'])[0].replace('.', ''))
        ruins = juizo_destinos(x['destinos']['text'], x['dest'], litros, x['reserva'], x['margem'], x['nos'], x['lph'])
        ped('textos: cada destino da base tem tempo (a 18 nós) e diesel (68 L/h) do guia e o juízo da ida e volta contra o diesel menos a reserva e a margem', not ruins and len(x['dest']) >= 3, ruins)
        prof = x['prof']
        ped('textos: a âncora recolhida diz quanta corrente lançar para fundear aqui (3 a 5 vezes a profundidade do guia §1, %s m)' % prof, 'de %d a %d m de corrente' % (int(prof * 3 + 0.5), int(prof * 5 + 0.5)) in x['ancora']['text'], x['ancora']['text'][-200:])
        ped('textos: o áudio e o dessalinizador saem do cadastro (modelo e produção nominal), sem SEM DADOS',
            'Fusion MS-UD755' in x['audio'] and 'Schenker Zen 30' in x['dessal'] and '30 L/h' in x['dessal'] and 'SEM DADOS' not in x['audio'] + x['dessal'], (x['audio'][:120], x['dessal'][:200]))
        ped('textos: os documentos não escrevem «SEM DADOS: .» nem a linha vazia, e não trazem a data do certificado do EPIRB',
            not re.search(r'SEM DADOS|A CONFERIR|A CONFIRMAR', x['docs']) and 'EPIRB' in x['docs'] and 'veja a etiqueta do equipamento' in x['docs'], x['docs'])
        ped('textos: os contatos dizem que os telefones ficam só no aparelho (Equipe), sem A CADASTRAR, e levam a situação de bordo sem posição com a hora',
            'A CADASTRAR' not in x['contatos'] and 'ficam só neste aparelho' in x['contatos'] and x['tx']['resumoSemPosicao'] in x['contatos'], x['contatos'][-300:])
        d = x['destinos']
        ped('textos: o destino é a rota em andamento (destino, distância e ETA do quadro) e a lista de destinos da base com tempo e diesel, sem «SEM DADOS de rotas»',
            x['tx']['destino'] in d['text'] and x['tx']['eta'] in d['text'] and 'SEM DADOS' not in d['text'] and 'Ilha das Cabras' in d['text'] and 'L' in d['text'].split('\n')[-1] + d['text'], d['text'][:420])
        a = x['ancora']['text']
        ped('textos: a âncora usa o contador de corrente do guincho (guia de eletrônicos §3), sem SEM LEITURA, e a profundidade do instante',
            'contador de corrente' in a and 'SEM LEITURA' not in a and x['tx']['prof'] in a, a[:420])
        ped('textos: o porão traz o nível do quadro (BB e BE em cm) e a faixa do guia, sem SEM LEITURA', x['tx']['porao'].split(' · ')[0] in x['porao'] and 'SEM LEITURA' not in x['porao'] and 'até 5 cm' in x['porao'], x['porao'][:300])
        tele = pg.evaluate(JS_TELE)   # antes do JS_ALARME_SEGURO: ele troca o coletor por um com alarme crítico
        al = pg.evaluate(JS_ALARME_SEGURO)
        ped('textos: o alarme do quadro entra no «seguro para sair» como ressalva (AVISO de 12:01:45: Sim, com 5 ressalvas) e o crítico de um coletor diz «Não saia agora»',
            al['aviso'].startswith('Sim, com 5 ressalvas') and 'Alarme ativo a bordo agora: AVISO: Temperatura do motor BE' in al['aviso'] and al['critico'].startswith('Não saia agora: há alarme crítico ativo'), (al['aviso'][:120], al['critico'][:200]))
        # revisão da P3B (2ª): a fala do «seguro para sair» lê a de segurança e o alarme ativo (as primeiras), e diz quantas ficaram na tela
        # (P3D, PROMPT Fase 3 «Voz»: a fala de dado de bordo diz a hora do instante; a do seguro a diz na abertura da lista, «… a primeira é de segurança, às 12:01:45: …»)
        ok, n_lidas, n_mais, n = confere_fala_seguro(al['aviso'], al['avisoFala'])
        ped('textos: a fala do seguro para sair em 12:01:45 lê a ressalva de segurança e o alarme do quadro («Temperatura do motor BE») e diz quantas ficaram na tela (lidas + «e mais K» = as 5)',
            ok and 'Temperatura do motor BE' in al['avisoFala'] and al['avisoFala'].startswith('Sim, com 5 ressalvas — a primeira é de segurança, às 12:01:45: teste das bombas de porão') and 'Alarme ativo a bordo agora' in al['avisoFala'] and n == 5 and n_lidas + n_mais == 5,
            (al['avisoFala'], n_lidas, n_mais))
        ok, n_lidas, n_mais, n = confere_fala_seguro(al['normal'], al['normalFala'])
        ped('textos: a fala do seguro para sair em 12:01:00 (sem alarme) também fecha a conta das ressalvas (lidas + «e mais K» = as 4)', ok and n == 4 and 'Alarme ativo' not in al['normalFala'] and al['normalFala'].startswith('Sim, com 4 ressalvas — a primeira é de segurança, às 12:01:00: teste das bombas de porão'), (al['normalFala'], n_lidas, n_mais))
        ped('textos: o alarme ativo é a ressalva 2, logo depois da de segurança (antes das de manutenção)', 'Ressalva 2: Alarme ativo a bordo agora' in al['aviso'] and 'Ressalva 1 (segurança)' in al['aviso'], al['aviso'][:700])
        for hh, alarme, tend in (('60', 'nenhum alarme ativo', TXT_TEND_60), ('105', 'AVISO: Temperatura do motor BE: 89,6 °C (acima de 88 °C)', TXT_TEND_105)):
            ped('textos (telemetria às 12:01:%s): as duas últimas linhas são «• Alarmes: …» do quadro e «• Tendência — últimos 30 s: …»' % ('00' if hh == '60' else '45'),
                tele[hh]['alarmes'] == alarme and tele[hh]['tend'] == tend and tele[hh]['text'].endswith('\n• Alarmes: ' + alarme + '\n• Tendência — ' + tend), tele[hh]['text'][-320:])
        # revisão da P3B (2ª), trava 17: a ficha inteira (vai à IA em toda pergunta) não traz o fabricante nem o modelo do EPIRB e do Seafire — só Equipamentos, Leme e Documentos
        vazou = [t for e in x['seguranca'] for t in (e['modelo'], '%s %s' % (e['nome'], e['fabricante']), e['fabricante'] if (e['fabricante'] or '').lower() not in e['palavras'] else None) if t and t.lower() in x['ficha'].lower()]
        ped('textos: a ficha não traz o fabricante nem o modelo dos equipamentos de segurança (EPIRB: %s; Seafire: %s)' % tuple('%s %s' % (e['fabricante'], e['modelo']) for e in x['seguranca']),
            len(x['seguranca']) == 2 and all(e['fabricante'] and e['modelo'] for e in x['seguranca']) and not vazou and len(x['ficha']) > 3000, (vazou, len(x['ficha'])))
        ped('textos: o estabilizador não manda para o manual do Drive (nenhum MANUAL NO DRIVE) e cita o guia', 'MANUAL NO DRIVE' not in x['estab'] and 'Guia de bordo — Estabilizador Seakeeper' in x['estab'], x['estab'])
        fb = x['fallback']
        ped('textos: o fallback não diz SEM DADOS nem «Não encontrei esse dado», traz a situação de bordo sem posição com a hora e mantém a fonte',
            fb['key'] == 'fallback' and 'SEM DADOS' not in fb['text'] and 'Não encontrei esse dado' not in fb['text'] and x['tx']['resumoSemPosicao'] in fb['text'] and fb['src'].startswith('Fonte'), fb['text'][:300])
        for k in ('foto', 'video'):
            ped('textos (%s): o anexo não diz o estado fixo («motores desligados · gerador ligado», snapshot) e leva a situação de bordo sem posição, com a hora' % k,
                not re.search(r'motores desligados|gerador ligado\)|snapshot', x[k]) and x['tx']['resumoSemPosicao'] in x[k] and 'A CONFIRMAR' in x[k], x[k][:360])
        ped('textos: o «Sobre o app» da ficha não diz «nada inventado» nem os rótulos, fala da telemetria ao vivo, da CONVERSA e traz a frase de sobreDados da decisão (f)',
            'nada inventado' not in x['sobre'].lower() and not re.search(r'SEM DADOS|SEM LEITURA|MANUAL NO DRIVE', x['sobre']) and 'telemetria ao vivo' in x['sobre'] and 'CONVERSA' in x['sobre'] and SOBRE_DADOS in x['sobre'], x['sobre'])
        ped('textos: o «Sobre o app» lista os equipamentos do cadastro e a sigla do AIS fica inteira (nenhum «aIS»)',
            'AIS (classe B) em-trak' in x['sobre'] and not re.search(r'\b[a-z][A-Z]{2}', x['sobre']) and 'motores Zeta' in x['sobre'], x['sobre'][:900])
        ped('textos: o cérebro exporta a frase de sobreDados (B.SOBRE_DADOS = a da decisão (f))', x['sobreDados'] == SOBRE_DADOS, x['sobreDados'])
        ped('textos: o convite não diz «demonstração» com simulacao true', 'demonstra' not in x['convite'].lower() and len(x['convite']) > 20, x['convite'][:200])
        ped('textos: o consumo e a autonomia não citam o período fixo da leitura antiga (01/08–26/09/2026)', '01/08–26/09' not in x['cons'] + x['aut'] + x['hor'], (x['cons'][:200], x['aut'][-200:]))
        # revisão da P3B (3ª): o que os mutantes de outros trechos não acusavam
        ped('textos: a fonte da autonomia e a do consumo citam a fonte do consumo do guia (%s) e não o período da leitura antiga (%s)' % (x['consFonte'], x['consPeriodo']),
            x['consFonte'] in x['autSrc'] and x['consFonte'] in x['consSrc'] and x['consPeriodo'] not in x['autSrc'] + x['consSrc'], (x['autSrc'], x['consSrc']))
        ped('textos: o áudio diz as zonas do cadastro («· %s zonas»)' % x['zonas'], bool(x['zonas']) and x['audio'].split('\n')[0].endswith(' · %s zonas.' % x['zonas']), x['audio'][:160])
        ped('textos: o estabilizador traz a tarefa do anodo da agenda com o prazo do dia do instante (%s)' % x['anodo'],
            re.search(r'\n%s: D-\d+ · \d\d/\d\d\.' % re.escape(x['anodo']), x['estab']) is not None, x['estab'][-220:])
        # o certificado do EPIRB (equipamento de segurança) vai só na linha «Segurança», com a nota da etiqueta: nem a data dele, nem na lista de vencimentos
        ped('textos: os documentos não trazem a data do certificado do EPIRB (%s) e ele só aparece na linha «Segurança:», com a nota da etiqueta' % (x['epirbDoc'] or {}).get('vence'),
            bool(x['epirbDoc']) and x['epirbDoc']['vence'] not in x['docs'] and x['docs'].lower().count('certificado do epirb') == 1 and re.search(r'\nSegurança: certificado do EPIRB[^\n]*veja a etiqueta do equipamento', x['docs']) is not None, x['docs'])
    finally:
        pg.ctx.close()
    # o convite diz «(demonstração)» só com a flag antiga e sem a simulação
    for extra, quer, nome in ((";window.CapitaoDados.demo = true;", False, 'simulacao true'), (SEM_SIMULACAO + ";window.CapitaoDados.demo = true;", True, 'simulacao false')):
        pg = pagina(b, muta=muta, extra=extra)
        try:
            c = pg.evaluate("() => (window.CapitaoBrain.linkConvite('Ana', '+55 47 99999-0000', 'total') || {}).href || ''")
            ped('textos (convite com D.demo e %s): «(demonstração)» %s' % (nome, 'volta' if quer else 'não aparece'), ('demonstra' in c.lower()) == quer, c[:200])
        finally:
            pg.ctx.close()


# revisão da P3B (3ª): o replay só navega (motores, radar, gerador e Seakeeper ligados o laço todo), então um estado fixo no código só aparece com um coletor de verdade. O quadro do instante com TUDO
# desligado e pouco diesel, e outro com tudo ligado: cada resposta concorda com o estado e a hora do quadro (nunca «ligado», «(motores desligados)» nem o radar fixos), a fala do gerador traz o
# estado e a hora, e o juízo dos destinos pesa o diesel do quadro contra a reserva E a margem de manobra
JS_ESTADOS = """() => { const B = window.CapitaoBrain, R = window.CapitaoReplay, D = window.CapitaoDados, op = { platform: 'app', commit: false }, out = {};
  const r = (q) => { const a = B.answer(q, op); return { key: a.key, text: a.text, fala: B.falaCurta(a) }; };
  out.replay = ['60', '105'].map((x) => { R.fixar(x); const i = B.instante(); return { x, hora: i.hora, ger: i.txt.gerador, r: r('quantas horas tem o gerador') }; });
  R.fixar('60'); const base = R.em(R.agora());
  const casos = { desligado: { motor_bb_rpm: 0, motor_be_rpm: 0, radar_ativo: false, ais_alvos: 1, gerador_ativo: false, gerador_kw: 0, seakeeper_ativo: false, seakeeper_volante_rpm: 0, seakeeper_volante_pct: 0,
                               climatizacao_ativa: false, dessalinizador_ativo: true, diesel_litros: 100, diesel_bb_pct: 6.3, diesel_be_pct: 6.2 },
                  ligado: { radar_ativo: true, ais_alvos: 3, dessalinizador_ativo: false } };
  Object.keys(casos).forEach((nome, k) => { R.fixar(String(61 + k)); const q = Object.assign({}, base, casos[nome]); delete q.simulado; window.CapitaoTelemetria = { atual: () => q };
    const i = B.instante(); out[nome] = { fonte: i.fonte, hora: i.hora, diesel: i.txt.diesel, hor: r('horímetros'), ger: r('quantas horas tem o gerador'), mot: r('motores'), eletr: r('plotter garmin'), estab: r('estabilizador Seakeeper'),
      clima: r('climatização'), dessal: r('dessalinizador'), dest: r('para onde vamos hoje?') }; });
  out.dados = { dest: D.destinos, reserva: D.reserva, margem: D.consumo.margemManobra_l, nos: D.consumo.cruzeiro.nos, lph: D.consumo.cruzeiro.lph };
  return out; }"""


def grupo_estados(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        x = pg.evaluate(JS_ESTADOS)
        # a fala do gerador (a 1ª linha sem parênteses) traz o estado e a hora, no replay, às 12:01:00 e às 12:01:45
        for g in x['replay']:
            est, kw, hh = g['ger'].split(' · ')
            quer = 'Gerador Onan QD 9 %s às %s · %s · %s.' % (est, g['hora'], kw, hh)
            ped('estados (replay %s): o gerador diz o estado e a hora na própria frase («%s») e a fala é a mesma frase, com «%s às %s»' % (g['hora'], quer, est, g['hora']),
                g['r']['text'].split('\n')[0] == quer and g['r']['fala'] == quer and ('%s às %s' % (est, g['hora'])) in g['r']['fala'] and '(' not in g['r']['text'].split('\n')[0], (g['r']['text'].split('\n')[0], g['r']['fala']))
        d, l = x['desligado'], x['ligado']
        ped('estados: os dois quadros são do coletor', d['fonte'] == 'coletor' and l['fonte'] == 'coletor', (d['fonte'], l['fonte']))
        for nome, e, est in (('tudo desligado', d, 'desligado'), ('tudo ligado', l, 'ligado')):
            plural = 'desligados' if est == 'desligado' else 'ligados'
            ped('estados (%s): os horímetros dizem «(motores %s)» do quadro, com a hora dele' % (nome, plural), e['hor']['text'].split('\n')[0] == 'Horímetros às %s (motores %s):' % (e['hora'], plural), e['hor']['text'][:90])
            ped('estados (%s): os motores dizem «Motores %s às hora»' % (nome, plural), e['mot']['text'].startswith('Motores %s às %s:' % (plural, e['hora'])), e['mot']['text'][:90])
            g1 = e['ger']['text'].split('\n')[0]
            ped('estados (%s): o gerador diz «%s às hora» na frase e na fala' % (nome, est),
                re.fullmatch(r'Gerador Onan QD 9 %s às %s%s · [\d.]+,\d h\.' % (est, e['hora'], '' if est == 'desligado' else r' · [\d,]+ kW'), g1) is not None and e['ger']['fala'] == g1, (g1, e['ger']['fala']))
            ped('estados (%s): a climatização e o dessalinizador dizem o estado do quadro e a hora' % nome,
                re.match(r'Climatização Webasto FCF Platinum .*? %s às %s\.' % ('desligada' if est == 'desligado' else 'ligada', e['hora']), e['clima']['text']) is not None
                and e['dessal']['text'].startswith('Dessalinizador Schenker Zen 30 %s às %s' % ('ligado' if est == 'desligado' else 'desligado', e['hora'])), (e['clima']['text'][:80], e['dessal']['text'][:80]))
            ped('estados (%s): o Seakeeper diz %s' % (nome, est), e['estab']['text'].startswith('Seakeeper agora: ' + ('desligado' if est == 'desligado' else 'LIGADO')), e['estab']['text'][:60])
        ped('estados: os eletrônicos dizem o radar e os alvos do AIS do quadro (desligado com 1 alvo; ligado com 3 alvos)',
            ' Às %s: radar desligado · AIS com 1 alvo.' % d['hora'] in d['eletr']['text'] and ' Às %s: radar ligado · AIS com 3 alvos.' % l['hora'] in l['eletr']['text'], (d['eletr']['text'][:200], l['eletr']['text'][:200]))
        # os destinos: o diesel do quadro (100 L: 90 L menos a margem de manobra = 30 L úteis) contra a ida e volta de cada um — os dois mais longos pedem abastecer, e SEM a margem caberiam
        dd = x['dados']
        litros = int(nums(d['diesel'])[0].replace('.', ''))
        ruins = juizo_destinos(d['dest']['text'], dd['dest'], litros, dd['reserva'], dd['margem'], dd['nos'], dd['lph'])
        ped('estados (100 L a bordo): cada destino pesa a ida e volta contra o diesel menos a reserva e a margem de manobra (%s L)' % dd['margem'], not ruins and litros == 100, (litros, ruins))
        pede = re.findall(r'^\d\. (.+?) — .*pede abastecer antes$', d['dest']['text'], re.M)
        sem_margem = [t['nome'] for t in dd['dest'] if 2 * int(t['mn'] / dd['nos'] * dd['lph'] + 0.5) > litros * (1 - dd['reserva'])]
        ped('estados (100 L a bordo): os destinos que pedem abastecer são os que passam do diesel útil, e a margem de manobra muda o juízo de ao menos um deles',
            len(pede) >= 1 and len(pede) > len(sem_margem), (pede, sem_margem))
        ruins = juizo_destinos(l['dest']['text'], dd['dest'], int(nums(l['diesel'])[0].replace('.', '')), dd['reserva'], dd['margem'], dd['nos'], dd['lph'])
        ped('estados (diesel cheio): todos os destinos cabem no diesel a bordo', not ruins and 'pede abastecer antes' not in l['dest']['text'], ruins)
    finally:
        pg.ctx.close()


def grupo_rotas(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        r = pg.evaluate("(qs) => qs.map(([q]) => { const a = window.CapitaoBrain.answer(q, { platform: 'app', commit: false }); return [q, a.key, a.text.split('\\n')[0]]; })", ROTAS_CORRENTE)
        ruins = [(q, k, esp) for (q, k, _), (_, esp) in zip(r, ROTAS_CORRENTE) if k != esp]
        ped('rotas: a corrente da âncora (metros, lançada, contador) vai para a âncora, a de maré, a correnteza e a da bateria seguem as suas (%d perguntas)' % len(ROTAS_CORRENTE), not ruins, ruins)
        anc = [t for q, k, t in r if k == 'ancora']
        ped('rotas: a resposta da âncora às perguntas da corrente fala do contador de corrente do guincho e da hora do instante', len(anc) == 5 and all('contador do guincho' in t and '12:01:00' in t for t in anc), anc)
    finally:
        pg.ctx.close()


GRUPOS_3A = {'forma': grupo_forma, 'uma': grupo_uma, 'resumo': grupo_resumo, 'virada': grupo_virada, 'sos': grupo_sos, 'real': grupo_real, 'alarmes': grupo_alarmes,
             'aninhadas': grupo_aninhadas, 'transicao': grupo_transicao, 'coletor': grupo_coletor, 'falha': grupo_falha, 'parcial': grupo_parcial,
             'numeros': grupo_numeros, 'ligados': grupo_ligados, 'coordenada': grupo_coordenada, 'marca': grupo_marca, 'emerg': grupo_emerg,
             'rotulos': grupo_rotulos, 'modos': grupo_modos, 'prazos': grupo_prazos, 'tempo': grupo_tempo, 'textos': grupo_textos, 'estados': grupo_estados, 'rotas': grupo_rotas}

# ——————————————— Fase 3, P3C: as rotas novas ———————————————
# (PROMPT Fase 3 «Rotas novas», «Fallback», «Voz»; §2.3, §2.6, §2.7; CONTRATO §1.2, §1.22, §1.24.) A 1ª linha de cada rota é a própria resposta, numa frase falável, com o dado e a hora do instante,
# sem coordenada e sem sigla solta; a situação de bordo (sem posição) vem na linha seguinte onde a decisão (g) manda (sobreDados, foraBarco). As conferências abaixo reconstroem o texto esperado
# do próprio instante (i.txt, i.q, o catálogo D.replay.alertas) e do cadastro (D.embarcacao): nenhum número escrito aqui.
P3C_PERGUNTAS = {
    'posicao': 'onde estamos?', 'profundidade': 'qual a profundidade?', 'eta': 'qual a hora de chegada?', 'wp': 'qual o próximo waypoint?', 'percorrido': 'distância percorrida hoje', 'alarmes': 'tem algum alarme ativo?', 'soa': 'o alarme está tocando',
    'arref': 'qual a temperatura do motor?', 'ondas': 'como está o estado do mar?', 'agua': 'qual a temperatura da água?', 'nav': 'como está a navegação?', 'pessoas': 'quantas pessoas a bordo?',
    'calado': 'qual o calado do barco?', 'compr': 'qual o comprimento?', 'boca': 'qual a boca do barco?', 'lotacao': 'qual a lotação?', 'registro': 'qual o registro do barco?', 'modelo': 'qual o modelo do barco?',
    'dim': 'dimensões do barco', 'mmsi': 'qual o MMSI do barco?', 'ais': 'quantos alvos no AIS?', 'sobre': 'esses dados são reais?', 'fora': 'qual o preço do dólar?',
    # revisão 4: a chegada em outro ponto da rota, as horas que faltam, o vento a bordo e o fundo no jeito de bordo
    'etaEst': 'quanto falta para o Estaleirinho?', 'etaBarra': 'quanto falta para a Barra Sul?', 'etaCabras': 'quanto falta para a Ilha das Cabras?', 'etaLaranj': 'quanto falta para a Ponta das Laranjeiras?',
    'etaQuando': 'quando chegamos?', 'faltaOleo': 'quanto falta para a troca de óleo?', 'faltaGer': 'quanto falta para a revisão do gerador?',
    'vento': 'qual o vento a bordo agora?', 'ventoAp': 'qual o vento aparente?', 'ventoDois': 'o vento é verdadeiro ou aparente?', 'ventoForte': 'o vento está forte agora', 'fundo': 'quanto de fundo tem aqui?',
}
JS_P3C = """([xs, qs]) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, D = window.CapitaoDados, A = window.CapitaoAgora, op = { platform: 'app', commit: false };
  const r = (q) => { const a = B.answer(q, op); return { key: a.key, text: a.text, src: a.src, fala: B.falaCurta(a), ia: B.pedeIA(a, q), acoes: a.actions || [] }; };
  const ais = (D.equipamentos || []).filter((e) => e.id === 'ais')[0] || {};
  return { E: D.embarcacao, sobre: B.SOBRE_DADOS, ais: [ais.nome, ais.fabricante, ais.modelo].join(' '), cat: (D.replay && D.replay.alertas) || {}, ate: D.replay && D.replay.limites && D.replay.limites.motor_bb_arref_c.normal.ate,
    r: xs.map((x) => { R.fixar(x); const i = B.instante();
      return { x, hora: i.hora, q: i.q, txt: i.txt, tend: i.tend, ag: (D.agenda || []).reduce((o, t) => { o[t.id] = { vence: t.vence, limite: t.horas && t.horas.limite }; return o; }, {}), falt: (i.calc && i.calc.faltam) || {}, campos: { destino_mn: A.fmt.campo(i.q, 'destino_mn'), wp_mn: A.fmt.campo(i.q, 'wp_mn'), distancia_mn: A.fmt.campo(i.q, 'distancia_mn') },
               r: Object.keys(qs).reduce((o, k) => { o[k] = r(qs[k]); return o; }, {}) }; }) }; }"""
JS_P3C_CHAVES = """(casos) => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false };
  return casos.map(([q]) => { const a = B.answer(q, op); return [a.key, B.pedeIA(a, q)]; }); }"""
# a pergunta mista (cabeça de equipamento + cauda de dado, nas duas ordens): [pergunta, chave, chave da cabeça sozinha] por par
JS_P3C_MISTAS = """(pares) => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }, k = (q) => B.answer(q, op).key;
  return pares.map(([cab, cauda]) => { const a = cab + ', ' + cauda, b = cauda.replace(/\\?$/, '') + ', ' + cab; return [[a, k(a), k(cab)], [b, k(b), k(cab)]]; }); }"""

# o número do cadastro e a chave de cada pergunta (a propriedade do MMSI e a do relato); o texto, a fonte e a fala
JS_P3C_NUM = """([qs, num]) => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false };
  return qs.map((q) => { const a = B.answer(q, op); return [a.key, (a.text + a.src + B.falaCurta(a)).indexOf(num) !== -1]; }); }"""
# Propriedade (revisão 3, MMSI): {verbo de pôr o MMSI no aparelho, no infinitivo, no presente e no imperativo} × {rádio, VHF, AIS, DSC, transponder, plotter} × {4 jeitos de perguntar}: o número do cadastro nunca aparece
MMSI_VERBOS = [('colocar', 'coloco', 'coloque'), ('digitar', 'digito', 'digite'), ('inserir', 'insiro', 'insira'), ('cadastrar', 'cadastro', 'cadastre'), ('atualizar', 'atualizo', 'atualize'),
               ('alterar', 'altero', 'altere'), ('mudar', 'mudo', 'mude'), ('ajustar', 'ajusto', 'ajuste'), ('definir', 'defino', 'defina'), ('configurar', 'configuro', 'configure'),
               ('programar', 'programo', 'programe'), ('gravar', 'gravo', 'grave'), ('salvar', 'salvo', 'salve'), ('informar', 'informo', 'informe'), ('adicionar', 'adiciono', 'adicione'),
               ('incluir', 'incluo', 'inclua'), ('preencher', 'preencho', 'preencha'), ('editar', 'edito', 'edite'), ('habilitar', 'habilito', 'habilite'), ('ativar', 'ativo', 'ative'),
               ('usar', 'uso', 'use'), ('registrar', 'registro', 'registre'), ('trocar', 'troco', 'troque'), ('setar', 'seto', 'sete'), ('pôr', 'ponho', 'ponha'), ('anotar', 'anoto', 'anote'),
               ('lançar', 'lanço', 'lance'), ('carregar', 'carrego', 'carregue'), ('apontar', 'aponto', 'aponte'), ('transmitir', 'transmito', 'transmita')]
MMSI_LUGARES = ['no rádio', 'no VHF', 'no AIS', 'no DSC', 'no transponder', 'no plotter', 'no rádio de bordo', 'para o rádio', 'ao rádio']
MMSI_JEITOS = ['como {v} o MMSI {l}?', '{v} o MMSI {l}', 'qual MMSI eu {v} {l}?', 'que MMSI {v} {l}?', 'onde {v} o MMSI {l}?']
MMSI_PROPRIEDADE = sorted({j.format(v=v, l=l) for vs in MMSI_VERBOS for v in vs for l in MMSI_LUGARES for j in MMSI_JEITOS}
                          | {j.format(v=v, l='') .replace(' ?', '?').strip() for vs in MMSI_VERBOS for v in vs[:2] for j in MMSI_JEITOS if v not in ('informe',)})
# Propriedade (revisão 3, relato): {relato de falha ou de equipamento} × {pergunta com palavra da rota nova}, nas duas ordens: nenhuma vira a leitura calma (posição, ETA, alarmes, pessoas, navegação, embarcação, profundidade,
# temperatura do motor, mar, água do mar), como antes da P3C (trava 10: relato de falha sem leitura calma). Os relatos que já têm a palavra de uma rota antiga de posição (GPS, proa, velocidade) ficam de fora.
RELATOS_CALMA = ['o motor parou', 'pane no motor', 'a bomba de porão parou', 'a âncora garrou', 'o rádio não funciona', 'o barco está sem governo', 'não consigo manobrar', 'o rumo mudou sozinho',
                 'o barco está desviando do rumo', 'estamos fora do rumo', 'o COG está errado', 'o waypoint sumiu', 'o ETA não atualiza', 'o plotter perdeu o waypoint', 'o plotter não calcula o ETA',
                 'o barco está inclinando', 'o piloto automático desligou', 'o gerador apagou', 'o leme está duro', 'a hélice enroscou', 'o motor está falhando', 'o motor está vibrando muito', 'o AIS parou',
                 'a sonda travou', 'o radar apagou', 'o plotter congelou', 'a bateria descarregou', 'o Seakeeper caiu', 'o ar condicionado parou', 'a bomba de água salgada falhou', 'o alarme não para',
                 'o alarme disparou sem motivo', 'o motor superaqueceu', 'a pressão do óleo caiu', 'o tender soltou', 'o cabo da âncora arrebentou', 'a corrente da âncora enroscou', 'o bote furou',
                 'o rádio ficou mudo', 'o VHF não transmite', 'a luz de navegação queimou', 'o painel apagou', 'o inversor desarmou', 'o motor BB morreu', 'a bomba do porão não liga',
                 'tem barulho estranho no motor', 'sentimos uma batida no casco', 'o barco encostou no fundo', 'perdemos o motor', 'o motor está engasgando', 'o barco está pesado de popa',
                 'o diesel está acabando', 'o tanque está vazando', 'o transdutor soltou', 'estamos sem energia', 'o piloto perdeu o rumo', 'o motor travou', 'o rádio caiu', 'o eixo está esquentando',
                 # revisão 4: o relato de perigo e o de falha do AIS e dos instrumentos que a lista branca da sobreDados e a do AIS têm de deixar de fora
                 'tem muita água no barco', 'o bote virou', 'estamos perdidos', 'vamos morrer', 'pelo amor de Deus', 'a situação é grave', 'tem um problema grave a bordo', 'a água está subindo',
                 'o motor morreu', 'estamos à deriva', 'o barco está afundando', 'estamos encalhados', 'o casco rachou', 'tem fumaça no motor', 'o leme travou', 'perdemos o leme', 'o bote soltou',
                 'a âncora arrastou', 'não tem mais diesel', 'o diesel acabou', 'o gerador falhou', 'a bateria morreu', 'estamos sem rádio', 'o radar parou', 'o AIS apagou', 'o AIS está desligado',
                 'sem sinal do AIS', 'o AIS não funciona', 'o AIS está com falha', 'o AIS não está recebendo nada', 'a sonda marca 2 metros', 'a profundidade está caindo', 'o motor está superaquecendo',
                 'a temperatura do motor está em 110', 'um tripulante caiu', 'alguém está ferido', 'o barco está adernando', 'estamos tomando água', 'o porão está cheio', 'senti um cheiro de queimado',
                 'tem faísca no painel', 'a hélice quebrou', 'o eixo quebrou', 'o piloto automático falhou', 'o plotter apagou', 'estamos com medo', 'não sei onde estamos', 'o barco está descontrolado',
                 # (o desgaste precoce e o intervalo preconizado têm o «preco» dentro: nunca são o foraBarco)
                 'o rotor tem desgaste precoce', 'a falha precoce do alternador', 'o intervalo preconizado já passou']
CAUDAS_CALMA = ['qual o ETA?', 'quanto falta para chegar?', 'qual o próximo waypoint?', 'quais alarmes ativos?', 'quantas pessoas a bordo?', 'como está a navegação?', 'situação agora', 'qual o calado do barco?',
                'qual o comprimento do barco?', 'qual o rumo?', 'qual o COG?', 'quantos nós?', 'onde estamos?', 'qual a profundidade?', 'qual a temperatura do motor?', 'como está o mar?',
                'qual a temperatura da água?', 'qual a distância até o destino?', 'tem algum alarme ativo?', 'qual o MMSI do barco?',
                # revisão 4: a pergunta sobre os dados (sobreDados), a do AIS e a chegada do jeito de bordo, depois e antes do relato
                'os dados são reais?', 'isso é real?', 'isso é simulado?', 'é sério, isso é real?', 'qual a situação do AIS?', 'quantos alvos no AIS?', 'quando chegamos?', 'qual o fundo?', 'quanto falta para a troca de óleo?']
CALMAS_P3C = ('eta', 'posicao', 'alarmes', 'pessoas', 'navegacao', 'embarcacao', 'profundidade', 'arrefecimento', 'ondas', 'temperaturaAgua', 'ais', 'sobreDados', 'horimetros', 'foraBarco')
RELATO_PARES = [p for r in RELATOS_CALMA for c in CAUDAS_CALMA for p in (r + ', ' + c, c.rstrip('?') + ', ' + r)]
# Propriedade (revisão 3, socorro): {pedido de ajuda, de risco ou «não é um teste» que a lista SOS não pega} × {pergunta com palavra da rota nova ou da sobreDados}: nunca a leitura calma nem a frase de apresentação
SOCORRO_FRASES = ['preciso de ajuda', 'estamos em risco', 'isso não é um teste', 'não é brincadeira, preciso de ajuda', 'é sério, preciso de ajuda', 'isso é real, preciso de ajuda', 'preciso de resgate',
                  'necessito de ajuda', 'precisamos de ajuda', 'o barco está em risco', 'não é um teste', 'estou em apuros']
CAUDAS_SOCORRO = [c for c in CAUDAS_CALMA if 'MMSI' not in c] + ['os dados são reais?', 'isso é real?', 'isso é simulado?', 'quantas pessoas estão a bordo?', 'qual a hora de chegada?', 'qual a posição?']
SOCORRO_PARES = [p for f in SOCORRO_FRASES for c in CAUDAS_SOCORRO for p in (f + ', ' + c, c.rstrip('?') + ', ' + f)]


def nc(s):
    """O nome sem acento, em minúscula, sem o que vem entre parênteses (a comparação do ponto da rota: «Barra Sul (base)» = «barra sul»)."""
    import unicodedata
    t = re.sub(r'\s*\(.*?\)', '', str(s or '')).strip().lower()
    return ''.join(ch for ch in unicodedata.normalize('NFD', t) if unicodedata.category(ch) != 'Mn')


def mil_py(x):
    return ('%d' % round(x)).replace(',', '') if x < 1000 else '{:,}'.format(int(round(x))).replace(',', '.')


def sinal_tend(v):
    return ('+' if v > 0 else '−' if v < 0 else '') + ('%.1f' % abs(v)).replace('.', ',')


def nbr(x, c=1):
    return ('%.*f' % (c, x)).replace('.', ',')


def sem_par(s):
    while True:
        n = re.sub(r'\s*\([^()]*\)', '', s)
        if n == s:
            return re.sub(r'\s*[()]', '', n)
        s = n


def grupo_p3c(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); })")
        # (1) a chave e o PEDE_IA de cada pergunta: as rotas novas respondem no aparelho e não roubam as vizinhas
        todas = ROTAS_P3C + ROTAS_P3C_REV + ROTAS_P3C_REV2 + ROTAS_P3C_REV3 + ROTAS_P3C_REV4
        res = pg.evaluate(JS_P3C_CHAVES, [[q] for q, _, _ in todas])
        ruins = [(q, esp, ia_esp, key, ia) for (q, esp, ia_esp), (key, ia) in zip(todas, res) if key != esp or ia != ia_esp]
        ped('p3c: as %d perguntas das rotas novas (e as que elas não podem roubar) caem na chave certa e com o PEDE_IA certo' % len(todas), not ruins, ruins[:6])
        # (1a) «quanto falta?» e «quantas milhas?» sozinhos não são a chegada (só junto de chegar, destino, waypoint, ponto, ETA ou o nome de um ponto da rota)
        res = pg.evaluate(JS_P3C_CHAVES, [[q] for q in NAO_ETA])
        ruins = [(q, key) for q, (key, ia) in zip(NAO_ETA, res) if key == 'eta']
        ped('p3c: «quanto falta?» e «quantas milhas?» sozinhos NÃO são a chegada da rota', not ruins, ruins)
        # (1b) o relato com número ou estado não é a pergunta da leitura calma («a temperatura do motor está em 110», «a sonda marca 2 metros», «profundidade caindo»…)
        res = pg.evaluate(JS_P3C_CHAVES, [[q] for q in RELATOS_P3C])
        ruins = [(q, key) for q, (key, ia) in zip(RELATOS_P3C, res) if key in LEITURAS_P3C]
        ped('p3c: as %d perguntas de relato (com número ou estado) NÃO são a leitura calma do arrefecimento, da profundidade, das ondas nem da água do mar' % len(RELATOS_P3C), not ruins, ruins[:6])
        # (1c) a pergunta mista com o equipamento de segurança (EPIRB, Seafire, canal 16, PAN-PAN, DSC) tem a chave do equipamento, nas duas ordens: nunca ETA, pessoas, profundidade, alarmes, mar, MMSI…
        pares = [[cab, cauda] for cab, _ in MISTAS_CABECAS for cauda in MISTAS_CAUDAS]
        res = [x for par in pg.evaluate(JS_P3C_MISTAS, pares) for x in par]
        ruins = [(q, key, cab) for q, key, cab in res if key != cab]
        ped('p3c: as %d perguntas mistas (equipamento de segurança + dado) são do equipamento' % len(res), not ruins, ruins[:6])
        ruins = [(cab, esp, x[2]) for cab, esp in MISTAS_CABECAS for x in res if (x[0].startswith(cab + ', ') or x[0].endswith(', ' + cab)) and x[2] != esp]
        ped('p3c: a cabeça de cada pergunta mista, sozinha, tem a chave do equipamento (epirb, seafire, canal16)', not ruins, ruins[:4])
        # (1d) revisão 3, MMSI: o número do cadastro só na pergunta NEUTRA; nunca perto de pôr o MMSI no rádio, no VHF, no AIS, no DSC, no transponder nem no plotter (CLAUDE.md 8: nunca com instrução de programar)
        num = pg.evaluate("() => window.CapitaoDados.embarcacao.mmsi")
        res = pg.evaluate(JS_P3C_NUM, [MMSI_PROPRIEDADE, num])
        ruins = [(q, key) for q, (key, tem) in zip(MMSI_PROPRIEDADE, res) if tem or key not in ('mmsi', 'canal16', 'diario')]   # (o DSC é o roteiro do rádio e «registre/anote o MMSI no rádio» é o comando do diário: também só o MMSI da etiqueta)
        ped('p3c mmsi: as %d perguntas de pôr o MMSI no aparelho (30 verbos em 3 flexões × rádio, VHF, AIS, DSC, transponder, plotter) são da rota mmsi (ou do roteiro do rádio, ou do comando do diário) e nunca trazem o número do cadastro' % len(MMSI_PROPRIEDADE), not ruins, ruins[:6])
        neutras = ['qual o MMSI do barco?', 'qual o MMSI?', 'MMSI', 'meu MMSI', 'qual o MMSI cadastrado no app?', 'qual o MMSI da embarcação?', 'qual o MMSI, por favor?', 'por favor, qual o MMSI?', 'Capitão, qual o MMSI?', 'qual o numero do MMSI?',
                   'qual o MMSI do cadastro?', 'qual o MMSI no cadastro do app?']
        res = pg.evaluate(JS_P3C_NUM, [neutras, num])
        ruins = [(q, key, tem) for q, (key, tem) in zip(neutras, res) if not tem or key != 'mmsi']
        ped('p3c mmsi: a pergunta NEUTRA do número («qual o MMSI do barco?», «meu MMSI», «por favor, qual o MMSI?») traz o do cadastro na 2ª linha', not ruins, ruins)
        # (1e) revisão 3, relato: nenhum relato de falha + palavra da rota nova vira a leitura calma (nem o número do cadastro do MMSI)
        res = pg.evaluate(JS_P3C_NUM, [RELATO_PARES, num])
        ruins = [(q, key, tem) for q, (key, tem) in zip(RELATO_PARES, res) if key in CALMAS_P3C or tem]
        ped('p3c: os %d pares relato de falha + pergunta da rota nova (nas duas ordens) NÃO viram a leitura calma' % len(RELATO_PARES), not ruins, ruins[:6])
        # (1f) revisão 3, socorro: o pedido de ajuda, de risco ou «não é um teste» + pergunta de rota nova não é a leitura calma nem a frase de apresentação
        res = pg.evaluate(JS_P3C_NUM, [SOCORRO_PARES, num])
        ruins = [(q, key) for q, (key, tem) in zip(SOCORRO_PARES, res) if key in CALMAS_P3C or key in ('sobreDados', 'foraBarco') or tem]
        ped('p3c: os %d pares pedido de socorro (que a lista SOS não pega) + pergunta da rota nova NÃO viram a leitura calma nem a frase de apresentação' % len(SOCORRO_PARES), not ruins, ruins[:6])
        # (2) as respostas, em 12:01:00 e 12:01:45
        out = pg.evaluate(JS_P3C, [['60', '105', '10@0', '149@575'], P3C_PERGUNTAS])
        E = out['E']
        cal, comp, boca, lot = nbr(E['calado'], 2), nbr(E['comprimento'], 2), nbr(E['boca'], 2), E['lotacao']
        # (2b) a rota mmsi com o indicativo («o da Licença de Estação (no rádio)», nunca gerado), a pergunta de programar (sem o número do cadastro) e as respostas do EPIRB, do rádio e do Seafire (nunca o 710123456)
        mm = pg.evaluate(JS_P3C_DADOS, {'ind': 'qual o MMSI e o indicativo do barco?', 'prog': 'como programar o MMSI no rádio?', 'cad': 'qual o MMSI cadastrado?', 'epirb': 'o EPIRB usa o MMSI do barco?',
                                        'epirb2': 'qual o MMSI do EPIRB?', 'pan': 'como fazer um pan-pan com o MMSI?', 'dsc': 'o MMSI do rádio está programado para o DSC?', 'pane': 'o motor parou, qual o MMSI?',
                                        'sea': 'qual o MMSI do Seafire?'})
        usa, ind = 'No MAYDAY e no DSC, use o MMSI da etiqueta do rádio (Licença de Estação).', mm['ind']['text'].split('\n')
        ped('p3c mmsi: a pergunta do MMSI e do indicativo traz «o da Licença de Estação (no rádio)» na 1ª linha (e na fala), o do cadastro na 2ª, e nenhum indicativo gerado',
            ind[0] == usa + ' Indicativo: o da Licença de Estação (no rádio).' and ind[1] == 'Cadastro do app: MMSI %s.' % E['mmsi'] and 'Indicativo: o da Licença de Estação' in mm['ind']['fala']
            and not re.search(r'\b(?:P[P-Y]|Z[V-Z])\d[A-Z]{1,3}\b', mm['ind']['text']) and mm['ind']['ia'] is False, (ind, mm['ind']['fala']))
        ped('p3c mmsi: a pergunta de programar o MMSI no rádio manda usar o da etiqueta e nunca mostra o número do cadastro (nunca com instrução de programar)',
            mm['prog']['text'] == usa and E['mmsi'] not in mm['prog']['text'], mm['prog']['text'])
        ped('p3c mmsi: «qual o MMSI cadastrado?» traz o do cadastro na 2ª linha', mm['cad']['text'].split('\n') == [usa, 'Cadastro do app: MMSI %s.' % E['mmsi']], mm['cad']['text'])
        ruins = [k for k in ('epirb', 'epirb2', 'pan', 'dsc', 'pane', 'sea') if E['mmsi'] in mm[k]['text'] or mm[k]['ia'] is not False]
        ped('p3c mmsi: a pergunta do MMSI no EPIRB, no PAN-PAN, no DSC, na pane ou no Seafire é do procedimento (epirb, canal16, seafire), sem o número do cadastro e sem IA', not ruins, ruins)
        for x in out['r']:
            t, q, h, r, c = x['txt'], x['q'], x['hora'], x['r'], x['campos']
            l = lambda k: r[k]['text'].split('\n')
            no = '%s (%s)' % (h, x['x'])
            ped('p3c %s: a posição abre com a posição RELATIVA, o rumo e a velocidade (sem coordenada na 1ª linha nem na fala); as coordenadas ficam na 2ª; a linha das leituras segue a de antes' % no,
                l('posicao')[0] == 'Navegando a %s, rumo %s, %s — %s.' % (t['sog'], t['rumo'], t['relativa'], h) and r['posicao']['fala'] == l('posicao')[0] and not confere.R_COORD.search(l('posicao')[0])
                and l('posicao')[1].startswith('Posição ') and confere.R_COORD.search(l('posicao')[1]) and l('posicao')[2].startswith('SOG %s · proa %s' % (t['sog'], t['proa'])) and r['posicao']['src'] == 'Fonte: telemetria ao vivo · ' + h,
                (l('posicao')[:2], r['posicao']['fala']))
            ped('p3c %s: a profundidade é a do quadro, com a hora, e o calado do cadastro na 2ª linha' % no,
                l('profundidade')[0] == 'Profundidade de %s às %s.' % (t['prof'], h) and l('profundidade')[1] == 'Calado do barco: %s m (cadastro).' % cal and r['profundidade']['fala'] == l('profundidade')[0], l('profundidade'))
            ped('p3c %s: a chegada prevista traz o destino, a hora, a distância, o próximo ponto e o percorrido desde as 07:00 (do quadro)' % no,
                l('eta')[0] == 'Chegada prevista em %s às %s, a %s mn — %s.' % (q['destino'], q['eta'], c['destino_mn'], h) and l('eta')[1] == 'Próximo ponto: %s, a %s mn.' % (q['wp_proximo'], c['wp_mn'])
                and l('eta')[2] == 'Percorrido desde as 07:00: %s mn · velocidade %s.' % (c['distancia_mn'], t['sog']) and r['eta']['fala'] == sem_par(l('eta')[0]), l('eta'))
            ped('p3c %s: «waypoint» abre com o próximo ponto e «distância percorrida» com o percorrido' % no,
                l('wp')[0] == 'Próximo ponto: %s, a %s mn — %s.' % (q['wp_proximo'], c['wp_mn'], h) and l('percorrido')[0] == 'Percorrido desde as 07:00: %s mn · velocidade %s — %s.' % (c['distancia_mn'], t['sog'], h),
                (l('wp')[0], l('percorrido')[0]))
            ped('p3c %s: a chegada cita a rota do plano na fonte' % no, r['eta']['src'].startswith('Fonte: telemetria ao vivo · %s · Plano de navegação' % h), r['eta']['src'])
            # alarmes: nenhum em 12:01:00; em 12:01:45 o AVISO do motor BE, com o que verificar primeiro (os passos do catálogo do guia) e o link para a C3
            if q['alarmes']:
                a0 = q['alarmes'][0]; cat = out['cat'][a0['id']]
                quer = ['Há 1 alarme ativo às %s — %s.' % (h, t['alarmes'])]
                ped('p3c %s: o alarme ativo vem com o nível e o texto na 1ª linha, o que verificar primeiro (os passos do guia) e o ver o alerta (C3)' % no,
                    l('alarmes')[0] == quer[0] and l('alarmes')[1].startswith(cat['titulo'] + ' (desde ') and l('alarmes')[1].endswith(') — o que verificar primeiro:')
                    and l('alarmes')[2:] == ['%d. %s' % (k + 1, p) for k, p in enumerate(cat['passos'])] and any(a.get('href') == 'C3-Leme-Alerta.dc.html#alarme=' + a0['id'] for a in r['alarmes']['acoes'])
                    and cat['fonte'] in r['alarmes']['src'] and r['alarmes']['fala'] == sem_par(quer[0]), (l('alarmes'), r['alarmes']['acoes']))
            else:
                ped('p3c %s: sem alarme, a resposta diz «Nenhum alarme ativo às hora.»' % no, l('alarmes') == ['Nenhum alarme ativo às %s.' % h] and r['alarmes']['fala'] == l('alarmes')[0], l('alarmes'))
            # o alarme que está SOANDO: o app só lê os alarmes do quadro de leitura, então nunca diz «nenhum alarme ativo» (falsa tranquilização): manda conferir o painel dos motores e o plotter primeiro
            conf = 'Confira também o painel dos motores e o plotter: o app só lê os alarmes do quadro de leitura.'
            if q['alarmes']:
                ped('p3c %s: «o alarme está tocando» com alarme no quadro traz o alarme (como a pergunta dos alarmes) e fecha mandando conferir o painel dos motores e o plotter' % no,
                    l('soa')[0] == 'Há 1 alarme ativo às %s — %s.' % (h, t['alarmes']) and l('soa')[-1] == conf and l('soa')[:-1] == l('alarmes') and 'Nenhum alarme ativo' not in r['soa']['text'], l('soa'))
            else:
                ped('p3c %s: «o alarme está tocando» sem alarme no quadro manda conferir o painel dos motores e o plotter e diz que o app só lê os alarmes do quadro, sem «nenhum alarme ativo»' % no,
                    l('soa') == ['Confira o painel dos motores e o plotter: às %s o quadro de leitura não traz alarme ativo, e o app só lê os alarmes do quadro.' % h] and r['soa']['fala'] == sem_par(l('soa')[0])
                    and 'Nenhum alarme ativo' not in r['soa']['text'] and r['soa']['ia'] is False, (l('soa'), r['soa']['fala']))
            ate = nbr(out['ate'], 0)
            if q['alarmes']:
                quer = 'Arrefecimento %s às %s: BE acima de %s °C (AVISO).' % (t['arref'], h, ate)
            else:
                quer = 'Arrefecimento %s às %s, dentro da faixa normal (até %s °C).' % (t['arref'], h, ate)
            td = x['tend']
            ped('p3c %s: a temperatura do motor traz a leitura, o nível contra a faixa do guia (§9), a tendência de 30 s e, com o AVISO, o que verificar primeiro' % no,
                l('arref')[0] == quer and l('arref')[1] == 'Nos últimos 30 s: BB %s · BE %s °C.' % (sinal_tend(td['motor_bb_arref_c']), sinal_tend(td['motor_be_arref_c']))
                and any(s.startswith('Faixa normal: até %s °C (' % ate) for s in l('arref')) and (('o que verificar primeiro:' in r['arref']['text']) == bool(q['alarmes'])), l('arref'))
            ped('p3c %s: as ondas e a temperatura da água são «a bordo agora», nunca previsão (o app não tem previsão de mar)' % no,
                l('ondas')[0] == 'Ondas de %s a bordo agora — %s.' % (t['ondas'], h) and l('ondas')[1] == 'Vento verdadeiro %s, a bordo agora.' % t['vento'] and 'o app não tem previsão de ondas' in l('ondas')[2]
                and l('agua')[0] == 'Água do mar a %s a bordo agora — %s.' % (t['agua'], h) and l('agua')[1] == 'Ar externo %s.' % t['ar'], (l('ondas'), l('agua')))
            ped('p3c %s: como está a navegação abre com o resumo narrado (estado, velocidade, rumo, lugar, chegada) e traz motores, diesel, equipamentos, tempo a bordo, alarmes e tendência do instante' % no,
                l('nav')[0] == 'Navegando a %s, rumo %s, %s; chegada prevista às %s — %s.' % (t['sog'], t['rumo'], t['relativa'], q['eta'], h)
                and l('nav')[1] == '• Motores %s · óleo %s · arrefecimento %s' % (t['rpm'], t['oleo'], t['arref']) and l('nav')[2] == '• Diesel %s · consumo %s · autonomia %s' % (t['diesel'], t['consumo'], t['autonomia'])
                and l('nav')[3] == '• Gerador %s · Seakeeper %s' % (t['gerador'], t['seakeeper']) and l('nav')[4] == '• Vento %s · ondas %s · profundidade %s (a bordo agora)' % (t['vento'], t['ondas'], t['prof'])
                and l('nav')[5] == '• Alarmes: ' + t['alarmes'] and l('nav')[6] == '• Tendência — ' + t['tend'], l('nav'))
            # o cadastro: a pergunta decide a 1ª linha; os números são os do D.embarcacao (calado, comprimento, boca, lotação, registro, modelo)
            ped('p3c %s: pessoas a bordo (registro de saída) e a lotação, sem posição nem quadro' % no,
                l('pessoas')[0] == '%d pessoas a bordo, pelo registro de saída (lotação %d) — %s.' % (E['pessoasBordo'], lot, h), l('pessoas'))
            mod = '%s, do %s' % (E['modelo'], E['fabricante'])
            esperado = {'calado': 'O calado do barco é %s m — %s.' % (cal, h), 'compr': 'O comprimento do barco é %s m — %s.' % (comp, h), 'boca': 'A boca do barco é %s m — %s.' % (boca, h),
                        'lotacao': 'A lotação do barco é de %d pessoas — %s.' % (lot, h), 'registro': 'O registro do barco é %s — %s.' % (E['registro'], h),
                        'modelo': 'O barco é o %s, de %d — %s.' % (mod, E['ano'], h),
                        'dim': '%s: %s, %s m de comprimento, boca de %s m e calado de %s m — %s.' % (E['nome'], mod, comp, boca, cal, h)}
            ruins = {k: l(k)[0] for k, v in esperado.items() if l(k)[0] != v}
            ped('p3c %s: a embarcação responde ao que foi perguntado (calado, comprimento, boca, lotação, registro, modelo, dimensões) com os números do cadastro e a hora' % no, not ruins, ruins)
            ped('p3c %s: a embarcação traz o rótulo e a motorização, e as dimensões, na 2ª e 3ª linhas' % no,
                l('calado')[1] == '%s · %s' % (E['rotulo'], E['motorizacao'])
                and l('calado')[2] == 'Comprimento %s m · boca %s m · calado %s m · deslocamento %s t · lotação %d pessoas · registro %s.' % (comp, boca, cal, nbr(E['deslocamento'], 1), lot, E['registro']), l('calado'))
            # mmsi: a 1ª linha manda usar o MMSI da etiqueta do rádio; a 2ª diz o do cadastro do app; o número só nela
            ped('p3c %s: o MMSI tem duas linhas (o da etiqueta do rádio e «Cadastro do app: MMSI …»), o número só na 2ª e nunca com «programe»' % no,
                l('mmsi') == ['No MAYDAY e no DSC, use o MMSI da etiqueta do rádio (Licença de Estação).', 'Cadastro do app: MMSI %s.' % E['mmsi']] and E['mmsi'] not in r['mmsi']['fala'] and 'programe' not in r['mmsi']['text'].lower()
                and r['mmsi']['ia'] is False and r['mmsi']['fala'] == 'No MAYDAY e no DSC, use o MMSI da etiqueta do rádio.', (l('mmsi'), r['mmsi']['fala']))
            ped('p3c %s: o AIS diz o transponder do cadastro e os alvos do quadro, com a hora' % no,
                l('ais')[0] == '%s com %d alvos às %s.' % (out['ais'], q['ais_alvos'], h) and r['ais']['fala'] == sem_par(l('ais')[0]), l('ais'))
            # sobreDados: a frase padrão (decisão (f)) e a situação de bordo sem posição, com a fonte; foraBarco: «Isso fica fora do barco.» e a situação
            ped('p3c %s: sobreDados é a frase padrão (decisão f) mais a situação de bordo sem posição, com a fonte «este aparelho · modo de apresentação», local' % no,
                l('sobre') == [out['sobre'], 'Situação de bordo agora: ' + t['resumoSemPosicao']] and r['sobre']['src'] == 'Fonte: este aparelho · modo de apresentação' and r['sobre']['ia'] is False
                and r['sobre']['fala'] == out['sobre'] and not confere.R_COORD.search(r['sobre']['text']), (l('sobre'), r['sobre']['src']))
            ped('p3c %s: foraBarco diz «Isso fica fora do barco.» e a situação de bordo sem posição com a hora; sem preço, telefone nem número inventado' % no,
                l('fora') == ['Isso fica fora do barco.', 'Situação de bordo agora: ' + t['resumoSemPosicao']] and r['fora']['src'] == 'Fonte: fontes de bordo consultadas às ' + h and r['fora']['ia'] is False
                and r['fora']['fala'] == 'Isso fica fora do barco.' and not RX['DINHEIRO'].search(r['fora']['text']) and not RX['PESSOAIS'].search(r['fora']['text']), (l('fora'), r['fora']['src']))
            # nenhuma resposta nova leva coordenada fora da posição; a voz é a 1ª linha (sem parênteses)
            ruins = [k for k, v in r.items() if k != 'posicao' and confere.R_COORD.search(v['text'] + v['src'] + v['fala'])]
            ped('p3c %s: nenhuma das respostas novas, fora a posição, leva coordenada (texto, fonte nem fala)' % no, not ruins, ruins)
            ruins = [k for k, v in r.items() if v['fala'] != sem_par(v['text'].split('\n')[0])]
            ped('p3c %s: a voz de cada rota nova é a 1ª linha da resposta, sem parênteses' % no, not ruins, [(k, r[k]['fala'][:80]) for k in ruins])
            ruins = [k for k, v in r.items() if k not in ('mmsi', 'sobre') and h not in v['text'] + '\n' + v['src']]
            ped('p3c %s: toda resposta nova de dado de bordo traz a hora do instante' % no, not ruins, ruins)
            # revisão 4 — a chegada em outro ponto: o ponto citado que não é o destino nem o próximo ponto NÃO recebe a chegada de outro lugar; o destino e o próximo ponto seguem a resposta de antes
            def esperado_eta(alvo, nome):
                if nc(q['destino']) == alvo:
                    return 'Chegada prevista em %s às %s, a %s mn — %s.' % (q['destino'], q['eta'], c['destino_mn'], h)
                if nc(q.get('wp_proximo')) == alvo:
                    return 'Próximo ponto: %s, a %s mn — %s.' % (q['wp_proximo'], c['wp_mn'], h)
                return 'O destino agora é %s, com chegada prevista às %s, a %s mn; %s não é o destino nem o próximo ponto — %s.' % (q['destino'], q['eta'], c['destino_mn'], nome, h)
            ruins = {k: l(k)[0] for k, alvo, nome in (('etaEst', 'estaleirinho', 'Estaleirinho'), ('etaBarra', 'barra sul', 'Barra Sul'), ('etaCabras', 'ilha das cabras', 'Ilha das Cabras'),
                                                     ('etaLaranj', 'ponta das laranjeiras', 'Ponta das Laranjeiras')) if l(k)[0] != esperado_eta(alvo, nome)
                     or (l(k)[0].startswith('O destino agora é ') != (l(k)[-1] == 'O app calcula a chegada só no destino e no próximo ponto da rota.'))}
            ped('p3c %s: «quanto falta para <ponto>?» nunca dá a chegada de OUTRO ponto como se fosse a do citado (o destino e o próximo ponto são os de antes; os demais dizem que não são o destino nem o próximo ponto)' % no, not ruins, ruins)
            ped('p3c %s: «quando chegamos?» é a chegada prevista (a mesma resposta de «qual a hora de chegada?»)' % no, l('etaQuando')[0] == l('eta')[0] and r['etaQuando']['key'] == 'eta', l('etaQuando'))
            # revisão 4 — as horas que faltam: a 1ª linha (a falada) diz o quanto falta, com o limite, a data e a hora
            def faltam_txt(id_, nome):
                return 'Faltam %s h para %s (limite de %s h) ou até %s, o que vier antes — %s.' % (nbr(x['falt'][id_], 1), nome, mil_py(x['ag'][id_]['limite']), x['ag'][id_]['vence'], h)
            ped('p3c %s: «quanto falta para a troca de óleo?» abre com as horas que faltam (do instante), o limite, a data e a hora; a revisão do gerador, igual' % no,
                l('faltaOleo')[0] == faltam_txt('motores-oleo', 'a troca de óleo e filtros dos motores') and r['faltaOleo']['fala'] == sem_par(l('faltaOleo')[0]) and l('faltaOleo')[1].startswith('Horímetros às ')
                and l('faltaGer')[0] == faltam_txt('gerador-revisao', 'a revisão de óleo e filtros do gerador') and r['faltaGer']['fala'] == sem_par(l('faltaGer')[0]) and r['faltaGer']['key'] == 'gerador',
                (l('faltaOleo')[:2], l('faltaGer')[:2]))
            # revisão 4 — o vento a bordo: a 1ª linha é o vento do quadro «a bordo agora», nunca a previsão; a pergunta de previsão (e o relato) seguem a previsão primeiro
            ped('p3c %s: «o vento a bordo agora» abre com o vento verdadeiro do quadro e a hora (o aparente na linha seguinte); «vento aparente», com o aparente; «verdadeiro ou aparente», com os dois' % no,
                l('vento')[0] == 'A bordo agora, vento verdadeiro %s — %s.' % (t['vento'], h) and l('vento')[1] == 'Vento aparente %s.' % t['ventoAp'] and r['vento']['fala'] == l('vento')[0]
                and l('ventoAp')[0] == 'A bordo agora, vento aparente %s — %s.' % (t['ventoAp'], h) and l('ventoAp')[1] == 'Vento verdadeiro %s.' % t['vento']
                and l('ventoDois')[0] == 'A bordo agora, vento verdadeiro %s e aparente %s — %s.' % (t['vento'], t['ventoAp'], h) and 'Previsão' not in l('vento')[0], (l('vento')[:2], l('ventoAp')[:2], l('ventoDois')[:1]))
            ped('p3c %s: «o vento está forte agora» (relato) segue a previsão primeiro, não o vento do quadro na 1ª linha' % no, not l('ventoForte')[0].startswith('A bordo agora, vento') and r['ventoForte']['key'] == 'clima', l('ventoForte')[:2])
            ped('p3c %s: «quanto de fundo tem aqui?» é a profundidade do quadro, com a hora' % no, l('fundo')[0] == l('profundidade')[0] and r['fundo']['key'] == 'profundidade', l('fundo'))
    finally:
        pg.ctx.close()


GRUPOS_3A['p3c'] = grupo_p3c


# Os dados que mudam e os modos: pessoas e calado do cadastro (nunca um número escrito no cérebro), o caminho null (SEM DADOS no modo real e na simulação), o coletor com quadro parcial,
# a CapitaoAlertas ausente, o modo real (simulacao false) e a página do SOS (nada do cadastro, do quadro nem da rota).
JS_P3C_DADOS = """(qs) => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }, o = {};
  Object.keys(qs).forEach((k) => { const a = B.answer(qs[k], op); o[k] = { key: a.key, text: a.text, src: a.src, fala: B.falaCurta(a), ia: B.pedeIA(a, qs[k]), acoes: a.actions || [] }; }); return o; }"""
JS_P3C_COLETOR = """(casos) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false };
  R.fixar('60'); const base = R.em(R.agora());
  return casos.map(([mut, apaga, qs], k) => { R.fixar(String(61 + k)); const q = Object.assign({}, base, mut); delete q.simulado; (apaga || []).forEach((c) => { delete q[c]; }); window.CapitaoTelemetria = { atual: () => q };
    const i = B.instante(); return { fonte: i.fonte, hora: i.hora, r: Object.keys(qs).reduce((o, n) => { const a = B.answer(qs[n], op); o[n] = { key: a.key, text: a.text, fala: B.falaCurta(a) }; return o; }, {}) }; }); }"""
P3C_DADOS = {'pessoas': 'quantas pessoas a bordo?', 'calado': 'qual o calado do barco?', 'prof': 'qual a profundidade?'}
P3C_REAL = {'calado': 'qual o calado do barco?', 'prof': 'qual a profundidade?', 'eta': 'qual a hora de chegada?', 'alarmes': 'tem algum alarme ativo?', 'ondas': 'como está o estado do mar?',
            'arref': 'qual a temperatura do motor?', 'agua': 'qual a temperatura da água?', 'nav': 'como está a navegação?', 'pessoas': 'quantas pessoas a bordo?', 'sobre': 'esses dados são reais?',
            'posicao': 'onde estamos?', 'fora': 'qual o preço do dólar?', 'mmsi': 'qual o MMSI do barco?', 'ais': 'quantos alvos no AIS?', 'emb': 'dimensões do barco'}
P3C_SOS = ['qual o calado do barco?', 'dimensões do barco', 'qual o modelo do barco?', 'qual o registro do barco?', 'quantas pessoas a bordo?', 'qual o MMSI do barco?', 'quantos alvos no AIS?', 'tem AIS?', 'qual a profundidade?',
           'qual a lotação?', 'o alarme está tocando',
           'qual a hora de chegada?', 'tem algum alarme ativo?', 'como está a navegação?', 'onde estamos?', 'esses dados são reais?', 'qual o preço do dólar?', 'qual a temperatura do motor?']


def grupo_p3c_dados(b, muta, ped):
    l = lambda r, k: r[k]['text'].split('\n')
    # (1) pessoas e calado do cadastro: troca o dado, a resposta acompanha (singular, 2 casas); o caminho null segue SEM DADOS (decisão 6)
    pg = pagina(b, muta=muta, extra=";window.CapitaoDados.embarcacao.pessoasBordo = 1; window.CapitaoDados.embarcacao.calado = 1.35;")
    try:
        r = pg.evaluate(JS_P3C_DADOS, P3C_DADOS)
        ped('p3c dados: pessoas a bordo e calado vêm do cadastro (1 pessoa no singular; 1,35 m com duas casas, na embarcação e na profundidade)',
            l(r, 'pessoas')[0] == '1 pessoa a bordo, pelo registro de saída (lotação 12) — 12:01:00.' and l(r, 'calado')[0] == 'O calado do barco é 1,35 m — 12:01:00.' and l(r, 'prof')[1] == 'Calado do barco: 1,35 m (cadastro).',
            (l(r, 'pessoas')[0], l(r, 'calado')[0], l(r, 'prof')[1]))
    finally:
        pg.ctx.close()
    pg = pagina(b, muta=muta, extra=";window.CapitaoDados.embarcacao.pessoasBordo = null; window.CapitaoDados.embarcacao.calado = null;")
    try:
        r = pg.evaluate(JS_P3C_DADOS, P3C_DADOS)
        ped('p3c dados (simulação, cadastro com null): o calado e as pessoas que faltam no cadastro seguem SEM DADOS (o caminho null não se apaga)',
            'SEM DADOS' in l(r, 'calado')[0] and l(r, 'pessoas')[0].startswith('Pessoas a bordo: SEM DADOS') and l(r, 'prof')[1] == 'Calado do barco: SEM DADOS.', (l(r, 'calado')[0], l(r, 'pessoas')[0], l(r, 'prof')[1]))
    finally:
        pg.ctx.close()
    # (2) modo real (simulacao false): sem quadro vivo; o calado null é SEM DADOS; nada de «ao vivo», de hora do replay nem de «apresentação»
    pg = pagina(b, muta=muta, extra=SEM_SIMULACAO + ";window.CapitaoDados.embarcacao.calado = null; window.CapitaoDados.embarcacao.pessoasBordo = null;")
    try:
        r = pg.evaluate(JS_P3C_DADOS, P3C_REAL)
        t = lambda k: r[k]['text']
        ped('p3c real: «qual o calado?» é SEM DADOS e a chave é a da embarcação', r['calado']['key'] == 'embarcacao' and 'SEM DADOS' in l(r, 'calado')[0], l(r, 'calado'))
        ped('p3c real: a profundidade, a temperatura da água e a posição vêm do snapshot de 26/09 (leitura de …), sem «ao vivo» nem a hora do replay',
            'leitura de 26/09/2026 10:12' in l(r, 'prof')[0] and 'leitura de 26/09/2026 10:12' in t('agua') and 'leitura de 26/09/2026 10:12' in l(r, 'posicao')[0]
            and not re.search(r'ao vivo|12:01', t('prof') + t('agua') + t('posicao')), (l(r, 'prof')[0], l(r, 'agua')[0], l(r, 'posicao')[0]))
        ped('p3c real: a posição abre sem coordenada e traz as coordenadas na 2ª linha (a falada não as diz)', not confere.R_COORD.search(l(r, 'posicao')[0]) and confere.R_COORD.search(l(r, 'posicao')[1]) is not None and not confere.R_COORD.search(r['posicao']['fala']),
            (l(r, 'posicao')[:2], r['posicao']['fala']))
        ped('p3c real: sem rota, sem alarmes e sem ondas no snapshot, a regra «Nada inventado»: SEM DADOS (rota) e SEM LEITURA (alarmes, ondas)',
            'SEM DADOS' in t('eta') and 'nenhuma rota ativa' in t('eta') and 'SEM LEITURA' in t('alarmes') and 'SEM LEITURA' in t('ondas') and 'SEM DADOS no app' in t('ondas'), (t('eta'), t('alarmes'), t('ondas')))
        ped('p3c real: a temperatura do motor é a da última leitura com motores ligados, e a navegação é a telemetria do snapshot',
            'última leitura com motores ligados' in t('arref') and r['nav']['key'] == 'navegacao' and t('nav').startswith('Leitura de 26/09/2026 10:12'), (t('arref'), t('nav')[:80]))
        rel = pg.evaluate(JS_P3C_DADOS, {str(i): q for i, q in enumerate(RELATOS_P3C)})
        ruins = [RELATOS_P3C[int(i)] for i, v in rel.items() if v['key'] in LEITURAS_P3C]
        ped('p3c real: o relato com número ou estado também não é a leitura calma no modo real (nem «última leitura com motores ligados» para «a temperatura do motor está em 110»)', not ruins, ruins[:6])
        ped('p3c real: pessoas sem dado é SEM DADOS; o AIS sem o quadro diz SEM LEITURA dos alvos', t('pessoas').startswith('Pessoas a bordo: SEM DADOS') and 'SEM LEITURA' in t('ais'), (t('pessoas'), t('ais')))
        ped('p3c real: sobreDados volta a «cada número vem de uma fonte» (sem «apresentação», «roteiro» nem «mudam a cada segundo»), local e com a fonte da regra da casa; foraBarco leva a última situação',
            t('sobre').startswith('Cada número vem de uma fonte, com a hora da leitura') and not re.search(r'apresentação|roteiro|a cada segundo', t('sobre')) and r['sobre']['src'] == 'Fonte: este aparelho · regra da casa: cada dado com a fonte'
            and r['sobre']['ia'] is False and l(r, 'fora')[0] == 'Isso fica fora do barco.' and l(r, 'fora')[1].startswith('Última situação de bordo: ') and r['fora']['ia'] is False, (t('sobre'), l(r, 'fora')))
        ped('p3c real: o MMSI e a embarcação não mudam com a flag (o cadastro é o mesmo)', l(r, 'mmsi')[0] == 'No MAYDAY e no DSC, use o MMSI da etiqueta do rádio (Licença de Estação).' and r['emb']['key'] == 'embarcacao', (l(r, 'mmsi'), r['emb']['key']))
    finally:
        pg.ctx.close()
    # (3) um coletor de verdade (quadro parcial): 1 alvo no AIS no singular; sem destino, sem alarmes e sem ondas a resposta diz o que o quadro não trouxe e nunca inventa
    pg = pagina(b, muta=muta)
    try:
        qs = {'ais': 'quantos alvos no AIS?', 'eta': 'qual a hora de chegada?', 'alarmes': 'tem algum alarme ativo?', 'ondas': 'como está o estado do mar?', 'prof': 'qual a profundidade?', 'agua': 'qual a temperatura da água?', 'arref': 'qual a temperatura do motor?'}
        cs = pg.evaluate(JS_P3C_COLETOR, [[{'ais_alvos': 1}, [], qs], [{}, ['destino', 'destino_mn', 'eta', 'wp_proximo', 'wp_mn', 'alarmes', 'ondas_m', 'profundidade_m', 'temp_agua_c'], qs],
                                          [{'sog_nos': 0, 'estado': 'Fundeado', 'proa_graus': 120, 'cog_graus': 45}, [], {'posicao': 'onde estamos?', 'nav': 'como está a navegação?'}]])
        um, dois, tres = cs
        ped('p3c coletor: parado (SOG < 0,5) a posição e a navegação dizem a proa e não o rumo sobre o fundo',
            tres['r']['posicao']['text'].split('\n')[0].startswith('Fundeado a 0,0 nós, proa 120°') and 'rumo' not in tres['r']['posicao']['text'].split('\n')[0] and 'rumo' not in tres['r']['nav']['text'].split('\n')[0],
            (tres['r']['posicao']['text'].split('\n')[0], tres['r']['nav']['text'].split('\n')[0]))
        ped('p3c coletor: o quadro do coletor (não do replay) com 1 alvo diz «1 alvo» e com a hora dele', um['fonte'] == 'coletor' and um['r']['ais']['text'].split('\n')[0].endswith(' com 1 alvo às %s.' % um['hora']), (um['fonte'], um['r']['ais']['text'].split('\n')[0]))
        d = dois['r']
        ped('p3c coletor: sem destino, alarmes, ondas, profundidade nem água no quadro, a resposta diz que o quadro não trouxe (com a hora), sem SEM DADOS nem SEM LEITURA e sem «nenhum alarme ativo»',
            d['eta']['text'].startswith('O quadro de %s não trouxe destino nem chegada prevista' % dois['hora']) and d['alarmes']['text'].startswith('O coletor não trouxe a lista de alarmes às %s' % dois['hora'])
            and d['ondas']['text'].startswith('O sensor de ondas não trouxe leitura às %s.' % dois['hora']) and d['prof']['text'].startswith('O sensor de profundidade não trouxe leitura às %s.' % dois['hora'])
            and d['agua']['text'].startswith('O sensor de temperatura da água não trouxe leitura às %s.' % dois['hora']) and 'nenhum alarme ativo' not in d['alarmes']['text']
            and not re.search(r'SEM DADOS|SEM LEITURA', ''.join(v['text'] for v in d.values())), {k: v['text'].split('\n')[0] for k, v in d.items()})
    finally:
        pg.ctx.close()
    # (4) sem a CapitaoAlertas na tela, os alarmes do quadro com o catálogo dão a MESMA resposta (texto e botões) que a lista da CapitaoAlertas
    textos = []
    for scripts in (SCRIPTS, SCRIPTS_SEM_ALERTAS):
        pg = pagina(b, muta=muta, scripts=scripts, fixo='105')
        try:
            a = pg.evaluate("() => { const a = window.CapitaoBrain.answer('tem algum alarme ativo?', { platform: 'app', commit: false }); const m = window.CapitaoBrain.answer('qual a temperatura do motor?', { platform: 'app', commit: false }); return [a.text, a.src, a.actions, m.text, m.src, !!window.CapitaoAlertas]; }")
            textos.append(a)
        finally:
            pg.ctx.close()
    ped('p3c alertas: a resposta dos alarmes e a da temperatura do motor são as mesmas com e sem a CapitaoAlertas na tela (a lista da faixa e a do quadro)',
        textos[0][5] is True and textos[1][5] is False and textos[0][:5] == textos[1][:5] and 'Há 1 alarme ativo' in textos[0][0], (textos[0][0][:120], textos[1][0][:120]))
    # (5) o SOS: nenhuma resposta nova traz o cadastro (registro, modelo, MMSI, pessoas), o quadro nem coordenada; a embarcação responde só o nome
    pg = pagina(b, extra=GETTERS_SOS, scripts=('capitao-dados.js', 'capitao-brain.js'), caminho='SOS-cerebro.html', fixo=None, muta=muta)
    try:
        r = pg.evaluate("(qs) => qs.map((q) => { const a = window.CapitaoBrain.answer(q, { platform: 'app', commit: false }); return [q, a.key, a.text + '\\n' + a.src + '\\n' + window.CapitaoBrain.falaCurta(a)]; })", P3C_SOS)
        todo = '\n'.join(t for _, _, t in r)
        ped('p3c SOS: nenhuma resposta nova do cérebro do SOS traz registro, modelo, fabricante, MMSI do cadastro, pessoas a bordo, leitura do quadro nem coordenada',
            not re.search(r'CIA-23-0417|Marévia|710123456|\b4 pessoas|18,1|1\.333|10,8 m|Barra Sul', todo) and not confere.R_COORD.search(todo), re.findall(r'CIA-23-0417|Marévia|710123456|\b4 pessoas|18,1|1\.333|10,8 m|Barra Sul', todo)[:4])
        # o cadastro inteiro (modelo, fabricante, registro, MMSI, motorização, as medidas e o fabricante e o modelo de cada equipamento) é o que o SOS nunca devolve: lido da própria página, sem número escrito aqui
        cad = pg.evaluate("() => ({ E: window.CapitaoDados.embarcacao, eq: (window.CapitaoDados.equipamentos || []).map((e) => [e.nome, e.fabricante, e.modelo]) })")
        E = cad['E']
        proibidos = [E[k] for k in ('modelo', 'fabricante', 'registro', 'mmsi', 'motorizacao') if E.get(k)] + ['%s m' % nbr(E[k], 2) for k in ('calado', 'comprimento', 'boca') if isinstance(E.get(k), (int, float))]
        proibidos += ['%s t' % nbr(E['deslocamento'], 1), '%d pessoas' % E['lotacao']]
        equips = [x for e in cad['eq'] for x in e[1:] if x and len(x) > 2]   # (o fabricante e o modelo de cada equipamento: o AIS, o Seakeeper… nas respostas do CADASTRO; o nome de um guia ou de um rótulo genérico, como «Seakeeper» na telemetria, não é cadastro)
        do_cadastro = '\n'.join(t for q, k, t in r if k in ('ais', 'embarcacao', 'mmsi', 'pessoas'))
        achados = [v for v in proibidos if v in todo] + [v for v in equips if v in do_cadastro]
        ped('p3c SOS: nenhuma resposta nova do cérebro do SOS traz um valor do cadastro da embarcação, nem o fabricante e o modelo de um equipamento nas respostas do cadastro (o AIS inclusive)', len(proibidos) > 5 and len(equips) > 10 and not achados, achados[:4])
        lidas = pg.evaluate("() => window.__lidas")
        ped('p3c SOS: as respostas novas não leem D.simulacao, D.replay, D.snapshot, D.rota nem D.campos', all(v == 0 for v in lidas.values()) and {'simulacao', 'replay', 'snapshot', 'rota'} <= set(lidas), lidas)
        ped('p3c SOS: a pergunta do MMSI no SOS é só a 1ª linha (o MMSI da etiqueta do rádio), sem o do cadastro', [t for q, k, t in r if k == 'mmsi'][0].split('\n')[0] == 'No MAYDAY e no DSC, use o MMSI da etiqueta do rádio (Licença de Estação).', [t for q, k, t in r if k == 'mmsi'][0][:200])
    finally:
        pg.ctx.close()


GRUPOS_3A['p3c_dados'] = grupo_p3c_dados


# ——————————————— Fase 3, P3D: a ficha, o TERMOS e a voz ———————————————
# (PROMPT Fase 3 «ficha()», «Voz» e §3 «Lista única de termos»; CONTRATO §1.23 txt, §6.6; PARIDADE F31, F32)
ORDEM_FICHA = ['Agora', 'Navegação agora', 'Emergência', 'Sobre o app', 'Embarcação', 'Equipamentos', 'Telemetria', 'Manutenção', 'Peças', 'Horímetros', 'Autonomia e consumo', 'Documentos', 'Pendências',
               'Diário de bordo', 'Equipe e contatos', 'Clima e maré', 'Guias de bordo']
ORDEM_RESUMIDA = ['Agora', 'Navegação agora', 'Sobre o app', 'Embarcação', 'Equipamentos', 'Ficha resumida']
INSTANTES_FICHA = ['0', '60', '100', '105', '149']
PERGUNTA_FICHA, PERGUNTA_META = 'como se faz um nó lais de guia?', 'Oque você faz?'
# as medidas do inst.txt que o «## Navegação agora» repete letra por letra (o texto único, CONTRATO §1.23)
TXT_NAVEGACAO = ['sog', 'stw', 'rumo', 'proa', 'prof', 'vento', 'ondas', 'agua', 'rpm', 'oleo', 'arref', 'carga', 'consumo', 'diesel', 'autonomia', 'gerador', 'seakeeper', 'b24', 'b12', 'porao', 'ancora', 'alarmes',
                 'tend', 'relativa', 'eta']
JS_FICHA = """(xs) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false };
  return { max: B.FICHA_MAX, xs: xs.map((x) => { R.fixar(x); const a = B.answer('%s', op), i = B.instante(), tel = B.answer('Telemetria agora', op), m = B.answer('%s', op), sos = B.answer('homem ao mar', op);
    return { x, hora: i.hora, fase: i.fase && i.fase.nome, txt: i.txt, f: B.ficha('app', '%s', a), r: B.ficha('app', '%s', m), tele: tel.text, sos: B.ficha('app', 'homem ao mar', sos), sosKey: sos.key }; }) }; }""" % (PERGUNTA_FICHA, PERGUNTA_META, PERGUNTA_FICHA, PERGUNTA_META)


# os instantes da medida: os 150 do laço (a volta do contrato) e 4 instantes de cada uma das 576 voltas do dia (a posição pela rota muda a cada volta: o trecho, o destino e os alarmes mudam o texto; a
# ficha resumida chega a 3.992 letras na volta 2, instante 100)
ESPECS_FICHA = [str(x) for x in range(150)] + ['%d@%d' % (x, k) for k in range(576) for x in (0, 40, 100, 149)]
# o tamanho da ficha nos instantes de ESPECS_FICHA (completa e resumida) e o bloco «## Clima e maré» dela; o diário do aparelho com 3 linhas longas (o pior caso do «## Diário de bordo» e das «## Pendências»)
JS_FICHA_TAM = """(xs) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false };
  for (let k = 0; k < 3; k++) B.addDiario({ t: 'Pendência anotada no diário do aparelho ' + k + ': conferir a troca do filtro de óleo do gerador e o cabo da bomba de porão com o técnico, na marina, antes da próxima saída.' });
  return { max: B.FICHA_MAX, xs: xs.map((x) => { R.fixar(String(x)); const a = B.answer('%s', op), m = B.answer('%s', op), f = B.ficha('app', '%s', a), r = B.ficha('app', '%s', m), i = f.indexOf('## Clima e maré'), c = f.slice(i, f.indexOf('\\n## ', i + 5));
    return [f.length, r.length, { n: c.length, previsao: c.indexOf('ECMWF via Open-Meteo, lida às') > 0, mare: c.indexOf('Maré agora') > 0 }]; }) }; }""" % (PERGUNTA_FICHA, PERGUNTA_META, PERGUNTA_FICHA, PERGUNTA_META)


def bloco_ficha(f, titulo):
    """O texto do bloco «## titulo» da ficha (sem o título), ou None."""
    m = re.search(r'^## ' + re.escape(titulo) + r'\n(.*?)(?:\n\n## |\Z)', f, re.S | re.M)
    return m.group(1) if m else None


def grupo_ficha(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        x = pg.evaluate(JS_FICHA, INSTANTES_FICHA)
        tam = []
        for r in x['xs']:
            f, rot = r['f'], 'ficha t=%s' % r['x']
            tit = re.findall(r'^## (.*)$', f, re.M)
            nav = bloco_ficha(f, 'Navegação agora') or ''
            tam.append(len(f))
            ped(rot + ': os blocos na ordem do PROMPT («## Navegação agora» logo depois de «## Agora», «## Emergência» perto do topo)', tit == ORDEM_FICHA, tit)
            ped(rot + ': «## Emergência» entre os primeiros 2.500 letras (o corte do cliente é pelo fim)', 0 <= f.find('## Emergência') < 2500, f.find('## Emergência'))
            ped(rot + ': a navegação abre com o estado, a hora HH:MM:SS do instante e a fase', ('Navegando às ' + r['hora']) in nav and re.match(r'\d\d:\d\d:\d\d$', r['hora']) and ('fase ' + r['fase']) in nav, nav[:100])
            falta = [k for k in TXT_NAVEGACAO if k in r['txt'] and r['txt'][k] not in nav]
            ped(rot + ': cada medida da navegação é o MESMO texto do inst.txt (SOG, STW, rumo, proa, profundidade, vento, ondas, mar, rpm, óleo, arrefecimento, carga, consumo, diesel, autonomia, gerador, Seakeeper, baterias, porão, âncora, alarmes, tendência, posição relativa, ETA)',
                not falta and len([k for k in TXT_NAVEGACAO if k in r['txt']]) >= 22, (falta, nav[:200]))
            lit = r['txt']['diesel'].split(' L')[0]   # (os litros: a resposta «telemetria» os escreve «≈ 1.333 L de 1.600», o inst.txt «1.333 L (83,3 %)»)
            ped(rot + ': a navegação e a telemetria da resposta dizem o mesmo rpm, SOG e litros de diesel', all(r['txt'][k] in r['tele'] and r['txt'][k] in nav for k in ('rpm', 'sog')) and lit in r['tele'] and lit in nav, (r['txt']['rpm'], lit, r['tele'][:80]))
            ped(rot + ': o vento da navegação é o de bordo agora (o vento verdadeiro do quadro, não a previsão)', ('vento a bordo agora ' + r['txt']['vento']) in nav, nav[:300])
            ped(rot + ': o vento aparente, as ondas e a água do mar do quadro também vão «a bordo agora» (decisão 12: vento e mar do quadro só assim; a ficha é o insumo da IA, que não pode dá-los como o mar do dia)',
                all(k in r['txt'] for k in ('ventoAp', 'ondas', 'agua')) and all((rt + ' a bordo agora ' + r['txt'][k]) in nav for k, rt in (('ventoAp', 'vento aparente'), ('ondas', 'ondas'), ('agua', 'água do mar'))), nav[:400])
            ped(rot + ': a navegação traz a rota («rumo (COG)», «SOG», «STW»), a posição relativa e os alarmes', 'rumo (COG)' in nav and 'SOG ' in nav and 'STW ' in nav and ('alarmes: ' + r['txt']['alarmes']) in nav and r['txt']['relativa'] in nav, nav[:160])
            ped(rot + ': nenhuma coordenada (regex do §2.8) e nenhum termo do §3 (ROTULOS, AUTENTICIDADE, VAZIOS, VISIVEL) na ficha', not confere.R_COORD.search(f) and not [n for n in ('ROTULOS', 'AUTENTICIDADE', 'VAZIOS', 'VISIVEL') if RX[n].search(f)],
                (confere.R_COORD.search(f) and confere.R_COORD.search(f).group(0), [n for n in ('ROTULOS', 'AUTENTICIDADE', 'VAZIOS', 'VISIVEL') if RX[n].search(f)]))
            ped(rot + ': a ficha mantém «1.600» (o tanque) e o rpm do quadro com o mesmo texto da resposta «telemetria»', '1.600' in f and r['txt']['rpm'] in f and r['txt']['rpm'] in r['tele'], (r['txt']['rpm'],))
            rs = r['r']; tr = re.findall(r'^## (.*)$', rs, re.M); nr = bloco_ficha(rs, 'Navegação agora') or ''
            ped(rot + ': a ficha resumida leva SÓ uma linha de navegação (o estado, a hora, SOG, rumo, posição relativa, motores, alarmes) e fica abaixo de 4.000 letras', tr == ORDEM_RESUMIDA and len(rs) < 4000 and len([l for l in nr.split('\n') if l and not l.startswith('(Fonte')]) == 1 and ('Navegando às ' + r['hora']) in nr and r['txt']['sog'] in nr and r['txt']['rpm'] in nr, (tr, len(rs), nr[:120]))
            ped(rot + ': a linha da resumida diz cada item com o MESMO texto do inst.txt: «SOG», «rumo (COG)», a posição relativa à rota, «motores» e «alarmes: …» (o título promete, cada um tem o seu mutante)',
                all(x in nr for x in ('SOG ' + r['txt']['sog'], 'rumo (COG) ' + r['txt']['rumo'], r['txt']['relativa'], 'motores ' + r['txt']['rpm'], 'alarmes: ' + r['txt']['alarmes'])), nr[:240])
            ped(rot + ': a ficha da resposta de emergência (sos) sai sem o quadro (nem a navegação) e com a emergência', r['sosKey'] == 'sos' and 'Navegação agora' not in re.findall(r'^## (.*)$', r['sos'], re.M) and not [k for k in ('Telemetria', 'Horímetros', 'Autonomia e consumo') if '## ' + k in r['sos']] and '## Emergência' in r['sos'] and 'Agora' in r['sos'], re.findall(r'^## (.*)$', r['sos'], re.M))
        ped('tamanho da ficha (página sem o capitao-clima.js): nunca passa de B.FICHA_MAX (%d) nos %d instantes (máx. %d); a medida que vale é a de baixo, com a previsão e a maré' % (x['max'], len(tam), max(tam)), all(3000 <= n <= x['max'] for n in tam), tam)
    finally:
        pg.ctx.close()
    # O tamanho que vale (decisão (i) do CLAUDE.md: a ficha vai até 16.000 se passar de ~11.500): o do app de verdade, com o capitao-clima.js e a leitura do dia e a maré salvas (o bloco
    # «## Clima e maré» inteiro, não a frase curta «sem conexão» da página sem ele) e o diário do aparelho no pior caso (3 linhas longas, que também entram nas pendências), nos 150 instantes
    # do laço e na pior segunda-feira (o nome do dia mais longo, na ficha resumida). A constante fica exposta em B.FICHA_MAX; o cliente (12.000) e os Workers sobem a 16.000 na Fase 6.
    pg = pagina(b, muta=muta, clima=True, relogio_ms=RELOGIO_12H00)
    try:
        t = pg.evaluate(JS_FICHA_TAM, ESPECS_FICHA)
        cheias, resumidas, climas = [r[0] for r in t['xs']], [r[1] for r in t['xs']], [r[2] for r in t['xs']]
        mx = max(cheias)
        ped('tamanho da ficha: a ficha completa tem o bloco «## Clima e maré» inteiro (previsão do dia com fonte e hora + maré), não a frase curta «sem conexão»', all(c['previsao'] and c['mare'] and c['n'] > 450 for c in climas), climas[:2])
        ped('tamanho da ficha: entre 3.000 e B.FICHA_MAX (%d) nos %d instantes (as 576 voltas do dia), com a previsão, a maré e o diário do aparelho (máx. %d, mín. %d)' % (t['max'], len(cheias), mx, min(cheias)), all(3000 <= n <= t['max'] for n in cheias), (min(cheias), mx))
        ped('tamanho da ficha (decisão (i)): B.FICHA_MAX é 16.000 se a ficha passa de ~11.500 e 12.000 se não (máx. %d com a previsão e a maré)' % mx, t['max'] == (16000 if mx > 11500 else 12000) and mx > 11500, (t['max'], mx))
        ped('tamanho da ficha: a ficha resumida (pergunta pura sobre o app) fica abaixo de 4.000 letras em todos eles, numa segunda-feira (o nome do dia mais longo; máx. %d)' % max(resumidas), max(resumidas) < 4000 and min(resumidas) > 1500, (min(resumidas), max(resumidas)))
    finally:
        pg.ctx.close()
    # o selo e o aviso da flag antiga nunca entram na ficha (nem sem a simulação); a sessão do convidado
    for nome, extra in (('simulação', ''), ('modo real', SEM_SIMULACAO)):
        pg = pagina(b, extra=';window.CapitaoDados.demo = true; window.CapitaoDados.selo = "SELOX"; window.CapitaoDados.aviso = "AVISOX"; window.CapitaoAuth = { nome: function () { return "Convidado"; } };' + extra, muta=muta)
        try:
            f = pg.evaluate("() => window.CapitaoBrain.ficha('app', '%s', window.CapitaoBrain.answer('%s', { platform: 'app', commit: false }))" % (PERGUNTA_FICHA, PERGUNTA_FICHA))
            ped('ficha (%s): sem D.selo nem D.aviso, e o convidado no «## Agora»' % nome, 'SELOX' not in f and 'AVISOX' not in f and 'usuário: Convidado' in f.split('\n\n')[0], f.split('\n\n')[0])
        finally:
            pg.ctx.close()
    # modo real: sem o coletor, a reserva do snapshot não tem «## Navegação agora» (o «## Telemetria» diz a data da leitura); com o coletor vivo, o bloco vem SEM a posição relativa
    pg = pagina(b, extra=SEM_SIMULACAO, muta=muta)
    try:
        sem = pg.evaluate("() => window.CapitaoBrain.ficha('app', 'telemetria', null)")
    finally:
        pg.ctx.close()
    pg = pagina(b, muta=muta)
    try:
        r = pg.evaluate("""() => { const B = window.CapitaoBrain, R = window.CapitaoReplay; R.fixar('60'); const q3 = Object.assign({}, R.em(R.agora())); delete q3.simulado;
          window.CapitaoDados.simulacao = false; window.CapitaoTelemetria = { atual: () => q3 };
          return { com: B.ficha('app', 'telemetria', null), rel: B.instante().txt.relativa || null, fonte: B.instante().fonte }; }""")
        ts, tc = re.findall(r'^## (.*)$', sem, re.M), re.findall(r'^## (.*)$', r['com'], re.M)
        nc = bloco_ficha(r['com'], 'Navegação agora') or ''
        ped('ficha (modo real): sem o coletor não há «## Navegação agora» (a reserva do snapshot), com os outros blocos e a emergência perto do topo', 'Navegação agora' not in ts and ts[:2] == ['Agora', 'Emergência'] and 'Telemetria' in ts, ts)
        ped('ficha (modo real): com o coletor vivo o bloco vem sem a posição relativa à rota («a 0,5 mn da Barra Sul, chegando») e sem a fase', r['fonte'] == 'coletor' and tc[:3] == ['Agora', 'Navegação agora', 'Emergência'] and 'SOG ' in nc and ' mn da Barra Sul, chegando' not in nc and ' · fase ' not in nc and r['rel'] is None, (r['fonte'], tc[:3], nc[:200]))
    finally:
        pg.ctx.close()
    # simulacao false: as linhas do aparelho com `sim: true` ficam FORA da ficha (diário e pendências); com a simulação, entram
    plantio = """() => { localStorage.setItem('capitao.diario.v1', JSON.stringify([
      { d: '02/11', iso: '2026-11-02T15:00:00.000Z', sys: 'Diário', who: 'Lucas', src: 'chat', sim: true, t: 'LINHAAAA gravada com a apresentação ligada' },
      { d: '02/11', iso: '2026-11-02T14:00:00.000Z', sys: 'Diário', who: 'Lucas', src: 'chat', t: 'LINHABBBB gravada no uso real' },
      { d: '02/11', iso: '2026-11-02T13:00:00.000Z', sys: 'Equipamentos', who: 'Lucas', src: 'app · foto', sim: true, t: 'Foto anexada: LINHACCCC — identificação A CONFIRMAR.' },
      { d: '02/11', iso: '2026-11-02T12:00:00.000Z', sys: 'Equipamentos', who: 'Lucas', src: 'app · foto', t: 'Foto anexada: LINHADDDD — identificação A CONFIRMAR.' }])); const B = window.CapitaoBrain;
      return B.ficha('app', 'como se faz um nó lais de guia?', B.answer('como se faz um nó lais de guia?', { platform: 'app', commit: false })); }"""
    for nome, extra, esperado in (('simulação', '', ('LINHAAAA', 'LINHABBBB', 'LINHACCCC', 'LINHADDDD')), ('modo real', SEM_SIMULACAO, ('LINHABBBB', 'LINHADDDD'))):
        pg = pagina(b, extra=extra, muta=muta)
        try:
            f = pg.evaluate(plantio)
            achou = tuple(k for k in ('LINHAAAA', 'LINHABBBB', 'LINHACCCC', 'LINHADDDD') if k in f)
            pg.evaluate("() => { const B = window.CapitaoBrain; B.addDiario({ t: 'LINHAEEEE grava depois' }); }")
            depois = pg.evaluate("() => JSON.parse(localStorage.getItem('capitao.diario.v1')).map((e) => e.t.slice(0, 9))")
            ped('ficha (%s): as linhas com `sim: true` %s, e o registro só cresce (a gravação depois da ficha guarda as 4 + 1)' % (nome, 'entram' if nome == 'simulação' else 'ficam FORA'), achou == esperado and len(depois) == 5, (achou, depois))
        finally:
            pg.ctx.close()
    # semCoord FINAL (PROMPT §2.8, nos dois modos): é o filtro de TODA a ficha. Só os blocos do `bloco()` passam por um semCoord próprio; «## Embarcação», «## Equipamentos», «## Sobre o app» e a ficha resumida
    # saem só pelo final. Coordenada plantada no cadastro (base, proprietário, registro, modelo e fabricante de equipamento) e no diário do aparelho nunca sai, na completa e na resumida
    PLANTA_COORD = (";(function () { var D = window.CapitaoDados, E = D.embarcacao; E.base = \"Marina 26°59,6'S 048°36,8'W\"; E.proprietario = 'Lucas -26.9931 -48.6140'; E.registro = 'CIA 26°59\\'35\"S 048°36\\'48\"W';"
                    " D.equipamentos.forEach(function (e) { if (e.id === 'motores') e.modelo = 'X lat -26.99312 lon -48.61403'; if (e.id === 'gerador') e.fabricante = '-26,993 / -48,614'; }); })();")
    JS_COORD_FICHA = """(qs) => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }; B.addDiario({ t: 'Fundeio em 26°59,6\\'S 048°36,8\\'W, de manhã.' });
      return qs.map((q) => [q, B.ficha('app', q, B.answer(q, op))]); }"""
    for nome, extra in (('simulação', ''), ('modo real', SEM_SIMULACAO)):
        pg = pagina(b, extra=PLANTA_COORD + extra, muta=muta)
        try:
            fs = pg.evaluate(JS_COORD_FICHA, [PERGUNTA_FICHA, PERGUNTA_META])
            for q, f in fs:
                tit = 'completa' if q == PERGUNTA_FICHA else 'resumida'
                emb, eqp = bloco_ficha(f, 'Embarcação') or '', bloco_ficha(f, 'Equipamentos') or ''
                ped('ficha %s (%s): coordenada plantada no cadastro (base, proprietário, registro, modelo e fabricante de equipamento) e no diário não sai: nenhum trecho casa o R_COORD e os dígitos somem' % (tit, nome),
                    not confere.R_COORD.search(f) and not [x for x in ("26°59", "048°36", "26.9931", "48.6140", "26.99312", "48.61403", "26,993", "48,614") if x in f] and emb.count('(coordenadas só na tela do app)') >= 3 and 'Marina' in emb and 'Lucas' in emb and '(coordenadas só na tela do app)' in eqp,
                    (confere.R_COORD.search(f) and confere.R_COORD.search(f).group(0), emb[:260], eqp[:120]))
        finally:
            pg.ctx.close()
    # a execução (capitao.executado.v1) com `sim: true` (CONTRATO §1.25): com simulacao false ela também fica FORA da ficha (a tarefa volta a atrasada, como a linha do diário), com a simulação ligada vale, uma
    # execução sem `sim` vale nos dois, o registro não perde nada e a ficha não deixa o filtro ligado nas respostas da tela
    JS_EXEC_FICHA = """(plantio) => { localStorage.setItem('capitao.executado.v1', JSON.stringify(plantio)); const B = window.CapitaoBrain, op = { platform: 'app', commit: false }, q = 'como se faz um nó lais de guia?';
      const blk = (f, t) => { const m = new RegExp('(?:^|\\\\n\\\\n)## ' + t + '\\\\n([\\\\s\\\\S]*?)(?=\\\\n\\\\n## |$)').exec(f); return m ? m[1] : ''; };
      const f = B.ficha('app', q, B.answer(q, op)), dep = B.answer('próximas manutenções', op);
      return { man: blk(f, 'Manutenção'), hor: blk(f, 'Horímetros'), depois: dep.text, bruto: localStorage.getItem('capitao.executado.v1') }; }"""
    EX = {'d': '03/11', 't': '00:38', 'iso': '2026-11-03T03:38:00.000Z'}
    TAREFA = 'Teste das bombas de porão'
    nat = lambda t: int((re.search(r'Atrasadas \((\d+)\)', t) or [0, -1])[1])
    OLEO = 'Óleo e filtros dos motores:'   # (a linha do óleo da «## Manutenção» some quando a troca está executada) e a do «## Horímetros»: «Troca de óleo dos motores: executada em …»
    pg = pagina(b, muta=muta)
    try:
        r0 = pg.evaluate(JS_EXEC_FICHA, {})
        n0 = nat(r0['man'])
    finally:
        pg.ctx.close()
    ped('ficha (execução sim: true): sem execução nenhuma o bloco «## Manutenção» tem a tarefa de segurança entre as atrasadas (a medida de comparação: %d), a linha do óleo e a próxima troca nos «## Horímetros»' % n0,
        n0 >= 2 and TAREFA in r0['man'] and OLEO in r0['man'] and 'executada em' not in r0['hor'] and 'Próxima troca de óleo dos motores' in r0['hor'], (n0, r0['man'][:80], r0['hor'][-200:]))
    for nome, extra, plantio, vale in (('simulação', '', dict(EX, sim=True), True), ('simulação', '', EX, True), ('modo real', SEM_SIMULACAO, dict(EX, sim=True), False), ('modo real', SEM_SIMULACAO, EX, True)):
        pg = pagina(b, extra=extra, muta=muta)
        try:
            mapa = {'porao-teste': plantio, 'motores-oleo': plantio}
            r = pg.evaluate(JS_EXEC_FICHA, mapa)
            ped('ficha (%s): a execução (teste das bombas e troca de óleo) %s %s na ficha (a tarefa de segurança %s das atrasadas, a linha do óleo %s e os «## Horímetros» %s)' % (nome, 'com `sim: true`' if plantio.get('sim') else 'sem `sim`', 'vale' if vale else 'NÃO vale', 'sai' if vale else 'continua entre', 'some' if vale else 'continua', 'dizem «executada»' if vale else 'não dizem «executada»'),
                nat(r['man']) == (n0 - 1 if vale else n0) and (TAREFA in r['man']) == (not vale) and (OLEO in r['man']) == (not vale) and ('Troca de óleo dos motores: executada em 03/11 às 00:38' in r['hor']) == vale, (nat(r['man']), n0, r['man'][:120], r['hor'][-160:]))
            ped('ficha (%s, execução %s): o registro só cresce (o mapa do aparelho fica como estava) e a resposta da tela depois da ficha ainda conta a execução (o filtro da ficha não vaza: «próximas manutenções» tem %d atrasadas e sem a linha do óleo)' % (nome, 'com `sim: true`' if plantio.get('sim') else 'sem `sim`', n0 - 1),
                json.loads(r['bruto']) == mapa and nat(r['depois']) == n0 - 1 and TAREFA not in r['depois'].split('Próximas')[0] and OLEO not in r['depois'], (nat(r['depois']), r['depois'][:100], r['bruto'][:80]))
        finally:
            pg.ctx.close()


GRUPOS_3A['ficha'] = grupo_ficha

# semCoord (PROMPT §2.8): as coordenadas não saem do aparelho nos dois modos; o milhar do pt-BR fica
COORD_POSITIVAS = ["26°59,6'S 048°36,8'W", "26° 59.6' S 48° 36.8' W", "-26°59,6' -48°36,8'", "26°59'S 048°36'W", "26º59,58'S", "26°59'35\"S 048°36'48\"W", "-26.9931 / -48.6140", "-26,9931; -48,6140", "-26.9931", "48,61403",
                   "-26.993,-48.614", "-26,993 / -48,614", "posição 26°59,46'S 048°36,71'W.", "lat -26.99312 lon -48.61403"]
COORD_NEGATIVAS = ['1.236,4 h', '1.600 L', '2.050 rpm', '12.000', '1.017,1 hPa', 'BB 2.049 · BE 2.038 rpm', 'serviço 27,79 V', 'a 0,5 mn da Barra Sul, chegando', '12:01:00', '26/09/2026', 'rumo 207°, proa 205°', 'jogo 0,5° · caimento 3,1°',
                   '10,8 m', '83,3 %', '156,800 MHz', 'vento 11,3 nós de 059°', '10.351 letras', 'versão 1.0.9']
JS_COORD = "([pos, neg]) => { const B = window.CapitaoBrain; return { pos: pos.map((s) => [s, B.semCoord(s), B.semCoord('antes ' + s + ' depois')]), neg: neg.map((s) => [s, B.semCoord(s)]), par: B.semCoord(\"26°59,6'S 048°36,8'W\"), ex: typeof B.semCoord }; }"


def grupo_semcoord(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        r = pg.evaluate(JS_COORD, [COORD_POSITIVAS, COORD_NEGATIVAS])
        ruins = [(s, o) for s, o, o2 in r['pos'] if re.search(r'\d', o.replace('(coordenadas só na tela do app)', '')) or re.search(r'\d', o2.replace('(coordenadas só na tela do app)', ''))]
        ped('semCoord: nenhuma das %d coordenadas (graus-minutos com vírgula ou ponto, segundos, decimal de 4 casas, par) deixa dígito' % len(r['pos']), not ruins, ruins[:3])
        ped('semCoord: o milhar do pt-BR, a hora, a data, o rumo e as medidas ficam intactos', all(s == o for s, o in r['neg']), [(s, o) for s, o in r['neg'] if s != o][:3])
        ped('semCoord: o par de coordenadas vira UM aviso só', r['par'] == '(coordenadas só na tela do app)', r['par'])
        ped('semCoord: nenhuma saída tem coordenada pela regex R_COORD do gerador', not [o for s, o, o2 in r['pos'] if confere.R_COORD.search(o) or confere.R_COORD.search(o2)], r['pos'][:2])
    finally:
        pg.ctx.close()


GRUPOS_3A['semcoord'] = grupo_semcoord


def grupo_termos(b, muta, ped):
    """B.TERMOS: as 8 regex do §3 com as fontes do testes/proibidos.json (os mesmos casos da barra e da passa)."""
    pg = pagina(b, muta=muta)
    try:
        T = json.load(open(confere.PROIBIDOS, encoding='utf-8'))
        casos = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proibidos-casos.json'), encoding='utf-8'))
        r = pg.evaluate("""([barra, passa]) => { const B = window.CapitaoBrain, T = B.TERMOS || {}, F = B.TERMOS_FONTES || {};
          return { nomes: Object.keys(T), fontes: Object.keys(F).map((k) => [k, F[k].src, F[k].flags]), flags: Object.keys(T).map((k) => [k, T[k].flags]), tipos: Object.keys(T).map((k) => [k, T[k] instanceof RegExp]),
            barra: Object.keys(barra).map((k) => [k, barra[k].filter((s) => !(T[k] && T[k].test(s)))]), passa: passa.filter((s) => Object.keys(T).some((k) => k !== 'ANEXO' && T[k].test(s))) }; }""", [casos['barra'], casos['passa']])
        nomes = [k for k in T if isinstance(T[k], dict) and 'src' in T[k]]
        ped('TERMOS: as 8 regex do §3 exportadas em B.TERMOS (RegExp) e B.TERMOS_FONTES', sorted(r['nomes']) == sorted(nomes) and len(nomes) == 8 and all(t for k, t in r['tipos']), (r['nomes'], r['tipos']))
        ped('TERMOS: as fontes e as flags são as do testes/proibidos.json (ROTULOS e VAZIOS sem «i»)', sorted(r['fontes']) == sorted([k, T[k]['src'], T[k]['flags']] for k in nomes) and dict(r['flags']).get('ROTULOS') == '' and 'i' in dict(r['flags']).get('AUTENTICIDADE', ''), [k for k, s, f in r['fontes'] if T[k]['src'] != s or T[k]['flags'] != f])
        ped('TERMOS: cada frase da lista «barra» do termos-casos.json casa a regex dela', all(not falta for k, falta in r['barra']), [(k, falta[:2]) for k, falta in r['barra'] if falta])
        ped('TERMOS: nenhuma frase da lista «passa» casa regex alguma (fora a ANEXO)', not r['passa'], r['passa'][:3])
        corpo = pg.evaluate("() => fetch('capitao-brain.js').then((r) => r.text())")   # (o texto que a página recebe: com o mutante, o mutante)
        ped('TERMOS: o cérebro não usa lookbehind (iOS < 16.4)', '(?<' not in corpo, '(?<')
        # a varredura dos 150 instantes do laço (e de 3 instantes de 72 das 576 voltas do dia): os 7 termos que valem para texto de bordo (a ANEXO é do anexo) em cada medida do inst.txt, no texto, na fonte,
        # na fala e na fala lida de cada pergunta (as 50 chaves e as extras da voz) e na ficha, mais a coordenada (§2.8: só na tela; o texto da resposta a leva) no inst.txt, na fala e na ficha. Um número
        # do quadro que tropeça numa regex (a tendência +551 rpm era o prefixo de telefone +55 da PESSOAIS) só aparece em UM instante: a varredura de 2 instantes não pega.
        achados = pg.evaluate("""([xs, qs]) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false }, out = [], RX = {};
          Object.keys(B.TERMOS_FONTES).forEach((k) => { if (k !== 'ANEXO') RX[k] = new RegExp(B.TERMOS_FONTES[k].src, B.TERMOS_FONTES[k].flags); });
          const ach = (x, onde, t, coord) => { if (typeof t !== 'string') return; Object.keys(RX).forEach((k) => { const m = RX[k].exec(t); if (m) out.push([x, onde, k, m[0], t.slice(Math.max(0, m.index - 30), m.index + 40)]); });
            if (coord && B.semCoord(t) !== t) out.push([x, onde, 'COORDENADA', '', t.slice(0, 70)]); };   // (§2.8, a regra do R_COORD do gerador: coordenada só na tela; nenhuma no inst.txt, na fala nem na ficha)
          xs.forEach((x) => { R.fixar(String(x)); const i = B.instante();
            Object.keys(i.txt).forEach((k) => ach(x, 'txt.' + k, i.txt[k], true));
            qs.forEach((q) => { const a = B.answer(q, op), f = B.falaCurta(a); ach(x, 'texto «' + q + '»', a.text, false); ach(x, 'fonte «' + q + '»', a.src, false); ach(x, 'fala «' + q + '»', f, true); ach(x, 'lida «' + q + '»', B.falavel(f), true); });
            ach(x, 'ficha', B.ficha('app', 'telemetria', B.answer('telemetria', op)), true); });
          return out; }""", [ESPECS_FICHA[:150] + ['%d@%d' % (x, k) for k in range(0, 576, 8) for x in (0, 62, 100)], list(PERGUNTAS_VOZ.values())])
        ped('TERMOS: nos 150 instantes do laço e em 216 outros (as voltas do dia) nenhum dos 7 termos nem coordenada casa no inst.txt, nas respostas (texto, fonte, fala e fala lida) das %d perguntas nem na ficha' % len(PERGUNTAS_VOZ), not achados, achados[:3])
        t62 = pg.evaluate("""() => { const R = window.CapitaoReplay, B = window.CapitaoBrain; R.fixar('62'); const i = B.instante(), a = B.answer('telemetria agora', { platform: 'app', commit: false });
          R.fixar('60'); const j = B.instante(); return { tend: i.txt.tend, bb: i.tend.motor_bb_rpm, pessoais: B.TERMOS.PESSOAIS.test(i.txt.tend), tela: a.text.indexOf(i.txt.tend) > 0, j: j.txt.tend }; }""")
        ped('TERMOS: a tendência de 12:01:02 (rpm BB +551) leva um espaço fino depois do sinal, a regex PESSOAIS (+55 e um dígito = telefone) não casa e a resposta «telemetria» diz o mesmo texto; o molde do contrato (+644) não muda',
            t62['bb'] == 551 and 'rpm BB +\u2009551 · BE +548' in t62['tend'] and not t62['pessoais'] and t62['tela'] and t62['j'].startswith('últimos 30 s: rpm BB +644 · BE +648 · '), t62)
    finally:
        pg.ctx.close()


GRUPOS_3A['termos'] = grupo_termos


# ——— a voz (PROMPT Fase 3 «Voz»; F31, F32) ———
# As chaves cuja fala é só a frase (sem a hora do instante): as de FALA_INTEIRA e de emergência, as do (g) (tempo e maré, contatos, fora do barco, sobre os dados, o fallback), o trecho
# do guia, o cadastro sem quadro (áudio, guias), a saudação, o diagnóstico e o registro (Fase 3, P3E, F09: os checklists saíram daqui — a fala deles traz a hora do instante). As outras são de dado de bordo: a fala traz o número e a hora do instante.
VOZ_SO_FRASE = ('sos', 'oleo', 'salvatagem', 'epirb', 'seafire', 'canal16', 'mmsi', 'diagnostico', 'saudacao', 'sobreDados', 'foraBarco', 'fallback', 'mare', 'clima',
                'contatos', 'manual', 'audio', 'diario')
# perguntas que caem numa chave que já tem outra pergunta acima, mas com a 1ª linha própria (a chave `eta` abre com «Percorrido desde as 07:00: …» na pergunta de distância)
VOZ_EXTRA = {'etaPercorrido': 'quantas milhas percorremos hoje?', 'etaProximoPonto': 'qual o próximo waypoint?', 'situacaoAgora': 'situação agora'}
PERGUNTAS_VOZ = dict(PERGUNTA_CHAVE, **VOZ_EXTRA)
VOZ_COM_HORA = [k for k in PERGUNTAS_VOZ if k not in VOZ_SO_FRASE]
# as siglas que a fala diz por extenso (F32): nenhuma pode sobrar na fala de uma resposta
SIGLAS_FALADAS = ('BB', 'BE', 'SOG', 'COG', 'STW', 'TWS', 'TWA', 'TWD', 'AWA', 'AWS', 'HDG', 'DPT', 'ETA', 'MOB', 'EPIRB', 'NMEA', 'RPM', 'STBY')
FALAVEL_CASOS = [
    ('Posição às 12:01:05.', 'Posição às 12 horas, 1 minuto e 5 segundos.'), ('Motores às 12:01:00: ok', 'Motores às 12 horas e 1 minuto: ok'), ('Alarme às 07:00:10', 'Alarme às 7 horas e 10 segundos'),
    ('às 13:00:00', 'às 13 horas'), ('às 01:00:05', 'às 1 hora e 5 segundos'), ('Chegando — 12:01:00.', 'Chegando, às 12 horas e 1 minuto.'),
    ('a 0,5 mn da Barra Sul, chegando — 12:01:00.', 'a 0 vírgula 5 milhas náuticas da Barra Sul, chegando, às 12 horas e 1 minuto.'), ('relação 3:00:15:20', 'relação 3:00:15:20'),
    ('EPIRB', 'épirbi'), ('MOB', 'móbi'), ('Marque MOB no plotter', 'Marque móbi no plotter'), ('NMEA', 'nêmea'),
    ('TWS 12,3 nós', 'velocidade do vento verdadeiro 12 vírgula 3 nós'), ('TWA 45° TWD 059°', 'ângulo do vento verdadeiro 45 graus direção do vento verdadeiro 59 graus'),
    ('AWA 36°', 'ângulo do vento aparente 36 graus'), ('AWS 10,5 nós', 'velocidade do vento aparente 10 vírgula 5 nós'), ('HDG 207°', 'proa 207 graus'),
    ('DPT 10,8 m', 'profundidade 10 vírgula 8 metros'), ('STW 17,8 nós', 'velocidade na água 17 vírgula 8 nós'), ('ETA 12:03', 'chegada prevista 12 horas e 3 minutos'),
    ('COG 207°', 'rumo sobre o fundo 207 graus'), ('SOG 18,1 nós', 'velocidade sobre o fundo 18 vírgula 1 nós'), ('1.017,1 hPa', '1.017 vírgula 1 hectopascais'), ('1 hPa', '1 hectopascal'),
    ('27,79 V', '27 vírgula 79 volts'), ('2.049 rpm', '2.049 rotações por minuto'), ('rpm BB +644 · BE +648', 'rotações por minuto bombordo mais 644, boreste mais 648'),
    # a hora seguida de «:» de pontuação (a 1ª linha da resposta «quantas milhas percorremos hoje?») é lida; o «:» da relação 3:00:15:20 não é hora
    ('desde as 07:00: 65,1 mn', 'desde as 7 horas: 65 vírgula 1 milhas náuticas'), ('Percorrido desde as 07:00: 65,1 mn · velocidade 18,1 nós — 12:01:00.', 'Percorrido desde as 7 horas: 65 vírgula 1 milhas náuticas, velocidade 18 vírgula 1 nós, às 12 horas e 1 minuto.'),
    ('sábado 07:00: tudo', 'sábado 7 horas: tudo'), ('às 07:00:10: ok', 'às 7 horas e 10 segundos: ok'), ('das 07:00 às 12:30: fora', 'das 7 horas às 12 horas e 30 minutos: fora'),
    # o sinal «+» e o número separados por um espaço fino (+ 551 rpm: o «+55» colado a um dígito é o prefixo de telefone da regex PESSOAIS) leem igual ao +644
    ('rpm BB +\u2009551 · BE +548', 'rotações por minuto bombordo mais 551, boreste mais 548'),
    ('diesel −0,5 L', 'diesel menos 0 vírgula 5 litros'), ('18 kts', '18 nós'), ('18 KTS', '18 nós'), ('vento em KT', 'vento em nós'), ('5 kn', '5 nós'), ('BB 2.049 · BE 2.038 rpm', 'bombordo 2.049, boreste 2.038 rotações por minuto'),
]
JS_VOZ_UNIDADE = "(cs) => cs.map(([e]) => window.CapitaoBrain.falavel(e))"
JS_VOZ_CHAVES = """([xs, qs]) => { const B = window.CapitaoBrain, R = window.CapitaoReplay;
  return xs.map((x) => { R.fixar(x); const hora = B.instante().hora;
    return { x, hora, r: Object.keys(qs).map((k) => { const a = B.answer(qs[k], { platform: 'app', commit: false }), f = B.falaCurta(a); return [k, a.key, f, B.falavel(f), a.text]; }) }; }); }"""


def grupo_voz(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        # F32: a leitura de cada sigla e unidade, e a hora com segundos
        r = pg.evaluate(JS_VOZ_UNIDADE, FALAVEL_CASOS)
        ruins = [(e, o, esp) for (e, esp), o in zip(FALAVEL_CASOS, r) if o != esp]
        ped('voz (F32): %d leituras de sigla, unidade e hora (EPIRB = épirbi, MOB = móbi, TWS, AWA, HDG, DPT, STW, ETA, COG, hectopascal, volts, rotações por minuto, 12:01:05)' % len(FALAVEL_CASOS), not ruins, ruins[:3])
        # a fala de cada chave, em dois instantes (a hora e os números mudam)
        x = pg.evaluate(JS_VOZ_CHAVES, [['60', '105'], PERGUNTAS_VOZ])
        for inst in x:
            for k, key, fala, fal, texto in inst['r']:
                rot = 'voz t=%s «%s»' % (inst['x'], k)
                if k in ('sos', 'oleo', 'epirb', 'seafire'):
                    ped(rot + ': a chave de FALA_INTEIRA sai inteira (a resposta toda, sem hora nem trava)', fala == texto and not re.search(r'Às \d\d:\d\d', fala), fala[-60:])
                    continue
                ped(rot + ': a fala não traz parênteses, coordenadas nem sigla solta (BB, SOG, ETA, MOB, EPIRB…) e a falável não deixa "12:01:00"',
                    (k == 'salvatagem' or ('(' not in fala and ')' not in fala)) and not confere.R_COORD.search(fal) and not [g for g in SIGLAS_FALADAS if re.search(r'(?<![A-Za-zÀ-ÿ])' + g + r'(?![A-Za-zÀ-ÿ])', fal)] and not re.search(r'\d:\d\d', fal),   # (a salvatagem fala o texto fixo do protocolo, letra por letra, com o parêntese da lotação)
                    (fala[:80], [g for g in SIGLAS_FALADAS if re.search(r'(?<![A-Za-zÀ-ÿ])' + g + r'(?![A-Za-zÀ-ÿ])', fal)]))
                ped(rot + ': a fala não casa ROTULOS nem AUTENTICIDADE', not RX['ROTULOS'].search(fal) and not RX['AUTENTICIDADE'].search(fal), fal[:100])
                if k in VOZ_SO_FRASE:
                    ped(rot + ': a fala desta chave (emergência, tempo e maré, contatos, fora do barco, sobre os dados, fallback, guias, áudio, checklists, saudação) não ganha a hora do instante no fim', inst['hora'] not in fala, fala[:80])
                if k in VOZ_COM_HORA:
                    ped(rot + ': a fala é uma frase completa com o número e a hora do instante (%s), no máximo 260 letras' % inst['hora'],
                        inst['hora'] in fala and re.search(r'\d', fala) and re.search(r'[.!?]$', fala) and len(fala) <= 260 and re.search(r'\d+ horas?\b', fal), (fala[:140], len(fala)))
        # a hora entra UMA vez só e é a do instante da resposta, mesmo com o relógio andando depois
        r2 = pg.evaluate("""() => { const B = window.CapitaoBrain, R = window.CapitaoReplay; R.fixar('60'); const a = B.answer('nível dos tanques', { platform: 'app', commit: false }), c = B.answer('consumo de diesel', { platform: 'app', commit: false });
          const ab = B.answer('pendências abertas', { platform: 'app', commit: false }), fi = B.answer('autonomia', { platform: 'app', commit: false });
          R.fixar('0@121'); return { abre: B.falaCurta(ab), fim: B.falaCurta(fi), t: B.falaCurta(a), c: B.falaCurta(c), copia: B.falaCurta(Object.assign({}, c, { src: c.src + ' · nota' })) }; }""")
        ped('voz: a hora da fala é a do instante da PRÓPRIA resposta (12:01:00), não a do relógio de quando a fala é montada, e vem uma vez só', r2['c'].count('12:01:00') == 1 and '12:02:30' not in r2['c'] and r2['t'].count('12:01:00') == 1, r2)
        ped('voz: a hora entra na abertura da lista («Pendências abertas, às 12:01:00: …») ou no fim da frase sem dois-pontos («… Às 12:01:00.»)', r2['abre'].startswith('Pendências abertas, às 12:01:00: ') and r2['fim'].endswith('. Às 12:01:00.') and r2['fim'].count(':') == 2, (r2['abre'][:60], r2['fim']))
        ped('voz: a tela copia a resposta (Object.assign) antes de falar e a fala ainda diz a hora do instante dela', r2['copia'].count('12:01:00') == 1, r2['copia'])
    finally:
        pg.ctx.close()
    # a trava de voz: só com a simulação; troca o termo (a palavra inteira, nunca um pedaço colado: «dado de bordoos»), não suprime nem encurta; as chaves de FALA_INTEIRA saem sempre inteiras
    ENTRADAS = ["Os dados são fictícios e o gerador está SEM LEITURA. Veja o guia DEMO do motor.", "Estes valores não são reais, mas a pressão do óleo é 3,9 bar. Manual: MANUAL NO DRIVE.",
                "Na demonstração o MMSI é fictício; o rpm é 2.049.", "O dado SEM DADOS do porão (agenda de demonstração) vem depois.", "Os dados são fictícios e simulados."]
    # a fala (falaCurta, chave `ia`: a 1ª frase e a seguinte, sem parênteses) e a trava direta (travaVoz) de cada entrada, letra por letra
    FALA_TRAVA = ["Os dados são de bordo e o gerador está sem informação. Veja o guia de bordo do motor.", "Estes valores não são de bordo, mas a pressão do óleo é 3,9 bar. Manual: no guia de bordo.",
                  "A bordo o MMSI é de bordo; o rpm é 2.049.", "O dado sem informação do porão vem depois.", "Os dados são de bordo."]
    DIRETA_TRAVA = [FALA_TRAVA[0], FALA_TRAVA[1], FALA_TRAVA[2], "O dado sem informação do porão (agenda de bordo) vem depois.", FALA_TRAVA[4]]
    # cada ramo da troca (a AUTENTICIDADE e os ROTULOS do §3): o substantivo, o verbo, a preposição e a pontuação ficam; só o termo, inteiro, vira «de bordo» (que não varia com o gênero nem o número)
    TRAVA_CASOS = [('As leituras simuladas mudam a cada segundo.', 'As leituras de bordo mudam a cada segundo.'), ('Esse número inventado não vale.', 'Esse número de bordo não vale.'),
                   ('A telemetria simulada mostra 2.050 rpm.', 'A telemetria de bordo mostra 2.050 rpm.'), ('Esse valor é inventado.', 'Esse valor é de bordo.'), ('valores inventados', 'valores de bordo'),
                   ('São dados de demonstração', 'São dados de bordo'), ('São dados de teste', 'São dados de bordo'), ('a navegação foi simulada', 'a navegação foi de bordo'), ('rota simulada do barco', 'rota de bordo do barco'),
                   ('o barco é fictício', 'o barco é de bordo'), ('esta embarcação é de demonstração', 'esta embarcação é de bordo'), ('dados fictícios, simulados e inventados', 'dados de bordo'),
                   ('Isto é uma simulação de navegação.', 'Isto é de bordo de navegação.'), ('é uma simulação', 'é de bordo'), ('foi demonstração', 'foi de bordo'),
                   ('estes valores não são reais', 'estes valores não são de bordo'), ('Os dados não são de verdade.', 'Os dados não são de bordo.'),
                   # a negação fica: trocar o casamento inteiro tirava o «não» e afirmava o contrário («a leitura não é verdadeira» virava «é de bordo»); só o predicado vira «de bordo», com a caixa do «Não»
                   ('Atenção: a leitura de pressão de óleo não é verdadeira, confira o manômetro.', 'Atenção: a leitura de pressão de óleo não é de bordo, confira o manômetro.'), ('Esses números não são verdadeiros.', 'Esses números não são de bordo.'),
                   ('Não é de verdade.', 'Não é de bordo.'), ('Isso não é uma simulação.', 'Isso não é de bordo.'), ('Os valores não são reais e fictícios.', 'Os valores não são de bordo.'),
                   ('Na demonstração, ok', 'A bordo, ok'), ('na demonstração', 'a bordo'), ('a rota da demonstração', 'a rota de bordo'), ('modo demonstração', 'modo de bordo'), ('Modo de simulação ligado', 'Modo de bordo ligado'),
                   ('(agenda de demonstração)', '(agenda de bordo)'), ('embarcação Capitão IA (demonstração)', 'embarcação Capitão IA de bordo'),
                   ('Guia de bordo de demonstração. Veja o resto.', 'Guia de bordo. Veja o resto.'), ('MMSI fictício de demonstração', 'MMSI de bordo'),
                   ('SEM DADOS', 'sem informação'), ('SEM LEITURA do ferro', 'sem informação do ferro'), ('MANUAL NO DRIVE', 'no guia de bordo'), ('snapshot DEMO', 'snapshot de bordo'), ('o guia DEMO do motor', 'o guia de bordo do motor'),
                   ('A pressão do óleo é 3,9 bar.', 'A pressão do óleo é 3,9 bar.'), ('Dados de bordo às 12:01:00.', 'Dados de bordo às 12:01:00.')]
    casos = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proibidos-casos.json'), encoding='utf-8'))['barra']
    corpus = casos['AUTENTICIDADE'] + casos['ROTULOS']
    for nome, extra in (('simulação', ''), ('modo real', SEM_SIMULACAO)):
        pg = pagina(b, extra=extra, muta=muta)
        try:
            t = pg.evaluate("""([es, cs, corpus]) => { const B = window.CapitaoBrain, RX = ['ROTULOS', 'AUTENTICIDADE'].map((k) => new RegExp(B.TERMOS_FONTES[k].src, B.TERMOS_FONTES[k].flags));
              return { ia: es.map((e) => [e, B.falaCurta({ key: 'ia', text: e }), B.travaVoz(e)]), casos: cs.map(([e]) => B.travaVoz(e)),
              corpus: corpus.map((e) => { const o = B.travaVoz(e); return [e, o, RX.some((r) => r.test(o)), B.travaVoz(o) === o]; }),
              inteira: ['sos', 'oleo', 'epirb', 'seafire'].map((k) => [k, B.falaCurta({ key: k, text: es[0] })]), base: B.falaCurta({ key: 'base', text: es[0], seguranca: true }), tem: typeof B.travaVoz, idem: B.travaVoz(es[3]) }; }""", [ENTRADAS, TRAVA_CASOS, corpus])
            if nome == 'simulação':
                ped('trava de voz (%s): a fala das 5 entradas troca o termo e a frase sai inteira, letra por letra (nada de «dado de bordoos», nenhuma sílaba solta, o substantivo e o verbo ficam)' % nome, [f for e, f, tv in t['ia']] == FALA_TRAVA, [f for e, f, tv in t['ia']])
                ped('trava de voz (%s): a trava direta das 5 entradas (com o parêntese que a fala tira)' % nome, [tv for e, f, tv in t['ia']] == DIRETA_TRAVA, [tv for e, f, tv in t['ia']])
                ruins = [(e, o, esp) for (e, esp), o in zip(TRAVA_CASOS, t['casos']) if o != esp]
                ped('trava de voz (%s): %d trocas, uma por ramo (adjetivo concordando, «de demonstração», «de teste», «é uma simulação», «não são reais», «na/da demonstração», «modo demo», «(demonstração)», ROTULOS, duplicata «de bordo de bordo»), letra por letra' % (nome, len(TRAVA_CASOS)), not ruins, ruins[:3])
                ruins = [(e, o) for e, o, resta, idem in t['corpus'] if resta or not idem or re.search(r'bordo[A-Za-zÀ-ÿ]|[A-Za-zÀ-ÿ]bordo|\s\s|^\s*$', o)]
                ped('trava de voz (%s): nas %d frases do §3 (AUTENTICIDADE e ROTULOS) nenhum termo resta, o resto da palavra nunca fica colado em «bordo», não sobra espaço dobrado e a troca é idempotente' % (nome, len(t['corpus'])), not ruins, ruins[:3])
                ped('trava de voz (%s): a negação nunca some (toda frase do §3 com «não» sai da trava com o «não») e a frase negada não vira afirmação' % nome,
                    all(re.search(r'\bn[ãa]o\b', o, re.I) for e, o, resta, idem in t['corpus'] if re.search(r'\bn[ãa]o\b', e, re.I)) and not [1 for (e, esp), o in zip(TRAVA_CASOS, t['casos']) if re.search(r'\bn[ãa]o\b', e, re.I) and not re.search(r'\bn[ãa]o\b', o, re.I)],
                    [(e, o) for e, o, resta, idem in t['corpus'] if re.search(r'\bn[ãa]o\b', e, re.I) and not re.search(r'\bn[ãa]o\b', o, re.I)])
                ped('trava de voz (%s): as chaves de FALA_INTEIRA saem sempre inteiras, mesmo com o termo no texto' % nome, all(f == ENTRADAS[0] for k, f in t['inteira']), t['inteira'])
                ped('trava de voz (%s): o trecho de segurança da base também passa pela trava' % nome, not RX['ROTULOS'].search(t['base']) and not RX['AUTENTICIDADE'].search(t['base']), t['base'])
                ped('trava de voz (%s): idempotente (trocar o que já foi trocado não muda)' % nome, pg.evaluate("(e) => window.CapitaoBrain.travaVoz(window.CapitaoBrain.travaVoz(e)) === window.CapitaoBrain.travaVoz(e)", ENTRADAS[0]), '')
            else:
                ped('trava de voz (%s): com simulacao false o termo fica como está (a regra «Nada inventado» volta)' % nome, all(tv == e for e, f, tv in t['ia']) and all(o == e for (e, esp), o in zip(TRAVA_CASOS, t['casos'])) and all(o == e for e, o, resta, idem in t['corpus'])
                    and 'SEM LEITURA' in t['ia'][0][1] and 'DEMO' in t['ia'][0][1] and 'fictícios' in t['ia'][0][1] and all(f == ENTRADAS[0] for k, f in t['inteira']), t['ia'][:2])
        finally:
            pg.ctx.close()
    # F31: o nome de equipamento que o ditado erra — a tabela é a dos equipamentos DESTA embarcação (D.equipamentos)
    CORRIGE = [('ligar o siker', 'ligar o Seakeeper'), ('estabilizador skip', 'estabilizador Seakeeper'), ('o ploter está ligado', 'o plotter está ligado'), ('garmim', 'Garmin'), ('kamins', 'Cummins'),
               ('sea fire', 'Seafire'), ('o ipirb', 'o EPIRB'), ('vebasto', 'Webasto'), ('leumar', 'Lewmar'), ('reimarine', 'Raymarine'), ('xenquer', 'Schenker'), ('emtrak', 'em-trak'),
               ('vitron', 'Victron'), ('honan', 'Onan'), ('aicom', 'Icom'), ('fiuchon', 'Fusion'), ('o siker.', 'o Seakeeper.'), ('sikerinho', 'sikerinho'), ('desiker', 'desiker'), ('ligar o gerador', 'ligar o gerador')]
    pg = pagina(b, muta=muta)
    try:
        r = pg.evaluate("(cs) => cs.map(([e]) => window.CapitaoBrain.corrigeVoz(e))", CORRIGE)
        ruins = [(e, o, esp) for (e, esp), o in zip(CORRIGE, r) if o != esp]
        ped('ditado (F31): %d nomes de equipamento que o reconhecimento erra viram o nome certo do cadastro (palavra inteira; o que não é erro fica)' % len(CORRIGE), not ruins, ruins[:3])
        u = pg.evaluate("""() => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }, a = B.answer('quantas horas tem o garmim', op), b = B.answer('quantas horas tem o gerador', op), c = B.answer('ligar o siker', op), d = B.answer('ligar o Seakeeper', op);
          return { ak: a.key, bk: b.key, c: [c.key, c.text, c.src], d: [d.key, d.text, d.src] }; }""")
        ped('ditado (F31): o answer() corrige o nome antes de rotear («ligar o siker» responde como «ligar o Seakeeper»)', u['c'] == u['d'], (u['c'][:1], u['d'][:1]))
        # o ditado de verdade (um reconhecedor de mentira): o texto parcial e o final já saem corrigidos
        d = pg.evaluate("""() => new Promise((res) => { const B = window.CapitaoBrain, got = [];
          window.SpeechRecognition = function () { this.start = function () { window.__sr = this; }; this.abort = function () {}; };
          const h = B.ditado({ pausa: 50, parcial: (t) => got.push('p:' + t), fim: (t) => { got.push('f:' + t); res(got); } });
          window.__sr.onresult({ results: [[{ transcript: 'ligar o siker' }]] }); h.parar(); })""")
        ped('ditado (F31): o ditado entrega o texto parcial e o final com o nome corrigido', d == ['p:ligar o Seakeeper', 'f:ligar o Seakeeper'], d)
        # a tabela de variantes é DESTA embarcação (o gerador não marca as grafias erradas do `palavras`: docs_pendentes da Fase 3): trocar a marca no cadastro tira a linha de uso, e este teste a acusa
        MARCAS = ['motores', 'gerador', 'estabilizador', 'climatizacao', 'eletronicos', 'audio', 'vhf', 'dessalinizador', 'ancora', 'piloto', 'ais', 'eletrico']
        m = pg.evaluate("""(ids) => ids.map((id) => { const e = window.CapitaoDados.equipamentos.filter((x) => x.id === id)[0], n = e ? String(e.fabricante).split(' ')[0] : '';
          return [id, n, window.CapitaoBrain.corrigeVoz('ligar o ' + n.toUpperCase())]; })""", MARCAS)
        ruins = [(i, n, o) for i, n, o in m if not n or o != 'ligar o ' + n]
        ped('ditado (F31): a VOZ_EQUIP acompanha as %d marcas do cadastro (a marca em maiúsculas vira a grafia do cadastro; marca nova no gerador pede a linha dela no cérebro)' % len(MARCAS), not ruins, ruins[:3])
    finally:
        pg.ctx.close()
    # a tabela vem do cadastro: sem o equipamento a linha some; o nome certo é a grafia do cadastro; com OUTRO fabricante a linha de marca fica inerte (nunca «cummins» virando o fabricante novo)
    pg = pagina(b, extra=";window.CapitaoDados.equipamentos = window.CapitaoDados.equipamentos.filter(function (e) { return e.id !== 'estabilizador'; });", muta=muta)
    try:
        sem = pg.evaluate("() => [window.CapitaoBrain.corrigeVoz('ligar o siker'), window.CapitaoBrain.corrigeVoz('garmim')]")
        ped('ditado (F31): a embarcação sem o equipamento não tem a linha dele na tabela («siker» fica) e as outras seguem', sem == ['ligar o siker', 'Garmin'], sem)
    finally:
        pg.ctx.close()
    pg = pagina(b, extra=";window.CapitaoDados.equipamentos.forEach(function (e) { if (e.id === 'estabilizador') e.fabricante = 'SEAKEEPER INC'; });", muta=muta)
    try:
        outro = pg.evaluate("() => [window.CapitaoBrain.corrigeVoz('ligar o siker'), window.CapitaoBrain.corrigeVoz('estabilizador skip')]")
        ped('ditado (F31): o nome certo é o fabricante do cadastro (a 1ª palavra, na caixa dele), não um nome fixo no cérebro', outro == ['ligar o SEAKEEPER', 'estabilizador SEAKEEPER'], outro)
    finally:
        pg.ctx.close()
    pg = pagina(b, extra=";window.CapitaoDados.equipamentos.forEach(function (e) { if (e.id === 'estabilizador') e.fabricante = 'Gyromax Pro'; if (e.id === 'motores') e.fabricante = 'Volvo Penta'; });", muta=muta)
    try:
        TEXTOS = ['ligar o siker', 'estabilizador skip', 'ligar o kamins', 'ligar o cummins', 'ligar o motor', 'garmim', 'o ploter', 'o ipirb']
        outra = pg.evaluate("(ts) => ts.map((t) => window.CapitaoBrain.corrigeVoz(t))", TEXTOS)
        ped('ditado (F31): com outro fabricante no cadastro as variantes da marca antiga ficam como estão («kamins» nunca vira «Volvo», «siker» nunca vira «Gyromax»); as outras marcas e o nome do sistema (plotter, EPIRB) seguem',
            outra == ['ligar o siker', 'estabilizador skip', 'ligar o kamins', 'ligar o cummins', 'ligar o motor', 'Garmin', 'o plotter', 'o EPIRB'], outra)
    finally:
        pg.ctx.close()
    # F31: a fala que só diz o equipamento continua a pergunta anterior (só depois de uma resposta que terminou em pergunta, por 10 min)
    pg = pagina(b, muta=muta)
    try:
        pg.evaluate("() => new Promise((r) => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); })")   # (o guia do gerador: a base carregada)
        c = pg.evaluate("""() => { const B = window.CapitaoBrain, op = { platform: 'app' }, o = {}, res = (a) => [a.key, a.src, a.text.slice(0, 80)];
          o.sozinha = res(B.answer('o gerador', { platform: 'app', commit: false }));
          B.limpaConversa(); B.conversa('como ligar?', 'Qual equipamento você quer ligar?');
          o.continua = res(B.answer('o gerador', op)); o.direta = res(B.answer('como ligar o gerador?', { platform: 'app', commit: false }));
          B.limpaConversa(); B.conversa('como ligar?', 'Qual equipamento você quer ligar?'); o.marca = res(B.answer('Seakeeper', op));
          B.limpaConversa(); B.conversa('como ligar?', 'Qual equipamento você quer ligar?'); o.conteudo = res(B.answer('o gerador está desligado', op));
          B.limpaConversa(); B.conversa('como ligar?', 'Qual equipamento você quer ligar?'); o.correcao = res(B.answer('não, o gerador', op));
          B.limpaConversa(); B.conversa('como ligar?', 'Qual equipamento você quer ligar?'); o.e = res(B.answer('e o gerador', op));
          B.limpaConversa(); B.conversa('como ligar?', 'Qual equipamento você quer ligar?'); o.pergunta = res(B.answer('o gerador?', op));
          B.limpaConversa(); B.conversa('como ligar?', 'Vou ligar agora.'); o.semPergunta = res(B.answer('o gerador', op));
          B.limpaConversa(); B.conversa('como ligar?', 'Qual equipamento você quer ligar?'); B.limpaConversa(); o.nova = res(B.answer('o gerador', op));
          B.limpaConversa(); B.conversa('socorro!', 'Onde?'); o.emergencia = res(B.answer('o gerador', op));
          // a emergência NO MEIO (a pergunta «como ligar?» foi respondida com «Qual equipamento?», depois vem a emergência e só então a fala «o gerador»): o contexto de antes não volta
          const meio = (emerg, o2) => { B.limpaConversa(); B.conversa('como ligar?', 'Qual equipamento você quer ligar?'); const e = B.answer(emerg, o2); return [e.key, res(B.answer('o gerador', op))]; };
          o.meioSos = meio('fogo na praça de máquinas, mayday', op); o.meioOleo = meio('alarme de óleo acendeu', op); o.meioEpirb = meio('onde fica o epirb', op); o.meioSemGravar = meio('mayday, homem ao mar', { platform: 'app', commit: false });
          o.meioCanal = meio('roteiro do canal 16', op);
          B.limpaConversa(); B.conversa('como ligar?', 'Qual equipamento você quer ligar?'); B.conversa('mayday, homem ao mar', 'Onde você está?'); o.meioIA = res(B.answer('o gerador', op));   // (a tela conta a emergência com B.conversa)
          B.limpaConversa(); B.conversa('onde fica o epirb', 'Qual EPIRB?'); o.contaEpirb = res(B.answer('o gerador', op)); B.limpaConversa(); B.conversa('roteiro do canal 16', 'Qual canal?'); o.contaCanal = res(B.answer('o gerador', op));
          B.limpaConversa(); B.conversa('como ligar?', 'Qual equipamento você quer ligar?'); B.answer('que horas são?', op); o.meioComum = res(B.answer('o gerador', op));   // (uma resposta comum no meio também troca o contexto, sem continuar)
          B.limpaConversa(); B.conversa('como ligar?', 'Qual equipamento você quer ligar?'); o.semGravar = res(B.answer('o gerador', { platform: 'app', commit: false }));
          B.limpaConversa(); B.conversa('como ligar?', 'Qual equipamento você quer ligar?'); const orig = Date.now; Date.now = () => orig() + 11 * 60e3; o.venceu = res(B.answer('o gerador', op)); Date.now = orig;
          B.limpaConversa(); B.conversa('como ligar?', 'Qual equipamento você quer ligar?'); B.answer('o gerador', op); o.consome = res(B.answer('o gerador', op));
          B.limpaConversa(); B.answer('qual equipamento?', op); o.local = res(B.answer('o gerador', op));
          return o; }""")
        ped('contexto (F31): sozinha, a fala «o gerador» é a resposta pronta do gerador', c['sozinha'][0] == 'gerador', c['sozinha'])
        ped('contexto (F31): «o gerador» depois de «Qual equipamento você quer ligar?» continua «como ligar?» (o guia do gerador, como «como ligar o gerador?»)', c['continua'][0] == 'base' and c['continua'][:2] == c['direta'][:2] and c['direta'][0] == 'base', (c['continua'], c['direta']))
        ped('contexto (F31): a marca sozinha («Seakeeper») também continua a pergunta anterior', c['marca'][0] == 'base' and 'Seakeeper' in c['marca'][1], c['marca'])
        ped('contexto (F31): fala com conteúdo («o gerador está desligado»), correção («não, o gerador»), «e o gerador» e pergunta («o gerador?») não continuam', all(c[k][0] != 'base' for k in ('conteudo', 'correcao', 'e', 'pergunta')), [(k, c[k][0]) for k in ('conteudo', 'correcao', 'e', 'pergunta')])
        ped('contexto (F31): sem pergunta na resposta anterior, depois do NOVA, com o app sem gravar (commit false), passados 10 min e em emergência, a fala não continua', all(c[k][0] == 'gerador' for k in ('semPergunta', 'nova', 'emergencia', 'venceu')) and c['semGravar'][0] == 'gerador', {k: c[k][0] for k in ('semPergunta', 'nova', 'emergencia', 'semGravar', 'venceu')})
        ped('contexto (F31): a continuação vale uma vez (a resposta local não termina em pergunta) e a resposta local nunca abre a continuação', c['consome'][0] == 'gerador' and c['local'][0] == 'gerador', (c['consome'][0], c['local'][0]))
        ped('contexto (F31): uma emergência entre a pergunta e a fala (mayday, alarme de óleo, EPIRB, canal 16, com ou sem gravar, ou contada pela tela) encerra o contexto: «o gerador» é a resposta pronta do gerador',
            [c[k][0] for k in ('meioSos', 'meioOleo', 'meioEpirb', 'meioSemGravar', 'meioCanal')] == ['sos', 'oleo', 'epirb', 'sos', 'canal16'] and all(c[k][1][0] == 'gerador' for k in ('meioSos', 'meioOleo', 'meioEpirb', 'meioSemGravar', 'meioCanal'))
            and all(c[k][0] == 'gerador' for k in ('meioIA', 'meioComum', 'contaEpirb', 'contaCanal')), {k: c[k] for k in ('meioSos', 'meioOleo', 'meioEpirb', 'meioSemGravar', 'meioCanal', 'meioIA', 'meioComum', 'contaEpirb', 'contaCanal')})
    finally:
        pg.ctx.close()
    # o SOS: a fala, a trava e a correção não leem o D.simulacao nem o D.equipamentos (CONTRATO §1.3), e a correção nem age
    getters = "window.__lidas = {}; (function () { var D = window.CapitaoDados; ['simulacao', 'equipamentos', 'replay', 'snapshot', 'rota', 'campos'].forEach(function (k) { if (!(k in D)) return; var v = D[k]; window.__lidas[k] = 0; Object.defineProperty(D, k, { get: function () { window.__lidas[k]++; return v; }, set: function (x) { v = x; }, configurable: true, enumerable: true }); }); })();"
    pg = pagina(b, extra=getters, scripts=('capitao-dados.js', 'capitao-brain.js'), caminho='SOS-cerebro.html', fixo=None, muta=muta)
    try:
        r = pg.evaluate("""(qs) => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }; Object.keys(window.__lidas).forEach((k) => { window.__lidas[k] = 0; });
          const falas = qs.map((q) => { const a = B.answer(q, op); return B.falavel(B.falaCurta(a)); });   // (as respostas de dado de bordo leem o cadastro, como antes: só a flag e o quadro são vigiados aqui)
          const lidasAnswers = Object.assign({}, window.__lidas); Object.keys(window.__lidas).forEach((k) => { window.__lidas[k] = 0; });
          B.conversa('como ligar?', 'Qual?'); const c = B.corrigeVoz('ligar o siker'), t = B.travaVoz('SEM DADOS'), f = B.falaCurta({ key: 'ia', text: 'SEM DADOS do motor.' }), e = B.falaCurta(B.answer('MAYDAY, homem ao mar!', op));
          const lidasNovas = Object.assign({}, window.__lidas), k = B.answer('o gerador', { platform: 'app' }).key;   // (a continuação não age no SOS: «o gerador» é a resposta pronta, que lê o cadastro como antes)
          return { falas: falas.length, c, t, f, k, lidasAnswers, lidasNovas, e: e.slice(0, 40) }; }""", list(PERGUNTA_CHAVE.values()))
        ped('voz (SOS): a fala de TODA chave não lê D.simulacao, D.replay, D.snapshot, D.rota nem D.campos; a correção, a trava e a continuação não leem nem D.equipamentos, e não agem',
            r['falas'] == len(PERGUNTA_CHAVE) and r['c'] == 'ligar o siker' and r['t'] == 'SEM DADOS' and r['f'] == 'SEM DADOS do motor.' and r['k'] == 'gerador'
            and all(v == 0 for k, v in r['lidasAnswers'].items() if k != 'equipamentos') and r['lidasNovas'].get('simulacao') == 0 and 'equipamentos' in r['lidasNovas']
            and r['lidasNovas']['equipamentos'] == 0 and r['e'].startswith('Emergência'), r)
    finally:
        pg.ctx.close()


GRUPOS_3A['voz'] = grupo_voz



# Mutantes do cérebro (cada um tem de ser acusado por `confere_instante` nos grupos indicados): (nome, trecho único do capitao-brain.js, troca, grupos)
MUTANTES_3A = [
    ('o instante nunca é solto (o contador não desce)', "    try { return f(); } finally { if (--CONG.n === 0) CONG.inst = null; }", "    try { return f(); } finally { }", ('uma',)),
    ('o instante só é solto sem exceção (sem finally)', "    try { return f(); } finally { if (--CONG.n === 0) CONG.inst = null; }", "    var r = f(); if (--CONG.n === 0) CONG.inst = null; return r;", ('uma',)),
    ('Date.now numa segunda leitura (a hora da ficha)', "    var ms = CONG.inst && CONG.inst.ms;   // a hora da ficha é a do instante da pergunta (a mesma da telemetria)", "    var ms = Date.now();", ('uma',)),
    ('o resumo lê um instante novo', "      if (i) return x && x.semPosicao ? i.txt.resumoSemPosicao : i.txt.resumo;", "      if (i) return lerInstante().txt.resumo;", ('uma',)),
    ('a ficha ignora o instante da resposta', "return congela(function () { return ficha1(p, q, a); }, a && a._inst);", "return congela(function () { return ficha1(p, q, a); });", ('uma',)),
    ('a resposta não leva o instante dela', "a = marca(responde(junto || q1, ctx));", "a = responde(junto || q1, ctx);", ('uma',)),
    ('a fonte do replay vira «coletor NMEA»', "      fonte: v.fonteTxt });", "      fonte: 'coletor NMEA \u00b7 ao vivo ' + v.hora });", ('uma',)),
    ('o VIVO escreve «coletor NMEA» para o replay', "      return { text: r.text, src: 'Fonte: ' + i.fonteTxt, actions: base.actions };", "      return { text: r.text, src: 'Fonte: coletor NMEA \u00b7 ao vivo ' + i.hora, actions: base.actions };", ('uma',)),
    ('instante fora do SOS devolvendo o quadro da reserva', "    if (EM_SOS) return null;   // o SOS não tem instante: nem quadro, nem resumo, nem posição (a guarda é a do rodapé; aqui antes de qualquer leitura)", "", ('sos',)),
    ('o resumo do SOS deixa de ser o do plotter', "      if (EM_SOS) return P.plotter || 'POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER';", "", ('sos',)),
    ('a tendência leva o diesel na virada das 07:00', "      if (i.ms - 30000 >= A.ancora(i.ms)) {", "      if (true) {", ('virada',)),
    ('a fronteira da virada (30 s depois da âncora) sem o diesel', "      if (i.ms - 30000 >= A.ancora(i.ms)) {", "      if (i.ms - 30000 > A.ancora(i.ms)) {", ('virada',)),
    ('o resumo leva a coordenada', "      if (t.sog) itens.push('SOG ' + t.sog);", "      if (t.sog) itens.push('SOG ' + t.sog + ' ' + A.fmt.coord(q.lat, q.lon));", ('resumo',)),
    ('o modo real lê o quadro da reserva como se fosse vivo', "    var v = i && VIVAS[i.fonte] === 1 && i.q && i.txt ? i : null, q, t, A, cap, lig, ab;", "    var v = i && i.q && i.txt ? i : null, q, t, A, cap, lig, ab;", ('real',)),
    ('sem o CapitaoAgora o instante some em vez de cair na reserva', "      if (!i || typeof i !== 'object' || !i.q || typeof i.q !== 'object') return instanteReserva();", "      if (!i || typeof i !== 'object' || !i.q || typeof i.q !== 'object') return null;", ('real',)),
    ('o faltam das tarefas por horas fica o da agenda', "  function faltam(t) { var i = vivo(), f = i && i.calc && i.calc.faltam && i.calc.faltam[t.id]; return typeof f === 'number' ? f : t.horas.faltam; }", "  function faltam(t) { return t.horas.faltam; }", ('forma',)),
    ('a autonomia fica a do snapshot', "AUT = v.calc && v.calc.autonomia ? { horas: v.calc.autonomia.horas, mn: v.calc.autonomia.mn, lenta: v.calc.autonomia.lenta } : { horas: null, mn: SD, lenta: SD };", "AUT = AUT0;", ('forma',)),
    # —— revisão da P3A ——
    ('o «desde o abastecimento» fica o da agenda (CON = CON0)', "    CON = Object.assign({}, CON0, { desdeAbast: ab ?", "    CON = CON0; var xx = ({ desdeAbast: ab ?", ('forma',)),
    ('a fonte do instante some do consumo e do checklist (comTele vazio)', "  function comTele() { return vivo() ? ' · ' + SNAP.fonte : ''; }", "  function comTele() { return ''; }", ('forma',)),
    ('o «faltam» da manutenção volta ao da agenda', "' h — faltam ' + nb(faltam(oleoM)) + ' h.'", "' h — faltam ' + nb(oleoM.horas.faltam) + ' h.'", ('forma',)),
    ('a hora da leitura do diesel some (DI.hora vazio)', "hora: v.hora, nota: 'leitura' } : { capacidade: cap, tanques: dieselN },", "hora: '', nota: 'leitura' } : { capacidade: cap, tanques: dieselN },", ('forma',)),
    ('canal16 cita a telemetria na fonte (FT.tele)', "src: FT.proto + ' · canal 16 e MMSI do rádio de bordo'", "src: FT.tele + ' · canal 16 e MMSI do rádio de bordo'", ('forma',)),
    ('o anexo não leva o instante dele (answerAttachment sem marca)', "return congela(function () { return marca(anexo1(kind, file, ctx)); }); }", "return congela(function () { return anexo1(kind, file, ctx); }); }", ('uma',)),
    ('cada chamada aninhada lê o instante de novo (CONG.n === 0 → true)', "    if (CONG.n === 0) {\n      CONG.inst = de || lerInstante();", "    if (true) {\n      CONG.inst = de || lerInstante();", ('aninhadas',)),
    ('a reserva não repõe o S (S = S0)', "      S = S0; AUT = AUT0; CON = CON0;", "      AUT = AUT0; CON = CON0;", ('transicao',)),
    ('a reserva não repõe a autonomia (AUT = AUT0)', "      S = S0; AUT = AUT0; CON = CON0;", "      S = S0; CON = CON0;", ('transicao',)),
    ('a reserva não repõe o consumo (CON = CON0)', "      S = S0; AUT = AUT0; CON = CON0;", "      S = S0; AUT = AUT0;", ('transicao',)),
    ('a tendência sem a guarda do replay (um coletor ganharia tendência)', "    if (i.fonte !== 'replay' || !R || typeof R.em !== 'function' || !A || !A.fmt) return undefined;", "    if (!R || typeof R.em !== 'function' || !A || !A.fmt) return undefined;", ('coletor',)),
    ('o VIVO escreve a fonte do replay para o coletor', "      return { text: r.text, src: 'Fonte: ' + i.fonteTxt, actions: base.actions };", "      return { text: r.text, src: 'Fonte: telemetria ao vivo · ' + i.hora, actions: base.actions };", ('coletor',)),
    ('a posição relativa sai sem a simulação (relativaDe sem a guarda da flag)', "    if (D.simulacao !== true || !R || !R.base ||", "    if (!R || !R.base ||", ('coletor',)),
    ('o alarme de um quadro de coletor vem da CapitaoAlertas (do replay)', "try { if (i.fonte === 'replay' && AL &&", "try { if (AL &&", ('coletor',)),
    ('a recarrega que lança deixa o instante vivo', "catch (e) { CONG.inst = EM_SOS ? null : instanteReserva(); try { recarrega(null); } catch (e2) {} }", "catch (e) { try { recarrega(null); } catch (e2) {} }", ('falha',)),
    ('a recarrega que lança sobe para a pergunta (sem try/catch)', "      try { recarrega(CONG.inst); } catch (e) { CONG.inst = EM_SOS ? null : instanteReserva(); try { recarrega(null); } catch (e2) {} }", "      recarrega(CONG.inst);", ('falha',)),
    ('o resumo sem quadro vivo leva a coordenada', "[semLocal ? (S.estado || '') : SNAP.local,", "[semLocal ? (S.estado || '') : SNAP.local + ' · ' + SNAP.pos,", ('real',)),
    ('o resumo sem quadro vivo ignora o semPosicao', "      return resumoReserva(!!(x && x.semPosicao));", "      return resumoReserva(false);", ('real',)),
    ('o resumo sem quadro vivo passa de 300 letras', "if (x && (r ? r + ' · ' + x : x).length + fim.length <= 300) r =", "if (x) r =", ('real',)),
    ('o alarme ignora a CapitaoAlertas', "    try { if (i.fonte === 'replay' && AL && typeof AL.ativos === 'function') lista = AL.ativos(i.ms); } catch (e) {}", "", ('alarmes',)),
    ('o alarme pergunta à CapitaoAlertas de outro instante (sem o ms)', "lista = AL.ativos(i.ms);", "lista = AL.ativos();", ('alarmes',)),
    ('o alarme da CapitaoAlertas perde o rótulo', "return a.rotulo + ': ' + a.texto;", "return a.texto;", ('alarmes',)),
    ('o molde do alarme de reserva diz «limite»', "' (' + (a.valor > a.limite ? 'acima' : 'abaixo') + ' de ' + lt + un + ')'", "' (limite ' + lt + un + ')'", ('alarmes',)),
    ('o Seakeeper sem leitura vira «desligado»', "(typeof q.seakeeper_ativo !== 'boolean' ? 'SEM LEITURA' : q.seakeeper_ativo ?", "(q.seakeeper_ativo ?", ('parcial',)),
    ('o gerador sem leitura vira «desligado»', "estado: bool(q.gerador_ativo) ? (q.gerador_ativo ? 'ligado' : 'desligado') : undefined, horas:", "estado: q.gerador_ativo ? 'ligado' : 'desligado', horas:", ('parcial',)),
    ('a autonomia do quadro parcial fica a do snapshot', ": { horas: null, mn: SD, lenta: SD };", ": AUT0;", ('parcial',)),
    ('o «desde o abastecimento» do quadro parcial fica o da agenda', ": { litros: SD, desde: '—', horas: SD } });", ": CON0.desdeAbast });", ('parcial',)),
    ('os motores sem leitura viram «motores undefined»', "      motores: temRpm ? 'motores ' + M.estado", "      motores: true ? 'motores ' + M.estado", ('parcial',)),
    ('o destinos divide a autonomia que não existe', "(typeof AUT.mn === 'number' ? Math.floor(AUT.mn / 2) : SD)", "Math.floor(AUT.mn / 2)", ('parcial',)),
    # —— revisão da P3A (2): o mapeamento do quadro para S, M, G, DI, T e SNAP; o milhar; a coordenada do rpm; o `_inst`; as leituras do SOS ——
    ('o banco de 24 V lê a bateria de 12 V (bat24)', "bat24: q.bateria_0_tensao_v, bat12: q.bateria_2_tensao_v,", "bat24: q.bateria_2_tensao_v, bat12: q.bateria_2_tensao_v,", ('numeros',)),
    ('o vento e a direção do vento trocados', "vento: q.vento_verdadeiro_nos, ventoDe: q.vento_verdadeiro_angulo,", "vento: q.vento_verdadeiro_angulo, ventoDe: q.vento_verdadeiro_nos,", ('numeros',)),
    ('o ar e a água trocados', "ar: q.temp_ar_externo_c, agua: q.temp_agua_c,", "ar: q.temp_agua_c, agua: q.temp_ar_externo_c,", ('numeros',)),
    ('o tanque de água doce e o de águas cinzas trocados', "tanques: { agua: q.tanque_agua_pct, cinzas: q.tanque_cinzas_pct, negras: q.tanque_negras_pct },", "tanques: { agua: q.tanque_cinzas_pct, cinzas: q.tanque_agua_pct, negras: q.tanque_negras_pct },", ('numeros',)),
    ('a SOG do quadro mais 1 nó', "      sog: q.sog_nos, proa: q.proa_graus,", "      sog: q.sog_nos + 1, proa: q.proa_graus,", ('numeros',)),
    ('os horímetros dos motores BB e BE trocados', "horimetro: temHor ? [q.motor_bb_horimetro_h, q.motor_be_horimetro_h] : undefined", "horimetro: temHor ? [q.motor_be_horimetro_h, q.motor_bb_horimetro_h] : undefined", ('numeros',)),
    ('as horas do gerador leem a potência (gerador_kw)', "horas: q.gerador_horimetro_h, kw: q.gerador_kw,", "horas: q.gerador_kw, kw: q.gerador_kw,", ('numeros',)),
    ('o estado dos motores só olha o motor BB (lig)', "lig = q.motor_bb_rpm > 0 || q.motor_be_rpm > 0;", "lig = q.motor_bb_rpm > 0;", ('ligados',)),
    ('o estado dos motores só olha o motor BE (lig)', "lig = q.motor_bb_rpm > 0 || q.motor_be_rpm > 0;", "lig = q.motor_be_rpm > 0;", ('ligados',)),
    ('o diesel do boreste copia o de bombordo (SNAP.diesel)', "' % · BE ' + nb(q.diesel_be_pct) + ' % (≈ '", "' % · BE ' + nb(q.diesel_bb_pct) + ' % (≈ '", ('numeros',)),
    ('o diesel do boreste copia o de bombordo (DI.be, da autonomia)', "diesel: temDie ? { bb: q.diesel_bb_pct, be: q.diesel_be_pct,", "diesel: temDie ? { bb: q.diesel_bb_pct, be: q.diesel_bb_pct,", ('numeros',)),
    # (S.quando e S.hora do quadro vivo ninguém lê, só o montaSnap() da reserva: os mutantes equivalentes não entram; as respostas leem o SNAP.quando, montado no mesmo recarrega)
    ('a hora do «Snapshot de» sem os segundos (SNAP.quando = hhmm)', "    troca(SNAP, { quando: v.hora, hora: v.hora, dia: '',", "    troca(SNAP, { quando: v.hhmm, hora: v.hora, dia: '',", ('numeros',)),
    ('«desde o abastecimento» sem o separador de milhar (autonomia)', "Consumido desde o abastecimento de ' + CON.desdeAbast.desde.slice(0, 5) + ': ≈ ' + litrosTxt(CON.desdeAbast.litros) + ' L (", "Consumido desde o abastecimento de ' + CON.desdeAbast.desde.slice(0, 5) + ': ≈ ' + CON.desdeAbast.litros + ' L (", ('numeros',)),
    ('«desde o abastecimento» sem o separador de milhar (consumo)', "Desde o abastecimento de ' + CON.desdeAbast.desde.slice(0, 5) + ': ≈ ' + litrosTxt(CON.desdeAbast.litros) + ' L (", "Desde o abastecimento de ' + CON.desdeAbast.desde.slice(0, 5) + ': ≈ ' + CON.desdeAbast.litros + ' L (", ('numeros',)),
    ('o par de rpm da pressão do óleo volta a «a/b» (coordenada decimal)', "(vivo() ? vivo().txt.rpm || '— rpm' : (M.rpm ? M.rpm.join('/') : '—') + ' rpm')", "(M.rpm ? M.rpm.join('/') : '—') + ' rpm'", ('coordenada', 'numeros')),
    ('o instante da resposta (_inst) enumerável: entraria no JSON com lat e lon', "{ value: CONG.inst, enumerable: false, configurable: true }", "{ value: CONG.inst, enumerable: true, configurable: true }", ('marca',)),
    ('o instante da resposta (_inst) como propriedade comum', "try { Object.defineProperty(a, '_inst', { value: CONG.inst, enumerable: false, configurable: true }); } catch (e) {}", "try { a._inst = CONG.inst; } catch (e) {}", ('marca',)),
    ('o instante lê D.simulacao antes da guarda do SOS', "  function lerInstante() {\n    var A, i;\n", "  function lerInstante() {\n    var A, i, _x = D.simulacao;\n", ('sos',)),
    ('o resumo do SOS lê D.replay', "      if (EM_SOS) return P.plotter || 'POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER';", "      if (EM_SOS) { var _y = D.replay; return P.plotter || 'POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER'; }", ('sos',)),
    ('o cérebro lê D.snapshot na carga do SOS', "S = EM_SOS ? {} : (D.snapshot || {}),", "S = (D.snapshot, EM_SOS ? {} : (D.snapshot || {})),", ('sos',)),
    # —— revisão da P3A (3): o óleo não cita o instante; a API da resposta de emergência (_inst, resumoAgora(a), ficha(p, q, a)) ——
    ('o óleo (queda ou alarme) cita o instante na fonte (comTele)', "OLEO_PASSOS + '\\n' + GRAVAR_AGORA, src: 'Fonte: ' + guia('g_motores') + ' §4'", "OLEO_PASSOS + '\\n' + GRAVAR_AGORA, src: 'Fonte: ' + guia('g_motores') + ' §4' + comTele()", ('forma',)),
    ('o óleo (queda ou alarme) cita o instante na fonte (FT.tele)', "OLEO_PASSOS + '\\n' + GRAVAR_AGORA, src: 'Fonte: ' + guia('g_motores') + ' §4'", "OLEO_PASSOS + '\\n' + GRAVAR_AGORA, src: FT.tele + ' · ' + guia('g_motores') + ' §4'", ('forma',)),
    ('a resposta de emergência leva o instante (marca sem a guarda)', "function marca(a) { if (a && typeof a === 'object' && !emerg(a)) {", "function marca(a) { if (a && typeof a === 'object') {", ('emerg', 'marca')),
    ('o resumoAgora(a) de emergência devolve o quadro', "    if (emerg(x)) return P.plotter || 'POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER';\n", "", ('emerg',)),
    ('a ficha(p, q, a) de emergência leva o Telemetria', "    var bloco = function (titulo, f) { if (emergencia && QUADRO[titulo]) return;", "    var bloco = function (titulo, f) { if (false) return;", ('emerg',)),
    ('a ficha(p, q, a) de emergência leva só o Telemetria (a guarda esquece o Horímetros)', "var QUADRO = { 'Telemetria': 1, 'Navegação agora': 1, 'Horímetros': 1, 'Autonomia e consumo': 1 };", "var QUADRO = { 'Telemetria': 1, 'Navegação agora': 1, 'Autonomia e consumo': 1 };", ('emerg',)),
    ('a guarda de emergência esquece o óleo', "var EMERG = { sos: 1, oleo: 1, canal16: 1,", "var EMERG = { sos: 1, canal16: 1,", ('emerg', 'forma')),
    ('a guarda de emergência esquece o seafire', "epirb: 1, seafire: 1, salvatagem: 1, mmsi: 1 };", "epirb: 1, salvatagem: 1, mmsi: 1 };", ('emerg',)),
    ('a guarda de emergência vale para qualquer chave (EMERG[a.key] sem === 1)', "return !!a && typeof a === 'object' && (EMERG[a.key] === 1 || (a.key === 'faqEquip' && a.emerg === true)); }", "return !!a && typeof a === 'object'; }", ('emerg', 'uma')),   # (P3E, F10: texto novo do emerg(), mesma mutação)
]


# Mutantes da P3B (respostas sem rótulo): cada um tem de ser acusado pelos grupos indicados. Os do caminho null (modos) provam que o SEM DADOS / SEM LEITURA do modo real não se apagou.
MUTANTES_3B = [
    ('demo() ignora a simulação (o (DEMO) volta com simulacao true)', r"  function demo() { return D.demo && !sim() ? ' (DEMO)' : ''; }", r"  function demo() { return D.demo ? ' (DEMO)' : ''; }", ('rotulos',)),
    ('sim() lê D.simulacao no SOS (sem a guarda do EM_SOS)', r"  function sim() { return !EM_SOS && D.simulacao === true; }", r"  function sim() { return D.simulacao === true; }", ('sos',)),
    ('a saudação põe o selo da flag antiga com a simulação', r"(D.demo && !sim() ? '\n' + (D.selo || 'DEMO') + ': esta embarcação é de demonstração.' : '')", r"(D.demo ? '\n' + (D.selo || 'DEMO') + ': esta embarcação é de demonstração.' : '')", ('rotulos',)),
    # (P3D: a ficha não leva mais o selo nem o aviso, nem sem a simulação; o mutante põe o selo de volta no «## Agora»)
    ('a ficha põe o selo da flag antiga com a simulação', r"out.push('## Agora\n' + agoraBR() + ' · usuário: ' + quem());", r"out.push('## Agora\n' + agoraBR() + ' · usuário: ' + quem() + (D.demo ? '\n' + (D.selo || 'DEMO') + ': ' + (D.aviso || '') : ''));", ('rotulos',)),
    ('o convite diz «(demonstração)» com a simulação', r"(D.demo && !sim() ? ' (demonstração)' : '')", r"(D.demo ? ' (demonstração)' : '')", ('textos',)),
    ('a frase do §2.5 perde o «confira o boletim da Marinha antes de sair»', r"+ ' — confira o boletim da Marinha antes de sair.'; }", r"+ '.'; }", ('tempo',)),
    ('a frase do §2.5 perde a hora da última leitura salva', r"(h ? ' (última às ' + h + ')' : '')", r"''", ('tempo',)),
    ('a última leitura salva só vê a mais antiga', r"if (v && typeof v.em === 'number' && isFinite(v.em) && v.em > ms) ms = v.em;", r"if (v && typeof v.em === 'number' && isFinite(v.em) && v.em < ms) ms = v.em;", ('tempo',)),
    ('o clima sem conexão perde a situação de bordo', r"s ? semConexao() + '\n' + linhaBordo() :", r"s ? semConexao() :", ('tempo',)),
    ('a maré sem conexão perde a situação de bordo', r"(DHN).\n' + linhaBordo(), src: 'Fonte: nenhuma leitura de maré", r"(DHN).', src: 'Fonte: nenhuma leitura de maré", ('tempo',)),
    ('a maré diz «Corrente: SEM DADOS» na simulação', r"(s ? 'Corrente: o modelo traz só a altura da maré.' : 'Corrente: ' + SD + '.')", r"'Corrente: ' + SD + '.'", ('tempo',)),
    ('o seguro para sair diz «mar (ondas): SEM DADOS» na simulação', r"(s ? MAR_SIM : ' · mar (ondas): ' + SD", r"(false ? MAR_SIM : ' · mar (ondas): ' + SD", ('tempo',)),
    ('o dn vem do dado (t.dn), não do dia do instante', r"var n = x ? diaData(x.vence) - diaDe(msAgora()) : NaN; return isNaN(n)", r"var n = NaN; return isNaN(n)", ('prazos',)),
    ('a agenda ignora o Executado', r".filter(function (t) { return !ex[t.id]; }).sort(function (a, b) { return (dnDe(a)", r".filter(function (t) { return true; }).sort(function (a, b) { return (dnDe(a)", ('prazos',)),
    ('o prazo da tarefa executada não diz «executado»', r"if (ex) return ex;", r"", ('prazos',)),
    ('a tarefa do EPIRB e do Seafire vai com a data (seg() sempre falso)', r"function seg(t) { var e = t && equip(t.sistema); return !!(e && e.seguranca); }", r"function seg(t) { return false; }", ('prazos',)),
    ('os documentos escrevem «SEM DADOS: .» com a lista vazia', r"(sem.length ? '\n' + SD + ': ' + sem.map", r"(true ? '\n' + SD + ': ' + sem.map", ('textos', 'rotulos')),
    ('os motores voltam a «Volvo Penta» fixo', r"function motoresTxt() { var e = equip('motores'); return fabMod('motores') +", r"function motoresTxt() { var e = equip('motores'); return 'Motores Volvo Penta' +", ('textos',)),
    ('os motores voltam ao «ou 450 h» fixo', r"(o.horas ? ' ou ' + o.horas.limite + ' h' : '')", r"' ou 450 h'", ('textos',)),
    ('os motores voltam ao «sem alarme» fixo', r"alarmesCl(i, ' · alarmes: ') + '.\n' : '')", r"' · sem alarme.\n' : '')", ('textos',)),
    ('a pressão do óleo agora volta a «motores desligados»', r"(i ? 'Pressão do óleo agora (' + i.hora + '): '", r"(i ? 'Motores desligados. Pressão do óleo na última leitura (' + i.hora + '): '", ('textos',)),
    ('a faixa normal do óleo com os limites trocados', r"return 'de ' + nb(n.de) + ' a ' + nb(n.ate) + ' bar '", r"return 'de ' + nb(n.ate) + ' a ' + nb(n.de) + ' bar '", ('textos',)),
    ('a climatização perde o registro do diário da tarefa', r"(d ? ' Diário de ' + d.d + ': ' + d.t : '')", r"''", ('textos',)),
    ('os eletrônicos citam o guia do radar no lugar do guia do piloto', r"(' + guia('g_piloto') + ' §1–3)", r"(' + guia('g_radar') + ' §1–3)", ('textos',)),
    ('o destino perde a hora de chegada (ETA)', r"', chegada prevista às ' + t.eta + ' — '", r"', chegada prevista' + ' — '", ('textos',)),
    ('o juízo da ida e volta invertido', r"(iv <= util ? 'cabe no diesel a bordo' : 'pede abastecer antes')", r"(iv > util ? 'cabe no diesel a bordo' : 'pede abastecer antes')", ('textos',)),
    ('o diesel do destino em dobro', r"l = h != null && lphOk ? Math.round(h * lph) : null", r"l = h != null && lphOk ? Math.round(h * lph * 2) : null", ('textos',)),
    ('a âncora esquece o contador de corrente', r"o contador de corrente mostra os metros lançados no controle do guincho (", r"o controle do guincho (", ('textos',)),
    ('a corrente para fundear em 2 vezes a profundidade', r"Math.round(3 * prof)", r"Math.round(2 * prof)", ('textos',)),
    ('o porão perde a faixa normal do guia', r"(ate != null ? ' (normal até ' + nb(ate, 0) + ' cm)' : '')", r"''", ('textos',)),
    ('o gerador perde a carga em kW', r"(typeof G.kw === 'number' && G.estado !== 'desligado' ? ' · ' + nb(G.kw) + ' kW' : '')", r"''", ('rotulos', 'estados')),
    ('os contatos perdem a situação de bordo', r"(ctx && ctx.semBordo ? '' : '\n' + linhaBordo())", r"''", ('textos',)),
    ('o fallback volta a «Não encontrei esse dado»', r"text: 'Isso não está nas fontes de bordo que o app consulta", r"text: 'Não encontrei esse dado nas fontes de bordo que o app consulta", ('textos',)),
    ('o anexo perde a situação de bordo', r"(grava ? 'anexei ao diário como anomalia A CONFIRMAR.' : nao) + '\n' + linhaBordo() +", r"(grava ? 'anexei ao diário como anomalia A CONFIRMAR.' : nao) + '\n' +", ('textos',)),
    ('a frase de sobreDados afirma que o barco é real', r"Esta é a embarcação de apresentação da plataforma Capitão IA", r"Esta é uma embarcação real da plataforma Capitão IA", ('textos',)),
    ('o «Sobre o app» volta a «nada inventado»', r"'Sobre os dados: ' + SOBRE_DADOS", r"'Regra da casa: nada inventado. Sobre os dados: ' + SOBRE_DADOS", ('textos',)),
    ('a resposta de dado de bordo perde a hora do instante na fonte', r"a.src += ' · consultado às ' + vivo().hora;", r"a.src += '';", ('rotulos',)),
    ('a hora do instante entra na fonte da emergência', r"if (!SEM_HORA_NA_FONTE[key] && sim() && vivo()", r"if (sim() && vivo()", ('forma',)),
    ('o diagnóstico volta a «app SEM DADOS»', r"'não carregado nesta tela'", r"SD", ('rotulos',)),
    ('a telemetria escreve SEM LEITURA do porão e da âncora sempre', r"(po || 'SEM LEITURA')", r"'SEM LEITURA'", ('rotulos',)),
    ('a telemetria sem leitura do porão perde o SEM LEITURA (modo real)', r"(po || 'SEM LEITURA')", r"(po || '')", ('modos',)),
    ('o resumo da reserva volta a dizer «snapshot»', r"var fim = ' — leitura' + demo_() + ' de ' + SNAP.quando + '.', r = '';", r"var fim = ' — snapshot' + demo_() + ' ' + SNAP.quando + '.', r = '';", ('falha',)),
    ('o seguro para sair perde o alarme ativo do quadro', r"if (al) ress.push('Alarme ativo a bordo agora: ' + al + '.');", r"", ('textos',)),
    ('o seguro para sair não diz «Não» com o alarme crítico', r"(crit ? 'Não saia agora:", r"(false ? 'Não saia agora:", ('textos',)),
    ('a maré sem conexão e sem leitura perde o SEM DADOS do modo real', r"text: 'SEM DADOS de maré agora", r"text: 'Maré: sem leitura agora", ('modos',)),
    ('o porão sem leitura perde o SEM LEITURA do modo real', r"'Sem sensor de porão no barramento NMEA — SEM LEITURA.'", r"'Sem sensor de porão no barramento NMEA.'", ('modos',)),
    ('os destinos sem rota perdem o SEM DADOS do modo real', r"SD + ' de rotas: nenhum roteiro", r"'Rotas: nenhum roteiro", ('modos',)),
    ('o dessalinizador que não consta perde o SEM DADOS do modo real', r"SD + ' — dessalinizador não consta na lista de equipamentos.", r"'Dessalinizador não consta na lista de equipamentos.", ('modos',)),
    ('o clima sem a previsão perde o SEM DADOS do modo real', "'Previsão do dia: ' + SD + ' (sem leitura de hoje neste aparelho).';\n      var bordo", "'Previsão do dia: indisponível (sem leitura de hoje neste aparelho).';\n      var bordo", ('modos',)),
    ('a âncora sem leitura perde o SEM LEITURA do modo real', r"'Sem sensor de âncora na rede NMEA — SEM LEITURA do ferro.'", r"'Sem sensor de âncora na rede NMEA.'", ('modos',)),
    ('o cérebro não exporta B.CHAVES', r"CHAVES: CHAVES, SOBRE_DADOS: SOBRE_DADOS,", r"SOBRE_DADOS: SOBRE_DADOS,", ('rotulos',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3B

# Mutantes da revisão da P3B: o consumo e a autonomia do instante, o item 7 do checklist, a primeira ressalva do seguro, o documento vencido, os dois prefixos da situação de bordo, a âncora do
# modo real, o «Sobre o app» e a saudação dos dois modos, a sigla do AIS, a previsão parcial (sem rajada, sem vento) nos dois modos e as leituras do SOS (D.replay, D.rota)
MUTANTES_3B_REV = [
    ('o consumo agora vira um valor fixo', r"(i.txt.consumo || SD)", r"'0 L/h'", ('rotulos',)),
    ('a autonomia da resposta fica a do snapshot (AUT0)', r"'Autonomia ≈ ' + nb(AUT.horas) + ' h · ≈ ' + AUT.mn + ' mn a '", r"'Autonomia ≈ ' + nb(AUT0.horas) + ' h · ≈ ' + AUT0.mn + ' mn a '", ('rotulos',)),
    # (P3E, F09: o «item 7» fixo do checklist saiu com a troca pelo D.checklists; o mutante equivalente tira a fonte e o código do FAQ de cada item)
    ('o checklist de saída perde a fonte do item (o 13 da salvatagem e o 1 da previsão)', "+ por + ' (' + x.fonte + (x.faq ? ' · FAQ ' + x.faq : '') + ')';", "+ por;", ('textos',)),
    ('o seguro para sair sempre diz «a primeira é de segurança»', r"(primeiraSeg ? ' — a primeira é de segurança.' : '.')", r"(true ? ' — a primeira é de segurança.' : '.')", ('prazos',)),
    ('o documento vencido perde o «VENCIDO há»', r"return n < 0 ? 'VENCIDO há ' + (-n)", r"return n < 0 ? 'vencido ' + (-n)", ('prazos',)),
    ('a situação de bordo sempre diz «Última situação de bordo»', r"(vivo() ? 'Situação de bordo agora: ' : 'Última situação de bordo: ')", r"'Última situação de bordo: '", ('textos',)),
    ('a situação de bordo sempre diz «Situação de bordo agora»', r"(vivo() ? 'Situação de bordo agora: ' : 'Última situação de bordo: ')", r"'Situação de bordo agora: '", ('modos',)),
    ('a âncora do modo real perde os metros de corrente do contador', r"', com ' + mil(AN.cabo_m) + ' m de corrente no contador do guincho'", r"''", ('modos',)),
    ('a telemetria do modo real perde os metros de corrente da âncora', r"', ' + mil(AN.cabo_m) + ' m de corrente'", r"''", ('modos',)),
    ('o «Sobre o app» do modo real traz a frase de sobreDados', r"sm ? 'Sobre os dados: ' + SOBRE_DADOS :", r"true ? 'Sobre os dados: ' + SOBRE_DADOS :", ('modos',)),
    ('o «Sobre o app» do modo real fala da telemetria ao vivo do coletor', r"'Responde sobre: ' + (sm ? 'telemetria ao vivo", r"'Responde sobre: ' + (true ? 'telemetria ao vivo", ('modos',)),
    ('o «Sobre o app» do modo real responde «com o número, a hora e a fonte»', r"(sm ? 'o número, a hora e a fonte.' : 'a fonte.')", r"'o número, a hora e a fonte.'", ('modos',)),
    ('o «Sobre o app» da simulação volta à regra «Nada inventado»', r"sm ? 'Sobre os dados: ' + SOBRE_DADOS : 'Regra da casa", r"false ? 'Sobre os dados: ' + SOBRE_DADOS : 'Regra da casa", ('textos',)),
    ('a saudação do modo real fala da telemetria ao vivo', r"'\nRespondo sobre telemetria' + (sim() ? ' ao vivo' : '')", r"'\nRespondo sobre telemetria' + ' ao vivo'", ('modos',)),
    ('a saudação da simulação perde a telemetria ao vivo', r"'\nRespondo sobre telemetria' + (sim() ? ' ao vivo' : '')", r"'\nRespondo sobre telemetria' + ''", ('textos',)),
    ('a sigla do AIS perde a maiúscula (min1 baixa sempre)', r"return /^[A-ZÀ-Ý]{2}/.test(s) ? s : s.charAt(0).toLowerCase() + s.slice(1); }", r"return s.charAt(0).toLowerCase() + s.slice(1); }", ('textos',)),
    ('a rajada ausente volta a «rajadas SEM DADOS» na simulação', r"') : s ? '' : ', rajadas ' + SD) : s ? 'sem previsão de vento nesta leitura' : 'vento ' + SD;", r"') : ', rajadas ' + SD) : s ? 'sem previsão de vento nesta leitura' : 'vento ' + SD;", ('tempo',)),
    ('o vento ausente volta a «vento SEM DADOS» na simulação', r"') : s ? '' : ', rajadas ' + SD) : s ? 'sem previsão de vento nesta leitura' : 'vento ' + SD;", r"') : s ? '' : ', rajadas ' + SD) : 'vento ' + SD;", ('tempo',)),
    ('o modo real perde o «rajadas SEM DADOS»', r"') : s ? '' : ', rajadas ' + SD) : s ? 'sem previsão de vento nesta leitura' : 'vento ' + SD;", r"') : '') : s ? 'sem previsão de vento nesta leitura' : 'vento ' + SD;", ('tempo',)),
    ('o modo real perde o «vento SEM DADOS»', r"') : s ? '' : ', rajadas ' + SD) : s ? 'sem previsão de vento nesta leitura' : 'vento ' + SD;", r"') : s ? '' : ', rajadas ' + SD) : 'sem previsão de vento nesta leitura';", ('tempo',)),
    ('a pressão do óleo no SOS lê o D.replay (limitesDe sem a guarda)', r"function limitesDe(campo) { if (EM_SOS) return null; var L", r"function limitesDe(campo) { var L", ('sos',)),
    ('os destinos no SOS leem a D.rota', r"R = EM_SOS ? null : D.rota,", r"R = D.rota,", ('sos',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3B_REV

# Mutantes da 2ª revisão da P3B: o fuso e o instante dos prazos (valor absoluto), o Executado dos motores, dos horímetros e do gerador
MUTANTES_3B_REV2 = [
    ('o dia do prazo é o dia UTC (sem o fuso do barco)', r"return Math.floor((ms + o * 60000) / 86400000); }", r"return Math.floor(ms / 86400000); }", ('prazos',)),
    ('o dn tem um dia a mais', r"var n = x ? diaData(x.vence) - diaDe(msAgora()) : NaN; return isNaN(n)", r"var n = x ? diaData(x.vence) - diaDe(msAgora()) + 1 : NaN; return isNaN(n)", ('prazos',)),
    ('o prazo lê o Date.now() e não o instante do cérebro', r"function msAgora() { var i = CONG.inst; return i && typeof i.ms === 'number' ? i.ms : Date.now(); }", r"function msAgora() { return Date.now(); }", ('prazos',)),
    ('os horímetros ignoram a troca de óleo executada', r"(oEx ? 'Troca de óleo dos motores: ' + oEx + '.' : 'Próxima troca de óleo dos motores: '", r"(false ? 'Troca de óleo dos motores: ' + oEx + '.' : 'Próxima troca de óleo dos motores: '", ('prazos',)),
    ('os horímetros ignoram a revisão do gerador executada', r"(rvEx ? rvEx + '.' : rv.vence", r"(false ? rvEx + '.' : rv.vence", ('prazos',)),
    ('os motores ignoram a troca de óleo executada', r"' · troca de óleo ' + (execTxt(o) || prazoTxt(o) + (o.horas ? ' ou '", r"' · troca de óleo ' + (prazoTxt(o) + (o.horas ? ' ou '", ('prazos',)),
    ('o gerador ignora a revisão executada', r"(execTxt(rv) ? execTxt(rv) + '.' : rv.vence", r"(false ? execTxt(rv) + '.' : rv.vence", ('prazos',)),
    ('o Executado é sempre masculino («troca executado»)', r"'executada' : 'executado') + ' em '", r"'executado' : 'executado') + ' em '", ('prazos',)),
    ('a telemetria perde as linhas «Alarmes» e «Tendência»', r"(i ? alarmesCl(i, '\n• Alarmes: ') + (t.tend ? '\n• Tendência — ' + t.tend : '') : '')", r"''", ('textos',)),
    ('a telemetria perde só a linha «Tendência»', r"(t.tend ? '\n• Tendência — ' + t.tend : '')", r"''", ('textos',)),
    ('o «Sobre o app» lista o fabricante do EPIRB e do Seafire (sem o filtro de segurança)', r"return !e.seguranca && e.id !== 'eletrico'; })", r"return e.id !== 'eletrico'; })", ('textos',)),
    ('o seguro para sair põe o alarme ativo depois das ressalvas de manutenção',
     "      if (al) ress.push('Alarme ativo a bordo agora: ' + al + '.');   // logo depois da de segurança: a fala lê as primeiras ressalvas e o alarme ativo não pode ficar de fora\n      at.filter(function (x) { return x.id !== 'porao-teste'; }).forEach(function (x) { ress.push(x.t + ' — ' + prazoTxt(x) + '.'); });\n",
     "      at.filter(function (x) { return x.id !== 'porao-teste'; }).forEach(function (x) { ress.push(x.t + ' — ' + prazoTxt(x) + '.'); });\n      if (al) ress.push('Alarme ativo a bordo agora: ' + al + '.');\n", ('textos',)),
    ('a fala das ressalvas corta sem dizer «e mais K»', r"while (ressalvas && extra.length > 1 && junta().length > lim) { extra.pop(); resto++; }", r"while (ressalvas && extra.length > 1 && junta().length > lim) { extra.pop(); }", ('textos',)),
    ('os destinos sem o cruzeiro voltam a escrever «a undefined nós»', r"var vel = nosTxt ? ', a ' + nosTxt + (lphTxt ? ' (' + lphTxt + ')' : '') : lphTxt ? ', ' + lphTxt : '';", r"var vel = ', a ' + nos + ' nós (' + lph + ' L/h)';", ('modos',)),
    ('os destinos do modo real perdem o SEM DADOS do tempo e do diesel', r"(h != null ? ' · ≈ ' + tempo(h) : s ? '' : ' · tempo ' + SD) + (l != null ? ' · ≈ ' + l + ' L' : s ? '' : ' · diesel ' + SD)", r"(h != null ? ' · ≈ ' + tempo(h) : '') + (l != null ? ' · ≈ ' + l + ' L' : '')", ('modos',)),
    ('os destinos da simulação escrevem SEM DADOS no tempo e no diesel', r"(h != null ? ' · ≈ ' + tempo(h) : s ? '' : ' · tempo ' + SD) + (l != null ? ' · ≈ ' + l + ' L' : s ? '' : ' · diesel ' + SD)", r"(h != null ? ' · ≈ ' + tempo(h) : ' · tempo ' + SD) + (l != null ? ' · ≈ ' + l + ' L' : ' · diesel ' + SD)", ('modos',)),
    ('o alcance sem o cruzeiro escreve «a  nós»', r"' h' + (nosTxt ? ' a ' + nosTxt : '') + ', reserva de '", r"' h a ' + nos + ' nós, reserva de '", ('modos',)),
    ('o atalho do diário grava (DEMO) na fonte da linha permanente', r"src: junto ? 'chat · voz/texto · telemetria' + demo() : 'atalho · telemetria' + demo() });", r"src: junto ? 'chat · voz/texto · telemetria' + ' (DEMO)' : 'atalho · telemetria' + ' (DEMO)' });", ('rotulos',)),
    ('o atalho do diário perde o (DEMO) do modo real', r"src: junto ? 'chat · voz/texto · telemetria' + demo() : 'atalho · telemetria' + demo() });", r"src: junto ? 'chat · voz/texto · telemetria' : 'atalho · telemetria' });", ('rotulos',)),
    ('a fala das ressalvas diz «1 ressalvas» (plural fixo)', r"(resto === 1 ? ' ressalva' : ' ressalvas')", r"' ressalvas'", ('textos',)),
    ('a fala das ressalvas não corta no limite (lê todas)', r"while (ressalvas && extra.length > 1 && junta().length > lim) { extra.pop(); resto++; }", r"", ('textos',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3B_REV2

# Mutantes da 3ª revisão da P3B: a hora da maré (real, não a do replay), o coletor sem o campo `alarmes`, a fala do gerador, a corrente da âncora e os estados fixos que os mutantes anteriores
# não alcançavam (o replay só navega: horímetros, radar, motores, climatização, Seakeeper e dessalinizador só mudam num coletor; destinos com pouco diesel; tudo Executado; tarefa de segurança)
MUTANTES_3B_REV3 = [
    ('a maré volta a levar o carimbo «consultado às» do instante do replay', r"diario: 1, mare: 1 };", r"diario: 1 };", ('tempo',)),
    ('a fonte da maré salva perde a hora da leitura', r"(s && mareLidaHM() ? ' · lida às ' + mareLidaHM() : '')", r"''", ('tempo',)),
    ('a hora da leitura da maré vale também com a simulação desligada', r"(s && mareLidaHM() ? ' · lida às '", r"(mareLidaHM() ? ' · lida às '", ('tempo',)),
    ('a hora da leitura da maré é a do instante do replay', r"isFinite(v.em) ? fmtHM(v.em) : ''; }", r"isFinite(v.em) ? fmtHM(msAgora()) : ''; }", ('tempo',)),
    ('o coletor sem o campo `alarmes` volta a dizer «nenhum alarme ativo»', r"if (!Array.isArray(q)) return null;", r"if (!Array.isArray(q)) return 'nenhum alarme ativo';", ('alarmes',)),
    ('sem o campo `alarmes` a cláusula some também sem a simulação (sem SEM LEITURA)', r"return a ? rot + a : sim() ? '' : rot + SL; }", r"return a ? rot + a : ''; }", ('alarmes',)),
    ('sem o campo `alarmes` a cláusula escreve SEM LEITURA também com a simulação', r"return a ? rot + a : sim() ? '' : rot + SL; }", r"return a ? rot + a : rot + SL; }", ('alarmes',)),
    ('a telemetria escreve o texto cru dos alarmes (undefined sem o campo)', r"alarmesCl(i, '\n• Alarmes: ')", r"'\n• Alarmes: ' + t.alarmes", ('alarmes',)),
    ('o seguro para sair escreve o texto cru dos alarmes', r"(i ? alarmesCl(i, ' · alarmes: ') : '') + '.',", r"(i ? ' · alarmes: ' + i.txt.alarmes : '') + '.',", ('alarmes',)),
    ('os motores escrevem o texto cru dos alarmes', r"(i.txt.rpm || '—') + alarmesCl(i, ' · alarmes: ') + '.\n' : '')", r"(i.txt.rpm || '—') + ' · alarmes: ' + i.txt.alarmes + '.\n' : '')", ('alarmes',)),
    ('o gerador volta ao estado entre parênteses (a fala perde o estado e a hora)', r"fabMod('gerador') + (G.estado ? ' ' + G.estado + ' ' + quand :", r"fabMod('gerador') + (G.estado ? ' (' + G.estado + ' ' + quand + ')' :", ('estados',)),
    ('o gerador diz sempre «ligado»', r"(G.estado ? ' ' + G.estado + ' ' + quand :", r"(G.estado ? ' ligado ' + quand :", ('estados',)),
    ('o gerador desligado mostra os kW', r"typeof G.kw === 'number' && G.estado !== 'desligado' ?", r"typeof G.kw === 'number' ?", ('estados',)),
    ('o gerador não diz a hora do quadro', r"quand = vivo() ? 'às ' + SNAP.quando : 'na ' + quando()", r"quand = vivo() ? 'agora' : 'na ' + quando()", ('estados',)),
    ('a corrente da âncora volta a cair na maré (sem a precedência da âncora)', r"if (CORRENTE_ANCORA.test(q) && !has(q, [' mare', 'correnteza', 'corrente de mare'])) return 'ancora';", r"", ('rotas',)),
    ('a corrente de maré vai para a âncora (sem a guarda da maré)', r"CORRENTE_ANCORA.test(q) && !has(q, [' mare', 'correnteza', 'corrente de mare'])) return 'ancora';", r"CORRENTE_ANCORA.test(q)) return 'ancora';", ('rotas',)),
    ('«quanto de corrente» não é da âncora', r"\bquant[oa]s? (?:de )?corrente\b|", r"", ('rotas',)),
    ('«metros de corrente» não é da âncora', r"\b(?:metros?|m) de corrente\b|", r"", ('rotas',)),
    ('os horímetros dizem «(motores desligados)» fixo', r"'às ' + SNAP.quando + ' (motores ' + (M.estado || SD) + ')'", r"'às ' + SNAP.quando + ' (motores desligados)'", ('estados',)),
    ('os motores dizem «ligados» fixo', r"'Motores ' + (M.estado || SD) + ' às ' + i.hora + ': '", r"'Motores ligados às ' + i.hora + ': '", ('estados',)),
    ('os destinos ignoram a margem de manobra no juízo da ida e volta', r"(typeof D.reserva === 'number' ? D.reserva : 0.1)) - margem : null;", r"(typeof D.reserva === 'number' ? D.reserva : 0.1)) : null;", ('estados',)),
    ('os eletrônicos dizem o radar sempre ligado', r"': radar ' + (q.radar_ativo ? 'ligado' : 'desligado')", r"': radar ligado'", ('estados',)),
    ('os eletrônicos dizem «alvos» no plural fixo', r"(q.ais_alvos === 1 ? ' alvo' : ' alvos')", r"' alvos'", ('estados',)),
    ('a climatização diz «ligada» fixo', r"(i.q.climatizacao_ativa ? ' ligada' : ' desligada')", r"' ligada'", ('estados',)),
    ('o dessalinizador diz «desligado» fixo', r"(i.q.dessalinizador_ativo ? ' ligado' : ' desligado')", r"' desligado'", ('estados',)),
    ('o Seakeeper diz «LIGADO» fixo', r": 'desligado') + ' · ao vivo ' + i.hora + '.\n'", r": 'LIGADO') + ' · ao vivo ' + i.hora + '.\n'", ('estados',)),
    ('a manutenção sem atrasadas perde a hora do instante', r"'Nenhuma tarefa atrasada' + (i ? ' às ' + i.hora : '') + '.')", r"'Nenhuma tarefa atrasada.')", ('prazos',)),
    ('o seguro para sair diz «1 ressalvas» (plural fixo)', r"'Sim, com ' + ress.length + (ress.length === 1 ? ' ressalva' : ' ressalvas')", r"'Sim, com ' + ress.length + ' ressalvas'", ('prazos',)),
    ('o prazo da tarefa de segurança volta ao «D-n · dd/mm»', r"return seg(t) ? NOTA_ETIQUETA : 'D-' + n + ' · ' + String(t.vence).slice(0, 5);", r"return 'D-' + n + ' · ' + String(t.vence).slice(0, 5);", ('prazos',)),
    ('o áudio perde as zonas do cadastro', r"(e && e.nominal && e.nominal.zonas ? ' · ' + e.nominal.zonas + ' zonas' : '')", r"''", ('textos',)),
    ('o estabilizador perde a tarefa do anodo da agenda', r"(an ? '\n' + an.t + ': ' + prazoTxt(an) + '.' : '')", r"''", ('textos',)),
    ('a fonte da autonomia cita o período da leitura antiga e não a fonte do consumo', r"(vivo() ? CON.fonte : CON.periodo) + ') · '", r"CON.periodo + ') · '", ('textos',)),
    ('os documentos listam o certificado do EPIRB com a data (sem o filtro de segurança)', r"var segd = function (d) { return (D.equipamentos || []).some(function (e) { return e.seguranca && e.validade === d.id; }); };", r"var segd = function (d) { return false; };", ('textos',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3B_REV3


# Mutantes da P3C (as rotas novas): a ordem das rotas, os gatilhos, o texto de cada resposta e as guardas do SOS e do modo real. Cada um tem de ser acusado pelo grupo indicado.
MUTANTES_3C = [
    # —— a ordem e os gatilhos (grupo p3c: a tabela ROTAS_P3C) ——
    ('a pergunta do MMSI volta ao canal16', r"if (has(q, ['mmsi'])) return mmsiRota(q);", r"if (has(q, ['mmsi'])) return 'canal16';", ('p3c',)),
    ('o AIS volta ao canal16 (sem a rota própria)', r"if (has(q, [' ais ']) && leitura(q, AIS_OK)) return 'ais';", r"if (has(q, [' ais ']) && leitura(q, AIS_OK)) return 'canal16';", ('p3c',)),
    ('a sobreDados sai da route()', r"    if (sobreDados(q)) return 'sobreDados';", r"", ('p3c',)),
    ('o foraBarco antes das rotas de bordo («quanto custa o diesel em reais?» deixa de ser o diesel)', r"if (sobreDados(q)) return 'sobreDados';", r"if (sobreDados(q)) return 'sobreDados'; if (has(q, FORA_BARCO)) return 'foraBarco';", ('p3c',)),
    ('o foraBarco sem «dolar»', r"var FORA_BARCO = [' dolar ', ' dolares ', ", r"var FORA_BARCO = [", ('p3c',)),
    ('o foraBarco sem «preco»', r"' bitcoin ', ' preco ', ' precos ', 'quanto custa'", r"' bitcoin ', 'quanto custa'", ('p3c',)),
    # (P3E, F10: o `pedeIA` ganhou o 'faqEquip' na mesma linha; a mutação é a mesma, ancorada no texto novo)
    ('o foraBarco chama a IA', r"if (k !== 'fallback' && k !== 'base' && k !== 'saudacao' && k !== 'faqEquip') return false;", r"if (k !== 'fallback' && k !== 'base' && k !== 'saudacao' && k !== 'faqEquip' && k !== 'foraBarco') return false;", ('p3c',)),
    ('a sobreDados sem a forma curta («é de verdade?»)', r"if (AUT_CURTA.test(q) || AUT_QUE_E.test(q) || AUT_NAVEGANDO.test(q)) return true;", r"if (AUT_QUE_E.test(q) || AUT_NAVEGANDO.test(q)) return true;", ('p3c',)),
    ('a sobreDados sem «o barco existe»', r"var AUT_EXISTE = [' o barco existe ', ", r"var AUT_EXISTE = [", ('p3c',)),
    ('o horímetro pega a revisão do gerador e o filtro de água salgada (sem a lista branca)', r"has(q, ['troca', 'revisao', 'oleo', 'horas de motor']) && leitura(q, FALTA_TROCA_OK)) return 'horimetros';", r"has(q, ['troca', 'revisao', 'oleo', 'horas de motor'])) return 'horimetros';", ('p3c',)),
    ('«quanto falta» pega a troca de óleo (a chegada sem o «junto de»)', r"!(has(q, FALTA_PALAVRAS) && (has(q, FALTA_JUNTO) || has(q, lugaresRota())))) return false;", r"!has(q, FALTA_PALAVRAS)) return false;", ('p3c',)),
    ('a chegada pega o alcance em milhas (a lista branca aceita «alcance», «autonomia», «diesel»…)', r"var ETA_OK = NEUTRAS_BASE + 'quando ja muito estamos eta chegada", r"var ETA_OK = NEUTRAS_BASE + 'quando ja muito estamos alcance autonomia diesel barco limite acabar eta chegada", ('p3c',)),
    ('a profundidade pega o alarme e a mínima (sem a lista de palavras neutras)', r"function profundidadePergunta(q) { return (has(q, PROFUNDIDADE_PALAVRAS) && soNeutras(q, PROFUNDIDADE_OK)) || POUCO_FUNDO.test(q); }", r"function profundidadePergunta(q) { return has(q, PROFUNDIDADE_PALAVRAS) || POUCO_FUNDO.test(q); }", ('p3c',)),
    ('a posição sem «onde estamos»', r"var POSICAO_NOVAS = ['onde estamos', ", r"var POSICAO_NOVAS = [", ('p3c',)),
    ('a posição sem rumo, COG e «quantos nós»', r"' rumo ', ' cog ', ' sog ', ' quantos nos ', 'milhas por hora'];", r"'milhas por hora'];", ('p3c',)),
    ('o alarme sem «tem algum alerta»', r"    new RegExp(' (?:tem|ha|existe|existem|temos) (?:algum |alguns )?(?:alarmes?|alertas?)' + FIM_ALARME + ' $'),", r"", ('p3c',)),
    ('a temperatura do motor pega o alarme (sem a lista de palavras neutras)', r"function arrefecimentoPergunta(q) { return ARREF_REGEX.test(q) && soNeutras(q, arrefOk()); }", r"function arrefecimentoPergunta(q) { return ARREF_REGEX.test(q); }", ('p3c',)),
    ('as ondas pegam o relato (sem a lista de palavras neutras)', r"function ondasPergunta(q) { return has(q, ONDAS_PALAVRAS) && soNeutras(q, ONDAS_OK); }", r"function ondasPergunta(q) { return has(q, ONDAS_PALAVRAS); }", ('p3c',)),
    ('a temperatura da água pega a «subindo» do relato (sem a lista de palavras neutras)', r"function aguaPergunta(q) { return AGUA_REGEX.test(q) && soNeutras(q, AGUA_OK); }", r"function aguaPergunta(q) { return AGUA_REGEX.test(q); }", ('p3c',)),
    ('a navegação pega «como estamos de diesel» (a forma curta sem o fim ancorado)', r"(?: agora| por ai| a bordo| ai)? $/;", r"(?: agora| por ai| a bordo| ai)?/;", ('p3c',)),
    ('as pessoas pegam o relato com número (a leitura calma ignora os dígitos)', r"function leitura(q, ok) { return !DEFINICAO.test(q) && soNeutras(q, ok); }", r"function leitura(q, ok) { return !DEFINICAO.test(q) && soNeutras(q.replace(/ \d+ /g, ' '), ok); }", ('p3c',)),
    ('a embarcação sem «calado»', r"var EMB_PALAVRAS = [' calado', ", r"var EMB_PALAVRAS = [", ('p3c',)),
    ('a embarcação pega o deslocamento do Seakeeper (a lista neutra do barco aceita «Seakeeper»)', r"'barco barcos lancha embarcacao real sao maxima minima total '", r"'barco barcos lancha embarcacao real sao maxima minima total seakeeper estabilizador '", ('p3c',)),
    ('o AIS de status vai ao guia (sem a lista de status)', r"var AIS_STATUS = /\b(?:quantos?|", r"var AIS_STATUS = /\b(?:xquantos?|", ('p3c',)),
    ('o AIS sai da lista das respostas prontas de equipamento (a pergunta de guia fica na resposta)', r"porao: 1, ancora: 1, ais: 1, manual: 1", r"porao: 1, ancora: 1, manual: 1", ('p3c',)),
    # —— o texto de cada resposta (grupo p3c: o texto esperado do instante) ——
    ('a posição abre com as coordenadas', r"        l1 = cap1(q.estado || 'Navegando') + (t.sog ? ' a ' + t.sog : '') + (!parado && t.rumo ? ', rumo ' + t.rumo : t.proa", r"        l1 = SNAP.pos + ' ' + cap1(q.estado || 'Navegando') + (t.sog ? ' a ' + t.sog : '') + (!parado && t.rumo ? ', rumo ' + t.rumo : t.proa", ('p3c',)),
    ('a posição sem a posição relativa', r"parado = typeof q.sog_nos === 'number' && q.sog_nos < 0.5; onde = t.relativa || t.local;", r"parado = typeof q.sog_nos === 'number' && q.sog_nos < 0.5; onde = t.local;", ('p3c',)),
    ('a posição sem as coordenadas na 2ª linha', r"coord = typeof q.lat === 'number' && typeof q.lon === 'number' ? posicaoTxt() : '';", r"coord = '';", ('p3c',)),
    ('a posição parada diz o rumo sobre o fundo', r"(!parado && t.rumo ? ', rumo ' + t.rumo : t.proa ? ', proa ' + t.proa : '')", r"(t.rumo ? ', rumo ' + t.rumo : '')", ('p3c_dados',)),
    ('a profundidade perde o calado do cadastro', r"'\nCalado do barco: ' + (typeof cal === 'number' ? nb(cal, 2) + ' m (cadastro)' : SD) + '.'", r"''", ('p3c',)),
    ('a profundidade lê a velocidade', r"prof = i ? i.txt.prof :", r"prof = i ? i.txt.sog :", ('p3c',)),
    ('a chegada troca a distância do destino pela do ponto', r"(campoTxt(i, 'destino_mn') ? ', a ' + campoTxt(i, 'destino_mn') + ' mn' : '')", r"(campoTxt(i, 'wp_mn') ? ', a ' + campoTxt(i, 'wp_mn') + ' mn' : '')", ('p3c',)),
    ('o waypoint não abre com o ponto', r": (wp && ponto ? ponto + ' — '", r": (false && ponto ? ponto + ' — '", ('p3c',)),
    ('o percorrido some da chegada', r"perc = campoTxt(i, 'distancia_mn') ? 'Percorrido desde as '", r"perc = false ? 'Percorrido desde as '", ('p3c',)),
    ('o alarme perde o que verificar primeiro', r"partes.push((a.titulo || c.titulo || 'Alarme') + (a.hora ? ' (desde ' + a.hora + ')' : '') + ' — o que verificar primeiro:\n'", r"partes.push((a.titulo || c.titulo || 'Alarme') + (a.hora ? ' (desde ' + a.hora + ')' : '') + ' — sem passos:\n'", ('p3c',)),
    ('o alarme diz «1 alarmes» (plural fixo)', r"(n === 1 ? 'Há 1 alarme ativo' : 'Há ' + n + ' alarmes ativos')", r"('Há ' + n + ' alarmes ativos')", ('p3c',)),
    ('o alarme sem o botão ver o alerta', r"actions: (link ? [{ l: 'Ver o alerta', href: link }] : []).concat(", r"actions: ([]).concat(", ('p3c',)),
    ('a temperatura do motor não marca a que passou da faixa', r"if (niv && niv.nivel && niv.nivel !== 'normal') fora.push(", r"if (false) fora.push(", ('p3c',)),
    ('a temperatura do motor sem a faixa do guia', r"(fx ? '\n' + fx : '') + pass,", r"'' + pass,", ('p3c',)),
    ('a temperatura do motor troca BB e BE na tendência', r"sinal(i.tend.motor_bb_arref_c, 1) + ' · BE ' + sinal(i.tend.motor_be_arref_c, 1)", r"sinal(i.tend.motor_be_arref_c, 1) + ' · BE ' + sinal(i.tend.motor_bb_arref_c, 1)", ('p3c',)),
    ('a temperatura do motor sem o que verificar primeiro', r"alr = lista.filter(function (a) { return /arref/.test(a.campo || a.id || ''); });", r"alr = [];", ('p3c',)),
    ('as ondas viram previsão', r"'Ondas de ' + o + ' a bordo agora — '", r"'Ondas de ' + o + ' previstas — '", ('p3c',)),
    ('a temperatura da água lê o ar', r"ag = i ? i.txt.agua :", r"ag = i ? i.txt.ar :", ('p3c',)),
    ('a navegação sem a tendência', r"      if (t.tend) ls.push('• Tendência — ' + t.tend);", r"", ('p3c',)),
    ('a navegação sem o rumo', r"(!parado && t.rumo ? ', rumo ' + t.rumo : '') + (onde ? ', ' + onde : '') + (t.eta ?", r"(onde ? ', ' + onde : '') + (t.eta ?", ('p3c',)),
    ('as pessoas ignoram o singular', r"n + (n === 1 ? ' pessoa a bordo' : ' pessoas a bordo')", r"n + ' pessoas a bordo'", ('p3c_dados',)),
    ('o calado da embarcação com uma casa', r"'O calado do barco é ' + nm('calado', 2)", r"'O calado do barco é ' + nm('calado', 1)", ('p3c',)),
    ('o calado responde a boca', r"l1 = 'O calado do barco é ' + nm('calado', 2) + h + '.';", r"l1 = 'O calado do barco é ' + nm('boca', 2) + h + '.';", ('p3c',)),
    ('o AIS diz «1 alvos» (plural fixo)', r"' com ' + a + (a === 1 ? ' alvo' : ' alvos') + ' às ' + i.hora", r"' com ' + a + ' alvos às ' + i.hora", ('p3c_dados',)),
    ('o MMSI põe o do cadastro na 1ª linha, com instrução de programar', r"var MMSI_USO = 'No MAYDAY e no DSC, use o MMSI da etiqueta do rádio (Licença de Estação).';", r"var MMSI_USO = 'No MAYDAY e no DSC, programe o MMSI ' + (D.embarcacao || {}).mmsi + ' no rádio (Licença de Estação).';", ('p3c',)),
    ('o MMSI sem a 2ª linha do cadastro', r"(cad ? '\nCadastro do app: ' + mmsiNum() + '.' : '')", r"''", ('p3c',)),
    ('a sobreDados afirma que é real', r"return { text: (s ? SOBRE_DADOS :", r"return { text: (s ? 'Os dados são reais. ' + SOBRE_DADOS :", ('p3c',)),
    ('a sobreDados sem a situação de bordo', r"+ '\n' + linhaBordo()," "\n        src: s ? 'Fonte: este aparelho · modo de apresentação'", r"," "\n        src: s ? 'Fonte: este aparelho · modo de apresentação'", ('p3c',)),
    ('o foraBarco sem a situação de bordo', r"'Isso fica fora do barco.\n' + linhaBordo()", r"'Isso fica fora do barco.'", ('p3c',)),
    # —— o modo real e o SOS (grupo p3c_dados) ——
    ('a sobreDados do modo real diz a frase de apresentação', r"return { text: (s ? SOBRE_DADOS :", r"return { text: (true ? SOBRE_DADOS :", ('p3c_dados',)),
    ('o MMSI do SOS mostra o do cadastro', r"cad = !EM_SOS && mmsiNeutra(pq);", r"cad = mmsiNeutra(pq);", ('p3c_dados',)),
    ('as pessoas do SOS leem o cadastro', r"var n = EM_SOS ? null : E.pessoasBordo, lot = EM_SOS ? null : E.lotacao, i = vivo();", r"var n = E.pessoasBordo, lot = E.lotacao, i = vivo();", ('p3c_dados',)),
    ('a embarcação do SOS mostra o cadastro', r"      if (EM_SOS) return { text: (E.nome || SD) + '.', src: 'Fonte: cadastro da embarcação', actions: [] };   // no SOS o cérebro não lê o cadastro além do nome", r"", ('p3c_dados',)),
    ('a rota do plano é lida no SOS', r"function rotaDoPlano() { return EM_SOS ? null : D.rota; }", r"function rotaDoPlano() { return D.rota; }", ('p3c_dados',)),
    ('o catálogo de alertas é lido no SOS', r"function catalogoAlertas() { return EM_SOS ? {} : (D.replay && D.replay.alertas) || {}; }", r"function catalogoAlertas() { return (D.replay && D.replay.alertas) || {}; }", ('p3c_dados',)),
    ('o quadro de coletor sem destino diz o destino do replay', r"if (!i || typeof q.destino !== 'string') {", r"if (!i) {", ('p3c_dados',)),
    ('o quadro de coletor sem a lista de alarmes cai no «Nenhum alarme ativo»', r"if (!i || !lista) {" "\n        return { text: sim() && i ? 'O coletor não trouxe a lista de alarmes às '", r"if (!i) {" "\n        return { text: sim() && i ? 'O coletor não trouxe a lista de alarmes às '", ('p3c_dados',)),
    ('o alarme do quadro sem a CapitaoAlertas perde o botão da C3', r"detalhe: cat.passos ? 'C3-Leme-Alerta.dc.html#alarme=' + a.id : '' };", r"detalhe: '' };", ('p3c_dados',)),
    ('o alarme do quadro sem a CapitaoAlertas perde a hora desde', r"hora: isFinite(ms) ? F.hora(ms, true) : '', passos:", r"hora: '', passos:", ('p3c_dados',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3C

# Revisão da P3C: um mutante por guarda das rotas novas (cada um tem de ser acusado pelo grupo p3c; o do SOS, pelo p3c_dados)
MUTANTES_3C_REV = [
    # —— a navegação só é a pergunta inteira ——
    ('a navegação pega «situação atual do gerador» (a frase solta, sem o fim ancorado)', r"|neste momento|por ai|ai))* $/;", r"|neste momento|por ai|ai))* /;", ('p3c',)),
    ('a navegação pega o piloto automático (a lista neutra aceita «piloto», «automático», «gerador»)', r"var NAVEGACAO_OK = NEUTRAS_BASE + 'navegacao status", r"var NAVEGACAO_OK = NEUTRAS_BASE + 'piloto automatico gerador motor navegacao status", ('p3c',)),
    # —— o cadastro do barco não responde por outra coisa a bordo ——
    ('a embarcação pega a âncora do barco (a lista neutra do barco aceita «âncora», «corrente», «motor»)', r"'barco barcos lancha embarcacao real sao maxima minima total '", r"'barco barcos lancha embarcacao real sao maxima minima total ancora corrente motor amarra '", ('p3c',)),
    ('a embarcação pega o comprimento da sonda (sem a regra do que sobra na pergunta)', r"return q.trim().split(' ').every(function (w) { return EMB_RESTO_OK.indexOf(' ' + w + ' ') !== -1; });", r"return true;", ('p3c',)),
    ('as pessoas pegam a lotação do bote (a lista neutra aceita «cabem», «bote»)', r"var PESSOAS_OK = NEUTRAS_BASE + 'pessoas pessoa", r"var PESSOAS_OK = NEUTRAS_BASE + 'cabem cabe bote tender pessoas pessoa", ('p3c',)),
    # —— a temperatura do motor e da água ——
    ('a temperatura do motor pega o gerador e o Seakeeper (a lista neutra aceita «gerador», «seakeeper» e «climatização»)', r"estibordo esquerdo direito principal principais dois ambos graus", r"estibordo esquerdo direito principal principais dois ambos graus gerador seakeeper climatizacao", ('p3c',)),
    ('a temperatura da água pega a do Seakeeper (a lista neutra aceita «seakeeper»)', r"'temperatura agua mar graus fria gelada quente morna", r"'temperatura agua mar graus fria gelada quente morna seakeeper", ('p3c',)),
    ('a temperatura da água pega a que caiu (a lista neutra aceita «caiu»)', r"'temperatura agua mar graus fria gelada quente morna", r"'temperatura agua mar graus fria gelada quente morna caiu", ('p3c',)),
    # —— o alarme que soa e o que tem lugar ——
    ('o alarme que soa vira «nenhum alarme ativo» (a falsa tranquilização)', r"soa = alarmeSoando(qq || '')", r"soa = false", ('p3c',)),
    ('o alarme de um lugar ou equipamento volta à rota dos alarmes (a lista neutra aceita «cabine», «Seakeeper»)', r"var ALARMES_OK = NEUTRAS_BASE + 'alarme alarmes", r"var ALARMES_OK = NEUTRAS_BASE + 'cabine seakeeper climatizacao alarme alarmes", ('p3c',)),
    ('o resgate que se espera vira a chegada da rota (a lista branca aceita «resgate»)', r"var ETA_OK = NEUTRAS_BASE + 'quando ja muito estamos eta chegada", r"var ETA_OK = NEUTRAS_BASE + 'quando ja muito estamos resgate eta chegada", ('p3c',)),
    # —— o ETA e a profundidade ——
    ('o procedimento do waypoint volta à chegada (a lista branca aceita «criar», «marcar», «plotter»…)', r"var ETA_OK = NEUTRAS_BASE + 'quando ja muito estamos eta chegada", r"var ETA_OK = NEUTRAS_BASE + 'quando ja muito estamos um uma criar marcar salvar inserir plotter eta chegada", ('p3c',)),
    ('as milhas por litro voltam à chegada (a lista branca aceita «litro», «galão»)', r"var ETA_OK = NEUTRAS_BASE + 'quando ja muito estamos eta chegada", r"var ETA_OK = NEUTRAS_BASE + 'quando ja muito estamos litro galao eta chegada", ('p3c',)),
    ('«quantas milhas» sozinho volta a ser a chegada', r"'quantas milhas faltam', 'quantas milhas falta',", r"'quantas milhas', 'quantas milhas faltam', 'quantas milhas falta',", ('p3c',)),
    ('as milhas por hora saem da posição', r"' sog ', ' quantos nos ', 'milhas por hora'];", r"' sog ', ' quantos nos '];", ('p3c',)),
    ('a profundidade pega a do porão e a do fundeio (a lista neutra aceita «porão», «tanque» e «fundeio»)', r"neste nesse momento ponto local lugar metros", r"neste nesse momento ponto local lugar metros porao tanque fundeio", ('p3c',)),
    ('a profundidade pega a da corrente e da âncora (a lista neutra aceita «corrente», «âncora», «aguenta» e «transdutor»)', r"neste nesse momento ponto local lugar metros", r"neste nesse momento ponto local lugar metros corrente ancora aguenta transdutor", ('p3c',)),
    ('a profundidade pega o relato de falha do sensor (a lista neutra aceita «falha», «funciona», «erro», «zerada», «quebrou»)', r"neste nesse momento ponto local lugar metros", r"neste nesse momento ponto local lugar metros falha funciona funcionando erro zerada quebrou", ('p3c',)),
    ('a profundidade pega a negativa («não estou vendo»)', r"neste nesse momento ponto local lugar metros", r"neste nesse momento ponto local lugar metros nao estou vendo", ('p3c',)),
    ('a profundidade pega a de outro lugar (a lista neutra aceita «marina», «rio», «canal»)', r"neste nesse momento ponto local lugar metros", r"neste nesse momento ponto local lugar metros marina rio canal", ('p3c',)),
    # —— o câmbio, o jogo e a bolsa de bordo ——
    ('o câmbio do barco (a reversora) vira dinheiro', r"(has(q, ['cambio']) && !has(q, CAMBIO_BORDO))", r"has(q, ['cambio'])", ('p3c',)),
    ('o câmbio sai do foraBarco', r"|| (has(q, ['cambio']) && !has(q, CAMBIO_BORDO))", r"", ('p3c',)),
    ('o jogo do barco (o balanço) vira esporte', r"(has(q, [' jogo ', ' jogos ']) && !has(q, JOGO_BORDO))", r"has(q, [' jogo ', ' jogos '])", ('p3c',)),
    ('o jogo sai do foraBarco', r"|| (has(q, [' jogo ', ' jogos ']) && !has(q, JOGO_BORDO))", r"", ('p3c',)),
    ('a bolsa de bordo vira dinheiro', r"(has(q, ['bolsa']) && !has(q, BOLSA_BORDO))", r"has(q, ['bolsa'])", ('p3c',)),
    ('a bolsa sai do foraBarco', r"|| (has(q, ['bolsa']) && !has(q, BOLSA_BORDO))", r"", ('p3c',)),
    # —— a sobreDados: «real» como medida não é a pergunta ——
    ('a sobreDados pega «diesel real» (o «real» sem o predicado)', r"return !medidaAut(q) && (AUT_NOME.test(q) || (has(q, AUT_ALVO) && (AUT_PRED.test(q) || AUT_INV.test(q))));", r"return has(q, AUT_ALVO) && has(q, [' real ', ' reais ', ' de verdade ', ' verdadeir']);", ('p3c',)),
    ('a sobreDados sem a lancha, o Capitão IA e você como alvo', r"    ' lancha ', ' lanchas ', ' voce ', ' vc ', ' capitao ', ' ia ', ' sistema ',", r"    ' sistema ',", ('p3c',)),
    ('a sobreDados sem o diesel, a velocidade e o consumo como alvo', "' informacoes ', ' diesel ', ' combustivel ', ' velocidade ', ' rumo ', ' vento ', ' ondas ', ' profundidade ',\n    ' consumo ', ' autonomia ', ' temperatura ', ' calado ', ' horimetros '];", "' informacoes '];", ('p3c',)),
    ('a sobreDados sem «esse barco existe»', r"' esse barco existe ', ' este barco existe ', ' a lancha existe ', ' essa lancha existe ', ' essa embarcacao existe ', ' existe de verdade ', ' voce existe '];", r"' isso existe '];", ('p3c',)),
    ('a sobreDados sem «simulam»', r"' simulam ', ' simula ', ' simulou ', ", r"", ('p3c',)),
    # —— o SOS não lê o cadastro de equipamentos nem o calado ——
    ('o AIS do SOS lê o cadastro de equipamentos', r"      if (EM_SOS) return { text: 'AIS: os alvos aparecem no plotter, com nome, rumo e velocidade.', src: 'Fonte: Guia de bordo — AIS §1', actions: [] };   // no SOS o cérebro não lê o cadastro de equipamentos nem o quadro" + "\n", r"", ('p3c_dados',)),
    ('a profundidade do SOS mostra o calado do cadastro', r"cal = EM_SOS ? null : E.calado;", r"cal = E.calado;", ('p3c_dados',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3C_REV

# Revisão 2 da P3C: um mutante por regra da sobreDados (cada forma de perguntar), por desvio do MMSI, por guarda da pergunta mista e por lista de palavras neutras (todos acusados pelo grupo p3c)
MUTANTES_3C_REV2 = [
    # —— a sobreDados em cada jeito de perguntar ——
    ('a sobreDados sem as palavras no meio do predicado («os dados são de fato reais?»)', r"' ' + AUT_COP + ' (?:[a-z0-9]+ ){0,3}' + AUT_AW + AUT_CAUDA", r"' ' + AUT_COP + ' ' + AUT_AW + AUT_CAUDA", ('p3c',)),
    ('a sobreDados sem o nome dos dados («dados reais?», «você usa dados reais?»)', r"return !medidaAut(q) && (AUT_NOME.test(q) || (", r"return !medidaAut(q) && (false || (", ('p3c',)),
    ('a sobreDados sem a ordem invertida («são reais esses dados?»)', r"(AUT_PRED.test(q) || AUT_INV.test(q))", r"(AUT_PRED.test(q))", ('p3c',)),
    ('a sobreDados sem «o que é real aqui?»', r"if (AUT_CURTA.test(q) || AUT_QUE_E.test(q) || AUT_NAVEGANDO.test(q)) return true;", r"if (AUT_CURTA.test(q) || AUT_NAVEGANDO.test(q)) return true;", ('p3c',)),
    ('a sobreDados sem «estamos navegando de verdade?»', r"if (AUT_CURTA.test(q) || AUT_QUE_E.test(q) || AUT_NAVEGANDO.test(q)) return true;", r"if (AUT_CURTA.test(q) || AUT_QUE_E.test(q)) return true;", ('p3c',)),
    ('a sobreDados sem «está simulado?» e «estamos em…» na forma curta', r"(?:e|eh|sao|era|foi|esta|estao|ta|tao|estamos|estou|seria|sera) (?:(?:so|apenas", r"(?:e|eh|sao|era|foi|seria|sera) (?:(?:so|apenas", ('p3c',)),
    ('a sobreDados sem «estamos em uma simulação?» (o «em/numa» da forma curta)', r"(?:(?:em|numa|num|dentro de) )?", r"", ('p3c',)),
    ('a sobreDados sem «é só uma simulação?» (o «só/apenas» da forma curta)', r"(?:(?:so|apenas|somente|tudo|isso|isto|mesmo|totalmente|realmente|muito|tao) )*", r"(?:(?:tudo|isso|isto|mesmo|totalmente|realmente|muito|tao) )*", ('p3c',)),
    ('a sobreDados sem «é uma demo?» e «é um simulador?» na forma curta', r"|fake|de mentira|simulacao|simulador|demonstracao|demo)(?: (?:mesmo|ne|certo|de verdade|de fato|ou nao", r"|fake|de mentira|simulacao|demonstracao)(?: (?:mesmo|ne|certo|de verdade|de fato|ou nao", ('p3c',)),
    ('a sobreDados sem «falso» e «fake» como palavra de autenticidade', r"var AUT_AW = '(?:real|reais|de verdade|verdadeir[oa]s?|fals[oa]s?|fake)';", r"var AUT_AW = '(?:real|reais|de verdade|verdadeir[oa]s?)';", ('p3c',)),
    ('a sobreDados sem «você está simulando?» (o «simulando» entre as palavras fortes)', r"' simulou ', ' simuland', ' simulador',", r"' simulou ',", ('p3c',)),
    ('a sobreDados sem a cauda «mesmo», «né», «certo» («você usa dados reais, né?»)', r"(?: (?:mesmo|ne|certo|de fato|de verdade|hein|ou nao|nao e|nao))*", r"", ('p3c',)),
    # —— o que não é a pergunta da autenticidade ——
    ('a sobreDados pega «quanto de diesel é real?» (sem o quanto/qual como medida)', r" | (?:quanto|quanta|quantos|quantas|qual|quais) /;", r" /;", ('p3c',)),
    ('a sobreDados pega «isso é o consumo real?» (sem o consumo colado ao real)', r"(?:tempo|velocidade|vento|valor|consumo|diesel|", r"(?:tempo|velocidade|vento|valor|diesel|", ('p3c',)),
    ('a sobreDados pega «os valores são em reais?» (sem a moeda)', r" | (?:em|de|mil|milhoes de) reais ", r" | (?:xem|de|mil|milhoes de) reais ", ('p3c',)),
    ('a sobreDados pega «o rumo é verdadeiro?» (sem o vento e o rumo verdadeiros)', r"(has(q, [' vento', 'rumo', 'norte', ' proa', ' curso ', 'marcacao']) && has(q, [' verdadeir']))", r"false", ('p3c',)),
    ('a sobreDados pega «o vento é real?» (sem o vento real)', r" || (has(q, [' vento']) && has(q, [' real ', ' reais ']));", r";", ('p3c',)),
    # —— o MMSI com outro assunto junto ——
    ('o MMSI pega o EPIRB (sem o desvio para a rota epirb)', r"    if (epirbRelato(q) || has(q, ['baliza'])) return 'epirb';" "\n", r"", ('p3c',)),
    ('o MMSI pega a baliza (o desvio só para «epirb»)', r"if (epirbRelato(q) || has(q, ['baliza'])) return 'epirb';", r"if (epirbRelato(q)) return 'epirb';", ('p3c',)),
    ('o MMSI pega o Seafire (sem o desvio para a rota seafire)', r"    if (seafirePergunta(q)) return 'seafire';" "\n" r"    if (has(q, CANAL16_SEG) || has(q, MMSI_PERIGO)) return 'canal16';", r"    if (has(q, CANAL16_SEG) || has(q, MMSI_PERIGO)) return 'canal16';", ('p3c',)),
    ('o MMSI pega o roteiro de rádio (pan-pan, DSC, canal 16: sem as palavras do rádio)', r"if (has(q, CANAL16_SEG) || has(q, MMSI_PERIGO)) return 'canal16';", r"if (has(q, MMSI_PERIGO)) return 'canal16';", ('p3c',)),
    ('o MMSI pega a pane («o motor parou, qual o MMSI?»: sem as palavras de socorro e pane)', r"if (has(q, CANAL16_SEG) || has(q, MMSI_PERIGO)) return 'canal16';", r"if (has(q, CANAL16_SEG)) return 'canal16';", ('p3c',)),
    ('o MMSI vê «parou» dentro de «disparou» (a palavra sem o espaço)', r"' pane', ' parou', 'falha'", r"' pane', 'parou', 'falha'", ('p3c',)),
    ('o MMSI pega o vencimento (sem o desvio para o documento)', r"    if (has(q, MMSI_VENCE)) return 'docsvenc';" "\n", r"", ('p3c',)),
    ('o MMSI mostra o número do cadastro na pergunta de programar', r"cad = !EM_SOS && mmsiNeutra(pq);", r"cad = !EM_SOS;", ('p3c',)),
    ('o MMSI sem a linha do indicativo', r"(ind ? ' Indicativo: ' + INDICATIVO + '.' : '')", r"''", ('p3c',)),
    # —— a pergunta mista é do equipamento de segurança ——
    ('o AIS pega o relato e a pergunta mista do rádio (sem a lista branca)', r"if (has(q, [' ais ']) && leitura(q, AIS_OK)) return 'ais';", r"if (has(q, [' ais '])) return 'ais';", ('p3c',)),
    ('a pergunta mista não vê o «canal 16»', r"var CANAL16_SEG = ['canal 16', 'pan-pan',", r"var CANAL16_SEG = ['xcanal 16', 'pan-pan',", ('p3c',)),
    ('a pergunta mista não vê o «pan-pan»', r"'canal 16', 'pan-pan', 'pan pan', ' dsc', 'distress'];", r"'canal 16', 'xpan-pan', 'pan pan', ' dsc', 'distress'];", ('p3c',)),
    ('a pergunta mista não vê o «pan pan»', r"'canal 16', 'pan-pan', 'pan pan', ' dsc', 'distress'];", r"'canal 16', 'pan-pan', 'xpan pan', ' dsc', 'distress'];", ('p3c',)),
    ('a pergunta mista não vê o DSC', r"'canal 16', 'pan-pan', 'pan pan', ' dsc', 'distress'];", r"'canal 16', 'pan-pan', 'pan pan', ' xdsc', 'distress'];", ('p3c',)),
    ('a pergunta mista não vê o «distress»', r"'canal 16', 'pan-pan', 'pan pan', ' dsc', 'distress'];", r"'canal 16', 'pan-pan', 'pan pan', ' dsc', 'xdistress'];", ('p3c',)),
    ('a pergunta mista não vê a supressão do Seafire', r"'sistema de incendio', 'supressao', 'disparo manual'];", r"'sistema de incendio', 'xsupressao', 'disparo manual'];", ('p3c',)),
    ('a pergunta mista não vê o Seafire pelo nome', r"var SEAFIRE_PALAVRAS = ['seafire', 'sea fire', 'sea-fire',", r"var SEAFIRE_PALAVRAS = ['xseafire', 'sea fire', 'sea-fire',", ('p3c',)),
    # —— a leitura calma só responde a pergunta neutra ——
    ('a temperatura do motor pega o relato (a lista neutra aceita «vermelho», «parou», «chegou», «perdi»…)', r"estibordo esquerdo direito principal principais dois ambos graus", r"estibordo esquerdo direito principal principais dois ambos graus vermelho parou chegou perdi sem falhou passou critica perigosa preocupante elevada estourando apitando ponteiro", ('p3c',)),
    ('a profundidade pega o relato de estado (a lista neutra aceita «caindo», «diminuindo», «zero»…)', r"neste nesse momento ponto local lugar metros", r"neste nesse momento ponto local lugar metros caindo diminuindo zero rapido", ('p3c',)),
    ('as ondas pegam o relato (a lista neutra aceita «muito», «com», «batendo», «forte»…)', r"'mar ondas onda ondulacao altura estado swell agitado grosso calmo bordo", r"'mar ondas onda ondulacao altura estado swell agitado grosso calmo bordo muito com batendo forte", ('p3c',)),
    ('a água do mar pega o relato (a lista neutra aceita «subindo», «caiu»…)', r"'temperatura agua mar graus fria gelada quente morna", r"'temperatura agua mar graus fria gelada quente morna subindo caiu", ('p3c',)),
    ('a leitura calma aceita o número («a temperatura do motor está em 110»)', r"function soNeutras(q, ok) { return q.trim().split(' ').every(function (w) { return ok.indexOf(' ' + w + ' ') !== -1; }); }", r"function soNeutras(q, ok) { return q.trim().split(' ').every(function (w) { return ok.indexOf(' ' + w + ' ') !== -1 || /^\d+$/.test(w); }); }", ('p3c',)),
    ('a leitura calma aceita qualquer palavra (a lista neutra sem efeito)', r"function soNeutras(q, ok) { return q.trim().split(' ').every(function (w) { return ok.indexOf(' ' + w + ' ') !== -1; }); }", r"function soNeutras(q, ok) { return true; }", ('p3c',)),
    ('a temperatura do motor perde a marca do cadastro («Cummins»: sem as palavras do motor)', r"return ARREF_OK + (e && e.palavras ? e.palavras.map(norm).join(' ') + ' ' : ''); }", r"return ARREF_OK; }", ('p3c',)),
    ('a profundidade sem «real barco» (a lista neutra estreita demais)', r"mede medindo real barco lancha embarcacao nosso nossa", r"mede medindo lancha embarcacao nosso nossa", ('p3c',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3C_REV2


# Revisão 3 da P3C: um mutante por guarda nova (cada um tem de ser acusado pelo grupo p3c)
MUTANTES_3C_REV3 = [
    # —— o MMSI: lista branca ——
    ('o MMSI aceita o rádio, o VHF, o AIS, o DSC e o plotter na pergunta neutra', r"MMSI_OK = NEUTRAS_BASE.replace(' por ', ' ') + 'que mmsi", r"MMSI_OK = NEUTRAS_BASE.replace(' por ', ' ') + 'radio vhf ais dsc transponder plotter que mmsi", ('p3c',)),
    ('o MMSI aceita os verbos de pôr o número (coloco, digito, insiro, cadastro…)', r"MMSI_OK = NEUTRAS_BASE.replace(' por ', ' ') + 'que mmsi",
     r"MMSI_OK = NEUTRAS_BASE.replace(' por ', ' ') + 'coloco coloque colocar digito digite digitar insiro insira inserir cadastro cadastre cadastrar atualizo atualize atualizar altero altere alterar mudo mude mudar ajusto ajuste defino defina configuro configure programo programe gravo grave salvo salve informo adiciono adicione incluo inclua preencho preencha edito edite habilito habilite ativo ative uso use registro registre troco troque seto sete ponho ponha anoto anote lanco lance carrego carregue aponto aponte transmito transmita que mmsi", ('p3c',)),
    ('o MMSI aceita o «por» do «pôr» (a lista neutra com o «por favor»)', r"MMSI_OK = NEUTRAS_BASE.replace(' por ', ' ') + ", r"MMSI_OK = NEUTRAS_BASE + ", ('p3c',)),
    ('o MMSI perde o «por favor» no meio da pergunta', r"soNeutras(semVocativo(pq).replace(/ por favor /g, ' ').replace(", r"soNeutras(semVocativo(pq).replace(", ('p3c',)),
    ('o MMSI aceita o verbo «cadastro» («como cadastro o MMSI?»: o substantivo sem o «do/no/pelo»)', r"replace(/ (?:do|no|pelo|de) cadastro /g, ' cadastrado '), MMSI_OK)", r"replace(/ (?:do|no|pelo|de) cadastro /g, ' cadastrado ').replace(/ cadastro /g, ' cadastrado '), MMSI_OK)", ('p3c',)),
    ('o MMSI perde o «do cadastro» («qual o MMSI do cadastro?»)', r".replace(/ (?:do|no|pelo|de) cadastro /g, ' cadastrado '), MMSI_OK)", r", MMSI_OK)", ('p3c',)),
    ('o MMSI perde a pergunta neutra (a lista sem «mmsi», «barco», «cadastro»…)', r"'que mmsi barco lancha embarcacao cadastrado cadastrada registrado app aplicativo numero nosso nossa meu minha seu sua indicativo '", r"'que mmsi'", ('p3c',)),
    # —— a leitura calma só responde a pergunta neutra, em cada rota nova ——
    ('a posição pega o relato (as palavras novas sem a lista neutra)', r"(has(q, POSICAO_NOVAS) && leitura(q, POSICAO_OK))", r"has(q, POSICAO_NOVAS)", ('p3c',)),
    ('a posição pega a definição e o rumo magnético (a lista neutra aceita «significa», «magnético», «milha náutica»)', r"var POSICAO_OK = NEUTRAS_BASE + 'que estamos onde", r"var POSICAO_OK = NEUTRAS_BASE + 'significa magnetico nautica uma tem nossos tripulantes que estamos onde", ('p3c',)),
    ('a chegada pega o relato e o lugar fora da rota (sem a lista branca)', r"    return leitura(q, ETA_OK + lugaresRota().join(''));", r"    return true;", ('p3c',)),
    ('a chegada pega o nome de um lugar fora da rota (a lista branca aceita «Itajaí», «costa»)', r"var ETA_OK = NEUTRAS_BASE + 'quando ja muito estamos eta chegada", r"var ETA_OK = NEUTRAS_BASE + 'quando ja muito estamos itajai costa eta chegada", ('p3c',)),
    ('a chegada perde o nome dos pontos da rota (a lista branca sem o D.rota)', r"leitura(q, ETA_OK + lugaresRota().join(''))", r"leitura(q, ETA_OK)", ('p3c',)),
    ('os alarmes pegam o relato (sem a lista branca)', r"|| ALARME_SOANDO.test(q)) && leitura(q, ALARMES_OK); }", r"|| ALARME_SOANDO.test(q)); }", ('p3c',)),
    ('as pessoas pegam o relato (sem a lista branca)', r"if (has(q, PESSOAS_PALAVRAS) && leitura(q, PESSOAS_OK)) return 'pessoas';", r"if (has(q, PESSOAS_PALAVRAS)) return 'pessoas';", ('p3c',)),
    ('a navegação pega o relato (sem a lista branca)', r"(has(q, NAVEGACAO_PALAVRAS) && leitura(q, NAVEGACAO_OK))", r"has(q, NAVEGACAO_PALAVRAS)", ('p3c',)),
    ('a embarcação do barco pega o relato (sem a lista branca)', r"return !DEFINICAO.test(q) && q.trim().split(' ').every(function (w) { return ok.indexOf(' ' + w + ' ') !== -1 || /^\d+$/.test(w); }); }", r"return true; }", ('p3c',)),
    ('a embarcação não aceita o número («a lotação do barco é 12?»)', r"return ok.indexOf(' ' + w + ' ') !== -1 || /^\d+$/.test(w); }); }", r"return ok.indexOf(' ' + w + ' ') !== -1; }); }", ('p3c',)),
    ('a embarcação do barco pega a definição («o que é a lotação do barco?»)', r"return !DEFINICAO.test(q) && q.trim().split(' ').every(function (w) { return ok.indexOf", r"return q.trim().split(' ').every(function (w) { return ok.indexOf", ('p3c',)),
    ('a leitura pega a definição («o que é ETA?»)', r"var DEFINICAO = / (?:o que|oque|oq) (?:e|eh|sao|significa|quer dizer) | significa ", r"var DEFINICAO = / significa ", ('p3c',)),
    # —— o pedido de socorro que a lista SOS não pega ——
    ('o pedido de socorro implícito sai da route()', r"    if (socorroImplicito(q)) return 'sos';" "\n", r"", ('p3c',)),
    ('o pedido de socorro sem «estamos em risco»', r"var EM_RISCO = /\b(?:(?:estamos|estou|ficamos)(?: todos)? em (?:risco|apuros)|", r"var EM_RISCO = /\b(?:(?:xestamos|xestou|xficamos)(?: todos)? em (?:risco|apuros)|", ('p3c',)),
    ('o pedido de socorro sem «o barco está em risco»', r"|(?:o barco|a lancha|a embarcacao) (?:esta|ta) em (?:risco|apuros))", r"|(?:xo barco|xa lancha|xa embarcacao) (?:esta|ta) em (?:risco|apuros))", ('p3c',)),
    ('o pedido de socorro sem «corremos risco»', r"|(?:corremos|corro|correndo|corre|correm|correu|corriam) risco|", r"|(?:xcorremos|xcorro|xcorrendo|xcorre|xcorrem|xcorreu|xcorriam) risco|", ('p3c',)),
    ('«em risco de chuva» vira socorro (a regex sem a exceção do «de»)', r"em (?:risco|apuros))\b(?! de (?!(?:vida|afund|naufrag|incend|fogo|colid|colis|encalh|morr|explod|emborc|alag|capot|virar)))/;", r"em (?:risco|apuros))\b/;", ('p3c',)),
    ('o pedido de socorro sem «isso não é um teste»', r"|| NAO_TESTE.test(q) || EM_RISCO.test(q) || SOCORRO_AJUDA", r"|| EM_RISCO.test(q) || SOCORRO_AJUDA", ('p3c',)),
    ('o pedido de socorro sem «isso é real, preciso de ajuda» (o pedido + a declaração)', r"(SOCORRO_PEDE.test(q) && (SOCORRO_DECLARA.test(q) || has(q, DADOS_MAYDAY)))", r"(SOCORRO_PEDE.test(q) && has(q, DADOS_MAYDAY))", ('p3c',)),
    ('o pedido de socorro sem «preciso de ajuda, qual o ETA?» (o pedido + o dado do MAYDAY)', r"(SOCORRO_PEDE.test(q) && (SOCORRO_DECLARA.test(q) || has(q, DADOS_MAYDAY)))", r"(SOCORRO_PEDE.test(q) && SOCORRO_DECLARA.test(q))", ('p3c',)),
    ('o pedido de ajuda de rotina vira socorro («preciso de ajuda para trocar o óleo»)', r"(SOCORRO_PEDE.test(q) && (SOCORRO_DECLARA.test(q) || has(q, DADOS_MAYDAY)))", r"(SOCORRO_PEDE.test(q))", ('p3c',)),
    ('a sobreDados pega «o alarme de temperatura é real?»', r"if (AUT_SENSOR_DE.test(q) || (has(q, AUT_SENSOR)", r"if ((has(q, AUT_SENSOR)", ('p3c',)),
    ('a sobreDados pega «esse alarme é falso?»', r"(has(q, AUT_SENSOR) && AUT_FALSO.test(q)) || !soAutenticidade(q)) return false;", r"!soAutenticidade(q)) return false;", ('p3c',)),
    # —— a sobreDados em mais jeitos de perguntar ——
    ('a sobreDados sem «estão/tá/tão» (a cópula só com «ser»)', r"|parece|parecem|esta|estao|ta|tao|estava|estavam)';", r"|parece|parecem)';", ('p3c',)),
    ('a sobreDados sem a cauda «não é?» («os dados são reais, não é?»)', r"hein|ou nao|nao e|nao))*';", r"hein|ou nao))*';", ('p3c',)),
    ('a sobreDados sem «é real ou não?» na forma curta', r"|de fato|ou nao|nao e|nao|ou (?:e |eh |esta )?(?:real", r"|de fato|ou (?:e |eh |esta )?(?:real", ('p3c',)),
    ('a sobreDados sem «é simulado ou é real?» na forma curta', r"|de fato|ou nao|nao e|nao|ou (?:e |eh |esta )?(?:real|reais|de verdade|verdadeir[oa]s?|simulad[oa]s?|fictici[oa]s?|fals[oa]s?|fake|de mentira)))* $/;", r"|de fato|ou nao|nao e|nao))* $/;", ('p3c',)),
    # —— fora do barco: «quem venceu» ——
    ('a manutenção pega «quem venceu o jogo ontem?» (o «vence» dentro de «venceu»)', r"(has(q, ['vence']) && !(has(q, ['venceu', 'vencedor', 'venceram']) && foraBarcoPergunta(q)))", r"has(q, ['vence'])", ('p3c',)),
    ('o foraBarco sem «quem venceu» («quem venceu?»)', r", 'quem venceu', 'quem ganhou'];", r", 'quem ganhou'];", ('p3c',)),
    ('o foraBarco sem «quem ganhou» («quem ganhou o campeonato?»)', r", 'quem venceu', 'quem ganhou'];", r", 'quem venceu'];", ('p3c',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3C_REV3


# Revisão 4 da P3C: um mutante por guarda nova (cada um tem de ser acusado pelo grupo p3c)
MUTANTES_3C_REV4 = [
    # —— «preço» é palavra inteira ——
    ('o foraBarco casa «preco» solto (preconizado, precoce)', r"' cotacao ', ' cotacoes ', ' bitcoin ', ' preco ', ' precos ', 'quanto custa'", r"' cotacao ', ' cotacoes ', ' bitcoin ', 'preco', 'quanto custa'", ('p3c',)),
    ('o foraBarco sem «preços» (o plural)', r"' preco ', ' precos ', 'quanto custa'", r"' preco ', 'quanto custa'", ('p3c',)),
    # —— a sobreDados: lista branca ——
    ('a sobreDados responde ao relato de falha ou de perigo (sem a lista branca)', r"(has(q, AUT_SENSOR) && AUT_FALSO.test(q)) || !soAutenticidade(q)) return false;", r"(has(q, AUT_SENSOR) && AUT_FALSO.test(q))) return false;", ('p3c',)),
    ('a sobreDados perde o vocabulário do pedido («preciso saber», «é sério», «é urgente»)', r"existe existem preciso precisamos saber confirmar urgente serio relatorio decidir saio quero queria gostaria checar conferir verificar afinal pergunto duvida curiosidade ');", r"existe existem ');", ('p3c',)),
    ('a sobreDados perde o pedido que vem depois da pergunta («…são reais? preciso decidir se saio»)', r"    q = q.replace(AUT_PEDIDO_FIM, '$1');" + "\n", r"", ('p3c',)),
    ('a sobreDados aceita o «não» em qualquer lugar («o alarme não para, isso é real?»)', r"existe existem preciso precisamos saber", r"existe existem nao preciso precisamos saber", ('p3c',)),
    ('a sobreDados perde o «não» das caudas («isso não é real, né?»)', r"var AUT_NAO = / (?:ou )?nao (?:e|eh|sao|foi|era)(?= )| ou nao(?= )| nao $/g;", r"var AUT_NAO = / zzz /g;", ('p3c',)),
    ('a sobreDados perde as palavras do estado do pedido («ambiente de demonstração»)', r" demonstracao ambiente modo versao apresentacao plataforma programa exemplo treinamento genuino autentico oficial ", r" demonstracao ", ('p3c',)),
    # —— o pedido de socorro: «correr risco» e «ajudem» ——
    ('o pedido de socorro só em «corremos/corro risco» (sem «correndo», «corre»…)', r"|(?:corremos|corro|correndo|corre|correm|correu|corriam) risco|", r"|(?:corremos|corro) risco|", ('p3c',)),
    ('o «risco de <perigo de bordo>» não é socorro («estamos correndo risco de afundar»)', r"(?! de (?!(?:vida|afund|naufrag|incend|fogo|colid|colis|encalh|morr|explod|emborc|alag|capot|virar)))", r"(?! de (?!vida))", ('p3c',)),
    ('o pedido «ajudem» não é socorro', r"var SOCORRO_AJUDA = /\bajudem\b|", r"var SOCORRO_AJUDA = /\bxajudem\b|", ('p3c',)),
    ('o pedido «alguém me ajuda» não é socorro', r"|\balguem (?:me |nos )?(?:ajuda|ajude)(?: por favor", r"|\bxalguem (?:me |nos )?(?:ajuda|ajude)(?: por favor", ('p3c',)),
    ('«alguém me ajuda a trocar o óleo» vira socorro (o pedido sem o fim ancorado)', r"(?: por favor| aqui| agora)? $|\bpelo amor", r"(?: por favor| aqui| agora)?|\bpelo amor", ('p3c',)),
    ('o pedido «pelo amor de Deus, ajuda» não é socorro', r"|\bpelo amor de deus\b.*\b(?:ajuda|ajudem|ajude|socorro)\b/;", r"/;", ('p3c',)),
    # —— o AIS: só a pergunta neutra do status ——
    ('o AIS perde «situação», «status» e «estado» («qual a situação do AIS?»)', r"quantidade quais situacao status estado barco", r"quantidade quais barco", ('p3c',)),
    ('o AIS aceita o relato de falha (a lista neutra aceita «parou», «não», «funciona»)', r"var AIS_OK = NEUTRAS_BASE + 'ais alvos", r"var AIS_OK = NEUTRAS_BASE + 'parou apagou desligado desligada falha nao funciona sinal sem ais alvos", ('p3c',)),
    # —— a chegada em todo jeito de perguntar ——
    ('a chegada perde o «quando» («quando chegamos?»)', r"var ETA_OK = NEUTRAS_BASE + 'quando ja muito estamos eta", r"var ETA_OK = NEUTRAS_BASE + 'ja muito estamos eta", ('p3c',)),
    ('a chegada perde «já», «muito» e «estamos» («já chegamos?», «falta muito para chegar?», «estamos chegando?»)', r"var ETA_OK = NEUTRAS_BASE + 'quando ja muito estamos eta", r"var ETA_OK = NEUTRAS_BASE + 'quando eta", ('p3c',)),
    ('a chegada perde «vamos chegar a que horas»', r"    'vamos chegar a que horas', 'a que horas vamos chegar',", r"    'a que horas vamos chegar',", ('p3c',)),
    ('a chegada perde «em quanto tempo chegamos»', r"'em quanto tempo chegamos', 'em quanto tempo vamos chegar',", r"'em quanto tempo vamos chegar',", ('p3c',)),
    ('a chegada perde «já chegamos» e «estamos chegando»', r"    'ja chegamos', 'estamos chegando'];", r"    ];", ('p3c',)),
    ('a chegada perde «falta muito» («falta muito para chegar?»)', r"'o que falta para', 'falta muito'];", r"'o que falta para'];", ('p3c',)),
    ('a chegada perde «base» e «marina» («quanto falta pra base?»)', r"var FALTA_JUNTO = ['chegar', 'chegada', 'destino', 'waypoint', 'ponto', ' eta ', ' base ', ' marina '];", r"var FALTA_JUNTO = ['chegar', 'chegada', 'destino', 'waypoint', 'ponto', ' eta '];", ('p3c',)),
    ('a chegada perde «quantas milhas já navegamos»', r"'quantas milhas ja naveg', 'quantas milhas ja percorr', ", r"", ('p3c',)),
    ('a chegada dá a de outro ponto como se fosse a do citado («quanto falta para o Estaleirinho?»)', r"        else if (nc(cit) !== nc(q.destino)) outro = cit; }", r"        }", ('p3c',)),
    ('o próximo ponto citado vira «não é o destino nem o próximo ponto»', r"if (nc(cit) === nc(q.wp_proximo) && nc(cit) !== nc(q.destino)) wp = true;", r"", ('p3c',)),
    ('a chegada em outro ponto perde a explicação (só destino e próximo ponto)', r"+ '\nO app calcula a chegada só no destino e no próximo ponto da rota.'", r"", ('p3c',)),
    # —— a profundidade no jeito de bordo ——
    ('a profundidade perde «quanto de fundo», «qual o fundo», «fundo» e «sonda»', r"'agua sob', 'de fundo tem', 'quanto de fundo', 'qual o fundo', ' fundo ', ' sonda '];", r"'agua sob'];", ('p3c',)),
    ('a profundidade perde «fundo» e «sonda» sozinhos', r"'qual o fundo', ' fundo ', ' sonda '];", r"'qual o fundo'];", ('p3c',)),
    ('a profundidade perde «tem pouco fundo?»', r"|| POUCO_FUNDO.test(q); }", r"; }", ('p3c',)),
    ('a profundidade pega a válvula de fundo (a lista neutra aceita «feche», «válvula»)', r"neste nesse momento ponto local lugar metros", r"neste nesse momento ponto local lugar metros feche valvula do casco", ('p3c',)),
    # —— as horas que faltam ——
    ('«quanto falta para a troca de óleo?» perde a 1ª linha com as horas que faltam', r"l1 = has(pad(qq || ''), FALTA_PALAVRAS) ? linhaFalta(o, 'a troca de óleo e filtros dos motores') : ''", r"l1 = ''", ('p3c',)),
    ('«quanto falta para a revisão do gerador?» perde a 1ª linha com as horas que faltam', r"has(sq, ['revisao', 'oleo', 'filtro', 'troca', 'horas']) ? linhaFalta(rv, 'a revisão de óleo e filtros do gerador') : ''", r"has(sq, ['revisao', 'oleo', 'filtro', 'troca', 'horas']) ? '' : ''", ('p3c',)),
    ('as horas que faltam perdem a data (o que vier antes)', r"(t.vence ? ' ou até ' + t.vence + ', o que vier antes' : '')", r"''", ('p3c',)),
    ('as horas que faltam perdem o limite', r"' h para ' + nome + ' (limite de ' + mil(t.horas.limite) + ' h)'", r"' h para ' + nome", ('p3c',)),
    # —— o vento a bordo ——
    ('«o vento a bordo agora» perde a 1ª linha do quadro (a previsão primeiro)', r"lv = linhasVento(qq, i);", r"lv = '';", ('p3c',)),
    ('o relato «o vento está forte agora» vira o vento do quadro (sem a lista branca)', r" || !leitura(sq, NEUTRAS_BASE + VENTO_OK_P)) return '';", r") return '';", ('p3c',)),
    ('«vento aparente» perde o aparente na 1ª linha', r"if (ap && t.ventoAp) return 'A bordo agora, vento aparente '", r"if (false) return 'A bordo agora, vento aparente '", ('p3c',)),
    ('«verdadeiro ou aparente» perde o par na 1ª linha', r"if (ap && vd && t.ventoAp) return", r"if (false) return", ('p3c',)),
    # —— posição, ondas e navegação no jeito de bordo ——
    ('a posição perde «em que rumo estamos?»', r"var POSICAO_OK = NEUTRAS_BASE + 'que estamos onde", r"var POSICAO_OK = NEUTRAS_BASE + 'estamos onde", ('p3c',)),
    ('as ondas perdem «tem onda?»', r"var ONDAS_PALAVRAS = [' ondas ', ' onda ', 'ondulacao',", r"var ONDAS_PALAVRAS = [' ondas ', 'ondulacao',", ('p3c',)),
    ('a navegação perde «como estamos indo?»', r"(?:estamos|vamos|estao as coisas|esta tudo)(?: indo)?(?: agora|", r"(?:estamos|vamos|estao as coisas|esta tudo)(?: agora|", ('p3c',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3C_REV4


# Mutantes da P3D (ficha, semCoord, TERMOS): cada um tem de ser acusado pelo grupo indicado
MUTANTES_3D = [
    # —— a ficha ——
    ('a ficha perde o «## Navegação agora»', r"      bloco('Navegação agora', navegacaoAgora);", r"", ('ficha',)),
    ('a ficha põe a «## Emergência» depois do «Sobre o app» (fora do 3º lugar)', r"""      out.push('## Emergência\nAbrir o SOS do app. ' + SOS_FICHA + '\n(' + FT.proto + ')');
    }
    out.push('## Sobre o app\n' + sobreApp().join('\n'));""", r"""    }
    out.push('## Sobre o app\n' + sobreApp().join('\n'));
    if (!resumida) out.push('## Emergência\nAbrir o SOS do app. ' + SOS_FICHA + '\n(' + FT.proto + ')');""", ('ficha',)),
    ('a ficha perde a «## Emergência»', r"""      out.push('## Emergência\nAbrir o SOS do app. ' + SOS_FICHA + '\n(' + FT.proto + ')');
    }""", r"""    }""", ('ficha',)),
    ('a navegação perde a tendência dos últimos 30 s', r"t.tend ? 'tendência — ' + t.tend : '']);", r"'']);", ('ficha',)),
    ('a navegação perde os alarmes', r"junta([t.alarmes ? 'alarmes: ' + t.alarmes : '', t.tend", r"junta(['', t.tend", ('ficha',)),
    ('a navegação perde a fase', r"f ? 'fase ' + f : '']);", r"'']);", ('ficha',)),
    ('a navegação escreve o rumo sem o COG', r"un('rumo (COG)', t.rumo)", r"un('rumo', t.rumo)", ('ficha',)),
    ('a navegação perde a posição relativa', r"un('piloto', t.piloto), un('leme', t.leme), t.relativa, un('destino'", r"un('piloto', t.piloto), un('leme', t.leme), un('destino'", ('ficha',)),
    ('a navegação perde o consumo e o diesel', r"junta([un('consumo', t.consumo), un('diesel', t.diesel),", r"junta([", ('ficha',)),
    ('a navegação perde os motores (rpm, óleo, arrefecimento, carga)', r"junta([un('motores', t.rpm), un('óleo', t.oleo)", r"junta([un('óleo', t.oleo)", ('ficha',)),
    ('a navegação perde a profundidade, o vento e o mar', r"junta([un('profundidade', t.prof), t.vento ? 'vento a bordo agora ' + t.vento : '', un('vento aparente a bordo agora', t.ventoAp), un('ondas a bordo agora', t.ondas), un('água do mar a bordo agora', t.agua),", r"junta([", ('ficha',)),
    ('a navegação escreve o vento sem o «a bordo agora»', r"t.vento ? 'vento a bordo agora ' + t.vento : ''", r"t.vento ? 'vento ' + t.vento : ''", ('ficha',)),
    ('a ficha resumida perde a linha de navegação', r"    if (resumida) bloco('Navegação agora', linhaNavegacao);", r"", ('ficha',)),
    ('a ficha resumida leva a navegação inteira (passa de 4.000 letras)', r"    if (resumida) bloco('Navegação agora', linhaNavegacao);", r"    if (resumida) bloco('Navegação agora', navegacaoAgora);", ('ficha',)),
    ('a ficha de emergência leva a navegação (a guarda esquece o bloco novo)', r"var QUADRO = { 'Telemetria': 1, 'Navegação agora': 1, 'Horímetros': 1, 'Autonomia e consumo': 1 };", r"var QUADRO = { 'Telemetria': 1, 'Horímetros': 1, 'Autonomia e consumo': 1 };", ('ficha', 'emerg')),
    ('a ficha volta a levar o selo e o aviso da flag antiga', r"out.push('## Agora\n' + agoraBR() + ' · usuário: ' + quem());", r"out.push('## Agora\n' + agoraBR() + ' · usuário: ' + quem() + (D.demo ? '\n' + (D.selo || 'DEMO') + ': ' + (D.aviso || '') : ''));", ('ficha',)),
    ('a ficha do modo real leva as linhas com sim: true (semSim sempre falso)', r"semSim = !EM_SOS && D.simulacao === false;", r"semSim = false;", ('ficha',)),
    ('a ficha da simulação tira as linhas com sim: true (o filtro sempre ligado)', r"return ctx && ctx.semSim ? v.filter(function (e) { return e.sim !== true; }) : v; }", r"return v.filter(function (e) { return e.sim !== true; }); }", ('ficha',)),
    ('o registro perde as linhas sim: true ao gravar (o addDiario relê o diário filtrado)', r"function addDiario1(e) { var n = now(); var list = loadDiario();", r"function addDiario1(e) { var n = now(); var list = lerDiario({ semSim: D.simulacao === false });", ('ficha',)),
    ('o teto da ficha fica nos 12.000 do cliente (a ficha com a previsão e a maré passa de 11.500: a decisão (i) manda 16.000)', r"var FICHA_MAX = 16000;", r"var FICHA_MAX = 12000;", ('ficha',)),
    ('o teto da ficha cai abaixo da ficha (8.000)', r"var FICHA_MAX = 16000;", r"var FICHA_MAX = 8000;", ('ficha',)),
    ('o cérebro não exporta o teto da ficha', r"FICHA_MAX: FICHA_MAX,", r"", ('ficha',)),
    ('a ficha completa não é cortada pela fala do sos (a resposta de emergência sem a guarda do EMERG)', r"function emerg(a) { return !!a && typeof a === 'object' && (EMERG[a.key] === 1 || (a.key === 'faqEquip' && a.emerg === true)); }", r"function emerg(a) { return false; }", ('ficha', 'emerg')),   # (P3E, F10: o emerg() ganhou o cartão EM do FAQ; mesma mutação, texto novo)
    # —— semCoord (§2.8) ——
    ('o semCoord não tira nada', r"function semCoord(s) { return String(s || '').replace(COORD_RX, SEM_COORD).replace(SEM_COORD_PAR, SEM_COORD); }", r"function semCoord(s) { return String(s || ''); }", ('semcoord', 'ficha')),
    ('o semCoord perde o decimal de 4 casas (-26.9931)', r"|-?\d{1,3}[.,]\d{4,}(?!\d)|-?\d{1,3}[.,]\d{3,}\s*[;\/]", r"|-?\d{1,3}[.,]\d{3,}\s*[;\/]", ('semcoord',)),
    ('o semCoord perde o par com barra (-26,993 / -48,614)', r"|-?\d{1,3}[.,]\d{3,}\s*[;\/]\s*-?\d{1,3}[.,]\d{3,}|-\d{1,3}", r"|-\d{1,3}", ('semcoord',)),
    ('o semCoord perde o par de CSV (-26.993,-48.614)', r"|-\d{1,3}[.,]\d{3,}\s*,\s*-?\d{1,3}[.,]\d{3,}/g;", r"/g;", ('semcoord',)),
    ('o semCoord perde o graus-minutos com ponto (26°59.6\')', r"\s*[°º]\s*\d{1,2}\s*[,.]\s*\d+\s*['′’]?\s*[NSEWLO]?|", r"\s*[°º]\s*\d{1,2}\s*[,]\s*\d+\s*['′’]?\s*[NSEWLO]?|", ('semcoord',)),
    ('o semCoord perde os segundos (26°59\'35"S)', r"""(?:[NSEWLO]|\d{1,2}(?:[,.]\d+)?\s*(?:["″”]|''|’’))""", r"""(?:[NSEWLO])""", ('semcoord',)),
    ('o semCoord toma o milhar do pt-BR por coordenada (3 casas no lugar de 4)', r"|-?\d{1,3}[.,]\d{4,}(?!\d)|", r"|-?\d{1,3}[.,]\d{3,}(?!\d)|", ('semcoord', 'ficha')),
    ('o semCoord deixa duas avisos para o par (sem juntar)', r".replace(COORD_RX, SEM_COORD).replace(SEM_COORD_PAR, SEM_COORD); }", r".replace(COORD_RX, SEM_COORD); }", ('semcoord',)),
    ('o cérebro não exporta o semCoord', r"semCoord: semCoord, TERMOS: TERMOS,", r"TERMOS: TERMOS,", ('semcoord',)),
    # —— TERMOS (§3) ——
    ('o cérebro não exporta o TERMOS', r"TERMOS: TERMOS, TERMOS_FONTES: TERMOS_FONTES,", r"TERMOS_FONTES: TERMOS_FONTES,", ('termos',)),
    ('o cérebro não exporta as fontes do TERMOS', r"TERMOS: TERMOS, TERMOS_FONTES: TERMOS_FONTES,", r"TERMOS: TERMOS,", ('termos',)),
    ('o ROTULOS ganha a flag i (pegaria o id demo)', r"\\bMANUAL NO DRIVE\\b|\\bDEMO\\b', flags: '' }", r"\\bMANUAL NO DRIVE\\b|\\bDEMO\\b', flags: 'i' }", ('termos',)),
    ('a AUTENTICIDADE perde a flag i', r"demo)(?![A-Za-zÀ-ÿ])', flags: 'i' }", r"demo)(?![A-Za-zÀ-ÿ])', flags: '' }", ('termos',)),
    ('o VAZIOS perde o «A CADASTRAR»', r"cadastrad)|A CADASTRAR|(?:^|", r"cadastrad)|(?:^|", ('termos',)),
    ('o ROTULOS perde o «SEM LEITURA»', r"\\bSEM (?:DADOS|LEITURA)\\b", r"\\bSEM (?:DADOS)\\b", ('termos',)),
    ('o DINHEIRO perde o «R$»', r"src: 'R\\$\\s?\\d|US\\$", r"src: 'XR\\$\\s?\\d|US\\$", ('termos',)),
    ('o cérebro usa um lookbehind', r"  var TERMOS = {};", r"  var TERMOS = {}; var LB = new RegExp('(?<=a)b');", ('termos',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3D


# Mutantes da P3D (voz: F32, hora na fala, trava, F31): cada um tem de ser acusado pelo grupo voz
MUTANTES_3D_VOZ = [
    # —— F32: as siglas ——
    ('o EPIRB volta a ser soletrado', r"['EPIRB', 'épirbi'], ", r"", ('voz',)),
    ('o MOB volta a «homem ao mar»', r"['MOB', 'móbi']", r"['MOB', 'homem ao mar']", ('voz',)),
    ('o NMEA volta a ser soletrado', r"['NMEA', 'nêmea'], ", r"", ('voz',)),
    ('o ETA fica solto', r"['ETA', 'chegada prevista'],", r"", ('voz',)),
    ('o STW, o TWS, o TWA e o TWD ficam soltos', r"['STW', 'velocidade na água'], ['TWS', 'velocidade do vento verdadeiro'], ['TWA', 'ângulo do vento verdadeiro'], ['TWD', 'direção do vento verdadeiro'],", r"", ('voz',)),
    ('o AWA, o AWS, o HDG e o DPT ficam soltos', r"['AWA', 'ângulo do vento aparente'], ['AWS', 'velocidade do vento aparente'], ['HDG', 'proa'], ['DPT', 'profundidade'],", r"", ('voz',)),
    ('o kt e o kn ficam soltos', r"['KTS?|kts?|kn', 'nós'], ", r"", ('voz',)),
    ('o hPa, o kPa e o rpm sem número ficam soltos', r"['hPa', 'hectopascal'], ['kPa', 'quilopascal'], ['rpm', 'rotações por minuto'],", r"", ('voz',)),
    ('o menos do quadro (−0,5) é lido como traço', r"[/−(?=\d)/g, 'menos '],", r"", ('voz',)),
    # —— a hora com segundos ——
    ('a hora com segundos não é lida (12:01:05 fica "12:01:05")', r"(\d{1,2}):(\d{2}):(\d{2})(?!\d|:\d|\.\d)/g, function (m, a, h, mi, se) {", r"(\d{1,2}):(\d{2}):(\d{2})x(?!\d|:\d|\.\d)/g, function (m, a, h, mi, se) {", ('voz',)),
    ('a hora com segundos não é lida quando vem seguida de «:» («Motores às 12:01:00: …»)', r"(\d{1,2}):(\d{2}):(\d{2})(?!\d|:\d|\.\d)/g, function (m, a, h, mi, se) {", r"(\d{1,2}):(\d{2}):(\d{2})(?![\d:]|\.\d)/g, function (m, a, h, mi, se) {", ('voz',)),
    ('os segundos saem da hora lida', r"      if (se) p.push(se + (se === 1 ? ' segundo' : ' segundos'));", r"", ('voz',)),
    ('a hora depois do travessão não ganha o «às»', r"    s = s.replace(/ [—–] (\d{1,2}:\d{2}(?::\d{2})?)(?![\d:])/g, ', às $1');", r"", ('voz',)),
    # —— a hora na fala ——
    ('a fala não ganha a hora do instante', r"return String(t).replace(/[\s.;:,]+$/, '') + '. Às ' + h + '.';", r"return t;", ('voz',)),
    ('a hora vai sempre no fim da fala (nunca na abertura da lista)', r"    if (k > 0 && k < 140) return t.slice(0, k) + ', às ' + h + t.slice(k);", r"", ('voz',)),
    ('a fala ganha a hora do relógio de agora (não a do instante da resposta)', r"var h = a && typeof a === 'object' && typeof a.hora === 'string' ? a.hora : '';", r"var h = instante() ? instante().hora : '';", ('voz',)),
    ('a resposta não leva a hora do instante (a cópia da tela perde a fala com hora)', r"if (a && typeof a === 'object' && !emerg(a) && sim() && vivo()) a.hora = vivo().hora;", r"", ('voz',)),
    ('a resposta de emergência leva a hora do instante', r"if (a && typeof a === 'object' && !emerg(a) && sim() && vivo()) a.hora = vivo().hora;", r"if (a && typeof a === 'object' && sim() && vivo()) a.hora = vivo().hora;", ('voz', 'emerg')),
    ('a fala da resposta do tempo e da maré ganha a hora do instante', r"var FALA_SEM_HORA = { clima: 1, contatos: 1,", r"var FALA_SEM_HORA = { contatos: 1,", ('voz',)),
    ('a fala de uma chave do cadastro (áudio, guias) ganha a hora', r"base: 1, faqEquip: 1, audio: 1, manual: 1, ia: 1,", r"base: 1, faqEquip: 1, ia: 1,", ('voz',)),   # (P3E, F10: a lista ganhou o 'faqEquip'; mesma mutação, texto novo)
    ('a fala do diagnóstico e da saudação ganha a hora do instante', r"|| SEM_HORA_NA_FONTE[a.key] || FALA_SEM_HORA[a.key]", r"|| FALA_SEM_HORA[a.key]", ('voz',)),
    ('a hora entra duas vezes na fala (sem olhar se a frase já a diz)', r"|| !t || /\d\d:\d\d:\d\d/.test(t)) return t;", r"|| !t) return t;", ('voz',)),
    # —— a trava de voz ——
    ('a trava de voz não troca nada', """    if (!sim()) return s;
    for (n = 0; n < 4; n++) {""", """    return s;
    for (n = 0; n < 4; n++) {""", ('voz',)),
    ('a trava de voz age também sem a simulação', """    if (!sim()) return s;
    for (n = 0; n < 4; n++) {""", """    for (n = 0; n < 4; n++) {""", ('voz',)),
    ('a trava de voz não troca os ROTULOS', r"function (m) { return /^SEM/.test(m) ? 'sem informação' : /^MANUAL/.test(m) ? 'no guia de bordo' : VOZ_NEUTRO; }],", r"function (m) { return m; }],", ('voz',)),
    ('a trava de voz tira o SEM DADOS em vez de trocar por «sem informação»', r"return /^SEM/.test(m) ? 'sem informação' :", r"return /^SEM/.test(m) ? '' :", ('voz',)),
    ('a trava de voz não troca a AUTENTICIDADE', r"'g' + TERMOS_FONTES.AUTENTICIDADE.flags), neutraAutenticidade]];", r"'g' + TERMOS_FONTES.AUTENTICIDADE.flags), function (m) { return m; }]];", ('voz',)),
    ('a trava de voz suprime o termo (troca por nada) em vez de trocar', r"'g' + TERMOS_FONTES.AUTENTICIDADE.flags), neutraAutenticidade]];", r"'g' + TERMOS_FONTES.AUTENTICIDADE.flags), function (m) { return ''; }]];", ('voz',)),
    ('a trava de voz também filtra as chaves de FALA_INTEIRA', """    if (a && typeof a === 'object' && a.key && FALA_INTEIRA[a.key] === 1) return t;
    return travaVoz(""", """    return travaVoz(""", ('voz',)),
    ('a trava de voz não repete a troca (um termo novo nascido da troca fica)', r"    for (n = 0; n < 4; n++) {", r"    for (n = 0; n < 1; n++) {", ('voz',)),
    # a palavra inteira, o substantivo e o caractere de antes do termo ficam (a P3D deixava «dado de bordoos»)
    ('a trava troca só o radical do adjetivo (o resto da palavra fica colado: «bordoos»)', r"AUTENTICIDADE.src + ')[' + VOZ_LET + ']*(?:\\s*(?:,|e|ou)", r"AUTENTICIDADE.src + ')(?:\\s*(?:,|e|ou)", ('voz',)),
    ('a trava come o substantivo (a troca vale para o casamento todo: «dado de bordo»)', r"    return ini + (x ? r.slice(0, x.index) : '') + VOZ_NEUTRO;", r"    return ini + VOZ_NEUTRO;", ('voz',)),
    ('a trava come o caractere que antecede o termo (o espaço: «Osdados»)', r"    ini = /^[^A-Za-zÀ-ÿ]/.test(m) ? m.charAt(0) : ''; r = m.slice(ini.length);", r"    ini = ''; r = m.slice(/^[^A-Za-zÀ-ÿ]/.test(m) ? 1 : 0);", ('voz',)),
    ('a trava come o verbo de «é uma simulação» («Isto de bordo»)', r"(?:simula|demonstra)[çc][ãa]o$/i.exec(r))) return ini + x[1] + ' ' + VOZ_NEUTRO;", r"(?:simula|demonstra)[çc][ãa]o$/i.exec(r))) return ini + VOZ_NEUTRO;", ('voz',)),
    ('a trava apaga a negação inteira (o ramo «não é/são …» some: «não são reais» vira só «de bordo»)', r"    if ((x = /^(n[ãa]o) (é|são) /i.exec(r))) return ini + x[1] + ' ' + x[2] + ' ' + VOZ_NEUTRO;", r"", ('voz',)),
    ('a trava troca «na demonstração» por «de bordo» (a preposição vira a mesma)', r"vozMaiuscula(/^da$/i.test(x[1]) ? VOZ_NEUTRO : 'a bordo', x[1])", r"vozMaiuscula(VOZ_NEUTRO, x[1])", ('voz',)),
    ('a trava perde a maiúscula do começo da frase («a bordo»)', r"return ini + vozMaiuscula(/^da$/i.test(x[1]) ? VOZ_NEUTRO : 'a bordo', x[1]);", r"return ini + (/^da$/i.test(x[1]) ? VOZ_NEUTRO : 'a bordo');", ('voz',)),
    ('a trava não troca o «modo demo» pelo «modo de bordo» (o termo fica sem o «modo»)', r"return ini + r.slice(0, 4) + ' ' + VOZ_NEUTRO;", r"return ini + VOZ_NEUTRO;", ('voz',)),
    ('a trava deixa o parêntese solto no «(demonstração)»', r"    if (/^\(demonstra/i.test(m)) return VOZ_NEUTRO;", r"", ('voz',)),
    ('a trava não junta os adjetivos coordenados («fictícios e simulados»: o 2º fica)', r"AUTENTICIDADE.src + ')[' + VOZ_LET + ']*(?:\\s*(?:,|e|ou)\\s+' + VOZ_ADJ + ')*'", r"AUTENTICIDADE.src + ')[' + VOZ_LET + ']*'", ('voz',)),
    ('a trava não junta «de bordo de bordo»', r"    return s === orig ? s : s.replace(/\bde bordo(?:\s+(?:e\s+)?de bordo)+/gi, VOZ_NEUTRO);", r"    return s;", ('voz',)),
    ('a trava troca «de teste» sem o «dados»', r"    if ((x = /^(dados) de teste$/i.exec(r))) return ini + x[1] + ' ' + VOZ_NEUTRO;", r"", ('voz',)),
    ('o cérebro não exporta a trava de voz', r"falaCurta: falaCurta, travaVoz: travaVoz,", r"falaCurta: falaCurta,", ('voz',)),
    # —— F31: o ditado ——
    ('o ditado não corrige o nome do equipamento', r"function atual() { return corrigeVoz((texto + ' ' + sessao).replace(/\s+/g, ' ').trim()); }", r"function atual() { return (texto + ' ' + sessao).replace(/\s+/g, ' ').trim(); }", ('voz',)),
    ('o answer() não corrige o nome do equipamento', r"var q1 = corrigeVoz(q),", r"var q1 = q,", ('voz',)),
    ('o nome certo é fixo no cérebro («Seakeeper»), não o do cadastro', r"String(e.fabricante).split(' ')[0] : '')", r"'Seakeeper' : '')", ('voz',)),
    ('a tabela ignora qual é o equipamento (pega o 1º do cadastro)', r"return y && y.id === x.id; })[0]", r"return !!y; })[0]", ('voz',)),
    ('a correção vale também no SOS (lê o D.equipamentos)', r"if (!s || EM_SOS) return s;", r"if (!s) return s;", ('voz',)),
    ('a correção de «estabilizador skip» sai da tabela', r"    { id: 'estabilizador', marca: 'seakeeper', mantem: '(?:estabilizador|giroestabilizador)\\s+', v: 'skip|ski|squip' },", r"", ('voz',)),
    ('a linha de marca vale com OUTRO fabricante no cadastro (sem a guarda da marca: «cummins» vira «Volvo»)', r"if (e && nome && (!x.marca || norm(nome) === x.marca)) s = s.replace(", r"if (e && nome) s = s.replace(", ('voz',)),
    ('a linha do «estabilizador skip» perde a marca (vale com outro fabricante: «estabilizador Gyromax»)', r"{ id: 'estabilizador', marca: 'seakeeper', mantem:", r"{ id: 'estabilizador', mantem:", ('voz',)),
    ('a tabela do motor perde o nome certo («cummins» em maiúsculas não vira «Cummins»)', r"v: 'kamins|camins|comins|cumins|cumis|cummins' }", r"v: 'kamins|camins|comins|cumins|cumis' }", ('voz',)),
    ('a correção pega pedaço de palavra («sikerinho»)', r"'(?:' + x.v + ')(?![' + LET + '\\d])', 'gi');", r"'(?:' + x.v + ')', 'gi');", ('voz',)),
    ('a correção do EPIRB usa o fabricante (não o nome do sistema)', r"{ id: 'epirb', v: 'ipirb|ipirbi|epirbe|epirbi|e pirb|epirb', nome: 'EPIRB' },", r"{ id: 'epirb', v: 'ipirb|ipirbi|epirbe|epirbi|e pirb|epirb' },", ('voz',)),
    ('o cérebro não exporta a correção do ditado', r"travaVoz: travaVoz, corrigeVoz: corrigeVoz,", r"travaVoz: travaVoz,", ('voz',)),
    # —— F31: a fala que só diz o equipamento continua a pergunta anterior ——
    ('a fala que só diz o equipamento nunca continua', """    return CONV.q + ' — ' + String(q).trim();
  }""", """    return null;
  }""", ('voz',)),
    ('a continuação vale para sempre (sem os 10 min)', r"|| Date.now() - CONV.t > CONV_VALE ||", r"||", ('voz',)),
    ('a continuação vale sem a pergunta na resposta anterior', r"if (EM_SOS || !CONV.q || !CONV.pergunta ||", r"if (EM_SOS || !CONV.q ||", ('voz',)),
    ('a continuação pega fala com conteúdo («o gerador está desligado»)', r"|| !soNomeia(n) || emergencia(n)", r"|| emergencia(n)", ('voz',)),
    ('a continuação vale com o app sem gravar (commit false)', r"(ctx && (ctx.id || ctx.commit === false))) return null;", r"(ctx && ctx.id)) return null;", ('voz',)),
    ('a continuação vale depois de uma emergência (a pergunta de emergência nunca é emergência para o contexto)', r"function perguntaEmerg(q) { var n = pad(q); return !!(emergencia(n) || oleo(n) === 1 || EMERG[route(q)] === 1); }", r"function perguntaEmerg(q) { return false; }", ('voz',)),
    ('a pergunta do EPIRB, do Seafire e do canal 16 não é emergência para o contexto (só a lista SOS e o óleo)', r"|| oleo(n) === 1 || EMERG[route(q)] === 1); }", r"|| oleo(n) === 1); }", ('voz',)),
    ('a resposta de emergência não encerra o contexto de antes (a CONV da pergunta anterior fica)', """        if (emerg(a)) limpaConversa();
        else if (!ctx || ctx.commit !== false) CONV = {""", """        if (!emerg(a) && (!ctx || ctx.commit !== false)) CONV = {""", ('voz',)),
    ('a continuação vale com a correção («não, o gerador»)', r"/^ (?:e|nao)(?= )/.test(n) ||", r"", ('voz',)),
    ('a continuação vale depois do NOVA (o limpaConversa não zera)', r"function limpaConversa() { CONV = { q: '', a: '', t: 0, pergunta: false, n: (CONV.n || 0) + 1 }; }", r"function limpaConversa() { }", ('voz',)),
    ('a continuação pega a pergunta («o gerador?»)', r"|| /\?\s*$/.test(String(q)) ||", r"||", ('voz',)),
    ('o cérebro não exporta o contexto da conversa', r"corrigeVoz: corrigeVoz, conversa: conversa, limpaConversa: limpaConversa,", r"corrigeVoz: corrigeVoz,", ('voz',)),
    # —— revisão: a hora seguida de «:» de pontuação e o +55 da tendência ——
    ('a hora seguida de «:» de pontuação não é lida («desde as 07:00: 65 milhas» fica com "07:00:")', r"(?:min(?![A-Za-z]))?(?!\d|:\d|\.\d)/g, function (m, a, h, mi) {", r"(?:min(?![A-Za-z]))?(?![\d:]|\.\d)/g, function (m, a, h, mi) {", ('voz',)),
    ('a relação 3:00:15:20 é lida como hora (o «:» seguido de dígito deixa de proteger)', r"(?:min(?![A-Za-z]))?(?!\d|:\d|\.\d)/g, function (m, a, h, mi) {", r"(?:min(?![A-Za-z]))?(?!\d|\.\d)/g, function (m, a, h, mi) {", ('voz',)),
    ('o +551 da tendência sai sem o espaço fino (o prefixo de telefone +55 da PESSOAIS)', r"'+' + (/^55\d/.test(n) ? '\u2009' : '')", r"'+' + ''", ('termos',)),
    ('a tendência põe o espaço fino depois de TODO + (o +644 do contrato muda)', r"'+' + (/^55\d/.test(n) ? '\u2009' : '')", r"'+\u2009'", ('termos', 'forma')),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3D_VOZ


# Mutantes da revisão da P3D: o semCoord FINAL da ficha, cada item da linha da resumida, o «a bordo agora» do vento aparente, das ondas e da água do mar, a execução com `sim: true` e a negação da trava de voz
MUTANTES_3D_REV = [
    # —— o semCoord final (o único filtro de «## Agora», «## Sobre o app», «## Embarcação», «## Equipamentos», «## Emergência» e da «## Ficha resumida») ——
    ('a ficha completa perde o semCoord final (a coordenada do cadastro vaza em «## Embarcação» e «## Equipamentos»)', r"""    return semCoord(out.join('\n\n'));
  }

  // Anexos""", r"""    return out.join('\n\n');
  }

  // Anexos""", ('ficha',)),
    ('a ficha resumida perde o semCoord final (a coordenada do cadastro vaza em «## Embarcação»)', r"""      return semCoord(out.join('\n\n'));
    }
    bloco('Telemetria'""", r"""      return out.join('\n\n');
    }
    bloco('Telemetria'""", ('ficha',)),
    # —— a linha única da ficha resumida: cada item que o título promete ——
    ('a linha da resumida perde os alarmes', r"t.alarmes ? 'alarmes: ' + t.alarmes : ''].filter(Boolean).join(' · ');", r"''].filter(Boolean).join(' · ');", ('ficha',)),
    ('a linha da resumida perde o rumo (COG)', r"t.rumo ? 'rumo (COG) ' + t.rumo : '', t.relativa || '',", r"t.relativa || '',", ('ficha',)),
    ('a linha da resumida perde a posição relativa à rota', r"t.rumo ? 'rumo (COG) ' + t.rumo : '', t.relativa || '',", r"t.rumo ? 'rumo (COG) ' + t.rumo : '',", ('ficha',)),
    ('a linha da resumida perde o rótulo «motores»', r"t.rpm ? 'motores ' + t.rpm : '',", r"t.rpm ? t.rpm : '',", ('ficha',)),
    ('a linha da resumida perde o SOG', r"t.sog ? 'SOG ' + t.sog : '', t.rumo", r"t.rumo", ('ficha',)),
    # —— vento aparente, ondas e água do mar do quadro: «a bordo agora» (decisão 12) ——
    ('a navegação escreve o vento aparente sem o «a bordo agora»', r"un('vento aparente a bordo agora', t.ventoAp)", r"un('vento aparente', t.ventoAp)", ('ficha',)),
    ('a navegação escreve as ondas sem o «a bordo agora»', r"un('ondas a bordo agora', t.ondas)", r"un('ondas', t.ondas)", ('ficha',)),
    ('a navegação escreve a água do mar sem o «a bordo agora»', r"un('água do mar a bordo agora', t.agua)", r"un('água do mar', t.agua)", ('ficha',)),
    # —— a execução com `sim: true` fora da ficha com simulacao false ——
    ('a ficha do modo real conta a execução com `sim: true` (a visão da execução ignora a flag)', r"if (!EXEC_SEM_SIM) return m; var r = {};", r"return m; var r = {};", ('ficha',)),
    ('a ficha nunca liga o filtro da execução', r"    EXEC_SEM_SIM = semSim;   // a execução", r"    // a execução", ('ficha',)),
    ('a ficha tira a execução com `sim: true` também com a simulação ligada (o filtro sempre ligado)', r"    EXEC_SEM_SIM = semSim;   // a execução", r"    EXEC_SEM_SIM = true;   // a execução", ('ficha',)),
    ('a ficha deixa o filtro da execução ligado depois (vaza para a resposta da tela)', r"finally { EXEC_SEM_SIM = false; } }", r"finally { } }", ('ficha',)),
    ('a agenda lê o mapa cru da execução (a ficha do modo real esconde a tarefa executada com sim)', r"function agenda() { var ex = execVisivel();", r"function agenda() { var ex = loadExec();", ('ficha',)),
    ('o texto «executada em …» lê o mapa cru (os «## Horímetros» do modo real dizem «executada» com sim)', r"var f = t && execVisivel()[t.id];", r"var f = t && loadExec()[t.id];", ('ficha',)),
    ('a linha do óleo da «## Manutenção» lê o mapa cru', r"oleoM && oleoM.horas && !execVisivel()[oleoM.id] ?", r"oleoM && oleoM.horas && !loadExec()[oleoM.id] ?", ('ficha',)),
    ('a visão da execução tira também a execução sem `sim` (o filtro pega tudo)', r"if (!m[k] || m[k].sim !== true) r[k] = m[k];", r"if (!m[k]) r[k] = m[k];", ('ficha',)),
    # —— a trava de voz mantém a negação ——
    ('a trava tira o «não» de «não é verdadeira» (afirma o contrário: «a leitura é de bordo»)', r"return ini + x[1] + ' ' + x[2] + ' ' + VOZ_NEUTRO;   // a negação FICA", r"return ini + x[2] + ' ' + VOZ_NEUTRO;   // a negação FICA", ('voz',)),
    ('a trava perde a maiúscula do «Não» (a frase começa em minúscula)', r"return ini + x[1] + ' ' + x[2] + ' ' + VOZ_NEUTRO;   // a negação FICA", r"return ini + 'não ' + x[2] + ' ' + VOZ_NEUTRO;   // a negação FICA", ('voz',)),
    ('a trava troca «não é verdadeira» por «não é» (sem o predicado «de bordo»)', r"return ini + x[1] + ' ' + x[2] + ' ' + VOZ_NEUTRO;   // a negação FICA", r"return ini + x[1] + ' ' + x[2];   // a negação FICA", ('voz',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3D_REV

# ——————————————— Fase 3, P3E: checklists (F09), FAQ (F10), tendências (F11) e peças (F22) ———————————————
# (PARIDADE F09, F10, F11, F22; CONTRATO §1.6, §1.13, §1.18, §1.20, §1.25.) Só o cérebro: as telas C4, F6 e a aba de peças são da Fase 4. Nenhum texto escrito aqui repete um número do dado:
# o esperado sai do instante (i.q, i.calc, i.tend) e do cadastro (D.checklists, D.pecas, D.agenda), como nos grupos da P3C.

# —— F11: as tendências ——
ROTAS_P3E_F11 = [
    ('quais as tendências?', 'preditiva', False), ('análise preditiva', 'preditiva', False), ('tendências dos motores', 'preditiva', False), ('qual a tendência do óleo?', 'preditiva', False),
    ('qual a tendência da pressão de óleo?', 'preditiva', False), ('tendência do arrefecimento', 'preditiva', False), ('as baterias estão perdendo capacidade?', 'preditiva', False),
    ('tem alguma tendência de queda nas baterias?', 'preditiva', False), ('recomendação da IA', 'preditiva', False), ('capitão, quais as tendências?', 'preditiva', False), ('tem alguma tendência?', 'preditiva', False),
    ('quais as tendências do motor BE?', 'preditiva', False), ('tendência da temperatura do motor BE', 'preditiva', False), ('tendências da bateria de partida', 'preditiva', False),
    ('tendência de horas até a revisão', 'preditiva', False), ('quais são as tendências da manutenção', 'preditiva', False), ('tendência do gerador', 'preditiva', False),
    # o que ela não pode roubar: o relato de queda do óleo (segurança, em `oleo`), o vento, a maré, a pressão barométrica, o consumo e o dinheiro seguem as suas rotas
    ('a pressão do óleo está caindo, qual a tendência?', 'oleo', False), ('qual a tendência do vento?', 'clima', False), ('tendência da maré', 'mare', False),
    ('tendência da pressão barométrica', 'fallback', True), ('qual a tendência de consumo?', 'consumo', False), ('tendência do dólar', 'foraBarco', False),
    # (revisão) a trava 10: o pedido de socorro, a salvatagem, o EPIRB, o Seafire, o canal 16 e o MMSI com a palavra «tendência» seguem a rota de emergência (a instrução de segurança, local) — nunca a lista de achados do motor
    ('estamos em risco, qual a tendência?', 'sos', False), ('isso não é um teste, tendência', 'sos', False), ('isso é real, preciso de ajuda, qual a tendência?', 'sos', False),
    ('tendências, onde ficam os coletes?', 'salvatagem', False), ('qual a tendência do EPIRB?', 'epirb', False), ('tendência do EPIRB', 'epirb', False), ('análise preditiva do sistema Seafire', 'seafire', False),
    ('tendências: qual o canal 16?', 'canal16', False), ('tendência do MMSI', 'mmsi', False),
    # (revisão) outro assunto, outro substantivo, ou relato: segue a rota dele (clima/mar/água/âncora/rumo, o guia, a IA), nunca os achados do motor; «perdendo capacidade» só vale com a bateria
    ('qual a tendência do tempo?', 'fallback', True), ('o tempo tem tendência a piorar?', 'fallback', True), ('tendência do mar', 'fallback', True), ('o mar tem tendência a crescer?', 'fallback', True),
    ('qual a tendência da temperatura da água?', 'base', True), ('tendência do rumo', 'fallback', True), ('a âncora tem tendência a garrar?', 'ancora', False), ('tendência de deriva da âncora', 'ancora', False),
    ('qual a tendência do Flamengo?', 'fallback', True), ('tendência da inflação', 'fallback', True), ('perdendo capacidade de carga', 'fallback', True), ('isso é real, tendências', 'fallback', True),
    ('o barco está perdendo capacidade?', 'fallback', True), ('estamos perdendo capacidade de governo', 'fallback', True), ('perdendo capacidade de manobra', 'fallback', True),
    ('o gerador está perdendo capacidade', 'gerador', False), ('o barco tem tendência a adernar', 'fallback', True), ('o que é análise preditiva?', 'fallback', True), ('tendência de pressão', 'fallback', True),
    # (revisão 3) o relato do sintoma («está subindo», «caindo») + a palavra «tendência» não é a pergunta da tendência: a leitura calma («dentro da faixa normal», «ESTÁVEL») contra o relato seria o erro da trava 10;
    # segue o guia do motor, a rota do equipamento ou a IA (como sem a palavra «tendência»). «Tendência de queda / de subida» é o substantivo e continua a pergunta.
    ('a temperatura do motor está subindo, qual a tendência?', 'base', True), ('temperatura do motor subindo, tendência', 'base', True), ('arrefecimento subindo, qual a tendência', 'base', True),
    ('o gerador está subindo de temperatura, qual a tendência?', 'gerador', False), ('a bateria está caindo, qual a tendência?', 'eletrico', False), ('bateria caindo tendência', 'eletrico', False),
    ('tendência de subida da temperatura do motor', 'preditiva', False), ('qual a tendência de queda das baterias?', 'preditiva', False),
    # (revisão 3) o relato de queda da pressão do óleo (segurança) vem antes, mesmo com «tendência de queda»
    ('tendência de queda da pressão do óleo', 'oleo', False), ('qual a tendência de queda do óleo?', 'oleo', False),
]
CASOS = CASOS + [(q, k) for q, k, _ in ROTAS_P3E_F11]
PEDE_IA.update({q: ia for q, k, ia in ROTAS_P3E_F11})
JS_PRED = """(xs) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false }, Q = 'quais as tendências?';
  return xs.map((x) => { R.fixar(x); const i = B.instante(), a = B.answer(Q, op);
    return { x, hora: i.hora, achados: B.preditiva(), key: a.key, texto: a.text, src: a.src, fala: B.falaCurta(a), ia: B.pedeIA(a, Q), be: i.q.motor_be_arref_c, bb: i.q.motor_bb_arref_c,
             tend: i.tend && i.tend.motor_be_arref_c, faltam: i.calc.faltam, alarme: i.q.alarmes && i.q.alarmes[0] && i.q.alarmes[0].desde }; }); }"""
# (revisão) a pergunta que nomeia o assunto abre (e fala) com o achado dele: o óleo, o arrefecimento/temperatura, as baterias, as horas/revisão/gerador
PRED_FOCO = [('qual a tendência do óleo?', ('oleo_cruzeiro',)), ('qual a tendência da pressão de óleo?', ('oleo_cruzeiro',)), ('as baterias estão perdendo capacidade?', ('baterias',)),
             ('tendência da temperatura do motor BE', ('arref_agora', 'arref_cruzeiro')), ('tendência do arrefecimento', ('arref_agora', 'arref_cruzeiro')), ('tendência das horas até a revisão', ('horas',)),
             ('tendência do gerador', ('horas',)), ('quais as tendências?', None)]   # (o arrefecimento tem dois achados, o do instante e o de cruzeiro: o mais grave dos dois)
JS_PRED_FOCO = """(xs) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false }, Q = PERGUNTAS;
  return xs.map((x) => { R.fixar(x); const i = B.instante(); return { x, hora: i.hora, achados: B.preditiva(), r: Q.map((q) => { const a = B.answer(q, op); return { q, key: a.key, linhas: a.text.split('\\n'), fala: B.falaCurta(a), ia: B.pedeIA(a, q) }; }) }; }); }""".replace('PERGUNTAS', json.dumps([q for q, _ in PRED_FOCO], ensure_ascii=False))
PRED_ORDEM_60 = ['arref_cruzeiro', 'horas', 'arref_agora', 'oleo_cruzeiro', 'baterias']
PRED_ORDEM_105 = ['arref_agora', 'arref_cruzeiro', 'horas', 'oleo_cruzeiro', 'baterias']


def f1(x):
    return ('%.1f' % x).replace('.', ',')


def hora_alarme(iso):
    d = datetime.datetime.strptime(iso, '%Y-%m-%dT%H:%M:%SZ') - datetime.timedelta(hours=3)
    return d.strftime('%H:%M:%S')


def grupo_preditiva(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); })")
        # (1) as perguntas: a chave e o PEDE_IA (a tendência nunca vai à IA); o relato de queda do óleo segue em `oleo`
        res = pg.evaluate(JS_P3C_CHAVES, [[q] for q, _, _ in ROTAS_P3E_F11])
        ruins = [(q, esp, ia_esp, key, ia) for (q, esp, ia_esp), (key, ia) in zip(ROTAS_P3E_F11, res) if key != esp or ia != ia_esp]
        ped('preditiva: as %d perguntas de tendência (e as que ela não rouba: relato de óleo, vento, maré, consumo, dinheiro) caem na chave certa, local' % len(ROTAS_P3E_F11), not ruins, ruins[:6])
        r = pg.evaluate(JS_PRED, ['60', '105'])
        a60, a105 = r
        for a, fase in ((a60, 'ok'), (a105, 'atencao')):
            ids = [x['id'] for x in a['achados']]
            quer = PRED_ORDEM_60 if fase == 'ok' else PRED_ORDEM_105
            ped('preditiva t=%s: os achados, do mais grave ao estável (no mesmo nível, o do instante primeiro): %s' % (a['x'], ', '.join(quer)), ids == quer, ids)
            pesos = {'acao': 3, 'atencao': 2, 'ok': 1}
            ped('preditiva t=%s: nunca um achado mais estável antes de um mais grave' % a['x'], all(pesos[p['nivel']] >= pesos[q['nivel']] for p, q in zip(a['achados'], a['achados'][1:])), [(x['id'], x['nivel']) for x in a['achados']])
            ped('preditiva t=%s: cada achado traz id, sistema, nível, rótulo, título, texto e a fonte' % a['x'],
                all(all(isinstance(x.get(k), str) and x[k] for k in ('id', 'sistema', 'nivel', 'rotulo', 'titulo', 'texto', 'fonte')) for x in a['achados']), a['achados'][:1])
        por = lambda a: {x['id']: x for x in a['achados']}
        p60, p105 = por(a60), por(a105)
        # (1b) o assunto da pergunta sobe para a 1ª linha (a falada): óleo, arrefecimento/temperatura, baterias, horas/revisão/gerador; a lista de baixo segue a gravidade; sem assunto, o mais grave
        for a in pg.evaluate(JS_PRED_FOCO, ['60', '105']):
            pedem = sum(1 for x in a['achados'] if x['nivel'] != 'ok')
            ruins = []
            for (q, alvo), r in zip(PRED_FOCO, a['r']):
                topo = next(x for x in a['achados'] if x['id'] in alvo) if alvo else a['achados'][0]
                suf = ', %d pedem atenção.' % pedem if (alvo and topo['nivel'] == 'ok' and pedem) else '.'
                quer = 'Tendências às %s: %s Mais 4 achados na lista%s' % (a['hora'], topo['texto'], suf)
                fala = re.sub(r' \([^)]*\)', '', quer)   # (a fala não lê o que está entre parênteses)
                lista_ok = len(r['linhas']) == 6 and all(l.startswith('• ' + x['rotulo'] + ' · ' + x['sistema'] + ' — ' + x['texto'] + ' (') for l, x in zip(r['linhas'][1:], a['achados']))
                if not (r['key'] == 'preditiva' and r['linhas'][0] == quer and r['fala'] == fala and r['ia'] is False and lista_ok):
                    ruins.append((q, r['linhas'][0][:150], quer[:150]))
            ped('preditiva t=%s: a pergunta que nomeia o assunto (óleo, pressão de óleo, baterias, temperatura, arrefecimento, horas, gerador) abre e fala com o achado dele (e diz quantos pedem atenção se ele está estável); a lista segue a gravidade; sem assunto, o mais grave' % a['x'], not ruins, ruins[:3])
        # (2) os três achados do contrato (§1.13): o do histórico e o dos contadores são iguais nos dois instantes; o do instante é o que muda
        ped('preditiva: o achado do histórico é «Motor BE 2,5 °C acima do BB em cruzeiro, subindo há 60 dias.» (a série de 60 dias e a volta de hoje), igual em 12:01:00 e 12:01:45, em atenção',
            p60['arref_cruzeiro']['texto'] == 'Motor BE 2,5 °C acima do BB em cruzeiro, subindo há 60 dias.' and p60['arref_cruzeiro'] == p105['arref_cruzeiro'] and p60['arref_cruzeiro']['nivel'] == 'atencao', p60['arref_cruzeiro'])
        for a in (a60, a105):
            f = a['faltam']
            quer = 'Faltam %s h para a troca de óleo e filtros dos motores (limite de 450 h) e %s h para a revisão do gerador (limite de 1.300 h).' % (f1(f['motores-oleo']), f1(f['gerador-revisao']))
            ped('preditiva t=%s: as horas até a troca de óleo e a revisão do gerador são os contadores do instante (calc.faltam), em atenção' % a['x'], por(a)['horas']['texto'] == quer and por(a)['horas']['nivel'] == 'atencao', (por(a)['horas']['texto'], quer))
        ped('preditiva: as horas que faltam são iguais nos dois instantes (em 45 s não mudam com 1 casa)', p60['horas']['texto'] == p105['horas']['texto'], (p60['horas']['texto'], p105['horas']['texto']))
        for a, quente in ((a60, 'normal'), (a105, 'aviso')):
            lado = 'BE' if a['be'] >= a['bb'] else 'BB'
            t = a['tend']
            sg = ('+' if t > 0 else '−' if t < 0 else '') + f1(abs(t))
            if quente == 'normal':
                quer = 'Arrefecimento do motor %s agora: %s °C, dentro da faixa normal (até 88 °C); %s °C nos últimos 30 s.' % (lado, f1(a['be'] if lado == 'BE' else a['bb']), sg)
            else:
                quer = 'Arrefecimento do motor %s agora: %s °C, acima de 88 °C — AVISO desde %s; %s °C nos últimos 30 s.' % (lado, f1(a['be'] if lado == 'BE' else a['bb']), hora_alarme(a['alarme']), sg)
            ped('preditiva t=%s: o achado do instante é o arrefecimento do motor agora contra a faixa e a tendência de 30 s (o texto do contrato)' % a['x'], por(a)['arref_agora']['texto'] == quer, (por(a)['arref_agora']['texto'], quer))
        ped('preditiva: o achado do instante muda entre 12:01:00 (estável) e 12:01:45 (atenção, AVISO desde 12:01:39) e é o único que muda de texto', p60['arref_agora']['texto'] != p105['arref_agora']['texto']
            and p60['arref_agora']['nivel'] == 'ok' and p105['arref_agora']['nivel'] == 'atencao' and p105['arref_agora']['rotulo'] == 'ATENÇÃO' and 'AVISO desde 12:01:39' in p105['arref_agora']['texto']
            and all(p60[k]['texto'] == p105[k]['texto'] for k in ('arref_cruzeiro', 'horas', 'oleo_cruzeiro')), (p60['arref_agora']['texto'], p105['arref_agora']['texto']))
        ped('preditiva: a pressão de óleo em cruzeiro (por motor) e as baterias (30 dias) são estáveis, com os números do histórico e do quadro',
            re.match(r'^Pressão de óleo em cruzeiro estável há 60 dias: BB \d,\d bar · BE \d,\d bar, com mínimo normal de 2,4 bar\.$', p60['oleo_cruzeiro']['texto']) and p60['oleo_cruzeiro']['nivel'] == 'ok'
            and re.match(r'^Baterias estáveis nos últimos 30 dias: serviço \d\d,\d\d V · partida \d\d,\d\d V · 12 V \d\d,\d\d V, com variação de até \d,\d V\.$', p60['baterias']['texto']) and p60['baterias']['nivel'] == 'ok', (p60['oleo_cruzeiro']['texto'], p60['baterias']['texto']))
        # (3) a resposta: a 1ª linha é o achado mais grave com a hora do instante; as demais, um achado por linha com a fonte; local (nunca IA); a fala é a 1ª linha
        for a in (a60, a105):
            top = a['achados'][0]
            ped('preditiva t=%s: a resposta abre com «Tendências às %s: » e o achado mais grave, diz quantos mais há, e é local (nunca à IA)' % (a['x'], a['hora']),
                a['key'] == 'preditiva' and a['texto'].split('\n')[0] == 'Tendências às %s: %s Mais 4 achados na lista.' % (a['hora'], top['texto']) and a['ia'] is False, (a['key'], a['texto'].split('\n')[0], a['ia']))
            linhas = a['texto'].split('\n')[1:]
            ped('preditiva t=%s: uma linha por achado, na ordem, com o rótulo, o sistema e a fonte' % a['x'], len(linhas) == 5 and all(l.startswith('• ' + x['rotulo'] + ' · ' + x['sistema'] + ' — ' + x['texto'] + ' (') and l.endswith(x['fonte'] + ')') for l, x in zip(linhas, a['achados'])), linhas[:2])
            ped('preditiva t=%s: a fonte cita a regra fixa, o histórico, a agenda e a hora do instante; a fala é a 1ª linha, sem parênteses' % a['x'],
                a['src'].startswith('Fonte: achados por regra fixa neste aparelho sobre ') and a['hora'] in a['src'] and 'Agenda preditiva' in a['src'] and a['fala'] == a['texto'].split('\n')[0] and '(' not in a['fala'], (a['src'], a['fala']))
            tudo = a['texto'] + '\n' + a['src'] + '\n' + a['fala']
            ruim = [(n, m.group(0)) for n in VARREDURA for m in [RX[n].search(tudo)] if m]
            ped('preditiva t=%s: nenhuma das regex do §3 (ROTULOS, AUTENTICIDADE, VAZIOS, VISIVEL, DINHEIRO) casa o texto, a fonte nem a fala, e nenhuma coordenada' % a['x'], not ruim and not confere.R_COORD.search(tudo), ruim)
    finally:
        pg.ctx.close()
    # (4) modo real (simulacao false): o replay não anda; só o que vem do histórico e da agenda (sem o instante, sem a volta de hoje, sem as baterias de 30 dias), sem hora, sem rótulo novo
    pg = pagina(b, extra=SEM_SIMULACAO, muta=muta)
    try:
        r = pg.evaluate("""() => { const B = window.CapitaoBrain, a = B.answer('quais as tendências?', { platform: 'app', commit: false }), h = window.CapitaoDados.historico.cruzeiro, m = (k) => h[k].d.slice(-7).reduce((s, x) => s + x, 0) / 7 / h[k].escala;
          return { ids: B.preditiva().map((x) => [x.id, x.texto]), texto: a.text, key: a.key, src: a.src, dif: m('motor_be_arref_c') - m('motor_bb_arref_c') }; }""")
        quer = 'Motor BE %s °C acima do BB em cruzeiro, subindo há 60 dias.' % f1(r['dif'])
        ped('preditiva (simulacao false): só o histórico, o óleo e as horas da agenda (sem o instante nem as baterias de 30 dias), sem a volta de hoje: a diferença é a da última semana do histórico',
            [x for x, _ in r['ids']] == ['arref_cruzeiro', 'horas', 'oleo_cruzeiro'] and r['ids'][0][1] == quer and r['key'] == 'preditiva' and r['texto'].startswith('Tendências: ' + quer), (quer, r))
        ped('preditiva (simulacao false): a resposta não tem hora do instante nem «ao vivo»', not re.search(r'\d\d:\d\d:\d\d|ao vivo', r['texto'] + r['src']), r['src'])
    finally:
        pg.ctx.close()
    # (4b) (revisão) os ramos do arrefecimento em cruzeiro que o histórico gerado não exercita: a diferença abaixo de 1 °C («esfriam igual»), a de 1,5 °C estável com o BE e com o BB mais quente.
    # O histórico do BE é plantado a partir do BB (a diferença fixa, em décimos de grau); sem a simulação não há a volta de hoje, e a diferença é a da última semana.
    for dif, quer in ((0.7, 'Os dois motores esfriam igual em cruzeiro: diferença de 0,7 °C, estável há 60 dias.'), (-0.4, 'Os dois motores esfriam igual em cruzeiro: diferença de 0,4 °C, estável há 60 dias.'),
                      (1.5, 'Motor BE 1,5 °C acima do BB em cruzeiro, estável há 60 dias.'), (-1.5, 'Motor BB 1,5 °C acima do BE em cruzeiro, estável há 60 dias.')):
        pg = pagina(b, extra=SEM_SIMULACAO + ";(function () { var h = window.CapitaoDados.historico.cruzeiro, bb = h.motor_bb_arref_c, be = h.motor_be_arref_c; be.d = bb.d.map(function (x) { return x + Math.round(%s * be.escala); }); })();" % dif, muta=muta)
        try:
            r = pg.evaluate("() => { const x = window.CapitaoBrain.preditiva().filter((a) => a.id === 'arref_cruzeiro')[0]; return x && { texto: x.texto, nivel: x.nivel, rotulo: x.rotulo }; }")
            ped('preditiva (histórico plantado, diferença %s °C): o arrefecimento em cruzeiro diz «%s» (estável, nível ok)' % (dif, quer), r == {'texto': quer, 'nivel': 'ok', 'rotulo': 'ESTÁVEL'}, r)
        finally:
            pg.ctx.close()
    # (4c) (revisão 4) os ramos que o histórico gerado nunca exercita (ele é estável): o banco de baterias que cai 0,3 V ou mais em 30 dias (a série do replay plantada), a pressão de óleo em cruzeiro que cai 0,2 bar
    # ou mais em 60 dias (o histórico plantado) e a série de menos de 14 dias, que não dá achado. Cada caso numa página nova, com a série/histórico adulterados DEPOIS do carregamento (o cérebro lê a cada chamada).
    PLANTA = """([modo, a, b_]) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, D = window.CapitaoDados, h = D.historico.cruzeiro;
      const ach = () => { const o = {}; B.preditiva().forEach((x) => { o[x.id] = { texto: x.texto, nivel: x.nivel, rotulo: x.rotulo }; }); return o; };
      if (modo === 'bateria') R.serie = (c, j, ms) => Array.from({ length: 30 }, (_, k) => ({ t: ms - (30 - k) * 86400e3, v: k < 5 ? a : k >= 25 ? b_ : (a + b_) / 2 }));
      if (modo === 'oleo') ['motor_bb_oleo_bar', 'motor_be_oleo_bar'].forEach((c) => { const s = h[c]; s.d = Array.from({ length: 60 }, (_, k) => Math.round((a - k * b_) * s.escala)); });
      if (modo === 'curto') ['motor_bb_arref_c', 'motor_be_arref_c', 'motor_bb_oleo_bar', 'motor_be_oleo_bar'].forEach((c) => { h[c].d = h[c].d.slice(0, a); });
      return ach(); }"""
    for (rot, args, quer_id, rx_texto, quer_nivel, quer_rotulo) in (
            ('baterias com queda de 1,3 V', ['bateria', 26.0, 24.7], 'baterias', r'^Banco de baterias caiu 1,3 V nos últimos 30 dias: serviço \d\d,\d\d V · partida \d\d,\d\d V · 12 V \d\d,\d\d V\.$', 'atencao', 'ATENÇÃO'),
            ('baterias com queda de 0,2 V (abaixo de 0,3)', ['bateria', 26.0, 25.8], 'baterias', r'^Baterias estáveis nos últimos 30 dias: serviço \d\d,\d\d V · partida \d\d,\d\d V · 12 V \d\d,\d\d V, com variação de até 0,2 V\.$', 'ok', 'ESTÁVEL'),
            ('pressão de óleo em cruzeiro caindo 0,01 bar por dia (0,53 bar em 60 dias)', ['oleo', 3.0, 0.01], 'oleo_cruzeiro', r'^Pressão de óleo em cruzeiro caindo há 60 dias: BB \d,\d bar · BE \d,\d bar, com mínimo normal de 2,4 bar\.$', 'atencao', 'ATENÇÃO'),
            ('pressão de óleo em cruzeiro caindo 0,002 bar por dia (0,11 bar, abaixo de 0,2)', ['oleo', 3.0, 0.002], 'oleo_cruzeiro', r'^Pressão de óleo em cruzeiro estável há 60 dias: BB \d,\d bar · BE \d,\d bar, com mínimo normal de 2,4 bar\.$', 'ok', 'ESTÁVEL')):
        pg = pagina(b, muta=muta)
        try:
            a_ = pg.evaluate(PLANTA, args)
            x_ = a_.get(quer_id)
            ped('preditiva (plantado, %s): o achado diz «%s», nível %s' % (rot, quer_id, quer_nivel), bool(x_) and re.match(rx_texto, x_['texto']) is not None and x_['nivel'] == quer_nivel and x_['rotulo'] == quer_rotulo, x_)
        finally:
            pg.ctx.close()
    pg = pagina(b, muta=muta)
    try:
        a_ = pg.evaluate(PLANTA, ['curto', 10, 0])
        ped('preditiva (plantado): a série de cruzeiro com menos de 14 dias não dá achado (nem o arrefecimento nem a pressão de óleo); sobram as horas e as baterias', 'arref_cruzeiro' not in a_ and 'oleo_cruzeiro' not in a_ and 'horas' in a_ and 'baterias' in a_, sorted(a_))
    finally:
        pg.ctx.close()
    pg = pagina(b, muta=muta)
    try:
        a_ = pg.evaluate(PLANTA, ['curto', 14, 0])
        ped('preditiva (plantado): a série com exatamente 14 dias ainda dá o achado do arrefecimento e o da pressão de óleo', 'arref_cruzeiro' in a_ and 'oleo_cruzeiro' in a_, sorted(a_))
    finally:
        pg.ctx.close()
    # (5) o SOS: nenhum achado (nem o histórico nem a agenda) — o SOS não lê dado do barco
    pg = pagina(b, scripts=('capitao-dados.js', 'capitao-brain.js'), caminho='SOS-cerebro.html', fixo=None, muta=muta)
    try:
        r = pg.evaluate("() => { const B = window.CapitaoBrain, a = B.answer('quais as tendências?', { platform: 'app', commit: false }); return { n: B.preditiva().length, texto: a.text }; }")
        ped('preditiva (SOS): nenhum achado e nenhum dado do barco na resposta', r['n'] == 0 and not re.search(r'Faltam|BE \d|ATENÇÃO|ESTÁVEL|Motor B', r['texto']), r)
    finally:
        pg.ctx.close()


GRUPOS_3A['preditiva'] = grupo_preditiva
MUTANTES_3E_F11 = [
    ('p3e preditiva: o achado do instante sem o AVISO desde', r"if (al && al.hora) desde = ' desde ' + al.hora;", r"if (al && al.hora) desde = '';", ('preditiva',)),
    ('p3e preditiva: sem ordenar do mais grave ao estável', r"return (PRED_PESO[b.nivel] - PRED_PESO[a.nivel]) || (PRED_ORDEM.indexOf(a.id) - PRED_ORDEM.indexOf(b.id));", r"return (PRED_ORDEM.indexOf(a.id) - PRED_ORDEM.indexOf(b.id));", ('preditiva',)),
    ('p3e preditiva: a diferença dos motores nunca sobe', r"tend = rumo >= 0.5 ? ', subindo há '", r"tend = rumo >= 99 ? ', subindo há '", ('preditiva',)),
    ('p3e preditiva: a tendência perde para a leitura do óleo', "    if (tendenciaPergunta(q)) return 'preditiva';", "    if (!ol && tendenciaPergunta(q)) return 'preditiva';", ('preditiva',)),
    # (o mutante «o relato de queda do óleo perde para a tendência» saiu: com o cabecaEmerg no topo da tendenciaPergunta — que inclui o relato do óleo — ele é equivalente; a ordem da route() e a guarda cobrem a mesma pergunta)
    ('p3e preditiva: as horas não leem o contador do instante', "      var f = faltam(t);\n      if (typeof f !== 'number' || !isFinite(f)) return;\n      menor", "      var f = t.horas.faltam;\n      if (typeof f !== 'number' || !isFinite(f)) return;\n      menor", ('preditiva',)),
    ('p3e preditiva: a volta de hoje não entra (só o histórico)', "hoje = cruzeiroHoje(['motor_bb_arref_c', 'motor_be_arref_c']); n = bb.length;", "hoje = null; n = bb.length;", ('preditiva',)),
    ('p3e preditiva: a diferença abaixo de 1 °C vira «motor X acima do Y» (sem o ramo «esfriam igual»)', r"    if (abs < 1) return { id: 'arref_cruzeiro'", r"    if (abs < 0) return { id: 'arref_cruzeiro'", ('preditiva',)),
    ('p3e preditiva: o motor mais quente em cruzeiro é sempre o BE', r"quente = fim >= 0 ? 'BE' : 'BB'; frio = fim >= 0 ? 'BB' : 'BE';", r"quente = 'BE'; frio = 'BB';", ('preditiva',)),
    # (revisão) a lista branca, o «perdendo capacidade» só com a bateria, a pressão barométrica, o assunto na 1ª linha
    ('p3e preditiva: sem a lista branca a tendência rouba o tempo, o mar, a âncora, o relato e a emergência', r"has(q, ['bateria']))) && leitura(q.replace(PRED_TENDENCIA_DE, ' tendencia '), PRED_OK) && !(has(q, ['pressao'])", r"has(q, ['bateria']))) && !(has(q, ['pressao'])", ('preditiva',)),
    ('p3e preditiva: «perdendo capacidade» vale sem a bateria', r"(has(q, ['perdendo capacidade']) && has(q, ['bateria']))", r"has(q, ['perdendo capacidade'])", ('preditiva',)),
    ('p3e preditiva: a tendência da pressão (a barométrica) vira a do óleo', r"PRED_OK) && !(has(q, ['pressao']) && !has(q, ['oleo']));", r"PRED_OK);", ('preditiva',)),
    # (revisão 3) o relato do sintoma + «tendência»; «tendência de queda» é a pergunta
    ('p3e preditiva: «subindo», «caindo», «queda» e «subida» voltam à lista branca (o relato vira a leitura calma)', r"recomendacao recomendacoes algum alguma alguns algumas estavel estaveis", r"recomendacao recomendacoes algum alguma alguns algumas queda quedas subida subindo caindo estavel estaveis", ('preditiva',)),
    ('p3e preditiva: «tendência de queda / de subida» deixa de ser a pergunta da tendência', r"leitura(q.replace(PRED_TENDENCIA_DE, ' tendencia '), PRED_OK)", r"leitura(q, PRED_OK)", ('preditiva',)),
    ('p3e preditiva: o assunto da pergunta não sobe para a 1ª linha', r"topo = l.filter(function (a) { return ids.indexOf(a.id) !== -1; })[0] || l[0]", r"topo = l[0]", ('preditiva',)),
    ('p3e preditiva: a 1ª linha do achado estável não diz quantos pedem atenção', r"(topo.nivel === 'ok' && pedem ? ', ' + pedem + (pedem === 1 ? ' pede atenção.' : ' pedem atenção.') : '.')", r"'.'", ('preditiva',)),
    ('p3e preditiva: a pergunta do gerador e da revisão não sobe o achado das horas', r"[[' hora', 'revisao', 'troca', 'gerador'], ['horas']]", r"[[' hora', 'revisao', 'troca'], ['horas']]", ('preditiva',)),
    # (revisão 4) os ramos plantados: o limiar das baterias (0,3 V) no nível e no texto, o da pressão de óleo (0,2 bar) no nível e no texto, a série mínima de 14 dias
    ('p3e preditiva: o nível das baterias só vai a atenção com 3 V de queda', r"nivel: queda >= 0.3 ? 'atencao' : 'ok', titulo: 'Baterias nos últimos 30 dias',", r"nivel: queda >= 3 ? 'atencao' : 'ok', titulo: 'Baterias nos últimos 30 dias',", ('preditiva',)),
    ('p3e preditiva: o texto das baterias só diz «caiu» com 3 V de queda', r"texto: queda >= 0.3 ? 'Banco de baterias caiu '", r"texto: queda >= 3 ? 'Banco de baterias caiu '", ('preditiva',)),
    ('p3e preditiva: o nível da pressão de óleo só vai a atenção com 2 bar de queda', r"nivel: queda >= 0.2 || abaixo ?", r"nivel: queda >= 2 || abaixo ?", ('preditiva',)),
    ('p3e preditiva: o texto da pressão de óleo só diz «caindo» com 2 bar de queda', r"(queda >= 0.2 ? 'caindo' : 'estável') + ' há ' + n + ' dias: BB '", r"(queda >= 2 ? 'caindo' : 'estável') + ' há ' + n + ' dias: BB '", ('preditiva',)),
    ('p3e preditiva: a série de cruzeiro curta (menos de 14 dias) dá achado', r"s.d.length < 14 ||", r"s.d.length < 3 ||", ('preditiva',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3E_F11

# —— F22: peças e estoque ——
ROTAS_P3E_F22 = [
    ('quais peças temos a bordo?', 'pecas', False), ('estoque de peças', 'pecas', False), ('tem rotor sobressalente?', 'pecas', False), ('quais peças estão no mínimo?', 'pecas', False),
    ('peças da revisão do gerador', 'pecas', False), ('peças para o filtro da climatização', 'pecas', False), ('quantas peças faltam?', 'pecas', False), ('peças do guincho', 'pecas', False),
    ('peça sobressalente do estabilizador', 'pecas', False), ('quando repor as peças?', 'pecas', False),
    # o que ela não rouba: reparo e vida útil (o guia ou a IA), a peça que quebrou, o estoque de água
    ('como trocar a peça do motor', 'base', True), ('peça quebrou', 'fallback', True), ('estoque de água', 'fallback', True),
    # (revisão) o estoque pelo NOME da peça cadastrada, com o verbo ou o número de estoque («tem rotor de reposição?» não é a posição do barco; «quantos filtros de óleo temos?» não é o intervalo do guia)
    ('tem anodo a bordo?', 'pecas', False), ('tem rotor de reposição?', 'pecas', False), ('quantos rotores do gerador temos?', 'pecas', False), ('temos filtro de óleo a bordo?', 'pecas', False),
    ('quantos filtros de óleo temos?', 'pecas', False), ('quantos anodos temos a bordo?', 'pecas', False), ('quantos impellers temos?', 'pecas', False), ('tem filtro de combustível a bordo?', 'pecas', False),
    ('onde fica o rotor de reposição?', 'pecas', False), ('falta rotor?', 'pecas', False),
    # a pergunta de estoque sem nome (alguma peça, alguma coisa para repor, onde ficam/guardamos, cadê, usei) é o estoque inteiro
    ('preciso repor alguma peça?', 'pecas', False), ('falta alguma peça?', 'pecas', False), ('tem alguma coisa para repor?', 'pecas', False), ('onde ficam as peças sobressalentes?', 'pecas', False),
    ('onde fica o rotor sobressalente?', 'pecas', False), ('quais peças preciso repor?', 'pecas', False), ('quais peças precisam de reposição?', 'pecas', False), ('preciso de peças?', 'pecas', False),
    ('vou precisar de peças na revisão?', 'pecas', False), ('cadê as peças?', 'pecas', False), ('onde guardamos os sobressalentes?', 'pecas', False), ('usei uma peça do estoque', 'pecas', False),
    ('cabe quantas peças no armário?', 'pecas', False),
    # (revisão) a trava 10: o EPIRB, o Seafire (o sistema fixo), o canal 16 e o rádio com a palavra «peça», «estoque» ou «sobressalente» seguem a rota do equipamento (a instrução de segurança, local)
    ('tem sobressalente do EPIRB?', 'epirb', False), ('estoque de peças e a bateria do EPIRB', 'epirb', False), ('bateria do EPIRB em estoque?', 'epirb', False), ('estoque de peças do sistema fixo Seafire', 'seafire', False),
    ('tem peça sobressalente do sistema fixo Seafire?', 'seafire', False), ('tem peça de reposição para o sistema fixo de supressão', 'seafire', False), ('peças do rádio VHF canal 16', 'canal16', False),
    ('peças do rádio VHF', 'canal16', False), ('tem rádio sobressalente?', 'canal16', False), ('tem sobressalente de coletes?', 'salvatagem', False), ('peças do extintor', 'salvatagem', False),
    # (revisão) o preço e a compra são o dinheiro (foraBarco, local) ou a IA; o prazo, a idade e o reparo não são o estoque; o óleo e o diesel não são peça
    ('qual o preço das peças?', 'foraBarco', False), ('quanto custa a peça do rotor?', 'foraBarco', False), ('preço das peças em estoque', 'foraBarco', False), ('qual o valor das peças?', 'fallback', True),
    ('preciso comprar peças', 'fallback', True), ('quanto falta para o rotor do gerador?', 'base', True), ('falta trocar o rotor?', 'base', True), ('quanto tempo dura o rotor?', 'fallback', True),
    ('quando trocar o filtro de óleo?', 'base', True), ('quantos filtros de óleo o motor leva?', 'base', True), ('quanto óleo temos a bordo?', 'base', True), ('quanto diesel temos?', 'autonomia', False),
    ('fusível de reposição', 'pecas', False), ('reposição', 'fallback', True), ('qual a posição?', 'posicao', False), ('minha posição', 'posicao', False),
    ('quanto tempo tem o rotor a bordo?', 'base', True), ('quando trocar o rotor que temos a bordo?', 'base', True), ('temos que trocar o filtro de óleo que temos a bordo', 'base', True),
    ('estoque de combustível', 'autonomia', False), ('preciso repor óleo', 'fallback', True), ('preciso repor o gelo', 'fallback', True),
    # (revisão 3) o relato de falha com «falta / acabou / zerou» + palavra que é nome de peça («tela», «filtro», «rotor») NÃO é o estoque: a peça tem de ser o OBJETO do verbo («falta rotor?»), e «tela» sozinha é a do plotter
    ('falta imagem na tela do radar', 'eletronicos', False), ('falta sinal na tela do plotter', 'eletronicos', False), ('a tela do plotter apagou, falta sinal', 'eletronicos', False), ('faltando brilho na tela', 'fallback', True),
    ('zerou a tela do plotter', 'eletronicos', False), ('acabou a luz da tela', 'fallback', True), ('faltando fluxo de água no filtro de água salgada', 'base', True), ('falta fluxo no filtro', 'base', True),
    ('falta água no rotor', 'base', True), ('falta combustível no filtro separador', 'autonomia', False), ('acabou o combustível do filtro', 'autonomia', False), ('faltando diesel nos filtros', 'autonomia', False),
    ('acabou a água do rotor', 'base', True), ('quanta água tem no filtro de água salgada?', 'base', True), ('tem fluxo de água no filtro a bordo?', 'base', True),
    ('falta tela do filtro?', 'pecas', False), ('quantas telas do filtro temos?', 'pecas', False), ('acabou o rotor?', 'pecas', False), ('faltando filtros de óleo?', 'pecas', False),
    # (revisão 3) o singular e o plural de uma peça casam («fusível» e «fusíveis»), com qualquer verbo de estoque
    ('temos fusível sobressalente?', 'pecas', False), ('tem fusível de reposição?', 'pecas', False), ('temos fusível a bordo?', 'pecas', False), ('falta fusível?', 'pecas', False), ('quantos fusíveis temos?', 'pecas', False),
    # (revisão 3) telefone, contato, CNPJ, e-mail e nome de oficina, fornecedor e técnico (trava 13) seguem a rota dos contatos ou a IA, nunca a lista de estoque
    ('telefone do fornecedor de peças', 'contatos', False), ('contato da oficina para peças sobressalentes', 'contatos', False), ('quem é o técnico de bordo que cuida das peças', 'contatos', False),
    ('peças do técnico de bordo', 'contatos', False), ('onde fica a marina da base peças', 'contatos', False), ('peças de reposição para quando eu ligar para a oficina', 'contatos', False),
    ('CNPJ do fornecedor de peças', 'fallback', True), ('tem alguma peça do fornecedor Marcos?', 'fallback', True), ('peças do fornecedor Náutica Sol', 'fallback', True), ('e-mail do fornecedor de sobressalentes', 'fallback', True),
    # (revisão 3) «temos que / tenho que» + repor é a obrigação (o guia ou a IA), não a pergunta do estoque
    ('temos que repor o filtro de óleo', 'fallback', True), ('tenho que repor o rotor', 'fallback', True),
    # (revisão 4) a pergunta central do estoque: o que acabou, o que está zerado, a peça pelo nome com o estado dela («o rotor do gerador está zerado?»), o que preciso de uma peça
    ('que peça acabou?', 'pecas', False), ('qual peça acabou?', 'pecas', False), ('alguma peça acabou?', 'pecas', False), ('acabou alguma peça?', 'pecas', False), ('tem peça zerada?', 'pecas', False),
    ('quais peças estão zeradas?', 'pecas', False), ('o rotor do gerador está zerado?', 'pecas', False), ('por que o rotor do gerador está zerado?', 'pecas', False), ('o rotor já acabou?', 'pecas', False),
    ('o filtro de óleo está no mínimo?', 'pecas', False), ('o anodo está no mínimo?', 'pecas', False), ('preciso de rotor para o gerador', 'pecas', False), ('preciso de um filtro de óleo', 'pecas', False),
    # (revisão 4) o relato com «zerado / acabou» cujo sujeito não é a peça cadastrada (o fluxo, a tela do plotter, a peça que quebrou, a que acabou de chegar) NÃO é o estoque; «o que acabou?» sem a palavra peça
    # é vago (comida, gelo, energia): vai à IA, que agora recebe o bloco «## Peças» na ficha
    ('o fluxo do filtro está zerado', 'base', True), ('a peça acabou de quebrar', 'fallback', True), ('o filtro acabou de chegar', 'base', True), ('o que acabou?', 'fallback', True),
    ('o que está faltando?', 'fallback', True), ('preciso trocar o rotor', 'base', True), ('preciso comprar um rotor', 'fallback', True),
    # (revisão 4) a trava 10 com a «Licença de Estação» (papelada, não o roteiro): a rota docsvenc, nunca o estoque; e a cabeça do botão DISTRESS e da baliza do EPIRB é local (o trecho de segurança deles)
    ('licença de estação do rádio, quais peças temos?', 'docsvenc', False), ('o botão DISTRESS, quais peças temos?', 'base', False), ('o botão DISTRESS, tem peça sobressalente?', 'base', False),
    ('a baliza, quais peças temos?', 'base', False), ('quais peças temos, a baliza', 'base', False),
]
CASOS = CASOS + [(q, k) for q, k, _ in ROTAS_P3E_F22]
PEDE_IA.update({q: ia for q, k, ia in ROTAS_P3E_F22})
K_PECAS_T = 'capitao.pecas.v1'
GENERICAS_PECAS = ['quais peças preciso repor?', 'quais peças precisam de reposição?', 'preciso de peças?', 'vou precisar de peças na revisão?', 'cadê as peças?', 'onde guardamos os sobressalentes?', 'onde ficam as peças sobressalentes?',
                   'usei uma peça do estoque', 'preciso repor alguma peça?', 'falta alguma peça?', 'tem alguma coisa para repor?', 'cabe quantas peças no armário?',
                   # (revisão 3) a palavra que o app não conhece como coisa de bordo («dizer», «atual», «indisponível», «leitura fixa», um e-mail, um site) não vira nome: abre direto com a lista, sem «Nenhuma peça cadastrada…»
                   'pode me dizer quais peças temos?', 'me informa o estoque de peças', 'situação do estoque', 'temos peças suficientes?', 'peças de reposição disponíveis', 'qual o estoque de peças atual?', 'resumo das peças',
                   'peças críticas', 'peças vencidas', 'peças com validade', 'estoque baixo', 'preciso de ajuda com as peças', 'peças para o fim de semana', 'peças indisponível', 'peças leitura fixa', 'peças joao@marina.com.br',
                   'peças www.nauticasol.com.br']
# (revisão 4) o qualificador «para o motor» não empata com o nome da peça; a pergunta central do estoque (o que acabou, o que está zerado); a peça pelo nome com o estado dela
DESEMPATE_PECAS = [('tem correia sobressalente para o motor?', ['p04']), ('temos correia de reposição para o motor?', ['p04']), ('falta correia no motor', ['p04']),
                   ('tem escova sobressalente para o motor?', ['p12']), ('tem anodo sobressalente para o motor?', ['p07', 'p08']), ('tem fusível sobressalente para o motor?', ['p11']),
                   ('tem rotor sobressalente para o gerador?', ['p05']), ('tem filtro sobressalente para o gerador?', ['p06'])]
ZERADAS_PECAS = ['que peça acabou?', 'qual peça acabou?', 'alguma peça acabou?', 'acabou alguma peça?', 'tem peça zerada?', 'quais peças estão zeradas?', 'falta alguma peça?', 'preciso repor alguma peça?']
ESTADO_NOME_PECAS = [('o rotor já acabou?', ['p03', 'p05']), ('o filtro de óleo está no mínimo?', ['p01', 'p06']), ('o anodo está no mínimo?', ['p07', 'p08']), ('preciso de rotor para o gerador', ['p05']),
                     ('preciso de um filtro de óleo', ['p01', 'p06']), ('o rotor do gerador está zerado?', None), ('por que o rotor do gerador está zerado?', None)]   # (None: a tarefa da agenda que a pergunta cita abre a resposta, «Peças para inspeção do rotor…»)
JS_PECAS = """() => { const B = window.CapitaoBrain, D = window.CapitaoDados, op = { platform: 'app', commit: false }, R = window.CapitaoReplay; R.fixar('60');
  const antes = JSON.stringify(D.pecas), chave = () => localStorage.getItem('capitao.pecas.v1'), movs = () => { const v = JSON.parse(chave() || '{}'); return v.movs || []; }, q = (id) => B.pecas().filter((x) => x.id === id)[0];
  const out = { base: D.pecas.map((x) => ({ id: x.id, n: x.n, qtd: x.qtd, min: x.min, local: x.local, tarefas: x.tarefas || [] })), ags: D.agenda.map((t) => t.id) };
  const resp = (p) => { const a = B.answer(p, op); return { key: a.key, text: a.text, src: a.src, fala: B.falaCurta(a), ia: B.pedeIA(a, p) }; };
  out.genericas = GENERICAS.map((q) => [q, resp(q)]);
  out.desempate = DESEMPATE.map((q) => [q, resp(q)]); out.zeradas = ZERADAS.map((q) => [q, resp(q)]); out.estadoNome = ESTADONOME.map((q) => [q, resp(q)]); out.ficha = B.ficha('app', 'qualquer pergunta', null);
  out.nomes = { rotorGerador: resp('quantos rotores do gerador temos?'), filtroOleo: resp('temos filtro de óleo a bordo?'), filtroOleo2: resp('quantos filtros de óleo temos?'), anodos: resp('quantos anodos temos a bordo?'),
                rotorReposicao: resp('tem rotor de reposição?'), filtroComb: resp('tem filtro de combustível a bordo?'), filtros5: resp('quantos filtros temos?'), fusivel: resp('quantos fusíveis temos?'),
                fusivelSing: resp('temos fusível sobressalente?'), telaFiltro: resp('falta tela do filtro?'), telaPlotter: resp('peças da tela do plotter'), zerou: resp('acabou o rotor?') };
  out.eco = ['peças fictícias', 'peças simuladas do guincho', 'estoque de peças do 11 99999 9999', 'peças do guincho', 'peças do radar', 'peças do guincho amarelo'].map(resp);
  out.lista0 = B.pecas(); out.todas = resp('quais peças temos a bordo?'); out.gerador = resp('peças da revisão do gerador'); out.rotor = resp('tem rotor sobressalente?'); out.guincho = resp('peças do guincho'); out.clima = resp('peças para o filtro da climatização');
  out.semEscrita = chave() === null;
  // −1 USADA ×4 no p01 (4 → 0), a 5ª não existe; o Desfazer só da última; o da primeira recusa
  out.us = []; for (let k = 0; k < 5; k++) out.us.push(B.usaPeca('p01'));
  out.q1 = q('p01'); out.movs1 = movs();
  out.desfazAntigo = B.desfazUsoPeca(out.us[0]); out.movsAntigo = movs().length;
  out.desfaz = B.desfazUsoPeca(out.us[3]); out.movs2 = movs(); out.q2 = q('p01');
  out.zerada = B.usaPeca('p05'); out.movsZerada = movs().length; out.desconhecida = B.usaPeca('xx'); out.movsDesc = movs().length;
  out.ajuste = B.ajustaPeca('p02', 7); out.q3 = q('p02'); out.ajRuim = [B.ajustaPeca('p02', -1), B.ajustaPeca('p02', 1000), B.ajustaPeca('p02', 'x'), B.ajustaPeca('p02', 7), B.ajustaPeca('zz', 3)];
  out.nova = B.addPeca({ n: '  Fusível   10 A ', qtd: '5', min: 2, local: 'armário de ferramentas', obs: 'reserva do painel', tarefas: ['baterias', 'zzz'], pn: 'ABC123', preco: 12 });
  out.novaRuim = [B.addPeca({ n: '' }), B.addPeca({}), B.addPeca(null)];
  out.usaNova = out.nova ? B.usaPeca(out.nova.id) : null; out.qNova = out.nova ? q(out.nova.id) : null;
  out.estado = JSON.parse(chave()); out.depois = JSON.stringify(D.pecas) === antes; out.lista1 = B.pecas();
  out.respDepois = resp('quais peças temos a bordo?');
  out.isos = out.estado.movs.map((m) => m.iso);
  return out; }""".replace('GENERICAS', json.dumps(GENERICAS_PECAS, ensure_ascii=False)).replace('DESEMPATE', json.dumps([q for q, _ in DESEMPATE_PECAS], ensure_ascii=False)).replace('ZERADAS', json.dumps(ZERADAS_PECAS, ensure_ascii=False)).replace('ESTADONOME', json.dumps([q for q, _ in ESTADO_NOME_PECAS], ensure_ascii=False))


def esperado_peca(x):
    q, mn = x['qtd'], x['min']
    nivel = 'zero' if q <= 0 else 'baixa' if mn > 0 and q <= mn else 'ok'
    st = 'ZERADA' if q <= 0 else 'ABAIXO DO MÍNIMO' if mn > 0 and q < mn else 'NO MÍNIMO' if mn > 0 and q == mn else 'OK'
    return nivel, st


def min1_py(n):
    return n if re.match(r'^[A-ZÀ-Ý]{2}', n) else n[:1].lower() + n[1:]


def frase_peca(x):
    """A frase da peça na 1ª linha: «rotor do gerador, 0 a bordo, zerada, mínimo 1», «…, 1 a bordo, abaixo do mínimo de 2», «…, no mínimo», «…, 4 a bordo, mínimo 2»."""
    nivel, _ = esperado_peca(x)
    q, mn = x['qtd'], x['min']
    t = '%s, %d a bordo' % (min1_py(x['n']), q)
    if nivel == 'zero':
        t += ', zerada' + (', mínimo %d' % mn if mn > 0 else '')
    elif nivel == 'baixa':
        t += (', abaixo do mínimo de %d' % mn) if q < mn else ', no mínimo'
    elif mn > 0:
        t += ', mínimo %d' % mn
    return t


def corpo_pecas(xs):
    """O que vem depois do «Estoque de peças: » (ou do «Peças para <tarefa>: »): até 3 peças, cada uma com a quantidade; mais que isso, o total e as que pedem atenção (até 3)."""
    rank = {'zero': 0, 'baixa': 1, 'ok': 2}
    xs = sorted(xs, key=lambda x: rank[esperado_peca(x)[0]])   # estável, como o sort do cérebro
    ps = [x for x in xs if esperado_peca(x)[0] != 'ok']
    if len(xs) <= 3:
        return '; '.join(frase_peca(x) for x in xs) + '.'
    z = sum(1 for x in xs if esperado_peca(x)[0] == 'zero')
    r = ([('%d %s' % (z, 'zerada' if z == 1 else 'zeradas'))] if z else []) + (['%d no mínimo ou abaixo' % (len(ps) - z)] if len(ps) - z else [])
    if not ps:
        return '%d cadastradas, todas acima do mínimo.' % len(xs)
    return '%d cadastradas — %s: %s%s.' % (len(xs), ' e '.join(r), '; '.join(frase_peca(x) for x in ps[:3]), (' e mais %d' % (len(ps) - 3)) if len(ps) > 3 else '')


def grupo_pecas(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        pg.evaluate("() => { localStorage.removeItem('capitao.pecas.v1'); return new Promise(r => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); }); }")
        res = pg.evaluate(JS_P3C_CHAVES, [[q] for q, _, _ in ROTAS_P3E_F22])
        ruins = [(q, esp, ia_esp, key, ia) for (q, esp, ia_esp), (key, ia) in zip(ROTAS_P3E_F22, res) if key != esp or ia != ia_esp]
        ped('pecas: as %d perguntas de estoque (e as que ela não rouba: reparo, vida útil, a peça que quebrou, o estoque de água) caem na chave certa; a de estoque é local' % len(ROTAS_P3E_F22), not ruins, ruins[:6])
        x = pg.evaluate(JS_PECAS)
        base = {p['id']: p for p in x['base']}
        # (1) a lista: 12 peças da base com a quantidade da base, o nível e a situação (zerada, abaixo do mínimo, no mínimo); sem código de fabricante, sem R$
        ped('pecas: a lista sem movimento é a base gerada (12 peças, a quantidade da base) com o nível e a situação de cada uma',
            len(x['lista0']) == 12 and all(p['qtd'] == base[p['id']]['qtd'] and p['min'] == base[p['id']]['min'] and (p['nivel'], p['st']) == esperado_peca(base[p['id']]) and p['base'] is True for p in x['lista0']), x['lista0'][:2])
        ped('pecas: o contrato (§1.20): o rotor da bomba de água salgada está em 1 de mínimo 2 (abaixo) e o rotor do gerador em 0 de mínimo 1 (zerada)',
            (base['p03']['qtd'], base['p03']['min'], base['p05']['qtd'], base['p05']['min']) == (1, 2, 0, 1) and esperado_peca(base['p03']) == ('baixa', 'ABAIXO DO MÍNIMO') and esperado_peca(base['p05']) == ('zero', 'ZERADA'), (base['p03'], base['p05']))
        t = x['todas']
        # (revisão 4) a 1ª linha, a falada, nomeia as peças zeradas e no mínimo (até 3) com a quantidade a bordo: «quais estão zeradas?» não responde só a contagem
        quer = 'Peças a bordo: ' + corpo_pecas(x['base'])
        linhas = t['text'].split('\n')[1:]
        ordem = {'zero': 0, 'baixa': 1, 'ok': 2}
        nivs = [esperado_peca(next(p for p in x['base'] if p['n'] == l[2:].split(' · ')[0]))[0] for l in linhas]
        ped('pecas: a resposta abre com o total, quantas estão zeradas e no mínimo ou abaixo E QUAIS (até 3, com a quantidade a bordo: «rotor do gerador, 0 a bordo, zerada, mínimo 1»), uma linha por peça, as zeradas e as no mínimo primeiro', t['key'] == 'pecas' and t['text'].split('\n')[0] == quer and len(linhas) == 12 and nivs == sorted(nivs, key=lambda n: ordem[n]), (t['text'].split('\n')[0], quer, nivs))
        ped('pecas: cada linha traz o nome, a quantidade a bordo, o mínimo e o local; as não-ok trazem a situação; a ZERADA é a do rotor do gerador',
            all(re.match(r'^• .+ · \d+ a bordo · mínimo \d+ · .+', l) for l in linhas) and any(l.startswith('• Rotor (impeller) do gerador · 0 a bordo') and '— ZERADA' in l for l in linhas), linhas[:2])
        ped('pecas: a linha da peça ligada a uma tarefa traz a tarefa e o prazo de hoje («para: Troca de óleo e filtros dos motores (D-17 · 20/11)»)',
            any(l.startswith('• Filtro de óleo do motor') and re.search(r'para: Troca de óleo e filtros dos motores \((?:D-\d+ · \d\d/\d\d|em atraso há \d+ dias?)\)', l) for l in linhas), [l for l in linhas if 'Filtro de óleo do motor' in l])
        g = x['gerador']
        ped('pecas: a pergunta que cita a tarefa («peças da revisão do gerador») lista só as peças dela, com a tarefa, e a 1ª linha diz qual peça e quantas há a bordo', g['key'] == 'pecas'
            and g['text'].split('\n')[0] == 'Peças para revisão do gerador — óleo e filtros: ' + corpo_pecas([base['p06']]) and len(g['text'].split('\n')) == 2 and 'Filtro de óleo do gerador' in g['text'], g['text'][:200])
        cl = x['clima']
        ped('pecas: «peças para o filtro da climatização» abre com a tela do filtro e a quantidade (1 a bordo, no mínimo)', cl['key'] == 'pecas' and cl['text'].split('\n')[0].startswith('Peças para limpeza do filtro de água salgada da climatização: ')
            and cl['text'].split('\n')[0].endswith(corpo_pecas([base['p09']])) and 'tela do filtro de água salgada da climatização, 1 a bordo, no mínimo.' in cl['text'].split('\n')[0], cl['text'].split('\n')[0])
        r_ = x['rotor']
        ped('pecas: a pergunta que cita a peça pelo nome («tem rotor sobressalente?») lista as peças com esse nome (as duas, com a zerada primeiro)',
            r_['text'].split('\n')[0] == 'Estoque de peças: ' + corpo_pecas([base['p03'], base['p05']]) and r_['text'].split('\n')[1].startswith('• Rotor (impeller) do gerador'), r_['text'][:240])
        ped('pecas: a 1ª linha (a falada) diz QUAL peça e QUANTAS há («rotor do gerador, 0 a bordo, zerada, mínimo 1; rotor da bomba…, 1 a bordo, abaixo do mínimo de 2») e a hora do instante; nunca «com esse nome»',
            'rotor do gerador, 0 a bordo, zerada, mínimo 1' in r_['fala'] and 'rotor da bomba de água salgada dos motores, 1 a bordo, abaixo do mínimo de 2' in r_['fala'] and '12:01:00' in r_['fala'] and 'esse nome' not in r_['text'] + r_['fala'], r_['fala'])
        ped('pecas: o nome que nenhuma peça tem («peças do guincho») diz qual nome (como foi escrito) e mostra a lista inteira', x['guincho']['text'].startswith('Nenhuma peça cadastrada com «guincho» no nome. Peças a bordo: 12 cadastradas'), x['guincho']['text'][:120])
        # (revisão) a pergunta de estoque sem nome (verbo, contexto, lugar) não inventa um nome: abre com «Peças a bordo: 12 cadastradas…» e nunca com «Nenhuma peça cadastrada»
        ruins = [(q, t['text'].split('\n')[0][:80]) for q, t in x['genericas'] if not (t['key'] == 'pecas' and t['text'].split('\n')[0] == quer and len(t['text'].split('\n')) == 13)]
        ped('pecas: as %d perguntas de estoque sem nome (quais peças preciso repor, preciso de peças, vou precisar na revisão, cadê as peças, onde guardamos, usei uma peça, falta alguma peça…) abrem com o total e a lista inteira, sem «Nenhuma peça cadastrada com…»' % len(x['genericas']), not ruins, ruins[:3])
        # (revisão) a pergunta que cita a peça pelo nome (sem a palavra «peças») lista só as que casam MAIS palavras do nome: o rotor do gerador, não o filtro do gerador nem o rotor da bomba
        nm = x['nomes']
        ped('pecas: «quantos rotores do gerador temos?» lista só o rotor do gerador (1 zerada); «temos filtro de óleo a bordo?» e «quantos filtros de óleo temos?», os dois filtros de óleo; «quantos anodos temos a bordo?», os dois anodos; «tem rotor de reposição?», os dois rotores',
            nm['rotorGerador']['text'].split('\n')[0] == 'Estoque de peças: ' + corpo_pecas([base['p05']]) and len(nm['rotorGerador']['text'].split('\n')) == 2 and nm['rotorGerador']['text'].split('\n')[1].startswith('• Rotor (impeller) do gerador · 0 a bordo')
            and all(nm[k]['text'].split('\n')[0] == 'Estoque de peças: ' + corpo_pecas([p for p in x['base'] if p['n'] in esp]) and sorted(l[2:].split(' · ')[0] for l in nm[k]['text'].split('\n')[1:]) == sorted(esp) for k, esp in (
                ('filtroOleo', ['Filtro de óleo do gerador', 'Filtro de óleo do motor']), ('filtroOleo2', ['Filtro de óleo do gerador', 'Filtro de óleo do motor']),
                ('anodos', ['Anodo do trocador de calor do estabilizador', 'Jogo de anodos do eixo e do casco']), ('rotorReposicao', ['Rotor (impeller) da bomba de água salgada dos motores', 'Rotor (impeller) do gerador']))), [(k, v['text'][:100]) for k, v in nm.items()])
        ped('pecas: o nome que a pessoa digitou só é repetido se o app o conhece como coisa de bordo («guincho», «radar»; «guincho amarelo» repete só o «guincho»); «fictícias», «simuladas», um telefone ou uma palavra desconhecida abrem direto com a lista, sem «Nenhuma peça cadastrada…»',
            all(t['text'].split('\n')[0] == quer for t in (x['eco'][0], x['eco'][2])) and x['eco'][1]['text'].startswith('Nenhuma peça cadastrada com «guincho» no nome. Peças a bordo: 12')
            and x['eco'][3]['text'].startswith('Nenhuma peça cadastrada com «guincho» no nome. Peças a bordo: 12')
            and x['eco'][4]['text'].startswith('Nenhuma peça cadastrada com «radar» no nome. Peças a bordo: 12') and x['eco'][5]['text'].startswith('Nenhuma peça cadastrada com «guincho» no nome. Peças a bordo: 12')
            and not any(re.search(r'fict|simul|99999|amarelo', t['text'] + t['src'] + t['fala'], re.I) for t in x['eco']), [t['text'][:90] for t in x['eco']])
        ped('pecas: «tela» sozinha não é a tela do filtro (a do plotter, a do radar): «peças da tela do plotter» repete só o «plotter» e não lista a tela do filtro; «falta tela do filtro?» lista só ela',
            x['nomes']['telaPlotter']['text'].startswith('Nenhuma peça cadastrada com «plotter» no nome. Peças a bordo: 12') and 'tela' not in x['nomes']['telaPlotter']['text'].split('\n')[0].lower()
            and x['nomes']['telaFiltro']['text'].split('\n')[0] == 'Estoque de peças: ' + corpo_pecas([base['p09']]) and len(x['nomes']['telaFiltro']['text'].split('\n')) == 2, (x['nomes']['telaPlotter']['text'][:100], x['nomes']['telaFiltro']['text'][:100]))
        ped('pecas: o singular e o plural casam («fusível» e «fusíveis»): as duas perguntas listam o jogo de fusíveis de 24 V, na 1ª linha com a quantidade a bordo; «acabou o rotor?» lista os dois rotores',
            all(x['nomes'][k]['key'] == 'pecas' and x['nomes'][k]['text'].split('\n')[0] == 'Estoque de peças: ' + corpo_pecas([base['p11']]) for k in ('fusivel', 'fusivelSing'))
            and x['nomes']['zerou']['text'].split('\n')[0] == 'Estoque de peças: ' + corpo_pecas([base['p03'], base['p05']]), (x['nomes']['fusivel']['text'][:100], x['nomes']['zerou']['text'][:100]))
        f5 = [p for p in x['base'] if 'filtro' in p['n'].lower()]
        ped('pecas: a lista longa («quantos filtros temos?», 5 cadastradas) abre com o total e nomeia as peças no mínimo ou abaixo, com a quantidade; o texto traz as 5 linhas',
            len(f5) == 5 and x['nomes']['filtros5']['text'].split('\n')[0] == 'Estoque de peças: ' + corpo_pecas(f5) and len(x['nomes']['filtros5']['text'].split('\n')) == 6 and '5 cadastradas — 2 no mínimo ou abaixo: ' in x['nomes']['filtros5']['text'], x['nomes']['filtros5']['text'].split('\n')[0])
        ped('pecas: «tem filtro de combustível a bordo?» lista o filtro de combustível (o combustível não tira a pergunta da peça cadastrada), com a quantidade na 1ª linha', nm['filtroComb']['text'].split('\n')[0] == 'Estoque de peças: ' + corpo_pecas([base['p02']]) and 'Filtro de combustível' in nm['filtroComb']['text'], nm['filtroComb']['text'][:120])
        ruins = []
        for (q, ids), (_, r) in zip(DESEMPATE_PECAS, x['desempate']):
            linhas_r = r['text'].split('\n')
            if not (r['key'] == 'pecas' and linhas_r[0] == 'Estoque de peças: ' + corpo_pecas([base[i] for i in ids]) and len(linhas_r) == 1 + len(ids) and r['ia'] is False):
                ruins.append((q, linhas_r[0][:110]))
        ped('pecas (revisão 4): o qualificador «para o motor / no motor / para o gerador» não empata com o nome da peça: a correia, a escova, o fusível, os anodos, o rotor e o filtro do gerador saem sozinhos (a 1ª linha, a falada, fala da peça pedida)', not ruins, ruins)
        ruins = [(q, r['text'].split('\n')[0][:90]) for q, r in x['zeradas'] if not (r['key'] == 'pecas' and r['text'].split('\n')[0] == quer and len(r['text'].split('\n')) == 13 and r['ia'] is False
                                                                                  and 'rotor do gerador, 0 a bordo, zerada, mínimo 1' in r['fala'] and '12:01:00' in r['fala'])]   # (a fala não lê o que está entre parênteses: «rotor do gerador»)
        ped('pecas (revisão 4): «que peça acabou?», «qual peça acabou?», «alguma peça acabou?», «acabou alguma peça?», «tem peça zerada?», «quais peças estão zeradas?», «falta alguma peça?» e «preciso repor alguma peça?» são o estoque inteiro, local, e a fala nomeia a peça zerada (rotor do gerador, 0 a bordo)', not ruins, ruins)
        ruins = []
        for (q, ids), (_, r) in zip(ESTADO_NOME_PECAS, x['estadoNome']):
            l1 = r['text'].split('\n')[0]
            certo = (l1 == 'Estoque de peças: ' + corpo_pecas([base[i] for i in ids])) if ids else (l1.startswith('Peças para ') and l1.endswith(': ' + corpo_pecas([base['p05']])))
            if not (r['key'] == 'pecas' and certo and r['ia'] is False and ('rotor do gerador, 0 a bordo, zerada' in r['fala'] if 'gerador' in q else True)):
                ruins.append((q, l1[:110]))
        ped('pecas (revisão 4): a peça pelo nome com o estado dela («o rotor do gerador está zerado?», «o rotor já acabou?», «o filtro de óleo está no mínimo?», «preciso de rotor para o gerador») é o estoque dessa peça, local, com a quantidade a bordo na 1ª linha', not ruins, ruins)
        # a ficha da IA leva o estoque (só o total e as peças zeradas e no mínimo ou abaixo): a IA que recebe «que peça acabou?» sabe, e não responde de conhecimento geral
        fi = x['ficha']
        bl = re.search(r'## Peças\n(.*?)\n\n## ', fi, re.S)
        nao_ok = [p_ for p_ in x['base'] if esperado_peca(p_)[0] != 'ok']
        quer_f = '12 peças cadastradas — 1 zerada e 5 no mínimo ou abaixo:\n' + '\n'.join('• %s: %d a bordo, mínimo %d — %s' % (p_['n'], p_['qtd'], p_['min'], esperado_peca(p_)[1]) for p_ in nao_ok) + '\n(Fonte: estoque de peças a bordo · cadastro do app)'
        ped('pecas (revisão 4): a ficha da IA traz o bloco «## Peças» logo depois da Manutenção, com o total e só as peças zeradas e no mínimo ou abaixo (quantidade a bordo e mínimo) e a fonte', bool(bl) and bl.group(1) == quer_f
            and fi.index('## Manutenção') < fi.index('## Peças') < fi.index('## Horímetros') and not re.search(r'R\$|\bPN\b', bl.group(1)), (bl.group(1)[:200] if bl else None, quer_f[:200]))
        ped('pecas: nenhuma peça é de salvatagem nem tem código de fabricante, preço ou R$; a resposta é local (nunca à IA)',
            not re.search(r'R\$|preço|\bPN\b|código|colete|balsa|extintor|sinalizador', x['todas']['text'] + x['gerador']['text'] + x['rotor']['text']) and not any(r['ia'] for r in (x['todas'], x['gerador'], x['rotor'], x['guincho'], x['clima'])), x['todas']['text'][:80])
        for r in (x['todas'], x['gerador'], x['rotor']):
            tudo = r['text'] + '\n' + r['src'] + '\n' + r['fala']
            ruim = [(n, m.group(0)) for n in VARREDURA for m in [RX[n].search(tudo)] if m]
            ped('pecas: nenhuma regex do §3 casa o texto, a fonte nem a fala, e a fonte e a fala dizem a hora do instante (12:01:00)', not ruim and not confere.R_COORD.search(tudo) and '12:01:00' in r['src'] + r['fala'] and '(' not in r['fala'], (ruim, r['fala']))
        ped('pecas: perguntar não grava (o chat só lê): a chave capitao.pecas.v1 continua ausente depois das 5 respostas', x['semEscrita'] is True, '')
        # (2) −1 USADA: 4 → 0; a 5ª não existe; cada uso é um movimento novo de −1 (sim true na simulação); a base gerada não muda
        us = x['us']
        ped('pecas: o −1 USADA tira uma por vez do p01 (4 → 3 → 2 → 1 → 0) e devolve {id, ant, novo, iso}; a 5ª, com a peça zerada, devolve null',
            [(u['ant'], u['novo']) for u in us[:4]] == [(4, 3), (3, 2), (2, 1), (1, 0)] and all(u['id'] == 'p01' and u['iso'] for u in us[:4]) and us[4] is None, us)
        ped('pecas: cada −1 USADA é um movimento novo {id, dq: -1, iso, who, sim: true} (4 linhas), com iso único; a quantidade é a da base mais a soma (0, ZERADA)',
            len(x['movs1']) == 4 and all(m['id'] == 'p01' and m['dq'] == -1 and m['sim'] is True and m['who'] and m['iso'] for m in x['movs1']) and len({m['iso'] for m in x['movs1']}) == 4
            and x['q1']['qtd'] == 0 and x['q1']['nivel'] == 'zero' and x['q1']['st'] == 'ZERADA', (x['movs1'][:1], x['q1']))
        ped('pecas: a peça já zerada (p05) e a que não existe não gravam nada (null, sem movimento novo: seguem as 5 linhas)', x['zerada'] is None and x['desconhecida'] is None and x['movsZerada'] == 5 and x['movsDesc'] == 5, (x['zerada'], x['movsZerada']))
        # (3) Desfazer: um movimento NOVO (+1) e só se a quantidade ainda é a que o −1 deixou; o desfazer de um uso antigo (a quantidade já mudou) recusa
        ped('pecas: o Desfazer de um −1 antigo (a quantidade já mudou depois dele) recusa e não grava', x['desfazAntigo'] is None and x['movsAntigo'] == 4, (x['desfazAntigo'], x['movsAntigo']))
        ped('pecas: o Desfazer do último −1 devolve a unidade com um movimento NOVO de +1 (5 linhas, as 4 primeiras iguais), e a quantidade volta a 1',
            x['desfaz'] and x['desfaz']['qtd'] == 1 and len(x['movs2']) == 5 and x['movs2'][:4] == x['movs1'] and x['movs2'][4]['dq'] == 1 and x['movs2'][4]['id'] == 'p01' and x['q2']['qtd'] == 1, (x['desfaz'], x['movs2'][4:]))
        ped('pecas: usar ×4 e desfazer 1 soma certo (base 4 + (−1 ×4) + 1 = 1) e a base gerada nunca é mutada', x['q2']['qtd'] == base['p01']['qtd'] + sum(m['dq'] for m in x['movs2'] if m['id'] == 'p01') and x['depois'] is True, (x['q2'], x['depois']))
        # (4) ajuste (o ✎ da tela): a diferença como movimento; número inválido recusa
        ped('pecas: o ajuste da quantidade (7) grava a diferença como movimento e recusa -1, 1000, texto, o mesmo número e peça inexistente',
            x['ajuste'] and x['ajuste']['qtd'] == 7 and x['q3']['qtd'] == 7 and x['ajRuim'] == [None] * 5 and any(m['id'] == 'p02' and m['dq'] == 7 - base['p02']['qtd'] for m in x['estado']['movs']), (x['ajuste'], x['ajRuim']))
        # (5) + PEÇA: nome limpo, números inteiros, tarefa que existe, sem pn nem valor; fica em `novas`, com o mesmo −1 USADA
        n = x['nova']
        ped('pecas: + PEÇA cadastra em `novas` (nome sem espaço dobrado, inteiros, só a tarefa da agenda que existe), sem código de fabricante nem valor, com sim e id que não colide com a base',
            n and n['n'] == 'Fusível 10 A' and n['qtd'] == 5 and n['min'] == 2 and n['local'] == 'armário de ferramentas' and n['tarefas'] == ['baterias'] and 'pn' not in n and 'preco' not in n and n['sim'] is True and n['id'] not in base
            and x['estado']['novas'] == [n], n)
        ped('pecas: + PEÇA sem nome (vazio, objeto vazio, null) não cadastra', x['novaRuim'] == [None] * 3 and len(x['estado']['novas']) == 1, x['novaRuim'])
        ped('pecas: a peça nova entra na lista (base false) e aceita o −1 USADA (5 → 4)', x['usaNova'] and (x['usaNova']['ant'], x['usaNova']['novo']) == (5, 4) and x['qNova']['qtd'] == 4 and x['qNova']['base'] is False and len(x['lista1']) == 13, (x['usaNova'], x['qNova']))
        ped('pecas: depois dos usos a resposta já fala da peça zerada do p01 e da nova (13 cadastradas), e o registro só cresceu (os movimentos anteriores intactos)',
            x['respDepois']['text'].startswith('Peças a bordo: 13 cadastradas') and 'Fusível 10 A · 4 a bordo' in x['respDepois']['text'] and x['estado']['movs'][:5] == x['movs2'], x['respDepois']['text'][:90])
        ped('pecas: o iso de cada movimento é único (o dados.html soma pelo iso)', len(x['isos']) == len(set(x['isos'])) and len(x['isos']) == len(x['estado']['movs']), x['isos'])
    finally:
        pg.ctx.close()
    # (revisão 3) o eco passa pelo §3 mesmo com a palavra no vocabulário do app: com «indisponível», «simulada», «fictícia» e «demonstração» entre as palavras de um equipamento (dado adulterado), a resposta não as repete
    pg = pagina(b, muta=muta)
    try:
        r = pg.evaluate("""() => { const B = window.CapitaoBrain, D = window.CapitaoDados; D.equipamentos[0].palavras = D.equipamentos[0].palavras.concat(['indisponível', 'simulada', 'fictícia', 'demonstração', 'leitura', 'fixa', 'cadê', 'usei', 'precisam', 'ficam']);
          return ['peças indisponível', 'peças simulada', 'peças fictícia', 'peças demonstração', 'peças indisponível do guincho', 'peças leitura fixa', 'cadê as peças?', 'usei uma peça do estoque',
                  'quais peças precisam de reposição?', 'onde ficam as peças sobressalentes?'].map((q) => { const a = B.answer(q, { platform: 'app', commit: false }); return [a.key, a.text.split('\\n')[0]]; }); }""")
        ped('pecas: o eco do nome passa pelo §3 e pelo vocabulário que o app não repete: «indisponível», «simulada», «fictícia», «demonstração», «leitura fixa» e as palavras de estoque («cadê», «usei», «precisam», «ficam») nunca são repetidas, mesmo como palavra de equipamento; «guincho» é',
            all(k == 'pecas' for k, _ in r) and all(l.startswith('Peças a bordo: ') for _, l in r[:4]) and r[4][1].startswith('Nenhuma peça cadastrada com «guincho» no nome. ') and r[5][1].startswith('Peças a bordo: ')
            and all(l.startswith('Peças a bordo: ') for _, l in r[6:]) and not any(re.search(r'indispon|simulad|fict|demonstra|leitura|cadê|usei|precisam|ficam', l) for _, l in r), r)
    finally:
        pg.ctx.close()
    # (revisão 4) o inteiro PURO: «1e2», «12abc», «3.7», «1,5», «-1», «0x10», vazio, número com fração e o que não é número são recusados sem gravar (o <input type=number> aceita «1e2»); o + PEÇA com
    # quantidade ou mínimo que não é inteiro puro recusa o cadastro todo; vazio ou ausente vale 0
    pg = pagina(b, muta=muta)
    try:
        r = pg.evaluate("""() => { const B = window.CapitaoBrain, K = 'capitao.pecas.v1', est = () => JSON.parse(localStorage.getItem(K) || '{}'), tam = () => (est().movs || []).length + (est().novas || []).length;
          const ruins = ['1e2', '12abc', '3.7', '1,5', '-1', '0x10', '1 2', '', '   ', '1000', '+5', '5.', '١٢', 1.5, 3.7, 1000, -1, NaN, Infinity, true, null, undefined, [], {}];
          localStorage.removeItem(K); const ajRuim = ruins.map((v) => [String(v), B.ajustaPeca('p04', v)]), movsRuim = tam();
          const bons = [[' 7 ', 7], ['07', 7], ['007', 7], [7, 7], ['0', 0], [0, 0], ['999', 999], [999, 999], ['\\t5\\n', 5]].map(([v, esp]) => { localStorage.removeItem(K); const a = B.ajustaPeca('p04', v); return [String(v), esp, a && a.qtd]; });
          localStorage.removeItem(K);
          const nRuim = [{ n: 'Peça A', qtd: '1e2' }, { n: 'Peça A', qtd: '12abc' }, { n: 'Peça A', min: '3.7' }, { n: 'Peça A', qtd: 3.7 }, { n: 'Peça A', min: -1 }, { n: 'Peça A', qtd: 1000 }, { n: 'Peça A', qtd: true }, { n: 'Peça A', qtd: [] }].map((c) => B.addPeca(c));
          const movsNovas = tam();
          const nBom = [{ n: 'Peça B' }, { n: 'Peça C', qtd: '', min: null }, { n: 'Peça D', qtd: ' 5 ', min: '2' }, { n: 'Peça E', qtd: 0, min: 0 }].map((c) => { const a = B.addPeca(c); return a && [a.qtd, a.min]; });
          return { ajRuim, movsRuim, bons, nRuim, movsNovas, nBom, depois: tam() }; }""")
        ped('pecas (revisão 4): o ajuste da quantidade recusa «1e2», «12abc», «3.7», «1,5», «-1», «0x10», o vazio, o número com fração (1.5, 3.7), o NaN e o que não é número — null, sem gravar movimento algum',
            all(v is None for _, v in r['ajRuim']) and len(r['ajRuim']) == 24 and r['movsRuim'] == 0, [x_ for x_ in r['ajRuim'] if x_[1] is not None])
        ped('pecas (revisão 4): o ajuste aceita o inteiro puro de 0 a 999 (com espaço nas pontas, com zeros à esquerda ou como número): 7, 0, 999', all(q == esp for _, esp, q in r['bons']) and len(r['bons']) == 9, r['bons'])
        ped('pecas (revisão 4): o + PEÇA com quantidade ou mínimo que não é inteiro puro (1e2, 12abc, 3.7, 3.7 número, -1, 1000, true, lista) recusa o cadastro todo (null) e não grava', all(v is None for v in r['nRuim']) and r['movsNovas'] == 0, (r['nRuim'], r['movsNovas']))
        ped('pecas (revisão 4): o + PEÇA sem quantidade nem mínimo (ausente, vazio, null) cadastra com 0 e 0; «5» com espaço e «2» valem; 0 vale', r['nBom'] == [[0, 0], [0, 0], [5, 2], [0, 0]] and r['depois'] == 4, (r['nBom'], r['depois']))
    finally:
        pg.ctx.close()
    # (revisão 4) a ficha com a simulacao false deixa de fora o estoque que tem `sim: true` (o bloco «## Peças» lê o semSim)
    pg = pagina(b, muta=muta)
    try:
        r = pg.evaluate("""() => { const B = window.CapitaoBrain, D = window.CapitaoDados, K = 'capitao.pecas.v1'; localStorage.removeItem(K); B.usaPeca('p06');
          const bloco = (f) => { const m = f.match(/## Peças\\n([\\s\\S]*?)\\n\\n## /); return m ? m[1] : ''; }, com = bloco(B.ficha('app', 'qualquer pergunta', null)); D.simulacao = false; const sem = bloco(B.ficha('app', 'qualquer pergunta', null)); D.simulacao = true; return { com, sem }; }""")
        ped('pecas (revisão 4): na ficha, o filtro de óleo do gerador usado com a simulação (2 → 1, no mínimo) aparece «1 a bordo, mínimo 1 — NO MÍNIMO»; com a simulacao false o movimento `sim: true` fica de fora (o filtro volta a 2, acima do mínimo, e sai da lista)',
            'Filtro de óleo do gerador: 1 a bordo, mínimo 1 — NO MÍNIMO' in r['com'] and 'Filtro de óleo do gerador' not in r['sem'] and r['sem'].startswith('12 peças cadastradas — 1 zerada e 5 no mínimo ou abaixo:'), r)
    finally:
        pg.ctx.close()
    # modo real: a linha não leva `sim`; sem a simulação a ficha deixa de fora o que tem sim (semSim); JSON ruim no aparelho vale como vazio
    pg = pagina(b, extra=SEM_SIMULACAO, muta=muta)
    try:
        r = pg.evaluate("""() => { const B = window.CapitaoBrain; localStorage.removeItem('capitao.pecas.v1'); const u = B.usaPeca('p01'), m = JSON.parse(localStorage.getItem('capitao.pecas.v1')).movs[0]; return { u, m, q: B.pecas().filter((x) => x.id === 'p01')[0].qtd }; }""")
        ped('pecas (simulacao false): o −1 USADA grava a linha sem `sim`', r['u'] and 'sim' not in r['m'] and r['m']['dq'] == -1 and r['q'] == 3, r)
    finally:
        pg.ctx.close()
    pg = pagina(b, muta=muta)
    try:
        r = pg.evaluate("""() => { const B = window.CapitaoBrain, D = window.CapitaoDados; localStorage.removeItem('capitao.pecas.v1'); B.usaPeca('p01'); B.addPeca({ n: 'Peça do teste', qtd: 3 });
          const com = B.pecas().length, sim = B.pecas().filter((x) => x.id === 'p01')[0].qtd; D.simulacao = false; const sem = B.pecas({ semSim: true }), cheia = B.pecas();
          return { com, sim, sem: sem.length, qSem: sem.filter((x) => x.id === 'p01')[0].qtd, cheia: cheia.length }; }""")
        ped('pecas: com simulacao false a ficha (semSim) deixa de fora a peça e o movimento com sim: a quantidade volta a da base; a lista de tela (sem semSim) segue completa', r == {'com': 13, 'sim': 3, 'sem': 12, 'qSem': 4, 'cheia': 13}, r)
        bons = pg.evaluate("""() => { const B = window.CapitaoBrain, o = [];
          ['[]', 'null', '"texto"', '{"movs":"x","novas":3}', '{"movs":[null,1,{"id":"p01"},{"id":"p01","dq":"a"}],"novas":[null,{"id":"x"}]}', 'não é json'].forEach((v) => { localStorage.setItem('capitao.pecas.v1', v); o.push([B.pecas().length, B.pecas().filter((x) => x.id === 'p01')[0].qtd]); });
          return o; }""")
        ped('pecas: JSON de outra forma ou item sem forma no aparelho vale como vazio (12 peças da base, p01 em 4) e nunca lança', bons == [[12, 4]] * 6, bons)
    finally:
        pg.ctx.close()
    # o SOS: nenhuma peça, nenhuma gravação
    pg = pagina(b, scripts=('capitao-dados.js', 'capitao-brain.js'), caminho='SOS-cerebro.html', fixo=None, muta=muta)
    try:
        r = pg.evaluate("() => { const B = window.CapitaoBrain; localStorage.removeItem('capitao.pecas.v1'); return { n: B.pecas().length, u: B.usaPeca('p01'), a: B.addPeca({ n: 'x' }), k: localStorage.getItem('capitao.pecas.v1'), t: B.answer('quais peças temos a bordo?', { platform: 'app', commit: false }).text, f: B.ficha('app') }; }")
        ped('pecas (SOS): nenhuma peça, o −1 USADA e o + PEÇA não fazem nada, nada é gravado e a ficha não tem o bloco «## Peças»', r['n'] == 0 and r['u'] is None and r['a'] is None and r['k'] is None and 'Rotor' not in r['t'] and '## Peças' not in r['f'], r)
    finally:
        pg.ctx.close()


GRUPOS_3A['pecas'] = grupo_pecas
MUTANTES_3E_F22 = [
    ('p3e pecas: o −1 USADA não grava o movimento', "    m = pecaMov(id, -1);\n    return { id: id, ant: p.qtd, novo: p.qtd - 1, iso: m.iso };", "    m = { iso: 'x' };\n    return { id: id, ant: p.qtd, novo: p.qtd - 1, iso: m.iso };", ('pecas',)),
    ('p3e pecas: o Desfazer aceita a quantidade que mudou depois', "p.qtd !== u.novo || u.ant === u.novo) return null;", "u.ant === u.novo) return null;", ('pecas',)),
    ('p3e pecas: a quantidade ignora os movimentos', "(soma[x.id] || 0))), mn =", "0)), mn =", ('pecas',)),
    ('p3e pecas: a peça no mínimo não conta como baixa', "return q <= 0 ? 'zero' : mn > 0 && q <= mn ? 'baixa' : 'ok'; }", "return q <= 0 ? 'zero' : mn > 0 && q < mn ? 'baixa' : 'ok'; }", ('pecas',)),
    ('p3e pecas: o −1 USADA deixa a peça zerada ir a menos', "if (!p || !(p.qtd > 0)) return null;\n    m = pecaMov(id, -1);", "if (!p) return null;\n    m = pecaMov(id, -1);", ('pecas',)),
    ('p3e pecas: as zeradas não vêm primeiro', "ord = { zero: 0, baixa: 1, ok: 2 }, linha", "ord = { zero: 2, baixa: 1, ok: 0 }, linha", ('pecas',)),
    ('p3e pecas: o movimento sem o carimbo sim', "function selaSim() { return sim() ? { sim: true } : {}; }", "function selaSim() { return {}; }", ('pecas',)),
    ('p3e pecas: o movimento repete o iso', "do { iso = new Date(t++).toISOString(); } while (movs.some(function (x) { return x && x.iso === iso; }));", "iso = new Date(t).toISOString();", ('pecas',)),
    ('p3e pecas: a rota do estoque sai', "    if (pecasPergunta(q)) return 'pecas';", "", ('pecas',)),
    ('p3e pecas: o + PEÇA aceita a tarefa que não existe', "Array.isArray(c.tarefas) && c.tarefas.filter(function (t) { return ag[t]; }).length ? { tarefas: c.tarefas.filter(function (t) { return ag[t]; }).slice(0, 10) } : {}", "Array.isArray(c.tarefas) && c.tarefas.length ? { tarefas: c.tarefas.slice(0, 10) } : {}", ('pecas',)),
    ('p3e pecas: o SOS lê as peças', "    if (EM_SOS) return [];\n    est = pecasEstado();", "    est = pecasEstado();", ('pecas',)),
    # (revisão) a trava 10 (o equipamento de segurança), o dinheiro, o prazo, o estoque pelo nome, o estoque sem nome, a posição
    ('p3e pecas: o preço e a compra das peças vão para o estoque', r"' preco ', ' precos ', ' valor ', ' valores ', 'custa', 'r$', 'comprar', ' compra ', ' compro ', 'cotacao', 'orcamento', ' reais '];", r"'cotacao', 'orcamento', ' reais '];", ('pecas',)),
    ('p3e pecas: a idade e o prazo da peça vão para o estoque', r"'quanto tempo', 'desde quando', 'quando troc', 'quando subst', 'ultima troca', 'temos que ', ' tem que ', ' tenho que ', 'quanto falta', ' falta para ', ' faltam para ', 'o que falta para', 'falta muito', 'falta troc', 'faltam troc', 'falta a troca', 'falta fazer', 'falta inspec', 'falta revis',", r"'desde quando', 'ultima troca',", ('pecas',)),
    ('p3e pecas: o «temos que trocar» vai para o estoque', r"'temos que ', ' tem que ', ' tenho que ',", r"", ('pecas',)),
    ('p3e pecas: o estoque pelo nome da peça sai', "function pecasNomePede(q) {\n    return (", "function pecasNomePede(q) {\n    return false && (", ('pecas',)),
    ('p3e pecas: «falta / acabou / zerou» + qualquer palavra com nome de peça no resto da frase vira o estoque (a peça não precisa ser o objeto do verbo)', r"&& objetoPeca(q, PECAS_VERBOS_FALTA));", r"&& nomeCadastrado(q));", ('pecas',)),
    ('p3e pecas: «quantos X … temos» com a peça em qualquer lugar da frase vira o estoque («quanta água tem no filtro?»)', r"&& objetoPeca(q, PECAS_VERBOS_QUANT))", r"&& nomeCadastrado(q))", ('pecas',)),
    ('p3e pecas: «tem X … a bordo» com a peça em qualquer lugar da frase vira o estoque («tem fluxo de água no filtro a bordo?»)', r"de reposicao|de reserva|de sobressalente)/.test(q) && objetoPeca(q, PECAS_VERBOS_TEM))", r"de reposicao|de reserva|de sobressalente)/.test(q) && nomeCadastrado(q))", ('pecas',)),
    ('p3e pecas: o artigo entre o verbo e a peça barra o estoque («acabou o rotor?»)', r"var PECAS_ARTIGOS = ' o a os as um uma uns umas algum alguma alguns algumas mais outro outra outros outras de do da dos das estoque ';", r"var PECAS_ARTIGOS = ' ';", ('pecas',)),
    ('p3e pecas: «tela» sozinha (a do plotter, a do radar) é a tela do filtro', r"var PECAS_NUCLEO_FRACO = { tela: 'filtro' };", r"var PECAS_NUCLEO_FRACO = {};", ('pecas',)),
    ('p3e pecas: o singular e o plural da peça não casam («fusível»/«fusíveis»)', r"function radicalPeca(w) { return w.length > 4 ? w.replace(/([aeou])i$/, '$1l') : w; }", r"function radicalPeca(w) { return w; }", ('pecas',)),
    ('p3e pecas: telefone, contato, CNPJ, e-mail de oficina, fornecedor e técnico vão para o estoque', r"if (has(q, PECAS_FORA) || has(q, PECAS_CONTATO)) return false;", r"if (has(q, PECAS_FORA)) return false;", ('pecas',)),
    ('p3e pecas: «preciso/falta repor alguma coisa» sai', r"    return PECAS_REPOR.test(q) && (pecasPalavras(q).length === 0 || objetoPeca(q, ['repor']));", r"    return false;", ('pecas',)),
    ('p3e pecas: «preciso repor óleo» (nome que não é peça) vira o estoque', r"(pecasPalavras(q).length === 0 || objetoPeca(q, ['repor']));", r"true;", ('pecas',)),
    ('p3e pecas: o app repete qualquer palavra da pergunta («dizer», «atual», «indisponível», o e-mail), não só as que conhece como coisa de bordo', r"ws.filter(function (t) { return voc[t] === 1; })", r"ws.filter(function (t) { return true; })", ('pecas',)),
    ('p3e pecas: a 1ª linha da lista curta não diz qual peça nem quantas há', r"if (xs.length <= 3) return xs.map(frase).join('; ') + '.';", r"if (xs.length <= 3) return xs.length + ' cadastradas.';", ('pecas',)),
    ('p3e pecas: a 1ª linha da lista longa não nomeia as peças no mínimo ou abaixo', r"': ' + ps.slice(0, 3).map(frase).join('; ') +", r"'. ' +", ('pecas',)),
    ('p3e pecas: a 1ª linha não diz a peça zerada nem o mínimo', r"x.nivel === 'zero' ? ', zerada' + (x.min > 0 ? ', mínimo ' + x.min : '')", r"x.nivel === 'zero' ? ''", ('pecas',)),
    ('p3e pecas: a 1ª linha não diz o mínimo de quem está abaixo dele', r"(x.qtd < x.min ? ', abaixo do mínimo de ' + x.min : ', no mínimo')", r"', no mínimo'", ('pecas',)),
    ('p3e pecas: a pergunta que cita a tarefa abre só com o total', r"+ ': ' + corpo(lig)) + '\n'", r"+ ': ' + lig.length + ' cadastradas') + '\n'", ('pecas',)),
    ('p3e pecas: a pergunta que cita a peça abre só com o total', r": 'Estoque de peças: ' + corpo(nm.lista))", r": 'Estoque de peças: ' + nm.lista.length + ' cadastradas')", ('pecas',)),
    ('p3e pecas: a palavra sem coisa de bordo vira «Nenhuma peça cadastrada com esse nome» (a lista sem nada de palavra)', r"(nm.nome && nm.palavras.length ? 'Nenhuma peça cadastrada com «'", r"(nm.nome ? 'Nenhuma peça cadastrada com «'", ('pecas',)),
    ('p3e pecas: «alguma peça» não é pergunta de estoque', r"' alguma peca ',", r"", ('pecas',)),
    ('p3e pecas: sem a guarda do combustível, o «estoque de combustível» vira o das peças', "    if (has(q, PECAS_COMBUSTIVEL) && !nomeCadastrado(q)) return false;\n", "", ('pecas',)),
    ('p3e pecas: o combustível barra até o filtro de combustível cadastrado', r"if (has(q, PECAS_COMBUSTIVEL) && !nomeCadastrado(q)) return false;", r"if (has(q, PECAS_COMBUSTIVEL)) return false;", ('pecas',)),
    ('p3e pecas: a lista pelo nome traz toda peça que casa uma palavra (não só as que casam mais)', r"return pts[k] === max; }) : [] };", r"return pts[k] > 0; }) : [] };", ('pecas',)),
    ('p3e pecas: «precisam» é tomado por nome de peça (sem as raízes dos verbos de estoque)', r"var PECAS_GEN_RAIZES = ['precis', 'falt',", r"var PECAS_GEN_RAIZES = ['falt',", ('pecas',)),
    ('p3e pecas: «cadê» é tomado por nome de peça', r"guardar cade usei", r"guardar usei", ('pecas',)),
    ('p3e pecas: «usei» é tomado por nome de peça', r"cade usei usamos usou usado usada usadas usados uso usar", r"cade usamos usou usado usada usadas usados uso usar", ('pecas',)),
    ('p3e pecas: «onde ficam» é tomado por nome de peça', r"onde fica ficam guardamos", r"guardamos", ('pecas',)),
    ('p3e pecas: o app repete a palavra «simulada» ou «demonstração» do vocabulário', r"&& !/^(?:simul|fict|demo|invent|hipot|ilustr|exempl|roteir|laco|teste|snapshot)/.test(w)", r"", ('pecas',)),
    ('p3e pecas: o eco não passa cada palavra pelo §3 (a palavra «indisponível» do vocabulário é repetida)', r"&& !PECAS_ECO_TERMOS.some(function (k) { return TERMOS[k].test(w); });", r";", ('pecas',)),
    ('p3e pecas: o eco não passa o conjunto das palavras pelo §3 («leitura fixa» do vocabulário é repetida)', r"return l.length && !PECAS_ECO_TERMOS.some(function (k) { return TERMOS[k].test(l.join(' ')); }) ? l : [];", r"return l;", ('pecas',)),
    ('p3e pecas: «reposição» cai de novo na posição do barco', r"var POSICAO_VELHAS = [' posicao',", r"var POSICAO_VELHAS = ['posicao',", ('pecas',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3E_F22

# —— F09: checklists guiados ——
ROTAS_P3E_F09 = [
    ('checklist de saída', 'checklist', False), ('check list de saída', 'checklist', False), ('lista de verificação antes de sair', 'checklist', False), ('checklist de chegada', 'checklistChegada', False),
    ('checklist ao atracar', 'checklistChegada', False), ('checklist para chegar na marina', 'checklistChegada', False), ('checklist de fundeio', 'checklistFundeio', False), ('checklist ao fundear', 'checklistFundeio', False),
    ('lista de verificação de ancoragem', 'checklistFundeio', False), ('checklist de abastecimento', 'checklistAbastecimento', False), ('checklist para abastecer', 'checklistAbastecimento', False),
    # o que ela não rouba: a pergunta de chegada sem a palavra checklist segue como antes (P3C), a de fundeio sem a palavra checklist é a âncora, o diesel é a autonomia
    ('previsão de chegada do técnico da oficina', 'checklistChegada', False), ('âncora garrando?', 'ancora', False), ('quanto diesel tem?', 'autonomia', False),
    # (revisão 3) a trava 10: o EPIRB, o Seafire, o canal 16, o PAN-PAN e o DSC na pergunta do checklist são do equipamento (a instrução de segurança, local, sem a velocidade do quadro), nunca o checklist.
    # (revisão 4) o rádio e o VHF também: o cabecaEmerg é a união de TUDO o que a route() entrega às rotas de emergência (CANAL16_ROTA inclusive), então «checklist do rádio VHF» é o roteiro do canal 16, como «peças do rádio VHF»
    ('checklist de fundeio, onde fica o EPIRB?', 'epirb', False), ('checklist ao fundear, e o EPIRB?', 'epirb', False), ('checklist de fundeio com o EPIRB', 'epirb', False), ('checklist de fundeio e o canal 16', 'canal16', False),
    ('checklist do EPIRB', 'epirb', False), ('checklist do canal 16', 'canal16', False), ('checklist do sistema Seafire', 'seafire', False), ('checklist de chegada, pan-pan', 'canal16', False),
    ('checklist de saída e o EPIRB', 'epirb', False), ('checklist de saída, teste do DSC', 'canal16', False), ('checklist do rádio VHF', 'canal16', False),
    # (revisão 4) a cabeça de emergência em QUALQUER dos 4 checklists, nas duas ordens: o botão DISTRESS e a baliza do EPIRB (sem rota própria: o trecho de segurança deles, local), o abastecimento e a chegada
    # (que a rota do diesel e da autonomia tomava), e a Licença de Estação (papelada: docsvenc, nunca o checklist)
    ('o botão DISTRESS, checklist de saída', 'base', False), ('checklist de chegada, o botão DISTRESS', 'base', False), ('checklist de fundeio e o botão DISTRESS?', 'base', False), ('o botão DISTRESS, checklist de abastecimento', 'base', False),
    ('a baliza, checklist de saída', 'base', False), ('checklist de abastecimento, a baliza', 'base', False),
    ('onde fica o EPIRB, checklist de abastecimento', 'epirb', False), ('o sistema Seafire, checklist de abastecimento', 'seafire', False), ('o canal 16, checklist de abastecimento', 'canal16', False),
    ('pan-pan, checklist de abastecimento', 'canal16', False), ('a radiobaliza, checklist de abastecimento', 'epirb', False), ('checklist de abastecimento, onde fica o EPIRB', 'epirb', False),
    ('checklist de chegada, pan-pan', 'canal16', False), ('o DSC, checklist de chegada', 'canal16', False), ('a baliza do canal, checklist de saída', 'checklist', False),
    ('licença de estação do rádio, checklist de saída', 'docsvenc', False),
    # (revisão 4) «pronto para sair?» é o checklist de saída (era o item SK-02 do FAQ, sem dizer que é o Seakeeper); «pronto para sair hoje?» é a decisão
    ('pronto para sair?', 'checklist', False), ('estamos prontos para sair?', 'checklist', False), ('tudo pronto para largar?', 'checklist', False), ('prontos para zarpar?', 'checklist', False),
    ('pronto para sair hoje?', 'seguro', False),
    # (revisão 4) a pergunta SOBRE o app com a baliza ou o botão DISTRESS segue a saudação (que o trecho de segurança barra da IA: o pedeIA da cabeça de emergência é false); a baliza de sinalização com dado segue o dado
    ('como você me ajuda com o teste da baliza?', 'saudacao', False), ('o que você sabe sobre o teste da baliza?', 'saudacao', False), ('ajuda com o botão DISTRESS e o checklist de saída', 'saudacao', False),
    ('a baliza do canal está apagada, qual a maré?', 'mare', False),
    # (revisão 3) «antes de largar / de sair», «pré-saída» e «rotina de saída» são o checklist de saída
    ('o que preciso conferir antes de largar?', 'checklist', False), ('pré-saída', 'checklist', False), ('rotina de saída', 'checklist', False), ('o que conferir antes de sair?', 'checklist', False),
    ('o que devo verificar antes de zarpar?', 'checklist', False), ('o que fazer antes de largar', 'base', False),
]
# (revisão 3) a «saída» sem a palavra checklist que é do passado, do consumo, da duração, da distância, do horário ou de uma saída de coisa NÃO é o checklist de saída (o diário, o consumo, o guia ou a IA)
NAO_CHECK_SAIDA = ['como foi a saída de ontem?', 'resumo da última saída', 'quanto gastamos na saída de hoje cedo?', 'quanto tempo durou a saída?', 'quantas milhas fizemos na saída?', 'a que horas é a saída?',
                   'horário de saída da marina', 'vamos de saída amanhã cedo', 'qual o consumo da saída anterior?', 'onde fica a saída de água do motor?', 'saída do escape do gerador', 'a saída de ar da climatização está fraca',
                   'antes de sair, confira o porão']
CASOS = CASOS + [(q, k) for q, k, _ in ROTAS_P3E_F09]
PEDE_IA.update({q: ia for q, k, ia in ROTAS_P3E_F09})
# O estado de cada item `auto` em 12:01:00 (CONTRATO §1.18, «Estado esperado de cada item auto»): ok (✓ pelo quadro), falta (✗), ler (mostra a leitura e pede a conferência); None = item sem verificação automática.
# Em 12:01:45 só o s02 (alertas) muda: ✗ AVISO do arrefecimento do motor BE.
EST_60 = {
    'saida': {'s01': 'ler', 's02': 'ok', 's03': None, 's04': 'ler', 's05': 'ok', 's06': 'ok', 's07': 'ok', 's08': None, 's09': 'ok', 's10': None, 's11': 'ler', 's12': 'falta', 's13': None, 's14': None},
    'chegada': {'c01': None, 'c02': 'falta', 'c03': 'falta', 'c04': 'falta', 'c05': None, 'c06': 'ok', 'c07': None, 'c08': None},
    'abastecimento': {'a01': 'falta', 'a02': 'falta', 'a03': 'ok', 'a04': None, 'a05': None, 'a06': None, 'a07': None},
    'fundeio': {'f01': 'ok', 'f02': None, 'f03': None, 'f04': 'falta', 'f05': None, 'f06': 'ler'},
}
EST_105 = {k: dict(v) for k, v in EST_60.items()}
EST_105['saida']['s02'] = 'falta'
TIPOS_CK = ['saida', 'chegada', 'abastecimento', 'fundeio']
CHAVE_CK = {'saida': 'checklist', 'chegada': 'checklistChegada', 'abastecimento': 'checklistAbastecimento', 'fundeio': 'checklistFundeio'}
PERGUNTA_CK = {'saida': 'checklist de saída', 'chegada': 'checklist de chegada', 'abastecimento': 'checklist de abastecimento', 'fundeio': 'checklist de fundeio'}
JS_CK = """(xs) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, D = window.CapitaoDados, op = { platform: 'app', commit: false }, T = ['saida', 'chegada', 'abastecimento', 'fundeio'], P = %s;
  const pega = (i) => ({ id: i.id, c: i.c, t: i.t, fonte: i.fonte, faq: i.faq || null, link: i.link || null, parcial: !!i.parcial, auto: i.auto, manual: i.manual, anulado: i.anulado, porQuadro: i.porQuadro, feito: i.feito });
  return { tipos: B.checklistTipos(), dados: D.checklists, docs: D.documentos.map((d) => ({ id: d.id, vence: d.vence })), eqval: D.equipamentos.filter((e) => e.seguranca === true && e.validade).map((e) => e.validade), r: xs.map((x) => { R.fixar(x); const i = B.instante(), o = { x, hora: i.hora, txt: i.txt, q: { sog: i.q.sog_nos, bb: i.q.diesel_bb_pct }, itens: {}, resp: {} };
    T.forEach((t) => { o.itens[t] = B.checklistItens(t).map(pega); const a = B.answer(P[t], op); o.resp[t] = { key: a.key, text: a.text, src: a.src, fala: B.falaCurta(a), ia: B.pedeIA(a, P[t]) }; });
    return o; }) }; }""" % json.dumps(PERGUNTA_CK)
# (cada quadro adulterado num segundo próprio — 62, 64, 66…: o instante fixado fica guardado por segundo, e o do 60 volta limpo no fim)
JS_CK_SOBRE = """(sobres) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, T = ['saida', 'chegada', 'abastecimento', 'fundeio'];
  const r = sobres.map((s, k) => { localStorage.setItem('capitao.replay.sobre', JSON.stringify(s)); R.fixar(String(62 + 2 * k)); const o = {};
    T.forEach((t) => { o[t] = {}; B.checklistItens(t).forEach((i) => { o[t][i.id] = i.auto && i.auto.estado; }); }); localStorage.removeItem('capitao.replay.sobre'); return o; });
  R.fixar('60'); return r; }"""
SOBRE_BOM = {'motor_bb_rpm': 0, 'motor_be_rpm': 0, 'gerador_ativo': False, 'seakeeper_ativo': False, 'sog_nos': 0.2}
SOBRE_RUIM = {'diesel_bb_pct': 20, 'diesel_litros': 800, 'tanque_agua_pct': 10, 'bateria_0_tensao_v': 23.0, 'profundidade_m': 2.5, 'porao_bb_nivel': 8, 'seakeeper_volante_pct': 70}
# (revisão) UM campo por quadro: o lado que o quadro «ruim» não separa (porão BE, diesel BE), cada banco de baterias sozinho (partida 24 V e 12 V) e o barco a 2 nós (entre a deriva de 0,5 e o limiar de 5)
SOBRE_UM = [{'porao_be_nivel': 8}, {'diesel_be_pct': 20}, {'bateria_1_tensao_v': 20.0}, {'bateria_2_tensao_v': 9.0}, {'sog_nos': 2.0}]
JS_CK_ESCRITA = """() => { const B = window.CapitaoBrain, R = window.CapitaoReplay, D = window.CapitaoDados; R.fixar('60'); const op = { platform: 'app', commit: false };
  localStorage.removeItem('capitao.diario.v1'); localStorage.removeItem('capitao.checklist.v1');
  const pad = (s) => ' ' + s.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').replace(/[?!.,;:()"“”]+/g, ' ').replace(/\\s+/g, ' ').trim() + ' ';
  const n0 = B.loadDiario().length, marcas = JSON.stringify([B.checklistMarca('saida', 's03', true), B.checklistMarca('saida', 's02', 'n'), B.checklistMarca('saida', 'zzz', true), B.checklistMarca('xx', 's03', true), B.checklistMarca('chegada', 'c01', true)]);
  const it = (t) => B.checklistItens(t).reduce((o, i) => { o[i.id] = i; return o; }, {}), s = it('saida');
  const o = { n0, marcas, s03: { manual: s.s03.manual, feito: s.s03.feito }, s02: { anulado: s.s02.anulado, feito: s.s02.feito, porQuadro: s.s02.porQuadro, estado: s.s02.auto.estado }, linha: B.checklistLinha('saida'), lido: JSON.parse(localStorage.getItem('capitao.checklist.v1')), n1: B.loadDiario().length };
  o.resp = B.answer('checklist de saída', op).text.split('\\n').slice(0, 4);
  o.link = B.checklistConcluir('saida', { commit: false }); o.n2 = B.loadDiario().length;
  const c = B.checklistConcluir('saida'); o.c = c; o.n3 = B.loadDiario().length; o.entrada = B.loadDiario()[0]; o.depois = JSON.parse(localStorage.getItem('capitao.checklist.v1'));
  o.volta = B.checklistMarca('chegada', 'c01', false); o.vazio = JSON.parse(localStorage.getItem('capitao.checklist.v1'));
  o.ruim = B.checklistMarca('desconhecido', 'c01', true); o.semTipo = B.checklistConcluir('desconhecido');
  localStorage.setItem('capitao.checklist.v1', '[1,2]'); o.lixo1 = [B.checklistItens('saida').length, B.checklistMarcas('saida')];
  localStorage.setItem('capitao.checklist.v1', 'não é json'); o.lixo2 = [B.checklistItens('saida').length, JSON.stringify(B.checklistMarcas('saida'))];
  localStorage.setItem('capitao.checklist.v1', JSON.stringify({ saida: { m: 'x' }, chegada: 5 })); o.lixo3 = [B.checklistItens('saida').length, JSON.stringify(B.checklistMarcas('saida')), JSON.stringify(B.checklistMarcas('chegada'))];
  o.emerg = {}; ['saida', 'chegada', 'abastecimento', 'fundeio'].forEach((t) => { const l = B.checklistLinha(t), todas = D.checklists.itens[t].map((i) => i.c).join(', '), sint = D.checklists.tipos.filter((x) => x.id === t)[0].nome + ' concluído · 0/' + D.checklists.itens[t].length + ' · pendentes: ' + todas;
    o.emerg[t] = [l.t, sint].map((x) => [B.emergencia(pad(x)), B.route(x), B.answer('registre no diário ' + x, op).text.indexOf('Se a emergência é agora') !== -1]); });
  return o; }"""


def primeira_linha_ck(nome, hora, itens):
    f = sum(1 for i in itens if i['feito'])
    nao = [i['c'] for i in itens if not i['feito'] and i['auto'] and i['auto']['estado'] == 'falta']
    return '%s%s: %d de %d conferidos%s.' % (nome, ' às ' + hora if hora else '', f, len(itens), ('; ' + ('não passou: ' if len(nao) == 1 else 'não passaram: ') + ', '.join(nao)) if nao else '')


def linha_item_ck(k, i):
    m = '✓' if i['feito'] else '✗' if (i['auto'] and i['auto']['estado'] == 'falta') else '•'
    v = ' — ' + i['auto']['valor'] if i['auto'] else ''
    t = re.sub(r'\.$', '', i['t']) if v else i['t']
    return '%d. %s %s%s%s (%s%s)' % (k + 1, m, t, v, ' (conferido por você)' if i['manual'] else '', i['fonte'], ' · FAQ ' + i['faq'] if i['faq'] else '')


def grupo_checklist(b, muta, ped):
    pg = pagina(b, muta=muta)
    try:
        pg.evaluate("() => { localStorage.clear(); return new Promise(r => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); }); }")
        res = pg.evaluate(JS_P3C_CHAVES, [[q] for q, _, _ in ROTAS_P3E_F09])
        ruins = [(q, esp, ia_esp, key, ia) for (q, esp, ia_esp), (key, ia) in zip(ROTAS_P3E_F09, res) if key != esp or ia != ia_esp]
        res_nc = pg.evaluate(JS_P3C_CHAVES, [[q] for q in NAO_CHECK_SAIDA])
        ruins_nc = [(q, key) for q, (key, ia) in zip(NAO_CHECK_SAIDA, res_nc) if key.startswith('checklist')]
        ped('checklist: as %d perguntas de «saída» do passado, do consumo, da duração, da distância, do horário e de saída de coisa NÃO são o checklist de saída' % len(NAO_CHECK_SAIDA), not ruins_nc, ruins_nc)
        ped('checklist: as %d perguntas dos 4 checklists (saída, chegada, abastecimento, fundeio — «fundear» e «abastecer» não caem no de saída; «checklist de chegada» e «previsão de chegada…» seguem na rota certa) caem na chave certa, local' % len(ROTAS_P3E_F09), not ruins, ruins[:6])
        x = pg.evaluate(JS_CK, ['60', '105'])
        d = x['dados']
        ped('checklist: B.checklistTipos() são os 4 tipos do D.checklists, na ordem (saída, chegada, abastecimento, fundeio)', [t['id'] for t in x['tipos']] == TIPOS_CK and x['tipos'] == d['tipos'], x['tipos'])
        a60, a105 = x['r']
        for a, est in ((a60, EST_60), (a105, EST_105)):
            for t in TIPOS_CK:
                itens = a['itens'][t]
                dados = d['itens'][t]
                ped('checklist %s t=%s: os itens são os do D.checklists, na ordem, com o rótulo, o texto e a fonte do dado (e o FAQ e o link onde há)' % (t, a['x']),
                    [i['id'] for i in itens] == [i['id'] for i in dados] and all(i['c'] == o['c'] and i['t'] == o['t'] and i['fonte'] == o['fonte'] and i['faq'] == o.get('faq') and i['link'] == o.get('link') and i['parcial'] == bool(o.get('parcial')) for i, o in zip(itens, dados)), [i['id'] for i in itens])
                got = {i['id']: (i['auto'] or {}).get('estado') for i in itens}
                ped('checklist %s t=%s: o estado de cada item automático é o da tabela do contrato (ok ✓, falta ✗, ler = mostra a leitura; sem auto = sem estado)' % (t, a['x']), got == est[t], {k: (v, est[t][k]) for k, v in got.items() if v != est[t][k]})
                ped('checklist %s t=%s: só o ✓ do app (ok) é conferido; ✗, «ler» e o sem auto não são; nenhum item vem marcado pela pessoa' % (t, a['x']),
                    all(i['feito'] == ((i['auto'] or {}).get('estado') == 'ok') and i['porQuadro'] == i['feito'] and not i['manual'] and not i['anulado'] for i in itens), [(i['id'], i['feito']) for i in itens][:4])
                r = a['resp'][t]
                ped('checklist %s t=%s: a resposta abre com «<nome> às <hora>: N de M conferidos; não passou/passaram: …» (a fala), é local (nunca IA), e leva um item por linha com o marcador, a leitura e a fonte' % (t, a['x']),
                    r['key'] == CHAVE_CK[t] and r['ia'] is False and r['fala'] == r['text'].split('\n')[0] == primeira_linha_ck(next(tp['nome'] for tp in d['tipos'] if tp['id'] == t), a['hora'], itens)
                    and r['text'].split('\n')[1:1 + len(itens)] == [linha_item_ck(k, i) for k, i in enumerate(itens)] and r['text'].endswith('• pede a sua conferência a bordo.'), (r['text'].split('\n')[0], primeira_linha_ck('Checklist', a['hora'], itens)))
                ped('checklist %s t=%s: a fonte cita o checklist de bordo e a telemetria da hora do instante; nenhuma regex do §3 casa o texto, a fonte nem a fala, nem coordenada' % (t, a['x']),
                    r['src'] == 'Fonte: Checklist de bordo · telemetria ao vivo · ' + a['hora'] and not any(RX[n].search(r['text'] + '\n' + r['src'] + '\n' + r['fala']) for n in VARREDURA) and not confere.R_COORD.search(r['text']), r['src'])
            # a salvatagem do item s13 não nomeia lugar nem traz o número de pessoas a bordo; o item 13 diz «placa de salvatagem»
            s13 = a['resp']['saida']['text'].split('\n')[13]
            ped('checklist saida t=%s: o item da salvatagem (13) manda contar as pessoas e seguir a placa, sem paiol, armário, cabine, proa ou popa e sem o número de pessoas do cadastro' % a['x'],
                s13.startswith('13. • Coletes: um por pessoa — conte as pessoas a bordo agora') and not re.search(r'paiol|arm[áa]rio|cabine|\bproa\b|\bpopa\b|\b\d+ pessoas', s13), s13)
        # os valores lidos são os do instante (o texto único de cada medida)
        for a in (a60, a105):
            i = {t: {k['id']: k for k in a['itens'][t]} for t in TIPOS_CK}
            tx = a['txt']
            ped('checklist t=%s: o diesel, os tanques, as baterias, o Seakeeper e a sonda mostram o texto único do instante (txt.dieselLados, txt.diesel, txt.tanques, txt.b24, txt.b12, txt.seakeeper, txt.prof)' % a['x'],
                i['saida']['s05']['auto']['valor'] == tx['dieselLados'] + ' — ' + tx['diesel'] and i['abastecimento']['a03']['auto']['valor'] == i['saida']['s05']['auto']['valor'] and i['saida']['s06']['auto']['valor'] == tx['tanques']
                and i['saida']['s07']['auto']['valor'] == tx['b24'] + ' · 12 V ' + tx['b12'] and i['saida']['s09']['auto']['valor'] == tx['seakeeper'] and i['fundeio']['f01']['auto']['valor'] == tx['prof'] + ' (mínimo 3 m)', a['txt'])
            ped('checklist t=%s: o que ainda funciona diz o quadro («motores ligados: …», «ainda ligado…», «gerador ligado…», «navegando a …») e o porão traz o nível e o teste das bombas' % a['x'],
                i['chegada']['c03']['auto']['valor'] == 'motores ligados: ' + tx['rpm'] and i['chegada']['c02']['auto']['valor'] == 'ainda ' + tx['seakeeper'] and i['chegada']['c04']['auto']['valor'] == 'gerador ' + tx['gerador']
                and i['fundeio']['f04']['auto']['valor'] == 'navegando a ' + tx['sog'] and i['saida']['s04']['auto']['valor'].startswith('nível BB ') and 'teste das bombas em atraso há ' in i['saida']['s04']['auto']['valor']
                and i['saida']['s12']['auto']['valor'].startswith('teste das bombas de porão e alarmes (em atraso há '), (i['chegada']['c03']['auto'], i['saida']['s04']['auto']))
        com_prazo = [d for d in x['docs'] if d['vence'] and d['id'] not in x['eqval']]
        ped('checklist: o item dos documentos (s11) conta só os documentos com prazo que NÃO são a validade de um equipamento de segurança (a do EPIRB e a do Seafire vão pela etiqueta): %d, nenhum vencido, sem a data do certificado do EPIRB' % len(com_prazo),
            len(com_prazo) == 6 and all(a['itens']['saida'][10]['auto']['valor'].startswith('nenhum vencido (%d documentos com prazo); o mais próximo: ' % len(com_prazo)) and '2028' not in a['itens']['saida'][10]['auto']['valor'] for a in (a60, a105)), [a['itens']['saida'][10]['auto'] for a in (a60, a105)])
        ped('checklist: só o s02 (alertas) muda de estado entre 12:01:00 e 12:01:45: ✓ nenhum alarme ativo → ✗ AVISO do arrefecimento do motor BE (o texto do quadro)',
            a60['itens']['saida'][1]['auto'] == {'estado': 'ok', 'valor': 'nenhum alarme ativo'} and a105['itens']['saida'][1]['auto'] == {'estado': 'falta', 'valor': 'AVISO: Temperatura do motor BE: 89,6 °C (acima de 88 °C)'} and a105['txt']['alarmes'] == 'AVISO: Temperatura do motor BE: 89,6 °C (acima de 88 °C)'
            and all({i['id']: (i['auto'] or {}).get('estado') for i in a60['itens'][t]} == {i['id']: (i['auto'] or {}).get('estado') for i in a105['itens'][t]} for t in TIPOS_CK if t != 'saida'), (a60['itens']['saida'][1]['auto'], a105['itens']['saida'][1]['auto']))
        ped('checklist: a resposta do checklist de saída muda entre os instantes (a 1ª linha e o item 2); a previsão (s01) e a maré (f06) nunca dão ✓ sozinhas',
            a60['resp']['saida']['text'] != a105['resp']['saida']['text'] and all(i['auto']['estado'] == 'ler' for a in (a60, a105) for i in (a['itens']['saida'][0], a['itens']['fundeio'][5])), '')
        ped('checklist: o item «parcial» que o quadro só confere em parte (porão s04, documentos s11) nunca é ✓: mostra a leitura e pede a conferência',
            all(i['auto']['estado'] != 'ok' for a in (a60, a105) for i in (a['itens']['saida'][3], a['itens']['saida'][10])), '')
        # (sobre o quadro) cada ramo da verificação, com o quadro adulterado pelo gancho de teste do replay (só com o instante fixado)
        bom, ruim, so_bb, ven, porao_be, diesel_be, bat1, bat2, sog2 = pg.evaluate(JS_CK_SOBRE, [SOBRE_BOM, SOBRE_RUIM, {'diesel_bb_pct': 20}, {'seakeeper_ativo': False}] + SOBRE_UM)
        ped('checklist (quadro adulterado, tudo parado): motores, gerador e Seakeeper desligados dão ✓ na chegada e no abastecimento, e o barco parado dá ✓ na deriva',
            all(bom['chegada'][k] == 'ok' for k in ('c02', 'c03', 'c04')) and bom['abastecimento']['a01'] == 'ok' and bom['abastecimento']['a02'] == 'ok' and bom['fundeio']['f04'] == 'ok', {t: bom[t] for t in ('chegada', 'abastecimento', 'fundeio')})
        ped('checklist (quadro adulterado, tudo fora da faixa): o porão alto, o diesel de um lado abaixo de 25 %, a água doce em 10 %, o banco de serviço em 23 V e a sonda em 2,5 m dão ✗; o Seakeeper com o volante em 70 % só pede a conferência',
            ruim['saida']['s04'] == 'falta' and ruim['saida']['s05'] == 'falta' and ruim['saida']['s06'] == 'falta' and ruim['saida']['s07'] == 'falta' and ruim['saida']['s09'] == 'ler' and ruim['fundeio']['f01'] == 'falta' and ruim['chegada']['c06'] == 'falta', ruim['saida'])
        ped('checklist (quadro adulterado): o diesel de UM tanque abaixo de 25 % reprova o item mesmo com o total acima do aviso (cada tanque)', so_bb['saida']['s05'] == 'falta' and so_bb['abastecimento']['a03'] == 'falta', so_bb['saida']['s05'])
        ped('checklist (quadro adulterado, um campo só): o porão alto só no BE reprova o item do porão (cada lado, num item de segurança)', porao_be['saida']['s04'] == 'falta', porao_be['saida']['s04'])
        ped('checklist (quadro adulterado, um campo só): o diesel de UM tanque abaixo de 25 % também no BE reprova o item da saída e o do abastecimento', diesel_be['saida']['s05'] == 'falta' and diesel_be['abastecimento']['a03'] == 'falta', (diesel_be['saida']['s05'], diesel_be['abastecimento']['a03']))
        ped('checklist (quadro adulterado, um campo só): cada banco de baterias sozinho fora da faixa (a partida em 20 V, o de 12 V em 9 V) reprova o item das baterias — o app confere os três', bat1['saida']['s07'] == 'falta' and bat2['saida']['s07'] == 'falta', (bat1['saida']['s07'], bat2['saida']['s07']))
        ped('checklist (quadro adulterado, um campo só): o barco a 2 nós não está parado — a deriva reprova o fundeio (f04), e o barco a 0,2 nó dá ✓', sog2['fundeio']['f04'] == 'falta' and bom['fundeio']['f04'] == 'ok', (sog2['fundeio']['f04'], bom['fundeio']['f04']))
        ped('checklist (quadro adulterado): o Seakeeper desligado na saída pede a conferência (ler), não é ✓', ven['saida']['s09'] == 'ler' and ven['chegada']['c02'] == 'ok', (ven['saida']['s09'], ven['chegada']['c02']))
        # a escrita: as marcas são conveniência (não gravam no diário); CONCLUIR grava UMA linha nova, com sim, e some com as marcas do tipo; recusa tipo e item que não existem; JSON ruim vale como vazio
        w = pg.evaluate(JS_CK_ESCRITA)
        marc = json.loads(w['marcas'])
        ped('checklist (marcas): a marca ✓ da pessoa e a desmarca do ✓ do app ficam em capitao.checklist.v1 por tipo; tipo e item inexistentes recusam (null); marcar não grava no diário',
            marc[0] == {'s03': 1} and marc[1] == {'s03': 1, 's02': 'n'} and marc[2] is None and marc[3] is None and marc[4] == {'c01': 1} and w['lido']['saida']['m'] == {'s03': 1, 's02': 'n'} and w['lido']['chegada']['m'] == {'c01': 1}
            and w['n1'] == w['n0'], (marc, w['lido']))
        ped('checklist (marcas): o item marcado pela pessoa é conferido («conferido por você»); o ✓ do app desmarcado deixa de contar (anulado, não é porQuadro, não é feito) e a resposta mostra os dois',
            w['s03'] == {'manual': True, 'feito': True} and w['s02'] == {'anulado': True, 'feito': False, 'porQuadro': False, 'estado': 'ok'}
            and w['resp'][2] == '2. • Nenhum alerta ativo no painel — nenhum alarme ativo (boa prática)'
            and w['resp'][3] == '3. ✓ Óleo, arrefecimento, correias e válvulas de fundo conferidos com os motores frios. (conferido por você) (Guia de bordo — Motores Cummins §1 · Antes da partida · FAQ MO-01)', (w['s02'], w['resp'][2:]))
        ln = w['linha']
        pend = ['previsão', 'alertas', 'porão', 'gerador', 'plotter e VHF', 'documentos', 'tarefas de segurança', 'coletes e salvatagem', 'cabos e defensas']
        quer = 'Checklist de saída concluído · 5/14 (4 pela telemetria) · pendentes: ' + ', '.join(pend)
        ped('checklist (linha): «Checklist de saída concluído · 5/14 (4 pela telemetria) · pendentes: …» (5 conferidos: 4 pelo app e o s03 da pessoa; o s02 desmarcado vira pendente)', ln['t'] == quer and ln['feitos'] == 5 and ln['total'] == 14 and ln['porQuadro'] == 4 and ln['pend'] == pend and ln['sys'] == 'Navegação', (ln['t'], quer))
        ped('checklist (CONCLUIR): grava UMA linha nova no diário (a de saída, sys Navegação, com sim e o texto da linha); o pedido vindo de link (commit false) não grava; as marcas de saída somem e as de chegada ficam',
            w['link'] is None and w['n2'] == w['n0'] and w['n3'] == w['n0'] + 1 and w['entrada']['t'] == quer and w['entrada']['sys'] == 'Navegação' and w['entrada']['sim'] is True and w['entrada']['who'] and w['entrada']['src'] == 'checklist de bordo · telemetria'
            and w['c']['entrada'] == w['entrada'] and w['c']['t'] == quer and 'saida' not in w['depois'] and w['depois']['chegada']['m'] == {'c01': 1}, (w['n0'], w['n2'], w['n3'], w['entrada']))
        ped('checklist (marcas): false volta ao automático (apaga a marca); sem marca nenhuma o tipo continua no registro do aparelho vazio', w['volta'] == {} and w['vazio'].get('chegada', {}).get('m') == {}, (w['volta'], w['vazio']))
        ped('checklist: tipo que não existe — marca e CONCLUIR devolvem null e não gravam', w['ruim'] is None and w['semTipo'] is None, (w['ruim'], w['semTipo']))
        ped('checklist: JSON ruim no aparelho (lista, texto, marca que não é mapa, tipo que não é objeto) vale como sem marcas e os 14 itens seguem; nunca lança', w['lixo1'] == [14, {}] and w['lixo2'] == [14, '{}'] and w['lixo3'] == [14, '{}', '{}'], (w['lixo1'], w['lixo2'], w['lixo3']))
        ped('checklist (CONCLUIR): a linha gravada (e a pior, com todos os rótulos pendentes) de cada tipo não casa a lista SOS, não é o relato de óleo e não vira diário com alerta', all(r == [False, r_[1], False] and r_[1] not in ('sos', 'oleo') for t in TIPOS_CK for r_ in [w['emerg'][t][0], w['emerg'][t][1]] for r in [r_]), w['emerg'])
    finally:
        pg.ctx.close()
    # com a leitura do dia e a maré salvas (o capitao-clima.js da Main e da H2, Open-Meteo real; aqui a cópia plantada): a previsão (s01) e a maré (f06) mostram a leitura e NUNCA dão ✓ sozinhas (§2.5)
    pg = pagina(b, muta=muta, clima=True)
    try:
        r = pg.evaluate("() => { const B = window.CapitaoBrain; return { s01: B.checklistItens('saida')[0].auto, f06: B.checklistItens('fundeio')[5].auto, t: B.answer('checklist de fundeio', { platform: 'app', commit: false }).text }; }")
        ped('checklist (com a leitura do dia e a maré salvas): a previsão (s01) e a maré (f06) mostram o vento previsto e a maré do modelo e seguem «ler» — nunca ✓ sozinhas',
            r['s01']['estado'] == 'ler' and r['s01']['valor'].startswith('previsão de hoje: vento até 12 nós de nordeste, rajadas até 21 nós (') and r['f06']['estado'] == 'ler'
            and r['f06']['valor'].startswith('previsão de hoje: vento até 12 nós de nordeste') and ' · maré agora ' in r['f06']['valor'] and 'modelo, não é a tábua oficial da Marinha' in r['f06']['valor'] and '6. • Maré e vento conferidos' in r['t'], r)
    finally:
        pg.ctx.close()
    # (revisão 4) o documento VENCIDO (o histórico gerado nunca tem um): o item dos documentos (s11) dá ✗ «vencido: <documento> (<data>)», não passa, e a 1ª linha da resposta o diz entre os que não passaram
    pg = pagina(b, muta=muta)
    try:
        r = pg.evaluate("""() => { const B = window.CapitaoBrain, D = window.CapitaoDados; D.documentos.filter((d) => d.id === 'seguro')[0].vence = '01/01/2020';
          const i = B.checklistItens('saida')[10], a = B.answer('checklist de saída', { platform: 'app', commit: false }); return { id: i.id, auto: i.auto, feito: i.feito, l1: a.text.split('\\n')[0], l11: a.text.split('\\n')[11] }; }""")
        ped('checklist (plantado): com o seguro vencido o item dos documentos (s11) dá ✗ «vencido: Seguro da embarcação (01/01/2020)», não é conferido e a 1ª linha o põe entre os que não passaram',
            r['id'] == 's11' and r['auto'] == {'estado': 'falta', 'valor': 'vencido: Seguro da embarcação (01/01/2020)'} and r['feito'] is False and r['l1'].endswith('não passaram: documentos, tarefas de segurança.') and r['l11'].startswith('11. ✗ '), r)
    finally:
        pg.ctx.close()
    # modo real (simulacao false): sem o quadro, o item que precisa dele diz SEM LEITURA (o caminho null); a previsão, os documentos e as tarefas seguem; sem hora; a linha do CONCLUIR sem sim
    pg = pagina(b, extra=SEM_SIMULACAO, muta=muta)
    try:
        r = pg.evaluate("""() => { const B = window.CapitaoBrain, a = B.answer('checklist de saída', { platform: 'app', commit: false }); localStorage.removeItem('capitao.diario.v1'); const c = B.checklistConcluir('saida');
          return { t: a.text, src: a.src, fala: B.falaCurta(a), itens: B.checklistItens('saida').map((i) => [i.id, i.auto && i.auto.estado]), e: c.entrada, linhas: ['saida', 'chegada', 'abastecimento', 'fundeio'].map((t) => B.checklistLinha(t).t) }; }""")
        est = dict(r['itens'])
        ped('checklist (simulacao false): sem o quadro vivo os itens que o precisam voltam a «sem» (SEM LEITURA); previsão, documentos e tarefas seguem; a 1ª linha sem hora e sem «ao vivo»',
            all(est[k] == 'sem' for k in ('s02', 's04', 's05', 's06', 's07', 's09')) and est['s01'] == 'ler' and est['s11'] == 'ler' and est['s12'] == 'falta' and r['t'].split('\n')[0] == 'Checklist de saída: 0 de 14 conferidos; não passou: tarefas de segurança.'
            and r['t'].count('SEM LEITURA') >= 6 and not re.search(r'ao vivo|\d\d:\d\d:\d\d', r['t'] + r['src']) and r['src'] == 'Fonte: Checklist de bordo · coletor NMEA · leitura de 26/09/2026 10:12', (r['t'].split('\n')[0], r['src'], est))
        ped('checklist (simulacao false): CONCLUIR grava a linha sem `sim`, com 0 conferidos e todos os rótulos pendentes que o quadro não confere', 'sim' not in r['e'] and r['e']['t'].startswith('Checklist de saída concluído · 0/14 · pendentes: previsão, alertas'), r['e'])
    finally:
        pg.ctx.close()
    # o SOS: nenhum checklist (o SOS não lê dado do barco)
    pg = pagina(b, scripts=('capitao-dados.js', 'capitao-brain.js'), caminho='SOS-cerebro.html', fixo=None, muta=muta)
    try:
        r = pg.evaluate("() => { const B = window.CapitaoBrain, a = B.answer('checklist de saída', { platform: 'app', commit: false }); return { tipos: B.checklistTipos(), itens: B.checklistItens('saida'), c: B.checklistConcluir('saida'), t: a.text }; }")
        ped('checklist (SOS): nenhum tipo, nenhum item, CONCLUIR não grava e a resposta não traz item nenhum', r['tipos'] == [] and r['itens'] == [] and r['c'] is None and 'Previsão' not in r['t'] and 'Nenhum alerta' not in r['t'], r)
    finally:
        pg.ctx.close()


GRUPOS_3A['checklist'] = grupo_checklist
MUTANTES_3E_F09 = [
    ('p3e checklist: o s02 confere os alertas sempre ✓', "return a.indexOf('nenhum') === 0 ? R_('ok', 'nenhum alarme ativo') : R_('falta', a);", "return R_('ok', 'nenhum alarme ativo');", ('checklist',)),
    ('p3e checklist: o item parcial vira ✓', "if (it.parcial && a && a.estado === 'ok') a = R_('ler', a.valor + ' — o resto do item: confira');", "", ('checklist',)),
    ('p3e checklist: a maré dá ✓ sozinha (o s01 da previsão é parcial e ficaria «ler» de qualquer jeito)', "return R_('ler', [pv ? 'previsão de hoje: '", "return R_('ok', [pv ? 'previsão de hoje: '", ('checklist',)),
    ('p3e checklist: o CONCLUIR grava duas linhas', "    checklistZera(ln.tipo);\n    return Object.assign({ entrada: e }, ln);", "    addDiario({ sys: ln.sys, t: ln.t, who: quem(), src: 'x' });\n    checklistZera(ln.tipo);\n    return Object.assign({ entrada: e }, ln);", ('checklist',)),
    ('p3e checklist: o CONCLUIR não apaga as marcas do tipo', "    checklistZera(ln.tipo);\n    return Object.assign({ entrada: e }, ln);", "    return Object.assign({ entrada: e }, ln);", ('checklist',)),
    ('p3e checklist: a linha do CONCLUIR sem o carimbo sim', "who: quem(), src: 'checklist de bordo' + (ln.porQuadro ? ' · telemetria' : '') }, selaSim()));", "who: quem(), src: 'checklist de bordo' + (ln.porQuadro ? ' · telemetria' : '') }, {}));", ('checklist',)),
    ('p3e checklist: a marca da pessoa não conta', "feito: (ok && !anulado) || manual });", "feito: (ok && !anulado) });", ('checklist',)),
    ('p3e checklist: o ✓ do app não pode ser desmarcado', "feito: (ok && !anulado) || manual });", "feito: ok || manual });", ('checklist',)),
    ('p3e checklist: o diesel olha só o total', "nv(x, 'diesel_litros') === 'normal' && q.diesel_bb_pct >= min && q.diesel_be_pct >= min ? 'ok' : 'falta'", "nv(x, 'diesel_litros') === 'normal' ? 'ok' : 'falta'", ('checklist',)),
    ('p3e checklist: «checklist ao fundear» cai no de saída', "    if (has(q, CHECK_PALAVRAS) && has(q, ['fundei', 'fundear', 'ancorar', 'ancoragem'])) return 'checklistFundeio';\n", "", ('checklist',)),
    ('p3e checklist: «checklist de abastecimento» cai no de saída', "    if (has(q, CHECK_PALAVRAS) && has(q, ['abastec'])) return 'checklistAbastecimento';\n", "", ('checklist',)),
    # (revisão 3) a trava 10 (o equipamento de segurança), a «saída» de outra coisa, o «antes de largar»
    ('p3e checklist: toda pergunta com «saída» é o checklist de saída (sem a lista do passado, do consumo, da duração e do horário)', r"(has(q, [' saida']) && !has(q, SAIDA_NAO_CHECK))", r"has(q, [' saida'])", ('checklist',)),
    ('p3e checklist: «a que horas é a saída?» e «horário de saída» são o checklist', r"'hoje cedo', 'amanha', 'vamos de', 'horario', 'que horas',", r"'hoje cedo',", ('checklist',)),
    ('p3e checklist: «a saída de água / de ar / do escape» é o checklist de saída', r"' saida de ar', ' saida de agua', ' saida do escape', ' saida de escape',", r"", ('checklist',)),
    ('p3e checklist: o «antes de largar / de sair» não é o checklist de saída', r"|| (has(q, CHECK_ANTES) && leitura(q, CHECK_ANTES_OK))", r"", ('checklist',)),
    ('p3e checklist: «antes de sair, confira o porão» vira o checklist de saída (sem a lista branca)', r"(has(q, CHECK_ANTES) && leitura(q, CHECK_ANTES_OK))", r"has(q, CHECK_ANTES)", ('checklist',)),
    ('p3e checklist: «o que fazer antes de largar» (o trecho do guia «Saída · antes de largar») vira o checklist', r"conferir verificar checar revisar lembrar antes largar sair", r"conferir verificar checar revisar fazer lembrar antes largar sair", ('checklist',)),
    ('p3e checklist: a «pré-saída» não é o checklist de saída', r"|| has(q, ['pre-saida', 'pre saida'])", r"", ('checklist',)),
    ('p3e checklist: a marca aceita item que não existe', "if (!tp || !checkIds(tp.id).some(function (it) { return it.id === id; })) return null;", "if (!tp) return null;", ('checklist',)),
    ('p3e checklist: o item sem leitura do quadro vira ✓ (modo real)', "      if (!a) return R_('sem', SL);\n      return a.indexOf('nenhum') === 0", "      if (!a) return R_('ok', SL);\n      return a.indexOf('nenhum') === 0", ('checklist',)),
    ('p3e checklist: o SOS lê os tipos', "function checkTipos() { return EM_SOS || !D.checklists", "function checkTipos() { return !D.checklists", ('checklist',)),
    # (revisão) cada lado do porão e do diesel, cada banco de baterias, o limiar da deriva e a validade do equipamento de segurança nos documentos
    ('p3e checklist: o porão olha só o BB', "return R_(bb === 'normal' && be === 'normal' ? 'ok' : 'falta', niv);", "return R_(bb === 'normal' ? 'ok' : 'falta', niv);", ('checklist',)),
    ('p3e checklist: o diesel olha só o BB (o lado BE não conta)', "q.diesel_bb_pct >= min && q.diesel_be_pct >= min ? 'ok' : 'falta'", "q.diesel_bb_pct >= min ? 'ok' : 'falta'", ('checklist',)),
    ('p3e checklist: as baterias olham só o banco de serviço', "return R_(ns.every(function (n) { return n === 'normal'; }) ? 'ok' : 'falta', x.t.b24", "return R_(ns[0] === 'normal' ? 'ok' : 'falta', x.t.b24", ('checklist',)),
    ('p3e checklist: as baterias olham só os dois bancos de 24 V (o de 12 V não conta)', "return R_(ns.every(function (n) { return n === 'normal'; }) ? 'ok' : 'falta', x.t.b24", "return R_(ns[0] === 'normal' && ns[1] === 'normal' ? 'ok' : 'falta', x.t.b24", ('checklist',)),
    ('p3e checklist: a deriva aceita o barco andando a 2 nós (limiar de 5)', "return x.q.sog_nos < 0.5 ? R_('ok'", "return x.q.sog_nos < 5 ? R_('ok'", ('checklist',)),
    ('p3e checklist: o documento vencido só pede a conferência (ler), não reprova', r"if (venc.length) return R_('falta', 'vencido: '", r"if (venc.length) return R_('ler', 'vencido: '", ('checklist',)),
    ('p3e checklist: os documentos contam a validade do equipamento de segurança (a etiqueta)', "return !daEtiqueta(d) && !isNaN(dnDe(d)); })", "return !isNaN(dnDe(d)); })", ('checklist',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3E_F09

# —— F10: o FAQ dos equipamentos no chat ——
FAQ_JSON = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'faq-equipamentos.json'), encoding='utf-8'))
# as 8 frases do próprio FAQ (pergunta ou variante) que nenhuma resposta pronta nem trecho do guia responde (iam à IA): agora o item, com o código e a fonte
FAQ_TIPADAS = [('água rasa: o que faço', 'EL-08'), ('sonda mostrando pouca profundidade', 'EL-08'), ('conferência anual do guincho', 'AN-04'), ('Como vejo os outros barcos pelo AIS?', 'AI-01'),
               ('transponder só recebendo', 'AI-03'), ('boletim da Marinha antes de sair', 'CK-03'), ('O que faço ao chegar na marina?', 'CK-04'), ('Quando completo a água e esvazio as servidas?', 'CK-06')]
# o que o FAQ NÃO toma: a resposta pronta, o trecho do guia, a pergunta de uma palavra, a genérica sem item, a de náutica geral (essas seguem como antes)
FAQ_NAO = [('como se faz um nó lais de guia?', 'fallback'), ('como silenciar o alarme?', 'fallback'), ('como ligar o gerador?', 'base'), ('gerador', 'gerador'), ('como abrir a ventilação', 'fallback'),
           ('o alarme disparou', 'fallback'), ('como desligar o sistema', 'fallback'), ('quando trocar o óleo do motor?', 'base'), ('alarme de fluxo da climatização', 'base'),
           ('boletim', 'fallback'), ('autoteste', 'fallback'), ('em caso de alarme', 'fallback'), ('o que fazer em caso de alarme', 'fallback'), ('a baliza de canal', 'fallback'), ('baliza do canal', 'fallback'),
           ('a baliza do canal está apagada', 'fallback'), ('o que faço com o alarme?', 'fallback'), ('o que faço com a pressão?', 'fallback'),
           # (revisão 4) «pronto para sair?» é o checklist de saída (não o item do Seakeeper SK-02, que fala sem dizer o equipamento); com a cabeça de emergência, o equipamento
           ('pronto para sair?', 'checklist'), ('estamos prontos para sair?', 'checklist'), ('tudo pronto para largar?', 'checklist'), ('prontos para zarpar?', 'checklist'),
           ('o botão DISTRESS, água rasa: o que faço', 'base'), ('onde fica o EPIRB, sonda mostrando pouca profundidade', 'epirb')]   # (as duas últimas: pergunta genérica, o 1º item empata com o de outra seção — o alarme do piloto e o da climatização — e fica com a IA)   # (as duas últimas famílias: a palavra genérica «caso» não abre o item do fogo e a baliza de sinalização não é o EPIRB)   # (uma palavra só: «boletim» e «autoteste» casariam o CK-03 e o EP-02 se a busca aceitasse uma palavra)
JS_FAQ = """async () => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }; const ok = await B.carregaFaq(), d = B.faqDados();
  const out = { ok, pronto: B.faqPronto(), total: d.itens.length, id1: B.faqItem('MO-02'), nulos: [B.faqItem('XX-99'), B.faqItem(5), B.faqItem(null), B.faqItem()] };
  out.todos = d.itens.map((it) => { const a = B.answer('qualquer pergunta', Object.assign({ faq: it.id }, op));
    return { id: it.id, key: a.key, faq: a.faq, emerg: a.emerg, seguranca: a.seguranca, text: a.text, src: a.src, acoes: a.actions, ia: B.pedeIA(a, 'qualquer pergunta'), fala: B.falaCurta(a), hora: a.hora || null, ficha: it.emerg || it.id === 'MO-02' ? B.ficha('app', 'qualquer pergunta', a) : null }; });
  out.tipadas = FQ.map((q) => { const a = B.answer(q, op); return [q, a.key, a.faq || null, B.pedeIA(a, q), a.text.split('\\n')[0], a.src, B.falaCurta(a)]; });
  out.nao = FN.map((q) => { const a = B.answer(q, op); return [q, a.key, a.faq || null]; });
  out.frases = []; d.itens.forEach((it) => [it.pergunta].concat(it.variantes).forEach((q) => { const a = B.answer(q, op); if (a.key === 'faqEquip') out.frases.push([it.id, q, a.faq]); }));
  out.id = [B.answer('x', Object.assign({ faq: 'MO-02', id: 'checklist' }, op)).key, B.answer('MAYDAY', Object.assign({ faq: 'MO-02' }, op)).faq, B.answer('checklist de saída', Object.assign({ faq: 'XX-99' }, op)).key, B.answer('checklist de saída', Object.assign({ faq: 5 }, op)).key];
  return out; }""".replace('FQ', json.dumps([q for q, _ in FAQ_TIPADAS], ensure_ascii=False)).replace('FN', json.dumps([q for q, _ in FAQ_NAO], ensure_ascii=False))


def texto_faq(it):
    passos = it.get('passos', [])
    # (revisão 4) a 1ª linha abre com o título do item (o assunto): vários itens começam com um verbo sem sujeito; o cartão de emergência (EM-01…09) não — abre com a instrução de segurança
    t = (it['titulo'] + ' — ' if it.get('titulo') and not it.get('emerg') else '') + it['resposta']
    if passos:
        t += '\n' + '\n'.join('%d. %s' % (i + 1, x) for i, x in enumerate(passos[:8])) + ('\n… mais %d passos no FAQ (%s).' % (len(passos) - 8, it['id']) if len(passos) > 8 else '')
    if it.get('atencao'):
        t += '\nAtenção: ' + it['atencao']
    if it.get('senao'):
        t += '\nSe não resolver: ' + it['senao']
    if it.get('obs'):
        t += '\nObservação: ' + it['obs']
    return t


def grupo_faq(b, muta, ped):
    itens = FAQ_JSON['itens']
    por = {it['id']: it for it in itens}
    pg = pagina(b, muta=muta)
    try:
        pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); })")
        x = pg.evaluate(JS_FAQ)
        ped('faq: o cérebro carrega o faq-equipamentos.json (91 itens) e dá o item pelo código; código que não existe, número e vazio devolvem null',
            x['ok'] is True and x['pronto'] is True and x['total'] == 91 == len(itens) and x['id1'] == por['MO-02'] and x['nulos'] == [None] * 4, (x['ok'], x['total'], x['nulos']))
        ped('faq: 91 itens, 26 de segurança (os 9 cartões EM e os outros do contrato §1.6) e 9 de emergência', sum(1 for i in itens if i.get('seguranca')) == 26 and sum(1 for i in itens if i.get('emerg')) == 9, (sum(1 for i in itens if i.get('seguranca')), sum(1 for i in itens if i.get('emerg'))))
        ruins = []
        for r in x['todos']:
            it = por[r['id']]
            fs = [f['texto'] for f in it.get('fontes', [])]
            esp_src = 'Fonte: FAQ dos equipamentos ' + it['id'] + (' · ' + ' · '.join(fs) if fs else '')
            if not (r['key'] == 'faqEquip' and r['faq'] == it['id'] and r['text'] == texto_faq(it) and r['src'] == esp_src and r['seguranca'] == bool(it.get('seguranca')) and r['emerg'] == bool(it.get('emerg'))
                    and any(a['l'] == 'FAQ de bordo' for a in r['acoes']) and any(a['l'] == 'Abrir SOS' for a in r['acoes']) == bool(it.get('emerg'))):
                ruins.append((r['id'], 'forma'))
            if r['ia'] != (not it.get('seguranca')):
                ruins.append((r['id'], 'ia', r['ia']))
        ped('faq: o item pedido pelo código (ctx.faq) é o item: key faqEquip, o código, a resposta, os passos (até 8), a atenção e a fonte com o código; só o cartão de emergência tem o botão do SOS', not ruins, ruins[:12])
        # (revisão 4) a 1ª linha (a falada) abre com o TÍTULO do item, menos o cartão de emergência, que abre com a instrução de segurança: «Ligar o estabilizador antes de sair — Ligue pelo display…» e não «Ligue pelo display…»
        ruins = [r['id'] for r in x['todos'] if not (r['text'].split('\n')[0].startswith(por[r['id']]['titulo'] + ' — ' + por[r['id']]['resposta'][:30]) if not por[r['id']].get('emerg') else r['text'].startswith(por[r['id']]['resposta'][:30]))]
        sk = next(r for r in x['todos'] if r['id'] == 'SK-02')
        ped('faq (revisão 4): os 82 itens comuns abrem com «<título> — <resposta>» (SK-02: «Ligar o estabilizador antes de sair — Ligue pelo display…»); os 9 cartões de emergência abrem direto com a instrução, sem título antes (trava 10)',
            not ruins and sk['text'].startswith('Ligar o estabilizador antes de sair — Ligue pelo display') and sk['fala'].startswith('Ligar o estabilizador antes de sair — Ligue pelo display'), (ruins[:4], sk['text'][:80]))
        seg = [r for r in x['todos'] if por[r['id']].get('seguranca')]
        ped('faq: os 26 itens de segurança e os 9 cartões de emergência NUNCA vão à IA (pedeIA false); os outros 65, sim (como o trecho do guia)', len(seg) == 26 and all(r['ia'] is False for r in seg) and all(r['ia'] is True for r in x['todos'] if not por[r['id']].get('seguranca')), [r['id'] for r in seg if r['ia']][:5])
        # o cartão de emergência: a resposta de emergência não leva o quadro (a ficha sai sem a Telemetria, a Navegação, os Horímetros e a Autonomia), nem a hora, e a fala é a resposta inteira (a 1ª linha)
        em = [r for r in x['todos'] if por[r['id']].get('emerg')]
        ped('faq: o cartão de emergência (EM-01…09) é resposta de emergência: a ficha sai sem o quadro e sem hora, e a fala é a 1ª linha inteira (a resposta toda, com o rótulo do procedimento padrão), sem a hora do instante',
            len(em) == 9 and all(r['ficha'] and '## Telemetria' not in r['ficha'] and '## Navegação agora' not in r['ficha'] and '## Horímetros' not in r['ficha'] and r['hora'] is None and r['fala'] == por[r['id']]['resposta']
                                 and 'procedimento padrão — confirmar com o protocolo de bordo' in r['fala'].lower().replace('procedimento padrão', 'procedimento padrão') for r in em), [r['id'] for r in em if '## Telemetria' in (r['ficha'] or '')])
        mo = next(r for r in x['todos'] if r['id'] == 'MO-02')
        ped('faq: o item comum (MO-02) leva a ficha completa e a hora do instante como os outros; a fala é a 1ª linha («<título> — <resposta>»), sem a hora', '## Telemetria' in mo['ficha'] and mo['hora'] == '12:01:00' and mo['fala'].startswith(por['MO-02']['titulo'] + ' — ' + por['MO-02']['resposta'][:40]) and '12:01:00' not in mo['fala'], (mo['hora'], mo['fala'][:80]))
        ruim = []
        for r in x['todos']:
            tudo = r['text'] + '\n' + r['src'] + '\n' + r['fala']
            m = [(n, k.group(0)) for n in VARREDURA for k in [RX[n].search(tudo)] if k]
            if m or confere.R_COORD.search(tudo) or '710123456' in tudo or re.search(r'último fix|R\$', tudo):
                ruim.append((r['id'], m))
        ped('faq: nenhuma das 91 respostas casa as regex do §3 (ROTULOS, AUTENTICIDADE, VAZIOS, VISIVEL, DINHEIRO), nem coordenada, MMSI do cadastro, «último fix» ou R$', not ruim, ruim[:4])
        # a pergunta digitada: só o que nada mais responde (o fallback) e casa bem de perto com UM item
        ruins = [(q, esp, k, f, ia) for (q, esp), (_, k, f, ia, *_) in zip(FAQ_TIPADAS, x['tipadas']) if not (k == 'faqEquip' and f == esp and ia == (not por[esp].get('seguranca')))]
        ped('faq: as %d frases do FAQ que iam à IA (sem resposta pronta nem trecho do guia) agora têm o item certo, com o código; o de segurança (CK-03) fica no aparelho' % len(FAQ_TIPADAS), not ruins, ruins)
        for (q, esp), (_, k, f, ia, linha1, src, fala) in zip(FAQ_TIPADAS, x['tipadas']):
            it = por[esp]
            if not (linha1 == texto_faq(it).split('\n')[0] and src.startswith('Fonte: FAQ dos equipamentos %s · ' % esp) and fala):
                ruins.append((q, linha1[:60], src[:60]))
        ped('faq: a 1ª linha da resposta digitada é «<título> — <resposta>» do item e a fonte começa com «FAQ dos equipamentos <código> · <guia § seção>»', not ruins, ruins)
        ruins = [(q, esp, k, f) for (q, esp), (_, k, f) in zip(FAQ_NAO, x['nao']) if k != esp or f is not None]
        ped('faq: o FAQ não toma o que já responde (resposta pronta, trecho do guia) nem a pergunta de uma palavra, a genérica ou a de náutica geral (%d perguntas)' % len(FAQ_NAO), not ruins, ruins)
        ped('faq: nas %d frases do próprio FAQ (pergunta e variantes), toda resposta que vem do FAQ traz o código do PRÓPRIO item' % (len(itens) * 4), len(x['frases']) == 8 and all(i == f for i, q, f in x['frases']), x['frases'])
        # (revisão) o corte de 8 passos: nenhum item do FAQ tem mais de 8, então um item com 12 passos é plantado na cópia carregada (sem tocar o arquivo)
        longo = pg.evaluate("""() => { const B = window.CapitaoBrain, it = B.faqDados().itens.filter((x) => x.id === 'MO-02')[0], orig = it.passos; it.passos = Array.from({ length: 12 }, (_, k) => 'passo ' + (k + 1));
          const a = B.answer('x', { platform: 'app', commit: false, faq: 'MO-02' }); it.passos = orig; return a.text; }""")
        ped('faq: um item com 12 passos mostra os 8 primeiros e «… mais 4 passos no FAQ (MO-02).»', longo == texto_faq(dict(por['MO-02'], passos=['passo %d' % (k + 1) for k in range(12)])) and longo.count('\n8. passo 8\n… mais 4 passos no FAQ (MO-02).') == 1, longo[:300])
        ped('faq: o código vence a resposta pronta pedida (ctx.id não); com «MAYDAY» no texto o item pedido é o item; código inexistente ou número cai na rota normal',
            x['id'][0] != 'faqEquip' and x['id'][1] == 'MO-02' and x['id'][2] == 'checklist' and x['id'][3] == 'checklist', x['id'])
    finally:
        pg.ctx.close()
    # sem o arquivo (rede cortada): nada muda, nada lança
    pg = pagina(b, muta=muta, aborta=('**/faq-equipamentos.json',))
    try:
        r = pg.evaluate("""async () => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }; const ok = await B.carregaFaq();
          return { ok, pronto: B.faqPronto(), a: B.answer('água rasa: o que faço', op).key, b: B.answer('x', Object.assign({ faq: 'MO-02' }, op)).key, item: B.faqItem('MO-02'), busca: B.faqBusca('água rasa o que faço', 3) }; }""")
        ped('faq (sem o arquivo): carregaFaq devolve false e o chat segue como antes (fallback na pergunta, nada no código), sem erro', r['ok'] is False and r['pronto'] is False and r['a'] == 'fallback' and r['b'] == 'fallback' and r['item'] is None and r['busca'] == [], r)
    finally:
        pg.ctx.close()
    # modo real: o FAQ não depende da simulação (a mesma resposta)
    pg = pagina(b, extra=SEM_SIMULACAO, muta=muta)
    try:
        r = pg.evaluate("""async () => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }; await B.carregaFaq(); await new Promise((ok) => { B.carregaBase(); setTimeout(ok, 800); }); const a = B.answer('sonda mostrando pouca profundidade', op);
          return { key: a.key, faq: a.faq, text: a.text, src: a.src }; }""")
        ped('faq (simulacao false): a mesma resposta, com o código e a fonte', r['key'] == 'faqEquip' and r['faq'] == 'EL-08' and r['text'] == texto_faq(por['EL-08']), r)
    finally:
        pg.ctx.close()
    # o SOS: o arquivo nem é pedido, e o código não abre o FAQ
    pg = pagina(b, scripts=('capitao-dados.js', 'capitao-brain.js'), caminho='SOS-cerebro.html', fixo=None, muta=muta)
    try:
        pedidos = []
        pg.on('request', lambda rq: pedidos.append(rq.url) if 'faq-equipamentos' in rq.url else None)
        r = pg.evaluate("""async () => { const B = window.CapitaoBrain; await new Promise((ok) => setTimeout(ok, 1500)); const ok = await B.carregaFaq();
          return { ok, pronto: B.faqPronto(), k: B.answer('x', { platform: 'app', commit: false, faq: 'MO-02' }).key, item: B.faqItem('MO-02'), busca: B.faqBusca('água rasa o que faço') }; }""")
        ped('faq (SOS): o arquivo não é pedido, o código não abre o item e a busca é vazia', not pedidos and r['ok'] is False and r['pronto'] is False and r['k'] != 'faqEquip' and r['item'] is None and r['busca'] == [], (pedidos, r))
    finally:
        pg.ctx.close()
    # offline: o arquivo está no CORE do service worker (a instalação o guarda) e o site o serve
    sw = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sw.js'), encoding='utf-8').read()
    core = sw[sw.index('const CORE = ['):sw.index('].concat(TELAS')]
    ped("faq: './faq-equipamentos.json' está no CORE do sw.js (abre offline depois da instalação)", "'./faq-equipamentos.json'" in core and "'./base-conhecimento.json'" in core, '')


GRUPOS_3A['faq'] = grupo_faq
MUTANTES_3E_F10 = [
    ('p3e faq: o item de segurança do FAQ vai à IA', "    if (a && a.seguranca) return false;\n    if (cabecaEmerg", "    if (a && a.seguranca && a.key !== 'faqEquip') return false;\n    if (cabecaEmerg", ('faq',)),
    ('p3e faq: o cartão de emergência do FAQ leva o quadro na ficha', " || (a.key === 'faqEquip' && a.emerg === true));", ");", ('faq',)),
    ('p3e faq: o FAQ responde também no lugar do trecho do guia', "if (key === 'fallback' && !cabecaEmerg(pad(q))) { var fq = null;", "if ((key === 'fallback' || key === 'base') && !cabecaEmerg(pad(q))) { var fq = null;", ('faq',)),
    ('p3e faq: a cobertura solta toma a pergunta genérica', "if (!r || r.cobre < 1 || r.principal < 1 || r.titulo < 0.6) return null;", "if (!r || r.cobre < 0.34 || r.principal < 0.34 || r.titulo < 0.2) return null;", ('faq',)),
    ('p3e faq: o empate de seções não barra', "if (rs.length > 1 && rs[1].nota > r.nota * 0.85 && rs[1].it.secao !== r.it.secao) return null;", "", ('faq',)),
    ('p3e faq: a fonte sem o código do item', "src: 'Fonte: FAQ dos equipamentos ' + it.id + (fs.length", "src: 'Fonte: FAQ dos equipamentos' + (fs.length", ('faq',)),
    ('p3e faq: o código pedido (ctx.faq) é ignorado', "    if (typeof ctx.faq === 'string' && !ctx.id) { var fi = faqItem(ctx.faq); if (fi) return faqResposta(fi, p); }\n", "", ('faq',)),
    ('p3e faq: o corte de passos do FAQ sobe de 8 para 12', "var passos = it.passos || [], max = 8,", "var passos = it.passos || [], max = 12,", ('faq',)),
    ('p3e faq: o SOS busca o arquivo', "if (EM_SOS || !window.fetch) return Promise.resolve(false);\n    if (FAQ.itens)", "if (!window.fetch) return Promise.resolve(false);\n    if (FAQ.itens)", ('faq',)),
    # (a guarda de EM_SOS no faqItem é a 2ª trava, atrás da do carregaFaq: no SOS o arquivo nunca carrega, então tirá-la sozinha não muda nada — mutante equivalente, fora)
    ('p3e faq: a fala do item de segurança sai cortada', "if (a && (a.key === 'base' || a.key === 'faqEquip') && a.seguranca", "if (a && (a.key === 'base') && a.seguranca", ('faq',)),
    ('p3e faq: a pergunta de uma palavra busca', "    if (qs.length < 2) return [];\n", "    if (qs.length < 1) return [];\n", ('faq',)),
    ('p3e faq: a palavra genérica da identidade conta («em caso de alarme» abre o item do fogo)', "return a.indexOf(w) === k && !IDENT_GENERICAS[w]; });\n    if (qs.length < 2) return [];", "return a.indexOf(w) === k; });\n    if (qs.length < 2) return [];", ('faq',)),
    ('p3e faq: a baliza do canal vira o EPIRB', "      if (sinal && /EPIRB/.test(it.equip || '')) return;\n", "", ('faq',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3E_F10




# —— P3E, revisão 4: a CABEÇA DE EMERGÊNCIA (o predicado único do cérebro) ——
# A causa raiz dos bloqueios repetidos do P3E: cada rota nova listava à mão uma parte diferente dos predicados de emergência da route(). O cérebro tem agora UM predicado (cabecaEmerg: a união de tudo o que a
# route() entrega às rotas de emergência, com TODAS as palavras de CANAL16_SEG e CANAL16_ROTA) e UM despacho antecipado (equipRota) para a cabeça de equipamento de segurança. Este grupo lê as LISTAS do próprio
# arquivo do cérebro (nunca do cérebro mutante), gera a matriz cabeça × cauda a partir delas, nas duas ordens e em 12:01:00 e 12:01:45, e exige que toda pergunta mista termine LOCAL (pedeIA false, sem
# coordenada, sem o quadro: SOG, rumo, ETA, pessoas a bordo, hora do instante) na chave da cabeça (ou em outra chave de emergência: «qual o MMSI?» com o botão DISTRESS é o roteiro do rádio). Uma palavra nova nas
# listas passa a ser testada sozinha; os mutantes tiram cada palavra de todas as listas em que ela está.
BRAIN_TXT = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'capitao-brain.js'), encoding='utf-8').read()
LISTAS_CABECA = ('CANAL16_SEG', 'CANAL16_ROTA', 'EPIRB_PALAVRAS', 'SEAFIRE_PALAVRAS')


def palavras_lista(nome):
    m = re.search(r"var %s = \[([^\]]*)\];" % nome, BRAIN_TXT)
    assert m, 'lista %s não está no cérebro' % nome
    return re.findall(r"'([^']*)'", m.group(1))


PALAVRAS_CABECA = []
for _n in LISTAS_CABECA:
    for _w in palavras_lista(_n):
        if _w.strip() not in PALAVRAS_CABECA:
            PALAVRAS_CABECA.append(_w.strip())
# a cabeça de cada palavra («o canal 16», «o pan-pan», «o dsc», «o distress», «o vhf», «o radio», «o epirb»…) e a da baliza do EPIRB; mais uma de cada OUTRA rota de emergência
def palavras_ctx_baliza():
    m = re.search(r"var BALIZA_CTX = \{\}; \[([^\]]*)\]\.forEach", BRAIN_TXT)
    assert m, 'a lista BALIZA_CTX não está no cérebro'
    return re.findall(r"'([^']*)'", m.group(1))


# (revisão 5) a «baliza» sozinha é também a de balizamento: só é cabeça de emergência com contexto de EPIRB (uma palavra de BALIZA_CTX, lida do cérebro), sozinha com palavras neutras, ou junto de uma pergunta
# que tem rota própria. Uma cabeça por palavra do contexto («baliza teste», «baliza bateria», «baliza validade»…) entra na matriz com TODAS as caudas.
CTX_BALIZA = palavras_ctx_baliza()
CABECAS_BALIZA = ['baliza ' + w for w in CTX_BALIZA]
CABECAS_LISTAS = ['o ' + w for w in PALAVRAS_CABECA] + ['a baliza'] + CABECAS_BALIZA
CABECAS_OUTRAS = ['MAYDAY, homem ao mar', 'onde ficam os coletes', 'qual o MMSI', 'pressão de óleo baixa no motor BB', 'estamos em risco']
CABECAS_TODAS = CABECAS_LISTAS + CABECAS_OUTRAS
# as caudas: as da P3C, os 4 checklists, o estoque, a tendência, o FAQ, «pronto para sair?» e cada rota de dado do quadro SEM lista branca (a que levava a SOG, o rumo, o ETA, a hora do instante).
# A cauda de documentos fica de fora de propósito: «Licença de Estação» é papelada (docsvenc, local e sem quadro), a rota que a route() põe antes do rádio.
CAUDAS_CABECA = []
for _c in MISTAS_CAUDAS + ['checklist de abastecimento', 'checklist de chegada', 'checklist de saída', 'checklist de fundeio', 'quanto diesel temos?', 'pronto para sair?', 'quais peças temos?', 'que peça acabou?',
                           'o rotor do gerador está zerado?', 'qual a tendência do óleo?', 'água rasa: o que faço', 'como está o barco?', 'pendências abertas', 'qual a maré?', 'como está o clima?', 'para onde vamos?',
                           'é seguro sair hoje?', 'quantos metros de corrente?', 'qual a autonomia?', 'qual o consumo?', 'nível dos tanques', 'quanto falta para a troca de óleo?', 'onde estamos?', 'qual o vento?',
                           'o que tem no diário?', 'qual a velocidade?', 'qual o rumo?', 'quais as tendências?',
                           # (revisão 5) as formas novas do estoque: «tem <peça>?», «onde está <peça>?», o relato com «tem outro?»
                           'tem correia do alternador?', 'onde está o rotor do gerador?', 'o fusível queimou, tem outro?', 'temos fusível de 24 V?']:
    if _c not in CAUDAS_CABECA:
        CAUDAS_CABECA.append(_c)
EMERG_CHAVES = ('sos', 'oleo', 'canal16', 'epirb', 'seafire', 'salvatagem', 'mmsi')
QUADRO_RX = re.compile(r'\d+(?:,\d+)? nós|\bSOG\b|\bCOG\b|chegada prevista|\d+ pessoas a bordo|\b\d\d:\d\d:\d\d\b')
JS_CABECAS = """([t, qs]) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, op = { platform: 'app', commit: false }; R.fixar(t);
  return qs.map((q) => { const a = B.answer(q, op); return [q, a.key, B.pedeIA(a, q), !!a.seguranca, a.text, B.falaCurta(a), a.src || '']; }); }"""
_CHAVES_CABECA = {}


def chaves_cabecas(b):
    """A chave de cada cabeça SOZINHA no cérebro de verdade (nunca no mutante): é o que a pergunta mista tem de manter."""
    if not _CHAVES_CABECA:
        pg = pagina(b)
        try:
            pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); window.CapitaoBrain.carregaFaq(); setTimeout(r, 900); })")
            for q, k, *_ in pg.evaluate(JS_CABECAS, ['60', CABECAS_TODAS]):
                _CHAVES_CABECA[q] = k
        finally:
            pg.ctx.close()
    return _CHAVES_CABECA


_CAUDAS_SEM_ROTA = []


def caudas_sem_rota(b):
    """As caudas que NENHUMA rota do cérebro de verdade responde (o fallback, o trecho do guia ou o FAQ): com a «baliza» sozinha (ambígua: balizamento) elas não fazem a pergunta mista de emergência."""
    if not _CAUDAS_SEM_ROTA:
        pg = pagina(b)
        try:
            pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); window.CapitaoBrain.carregaFaq(); setTimeout(r, 900); })")
            for q, k, *_ in pg.evaluate(JS_CABECAS, ['60', CAUDAS_CABECA]):
                if k in ('fallback', 'base', 'faqEquip'):
                    _CAUDAS_SEM_ROTA.append(q)
        finally:
            pg.ctx.close()
    return _CAUDAS_SEM_ROTA


def pares_cabeca(b, cabecas):
    """(cabeça, cauda, ordem, pergunta) nas duas ordens. A baliza SIMPLES não se mistura com a cauda que não tem rota (ver CABECAS_BALIZA)."""
    sem = caudas_sem_rota(b)
    pares = []
    for h in cabecas:
        for c in CAUDAS_CABECA:
            if h == 'a baliza' and c in sem:
                continue
            pares.append((h, c, 'cabeça, cauda', h + ', ' + c))
            pares.append((h, c, 'cauda, cabeça', c.rstrip('?') + ', ' + h))
    return pares


def grupo_cabecas(b, muta, ped):
    chaves = chaves_cabecas(b)
    ped('cabeças: a chave de cada palavra das listas SOZINHA é a da família dela (CANAL16_ROTA → canal16, EPIRB_PALAVRAS → epirb, SEAFIRE_PALAVRAS → seafire; o «distress» do CANAL16_SEG e a «baliza» → o trecho de segurança, base)',
        all(chaves['o ' + w] == ('canal16' if w in [x.strip() for x in palavras_lista('CANAL16_ROTA')] else 'base') for w in [x.strip() for x in palavras_lista('CANAL16_SEG')])
        and all(chaves['o ' + w.strip()] == 'epirb' for w in palavras_lista('EPIRB_PALAVRAS')) and chaves['a baliza'] == 'base'
        and all(chaves['o ' + w.strip()] == ('sos' if w.strip() == 'sistema de incendio' else 'seafire') for w in palavras_lista('SEAFIRE_PALAVRAS'))
        and all(chaves['o ' + w.strip()] == 'canal16' for w in palavras_lista('CANAL16_ROTA')), {h: k for h, k in chaves.items() if h in CABECAS_LISTAS})
    pg = pagina(b, muta=muta)
    try:
        pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); window.CapitaoBrain.carregaFaq(); setTimeout(r, 900); })")
        # a cabeça SOZINHA no cérebro (mutante inclusive) tem de manter a chave de sempre: a palavra tirada de uma lista que a outra lista ou outro predicado ainda cobre só se denuncia aqui («o radiobaliza» vira canal16 pelo ' radio')
        sozinhas = pg.evaluate(JS_CABECAS, ['60', CABECAS_TODAS])
        ruins = [(q, k, 'esperado ' + chaves[q]) for q, k, *_ in sozinhas if k != chaves[q]]
        ped('cabeças: as %d cabeças sozinhas (uma de cada palavra das listas, a baliza e uma de cada outra rota de emergência) mantêm a chave da família' % len(CABECAS_TODAS), not ruins, ruins[:6])
        pares = pares_cabeca(b, CABECAS_TODAS)   # (cabeça, cauda, ordem, pergunta)
        for t in (('60', '105') if not muta else ('60',)):   # (o mutante da lista de palavras não depende do instante: só 12:01:00)
            res = pg.evaluate(JS_CABECAS, [t, [x[3] for x in pares]])
            ruins = []
            for (h, c, ordem, q), (_, key, ia, seg, texto, fala, src) in zip(pares, res):
                esp = chaves[h]
                tudo = texto + '\n' + fala + '\n' + src
                local = (not ia) and not confere.R_COORD.search(tudo) and not QUADRO_RX.search(tudo)
                if not ((key == esp or key in EMERG_CHAVES) and local and (key in EMERG_CHAVES or seg)):
                    ruins.append((q, key, 'esperado ' + esp, 'ia' if ia else '', 'quadro' if QUADRO_RX.search(tudo) else ''))
            ped('cabeças t=%s: as %d perguntas mistas (%d cabeças geradas das listas do cérebro × %d caudas, nas duas ordens) terminam LOCAL — na chave da cabeça (ou em outra de emergência), pedeIA false, sem coordenada, sem SOG, rumo, ETA, pessoas a bordo nem hora do instante'
                % (t, len(pares), len(CABECAS_TODAS), len(CAUDAS_CABECA)), not ruins, ruins[:12])
    finally:
        pg.ctx.close()
    # sem o guia carregado (o trecho de segurança do botão DISTRESS não vem) e com o FAQ: a cabeça de emergência continua local e o FAQ não a toma (a guarda do responde)
    pg = pagina(b, muta=muta, caminho='faq-equipamentos.json', aborta=('**/base-conhecimento.json',))
    try:
        pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaFaq(); setTimeout(r, 900); })")
        r = pg.evaluate("""() => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }; return ['teste da baliza', 'como testar a baliza', 'o botão DISTRESS, água rasa: o que faço', 'água rasa: o que faço'].map((q) => { const a = B.answer(q, op); return [a.key, a.faq || null, B.pedeIA(a, q)]; }); }""")
        ped('cabeças (sem o guia): «água rasa: o que faço» é o item EL-08 do FAQ; «teste da baliza» e «como testar a baliza» (que casam o item EP-02 do FAQ) e o botão DISTRESS na frase NÃO são do FAQ: ficam locais, sem IA, na instrução de segurança da família (a baliza → EPIRB, o botão DISTRESS → canal 16), nunca no fallback com o quadro (revisão 5)', r == [['epirb', None, False], ['epirb', None, False], ['canal16', None, False], ['faqEquip', 'EL-08', True]], r)
    finally:
        pg.ctx.close()


GRUPOS_3A['cabecas'] = grupo_cabecas


def mutantes_cabecas():
    """Um mutante por palavra: tira a palavra de TODAS as listas em que ela está (CANAL16_SEG e CANAL16_ROTA ficam numa região só). Ficam de fora os dois equivalentes por redundância proposital:
    «baliza disparou» (a EPIRB_REGEX pega do mesmo jeito), «sistema de incendio» (a lista SOS pega antes: a pergunta é o sos) e «sea fire» (o corrigeVoz da F31 troca «sea fire» por «Seafire» antes da rota)."""
    ms = []
    i0 = BRAIN_TXT.index('var CANAL16_SEG = ['); i1 = BRAIN_TXT.index('];', BRAIN_TXT.index('var CANAL16_ROTA = [')) + 2
    regiao = BRAIN_TXT[i0:i1]
    for w in sorted({x.strip() for x in palavras_lista('CANAL16_SEG') + palavras_lista('CANAL16_ROTA')}):
        ms.append(('p3e cabeças: «%s» sai do CANAL16_SEG e do CANAL16_ROTA' % w, regiao, regiao.replace("'%s'" % w, "'zz%s'" % w).replace("' %s'" % w, "' zz%s'" % w), ('cabecas',)))
    for nome, equiv in (('EPIRB_PALAVRAS', ('baliza disparou',)), ('SEAFIRE_PALAVRAS', ('sistema de incendio', 'sea fire'))):
        m = re.search(r"var %s = \[[^\]]*\];" % nome, BRAIN_TXT)
        for w in palavras_lista(nome):
            if w in equiv:
                continue
            ms.append(('p3e cabeças: «%s» sai do %s' % (w, nome), m.group(0), m.group(0).replace("'%s'" % w, "'zz%s'" % w), ('cabecas',)))
    return ms


MUTANTES_3E_CABECAS = mutantes_cabecas() + [
    ('p3e cabeças: a baliza do EPIRB deixa de ser cabeça de emergência', r"if (EM_BALIZA || !has(q, ['baliza'])) return false;", r"if (EM_BALIZA || !has(q, ['xbaliza'])) return false;", ('cabecas',)),
    ('p3e cabeças: a baliza de sinalização (canal, cardinal, luz) também é cabeça de emergência', r"    if (qs.some(function (w) { return SINAL_RAIZES[w]; }) && !qs.some(function (w) { return EPIRB_SO[w]; })) return false;" "\n", r"", ('checklist', 'rev5')),
    ('p3e cabeças: sem o despacho antecipado da cabeça de equipamento (as rotas de dado a tomam)', r"var eq = equipRota(q); if (eq) return eq;", r"", ('cabecas',)),
    ('p3e cabeças: o despacho antecipado não vê o EPIRB', r"    if (epirbRelato(q)) return 'epirb';" "\n" r"    if (seafirePergunta(q)) return 'seafire';" "\n" r"    if (has(q, DOC_PALAVRAS)) return null;", r"    if (seafirePergunta(q)) return 'seafire';" "\n" r"    if (has(q, DOC_PALAVRAS)) return null;", ('cabecas',)),
    ('p3e cabeças: o despacho antecipado não vê o Seafire', r"    if (seafirePergunta(q)) return 'seafire';" "\n" r"    if (has(q, DOC_PALAVRAS)) return null;", r"    if (has(q, DOC_PALAVRAS)) return null;", ('cabecas',)),
    ('p3e cabeças: o despacho antecipado não vê o canal 16, o rádio e o VHF', r"    if (has(q, CANAL16_ROTA)) return 'canal16';" "\n" r"    if (cabecaSemRota(q)", r"    if (cabecaSemRota(q)", ('cabecas',)),
    ('p3e cabeças: o despacho antecipado não vê o botão DISTRESS nem a baliza (sem rota própria)', r"    if (cabecaSemRota(q) && !SOBRE.test(q) && !has(q, ['ajuda'])) return 'fallback';", r"", ('cabecas',)),
    ('p3e cabeças: a Licença de Estação do rádio vira o roteiro do canal 16 (sem a exceção dos documentos)', r"    if (has(q, DOC_PALAVRAS)) return null;", r"", ('checklist', 'pecas')),
    ('p3e cabeças: a pergunta sobre o app com a baliza vira o trecho dela (sem a exceção do SOBRE e do «ajuda»)', r"if (cabecaSemRota(q) && !SOBRE.test(q) && !has(q, ['ajuda'])) return 'fallback';", r"if (cabecaSemRota(q)) return 'fallback';", ('checklist',)),
    ('p3e cabeças: a cabeça sem rota própria (DISTRESS, baliza) com cauda de dado vai ao fallback (sem o trecho dela)', r"if (rota0 === 'fallback' && (key === 'fallback' || key === 'base') && !a.seguranca) {", r"if (false) {", ('cabecas',)),
    ('p3e cabeças: a cabeça sem rota própria fica com o trecho da cauda (sem trocar o trecho que não é de segurança)', r"(key === 'fallback' || key === 'base') && !a.seguranca) {", r"(key === 'fallback') && !a.seguranca) {", ('cabecas',)),
    ('p3e cabeças: o pedeIA não barra a cabeça de emergência', r"    if (cabecaEmerg(pad(String(q || '')))) return false;", r"", ('checklist',)),
    ('p3e cabeças: o FAQ toma a pergunta de cabeça de emergência', r"if (key === 'fallback' && !cabecaEmerg(pad(q))) { var fq = null;", r"if (key === 'fallback') { var fq = null;", ('cabecas',)),
    ('p3e cabeças: o estoque de peças toma a pergunta de cabeça de emergência (sem a guarda do topo)', r"  function pecasPergunta(q) {" "\n" r"    if (cabecaEmerg(q)) return false;", r"  function pecasPergunta(q) {", ('pecas',)),
    ('p3e cabeças: o checklist toma a pergunta de cabeça de emergência (sem a guarda)', r"    if (!cabecaEmerg(q)) {", r"    if (true) {", ('checklist',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3E_CABECAS

# —— P3E, revisão 4: os mutantes do inteiro puro, do desempate, do estoque (acabou/zerado/preciso), da 1ª linha da lista, da ficha, do FAQ e do «pronto para sair» ——
MUTANTES_3E_REV4 = [
    ('p3e rev4: o inteiro puro aceita o prefixo numérico («12abc», «1e2»)', r"/^\d{1,3}$/.test(v.trim())", r"/^\d{1,3}/.test(v.trim())", ('pecas',)),
    ('p3e rev4: o inteiro puro arredonda a fração (3.7 vira 4)', r"return Number.isInteger(n) && n >= 0 && n <= 999 ? n : null;", r"return isFinite(n) && n >= 0 && n <= 999 ? Math.round(n) : null;", ('pecas',)),
    ('p3e rev4: o inteiro puro aceita até 9999', r"return Number.isInteger(n) && n >= 0 && n <= 999 ? n : null;", r"return Number.isInteger(n) && n >= 0 && n <= 9999 ? n : null;", ('pecas',)),
    ('p3e rev4: o + PEÇA com número inválido cadastra mesmo assim', r"    if (qtd === null || mn === null) return null;", r"", ('pecas',)),
    ('p3e rev4: o + PEÇA sem quantidade ou mínimo é recusado', r"function intPecaOpc(v) { return v == null || (typeof v === 'string' && !v.trim()) ? 0 : intPeca(v); }", r"function intPecaOpc(v) { return intPeca(v); }", ('pecas',)),
    ('p3e rev4: o desempate não pesa a palavra do núcleo da peça (o «motor» empata com a correia)', r"soma + (nt.indexOf(w) === -1 ? 0 : pw.indexOf(w) !== -1 ? 100 : 1)", r"soma + (nt.indexOf(w) === -1 ? 0 : 1)", ('pecas',)),
    ('p3e rev4: nenhuma palavra da pergunta é «da peça» (o desempate some)', r"pw = ws.filter(function (w) { return nucleos.some(function (nu) { return nu.indexOf(w) !== -1; }); });", r"pw = [];", ('pecas',)),
    ('p3e rev4: «acabou» e «acabaram» não pedem estoque', r"'acabando', 'acabou', 'acabaram', 'esgot', 'zerad',", r"'acabando', 'esgot', 'zerad',", ('pecas',)),
    ('p3e rev4: «peça zerada / acabou / no mínimo» sem artigo não é pergunta de estoque', r"' peca zerad', ' peca acab', ' peca esgot', ' peca falt', ' peca no minimo', ' peca abaixo'", r"' pecaxx'", ('pecas',)),
    ('p3e rev4: a peça pelo nome com o estado dela («o rotor do gerador está zerado?») sai do estoque', r"      || (PECAS_SEM_ESTOQUE.test(q) && sujeitoPeca(q))", r"", ('pecas',)),
    ('p3e rev4: o estado + qualquer palavra de peça na frase vira estoque (o fluxo do filtro está zerado)', r"(PECAS_SEM_ESTOQUE.test(q) && sujeitoPeca(q))", r"(PECAS_SEM_ESTOQUE.test(q) && nomeCadastrado(q))", ('pecas',)),
    ('p3e rev4: o sujeito da peça não pula os artigos', r"    while (j < ps.length && (PECAS_ARTIGOS + PECAS_ABRE).indexOf(' ' + ps[j] + ' ') !== -1) j++;", r"", ('pecas',)),
    ('p3e rev4: o sujeito da peça não pula o «por que»', r"var PECAS_ABRE = ' por que porque sera que ja ainda entao e mas ';", r"var PECAS_ABRE = ' ';", ('pecas',)),
    ('p3e rev4: «preciso de rotor» não é estoque', r"      || (/ (?:preciso|precisamos|precisa|precisar) /.test(q) && objetoPeca(q, PECAS_VERBOS_PRECISA))", r"", ('pecas',)),
    ('p3e rev4: «acabou de chegar / de quebrar» é estoque', r"var PECAS_FORA = [' acabou de ', ' acabaram de ', 'gasolina',", r"var PECAS_FORA = ['gasolina',", ('pecas',)),
    ('p3e rev4: a 1ª linha da lista inteira não nomeia as zeradas', r"'Peças a bordo: ' + corpo(todas) + '\n' + todas.map(linha).join('\n')", r"'Peças a bordo: ' + todas.length + ' cadastradas' + resumo(todas) + '\n' + todas.map(linha).join('\n')", ('pecas',)),
    ('p3e rev4: a ficha da IA sem o bloco «## Peças»', r"    bloco('Peças', function () { return fichaPecas(semSim); });" "\n", r"", ('pecas',)),
    ('p3e rev4: a ficha da IA leva as peças do aparelho mesmo com a simulacao false', r"return fichaPecas(semSim); });", r"return fichaPecas(false); });", ('pecas',)),
    ('p3e rev4: o bloco «## Peças» sai também sem peça cadastrada (SOS)', r"    if (!l.length) return null;" "\n" r"    return { text: l.length + (l.length === 1 ?", r"    return { text: l.length + (l.length === 1 ?", ('pecas',)),
    ('p3e rev4: o FAQ sem o título na 1ª linha', r"var text = (it.titulo && !it.emerg ? it.titulo + ' — ' : '') + it.resposta", r"var text = it.resposta", ('faq',)),
    ('p3e rev4: o cartão de emergência do FAQ abre com o título', r"var text = (it.titulo && !it.emerg ? it.titulo + ' — ' : '') + it.resposta", r"var text = (it.titulo ? it.titulo + ' — ' : '') + it.resposta", ('faq',)),
    ('p3e rev4: «pronto para sair?» não é o checklist de saída', r"|| (PRONTO_SAIR.test(q) && leitura(q, CHECK_ANTES_OK));", r";", ('checklist', 'faq')),
    ('p3e rev4: «prontos para zarpar?» (plural) não é o checklist de saída', r"var PRONTO_SAIR = / prontos? (?:para|pra)", r"var PRONTO_SAIR = / pronto (?:para|pra)", ('checklist', 'faq')),
    ('p3e rev4: «estamos prontos para sair?» não é o checklist de saída (a lista branca não tem estamos, pronto, tudo)', r"antes largar sair zarpar saida barco lancha embarcacao para pra estamos pronto prontos tudo ja ';", r"antes largar sair zarpar saida barco lancha embarcacao para pra ';", ('checklist', 'faq')),
    ('p3e rev4: a leitura da pressão do óleo toma a cabeça de equipamento («onde fica o EPIRB, qual a pressão do óleo?»)', r"    var eq = equipRota(q); if (eq) return eq;" "\n" r"    if (ol) return 'oleoLeitura';", r"    if (ol) return 'oleoLeitura';" "\n" r"    var eq = equipRota(q); if (eq) return eq;", ('cabecas',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3E_REV4


# ——— Fase 3, P3E, revisão 5 ———
# (1) a «baliza» de balizamento (cor, lado, luz, estado, tipo) não é o EPIRB: vai à IA (fallback, pedeIA true), e o trecho do EPIRB não aparece; (2) a baliza do EPIRB com contexto (teste, bateria, validade, acionamento…) ou
# sozinha segue local; (3) a cabeça de emergência SEM o guia (nem o FAQ) termina local, na instrução de segurança da família, sem o quadro; (4) o estoque responde «tem <peça>?», «onde está <peça>?» e «o fusível queimou,
# tem outro?»; (5) a gravação em capitao.pecas.v1 parte do que está guardado; (6) a pressão de óleo estável abaixo do mínimo normal é ATENÇÃO e o texto diz isso.
BALIZA_SINAL_R5 = ['qual a cor da baliza de boreste?', 'qual a baliza de bombordo?', 'passei pela baliza vermelha', 'vi uma baliza apagada', 'baliza luminosa', 'baliza de sinalização apagada', 'baliza náutica',
                   'como funciona a baliza?', 'a baliza está fora do lugar', 'baliza fora de posição', 'baliza verde', 'a baliza está torta', 'baliza de bombordo ou boreste?', 'tem baliza no canal?',
                   'qual a baliza para entrar na barra?', 'passamos pela baliza amarela', 'a baliza cardinal norte está apagada?', 'baliza de perigo isolado', 'a baliza de perigo isolado está apagada?']
BALIZA_EPIRB_R5 = ['a baliza', 'cadê a baliza?', 'bateria da baliza', 'validade da baliza', 'como acionar a baliza', 'autoteste da baliza']
ROTAS_P3E_R5_PECAS = [
    # «tem <peça cadastrada>?» sem sujeito antes do verbo, «reserva / sobressalente» depois da peça, o vocativo, «onde está / fica / guardamos / cadê <peça>?» e o relato com o pedido de outra
    ('tem correia do alternador?', 'pecas', False), ('tem escova do limpador?', 'pecas', False), ('tem fusível reserva?', 'pecas', False), ('tem rotor reserva?', 'pecas', False), ('temos correia reserva?', 'pecas', False),
    ('cadê o rotor?', 'pecas', False), ('o fusível queimou, tem outro?', 'pecas', False), ('temos fusível de 24 V?', 'pecas', False), ('onde está o rotor do gerador?', 'pecas', False),
    ('onde fica o filtro de óleo?', 'pecas', False), ('onde ficam os anodos?', 'pecas', False), ('onde guardamos o impeller?', 'pecas', False), ('há fusível de reserva?', 'pecas', False),
    ('ainda tem rotor?', 'pecas', False), ('você tem filtro de óleo?', 'pecas', False), ('a gente tem escova do limpador?', 'pecas', False), ('a correia estragou, temos outra?', 'pecas', False),
    ('tem rotor para o gerador?', 'pecas', False), ('onde está a escova', 'pecas', False), ('o painel tem fusível reserva?', 'pecas', False), ('o barco tem rotor extra?', 'pecas', False),
    ('capitão, tem correia do alternador?', 'pecas', False), ('capitão, quantos filtros temos?', 'pecas', False), ('ei capitão, tem rotor de reposição?', 'pecas', False), ('tem correia do alternador, capitão?', 'pecas', False),
    # o que ela não rouba: a peça instalada (sujeito antes do verbo, lugar), o equipamento, o relato de falha sem pedido de outra, o motor que queimou, o que não é peça cadastrada
    ('o motor tem filtro?', 'base', True), ('a bomba tem rotor?', 'base', True), ('tem rotor no gerador?', 'base', True), ('tem anodo no casco?', 'fallback', True), ('o fusível queimou', 'fallback', True),
    ('o fusível queimou, o que faço?', 'fallback', True), ('a correia estragou, como troco?', 'fallback', True), ('o motor queimou, tem outro?', 'motores', False), ('onde fica o alternador?', 'fallback', True),
    ('tem gelo a bordo?', 'fallback', True), ('onde está o motor?', 'motores', False), ('o apito está tocando', 'fallback', True), ('tem apito reserva?', 'fallback', True), ('tem peça?', 'fallback', True),
]
ROTAS_P3E_R5 = [(q, 'fallback', True) for q in BALIZA_SINAL_R5] + [(q, 'base', False) for q in BALIZA_EPIRB_R5] + ROTAS_P3E_R5_PECAS
CASOS = CASOS + [(q, k) for q, k, _ in ROTAS_P3E_R5]
PEDE_IA.update({q: ia for q, k, ia in ROTAS_P3E_R5})
# a 1ª linha (e a falada) de «onde está <peça>?»: o LOCAL do cadastro e quantas há; mais de 3 peças, a 1ª linha de sempre
ONDE_PECAS_R5 = [('onde está o rotor do gerador?', 'Onde ficam: rotor (impeller) do gerador — caixa de sobressalentes B (0 a bordo, zerada).'),
                 ('cadê a escova do limpador?', 'Onde ficam: escova do limpador do para-brisa — armário de ferramentas (2 a bordo).'),
                 ('onde ficam os anodos?', 'Onde ficam: jogo de anodos do eixo e do casco — estante técnica 3 (1 a bordo, no mínimo ou abaixo); anodo do trocador de calor do estabilizador — caixa de sobressalentes B (2 a bordo).')]
PECAS_PLANTADO_R5 = "{ novas: [{ id: 'x1', n: 'Peça de outra versão', qtd: '3', extra: 'n' }, null, 5], movs: [{ id: 'p01', dq: '-1', iso: '2026-01-01T00:00:00.000Z' }, { id: 'p01', dq: -1, iso: '2026-01-02T00:00:00.000Z', extra: 'a' }, 'texto', null], extra: { a: 1 }, v: 2 }"
JS_PECAS_R5 = """() => { const B = window.CapitaoBrain, K = 'capitao.pecas.v1', out = {}; localStorage.clear();
  localStorage.setItem(K, JSON.stringify(PLANTADO)); out.ant = JSON.parse(localStorage.getItem(K));
  out.u = !!B.usaPeca('p02'); out.d1 = JSON.parse(localStorage.getItem(K));
  out.n = !!B.addPeca({ n: 'Peça nova', qtd: 2 }); out.d2 = JSON.parse(localStorage.getItem(K));
  out.formas = ['[1,2]', 'não é json', '{"movs":"x","novas":3}', '"texto"', '{"movs":{"a":1},"movsAntes":"y"}'].map((v) => { localStorage.setItem(K, v);
    const u = !!B.usaPeca('p02'), a = !!B.addPeca({ n: 'Outra', qtd: 1 }); return [v, u, a, JSON.parse(localStorage.getItem(K)), B.pecas().length]; });
  return out; }""".replace('PLANTADO', PECAS_PLANTADO_R5)
JS_ONDE_R5 = """() => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }; window.CapitaoReplay.fixar('60'); localStorage.clear();
  return QS.map((q) => { const a = B.answer(q, op); return [q, a.key, a.text.split('\\n')[0], B.falaCurta(a), B.pedeIA(a, q)]; }); }""".replace('QS', json.dumps([q for q, _ in ONDE_PECAS_R5] + ['onde ficam os filtros?', 'onde ficam as peças sobressalentes?'], ensure_ascii=False))
JS_OLEO_R5 = """([sim, a, b_]) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, D = window.CapitaoDados, h = D.historico.cruzeiro;
  if (sim) { const orig = R.quadro; R.quadro = function (t) { return Object.assign({}, orig.call(R, t), { motor_bb_oleo_bar: a, motor_be_oleo_bar: b_ }); }; }
  else ['motor_bb_oleo_bar', 'motor_be_oleo_bar'].forEach((c) => { const s = h[c]; s.d = Array.from({ length: 60 }, (_, k) => Math.round((a - k * b_) * s.escala)); });
  const x = B.preditiva().filter((y) => y.id === 'oleo_cruzeiro')[0]; return x && { texto: x.texto, nivel: x.nivel, rotulo: x.rotulo }; }"""


def local_cabeca(texto, fala, src):
    tudo = texto + '\n' + fala + '\n' + src
    return not confere.R_COORD.search(tudo) and not QUADRO_RX.search(tudo)


def grupo_rev5(b, muta, ped):
    # (1) a baliza de balizamento vai à IA (fallback, pedeIA true, sem o trecho do EPIRB); a do EPIRB (sozinha, teste, bateria, validade, acionamento) é o trecho de segurança, local; nos dois instantes
    pg = pagina(b, muta=muta)
    try:
        pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); window.CapitaoBrain.carregaFaq(); setTimeout(r, 900); })")
        for t in ('60', '105'):
            res = pg.evaluate(JS_CABECAS, [t, BALIZA_SINAL_R5 + BALIZA_EPIRB_R5])
            ruins = []
            for q, key, ia, seg, texto, fala, src in res:
                if q in BALIZA_SINAL_R5:
                    if not (key == 'fallback' and ia and not seg and 'EPIRB' not in texto):
                        ruins.append((q, key, ia))
                elif not (key == 'base' and not ia and seg and local_cabeca(texto, fala, src)):
                    ruins.append((q, key, ia, seg))
            ped('rev5 t=%s: as %d perguntas de balizamento (cor, lado, luz, estado, tipo) vão à IA — fallback, pedeIA true, sem o trecho do EPIRB — e as %d da baliza do EPIRB (sozinha, onde fica, bateria, validade, acionar, autoteste) são o trecho de segurança, local'
                % (t, len(BALIZA_SINAL_R5), len(BALIZA_EPIRB_R5)), not ruins, ruins[:8])
        for t in ('60', '105'):
            pg.evaluate("(x) => window.CapitaoReplay.fixar(x)", t)
            res = pg.evaluate(JS_P3C_CHAVES, [[q] for q, _, _ in ROTAS_P3E_R5_PECAS])
            ruins = [(q, esp, ia_esp, key, ia) for (q, esp, ia_esp), (key, ia) in zip(ROTAS_P3E_R5_PECAS, res) if key != esp or ia != ia_esp]
            ped('rev5 t=%s: as %d perguntas do estoque («tem <peça>?», «reserva», «onde está <peça>?», o vocativo, o relato com «tem outro?») e as que ela não rouba (o equipamento, a peça instalada, o relato sem pedido de outra) caem na chave certa' % (t, len(ROTAS_P3E_R5_PECAS)), not ruins, ruins[:6])
        # a palavra que TEM «baliza» dentro e escapa da troca (a route() sobre o resto a veria de novo) não prende o cérebro: a guarda de volta
        x = pg.evaluate("() => { try { const B = window.CapitaoBrain, a = B.answer('rebaliza, qual a velocidade?', { platform: 'app', commit: false }); return [a.key, null]; } catch (e) { return [null, String(e).slice(0, 80)]; } }")
        ped('rev5: «rebaliza, qual a velocidade?» (a palavra com «baliza» dentro que a troca não tira) responde sem voltar a si mesma (nenhuma exceção de pilha)', x[1] is None, x)
        # a baliza de balizamento com um dado junto segue o dado (a maré, o checklist), com o quadro; é só a baliza com a pergunta de EPIRB que é emergência
        r = pg.evaluate(JS_CABECAS, ['60', ['a baliza vermelha, checklist de saída', 'a baliza do canal está apagada, qual a maré?']])
        ped('rev5: a baliza de balizamento com um dado junto segue o dado (checklist, maré), nunca o EPIRB', [x[1] for x in r] == ['checklist', 'mare'] and all(not x[3] for x in r), [(x[0], x[1]) for x in r])
    finally:
        pg.ctx.close()
    # (3) SEM o guia (e sem o guia nem o FAQ): TODA cabeça de emergência, sozinha e misturada com cada cauda, nas duas ordens, em 12:01:00 e 12:01:45, termina na chave de emergência, local — a instrução de segurança da
    # família, nunca o fallback com a situação de bordo (SOG, proa, hora do quadro) nem a IA
    familia = {'teste da baliza': 'epirb', 'como testar a baliza': 'epirb', 'o botão DISTRESS': 'canal16', 'onde fica o botão DISTRESS?': 'canal16', 'o distress': 'canal16'}
    for nome, aborta, caminho in (('sem o guia', ('**/base-conhecimento.json',), 'faq-equipamentos.json'), ('sem o guia nem o FAQ', ('**/base-conhecimento.json', '**/faq-equipamentos.json'), 'integracoes/integracoes.json')):
        pg = pagina(b, muta=muta, caminho=caminho, aborta=aborta)
        try:
            pg.evaluate("() => new Promise(r => { if (window.CapitaoBrain.carregaFaq) window.CapitaoBrain.carregaFaq(); setTimeout(r, 900); })")
            res = pg.evaluate(JS_CABECAS, ['60', list(familia)])
            ped('rev5 (%s): «teste da baliza» e «como testar a baliza» são o procedimento do EPIRB e o botão DISTRESS o do canal 16 — local, sem IA, sem o quadro (nunca o fallback)' % nome,
                all(key == familia[q] and not ia and local_cabeca(texto, fala, src) for q, key, ia, seg, texto, fala, src in res), [(q, key, ia) for q, key, ia, *_ in res])
            pares = [(h, '', '', h) for h in CABECAS_TODAS] + pares_cabeca(b, CABECAS_TODAS)
            for t in (('60', '105') if not muta else ('60',)):
                res = pg.evaluate(JS_CABECAS, [t, [x[3] for x in pares]])
                ruins = []
                for (h, c, ordem, q), (_, key, ia, seg, texto, fala, src) in zip(pares, res):
                    if not (key in EMERG_CHAVES and not ia and local_cabeca(texto, fala, src)):
                        ruins.append((q, key, 'ia' if ia else '', 'quadro' if QUADRO_RX.search(texto + fala + src) else ''))
                ped('rev5 t=%s (%s): as %d cabeças sozinhas e as %d perguntas mistas (cabeça × cauda, nas duas ordens) terminam local, em chave de emergência, sem IA, sem coordenada, sem SOG, rumo, ETA, pessoas a bordo nem hora do instante'
                    % (t, nome, len(CABECAS_TODAS), len(pares) - len(CABECAS_TODAS)), not ruins, ruins[:10])
        finally:
            pg.ctx.close()
    # (4) o estoque: a 1ª linha de «onde está <peça>?» diz o LOCAL do cadastro e quantas há (até 3 peças; mais que isso, a 1ª linha de sempre); a falada leva o local
    pg = pagina(b, muta=muta)
    try:
        r = pg.evaluate(JS_ONDE_R5)
        quer = ONDE_PECAS_R5
        ped('rev5: «onde está / cadê / onde ficam <peça>?» abre com «Onde ficam: <peça> — <local do cadastro> (N a bordo…)», é do estoque (pecas), local, e a falada leva o local',
            all(k == 'pecas' and l1 == esp and 'Onde ficam' in fala and ia is False for (q, esp), (_, k, l1, fala, ia) in zip(quer, r[:3]))
            and 'caixa de sobressalentes B' in r[0][3] and 'armário de ferramentas' in r[1][3] and 'estante técnica 3' in r[2][3], r[:3])
        ped('rev5: «onde ficam os filtros?» (5 peças) e «onde ficam as peças sobressalentes?» (sem nome) NÃO abrem com «Onde ficam: »: a 1ª linha de sempre (a lista e o resumo)', all(k == 'pecas' and not l1.startswith('Onde ficam:') for _, k, l1, *_ in r[3:]), r[3:])
        x = pg.evaluate("""() => { const B = window.CapitaoBrain, op = { platform: 'app', commit: false }; localStorage.clear(); B.addPeca({ n: 'Lâmpada de navegação', qtd: 2 });
          const a = B.answer('onde está a lâmpada?', op); return [a.key, a.text.split('\\n')[0]]; }""")
        ped('rev5: a peça cadastrada sem local diz «sem local cadastrado» na 1ª linha («Onde ficam»)', x == ['pecas', 'Onde ficam: lâmpada de navegação — sem local cadastrado (2 a bordo).'], x)
        # o iso do movimento novo é único entre TODAS as linhas guardadas (as que a leitura filtra também): com o relógio parado, a linha crua de dq em texto que já tem o iso de agora não o repete
        x = pg.evaluate("""() => { const B = window.CapitaoBrain, K = 'capitao.pecas.v1', T = 1767225600000, orig = Date.now; Date.now = () => T; localStorage.clear();
          localStorage.setItem(K, JSON.stringify({ movs: [{ id: 'zz', dq: 'x', iso: new Date(T).toISOString() }, { id: 'zz', dq: 'x', iso: new Date(T + 1).toISOString() }] }));
          B.usaPeca('p01'); Date.now = orig; const m = JSON.parse(localStorage.getItem(K)).movs; return [m.length, (m[2] || {}).iso, m.map((y) => y.iso)]; }""")
        ped('rev5: o iso do movimento novo não repete o de nenhuma linha guardada (com o relógio parado, pula as duas linhas cruas que já o têm)', x[0] == 3 and len(set(x[2])) == 3 and x[1] == '2026-01-01T00:00:00.002Z', x)
        # (5) a gravação parte do que está guardado: nenhuma linha, nenhuma chave de topo e nenhum valor de outra forma some (o registro só cresce)
        r = pg.evaluate(JS_PECAS_R5)
        ant, d1, d2 = r['ant'], r['d1'], r['d2']
        ped('rev5: o −1 USADA acrescenta UMA linha ao fim de movs e deixa TUDO o mais como estava: as 4 linhas anteriores (inclusive a de dq em texto, a de campo extra, o texto e o null), as 3 novas (inclusive o null e o número), a chave `extra` e a `v`',
            r['u'] and d1['movs'][:4] == ant['movs'] and len(d1['movs']) == 5 and d1['movs'][4]['id'] == 'p02' and d1['movs'][4]['dq'] == -1 and d1['novas'] == ant['novas'] and d1['extra'] == {'a': 1} and d1['v'] == 2, d1)
        ped('rev5: o + PEÇA acrescenta UMA peça ao fim de novas e deixa as movs, as chaves `extra` e `v` e as 3 novas anteriores como estavam', r['n'] and d2['novas'][:3] == ant['novas'] and len(d2['novas']) == 4 and d2['novas'][3]['n'] == 'Peça nova'
            and d2['movs'] == d1['movs'] and d2['extra'] == {'a': 1} and d2['v'] == 2, d2)
        f = {v: (u, a, st, n) for v, u, a, st, n in r['formas']}
        g = lambda v, k: (f[v][2] or {}).get(k)   # (o campo que falta é falha da conferência, não queda do teste)
        ped('rev5: valor guardado de outra forma (lista, texto, JSON ruim) fica em `antes` e a linha nova entra em movs/novas', g('[1,2]', 'antes') == [1, 2] and g('não é json', 'antes') == 'não é json' and g('"texto"', 'antes') == 'texto'
            and all(len(g(v, 'movs') or []) == 1 and (g(v, 'novas') or [{}])[0].get('n') == 'Outra' and f[v][0] and f[v][1] for v in ('[1,2]', 'não é json', '"texto"')), f)
        ped('rev5: o campo que não é lista fica em `<campo>Antes` (e o campo recomeça lista; um `movsAntes` que já existia não é pisado: o novo ganha `_`)', g('{"movs":"x","novas":3}', 'movsAntes') == 'x' and g('{"movs":"x","novas":3}', 'novasAntes') == 3
            and g('{"movs":{"a":1},"movsAntes":"y"}', 'movsAntes') == 'y' and g('{"movs":{"a":1},"movsAntes":"y"}', 'movsAntes_') == {'a': 1} and len(g('{"movs":"x","novas":3}', 'movs') or []) == 1, f['{"movs":{"a":1},"movsAntes":"y"}'])
    finally:
        pg.ctx.close()
    # (6) a pressão de óleo em cruzeiro abaixo do mínimo normal (2,4 bar) é ATENÇÃO e o texto diz «abaixo do mínimo normal», estável ou caindo; sem a simulação a pressão é a da última semana do histórico, com ela é a da volta de hoje
    for extra, args, quer, rot in ((SEM_SIMULACAO, [False, 2.0, 0.0], r'^Pressão de óleo em cruzeiro abaixo do mínimo normal de 2,4 bar: BB 2,0 bar · BE 2,0 bar, estável há 60 dias\.$', 'histórico estável em 2,0 bar'),
                                   (SEM_SIMULACAO, [False, 2.9, 0.015], r'^Pressão de óleo em cruzeiro abaixo do mínimo normal de 2,4 bar: BB 2,\d bar · BE 2,\d bar, caindo há 60 dias\.$', 'histórico caindo de 2,9 a 2,0 bar'),
                                   ('', [True, 3.2, 2.0], r'^Pressão de óleo em cruzeiro abaixo do mínimo normal de 2,4 bar: BB 3,2 bar · BE 2,0 bar, estável há 60 dias\.$', 'volta de hoje com o BB em 3,2 e o BE (o menor) em 2,0 bar')):
        pg = pagina(b, extra=extra, muta=muta)
        try:
            x = pg.evaluate(JS_OLEO_R5, args)
            ped('rev5 (óleo, %s): ATENÇÃO e o texto diz «abaixo do mínimo normal de 2,4 bar» (nunca «estável» sem dizer isso)' % rot, bool(x) and x['nivel'] == 'atencao' and x['rotulo'] == 'ATENÇÃO' and re.match(quer, x['texto']) is not None, x)
        finally:
            pg.ctx.close()


GRUPOS_3A['rev5'] = grupo_rev5


def mutantes_ctx_baliza():
    """Um mutante por palavra do contexto de EPIRB da baliza (BALIZA_CTX): a palavra sai da lista. Ficam de fora (equivalentes por redundância proposital, medidos) as palavras que o cérebro já pega por
    outro caminho: as de emergência da lista SOS (sos, socorro, emergência) e as que são, sozinhas, a rota de um assunto (a prova 3 já faz da baliza a cabeça: bateria, vence, teste, perigo…)."""
    m = re.search(r"var BALIZA_CTX = \{\}; \[[^\]]*\]\.forEach", BRAIN_TXT)
    regiao = m.group(0)
    return [('p3e rev5 baliza: «%s» sai do contexto de EPIRB' % w, regiao, regiao.replace("'%s'" % w, "'zz%s'" % w, 1), ('cabecas', 'rev5')) for w in CTX_BALIZA if w not in CTX_BALIZA_EQUIVALENTES]


# (equivalentes por redundância proposital, medidos: a palavra já é pega por outro caminho — a lista do EPIRB, a lista SOS ou a rota própria dela, que faz da baliza a cabeça pela prova 3)
CTX_BALIZA_EQUIVALENTES = ('epirb', 'radiobaliza', 'sos', 'socorro', 'emergencia', 'bateria', 'vence', 'venceu')
MUTANTES_3E_REV5 = mutantes_ctx_baliza() + [
    # a baliza de balizamento × a do EPIRB (as três provas)
    ('p3e rev5 baliza: sem o contexto de EPIRB (a prova 1)', r"if (qs.some(function (w) { return BALIZA_CTX[w]; }) || soNeutras(", r"if (false || soNeutras(", ('rev5', 'cabecas')),
    ('p3e rev5 baliza: sem a prova da baliza sozinha (a prova 2)', r" || soNeutras(semVocativo(q).replace(/ por favor /g, ' '), BALIZA_OK)) return true;", r") return true;", ('rev5', 'cabecas')),
    ('p3e rev5 baliza: sem a prova da pergunta mista (a prova 3)', r"    return rota !== 'fallback';", r"    return false;", ('cabecas', 'rev5')),
    ('p3e rev5 baliza: a prova 3 vale sempre (toda pergunta com «baliza» é cabeça de emergência)', r"    return rota !== 'fallback';", r"    return true;", ('rev5',)),
    ('p3e rev5 baliza: o artigo não sai junto da baliza (a cauda ficaria com um «a» solto)', r"(?:(?:a|as|da|das|na|nas|pela|uma|essa|esta|nossa|minha|de|do) )?baliza\w*(?= )", r"(?:(?:zz) )?baliza\w*(?= )", ('cabecas',)),
    ('p3e rev5 baliza: sem a guarda de volta, a route() sobre o resto chama a baliza de novo (a guarda só vale na 1ª entrada)', r"    if (EM_BALIZA || !has(q, ['baliza'])) return false;", r"    if (!has(q, ['baliza'])) return false;", ('rev5', 'cabecas')),
    ('p3e rev5 baliza: «fora» sai dos descritores da boia («baliza fora de posição» é a boia)', r"'deslocado', 'fora', 'deriva'", r"'deslocado', 'deriva'", ('rev5',)),
    ('p3e rev5 baliza: os descritores da boia (cor, lado, luz, estado) saem da lista', r"'sinalizacao', 'sinalizar', 'luminosa', 'luminoso', 'nautica', 'nautico', 'isolado', 'isolada', 'vermelha', 'vermelho', 'verde', 'amarela', 'amarelo', 'cor', 'cores', 'bombordo', 'boreste', 'estibordo',"
     "\n" r"    'apagada', 'apagado', 'apagou', 'torta', 'torto', 'deslocada', 'deslocado', 'fora', 'deriva', 'derivando'", r"'zzsinal'", ('rev5',)),
    ('p3e rev5 baliza: «baliza fora de posição» é a posição do barco (a rota da posição vê a baliza)', r"function posicaoPergunta(q) { return !has(q, ['baliza']) && (", r"function posicaoPergunta(q) { return (", ('rev5',)),
    # a cabeça de emergência SEM o guia: a instrução de segurança da família, nunca o fallback com o quadro
    ('p3e rev5 sem guia: a cabeça de emergência no fallback leva o quadro (SOG, proa, hora)', r"    if (key === 'fallback' && cabecaEmerg(pad(q))) { var fam", r"    if (false) { var fam", ('rev5', 'cabecas')),
    ('p3e rev5 sem guia: a cabeça sem guia é sempre o SOS', r"key = fam === 'baliza' ? 'epirb' : fam ? 'canal16' : 'sos';", r"key = 'sos';", ('rev5', 'cabecas')),
    ('p3e rev5 sem guia: a baliza do EPIRB sem guia é o roteiro do canal 16', r"key = fam === 'baliza' ? 'epirb' : fam ? 'canal16' : 'sos';", r"key = fam ? 'canal16' : 'sos';", ('rev5', 'cabecas')),
    ('p3e rev5 sem guia: o botão DISTRESS sem guia é o procedimento do EPIRB', r"key = fam === 'baliza' ? 'epirb' : fam ? 'canal16' : 'sos';", r"key = fam ? 'epirb' : 'sos';", ('rev5', 'cabecas')),
    # a gravação em capitao.pecas.v1 parte do que está guardado
    ('p3e rev5 pecas: o −1 USADA grava o estado filtrado (a linha de dq em texto e as chaves desconhecidas somem)', r"    movs.push(m); write(K_PECAS, cru);", r"    movs.push(m); write(K_PECAS, { novas: pecasEstado().novas, movs: pecasEstado().movs.concat([m]) });", ('rev5',)),
    ('p3e rev5 pecas: o + PEÇA grava o estado filtrado', r"    novas.push(item); write(K_PECAS, est);", r"    novas.push(item); write(K_PECAS, { novas: pecasEstado().novas.concat([item]), movs: pecasEstado().movs });", ('rev5',)),
    ('p3e rev5 pecas: o JSON ruim guardado vira vazio na gravação (e se perde)', r"    try { v = JSON.parse(s); } catch (e) { return { antes: s }; }", r"    try { v = JSON.parse(s); } catch (e) { return {}; }", ('rev5',)),
    ('p3e rev5 pecas: o valor guardado que não é objeto vira vazio na gravação (e se perde)', r"typeof v === 'object' && !Array.isArray(v) ? v : { antes: v };", r"typeof v === 'object' && !Array.isArray(v) ? v : {};", ('rev5',)),
    ('p3e rev5 pecas: o campo que não é lista é pisado', r"{ while (cru[k] !== undefined) k += '_'; cru[k] = cru[campo]; }", r"{ }", ('rev5',)),
    ('p3e rev5 pecas: o `<campo>Antes` que já existia é pisado', r"{ while (cru[k] !== undefined) k += '_'; cru[k] = cru[campo]; }", r"{ cru[k] = cru[campo]; }", ('rev5',)),
    ('p3e rev5 pecas: o iso do movimento novo ignora as linhas cruas', r"} while (movs.some(function (x) { return x && x.iso === iso; }));", r"} while (pecasEstado().movs.some(function (x) { return x.iso === iso; }));", ('pecas', 'rev5')),
    # «tem <peça>?», «onde está <peça>?» e o relato com o pedido de outra
    ('p3e rev5 pecas: «tem correia do alternador?» (o verbo sem sujeito) não é estoque', r"      || (PECAS_TEM_ABRE.test(semVocativo(q)) && !PECAS_LUGAR.test(q) && objetoPeca(q, PECAS_VERBOS_TEM))" "\n", r"", ('rev5',)),
    ('p3e rev5 pecas: «o motor tem filtro?» (com sujeito) é estoque', r"var PECAS_TEM_ABRE = /^ (?:(?:ainda|ja|sera que|a gente|voces?|vc|entao|e|mas|por acaso|aqui|ai|nos) )*(?:temos|tenho|tem|ha) /;", r"var PECAS_TEM_ABRE = /^ (?:.* )?(?:temos|tenho|tem|ha) /;", ('rev5',)),
    ('p3e rev5 pecas: «tem anodo no casco?» (a peça instalada, com o lugar) é estoque', r" && !PECAS_LUGAR.test(q) && objetoPeca(q, PECAS_VERBOS_TEM))", r" && objetoPeca(q, PECAS_VERBOS_TEM))", ('rev5',)),
    ('p3e rev5 pecas: «tem fusível reserva?» («reserva» depois da peça) não é estoque', r"      || (/ (?:temos|tenho|tem|ha) /.test(q) && PECAS_RESERVA.test(q) && objetoPeca(q, PECAS_VERBOS_TEM))" "\n", r"", ('rev5',)),
    ('p3e rev5 pecas: «onde está o rotor do gerador?» / «cadê o rotor?» não é estoque', r"      || (/ (?:onde|cade) /.test(q) && objetoPeca(q, PECAS_VERBOS_ONDE))", r"", ('rev5',)),
    ('p3e rev5 pecas: o verbo de «onde» não inclui «cadê»', r"var PECAS_VERBOS_ONDE = ['esta', 'estao', 'fica', 'ficam', 'cade', 'guardamos',", r"var PECAS_VERBOS_ONDE = ['esta', 'estao', 'fica', 'ficam', 'guardamos',", ('rev5',)),
    ('p3e rev5 pecas: «o fusível queimou, tem outro?» não é estoque (o relato vence)', r"    if (PECAS_RELATO_OUTRA.test(q) && sujeitoPeca(q) && !has(q, PECAS_CONTATO)) return true;" "\n", r"", ('rev5',)),
    ('p3e rev5 pecas: «o motor queimou, tem outro?» é estoque (o sujeito não é a peça)', r"if (PECAS_RELATO_OUTRA.test(q) && sujeitoPeca(q) &&", r"if (PECAS_RELATO_OUTRA.test(q) &&", ('rev5',)),
    ('p3e rev5 pecas: «apit» (o apito) dentro de «capitão» tira do estoque a pergunta com o vocativo', r"'nao parte', ' apit', 'fumac',", r"'nao parte', 'apit', 'fumac',", ('rev5',)),
    ('p3e rev5 pecas: «onde está <peça>?» não abre com «Onde ficam: » (a peça do nome)', r"(onde && nm.lista.length <= 3 ? ondeFicam(nm.lista) : 'Estoque de peças: ' + corpo(nm.lista))", r"('Estoque de peças: ' + corpo(nm.lista))", ('rev5',)),
    ('p3e rev5 pecas: mais de 3 peças também abrem com «Onde ficam: »', r"(onde && nm.lista.length <= 3 ? ondeFicam(nm.lista)", r"(onde ? ondeFicam(nm.lista)", ('rev5',)),
    ('p3e rev5 pecas: «onde está <peça>?» da tarefa da agenda não abre com «Onde ficam: »', r"(onde && lig.length <= 3 ? ondeFicam(lig) : 'Peças para '", r"(false ? ondeFicam(lig) : 'Peças para '", ('rev5',)),
    ('p3e rev5 pecas: a peça sem local cadastrado some da 1ª linha («Onde ficam»)', r"(x.local || 'sem local cadastrado')", r"x.local", ('rev5',)),
    # a pressão de óleo estável abaixo do mínimo
    ('p3e rev5 óleo: a pressão estável abaixo do mínimo normal não pede atenção', r"nivel: queda >= 0.2 || abaixo ? 'atencao' : 'ok'", r"nivel: queda >= 0.2 ? 'atencao' : 'ok'", ('rev5', 'preditiva')),
    ('p3e rev5 óleo: o texto abaixo do mínimo normal diz «estável» sem dizer que está abaixo', r"      texto: abaixo ? 'Pressão de óleo em cruzeiro abaixo do mínimo normal de '", r"      texto: false ? 'Pressão de óleo em cruzeiro abaixo do mínimo normal de '", ('rev5', 'preditiva')),
    ('p3e rev5 óleo: o texto abaixo do mínimo normal diz «estável» mesmo quando está caindo', r"BB ' + nb(vb, 1) + ' bar · BE ' + nb(ve, 1) + ' bar, ' + (queda >= 0.2 ? 'caindo' : 'estável') + ' há '", r"BB ' + nb(vb, 1) + ' bar · BE ' + nb(ve, 1) + ' bar, ' + ('estável') + ' há '", ('rev5',)),
    ('p3e rev5 óleo: só o maior dos dois motores conta para o mínimo (o outro, abaixo, passa)', r"abaixo = mn !== null && Math.min(vb, ve) < mn;", r"abaixo = mn !== null && Math.max(vb, ve) < mn;", ('rev5',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_3E_REV5



# ——————————————— Fase 3, P3F: registro, propostas A CONFIRMAR, relato, registro pelo chat, contexto e foto com texto ———————————————
# (PARIDADE F14, F16, F17, F18, F36; CONTRATO §1.25; PROMPT §2.9; CLAUDE.md 14.) Só o cérebro: as telas (os botões CONFIRMAR, ✎, RECUSAR, DESFAZER, o selo «apresentação», a
# lista A CONFIRMAR) são da Fase 4. O registro só cresce: confirmar = 1 linha, recusar = 0, desfazer = uma linha de anulação (a confirmada fica guardada e sai da leitura).

# —— o carimbo `sim` e a linha de ação ——
JS_P3F_SIM = """() => { const B = window.CapitaoBrain, o = {}; localStorage.clear();
  const d1 = B.addDiario({ t: 'nota normal', src: 'chat · voz/texto' }), d2 = B.addDiario({ t: 'MAYDAY teste', src: 'web · SOS · MAYDAY' }), d3 = B.addDiario({ t: 'MOB teste', src: 'app · SOS · MOB' }),
        d4 = B.addDiario({ t: 'linha com o carimbo dado', src: 'app · texto', sim: true }), d5 = B.addDiario({ t: 'linha com sim false', src: 'app · texto', sim: false });
  o.d = [d1.sim === true, 'sim' in d2, 'sim' in d3, d4.sim === true, d5.sim === false]; o.sosKeys = Object.keys(d2).sort();
  B.markExec('porao-teste'); o.exec = B.loadExec()['porao-teste'];
  B.addDoc({ n: 'doc.pdf', s: '1 KB', dd: '03/11', st: 'A CONFERIR', cat: 'Documentos', fonte: 'foto' }); B.addAbast({ n: 'nf.jpg', d: '03/11', st: 'A CONFIRMAR', fonte: 'foto' });
  o.doc = B.loadDocs()[0]; o.abast = B.loadAbast()[0];
  B.addDoc({ n: 'ja.pdf', sim: false }); o.docJa = B.loadDocs()[0].sim;   // o que a tela já mandou fica como está
  return o; }"""
# 3 linhas no MESMO milissegundo (o relógio parado): cada uma com o seu iso, e a anulação acha a certa
JS_P3F_ISO = """() => { const B = window.CapitaoBrain; localStorage.clear();
  const a = B.addDiario({ t: 'A' }), b = B.addDiario({ t: 'B' }), c = B.addDiario({ t: 'C' }), an = B.addDiario({ t: 'anula B', acao: 'anula', alvo: b.iso });
  return { isos: [a.iso, b.iso, c.iso, an.iso], ordem: B.loadDiario().map((e) => e.t), vigente: B.answer('diário de bordo', { platform: 'app', commit: false }).text, anBy: an && an.alvo === b.iso }; }"""
JS_P3F_ACAO = """() => { const B = window.CapitaoBrain, D = window.CapitaoDados, o = {}; localStorage.clear();
  const linha = B.addDiario({ t: 'uma linha do aparelho' }), pend = B.addDiario({ t: 'pendência do aparelho', pend: true }), n = () => B.loadDiario().length, n0 = n();
  const tenta = (e) => { const antes = n(), r = B.addDiario(e); return [r === null, n() - antes]; };
  o.semAlvo = tenta({ t: 'x', acao: 'anula' }); o.alvoNum = tenta({ t: 'x', acao: 'anula', alvo: 5 }); o.alvoInexistente = tenta({ t: 'x', acao: 'anula', alvo: '2020-01-01T00:00:00.000Z' });
  o.acaoDesconhecida = tenta({ t: 'x', acao: 'apaga', alvo: linha.iso }); o.acaoDesconhecidaPend = tenta({ t: 'x', acao: 'apaga', alvo: pend.iso }); o.acaoVazia = tenta({ t: 'x', acao: '', alvo: linha.iso });
  o.geradaPorIso = tenta({ t: 'x', acao: 'anula', alvo: D.diario[1].iso }); o.corrigeVazio = tenta({ t: '  ', acao: 'corrige', alvo: linha.iso });
  o.resolveNaoPend = tenta({ t: 'x', acao: 'resolve', alvo: D.diario.filter((x) => !x.pend)[0].id }); o.resolveLinhaSemPend = tenta({ t: 'x', acao: 'resolve', alvo: linha.iso });
  o.resolveIdFalso = tenta({ t: 'x', acao: 'reabre', alvo: 'd99' });
  o.pendIds = D.diario.filter((x) => x.pend).map((x) => x.id);
  const ok = (e) => { const antes = n(), r = B.addDiario(e); return [r !== null && r.acao === e.acao && r.alvo === e.alvo, n() - antes]; };
  o.anula = ok({ t: 'anula', acao: 'anula', alvo: linha.iso }); o.corrige = ok({ t: 'texto novo', acao: 'corrige', alvo: linha.iso });
  o.resolveGerada = D.diario.filter((x) => x.pend).map((x) => ok({ t: 'ok', acao: 'resolve', alvo: x.id })); o.reabreGerada = ok({ t: 'volta', acao: 'reabre', alvo: D.diario.filter((x) => x.pend)[0].id });
  o.resolveDoAparelho = ok({ t: 'ok', acao: 'resolve', alvo: pend.iso });
  const ac = B.loadDiario()[0]; o.anulaDeAcao = tenta({ t: 'x', acao: 'anula', alvo: ac.iso });   // uma linha de ação não é alvo de outra
  o.total = n() - n0; return o; }"""
JS_P3F_VIGENTE = """() => { const B = window.CapitaoBrain; localStorage.clear(); const op = { platform: 'app', commit: false };
  const a = B.addDiario({ t: 'LINHAAAA a ser anulada' }), c = B.addDiario({ t: 'LINHACCCC original' }), k = B.addDiario({ t: 'LINHAKKKK sempre vigente' });
  const antes = B.answer('diário de bordo', op).text;
  B.addDiario({ t: 'anulada', acao: 'anula', alvo: a.iso }); B.addDiario({ t: 'LINHACCCC corrigida', acao: 'corrige', alvo: c.iso }); B.addDiario({ t: 'LINHACCCC corrigida de novo', acao: 'corrige', alvo: c.iso });
  const depois = B.answer('diário de bordo', op).text, ficha = B.ficha('app');
  return { antes, depois, ficha, cru: B.loadDiario().map((e) => e.t), anomalias: B.answer('pendências abertas', op).text }; }"""

# —— as propostas A CONFIRMAR (F14) ——
JS_P3F_TICKET = """() => { const B = window.CapitaoBrain, o = {}; localStorage.clear(); const n = () => B.loadDiario().length, n0 = n();
  const t1 = B.addTicket({ k: 'diario', origem: 'relato', texto: '  Trocamos   o filtro de ar do gerador hoje de manhã  ', prop: { sys: 'Manutenção' } });
  o.t1 = t1; o.invalidos = [B.addTicket(null), B.addTicket({ k: 'diario' }), B.addTicket({ k: 'diario', texto: '   ' }), B.addTicket({ k: 'xyz', texto: 'a' }), B.addTicket({ k: 'exec', texto: 'a' })];
  o.mesmoId = B.addTicket({ id: 'tabc12', k: 'diario', texto: 'primeiro' }).texto + '|' + B.addTicket({ id: 'tabc12', k: 'diario', texto: 'segundo' }).texto + '|' + B.loadTickets().filter((t) => t.id === 'tabc12').length;
  o.idRuim = B.addTicket({ id: 'x/../y', k: 'diario', texto: 'id sem o t' }).id;
  o.abertos0 = B.ticketsAbertos().length; o.linhas0 = n() - n0;                       // propor não grava nada
  o.edit = B.editaTicket(t1.id, { texto: 'Trocamos o filtro de ar do gerador hoje às 09:30' }); o.editVazio = B.editaTicket(t1.id, { texto: '  ' }); o.editFalta = B.editaTicket('tnaoexiste', { texto: 'x' });
  const r = B.aceitaTicket(t1.id); o.r = r; o.linhas1 = n() - n0; o.linha = B.loadDiario()[0]; o.ticket1 = B.loadTickets().filter((t) => t.id === t1.id)[0];
  o.ja = B.aceitaTicket(t1.id); o.linhas2 = n() - n0; o.editAceito = B.editaTicket(t1.id, { texto: 'depois de confirmada' }); o.recusaAceito = B.recusaTicket(t1.id);
  o.nulo = [B.aceitaTicket('tnaoexiste'), B.aceitaTicket(null), B.recusaTicket('tnaoexiste'), B.desfazTicket('tnaoexiste'), B.desfazTicket(null)];
  const d = B.desfazTicket(r); o.d = d; o.linhas3 = n() - n0; o.vig = B.answer('diário de bordo', { platform: 'app', commit: false }).text; o.abertos1 = B.ticketsAbertos().map((t) => t.id).indexOf(t1.id) >= 0;
  o.dDeNovo = B.desfazTicket(r);                                                     // a proposta voltou a aberta: não há o que desfazer
  const r2 = B.aceitaTicket(t1.id); o.r2 = r2 && [r2.ja, r2.linha.iso !== r.linha.iso]; o.linhas4 = n() - n0;
  const t2 = B.addTicket({ k: 'diario', origem: 'relato', texto: 'A bomba de água doce começou a fazer barulho ontem à noite' });
  o.rec = B.recusaTicket(t2.id); o.recGuardada = B.loadTickets().filter((t) => t.id === t2.id)[0]; o.linhas5 = n() - n0; o.aceitaRecusado = B.aceitaTicket(t2.id); o.editRecusado = B.editaTicket(t2.id, { texto: 'x' }); o.recDeNovo = B.recusaTicket(t2.id); o.linhas6 = n() - n0;
  o.abertos2 = B.ticketsAbertos().length; o.estados = B.loadTickets().map((t) => t.estado).sort();
  o.tela = B.ticketTela(t2); o.telaNull = B.ticketTela(null);
  const t3 = B.addTicket({ k: 'diario', origem: 'ia', texto: 'Confirmada no chat', prop: { sys: 'Equipamentos' } }), r3 = B.aceitaTicket(t3.id, { chat: true });
  o.janelaChat = r3.desfazAte - Date.now(); o.janelaTela = (() => { const t4 = B.addTicket({ k: 'diario', texto: 'na tela' }); return B.aceitaTicket(t4.id).desfazAte - Date.now(); })();
  // a janela do desfazer: depois dela não desfaz e não escreve nada
  const t5 = B.addTicket({ k: 'diario', texto: 'fora da janela' }), r5 = B.aceitaTicket(t5.id), cru = JSON.parse(localStorage.getItem('capitao.tickets.v1')); cru.filter((t) => t.id === t5.id)[0].dec.ate = Date.now() - 1; localStorage.setItem('capitao.tickets.v1', JSON.stringify(cru));
  const antes = n(); o.foraJanela = B.desfazTicket(r5); o.foraJanelaLinhas = n() - antes; o.foraJanelaEstado = B.loadTickets().filter((t) => t.id === t5.id)[0].estado;
  o.cruTipos = JSON.parse(localStorage.getItem('capitao.tickets.v1')).every((t) => typeof t.id === 'string' && typeof t.iso === 'string' && t.who);
  return o; }"""
# a gravação parte do que está guardado: linha de outra forma fica; o valor que não é lista é guardado ao lado
JS_P3F_TICKET_CRU = """() => { const B = window.CapitaoBrain, o = {}; localStorage.clear();
  localStorage.setItem('capitao.tickets.v1', JSON.stringify([{ id: 'tfuturo1', k: 'novoTipo', texto: 'de uma versão futura', estado: 'aberto' }, 'lixo', { sem: 'id' }, null]));
  const t = B.addTicket({ k: 'diario', texto: 'Uma proposta nova' }); B.aceitaTicket(t.id);
  o.cru = JSON.parse(localStorage.getItem('capitao.tickets.v1')); o.lista = B.loadTickets().map((x) => x.id);
  localStorage.clear(); localStorage.setItem('capitao.tickets.v1', '{"nao":"e lista"}');
  const u = B.addTicket({ k: 'diario', texto: 'Outra proposta' }); o.antes = localStorage.getItem('capitao.tickets.v1.antes'); o.depois = JSON.parse(localStorage.getItem('capitao.tickets.v1')).length; o.u = !!u;
  localStorage.clear(); localStorage.setItem('capitao.tickets.v1', 'isto nem é JSON'); B.addTicket({ k: 'diario', texto: 'Mais uma' }); o.antes2 = localStorage.getItem('capitao.tickets.v1.antes');
  return o; }"""
# o alarme do replay só vira proposta num gesto, uma por alarme por dia de bordo; o replay nunca cria proposta nem grava no diário
JS_P3F_ALARME = """([dias]) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, A = window.CapitaoAlertas, o = {}; localStorage.clear();
  const n = () => B.loadDiario().length, n0 = n(), tk = () => B.loadTickets();
  R.fixar('105'); const ativo = A.porId('arref_be'); o.ativo = !!ativo;
  o.semGesto = [B.propoeAlarme('arref_be'), B.propoeAlarme('arref_be', false), B.propoeAlarme('arref_be', 'sim'), B.propoeAlarme('arref_be', 1)]; o.nSem = tk().length;
  o.ruim = [B.propoeAlarme('', true), B.propoeAlarme(null, true), B.propoeAlarme('../x', true), B.propoeAlarme('arref_bb', true), B.propoeAlarme('nao_existe', true)]; o.nRuim = tk().length;
  const a = B.propoeAlarme('arref_be', true), b = B.propoeAlarme('arref_be', true); o.a = a; o.mesma = a && b && a.id === b.id; o.n1 = tk().length; o.linhas = n() - n0;
  const dia1 = a.id; B.recusaTicket(a.id); const c = B.propoeAlarme('arref_be', true); o.aposRecusa = c && c.id === dia1 && c.estado === 'recusado'; o.n2 = tk().length;
  R.fixar('60'); o.foraDaJanela = B.propoeAlarme('arref_be', true); o.n3 = tk().length;
  R.fixar('105@576'); const d = B.propoeAlarme('arref_be', true); o.diaSeguinte = d && d.id !== dia1; o.idsDia = [dia1, d && d.id]; o.n4 = tk().length;
  const ac = B.aceitaTicket(d.id); o.linhaAlarme = ac && ac.linha; o.linhas2 = n() - n0;
  R.fixar('105'); o.texto = a.texto; o.passos = ativo && A.porId('arref_be').texto;
  return o; }"""
JS_P3F_REPLAY_SOZINHO = """() => new Promise((res) => { const B = window.CapitaoBrain, R = window.CapitaoReplay, o = {}; localStorage.clear(); R.fixar(null);
  const n0 = B.loadDiario().length, ev = []; window.addEventListener('capitao-alerta', (e) => ev.push(e.detail && e.detail.fase));
  window.dispatchEvent(new CustomEvent('capitao-alerta', { detail: { fase: 'inicio', alarme: { id: 'arref_be', nivel: 'aviso' } } }));
  window.dispatchEvent(new CustomEvent('capitao-alerta', { detail: { fase: 'nivel', alarme: { id: 'arref_be', nivel: 'critico' } } }));
  R.fixar('99'); R.fixar('105'); R.fixar(null);
  setTimeout(() => { o.ev = ev; o.tickets = localStorage.getItem('capitao.tickets.v1'); o.linhas = B.loadDiario().length - n0; o.chaves = Object.keys(localStorage).filter((k) => /tickets|diario/.test(k)); res(o); }, 2600); })"""


def grupo_p3f_registro(b, muta, ped):
    # —— o carimbo sim, as linhas de ação e a visão vigente ——
    pg = pagina(b, muta=muta, relogio_ms=1793653799900)
    try:
        x = pg.evaluate(JS_P3F_SIM)
        ped('p3f sim (simulação): addDiario, markExec, addDoc e addAbast gravam sim: true (a linha que já traz o carimbo — sim: true ou sim: false — e o documento com sim: false ficam como estão)',
            x['d'][0] is True and x['d'][3] is True and x['d'][4] is True and x['exec'].get('sim') is True and x['doc'].get('sim') is True and x['abast'].get('sim') is True and x['docJa'] is False, x)
        ped('p3f sim (simulação): a linha do SOS (src web · SOS / app · SOS) nunca leva sim, mesmo numa tela que não é a do SOS', x['d'][1] is False and x['d'][2] is False and x['sosKeys'] == ['d', 'iso', 'src', 'sys', 't', 'tone', 'who'], (x['d'], x['sosKeys']))
        y = pg.evaluate(JS_P3F_ISO)
        ped('p3f iso: três linhas no mesmo milissegundo têm iso diferentes, em ordem, e a anulação acha a linha certa (B), que sai da leitura',
            len(set(y['isos'])) == 4 and y['isos'] == sorted(y['isos']) and y['anBy'] and y['ordem'] == ['anula B', 'C', 'B', 'A'] and '— B (app)' not in y['vigente'] and '— A (app)' in y['vigente'] and '— C (app)' in y['vigente'], y)
        z = pg.evaluate(JS_P3F_ACAO)
        recusas = ('semAlvo', 'alvoNum', 'alvoInexistente', 'acaoDesconhecida', 'acaoDesconhecidaPend', 'acaoVazia', 'geradaPorIso', 'corrigeVazio', 'resolveNaoPend', 'resolveLinhaSemPend', 'resolveIdFalso', 'anulaDeAcao')
        ped('p3f acao: addDiario recusa (devolve null e não grava) a ação sem alvo, com alvo que não é texto, que não existe, de linha gerada (só o aparelho pelo iso), de linha de ação, com texto vazio na correção, com ação fora das quatro e a pendência que não é pendência',
            all(z[k] == [True, 0] for k in recusas), {k: z[k] for k in recusas if z[k] != [True, 0]})
        ped('p3f acao: grava (1 linha cada) a anulação e a correção pelo iso, o resolve e o reabre pelo id da pendência gerada (as 3 do arquivo) e pelo iso de uma linha do aparelho com pend',
            z['anula'] == [True, 1] and z['corrige'] == [True, 1] and len(z['pendIds']) == 3 and all(r == [True, 1] for r in z['resolveGerada']) and z['reabreGerada'] == [True, 1] and z['resolveDoAparelho'] == [True, 1] and z['total'] == 7, z)
        v = pg.evaluate(JS_P3F_VIGENTE)
        def quantos(t):
            m = re.match(r'Diário de bordo: (\d+) registros', t)
            return int(m.group(1)) if m else -1
        ped('p3f vigente: a linha anulada sai da leitura (o diário de bordo, a ficha), a corrigida mostra o último texto, a linha de ação não é registro, e nada some do guardado (6 linhas)',
            'LINHAAAA' in v['antes'] and 'LINHAAAA' not in v['depois'] and 'LINHAAAA' not in v['ficha'] and 'LINHACCCC corrigida de novo' in v['depois'] and 'LINHACCCC original' not in v['depois'] and 'LINHACCCC original' not in v['ficha']
            and 'LINHAKKKK' in v['depois'] and quantos(v['depois']) == quantos(v['antes']) - 1 and len(v['cru']) == 6 and 'anulada' not in v['depois'], (quantos(v['antes']), quantos(v['depois']), v['cru']))
    finally:
        pg.ctx.close()
    # —— sem a simulação ——
    pg = pagina(b, muta=muta, extra=SEM_SIMULACAO)
    try:
        x = pg.evaluate(JS_P3F_SIM)
        ped('p3f sim (simulacao false): nenhum registro novo leva sim (linha, execução, documento nem abastecimento), e o carimbo que a tela mandou (sim: true) fica',
            x['d'][0] is False and x['d'][3] is True and 'sim' not in x['exec'] and 'sim' not in x['doc'] and 'sim' not in x['abast'], x)
    finally:
        pg.ctx.close()
    # —— o SOS: sem sim, sem leitura da flag ——
    pg = pagina(b, muta=muta, scripts=('capitao-dados.js', 'capitao-brain.js'), caminho='SOS-cerebro.html', fixo=None, extra=GETTERS_SOS)
    try:
        x = pg.evaluate(JS_P3F_SIM)
        lidas = pg.evaluate("() => window.__lidas")
        ped('p3f sim (SOS): no SOS nada leva sim (linha, execução, documento nem abastecimento) e a flag simulacao nunca é lida', x['d'][0] is False and 'sim' not in x['exec'] and 'sim' not in x['doc'] and 'sim' not in x['abast'] and lidas.get('simulacao') == 0, (x['d'], lidas))
        t = pg.evaluate("() => { const B = window.CapitaoBrain; localStorage.clear(); return [B.addTicket({ k: 'diario', texto: 'uma proposta' }), B.propoeAlarme('arref_be', true), localStorage.getItem('capitao.tickets.v1')]; }")
        ped('p3f tickets (SOS): o SOS não propõe nada (nenhum ticket, nenhuma chave de tickets)', t == [None, None, None], t)
    finally:
        pg.ctx.close()


def grupo_p3f_tickets(b, muta, ped):
    pg = pagina(b, muta=muta, relogio_ms=1793653799900)
    try:
        o = pg.evaluate(JS_P3F_TICKET)
        t1, r, d = o['t1'], o['r'], o['d']
        ped('p3f tickets: a proposta nasce aberta, com o texto limpo, quem, quando, a origem e o carimbo sim; propor não grava linha nenhuma; texto vazio, tipo desconhecido (exec ainda não existe), null e o id repetido não criam outra',
            t1['estado'] == 'aberto' and t1['k'] == 'diario' and t1['origem'] == 'relato' and t1['texto'] == 'Trocamos o filtro de ar do gerador hoje de manhã' and t1['sim'] is True and t1['who'] and t1['iso'] and re.match(r't[A-Za-z0-9_-]{2,60}$', t1['id'])
            and all(x is None for x in o['invalidos']) and o['mesmoId'] == 'primeiro|primeiro|1' and re.match(r't[A-Za-z0-9_-]+$', o['idRuim']) and o['idRuim'] != 'x/../y' and o['linhas0'] == 0, o)
        ped('p3f tickets: ✎ muda só o texto da proposta aberta (vazio e inexistente devolvem null)', o['edit']['texto'] == 'Trocamos o filtro de ar do gerador hoje às 09:30' and o['editVazio'] is None and o['editFalta'] is None, (o['edit'], o['editVazio']))
        ped('p3f tickets: CONFIRMAR grava 1 linha (o texto editado, sys da proposta, quem, de onde veio, com sim) e guarda a decisão e o que criou; confirmar de novo devolve ja e não grava outra',
            o['linhas1'] == 1 and o['linha']['t'] == 'Trocamos o filtro de ar do gerador hoje às 09:30' and o['linha']['sys'] == 'Manutenção' and o['linha']['sim'] is True and o['linha']['who'] and o['linha']['src'] == 'app · proposta confirmada (relato)'
            and o['ticket1']['estado'] == 'aceito' and o['ticket1']['res'] == {'tipo': 'diario', 'id': o['linha']['iso']} and o['ticket1']['dec']['quem'] and r['res']['id'] == o['linha']['iso']
            and o['ja']['ja'] is True and o['linhas2'] == 1, o)
        ped('p3f tickets: a proposta confirmada não muda (✎) nem se recusa; id que não existe, null: tudo null', o['editAceito'] is None and o['recusaAceito'] is None and all(x is None for x in o['nulo']), (o['editAceito'], o['recusaAceito'], o['nulo']))
        ped('p3f tickets: DESFAZER (na janela) escreve uma linha de anulação (a confirmada fica guardada, sai da leitura), a proposta volta a aberta; desfazer de novo não faz nada; confirmar de novo escreve uma linha nova',
            d and d['estado'] == 'aberto' and d['anulada']['acao'] == 'anula' and d['anulada']['alvo'] == r['linha']['iso'] and o['linhas3'] == 2 and o['abertos1'] is True and o['dDeNovo'] is None
            and 'Trocamos o filtro de ar' not in o['vig'] and o['r2'] == [None, True] and o['linhas4'] == 3, o)
        ped('p3f tickets: RECUSAR grava 0 linhas, a recusada não ressuscita (confirmar e ✎ devolvem null) nem se recusa duas vezes; as abertas e os estados batem', o['rec']['estado'] == 'recusado' and o['recGuardada']['estado'] == 'recusado' and o['recGuardada']['dec']['quem'] and o['recGuardada']['dec']['iso'] and 'res' not in o['recGuardada'] and o['linhas5'] == 3 and o['aceitaRecusado'] is None and o['editRecusado'] is None and o['recDeNovo'] is None
            and o['linhas6'] == 3 and o['abertos0'] == 3 and o['abertos2'] == 2 and o['estados'] == ['aberto', 'aberto', 'aceito', 'recusado'], o)
        ped('p3f tickets: o desfazer vale 10 s na tela e 10 min vindo do chat (opts.chat)', 9000 <= o['janelaTela'] <= 10000 and 599000 <= o['janelaChat'] <= 600000, (o['janelaTela'], o['janelaChat']))
        ped('p3f tickets: fora da janela o desfazer devolve null, não escreve a anulação e a proposta continua aceita', o['foraJanela'] is None and o['foraJanelaLinhas'] == 0 and o['foraJanelaEstado'] == 'aceito', (o['foraJanela'], o['foraJanelaLinhas'], o['foraJanelaEstado']))
        ped('p3f tickets: ticketTela traz o texto que o CONFIRMAR grava, a origem em rótulo e o selo «apresentação» só com simulacao false (aqui não); sem ticket, valor seguro', o['tela']['texto'].startswith('A bomba de água doce') and o['tela']['origem'] == 'Relato' and o['tela']['apresentacao'] is False and o['tela']['longo'] is False and o['telaNull']['texto'] == '', (o['tela'], o['telaNull']))
        c = pg.evaluate(JS_P3F_TICKET_CRU)
        ped('p3f tickets: a gravação parte do que está guardado (a proposta de uma versão futura, o lixo e o objeto sem id ficam; só a nossa entra e a lista lida mostra só as que a versão entende)',
            len(c['cru']) == 5 and c['cru'][0]['estado'] == 'aceito' and c['cru'][1:] == [{'id': 'tfuturo1', 'k': 'novoTipo', 'texto': 'de uma versão futura', 'estado': 'aberto'}, 'lixo', {'sem': 'id'}, None] and len(c['lista']) == 1, c)
        ped('p3f tickets: o valor guardado que não é lista (objeto, texto sem JSON) é copiado para capitao.tickets.v1.antes antes de ser trocado (nada se perde)', c['antes'] == '{"nao":"e lista"}' and c['depois'] == 1 and c['u'] and c['antes2'] == 'isto nem é JSON', c)
    finally:
        pg.ctx.close()
    # —— o alarme do replay: só num gesto, um por dia ——
    pg = pagina(b, muta=muta, fixo='105')
    try:
        x = pg.evaluate(JS_P3F_ALARME, [None])
        ped('p3f alarme: sem gesto (nada, false, texto, 1) nenhuma proposta; id vazio, null, fora do formato, de alarme que não está ativo ou que não existe: null', x['ativo'] and all(v is None for v in x['semGesto']) and x['nSem'] == 0 and all(v is None for v in x['ruim']) and x['nRuim'] == 0, (x['semGesto'], x['ruim']))
        ped('p3f alarme: o gesto cria UMA proposta aberta (origem telemetria, k alarme) com o texto do alarme e a hora; o gesto repetido devolve a mesma (a recusada também); nenhuma linha no diário',
            x['a'] and x['a']['estado'] == 'aberto' and x['a']['k'] == 'alarme' and x['a']['origem'] == 'telemetria' and x['a']['texto'].startswith('AVISO: Temperatura do motor BE: 89,6 °C (acima de 88 °C) desde ') and x['a']['alvo'] == {'tipo': 'alarme', 'id': 'arref_be'} and x['a']['sim'] is True
            and x['mesma'] and x['n1'] == 1 and x['linhas'] == 0 and x['aposRecusa'] and x['n2'] == 1, x)
        ped('p3f alarme: fora da janela do alarme (12:01:00) nada; no dia seguinte (mesma volta, 576 voltas depois) é outra proposta; confirmar grava a linha do alarme (sys Motores, tom de aviso) e só ela',
            x['foraDaJanela'] is None and x['n3'] == 1 and x['diaSeguinte'] and x['n4'] == 2 and x['idsDia'][0] != x['idsDia'][1] and x['linhaAlarme']['sys'] == 'Motores' and x['linhaAlarme']['t'].startswith('AVISO: Temperatura do motor BE') and 'warn' in x['linhaAlarme']['tone'] and x['linhas2'] == 1 and x['linhaAlarme']['src'] == 'app · proposta confirmada (alarme)', x)
    finally:
        pg.ctx.close()
    # sem gesto, o replay andando sozinho (e o evento de alerta) nunca cria proposta nem grava no diário
    pg = pagina(b, muta=muta, fixo=None)
    try:
        y = pg.evaluate(JS_P3F_REPLAY_SOZINHO)
        ped('p3f alarme: o replay andando, o evento capitao-alerta (início e mudança de nível) e as voltas pela janela do alarme não criam proposta nem linha no diário', y['tickets'] is None and y['linhas'] == 0 and 'capitao.tickets.v1' not in y['chaves'], y)
    finally:
        pg.ctx.close()
    # modo real: o alarme não vira proposta (o replay é inerte), a flag é lida na hora
    pg = pagina(b, muta=muta, fixo='105')
    try:
        r = pg.evaluate("() => { const B = window.CapitaoBrain; localStorage.clear(); window.CapitaoDados.simulacao = false; const a = B.propoeAlarme('arref_be', true), t = B.addTicket({ k: 'diario', texto: 'relato no modo real' }); return [a, t && t.sim, B.loadTickets().length]; }")
        ped('p3f alarme (simulacao false, lida na hora): o alarme não vira proposta; o relato vira, sem o carimbo sim', r == [None, None, 1], r)
    finally:
        pg.ctx.close()


GRUPOS_3A['p3f_registro'] = grupo_p3f_registro
GRUPOS_3A['p3f_tickets'] = grupo_p3f_tickets


# —— os mutantes do registro, das linhas de ação e das propostas (P3F) ——
MUTANTES_P3F = [
    ('p3f sim: addDiario sem o carimbo sim', r"    if (sim() && !linhaDoSOS(entry) && entry.sim == null) entry.sim = true;", r"", ('p3f_registro',)),
    ('p3f sim: a linha do SOS leva sim fora da página do SOS', r"if (sim() && !linhaDoSOS(entry) && entry.sim == null)", r"if (sim() && entry.sim == null)", ('p3f_registro',)),
    ('p3f sim: o carimbo ignora a flag (leva sim com simulacao false)', r"if (sim() && !linhaDoSOS(entry) && entry.sim == null)", r"if (!EM_SOS && !linhaDoSOS(entry) && entry.sim == null)", ('p3f_registro',)),
    ('p3f sim: o carimbo pisa o que a tela mandou', r"!linhaDoSOS(entry) && entry.sim == null) entry.sim = true;", r"!linhaDoSOS(entry)) entry.sim = true;", ('p3f_registro',)),
    ('p3f sim: o SOS lê a flag mesmo no SOS (sim() sem a guarda)', r"function sim() { return !EM_SOS && D.simulacao === true; }", r"function sim() { return D.simulacao === true && !EM_SOS; }", ('p3f_registro',)),
    ('p3f sim: markExec sem o carimbo', r"m[task] = Object.assign(now(), selaSim()); write(K.exec, m);", r"m[task] = now(); write(K.exec, m);", ('p3f_registro',)),
    ('p3f sim: addDoc sem o carimbo', r"list.unshift(carimba(d)); write(K.docs, list);", r"list.unshift(d); write(K.docs, list);", ('p3f_registro',)),
    ('p3f sim: addAbast sem o carimbo', r"list.unshift(carimba(a)); write(K.abast, list);", r"list.unshift(a); write(K.abast, list);", ('p3f_registro',)),
    ('p3f sim: o carimbo do documento pisa o sim: false que a tela mandou', r"x && typeof x === 'object' && x.sim == null ? Object.assign({}, x, { sim: true }) : x; }", r"x && typeof x === 'object' ? Object.assign({}, x, { sim: true }) : x; }", ('p3f_registro',)),
    ('p3f iso: duas linhas no mesmo milissegundo dividem o iso', r"while (isFinite(ms) && list.some(function (x) { return x.iso === entry.iso; })) {", r"while (false) {", ('p3f_registro',)),
    ('p3f acao: addDiario grava a ação sem validar o alvo', r"    if (e && e.acao !== undefined && !alvoValido(e, list)) return null;", r"", ('p3f_registro',)),
    ('p3f acao: qualquer texto é alvo de anulação ou correção (a linha nem precisa existir)', r"return !!linha && !linha.acao && (a === 'anula' || !!String(e.t || '').trim());", r"return true;", ('p3f_registro',)),
    ('p3f acao: a correção com texto vazio passa', r"(a === 'anula' || !!String(e.t || '').trim());", r"true;", ('p3f_registro',)),
    ('p3f acao: a linha de ação é alvo de outra ação', r"return !!linha && !linha.acao && (a === 'anula'", r"return !!linha && (a === 'anula'", ('p3f_registro',)),
    ('p3f acao: o resolve vale para linha do aparelho sem pend', r"if (linha) return linha.pend === true && !linha.acao;", r"if (linha) return !linha.acao;", ('p3f_registro',)),
    ('p3f acao: o resolve vale para qualquer linha gerada (não só a pendência)', r"return (D.diario || []).some(function (x) { return x && x.id === alvo && x.pend === true; });", r"return (D.diario || []).some(function (x) { return x && x.id === alvo; });", ('p3f_registro',)),
    ('p3f acao: ação fora das quatro passa', r"if (!ACOES[a] || typeof alvo !== 'string' || !alvo) return false;", r"if (typeof alvo !== 'string' || !alvo) return false;", ('p3f_registro',)),
    ('p3f vigente: a linha anulada continua na leitura', r"return !x.acao && !anula[x.iso]; })", r"return !x.acao; })", ('p3f_registro',)),
    ('p3f vigente: a linha de ação aparece como registro', r"return !x.acao && !anula[x.iso]; })", r"return !anula[x.iso]; })", ('p3f_registro',)),
    ('p3f vigente: a correção não aparece', r"return corr[x.iso] ? Object.assign({}, x, { t: corr[x.iso].t, corrigido: true }) : x; });", r"return x; });", ('p3f_registro',)),
    ('p3f vigente: vale a correção mais antiga', r"else if (x.acao === 'corrige' && typeof x.alvo === 'string' && !corr[x.alvo]) corr[x.alvo] = x; })", r"else if (x.acao === 'corrige' && typeof x.alvo === 'string') corr[x.alvo] = x; })", ('p3f_registro',)),
    ('p3f tickets: o id repetido duplica a proposta', r"    ja = achaTicket(cru, id); if (ja) return ja;   // o id repetido não duplica", r"", ('p3f_tickets',)),
    ('p3f tickets: a proposta sem texto é criada', r"if (typeof t.k !== 'string' || !TICKET_K[t.k] || !texto) return null;", r"if (typeof t.k !== 'string' || !TICKET_K[t.k]) return null;", ('p3f_tickets',)),
    ('p3f tickets: o tipo desconhecido é criado', r"if (typeof t.k !== 'string' || !TICKET_K[t.k] || !texto) return null;", r"if (typeof t.k !== 'string' || !texto) return null;", ('p3f_tickets',)),
    ('p3f tickets: o SOS propõe', r"    if (EM_SOS) return null;   // o SOS não propõe nada", r"", ('p3f_registro',)),
    ('p3f tickets: a proposta sem o carimbo sim', r"    if (sim()) item.sim = true;", r"", ('p3f_tickets',)),
    ('p3f tickets: o id da tela não é conferido', r"id = typeof t.id === 'string' && /^t[A-Za-z0-9_-]{2,60}$/.test(t.id) ? t.id : novoIdTicket(cru);", r"id = typeof t.id === 'string' ? t.id : novoIdTicket(cru);", ('p3f_tickets',)),
    ('p3f tickets: confirmar duas vezes grava duas linhas', r"    if (t.estado === 'aceito') return { id: id, k: t.k, ja: true, dec: t.dec || null, res: t.res || null };", r"", ('p3f_tickets',)),
    ('p3f tickets: a proposta recusada ressuscita ao confirmar', "    if (!t || t.estado === 'recusado') return null;\n    if (t.estado === 'aceito')", "    if (!t) return null;\n    if (t.estado === 'aceito')", ('p3f_tickets',)),
    ('p3f tickets: o ✎ muda a proposta confirmada', "    var cru = ticketsCru(), t = achaTicket(cru, id), tx;\n    if (!t || t.estado !== 'aberto') return null;", "    var cru = ticketsCru(), t = achaTicket(cru, id), tx;\n    if (!t) return null;", ('p3f_tickets',)),
    ('p3f tickets: o ✎ aceita o texto vazio', r"if (campos.texto != null) { tx = limpaT(campos.texto, 600); if (!tx) return null; t.texto = tx; }", r"if (campos.texto != null) { tx = limpaT(campos.texto, 600); t.texto = tx; }", ('p3f_tickets',)),
    ('p3f tickets: recusar a proposta já confirmada', "    var cru = ticketsCru(), t = achaTicket(cru, id);\n    if (!t || t.estado !== 'aberto') return null;\n    t.estado = 'recusado';", "    var cru = ticketsCru(), t = achaTicket(cru, id);\n    if (!t) return null;\n    t.estado = 'recusado';", ('p3f_tickets',)),
    ('p3f tickets: recusar grava a decisão sem quem', r"t.estado = 'recusado'; t.dec = { quem: quem(), iso: new Date().toISOString() }; write(K.tickets, cru);", r"t.estado = 'recusado'; write(K.tickets, cru);", ('p3f_tickets',)),
    ('p3f tickets: o desfazer vale para sempre', r" || Date.now() > t.dec.ate) return null;", r") return null;", ('p3f_tickets',)),
    ('p3f tickets: o desfazer escreve a correção e não a anulação', r"src: 'app · proposta desfeita', acao: 'anula', alvo: lin.iso });", r"src: 'app · proposta desfeita', acao: 'corrige', alvo: lin.iso });", ('p3f_tickets',)),
    ('p3f tickets: o desfazer não reabre a proposta', r"    t.estado = 'aberto'; delete t.dec; delete t.res; write(K.tickets, cru);", r"    write(K.tickets, cru);", ('p3f_tickets',)),
    ('p3f tickets: o desfazer apaga a linha confirmada (o registro não pode encolher)', r"    an = addDiario({ sys: lin.sys,", r"    write(K.diario, loadDiario().filter(function (x) { return x.iso !== lin.iso; })); an = addDiario({ sys: lin.sys,", ('p3f_tickets',)),
    ('p3f tickets: a janela do chat é a da tela', r"(opts && opts.chat ? TICKET_DESFAZ_CHAT : TICKET_DESFAZ)", r"TICKET_DESFAZ", ('p3f_tickets',)),
    ('p3f tickets: a janela da tela é a do chat', r"(opts && opts.chat ? TICKET_DESFAZ_CHAT : TICKET_DESFAZ)", r"TICKET_DESFAZ_CHAT", ('p3f_tickets',)),
    ('p3f tickets: a gravação perde as linhas de outra forma (parte do filtrado)', r"    cru.unshift(item); write(K.tickets, cru);", r"    cru = cru.filter(ehTicket); cru.unshift(item); write(K.tickets, cru);", ('p3f_tickets',)),
    ('p3f tickets: o valor que não é lista é pisado sem cópia', r"try { if (s && localStorage.getItem(K.tickets + '.antes') === null) localStorage.setItem(K.tickets + '.antes', s); } catch (e) {}", r"", ('p3f_tickets',)),
    ('p3f tickets: o selo «apresentação» aparece com a simulação ligada', r"apresentacao: !!(t && t.sim === true && !EM_SOS && D.simulacao === false)", r"apresentacao: !!(t && t.sim === true)", ('p3f_tickets',)),
    ('p3f alarme: a proposta sem gesto', r"if (gesto !== true || EM_SOS || !sim() ||", r"if (EM_SOS || !sim() ||", ('p3f_tickets',)),
    ('p3f alarme: o gesto vale qualquer valor verdadeiro', r"if (gesto !== true || EM_SOS", r"if (!gesto || EM_SOS", ('p3f_tickets',)),
    ('p3f alarme: a proposta de um alarme que não está ativo', "    if (!al) return null;\n    try { dia =", "    try { dia =", ('p3f_tickets',)),
    ('p3f alarme: uma proposta por alarme sem o dia (a de ontem vale hoje)', r"id: 'tal_' + id + '_' + dia, k: 'alarme'", r"id: 'tal_' + id, k: 'alarme'", ('p3f_tickets',)),
    ('p3f alarme: a proposta nova a cada gesto', r"id: 'tal_' + id + '_' + dia, k: 'alarme'", r"k: 'alarme'", ('p3f_tickets',)),
    ('p3f alarme: o dia é o do relógio e não o do instante', r"format(new Date(i.ms)).replace(/-/g, ''); } catch (e) { return null; }", r"format(new Date()).replace(/-/g, ''); } catch (e) { return null; }", ('p3f_tickets',)),
    ('p3f alarme: o alarme grava a linha no diário ao propor', r"    return addTicket({ id: 'tal_' + id", r"    addDiario({ t: al.texto, sys: 'Motores' }); return addTicket({ id: 'tal_' + id", ('p3f_tickets',)),
    ('p3f alarme: a linha do alarme com o sys errado', r"prop: { sys: al.sistema === 'motores' ? 'Motores' : 'Equipamentos'", r"prop: { sys: 'Equipamentos'", ('p3f_tickets',)),
    ('p3f alarme: a proposta do alarme sem o alvo', r"alvo: { tipo: 'alarme', id: id } });", r"});", ('p3f_tickets',)),
]
MUTANTES_3A = MUTANTES_3A + MUTANTES_P3F


def instante_3a(b):
    falhas = 0
    ruins = confere_instante(b)
    for r in ruins:
        falhas += 1
        print('FALHA instante (P3A):', r)
    print('instante (P3A): %d falhas' % falhas)
    vivos = []
    corpo = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'capitao-brain.js'), encoding='utf-8').read()
    for nome, trecho, troca, grupos in MUTANTES_3A:
        if corpo.count(trecho) != 1:   # um mutante cujo trecho saiu do cérebro não troca nada (e a rota da página falharia): é defeito do teste, não mutante acusado
            vivos.append(nome)
            print('FALHA mutante sem o trecho (uma vez) no cérebro:', nome)
            continue
        if not confere_instante(b, muta=(trecho, troca), grupos=grupos):
            vivos.append(nome)
            print('FALHA mutante do instante NÃO acusado:', nome)
    falhas += len(vivos)
    print('instante (P3A): %d mutantes, %d acusados' % (len(MUTANTES_3A), len(MUTANTES_3A) - len(vivos)))
    return falhas


if __name__ == '__main__':
    main()
