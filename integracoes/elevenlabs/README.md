# ElevenLabs · voz em nuvem — OPCIONAL (estrutura, desligada)

Hoje o Capitão IA fala com **a voz do próprio aparelho** (Web Speech): grátis, sem chave, funciona offline. A voz em nuvem é opcional e não está ligada.

| Arquivo | O que é |
|---|---|
| `voz-worker/worker.js` | Proxy `capitao-voz` (Cloudflare Worker). `ORIGENS` + `CHAVE_APP` (`X-Capitao-Chave`) + 30 falas/min por IP + texto até 1.200 letras. A chave do ElevenLabs fica só como segredo. |
| `voz-worker/wrangler.toml` | `ELEVENLABS_VOICE_ID` (vazio), `MODELO`, `ORIGENS`. |
| `cliente/capitao-voz-nuvem.js` | Lado do app, não carregado. `CapitaoVozNuvem.falar(texto)` → `true` se tocou; `false` → a tela usa `CapitaoBrain.speak`. |

## Regras

- Chave nunca no aparelho nem no repositório (só no Worker).
- Falhou, demorou (> 9 s) ou sem internet → voz do aparelho, sem perder a resposta.
- Velocidade **1,15x**, igual à voz do aparelho (`speed` no Worker; a ElevenLabs aceita de 0,7 a 1,2).
- **Emergência sempre na voz do aparelho** (funciona offline; não depende de terceiros).
- Voz clonada só com **consentimento por escrito** de quem grava. Sem voz definida: SEM DADOS (escolha do proprietário).

## Para ligar (decisão do proprietário)

1. Escolher a voz (Voice Library pt-BR ou clone com consentimento) e copiar o **Voice ID**.
2. `voz-worker/`: `npx wrangler secret put ELEVENLABS_API_KEY` · `npx wrangler secret put CHAVE_APP` · preencher `ELEVENLABS_VOICE_ID` · `npx wrangler deploy`. Definir limite de gasto no ElevenLabs.
3. Copiar `cliente/capitao-voz-nuvem.js` para a raiz, pôr a URL em `URL_PROXY`, carregar nas telas de chat e, no `speakAndResume` das telas, tentar `CapitaoVozNuvem.falar(texto)` antes de `CapitaoBrain.speak` (fora de emergência). Adicionar em `CORE` do `sw.js` e lançar versão.
4. Em cada aparelho: abrir uma vez com `#voz=<CHAVE_APP>`; `#voz=sair` apaga.
