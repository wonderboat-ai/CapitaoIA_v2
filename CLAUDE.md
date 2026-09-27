# Capitão IA — guia para o Claude

Cérebro operacional da embarcação **Capitão IA** (fabricante/modelo e registro SEM DADOS · proprietário Lucas Araújo · base Balneário Camboriú (SC) · fuso America/Sao_Paulo).
**Hoje é uma DEMONSTRAÇÃO da plataforma** para mostrar a clientes e servir de modelo para as próximas embarcações: clone da arquitetura, da taxonomia da interface e do padrão de integrações do Avanti Vessel AI 1.4.6, com **dados fictícios rotulados DEMO**.
Repositório `wonderboat-ai/CapitaoIA_v2` (público). Site: GitHub Pages da `main`, raiz → **https://v2.capitaoia.com.br/** (arquivo `CNAME`; DNS no Registro.br: CNAME `v2` → `wonderboat-ai.github.io`; o endereço antigo wonderboat-ai.github.io/CapitaoIA_v2/ redireciona). A raiz capitaoia.com.br é o site de apresentação feito no Lovable — não mexer. Domínio verificado no GitHub (TXT `_github-pages-challenge-wonderboat-ai` — manter) e HTTPS obrigatório; o Custom domain do repositório tem de continuar `v2.capitaoia.com.br`.
Crédito no rodapé: **Wonder BOAT | WonderHUB.AI** (grafia do manual da marca).

## Como falar com o usuário
- Português do Brasil, direto; primeira linha = a resposta; nunca perguntar o óbvio; citar fabricante e modelo. Abertura: "Capitão IA online. Que precisa?"
- **Nada inventado:** todo número, data, peça ou procedimento vem de uma fonte e aparece com ela (e a hora, se for leitura). Sem fonte → SEM DADOS; sensor ausente → SEM LEITURA; manual existe e passo a passo não confirmado → MANUAL NO DRIVE; foto/nota → A CONFERIR / A CONFIRMAR. Divergência: manual oficial › registro oficial › laudo › diário › foto › nota informal. A IA na nuvem pode usar conhecimento geral de náutica **rotulado** ("conhecimento geral — confirmar no manual do fabricante"), nunca como dado do barco (1.0.5, depois que o proprietário achou a IA "burra"; volta atrás com uma linha no `SISTEMA` dos Workers).
- Emergência acima de tudo: SOS em todas as telas, offline, sem login; emergência roteada primeiro; resposta e voz completas.
- Registro só cresce: diário e Executado criam linha nova; o chat só grava com comando explícito ("registre no diário…").
- Merge na `main` só quando o proprietário pedir (publica o site). Trabalhar em branch `claude/…`, commits pequenos. Commits com o e-mail noreply do GitHub.
- Não copiar dados da Avanti Vessel (nomes, registro, MMSI, indicativo, hashes, IDs do Drive, NotebookLM, leituras, valores). Só o motor e a estrutura.

## Estrutura
- `*.dc.html` — telas no formato "design canvas" (HTML com `{{…}}`, `<sc-if>`, `<sc-for>`, `<x-import component-from-global-scope="…">` e `<script type="text/x-dc">` com `class Component extends DCLogic`), montadas pelo `support.js` (runtime gerado, React 18.3.1 do unpkg — **não editar**). Web 1440×900, app 390×844.
  **Nunca `{{…}}` em atributo geométrico de SVG** (o navegador lê o modelo cru antes do runtime e loga erro): ícone dinâmico = elemento React (helper `ico()` nas telas).
