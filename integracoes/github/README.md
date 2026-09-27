# GitHub — repositório e publicação

- **Repositório:** `wonderboat-ai/CapitaoIA_v2` (público).
- **Site:** GitHub Pages, `main` › `/ (root)` → **`https://v2.capitaoia.com.br/`** (arquivo `CNAME`; o endereço antigo `https://wonderboat-ai.github.io/CapitaoIA_v2/` redireciona). `.nojekyll` publica os arquivos exatamente como estão. Nova versão no ar em 1 a 2 minutos.
- **Trabalho:** sempre em branch `claude/…`; merge na `main` **só quando o proprietário pedir** (publica o site na hora).
- **Sem build e sem GitHub Actions:** HTML, JS e JSON servidos como estão. O PDF do Guia rápido é gerado localmente (Playwright, `page.pdf`, A4).
- **Público:** repositório e site. Por isso nada de contratos, NF, CPF/CNPJ, telefones, e-mails, valores, nomes de terceiros, chaves, IDs do Drive ou link público da telemetria. Commits assinados com o e-mail *noreply* do GitHub.

## Para publicar pela primeira vez

1. Merge da branch na `main` (quando o proprietário pedir).
2. GitHub › Settings › Pages › Deploy from a branch › `main` · `/ (root)` › Save.
3. Domínio próprio: `v2.capitaoia.com.br` (CNAME no Registro.br + arquivo `CNAME` no repositório) — ver [cloudflare/](../cloudflare/README.md#domínio-v2capitaoiacombr).

## Planejado: repositório privado

Junto com o login no servidor. Pages a partir de repositório privado depende do plano da conta, e o site publicado pode continuar público — tornar o repositório privado não protege o site sozinho. Se o endereço do site mudar, atualizar o arquivo `CNAME`, `ORIGENS` em todos os `wrangler.toml` e `worker.js` (`PADRAO_ORIGENS`), o `PUBLICADO` do `capitao-auth.js` e o `HOSTS` do `capitao-app.js`.
