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
    ('qual o preço do dólar?', 'fallback'), ('quem ganhou o jogo ontem', 'fallback'),
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
    ('pessoa caiu da lancha', 'sos'), ('não vejo a pessoa que caiu', 'base'), ('perdemos de vista quem caiu', 'base'),
    ('sem governo', 'base'), ('barco sem governo', 'base'), ('pane no barco', 'base'),
    # as palavras de acionamento não abrem o trecho em pergunta comum: o assunto da pergunta tem de ser o do trecho
    ('o parafuso caiu', 'fallback'), ('quantas pessoas a bordo', 'fallback'), ('a pessoa da marina', 'fallback'), ('o governo federal', 'fallback'),
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
    ('tem vista para o mar?', 'fallback'), ('qual a vista do mar', 'fallback'), ('a temperatura do mar caiu', 'fallback'),
    ('pessoa ao mar', 'base'),
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
    ('qual o MMSI do barco?', 'canal16'),
    # ——— 1b, segunda revisão (achados da revisão do commit 13de688): a regex de emergência vem de LISTA POSITIVA, não de «qualquer coisa menos unidade» ———
    # (1) «bateu em um/uma/num/numa <qualquer coisa>» era SOS (a 6ª regex só excluía a unidade): leitura, pico, valor, limite, recorde e média são telemetria
    ('o consumo bateu em um valor alto', 'consumo'), ('a temperatura bateu em um pico de 90 graus', 'fallback'), ('a pressão do óleo bateu em um patamar baixo', 'oleo'),
    ('o vento bateu em um pico de 30 nós', 'clima'), ('a bateria bateu em um mínimo de 24 volts', 'eletrico'), ('o horímetro bateu em uma marca de 1200 horas', 'horimetros'),
    ('a rotação bateu em um limite', 'motores'), ('o nível do tanque bateu num valor baixo', 'tanques'), ('bateu num limite', 'fallback'),
    ('o consumo bateu num recorde', 'consumo'), ('o motor bateu num limite de horas', 'motores'), ('o gerador bateu numa média alta', 'gerador'),
    ('bateu num valor', 'fallback'), ('a pressão bateu num valor alto', 'fallback'), ('bateu num pico', 'fallback'),
    # o «bateu forte / em cheio / em mim» de quem não é o barco, e o que bate no fundo ou no banco sem ser casco nem sandbank
    ('o motor bateu forte', 'motores'), ('o preço bateu em cheio', 'fallback'), ('a previsão bateu em cheio', 'clima'), ('a vela bateu forte', 'fallback'),
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
    ('choque térmico', 'fallback'), ('o preço deu um choque', 'fallback'), ('rombo no orçamento', 'fallback'),
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
    ('baliza cardinal', 'fallback'), ('a baliza de canal', 'base'), ('o eixo estava bom quando o barco partiu', 'fallback'), ('o eixo da hélice está ok', 'fallback'),
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
]
# As chaves de emergência (§2.3 do PROMPT): nunca vão à IA na nuvem, qualquer que seja a pergunta
CHAVES_LOCAIS = ('sos', 'epirb', 'seafire', 'salvatagem', 'canal16', 'oleo')
# IA na nuvem (quando a tela chama a IA, com o aparelho ativado): SEM DADOS, trecho do guia e pergunta sobre o app — nunca
# emergência, óleo, registro no diário, resposta pronta ou só um cumprimento.
PEDE_IA = {
    'Oque você faz?': True, 'o que vc sabe fazer?': True, 'como ligar o gerador?': True, 'qual o preço do dólar?': True, 'não registre isso': True,
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
    'o parafuso caiu': True, 'quantas pessoas a bordo': True, 'a pessoa da marina': True, 'o governo federal': True,
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
PEDE_IA.update({'fazendo água potável': True, 'fazendo água na boca': True, 'o bebedouro está fazendo água': True, 'a máquina de gelo está fazendo água': True,
                'baliza cardinal': True, 'a poita tocou o fundo': True, 'a sonda tocou o fundo': True, 'o mergulhador tocou o fundo': True,
                'o eixo estava bom quando o barco partiu': True, 'o eixo da hélice está ok': True, 'entrou água na bota': True})


def main():
    falhas = 0
    with sync_playwright() as p:
        b = p.chromium.launch(channel=CANAL, headless=True)
        pg = b.new_page()
        erros = []
        pg.on('pageerror', lambda e: erros.append(str(e)))
        pg.goto(BASE + 'base-conhecimento.json')  # mesma origem, sem a porta de login
        pg.add_script_tag(url=BASE + 'capitao-dados.js')
        pg.add_script_tag(url=BASE + 'capitao-brain.js')
        pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); })")
        res = pg.evaluate("""(casos) => { const B = window.CapitaoBrain; localStorage.clear();
          return casos.map(([q, k]) => { const a = B.answer(q, { platform: 'app' }); return { q, esperado: k, key: a.key, src: a.src, text: a.text, curta: B.falaCurta(a), ia: B.pedeIA(a, q) }; }); }""", CASOS)
        diario = pg.evaluate("() => window.CapitaoBrain.loadDiario().length")
        for r in res:
            ok = r['key'] == r['esperado']
            fonte = bool(r['src']) and r['src'].startswith('Fonte')
            semdados = r['key'] != 'fallback' or 'SEM DADOS' in r['text']
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
        blocos = ['## Agora', '## Sobre o app', '## Embarcação', '## Equipamentos', '## Telemetria', '## Manutenção', '## Horímetros', '## Autonomia e consumo',
                  '## Documentos', '## Pendências', '## Diário de bordo', '## Equipe e contatos', '## Clima e maré', '## Guias de bordo', '## Emergência']
        faltam = [x for x in blocos if x not in f]
        coord = [x for x in ("26°59", "048°36", "-26.99", "-48.6") if x in f]
        voz = pg.evaluate("() => window.CapitaoBrain.falaCurta({ key: 'ia', text: 'Sou o Capitão IA.\\nRespondo sobre telemetria, manutenção e documentos, sempre com a fonte.\\n• item\\nFonte: Sobre o app' })")
        x = pg.evaluate("""() => { const B = window.CapitaoBrain, r = (q) => { const a = B.answer(q, { platform: 'app', commit: false }); return { a, f: B.ficha('app', q, a), voz: B.falaCurta(a) }; };
            const meta = r('Oque você faz?'), base = r('Quando foi a última troca de óleo do motor?'), sd = r('qual o calado do barco?'), oi = r('oi'), dg = r('diagnóstico');
            const func = r('como você funciona?'), seguro = r('o que você sabe sobre o seguro?');
            return { metaF: meta.f, baseK: base.a.key, baseF: base.f, sdF: sd.f, funcF: func.f, seguroK: seguro.a.key, seguroF: seguro.f, metaVoz: meta.voz, oiVoz: oi.voz,
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
            const protocolo = (qs, sec) => qs.filter((q) => { const a = resp(q), x = h(q); return !(a.key === 'base' && a.seguranca && x.fonte === D.guias.protocolo && x.secao === sec); });
            // (1b: «pessoa caiu da lancha» saiu desta lista: «caiu da lancha» é da lista SOS e a chave passou a `sos`, ver as verificações «1b» abaixo)
            const mob = protocolo(['não vejo a pessoa que caiu', 'perdemos de vista quem caiu', 'perdi a pessoa de vista', 'a pessoa que caiu sumiu'], 'Homem ao mar');
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
        rev6 = pg.evaluate("""() => { const B = window.CapitaoBrain, D = window.CapitaoDados;
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
              mar: onde(['pessoa ao mar', 'pessoa ao mar, o que faço'], 'protocolo', 'Homem ao mar', true) }; }""")
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
            ('revisão 6 do C5: "pessoa ao mar" traz o protocolo de homem ao mar, com seguranca (o "mar" sozinho não nomeia, o identCom "pessoa" sim)', not rev6['mar'], rev6['mar']),
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
            ('ficha completa para SEM DADOS', '## Telemetria' in x['sdF'] and '## Ficha resumida' not in x['sdF'], len(x['sdF'])),
            ('voz de "Oque você faz?" sem a IA diz o que o Capitão faz (não repete a abertura)', x['metaVoz'].startswith('Respondo sobre telemetria') and x['oiVoz'] == 'Capitão IA online. Que precisa?', (x['metaVoz'][:60], x['oiVoz'])),
            ('diagnóstico local: versões, internet, fonte "este aparelho"', 'Diagnóstico do Capitão IA neste aparelho' in x['dgTexto'] and 'cérebro ' + x['versao'] in x['dgTexto'] and x['dgSrc'].startswith('Fonte: este aparelho'), x['dgTexto'][:200]),
            ('ficha com todos os blocos', not faltam, faltam),
            ('ficha sem coordenadas do barco', not coord, coord),
            # Decisão 1.1.0 (b), contrato C2: títulos e fontes sem "(DEMO)", então a ficha não leva mais o rótulo. A exigência de
            # SEM DADOS sai junto: volta invertida na Fase 3 (nenhum SEM DADOS na ficha com simulacao: true).
            ('ficha sem o rótulo DEMO', 'DEMO' not in f, [l for l in f.split('\n') if 'DEMO' in l][:3]),
            ('ficha entre 3.000 e 10.000 letras (o proxy aceita 12.000)', 3000 <= len(f) <= 10000, len(f)),
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
             not [x for x in ("26°59", "048°36", "-26.99", "-48.6") if x in rev2['guincho']], rev2['guincho'][:200]),
            ('revisão 2 do C5: "guias de bordo" lista os 16 guias do D.guias, sem SEM DADOS nem "modelos não informados"',
             rev2['manualK'] == 'manual' and not rev2['manualSD'] and not rev2['faltam'], (rev2['manualK'], rev2['manualSD'], rev2['faltam'])),
        ]:
            if not cond:
                falhas += 1
                print('FALHA', nome, extra)
        print('ficha de bordo: %d letras' % len(f))
        if '-v' in sys.argv:
            print(f)
        falhas += agenda_sem_falta(pg)
        falhas += emergencia_1b(pg, res)
        falhas += faq_de_seguranca(pg)
        falhas += perguntas_da_g1(pg)
        falhas += consumo_sem_abastecimentos(b)
        # sem o capitao-clima.js (página acima): previsão SEM DADOS, nenhum vento previsto inventado
        sem = {r['q']: r for r in res}
        for q in ('clima e vento', 'é seguro sair hoje?'):
            t = sem[q]['text']
            if 'SEM DADOS' not in t or 'vento até' in t or 'rajadas até' in t:
                falhas += 1
                print('FALHA sem previsão carregada, %r inventou vento ou perdeu o SEM DADOS: %s' % (q, t[:200]))
        falhas += vento_do_dia(b)
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
    esperadas = {'sos': 'sos', 'oleo': 'oleo', 'canal16': 'canal16', 'rmmsi': 'canal16', 'epirb': 'epirb', 'seafire': 'seafire', 'disparo': 'seafire',
                 'salvatagem': 'salvatagem', 'queda': 'sos', 'diario': 'diario'}
    erros = []
    for k in chaves:
        r = x[k]
        txt = r['text'] + '\n' + r['fala']
        if r['key'] != esperadas[k]: erros.append('%s: chave %s' % (k, r['key']))
        if r['ia']: erros.append('%s: vai à IA' % k)
        if '710123456' in txt or str(x['mmsi']) in txt: erros.append('%s: traz o número do cadastro do MMSI' % k)
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
                    and mm in x['canal16']['text'] and ind in x['canal16']['text'] and ' — '.join(P['roteiro']) in x['canal16']['text'] and mm in x['rmmsi']['text'] and 'SEM DADOS' not in x['canal16']['text'],
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


def conta(nome, cond, extra=''):
    if cond:
        return 0
    print('FALHA', nome, extra)
    return 1


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
MAR = ' · mar (ondas): SEM DADOS no app — confira a previsão da Marinha antes de sair.'
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
    pg.evaluate(SEMEIA, {'desloca': -86400e3, 'max': 30, 'min': 20, 'vento': 25, 'raj': 33, 'dir': 180, 'modelo': 'ECMWF'})  # só a de ontem
    sem = pg.evaluate(RESPOSTAS)
    windy = [x for x in com['clima']['acoes'] if x.get('ext') and x.get('href', '').startswith('https://www.windy.com/')]
    linha1 = lambda r: r['text'].split('\n')[0]
    for nome, cond, extra in [
        ('clima com a previsão: 1ª linha (a falada) com máx/mín, vento, rajada, direção, fonte e hora', linha1(com['clima']).startswith('Hoje em Balneário Camboriú: máx 27° · mín 18° · ' + VENTO) and fonte in linha1(com['clima']) and VENTO in com['clima']['voz'], linha1(com['clima'])),
        ('clima: fonte com o modelo e a hora da leitura; toque abre o windy.com (nova aba)', ('previsão ' + fonte) in com['clima']['src'] and len(windy) == 1, (com['clima']['src'], com['clima']['acoes'])),
        ('"vai ter rajada hoje?" responde com a rajada prevista', com['rajada']['key'] == 'clima' and 'rajadas até 19 nós' in com['rajada']['text'], com['rajada']['key']),
        ('seguro para sair: vento previsto com fonte e hora, mar (ondas) SEM DADOS + "confira a previsão da Marinha antes de sair"', (VENTO + MAR) in com['seguro']['text'] and fonte in com['seguro']['text'] and ('previsão ' + fonte) in com['seguro']['src'], com['seguro']['text'][-260:]),
        ('seguro para sair: o vento previsto não muda a decisão (sem limite de vento inventado)', linha1(com['seguro']) == linha1(sem['seguro']), (linha1(com['seguro']), linha1(sem['seguro']))),
        ('seguro para sair com vento forte (45/60 kn): a previsão aparece com a fonte, a decisão não muda e nenhum limite é inventado', ('vento até 45 nós de sudoeste, rajadas até 60 nós' + MAR) in forte['seguro']['text'] and ('lida às ' + hora_f) in forte['seguro']['text'] and linha1(forte['seguro']) == linha1(sem['seguro']) and linha1(forte['seguro']).startswith('Sim, com ') and not [x for x in LIMITE if x in forte['seguro']['text'].lower()], (linha1(forte['seguro']), [x for x in LIMITE if x in forte['seguro']['text'].lower()])),
        ('leitura do dia sem o vento: seguro com vento SEM DADOS e mar (ondas) SEM DADOS, nada inventado', ('vento SEM DADOS' + MAR) in semv['seguro']['text'] and 'vento até' not in semv['seguro']['text'] and linha1(semv['seguro']) == linha1(sem['seguro']), semv['seguro']['text'][-200:]),
        ('ficha da IA: vento previsto com fonte e hora, sem limite inventado e sem coordenadas', VENTO in com['bloco'] and fonte in com['bloco'] and 'não tem limite de vento' in com['bloco'] and not [x for x in ('26°59', '048°36', '-26.99', '-48.6', 'windy.com/') if x in com['ficha']], com['bloco'][:300]),
        ('rajada que o ECMWF não trouxe: vem do melhor modelo do Open-Meteo, dito na resposta', 'rajadas até 21 nós (rajada do melhor modelo do Open-Meteo; o ECMWF não trouxe)' in raj['clima']['text'] and ('lida às ' + hora_r) in raj['clima']['text'], linha1(raj['clima'])),
        ('só a leitura de ontem: clima, seguro e ficha com SEM DADOS e nenhum vento previsto', all('vento até' not in x and 'rajadas até' not in x for x in (sem['clima']['text'], sem['seguro']['text'], sem['bloco'])) and 'Previsão do dia: SEM DADOS' in sem['clima']['text'] and 'Sem previsão de vento e mar carregada (SEM DADOS) — confira a previsão da Marinha antes de sair.' in sem['seguro']['text'] and 'Previsão do dia: SEM DADOS' in sem['bloco'] and not sem['clima']['acoes'][1:], (linha1(sem['clima']), sem['bloco'][:160])),
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


if __name__ == '__main__':
    main()