- `capitao-dados.js` — **todos os dados da embarcação** (`window.CapitaoDados`), GERADO por `ferramentas/demo/gerar_demo.py` (não editar à mão). `null` = SEM DADOS.
- `capitao-brain.js` — `answer(q, ctx)` → `route()` (emergência e óleo no topo) → `ANSWERS` `{ text, src, actions }` → `buscaBase()` (BM25 PT/EN sobre `base-conhecimento.json`) → SEM DADOS; diário, Executado, docs, abastecimento, equipe, atalhos; voz (`ditado`, `speak`, `falavel`, `falaCurta`: 1ª linha; SOS/óleo/EPIRB/Seafire inteiros; resposta da IA: 1ª frase + a seguinte, se curta). IA na nuvem: `pedeIA(a, q)` (SEM DADOS, `base` ou pergunta sobre o app — nunca emergência, óleo, registro, resposta pronta ou só "oi"), `ficha()` (o que o app sabe, bloco a bloco com a fonte, **sem coordenadas**, ~9 mil letras), `vozPensando()` (núcleo em PROCESSANDO até a fala).
- `capitao-auth.js` — porta de entrada: PBKDF2-SHA-256 (210.000 iterações, sal por usuário), sessão 12 h / 30 dias, trava após 5 erros, `VERSAO`, rodapé (versão · DEMO · usuário/Sair · crédito · Guia), saudação sorteada, período. **S1/S2 (SOS) abrem sem login.**
- `capitao-theme.js` (escuro = fallback de cada `var(--cap-*)`, claro = variáveis no `:root`; paleta WonderHUB.AI), `capitao-app.js` (ajuste da prancheta, SW, SOS flutuante, web→app), `capitao-moldura.js` (cabeçalho, trilho de 9 seções, faixa de leitura, SOS web; topo e SOS do app), `capitao-voz.js` (núcleo ESCUTA/PROCESSANDO/RESPOSTA), `capitao-clima.js` (hora, máx/mín ECMWF, maré — Open-Meteo na posição de referência), `capitao-barra.js` (barra do assistente do app), `capitao-telemetria.js` (ao vivo via proxy, **desligado**: `URL_PROXY = ''`).
- `base-conhecimento.json` — trechos dos guias de bordo DEMO (fonte + seção).
- `capitao-ia.js` — cliente da IA na nuvem, **ligado** (Main e H2): cópia de `integracoes/ia-cliente/capitao-ia.js` com a URL do Worker (o teste confere que só a URL muda). Só age em aparelho ativado: depois do login, `#ia=ativar` (ou o botão **Ativar IA na nuvem** do chat, via hashchange) abre uma caixa para colar a `CHAVE_APP` (a chave nunca passa pelo endereço). `perguntar(q, hits, contexto, { ficha, historico })`; `estado()`/`aviso()`/`falha()` dão o motivo quando a IA não entra (a tela põe na linha da fonte). Nas telas, a resposta espera a IA e entra logo depois da pergunta dela (chat e CONVERSA por voz).
- `integracoes/` — telemetria-worker (desligado), workers-ai (**IA ligada na demonstração**), claude-api (IA paga, estrutura), ia-cliente (modelo do cliente), elevenlabs, cloudflare, google-*, github, `integracoes.json`.
- `ferramentas/` — `demo/gerar_demo.py` (dados), `gerar-senha.html` (sal + hash no navegador).
- `testes/` — `cerebro.py` (roteamento, fonte, registro, `pedeIA`, ficha), `verificar.py` (matriz de telas e offline), `worker_ia.py` (proxies da IA + clientes, com env.AI e SDK simulados) e `chat_ia.py` (IA nas telas de chat e na CONVERSA por voz, com Worker, microfone e fala simulados — não gasta cota).
- `Manual-Capitao-IA.dc.html` + `deck-stage.js` (apresentação), `guia-rapido/` + `Guia-Rapido-Capitao-IA.pdf` (A4, Playwright).

## Lançar versão
`VERSAO` em `capitao-auth.js`, `CACHE` em `sw.js` (`capitao-site-v<versão>`) e a tabela de versões do `README.md` — os três iguais. Tela ou arquivo novo usado offline → `TELAS`/`CORE` do `sw.js` e a lista do `index.html`. Mudou dado → regerar (`python ferramentas/demo/gerar_demo.py`), atualizar Manual e Guia e regerar o PDF (`python ferramentas/guia/gerar_guia.py`).

## Dados atuais (DEMO · fictícios)
- Fonte única: `ferramentas/demo/gerar_demo.py` → `capitao-dados.js`, `base-conhecimento.json` e os arquivos enviados ao **Google Drive › Capitão IA v2** (pasta privada criada em 26/09/2026: 01 Manuais e guias de bordo · 02 Documentos · 03 Agenda de manutenção · 04 Diário de bordo · 05 Telemetria — coletor NMEA · 06 Abastecimento · 07 Protocolos de emergência · LEIA-ME). **IDs do Drive não entram no repositório** (ficam num arquivo privado do proprietário, fora do repo).
- Snapshot do coletor (DEMO): 26/09/2026 10:12 · fundeado na enseada de Balneário Camboriú · motores desligados desde 09:31 (última leitura ligados: 700/690 rpm, óleo 3,4/3,3 bar) · gerador ligado (1.236,4 h) · Seakeeper ligado · diesel 54/52 % ≈ 848 L de 1.600 · porão e âncora SEM LEITURA.
- Agenda (DEMO): 11 tarefas, 3 atrasadas em 26/09 (bombas de porão, filtro de água salgada da climatização, rotor do gerador). Prazos contados a partir de 26/09/2026.
- Posição de referência (clima/maré): centro de Balneário Camboriú (Open-Meteo Geocoding, GeoNames 3471039) — fonte real, não inventada.
- MMSI 710123456 **fictício** (informado pelo proprietário para a demonstração). Indicativo SEM DADOS.
- SEM DADOS por decisão do proprietário: fabricante/modelo e registro do barco, modelos dos equipamentos, Seafire e EPIRB (procedimento, localização, validade).
- Procedimentos de emergência (MAYDAY/PAN-PAN, homem ao mar): **procedimento padrão — confirmar com o protocolo de bordo** (decisão do proprietário em 26/09/2026).
- Para a próxima embarcação: trocar os dados do gerador pelos reais (com a fonte de cada um), rodar o gerador, trocar o rótulo DEMO (`demo: False`), revisar `USUARIOS` no `capitao-auth.js`, lançar versão.

