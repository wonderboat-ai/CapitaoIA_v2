# -*- coding: utf-8 -*-
"""Capitão IA — matriz de verificação das telas (critérios de aceite).

Cada tela × tema (escuro, claro) × tamanho (web 1440×900 · 1280×720 · 1920×1080 · 1024×768;
app 390×844 · 360×640 · 430×932 · 844×390). Confere: erro de script, rolagem lateral, imagem/ícone
deformado (proporção exibida × natural) e se a prancheta desenhou. Opcional: offline depois da 1ª visita.
React do próprio site (assets/vendor): com o unpkg.com fora do ar, o início (web e app) e o SOS montam, sem erro de script e
sem nenhum pedido ao unpkg; no teste offline, nenhum pedido ao unpkg (instalação do SW inclusive) e a instalação já
guarda os dois arquivos do React (CORE do sw.js, tudo ou nada). Reserva da troca de versão: com o assets/vendor fora, o SOS
monta com o React do endereço do unpkg e o mesmo SRI (o cache do SW da 1.0.x tem essa cópia; aqui o teste a serve).
Também o login e a lista (index.html?v=lista), fora das TELAS do sw.js, em todos os tamanhos: sem erro, sem rolagem
lateral, sem imagem deformada; no login, o ENTRAR na 1ª tela (altura ≥ 640) e o crédito inteiro (altura ≥ 844).
Vento e rajada do dia no cabeçalho (paridade Avanti 1.24.0), em Main, H2-Home-Mobile e S1-SOS-Web, com o Open-Meteo simulado
(JSON fixo no route; nenhum pedido sai para a internet): direção e "n/n KT", os três toques abrindo o windy.com na posição de
referência (nova aba, noopener), nada cortado nem sobreposto no cabeçalho (web 1440×900 e 1024×768, app 390×844 e 360×640, dois
temas); sem rede e sem leitura do dia, "—" (nunca o vento do snapshot); sem rede com a leitura salva de hoje, ela com a hora dela;
rajada que o ECMWF não trouxe vem do melhor modelo, dito no title. Na B3-Carta-Resposta (responde ali mesmo, sem o cabeçalho do
clima), a leitura de hoje salva entra no clima e no "seguro para sair?" como na home, com fonte, hora e o windy.com em nova aba;
sem ela, a frase do §2.5 (sem conexão agora) e nenhum vento previsto.
Ícones dos atalhos do app instalado (paridade Avanti 1.24.0, desenho próprio), em toda rodada menos a --so-offline (é o manifest,
não uma tela): cada shortcut tem ícone any e maskable; cada src responde 200 e o PNG tem o tamanho declarado (cabeçalho lido com
struct, sem Pillow); desenho centrado e, no maskable, fundo inteiro e desenho dentro da zona segura de 80 %.
Dados do aparelho (dados.html, paridade Avanti 1.24.0), como o login e a lista: em todos os tamanhos e nos dois temas, sem erro,
sem rolagem lateral, com o fundo do tema e o SOS à vista no topo e depois de rolar até o fim (S1 no computador, S2 no celular);
o rodapé do Main e da H2 leva a ela. Ida e volta: o diário, os documentos e os abastecimentos com A e B vão para o arquivo (sem a
sessão, as tentativas de login nem as chaves); o aparelho passa a ter A e C; restaurar dá C, B e A (nenhuma linha some, nada
duplica ao restaurar de novo); a linha que entra vai pela hora, mais nova primeiro (sem linha em comum: aparelho A, arquivo C e B
→ C, B, A; a mais nova do arquivo vira o "último" do A2 e abre os "Últimos registros"), a sem hora na ordem do arquivo; tarefas
feitas e Equipe só somam; o tema só volta com a caixa marcada; arquivo de outro app, de formato novo, corrompido ou com linha de
forma errada não muda nada; sessão e chave da IA de um arquivo montado à mão nunca entram; item que o app não lê (linha sem
texto, Executado sem data, telefone que não é texto) nunca entra no registro. Desfeito depois não volta: marcar o Executado (C1),
cadastrar um telefone e abrir um convite (G4), baixar, desfazer os três nas telas e restaurar → nada volta, a prévia diz o que
ficou de fora e a tarefa continua aberta (num aparelho sem esse diário, a cópia devolve os três); as telas do app gravam os mesmos
textos. A cópia leva intacta a linha do SOS (com a posição) e a página avisa. Sem sessão, vai para o login. Abre offline
(--offline, com "dados" na lista). No --offline, cada tela e página da rodada tem de estar no cache da instalação (TELAS/CORE).
Nenhum selo (decisão b da 1.1.0; o Manual fica de fora até a Fase 8, que o reescreve): o rodapé de nenhuma tela ou página diz
DEMO nem dados fictícios; nenhuma caixa com a borda violeta do antigo selo diz DEMO, fictício ou SNAPSHOT; na Main e na H2 a
caixa do cabeçalho é a ÚLTIMA LEITURA (dia e hora do snapshot), nunca vazia; S1 e S2 sem caixa de selo; login e lista sem a
linha DEMO; nenhum DEMO, Demo, demonstração ou fictício escrito no código de tela nenhuma (texto visível, title, aria-label e alt;
o que vem do capitao-dados.js fica de fora até o C2, o C12 e a 1b trocarem os rótulos do gerador) e nenhuma tela afirma que o
dado é real ("leitura real", "dados reais", "barco real": decisão 5). Login do convidado (decisão
k), com "login" na lista, sem senha nenhuma (o deriveBits do navegador é trocado por um que devolve o hash público do usuário do
sal pedido): o botão mostra CONVIDADO e põe a chave "demo" no campo; "demo", "Demo", " DEMO ", "Convidado" e o valor do botão
entram como demo; digitar "Convidado" com 4 erros na trava entra e zera a trava (não chega aos 5); usuário que não existe conta
1 erro. Equipe (G4 web e app) com o convidado logado: "Convidado", papel convidado · fora da lista da embarcação, sem A
CONFIRMAR, sem DEMO, Demo nem demonstração.
SOS sem dado gerado da embarcação além do nome (trava §2.1 do PROMPT; CONTRATO-DADOS §1.3 e §6.2 C4): em S1 e S2, em todos os
tamanhos e temas e na abertura offline (--offline), nem "REG." nem o registro, o fabricante, o modelo, a marca, o rotulo, a
motorizacao e o motor do embarcacao do capitao-dados.js (sem distinguir maiúsculas nem acentos; o registro com qualquer separador)
no texto visível, no title, no aria-label, no alt e no href — na tela fechada, com o roteiro MAYDAY aberto e com cada cartão de
protocolo aberto (a tela volta ao estado inicial); o D tem de ter esses campos e o roteiro e todos os cartões têm de abrir (senão a
conferência não vale). A base entra na 1b, que a tira do cabeçalho da S1.
1b (SOS fora da simulação, PROMPT §2.1): a mesma leitura do SOS (achados_texto_sos) agora também recusa a base, o MMSI de 9 dígitos, coordenada,
snapshot.local e snapshot.estado, a palavra snapshot, SOG/PROA com número, fabricante e modelo de equipamento e SEM DADOS/DEMO/A CONFERIR/«último fix»
(o chip do clima da S1 fica de fora: é a previsão real, com o teste da F13). A F3 (web e app) diz «MMSI (cadastro do app)» e a nota «No MAYDAY e no DSC:
MMSI do rádio de bordo», nunca «MMSI SEM DADOS» nem «MMSI da embarcação (DSC)». O teste do dados.html cria a linha do SOS tocando no MAYDAY (F04: abrir a
tela não grava). A conferência sem login, sem rede, com GPS e por ação é o testes/sos.py.
Equipamento de segurança fora de Equipamentos, Leme e Documentos (CONTRATO-DADOS §1.4, C5): na F1 (web e app) e na E2, nenhum
modelo nem fabricante do EPIRB e do Seafire no texto visível e nos atributos (na E2 também com cada sistema e cada sintoma
escolhidos; o fabricante fica de fora quando é o próprio nome do sistema, o id: "Seafire"), nenhum link do chat (#q=) com o
fabricante deles, e, na F1, o cartão do VHF e o do áudio abrem a pergunta certa do FAQ de eletrônicos (#p= > 0, na pergunta de
"VHF" e na de "Fusion"), pelas palavras do equipamento. Revisão do C5: na F1, nenhum cartão cortado (a pergunta, a fonte e a ação
à vista: a grade da web rola), e a pergunta de cada cartão ao chat (#q=), passada pelo cérebro, não cai em chave de emergência
(sos, oleo, canal16, epirb, seafire), menos a do próprio equipamento de segurança, que dá a chave dele, e a resposta dos outros cita
o guia do próprio equipamento (menos dessalinizador, porão e sistema elétrico, cujas respostas prontas a Fase 3 reescreve); na F1 e na
E2, o fabricante não se repete quando o modelo já começa por ele ("Seakeeper Seakeeper 3").
Validade do EPIRB e do Seafire (CONTRATO-DADOS §1.4, revisão do C7): a data do `doc-epirb` e o `vence` das tarefas deles (o autoteste do
EPIRB e a inspeção do sistema fixo) só em Equipamentos, Leme e Documentos (B1, B2, C1, C2 e G1). Em toda outra tela, nenhuma delas no texto
visível nem nos atributos (title, aria-label, alt, href), nem completa (dd/mm/aaaa) nem curta depois de "vence", "venceu", "validade" ou
"vencimento" (a A1 listava a agenda inteira com "vence 09/11" e "vence 16/03"); em C1 e G1 a data aparece (controle: a conferência
não vale se o detector não a enxerga onde ela pode estar).

Fase 4, P4B (base compartilhada das telas; PROMPT Fase 4 e Fase 7 «verificar.py»): a matriz roda com o replay congelado em 60 s (cruzeiro, sem alarme) e uma passada
a 105 s (a janela do alarme: só AVISO) em 2 tamanhos e 2 temas por tela; em cada instante, a varredura do texto visível, do title, do aria-label, do placeholder e do alt
pelas regex ROTULOS, AUTENTICIDADE, VAZIOS e VISIVEL do testes/proibidos.json (cada uma com a flag dela), a tela com `typeof CapitaoReplay === 'object'` (o filtro de
«Failed to load resource» esconde o script ausente; S1/S2 sem ele) e a faixa global de alerta: ausente em 60 s, presente em 105 s (AVISO, «ABRIR ›» → C3-Leme-Alerta.dc.html#alarme=<id>,
com a hora «desde», empurrando a prancheta, sem fala nem registro) e sempre ausente em S1/S2, no Manual e na C3. PENDENTES_ROTULO lista as telas que ainda têm rótulo (cada item da
Fase 4 retira as suas; uma tela da lista que já está limpa reprova, para a lista só encolher). Sem congelar, a leitura da Main, da A1 e da E1 muda em 1,5 s (a C3, que a Fase 4
ainda não tornou viva, está em PENDENTES_MUDA). Selo do coletor pela cor (F06): verde com o replay ao vivo, amarelo com a última leitura (replay desligado ou que falhou ao carregar).
Offline: capitao-replay.js responde 200 e CapitaoReplay.quadro() não é nulo em cada tela (o SOS só confere o arquivo). Login com o botão de SOS (S2 no celular, S1 no computador).

Fase 4, P4D (a Carta: B1 Gestão, B2 Sistemas, B3 Resposta por voz; `--so-p4d` roda só as conferências dela e `--mutantes-p4d` planta 26 defeitos, todos acusados): B1 com a propulsão, o diesel,
o consumo, a autonomia e as horas até a troca do óleo do quadro (nada do snapshot de 26/09), o dia do instante, os 4 cartões iguais às contagens do CapitaoAgora e do cérebro (Executado e pendência
resolvida por linha nova acompanham); B2 com o estado de cada um dos 11 sistemas do quadro e de D.equipamentos (áudio e VHF), EPIRB e Seafire só com o procedimento padrão e a nota da etiqueta, o
fabricante e o modelo de D.equipamentos em toda linha (as bombas e as baterias também); B3 com a hora da resposta (calculada uma vez por pergunta; nunca na emergência), a marca da janela de
conversa em emergência (CapitaoEmergencia: abre com sos, óleo, canal 16, EPIRB e Seafire, não com salvatagem nem MMSI; dentro dela posição, SOG, chegada e pessoas viram «LEIA NO PLOTTER»), o
botão de uma resposta (#capitao-prop-… e #capitao-relato-…) que vira a pergunta sem gravar, e nenhum link vazio. Sem congelar o replay, a propulsão da B1 e da B2 muda em 1,5 s; com simulacao false
as duas leem a última leitura salva (D.snapshot).

Fase 4, P4E (o Leme: C1 Manutenção, C2, C3 alerta vivo, e os checklists C4 web e app; `--so-p4e` roda só as conferências dela e `--mutantes-p4e` planta 35 defeitos, todos acusados; `MUT_FILTRO=texto`
refaz só os mutantes cujo nome tem o texto): C1 com as 6 leituras de agora do quadro (o vento «a bordo agora»), a fonte e o resumo sem rótulo, as horas até a troca do horímetro de agora (32,4 h e 58,6 h, e não as
da agenda gerada), os 3 cartões iguais às contagens do CapitaoAgora (a agenda e as tarefas da equipe, as do aparelho também; Executado acompanha e o Executado da tarefa do aparelho grava 1 linha nova com sim);
C2 com as atrasadas, o horímetro de agora (BB, BE e gerador) e as mesmas horas até a troca; C3 como alerta vivo: o AVISO a 105 s com a leitura «BE 89,6 °C · 12:01:45» (o lado, o valor do alarme e a hora do
quadro), a faixa normal do guia (a do regime do giro, no óleo), a tendência dos 10 s (o quadro do segundo 95 da volta) e dos 30 s (+7,5 °C, a do cérebro), os passos e a fonte do catálogo, o equipamento de
D.equipamentos, o pisca; o NORMALIZADO às 11:59 a 60 s (o fim da volta anterior, 11:59:27) e às 12:01 ao fixar 120 s com a tela aberta, sem navegação, fala nem registro; sem alarme e id fora do catálogo
(neutro, sem rótulo), o alerta sem janela («dentro da faixa»), o crítico plantado (cenário alarme-critico injetado: cartão vermelho que brilha); registrar() só com o toque (1 linha com valor, lado e hora reais,
sim; dois toques seguidos não duplicam; nem ao abrir nem a cada mudança de estado), sempre escura (tema claro) e leve (sem tema, sem cérebro até o toque); C4 nos 4 tipos a 60 e a 105 s: itens, fonte, verificação do
quadro (s02: ✓ a 60 s, ✗ a 105 s), marcas, desmarca do ✓ do quadro, Recomeçar sem diário, CONCLUIR = 1 linha nova (dois toques seguidos não duplicam), links do FAQ e do app; simulacao false nas 5 telas.

Fase 4, P4F (o Modo navegação: E1 Gatilhos e E2 Sintoma; `--so-p4f [E1-Navegando-Gatilhos|E2-Navegando-Sintoma]` roda só as conferências dela e `--mutantes-p4f` planta 31 defeitos, todos acusados; `MUT_FILTRO=texto`
refaz só os mutantes cujo nome tem o texto): E1 NAVEGANDO a 60 e 105 s em 3 tamanhos e 2 temas (os 6 gatilhos na ordem do CSS, os links, a pergunta de cada gatilho ao chat e a chave que o cérebro responde: o relato no porão
é SOS e nunca traz o nível; o vigia com o chip «AO VIVO hh:mm:ss», o estado, as 5 leituras do quadro e o diesel do quadro e não o de 26/09, a posição e a fonte, sem corte; a nota da troca sem «ainda não está ativa»); o alarme
(o 1º cartão no DOM e no CSS leva à C3-Leme-Alerta.dc.html#alarme=<id>, amarelo no AVISO, vermelho no crítico plantado, também com o barco parado; o toque abre a C3; nunca abre o SOS, fala ou grava); a troca automática com
a tela aberta (SOG 0: aos 3 s ainda NAVEGANDO, aos 7 s FUNDEADO com ÂNCORA/GARRA, CHECKLIST DE SAÍDA, ABASTECER e DIÁRIO e sem o REGISTRAR; SOG 1,5: só aos 7 s volta), a histerese (0,8 nó nunca troca; 0,3 nó com o quadro
Atracado vira ATRACADO; um SOG 0 de 3 s não pisca), a aba escondida que zera a contagem, o REGISTRAR POSIÇÃO só com o toque (1 linha com sim: true, sem duplicar em 2,5 s, com a janela de emergência a linha leva «LEIA NO
PLOTTER»), a E1 que anda sem congelar e o ramo simulacao false (a última leitura salva como reserva). E2: a leitura de agora de cada um dos 5 sistemas (motores, gerador kW, Seakeeper rpm e %, climatização, GPS com
satélites) do quadro a 60 e 105 s, o fabricante e o modelo de D.equipamentos (nunca «modelo SEM DADOS»), a introdução sem «(guias DEMO)», cada sistema × sintoma sem termo do §3, a resposta com o segundo do quadro
(«Calculado às 12:01:00 pelo Capitão IA»; a de emergência sem hora e sem leitura; o relato de óleo baixo sem o óleo do quadro), a janela de conversa em emergência (marca, vale no cérebro, o botão de uma resposta), a
resposta calculada uma vez por escolha enquanto a leitura anda, o registrar só com o toque e o ramo simulacao false. O instante guarda 1 s: o gancho `capitao.replay.sobre` só entra com a tela aberta se o teste
muda também o `capitao.clima.v1` (uma leitura de OUTRO dia, que não trava nada).

Fase 4, P4G (a Home: Main e H2, e os atalhos H3 web e app; `--so-p4g [Main|H2-Home-Mobile|H3-Atalhos-Editar-Web|H3-Atalhos-Editar]` roda só as conferências dela e `--mutantes-p4g` planta 47 defeitos, todos acusados;
`MUT_FILTRO=texto` refaz só os mutantes cujo nome tem o texto; o Worker da IA é de mentira, sem cota): a leitura de agora a 60 e 105 s (a Main: o selo «AO VIVO · hh:mm:ss», o LED verde que pulsa, o registro do
cadastro, a faixa de baixo SOG/PROA/VENTO/24 V/ÁGUA DOCE/DIESEL igual ao D.campos e ao CONTRATO §1.22, o diesel do quadro e não o 54/52 de 26/09, o estado e o local do quadro com a dica inteira e a hora que não é cortada;
a H2: o LED e a dica), os 5 e os 4 cartões com o fabricante, o modelo e as horas do gerador do quadro e do D.equipamentos (planta outros fabricantes: aparecem; nenhum fixo no código), os chips («3 ATRASADAS», «ROTOR · 2 D»,
«PRONTO», «5 FAQ») iguais às contagens do CapitaoAgora e ao Executado, nenhuma caixa de selo violeta e a varredura do §3; o ramo sem fabricante (a simulação deixa o cartão sem a palavra, simulacao false diz «SEM DADOS»); a Home
que anda sozinha; simulacao false com a última leitura salva (LED âmbar parado, «ÚLTIMA LEITURA · 26/09 10:12»); os 5 ouvintes (telemetria, virada do dia, botão de resposta, hash, ENCERRAR) tirados pelo componentWillUnmount e
religados sem vazar em 3 voltas; a IA (o 3º argumento é B.resumoAgora, o histórico é B.historicoIA — sem coordenadas e sem a emergência —, o ditado vai corrigido e a resposta da IA é contada ao cérebro com B.conversa: «o
gerador» depois de «Qual equipamento você quer ligar?» continua o «como ligar?»); a janela de conversa em emergência (o SOS a marca, dentro dela a posição é «LEIA NO PLOTTER» e nada vai à IA, o NOVA e o ENCERRAR zeram a marca e
chamam B.limpaConversa); os botões das propostas (#capitao-relato-… e #capitao-prop-…: o toque vira a pergunta digitada, não navega, Registrar = 1 linha, Não registrar e Recusar = 0, Confirmar grava a regra ou a tarefa e o
Desfazer a tira, «O que verificar?» vai à IA com o relato, o toque não leva o anexo nem apaga o rascunho); e a H3 sem rótulo (nem com D.demo ligado) com os atalhos para o mapa de sensores e os checklists da plataforma da tela.
A única asserção que já existia e mudou: `problemas_selo` de Main e H2 passou de «a caixa do cabeçalho é a ÚLTIMA LEITURA» para «nenhuma caixa de selo» (a linha da P4G manda `demo ''`; com o replay ao vivo a caixa dizia uma
leitura de 26/09 ao lado do «AO VIVO»).

Fase 4, P4I (Documentos G1 e Abastecimento G2, web e app; `--so-p4i [Tela…]` roda só as conferências dela e `--mutantes-p4i` planta 27 defeitos, todos acusados; `MUT_FILTRO=texto` refaz só os mutantes cujo nome tem o texto; sem Worker): G1 aba
Documentos com a validade de cada documento = hoje + o prazo relativo (venceEm), conferida contra o relógio da própria página e refeita com o dia virado (fixar 60@1152, sem recarregar), a situação do CapitaoAgora (VENCIDO, VENCE EM n D,
EM DIA; a nota fiscal, CONFERIDA, sem prazo), os cartões iguais a contagens(), nenhuma linha com A CONFERIR, MANUAL NO DRIVE nem SEM DADOS e a pergunta de cada linha no docsvenc sem IA; o envio de documento (anexo: continua A CONFERIR, carimbo sim: true só
com a simulação, selo «apresentação» só com simulacao false); a aba Peças com as 12 peças do D.pecas (quantidade, mínimo, ZERADA / ABAIXO DO MÍNIMO / NO MÍNIMO / OK, tarefas ligadas com o prazo de hoje), o aviso das zeradas e no mínimo, o −1 USADA com
Desfazer (movimento novo, o −1 fica; recusado se outra aba mexeu), o ✎ e o + PEÇA só com inteiro puro de 0 a 999, a quantidade e o mínimo entregues ao cérebro como TEXTO e o erro EXPLÍCITO quando o cérebro devolve null; G2 aba Nível com o diesel, o último
abastecimento, o consumido desde ele e a autonomia do instante (não a leitura de 26/09), o histórico do D.abastecimentos, a regra de bordo sem rótulo e os gráficos do capitao-grafico.js (diesel válido, água doce e servidas, baterias com 3 séries, estação
meteorológica com o TWA, 5 janelas); aba Consumo com o L/h, as horas e os litros de cada faixa do CapitaoReplay.porFaixa() e a soma (motores + gerador) batendo com o contador de diesel; a foto da NF (A CONFIRMAR, carimbo sim); o ramo simulacao false
(SEM DADOS só ali); os estados de dentro das 4 telas em 3 tamanhos e 2 temas (sem rolagem lateral nem texto cortado em silêncio); e o código (ouvintes, timers, DEMO, SVG, CRLF). PENDENTES_ROTULO fica só com a G4; a G2 entra em MUDA_SEM_FIXO (a leitura anda).

Uso (site servido em http://127.0.0.1:8765):
    python testes/verificar.py                     todas as telas, todos os tamanhos e temas
    python testes/verificar.py Main S2-SOS-Mobile  só essas telas (login, index e dados: as páginas fora das TELAS)
    python testes/verificar.py --fotos             salva capturas em testes/saida/
    python testes/verificar.py --offline           testa a abertura offline depois da 1ª visita
    python testes/verificar.py --so-offline        só o teste offline (sem a matriz)
Navegador: Edge instalado (channel="msedge").
"""
import datetime
import json
import math
import os
import re
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8765/'
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(RAIZ, 'ferramentas', 'demo'))
import confere  # noqa: E402  (barco_sos: o dado da embarcação que o SOS nunca mostra, a mesma regra do gerador)
SAIDA = os.path.join(os.path.dirname(__file__), 'saida')
WEB = [(1440, 900), (1280, 720), (1920, 1080), (1024, 768)]
APP = [(390, 844), (360, 640), (430, 932), (844, 390)]
MOBILE_UA = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Mobile Safari/537.36'
# React do próprio site (paridade Avanti 1.24.0): estas telas montam com o unpkg.com fora do ar.
SEM_UNPKG = ['Main', 'H2-Home-Mobile', 'S2-SOS-Mobile']
# Telas com o <capitao-hora-clima> no cabeçalho (o SOS também: só previsão real ou a última leitura salva).
CLIMA = ['Main', 'H2-Home-Mobile', 'S1-SOS-Web']
# Telas que respondem ali mesmo sem o <capitao-hora-clima>: a previsão salva pelo cabeçalho entra na resposta como na home.
RESPOSTA_CLIMA = ['B3-Carta-Resposta']
REACT_LOCAL = BASE + 'assets/vendor/react-18.3.1/'
REACT_ARQS = ['react.production.min.js', 'react-dom.production.min.js']
# reserva do support.js quando a cópia local falha (troca de versão com o SW da 1.0.x): endereço do unpkg → arquivo local (mesmos bytes)
REACT_RESERVA = {'https://unpkg.com/react@18.3.1/umd/react.production.min.js': 'react.production.min.js',
                 'https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js': 'react-dom.production.min.js'}


def telas():
    sw = open(os.path.join(RAIZ, 'sw.js'), encoding='utf-8').read()
    m = re.search(r'const TELAS = \[(.*?)\];', sw, re.S)
    return re.findall(r"'([^']+)'", m.group(1))


def eh_app(t):
    return not (t == 'Main' or t.endswith('-Web') or t.startswith('D-') or t.startswith('Manual-'))


def eh_unpkg(url):
    return bool(re.search(r'(^|\.)unpkg\.com$', urllib.parse.urlparse(url).hostname or ''))


def corta_unpkg(ctx):
    """unpkg.com fora do ar no contexto (o route mais novo ganha do que já houver); devolve a lista dos pedidos que tentaram ir para lá."""
    pedidos = []
    ctx.on('request', lambda r: pedidos.append(r.url) if eh_unpkg(r.url) else None)
    ctx.route('https://unpkg.com/**', lambda rt: rt.abort('connectionrefused'))
    return pedidos


# Fase 4 (P4B): as regex do §3 (testes/proibidos.json, a mesma fonte de todas as varreduras), cada uma com a flag dela
TERMOS = confere.carrega_termos()
VARREDURA = ('ROTULOS', 'AUTENTICIDADE', 'VAZIOS', 'VISIVEL')
# Telas que ainda têm rótulo do §3 no texto (cada item da Fase 4 retira as suas daqui; o P4K a deixa só com o que a Fase 8 reescreve). O Manual é a apresentação,
# reescrita na Fase 8. Uma tela daqui que já está limpa nos dois instantes reprova (retire-a da lista): a lista só encolhe.
PENDENTES_ROTULO = (
    'G4-Equipe-Web', 'G4-Equipe-Mobile',
)   # (2 telas em 10/11/2026, depois da P4I: G1 e G2 (web e app) saíram; só a G4 ainda tem rótulo. 6 telas em 10/11/2026, depois da P4H: F1 a F5 (web e app) saíram; 16 telas depois da P4G: Main e H2 saíram (a H3 web e app já estavam limpas: o ' · DEMO' da H3 web só valia com D.demo). 18 telas depois da P4F: a E2 saiu (a E1 já estava limpa: o ramo ao vivo não tinha rótulo e a varredura a vigiava). 19 telas em 09/11/2026, depois da P4E: C1 e C3 saíram (a C2, a C4 web e app já nascem limpas). 21 depois da P4D: B1 e B2 saíram (a B3 já estava limpa). 23 depois da P4C: A1 e A2 saíram (e a A3, a A4 e a A5 já nascem limpas). Eram 25 depois da P4B: a moldura e o chip do clima já saíram; A3, B3, C2, E1, G3 e H3 já estão limpas e a varredura as vigia. A E2 mostra «snapshot 26/09/2026 10:12»
#  no 1º meio segundo, antes de a leitura do replay entrar: a varredura a 900 ms pega, a sonda a 1,5 s não pegava)
FORA_ATE_FASE_8 = ('Manual-Capitao-IA',)
# Telas cuja leitura ainda não anda sem o replay congelado (a C3 vira alerta vivo na Fase 4): a mesma regra, a lista só encolhe.
PENDENTES_MUDA = ()   # (a C3 saiu na P4E: virou alerta vivo)
MUDA_SEM_FIXO = ('Main', 'A1-Ponte-Web', 'A2-Ponte-Mobile', 'A4-Sensores-Web', 'A5-Sensores-Mobile', 'B1-Carta-Web', 'B2-Carta-Mobile', 'C1-Leme-Web', 'C2-Leme-Mobile', 'C3-Leme-Alerta', 'C4-Checklist-Web', 'C4-Checklist-Mobile', 'E1-Navegando-Gatilhos', 'G2-Abastecimento-Web', 'G2-Abastecimento-Mobile')
# Sem faixa global de alerta: o SOS (nunca muda de lugar), o Manual (apresentação) e a C3 (a própria tela do alerta)
SEM_FAIXA = ('S1-SOS-Web', 'S2-SOS-Mobile', 'Manual-Capitao-IA', 'C3-Leme-Alerta')
MUT_ARQ = {}   # {arquivo: [(trecho, no lugar)]}: serve o arquivo do site com o defeito plantado (as mutações dos testes da P4B; nunca no uso normal)
SESSAO = "(() => { const n = Date.now(); localStorage.setItem('capitao.sessao.v1', JSON.stringify({ u: 'lucas', em: n, exp: n + 3600e3 })); })()"
# páginas fora das TELAS do sw.js: nome → (endereço, com sessão). O login com sessão redireciona; a lista precisa de ?v=lista.
PAGINAS = {'login': ('login.html', False), 'index': ('index.html?v=lista', True), 'dados': ('dados.html', True)}
MEDE_LOGIN = """() => { const q = (s) => { const e = document.querySelector(s); return e ? e.getBoundingClientRect().bottom : null; };
  const a = document.querySelector('a[href*="SOS-"]'), r = a ? a.getBoundingClientRect() : null;
  return { go: q('#go'), credito: q('.credito'), sos: a ? { href: a.getAttribute('href'), aria: a.getAttribute('aria-label'), txt: a.textContent.trim(), w: r.width, h: r.height, topo: r.top, fim: r.bottom, esq: r.left, dir: r.right,
    cor: getComputedStyle(a).backgroundColor, vw: document.documentElement.clientWidth } : null }; }"""
# Dados do aparelho: o SOS do topo à vista (≥ 44 px) no alto e depois de rolar até o fim; fundo e tema.
MEDE_DADOS = """() => {
  const de = document.documentElement, a = document.querySelector('header a[href*="SOS-"]');
  const ve = () => { if (!a) return false; const r = a.getBoundingClientRect();
    return r.width >= 43.5 && r.height >= 43.5 && r.top >= 0 && r.bottom <= innerHeight + 0.5 && r.left >= 0 && r.right <= de.clientWidth + 0.5; };
  const topo = ve(); window.scrollTo(0, de.scrollHeight); const fim = ve(); window.scrollTo(0, 0);
  return { sos: a ? a.getAttribute('href') : null, texto: a ? a.textContent.trim() : '', topo, fim, tema: de.getAttribute('data-capitao-tema'),
           fundo: getComputedStyle(document.body).backgroundColor, titulo: document.title, lista: (document.getElementById('lista') || {}).textContent || '' };
}"""
FUNDO = {'escuro': 'rgb(5, 8, 22)', 'claro': 'rgb(243, 246, 252)'}
# Texto escrito no código da tela que casa com rx, no texto visível, no title, no aria-label e no alt. O que vem do
# capitao-dados.js fica de fora até o gerador trocar os rótulos (títulos, fontes e regraAbast já sem "(DEMO)" desde o C2; as
# notas e os textos dos guias nos commits seguintes do gerador; o mmsiNota saiu na 1b): o casamento é do D
# quando ele e os 10 caracteres antes (ou os 10 depois) estão num texto do D. Casamento sem 10 caracteres de nenhum lado (o chip
# "PRONTO · DEMO") conta como do código.
FORA_DO_D = r"""((rx) => {
  const dTxt = [], anda = (v) => { if (typeof v === 'string') dTxt.push(v.toLowerCase()); else if (v && typeof v === 'object') Object.keys(v).forEach((k) => anda(v[k])); };
  anda(window.CapitaoDados || {});
  const doD = (s) => !!s && dTxt.some((x) => x.indexOf(s.toLowerCase()) >= 0);
  const textos = document.body ? document.body.innerText.split('\n') : [];
  document.querySelectorAll('[title],[aria-label],[alt]').forEach((e) => ['title', 'aria-label', 'alt'].forEach((a) => { const v = e.getAttribute(a); if (v) textos.push(v); }));
  const achados = [], A = 10;
  textos.forEach((l) => {
    for (let m = rx.exec(l); m; m = rx.exec(l)) {
      const i = m.index, f = i + m[0].length;
      if (!doD(i >= A ? l.slice(i - A, f) : '') && !doD(l.length - f >= A ? l.slice(i, f + A) : '')) { achados.push(l.trim().slice(0, 140)); break; }
    }
    rx.lastIndex = 0;
  });
  return achados;
})"""
# Selo (decisão b): DEMO, Demo, demonstração ou fictício.
SELO_TEXTO = FORA_DO_D + r"""(/\bDEMO\b|\bDemo\b|[Dd]emonstra[çc]|DEMONSTRA[ÇC]|[Ff]ict[ií]ci|FICT[IÍ]CI/g)"""
# Afirmar que é real (decisão 5, trava §2.6 do PROMPT): a AFIRMA_REAL do contrato, com "real" no singular ("Última leitura real"
# da E1 passava com o "reais?" de lá).
AFIRMA_TEXTO = FORA_DO_D + r"""(/(?:^|[^A-Za-zÀ-ÿ])(?:dados?|leituras?|barco|embarca[çc][ãa]o|navega[çc][ãa]o)\s+(?:\S+\s+){0,2}(?:rea(?:l|is)|verdadeir[A-Za-zÀ-ÿ]*|oficia(?:l|is))(?![A-Za-zÀ-ÿ])/gi)"""
CHECA = """() => {
  const de = document.documentElement, root = document.getElementById('dc-root');
  const lateral = Math.max(de.scrollWidth, document.body ? document.body.scrollWidth : 0) - de.clientWidth;
  const deform = [];
  document.querySelectorAll('img').forEach((im) => {
    const r = im.getBoundingClientRect(); if (!im.naturalWidth || r.width < 2 || r.height < 2) return;
    const fit = getComputedStyle(im).objectFit;
    if (fit === 'contain' || fit === 'cover') return;
    const a = im.naturalWidth / im.naturalHeight, b = r.width / r.height;
    if (Math.abs(a - b) / a > 0.04) deform.push((im.getAttribute('src') || '') + ' ' + a.toFixed(2) + '→' + b.toFixed(2));
  });
  document.querySelectorAll('svg').forEach((s) => {
    const r = s.getBoundingClientRect(), vb = s.viewBox && s.viewBox.baseVal;
    if (!vb || !vb.width || r.width < 4 || r.height < 4) return;
    const par = s.getAttribute('preserveAspectRatio');
    if (par && par !== 'none') return;
    const a = vb.width / vb.height, b = r.width / r.height;
    if (par === 'none' && Math.abs(a - b) / a > 0.04) deform.push('svg ' + a.toFixed(2) + '→' + b.toFixed(2));
  });
  const prancheta = !!(root && root.querySelector('[style*="width: 1440px"],[style*="width: 390px"],[style*="width: 2380px"],deck-stage'));
  const rodape = [...document.querySelectorAll('capitao-rodape a')].map((a) => a.getAttribute('href'));
  const rodapeTxt = [...document.querySelectorAll('capitao-rodape')].map((e) => e.textContent).join(' ');
  // Caixas visíveis com a borda violeta do antigo selo (a cor do tema em --cap-violeta-rgb; no escuro, o fallback): o texto de cada uma.
  const vr = (getComputedStyle(de).getPropertyValue('--cap-violeta-rgb').trim() || '162,43,253').replace(/\\s/g, '');
  const selos = [...document.querySelectorAll('span,div,b,p')].filter((e) => {
    const q = e.getBoundingClientRect(); if (q.width < 1 || q.height < 1) return false;
    const cs = getComputedStyle(e), c = cs.borderTopColor.replace(/\\s/g, '');
    return parseFloat(cs.borderTopWidth) > 0 && cs.borderTopStyle !== 'none' && (c.indexOf('(' + vr + ',') >= 0 || c.indexOf('(' + vr + ')') >= 0);
  }).map((e) => e.textContent.trim());
  const S = (window.CapitaoDados || {}).snapshot || {};
  const ultima = S.quando ? ('ÚLTIMA LEITURA · ' + S.quando.slice(0, 5) + ' ' + (S.hora || '')).trim() : null;
  const seloTexto = """ + SELO_TEXTO + """, afirma = """ + AFIRMA_TEXTO + """;
  const fx = document.getElementById('capitao-faixa-alertas');
  return { lateral: lateral, deform: deform, prancheta: prancheta, titulo: document.title, rodape: rodape, rodapeTxt: rodapeTxt, selos: selos, ultima: ultima, seloTexto: seloTexto, afirma: afirma,
           replay: typeof window.CapitaoReplay, alertas: typeof window.CapitaoAlertas, faixa: fx ? (fx.hidden ? 'oculta' : 'visivel') : null };
}"""
# SOS sem o registro gerado (trava §2.1; C4): o embarcacao.registro e "REG." no texto visível e nos atributos de S1/S2.
# Revisão do C4: o roteiro MAYDAY (<sc-if value="{{mayday}}">) e os passos de cada cartão (<sc-if value="{{p.open}}">) só existem
# no DOM depois do toque, e o roteiro é o texto lido no rádio, onde uma identificação gerada entraria primeiro. TEXTOS_SOS lê a tela
# fechada, com o roteiro aberto e com cada cartão aberto (um de cada vez, que a tela só abre um), e devolve a tela ao estado
# inicial; sem abrir o roteiro e todos os cartões, a conferência não vale. A 1b reaproveita os textos (MMSI, coordenada, modelo, base).
# Revisão 2 do C4: e o fabricante, o modelo, a marca, o rotulo, a motorizacao e o motor (confere.barco_sos, a regra do gerador
# sobre o protocolos, tirada do próprio D). Sem os números (ano, dimensões, tanques): a tela do SOS mostra o clima real, e uma
# ondulação de "1,1 m" seria o calado; no protocolos, que é só texto gerado, o gerador confere os números também. A base entrou na 1b,
# que a tirou do cabeçalho da S1 (CONTRATO §1.2).
# Revisão 3 do C4: D.simulacao vai junto (TEXTOS_SOS devolve `simulacao`). Na simulação, o D tem de trazer os cinco campos da
# embarcação (confere.falta_barco_sos); no modo real (simulacao false, CONTRATO §4.2), None é SEM DADOS e a conferência vale só
# para o campo que existe, como a_embarcacao e a_registro no gerador.
TELAS_SOS = ('S1-SOS-Web', 'S2-SOS-Mobile')
TEXTOS_SOS = r"""async () => {
  // __dadosCru: o contador de leituras do sos.py guarda o D cru aqui (a leitura do próprio teste não conta como a do SOS)
  const D = window.__dadosCru || window.CapitaoDados || {}, E = D.embarcacao || {}, S0 = D.snapshot || {}, barco = {}; ['nome', 'registro', 'fabricante', 'modelo', 'rotulo', 'motorizacao', 'base'].forEach((k) => { if (typeof E[k] === 'string') barco[k] = E[k]; });
  const textos = [];
  const le = () => {
    textos.push(document.body ? document.body.innerText : '');
    // O chip do clima (<capitao-hora-clima>, só na S1) é a previsão real do Open-Meteo na posição de referência, com o teste próprio
    // (teste_clima, F13): os title dele ("Previsão de hoje em Balneário Camboriú…", "…SEM DADOS…") e o link do windy.com (coordenada da
    // referência) não são o dado do barco e ficam de fora desta leitura. Texto visível e atributos do resto da tela entram.
    document.querySelectorAll('[title],[aria-label],[alt],[href]').forEach((e) => { if (e.closest('capitao-hora-clima')) return; ['title', 'aria-label', 'alt', 'href'].forEach((a) => { const v = e.getAttribute(a); if (v) textos.push(v); }); });
  };
  const ate = async (cond) => { for (let i = 0; i < 50 && !cond(); i++) await new Promise((ok) => requestAnimationFrame(() => setTimeout(ok, 30))); return cond(); };
  // o botão do MAYDAY (o da sirene também tem aria-pressed, mas tem aria-label e não diz MAYDAY)
  const may = () => [...document.querySelectorAll('button[aria-pressed]')].find((b) => !b.hasAttribute('aria-label') && /MAYDAY|ROTEIRO/.test(b.textContent));
  const cartoes = () => [...document.querySelectorAll('button[aria-expanded]')];
  le();
  let roteiro = false, abertos = 0;
  const m0 = may();
  if (m0 && m0.getAttribute('aria-pressed') !== 'true') m0.click();
  if (await ate(() => may() && may().getAttribute('aria-pressed') === 'true' && /ROTEIRO · CANAL 16/.test(document.body.innerText))) { roteiro = true; le(); }
  const n = cartoes().length;
  for (let i = 0; i < n; i++) {
    const b = cartoes()[i];
    if (!b) break;
    if (b.getAttribute('aria-expanded') !== 'true') b.click();
    if (await ate(() => cartoes()[i] && cartoes()[i].getAttribute('aria-expanded') === 'true')) { abertos++; le(); }
    const c = cartoes()[i];
    if (c && c.getAttribute('aria-expanded') === 'true') c.click();
    await ate(() => !cartoes().some((x) => x.getAttribute('aria-expanded') === 'true'));
  }
  const m1 = may();
  if (m1 && m1.getAttribute('aria-pressed') === 'true') m1.click();
  const inicial = await ate(() => may() && may().getAttribute('aria-pressed') !== 'true' && !cartoes().some((x) => x.getAttribute('aria-expanded') === 'true'));
  return { barco: barco, simulacao: D.simulacao, texto: textos.join('\n'), roteiro: roteiro, cartoes: n, abertos: abertos, inicial: inicial,
           equip: (D.equipamentos || []).map((e) => ({ id: e.id, fabricante: e.fabricante, modelo: e.modelo })), snap: { local: S0.local, estado: S0.estado } };
}"""


def textos_sos(pg):
    """Texto visível e atributos de S1/S2 na tela fechada, com o roteiro MAYDAY aberto e com cada cartão aberto; e os problemas
    da própria leitura (roteiro ou cartão que não abriu, tela que não voltou ao estado inicial)."""
    r = pg.evaluate(TEXTOS_SOS)
    prob = []
    if not r['roteiro']: prob.append('a conferência não abriu o roteiro MAYDAY (botão CANAL 16 · MAYDAY)')
    if not r['cartoes'] or r['abertos'] != r['cartoes']:
        prob.append('a conferência abriu %d de %d cartões de protocolo' % (r['abertos'], r['cartoes']))
    if not r['inicial']: prob.append('a tela não voltou ao estado inicial depois da conferência (roteiro ou cartão aberto)')
    return r, prob


R_NOVE_DIGITOS = re.compile(r'\b\d{9}\b')
R_SOG_PROA = re.compile(r'\b(?:SOG|PROA|COG|ETA)\b[^\n]{0,12}\d', re.I)
R_ROTULO_SOS = re.compile(r'SEM DADOS|\bDEMO\b|A CONFERIR|A CONFIRMAR|[uú]ltimo fix', re.I)


def achados_texto_sos(txt, E, equip, snap, coord_aparelho=None):
    """O que o texto visível e os atributos de S1/S2 não podem ter (PROMPT §2.1 e a conferência da 1b; CONTRATO §1.3, §6.2): {regra: [achados]},
    cada regra vazia quando a tela está limpa. 9 dígitos (MMSI), coordenada (a R_COORD do gerador; com `coord_aparelho`, só ela é permitida: a do
    GPS do celular), snapshot.local e snapshot.estado, a palavra snapshot, SOG/PROA/COG/ETA com número, o registro e o resto do dado gerado da
    embarcação (confere.barco_sos com a base, sem os números: a tela mostra o clima real), fabricante e modelo de equipamento (o nome do próprio
    sistema, como «Seafire», é o id e fica) e os rótulos que o SOS nunca tem (SEM DADOS, DEMO, A CONFERIR, «último fix»)."""
    def com_contexto(rx, t):
        return [t[max(0, m.start() - 30):m.end() + 30].replace('\n', ' | ') for m in rx.finditer(t)]
    t_coord = txt.replace(coord_aparelho, ' ') if coord_aparelho else txt
    ntxt = confere.norm(txt)
    snap_val = [k for k, v in (snap or {}).items() if isinstance(v, str) and v.strip() and v.lower() in txt.lower()]
    barco = ['%s %r' % (c, t) for c, t, _ in confere.acha_barco(txt, E, confere.barco_sos(E, numeros=False))]
    if re.search(r'(?:^|[^A-Za-zÀ-ÿ])REG\.', txt): barco.append('"REG."')
    equipamentos = [x for e in (equip or []) for x in (e.get('fabricante'), e.get('modelo')) if x and confere.norm(x) != confere.norm(e.get('id', '')) and confere.norm(x) in ntxt]
    return {'9 dígitos (MMSI)': com_contexto(R_NOVE_DIGITOS, txt), 'coordenada': [m.group(0) for m in confere.R_COORD.finditer(t_coord)],
            'snapshot.local/.estado': snap_val, 'a palavra snapshot': ['snapshot'] if 'snapshot' in txt.lower() else [], 'SOG/PROA/COG/ETA com número': com_contexto(R_SOG_PROA, txt),
            'dado gerado da embarcação': barco, 'fabricante/modelo de equipamento': equipamentos, 'SEM DADOS/DEMO/A CONFERIR/último fix': com_contexto(R_ROTULO_SOS, txt)}


def problemas_barco_sos(pg):
    """S1/S2 (trava §2.1 e a conferência da 1b): nem "REG." nem dado gerado da embarcação além do nome (confere.barco_sos sem os números, com a
    base: registro, fabricante, modelo, marca, rotulo, motorizacao, motor e base), nem MMSI de 9 dígitos, coordenada, snapshot.local/.estado,
    "snapshot", SOG/PROA com número, fabricante ou modelo de equipamento, SEM DADOS/DEMO/A CONFERIR/«último fix», na tela fechada, no roteiro MAYDAY
    e nos passos de cada cartão (achados_texto_sos); na simulação, sem os campos da embarcação no D a conferência não vale; no modo real
    (D.simulacao false), o campo None é SEM DADOS e só o que existe se confere (confere.falta_barco_sos)."""
    r, prob = textos_sos(pg)
    E = r['barco']
    falta = confere.falta_barco_sos(E, r.get('simulacao'))
    if falta: prob.append('D sem embarcacao.%s: a conferência do dado da embarcação no SOS não vale' % ', '.join(falta))
    for regra, achados in achados_texto_sos(r['texto'], E, r['equip'], r['snap']).items():
        if achados: prob.append('SOS mostra %s: %s (trava §2.1: só o nome da embarcação e o protocolos)' % (regra, '; '.join(map(str, achados[:3]))))
    return prob


# F3 (eletrônicos): o número do MMSI é o do cadastro do app e a nota diz que no MAYDAY e no DSC vale o do rádio de bordo (1b; PROMPT §2.2,
# CONTRATO §1.2): o rótulo «MMSI (cadastro do app)» no lugar de «MMSI da embarcação (DSC)», nunca «MMSI SEM DADOS».
def problemas_f3_mmsi(pg):
    t = pg.evaluate("() => document.body.innerText")
    prob = []
    if 'MMSI (cadastro do app)' not in t: prob.append('F3 sem o rótulo «MMSI (cadastro do app)»')
    if 'No MAYDAY e no DSC: MMSI do rádio de bordo (etiqueta / Licença de Estação)' not in t: prob.append('F3 sem a nota «No MAYDAY e no DSC: MMSI do rádio de bordo (etiqueta / Licença de Estação)»')
    for ruim in ('MMSI SEM DADOS', 'MMSI da embarcação (DSC)'):
        if ruim in t: prob.append('F3 ainda diz «%s»' % ruim)
    return prob


# Equipamento de segurança (EPIRB e Seafire: seguranca no capitao-dados.js) só em Equipamentos, Leme e Documentos (CONTRATO-DADOS
# §1.4, C5). Na F1 e na E2: o modelo e o fabricante nunca no texto nem nos atributos; o fabricante nunca no link do chat (#q=); na
# F1, o VHF e o áudio abrem a pergunta deles no FAQ de eletrônicos (as palavras do equipamento). Na E2, a leitura passa por cada
# sistema e sintoma. Revisão do C5: na F1, nenhum cartão cortado e nenhuma pergunta de cartão numa chave de emergência; na F1 e na E2,
# o fabricante não se repete quando o modelo começa por ele.
TELAS_SEGURANCA = ('F1-FAQ-Hub', 'F1-FAQ-Hub-Web', 'E2-Navegando-Sintoma')
TEXTOS_SEGURANCA = r"""async (e2) => {
  const D = window.CapitaoDados || {}, EQ = D.equipamentos || [], P = ((D.faq || {}).eletronicos || {}).perguntas || [];
  const textos = [], chats = [];
  const dec = (v) => { try { return decodeURIComponent(v); } catch (x) { return v; } };
  const le = () => {
    textos.push(document.body ? document.body.innerText : '');
    document.querySelectorAll('[title],[aria-label],[alt],[href]').forEach((e) => ['title', 'aria-label', 'alt', 'href'].forEach((a) => {
      const v = e.getAttribute(a); if (!v) return; textos.push(a === 'href' ? dec(v) : v);
      if (a === 'href' && v.indexOf('#q=') !== -1) chats.push(dec(v.split('#q=')[1]));
    }));
  };
  const espera = () => new Promise((ok) => requestAnimationFrame(() => setTimeout(ok, 40)));
  le();
  if (e2) {
    const sis = () => [...document.querySelectorAll('button[aria-pressed][aria-label^="Sistema:"]')];
    for (let i = 0; i < sis().length; i++) {
      sis()[i].click(); await espera(); le();
      const sint = () => [...document.querySelectorAll('button[aria-pressed]:not([aria-label])')];
      for (let j = 0; j < sint().length; j++) { sint()[j].click(); await espera(); le(); }
    }
  }
  const cartoes = {}, cortados = [];
  document.querySelectorAll('a[href]').forEach((a) => {
    const n = (a.innerText || '').split('\n')[0].trim(), e = EQ.find((x) => x.nome === n); if (!e || cartoes[e.id]) return;
    cartoes[e.id] = a.getAttribute('href');
    // cartão cortado: o conteúdo passa da altura do cartão (overflow: hidden esconde a pergunta, a fonte, a ação ou a nota)
    if (a.scrollHeight - a.clientHeight > 1) cortados.push(e.id + ' (' + a.clientHeight + ' de ' + a.scrollHeight + ' px)');
  });
  // "Seakeeper Seakeeper 3": o fabricante seguido do modelo que já começa por ele
  const repetidos = EQ.filter((e) => e.fabricante && e.modelo && e.modelo.toLowerCase().indexOf(e.fabricante.toLowerCase()) === 0).map((e) => e.fabricante + ' ' + e.modelo);
  const un = [...document.querySelectorAll('a[href]')].find((a) => (a.innerText || '').split('\n')[0].trim() === 'Eletrônicos');
  return { seg: EQ.filter((e) => e.seguranca).map((e) => ({ id: e.id, fabricante: e.fabricante, modelo: e.modelo })), texto: textos.join('\n'), chats: chats,
           cartoes: cartoes, cortados: cortados, repetidos: repetidos, perguntas: P.map((p) => p.q), unico: un ? { href: un.getAttribute('href'), texto: un.innerText } : null };
}"""
# A pergunta de cada cartão da F1 ao chat (#q=) passada pelo cérebro (carregado na própria tela, que não o tem; commit: false).
CHAVES_CARTOES = r"""async (qs) => {
  if (!window.CapitaoBrain) await new Promise((ok, erro) => { const s = document.createElement('script'); s.src = './capitao-brain.js';
    s.onload = ok; s.onerror = () => erro(new Error('capitao-brain.js não carregou')); document.head.appendChild(s); });
  const B = window.CapitaoBrain, D = window.CapitaoDados || {}, out = {};
  // a base de conhecimento (o guia de cada cartão) carrega em segundo plano: sem ela, toda pergunta de guia cairia no SEM DADOS
  B.carregaBase();
  for (let i = 0; i < 60 && !B.buscaBase('como ligar o gerador', 1).length; i++) await new Promise((ok) => setTimeout(ok, 50));
  Object.keys(qs).forEach((id) => {
    const a = B.answer(qs[id], { platform: 'app', commit: false }), e = (D.equipamentos || []).find((x) => x.id === id) || {};
    const g = (D.guias || {})[e.guia];
    out[id] = { k: a.key, guia: g || '', cita: !!g && String(a.src || '').indexOf(g) !== -1 };
  });
  return out;
}"""
# Chaves que, a partir da Fase 3, deixam a conversa em modo emergência por 15 min (PROMPT §2.2): um toque de rotina no FAQ nunca
# cai nelas; o cartão do próprio equipamento de segurança dá a chave dele (EPIRB → epirb, Seafire → seafire).
CHAVES_EMERGENCIA = {'sos', 'oleo', 'canal16', 'epirb', 'seafire'}
# Revisão do C5: fora os de segurança, a pergunta do cartão cai numa resposta cuja fonte é o guia do próprio equipamento (o cartão
# diz "Fonte: <guia>"). O radar e o piloto caíam na resposta pronta dos eletrônicos e o guincho na da âncora, com a posição. Ficam de
# fora só as respostas prontas de antes do C5 que a Fase 3 reescreve (CONTRATO §6.6): dessalinizador, porão e sistema elétrico.
CARTAO_SEM_GUIA_ATE_FASE3 = {'dessalinizador', 'porao', 'eletrico'}


def problemas_seguranca(pg, tela):
    """F1 e E2 (CONTRATO-DADOS §1.4, C5): sem modelo nem fabricante do EPIRB e do Seafire na tela, sem o fabricante deles no link
    do chat e, na F1, o VHF e o áudio abrindo a pergunta certa, nenhum cartão cortado, nenhuma pergunta de cartão numa chave de
    emergência que não seja a do próprio equipamento de segurança e a resposta dos outros com o guia dele; sem "Seakeeper Seakeeper 3". Sem os dois equipamentos de
    segurança no D, a conferência não vale."""
    r = pg.evaluate(TEXTOS_SEGURANCA, tela.startswith('E2-'))
    prob = []
    if sorted(e['id'] for e in r['seg']) != ['epirb', 'seafire']:
        prob.append('D sem EPIRB e Seafire com seguranca: a conferência do equipamento de segurança não vale')
    for e in r['seg']:
        for n in confere.candidatos_modelo(e['fabricante'], e['modelo']):
            if next(confere.acha_nomes(r['texto'], n), None):
                prob.append('modelo do %s na tela (só em Equipamentos, Leme e Documentos, §1.4)' % e['id'])
                break
        # o fabricante também (§1.4: "fabricante e modelo trocam por nota"; trava 17), menos quando a marca é o próprio nome do
        # sistema, o id: o "Seafire" do protocolo e da resposta sos (a E2 mostra a sos nos sintomas de emergência)
        if confere.norm(e['fabricante']) != e['id'] and next(confere.acha_nomes(r['texto'], e['fabricante']), None):
            prob.append('fabricante do %s na tela (só em Equipamentos, Leme e Documentos, §1.4)' % e['id'])
        ruins = sorted({q for q in r['chats'] if next(confere.acha_nomes(q, e['fabricante']), None)})
        if ruins:
            prob.append('link do chat com o fabricante do %s: %s' % (e['id'], ruins[:2]))
    baixo = r['texto'].lower()
    rep = [x for x in r['repetidos'] if x.lower() in baixo]
    if rep:
        prob.append('fabricante repetido antes do modelo: %s' % rep)
    if tela.startswith('F1-'):
        # (P4H, PARIDADE F10: «cartão Eletrônicos único») plotters, áudio e VHF são UM cartão, «Eletrônicos», que abre o F3: os cartões do áudio e do VHF (que abriam a pergunta deles pelo #p=) saíram;
        # as perguntas do VHF e do Fusion ficam no F3 (a web as lista no próprio cartão)
        for i in ('eletronicos', 'audio', 'vhf'):
            if i in r['cartoes']: prob.append('cartão %s ainda existe na F1: plotters, áudio e VHF são o cartão único «Eletrônicos»' % i)
        un = r['unico']
        if not un or not re.fullmatch(r'F3-FAQ-Eletronicos(?:-Web)?\.dc\.html', un['href']): prob.append('o cartão «Eletrônicos» da F1 devia abrir o F3 (sem #p=): %r' % (un and un['href']))
        elif tela.endswith('-Web'):
            for alvo in ('VHF', 'Fusion'):
                q = [x for x in r['perguntas'] if alvo in x]
                if not q or not all(x in un['texto'] for x in q): prob.append('o cartão «Eletrônicos» da F1 não lista a pergunta de %s do FAQ de eletrônicos: %s' % (alvo, q))
        if r['cortados']:
            prob.append('cartão da F1 cortado: %s' % r['cortados'][:4])
        qs = {i: urllib.parse.unquote(h.split('#q=', 1)[1]) for i, h in r['cartoes'].items() if '#q=' in h}
        seg = {e['id'] for e in r['seg']}
        if not seg <= set(qs):
            prob.append('cartão de segurança sem pergunta ao chat: %s' % sorted(seg - set(qs)))
        try:
            chaves = pg.evaluate(CHAVES_CARTOES, qs)
        except Exception as x:
            chaves = None
            prob.append('cérebro não respondeu às perguntas dos cartões: %s' % str(x)[:160])
        for i, c in sorted((chaves or {}).items()):
            k = c['k']
            if (k != i) if i in seg else (k in CHAVES_EMERGENCIA):
                prob.append('cartão %s pergunta %r ao chat e cai na chave %s (%s)' % (
                    i, qs[i], k, 'esperado %s' % i if i in seg else 'emergência num toque de rotina'))
            elif i not in seg and i not in CARTAO_SEM_GUIA_ATE_FASE3 and not c['cita']:
                prob.append('cartão %s pergunta %r ao chat e a resposta (%s) não cita o guia dele (%s)' % (i, qs[i], k, c['guia']))
    return prob


# Validade do EPIRB e do Seafire (revisão do C7; CONTRATO-DADOS §1.4): só nas telas de Equipamentos, Leme e Documentos. As datas saem do D da
# própria tela: o `vence` das tarefas do equipamento com seguranca (e a que guarda a validade dele) e o do documento que a guarda (doc-epirb).
TELAS_COM_VALIDADE = ('B1-Carta-Web', 'B2-Carta-Mobile', 'C1-Leme-Web', 'C2-Leme-Mobile', 'G1-Documentos-Web', 'G1-Documentos-Mobile')
TELAS_COM_DATA = ('C1-Leme-Web', 'G1-Documentos-Web', 'G1-Documentos-Mobile')   # controle: mostram a data sempre (a C2 abre filtrada nas atrasadas)
TEXTOS_VALIDADE = r"""() => {
  const D = window.CapitaoDados;
  if (!D) return { semD: true };
  const seg = (D.equipamentos || []).filter((e) => e.seguranca), ids = seg.map((e) => e.id), val = seg.map((e) => e.validade).filter(Boolean);
  const datas = [];
  (D.agenda || []).forEach((t) => { if ((ids.indexOf(t.sistema) !== -1 || val.indexOf(t.id) !== -1) && t.vence) datas.push({ de: t.id, vence: t.vence }); });
  (D.documentos || []).forEach((x) => { if (val.indexOf(x.id) !== -1 && x.vence) datas.push({ de: x.id, vence: x.vence }); });
  const dec = (v) => { try { return decodeURIComponent(v); } catch (x) { return v; } };
  const textos = [document.body ? document.body.innerText : ''];
  document.querySelectorAll('[title],[aria-label],[alt],[href]').forEach((e) => ['title', 'aria-label', 'alt', 'href'].forEach((a) => {
    const v = e.getAttribute(a); if (v) textos.push(a === 'href' ? dec(v) : v);
  }));
  return { ids: ids, datas: datas, texto: textos.join('\n') };
}"""


def data_na_tela(texto, vence):
    """A data (dd/mm/aaaa) inteira no texto, ou a curta (dd/mm) depois de vence, venceu, validade ou vencimento. A curta sozinha não vale
    (a última inspeção cai no mesmo dd/mm um ano antes) e a seguida de "/" já é a inteira de outro ano."""
    return vence in texto or bool(re.search(r'(?:vence|venceu|validade|vencimento)\s*(?:em\s*)?' + re.escape(vence[:5]) + r'(?![\d/])', texto, re.I))


def problemas_validade(pg, tela):
    """Revisão do C7 (CONTRATO-DADOS §1.4): a validade do EPIRB e do Seafire fora de Equipamentos, Leme e Documentos, e o controle de que o
    detector enxerga a data onde ela pode estar. Tela sem o capitao-dados.js não tem o que mostrar."""
    r = pg.evaluate(TEXTOS_VALIDADE)
    if r.get('semD'):
        return []
    if sorted(r['ids']) != ['epirb', 'seafire'] or sorted(d['de'] for d in r['datas']) != ['doc-epirb', 'epirb-teste', 'seafire-inspecao']:
        return ['D sem EPIRB e Seafire com seguranca e as 3 datas deles (doc-epirb, epirb-teste, seafire-inspecao): a conferência da validade não vale']
    achadas = sorted(d['de'] + ' ' + d['vence'] for d in r['datas'] if data_na_tela(r['texto'], d['vence']))
    if tela in TELAS_COM_DATA:
        return [] if achadas else ['a conferência da validade não vale: nem a data do EPIRB nem a do Seafire aparece em %s (onde ela pode estar)' % tela]
    if tela in TELAS_COM_VALIDADE:
        return []
    return ['validade do EPIRB ou do Seafire na tela (só em Equipamentos, Leme e Documentos, §1.4): %s' % achadas] if achadas else []


# Selo de demonstração (decisão b da 1.1.0: nenhum): no rodapé, numa caixa de selo ou no texto do login e da lista.
SELO_RE = re.compile(r'DEMO|FICT[IÍ]CI|DEMONSTRA', re.I)


def problemas_selo(tela, r):
    """Selo que sobrou na tela (r = CHECA). Main e H2: nenhuma caixa de selo no cabeçalho (a origem é o selo ao vivo e o LED); SOS sem caixa."""
    prob = []
    if SELO_RE.search(r['rodapeTxt']): prob.append('selo no rodapé: %r' % r['rodapeTxt'][:120])
    ruins = [t for t in r['selos'] if SELO_RE.search(t) or 'SNAPSHOT' in t.upper()]
    if ruins: prob.append('caixa de selo: %s' % ruins[:3])
    if tela in ('Main', 'H2-Home-Mobile') and r['selos']:   # (P4G: a caixa «ÚLTIMA LEITURA» do cabeçalho saiu; a origem é o selo «AO VIVO · hh:mm:ss» e o LED, conferidos em teste_home_leitura)
        prob.append('caixa de selo no cabeçalho da Home %s (esperado nenhuma)' % r['selos'][:3])
    if tela in ('S1-SOS-Web', 'S2-SOS-Mobile') and r['selos']: prob.append('caixa de selo no SOS: %s' % r['selos'][:3])
    if r['seloTexto']: prob.append('selo no texto da tela (fora do capitao-dados.js): %s' % r['seloTexto'][:3])
    if r['afirma']: prob.append('a tela afirma que o dado é real (fora do capitao-dados.js): %s' % r['afirma'][:3])
    return prob


# Varredura de termos (P4B): o texto visível, o title, o aria-label, o placeholder e o alt de cada tela, pelas regex do §3 com a flag de cada uma. Python, sobre o
# texto lido na página (as mesmas fontes do cérebro, dos Workers e do cliente; a conferência dos casos é o testes/proibidos.py da Fase 7).
LE_TEXTOS = """() => { const o = [document.body.innerText];
  document.querySelectorAll('[title],[aria-label],[placeholder],[alt]').forEach((e) => ['title', 'aria-label', 'placeholder', 'alt'].forEach((a) => { const v = e.getAttribute(a); if (v) o.push(v); }));
  return o.join('\\n'); }"""
# «telefone … não cadastrado — abrir Equipe para cadastrar» é o texto do SOS da 1b (o contato sem número neste aparelho), não dado de bordo vazio: o SOS não se mexe na Fase 4.
# É a única exceção da varredura, só no SOS e só dessa frase; qualquer outro termo do §3 no SOS reprova.
EXCECAO_SOS_VAZIOS = re.compile(r'n[ãa]o cadastrad')


def achados_termos(tela, texto):
    """{regex: [trecho com contexto]} dos termos do §3 (VARREDURA) no texto, cada regex com a flag dela; vazio quando a tela está limpa."""
    out = {}
    for nome in VARREDURA:
        ms = [texto[max(0, m.start() - 25):m.end() + 25].replace('\n', ' | ') for m in TERMOS[nome].finditer(texto)]
        if tela in TELAS_SOS and nome == 'VAZIOS':
            ms = [x for x in ms if not EXCECAO_SOS_VAZIOS.search(x)]
        if ms:
            out[nome] = ms
    return out


# A faixa global de alerta (P4B, capitao-app.js; PROMPT «Faixa global de alerta»): o que a tela mostra e o que a API de alertas diz no mesmo instante
LE_FAIXA = """() => { const f = document.getElementById('capitao-faixa-alertas'), A = window.CapitaoAlertas, a = A && typeof A.ativos === 'function' ? A.ativos() : [];
  const art = [...document.querySelectorAll('#dc-root [style*="width: 1440px"],#dc-root [style*="width: 390px"],#dc-root [style*="width: 2380px"]')].find((c) => /px$/.test(c.style.width) && parseFloat(c.style.height) >= 600);
  const r = f ? f.getBoundingClientRect() : null, p = art ? art.getBoundingClientRect() : null, lk = f ? f.querySelector('a') : null;
  return { existe: !!f, oculta: f ? f.hidden : null, nivel: f ? f.getAttribute('data-nivel') : null, texto: f ? f.innerText : '', href: lk ? lk.getAttribute('href') : null,
    alerta: a[0] ? { id: a[0].id, texto: a[0].texto, nivel: a[0].nivel, detalhe: a[0].detalhe, hora: a[0].hora } : null, n: a.length, fim: r ? r.bottom : 0, alt: r ? r.height : 0, topoArt: p ? p.top : null,
    falas: window.__falas || 0, registro: Object.keys(localStorage).filter((k) => /^capitao\\.(diario|executado|tickets|tarefas)\\.v1$/.test(k)), replay: typeof window.CapitaoReplay }; }"""
ESPIA_FALA = "(() => { window.__falas = 0; try { const o = speechSynthesis.speak.bind(speechSynthesis); speechSynthesis.speak = function () { window.__falas++; return o.apply(this, arguments); }; } catch (e) {} })()"


def problemas_faixa(tela, fixo, f):
    """A faixa global de alerta (F05): em 60 s nenhuma (cruzeiro, sem alarme); em 105 s o AVISO do instante, e nunca no SOS, no Manual nem na C3."""
    prob = []
    if tela in SEM_FAIXA:
        if f['existe']: prob.append('%s tem a faixa de alerta (nunca no SOS, no Manual nem na C3)' % tela)
        return prob
    if fixo == '60':
        if f['existe'] and not f['oculta']: prob.append('faixa de alerta visível em t = 60 (cruzeiro: nenhum alarme): %r' % f['texto'][:80])
        return prob
    a = f['alerta']
    if not a or f['n'] < 1: return ['sem alarme no instante 105 s (a API de alertas devolveu %d): o teste da faixa não vale' % f['n']]
    if not f['existe'] or f['oculta']: return ['sem a faixa de alerta em t = 105 (o AVISO %r está aberto)' % a['texto']]
    if a['nivel'] != 'aviso' or f['nivel'] != 'aviso': prob.append('a faixa não é AVISO (crítico só com o cenário alarme-critico, desligado): %s / %s' % (a['nivel'], f['nivel']))
    if a['texto'] not in f['texto']: prob.append('a faixa não diz o alerta «%s»: %r' % (a['texto'], f['texto'][:120]))
    if 'desde ' + a['hora'] not in f['texto']: prob.append('a faixa não diz «desde %s»: %r' % (a['hora'], f['texto'][:120]))
    if 'ABRIR' not in f['texto']: prob.append('a faixa sem «ABRIR»: %r' % f['texto'][:120])
    if f['href'] != 'C3-Leme-Alerta.dc.html#alarme=' + a['id'] or a['detalhe'] != f['href']:
        prob.append('ABRIR leva a %r (esperado C3-Leme-Alerta.dc.html#alarme=%s)' % (f['href'], a['id']))
    if f['alt'] < 44: prob.append('a faixa tem %d px de altura (o toque pede 44)' % f['alt'])
    if f['topoArt'] is None or f['topoArt'] < f['fim'] - 0.5: prob.append('a faixa cobre a prancheta (a prancheta começa em %s, a faixa termina em %s)' % (f['topoArt'], f['fim']))
    if f['falas']: prob.append('a faixa falou (speechSynthesis.speak %d vez(es)): nunca fala sem gesto' % f['falas'])
    if f['registro']: prob.append('a faixa gravou no registro: %s' % f['registro'])
    return prob


# SOS ao alcance (P4B, revisão). App: a barra SOS da tela (capitao-sos-app) fica TODA à vista (≥ 95 % dentro da janela) ou, se não, o SOS fixo do canto está ligado (display flex) e dentro da janela.
# Com a faixa de alerta a 105 s a prancheta desce 64 px: na H2 (390×844 e 430×932) a barra sobrava 12 px na dobra, e o observador do SOS fixo contava 1 px como «à vista». Web: o fit() faz a prancheta
# caber inteira abaixo da faixa, então o SOS circular (capitao-sos-web) tem de estar dentro da janela e abaixo dela.
LE_SOS_ALCANCE = """() => { const el = document.querySelector('#dc-root capitao-sos-app a[href*="SOS-"], #dc-root capitao-sos-web a[href*="SOS-"]') || document.querySelector('#dc-root a[href*="SOS-"]');
  const fx = [...document.querySelectorAll('body > a')].find((a) => a.textContent.trim() === 'SOS' && a.style.position === 'fixed');
  const r = el ? el.getBoundingClientRect() : null, vh = window.innerHeight, vw = document.documentElement.clientWidth;
  const f = fx ? fx.getBoundingClientRect() : null, cs = fx ? getComputedStyle(fx) : null;
  const fe = document.getElementById('capitao-faixa-alertas'), fb = fe && !fe.hidden ? fe.getBoundingClientRect().bottom : 0;
  return { link: !!el, vis: r && r.height > 0 ? Math.max(0, Math.min(r.bottom, vh) - Math.max(r.top, 0)) / r.height : null, topo: r && r.top, fim: r && r.bottom, esq: r && r.left, dir: r && r.right, vw, vh, faixaFim: fb,
    fixo: fx ? cs.display : null, fixoDentro: !!f && f.width > 0 && f.top >= -0.5 && f.bottom <= vh + 0.5 && f.left >= -0.5 && f.right <= vw + 0.5, fixoHref: fx ? fx.getAttribute('href') : null,
    faixa: (() => { const e = document.getElementById('capitao-faixa-alertas'); return e && !e.hidden ? e.offsetHeight : 0; })() }; }"""


def problemas_sos_alcance(pg, tela):
    """App: a barra SOS da tela inteira à vista, ou o SOS fixo ligado e dentro da janela. Web: a prancheta cabe inteira (fit), então o SOS circular fica dentro da janela e abaixo da faixa de
    alerta. Nunca nas telas do SOS nem no Manual."""
    if tela in TELAS_SOS or tela.startswith('Manual-'): return []
    pg.wait_for_timeout(350)   # o observador de interseção responde um quadro depois do fit()
    r = pg.evaluate(LE_SOS_ALCANCE)
    if not r['link']: return ['a tela não tem o link do SOS (a[href*="SOS-"]): SOS em todas as telas']
    if not eh_app(tela):
        if r['esq'] < -0.5 or r['dir'] > r['vw'] + 0.5 or r['topo'] < r['faixaFim'] - 0.5 or r['fim'] > r['vh'] + 0.5:
            return ['o SOS da web fica fora da janela ou sob a faixa de alerta (de %.0f a %.0f na vertical e de %.0f a %.0f na horizontal, janela %d×%d, a faixa termina em %.0f)' % (r['topo'], r['fim'], r['esq'], r['dir'], r['vw'], r['vh'], r['faixaFim'])]
        return []
    if r['vis'] is not None and r['vis'] >= 0.95: return []
    if r['fixo'] != 'flex' or not r['fixoDentro']:
        return ['o SOS fica fora do alcance: a barra está %.0f %% à vista (de %.0f a %.0f numa janela de %d px, faixa de %d px) e o SOS fixo do canto está %s%s'
                % (100 * (r['vis'] or 0), r['topo'], r['fim'], r['vh'], r['faixa'], r['fixo'] or 'ausente', '' if r['fixoDentro'] or r['fixo'] != 'flex' else ' mas fora da janela')]
    return []


# Texto cortado em silêncio na moldura (P4B, revisão): na faixa de leitura, o estado e o local do quadro («AO LARGO DA ILHA DAS CABRAS, A CAMINHO DA BARRA SUL…») empurravam «HH:MM:SS · AO VIVO»
# para fora (reticências no fim do nó único) em 43 % do laço. Agora só o estado/local encolhe (com reticências E a dica com o texto inteiro) e a hora nunca; o resto da moldura não corta nada.
LE_CORTE = r"""() => { const out = [], raizes = [...document.querySelectorAll('capitao-faixa,capitao-cabecalho,capitao-topo-app')];
  const dentro = (e) => !!e.closest('capitao-theme-toggle');   // o anel do botão do tema passa 2 px do botão: não é texto
  for (const raiz of raizes) {
    const rt = raiz.tagName.toLowerCase();
    for (const e of [raiz, ...raiz.querySelectorAll('*')]) {
      if (dentro(e) || !(e.clientWidth > 0) || !(e.scrollWidth > e.clientWidth + 1)) continue;
      const txt = (e.innerText || '').replace(/\s+/g, ' ').trim(), tit = (e.getAttribute('title') || '').replace(/\s+/g, ' ').trim();
      const reticencias = getComputedStyle(e).textOverflow === 'ellipsis';
      if (!(reticencias && tit && tit === txt)) out.push(rt + ' › ' + e.tagName.toLowerCase() + (e.getAttribute('data-cpm') ? '[' + e.getAttribute('data-cpm') + ']' : '') + ' cortado (' + e.scrollWidth + ' px de conteúdo em ' + e.clientWidth + ')'
        + (reticencias ? ' com reticências e sem a dica do texto inteiro' : '') + ': «' + txt.slice(-70) + '»');
    }
  }
  const f = document.querySelector('capitao-faixa'), h = f ? f.querySelector('[data-cpm="hora"]') : null;
  if (f) {
    const rf = f.getBoundingClientRect(), rh = h ? h.getBoundingClientRect() : null, t = h ? h.innerText.trim() : '';
    if (!h || !/^\d\d:\d\d:\d\d · (AO VIVO|ÚLTIMA LEITURA)$/.test(t)) out.push('faixa › a hora «' + t + '» não está inteira num nó só dela («HH:MM:SS · AO VIVO»)');
    else if (rh.left < rf.left - 0.5 || rh.right > rf.right + 0.5) out.push('faixa › a hora «' + t + '» passa da borda da faixa (' + Math.round(rh.left) + ' a ' + Math.round(rh.right) + ' de ' + Math.round(rf.left) + ' a ' + Math.round(rf.right) + ')');
    const ini = [...f.querySelectorAll('a')].find((a) => /INÍCIO/.test(a.innerText)), ri = ini ? ini.getBoundingClientRect() : null;
    if (ri && (ri.right > rf.right + 0.5 || ri.left < rf.left - 0.5)) out.push('faixa › INÍCIO passa da borda da faixa');
  }
  return out; }"""


def problemas_corte(pg):
    return pg.evaluate(LE_CORTE)


def aplica_mut(ctx):
    """Serve o arquivo do site com o defeito plantado (MUT_ARQ) neste contexto; sem mutação, nada muda."""
    def para(trocas):
        def trata(route):
            r = route.fetch()
            corpo = r.text()
            for velho, novo in trocas:
                corpo = corpo.replace(velho, novo, 1)
            route.fulfill(response=r, body=corpo)
        return trata
    for arq, trocas in MUT_ARQ.items():
        ctx.route('**/' + arq, para(trocas))


def roda_tela(b, tela, tema, w, h, fixo='60', fotos=False):
    """Uma tela num tema e num tamanho, com o replay congelado em `fixo` s: erro de script, rolagem lateral, imagem deformada, prancheta, selo, SOS, validade,
    typeof CapitaoReplay, a faixa de alerta e a varredura dos termos do §3. Devolve (problemas, quantos termos do §3 a tela mostra)."""
    movel = eh_app(tela)  # celular, inclusive deitado (844×390): toque + UA móvel
    ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None,
                        is_mobile=movel, has_touch=movel, service_workers='block')
    ctx.add_init_script(SESSAO + ";localStorage.setItem('capitao.tema.v1', '" + tema + "');localStorage.setItem('capitao.plataforma.v1', '" + ('app' if movel else 'web') + "');"
                        "try { localStorage.setItem('capitao.replay.fixo', '" + fixo + "'); } catch (e) {}")
    ctx.add_init_script(ESPIA_FALA)
    aplica_mut(ctx)
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
    pg.on('console', lambda m: erros.append('console: ' + m.text[:300]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    pg.goto(BASE + tela + '.dc.html', wait_until='load')
    try:
        pg.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
    except Exception:
        erros.append('prancheta não desenhou em 15 s')
    pg.wait_for_timeout(900)
    r = pg.evaluate(CHECA)
    url = pg.url
    prob = []
    if erros: prob += erros
    if r['lateral'] > 1: prob.append('rolagem lateral de %d px' % r['lateral'])
    if r['deform']: prob.append('deformado: ' + '; '.join(r['deform'][:4]))
    if not r['prancheta']: prob.append('prancheta ausente')
    if not url.split('#')[0].endswith(tela + '.dc.html'): prob.append('redirecionou para ' + url)
    if tela in ('Main', 'H2-Home-Mobile') and 'dados.html' not in r['rodape']:
        prob.append('rodapé sem o link dos Dados do aparelho: %s' % r['rodape'])
    # o Manual (apresentação) ainda descreve a 1.0.9, com os selos dela: é reescrito na Fase 8, que tira esta exceção
    if not tela.startswith('Manual-'): prob += problemas_selo(tela, r)
    if tela in TELAS_SOS: prob += problemas_barco_sos(pg)
    if tela.startswith('F3-FAQ-Eletronicos'): prob += problemas_f3_mmsi(pg)
    if tela in TELAS_SEGURANCA: prob += problemas_seguranca(pg, tela)
    if not tela.startswith('Manual-'): prob += problemas_validade(pg, tela)
    # P4B: o replay carregou (o filtro de «Failed to load resource» esconde o script ausente) e o SOS não o carregou
    if tela in TELAS_SOS:
        if r['replay'] != 'undefined': prob.append('o SOS carregou o CapitaoReplay (typeof %s): ele nunca lê a reprodução' % r['replay'])
    elif r['replay'] != 'object': prob.append('typeof CapitaoReplay = %s (esperado object)' % r['replay'])
    prob += problemas_faixa(tela, fixo, pg.evaluate(LE_FAIXA))
    prob += problemas_corte(pg)
    prob += problemas_sos_alcance(pg, tela)
    ach = achados_termos(tela, pg.evaluate(LE_TEXTOS))
    n_ach = sum(len(v) for v in ach.values())
    if ach and tela not in PENDENTES_ROTULO and tela not in FORA_ATE_FASE_8:
        prob.append('termo do §3 no texto da tela em t = %s (%s): %s' % (fixo, ' · '.join('%s %d' % (k, len(v)) for k, v in ach.items()), '; '.join(x for v in ach.values() for x in v[:2])[:300]))
    if fotos:
        pg.screenshot(path=os.path.join(SAIDA, '%s_%s_%dx%d%s.png' % (tela, tema, w, h, '' if fixo == '60' else '_' + fixo)))
    ctx.close()
    return prob, n_ach


# A passada a 105 s (a janela do alarme, só AVISO): 2 tamanhos no tema escuro e o menor no claro, onde um número longo ou a faixa de alerta podem puxar rolagem lateral
def tamanhos_105(tela):
    t = [(360, 640), (844, 390)] if eh_app(tela) else [(1024, 768), (1440, 900)]
    r = [('escuro', t[0]), ('escuro', t[1]), ('claro', t[0])]
    if eh_app(tela): r += [('escuro', (390, 844)), ('escuro', (430, 932))]   # as duas telas altas, onde a faixa empurra a barra SOS para a dobra (P4B, revisão)
    return r


def main():
    if '--so-p4i' in sys.argv or '--mutantes-p4i' in sys.argv:   # só as conferências da P4I (e, com --mutantes-p4i, os defeitos plantados delas)
        with sync_playwright() as p:
            b = p.chromium.launch(channel='msedge', headless=True)
            t0, falhas = time.time(), []
            if '--mutantes-p4i' in sys.argv:
                falhas = mutantes_p4i(b)
            else:
                for nome, prob in p4i_conferencias(b, [a for a in sys.argv[1:] if a in TELAS_P4I] or list(TELAS_P4I)):
                    print('FALHA' if prob else 'ok   ', nome, ' | '.join(prob[:6]) if prob else '')
                    if prob: falhas.append(nome)
            b.close()
        print('%d falhas · %.0f s' % (len(falhas), time.time() - t0))
        sys.exit(1 if falhas else 0)
    if '--so-p4h' in sys.argv or '--mutantes-p4h' in sys.argv:   # só as conferências da P4H (e, com --mutantes-p4h, os defeitos plantados delas)
        with sync_playwright() as p:
            b = p.chromium.launch(channel='msedge', headless=True)
            t0, falhas = time.time(), []
            if '--mutantes-p4h' in sys.argv:
                falhas = mutantes_p4h(b)
            else:
                for nome, prob in p4h_conferencias(b, [a for a in sys.argv[1:] if a in TELAS_P4H] or list(TELAS_P4H)):
                    print('FALHA' if prob else 'ok   ', nome, ' | '.join(prob[:6]) if prob else '')
                    if prob: falhas.append(nome)
            b.close()
        print('%d falhas · %.0f s' % (len(falhas), time.time() - t0))
        sys.exit(1 if falhas else 0)
    if '--so-p4g' in sys.argv or '--mutantes-p4g' in sys.argv:   # só as conferências da P4G (e, com --mutantes-p4g, os defeitos plantados delas)
        with sync_playwright() as p:
            b = p.chromium.launch(channel='msedge', headless=True)
            t0, falhas = time.time(), []
            if '--mutantes-p4g' in sys.argv:
                falhas = mutantes_p4g(b)
            else:
                for nome, prob in p4g_conferencias(b, [a for a in sys.argv[1:] if a in TELAS_P4G] or list(TELAS_P4G)):
                    print('FALHA' if prob else 'ok   ', nome, ' | '.join(prob[:6]) if prob else '')
                    if prob: falhas.append(nome)
            b.close()
        print('%d falhas · %.0f s' % (len(falhas), time.time() - t0))
        sys.exit(1 if falhas else 0)
    if '--so-p4f' in sys.argv or '--mutantes-p4f' in sys.argv:   # só as conferências da P4F (e, com --mutantes-p4f, os defeitos plantados delas)
        with sync_playwright() as p:
            b = p.chromium.launch(channel='msedge', headless=True)
            t0, falhas = time.time(), []
            if '--mutantes-p4f' in sys.argv:
                falhas = mutantes_p4f(b)
            else:
                for nome, prob in p4f_conferencias(b, [a for a in sys.argv[1:] if a in TELAS_P4F] or list(TELAS_P4F)):
                    print('FALHA' if prob else 'ok   ', nome, ' | '.join(prob[:6]) if prob else '')
                    if prob: falhas.append(nome)
            b.close()
        print('%d falhas · %.0f s' % (len(falhas), time.time() - t0))
        sys.exit(1 if falhas else 0)
    if '--so-p4e' in sys.argv or '--mutantes-p4e' in sys.argv:   # só as conferências da P4E (e, com --mutantes-p4e, os defeitos plantados delas)
        with sync_playwright() as p:
            b = p.chromium.launch(channel='msedge', headless=True)
            t0, falhas = time.time(), []
            if '--mutantes-p4e' in sys.argv:
                falhas = mutantes_p4e(b)
            else:
                for nome, prob in p4e_conferencias(b, list(TELAS_P4E)):
                    print('FALHA' if prob else 'ok   ', nome, ' | '.join(prob[:6]) if prob else '')
                    if prob: falhas.append(nome)
            b.close()
        print('%d falhas · %.0f s' % (len(falhas), time.time() - t0))
        sys.exit(1 if falhas else 0)
    if '--so-p4d' in sys.argv or '--mutantes-p4d' in sys.argv:   # só as conferências da P4D (e, com --mutantes-p4d, os defeitos plantados delas)
        with sync_playwright() as p:
            b = p.chromium.launch(channel='msedge', headless=True)
            t0, falhas = time.time(), []
            if '--mutantes-p4d' in sys.argv:
                falhas = mutantes_p4d(b)
            else:
                for nome, prob in p4d_conferencias(b, list(TELAS_P4D)):
                    print('FALHA' if prob else 'ok   ', nome, ' | '.join(prob[:6]) if prob else '')
                    if prob: falhas.append(nome)
            b.close()
        print('%d falhas · %.0f s' % (len(falhas), time.time() - t0))
        sys.exit(1 if falhas else 0)
    if '--so-p4c' in sys.argv or '--mutantes-p4c' in sys.argv:   # só as conferências da P4C (e, com --mutantes-p4c, os defeitos plantados delas)
        with sync_playwright() as p:
            b = p.chromium.launch(channel='msedge', headless=True)
            t0, falhas = time.time(), []
            if '--mutantes-p4c' in sys.argv:
                falhas = mutantes_p4c(b)
            else:
                for nome, prob in p4c_conferencias(b, list(TELAS_P4C)):
                    print('FALHA' if prob else 'ok   ', nome, ' | '.join(prob[:6]) if prob else '')
                    if prob: falhas.append(nome)
            b.close()
        print('%d falhas · %.0f s' % (len(falhas), time.time() - t0))
        sys.exit(1 if falhas else 0)
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    fotos = '--fotos' in sys.argv
    offline = '--offline' in sys.argv or '--so-offline' in sys.argv
    so_offline = '--so-offline' in sys.argv  # pula a matriz, só o teste offline
    lista = [a for a in args if a not in PAGINAS] if args else telas()
    paginas = [a for a in args if a in PAGINAS] if args else list(PAGINAS)
    if fotos:
        os.makedirs(SAIDA, exist_ok=True)
    falhas, total = [], 0
    t0 = time.time()
    with sync_playwright() as p:
        b = p.chromium.launch(channel='msedge', headless=True)
        ach_total = {}   # tela → quantos termos do §3 ela mostrou em todas as rodadas (os instantes 60 s e 105 s): a lista PENDENTES_ROTULO só encolhe
        for tema in (() if so_offline else ('escuro', 'claro')):
            for tela in lista:
                for (w, h) in (APP if eh_app(tela) else WEB):
                    total += 1
                    prob, n_ach = roda_tela(b, tela, tema, w, h, '60', fotos)
                    ach_total[tela] = ach_total.get(tela, 0) + n_ach
                    if prob:
                        falhas.append({'tela': tela, 'tema': tema, 'tam': '%dx%d' % (w, h), 'prob': prob})
                        print('FALHA', tela, tema, '%dx%d' % (w, h), ' | '.join(prob))
            for nome in paginas:
                end, com_sessao = PAGINAS[nome]
                for (w, h) in WEB + APP:
                    total += 1
                    movel = (w, h) in APP
                    ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None,
                                        is_mobile=movel, has_touch=movel, service_workers='block')
                    ctx.add_init_script((SESSAO + ';' if com_sessao else '') + "localStorage.setItem('capitao.tema.v1', '" + tema + "');")
                    aplica_mut(ctx)
                    pg = ctx.new_page()
                    erros = []
                    pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
                    pg.on('console', lambda m: erros.append('console: ' + m.text[:300]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
                    pg.goto(BASE + end, wait_until='load')
                    pg.wait_for_timeout(500)
                    r = pg.evaluate(CHECA)
                    prob = list(erros)
                    if r['lateral'] > 1: prob.append('rolagem lateral de %d px' % r['lateral'])
                    if r['deform']: prob.append('deformado: ' + '; '.join(r['deform'][:4]))
                    if not pg.url.split('#')[0].endswith(end): prob.append('redirecionou para ' + pg.url)
                    prob += problemas_selo(nome, r)
                    ach = achados_termos(nome, pg.evaluate(LE_TEXTOS))   # P4B: a mesma varredura do §3 (a página não lê o replay: um instante só)
                    if ach: prob.append('termo do §3 no texto da página (%s): %s' % (' · '.join('%s %d' % (k, len(v)) for k, v in ach.items()), '; '.join(x for v in ach.values() for x in v[:2])[:300]))
                    # o texto da prévia do link (WhatsApp, busca): meta description, og: e twitter:, que o innerText não lê
                    metas = pg.evaluate("""() => [...document.querySelectorAll('meta[name="description"],meta[property^="og:"],meta[name^="twitter:"]')]
  .map((m) => (m.getAttribute('name') || m.getAttribute('property')) + ': ' + (m.getAttribute('content') || ''))""")
                    ruins = [m for m in metas if SELO_RE.search(m)]
                    if ruins: prob.append('selo na meta da página: %s' % ruins[:3])
                    if nome in ('login', 'index'):
                        corpo = pg.evaluate("() => ({ t: document.body.innerText, demo: document.querySelectorAll('.demo').length })")
                        if SELO_RE.search(corpo['t']) or corpo['demo']: prob.append('linha de selo na página: %r' % (SELO_RE.findall(corpo['t'])[:3],))
                    if nome == 'login':
                        m = pg.evaluate(MEDE_LOGIN)
                        if h >= 640 and (m['go'] is None or m['go'] > h): prob.append('ENTRAR fora da 1ª tela (borda %s > %d)' % (m['go'], h))
                        if h >= 844 and (m['credito'] is None or m['credito'] > h): prob.append('crédito cortado (borda %s > %d)' % (m['credito'], h))
                        prob += problemas_login_sos(m['sos'], movel, h)
                    if nome == 'index' and 'Alerta crítico' not in pg.evaluate("() => document.body.innerText"):
                        prob.append('a lista não tem a linha «Alerta crítico» (C3): o «Modelo de alerta crítico» saiu na Fase 4')
                    if nome == 'dados':
                        m = pg.evaluate(MEDE_DADOS)
                        esperado = 'S2-SOS-Mobile.dc.html' if movel else 'S1-SOS-Web.dc.html'
                        if m['sos'] != esperado or m['texto'] != 'SOS': prob.append('SOS do topo %r %r (esperado %s)' % (m['sos'], m['texto'], esperado))
                        if not m['topo']: prob.append('SOS fora da 1ª tela')
                        if not m['fim']: prob.append('SOS some ao rolar até o fim')
                        if m['tema'] != tema or m['fundo'] != FUNDO[tema]: prob.append('tema %s com fundo %s (esperado %s)' % (m['tema'], m['fundo'], FUNDO[tema]))
                        if m['titulo'] != 'Dados do aparelho · Capitão IA': prob.append('título %r' % m['titulo'])
                        if 'lendo' in m['lista'] or not m['lista'].strip(): prob.append('lista do aparelho não montou: %r' % m['lista'][:80])
                    if fotos:
                        pg.screenshot(path=os.path.join(SAIDA, '%s_%s_%dx%d.png' % (nome, tema, w, h)))
                    if prob:
                        falhas.append({'tela': nome, 'tema': tema, 'tam': '%dx%d' % (w, h), 'prob': prob})
                        print('FALHA', nome, tema, '%dx%d' % (w, h), ' | '.join(prob))
                    ctx.close()
        if not so_offline:
            for tela in lista:   # a passada a 105 s: a janela do alarme (só AVISO), com a faixa de alerta
                for tema, (w, h) in tamanhos_105(tela):
                    total += 1
                    prob, n_ach = roda_tela(b, tela, tema, w, h, '105', fotos)
                    ach_total[tela] = ach_total.get(tela, 0) + n_ach
                    if prob:
                        falhas.append({'tela': tela, 'tema': tema + ' · t = 105 s', 'tam': '%dx%d' % (w, h), 'prob': prob})
                        print('FALHA', tela, tema, '%dx%d' % (w, h), 't = 105 s', ' | '.join(prob))
            for tela in [t for t in lista if t in PENDENTES_ROTULO and ach_total.get(t, 0) == 0]:   # a lista só encolhe
                total += 1
                falhas.append({'tela': tela, 'tema': 'PENDENTES_ROTULO', 'prob': ['a tela não tem termo do §3 em t = 60 nem em t = 105: retire-a de PENDENTES_ROTULO']})
                print('FALHA', tela, 'PENDENTES_ROTULO: a tela está limpa, retire-a da lista')
            for tela in [t for t in lista if t in MUDA_SEM_FIXO]:   # sem congelar, a leitura anda (em 1,5 s)
                total += 1
                prob = teste_muda_sem_fixo(b, tela)
                if prob:
                    falhas.append({'tela': tela, 'tema': 'leitura viva', 'prob': prob})
                    print('FALHA leitura viva', tela, ' | '.join(prob))
            for tela in [t for t in ('G3-Diario-Web', 'A1-Ponte-Web', 'A2-Ponte-Mobile') if t in lista]:   # a moldura não corta texto em silêncio, em nenhum ponto do laço (P4B, revisão)
                total += 1
                prob = teste_corte_moldura(b, tela)
                if prob:
                    falhas.append({'tela': tela, 'tema': 'moldura sem corte', 'prob': prob[:6]})
                    print('FALHA moldura sem corte', tela, ' | '.join(prob[:3]))
            for tela in [t for t in ('A1-Ponte-Web', 'A2-Ponte-Mobile', 'A4-Sensores-Web', 'A5-Sensores-Mobile') if t in lista]:   # F06: o selo do coletor pela cor (a moldura e, nas telas que têm, o da página)
                total += 1
                prob = teste_selo_coletor(b, tela)
                if prob:
                    falhas.append({'tela': tela, 'tema': 'selo do coletor', 'prob': prob})
                    print('FALHA selo do coletor', tela, ' | '.join(prob))
            for nome, prob in p4c_conferencias(b, lista):   # P4C: gráfico, Ponte, sensores, ramo simulacao:false e o código
                total += 1
                if prob:
                    falhas.append({'tela': nome, 'tema': 'P4C', 'prob': prob[:8]})
                    print('FALHA P4C ·', nome, ' | '.join(prob[:4]))
            for nome, prob in p4d_conferencias(b, lista):   # P4D: a Carta (B1 a B3): propulsão, estados, hora da resposta, janela de emergência, ramo simulacao:false e o código
                total += 1
                if prob:
                    falhas.append({'tela': nome, 'tema': 'P4D', 'prob': prob[:8]})
                    print('FALHA P4D ·', nome, ' | '.join(prob[:4]))
            for nome, prob in p4e_conferencias(b, lista):   # P4E: o Leme (C1 a C3, o alerta vivo) e os checklists C4: leituras, alerta, marcas, CONCLUIR, ramo simulacao:false e o código
                total += 1
                if prob:
                    falhas.append({'tela': nome, 'tema': 'P4E', 'prob': prob[:8]})
                    print('FALHA P4E ·', nome, ' | '.join(prob[:4]))
            for nome, prob in p4f_conferencias(b, lista):   # P4F: o Modo navegação (E1 e E2): troca NAVEGANDO × FUNDEADO, alarme → C3, vigia ao vivo, triagem com o segundo do quadro, ramo simulacao:false e o código
                total += 1
                if prob:
                    falhas.append({'tela': nome, 'tema': 'P4F', 'prob': prob[:8]})
                    print('FALHA P4F ·', nome, ' | '.join(prob[:4]))
            for nome, prob in p4g_conferencias(b, lista):   # P4G: a Home (Main e H2) e os atalhos (H3): leitura de agora, cartões, ouvintes, a IA, a janela de emergência, os botões das propostas e o código
                total += 1
                if prob:
                    falhas.append({'tela': nome, 'tema': 'P4G', 'prob': prob[:8]})
                    print('FALHA P4G ·', nome, ' | '.join(prob[:4]))
            for nome, prob in p4h_conferencias(b, lista):   # P4H: o FAQ dos equipamentos (F1 a F5 e a F6): o hub, o estado a bordo do instante, a lista, a busca e os 91 itens, do FAQ ao chat e o código
                total += 1
                if prob:
                    falhas.append({'tela': nome, 'tema': 'P4H', 'prob': prob[:8]})
                    print('FALHA P4H ·', nome, ' | '.join(prob[:4]))
            for nome, prob in p4i_conferencias(b, lista):   # P4I: Documentos com peças (G1) e Abastecimento com consumo (G2): validade pelo CapitaoAgora, estoque, −1 USADA, consumo por faixa, gráficos, ramo simulacao:false e o código
                total += 1
                if prob:
                    falhas.append({'tela': nome, 'tema': 'P4I', 'prob': prob[:8]})
                    print('FALHA P4I ·', nome, ' | '.join(prob[:4]))
            for tela in [t for t in SEM_UNPKG if t in lista]:
                total += 1
                prob = teste_sem_unpkg(b, tela)
                if prob:
                    falhas.append({'tela': tela, 'tema': 'sem unpkg', 'prob': prob})
                    print('FALHA sem unpkg', tela, ' | '.join(prob))
            for tela in [t for t in CLIMA if t in lista]:
                total += 1
                prob = teste_clima(b, tela)
                if prob:
                    falhas.append({'tela': tela, 'tema': 'vento no cabeçalho', 'prob': prob})
                    print('FALHA vento no cabeçalho', tela, ' | '.join(prob))
            for tela in [t for t in RESPOSTA_CLIMA if t in lista]:
                total += 1
                prob = teste_resposta_clima(b, tela)
                if prob:
                    falhas.append({'tela': tela, 'tema': 'previsão na resposta', 'prob': prob})
                    print('FALHA previsão na resposta', tela, ' | '.join(prob))
            if 'S2-SOS-Mobile' in lista:
                total += 1
                prob = teste_reserva(b, 'S2-SOS-Mobile')
                if prob:
                    falhas.append({'tela': 'S2-SOS-Mobile', 'tema': 'reserva do React', 'prob': prob})
                    print('FALHA reserva do React', ' | '.join(prob))
            if 'login' in paginas:
                total += 1
                prob = teste_login_sos(b)
                if prob:
                    falhas.append({'tela': 'login', 'tema': 'SOS sem login', 'prob': prob})
                    print('FALHA login · SOS sem login', ' | '.join(prob))
                for nome, prob in teste_login(b).items():
                    total += 1
                    if prob:
                        falhas.append({'tela': 'login', 'tema': nome, 'prob': prob})
                        print('FALHA login ·', nome, ' | '.join(prob))
            for tela in [t for t in ('G4-Equipe-Web', 'G4-Equipe-Mobile') if t in lista]:
                total += 1
                prob = teste_equipe_convidado(b, tela)
                if prob:
                    falhas.append({'tela': tela, 'tema': 'convidado', 'prob': prob})
                    print('FALHA convidado', tela, ' | '.join(prob))
            if 'dados' in paginas:
                for nome, prob in teste_dados(b).items():
                    total += 1
                    if prob:
                        falhas.append({'tela': 'dados', 'tema': nome, 'prob': prob})
                        print('FALHA dados ·', nome, ' | '.join(prob))
            total += 1
            prob = selo_manifest()  # qualquer lista de telas: é o manifest, não uma tela
            if prob:
                falhas.append({'tela': 'manifest', 'tema': 'selo', 'prob': prob})
                print('FALHA manifest · selo', ' | '.join(prob))
            for nome, prob in teste_atalhos(b).items():  # qualquer lista de telas: é o manifest, não uma tela
                total += 1
                if prob:
                    falhas.append({'tela': 'manifest', 'tema': 'atalho ' + nome, 'prob': prob})
                    print('FALHA atalho', nome, ' | '.join(prob))
        if offline:
            total += 1
            prob = teste_offline(b, lista, paginas)
            if prob:
                falhas.append({'tela': 'offline', 'prob': prob}); print('FALHA offline', ' | '.join(prob))
        b.close()
    print('%d verificações · %d falhas · %.0f s' % (total, len(falhas), time.time() - t0))
    with open(os.path.join(RAIZ, 'testes', 'saida-ultima.json'), 'w', encoding='utf-8') as f:
        json.dump({'total': total, 'falhas': falhas}, f, ensure_ascii=False, indent=1)
    sys.exit(1 if falhas else 0)


def problemas_login_sos(m, movel, h):
    """O botão de SOS do login (SOS em todas as telas, PROMPT Fase 4): vermelho, S2 no celular e S1 no computador, à vista na 1ª tela, com alvo de 44 px e sem
    passar da largura; o ENTRAR continua na 1ª tela a partir de 640 px (conferido ao lado, em MEDE_LOGIN)."""
    if not m: return ['o login não tem o botão de SOS (a[href*="SOS-"])']
    prob = []
    esperado = 'S2-SOS-Mobile.dc.html' if movel else 'S1-SOS-Web.dc.html'
    if m['href'] != esperado: prob.append('SOS do login leva a %r (esperado %s)' % (m['href'], esperado))
    if not m['txt'].startswith('SOS') or m['aria'] != 'SOS — emergência': prob.append('SOS do login com texto %r e aria-label %r' % (m['txt'], m['aria']))
    if m['w'] < 43.5 or m['h'] < 43.5: prob.append('SOS do login com alvo de %.0f×%.0f px (o toque pede 44)' % (m['w'], m['h']))
    if m['topo'] < 0 or m['fim'] > h + 0.5: prob.append('SOS do login fora da 1ª tela (%.0f a %.0f de %d)' % (m['topo'], m['fim'], h))
    if m['esq'] < 0 or m['dir'] > m['vw'] + 0.5: prob.append('SOS do login passa da largura (%.0f a %.0f de %d)' % (m['esq'], m['dir'], m['vw']))
    cor = [int(x) for x in re.findall(r'\d+', m['cor'])[:3]]
    if len(cor) != 3 or not (cor[0] > 150 and cor[0] > cor[1] + 80 and cor[0] > cor[2] + 80): prob.append('SOS do login não é vermelho: %s' % m['cor'])
    return prob


def teste_login_sos(b):
    """O SOS do login abre sem login (nenhuma sessão): a tela de emergência certa para o aparelho, com o roteiro do canal 16, sem voltar ao login."""
    prob = []
    for (w, h), movel in (((1440, 900), False), ((390, 844), True)):
        ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None, is_mobile=movel, has_touch=movel, service_workers='block')
        aplica_mut(ctx)
        pg = ctx.new_page()
        erros = []
        pg.on('pageerror', lambda e: erros.append(str(e)[:200]))
        pg.goto(BASE + 'login.html', wait_until='load')
        pg.click('a[href*="SOS-"]')
        esperado = 'S2-SOS-Mobile.dc.html' if movel else 'S1-SOS-Web.dc.html'
        try:
            pg.wait_for_function("() => document.body && /CANAL 16|MAYDAY/.test(document.body.innerText)", timeout=15000)
        except Exception:
            prob.append('%dx%d: o SOS do login não abriu o roteiro (url %s)' % (w, h, pg.url))
        if not pg.url.split('#')[0].endswith(esperado): prob.append('%dx%d: o SOS do login abriu %s (esperado %s, sem passar pelo login)' % (w, h, pg.url, esperado))
        if erros: prob.append('%dx%d: erro de script %s' % (w, h, erros[0]))
        ctx.close()
    return prob


# A leitura da tela anda sem o replay congelado (P4B): em 1,5 s o texto (ou o aria-label/title) da tela muda (o tique é de 1 s). A C3 vira alerta vivo na Fase 4: até lá está em
# PENDENTES_MUDA e, se já mudar, reprova (retire-a da lista).
LE_MUDA = """() => ({ t: document.body.innerText, a: [...document.querySelectorAll('[aria-label],[title]')].map((e) => (e.getAttribute('aria-label') || '') + '|' + (e.title || '')).join('~') })"""


def teste_muda_sem_fixo(b, tela):
    movel = eh_app(tela)
    w, h = (390, 844) if movel else (1440, 900)
    ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None, is_mobile=movel, has_touch=movel, service_workers='block')
    ctx.add_init_script(SESSAO + ";localStorage.setItem('capitao.plataforma.v1', '" + ('app' if movel else 'web') + "');")   # sem o 'capitao.replay.fixo': o replay anda
    aplica_mut(ctx)
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
    pg.goto(BASE + tela + '.dc.html', wait_until='load')
    try:
        pg.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
    except Exception:
        erros.append('prancheta não desenhou em 15 s')
    pg.wait_for_timeout(2500)
    fixo = pg.evaluate("() => { try { return localStorage.getItem('capitao.replay.fixo'); } catch (e) { return 'erro'; } }")
    mudou = False
    for _ in range(3):   # um tique de 1 s cai dentro de qualquer janela de 1,5 s; a repetição só cobre o valor que por acaso não mudou no segundo
        a = pg.evaluate(LE_MUDA)
        pg.wait_for_timeout(1500)
        if a != pg.evaluate(LE_MUDA):
            mudou = True
            break
    ctx.close()
    prob = list(erros)
    if fixo: prob.append('o teste não vale: o replay estava fixado (%r)' % fixo)
    if tela in PENDENTES_MUDA:
        if mudou: prob.append('a leitura já muda em 1,5 s sem congelar: retire a tela de PENDENTES_MUDA')
    elif not mudou:
        prob.append('a leitura não mudou em 1,5 s sem congelar o replay (3 tentativas): o quadro do replay não chega à tela')
    return prob


# O laço inteiro na moldura da web (P4B, revisão): o estado e o local mudam de comprimento com o quadro («AO LARGO DA ILHA DAS CABRAS, A CAMINHO DA BARRA SUL» só nos primeiros 70 s), então um instante só
# não pega o corte. Uma página só por tamanho: CapitaoReplay.fixar(t) refaz a moldura no mesmo instante (o tique sai dentro da chamada). 0, 5, 10, 20, 30, 45, 60, 80, 105, 120 e 149 s, a 1440×900 e 1280×720.
INSTANTES_CORTE = (0, 5, 10, 20, 30, 45, 60, 80, 105, 120, 149)


def teste_corte_moldura(b, tela):
    prob = []
    movel = eh_app(tela)
    for (w, h) in ([(390, 844), (360, 640)] if movel else [(1440, 900), (1280, 720)]):
        ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None, is_mobile=movel, has_touch=movel, service_workers='block')
        ctx.add_init_script(SESSAO + ";localStorage.setItem('capitao.plataforma.v1', '" + ('app' if movel else 'web') + "');try { localStorage.setItem('capitao.replay.fixo', '60'); } catch (e) {}")
        aplica_mut(ctx)
        pg = ctx.new_page()
        erros = []
        pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
        pg.goto(BASE + tela + '.dc.html', wait_until='load')
        try:
            pg.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0 && window.CapitaoReplay", timeout=15000)
        except Exception:
            erros.append('prancheta não desenhou em 15 s')
        pg.wait_for_timeout(700)
        for t in INSTANTES_CORTE:
            pg.evaluate("(t) => window.CapitaoReplay.fixar(t)", t)
            for x in problemas_corte(pg):
                prob.append('%s %dx%d, t = %d s: %s' % (tela, w, h, t, x))
        if erros: prob += ['%s %dx%d: %s' % (tela, w, h, e) for e in erros[:2]]
        ctx.close()
    return prob


# F06 — selo do coletor pela cor: verde (e LED que pulsa) com o replay ao vivo; amarelo (LED parado, «Última leitura · dd/mm HH:MM») quando só há a última leitura salva:
# com a flag D.simulacao desligada com a página aberta, e com o capitao-replay.js que não carregou (a reprodução falhou). Volta a verde quando a flag volta.
LE_SELO = """() => { const L = window.CapitaoMoldura.leitura(), D = window.CapitaoDados, pil = document.querySelector('[data-cpm=pilula]'), led = document.querySelector('capitao-topo-app [data-cpm=led]');
  const bola = pil ? pil.firstElementChild : led ? led.firstElementChild : null, cs = bola ? getComputedStyle(bola) : null, S = D.snapshot || {};
  return { vivo: L.vivo, rotulo: L.rotulo, texto: pil ? pil.innerText : led ? led.getAttribute('aria-label') : '', titulo: pil ? pil.title : led ? led.title : '', cor: cs ? cs.backgroundColor : '',
    pulsa: !!(bola && bola.classList.contains('cpm-led')), ultima: 'Última leitura · ' + String(S.quando || '').slice(0, 5) + ' ' + (S.hora || ''), replay: typeof window.CapitaoReplay,
    nota: (() => { const n = document.querySelector('[data-selo]'); return n ? { tom: n.getAttribute('data-selo'), texto: n.innerText.trim(), cor: getComputedStyle(n.firstElementChild).backgroundColor } : null; })() }; }"""


def cor_do_selo(rgb):
    c = [int(x) for x in re.findall(r'\d+', rgb or '')[:3]]
    if len(c) != 3: return '?'
    if c[1] > c[0] + 30 and c[1] > c[2]: return 'verde'
    if c[0] > c[1] > c[2] and c[0] - c[2] > 60: return 'amarelo'
    return '?'


def teste_selo_coletor(b, tela):
    movel = eh_app(tela)
    w, h = (390, 844) if movel else (1440, 900)
    tema = 'claro' if movel else 'escuro'   # os dois temas ficam cobertos (a A1 no escuro, a A2 no claro)
    prob = []

    def abre(sem_replay):
        ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None, is_mobile=movel, has_touch=movel, service_workers='block')
        ctx.add_init_script(SESSAO + ";localStorage.setItem('capitao.tema.v1', '" + tema + "');localStorage.setItem('capitao.plataforma.v1', '" + ('app' if movel else 'web') + "');"
                            "try { localStorage.setItem('capitao.replay.fixo', '60'); } catch (e) {}")
        aplica_mut(ctx)
        if sem_replay:
            ctx.route('**/capitao-replay.js', lambda rt: rt.abort('connectionrefused'))
        pg = ctx.new_page()
        erros = []
        pg.on('pageerror', lambda e: erros.append(str(e)[:200]))
        pg.goto(BASE + tela + '.dc.html', wait_until='load')
        pg.wait_for_function("() => document.querySelector('capitao-theme-toggle button') && window.CapitaoMoldura", timeout=15000)
        pg.wait_for_timeout(1500)
        return ctx, pg, erros

    def le(pg):
        return pg.evaluate(LE_SELO)

    def confere(rot, r, vivo, com_nota=False):
        cor = cor_do_selo(r['cor'])
        if com_nota and r['nota'] is not None:   # P4C (F06): o selo da própria página (A1, A4, A5) pela mesma cor: verde «Ao vivo · HH:MM», âmbar «Última leitura · dd/mm HH:MM»
            n = r['nota']
            if n['tom'] != ('ok' if vivo else 'warn') or cor_do_selo(n['cor']) != ('verde' if vivo else 'amarelo'): prob.append('%s: o selo da página é %s/%s (esperado %s)' % (rot, n['tom'], cor_do_selo(n['cor']), 'verde' if vivo else 'âmbar'))
            if vivo and not re.fullmatch(r'Ao vivo · \d\d:\d\d', n['texto']): prob.append('%s: o selo da página diz %r (esperado «Ao vivo · HH:MM»)' % (rot, n['texto']))
            if not vivo and n['texto'] != r['ultima']: prob.append('%s: o selo da página diz %r (esperado «%s»)' % (rot, n['texto'], r['ultima']))
        if r['vivo'] is not vivo: prob.append('%s: leitura().vivo = %s (esperado %s)' % (rot, r['vivo'], vivo))
        if cor != ('verde' if vivo else 'amarelo'): prob.append('%s: o LED é %s (%s), esperado %s' % (rot, cor, r['cor'], 'verde' if vivo else 'amarelo'))
        if r['pulsa'] is not vivo: prob.append('%s: o LED %s (verde pulsa, amarelo fica parado)' % (rot, 'pulsa' if r['pulsa'] else 'não pulsa'))
        if vivo:
            if not re.fullmatch(r'Ao vivo · \d\d:\d\d:\d\d', r['texto'].strip()) : prob.append('%s: o selo diz %r (esperado «Ao vivo · HH:MM:SS»)' % (rot, r['texto']))
        elif r['texto'].strip() != r['ultima']:
            prob.append('%s: o selo diz %r (esperado «%s»)' % (rot, r['texto'], r['ultima']))
        if not vivo and re.search(r'snapshot|desligad|fixa|demo', r['texto'] + ' ' + r['titulo'], re.I): prob.append('%s: o selo ou a dica usa palavra de rótulo: %r %r' % (rot, r['texto'], r['titulo']))

    ctx, pg, erros = abre(False)
    confere('replay ao vivo', le(pg), True, True)
    pg.evaluate("() => { window.CapitaoDados.simulacao = false; window.dispatchEvent(new CustomEvent('capitao-sessao')); }")
    pg.wait_for_timeout(300)
    confere('replay desligado (D.simulacao false)', le(pg), False)
    pg.evaluate("() => { window.CapitaoDados.simulacao = true; window.dispatchEvent(new CustomEvent('capitao-sessao')); }")
    pg.wait_for_timeout(300)
    confere('replay de volta', le(pg), True, True)
    if erros: prob.append('erro de script: ' + erros[0])
    ctx.close()
    ctx, pg, erros = abre(True)
    r = le(pg)
    if r['replay'] != 'undefined': prob.append('o teste não vale: o capitao-replay.js carregou (typeof %s)' % r['replay'])
    confere('replay que falhou ao carregar', r, False, True)
    if erros: prob.append('sem o capitao-replay.js: erro de script ' + erros[0])
    ctx.close()
    return prob


def teste_sem_unpkg(b, tela):
    """unpkg.com abortado: a tela monta (dc-root com filhos), sem erro de script, com o React de assets/vendor e sem pedido ao unpkg."""
    movel = eh_app(tela)
    w, h = (APP if movel else WEB)[0]
    ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None,
                        is_mobile=movel, has_touch=movel, service_workers='block')
    ctx.add_init_script(SESSAO)
    unpkg = corta_unpkg(ctx)
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
    pg.on('console', lambda m: erros.append('console: ' + m.text[:300]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    prob = []
    pg.goto(BASE + tela + '.dc.html', wait_until='load')
    try:
        pg.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
    except Exception:
        prob.append('não montou em 15 s')
    pg.wait_for_timeout(900)
    r = pg.evaluate("""() => ({ react: !!(window.React && window.ReactDOM),
  src: [...document.scripts].map((s) => s.src).filter((s) => /\\/react(-dom)?\\.production\\.min\\.js$/.test(s)) })""")
    if not r['react']: prob.append('sem React')
    if len(r['src']) != 2 or not all(s.startswith(REACT_LOCAL) for s in r['src']): prob.append('React fora de assets/vendor: %s' % r['src'])
    if erros: prob += erros
    if unpkg: prob.append('%d pedido(s) ao unpkg: %s' % (len(unpkg), unpkg[0]))
    ctx.close()
    return prob


# Previsão de hoje como o Open-Meteo devolve (daily, nós). A data entra no teste (hoje no fuso do barco); 48° = NE.
PREVISAO = {'temperature_2m_max': [27.4], 'temperature_2m_min': [18.2], 'wind_speed_10m_max': [12.3], 'wind_gusts_10m_max': [19.4],
            'wind_direction_10m_dominant': [48]}
WINDY_REF = 'https://www.windy.com/-26.991/-48.635?-26.991,-48.635,11'  # posição de referência (GeoNames 3471039), 3 casas
DIA_BARCO = """(ms) => new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(Date.now() + ms))"""
LE_CLIMA = """() => {
  const el = document.querySelector('capitao-hora-clima'); if (!el || el.children.length < 4) return null;
  const hd = el.closest('header'), H = hd.getBoundingClientRect(), prob = [];
  const plano = (p) => [...p.children].flatMap((k) => getComputedStyle(k).display === 'contents' ? plano(k) : [k]);
  const itens = plano(hd).map((k) => ({ k, r: k.getBoundingClientRect() })).filter((x) => x.r.width > 0 && x.r.height > 0).sort((a, b) => a.r.left - b.r.left);
  const nome = (k) => (k.tagName.toLowerCase() + ' ' + (k.textContent || '').trim()).slice(0, 40);
  itens.forEach((x, i) => {
    if (x.r.left < H.left - 0.5 || x.r.right > H.right + 0.5 || x.r.top < H.top - 0.5 || x.r.bottom > H.bottom + 0.5) prob.push('fora do cabeçalho: ' + nome(x.k));
    // só onde há texto: o botão do tema tem alvo de 44 px com margem negativa (de propósito) e passa da caixa de 34
    if ((x.k.textContent || '').trim() && x.k.scrollWidth > x.k.clientWidth + 1) prob.push('texto cortado: ' + nome(x.k));
    const y = itens[i + 1]; if (y && x.r.right > y.r.left + 0.5) prob.push('sobreposto: ' + nome(x.k) + ' × ' + nome(y.k));
  });
  [...el.querySelectorAll('a')].forEach((a) => { if (a.scrollWidth > a.clientWidth + 1) prob.push('texto cortado: ' + nome(a)); });
  const de = document.documentElement, links = [...el.querySelectorAll('a')], vento = links.find((a) => /KT/.test(a.textContent));
  const r = el.getBoundingClientRect(), hora = el.querySelector('b').getBoundingClientRect(), vr = vento ? vento.getBoundingClientRect() : null;
  return { prob, lateral: de.scrollWidth - de.clientWidth, vento: vento ? vento.textContent : null, titulo: vento ? vento.title : '',
           titulos: links.map((a) => a.title), links: links.map((a) => [a.href, a.target, a.rel]), texto: el.textContent,
           duasLinhas: !!vr && vr.top > hora.bottom - 1, altura: r.height / (H.height || 1), local: (window.CapitaoDados.posicaoRef || {}).nome };
}"""


def teste_clima(b, tela):
    """Vento e rajada do dia no cabeçalho, com o Open-Meteo simulado (JSON fixo; marine com a maré). Ver o cabeçalho do arquivo."""
    movel = eh_app(tela)
    prob = []
    pg0 = b.new_page()
    hoje, ontem = pg0.evaluate(DIA_BARCO, 0), pg0.evaluate(DIA_BARCO, -86400e3)
    pg0.close()
    t0 = int(time.time()) // 3600 * 3600
    mare = {'hourly': {'time': [t0 + 3600 * i for i in range(-24, 48)], 'sea_level_height_msl': [0.42] * 72}}

    def abre(w, h, tema, modo, salva=None):
        ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None,
                            is_mobile=movel, has_touch=movel, service_workers='block')
        ctx.add_init_script(SESSAO + ";localStorage.setItem('capitao.tema.v1', '" + tema + "');")
        aplica_mut(ctx)
        if salva:  # leitura salva (sem a data e a hora, que o próprio navegador põe: dia no fuso do barco, em = 3 h atrás)
            ctx.add_init_script("(() => { const c = %s; c.em = Date.now() - 3 * 3600e3; localStorage.setItem('capitao.clima.v1', JSON.stringify(c)); })()" % json.dumps(salva))
        pedidos = []

        def rota(rt):
            url = rt.request.url
            pedidos.append(url)
            if modo == 'sem rede':
                return rt.abort('internetdisconnected')
            if 'marine-api.' in url:
                corpo = mare
            else:
                d = dict(PREVISAO, time=[hoje])
                if modo == 'sem rajada no ECMWF' and 'models=ecmwf' in url:
                    d['wind_gusts_10m_max'] = [None]
                elif modo == 'sem rajada no ECMWF':
                    d['wind_gusts_10m_max'] = [21.2]  # melhor modelo do Open-Meteo
                corpo = {'daily': d}
            rt.fulfill(status=200, content_type='application/json', body=json.dumps(corpo), headers={'access-control-allow-origin': '*'})
        ctx.route('https://*.open-meteo.com/**', rota)
        pg = ctx.new_page()
        pg.goto(BASE + tela + '.dc.html', wait_until='load')
        try:
            pg.wait_for_function("() => { const e = document.querySelector('capitao-hora-clima'); return e && e.children.length >= 4; }", timeout=15000)
        except Exception:
            ctx.close()
            return None, pedidos
        pg.wait_for_timeout(1200)
        r = pg.evaluate(LE_CLIMA)
        if r is not None and salva:
            r['hora_salva'] = pg.evaluate("() => new Intl.DateTimeFormat('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(JSON.parse(localStorage.getItem('capitao.clima.v1')).em))")
        ctx.close()
        return r, pedidos

    tams = [(390, 844), (360, 640)] if movel else [(1440, 900), (1024, 768)]
    for tema in ('escuro', 'claro'):
        for (w, h) in tams:
            tag = '%s %dx%d' % (tema, w, h)
            r, pedidos = abre(w, h, tema, 'json fixo')
            if r is None:
                prob.append(tag + ': o cabeçalho não montou'); continue
            if r['vento'] != 'NE12/19KT': prob.append(tag + ': vento no cabeçalho %r (esperado NE 12/19 KT)' % r['vento'])
            if any(x != [WINDY_REF, '_blank', 'noopener'] for x in r['links']) or len(r['links']) != 3:
                prob.append(tag + ': toques do clima, vento e maré não abrem o windy.com na referência em nova aba: %s' % r['links'])
            if 'ECMWF via Open-Meteo, lida às' not in r['titulo'] or 'até 12 nós de NE, rajadas até 19 nós' not in r['titulo']:
                prob.append(tag + ': title do vento sem fonte e hora: ' + r['titulo'])
            # P4B (§2.5): o lugar dos title é o D.posicaoRef.nome (não um nome escrito no código) e nenhum title leva termo do §3
            prev = [t for t in r['titulos'] if t.startswith('Previsão de hoje')]   # (no celular a maré vem antes do clima: a ordem dos links muda)
            if not r['local'] or len(prev) != 1 or any(r['local'] not in t for t in (prev[0], r['titulo'])) or 'Balneário Camboriú: ' in r['titulo']:
                prob.append(tag + ': os title do clima e do vento não dizem o lugar de D.posicaoRef.nome (%r): %s' % (r['local'], r['titulos'][:3]))
            ach = achados_termos('clima', '\n'.join(r['titulos']))
            if ach: prob.append(tag + ': termo do §3 nos title do clima, do vento ou da maré: %s' % ach)
            if r['prob']: prob.append(tag + ': ' + '; '.join(r['prob'][:4]))
            if r['lateral'] > 1: prob.append(tag + ': rolagem lateral de %d px' % r['lateral'])
            if movel and not r['duasLinhas']: prob.append(tag + ': no celular o vento vai na 2ª linha')
            if movel and r['altura'] > 1: prob.append(tag + ': clima mais alto que o cabeçalho (%.2f)' % r['altura'])
            if any('open-meteo.com' not in u for u in pedidos) or not any('models=ecmwf_ifs025' in u and 'wind_gusts_10m_max' in u and 'wind_speed_unit=kn' in u for u in pedidos):
                prob.append(tag + ': pedido fora do esperado (ECMWF com vento e rajada em nós): %s' % pedidos[:3])
    w, h = tams[0]
    # sem rede e só a leitura de ontem: "—" em tudo (nem a leitura velha nem o vento do snapshot)
    r, _ = abre(w, h, 'escuro', 'sem rede', {'dia': ontem, 'max': 30, 'min': 20, 'vento': 25, 'raj': 33, 'dir': 180, 'modelo': 'ECMWF'})
    if r is None:
        prob.append('sem rede: o cabeçalho não montou')
    else:
        if r['vento'] != '—/—KT': prob.append('sem rede, sem leitura de hoje: vento %r (esperado —/— KT)' % r['vento'])
        if any(ch.isdigit() for ch in r['texto'][5:]): prob.append('sem rede, sem leitura de hoje: número fora da hora (HH:MM): %r' % r['texto'])
        # P4B (§2.5): sem rede e sem leitura de hoje, os três title dizem a frase de tempo e maré sem conexão (com a hora da última leitura salva), nunca SEM DADOS
        for t in r['titulos']:
            if 'Previsão e maré: sem conexão agora (última às ' + r['hora_salva'] + ') — confira o boletim da Marinha antes de sair' not in t:
                prob.append('sem rede: title sem a frase do §2.5 com a última leitura às %s: %s' % (r['hora_salva'], t))
        ach = achados_termos('clima', '\n'.join(r['titulos']))
        if ach: prob.append('sem rede: termo do §3 nos title: %s' % ach)
    # sem rede com a leitura salva de hoje: ela, com a hora dela
    r, _ = abre(w, h, 'claro', 'sem rede', {'dia': hoje, 'max': 26, 'min': 17, 'vento': 8.4, 'raj': 14.6, 'dir': 200, 'modelo': 'ECMWF'})
    if r is None:
        prob.append('sem rede com leitura salva: o cabeçalho não montou')
    elif r['vento'] != 'S8/15KT' or ('lida às ' + r['hora_salva']) not in r['titulo']:
        prob.append('sem rede com a leitura salva de hoje: %r · %s (esperado S 8/15 KT, lida às %s)' % (r['vento'], r['titulo'], r['hora_salva']))
    # ECMWF sem rajada: a rajada vem do melhor modelo do Open-Meteo, dito no title
    r, pedidos = abre(w, h, 'escuro', 'sem rajada no ECMWF')
    if r is None:
        prob.append('ECMWF sem rajada: o cabeçalho não montou')
    elif r['vento'] != 'NE12/21KT' or 'rajada: melhor modelo do Open-Meteo' not in r['titulo']:
        prob.append('ECMWF sem rajada: %r · %s' % (r['vento'], r['titulo']))
    return prob


def teste_resposta_clima(b, tela):
    """Previsão do dia na resposta de uma tela sem o cabeçalho do clima (B3): a leitura salva de hoje (capitao.clima.v1, como o
    capitao-clima.js grava) entra no clima e no "seguro para sair?", com fonte e hora; sem ela, a frase do §2.5 (sem conexão agora). Open-Meteo fora (abort)."""
    movel = eh_app(tela)
    prob = []
    pg0 = b.new_page()
    hoje = pg0.evaluate(DIA_BARCO, 0)
    pg0.close()
    salva = {'dia': hoje, 'max': 27.4, 'min': 18.2, 'vento': 12.3, 'raj': 19.4, 'dir': 48, 'modelo': 'ECMWF'}
    vento = 'vento até 12 nós de nordeste, rajadas até 19 nós'
    for semeada in (True, False):
        for q in ('é seguro sair hoje?', 'como está o vento hoje?'):
            tag = '%s (%s)' % (q, 'leitura de hoje salva' if semeada else 'sem leitura')
            ctx = b.new_context(viewport={'width': 390, 'height': 844}, user_agent=MOBILE_UA if movel else None,
                                is_mobile=movel, has_touch=movel, service_workers='block')
            ctx.add_init_script(SESSAO)
            if semeada:
                ctx.add_init_script("(() => { const c = %s; c.em = Date.now() - 3 * 3600e3; localStorage.setItem('capitao.clima.v1', JSON.stringify(c)); })()" % json.dumps(salva))
            ctx.route('https://*.open-meteo.com/**', lambda rt: rt.abort('internetdisconnected'))
            pg = ctx.new_page()
            erros = []
            pg.on('pageerror', lambda e: erros.append(str(e)[:200]))
            pg.goto(BASE + tela + '.dc.html#q=' + urllib.parse.quote(q), wait_until='load')
            try:
                pg.wait_for_function("() => /Fonte:/.test(document.body.innerText)", timeout=15000)
            except Exception:
                prob.append(tag + ': a resposta não apareceu'); ctx.close(); continue
            r = pg.evaluate("""() => ({ texto: document.body.innerText, hora: (() => { const c = JSON.parse(localStorage.getItem('capitao.clima.v1') || 'null');
              return c ? new Intl.DateTimeFormat('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(c.em)) : ''; })(),
              windy: [...document.querySelectorAll('a')].filter((a) => a.href.startsWith('https://www.windy.com/')).map((a) => [a.href, a.target, a.rel]) })""")
            ctx.close()
            t = r['texto']
            if erros: prob.append(tag + ': erro de script ' + '; '.join(erros[:2]))
            if semeada:
                if vento not in t or ('ECMWF via Open-Meteo, lida às ' + r['hora']) not in t:
                    prob.append(tag + ': sem o vento previsto com fonte e hora: ' + t[:300].replace('\n', ' / '))
                if r['windy'] != [[WINDY_REF, '_blank', 'noopener']]:
                    prob.append(tag + ': atalho do windy.com fora do esperado: %s' % r['windy'])
            else:
                # Fase 3 (P3B), PROMPT §2.5: sem leitura de hoje a resposta diz a frase de tempo e maré sem conexão (a exceção escrita), nunca SEM DADOS nem vento inventado
                if 'Previsão e maré: sem conexão agora' not in t or 'confira o boletim da Marinha antes de sair' not in t or 'vento até' in t or 'rajadas até' in t or r['windy']:
                    prob.append(tag + ': inventou vento ou perdeu a frase de «sem conexão» do §2.5: ' + t[:300].replace('\n', ' / '))
            if 'sem internet e sem leitura salva' in t:
                prob.append(tag + ': diz "sem internet" sem saber (o Open-Meteo nem foi consultado)')
    return prob


def teste_reserva(b, tela):
    """Troca de versão com o SW da 1.0.x: o cache dele pode ficar com o support.js novo sem o assets/vendor. Com a cópia local
    fora, a tela (o SOS) monta com o React da reserva — o endereço do unpkg, com o mesmo SRI —, sem erro de script. O teste
    serve a reserva com os bytes de assets/vendor (os do pacote npm): não depende da internet."""
    ctx = b.new_context(viewport={'width': APP[0][0], 'height': APP[0][1]}, user_agent=MOBILE_UA, is_mobile=True, has_touch=True,
                        service_workers='block')
    ctx.add_init_script(SESSAO)
    pedidos = []

    def unpkg(rt):
        pedidos.append(rt.request.url)
        arq = REACT_RESERVA.get(rt.request.url)
        if not arq:
            return rt.abort('connectionrefused')
        rt.fulfill(path=os.path.join(RAIZ, 'assets', 'vendor', 'react-18.3.1', arq), status=200,
                   headers={'content-type': 'text/javascript; charset=utf-8', 'access-control-allow-origin': '*'})
    ctx.route('https://unpkg.com/**', unpkg)
    ctx.route(REACT_LOCAL + '**', lambda rt: rt.abort('connectionrefused'))
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
    pg.on('console', lambda m: erros.append('console: ' + m.text[:300]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    prob = []
    pg.goto(BASE + tela + '.dc.html', wait_until='load')
    try:
        pg.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
    except Exception:
        prob.append('não montou em 15 s com a cópia local fora')
    pg.wait_for_timeout(900)
    r = pg.evaluate("() => ({ react: !!(window.React && window.ReactDOM && window.ReactDOM.createRoot), texto: document.body.innerText.toUpperCase() })")
    if not r['react']: prob.append('sem React')
    if 'CANAL 16' not in r['texto'] and 'MAYDAY' not in r['texto']: prob.append('SOS sem CANAL 16 / MAYDAY: ' + r['texto'][:120])
    if sorted(pedidos) != sorted(REACT_RESERVA): prob.append('reserva fora do esperado: %s' % pedidos)
    if erros: prob += erros
    ctx.close()
    return prob


def tamanho_png(dados):
    """(largura, altura) do cabeçalho IHDR do PNG, lido com struct (sem Pillow); None se não for PNG."""
    if len(dados) < 24 or dados[:8] != b'\x89PNG\r\n\x1a\n' or dados[12:16] != b'IHDR':
        return None
    return struct.unpack('>II', dados[16:24])


# Desenho de um ícone de atalho, no navegador (o PNG do mesmo site não "suja" o canvas): pixels do desenho (opacos e longe do
# fundo #050816; a borda suavizada do disco do any fica de fora), retângulo que os contém, quantos saem da zona segura do
# maskable (círculo de raio 0,4 × lado) e quantos pixels são opacos.
DESENHO_ATALHO = """async ([src, lado]) => {
  const im = new Image(); im.src = src; await im.decode();
  const c = document.createElement('canvas'); c.width = c.height = lado;
  const g = c.getContext('2d'); g.drawImage(im, 0, 0);
  const d = g.getImageData(0, 0, lado, lado).data, m = lado / 2, zona = 0.4 * lado;
  let n = 0, fora = 0, opacos = 0, x0 = lado, y0 = lado, x1 = -1, y1 = -1;
  for (let y = 0; y < lado; y++) for (let x = 0; x < lado; x++) {
    const i = (y * lado + x) * 4;
    if (d[i + 3] === 255) opacos++;
    if (d[i + 3] < 128 || Math.abs(d[i] - 5) + Math.abs(d[i + 1] - 8) + Math.abs(d[i + 2] - 22) < 60) continue;
    n++; x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y);
    if (Math.hypot(x + 0.5 - m, y + 0.5 - m) > zona) fora++;
  }
  return { n, fora, opacos, caixa: [x0, y0, x1 + 1, y1 + 1] };
}"""


def selo_manifest():
    """Selo (decisão b) no manifest.webmanifest: name, short_name e description, os mesmos dos atalhos e o rótulo das capturas —
    é o texto da instalação do app. Devolve a lista de problemas."""
    man = json.load(open(os.path.join(RAIZ, 'manifest.webmanifest'), encoding='utf-8'))
    campos = [('', man)] + [('atalho %d ' % i, sc) for i, sc in enumerate(man.get('shortcuts') or [])]
    campos += [('captura %d ' % i, c) for i, c in enumerate(man.get('screenshots') or [])]
    return ['%s%s: %r' % (onde, k, o[k]) for onde, o in campos for k in ('name', 'short_name', 'description', 'label')
            if isinstance(o.get(k), str) and SELO_RE.search(o[k])]


def teste_atalhos(b):
    """Ícones dos atalhos do app instalado (paridade Avanti 1.24.0, desenho próprio: ferramentas/icones/gerar_atalhos.py).
    Cada shortcut do manifest.webmanifest tem ícone any e maskable (image/png); cada src responde 200 no servidor local e o PNG
    tem exatamente o tamanho declarado em sizes (cabeçalho lido com struct). No navegador: há desenho, centrado (a caixa dele a
    no máximo 4 % do centro); no any ele não encosta na borda; no maskable o fundo é inteiro (todo pixel opaco) e o desenho fica
    dentro da zona segura. Devolve {nome do atalho: [problemas]}."""
    man = json.load(open(os.path.join(RAIZ, 'manifest.webmanifest'), encoding='utf-8'))
    sem_proxy = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    ctx = b.new_context(viewport={'width': 400, 'height': 300}, device_scale_factor=1, service_workers='block')
    ctx.route(BASE + '__atalhos__', lambda rt: rt.fulfill(status=200, content_type='text/html; charset=utf-8', body='<!doctype html><title>atalhos</title>'))
    pg = ctx.new_page()
    pg.goto(BASE + '__atalhos__')
    res = {}
    for sc in man.get('shortcuts') or [{'short_name': '(nenhum shortcut no manifest)'}]:
        nome = sc.get('short_name') or sc.get('name')
        prob = res[nome] = []
        icones = sc.get('icons') or []
        for pp in ('any', 'maskable'):
            if not any(pp in (i.get('purpose') or 'any').split() for i in icones):
                prob.append('sem ícone %s' % pp)
        for i in icones:
            src, sizes = i.get('src') or '', i.get('sizes') or ''
            tag = src or '(sem src)'
            if i.get('type') != 'image/png':
                prob.append('%s: type %r (esperado image/png)' % (tag, i.get('type')))
            m = re.fullmatch(r'(\d+)x(\d+)', sizes)
            if not m:
                prob.append('%s: sizes %r fora do formato LxA' % (tag, sizes)); continue
            decl = (int(m.group(1)), int(m.group(2)))
            try:
                with sem_proxy.open(BASE + src, timeout=10) as r:
                    st, dados = r.status, r.read()
            except urllib.error.HTTPError as e:
                st, dados = e.code, b''
            except Exception as e:
                prob.append('%s: %s' % (tag, str(e)[:120])); continue
            if st != 200:
                prob.append('%s: HTTP %s' % (tag, st)); continue
            real = tamanho_png(dados)
            if real != decl:
                prob.append('%s: PNG %s, declarado %s' % (tag, 'x'.join(map(str, real)) if real else 'inválido', sizes)); continue
            lado = decl[0]
            mask = 'maskable' in (i.get('purpose') or '').split()
            d = pg.evaluate(DESENHO_ATALHO, [BASE + src, lado])
            if d['n'] < 0.03 * lado * lado:
                prob.append('%s: quase sem desenho (%d pixels)' % (tag, d['n'])); continue
            x0, y0, x1, y1 = d['caixa']
            desvio = max(abs((x0 + x1) / 2 - lado / 2), abs((y0 + y1) / 2 - lado / 2))
            if desvio > 0.04 * lado:
                prob.append('%s: desenho fora do centro (caixa %s, desvio %.1f px)' % (tag, d['caixa'], desvio))
            if mask and d['opacos'] != lado * lado:
                prob.append('%s: maskable com fundo transparente (%d de %d pixels opacos)' % (tag, d['opacos'], lado * lado))
            if mask and d['fora']:
                prob.append('%s: %d pixel(s) do desenho fora da zona segura de 80 %%' % (tag, d['fora']))
            if not mask and min(x0, y0, lado - x1, lado - y1) < 0.1 * lado:
                prob.append('%s: desenho encostando na borda (caixa %s)' % (tag, d['caixa']))
    ctx.close()
    return res


# Dados do aparelho: linhas do diário como o capitao-brain.js grava (mais nova primeiro) e valores que nunca vão no arquivo.
# Nenhuma chave, telefone ou senha real: os segredos aqui são marcas do teste.
def linha_teste(letra, dia):
    return {'d': '%02d/10' % dia, 't': 'Linha %s do teste da cópia' % letra, 'iso': '2026-10-%02dT12:00:00.000Z' % dia, 'sys': 'Diário',
            'tone': 'var(--cap-accent, #00a1fe)', 'who': 'Lucas', 'src': 'app · texto'}


L_A, L_B, L_C, L_D, L_E = linha_teste('A', 20), linha_teste('B', 21), linha_teste('C', 22), linha_teste('D', 23), linha_teste('E', 24)
# Linha sem hora (iso): na restauração vale a ordem do arquivo.
L_X = {k: v for k, v in linha_teste('X', 21).items() if k != 'iso'}


# Documento e abastecimento no formato que G1 e G2 gravam (addDoc / addAbast: mais novo primeiro, data dd/mm/aaaa, sem iso).
def doc_teste(letra, dia):
    return {'n': 'Documento %s do teste da cópia.pdf' % letra, 's': '120 KB', 'dd': '%02d/10/2026' % dia, 'st': 'A CONFERIR', 'cat': 'Seguro',
            'fonte': 'enviado no console por Lucas'}


def abast_teste(letra, dia):
    return {'n': 'NF %s do teste da cópia.jpg' % letra, 'd': '%02d/10/2026' % dia, 'st': 'A CONFIRMAR', 'fonte': 'foto enviada no console por Lucas'}


D_A, D_B, D_C = doc_teste('A', 20), doc_teste('B', 21), doc_teste('C', 22)
N_A, N_B, N_C = abast_teste('A', 20), abast_teste('B', 21), abast_teste('C', 22)
# Linhas que a restauração do dados.html lê para não devolver o que foi desfeito depois (Executado desfeito, telefone apagado, convite
# cancelado). As telas web são conferidas clicando (teste_dados); as do app, que gravam o mesmo texto, no código.
TEXTOS_DESFEITO = {
    'C1-Leme-Web': ["t: 'Executado: ' + t.t + ' (' + t.equip + ').", "t: 'Desfeito: ' + t.t + ' volta para a agenda"],
    'C2-Leme-Mobile': ["t: 'Executado: ' + t.t + ' (' + t.equip + ').", "t: 'Desfeito: ' + t.t + ' volta para a agenda"],
    'G4-Equipe-Web': ["'Telefone de ' + this.papel(id) + ' ' + acao + ' em Equipe", "'Convite de ' + c.nome + ' (' + c.acesso + ') cancelado em Equipe",
                      "'Convite de acesso (' + acesso + ') aberto no ' + lk.canal + ' para ' + nome + (func ? ' · ' + func : '') + ' — "],
    'G4-Equipe-Mobile': ["'Telefone de ' + this.papel(id) + ' ' + acao + ' em Equipe", "'Convite de ' + c.nome + ' (' + c.acesso + ') cancelado em Equipe",
                         "'Convite de acesso (' + acesso + ') aberto no ' + lk.canal + ' para ' + nome + (func ? ' · ' + func : '') + ' — "],
}


def feita(dia):
    return {'d': '%02d/10' % dia, 't': '09:00', 'iso': '2026-10-%02dT12:00:00.000Z' % dia}


SEGREDOS = {'capitao.ia.chave.v1': 'segredo-teste-ia', 'capitao.ia.url.v1': 'segredo-teste-url', 'capitao.telemetria.chave.v1': 'segredo-teste-tele',
            'capitao.voz.chave.v1': 'segredo-teste-voz', 'capitao.login.tentativas.v1': json.dumps({'n': 2, 'ate': 0, 'ult': 1, 'm': 'segredo-teste-login'}),
            'capitao.telemetria.ultima.v1': json.dumps({'pos': 'segredo-teste-posicao'}), 'capitao.clima.v1': json.dumps({'dia': 'segredo-teste-clima'})}
# Cópia de trabalho do replay (o instante congelado e o gancho de teste do quadro): `capitao.replay.*` nunca vai no arquivo nem volta da
# restauração (CONTRATO §1.25: restaurar um instante fixado congelaria o app). O motor cria as duas; o dados.html tira o prefixo inteiro.
REPLAY_FORA = {'capitao.replay.fixo': '60@120', 'capitao.replay.sobre': json.dumps({'sog_nos': 0, 'estado': 'Fundeado', 'alarmes': []})}
GRAVA_LS = "(o) => Object.keys(o).forEach((k) => localStorage.setItem(k, o[k]))"
LE_LS = "() => Object.fromEntries(Object.keys(localStorage).sort().map((k) => [k, localStorage.getItem(k)]))"


def teste_dados(b):
    """Ida e volta da cópia (dados.html) e as proteções da restauração. Devolve {caso: [problemas]}. Arquivos fora do repositório."""
    import tempfile
    res = {}
    pasta = tempfile.mkdtemp(prefix='capitao-dados-')
    ctx = b.new_context(viewport={'width': 1280, 'height': 900}, accept_downloads=True, service_workers='block')
    ctx.add_init_script(SESSAO)
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
    pg.on('console', lambda m: erros.append('console: ' + m.text[:300]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)

    def ls():
        return pg.evaluate(LE_LS)

    def diario():
        return json.loads(ls().get('capitao.diario.v1') or 'null')

    def escolhe(files):
        pg.set_input_files('#arquivo', files)
        pg.wait_for_function("() => document.getElementById('msg').textContent.trim()", timeout=5000)
        return pg.evaluate("""() => ({ msg: document.getElementById('msg').textContent, classe: document.getElementById('msg').className,
          previa: !document.getElementById('previa').hidden, resumo: document.getElementById('resumo').innerText,
          caixa: (() => { const c = document.getElementById('prefsCaixa'); return !!(c && c.offsetParent !== null && c.getBoundingClientRect().height > 0); })(), marcada: document.getElementById('prefs').checked,
          botao: !document.getElementById('restaurar').disabled })""")

    def arquivo(dados):
        corpo = json.dumps({'app': 'Capitão IA', 'formato': 1, 'versao': 'teste', 'exportado_em': '2026-10-22T12:00:00.000Z', 'dados': dados})
        return {'name': 'copia.json', 'mimeType': 'application/json', 'buffer': corpo.encode('utf-8')}

    def restaura():
        if not pg.is_visible('#restaurar') or pg.is_disabled('#restaurar'):
            return {'msg': '(Restaurar escondido ou desligado)', 'classe': ''}
        pg.click('#restaurar')
        pg.wait_for_function("() => document.getElementById('msg').className === 'ok' || document.getElementById('msg').className === 'erro'", timeout=5000)
        return pg.evaluate("() => ({ msg: document.getElementById('msg').textContent, classe: document.getElementById('msg').className })")

    try:
        # 1) Baixar: o diário, os documentos e os abastecimentos com A e B (mais novo primeiro), uma tarefa feita, Equipe, tema
        # escuro e os segredos.
        p = res['baixar'] = []
        pg.goto(BASE + 'dados.html', wait_until='load')
        pg.evaluate(GRAVA_LS, dict(SEGREDOS, **REPLAY_FORA, **{'capitao.diario.v1': json.dumps([L_B, L_A]), 'capitao.executado.v1': json.dumps({'t1': feita(20)}),
                                             'capitao.docs.v1': json.dumps([D_B, D_A]), 'capitao.abast.v1': json.dumps([N_B, N_A]),
                                             'capitao.equipe.v1': json.dumps({'fones': {'Marinheiro': 'tel-teste-1'}, 'convites': []}), 'capitao.tema.v1': 'escuro'}))
        pg.reload(wait_until='load')
        pg.wait_for_timeout(300)
        lista = pg.inner_text('#lista')
        if 'Diário de bordo · 2 linhas' not in lista or 'Documentos enviados · 2 documentos' not in lista \
                or 'Abastecimentos enviados · 2 abastecimentos' not in lista or 'segredo' in lista or 'sessao' in lista or 'replay' in lista:
            p.append('lista do aparelho: %r' % lista)
        with pg.expect_download() as dl:
            pg.click('#baixar')
        nome = dl.value.suggested_filename
        caminho = os.path.join(pasta, nome)
        dl.value.save_as(caminho)
        texto = open(caminho, encoding='utf-8').read()
        pac = json.loads(texto)
        if not re.fullmatch(r'capitao-dados-\d{4}-\d{2}-\d{2}\.json', nome): p.append('nome do arquivo %r' % nome)
        if pac.get('app') != 'Capitão IA' or pac.get('formato') != 1 or not pac.get('versao'): p.append('cabeçalho do pacote: %r' % {k: pac.get(k) for k in ('app', 'formato', 'versao')})
        esperadas = ['capitao.abast.v1', 'capitao.diario.v1', 'capitao.docs.v1', 'capitao.equipe.v1', 'capitao.executado.v1', 'capitao.tema.v1']
        if sorted(pac.get('dados', {})) != esperadas: p.append('chaves no arquivo %s (esperado %s)' % (sorted(pac.get('dados', {})), esperadas))
        vazou = [x for x in ['capitao.sessao', 'segredo-teste', 'capitao.login', 'capitao.ia.', 'capitao.telemetria', 'capitao.voz', 'capitao.clima', 'capitao.replay'] if x in texto]
        if vazou: p.append('o arquivo leva o que nunca vai: %s' % vazou)
        if json.loads(pac['dados'].get('capitao.diario.v1', 'null')) != [L_B, L_A]: p.append('diário no arquivo diferente do aparelho')
        if json.loads(pac['dados'].get('capitao.docs.v1', 'null')) != [D_B, D_A] or json.loads(pac['dados'].get('capitao.abast.v1', 'null')) != [N_B, N_A]:
            p.append('documentos ou abastecimentos no arquivo diferentes do aparelho')

        # 2) O aparelho passa a ter A e C no diário, nos documentos e nos abastecimentos (B não está mais aqui, C é novo), outra
        # tarefa feita, outro telefone e o tema claro. Restaurar soma: nada some, nada duplica.
        p = res['restaurar soma'] = []
        pg.evaluate(GRAVA_LS, {'capitao.diario.v1': json.dumps([L_C, L_A]), 'capitao.executado.v1': json.dumps({'t2': feita(22)}),
                               'capitao.docs.v1': json.dumps([D_C, D_A]), 'capitao.abast.v1': json.dumps([N_C, N_A]),
                               'capitao.equipe.v1': json.dumps({'fones': {'Mecânico': 'tel-teste-2'}, 'convites': []}), 'capitao.tema.v1': 'claro'})
        pg.reload(wait_until='load')
        r = escolhe(caminho)
        for falta in ('Diário de bordo · 2 linhas no arquivo · falta aqui 1 linha', 'falta aqui 1 tarefa',
                      'Documentos enviados · 2 documentos no arquivo · falta aqui 1 documento',
                      'Abastecimentos enviados · 2 abastecimentos no arquivo · falta aqui 1 abastecimento'):
            if not r['previa'] or falta not in r['resumo']: p.append('prévia sem %r: %r · %r' % (falta, r['msg'], r['resumo']))
        if not r['caixa'] or r['marcada'] or not r['botao']: p.append('caixa das preferências (à vista, desmarcada) e Restaurar: %r' % r)
        fim = restaura()
        d, tudo = diario(), ls()
        if d != [L_C, L_B, L_A]: p.append('diário depois de restaurar: %s (esperado C, B, A)' % [x.get('t', '?')[6:7] for x in (d or [])])
        if json.loads(tudo.get('capitao.docs.v1') or 'null') != [D_C, D_B, D_A]: p.append('documentos depois de restaurar: %r (esperado C, B, A)' % tudo.get('capitao.docs.v1'))
        if json.loads(tudo.get('capitao.abast.v1') or 'null') != [N_C, N_B, N_A]: p.append('abastecimentos depois de restaurar: %r (esperado C, B, A)' % tudo.get('capitao.abast.v1'))
        if 'Documentos enviados +1' not in fim['msg'] or 'Abastecimentos enviados +1' not in fim['msg']: p.append('mensagem final sem documentos e abastecimentos: %r' % fim['msg'])
        ex = json.loads(tudo.get('capitao.executado.v1') or '{}')
        if ex != {'t1': feita(20), 't2': feita(22)}: p.append('tarefas feitas: %r' % ex)
        eq = json.loads(tudo.get('capitao.equipe.v1') or '{}')
        if eq.get('fones') != {'Mecânico': 'tel-teste-2', 'Marinheiro': 'tel-teste-1'}: p.append('Equipe: %r' % eq)
        if tudo.get('capitao.tema.v1') != 'claro': p.append('o tema mudou sem a caixa marcada')
        if any(tudo.get(k) != v for k, v in SEGREDOS.items()) or 'lucas' not in (tudo.get('capitao.sessao.v1') or ''):
            p.append('restaurar mexeu em sessão ou segredo')
        if fim['classe'] != 'ok' or 'Nada deste aparelho foi apagado' not in fim['msg']: p.append('mensagem final: %r' % fim)

        # 3) Restaurar de novo: nada novo, nada duplica; o tema só volta com a caixa marcada.
        p = res['restaurar de novo e preferências'] = []
        r = escolhe(caminho)
        if not r['previa'] or 'nada novo' not in r['resumo'] or r['botao']: p.append('2ª prévia (nada novo, Restaurar desligado sem a caixa): %r' % r)
        if r['caixa']:
            pg.check('#prefs')
        if pg.is_disabled('#restaurar'): p.append('Restaurar continua desligado com a caixa marcada')
        restaura()
        tudo = ls()
        if diario() != [L_C, L_B, L_A]: p.append('2ª restauração mudou o diário')
        if json.loads(tudo.get('capitao.docs.v1') or 'null') != [D_C, D_B, D_A] or json.loads(tudo.get('capitao.abast.v1') or 'null') != [N_C, N_B, N_A]:
            p.append('2ª restauração mudou documentos ou abastecimentos')
        if tudo.get('capitao.tema.v1') != 'escuro' or pg.evaluate("() => document.documentElement.getAttribute('data-capitao-tema')") != 'escuro':
            p.append('com a caixa marcada o tema não voltou para o do arquivo (escuro)')

        # 3b) Arquivo só com o diário: a caixa das preferências não aparece (o CSS da página não pode vencer o hidden).
        p = res['sem preferência no arquivo, sem caixa'] = []
        r = escolhe(arquivo({'capitao.diario.v1': json.dumps([L_D])}))
        if not r['previa'] or r['caixa']: p.append('arquivo sem preferência mostrou a caixa das preferências: %r' % r)

        # 4) Arquivo de outro app, de formato novo, corrompido ou com forma errada: mensagem de erro e nada muda.
        p = res['arquivo ruim'] = []
        linhas = json.dumps([L_D])
        ruins = {
            'outro app': json.dumps({'app': 'Outro App', 'formato': 1, 'dados': {'capitao.diario.v1': linhas}}),
            'formato novo': json.dumps({'app': 'Capitão IA', 'formato': 2, 'dados': {'capitao.diario.v1': linhas}}),
            'cortado': texto[:len(texto) // 2],
            'não é JSON': 'isto não é uma cópia',
            'diário que não é lista': json.dumps({'app': 'Capitão IA', 'formato': 1, 'dados': {'capitao.diario.v1': json.dumps({'t': 'x'}), 'capitao.docs.v1': '[]'}}),
            'valor que não é texto': json.dumps({'app': 'Capitão IA', 'formato': 1, 'dados': {'capitao.diario.v1': [L_D]}}),
            'tema inválido': json.dumps({'app': 'Capitão IA', 'formato': 1, 'dados': {'capitao.diario.v1': linhas, 'capitao.tema.v1': 'roxo'}}),
        }
        for caso, corpo in ruins.items():
            antes = ls()
            r = escolhe({'name': 'copia.json', 'mimeType': 'application/json', 'buffer': corpo.encode('utf-8')})
            if r['classe'] != 'erro' or 'Nada mudou' not in r['msg'] or r['previa']: p.append('%s: %r' % (caso, r['msg']))
            if ls() != antes: p.append('%s: o aparelho mudou' % caso)
        r = escolhe({'name': 'copia.json', 'mimeType': 'application/json', 'buffer': ruins['formato novo'].encode('utf-8')})
        if 'mais nova' not in r['msg']: p.append('formato novo sem "versão mais nova": %r' % r['msg'])
        r = escolhe({'name': 'copia.json', 'mimeType': 'application/json', 'buffer': ruins['outro app'].encode('utf-8')})
        if 'outro app' not in r['msg']: p.append('outro app sem dizer: %r' % r['msg'])

        # 5) Arquivo montado à mão com sessão de outro usuário e outra chave da IA: só a linha D entra.
        p = res['segredo no arquivo'] = []
        mao = {'app': 'Capitão IA', 'formato': 1, 'dados': {'capitao.sessao.v1': json.dumps({'u': 'demo', 'em': 1, 'exp': 9e15}),
               'capitao.ia.chave.v1': 'chave-do-arquivo', 'capitao.login.tentativas.v1': '{}', 'capitao.diario.v1': linhas,
               'capitao.replay.fixo': '5', 'capitao.replay.sobre': json.dumps({'sog_nos': 99}), 'capitao.replay.outra': 'x'}}
        r = escolhe({'name': 'copia.json', 'mimeType': 'application/json', 'buffer': json.dumps(mao).encode('utf-8')})
        if not r['previa'] or 'sess' in r['resumo'].lower() or 'chave' in r['resumo'].lower() or 'replay' in r['resumo'].lower(): p.append('prévia: %r' % r['resumo'])
        restaura()
        tudo = ls()
        # Antes a linha sem âncora no aparelho ia para o fim ([C, B, A, D]); D (23/10) é a mais nova e o app lê a lista com a mais
        # nova primeiro (A2 "último", diarioLer): ela entra no topo. Mudado na revisão da F25.
        if diario() != [L_D, L_C, L_B, L_A]: p.append('diário: %s (esperado D, C, B, A)' % [x.get('t', '?')[6:7] for x in (diario() or [])])
        if tudo.get('capitao.ia.chave.v1') != SEGREDOS['capitao.ia.chave.v1'] or '"lucas"' not in (tudo.get('capitao.sessao.v1') or '') \
                or tudo.get('capitao.login.tentativas.v1') != SEGREDOS['capitao.login.tentativas.v1']:
            p.append('sessão, tentativas ou chave da IA vieram do arquivo')
        if any(tudo.get(k) != v for k, v in REPLAY_FORA.items()) or 'capitao.replay.outra' in tudo:
            p.append('o replay (capitao.replay.*) veio do arquivo: %r' % {k: v for k, v in tudo.items() if k.startswith('capitao.replay')})

        # 6) Item que o app não lê (capitao-brain.js: diário sem t, documento sem n, Executado sem d/t, telefone que não é texto,
        # convite sem nome) nunca entra no registro: sozinho, nada a restaurar e nada muda; ao lado de uma linha boa, só ela entra.
        p = res['item ilegível no arquivo'] = []
        lixo = {'capitao.diario.v1': json.dumps([1, 'x', None, {'sem': 't'}, L_A]), 'capitao.docs.v1': json.dumps([{'sem': 'n'}, 7]),
                'capitao.executado.v1': json.dumps({'t7': 1, 't8': 'x', 't9': {'d': 1, 't': '09:00'}}),
                'capitao.equipe.v1': json.dumps({'fones': {'Cozinheiro': 5}, 'convites': [{'sem': 'nome'}, 'x']})}
        antes = ls()
        r = escolhe(arquivo(lixo))
        if r['previa'] or r['classe'] != 'ok' or 'Nada a restaurar' not in r['msg'] or 'ilegíveis' not in r['msg'] or 'Nada mudou' not in r['msg']:
            p.append('só ilegível: %r' % r['msg'])
        if ls() != antes: p.append('só ilegível: o aparelho mudou')
        lixo['capitao.diario.v1'] = json.dumps([1, L_E, 'x', L_A])
        r = escolhe(arquivo(lixo))
        if not r['previa'] or 'falta aqui 1 linha' not in r['resumo'] or '2 itens ilegíveis no arquivo ficam de fora' not in r['resumo']:
            p.append('ilegível ao lado de linha boa, prévia: %r' % r['resumo'])
        restaura()
        tudo, d = ls(), diario() or []
        if d.count(L_E) != 1 or len(d) != 5 or any(not isinstance(x, dict) for x in d): p.append('diário: %r' % d)
        if any(tudo.get(k) != antes.get(k) for k in ('capitao.docs.v1', 'capitao.executado.v1', 'capitao.equipe.v1')):
            p.append('item ilegível entrou: %r' % {k: tudo.get(k) for k in ('capitao.docs.v1', 'capitao.executado.v1', 'capitao.equipe.v1')})

        # 7) Desfeito depois não volta: nas telas, marca o Executado de uma tarefa atrasada (C1), cadastra um telefone e abre um
        # convite (G4); baixa a cópia; desfaz os três nas mesmas telas (o diário ganha as linhas). Restaurar: nada volta, a prévia
        # nomeia o que ficou de fora e a tarefa continua aberta. Num aparelho sem esse diário, a mesma cópia devolve os três.
        p = res['desfeito depois não volta'] = []
        ctx.route('https://wa.me/**', lambda rt: rt.abort())
        t = pg.evaluate("() => (window.CapitaoDados.agenda || []).filter((t) => t.dn < 0).map((t) => ({ id: t.id, t: t.t }))[0]")
        papel = pg.evaluate("() => ((window.CapitaoDados.equipe || {}).apoio || [])[0].papel")
        nome = 'Convidado do teste'

        def tela(arq):
            q = ctx.new_page()
            q.goto(BASE + arq, wait_until='load')
            q.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
            return q

        def fone(q, aria, valor):
            q.click('[aria-label="%s"]' % aria)
            q.fill('[aria-label="Telefone de %s"]' % papel, valor)
            q.click('button:has-text("SALVAR")')
            q.wait_for_timeout(200)

        c1, g4 = tela('C1-Leme-Web.dc.html'), tela('G4-Equipe-Web.dc.html')
        c1.click('[aria-label="Marcar como executado: %s"]' % t['t'])
        fone(g4, 'Cadastrar telefone de ' + papel, '00 0000 0000')
        g4.fill('[aria-label="Nome de quem vai receber o convite"]', nome)
        g4.fill('[aria-label="Celular com DDD ou e-mail"]', '(00) 0000-00000')
        with ctx.expect_page() as aba:
            g4.click('button:has-text("ENVIAR CONVITE")')
        aba.value.close()
        pg.reload(wait_until='load')
        with pg.expect_download() as dl:
            pg.click('#baixar')
        caminho2 = os.path.join(pasta, 'com-os-tres.json')
        dl.value.save_as(caminho2)
        dentro = json.loads(json.load(open(caminho2, encoding='utf-8'))['dados'].get('capitao.equipe.v1', '{}'))
        ex_arq = json.loads(json.load(open(caminho2, encoding='utf-8'))['dados'].get('capitao.executado.v1', '{}'))
        if t['id'] not in ex_arq or not dentro.get('convites') or not any(v == '00 0000 0000' for v in dentro.get('fones', {}).values()):
            p.append('a cópia não levou o Executado, o telefone e o convite feitos nas telas')
        c1.click('button:has-text("Desfazer")')
        fone(g4, 'Editar telefone de ' + papel, '')
        g4.click('[aria-label="Cancelar convite de %s"]' % nome)
        g4.wait_for_timeout(200)
        pg.reload(wait_until='load')
        antes = ls()
        if t['id'] in json.loads(antes.get('capitao.executado.v1') or '{}'): p.append('o Desfazer da C1 não tirou a marca')
        r = escolhe(caminho2)
        for falta in (t['t'], 'telefone de ' + papel, 'convite de ' + nome):
            if falta not in r['msg']: p.append('a mensagem não diz que fica de fora: %s · %r' % (falta, r['msg']))
        if r['previa'] or 'Nada mudou' not in r['msg']: p.append('restaurar o desfeito: %r' % r['msg'])
        if ls() != antes: p.append('o aparelho mudou: %r' % {k: v for k, v in ls().items() if antes.get(k) != v})
        c1.reload(wait_until='load')
        c1.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
        if not c1.is_visible('[aria-label="Marcar como executado: %s"]' % t['t']): p.append('a tarefa %s não continua aberta na C1' % t['id'])
        c1.close(); g4.close()
        pg.evaluate("() => { const s = localStorage.getItem('capitao.sessao.v1'); localStorage.clear(); localStorage.setItem('capitao.sessao.v1', s); }")
        pg.reload(wait_until='load')
        r = escolhe(caminho2)
        for volta in (t['t'], 'telefone de ' + papel, 'convite de ' + nome):
            if volta not in r['resumo']: p.append('aparelho sem o diário: a prévia não nomeia %s · %r' % (volta, r['resumo']))
        restaura()
        tudo = ls()
        eq = json.loads(tudo.get('capitao.equipe.v1') or '{}')
        if t['id'] not in json.loads(tudo.get('capitao.executado.v1') or '{}') or not eq.get('fones') or [c.get('nome') for c in eq.get('convites', [])] != [nome]:
            p.append('aparelho sem o diário: a cópia não devolveu os três: %r' % {k: tudo.get(k) for k in ('capitao.executado.v1', 'capitao.equipe.v1')})

        # 8) A cópia leva a posição gravada no diário (a linha do SOS: o registro fica intacto) e a página avisa.
        p = res['posição no arquivo e aviso'] = []
        sos = tela('S1-SOS-Web.dc.html')
        sos.wait_for_timeout(500)
        # F04 (1b): a tela do SOS só grava na ação (MAYDAY, MOB ou ligar), não ao abrir; o toque no roteiro do MAYDAY cria a linha que a cópia leva
        sos.locator('button[aria-pressed]:not([aria-label])', has_text='MAYDAY').first.click()
        sos.wait_for_function("() => JSON.parse(localStorage.getItem('capitao.diario.v1') || '[]').some((x) => /^SOS acionado/.test(x.t || ''))", timeout=8000)
        sos.close()
        pg.reload(wait_until='load')
        linha = [x for x in (diario() or []) if str(x.get('t', '')).startswith('SOS acionado')]
        with pg.expect_download() as dl:
            pg.click('#baixar')
        caminho3 = os.path.join(pasta, 'com-sos.json')
        dl.value.save_as(caminho3)
        no_arq = json.loads(json.load(open(caminho3, encoding='utf-8'))['dados'].get('capitao.diario.v1', '[]'))
        if len(linha) != 1 or linha[0] not in no_arq: p.append('a linha do SOS não foi intacta para a cópia: %r' % linha)
        leva = pg.inner_text('#leva')
        if 'posições do barco gravadas no diário' not in leva or 'SOS' not in leva or 'contatos de convite' not in leva:
            p.append('o aviso não diz que a cópia leva as posições do diário e os contatos de convite: %r' % leva)

        # 9) Ordem pela hora: o app grava a lista com a mais nova primeiro (unshift) e lê as primeiras (A2 "último", diarioLer e a
        # ficha da IA). A linha que entra vai pela hora, mesmo sem linha em comum com o aparelho; a sem hora fica na ordem do arquivo;
        # as do aparelho não trocam de lugar entre si.
        p = res['ordem pela hora'] = []

        def letras(xs):
            return [str(x.get('t') or x.get('n') or '?').split(' ')[1] if isinstance(x, dict) else '?' for x in (xs or [])]

        # a) Cópia de outro aparelho, sem linha em comum: aparelho [A], arquivo [C, B] → [C, B, A], nas três listas.
        pg.evaluate(GRAVA_LS, {'capitao.diario.v1': json.dumps([L_A]), 'capitao.docs.v1': json.dumps([D_A]), 'capitao.abast.v1': json.dumps([N_A])})
        pg.reload(wait_until='load')
        escolhe(arquivo({'capitao.diario.v1': json.dumps([L_C, L_B]), 'capitao.docs.v1': json.dumps([D_C, D_B]), 'capitao.abast.v1': json.dumps([N_C, N_B])}))
        restaura()
        tudo = ls()
        for k, esp, rot in (('capitao.diario.v1', [L_C, L_B, L_A], 'diário'), ('capitao.docs.v1', [D_C, D_B, D_A], 'documentos'),
                            ('capitao.abast.v1', [N_C, N_B, N_A], 'abastecimentos')):
            v = json.loads(tudo.get(k) or 'null')
            if v != esp: p.append('sem linha em comum, %s: %s (esperado C, B, A)' % (rot, letras(v)))
        # b) A linha do arquivo é a mais nova de todas: aparelho [B, A], arquivo [E, X (sem hora), A] → [E, B, X, A]. O "último" do
        # A2 e os "Últimos registros do diário" do cérebro começam pela E.
        pg.evaluate(GRAVA_LS, {'capitao.diario.v1': json.dumps([L_B, L_A])})
        pg.reload(wait_until='load')
        escolhe(arquivo({'capitao.diario.v1': json.dumps([L_E, L_X, L_A])}))
        restaura()
        d = diario()
        if d != [L_E, L_B, L_X, L_A]: p.append('linha mais nova no arquivo: %s (esperado E, B, X, A)' % letras(d))
        a2 = tela('A2-Ponte-Mobile.dc.html')
        try:
            a2.wait_for_function("() => document.body.innerText.indexOf('último 24/10') >= 0", timeout=8000)
        except Exception:
            p.append('o A2 não mostra "último 24/10" (linha E) depois de restaurar')
        ult = a2.evaluate("() => window.CapitaoBrain.answer('últimos registros do diário', {}).text")
        topo = [l for l in ult.split('\n') if l.startswith('•')][:1]
        if not topo or 'Linha E' not in topo[0]: p.append('"últimos registros do diário" não começa pela linha E: %r' % ult[:200])
        a2.close()
    except Exception as e:  # um passo que não chega ao fim (botão escondido, prazo) vira falha do caso, não derruba a matriz
        p.append('não chegou ao fim: ' + str(e).splitlines()[0][:200])
    res['erro de script'] = list(erros)
    ctx.close()

    # 10) Os textos que a restauração reconhece continuam nas telas (as do app gravam o mesmo que as web, clicadas acima).
    p = res['textos de desfazer nas telas'] = []
    for tela_, trechos in TEXTOS_DESFEITO.items():
        fonte = open(os.path.join(RAIZ, tela_ + '.dc.html'), encoding='utf-8').read()
        for tr in trechos:
            if tr not in fonte: p.append('%s não grava mais %r: atualize junto o dados.html (regrasDesfeito)' % (tela_, tr))

    # 11) Atrás do login: sem sessão, a página vai para o login (e volta para ela depois de entrar).
    p = res['sem sessão'] = []
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, service_workers='block')
    pg = ctx.new_page()
    pg.goto(BASE + 'dados.html', wait_until='load')
    pg.wait_for_timeout(300)
    if 'login.html?next=dados.html' not in pg.url: p.append('sem sessão abriu %s' % pg.url)
    ctx.close()
    return res


# Login sem senha nenhuma: o deriveBits do navegador devolve o hash público (capitao-auth.js) do usuário cujo sal veio no
# pedido, seja qual for a senha digitada. Assim o teste confere a CHAVE que o login resolve, nunca a senha.
DERIVE_FALSO = """(() => {
  const MAPA = %s, S = window.SubtleCrypto && SubtleCrypto.prototype;
  if (!S) return;
  const b64 = (buf) => { let s = ''; new Uint8Array(buf).forEach((x) => { s += String.fromCharCode(x); }); return btoa(s); };
  S.deriveBits = function (alg, key, len) {
    const h = MAPA[b64(alg.salt)];
    return Promise.resolve(h ? Uint8Array.from(atob(h), (c) => c.charCodeAt(0)).buffer : new ArrayBuffer(len / 8));
  };
})()"""
SENHA_FALSA = 'nao-e-a-senha'  # qualquer texto: o deriveBits falso não olha a senha
KT = 'capitao.login.tentativas.v1'


def usuarios_auth():
    """{id: (nome, sal, hash)} lidos do capitao-auth.js (sal e hash são públicos; a senha não está em lugar nenhum)."""
    txt = open(os.path.join(RAIZ, 'capitao-auth.js'), encoding='utf-8').read()
    return {m.group(1): (m.group(2), m.group(3), m.group(4))
            for m in re.finditer(r"(\w+): \{ nome: '([^']+)'.*?sal: '([^']+)', hash: '([^']+)' \}", txt)}


def teste_login(b):
    """Convidado (decisão k da 1.1.0): o botão põe a chave, o nome fica no texto; as grafias que o cliente digita entram no mesmo
    id; a trava de 5 tentativas não sobe com "Convidado"; usuário que não existe conta erro. Ver o cabeçalho do arquivo."""
    res = {}
    us = usuarios_auth()
    mapa = json.dumps({sal: h for (_, sal, h) in us.values()})

    def abre(tentativas=None):
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, service_workers='block')
        ctx.add_init_script(DERIVE_FALSO % mapa)
        if tentativas is not None:  # erros anteriores (a página põe o "ult" de agora: dentro da 1 h que a trava considera)
            ctx.add_init_script("(() => { if (!sessionStorage.getItem('t')) { sessionStorage.setItem('t', '1'); localStorage.setItem('%s', JSON.stringify({ n: %d, ate: 0, ult: Date.now() })); } })()" % (KT, tentativas))
        # destino depois do login: página vazia (o teste lê a sessão nela, sem seguir para a tela inicial)
        ctx.route(re.compile(r'/index\.html(\?.*)?$'), lambda rt: rt.fulfill(status=200, content_type='text/html', body='<!doctype html><title>destino</title>'))
        pg = ctx.new_page()
        pg.goto(BASE + 'login.html', wait_until='load')
        pg.wait_for_function("() => document.querySelectorAll('.chip').length > 0", timeout=10000)
        return ctx, pg

    def entra(pg, valor):
        if valor is not None:
            pg.fill('#u', valor)
        pg.fill('#p', SENHA_FALSA)
        pg.click('#go')
        try:
            pg.wait_for_url(re.compile(r'/index\.html'), timeout=8000)
        except Exception:
            return {'url': pg.url, 'msg': pg.evaluate("() => document.getElementById('m').textContent"),
                    'kt': pg.evaluate("(k) => localStorage.getItem(k)", KT)}
        return {'url': pg.url, 'sessao': pg.evaluate("() => JSON.parse(localStorage.getItem('capitao.sessao.v1') || 'null')"),
                'kt': pg.evaluate("(k) => localStorage.getItem(k)", KT)}

    # 1) botões: texto = nome exibido, data-u = chave; o do convidado põe "demo" no campo e fica marcado
    p = res['botões do login'] = []
    ctx, pg = abre()
    chips = pg.evaluate("() => [...document.querySelectorAll('.chip')].map((c) => [c.textContent, c.getAttribute('data-u')])")
    esperado = [[nome.upper(), uid] for uid, (nome, _, _) in us.items()]
    if chips != esperado: p.append('botões %s (esperado %s)' % (chips, esperado))
    if ['CONVIDADO', 'demo'] not in chips: p.append('sem o botão CONVIDADO com a chave demo: %s' % chips)
    else:
        pg.click('.chip[data-u="demo"]')
        v = pg.evaluate("() => [document.getElementById('u').value, document.querySelector('.chip[data-u=\"demo\"]').getAttribute('aria-pressed')]")
        if v != ['demo', 'true']: p.append('o botão CONVIDADO pôs %r no campo (aria-pressed %s; esperado "demo", true)' % tuple(v))
        for txt in ('Convidado', ' DEMO ', 'Demo'):
            pg.fill('#u', txt)
            if pg.evaluate("() => document.querySelector('.chip[data-u=\"demo\"]').getAttribute('aria-pressed')") != 'true':
                p.append('digitar %r não marca o botão CONVIDADO' % txt)
    ids = pg.evaluate("""() => { const A = window.CapitaoAuth; if (!A || typeof A.idDe !== 'function') return 'CapitaoAuth.idDe ausente';
      return ['demo', 'Demo', ' DEMO ', 'Convidado', 'CONVIDADO', 'convidado ', 'Lucas Araújo', 'constructor', 'toString'].map((x) => A.idDe(x)); }""")
    if ids != ['demo'] * 6 + ['lucas', 'constructor', 'tostring']: p.append('normalização do login: %s' % ids)
    ctx.close()

    # 2) cada grafia entra como demo, sem senha nenhuma e sem erro na trava
    p = res['grafias do convidado'] = []
    for valor in ('demo', 'Demo', ' DEMO ', 'Convidado', None):
        ctx, pg = abre()
        rot = 'botão CONVIDADO' if valor is None else repr(valor)
        if valor is None:  # o valor que o botão põe
            if not pg.locator('.chip[data-u="demo"]').count():
                p.append('sem o botão com a chave demo'); ctx.close(); continue
            pg.click('.chip[data-u="demo"]')
        r = entra(pg, valor)
        if not r.get('sessao') or r['sessao'].get('u') != 'demo': p.append('%s não entrou como demo: %s' % (rot, r))
        elif r['kt'] is not None: p.append('%s entrou mas deixou a trava %s' % (rot, r['kt']))
        ctx.close()

    # 3) a trava: com 4 erros antes, "Convidado" entra e zera a trava (com o nome no campo, seria o 5º erro e travaria)
    p = res['trava com Convidado'] = []
    ctx, pg = abre(tentativas=4)
    if pg.evaluate("(k) => JSON.parse(localStorage.getItem(k)).n", KT) != 4: p.append('a trava semeada não ficou em 4')
    r = entra(pg, 'Convidado')
    if not r.get('sessao') or r['sessao'].get('u') != 'demo': p.append('"Convidado" com 4 erros na trava não entrou: %s' % r)
    elif r['kt'] is not None: p.append('"Convidado" entrou mas a trava ficou %s' % r['kt'])
    ctx.close()

    # 4) contraprova: usuário que não existe não entra (o deriveBits falso não abre a porta) e conta 1 erro
    p = res['usuário que não existe'] = []
    ctx, pg = abre()
    r = entra(pg, 'visitante')
    n = json.loads(r['kt'])['n'] if r.get('kt') else 0
    if r.get('sessao') or 'login.html' not in r['url'] or n != 1 or 'incorretos' not in (r.get('msg') or ''):
        p.append('"visitante": %s (esperado ficar no login com 1 erro na trava)' % r)
    ctx.close()
    return res


def teste_equipe_convidado(b, tela):
    """Equipe com o convidado logado (decisão k): nome Convidado, papel convidado · fora da lista da embarcação, sem A CONFIRMAR."""
    movel = eh_app(tela)
    w, h = (APP if movel else WEB)[0]
    ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None,
                        is_mobile=movel, has_touch=movel, service_workers='block')
    ctx.add_init_script("(() => { const n = Date.now(); localStorage.setItem('capitao.sessao.v1', JSON.stringify({ u: 'demo', em: n, exp: n + 3600e3 })); })()")
    pg = ctx.new_page()
    prob = []
    pg.goto(BASE + tela + '.dc.html', wait_until='load')
    try:
        pg.wait_for_function("() => document.getElementById('dc-root') && /fora da lista da embarca/.test(document.body.innerText)", timeout=15000)
    except Exception:
        prob.append('o perfil do convidado não apareceu em 15 s')
    r = pg.evaluate("""() => ({ linhas: document.body.innerText.split('\\n').filter((l) => /fora da lista da embarca/.test(l)),
      texto: document.body.innerText, rodape: [...document.querySelectorAll('capitao-rodape')].map((e) => e.textContent).join(' '),
      selo: """ + SELO_TEXTO + """ })""")
    if not r['linhas'] or any('convidado · fora da lista da embarcação' not in l or 'A CONFIRMAR' in l for l in r['linhas']):
        prob.append('linha do perfil: %s' % r['linhas'][:2])
    if 'Convidado' not in r['texto'] or 'CONVIDADO' not in r['texto']: prob.append('sem o nome Convidado ou o chip CONVIDADO')
    # DEMO, Demo ou demonstração escritos no código da tela (antes só Demo/demonstração, e o "(DEMO)" fixo da fonte das regras de
    # acesso passava); o que ainda vem do capitao-dados.js fica de fora (SELO_TEXTO; os títulos saíram no C2)
    if r['selo']: prob.append('o convidado ainda vê DEMO/Demo/demonstração: %s' % r['selo'][:3])
    if 'Convidado' not in r['rodape']: prob.append('rodapé sem o usuário Convidado: %r' % r['rodape'][:120])
    ctx.close()
    return prob


# ——— P4C: a Ponte (A1 a A5), o gráfico compartilhado (capitao-grafico.js) e o mapa de sensores (capitao-sensores.js) ———
# PROMPT Fase 4 «Gráficos» e linha P4C; PARIDADE F05 (lista de alertas), F06 (selo), F07/F33 (gráfico), F08 (sensores), F11 (tendências). Cada conferência abaixo tem um defeito plantado que a faz falhar
# (MUTANTES_P4C, rodados com --mutantes-p4c): o teste só vale se acusa o defeito.
TELAS_PONTE = ('A1-Ponte-Web', 'A2-Ponte-Mobile')
TELAS_SENSORES = ('A4-Sensores-Web', 'A5-Sensores-Mobile')
TELAS_P4C = TELAS_PONTE + ('A3-Ponte-Editar',) + TELAS_SENSORES


def abre_tela(b, tela, w=None, h=None, fixo='60', tema='escuro', depois='', hash_='', ls=None):
    """A tela com sessão, o replay congelado em `fixo` s (None = livre), o tema, `depois` somado ao fim do capitao-dados.js (a flag, o inventário…) e localStorage `ls` posto antes da carga."""
    movel = eh_app(tela)
    if w is None: w, h = (390, 844) if movel else (1440, 900)
    ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None, is_mobile=movel, has_touch=movel, service_workers='block')
    init = SESSAO + ";localStorage.setItem('capitao.tema.v1', '%s');localStorage.setItem('capitao.plataforma.v1', '%s');" % (tema, 'app' if movel else 'web')
    if fixo: init += "try { localStorage.setItem('capitao.replay.fixo', '%s'); } catch (e) {}" % fixo
    for k, v in (ls or {}).items(): init += "localStorage.setItem(%s, %s);" % (json.dumps(k), json.dumps(v))
    ctx.add_init_script(init)
    ctx.add_init_script(ESPIA_FALA)
    aplica_mut(ctx)
    if depois:
        def injeta(route):
            r = route.fetch()
            route.fulfill(response=r, body=r.text() + '\n' + depois)
        ctx.route('**/capitao-dados.js', injeta)
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
    pg.on('console', lambda m: erros.append('console: ' + m.text[:300]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    pg.goto(BASE + tela + '.dc.html' + hash_, wait_until='load')
    try:
        pg.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
    except Exception:
        erros.append('prancheta não desenhou em 15 s')
    pg.wait_for_timeout(1300)
    return ctx, pg, erros


# o JS comum: o instante, o texto de cada campo (a mesma CapitaoAgora.fmt.campo da moldura e do cérebro) e um achatador de espaços
JS_BASE = """const A = window.CapitaoAgora, F = A.fmt, I = A.instante(), q = I.q, D = window.CapitaoDados, T = {}; Object.keys(D.campos).forEach((c) => { T[c] = F.campo(q, c); });
  const lin = (s) => (s || '').replace(/\\s+/g, ' ').trim();"""

# ——— o gráfico: cada métrica × cada janela, nos dois temas, com o cursor, o ponto «agora» e sem NaN ———
CLICA_GRUPO = """([grupo, texto]) => { const g = document.querySelector('[role=group][aria-label="' + grupo + '"]'); const bt = g && [...g.querySelectorAll('button')].find((x) => x.innerText.trim() === texto);
  if (!bt) return false; bt.click(); return true; }"""
LE_GRAFICO = """() => { """ + JS_BASE + """
  const raiz = document.querySelector('[data-capitao-grafico]'), svg = raiz && raiz.querySelector('svg');
  if (!svg) return { sem: true, vazio: raiz ? raiz.getAttribute('data-vazio') : null, texto: raiz ? lin(raiz.innerText) : '' };
  const html = svg.outerHTML, pts = (d) => [...d.matchAll(/[ML]([-\\d.]+),([-\\d.]+)/g)].map((m) => [+m[1], +m[2]]);
  const linhas = [...svg.querySelectorAll('path[d]')].filter((p) => p.getAttribute('fill') === 'none' && p.getAttribute('stroke-width') === '2').map((p) => ({ d: p.getAttribute('d'), n: (p.getAttribute('d').match(/M/g) || []).length, pts: pts(p.getAttribute('d')) }));
  const dots = [...svg.querySelectorAll('circle[data-agora]')].map((c) => ({ campo: c.getAttribute('data-campo'), v: c.getAttribute('data-agora'), esperado: T[c.getAttribute('data-campo')], cx: +c.getAttribute('cx'), cy: +c.getAttribute('cy') }));
  const leg = raiz.querySelector('[data-legenda]'), vb = svg.getAttribute('viewBox').split(' ').map(Number);
  return { met: raiz.getAttribute('data-capitao-grafico'), jan: raiz.getAttribute('data-janela'), ruim: /NaN|undefined|Infinity|null/.test(html), linhas, dots, nTexto: svg.querySelectorAll('text').length, vb,
    legenda: leg ? lin(leg.innerText) : '', titulo: leg ? leg.getAttribute('title') : '', aria: svg.getAttribute('aria-label') }; }"""
JAN_ID = {'150 s': '150S', '1 D': '1D', '7 D': '7D', '30 D': '30D', '1 A': '1A'}
SO150 = ('Rotação', 'Óleo', 'Arrefecimento')
CURSOR_JS = """async (x) => { const svg = document.querySelector('[data-capitao-grafico] svg'), r = svg.getBoundingClientRect(), n0 = svg.querySelectorAll('line').length;
  const ev = (t, fx) => svg.dispatchEvent(new PointerEvent(t, { bubbles: true, clientX: r.left + fx * r.width, clientY: r.top + r.height / 2, pointerType: 'mouse', relatedTarget: t === 'pointerout' ? document.body : null }));
  ev('pointermove', x); await new Promise((ok) => setTimeout(ok, 120));
  const cx = document.querySelector('[data-cursor=caixa]'), dentro = { texto: cx ? cx.innerText.replace(/\\s+/g, ' ').trim() : null, linhas: svg.querySelectorAll('line').length - n0, pontos: svg.querySelectorAll('circle').length };
  ev('pointerout', x); await new Promise((ok) => setTimeout(ok, 120));
  return { dentro, saiu: document.querySelector('[data-cursor=caixa]') === null }; }"""
CONTRASTE_JS = """() => { const raiz = document.querySelector('[data-capitao-grafico]'), card = raiz.closest('section'), svg = raiz.querySelector('svg');
  const rgb = (s) => (s.match(/[\\d.]+/g) || []).slice(0, 3).map(Number), lum = (c) => { const f = c.map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]; };
  const cr = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }, bg = rgb(getComputedStyle(card).backgroundColor);
  return { bg, txt: Math.min(...[...svg.querySelectorAll('text')].map((t) => cr(rgb(getComputedStyle(t).fill), bg))), linha: Math.min(...[...svg.querySelectorAll('path[stroke-width="2"]')].map((p) => cr(rgb(getComputedStyle(p).stroke), bg))), tema: document.documentElement.getAttribute('data-capitao-tema') }; }"""


def teste_grafico(b, tela):
    prob = []
    ctx, pg, erros = abre_tela(b, tela)
    ordem = pg.evaluate("() => window.CapitaoGrafico.ORDEM")
    nomes = pg.evaluate("() => window.CapitaoGrafico.ORDEM.map((k) => window.CapitaoGrafico.rotulo(k))")
    if len(ordem) != 10: prob.append('as métricas do gráfico são %d (esperado 10: baterias, temperaturas, vento, pressão, água, servidas, diesel, rotação, óleo e arrefecimento)' % len(ordem))
    n = 0
    for k, nome in zip(ordem, nomes):
        if not pg.evaluate(CLICA_GRUPO, ['Série', nome]): prob.append('sem o botão da série %s' % nome); continue
        for jr, jid in JAN_ID.items():
            esperada = '150S' if nome in SO150 else jid
            pg.evaluate(CLICA_GRUPO, ['Período', jr])
            try:
                pg.wait_for_function("([m, j]) => { const r = document.querySelector('[data-capitao-grafico]'); return !!r && r.getAttribute('data-capitao-grafico') === m && r.getAttribute('data-janela') === j; }", arg=[k, esperada], timeout=4000)
            except Exception:
                prob.append('%s × %s: o gráfico não trocou para %s/%s' % (nome, jr, k, esperada)); continue
            r = pg.evaluate(LE_GRAFICO)
            rot = '%s × %s' % (nome, jr)
            n += 1
            if r.get('sem'): prob.append('%s: sem gráfico (%s %s)' % (rot, r.get('vazio'), r.get('texto'))); continue
            if r['ruim']: prob.append('%s: NaN, undefined, Infinity ou null dentro do SVG' % rot)
            if not r['linhas'] or len(r['linhas']) != len(r['dots']): prob.append('%s: %d linhas para %d pontos «agora»' % (rot, len(r['linhas']), len(r['dots'])))
            for ln in r['linhas']:
                if len(ln['pts']) < 2:   # (uma linha com NaN no d não tem pontos que a regex leia)
                    prob.append('%s: linha sem pontos legíveis: %s' % (rot, ln['d'][:80])); continue
                xs = [p[0] for p in ln['pts']]
                if ln['n'] != 1 or len(xs) < 2: prob.append('%s: a linha não é contínua (%d trechos, %d pontos)' % (rot, ln['n'], len(xs)))
                if any(b_ < a_ for a_, b_ in zip(xs, xs[1:])): prob.append('%s: a linha volta no tempo' % rot)
                if any(not (0 <= v <= r['vb'][2]) for v in xs) or any(not (0 <= p[1] <= r['vb'][3]) for p in ln['pts']): prob.append('%s: ponto da linha fora do desenho' % rot)
                if not any(abs(ln['pts'][-1][0] - dt['cx']) <= 0.2 and abs(ln['pts'][-1][1] - dt['cy']) <= 0.2 for dt in r['dots']): prob.append('%s: o ponto «agora» não está no fim da linha' % rot)
            for dt in r['dots']:
                if dt['v'] != dt['esperado']: prob.append('%s: o último ponto de %s é %r e o quadro de agora diz %r' % (rot, dt['campo'], dt['v'], dt['esperado']))
            if r['nTexto'] < 4: prob.append('%s: só %d rótulos de eixo' % (rot, r['nTexto']))
            if len(r['legenda']) < 8 or not re.search(r'\d', r['legenda']): prob.append('%s: legenda vazia ou sem número: %r' % (rot, r['legenda']))
            if not r['aria'] or 'NaN' in r['aria']: prob.append('%s: aria-label do gráfico: %r' % (rot, r['aria']))
        if nome in SO150:   # as métricas do laço só têm a janela de 150 s: os outros botões ficam desativados
            off = pg.evaluate("() => [...document.querySelectorAll('[role=group][aria-label=\"Período\"] button')].map((x) => [x.innerText.trim(), x.getAttribute('aria-disabled')])")
            if [x[0] for x in off if x[1] == 'true'] != ['1 D', '7 D', '30 D', '1 A']: prob.append('%s: botões desativados %s (esperado 1 D, 7 D, 30 D e 1 A)' % (nome, off))
    # o cursor: linha no instante, pontos nas séries, caixa com a hora e os valores com unidade; some ao sair
    for met, jr, formato in (('Baterias', '7 D', r'\d\d/\d\d \d\d:\d\d'), ('Rotação', '150 s', r'\d\d:\d\d:\d\d')):
        pg.evaluate(CLICA_GRUPO, ['Série', met]); pg.evaluate(CLICA_GRUPO, ['Período', jr]); pg.wait_for_timeout(200)
        c = pg.evaluate(CURSOR_JS, 0.5)
        tx = c['dentro']['texto']
        if not tx or not re.search(formato, tx) or not re.search(r'\d', tx.split(' ', 2)[-1]): prob.append('cursor de %s × %s: caixa %r (esperado a hora no formato %s e os valores)' % (met, jr, tx, formato))
        elif met == 'Baterias' and not all(u in tx for u in ('serviço 24 V', 'partida 24 V', 'banco 12 V', ' V')): prob.append('cursor das baterias sem as 3 séries com unidade: %r' % tx)
        elif met == 'Rotação' and not all(u in tx for u in ('motor BB', 'motor BE', 'rpm')): prob.append('cursor da rotação sem os dois motores com unidade: %r' % tx)
        if c['dentro']['linhas'] < 1 or c['dentro']['pontos'] < 2: prob.append('cursor de %s: sem a linha vertical (%s) ou os pontos nas séries (%s)' % (met, c['dentro']['linhas'], c['dentro']['pontos']))
        if not c['saiu']: prob.append('cursor de %s: a caixa não some ao sair' % met)
    if erros: prob += erros[:2]
    ctx.close()
    # claro e escuro: texto do eixo ≥ 3:1 e linhas das séries ≥ 3:1 contra o cartão (as variáveis do tema chegam ao SVG)
    for tema in ('escuro', 'claro'):
        ctx, pg, erros = abre_tela(b, tela, tema=tema)
        pg.evaluate(CLICA_GRUPO, ['Série', 'Baterias']); pg.wait_for_timeout(300)
        c = pg.evaluate(CONTRASTE_JS)
        if c['tema'] != tema or c['txt'] < 3 or c['linha'] < 3: prob.append('gráfico no tema %s: contraste do texto %.1f e das linhas %.1f contra o cartão %s (esperado ≥ 3)' % (tema, c['txt'], c['linha'], c['bg']))
        if erros: prob += erros[:2]
        ctx.close()
    # livre: a janela de 150 s anda com o replay (a linha muda em 1,6 s e o último ponto avança)
    ctx, pg, erros = abre_tela(b, tela, fixo=None)
    pg.evaluate(CLICA_GRUPO, ['Série', 'Rotação']); pg.evaluate(CLICA_GRUPO, ['Período', '150 s']); pg.wait_for_timeout(600)
    d1 = pg.evaluate("() => [document.querySelector('[data-capitao-grafico] path[stroke-width=\"2\"]').getAttribute('d'), window.CapitaoGrafico.dados('rpm', '150S').t1]")
    pg.wait_for_timeout(1700)
    d2 = pg.evaluate("() => [document.querySelector('[data-capitao-grafico] path[stroke-width=\"2\"]').getAttribute('d'), window.CapitaoGrafico.dados('rpm', '150S').t1]")
    if d1[0] == d2[0] or d2[1] - d1[1] < 1000: prob.append('livre: a janela de 150 s não andou em 1,7 s (linha igual %s, último ponto +%d ms)' % (d1[0] == d2[0], d2[1] - d1[1]))
    if erros: prob += erros[:2]
    ctx.close()
    if n != 50: prob.append('%d combinações métrica × janela conferidas (esperado 50: 10 métricas × 5 janelas; as do laço de 150 s caem na janela de 150 s)' % n)
    return prob


# ——— A1 e A2: os blocos ao vivo, a lista de alertas, as tendências e o cartão do mapa de sensores ———
FAB_FALSOS = ("(() => { const E = window.CapitaoDados.equipamentos, z = { motores: 'Zyxmotor', gerador: 'Zyxgerador', estabilizador: 'Zyxestab' }; "
              "E.forEach((e) => { if (z[e.id]) { e.fabricante = z[e.id]; e.modelo = z[e.id] + ' Mod9'; } }); })();")
PED_FOGO = [{'id': 'usr_1', 'campo': 'motor_bb_arref_c', 'op': '>', 'limite': 80, 'iso': '2026-11-09T10:00:00-03:00', 'who': 'Lucas', 'sim': True}]
LE_A1 = """() => { """ + JS_BASE + """
  const art = (nome) => [...document.querySelectorAll('article')].find((a) => { const h = a.querySelector('h2'); return h && lin(h.innerText).indexOf(nome) === 0; });
  const t = (nome) => lin((art(nome) || { innerText: '' }).innerText);
  const chips = [...document.querySelectorAll('section[aria-label="Mapa de sensores"] [title]')].filter((e) => /\\bna rede\\b|SEM LEITURA/.test(e.getAttribute('title') || '')).map((e) => ({ texto: lin(e.innerText), titulo: e.getAttribute('title') }));
  const mapa = document.querySelector('section[aria-label="Mapa de sensores"] > a');
  const tit = document.querySelector('[data-alertas=titulo]'), itens = [...document.querySelectorAll('[data-alerta]')].map((e) => ({ id: e.getAttribute('data-alerta'), texto: lin(e.innerText), href: e.getAttribute('href'), aria: e.getAttribute('aria-label') }));
  const fx = document.getElementById('capitao-faixa-alertas'), nota = document.querySelector('[data-selo]'), tab = (n) => [...document.querySelectorAll('[role=tab]')].find((b) => lin(b.innerText).indexOf(n) === 0);
  const cel = (txt) => [...document.querySelectorAll('article[aria-label="Motores"] span')].find((e) => e.children.length === 0 && lin(e.innerText) === txt);
  const probe = document.createElement('span'); probe.style.color = 'var(--cap-warn, #f0a63a)'; document.body.appendChild(probe); const warn = getComputedStyle(probe).color; probe.remove();
  return { T, fase: I.fase ? I.fase.nome : '', coord: F.coord(q.lat, q.lon), q: { ancora: q.ancora_estado, ciclos: q.bomba_porao_ciclos, marcha: q.marcha, estado: q.estado, local: q.local }, nav: t('Navegação'), amb: t('Ambiente'), ene: t('Energia'), tan: t('Tanques'), mot: t('Motores'), chips,
    mapa: mapa ? { href: mapa.getAttribute('href'), texto: lin(mapa.innerText) } : null, alertasTitulo: tit ? lin(tit.innerText) : null, itens, faixa: fx && !fx.hidden ? lin(fx.innerText) : '',
    nota: nota ? { tom: nota.getAttribute('data-selo'), texto: lin(nota.innerText) } : null, abas: [...document.querySelectorAll('[role=tab]')].map((x) => [lin(x.innerText), x.getAttribute('aria-selected')]),
    corArref: (() => { const c = cel(T.motor_be_arref_c); return c ? getComputedStyle(c).color : null; })(), warn, texto: lin(document.body.innerText),
    ativos: window.CapitaoAlertas.ativos().map((a) => ({ id: a.id, texto: a.texto, hora: a.hora, detalhe: a.detalhe })), pedidos: window.CapitaoBrain.alarmesPedidosAtivos().map((a) => ({ id: a.id, texto: a.texto, desdeTxt: a.desdeTxt })), eqs: D.equipamentos.map((e) => [e.id, e.fabricante, e.modelo]) }; }"""
LE_TENDENCIAS = """() => { const B = window.CapitaoBrain, lin = (s) => (s || '').replace(/\\s+/g, ' ').trim(), el = [...document.querySelectorAll('[data-tendencia]')];
  const lk = [...document.querySelectorAll('[role=tabpanel] a')].find((a) => /Ver tendências/.test(a.innerText));
  return { itens: el.map((e) => ({ id: e.getAttribute('data-tendencia'), texto: lin(e.innerText), fonte: e.getAttribute('title') })), api: B.preditiva().map((x) => ({ id: x.id, nivel: x.nivel, texto: x.texto, titulo: x.titulo })), href: lk ? lk.getAttribute('href') : null }; }"""


def sem_rotulo(txt):
    """Os termos do §3 (VARREDURA) no texto da tela: o mesmo critério do roda_tela."""
    return achados_termos('A1-Ponte-Web', txt)


def teste_ponte_web(b):
    """A1: o texto de cada bloco é o do quadro (CapitaoAgora.fmt.campo, a mesma conta da moldura e do cérebro), sem rótulo, o selo F06 pela cor, a lista de alertas igual à faixa, as tendências do
    cérebro e o cartão do mapa de sensores; fabricante e modelo de D.equipamentos (nunca fixos); tudo a 60 s e a 105 s."""
    prob = []
    guarda = {}
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_tela(b, 'A1-Ponte-Web', fixo=fixo)
        r = pg.evaluate(LE_A1)
        T = r['T']
        rot = 'A1 a %s s' % fixo
        achei = lambda txt, *xs: [x for x in xs if x not in txt]
        f = achei(r['nav'], T['sog_nos'], T['proa_graus'] + '°', r['coord'], T['profundidade_m'] + ' m', T['gps_satelites'], 'Navegando')
        if f: prob.append('%s: o bloco Navegação não mostra %s: %r' % (rot, f, r['nav']))
        f = achei(r['amb'], T['vento_verdadeiro_nos'] + ' nós', T['pressao_barometrica_hpa'] + ' hPa', T['temp_ar_externo_c'] + ' °C', T['temp_agua_c'] + ' °C', 'A bordo agora')
        if f: prob.append('%s: o bloco Ambiente não mostra %s: %r' % (rot, f, r['amb']))
        f = achei(r['ene'], T['bateria_0_tensao_v'] + ' V', T['bateria_2_tensao_v'] + ' V', 'ligado · ' + T['gerador_kw'] + ' kW', T['gerador_horimetro_h'] + ' h', 'ligado · ' + T['seakeeper_volante_pct'] + ' %')
        if f: prob.append('%s: o bloco Energia não mostra %s: %r' % (rot, f, r['ene']))
        f = achei(r['tan'], T['tanque_agua_pct'] + ' %', T['tanque_cinzas_pct'] + ' %', T['tanque_negras_pct'] + ' %', T['diesel_bb_pct'] + ' %', T['diesel_be_pct'] + ' %', T['diesel_litros'] + ' L')
        if f: prob.append('%s: o bloco Tanques não mostra %s: %r' % (rot, f, r['tan']))
        nums = [T[c] for c in ('motor_bb_rpm', 'motor_be_rpm', 'motor_bb_oleo_bar', 'motor_be_oleo_bar', 'motor_bb_arref_c', 'motor_be_arref_c', 'motor_bb_carga_pct', 'motor_be_carga_pct', 'motor_bb_horimetro_h', 'motor_be_horimetro_h')]
        f = achei(r['mot'], *nums)
        if f: prob.append('%s: o bloco Motores não mostra %s: %r' % (rot, f, r['mot']))
        if not re.search(r'Ligados · %s · marcha %s' % (r['fase'], r['q']['marcha']), r['mot']): prob.append('%s: o estado dos motores devia ser «Ligados · %s · marcha %s»: %r' % (rot, r['fase'], r['q']['marcha'], r['mot'][:120]))
        if r['fase'] != 'cruzeiro': prob.append('%s: a fase do replay é %r (esperado cruzeiro)' % (rot, r['fase']))
        if re.search(r'última leitura|ultima leitura', r['mot'], re.I): prob.append('%s: o bloco dos motores ainda fala de «última leitura»' % rot)
        # os 12 sensores com valor, o porão e a âncora também
        if len(r['chips']) != 12 or any(re.search(r'SEM LEITURA|—', c['texto']) for c in r['chips']): prob.append('%s: %d sensores no mapa, com SEM LEITURA ou «—»: %s' % (rot, len(r['chips']), [c['texto'] for c in r['chips'] if re.search(r'SEM LEITURA|—', c['texto'])]))
        porao = [c for c in r['chips'] if c['texto'].startswith('Porão')]
        ancora = [c for c in r['chips'] if c['texto'].startswith('Âncora')]
        if not porao or 'BB ' + T['porao_bb_nivel'] + ' · BE ' + T['porao_be_nivel'] + ' cm' not in porao[0]['texto']: prob.append('%s: o chip do porão não mostra o nível do quadro: %s' % (rot, porao))
        if not ancora or r['q']['ancora'] not in ancora[0]['texto']: prob.append('%s: o chip da âncora não mostra %r: %s' % (rot, r['q']['ancora'], ancora))
        if not r['mapa'] or r['mapa']['href'] != 'A4-Sensores-Web.dc.html' or 'Mapa de sensores ›' not in r['mapa']['texto'] or '22 de 22 na rede' not in r['mapa']['texto']: prob.append('%s: o cartão «Mapa de sensores ›» → A4: %s' % (rot, r['mapa']))
        # selo F06 e o texto de cada alerta
        if not r['nota'] or r['nota']['tom'] != 'ok' or not re.fullmatch(r'Ao vivo · \d\d:\d\d', r['nota']['texto']): prob.append('%s: o selo da página devia ser verde «Ao vivo · HH:MM»: %s' % (rot, r['nota']))
        ach = sem_rotulo(r['texto'])
        if ach: prob.append('%s: termo do §3 no texto: %s' % (rot, ach))
        if fixo == '60':
            if r['alertasTitulo'] != 'Nenhum alerta ativo' or r['itens']: prob.append('A1 a 60 s: devia ter «Nenhum alerta ativo», e tem %r %s' % (r['alertasTitulo'], r['itens']))
        else:
            ids = [i['id'] for i in r['itens']]
            if r['alertasTitulo'] != '1 alerta ativo' or ids != ['arref_be']: prob.append('A1 a 105 s: a lista tem %r %s (esperado 1 alerta ativo: arref_be)' % (r['alertasTitulo'], ids))
            a0 = r['itens'][0] if r['itens'] else {}
            if not r['ativos'] or r['ativos'][0]['texto'] not in a0.get('texto', '') or ('desde ' + r['ativos'][0]['hora']) not in a0.get('texto', ''): prob.append('A1 a 105 s: o 1º item devia ser o da CapitaoAlertas (%s) com «desde %s»: %s' % (r['ativos'][:1], r['ativos'][0]['hora'] if r['ativos'] else '', a0))
            if a0.get('href') != 'C3-Leme-Alerta.dc.html#alarme=arref_be': prob.append('A1 a 105 s: o alerta leva a %r (esperado a C3 com #alarme=arref_be)' % a0.get('href'))
            if r['ativos'] and r['ativos'][0]['texto'] not in r['faixa']: prob.append('A1 a 105 s: a faixa do topo diz %r e a lista %r: não são a mesma lista' % (r['faixa'], r['ativos'][0]['texto']))
            if r['corArref'] != r['warn']: prob.append('A1 a 105 s: o arrefecimento do BE (%s) não está na cor de AVISO (%s): %s' % (T['motor_be_arref_c'], r['warn'], r['corArref']))
        # as tendências: a aba, os 5 achados do cérebro (na ordem dele) e o link
        pg.evaluate("() => [...document.querySelectorAll('[role=tab]')].find((x) => /^Tendências/.test(x.innerText.trim())).click()")
        pg.wait_for_selector('[data-tendencia]', timeout=4000)
        td = pg.evaluate(LE_TENDENCIAS)
        if [i['id'] for i in td['itens']] != [x['id'] for x in td['api']] or len(td['itens']) != 5: prob.append('%s: as tendências da tela %s não são as 5 do cérebro %s' % (rot, [i['id'] for i in td['itens']], [x['id'] for x in td['api']]))
        if not td['href'] or not td['href'].startswith('Main.dc.html#q='): prob.append('%s: o link «Ver tendências ›» leva a %r' % (rot, td['href']))
        if any(not i['fonte'] for i in td['itens']): prob.append('%s: tendência sem a fonte no title' % rot)
        guarda[fixo] = {i['id']: i['texto'] for i in td['itens']}
        ach = sem_rotulo(pg.evaluate("() => document.body.innerText"))
        if ach: prob.append('%s: termo do §3 na aba Tendências: %s' % (rot, ach))
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    # com um alarme pedido no chat (arrefecimento do BB acima de 80 °C): a lista junta os dois, na ordem da faixa (o mais antigo primeiro: o pedido começou antes do aviso do BE)
    ctx, pg, erros = abre_tela(b, 'A1-Ponte-Web', fixo='105', ls={'capitao.alarmes.v1': json.dumps(PED_FOGO)})
    r = pg.evaluate(LE_A1)
    ids = [i['id'] for i in r['itens']]
    if r['alertasTitulo'] != '2 alertas ativos' or ids != ['usr_1', 'arref_be']: prob.append('A1 a 105 s com o alarme pedido: a lista tem %r %s (esperado 2 alertas ativos: usr_1 e arref_be, o mais antigo primeiro)' % (r['alertasTitulo'], ids))
    if not r['pedidos'] or not r['itens'] or not r['itens'][0]['href'].startswith('Main.dc.html#q=') or r['pedidos'][0]['texto'] not in r['itens'][0]['texto'] or r['pedidos'][0]['texto'] not in r['faixa'] or r['pedidos'][0]['desdeTxt'] not in r['itens'][0]['texto']:
        prob.append('A1 com o alarme pedido: o 1º item da lista %s não é o que a faixa mostra (%r) nem o do cérebro %s' % (r['itens'][:1], r['faixa'], r['pedidos'][:1]))
    if erros: prob += erros[:2]
    ctx.close()
    # o alarme pedido sem começo conhecido (a SOG acima de 2 nós vale há mais de 160 s: desdeMs null) vai para o FIM da lista e diz «há mais de …» (o desdeTxt do cérebro), como na faixa
    ctx, pg, erros = abre_tela(b, 'A1-Ponte-Web', fixo='105', ls={'capitao.alarmes.v1': json.dumps([dict(PED_FOGO[0], campo='sog_nos', limite=2)])})
    r = pg.evaluate(LE_A1)
    ids = [i['id'] for i in r['itens']]
    if ids != ['arref_be', 'usr_1'] or not r['pedidos'] or not r['pedidos'][0]['desdeTxt'].startswith('há mais de') or r['pedidos'][0]['desdeTxt'] not in r['itens'][-1]['texto']:
        prob.append('A1 com o alarme pedido sem começo conhecido: a lista %s (esperado arref_be e, no fim, usr_1 com «há mais de …»); o cérebro diz %s' % ([(i['id'], i['texto'][-40:]) for i in r['itens']], r['pedidos'][:1]))
    if erros: prob += erros[:2]
    ctx.close()
    a60, a105 = guarda['60'].get('arref_agora', ''), guarda['105'].get('arref_agora', '')
    if 'dentro da faixa normal' not in a60 or 'AVISO desde' not in a105 or a60 == a105: prob.append('as tendências não mudam de 60 s para 105 s: %r → %r (o arrefecimento sai da faixa e vira AVISO)' % (a60, a105))
    # o fabricante e o modelo vêm do D.equipamentos (nunca fixos na tela): trocados na carga, a tela mostra os trocados
    ctx, pg, erros = abre_tela(b, 'A1-Ponte-Web', depois=FAB_FALSOS)
    r = pg.evaluate(LE_A1)
    if not r['mot'].startswith('Motores Zyxmotor') or 'modelo Zyxmotor Mod9' not in r['mot']: prob.append('fabricante e modelo dos motores trocados no D.equipamentos e a A1 não os mostra (título e modelo): %r' % r['mot'][:120])
    if 'Zyxgerador Mod9' not in r['ene'] or 'Zyxestab Mod9' not in r['ene']: prob.append('fabricante do gerador e do estabilizador trocados no D.equipamentos e a A1 não os mostra: %r' % r['ene'][-90:])
    if erros: prob += erros[:2]
    ctx.close()
    # o hash #alertas (o ABRIR › da faixa para os alarmes pedidos) abre a página sem erro
    ctx, pg, erros = abre_tela(b, 'A1-Ponte-Web', hash_='#alertas')
    if not pg.evaluate("() => !!document.getElementById('alertas') && !!document.querySelector('[data-alertas=titulo]')"): prob.append('A1#alertas: sem a seção de alertas')
    if erros: prob += erros[:2]
    ctx.close()
    return prob


LE_A2 = """() => { """ + JS_BASE + """
  const blocos = {}; [...document.querySelectorAll('a[aria-label]')].forEach((a) => { const m = /^([^—]+) — (.*)$/.exec(a.getAttribute('aria-label')); if (m) blocos[m[1].trim()] = m[2]; });
  const tit = document.querySelector('[data-alertas=titulo]'), itens = [...document.querySelectorAll('[data-alerta]')].map((e) => ({ id: e.getAttribute('data-alerta'), texto: lin(e.innerText), href: e.getAttribute('href') }));
  const tend = [...document.querySelectorAll('[data-tendencia]')].map((e) => e.getAttribute('data-tendencia')), fx = document.getElementById('capitao-faixa-alertas');
  const mapa = [...document.querySelectorAll('a[href]')].find((a) => /A5-Sensores-Mobile/.test(a.getAttribute('href')));
  const eq = (id) => D.equipamentos.find((e) => e.id === id) || {};
  return { T, blocos, alertasTitulo: tit ? lin(tit.innerText) : null, itens, tend, faixa: fx && !fx.hidden ? lin(fx.innerText) : '', mapa: mapa ? { href: mapa.getAttribute('href'), texto: lin(mapa.innerText) } : null, texto: lin(document.body.innerText),
    ativos: window.CapitaoAlertas.ativos().map((a) => ({ id: a.id, texto: a.texto })), api: window.CapitaoBrain.preditiva().map((x) => x.id), hhmm: I.hhmm, estado: q.estado, fab: { gerador: eq('gerador').fabricante, motores: eq('motores').fabricante }, nEq: D.equipamentos.length,
    ancora: q.ancora_estado, ciclos: q.bomba_porao_ciclos }; }"""


def teste_ponte_app(b):
    """A2: o estado de cada bloco do console é o do quadro (telemetria, navegação, gerador, sistemas, porão), sem rótulo; lista de alertas, tendências e o cartão do mapa de sensores."""
    prob = []
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_tela(b, 'A2-Ponte-Mobile', fixo=fixo, ls={'capitao.blocos.v1': json.dumps([{'id': i, 'label': i, 'icon': 'motor'} for i in ('telemetria', 'navegacao', 'gerador', 'sistemas', 'porao', 'estabilizador', 'posicao', 'clima')])})
        r = pg.evaluate(LE_A2)
        T = r['T']
        rot = 'A2 a %s s' % fixo
        if r['blocos'].get('Telemetria') != 'ao vivo ' + r['hhmm']: prob.append('%s: o bloco Telemetria diz %r (esperado «ao vivo %s»)' % (rot, r['blocos'].get('Telemetria'), r['hhmm']))
        esp = '%s · %s nós · %s°' % (r['estado'].lower(), T['sog_nos'], T['proa_graus'])
        if r['blocos'].get('Navegação') != esp: prob.append('%s: o bloco Navegação diz %r (esperado %r: estado, SOG e proa do quadro)' % (rot, r['blocos'].get('Navegação'), esp))
        esp = '%s · %s kW · %s h' % (r['fab']['gerador'], T['gerador_kw'], T['gerador_horimetro_h'])
        if not (r['blocos'].get('Gerador') or '').startswith(esp): prob.append('%s: o bloco Gerador diz %r (esperado %r: fabricante do inventário, kW e horas de agora)' % (rot, r['blocos'].get('Gerador'), esp))
        sis = r['blocos'].get('Sistemas') or ''
        if 'SEM DADOS' in sis or str(r['nEq']) + ' equipamentos' not in sis: prob.append('%s: o bloco Sistemas diz %r' % (rot, sis))
        esp = 'BB %s · BE %s cm · bomba %s %s/h' % (T['porao_bb_nivel'], T['porao_be_nivel'], r['ciclos'], 'ciclo' if r['ciclos'] == 1 else 'ciclos')
        if not (r['blocos'].get('Porão') or '').startswith(esp): prob.append('%s: o bloco Porão diz %r (esperado %r: nível e ciclos da bomba)' % (rot, r['blocos'].get('Porão'), esp))
        if 'Estabilizador' in r['blocos'] and (T['seakeeper_volante_pct'] + ' %') not in r['blocos']['Estabilizador']: prob.append('%s: o bloco Estabilizador diz %r' % (rot, r['blocos']['Estabilizador']))
        ach = achados_termos('A2-Ponte-Mobile', r['texto'] + ' ' + ' '.join(r['blocos'].values()))
        if ach: prob.append('%s: termo do §3: %s' % (rot, ach))
        if fixo == '60' and (r['alertasTitulo'] != 'Nenhum alerta ativo' or r['itens']): prob.append('A2 a 60 s: devia ter «Nenhum alerta ativo»: %r %s' % (r['alertasTitulo'], r['itens']))
        if fixo == '105':
            if r['alertasTitulo'] != '1 alerta ativo' or [i['id'] for i in r['itens']] != ['arref_be'] or r['itens'][0]['href'] != 'C3-Leme-Alerta.dc.html#alarme=arref_be': prob.append('A2 a 105 s: a lista de alertas %r %s (esperado o arref_be com o link da C3)' % (r['alertasTitulo'], r['itens']))
            if r['ativos'] and r['ativos'][0]['texto'] not in r['faixa']: prob.append('A2 a 105 s: a faixa %r e a lista %r não são a mesma' % (r['faixa'], r['ativos'][0]['texto']))
        if r['tend'] != r['api'] or len(r['tend']) != 5: prob.append('%s: as tendências da tela %s não são as 5 do cérebro %s' % (rot, r['tend'], r['api']))
        if not r['mapa'] or r['mapa']['href'] != 'A5-Sensores-Mobile.dc.html' or 'Mapa de sensores ›' not in r['mapa']['texto'] or '22 de 22 sensores na rede' not in r['mapa']['texto']: prob.append('%s: o cartão «Mapa de sensores ›» → A5: %s' % (rot, r['mapa']))
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    ctx, pg, erros = abre_tela(b, 'A2-Ponte-Mobile', depois=FAB_FALSOS, ls={'capitao.blocos.v1': json.dumps([{'id': 'gerador', 'label': 'Gerador', 'icon': 'motor'}, {'id': 'estabilizador', 'label': 'Estabilizador', 'icon': 'motor'}])})
    r = pg.evaluate(LE_A2)
    if not (r['blocos'].get('Gerador') or '').startswith('Zyxgerador') or 'Zyxestab Mod9' not in (r['blocos'].get('Estabilizador') or ''): prob.append('fabricante trocado no D.equipamentos e a A2 não o mostra: %s' % r['blocos'])
    if erros: prob += erros[:2]
    ctx.close()
    return prob


# ——— A4 e A5: o mapa de sensores ———
LE_SENS = """() => { """ + JS_BASE + """
  const re = (e) => { const r = e.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom }; }, nome = (s) => (s || '').replace(/\\s+/g, ' ').trim();
  const sec = (e) => e.closest('section'), regiao = (e) => e.closest('[role=region]') || sec(e);
  const blocos = [...document.querySelectorAll('[data-bloco]')].map((e) => { const l1 = e.querySelector('[data-l1]'), l2 = e.querySelector('[data-l2]'); return Object.assign({ id: e.getAttribute('data-bloco'), l1: nome(l1.innerText), l2: nome(l2.innerText), c1: l1.scrollWidth <= l1.clientWidth + 1, c2: l2.scrollWidth <= l2.clientWidth + 1, titulo: e.getAttribute('title'),
    cartao: sec(e).getAttribute('aria-label'), dentro: (() => { const r = re(e), s = re(regiao(e)), rolavel = !!e.closest('[role=region]'); return (rolavel || (r.l >= s.l - 0.5 && r.r <= s.r + 0.5)) && r.t >= s.t - 0.5 && r.b <= s.b + 0.5; })() }, re(e)); });
  const pontos = [...document.querySelectorAll('[data-ponto]')].map((e) => { e.scrollIntoView({ block: 'center', inline: 'center' }); const r = e.getBoundingClientRect(), cx = (r.left + r.right) / 2, cy = (r.top + r.bottom) / 2, topo = document.elementFromPoint(cx, cy);
    return { id: e.getAttribute('data-ponto'), nivel: e.getAttribute('data-nivel'), visivel: topo === e || e.contains(topo), esq: parseFloat(e.style.left) + parseFloat(e.style.width) / 2, topo: parseFloat(e.style.top) + parseFloat(e.style.height) / 2 }; });
  const linhas = [...document.querySelectorAll('[data-linha]')].map((e) => ({ id: e.getAttribute('data-linha'), esq: parseFloat(e.style.left), topo: parseFloat(e.style.top) + 0.5 }));
  window.scrollTo(0, 0);
  const num = (e, k) => parseFloat(e.style[k]), colide = [];
  document.querySelectorAll('[data-desenho]').forEach((cx) => { const bl = [...cx.querySelectorAll(':scope > [data-bloco]')].map((e) => ({ id: e.getAttribute('data-bloco'), l: num(e, 'left'), t: num(e, 'top'), r: num(e, 'left') + num(e, 'width'), b: num(e, 'top') + num(e, 'height') }));
    cx.querySelectorAll(':scope > [data-ponto]').forEach((d) => { const x = num(d, 'left') + num(d, 'width') / 2, y = num(d, 'top') + num(d, 'height') / 2, m = num(d, 'width') / 2 + 1;
      bl.forEach((q) => { if (x > q.l - m && x < q.r + m && y > q.t - m && y < q.b + m) colide.push(d.getAttribute('data-ponto') + ' dentro do bloco ' + q.id); }); }); });
  return { T, colide, q: { ancora: q.ancora_estado, ciclos: q.bomba_porao_ciclos }, blocos, pontos, linhas, lista: [...document.querySelectorAll('[data-sensor]')].map((e) => nome(e.innerText)), desenhos: [...document.querySelectorAll('[data-desenho]')].map((e) => e.getAttribute('data-desenho')),
    texto: nome(document.body.innerText), D: { sens: D.sensores.pontos.map((p) => [p.id, p.vista]), mapa: [D.sensores.perfil, D.sensores.planta] },
    selo: (() => { const n = document.querySelector('[data-selo]'); return n ? [n.getAttribute('data-selo'), nome(n.innerText)] : null; })() }; }"""
LIVRE_DE_SALVATAGEM = re.compile(r'colete|balsa|boia|extintor|sinalizador|epirb|radiobaliza|seafire|supress|incêndio|incendio|salva-?vidas', re.I)


def esperado_sensores(T, q, app):
    """O texto de cada miniquadro (2ª linha), refeito a partir do texto de cada campo do quadro: o bloco mostra os 2 primeiros campos do sensor (o 1º no app), o inclinômetro roll, pitch e yaw."""
    e = {'gps': [T['gps_satelites'] + ' satélites'], 'radar': ['ligado'], 'meteo': [T['vento_verdadeiro_nos'] + ' nós', T['vento_verdadeiro_angulo'] + '°'], 'sonda': [T['profundidade_m'] + ' m', T['temp_agua_c'] + ' °C'],
         'estabilizador': [T['seakeeper_volante_rpm'] + ' rpm', T['seakeeper_volante_pct'] + ' %'], 'praca': [T['temp_praca_maquinas_c'] + ' °C'],
         'motor_bb': [T['motor_bb_rpm'] + ' rpm', T['motor_bb_oleo_bar'] + ' bar'], 'motor_be': [T['motor_be_rpm'] + ' rpm', T['motor_be_oleo_bar'] + ' bar'], 'gerador': [T['gerador_kw'] + ' kW', T['gerador_horimetro_h'] + ' h'],
         'diesel_bb': [T['diesel_bb_pct'] + ' %'], 'diesel_be': [T['diesel_be_pct'] + ' %'], 'agua': [T['tanque_agua_pct'] + ' %'], 'servidas': [T['tanque_cinzas_pct'] + ' %', T['tanque_negras_pct'] + ' %'],
         'b24s': [T['bateria_0_tensao_v'] + ' V'], 'b24p': [T['bateria_1_tensao_v'] + ' V'], 'b12': [T['bateria_2_tensao_v'] + ' V'], 'porao_bb': [T['porao_bb_nivel'] + ' cm'],
         'leme': [T['leme_graus'] + '°', T['piloto_rumo'] + '°'], 'guincho': [q['ancora']], 'dessal': ['desligado']}
    e['porao_be'] = [T['porao_be_nivel'] + ' cm', T['bomba_porao_ciclos'] + ' ciclos']
    out = {k: ' · '.join(v[:1] if app else v[:2]) for k, v in e.items()}
    out['inclinometro'] = 'R %s° P %s° Y %s°' % (T['jogo_graus'], T['caimento_graus'], T['proa_graus'])
    return out


def interseca(a, b):
    return a['l'] < b['r'] - 0.5 and b['l'] < a['r'] - 0.5 and a['t'] < b['b'] - 0.5 and b['t'] < a['b'] - 0.5


def problemas_sensores(r, tela, rot):
    prob = []
    app = tela.startswith('A5')
    ids = sorted(x[0] for x in r['D']['sens'])
    if sorted(p['id'] for p in r['pontos']) != ids or sorted(b_['id'] for b_ in r['blocos']) != ids or len(r['lista']) != 22 or len(r['linhas']) != 22:
        prob.append('%s: %d pontos, %d blocos, %d linhas e %d itens na lista (esperado 22 de cada, os do D.sensores)' % (rot, len(r['pontos']), len(r['blocos']), len(r['linhas']), len(r['lista'])))
    if r['desenhos'] != ['assets/sensores-perfil.svg', 'assets/sensores-planta.svg']: prob.append('%s: desenhos %s' % (rot, r['desenhos']))
    por = {}
    for b_ in r['blocos']: por.setdefault(b_['cartao'], []).append(b_)
    if {k: len(v) for k, v in por.items()} != {'Perfil do barco': 7, 'Planta do barco': 15}: prob.append('%s: blocos por vista %s (esperado perfil 7 e planta 15)' % (rot, {k: len(v) for k, v in por.items()}))
    for vista, bl in por.items():
        for i, a in enumerate(bl):
            for c in bl[i + 1:]:
                if interseca(a, c): prob.append('%s: os blocos %s e %s se sobrepõem na %s' % (rot, a['id'], c['id'], vista))
    esp = esperado_sensores(r['T'], r['q'], app)
    for b_ in r['blocos']:
        if b_['l2'] != esp.get(b_['id']): prob.append('%s: o bloco %s mostra %r (esperado %r, do quadro)' % (rot, b_['id'], b_['l2'], esp.get(b_['id'])))
        if not (b_['c1'] and b_['c2']): prob.append('%s: o texto do bloco %s está cortado (%r / %r)' % (rot, b_['id'], b_['l1'], b_['l2']))
        if not b_['dentro']: prob.append('%s: o bloco %s sai do cartão (cortado pela borda)' % (rot, b_['id']))
    if r['colide']: prob.append('%s: ponto dentro de um bloco (o texto do bloco ficaria sob o ponto): %s' % (rot, r['colide'][:4]))
    for p in r['pontos']:
        if not p['visivel']: prob.append('%s: o ponto %s está coberto por outro elemento' % (rot, p['id']))
        if p['nivel'] not in ('normal', 'aviso', 'critico'): prob.append('%s: o ponto %s sem nível (%r)' % (rot, p['id'], p['nivel']))
    pontos = {p['id']: p for p in r['pontos']}
    for ln in r['linhas']:
        p = pontos.get(ln['id'])
        if not p or abs(ln['esq'] - p['esq']) > 0.6 or abs(ln['topo'] - p['topo']) > 0.6: prob.append('%s: a linha do bloco %s não sai do ponto (%s × %s)' % (rot, ln['id'], ln, p and (p['esq'], p['topo'])))
    if LIVRE_DE_SALVATAGEM.search(' '.join(r['lista'])): prob.append('%s: sensor de salvatagem ou de incêndio na lista: %s' % (rot, LIVRE_DE_SALVATAGEM.findall(' '.join(r['lista']))))
    ach = achados_termos(tela, r['texto'])
    if ach: prob.append('%s: termo do §3 no texto: %s' % (rot, ach))
    if not r['selo'] or r['selo'][0] != 'ok' or not re.fullmatch(r'Ao vivo · \d\d:\d\d', r['selo'][1]): prob.append('%s: o selo da página devia ser verde «Ao vivo · HH:MM»: %s' % (rot, r['selo']))
    return prob


def teste_sensores(b, tela):
    prob = []
    movel = eh_app(tela)
    for tema, (w, h), fixo in [('escuro', ((390, 844) if movel else (1440, 900)), '60'), ('claro', ((390, 844) if movel else (1440, 900)), '105')] + [('escuro', t, '60') for t in ([(360, 640), (844, 390), (430, 932)] if movel else [(1280, 720), (1920, 1080), (1024, 768)])]:
        ctx, pg, erros = abre_tela(b, tela, w, h, fixo=fixo, tema=tema)
        r = pg.evaluate(LE_SENS)
        prob += problemas_sensores(r, tela, '%s %s %dx%d t=%s' % (tela, tema, w, h, fixo))
        if erros: prob += erros[:2]
        ctx.close()
    return prob


# O desenho (assets/sensores-*.svg) segue a `referencia` do D.sensores (CONTRATO §1.19): o viewBox é o w × h do dado, a popa e a proa nas frações, a quilha e o topo do mastro (perfil), o eixo e a meia-boca (planta);
# e cada ponto cai a menos de 24 px de traço. O SVG é rasterizado no navegador, sem rede.
DESENHO_JS = """async () => { const D = window.CapitaoDados.sensores, out = {};
  for (const k of ['perfil', 'planta']) {
    const v = D[k], im = new Image(); im.src = v.img; await im.decode();
    const c = document.createElement('canvas'); c.width = v.w; c.height = v.h; const g = c.getContext('2d'); g.drawImage(im, 0, 0, v.w, v.h);
    const d = g.getImageData(0, 0, v.w, v.h).data, a = (x, y) => d[(y * v.w + x) * 4 + 3] > 40;
    const caixa = (x0, x1, y0, y1) => { let mx = 1e9, Mx = -1, my = 1e9, My = -1; for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) if (a(x, y)) { mx = Math.min(mx, x); Mx = Math.max(Mx, x); my = Math.min(my, y); My = Math.max(My, y); } return { mx, Mx, my, My }; };
    const r = D.referencia, W = v.w, H = v.h, res = { w: v.w, h: v.h, nat: [im.naturalWidth, im.naturalHeight] };
    if (k === 'perfil') { const q = caixa(300, 780, 0, H - 1), m = caixa(540, 660, 0, 120), po = caixa(0, 120, 205, 280), pr = caixa(1100, W - 1, 200, 240);
      res.quilha = [q.My, r.quilha_y * H]; res.topo = [m.my, r.topo_y * H]; res.popa = [po.mx, r.popa_x * W]; res.proa = [pr.Mx, r.proa_x * W]; }
    else { const m = caixa(400, 600, 0, H - 1), po = caixa(0, 100, 110, 140), pr = caixa(1100, W - 1, 205, 215);
      res.topo = [m.my, (r.eixo_y - r.meia_boca) * H]; res.quilha = [m.My, (r.eixo_y + r.meia_boca) * H]; res.popa = [po.mx, r.popa_x * W]; res.proa = [pr.Mx, r.proa_x * W]; }
    res.pontos = D.pontos.filter((p) => p.vista === k).map((p) => { const x = Math.round(p.x * W), y = Math.round(p.y * H), cx = caixa(Math.max(0, x - 24), Math.min(W - 1, x + 24), Math.max(0, y - 24), Math.min(H - 1, y + 24)); return [p.id, cx.Mx >= 0]; });
    out[k] = res;
  } return out; }"""


def teste_sensores_desenho(b):
    prob = []
    ctx, pg, erros = abre_tela(b, 'A4-Sensores-Web')
    r = pg.evaluate(DESENHO_JS)
    for k, v in r.items():
        if v['nat'] != [v['w'], v['h']] and v['nat'] != [0, 0]: prob.append('%s: o SVG tem %s e o D.sensores diz %dx%d' % (k, v['nat'], v['w'], v['h']))
        for nome, tol in (('quilha', 6), ('topo', 6), ('popa', 10), ('proa', 10)):
            obs, esp = v[nome]
            if abs(obs - esp) > tol: prob.append('%s: %s do desenho em %.1f e a referência do D.sensores em %.1f (tolerância %d)' % (k, nome, obs, esp, tol))
        longe = [p[0] for p in v['pontos'] if not p[1]]
        if longe: prob.append('%s: pontos a mais de 24 px de qualquer traço: %s' % (k, longe))
    for arq in ('assets/sensores-perfil.svg', 'assets/sensores-planta.svg'):
        t = open(os.path.join(RAIZ, arq), encoding='utf-8').read()
        if re.search(r'<image|href=|xlink|<script|data:', t, re.I): prob.append('%s: referência externa ou script dentro do SVG' % arq)
    if erros: prob += erros[:2]
    ctx.close()
    return prob


# ——— o ramo simulacao:false: a Ponte e o mapa de sensores mantêm o caminho `null` → SEM DADOS e a última leitura salva (o D.snapshot), sem erro e sem dizer «ao vivo» ———
def teste_ponte_real(b, lista=TELAS_P4C):
    prob = []
    for tela in TELAS_P4C:
        if tela == 'A3-Ponte-Editar' or tela not in lista: continue
        ctx, pg, erros = abre_tela(b, tela, fixo=None, depois='window.CapitaoDados.simulacao = false;')
        r = pg.evaluate("""() => { const lin = (s) => (s || '').replace(/\\s+/g, ' ').trim(), n = document.querySelector('[data-selo]'), g = document.querySelector('[data-capitao-grafico],[data-vazio]');
          return { texto: lin(document.body.innerText), nota: n ? [n.getAttribute('data-selo'), lin(n.innerText)] : null, replay: window.CapitaoReplay ? window.CapitaoReplay.ativo() : null, grafico: g ? lin(g.innerText) : null,
            ultima: (() => { const S = window.CapitaoDados.snapshot; return 'Última leitura · ' + S.quando.slice(0, 5) + ' ' + S.hora; })() }; }""")
        rot = '%s com simulacao false' % tela
        if r['replay']: prob.append('%s: o replay ainda anda' % rot)
        if re.search(r'NaN|undefined|\[object', r['texto']): prob.append('%s: NaN, undefined ou [object na tela' % rot)
        if r['nota'] and (r['nota'][0] != 'warn' or not r['nota'][1].startswith('Última leitura · 26/09')): prob.append('%s: o selo diz %s (esperado âmbar, «Última leitura · 26/09 …»)' % (rot, r['nota']))
        if tela.startswith('A1'):
            if 'lançada · 30 m' not in r['texto'] or 'BB 1,2 · BE 0,9 cm' not in r['texto']: prob.append('%s: o chip da âncora e o do porão devem mostrar o que o D.snapshot tem (lançada · 30 m; BB 1,2 · BE 0,9 cm)' % rot)
            if not r['grafico'] or 'SEM DADOS' not in r['grafico']: prob.append('%s: sem replay o gráfico devia dizer SEM DADOS: %r' % (rot, r['grafico']))
        if tela.startswith('A2') and (not r['grafico'] or 'SEM DADOS' not in r['grafico']): prob.append('%s: sem replay o gráfico devia dizer SEM DADOS: %r' % (rot, r['grafico']))
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    return prob


# ——— o código das telas e dos dois arquivos novos ———
def teste_codigo_ponte():
    prob = []
    def le_(a):   # o arquivo do disco, com o defeito plantado (MUT_ARQ) se houver
        t = open(os.path.join(RAIZ, a), encoding='utf-8').read()
        for velho, novo in MUT_ARQ.get(a, []): t = t.replace(velho, novo, 1)
        return t
    GEOM = re.compile(r'<(?:svg|path|circle|line|rect|ellipse|polyline|polygon|g)\b[^>]*\b(?:d|x|y|x1|x2|y1|y2|cx|cy|r|rx|ry|width|height|viewBox|points|transform)="[^"]*\{\{')
    for t in TELAS_P4C:
        h = le_(t + '.dc.html')
        if GEOM.search(h): prob.append('%s: {{…}} em atributo geométrico de SVG' % t)
        if t in ('A3-Ponte-Editar',): continue
        mont, desm = h.find('componentDidMount'), h.find('componentWillUnmount')
        if "addEventListener('capitao-telemetria'" not in h[mont:desm] or "removeEventListener('capitao-telemetria'" not in h[desm:]: prob.append('%s: não assina o capitao-telemetria no componentDidMount e remove no componentWillUnmount' % t)
        if 'document.hidden' not in h: prob.append('%s: não pausa com document.hidden' % t)
        if 'if (k === this._k) return;' not in h or 'this.setState({ vivo: k })' not in h: prob.append('%s: não compara o texto antes do setState' % t)
        if h.count('setInterval') > (1 if t.startswith(('A1', 'A2')) else 0): prob.append('%s: setInterval novo (%d)' % (t, h.count('setInterval')))
        if re.search(r'D\.snapshot|\.snapshot\b', h) and t not in ('A1-Ponte-Web',): prob.append('%s: lê o D.snapshot' % t)
    for arq in ('capitao-grafico.js', 'capitao-sensores.js'):
        src = le_(arq)
        sem_com = re.sub(r'(?s)/\*.*?\*/', '', src)
        if '(?<' in src or '\\w' in src: prob.append('%s: lookbehind ou \\w' % arq)
        if 'setInterval' in sem_com: prob.append('%s: setInterval' % arq)
        if re.search(r'localStorage|sessionStorage|indexedDB|speechSynthesis|location\s*(\.\s*(href|assign|replace|reload)|=)|window\s*\.\s*open', sem_com): prob.append('%s: escreve no aparelho, fala ou troca de tela' % arq)
        if 'EM_SOS' not in src or 'SOS-' not in src: prob.append('%s: não sai em /SOS-/' % arq)
    sw = le_('sw.js')
    for x in ("'./capitao-grafico.js'", "'./capitao-sensores.js'", "'./assets/sensores-perfil.svg'", "'./assets/sensores-planta.svg'", "'A4-Sensores-Web'", "'A5-Sensores-Mobile'"):
        if x not in sw: prob.append('sw.js sem %s' % x)
    if 'A4-Sensores-Web.dc.html' not in le_('index.html') or 'A5-Sensores-Mobile.dc.html' not in le_('index.html'): prob.append('index.html sem A4 e A5')
    if "'A4-Sensores-Web': 'A5-Sensores-Mobile'" not in le_('capitao-app.js'): prob.append('capitao-app.js sem o par A4 → A5 no mapa APP')
    for t in TELAS_SENSORES:
        h = le_(t + '.dc.html')
        ordem = [h.find(x) for x in ('<script src="./capitao-dados.js">', '<script src="./capitao-replay.js">', '<script src="./capitao-alertas.js"></script>', '<script src="./support.js">')]
        if ordem != sorted(ordem) or -1 in ordem or h.count('capitao-replay.js') != 1: prob.append('%s: <head> fora da ordem das outras telas (dados, replay, alertas, …, support)' % t)
    return prob


def p4c_conferencias(b, lista):
    """[(nome, problemas)] das conferências da P4C para as telas da rodada."""
    out = []
    if any(t in lista for t in TELAS_P4C): out.append(('código da Ponte, do gráfico e dos sensores', teste_codigo_ponte()))
    for tela in [t for t in TELAS_PONTE if t in lista]: out.append(('gráfico em ' + tela, teste_grafico(b, tela)))
    if 'A1-Ponte-Web' in lista: out.append(('A1 · blocos, alertas, tendências e mapa', teste_ponte_web(b)))
    if 'A2-Ponte-Mobile' in lista: out.append(('A2 · estados, alertas, tendências e mapa', teste_ponte_app(b)))
    for tela in [t for t in TELAS_SENSORES if t in lista]: out.append(('sensores em ' + tela, teste_sensores(b, tela)))
    if 'A4-Sensores-Web' in lista: out.append(('desenho dos sensores × referência', teste_sensores_desenho(b)))
    if any(t in lista for t in TELAS_P4C): out.append(('simulacao false na Ponte e nos sensores', teste_ponte_real(b, lista)))
    return out


# Defeitos plantados da P4C: cada um é servido no lugar do arquivo (MUT_ARQ) e a conferência que cuida dele TEM de acusar (--mutantes-p4c; um mutante vivo reprova).
MUTANTES_P4C = [
    ('o último ponto do gráfico é o penúltimo (não é o quadro de agora)', 'capitao-grafico.js', [("agora: pts[pts.length - 1],", "agora: pts[pts.length - 2],")], 'grafico'),
    ('NaN na janela de 1 A', 'capitao-grafico.js', [("var xdoT = function (t) { return X0 + (t - d.t0) / (d.t1 - d.t0) * (X1 - X0); };", "var xdoT = function (t) { return X0 + (t - d.t0) / (d.t1 - d.t0) * (X1 - X0) * (jan === '1A' ? NaN : 1); };")], 'grafico'),
    ('sem cursor (o ponteiro não faz nada)', 'capitao-grafico.js', [("onPointerMove: aoPonteiro, onPointerDown: aoPonteiro,", "onPointerDown: aoPonteiro,")], 'grafico'),
    ('texto do eixo numa cor fixa escura (some no tema escuro)', 'capitao-grafico.js', [("var ink4 = { fill: 'var(--cap-ink4, #7985a6)' };", "var ink4 = { fill: '#2b3350' };")], 'grafico'),
    ('a lista de alertas da A1 sem os alarmes pedidos no chat', 'A1-Ponte-Web.dc.html', [("pedidos.forEach((a) => { if (a && typeof a.id === 'string' && a.nivel === 'aviso') itens.push(", "pedidos.slice(0, 0).forEach((a) => { if (a && typeof a.id === 'string' && a.nivel === 'aviso') itens.push(")], 'ponte_web'),
    ('o alerta sem começo conhecido (desdeMs null) no COMEÇO da lista da A1', 'A1-Ponte-Web.dc.html', [("inf = (x) => (x === null || x === undefined ? Infinity : x);", "inf = (x) => (x === null || x === undefined ? 0 : x);")], 'ponte_web'),
    ('o estado dos motores da A1 sem a fase da reprodução («ligados · cruzeiro»)', 'A1-Ponte-Web.dc.html', [("(ligados && fase ? ' · ' + fase : '')", "''")], 'ponte_web'),
    ('o fabricante dos motores fixo na A1 (Cummins)', 'A1-Ponte-Web.dc.html', [("t: 'Motores ' + (eM.fabricante || falta('(fabricante ' + SD + ')'))", "t: 'Motores Cummins'")], 'ponte_web'),
    ('o fabricante do gerador fixo na A2 (Onan)', 'A2-Ponte-Mobile.dc.html', [("(equip('gerador').fabricante || falta(SD))", "'Onan'")], 'ponte_app'),
    ('os blocos dos sensores sem a faixa livre (cobrem o radar e a estação meteorológica)', 'capitao-sensores.js', [("      while (!livre(sc, 'cima') && sc < 0.2 * H) sc += passo;\n", "")], 'sensores_web'),
    ('o inclinômetro sem o yaw (só roll e pitch)', 'capitao-sensores.js', [("linha2 = j !== null && c !== null && y !== null ? 'R ' + j + ' P ' + c + ' Y ' + y : falta(SL);", "linha2 = j !== null && c !== null ? 'R ' + j + ' P ' + c : falta(SL);")], 'sensores_web'),
    ('blocos largos demais (se sobrepõem e cortam o texto)', 'capitao-sensores.js', [("bw = Math.floor(0.1 * W) - 4;", "bw = Math.floor(0.16 * W) - 4;")], 'sensores_app'),
    ('capitao-grafico.js fora do CORE do sw.js', 'sw.js', [("'./capitao-grafico.js', ", "")], 'codigo'),
]


def mutantes_p4c(b):
    global MUT_ARQ
    vivos = []
    for nome, arq, trocas, qual in MUTANTES_P4C:
        src = open(os.path.join(RAIZ, arq), encoding='utf-8').read()
        faltam = [x for x, _ in trocas if src.count(x) != 1]
        if faltam:
            print('ERRO no mutante «%s»: o trecho não está uma vez em %s: %s' % (nome, arq, faltam)); vivos.append(nome); continue
        MUT_ARQ = {arq: trocas}
        sai = sys.stdout
        prob = []
        try:
            sys.stdout = open(os.devnull, 'w')
            prob = {'grafico': lambda: teste_grafico(b, 'A1-Ponte-Web'), 'ponte_web': lambda: teste_ponte_web(b), 'ponte_app': lambda: teste_ponte_app(b),
                    'sensores_web': lambda: teste_sensores(b, 'A4-Sensores-Web'), 'sensores_app': lambda: teste_sensores(b, 'A5-Sensores-Mobile'), 'codigo': lambda: teste_codigo_ponte()}[qual]()
        except Exception as e:   # um erro do próprio teste não conta como acusação (esconderia um defeito do teste): o mutante fica vivo
            sys.stdout = sai
            print('ERRO do teste no mutante «%s»: %s' % (nome, str(e).splitlines()[-1][:160]))
            prob = []
        finally:
            sys.stdout = sai
            MUT_ARQ = {}
        print('MUTANTE %s: %s (%d problema(s))%s' % ('ACUSADO' if prob else 'VIVO', nome, len(prob), ' · ' + prob[0][:150] if prob else ''))
        if not prob: vivos.append(nome)
    print('%d mutantes · %d vivos' % (len(MUTANTES_P4C), len(vivos)))
    return vivos


# ——— P4D: a Carta (B1 Gestão, B2 Sistemas, B3 Resposta por voz) ———
# PROMPT Fase 4 e linha P4D (MAPA §6 B1, B2, B3); a janela de conversa em emergência (PROMPT §2.2, CLAUDE.md 10) e a decisão 17 (EPIRB e Seafire só com o procedimento padrão). Cada conferência abaixo
# tem um defeito plantado que a faz falhar (MUTANTES_P4D, rodados com --mutantes-p4d): o teste só vale se acusa o defeito.
TELAS_P4D = ('B1-Carta-Web', 'B2-Carta-Mobile', 'B3-Carta-Resposta')
PADRAO_SEG = 'procedimento padrão — confirmar com o protocolo de bordo'
NOTA_ETIQUETA = 'modelo, validade e acionamento: veja a etiqueta do equipamento'

# B1: o texto de cada bloco refeito do quadro (a mesma CapitaoAgora.fmt.campo da moldura e do cérebro) e dos números que o instante calcula (calc), os 4 cartões contra as contagens do CapitaoAgora
LE_B1 = """() => { """ + JS_BASE + """
  const un = (s) => { const e = document.querySelector(s); return e ? lin(e.innerText) : null; }, B = window.CapitaoBrain, C = A.contagens(), nb = F.nb, calc = I.calc;
  const mot = {}; document.querySelectorAll('[data-motor]').forEach((e) => { const l = e.querySelector('[data-b1=motor-leitura]'); mot[e.getAttribute('data-motor')] = { texto: lin(e.innerText), leitura: lin(l.innerText), cor: getComputedStyle(l).color, titulo: e.getAttribute('title') }; });
  const kpi = {}; document.querySelectorAll('[data-kpi]').forEach((e) => { kpi[e.getAttribute('data-kpi')] = { v: lin(e.querySelectorAll(':scope > span')[1].innerText), texto: lin(e.innerText), href: e.getAttribute('href') }; });
  const m = /Pendências abertas \\((\\d+)\\)/.exec(B.answer('Anomalias abertas', { platform: 'web', commit: false }).text);
  const dia = new Intl.DateTimeFormat('pt-BR', { weekday: 'long', timeZone: A.fuso }).format(new Date(I.ms)), ddmm = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', timeZone: A.fuso }).format(new Date(I.ms));
  const warn = (() => { const e = document.createElement('i'); e.style.color = 'var(--cap-warn, #f0a63a)'; document.body.appendChild(e); const c = getComputedStyle(e).color; e.remove(); return c; })();
  const tOleo = D.agenda.find((t) => t.id === 'motores-oleo'), hMax = (campos) => Math.max(...campos.map((c) => q[c]));
  const manut = [...document.querySelectorAll('a[href*="C1-Leme-Web.dc.html#f="]')].filter((a) => !a.hasAttribute('data-kpi') && a.querySelector('b')).map((a) => lin(a.innerText));
  return { T, I: { hora: I.hora, hhmm: I.hhmm, fase: I.fase && I.fase.nome }, marcha: q.marcha, mot, kpi, C, anom: m ? +m[1] : null, warn, texto: lin(document.body.innerText),
    resumo: un('[data-b1=resumo]'), propSub: un('[data-b1=prop-sub]'), estado: un('[data-b1=prop-estado]'), diesel: un('[data-b1=diesel]'), dieselHora: un('[data-b1=diesel-hora]'), consumo: un('[data-b1=consumo]'),
    autonomia: un('[data-b1=autonomia]'), oleo: un('[data-b1=oleo-s]'), manut, versao: D.versao,
    esp: { dia: dia.charAt(0).toUpperCase() + dia.slice(1) + ', ' + ddmm, aut: calc.autonomia ? '≈ ' + nb(calc.autonomia.horas, 1) + ' h · ≈ ' + nb(calc.autonomia.mn, 0, true) + ' mn' : null,
      desde: calc.desdeAbast ? '≈ ' + nb(calc.desdeAbast.litros, 0, true) + ' L desde' : null, oleoHoras: nb(hMax(tOleo.horas.campos), 1, true), oleoFaltam: nb(calc.faltam['motores-oleo'], 1) } }; }"""


def teste_carta_web(b):
    """B1: propulsão, diesel, consumo e autonomia do quadro (nada do snapshot de 26/09), as horas até a troca do horímetro de agora, o dia do instante, os 4 cartões iguais às contagens do CapitaoAgora e
    do cérebro, sem rótulo, o arrefecimento do BE em AVISO a 105 s; Executado e pendência resolvida acompanham; fabricante e modelo de D.equipamentos."""
    prob = []
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_tela(b, 'B1-Carta-Web', fixo=fixo)
        r = pg.evaluate(LE_B1)
        T, rot = r['T'], 'B1 a %s s' % fixo
        if not re.fullmatch(r'Ligados · cruzeiro · marcha avante · ao vivo %s' % re.escape(r['I']['hora']), r['estado'] or ''): prob.append('%s: o estado da propulsão devia ser «Ligados · cruzeiro · marcha avante · ao vivo %s»: %r' % (rot, r['I']['hora'], r['estado']))
        for lado, k in (('bb', 'BB'), ('be', 'BE')):
            m = r['mot'].get(lado, {})
            esp = '%s rpm · óleo %s bar · %s °C' % (T['motor_%s_rpm' % lado], T['motor_%s_oleo_bar' % lado], T['motor_%s_arref_c' % lado])
            if m.get('leitura') != esp: prob.append('%s: o motor %s diz %r (esperado %r, do quadro)' % (rot, k, m.get('leitura'), esp))
            if (T['motor_%s_horimetro_h' % lado] + ' h') not in m.get('texto', ''): prob.append('%s: o horímetro do %s não é o do quadro (%s): %r' % (rot, k, T['motor_%s_horimetro_h' % lado], m.get('texto')))
            if 'ao vivo ' + r['I']['hora'] not in (m.get('titulo') or ''): prob.append('%s: a dica do motor %s não leva a hora do quadro: %r' % (rot, k, m.get('titulo')))
        if r['diesel'] != '≈ %s L' % T['diesel_litros']: prob.append('%s: o diesel diz %r (esperado «≈ %s L», do quadro)' % (rot, r['diesel'], T['diesel_litros']))
        if 'BB %s %% · BE %s %%' % (T['diesel_bb_pct'], T['diesel_be_pct']) not in r['texto']: prob.append('%s: os tanques de diesel BB %s e BE %s não estão na tela' % (rot, T['diesel_bb_pct'], T['diesel_be_pct']))
        if not (r['dieselHora'] or '').startswith('Ao vivo · ' + r['I']['hora']): prob.append('%s: a hora do diesel diz %r (esperado «Ao vivo · %s»)' % (rot, r['dieselHora'], r['I']['hora']))
        if ('agora ' + T['consumo_lph'] + ' L/h') not in (r['consumo'] or '') or r['esp']['desde'] not in (r['consumo'] or ''): prob.append('%s: o consumo %r não tem «agora %s L/h» nem «%s»' % (rot, r['consumo'], T['consumo_lph'], r['esp']['desde']))
        if r['esp']['aut'] not in (r['autonomia'] or ''): prob.append('%s: a autonomia diz %r (esperado %r, do instante)' % (rot, r['autonomia'], r['esp']['aut']))
        if ('Horímetro %s h · faltam %s h' % (r['esp']['oleoHoras'], r['esp']['oleoFaltam'])) not in (r['oleo'] or ''): prob.append('%s: a troca de óleo diz %r (esperado «Horímetro %s h · faltam %s h», do horímetro de agora)' % (rot, r['oleo'], r['esp']['oleoHoras'], r['esp']['oleoFaltam']))
        if r['esp']['dia'] not in (r['resumo'] or '') or ('Telemetria ao vivo · ' + r['I']['hhmm']) not in (r['resumo'] or '') or ('prazos contados a partir de ' + r['versao']) not in (r['resumo'] or ''):
            prob.append('%s: o resumo %r devia ter «%s», «Telemetria ao vivo · %s» e «prazos contados a partir de %s»' % (rot, r['resumo'], r['esp']['dia'], r['I']['hhmm'], r['versao']))
        C = r['C']
        for k, v in (('atrasadas', C['atrasadas']), ('d30', C['d30']), ('docs', C['docsVencidos'] + C['docsVencem90']), ('pendencias', r['anom'])):
            if r['kpi'].get(k, {}).get('v') != str(v): prob.append('%s: o cartão %s mostra %r (esperado %s: %s)' % (rot, k, r['kpi'].get(k, {}).get('v'), v, 'a contagem do CapitaoAgora' if k != 'pendencias' else 'o que o cérebro conta em «Anomalias abertas»'))
        if r['kpi'].get('pendencias', {}).get('v') != str(C['pendencias']): prob.append('%s: as pendências do cartão (%s) não são as do CapitaoAgora.contagens() (%s)' % (rot, r['kpi'].get('pendencias', {}).get('v'), C['pendencias']))
        if len(r['manut']) != 6: prob.append('%s: a lista da manutenção tem %d linhas (esperado 6)' % (rot, len(r['manut'])))
        cor_be = r['mot'].get('be', {}).get('cor')
        if fixo == '105' and cor_be != r['warn']: prob.append('%s: o arrefecimento do BE (%s °C) devia estar na cor de AVISO (%s): %s' % (rot, T['motor_be_arref_c'], r['warn'], cor_be))
        if fixo == '60' and cor_be == r['warn']: prob.append('%s: o BE está em AVISO a 60 s (cruzeiro, sem alarme)' % rot)
        ach = achados_termos('B1-Carta-Web', pg.evaluate(LE_TEXTOS))
        if ach: prob.append('%s: termo do §3 na tela: %s' % (rot, ach))
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    # Executado no aparelho tira a tarefa da conta (o mesmo número do CapitaoAgora); pendência resolvida por linha nova sai da contagem (a mesma do chat)
    ctx, pg, erros = abre_tela(b, 'B1-Carta-Web', ls={'capitao.executado.v1': json.dumps({'porao-teste': {'d': '09/11', 't': '12:00'}})})
    r = pg.evaluate(LE_B1)
    if r['C']['atrasadas'] != 2 or r['kpi']['atrasadas']['v'] != '2' or 'Bombas de porão' in r['kpi']['atrasadas']['texto']: prob.append('B1 com o teste do porão executado: os atrasados são %r (esperado 2, sem as bombas de porão): %s' % (r['kpi']['atrasadas']['v'], r['kpi']['atrasadas']['texto']))
    if erros: prob += erros[:2]
    ctx.close()
    resolve = [{'id': 'x1', 'acao': 'resolve', 'alvo': 'd05', 't': 'Pendência resolvida: Climatização da cabine de proa com fluxo fraco — marcada como resolvida por Lucas. Linha nova, nada se apaga.', 'iso': '2026-11-09T11:00:00-03:00', 'd': '09/11', 'who': 'Lucas', 'sys': 'Equipamentos', 'sim': True}]
    ctx, pg, erros = abre_tela(b, 'B1-Carta-Web', ls={'capitao.diario.v1': json.dumps(resolve)})
    r = pg.evaluate(LE_B1)
    if r['kpi']['pendencias']['v'] != '2' or r['anom'] != 2 or r['C']['pendencias'] != 2: prob.append('B1 com a pendência da climatização resolvida: o cartão mostra %r, o cérebro conta %s e o CapitaoAgora %s (esperado 2 nos três)' % (r['kpi']['pendencias']['v'], r['anom'], r['C']['pendencias']))
    if erros: prob += erros[:2]
    ctx.close()
    # fabricante e modelo vêm do D.equipamentos (nunca fixos na tela)
    ctx, pg, erros = abre_tela(b, 'B1-Carta-Web', depois=FAB_FALSOS)
    r = pg.evaluate(LE_B1)
    if r['propSub'] != '2 × Zyxmotor · modelo Zyxmotor Mod9': prob.append('fabricante e modelo dos motores trocados no D.equipamentos e a B1 diz %r' % r['propSub'])
    if erros: prob += erros[:2]
    ctx.close()
    return prob


# B2: o estado de cada um dos 11 sistemas, refeito do quadro e de D.equipamentos
LE_B2 = """() => { """ + JS_BASE + """
  const un = (s) => { const e = document.querySelector(s); return e ? lin(e.innerText) : null; }, C = A.contagens(), eq = (id) => D.equipamentos.find((e) => e.id === id) || {};
  const rows = {}; document.querySelectorAll('[data-sistema]').forEach((e) => { const est = e.querySelector('[data-b2=estado]'); rows[e.getAttribute('data-sistema')] = { fab: lin(e.querySelector('[data-b2=fab]').innerText), estado: lin(est.innerText), cor: getComputedStyle(est).color,
    texto: lin(e.innerText), hrefs: [...e.querySelectorAll('a')].map((a) => a.getAttribute('href')) }; });
  const warn = (() => { const e = document.createElement('i'); e.style.color = 'var(--cap-warn, #f0a63a)'; document.body.appendChild(e); const c = getComputedStyle(e).color; e.remove(); return c; })();
  const atr = document.querySelector('[data-b2=atrasadas]');
  return { T, I: { hora: I.hora, hhmm: I.hhmm, fase: I.fase && I.fase.nome }, q: { clima: q.climatizacao_ativa, radar: q.radar_ativo, ais: q.ais_alvos, ciclos: q.bomba_porao_ciclos }, rows, warn, C, agora: un('[data-b2=agora]'), atr: atr ? lin(atr.innerText) : null,
    nota: lin(document.body.innerText), D: { guia: D.guias.g_eletronicos, canal: D.protocolos.canal16, zonas: eq('audio').nominal.zonas, licenca: D.documentos.find((d) => /VHF/.test(d.n)), cartas: D.diario.find((x) => /cartas/i.test(x.t)).d,
      fab: Object.fromEntries(['motores', 'gerador', 'estabilizador', 'porao', 'eletrico', 'epirb', 'seafire'].map((id) => [id, [eq(id).fabricante, eq(id).modelo, eq(id).qtd, eq(id).lados]])), nSis: D.equipamentos.length } }; }"""


def teste_carta_app(b):
    """B2: o estado de cada sistema é o do quadro (motores, gerador, estabilizador, climatização, eletrônicos, porão, baterias) ou de D.equipamentos (áudio, VHF), sem «SEM LEITURA» nem «SEM DADOS»;
    EPIRB e Seafire só com o procedimento padrão e a nota da etiqueta; fabricante e modelo de D.equipamentos (as bombas e as baterias também); tudo a 60 s e a 105 s."""
    prob = []
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_tela(b, 'B2-Carta-Mobile', fixo=fixo)
        r = pg.evaluate(LE_B2)
        T, rot, R = r['T'], 'B2 a %s s' % fixo, r['rows']
        if sorted(R) != sorted(['motores', 'gerador', 'estabilizador', 'climatizacao', 'eletronicos', 'audio', 'vhf', 'epirb', 'seafire', 'porao', 'baterias']): prob.append('%s: os sistemas da tela são %s' % (rot, sorted(R)))
        esp = {
            'motores': 'Ligados · %s · %s/%s rpm · óleo %s/%s bar · arrefecimento %s/%s °C' % (r['I']['fase'], T['motor_bb_rpm'], T['motor_be_rpm'], T['motor_bb_oleo_bar'], T['motor_be_oleo_bar'], T['motor_bb_arref_c'], T['motor_be_arref_c']),
            'gerador': 'Ligado · %s kW · %s h' % (T['gerador_kw'], T['gerador_horimetro_h']),
            'estabilizador': 'Ligado · %s %% · %s rpm' % (T['seakeeper_volante_pct'], T['seakeeper_volante_rpm']),
            'eletronicos': 'GPS: %s satélites · AIS %s %s · radar %s' % (T['gps_satelites'], T['ais_alvos'], 'alvo' if r['q']['ais'] == 1 else 'alvos', 'ligado' if r['q']['radar'] else 'desligado'),
            'porao': 'porão: BB %s cm · BE %s cm · bomba %s %s/h' % (T['porao_bb_nivel'], T['porao_be_nivel'], r['q']['ciclos'], 'ciclo' if r['q']['ciclos'] == 1 else 'ciclos'),
            'baterias': '24 V %s V · 12 V %s V' % (T['bateria_0_tensao_v'], T['bateria_2_tensao_v'])}
        for k, e in esp.items():
            if not R.get(k, {}).get('estado', '').startswith(e): prob.append('%s: o estado de %s diz %r (esperado «%s…», do quadro)' % (rot, k, R.get(k, {}).get('estado'), e))
        if not R['climatizacao']['estado'].startswith('Ligada' if r['q']['clima'] else 'Desligada') or 'diário' not in R['climatizacao']['estado']: prob.append('%s: o estado da climatização diz %r (esperado o do quadro, com a linha do diário)' % (rot, R['climatizacao']['estado']))
        if '%s zonas de áudio · %s' % (r['D']['zonas'], r['D']['guia']) != R['audio']['estado']: prob.append('%s: o áudio diz %r (esperado as zonas e o guia do D.equipamentos)' % (rot, R['audio']['estado']))
        L = r['D']['licenca']
        if not R['vhf']['estado'].startswith('Canal %s · %s MHz' % (r['D']['canal']['canal'], r['D']['canal']['mhz'])) or ('licença de estação vence %s (D-%d)' % (L['vence'], L['dn'])) not in R['vhf']['estado']: prob.append('%s: o VHF diz %r (esperado o canal 16 e a licença de estação)' % (rot, R['vhf']['estado']))
        for k in ('epirb', 'seafire'):   # decisão 17: só o procedimento padrão e a nota da etiqueta; fabricante e modelo ficam na linha de cima (Equipamentos)
            if R[k]['estado'] != '%s · %s' % (PADRAO_SEG, NOTA_ETIQUETA): prob.append('%s: o estado de %s diz %r (esperado só «%s · %s»)' % (rot, k, R[k]['estado'], PADRAO_SEG, NOTA_ETIQUETA))
        # fabricante e modelo de D.equipamentos em toda linha (as bombas e as baterias também), nunca «SEM DADOS»
        for k, id_ in (('motores', 'motores'), ('gerador', 'gerador'), ('estabilizador', 'estabilizador'), ('porao', 'porao'), ('baterias', 'eletrico'), ('epirb', 'epirb'), ('seafire', 'seafire')):
            f, m_, qtd, lados = r['D']['fab'][id_]
            nome = m_ if m_.lower().startswith(f.lower()) else f + ' ' + m_   # o fabricante não se repete quando o modelo já começa por ele («Seakeeper 3»)
            if nome not in R[k]['fab']: prob.append('%s: a linha de %s não tem %r (fabricante e modelo do D.equipamentos): %r' % (rot, k, nome, R[k]['fab']))
            if qtd > 1 and ('%d unidades' % qtd) not in R[k]['fab']: prob.append('%s: a linha de %s não diz %d unidades: %r' % (rot, k, qtd, R[k]['fab']))
        if r['agora'] != 'ao vivo · ' + r['I']['hora']: prob.append('%s: o rótulo da hora diz %r (esperado «ao vivo · %s»)' % (rot, r['agora'], r['I']['hora']))
        if r['atr'] is None or not re.search(r'3 manutenções atrasadas', r['atr']) or r['C']['atrasadas'] != 3: prob.append('%s: a faixa de atrasadas diz %r e o CapitaoAgora conta %s (esperado 3)' % (rot, r['atr'], r['C']['atrasadas']))
        warn_motores = R['motores']['cor'] == r['warn']
        if fixo == '105' and not warn_motores: prob.append('%s: o estado dos motores (BE a %s °C) devia estar na cor de AVISO: %s' % (rot, T['motor_be_arref_c'], R['motores']['cor']))
        if fixo == '60' and warn_motores: prob.append('%s: o estado dos motores está em AVISO a 60 s' % rot)
        ach = achados_termos('B2-Carta-Mobile', pg.evaluate(LE_TEXTOS))
        if ach: prob.append('%s: termo do §3 na tela: %s' % (rot, ach))
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    # Executado tira a tarefa dos atrasados (e da etiqueta do porão); a lista segue o CapitaoAgora
    ctx, pg, erros = abre_tela(b, 'B2-Carta-Mobile', ls={'capitao.executado.v1': json.dumps({'porao-teste': {'d': '09/11', 't': '12:00'}})})
    r = pg.evaluate(LE_B2)
    if '2 manutenções atrasadas' not in (r['atr'] or '') or r['C']['atrasadas'] != 2 or 'Teste das bombas' in (r['atr'] or '') or 'EXECUTADO' not in r['rows']['porao']['texto']: prob.append('B2 com o teste do porão executado: %r (esperado 2 atrasadas, sem as bombas, e a etiqueta EXECUTADO no porão)' % r['atr'])
    if erros: prob += erros[:2]
    ctx.close()
    ctx, pg, erros = abre_tela(b, 'B2-Carta-Mobile', depois=FAB_FALSOS)
    r = pg.evaluate(LE_B2)
    if 'Zyxmotor Mod9' not in r['rows']['motores']['fab'] or 'Zyxgerador Mod9' not in r['rows']['gerador']['fab'] or 'Zyxestab Mod9' not in r['rows']['estabilizador']['fab']: prob.append('fabricante trocado no D.equipamentos e a B2 não o mostra: %s' % [r['rows'][k]['fab'] for k in ('motores', 'gerador', 'estabilizador')])
    if erros: prob += erros[:2]
    ctx.close()
    return prob


# B3: a pergunta, a hora da resposta, o aviso de emergência (a marca CapitaoEmergencia) e o texto da resposta
LE_B3 = """() => { const lin = (s) => (s || '').replace(/\\s+/g, ' ').trim(), A = window.CapitaoAgora, E = window.CapitaoEmergencia, h = document.querySelector('[data-b3=hora]'), pr = document.querySelector('[data-b3=pergunta]');
  const rot = [...document.querySelectorAll('#dc-root span')].find((s) => lin(s.innerText) === 'AÇÕES'), fala = document.querySelector('#dc-root [aria-live=polite]'), raiz = document.getElementById('dc-root');
  const ate = E.ate(), dia = A.instante();
  return { hora: h ? lin(h.innerText) : null, horaTitulo: h ? h.getAttribute('title') : null, pergunta: pr ? lin(pr.innerText) : null, valendo: E.valendo(), ate: ate, agora: Date.now(), inst: dia ? dia.hora : null,
    acoes: rot ? [...rot.parentElement.querySelectorAll('a')].map((a) => ({ l: lin(a.innerText), href: a.getAttribute('href') })) : null, fala: fala ? lin(fala.innerText) : null, texto: raiz ? lin(raiz.innerText) : '', hash: location.hash,
    origem: pr ? lin(pr.parentElement.parentElement.querySelector(':scope > span:last-child').innerText) : null, diario: localStorage.getItem('capitao.diario.v1'), aviso: sessionStorage.getItem('capitao.emergenciaAte') }; }"""


def pergunta_b3(pg, q):
    """Pergunta pelo endereço (#q=…), como a H2 e os cartões da B2 fazem, e espera a tela mostrar a pergunta."""
    pg.evaluate("(q) => { location.hash = '#q=' + encodeURIComponent(q); }", q)
    pg.wait_for_function("(q) => { const e = document.querySelector('[data-b3=pergunta]'); return !!e && e.innerText.trim() === q; }", arg=q, timeout=6000)
    pg.wait_for_timeout(400)
    return pg.evaluate(LE_B3)


R_POSICAO = confere.R_COORD
R_NAV = re.compile(r'\d+(?:,\d+)?\s*nós|rumo\s*\d|proa\s*\d|\d+\s*pessoas|SOG\s*\d|\d+\s*mn\b', re.I)


def teste_carta_resposta(b):
    """B3: a resposta diz o segundo do instante em que foi calculada (uma vez por pergunta, nunca na emergência); depois de uma resposta que abre a janela de emergência a marca vale 15 min e posição, rumo,
    SOG, ETA e pessoas viram «LEIA NO PLOTTER»; salvatagem e MMSI não abrem a janela; o botão de uma resposta (#capitao-prop-… e #capitao-relato-…) vira a pergunta e nunca grava; sem link vazio."""
    prob = []
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_tela(b, 'B3-Carta-Resposta', fixo=fixo)
        r = pg.evaluate(LE_B3)
        rot = 'B3 a %s s' % fixo
        if r['hora'] != 'respondida às ' + r['inst']: prob.append('%s: a resposta diz %r (esperado «respondida às %s», o segundo do instante)' % (rot, r['hora'], r['inst']))
        if ('Resposta calculada às ' + r['inst']) not in r['texto']: prob.append('%s: o texto de cálculo não diz «Resposta calculada às %s»' % (rot, r['inst']))
        if not r['fala'] or r['inst'] not in r['fala']: prob.append('%s: a 1ª linha falada não traz a hora do quadro: %r' % (rot, r['fala']))
        ach = achados_termos('B3-Carta-Resposta', r['texto'])
        if ach: prob.append('%s: termo do §3 na tela: %s' % (rot, ach))
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    # a resposta é calculada uma vez por pergunta (o valor é o do momento dela, com a hora): sem congelar, o texto não anda sozinho; perguntar de novo recalcula
    ctx, pg, erros = abre_tela(b, 'B3-Carta-Resposta', fixo=None)
    a = pg.evaluate(LE_B3)
    pg.wait_for_timeout(2300)
    c = pg.evaluate(LE_B3)
    if a['hora'] != c['hora'] or a['texto'] != c['texto']: prob.append('B3 livre: a resposta mudou sozinha em 2,3 s (%r → %r): devia ser calculada uma vez' % (a['hora'], c['hora']))
    pg.evaluate("() => [...document.querySelectorAll('#dc-root button')].find((x) => x.innerText.trim() === 'Motores').click()")
    pg.wait_for_timeout(700)
    d = pg.evaluate(LE_B3)
    if d['hora'] == a['hora'] or not d['hora']: prob.append('B3 livre: perguntar de novo não recalculou (hora %r → %r)' % (a['hora'], d['hora']))
    if erros: prob += erros[:2]
    ctx.close()
    # a janela de conversa em emergência
    ctx, pg, erros = abre_tela(b, 'B3-Carta-Resposta')
    PLOTTER = pg.evaluate("() => window.CapitaoDados.protocolos.plotter")
    normal = {q: pergunta_b3(pg, q) for q in ('qual a velocidade?', 'quanto falta para chegar?')}
    for q, r in normal.items():
        if not R_NAV.search(r['texto']): prob.append('controle: «%s» fora da janela devia dar número (nós, mn…) e deu %r' % (q, r['texto'][:160]))
    pos0 = pergunta_b3(pg, 'qual a nossa posição?')
    if not R_POSICAO.search(pos0['texto']) or pos0['valendo']: prob.append('controle: a posição fora da janela devia ter coordenada, sem a marca: %r (marca %s)' % (pos0['texto'][:140], pos0['valendo']))
    for chave in ('mayday', 'canal 16', 'epirb', 'seafire', 'Pressão de óleo baixa: o que verificar primeiro?'):
        pg.evaluate("() => window.CapitaoEmergencia.zera()")
        r = pergunta_b3(pg, chave)
        rot = 'B3 «%s»' % chave
        if not r['valendo'] or not (r['agora'] < r['ate'] <= r['agora'] + 15 * 60 * 1000 + 2000): prob.append('%s: a resposta devia abrir a janela de 15 min (marca %s, fim %s, agora %s)' % (rot, r['valendo'], r['ate'], r['agora']))
        if r['hora'] is not None: prob.append('%s: a resposta de emergência leva a hora do quadro: %r' % (rot, r['hora']))
        if R_POSICAO.search(r['texto']) or R_NAV.search(r['texto'].replace('canal 16', '')): prob.append('%s: a resposta de emergência traz posição, rumo, SOG ou pessoas: %s' % (rot, (R_POSICAO.findall(r['texto']) or R_NAV.findall(r['texto']))[:3]))
    # dentro da janela (a marca do último passo vale): a posição, a velocidade, a chegada e as pessoas viram a instrução do plotter, sem número
    for q in ('qual a nossa posição?', 'qual a velocidade?', 'quanto falta para chegar?', 'quantas pessoas a bordo?'):
        r = pergunta_b3(pg, q)
        if PLOTTER not in r['texto'] or R_POSICAO.search(r['texto']) or R_NAV.search(r['texto']): prob.append('B3 na janela: «%s» devia dar só «%s» e deu %r' % (q, PLOTTER, r['texto'][:200]))
        if r['hora'] is not None: prob.append('B3 na janela: «%s» leva a hora do quadro (%r)' % (q, r['hora']))
    # fora da janela de novo (a marca zerada): a posição volta com coordenada (o que muda a resposta é a marca)
    pg.evaluate("() => window.CapitaoEmergencia.zera()")
    r = pergunta_b3(pg, 'qual a nossa posição?')
    if not R_POSICAO.search(r['texto']) or r['valendo']: prob.append('B3 com a marca zerada: a posição devia voltar com coordenada: %r' % r['texto'][:140])
    # salvatagem e MMSI são perguntas de rotina: não ligam a janela e não levam a hora do quadro
    for q in ('onde ficam os coletes salva-vidas?', 'qual o MMSI do barco?'):
        pg.evaluate("() => window.CapitaoEmergencia.zera()")
        r = pergunta_b3(pg, q)
        if r['valendo']: prob.append('B3 «%s»: a pergunta de rotina abriu a janela de emergência' % q)
        if r['hora'] is not None: prob.append('B3 «%s»: a resposta de segurança leva a hora do quadro: %r' % (q, r['hora']))
    # a ação sem destino (o checklist guiado ainda não tem tela) não vira link vazio
    r = pergunta_b3(pg, 'onde ficam os coletes salva-vidas?')
    if r['acoes'] is None or any(not a['href'] for a in r['acoes']): prob.append('B3: a resposta tem ação sem destino: %s' % r['acoes'])
    if erros: prob += erros[:2]
    ctx.close()
    # o botão de uma resposta vira a pergunta (o cérebro escuta o clique e avisa a tela) e esta tela nunca grava no diário
    ctx, pg, erros = abre_tela(b, 'B3-Carta-Resposta')
    ant = pg.evaluate("() => localStorage.getItem('capitao.diario.v1')")
    pg.evaluate("() => window.dispatchEvent(new CustomEvent('capitao-chat-pergunta', { detail: { q: 'Autonomia' } }))")
    pg.wait_for_timeout(700)
    r = pg.evaluate(LE_B3)
    if r['pergunta'] != 'Autonomia' or r['origem'] is None or 'Botão da resposta' not in r['origem']: prob.append('B3: o evento capitao-chat-pergunta não virou a pergunta (pergunta %r, origem %r)' % (r['pergunta'], r['origem']))
    for href, esperado in (('#capitao-relato-registra-tabc123', 'registrar o relato'), ('#capitao-relato-cancela-tabc123', 'não registrar o relato'), ('#capitao-prop-confirma-7', 'confirmar a proposta'), ('#capitao-prop-recusa-7', 'recusar a proposta')):
        pg.evaluate("(h) => { const a = document.createElement('a'); a.href = h; a.id = 'bt'; a.textContent = 'x'; document.body.appendChild(a); }", href)
        pg.click('#bt')
        pg.wait_for_timeout(600)
        r = pg.evaluate(LE_B3)
        pg.evaluate("() => document.getElementById('bt').remove()")
        if r['pergunta'] != esperado: prob.append('B3: o botão %s devia perguntar «%s» e perguntou %r' % (href, esperado, r['pergunta']))
        if r['diario'] != ant: prob.append('B3: o botão %s gravou no diário' % href)
        if r['hash'].startswith('#capitao-'): prob.append('B3: o botão %s ficou no endereço (%s): o link não devia navegar' % (href, r['hash']))
    if erros: prob += erros[:2]
    ctx.close()
    return prob


# B1 nos 4 tamanhos da web: a leitura de cada motor (2 linhas, com o arrefecimento) e a linha do diesel não são cortadas, e o último texto de cada cartão fica dentro dele
LE_CORTE_B1 = """() => { const secs = [...document.querySelectorAll('main section')].filter((s) => getComputedStyle(s).overflow === 'hidden');
  const folga = secs.map((s) => { const r = s.getBoundingClientRect(); let maxb = 0; s.querySelectorAll('*').forEach((e) => { if (e.children.length === 0 && (e.innerText || '').trim()) maxb = Math.max(maxb, e.getBoundingClientRect().bottom); });
    return { t: (s.innerText || '').trim().slice(0, 14).replace(/\\n/g, ' '), folga: Math.round((r.bottom - maxb) * 10) / 10 }; });
  return { motor: [...document.querySelectorAll('[data-b1=motor-leitura]')].map((e) => ({ h: e.scrollHeight > e.clientHeight + 1, w: e.scrollWidth > e.clientWidth + 1, texto: (e.innerText || '').trim() })),
    diesel: (() => { const e = document.querySelector('[data-b1=diesel-tanques]'); return e ? { w: e.scrollWidth > e.clientWidth + 1, texto: e.innerText.trim() } : null; })(), folga }; }"""


def teste_carta_corte(b):
    prob = []
    for (w, h) in WEB:
        for fixo in ('60', '105'):
            ctx, pg, erros = abre_tela(b, 'B1-Carta-Web', w=w, h=h, fixo=fixo)
            r = pg.evaluate(LE_CORTE_B1)
            rot = 'B1 %dx%d a %s s' % (w, h, fixo)
            for m in r['motor']:
                if m['h'] or m['w']: prob.append('%s: a leitura do motor está cortada: %r' % (rot, m['texto']))
            if not r['diesel'] or r['diesel']['w']: prob.append('%s: a linha do diesel está cortada: %r' % (rot, r['diesel']))
            ruins = [x for x in r['folga'] if x['folga'] < 1]
            if ruins: prob.append('%s: o texto passa da borda de baixo do cartão: %s' % (rot, ruins))
            if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
            ctx.close()
    return prob


def teste_carta_vivo(b):
    """Sem congelar o replay, o que a B1 e a B2 mostram do quadro muda em 1,5 s (as telas assinam o capitao-telemetria; a moldura sozinha já muda)."""
    prob = []
    for tela, sel in (('B1-Carta-Web', '[data-motor=bb] [data-b1=motor-leitura]'), ('B2-Carta-Mobile', '[data-sistema=motores] [data-b2=estado]')):
        ctx, pg, erros = abre_tela(b, tela, fixo=None)
        mudou = False
        for _ in range(3):
            a = pg.evaluate("(s) => document.querySelector(s).innerText", sel)
            pg.wait_for_timeout(1500)
            if a != pg.evaluate("(s) => document.querySelector(s).innerText", sel): mudou = True; break
        if not mudou: prob.append('%s: a propulsão não mudou em 1,5 s sem congelar o replay (3 tentativas): a tela não assina o capitao-telemetria' % tela)
        if erros: prob += erros[:2]
        ctx.close()
    return prob


def teste_carta_real(b):
    """Ramo simulacao false: o instante cai na última leitura salva (o D.snapshot): motores desligados, âncora e porão do que o snapshot tem, sem NaN, undefined nem [object Object]."""
    prob = []
    for tela, JS in (('B1-Carta-Web', LE_B1), ('B2-Carta-Mobile', LE_B2)):
        ctx, pg, erros = abre_tela(b, tela, fixo=None, depois='window.CapitaoDados.simulacao = false;')
        r = pg.evaluate("() => ({ replay: window.CapitaoReplay.ativo(), texto: document.body.innerText, fonte: window.CapitaoAgora.instante().fonte })")
        rot = '%s com simulacao false' % tela
        if r['replay'] or r['fonte'] != 'snapshot': prob.append('%s: o replay ainda anda (%s)' % (rot, r['fonte']))
        if re.search(r'NaN|undefined|\[object', r['texto']): prob.append('%s: NaN, undefined ou [object na tela' % rot)
        if tela.startswith('B1'):
            t = pg.evaluate(JS)
            if not (t['estado'] or '').startswith('Desligados · marcha neutro · última leitura 26/09 10:12'): prob.append('%s: o estado diz %r (esperado «Desligados · marcha neutro · última leitura 26/09 10:12»)' % (rot, t['estado']))
            if t['diesel'] != '≈ 848 L' or not (t['dieselHora'] or '').startswith('Última leitura · 26/09 10:12'): prob.append('%s: o diesel diz %r %r (esperado a última leitura salva: 848 L)' % (rot, t['diesel'], t['dieselHora']))
            if 'Sábado, 26/09' not in (t['resumo'] or '') or 'Última leitura · 26/09 10:12' not in (t['resumo'] or ''): prob.append('%s: o resumo diz %r (esperado o dia e a hora da última leitura)' % (rot, t['resumo']))
        else:
            t = pg.evaluate(JS)
            if t['rows']['porao']['estado'] != 'porão: BB 1,2 cm · BE 0,9 cm · bomba 0 ciclos/h' or t['agora'] != 'última leitura 26/09 10:12': prob.append('%s: o porão diz %r e o rótulo %r (esperado a última leitura salva)' % (rot, t['rows']['porao']['estado'], t['agora']))
            if not t['rows']['motores']['estado'].startswith('Desligados · horímetros BB 412,6 · BE 409,8 h'): prob.append('%s: os motores dizem %r' % (rot, t['rows']['motores']['estado']))
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    return prob


# o código das três telas
def teste_carta_codigo():
    prob = []
    def le_(a):   # o arquivo do disco, com o defeito plantado (MUT_ARQ) se houver
        t = open(os.path.join(RAIZ, a), encoding='utf-8').read()
        for velho, novo in MUT_ARQ.get(a, []): t = t.replace(velho, novo, 1)
        return t
    GEOM = re.compile(r'<(?:svg|path|circle|line|rect|ellipse|polyline|polygon|g)\b[^>]*\b(?:d|x|y|x1|x2|y1|y2|cx|cy|r|rx|ry|width|height|viewBox|points|transform)="[^"]*\{\{')
    for t in TELAS_P4D:
        h = le_(t + '.dc.html')
        if GEOM.search(h): prob.append('%s: {{…}} em atributo geométrico de SVG' % t)
        if re.search(r'D\.demo|\.demo\b|DEMO', h): prob.append('%s: lê D.demo ou escreve DEMO no código' % t)
        if re.search(r'D\.snapshot|\.snapshot\b', h): prob.append('%s: lê o D.snapshot (o dado vem do instante)' % t)
        mont, desm = h.find('componentDidMount'), h.find('componentWillUnmount')
        if t != 'B3-Carta-Resposta':
            for ev in ('capitao-telemetria', 'capitao-rebase'):
                if "addEventListener('%s'" % ev not in h[mont:desm] or "removeEventListener('%s'" % ev not in h[desm:]: prob.append('%s: não assina o %s no componentDidMount e remove no componentWillUnmount' % (t, ev))
            if 'document.hidden' not in h: prob.append('%s: não pausa com document.hidden' % t)
            if 'if (k === this._k) return;' not in h or 'this.setState({ vivo: k })' not in h: prob.append('%s: não compara o texto antes do setState' % t)
            if h.count('setInterval') > 1: prob.append('%s: setInterval novo (%d)' % (t, h.count('setInterval')))
        else:
            if "addEventListener('capitao-chat-pergunta'" not in h[mont:desm] or "removeEventListener('capitao-chat-pergunta'" not in h[desm:]: prob.append('%s: não escuta o capitao-chat-pergunta (os botões das respostas)' % t)
            if 'a.abreJanela === true' not in h or 'E.marca()' not in h: prob.append('%s: não marca a janela de emergência quando a resposta a abre' % t)
            if 'emergencia: emergencia' not in h or 'E.valendo()' not in h: prob.append('%s: não passa a marca da janela ao cérebro (answer com emergencia)' % t)
            if 'commit: false' not in h: prob.append('%s: a resposta deixou de ser commit:false (esta tela não grava)' % t)
            if re.search(r'localStorage\s*\.\s*setItem|addDiario|markExec|addDoc\b|addAbast|addTarefa|criaAlarmePedido|apagaAlarmePedido', h): prob.append('%s: grava no aparelho' % t)
            if 'capitao-ia' in h: prob.append('%s: carrega a IA na nuvem (esta tela responde só com o cérebro local; a IA é das telas de conversa)' % t)
            if '.filter((x) => x && x.l && x.href)' not in h: prob.append('%s: não tira a ação sem destino' % t)
    return prob


def p4d_conferencias(b, lista):
    """[(nome, problemas)] das conferências da P4D para as telas da rodada."""
    out = []
    if any(t in lista for t in TELAS_P4D): out.append(('código da Carta', teste_carta_codigo()))
    if 'B1-Carta-Web' in lista: out.append(('B1 · propulsão, diesel, cartões e prazos', teste_carta_web(b)))
    if 'B1-Carta-Web' in lista: out.append(('B1 · nada cortado nos 4 tamanhos da web', teste_carta_corte(b)))
    if 'B2-Carta-Mobile' in lista: out.append(('B2 · estado de cada sistema', teste_carta_app(b)))
    if 'B3-Carta-Resposta' in lista: out.append(('B3 · hora da resposta, janela de emergência e botões', teste_carta_resposta(b)))
    if 'B1-Carta-Web' in lista or 'B2-Carta-Mobile' in lista: out.append(('B1 e B2 · a propulsão anda sem congelar o replay', teste_carta_vivo(b)))
    if 'B1-Carta-Web' in lista or 'B2-Carta-Mobile' in lista: out.append(('simulacao false na B1 e na B2', teste_carta_real(b)))
    return out


# Defeitos plantados da P4D: cada um é servido no lugar do arquivo (MUT_ARQ) e a conferência que cuida dele TEM de acusar (--mutantes-p4d; um mutante vivo reprova).
MUTANTES_P4D = [
    ('o diesel da B1 fixo no snapshot (848 L)', 'B1-Carta-Web.dc.html', [("dieselL: tem('diesel_litros') ? '≈ ' + c('diesel_litros') : falta(SL),", "dieselL: '≈ 848',")], 'web'),
    ('as horas até a troca do óleo da B1 só da agenda gerada (não do horímetro de agora)', 'B1-Carta-Web.dc.html', [("const f = I && I.calc && I.calc.faltam ? I.calc.faltam[t.id] : undefined; return num(f) ? f : num(h.faltam) ? h.faltam : null;", "return num(h.faltam) ? h.faltam : null;")], 'web'),
    ('a propulsão da B1 sem a fase da reprodução («ligados · cruzeiro»)', 'B1-Carta-Web.dc.html', [("(ligados && fase ? ' · ' + fase : '')", "''")], 'web'),
    ('a B1 com o dia fixo do snapshot (sábado, 26/09)', 'B1-Carta-Web.dc.html', [("const ms = I && !reserva ? I.ms : q ? Date.parse(q.timestamp_utc) : NaN,", "const ms = Date.parse('2026-09-26T10:12:00-03:00'),")], 'web'),
    ('a B1 conta as pendências sem tirar as resolvidas por linha nova', 'B1-Carta-Web.dc.html', [("B.pendenciasLista().filter((p) => p.aberta) : null;", "B.pendenciasLista() : null;")], 'web'),
    ('a B1 conta a tarefa executada como atrasada', 'B1-Carta-Web.dc.html', [("const abertas = tarefas.filter((t) => !ex[t.id] && !t.feita && num(t.dn))", "const abertas = tarefas.filter((t) => !t.feita && num(t.dn))")], 'web'),
    ('o fabricante dos motores fixo na B1 (Cummins)', 'B1-Carta-Web.dc.html', [("(eM.fabricante || falta('fabricante ' + SD))", "'Cummins'")], 'web'),
    ('a B1 sem a cor de AVISO no motor (o arrefecimento do BE a 105 s)', 'B1-Carta-Web.dc.html', [("tomK: ligados ? pior : ''", "tomK: ''")], 'web'),
    ('a leitura do motor da B1 numa linha só (o arrefecimento cortado)', 'B1-Carta-Web.dc.html', [("display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; overflow-wrap: anywhere;\">{{m.s}}", "white-space: nowrap; overflow: hidden; text-overflow: ellipsis;\">{{m.s}}")], 'corte'),
    ('a linha do diesel da B1 de volta com o desenho dos tanques (BE cortado)', 'B1-Carta-Web.dc.html', [("dieselS: tem('diesel_bb_pct') ? 'de ' + mil(CAP) + ' L · BB '", "dieselS: tem('diesel_bb_pct') ? 'de ' + mil(CAP) + ' L (' + nDiesel + ' × ' + mil(CAP / nDiesel) + ' L) · BB '")], 'corte'),
    ('a B1 sem assinar o capitao-telemetria', 'B1-Carta-Web.dc.html', [("    window.addEventListener('capitao-telemetria', this._onTele);\n", "")], 'vivo'),
    ('a B2 sem assinar o capitao-telemetria', 'B2-Carta-Mobile.dc.html', [("    window.addEventListener('capitao-telemetria', this._onTele);\n", "")], 'vivo'),
    ('o estado do EPIRB da B2 de volta com SEM DADOS', 'B2-Carta-Mobile.dc.html', [("estado: PADRAO + ' · ' + notaEtiqueta(eq('epirb'), 'epirb')", "estado: 'SEM DADOS — modelo, localização a bordo, acionamento e validade da bateria não carregados'")], 'app'),
    ('o estado do Seafire da B2 sem a nota da etiqueta', 'B2-Carta-Mobile.dc.html', [("estado: PADRAO + ' · ' + notaEtiqueta(eq('seafire'), 'seafire')", "estado: PADRAO")], 'app'),
    ('o fabricante do gerador fixo na B2 (Onan)', 'B2-Carta-Mobile.dc.html', [("fab: fab(eq('gerador')),", "fab: 'Onan QD 9',")], 'app'),
    ('as bombas de porão da B2 sem fabricante nem modelo (de volta ao texto fixo)', 'B2-Carta-Mobile.dc.html', [("fab: fab(eq('porao'), 'Bombas de porão'),", "fab: 'Bombas de porão · fabricante SEM DADOS · modelo SEM DADOS',")], 'app'),
    ('a climatização da B2 de volta com SEM LEITURA', 'B2-Carta-Mobile.dc.html', [("(q && typeof q.climatizacao_ativa === 'boolean' ? (q.climatizacao_ativa ? 'Ligada' : 'Desligada') : falta(SL))", "'SEM LEITURA no coletor'")], 'app'),
    ('o estado dos motores da B2 sem a fase («ligados · cruzeiro»)', 'B2-Carta-Mobile.dc.html', [("'Ligados' + (fase ? ' · ' + fase : '') + ' · '", "'Ligados · '")], 'app'),
    ('a B2 conta a tarefa executada como atrasada', 'B2-Carta-Mobile.dc.html', [("t.dn < 0 && !ex[t.id] && !t.feita)", "t.dn < 0 && !t.feita)")], 'app'),
    ('o rótulo da hora da B2 de volta com «snapshot … ao vivo desligado»', 'B2-Carta-Mobile.dc.html', [("snapLabel: I ? (reserva ? 'última leitura ' + lei : 'ao vivo · ' + I.hora) : falta(SL),", "snapLabel: 'snapshot 26/09 10:12 · ao vivo desligado',")], 'app'),
    ('a B3 sem passar a marca da janela de emergência ao cérebro (a posição sai com coordenada)', 'B3-Carta-Resposta.dc.html', [("emergencia: emergencia }", "emergencia: false }")], 'resposta'),
    ('a B3 não marca a janela quando a resposta a abre', 'B3-Carta-Resposta.dc.html', [("if (E) E.marca();", "")], 'resposta'),
    ('a B3 mostra o segundo do quadro também na resposta de emergência', 'B3-Carta-Resposta.dc.html', [("const hora = a && typeof a.hora === 'string' ? a.hora : '',", "const hora = a && typeof a.hora === 'string' ? a.hora : (window.CapitaoAgora.instante() || {}).hora || '',")], 'resposta'),
    ('a B3 sem escutar os botões das respostas (capitao-chat-pergunta)', 'B3-Carta-Resposta.dc.html', [("    window.addEventListener('capitao-chat-pergunta', this._chat);\n", "")], 'resposta'),
    ('a B3 com link vazio na ação sem destino', 'B3-Carta-Resposta.dc.html', [(".filter((x) => x && x.l && x.href)", "")], 'resposta'),
    ('a B3 sem dizer a hora da resposta', 'B3-Carta-Resposta.dc.html', [("temHora: !!hora,", "temHora: false,")], 'resposta'),
]


def mutantes_p4d(b):
    global MUT_ARQ
    vivos = []
    for nome, arq, trocas, qual in MUTANTES_P4D:
        src = open(os.path.join(RAIZ, arq), encoding='utf-8').read()
        faltam = [x for x, _ in trocas if src.count(x) != 1]
        if faltam:
            print('ERRO no mutante «%s»: o trecho não está uma vez em %s: %s' % (nome, arq, faltam)); vivos.append(nome); continue
        MUT_ARQ = {arq: trocas}
        sai = sys.stdout
        prob = []
        try:
            sys.stdout = open(os.devnull, 'w')
            prob = {'web': lambda: teste_carta_web(b), 'app': lambda: teste_carta_app(b), 'resposta': lambda: teste_carta_resposta(b), 'corte': lambda: teste_carta_corte(b), 'vivo': lambda: teste_carta_vivo(b) + teste_carta_codigo(), 'codigo': lambda: teste_carta_codigo()}[qual]()
        except Exception as e:   # um erro do próprio teste não conta como acusação (esconderia um defeito do teste): o mutante fica vivo
            sys.stdout = sai
            print('ERRO do teste no mutante «%s»: %s' % (nome, str(e).splitlines()[-1][:160]))
            prob = []
        finally:
            sys.stdout = sai
            MUT_ARQ = {}
        print('MUTANTE %s: %s (%d problema(s))%s' % ('ACUSADO' if prob else 'VIVO', nome, len(prob), ' · ' + prob[0][:150] if prob else ''))
        if not prob: vivos.append(nome)
    print('%d mutantes · %d vivos' % (len(MUTANTES_P4D), len(vivos)))
    return vivos


# ——— P4E: o Leme (C1 Manutenção, C2, C3 alerta vivo) e os checklists (C4 web e app) ———
# PROMPT Fase 4 e linha P4E (MAPA §6 C1, C2, C3; PARIDADE F05 e F09; CONTRATO §1.18, §1.22 a §1.25). Cada conferência abaixo tem defeito plantado que a faz falhar (MUTANTES_P4E, rodados com
# --mutantes-p4e): o teste só vale se acusa o defeito. `--so-p4e` roda só as conferências da P4E.
TELAS_P4E = ('C1-Leme-Web', 'C2-Leme-Mobile', 'C3-Leme-Alerta', 'C4-Checklist-Web', 'C4-Checklist-Mobile')
CRITICO_PLANTADO = "window.CapitaoDados.replay.cenario = 'alarme-critico'; window.CapitaoDados.replay.limites.motor_be_arref_c.critico = { acima: 85 };"   # o crítico só existe com o cenário (desligado no gerador)
MARCAS_FIXAS = re.compile(r'Volvo|Penta|Cummins|Onan|Seakeeper|Webasto|Garmin|Victron|Lewmar|Raymarine|Icom|Fusion|Schenker|Ocean Signal|em-trak')   # fabricante nunca fixo na tela (vem de D.equipamentos)


def pl(n, um, varios):
    return '%d %s' % (n, um if n == 1 else varios)


# C1 e C2: o texto que a tela mostra de cada bloco, o instante, as contagens do CapitaoAgora e o que o cérebro tem das tarefas da equipe
LE_LEME = """() => { """ + JS_BASE + """
  const un = (s) => { const e = document.querySelector(s); return e ? lin(e.innerText) : null; }, C = A.contagens(), B = window.CapitaoBrain;
  const live = {}; document.querySelectorAll('[data-live]').forEach((e) => { live[e.getAttribute('data-live')] = lin(e.innerText); });
  const linhas = {}, ids = []; document.querySelectorAll('[data-tarefa]').forEach((e) => { linhas[e.getAttribute('data-tarefa')] = lin(e.innerText); ids.push(e.getAttribute('data-tarefa')); });
  const cartoes = [...document.querySelectorAll('section button[aria-pressed]')].filter((e) => /filtr|filtro/.test(e.innerText)).map((e) => lin(e.innerText));
  const eq = B && B.tarefasEquipe ? B.tarefasEquipe().map((t) => ({ id: t.id, dn: t.dn, n: t.n })) : [];
  const fm = {}; D.agenda.filter((t) => t.horas).forEach((t) => { fm[t.id] = { faltam: F.nb(I.calc.faltam[t.id], 1, false), limite: F.nb(t.horas.limite, 0, true), agenda: F.nb(t.horas.faltam, 1, false) }; });
  const atr = D.agenda.filter((t) => t.dn < 0).map((t) => t.equip.split(' (')[0] + ' · ' + (-t.dn) + ' d');
  return { T, hora: I.hora, fase: I.fase && I.fase.nome, C, live, linhas, ids, idsEsp: D.agenda.map((t) => t.id).concat(eq.map((t) => t.id)), cartoes, eq, fm, atr, versao: D.versao, nAg: D.agenda.length, nEq: D.tarefasEquipe.length,
    resumo: un('[data-c1=resumo]'), leituraSub: un('[data-c1=leitura-sub]'), atrSub: un('[data-c2=atr-sub]'), hor: un('[data-c2=horimetros-txt]'), horSub: un('[data-c2=horimetros-sub]'),
    texto: lin(document.body.innerText), executado: localStorage.getItem('capitao.executado.v1'), diario: localStorage.getItem('capitao.diario.v1') }; }"""
ORACULO_FALTAM = {'motores-oleo': '32,4', 'gerador-revisao': '58,6'}   # CONTRATO §1.23: as horas que faltam às 12:01:00 e 12:01:45 (a agenda gerada diz 37,4 e 63,6)


def esperado_live_c1(r):
    T, f = r['T'], r['fase']
    return {'sog': 'Velocidade %s nós navegando · %s' % (T['sog_nos'], f), 'proa': 'Proa %s° %s satélites' % (T['proa_graus'], T['gps_satelites']),
            'vento': 'Vento %s nós a bordo agora · verdadeiro de %s°' % (T['vento_verdadeiro_nos'], T['vento_verdadeiro_angulo']),
            'bateria': 'Banco 24 V %s V banco 12 V %s V' % (T['bateria_0_tensao_v'], T['bateria_2_tensao_v']),
            'agua-mar': 'Água do mar %s °C ar %s °C · %s hPa' % (T['temp_agua_c'], T['temp_ar_externo_c'], T['pressao_barometrica_hpa']),
            'agua-doce': 'Água doce %s %% cinzas %s %% · negras %s %%' % (T['tanque_agua_pct'], T['tanque_cinzas_pct'], T['tanque_negras_pct'])}


def problemas_faltam(r, rot, prob):
    for id_, f in r['fm'].items():
        esp = 'ou %s h (faltam %s h)' % (f['limite'], f['faltam'])
        if f['faltam'] != ORACULO_FALTAM.get(id_, f['faltam']): prob.append('%s: calc.faltam de %s é %s (o contrato diz %s)' % (rot, id_, f['faltam'], ORACULO_FALTAM[id_]))
        if esp not in r['linhas'].get(id_, ''): prob.append('%s: a linha de %s devia ter «%s» (as horas do horímetro de agora, não as %s da agenda gerada): %r' % (rot, id_, esp, f['agenda'], r['linhas'].get(id_)))


def teste_leme_c1(b):
    """C1: as 6 leituras de agora são as do quadro (CapitaoAgora.fmt.campo; o vento «a bordo agora»), o resumo e a fonte da leitura sem rótulo, as horas que faltam são as do horímetro de agora, os 3 cartões
    iguais às contagens do CapitaoAgora (a agenda gerada e as tarefas da equipe, as do aparelho também; Executado acompanha) e o Executado de uma tarefa do aparelho grava 1 linha nova; tudo a 60 s e a 105 s."""
    prob = []
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_tela(b, 'C1-Leme-Web', fixo=fixo)
        r = pg.evaluate(LE_LEME)
        rot, C, h = 'C1 a %s s' % fixo, r['C'], r['hora']
        esp = 'Telemetria ao vivo · %s · %d tarefas · %s · horímetros BB %s h · BE %s h · prazos contados a partir de %s' % (h, r['nAg'] + r['nEq'], pl(C['atrasadas'], 'atrasada', 'atrasadas'), r['T']['motor_bb_horimetro_h'], r['T']['motor_be_horimetro_h'], r['versao'])
        if r['resumo'] != esp: prob.append('%s: o resumo diz %r (esperado %r)' % (rot, r['resumo'], esp))
        if r['leituraSub'] != 'Telemetria ao vivo · ' + h: prob.append('%s: a fonte da leitura diz %r (esperado «Telemetria ao vivo · %s»)' % (rot, r['leituraSub'], h))
        for k, v in esperado_live_c1(r).items():
            if r['live'].get(k) != v: prob.append('%s: o cartão %s diz %r (esperado %r, do quadro)' % (rot, k, r['live'].get(k), v))
        problemas_faltam(r, rot, prob)
        if sorted(r['ids']) != sorted(r['idsEsp']): prob.append('%s: a lista tem %d tarefas (esperado %d: a agenda e as da equipe)' % (rot, len(r['ids']), len(r['idsEsp'])))
        n = [int(re.match(r'\d+', c).group(0)) for c in r['cartoes']]
        if n != [C['atrasadas'], C['d30'], C['d60'] + C['d90'] + C['emDia']]: prob.append('%s: os cartões mostram %s (esperado %s, as contagens do CapitaoAgora)' % (rot, n, [C['atrasadas'], C['d30'], C['d60'] + C['d90'] + C['emDia']]))
        ach = achados_termos('C1-Leme-Web', pg.evaluate(LE_TEXTOS))
        if ach: prob.append('%s: termo do §3 na tela: %s' % (rot, ach))
        if r['executado'] or r['diario']: prob.append('%s: a tela gravou no registro ao abrir (Executado %r, diário %r)' % (rot, r['executado'], r['diario']))
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    # Executado acompanha as contas e o «em dia»
    ctx, pg, erros = abre_tela(b, 'C1-Leme-Web', ls={'capitao.executado.v1': json.dumps({'porao-teste': {'d': '09/11', 't': '12:00'}})})
    r = pg.evaluate(LE_LEME)
    if r['C']['atrasadas'] != 2 or not r['cartoes'][0].startswith('2 ') or 'Bombas de porão' in r['cartoes'][0] or 'feito · 09/11' not in r['linhas']['porao-teste'] or 'inclui 1 executada' not in r['cartoes'][2]:
        prob.append('C1 com o teste do porão executado: os cartões dizem %s (esperado 2 atrasadas, sem as bombas, «feito · 09/11» na linha e «inclui 1 executada»): %r' % (r['cartoes'], r['linhas'].get('porao-teste')))
    if erros: prob += erros[:2]
    ctx.close()
    # tarefa do aparelho (F15): entra na lista e nas contas como no CapitaoAgora; o Executado dela é 1 linha nova no diário
    vence = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()
    tarefa = [{'id': 'gptest1', 'n': 'Trocar a lâmpada de navegação', 'vence': vence, 'quem': 'Lucas', 'sistema': 'Casco', 'origem': 'tela', 'iso': '2026-11-09T10:00:00-03:00', 'who': 'Lucas', 'sim': True}]
    ctx, pg, erros = abre_tela(b, 'C1-Leme-Web', ls={'capitao.tarefas.v1': json.dumps(tarefa)})
    r = pg.evaluate(LE_LEME)
    t = next((x for x in r['eq'] if x['id'] == 'gptest1'), None)
    n = [int(re.match(r'\d+', c).group(0)) for c in r['cartoes']]
    if not t or 'gptest1' not in r['linhas'] or ('D-%d' % t['dn']) not in r['linhas']['gptest1']: prob.append('C1 com uma tarefa do aparelho: a linha não aparece com o prazo do dia (D-%s): %r' % (t and t['dn'], r['linhas'].get('gptest1')))
    if r['C']['tarefasEquipe'] != 3 or n != [r['C']['atrasadas'], r['C']['d30'], r['C']['d60'] + r['C']['d90'] + r['C']['emDia']]: prob.append('C1 com uma tarefa do aparelho: os cartões %s não são as contagens do CapitaoAgora (%s)' % (n, r['C']))
    if t and 'gptest1' in r['linhas']:
        pg.evaluate("() => [...document.querySelectorAll('[data-tarefa=gptest1] button')].find((x) => x.innerText.trim() === 'Executado').click()")
        pg.wait_for_timeout(400)
        r2 = pg.evaluate(LE_LEME)
        linhas = json.loads(r2['diario'] or '[]')
        if len(linhas) != 1 or not linhas[0]['t'].startswith('Executado: Trocar a lâmpada de navegação (Casco)') or linhas[0].get('sim') is not True: prob.append('C1: o Executado da tarefa do aparelho devia gravar 1 linha nova com sim: %r' % linhas)
        if 'gptest1' not in json.loads(r2['executado'] or '{}') or 'feito' not in r2['linhas']['gptest1']: prob.append('C1: a tarefa executada não ficou feita na lista: %r' % r2['linhas'].get('gptest1'))
        if r2['C']['tarefasEquipe'] != 2: prob.append('C1: a tarefa executada ainda conta nas da equipe (%s)' % r2['C']['tarefasEquipe'])
    if erros: prob += erros[:2]
    ctx.close()
    # o filtro do endereço (#f=atrasadas)
    ctx, pg, erros = abre_tela(b, 'C1-Leme-Web', hash_='#f=atrasadas')
    r = pg.evaluate(LE_LEME)
    if len(r['ids']) != r['C']['atrasadas']: prob.append('C1#f=atrasadas: %d linhas (esperado %d)' % (len(r['ids']), r['C']['atrasadas']))
    ctx.close()
    return prob


def teste_leme_c2(b):
    """C2: o cartão das atrasadas e a lista iguais ao CapitaoAgora, o horímetro de agora (BB, BE e gerador) com a fonte do instante, as horas que faltam do horímetro de agora, sem rótulo; a 60 s e a 105 s."""
    prob = []
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_tela(b, 'C2-Leme-Mobile', fixo=fixo)
        r = pg.evaluate(LE_LEME)
        rot, C, T, h = 'C2 a %s s' % fixo, r['C'], r['T'], r['hora']
        esp = 'BB %s h · BE %s h · gerador %s h' % (T['motor_bb_horimetro_h'], T['motor_be_horimetro_h'], T['gerador_horimetro_h'])
        if r['hor'] != esp: prob.append('%s: os horímetros dizem %r (esperado %r, do quadro)' % (rot, r['hor'], esp))
        if r['horSub'] != 'Horímetros de agora · Telemetria ao vivo · ' + h: prob.append('%s: a fonte dos horímetros diz %r (esperado «Horímetros de agora · Telemetria ao vivo · %s»)' % (rot, r['horSub'], h))
        if r['atrSub'] != ' · '.join(r['atr']): prob.append('%s: as atrasadas dizem %r (esperado %r)' % (rot, r['atrSub'], ' · '.join(r['atr'])))
        if len(r['ids']) != C['atrasadas'] or C['atrasadas'] != 3: prob.append('%s: %d linhas na lista das atrasadas (esperado %d = CapitaoAgora)' % (rot, len(r['ids']), C['atrasadas']))
        pg.evaluate("() => [...document.querySelectorAll('button')].find((x) => x.innerText.trim() === 'Todas').click()"); pg.wait_for_timeout(400)
        r = pg.evaluate(LE_LEME)
        if len(r['ids']) != r['nAg'] + r['nEq']: prob.append('%s: «Todas» mostra %d linhas (esperado %d)' % (rot, len(r['ids']), r['nAg'] + r['nEq']))
        problemas_faltam(r, rot, prob)
        ach = achados_termos('C2-Leme-Mobile', pg.evaluate(LE_TEXTOS))
        if ach: prob.append('%s: termo do §3 na tela: %s' % (rot, ach))
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    ctx, pg, erros = abre_tela(b, 'C2-Leme-Mobile', ls={'capitao.executado.v1': json.dumps({'porao-teste': {'d': '09/11', 't': '12:00'}})})
    r = pg.evaluate(LE_LEME)
    if r['C']['atrasadas'] != 2 or 'Bombas de porão' in r['atrSub'] or 'EXECUTADO 09/11' not in r['linhas'].get('porao-teste', '') or not r['atrSub'].startswith('Climatização'):
        prob.append('C2 com o teste do porão executado: atrasadas %r, linha do porão %r (esperado 2 atrasadas sem as bombas, e a linha com «EXECUTADO 09/11»)' % (r['atrSub'], r['linhas'].get('porao-teste')))
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_leme_real(b):
    """Ramo simulacao false (C1, C2, C3 e C4): sem NaN, undefined nem [object; a C1 e a C2 leem a última leitura salva (horímetros de 26/09 10:12) e a C3 não diz «tudo dentro da faixa»."""
    prob = []
    for tela, hash_ in (('C1-Leme-Web', ''), ('C2-Leme-Mobile', ''), ('C3-Leme-Alerta', '#alarme=arref_be'), ('C4-Checklist-Web', ''), ('C4-Checklist-Mobile', '')):
        ctx, pg, erros = abre_tela(b, tela, fixo=None, depois='window.CapitaoDados.simulacao = false;', hash_=hash_)
        r = pg.evaluate("() => ({ replay: window.CapitaoReplay.ativo(), texto: document.body.innerText, fonte: window.CapitaoAgora.instante().fonte })")
        rot = '%s com simulacao false' % tela
        if r['replay'] or r['fonte'] != 'snapshot': prob.append('%s: o replay ainda anda (%s)' % (rot, r['fonte']))
        if re.search(r'NaN|undefined|\[object|Infinity', r['texto']): prob.append('%s: NaN, undefined ou [object na tela' % rot)
        if tela.startswith('C1'):
            t = pg.evaluate(LE_LEME)
            if t['leituraSub'] != 'Última leitura · 26/09 10:12' or 'horímetros BB 412,6 h · BE 409,8 h' not in t['resumo']: prob.append('%s: a leitura diz %r e o resumo %r (esperado a última leitura salva)' % (rot, t['leituraSub'], t['resumo']))
        if tela.startswith('C3') and ('Tudo dentro da faixa' in r['texto'] or 'SEM ALARME ATIVO' not in r['texto']): prob.append('%s: sem a reprodução ninguém avalia os limites: %r' % (rot, r['texto'][:160]))
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    return prob


# C3: o que a tela mostra do alerta, e o que a API de alertas e o replay dizem no mesmo instante
LE_C3 = """() => { """ + JS_BASE + """
  const AL = window.CapitaoAlertas, R = window.CapitaoReplay, g = (s) => { const e = document.querySelector('[data-c3=' + s + ']'); return e ? lin(e.innerText) : null; };
  const c = document.querySelector('[data-c3=cartao]'), lt = document.querySelector('[data-c3=leitura]'), pa = document.querySelector('[data-c3=passos]'), sp = document.querySelector('[data-c3=spark]');
  const kids = pa ? [...pa.children] : [], porId = (id) => AL.porId(id), a = AL.ativos()[0] || null;
  const cat = D.replay.alertas.arref_be, lim = D.replay.limites;
  return { hora: I.hora, ms: I.ms, fonteTxt: I.fonteTxt, selo: g('selo'), kicker: g('kicker'), titulo: g('titulo'), situacao: g('situacao'), equip: g('equip'), leitura: g('leitura'), leituraSub: g('leitura-sub'), faixa: g('faixa'), faixaSub: g('faixa-sub'),
    tendencia: g('tendencia'), tend30: g('tendencia30'), fonte: g('fonte'), info: g('info'), nota: g('nota'), registrado: g('registrado'), temRegistrar: !!document.querySelector('[data-c3=registrar]'),
    estado: c ? c.getAttribute('data-estado') : null, nivel: c ? c.getAttribute('data-nivel') : null, brilho: c ? c.getAttribute('data-brilho') : null, bg: c ? getComputedStyle(c).backgroundColor : null,
    pisca: lt ? lt.getAttribute('data-pisca') : null, anim: lt ? getComputedStyle(lt).animationName : null, cor: lt ? getComputedStyle(lt).color : null, corpo: getComputedStyle(document.body).backgroundColor,
    passos: pa ? { titulo: lin(kids[0].innerText), passos: kids.slice(1, -1).map((k) => lin(k.innerText)), fonte: lin(kids[kids.length - 1].innerText) } : null,
    spark: sp ? { pontos: (sp.querySelector('polyline').getAttribute('points').match(/ /g) || []).length + 1, limite: !!sp.querySelector('line') } : null,
    ativo: a ? { id: a.id, nivel: a.nivel, valorTxt: a.valorTxt, limiteTxt: a.limiteTxt, hora: a.hora, seg: a.seg, lado: a.lado } : null,
    janela: R.janela('arref_be'), cat: { titulo: cat.titulo, passos: cat.passos, fonte: cat.fonte, campo: cat.campo }, q95: R.quadro(95).motor_be_arref_c, q30: R.em(I.ms - 30000).motor_be_arref_c, agora: q.motor_be_arref_c,
    eq: D.equipamentos.filter((e) => e.id === 'motores').map((e) => [e.nome, e.qtd, e.fabricante, e.lados, e.modelo])[0], hora6: F.hora(R.janela('arref_be') ? R.janela('arref_be').ate || 0 : 0, true),
    url: location.href, cerebro: typeof window.CapitaoBrain, scripts: [...document.scripts].map((s) => s.getAttribute('src') || '').filter(Boolean), tema: document.documentElement.getAttribute('data-capitao-tema'),
    diario: localStorage.getItem('capitao.diario.v1'), falas: window.__falas || 0, texto: lin(document.body.innerText), faixaGlobal: !!document.getElementById('capitao-faixa-alertas') }; }"""
RGB_AVISO_CARTAO = 'rgba(240, 166, 58, 0.13)'


def nb1(x, c=1):
    return ('%.*f' % (c, abs(x))).replace('.', ',')


def sinal1(x, c=1):
    v = round(x, c)
    return ('+' if v > 0 else '−' if v < 0 else '') + nb1(v, c)


def problemas_c3_aviso(r, rot, equip=('Motores', 2, 'Cummins', 'BB e BE', 'QSB6.7 305')):
    """O AVISO do arrefecimento do BE a 105 s (12:01:45, desde 12:01:39): selo, título, situação, leitura «BE 89,6 °C · 12:01:45», faixa, tendência dos 10 s e dos 30 s, passos, equipamento e o pisca."""
    prob = []
    esp = {'selo': 'AVISO', 'kicker': 'Motores · BE', 'titulo': 'Temperatura do motor BE', 'situacao': '89,6 °C · acima de 88 °C · desde 12:01:39 · há 6 s', 'leitura': 'BE 89,6 °C · 12:01:45',
           'leituraSub': 'fora da faixa agora · telemetria ao vivo · 12:01:45', 'faixa': 'até 88 °C', 'faixaSub': 'aviso acima de 88 °C · crítico acima de 97 °C',
           'estado': 'ativo', 'nivel': 'aviso', 'brilho': '0', 'pisca': '1', 'anim': 'capPisca'}
    for k, v in esp.items():
        if r[k] != v: prob.append('%s: %s diz %r (esperado %r)' % (rot, k, r[k], v))
    nome, qtd, fab, lados, mod = equip
    if r['equip'] != '%s %d × %s (%s) · modelo %s · lado: BE' % (nome, qtd, fab, lados, mod): prob.append('%s: o equipamento diz %r (esperado o de D.equipamentos: %s × %s (%s) · modelo %s)' % (rot, r['equip'], qtd, fab, lados, mod))
    d10 = r['agora'] - r['q95']
    dir_ = 'subindo' if round(d10, 1) > 0 else 'caindo' if round(d10, 1) < 0 else 'estável'
    esp_t = '%s °C · %s (%s → %s)' % (sinal1(d10), dir_, nb1(r['q95']), nb1(r['agora']))
    if r['tendencia'] != esp_t: prob.append('%s: a tendência de 10 s diz %r (esperado %r: o quadro de 10 s atrás é o do segundo 95 da volta)' % (rot, r['tendencia'], esp_t))
    if r['tend30'] != 'últimos 30 s: +7,5 °C': prob.append('%s: a tendência de 30 s diz %r (esperado «últimos 30 s: +7,5 °C», o do cérebro, CONTRATO §1.23)' % (rot, r['tend30']))
    if not r['spark'] or r['spark']['pontos'] != 11 or not r['spark']['limite']: prob.append('%s: o traço dos últimos 10 s não tem os 11 pontos e a linha do limite: %r' % (rot, r['spark']))
    p = r['passos']
    if not p or p['titulo'] != 'Faça agora enquanto o alarme durar' or [re.sub(r'^\d+ ', '', x) for x in p['passos']] != r['cat']['passos'] or p['fonte'] != 'Fonte: ' + r['cat']['fonte']:
        prob.append('%s: os passos não são os do catálogo (%s): %r' % (rot, r['cat']['titulo'], p))
    if r['fonte'] != 'Telemetria ao vivo · 12:01:45 · faixa: Guia de bordo — Motores Cummins §9 · Faixas de operação': prob.append('%s: a fonte diz %r' % (rot, r['fonte']))
    return prob


def teste_c3_estados(b):
    """C3: o AVISO a 105 s (leitura com o lado e a hora, faixa normal, tendência, passos e equipamento de D.equipamentos; pisca), o NORMALIZADO a 60 s (às 11:59, o fim da volta anterior), sem alarme
    (neutro, sem rótulo), id fora do catálogo, id sem janela («dentro da faixa»), o alarme que estiver tocando quando não há #alarme, e a faixa do óleo pelo giro."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'C3-Leme-Alerta', fixo='105', hash_='#alarme=arref_be')
    r = pg.evaluate(LE_C3)
    prob += problemas_c3_aviso(r, 'C3 a 105 s')
    if r['bg'] != RGB_AVISO_CARTAO: prob.append('C3 a 105 s: o cartão do AVISO tem o fundo %s (esperado o âmbar translúcido, nunca o vermelho do crítico)' % r['bg'])
    if r['faixaGlobal']: prob.append('C3: a faixa global de alerta aparece na tela do próprio alerta')
    ach = achados_termos('C3-Leme-Alerta', pg.evaluate(LE_TEXTOS))
    if ach: prob.append('C3 a 105 s: termo do §3 na tela: %s' % ach)
    if r['diario'] or r['falas']: prob.append('C3 a 105 s: gravou no diário (%r) ou falou (%d)' % (r['diario'], r['falas']))
    if erros: prob += erros[:2]
    ctx.close()
    # o mesmo alerta com o equipamento trocado no D.equipamentos: nada de fabricante fixo
    ctx, pg, erros = abre_tela(b, 'C3-Leme-Alerta', fixo='105', hash_='#alarme=arref_be', depois=FAB_FALSOS)
    r = pg.evaluate(LE_C3)
    if r['equip'] != 'Motores 2 × Zyxmotor (BB e BE) · modelo Zyxmotor Mod9 · lado: BE': prob.append('C3: fabricante e modelo trocados no D.equipamentos e a tela diz %r' % r['equip'])
    ctx.close()
    # 60 s: o alarme acabou na volta anterior (11:59:27): NORMALIZADO, sem pisca, a leitura de agora dentro da faixa
    ctx, pg, erros = abre_tela(b, 'C3-Leme-Alerta', fixo='60', hash_='#alarme=arref_be')
    r = pg.evaluate(LE_C3)
    esp = {'selo': 'NORMALIZADO às 11:59', 'estado': 'normalizado', 'nivel': '', 'pisca': '0', 'anim': 'none', 'titulo': 'Temperatura do motor BE', 'situacao': 'normalizou às 11:59:27 · ficou 18 s fora da faixa (desde 11:59:09)',
           'leituraSub': 'dentro da faixa · telemetria ao vivo · 12:01:00', 'faixa': 'até 88 °C', 'brilho': '0'}
    for k, v in esp.items():
        if r[k] != v: prob.append('C3 a 60 s: %s diz %r (esperado %r)' % (k, r[k], v))
    if r['leitura'] != 'BE %s °C · 12:01:00' % nb1(r['agora']): prob.append('C3 a 60 s: a leitura diz %r (esperado «BE %s °C · 12:01:00»)' % (r['leitura'], nb1(r['agora'])))
    if r['cor'] != 'rgb(52, 199, 122)': prob.append('C3 a 60 s: a leitura dentro da faixa devia ser verde: %s' % r['cor'])
    if not r['passos'] or r['passos']['titulo'] != 'Depois do alarme o que conferir': prob.append('C3 a 60 s: os passos dizem %r' % (r['passos'] and r['passos']['titulo']))
    if not r['temRegistrar']: prob.append('C3 a 60 s: sem o botão de registrar a ocorrência')
    if erros: prob += erros[:2]
    ctx.close()
    # sem #alarme: a 60 s nenhum alarme (estado neutro, sem leitura nem rótulo); a 105 s o que estiver tocando
    ctx, pg, erros = abre_tela(b, 'C3-Leme-Alerta', fixo='60')
    r = pg.evaluate(LE_C3)
    if r['estado'] != 'nenhum' or r['selo'] != 'SEM ALARME ATIVO' or r['titulo'] != 'Nenhum alarme ativo agora' or r['leitura'] is not None or r['temRegistrar'] or not r['info'] or not r['situacao'].startswith('Tudo dentro da faixa às 12:01:00'):
        prob.append('C3 a 60 s sem #alarme: estado %r, selo %r, leitura %r, situação %r (esperado o estado neutro, sem leitura nem registrar)' % (r['estado'], r['selo'], r['leitura'], r['situacao']))
    ach = achados_termos('C3-Leme-Alerta', pg.evaluate(LE_TEXTOS))
    if ach: prob.append('C3 a 60 s sem #alarme: termo do §3 na tela: %s' % ach)
    ctx.close()
    ctx, pg, erros = abre_tela(b, 'C3-Leme-Alerta', fixo='105')
    r = pg.evaluate(LE_C3)
    prob += problemas_c3_aviso(r, 'C3 a 105 s sem #alarme (o que estiver tocando)')
    ctx.close()
    # id que não existe (nem 'constructor', nem '__proto__'): neutro, sem erro
    for h in ('#alarme=zzz', '#alarme=constructor', '#alarme=__proto__', '#alarme=%E0%A4%A'):
        ctx, pg, erros = abre_tela(b, 'C3-Leme-Alerta', fixo='105', hash_=h)
        r = pg.evaluate(LE_C3)
        if r['estado'] not in ('nenhum', 'ativo') or (h != '#alarme=%E0%A4%A' and r['estado'] != 'nenhum') or re.search(r'NaN|undefined|\[object', r['texto']): prob.append('C3 com %s: estado %r (esperado neutro, sem NaN)' % (h, r['estado']))
        if erros: prob += ['C3 com %s: %s' % (h, e) for e in erros[:2]]
        ctx.close()
    # alerta do catálogo sem janela no cenário aviso (o banco de 12 V): dentro da faixa, com a faixa do guia
    ctx, pg, erros = abre_tela(b, 'C3-Leme-Alerta', fixo='60', hash_='#alarme=b12')
    r = pg.evaluate(LE_C3)
    if r['selo'] != 'DENTRO DA FAIXA' or r['estado'] != 'normal' or r['faixa'] != 'de 12,2 a 14,7 V' or not r['leitura'].endswith(' V · 12:01:00') or r['passos'] is not None:
        prob.append('C3#alarme=b12 a 60 s: selo %r, faixa %r, leitura %r, passos %r (esperado DENTRO DA FAIXA, «de 12,2 a 14,7 V» e sem passos)' % (r['selo'], r['faixa'], r['leitura'], r['passos']))
    ctx.close()
    # a faixa do óleo é a do regime do giro (a partir de 1.000 rpm: 2,4 a 6,0 bar), com o aviso e o crítico do regime
    ctx, pg, erros = abre_tela(b, 'C3-Leme-Alerta', fixo='60', hash_='#alarme=oleo_bb')
    r = pg.evaluate(LE_C3)
    if r['faixa'] != 'de 2,4 a 6,0 bar (a partir de 1.000 rpm)' or r['faixaSub'] != 'aviso abaixo de 2,4 bar ou acima de 6,0 bar · crítico abaixo de 1,4 bar': prob.append('C3#alarme=oleo_bb: a faixa diz %r / %r (esperado a do regime de 1.000 rpm ou mais)' % (r['faixa'], r['faixaSub']))
    ctx.close()
    return prob


def teste_c3_critico(b):
    """C3 com o alarme CRÍTICO plantado (o cenário alarme-critico, desligado no gerador, injetado): selo, cartão vermelho que brilha, leitura vermelha, limite e faixa; nunca abre o SOS, fala ou grava."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'C3-Leme-Alerta', fixo='105', hash_='#alarme=arref_be', depois=CRITICO_PLANTADO)
    r = pg.evaluate(LE_C3)
    esp = {'selo': 'ALERTA CRÍTICO', 'estado': 'ativo', 'nivel': 'critico', 'brilho': '1', 'bg': 'rgb(211, 47, 39)', 'cor': 'rgb(255, 106, 96)', 'pisca': '1', 'leitura': 'BE 89,6 °C · 12:01:45',
           'faixaSub': 'aviso acima de 88 °C · crítico acima de 85 °C'}
    for k, v in esp.items():
        if r[k] != v: prob.append('C3 crítico: %s diz %r (esperado %r)' % (k, r[k], v))
    if not r['situacao'].startswith('89,6 °C · acima de 85 °C · desde '): prob.append('C3 crítico: a situação diz %r (esperado o limite de 85 °C)' % r['situacao'])
    if not r['ativo'] or r['ativo']['nivel'] != 'critico': prob.append('C3 crítico: o plantio não valeu (a API de alertas diz %r)' % r['ativo'])
    if r['url'].split('#')[0].endswith('S1-SOS-Web.dc.html') or 'SOS-' in r['url'].split('#')[0] or r['falas'] or r['diario']: prob.append('C3 crítico: abriu o SOS, falou ou gravou sozinha (%s, %d falas, diário %r)' % (r['url'], r['falas'], r['diario']))
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_c3_transicao(b):
    """C3 viva: com a tela aberta, o alarme acaba (fixar 105 → 120) e o selo vira NORMALIZADO às 12:01 SEM sair da tela nem recarregar (nada de navegação, fala ou registro); e reabre (120 → 105)."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'C3-Leme-Alerta', fixo='105', hash_='#alarme=arref_be')
    pg.evaluate("() => { window.__marca = 'viva'; window.__href0 = location.href; }")
    seq = []
    for t, esp in (('105', ('AVISO', 'ativo')), ('120', ('NORMALIZADO às 12:01', 'normalizado')), ('105', ('AVISO', 'ativo'))):
        try:
            pg.evaluate("(t) => window.CapitaoReplay.fixar(t)", t)
            pg.wait_for_timeout(600)
            r = pg.evaluate(LE_C3)
        except Exception as e:   # a página foi trocada no meio (navegação): é a falha que este teste procura
            prob.append('C3 ao fixar %s s: a tela foi trocada ou recarregada (%s)' % (t, str(e).splitlines()[0][:100]))
            break
        seq.append((r['selo'], r['estado']))
        if (r['selo'], r['estado']) != esp: prob.append('C3 ao fixar %s s: %r (esperado %r)' % (t, (r['selo'], r['estado']), esp))
        if t == '120' and not (r['situacao'] or '').startswith('normalizou às 12:01:57 · ficou 18 s fora da faixa (desde 12:01:39)'): prob.append('C3 a 120 s: a situação diz %r (esperado «normalizou às 12:01:57 · ficou 18 s…»)' % r['situacao'])
    try:
        m = pg.evaluate("() => [window.__marca, location.href === window.__href0, window.__falas || 0, localStorage.getItem('capitao.diario.v1')]")
    except Exception:
        m = ['trocada']
    if m != ['viva', True, 0, None]: prob.append('C3: a tela foi trocada, recarregada, falou ou gravou ao normalizar: %r' % m)
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_c3_registrar(b):
    """C3: registrar() grava UMA linha nova só com o toque (nunca ao abrir nem enquanto o alarme dura), com o valor, o lado e a hora reais do quadro, sim: true e a fonte; o 2º toque não duplica;
    depois do registro a tela mostra o link do diário; a ocorrência normalizada também se registra."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'C3-Leme-Alerta', fixo='105', hash_='#alarme=arref_be')
    for t in ('120', '105'):   # o alarme acaba e volta com a tela aberta: nem ao abrir nem a cada mudança de estado a tela grava sozinha
        pg.evaluate("(t) => window.CapitaoReplay.fixar(t)", t); pg.wait_for_timeout(500)
    pg.wait_for_timeout(1200)
    r0 = pg.evaluate(LE_C3)
    if r0['diario'] is not None or r0['cerebro'] != 'undefined': prob.append('C3: gravou no diário ou carregou o cérebro sem o toque (diário %r, cérebro %s)' % (r0['diario'], r0['cerebro']))
    if prob:   # gravou sozinha: o botão já não existe e o resto do teste não vale
        ctx.close()
        return prob
    pg.evaluate("() => { const bt = document.querySelector('[data-c3=registrar]'); bt.click(); bt.click(); }")   # dois toques seguidos: uma linha só
    pg.wait_for_function("() => !!document.querySelector('[data-c3=registrado]')", timeout=8000)
    pg.wait_for_timeout(300)
    r = pg.evaluate(LE_C3)
    linhas = json.loads(r['diario'] or '[]')
    if len(linhas) != 1: prob.append('C3: o registrar gravou %d linhas (esperado 1)' % len(linhas))
    else:
        e = linhas[0]
        if not re.fullmatch(r'Alerta registrado no app às \d\d:\d\d por Lucas — Temperatura do motor BE \(lado BE\): 89,6 °C \(acima de 88 °C\), AVISO desde 12:01:39 · leitura às 12:01:45 \(telemetria ao vivo\)\. Passos: Guia de bordo — Motores Cummins §5 · Temperatura alta\. Linha nova, nada se apaga\.', e['t']):
            prob.append('C3: a linha gravada não tem o valor, o lado e a hora do quadro: %r' % e['t'])
        if e.get('sim') is not True or e['src'] != 'app · alerta' or e['sys'] != 'Motores' or e['who'] != 'Lucas': prob.append('C3: a linha gravada devia ter sim: true, src «app · alerta», sys Motores e who Lucas: %r' % {k: e.get(k) for k in ('sim', 'src', 'sys', 'who')})
        if re.search(r'SEM DADOS|SEM LEITURA|DEMO|snapshot|MODELO', e['t']): prob.append('C3: rótulo na linha gravada: %r' % e['t'])
    if r['temRegistrar'] or not (r['registrado'] or '').startswith('REGISTRADO'): prob.append('C3: depois do registro a tela devia trocar o botão pelo link «REGISTRADO …»: %r' % r['registrado'])
    if r['falas']: prob.append('C3: falou ao registrar')
    if erros: prob += erros[:2]
    ctx.close()
    # a ocorrência normalizada (60 s) também se registra, com o fim dela
    ctx, pg, erros = abre_tela(b, 'C3-Leme-Alerta', fixo='60', hash_='#alarme=arref_be')
    pg.evaluate("() => document.querySelector('[data-c3=registrar]').click()")
    pg.wait_for_function("() => !!document.querySelector('[data-c3=registrado]')", timeout=8000)
    linhas = json.loads(pg.evaluate("() => localStorage.getItem('capitao.diario.v1')") or '[]')
    if len(linhas) != 1 or 'normalizado às 11:59:27 (ficou 18 s fora da faixa, desde 11:59:09)' not in linhas[0]['t']: prob.append('C3 a 60 s: a linha do alerta normalizado diz %r' % [x['t'] for x in linhas])
    ctx.close()
    return prob


def teste_c3_leve(b):
    """C3 sempre escura e leve: com o tema claro o fundo segue #050816, sem o capitao-theme.js; o cérebro só entra no toque de registrar; carrega o capitao-telemetria.js; assina o evento."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'C3-Leme-Alerta', fixo='105', tema='claro', hash_='#alarme=arref_be')
    r = pg.evaluate(LE_C3)
    if r['corpo'] != 'rgb(5, 8, 22)': prob.append('C3 com o tema claro: o fundo é %s (esperado a prancheta escura rgb(5, 8, 22))' % r['corpo'])
    if any('capitao-theme.js' in s or 'capitao-brain.js' in s for s in r['scripts']) or r['cerebro'] != 'undefined': prob.append('C3: carrega o tema ou o cérebro na abertura (não é leve): %s' % [s for s in r['scripts'] if 'theme' in s or 'brain' in s])
    if not any('capitao-telemetria.js' in s for s in r['scripts']): prob.append('C3: não carrega o capitao-telemetria.js')
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_c3_codigo():
    prob = []
    def le_(a):
        t = open(os.path.join(RAIZ, a), encoding='utf-8').read()
        for velho, novo in MUT_ARQ.get(a, []): t = t.replace(velho, novo, 1)
        return t
    h = le_('C3-Leme-Alerta.dc.html')
    mont, desm = h.find('componentDidMount'), h.find('componentWillUnmount')
    for ev in ('capitao-telemetria', 'capitao-alerta'):
        if "addEventListener('%s'" % ev not in h[mont:desm] or "removeEventListener('%s'" % ev not in h[desm:]: prob.append('C3: não assina o %s no componentDidMount e remove no componentWillUnmount' % ev)
    if 'document.hidden' not in h: prob.append('C3: não pausa com document.hidden')
    if 'if (k === this._k) return;' not in h or 'this.setState({ vivo: k })' not in h: prob.append('C3: não compara o texto antes do setState')
    if h.count('setInterval') != 1: prob.append('C3: setInterval a mais (%d; só o do whenBrain)' % h.count('setInterval'))
    if re.search(r'D\.demo|\.demo\b|DEMO|D\.snapshot|\.snapshot\b', h): prob.append('C3: lê D.demo ou D.snapshot (ou escreve DEMO) no código')
    if MARCAS_FIXAS.search(h): prob.append('C3: fabricante fixo no código: %s' % MARCAS_FIXAS.search(h).group(0))
    if re.search(r'location\s*\.\s*(href|assign|replace|reload)|window\s*\.\s*open|speechSynthesis|history\s*\.\s*(push|replace)State', h): prob.append('C3: troca de tela, abre janela ou fala sozinha')
    if h.count('addDiario') != 1 or h.find('addDiario') < h.find('registrar() {') or 'onClick="{{registrar}}"' not in h: prob.append('C3: grava no diário fora do registrar() ou sem ser pelo toque')
    if 'capitao-theme.js' in h or re.search(r'<script src="\./capitao-brain\.js"', h): prob.append('C3: carrega o tema ou o cérebro no <head> (é sempre escura e leve)')
    if 'capitao-faixa-alertas' in h: prob.append('C3: tem a faixa global de alerta')
    GEOM = re.compile(r'<(?:svg|path|circle|line|rect|ellipse|polyline|polygon|g)\b[^>]*\b(?:d|x|y|x1|x2|y1|y2|cx|cy|r|rx|ry|width|height|viewBox|points|transform)="[^"]*\{\{')
    if GEOM.search(h): prob.append('C3: {{…}} em atributo geométrico de SVG')
    return prob


# C4: os 4 checklists, item a item
LE_C4 = """() => { const B = window.CapitaoBrain, lin = (s) => (s || '').replace(/\\s+/g, ' ').trim(), g = (s) => { const e = document.querySelector('[data-c4=' + s + ']'); return e ? lin(e.innerText) : null; };
  const tipo = (location.hash.match(/tipo=([a-z]+)/) || [])[1] || 'saida', itens = {};
  document.querySelectorAll('[data-c4=item]').forEach((e) => { const a = e.querySelector('[data-c4=auto-rotulo]'), v = e.querySelector('[data-c4=auto-valor]'), l = e.querySelector('[data-c4=link]'), m = e.querySelector('[data-c4=marca]');
    itens[e.getAttribute('data-item')] = { feito: e.getAttribute('data-feito'), texto: lin(e.innerText), auto: a ? lin(a.innerText) : null, valor: v ? lin(v.innerText) : null, fonte: lin(e.querySelector('[data-c4=fonte]').innerText), link: l ? [l.getAttribute('href'), lin(l.innerText)] : null,
      pressed: m.getAttribute('aria-pressed'), aria: m.getAttribute('aria-label') }; });
  const abas = [...document.querySelectorAll('[data-c4=aba]')].map((e) => ({ tipo: e.getAttribute('data-tipo'), sel: e.getAttribute('aria-selected'), conta: lin(e.querySelector('[data-c4=aba-conta]').innerText) }));
  const T = B.checklistTipos(), cur = T.find((t) => t.id === tipo) || T[0];
  const api = {}; T.forEach((t) => { api[t.id] = B.checklistItens(t.id).map((i) => ({ id: i.id, c: i.c, t: i.t, fonte: i.fonte, faq: i.faq || null, link: i.link || null, feito: i.feito, manual: i.manual, anulado: i.anulado, porQuadro: i.porQuadro, auto: i.auto })); });
  const faq = {}; api[cur.id].forEach((i) => { if (i.faq) { const f = B.faqItem(i.faq); faq[i.faq] = f ? f.pergunta : null; } });
  return { tipo: cur.id, tipos: T, abas, itens, api, faq, titulo: g('titulo'), conta: g('conta'), pend: g('pend'), aviso: g('aviso'), resumo: g('resumo'), agora: [...document.querySelectorAll('[data-c4=agora]')].map((e) => lin(e.innerText)),
    linha: B.checklistLinha(cur.id), hash: location.hash, diario: localStorage.getItem('capitao.diario.v1'), marcas: localStorage.getItem('capitao.checklist.v1'), texto: lin(document.body.innerText), temConcluir: !!document.querySelector('[data-c4=concluir]') }; }"""
EST_ROTULO = {'ok': 'TELEMETRIA ✓', 'falta': 'ATENÇÃO', 'ler': 'CONFIRA'}


def problemas_c4_itens(r, rot, app):
    """Cada item da tela é o do cérebro (B.checklistItens): o texto, a fonte, o rótulo e a leitura da verificação pelo quadro, o estado (conferido pelo quadro, pela pessoa, desmarcado), o link do FAQ e do app."""
    prob = []
    api = r['api'][r['tipo']]
    if list(r['itens']) != [i['id'] for i in api]: prob.append('%s: os itens da tela são %s (esperado %s, na ordem do D.checklists)' % (rot, list(r['itens']), [i['id'] for i in api])); return prob
    for i in api:
        e = r['itens'][i['id']]
        est = 'quadro' if i['porQuadro'] else 'pessoa' if i['manual'] else 'anulado' if i['anulado'] else 'aberto'
        if e['feito'] != est or e['pressed'] != ('true' if i['feito'] else 'false'): prob.append('%s: o item %s está %r/%r (esperado %r)' % (rot, i['id'], e['feito'], e['pressed'], est))
        if i['t'] not in e['texto'] or e['fonte'] != 'Fonte: ' + i['fonte']: prob.append('%s: o item %s não traz o texto e a fonte do guia: %r' % (rot, i['id'], e['texto'][:80]))
        a = i['auto']
        if (e['auto'], e['valor']) != ((EST_ROTULO[a['estado']], a['valor']) if a and a['estado'] in EST_ROTULO else (None, None)): prob.append('%s: o item %s mostra %r / %r (esperado a verificação do quadro %r)' % (rot, i['id'], e['auto'], e['valor'], a))
        if i['faq']:
            # (P4H) o «passo a passo» abre o item no FAQ dos equipamentos (F6, o mesmo da plataforma da tela) pelo código; antes abria o chat com a pergunta (#q=)
            esp = ('F6-FAQ-Equipamentos.dc.html' if app else 'F6-FAQ-Equipamentos-Web.dc.html') + '#id=' + urllib.parse.quote(i['faq'], safe="!~*'()")
            if not r['faq'][i['faq']] or e['link'] != [esp, 'FAQ %s — passo a passo ›' % i['faq']]: prob.append('%s: o link do FAQ de %s é %r (esperado %r)' % (rot, i['id'], e['link'], [esp, 'FAQ %s — passo a passo ›' % i['faq']]))
        elif i['link']:
            arq = 'G3-Diario' if i['link'] == 'G3-Diario' else 'G2-Abastecimento'
            if e['link'] != [arq + ('-Mobile' if app else '-Web') + '.dc.html', 'Abrir o Diário ›' if arq == 'G3-Diario' else 'Abrir Abastecimento ›']: prob.append('%s: o link do item %s é %r (esperado %s da %s)' % (rot, i['id'], e['link'], arq, 'app' if app else 'web'))
    f = sum(1 for i in api if i['feito'])
    if r['conta'] != '%d/%d' % (f, len(api)): prob.append('%s: o andamento diz %r (esperado %d/%d)' % (rot, r['conta'], f, len(api)))
    pend = [i['c'] for i in api if not i['feito']]
    if not (r['pend'] or '').startswith('Pendentes: ' + ', '.join(pend) + '.' if pend else 'Tudo conferido'): prob.append('%s: os pendentes dizem %r (esperado %s)' % (rot, r['pend'], pend))
    ab = {a['tipo']: a for a in r['abas']}
    for t in r['tipos']:
        n = sum(1 for i in r['api'][t['id']] if i['feito'])
        if ab.get(t['id'], {}).get('conta') != '%d/%d' % (n, len(r['api'][t['id']])) or (ab.get(t['id'], {}).get('sel') == 'true') != (t['id'] == r['tipo']): prob.append('%s: a aba %s diz %r (esperado %d/%d e selecionada só a do tipo atual)' % (rot, t['id'], ab.get(t['id']), n, len(r['api'][t['id']])))
    return prob


def teste_c4(b, tela):
    """C4: a aba pelo #tipo=, os itens do cérebro com a fonte do guia, o ✓ do quadro que muda com o replay (s02: ✓ a 60 s, ✗ a 105 s), a marca da pessoa, a desmarca do ✓ do quadro, o CONCLUIR (UMA linha
    nova no diário só com o toque, mesmo com dois toques; sim: true; as marcas somem), o Recomeçar sem diário, o FAQ e os links, e sem rótulo nos 4 tipos; tudo a 60 s e a 105 s."""
    app = tela.endswith('Mobile')
    prob = []
    for fixo in ('60', '105'):
        for tipo in ('saida', 'chegada', 'abastecimento', 'fundeio'):
            ctx, pg, erros = abre_tela(b, tela, fixo=fixo, hash_='#tipo=' + tipo)
            r = pg.evaluate(LE_C4)
            rot = '%s %s a %s s' % (tela.split('-')[0], tipo, fixo)
            if r['tipo'] != tipo: prob.append('%s: a aba aberta é %s' % (rot, r['tipo']))
            prob += problemas_c4_itens(r, rot, app)
            if r['diario'] or r['marcas']: prob.append('%s: gravou no registro só de abrir (diário %r, marcas %r)' % (rot, r['diario'], r['marcas']))
            ach = achados_termos(tela, pg.evaluate(LE_TEXTOS))
            if ach: prob.append('%s: termo do §3 na tela: %s' % (rot, ach))
            if tipo == 'saida':
                s02 = r['itens'].get('s02', {})
                esp = ('quadro', 'TELEMETRIA ✓', 'nenhum alarme ativo') if fixo == '60' else ('aberto', 'ATENÇÃO', 'AVISO: Temperatura do motor BE: 89,6 °C (acima de 88 °C)')
                if (s02.get('feito'), s02.get('auto'), s02.get('valor')) != esp: prob.append('%s: o item dos alertas (s02) diz %r (esperado %r: o ✓ do quadro muda com o replay)' % (rot, (s02.get('feito'), s02.get('auto'), s02.get('valor')), esp))
                if not app:
                    if not r['agora'] or not any(x.startswith('Alarmes ') for x in r['agora']): prob.append('%s: o painel «agora a bordo» não tem os alarmes: %s' % (rot, r['agora']))
                    if any(re.search(r'nós|rumo|proa|SOG|\d+°', x) for x in r['agora']): prob.append('%s: o painel «agora a bordo» traz posição, rumo ou velocidade: %s' % (rot, r['agora']))
            if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
            ctx.close()
    # a aba que não existe cai na saída; trocar de aba muda o endereço sem recarregar
    ctx, pg, erros = abre_tela(b, tela, hash_='#tipo=xyz')
    r = pg.evaluate(LE_C4)
    if r['tipo'] != 'saida' or [a['tipo'] for a in r['abas'] if a['sel'] == 'true'] != ['saida']: prob.append('%s #tipo=xyz: devia cair na saída: %s' % (tela, [a for a in r['abas'] if a['sel'] == 'true']))
    pg.evaluate("() => { window.__marca = 'viva'; [...document.querySelectorAll('[data-c4=aba]')].find((e) => e.getAttribute('data-tipo') === 'fundeio').click(); }")
    pg.wait_for_timeout(500)
    r = pg.evaluate(LE_C4)
    if r['hash'] != '#tipo=fundeio' or r['tipo'] != 'fundeio' or pg.evaluate("() => window.__marca") != 'viva': prob.append('%s: a aba Fundeio não mudou o endereço sem recarregar: %r' % (tela, r['hash']))
    ctx.close()
    # as marcas, a desmarca do ✓ do quadro, o Recomeçar e o CONCLUIR
    ctx, pg, erros = abre_tela(b, tela, hash_='#tipo=saida')
    clica = "(id) => document.querySelector('[data-item=' + id + '] [data-c4=marca]').click()"
    f0 = sum(1 for i in pg.evaluate(LE_C4)['api']['saida'] if i['feito'])   # os conferidos pelo quadro antes de qualquer toque (o s02 conta a 60 s)
    pg.evaluate(clica, 's03'); pg.wait_for_timeout(300)
    r = pg.evaluate(LE_C4)
    m = json.loads(r['marcas'] or '{}')
    if m.get('saida', {}).get('m') != {'s03': 1} or r['itens']['s03']['feito'] != 'pessoa' or r['conta'] != '%d/14' % (f0 + 1): prob.append('%s: marcar o s03 devia gravar {s03: 1}, deixar o item «pessoa» e o andamento %d/14: %r %r %r' % (tela, f0 + 1, m, r['itens']['s03']['feito'], r['conta']))
    if r['diario']: prob.append('%s: marcar um item gravou no diário' % tela)
    pg.evaluate(clica, 's05'); pg.wait_for_timeout(300)
    r = pg.evaluate(LE_C4)
    m = json.loads(r['marcas'] or '{}')
    if m['saida']['m'].get('s05') != 'n' or r['itens']['s05']['feito'] != 'anulado' or r['conta'] != '%d/14' % f0 or 'NÃO conferido' not in (r['aviso'] or ''): prob.append('%s: tocar no ✓ do quadro (s05) devia marcar «n», deixar o item desmarcado (%d/14) e avisar: %r %r %r' % (tela, f0, m, r['itens']['s05']['feito'], r['aviso']))
    pg.evaluate(clica, 's05'); pg.wait_for_timeout(300)
    r = pg.evaluate(LE_C4)
    if 's05' in json.loads(r['marcas'])['saida']['m'] or r['itens']['s05']['feito'] != 'quadro': prob.append('%s: tocar de novo devia voltar ao ✓ automático: %r' % (tela, r['itens']['s05']['feito']))
    pg.evaluate("() => [...document.querySelectorAll('[data-c4=zera]')][0].click()"); pg.wait_for_timeout(300)
    r = pg.evaluate(LE_C4)
    if 'saida' in json.loads(r['marcas'] or '{}') or r['diario'] or r['itens']['s03']['feito'] == 'pessoa': prob.append('%s: o Recomeçar devia apagar as marcas sem gravar no diário: marcas %r, diário %r' % (tela, r['marcas'], r['diario']))
    pg.evaluate(clica, 's03'); pg.wait_for_timeout(300)
    linha = pg.evaluate(LE_C4)['linha']
    pg.evaluate("() => { const bt = document.querySelector('[data-c4=concluir]'); bt.click(); bt.click(); }")   # dois toques seguidos: uma linha só
    pg.wait_for_timeout(700)
    r = pg.evaluate(LE_C4)
    d = json.loads(r['diario'] or '[]')
    if len(d) != 1: prob.append('%s: o CONCLUIR gravou %d linhas no diário (esperado 1, mesmo com dois toques)' % (tela, len(d)))
    else:
        e = d[0]
        if e['t'] != linha['t'] or e['sys'] != linha['sys'] or e.get('sim') is not True or not e['src'].startswith('checklist de bordo') or e['who'] != 'Lucas': prob.append('%s: a linha do CONCLUIR devia ser %r (sys %s, sim: true): %r' % (tela, linha['t'], linha['sys'], {k: e.get(k) for k in ('t', 'sys', 'sim', 'src', 'who')}))
        if not re.fullmatch(r'Checklist de saída concluído · %d/14 \(%d pela telemetria\) · pendentes: .+' % (f0 + 1, f0), e['t']): prob.append('%s: o formato da linha do CONCLUIR: %r (esperado %d/14, %d pela telemetria)' % (tela, e['t'], f0 + 1, f0))
    if 'saida' in json.loads(r['marcas'] or '{}'): prob.append('%s: o CONCLUIR devia apagar as marcas do tipo: %r' % (tela, r['marcas']))
    if 'No diário: Checklist de saída concluído' not in (r['aviso'] or '') or 'VER NO DIÁRIO' not in (r['aviso'] or ''): prob.append('%s: depois do CONCLUIR a tela devia avisar e levar ao diário: %r' % (tela, r['aviso']))
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_c4_vivo(b):
    """Sem congelar o replay, a C4 anda sozinha (a fonte e a hora do quadro mudam em 1,5 s): assina o capitao-telemetria."""
    prob = []
    for tela in ('C4-Checklist-Web', 'C4-Checklist-Mobile'):
        ctx, pg, erros = abre_tela(b, tela, fixo=None)
        mudou = False
        for _ in range(3):
            a = pg.evaluate("() => document.querySelector('[data-c4=resumo]').innerText")
            pg.wait_for_timeout(1500)
            if a != pg.evaluate("() => document.querySelector('[data-c4=resumo]').innerText"): mudou = True; break
        if not mudou: prob.append('%s: a hora do quadro não mudou em 1,5 s sem congelar o replay (3 tentativas)' % tela)
        if erros: prob += erros[:2]
        ctx.close()
    return prob


def teste_c4_codigo():
    prob = []
    def le_(a):
        t = open(os.path.join(RAIZ, a), encoding='utf-8').read()
        for velho, novo in MUT_ARQ.get(a, []): t = t.replace(velho, novo, 1)
        return t
    GEOM = re.compile(r'<(?:svg|path|circle|line|rect|ellipse|polyline|polygon|g)\b[^>]*\b(?:d|x|y|x1|x2|y1|y2|cx|cy|r|rx|ry|width|height|viewBox|points|transform)="[^"]*\{\{')
    for t in ('C4-Checklist-Web', 'C4-Checklist-Mobile', 'C1-Leme-Web', 'C2-Leme-Mobile'):
        h = le_(t + '.dc.html')
        mont, desm = h.find('componentDidMount'), h.find('componentWillUnmount')
        if GEOM.search(h): prob.append('%s: {{…}} em atributo geométrico de SVG' % t)
        if re.search(r'D\.demo|\.demo\b|DEMO|D\.snapshot|\.snapshot\b', h): prob.append('%s: lê D.demo ou D.snapshot (ou escreve DEMO) no código' % t)
        if MARCAS_FIXAS.search(h): prob.append('%s: fabricante fixo no código: %s' % (t, MARCAS_FIXAS.search(h).group(0)))
        for ev in ('capitao-telemetria', 'capitao-rebase'):
            if t.startswith('C4'):   # a C4 guarda os eventos numa lista (a telemetria, o alerta e a virada do dia)
                lista = "['capitao-telemetria', 'capitao-alerta', 'capitao-rebase'].forEach((ev) => window.%sEventListener(ev, this._onTele))"
                ok_ = (lista % 'add') in h[mont:desm] and (lista % 'remove') in h[desm:]
            else:
                ok_ = ("addEventListener('%s'" % ev) in h[mont:desm] and ("removeEventListener('%s'" % ev) in h[desm:]
            if not ok_: prob.append('%s: não assina o %s no componentDidMount e remove no componentWillUnmount' % (t, ev))
        if 'document.hidden' not in h: prob.append('%s: não pausa com document.hidden' % t)
        if 'if (k === this._k) return;' not in h or 'this.setState({ vivo: k })' not in h: prob.append('%s: não compara o texto antes do setState' % t)
        if h.count('setInterval') > 1: prob.append('%s: setInterval novo (%d)' % (t, h.count('setInterval')))
        if t.startswith('C4'):
            if h.count('checklistConcluir') != 1 or h.find('checklistConcluir') < h.find('  conclui() {') or 'onClick="{{conclui}}"' not in h: prob.append('%s: grava no diário fora do conclui() ou sem ser pelo toque' % t)
            if re.search(r'localStorage\s*\.\s*setItem|addDiario|apagaDiario|removeItem', h): prob.append('%s: grava no aparelho direto (o cérebro grava)' % t)
            if 'Date.now() - (this._tq || 0) < 1500' not in h: prob.append('%s: sem o intervalo entre dois CONCLUIR' % t)
    return prob


def p4e_conferencias(b, lista):
    """[(nome, problemas)] das conferências da P4E para as telas da rodada."""
    out = []
    if any(t in lista for t in TELAS_P4E): out.append(('código da P4E (C1 a C4)', teste_c4_codigo() + (teste_c3_codigo() if 'C3-Leme-Alerta' in lista else [])))
    if 'C1-Leme-Web' in lista: out.append(('C1 · leituras de agora, contas, horas que faltam e tarefas da equipe', teste_leme_c1(b)))
    if 'C2-Leme-Mobile' in lista: out.append(('C2 · atrasadas, horímetros de agora e horas que faltam', teste_leme_c2(b)))
    if 'C3-Leme-Alerta' in lista:
        out.append(('C3 · o alerta vivo: AVISO, NORMALIZADO, sem alarme e a faixa do óleo', teste_c3_estados(b)))
        out.append(('C3 · o alarme crítico plantado (o cenário desligado)', teste_c3_critico(b)))
        out.append(('C3 · normaliza com a tela aberta, sem sair dela', teste_c3_transicao(b)))
        out.append(('C3 · registrar só com o toque, com o valor, o lado e a hora do quadro', teste_c3_registrar(b)))
        out.append(('C3 · sempre escura e leve', teste_c3_leve(b)))
    for tela in ('C4-Checklist-Web', 'C4-Checklist-Mobile'):
        if tela in lista: out.append(('%s · itens, ✓ do quadro, marcas, CONCLUIR e links' % tela, teste_c4(b, tela)))
    if any(t.startswith('C4') for t in lista): out.append(('C4 · anda sem congelar o replay', teste_c4_vivo(b)))
    if any(t in lista for t in TELAS_P4E): out.append(('simulacao false no Leme e nos checklists', teste_leme_real(b)))
    return out


# Defeitos plantados da P4E: cada um é servido no lugar do arquivo (MUT_ARQ) e a conferência que cuida dele TEM de acusar (--mutantes-p4e; um mutante vivo reprova).
MUTANTES_P4E = [
    # —— C1 ——
    ('a velocidade da C1 fixa em 0,0 (a leitura de agora não anda)', 'C1-Leme-Web.dc.html', [("{ id: 'sog', k: 'Velocidade', v: c('sog_nos'),", "{ id: 'sog', k: 'Velocidade', v: '0,0',")], 'c1'),
    ('o vento da C1 sem «a bordo agora» (trava 12)', 'C1-Leme-Web.dc.html', [("'a bordo agora · verdadeiro de '", "'verdadeiro de '")], 'c1'),
    ('as horas que faltam da C1 só da agenda gerada (não do horímetro de agora)', 'C1-Leme-Web.dc.html', [("const f = I && I.calc && I.calc.faltam ? I.calc.faltam[t.id] : undefined; return num(f) ? f : num(h.faltam) ? h.faltam : null;", "return num(h.faltam) ? h.faltam : null;")], 'c1'),
    ('a C1 conta a tarefa executada como atrasada', 'C1-Leme-Web.dc.html', [("grupo(t.dn) === g && !ex[t.id] && !t.feita);", "grupo(t.dn) === g && !t.feita);")], 'c1'),
    ('a C1 sem as tarefas da equipe do aparelho', 'C1-Leme-Web.dc.html', [(".concat(equipe.map((t) => ({ id: t.id, t: t.n,", ".concat([].map((t) => ({ id: t.id, t: t.n,")], 'c1'),
    ('o resumo da C1 de volta com «snapshot DEMO»', 'C1-Leme-Web.dc.html', [("const resumo = fonteTxt + ' · '", "const resumo = 'snapshot DEMO · ' + fonteTxt + ' · '")], 'c1'),
    ('a fonte da leitura da C1 de volta com «telemetria ao vivo desligada»', 'C1-Leme-Web.dc.html', [("resumo: resumo, leituraSub: fonteTxt,", "resumo: resumo, leituraSub: 'Coletor NMEA · snapshot · telemetria ao vivo desligada',")], 'c1'),
    ('a C1 sem assinar o capitao-telemetria', 'C1-Leme-Web.dc.html', [("    window.addEventListener('capitao-telemetria', this._onTele);\n", "")], 'c1_vivo'),
    # —— C2 ——
    ('os horímetros da C2 fixos no snapshot (BB 412,6 h)', 'C2-Leme-Mobile.dc.html', [("horimetros: 'BB ' + c('motor_bb_horimetro_h')", "horimetros: 'BB 412,6'")], 'c2'),
    ('as horas que faltam da C2 só da agenda gerada', 'C2-Leme-Mobile.dc.html', [("const f = I && I.calc && I.calc.faltam ? I.calc.faltam[t.id] : undefined; return num(f) ? f : num(h.faltam) ? h.faltam : null;", "return num(h.faltam) ? h.faltam : null;")], 'c2'),
    ('a C2 conta a tarefa executada como atrasada', 'C2-Leme-Mobile.dc.html', [("t.dn < 0 && !ex[t.id] && !t.feita)", "t.dn < 0 && !t.feita)")], 'c2'),
    ('a C2 sem assinar o capitao-telemetria', 'C2-Leme-Mobile.dc.html', [("    window.addEventListener('capitao-telemetria', this._onTele);\n", "")], 'c2_codigo'),
    # —— C3 ——
    ('a leitura agora da C3 sem a hora do quadro', 'C3-Leme-Alerta.dc.html', [("(horaI ? ' · ' + horaI : '')", "''")], 'c3'),
    ('a leitura agora da C3 sem o lado (BB/BE)', 'C3-Leme-Alerta.dc.html', [("(lado ? String(lado).toUpperCase() + ' ' : '') + valor", "valor")], 'c3'),
    ('a leitura da C3 não pisca com o alarme ativo', 'C3-Leme-Alerta.dc.html', [("piscaLeitura: ativo ? '1' : '0'", "piscaLeitura: '0'")], 'c3'),
    ('o NORMALIZADO da C3 diz a hora do começo da janela (e não a do fim) na situação', 'C3-Leme-Alerta.dc.html', [("situacao = 'normalizou às ' + hora(j.ate, true)", "situacao = 'normalizou às ' + hora(j.desde, true)")], 'c3'),
    ('o NORMALIZADO da C3 sem o fim (a janela esquecida: sempre «dentro da faixa»)', 'C3-Leme-Alerta.dc.html', [("(j && num(j.ate) ? 'normalizado' : 'normal')", "'normal'")], 'c3'),
    ('a C3 fecha a tela sozinha quando o alarme normaliza', 'C3-Leme-Alerta.dc.html', [("    this.setState({ vivo: k });\n  }\n  ico(", "    this.setState({ vivo: k });\n    if (d.estado === 'normalizado') location.replace('H2-Home-Mobile.dc.html');\n  }\n  ico(")], 'c3_transicao'),
    ('o fabricante dos motores fixo na C3 (Volvo Penta)', 'C3-Leme-Alerta.dc.html', [("(num(eq.qtd) && eq.qtd > 1 ? eq.qtd + ' ×' : ''), eq.fabricante,", "(num(eq.qtd) && eq.qtd > 1 ? eq.qtd + ' ×' : ''), 'Volvo Penta',")], 'c3'),
    ('a C3 registra sozinha quando o estado muda para ativo (sem o toque)', 'C3-Leme-Alerta.dc.html', [("    this._k = k; this._din = d; this._fresco = true;\n    this.setState({ vivo: k });", "    this._k = k; this._din = d; this._fresco = true;\n    if (d.estado === 'ativo' && !this._auto) { this._auto = 1; setTimeout(() => this.registrar(), 0); }\n    this.setState({ vivo: k });")], 'c3_registrar'),
    ('o registrar da C3 grava o valor fixo (1,6 bar) e não o do quadro', 'C3-Leme-Alerta.dc.html', [("': ' + x.regTxt + ' · leitura às '", "': 1,6 bar · leitura às '")], 'c3_registrar'),
    ('a faixa normal da C3 fixa (até 6 bar)', 'C3-Leme-Alerta.dc.html', [("if (Rg) { faixa = faixaDe(Rg) + regTxt;", "if (Rg) { faixa = 'até 6 bar';")], 'c3'),
    ('a tendência da C3 olha 30 s atrás no lugar de 10 s', 'C3-Leme-Alerta.dc.html', [("const qq = R.em(ms - k * 1000);", "const qq = R.em(ms - k * 3000);")], 'c3'),
    ('a C3 de volta com o texto fixo «MODELO DE ALERTA»', 'C3-Leme-Alerta.dc.html', [('<span data-c3="selo" style="font-size: 12.5px; font-weight: 800; letter-spacing: 0.10em; color: {{cartaoAcc}};">{{selo}}</span>', '<span data-c3="selo" style="font-size: 12.5px; font-weight: 800; letter-spacing: 0.10em; color: {{cartaoAcc}};">MODELO DE ALERTA · {{selo}}</span>')], 'c3'),
    ('a C3 carrega o cérebro na abertura (deixa de ser leve)', 'C3-Leme-Alerta.dc.html', [('<script src="./capitao-telemetria.js"></script>\n<style>', '<script src="./capitao-telemetria.js"></script>\n<script src="./capitao-brain.js"></script>\n<style>')], 'c3_leve'),
    ('o alerta crítico da C3 sem o fundo vermelho', 'C3-Leme-Alerta.dc.html', [("d.nivel === 'critico' ? { bg: '#d32f27',", "d.nivel === 'critico' ? { bg: 'rgba(240,166,58,0.13)',")], 'c3_critico'),
    ('a C3 sem assinar o capitao-alerta', 'C3-Leme-Alerta.dc.html', [("    window.addEventListener('capitao-alerta', this._onTele);\n", "")], 'c3_codigo'),
    # —— C4 ——
    ('a C4 sem o ✓ do quadro (os itens sem a verificação)', 'C4-Checklist-Web.dc.html', [("aEstado: i.auto ? i.auto.estado : '', aValor: i.auto ? String(i.auto.valor) : '',", "aEstado: '', aValor: '',")], 'c4_web'),
    ('o CONCLUIR da C4 grava duas linhas', 'C4-Checklist-Web.dc.html', [("try { r = B.checklistConcluir(this._tipo); } catch (e) { r = null; }", "try { r = B.checklistConcluir(this._tipo); B.checklistConcluir(this._tipo); } catch (e) { r = null; }")], 'c4_web'),
    ('a C4 sem o intervalo entre dois CONCLUIR', 'C4-Checklist-Web.dc.html', [("Date.now() - (this._tq || 0) < 1500", "false")], 'c4_web'),
    ('a C4 conclui o checklist de saída ao abrir (sem o toque)', 'C4-Checklist-Web.dc.html', [("this.whenBrain((B) => { try { if (B.carregaFaq)", "this.whenBrain((B) => { try { B.checklistConcluir('saida'); } catch (e) {} try { if (B.carregaFaq)")], 'c4_web'),
    ('o toque no ✓ do quadro da C4 não desmarca (marca como conferido)', 'C4-Checklist-Web.dc.html', [("B.checklistMarca(tipo, i.id, 'n'); this.atualiza(); return", "B.checklistMarca(tipo, i.id, 1); this.atualiza(); return")], 'c4_web'),
    ('a C4 do app com o link do diário da web', 'C4-Checklist-Mobile.dc.html', [("'G3-Diario': ['G3-Diario-Mobile.dc.html',", "'G3-Diario': ['G3-Diario-Web.dc.html',")], 'c4_app'),
    ('a C4 do app sem assinar o capitao-telemetria', 'C4-Checklist-Mobile.dc.html', [("['capitao-telemetria', 'capitao-alerta', 'capitao-rebase'].forEach((ev) => window.addEventListener(ev, this._onTele));", "['capitao-alerta', 'capitao-rebase'].forEach((ev) => window.addEventListener(ev, this._onTele));")], 'c4_vivo'),
    ('o Recomeçar da C4 grava no diário', 'C4-Checklist-Mobile.dc.html', [("zera() { const B = window.CapitaoBrain; if (!B) return; B.checklistZera(this._tipo);", "zera() { const B = window.CapitaoBrain; if (!B) return; B.checklistConcluir(this._tipo); B.checklistZera(this._tipo);")], 'c4_app'),
]
QUAL_P4E = {'c1': lambda b: teste_leme_c1(b), 'c1_vivo': lambda b: teste_leme_vivo(b), 'c2': lambda b: teste_leme_c2(b), 'c2_codigo': lambda b: teste_c4_codigo(),
            'c3': lambda b: teste_c3_estados(b) + teste_c3_codigo(), 'c3_critico': lambda b: teste_c3_critico(b), 'c3_transicao': lambda b: teste_c3_transicao(b), 'c3_registrar': lambda b: teste_c3_registrar(b),
            'c3_leve': lambda b: teste_c3_leve(b) + teste_c3_codigo(), 'c3_codigo': lambda b: teste_c3_codigo(),
            'c4_web': lambda b: teste_c4(b, 'C4-Checklist-Web'), 'c4_app': lambda b: teste_c4(b, 'C4-Checklist-Mobile'), 'c4_vivo': lambda b: teste_c4_vivo(b) + teste_c4_codigo()}


def teste_leme_vivo(b):
    """Sem congelar o replay, a C1 anda sozinha (a leitura de agora muda em 1,5 s): assina o capitao-telemetria."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'C1-Leme-Web', fixo=None)
    mudou = False
    for _ in range(3):
        a = pg.evaluate("() => document.querySelector('[data-c1=leitura-sub]').innerText")
        pg.wait_for_timeout(1500)
        if a != pg.evaluate("() => document.querySelector('[data-c1=leitura-sub]').innerText"): mudou = True; break
    if not mudou: prob.append('C1: a leitura de agora não mudou em 1,5 s sem congelar o replay (3 tentativas): a tela não assina o capitao-telemetria')
    if erros: prob += erros[:2]
    ctx.close()
    return prob + teste_c4_codigo()


def mutantes_p4e(b):
    global MUT_ARQ
    vivos = []
    filtro = os.environ.get('MUT_FILTRO', '')   # só os mutantes cujo nome tem este texto (para refazer um)
    for nome, arq, trocas, qual in MUTANTES_P4E:
        if filtro and filtro not in nome: continue
        src = open(os.path.join(RAIZ, arq), encoding='utf-8').read()
        faltam = [x for x, _ in trocas if src.count(x) != 1]
        if faltam:
            print('ERRO no mutante «%s»: o trecho não está uma vez em %s: %s' % (nome, arq, faltam)); vivos.append(nome); continue
        MUT_ARQ = {arq: trocas}
        sai = sys.stdout
        prob = []
        try:
            sys.stdout = open(os.devnull, 'w')
            prob = QUAL_P4E[qual](b)
        except Exception as e:   # um erro do próprio teste não conta como acusação: o mutante fica vivo
            sys.stdout = sai
            print('ERRO do teste no mutante «%s»: %s' % (nome, str(e).splitlines()[-1][:160]))
            prob = []
        finally:
            sys.stdout = sai
            MUT_ARQ = {}
        print('MUTANTE %s: %s (%d problema(s))%s' % ('ACUSADO' if prob else 'VIVO', nome, len(prob), ' · ' + prob[0][:150] if prob else ''))
        if not prob: vivos.append(nome)
    print('%d mutantes · %d vivos' % (len(MUTANTES_P4E), len(vivos)))
    return vivos


# ═══ Fase 4, P4F: o Modo navegação (E1 Gatilhos e E2 Sintoma) ═══
# `--so-p4f` roda só as conferências dela; `--mutantes-p4f` planta os defeitos (MUTANTES_P4F), cada um servido no lugar do arquivo (MUT_ARQ) e acusado pela conferência que cuida dele.
# O gancho da troca: o `capitao.replay.sobre` planta o SOG no quadro do instante fixado, mas o instante guarda 1 s (a chave inclui o `capitao.clima.v1`): para o valor novo entrar com a tela aberta, o teste muda também
# o clima (uma leitura de OUTRO dia, que não trava nada) — só assim o quadro de 60 s passa a valer outro SOG sem recarregar.
TELAS_P4F = ('E1-Navegando-Gatilhos', 'E2-Navegando-Sintoma')
IDS_NAV = ['mob', 'porao', 'pane', 'alarme', 'registrar', 'canal16']   # na ordem do CSS (order 1 a 6)
IDS_PARADO = ['ancora', 'checklist', 'abastecer', 'diario']
HREF_NAV = {'mob': 'S2-SOS-Mobile.dc.html', 'pane': 'E2-Navegando-Sintoma.dc.html#sis=motores', 'alarme': 'E2-Navegando-Sintoma.dc.html'}
HREF_PARADO = {'checklist': 'C4-Checklist-Mobile.dc.html#tipo=saida', 'abastecer': 'G2-Abastecimento-Mobile.dc.html', 'diario': 'G3-Diario-Mobile.dc.html'}
PERGUNTA_E1 = {'porao': 'Tem água no porão', 'canal16': 'Canal 16', 'ancora': 'A âncora está garrando?'}   # os que abrem o chat do app (#q=)
CHAVE_E1 = {'porao': 'sos', 'canal16': 'canal16', 'ancora': 'ancora'}   # o relato no porão é SOS (CLAUDE.md 10): nunca a leitura do porão; o canal 16 abre a janela; a âncora é a resposta pronta dela
ORACULO_E1 = {'60': {'hora': '12:01:00', 'sog': '18,1', 'litros': '1.333', 'porao': 'BB 1,1 · BE 0,9 cm'}, '105': {'hora': '12:01:45', 'sog': '18,0', 'litros': '1.332', 'porao': 'BB 1,2 · BE 0,9 cm'}}   # CONTRATO §1.22
SOBRE_JS = "([v, n]) => { if (v === null) localStorage.removeItem('capitao.replay.sobre'); else localStorage.setItem('capitao.replay.sobre', JSON.stringify(v)); localStorage.setItem('capitao.clima.v1', JSON.stringify({ dia: '2000-01-01', n: n })); }"
JANELA_VALE = "try { sessionStorage.setItem('capitao.emergenciaAte', String(Date.now() + 600000)); } catch (e) {}"   # a janela de conversa em emergência já marcada (10 min) quando a tela abre

LE_E1 = """() => { """ + JS_BASE + """
  const AL = window.CapitaoAlertas, B = window.CapitaoBrain, g = (s) => { const e = document.querySelector('[data-e1=' + s + ']'); return e ? lin(e.innerText) : null; };
  const gat = [...document.querySelectorAll('[data-e1=gatilho]')].map((e) => { const cs = getComputedStyle(e); return { id: e.dataset.id, tag: e.tagName, href: e.getAttribute('href'), txt: lin(e.innerText), aria: e.getAttribute('aria-label'),
    ordem: parseInt(cs.order, 10), col: cs.gridColumnStart + '/' + cs.gridColumnEnd, bg: cs.backgroundColor, h: e.getBoundingClientRect().height }; });
  const vg = document.querySelector('[data-e1=vigia]'), ch = document.querySelector('[data-e1=chip]'), es = document.querySelector('[data-e1=estado]');
  const leit = [...document.querySelectorAll('[data-e1=leitura]')].map((e) => ({ txt: lin(e.innerText), title: e.title, corte: [...e.querySelectorAll('span')].filter((s) => s.scrollWidth - s.clientWidth > 1).map((s) => lin(s.innerText)) }));
  const al = AL ? AL.ativos().map((a) => ({ id: a.id, nivel: a.nivel, texto: a.texto, hora: a.hora, detalhe: a.detalhe, lado: a.lado, sistema: a.sistema })) : [];
  const pergunta = {}; gat.forEach((x) => { const m = /#q=(.*)$/.exec(x.href || ''); if (m) { let q2 = m[1]; try { q2 = decodeURIComponent(q2); } catch (e) {} pergunta[x.id] = q2; } });
  const resp = {}; if (B) Object.keys(pergunta).forEach((k) => { const a = B.answer(pergunta[k], { platform: 'app', commit: false }); resp[k] = { key: a.key, texto: a.text }; });
  return { hora: I.hora, hhmm: I.hhmm, fonte: I.fonte, fonteTxt: I.fonteTxt, T, local: q.local, estado: q.estado, coord: F.coord(q.lat, q.lon), pctTxt: I.calc && typeof I.calc.diesel_pct === 'number' ? F.nb(I.calc.diesel_pct, 1) + ' %' : null,
    dBB: Math.round(q.diesel_bb_pct), dBE: Math.round(q.diesel_be_pct), gat, modo: vg ? vg.dataset.modo : null, vigia: g('vigia'), chip: ch ? lin(ch.innerText) : null, estadoV: es ? lin(es.innerText) : null, estadoCor: es ? getComputedStyle(es).color : null,
    sub: g('sub'), subTitle: (document.querySelector('[data-e1=sub]') || {}).title, leit, titulo: g('gatilhos-titulo'), troca: g('troca'), texto: lin(document.body.innerText), al, pergunta, resp,
    url: location.href, falas: window.__falas || 0, diario: localStorage.getItem('capitao.diario.v1'), lateral: document.documentElement.scrollWidth - document.documentElement.clientWidth }; }"""
LE_E1_MIN = """() => { const g = (s) => { const e = document.querySelector('[data-e1=' + s + ']'); return e ? e.innerText.replace(/\\s+/g, ' ').trim() : null; };
  return { modo: document.querySelector('[data-e1=vigia]').dataset.modo, ids: [...document.querySelectorAll('[data-e1=gatilho]')].map((e) => e.dataset.id).join(','), titulo: g('gatilhos-titulo'), sub: g('sub') }; }"""


def ids_e1(r):
    return [x['id'] for x in sorted(r['gat'], key=lambda x: x['ordem'])]


def problemas_e1_conjunto(r, conj, rot, titulo='GATILHOS · NAVEGANDO'):
    """O conjunto de gatilhos (ids na ordem do CSS, links, perguntas ao chat e a chave que o cérebro responde a cada uma) e o título."""
    prob = []
    por = {x['id']: x for x in r['gat']}
    esp = (['alerta'] if r['al'] else []) + (IDS_PARADO if conj == 'parado' else IDS_NAV)
    if ids_e1(r) != esp: prob.append('%s: os gatilhos são %s (esperado %s)' % (rot, ids_e1(r), esp))
    if r['titulo'] != titulo: prob.append('%s: o título dos gatilhos diz %r (esperado %r)' % (rot, r['titulo'], titulo))
    if r['modo'] != conj: prob.append('%s: o vigia diz modo %r (esperado %r)' % (rot, r['modo'], conj))
    for i, h in (HREF_PARADO if conj == 'parado' else HREF_NAV).items():
        if i in por and por[i]['href'] != h: prob.append('%s: o gatilho %s leva a %r (esperado %r)' % (rot, i, por[i]['href'], h))
    for i in (['ancora'] if conj == 'parado' else ['porao', 'canal16']):
        p = r['pergunta'].get(i)
        if i in por and (p != PERGUNTA_E1[i] or not (por[i]['href'] or '').startswith('H2-Home-Mobile.dc.html#q=')): prob.append('%s: o gatilho %s pergunta %r a %r (esperado %r no chat do app)' % (rot, i, p, por[i]['href'], PERGUNTA_E1[i]))
        k = (r['resp'].get(i) or {}).get('key')
        if i in por and k != CHAVE_E1[i]: prob.append('%s: a pergunta do gatilho %s cai na chave %s do cérebro (esperado %s)' % (rot, i, k, CHAVE_E1[i]))
    if conj == 'nav':
        reg = por.get('registrar')
        if not reg or reg['tag'] != 'BUTTON': prob.append('%s: o REGISTRAR POSIÇÃO não é um botão' % rot)
        for i, tg in (('mob', 'A'), ('porao', 'A'), ('pane', 'A'), ('alarme', 'A'), ('canal16', 'A')):
            if i in por and por[i]['tag'] != tg: prob.append('%s: %s não é um link' % (rot, i))
        if 'porao' in por and 'nível' in (r['resp'].get('porao') or {}).get('texto', ''): prob.append('%s: a resposta ao relato no porão traz o nível do porão (relato de falha sem leitura)' % rot)
    elif 'registrar' in por: prob.append('%s: o REGISTRAR POSIÇÃO continua com o barco parado' % rot)
    return prob


def problemas_e1_leituras(r, fixo, rot):
    """O vigia ao vivo: o chip «AO VIVO hh:mm:ss», o estado, as 5 leituras do quadro (nada do snapshot de 26/09), a posição e a fonte, sem corte."""
    prob = []
    o = ORACULO_E1[fixo]
    if r['hora'] != o['hora'] or r['T']['sog_nos'] != o['sog'] or r['T']['diesel_litros'] != o['litros']: prob.append('%s: o oráculo não vale (instante %s, SOG %s, diesel %s)' % (rot, r['hora'], r['T']['sog_nos'], r['T']['diesel_litros']))
    if r['chip'] != 'AO VIVO ' + r['hora']: prob.append('%s: o chip diz %r (esperado «AO VIVO %s»)' % (rot, r['chip'], r['hora']))
    esp = 'Vigia ligada · ' + ('nenhum alarme ativo' if fixo == '60' else 'AVISO ativo')
    if r['estadoV'] != esp: prob.append('%s: o estado do vigia diz %r (esperado %r)' % (rot, r['estadoV'], esp))
    if r['fonte'] != 'replay': prob.append('%s: a fonte do instante é %s' % (rot, r['fonte']))
    T = r['T']
    esp = ['SOG %s nós' % T['sog_nos'], 'PROA %s° %s' % (T['proa_graus'], r['hhmm']), 'VENTO %s nós · %s°' % (T['vento_verdadeiro_nos'], T['vento_verdadeiro_angulo']), 'PROF. %s m' % T['profundidade_m'],
           'DIESEL %d/%d %% %s L' % (r['dBB'], r['dBE'], T['diesel_litros'])]
    if [x['txt'] for x in r['leit']] != esp: prob.append('%s: as leituras do vigia dizem %s (esperado %s)' % (rot, [x['txt'] for x in r['leit']], esp))
    if any(x['corte'] for x in r['leit']): prob.append('%s: leitura cortada no cartão: %s' % (rot, [x['corte'] for x in r['leit'] if x['corte']]))
    if 'Vento verdadeiro a bordo agora' not in r['leit'][2]['title']: prob.append('%s: o vento do vigia sem «a bordo agora» no title (trava 12): %r' % (rot, r['leit'][2]['title']))
    if 'BB %s %% · BE %s %%' % (T['diesel_bb_pct'], T['diesel_be_pct']) not in r['leit'][4]['title']: prob.append('%s: o title do diesel não traz os dois lados do quadro: %r' % (rot, r['leit'][4]['title']))
    if r['coord'] not in r['vigia'] or ('Fonte: ' + r['fonteTxt']) not in r['vigia']: prob.append('%s: o vigia sem a posição do quadro (%s) ou sem «Fonte: %s»' % (rot, r['coord'], r['fonteTxt']))
    if r['fonteTxt'] != 'telemetria ao vivo · ' + r['hora']: prob.append('%s: a fonte do quadro diz %r' % (rot, r['fonteTxt']))
    if not r['sub'].startswith('NAVEGANDO · ' + r['local']): prob.append('%s: a linha do vigia diz %r (esperado «NAVEGANDO · %s»)' % (rot, r['sub'], r['local']))
    if o['porao'] not in (next((x for x in r['gat'] if x['id'] == 'porao'), {}).get('txt') or ''): prob.append('%s: o gatilho do porão sem a leitura %r: %r' % (rot, o['porao'], next((x['txt'] for x in r['gat'] if x['id'] == 'porao'), None)))
    esp = 'Agora: NAVEGANDO · SOG %s nós.' % T['sog_nos']
    if not (r['troca'] or '').startswith('o conjunto de botões muda sozinho com o SOG: NAVEGANDO com 1 nó ou mais por 5 s, FUNDEADO ou ATRACADO com menos de 0,5 nó por 5 s.') or esp not in r['troca']: prob.append('%s: a nota da troca automática diz %r' % (rot, r['troca']))
    if re.search(r'ESPECIFICADO|não está ativa|ainda não|demonstra|snapshot|SEM LEITURA|SEM DADOS|coletor NMEA|DEMO\b|26/09|09:31|54/52', r['texto']): prob.append('%s: rótulo ou leitura do snapshot na tela: %s' % (rot, re.search(r'ESPECIFICADO|não está ativa|ainda não|demonstra|snapshot|SEM LEITURA|SEM DADOS|coletor NMEA|DEMO\b|26/09|09:31|54/52', r['texto']).group(0)))
    if r['lateral'] > 1: prob.append('%s: rolagem lateral de %d px' % (rot, r['lateral']))
    return prob


def teste_e1_nav(b):
    """E1 NAVEGANDO a 60 s e a 105 s, em 3 tamanhos e 2 temas: o conjunto, os links, o vigia ao vivo (chip, estado, leituras, posição, fonte), a nota da troca e nenhum rótulo nem dado do snapshot."""
    prob = []
    for fixo in ('60', '105'):
        for tema, w, h in (('escuro', 390, 844), ('claro', 360, 640), ('escuro', 844, 390)):
            ctx, pg, erros = abre_tela(b, 'E1-Navegando-Gatilhos', w, h, fixo=fixo, tema=tema)
            r = pg.evaluate(LE_E1)
            rot = 'E1 a %s s (%s, %d×%d)' % (fixo, tema, w, h)
            prob += problemas_e1_conjunto(r, 'nav', rot)
            prob += problemas_e1_leituras(r, fixo, rot)
            ach = achados_termos('E1-Navegando-Gatilhos', pg.evaluate(LE_TEXTOS))
            if ach: prob.append('%s: termo do §3 na tela: %s' % (rot, ach))
            if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
            ctx.close()
    # os destinos existem (os arquivos que os links abrem)
    for arq in sorted(set(list(HREF_NAV.values()) + list(HREF_PARADO.values()) + ['H2-Home-Mobile.dc.html', 'C3-Leme-Alerta.dc.html'])):
        try:
            if urllib.request.urlopen(BASE + arq.split('#')[0], timeout=10).status != 200: prob.append('E1: o destino %s não responde 200' % arq)
        except Exception as e:
            prob.append('E1: o destino %s não abre: %s' % (arq, str(e)[:80]))
    return prob


def teste_e1_alerta(b):
    """Com alarme, o 1º cartão leva ao detalhe (C3-Leme-Alerta.dc.html#alarme=<id>): primeiro no DOM e no CSS, 2 colunas, amarelo no AVISO e vermelho no crítico (o cenário alarme-critico, desligado, plantado); sem alarme, nenhum;
    o conjunto parado leva o mesmo cartão; o toque abre a C3. Nunca abre o SOS, fala ou grava sozinho."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'E1-Navegando-Gatilhos', fixo='60')
    r = pg.evaluate(LE_E1)
    if any(x['id'] == 'alerta' for x in r['gat']) or r['al']: prob.append('E1 a 60 s: tem o cartão de alerta sem alarme (%s)' % [x['id'] for x in r['gat']])
    ctx.close()
    ctx, pg, erros = abre_tela(b, 'E1-Navegando-Gatilhos', fixo='105')
    r = pg.evaluate(LE_E1)
    a = r['al'][0] if r['al'] else None
    primeiro = r['gat'][0] if r['gat'] else {}
    if not a or a['id'] != 'arref_be': prob.append('E1 a 105 s: o alarme do instante não é o arref_be (%r): o teste não vale' % a)
    else:
        esp_h = 'C3-Leme-Alerta.dc.html#alarme=arref_be'
        if primeiro.get('id') != 'alerta' or primeiro.get('href') != esp_h or a['detalhe'] != esp_h: prob.append('E1 a 105 s: o 1º cartão é %r e leva a %r (esperado «alerta» → %s)' % (primeiro.get('id'), primeiro.get('href'), esp_h))
        if ids_e1(r)[0] != 'alerta' or primeiro.get('ordem') != 0 or primeiro.get('col') != '1/-1': prob.append('E1 a 105 s: o cartão de alerta não é o 1º no CSS (order %r) nem ocupa as 2 colunas (%r)' % (primeiro.get('ordem'), primeiro.get('col')))
        if not primeiro.get('txt', '').startswith('AVISO · MOTORES BE Temperatura do motor BE: 89,6 °C (acima de 88 °C) · desde 12:01:39'): prob.append('E1 a 105 s: o texto do cartão de alerta diz %r' % primeiro.get('txt'))
        if primeiro.get('bg') != 'rgba(240, 166, 58, 0.12)': prob.append('E1 a 105 s: o cartão do AVISO tem fundo %r (esperado o amarelo do AVISO)' % primeiro.get('bg'))
        if r['estadoCor'] != 'rgb(240, 166, 58)': prob.append('E1 a 105 s: o estado do vigia não é amarelo com o AVISO (%r)' % r['estadoCor'])
        try:
            pg.click('[data-e1=gatilho][data-id=alerta]', timeout=5000)
            pg.wait_for_url('**/C3-Leme-Alerta.dc.html#alarme=arref_be', timeout=8000)
        except Exception as e:
            prob.append('E1: o toque no cartão de alerta não abriu a C3 do alarme (%s): %s' % (pg.url, str(e).splitlines()[0][:100]))
    if r['url'].split('#')[0].endswith('SOS-Mobile.dc.html') or r['falas'] or r['diario']: prob.append('E1 a 105 s: abriu o SOS, falou ou gravou sozinha (%s, %d falas, diário %r)' % (r['url'], r['falas'], r['diario']))
    if erros: prob += erros[:2]
    ctx.close()
    # o crítico plantado: vermelho e brilho; o estado do vigia diz ALERTA CRÍTICO
    ctx, pg, erros = abre_tela(b, 'E1-Navegando-Gatilhos', fixo='105', depois=CRITICO_PLANTADO)
    r = pg.evaluate(LE_E1)
    primeiro = r['gat'][0] if r['gat'] else {}
    if primeiro.get('id') != 'alerta' or primeiro.get('bg') != 'rgb(211, 47, 39)' or not primeiro.get('txt', '').startswith('ALERTA CRÍTICO · MOTORES BE'): prob.append('E1 crítico: o 1º cartão é %r (fundo %r, texto %r): esperado o vermelho de ALERTA CRÍTICO · MOTORES BE' % (primeiro.get('id'), primeiro.get('bg'), primeiro.get('txt')))
    if r['estadoV'] != 'Vigia ligada · ALERTA CRÍTICO ativo' or r['estadoCor'] != 'rgb(255, 59, 48)': prob.append('E1 crítico: o estado do vigia diz %r em %r' % (r['estadoV'], r['estadoCor']))
    if not r['al'] or r['al'][0]['nivel'] != 'critico': prob.append('E1 crítico: o plantio não valeu (a API de alertas diz %r)' % r['al'])
    if r['url'].split('#')[0].endswith('SOS-Mobile.dc.html') or r['falas'] or r['diario']: prob.append('E1 crítico: abriu o SOS, falou ou gravou sozinha')
    ctx.close()
    # o barco parado com alarme: o cartão de alerta vem antes dos 4 gatilhos do conjunto parado
    ctx, pg, erros = abre_tela(b, 'E1-Navegando-Gatilhos', fixo='105', ls={'capitao.replay.sobre': json.dumps({'sog_nos': 0, 'estado': 'Fundeado'})})
    r = pg.evaluate(LE_E1)
    prob += problemas_e1_conjunto(r, 'parado', 'E1 parado com alarme', 'GATILHOS · FUNDEADO')
    if ids_e1(r)[:1] != ['alerta'] or not r['al']: prob.append('E1 parado a 105 s: o cartão de alerta não é o 1º (%s; alarmes %s)' % (ids_e1(r), r['al']))
    ctx.close()
    return prob


def teste_e1_troca(b):
    """A troca automática com a tela aberta: SOG 0 → no 3º segundo ainda NAVEGANDO (nada de piscar) e no 7º FUNDEADO (ÂNCORA/GARRA, CHECKLIST DE SAÍDA, ABASTECER, DIÁRIO, sem o REGISTRAR); SOG 1,5 → só no 7º volta a
    NAVEGANDO. Os links vêm do estado: âncora ao chat, checklist de saída na C4, abastecer na G2, diário na G3."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'E1-Navegando-Gatilhos', fixo='60')
    r0 = pg.evaluate(LE_E1)
    prob += problemas_e1_conjunto(r0, 'nav', 'E1 ao abrir')
    pg.evaluate(SOBRE_JS, [{'sog_nos': 0, 'estado': 'Fundeado', 'ancora_estado': 'lançada'}, 1])
    pg.wait_for_timeout(3000)
    m = pg.evaluate(LE_E1_MIN)
    if m['modo'] != 'nav' or m['ids'] != ','.join(x for x in ['mob', 'porao', 'pane', 'alarme', 'canal16', 'registrar']): prob.append('E1: o conjunto trocou 3 s depois de o SOG cair a 0 (a troca é com 5 s seguidos): %s' % m)
    pg.wait_for_timeout(4500)
    r = pg.evaluate(LE_E1)
    prob += problemas_e1_conjunto(r, 'parado', 'E1 7 s depois do SOG 0', 'GATILHOS · FUNDEADO')
    por = {x['id']: x for x in r['gat']}
    if por.get('ancora') and 'Âncora lançada · alarme de âncora e corrente' not in por['ancora']['txt']: prob.append('E1 parado: o gatilho da âncora diz %r (o quadro diz lançada)' % por['ancora']['txt'])
    esp = 'Diesel ≈ %s L · %s' % (r['T']['diesel_litros'], r['pctTxt'])
    if por.get('abastecer') and esp not in por['abastecer']['txt']: prob.append('E1 parado: o gatilho ABASTECER diz %r (esperado «%s», o diesel do quadro)' % (por['abastecer']['txt'], esp))
    if not r['sub'].startswith('FUNDEADO · '): prob.append('E1 parado: a linha do vigia diz %r (esperado «FUNDEADO · …»)' % r['sub'])
    if not (r['troca'] or '').endswith('Agora: FUNDEADO · SOG 0,0 nós.'): prob.append('E1 parado: a nota da troca diz %r' % r['troca'])
    pg.evaluate(SOBRE_JS, [{'sog_nos': 1.5, 'estado': 'Navegando'}, 2])
    pg.wait_for_timeout(3000)
    m = pg.evaluate(LE_E1_MIN)
    if m['modo'] != 'parado': prob.append('E1: o conjunto voltou a NAVEGANDO 3 s depois de o SOG subir a 1,5 (a troca é com 5 s seguidos): %s' % m)
    pg.wait_for_timeout(4500)
    r = pg.evaluate(LE_E1)
    prob += problemas_e1_conjunto(r, 'nav', 'E1 7 s depois do SOG 1,5')
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_e1_histerese(b):
    """A histerese (entra com 1 nó ou mais, sai com menos de 0,5 nó): SOG 0,8 não troca nunca, nem navegando nem parado; um SOG 0 de 3 s (menos que os 5 s) não pisca o conjunto; e FUNDEADO × ATRACADO vem do estado do quadro."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'E1-Navegando-Gatilhos', fixo='60')
    def modo(): return pg.evaluate(LE_E1_MIN)
    n = [0]
    def muda(v):
        n[0] += 1; pg.evaluate(SOBRE_JS, [v, n[0]])
    muda({'sog_nos': 0.8, 'estado': 'Navegando'}); pg.wait_for_timeout(7500)
    if modo()['modo'] != 'nav': prob.append('E1: navegando, o SOG de 0,8 nó trocou o conjunto (histerese: só sai abaixo de 0,5 nó)')
    muda({'sog_nos': 0.3, 'estado': 'Atracado'}); pg.wait_for_timeout(7500)
    m = modo()
    if m['modo'] != 'parado' or m['titulo'] != 'GATILHOS · ATRACADO': prob.append('E1: com o SOG em 0,3 nó por 7 s e o quadro Atracado: %s (esperado parado · ATRACADO)' % m)
    muda({'sog_nos': 0.8, 'estado': 'Atracado'}); pg.wait_for_timeout(7500)
    if modo()['modo'] != 'parado': prob.append('E1: parado, o SOG de 0,8 nó trocou o conjunto (histerese: só entra com 1 nó ou mais)')
    muda({'sog_nos': 1.2, 'estado': 'Navegando'}); pg.wait_for_timeout(7500)
    if modo()['modo'] != 'nav': prob.append('E1: o SOG de 1,2 nó por 7 s não voltou a NAVEGANDO')
    muda({'sog_nos': 0, 'estado': 'Fundeado'}); pg.wait_for_timeout(3000)
    muda(None); pg.wait_for_timeout(7000)   # um SOG 0 de 3 s e o quadro normal de volta: nenhuma troca
    m = modo()
    if m['modo'] != 'nav' or 'registrar' not in m['ids']: prob.append('E1: um SOG 0 de 3 s (menos de 5 s) trocou o conjunto: %s' % m)
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_e1_aba_escondida(b):
    """A contagem dos 5 s zera num intervalo sem tique (aba escondida): o SOG 0 visto 2 s antes de a aba esconder por 4 s não vale como 5 s seguidos."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'E1-Navegando-Gatilhos', fixo='60')
    pg.evaluate(SOBRE_JS, [{'sog_nos': 0, 'estado': 'Fundeado'}, 1])
    pg.wait_for_timeout(2500)
    pg.evaluate("() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => true }); document.dispatchEvent(new Event('visibilitychange')); }")
    pg.wait_for_timeout(4000)
    pg.evaluate("() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => false }); document.dispatchEvent(new Event('visibilitychange')); }")
    pg.wait_for_timeout(1800)
    m = pg.evaluate(LE_E1_MIN)
    if m['modo'] != 'nav': prob.append('E1: voltando de 4 s escondida, o SOG 0 visto antes dela trocou o conjunto na hora (a contagem devia zerar): %s' % m)
    pg.wait_for_timeout(5500)
    m = pg.evaluate(LE_E1_MIN)
    if m['modo'] != 'parado': prob.append('E1: depois de 5 s à vista com o SOG 0 o conjunto não trocou: %s' % m)
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_e1_registrar(b):
    """REGISTRAR POSIÇÃO só com o toque: abrir não grava; 1 toque = 1 linha nova (sim: true, src de atalho), o toque duplo em 2,5 s não duplica, o seguinte é linha nova; com a janela de conversa em emergência valendo a linha
    leva «LEIA NO PLOTTER» no lugar da posição, do SOG e da proa."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'E1-Navegando-Gatilhos', fixo='60')
    ls = lambda: json.loads(pg.evaluate("() => localStorage.getItem('capitao.diario.v1') || '[]'"))
    if ls(): prob.append('E1: gravou no diário só de abrir: %s' % ls())
    pg.click('[data-e1=gatilho][data-id=registrar]'); pg.wait_for_timeout(300)
    l = ls()
    if len(l) != 1 or l[0].get('sim') is not True or not re.search(r'atalho|telemetria', l[0].get('src', '')) or 'SOG 18,1 nós' not in l[0].get('t', ''): prob.append('E1: 1 toque devia gravar 1 linha de atalho com sim: true e o SOG do quadro: %s' % l)
    pg.click('[data-e1=gatilho][data-id=registrar]'); pg.wait_for_timeout(300)
    if len(ls()) != 1: prob.append('E1: o toque duplo em 2,5 s gravou outra linha (%d linhas)' % len(ls()))
    pg.wait_for_timeout(2400)
    pg.click('[data-e1=gatilho][data-id=registrar]'); pg.wait_for_timeout(300)
    if len(ls()) != 2: prob.append('E1: o toque depois dos 2,5 s devia ser linha nova (%d linhas)' % len(ls()))
    if erros: prob += erros[:2]
    ctx.close()
    ctx, pg, erros = abre_tela(b, 'E1-Navegando-Gatilhos', fixo='60', depois=JANELA_VALE)
    pg.click('[data-e1=gatilho][data-id=registrar]'); pg.wait_for_timeout(300)
    l = json.loads(pg.evaluate("() => localStorage.getItem('capitao.diario.v1') || '[]'"))
    t = l[0].get('t', '') if l else ''
    if len(l) != 1 or 'LEIA NO PLOTTER' not in t or re.search(r'SOG|proa|nós|\d+°', t): prob.append('E1 com a janela de emergência: a linha do registro devia trocar a posição por «LEIA NO PLOTTER» (sem SOG nem proa): %r' % t)
    ctx.close()
    return prob


def teste_e1_vivo(b):
    """Sem congelar o replay a E1 anda sozinha: o chip «AO VIVO hh:mm:ss» muda em 1,5 s e a hora dele é a do instante (assina o capitao-telemetria)."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'E1-Navegando-Gatilhos', fixo=None)
    mudou = False
    for _ in range(3):
        a = pg.evaluate(LE_E1)
        pg.wait_for_timeout(1500)
        c = pg.evaluate(LE_E1)
        if not re.fullmatch(r'AO VIVO \d\d:\d\d:\d\d', c['chip'] or ''): prob.append('E1 livre: o chip diz %r (esperado «AO VIVO hh:mm:ss»)' % c['chip']); break
        if a['chip'] != c['chip'] and c['chip'] == 'AO VIVO ' + c['hora']: mudou = True; break
    if not mudou: prob.append('E1 livre: o chip não mudou em 1,5 s (3 tentativas): a tela não assina o capitao-telemetria')
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_e1_real(b):
    """E1 com simulacao false: sem replay, a última leitura salva (26/09 10:12) como reserva, com SEM LEITURA no que falta e o conjunto do barco parado do quadro; sem NaN, undefined nem AO VIVO."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'E1-Navegando-Gatilhos', fixo=None, depois='window.CapitaoDados.simulacao = false;')
    r = pg.evaluate(LE_E1)
    rot = 'E1 com simulacao false'
    if r['fonte'] != 'snapshot' or not pg.evaluate("() => !window.CapitaoReplay.ativo()"): prob.append('%s: o replay ainda anda (%s)' % (rot, r['fonte']))
    if re.search(r'NaN|undefined|\[object|Infinity|AO VIVO', r['texto']): prob.append('%s: NaN, undefined, [object ou AO VIVO na tela: %s' % (rot, re.search(r'NaN|undefined|\[object|Infinity|AO VIVO', r['texto']).group(0)))
    for t in ('ÚLTIMA LEITURA', 'Vigia automática inativa · SEM LEITURA ao vivo', 'Última leitura salva · coletor NMEA · leitura de 26/09 10:12'):
        if t not in r['texto']: prob.append('%s: a tela devia dizer %r' % (rot, t))
    if ids_e1(r) != IDS_PARADO or r['titulo'] != 'GATILHOS · FUNDEADO': prob.append('%s: o conjunto é %s (%s): esperado o do barco fundeado da última leitura' % (rot, ids_e1(r), r['titulo']))
    if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
    ctx.close()
    return prob


def teste_e1_codigo():
    prob = []
    def le_(a):
        t = open(os.path.join(RAIZ, a), encoding='utf-8').read()
        for velho, novo in MUT_ARQ.get(a, []): t = t.replace(velho, novo, 1)
        return t
    h = le_('E1-Navegando-Gatilhos.dc.html')
    cod = re.sub(r'//[^\n]*', '', h)
    mont, desm = h.find('componentDidMount'), h.find('componentWillUnmount')
    for ev in ('capitao-telemetria', 'capitao-alerta', 'capitao-rebase'):
        if "'%s'" % ev not in h[mont:desm] or "'%s'" % ev not in h[desm:desm + 400]: prob.append('E1: não assina o %s no componentDidMount e remove no componentWillUnmount' % ev)
    if "forEach((ev) => window.addEventListener(ev, this._onTele))" not in h[mont:desm] or "forEach((ev) => window.removeEventListener(ev, this._onTele))" not in h[desm:desm + 400]: prob.append('E1: addEventListener/removeEventListener fora do par do componentDidMount/componentWillUnmount')
    if 'document.hidden' not in h: prob.append('E1: não pausa com document.hidden')
    if 'if (!forca && k === this._k) return;' not in h or 'this.setState({ vivo: k })' not in h: prob.append('E1: não compara o texto antes do setState')
    if h.count('setInterval') != 1: prob.append('E1: setInterval a mais (%d; só o do whenBrain)' % h.count('setInterval'))
    if re.search(r'D\.demo|\.demo\b|DEMO|D\.snapshot|\.snapshot\b', cod): prob.append('E1: lê D.demo ou D.snapshot (ou escreve DEMO) no código')
    if MARCAS_FIXAS.search(cod): prob.append('E1: fabricante fixo no código: %s' % MARCAS_FIXAS.search(cod).group(0))
    if re.search(r'location\s*\.\s*(href|assign|replace|reload)|window\s*\.\s*open|speechSynthesis|history\s*\.\s*(push|replace)State', cod): prob.append('E1: troca de tela, abre janela ou fala sozinha')
    if 'ENTRA = 1, SAI = 0.5, ESPERA = 5000' not in h: prob.append('E1: os limiares da troca não são 1 nó, 0,5 nó e 5 s')
    if h.count('B.answer(') != 1 or h.find('B.answer(') < h.find('  registrar() {') or 'onClick="{{registrar}}"' not in h or h.count('this.registrar()') != 1: prob.append('E1: o cérebro responde fora do registrar() ou o registro não é só pelo toque')
    if 'emergencia: emergencia' not in h: prob.append('E1: o registrar() não passa a janela de emergência ao cérebro')
    if re.search(r'addDiario|localStorage\s*\.\s*setItem', cod): prob.append('E1: grava direto (o cérebro grava)')
    GEOM = re.compile(r'<(?:svg|path|circle|line|rect|ellipse|polyline|polygon|g)\b[^>]*\b(?:d|x|y|x1|x2|y1|y2|cx|cy|r|rx|ry|width|height|viewBox|points|transform)="[^"]*\{\{')
    if GEOM.search(h): prob.append('E1: {{…}} em atributo geométrico de SVG')
    return prob


# E2: o que a tela mostra da leitura de agora e da resposta
LE_E2 = """() => { """ + JS_BASE + """
  const g = (s) => { const e = document.querySelector('[data-e2=' + s + ']'); return e ? lin(e.innerText) : null; }, sec = document.querySelector('[data-e2=resposta]');
  return { hora: I.hora, hhmm: I.hhmm, fonteTxt: I.fonteTxt, T, intro: g('intro'), ref: g('ref'), refTexto: g('ref-texto'), refFonte: g('ref-fonte'), pergunta: g('pergunta'), fonte: g('fonte'), chave: sec ? sec.dataset.chave : null,
    resp: sec ? lin(sec.innerText) : null, texto: lin(document.body.innerText), emerg: window.CapitaoEmergencia ? window.CapitaoEmergencia.valendo() : null, ate: sessionStorage.getItem('capitao.emergenciaAte'),
    diario: localStorage.getItem('capitao.diario.v1'), sistemas: [...document.querySelectorAll('button[aria-label^="Sistema:"]')].map((e) => ({ txt: lin(e.innerText), aria: e.getAttribute('aria-label') })),
    sintomas: [...document.querySelectorAll('button[aria-pressed]:not([aria-label])')].map((e) => lin(e.innerText)), eq: D.equipamentos.map((e) => ({ id: e.id, f: e.fabricante, m: e.modelo, n: e.nome })),
    regBt: !!document.querySelector('button[aria-label^="Registrar no diário"]'), url: location.href }; }"""
SIS_E2 = [('motores', 'MOTORES'), ('gerador', 'GERADOR'), ('climatizacao', 'CLIMA'), ('estabilizador', 'ESTABILIZADOR'), ('eletronicos', 'ELETRÔNICOS')]
SINTOMAS_E2 = {'motores': ['Temperatura alta', 'Pressão de óleo baixa', 'Sem água no escapamento', 'Não liga', 'Fumaça / cheiro de queimado', 'Entrada de água']}
ORACULO_E2 = {'60': 'Motores ligados · BB 2.049 · BE 2.038 rpm · óleo BB 3,9 · BE 3,8 bar · arrefecimento BB 82,0 · BE 82,1 °C.',
              '105': 'Motores ligados · BB 2.049 · BE 2.036 rpm · óleo BB 3,9 · BE 3,8 bar · arrefecimento BB 81,9 · BE 89,6 °C.'}   # CONTRATO §1.22


def clica_e2(pg, tipo, i):
    pg.click('button[aria-pressed][aria-label^="Sistema:"] >> nth=%d' % i if tipo == 'sis' else 'button[aria-pressed]:not([aria-label]) >> nth=%d' % i)
    pg.wait_for_timeout(250)


def esperado_ref_e2(sid, T, fab):
    par = lambda a, b, suf: 'BB %s · BE %s%s' % (T[a], T[b], suf)
    if sid == 'motores': return 'Motores ligados · %s · óleo %s · arrefecimento %s.' % (par('motor_bb_rpm', 'motor_be_rpm', ' rpm'), par('motor_bb_oleo_bar', 'motor_be_oleo_bar', ' bar'), par('motor_bb_arref_c', 'motor_be_arref_c', ' °C'))
    if sid == 'gerador': return 'Gerador ligado · %s kW · horímetro %s h.' % (T['gerador_kw'], T['gerador_horimetro_h'])
    if sid == 'estabilizador': return '%s ligado · volante %s rpm (%s %%).' % (fab, T['seakeeper_volante_rpm'], T['seakeeper_volante_pct'])
    if sid == 'climatizacao': return 'Climatização ligada.'
    return 'GPS com %s satélites · radar ligado · AIS com %s alvos.' % (T['gps_satelites'], T['ais_alvos'])


def teste_e2_ref(b):
    """E2: a leitura de agora de cada um dos 5 sistemas vem do quadro do instante (60 s e 105 s: motores, gerador kW, Seakeeper rpm e %, climatização, GPS com satélites), com a fonte «telemetria ao vivo · hh:mm:ss»;
    o fabricante e o modelo de cada sistema são os de D.equipamentos (nunca «modelo SEM DADOS»); a introdução sem «(guias DEMO)»; nada do snapshot de 26/09."""
    prob = []
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_tela(b, 'E2-Navegando-Sintoma', fixo=fixo)
        r = pg.evaluate(LE_E2)
        if r['intro'] != 'Triagem: escolha o sistema e o sintoma. O Capitão IA responde na hora com o trecho do guia de bordo e a fonte.': prob.append('E2 a %s s: a introdução diz %r' % (fixo, r['intro']))
        eq = {e['id']: e for e in r['eq']}
        for i, (sid, rot) in enumerate(SIS_E2):
            e = eq[sid]
            esp_aria = 'Sistema: ' + e['n'] + ('' if e['m'].lower().startswith(e['f'].lower()) else ' ' + e['f']) + ' ' + e['m']
            if r['sistemas'][i]['aria'] != esp_aria or r['sistemas'][i]['txt'] != '%s %s' % (rot, e['f']): prob.append('E2 a %s s: o botão do sistema %s diz %r / %r (esperado %r e «%s %s»)' % (fixo, sid, r['sistemas'][i]['aria'], r['sistemas'][i]['txt'], esp_aria, rot, e['f']))
            clica_e2(pg, 'sis', i)
            r = pg.evaluate(LE_E2)
            esp = esperado_ref_e2(sid, r['T'], e['f'])
            if sid == 'motores' and esp != ORACULO_E2[fixo]: prob.append('E2 a %s s: o oráculo dos motores não vale (%r)' % (fixo, esp))
            if r['refTexto'] != esp: prob.append('E2 a %s s · %s: a leitura de agora diz %r (esperado %r)' % (fixo, sid, r['refTexto'], esp))
            if not (r['ref'] or '').startswith('LEITURA AGORA · ' + rot) or r['refFonte'] != 'Fonte: telemetria ao vivo · ' + r['hora']: prob.append('E2 a %s s · %s: o título ou a fonte da leitura dizem %r / %r' % (fixo, sid, (r['ref'] or '')[:40], r['refFonte']))
            if re.search(r'snapshot|SEM LEITURA|SEM DADOS|26/09|desligada|última leitura com motores|DEMO\b', r['texto']): prob.append('E2 a %s s · %s: rótulo ou dado do snapshot na tela: %s' % (fixo, sid, re.search(r'snapshot|SEM LEITURA|SEM DADOS|26/09|desligada|última leitura com motores|DEMO\b', r['texto']).group(0)))
            if r['chave'] is not None: prob.append('E2 a %s s · %s: mostra resposta antes de escolher o sintoma' % (fixo, sid))
        if erros: prob += ['E2 a %s s: %s' % (fixo, e) for e in erros[:2]]
        ctx.close()
    return prob


def teste_e2_varre(b):
    """Cada sistema × cada sintoma a 60 s e a 105 s: nenhum termo do §3 no texto, no title, no aria-label, no placeholder nem no alt (nem «SEM DADOS» do fabricante, «modelo SEM DADOS» ou «(guias DEMO)»),
    nem NaN, undefined ou [object."""
    prob = []
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_tela(b, 'E2-Navegando-Sintoma', fixo=fixo)
        for i in range(len(SIS_E2)):
            clica_e2(pg, 'sis', i)
            n = pg.evaluate("() => document.querySelectorAll('button[aria-pressed]:not([aria-label])').length")
            for j in list(range(n)):
                clica_e2(pg, 'sin', j)
                t = pg.evaluate(LE_TEXTOS)
                ach = achados_termos('E2-Navegando-Sintoma', t)
                if ach: prob.append('E2 a %s s · %s/%d: termo do §3: %s' % (fixo, SIS_E2[i][0], j, ach))
                if re.search(r'NaN|undefined|\[object|Infinity|modelo SEM|fabricante SEM|guias DEMO', t): prob.append('E2 a %s s · %s/%d: NaN, undefined ou rótulo: %s' % (fixo, SIS_E2[i][0], j, re.search(r'NaN|undefined|\[object|Infinity|modelo SEM|fabricante SEM|guias DEMO', t).group(0)))
        if erros: prob += ['E2 a %s s: %s' % (fixo, e) for e in erros[:2]]
        ctx.close()
    return prob


def teste_e2_resposta(b):
    """A resposta leva o segundo do quadro (a.hora: «Calculado às 12:01:00 pelo Capitão IA» a 60 s e «12:01:45» a 105 s), a de emergência não (sos, fumaça e água): a leitura de agora some dela, e o relato de pressão de óleo
    baixa troca a leitura por «confira o manômetro agora» (sem o óleo do quadro); a resposta que abre a janela (sos, óleo) a marca em 15 min, a de rotina não."""
    prob = []
    for fixo, hora in (('60', '12:01:00'), ('105', '12:01:45')):
        ctx, pg, erros = abre_tela(b, 'E2-Navegando-Sintoma', fixo=fixo)
        clica_e2(pg, 'sis', 0)
        clica_e2(pg, 'sin', 2)   # sem água no escapamento (a resposta pronta dos motores, com a leitura do quadro)
        r = pg.evaluate(LE_E2)
        if not (r['pergunta'] or '').startswith('Calculado às %s pelo Capitão IA · pergunta: “sem água no escapamento motores' % hora): prob.append('E2 a %s s: a resposta não leva o segundo do quadro: %r' % (fixo, r['pergunta']))
        if r['chave'] == 'motores' and ('Motores ligados às %s' % hora) not in r['resp']: prob.append('E2 a %s s: a resposta dos motores não traz as %s do quadro: %r' % (fixo, hora, (r['resp'] or '')[:200]))
        if r['emerg']: prob.append('E2 a %s s: a janela de emergência abriu com uma resposta de rotina' % fixo)
        clica_e2(pg, 'sin', 0)   # temperatura alta (trecho do guia)
        r = pg.evaluate(LE_E2)
        if not (r['pergunta'] or '').startswith('Calculado às %s pelo Capitão IA' % hora): prob.append('E2 a %s s: o trecho do guia não leva o segundo do quadro: %r' % (fixo, r['pergunta']))
        for j, nome, chave in ((4, 'fumaça', 'sos'), (5, 'água', 'sos')):
            ctx2, pg2, erros2 = abre_tela(b, 'E2-Navegando-Sintoma', fixo=fixo)
            clica_e2(pg2, 'sis', 0); clica_e2(pg2, 'sin', j)
            r = pg2.evaluate(LE_E2)
            rot = 'E2 a %s s · %s' % (fixo, nome)
            if r['chave'] != chave: prob.append('%s: a resposta é %s (esperado %s)' % (rot, r['chave'], chave))
            if not (r['pergunta'] or '').startswith('Calculado agora pelo Capitão IA') or hora in (r['pergunta'] or ''): prob.append('%s: a resposta de emergência leva a hora do quadro: %r' % (rot, r['pergunta']))
            if r['refTexto'] != 'Em emergência não há leitura de referência: confira os instrumentos e o plotter agora. POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER · PESSOAS: CONTE AGORA' or not (r['ref'] or '').startswith('INSTRUMENTOS · MOTORES'): prob.append('%s: no lugar da leitura, a tela diz %r' % (rot, r['ref']))
            if re.search(r'rpm|\d,\d bar|BB \d|SOG|proa', r['texto']): prob.append('%s: leitura do quadro na tela da emergência: %s' % (rot, re.search(r'rpm|\d,\d bar|BB \d|SOG|proa', r['texto']).group(0)))
            if not r['emerg'] or not r['ate']: prob.append('%s: a resposta que abre a janela não a marcou (valendo %r, sessionStorage %r)' % (rot, r['emerg'], r['ate']))
            if erros2: prob += ['%s: %s' % (rot, e) for e in erros2[:2]]
            ctx2.close()
        ctx2, pg2, erros2 = abre_tela(b, 'E2-Navegando-Sintoma', fixo=fixo)
        clica_e2(pg2, 'sis', 0); clica_e2(pg2, 'sin', 1)
        r = pg2.evaluate(LE_E2)
        rot = 'E2 a %s s · pressão de óleo baixa' % fixo
        if r['chave'] != 'oleo' or r['refTexto'] != 'Pressão de óleo baixa: confira o manômetro de cada motor agora, no painel.': prob.append('%s: a resposta é %s e a leitura diz %r' % (rot, r['chave'], r['refTexto']))
        if re.search(r'óleo BB|\d,\d bar|rpm|BB \d', r['texto']): prob.append('%s: o óleo ou a rotação do quadro na tela do relato (relato de falha sem leitura): %s' % (rot, re.search(r'óleo BB|\d,\d bar|rpm|BB \d', r['texto']).group(0)))
        if not r['emerg']: prob.append('%s: a resposta do óleo não marcou a janela' % rot)
        ctx2.close()
        if erros: prob += ['E2 a %s s: %s' % (fixo, e) for e in erros[:2]]
        ctx.close()
    return prob


def teste_e2_janela(b):
    """A janela de conversa em emergência vale na E2 (a marca é a mesma das telas de conversa): marcada, a pergunta que chega pelo botão de uma resposta (capitao-chat-pergunta) responde com a posição trocada por
    «LEIA NO PLOTTER» (sem o ponto da rota); sem a marca, responde com a situação de bordo. A pergunta de emergência que chega pelo botão abre a janela e não mostra leitura nem botão de registro."""
    prob = []
    Q = "(q) => window.dispatchEvent(new CustomEvent('capitao-chat-pergunta', { detail: { q: q } }))"
    ctx, pg, erros = abre_tela(b, 'E2-Navegando-Sintoma', fixo='60', depois=JANELA_VALE)
    if not pg.evaluate(LE_E2)['emerg']: prob.append('E2: o teste não vale (a janela não estava marcada)')
    pg.evaluate(Q, 'Âncora'); pg.wait_for_timeout(500)
    r = pg.evaluate(LE_E2)
    if r['chave'] != 'ancora' or 'leia no plotter' not in (r['resp'] or '').lower() or 'Barra Sul' in (r['resp'] or ''): prob.append('E2 com a janela marcada: a pergunta do botão (Âncora) devia vir com «leia no plotter» e sem o ponto da rota: %r' % (r['resp'] or '')[:260])
    ctx.close()
    ctx, pg, erros = abre_tela(b, 'E2-Navegando-Sintoma', fixo='60')
    pg.evaluate(Q, 'Âncora'); pg.wait_for_timeout(500)
    r = pg.evaluate(LE_E2)
    if r['chave'] != 'ancora' or 'Barra Sul' not in (r['resp'] or '') or r['emerg']: prob.append('E2 sem a janela: a pergunta do botão (Âncora) devia vir com a situação de bordo (e não abrir a janela): %r' % (r['resp'] or '')[:200])
    if r['regBt'] or r['diario']: prob.append('E2: a resposta de um botão tem o botão de registro ou gravou no diário (%r)' % r['diario'])
    pg.evaluate(Q, 'Tem água no porão'); pg.wait_for_timeout(500)
    r = pg.evaluate(LE_E2)
    if r['chave'] != 'sos' or not r['emerg'] or not r['ate']: prob.append('E2: a pergunta de emergência do botão (porão) devia abrir a janela (resposta %s, valendo %r)' % (r['chave'], r['emerg']))
    if re.search(r'nível|BB \d|cm\b', r['resp'] or '') or r['diario']: prob.append('E2: a resposta ao relato no porão traz o nível do porão ou gravou: %r' % (r['resp'] or '')[:200])
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_e2_cache(b):
    """Sem congelar o replay: a leitura de agora anda (muda em 2,2 s) e a resposta NÃO (calculada uma vez por escolha, com a hora dela); tocar de novo no mesmo sintoma recalcula agora (hora nova); a tela só redesenha quando o texto muda."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'E2-Navegando-Sintoma', fixo=None)
    clica_e2(pg, 'sis', 0); clica_e2(pg, 'sin', 2)
    a = pg.evaluate(LE_E2)
    pg.wait_for_timeout(2200)
    c = pg.evaluate(LE_E2)
    if a['refTexto'] == c['refTexto'] and a['refFonte'] == c['refFonte']: prob.append('E2 livre: a leitura de agora não mudou em 2,2 s: a tela não assina o capitao-telemetria')
    if a['pergunta'] != c['pergunta'] or a['resp'] != c['resp']: prob.append('E2 livre: a resposta se refez sozinha em 2,2 s (devia ser calculada uma vez por escolha): %r → %r' % (a['pergunta'][:60], c['pergunta'][:60]))
    clica_e2(pg, 'sin', 2)
    d = pg.evaluate(LE_E2)
    if d['pergunta'] == c['pergunta']: prob.append('E2 livre: o toque de novo no sintoma não recalculou a resposta (a hora ficou %r)' % c['pergunta'][:40])
    if not re.match(r'Calculado às \d\d:\d\d:\d\d pelo Capitão IA', d['pergunta'] or ''): prob.append('E2 livre: a resposta sem a hora do quadro: %r' % d['pergunta'])
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_e2_registrar(b):
    """Registrar no diário só com o toque: escolher o sintoma não grava; 1 toque = 1 linha de «app · sintoma» (sim: true, sem posição nem leitura), o 2º toque no mesmo sintoma não duplica."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'E2-Navegando-Sintoma', fixo='60')
    ls = lambda: json.loads(pg.evaluate("() => localStorage.getItem('capitao.diario.v1') || '[]'"))
    clica_e2(pg, 'sis', 0); clica_e2(pg, 'sin', 0)
    if ls():   # (a tela que grava sozinha também troca o botão: sem o botão o toque abaixo daria erro e esconderia esta acusação)
        linhas = ls()
        ctx.close()
        return ['E2: gravou no diário só de escolher o sintoma: %s' % linhas]
    pg.click('button[aria-label^="Registrar no diário"]'); pg.wait_for_timeout(400)
    l = ls()
    t = l[0].get('t', '') if l else ''
    if len(l) != 1 or l[0].get('src') != 'app · sintoma' or l[0].get('sim') is not True or not t.startswith('Sintoma relatado: temperatura alta — Motores Cummins QSB6.7 305. Anomalia A CONFIRMAR · triagem no app') or re.search(r'SEM DADOS|rpm|SOG|proa|\d,\d bar', t): prob.append('E2: 1 toque devia gravar 1 linha de app · sintoma, com sim: true, sem leitura: %s' % l)
    if pg.query_selector('button[aria-label^="Registrar no diário"]'): prob.append('E2: o botão de registro continua depois de registrar')
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_e2_real(b):
    """E2 com simulacao false: a leitura vem da última leitura salva (26/09 10:12) com «ÚLTIMA LEITURA», sem NaN nem undefined, e a resposta continua do cérebro (sem a hora do quadro)."""
    prob = []
    ctx, pg, erros = abre_tela(b, 'E2-Navegando-Sintoma', fixo=None, depois='window.CapitaoDados.simulacao = false;')
    clica_e2(pg, 'sis', 0); clica_e2(pg, 'sin', 2)
    r = pg.evaluate(LE_E2)
    rot = 'E2 com simulacao false'
    if not (r['ref'] or '').startswith('ÚLTIMA LEITURA · MOTORES') or r['refFonte'] != 'Fonte: coletor NMEA · leitura de 26/09 10:12': prob.append('%s: a leitura diz %r / %r (esperado a última leitura salva)' % (rot, (r['ref'] or '')[:40], r['refFonte']))
    if re.search(r'NaN|undefined|\[object|Infinity', r['texto']): prob.append('%s: NaN, undefined ou [object na tela' % rot)
    if not (r['pergunta'] or '').startswith('Calculado agora pelo Capitão IA'): prob.append('%s: a resposta diz %r (sem o quadro, sem a hora)' % (rot, r['pergunta']))
    if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
    ctx.close()
    return prob


def teste_e2_codigo():
    prob = []
    def le_(a):
        t = open(os.path.join(RAIZ, a), encoding='utf-8').read()
        for velho, novo in MUT_ARQ.get(a, []): t = t.replace(velho, novo, 1)
        return t
    h = le_('E2-Navegando-Sintoma.dc.html')
    cod = re.sub(r'//[^\n]*', '', h)
    mont, desm = h.find('componentDidMount'), h.find('componentWillUnmount')
    for ev in ('capitao-telemetria', 'capitao-rebase'):
        if "'%s'" % ev not in h[mont:desm] or "'%s'" % ev not in h[desm:desm + 500]: prob.append('E2: não assina o %s no componentDidMount e remove no componentWillUnmount' % ev)
    if "addEventListener('capitao-chat-pergunta'" not in h[mont:desm] or "removeEventListener('capitao-chat-pergunta'" not in h[desm:desm + 500]: prob.append('E2: não escuta o capitao-chat-pergunta (o botão de uma resposta)')
    if 'document.hidden' not in h: prob.append('E2: não pausa com document.hidden')
    if 'if (k === this._refK) return;' not in h or 'this.setState({ vivo: k })' not in h: prob.append('E2: não compara o texto antes do setState')
    if h.count('setInterval') != 2: prob.append('E2: setInterval a mais ou a menos (%d; o do whenBrain e o da base)' % h.count('setInterval'))
    if re.search(r'D\.demo|\.demo\b|DEMO|D\.snapshot|\.snapshot\b|\bS\.\w+', cod): prob.append('E2: lê D.demo ou D.snapshot (ou escreve DEMO) no código')
    if MARCAS_FIXAS.search(cod): prob.append('E2: fabricante fixo no código: %s' % MARCAS_FIXAS.search(cod).group(0))
    if "commit: false" not in h or 'emergencia: emergencia' not in h or 'a.abreJanela === true' not in h or 'E.marca()' not in h: prob.append('E2: a resposta não passa commit:false e a janela de emergência ao cérebro, ou não marca a janela')
    if h.count('addDiario') != 1 or h.find('addDiario') < h.find('  registrar(s, x, a) {') or 'onClick="{{registrar}}"' not in h: prob.append('E2: grava no diário fora do registrar() ou sem ser pelo toque')
    if re.search(r'location\s*\.\s*(href|assign|replace|reload)|window\s*\.\s*open|speechSynthesis', cod): prob.append('E2: troca de tela, abre janela ou fala sozinha')
    GEOM = re.compile(r'<(?:svg|path|circle|line|rect|ellipse|polyline|polygon|g)\b[^>]*\b(?:d|x|y|x1|x2|y1|y2|cx|cy|r|rx|ry|width|height|viewBox|points|transform)="[^"]*\{\{')
    if GEOM.search(h): prob.append('E2: {{…}} em atributo geométrico de SVG')
    return prob


def p4f_conferencias(b, lista):
    """[(nome, problemas)] das conferências da P4F para as telas da rodada."""
    out = []
    if 'E1-Navegando-Gatilhos' in lista:
        out.append(('código da E1', teste_e1_codigo()))
        out.append(('E1 · NAVEGANDO a 60 e 105 s: conjunto, links, vigia ao vivo, sem rótulo', teste_e1_nav(b)))
        out.append(('E1 · o alarme: o 1º cartão leva à C3 (aviso, crítico plantado, barco parado)', teste_e1_alerta(b)))
        out.append(('E1 · a troca automática com 5 s seguidos (NAVEGANDO × FUNDEADO)', teste_e1_troca(b)))
        out.append(('E1 · a histerese e o ATRACADO', teste_e1_histerese(b)))
        out.append(('E1 · a aba escondida zera a contagem', teste_e1_aba_escondida(b)))
        out.append(('E1 · REGISTRAR POSIÇÃO só com o toque (e com a janela de emergência)', teste_e1_registrar(b)))
        out.append(('E1 · anda sozinha sem congelar o replay', teste_e1_vivo(b)))
        out.append(('E1 · simulacao false', teste_e1_real(b)))
    if 'E2-Navegando-Sintoma' in lista:
        out.append(('código da E2', teste_e2_codigo()))
        out.append(('E2 · a leitura de agora de cada sistema, o fabricante e a introdução', teste_e2_ref(b)))
        out.append(('E2 · cada sistema × sintoma sem rótulo', teste_e2_varre(b)))
        out.append(('E2 · a resposta leva o segundo do quadro; a emergência e o óleo sem leitura', teste_e2_resposta(b)))
        out.append(('E2 · a janela de conversa em emergência e o botão de uma resposta', teste_e2_janela(b)))
        out.append(('E2 · a resposta é calculada uma vez por escolha; a leitura anda', teste_e2_cache(b)))
        out.append(('E2 · registrar só com o toque', teste_e2_registrar(b)))
        out.append(('E2 · simulacao false', teste_e2_real(b)))
    return out


MUTANTES_P4F = [
    # —— E1 ——
    ('a troca da E1 sem espera (ESPERA = 0: pisca com qualquer leitura)', 'E1-Navegando-Gatilhos.dc.html', [("ENTRA = 1, SAI = 0.5, ESPERA = 5000", "ENTRA = 1, SAI = 0.5, ESPERA = 0")], 'troca'),
    ('a troca da E1 com 20 s de espera (nunca troca na hora)', 'E1-Navegando-Gatilhos.dc.html', [("ENTRA = 1, SAI = 0.5, ESPERA = 5000", "ENTRA = 1, SAI = 0.5, ESPERA = 20000")], 'troca'),
    ('a E1 sem histerese (sai com menos de 1 nó)', 'E1-Navegando-Gatilhos.dc.html', [("ENTRA = 1, SAI = 0.5, ESPERA = 5000", "ENTRA = 1, SAI = 1, ESPERA = 5000")], 'histerese'),
    ('a E1 entra em NAVEGANDO com 0,5 nó (ENTRA = 0,5)', 'E1-Navegando-Gatilhos.dc.html', [("ENTRA = 1, SAI = 0.5, ESPERA = 5000", "ENTRA = 0.5, SAI = 0.5, ESPERA = 5000")], 'histerese'),
    ('a E1 não zera a contagem depois de um intervalo sem tique', 'E1-Navegando-Gatilhos.dc.html', [("if (this._ult1 && agora - this._ult1 > 2500) this._cand = null;", "")], 'aba'),
    ('a E1 sem o FUNDEADO × ATRACADO do quadro (sempre FUNDEADO)', 'E1-Navegando-Gatilhos.dc.html', [("(/atrac/i.test(est) ? 'ATRACADO' : /fundead/i.test(est) ? 'FUNDEADO' : 'FUNDEADO / ATRACADO')", "'FUNDEADO'")], 'histerese'),
    ('o 1º cartão de alerta da E1 sem o id do alarme (C3 sem #alarme=)', 'E1-Navegando-Gatilhos.dc.html', [("typeof al.detalhe === 'string' && al.detalhe ? al.detalhe : 'C3-Leme-Alerta.dc.html#alarme=' + al.id,", "'C3-Leme-Alerta.dc.html',")], 'alerta'),
    ('o cartão de alerta da E1 depois dos gatilhos (order 9)', 'E1-Navegando-Gatilhos.dc.html', [("'M12 4 21 20H3z M12 10v4 M12 17h.01', crit ? 'critico' : 'aviso', 0,", "'M12 4 21 20H3z M12 10v4 M12 17h.01', crit ? 'critico' : 'aviso', 9,")], 'alerta'),
    ('o alerta crítico da E1 sem o fundo vermelho', 'E1-Navegando-Gatilhos.dc.html', [("critico: { line: 'var(--cap-crit-fill, #d32f27)', cor: '#ffffff', bg: 'var(--cap-crit-fill, #d32f27)',", "critico: { line: 'var(--cap-crit-fill, #d32f27)', cor: '#ffffff', bg: 'rgba(var(--cap-warn-rgb, 240,166,58), 0.12)',")], 'alerta'),
    ('a E1 sem assinar o capitao-telemetria', 'E1-Navegando-Gatilhos.dc.html', [("['capitao-telemetria', 'capitao-alerta', 'capitao-rebase'].forEach((ev) => window.addEventListener(ev, this._onTele));", "['capitao-alerta', 'capitao-rebase'].forEach((ev) => window.addEventListener(ev, this._onTele));")], 'vivo'),
    ('o diesel da E1 de volta no snapshot (54/52)', 'E1-Navegando-Gatilhos.dc.html', [("dieselOk ? Math.round(q.diesel_bb_pct) + '/' + Math.round(q.diesel_be_pct) : null", "dieselOk ? '54/52' : null")], 'nav'),
    ('o chip da E1 sem os segundos (AO VIVO hh:mm)', 'E1-Navegando-Gatilhos.dc.html', [("chip = 'AO VIVO ' + I.hora;", "chip = 'AO VIVO ' + I.hhmm;")], 'nav'),
    ('o gatilho do porão da E1 sem a leitura (SEM LEITURA fixo)', 'E1-Navegando-Gatilhos.dc.html', [("'Passo a passo do Capitão IA · sensor ' + porao,", "'Passo a passo do Capitão IA · sensor SEM LEITURA',")], 'nav'),
    ('o gatilho do porão da E1 pergunta só «Porão» (a leitura, não o relato)', 'E1-Navegando-Gatilhos.dc.html', [("ask('Tem água no porão')", "ask('Porão')")], 'nav'),
    ('a nota da troca da E1 de volta com «ainda não está ativa»', 'E1-Navegando-Gatilhos.dc.html', [("especificado: 'o conjunto de botões muda sozinho com o SOG:", "especificado: 'a troca automática ainda não está ativa nesta demonstração. O conjunto de botões muda sozinho com o SOG:")], 'nav'),
    ('o REGISTRAR POSIÇÃO continua com o barco parado', 'E1-Navegando-Gatilhos.dc.html', [("reg: { on: tele.conj === 'nav',", "reg: { on: true,")], 'troca'),
    ('a E1 registra sozinha ao abrir (sem o toque)', 'E1-Navegando-Gatilhos.dc.html', [("this.whenBrain(() => this.atualiza(true));", "this.whenBrain(() => { this.atualiza(true); this.registrar(); });")], 'registrar'),   # (uma linha só: o arquivo é CRLF e o trecho com \\n não casaria com o corpo servido)
    ('o registrar da E1 sem a janela de emergência', 'E1-Navegando-Gatilhos.dc.html', [("{ platform: 'app', emergencia: emergencia }", "{ platform: 'app' }")], 'registrar'),
    ('o link do CHECKLIST DE SAÍDA da E1 na web', 'E1-Navegando-Gatilhos.dc.html', [("'C4-Checklist-Mobile.dc.html#tipo=saida'", "'C4-Checklist-Web.dc.html#tipo=saida'")], 'troca'),
    # —— E2 ——
    ('a leitura dos motores da E2 fixa no snapshot (700/690 rpm)', 'E2-Navegando-Sintoma.dc.html', [("t = p.length ? 'Motores ' + (gira ? 'ligados' : 'desligados') + ' · ' + p.join(' · ') + '.' : null;", "t = 'Motores desligados · BB 700 · BE 690 rpm.';")], 'ref'),
    ('a E2 sem assinar o capitao-telemetria', 'E2-Navegando-Sintoma.dc.html', [("['capitao-telemetria', 'capitao-rebase'].forEach((ev) => window.addEventListener(ev, this._onTele));", "['capitao-rebase'].forEach((ev) => window.addEventListener(ev, this._onTele));")], 'cache'),
    ('a resposta da E2 se refaz a cada segundo (o segundo na chave)', 'E2-Navegando-Sintoma.dc.html', [("return this.pergunta(s, x) + '|' + this.state.baseOk + '|' + this.state.seq; }", "return this.pergunta(s, x) + '|' + this.state.baseOk + '|' + this.state.seq + '|' + Math.floor(Date.now() / 1000); }")], 'cache'),
    ('o toque de novo no sintoma da E2 não recalcula', 'E2-Navegando-Sintoma.dc.html', [("onClick: () => this.setState({ sin: y.id, seq: this.state.seq + 1, livre: null,", "onClick: () => this.setState({ sin: y.id, seq: this.state.seq, livre: null,")], 'cache'),
    ('a resposta da E2 sem a hora do quadro', 'E2-Navegando-Sintoma.dc.html', [("(hora ? 'Calculado às ' + hora + ' pelo Capitão IA' : 'Calculado agora pelo Capitão IA')", "'Calculado agora pelo Capitão IA'")], 'resposta'),
    ('a E2 sem a janela de emergência no cérebro', 'E2-Navegando-Sintoma.dc.html', [("{ platform: 'app', commit: false, emergencia: emergencia }", "{ platform: 'app', commit: false }")], 'janela'),
    ('a E2 não marca a janela quando a resposta a abre', 'E2-Navegando-Sintoma.dc.html', [("if (a && a.abreJanela === true) { try { if (E) E.marca(); } catch (e) {} }", "")], 'resposta'),
    ('a E2 mostra a leitura do quadro na emergência e no relato do óleo', 'E2-Navegando-Sintoma.dc.html', [("if (oleo || emerg) {", "if (false) {")], 'resposta'),
    ('o fabricante da E2 de volta com «modelo SEM DADOS»', 'E2-Navegando-Sintoma.dc.html', [("(m ? ' ' + m : sim ? '' : ' · modelo SEM DADOS');", "(m ? ' ' + m + ' · modelo SEM DADOS' : '');")], 'varre'),
    ('a introdução da E2 de volta com «(guias DEMO)»', 'E2-Navegando-Sintoma.dc.html', [("com o trecho do guia de bordo e a fonte.',", "com o trecho do guia de bordo e a fonte (guias DEMO).',")], 'ref'),
    ('a fonte da leitura da E2 de volta com «telemetria ao vivo desligada»', 'E2-Navegando-Sintoma.dc.html', [("fonte: 'Fonte: ' + fonte };", "fonte: 'Fonte: ' + fonte + ' — telemetria ao vivo desligada' };")], 'ref'),
    ('a E2 registra sozinha ao escolher o sintoma', 'E2-Navegando-Sintoma.dc.html', [("onClick: () => this.setState({ sin: y.id, seq: this.state.seq + 1, livre: null, reg: null, nota: '' }, () => this.mostra())", "onClick: () => this.setState({ sin: y.id, seq: this.state.seq + 1, livre: null, reg: null, nota: '' }, () => { this.mostra(); this.registrar(s, y, null); })")], 'registrar'),
]
QUAL_P4F = {'troca': lambda b: teste_e1_troca(b), 'histerese': lambda b: teste_e1_histerese(b), 'aba': lambda b: teste_e1_aba_escondida(b), 'alerta': lambda b: teste_e1_alerta(b), 'vivo': lambda b: teste_e1_vivo(b) + teste_e1_codigo(),
            'nav': lambda b: teste_e1_nav(b), 'registrar': lambda b: teste_e1_registrar(b) + teste_e2_registrar(b), 'ref': lambda b: teste_e2_ref(b), 'cache': lambda b: teste_e2_cache(b) + teste_e2_codigo(),
            'resposta': lambda b: teste_e2_resposta(b), 'janela': lambda b: teste_e2_janela(b), 'varre': lambda b: teste_e2_varre(b)}


def mutantes_p4f(b):
    global MUT_ARQ
    vivos = []
    filtro = os.environ.get('MUT_FILTRO', '')   # só os mutantes cujo nome tem este texto (para refazer um)
    for nome, arq, trocas, qual in MUTANTES_P4F:
        if filtro and filtro not in nome: continue
        src = open(os.path.join(RAIZ, arq), encoding='utf-8').read()
        faltam = [x for x, _ in trocas if src.count(x) != 1]
        if faltam:
            print('ERRO no mutante «%s»: o trecho não está uma vez em %s: %s' % (nome, arq, faltam)); vivos.append(nome); continue
        MUT_ARQ = {arq: trocas}
        sai = sys.stdout
        prob = []
        try:
            sys.stdout = open(os.devnull, 'w')
            prob = QUAL_P4F[qual](b)
        except Exception as e:   # um erro do próprio teste não conta como acusação: o mutante fica vivo
            sys.stdout = sai
            print('ERRO do teste no mutante «%s»: %s' % (nome, str(e).splitlines()[-1][:160]))
            prob = []
        finally:
            sys.stdout = sai
            MUT_ARQ = {}
        print('MUTANTE %s: %s (%d problema(s))%s' % ('ACUSADO' if prob else 'VIVO', nome, len(prob), ' · ' + prob[0][:150] if prob else ''))
        if not prob: vivos.append(nome)
    print('%d mutantes · %d vivos' % (len(MUTANTES_P4F), len(vivos)))
    return vivos


# ═══ Fase 4, P4G: a Home (Main e H2) e os atalhos (H3 web e app) ═══
# `--so-p4g [Main|H2-Home-Mobile|H3-Atalhos-Editar-Web|H3-Atalhos-Editar]` roda só as conferências dela; `--mutantes-p4g` planta os defeitos (MUTANTES_P4G), cada um servido no lugar do arquivo (MUT_ARQ) e acusado pela
# conferência que cuida dele (`MUT_FILTRO=texto` refaz só os mutantes cujo nome tem o texto). O Worker da IA é de mentira (ctx.route): não gasta cota; cada corpo que o app manda fica em estado['pedidos'].
TELAS_P4G = ('Main', 'H2-Home-Mobile', 'H3-Atalhos-Editar-Web', 'H3-Atalhos-Editar')
TELAS_HOME = ('Main', 'H2-Home-Mobile')
TELAS_H3 = ('H3-Atalhos-Editar-Web', 'H3-Atalhos-Editar')
CAMPO_HOME = {'Main': '#pergunta', 'H2-Home-Mobile': '#pergunta-m'}
URL_IA = re.search(r"var URL_PROXY = '([^']+)'", open(os.path.join(RAIZ, 'capitao-ia.js'), encoding='utf-8').read()).group(1)
TEXTO_IA_HOME = 'Resposta da IA: confira o painel do gerador.'
PEDIDO_IA = 'como se faz um nó lais de guia?'   # sem resposta pronta: cai em fallback e vai à IA
RELATO_DEFEITO = 'O gerador desligou sozinho duas vezes hoje de manhã quando ligamos o ar condicionado'   # vira proposta de relato com «O que verificar?»
ORACULO_HOME = {   # CONTRATO §1.22 (as horas, o SOG e o diesel dos dois instantes); o resto sai do D.campos (T)
    '60': {'hora': '12:01:00', 'sog': '18,1 NÓS', 'diesel': '1.333 L (83,3 %)', 'ger': '1.241,4 h', 'estado': 'NAVEGANDO · AO LARGO DA ILHA DAS CABRAS, A CAMINHO DA BARRA SUL'},
    '105': {'hora': '12:01:45', 'sog': '18,0 NÓS', 'diesel': '1.332 L (83,3 %)', 'ger': '1.241,4 h', 'estado': 'NAVEGANDO · NA SAÍDA DA BARRA SUL, CHEGANDO'}}
NOMES_MAIN = ['1 · CONSOLE', '2 · GERADOR', '3 · CLIMATIZAÇÃO', '4 · ESTABILIZADOR', '5 · ELETRÔNICOS']
NOMES_H2 = ['2 · GERADOR', '3 · CLIMATIZAÇÃO', '4 · ESTABILIZADOR', '5 · ELETRÔNICOS']
FABRICANTES_FALSOS = ("(() => { const E = window.CapitaoDados.equipamentos, z = { gerador: 'Zyxgerador', climatizacao: 'Zyxclima', estabilizador: 'Zyxestab', eletronicos: 'Zyxeletro', audio: 'Zyxaudio', vhf: 'Zyxvhf' }; "
                      "E.forEach((e) => { if (z[e.id]) { e.fabricante = z[e.id]; e.modelo = z[e.id] + ' Mod9'; } }); })();")
SEM_FABRICANTE = "(() => { window.CapitaoDados.equipamentos.forEach((e) => { if (['gerador', 'climatizacao', 'estabilizador', 'eletronicos', 'audio', 'vhf'].indexOf(e.id) >= 0) { e.fabricante = ''; e.modelo = ''; } }); })();"
OUVINTES_JS = """(() => { const add = window.addEventListener, rem = window.removeEventListener, c = {};
  window.__ev = (t) => (c[t] || new Set()).size;
  window.addEventListener = function (t, f, o) { (c[t] = c[t] || new Set()).add(f); return add.call(this, t, f, o); };
  window.removeEventListener = function (t, f, o) { if (c[t]) c[t].delete(f); return rem.call(this, t, f, o); }; })()"""
EVENTOS_HOME = ['capitao-telemetria', 'capitao-rebase', 'capitao-chat-pergunta', 'hashchange', 'capitao-voz-encerrar']
PNG_1X1 = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000001e221bc330000000049454e44ae426082')

LE_HOME = """() => { """ + JS_BASE + """
  const el = (s) => document.querySelector('[data-home=' + s + ']'), g = (s) => { const e = el(s); return e ? lin(e.innerText) : null; };
  const led = el('led') || el('selo'), bola = led ? led.querySelector('span') : null, cs = bola ? getComputedStyle(bola) : null;
  const E = D.embarcacao || {}, eq = (D.equipamentos || []).map((e) => ({ id: e.id, f: e.fabricante, m: e.modelo })), ag = D.agenda || [];
  const cartoes = [...document.querySelectorAll('[data-home=cartao]')].map((e) => ({ href: e.getAttribute('href'), title: e.title, aria: e.getAttribute('aria-label'), txt: lin(e.innerText),
    nome: lin((e.querySelector('[data-home=nome]') || {}).innerText), eq: lin((e.querySelector('[data-home=eq]') || {}).innerText), chip: lin((e.querySelector('[data-home=chip]') || {}).innerText),
    ponto: (() => { const d = e.querySelector('span[style*="border-radius: 50%"]'); return d ? getComputedStyle(d).backgroundColor : null; })() }));
  const est = el('estado'), hora = el('hora'), rod = document.querySelector('footer'), sel = el('selo') || el('led');
  const feitas = (() => { try { return JSON.parse(localStorage.getItem('capitao.executado.v1') || '{}'); } catch (e) { return {}; } })();
  return { hora: I.hora, hhmm: I.hhmm, fonte: I.fonte, T, q: { estado: q.estado, local: q.local }, selo: g('selo'), seloTitle: sel ? sel.title : null, ledAria: el('led') ? el('led').getAttribute('aria-label') : null,
    ledCor: cs ? cs.backgroundColor : null, ledAnim: cs ? cs.animationName : null, reg: g('reg'), registro: E.registro, faixa: [...document.querySelectorAll('[data-home=faixa]')].map((e) => lin(e.innerText)),
    estado: est ? lin(est.innerText) : null, estadoTitle: est ? est.title : null, horaTxt: hora ? lin(hora.innerText) : null, corteHora: hora ? hora.scrollWidth - hora.clientWidth : null,
    rodLateral: rod ? rod.scrollWidth - rod.clientWidth : null, cartoes, eq, ag: ag.filter((t) => t.id === 'gerador-rotor' || t.id === 'clima-filtro').map((t) => ({ id: t.id, dn: t.dn })), faq: Object.keys(D.faq).map((k) => ({ k, st: D.faq[k].status, n: (D.faq[k].perguntas || []).length })),
    atrasadas: A.contagens().atrasadas, consoleChip: g('console-chip'), feitas, texto: lin(document.body.innerText), lateral: document.documentElement.scrollWidth - document.documentElement.clientWidth }; }"""


def fab_mod(f, m):
    f, m = f or '', m or ''
    return m if f and m and m.lower().startswith(f.lower()) else ' '.join(x for x in (f, m) if x)


def fabs_eletronicos(eq):
    d = {e['id']: e for e in eq}
    fabs = []
    for i in ('eletronicos', 'audio', 'vhf'):
        f = (d.get(i) or {}).get('f')
        if f and f not in fabs: fabs.append(f)
    return fabs


def atrasada(r, tarefa):
    dn = [t['dn'] for t in r['ag'] if t['id'] == tarefa]
    return dn[0] if dn and isinstance(dn[0], int) and dn[0] < 0 and not r['feitas'].get(tarefa) else None


def chip_equip(r, k, tarefa):
    """O chip do cartão: «ROTOR · 2 D» / «FILTRO · 16 D» enquanto a tarefa está atrasada e não foi executada; senão o status do FAQ («PRONTO») ou a contagem do eletrônicos."""
    dn = atrasada(r, tarefa) if tarefa else None
    if dn is not None: return ('ROTOR' if tarefa == 'gerador-rotor' else 'FILTRO') + ' · %d D' % -dn
    f = [x for x in r['faq'] if x['k'] == k][0]
    return 'PRONTO' if f['st'] == 'PRONTO' and k != 'eletronicos' else '%d FAQ' % f['n']


def problemas_home_leitura(r, fixo, tela):
    """O que a Home mostra do instante fixado: a origem («AO VIVO · hh:mm:ss» na Main; o LED e a dica na H2), o LED verde que pulsa, o registro do cadastro, a faixa de baixo (só da Main) igual ao D.campos,
    o estado e o local do quadro, a hora que não é cortada e os cartões com o fabricante, o modelo, as horas do gerador e os prazos."""
    p, o, rot = [], ORACULO_HOME[fixo], '%s a %s s' % (tela, fixo)
    main = tela == 'Main'
    if r['hora'] != o['hora']: p.append('%s: o instante é %s (esperado %s): o teste não vale' % (rot, r['hora'], o['hora']))
    if cor_do_selo(r['ledCor']) != 'verde' or 'capVivo' not in (r['ledAnim'] or ''): p.append('%s: o LED é %s (%s) e a animação %r: esperado verde que pulsa (selo do coletor, F06)' % (rot, cor_do_selo(r['ledCor']), r['ledCor'], r['ledAnim']))
    if main:
        if r['selo'] != 'AO VIVO · ' + o['hora']: p.append('%s: o selo diz %r (esperado «AO VIVO · %s»)' % (rot, r['selo'], o['hora']))
        if r['seloTitle'] != 'Telemetria ao vivo — atualiza a cada segundo': p.append('%s: a dica do selo diz %r' % (rot, r['seloTitle']))
        if r['reg'] != 'REG. ' + str(r['registro']) or not r['registro']: p.append('%s: o registro diz %r (esperado o do cadastro %r)' % (rot, r['reg'], r['registro']))
        T = r['T']
        esperado = [('SOG', T['sog_nos'] + ' NÓS'), ('PROA', T['proa_graus'] + '°'), ('VENTO', T['vento_verdadeiro_nos'] + ' NÓS'), ('24 V', T['bateria_0_tensao_v'] + ' V'), ('ÁGUA DOCE', T['tanque_agua_pct'] + ' %'),
                    ('DIESEL', T['diesel_litros'] + ' L (' + o['diesel'].split('(')[1])]
        if len(r['faixa']) != 6: p.append('%s: a faixa de baixo tem %d valores (esperado 6): %s' % (rot, len(r['faixa']), r['faixa']))
        for (k, v), txt in zip(esperado, r['faixa']):
            if txt != k + ' ' + v: p.append('%s: a faixa diz %r (esperado %r)' % (rot, txt, k + ' ' + v))
        if r['faixa'][:1] != ['SOG ' + o['sog']] or (len(r['faixa']) == 6 and r['faixa'][5] != 'DIESEL ' + o['diesel']): p.append('%s: SOG ou diesel fora do CONTRATO §1.22 (%s · %s): %s' % (rot, o['sog'], o['diesel'], r['faixa']))
        est = ('%s · %s' % (r['q']['estado'], r['q']['local'])).upper()
        if r['estadoTitle'] != est or r['estado'] != o['estado'] or est != o['estado']: p.append('%s: o estado diz %r (dica %r), esperado o do quadro %r' % (rot, r['estado'], r['estadoTitle'], est))
        if r['horaTxt'] != o['hora'] + ' · AO VIVO' or (r['corteHora'] or 0) > 1: p.append('%s: a hora do rodapé diz %r (cortada em %s px)' % (rot, r['horaTxt'], r['corteHora']))
        if (r['rodLateral'] or 0) > 1: p.append('%s: o rodapé rola para o lado (%s px)' % (rot, r['rodLateral']))
        if re.search(r'54/52|\b848\b|26/09|SOG 0,1', r['texto']): p.append('%s: sobrou leitura do snapshot de 26/09 na tela: %s' % (rot, re.search(r'54/52|\b848\b|26/09|SOG 0,1', r['texto']).group(0)))
    else:
        if r['ledAria'] != 'Telemetria ao vivo — atualiza a cada segundo': p.append('%s: a dica do LED diz %r' % (rot, r['ledAria']))
    eqd = {e['id']: e for e in r['eq']}
    fe = fabs_eletronicos(r['eq'])
    ger = fab_mod(eqd['gerador']['f'], eqd['gerador']['m']); cli = fab_mod(eqd['climatizacao']['f'], eqd['climatizacao']['m']); est_ = fab_mod(eqd['estabilizador']['f'], eqd['estabilizador']['m'])
    if main:
        eqs = [None, '%s · %s h' % (ger, r['T']['gerador_horimetro_h']), cli, est_, ' · '.join(fe)]
        chips = ['%d ATRASADAS' % r['atrasadas'] if r['atrasadas'] else 'EM DIA', chip_equip(r, 'gerador', 'gerador-rotor'), chip_equip(r, 'climatizacao', 'clima-filtro'), chip_equip(r, 'estabilizador', None), chip_equip(r, 'eletronicos', None)]
        if r['T']['gerador_horimetro_h'] + ' h' != o['ger']: p.append('%s: as horas do gerador do quadro são %s (CONTRATO §1.22: %s)' % (rot, r['T']['gerador_horimetro_h'], o['ger']))
        if [c['nome'] for c in r['cartoes']] != NOMES_MAIN: p.append('%s: os cartões são %s' % (rot, [c['nome'] for c in r['cartoes']]))
        for c, e, ch in zip(r['cartoes'], eqs, chips):
            if e is not None and c['eq'] != e: p.append('%s: o cartão %s diz %r (esperado %r)' % (rot, c['nome'], c['eq'], e))
            if c['chip'] != ch: p.append('%s: o chip de %s diz %r (esperado %r)' % (rot, c['nome'], c['chip'], ch))
    else:
        titulos = ['Gerador %s — ligar · desligar · alarmes%s' % (ger, ' · rotor em atraso' if atrasada(r, 'gerador-rotor') is not None else ''),
                   'Climatização %s — ligar · alarme de fluxo · filtros%s' % (cli, ' · filtro em atraso' if atrasada(r, 'clima-filtro') is not None else ''),
                   'Estabilizador %s — ligar antes de sair · desligar ao atracar' % est_, '%s — plotter · piloto · rádio · áudio' % ' · '.join(fe)]
        if [c['aria'] for c in r['cartoes']] != NOMES_H2: p.append('%s: os cartões são %s' % (rot, [c['aria'] for c in r['cartoes']]))
        for c, t in zip(r['cartoes'], titulos):
            if c['title'] != t: p.append('%s: a dica de %s diz %r (esperado %r)' % (rot, c['aria'], c['title'], t))
        esp = '%d ATRASADAS' % r['atrasadas'] if r['atrasadas'] else 'EM DIA'
        if r['consoleChip'] != esp: p.append('%s: o chip do CONSOLE diz %r (esperado %r)' % (rot, r['consoleChip'], esp))
    if re.search(r'NaN|undefined|\[object|Infinity', r['texto']): p.append('%s: NaN, undefined ou [object na tela' % rot)
    if r['lateral'] > 1: p.append('%s: rola para o lado (%d px)' % (rot, r['lateral']))
    return p


def teste_home_leitura(b, tela):
    prob = []
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_tela(b, tela, fixo=fixo)
        prob += problemas_home_leitura(pg.evaluate(LE_HOME), fixo, tela)
        prob += ['%s a %s s: %s' % (tela, fixo, x) for x in problemas_selo(tela, pg.evaluate(CHECA))]   # nenhuma caixa de selo violeta, nada de «DEMO» nem de «é real» fora do capitao-dados.js
        ach = achados_termos(tela, pg.evaluate(LE_TEXTOS))   # a varredura do §3 (texto, title, aria-label, placeholder e alt)
        if ach: prob.append('%s a %s s: termo do §3 na tela: %s' % (tela, fixo, {k: v[:2] for k, v in ach.items()}))
        if erros: prob += ['%s a %s s: %s' % (tela, fixo, e) for e in erros[:2]]
        ctx.close()
    return prob


def teste_home_dados(b, tela):
    """O fabricante e o modelo vêm de D.equipamentos (planta outros nomes: aparecem); a tarefa executada tira o chip de atraso e a contagem do CONSOLE; sem o fabricante, a simulação deixa o cartão sem a palavra
    (nunca «SEM DADOS») e o ramo simulacao false diz «SEM DADOS»."""
    prob = []
    ctx, pg, erros = abre_tela(b, tela, fixo='60', depois=FABRICANTES_FALSOS)
    r = pg.evaluate(LE_HOME)
    prob += ['%s com fabricantes plantados: %s' % (tela, x) for x in problemas_home_leitura(r, '60', tela)]
    txt = r['texto'] + ' ' + ' '.join(c['title'] for c in r['cartoes'])
    for z in ('Zyxgerador Mod9', 'Zyxclima Mod9', 'Zyxestab Mod9'):
        if z not in txt: prob.append('%s: o fabricante e o modelo plantados (%s) não aparecem' % (tela, z))
    if 'Zyxeletro · Zyxaudio · Zyxvhf' not in txt: prob.append('%s: os fabricantes dos eletrônicos plantados não aparecem (esperado «Zyxeletro · Zyxaudio · Zyxvhf»)' % tela)
    if re.search(r'Onan|Webasto|Seakeeper|Garmin|Icom|Fusion', txt): prob.append('%s: sobrou fabricante fixo: %s' % (tela, re.search(r'Onan|Webasto|Seakeeper|Garmin|Icom|Fusion', txt).group(0)))
    ctx.close()
    ctx, pg, erros = abre_tela(b, tela, fixo='60')   # a tarefa do rotor e a do filtro executadas (Executado): saem do atraso
    r0 = pg.evaluate(LE_HOME)
    ctx.close()
    ex = json.dumps({'gerador-rotor': {'iso': '2026-11-10T09:00:00-03:00', 't': '09:00', 'sim': True}})
    ctx, pg, erros = abre_tela(b, tela, fixo='60', ls={'capitao.executado.v1': ex})
    r1 = pg.evaluate(LE_HOME)
    prob += ['%s com o rotor executado: %s' % (tela, x) for x in problemas_home_leitura(r1, '60', tela)]
    if r0['atrasadas'] != r1['atrasadas'] + 1: prob.append('%s: executar o rotor devia tirar 1 das atrasadas (%d → %d)' % (tela, r0['atrasadas'], r1['atrasadas']))
    if any('ROTOR' in c['chip'] or 'rotor em atraso' in c['title'] for c in r1['cartoes']): prob.append('%s: o cartão do gerador ainda mostra o rotor em atraso depois do Executado' % tela)
    ctx.close()
    ctx, pg, erros = abre_tela(b, tela, fixo='60', depois=SEM_FABRICANTE)
    r = pg.evaluate(LE_HOME)
    if re.search(r'SEM DADOS|SEM LEITURA', r['texto'] + ' '.join(c['title'] for c in r['cartoes'])): prob.append('%s (simulação, sem fabricante): rótulo SEM DADOS na tela' % tela)
    ctx.close()
    ctx, pg, erros = abre_tela(b, tela, fixo=None, depois=SEM_FABRICANTE + 'window.CapitaoDados.simulacao = false;')
    r = pg.evaluate(LE_HOME)
    if 'SEM DADOS' not in r['texto'] + ' '.join(c['title'] for c in r['cartoes']): prob.append('%s (simulacao false, sem fabricante): devia dizer SEM DADOS (a regra do modo real)' % tela)
    ctx.close()
    return prob


def teste_home_vivo(b, tela):
    """Sem congelar o replay a Home anda sozinha: a hora do selo (Main) e a da faixa mudam em 1,5 s; a H2 não tem texto que ande e não se redesenha à toa."""
    prob = []
    ctx, pg, erros = abre_tela(b, tela, fixo=None)
    if tela == 'Main':
        mudou = False
        for _ in range(3):
            a = pg.evaluate(LE_HOME); pg.wait_for_timeout(1500); c = pg.evaluate(LE_HOME)
            if not re.fullmatch(r'AO VIVO · \d\d:\d\d:\d\d', c['selo'] or ''): prob.append('Main livre: o selo diz %r (esperado «AO VIVO · hh:mm:ss»)' % c['selo']); break
            if a['selo'] != c['selo'] and c['selo'] == 'AO VIVO · ' + c['hora'] and c['horaTxt'] == c['hora'] + ' · AO VIVO' and a['faixa'][0] is not None: mudou = True; break
        if not mudou: prob.append('Main livre: a hora do selo não mudou em 1,5 s (3 tentativas): a tela não assina o capitao-telemetria')
    else:
        r = pg.evaluate(LE_HOME)
        if cor_do_selo(r['ledCor']) != 'verde': prob.append('H2 livre: o LED não é verde (%s)' % r['ledCor'])
    if erros: prob += ['%s livre: %s' % (tela, e) for e in erros[:2]]
    ctx.close()
    return prob


def teste_home_real(b, tela):
    """Com simulacao false: o replay não anda, a leitura vem da última leitura salva (26/09 10:12) com «ÚLTIMA LEITURA», o LED é âmbar e parado, sem NaN, undefined nem AO VIVO."""
    prob = []
    ctx, pg, erros = abre_tela(b, tela, fixo=None, depois='window.CapitaoDados.simulacao = false;')
    r = pg.evaluate(LE_HOME)
    rot = '%s com simulacao false' % tela
    if r['fonte'] != 'snapshot': prob.append('%s: a fonte do instante é %s (esperado a última leitura salva)' % (rot, r['fonte']))
    if cor_do_selo(r['ledCor']) != 'amarelo' or 'capVivo' in (r['ledAnim'] or ''): prob.append('%s: o LED é %s e a animação %r: esperado âmbar e parado' % (rot, cor_do_selo(r['ledCor']), r['ledAnim']))
    if re.search(r'NaN|undefined|\[object|Infinity|AO VIVO', r['texto']): prob.append('%s: NaN, undefined, [object ou AO VIVO na tela: %s' % (rot, re.search(r'NaN|undefined|\[object|Infinity|AO VIVO', r['texto']).group(0)))
    if tela == 'Main':
        if r['selo'] != 'ÚLTIMA LEITURA · 26/09 10:12' or r['seloTitle'] != 'Sem leitura ao vivo agora — mostrando a última leitura salva': prob.append('%s: o selo diz %r (dica %r)' % (rot, r['selo'], r['seloTitle']))
        if r['horaTxt'] != r['horaTxt'].split(' · ')[0] + ' · ÚLTIMA LEITURA' or not (r['estado'] or '').startswith('FUNDEADO'): prob.append('%s: o rodapé diz %r · %r (esperado a hora com «· ÚLTIMA LEITURA» e o estado Fundeado)' % (rot, r['horaTxt'], r['estado']))
        if len(r['faixa']) != 6 or any(re.search(r'—$', f) for f in r['faixa']): prob.append('%s: a faixa de baixo ficou incompleta: %s' % (rot, r['faixa']))
        if r['faixa'][:1] != ['SOG 0,1 NÓS']: prob.append('%s: o SOG da última leitura é %s (esperado 0,1 nó)' % (rot, r['faixa'][:1]))
    else:
        if r['ledAria'] != 'Sem leitura ao vivo agora — mostrando a última leitura salva': prob.append('%s: a dica do LED diz %r' % (rot, r['ledAria']))
    if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
    ctx.close()
    return prob


def teste_home_ouvintes(b, tela):
    """Sem vazamento de listener: a tela liga 5 ouvintes (telemetria, virada do dia, botão de resposta, hash e ENCERRAR) e o componentWillUnmount tira os 5; religar volta aos mesmos números, em 3 voltas."""
    prob = []
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, service_workers='block')
    ctx.add_init_script(SESSAO + ";localStorage.setItem('capitao.replay.fixo', '60');")
    ctx.add_init_script(OUVINTES_JS)
    aplica_mut(ctx)
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
    pg.goto(BASE + tela + '.dc.html', wait_until='load')
    pg.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
    pg.wait_for_timeout(1300)
    r = pg.evaluate("""(ev) => { const hosts = [...document.querySelectorAll('.sc-host')], n = () => ev.map((e) => window.__ev(e));
      let L = null; for (const hs of hosts) { const k = Object.keys(hs).find((x) => x.startsWith('__reactFiber')); let f = hs[k]; while (f && !(f.stateNode && f.stateNode.logic && f.stateNode.logic.ask)) f = f.return; if (f) { L = f.stateNode.logic; break; } }
      if (!L) return { achou: false };
      const n0 = n(), voltas = []; for (let i = 0; i < 3; i++) { L.componentWillUnmount(); const fora = n(); L.componentDidMount(); voltas.push({ fora, dentro: n() }); }
      return { achou: true, n0, voltas }; }""", EVENTOS_HOME)
    if not r['achou']: prob.append('%s: não achei a lógica da tela para desmontar' % tela)
    else:
        for i, v in enumerate(r['voltas']):
            queda = [a - c for a, c in zip(r['n0'], v['fora'])]
            if queda != [1, 1, 1, 1, 1]: prob.append('%s volta %d: o componentWillUnmount tira %s ouvintes de %s (esperado 1 de cada)' % (tela, i + 1, queda, EVENTOS_HOME))
            if v['dentro'] != r['n0']: prob.append('%s volta %d: religar deixa %s ouvintes (esperado %s: vazou ou duplicou)' % (tela, i + 1, v['dentro'], r['n0']))
    if erros: prob += erros[:2]
    ctx.close()
    return prob


# ——— o chat completo ———
def liga_ia(ctx, estado):
    """O Worker da IA de mentira: guarda cada corpo em estado['pedidos'] e responde estado['texto'] (422 sem ficha, trecho nem leitura, como o de verdade)."""
    def rota(route):
        req = route.request
        cab = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type, X-Capitao-Chave', 'Access-Control-Allow-Methods': 'POST, OPTIONS'}
        if req.method == 'OPTIONS': return route.fulfill(status=204, headers=cab)
        corpo = json.loads(req.post_data or '{}')
        estado['pedidos'].append(corpo)
        if not (corpo.get('ficha') or corpo.get('trechos') or corpo.get('contexto')): return route.fulfill(status=422, content_type='application/json', headers=cab, body='{"erro":"sem fontes","motivo":"sem_fontes"}')
        return route.fulfill(status=200, content_type='application/json', headers=cab, body=json.dumps({'texto': estado['texto'] + '\nFonte: ficha de bordo', 'provedor': 'Workers AI', 'modelo': 'teste', 'parou': 'fim'}))
    ctx.route(URL_IA.rstrip('/') + '**', rota)


def abre_home(b, tela, fixo='60', ia=True, ls=None, depois='', texto=None, hash_=''):
    est = {'pedidos': [], 'texto': texto or TEXTO_IA_HOME}
    ls = dict(ls or {})
    if ia: ls['capitao.ia.chave.v1'] = 'chave-de-teste'
    ctx, pg, erros = abre_tela(b, tela, fixo=fixo, ls=ls, depois=depois, hash_=hash_)
    if ia: liga_ia(ctx, est)
    return ctx, pg, erros, est


LE_MSGS = """() => [...document.querySelectorAll('[data-home=msg]')].map((m) => ({ papel: m.dataset.papel, txt: m.innerText.replace(/\\s+/g, ' ').trim(), acoes: [...m.querySelectorAll('[data-home=acao]')].map((a) => ({ l: a.innerText.replace(/[›\\s]+$/, '').trim(), href: a.getAttribute('href') })) }))"""
LE_ESTADO_HOME = """() => ({ emerg: window.CapitaoEmergencia.valendo(), ate: sessionStorage.getItem('capitao.emergenciaAte'), url: location.href, diario: JSON.parse(localStorage.getItem('capitao.diario.v1') || '[]'),
  alarmes: JSON.parse(localStorage.getItem('capitao.alarmes.v1') || '[]'), tarefas: JSON.parse(localStorage.getItem('capitao.tarefas.v1') || '[]'), anexo: !!document.querySelector('button[aria-label="Remover anexo"]'), digitado: (document.querySelector('#pergunta, #pergunta-m') || {}).value,
  limpou: window.__limpou || 0, resumo: window.CapitaoBrain.resumoAgora() }) """


def pergunta_home(pg, tela, q, espera=True):
    """Digita no campo e envia (Enter); espera a resposta e devolve as mensagens (papel, texto, ações)."""
    campo = CAMPO_HOME[tela]
    n0 = pg.evaluate("() => document.querySelectorAll('[data-home=msg][data-papel=bot]').length")
    pg.fill(campo, q); pg.press(campo, 'Enter')
    if espera:
        try: pg.wait_for_function("(n) => document.querySelectorAll('[data-home=msg][data-papel=bot]').length > n && !document.querySelector('[data-capitao-pensando]')", arg=n0, timeout=20000)
        except Exception: pass   # (a tela com defeito pode não responder: quem chama acusa pelo conteúdo, não por um erro do teste)
        pg.wait_for_timeout(250)
    return pg.evaluate(LE_MSGS)


def clica_acao(pg, texto, esperar=True):
    """Toca no botão de uma resposta (o link #capitao-prop-… ou #capitao-relato-…); o link não navega e vira a pergunta digitada."""
    n0 = pg.evaluate("() => document.querySelectorAll('[data-home=msg]').length")
    pg.locator('[data-home=acao]:has-text("%s")' % texto).last.click()
    if esperar:
        try: pg.wait_for_function("(n) => document.querySelectorAll('[data-home=msg]').length >= n + 2 && !document.querySelector('[data-capitao-pensando]')", arg=n0, timeout=6000)
        except Exception: pass
    pg.wait_for_timeout(300)
    return pg.evaluate(LE_MSGS)


def teste_home_ia(b, tela):
    """A IA a partir da Home: o 3º argumento é a leitura de agora (B.resumoAgora, o instante da resposta, sem coordenadas), o histórico vem de B.historicoIA (sem coordenadas e sem a emergência), o texto que vai
    é o ditado corrigido (B.corrigeVoz) e a resposta da IA é contada ao cérebro (B.conversa): «o gerador» depois de «Qual equipamento você quer ligar?» continua o «como ligar?»."""
    prob = []
    rot = tela
    COORD = "Estamos em 26°59,58'S 048°36,84'W, perto da Ilha das Cabras."
    ctx, pg, erros, est = abre_home(b, tela, texto=COORD)
    m = pergunta_home(pg, tela, PEDIDO_IA)
    if len(est['pedidos']) != 1: prob.append('%s: a pergunta sem resposta pronta devia fazer 1 pedido à IA (fez %d)' % (rot, len(est['pedidos'])))
    else:
        ped, esperado = est['pedidos'][0], pg.evaluate('() => window.CapitaoBrain.resumoAgora()')
        ctxt = ped.get('contexto') or ''
        if not ctxt or ctxt != esperado: prob.append('%s: o 3º argumento (contexto) é %r, esperado a leitura de agora do cérebro %r' % (rot, ctxt[:80], esperado[:80]))
        if len(ctxt) > 300 or confere.R_COORD.search(ctxt) or not re.search(r'SOG \d+,\d nós', ctxt) or '12:01:00' not in ctxt: prob.append('%s: o contexto não é o resumo do instante (≤ 300 letras, sem coordenada, com SOG e a hora 12:01:00): %r' % (rot, ctxt[:200]))
        if ped.get('historico') != []: prob.append('%s: o histórico da 1ª pergunta devia ser vazio: %r' % (rot, ped.get('historico')))
    m = pergunta_home(pg, tela, 'qual é a diferença entre barlavento e sotavento?')
    if len(est['pedidos']) != 2: prob.append('%s: a 2ª pergunta de náutica geral devia fazer o 2º pedido (fez %d)' % (rot, len(est['pedidos'])))
    else:
        h = est['pedidos'][1].get('historico') or []
        if [x.get('papel') for x in h] != ['usuario', 'capitao'] or h[0].get('texto') != PEDIDO_IA: prob.append('%s: o histórico do 2º pedido devia ser a pergunta e a resposta de antes: %r' % (rot, h))
        if h and (confere.R_COORD.search(h[-1].get('texto', '')) or '26°' in h[-1].get('texto', '')): prob.append('%s: coordenada no histórico que vai à IA (o cérebro a corta, B.historicoIA): %r' % (rot, h[-1].get('texto')))
    ctx.close()
    # a emergência nunca vai à IA, nem depois da janela: o histórico do pedido não leva o SOS nem a resposta dele
    ctx, pg, erros, est = abre_home(b, tela)
    pergunta_home(pg, tela, 'mayday, homem ao mar')
    pg.evaluate("() => window.CapitaoEmergencia.marca(Date.now() - 1000)")   # a janela venceu (a marca guarda também em memória: só o marca() com um fim no passado a encerra)
    if pg.evaluate(LE_ESTADO_HOME)['emerg']: prob.append('%s: o teste não vale (a janela não venceu)' % rot)
    pergunta_home(pg, tela, PEDIDO_IA)
    if len(est['pedidos']) != 1: prob.append('%s: depois da janela a pergunta devia ir à IA (pedidos %d)' % (rot, len(est['pedidos'])))
    else:
        txt = json.dumps(est['pedidos'][0].get('historico'), ensure_ascii=False)
        if re.search(r'mayday|Emergência|homem ao mar|canal 16', txt, re.I): prob.append('%s: o histórico que vai à IA leva a emergência: %s' % (rot, txt[:200]))
    ctx.close()
    # o ditado corrigido vai à IA
    ctx, pg, erros, est = abre_home(b, tela)
    pergunta_home(pg, tela, 'como ligar o siker?')
    if len(est['pedidos']) != 1 or est['pedidos'][0].get('pergunta') != 'como ligar o Seakeeper?': prob.append('%s: o texto que vai à IA devia ser o corrigido «como ligar o Seakeeper?»: %r' % (rot, [x.get('pergunta') for x in est['pedidos']]))
    ctx.close()
    # a IA pergunta, a pessoa responde só o equipamento: o cérebro precisa saber que a IA perguntou
    ctx, pg, erros, est = abre_home(b, tela, texto='Qual equipamento você quer ligar?')
    pergunta_home(pg, tela, 'como ligar?')
    pg.evaluate("() => localStorage.removeItem('capitao.ia.chave.v1')")
    m = pergunta_home(pg, tela, 'o gerador')
    t = m[-1]['txt']
    if 'PARTIDA até o motor pegar' not in t: prob.append('%s: «o gerador» depois da pergunta da IA devia continuar o «como ligar?» (os passos de partida): %r' % (rot, t[:200]))
    ctx.close()
    ctx, pg, erros, est = abre_home(b, tela, texto='Qual equipamento você quer ligar?')
    pergunta_home(pg, tela, 'como ligar?')
    pg.click('[aria-label="Nova conversa"]'); pg.wait_for_timeout(300)
    pg.evaluate("() => localStorage.removeItem('capitao.ia.chave.v1')")
    m = pergunta_home(pg, tela, 'o gerador')
    if 'PARTIDA até o motor pegar' in m[-1]['txt']: prob.append('%s: depois do NOVA o «o gerador» não devia continuar a pergunta de antes' % rot)
    ctx.close()
    return prob


def teste_home_janela(b, tela):
    """A janela de conversa em emergência: o SOS a marca (CapitaoEmergencia); dentro dela a posição vira «LEIA NO PLOTTER» e nada vai à IA; o NOVA e o ENCERRAR zeram a marca e o contexto do cérebro (limpaConversa)."""
    prob = []
    rot = tela
    SPY = "window.__limpou = 0; (() => { const B = window.CapitaoBrain; const f = B.limpaConversa; B.limpaConversa = function () { window.__limpou++; return f.apply(this, arguments); }; })()"
    ctx, pg, erros, est = abre_home(b, tela)
    pg.evaluate(SPY)
    s0 = pg.evaluate(LE_ESTADO_HOME)
    pergunta_home(pg, tela, 'qual a nossa posição?')
    if 'LEIA NO PLOTTER' in pg.evaluate(LE_MSGS)[-1]['txt'] or s0['emerg']: prob.append('%s: fora da janela a posição devia vir do quadro' % rot)
    m = pergunta_home(pg, tela, 'mayday, homem ao mar')
    s = pg.evaluate(LE_ESTADO_HOME)
    if not s['emerg'] or not s['ate']: prob.append('%s: a resposta do SOS não marcou a janela (valendo %r, sessionStorage %r)' % (rot, s['emerg'], s['ate']))
    if s['diario']: prob.append('%s: a pergunta de emergência gravou no diário: %s' % (rot, s['diario']))
    antes = len(est['pedidos'])
    m = pergunta_home(pg, tela, 'qual a nossa posição?')
    t = m[-1]['txt']
    if 'LEIA NO PLOTTER' not in t or 'Barra Sul' in t or confere.R_COORD.search(t): prob.append('%s: dentro da janela a posição devia vir como «LEIA NO PLOTTER», sem o ponto da rota: %r' % (rot, t[:200]))
    m = pergunta_home(pg, tela, PEDIDO_IA)
    if len(est['pedidos']) != antes: prob.append('%s: dentro da janela a pergunta foi à IA (%d pedidos)' % (rot, len(est['pedidos']) - antes))
    if 'LEIA NO PLOTTER' not in m[-1]['txt']: prob.append('%s: dentro da janela o fallback devia trazer «LEIA NO PLOTTER»: %r' % (rot, m[-1]['txt'][:200]))
    pg.click('[aria-label="Nova conversa"]'); pg.wait_for_timeout(300)
    s = pg.evaluate(LE_ESTADO_HOME)
    if s['emerg'] or s['ate'] or s['limpou'] != 1: prob.append('%s: o NOVA devia zerar a marca (valendo %r, sessionStorage %r) e chamar B.limpaConversa 1 vez (chamou %d)' % (rot, s['emerg'], s['ate'], s['limpou']))
    m = pergunta_home(pg, tela, 'qual a nossa posição?')
    if 'LEIA NO PLOTTER' in m[-1]['txt']: prob.append('%s: depois do NOVA a posição devia voltar do quadro' % rot)
    pergunta_home(pg, tela, 'mayday, homem ao mar')
    if not pg.evaluate(LE_ESTADO_HOME)['emerg']: prob.append('%s: o 2º SOS não marcou a janela' % rot)
    pg.evaluate("() => window.dispatchEvent(new CustomEvent('capitao-voz-encerrar'))"); pg.wait_for_timeout(300)
    s = pg.evaluate(LE_ESTADO_HOME)
    if s['emerg'] or s['ate'] or s['limpou'] != 2: prob.append('%s: o ENCERRAR devia zerar a marca (valendo %r, sessionStorage %r) e chamar B.limpaConversa (chamadas %d, esperado 2)' % (rot, s['emerg'], s['ate'], s['limpou']))
    if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
    ctx.close()
    # com a janela já marcada ao abrir (outra tela de conversa a marcou), a pergunta de rotina também não vai à IA
    ctx, pg, erros, est = abre_home(b, tela, depois=JANELA_VALE)
    if not pg.evaluate(LE_ESTADO_HOME)['emerg']: prob.append('%s: o teste não vale (a janela não estava marcada)' % rot)
    m = pergunta_home(pg, tela, 'qual a nossa posição?')
    if 'LEIA NO PLOTTER' not in m[-1]['txt'] or 'Barra Sul' in m[-1]['txt']: prob.append('%s: com a janela marcada por outra tela a posição devia vir como «LEIA NO PLOTTER»: %r' % (rot, m[-1]['txt'][:160]))
    pergunta_home(pg, tela, PEDIDO_IA)
    if est['pedidos']: prob.append('%s: com a janela marcada por outra tela a pergunta foi à IA' % rot)
    ctx.close()
    return prob


def teste_home_botoes(b, tela):
    """Os botões das propostas (os links #capitao-relato-… e #capitao-prop-…): o toque vira a pergunta digitada (a bolha do usuário aparece), o link não navega, o cérebro grava só o que o botão pede (Registrar = 1 linha;
    Não registrar = 0; Confirmar o alarme = 1 regra; Desfazer a apaga; Recusar não grava), «O que verificar?» vai à IA com o relato, e o toque não leva o anexo nem apaga o que está sendo digitado."""
    prob = []
    rot = tela
    ctx, pg, erros, est = abre_home(b, tela)
    m = pergunta_home(pg, tela, RELATO_DEFEITO)
    ls = [a['l'] for a in m[-1]['acoes']]
    for t in ('Registrar no diário', 'Não registrar', 'O que verificar?'):
        if t not in ls: prob.append('%s: a proposta do relato devia ter o botão «%s» (tem %s)' % (rot, t, ls))
    url0 = pg.evaluate("() => location.href")
    m = clica_acao(pg, 'Não registrar')
    s = pg.evaluate(LE_ESTADO_HOME)
    if m[-2]['papel'] != 'user' or 'não registrar o relato' not in m[-2]['txt'].lower(): prob.append('%s: o toque em «Não registrar» devia aparecer como a pergunta do usuário: %r' % (rot, m[-2]['txt'][:80]))
    if s['diario'] or s['url'] != url0: prob.append('%s: «Não registrar» gravou no diário ou navegou (%s · %s)' % (rot, s['diario'], s['url']))
    m = pergunta_home(pg, tela, RELATO_DEFEITO)
    m = clica_acao(pg, 'Registrar no diário')
    s = pg.evaluate(LE_ESTADO_HOME)
    if len(s['diario']) != 1 or s['diario'][0].get('sim') is not True or 'desligou sozinho' not in s['diario'][0].get('t', ''): prob.append('%s: «Registrar no diário» devia gravar 1 linha com o relato e sim: true: %s' % (rot, s['diario']))
    if s['url'] != url0: prob.append('%s: o botão navegou (%s)' % (rot, s['url']))
    antes = len(est['pedidos'])
    m = pergunta_home(pg, tela, RELATO_DEFEITO)
    m = clica_acao(pg, 'O que verificar?')
    ult = est['pedidos'][-1] if est['pedidos'] else {}
    if len(est['pedidos']) != antes + 1 or not (ult.get('pergunta') or '').startswith('O que verificar'): prob.append('%s: «O que verificar?» devia mandar a pergunta pronta do relato à IA (pedidos %d → %d): %r' % (rot, antes, len(est['pedidos']), (ult.get('pergunta') or '')[:60]))
    elif not ult.get('contexto') or confere.R_COORD.search(ult['pergunta']): prob.append('%s: o pedido do «O que verificar?» sem a leitura de agora ou com coordenada' % rot)
    if len(pg.evaluate(LE_ESTADO_HOME)['diario']) != 1: prob.append('%s: «O que verificar?» gravou no diário' % rot)
    ctx.close()
    # a proposta do alarme: Confirmar grava a regra, Recusar não grava; a da agenda: Confirmar grava a tarefa e o Desfazer a tira
    ctx, pg, erros, est = abre_home(b, tela)
    pergunta_home(pg, tela, 'me avise se a pressão do óleo do BB cair abaixo de 2 bar')
    m = clica_acao(pg, 'Confirmar')
    s = pg.evaluate(LE_ESTADO_HOME)
    if [a.get('id') for a in s['alarmes'] if not a.get('acao')] != ['usr_1']: prob.append('%s: «Confirmar» devia gravar a regra usr_1: %s' % (rot, s['alarmes']))
    ctx.close()
    ctx, pg, erros, est = abre_home(b, tela)
    pergunta_home(pg, tela, 'me avise se a pressão do óleo do BB cair abaixo de 2 bar')
    clica_acao(pg, 'Recusar')
    if pg.evaluate(LE_ESTADO_HOME)['alarmes']: prob.append('%s: «Recusar» gravou o alarme' % rot)
    ctx.close()
    ctx, pg, erros, est = abre_home(b, tela)
    pergunta_home(pg, tela, 'agendar revisão do gerador para 15/11')
    if pg.evaluate(LE_ESTADO_HOME)['tarefas']: prob.append('%s: a proposta da tarefa gravou antes do Confirmar' % rot)
    m = clica_acao(pg, 'Confirmar')
    s = pg.evaluate(LE_ESTADO_HOME)
    if len(s['tarefas']) != 1 or not s['tarefas'][0]['vence'].endswith('-11-15'): prob.append('%s: «Confirmar» devia gravar a tarefa (vence 15/11): %s' % (rot, s['tarefas']))
    if 'Desfazer' not in [a['l'] for a in m[-1]['acoes']]: prob.append('%s: depois do Confirmar devia haver o botão «Desfazer» (tem %s)' % (rot, [a['l'] for a in m[-1]['acoes']]))
    else:
        clica_acao(pg, 'Desfazer')
        if pg.evaluate(LE_ESTADO_HOME)['tarefas']: prob.append('%s: o «Desfazer» devia tirar a tarefa da agenda da equipe' % rot)
    ctx.close()
    # o botão não leva o anexo nem apaga o que está sendo digitado
    ctx, pg, erros, est = abre_home(b, tela)
    pergunta_home(pg, tela, RELATO_DEFEITO)
    pg.set_input_files('input[type=file][accept="image/*"]', {'name': 'etiqueta.png', 'mimeType': 'image/png', 'buffer': PNG_1X1})
    pg.wait_for_timeout(300)
    pg.fill(CAMPO_HOME[tela], 'rascunho da próxima pergunta')
    if not pg.evaluate(LE_ESTADO_HOME)['anexo']: prob.append('%s: o teste não vale (o anexo não ficou pendente)' % rot)
    clica_acao(pg, 'Não registrar')
    s = pg.evaluate(LE_ESTADO_HOME)
    if not s['anexo']: prob.append('%s: o toque no botão da resposta levou o anexo pendente' % rot)
    if s['digitado'] != 'rascunho da próxima pergunta': prob.append('%s: o toque no botão da resposta apagou o que estava sendo digitado (%r)' % (rot, s['digitado']))
    if s['diario']: prob.append('%s: o anexo ou o botão gravou no diário: %s' % (rot, s['diario']))
    if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
    ctx.close()
    return prob


def teste_home_codigo():
    prob = []
    def le_(a):
        t = open(os.path.join(RAIZ, a), encoding='utf-8', newline='').read()
        for velho, novo in MUT_ARQ.get(a, []): t = t.replace(velho, novo, 1)
        return t
    GEOM = re.compile(r'<(?:svg|path|circle|line|rect|ellipse|polyline|polygon|g)\b[^>]*\b(?:d|x|y|x1|x2|y1|y2|cx|cy|r|rx|ry|width|height|viewBox|points|transform)="[^"]*\{\{')
    for a in ('Main.dc.html', 'H2-Home-Mobile.dc.html'):
        h = le_(a)
        n = a.split('.')[0]
        cod = re.sub(r'//[^\n]*', '', h)
        mont, desm = h.find('componentDidMount'), h.find('componentWillUnmount')
        for ev in ('capitao-telemetria', 'capitao-rebase', 'capitao-chat-pergunta'):
            if "'%s'" % ev not in h[mont:desm] or "'%s'" % ev not in h[desm:desm + 700]: prob.append('%s: não assina o %s no componentDidMount e remove no componentWillUnmount' % (n, ev))
        if h.count('setInterval') != 1: prob.append('%s: setInterval a mais (%d; só o do whenBrain)' % (n, h.count('setInterval')))
        if h.count('if (document.hidden) return;') < (1 if n == 'Main' else 2): prob.append('%s: o tique da telemetria (e a virada do dia) não pausa com document.hidden' % n)
        if re.search(r'D\.demo|\.demo\b|DEMO|D\.aviso|D\.snapshot|\.snapshot\b|demoTip', cod): prob.append('%s: lê D.demo, D.aviso ou D.snapshot (ou escreve DEMO) no código' % n)
        if MARCAS_FIXAS.search(cod): prob.append('%s: fabricante fixo no código: %s' % (n, MARCAS_FIXAS.search(cod).group(0)))
        for l in cod.split('\n'):   # SEM DADOS / SEM LEITURA só no ramo simulacao:false (falta() ou sim ?)
            if re.search(r'SEM (?:DADOS|LEITURA)', l) and not re.search(r'falta\(|sim \?', l): prob.append('%s: rótulo fora do ramo simulacao false: %s' % (n, l.strip()[:100]))
        if re.search(r'Não consegui responder agora|Fonte: nenhuma', cod): prob.append('%s: o texto de erro ao montar a resposta ainda leva o rótulo' % n)
        if 'B.resumoAgora(a, { emergencia: emg })' not in h or re.search(r"B\.buscaBase\(qc, 3\), ''", h): prob.append('%s: o 3º argumento da IA não é B.resumoAgora(a)' % n)
        if 'B.historicoIA(' not in h or re.search(r'slice\(-6\)', cod): prob.append('%s: o histórico não vem só de B.historicoIA (ou a tela corta as 6 últimas)' % n)
        if 'B.corrigeVoz(q)' not in h or 'B.conversa(qc, r.text)' not in h: prob.append('%s: falta o B.corrigeVoz no texto da IA ou o B.conversa depois da resposta dela' % n)
        if h.count('limpaContexto()') < 3 or 'B.limpaConversa()' not in h or 'E.zera()' not in h: prob.append('%s: o NOVA e o ENCERRAR não zeram o contexto e a marca da janela (limpaContexto)' % n)
        if 'emergencia: emg' not in h or 'B.pedeIA(a, qc, { emergencia: emg })' not in h or "EM.marca()" not in h or 'a.abreJanela === true' not in h: prob.append('%s: a janela de conversa em emergência não é passada ao cérebro ou não é marcada' % n)
        if "this.ask(d.q, null, 'botao')" not in h: prob.append('%s: o botão de uma resposta não vira a pergunta (capitao-chat-pergunta → ask)' % n)
        if re.search(r'location\s*\.\s*(href|assign|replace|reload)|window\s*\.\s*open|history\s*\.\s*(push|replace)State', cod): prob.append('%s: troca de tela ou abre janela sozinha' % n)
        if GEOM.search(h): prob.append('%s: {{…}} em atributo geométrico de SVG' % n)
    return prob


def teste_h3(b, tela):
    """H3: nenhum rótulo (nem com D.demo ligado: o « · DEMO» do resumo só valia com a flag), o atalho para o mapa de sensores, os checklists guiados e o FAQ dos equipamentos com os destinos da plataforma da tela (web ou app) que existem."""
    prob = []
    web = tela.endswith('-Web')
    ctx, pg, erros = abre_tela(b, tela, fixo='60', depois='window.CapitaoDados.demo = true;')
    r = pg.evaluate("""() => ({ texto: document.body.innerText, a: [...document.querySelectorAll('[data-h3^=tela-]')].map((e) => ({ id: e.dataset.h3, href: e.getAttribute('href'), txt: e.innerText.replace(/\\s+/g, ' ').trim(), h: e.offsetHeight })),
      lateral: document.documentElement.scrollWidth - document.documentElement.clientWidth })""")
    if re.search(r'\bDEMO\b|SEM DADOS|SEM LEITURA|snapshot|fict[ií]ci', r['texto'], re.I): prob.append('%s: rótulo na tela: %s' % (tela, re.search(r'\bDEMO\b|SEM DADOS|SEM LEITURA|snapshot|fict[ií]ci', r['texto'], re.I).group(0)))
    # (P4H) o FAQ dos equipamentos (F6) entrou no quadro «Abrem direto», como a P4G deixou combinado
    esperado = {'tela-sensores': 'A4-Sensores-Web.dc.html' if web else 'A5-Sensores-Mobile.dc.html', 'tela-checklist': 'C4-Checklist-Web.dc.html' if web else 'C4-Checklist-Mobile.dc.html',
                'tela-faq': 'F6-FAQ-Equipamentos-Web.dc.html' if web else 'F6-FAQ-Equipamentos.dc.html'}
    if {x['id']: x['href'] for x in r['a']} != esperado: prob.append('%s: os atalhos das telas novas são %s (esperado %s)' % (tela, {x['id']: x['href'] for x in r['a']}, esperado))
    sw = open(os.path.join(RAIZ, 'sw.js'), encoding='utf-8').read()
    for x in r['a']:
        if not os.path.exists(os.path.join(RAIZ, x['href'])) or ("'%s'" % x['href'].replace('.dc.html', '')) not in sw: prob.append('%s: o destino %s não existe ou não está no TELAS do sw.js' % (tela, x['href']))
        if x['h'] < 43.5: prob.append('%s: o atalho %s tem %.0f px de altura (< 44)' % (tela, x['id'], x['h']))
    if r['lateral'] > 1: prob.append('%s: rola para o lado (%d px)' % (tela, r['lateral']))
    if erros: prob += ['%s: %s' % (tela, e) for e in erros[:2]]
    ctx.close()
    return prob


def p4g_conferencias(b, lista):
    """[(nome, problemas)] das conferências da P4G para as telas da rodada."""
    out = []
    if any(t in lista for t in TELAS_HOME): out.append(('código da Main e da H2', teste_home_codigo()))
    for tela in [t for t in TELAS_HOME if t in lista]:
        out.append((tela + ' · a leitura de agora a 60 e 105 s: selo, faixa, estado, cartões e prazos', teste_home_leitura(b, tela)))
        out.append((tela + ' · fabricante e modelo de D.equipamentos, Executado e o ramo sem fabricante', teste_home_dados(b, tela)))
        out.append((tela + ' · anda sozinha sem congelar o replay', teste_home_vivo(b, tela)))
        out.append((tela + ' · simulacao false: a última leitura salva', teste_home_real(b, tela)))
        out.append((tela + ' · os ouvintes: nenhum vazamento em 3 voltas de desmontar e montar', teste_home_ouvintes(b, tela)))
        out.append((tela + ' · a IA: leitura de agora, histórico do cérebro, ditado corrigido e a conversa', teste_home_ia(b, tela)))
        out.append((tela + ' · a janela de conversa em emergência, o NOVA e o ENCERRAR', teste_home_janela(b, tela)))
        out.append((tela + ' · os botões das propostas e do «O que verificar?»', teste_home_botoes(b, tela)))
    for tela in [t for t in TELAS_H3 if t in lista]:
        out.append((tela + ' · sem rótulo e com o atalho das telas novas', teste_h3(b, tela)))
    return out


MUTANTES_P4G = [
    # —— Main ——
    ('o diesel da faixa da Main de volta no snapshot (54/52)', 'Main.dc.html', [("litros === null || litros === undefined ? falta('SEM LEITURA') : litros + ' L' + (pct ? ' (' + pct + ' %)' : '') }] };", "'54/52' }] };")], 'leitura'),
    ('a Main sem a hora do quadro no selo (SNAPSHOT fixo)', 'Main.dc.html', [("liveLabel: L.selo,", "liveLabel: 'SNAPSHOT · 26/09 10:12',")], 'leitura'),
    ('o estado da faixa da Main fixo no snapshot', 'Main.dc.html', [("faixaEstado: (L.estado + (L.local ? ' · ' + L.local.replace(/^enseada de /i, '') : '')).toUpperCase(),", "faixaEstado: 'FUNDEADO · ENSEADA DE BALNEÁRIO CAMBORIÚ',")], 'leitura'),
    ('a hora do rodapé da Main sem o «· AO VIVO»', 'Main.dc.html', [("faixaHora: L.hora + (L.vivo ? ' · AO VIVO' : ' · ÚLTIMA LEITURA'),", "faixaHora: L.hora,")], 'leitura'),
    ('o LED da Main de volta no ciano que não diz a origem (sem verde)', 'Main.dc.html', [("background: 'var(--cap-ok, #34c77a)', animation: 'capVivo 2s ease-in-out infinite', display: 'inline-block' } }),", "background: 'var(--cap-tele, #00f4fd)', animation: 'capVivo 2s ease-in-out infinite', display: 'inline-block' } }),")], 'leitura'),
    ('o LED da Main em última leitura sem o âmbar', 'Main.dc.html', [("background: 'var(--cap-warn, #f0a63a)', boxShadow: '0 0 0 3px rgba(var(--cap-warn-rgb, 240,166,58), 0.22)', display: 'inline-block' } }),", "border: '1.5px solid var(--cap-ink3, #97a3c0)', boxSizing: 'border-box', display: 'inline-block' } }),")], 'real'),
    ('o gerador da Main com «Onan» fixo no código', 'Main.dc.html', [("Object.assign({ n: '2 · GERADOR', eq: [nome('gerador'), horas].filter(Boolean).join(' · '),", "Object.assign({ n: '2 · GERADOR', eq: ['Onan QD 9', horas].filter(Boolean).join(' · '),")], 'dados'),
    ('as horas do gerador da Main sem o quadro (só o fabricante)', 'Main.dc.html', [("hg = I && I.q && f && !(I.fonte === 'replay' && !sim) ? f(I.q, 'gerador_horimetro_h') : null;", "hg = null;")], 'leitura'),
    ('o chip da Main de volta com «PRONTO · DEMO»', 'Main.dc.html', [("Object.assign({ chip: 'PRONTO' }, chip('ok'))", "Object.assign({ chip: 'PRONTO · DEMO' }, chip('ok'))")], 'leitura'),
    ('o chip dos eletrônicos da Main de volta com «FAQ · DEMO»', 'Main.dc.html', [("Object.assign({ chip: faq.eletronicos.perguntas.length + ' FAQ' }, chip('ok'))", "Object.assign({ chip: faq.eletronicos.perguntas.length + ' FAQ · DEMO' }, chip('ok'))")], 'leitura'),
    ('o atraso do rotor na Main ignora o Executado', 'Main.dc.html', [("return t && !feitas[t.id] && typeof t.dn === 'number' && t.dn < 0 ? t : null; };", "return t && typeof t.dn === 'number' && t.dn < 0 ? t : null; };")], 'dados'),
    ('as atrasadas da Main contadas na agenda crua (sem o CapitaoAgora)', 'Main.dc.html', [("atr = A.contagens ? A.contagens().atrasadas : ag.filter((t) => !feitas[t.id] && t.dn < 0).length;", "atr = ag.filter((t) => t.dn < 0).length;")], 'dados'),
    ('a Main com «SEM DADOS» sem o ramo simulacao false (falta() sempre rotula)', 'Main.dc.html', [("falta = (r) => (sim ? '' : r), ag = D.agenda || [], EQ", "falta = (r) => r, ag = D.agenda || [], EQ")], 'dados'),
    ('a Main sem assinar o capitao-telemetria', 'Main.dc.html', [("['capitao-telemetria', 'capitao-rebase'].forEach((ev) => window.addEventListener(ev, this._onTele));", "['capitao-rebase'].forEach((ev) => window.addEventListener(ev, this._onTele));")], 'vivo'),
    ('a Main não remove o ouvinte da telemetria ao desmontar', 'Main.dc.html', [("['capitao-telemetria', 'capitao-rebase'].forEach((ev) => window.removeEventListener(ev, this._onTele));", "['capitao-rebase'].forEach((ev) => window.removeEventListener(ev, this._onTele));")], 'ouvintes'),
    ('a Main não remove o ouvinte do botão de uma resposta', 'Main.dc.html', [("    window.removeEventListener('capitao-chat-pergunta', this._chat);\n", "")], 'ouvintes'),
    # —— H2 ——
    ('o selo violeta da H2 de volta (DEMO · DADOS FICTÍCIOS)', 'H2-Home-Mobile.dc.html', [("<svg width=\"11\" height=\"11\" viewBox=\"0 0 24 24\" fill=\"none\" aria-hidden=\"true\" style=\"flex-shrink: 0;\"><path d=\"M12 2l10 10-10 10L2 12z", "<span style=\"border: 1px solid rgba(var(--cap-violeta-rgb, 162,43,253), 0.55); font-size: 9px; padding: 3px 7px;\">DEMO · DADOS FICTÍCIOS</span><svg width=\"11\" height=\"11\" viewBox=\"0 0 24 24\" fill=\"none\" aria-hidden=\"true\" style=\"flex-shrink: 0;\"><path d=\"M12 2l10 10-10 10L2 12z")], 'leitura'),
    ('a dica do LED da H2 de volta com «snapshot»', 'H2-Home-Mobile.dc.html', [("liveTip: vivo ? 'Telemetria ao vivo — atualiza a cada segundo' : 'Sem leitura ao vivo agora — mostrando a última leitura salva',", "liveTip: vivo ? 'Telemetria ao vivo — atualiza a cada segundo' : 'Telemetria ao vivo desligada — snapshot de 26/09',")], 'real'),
    ('o gerador da H2 com «Onan» fixo no código', 'H2-Home-Mobile.dc.html', [("s: rot('gerador', 'Gerador') + ' — ligar · desligar · alarmes'", "s: 'Gerador Onan (modelo SEM DADOS) — ligar · desligar · alarmes'")], 'dados'),
    ('os eletrônicos da H2 com a lista fixa «Garmin · Fusion · Icom»', 'H2-Home-Mobile.dc.html', [("s: (fabs.join(' · ') || falta('Fabricantes SEM DADOS')) + ' — plotter", "s: 'Garmin · Fusion · Icom — plotter")], 'dados'),
    ('o atraso do filtro na H2 ignora o Executado', 'H2-Home-Mobile.dc.html', [("const atr = (t) => !!(t && !feitas[t.id] && typeof t.dn === 'number' && t.dn < 0);", "const atr = (t) => !!(t && typeof t.dn === 'number' && t.dn < 0);")], 'dados'),
    ('o LED da H2 sem o selo do coletor (sempre verde)', 'H2-Home-Mobile.dc.html', [("return !!(I && I.q && !(I.fonte === 'replay' && D.simulacao !== true) && (!I.selo || I.selo.tom === 'ok'));", "return true;")], 'real'),
    ('a H2 não remove o ouvinte da virada do dia', 'H2-Home-Mobile.dc.html', [("    window.removeEventListener('capitao-rebase', this._onReb);\n", "")], 'ouvintes'),
    ('a Main redesenha com a aba escondida (o tique sem o document.hidden)', 'Main.dc.html', [("this._onTele = () => { if (document.hidden) return; const k = JSON.stringify(this.leitura());", "this._onTele = () => { const k = JSON.stringify(this.leitura());")], 'codigo'),
    ('a H2 redesenha o LED com a aba escondida (o tique sem o document.hidden)', 'H2-Home-Mobile.dc.html', [("this._onTele = () => { if (document.hidden) return; const k = this.vivoTele();", "this._onTele = () => { const k = this.vivoTele();")], 'codigo'),
    # —— o chat (Main e H2) ——
    ('a Main manda a IA o 3º argumento vazio (sem a leitura de agora)', 'Main.dc.html', [("B.resumoAgora ? B.resumoAgora(a, { emergencia: emg }) : '', {", "'', {")], 'ia'),
    ('a H2 manda a IA o 3º argumento vazio (sem a leitura de agora)', 'H2-Home-Mobile.dc.html', [("B.resumoAgora ? B.resumoAgora(a, { emergencia: emg }) : '', {", "'', {")], 'ia'),
    ('a Main monta o histórico por conta própria (as 6 últimas, sem filtro)', 'Main.dc.html', [("return B && B.historicoIA ? B.historicoIA(i < 0 ? th : th.slice(0, i), { emergencia: !!emg }) : [];", "return (i < 0 ? th : th.slice(0, i)).slice(-6).map((m) => ({ papel: m.role === 'user' ? 'usuario' : 'capitao', texto: String(m.text || '').slice(0, 600) }));")], 'ia'),
    ('a H2 monta o histórico por conta própria (as 6 últimas, sem filtro)', 'H2-Home-Mobile.dc.html', [("return B && B.historicoIA ? B.historicoIA(i < 0 ? th : th.slice(0, i), { emergencia: !!emg }) : [];", "return (i < 0 ? th : th.slice(0, i)).slice(-6).map((m) => ({ papel: m.role === 'user' ? 'usuario' : 'capitao', texto: String(m.text || '').slice(0, 600) }));")], 'ia'),
    ('a Main não conta a resposta da IA ao cérebro (sem B.conversa)', 'Main.dc.html', [("try { if (B.conversa) B.conversa(qc, r.text); } catch (e) {} ", "")], 'ia'),
    ('a H2 não conta a resposta da IA ao cérebro (sem B.conversa)', 'H2-Home-Mobile.dc.html', [("try { if (B.conversa) B.conversa(qc, r.text); } catch (e) {} ", "")], 'ia'),
    ('a Main manda o ditado sem corrigir à IA', 'Main.dc.html', [("const qc = B.corrigeVoz ? B.corrigeVoz(q) : q;", "const qc = q;")], 'ia'),
    ('a H2 manda o ditado sem corrigir à IA', 'H2-Home-Mobile.dc.html', [("const qc = B.corrigeVoz ? B.corrigeVoz(q) : q;", "const qc = q;")], 'ia'),
    ('a Main não passa a janela de emergência ao cérebro (answer)', 'Main.dc.html', [("} else a = B.answer(q, link ? { platform: 'web', id: id, commit: false, emergencia: emg, faq: faq } : { platform: 'web', id: id, emergencia: emg });", "} else a = B.answer(q, link ? { platform: 'web', id: id, commit: false, faq: faq } : { platform: 'web', id: id });")], 'janela'),
    ('a H2 não passa a janela de emergência ao cérebro (answer)', 'H2-Home-Mobile.dc.html', [("} else a = B.answer(q, link ? { platform: 'app', id: id, commit: false, emergencia: emg, faq: faq } : { platform: 'app', id: id, emergencia: emg });", "} else a = B.answer(q, link ? { platform: 'app', id: id, commit: false, faq: faq } : { platform: 'app', id: id });")], 'janela'),
    ('a Main não marca a janela quando a resposta a abre', 'Main.dc.html', [("if (a && a.abreJanela === true) { try { if (EM) EM.marca(); } catch (e) {} }", "")], 'janela'),
    ('a H2 não marca a janela quando a resposta a abre', 'H2-Home-Mobile.dc.html', [("if (a && a.abreJanela === true) { try { if (EM) EM.marca(); } catch (e) {} }", "")], 'janela'),
    ('o NOVA da Main não zera o contexto nem a janela', 'Main.dc.html', [("  clearThread() {\n    this.limpaContexto();\n", "  clearThread() {\n")], 'janela'),
    ('o NOVA da H2 não zera o contexto nem a janela', 'H2-Home-Mobile.dc.html', [("  clearThread() {\n    this.limpaContexto();\n", "  clearThread() {\n")], 'janela'),
    ('o ENCERRAR da Main não zera o contexto nem a janela', 'Main.dc.html', [("this._onEncerra = () => { this.limpaContexto(); if", "this._onEncerra = () => { if")], 'janela'),
    ('o ENCERRAR da H2 não zera o contexto nem a janela', 'H2-Home-Mobile.dc.html', [("this._onEncerra = () => { this.limpaContexto(); if", "this._onEncerra = () => { if")], 'janela'),
    ('o botão de uma resposta na Main leva o anexo e apaga o que se digita (modo de pergunta digitada)', 'Main.dc.html', [("this.ask(d.q, null, 'botao')", "this.ask(d.q)")], 'botoes'),
    ('o botão de uma resposta na H2 leva o anexo e apaga o que se digita (modo de pergunta digitada)', 'H2-Home-Mobile.dc.html', [("this.ask(d.q, null, 'botao')", "this.ask(d.q)")], 'botoes'),
    ('a Main não escuta o botão de uma resposta (sem capitao-chat-pergunta)', 'Main.dc.html', [("    window.addEventListener('capitao-chat-pergunta', this._chat);\n", "")], 'botoes'),
    ('a H2 não escuta o botão de uma resposta (sem capitao-chat-pergunta)', 'H2-Home-Mobile.dc.html', [("    window.addEventListener('capitao-chat-pergunta', this._chat);\n", "")], 'botoes'),
    # —— H3 ——
    ('o resumo da H3 web de volta com « · DEMO»', 'H3-Atalhos-Editar-Web.dc.html', [("iguais no console e no app',", "iguais no console e no app' + (window.CapitaoDados.demo ? ' · DEMO' : ''),")], 'h3'),
    ('o atalho do checklist da H3 app leva à C4 web', 'H3-Atalhos-Editar.dc.html', [('<a href="C4-Checklist-Mobile.dc.html" data-h3="tela-checklist"', '<a href="C4-Checklist-Web.dc.html" data-h3="tela-checklist"')], 'h3'),
]
# cada conferência roda só na tela do arquivo que recebeu o defeito (a Main, a H2 ou a H3)
QUAL_P4G = {'leitura': lambda b, t: teste_home_leitura(b, t), 'real': lambda b, t: teste_home_real(b, t), 'dados': lambda b, t: teste_home_dados(b, t) + teste_home_codigo(),
            'vivo': lambda b, t: teste_home_vivo(b, t) + teste_home_codigo(), 'ouvintes': lambda b, t: teste_home_ouvintes(b, t) + teste_home_codigo(), 'ia': lambda b, t: teste_home_ia(b, t),
            'janela': lambda b, t: teste_home_janela(b, t), 'botoes': lambda b, t: teste_home_botoes(b, t), 'h3': lambda b, t: teste_h3(b, t), 'codigo': lambda b, t: teste_home_codigo()}


def mutantes_p4g(b):
    global MUT_ARQ
    vivos = []
    filtro = os.environ.get('MUT_FILTRO', '')   # só os mutantes cujo nome tem este texto (para refazer um)
    for nome, arq, trocas, qual in MUTANTES_P4G:
        if filtro and filtro not in nome: continue
        src = open(os.path.join(RAIZ, arq), encoding='utf-8', newline='').read()
        faltam = [x for x, _ in trocas if src.count(x) != 1]
        if faltam:
            print('ERRO no mutante «%s»: o trecho não está uma vez em %s: %s' % (nome, arq, faltam)); vivos.append(nome); continue
        MUT_ARQ = {arq: trocas}
        sai = sys.stdout
        prob = []
        try:
            sys.stdout = open(os.devnull, 'w')
            prob = QUAL_P4G[qual](b, arq.replace('.dc.html', ''))
        except Exception as e:   # um erro do próprio teste não conta como acusação: o mutante fica vivo
            sys.stdout = sai
            print('ERRO do teste no mutante «%s»: %s' % (nome, str(e).splitlines()[-1][:160]))
            prob = []
        finally:
            sys.stdout = sai
            MUT_ARQ = {}
        print('MUTANTE %s: %s (%d problema(s))%s' % ('ACUSADO' if prob else 'VIVO', nome, len(prob), ' · ' + prob[0][:150] if prob else ''))
        if not prob: vivos.append(nome)
    print('%d mutantes · %d vivos' % (len(MUTANTES_P4G), len(vivos)))
    return vivos


# ═══ Fase 4, P4H: o FAQ dos equipamentos (o hub F1, os FAQs F2 a F5 e a F6, web e app) ═══
# `--so-p4h [Tela…]` roda só as conferências dela; `--mutantes-p4h` planta os defeitos (todos acusados; `MUT_FILTRO=texto` refaz só os mutantes cujo nome tem o texto).
# O Worker da IA é de mentira (sem cota). A F6 é tela nova (prancheta 1440 e 390); o capitao-faq.js é o modelo dela (o cérebro carrega, indexa e busca o faq-equipamentos.json).
TELAS_F1 = ('F1-FAQ-Hub-Web', 'F1-FAQ-Hub')
TELAS_F2F5 = ('F2-FAQ-Estabilizador-Web', 'F2-FAQ-Estabilizador', 'F3-FAQ-Eletronicos-Web', 'F3-FAQ-Eletronicos', 'F4-FAQ-Gerador-Web', 'F4-FAQ-Gerador', 'F5-FAQ-Climatizacao-Web', 'F5-FAQ-Climatizacao')
TELAS_F6 = ('F6-FAQ-Equipamentos-Web', 'F6-FAQ-Equipamentos')
TELAS_CHAT_FAQ = ('Main', 'H2-Home-Mobile')   # o chat que recebe o toque do FAQ (#q=…&faq=…)
TELAS_P4H = TELAS_F1 + TELAS_F2F5 + TELAS_F6 + TELAS_CHAT_FAQ
FAQ_JSON = json.load(open(os.path.join(RAIZ, 'faq-equipamentos.json'), encoding='utf-8'))
FAQ_ITENS = {it['id']: it for it in FAQ_JSON['itens']}
CHAT_DE = {'web': 'Main.dc.html', 'app': 'H2-Home-Mobile.dc.html'}
SOS_DE = {'web': 'S1-SOS-Web.dc.html', 'app': 'S2-SOS-Mobile.dc.html'}
# o FAQ completo de cada tela F2 a F5 (as seções do arquivo) e o cartão único «Eletrônicos» do hub (F3: plotters, áudio e VHF)
F6_DE = {'F2': '#s=4', 'F3': '#s=6,7', 'F4': '#s=3', 'F5': '#s=5'}
UNICO_ELETRONICOS = ('eletronicos', 'audio', 'vhf')


def plat(tela): return 'app' if eh_app(tela) else 'web'
def f6_arq(tela): return 'F6-FAQ-Equipamentos.dc.html' if eh_app(tela) else 'F6-FAQ-Equipamentos-Web.dc.html'
def lin(s): return re.sub(r'\s+', ' ', s or '').strip()
def enc(s): return urllib.parse.quote(s, safe="!~*'()")


LE_F6 = """() => { const lin = (s) => (s || '').replace(/\\s+/g, ' ').trim(), q = (s) => document.querySelector(s), d = q('[data-f6=detalhe]');
  const det = d ? { id: d.getAttribute('data-id'), codigo: lin((q('[data-f6=codigo]') || {}).innerText), titulo: lin((q('[data-f6=titulo]') || {}).innerText), resposta: lin((q('[data-f6=resposta]') || {}).innerText), acao: lin((q('[data-f6=acao]') || {}).innerText),
    passos: [...document.querySelectorAll('[data-f6=passo]')].map((e) => lin(e.innerText).replace(/^\\d+\\s*/, '')), fontes: [...document.querySelectorAll('[data-f6=fonte]')].map((e) => lin(e.innerText)),
    atencao: lin((q('[data-f6=atencao]') || {}).innerText), senao: lin((q('[data-f6=senao]') || {}).innerText), obs: lin((q('[data-f6=obs]') || {}).innerText),
    sos: q('[data-f6=sos]') ? q('[data-f6=sos]').getAttribute('href') : null, chat: q('[data-f6=chat]') ? q('[data-f6=chat]').getAttribute('href') : null,
    ver: [...document.querySelectorAll('[data-f6=ver]')].map((e) => e.getAttribute('data-id')), texto: d.innerText } : null;
  return { itens: [...document.querySelectorAll('[data-f6=item]')].map((e) => e.getAttribute('data-id')), filtros: [...document.querySelectorAll('[data-f6=filtro]')].map((e) => ({ l: lin(e.innerText), on: e.getAttribute('aria-pressed') })),
    contagem: lin((q('[data-f6=contagem]') || {}).innerText), resumo: lin((q('[data-f6=resumo]') || {}).innerText), busca: (q('[data-f6=busca]') || {}).value, hash: location.hash, det,
    termos: [...document.querySelectorAll('[data-f6=termo]')].map((e) => lin(e.innerText)), vazio: !!q('[data-f6=vazio]'), como: !!q('[data-f6=como-usar]'), lateral: document.documentElement.scrollWidth - document.documentElement.clientWidth, texto: document.body.innerText }; }"""
LE_F6_TODOS = "async (ids) => { const le = " + LE_F6 + "; const out = []; for (const id of ids) { location.hash = '#id=' + id; await new Promise((ok) => setTimeout(ok, 45)); out.push(le()); } return out; }"
CLICA_FILTRO = "(i) => document.querySelectorAll('[data-f6=filtro]')[i].click()"


def abre_f6(b, tela, hash_='', fixo='60', **kw):
    ctx, pg, erros = abre_tela(b, tela, fixo=fixo, hash_=hash_, **kw)
    try: pg.wait_for_function("() => document.querySelector('[data-f6=item],[data-f6=termo],[data-f6=detalhe],[data-f6=vazio]')", timeout=10000)
    except Exception: pass
    pg.wait_for_timeout(300)
    return ctx, pg, erros


def ids_secao(*ns): return [it['id'] for it in FAQ_JSON['itens'] if it['secao'] in ns]


def teste_f6_lista(b, tela):
    """F6: os 91 itens do arquivo na ordem das seções, os 11 filtros (Todas, as 9 seções do arquivo e o Glossário), a contagem, cada seção só com os itens dela e o endereço (#s=n), o glossário com os 14 termos e a
    varredura do §3 em cada estado; a 60 s e a 105 s (a tela não lê leitura: é a mesma)."""
    prob = []
    todos = [it['id'] for it in FAQ_JSON['itens']]
    secs = FAQ_JSON['secoes']
    nem = sum(1 for it in FAQ_JSON['itens'] if it.get('emerg'))
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_f6(b, tela, fixo=fixo)
        r = pg.evaluate(LE_F6)
        rot = '%s a %s s' % (tela, fixo)
        if r['itens'] != todos: prob.append('%s: os itens da lista são %d (esperado os %d do arquivo, na ordem das seções)' % (rot, len(r['itens']), len(todos)))
        esp = ('%d itens · %d cartões de emergência e %d perguntas' % (len(todos), nem, len(todos) - nem)).upper()
        if r['contagem'] != esp: prob.append('%s: a contagem diz %r (esperado %r)' % (rot, r['contagem'], esp))
        chips = [f['l'] for f in r['filtros']]
        if chips != ['Todas'] + [s['titulo'] for s in secs] + ['Glossário']: prob.append('%s: os filtros são %s (esperado Todas, as seções do arquivo e Glossário)' % (rot, chips))
        if [f['l'] for f in r['filtros'] if f['on'] == 'true'] != ['Todas']: prob.append('%s: o filtro marcado devia ser só «Todas»: %s' % (rot, [f for f in r['filtros'] if f['on'] == 'true']))
        if str(len(todos)) not in r['resumo'] or 'edição de' not in r['resumo']: prob.append('%s: o resumo não diz o total nem a edição: %r' % (rot, r['resumo']))
        if plat(tela) == 'web' and not r['como']: prob.append('%s: a coluna da direita sem o «como usar» enquanto nenhum item está aberto' % rot)
        if r['lateral'] > 1: prob.append('%s: rola para o lado (%d px)' % (rot, r['lateral']))
        ach = achados_termos(tela, r['texto'])
        if ach: prob.append('%s: termo do §3 na lista: %s' % (rot, ach))
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        if fixo == '105':
            ctx.close(); continue
        # cada seção: só os itens dela, o título e a contagem dela, o endereço #s=n; Todas volta ao fim, sem endereço
        for k, s in enumerate(secs):
            pg.evaluate(CLICA_FILTRO, k + 1); pg.wait_for_timeout(120)
            x = pg.evaluate(LE_F6)
            esp = ('%d. %s · %d itens' % (s['n'], s['titulo'], len(s['ids']))).upper()
            if x['itens'] != s['ids'] or x['contagem'] != esp or x['hash'] != '#s=%d' % s['n'] or [f['l'] for f in x['filtros'] if f['on'] == 'true'] != [s['titulo']]:
                prob.append('%s: o filtro «%s» mostra %d itens, contagem %r, endereço %r (esperado %s, %r, #s=%d)' % (rot, s['titulo'], len(x['itens']), x['contagem'], x['hash'], len(s['ids']), esp, s['n']))
            ach = achados_termos(tela, x['texto'])
            if ach: prob.append('%s: termo do §3 na seção %d: %s' % (rot, s['n'], ach))
        pg.evaluate(CLICA_FILTRO, len(secs) + 1); pg.wait_for_timeout(150)
        g = pg.evaluate(LE_F6)
        esp_g = [lin(t['termo'] + ' ' + t['texto'] + (' Fonte: ' + t['fonte'] if t.get('fonte') else '')) for t in FAQ_JSON['glossario']]
        if g['termos'] != esp_g or g['itens'] or g['hash'] != '#glossario' or [f['l'] for f in g['filtros'] if f['on'] == 'true'] != ['Glossário']:
            prob.append('%s: o glossário mostra %d termos (esperado os %d do arquivo, com o texto e a fonte), %d itens de lista e endereço %r' % (rot, len(g['termos']), len(esp_g), len(g['itens']), g['hash']))
        ach = achados_termos(tela, g['texto'])
        if ach: prob.append('%s: termo do §3 no glossário: %s' % (rot, ach))
        pg.evaluate(CLICA_FILTRO, 0); pg.wait_for_timeout(150)
        t = pg.evaluate(LE_F6)
        if t['itens'] != todos or t['hash'] != '': prob.append('%s: «Todas» devia voltar aos %d itens e limpar o endereço: %d itens, %r' % (rot, len(todos), len(t['itens']), t['hash']))
        ctx.close()
    return prob


def teste_f6_enderecos(b, tela):
    """F6: os endereços que o hub, o chat e o checklist usam: #id=<código> abre o item (minúscula também), código que não existe vale como lista, #s=6,7 (as duas seções do «Eletrônicos»), #s=99 vale como todas,
    #busca=texto, #glossario; e trocar o endereço com a tela aberta muda a tela sem recarregar."""
    prob = []
    todos = [it['id'] for it in FAQ_JSON['itens']]
    casos = [('#id=GE-02', 'det', 'GE-02'), ('#id=ge-02', 'det', 'GE-02'), ('#id=EM-01', 'det', 'EM-01'), ('#id=XX-99', 'lista', todos), ('#id=lixo', 'lista', todos), ('#s=6,7', 'lista', ids_secao(6, 7)), ('#s=6', 'lista', ids_secao(6)),
             ('#s=99', 'lista', todos), ('#s=1,99', 'lista', ids_secao(1)), ('#s=7,6', 'lista', ids_secao(6, 7)), ('#glossario', 'gloss', None), ('#busca=baliza', 'busca', 'baliza')]
    for h, tipo, esp in casos:
        ctx, pg, erros = abre_f6(b, tela, hash_=h)
        r = pg.evaluate(LE_F6)
        if tipo == 'det' and not (r['det'] and r['det']['id'] == esp): prob.append('%s %s: devia abrir o item %s: %s' % (tela, h, esp, r['det'] and r['det']['id']))
        elif tipo == 'lista' and (r['det'] or r['itens'] != esp): prob.append('%s %s: devia ser a lista de %d itens sem item aberto: %d itens, detalhe %s' % (tela, h, len(esp), len(r['itens']), r['det'] and r['det']['id']))
        elif tipo == 'gloss' and (len(r['termos']) != len(FAQ_JSON['glossario']) or r['itens']): prob.append('%s %s: devia abrir o glossário: %d termos' % (tela, h, len(r['termos'])))
        elif tipo == 'busca' and (r['busca'] != esp or not r['itens'] or 'EP-02' not in r['itens']): prob.append('%s %s: devia buscar «baliza» (campo %r, %d itens, com o EP-02): %s' % (tela, h, r['busca'], len(r['itens']), r['itens'][:5]))
        if h in ('#s=6,7', '#s=7,6'):
            on = [f['l'] for f in r['filtros'] if f['on'] == 'true']
            if on != ['Eletrônicos'] or r['contagem'] != ('Eletrônicos · seções 6 e 7 · %d itens' % len(esp)).upper(): prob.append('%s %s: o grupo «Eletrônicos» devia ficar marcado, com a contagem das seções 6 e 7: %s %r' % (tela, h, on, r['contagem']))
        if erros: prob += ['%s %s: %s' % (tela, h, e) for e in erros[:2]]
        ctx.close()
    # com a tela aberta: o endereço novo muda a tela, sem recarregar
    ctx, pg, erros = abre_f6(b, tela)
    pg.evaluate("() => { window.__marca = 'viva'; location.hash = '#id=EM-03'; }"); pg.wait_for_timeout(400)
    r = pg.evaluate(LE_F6)
    if not (r['det'] and r['det']['id'] == 'EM-03') or pg.evaluate("() => window.__marca") != 'viva': prob.append('%s: trocar o endereço para #id=EM-03 devia abrir o item sem recarregar: %s' % (tela, r['det'] and r['det']['id']))
    pg.evaluate("() => { location.hash = '#s=2'; }"); pg.wait_for_timeout(400)
    r = pg.evaluate(LE_F6)
    if r['det'] or r['itens'] != ids_secao(2): prob.append('%s: trocar o endereço para #s=2 devia mostrar a lista dos motores: %d itens, detalhe %s' % (tela, len(r['itens']), r['det'] and r['det']['id']))
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_f6_busca(b, tela):
    """F6: a busca. O código acha o item (EM-06, em-6), a frase vai pela busca do cérebro (a mesma do chat: «profundidade mínima na sonda» → EL-08 primeiro), a palavra solta (que o cérebro não busca) casa o título
    («baliza» → o teste da baliza e o cartão do EPIRB), a seção filtra a busca, o que não existe diz que não achou, o botão limpa volta aos 91 e o endereço guarda o texto."""
    prob = []
    ctx, pg, erros = abre_f6(b, tela)
    def digita(t):
        pg.fill('[data-f6=busca]', t); pg.wait_for_timeout(250)
        return pg.evaluate(LE_F6)
    r = digita('EM-06')
    if r['itens'] != ['EM-06'] or r['hash'] != '#busca=EM-06': prob.append('%s: «EM-06» devia achar só o item EM-06 (endereço #busca=EM-06): %s %r' % (tela, r['itens'], r['hash']))
    r = digita('em-6')
    if r['itens'] != ['EM-06']: prob.append('%s: «em-6» devia achar o EM-06: %s' % (tela, r['itens']))
    r = digita('profundidade mínima na sonda')
    if not r['itens'] or r['itens'][0] != 'EL-08': prob.append('%s: «profundidade mínima na sonda» devia achar o EL-08 primeiro (a busca do cérebro): %s' % (tela, r['itens'][:4]))
    r = digita('baliza')
    if not {'EP-02', 'EM-08'} <= set(r['itens']): prob.append('%s: «baliza» (uma palavra: casa o título) devia achar o EP-02 e o EM-08: %s' % (tela, r['itens'][:6]))
    if r['contagem'] != ('%d resultados' % len(r['itens'])).upper(): prob.append('%s: a contagem da busca diz %r (esperado %d resultados)' % (tela, r['contagem'], len(r['itens'])))
    r = digita('xyzzy')
    if r['itens'] or not r['vazio']: prob.append('%s: o que não existe devia dizer que nada foi achado: %s vazio=%s' % (tela, r['itens'], r['vazio']))
    r = digita('gerador')
    if not r['itens'] or not all('gerador' in lin(FAQ_ITENS[i]['titulo'] + ' ' + FAQ_ITENS[i]['pergunta'] + ' ' + ' '.join(FAQ_ITENS[i]['variantes']) + ' ' + FAQ_ITENS[i]['equip']).lower() for i in r['itens']): prob.append('%s: «gerador» devia achar só itens que falam do gerador: %s' % (tela, r['itens'][:6]))
    # a seção filtra a busca: «gerador» na seção dos motores (2) não acha o gerador (seção 3)
    pg.evaluate(CLICA_FILTRO, 2); pg.wait_for_timeout(250)
    r2 = pg.evaluate(LE_F6)
    if any(FAQ_ITENS[i]['secao'] != 2 for i in r2['itens']): prob.append('%s: a seção dos motores filtrando a busca deixou passar item de outra seção: %s' % (tela, r2['itens'][:6]))
    pg.evaluate(CLICA_FILTRO, 0); pg.wait_for_timeout(200)
    digita('baliza')
    pg.click('[data-f6=limpa]'); pg.wait_for_timeout(250)
    r = pg.evaluate(LE_F6)
    if r['busca'] != '' or r['itens'] != [it['id'] for it in FAQ_JSON['itens']] or r['hash'] != '': prob.append('%s: limpar a busca devia voltar aos %d itens, com o campo vazio e sem endereço: %d itens %r %r' % (tela, len(FAQ_JSON['itens']), len(r['itens']), r['busca'], r['hash']))
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def problemas_f6_item(r, i, tela):
    """Um item aberto na F6 é o do arquivo: o código, o título, a resposta, cada passo, a atenção, o «se não resolver», a observação, as fontes, o «ver também», o botão do SOS só no cartão de emergência e o
    link do chat com a pergunta e o código (#q=<pergunta>&faq=<código>)."""
    prob = []
    it, d, p = FAQ_ITENS[i], r['det'], plat(tela)
    if not d or d['id'] != i or d['codigo'] != i: return ['%s %s: o item não abriu (detalhe %s)' % (tela, i, d and d['id'])]
    if d['titulo'] != lin(it['titulo']): prob.append('%s %s: o título é %r' % (tela, i, d['titulo']))
    if d['resposta'] != lin(it['resposta']): prob.append('%s %s: a resposta é %r' % (tela, i, d['resposta'][:60]))
    if d['passos'] != [lin(x) for x in it.get('passos', [])]: prob.append('%s %s: os passos são %d (esperado os %d do arquivo, na ordem)' % (tela, i, len(d['passos']), len(it.get('passos', []))))
    if d['fontes'] != [lin(f['tipo'].upper() + ' ' + f['texto']) for f in it['fontes']]: prob.append('%s %s: as fontes são %s' % (tela, i, d['fontes']))
    for campo in ('atencao', 'senao', 'obs'):
        if d[campo] != lin(it.get(campo, '')): prob.append('%s %s: %s é %r (esperado %r)' % (tela, i, campo, d[campo][:50], lin(it.get(campo, ''))[:50]))
    if it.get('acao') and d['acao'] != lin(it['acao']): prob.append('%s %s: a ação é %r (esperado %r)' % (tela, i, d['acao'], it['acao']))
    if not it.get('acao') and d['acao']: prob.append('%s %s: tem ação (%r) e o arquivo não' % (tela, i, d['acao']))
    if d['sos'] != (SOS_DE[p] if it.get('emerg') else None): prob.append('%s %s: o botão do SOS é %r (esperado %r: só o cartão de emergência, para a tela de emergência %s)' % (tela, i, d['sos'], SOS_DE[p] if it.get('emerg') else None, 'do app' if p == 'app' else 'do computador'))
    if d['chat'] != CHAT_DE[p] + '#q=' + enc(it['pergunta']) + '&faq=' + enc(i): prob.append('%s %s: o link do chat é %r (esperado %s#q=<pergunta>&faq=%s)' % (tela, i, d['chat'], CHAT_DE[p], i))
    if d['ver'] != [x for x in it.get('ver', []) if x in FAQ_ITENS]: prob.append('%s %s: o «ver também» é %s (esperado %s)' % (tela, i, d['ver'], it.get('ver')))
    ach = achados_termos(tela, d['texto'])
    if ach: prob.append('%s %s: termo do §3 no item: %s' % (tela, i, ach))
    if re.search(r'710123456|' + R_POSICAO.pattern, d['texto']): prob.append('%s %s: o item traz o MMSI do cadastro ou coordenada' % (tela, i))
    return prob


def teste_f6_itens(b, tela):
    """F6: os 91 itens abertos um a um (pelo endereço, no mesmo carregamento): cada um é o do arquivo, sem termo do §3, com o botão do SOS só nos 9 cartões de emergência e o link do chat com o código."""
    prob = []
    ctx, pg, erros = abre_f6(b, tela)
    todos = pg.evaluate(LE_F6_TODOS, [it['id'] for it in FAQ_JSON['itens']])
    if len(todos) != len(FAQ_JSON['itens']): prob.append('%s: abriu %d itens de %d' % (tela, len(todos), len(FAQ_JSON['itens'])))
    for it, r in zip(FAQ_JSON['itens'], todos):
        prob += problemas_f6_item(r, it['id'], tela)
        if len(prob) > 12: break
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def teste_f6_carga_lenta(b, tela):
    """F6: o arquivo do FAQ chega devagar (0,7 s por pedido), depois de a 2ª cópia do capitao-brain.js (o <head> da tela o roda duas vezes) assumir o window.CapitaoBrain sem o FAQ: a tela sai do «Carregando…» e mostra os
    91 itens (o módulo pede de novo ao cérebro de agora e guarda o arquivo); sem rede, a F6 diz que está carregando e não quebra."""
    prob = []
    movel = eh_app(tela)
    for modo in ('lenta', 'sem rede'):
        ctx = b.new_context(viewport={'width': 390 if movel else 1440, 'height': 844 if movel else 900}, user_agent=MOBILE_UA if movel else None, is_mobile=movel, has_touch=movel, service_workers='block')
        ctx.add_init_script(SESSAO + ";localStorage.setItem('capitao.plataforma.v1','%s');localStorage.setItem('capitao.replay.fixo','60');" % ('app' if movel else 'web'))
        def lenta(route):
            if modo == 'lenta':
                time.sleep(0.7); route.continue_()
            else:
                route.abort()
        ctx.route('**/faq-equipamentos.json', lenta)
        aplica_mut(ctx)
        pg = ctx.new_page()
        erros = []
        pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
        pg.goto(BASE + tela + '.dc.html', wait_until='load')
        try: pg.wait_for_function("() => document.querySelectorAll('[data-f6=item]').length > 0", timeout=14000 if modo == 'lenta' else 3500)
        except Exception: pass
        n = pg.evaluate("() => document.querySelectorAll('[data-f6=item]').length")
        res = pg.evaluate("() => (document.querySelector('[data-f6=resumo]') || {}).innerText")
        if modo == 'lenta' and n != len(FAQ_JSON['itens']): prob.append('%s: com o arquivo lento a F6 ficou com %d itens (esperado %d): %r' % (tela, n, len(FAQ_JSON['itens']), res))
        if modo == 'sem rede' and (n != 0 or 'Carregando' not in (res or '')): prob.append('%s: sem o arquivo a F6 devia dizer «Carregando…» sem itens: %d itens, %r' % (tela, n, res))
        if erros: prob += ['%s (%s): %s' % (tela, modo, e) for e in erros[:2]]
        ctx.close()
    return prob


def teste_f6_navegacao(b, tela):
    """F6: o toque. Tocar num item abre o detalhe e põe #id=<código> no endereço; «Fechar» volta à lista (e limpa o endereço); o «ver também» abre o outro item; no app a lista some com o item aberto e volta com
    «Voltar à lista»; o cartão de emergência (EM-06) tem o botão do SOS vermelho (S1 no computador, S2 no celular) e o item comum (MO-02) não."""
    prob = []
    p = plat(tela)
    ctx, pg, erros = abre_f6(b, tela)
    pg.evaluate("() => document.querySelector('[data-f6=item][data-id=EM-06]').click()"); pg.wait_for_timeout(300)
    r = pg.evaluate(LE_F6)
    if not r['det'] or r['det']['id'] != 'EM-06' or r['hash'] != '#id=EM-06': prob.append('%s: tocar no EM-06 devia abrir o item e pôr #id=EM-06: %s %r' % (tela, r['det'] and r['det']['id'], r['hash']))
    if p == 'app' and r['itens']: prob.append('%s: no app a lista devia sumir com o item aberto (%d itens)' % (tela, len(r['itens'])))
    if p == 'web' and not r['itens']: prob.append('%s: na web a lista fica ao lado do item aberto' % tela)
    sos = pg.evaluate("() => { const a = document.querySelector('[data-f6=sos]'); if (!a) return null; const r = a.getBoundingClientRect(); return { h: Math.round(r.height), bg: getComputedStyle(a).backgroundColor }; }")
    if not sos or sos['h'] < 44: prob.append('%s: o botão do SOS do cartão de emergência não tem 44 px de altura: %s' % (tela, sos))
    ver = r['det']['ver'] if r['det'] else []
    if ver:
        pg.evaluate("(i) => document.querySelector('[data-f6=ver][data-id=' + i + ']').click()", ver[0]); pg.wait_for_timeout(300)
        r2 = pg.evaluate(LE_F6)
        if not r2['det'] or r2['det']['id'] != ver[0] or r2['hash'] != '#id=' + ver[0]: prob.append('%s: o «ver também» (%s) devia abrir o outro item: %s %r' % (tela, ver[0], r2['det'] and r2['det']['id'], r2['hash']))
    pg.evaluate("() => document.querySelector('[data-f6=fecha]').click()"); pg.wait_for_timeout(300)
    r3 = pg.evaluate(LE_F6)
    if r3['det'] or len(r3['itens']) != len(FAQ_JSON['itens']) or r3['hash'] != '': prob.append('%s: fechar devia voltar à lista de %d itens sem endereço: detalhe %s, %d itens, %r' % (tela, len(FAQ_JSON['itens']), r3['det'] and r3['det']['id'], len(r3['itens']), r3['hash']))
    pg.evaluate("() => document.querySelector('[data-f6=item][data-id=MO-02]').click()"); pg.wait_for_timeout(300)
    r4 = pg.evaluate(LE_F6)
    if not r4['det'] or r4['det']['id'] != 'MO-02' or r4['det']['sos'] is not None: prob.append('%s: o item comum (MO-02) não tem botão do SOS: %s' % (tela, r4['det'] and r4['det']['sos']))
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def abre_chat_do_f6(b, tela, item, ia=True):
    """A F6 aberta com o Worker da IA de mentira; toca no item e em «PERGUNTAR AO BARCO»: a navegação real leva ao chat (Main ou H2) com o referrer da própria tela. Devolve (ctx, pg, erros, est, mensagens)."""
    ctx, pg, erros, est = abre_home(b, tela, ia=ia)
    try: pg.wait_for_function("() => document.querySelector('[data-f6=item]')", timeout=10000)
    except Exception: pass
    pg.evaluate("(i) => document.querySelector('[data-f6=item][data-id=' + i + ']').click()", item); pg.wait_for_timeout(300)
    pg.evaluate("() => document.querySelector('[data-f6=chat]').click()")
    try:
        pg.wait_for_url(re.compile(re.escape(CHAT_DE[plat(tela)])), timeout=15000)
        pg.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
        pg.wait_for_function("() => document.querySelectorAll('[data-home=msg][data-papel=bot]').length >= 1 && !document.querySelector('[data-capitao-pensando]')", timeout=20000)
    except Exception:
        pass
    pg.wait_for_timeout(400)
    return ctx, pg, erros, est, pg.evaluate(LE_MSGS)


def teste_f6_chat(b, tela):
    """F6 → chat (o toque numa pergunta do FAQ): a resposta é o item com o código e a fonte (ctx.faq do cérebro), o chat é o da plataforma, o botão leva ao item no FAQ, e NENHUM pedido sai ao Worker da IA (a IA entra nele
    com o item como trecho [1] na Fase 6); o cartão de emergência (EM-06) abre local, abre a janela de conversa em emergência (como o SOS) e não grava no diário; o de salvatagem (EM-09) não abre a janela."""
    prob = []
    p = plat(tela)
    for item in ('MO-02', 'EM-06', 'EM-09', 'EP-02'):
        it = FAQ_ITENS[item]
        ctx, pg, erros, est, msgs = abre_chat_do_f6(b, tela, item)
        bots = [m for m in msgs if m['papel'] == 'bot']
        st = pg.evaluate(LE_ESTADO_HOME)
        rot = '%s → %s %s' % (tela, CHAT_DE[p].split('.')[0], item)
        esp0 = lin(('' if it.get('emerg') else it['titulo'] + ' — ') + it['resposta'])[:60]
        corpo = re.sub(r'^CAPITÃO IA\s*', '', bots[0]['txt']) if bots else ''   # (a mensagem abre com o nome de quem responde)
        if len(bots) != 1 or not corpo.startswith(esp0): prob.append('%s: a resposta devia ser o item (começa por %r): %s' % (rot, esp0, bots and bots[0]['txt'][:80]))
        elif ('Fonte: FAQ dos equipamentos ' + item) not in bots[0]['txt']: prob.append('%s: a resposta não traz a fonte com o código (FAQ dos equipamentos %s): %s' % (rot, item, bots[0]['txt'][-160:]))
        if bots and not any(a['l'] == 'Abrir %s no FAQ' % item and a['href'] == f6_arq(tela) + '#id=' + item for a in bots[0]['acoes']): prob.append('%s: falta a ação «Abrir %s no FAQ» → %s#id=%s: %s' % (rot, item, f6_arq(tela), item, bots[0]['acoes']))
        if bots and any(a['l'] == 'Abrir SOS' for a in bots[0]['acoes']) != bool(it.get('emerg')): prob.append('%s: o botão «Abrir SOS» só vem no cartão de emergência: %s' % (rot, bots[0]['acoes']))
        if est['pedidos']: prob.append('%s: o toque no FAQ chamou a IA (%d pedido(s) ao Worker)' % (rot, len(est['pedidos'])))
        if st['emerg'] != bool(it.get('emerg') and item != 'EM-09'): prob.append('%s: a janela de conversa em emergência está %s (esperado %s: abre com os cartões de emergência, menos o de salvatagem)' % (rot, st['emerg'], bool(it.get('emerg') and item != 'EM-09')))
        if st['diario']: prob.append('%s: abrir o FAQ gravou no diário: %s' % (rot, st['diario']))
        if st['url'].split('#')[0].endswith(CHAT_DE[p]) and '#' in st['url']: prob.append('%s: o endereço do chat devia ficar limpo depois da pergunta: %s' % (rot, st['url']))
        if it.get('emerg') and bots and (R_POSICAO.search(bots[0]['txt']) or R_NAV.search(bots[0]['txt']) or '710123456' in bots[0]['txt']): prob.append('%s: o cartão de emergência traz posição, rumo, velocidade, pessoas ou o MMSI do cadastro: %s' % (rot, bots[0]['txt'][:200]))
        ach = achados_termos(CHAT_DE[p], bots[0]['txt'] if bots else '')
        if ach: prob.append('%s: termo do §3 na resposta: %s' % (rot, ach))
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    # o link aberto direto (sem referrer: de fora do app) e com a IA ligada: o item também é a resposta; código que não existe cai na resposta normal; o código sem pergunta não faz nada
    chat = CHAT_DE[p].replace('.dc.html', '')
    for h, esp in (('#q=%s&faq=GE-02' % enc('Como ligo o gerador?'), 'GE-02'), ('#q=%s&faq=XX-99' % enc('Como ligo o gerador?'), None), ('#q=%s&faq=lixo' % enc('Como ligo o gerador?'), None), ('#faq=GE-02', None)):
        ctx, pg, erros, est = abre_home(b, chat, ia=True, hash_=h)
        pg.wait_for_timeout(2500)
        bots = [m for m in pg.evaluate(LE_MSGS) if m['papel'] == 'bot']
        txt = bots[-1]['txt'] if bots else ''
        if esp and ('Fonte: FAQ dos equipamentos ' + esp) not in txt: prob.append('%s %s: o link com o código devia responder com o item %s: %s' % (chat, h, esp, txt[-120:]))
        if not esp and h.startswith('#q=') and (not bots or 'FAQ dos equipamentos' in txt and ('XX-99' in txt or 'lixo' in txt)): prob.append('%s %s: código que não existe devia cair na resposta normal: %s' % (chat, h, txt[-120:]))
        if h == '#faq=GE-02' and bots: prob.append('%s %s: o código sem pergunta não devia responder nada (%d resposta)' % (chat, h, len(bots)))
        if erros: prob += ['%s %s: %s' % (chat, h, e) for e in erros[:2]]
        ctx.close()
    return prob


# ——— o hub F1 ———
LE_F1 = """() => { const lin = (s) => (s || '').replace(/\\s+/g, ' ').trim(), D = window.CapitaoDados, q = (s) => document.querySelector(s);
  const cartoes = [...document.querySelectorAll('[data-faq=cartao]')].map((a) => { const g = (n) => { const e = a.querySelector('[data-faq=c-' + n + ']'); return e ? lin(e.innerText) : null; };
    return { nome: g('nome'), chip: g('chip'), fab: g('fab'), sub: g('sub'), acao: g('acao'), fonte: g('fonte'), href: a.getAttribute('href'), corte: a.scrollHeight - a.clientHeight }; });
  return { cartoes, resultados: [...document.querySelectorAll('[data-faq=resultado]')].map((a) => ({ href: a.getAttribute('href'), txt: lin(a.innerText) })),
    verTodos: q('[data-faq=ver-todos]') ? { href: q('[data-faq=ver-todos]').getAttribute('href'), txt: lin(q('[data-faq=ver-todos]').innerText) } : null,
    eq: D.equipamentos.map((e) => ({ id: e.id, nome: e.nome, f: e.fabricante, m: e.modelo, seg: !!e.seguranca })), perguntasEl: ((D.faq || {}).eletronicos || {}).perguntas.map((p) => p.q),
    esperaBusca: window.CapitaoFAQ && window.CapitaoFAQ.pronto() ? window.CapitaoFAQ.busca('baliza', 20).map((r) => r.it.id) : null, texto: document.body.innerText,
    lateral: document.documentElement.scrollWidth - document.documentElement.clientWidth }; }"""


def teste_f1(b, tela):
    """F1 (o hub): o cartão do FAQ completo (F6) e o das emergências (F6#s=1) em cima, com o total do arquivo; plotters, áudio e VHF são UM cartão «Eletrônicos» (o F3, com o fabricante e o modelo de cada um vindos de
    D.equipamentos); nenhum cartão cortado; a busca é a dos 91 itens (resultado → F6#id=<código>, «Ver todos» → F6#busca=, Enter → chat); a 60 s e a 105 s, sem termo do §3."""
    prob = []
    p = plat(tela)
    f6, f3 = f6_arq(tela), 'F3-FAQ-Eletronicos%s.dc.html' % ('' if p == 'app' else '-Web')
    for fixo, depois in (('60', ''), ('105', ''), ('60', FABRICANTES_FALSOS)):
        ctx, pg, erros = abre_tela(b, tela, fixo=fixo, depois=depois)
        try: pg.wait_for_function("() => window.CapitaoFAQ && window.CapitaoFAQ.pronto()", timeout=10000)
        except Exception: prob.append('%s: o FAQ dos equipamentos não carregou' % tela)
        pg.wait_for_timeout(400)
        r = pg.evaluate(LE_F1)
        rot = '%s a %s s%s' % (tela, fixo, ' (fabricantes plantados)' if depois else '')
        eq = {e['id']: e for e in r['eq']}
        esp = ['FAQ completo dos equipamentos', 'Emergências'] + ['Eletrônicos' if e['id'] == 'eletronicos' else e['nome'] for e in r['eq'] if e['id'] not in ('audio', 'vhf')]
        nomes = [c['nome'] for c in r['cartoes']]
        if nomes != esp: prob.append('%s: os cartões são %s (esperado FAQ completo, Emergências e os equipamentos, com Plotters, Áudio e VHF num cartão só «Eletrônicos»)' % (rot, nomes)); ctx.close(); continue
        c = {x['nome']: x for x in r['cartoes']}
        tot = len(FAQ_JSON['itens'])
        a, em, el = c['FAQ completo dos equipamentos'], c['Emergências'], c['Eletrônicos']
        if a['href'] != f6 or a['chip'] != '%d ITENS' % tot or a['acao'] != 'Abrir o FAQ ›' or ('%d perguntas e respostas' % tot) not in a['fab']: prob.append('%s: o cartão do FAQ completo é %s (esperado → %s, chip %d ITENS)' % (rot, {k: a[k] for k in ('href', 'chip', 'fab')}, f6, tot))
        ids_em = [it['id'] for it in FAQ_JSON['itens'] if it.get('emerg')]
        if em['href'] != f6 + '#s=1' or em['chip'] != 'EMERGÊNCIA' or not em['fab'].startswith('%s a %s' % (ids_em[0], ids_em[-1])) or 'procedimento padrão — confirmar com o protocolo de bordo' not in em['fab']: prob.append('%s: o cartão das emergências é %s (esperado → %s#s=1, EM-01 a EM-09 e o rótulo do procedimento padrão)' % (rot, {k: em[k] for k in ('href', 'chip', 'fab')}, f6))
        if p == 'web' and not all(x in em['sub'] for x in ('MAYDAY', 'Homem ao mar', 'EPIRB')): prob.append('%s: o cartão das emergências não lista os cartões do arquivo: %r' % (rot, em['sub']))
        fabs = ' · '.join(fab_mod(eq[i]['f'], eq[i]['m']) for i in UNICO_ELETRONICOS)
        n_el = len(r['perguntasEl'])
        if el['href'] != f3 or el['fab'] != fabs or el['chip'] != 'PRONTO' or el['acao'] != '%d perguntas ›' % n_el: prob.append('%s: o cartão «Eletrônicos» é %s (esperado → %s sem #p=, «%s», PRONTO e %d perguntas)' % (rot, {k: el[k] for k in ('href', 'fab', 'chip', 'acao')}, f3, fabs, n_el))
        if p == 'web' and not all(any(w in q for q in r['perguntasEl']) and any(w in x for x in [el['sub']]) for w in ('VHF', 'Fusion')): prob.append('%s: o cartão «Eletrônicos» não lista as perguntas do VHF e do Fusion: %r' % (rot, el['sub']))
        cortados = [x['nome'] for x in r['cartoes'] if x['corte'] > 1]
        if cortados: prob.append('%s: cartão cortado: %s' % (rot, cortados))
        if r['lateral'] > 1: prob.append('%s: rola para o lado (%d px)' % (rot, r['lateral']))
        ach = achados_termos(tela, r['texto'])
        if ach: prob.append('%s: termo do §3: %s' % (rot, ach))
        if depois and not all(w in r['texto'] for w in ('Zyxeletro Mod9', 'Zyxaudio Mod9', 'Zyxvhf Mod9', 'Zyxgerador Mod9')): prob.append('%s: os fabricantes plantados não aparecem nos cartões: fabricante fixo no código' % rot)
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        if fixo == '105' or depois:
            ctx.close(); continue
        # a busca: os itens do arquivo (a busca do cérebro), cada um → F6#id=<código>; «Ver todos» → F6#busca=; Enter → o chat
        campo = '#faq-busca'
        pg.fill(campo, 'baliza'); pg.wait_for_timeout(350)
        r = pg.evaluate(LE_F1)
        ids = [re.search(r'#id=([A-Z]{2}-\d\d)$', x['href']).group(1) if re.search(r'#id=([A-Z]{2}-\d\d)$', x['href']) else None for x in r['resultados']]
        esp_ids = (r['esperaBusca'] or [])[:8 if p == 'web' else 6]
        if ids != esp_ids or 'EP-02' not in ids or any(not x['href'].startswith(f6 + '#id=') for x in r['resultados']): prob.append('%s: a busca «baliza» devia dar os itens do FAQ (%s) com o link F6#id=<código>: %s' % (tela, esp_ids, [x['href'] for x in r['resultados']]))
        if not r['verTodos'] or r['verTodos']['href'] != f6 + '#busca=baliza' or 'Ver todos no FAQ completo' not in r['verTodos']['txt']: prob.append('%s: falta o «Ver todos no FAQ completo» → %s#busca=baliza: %s' % (tela, f6, r['verTodos']))
        ach = achados_termos(tela, r['texto'])
        if ach: prob.append('%s: termo do §3 na busca: %s' % (tela, ach))
        pg.fill(campo, 'MAYDAY'); pg.wait_for_timeout(350)
        r = pg.evaluate(LE_F1)
        if not r['resultados'] or 'EM-01' not in r['resultados'][0]['href'] or 'EMERGÊNCIA' not in r['resultados'][0]['txt'] and p == 'web': prob.append('%s: a busca «MAYDAY» devia achar o cartão EM-01 primeiro (com a etiqueta EMERGÊNCIA na web): %s' % (tela, r['resultados'][:2]))
        pg.fill(campo, 'xyzzy'); pg.wait_for_timeout(350)
        r = pg.evaluate(LE_F1)
        if r['resultados'] or r['verTodos'] or ('Nenhum item do FAQ com “xyzzy”' not in r['texto'] and 'NENHUM ITEM NO FAQ' not in r['texto']): prob.append('%s: o que não existe devia dizer «Nenhum item do FAQ» e não oferecer o «Ver todos»: %s' % (tela, r['resultados'][:2]))
        pg.fill(campo, 'baliza'); pg.press(campo, 'Enter')
        try: pg.wait_for_url(re.compile(re.escape(CHAT_DE[p]) + '#q=baliza'), timeout=8000)
        except Exception: prob.append('%s: Enter na busca devia mandar a pergunta ao chat (%s#q=baliza): %s' % (tela, CHAT_DE[p], pg.url))
        ctx.close()
    return prob


# ——— os FAQs F2 a F5 ———
LE_F2F5 = """() => { """ + JS_BASE + """
  const rel = [...document.querySelectorAll('[data-faq=rel-k]')].map((k) => { const row = k.parentElement.parentElement; const g = (n) => { const e = row.querySelector('[data-faq=rel-' + n + ']'); return e ? lin(e.innerText) : ''; }; return { k: lin(k.innerText), s: g('s'), v: g('v') }; });
  const f = document.querySelector('[data-faq=f6]'), sub = document.querySelector('[data-faq=rel-sub]'), fonte = document.querySelector('[data-faq=rel-fonte]');
  return { rel, sub: sub ? lin(sub.innerText) : null, fonte: fonte ? lin(fonte.innerText) : null, f6: f ? f.getAttribute('href') : null, T, hora: I.hora, fonteTxt: I.fonteTxt, calc: I.calc || null,
    q: { gerador_ativo: q.gerador_ativo, seakeeper_ativo: q.seakeeper_ativo, climatizacao_ativa: q.climatizacao_ativa, ancora_estado: q.ancora_estado, estado: q.estado, local: q.local },
    eq: D.equipamentos.map((e) => ({ id: e.id, nome: e.nome, f: e.fabricante, m: e.modelo })), perguntas: ((D.faq || {})[@CHAVE@] || {}).perguntas || [], texto: document.body.innerText, lateral: document.documentElement.scrollWidth - document.documentElement.clientWidth }; }"""
CHAVE_FAQ = {'F2': 'estabilizador', 'F3': 'eletronicos', 'F4': 'gerador', 'F5': 'climatizacao'}


def nb_f2f5(x): return ('%.1f' % x).replace('.', ',')   # (não é o nb1 da C3: outro nome, o de lá tem 2 argumentos)


def esperado_f2f5(cod, r):
    """As linhas do estado a bordo que a tela tem de mostrar neste instante (o que a CapitaoAgora.fmt diz do quadro): {chave da linha: (valor, [trechos do subtítulo])}."""
    T, q, E = r['T'], r['q'], {e['id']: e for e in r['eq']}
    nome = lambda i, base: base + (' ' + E[i]['f'] if E[i]['f'] else '')
    lig = lambda v: 'LIGADO' if v else 'DESLIGADO'
    hora = 'leitura ' + r['hora']
    out = {}
    if cod == 'F2':
        out[nome('estabilizador', 'Estabilizador')] = (lig(q['seakeeper_ativo']), ['volante %s rpm (%s %%)' % (T['seakeeper_volante_rpm'], T['seakeeper_volante_pct']), hora])
    if cod in ('F2', 'F5'):
        out[nome('gerador', 'Gerador') + ' (energia AC)'] = (lig(q['gerador_ativo']), ['%s kW' % T['gerador_kw'], 'horímetro %s h' % T['gerador_horimetro_h'], hora])
    if cod == 'F3':
        out['GPS'] = ('%s satélites' % T['gps_satelites'], ['a posição está no plotter', hora])
        out['Posição do ferro (âncora)'] = (q['ancora_estado'].upper(), [q['estado'], hora])
        out['MMSI (cadastro do app)'] = ('710123456', ['No MAYDAY e no DSC: MMSI do rádio de bordo (etiqueta / Licença de Estação)'])
    if cod == 'F4':
        out['Horímetro do gerador'] = ('%s h' % T['gerador_horimetro_h'], ['ligado · %s kW' % T['gerador_kw'], hora])
    if cod == 'F5':
        out[nome('climatizacao', 'Climatização')] = ('LIGADA' if q['climatizacao_ativa'] else 'DESLIGADA', ['funcionando', hora])
    return out


def problemas_f2f5(r, tela, rot):
    prob = []
    cod = tela[:2]
    esp = esperado_f2f5(cod, r)
    linhas = {x['k']: x for x in r['rel']}
    for k, (v, subs) in esp.items():
        x = linhas.get(k)
        if not x: prob.append('%s: falta a linha «%s» no estado a bordo: %s' % (rot, k, list(linhas))); continue
        if x['v'] != v: prob.append('%s: «%s» diz %r (esperado %r, o quadro de agora)' % (rot, k, x['v'], v))
        for s in subs:
            if s not in x['s']: prob.append('%s: «%s»: o subtítulo %r não tem %r' % (rot, k, x['s'], s))
    if r['sub'] != 'Telemetria ao vivo · ' + r['hora']: prob.append('%s: a fonte do estado a bordo diz %r (esperado «Telemetria ao vivo · %s»)' % (rot, r['sub'], r['hora']))
    if cod == 'F4':   # as horas que faltam para a revisão: as do instante (o horímetro de agora), não as da agenda gerada
        f = (r['calc'] or {}).get('faltam', {}).get('gerador-revisao')
        if f is None or not any('faltam %s h' % nb_f2f5(f) in x['s'] for x in r['rel']): prob.append('%s: a revisão do gerador devia dizer «faltam %s h» (o horímetro de agora): %s' % (rot, f and nb_f2f5(f), [x['s'] for x in r['rel'] if 'faltam' in x['s']]))
    if r['f6'] != f6_arq(tela) + F6_DE[cod]: prob.append('%s: o link do FAQ completo é %r (esperado %s%s)' % (rot, r['f6'], f6_arq(tela), F6_DE[cod]))
    if 'Manual do fabricante' in r['texto']: prob.append('%s: ainda tem a linha «Manual do fabricante»' % rot)
    if re.search(R_POSICAO.pattern, ' | '.join(x['s'] + ' ' + x['v'] for x in r['rel'])): prob.append('%s: o estado a bordo traz coordenada' % rot)
    ach = achados_termos(tela, r['texto'])
    if ach: prob.append('%s: termo do §3: %s' % (rot, ach))
    if r['lateral'] > 1: prob.append('%s: rola para o lado (%d px)' % (rot, r['lateral']))
    return prob


def teste_f2f5(b, tela):
    """F2 a F5 (web e app): o estado a bordo é o do INSTANTE a 60 e a 105 s (o gerador ligado com a potência e o horímetro, o estabilizador com o volante, o GPS com os satélites e sem coordenada, o ferro recolhido, a
    climatização, as horas que faltam para a revisão do gerador), o fabricante e o modelo vêm de D.equipamentos (plantados, aparecem), sem rótulo nem «Manual do fabricante», com o link do FAQ completo (F6) na seção
    certa; a tela anda sozinha e só mexe no DOM quando o texto muda; o Executado vale; com simulacao false mostra a última leitura salva."""
    prob = []
    cod = tela[:2]
    js = LE_F2F5.replace('@CHAVE@', json.dumps(CHAVE_FAQ[cod]))
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_tela(b, tela, fixo=fixo)
        r = pg.evaluate(js)
        rot = '%s a %s s' % (tela, fixo)
        prob += problemas_f2f5(r, tela, rot)
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    # os fabricantes plantados aparecem (nada fixo na tela): no estado a bordo e na linha do equipamento; com D.demo ligado, nenhum DEMO
    ctx, pg, erros = abre_tela(b, tela, depois=FABRICANTES_FALSOS + 'window.CapitaoDados.demo = true;')
    r = pg.evaluate(js)
    z = {'F2': ['Zyxestab Mod9', 'Estabilizador Zyxestab', 'Gerador Zyxgerador (energia AC)'], 'F3': ['Zyxeletro Mod9', 'Zyxaudio Mod9', 'Zyxvhf Mod9'], 'F4': ['Zyxgerador Mod9'], 'F5': ['Zyxclima Mod9', 'Climatização Zyxclima', 'Gerador Zyxgerador (energia AC)']}[cod]
    falta = [x for x in z if x not in r['texto']]
    if falta: prob.append('%s: os fabricantes plantados não aparecem (%s): fabricante fixo no código' % (tela, falta))
    if re.search(r'\bDEMO\b|demonstra', r['texto'], re.I): prob.append('%s: com D.demo ligado a tela diz DEMO ou demonstração' % tela)
    ctx.close()
    # sem congelar: a hora da fonte anda (assina o capitao-telemetria); congelada, o DOM do estado a bordo não muda em 3,5 s (setState só quando o texto muda)
    ctx, pg, erros = abre_tela(b, tela, fixo=None)
    subs = set()
    for _ in range(4):
        subs.add(pg.evaluate("() => document.querySelector('[data-faq=rel-sub]').innerText")); pg.wait_for_timeout(1100)
    if len(subs) < 2: prob.append('%s: a fonte do estado a bordo não mudou em 4,4 s sem congelar o replay: %s' % (tela, subs))
    ctx.close()
    ctx, pg, erros = abre_tela(b, tela, fixo='60')
    n = pg.evaluate("""() => new Promise((ok) => { let n = 0; const alvo = document.querySelector('[data-faq=rel-k]').closest('section'), mo = new MutationObserver((l) => { n += l.length; });
      mo.observe(alvo, { subtree: true, childList: true, characterData: true, attributes: true }); setTimeout(() => { mo.disconnect(); ok(n); }, 3500); })""")
    if n: prob.append('%s: o estado a bordo mexeu no DOM %d vezes em 3,5 s com o instante congelado (redesenha sem o texto mudar)' % (tela, n))
    ctx.close()
    # o Executado (F4: a revisão do gerador marcada na Manutenção vira EXECUTADO na tela)
    if cod == 'F4':
        ex = json.dumps({'gerador-revisao': {'d': '10/11', 't': '09:00', 'iso': '2026-11-10T09:00:00-03:00', 'sim': True}})
        ctx, pg, erros = abre_tela(b, tela, ls={'capitao.executado.v1': ex})
        r = pg.evaluate(js)
        if not any(x['v'] == 'EXECUTADO 10/11' for x in r['rel']): prob.append('%s: a revisão executada (Executado do aparelho) devia aparecer como «EXECUTADO 10/11»: %s' % (tela, [x['v'] for x in r['rel']]))
        ctx.close()
    # simulacao false: a última leitura salva (o quadro do snapshot), sem erro
    ctx, pg, erros = abre_tela(b, tela, depois='window.CapitaoDados.simulacao = false;')
    sub = pg.evaluate("() => (document.querySelector('[data-faq=rel-sub]') || {}).innerText")
    if not (sub or '').startswith('Última leitura'): prob.append('%s: com simulacao false a fonte devia ser «Última leitura · …»: %r' % (tela, sub))
    if cod == 'F3':   # a última leitura salva: o ferro lançado e o cabo do snapshot aninhado («LANÇADA · 30 m»)
        x = pg.evaluate(js)
        anc = pg.evaluate("() => window.CapitaoDados.snapshot.ancora")
        esp = '%s · %d m' % (anc['estado'].upper(), anc['cabo_m'])
        v = [l['v'] for l in x['rel'] if l['k'] == 'Posição do ferro (âncora)']
        if v != [esp]: prob.append('%s: com simulacao false o ferro devia ser %r (o do snapshot, com o cabo): %s' % (tela, esp, v))
    if erros: prob += ['%s (simulacao false): %s' % (tela, e) for e in erros[:2]]
    ctx.close()
    return prob


# ——— o código ———
def le_arq(a):
    t = open(os.path.join(RAIZ, a), encoding='utf-8', newline='').read()
    for velho, novo in MUT_ARQ.get(a, []): t = t.replace(velho, novo, 1)
    return t


GEOM_SVG = re.compile(r'<(?:svg|path|circle|line|rect|ellipse|polyline|polygon|g)\b[^>]*\b(?:d|x|y|x1|x2|y1|y2|cx|cy|r|rx|ry|width|height|viewBox|points|transform)="[^"]*\{\{')
ESCRITA = re.compile(r'addDiario|markExec|addDoc|addAbast|localStorage\s*\.\s*setItem|\.speak\(|speechSynthesis|location\s*\.\s*(?:href|assign|replace)\s*=|window\s*\.\s*open')


def teste_faq_codigo():
    """O código das 12 telas e do capitao-faq.js: nada de rótulo, snapshot, D.demo nem fabricante fixo; os ouvintes assinados e removidos; nenhum setInterval a mais; a tela só redesenha com o texto novo e com a aba à vista; a F6 e o módulo
    não gravam, não falam nem trocam de tela; o módulo não corre no SOS, não usa lookbehind e não busca o arquivo (é do cérebro); nenhum {{…}} em atributo geométrico de SVG; o registro (TELAS, CORE, lista, mapa APP)."""
    prob = []
    for a in ['F1-FAQ-Hub-Web.dc.html', 'F1-FAQ-Hub.dc.html'] + [t + '.dc.html' for t in TELAS_F2F5] + [t + '.dc.html' for t in TELAS_F6]:
        h = le_arq(a)
        n = a.split('.')[0]
        cod = re.sub(r'//[^\n]*', '', h[h.find('<script type="text/x-dc"'):])
        fora_reserva = '\n'.join(l for l in cod.split('\n') if 'reserva' not in l)   # (o snapshot aninhado só na linha do ramo de reserva: o cabo do ferro da F3 com simulacao false, como na A1)
        if re.search(r'D\.demo|\.demo\b|DEMO|D\.aviso|D\.snapshot|\.snapshot\b', fora_reserva): prob.append('%s: lê D.demo, D.aviso ou D.snapshot (ou escreve DEMO) no código' % n)
        if MARCAS_FIXAS.search(cod): prob.append('%s: fabricante fixo no código: %s' % (n, MARCAS_FIXAS.search(cod).group(0)))
        for l in cod.split('\n'):   # SEM DADOS / SEM LEITURA só no ramo simulacao false (falta() ou sim ?) e na constante SD
            if re.search(r'SEM (?:DADOS|LEITURA)', l) and not re.search(r'falta\(|sim \?|const SD = ', l): prob.append('%s: rótulo fora do ramo simulacao false: %s' % (n, l.strip()[:100]))
        if GEOM_SVG.search(h): prob.append('%s: {{…}} em atributo geométrico de SVG' % n)
        if re.search(r'Manual do fabricante|manualFab|seloDemo|chipDemo', h): prob.append('%s: ainda tem «Manual do fabricante» ou o selo violeta de DEMO' % n)
        if a.startswith('F6-'):
            if ESCRITA.search(cod): prob.append('%s: grava, fala ou troca de tela (%s): a F6 só lê' % (n, ESCRITA.search(cod).group(0)))
            if re.search(r"'capitao-telemetria'|CapitaoReplay|CapitaoAlertas", cod): prob.append('%s: a F6 não lê leitura de bordo (nem assina a telemetria)' % n)
            mont, desm = cod.find('componentDidMount'), cod.find('componentWillUnmount')
            for ev in ('hashchange', 'capitao-faq'):
                if "'%s'" % ev not in cod[mont:desm] or "'%s'" % ev not in cod[desm:desm + 500]: prob.append('%s: não assina o %s no componentDidMount e remove no componentWillUnmount' % (n, ev))
            if cod.count('setInterval') != 1 or 'clearInterval(this._b)' not in cod[desm:desm + 500]: prob.append('%s: setInterval a mais (só o de espera do cérebro e do módulo, limpo ao desmontar)' % n)
            for s in ('capitao-brain.js', 'capitao-faq.js'):
                if '<script src="./%s"></script>' % s not in h: prob.append('%s: o <head> não carrega o %s' % (n, s))
        elif a.startswith('F1-'):
            mont, desm = cod.find('componentDidMount'), cod.find('componentWillUnmount')
            if "'capitao-faq'" not in cod[mont:desm] or "'capitao-faq'" not in cod[desm:desm + 400]: prob.append('%s: não assina o capitao-faq no componentDidMount e remove no componentWillUnmount' % n)
            if cod.count('setInterval') != 1: prob.append('%s: setInterval a mais' % n)
            for s in ('capitao-brain.js', 'capitao-faq.js'):
                if '<script src="./%s"></script>' % s not in h: prob.append('%s: o <head> não carrega o %s' % (n, s))
        else:
            mont, desm = cod.find('componentDidMount'), cod.find('componentWillUnmount')
            for ev in ('capitao-telemetria', 'capitao-rebase'):
                if "'%s'" % ev not in cod[mont:desm] or "'%s'" % ev not in cod[desm:desm + 700]: prob.append('%s: não assina o %s no componentDidMount e remove no componentWillUnmount' % (n, ev))
            if 'setInterval' in cod: prob.append('%s: setInterval novo (a tela anda pelo evento da telemetria)' % n)
            if 'if (document.hidden) return;' not in cod or 'if (k !== this._bk)' not in cod: prob.append('%s: o tique não pausa com document.hidden ou redesenha sem comparar o texto' % n)
            if 'I.calc.faltam' not in cod and n.startswith('F4'): prob.append('%s: as horas que faltam não vêm do instante (calc.faltam)' % n)
    for a in ('Main.dc.html', 'H2-Home-Mobile.dc.html'):   # o toque no FAQ: o código (#faq=) chega ao cérebro, espera o arquivo (até 3 s) e não chama a IA (a Fase 6 liga com o item como trecho [1])
        h = le_arq(a)
        n = a.split('.')[0]
        if 'this.ask(h.q, null, true, faq ? { faq: faq } : null)' not in h or 'emergencia: emg, faq: faq }' not in h: prob.append('%s: o código do FAQ (#faq=) não chega ao cérebro (ctx.faq)' % n)
        if 'Promise.race([atual().carregaFaq().then(() => atual().carregaFaq()), new Promise((ok) => setTimeout(ok, 3000))])' not in h or 'faqPronto && atual().faqPronto()' not in h: prob.append('%s: não espera o arquivo do FAQ (até 3 s) antes de responder pelo código' % n)
        if 'const pede = !att && interno && !faq &&' not in h: prob.append('%s: o toque no FAQ chama a IA (a Fase 6 liga, com o item como trecho [1])' % n)
        if "(a.key === 'base' || a.key === 'faqEquip')" not in h or "a.key === 'base' || a.key === 'faqEquip' ? a.actions : []" not in h: prob.append('%s: a IA sem dado troca o item do FAQ (o item de faqEquip deve ficar, como o trecho do guia) ou perde as ações' % n)
    m = le_arq('capitao-faq.js')
    cod = re.sub(r'/\*.*?\*/', '', m, flags=re.S)
    cod = re.sub(r'//[^\n]*', '', cod)
    if 'if (EM_SOS || window.CapitaoFAQ) return;' not in cod: prob.append('capitao-faq.js: sai sem definir nada numa rota /SOS- só se o arquivo conferir EM_SOS')
    if '(?<' in cod: prob.append('capitao-faq.js: lookbehind (iOS < 16.4)')
    if re.search(r'\bfetch\(|XMLHttpRequest', cod): prob.append('capitao-faq.js: busca o arquivo por conta própria (é do cérebro: B.carregaFaq)')
    if ESCRITA.search(cod) or re.search(r'localStorage|sessionStorage', cod): prob.append('capitao-faq.js: grava, fala ou troca de tela: %s' % (ESCRITA.search(cod) or re.search(r'localStorage|sessionStorage', cod)).group(0))
    if re.search(r'SEM (?:DADOS|LEITURA)|\bDEMO\b|snapshot|D\.demo|fict[ií]ci', cod): prob.append('capitao-faq.js: rótulo, snapshot ou D.demo')
    for ap in ('faqBusca', 'faqDados', 'faqItem', 'carregaFaq'):
        if ap not in cod: prob.append('capitao-faq.js: não usa o %s do cérebro' % ap)
    # o registro das duas telas novas e do módulo
    sw = le_arq('sw.js')
    tel = re.search(r'const TELAS = \[(.*?)\];', sw, re.S).group(1)
    for t in TELAS_F6:
        if "'%s'" % t not in tel: prob.append('sw.js: %s fora das TELAS (não abre offline)' % t)
    if "'./capitao-faq.js'" not in re.search(r'const CORE = \[(.*?)\]\.concat', sw, re.S).group(1): prob.append('sw.js: ./capitao-faq.js fora do CORE (a F6 não abre offline)')
    idx = le_arq('index.html')
    for t in TELAS_F6:
        if 'href="%s.dc.html"' % t not in idx: prob.append('index.html: %s fora da lista de telas' % t)
    app = le_arq('capitao-app.js')
    if "'F6-FAQ-Equipamentos-Web': 'F6-FAQ-Equipamentos'" not in app: prob.append('capitao-app.js: o par F6 web → app fora do mapa APP')
    for t in TELAS_F6:
        if not os.path.exists(os.path.join(RAIZ, t + '.dc.html')): prob.append('%s.dc.html não existe' % t)
    return prob


def teste_chat_faq(b, tela):
    """Main e H2: a pergunta digitada que cai no FAQ (a «sonda mostrando pouca profundidade» é o EL-08) vai à IA como o trecho do guia; a IA que responde SEM DADOS NÃO troca o item (o texto local, com o código, a fonte e as ações,
    fica); a IA que responde com dado troca o texto e guarda as ações do item («Abrir EL-08 no FAQ»); o toque no FAQ (#q=…&faq=…, de dentro do app) nunca chama a IA."""
    prob = []
    p = plat(tela)
    q = 'sonda mostrando pouca profundidade'
    for texto, deve_trocar in (('SEM DADOS — isso não está nas fontes de bordo.', False), ('Resposta da IA: confira a sonda e a carta.', True)):
        ctx, pg, erros, est = abre_home(b, tela, texto=texto)
        msgs = pergunta_home(pg, tela, q)
        bots = [m for m in msgs if m['papel'] == 'bot']
        rot = '%s · IA %s' % (tela, 'sem dado' if not deve_trocar else 'com dado')
        if len(est['pedidos']) != 1: prob.append('%s: a pergunta do FAQ devia ir à IA 1 vez (como o trecho do guia): %d' % (rot, len(est['pedidos'])))
        if not bots: prob.append('%s: sem resposta' % rot)
        else:
            tx = bots[-1]['txt']
            if deve_trocar and 'Resposta da IA: confira a sonda e a carta.' not in tx: prob.append('%s: a IA com dado devia trocar o texto: %s' % (rot, tx[:120]))
            if not deve_trocar and ('SEM DADOS' in tx or 'Profundidade mínima na sonda' not in tx or 'FAQ dos equipamentos EL-08' not in tx): prob.append('%s: a IA sem dado devia deixar o item local (EL-08, com a fonte): %s' % (rot, tx[:160]))
            if not any(a['l'] == 'Abrir EL-08 no FAQ' and a['href'] == f6_arq(tela) + '#id=EL-08' for a in bots[-1]['acoes']): prob.append('%s: a resposta perdeu a ação «Abrir EL-08 no FAQ»: %s' % (rot, bots[-1]['acoes']))
        if erros: prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    return prob


def teste_chat_faq_lento(b, tela):
    """Main e H2: o endereço #q=…&faq=<código> espera o arquivo do FAQ chegar (0,8 s por pedido): a resposta é o item, com o código e a fonte, e não a resposta de outra rota."""
    prob = []
    p = plat(tela)
    it = FAQ_ITENS['MO-02']
    ctx = b.new_context(viewport={'width': 390 if p == 'app' else 1440, 'height': 844 if p == 'app' else 900}, user_agent=MOBILE_UA if p == 'app' else None, is_mobile=p == 'app', has_touch=p == 'app', service_workers='block')
    ctx.add_init_script(SESSAO + ";localStorage.setItem('capitao.plataforma.v1','%s');localStorage.setItem('capitao.replay.fixo','60');" % p)
    def lenta(route):
        time.sleep(0.8); route.continue_()
    ctx.route('**/faq-equipamentos.json', lenta)
    aplica_mut(ctx)
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
    pg.goto(BASE + tela + '.dc.html#q=' + enc(it['pergunta']) + '&faq=MO-02', wait_until='load')
    try: pg.wait_for_function("() => document.querySelectorAll('[data-home=msg][data-papel=bot]').length >= 1 && !document.querySelector('[data-capitao-pensando]')", timeout=20000)
    except Exception: pass
    pg.wait_for_timeout(500)
    bots = [m for m in pg.evaluate(LE_MSGS) if m['papel'] == 'bot']
    tx = bots[0]['txt'] if bots else ''
    if 'Fonte: FAQ dos equipamentos MO-02' not in tx or it['titulo'] not in tx: prob.append('%s: com o arquivo do FAQ lento a resposta devia ser o item MO-02 (a tela espera o arquivo): %s' % (tela, tx[:160]))
    if erros: prob += erros[:2]
    ctx.close()
    return prob


def p4h_conferencias(b, lista):
    """[(nome, problemas)] das conferências da P4H para as telas da rodada."""
    out = []
    if any(t in lista for t in TELAS_P4H): out.append(('código das telas, do capitao-faq.js e o registro (TELAS, CORE, lista, mapa APP)', teste_faq_codigo()))
    for tela in [t for t in TELAS_F6 if t in lista]:
        out.append((tela + ' · a lista, os filtros por seção, o glossário e a varredura do §3', teste_f6_lista(b, tela)))
        out.append((tela + ' · os endereços (#id=, #s=, #busca=, #glossario) e a troca com a tela aberta', teste_f6_enderecos(b, tela)))
        out.append((tela + ' · a busca (código, frase, palavra solta, seção, limpar)', teste_f6_busca(b, tela)))
        out.append((tela + ' · os 91 itens abertos um a um', teste_f6_itens(b, tela)))
        out.append((tela + ' · o arquivo lento (a 2ª cópia do cérebro) e sem rede', teste_f6_carga_lenta(b, tela)))
        out.append((tela + ' · o toque: abrir, fechar, ver também e o botão do SOS', teste_f6_navegacao(b, tela)))
        out.append((tela + ' · do FAQ ao chat: o item com o código e a fonte, sem IA, e a janela de emergência', teste_f6_chat(b, tela)))
    for tela in [t for t in TELAS_CHAT_FAQ if t in lista]:
        out.append((tela + ' · a pergunta do FAQ na IA: o item fica com a IA sem dado e guarda as ações', teste_chat_faq(b, tela)))
        out.append((tela + ' · o código do FAQ com o arquivo lento: a tela espera o arquivo', teste_chat_faq_lento(b, tela)))
    for tela in [t for t in TELAS_F1 if t in lista]:
        out.append((tela + ' · o hub: FAQ completo, emergências, o cartão Eletrônicos único e a busca nos 91 itens', teste_f1(b, tela)))
    for tela in [t for t in TELAS_F2F5 if t in lista]:
        out.append((tela + ' · o estado a bordo do instante, os fabricantes de D.equipamentos, o link do FAQ completo e o ramo simulacao false', teste_f2f5(b, tela)))
    return out


MUTANTES_P4H = [
    # —— capitao-faq.js (o modelo da F6 e o que o hub usa) ——
    ('o código (EM-06) não acha o item', 'capitao-faq.js', [("m = COD.exec(t.toUpperCase());", "m = null;")], 'busca'),
    ('a palavra solta (baliza) não acha nada (sem o texto no título)', 'capitao-faq.js', [("if (!achados.length) achados = porTexto(t, d);", "")], 'busca'),
    ('a seção não filtra a busca', 'capitao-faq.js', [("return achados.filter(function (r) { return naSecao(r.it, sec); }).slice(0, n || 40);", "return achados.slice(0, n || 40);")], 'busca'),
    ('o link do chat sem o código do item (#faq=)', 'capitao-faq.js', [("+ '&faq=' + encodeURIComponent(it.id)", "+ ''")], 'itens'),
    ('o link do chat com o título no lugar da pergunta', 'capitao-faq.js', [("encodeURIComponent(it.pergunta || it.titulo || '')", "encodeURIComponent(it.titulo || '')")], 'itens'),
    ('o grupo «Eletrônicos» (#s=6,7) sem nome', 'capitao-faq.js', [("var GRUPOS = { '6,7': 'Eletrônicos' };", "var GRUPOS = {};")], 'enderecos'),
    ('a lista de seções fora de ordem (#s=7,6) não vira o grupo', 'capitao-faq.js', [(".sort(function (p, q) { return p - q; })", "")], 'enderecos'),
    ('a seção que não existe (#s=99) vira lista vazia', 'capitao-faq.js', [("if (typeof sec === 'number' && sec && conhecidas.indexOf(sec) === -1) sec = 0;", "")], 'enderecos'),
    ('o glossário sem os termos', 'capitao-faq.js', [("vm.termos = (d.glossario || [])", "vm.termos = ([])")], 'lista'),
    ('o passo a passo do item cortado nos 3 primeiros', 'capitao-faq.js', [("passos: (it.passos || []).map(function (p, i) { return { n: String(i + 1), t: p }; })", "passos: (it.passos || []).slice(0, 3).map(function (p, i) { return { n: String(i + 1), t: p }; })")], 'itens'),
    ('o «ver também» do item some', 'capitao-faq.js', [("ver: (it.ver || []).map(", "ver: ([]).map(")], 'itens'),
    ('o SOS do app aponta para o SOS do computador', 'capitao-faq.js', [("sos: app ? 'S2-SOS-Mobile.dc.html' : 'S1-SOS-Web.dc.html'", "sos: 'S1-SOS-Web.dc.html'")], 'itens_app'),
    ('o «Fechar» do item não fecha', 'capitao-faq.js', [("fecha: function () { set({ sel: null }); }", "fecha: function () {}")], 'navegacao'),
    ('a 2ª cópia do cérebro deixa a F6 em «Carregando…» (sem repetir o pedido ao cérebro de agora)', 'capitao-faq.js', [("if (!d && tent++ < 3) return uma();", "")], 'lista_carga'),
    # —— F6 ——
    ('a F6 web não põe o código do item no endereço', 'F6-FAQ-Equipamentos-Web.dc.html', [("try { history.replaceState(null, '', location.pathname + location.search + h); } catch (e) {}", "")], 'navegacao'),
    ('a F6 web não remove o ouvinte do endereço ao desmontar', 'F6-FAQ-Equipamentos-Web.dc.html', [("    window.removeEventListener('hashchange', this._hash);\n", "")], 'codigo'),
    ('a F6 do app deixa a lista aberta com o item (uma coluna)', 'F6-FAQ-Equipamentos.dc.html', [("mostraLista: !vm.carregando && !vm.glossario && !vm.detalhe,", "mostraLista: !vm.carregando && !vm.glossario,")], 'navegacao_app'),
    ('a F6 do app não remove o ouvinte do FAQ ao desmontar', 'F6-FAQ-Equipamentos.dc.html', [("    window.removeEventListener('capitao-faq', this._faq);\n", "")], 'codigo'),
    # —— o chat (o toque no FAQ) ——
    ('a Main não passa o código do FAQ ao cérebro', 'Main.dc.html', [("this.ask(h.q, null, true, faq ? { faq: faq } : null)", "this.ask(h.q, null, true, null)")], 'chat_web'),
    ('a H2 não passa o código do FAQ ao cérebro', 'H2-Home-Mobile.dc.html', [("this.ask(h.q, null, true, faq ? { faq: faq } : null)", "this.ask(h.q, null, true, null)")], 'chat_app'),
    ('a Main chama a IA no toque do FAQ', 'Main.dc.html', [("const pede = !att && interno && !faq && !!IA", "const pede = !att && interno && !!IA")], 'chat_web'),
    ('a H2 chama a IA no toque do FAQ', 'H2-Home-Mobile.dc.html', [("const pede = !att && interno && !faq && !!IA", "const pede = !att && interno && !!IA")], 'chat_app'),
    ('a Main não espera o arquivo do FAQ antes de responder pelo código', 'Main.dc.html', [("if (faq && atual().carregaFaq && !pronto()) Promise.race", "if (false) Promise.race")], 'lento_web'),
    ('a H2 não espera o arquivo do FAQ antes de responder pelo código', 'H2-Home-Mobile.dc.html', [("if (faq && atual().carregaFaq && !pronto()) Promise.race", "if (false) Promise.race")], 'lento_app'),
    ('a IA sem dado troca o item do FAQ na Main', 'Main.dc.html', [("if (r && !(r.semDados && (a.key === 'base' || a.key === 'faqEquip'))) {", "if (r && !(r.semDados && a.key === 'base')) {")], 'semdados_web'),
    ('a IA sem dado troca o item do FAQ na H2', 'H2-Home-Mobile.dc.html', [("if (r && !(r.semDados && (a.key === 'base' || a.key === 'faqEquip'))) {", "if (r && !(r.semDados && a.key === 'base')) {")], 'semdados_app'),
    # —— o hub F1 ——
    ('o hub web com os cartões do áudio e do VHF (o Eletrônicos não é único)', 'F1-FAQ-Hub-Web.dc.html', [("EQ.filter((e) => e.id !== 'audio' && e.id !== 'vhf')", "EQ")], 'f1_web'),
    ('o hub do app com os cartões do áudio e do VHF (o Eletrônicos não é único)', 'F1-FAQ-Hub.dc.html', [("EQ.filter((e) => e.id !== 'audio' && e.id !== 'vhf')", "EQ")], 'f1_app'),
    ('o cartão das emergências abre o FAQ inteiro', 'F1-FAQ-Hub-Web.dc.html', [("href: this.f6('#s=1')", "href: this.f6('')")], 'f1_web'),
    ('o cartão das emergências do app abre os motores', 'F1-FAQ-Hub.dc.html', [("href: this.f6('#s=1')", "href: this.f6('#s=2')")], 'f1_app'),
    ('a busca do hub não acha nada', 'F1-FAQ-Hub-Web.dc.html', [("return F.busca(busca, CFG.max).map((r) => r.it);", "return [];")], 'f1_web'),
    ('o hub sem o «Ver todos no FAQ completo»', 'F1-FAQ-Hub-Web.dc.html', [("verTodos: nR > 0,", "verTodos: false,")], 'f1_web'),
    ('o cartão Eletrônicos só com o fabricante dos plotters (fabricante fixo no código)', 'F1-FAQ-Hub-Web.dc.html', [(".map(fabMod).join(' · ')", ".slice(0, 1).map(fabMod).join(' · ')")], 'f1_web'),
    ('o total do cartão do FAQ completo errado', 'F1-FAQ-Hub-Web.dc.html', [("chip: D6 ? tot + ' ITENS' : 'FAQ'", "chip: D6 ? (tot - 1) + ' ITENS' : 'FAQ'")], 'f1_web'),
    ('o hub com a regra antiga («a resposta é SEM DADOS…») também na simulação', 'F1-FAQ-Hub-Web.dc.html', [("regra: sim ? 'cada resposta cita", "regra: false ? 'cada resposta cita")], 'f1_web'),
    # —— F2 a F5 ——
    ('a F2 web sem a potência do gerador no estado a bordo', 'F2-FAQ-Estabilizador-Web.dc.html', [("[l === 'ligado' && kw !== null ? kw + ' kW' : null, h !== null ? 'horímetro ' + h + ' h' : null]", "[h !== null ? 'horímetro ' + h + ' h' : null]")], 'f2f5_web:F2-FAQ-Estabilizador-Web'),
    ('a F2 do app com o fabricante do estabilizador fixo', 'F2-FAQ-Estabilizador.dc.html', [("linha(nomeEq('estabilizador', 'Estabilizador'),", "linha('Estabilizador Seakeeper',")], 'f2f5:F2-FAQ-Estabilizador'),
    ('a F3 do app sem o cabo do ferro do snapshot na última leitura', 'F3-FAQ-Eletronicos.dc.html', [("reserva && typeof ((D.snapshot || {}).ancora || {}).cabo_m === 'number' ? ' · ' + nb(((D.snapshot || {}).ancora || {}).cabo_m, 0) + ' m' : '';", "false ? '' : '';")], 'f2f5:F3-FAQ-Eletronicos'),
    ('a F3 web com a coordenada no GPS', 'F3-FAQ-Eletronicos-Web.dc.html', [("'a posição está no plotter' + hora", "c('lat') + ' ' + c('lon') + hora")], 'f2f5_web:F3-FAQ-Eletronicos-Web'),
    ('a F3 do app com o ferro lançado de reserva (não o do quadro)', 'F3-FAQ-Eletronicos.dc.html', [("const e = q && typeof q.ancora_estado === 'string' ? q.ancora_estado : null", "const e = 'lançada'")], 'f2f5:F3-FAQ-Eletronicos'),
    ('a F4 web com as horas da agenda e não as do instante', 'F4-FAQ-Gerador-Web.dc.html', [("const f = I && I.calc && I.calc.faltam ? I.calc.faltam[t.id] : undefined;", "const f = undefined;")], 'f2f5_web:F4-FAQ-Gerador-Web'),
    ('a F4 do app com o horímetro do gerador fixo', 'F4-FAQ-Gerador.dc.html', [("linha('Horímetro do gerador', h !== null ? h + ' h' : null,", "linha('Horímetro do gerador', '1.236,4 h',")], 'f2f5:F4-FAQ-Gerador'),
    ('a F5 web não assina a telemetria', 'F5-FAQ-Climatizacao-Web.dc.html', [("['capitao-telemetria', 'capitao-rebase'].forEach((ev) => window.addEventListener(ev, this._onTele));", "['capitao-rebase'].forEach((ev) => window.addEventListener(ev, this._onTele));")], 'f2f5_web:F5-FAQ-Climatizacao-Web'),
    ('a F5 do app não remove o ouvinte da telemetria ao desmontar', 'F5-FAQ-Climatizacao.dc.html', [("['capitao-telemetria', 'capitao-rebase'].forEach((ev) => window.removeEventListener(ev, this._onTele));", "['capitao-rebase'].forEach((ev) => window.removeEventListener(ev, this._onTele));")], 'codigo'),
    ('a F2 do app redesenha com a aba escondida', 'F2-FAQ-Estabilizador.dc.html', [("if (document.hidden) return;", "")], 'codigo'),
    ('a F2 web redesenha sem comparar o texto', 'F2-FAQ-Estabilizador-Web.dc.html', [("if (k !== this._bk)", "if (true)")], 'codigo'),
    ('a F5 web com «(DEMO)» no selo de segurança do guia', 'F5-FAQ-Climatizacao-Web.dc.html', [("seloTxt: pronto ? 'passo a passo do guia de bordo — confirmar no manual do fabricante'", "seloTxt: pronto ? 'passo a passo do guia de bordo (DEMO) — confirmar no manual do fabricante'")], 'f2f5_web:F5-FAQ-Climatizacao-Web'),
    ('o link do FAQ completo da F3 web abre a seção errada', 'F3-FAQ-Eletronicos-Web.dc.html', [("f6: '#s=6,7'", "f6: '#s=2'")], 'f2f5_web:F3-FAQ-Eletronicos-Web'),
    # —— as outras telas que a P4H toca ——
    ('o «passo a passo» da C4 web volta a abrir o chat (sem o código)', 'C4-Checklist-Web.dc.html', [("['F6-FAQ-Equipamentos-Web.dc.html#id=' + encodeURIComponent(i.faq)", "['Main.dc.html#q=' + encodeURIComponent(i.faqPergunta)")], 'c4_web'),
    ('o «passo a passo» da C4 do app abre a F6 web', 'C4-Checklist-Mobile.dc.html', [("['F6-FAQ-Equipamentos.dc.html#id=' + encodeURIComponent(i.faq)", "['F6-FAQ-Equipamentos-Web.dc.html#id=' + encodeURIComponent(i.faq)")], 'c4_app'),
    ('a H3 web sem o atalho do FAQ dos equipamentos', 'H3-Atalhos-Editar-Web.dc.html', [('data-h3="tela-faq"', 'data-h3="tela-faq-x"')], 'h3_web'),
    # —— o registro (TELAS, CORE, lista, mapa APP) ——
    ('a F6 do app fora das TELAS do sw.js', 'sw.js', [("'F6-FAQ-Equipamentos-Web', 'F6-FAQ-Equipamentos',", "'F6-FAQ-Equipamentos-Web',")], 'codigo'),
    ('o capitao-faq.js fora do CORE do sw.js', 'sw.js', [("'./capitao-faq.js', ", "")], 'codigo'),
    ('a F6 web fora da lista do index', 'index.html', [('<a class="row" href="F6-FAQ-Equipamentos-Web.dc.html">FAQ dos equipamentos<span>F6</span></a>', '')], 'codigo'),
    ('a F6 fora do mapa APP do capitao-app.js', 'capitao-app.js', [("'F6-FAQ-Equipamentos-Web': 'F6-FAQ-Equipamentos',", "")], 'codigo'),
]
F6W, F6A = 'F6-FAQ-Equipamentos-Web', 'F6-FAQ-Equipamentos'
QUAL_P4H = {
    'busca': lambda b, t: teste_f6_busca(b, F6W), 'itens': lambda b, t: teste_f6_itens(b, F6W), 'itens_app': lambda b, t: teste_f6_itens(b, F6A), 'enderecos': lambda b, t: teste_f6_enderecos(b, F6W), 'lista': lambda b, t: teste_f6_lista(b, F6W),
    'lista_carga': lambda b, t: teste_f6_carga_lenta(b, F6W), 'navegacao': lambda b, t: teste_f6_navegacao(b, F6W), 'navegacao_app': lambda b, t: teste_f6_navegacao(b, F6A),
    'lento_web': lambda b, t: teste_chat_faq_lento(b, 'Main'), 'lento_app': lambda b, t: teste_chat_faq_lento(b, 'H2-Home-Mobile'),
    'chat_web': lambda b, t: teste_f6_chat(b, F6W), 'chat_app': lambda b, t: teste_f6_chat(b, F6A), 'semdados_web': lambda b, t: teste_chat_faq(b, 'Main'), 'semdados_app': lambda b, t: teste_chat_faq(b, 'H2-Home-Mobile'),
    'f1_web': lambda b, t: teste_f1(b, 'F1-FAQ-Hub-Web'), 'f1_app': lambda b, t: teste_f1(b, 'F1-FAQ-Hub'), 'codigo': lambda b, t: teste_faq_codigo(),
    'c4_web': lambda b, t: teste_c4(b, 'C4-Checklist-Web'), 'c4_app': lambda b, t: teste_c4(b, 'C4-Checklist-Mobile'), 'h3_web': lambda b, t: teste_h3(b, 'H3-Atalhos-Editar-Web'),
}


def mutantes_p4h(b):
    global MUT_ARQ
    vivos = []
    filtro = os.environ.get('MUT_FILTRO', '')   # só os mutantes cujo nome tem este texto (para refazer um)
    for nome, arq, trocas, qual in MUTANTES_P4H:
        if filtro and filtro not in nome: continue
        src = open(os.path.join(RAIZ, arq), encoding='utf-8', newline='').read()
        faltam = [x for x, _ in trocas if src.count(x) != 1]
        if faltam:
            print('ERRO no mutante «%s»: o trecho não está uma vez em %s: %s' % (nome, arq, faltam)); vivos.append(nome); continue
        MUT_ARQ = {arq: trocas}
        sai = sys.stdout
        prob = []
        try:
            sys.stdout = open(os.devnull, 'w')
            if ':' in qual:   # «f2f5:<tela>» e «f2f5_web:<tela>»: o teste do estado a bordo na tela do arquivo mutado
                k, tela = qual.split(':', 1)
                prob = teste_f2f5(b, tela) + teste_faq_codigo()
            else:
                prob = QUAL_P4H[qual](b, arq.replace('.dc.html', ''))
        except Exception as e:   # um erro do próprio teste não conta como acusação: o mutante fica vivo
            sys.stdout = sai
            print('ERRO do teste no mutante «%s»: %s' % (nome, str(e).splitlines()[-1][:160]))
            prob = []
        finally:
            sys.stdout = sai
            MUT_ARQ = {}
        print('MUTANTE %s: %s (%d problema(s))%s' % ('ACUSADO' if prob else 'VIVO', nome, len(prob), ' · ' + prob[0][:150] if prob else ''))
        if not prob: vivos.append(nome)
    print('%d mutantes · %d vivos' % (len(MUTANTES_P4H), len(vivos)))
    return vivos


# ═══ Fase 4, P4I: Documentos com peças (G1) e Abastecimento com consumo (G2), web e app ═══
# `--so-p4i [Tela…]` roda só as conferências dela; `--mutantes-p4i` planta os defeitos (todos acusados; `MUT_FILTRO=texto` refaz só os mutantes cujo nome tem o texto).
# As expectativas saem do D e do instante da própria página (CapitaoAgora, CapitaoReplay, D.pecas, D.agenda) e de contas feitas aqui em Python (a data de hoje + venceEm, o estado da peça, o TWA), nunca do
# texto que a tela escreve. Sem Worker (a IA nem entra), sem valor em dinheiro.
TELAS_G1 = ('G1-Documentos-Web', 'G1-Documentos-Mobile')
TELAS_G2 = ('G2-Abastecimento-Web', 'G2-Abastecimento-Mobile')
TELAS_P4I = TELAS_G1 + TELAS_G2
LE_G1 = """() => { const lin = (s) => (s || '').replace(/\\s+/g, ' ').trim(), q = (s) => document.querySelector(s), qa = (s) => [...document.querySelectorAll(s)];
  const ls = (k) => { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }, at = (e, s, a) => { const x = e.querySelector(s); return x ? x.getAttribute(a) : null; };
  return {
    abas: qa('[data-g1=aba]').map((e) => [e.getAttribute('data-aba'), e.getAttribute('aria-selected')]), hash: location.hash,
    resumo: lin((q('[data-g1=resumo]') || {}).innerText), nota: lin((q('[data-g1=nota]') || {}).innerText), perguntar: q('[data-g1=perguntar]') ? q('[data-g1=perguntar]').getAttribute('href') : null,
    tiles: qa('[data-g1=tile]').map((e) => [e.getAttribute('data-k'), lin(e.innerText), e.getAttribute('aria-pressed')]),
    ptiles: qa('[data-g1=ptile]').map((e) => [e.getAttribute('data-k'), lin(e.innerText), e.getAttribute('aria-pressed')]),
    docs: qa('[data-g1=doc]').map((e) => ({ id: e.getAttribute('data-id'), nome: lin((e.querySelector('[data-g1=doc-nome]') || {}).innerText), validade: lin((e.querySelector('[data-g1=validade]') || {}).innerText),
      st: lin((e.querySelector('[data-g1=st]') || {}).innerText), selo: !!e.querySelector('[data-g1=selo]'), ask: at(e, '[data-g1=ask]', 'href'), texto: lin(e.innerText) })),
    proximos: qa('[data-g1=proximo]').map((e) => lin(e.innerText)),
    pecas: qa('[data-g1=peca]').map((e) => ({ id: e.getAttribute('data-id'), nivel: e.getAttribute('data-nivel'), nome: lin((e.querySelector('[data-g1=nome]') || {}).innerText), qtd: lin((e.querySelector('[data-g1=qtd]') || {}).innerText),
      st: lin((e.querySelector('[data-g1=st]') || {}).innerText), selo: !!e.querySelector('[data-g1=selo]'), tarefas: lin((e.querySelector('[data-g1=tarefas]') || {}).innerText), ask: at(e, '[data-g1=ask]', 'href'),
      usaOff: at(e, '[data-g1=usa]', 'aria-disabled'), editor: !!e.querySelector('[data-g1=editor]') })),
    aviso: lin((q('[data-g1=aviso]') || {}).innerText), avisoLinhas: ((q('[data-g1=aviso]') || { innerText: '' }).innerText || '').split('\\n').map(lin).filter(Boolean), uso: lin((q('[data-g1=uso-texto]') || {}).innerText),
    erros: qa('[data-g1=erro]').map((e) => lin(e.innerText)).filter(Boolean), form: !!q('[data-g1=form]'), nova: q('[data-g1=nova]') ? q('[data-g1=nova]').getAttribute('aria-expanded') : null,
    falta: /FALTA REGISTRAR/.test(document.body.innerText), texto: document.body.innerText,
    pecasLs: ls('capitao.pecas.v1'), docsLs: ls('capitao.docs.v1'), diarioLs: ls('capitao.diario.v1') }; }"""
ESP_G1 = """() => { const D = window.CapitaoDados, A = window.CapitaoAgora;
  return { hoje: A.relogio.hoje, hojeIso: A.relogio.hojeIso, sim: D.simulacao === true,
    docs: D.documentos.map((x) => ({ id: x.id, n: x.n, venceEm: typeof x.venceEm === 'number' ? x.venceEm : null, cat: x.cat })),
    pecas: D.pecas.map((p) => ({ id: p.id, n: p.n, qtd: p.qtd, min: p.min, tarefas: p.tarefas || [] })),
    agenda: D.agenda.map((t) => ({ id: t.id, t: t.t, venceEm: t.venceEm })), cont: A.contagens() }; }"""
G1_PERGUNTA = """(qs) => { const B = window.CapitaoBrain; return qs.map((q) => { const a = B.answer(q, { platform: 'web', commit: false }); return { q: q, key: a.key, ia: B.pedeIA(a, q) }; }); }"""


def nbp(x, c=1, mil=False):
    """O número como o CapitaoAgora.fmt.nb escreve: floor(x·10^c + 0,5) / 10^c, vírgula decimal, ponto de milhar opcional, sem -0."""
    p = 10 ** c
    v = math.floor(x * p + 0.5) / p
    if v == 0: v = 0.0
    inteiro, _, frac = ('%.*f' % (c, abs(v))).partition('.')
    if mil: inteiro = re.sub(r'(\d)(?=(\d{3})+$)', r'\1.', inteiro)
    return ('-' if v < 0 else '') + inteiro + (',' + frac if c else '')


def data_de(hoje_iso, dias): return (datetime.date.fromisoformat(hoje_iso) + datetime.timedelta(days=dias)).strftime('%d/%m/%Y')
def st_doc(dn): return 'VENCIDO' if dn < 0 else 'VENCE EM %d D' % dn if dn <= 90 else 'EM DIA'
def st_peca(q, mn): return 'ZERADA' if q <= 0 else 'ABAIXO DO MÍNIMO' if mn > 0 and q < mn else 'NO MÍNIMO' if mn > 0 and q == mn else 'OK'
def nivel_peca(q, mn): return 'zero' if q <= 0 else 'baixa' if mn > 0 and q <= mn else 'ok'
def rot_prazo(n): return 'ATRASADA · %d D' % -n if n < 0 else 'D-%d' % n


def abre_g1(b, tela, aba='docs', fixo='60', depois='', ls=None):
    ctx, pg, erros = abre_tela(b, tela, fixo=fixo, hash_='#aba=pecas' if aba == 'pecas' else '', depois=depois, ls=ls)
    try: pg.wait_for_function("() => document.querySelector('[data-g1=doc],[data-g1=peca]')", timeout=10000)
    except Exception: pass
    pg.wait_for_timeout(250)
    return ctx, pg, erros


def g1_docs_confere(r, E, rot, app):
    """O que a aba Documentos tem de mostrar com o relógio `E` (hoje, venceEm de cada documento): a ordem, a validade (hoje + venceEm), a situação, os 3 cartões e a pergunta de cada linha."""
    prob = []
    docs = sorted(E['docs'], key=lambda x: x['venceEm'] if x['venceEm'] is not None else 2e6)
    if [d['id'] for d in r['docs']] != [d['id'] for d in docs]: return ['%s: os documentos da lista são %s (esperado %s, por vence primeiro)' % (rot, [d['id'] for d in r['docs']], [d['id'] for d in docs])]
    chat = CHAT_DE['app' if app else 'web']
    for d, x in zip(docs, r['docs']):
        ev = data_de(E['hojeIso'], d['venceEm']) if d['venceEm'] is not None else 'sem prazo'
        es = st_doc(d['venceEm']) if d['venceEm'] is not None else 'CONFERIDA'
        if x['nome'] != d['n'] or x['validade'] != ev or x['st'] != es: prob.append('%s: %s mostra %r / %r / %r (esperado %r / %r / %r)' % (rot, d['id'], x['nome'], x['validade'], x['st'], d['n'], ev, es))
        if x['ask'] != chat + '#q=' + enc('Situação e vencimento do documento: ' + d['n']): prob.append('%s: o «Perguntar sobre» de %s é %r' % (rot, d['id'], x['ask']))
        if re.search(r'A CONFERIR|A CONFIRMAR|MANUAL NO DRIVE|SEM DADOS|\bDEMO\b', x['texto']): prob.append('%s: a linha de %s tem rótulo: %r' % (rot, d['id'], x['texto'][:120]))
    com = [d for d in docs if d['venceEm'] is not None]
    n90 = sum(1 for d in com if d['venceEm'] <= 90)
    nem = len(docs) - n90
    t = {k: (txt, pr) for k, txt, pr in r['tiles']}
    if [k for k, _, _ in r['tiles']] != ['emdia', 'venc90', 'enviado']: prob.append('%s: os cartões são %s (esperado em dia, vencem em 90 dias e enviados; SEM DADOS só no ramo simulacao false)' % (rot, [k for k, _, _ in r['tiles']]))
    elif not (t['emdia'][0].lower().startswith('%d em dia' % nem) and t['venc90'][0].lower().startswith('%d %s' % (n90, '≤ 90 dias' if app else 'vencem em 90 dias')) and t['enviado'][0].lower().startswith('0 enviados')):
        prob.append('%s: os cartões dizem %s (esperado %d em dia, %d vencem em 90 dias, 0 enviados)' % (rot, [x[1][:40] for x in r['tiles']], nem, n90))
    cont = E['cont']
    if cont['docsVencem90'] + cont['docsVencidos'] != n90: prob.append('%s: o CapitaoAgora.contagens() conta %d documentos até 90 dias e a conta daqui, %d' % (rot, cont['docsVencem90'] + cont['docsVencidos'], n90))
    esp_res = ('%d documentos · %d em dia · %d vencem em 90 dias · prazos contados a partir de %s' % (len(docs), nem, n90, E['hoje'])) if not app else ('%d documentos · toque para filtrar · prazos a partir de %s' % (len(docs), E['hoje']))
    if esp_res not in r['resumo']: prob.append('%s: o resumo diz %r (esperado %r)' % (rot, r['resumo'], esp_res))
    if r['falta']: prob.append('%s: o bloco FALTA REGISTRAR na simulação (todo documento tem prazo ou conferência)' % rot)
    if r['perguntar'] and r['perguntar'] != chat + '#q=' + enc('Quais documentos e licenças vencem primeiro?'): prob.append('%s: o «Perguntar» do alto é %r' % (rot, r['perguntar']))
    if not app:
        esp = [d for d in com][:2]
        if len(r['proximos']) != 2 or not all(d['n'] in p and 'D-%d' % d['venceEm'] in p and 'vence ' + data_de(E['hojeIso'], d['venceEm']) in p for d, p in zip(esp, r['proximos'])):
            prob.append('%s: «Vence primeiro» diz %s (esperado %s)' % (rot, r['proximos'], [(d['n'], d['venceEm']) for d in esp]))
    return prob


def teste_g1_documentos(b, tela):
    """G1, aba Documentos: a validade de cada documento é hoje + o prazo relativo (venceEm), a situação vem do CapitaoAgora (VENCIDO, VENCE EM n D, EM DIA; a nota fiscal, CONFERIDA, sem prazo), os cartões batem com
    contagens(), nenhuma linha traz A CONFERIR, MANUAL NO DRIVE nem SEM DADOS, a pergunta de cada linha vai ao docsvenc sem IA; e com o dia virado (fixar 2 dias adiante) as datas se refazem sem recarregar."""
    prob = []
    app = eh_app(tela)
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_g1(b, tela, fixo=fixo)
        r, E = pg.evaluate(LE_G1), pg.evaluate(ESP_G1)
        rot = '%s a %s s' % (tela, fixo)
        prob += g1_docs_confere(r, E, rot, app)
        if r['abas'] != [['docs', 'true'], ['pecas', 'false']]: prob.append('%s: as abas são %s (esperado Documentos marcada e Peças)' % (rot, r['abas']))
        qs = ['Quais documentos e licenças vencem primeiro?'] + ['Situação e vencimento do documento: ' + d['n'] for d in E['docs']]
        for x in pg.evaluate(G1_PERGUNTA, qs):
            if x['key'] != 'docsvenc' or x['ia']: prob.append('%s: «%s» dá %s (IA %s), esperado docsvenc sem IA' % (rot, x['q'][:60], x['key'], x['ia']))
        ach = achados_termos(tela, r['texto'])
        if ach: prob.append('%s: termo do §3 na tela: %s' % (rot, ach))
        if TERMOS['DINHEIRO'].search(r['texto']) or 'R$' in r['texto']: prob.append('%s: valor em dinheiro na tela' % rot)
        if fixo == '60':   # o dia vira: o CapitaoAgora refaz as datas (hoje + venceEm) e a tela, que ouve 'capitao-rebase', as redesenha sem recarregar
            pg.evaluate("() => { window.__marca = 'viva'; window.CapitaoReplay.fixar('60@1152'); }"); pg.wait_for_timeout(700)
            r2, E2 = pg.evaluate(LE_G1), pg.evaluate(ESP_G1)
            if E2['hoje'] == E['hoje']: prob.append('%s: o teste não vale: fixar 60@1152 não mudou o dia (%s)' % (rot, E2['hoje']))
            prob += g1_docs_confere(r2, E2, rot + ' com o dia virado', app)
            if pg.evaluate("() => window.__marca") != 'viva': prob.append('%s: a virada do dia recarregou a tela' % rot)
        prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    return prob


def teste_g1_envio(b, tela):
    """G1, o envio de documento (anexo do aparelho: continua A CONFERIR): sem categoria avisa e não grava; com ela, 1 linha nova com o nome, o tamanho e a categoria, A CONFERIR e carimbada sim: true com a simulação
    (sem o carimbo e sem o selo «apresentação» com simulacao false), 1 linha no diário que diz «linha criada como A CONFERIR», o cartão «enviados» em 1; e o selo «apresentação» só na linha gravada com a simulação e vista com simulacao false."""
    prob = []
    sel = 'select[aria-label^="Categoria"]'
    for modo, depois in (('simulação', ''), ('simulacao false', 'window.CapitaoDados.simulacao = false;')):
        ctx, pg, erros = abre_g1(b, tela, depois=depois)
        pg.click('[data-g1=foto]'); pg.wait_for_timeout(250)
        r = pg.evaluate(LE_G1)
        if 'Escolha a categoria' not in r['nota'] or r['docsLs']: prob.append('%s (%s): sem categoria devia avisar e não gravar: %r %r' % (tela, modo, r['nota'], r['docsLs']))
        pg.select_option(sel, 'Seguro')
        pg.set_input_files('[data-g1=arq-foto]', {'name': 'apolice-teste.jpg', 'mimeType': 'image/jpeg', 'buffer': b'\xff\xd8' + b'0' * 3000}); pg.wait_for_timeout(450)
        r = pg.evaluate(LE_G1)
        ls_, dia = r['docsLs'] or [], r['diarioLs'] or []
        if len(ls_) != 1: prob.append('%s (%s): o envio devia gravar 1 linha em capitao.docs.v1: %s' % (tela, modo, ls_)); ctx.close(); continue
        l = ls_[0]
        if (l.get('n'), l.get('st'), l.get('cat'), l.get('s')) != ('apolice-teste.jpg', 'A CONFERIR', 'Seguro', '3 KB'): prob.append('%s (%s): a linha gravada é %s' % (tela, modo, l))
        if (l.get('sim') is True) != (modo == 'simulação') or ('sim' in l and modo != 'simulação'): prob.append('%s (%s): a linha %s o carimbo sim: true (esperado só com a simulação)' % (tela, modo, 'tem' if 'sim' in l else 'não tem'))
        d = [x for x in dia if 'apolice-teste.jpg' in (x.get('t') or '')]
        if len(d) != 1 or 'linha criada como A CONFERIR' not in d[0]['t'] or not str(d[0].get('src', '')).endswith('· documento') or (d[0].get('sim') is True) != (modo == 'simulação'): prob.append('%s (%s): o diário devia ganhar 1 linha «linha criada como A CONFERIR» do documento (sim só na simulação): %s' % (tela, modo, d))
        x = [y for y in r['docs'] if y['nome'] == 'apolice-teste.jpg']
        if len(x) != 1 or x[0]['st'] != 'A CONFERIR' or x[0]['validade'] != 'a conferir' or x[0]['selo']: prob.append('%s (%s): a linha enviada na tela é %s (esperado A CONFERIR, a conferir, sem selo: ela foi gravada agora)' % (tela, modo, x))
        t = {k: txt for k, txt, _ in r['tiles']}
        if not t.get('enviado', '').lower().startswith('1 enviados'): prob.append('%s (%s): o cartão dos enviados diz %r' % (tela, modo, t.get('enviado')))
        if 'Contratos, notas fiscais, título de propriedade e dados pessoais não ficam neste site' not in r['texto']: prob.append('%s (%s): sumiu o aviso de privacidade' % (tela, modo))
        prob += ['%s (%s): %s' % (tela, modo, e) for e in erros[:2]]
        ctx.close()
    ls = {'capitao.docs.v1': json.dumps([{'n': 'com-selo.jpg', 's': '1 KB', 'dd': '01/11/2026', 'st': 'A CONFERIR', 'cat': 'Laudos', 'fonte': 'enviado no app por Lucas', 'sim': True},
                                         {'n': 'sem-selo.jpg', 's': '1 KB', 'dd': '01/11/2026', 'st': 'A CONFERIR', 'cat': 'Laudos', 'fonte': 'enviado no app por Lucas'}])}
    for modo, depois, esp in (('simulação', '', {'com-selo.jpg': False, 'sem-selo.jpg': False}), ('simulacao false', 'window.CapitaoDados.simulacao = false;', {'com-selo.jpg': True, 'sem-selo.jpg': False})):
        ctx, pg, erros = abre_g1(b, tela, depois=depois, ls=ls)
        r = pg.evaluate(LE_G1)
        got = {x['nome']: x['selo'] for x in r['docs'] if x['nome'] in esp}
        if got != esp: prob.append('%s (%s): o selo «apresentação» das linhas enviadas é %s (esperado %s)' % (tela, modo, got, esp))
        ctx.close()
    return prob


def g1_peca_esperada(E, estado=None):
    """As peças que a tela tem de mostrar: do D.pecas (+ `estado` = {id: quantidade a bordo} das que o teste mexeu), com o estado e as tarefas ligadas (nome, D-n ou ATRASADA, dd/mm) feitos aqui."""
    ag = {t['id']: t for t in E['agenda']}
    out = []
    for p in E['pecas']:
        q = (estado or {}).get(p['id'], p['qtd'])
        tf = ['%s — %s · %s' % (ag[i]['t'], rot_prazo(ag[i]['venceEm']), data_de(E['hojeIso'], ag[i]['venceEm'])[:5]) for i in p['tarefas'] if i in ag]
        out.append({'id': p['id'], 'n': p['n'], 'qtd': '%d / %d' % (q, p['min']), 'q': q, 'min': p['min'], 'st': st_peca(q, p['min']), 'nivel': nivel_peca(q, p['min']), 'tarefas': ' '.join(tf) if tf else 'nenhuma tarefa da agenda'})
    return out


def g1_pecas_confere(r, E, rot, app, estado=None, extra=()):
    prob = []
    esp = g1_peca_esperada(E, estado) + list(extra)
    if [p['id'] for p in r['pecas']] != [p['id'] for p in esp]: return ['%s: as peças da lista são %s (esperado %s)' % (rot, [p['id'] for p in r['pecas']], [p['id'] for p in esp])]
    chat = CHAT_DE['app' if app else 'web']
    for e, x in zip(esp, r['pecas']):
        if (x['nome'], x['qtd'], x['st'], x['nivel']) != (e['n'], e['qtd'], e['st'], e['nivel']): prob.append('%s: %s mostra %r %r %r %r (esperado %r %r %r %r)' % (rot, e['id'], x['nome'], x['qtd'], x['st'], x['nivel'], e['n'], e['qtd'], e['st'], e['nivel']))
        if x['tarefas'] != e['tarefas']: prob.append('%s: as tarefas ligadas de %s são %r (esperado %r)' % (rot, e['id'], x['tarefas'], e['tarefas']))
        if x['ask'] != chat + '#q=' + enc('Estoque de peças: ' + e['n']): prob.append('%s: o «Perguntar sobre» de %s é %r' % (rot, e['id'], x['ask']))
        if (x['usaOff'] == 'true') != (e['q'] <= 0): prob.append('%s: o −1 USADA de %s está aria-disabled=%r com %d a bordo' % (rot, e['id'], x['usaOff'], e['q']))
    z = [p for p in esp if p['nivel'] == 'zero']; bx = [p for p in esp if p['nivel'] == 'baixa']; ok = [p for p in esp if p['nivel'] == 'ok']
    t = {k: txt for k, txt, _ in r['ptiles']}
    if [k for k, _, _ in r['ptiles']] != ['todas', 'zero', 'baixa', 'ok'] or not (t['todas'].lower().startswith('%d peças' % len(esp)) and t['zero'].lower().startswith('%d zeradas' % len(z)) and t['baixa'].lower().startswith('%d no mínimo' % len(bx)) and t['ok'].lower().startswith('%d acima' % len(ok))):
        prob.append('%s: os cartões das peças dizem %s (esperado %d peças, %d zeradas, %d no mínimo, %d acima)' % (rot, [x[1][:30] for x in r['ptiles']], len(esp), len(z), len(bx), len(ok)))
    av = z + bx
    esp_av = ['%d %s' % (len(av), 'peça zerada ou no mínimo' if len(av) == 1 else 'peças zeradas ou no mínimo')] + [x for p in av for x in (p['n'], '%d / %d' % (p['q'], p['min']))] if av else ['Estoque acima do mínimo']
    got = [l for l in r['avisoLinhas'] if not l.startswith('Fonte:')]
    if got != esp_av: prob.append('%s: o aviso de estoque diz %s (esperado %s)' % (rot, got, esp_av))
    return prob


def teste_g1_pecas_lista(b, tela):
    """G1, aba Peças: as peças do D.pecas com a quantidade, o mínimo, a situação (ZERADA, ABAIXO DO MÍNIMO, NO MÍNIMO, OK), o local, as tarefas ligadas (nome e o prazo de hoje do CapitaoAgora, ATRASADA ou D-n, com o dia),
    o aviso das zeradas e no mínimo, os 4 cartões (e o filtro), a pergunta de cada peça no cérebro (pecas, sem IA), a aba pelo #aba= e por toque, sem valor em dinheiro nem rótulo; a 60 s e a 105 s."""
    prob = []
    app = eh_app(tela)
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_g1(b, tela, aba='pecas', fixo=fixo)
        r, E = pg.evaluate(LE_G1), pg.evaluate(ESP_G1)
        rot = '%s a %s s' % (tela, fixo)
        prob += g1_pecas_confere(r, E, rot, app)
        if r['abas'] != [['docs', 'false'], ['pecas', 'true']]: prob.append('%s: com #aba=pecas as abas são %s' % (rot, r['abas']))
        esp = g1_peca_esperada(E)
        z = sum(1 for p in esp if p['nivel'] == 'zero'); bx = sum(1 for p in esp if p['nivel'] == 'baixa')
        if ('%d peças' % len(esp)) not in r['resumo'] or ('%d zerada' % z) not in r['resumo'] or ('%d no mínimo ou abaixo' % bx) not in r['resumo']: prob.append('%s: o resumo das peças diz %r' % (rot, r['resumo']))
        qs = ['Quais peças estão zeradas ou no mínimo?'] + ['Estoque de peças: ' + p['n'] for p in E['pecas']]
        for x in pg.evaluate(G1_PERGUNTA, qs):
            if x['key'] != 'pecas' or x['ia']: prob.append('%s: «%s» dá %s (IA %s), esperado pecas sem IA' % (rot, x['q'][:60], x['key'], x['ia']))
        chat = CHAT_DE['app' if app else 'web']
        if r['perguntar'] and r['perguntar'] != chat + '#q=' + enc('Quais peças estão zeradas ou no mínimo?'): prob.append('%s: o «Perguntar» do alto das peças é %r' % (rot, r['perguntar']))
        ach = achados_termos(tela, r['texto'])
        if ach: prob.append('%s: termo do §3 na aba Peças: %s' % (rot, ach))
        if TERMOS['DINHEIRO'].search(r['texto']) or 'R$' in r['texto'] or re.search(r'\bpn\b|código do fabricante:', r['texto']): prob.append('%s: valor em dinheiro ou código de fabricante na aba Peças' % rot)
        if fixo == '60':
            # o filtro dos cartões: só as zeradas; de novo, volta a todas
            pg.click('[data-g1=ptile][data-k=zero]'); pg.wait_for_timeout(200)
            f = pg.evaluate(LE_G1)
            if [p['id'] for p in f['pecas']] != [p['id'] for p in esp if p['nivel'] == 'zero']: prob.append('%s: o cartão das zeradas filtra %s' % (rot, [p['id'] for p in f['pecas']]))
            pg.click('[data-g1=ptile][data-k=zero]'); pg.wait_for_timeout(200)
            if len(pg.evaluate(LE_G1)['pecas']) != len(esp): prob.append('%s: o 2º toque no cartão das zeradas devia soltar o filtro' % rot)
            # a aba por toque: troca o endereço, fecha o que estava aberto e volta; o #aba= com a tela aberta também troca
            pg.click('[data-g1=aba][data-aba=docs]'); pg.wait_for_timeout(250)
            f = pg.evaluate(LE_G1)
            if f['abas'] != [['docs', 'true'], ['pecas', 'false']] or f['hash'] != '#aba=docs' or not f['docs'] or f['pecas']: prob.append('%s: o toque em DOCUMENTOS devia abrir os documentos e pôr #aba=docs: %s %s' % (rot, f['abas'], f['hash']))
            pg.evaluate("() => { window.__marca = 'viva'; location.hash = '#aba=pecas'; }"); pg.wait_for_timeout(300)
            f = pg.evaluate(LE_G1)
            if f['abas'] != [['docs', 'false'], ['pecas', 'true']] or not f['pecas'] or pg.evaluate("() => window.__marca") != 'viva': prob.append('%s: trocar o endereço para #aba=pecas devia abrir as peças sem recarregar: %s' % (rot, f['abas']))
        prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    return prob


def g1_clica(pg, sel):
    pg.click(sel); pg.wait_for_timeout(320)
    return pg.evaluate(LE_G1)


def g1_movs(r):
    return ((r['pecasLs'] or {}).get('movs') or [])


def teste_g1_uso(b, tela):
    """G1, −1 USADA e Desfazer: o toque tira 1 da quantidade (e só do que há), grava UM movimento dq −1 carimbado sim: true, a peça entra no aviso ao chegar no mínimo; o Desfazer devolve a unidade com um movimento NOVO
    (o registro só cresce: o −1 continua lá) e some com o botão; a peça zerada não perde unidade nem grava; o Desfazer depois que outra aba mexeu na quantidade é RECUSADO com a mensagem, sem gravar; e o cérebro que
    devolve null no −1 vira mensagem, nunca silêncio."""
    prob = []
    app = eh_app(tela)
    ctx, pg, erros = abre_g1(b, tela, aba='pecas')
    E = pg.evaluate(ESP_G1)
    rot = tela
    r = g1_clica(pg, '[data-g1=peca][data-id=p01] [data-g1=usa]')
    m = g1_movs(r)
    if len(m) != 1 or m[0].get('id') != 'p01' or m[0].get('dq') != -1 or m[0].get('sim') is not True or not m[0].get('iso'): prob.append('%s: o −1 USADA devia gravar 1 movimento {id p01, dq −1, sim true}: %s' % (rot, m))
    prob += g1_pecas_confere(r, E, rot + ' depois do −1', app, {'p01': 3})
    if r['uso'] != '−1 USADA: Filtro de óleo do motor — 4 → 3 a bordo.': prob.append('%s: o aviso do −1 diz %r' % (rot, r['uso']))
    iso0 = m[0]['iso'] if m else None
    r = g1_clica(pg, '[data-g1=desfazer]')
    m = g1_movs(r)
    if len(m) != 2 or m[0].get('iso') != iso0 or m[0].get('dq') != -1 or m[1].get('dq') != 1 or m[1].get('iso') == iso0: prob.append('%s: o Desfazer devia ACRESCENTAR um movimento dq +1 e manter o −1 (o registro só cresce): %s' % (rot, m))
    prob += g1_pecas_confere(r, E, rot + ' depois do Desfazer', app)
    if r['uso'] or 'Desfeito' not in r['nota']: prob.append('%s: depois do Desfazer a barra devia sumir e a nota dizer «Desfeito»: %r %r' % (rot, r['uso'], r['nota']))
    # p02 (4, mínimo 2): dois toques levam ao mínimo e a peça entra no aviso; um terceiro, abaixo dele
    g1_clica(pg, '[data-g1=peca][data-id=p02] [data-g1=usa]'); r = g1_clica(pg, '[data-g1=peca][data-id=p02] [data-g1=usa]')
    prob += g1_pecas_confere(r, E, rot + ' com a p02 no mínimo', app, {'p02': 2})
    if [p['st'] for p in r['pecas'] if p['id'] == 'p02'] != ['NO MÍNIMO']: prob.append('%s: a p02 com 2/2 devia dizer NO MÍNIMO (e subir o aviso para 7 peças): %s' % (rot, [p['st'] for p in r['pecas'] if p['id'] == 'p02']))
    # a peça zerada: nada a tirar, nada grava
    n0 = len(g1_movs(r))
    pg.evaluate("() => document.querySelector('[data-g1=peca][data-id=p05] [data-g1=usa]').click()"); pg.wait_for_timeout(300)
    r = pg.evaluate(LE_G1)
    if len(g1_movs(r)) != n0 or 'já está zerada' not in r['nota']: prob.append('%s: o −1 na peça zerada devia avisar e não gravar: %r (movimentos %d → %d)' % (rot, r['nota'], n0, len(g1_movs(r))))
    # o Desfazer depois que outra aba mexeu na quantidade: recusado, com a mensagem
    g1_clica(pg, '[data-g1=peca][data-id=p04] [data-g1=usa]')
    pg.evaluate("() => window.CapitaoBrain.ajustaPeca('p04', '9')")
    n1 = len(g1_movs(pg.evaluate(LE_G1)))
    r = g1_clica(pg, '[data-g1=desfazer]')
    q4 = [p['qtd'] for p in r['pecas'] if p['id'] == 'p04']
    if 'Não deu para desfazer' not in r['nota'] or len(g1_movs(r)) != n1 or q4 != ['9 / 1']: prob.append('%s: o Desfazer depois de a quantidade mudar devia ser recusado com a mensagem e sem gravar: %r, movimentos %d → %d, p04 %s' % (rot, r['nota'], n1, len(g1_movs(r)), q4))
    # o cérebro que devolve null no −1: mensagem explícita
    pg.evaluate("() => { window.CapitaoBrain.usaPeca = () => null; }")
    n2 = len(g1_movs(pg.evaluate(LE_G1)))
    r = g1_clica(pg, '[data-g1=peca][data-id=p06] [data-g1=usa]')
    if 'Não deu para tirar uma unidade' not in r['nota'] or len(g1_movs(r)) != n2: prob.append('%s: o cérebro recusou o −1 e a tela não disse (nota %r)' % (rot, r['nota']))
    prob += ['%s: %s' % (rot, e) for e in erros[:2]]
    ctx.close()
    # com simulacao false, nada é carimbado
    ctx, pg, erros = abre_g1(b, tela, aba='pecas', depois='window.CapitaoDados.simulacao = false;')
    r = g1_clica(pg, '[data-g1=peca][data-id=p01] [data-g1=usa]')
    m = g1_movs(r)
    if len(m) != 1 or 'sim' in m[0]: prob.append('%s (simulacao false): o movimento não leva sim: %s' % (rot, m))
    ctx.close()
    return prob


def teste_g1_edita(b, tela):
    """G1, ✎ e + PEÇA: só o inteiro puro de 0 a 999 (1e2, 12abc, 3,5, −1, 1000, 0x10 e o vazio dão «Quantidade inválida», sem gravar); o mesmo número avisa «nada mudou»; o valor bom (com espaços) grava UM movimento
    com a diferença; o + PEÇA pede o nome, recusa quantidade e mínimo inválidos, entrega ao cérebro a quantidade e o mínimo como TEXTO, grava a peça (com a tarefa ligada, o carimbo sim e sem código de fabricante) e a lista a
    mostra; e o cérebro que devolve null no ✎ ou no + PEÇA vira mensagem EXPLÍCITA (o formulário não se apaga)."""
    prob = []
    app = eh_app(tela)
    ctx, pg, erros = abre_g1(b, tela, aba='pecas')
    E = pg.evaluate(ESP_G1)
    rot = tela
    r = g1_clica(pg, '[data-g1=peca][data-id=p03] [data-g1=editar]')
    if not [p for p in r['pecas'] if p['id'] == 'p03' and p['editor']]: prob.append('%s: o ✎ devia abrir o editor da p03' % rot)
    for v in ('', '1e2', '12abc', '3,5', '-1', '1000', '0x10'):
        pg.fill('[data-g1=editar-campo]', v); r = g1_clica(pg, '[data-g1=editar-ok]')
        if not r['erros'] or not r['erros'][0].startswith('Quantidade inválida') or g1_movs(r) or [p['qtd'] for p in r['pecas'] if p['id'] == 'p03'] != ['1 / 2']: prob.append('%s: ✎ com %r devia dar «Quantidade inválida» sem gravar: %s %s' % (rot, v, r['erros'], g1_movs(r)))
    pg.fill('[data-g1=editar-campo]', '1'); r = g1_clica(pg, '[data-g1=editar-ok]')
    if not r['erros'] or 'nada mudou' not in r['erros'][0] or g1_movs(r): prob.append('%s: ✎ com o mesmo número devia dizer que nada mudou: %s' % (rot, r['erros']))
    # o cérebro que devolve null: mensagem, não silêncio
    pg.evaluate("() => { window.__ajusta = window.CapitaoBrain.ajustaPeca; window.CapitaoBrain.ajustaPeca = () => null; }")
    pg.fill('[data-g1=editar-campo]', '4'); r = g1_clica(pg, '[data-g1=editar-ok]')
    if not r['erros'] or 'Não deu para ajustar' not in r['erros'][0] or g1_movs(r): prob.append('%s: o cérebro recusou o ✎ e a tela não disse: %s' % (rot, r['erros']))
    pg.evaluate("() => { window.CapitaoBrain.ajustaPeca = window.__ajusta; }")
    pg.fill('[data-g1=editar-campo]', ' 5 '); r = g1_clica(pg, '[data-g1=editar-ok]')
    m = g1_movs(r)
    if len(m) != 1 or (m[0].get('id'), m[0].get('dq'), m[0].get('sim')) != ('p03', 4, True) or r['erros'] or [p['editor'] for p in r['pecas'] if p['id'] == 'p03'] != [False]: prob.append('%s: ✎ com « 5 » devia gravar 1 movimento p03 +4 e fechar o editor: %s' % (rot, m))
    prob += g1_pecas_confere(r, E, rot + ' depois do ✎', app, {'p03': 5})
    r = g1_clica(pg, '[data-g1=peca][data-id=p03] [data-g1=editar]'); r = g1_clica(pg, '[data-g1=peca][data-id=p03] [data-g1=editar-cancela]')
    if len(g1_movs(r)) != 1 or [p['editor'] for p in r['pecas'] if p['id'] == 'p03'] != [False]: prob.append('%s: Cancelar devia fechar o editor sem gravar' % rot)
    # + PEÇA
    r = g1_clica(pg, '[data-g1=nova]')
    if not r['form'] or r['nova'] != 'true': prob.append('%s: o + PEÇA devia abrir o formulário (aria-expanded true)' % rot)
    def nova(nome, qtd, mn, local='', tarefa=''):
        pg.fill('[data-g1=f-nome]', nome); pg.fill('[data-g1=f-qtd]', qtd); pg.fill('[data-g1=f-min]', mn); pg.fill('[data-g1=f-local]', local)
        pg.select_option('[data-g1=f-tarefa]', tarefa)
        return g1_clica(pg, '[data-g1=f-salvar]')
    casos = [(('', '3', '1'), 'Dê um nome'), (('Peça x', '1e2', '1'), 'Quantidade inválida'), (('Peça x', '3', '12abc'), 'Mínimo inválido'), (('Peça x', '1000', '1'), 'Quantidade inválida'), (('Peça x', '3,5', '1'), 'Quantidade inválida')]
    for args, esperado in casos:
        r = nova(*args)
        if not r['erros'] or not r['erros'][0].startswith(esperado) or len(r['pecas']) != 12 or (r['pecasLs'] or {}).get('novas'): prob.append('%s: + PEÇA com %s devia dar «%s» sem cadastrar: %s, %d peças' % (rot, args, esperado, r['erros'], len(r['pecas'])))
    pg.evaluate("() => { window.__args = []; window.__add = window.CapitaoBrain.addPeca; window.CapitaoBrain.addPeca = () => null; }")
    r = nova('Filtro de ar do gerador', '3', '1', 'estante técnica 2', 'gerador-revisao')
    if not r['erros'] or 'Não deu para cadastrar' not in r['erros'][0] or len(r['pecas']) != 12 or not r['form']: prob.append('%s: o cérebro recusou o + PEÇA e a tela não disse (ou apagou o formulário): %s' % (rot, r['erros']))
    pg.evaluate("() => { window.CapitaoBrain.addPeca = function (c) { window.__args.push(JSON.parse(JSON.stringify(c))); return window.__add.call(window.CapitaoBrain, c); }; }")
    r = pg.evaluate(LE_G1)
    pg.click('[data-g1=f-salvar]'); pg.wait_for_timeout(350)
    r = pg.evaluate(LE_G1)
    args = pg.evaluate("() => window.__args")
    if len(args) != 1 or not (isinstance(args[0].get('qtd'), str) and isinstance(args[0].get('min'), str)) or args[0].get('qtd') != '3' or args[0].get('min') != '1': prob.append('%s: a quantidade e o mínimo vão ao cérebro como TEXTO ("3" e "1"): %s' % (rot, args))
    novas = (r['pecasLs'] or {}).get('novas') or []
    if len(novas) != 1 or (novas[0].get('n'), novas[0].get('qtd'), novas[0].get('min'), novas[0].get('local'), novas[0].get('tarefas'), novas[0].get('sim')) != ('Filtro de ar do gerador', 3, 1, 'estante técnica 2', ['gerador-revisao'], True) or 'pn' in novas[0] or re.search(r'pre[cç]o|valor|r\$', json.dumps(novas[0]), re.I):
        prob.append('%s: a peça cadastrada devia ser %s: %s' % (rot, 'Filtro de ar do gerador 3/1 estante técnica 2 com a tarefa gerador-revisao e sim true', novas))
    nid = novas[0]['id'] if novas else 'x'
    ag = {t['id']: t for t in E['agenda']}['gerador-revisao']
    extra = [{'id': nid, 'n': 'Filtro de ar do gerador', 'qtd': '3 / 1', 'q': 3, 'min': 1, 'st': 'OK', 'nivel': 'ok', 'tarefas': '%s — %s · %s' % (ag['t'], rot_prazo(ag['venceEm']), data_de(E['hojeIso'], ag['venceEm'])[:5])}]
    prob += g1_pecas_confere(r, E, rot + ' com a peça cadastrada', app, {'p03': 5}, extra)
    if r['form'] or r['erros'] or 'Peça cadastrada' not in r['nota']: prob.append('%s: depois de cadastrar o formulário devia fechar e a nota dizer «Peça cadastrada»: %r %r' % (rot, r['nota'], r['form']))
    prob += ['%s: %s' % (rot, e) for e in erros[:2]]
    ctx.close()
    return prob


def teste_g1_real(b, tela):
    """G1, o caminho `null` → SEM DADOS é do ramo simulacao false: um documento sem prazo e sem conferência diz SEM DADOS (cartão, linha, FALTA REGISTRAR); na simulação o mesmo documento diz «sem prazo», sem rótulo; e as peças cadastradas
    com a simulação ligada ganham o selo «apresentação» só com simulacao false (as de antes, não)."""
    prob = []
    doc = "window.CapitaoDados.documentos.push({ id: 'sem-prazo-teste', n: 'Documento sem prazo do teste', cat: 'Registro', nota: 'teste', fonte: 'Controle de documentos' });"
    ctx, pg, erros = abre_g1(b, tela, depois=doc)
    r = pg.evaluate(LE_G1)
    x = [d for d in r['docs'] if d['id'] == 'sem-prazo-teste']
    if len(x) != 1 or x[0]['st'] != 'sem prazo' or x[0]['validade'] != 'sem prazo' or r['falta'] or ach_g1(tela, r): prob.append('%s (simulação): o documento sem prazo devia dizer «sem prazo» sem rótulo nem FALTA REGISTRAR: %s %s' % (tela, x, ach_g1(tela, r)))
    ctx.close()
    ctx, pg, erros = abre_g1(b, tela, depois=doc + ' window.CapitaoDados.simulacao = false;')
    r = pg.evaluate(LE_G1)
    x = [d for d in r['docs'] if d['id'] == 'sem-prazo-teste']
    t = {k: txt for k, txt, _ in r['tiles']}
    if len(x) != 1 or x[0]['st'] != 'SEM DADOS' or x[0]['validade'] != 'SEM DADOS' or not r['falta'] or not t.get('semdados', '').startswith('1 SEM DADOS'): prob.append('%s (simulacao false): o documento sem prazo devia dizer SEM DADOS na linha, no cartão e no FALTA REGISTRAR: %s %s' % (tela, x, t.get('semdados')))
    prob += ['%s (simulacao false): %s' % (tela, e) for e in erros[:2]]
    ctx.close()
    ls = {'capitao.pecas.v1': json.dumps({'novas': [{'id': 'u1', 'n': 'Peça com selo do teste', 'qtd': 2, 'min': 1, 'sim': True}, {'id': 'u2', 'n': 'Peça sem selo do teste', 'qtd': 2, 'min': 1}], 'movs': []})}
    for modo, depois, esp in (('simulação', '', {'u1': False, 'u2': False}), ('simulacao false', 'window.CapitaoDados.simulacao = false;', {'u1': True, 'u2': False})):
        ctx, pg, erros = abre_g1(b, tela, aba='pecas', depois=depois, ls=ls)
        r = pg.evaluate(LE_G1)
        got = {p['id']: p['selo'] for p in r['pecas'] if p['id'] in esp}
        if got != esp: prob.append('%s (%s): o selo «apresentação» das peças cadastradas é %s (esperado %s)' % (tela, modo, got, esp))
        ctx.close()
    return prob


def ach_g1(tela, r): return achados_termos(tela, r['texto'])


LE_G2 = """() => { const lin = (s) => (s || '').replace(/\\s+/g, ' ').trim(), q = (s) => document.querySelector(s), qa = (s) => [...document.querySelectorAll(s)];
  const ls = (k) => { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } };
  const g = q('[data-capitao-grafico]');
  return {
    abas: qa('[data-g2=aba]').map((e) => [e.getAttribute('data-aba'), e.getAttribute('aria-selected')]), hash: location.hash,
    resumo: lin((q('[data-g2=resumo]') || {}).innerText), nota: lin((q('[data-g2=nota]') || {}).innerText), perguntar: q('[data-g2=perguntar]') ? q('[data-g2=perguntar]').getAttribute('href') : null,
    kpis: Object.fromEntries(qa('[data-g2=kpi]').map((e) => [e.getAttribute('data-k'), lin(e.innerText)])), hrefs: Object.fromEntries(qa('[data-g2=kpi]').map((e) => [e.getAttribute('data-k'), e.getAttribute('href')])), litros: lin((q('[data-g2=litros]') || {}).innerText),
    serieTitulo: lin((q('[data-g2=serie-titulo]') || {}).innerText), series: qa('[data-g2=serie]').map((e) => [e.getAttribute('data-s'), lin(e.innerText), e.getAttribute('aria-pressed')]),
    janelas: qa('[data-g2=janela]').map((e) => [e.getAttribute('data-j'), e.getAttribute('aria-pressed')]),
    graf: g ? { met: g.getAttribute('data-capitao-grafico'), jan: g.getAttribute('data-janela'), vazio: (g.querySelector('[data-vazio]') || g).getAttribute('data-vazio'), linhas: g.querySelectorAll('svg path[fill=none][stroke-width="2"]').length,
      agora: [...g.querySelectorAll('circle[data-agora]')].map((c) => [c.getAttribute('data-campo'), c.getAttribute('data-agora')]), texto: lin(g.innerText) } : null,
    nota2: lin((q('[data-g2=grafico-nota]') || {}).innerText), estacao: Object.fromEntries(qa('[data-g2=estacao-item]').map((e) => [e.getAttribute('data-e'), lin(e.innerText)])),
    histSub: lin((q('[data-g2=hist-sub]') || {}).innerText), hist: qa('[data-g2=hist-linha]').map((e) => ({ texto: lin(e.innerText), st: lin((e.querySelector('[data-g2=st]') || {}).innerText), selo: !!e.querySelector('[data-g2=selo]') })),
    regra: lin((q('[data-g2=regra]') || {}).innerText), regraAgora: lin((q('[data-g2=regra-agora]') || {}).innerText),
    faixas: qa('[data-g2=faixa]').map((e) => ({ nome: e.getAttribute('data-nome'), nomeTxt: lin((e.querySelector('[data-g2=faixa-nome]') || {}).innerText), lph: lin((e.querySelector('[data-g2=faixa-lph]') || {}).innerText), horas: lin((e.querySelector('[data-g2=faixa-horas]') || {}).innerText), litros: lin((e.querySelector('[data-g2=faixa-litros]') || {}).innerText), texto: lin(e.innerText) })),
    totais: Object.fromEntries(qa('[data-g2=total]').map((e) => [e.getAttribute('data-t'), lin(e.innerText)])), coerencia: lin((q('[data-g2=coerencia]') || {}).innerText), faixasSub: lin((q('[data-g2=faixas-sub]') || {}).innerText),
    agora: qa('[data-g2=agora-valor]').map((e) => lin(e.innerText)), texto: document.body.innerText,
    abastLs: ls('capitao.abast.v1'), diarioLs: ls('capitao.diario.v1') }; }"""
ESP_G2 = """() => { const D = window.CapitaoDados, A = window.CapitaoAgora, R = window.CapitaoReplay, F = A.fmt, I = A.instante(), q = I.q, T = {};
  ['diesel_litros', 'diesel_bb_pct', 'diesel_be_pct', 'bateria_0_tensao_v', 'bateria_1_tensao_v', 'bateria_2_tensao_v', 'tanque_agua_pct', 'tanque_cinzas_pct', 'tanque_negras_pct', 'vento_verdadeiro_nos', 'pressao_barometrica_hpa',
   'temp_ar_externo_c', 'temp_agua_c', 'consumo_lph', 'sog_nos', 'motor_bb_rpm', 'motor_be_rpm', 'gerador_kw'].forEach((c) => { T[c] = F.campo(q, c); });
  let c0 = null, c1 = null; try { c0 = R.contadoresEm(A.ancora(I.ms)); c1 = R.contadores(); } catch (e) {}
  return { hora: I.hora, fonteTxt: I.fonteTxt, ms: I.ms, anc: A.ancora(I.ms), calc: I.calc, T: T, twd: q.vento_verdadeiro_angulo, proa: q.proa_graus, lph: q.consumo_lph, sog: q.sog_nos, gerador: q.gerador_ativo === true,
    hoje: A.relogio.hoje, hojeIso: A.relogio.hojeIso, regra: D.regraAbast, cons: { cruzeiro: D.consumo.cruzeiro, lenta: D.consumo.lenta, gerador_lph: D.consumo.gerador_lph, faixas: D.consumo.faixas }, cap: D.embarcacao.tanques.diesel_l,
    ab: D.abastecimentos.map((a) => ({ id: a.id, d: a.d, h: a.h, litros: a.litros, local: a.local, st: a.st, nivelDepois: a.nivelDepois })), faixas: R.porFaixa(), c0: c0 && c0.diesel_litros, c1: c1 && c1.diesel_litros }; }"""
G2_SERIES = [('diesel', 'Diesel válido', 'diesel', ['diesel_litros']), ('agua', 'Água doce', 'agua', ['tanque_agua_pct']), ('servidas', 'Servidas', 'servidas', ['tanque_cinzas_pct', 'tanque_negras_pct']),
             ('baterias', 'Baterias', 'baterias', ['bateria_0_tensao_v', 'bateria_1_tensao_v', 'bateria_2_tensao_v']), ('estacao', 'Estação meteorológica', 'vento', ['vento_verdadeiro_nos'])]


def abre_g2(b, tela, aba='nivel', fixo='60', depois='', ls=None):
    ctx, pg, erros = abre_tela(b, tela, fixo=fixo, hash_='#aba=consumo' if aba == 'consumo' else '', depois=depois, ls=ls)
    try: pg.wait_for_function("() => document.querySelector('[data-g2=kpi]') && document.querySelector('[data-capitao-grafico],[data-g2=faixa]')", timeout=10000)
    except Exception: pass
    pg.wait_for_timeout(350)
    return ctx, pg, erros


def g2_twa(twd, proa):
    t = (twd - proa + 540) % 360 - 180
    if t == -180: t = 180
    return '%d° %s' % (abs(math.floor(t + 0.5)), 'BE' if t >= 0 else 'BB')


def teste_g2_nivel(b, tela):
    """G2, aba Nível, a 60 s e a 105 s: o diesel, o último abastecimento, o consumido desde ele e a autonomia vêm do instante (quadro e `calc` do CapitaoAgora), nunca do D.snapshot de 26/09 (848 L, 11,2 h) nem da
    D.autonomia; o histórico é o D.abastecimentos (data, 1.086 L, local, CONFERIDO, 97,5 % depois); a regra de bordo sem rótulo e o nível de agora contra ela; os gráficos do capitao-grafico.js: diesel válido, água doce e
    servidas (os tanques em 2 abas), baterias (3 séries) e a estação meteorológica (o vento, com o TWA, o barômetro e o ar), cada um com o ponto «agora» igual ao quadro e as 5 janelas; e, sem congelar, a leitura anda."""
    prob = []
    app = eh_app(tela)
    chat = CHAT_DE['app' if app else 'web']
    for fixo in ('60', '105'):
        ctx, pg, erros = abre_g2(b, tela, fixo=fixo)
        r, E = pg.evaluate(LE_G2), pg.evaluate(ESP_G2)
        rot = '%s a %s s' % (tela, fixo)
        T, calc = E['T'], E['calc']
        cap = nbp(E['cap'], 0, True)
        if r['abas'] != [['nivel', 'true'], ['consumo', 'false']]: prob.append('%s: as abas são %s' % (rot, r['abas']))
        fonte = E['fonteTxt'][:1].upper() + E['fonteTxt'][1:]
        res = r['resumo']
        if fonte not in res or E['hora'] not in res or (not app and (('≈ %s' % T['diesel_litros']) not in res or ('(%s %%)' % nbp(calc['diesel_pct'])) not in res or 'regra: abastecer antes de 25 %' not in res)): prob.append('%s: o resumo diz %r (esperado %r, %s e, na web, o diesel %s L e a regra de 25 %%)' % (rot, res, fonte, E['hora'], T['diesel_litros']))
        k = r['kpis']
        if app:
            if ('≈ %s' % T['diesel_litros']) not in r['litros'] or 'L de ' + cap not in r['texto']: prob.append('%s: o diesel do app é %r (esperado ≈ %s L de %s)' % (rot, r['litros'], T['diesel_litros'], cap))
            if sorted(k) != ['autonomia', 'desde', 'regra', 'ultimo']: prob.append('%s: os cartões do app são %s' % (rot, sorted(k)))
        else:
            d = k.get('diesel', '')
            if ('≈ %s' % T['diesel_litros']) not in d or 'L de ' + cap not in d or ('BB %s %%' % T['diesel_bb_pct']) not in d or ('BE %s %%' % T['diesel_be_pct']) not in d or E['hora'] not in d: prob.append('%s: o cartão do diesel diz %r (esperado ≈ %s L de %s, BB %s %%, BE %s %%, %s)' % (rot, d, T['diesel_litros'], cap, T['diesel_bb_pct'], T['diesel_be_pct'], E['hora']))
        a0 = E['ab'][0] if E['ab'] else {}
        u = k.get('ultimo', '')
        if not E['ab'] or nbp(a0['litros'], 0, True) not in u or a0['d'] not in u or a0['h'] not in u or a0['local'] not in u or a0['st'] not in u or ('tanques ≈ %s %% depois' % nbp(a0['nivelDepois'])) not in u: prob.append('%s: o último abastecimento diz %r (esperado %s)' % (rot, u, a0))
        ds = k.get('desde', ''); dd = calc.get('desdeAbast') or {}
        if ('≈ %s' % nbp(dd.get('litros', 0), 0, True)) not in ds or dd.get('desde', '?')[:5] not in ds: prob.append('%s: o consumido desde o abastecimento diz %r (esperado ≈ %s L desde %s)' % (rot, ds, dd.get('litros'), dd.get('desde')))
        au = k.get('autonomia', ''); aa = calc['autonomia']
        if ('≈ %s h' % nbp(aa['horas'])) not in au or ('≈ %s mn' % nbp(aa['mn'], 0, True)) not in au or ('marcha lenta ≈ %s h' % nbp(aa['lenta'], 0, True)) not in au or '11,2' in au: prob.append('%s: a autonomia diz %r (esperado ≈ %s h, ≈ %s mn, lenta ≈ %s h: a do instante, não a de 26/09)' % (rot, au, aa['horas'], aa['mn'], aa['lenta']))
        if not app:   # as perguntas dos cartões e do «Perguntar» vão ao cérebro (autonomia, consumo), sem IA; o cartão do diesel leva à Ponte
            esp_k = {'ultimo': 'consumo', 'desde': 'consumo', 'autonomia': 'autonomia'}
            qs = [(k_, urllib.parse.unquote(h.split('#q=', 1)[1])) for k_, h in r['hrefs'].items() if k_ in esp_k and '#q=' in (h or '')] + [('perguntar', urllib.parse.unquote(r['perguntar'].split('#q=', 1)[1]))]
            if len(qs) != 4 or r['hrefs'].get('diesel') != 'A1-Ponte-Web.dc.html' or not r['perguntar'].startswith(chat + '#q='): prob.append('%s: os links dos cartões são %s e o «Perguntar» %r' % (rot, r['hrefs'], r['perguntar']))
            for (k_, _), x in zip(qs, pg.evaluate(G1_PERGUNTA, [q_ for _, q_ in qs])):
                if x['key'] != esp_k.get(k_, 'autonomia') or x['ia']: prob.append('%s: a pergunta do cartão %r dá %s (IA %s), esperado %s sem IA' % (rot, k_, x['key'], x['ia'], esp_k.get(k_, 'autonomia')))
        for ruim in ('26/09', '848', 'snapshot', 'telemetria ao vivo desligada'):
            if ruim in r['texto']: prob.append('%s: a tela ainda mostra %r (a leitura de 26/09)' % (rot, ruim))
        # o histórico: o registro (D.abastecimentos) com as datas de hoje
        if len(r['hist']) != len(E['ab']): prob.append('%s: o histórico tem %d linhas (esperado as %d do D.abastecimentos)' % (rot, len(r['hist']), len(E['ab'])))
        for x, a in zip(r['hist'], E['ab']):
            if a['d'] not in x['texto'] or a['h'] not in x['texto'] or nbp(a['litros'], 0, True) + ' L' not in x['texto'] or a['local'] not in x['texto'] or x['st'] != a['st'] or ('tanques ≈ %s %% depois' % nbp(a['nivelDepois'])) not in x['texto'] or x['selo']: prob.append('%s: a linha do histórico de %s diz %r' % (rot, a['d'], x['texto'][:140]))
        if not app and ('%d registros' % len(E['ab'])) not in r['histSub']: prob.append('%s: o histórico diz %r' % (rot, r['histSub']))
        # a regra de bordo
        if not r['regra'].startswith('REGRA DE BORDO ' + E['regra'][:1].upper() + E['regra'][1:40]) or re.search(r'DEMO|demonstra', r['regra']): prob.append('%s: a regra de bordo diz %r' % (rot, r['regra'][:120]))
        esp_ra = 'Agora %s %% do total · ≈ %s L — acima da regra (%s)' % (nbp(calc['diesel_pct']), T['diesel_litros'], E['hora'])
        if r['regraAgora'] != esp_ra: prob.append('%s: o nível contra a regra diz %r (esperado %r)' % (rot, r['regraAgora'], esp_ra))
        # os gráficos
        g = r['graf']
        if not g or g['met'] != 'diesel' or g['jan'] != '7D' or g['vazio'] or not g['agora'] or g['agora'][0][1] != T['diesel_litros']: prob.append('%s: o gráfico de abertura devia ser o diesel válido em 7 D com o ponto «agora» em %s L: %s' % (rot, T['diesel_litros'], g))
        if r['serieTitulo'].split(' · ')[0] != 'Diesel válido' and 'Diesel válido' not in r['serieTitulo']: prob.append('%s: o título do gráfico diz %r' % (rot, r['serieTitulo']))
        if [s[0] for s in r['series']] != [s[0] for s in G2_SERIES] or [s[1] for s in r['series']] != [s[1] for s in G2_SERIES]: prob.append('%s: os gráficos escolhíveis são %s (esperado diesel válido, água doce, servidas, baterias e estação meteorológica)' % (rot, [s[1] for s in r['series']]))
        if fixo == '60':
            for chave, rotulo, met, campos in G2_SERIES:
                pg.click('[data-g2=serie][data-s=%s]' % chave); pg.wait_for_timeout(400)
                x = pg.evaluate(LE_G2)
                g = x['graf']
                if not g or g['met'] != met or g['vazio'] or [a[0] for a in g['agora']] != campos or [a[1] for a in g['agora']] != [E['T'][c] for c in campos]:
                    prob.append('%s: o gráfico «%s» devia ser a métrica %s com o ponto «agora» do quadro %s: %s' % (rot, rotulo, met, [E['T'][c] for c in campos], g and (g['met'], g['vazio'], g['agora'])))
                if chave == 'baterias' and g and g['linhas'] < 3: prob.append('%s: as baterias têm de ter 3 séries no gráfico (linhas: %s)' % (rot, g['linhas']))
                if [s[2] for s in x['series'] if s[0] == chave] != ['true']: prob.append('%s: o chip «%s» devia ficar marcado' % (rot, rotulo))
                if chave == 'estacao':
                    est = x['estacao']
                    esp = {'vento': '%s nós' % E['T']['vento_verdadeiro_nos'], 'twa': g2_twa(E['twd'], E['proa']), 'pressao': '%s hPa' % E['T']['pressao_barometrica_hpa'], 'ar': '%s °C' % E['T']['temp_ar_externo_c']}
                    if sorted(est) != sorted(esp) or any(v not in est[k_] for k_, v in esp.items()): prob.append('%s: a estação meteorológica diz %s (esperado %s, com o TWA = vento verdadeiro − proa, + a boreste)' % (rot, est, esp))
                    if 'TWA' not in est.get('twa', '') or 'proa' not in est.get('twa', ''): prob.append('%s: o TWA diz %r (esperado o ângulo em relação à proa)' % (rot, est.get('twa')))
                elif x['estacao']: prob.append('%s: o gráfico «%s» não é a estação e mostra a faixa de meteorologia' % (rot, rotulo))
                if not x['nota2']: prob.append('%s: o gráfico «%s» sem a nota do que ele mostra' % (rot, rotulo))
            # as 5 janelas, no diesel e nas baterias: o gráfico muda de janela e o «agora» continua sendo o quadro
            for chave, campos in (('diesel', ['diesel_litros']), ('baterias', ['bateria_0_tensao_v', 'bateria_1_tensao_v', 'bateria_2_tensao_v'])):
                pg.click('[data-g2=serie][data-s=%s]' % chave); pg.wait_for_timeout(300)
                for j in ('150S', '1D', '7D', '30D', '1A'):
                    pg.click('[data-g2=janela][data-j="%s"]' % j); pg.wait_for_timeout(350)
                    x = pg.evaluate(LE_G2); g = x['graf']
                    if not g or g['jan'] != j or g['vazio'] or [a[1] for a in g['agora']] != [E['T'][c] for c in campos] or [w[1] for w in x['janelas'] if w[0] == j] != ['true']:
                        prob.append('%s: %s na janela %s devia desenhar com o «agora» do quadro %s: %s' % (rot, chave, j, [E['T'][c] for c in campos], g and (g['jan'], g['vazio'], g['agora'])))
        ach = achados_termos(tela, r['texto'])
        if ach: prob.append('%s: termo do §3 na tela: %s' % (rot, ach))
        if TERMOS['DINHEIRO'].search(r['texto']) or 'R$' in r['texto']: prob.append('%s: valor em dinheiro na tela' % rot)
        prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    # sem congelar o replay, a leitura de agora anda (o tique de 1 s redesenha o texto; o gráfico ouve o tique sozinho)
    ctx, pg, erros = abre_g2(b, tela, fixo=None)
    a = pg.evaluate(LE_G2)
    pg.wait_for_timeout(2300)
    c = pg.evaluate(LE_G2)
    if a['resumo'] == c['resumo'] and a['kpis'] == c['kpis'] and (a['litros'] == c['litros']): prob.append('%s: sem congelar, o resumo e a leitura não mudaram em 2,3 s: %r' % (tela, a['resumo']))
    ctx.close()
    return prob


def teste_g2_consumo(b, tela):
    """G2, aba Consumo (F23), a 60 s, a 105 s e a 60 s da volta 300 (19:31, outro ponto do dia de bordo): as 5 faixas do D.consumo.faixas com o L/h, as horas e os litros do CapitaoReplay.porFaixa(); o total desde as 07:00 é
    a soma dos motores e do gerador e BATE com o contador de diesel (c(07:00) − c(agora), diferença só de arredondamento) e a frase da coerência cita os dois contadores; as horas das faixas somam o tempo desde as 07:00; o consumo
    de agora (L/h, L/mn, gerador) é o do quadro; nenhum R$; e o #aba=consumo é a aba."""
    prob = []
    app = eh_app(tela)
    for fixo in ('60', '105', '60@300'):
        ctx, pg, erros = abre_g2(b, tela, aba='consumo', fixo=fixo)
        r, E = pg.evaluate(LE_G2), pg.evaluate(ESP_G2)
        rot = '%s a %s s' % (tela, fixo)
        if r['abas'] != [['nivel', 'false'], ['consumo', 'true']]: prob.append('%s: com #aba=consumo as abas são %s' % (rot, r['abas']))
        fx, nomes = E['faixas'], [f['nome'] for f in E['cons']['faixas']]
        if [f['nome'] for f in r['faixas']] != nomes or [f['nome'] for f in fx] != nomes: prob.append('%s: as faixas da tela são %s (esperado %s, as do D.consumo.faixas)' % (rot, [f['nome'] for f in r['faixas']], nomes)); ctx.close(); continue
        for f, x in zip(fx, r['faixas']):
            esp = (f['nome'][:1].upper() + f['nome'][1:], nbp(f['lph']) + ' L/h' if f['seg'] else '—', nbp(f['horas']) + ' h', nbp(f['litros']) + ' L')
            if (x['nomeTxt'], x['lph'], x['horas'], x['litros']) != esp: prob.append('%s: a faixa %s mostra %s (esperado %s, do CapitaoReplay.porFaixa())' % (rot, f['nome'], (x['nomeTxt'], x['lph'], x['horas'], x['litros']), esp))
            if ('rpm %s a %s' % (nbp(f['rpm_de'], 0, True), nbp(f['rpm_ate'], 0, True))) not in x['texto']: prob.append('%s: a faixa %s sem a rotação %d a %d: %r' % (rot, f['nome'], f['rpm_de'], f['rpm_ate'], x['texto'][:80]))
        sm = sum(f['litros'] for f in fx); sg = sum(f['gerador_litros'] for f in fx); sh = sum(f['horas'] for f in fx)
        tot = r['totais']
        if tot != {'motores': nbp(sm) + ' L', 'gerador': nbp(sg) + ' L', 'total': nbp(sm + sg) + ' L'}: prob.append('%s: os totais dizem %s (esperado motores %s L, gerador %s L, total %s L)' % (rot, tot, nbp(sm), nbp(sg), nbp(sm + sg)))
        dif = (E['c0'] - E['c1']) if E['c0'] is not None and E['c1'] is not None else None
        if dif is None or abs((sm + sg) - dif) > 1.0: prob.append('%s: a soma das faixas e do gerador (%.1f L) não bate com o contador de diesel (%s − %s = %s L)' % (rot, sm + sg, E['c0'], E['c1'], dif))
        elif not all(nbp(v, 0, True) in r['coerencia'] for v in (E['c0'], E['c1'], dif)) or '07:00' not in r['coerencia']: prob.append('%s: a coerência diz %r (esperado os contadores %s → %s = %s L desde as 07:00)' % (rot, r['coerencia'], E['c0'], E['c1'], dif))
        ms_desde = (E['ms'] - E['anc']) / 3.6e6
        if abs(sh - ms_desde) > 0.06: prob.append('%s: as horas das faixas somam %.2f h e desde as 07:00 passaram %.2f h' % (rot, sh, ms_desde))
        if 'Desde as 07:00' not in r['faixasSub'] and not app: prob.append('%s: o subtítulo não diz «Desde as 07:00»: %r' % (rot, r['faixasSub']))
        T = E['T']
        esp_ag = ['%s L/h' % T['consumo_lph'], '%s L/mn' % nbp(E['lph'] / E['sog']) if E['sog'] >= 1 else '—', '%s L/h' % nbp(E['cons']['gerador_lph']) if E['gerador'] else '0,0 L/h']
        if r['agora'] != esp_ag: prob.append('%s: o consumo de agora diz %s (esperado %s, do quadro e do D.consumo)' % (rot, r['agora'], esp_ag))
        ach = achados_termos(tela, r['texto'])
        if ach: prob.append('%s: termo do §3 na aba Consumo: %s' % (rot, ach))
        if TERMOS['DINHEIRO'].search(r['texto']) or 'R$' in r['texto']: prob.append('%s: valor em dinheiro na aba Consumo' % rot)
        prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    # a aba por toque
    ctx, pg, erros = abre_g2(b, tela)
    pg.click('[data-g2=aba][data-aba=consumo]'); pg.wait_for_timeout(350)
    r = pg.evaluate(LE_G2)
    if r['abas'] != [['nivel', 'false'], ['consumo', 'true']] or r['hash'] != '#aba=consumo' or len(r['faixas']) != 5 or r['graf']: prob.append('%s: o toque em CONSUMO devia abrir a aba e pôr #aba=consumo: %s %s' % (tela, r['abas'], r['hash']))
    pg.evaluate("() => { window.__marca = 'viva'; location.hash = '#aba=nivel'; }"); pg.wait_for_timeout(350)
    r = pg.evaluate(LE_G2)
    if r['abas'] != [['nivel', 'true'], ['consumo', 'false']] or not r['graf'] or pg.evaluate("() => window.__marca") != 'viva': prob.append('%s: trocar o endereço para #aba=nivel devia voltar ao nível sem recarregar: %s' % (tela, r['abas']))
    ctx.close()
    return prob


def teste_g2_nf(b, tela):
    """G2, a foto da NF (anexo: continua A CONFIRMAR, o app não lê o arquivo): 1 linha nova no histórico e no capitao.abast.v1 com o nome, a data de hoje e o carimbo sim: true na simulação (sem carimbo com simulacao false: a
    regra do carimbo, CONTRATO §1.25), 1 linha no diário «linha criada como A CONFIRMAR» (sim só na simulação); e o selo «apresentação» só na linha gravada com a simulação e vista com simulacao false."""
    prob = []
    for modo, depois in (('simulação', ''), ('simulacao false', 'window.CapitaoDados.simulacao = false;')):
        ctx, pg, erros = abre_g2(b, tela, depois=depois)
        n0 = len(pg.evaluate(LE_G2)['hist'])
        pg.set_input_files('[data-g2=arq-nf]', {'name': 'nf-diesel-teste.jpg', 'mimeType': 'image/jpeg', 'buffer': b'\xff\xd8' + b'0' * 2000}); pg.wait_for_timeout(450)
        r = pg.evaluate(LE_G2)
        ls_, dia = r['abastLs'] or [], r['diarioLs'] or []
        hoje = datetime.date.today().strftime('%d/%m/%Y')
        if len(ls_) != 1: prob.append('%s (%s): a foto devia gravar 1 linha em capitao.abast.v1: %s' % (tela, modo, ls_)); ctx.close(); continue
        l = ls_[0]
        if (l.get('n'), l.get('st')) != ('nf-diesel-teste.jpg', 'A CONFIRMAR') or l.get('d') != hoje: prob.append('%s (%s): a linha gravada é %s (esperado a foto, A CONFIRMAR, de %s)' % (tela, modo, l, hoje))
        if (l.get('sim') is True) != (modo == 'simulação') or ('sim' in l and modo != 'simulação'): prob.append('%s (%s): a linha %s o carimbo sim: true (esperado só com a simulação)' % (tela, modo, 'tem' if 'sim' in l else 'não tem'))
        d = [x for x in dia if 'nf-diesel-teste.jpg' in (x.get('t') or '')]
        if len(d) != 1 or 'linha criada como A CONFIRMAR' not in d[0]['t'] or not str(d[0].get('src', '')).endswith('· abastecimento') or (d[0].get('sim') is True) != (modo == 'simulação'): prob.append('%s (%s): o diário devia ganhar 1 linha «linha criada como A CONFIRMAR» do abastecimento (sim só na simulação): %s' % (tela, modo, d))
        x = [h for h in r['hist'] if 'nf-diesel-teste.jpg' in h['texto']]
        if len(r['hist']) != n0 + 1 or len(x) != 1 or x[0]['st'] != 'A CONFIRMAR' or x[0]['selo']: prob.append('%s (%s): o histórico devia ganhar 1 linha A CONFIRMAR da foto, sem selo: %d → %d linhas, %s' % (tela, modo, n0, len(r['hist']), x))
        if not eh_app(tela) and '1 A CONFIRMAR' not in r['histSub']: prob.append('%s (%s): o resumo do histórico diz %r' % (tela, modo, r['histSub']))
        prob += ['%s (%s): %s' % (tela, modo, e) for e in erros[:2]]
        ctx.close()
    ls = {'capitao.abast.v1': json.dumps([{'n': 'com-selo.jpg', 'd': '01/11/2026', 'st': 'A CONFIRMAR', 'fonte': 'foto enviada no app por Lucas', 'sim': True}, {'n': 'sem-selo.jpg', 'd': '02/11/2026', 'st': 'A CONFIRMAR', 'fonte': 'foto enviada no app por Lucas'}])}
    for modo, depois, esp in (('simulação', '', {'com-selo.jpg': False, 'sem-selo.jpg': False}), ('simulacao false', 'window.CapitaoDados.simulacao = false;', {'com-selo.jpg': True, 'sem-selo.jpg': False})):
        ctx, pg, erros = abre_g2(b, tela, depois=depois, ls=ls)
        r = pg.evaluate(LE_G2)
        got = {n: any(n in h['texto'] and h['selo'] for h in r['hist']) for n in esp}
        if got != esp: prob.append('%s (%s): o selo «apresentação» das fotos é %s (esperado %s)' % (tela, modo, got, esp))
        ctx.close()
    return prob


def teste_g2_real(b, tela):
    """G2, o caminho `null` → SEM DADOS / SEM LEITURA é do ramo simulacao false: o diesel é a última leitura salva (a de 26/09, dita com o dia e a hora), o último abastecimento e o consumido desde ele dizem SEM DADOS (o registro
    está vazio), o gráfico diz SEM DADOS com a leitura de agora, a aba Consumo diz SEM DADOS; nada de erro de script. Na simulação, nenhuma dessas frases."""
    prob = []
    for aba in ('nivel', 'consumo'):
        ctx, pg, erros = abre_g2(b, tela, aba=aba, depois='window.CapitaoDados.simulacao = false;')
        r = pg.evaluate(LE_G2)
        S = pg.evaluate("() => { const s = window.CapitaoDados.snapshot; return { quando: s.quando, hora: s.hora, litros: s.quadro.diesel_litros }; }")
        rot = '%s (simulacao false, %s)' % (tela, aba)
        ultima = 'Última leitura · ' + S['quando'][:5] + ' ' + S['hora'][:5]
        if ultima not in r['texto']: prob.append('%s: devia dizer a última leitura salva «%s»: %r' % (rot, ultima, r['resumo'] or r['texto'][:200]))
        if 'telemetria ao vivo' in r['texto'].lower() and aba == 'nivel': prob.append('%s: diz «telemetria ao vivo» sem o replay' % rot)
        if aba == 'nivel':
            if ('≈ %s' % nbp(S['litros'], 0, True)) not in (r['litros'] + r['kpis'].get('diesel', '')) : prob.append('%s: o diesel devia ser o da última leitura salva (%s L)' % (rot, S['litros']))
            if 'SEM DADOS' not in r['kpis'].get('ultimo', r['texto']) or 'SEM DADOS' not in r['kpis'].get('desde', ''): prob.append('%s: o último abastecimento e o consumido desde ele devem dizer SEM DADOS (registro vazio): %s' % (rot, {k: v[:50] for k, v in r['kpis'].items()}))
            if not r['graf'] or r['graf']['vazio'] is None or 'SEM DADOS' not in r['graf']['texto']: prob.append('%s: o gráfico sem série devia dizer SEM DADOS: %s' % (rot, r['graf']))
        else:
            if r['faixas'] or 'SEM DADOS' not in (r['coerencia'] + r['faixasSub']): prob.append('%s: sem o replay a aba Consumo devia dizer SEM DADOS e não listar faixas: %d faixas, %r' % (rot, len(r['faixas']), r['coerencia']))
        prob += ['%s: %s' % (rot, e) for e in erros[:2]]
        ctx.close()
    ctx, pg, erros = abre_g2(b, tela)
    r = pg.evaluate(LE_G2)
    if 'SEM DADOS' in r['texto'] or 'Última leitura' in r['texto']: prob.append('%s (simulação): a tela devia estar sem SEM DADOS nem «Última leitura»' % tela)
    ctx.close()
    # a simulação sem nenhuma linha de abastecimento (o dia de bordo sem a linha): a tela diz «nenhum registro» e traço, nunca SEM DADOS
    ctx, pg, erros = abre_g2(b, tela, depois='window.CapitaoDados.replay.diaDeBordo.abastecimento = null;')
    r = pg.evaluate(LE_G2)
    if r['hist'] or 'SEM DADOS' in r['texto'] or 'SEM LEITURA' in r['texto'] or 'nenhum registro' not in r['kpis'].get('ultimo', '') or achados_termos(tela, r['texto']): prob.append('%s (simulação sem linha de abastecimento): devia dizer «nenhum registro», sem SEM DADOS nem linha no histórico: %s %s' % (tela, r['kpis'].get('ultimo'), achados_termos(tela, r['texto'])))
    prob += ['%s (simulação sem linha de abastecimento): %s' % (tela, e) for e in erros[:2]]
    ctx.close()
    return prob


def teste_p4i_codigo():
    """O código das 4 telas: G1 ouve a virada do dia ('capitao-rebase') e o 'storage' e tira os dois ao desmontar, só dá setState se o texto mudou e nunca com a aba escondida na virada; G2 ouve também o tique da telemetria e tira os
    três; nenhum timer novo (só o da espera do cérebro); G2 carrega o capitao-grafico.js no <head> e usa o gráfico, o porFaixa() e os contadores; nada lê o D.snapshot nem escreve DEMO, R$ ou {{…}} em atributo geométrico de SVG; o app guarda os
    CRLF do arquivo e a web, os LF; a G1 chama as 4 funções de peça do cérebro e passa a quantidade e o mínimo do + PEÇA como o texto digitado."""
    prob = []
    for tela in TELAS_P4I:
        arq = tela + '.dc.html'
        h = le_arq(arq)
        t = h.replace('\r\n', '\n')
        g1 = tela.startswith('G1')
        for ev in (('capitao-rebase',) if g1 else ('capitao-telemetria', 'capitao-rebase')):
            if t.count("addEventListener('%s'" % ev) != 1 or t.count("removeEventListener('%s'" % ev) != 1: prob.append('%s: devia ouvir e tirar o ouvinte de %r uma vez' % (arq, ev))
        if t.count("addEventListener('storage'") != 1 or t.count("removeEventListener('storage'") != 1: prob.append('%s: o ouvinte do storage (registro em outra aba)' % arq)
        if "if (!document.hidden)" not in t: prob.append('%s: a virada do dia/o tique sem a guarda de document.hidden' % arq)
        if 'if (k === this._k) return;' not in t or t.count('setInterval') != 1 or t.count('setTimeout') < 1: prob.append('%s: só dá setState quando o texto muda (k === this._k) e o único setInterval é a espera do cérebro' % arq)
        cod = re.sub(r'//[^\n]*', '', t.split('<script type="text/x-dc"')[1])
        if re.search(r'D\.demo|\.demo\b|D\.aviso|D\.snapshot', cod): prob.append('%s: lê D.demo, D.aviso ou o D.snapshot (a leitura de 26/09)' % arq)
        if re.search(r'DEMO|R\$|demonstra|fict[ií]ci', t): prob.append('%s: DEMO, R$, demonstração ou fictício no código da tela' % arq)
        if MARCAS_FIXAS.search(cod): prob.append('%s: fabricante fixo no código: %s' % (arq, MARCAS_FIXAS.search(cod).group(0)))
        for l in cod.split('\n'):   # SEM DADOS / SEM LEITURA só no ramo simulacao false (falta(), sim ? ou !sim) e na constante SD
            if re.search(r'SEM (?:DADOS|LEITURA)', l) and not re.search(r"falta\(|sim \?|!sim|SD = 'SEM DADOS'", l): prob.append('%s: rótulo fora do ramo simulacao false: %s' % (arq, l.strip()[:100]))
        if GEOM_SVG.search(t): prob.append('%s: {{…}} em atributo geométrico de SVG' % arq)
        if arq.endswith('Mobile.dc.html'):
            if h.count('\r\n') != h.count('\n') or h.count('\n') < 100: prob.append('%s: o arquivo do app perdeu as quebras CRLF' % arq)
        elif '\r' in h: prob.append('%s: o arquivo da web ganhou CR' % arq)
        if g1:
            for f in ('B.usaPeca(', 'B.desfazUsoPeca(', 'B.ajustaPeca(', 'B.addPeca(', 'B.pecas()', 'B.loadPecas'):
                if f not in t: prob.append('%s: sem a chamada %s do cérebro' % (arq, f))
            if "B.addPeca({ n: s.fNome, qtd: s.fQtd, min: s.fMin," not in t: prob.append('%s: o + PEÇA devia passar a quantidade e o mínimo como o texto digitado (s.fQtd, s.fMin)' % arq)
            if 'capitao-grafico' in t: prob.append('%s: carrega o gráfico sem usar' % arq)
        else:
            head = t.split('</head>')[0]
            if '<script src="./capitao-grafico.js"></script>' not in head or head.index('capitao-grafico.js') < head.index('capitao-replay.js'): prob.append('%s: o capitao-grafico.js devia estar no <head>, depois do replay' % arq)
            for f in ('G.elemento(', 'R.porFaixa(', 'R.contadoresEm(', 'R.contadores(', 'A.instante('):
                if f not in t: prob.append('%s: sem %s' % (arq, f))
    return prob


LE_LAYOUT_P4I = r"""() => { const out = [], de = document.documentElement, lin = (x) => (x || '').replace(/\s+/g, ' ').trim();
  const lateral = Math.max(de.scrollWidth, document.body ? document.body.scrollWidth : 0) - de.clientWidth;
  for (const e of document.getElementById('dc-root').querySelectorAll('*')) {
    if (e.closest('capitao-faixa,capitao-cabecalho,capitao-topo-app,capitao-trilho,capitao-sos-web,capitao-sos-app,capitao-barra-chat,svg,[data-capitao-grafico]')) continue;
    const cs = getComputedStyle(e);
    if (!(e.clientWidth > 0) || !(e.scrollWidth > e.clientWidth + 1) || /(auto|scroll)/.test(cs.overflowX)) continue;
    const txt = lin(e.innerText); if (!txt) continue;
    if (!(cs.textOverflow === 'ellipsis' && lin(e.getAttribute('title')) === txt)) out.push(e.tagName.toLowerCase() + ' cortado (' + e.scrollWidth + ' px de conteúdo em ' + e.clientWidth + ')' + (cs.textOverflow === 'ellipsis' ? ' com reticências e sem a dica do texto inteiro' : '') + ': «' + txt.slice(0, 60) + '»');
  }
  return { lateral: lateral, cortes: out }; }"""


def teste_p4i_layout(b, tela):
    """Os estados de dentro das 4 telas, que a matriz (só a tela de abertura) não vê: G1 nas peças, com o formulário do + PEÇA aberto e com o erro do ✎; G2 com a estação meteorológica e na aba Consumo. Em 3 tamanhos e 2 temas: nenhuma rolagem
    lateral, nenhum texto cortado em silêncio (reticências só com a dica do texto inteiro)."""
    prob = []
    app = eh_app(tela)
    g1 = tela.startswith('G1')
    for w, h, tema in ([(360, 640, 'escuro'), (844, 390, 'escuro'), (390, 844, 'claro')] if app else [(1024, 768, 'escuro'), (1440, 900, 'escuro'), (1280, 720, 'claro')]):
        ctx, pg, erros = abre_tela(b, tela, w=w, h=h, tema=tema)
        pg.wait_for_timeout(300)
        def olha(estado):
            r = pg.evaluate(LE_LAYOUT_P4I)
            if r['lateral'] > 1: prob.append('%s %dx%d %s · %s: rola para o lado (%d px)' % (tela, w, h, tema, estado, r['lateral']))
            prob.extend('%s %dx%d %s · %s: %s' % (tela, w, h, tema, estado, x) for x in r['cortes'][:3])
        olha('abertura')
        if g1:
            pg.click('[data-g1=aba][data-aba=pecas]'); pg.wait_for_timeout(300); olha('peças')
            pg.click('[data-g1=nova]'); pg.wait_for_timeout(250); olha('+ PEÇA aberto')
            pg.click('[data-g1=peca][data-id=p03] [data-g1=editar]'); pg.wait_for_timeout(250)
            pg.fill('[data-g1=editar-campo]', '1e2'); pg.click('[data-g1=editar-ok]'); pg.wait_for_timeout(250); olha('✎ com o erro')
        else:
            pg.click('[data-g2=serie][data-s=estacao]'); pg.wait_for_timeout(450); olha('estação meteorológica')
            pg.click('[data-g2=aba][data-aba=consumo]'); pg.wait_for_timeout(350); olha('consumo')
        prob += ['%s %dx%d: %s' % (tela, w, h, e) for e in erros[:2]]
        ctx.close()
    return prob


def p4i_conferencias(b, lista):
    """[(nome, problemas)] das conferências da P4I para as telas da rodada."""
    out = []
    if any(t in lista for t in TELAS_P4I): out.append(('código das telas G1 e G2 (ouvintes, timers, DEMO, SVG, CRLF, o cérebro)', teste_p4i_codigo()))
    for tela in [t for t in TELAS_P4I if t in lista]:
        out.append((tela + ' · os estados de dentro (peças, formulário, erro do ✎, estação, consumo): sem rolagem lateral nem texto cortado em silêncio, em 3 tamanhos e 2 temas', teste_p4i_layout(b, tela)))
    for tela in [t for t in TELAS_G1 if t in lista]:
        out.append((tela + ' · os documentos: validade (hoje + prazo), situação do CapitaoAgora, cartões, a virada do dia e as perguntas ao docsvenc', teste_g1_documentos(b, tela)))
        out.append((tela + ' · o envio do documento (A CONFERIR, carimbo sim, selo apresentação)', teste_g1_envio(b, tela)))
        out.append((tela + ' · as peças: lista, aviso no mínimo, tarefas ligadas, cartões, filtro e abas', teste_g1_pecas_lista(b, tela)))
        out.append((tela + ' · −1 USADA e Desfazer', teste_g1_uso(b, tela)))
        out.append((tela + ' · ✎ e + PEÇA (inteiro puro, texto ao cérebro, erro explícito)', teste_g1_edita(b, tela)))
        out.append((tela + ' · o ramo simulacao false (SEM DADOS) e o selo das peças', teste_g1_real(b, tela)))
    for tela in [t for t in TELAS_G2 if t in lista]:
        out.append((tela + ' · o nível: diesel, último abastecimento, consumido, autonomia, histórico, regra e os gráficos', teste_g2_nivel(b, tela)))
        out.append((tela + ' · o consumo por faixa de rpm e a soma com os contadores', teste_g2_consumo(b, tela)))
        out.append((tela + ' · a foto da NF (A CONFIRMAR, carimbo sim, selo apresentação)', teste_g2_nf(b, tela)))
        out.append((tela + ' · o ramo simulacao false (SEM DADOS e a última leitura)', teste_g2_real(b, tela)))
    return out


MUTANTES_P4I = [
    # —— G1: os documentos ——
    ('a G1 web sem ouvir a virada do dia (as datas ficam as de antes)', 'G1-Documentos-Web.dc.html', [("window.addEventListener('capitao-rebase', this._onRebase);", "")], 'docs'),
    ('o cartão «vencem em 90 dias» da G1 web conta só até 60', 'G1-Documentos-Web.dc.html', [("x.dn <= 90 ? 'venc90'", "x.dn <= 60 ? 'venc90'")], 'docs'),
    ('a situação de todo documento da G1 web fixa em EM DIA', 'G1-Documentos-Web.dc.html', [("x.st = dd ? dd.st :", "x.st = dd ? 'EM DIA' :")], 'docs'),
    ('a G1 do app abre o chat da web na pergunta de cada documento', 'G1-Documentos-Mobile.dc.html', [("'H2-Home-Mobile.dc.html#q=' + encodeURIComponent('Situação e vencimento do documento: ' + x.n)", "'Main.dc.html#q=' + encodeURIComponent('Situação e vencimento do documento: ' + x.n)")], 'docs'),
    ('a G1 web sem o selo «apresentação» nas linhas enviadas', 'G1-Documentos-Web.dc.html', [("selo: x.sim === true && !sim", "selo: false")], 'envio'),
    ('a G1 do app mostra o selo «apresentação» também com a simulação', 'G1-Documentos-Mobile.dc.html', [("selo: x.sim === true && !sim", "selo: x.sim === true")], 'envio'),
    # —— G1: as peças ——
    ('o aviso da G1 web só lista as zeradas (as no mínimo somem)', 'G1-Documentos-Web.dc.html', [("pz.concat(pb)", "pz")], 'pecas'),
    ('a tarefa ligada da G1 do app sem o prazo (só o dia)', 'G1-Documentos-Mobile.dc.html', [("prazo: (p.rot || '')", "prazo: ('')")], 'pecas'),
    ('o −1 USADA da G1 web não chama o cérebro (a quantidade só muda na tela)', 'G1-Documentos-Web.dc.html', [("const u = B.usaPeca(p.id);", "const u = { id: p.id, ant: p.qtd, novo: p.qtd - 1, iso: 'x' };")], 'uso'),
    ('o Desfazer da G1 do app diz que desfez mesmo com a recusa do cérebro', 'G1-Documentos-Mobile.dc.html', [("const r = B.desfazUsoPeca({ id: u.id, ant: u.ant, novo: u.novo, iso: u.iso });", "const r = B.desfazUsoPeca({ id: u.id, ant: u.ant, novo: u.novo, iso: u.iso }) || { qtd: u.ant };")], 'uso'),
    ('o + PEÇA da G1 web passa a quantidade e o mínimo como número (1e2 vira 100)', 'G1-Documentos-Web.dc.html', [("B.addPeca({ n: s.fNome, qtd: s.fQtd, min: s.fMin,", "B.addPeca({ n: s.fNome, qtd: Number(s.fQtd), min: Number(s.fMin),")], 'edita'),
    ('o + PEÇA recusado pelo cérebro fica sem mensagem na G1 do app', 'G1-Documentos-Mobile.dc.html', [("if (!it) return this.setState({ formErro:", "if (!it) return; this.setState({ formErro:")], 'edita'),
    ('o ✎ da G1 web não confere o inteiro (1e2 chega ao cérebro)', 'G1-Documentos-Web.dc.html', [("if (!this.inteiro(v)) return this.setState", "if (false) return this.setState")], 'edita'),
    # —— G1: o ramo simulacao false ——
    ('a G1 web diz SEM DADOS também na simulação (documento sem prazo)', 'G1-Documentos-Web.dc.html', [("const falta = (rot) => (sim ? 'sem prazo' : rot);", "const falta = (rot) => rot;")], 'real_g1'),
    # —— G2: o nível ——
    ('a G2 web mostra o diesel da última leitura de 26/09 (848 L)', 'G2-Abastecimento-Web.dc.html', [("const litros = q && num(q.diesel_litros)", "const litros = '848'; const _x = q && num(q.diesel_litros)")], 'nivel'),
    ('a G2 do app usa a autonomia do D (11,2 h) e não a do instante', 'G2-Abastecimento-Mobile.dc.html', [("const aut = calc.autonomia", "const aut = D.autonomia")], 'nivel'),
    ('a G2 web não assina o tique da telemetria (a leitura para)', 'G2-Abastecimento-Web.dc.html', [("window.addEventListener('capitao-telemetria', this._onTele);", "")], 'nivel'),
    ('o gráfico «Diesel válido» da G2 web desenha a água', 'G2-Abastecimento-Web.dc.html', [("['diesel', 'Diesel válido', 'diesel']", "['diesel', 'Diesel válido', 'agua']")], 'nivel'),
    ('o TWA da G2 do app troca BE por BB', 'G2-Abastecimento-Mobile.dc.html', [("twa >= 0 ? 'BE' : 'BB'", "twa >= 0 ? 'BB' : 'BE'")], 'nivel'),
    ('as janelas do gráfico da G2 do app não fazem nada', 'G2-Abastecimento-Mobile.dc.html', [("onClick: () => { if (!off) this.setState({ janela: k }); }", "onClick: () => {}")], 'nivel'),
    # —— G2: o consumo ——
    ('o total do consumo da G2 web esquece o gerador', 'G2-Abastecimento-Web.dc.html', [("const total = sL !== null ? sL + sG : null;", "const total = sL !== null ? sL : null;")], 'consumo'),
    ('o L/h da faixa da G2 do app é o de cruzeiro da base', 'G2-Abastecimento-Mobile.dc.html', [("lph: f.seg ? nb(f.lph)", "lph: f.seg ? nb(cz.lph)")], 'consumo'),
    # —— G2: a foto da NF ——
    ('a foto da NF da G2 web não vai ao diário', 'G2-Abastecimento-Web.dc.html', [("B.addDiario({ sys: 'Combustível'", "(() => {})({ sys: 'Combustível'")], 'nf'),
    ('a foto da NF da G2 do app entra como CONFERIDO', 'G2-Abastecimento-Mobile.dc.html', [("st: 'A CONFIRMAR'", "st: 'CONFERIDO'")], 'nf'),
    ('a G2 web diz SEM DADOS também na simulação', 'G2-Abastecimento-Web.dc.html', [("falta = (rot) => (sim ? '—' : rot)", "falta = (rot) => rot")], 'real_g2'),
    # —— o código ——
    ('a G1 web não tira o ouvinte da virada do dia ao desmontar', 'G1-Documentos-Web.dc.html', [("window.removeEventListener('capitao-rebase', this._onRebase);", "")], 'codigo'),
    ('a G2 do app não tira o ouvinte da telemetria ao desmontar', 'G2-Abastecimento-Mobile.dc.html', [("window.removeEventListener('capitao-telemetria', this._onTele);", "")], 'codigo'),
]
QUAL_P4I = {'docs': teste_g1_documentos, 'envio': teste_g1_envio, 'pecas': teste_g1_pecas_lista, 'uso': teste_g1_uso, 'edita': teste_g1_edita, 'real_g1': teste_g1_real,
            'nivel': teste_g2_nivel, 'consumo': teste_g2_consumo, 'nf': teste_g2_nf, 'real_g2': teste_g2_real, 'codigo': lambda b, t: teste_p4i_codigo()}


def mutantes_p4i(b):
    global MUT_ARQ
    vivos = []
    filtro = os.environ.get('MUT_FILTRO', '')   # só os mutantes cujo nome tem este texto (para refazer um)
    for nome, arq, trocas, qual in MUTANTES_P4I:
        if filtro and filtro not in nome: continue
        src = open(os.path.join(RAIZ, arq), encoding='utf-8', newline='').read()
        faltam = [x for x, _ in trocas if src.count(x) != 1]
        if faltam:
            print('ERRO no mutante «%s»: o trecho não está uma vez em %s: %s' % (nome, arq, faltam)); vivos.append(nome); continue
        MUT_ARQ = {arq: trocas}
        sai = sys.stdout
        prob = []
        try:
            sys.stdout = open(os.devnull, 'w')
            prob = QUAL_P4I[qual](b, arq.replace('.dc.html', ''))
        except Exception as e:   # um erro do próprio teste não conta como acusação: o mutante fica vivo
            sys.stdout = sai
            print('ERRO do teste no mutante «%s»: %s' % (nome, str(e).splitlines()[-1][:160]))
            prob = []
        finally:
            sys.stdout = sai
            MUT_ARQ = {}
        print('MUTANTE %s: %s (%d problema(s))%s' % ('ACUSADO' if prob else 'VIVO', nome, len(prob), ' · ' + prob[0][:150] if prob else ''))
        if not prob: vivos.append(nome)
    print('%d mutantes · %d vivos' % (len(MUTANTES_P4I), len(vivos)))
    return vivos


def teste_offline(b, lista, paginas=()):
    """1ª visita com internet (SW instala), confere no cache da instalação cada tela e página da rodada, depois abre cada tela sem
    rede. unpkg.com fora do ar o tempo todo: nenhum pedido a ele. Com "dados" na lista: a página dos Dados do aparelho também abre
    sem rede (CORE do sw.js), com a lista e o ∞, depois das telas."""
    prob = []
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script(SESSAO)
    aplica_mut(ctx)
    unpkg = corta_unpkg(ctx)
    pg = ctx.new_page()
    pg.goto(BASE + 'Main.dc.html', wait_until='load')
    try:
        pg.wait_for_function("() => navigator.serviceWorker && navigator.serviceWorker.controller", timeout=30000)
    except Exception:
        ctx.close()
        return ['service worker não instalou em 30 s (arquivo do CORE faltando? ex.: Guia-Rapido-Capitao-IA.pdf)']
    pg.wait_for_timeout(1500)
    # React no CORE do sw.js: a 1ª visita carregou o React antes de o SW controlar a tela, então só a instalação o põe no
    # cache. Sem esta conferência a falta passaria: offline, o cache HTTP do navegador ainda serve o React ao SW.
    guardou = pg.evaluate('(us) => Promise.all(us.map((u) => caches.match(u).then(Boolean)))', [REACT_LOCAL + arq for arq in REACT_ARQS])
    if guardou != [True, True]:
        prob.append('React fora do CORE do sw.js: a instalação não guardou %s' % ', '.join(arq for arq, g in zip(REACT_ARQS, guardou) if not g))
    # P4B: o motor da reprodução também sai do cache da instalação (o cache HTTP do navegador esconderia a falta na abertura sem rede, como no React)
    if not pg.evaluate('(u) => caches.match(u).then(Boolean)', BASE + 'capitao-replay.js'):
        prob.append('capitao-replay.js fora do CORE do sw.js: a instalação não o guardou (offline a tela não anda)')
    # P4C: o gráfico, o mapa de sensores e os dois desenhos também saem do cache da instalação (offline a Ponte não desenha o histórico e A4/A5 não desenham o barco)
    for arq in ('capitao-grafico.js', 'capitao-sensores.js', 'assets/sensores-perfil.svg', 'assets/sensores-planta.svg', 'capitao-faq.js', 'faq-equipamentos.json'):   # (P4H: a F6 não lista o FAQ sem o módulo e o arquivo)
        if not pg.evaluate('(u) => caches.match(u).then(Boolean)', BASE + arq): prob.append('%s fora do CORE do sw.js: a instalação não o guardou' % arq)
    # Cada tela e página desta rodada no cache da instalação (TELAS/CORE do sw.js), conferido no cache como o React: depois da
    # 1ª página aberta sem rede, o modo offline do Playwright nem sempre alcança o SW (que busca na rede e abre a tela), então só
    # a abertura sem rede abaixo deixava passar uma tela fora do cache — menos a 1ª da lista.
    arqs = [tela + '.dc.html' for tela in lista] + [PAGINAS[n][0].split('?')[0] for n in paginas]
    guardou = pg.evaluate('(us) => Promise.all(us.map((u) => caches.match(u).then(Boolean)))', [BASE + a for a in arqs])
    fora = [a for a, g in zip(arqs, guardou) if not g]
    if fora:
        prob.append('fora do cache da instalação (TELAS/CORE do sw.js): ' + ', '.join(fora))
    ctx.set_offline(True)
    for tela in lista:
        erros = []
        pg2 = ctx.new_page()
        pg2.on('pageerror', lambda e: erros.append(str(e)[:200]))
        try:
            pg2.goto(BASE + tela + '.dc.html', wait_until='load', timeout=20000)
            pg2.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
        except Exception as e:
            prob.append(tela + ' não abriu offline: ' + str(e)[:120])
        # marca (assets/) e o ∞ do botão CONVERSA também saem da cópia guardada (CORE do sw.js)
        try:
            pg2.wait_for_timeout(600)
            falta = pg2.evaluate("""async () => {
  const f = [...document.images].filter((i) => /\\/assets\\//.test(i.src) && i.complete && !i.naturalWidth).map((i) => i.src.split('/').pop());
  if (document.querySelector('capitao-simbolo')) {
    for (let n = 0; n < 50 && !customElements.get('capitao-simbolo'); n++) await new Promise((ok) => setTimeout(ok, 100));
    if (!customElements.get('capitao-simbolo')) f.push('capitao-simbolo.js');
  }
  return f;
}""")
            if falta:
                prob.append(tela + ' offline sem: ' + ', '.join(falta))
            if tela in TELAS_SOS:
                prob += [tela + ' offline: ' + x for x in problemas_barco_sos(pg2)]
            # P4B: o motor da reprodução vem da cópia guardada (CORE do sw.js) e anda sem rede: o arquivo responde 200 e o quadro() não é nulo (o SOS só confere o arquivo)
            rp = pg2.evaluate("""async () => { const st = await fetch('./capitao-replay.js').then((r) => r.status, () => 'falhou'); let q = null;
  try { q = window.CapitaoReplay && typeof window.CapitaoReplay.quadro === 'function' ? window.CapitaoReplay.quadro() : null; } catch (e) {}
  return { st, tipo: typeof window.CapitaoReplay, quadro: !!q && typeof q.sog_nos === 'number' }; }""")
            if rp['st'] != 200: prob.append('%s offline: capitao-replay.js respondeu %s (esperado 200)' % (tela, rp['st']))
            if tela in TELAS_SOS:
                if rp['tipo'] != 'undefined': prob.append('%s offline: o SOS carregou o CapitaoReplay' % tela)
            elif rp['tipo'] != 'object' or not rp['quadro']: prob.append('%s offline: CapitaoReplay.quadro() nulo (typeof %s)' % (tela, rp['tipo']))
            if tela in TELAS_F6:   # P4H: a F6 monta os 91 itens com o arquivo e o módulo da cópia guardada
                fx = pg2.evaluate("""async () => { for (let n = 0; n < 60 && !(window.CapitaoFAQ && window.CapitaoFAQ.pronto()); n++) await new Promise((ok) => setTimeout(ok, 100));
                  return { pronto: !!(window.CapitaoFAQ && window.CapitaoFAQ.pronto()), itens: document.querySelectorAll('[data-f6=item]').length }; }""")
                if not fx['pronto'] or fx['itens'] != len(FAQ_JSON['itens']): prob.append('%s offline: o FAQ não montou os %d itens (%s)' % (tela, len(FAQ_JSON['itens']), fx))
            if tela in TELAS_PONTE or tela in TELAS_SENSORES:   # P4C: o gráfico monta a série e o mapa desenha os 22 pontos sobre o SVG da cópia guardada
                gx = pg2.evaluate("""async () => ({ grafico: window.CapitaoGrafico ? window.CapitaoGrafico.dados('rpm', '150S').ok : null, svg: await Promise.all(['assets/sensores-perfil.svg', 'assets/sensores-planta.svg'].map((u) => fetch('./' + u).then((r) => r.status, () => 'falhou'))),
                  pontos: document.querySelectorAll('[data-ponto]').length, svgs: document.querySelectorAll('[data-capitao-grafico] svg').length })""")
                if tela in TELAS_PONTE and (gx['grafico'] is not True or gx['svgs'] != 1): prob.append('%s offline: o gráfico não monta a série (%s)' % (tela, gx))
                if tela in TELAS_SENSORES and (gx['svg'] != [200, 200] or gx['pontos'] != 22): prob.append('%s offline: desenhos %s e %d pontos (esperado 200, 200 e 22)' % (tela, gx['svg'], gx['pontos']))
        except Exception as e:
            prob.append(tela + ' offline: ' + str(e)[:120])
        if erros:
            prob.append(tela + ' offline com erro: ' + erros[0])
        pg2.close()
    # dados.html sem rede depois das telas: a 1ª página aberta sem rede continua sendo a 1ª tela da lista (Main, na rodada
    # inteira), a única em que o corte da rede alcança o SW com certeza.
    if 'dados' in paginas:
        pg5 = ctx.new_page()
        erros5 = []
        pg5.on('pageerror', lambda e: erros5.append(str(e)[:200]))
        try:
            pg5.goto(BASE + 'dados.html', wait_until='load', timeout=20000)
            pg5.wait_for_timeout(400)
            r = pg5.evaluate("""() => ({ titulo: document.title, lista: (document.getElementById('lista') || {}).textContent || '',
  falta: [...document.images].filter((i) => i.src.indexOf('/assets/') >= 0 && (!i.complete || !i.naturalWidth)).map((i) => i.src.split('/').pop()) })""")
            if r['titulo'] != 'Dados do aparelho · Capitão IA' or 'lendo' in r['lista']:
                prob.append('dados.html offline: %r · %r' % (r['titulo'], r['lista'][:60]))
            if r['falta']:
                prob.append('dados.html offline sem: ' + ', '.join(r['falta']))
        except Exception as e:
            prob.append('dados.html offline: ' + str(e)[:120])
        if erros5:
            prob.append('dados.html offline com erro: ' + erros5[0])
        pg5.close()
    # P4B: o SOS do login abre sem rede e sem login: o login guardado (CORE) tem o botão e ele leva à tela de emergência do computador (S1), com o roteiro do canal 16
    pg6 = ctx.new_page()
    erros6 = []
    pg6.on('pageerror', lambda e: erros6.append(str(e)[:200]))
    try:
        pg6.goto(BASE + 'login.html', wait_until='load', timeout=20000)
        pg6.click('a[href*="SOS-"]', timeout=5000)
        pg6.wait_for_function("() => document.body && /CANAL 16|MAYDAY/.test(document.body.innerText)", timeout=15000)
        if not pg6.url.split('#')[0].endswith('S1-SOS-Web.dc.html'): prob.append('o SOS do login offline abriu %s (esperado S1-SOS-Web.dc.html, sem login)' % pg6.url)
    except Exception as e:
        prob.append('o SOS do login não abriu offline: ' + str(e)[:120])
    if erros6:
        prob.append('o SOS do login offline com erro: ' + erros6[0])
    pg6.close()
    # lista (index.html): a assinatura sai da cópia guardada (CORE)
    pg4 = ctx.new_page()
    try:
        pg4.goto(BASE + 'index.html?v=lista', wait_until='load', timeout=20000)
        falta = pg4.evaluate("() => [...document.images].filter((i) => i.src.indexOf('/assets/') >= 0 && (!i.complete || !i.naturalWidth)).map((i) => i.src.split('/').pop())")
        if falta:
            prob.append('lista offline sem: ' + ', '.join(falta))
    except Exception as e:
        prob.append('lista offline: ' + str(e)[:120])
    pg4.close()
    # rosto da conversa por voz: entra à parte (capitao-voz.js), tem de vir da cópia guardada
    pg3 = ctx.new_page()
    try:
        pg3.goto(BASE + 'S2-SOS-Mobile.dc.html', wait_until='load', timeout=20000)
        st = pg3.evaluate("() => fetch('./capitao-rosto.js').then((r) => r.status, () => 'falhou')")
        if st != 200:
            prob.append('capitao-rosto.js offline: ' + str(st))
    except Exception as e:
        prob.append('capitao-rosto.js offline: ' + str(e)[:120])
    pg3.close()
    ctx.close()
    if unpkg:
        prob.append('%d pedido(s) ao unpkg no teste offline (o React sai da cópia guardada de assets/vendor): %s' % (len(unpkg), unpkg[0]))
    return prob


if __name__ == '__main__':
    main()
