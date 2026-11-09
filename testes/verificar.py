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
    'Main', 'H2-Home-Mobile',
    'F1-FAQ-Hub-Web', 'F1-FAQ-Hub', 'F2-FAQ-Estabilizador-Web', 'F2-FAQ-Estabilizador', 'F3-FAQ-Eletronicos-Web', 'F3-FAQ-Eletronicos',
    'E2-Navegando-Sintoma', 'F4-FAQ-Gerador-Web', 'F4-FAQ-Gerador', 'F5-FAQ-Climatizacao-Web', 'F5-FAQ-Climatizacao',
    'G1-Documentos-Web', 'G1-Documentos-Mobile', 'G2-Abastecimento-Web', 'G2-Abastecimento-Mobile', 'G4-Equipe-Web', 'G4-Equipe-Mobile',
)   # (19 telas em 09/11/2026, depois da P4E: C1 e C3 saíram (a C2, a C4 web e app já nascem limpas). 21 depois da P4D: B1 e B2 saíram (a B3 já estava limpa). 23 depois da P4C: A1 e A2 saíram (e a A3, a A4 e a A5 já nascem limpas). Eram 25 depois da P4B: a moldura e o chip do clima já saíram; A3, B3, C2, E1, G3 e H3 já estão limpas e a varredura as vigia. A E2 mostra «snapshot 26/09/2026 10:12»
#  no 1º meio segundo, antes de a leitura do replay entrar: a varredura a 900 ms pega, a sonda a 1,5 s não pegava)
FORA_ATE_FASE_8 = ('Manual-Capitao-IA',)
# Telas cuja leitura ainda não anda sem o replay congelado (a C3 vira alerta vivo na Fase 4): a mesma regra, a lista só encolhe.
PENDENTES_MUDA = ()   # (a C3 saiu na P4E: virou alerta vivo)
MUDA_SEM_FIXO = ('Main', 'A1-Ponte-Web', 'A2-Ponte-Mobile', 'A4-Sensores-Web', 'A5-Sensores-Mobile', 'B1-Carta-Web', 'B2-Carta-Mobile', 'C1-Leme-Web', 'C2-Leme-Mobile', 'C3-Leme-Alerta', 'C4-Checklist-Web', 'C4-Checklist-Mobile', 'E1-Navegando-Gatilhos')
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
  return { seg: EQ.filter((e) => e.seguranca).map((e) => ({ id: e.id, fabricante: e.fabricante, modelo: e.modelo })), texto: textos.join('\n'), chats: chats,
           cartoes: cartoes, cortados: cortados, repetidos: repetidos, perguntas: P.map((p) => p.q) };
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
        for i, alvo in (('vhf', 'VHF'), ('audio', 'Fusion')):
            h = r['cartoes'].get(i) or ''
            m = re.search(r'F3-FAQ-Eletronicos(?:-Web)?\.dc\.html#p=(\d+)$', h)
            n = int(m.group(1)) if m else 0
            if not (0 < n <= len(r['perguntas']) and alvo in r['perguntas'][n - 1]):
                prob.append('cartão %s da F1 não abre a pergunta de %s no FAQ de eletrônicos: %r' % (i, alvo, h))
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
    """Selo que sobrou na tela (r = CHECA). Main e H2: a caixa do cabeçalho é a ÚLTIMA LEITURA, nunca vazia nem SNAPSHOT; SOS sem caixa."""
    prob = []
    if SELO_RE.search(r['rodapeTxt']): prob.append('selo no rodapé: %r' % r['rodapeTxt'][:120])
    ruins = [t for t in r['selos'] if SELO_RE.search(t) or 'SNAPSHOT' in t.upper()]
    if ruins: prob.append('caixa de selo: %s' % ruins[:3])
    if tela in ('Main', 'H2-Home-Mobile') and (r['selos'] != [r['ultima']] or not r['ultima']):
        prob.append('caixa do cabeçalho %s (esperado só %r)' % (r['selos'][:3], r['ultima']))
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
            esp = ('H2-Home-Mobile.dc.html' if app else 'Main.dc.html') + '#q=' + urllib.parse.quote(r['faq'][i['faq']] or '', safe="!~*'()")
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
    for arq in ('capitao-grafico.js', 'capitao-sensores.js', 'assets/sensores-perfil.svg', 'assets/sensores-planta.svg'):
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
