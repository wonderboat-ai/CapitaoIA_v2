# Capitão IA

Cérebro operacional da embarcação **Capitão IA**: chat com o barco, console de telemetria e manutenção, FAQ de bordo e SOS. Tem versão **web** (computador e tablet) e versão **app** (celular), com um cérebro só.

> **Versão 1.1.0 · 14/11/2026** · Design by Wonder BOAT | WonderHUB.AI

> **Paridade com o Avanti Vessel AI 1.24.0** (motor, estrutura, telas e integrações; nenhum dado dele). A embarcação navega num laço de 150 s com âncora às 07:00 (America/Sao_Paulo) e posição contínua pela rota; **tudo o que o app mostra, fala e manda à IA lê o mesmo instante**. Toda resposta de bordo traz número e hora, sem selo e sem rótulo de demonstração. **Tempo e maré são sempre reais.** O **SOS** nunca usa a navegação: a posição é o GPS do aparelho ou "leia no plotter". Procedimentos de emergência são o **padrão internacional, a confirmar com o protocolo de bordo**.

- **Abrir:** https://v2.capitaoia.com.br/ (o endereço antigo `wonderboat-ai.github.io/CapitaoIA_v2/` redireciona)
- **Todas as telas:** `index.html?v=lista`
- **Dados do aparelho** (baixar uma cópia e restaurar): `dados.html`, ou **Dados** no rodapé do Início
- **Relatório A4** (agenda, histórico, documentos, abastecimentos e peças, para imprimir ou salvar em PDF): `relatorio.html`
- **Manual de uso:** `Manual-Capitao-IA.dc.html`
- **Guia rápido (PDF, para quem nunca usou):** `Guia-Rapido-Capitao-IA.pdf`

## Acesso

Toda tela pede login, **menos o SOS** (numa emergência ninguém pode ficar preso na senha; o login também tem o botão de SOS). Usuários: **Lucas** (Lucas Araújo · proprietário) e **Convidado** (chave `demo`, para mostrar o app a clientes; fora da lista da embarcação). As senhas são combinadas fora deste repositório.

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
| `#replay=<segundo>` | Congela o laço de 150 s num segundo (testes e capturas) |

**Instalar no celular:** iPhone (Safari) › Compartilhar › Adicionar à Tela de Início · Android (Chrome) › menu ⋮ › Instalar app. Segurar o ícone no Android mostra atalhos para SOS, Console e Diário, cada um com ícone próprio (boia, timão e livro).

## O que dá para fazer

