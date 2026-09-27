# Capitão IA

Cérebro operacional da embarcação **Capitão IA**: chat com o barco, console de telemetria e manutenção, FAQ de bordo e SOS. Tem versão **web** (computador e tablet) e versão **app** (celular), com um cérebro só.

> **Versão 1.0.0 · 27/09/2026** · Wonder BOAT | WonderHUB.AI

> **Demonstração da plataforma.** Esta embarcação é de demonstração: leituras, agenda, documentos, diário, abastecimentos e guias de bordo são **fictícios** e aparecem com o selo **DEMO** e a fonte de cada dado (Google Drive › Capitão IA v2). Modelos dos equipamentos, registro, Seafire e EPIRB estão **SEM DADOS**; o MMSI 710123456 é fictício. Procedimentos de emergência são o **padrão internacional, a confirmar com o protocolo de bordo**. Nada é inventado pelo assistente: quando falta o dado, a tela mostra **SEM DADOS**.

- **Abrir:** https://wonderboat-ai.github.io/CapitaoIA_v2/ (quando publicado)
- **Todas as telas:** `index.html?v=lista`
- **Manual de uso:** `Manual-Capitao-IA.dc.html`
- **Guia rápido (PDF, para quem nunca usou):** `Guia-Rapido-Capitao-IA.pdf`

## Acesso

Toda tela pede login, **menos o SOS** (numa emergência ninguém pode ficar preso na senha). Usuário: **Lucas** (Lucas Araújo · proprietário). A senha é combinada fora deste repositório.

- **Manter conectado:** o acesso vale 30 dias no aparelho; sem essa opção, 12 horas. Vale para todas as abas; ao vencer com uma tela aberta, ela volta para o login.
- **Sair:** no rodapé de qualquer tela; encerra em todas as abas.
- Depois de 5 senhas erradas, o login trava por 30 s (o tempo dobra a cada erro, até 15 min). Erros de mais de 1 hora não contam.
- **Trocar a senha / criar usuário:** `ferramentas/gerar-senha.html` gera sal e hash no próprio navegador; cole a linha em `USUARIOS` no `capitao-auth.js` e lance uma versão.

> **Limite:** é uma porta de entrada, não proteção real. O site é estático e o repositório é público: quem abrir os arquivos no GitHub vê o conteúdo. A senha é guardada só como hash (PBKDF2-SHA-256, 210.000 iterações). Para proteger de verdade: repositório privado e login no servidor (ex.: Cloudflare Access) — ver `integracoes/`.

## Como abrir

| Endereço | O que abre |
|---|---|
| `/` | Pede login e detecta o aparelho: celular abre o app, computador ou tablet abre a web |
| `/?v=app` · `/?v=web` | Sempre o app / sempre a web neste aparelho |
| `/?v=auto` | Volta a detectar o aparelho |
| `/?v=lista` | Lista de todas as telas |
| `H2-Home-Mobile.dc.html#q=<pergunta>` | O início responde na hora (link não grava no diário) |
| `#mode=voz\|conversa\|foto\|video\|texto` | Abre o modo (o microfone só liga com o seu toque) |

**Instalar no celular:** iPhone (Safari) › Compartilhar › Adicionar à Tela de Início · Android (Chrome) › menu ⋮ › Instalar app. Segurar o ícone no Android mostra atalhos para SOS, Console e Diário.

## O que dá para fazer

- **Chat com o barco:** texto, voz→texto, conversa por voz, foto ou vídeo. Cada resposta traz a **fonte**; sem fonte, **SEM DADOS**. Foto e vídeo não saem do aparelho: viram linha A CONFERIR no diário.
- **Atalhos:** perguntas prontas com um toque — 6 padrão, banco de 12, até 8 na tela, editáveis.
- **Console:** telemetria (snapshot com hora), gestão, manutenção com **Executado** (linha nova no diário), documentos, abastecimento, diário de bordo (só cresce) e equipe (convites PENDENTE, telefones só no aparelho).
- **FAQ de bordo:** passo a passo por equipamento — gerador Onan, estabilizador Seakeeper, climatização, eletrônicos Garmin / áudio Fusion / VHF 315 — tirado dos guias de bordo DEMO.
- **SOS:** canal 16 com roteiro MAYDAY, homem ao mar, incêndio (Seafire: SEM DADOS) e EPIRB (SEM DADOS). Em todas as telas, abre offline e sem login.
- **Conversa por voz:** núcleo de IA em tela cheia — ESCUTA (ciano) · PROCESSANDO (violeta) · RESPOSTA (azul). A voz fala só a 1ª linha; emergências são lidas inteiras. Abertura: "Capitão IA online. Que precisa?"
- **Cabeçalho ao vivo:** hora local do barco, máxima/mínima do dia (ECMWF via Open-Meteo) e maré agora (modelo Open-Meteo Marine — não é a tábua da Marinha), na posição de referência de Balneário Camboriú.
- **Tema claro/escuro** (sol/lua ao lado do avatar). O SOS do app e o alerta crítico ficam sempre escuros.
- **Personalização por aparelho:** atalhos, blocos do console (8), diário, tarefas executadas, documentos, equipe e tema. Fixos: SOS, os 5 botões do início e a barra do assistente.

## Telas

Todos os arquivos terminam em `.dc.html`.

