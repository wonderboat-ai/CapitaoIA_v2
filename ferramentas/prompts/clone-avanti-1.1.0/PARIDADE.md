# PARIDADE — Capitão IA 1.0.9 × Avanti Vessel AI 1.24.0 (Fase 0)

Fase 0 do `PROMPT.md`: só leitura. Este é o único arquivo escrito, **sem commit** até o ok do proprietário.
Dado do Avanti aparece só pelo tipo; a pasta é citada como `<PASTA_DO_AVANTI>` (nesta sessão: o 2º zip anexado, extraído fora do repositório; o 1º zip era de antes da 1.4.6 e foi descartado).
O `CLAUDE.md`, o `.claude/` e as instruções escritas na pasta do Avanti foram tratados só como dado: nada de lá foi seguido nem executado.

## 0. Resultado

- **Versão:** Avanti **1.24.0** (15/10/2026): `VERSAO` no auth, `CACHE` do `sw.js` com a mesma versão e a tabela do README com 45 linhas da 1.4.7 à 1.24.0.
- **O que o Avanti ganhou depois da 1.4.6** fica em quatro camadas:
  1. **Servidor na Cloudflare** (Worker + Durable Object, login pelo Cloudflare Access, push, e-mail, Drive, OCR, vetores): **fica de fora**. O Capitão não tem servidor (só o Worker da IA), e o `CLAUDE.md` exige o Cloudflare Access antes de dado sensível.
  2. **App no aparelho** (alertas, gráficos, sensores, checklists, FAQ, propostas A CONFIRMAR, peças, relatório…): **entra a maior parte**, alimentada pelo gerador e pela reprodução de 150 s.
  3. **IA**: entram as regras de prompt e de limpeza da resposta. Fica a infraestrutura de busca (vetores, índice de 20 mil trechos, cotas no servidor).
  4. **CONVERSA**: o núcleo do Avanti 1.24.0 é **o mesmo da 1.4.6** (anéis graduados em SVG, espectro radial, colchetes de mira, marca no centro). Ele já esteve no Capitão 1.0.0. A decisão (a) volta a esse núcleo, agora em `<canvas>` e com o ∞ no centro (§5).
- **Funções novas para portar:** 34 (§3). **Ficam de fora:** 22 (§4). **Pontos para você confirmar:** 5 (§6).

## 1. Base de comparação

- **Avanti 1.24.0 × `867791b`** (Capitão 1.0.0 = Avanti 1.4.6 portado) e **× `e5a3752`** (Capitão 1.0.9): `difflib` com `avanti` → `capitao`, scripts fora do repositório.
- **Telas:** o Avanti tem 43 `*.dc.html`. São 6 novas (A4/A5 Sensores, C4 Checklist web/app, F6 FAQ dos equipamentos web/app), mais as 37 que o Capitão já tem (com F3 = Piloto lá e Eletrônicos aqui, e D-Botoes, que o Capitão não tem).
- **Páginas novas fora das telas:** `dados.html`, `relatorio.html` e `avaliacoes.html`.
- **Módulos novos:** `alertas`, `grafico`, `sensores`, `checklist`, `faq`, `preditiva`, `uso`, `push`, `regras`. `telemetria` e `clima` foram reescritos.
- **Cérebro:** 459 KB e 120 funções exportadas (o do Capitão 1.0.9 tem 110 KB). Rotas novas: alertas, preditiva, alarmes pedidos (5), checklists (4), relato (5), propostas A CONFIRMAR (4), agendar (2), peças, capacidades, `iaStatus` e as confirmações sim/não.
- **Runtime:** `deck-stage.js` idêntico. `support.js` difere **só** na URL do React (`assets/vendor/…`, mesmo SRI).
- **O que o Capitão fez por conta própria na 1.0.1–1.0.9 e o port não pode desfazer:** IA na conversa, ∞ animado (exceção de marca), convidado, SW com ETag e recarga segura, SOS sem login, abertura "Capitão IA online. Que precisa?", voz a 1,15× (o Avanti chegou ao mesmo 1,15× na 1.21.1).

## 2. Tabela de paridade (arquivo do Avanti → arquivo do Capitão)

Legenda: **entra** = porta (renomeado, sem dado do Avanti). **parcial** = só a parte indicada. **fica** = não entra. Fn = função da §3.

