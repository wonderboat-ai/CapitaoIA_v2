# Documentação pendente (Fase 8)

Linhas de documentação que ficaram desatualizadas com o port da Fase 0b, relatadas pelos implementadores e revisores.
Não foram editadas na Fase 0b (regra da fase): entram na Fase 8, junto com a versão 1.1.0. Os números de linha são do momento
do relato; confira com grep antes de editar.

## F01 React do próprio site

- CLAUDE.md:18: 'montadas pelo support.js (runtime gerado, React 18.3.1 do unpkg — não editar)'. Passa a ser: React 18.3.1 do próprio site (assets/vendor/react-18.3.1, cópia do npm com o mesmo SRI). O support.js é o do Avanti 1.24.0 (decisão h) e continua sem edição à mão
- CLAUDE.md:24 (sw.js): 'SOS e React da CDN (versão fixa) saem da cópia guardada'. Passa a ser: 'SOS e React (assets/vendor, versão fixa no caminho) saem da cópia guardada; o React está no CORE (tudo ou nada); nada de fora passa pelo cache'
- CLAUDE.md:66 e :68 (Testes locais): o publicacao.py ganhou o 4b (React lento sai da cópia guardada) e 'nenhum pedido ao unpkg' a partir da B; o verificar.py ganhou o teste sem unpkg (Main, H2, S2) e a contagem de pedidos ao unpkg no --offline
- README.md:85: 'Internet na primeira visita (React vem do unpkg)'. Passa a ser: o React vem do próprio site
- README.md:102 (Estrutura): falta a linha assets/vendor/ (React 18.3.1, cópia do npm, licença MIT)
- integracoes/integracoes.json:13-15: o item 'cdn-react' ('unpkg (React 18.3.1)', onde 'sw.js › CDN', notas sobre a 1ª visita) ficou desatualizado. O React não é mais integração externa: tirar o item ou trocar por 'React 18.3.1 em assets/vendor (próprio site)'. Deixei para a Fase 8 porque o PROMPT põe o integracoes.json na atualização de docs
- CLAUDE.md:18 (Estrutura, *.dc.html): 'runtime gerado, React 18.3.1 do unpkg' → o React agora vem de assets/vendor/react-18.3.1/ (cópia npm, mesmo SRI); o Babel continua no unpkg e nunca é carregado.
- CLAUDE.md, linha do sw.js: 'SOS e React da CDN (versão fixa) saem da cópia guardada' → o React de assets/vendor está no CORE (tudo ou nada) e sai da cópia guardada primeiro; o SW não guarda mais nada de fora do site.
- CLAUDE.md:66 (Testes locais, publicacao.py): falta o 4b (React lento sai da cópia guardada), o 'nenhum pedido ao unpkg' e a conferência nova do 2b (a versão nova ativa já com o React no cache, CORE).
- CLAUDE.md:68 (Testes locais, verificar.py): no --offline, falta 'a instalação já guarda o React (CORE)' e 'nenhum pedido ao unpkg'. Falta também o teste sem unpkg (Main, H2-Home-Mobile, S2-SOS-Mobile montam com o unpkg abortado).
- README.md:85: 'Internet na primeira visita (React vem do unpkg)' → o React vem do próprio site; continua precisando de internet na 1ª visita, mas não do unpkg.
- CLAUDE.md:18 — 'support.js (runtime gerado, React 18.3.1 do unpkg — não editar)' → React 18.3.1 de assets/vendor/react-18.3.1/ (cópia do pacote npm, mesmo SRI, LICENSE.txt MIT); support.js = o do Avanti 1.24.0 + a reserva do Capitão no loadReactUmd (unpkg com o mesmo SRI, só se a cópia local falhar — troca a partir da 1.0.x); registrar essa exceção ao 'não editar' e que uma troca inteira futura tem de repor a reserva
- CLAUDE.md:18/24 (Estrutura) — falta a pasta nova assets/vendor/react-18.3.1/ (react.production.min.js, react-dom.production.min.js, LICENSE.txt) e que ela está no CORE do sw.js
- CLAUDE.md:24 — 'SOS e React da CDN (versão fixa) saem da cópia guardada' → o React está no CORE (instalação tudo ou nada) e assets/vendor sai da cópia guardada primeiro (exceção ao 'arquivo do site sempre confere com o servidor', que a mesma linha afirma); sem lista CDN; o unpkg (reserva) vai direto para a rede
- CLAUDE.md:66 (publicacao.py) — acrescentar: 2b) a versão nova ativa já com o React no cache; 4b) React lento (assets/vendor) sai da cópia guardada em < 4 s; da árvore em diante unpkg cortado e nenhum pedido a ele; 5) troca de versão com a conexão caindo logo depois do support.js novo → SOS abre offline (pulado se a publicada tem o mesmo support.js)
- CLAUDE.md:68 (verificar.py) — acrescentar: teste 'sem unpkg' (Main, H2-Home-Mobile, S2-SOS-Mobile montam sem pedido ao unpkg), 'reserva do React' (S2 monta com assets/vendor fora) e, no --offline, a conferência do React no cache logo depois da instalação e nenhum pedido ao unpkg
- integracoes/integracoes.json:13-15 — entrada 'cdn-react' / 'unpkg (React 18.3.1)' / onde 'sw.js › CDN' (a constante CDN não existe mais) → 'React 18.3.1 (assets/vendor, cópia do npm)', onde ['support.js', 'sw.js › CORE'], notas: unpkg só como reserva da troca a partir da 1.0.x; 'app' do cabeçalho ainda diz 1.0.4
- ferramentas/prompts/clone-avanti-1.1.0/MAPA.md:29 — 'O React do unpkg sai da cópia guardada' → React no CORE (assets/vendor)
- ferramentas/prompts/clone-avanti-1.1.0/MAPA.md:88 — 'Só a mesma origem e o unpkg ficam em cache (linhas 104-105)' → só a mesma origem fica em cache (o unpkg nem passa pelo cache do SW)
- ferramentas/prompts/clone-avanti-1.1.0/MAPA.md:726 (evidência) — 'sw.js:24-27 (CDN) guarda só esses dois React' / 'sw.js:104-105 só põe em cache a mesma origem e o unpkg.com' ficaram desatualizados

