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
sem ela, SEM DADOS e nenhum vento previsto.
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
Equipamento de segurança fora de Equipamentos, Leme e Documentos (CONTRATO-DADOS §1.4, C5): na F1 (web e app) e na E2, nenhum
modelo do EPIRB nem do Seafire no texto visível e nos atributos (na E2 também com cada sistema e cada sintoma escolhidos), nenhum
link do chat (#q=) com o fabricante deles, e, na F1, o cartão do VHF e o do áudio abrem a pergunta certa do FAQ de eletrônicos
(#p= > 0, na pergunta de "VHF" e na de "Fusion"), pelas palavras do equipamento.

Uso (site servido em http://127.0.0.1:8765):
    python testes/verificar.py                     todas as telas, todos os tamanhos e temas
    python testes/verificar.py Main S2-SOS-Mobile  só essas telas (login, index e dados: as páginas fora das TELAS)
    python testes/verificar.py --fotos             salva capturas em testes/saida/
    python testes/verificar.py --offline           testa a abertura offline depois da 1ª visita
    python testes/verificar.py --so-offline        só o teste offline (sem a matriz)
Navegador: Edge instalado (channel="msedge").
"""
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


SESSAO = "(() => { const n = Date.now(); localStorage.setItem('capitao.sessao.v1', JSON.stringify({ u: 'lucas', em: n, exp: n + 3600e3 })); })()"
# páginas fora das TELAS do sw.js: nome → (endereço, com sessão). O login com sessão redireciona; a lista precisa de ?v=lista.
PAGINAS = {'login': ('login.html', False), 'index': ('index.html?v=lista', True), 'dados': ('dados.html', True)}
MEDE_LOGIN = """() => { const q = (s) => { const e = document.querySelector(s); return e ? e.getBoundingClientRect().bottom : null; };
  return { go: q('#go'), credito: q('.credito') }; }"""
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
# notas e os textos dos guias nos commits seguintes do gerador, mmsiNota e o "no barco real" do guia na 1b): o casamento é do D
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
  return { lateral: lateral, deform: deform, prancheta: prancheta, titulo: document.title, rodape: rodape, rodapeTxt: rodapeTxt, selos: selos, ultima: ultima, seloTexto: seloTexto, afirma: afirma };
}"""
# SOS sem o registro gerado (trava §2.1; C4): o embarcacao.registro e "REG." no texto visível e nos atributos de S1/S2.
# Revisão do C4: o roteiro MAYDAY (<sc-if value="{{mayday}}">) e os passos de cada cartão (<sc-if value="{{p.open}}">) só existem
# no DOM depois do toque, e o roteiro é o texto lido no rádio, onde uma identificação gerada entraria primeiro. TEXTOS_SOS lê a tela
# fechada, com o roteiro aberto e com cada cartão aberto (um de cada vez, que a tela só abre um), e devolve a tela ao estado
# inicial; sem abrir o roteiro e todos os cartões, a conferência não vale. A 1b reaproveita os textos (MMSI, coordenada, modelo).
# Revisão 2 do C4: e o fabricante, o modelo, a marca, o rotulo, a motorizacao e o motor (confere.barco_sos, a regra do gerador
# sobre o protocolos, tirada do próprio D). Sem os números (ano, dimensões, tanques): a tela do SOS mostra o clima real, e uma
# ondulação de "1,1 m" seria o calado; no protocolos, que é só texto gerado, o gerador confere os números também. Sem a base até
# a 1b, que a tira do cabeçalho da S1 (CONTRATO §1.2) e acrescenta aqui.
TELAS_SOS = ('S1-SOS-Web', 'S2-SOS-Mobile')
TEXTOS_SOS = r"""async () => {
  const E = (window.CapitaoDados || {}).embarcacao || {}, barco = {}; ['nome', 'registro', 'fabricante', 'modelo', 'rotulo', 'motorizacao'].forEach((k) => { if (typeof E[k] === 'string') barco[k] = E[k]; });
  const textos = [];
  const le = () => {
    textos.push(document.body ? document.body.innerText : '');
    document.querySelectorAll('[title],[aria-label],[alt],[href]').forEach((e) => ['title', 'aria-label', 'alt', 'href'].forEach((a) => { const v = e.getAttribute(a); if (v) textos.push(v); }));
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
  return { barco: barco, texto: textos.join('\n'), roteiro: roteiro, cartoes: n, abertos: abertos, inicial: inicial };
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


BARCO_SOS = ('registro', 'fabricante', 'modelo', 'rotulo', 'motorizacao')   # o D tem de ter todos (senão a conferência não vale)


def problemas_barco_sos(pg):
    """S1/S2 (trava §2.1): nem "REG." nem dado gerado da embarcação além do nome (confere.barco_sos sem os números e sem a base:
    registro, fabricante, modelo, marca, rotulo, motorizacao e motor) na tela, também no roteiro MAYDAY e nos passos de cada
    cartão; sem esses campos no D, a conferência não vale."""
    r, prob = textos_sos(pg)
    E = r['barco']
    falta = [k for k in BARCO_SOS if not E.get(k)]
    if falta: prob.append('D sem embarcacao.%s: a conferência do dado da embarcação no SOS não vale' % ', '.join(falta))
    achados = []
    for campo, txt, _ in confere.acha_barco(r['texto'], E, confere.barco_sos(E, numeros=False, base=False)):
        a = '%s %r' % (campo, txt)
        if a not in achados: achados.append(a)
    if re.search(r'(?:^|[^A-Za-zÀ-ÿ])REG\.', r['texto']): achados.append('"REG."')
    if achados: prob.append('SOS mostra ' + ' e '.join(achados) + ' (trava §2.1: só o nome da embarcação)')
    return prob


# Equipamento de segurança (EPIRB e Seafire: seguranca no capitao-dados.js) só em Equipamentos, Leme e Documentos (CONTRATO-DADOS
# §1.4, C5). Na F1 e na E2: o modelo nunca no texto nem nos atributos; o fabricante nunca no link do chat (#q=); na F1, o VHF e o
# áudio abrem a pergunta deles no FAQ de eletrônicos (as palavras do equipamento). Na E2, a leitura passa por cada sistema e sintoma.
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
  const cartoes = {};
  document.querySelectorAll('a[href]').forEach((a) => { const n = (a.innerText || '').split('\n')[0].trim(); const e = EQ.find((x) => x.nome === n); if (e && !cartoes[e.id]) cartoes[e.id] = a.getAttribute('href'); });
  return { seg: EQ.filter((e) => e.seguranca).map((e) => ({ id: e.id, fabricante: e.fabricante, modelo: e.modelo })), texto: textos.join('\n'), chats: chats,
           cartoes: cartoes, perguntas: P.map((p) => p.q) };
}"""


def problemas_seguranca(pg, tela):
    """F1 e E2 (CONTRATO-DADOS §1.4, C5): sem modelo do EPIRB e do Seafire na tela, sem o fabricante deles no link do chat e, na F1,
    o VHF e o áudio abrindo a pergunta certa. Sem os dois equipamentos de segurança no D, a conferência não vale."""
    r = pg.evaluate(TEXTOS_SEGURANCA, tela.startswith('E2-'))
    prob = []
    if sorted(e['id'] for e in r['seg']) != ['epirb', 'seafire']:
        prob.append('D sem EPIRB e Seafire com seguranca: a conferência do equipamento de segurança não vale')
    for e in r['seg']:
        for n in confere.candidatos_modelo(e['fabricante'], e['modelo']):
            if next(confere.acha_nomes(r['texto'], n), None):
                prob.append('modelo do %s na tela (só em Equipamentos, Leme e Documentos, §1.4)' % e['id'])
                break
        ruins = sorted({q for q in r['chats'] if next(confere.acha_nomes(q, e['fabricante']), None)})
        if ruins:
            prob.append('link do chat com o fabricante do %s: %s' % (e['id'], ruins[:2]))
    if tela.startswith('F1-'):
        for i, alvo in (('vhf', 'VHF'), ('audio', 'Fusion')):
            h = r['cartoes'].get(i) or ''
            m = re.search(r'F3-FAQ-Eletronicos(?:-Web)?\.dc\.html#p=(\d+)$', h)
            n = int(m.group(1)) if m else 0
            if not (0 < n <= len(r['perguntas']) and alvo in r['perguntas'][n - 1]):
                prob.append('cartão %s da F1 não abre a pergunta de %s no FAQ de eletrônicos: %r' % (i, alvo, h))
    return prob


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


def main():
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
        for tema in (() if so_offline else ('escuro', 'claro')):
            for tela in lista:
                tamanhos = APP if eh_app(tela) else WEB
                for (w, h) in tamanhos:
                    total += 1
                    movel = eh_app(tela)  # celular, inclusive deitado (844×390): toque + UA móvel
                    ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None,
                                        is_mobile=movel, has_touch=movel, service_workers='block')
                    ctx.add_init_script(SESSAO + ";localStorage.setItem('capitao.tema.v1', '" + tema + "');localStorage.setItem('capitao.plataforma.v1', '" + ('app' if eh_app(tela) else 'web') + "');")
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
                    if tela in TELAS_SEGURANCA: prob += problemas_seguranca(pg, tela)
                    if fotos:
                        pg.screenshot(path=os.path.join(SAIDA, '%s_%s_%dx%d.png' % (tela, tema, w, h)))
                    if prob:
                        falhas.append({'tela': tela, 'tema': tema, 'tam': '%dx%d' % (w, h), 'prob': prob})
                        print('FALHA', tela, tema, '%dx%d' % (w, h), ' | '.join(prob))
                    ctx.close()
            for nome in paginas:
                end, com_sessao = PAGINAS[nome]
                for (w, h) in WEB + APP:
                    total += 1
                    movel = (w, h) in APP
                    ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None,
                                        is_mobile=movel, has_touch=movel, service_workers='block')
                    ctx.add_init_script((SESSAO + ';' if com_sessao else '') + "localStorage.setItem('capitao.tema.v1', '" + tema + "');")
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
           duasLinhas: !!vr && vr.top > hora.bottom - 1, altura: r.height / (H.height || 1) };
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
        if 'SEM DADOS' not in r['titulo']: prob.append('sem rede: title do vento sem SEM DADOS: ' + r['titulo'])
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
    capitao-clima.js grava) entra no clima e no "seguro para sair?", com fonte e hora; sem ela, SEM DADOS. Open-Meteo fora (abort)."""
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
                if 'SEM DADOS' not in t or 'vento até' in t or 'rajadas até' in t or r['windy']:
                    prob.append(tag + ': inventou vento ou perdeu o SEM DADOS: ' + t[:300].replace('\n', ' / '))
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
        pg.evaluate(GRAVA_LS, dict(SEGREDOS, **{'capitao.diario.v1': json.dumps([L_B, L_A]), 'capitao.executado.v1': json.dumps({'t1': feita(20)}),
                                             'capitao.docs.v1': json.dumps([D_B, D_A]), 'capitao.abast.v1': json.dumps([N_B, N_A]),
                                             'capitao.equipe.v1': json.dumps({'fones': {'Marinheiro': 'tel-teste-1'}, 'convites': []}), 'capitao.tema.v1': 'escuro'}))
        pg.reload(wait_until='load')
        pg.wait_for_timeout(300)
        lista = pg.inner_text('#lista')
        if 'Diário de bordo · 2 linhas' not in lista or 'Documentos enviados · 2 documentos' not in lista \
                or 'Abastecimentos enviados · 2 abastecimentos' not in lista or 'segredo' in lista or 'sessao' in lista:
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
        vazou = [x for x in ['capitao.sessao', 'segredo-teste', 'capitao.login', 'capitao.ia.', 'capitao.telemetria', 'capitao.voz', 'capitao.clima'] if x in texto]
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
               'capitao.ia.chave.v1': 'chave-do-arquivo', 'capitao.login.tentativas.v1': '{}', 'capitao.diario.v1': linhas}}
        r = escolhe({'name': 'copia.json', 'mimeType': 'application/json', 'buffer': json.dumps(mao).encode('utf-8')})
        if not r['previa'] or 'sess' in r['resumo'].lower() or 'chave' in r['resumo'].lower(): p.append('prévia: %r' % r['resumo'])
        restaura()
        tudo = ls()
        # Antes a linha sem âncora no aparelho ia para o fim ([C, B, A, D]); D (23/10) é a mais nova e o app lê a lista com a mais
        # nova primeiro (A2 "último", diarioLer): ela entra no topo. Mudado na revisão da F25.
        if diario() != [L_D, L_C, L_B, L_A]: p.append('diário: %s (esperado D, C, B, A)' % [x.get('t', '?')[6:7] for x in (diario() or [])])
        if tudo.get('capitao.ia.chave.v1') != SEGREDOS['capitao.ia.chave.v1'] or '"lucas"' not in (tudo.get('capitao.sessao.v1') or '') \
                or tudo.get('capitao.login.tentativas.v1') != SEGREDOS['capitao.login.tentativas.v1']:
            p.append('sessão, tentativas ou chave da IA vieram do arquivo')

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


def teste_offline(b, lista, paginas=()):
    """1ª visita com internet (SW instala), confere no cache da instalação cada tela e página da rodada, depois abre cada tela sem
    rede. unpkg.com fora do ar o tempo todo: nenhum pedido a ele. Com "dados" na lista: a página dos Dados do aparelho também abre
    sem rede (CORE do sw.js), com a lista e o ∞, depois das telas."""
    prob = []
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script(SESSAO)
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