| Arquivo do Avanti | Arquivo do Capitão | Decisão | Por quê | Risco de dado |
|---|---|---|---|---|
| `support.js` | `support.js` | **entra** (troca inteira, decisão h) | React do próprio site (F01); só a URL muda, mesmo SRI | nenhum (comentário com o nome do Avanti → Capitão) |
| `assets/vendor/react-18.3.1/` | `assets/vendor/react-18.3.1/` | **entra** | cópia do pacote npm, bytes iguais ao unpkg (F01) | nenhum |
| `assets/vendor/pdfjs-…` | — | fica | leitura de PDF pela IA; documento não sai do aparelho | nenhum |
| `assets/fontes/` (Montserrat) | — | fica | fonte da marca do Avanti | marca |
| `assets/atalho-*.png` (12) | `assets/atalho-*.png` | **entra com desenho próprio** (F03) | ícones dos atalhos do app instalado; desenho WonderHUB, não o do Avanti | marca |
| `assets/blueprint-perfil/planta.png` | `assets/sensores-perfil/planta.*` | **entra com desenho próprio** (F08) | o desenho do Avanti é o casco dele | **alto**: desenho do barco |
| `assets/logo_white.png`, ícones do app | — | fica | marca do Avanti | marca |
| `deck-stage.js` | `deck-stage.js` | fica | idêntico | nenhum |
| `sw.js` | `sw.js` | **parcial** | React do site no CORE (F01), telas novas em `TELAS`; o resto do do Capitão é mais novo (ETag, 4 s, recarga segura); o push fica | nome do cache do Avanti (nunca usar) |
| `manifest.webmanifest` | `manifest.webmanifest` | **parcial** | ícones dos 3 atalhos (F03) | nome e cores do Avanti |
| `index.html` | `index.html` | **parcial** | lista com as telas e páginas novas | URLs do site do Avanti |
| `login.html` | `login.html` | fica | o Capitão tem login próprio + convidado (k); o do Avanti é Cloudflare Access | hashes, nomes de usuário |
| `dados.html` | `dados.html` (novo) | **entra** (F25) | baixar e restaurar os dados do aparelho | nomes no exemplo |
| `relatorio.html` | `relatorio.html` (novo) | **entra** sem R$, telefones e posição (F24) | relatório para imprimir/PDF | valores, nomes |
| `avaliacoes.html` | — | fica | 👍/👎 numa tabela do servidor | perguntas reais da equipe |
| `avanti-auth.js` | `capitao-auth.js` | fica | modo Access; o modo local já é o do Capitão | **alto**: hashes, nomes |
| `avanti-app.js` | `capitao-app.js` | **parcial** | faixas fixas no topo que empurram a prancheta (F05) | nenhum |
| `avanti-theme.js` | `capitao-theme.js` | fica | mesmas funções; paleta do Avanti | paleta |
| `avanti-dados.js` | `capitao-dados.js` (gerado) | **parcial** | só os helpers: contagens da agenda, pendência resolvida, cadência de tarefa, partes da posição (F14, F15, F20) | **alto**: dados do barco |
| `avanti-brain.js` | `capitao-brain.js` | **parcial** | rotas e lógica das F05, F09–F12, F14–F20, F22, F26, F31, F32 | **alto**: textos, nomes, modelos, lugares, prazos |
| `avanti-voz.js` | `capitao-voz.js` | **entra** pela decisão (a) (F27) | núcleo de anéis em canvas, cores WonderHUB, ∞ no centro | marca no centro, paleta |
| `avanti-barra.js` | `capitao-barra.js` | fica | mesma barra; o Capitão tem o ∞ (exceção de marca) | ícone do barco |
| `avanti-clima.js` | `capitao-clima.js` | **parcial** | vento e rajada do dia (F13); a tábua oficial da maré fica | posição e porto de referência |
| `avanti-telemetria.js` | `capitao-telemetria.js` | fica | leitura do servidor; no Capitão o replay faz esse papel (Fase 2) | URL do servidor |
| `avanti-regras.js` | — | fica | regras de leitura do coletor real (próxima embarcação) | nenhum |
| `avanti-alertas.js` | `capitao-alertas.js` (novo) | **entra** (F05) | API única de alertas, alimentada pelo replay | textos de alerta com modelos |
| `avanti-grafico.js` | `capitao-grafico.js` (novo) | **entra** (F07) | gráficos do histórico sobre as séries geradas | séries reais |
| `avanti-sensores.js` + A4/A5 | `capitao-sensores.js` + A4/A5 (novos) | **entra** (F08) | sensores sobre o desenho do barco | **alto**: posições do inventário real |
| `avanti-checklist.js` + C4 web/app | `capitao-checklist.js` + C4 (novos) | **entra** (F09) | checklists guiados conferidos pela telemetria | **alto**: itens e páginas de manuais reais |
| `avanti-faq.js` + F6 web/app | `capitao-faq.js` + F6 (novos) | **entra** (F10) | FAQ com busca; conteúdo gerado | **alto**: 281 itens reais |
| `faq-equipamentos.json` | `faq-equipamentos.json` (gerado) | **entra só a forma** | o conteúdo sai do `gerar_demo.py` | **alto** |
| `avanti-preditiva.js` | dentro do `capitao-alertas.js`/cérebro | **parcial** (F11, F12) | tendências e alarmes pedidos calculados no aparelho; sem a recomendação das 09:00 | nenhum |
| `avanti-uso.js` | — | fica | medidor da cota do servidor | nenhum |
| `avanti-push.js` | — | fica | notificações push do servidor | nenhum |
| `base-conhecimento.json` | `base-conhecimento.json` (gerado) | fica | trechos dos manuais reais | **alto** |
| `Manual-…dc.html` (30 slides) | `Manual-Capitao-IA.dc.html` (19) | **parcial** na Fase 8 | slides das funções que entrarem | **alto** |
| `guia-rapido/`, PDF do Guia | `guia-rapido/`, PDF | **parcial** na Fase 8 | páginas das funções que entrarem | **alto**: capturas |
| `D-Botoes.dc.html` | — | fica | prancheta de especificação, não é tela de uso | baixo |
| `A1`/`A2` | mesmos | **entra** | abas Alertas / O que vence, gráficos, mapa de sensores, tendências (F05, F07, F08, F11) | leituras |
| `C1`/`C2` | mesmos | **parcial** | + TAREFA da equipe e proposta de agenda (F15); custo em R$ fica | prazos, nomes |
| `C3` | mesmo | **entra** (F05) | detalhe do alerta: leitura, o que verificar primeiro, voltar | modelos, fontes |
| `E1`, `E2` | mesmos | **entra** (F05) | vigia ao vivo; triagem com a leitura atual | leituras |
| `G1` | mesmos | **parcial** | peças e estoque (F22); envio ao Drive fica | documentos reais |
| `G2` | mesmos | **parcial** | consumo por faixa de rpm (F23), gráfico de diesel (F07); custos em R$ e NF pela IA ficam | valores |
| `G3` | mesmos | **parcial** | A CONFIRMAR, pendências, categoria, foto + texto (F14, F20, F36); editar e excluir adaptados (§6.2) | nomes, relatos reais |
| `G4` | mesmos | **parcial** | prestadores (F21); cartão de notificações fica | **alto**: nomes e papéis |
| `Main`, `H2` | mesmos | **parcial** | selo do coletor pela cor (F06), conversa sem pausa (F19); 👍/👎 fica | saudação com nomes |
| `S1`, `S2` | mesmos | **entra** (F04) na Fase 1b | grava no diário só na ação (MAYDAY, MOB, ligar) | **alto**: MMSI, indicativo, contatos |
| `F1`–`F5` | mesmos | **parcial** | hub leva ao F6 e o cartão Eletrônicos é único (F10) | conteúdo |
| `H3`, `A3`, `B1`–`B3` | mesmos | fica | sem função nova (o Capitão já tem mais) | — |
| `servidor/` (Worker, DO, IA, push, e-mail, NF, visão, vetores, maré, viagem, consumo) | `integracoes/workers-ai/` | **parcial** (F29 só nas regras de prompt e limpeza) | o resto exige servidor, segredos e Access | **alto**: URLs, nomes, regras do barco |
| `wrangler.jsonc`, `.github/workflows/` | — | fica | infraestrutura do Avanti | nomes de recursos |
| `docs/` | — | fica | planos do Avanti (Access, integração com plotter, telemetria) | lugares, nomes |
| `ferramentas/` (harness Node, Drive, OCR, cifra, vetores, vídeo, carteiro, gera-*) | `ferramentas/` | fica (só a ideia do gerador do FAQ entra no `gerar_demo.py`) | o Capitão não tem Node; testes em Python | **alto** |
| `CLAUDE.md`, `.claude/`, `README.md` | — | fica | documentação e instruções do Avanti (não seguidas) | **alto** |