## F19 conversa sem pausa

- README.md, tabela de versões (linha da 1.1.0, Fase 8): 'conversa por voz sem a pausa de 0,65 s: a pergunta ouvida sai na hora; texto, VOZ→TEXTO e atalhos mantêm a pausa'
- README.md:46 (item 'Conversa por voz'): pode dizer que a pergunta falada sai na hora, sem a pausa do chat
- CLAUDE.md, linha de testes/: a descrição do chat_ia.py ('IA nas telas de chat e na CONVERSA por voz — rosto, som e voz a 1,15x —…') ganha 'CONVERSA sem a pausa de 0,65 s (< 200 ms do fim do ditado ao cérebro), VOZ→TEXTO com a pausa'
- CLAUDE.md, linha do capitao-ia.js ('Nas telas, a resposta espera a IA e entra logo depois da pergunta dela (chat e CONVERSA por voz)'): pode acrescentar que na CONVERSA a pergunta sai sem a pausa de 0,65 s
- Manual-Capitao-IA.dc.html, slide '08 Conversa por voz' (texto e speaker notes), e guia-rapido/Guia-Rapido-Capitao-IA.html, cartão 'Na conversa' (+ PDF regerado): opcional na Fase 8, uma linha 'a pergunta falada sai na hora'

## F13 vento e rajada

