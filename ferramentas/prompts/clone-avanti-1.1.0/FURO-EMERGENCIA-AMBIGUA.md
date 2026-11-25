# Furo estrutural de emergência ambígua — água, incêndio, saúde e colisão (tarefa #12)

Registro durável, no mesmo papel que o `RESIDUO-PESSOA-AO-MAR.md` tem para «pessoa ao mar». Interno; não faz parte do app. Escrito em 25/11/2026 sobre o commit `654d632` (branch `claude/relaxed-newton-rpb40c`, PR de rascunho #13). Números das medições de 22 a 24/11/2026 e do código; o versionado está na seção 9.

## Em uma frase

Antes do patch só «pessoa ao mar» tinha rede de segunda camada em `route()`. Relato ambíguo de água, incêndio, mal-estar ou colisão caía numa rota de dado ou de equipamento, levava o quadro de bordo e/ou liberava a IA na nuvem (15,38 % da matriz de 15.240 combinações; 69,90 % sem a instrução de segurança). O portão `riscoEmergAmbigua` (`654d632`) leva esse relato ao texto seguro: **dentro da amostra 15,38 % → 1,84 %; fora da amostra o ganho medido é de cerca de 28 %**, e 8,27 % do lacrado combinado com o FAQ ainda é perigoso. O furo está **fechado em parte, taxa aceita pelo proprietário em 25/11/2026**; não está «fechado». Só a taxa «perigosa» foi re-medida depois do portão: a «insegura» da base (69,90 %, que inclui os 54,52 % sem a instrução de segurança) não tem medida depois dele (seção 5). O relato ambíguo também não liga a janela de 15 minutos (seção 3, Limites).

## 1. Estado e decisões

| # | Decisão do proprietário | Estado |
| --- | --- | --- |
| 1 | Aceitar a taxa: ~28 % de redução realista em frase nova, com 8,27 % ainda perigoso no lacrado combinado com o FAQ | **Aceita em 25/11/2026** («aceito a taxa, atualiza todos os MDs e documentos essenciais») |
| 2 | Aceitar o limite da voz: a pergunta longa sem «?» ainda é lida como relato | Pendente |
| 3 | Autorizar ou não mexer no diário e na resposta de emergência na rodada 4 (toca a trava 14) | Pendente |
| 4 | Manter os 281 casos de «pessoa ao mar» como estão (domínio que o portão não toca) | Pendente |

- **Merge na `main`:** só quando o proprietário pedir; ele não pediu. A taxa é a decisão 1 de 4.
- **Fora das quatro decisões:** o relato ambíguo não liga a janela de 15 minutos (seção 3, Limites; seção 7, item 8). Não consta entre as decisões acima.
- **Versão:** o patch não lançou versão (`VERSAO` 1.1.0, `CACHE` do `sw.js` inalterado) e não toca Worker: só `capitao-brain.js`, `testes/cerebro.py`, dois arquivos de `testes/dados/` e o `CLAUDE.md`.
- **Antes do merge**, o proprietário confere o diff contra as listas privadas do Avanti, localmente.

## 2. O achado

**O que era.** `route()` só tinha uma rede de segunda camada, `risco(qRaw).n >= 1 → 'fallback'`, para «pessoa ao mar / sumida». Água, incêndio, mal-estar e colisão ou perda de governo dependiam só de `emergencia()` (a lista SOS e a `SOS_REGEX`), checada uma vez perto do topo. A frase ambígua que escapava dali caía direto numa rota comum («está cheirando a queimado forte» não bate «cheiro de queimado»; «tem água aqui» não bate «entrando agua»). A rota comum pode levar a «Situação de bordo agora» (SOG, proa, posição, ETA, pessoas a bordo) e `pedeIA()` pode devolver verdadeiro: o relato vai à IA na nuvem sem a instrução de segurança, o que a trava 10 proíbe nas rotas de emergência (aqui a emergência nem era reconhecida).

**Como apareceu.** Na rodada 2 do canal16 (`73fa6fc`, 22/11/2026; o candidato único foi descartado). Os itens VH-08 e VH-19 do FAQ não têm palavra de `CANAL16_ROTA`, então nunca passam por `cabecaEmerg()`; com uma cláusula ambígua junto, caíam em `fallback`/`posicao` com `pedeIA` verdadeiro e o quadro exposto, igual antes e depois do patch daquela rodada: o furo já existia. A estimativa inicial, 2 ids, foi trocada pela medida completa no `b7dc59f` (23/11/2026).

**Escala antes do patch** (matriz de 15.240 combinações, 100 % rodada): **69,90 % inseguras**, sendo 15,38 % as que vazam o quadro e/ou habilitam a IA e 54,52 % as que só não dão a instrução de segurança; 192 dos 254 ids do FAQ (75,6 %) têm pelo menos 1 combinação insegura; `risco()`/`pessoaPerdida()` falha em 51,6 % da mesma matriz. O `canal16` nunca falha (protegido por construção); o risco está em `fallback`, `ancora`, `posicao`, `telemetria`, `mare`, `clima` e nas 13 rotas de equipamento comuns. Com a rede mais madura do cérebro falhando em 51,6 %, fechar a classe por inteiro não cabe numa rodada.

**Decisão de risco.** O caminho principal de emergência não passa por esta rede: o SOS está em todas as telas, offline e sem login, e as rotas locais (`sos`, `canal16`, `epirb`, `seafire`, `salvatagem`, `mmsi`) respondem sem IA. Aqui é a rede secundária do chat e da voz, para o texto livre. Coordenadas não saem do aparelho (trava 14).

## 3. O que o portão faz

`riscoEmergAmbigua(qRaw)`, irmão de `risco()`, devolve `{ n: 1, cat }` para o relato reconhecido e `{ n: 0 }` para o resto.

**Desenho.** Quatro detectores (`ambAgua`, `ambIncendio`, `ambMedica`, `ambColisao`), nessa ordem. Cada um combina raízes de palavra (o que acontece) com o contexto (onde, em quê) e, quando a raiz sozinha é rotina, exige um sinal de anomalia («de repente», «demais», «sozinho»…), numa janela de poucas palavras, com guarda de rotina (tanque, chuva, marcha, piloto, atracação…) e negação. A base é léxica.

**Três pontos de ligação**, ao lado das linhas do `risco()`, que ficaram intactas:

| Ponto | O que faz |
| --- | --- |
| `route()` | depois de `risco(qRaw).n >= 1`, devolve `'fallback'` quando o portão acusa, antes das rotas que vazam o quadro (`ancora`, `posicao`, `telemetria`, `mare`, `clima`) e das de equipamento comuns |
| `responde()` | com a chave `fallback` e o portão acusando, troca o texto por `fallbackEmergenciaAmbigua(p)` |
| `pedeIA()` | devolve falso: a IA na nuvem nunca recebe o relato |

`perguntaEmerg()` também reconhece o relato: a frase e a resposta saem do histórico enviado à IA e encerram o contexto.

**O texto seguro**, um só para as quatro categorias: «Isso pode ser uma emergência de bordo (água, incêndio, saúde ou colisão): procedimento padrão — confirmar com o protocolo de bordo. Em caso de risco, abra o SOS.» Segue a forma do fallback da pessoa (botões «Abrir SOS» e «Registrar pendência», fonte do protocolo). Sem posição, rumo, SOG, ETA nem pessoas a bordo; sem IA; sem abrir a janela de 15 minutos (a consequência está nos Limites, abaixo).

**Não toca:** `cabecaEmerg`, `equipRota`, canal16, `mmsiRota`, `emergencia()`, `SOS`, `SOS_REGEX`, `risco()` e `riscoLargo()`. O único código original que mudou em `capitao-brain.js` é a linha que exporta `B` (ganhou `riscoEmergAmbigua`); as âncoras dos mutantes também ficaram intactas (a única âncora ausente na rodada de mutantes, seção 6, já faltava na base).

**Limites.** É lexical e a classe é aberta. Quando o portão acusa, a resposta não traz o quadro e a IA não entra; o que ele não acusa segue a rota comum e pode levar o quadro (seção 7). Nas medidas, o custo do portão é a resposta útil perdida nos falsos positivos, e na matriz de 15.240 ele não piorou nenhuma combinação (0 pioras). Cada cláusula (separada por pontuação) é avaliada à parte e o portão lê só as primeiras 1.200 letras. Não contam como relato a pergunta de procedimento («como/qual/quando/onde…», com «?» ou, no ditado, sem ele se tiver até 10 palavras e não disser «não sei por quê»), a negação e a hipótese com subjuntivo.

**Sem a janela de 15 minutos.** O texto seguro não liga a janela de conversa em emergência: `ABRE_JANELA` (`capitao-brain.js`) só vale para `sos`, `oleo`, `canal16`, `epirb` e `seafire`, e a resposta do portão não traz `abreJanela` (o nível 1 da pessoa, que dá a instrução do SOS sem janela, também não liga). Consequência, reproduzida em 25/11/2026 com os dados, o replay e o cérebro da árvore `654d632` (sem `capitao-app.js`, que é quem grava a marca da janela): `answer('tem água aqui')` devolve `fallback` com o texto seguro e `abreJanela` falso; `answer('qual a posição agora?')` logo depois, na mesma conversa, devolve `posicao`, com rumo, posição e SOG. O relato ambíguo não protege a pergunta de dado seguinte. O patch não introduz isso (antes dele também não havia janela), mas não estava registrado como limite. Mudar é decisão de produto: entra na rodada 4 (seção 10) só se o proprietário autorizar.

## 4. Como se mediu

**«Perigoso»** = `pedeIA` verdadeiro OU o texto traz o quadro (situação de bordo, SOG, proa, posição, ETA, pessoas a bordo, coordenada); a resposta da rota `autonomia` traz «a 18 nós», a velocidade de cruzeiro do cadastro e não o SOG (conferido em 25/11/2026), e, segundo o registro da medição, o `classif.py` da fase 1 não a conta como quadro; o `classif.py` não está versionado, então essa regra não é conferível pela árvore. **Falso positivo** = frase de rotina que recebe uma rota de emergência (`sos`, `canal16`, `epirb`, `seafire`, `salvatagem`, `mmsi`) ou o texto seguro; reproduz os 157 / 4,74 % da fase 1 (refeito em 25/11/2026, seção 5). Vale a decisão da pessoa ao mar: preferir o falso positivo.

Harness (não versionado): `answer()` e `pedeIA()` no Chrome real. A seção 5 compara a **base** (`b7dc59f`, sem o patch) com o **candidato** (o A da rodada 3, que é o `654d632`). A rodada 2 teve um candidato anterior, o C1, que só aparece num comentário de `testes/cerebro.py`. Os detalhes do harness, a divisão em braços de comparação e o guia de rótulos não estão na árvore e não foram conferidos; esta seção não os usa.

| Conjunto | Tamanho | O que mede | Versionado |
| --- | ---: | --- | --- |
| Matriz `emergencia-ambigua-matriz-20261123.txt` | 15.240 | 254 perguntas do FAQ × 5 categorias (água, incêndio, médica, colisão, pessoa ao mar) × 6 variações × 2 ordens; DENTRO da amostra (o vocabulário nasceu nela) | sim |
| Corpus natural `corpus-natural-bordo-20261123.txt` | 3.309 | falso positivo em rotina (FAQ sem emergência, arquivos de pessoa, `CASOS` do `cerebro.py`) | sim |
| HO-V1 e HO-V2 | — | conjuntos de cláusulas já vistos, usados na sintonia (a rodada em que nasceram não é conferível pela árvore); não medem generalização | não |
| **Lacrado** | 160 cláusulas | **fora da amostra**: escrito por agente que não viu o código; sozinho e combinado com 60 perguntas do FAQ × 2 ordens (160 × 60 × 2 = 19.200) | não |
| Falso positivo | vários | rotina lacrada (360), calor e falha, tema, perguntas, frases contra o portão | não |

## 5. Resultados

| Perigoso (base `b7dc59f`) | Base | Com o portão | Observação |
| --- | ---: | ---: | --- |
| Matriz de 15.240 (dentro da amostra) | 2.344 (15,38 %) | 281 (1,84 %) | os 281 são todos «pessoa ao mar»; água, incêndio, saúde e colisão = 0; 0 pioras |
| Lacrado, 160 cláusulas sozinhas | 83 | 59 (−28,9 %) | fora da amostra |
| Lacrado × FAQ × 2 ordens (19.200) | 2.200 (11,46 %) | 1.587 (8,27 %, −27,9 %) | fora da amostra |
| HO-V1 | 13,48 % | 6,02 % | usado na sintonia |
| HO-V2 | 17,69 % | 5,47 % | usado na sintonia |

**O ganho realista em frase nova é de cerca de 28 %**, não os 55 % a 69 % dos dois conjuntos de sintonia (HO-V1 55 %, HO-V2 69 %) nem os 88 % da matriz dentro da amostra; é a taxa aceita. As reduções relativas saem dos números da tabela: (13,48 − 6,02) ÷ 13,48 = 55 %; (17,69 − 5,47) ÷ 17,69 = 69 %; (2.344 − 281) ÷ 2.344 = 88 %.

**Falso positivo** (rotina que recebe o texto seguro, novos sobre a base): corpus natural 157 → 157 (4,74 %), 0 linhas mudaram; rotina lacrada de 360 frases +2 (0,56 %); calor e falha de rotina 0; tema 0,65 %; pergunta procedural com «?» 1,7 % e sem «?» 0; frases escritas de propósito contra o portão, de ~5 % a ~28 %.

**O que é o 4,74 %.** Na medição de 23/11/2026 (`b7dc59f`), os 157 do corpus natural foram atribuídos quase todos ao léxico que já existia e está documentado, inclusive o furo específico do `canal16`, medido contra os 254 itens do FAQ e não só contra os 41 de VH; essa atribuição é a da medição e não foi refeita. Refiz a contagem em 25/11/2026 no cérebro da árvore `654d632`: 157 das 3.309 frases recebem uma das seis rotas de emergência (156: `canal16` 62, `sos` 46, `epirb` 22, `salvatagem` 13, `seafire` 12, `mmsi` 1) ou o texto seguro (1, o da pessoa). Das 62 do `canal16`, 49 são perguntas ou variantes do FAQ. O portão acusa uma só frase do corpus, que já ia à rota `sos`: por isso nenhuma linha mudou.

**Só a taxa «perigosa» foi re-medida.** A taxa «insegura» da base (69,90 %: os 15,38 % perigosos mais os 54,52 % que só não dão a instrução de segurança) não tem medida depois do portão neste registro. Os números desta seção (15,38 % → 1,84 % e as linhas do lacrado) são da taxa «perigosa» e não podem ser lidos como queda dos 69,90 %.

## 6. Suíte e mutantes

**Suíte.** 0 falha nova comparando o log inteiro com o da base (112 linhas `FALHA`, 13 delas do instante, iguais nos dois). A base `b7dc59f` já tem o `cerebro.py` vermelho desde o `e8f50a2` (FAQ de 254 itens): a `main` (`b6e3225`) está verde, medido em 25/11/2026 (2.067 perguntas, 0 falhas, instante 0), de modo que este registro compara com a base e não com a `main`; `amb_emerg` sem falha; `p3f_rev2` 9/9 com `pedeIA` verdadeiro; `proibidos.py` 0 de resto. O candidato passou por 6 ou mais lentes adversariais e as medidas-chave foram refeitas. Não rodados nesta rodada: `gerador.py`, `verificar.py --offline`, `replay.py`, `rodape.py`, `publicacao.py`, `sos.py`, `worker_ia.py`; os que leem o cérebro rodaram na revisão, sem diferença para a base (`sos.py` 137/0; `gerador.py` OK). O `chat_ia.py` rodou inteiro em 25/11/2026 (416 conferências): na `main`, 2 falhas (as esperadas do Open-Meteo bloqueado); na branch, 4, as 2 esperadas mais 2 «desfazer» que eram asserção velha do teste (o `removeTarefa` grava linha de cancelamento desde o `c492944`); com a asserção ajustada em `testes/chat_ia.py`, 2 falhas, as esperadas.

**Mutantes.** Laço completo de `MUTANTES_3A`: 2.035 = 1.980 + 55 novos, em 4 fatias. **1.877 acusados** (os 55 novos, todos), **156 vácuos** (grupos que já falham igual na base sem o mutante: `p3c` 143, `p3f_rev2` 9, `p3f_relato` 3, `faq` 1), **1 vivo** («26.99 S 48.61 W» (decimal com hemisfério) não troca, grupo `janela`), **1 sem âncora** (o `semCoord` perde o par de CSV), 0 inválidos. Os dois já eram iguais na base; nenhum vem deste patch. Um mutante inválido (#2012) foi corrigido e acusado de novo.

## 7. Resíduo conhecido (rodada 4), em ordem de impacto

Exemplos conferidos em 25/11/2026 no cérebro da árvore `654d632`.

1. **Sinônimos fora das listas.** «tem um odor forte de queimado no camarote», «a água está esguichando pelo casco», «tem mar dentro do barco», «o barco está fazeno agua» (e «sentina»). Nos quatro primeiros, `n: 0`, todos vão à IA e três ou quatro levam o quadro no texto, conforme o instante do laço.
2. **Colisão sem verbo de impacto.** «a corrente estourou», «a âncora caiu sozinha». O portão devolve `n: 0` nas duas: `ambColisao` cala a cláusula que traz «corrente», «âncora», «ferro» ou «amarra» (a lista de guarda `CO_G`) e nenhuma lista de impacto tem «estourou» nem «caiu sozinha». A frase segue para a rota de assunto. A ordem de `route()` não é a causa: o portão vem antes de `ancora`, `mare` e `clima`. A primeira cai em `mare`: sem leitura de maré salva (a rede de teste), a resposta traz a linha «Situação de bordo agora: Navegando · SOG … · proa … · motores … rpm · diesel …», que é a decisão (g) do projeto (tempo e maré sem rede levam a situação de bordo), e é por isso que essas cláusulas contam no «perigoso» do lacrado; `clima` faz o mesmo; a segunda frase cai em `ancora`, que responde com a posição relativa e a profundidade. Nenhuma das três rotas traz a instrução de segurança. Segundo o lacrado (não versionado, não conferível pela árvore), quatro cláusulas dessas respondem por 19 % do perigoso lacrado e caem em `ancora`, `mare` ou `clima` pelo mesmo caminho.
3. **Saúde sem palavra do rol.** «ela está confusa», «o rosto dela ficou torto e a fala enrolando», «ele está com pressão no braço esquerdo», «ela não acorda». Nos quatro, `n: 0`, IA e quadro no texto.
4. **Perigo em pergunta ou hipótese curta.** «como pode ter água aqui embaixo» (descartada como pergunta, com ou sem «?») e «quando esquentar o painel sai cheiro de plástico» (descartada como hipótese). O inverso é a decisão 2: a pergunta longa sem «?» («como lanço a âncora aqui embaixo tá todo molhado não sei por quê») é lida como relato.
5. **Palavra de guarda que cala a cláusula inteira** (tanque, cozinha, âncora, rádio). «o piso está molhado e a água está minando perto do tanque» cai em `tanques` (`n: 0`); sem «perto do tanque» o portão acusa. Idem «sentimos uma pancada forte no casco quando soltamos a âncora» (rota `ancora`). Correção prevista: «cala só junto do sinal».
6. **Diário e ficha da IA.** «registre no diário: o piso está molhado» grava a nota e responde sem quadro e sem IA, mas sem a instrução de segurança; a nota entra depois na ficha que a IA lê. A foto com legenda de perigo também está no resíduo. Mexer nisto toca uma rota que grava registro (trava 14): decisão 3.
7. **Os 281 de «pessoa ao mar»** (domínio de `risco()`, não tocado: decisão 4). Exemplo, `pessoa_mar-1` da matriz: «Ele ficou bem quieto depois daquela onda forte que pegamos, nem parece ele.» Sozinha, ainda vai à IA e leva o quadro.
8. **O relato ambíguo não liga a janela de 15 minutos** (acrescentado em 25/11/2026, fora da ordem de impacto). Seção 3, Limites: depois do texto seguro, a pergunta de dado seguinte na mesma conversa devolve o quadro. Mudar isso é decisão de produto, fora das decisões 1 a 4.

## 8. Candidato B descartado

O candidato B («arquitetura de evidência») foi descartado: abre vazamento do quadro na entrada por voz (14 a 23 de 40 cláusulas fechadas voltam a ser perigosas com «como faço» na frente; o ditado não pontua); ganha só 4,7 pontos sobre o A no lacrado; e fechava o buraco do diário e da ficha (item 6), mas mexia numa rota que grava registro (trava 14), fora do escopo autorizado.

## 9. Como reproduzir e limites

**No repositório:**
- `testes/dados/emergencia-ambigua-matriz-20261123.txt`: 15.240 linhas de dados, mais 6 de comentário no topo (`wc -l` dá 15.246) (`frase`, `faq_id`, `categoria`, `variante`, `ordem`; sem nível esperado). Escala do furo, DENTRO da amostra do portão.
- `testes/dados/corpus-natural-bordo-20261123.txt`: 3.309 linhas de dados, mais 7 de comentário no topo (`wc -l` dá 3.316) (`frase`, `fonte`). Falso positivo em rotina.
- `testes/dados/amb-emerg-perigo.txt` (48 cláusulas, 12 por categoria) e `amb-emerg-rotina.txt` (95 frases): guarda de regressão do reconhecimento e do falso positivo.
- `testes/cerebro.py`: o grupo `amb_emerg` (em `GRUPOS_3A` e no conjunto padrão) e `MUTANTES_AMB` (55 mutantes).

O grupo `amb_emerg` exige: pelo menos 40 das 48 cláusulas de perigo reconhecidas e 9 por categoria (hoje 48 de 48, conferido em 25/11/2026); no máximo 3 das 95 frases de rotina com o texto seguro (hoje 0, conferido); as 576 combinações cláusula × pergunta de dado (6 × 2 × 48) com o texto seguro, sem quadro, sem as 8 regex de `TERMOS`, sem IA e sem janela; os 9 relatos do `p3f_rev2` com `pedeIA` verdadeiro; as fronteiras, o histórico e o desempenho. Sem opção de linha de comando para rodar só este grupo: ele roda dentro de `python -X utf8 testes/cerebro.py`, com a raiz servida em `127.0.0.1:8765` (ou `CAPITAO_BASE`).

**O teste `amb_emerg` é guarda de regressão por taxa e NÃO é medida de generalização** (está dito no próprio teste): os dois conjuntos pequenos nasceram junto do portão.

**Fora do repositório** (eram do scratchpad da sessão, efêmero, NÃO versionados): o harness (`run_rows.py`, `classif.py`), o lacrado de 160 cláusulas, HO-V1 e HO-V2, os conjuntos de falso positivo e as listas de ataque; sem eles, os números do lacrado e da sintonia não se reproduzem a partir da árvore. Um comentário em `capitao-brain.js` (acima de `ambNorm`) cita `emergencia-ambigua-holdout{,2,3}-20261123.txt` e `corpus-natural-hardneg` em `testes/dados/`, que não estão no repositório.

## 10. Critério de aceite por taxa e a rodada 4

**Critério.** Como no `RESIDUO-PESSOA-AO-MAR.md`, o aceite é por taxa, nunca por zero nem por contagem de achados: a classe é aberta e uma nova rodada adversarial sempre acha mais. O proprietário aceitou em 25/11/2026 a taxa («aceito a taxa, atualiza todos os MDs e documentos essenciais»): cerca de 28 % de redução fora da amostra, com 8,27 % do lacrado combinado com o FAQ ainda perigoso. Foi a única decisão que ele tomou (decisão 1 de 4). Fatos medidos, que a aceitação não cobre por si: o falso positivo do corpus natural ficou em 4,74 %, igual ao da base; este registro não fixa teto numérico para mudanças futuras, e os limites que existem estão no teste `amb_emerg`. A expectativa do agente é uma redução medida e reportada, priorizando a classe que vaza o quadro ou habilita a IA.

**A rodada 4, se autorizada, faria** (ordem de impacto, seção 7): (1) sinônimos e formas coloquiais fora das listas; (2) colisão sem verbo de impacto: ampliar o léxico e afrouxar a guarda `CO_G` de `ambColisao`, porque o portão já vem antes de `ancora`, `mare` e `clima` em `route()` e hoje devolve `n: 0` nessas frases (reordenar não resolve); (3) saúde com sinais fora do rol; (4) a guarda que cala só junto do sinal; (5) a pergunta e a hipótese curtas sem «?», pesando a decisão 2; (6) só com a decisão 3, o diário, a resposta de emergência e a ficha da IA; (7) os 281 de «pessoa ao mar» só com a decisão 4; (8) só se o proprietário autorizar, ligar a janela de 15 minutos ao texto seguro (seção 3, Limites; seção 7, item 8).

Proposta de aceite (do agente, não regra do proprietário): nenhuma falha nova contra o log inteiro da base; falso positivo do corpus natural sem piora sobre os 157; mutantes novos para cada mudança, todos acusados; um lacrado novo, porque o atual deixa de medir generalização se for usado para sintonizar.

A conferência contra as listas privadas de valores e de modelos do Avanti fica com o proprietário, localmente, antes do merge (seção 1); este documento não cita fabricante nem modelo de equipamento.
