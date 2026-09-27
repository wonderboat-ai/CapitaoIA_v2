# Claude API · IA na nuvem — ESTRUTURA (desligada)

Nada publicado, nenhuma tela chama. Hoje o chat e a voz respondem **só no aparelho**:
resposta pronta (`ANSWERS`) → trecho da base de bordo (`buscaBase`) → **SEM DADOS**.
A IA entra como **mais uma camada antes do SEM DADOS**, respondendo só com as fontes que o próprio app mandar. Ela **não substitui** as respostas prontas nem o SOS: emergência continua roteada no aparelho, offline.

## Arquivos

| Arquivo | O que é |
|---|---|
| `ia-worker/worker.js` | Proxy `capitao-ia` (Cloudflare Worker) com o SDK oficial `@anthropic-ai/sdk`. Chave da API só como segredo. `ORIGENS` + `CHAVE_APP` (`X-Capitao-Chave`) + freio de 30/min por IP. |
| `ia-worker/wrangler.toml` | `MODELO = "claude-opus-5"` (em variável), `ESFORCO` opcional, `ORIGENS`. |
| `ia-worker/package.json` | Dependência `@anthropic-ai/sdk` (o wrangler empacota no deploy). |
| `cliente/capitao-ia.js` | Lado do app. `URL_PROXY = ''` (desligado). `CapitaoIA.perguntar(pergunta, hits, contexto)` → `{ text, src, key: 'ia' }` ou `null`. |

## Contrato

**App → proxy** · `POST` · cabeçalho `X-Capitao-Chave: <CHAVE_APP>`

```json
{ "pergunta": "até 500 letras",
  "trechos": [{ "fonte": "Guia de bordo (DEMO) — Gerador Onan", "pag": null, "secao": "2 · Ligar", "texto": "…" }],
  "contexto": "leitura que a tela já mostra (snapshot ou ao vivo), até 2.000 letras" }
```

**Proxy → app** · `200 { "texto": "…\nFonte: …", "modelo": "claude-opus-5", "parou": "end_turn" }`
Erros: `401` chave · `403` origem · `422` recusada (toda a cadeia) · `429` limite · `500` configuração · `502` API/conexão. Qualquer erro → o app mantém a resposta local.

**Proxy → Claude API** (feito pelo SDK, `client.beta.messages.create`):
- `model` da variável `MODELO` (padrão `claude-opus-5`), `max_tokens: 16000`;
- `thinking: { type: "adaptive" }` (o modelo decide quanto pensar); `output_config.effort` só se `ESFORCO` estiver definido;
- **fallback de recusa no servidor:** `betas: ["server-side-fallback-2026-07-01"]` + `fallbacks: "default"` — se os classificadores de segurança recusarem, a própria API refaz o pedido no modelo reserva recomendado para aquela categoria, na mesma chamada. `stop_reason: "refusal"` no fim significa que a cadeia inteira recusou → `422` e o app fica com a resposta local;
- `system`: as regras do projeto em texto fixo com `cache_control` (entra no cache de prompt quando passa do mínimo do modelo);
- `messages`: trechos com a fonte + leitura atual + a pergunta por último.

## Regras que o proxy passa para a IA (do `CLAUDE.md`)

- Português do Brasil, direto; primeira linha = a resposta; nunca perguntar o óbvio. Emergência ignora a concisão.
- Só com os trechos e a leitura enviados. Sem fonte → **SEM DADOS** e onde buscar.
- Cita fabricante e modelo ("modelo SEM DADOS" quando não houver) e termina com `Fonte: …`.
- Estados honestos: SEM LEITURA · SEM DADOS · MANUAL NO DRIVE · A CONFERIR / A CONFIRMAR. Procedimento padrão continua rotulado "confirmar com o protocolo de bordo".
- Hierarquia quando as fontes divergem: manual oficial › registro oficial › laudo › diário › foto › nota informal.
- A IA nunca grava no diário.

## Para ligar (depois do login no servidor)

1. Console da Anthropic: criar a chave da API e **definir limite de gasto**.
2. Nesta pasta: `npm install` · `npx wrangler secret put ANTHROPIC_API_KEY` · `npx wrangler secret put CHAVE_APP` (chave longa aleatória, própria da IA) · `npx wrangler deploy`.
3. Copiar `cliente/capitao-ia.js` para a raiz, pôr o endereço do Worker em `URL_PROXY`, incluir `<script src="./capitao-ia.js"></script>` no `<helmet>` de `Main` e `H2-Home-Mobile` e adicionar `./capitao-ia.js` em `CORE` do `sw.js`.
4. Ponto de encaixe (nas telas de chat, no método `ask`): quando a chave da resposta for `fallback` (ou `base`, a decidir), chamar `CapitaoIA.perguntar(q, CapitaoBrain.buscaBase(q, 3), <leitura da tela>)` e, se vier resposta, trocar a mensagem. A voz continua usando `falaCurta`.
5. Em cada aparelho: abrir uma vez com `#ia=<CHAVE_APP>`. `#ia=sair` apaga.
6. Lançar versão (`VERSAO`, `CACHE`, tabela do README) e atualizar Manual e Guia rápido.

## Decisões em aberto

- Quais perguntas vão para a IA (só `fallback`, ou também `base`?).
- `ESFORCO`: medir custo e qualidade em perguntas reais antes de fixar.
- Foto e vídeo: hoje viram linha A CONFERIR no diário; análise de imagem pela IA não está definida.
- O que pode ir no `contexto` (posição do barco só depois do login no servidor).