- **Chat com o barco:** texto, voz→texto, conversa por voz, foto ou vídeo. Cada resposta traz número, hora e **fonte**. Foto e vídeo não saem do aparelho: viram linha A CONFERIR no diário. O chat responde onde estamos, rumo, profundidade, chegada prevista e distância, alarmes ativos, temperatura do motor e da água, estado do mar, pessoas a bordo, dimensões e onde ler o MMSI do rádio (etiqueta ou Licença de Estação), e **só grava no diário com comando explícito** ou com o toque em CONFIRMAR numa proposta (o registro só cresce: corrigir e anular são linhas novas). Pergunta de emergência (ou pessoa em perigo) abre sempre com a instrução de segurança, no aparelho; por 15 minutos a conversa não devolve posição, rumo, velocidade, chegada nem pessoas a bordo.
- **IA na nuvem:** nos aparelhos ativados, a IA (Llama 3.3 70B no Cloudflare Workers AI, grátis) **conversa**: responde quando o app não tem resposta pronta, quando a resposta vem de um trecho do guia e em perguntas sobre o próprio app ("o que você faz?"), **no chat e na conversa por voz**. Ela recebe a **ficha de bordo** — o que o app sabe agora, cada bloco com a fonte, sem as coordenadas do barco, que nunca saem do aparelho — e as últimas mensagens, para entender continuações ("e o gerador?"). O item do FAQ que você toca vai à IA como o primeiro trecho. Resposta pronta, emergência, salvatagem, óleo e registro no diário continuam 100% no aparelho. A linha da fonte mostra "via IA na nuvem (Workers AI · …)". Sem a IA (aparelho não ativado, sem internet, limite ou cota do dia), fica a resposta local, com o motivo na linha da fonte. **Ativar um aparelho** (uma vez por celular ou computador): entrar no app com login e senha e, **depois**, tocar em **Ativar IA na nuvem** numa resposta do chat ou abrir `https://v2.capitaoia.com.br/#ia=ativar` — aparece uma caixa: colar a `CHAVE_APP` (do arquivo PRIVADO do proprietário, fora do repositório) e confirmar. A chave colada é limpa (sai "CHAVE_APP:", aspas, espaços) e conferida na hora no servidor, sem gastar a cota: aparece "IA na nuvem ativada ✓" ou o motivo. A chave fica só no aparelho e **nunca passa pelo endereço** (o endereço fica no histórico do navegador, que pode sincronizar). `#ia=sair` desativa; qualquer outro valor em `#ia=` é ignorado. **Se a IA não responder:** digite **diagnóstico** no chat — mostra a versão de cada parte do app, se a IA está ligada neste aparelho, se há chave guardada e testa a chave no servidor.
- **Atalhos:** perguntas prontas com um toque — 6 padrão, banco de 12, até 8 na tela, editáveis.
- **Console:** telemetria do instante (hora e fonte em cada leitura) com **gráficos** do histórico e da janela de 150 s e as abas de tendências (a Ponte), o **mapa de sensores** sobre o desenho do barco (A4 na web, A5 no app), a **lista de alertas** e a **faixa de AVISO** no alto (toque em ABRIR para ver o alerta; ela nunca troca de tela sozinha e nunca aparece no SOS), gestão, manutenção com **Executado** (linha nova no diário), **checklists** de saída, chegada, abastecimento e fundeio (CONCLUIR grava uma linha no diário), documentos com **estoque de peças**, abastecimento com **consumo** e autonomia, diário de bordo (só cresce) e equipe com prestadores e tarefas (telefones só no aparelho).
- **Alarmes e pendências pelo chat:** "me avise se…", "meus alarmes", "apagar alarme #n", "agendar … para dd/mm"; o relato de uma falha vira pendência com Desfazer, e o fechamento é uma linha nova. O aviso aparece só na tela do app e nunca é crítico.
- **Modo navegação:** o conjunto de gatilhos troca sozinho pelo SOG (NAVEGANDO com 1 nó ou mais por 5 s; FUNDEADO ou ATRACADO com menos de 0,5 nó por 5 s), sem trocar de tela.
- **FAQ de bordo:** 91 itens com busca (a F6) — passo a passo por equipamento (motores, gerador, estabilizador, climatização, dessalinizador, eletrônicos, radar, AIS, piloto, guincho, bombas de porão, sistema elétrico, sistema fixo de incêndio, EPIRB) e os 9 cartões de emergência, que abrem no aparelho. Cada item tem o botão para perguntar ao barco.
- **SOS:** canal 16 com roteiro MAYDAY, homem ao mar, incêndio (Seafire) e EPIRB, com o procedimento padrão e "modelo, validade e acionamento: veja a etiqueta do equipamento"; o MMSI é o do rádio de bordo (etiqueta / Licença de Estação), e o indicativo é o da Licença de Estação (no rádio). A posição é o GPS do aparelho ou "leia no plotter". Em todas as telas, abre offline e sem login.
- **Conversa por voz:** o botão **CONVERSA** é o círculo com o ∞ da WonderHUB.AI, as cores da logo correndo pelo infinito. A conversa abre em tela cheia um **núcleo de anéis** (anel graduado, anel de segmentos, espectro de 48 barras e anel tracejado, com o ∞ no centro, nas cores WonderHUB.AI) — ouvindo, processando enquanto a IA na nuvem responde, falando — com a legenda, um painel vivo a cada segundo (hora, posição, velocidade, rotação e diesel), o SOS no canto e ENCERRAR (ou Esc). A pergunta falada sai na hora, sem a pausa do chat. **Voz a 1,15x em tudo**, emergência inclusive. A voz fala só a 1ª linha (na resposta da IA, a 1ª frase e a seguinte, se a primeira for curta); emergências são lidas inteiras. Abertura: "Capitão IA online. Que precisa?"
- **Cabeçalho ao vivo:** hora local do barco, máxima e mínima do dia, vento e rajada do dia em nós com a direção (ECMWF via Open-Meteo; o toque abre o windy.com) e maré agora (modelo Open-Meteo Marine — não é a tábua da Marinha), na posição de referência de Balneário Camboriú. Tempo e maré são sempre reais; sem rede, aparece a última leitura com a hora.
- **Tema claro/escuro** (sol/lua ao lado do avatar). O SOS do app e o alerta crítico ficam sempre escuros.
- **Personalização por aparelho:** atalhos, blocos do console (8), diário, tarefas executadas, documentos, peças, equipe e tema. Fixos: SOS, os 5 botões do início e a barra do assistente.
- **Dados do aparelho:** `dados.html` baixa uma cópia JSON do que você guardou (nunca a sessão, as chaves nem a última leitura) e restaura sem apagar nada: restaurar só soma.

