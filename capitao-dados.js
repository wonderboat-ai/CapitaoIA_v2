/* Capitão IA — dados da embarcação (GERADO por ferramentas/demo/gerar_demo.py — não editar à mão).
   Cada grupo traz a fonte (arquivo no Drive › Capitão IA v2). Na leitura, null = SEM DADOS (ou SEM LEITURA, em sensor). */
window.CapitaoDados = {
 "versao": "26/09/2026",
 "simulacao": true,
 "demo": false,
 "embarcacao": {
  "nome": "Capitão IA",
  "fabricante": "Estaleiro Marévia",
  "modelo": "Marévia 40 HT",
  "rotulo": "Marévia 40 HT · 12,40 m · 2023",
  "motorizacao": "2 × Cummins QSB6.7 305 · eixo",
  "ano": 2023,
  "registro": "CIA-23-0417",
  "comprimento": 12.4,
  "boca": 3.95,
  "calado": 1.1,
  "deslocamento": 9.3,
  "lotacao": 12,
  "pessoasBordo": 4,
  "tanques": {"diesel_l":1600,"diesel_n":2,"agua_l":400,"cinzas_l":100,"negras_l":100},
  "un": {"comprimento":"m","boca":"m","calado":"m","deslocamento":"t","lotacao":"pessoas","pessoasBordo":"pessoas"},
  "proprietario": "Lucas Araújo",
  "base": "Balneário Camboriú (SC)",
  "fuso": "America/Sao_Paulo",
  "mmsi": "710123456",
  "mmsiNota": "fictício · demonstração",
  "fonte": "cadastro da embarcação no app (proprietário)"
 },
 "posicaoRef": {
  "lat": -26.99056,
  "lon": -48.63472,
  "nome": "Balneário Camboriú (centro)",
  "fonte": "Open-Meteo Geocoding (GeoNames 3471039)"
 },
 "mar": [[-26.99056,-48.63472],[-26.995,-48.6],[-27.0,-48.55]],
 "drive": {
  "raiz": "Drive › Capitão IA v2",
  "pastas": {"manuais":"01 Manuais e guias de bordo","docs":"02 Documentos","agenda":"03 Agenda de manutenção","diario":"04 Diário de bordo","tele":"05 Telemetria — coletor NMEA","abast":"06 Abastecimento","protocolos":"07 Protocolos de emergência"},
  "arquivos": {"leiame":"LEIA-ME — Capitão IA v2","g_motores":"Guia de bordo — Motores Cummins","g_gerador":"Guia de bordo — Gerador Onan","g_seakeeper":"Guia de bordo — Estabilizador Seakeeper","g_clima":"Guia de bordo — Climatização Webasto","g_eletronicos":"Guia de bordo — Eletrônicos Garmin, áudio Fusion e rádios Icom","g_eletrico":"Guia de bordo — Sistema elétrico 24 V e 12 V","g_dessalinizador":"Guia de bordo — Dessalinizador Schenker","g_porao":"Guia de bordo — Bombas de porão Rule","g_ancora":"Guia de bordo — Guincho e corrente Lewmar","g_piloto":"Guia de bordo — Piloto automático Raymarine","g_radar":"Guia de bordo — Radar Garmin","g_ais":"Guia de bordo — AIS em-trak","g_seafire":"Guia de bordo — Sistema fixo de incêndio","g_epirb":"Guia de bordo — EPIRB","checklist":"Checklist de bordo","inventario":"Inventário de bordo","documentos":"Controle de documentos","agenda":"Agenda preditiva","diario":"Diário de bordo","snapshot":"Leitura do coletor NMEA — 26-09-2026 10h12.json","abast":"Registro de abastecimento","protocolo":"Protocolo de emergência — procedimento padrão"}
 },
 "equipamentos": [{"id":"motores","nome":"Motores","fabricante":"Cummins","modelo":"QSB6.7 305","qtd":2,"lados":"BB e BE","guia":"g_motores","palavras":["cummins","kamins","comins","qsb","motor","motores"],"nominal":{"potencia_cv":305,"rpm_max":2600,"rpm_cruzeiro":2050,"rpm_lenta":700,"transmissao":"eixo"},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"gerador","nome":"Gerador","fabricante":"Onan","modelo":"QD 9","qtd":1,"guia":"g_gerador","palavras":[" onan ","gerador","qd 9","qd nove"],"nominal":{"kw":9,"hz":60,"rpm":1800},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"estabilizador","nome":"Estabilizador giroscópico","fabricante":"Seakeeper","modelo":"Seakeeper 3","qtd":1,"guia":"g_seakeeper","palavras":["seakeeper","sikiper","giroscopio","estabilizador"],"nominal":{"pct_estabiliza":85},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"climatizacao","nome":"Climatização","fabricante":"Webasto","modelo":"FCF Platinum 16000 e 12000","qtd":3,"guia":"g_clima","palavras":["webasto","vebasto","fcf","platinum","climatizacao","ar condicionado"],"nominal":{"btu_h_total":40000},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"eletronicos","nome":"Plotters","fabricante":"Garmin","modelo":"GPSMAP 1243xsv","qtd":2,"guia":"g_eletronicos","palavras":["garmin","gpsmap","plotter","plotters","chartplotter"],"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"audio","nome":"Áudio","fabricante":"Fusion","modelo":"MS-UD755","qtd":1,"guia":"g_eletronicos","palavras":["fusion","audio"," som ","bluetooth"],"nominal":{"zonas":2},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"vhf","nome":"Rádios VHF","fabricante":"Icom","modelo":"IC-M510 e IC-M37","qtd":2,"guia":"g_eletronicos","palavras":["vhf","radio vhf","icom","canal 16"],"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"epirb","nome":"EPIRB","fabricante":"Ocean Signal","modelo":"SafeSea E100G","qtd":1,"guia":"g_epirb","palavras":["epirb","radiobaliza","baliza","ipirb"],"validade":"doc-epirb","seguranca":true,"nota":"modelo, validade e acionamento: veja a etiqueta do equipamento","fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"seafire","nome":"Sistema fixo de supressão de incêndio","fabricante":"Seafire","modelo":"FD 300M","qtd":1,"guia":"g_seafire","palavras":["seafire","sea fire","sistema de incendio","supressao"],"validade":"seafire-inspecao","seguranca":true,"nota":"modelo, validade e acionamento: veja a etiqueta do equipamento","fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"dessalinizador","nome":"Dessalinizador","fabricante":"Schenker","modelo":"Zen 30","qtd":1,"guia":"g_dessalinizador","palavras":["schenker","shenker","zen 30","dessalinizador","osmose"],"nominal":{"lph":30},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"porao","nome":"Bombas de porão","fabricante":"Rule","modelo":"Rule 2000 (24 V)","qtd":2,"lados":"BB e BE","guia":"g_porao","palavras":[" rule ","bomba de porao","bombas de porao","porao"],"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"ancora","nome":"Guincho e contador de corrente","fabricante":"Lewmar","modelo":"V2 · contador AA150","qtd":1,"guia":"g_ancora","palavras":["lewmar","leumar","guincho","ancora","contador de corrente","molinete"],"nominal":{"corrente_m":60},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"piloto","nome":"Piloto automático","fabricante":"Raymarine","modelo":"Evolution EV-1 · ACU-400","qtd":1,"guia":"g_piloto","palavras":["raymarine","reimarine","evolution","piloto automatico","piloto"],"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"radar","nome":"Radar","fabricante":"Garmin","modelo":"GMR 24 xHD3","qtd":1,"guia":"g_radar","palavras":["radar","gmr","xhd3","domo"],"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"ais","nome":"AIS (classe B)","fabricante":"em-trak","modelo":"B954","qtd":1,"guia":"g_ais","palavras":[" ais ","em-trak","emtrak","transponder"],"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"eletrico","nome":"Baterias (24 V e 12 V)","fabricante":"Victron Energy","modelo":"AGM Super Cycle 12 V 230 Ah","qtd":8,"guia":"g_eletrico","palavras":["victron","vitron","bateria","baterias","banco de baterias"," agm "],"nominal":{"bancos":[{"id":"servico","v":24,"n":4,"campo":"bateria_0_tensao_v"},{"id":"partida","v":24,"n":2,"campo":"bateria_1_tensao_v"},{"id":"eletronica","v":12,"n":2,"campo":"bateria_2_tensao_v"}]},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"}],
 "equipNota": "Inventário de bordo · 16 equipamentos · Drive › Capitão IA v2 › 01 Manuais e guias de bordo",
 "snapshot": {
  "quando": "26/09/2026 10:12",
  "hora": "10:12",
  "dia": "26/09",
  "iso": "2026-09-26T10:12:00-03:00",
  "fonte": "coletor NMEA · leitura de 26/09/2026 10:12",
  "estado": "Fundeado",
  "local": "enseada de Balneário Camboriú",
  "gps": {"lat":-26.993,"lon":-48.614,"texto":"26°59,58'S 048°36,84'W","satelites":26},
  "sog": 0.1,
  "proa": 71,
  "profundidade": 7.4,
  "vento": 9.2,
  "ventoDe": 58,
  "pressao": 1017,
  "ar": 22.6,
  "agua": 20.1,
  "bat24": 27.42,
  "bat12": 13.18,
  "tanques": {"agua":68.5,"cinzas":21.0,"negras":34.5},
  "diesel": {"bb":54.0,"be":52.0,"litros":848,"capacidade":1600,"tanques":"2 × 800 L","hora":"26/09 09:31","nota":"última leitura com motores ligados"},
  "motores": {"hora":"26/09 09:31","estado":"desligados desde 09:31","rpm":[700,690],"oleo":[3.4,3.3],"arref":[79,78],"horimetro":[412.6,409.8],"marcha":"neutro"},
  "gerador": {"estado":"ligado desde 09:35","horas":1236.4,"hora":"26/09 10:12"},
  "seakeeper": {"estado":"ligado","hora":"26/09 10:12"},
  "porao": null,
  "ancora": null
 },
 "consumo": {
  "cruzeiro": {"nos":18,"rpm":2050,"lph":68},
  "lenta": {"lph":6.2},
  "periodo": "01/08–26/09/2026",
  "fonte": "telemetria · taxa de combustível dos dois motores",
  "desdeAbast": {"litros":192,"desde":"12/09/2026","horas":"2,8 h de motor por lado"}
 },
 "reserva": 0.1,
 "autonomia": {
  "horas": 11.2,
  "mn": 202,
  "lenta": 123
 },
 "serie24v": [{"diasAtras":6,"min":26.1,"max":28.4,"d":"20/09"},{"diasAtras":5,"min":26.0,"max":28.6,"d":"21/09"},{"diasAtras":4,"min":25.9,"max":27.2,"d":"22/09"},{"diasAtras":3,"min":25.8,"max":27.0,"d":"23/09"},{"diasAtras":2,"min":25.7,"max":28.5,"d":"24/09"},{"diasAtras":1,"min":25.9,"max":27.1,"d":"25/09"},{"diasAtras":0,"min":26.0,"max":27.4,"d":"26/09"}],
 "agenda": [{"id":"porao-teste","t":"Teste das bombas de porão e alarmes","curto":"TESTE","equip":"Bombas de porão Rule 2000","sistema":"porao","quem":"técnico","intervalo":"mensal","meses":1,"ultimaHa":56,"venceEm":-25,"seguranca":true,"palavras":["bombas de porao","bomba de porao","teste das bombas"],"fonte":"Agenda preditiva","ultima":"01/08/2026","vence":"01/09/2026","dn":-25,"st":"ATRASADA","rot":"ATRASADA · 25 D","tom":"crit"},{"id":"clima-filtro","t":"Limpeza do filtro de água salgada da climatização","curto":"FILTRO","equip":"Climatização Webasto FCF Platinum","sistema":"climatizacao","quem":"marina","intervalo":"mensal","meses":1,"ultimaHa":47,"venceEm":-16,"palavras":["filtro de agua salgada","filtro da climatizacao","filtro do ar condicionado","filtro do ar-condicionado"],"fonte":"Agenda preditiva","ultima":"10/08/2026","vence":"10/09/2026","dn":-16,"st":"ATRASADA","rot":"ATRASADA · 16 D","tom":"crit"},{"id":"gerador-rotor","t":"Inspeção do rotor (impeller) do gerador","curto":"ROTOR","equip":"Gerador Onan QD 9","sistema":"gerador","quem":"técnico","intervalo":"12 meses","meses":12,"ultimaHa":367,"venceEm":-2,"palavras":["rotor do gerador","impeller do gerador","rotor impeller do gerador"],"fonte":"Agenda preditiva","ultima":"24/09/2025","vence":"24/09/2026","dn":-2,"st":"ATRASADA","rot":"ATRASADA · 2 D","tom":"crit"},{"id":"casco-anodos","t":"Limpeza de casco e troca de anodos","curto":"ANODOS","equip":"Casco","sistema":"casco","quem":"marina","intervalo":"6 meses","meses":6,"ultimaHa":175,"venceEm":9,"palavras":["limpeza de casco","limpeza do casco","anodos do casco","troca de anodos"],"fonte":"Agenda preditiva","ultima":"04/04/2026","vence":"05/10/2026","dn":9,"st":"D-30","rot":"D-9","tom":"warn"},{"id":"epirb-teste","t":"Autoteste do EPIRB e validade conferida na etiqueta","curto":"AUTOTESTE","equip":"EPIRB","sistema":"epirb","quem":"Lucas","intervalo":"mensal","meses":1,"ultimaHa":18,"venceEm":13,"seguranca":true,"palavras":["autoteste do epirb","teste do epirb","teste da baliza","autoteste da baliza"],"fonte":"Agenda preditiva","ultima":"08/09/2026","vence":"09/10/2026","dn":13,"st":"D-30","rot":"D-13","tom":"warn"},{"id":"motores-oleo","t":"Troca de óleo e filtros dos motores","curto":"ÓLEO","equip":"Motores Cummins QSB6.7 305","sistema":"motores","quem":"oficina de motores","intervalo":"12 meses ou 450 h (o que vier antes)","meses":12,"ultimaHa":348,"venceEm":17,"horas":{"limite":450,"campos":["motor_bb_horimetro_h","motor_be_horimetro_h"],"atual":412.6,"faltam":37.4},"palavras":["oleo dos motores","oleo do motor","filtros dos motores"],"fonte":"Agenda preditiva","ultima":"13/10/2025","vence":"13/10/2026","dn":17,"st":"D-30","rot":"D-17","tom":"warn"},{"id":"gerador-revisao","t":"Revisão do gerador: óleo e filtros","curto":"REVISÃO","equip":"Gerador Onan QD 9","sistema":"gerador","quem":"técnico","intervalo":"12 meses ou 1.300 h","meses":12,"ultimaHa":341,"venceEm":24,"horas":{"limite":1300,"campos":["gerador_horimetro_h"],"atual":1236.4,"faltam":63.6},"palavras":["revisao do gerador","oleo do gerador","filtros do gerador"],"fonte":"Agenda preditiva","ultima":"20/10/2025","vence":"20/10/2026","dn":24,"st":"D-30","rot":"D-24","tom":"warn"},{"id":"seakeeper-anodo","t":"Anodo do trocador de calor do estabilizador","curto":"ANODO","equip":"Estabilizador Seakeeper 3","sistema":"estabilizador","quem":"técnico","intervalo":"6 meses","meses":6,"ultimaHa":149,"venceEm":35,"palavras":["anodo do estabilizador","anodo do seakeeper","anodo do trocador"],"fonte":"Agenda preditiva","ultima":"30/04/2026","vence":"31/10/2026","dn":35,"st":"D-60","rot":"D-35","tom":"tele"},{"id":"motores-rotor","t":"Troca do rotor da bomba de água salgada dos motores","curto":"ROTOR","equip":"Motores Cummins QSB6.7 305","sistema":"motores","quem":"oficina de motores","intervalo":"12 meses","meses":12,"ultimaHa":324,"venceEm":41,"palavras":["rotor da bomba de agua salgada","rotor dos motores","impeller dos motores","rotor do motor"],"fonte":"Agenda preditiva","ultima":"06/11/2025","vence":"06/11/2026","dn":41,"st":"D-60","rot":"D-41","tom":"tele"},{"id":"baterias","t":"Verificação do banco de baterias e conexões","curto":"VERIFICAÇÃO","equip":"Baterias Victron Energy (24 V e 12 V)","sistema":"eletrico","quem":"técnico","intervalo":"6 meses","meses":6,"ultimaHa":134,"venceEm":50,"palavras":["banco de baterias","conexoes das baterias","verificacao das baterias"],"fonte":"Agenda preditiva","ultima":"15/05/2026","vence":"15/11/2026","dn":50,"st":"D-60","rot":"D-50","tom":"tele"},{"id":"garmin-cartas","t":"Atualização de cartas e software dos eletrônicos","curto":"CARTAS","equip":"Plotters Garmin GPSMAP 1243xsv","sistema":"eletronicos","quem":"Lucas","intervalo":"12 meses","meses":12,"ultimaHa":299,"venceEm":66,"palavras":["cartas do plotter","cartas nauticas","atualizacao das cartas","software dos eletronicos"],"fonte":"Agenda preditiva","ultima":"01/12/2025","vence":"01/12/2026","dn":66,"st":"D-90","rot":"D-66","tom":"accent"},{"id":"clima-revisao","t":"Revisão anual da climatização","curto":"REVISÃO","equip":"Climatização Webasto FCF Platinum","sistema":"climatizacao","quem":"marina","intervalo":"12 meses","meses":12,"ultimaHa":279,"venceEm":86,"palavras":["revisao da climatizacao","revisao do ar condicionado"],"fonte":"Agenda preditiva","ultima":"21/12/2025","vence":"21/12/2026","dn":86,"st":"D-90","rot":"D-86","tom":"accent"},{"id":"motores-revisao","t":"Revisão anual dos motores","curto":"REVISÃO","equip":"Motores Cummins QSB6.7 305","sistema":"motores","quem":"oficina de motores","intervalo":"12 meses","meses":12,"ultimaHa":253,"venceEm":112,"palavras":["revisao dos motores","revisao anual dos motores"],"fonte":"Agenda preditiva","ultima":"16/01/2026","vence":"16/01/2027","dn":112,"st":"EM DIA","rot":"D-112","tom":"ok"},{"id":"seafire-inspecao","t":"Inspeção anual do sistema fixo de supressão","curto":"INSPEÇÃO","equip":"Sistema fixo de supressão de incêndio","sistema":"seafire","quem":"técnico","intervalo":"12 meses","meses":12,"ultimaHa":225,"venceEm":140,"seguranca":true,"palavras":["inspecao do sistema fixo","sistema fixo de supressao","inspecao do seafire"],"fonte":"Agenda preditiva","ultima":"13/02/2026","vence":"13/02/2027","dn":140,"st":"EM DIA","rot":"D-140","tom":"ok"}],
 "agendaFonte": "Agenda preditiva · Drive › Capitão IA v2 › 03 Agenda de manutenção",
 "tarefasEquipe": [{"id":"g01","n":"Revisar mangueiras do dessalinizador","venceEm":20,"quem":"técnico","meses":6,"sistema":"dessalinizador","origem":"equipe","vence":"2026-10-16","dn":20,"st":"D-30","rot":"D-20","tom":"warn"},{"id":"g02","n":"Lavar o convés e o hard-top","venceEm":5,"quem":"marina","meses":1,"sistema":"casco","origem":"equipe","vence":"2026-10-01","dn":5,"st":"D-30","rot":"D-5","tom":"warn"}],
 "documentos": [{"id":"tie","n":"Título de Inscrição da Embarcação (TIE)","cat":"Registro","venceEm":646,"emitidoHa":1180,"numero":"CIA-23-0417","nota":"renovação a cada 5 anos","fonte":"Controle de documentos","vence":"03/07/2028","dn":646,"st":"EM DIA","emitido":"04/07/2023"},{"id":"seguro","n":"Seguro da embarcação","cat":"Seguro","venceEm":19,"emitidoHa":346,"nota":"apólice guardada a bordo e no Drive","fonte":"Controle de documentos","vence":"15/10/2026","dn":19,"st":"VENCE EM 19 D","emitido":"15/10/2025"},{"id":"licenca","n":"Licença de Estação de rádio (VHF)","cat":"Licenças","venceEm":65,"nota":"rádios VHF fixo e portátil","fonte":"Controle de documentos","vence":"30/11/2026","dn":65,"st":"VENCE EM 65 D"},{"id":"laudo","n":"Laudo de vistoria anual","cat":"Laudos","venceEm":326,"emitidoHa":39,"nota":"laudo arquivado no Drive","fonte":"Controle de documentos","vence":"18/08/2027","dn":326,"st":"EM DIA","emitido":"18/08/2026"},{"id":"gar-estab","n":"Garantia do estabilizador","cat":"Garantias","venceEm":175,"nota":"Seakeeper 3","fonte":"Controle de documentos","vence":"20/03/2027","dn":175,"st":"EM DIA"},{"id":"gar-eletr","n":"Garantia dos eletrônicos","cat":"Garantias","venceEm":137,"nota":"plotters e radar Garmin","fonte":"Controle de documentos","vence":"10/02/2027","dn":137,"st":"EM DIA"},{"id":"doc-epirb","n":"Certificado do EPIRB (bateria e disparador hidrostático)","cat":"Segurança","venceEm":540,"nota":"validade conferida também na etiqueta do equipamento","fonte":"Controle de documentos","vence":"19/03/2028","dn":540,"st":"EM DIA"},{"id":"nf-abast","n":"Nota fiscal do abastecimento","cat":"Notas","emitidoHa":14,"st":"CONFERIDA","nota":"abastecimento de 620 L · sem valores no app","fonte":"Controle de documentos","emitido":"12/09/2026"}],
 "docsFonte": "Controle de documentos · Drive › Capitão IA v2 › 02 Documentos",
 "abastecimentos": [{"diasAtras":14,"litros":620,"combustivel":"diesel","local":"posto da marina · Balneário Camboriú","st":"CONFERIDO","nivelDepois":65,"nota":"NF no Drive","d":"12/09/2026"},{"diasAtras":55,"litros":540,"combustivel":"diesel","local":"posto da marina · Balneário Camboriú","st":"CONFERIDO","nivelDepois":71,"nota":"NF no Drive","d":"02/08/2026"}],
 "abastFonte": "Registro de abastecimento · Drive › Capitão IA v2 › 06 Abastecimento",
 "regraAbast": "abastecer antes de 25 % do total dos tanques, 400 L de 1.600 L (Checklist de bordo § Abastecimento)",
 "diario": [{"id":"d01","diasAtras":0,"h":"07:00","sys":"Navegação","tom":"tele","who":"Lucas","pend":false,"t":"Saída da base com 4 pessoas a bordo. Checklist de saída feito; teste das bombas de porão continua pendente.","d":"26/09","iso":"2026-09-26T07:00:00-03:00"},{"id":"d03","diasAtras":2,"h":"17:10","sys":"Manutenção","tom":"warn","who":"técnico","pend":true,"ref":"gerador-rotor","t":"Inspeção do rotor do gerador não feita no prazo — reagendar; rotor de reserva em falta no estoque.","palavras":["rotor do gerador","impeller do gerador","rotor impeller do gerador"],"d":"24/09","iso":"2026-09-24T17:10:00-03:00"},{"id":"d04","diasAtras":3,"h":"19:30","sys":"Motores","tom":"accent","who":"Lucas","pend":false,"ref":"motores-rotor","t":"Motor BE 1 a 2 °C acima do BB em cruzeiro nos últimos dias, com picos acima de 88 °C — acompanhar; rotor da bomba de água salgada dos motores na agenda.","d":"23/09","iso":"2026-09-23T19:30:00-03:00"},{"id":"d05","diasAtras":6,"h":"11:05","sys":"Equipamentos","tom":"accent","who":"Lucas","pend":true,"ref":"clima-filtro","t":"Climatização da cabine de proa com fluxo fraco. Suspeita: filtro de água salgada sujo (limpeza atrasada).","palavras":["filtro de agua salgada","filtro da climatizacao","filtro do ar condicionado","filtro do ar-condicionado"],"d":"20/09","iso":"2026-09-20T11:05:00-03:00"},{"id":"d02","diasAtras":14,"h":"15:40","sys":"Combustível","tom":"ok","who":"Lucas","pend":false,"t":"Abastecimento de 620 L de diesel no posto da marina; tanques em ≈ 65 %. NF no Drive.","d":"12/09","iso":"2026-09-12T15:40:00-03:00"},{"id":"d06","diasAtras":18,"h":"08:30","sys":"Segurança","tom":"ok","who":"Lucas","pend":false,"ref":"epirb-teste","t":"Autoteste do EPIRB feito: luz de teste conforme a etiqueta.","d":"08/09","iso":"2026-09-08T08:30:00-03:00"},{"id":"d07","diasAtras":21,"h":"10:00","sys":"Segurança","tom":"crit","who":"técnico","pend":true,"ref":"porao-teste","t":"Teste das bombas de porão adiado por chuva.","palavras":["bombas de porao","bomba de porao","teste das bombas"],"d":"05/09","iso":"2026-09-05T10:00:00-03:00"},{"id":"d08","diasAtras":29,"h":"16:25","sys":"Eletrônicos","tom":"accent","who":"Lucas","pend":false,"ref":"garmin-cartas","t":"Cartas do plotter desatualizadas; a atualização está na agenda.","d":"28/08","iso":"2026-08-28T16:25:00-03:00"},{"id":"d09","diasAtras":39,"h":"09:00","sys":"Documentos","tom":"ok","who":"Lucas","pend":false,"ref":"laudo","t":"Vistoria anual feita; laudo arquivado no Drive.","d":"18/08","iso":"2026-08-18T09:00:00-03:00"}],
 "diarioFonte": "Diário de bordo · Drive › Capitão IA v2 › 04 Diário de bordo",
 "equipe": {
  "perfis": [{"id":"lucas","nome":"Lucas Araújo","ini":"LA","papel":"proprietário","acesso":"total"}],
  "apoio": [{"id":"marina","papel":"Marina da base","onde":"Balneário Camboriú (SC)","para":"casco, filtros, vaga","servico":"casco, filtros, vaga"},{"id":"oficina","papel":"Oficina de motores diesel","onde":"atende na marina da base","para":"motores e gerador","servico":"motores e gerador"},{"id":"tecnico","papel":"Técnico de bordo","onde":"atende na marina da base","para":"estabilizador, elétrica, porão","servico":"estabilizador, elétrica, porão"},{"id":"eletronica","papel":"Técnico de eletrônicos","onde":"atende na marina da base","para":"plotters, rádios, piloto, radar, AIS","servico":"plotters, rádios, piloto, radar, AIS"},{"id":"refrigeracao","papel":"Técnico de refrigeração","onde":"atende na marina da base","para":"climatização, dessalinizador","servico":"climatização, dessalinizador"},{"id":"posto","papel":"Posto de combustível","onde":"na marina da base","para":"diesel","servico":"diesel"}],
  "nota": "Telefones: ficam só no aparelho (Equipe)."
 },
 "faq": {
  "gerador": {"status":"PRONTO","fonte":"Guia de bordo — Gerador Onan","equip":"Gerador Onan","modelo":"QD 9","perguntas":[{"q":"Como ligar o gerador?","passos":[{"n":"1","t":"Com o gerador parado, confira o nível de óleo e o líquido de arrefecimento. Abra a válvula de fundo da entrada de água salgada e confira se o filtro de água salgada está limpo. Ligue a ventilação do compartimento por alguns minutos se houver cheiro de combustível.","secao":"1 · Antes de ligar"},{"n":"2","t":"No painel do gerador, pressione e segure PARTIDA até o motor pegar. Aguarde a tensão e a frequência estabilizarem no painel. Só depois transfira as cargas no quadro elétrico, uma de cada vez; ligue a climatização por último.","secao":"2 · Ligar"},{"n":"3","t":"Com o gerador ligado, confira a saída de água pelo escapamento. Sem água saindo, desligue na hora: é sinal de falta de refrigeração (válvula de fundo fechada, filtro entupido ou rotor danificado).","secao":"3 · Água no escapamento"}]},{"q":"Como desligar o gerador?","passos":[{"n":"1","t":"Retire as cargas no quadro elétrico. Deixe o gerador funcionar de 3 a 5 minutos sem carga para esfriar e pressione PARADA. Feche a válvula de fundo se o barco for ficar parado por vários dias.","secao":"4 · Desligar"}]},{"q":"Alarme de alta temperatura","passos":[{"n":"1","t":"Desligue o gerador. Verifique a válvula de fundo, o filtro de água salgada e o rotor (impeller). Nunca abra a tampa do arrefecimento com o motor quente. Registre o alarme no diário.","secao":"5 · Alarme de alta temperatura"}]},{"q":"Alarme de baixa pressão de óleo","passos":[{"n":"1","t":"Desligue o gerador e confira o nível de óleo com ele parado. Se o nível estiver correto e o alarme voltar, não religue: chame o técnico de bordo.","secao":"6 · Alarme de baixa pressão de óleo"}]},{"q":"Quantas horas tem e quando revisar?","passos":[{"n":"1","t":"O horímetro aparece no painel do gerador e na telemetria.","secao":"8 · Horímetro"},{"n":"2","t":"Óleo e filtros: 12 meses ou 1.300 h (o que vier antes). Rotor (impeller): inspeção a cada 12 meses e troca quando estiver gasto.","secao":"7 · Manutenção na agenda"}]}]},
  "estabilizador": {"status":"PRONTO","fonte":"Guia de bordo — Estabilizador Seakeeper","equip":"Estabilizador Seakeeper","modelo":"Seakeeper 3","perguntas":[{"q":"Como ligar antes de sair?","passos":[{"n":"1","t":"O estabilizador é alimentado pelo banco de 12 V. Para acelerar o volante, mantenha o banco carregado, com o carregador ligado ao gerador ou ao cais. Com tensão baixa no 12 V, o display avisa e o volante não acelera.","secao":"1 · Energia"},{"n":"2","t":"Ligue pelo display com antecedência, com o banco de 12 V carregado (carregador ligado ao gerador ou ao cais). O volante estabiliza a partir de cerca de 85 % da rotação de operação; o display mostra a rotação e indica quando a estabilização está disponível. Espere a indicação antes de sair.","secao":"2 · Ligar antes de sair"},{"n":"3","t":"O botão de estabilização liga e desliga o efeito sem parar o volante. Em manobra de marina, deixe a estabilização desligada se o display recomendar.","secao":"3 · Estabilizar"}]},{"q":"Como desligar ao atracar?","passos":[{"n":"1","t":"Desligue pelo display. O volante continua girando por muito tempo depois de desligado; mantenha o banco de 12 V ligado até o display indicar que parou.","secao":"4 · Desligar ao atracar"},{"n":"2","t":"Nunca abra tampas nem faça manutenção com o volante girando. Confira no display que a rotação está em zero antes de qualquer serviço.","secao":"5 · Segurança"}]},{"q":"Apareceu um alarme","passos":[{"n":"1","t":"Mensagens do display e o que fazer: tensão baixa no 12 V (ligue o carregador ao gerador ou ao cais); arrefecimento do estabilizador (confira a bomba e a válvula de fundo); temperatura alta (desligue e chame o técnico); volante abaixo de 85 % (sem estabilização até o volante acelerar). O display mostra a mensagem e o código: anote no diário com a hora.","secao":"6 · Alarmes"}]},{"q":"Manutenção","passos":[{"n":"1","t":"Anodo do trocador de calor: a cada 6 meses. Revisão anual pelo técnico de bordo.","secao":"7 · Manutenção na agenda"}]}]},
  "eletronicos": {"status":"PRONTO","fonte":"Guia de bordo — Eletrônicos Garmin, áudio Fusion e rádios Icom","equip":"Eletrônicos Garmin · Fusion · Icom","modelo":"GPSMAP 1243xsv · MS-UD755 · IC-M510","perguntas":[{"q":"Homem ao mar no plotter","passos":[{"n":"1","t":"Ao ver alguém cair na água, acione a função MOB do plotter: a posição fica marcada e o plotter mostra o rumo de volta. Siga o protocolo de emergência (homem ao mar).","secao":"1 · Plotter: homem ao mar"}]},{"q":"Piloto automático","passos":[{"n":"1","t":"Deixe o piloto automático em espera (standby) antes de manobrar na marina e sempre que houver gente na água. Engate só em área livre, com a rota conferida no plotter.","secao":"2 · Piloto automático"}]},{"q":"Alarme de âncora","passos":[{"n":"1","t":"Ao fundear, ative o alarme de âncora no plotter e defina o raio conforme a corrente lançada. O contador de corrente mostra os metros lançados no controle do guincho.","secao":"3 · Alarme de âncora"}]},{"q":"Rádio VHF: canal 16 e DSC","passos":[{"n":"1","t":"Mantenha o canal 16 em escuta permanente no rádio fixo. A dupla escuta acompanha o canal 16 e um canal de trabalho ao mesmo tempo. Deixe o rádio portátil carregado e pronto para uso.","secao":"4 · Rádio VHF: escuta"},{"n":"2","t":"O botão DISTRESS envia o alerta com a identificação programada no rádio: é o MMSI do rádio de bordo (etiqueta / Licença de Estação). Depois do alerta, faça o MAYDAY por voz no canal 16.","secao":"5 · Rádio VHF: DSC"}]},{"q":"Parear o celular no áudio Fusion","passos":[{"n":"1","t":"Para parear o celular: escolha a fonte Bluetooth no controle Fusion, deixe o aparelho visível e selecione o Fusion na lista de Bluetooth do celular. O volume é ajustado por zona.","secao":"6 · Áudio Fusion: Bluetooth"}]}]},
  "climatizacao": {"status":"PRONTO","fonte":"Guia de bordo — Climatização Webasto","equip":"Climatização Webasto","modelo":"FCF Platinum","perguntas":[{"q":"Como ligar a climatização?","passos":[{"n":"1","t":"Confira a válvula de fundo aberta e o filtro de água salgada limpo. Com energia AC no quadro elétrico, ligue a bomba de água salgada no painel e depois o controle da cabine.","secao":"1 · Ligar"},{"n":"2","t":"No controle de cada ambiente escolha frio, calor ou ventilação e ajuste a temperatura desejada. A unidade de 16.000 BTU/h atende o salão e as duas de 12.000 BTU/h, as cabines; ligue uma de cada vez para não sobrecarregar o quadro.","secao":"2 · Modos e temperatura"}]},{"q":"Alarme de fluxo","passos":[{"n":"1","t":"Alarme de fluxo ou de alta pressão quase sempre é falta de água salgada: filtro sujo, válvula de fundo fechada ou bomba desligada. Desligue a unidade, limpe o filtro e religue.","secao":"3 · Alarme de fluxo"}]},{"q":"Ar fraco na cabine","passos":[{"n":"1","t":"Fluxo de ar fraco na cabine: limpe o filtro de ar da unidade daquela cabine. Se continuar, registre no diário e chame a marina.","secao":"4 · Fluxo de ar fraco"}]},{"q":"Como desligar?","passos":[{"n":"1","t":"Desligue pelo controle das cabines e depois a bomba de água salgada. Ao deixar o barco, feche a válvula de fundo se a climatização não for usada.","secao":"5 · Desligar"}]}]}
 },
 "guias": {
  "g_motores": "Guia de bordo — Motores Cummins",
  "g_gerador": "Guia de bordo — Gerador Onan",
  "g_seakeeper": "Guia de bordo — Estabilizador Seakeeper",
  "g_clima": "Guia de bordo — Climatização Webasto",
  "g_eletronicos": "Guia de bordo — Eletrônicos Garmin, áudio Fusion e rádios Icom",
  "g_eletrico": "Guia de bordo — Sistema elétrico 24 V e 12 V",
  "g_dessalinizador": "Guia de bordo — Dessalinizador Schenker",
  "g_porao": "Guia de bordo — Bombas de porão Rule",
  "g_ancora": "Guia de bordo — Guincho e corrente Lewmar",
  "g_piloto": "Guia de bordo — Piloto automático Raymarine",
  "g_radar": "Guia de bordo — Radar Garmin",
  "g_ais": "Guia de bordo — AIS em-trak",
  "g_seafire": "Guia de bordo — Sistema fixo de incêndio",
  "g_epirb": "Guia de bordo — EPIRB",
  "checklist": "Checklist de bordo",
  "protocolo": "Protocolo de emergência — procedimento padrão"
 },
 "protocolos": {
  "rotulo": "procedimento padrão — confirmar com o protocolo de bordo",
  "fonte": "Protocolo de emergência — procedimento padrão · Drive › Capitão IA v2 › 07 Protocolos de emergência",
  "mmsiRadio": "MMSI do rádio de bordo (etiqueta / Licença de Estação)",
  "mmsiRotulo": "MMSI (cadastro do app)",
  "indicativo": "o da Licença de Estação (no rádio)",
  "plotter": "POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER · PESSOAS: CONTE AGORA",
  "hud": "POSIÇÃO · LEIA NO PLOTTER",
  "canal16": {"canal":"16","mhz":"156,800","fonte":"Protocolo de emergência — procedimento padrão · MAYDAY · canal 16"},
  "roteiro": ["MAYDAY, MAYDAY, MAYDAY","AQUI É CAPITÃO IA, CAPITÃO IA, CAPITÃO IA","MMSI — LEIA NA ETIQUETA DO RÁDIO (Licença de Estação)","POSIÇÃO — LEIA NO PLOTTER AGORA","NATUREZA DO PERIGO: ________","PESSOAS A BORDO: conte agora","AUXÍLIO NECESSÁRIO: ________","CÂMBIO"],
  "mob": ["Grite HOMEM AO MAR e o lado (bombordo ou boreste). Jogue a boia ou qualquer objeto que flutue.","Uma pessoa só aponta para quem caiu, sem perder de vista. Marque MOB no plotter.","Volte devagar, com o motor em neutro perto da pessoa (hélice). Se perder de vista: MAYDAY no canal 16 com a posição da marca MOB lida no plotter."],
  "seafire": {"passos":["Fogo no motor ou alarme do sistema fixo: desligue motores e gerador e corte a ventilação do motor.","Se o sistema não disparou sozinho e há fogo no motor, use o disparo manual.","Não abra o acesso ao motor depois da descarga: espere o tempo indicado na etiqueta do sistema e o motor esfriar.","Fogo pequeno fora do motor: extintor portátil na base das chamas, de costas para a saída.","Fogo que não apaga: MAYDAY no canal 16 e prepare o abandono."],"nota":"modelo, validade e acionamento: veja a etiqueta do equipamento"},
  "epirb": {"passos":["Só em perigo grave e iminente, depois do MAYDAY (ou sem rádio).","Acione conforme a etiqueta do equipamento e deixe a antena para cima, com céu aberto.","Leve o EPIRB para a balsa ou mantenha-o flutuando preso por um cabo. Não desligue até o resgate.","Disparo por engano: desligue e avise no canal 16."],"teste":["Teste da baliza (EPIRB): faça o autoteste conforme a etiqueta. O teste não envia alerta.","Confira na etiqueta a validade da bateria e do disparador hidrostático."],"nota":"modelo, validade e acionamento: veja a etiqueta do equipamento"},
  "alagamento": ["Água entrando: ligue as bombas de porão no manual, procure a entrada (válvulas de fundo, mangueiras, eixos) e feche o que puder. Água subindo mesmo assim: MAYDAY no canal 16."],
  "abandono": ["Abandono: só quando não houver como manter o barco. Antes, MAYDAY no canal 16. Coletes em todos; leve o EPIRB e o VHF portátil; embarque na balsa sem pular na água."],
  "oleo": ["Reduza para marcha lenta e confira o manômetro agora.","Compare BB e BE no mesmo giro: só um lado baixo aponta o motor.","Com o motor parado, procure vazamento e confira o nível de óleo na vareta.","Se continuar baixa, desligue o motor afetado, siga com o outro e chame a oficina dos motores."],
  "salvatagem": "Em perigo agora: SOS do app e VHF canal 16. Coletes: um por pessoa — conte as pessoas a bordo agora (lotação: veja a placa de lotação). Balsa, coletes, boias, extintores e sinalizadores: no local da placa de salvatagem e do plano de segurança de bordo — confira na saída.",
  "panpan": "Urgência sem perigo imediato de vida (pane, sem governo, alguém ferido sem risco de morte): PAN-PAN, PAN-PAN, PAN-PAN no canal 16, no mesmo formato da chamada MAYDAY.",
  "dsc": "O botão DISTRESS envia o alerta com a identificação programada no rádio: é o MMSI do rádio de bordo (etiqueta / Licença de Estação). Depois do alerta, faça o MAYDAY por voz no canal 16."
 }
};
/* CapitaoAgora — rodapé do capitao-dados.js (CONTRATO-DADOS §1.23, §4.1): anexado pelo gerar_demo.py, não editar lá.
   O relógio do aparelho no fuso da embarcação refaz os prazos; o D continua só dado. Nada aqui escreve no D.snapshot. */
(function () {
  try {
    var D = window.CapitaoDados, MIN = 60000, DIA = 86400000, EM_SOS = false;
    if (!D) return;
    try { EM_SOS = /SOS-/.test(location.pathname); } catch (e) {}
    var FUSO = (D.embarcacao && D.embarcacao.fuso) || 'America/Sao_Paulo';
    var BORDO = { d01: 1, d02: 1 };   // linhas do diário contadas no dia de bordo (as outras, em hoje)
    var A = window.CapitaoAgora = { fuso: FUSO, assinatura: '' };
    function p2(n) { return (n < 10 ? '0' : '') + n; }

    // fuso: minutos (local − UTC), com cache por hora; sem Intl, o de Brasília (sem horário de verão desde 2019)
    var dtf = null, cache = {};
    function off(ms) {
      var h = Math.floor(ms / 3600000), r = -180;
      if (cache[h] !== undefined) return cache[h];
      try {
        dtf = dtf || new Intl.DateTimeFormat('en-CA', { timeZone: FUSO, hour12: false, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
        var ps = dtf.formatToParts(new Date(h * 3600000)), v = {};
        for (var i = 0; i < ps.length; i++) v[ps[i].type] = parseInt(ps[i].value, 10);
        r = Math.round((Date.UTC(v.year, v.month - 1, v.day, v.hour % 24, v.minute, v.second) - h * 3600000) / MIN);
        if (!isFinite(r)) r = -180;
      } catch (e) { r = -180; }
      return (cache[h] = r);
    }
    function diaN(ms) { return Math.floor((ms + off(ms) * MIN) / DIA); }   // dia do calendário no fuso, em dias desde 1970
    function ymd(n) { var d = new Date(n * DIA); return [d.getUTCFullYear(), d.getUTCMonth() + 1, d.getUTCDate()]; }
    function br(n) { var x = ymd(n); return p2(x[2]) + '/' + p2(x[1]) + '/' + x[0]; }
    function isoDia(n) { var x = ymd(n); return x[0] + '-' + p2(x[1]) + '-' + p2(x[2]); }
    function ddmm(n) { return br(n).slice(0, 5); }
    function deData(s) {   // 'dd/mm/aaaa' ou 'aaaa-mm-dd' → dia desde 1970 (data absoluta); NaN se não for data
      var m = /^(\d\d)\/(\d\d)\/(\d{4})$/.exec(s || ''), n = m ? [m[3], m[2], m[1]] : /^(\d{4})-(\d\d)-(\d\d)/.exec(s || '');
      if (n && !m) n = [n[1], n[2], n[3]];
      return n ? Math.floor(Date.UTC(+n[0], +n[1] - 1, +n[2]) / DIA) : NaN;
    }
    function isoLocal(n, hhmm, seg) {   // 'AAAA-MM-DDTHH:MM:SS-03:00': hora de parede do fuso naquele dia
      var x = ymd(n), hm = /^\d\d:\d\d$/.test(hhmm) ? hhmm : '00:00', parede = Date.UTC(x[0], x[1] - 1, x[2], +hm.slice(0, 2), +hm.slice(3), seg);
      var o = off(parede - off(parede) * MIN), a = Math.abs(o);
      return isoDia(n) + 'T' + hm + ':' + p2(seg) + (o < 0 ? '-' : '+') + p2(Math.floor(a / 60)) + ':' + p2(a % 60);
    }

    // âncora do dia de bordo: 07:00 de hoje no fuso (antes das 07:00, a de ontem). A mesma função para o rebase e para o replay
    function ancMin() {
      var m = EM_SOS ? null : /^(\d\d):(\d\d)$/.exec((D.replay && D.replay.ancora_hora) || '');   // o SOS não lê o replay
      return m ? +m[1] * 60 + +m[2] : 420;
    }
    function ancora(ms) {
      var o = off(ms), l = ms + o * MIN, parede = Math.floor(l / DIA) * DIA + ancMin() * MIN;   // parede: relógio do fuso lido como UTC
      if (l < parede) parede -= DIA;
      return parede - off(parede - o * MIN) * MIN;
    }

    // prazos (port do status_prazo do gerador)
    function prazoDe(n) {
      var i = n < 0 ? 0 : n <= 30 ? 1 : n <= 60 ? 2 : n <= 90 ? 3 : 4;
      return { st: ['ATRASADA', 'D-30', 'D-60', 'D-90', 'EM DIA'][i], rot: i ? 'D-' + n : 'ATRASADA · ' + (-n) + ' D', tom: ['crit', 'warn', 'tele', 'accent', 'ok'][i] };
    }
    function docDe(n) { return { st: n < 0 ? 'VENCIDO' : n <= 90 ? 'VENCE EM ' + n + ' D' : 'EM DIA', tom: prazoDe(n).tom }; }

    // rebase: só campos derivados, de deslocamentos que nunca reescreve; idempotente; as listas mudam no lugar (sort/splice)
    function dnDe(x, hoje) { var n = typeof x.venceEm === 'number' ? x.venceEm : deData(x.vence) - hoje; return n; }   // NaN sem prazo
    function segundos(lista) {   // mesmo dia e mesma hora: a linha de cima (mais nova) ganha 1 s a mais, para o iso seguir a ordem
      var ch = lista.map(function (x) { return x && typeof x.diasAtras === 'number' ? (BORDO[x.id] ? 'b' : 'h') + x.diasAtras + x.h : ''; }), vistos = {};
      return ch.map(function (k) {
        if (!k) return 0;
        vistos[k] = (vistos[k] || 0) + 1;
        return ch.filter(function (c) { return c === k; }).length - vistos[k];
      });
    }
    function rebase(ms, forca) {
      try {
        ms = typeof ms === 'number' && isFinite(ms) ? ms : Date.now();
        var hojeN = diaN(ms), anc = ancora(ms), bordoN = diaN(anc), assin = br(hojeN) + '|' + br(bordoN), n;
        if (!forca && A.assinatura === assin) return false;
        A.relogio = { ms: ms, hoje: br(hojeN), hojeIso: isoDia(hojeN), diaBordo: br(bordoN), diaBordoIso: isoDia(bordoN), ancoraMs: anc, off: off(ms) };
        var prazo = function (x, fmt) {   // vence (se veio de venceEm), dn, st, rot, tom
          var n = dnDe(x, hojeN), d;
          if (isNaN(n)) return;
          if (typeof x.venceEm === 'number') x.vence = fmt(hojeN + n);
          d = prazoDe(n); x.dn = n; x.st = d.st; x.rot = d.rot; x.tom = d.tom;
        };
        (D.agenda || []).forEach(function (t) { if (typeof t.ultimaHa === 'number') t.ultima = br(hojeN - t.ultimaHa); prazo(t, br); });
        (D.agenda || []).sort(function (a, b) { return (a.dn - b.dn) || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0); });
        (D.tarefasEquipe || []).forEach(function (t) { prazo(t, isoDia); });
        (D.documentos || []).forEach(function (x) {
          if (typeof x.emitidoHa === 'number') x.emitido = br((x.id === 'nf-abast' || /^ab-/.test(String(x.ref)) ? bordoN : hojeN) - x.emitidoHa);
          if (isNaN(n = dnDe(x, hojeN))) return;   // sem prazo (a nota fiscal): vence, dn e o st de prazo ficam de fora; o st gerado é dela
          if (typeof x.venceEm === 'number') x.vence = br(hojeN + n);
          x.dn = n; x.st = docDe(n).st;
        });
        var di = D.diario || [], seg = segundos(di);
        di.forEach(function (x, i) {
          if (!x || typeof x.diasAtras !== 'number') return;
          var n = (BORDO[x.id] ? bordoN : hojeN) - x.diasAtras;
          x.d = ddmm(n); x.iso = isoLocal(n, x.h, seg[i]);
        });
        (D.abastecimentos || []).forEach(function (a) { if (a && typeof a.diasAtras === 'number') a.d = br(bordoN - a.diasAtras); });
        (D.serie24v || []).forEach(function (s) { if (s && typeof s.diasAtras === 'number') s.d = ddmm(bordoN - s.diasAtras); });
        D.versao = br(hojeN);
        A.assinatura = assin;
        return true;
      } catch (e) { return false; }
    }

    // formatadores: o valor como a tela mostra, floor(x·10^c + 0,5) / 10^c, sem -0
    function arred(x, c) { var p = Math.pow(10, c || 0), v = Math.floor(x * p + 0.5) / p; return v === 0 ? 0 : v; }
    function nb(x, c, mil) {
      if (typeof x !== 'number' || !isFinite(x)) return null;
      var v = arred(x, c), s = Math.abs(v).toFixed(c || 0).split('.');
      if (mil) s[0] = s[0].replace(/(\d)(?=(\d{3})+$)/g, '$1.');
      return (v < 0 ? '-' : '') + s.join(',');
    }
    function grau3(x) { return typeof x === 'number' && isFinite(x) ? ('00' + (Math.round(((x % 360) + 360) % 360) % 360)).slice(-3) : null; }
    function hora(ms, comSeg) { var d = new Date(ms + off(ms) * MIN); return p2(d.getUTCHours()) + ':' + p2(d.getUTCMinutes()) + (comSeg ? ':' + p2(d.getUTCSeconds()) : ''); }
    function grausMin(v, pos, neg, g) {   // 59,995′ já é o grau seguinte
      var a = Math.abs(v), gr = Math.floor(a), mi = Math.round((a - gr) * 6000) / 100;
      if (mi >= 60) { gr += 1; mi = 0; }
      return ('000' + gr).slice(-g) + '°' + (mi < 10 ? '0' : '') + mi.toFixed(2).replace('.', ',') + "'" + (v < 0 ? neg : pos);
    }
    function coord(lat, lon) { return grausMin(lat, 'N', 'S', 2) + ' ' + grausMin(lon, 'E', 'W', 3); }   // só para tela
    function campo(q, nome) {   // o valor como a tela mostra, ou null se falta: o leitor mantém o seu SD/SL
      var v = q ? q[nome] : null, c = D.campos && D.campos[nome];
      if (typeof v === 'string') return v;
      if (typeof v !== 'number' || !isFinite(v)) return null;
      return c && c.ang ? grau3(v) : nb(v, c && typeof c.casas === 'number' ? c.casas : 0, c && c.mil);
    }

    // trava do ar e da água: presos na máx/mín de hoje da leitura salva do clima (§2.5 do PROMPT); devolve cópia, a origem não muda
    function copia(o, extra) {
      var c = {}, k;
      for (k in o) if (Object.prototype.hasOwnProperty.call(o, k)) c[k] = o[k];
      for (k in extra || {}) c[k] = extra[k];
      return c;
    }
    // registro do aparelho: JSON válido de OUTRA forma ('{}' onde se espera lista; lista, texto ou número onde se espera mapa) vale como vazio,
    // para um valor estranho num campo nunca zerar as outras contas (o cérebro faz o mesmo: loadDiario e loadAbast filtram Array.isArray)
    function local(chave, vazio) {
      try {
        var v = JSON.parse(localStorage.getItem(chave) || 'null'), lista = Array.isArray(vazio);
        if (v == null || (lista ? !Array.isArray(v) : (typeof v !== 'object' || Array.isArray(v)))) return vazio;
        return v;
      } catch (e) { return vazio; }
    }
    function trava(q) {
      var c = copia(q), v = local('capitao.clima.v1', null);
      if (v && A.relogio && v.dia === A.relogio.hojeIso && typeof v.max === 'number' && typeof v.min === 'number' && v.min <= v.max) {
        ['temp_ar_externo_c', 'temp_agua_c'].forEach(function (f) { if (typeof c[f] === 'number') c[f] = Math.min(v.max, Math.max(v.min, c[f])); });
      }
      return c;
    }

    // contagens: tarefas abertas (agenda e equipe, geradas e do aparelho; as executadas não contam), documentos e pendências do diário
    function contagens() {
      var c = { atrasadas: 0, d30: 0, d60: 0, d90: 0, emDia: 0, docsVencidos: 0, docsVencem90: 0, pendencias: 0, tarefasEquipe: 0 };
      try {
        var hoje = diaN(A.relogio ? A.relogio.ms : Date.now()), feitas = local('capitao.executado.v1', {}), acoes = {}, linhas = local('capitao.diario.v1', []), eq = [];
        var conta = function (dn) { c[dn < 0 ? 'atrasadas' : dn <= 30 ? 'd30' : dn <= 60 ? 'd60' : dn <= 90 ? 'd90' : 'emDia']++; };
        (D.agenda || []).forEach(function (t) { if (!feitas[t.id] && typeof t.dn === 'number') conta(t.dn); });
        (D.tarefasEquipe || []).forEach(function (t) { eq.push({ id: t.id, dn: t.dn }); });
        local('capitao.tarefas.v1', []).forEach(function (t) { if (t && !isNaN(deData(t.vence))) eq.push({ id: t.id, dn: deData(t.vence) - hoje }); });
        eq.forEach(function (t) { if (!feitas[t.id] && typeof t.dn === 'number') { conta(t.dn); c.tarefasEquipe++; } });
        (D.documentos || []).forEach(function (x) { if (typeof x.dn === 'number') { if (x.dn < 0) c.docsVencidos++; else if (x.dn <= 90) c.docsVencem90++; } });
        // pendência aberta: linha com pend (gerada, pelo id; do aparelho, pelo iso) cuja última ação por alvo (resolve/reabre) não é "resolve"
        linhas.slice().reverse().forEach(function (l) { if (l && (l.acao === 'resolve' || l.acao === 'reabre') && l.alvo) acoes[l.alvo] = l.acao; });
        (D.diario || []).forEach(function (x) { if (x.pend && acoes[x.id] !== 'resolve') c.pendencias++; });
        linhas.forEach(function (l) { if (l && l.pend && !l.acao && acoes[l.iso] !== 'resolve') c.pendencias++; });
      } catch (e) {}
      return c;
    }

    // instante: o quadro único que telas, cérebro e IA leem. Nunca lança erro; em /SOS-/ é null, antes de qualquer leitura (§1.3).
    // tend, txt e resumo entram com o replay e o D.campos (Fases 2 a 4); o calc sai daqui e vale para as três fontes.
    var guardado = null;
    function calcular(q) {
      var o = { faltam: {} }, cons = D.consumo || {}, cr = cons.cruzeiro || {}, ln = cons.lenta || {}, cap = D.embarcacao && D.embarcacao.tanques && D.embarcacao.tanques.diesel_l;
      var util = typeof q.diesel_litros === 'number' ? q.diesel_litros * (1 - (typeof D.reserva === 'number' ? D.reserva : 0.1)) : null, ab = (D.abastecimentos || [])[0];
      if (util != null && typeof cap === 'number' && cap > 0) o.diesel_pct = arred(q.diesel_litros / cap * 100, 1);
      if (util != null && cr.lph > 0 && cr.nos > 0 && ln.lph > 0) o.autonomia = { horas: arred(util / cr.lph, 1), mn: Math.floor(util / cr.lph * cr.nos + 0.5), lenta: Math.floor(util / ln.lph + 0.5) };
      if (util != null && typeof cap === 'number' && ab && typeof ab.nivelDepois === 'number') {
        o.desdeAbast = { litros: Math.floor(ab.nivelDepois / 100 * cap - q.diesel_litros + 0.5), desde: ab.d };
        if (ab.h) o.desdeAbast.h = ab.h;
      }
      (D.agenda || []).forEach(function (t) {
        var h = t.horas, a = null;
        if (!h || !h.campos || typeof h.limite !== 'number') return;
        h.campos.forEach(function (f) { if (typeof q[f] === 'number' && (a == null || q[f] > a)) a = q[f]; });
        if (a != null) o.faltam[t.id] = arred(h.limite - a, 1);
      });
      return o;
    }
    function instante() {
      try {
        if (/SOS-/.test(location.pathname)) return null;
        var R = window.CapitaoReplay, T = window.CapitaoTelemetria, ms = Date.now(), o = null, x, i;
        if (R && typeof R.agora === 'function') { x = R.agora(); if (typeof x === 'number' && isFinite(x)) ms = x; }
        var clima = ''; try { clima = localStorage.getItem('capitao.clima.v1') || ''; } catch (e) {}
        var chave = Math.floor(ms / 1000) + '|' + A.assinatura + '|' + (R && typeof R.fixo === 'function' ? R.fixo() : '') + '|' + clima;   // guardado por segundo
        if (guardado && guardado.chave === chave) return guardado.i;
        if (T && typeof T.atual === 'function' && (x = T.atual())) o = { q: x, fonte: x.simulado ? 'replay' : 'coletor' };
        if (!o && R && typeof R.em === 'function' && (x = R.em(ms))) o = { q: x, fonte: 'replay' };
        if (!o && D.snapshot && D.snapshot.quadro) o = { q: D.snapshot.quadro, fonte: 'snapshot', reserva: true };
        if (!o) return null;
        var q = o.fonte !== 'coletor' && D.simulacao === true ? trava(o.q) : copia(o.q);   // leitura real nunca é presa
        var t = o.reserva ? Date.parse(q.timestamp_utc) : ms, hh = hora(isNaN(t) ? ms : t, true), lei = ddmm(diaN(isNaN(t) ? ms : t)) + ' ' + hh.slice(0, 5);
        i = { ms: ms, q: q, fonte: o.fonte, hora: hh, hhmm: hh.slice(0, 5) };
        i.fonteTxt = o.reserva ? 'coletor NMEA \u00b7 leitura de ' + lei : o.fonte === 'coletor' ? 'coletor NMEA \u00b7 ao vivo ' + hh : 'telemetria ao vivo \u00b7 ' + hh;
        i.selo = o.reserva ? { tom: 'warn', texto: '\u00daLTIMA LEITURA \u00b7 ' + lei } : { tom: 'ok', texto: 'AO VIVO \u00b7 ' + hh };
        if (o.fonte === 'replay' && R) {
          if (typeof R.t === 'function') i.seg = R.t(ms);
          if (typeof R.fase === 'function') i.fase = R.fase(ms);
        }
        i.calc = calcular(q);
        guardado = { chave: chave, i: i };
        return i;
      } catch (e) { return null; }
    }

    A.off = off; A.ancora = ancora; A.prazoDe = prazoDe; A.docDe = docDe; A.rebase = rebase; A.trava = trava; A.contagens = contagens; A.instante = instante;
    A.fmt = { arred: arred, nb: nb, mil: function (x) { return nb(x, 0, true); }, grau3: grau3, hora: hora, coord: coord, campo: campo };
    rebase(Date.now());

    // Dia de bordo (só com simulacao: true), numa microtarefa: roda depois do arquivo inteiro, para a injeção de teste "simulacao = false"
    // no fim dele valer. Insere por id (rodar de novo substitui) e nas mesmas listas (splice); nunca grava no aparelho. Em /SOS-/ sai
    // antes de ler a flag: o SOS nunca lê D.simulacao.
    function poe(lista, item, pos) {
      for (var i = 0; i < lista.length; i++) if (lista[i] && lista[i].id === item.id) { lista.splice(i, 1, item); return; }
      if (pos >= 0 && pos <= lista.length) lista.splice(pos, 0, item); else lista.push(item);
    }
    function insereDiaDeBordo() {
      var B = D.replay && D.replay.diaDeBordo, k;
      if (!B) return;
      D.abastecimentos = D.abastecimentos || []; D.diario = D.diario || []; D.documentos = D.documentos || [];
      if (B.abastecimento) for (k = 0; k < (B.dias || 0); k++) poe(D.abastecimentos, copia(B.abastecimento, { id: 'ab-' + k, diasAtras: k }), k);
      (B.diario || []).forEach(function (l, j) { poe(D.diario, copia(l), j); });
      if (B.documento) poe(D.documentos, copia(B.documento), -1);
    }
    Promise.resolve().then(function () {
      try {
        if (/SOS-/.test(location.pathname)) return;
        if (D.simulacao === true) { insereDiaDeBordo(); rebase(Date.now(), true); }
      } catch (e) {}
    });
  } catch (e) {}
})();