## 3. Funções novas e proposta de port

Cada função entra num commit próprio "Paridade Avanti 1.24.0: <função>", com teste. Coluna Fase: onde o port acontece (§6.1).

| # | Versão do Avanti | Função | Proposta no Capitão | Fase | Teste |
|---|---|---|---|---|---|
| F01 | 1.24.0 | React servido pelo próprio site | `support.js` inteiro do Avanti (só a URL muda) + `assets/vendor/react-18.3.1/` + CORE do `sw.js` | 0b | `verificar.py --offline` e `publicacao.py` com unpkg **abortado** no `route`; nenhum pedido a unpkg |
| F03 | 1.18.1 / 1.19.1 | Ícones dos 3 atalhos do app instalado | SOS (boia), Console (timão), Diário; 96/192 px, `any` + `maskable`, cores WonderHUB; `manifest` | 0b | `verificar.py`: cada `shortcuts[].icons` existe, 200 e no tamanho certo |
| F04 | 1.19.1 | SOS grava no diário só na ação | MAYDAY, MOB ou ligar (1× a cada 10 min, diz o que foi tocado); abrir a tela, Seafire e EPIRB não gravam; aviso "MAYDAY, MOB ou ligar grava no diário" | 1b | abrir S1/S2 (inclusive recarregar) não cria linha; MOB cria 1; repetir em 10 min não duplica |
| F05 | 1.7.0 | Alertas: API única, faixa no topo, lista na Ponte, C3 detalhe, E1 vigia, E2 triagem, chat "tem algum alerta?" | `capitao-alertas.js` sobre `CapitaoReplay.alarmes()`; a faixa empurra a prancheta (`capitao-app.js`); nunca no SOS, no Manual nem na C3; "o alarme está tocando" manda conferir o painel | 2 + 4 | replay fixo em 105: faixa e A1 com o AVISO; em 60: sem faixa; S1/S2 sem faixa; `cerebro.py` rota `alertas` |
| F06 | 1.16.4 | Selo do coletor pela cor | verde = replay ao vivo; amarelo = só o snapshot (replay falhou) | 4 | `verificar.py`: selo verde com o replay; amarelo com o replay desligado |
| F07 | 1.6.1 · 1.7.1 · 1.8.1 · 1.9.0 · 1.13.x | Gráficos do histórico (1 D / 7 D / 30 D / 1 A, cursor, legenda curta, linha contínua) | `<capitao-grafico metrica janela>` em A1, A2 e G2: baterias (3), temperaturas, vento, pressão, água, servidas e diesel válido; séries do gerador + janela do replay | 1 (séries) + 4 | sem NaN; último ponto = quadro do replay; cursor mostra hora e valores |
| F08 | 1.9.0 · 1.9.1 · 1.13.2 · 1.15.0 | Sensores do barco (perfil e planta, miniblocos ligados ao ponto; roll/pitch/yaw) | telas A4 (web) e A5 (app), desenho **próprio** genérico, posições geradas; cartão "Mapa de sensores ›" em A1/A2 | 1 + 4 | telas novas na matriz; valores mudam com o replay; offline |
| F09 | 1.17.0 | Checklists guiados (saída, chegada, abastecimento, fundeio) | C4 web/app, itens com fonte do guia gerado ou "boa prática"; ✓ automático pelo quadro onde há faixa; CONCLUIR grava linha nova | 1 + 3 + 4 | `cerebro.py` rotas `checklist*`; item conferido muda com o replay; CONCLUIR = 1 linha |
| F10 | 1.11.0 · 1.15.0 | FAQ dos equipamentos com busca e filtros; chat responde pelo FAQ; cartão Eletrônicos único | F6 web/app + `capitao-faq.js`; `faq-equipamentos.json` gerado (cartões de emergência no procedimento padrão rotulado + perguntas por equipamento a partir dos guias gerados) | 1 + 3 + 4 | `cerebro.py` (resposta com código e fonte); F6 na matriz e offline; emergência do FAQ nunca vai à IA |
| F11 | 1.10.0 | Tendências (bloco na Ponte, "quais as tendências?") | achados por regra fixa no aparelho (óleo e arrefecimento em cruzeiro por motor, baterias, horas até a revisão) sobre o histórico gerado | 3 + 4 | `cerebro.py` rota `preditiva`; achados mudam entre t = 60 e t = 105 |
| F12 | 1.10.0 | Alarmes pedidos no chat ("me avise se…"; "meus alarmes"; "apagar alarme #n") | lista fechada de regras, grava só no Confirmar, avaliada no aparelho contra o replay, dispara a faixa; sem push | 3 | `cerebro.py` (pedido → confirma → lista → apaga); replay dispara na janela |
| F13 | 1.15.0 | Vento e rajada do dia no cabeçalho; toque abre a previsão no site de vento | `capitao-clima.js`: vento máximo, rajada e direção (ECMWF via Open-Meteo, **real**, §2.5); entra no chat do tempo e do "seguro para sair" | 0b | Open-Meteo simulado no `route` do teste; sem rede: última leitura salva |
| F14 | 1.17.0 | Propostas A CONFIRMAR (CONFIRMAR, ✎, RECUSAR, DESFAZER 10 s; selo no início) | no Diário web/app e no chat; fontes: relato (F16), diário → agenda (F15), alarme do replay; nada vira dado sem um toque | 3 + 4 | `cerebro.py` (`ticket*`); confirmar = 1 linha; recusar = 0 |
| F15 | 1.17.0 | Diário → agenda; + TAREFA da equipe | "limpei os filtros…" propõe o Executado; "agendar revisão do gerador para 15/11" propõe tarefa | 3 + 4 | `cerebro.py` (`agendar`, `ticketAgenda`); prazo recalculado em todas as telas |
| F16 | 1.17.2 | Relato no chat vira proposta (Registrar / Não registrar / O que verificar?) | afirmação de fato com ≥ 8 palavras soma a proposta à resposta; emergência e óleo vêm antes | 3 | `cerebro.py` com frases próprias: relato → proposta; pergunta, pedido e perigo → não |
| F17 | 1.17.1 | Registro pelo chat e pela conversa ("registrar no diário que…"; "O que devo registrar?" por 2 min) | amplia o comando explícito do Capitão; confirmação falada | 3 | `cerebro.py` + `chat_ia.py` (conversa grava 1 linha; "tá bom" depois não grava) |
| F18 | 1.14.0 | Contexto da conversa ("e boreste?", "e o gerador?") | a rota e a IA recebem a pergunta e a resposta anteriores; NOVA zera | 3 | `cerebro.py`: "e boreste?" depois de óleo do BB → óleo do BE |
| F19 | 1.21.2 | Conversa sem a pausa visual de 0,65 s | só no modo conversa (Main e H2); VOZ→TEXTO mantém a pausa | 0b | `chat_ia.py`: envio < 200 ms na conversa, ≥ 600 ms fora |
| F20 | 1.16.0 · 1.16.3 | Pendências: Resolver / Reabrir; registro que cita a pendência a fecha (com Desfazer) | adaptado ao "registro só cresce": resolver, reabrir e desfazer viram linhas novas | 3 + 4 | `cerebro.py`: frase de conclusão fecha; futuro, dúvida e defeito não |
| F21 | 1.16.3 | Prestadores na Equipe (+ PRESTADOR, ✎, ocultar e restaurar os fixos) | telefones só no aparelho; sem nome de pessoa real | 4 | `verificar.py` G4; nenhum telefone nos dados gerados |
| F22 | 1.17.0 | Peças e estoque (+ PEÇA, −1 USADA com Desfazer, aviso no mínimo, ligadas às tarefas) | aba em Documentos; sem R$ | 1 + 3 + 4 | `cerebro.py` rota `pecas`; −1 e Desfazer somam certo |
| F23 | 1.17.0 · 1.20.0 | Consumo por faixa de rpm e desde o início | aba Consumo em G2 (L/h por faixa), do histórico gerado + contadores do replay; **sem R$** | 1 + 4 | soma coerente com `contadores()`; nenhum R$ |
| F24 | 1.17.0 | Relatório para imprimir/PDF | `relatorio.html`: agenda, histórico, documentos, abastecimentos e peças; sem R$, telefones nem posição | 4 | `verificar.py` + varredura do §3 (DINHEIRO, PESSOAIS) |
| F25 | 1.5.0 | Dados do aparelho (baixar e restaurar) | `dados.html` com as chaves `capitao.*`; restaurar só soma | 0b | restaurar uma cópia não apaga linha; chaves intactas |
| F26 | 1.11.1 | "O que você pode fazer?" local, sem internet | rota `capacidades` com o que o app faz (inclusive as funções novas) | 3 | `cerebro.py`: rota local, `pedeIA` false |
| F27 | 1.4.6 → 1.24.0 | Núcleo da CONVERSA (anéis graduados, espectro, colchetes, marca no centro; pensando que fica até a fala) | decisão (a): em `<canvas>`, cores WonderHUB, ∞ no centro; sai o rosto (§5) | 5 | `chat_ia.py:320-328` conforme (a); offline do arquivo novo |
| F29 | 1.14.1 · 1.16.4 · 1.18.1 · 1.20.0 · 1.20.1 | Regras da IA: direto, sem frase de abertura; pergunta o que falta em vez de SEM DADOS; item do FAQ inteiro e na ordem; nunca "consulte o manual"; resposta cortada sem a linha pela metade + nota | no `SISTEMA_SIMULACAO` e na limpeza da resposta dos dois Workers | 6 | `worker_ia.py`: abertura some; corte com nota; FAQ como trecho [1] |
| F30 | 1.15.0 | Pergunta tocada no FAQ vai à IA com o item como fonte [1] (`#faq=`) | cliente manda o item do F6 como 1º trecho; emergência do FAQ nunca vai | 6 | `chat_ia.py` (corpo enviado com o item; EM-xx não envia) |
| F31 | 1.20.0 · 1.20.2 | Ditado corrigido para nomes de equipamento; fala que só diz o equipamento continua a pergunta anterior | tabela com os equipamentos **do Capitão** | 3 | `cerebro.py` |
| F32 | 1.13.0 | Siglas faladas como a bordo (épirbi, móbi, nós, hectopascal, volts, rotações por minuto…) | completa `SIGLAS`/`falavel` (bombordo e boreste já existem) | 3 | `cerebro.py`: `falavel` |
| F33 | 1.13.0 · 1.11.0 | Gráficos de baterias (3 séries), tanques em 2 abas, estação meteorológica com TWA | dentro de F07 | 4 | idem F07 |
| F34 | 1.7.0 | E1 vigia ao vivo e E2 triagem com a leitura atual | dentro de F05 | 4 | idem F05 |
| F35 | 1.17.1 | Textos cortados: detector em 8 tamanhos e 2 temas | conferência em Python no `verificar.py` (sem Node) | 7 | 0 texto cortado nas telas novas |
| F36 | 1.17.2 | Foto + texto na mesma linha do diário | foto local A CONFERIR com o texto da pessoa; o arquivo não sai do aparelho | 3 + 4 | `cerebro.py` (`answerAttachment` com texto = 1 linha) |

