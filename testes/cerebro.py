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
import sys
from playwright.sync_api import sync_playwright

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
    ('pegamos uma rajada agora e o barco adernou', 'fallback'), ('rajada derrubou alguém no mar agora', 'fallback'),
    ('a rajada de hoje arrancou o toldo', 'fallback'), ('há rajada forte entrando, o que faço?', 'fallback'),
    ('quanto tempo dura uma rajada?', 'fallback'), ('tem rajada hoje?', 'clima'), ('qual a previsão de rajada para amanhã?', 'clima'),
    # C5 (CONTRATO §6.2): com os 91 trechos dos 16 guias, pergunta fora do barco continua sem trecho (nenhum guia tem "lais")
    ('como se faz um nó lais de guia?', 'fallback'),
    # Revisão do C5: trecho de segurança no topo (g_epirb, g_seafire, protocolo §DSC) responde local e não vai à IA (PEDE_IA False,
    # PROMPT §2.3); "supressão" é a rota seafire (§2.3); as perguntas dos cartões da F1 ao chat (Seafire, AIS e guincho, CONTRATO §1.4)
    # caem na chave do equipamento ou no guia, nunca no SOS, no roteiro MAYDAY (canal16) nem na maré.
    ('teste da baliza', 'base'), ('como acionar o disparo manual do sistema fixo?', 'base'), ('supressão', 'seafire'), ('botão distress', 'base'),
    # Revisão 2 do C5: o cartão do guincho perguntava "guincho da âncora Lewmar", que caía na resposta pronta "ancora" (com a posição
    # do snapshot e o texto antigo do §3): agora pergunta o procedimento e cai no g_ancora. Radar e piloto: a resposta pronta dos
    # eletrônicos não fala deles; a pergunta de procedimento cai no guia de cada um (CONTRATO §1.4).
    ('sistema fixo de supressão', 'seafire'), ('transponder em-trak', 'base'), ('como lançar com o guincho Lewmar', 'base'),
    ('como ligar o radar Garmin', 'base'), ('como engatar o piloto automático Raymarine', 'base'),
    # Revisão 2 do C5: saudação com assunto de segurança (o g_epirb §2 no topo do buscaBase, que a tela manda à IA) fica no aparelho;
    # depois do disparo do sistema fixo, o trecho do topo manda não abrir o acesso ao motor (nunca o "use o disparo manual").
    ('como você me ajuda com o teste da baliza?', 'saudacao'), ('o que você sabe sobre o teste da baliza?', 'saudacao'),
    ('o que fazer depois do disparo do sistema fixo', 'base'), ('o sistema fixo disparou', 'base'), ('o sistema fixo descarregou', 'base'),
    ('alarme do sistema fixo', 'base'),
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
    ('o sistema descarregou', 'base'), ('o sistema fixo disparou sozinho', 'base'), ('distress', 'base'), ('como usar o botão distress', 'base'),
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
    ('pessoa caiu da lancha', 'base'), ('não vejo a pessoa que caiu', 'base'), ('perdemos de vista quem caiu', 'base'),
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
    ('bombas de porão', 'porao'), ('como testar as bombas de porão', 'porao'), ('como ligar as bombas de porão', 'base'),
    ('como trocar a bateria de partida', 'base'), ('como verificar a bateria de partida', 'base'), ('bateria de partida', 'eletrico'),
    ('o motor não pega, a bateria de partida está fraca', 'motores'),
    ('o disjuntor caiu, qual o procedimento', 'fallback'), ('a bateria caiu, procedimento', 'eletrico'), ('o gerador caiu, procedimento', 'gerador'),
    ('o plotter caiu, como resolver', 'eletronicos'), ('o motor caiu, como resolver', 'motores'), ('a conexão do plotter caiu, procedimento', 'eletronicos'),
    ('a energia caiu', 'fallback'), ('o wifi caiu', 'fallback'), ('a tensão caiu', 'eletrico'), ('caiu a chave no mar', 'fallback'),
    ('onde fica o manual do motor', 'manual'), ('como acho o manual do motor', 'manual'), ('onde fica o manual', 'manual'),
    ('tem vista para o mar?', 'fallback'), ('qual a vista do mar', 'fallback'), ('a temperatura do mar caiu', 'fallback'),
    ('pessoa ao mar', 'base'),
    # as quatro perguntas de religar depois do disparo e o alarme de âncora ficam no trecho de segurança / no plotter (seção na verificação)
    ('como religar o gerador depois que o sistema fixo disparou', 'base'), ('como ligar o gerador depois do disparo do sistema fixo', 'base'),
    ('o sistema fixo disparou, como religo o gerador?', 'base'), ('como abrir o motor depois que o sistema fixo disparou', 'base'),
]
# IA na nuvem (quando a tela chama a IA, com o aparelho ativado): SEM DADOS, trecho do guia e pergunta sobre o app — nunca
# emergência, óleo, registro no diário, resposta pronta ou só um cumprimento.
PEDE_IA = {
    'Oque você faz?': True, 'o que vc sabe fazer?': True, 'como ligar o gerador?': True, 'qual o preço do dólar?': True, 'não registre isso': True,
    '': False, 'oi, bom dia': False, 'MAYDAY, homem ao mar!': False, 'pressão de óleo baixa no motor BB': False,
    'Registre no diário: saída com 4 pessoas': False, 'autonomia': False, 'é seguro sair hoje?': False, 'diagnóstico': False,
    'a IA não está funcionando': False, 'qual a rajada máxima que o barco aguenta?': True,
    # revisão do C5: base com trecho de segurança no topo (o respostaBase marca a.seguranca) e a rota seafire ficam no aparelho
    'teste da baliza': False, 'como acionar o disparo manual do sistema fixo?': False, 'supressão': False, 'botão distress': False,
    'transponder em-trak': False,
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
}


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
            const inteira = ['sistema fixo em caso de alarme', 'o sistema fixo descarregou', 'o sistema fixo disparou', 'o que fazer depois do disparo do sistema fixo',
              'alarme do sistema fixo', 'teste da baliza', 'botão distress'].map((q) => { const a = resp(q), x = h(q), t = (x.texto || '').replace(/\\s+/g, ' ').trim();
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
            const mob = protocolo(['pessoa caiu da lancha', 'não vejo a pessoa que caiu', 'perdemos de vista quem caiu', 'perdi a pessoa de vista', 'a pessoa que caiu sumiu'], 'Homem ao mar');
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
              disparo: onde(['como religar o gerador depois que o sistema fixo disparou', 'como ligar o gerador depois do disparo do sistema fixo',
                'o sistema fixo disparou, como religo o gerador?', 'como abrir o motor depois que o sistema fixo disparou'], 'g_seafire', '3 · Depois da descarga', true),
              ancora: onde(['alarme de âncora', 'como fundear'], 'g_eletronicos', '3 · Alarme de âncora'),
              arLigar: onde(['como ligar o ar condicionado'], 'g_clima', '1 · Ligar'),
              arFiltro: onde(['trocar o filtro do ar condicionado'], 'g_clima', '3 · Alarme de fluxo'),
              mar: onde(['pessoa ao mar', 'pessoa ao mar, o que faço'], 'protocolo', 'Homem ao mar', true) }; }""")
        for nome, cond, extra in [
            ('revisão 6 do C5: a bomba de água salgada, o rotor e o impeller vão ao g_motores §7 e à Climatização (§3 alarme, §1 ligar, §5 desligar), e a do gerador ao g_gerador §7, não à resposta pronta do porão',
             not (rev6['rotor'] or rev6['alarme'] or rev6['ligar'] or rev6['desligar'] or rev6['gerador']),
             (rev6['rotor'], rev6['alarme'], rev6['ligar'], rev6['desligar'], rev6['gerador'])),
            ('revisão 6 do C5: "como trocar/verificar a bateria de partida" vai ao g_eletrico §1 · Bancos, não à resposta pronta dos motores', not rev6['bancos'], rev6['bancos']),
            ('revisão 6 do C5: depois do disparo do sistema fixo, religar o gerador ou abrir o motor traz o g_seafire §3 (trecho de segurança, sem IA), não a resposta pronta',
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


if __name__ == '__main__':
    main()
