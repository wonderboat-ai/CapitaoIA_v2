# Google Cloud — conta de serviço (planejado)

Usada pelo proxy da telemetria (`integracoes/telemetria-worker/`) para ler o Drive **sem** link público.

1. Google Cloud › IAM › Contas de serviço: criar uma conta e gerar uma chave JSON.
2. No Drive, compartilhar **só o arquivo necessário** (o JSON do coletor) com o e-mail da conta, como **Leitor**.
3. `wrangler.toml`: `GOOGLE_SA_EMAIL` = e-mail da conta. Segredos: `npx wrangler secret put GOOGLE_SA_KEY` (a `private_key` do JSON) e `npx wrangler secret put DRIVE_FILE_ID`.
4. O JSON inteiro **nunca** vai para o repositório nem para o chat.

Como o Worker usa a conta (já implementado em `telemetria-worker/worker.js`):
JWT RS256 assinado com a chave (`iss` = e-mail, `scope` = `https://www.googleapis.com/auth/drive.readonly`, `aud` = `https://oauth2.googleapis.com/token`, 1 h)
→ troca por `access_token` → `GET https://www.googleapis.com/drive/v3/files/<ID>?alt=media` → tira campos internos → devolve ao app. Token guardado até 1 min antes de vencer.

## Reuso previsto

- A mesma conta pode ler outras pastas do `Drive › Capitão IA v2` quando os documentos sensíveis forem conectados (depois do login no servidor) — ver [google-drive/](../google-drive/README.md). Compartilhar pasta a pasta, sempre como Leitor.
- Alternativa não decidida: a Claude API também é oferecida no Google Cloud (Vertex AI), com cobrança na conta Google. O esqueleto em `integracoes/claude-api/` usa a API direta da Anthropic.