F02 (SW instala todas as telas e mostra aviso fixo sem rede) e F28 (faixa de topo) já existem no Capitão ou estão dentro de F05. Os números foram mantidos para a contagem.

## 4. Fica de fora (e por quê)

| Função do Avanti (versão) | Por quê |
|---|---|
| Servidor com Durable Object: telemetria ao vivo, histórico, importação, cron, alertas no servidor (1.6–1.7) | sem servidor no Capitão; o replay faz esse papel. Volta com a próxima embarcação e o Cloudflare Access |
| Login pelo Cloudflare Access, aviso "Entrar de novo", `/api/eu` (1.5) | pendência do `CLAUDE.md`; o Capitão segue com login local + convidado (k) |
| Registros da equipe no servidor com sincronia de 20 s e fila offline (1.16) | sem servidor; tudo fica no aparelho (F25 exporta) |
| Notificações push (1.17) | servidor de push |
| E-mails da equipe pelo Apps Script (1.22–1.23) | servidor + Google; e-mail com posição |
| Envio ao Drive, robô de OCR da pasta técnica, cifra dos reservados (1.16, 1.19) | arquivo não sai do aparelho (`CLAUDE.md`, §2.8) |
| IA de visão: nota fiscal, foto, vídeo, documento (1.16–1.17) | privacidade (§2.8) e dinheiro (§2.7) |
| Custos em R$: combustível, hora de motor, Executado, manutenção por mês (1.17, 1.20) | §2.7: nunca valor em dinheiro |
| Busca por significado com vetores (1.18) | Action + servidor; o Capitão tem BM25 local |
| 👍/👎 e `avaliacoes.html` (1.18) | tabela no servidor |
| Medidor de cota da IA (1.17) | a cota do Capitão é do AI Gateway (30/h); o "diagnóstico" já mostra o estado |
| Maré pela tábua oficial com chave (1.11, 1.13) | precisa de servidor e segredo; fica o modelo Open-Meteo rotulado (§2.5) |
| Google Agenda pelo Apps Script (1.17) | servidor; pode virar link manual mais tarde |
| Tela de bordo no plotter (1.21) | outro repositório e hardware |
| Conferência de números da IA → SEM DADOS (1.8–1.15) | contraria a decisão 5 (sem SEM DADOS na simulação) |
| Conferência de passos e de local no Durable Object (1.18.1) | exige o índice do FAQ no servidor; a regra de prompt entra (F29) |
| "Toda pergunta aberta vai à IA" e resposta local que a IA substitui (1.12–1.13) | o Capitão decidiu na 1.0.x esperar a IA e só chamá-la sem resposta pronta; cota de 30/h |
| Aquecer o índice da IA (1.21.2 C) | sem índice no Worker do Capitão |
| CSP por cabeçalho (1.24) | o GitHub Pages não manda cabeçalho |
| Revisão de segurança digital na agenda (1.24) | tarefa do Access e do token do coletor do Avanti |
| Backup semanal, Actions, harness Node, vídeo (1.19–1.24) | infraestrutura do Avanti; esta máquina não tem Node |
| Editar e excluir registro do diário (1.16) | trava §2.9; vai adaptado (§6.2) |

