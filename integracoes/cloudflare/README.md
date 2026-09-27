# Cloudflare — Workers (borda) e Access (login no servidor)

## Workers do projeto (todos desligados)

| Worker | Pasta | Status | Segredos | Variáveis |
|---|---|---|---|---|
| `capitao-telemetria` | `integracoes/telemetria-worker/` | preparado · desligado | `GOOGLE_SA_KEY`, `CHAVE_APP`, `DRIVE_FILE_ID` | `GOOGLE_SA_EMAIL`, `ORIGENS` |
| `capitao-ia` | `integracoes/claude-api/ia-worker/` | estrutura · desligado | `ANTHROPIC_API_KEY`, `CHAVE_APP` | `MODELO`, `ESFORCO`, `ORIGENS` |
| `capitao-voz` | `integracoes/elevenlabs/voz-worker/` | estrutura · opcional | `ELEVENLABS_API_KEY`, `CHAVE_APP` | `ELEVENLABS_VOICE_ID`, `MODELO`, `ORIGENS` |

Padrão comum:

- `ORIGENS` — só o site publicado (`https://wonderboat-ai.github.io` e, quando o domínio existir, `https://www.xn--capitoia-vza.com.br` = www.capitãoia.com.br); outra origem → `403`.
- `CHAVE_APP` — cabeçalho `X-Capitao-Chave`, comparação em tempo constante; errada → `401`. Cada Worker com a sua chave.
- **Freio por IP** em memória (telemetria 120/min, IA 30/min, voz 30/min) → `429`. Não substitui o limite de gasto de cada serviço.
- CORS explícito (`Access-Control-Allow-Origin` = a origem aceita, `Vary: Origin`), preflight `OPTIONS` → `204`; respostas com `Cache-Control: no-store`.
- Segredos com `npx wrangler secret put …`; variáveis no `[vars]` do `wrangler.toml`. Publicar com `npx wrangler deploy` dentro da pasta. Conta grátis atende.
- No app, cada módulo vem com `URL_PROXY = ''` e cai no dado local em erro, demora ou sem internet.

## Access — login no servidor (planejado)

Pré-requisito para telemetria ao vivo, documentos sensíveis e IA sobre eles. Pontos a decidir:

- O Access protege endereços que passam pela Cloudflare. `*.github.io` não passa — o site precisaria ser servido por um domínio na Cloudflare (ex.: www.capitãoia.com.br com proxy, ou Cloudflare Pages). Conferir na documentação da Cloudflare ao decidir.
- Com o repositório público, o código continua legível no GitHub mesmo com o site protegido.
- Com login no servidor, o `login.html` atual (hash PBKDF2 no navegador, "porta de entrada") pode virar só a identificação do usuário (nome no chat e no diário).
- Os Workers podem continuar exigindo `CHAVE_APP` ou passar a aceitar a identidade do Access.

## Domínio www.capitãoia.com.br

Em 26/09/2026 o nome `xn--capitoia-vza.com.br` **não existia no DNS**. Por isso o repositório **não** tem arquivo `CNAME` (com ele, o GitHub redirecionaria o site para um domínio que não responde). Quando o domínio estiver registrado: apontar `www` (CNAME) para `wonderboat-ai.github.io`, configurar em GitHub › Settings › Pages › Custom domain e então incluir o `CNAME` no repositório.
