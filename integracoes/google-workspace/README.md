# Google Workspace — a definir

O escopo não está definido. Abaixo, só o que já toca produtos Google e os pontos do app onde uma conexão encaixaria.

## O que já existe

| Produto | Como está | Onde |
|---|---|---|
| Drive | pasta `Capitão IA v2` com as fontes (hoje DEMO) | [google-drive/](../google-drive/README.md) |
| NotebookLM | **não configurado** nesta embarcação (o chat não mostra botão de base externa) | `capitao-brain.js › BASE = null` |
| Gemini | citado para documentos sensíveis, depois do login no servidor | `CLAUDE.md › Privacidade` |
| E-mail | convites da Equipe saem por `mailto:` do próprio aparelho | `capitao-brain.js › linkConvite` |

## Pontos onde uma conexão encaixaria (candidatos, nada decidido)

- **Agenda preditiva** (escada D-90 · D-60 · D-30 · D-0, botão Executado) — hoje só no app e no `localStorage`.
- **Convites da Equipe** — hoje `mailto:` / `wa.me`; o convite fica PENDENTE até a confirmação do proprietário.
- **Diário de bordo** — hoje só cresce no navegador de cada aparelho (não sincroniza).
- **Documentos** — vencimentos com alerta abaixo de 90 dias.

Qualquer um desses exige servidor com login (dados pessoais, contatos, valores): mesma regra da [pasta de integrações](../README.md).