## 5. CONVERSA lado a lado

Capturas nos 4 estados, web (`Main`, 1440×900) e app (`H2`, 390×844), com microfone e fala simulados como no `chat_ia.py`, fora do repositório (`$TEMP/paridade-avanti/capturas/folha-web.png`, `folha-app.png` e 36 imagens). O Avanti foi servido em `127.0.0.1:8790`, com o SW bloqueado e todo pedido fora de 8790 abortado (o React dele é local), e sessão injetada sem senha.

| Elemento | Avanti 1.24.0 | Capitão 1.0.0 (Avanti 1.4.6 portado) | Capitão 1.0.9 (hoje) |
|---|---|---|---|
| Camada | `.avz` em tela cheia, vidro quase preto | `.cpz`, vidro #050816 | `.cpz` |
| Núcleo | SVG: anel externo com 72 marcas (180 s/volta), arcos (40 s, ao contrário), anel tracejado (30 s), espectro radial que acompanha a voz, colchetes de mira, núcleo com brilho; **marca do barco** no centro | igual, com 120 marcas e **"IA"** no gradiente da marca | rosto de partículas em canvas |
| Ouvindo | ciano · "ESCUTA ATIVA" · "TOQUE NO NÚCLEO PARA ENVIAR" | igual | igual, rosto respirando |
| Pensando | violeta · anéis aceleram (8 s / 6 s) · "CRUZANDO TELEMETRIA · AGENDA · DOCUMENTOS…" · fica até 35 s (`fica`) | igual, some em 2,5 s (o `segura` veio depois) | neurônios violeta; `segura` até a fala |
| Falando | azul · nome do app · legenda · "TOQUE NO NÚCLEO PARA INTERROMPER" | igual ("CAPITÃO IA") | boca com ondas ciano→magenta, só com som |
| Encerrar | "✕ ENCERRAR" e Esc; some e volta ao chat | igual | igual |
| HUD | "<marca> · NÚCLEO IA / MODO / SINAL"; hora e última posição | "CAPITÃO IA · NÚCLEO"; hora, posição e "DEMO · hh:mm" | igual à 1.0.0 |
| SOS | canto, por cima | igual | igual |
| Gestos | toque no núcleo envia e interrompe | igual | igual |
| Carregamento | camada montada no 1º uso | igual | rosto carregado no ocioso e aquecido |
| Conversa (lógica) | sem a pausa de 0,65 s (F19); contexto (F18); registro pela conversa (F17) | com a pausa | com a pausa; IA na conversa (1.0.5) |

**Proposta para a Fase 5 (decisão a):**
- O núcleo da 1.24.0 desenhado em `<canvas>`, porque o teste barra `svg circle`: os 3 anéis, o espectro (que reage ao `som` e ao `pulso`), os colchetes e o brilho, com as velocidades e a aceleração no pensando.
- Cores ESCUTA #00F4FD, PROCESSANDO #A22BFD, RESPOSTA #00A1FE.
- No centro, o **∞ WonderHUB** (a marca no centro, como no Avanti).
- O `capitao-rosto.js` sai do CORE e o arquivo novo do núcleo ganha a conferência offline.
- O contrato `.cpz` fica (o `capitao-app.js` depende dele).

## 6. Pontos confirmados pelo proprietário (22/10/2026: "ok nas 5 propostas")

1. **Quando portar.** O PROMPT põe o port na Fase 0b, antes das Fases 1–6. Mas 29 das 34 funções dependem do que as Fases 1–6 fazem: dados gerados, replay, reescrita do cérebro, das telas, da CONVERSA e dos Workers (alertas, gráficos, sensores, checklists, FAQ, tendências…).
   **Aprovado:** a Fase 0b porta só as independentes (F01, F03, F13, F19, F25). Cada uma das outras entra na fase indicada na §3, com o mesmo commit próprio e o mesmo teste.