## Telas

Todos os arquivos terminam em `.dc.html` (41 telas: 18 web · 23 app).

| Web (1440 × 900) | App (390 × 844) |
|---|---|
| `Main` · Início | `H2-Home-Mobile` · Início |
| `A1-Ponte-Web` · Telemetria | `A2-Ponte-Mobile` · Console · `A3-Ponte-Editar` · editar blocos |
| `A4-Sensores-Web` · Mapa de sensores | `A5-Sensores-Mobile` · Mapa de sensores |
| `B1-Carta-Web` · Gestão | `B2-Carta-Mobile` · Sistemas · `B3-Carta-Resposta` · resposta por voz |
| `C1-Leme-Web` · Manutenção | `C2-Leme-Mobile` · Manutenção · `C3-Leme-Alerta` · alerta vivo |
| `C4-Checklist-Web` · Checklists | `C4-Checklist-Mobile` · Checklists |
| `G1-Documentos-Web` · Documentos e peças | `G1-Documentos-Mobile` |
| `G2-Abastecimento-Web` · Nível e consumo | `G2-Abastecimento-Mobile` |
| `G3-Diario-Web` | `G3-Diario-Mobile` |
| `G4-Equipe-Web` | `G4-Equipe-Mobile` |
| `F1-FAQ-Hub-Web` e `F2`–`F5` `-Web` | `F1-FAQ-Hub` e `F2`–`F5` (Estabilizador · Eletrônicos · Gerador · Climatização) |
| `F6-FAQ-Equipamentos-Web` · 91 itens com busca | `F6-FAQ-Equipamentos` |
| `H3-Atalhos-Editar-Web` | `H3-Atalhos-Editar` |
| `S1-SOS-Web` | `S2-SOS-Mobile` |
| — | `E1-Navegando-Gatilhos` · `E2-Navegando-Sintoma` · modo navegação |

Fora da prancheta: `index.html` e `login.html` (entrada), `dados.html` (dados do aparelho) e `relatorio.html` (relatório A4). E ainda: `Manual-Capitao-IA` (apresentação de uso) e o `Guia-Rapido-Capitao-IA.pdf` (A4, gerado de `guia-rapido/`).

## Dados e privacidade

- **Uma fonte só:** `capitao-dados.js` (gerado por `ferramentas/demo/gerar_demo.py`) — embarcação, equipamentos, guias de bordo, agenda, documentos, diário, abastecimentos, equipe, peças, checklists, FAQ, protocolos, o histórico e o roteiro da navegação. `base-conhecimento.json` e `faq-equipamentos.json` trazem os trechos dos guias e o FAQ (fonte e seção), para a busca do chat e da voz, offline. A agenda, os documentos e o diário contam os prazos a partir da data de hoje do aparelho.
- **O site é público.** Nada de contratos, notas fiscais, título de propriedade, CPF/CNPJ, telefones, e-mails, valores, nomes de terceiros, chaves ou IDs do Drive.
- **O que você edita fica no navegador** (localStorage): atalhos, blocos, diário, executadas, documentos e NFs enviados, peças, equipe e tema. Não sincroniza entre aparelhos; limpar os dados do navegador apaga — por isso a página **Dados do aparelho** baixa uma cópia e restaura (só soma, nunca apaga).
- **Coordenadas nunca saem do aparelho** (nem para a IA). **Motor desligado** mostra a última leitura com motor ligado e a hora, nunca zero. **Telemetria real desligada:** o app usa a navegação em laço do próprio aparelho, sem proxy e sem rede.

## Integrações

Tudo que precisa de chave passa por um Cloudflare Worker (`ORIGENS` + `CHAVE_APP` no cabeçalho `X-Capitao-Chave` + freio por IP) e **vem desligado** (`URL_PROXY = ''`), caindo no dado local em erro, demora ou sem internet: telemetria real (`capitao-telemetria`), IA na nuvem (`capitao-ia`: **Workers AI, ligada desde a 1.0.4**; ou Claude API, paga — mesmo cliente) e voz em nuvem opcional (`capitao-voz`). O Worker com o modo da 1.1.0 está pronto no repositório e ainda não foi colado no painel da Cloudflare. Detalhes, status e ordem para ligar: [`integracoes/`](integracoes/README.md).