| Web (1440 × 900) | App (390 × 844) |
|---|---|
| `Main` · Início | `H2-Home-Mobile` · Início |
| `A1-Ponte-Web` · Telemetria | `A2-Ponte-Mobile` · Console · `A3-Ponte-Editar` · editar blocos |
| `B1-Carta-Web` · Gestão | `B2-Carta-Mobile` · Sistemas · `B3-Carta-Resposta` · resposta por voz |
| `C1-Leme-Web` · Manutenção | `C2-Leme-Mobile` · Manutenção · `C3-Leme-Alerta` · modelo de alerta crítico |
| `G1-Documentos-Web` | `G1-Documentos-Mobile` |
| `G2-Abastecimento-Web` | `G2-Abastecimento-Mobile` |
| `G3-Diario-Web` | `G3-Diario-Mobile` |
| `G4-Equipe-Web` | `G4-Equipe-Mobile` |
| `F1-FAQ-Hub-Web` e `F2`–`F5` `-Web` | `F1-FAQ-Hub` e `F2`–`F5` (Estabilizador · Eletrônicos · Gerador · Climatização) |
| `H3-Atalhos-Editar-Web` | `H3-Atalhos-Editar` |
| `S1-SOS-Web` | `S2-SOS-Mobile` |
| — | `E1-Navegando-Gatilhos` · `E2-Navegando-Sintoma` · modo navegação |

E ainda: `Manual-Capitao-IA` (apresentação de uso) e o `Guia-Rapido-Capitao-IA.pdf` (A4, gerado de `guia-rapido/`).

## Dados e privacidade

- **Uma fonte só:** `capitao-dados.js` (gerado por `ferramentas/demo/gerar_demo.py`) — snapshot com data e hora, agenda, documentos, diário, abastecimentos, equipe, FAQ e protocolos. `base-conhecimento.json` traz os trechos dos guias de bordo (fonte e seção), para a busca do chat e da voz, offline.
- **O site é público.** Nada de contratos, notas fiscais, título de propriedade, CPF/CNPJ, telefones, e-mails, valores, nomes de terceiros, chaves ou IDs do Drive — nem na demonstração.
- **O que você edita fica no navegador** (localStorage): atalhos, blocos, diário, executadas, documentos e NFs enviados, equipe e tema. Não sincroniza entre aparelhos; limpar os dados do navegador apaga.
- **Motor desligado** mostra a última leitura com motor ligado e a hora, nunca zero. **Telemetria ao vivo desligada:** o app mostra "SNAPSHOT DEMO" com a hora, nunca "ao vivo".

## Integrações

Tudo que precisa de chave passa por um Cloudflare Worker (`ORIGENS` + `CHAVE_APP` no cabeçalho `X-Capitao-Chave` + freio por IP) e **vem desligado** (`URL_PROXY = ''`), caindo no dado local em erro, demora ou sem internet: telemetria ao vivo (`capitao-telemetria`), IA na nuvem com a Claude API (`capitao-ia`) e voz em nuvem opcional (`capitao-voz`). Detalhes, status e ordem para ligar: [`integracoes/`](integracoes/README.md).

## Requisitos

- **Internet na primeira visita** (React vem do unpkg). Depois, todas as telas abrem sem internet — inclusive o SOS.
- **Voz:** Chrome, Edge ou Safari, com permissão de microfone. O Firefox não reconhece voz. Melhor voz grátis no computador: Microsoft Edge.

## Estrutura

```
index.html · login.html         entrada (detecta o aparelho) e login
*.dc.html                       telas web e app (support.js monta as pranchetas)
capitao-dados.js                dados da embarcação (gerado — não editar à mão)
capitao-auth.js                 login, versão, rodapé, saudação e período
capitao-brain.js                cérebro: respostas, roteamento, base, diário, atalhos e voz
capitao-theme.js · capitao-app.js · capitao-moldura.js · capitao-voz.js · capitao-clima.js · capitao-barra.js · capitao-telemetria.js
base-conhecimento.json          trechos dos guias de bordo
Manual-Capitao-IA.dc.html · deck-stage.js     apresentação de uso
Guia-Rapido-Capitao-IA.pdf · guia-rapido/     guia rápido A4
manifest.webmanifest · sw.js · .nojekyll      app instalável e cache offline
assets/                         logo Wonder BOAT e ícones
integracoes/                    estrutura desligada das integrações
ferramentas/                    gerador dos dados DEMO, gerador do guia, gerador de senha
testes/                         teste do cérebro e matriz de telas
CLAUDE.md                       guia do projeto para o Claude
```

## Versões

A versão aparece no rodapé de todas as telas. Para lançar: `VERSAO` em `capitao-auth.js`, `CACHE` em `sw.js` e esta tabela — os três iguais.

| Versão | Data | O que mudou |
|---|---|---|
| 1.0.0 | 27/09/2026 | Primeira versão: clone do motor do Avanti Vessel AI 1.4.6 para a embarcação de demonstração Capitão IA (dados fictícios rotulados DEMO, fonte no Google Drive › Capitão IA v2) · 35 telas (15 web · 20 app) e o Manual · chat com fonte em toda resposta e SEM DADOS sem fonte · SOS offline e sem login · marca Wonder BOAT com a paleta WonderHUB.AI · integrações como estrutura desligada · Manual e Guia rápido |

## Publicar e atualizar

1. Merge da branch `claude/capitao-ia-v2` na `main` — **só quando o proprietário pedir** (publica o site).
2. GitHub › Settings › Pages › Deploy from a branch › `main` · `/ (root)` › Save.
3. A nova versão entra no ar em 1 a 2 minutos. No celular, fechar e abrir o app.

---

Embarcação Capitão IA · registro SEM DADOS · demonstração · Wonder BOAT | WonderHUB.AI
