# Resíduo da classe «pessoa ao mar / sumida» — fim da Fase 4 (grupo home)

Documento para o proprietário. Interno; não faz parte do app. Escrito em 13/11/2026, sobre o commit `700d9ea`.

## Em uma frase

Depois de 3 rodadas de correção e revisão adversarial por estrutura, a classe caiu de **88,70 %** para **9,24 %** de falha na matriz adversarial, sem nenhuma frase pior que no cérebro antigo. Restam **19 achados** (9 bloqueiam). A classe é **aberta** (o português tem formas ilimitadas de dizer «alguém sumiu»), então outra rodada adversarial sempre acha mais. A recomendação está no fim: parar a revisão aberta, aceitar um critério de taxa e decidir se vale uma passada curta e focada nos 5 bloqueios de falso negativo antes do merge na `main`.

## O que é a classe e o que vale como falha

A frase descreve pessoa em risco (caiu, sumiu, não aparece, não responde, ficou para trás) e a resposta tem de ser local: instrução do SOS, rota `sos` ou fallback seguro de pessoa, nunca a IA, nunca posição, rumo, SOG, ETA nem pessoas a bordo (trava 10 do `CLAUDE.md`), e com a janela de 15 min quando a pessoa está na água.

Na matriz, uma frase **falha** quando acontece qualquer um destes:
- a pergunta vai à IA (`pedeIA` verdadeiro);
- o texto traz a «Situação de bordo agora» (SOG, proa, posição, pessoas a bordo);
- a rota não é `sos` nem o fallback seguro de pessoa;
- é de pessoa na água e a janela de 15 min não abre.

**Falso positivo** (instrução do SOS onde a frase era rotina, como «o fornecedor sumiu») custa só a resposta local e a janela. **Falso negativo** (pessoa em risco que chega à IA com a situação de bordo) é o risco real. A decisão do projeto é preferir o falso positivo.

## Medida

Matriz adversarial montada pelo revisor da rodada 3 com texto novo: **58.929 frases** (872 substantivos e papéis em cinco classes: pessoa na água, pessoa sumida, busca, contagem e pronome). Rodada na plataforma app, replay fixo em 60 s, sem gravar (`commit:false`), contra quatro versões do `capitao-brain.js` com os mesmos dados:

| Versão do cérebro | Frases que falham | Taxa |
| --- | ---: | ---: |
| `f3b121c` (antes da revisão final do grupo home) | 52.268 | 88,70 % |
| `11fc4a7` (fim da 1ª instância, abordagem por lista) | 47.087 | 79,90 % |
| `3252324` (fim da rodada 2 por estrutura) | 7.930 | 13,46 % |
| `700d9ea` (HEAD, fim da rodada 3) | 5.446 | **9,24 %** |

- Frases que falham no HEAD e **não** falhavam no `f3b121c`: **0**. Frases que falhavam no `f3b121c` e passam no HEAD: 46.822. Em ambos: 5.446.
- Por classe no HEAD: pessoa na água 1.163/27.757 (4,19 %) · pessoa sumida 3.148/21.243 (14,82 %) · busca 987/4.524 (21,82 %) · contagem 144/5.361 (2,69 %) · pronome 4/44.
- **Concentração:** 4 quadros de sinal («não foi visto desde…», «ficou incomunicável», «o paradeiro é desconhecido», «alguém sabe onde X está?») respondem por **3.485 das 5.446** falhas (64 %), com cerca de 98 % de falha em cada quadro. É lacuna de **sinal**, não de vocabulário de pessoa: reproduz com «o Pedro», «meu filho», «a criança». Fechar esses quadros leva a matriz a perto de 3,3 %.
- **Limite da medida:** a matriz foi construída para achar furos, então 9,24 % é teto, não taxa de uso. Ela não mede falso positivo.
- **Falso positivo, corpus natural (1.341 frases de rotina, diferencial contra o `f3b121c`):** 86 frases (6,4 %) passam de resposta normal para o fallback seguro de pessoa. As maiores concentrações: marina 22 % (21/96), misto 17 %, ditado 11 %, contato 11 %.

## Os 19 achados que sobraram (rodada 3)

Texto completo, com a evidência e a correção proposta de cada um, em `RESIDUO-PESSOA-AO-MAR-achados.json` (mesma pasta; a numeração é a daqui). `$S` nesse arquivo é a pasta de trabalho temporária dos agentes, que não fica no repositório.

