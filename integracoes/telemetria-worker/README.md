# Telemetria ao vivo — `capitao-telemetria` (preparado · desligado)

Hoje o app mostra a **navegação simulada**: o `capitao-replay.js` repete um laço de 150 s, com âncora às 07:00 (America/Sao_Paulo), e o `CapitaoTelemetria.atual()` entrega esse quadro com `simulado: true`. O módulo `capitao-telemetria.js` já sabe ler a telemetria ao vivo, mas vem com `URL_PROXY = ''`: nada é buscado e nenhum dado sai do aparelho. Com o proxy ligado, uma leitura real recente vale mais que o laço; sem ela (ou com `simulacao: false`) o app volta ao último quadro conhecido e diz a hora.

```
coletor NMEA 2000 → Google Drive (JSON privado, ~10 s) → capitao-telemetria (Worker, conta de serviço) → app (X-Capitao-Chave) → evento capitao-telemetria
```

## Para ligar (junto com o login no servidor)

1. **Coletor**: definir o equipamento (ainda não escolhido) e fazê-lo gravar um JSON no Drive com o **mesmo quadro plano que o replay entrega** (snake_case, unidade no nome). Os campos que o app sempre leu: `timestamp_utc`, `lat`, `lon`, `sog_nos`, `proa_graus`, `gps_satelites`, `profundidade_m`, `vento_verdadeiro_nos`, `vento_verdadeiro_angulo`, `pressao_barometrica_hpa`, `temp_ar_externo_c`, `temp_agua_c`, `tanque_agua_pct`, `tanque_cinzas_pct`, `tanque_negras_pct`, `bateria_0_tensao_v`, `bateria_2_tensao_v`, `seakeeper_ativo`, `seakeeper_volante_rpm`, `seakeeper_volante_pct`.
   **Campos novos do quadro (1.1.0)**, para o coletor real usar o mesmo formato: rota e atitude (`cog_graus`, `stw_nos`, `piloto_rumo`, `leme_graus`, `jogo_graus`, `caimento_graus`, `distancia_mn`) · motores BB/BE (`motor_bb_rpm`, `motor_be_rpm`, `motor_bb_oleo_bar`, `motor_be_oleo_bar`, `motor_bb_arref_c`, `motor_be_arref_c`, `motor_bb_carga_pct`, `motor_be_carga_pct`, `motor_bb_horimetro_h`, `motor_be_horimetro_h`, `marcha`, `temp_praca_maquinas_c`) · diesel (`consumo_lph`, `diesel_litros`, `diesel_bb_pct`, `diesel_be_pct`) · gerador (`gerador_ativo`, `gerador_kw`, `gerador_horimetro_h`) · baterias (`bateria_1_tensao_v`, além das duas acima) · porão e âncora (`porao_bb_nivel`, `porao_be_nivel`, `bomba_porao_ciclos`, `ancora_estado`) · mar e vento aparente (`ondas_m`, `vento_aparente_nos`, `vento_aparente_angulo`) · equipamentos (`climatizacao_ativa`, `dessalinizador_ativo`, `radar_ativo`, `ais_alvos`) · estado e destino (`estado` — `Navegando`, `Fundeado` ou `Atracado` —, `local`, `destino`, `destino_mn`, `wp_proximo`, `wp_mn`, `eta`) · `alarmes`: lista de `{id, nivel, sistema, lado?, campo, valor, limite, desde}` (sem o campo, o app nunca diz «nenhum alarme ativo»: na simulação a cláusula some e no modo real o texto é SEM LEITURA; o coletor que mede alarmes manda a lista, vazia quando não há nenhum). Posição só em `lat` e `lon` numéricos: nunca em texto. Fica **fora** do quadro, de propósito: pessoas a bordo, MMSI, registro, indicativo e qualquer texto de protocolo. O catálogo de rótulo, unidade e casas de cada campo é o `D.campos` do `capitao-dados.js`, e o arquivo `Formato do quadro do coletor.csv` (Drive › Capitão IA v2 › 05 Telemetria — coletor NMEA) traz o mesmo catálogo; o `Série do coletor NMEA — 150 s.csv` traz um laço de exemplo.
2. **Google Cloud**: conta de serviço + chave JSON — ver [../google-cloud/](../google-cloud/README.md). Compartilhar **só** o JSON do coletor com o e-mail da conta (Leitor).
3. **Worker** (nesta pasta): preencher `GOOGLE_SA_EMAIL` no `wrangler.toml`; `npx wrangler secret put GOOGLE_SA_KEY` (a `private_key`), `npx wrangler secret put DRIVE_FILE_ID`, `npx wrangler secret put CHAVE_APP` (chave longa aleatória); `npx wrangler deploy`.
4. **App**: pôr o endereço em `URL_PROXY` no `capitao-telemetria.js`, lançar versão (`VERSAO`, `CACHE`, README).
5. **Aparelhos**: abrir uma vez com `#tele=<CHAVE_APP>` no fim do endereço (a chave fica só naquele aparelho e sai do endereço na hora). `#tele=sair` apaga.

Teste num aparelho antes de publicar: `localStorage['capitao.telemetria.url.v1'] = '<URL do Worker>'`.

## Comportamento

- Cadência no app: navegando 30 s (até 5 nós) · 10 s (até 12 nós) · 5 s (acima); atracado/fundeado 2 min (30 min) · 5 min (1 h) · 10 min.
- Leitura com mais de 10 min não conta como ao vivo: o app volta ao último quadro conhecido (na simulação, o laço) e diz a hora.
- Erro, demora (8 s) ou sem internet → segue com o dado local. Motor desligado continua mostrando a última leitura com motor ligado e a hora, nunca zero.
- Proteções do Worker: `ORIGENS`, `CHAVE_APP` em tempo constante, 120 leituras/min por IP, cache de 4 s, `no-store`.