## Requisitos

- **Internet na primeira visita** (o React vem do próprio site, em `assets/vendor/`). Depois, todas as telas abrem sem internet — inclusive o SOS.
- **Voz:** Chrome, Edge ou Safari, com permissão de microfone. O Firefox não reconhece voz. Melhor voz grátis no computador: Microsoft Edge.

## Estrutura

```
index.html · login.html         entrada (detecta o aparelho) e login
dados.html · relatorio.html     dados do aparelho (copiar e restaurar) · relatório A4
*.dc.html                       41 telas web e app (support.js monta as pranchetas)
capitao-dados.js                dados da embarcação (gerado — não editar à mão)
capitao-auth.js                 login, versão, rodapé, saudação e período
capitao-brain.js                cérebro: respostas, roteamento, base, diário, atalhos e voz
capitao-replay.js               navegação em laço de 150 s (o instante único de todas as telas)
capitao-alertas.js              API única de alertas (AVISO)
capitao-grafico.js              gráfico do histórico e da janela de 150 s
capitao-sensores.js             sensores sobre o desenho do barco (A4 e A5)
capitao-faq.js                  FAQ dos equipamentos (F6)
capitao-theme.js · capitao-app.js · capitao-moldura.js · capitao-voz.js · capitao-clima.js · capitao-barra.js · capitao-telemetria.js · capitao-ia.js
capitao-simbolo.js              ∞ da WonderHUB.AI com as cores correndo (botão CONVERSA)
base-conhecimento.json · faq-equipamentos.json    trechos dos guias de bordo · FAQ dos equipamentos
Manual-Capitao-IA.dc.html · deck-stage.js     apresentação de uso
Guia-Rapido-Capitao-IA.pdf · guia-rapido/     guia rápido A4
manifest.webmanifest · sw.js · .nojekyll      app instalável e cache offline
assets/ · favicon.ico           ∞ e assinatura WonderHUB.AI, ícones, favicon e atalhos do app instalado (atalho-*.png), logo Wonder BOAT (crédito), desenho dos sensores e o React (vendor/)
integracoes/                    estrutura desligada das integrações
ferramentas/                    gerador dos dados, gerador do guia, gerador dos ícones dos atalhos, gerador de senha, plano da versão (prompts/)
testes/                         cérebro, SOS, rodapé, gerador, reprodução, termos, matriz de telas, proxies da IA (worker_ia.py), IA no chat (chat_ia.py) e publicação
CLAUDE.md                       guia do projeto para o Claude
```

## Versões

A versão aparece no rodapé de todas as telas. Para lançar: `VERSAO` em `capitao-auth.js`, `capitao-brain.js` e nas duas cópias do `capitao-ia.js`, `CACHE` em `sw.js` e a versão e esta tabela — os seis lugares iguais.