2. **Editar e excluir no Diário** contraria a trava §2.9. **Aprovado:** ✎ grava uma linha de correção ("corrige a linha de hh:mm: …"), 🗑 grava uma linha de anulação, e a tela mostra só a versão vigente com "corrigido"/"anulado". Nada some do registro.
3. **Centro do núcleo:** **aprovado o ∞ WonderHUB** (não o "IA" da 1.0.0).
4. **Branch.** O PROMPT manda trabalhar na `claude/trusting-feynman-n6z7gt` (PR #12). Esta sessão foi aberta na `claude/relaxed-newton-rpb40c` e só avançou localmente até ela. **Aprovado:** commits e push na `claude/trusting-feynman-n6z7gt` (PR #12) desde o commit desta PARIDADE.md.
5. **Escopo:** **aprovadas as 34 funções** (§3), sem corte.

**Achado para a Fase 1 (§2.10):** o Capitão 1.0.9 já usa o **mesmo modelo de rádio VHF do Avanti** (51 linhas: telas do SOS, Início, guia de eletrônicos, dados e gerador). O gerador troca na Fase 1. A lista de modelos do Avanti para essa conferência está fora do repositório (`$TEMP/paridade-avanti/modelos-avanti.txt`, 23 modelos).

## 7. Linha de base (1.0.9, `e5a3752`, antes de qualquer edição)

Ambiente: contêiner Linux na nuvem, não a máquina Windows. Chromium do Playwright no lugar do Edge (shim fora do repositório). A rede bloqueia `unpkg.com` e `open-meteo.com`; o React e o Babel vieram do registro npm com o mesmo SRI (F01 resolve isso de vez).

| Teste | Resultado | Observação |
|---|---|---|
| `cerebro.py` | **69 perguntas · 0 falhas** | diário: 1 linha (só o comando explícito); ficha 9.170 letras |
| `worker_ia.py` | **92 conferências · 0 falhas** | |
| `chat_ia.py` | **74 conferências · 2 falhas** | as 2 = "sem erro de script" em Main e H2: `Failed to load resource` de `api.open-meteo.com` e `marine-api.open-meteo.com`, bloqueados pela rede deste contêiner. Não é código |
| `verificar.py Main H2-Home-Mobile S1-SOS-Web login --offline` | **41 verificações · 0 falhas** | com o SW roteado (`PW_EXPERIMENTAL_SERVICE_WORKER_NETWORK_EVENTS=1`) |
| `publicacao.py` (depois de `git fetch`) | **7 conferências · 0 falhas** | cenário 1 pulado: `origin/main` já é a 1.0.9 desta árvore |

## 8. Valores do Avanti

A lista de valores do Avanti existe fora do repositório (`$TEMP/paridade-avanti/valores.txt`, 59 itens: nome e casco, MMSI, indicativo, inscrição, HIN, Hex ID, séries, URLs, hashes, nomes de pessoas e empresas, lugares). `git grep -n -i -F -f` com ela dá **0** na árvore atual.

## 9. Decisão (e): o que o Claude escolheu na Fase 1 (barco, registro, rota)

A decisão (e) do `CLAUDE.md` deixa o barco, o registro e a rota para o Claude, com a lista aqui. Nenhuma escolha repete valor ou modelo do Avanti: o gerador confere por substring contra as duas listas privadas e contra a pasta do Avanti (só contagens; ver o §8), e o `git grep` das listas na árvore dá 0. Fonte dos números: `ferramentas/demo/gerar_demo.py` (o `CONTRATO-DADOS.md` §2 e §8 têm o porquê de cada um).

### 9.1 Escolhas (para conferência)

| Item | Escolha |
|---|---|
| Barco | Estaleiro Marévia · Marévia 40 HT · 2023 (marca fictícia, sem colisão) |
| Dimensões | 12,40 m · boca 3,95 m · calado 1,10 m · 9,3 t métricas · tanques 2 × 800 L de diesel, 400 L de água, 100 + 100 L de servidas |
| Lotação / a bordo | 12 / 4 |
| Registro | CIA-23-0417 (= número do TIE; nunca no SOS) |
| MMSI / indicativo | 710123456 só nos lugares do §2.2 do PROMPT (Embarcação, Documentos, F3 «MMSI (cadastro do app)», `## Embarcação` e a 2ª linha da rota `mmsi`) / indicativo nunca gerado |
| Motores | 2 × Cummins QSB6.7 305 (eixo) |
| Gerador | Onan QD 9 (9 kW, 60 Hz) |
| Estabilizador | Seakeeper 3 (12 V DC, no banco de 12 V; sem números do fabricante no guia; exceção de contagem aprovada, ponto 9 abaixo) |
| Climatização | Webasto FCF Platinum 16000 + 2 × 12000 |
| Plotters / radar | Garmin GPSMAP 1243xsv ×2 / Garmin GMR 24 xHD3 |
| Áudio / VHF | Fusion MS-UD755 / Icom IC-M510 + IC-M37 (troca do rádio que o 1.0.9 tinha em comum com o Avanti) |
| EPIRB / incêndio | Ocean Signal SafeSea E100G / Seafire FD 300M (fabricante, modelo e validade só em Equipamentos, Leme e Documentos; nos guias e no SOS, só o procedimento padrão) |
| Dessalinizador / bombas / guincho | Schenker Zen 30 / Rule 2000 (24 V) ×2 / Lewmar V2 + AA150 |
| Piloto / AIS | Raymarine Evolution (EV-1 · ACU-400) / em-trak B954 |
| Baterias | Victron Energy AGM Super Cycle 12 V 230 Ah ×8 (serviço 24 V, partida 24 V, 12 V) |
| Base e rota | 19 circuitos por dia, fator 0,9866 · Barra Sul (saída do Rio Camboriú) → Ilha das Cabras → Ponta das Laranjeiras → Taquaras → Estaleirinho → Praia do Pinho → Laranjeiras → Ilha das Cabras → base; circuito de 16,17 mn. Os pontos e as 8 pernas passaram pelo portão manual do C8 contra a costa (0 amostras em terra); a rota só existe na simulação, **nunca no SOS** |

A rota do contrato (15,42 mn, fator 0,9407) mudou no portão manual: os pontos do contrato cortavam terra, foram movidos para o mar e o circuito ficou mais longo. Circuito, fator, velocidade média, COG, ETA e `destino_mn` do §1.22 do contrato são, por isso, os do `D.rota` gerado (os números do contrato ficam históricos; entram nos documentos pendentes da Fase 8).

### 9.2 Pontos do §8.2 do contrato: resolvidos pelo orquestrador com a proposta do contrato

| # | Ponto | Decisão | Como ficou |
|---|---|---|---|
| 1 | Códigos de alarme do Seakeeper | resolvido pelo orquestrador com a proposta do contrato: mensagens do display e o que fazer, sem código numérico | `g_seakeeper` §6 · Alarmes lista quatro mensagens com a providência de cada uma e manda anotar a mensagem e o código no diário; nenhum número de manual do fabricante |
| 2 | Emenda do `termos.json` (câmbio do rádio no DINHEIRO e `sea-?fire` no LOCAL_SEGURANCA) | resolvido pelo orquestrador com a proposta do contrato | Entrou antes do C3 (commit «Termos: câmbio do rádio e grafia Sea-Fire», com as revisões); `testes/proibidos.json` e `proibidos-casos.json` são cópias iguais do `termos.json` e do `termos-casos.json` (134 casos: 91 que barram e 43 que passam) |
| 3 | Grafia «Seafire» (sem hífen) em todo dado | resolvido pelo orquestrador com a proposta do contrato | asserção `GRAFIA_SEAFIRE` (valor, chave e nome de arquivo; a exceção é só `equipamentos[].palavras[]`, o vocabulário do ditado) |
| 4 | Motores: Cummins no lugar da marca de hoje | resolvido pelo orquestrador com a proposta do contrato | 2 × Cummins QSB6.7 305, coerente com 2.050 rpm a 18 nós; os textos fixos «Volvo Penta» do cérebro, da C3 e da G4 saem nas Fases 3 e 4 (contrato §6.6) |
| 5 | Piloto de fabricante diferente do dos plotters | resolvido pelo orquestrador com a proposta do contrato | Raymarine Evolution (EV-1 · ACU-400): direção hidráulica pede piloto hidráulico |
| 6 | `porao-teste` como tarefa de segurança | resolvido pelo orquestrador com a proposta do contrato | `agenda[porao-teste].seguranca: true`; o item s12 do checklist («Nenhuma tarefa de segurança atrasada») fica pendente enquanto o teste estiver atrasado. A asserção `AGENDA` limita `seguranca` a `epirb-teste`, `seafire-inspecao` e `porao-teste` |
| 7 | 19 circuitos por dia, posição abaixo do SOG | resolvido pelo orquestrador com a proposta do contrato (aceitar, ou alongar o circuito no portão manual se a carta pedir) | A carta pediu: 19 circuitos mantidos, circuito alongado para 16,17 mn e fator 0,9866 (a posição anda 1,3 % abaixo do que o odômetro soma). `gcd(19, 576) = 1`, então nenhuma chegada cai numa emenda de 150 s (`EMENDA_ROTA`) |
| 8 | FAQ sem o chip de confiabilidade nem os anexos de decisões e divergências | resolvido pelo orquestrador com a proposta do contrato | `faq-equipamentos.json` com 91 itens, todos vindos do guia de bordo gerado; a asserção `FAQ` reprova `conf`, `edicao`, `origem`, `selos`, `decisoes`, `limites`, `lacunas`, `divergencias`, `alertas` e `invalidos` |
| 9 | Estabilizador Seakeeper 3 (1 ocorrência por substring na pasta do Avanti) | resolvido pelo orquestrador com a proposta do contrato (aceitar, depois de conferir na web) | Conferido de novo em 28/10/2026 por busca na web (listagem da Twin Disc e matéria da Motor Boat & Yachting): o modelo é para barcos de 10,5 a 12,5 m (35 a 41 pés), é só 12 V DC e a rotação nominal é 8.450 rpm; o limite de peso («até cerca de 10,5 t») só aparece em blog de terceiros. O barco de 12,40 m e 9,3 t métricas cabe nas duas leituras e o volante do laço (~8.420 rpm) fica abaixo da nominal. Fica. `EXCECOES_MODELO = {'Seakeeper 3': 1}` na `COLISAO_MODELOS`; o modelo não está nas listas privadas |
| 10 | Linha do SOS no diário sem `sim` | resolvido pelo orquestrador com a proposta do contrato (pela trava §2.1) | Vale na 1b e na Fase 7: `addDiario` e a microtarefa do rodapé não leem `D.simulacao` em `/SOS-/`; com `simulacao: false`, um MAYDAY ou MOB gravado no aparelho de apresentação não vira «apresentação» nem sai da ficha |

**Não está entre os 10 e continua em aberto:** o ponto 11 do §8.2 do contrato (tokens a mais na lista `SOS` da 1b: «alguém caiu», «tripulante ao mar», «sem governo», «fazendo água», «leme travou» e as outras frases de queda e de perda de governo). Sem o ok do proprietário, a frase continua valendo como está (vai à IA, sem trecho local). Decidir antes da Fase 1b.

## Andamento

**Fase 0 — diagnóstico e paridade**
- [x] Linha de base na 1.0.9 (5 testes; 2 falhas de rede do contêiner no `chat_ia.py`)
- [x] Versão do Avanti: 1.24.0 (o 1º zip, anterior à 1.4.6, foi descartado)
- [x] Comparação com `867791b` e com a 1.0.9; tabela de paridade; 34 funções novas; 22 de fora
- [x] CONVERSA lado a lado (Avanti 1.24.0 × Capitão 1.0.0 × 1.0.9)
- [x] Valores e modelos do Avanti fora do repositório; `git grep` = 0
- [x] **Ok do proprietário** na tabela e nos 5 pontos da §6 (22/10/2026)

**Fase 0b — port (aprovado §6.1: só as independentes)**
- [x] F01 React do próprio site · [x] F03 ícones dos atalhos · [x] F13 vento e rajada · [x] F19 conversa sem pausa · [x] F25 dados do aparelho
  (cada função com implementação, testes e revisão independente em duas lentes, até 3 rodadas; 22/10/2026)
- **Exceção à decisão (h), para conferência do proprietário:** o `support.js` é o do Avanti 1.24.0 **mais uma reserva do Capitão**
  no `loadReactUmd` (≈ 10 linhas marcadas "só do Capitão"): se a cópia local do React falhar, ele sai do endereço do unpkg com o mesmo
  SRI. Motivo, reproduzido pelo revisor: o SW da 1.0.x guarda arquivo por arquivo; se a conexão cai logo depois do `support.js` novo,
  o cache fica sem o `assets/vendor` e, offline, nem o SOS abriria. Com a reserva, abre (contraprova nos testes `publicacao.py` 5 e
  `verificar.py` "reserva do React"). Sem ela, a saída seria lançar em 2 passos. Numa troca futura do runtime inteiro, a reserva tem
  de ser reposta (o teste acusa).
- `.gitattributes` com `assets/vendor/** -text`: no Windows com `core.autocrlf=true`, o fim de linha mudaria os bytes do React e o SRI
  não bateria nos testes locais.
- Documentação que ficou desatualizada: lista por função em `DOCS-PENDENTES.md` (entra na Fase 8).

**Fase 1 — gerador e dados completos** (commits locais C1–C12, sem push: a Fase 1 vai para o remoto junto com a 1b, contrato §6.6)
- [x] Passo 0: commit só do `CLAUDE.md` com a Decisão 1.1.0 (`CLAUDE.md: decisão do proprietário 1.1.0`)
- [x] Flags `simulacao: True`, `demo: False`, sem selo; `USUARIOS` e login (k) no mesmo commit (C1, `Flags 1.1.0, convidado (k) e selos`)
- [x] Embarcação, equipamentos (+6, nenhum modelo do Avanti: sai o rádio VHF), guias, `g_seafire`, `g_epirb`, `MMSI_RADIO` (C2 a C6: rótulos fora dos títulos, `--saida`/determinismo/`confere()`, embarcação e registro, equipamentos/modelos/guias, protocolos)
- [x] Prazos relativos + rebase no rodapé do `capitao-dados.js` (C7, `ferramentas/demo/rodape.js`)
- [x] Histórico (séries da F07), ROTA, `D.replay`; FAQ gerado (F10), itens dos checklists (F09), peças (F22), posições dos sensores (F08) (C8 a C11)
- [x] Fontes do Drive sem rótulo; determinismo provado (2 rodadas e a árvore sem diferença); lista da decisão (e) nesta PARIDADE.md (§9.1) e os 10 pontos do §8.2 do contrato, resolvidos pelo orquestrador com a proposta do contrato (§9.2) (C12)
- [x] A varredura de termos (as 8 regex do `termos.json`) **reprova o gerador** desde o C12; a única exceção é `embarcacao.mmsiNota`, que sai na 1b
- Fica para as fases seguintes (contrato §6.6): a 1b (SOS fora da simulação, `mmsiNota`, ponto 11 do §8.2) e, nas Fases 2 a 4, os leitores que ainda leem a forma antiga (L); a documentação (README, Manual, Guia e PDF, `CLAUDE.md`) é da Fase 8 (`DOCS-PENDENTES.md`).

**Fase 1b — SOS fora da simulação**
- [ ] S1/S2: GPS do aparelho, `MMSI_RADIO`, sem REG/selo/snapshot, clima só real; F04 (grava só na ação)
- [x] Cérebro (commit «SOS fora da simulação (Fase 1b): cérebro de emergência»): `SOS_PASSOS`/`sos`/`canal16`/`epirb`/`seafire`/`oleo` leem só o `D.protocolos` (MMSI do rádio de bordo, indicativo da Licença, Seafire e EPIRB no procedimento padrão com a etiqueta; sem leitura do quadro); rota `salvatagem`; lista `SOS` ampliada (PROMPT §2.3 + as frases da revisão do C5 + o subconjunto do §8.2 item 11, sem «sem governo» e «água subindo»); `baliza disparou` e `disparador hidrostático` na rota `epirb` (não na `SOS`: o certificado do EPIRB da G1 tem «disparador hidrostático» e tem de seguir `docsvenc`); o sistema fixo que disparou ou descarregou é a rota `seafire`; `SINONIMOS` baliza/testar; ficha sem fabricante e modelo de EPIRB e Seafire, `docsvenc` sem a data do `doc-epirb`; `S` vazio em `/SOS-/`; as listas do cérebro iguais às do gerador (testadas)
- [ ] Conferência Playwright + `verificar.py S1-SOS-Web S2-SOS-Mobile --offline`

**Fase 2 — `capitao-replay.js`**
- [ ] API, âncora 07:00, eventos, congelamento, isolamento; `capitao-alertas.js` (F05) sobre os alarmes do replay
- [ ] Moldura em nós Text; `setState` só quando o texto muda; teste de desempenho

**Fase 3 — cérebro**
- [ ] `instante()`, `resumoAgora()`, VIVO generalizado; respostas sem rótulo; rotas novas; `foraBarco`; `sobreDados`
- [ ] F09–F12, F14–F18, F20, F22, F26, F31, F32, F36; voz; `ficha()`; `TERMOS`

**Fase 4 — telas**
- [ ] 35 telas + moldura + clima + index/login/manifest; F05–F09, F10 (F6), F11, F14, F15, F20–F24; telas novas A4, A5, C4 ×2, F6 ×2, `relatorio.html`; SOS no login

**Fase 5 — CONVERSA**
- [ ] F27: núcleo do Avanti em canvas (cores WonderHUB, ∞ no centro); contrato mantido; HUD vivo; falhas da IA silenciosas na simulação

**Fase 6 — IA na nuvem**
- [ ] `SISTEMA_SIMULACAO` + F29 e F30; filtro de saída e de coordenadas (Workers e cliente); passo a passo do Worker

**Fase 7 — testes**
- [ ] Quebras previstas por fase; `proibidos.py`; `replay.py`; F35; acréscimos no `cerebro.py`, `chat_ia.py`, `worker_ia.py` e `verificar.py`; grep final

**Fase 8 — versão, docs e PR**
- [ ] 1.1.0 em todos os lugares; README, Manual (slides das funções novas), Guia + PDF, integrações, `CLAUDE.md`; rodada final; PR #12
