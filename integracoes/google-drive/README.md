# Google Drive — fonte dos dados (estrutura)

O Drive é a **fonte de verdade** do projeto. O site nunca lê o Drive direto (é público): o que chega ao app passa por **extração** (gerador) ou por **proxy** (Worker com conta de serviço).

## Pasta `Capitão IA v2` (criada em 26/09/2026 · privada · só o dono)

Hoje com **dados fictícios de demonstração** (rótulo DEMO em cada arquivo). Os IDs ficam fora do repositório.

| Pasta | Arquivo (DEMO) | Uso no app | Pode ir ao site público? |
|---|---|---|---|
| `01 Manuais e guias de bordo` | Guias de bordo (Gerador Onan, Estabilizador Seakeeper, Climatização, Eletrônicos Garmin/Fusion/VHF 315, Motores Volvo Penta), Checklist de saída e chegada, Inventário de bordo | trechos em `base-conhecimento.json`, FAQ (`D.faq`), inventário (`D.equipamentos`) | trechos técnicos, sim |
| `02 Documentos` | Controle de documentos | `D.documentos` (situação e validade; sem números nem valores) | só o controle; documentos em si **não** |
| `03 Agenda de manutenção` | Agenda preditiva | `D.agenda` (escada D-90 · D-60 · D-30 · D-0) | sim |
| `04 Diário de bordo` | Diário de bordo | `D.diario` (linhas da fonte) | resumo, sem valores e sem terceiros |
| `05 Telemetria — coletor NMEA` | `snapshot_demo_…json` | `D.snapshot` (fixo) | **não** o arquivo (tem a posição) — só via proxy |
| `06 Abastecimento` | Registro de abastecimento | `D.abastecimentos` (litros, data, situação) | sem valores e sem número de NF |
| `07 Protocolos de emergência` | Protocolo de emergência — procedimento padrão | `D.protocolos` (SOS) | sim |
| raiz | LEIA-ME — Capitão IA v2 (DEMO) | regras da pasta | — |

## Três caminhos

1. **Extração (ativo).** `ferramentas/demo/gerar_demo.py` é hoje a fonte única dos dados de demonstração: gera `capitao-dados.js`, `base-conhecimento.json` e os arquivos que foram enviados ao Drive. Para a próxima embarcação: trocar os dados do gerador pelos reais (lidos do Drive, com a fonte de cada um), rodar o gerador e lançar versão.
2. **Proxy de leitura (preparado · desligado).** `integracoes/telemetria-worker/` com conta de serviço — ver [google-cloud/](../google-cloud/README.md).
3. **Documentos sensíveis (planejado · depois do login no servidor).** Foto ou PDF → leitura por IA → linha **A CONFERIR** com vencimento; o original fica em `02 Documentos`. Hoje o arquivo **não sai do aparelho** e vira uma linha A CONFERIR.