## Privacidade (repositório e site são públicos)
- Nunca publicar: contratos, notas fiscais, título de propriedade, CPF/CNPJ, telefones, e-mails, valores, nomes de terceiros, chaves, IDs do Drive, link público de arquivo com a posição do barco.
- Documentos sensíveis, IA sobre eles e telemetria ao vivo: só depois de login no servidor (repositório privado ou Cloudflare Access).
- Senhas combinadas fora do repositório; no código só sal + hash. A senha inicial do Lucas está num arquivo privado do proprietário, fora do repositório; trocar com `ferramentas/gerar-senha.html`.
- Fotos, vídeos e PDFs enviados no app não saem do aparelho: viram linha A CONFERIR / A CONFIRMAR.

## Pendências conhecidas
- Posição de referência exata da marina (lat, lon) — hoje centro da cidade.
- Ícones do app provisórios (logo Wonder BOAT sobre #050816): o manual pede versão específica validada para avatar/favicon.
- Dados reais da embarcação (modelos, registro, EPIRB, Seafire, protocolo de bordo, manuais dos fabricantes, coletor NMEA) — hoje SEM DADOS ou DEMO.
- **IA na nuvem LIGADA na demonstração (1.0.4, 27/09/2026) — exceção aprovada pelo proprietário** à regra "IA só depois de login no servidor", porque os dados são fictícios e o app já tem origem própria. Worker `https://capitao-ia.luka-araujos.workers.dev` (conta Cloudflare do proprietário; Workers AI · Llama 3.3 70B; `GATEWAY=capitao-ia`, 30 pedidos/hora desde a 1.0.5 (3 na 1.0.4); logs de invocação desligados porque gravavam o `X-Capitao-Chave`). `CHAVE_APP` num arquivo PRIVADO fora do repositório. **Antes de dados reais: Cloudflare Access.** 1.0.5: a IA conversa (SEM DADOS, trecho do guia e pergunta sobre o app, no chat e na voz, com ficha de bordo e histórico); **conhecimento geral de náutica vale, rotulado**; dado do barco continua só das fontes. Código do Worker colado no painel da Cloudflare (esta máquina não tem Node): o editor do painel fica num iframe de outra origem, só aceita o teclado com a janela do Chrome visível; a API do painel barra o envio (WAF) — não contornar.
- Telemetria ao vivo, voz em nuvem e documentos sensíveis: estrutura pronta e desligada; ligar junto com o login no servidor (ordem em `integracoes/README.md`).
- **Origem:** o app tem origem própria (v2.capitaoia.com.br) desde a 1.0.3; `wonderboat-ai.github.io` (dividido com os 11 sites da conta) fica fora de `ORIGENS`. Antes de ligar qualquer proxy, falta o Cloudflare Access.
- Modo navegação e alerta crítico: modelos sem disparo automático (dependem da telemetria ao vivo).
- NotebookLM não configurado (`BASE = null`).
- Cópias no Drive feitas em 26/09/2026: o "Guia de bordo (DEMO) — Estabilizador Seakeeper" ainda diz "MANUAL NO DRIVE" no §6 Alarmes (o repositório já diz SEM DADOS: manual do fabricante não carregado). Corrigir à mão no Drive ou reenviar a partir de `ferramentas/demo/fontes/`.

## Testes locais
- Servir a raiz: `python -m http.server 8765 --bind 127.0.0.1`.
- Cérebro: `python -X utf8 testes/cerebro.py` (`-v` mostra as respostas).
- Proxy da IA (Workers AI) e cliente: `python -X utf8 testes/worker_ia.py` (env.AI simulado; não precisa de conta nem de Node).
- IA nas telas de chat: `python -X utf8 testes/chat_ia.py` (Worker simulado com `page.route`; **não** chama o Worker real, que gasta a cota: 30/hora e ~50 a 60 perguntas por dia).
- Telas: `python -X utf8 testes/verificar.py [Telas…] [--fotos] [--offline]` — cada tela em escuro e claro, web 1440×900 · 1280×720 · 1920×1080 · 1024×768 e app 390×844 · 360×640 · 430×932 · 844×390 (celular com toque); confere erro de script/console, rolagem lateral, imagem/ícone deformado e prancheta; `--offline` testa a abertura sem rede depois da 1ª visita (inclui o SOS).
- Navegador: Edge instalado (Playwright `channel="msedge"`); sessão injetada em `localStorage` `capitao.sessao.v1 = { u: 'lucas', em, exp }`.