- CLAUDE.md, seção Estrutura: a descrição do `capitao-clima.js` ('hora, máx/mín ECMWF, maré — Open-Meteo na posição de referência') precisa citar vento e rajada do dia em nós com a direção (ECMWF; rajada do melhor modelo se faltar), o toque no windy.com e as duas linhas no celular
- README.md:47 ('Cabeçalho ao vivo: hora local do barco, máxima/mínima do dia (ECMWF via Open-Meteo) e maré agora…'): falta o vento e a rajada do dia, com a direção
- guia-rapido/Guia-Rapido-Capitao-IA.html:253 (card 'Cabeçalho'): falta o vento e a rajada (≋ NE 12/19 KT). Depois, regerar o PDF (ferramentas/guia/gerar_guia.py)
- guia-rapido/Guia-Rapido-Capitao-IA.html:272 ('Clima e maré mostram "—" até voltar a a rede'): já estava impreciso antes da F13. O app mostra a última leitura salva do dia, com a hora dela, e só mostra '—' sem nenhuma leitura
- integracoes/integracoes.json:18 (notas do open-meteo: 'Máx/mín do dia e maré…'): incluir o vento e a rajada do dia (wind_speed_10m_max, wind_gusts_10m_max e wind_direction_10m_dominant, em nós)
- integracoes/README.md:12 ('Open-Meteo (clima ECMWF, maré, geocoding)'): incluir o vento e a rajada
- Manual-Capitao-IA.dc.html: nenhum slide descreve o cabeçalho de clima hoje. Se a Fase 8 fizer slides das funções novas, entra o vento e a rajada
- CLAUDE.md:23 — '`capitao-clima.js` (hora, máx/mín ECMWF, maré — Open-Meteo na posição de referência)': incluir o vento máximo, a rajada e a direção dominante de hoje em nós (ECMWF via Open-Meteo; a rajada que o ECMWF não trouxer vem do melhor modelo, dito no title); o toque no clima/vento abre o windy.com (nova aba); no celular, duas linhas; sem rede, a leitura salva do dia com a hora dela; sem nenhuma, '—'
- CLAUDE.md:29 — testes/: 'cerebro.py (roteamento, fonte, registro, pedeIA, ficha)' e 'verificar.py (matriz de telas e offline)': incluir o vento do dia (cerebro.py: clima, seguro e ficha com a leitura salva, inclusive com vento forte, sem limite inventado e com o mar SEM DADOS; verificar.py: cabeçalho de Main, H2 e S1 com o Open-Meteo simulado)
- guia-rapido/Guia-Rapido-Capitao-IA.html:253 — card Cabeçalho 'Hora do barco, máxima/mínima de hoje e maré agora… Tocar abre o windy.com': incluir o vento e a rajada de hoje em nós, com a direção (ex.: '≋ NE 12/19 KT'), e as duas linhas no celular
- guia-rapido/Guia-Rapido-Capitao-IA.html:272 — 'Sem internet… Clima e maré mostram "—" até voltar a rede': com a F13, sem rede o cabeçalho mostra a leitura salva do dia com a hora dela; '—' só quando não há leitura do dia
- Guia-Rapido-Capitao-IA.pdf — regerar com python ferramentas/guia/gerar_guia.py depois de corrigir as duas linhas do guia
- integracoes/integracoes.json:18 — item open-meteo, notas 'Máx/mín do dia e maré…': incluir o vento máximo, a rajada (com o melhor modelo quando o ECMWF não trouxer) e a direção dominante de hoje
- CLAUDE.md:21 — capitao-brain.js: falta a previsão do dia (vento/rajada com fonte e hora) no clima, no 'seguro para sair?' (como informação, sem limite de vento) e no bloco 'Clima e maré' da ficha; e a regra de rota: 'rajada' só vai para o clima em pergunta de previsão, depois das rotas de equipamento
- CLAUDE.md:68 — Testes locais › verificar.py: falta a conferência do vento no cabeçalho de Main, H2-Home-Mobile e S1-SOS-Web (Open-Meteo simulado, windy.com, nada cortado, '—' sem leitura do dia) e a da previsão na resposta da B3-Carta-Resposta
- integracoes/integracoes.json:18 — open-meteo › notas: 'Máx/mín do dia e maré…' sem vento, rajada e direção (ECMWF; rajada do melhor modelo quando o ECMWF não traz)

## F03 ícones dos atalhos

