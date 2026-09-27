# Telemetria ao vivo — `capitao-telemetria` (preparado · desligado)

Hoje o app mostra o **snapshot fixo** do `capitao-dados.js` (demonstração: 26/09/2026 10:12). O módulo `capitao-telemetria.js` já sabe ler a telemetria ao vivo, mas vem com `URL_PROXY = ''`: nada é buscado.

```
coletor NMEA 2000 → Google Drive (JSON privado, ~10 s) → capitao-telemetria (Worker, conta de serviço) → app (X-Capitao-Chave) → evento capitao-telemetria
```

## Para ligar (junto com o login no servidor)

1. **Coletor**: definir o equipamento (SEM DADOS hoje) e fazê-lo gravar um JSON no Drive com os campos que o app usa: `timestamp_utc`, `lat`, `lon`, `sog_nos`, `proa_graus`, `gps_satelites`, `profundidade_m`, `vento_verdadeiro_nos`, `vento_verdadeiro_angulo`, `pressao_barometrica_hpa`, `temp_ar_externo_c`, `temp_agua_c`, `tanque_agua_pct`, `tanque_cinzas_pct`, `tanque_negras_pct`, `bateria_0_tensao_v`, `bateria_2_tensao_v`, `seakeeper_ativo`, `seakeeper_volante_rpm`, `seakeeper_volante_pct`. O formato de exemplo está em `Drive › Capitão IA v2 › 05 Telemetria — coletor NMEA` (arquivo DEMO).
2. **Google Cloud**: conta de serviço + chave JSON — ver [../google-cloud/](../google-cloud/README.md). Compartilhar **só** o JSON do coletor com o e-mail da conta (Leitor).
3. **Worker** (nesta pasta): preencher `GOOGLE_SA_EMAIL` no `wrangler.toml`; `npx wrangler secret put GOOGLE_SA_KEY` (a `private_key`), `npx wrangler secret put DRIVE_FILE_ID`, `npx wrangler secret put CHAVE_APP` (chave longa aleatória); `npx wrangler deploy`.
4. **App**: pôr o endereço em `URL_PROXY` no `capitao-telemetria.js`, lançar versão (`VERSAO`, `CACHE`, README).
5. **Aparelhos**: abrir uma vez com `#tele=<CHAVE_APP>` no fim do endereço (a chave fica só naquele aparelho e sai do endereço na hora). `#tele=sair` apaga.

Teste num aparelho antes de publicar: `localStorage['capitao.telemetria.url.v1'] = '<URL do Worker>'`.

## Comportamento

- Cadência no app: navegando 30 s (até 5 nós) · 10 s (até 12 nós) · 5 s (acima); atracado/fundeado 2 min (30 min) · 5 min (1 h) · 10 min.
- Leitura com mais de 10 min não conta como ao vivo: o app volta ao snapshot e diz a hora.
- Erro, demora (8 s) ou sem internet → segue com o dado local. Motor desligado continua mostrando a última leitura com motor ligado e a hora, nunca zero.
- Proteções do Worker: `ORIGENS`, `CHAVE_APP` em tempo constante, 120 leituras/min por IP, cache de 4 s, `no-store`.
