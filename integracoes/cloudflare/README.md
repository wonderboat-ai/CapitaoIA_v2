# Cloudflare — Workers (borda) e Access (login no servidor)

## Workers do projeto (todos desligados)

| Worker | Pasta | Status | Segredos | Variáveis |
|---|---|---|---|---|
| `capitao-telemetria` | `integracoes/telemetria-worker/` | preparado · desligado | `GOOGLE_SA_KEY`, `CHAVE_APP`, `DRIVE_FILE_ID` | `GOOGLE_SA_EMAIL`, `ORIGENS` |
| `capitao-ia` (grátis) | `integracoes/workers-ai/ia-worker/` | estrutura · desligado | `CHAVE_APP` (sem chave de API: binding `AI`) | `MODELO`, `MAX_TOKENS`, `GATEWAY`, `ORIGENS` |
| `capitao-ia` (paga) | `integracoes/claude-api/ia-worker/` | estrutura · desligado | `ANTHROPIC_API_KEY`, `CHAVE_APP` | `MODELO`, `ESFORCO`, `ORIGENS` |
| `capitao-voz` | `integracoes/elevenlabs/voz-worker/` | estrutura · opcional | `ELEVENLABS_API_KEY`, `CHAVE_APP` | `ELEVENLABS_VOICE_ID`, `MODELO`, `ORIGENS` |

Padrão comum:

- `ORIGENS` — só o app: `https://v2.capitaoia.com.br`. O `wonderboat-ai.github.io` fica de fora (é dividido com os outros sites da conta). Outra origem → `403`.
- `CHAVE_APP` — cabeçalho `X-Capitao-Chave`, comparação em tempo constante; errada → `401`. Cada Worker com a sua chave.
- **Freio por IP** em memória (telemetria 120/min, IA 30/min, voz 30/min) → `429`. Não substitui o limite de gasto de cada serviço.
- CORS explícito (`Access-Control-Allow-Origin` = a origem aceita, `Vary: Origin`), preflight `OPTIONS` → `204`; respostas com `Cache-Control: no-store`.
- Segredos com `npx wrangler secret put …`; variáveis no `[vars]` do `wrangler.toml`. Publicar com `npx wrangler deploy` dentro da pasta. Conta grátis atende.
- No app, cada módulo vem com `URL_PROXY = ''` e cai no dado local em erro, demora ou sem internet.

## Access — login no servidor (planejado)

Pré-requisito para telemetria ao vivo, documentos sensíveis e IA sobre eles. Pontos a decidir:

- O Access protege endereços que passam pela Cloudflare. O app hoje é servido pelo GitHub Pages em v2.capitaoia.com.br, com DNS no Registro.br (não passa pela Cloudflare). Para o Access no site, o subdomínio precisaria passar pela Cloudflare (ou o app ir para Cloudflare Pages); nos Workers, o Access vale direto. Conferir na documentação da Cloudflare ao decidir.
- Com o repositório público, o código continua legível no GitHub mesmo com o site protegido.
- Com login no servidor, o `login.html` atual (hash PBKDF2 no navegador, "porta de entrada") pode virar só a identificação do usuário (nome no chat e no diário).
- Os Workers podem continuar exigindo `CHAVE_APP` ou passar a aceitar a identidade do Access.

## Domínio v2.capitaoia.com.br

- **DNS:** Registro.br (servidores `e.sec.dns.br` e `f.sec.dns.br`, zona em modo avançado). Registro do app: **CNAME `v2` → `wonderboat-ai.github.io`** (sem o nome do repositório).
- **Raiz `capitaoia.com.br`:** site de apresentação feito no Lovable (A `185.158.133.1` e TXT `_lovable`). **Não mexer.**
- **Verificação no GitHub** (contra takeover): **feita em 27/09/2026** — `capitaoia.com.br` verificado em https://github.com/settings/pages (Settings do **perfil**, não do repositório) com o TXT `_github-pages-challenge-wonderboat-ai`. **Manter o TXT.** Cobre os subdomínios imediatos, inclusive `v2` (API: `protected_domain_state: verified`).
- **Não mexer** no Custom domain em Settings › Pages do **repositório**: tem de ser `v2.capitaoia.com.br` (em 27/09 a raiz foi posta ali por engano e o app redirecionou para o site do Lovable por ~10 min).
- **No repositório:** arquivo `CNAME` na raiz com `v2.capitaoia.com.br` (publicação por branch). Se o arquivo sumir num push, o site sai do domínio.
- **HTTPS:** certificado Let's Encrypt emitido pelo GitHub em até 1 hora; depois, Settings › Pages › **Enforce HTTPS**. Não há registro CAA na zona (se um dia houver, incluir `letsencrypt.org`).
- **Endereço antigo:** `https://wonderboat-ai.github.io/CapitaoIA_v2/` redireciona para `https://v2.capitaoia.com.br/`.
- **Nunca** desligar o Pages nem apagar o repositório deixando o CNAME `v2` no DNS (risco de outra pessoa assumir o subdomínio): remover o registro junto.