- CLAUDE.md §Estrutura, linha do `ferramentas/` ("`demo/gerar_demo.py` (dados), `gerar-senha.html`…"): falta `icones/gerar_atalhos.py` (ícones dos atalhos do app instalado: desenha o SVG e rasteriza no navegador, sem Pillow).
- CLAUDE.md §Testes locais, linha do `verificar.py` ("Telas: … confere erro de script/console…"): falta que toda rodada também confere os ícones dos atalhos do manifest (any + maskable, 200, tamanho do PNG, centro, zona segura de 80 % no maskable).
- CLAUDE.md, cabeçalho de marca ("o ∞ sozinho em espaço pequeno (cabeçalhos, ícone do app, …)"): os atalhos do app instalado não usam o ∞. Eles têm desenho próprio (boia/timão/livro em traço branco sobre #050816, SOS em #d32f27). Vale uma nota.
- CLAUDE.md §Lançar versão: pode ganhar "mudou o desenho dos atalhos → `python ferramentas/icones/gerar_atalhos.py` (o verificar.py confere)".
- README.md:36 ("Segurar o ícone no Android mostra atalhos para SOS, Console e Diário."): os atalhos agora têm ícone próprio (boia, timão e livro).
- README.md:105 ("ferramentas/ … gerador dos dados DEMO, gerador do guia, gerador de senha"): falta o gerador dos ícones dos atalhos.
- README.md, tabela de versões (entrada 1.1.0, Fase 8): incluir "ícones dos atalhos do app instalado".
- CLAUDE.md:28 (Estrutura › `ferramentas/`): hoje diz só `demo/gerar_demo.py` (dados) e `gerar-senha.html` (sal + hash). Falta `icones/gerar_atalhos.py`: ícones dos atalhos do app instalado (SOS boia, Console timão, Diário livro), SVG rasterizado com Playwright, sem Pillow, determinístico, 96 e 192 px, any e maskable.
- CLAUDE.md:29 (Estrutura › `testes/`): `verificar.py (matriz de telas e offline)` não cita a conferência dos ícones dos atalhos do manifest.
- CLAUDE.md:68 (Testes locais › Telas): a lista do que o verificar.py confere precisa de "em toda rodada menos a --so-offline: ícones dos atalhos do manifest (any e maskable, 200, tamanho do PNG lido do IHDR, desenho centrado; no maskable, fundo inteiro e zona segura de 80 %)". Isso soma 3 verificações por rodada (ex.: login/index/Main/H2-Home-Mobile = 55).
- CLAUDE.md:24 (Estrutura › `sw.js`): o trecho "Fora da instalação (`EXTRA` …)" não diz que os 12 assets/atalho-*.png ficam fora do CORE e do EXTRA. O Android os lê do manifest, e eles não precisam abrir offline.
- CLAUDE.md:7 (Marca): "o ∞ sozinho em espaço pequeno (cabeçalhos, ícone do app, tela de abertura, favicon)". Avaliar se vale citar que os atalhos do app instalado têm desenho próprio (boia/timão/livro) sobre o #050816 da marca, sem o ∞.
- README.md:103 (`assets/ · favicon.ico  ∞ e assinatura WonderHUB.AI, ícones e favicon (∞)…`): faltam os ícones dos atalhos do app instalado (atalho-*.png).
- README.md:106 (`testes/  teste do cérebro, matriz de telas, …`): falta a conferência dos ícones dos atalhos do manifest no verificar.py.
- README.md, tabela de Versões: a linha da 1.1.0 (Fase 8) deve citar "ícones dos atalhos do app instalado (paridade Avanti 1.18.1/1.19.1, desenho próprio)".
- guia-rapido/Guia-Rapido-Capitao-IA.html:122: "Segurar o ícone mostra atalhos: SOS, Console, Diário." Ainda está correto; opcional acrescentar "com ícone próprio" junto com o README:36. Se mudar, regerar o PDF.

## F25 Dados do aparelho

- CLAUDE.md › Estrutura: falta a linha do dados.html. Ela baixa uma cópia JSON das chaves capitao.* e deixa de fora a sessão, as tentativas de login, as chaves e as URLs de teste da IA, da telemetria e da voz, a última leitura do coletor, o clima e a maré salvos, a saudação, o replay.fixo e toda chave com segmento sessao/login/chave/senha/token/segredo/url. Ao restaurar, o registro (diário, Executado, documentos, abastecimentos, Equipe) só soma, e as preferências (tema, atalhos, blocos, plataforma) só voltam com a caixa marcada. A página fica atrás do login, tem o SOS no topo e está no CORE do sw.js
- CLAUDE.md › Estrutura, linha do capitao-auth.js: o rodapé agora é '(versão · DEMO · usuário/Sair · crédito · Guia · Dados)'. Guia e Dados aparecem só no Main e na H2
- CLAUDE.md › Estrutura, linha do sw.js: o CORE agora inclui o dados.html
- CLAUDE.md › Testes locais, linha do verificar.py: incluir a página 'dados' com login/index. O teste cobre fundo do tema, SOS à vista no alto e no fim da rolagem, ida e volta da cópia, arquivos ruins, segredo num arquivo montado à mão, redirecionamento ao login sem sessão, abertura offline e o link 'Dados' no rodapé do Main e da H2
- CLAUDE.md › Privacidade: dizer que a cópia dos Dados do aparelho fica com a pessoa, leva os telefones da Equipe e nunca leva sessão nem chaves
- README.md › linha 91 (index.html · login.html): somar o dados.html (cópia e restauração dos dados do aparelho)
- README.md › acessos do topo (linhas 10–19): pôr o caminho dos 'Dados do aparelho' (rodapé › Dados, ou dados.html)
- README.md › tabela de versões: a linha da 1.1.0 (Fase 8) tem de citar a F25
- Manual-Capitao-IA.dc.html e guia-rapido/ + PDF: falta um slide ou página 'Dados do aparelho' (baixar antes de trocar de celular, restaurar só soma). Fica para a Fase 8
- CLAUDE.md:22 — capitao-auth.js: o rodapé é 'versão · DEMO · usuário/Sair · crédito · Guia'; agora tem também 'Dados' (link para dados.html, só no Main e na H2)
- CLAUDE.md, seção Estrutura — falta o dados.html: baixar uma cópia JSON das chaves capitao.* (nunca sessão, tentativas, chaves, endereços de teste, última leitura do coletor, clima/maré, saudação, replay); restaurar só soma, item ilegível fica de fora, o que o diário diz desfeito depois não volta, preferências só com a caixa marcada, outro app/formato/corrompido → nada muda; atrás do login, SOS no topo, abre offline (CORE)
- CLAUDE.md:13 — 'Registro só cresce': acrescentar que restaurar uma cópia (dados.html) também só soma e não desfaz o que uma linha mais nova do diário desfez
- CLAUDE.md, seção Privacidade — a cópia do dados.html fica com a pessoa e leva telefones e contatos de convite da Equipe e as posições gravadas no diário (SOS e resumos de navegação)
- CLAUDE.md:68 — verificar.py: 'e `login`/`index`' agora também `dados` (temas, tamanhos, SOS à vista, ida e volta, item ilegível, desfeito nas telas, linha do SOS e aviso); '--offline' agora também confere no cache da instalação cada tela e página da rodada
- README.md:8-12 — lista de endereços sem 'Dados do aparelho' (dados.html: baixar e restaurar)
- README.md:76 — 'O que você edita fica no navegador … limpar os dados do navegador apaga': acrescentar que a página Dados do aparelho baixa uma cópia e restaura (só soma)
- README.md:91 — 'index.html · login.html  entrada…': falta o dados.html
- Manual-Capitao-IA.dc.html — não menciona a cópia e a restauração dos dados do aparelho (Fase 8)
- guia-rapido/ e Guia-Rapido-Capitao-IA.pdf — não mencionam a cópia e a restauração; regerar o PDF com ferramentas/guia/gerar_guia.py (Fase 8)
- CLAUDE.md:22 (capitao-auth.js): 'rodapé (versão · DEMO · usuário/Sair · crédito · Guia)' não traz o link 'Dados' (dados.html) que o rodapé do Main e da H2 ganhou ao lado do 'Guia'.
- CLAUDE.md:29 (Estrutura › testes/): o verificar.py aparece só como '(matriz de telas e offline)'. Falta dizer que cobre o dados.html: matriz, teste_dados de ida e volta com diário, documentos, abastecimentos, Executado e Equipe, ordem pela hora, desfeito, segredos e arquivos ruins, e offline com conferência do cache da instalação.
- CLAUDE.md:68 (Testes locais › Telas): cita só 'login'/'index' entre as páginas fora das TELAS. Falta o 'dados' (temas, 8 tamanhos, SOS à vista no topo e no fim, teste_dados, '--offline' com 'dados' na lista e cada tela e página da rodada no cache da instalação).
- CLAUDE.md, seção Estrutura: falta uma linha para o dados.html. Ela deve dizer: só as chaves capitao.* vão no arquivo; a lista FORA nunca vai (sessão, tentativas, chaves e URLs de IA/telemetria/voz, última leitura do coletor, clima e maré salvos, saudação, replay fixo) e a regex de segredo também fica de fora; restaurar só soma (registro: diário, Executado, documentos, abastecimentos, Equipe), com a linha nova pela hora e mais nova primeiro (iso no diário, dd/mm/aaaa em documentos e abastecimentos); item ilegível fica de fora; preferências só voltam com a caixa marcada; outro app, formato novo ou arquivo corrompido não muda nada; a regra de desfeito depende dos textos que C1/C2/G4 gravam no diário; o SOS fica no topo (S1/S2).
- README.md:91 (Estrutura): a linha 'index.html · login.html  entrada (detecta o aparelho) e login' não traz o dados.html (baixar e restaurar os dados do aparelho).
- README.md:19 (Acesso: 'Sair: no rodapé…') e README.md:38-49 ('O que dá para fazer', especialmente a :49 'Personalização por aparelho'): não há Dados do aparelho (baixar uma cópia JSON e restaurar sem apagar nada; o arquivo fica com a pessoa e leva telefones da Equipe, contatos de convite e posições gravadas no diário).
- Manual-Capitao-IA.dc.html:75 (Sair no rodapé) e guia-rapido/Guia-Rapido-Capitao-IA.html:124 (card 'Sair e segurança'): não falam do link Dados no rodapé nem da cópia e da restauração. O PDF Guia-Rapido-Capitao-IA.pdf terá de ser regerado (python ferramentas/guia/gerar_guia.py).

## Fora das funções

- MAPA.md: as evidências sobre o CDN do `sw.js` (linhas 29, 88 e 726) e o "React do unpkg" ficaram históricas: o MAPA é da 1.0.9 e não se reescreve.
