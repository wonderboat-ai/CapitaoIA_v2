# Integrações · Capitão IA

Estrutura para conectar o assistente a Cloudflare, Google (Cloud, Drive, Workspace), GitHub, Claude API e ElevenLabs.
**Tudo o que tem segredo vem desligado.** Nenhuma tela carrega arquivos desta pasta. O registro legível por máquina está em [`integracoes.json`](integracoes.json).

## Status (26/09/2026 · app 1.0.0)

| Integração | Status | Onde |
|---|---|---|
| GitHub Pages (hospedagem) | **ativo** (publica quando o proprietário pedir o merge) | [github/](github/README.md) |
| PWA / cache offline | **ativo** | `sw.js`, `manifest.webmanifest` |
| Open-Meteo (clima ECMWF, maré, geocoding) | **ativo** · sem chave | `capitao-clima.js` |
| windy.com | **ativo** · só link | `capitao-clima.js` |
| Voz do aparelho (Web Speech) | **ativo** | `capitao-brain.js`, `capitao-voz.js` |
| WhatsApp / e-mail (convites) | **ativo** · link do aparelho | `capitao-brain.js › linkConvite` |
| Base de bordo (trechos dos guias) | **ativo** · offline | `base-conhecimento.json` |
| Google Drive › Capitão IA v2 (fontes DEMO) | **ativo** · privado | [google-drive/](google-drive/README.md) |
| Proxy da telemetria (`capitao-telemetria`) | **preparado · desligado** | [telemetria-worker/](telemetria-worker/README.md), `capitao-telemetria.js` |
| Coletor NMEA → Drive | a definir (equipamento SEM DADOS) | [telemetria-worker/](telemetria-worker/README.md) |
| Google Cloud · conta de serviço | planejado | [google-cloud/](google-cloud/README.md) |
| Login no servidor (Cloudflare Access ou repo privado) | planejado | [cloudflare/](cloudflare/README.md) |
| Claude API (`capitao-ia`) | **estrutura** · desligada | [claude-api/](claude-api/README.md) |
| ElevenLabs (`capitao-voz`) | **opcional** · estrutura desligada | [elevenlabs/](elevenlabs/README.md) |
| NotebookLM | planejado (não configurado) | `capitao-brain.js › BASE` |
| Gemini (documentos sensíveis) | planejado | `CLAUDE.md › Privacidade` |
| Google Workspace (Gmail, Agenda) | a definir | [google-workspace/](google-workspace/README.md) |
| Domínio www.capitãoia.com.br | planejado (sem DNS) | [cloudflare/](cloudflare/README.md) |

## Regra de todas as integrações

O site é estático e público. Por isso:

1. **Chave de API nunca no site nem no repositório.** Fica como segredo num intermediário (Cloudflare Worker).
2. **O intermediário só responde ao site** (`ORIGENS`) **e só a aparelhos com a chave** (`CHAVE_APP` no cabeçalho `X-Capitao-Chave`), com **freio por IP**.
3. **O app vem desligado.** Cada módulo do lado do app tem `URL_PROXY = ''`; vazio = nada é buscado e a tela segue com o dado local.
   Teste num aparelho só: `localStorage` `capitao.<modulo>.url.v1` = URL do proxy. Chave no aparelho: abrir uma vez com `#<modulo>=<CHAVE_APP>`; `#<modulo>=sair` apaga (`#tele=`, `#ia=`, `#voz=`).
4. **Falhou, demorou ou está sem internet → cai no local**, sem perder a resposta (snapshot fixo, voz do aparelho, base de bordo, SEM DADOS).
5. **Limite de gasto** na conta de cada serviço (Anthropic, ElevenLabs).
6. **Arquivo com a posição do barco nunca em link público.**

```
 aparelho (site público)                  borda (segredos)                       serviços
 ───────────────────────                  ────────────────                       ────────
 capitao-telemetria.js ─X-Capitao-Chave─▶ capitao-telemetria (Worker) ──SA JWT──▶ Google Drive (JSON do coletor, privado)
 capitao-ia.js*        ─X-Capitao-Chave─▶ capitao-ia (Worker)*        ─SDK─────▶ Claude API
 capitao-voz-nuvem.js* ─X-Capitao-Chave─▶ capitao-voz (Worker)*       ─xi-key──▶ ElevenLabs
                                                                      * estrutura / desligado
```

## Ordem recomendada para ligar

1. Login no servidor — [cloudflare/](cloudflare/README.md) (Access) ou [github/](github/README.md) (repositório privado).
2. Conta de serviço Google — [google-cloud/](google-cloud/README.md).
3. Telemetria ao vivo — [telemetria-worker/](telemetria-worker/README.md).
4. IA na nuvem — [claude-api/](claude-api/README.md).
5. Documentos sensíveis — [google-drive/](google-drive/README.md).
6. Voz em nuvem (opcional) — [elevenlabs/](elevenlabs/README.md).

Ao ligar qualquer uma: módulo novo usado offline entra em `CORE` do `sw.js`; lançar versão (`VERSAO` em `capitao-auth.js`, `CACHE` em `sw.js`, tabela do `README.md`); atualizar Manual e Guia rápido.