| Versão | Data | O que mudou |
|---|---|---|
| 1.1.0 | 14/11/2026 | **Paridade com o Avanti Vessel AI 1.24.0** e navegação em laço: a embarcação navega num laço de 150 s (âncora 07:00, posição contínua pela rota) e **tudo lê o mesmo instante** — moldura, telas, chat, voz, ficha da IA — com número e hora e **sem selo nem rótulo** (dados completos: barco, registro, equipamentos, guias, agenda, histórico) · tempo e maré sempre reais · **SOS fora da navegação** (GPS do aparelho ou "leia no plotter", MMSI do rádio de bordo, EPIRB e Seafire no procedimento padrão, rota de salvatagem sempre local) e **emergência só no aparelho**, com janela de 15 min sem posição, rumo, velocidade, chegada nem pessoas · **funções do Avanti 1.24.0 portadas:** React do próprio site (F01), ícones dos atalhos (F03), vento e rajada do dia (F13), conversa por voz sem pausa (F19), dados do aparelho (F25), alertas com a faixa de AVISO (F05), gráficos do histórico (F07, F33), mapa de sensores A4/A5 (F08), checklists (F09), FAQ dos equipamentos com 91 itens (F10), tendências (F11), alarmes pedidos pelo chat (F12), propostas A CONFIRMAR (F14), diário→agenda (F15), relato de falha (F16), registro pelo chat (F17), contexto da conversa (F18), pendências (F20), prestadores (F21), estoque de peças (F22), consumo (F23), relatório A4 (F24), capacidades (F26), CONVERSA com o núcleo de anéis (F27), limpeza da resposta da IA (F29), FAQ na IA (F30), ditado e siglas (F31, F32), foto com texto (F36) · **41 telas** (novas: A4, A5, C4 web e app, F6 web e app) e as páginas `dados.html` e `relatorio.html` · IA na nuvem: os dois Workers com o texto de sistema do modo da navegação, filtro de saída e de coordenadas, ficha de até 16.000 letras (o código está no repositório; falta colar no painel) · pessoa ao mar e sumida detectada por estrutura (falha de 2,68 % na matriz adversarial) · testes novos: gerador, SOS, rodapé, reprodução (`--dia`, `--moldura`) e termos · fora, de propósito: o rosto de partículas (sai da CONVERSA) e os selos de demonstração |
| 1.0.9 | 29/09/2026 | **Login de convidado** para mostrar o app a clientes: botão no login, senha passada pelo proprietário (no código, só sal e hash) · entra como convidado (rodapé, saudação, chat e diário deste aparelho) e aparece em Equipe como convidado, fora da lista da embarcação · a IA na nuvem continua só em aparelho ativado (a chave não vem com o login) |
| 1.0.8 | 27/09/2026 | **Marca WonderHUB.AI em tudo:** o ∞ nos cabeçalhos, no ícone do app instalado, na tela de abertura e no favicon; a assinatura (∞ + WonderHUB.AI) no login, no início da lista, na capa do Manual e do Guia · a Wonder BOAT fica no crédito **"Design by Wonder BOAT \| WonderHUB.AI"** (as duas logos lado a lado no login e no fecho do Manual; em texto no rodapé) · botão **CONVERSA** = círculo com o ∞ original e as cores da logo correndo pelo infinito (mais rápido com a conversa ligada), no Main, no dock da H2 e na barra das telas do app · a conversa por voz troca os anéis por um rosto de perfil feito de partículas (trocado na 1.1.0 pelo núcleo de anéis) · **voz a 1,15x em toda fala**, emergência inclusive (e na voz em nuvem, desligada) |
| 1.0.7 | 27/09/2026 | Correções da revisão adversarial da 1.0.6 (a IA já funcionava no celular do proprietário): "a IA não está funcionando" e "luz do óleo acesa… funcionando" caíam no gerador ("funci**onan**do" continha "onan") — o alarme de óleo volta ao passo a passo dos motores · ficha resumida só em pergunta pura sobre o app (trecho do guia e "o que você sabe sobre o seguro?" voltam à completa: a resumida tirava o dado) · chave colada é testada ANTES de ser guardada (texto recusado nunca apaga uma chave que funciona) e o aviso diz se ficou no app instalado ou no navegador · caixa da chave fechada por uma recarga reabre · a recarga de versão nova espera um momento seguro (sem texto digitado, conversa por voz ou resposta a caminho) e nunca recarrega o SOS · PDF do guia fora da instalação e React da cópia guardada (versão nova instala no 4G fraco; SOS monta sem esperar a CDN) · "diagnóstico" entende "Capitão, diagnóstico", "a IA não está funcionando"… e, na voz, fala se a IA está ligada |
| 1.0.6 | 27/09/2026 | **A IA volta a funcionar no celular do proprietário:** depois da 1.0.5 o aparelho não mandava nenhum pedido ao Worker (métricas da Cloudflare: 0 pedidos do celular; o Worker respondia certo em 3 a 5 s). Causas atacadas: arquivos velhos ou misturados no aparelho (o GitHub Pages manda max-age=600 e o service worker buscava pelo cache HTTP; o app instalado fica vivo com o JS antigo) · chave colada com "CHAVE_APP:", aspas, espaço ou caractere invisível · aviso de IA desligada quase invisível e mudo na voz. Agora: o service worker sempre confere com o servidor (ETag); a tela recarrega uma vez quando uma versão nova assume, procura versão nova ao voltar para a frente e se recarrega sozinha se cérebro, cliente e rodapé vierem de versões diferentes · a chave é limpa ao colar, validada e testada no servidor na hora (sem gastar a cota), com aviso · link #ia=ativar aberto sem login abre a caixa depois de entrar · sem a IA ativada, aviso grande na tela e falado na conversa; a voz diz o motivo quando a IA falha e não repete a abertura em "o que você faz?" · **"diagnóstico" no chat**: versões, internet, estado da IA, chave (só o tamanho) e teste da chave no servidor · ficha resumida em pergunta sobre o app e em trecho do guia (~70 % menos cota) |
| 1.0.5 | 27/09/2026 | **IA que conversa:** a IA na nuvem passa a responder quando não há resposta pronta (antes só entrava em trecho do guia), em perguntas sobre o app ("Oque você faz?" agora é entendido) e **na conversa por voz**, com a **ficha de bordo** (tudo o que o app sabe, com as fontes, sem coordenadas) e o **histórico** da conversa · conhecimento geral de náutica permitido; dado do barco só das fontes · a resposta espera a IA e entra logo depois da pergunta; na voz, o núcleo fica em PROCESSANDO e fala a resposta da IA · sem a IA, a linha da fonte diz o porquê (aparelho não ativado, sem internet, limite, cota) e o botão **Ativar IA na nuvem** ativa o aparelho sem digitar endereço · Worker `capitao-ia` com ficha, histórico e limite do AI Gateway (429), publicado · AI Gateway de 3 para **30 perguntas por hora** · proxy da Claude API com o mesmo contrato |
| 1.0.4 | 27/09/2026 | **IA na nuvem ligada** (Workers AI · Llama 3.3 70B, grátis): Worker `capitao-ia` publicado com limite global de 3 perguntas/hora (AI Gateway) e sem logs de invocação; Main e H2 usam a IA só nas respostas do guia, com a fonte "IA na nuvem"; cada aparelho ativa com `#ia=ativar` depois do login, colando a chave numa caixa (a chave nunca passa pelo endereço) · o login não leva mais nada de `#ia=`/`#tele=`/`#voz=` para o `?next=` · link de fora (`#q=`) não gasta a cota · exceção à regra do login no servidor, aprovada pelo proprietário: Cloudflare Access antes de dados reais |
| 1.0.3 | 27/09/2026 | Domínio próprio **v2.capitaoia.com.br** (o app ganha uma origem só dele; o endereço antigo redireciona). Mudou a origem: **entrar de novo em cada aparelho**; atalhos, diário, documentos, equipe e tema salvos no aparelho ficaram no endereço antigo · Workers aceitam só a origem nova |
| 1.0.2 | 27/09/2026 | Telemetria: chave no endereço (`#tele=`) sem estragar o link e URL de teste restrita ao próprio Worker · IA na nuvem: integração grátis com Workers AI (desligada), cliente único para Workers AI ou Claude API, proxy da Claude API com as mesmas guardas · regra: origem só do app antes de ligar proxies · Manual atualizado |
| 1.0.1 | 27/09/2026 | Senha do proprietário trocada (sal e hash novos; a senha inicial deixa de valer) |
| 1.0.0 | 27/09/2026 | Primeira versão: clone do motor do Avanti Vessel AI 1.4.6 para a embarcação Capitão IA (fonte no Google Drive › Capitão IA v2) · 35 telas (15 web · 20 app) e o Manual · chat com fonte em toda resposta · SOS offline e sem login · marca Wonder BOAT com a paleta WonderHUB.AI · integrações como estrutura desligada · Manual e Guia rápido |

## Publicar e atualizar

1. Merge da branch `claude/…` da versão (a do PR aberto no GitHub) na `main` — **só quando o proprietário pedir** (publica o site).
2. GitHub › Settings › Pages › Deploy from a branch › `main` · `/ (root)` › Save.
3. A nova versão entra no ar em 1 a 2 minutos. Desde a 1.0.6 o celular se atualiza sozinho: a 1ª abertura depois de publicar ainda pode vir da versão anterior, e a tela se recarrega na nova assim que ela assume (o app instalado procura versão nova ao voltar para a frente). Para conferir: digite **diagnóstico** no chat.
4. O Worker `capitao-ia` não se publica com o site: o código de `integracoes/workers-ai/ia-worker/worker.js` é colado no painel da Cloudflare pelo proprietário (passo a passo em `integracoes/workers-ai/README.md`). Site e Worker podem ir no ar em qualquer ordem.

---

Embarcação Capitão IA · Design by Wonder BOAT | WonderHUB.AI