**Falso negativo — pessoa em risco chega à IA ou a dado (13; 5 bloqueiam)**
1. Bloqueia — sinal fora da tabela: «não foi visto/encontrado/localizado», «não se sabe do X», «ficou incomunicável», «paradeiro desconhecido», «em local incerto», «não deu sinal de vida», «onde será que X se meteu?», «alguém sabe onde X está?».
2. Bloqueia — «dar falta de X» com nome ou possessivo sem artigo («dei falta de Pedro»); com artigo («do Pedro») já fica local.
3. Bloqueia — pessoa com complemento de lugar ou organização («o Pedro da marina», «a dona da pousada», «os clientes do charter») com verbo fraco (arrastado, engoliu água).
13. Bloqueia — «está boiando» com cauda de dado («qual a posição?») devolve posição e SOG.
18. Bloqueia — papel ambíguo com complemento («o guia do mergulho não subiu», «o capitão da lancha sumiu») vira «coisa».
4, 5, 6, 14, 15, 16, 17, 19. Corrigir — «ficou no mar» sem janela com papel aberto; substantivos em -ando/-endo/-indo (mestrando); nome próprio em minúscula fora da lista; apuro sem substantivo («não respira», «está se debatendo»); pessoa esquecida em outra forma de frase; papel ambíguo («o capitão do barco»); vocativo com verbo em maiúscula; pedido de socorro em inglês (7 de 20 formas).

**Falso positivo — instrução do SOS onde era rotina (6; 4 bloqueiam)**
7. Bloqueia — ofício ou terceiro de terra com «sumiu» (fornecedor, mecânico, despachante, advogado) abre `sos` e a janela de 15 min, mesmo com contexto administrativo escrito.
8. Bloqueia — pessoa nomeada ou substantivo comum com «não atende/não responde/não apareceu» sem objeto abre `sos` e janela.
9. Bloqueia — «registre no diário que X não voltou/sumiu» grava a nota e liga a janela (14 de 72 na matriz; antes, 0).
10. Bloqueia — «sumiu da escala», «do grupo», «ficou para trás na escala/lista» abrem `sos` e janela.
11, 12. Corrigir — pergunta de equipe, contato, peça ou marina com contexto de terra explícito recebe a instrução do SOS; equipamento de mergulho («a roupa de mergulho sumiu») e equipe de mergulho em frase administrativa abrem `sos` e janela.

## Por que não insisti

Cada rodada com um revisor de vocabulário novo acha furos novos: 26 achados (12 bloqueiam) na rodada 1, 21 (9) na rodada 2, 19 (9) na rodada 3. A **contagem** não cai, mas a **taxa** cai a cada rodada (88,70 → 79,90 → 13,46 → 9,24 %). Como a classe é aberta, a contagem de achados não chega a zero; só uma meta de taxa em matriz fixa e em corpus natural fecha a conversa. Os ajustes do lado do falso negativo empurram frases para o lado do falso positivo e vice-versa; sem uma meta de taxa, cada rodada reabre o que a anterior fechou.

## Decisão de risco

- O caminho principal de emergência **não passa por esta rede**: o SOS está em todas as telas, funciona offline e sem login, e as rotas locais (`sos`, `canal16`, `epirb`, `seafire`, `salvatagem`, `mmsi`) respondem sem IA. A classe tratada aqui é a rede secundária do chat para quem descreve a emergência em texto livre.
- No pior caso dos 9,24 %, a frase vai à IA, que responde com a situação de bordo e sem a instrução de segurança, e a pergunta seguinte («qual a posição?») é respondida normalmente. Não há coordenada fora do aparelho (trava 14) nem alteração de registro.
- O custo do outro lado é só resposta local (a instrução do SOS e a janela de 15 min).

## Recomendação

1. **Aceitar este estado como base da Fase 4** e seguir para as Fases 5 a 8. As rodadas abertas param aqui.
2. **Antes do merge na `main`, autorizar uma passada curta e focada nos 5 bloqueios de falso negativo** (itens 1, 2, 3, 13 e 18), com os patches já descritos pelos revisores (tabela de sinais, «dar falta de», complemento de lugar, cauda de dado depois de «está boiando», papel ambíguo). Custo estimado: de 1,5 a 2 h e cerca de 0,6 M de tokens, sem rodada adversarial depois.
3. **Critério de aceite por taxa, não por contagem de achados:** matriz fixa de 58.929 frases com no máximo 3 % de falha; corpus natural de 1.341 frases com no máximo 5 % de falso positivo no mesmo diferencial; zero frases piores que o `f3b121c`. Esse critério vale também para qualquer mudança futura na classe.
4. **Os 4 bloqueios de falso positivo (7 a 10) são decisão de produto:** aceitar a instrução do SOS para ofício de terra e para «sumiu da escala/grupo» (seguro, mas incomoda quem só fala de rotina) ou pedir a passada para os dois lados. Como a regra do projeto prefere o falso positivo, a sugestão é aceitar e corrigir só o item 9 (o diário não deve ligar a janela).

Valores e modelos do Avanti: nenhum neste documento.
