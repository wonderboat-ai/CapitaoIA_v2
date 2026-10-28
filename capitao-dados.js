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
  "arquivos": {"leiame":"LEIA-ME — Capitão IA v2","g_motores":"Guia de bordo — Motores Cummins","g_gerador":"Guia de bordo — Gerador Onan","g_seakeeper":"Guia de bordo — Estabilizador Seakeeper","g_clima":"Guia de bordo — Climatização Webasto","g_eletronicos":"Guia de bordo — Eletrônicos Garmin, áudio Fusion e rádios Icom","g_eletrico":"Guia de bordo — Sistema elétrico 24 V e 12 V","g_dessalinizador":"Guia de bordo — Dessalinizador Schenker","g_porao":"Guia de bordo — Bombas de porão Rule","g_ancora":"Guia de bordo — Guincho e corrente Lewmar","g_piloto":"Guia de bordo — Piloto automático Raymarine","g_radar":"Guia de bordo — Radar Garmin","g_ais":"Guia de bordo — AIS em-trak","g_seafire":"Guia de bordo — Sistema fixo de incêndio","g_epirb":"Guia de bordo — EPIRB","checklist":"Checklist de bordo","inventario":"Inventário de bordo","documentos":"Controle de documentos","agenda":"Agenda preditiva","diario":"Diário de bordo","snapshot":"Leitura do coletor NMEA — 26-09-2026 10h12.json","serie":"Série do coletor NMEA — 150 s.csv","formato":"Formato do quadro do coletor.csv","abast":"Registro de abastecimento","protocolo":"Protocolo de emergência — procedimento padrão"}
 },
 "equipamentos": [{"id":"motores","nome":"Motores","fabricante":"Cummins","modelo":"QSB6.7 305","qtd":2,"lados":"BB e BE","guia":"g_motores","palavras":["cummins","kamins","comins","qsb","motor","motores"],"nominal":{"potencia_cv":305,"rpm_max":2600,"rpm_cruzeiro":2050,"rpm_lenta":700,"transmissao":"eixo"},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"gerador","nome":"Gerador","fabricante":"Onan","modelo":"QD 9","qtd":1,"guia":"g_gerador","palavras":[" onan ","gerador","qd 9","qd nove"],"nominal":{"kw":9,"hz":60,"rpm":1800},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"estabilizador","nome":"Estabilizador giroscópico","fabricante":"Seakeeper","modelo":"Seakeeper 3","qtd":1,"guia":"g_seakeeper","palavras":["seakeeper","sikiper","giroscopio","estabilizador"],"nominal":{"pct_estabiliza":85},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"climatizacao","nome":"Climatização","fabricante":"Webasto","modelo":"FCF Platinum 16000 e 12000","qtd":3,"guia":"g_clima","palavras":["webasto","vebasto","fcf","platinum","climatizacao","ar condicionado"],"nominal":{"btu_h_total":40000},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"eletronicos","nome":"Plotters","fabricante":"Garmin","modelo":"GPSMAP 1243xsv","qtd":2,"guia":"g_eletronicos","palavras":["garmin","gpsmap","plotter","plotters","chartplotter"],"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"audio","nome":"Áudio","fabricante":"Fusion","modelo":"MS-UD755","qtd":1,"guia":"g_eletronicos","palavras":["fusion","audio"," som ","bluetooth"],"nominal":{"zonas":2},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"vhf","nome":"Rádios VHF","fabricante":"Icom","modelo":"IC-M510 e IC-M37","qtd":2,"guia":"g_eletronicos","palavras":["vhf","radio vhf","icom","canal 16"],"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"epirb","nome":"EPIRB","fabricante":"Ocean Signal","modelo":"SafeSea E100G","qtd":1,"guia":"g_epirb","palavras":["epirb","radiobaliza","baliza","ipirb"],"validade":"doc-epirb","seguranca":true,"nota":"modelo, validade e acionamento: veja a etiqueta do equipamento","fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"seafire","nome":"Sistema fixo de supressão de incêndio","fabricante":"Seafire","modelo":"FD 300M","qtd":1,"guia":"g_seafire","palavras":["seafire","sea fire","sistema de incendio","supressao"],"validade":"seafire-inspecao","seguranca":true,"nota":"modelo, validade e acionamento: veja a etiqueta do equipamento","fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"dessalinizador","nome":"Dessalinizador","fabricante":"Schenker","modelo":"Zen 30","qtd":1,"guia":"g_dessalinizador","palavras":["schenker","shenker","zen 30","dessalinizador","osmose"],"nominal":{"lph":30},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"porao","nome":"Bombas de porão","fabricante":"Rule","modelo":"Rule 2000 (24 V)","qtd":2,"lados":"BB e BE","guia":"g_porao","palavras":[" rule ","bomba de porao","bombas de porao","porao"],"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"ancora","nome":"Guincho e contador de corrente","fabricante":"Lewmar","modelo":"V2 · contador AA150","qtd":1,"guia":"g_ancora","palavras":["lewmar","leumar","guincho","ancora","contador de corrente","molinete"],"nominal":{"corrente_m":60},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"piloto","nome":"Piloto automático","fabricante":"Raymarine","modelo":"Evolution EV-1 · ACU-400","qtd":1,"guia":"g_piloto","palavras":["raymarine","reimarine","evolution","piloto automatico","piloto"],"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"radar","nome":"Radar","fabricante":"Garmin","modelo":"GMR 24 xHD3","qtd":1,"guia":"g_radar","palavras":["radar","gmr","xhd3","domo"],"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"ais","nome":"AIS (classe B)","fabricante":"em-trak","modelo":"B954","qtd":1,"guia":"g_ais","palavras":[" ais ","em-trak","emtrak","transponder"],"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"},{"id":"eletrico","nome":"Baterias (24 V e 12 V)","fabricante":"Victron Energy","modelo":"AGM Super Cycle 12 V 230 Ah","qtd":8,"guia":"g_eletrico","palavras":["victron","vitron","bateria","baterias","banco de baterias"," agm "],"nominal":{"bancos":[{"id":"servico","v":24,"n":4,"campo":"bateria_0_tensao_v"},{"id":"partida","v":24,"n":2,"campo":"bateria_1_tensao_v"},{"id":"eletronica","v":12,"n":2,"campo":"bateria_2_tensao_v"}]},"fonte":"Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo"}],
 "equipNota": "Inventário de bordo · 16 equipamentos · Drive › Capitão IA v2 › 01 Manuais e guias de bordo",
 "campos": {
  "timestamp_utc": {"rotulo":"Hora da leitura (UTC)","origem":"relógio"},
  "lat": {"rotulo":"Latitude","un":"°","casas":5,"origem":"rota"},
  "lon": {"rotulo":"Longitude","un":"°","casas":5,"origem":"rota"},
  "cog_graus": {"rotulo":"Rumo sobre o fundo (COG)","un":"°","casas":0,"origem":"rota","ang":true},
  "proa_graus": {"rotulo":"Proa","un":"°","casas":0,"origem":"derivado","ang":true},
  "piloto_rumo": {"rotulo":"Rumo do piloto automático","un":"°","casas":0,"origem":"rota","ang":true},
  "leme_graus": {"rotulo":"Leme","un":"°","casas":1,"origem":"laço","desc":"bombordo negativo, boreste positivo"},
  "sog_nos": {"rotulo":"Velocidade sobre o fundo (SOG)","un":"nós","casas":1,"origem":"laço"},
  "stw_nos": {"rotulo":"Velocidade na água (STW)","un":"nós","casas":1,"origem":"derivado"},
  "profundidade_m": {"rotulo":"Profundidade","un":"m","casas":1,"origem":"rota"},
  "motor_bb_rpm": {"rotulo":"Rotação do motor BB","un":"rpm","casas":0,"origem":"laço","mil":true},
  "motor_be_rpm": {"rotulo":"Rotação do motor BE","un":"rpm","casas":0,"origem":"laço","mil":true},
  "motor_bb_oleo_bar": {"rotulo":"Pressão de óleo BB","un":"bar","casas":1,"origem":"laço"},
  "motor_be_oleo_bar": {"rotulo":"Pressão de óleo BE","un":"bar","casas":1,"origem":"laço"},
  "motor_bb_arref_c": {"rotulo":"Arrefecimento do motor BB","un":"°C","casas":1,"origem":"laço"},
  "motor_be_arref_c": {"rotulo":"Arrefecimento do motor BE","un":"°C","casas":1,"origem":"laço"},
  "motor_bb_carga_pct": {"rotulo":"Carga do motor BB","un":"%","casas":0,"origem":"laço"},
  "motor_be_carga_pct": {"rotulo":"Carga do motor BE","un":"%","casas":0,"origem":"laço"},
  "marcha": {"rotulo":"Marcha","origem":"fixo"},
  "consumo_lph": {"rotulo":"Consumo dos dois motores","un":"L/h","casas":1,"origem":"laço"},
  "diesel_litros": {"rotulo":"Diesel a bordo","un":"L","casas":0,"origem":"contador","sentido":-1,"mil":true},
  "diesel_bb_pct": {"rotulo":"Tanque de diesel BB","un":"%","casas":1,"origem":"derivado"},
  "diesel_be_pct": {"rotulo":"Tanque de diesel BE","un":"%","casas":1,"origem":"derivado"},
  "distancia_mn": {"rotulo":"Distância percorrida no dia de bordo","un":"mn","casas":1,"origem":"contador","sentido":1},
  "motor_bb_horimetro_h": {"rotulo":"Horímetro do motor BB","un":"h","casas":1,"origem":"contador","sentido":1,"mil":true},
  "motor_be_horimetro_h": {"rotulo":"Horímetro do motor BE","un":"h","casas":1,"origem":"contador","sentido":1,"mil":true},
  "gerador_ativo": {"rotulo":"Gerador ligado","un":"liga/desliga","casas":0,"origem":"fixo"},
  "gerador_kw": {"rotulo":"Carga do gerador","un":"kW","casas":1,"origem":"laço"},
  "gerador_horimetro_h": {"rotulo":"Horímetro do gerador","un":"h","casas":1,"origem":"contador","sentido":1,"mil":true},
  "seakeeper_ativo": {"rotulo":"Estabilizador ligado","un":"liga/desliga","casas":0,"origem":"fixo"},
  "seakeeper_volante_rpm": {"rotulo":"Volante do estabilizador","un":"rpm","casas":0,"origem":"laço","mil":true},
  "seakeeper_volante_pct": {"rotulo":"Volante do estabilizador","un":"%","casas":0,"origem":"laço"},
  "bateria_0_tensao_v": {"rotulo":"Banco de serviço de 24 V","un":"V","casas":2,"origem":"laço"},
  "bateria_1_tensao_v": {"rotulo":"Banco de partida de 24 V","un":"V","casas":2,"origem":"laço"},
  "bateria_2_tensao_v": {"rotulo":"Banco de 12 V","un":"V","casas":2,"origem":"laço"},
  "tanque_agua_pct": {"rotulo":"Tanque de água doce","un":"%","casas":1,"origem":"contador","sentido":-1},
  "tanque_cinzas_pct": {"rotulo":"Tanque de águas cinzas","un":"%","casas":1,"origem":"contador","sentido":1},
  "tanque_negras_pct": {"rotulo":"Tanque de águas negras","un":"%","casas":1,"origem":"contador","sentido":1},
  "porao_bb_nivel": {"rotulo":"Nível do porão BB","un":"cm","casas":1,"origem":"laço"},
  "porao_be_nivel": {"rotulo":"Nível do porão BE","un":"cm","casas":1,"origem":"laço"},
  "bomba_porao_ciclos": {"rotulo":"Ciclos das bombas de porão na última hora","un":"ciclos","casas":0,"origem":"fixo"},
  "ancora_estado": {"rotulo":"Âncora","origem":"fixo"},
  "ondas_m": {"rotulo":"Ondas","un":"m","casas":1,"origem":"laço"},
  "vento_verdadeiro_nos": {"rotulo":"Vento verdadeiro","un":"nós","casas":1,"origem":"laço"},
  "vento_verdadeiro_angulo": {"rotulo":"Vento verdadeiro (de onde vem)","un":"°","casas":0,"origem":"laço","ang":true,"desc":"em relação ao norte verdadeiro"},
  "vento_aparente_nos": {"rotulo":"Vento aparente","un":"nós","casas":1,"origem":"derivado"},
  "vento_aparente_angulo": {"rotulo":"Vento aparente (em relação à proa)","un":"°","casas":0,"origem":"derivado","desc":"de -180 a 180; positivo a boreste"},
  "pressao_barometrica_hpa": {"rotulo":"Pressão atmosférica","un":"hPa","casas":1,"origem":"laço","mil":true},
  "temp_ar_externo_c": {"rotulo":"Temperatura do ar","un":"°C","casas":1,"origem":"laço"},
  "temp_agua_c": {"rotulo":"Temperatura da água","un":"°C","casas":1,"origem":"laço"},
  "temp_praca_maquinas_c": {"rotulo":"Temperatura da praça de máquinas","un":"°C","casas":0,"origem":"laço"},
  "jogo_graus": {"rotulo":"Jogo (balanço de bordo a bordo)","un":"°","casas":1,"origem":"laço"},
  "caimento_graus": {"rotulo":"Caimento (inclinação de proa a popa)","un":"°","casas":1,"origem":"laço"},
  "gps_satelites": {"rotulo":"Satélites do GPS","un":"satélites","casas":0,"origem":"fixo"},
  "climatizacao_ativa": {"rotulo":"Climatização ligada","un":"liga/desliga","casas":0,"origem":"fixo"},
  "dessalinizador_ativo": {"rotulo":"Dessalinizador ligado","un":"liga/desliga","casas":0,"origem":"fixo"},
  "radar_ativo": {"rotulo":"Radar transmitindo","un":"liga/desliga","casas":0,"origem":"fixo"},
  "ais_alvos": {"rotulo":"Alvos do AIS","un":"alvos","casas":0,"origem":"fixo"},
  "estado": {"rotulo":"Estado","origem":"fixo"},
  "local": {"rotulo":"Onde está","origem":"rota"},
  "destino": {"rotulo":"Destino","origem":"rota"},
  "destino_mn": {"rotulo":"Distância ao destino","un":"mn","casas":1,"origem":"rota"},
  "wp_proximo": {"rotulo":"Próximo ponto da rota","origem":"rota"},
  "wp_mn": {"rotulo":"Distância ao próximo ponto","un":"mn","casas":1,"origem":"rota"},
  "eta": {"rotulo":"Chegada prevista (hora local)","origem":"rota"},
  "alarmes": {"rotulo":"Alarmes ativos","origem":"janela"}
 },
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
  "gerador": {"estado":"ligado desde 09:35","horas":1236.4,"kw":5.6,"hora":"26/09 10:12"},
  "seakeeper": {"estado":"ligado","volante_rpm":8420,"volante_pct":100,"hora":"26/09 10:12"},
  "porao": {"bb_cm":1.2,"be_cm":0.9,"ciclos_h":0},
  "ancora": {"estado":"lançada","cabo_m":30},
  "quadro": {"timestamp_utc":"2026-09-26T13:12:00Z","lat":-26.993,"lon":-48.614,"cog_graus":71,"proa_graus":71,"leme_graus":0,"sog_nos":0.1,"stw_nos":0.3,"profundidade_m":7.4,"motor_bb_rpm":0,"motor_be_rpm":0,"motor_bb_oleo_bar":0,"motor_be_oleo_bar":0,"motor_bb_arref_c":54,"motor_be_arref_c":53,"motor_bb_carga_pct":0,"motor_be_carga_pct":0,"marcha":"neutro","consumo_lph":0,"diesel_litros":848,"diesel_bb_pct":54.0,"diesel_be_pct":52.0,"distancia_mn":11.6,"motor_bb_horimetro_h":412.6,"motor_be_horimetro_h":409.8,"gerador_ativo":true,"gerador_kw":5.6,"gerador_horimetro_h":1236.4,"seakeeper_ativo":true,"seakeeper_volante_rpm":8420,"seakeeper_volante_pct":100,"bateria_0_tensao_v":27.42,"bateria_1_tensao_v":27.2,"bateria_2_tensao_v":13.18,"tanque_agua_pct":68.5,"tanque_cinzas_pct":21.0,"tanque_negras_pct":34.5,"porao_bb_nivel":1.2,"porao_be_nivel":0.9,"bomba_porao_ciclos":0,"ancora_estado":"lançada","ondas_m":0.5,"vento_verdadeiro_nos":9.2,"vento_verdadeiro_angulo":58,"vento_aparente_nos":9.2,"vento_aparente_angulo":-13,"pressao_barometrica_hpa":1017,"temp_ar_externo_c":22.6,"temp_agua_c":20.1,"temp_praca_maquinas_c":38,"jogo_graus":0.6,"caimento_graus":0.4,"gps_satelites":26,"climatizacao_ativa":true,"dessalinizador_ativo":false,"radar_ativo":false,"ais_alvos":3,"estado":"Fundeado","local":"na enseada de Balneário Camboriú"}
 },
 "consumo": {
  "cruzeiro": {"nos":18,"rpm":2050,"lph":68},
  "lenta": {"nos":5,"rpm":700,"lph":6.2},
  "maxima": {"nos":26,"rpm":2600,"lph":111},
  "gerador_lph": 2.3,
  "faixas": [{"rpm_de":600,"rpm_ate":1000,"nome":"marcha lenta"},{"rpm_de":1000,"rpm_ate":1500,"nome":"deslocamento"},{"rpm_de":1500,"rpm_ate":1800,"nome":"transição"},{"rpm_de":1800,"rpm_ate":2000,"nome":"planeio"},{"rpm_de":2000,"rpm_ate":2600,"nome":"cruzeiro"}],
  "fonte": "Guia de bordo — Motores Cummins §10 · Consumo",
  "margemManobra_l": 60,
  "periodo": "01/08–26/09/2026",
  "desdeAbast": {"litros":192,"desde":"12/09/2026","horas":"2,8 h de motor por lado"}
 },
 "reserva": 0.1,
 "autonomia": {
  "horas": 11.2,
  "mn": 202,
  "lenta": 123
 },
 "destinos": [{"id":"cabras","nome":"Ilha das Cabras","mn":0.9},{"id":"laranjeiras","nome":"Ponta das Laranjeiras","mn":3.2},{"id":"taquaras","nome":"Taquaras","mn":6.3},{"id":"estaleirinho","nome":"Estaleirinho","mn":8.1}],
 "rota": {
  "fonte": "Plano de navegação de bordo · Barra Sul ⇄ Estaleirinho",
  "base": {"id":"base","nome":"Barra Sul (saída do Rio Camboriú)","rel":"da Barra Sul","perto":"na saída da Barra Sul","lat":-26.9985,"lon":-48.616,"prof_m":8},
  "pontos": [{"id":"cabras","nome":"Ilha das Cabras","rel":"da Ilha das Cabras","perto":"ao largo da Ilha das Cabras","lat":-26.9838,"lon":-48.61,"prof_m":12},{"id":"laranjeiras","nome":"Ponta das Laranjeiras","rel":"da Ponta das Laranjeiras","perto":"ao largo da Ponta das Laranjeiras","lat":-26.982,"lon":-48.568,"prof_m":16},{"id":"taquaras","nome":"Taquaras","rel":"de Taquaras","perto":"ao largo de Taquaras","lat":-27.032,"lon":-48.554,"prof_m":19},{"id":"estaleirinho","nome":"Estaleirinho","rel":"do Estaleirinho","perto":"ao largo do Estaleirinho","lat":-27.062,"lon":-48.553,"prof_m":21},{"id":"pinho","nome":"Praia do Pinho","rel":"da Praia do Pinho","perto":"ao largo da Praia do Pinho","lat":-27.045,"lon":-48.543,"prof_m":22},{"id":"laranjeiras_v","nome":"Laranjeiras","rel":"de Laranjeiras","perto":"ao largo de Laranjeiras","lat":-26.981,"lon":-48.574,"prof_m":18},{"id":"cabras_v","nome":"Ilha das Cabras","rel":"da Ilha das Cabras","perto":"ao largo da Ilha das Cabras","lat":-26.985,"lon":-48.6084,"prof_m":13}],
  "destino": {"id":"estaleirinho","nome":"Estaleirinho","caminho":"a caminho do Estaleirinho"},
  "volta": {"nome":"Barra Sul (base)","caminho":"a caminho da Barra Sul"},
  "pernas": [{"de":"base","para":"cabras","mn":0.9385,"rumo":19.99,"ini_mn":0.0},{"de":"cabras","para":"laranjeiras","mn":2.2483,"rumo":87.25,"ini_mn":0.9385},{"de":"laranjeiras","para":"taquaras","mn":3.0919,"rumo":165.99,"ini_mn":3.1868},{"de":"taquaras","para":"estaleirinho","mn":1.8008,"rumo":178.3,"ini_mn":6.2787},{"de":"estaleirinho","para":"pinho","mn":1.1515,"rumo":27.65,"ini_mn":8.0795},{"de":"pinho","para":"laranjeiras_v","mn":4.1823,"rumo":336.66,"ini_mn":9.231},{"de":"laranjeiras_v","para":"cabras_v","mn":1.8549,"rumo":262.57,"ini_mn":13.4133},{"de":"cabras_v","para":"base","mn":0.9062,"rumo":206.64,"ini_mn":15.2682}],
  "distancia_mn": 16.1744,
  "ida_mn": 8.0795,
  "circuitos_dia": 19,
  "fator": 0.986558,
  "guinada_max_gps": 3,
  "corrente": {"nos":0.3,"para_graus":200}
 },
 "replay": {
  "duracao": 150,
  "passo": 1,
  "passo_chave": 5,
  "cenario": "aviso",
  "ancora_hora": "07:00",
  "voltas_fixo": 120,
  "chaves": {"motor_bb_rpm":[700,700,705,700,710,1100,1400,1650,1850,1980,2050,2050,2050,2050,2050,2050,2050,2050,2050,2050,2050,2050,2050,2050,2050,1450,950,710,705,700],"motor_be_rpm":[695,695,700,695,705,1090,1390,1640,1840,1970,2040,2040,2040,2040,2040,2040,2040,2040,2040,2040,2040,2040,2040,2040,2040,1440,945,705,700,695],"sog_nos":[5.0,5.0,5.0,5.0,5.1,7.6,10.0,12.6,15.0,16.9,18.0,18.0,18.0,18.0,18.0,18.0,18.0,18.0,18.0,18.0,18.0,18.0,18.0,18.0,18.0,10.4,6.6,5.1,5.0,5.0],"consumo_lph":[6.2,6.2,6.3,6.2,6.4,14.0,24.0,36.0,48.0,60.0,68.0,68.0,68.0,68.0,68.0,68.0,68.0,68.0,68.0,68.0,68.0,68.0,68.0,68.0,68.0,26.0,10.5,6.4,6.3,6.2],"motor_bb_oleo_bar":[2.8,2.8,2.8,2.8,2.8,3.13,3.37,3.57,3.74,3.84,3.9,3.9,3.9,3.9,3.9,3.9,3.9,3.9,3.9,3.9,3.9,3.9,3.9,3.9,3.9,3.41,3.0,2.8,2.8,2.8],"motor_be_oleo_bar":[2.7,2.7,2.7,2.7,2.7,3.03,3.27,3.47,3.64,3.74,3.8,3.8,3.8,3.8,3.8,3.8,3.8,3.8,3.8,3.8,3.8,3.8,3.8,3.8,3.8,3.31,2.9,2.7,2.7,2.7],"motor_bb_arref_c":[78.0,78.0,78.0,78.0,78.0,78.0,79.2,80.1,80.8,81.4,81.8,82.0,82.0,82.0,82.0,82.0,82.0,82.0,82.0,82.0,82.0,82.0,82.0,82.0,82.0,82.0,80.2,78.7,78.0,78.0],"motor_be_arref_c":[78.0,78.0,78.0,78.0,78.0,78.0,79.2,80.1,80.8,81.4,81.8,82.0,82.0,82.0,82.0,82.0,82.0,82.0,82.0,86.2,89.0,89.6,89.6,89.0,85.8,82.0,80.2,78.7,78.0,78.0],"motor_bb_carga_pct":[10,10,10,10,10,25,37,47,54,59,62,62,62,62,62,62,62,62,62,62,62,62,62,62,62,39,20,10,10,10],"motor_be_carga_pct":[9,9,9,9,9,24,36,46,53,58,61,61,61,61,61,61,61,61,61,61,61,61,61,61,61,38,19,9,9,9],"gerador_kw":[6.0,6.2,6.3,6.3,6.2,6.0,5.8,5.7,5.7,5.8,6.0,6.2,6.3,6.3,6.2,6.0,5.8,5.7,5.7,5.8,6.0,6.2,6.3,6.3,6.2,6.0,5.8,5.7,5.7,5.8],"bateria_0_tensao_v":[27.3,27.3,27.3,27.3,27.3,27.45,27.56,27.65,27.73,27.77,27.8,27.8,27.8,27.8,27.8,27.8,27.8,27.8,27.8,27.8,27.8,27.8,27.8,27.8,27.8,27.58,27.39,27.3,27.3,27.3],"bateria_1_tensao_v":[27.4,27.4,27.4,27.4,27.4,27.56,27.69,27.79,27.87,27.92,27.95,27.95,27.95,27.95,27.95,27.95,27.95,27.95,27.95,27.95,27.95,27.95,27.95,27.95,27.95,27.71,27.5,27.4,27.4,27.4],"bateria_2_tensao_v":[13.55,13.55,13.55,13.55,13.55,13.59,13.63,13.66,13.68,13.69,13.7,13.7,13.7,13.7,13.7,13.7,13.7,13.7,13.7,13.7,13.7,13.7,13.7,13.7,13.7,13.63,13.58,13.55,13.55,13.55],"ondas_m":[0.7,0.7,0.7,0.7,0.7,0.7,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.7,0.7,0.7,0.7],"vento_verdadeiro_nos":[10.5,10.7,11.0,11.2,11.4,11.5,11.6,11.7,11.7,11.6,11.5,11.4,11.2,11.0,10.7,10.5,10.3,10.0,9.8,9.6,9.5,9.4,9.3,9.3,9.4,9.5,9.6,9.8,10.0,10.3],"vento_verdadeiro_angulo":[58,59,60,60,61,61,62,62,62,62,61,61,60,60,59,58,57,56,56,55,55,54,54,54,54,55,55,56,56,57],"pressao_barometrica_hpa":[1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1,1017.1],"temp_ar_externo_c":[22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6,22.6],"temp_agua_c":[20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1,20.1],"porao_bb_nivel":[1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2],"porao_be_nivel":[0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9,0.9],"seakeeper_volante_rpm":[8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420,8420],"seakeeper_volante_pct":[100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100],"jogo_graus":[0.0,0.4,0.6,0.6,0.4,0.0,-0.4,-0.6,-0.6,-0.4,0.0,0.4,0.6,0.6,0.4,0.0,-0.4,-0.6,-0.6,-0.4,0.0,0.4,0.6,0.6,0.4,0.0,-0.4,-0.6,-0.6,-0.4],"caimento_graus":[0.8,0.8,0.8,0.8,0.9,2.6,4.8,5.1,4.4,3.6,3.2,3.2,3.2,3.2,3.2,3.2,3.2,3.2,3.2,3.2,3.2,3.2,3.2,3.2,3.2,2.4,1.2,0.9,0.8,0.8],"temp_praca_maquinas_c":[41,41,41,41,41,41,41,42,44,45,45,46,46,46,46,46,46,46,46,46,46,46,46,46,46,46,46,44,42,41],"leme_graus":[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]},
  "ruido": {"motor_bb_rpm":[6,1100],"motor_be_rpm":[6,1101],"sog_nos":[0.1,1102],"consumo_lph":[0,1103],"motor_bb_oleo_bar":[0.03,1104],"motor_be_oleo_bar":[0.03,1105],"motor_bb_arref_c":[0.1,1106],"motor_be_arref_c":[0.1,1107],"motor_bb_carga_pct":[0.6,1108],"motor_be_carga_pct":[0.6,1109],"gerador_kw":[0.1,1110],"bateria_0_tensao_v":[0.02,1111],"bateria_1_tensao_v":[0.02,1112],"bateria_2_tensao_v":[0.01,1113],"ondas_m":[0.05,1114],"vento_verdadeiro_nos":[0.4,1115],"vento_verdadeiro_angulo":[2,1116],"pressao_barometrica_hpa":[0.05,1117],"temp_ar_externo_c":[0,1118],"temp_agua_c":[0,1119],"porao_bb_nivel":[0.1,1120],"porao_be_nivel":[0.1,1121],"seakeeper_volante_rpm":[12,1122],"seakeeper_volante_pct":[0,1123],"jogo_graus":[0.3,1124],"caimento_graus":[0.1,1125],"temp_praca_maquinas_c":[0.2,1126],"leme_graus":[0.4,1127],"proa_graus":[0.4,1201],"profundidade_m":[0.2,1202]},
  "fixos": {"marcha":"avante","estado":"Navegando","gerador_ativo":true,"seakeeper_ativo":true,"ancora_estado":"recolhida","bomba_porao_ciclos":0,"gps_satelites":18,"climatizacao_ativa":true,"dessalinizador_ativo":false,"radar_ativo":true,"ais_alvos":4},
  "velocidade_media_nos": 12.8047,
  "fases": [{"ini":0,"fim":20,"nome":"marcha lenta"},{"ini":20,"fim":50,"nome":"aceleração"},{"ini":50,"fim":120,"nome":"cruzeiro"},{"ini":120,"fim":135,"nome":"redução"},{"ini":135,"fim":150,"nome":"marcha lenta"}],
  "contadores_base": {"motor_bb_horimetro_h":412.6,"motor_be_horimetro_h":409.8,"gerador_horimetro_h":1236.4,"diesel_litros":1560,"distancia_mn":0,"tanque_agua_pct":92,"tanque_cinzas_pct":8,"tanque_negras_pct":5},
  "taxas_h": {"tanque_agua_pct":-1.2,"tanque_cinzas_pct":1.4,"tanque_negras_pct":0.9},
  "por_volta": {"diesel_l":1.8857,"motores_l":1.7899,"gerador_l":0.0958,"distancia_mn":0.5408,"motor_h":0.041667,"gerador_h":0.041667},
  "por_dia": {"voltas":576,"diesel_l":1086.2,"distancia_mn":311.5,"motor_h":24,"gerador_h":24},
  "diesel_piso_l": 400,
  "limites": {"motor_bb_oleo_bar":{"un":"bar","fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação","regimes":[{"rpm_campo":"motor_bb_rpm","rpm_ate":1000,"normal":{"de":1.0,"ate":6.0},"aviso":{"abaixo":1.0,"acima":6.0},"critico":{"abaixo":0.6}},{"rpm_campo":"motor_bb_rpm","rpm_de":1000,"normal":{"de":2.4,"ate":6.0},"aviso":{"abaixo":2.4,"acima":6.0},"critico":{"abaixo":1.4}}],"ativo_se":{"campo":"motor_bb_rpm","acima":0}},"motor_bb_arref_c":{"un":"°C","fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação","normal":{"ate":88},"aviso":{"acima":88},"critico":{"acima":97},"ativo_se":{"campo":"motor_bb_rpm","acima":0}},"motor_bb_rpm":{"un":"rpm","fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação","normal":{"ate":2600},"aviso":{"acima":2600}},"motor_bb_carga_pct":{"un":"%","fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação","normal":{"ate":90},"aviso":{"acima":90},"ativo_se":{"campo":"motor_bb_rpm","acima":0}},"motor_be_oleo_bar":{"un":"bar","fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação","regimes":[{"rpm_campo":"motor_be_rpm","rpm_ate":1000,"normal":{"de":1.0,"ate":6.0},"aviso":{"abaixo":1.0,"acima":6.0},"critico":{"abaixo":0.6}},{"rpm_campo":"motor_be_rpm","rpm_de":1000,"normal":{"de":2.4,"ate":6.0},"aviso":{"abaixo":2.4,"acima":6.0},"critico":{"abaixo":1.4}}],"ativo_se":{"campo":"motor_be_rpm","acima":0}},"motor_be_arref_c":{"un":"°C","fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação","normal":{"ate":88},"aviso":{"acima":88},"critico":{"acima":97},"ativo_se":{"campo":"motor_be_rpm","acima":0}},"motor_be_rpm":{"un":"rpm","fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação","normal":{"ate":2600},"aviso":{"acima":2600}},"motor_be_carga_pct":{"un":"%","fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação","normal":{"ate":90},"aviso":{"acima":90},"ativo_se":{"campo":"motor_be_rpm","acima":0}},"temp_praca_maquinas_c":{"un":"°C","fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação","normal":{"ate":60},"aviso":{"acima":60}},"bateria_0_tensao_v":{"un":"V","fonte":"Guia de bordo — Sistema elétrico 24 V e 12 V §2 · Faixas","normal":{"de":24.4,"ate":29.4},"aviso":{"abaixo":24.4,"acima":29.4},"critico":{"abaixo":23.6}},"bateria_1_tensao_v":{"un":"V","fonte":"Guia de bordo — Sistema elétrico 24 V e 12 V §2 · Faixas","normal":{"de":24.4,"ate":29.4},"aviso":{"abaixo":24.4,"acima":29.4},"critico":{"abaixo":23.6}},"bateria_2_tensao_v":{"un":"V","fonte":"Guia de bordo — Sistema elétrico 24 V e 12 V §2 · Faixas","normal":{"de":12.2,"ate":14.7},"aviso":{"abaixo":12.2,"acima":14.7},"critico":{"abaixo":11.8}},"porao_bb_nivel":{"un":"cm","fonte":"Guia de bordo — Bombas de porão Rule §2 · Faixas","normal":{"ate":5},"aviso":{"acima":5},"critico":{"acima":10}},"porao_be_nivel":{"un":"cm","fonte":"Guia de bordo — Bombas de porão Rule §2 · Faixas","normal":{"ate":5},"aviso":{"acima":5},"critico":{"acima":10}},"profundidade_m":{"un":"m","fonte":"Guia de bordo — Eletrônicos Garmin, áudio Fusion e rádios Icom §8 · Sonda","normal":{"de":3.0},"aviso":{"abaixo":3.0},"critico":{"abaixo":2.0}},"diesel_litros":{"un":"L","fonte":"Checklist de bordo § Abastecimento","normal":{"de":400},"aviso":{"abaixo":400},"critico":{"abaixo":160}},"gerador_kw":{"un":"kW","fonte":"Guia de bordo — Gerador Onan §9 · Potência e carga","normal":{"ate":8.1},"aviso":{"acima":8.1},"ativo_se":{"campo":"gerador_ativo","igual":true}},"seakeeper_volante_pct":{"un":"%","fonte":"Guia de bordo — Estabilizador Seakeeper §8 · Faixas","normal":{"de":85},"aviso":{"abaixo":85},"ativo_se":{"campo":"seakeeper_ativo","igual":true}},"tanque_agua_pct":{"un":"%","fonte":"Checklist de bordo § Tanques","normal":{"de":15},"aviso":{"abaixo":15}},"tanque_cinzas_pct":{"un":"%","fonte":"Checklist de bordo § Tanques","normal":{"ate":80},"aviso":{"acima":80}},"tanque_negras_pct":{"un":"%","fonte":"Checklist de bordo § Tanques","normal":{"ate":80},"aviso":{"acima":80}}},
  "alertas": {"arref_bb":{"campo":"motor_bb_arref_c","sistema":"motores","lado":"bb","titulo":"Temperatura do motor BB","guia":"g_motores","secao":"5 · Temperatura alta","passos":["Reduza para marcha lenta e confira a saída de água pelo escapamento.","Sem água no escapamento ou com a temperatura ainda subindo: desligue o motor afetado e siga com o outro.","Com o motor parado, feche a válvula de fundo e confira o filtro de água salgada e o rotor da bomba de água salgada."],"fonte":"Guia de bordo — Motores Cummins §5 · Temperatura alta"},"arref_be":{"campo":"motor_be_arref_c","sistema":"motores","lado":"be","titulo":"Temperatura do motor BE","guia":"g_motores","secao":"5 · Temperatura alta","passos":["Reduza para marcha lenta e confira a saída de água pelo escapamento.","Sem água no escapamento ou com a temperatura ainda subindo: desligue o motor afetado e siga com o outro.","Com o motor parado, feche a válvula de fundo e confira o filtro de água salgada e o rotor da bomba de água salgada."],"fonte":"Guia de bordo — Motores Cummins §5 · Temperatura alta"},"oleo_bb":{"campo":"motor_bb_oleo_bar","sistema":"motores","lado":"bb","titulo":"Pressão de óleo do motor BB","guia":"g_motores","secao":"4 · Pressão de óleo baixa","passos":["Reduza para marcha lenta e confira o manômetro agora.","Compare BB e BE no mesmo giro: só um lado baixo aponta o motor.","Com o motor parado, procure vazamento e confira o nível de óleo na vareta.","Se continuar baixa, desligue o motor afetado, siga com o outro e chame a oficina dos motores."],"fonte":"Guia de bordo — Motores Cummins §4 · Pressão de óleo baixa"},"oleo_be":{"campo":"motor_be_oleo_bar","sistema":"motores","lado":"be","titulo":"Pressão de óleo do motor BE","guia":"g_motores","secao":"4 · Pressão de óleo baixa","passos":["Reduza para marcha lenta e confira o manômetro agora.","Compare BB e BE no mesmo giro: só um lado baixo aponta o motor.","Com o motor parado, procure vazamento e confira o nível de óleo na vareta.","Se continuar baixa, desligue o motor afetado, siga com o outro e chame a oficina dos motores."],"fonte":"Guia de bordo — Motores Cummins §4 · Pressão de óleo baixa"},"rpm_bb":{"campo":"motor_bb_rpm","sistema":"motores","lado":"bb","titulo":"Rotação do motor BB","guia":"g_motores","secao":"9 · Faixas de operação","passos":["Reduza o giro para o cruzeiro.","Confira o painel dos dois motores.","Registre no diário com a hora."],"fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação"},"rpm_be":{"campo":"motor_be_rpm","sistema":"motores","lado":"be","titulo":"Rotação do motor BE","guia":"g_motores","secao":"9 · Faixas de operação","passos":["Reduza o giro para o cruzeiro.","Confira o painel dos dois motores.","Registre no diário com a hora."],"fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação"},"carga_bb":{"campo":"motor_bb_carga_pct","sistema":"motores","lado":"bb","titulo":"Carga do motor BB","guia":"g_motores","secao":"9 · Faixas de operação","passos":["Reduza o giro para o cruzeiro.","Confira o painel dos dois motores.","Registre no diário com a hora."],"fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação"},"carga_be":{"campo":"motor_be_carga_pct","sistema":"motores","lado":"be","titulo":"Carga do motor BE","guia":"g_motores","secao":"9 · Faixas de operação","passos":["Reduza o giro para o cruzeiro.","Confira o painel dos dois motores.","Registre no diário com a hora."],"fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação"},"praca":{"campo":"temp_praca_maquinas_c","sistema":"motores","titulo":"Temperatura da praça de máquinas","guia":"g_motores","secao":"9 · Faixas de operação","passos":["Reduza o giro para o cruzeiro.","Confira a ventilação da praça de máquinas.","Registre no diário com a hora."],"fonte":"Guia de bordo — Motores Cummins §9 · Faixas de operação"},"b24s":{"campo":"bateria_0_tensao_v","sistema":"eletrico","titulo":"Banco de serviço de 24 V","guia":"g_eletrico","secao":"2 · Faixas","passos":["Confira o carregador de bordo ligado ao gerador ou ao cais.","Confira os bornes limpos e apertados.","Registre a tensão e a hora no diário."],"fonte":"Guia de bordo — Sistema elétrico 24 V e 12 V §2 · Faixas"},"b24p":{"campo":"bateria_1_tensao_v","sistema":"eletrico","titulo":"Banco de partida de 24 V","guia":"g_eletrico","secao":"2 · Faixas","passos":["Confira o carregador de bordo ligado ao gerador ou ao cais.","Confira os bornes limpos e apertados.","Registre a tensão e a hora no diário."],"fonte":"Guia de bordo — Sistema elétrico 24 V e 12 V §2 · Faixas"},"b12":{"campo":"bateria_2_tensao_v","sistema":"eletrico","titulo":"Banco de 12 V","guia":"g_eletrico","secao":"2 · Faixas","passos":["Confira o carregador de bordo ligado ao gerador ou ao cais.","Confira os bornes limpos e apertados.","Registre a tensão e a hora no diário."],"fonte":"Guia de bordo — Sistema elétrico 24 V e 12 V §2 · Faixas"},"porao_bb":{"campo":"porao_bb_nivel","sistema":"porao","lado":"bb","titulo":"Nível do porão BB","guia":"g_porao","secao":"2 · Faixas","passos":["Confirme a bomba ligada pelo sensor de nível.","Acione a bomba no manual.","Procure a entrada de água.","Nível subindo com a bomba ligada ou água entrando é alagamento: use o SOS do app.","Registre o nível e a hora no diário."],"fonte":"Guia de bordo — Bombas de porão Rule §2 · Faixas"},"porao_be":{"campo":"porao_be_nivel","sistema":"porao","lado":"be","titulo":"Nível do porão BE","guia":"g_porao","secao":"2 · Faixas","passos":["Confirme a bomba ligada pelo sensor de nível.","Acione a bomba no manual.","Procure a entrada de água.","Nível subindo com a bomba ligada ou água entrando é alagamento: use o SOS do app.","Registre o nível e a hora no diário."],"fonte":"Guia de bordo — Bombas de porão Rule §2 · Faixas"},"profundidade":{"campo":"profundidade_m","sistema":"eletronicos","titulo":"Profundidade","guia":"g_eletronicos","secao":"8 · Sonda","passos":["Reduza a velocidade.","Confira a carta no plotter.","Mude de rumo para águas mais fundas."],"fonte":"Guia de bordo — Eletrônicos Garmin, áudio Fusion e rádios Icom §8 · Sonda"},"diesel":{"campo":"diesel_litros","sistema":"tanques","titulo":"Diesel a bordo","guia":"checklist","secao":"Abastecimento","passos":["Abasteça antes da próxima saída.","Confira a autonomia no app.","Registre os litros e o nível no app depois de abastecer."],"fonte":"Checklist de bordo § Abastecimento"},"gerador":{"campo":"gerador_kw","sistema":"gerador","titulo":"Carga do gerador","guia":"g_gerador","secao":"9 · Potência e carga","passos":["Retire cargas no quadro elétrico, uma de cada vez.","Deixe a climatização por último.","Registre no diário com a hora."],"fonte":"Guia de bordo — Gerador Onan §9 · Potência e carga"},"seakeeper":{"campo":"seakeeper_volante_pct","sistema":"estabilizador","titulo":"Volante do estabilizador","guia":"g_seakeeper","secao":"8 · Faixas","passos":["Confira o banco de 12 V e o carregador.","Espere a indicação do display.","Anote a mensagem do display no diário com a hora."],"fonte":"Guia de bordo — Estabilizador Seakeeper §8 · Faixas"},"agua":{"campo":"tanque_agua_pct","sistema":"tanques","titulo":"Tanque de água doce","guia":"checklist","secao":"Tanques","passos":["Complete a água doce na marina.","Confira o nível no app.","Registre no diário com a hora."],"fonte":"Checklist de bordo § Tanques"},"cinzas":{"campo":"tanque_cinzas_pct","sistema":"tanques","titulo":"Tanque de águas cinzas","guia":"checklist","secao":"Tanques","passos":["Esvazie as servidas na marina.","Confira o nível no app.","Registre no diário com a hora."],"fonte":"Checklist de bordo § Tanques"},"negras":{"campo":"tanque_negras_pct","sistema":"tanques","titulo":"Tanque de águas negras","guia":"checklist","secao":"Tanques","passos":["Esvazie as servidas na marina.","Confira o nível no app.","Registre no diário com a hora."],"fonte":"Checklist de bordo § Tanques"}},
  "janelas": [{"id":"arref_be","campo":"motor_be_arref_c","nivel":"aviso","ini":99,"fim":116}],
  "diaDeBordo": {"dias":3,"abastecimento":{"h":"07:00","litros":1086,"combustivel":"diesel","local":"posto da marina da base","st":"CONFERIDO","nivelAntes":29.6,"nivelDepois":97.5,"nota":"para a saída das 07:00 · nota fiscal conferida (Documentos)"},"documento":{"id":"nf-abast","n":"Nota fiscal do abastecimento","cat":"Notas","emitidoHa":0,"st":"CONFERIDA","ref":"ab-0","nota":"abastecimento das 07:00 · sem valores no app","fonte":"Controle de documentos · Drive › Capitão IA v2 › 02 Documentos"},"diario":[{"id":"d01","diasAtras":0,"h":"07:00","sys":"Navegação","tom":"tele","who":"Lucas","pend":false,"t":"Saída da Barra Sul às 07:00 com 4 pessoas a bordo: passeio Barra Sul ⇄ Estaleirinho pela Interpraias. Checklist de saída feito; o teste das bombas de porão continua pendente."},{"id":"d02","diasAtras":0,"h":"07:00","sys":"Combustível","tom":"ok","who":"Lucas","pend":false,"ref":"ab-0","t":"Abastecimento de 1.086 L de diesel no posto da marina da base para a saída das 07:00, com água completada e servidas esvaziadas; tanques de diesel em 97,5 %."}]}
 },
 "historico": {
  "fim": "ancora",
  "passo_dias": 2,
  "n": 183,
  "desvios": {"vento_verdadeiro_nos":{"escala":10,"d":[-26,-17,-4,-12,-12,-27,-24,-3,2,-8,-8,3,4,4,22,25,11,16,23,16,17,26,23,-7,-13,-9,-7,-6,-1,17,23,12,11,1,-5,-10,-24,-25,-13,7,13,14,1,-9,-18,-15,-20,-19,-2,-6,19,10,16,18,14,11,15,1,-6,3,20,8,-16,-6,-19,-9,9,9,-7,-10,-15,1,2,-7,1,-2,-8,0,0,-14,-22,-30,-20,-3,0,1,-10,-8,7,13,7,-1,-4,6,3,13,4,20,40,27,27,15,-12,-27,-26,-14,-10,14,19,25,7,-19,-22,-5,8,17,24,25,13,-7,-18,0,17,11,27,14,2,-7,-11,-5,-17,-1,14,-5,10,-7,-1,-4,6,15,19,2,-1,-24,-23,-13,-5,-8,-10,-14,-5,11,18,9,-15,-23,-18,-10,-13,-2,0,5,2,7,28,10,-1,0,-6,-3,-8,2,-9,-2,-13,-3,-4,-7,5,9,20,22,11]},"pressao_barometrica_hpa":{"escala":10,"d":[27,33,42,42,33,25,22,18,10,1,-10,-21,-26,-29,-37,-46,-42,-25,-15,-29,-55,-70,-61,-45,-35,-44,-60,-70,-62,-43,-33,-42,-58,-66,-65,-66,-67,-51,-17,9,24,36,41,38,33,29,27,24,23,24,27,35,34,20,12,7,-7,-26,-40,-43,-43,-33,-12,11,32,51,59,46,20,3,9,27,37,28,10,-4,-1,10,17,16,16,21,31,40,45,30,0,-23,-33,-38,-40,-36,-30,-27,-37,-51,-59,-57,-56,-58,-58,-53,-50,-40,-19,3,10,5,0,-4,-13,-18,-15,-12,-10,-1,15,28,31,31,31,34,38,38,36,38,40,36,29,27,36,49,56,42,14,-9,-24,-36,-41,-31,-8,14,28,36,39,39,34,20,-5,-27,-37,-42,-50,-51,-34,-7,7,6,1,-7,-19,-31,-37,-41,-46,-47,-46,-47,-49,-48,-44,-32,-8,18,30,34,40,43,32,14,4,12,26]},"bateria_0_tensao_v":{"escala":100,"d":[0,0,1,2,2,1,2,1,1,1,2,-1,0,1,1,3,0,-1,-4,-4,-2,-2,1,1,2,4,5,4,3,4,2,1,1,4,1,1,2,2,5,5,5,2,2,2,0,-2,-2,-3,-1,-2,-5,-6,-5,-2,-3,-3,-2,-2,-2,0,1,0,2,2,2,1,3,2,3,3,2,2,3,3,1,0,-2,-5,-4,-2,0,1,1,0,0,1,0,-1,-1,-2,-2,-2,1,1,1,0,0,0,1,-1,-1,2,0,0,0,2,0,2,3,2,0,-3,-3,0,0,1,2,1,0,-1,-2,-2,-1,0,1,2,3,3,2,1,1,1,1,2,2,-1,0,-2,0,0,-2,-2,-1,0,0,0,0,-1,0,1,0,0,1,2,2,3,4,5,4,2,3,6,6,4,0,-1,-1,0,-1,-1,0,1,1,1,1,0,1,-1,-3,-5,-3,-2,1]},"bateria_1_tensao_v":{"escala":100,"d":[-2,0,0,2,1,1,1,0,3,3,2,2,1,1,3,3,4,2,1,2,2,1,2,2,1,0,-1,-4,-4,-2,-1,-1,1,2,4,2,4,1,0,-2,-2,-2,-4,-1,0,2,2,1,2,2,3,3,3,3,3,2,3,5,4,5,5,4,6,6,5,5,5,4,3,2,4,6,6,4,4,4,3,3,2,1,0,2,1,-1,-1,-1,-3,-2,-2,-1,-1,-1,-2,-4,-3,-2,1,1,0,-2,-2,-1,-1,0,1,2,2,2,0,-1,-2,-2,-1,-1,-2,-2,-2,-3,-2,-2,1,-1,-2,-1,1,1,0,2,3,5,3,2,1,3,2,1,2,3,4,2,2,0,2,0,-2,-1,-2,-3,-4,-4,-3,-2,-1,0,-2,-2,-2,-1,0,-1,0,-2,-1,-1,0,2,1,1,0,1,1,3,2,0,-2,-2,1,3,3,1,2,4,3]},"bateria_2_tensao_v":{"escala":100,"d":[4,3,3,3,3,4,3,1,0,-3,-4,-5,-2,2,3,3,2,0,-1,-1,-1,-1,-3,-3,-2,-2,-2,-1,3,3,2,0,-2,-3,-1,-2,-2,-1,2,2,3,1,0,-2,-3,-3,-2,-2,-2,1,1,1,1,2,2,3,2,0,0,0,0,1,1,2,3,2,1,1,3,3,1,1,2,0,-2,-1,-1,-1,1,2,1,4,4,4,1,4,5,4,2,4,5,2,-1,-1,0,0,-2,-1,-1,1,4,3,2,0,1,1,-1,-1,-2,-2,0,-1,1,-1,-3,-2,-1,0,0,-3,-4,-3,-2,-1,-1,0,1,-1,-1,-1,-2,-3,-5,-4,-1,-1,-2,-3,-3,-4,-4,-1,-1,2,4,5,6,2,1,3,5,4,0,1,0,1,1,2,1,0,1,-1,0,-2,-3,-4,0,-2,-1,-2,1,-1,0,-3,-3,-3,-2,0,0,2,2,3,3]},"temp_ar_externo_c":{"escala":10,"d":[13,12,8,2,-3,-2,1,-1,-2,3,8,5,2,0,-3,-6,-9,-8,-6,0,6,3,0,5,9,11,11,5,-1,-1,-1,3,5,-5,-14,-11,-6,-6,-7,-6,-5,-8,-10,-3,3,3,1,3,5,9,12,10,7,6,5,5,7,6,5,3,1,-2,-6,-3,1,-1,-2,2,7,9,10,4,-5,-7,-10,-10,-7,-4,0,-2,-5,-1,4,4,3,8,11,11,11,9,9,2,-6,-4,-2,-3,-1,-2,-1,4,8,8,7,2,-3,-7,-8,-4,0,-1,-2,2,8,11,12,10,5,1,-5,-9,-11,-12,-14,-9,-5,-3,-1,0,1,3,4,5,6,2,-3,-2,-2,-1,-1,-3,-4,-4,-4,1,4,2,0,0,0,2,4,2,-1,0,2,1,0,-1,-2,-3,-2,-4,-3,1,5,8,8,5,0,-9,-15,-9,0,6,11,10,6,1,-5,-8,-8,-7,-4]},"temp_agua_c":{"escala":10,"d":[3,3,4,4,4,3,2,2,1,1,1,1,1,1,2,3,3,2,1,0,0,0,-1,-1,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,1,1,2,2,2,2,2,2,2,2,3,3,3,3,3,4,3,3,2,2,1,0,-1,-2,-2,-2,-2,-2,-1,-1,-1,-1,-1,-1,-1,-2,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,0,0,0,0,0,0,0,0,0,0,-1,-2,-3,-4,-4,-3,-3,-2,-3,-3,-3,-3,-3,-2,-2,-2,-1,-1,0,1,1,1,0,0,0,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-2,-2,-2,-2,-1,0,0,0,-1,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-1,0,1,1,1,1,1,1,1,2,3,3,3,2,2,2,2,3,4,4,4,3,3,3,3,2]}},
  "sazonal": {"passo_dias":5,"n":73,"temp_ar_externo_c":{"escala":10,"d":[44,44,45,45,45,44,44,42,41,39,37,35,32,29,26,23,20,16,12,9,5,1,-3,-7,-11,-14,-18,-21,-25,-28,-31,-33,-36,-38,-40,-42,-43,-44,-45,-45,-45,-45,-44,-43,-42,-40,-38,-36,-33,-31,-28,-25,-21,-18,-14,-11,-7,-3,1,5,9,12,16,20,23,26,29,32,35,37,39,41,42]},"temp_agua_c":{"escala":10,"d":[25,27,29,30,32,33,34,34,35,35,35,34,34,33,32,30,29,27,25,23,20,18,15,13,10,7,4,1,-2,-5,-8,-11,-14,-17,-19,-22,-24,-26,-28,-30,-31,-32,-33,-34,-35,-35,-35,-35,-34,-33,-32,-31,-30,-28,-26,-24,-22,-19,-17,-14,-11,-8,-5,-2,1,4,7,10,13,15,18,20,23]}},
  "cruzeiro": {"dias":60,"motor_bb_arref_c":{"escala":10,"d":[819,820,821,821,821,820,821,821,820,820,819,820,820,820,821,820,820,820,821,820,819,820,820,821,822,821,821,822,821,820,821,820,821,821,819,820,818,819,819,819,819,819,820,820,820,820,820,819,819,820,820,820,820,819,821,819,819,819,818,818]},"motor_be_arref_c":{"escala":10,"d":[824,824,824,825,825,825,826,826,826,826,826,826,827,827,827,828,828,829,829,829,829,829,830,831,830,830,831,831,831,832,832,832,833,833,833,833,833,834,834,833,834,834,834,834,835,835,836,837,837,837,838,838,838,838,838,838,838,838,838,838]},"motor_bb_oleo_bar":{"escala":100,"d":[390,391,390,392,391,391,392,392,390,389,390,390,390,391,388,389,390,391,392,392,391,393,392,392,392,392,391,391,391,389,387,389,388,388,389,389,391,389,390,390,389,390,391,392,390,391,391,391,390,390,390,390,389,388,388,388,390,389,390,391]},"motor_be_oleo_bar":{"escala":100,"d":[380,380,379,378,379,379,378,380,380,380,380,380,381,380,380,378,379,380,379,380,379,380,381,382,381,381,381,382,382,381,382,381,382,381,381,381,380,380,378,379,379,377,378,378,379,379,380,380,380,380,382,382,381,381,382,382,381,381,382,381]}},
  "janelas": {"150S":{"passo_s":1,"n":150},"1D":{"passo_s":900,"n":96},"7D":{"passo_s":3600,"n":168},"30D":{"passo_s":21600,"n":120},"1A":{"passo_s":86400,"n":365}},
  "metricas": {"b24":["bateria_0_tensao_v","bateria_1_tensao_v"],"b12":["bateria_2_tensao_v"],"tanques":["tanque_agua_pct","tanque_cinzas_pct","tanque_negras_pct"],"vento":["vento_verdadeiro_nos"],"pressao":["pressao_barometrica_hpa"],"diesel":["diesel_litros"],"temperaturas":["temp_praca_maquinas_c","temp_ar_externo_c","temp_agua_c"],"motores":["motor_bb_rpm","motor_be_rpm"],"oleo":["motor_bb_oleo_bar","motor_be_oleo_bar"],"arref":["motor_bb_arref_c","motor_be_arref_c"],"navegacao":["sog_nos","stw_nos"],"consumo":["consumo_lph"]},
  "so150": ["motores","oleo","arref","navegacao","consumo"],
  "fonte": "coletor NMEA de bordo · histórico"
 },
 "serie24v": [{"diasAtras":6,"min":27.25,"max":27.79,"d":"20/09"},{"diasAtras":5,"min":27.26,"max":27.8,"d":"21/09"},{"diasAtras":4,"min":27.26,"max":27.8,"d":"22/09"},{"diasAtras":3,"min":27.28,"max":27.82,"d":"23/09"},{"diasAtras":2,"min":27.29,"max":27.83,"d":"24/09"},{"diasAtras":1,"min":27.29,"max":27.83,"d":"25/09"},{"diasAtras":0,"min":27.28,"max":27.82,"d":"26/09"}],
 "agenda": [{"id":"porao-teste","t":"Teste das bombas de porão e alarmes","curto":"TESTE","equip":"Bombas de porão Rule 2000","sistema":"porao","quem":"técnico","intervalo":"mensal","meses":1,"ultimaHa":56,"venceEm":-25,"seguranca":true,"palavras":["bombas de porao","bomba de porao","teste das bombas"],"fonte":"Agenda preditiva","ultima":"01/08/2026","vence":"01/09/2026","dn":-25,"st":"ATRASADA","rot":"ATRASADA · 25 D","tom":"crit"},{"id":"clima-filtro","t":"Limpeza do filtro de água salgada da climatização","curto":"FILTRO","equip":"Climatização Webasto FCF Platinum","sistema":"climatizacao","quem":"marina","intervalo":"mensal","meses":1,"ultimaHa":47,"venceEm":-16,"palavras":["filtro de agua salgada","filtro da climatizacao","filtro do ar condicionado","filtro do ar-condicionado"],"fonte":"Agenda preditiva","ultima":"10/08/2026","vence":"10/09/2026","dn":-16,"st":"ATRASADA","rot":"ATRASADA · 16 D","tom":"crit"},{"id":"gerador-rotor","t":"Inspeção do rotor (impeller) do gerador","curto":"ROTOR","equip":"Gerador Onan QD 9","sistema":"gerador","quem":"técnico","intervalo":"12 meses","meses":12,"ultimaHa":367,"venceEm":-2,"palavras":["rotor do gerador","impeller do gerador","rotor impeller do gerador"],"fonte":"Agenda preditiva","ultima":"24/09/2025","vence":"24/09/2026","dn":-2,"st":"ATRASADA","rot":"ATRASADA · 2 D","tom":"crit"},{"id":"casco-anodos","t":"Limpeza de casco e troca de anodos","curto":"ANODOS","equip":"Casco","sistema":"casco","quem":"marina","intervalo":"6 meses","meses":6,"ultimaHa":175,"venceEm":9,"palavras":["limpeza de casco","limpeza do casco","anodos do casco","troca de anodos"],"fonte":"Agenda preditiva","ultima":"04/04/2026","vence":"05/10/2026","dn":9,"st":"D-30","rot":"D-9","tom":"warn"},{"id":"epirb-teste","t":"Autoteste do EPIRB e validade conferida na etiqueta","curto":"AUTOTESTE","equip":"EPIRB","sistema":"epirb","quem":"Lucas","intervalo":"mensal","meses":1,"ultimaHa":18,"venceEm":13,"seguranca":true,"palavras":["autoteste do epirb","teste do epirb","teste da baliza","autoteste da baliza"],"fonte":"Agenda preditiva","ultima":"08/09/2026","vence":"09/10/2026","dn":13,"st":"D-30","rot":"D-13","tom":"warn"},{"id":"motores-oleo","t":"Troca de óleo e filtros dos motores","curto":"ÓLEO","equip":"Motores Cummins QSB6.7 305","sistema":"motores","quem":"oficina de motores","intervalo":"12 meses ou 450 h (o que vier antes)","meses":12,"ultimaHa":348,"venceEm":17,"horas":{"limite":450,"campos":["motor_bb_horimetro_h","motor_be_horimetro_h"],"atual":412.6,"faltam":37.4},"palavras":["oleo dos motores","oleo do motor","filtros dos motores"],"fonte":"Agenda preditiva","ultima":"13/10/2025","vence":"13/10/2026","dn":17,"st":"D-30","rot":"D-17","tom":"warn"},{"id":"gerador-revisao","t":"Revisão do gerador: óleo e filtros","curto":"REVISÃO","equip":"Gerador Onan QD 9","sistema":"gerador","quem":"técnico","intervalo":"12 meses ou 1.300 h","meses":12,"ultimaHa":341,"venceEm":24,"horas":{"limite":1300,"campos":["gerador_horimetro_h"],"atual":1236.4,"faltam":63.6},"palavras":["revisao do gerador","oleo do gerador","filtros do gerador"],"fonte":"Agenda preditiva","ultima":"20/10/2025","vence":"20/10/2026","dn":24,"st":"D-30","rot":"D-24","tom":"warn"},{"id":"seakeeper-anodo","t":"Anodo do trocador de calor do estabilizador","curto":"ANODO","equip":"Estabilizador Seakeeper 3","sistema":"estabilizador","quem":"técnico","intervalo":"6 meses","meses":6,"ultimaHa":149,"venceEm":35,"palavras":["anodo do estabilizador","anodo do seakeeper","anodo do trocador"],"fonte":"Agenda preditiva","ultima":"30/04/2026","vence":"31/10/2026","dn":35,"st":"D-60","rot":"D-35","tom":"tele"},{"id":"motores-rotor","t":"Troca do rotor da bomba de água salgada dos motores","curto":"ROTOR","equip":"Motores Cummins QSB6.7 305","sistema":"motores","quem":"oficina de motores","intervalo":"12 meses","meses":12,"ultimaHa":324,"venceEm":41,"palavras":["rotor da bomba de agua salgada","rotor dos motores","impeller dos motores","rotor do motor"],"fonte":"Agenda preditiva","ultima":"06/11/2025","vence":"06/11/2026","dn":41,"st":"D-60","rot":"D-41","tom":"tele"},{"id":"baterias","t":"Verificação do banco de baterias e conexões","curto":"VERIFICAÇÃO","equip":"Baterias Victron Energy (24 V e 12 V)","sistema":"eletrico","quem":"técnico","intervalo":"6 meses","meses":6,"ultimaHa":134,"venceEm":50,"palavras":["banco de baterias","conexoes das baterias","verificacao das baterias"],"fonte":"Agenda preditiva","ultima":"15/05/2026","vence":"15/11/2026","dn":50,"st":"D-60","rot":"D-50","tom":"tele"},{"id":"garmin-cartas","t":"Atualização de cartas e software dos eletrônicos","curto":"CARTAS","equip":"Plotters Garmin GPSMAP 1243xsv","sistema":"eletronicos","quem":"Lucas","intervalo":"12 meses","meses":12,"ultimaHa":299,"venceEm":66,"palavras":["cartas do plotter","cartas nauticas","atualizacao das cartas","software dos eletronicos"],"fonte":"Agenda preditiva","ultima":"01/12/2025","vence":"01/12/2026","dn":66,"st":"D-90","rot":"D-66","tom":"accent"},{"id":"clima-revisao","t":"Revisão anual da climatização","curto":"REVISÃO","equip":"Climatização Webasto FCF Platinum","sistema":"climatizacao","quem":"marina","intervalo":"12 meses","meses":12,"ultimaHa":279,"venceEm":86,"palavras":["revisao da climatizacao","revisao do ar condicionado"],"fonte":"Agenda preditiva","ultima":"21/12/2025","vence":"21/12/2026","dn":86,"st":"D-90","rot":"D-86","tom":"accent"},{"id":"motores-revisao","t":"Revisão anual dos motores","curto":"REVISÃO","equip":"Motores Cummins QSB6.7 305","sistema":"motores","quem":"oficina de motores","intervalo":"12 meses","meses":12,"ultimaHa":253,"venceEm":112,"palavras":["revisao dos motores","revisao anual dos motores"],"fonte":"Agenda preditiva","ultima":"16/01/2026","vence":"16/01/2027","dn":112,"st":"EM DIA","rot":"D-112","tom":"ok"},{"id":"seafire-inspecao","t":"Inspeção anual do sistema fixo de supressão","curto":"INSPEÇÃO","equip":"Sistema fixo de supressão de incêndio","sistema":"seafire","quem":"técnico","intervalo":"12 meses","meses":12,"ultimaHa":225,"venceEm":140,"seguranca":true,"palavras":["inspecao do sistema fixo","sistema fixo de supressao","inspecao do seafire"],"fonte":"Agenda preditiva","ultima":"13/02/2026","vence":"13/02/2027","dn":140,"st":"EM DIA","rot":"D-140","tom":"ok"}],
 "agendaFonte": "Agenda preditiva · Drive › Capitão IA v2 › 03 Agenda de manutenção",
 "tarefasEquipe": [{"id":"g01","n":"Revisar mangueiras do dessalinizador","venceEm":20,"quem":"técnico","meses":6,"sistema":"dessalinizador","origem":"equipe","vence":"2026-10-16","dn":20,"st":"D-30","rot":"D-20","tom":"warn"},{"id":"g02","n":"Lavar o convés e o hard-top","venceEm":5,"quem":"marina","meses":1,"sistema":"casco","origem":"equipe","vence":"2026-10-01","dn":5,"st":"D-30","rot":"D-5","tom":"warn"}],
 "documentos": [{"id":"tie","n":"Título de Inscrição da Embarcação (TIE)","cat":"Registro","venceEm":646,"emitidoHa":1180,"numero":"CIA-23-0417","nota":"renovação a cada 5 anos","fonte":"Controle de documentos","vence":"03/07/2028","dn":646,"st":"EM DIA","emitido":"04/07/2023"},{"id":"seguro","n":"Seguro da embarcação","cat":"Seguro","venceEm":19,"emitidoHa":346,"nota":"apólice guardada a bordo e no Drive","fonte":"Controle de documentos","vence":"15/10/2026","dn":19,"st":"VENCE EM 19 D","emitido":"15/10/2025"},{"id":"licenca","n":"Licença de Estação de rádio (VHF)","cat":"Licenças","venceEm":65,"nota":"rádios VHF fixo e portátil","fonte":"Controle de documentos","vence":"30/11/2026","dn":65,"st":"VENCE EM 65 D"},{"id":"laudo","n":"Laudo de vistoria anual","cat":"Laudos","venceEm":326,"emitidoHa":39,"nota":"laudo arquivado no Drive","fonte":"Controle de documentos","vence":"18/08/2027","dn":326,"st":"EM DIA","emitido":"18/08/2026"},{"id":"gar-estab","n":"Garantia do estabilizador","cat":"Garantias","venceEm":175,"nota":"Seakeeper 3","fonte":"Controle de documentos","vence":"20/03/2027","dn":175,"st":"EM DIA"},{"id":"gar-eletr","n":"Garantia dos eletrônicos","cat":"Garantias","venceEm":137,"nota":"plotters e radar Garmin","fonte":"Controle de documentos","vence":"10/02/2027","dn":137,"st":"EM DIA"},{"id":"doc-epirb","n":"Certificado do EPIRB (bateria e disparador hidrostático)","cat":"Segurança","venceEm":540,"nota":"validade conferida também na etiqueta do equipamento","fonte":"Controle de documentos","vence":"19/03/2028","dn":540,"st":"EM DIA"}],
 "docsFonte": "Controle de documentos · Drive › Capitão IA v2 › 02 Documentos",
 "abastecimentos": [],
 "abastFonte": "Registro de abastecimento · Drive › Capitão IA v2 › 06 Abastecimento",
 "regraAbast": "abastecer antes de 25 % do total dos tanques, 400 L de 1.600 L (Checklist de bordo § Abastecimento)",
 "diario": [{"id":"d03","diasAtras":2,"h":"17:10","sys":"Manutenção","tom":"warn","who":"técnico","pend":true,"ref":"gerador-rotor","t":"Inspeção do rotor do gerador não feita no prazo — reagendar; rotor de reserva em falta no estoque.","palavras":["rotor do gerador","impeller do gerador","rotor impeller do gerador"],"d":"24/09","iso":"2026-09-24T17:10:00-03:00"},{"id":"d04","diasAtras":3,"h":"19:30","sys":"Motores","tom":"accent","who":"Lucas","pend":false,"ref":"motores-rotor","t":"Motor BE 1 a 2 °C acima do BB em cruzeiro nos últimos dias, com picos acima de 88 °C — acompanhar; rotor da bomba de água salgada dos motores na agenda.","d":"23/09","iso":"2026-09-23T19:30:00-03:00"},{"id":"d05","diasAtras":6,"h":"11:05","sys":"Equipamentos","tom":"accent","who":"Lucas","pend":true,"ref":"clima-filtro","t":"Climatização da cabine de proa com fluxo fraco. Suspeita: filtro de água salgada sujo (limpeza atrasada).","palavras":["filtro de agua salgada","filtro da climatizacao","filtro do ar condicionado","filtro do ar-condicionado"],"d":"20/09","iso":"2026-09-20T11:05:00-03:00"},{"id":"d06","diasAtras":18,"h":"08:30","sys":"Segurança","tom":"ok","who":"Lucas","pend":false,"ref":"epirb-teste","t":"Autoteste do EPIRB feito: luz de teste conforme a etiqueta.","d":"08/09","iso":"2026-09-08T08:30:00-03:00"},{"id":"d07","diasAtras":21,"h":"10:00","sys":"Segurança","tom":"crit","who":"técnico","pend":true,"ref":"porao-teste","t":"Teste das bombas de porão adiado por chuva.","palavras":["bombas de porao","bomba de porao","teste das bombas"],"d":"05/09","iso":"2026-09-05T10:00:00-03:00"},{"id":"d08","diasAtras":29,"h":"16:25","sys":"Eletrônicos","tom":"accent","who":"Lucas","pend":false,"ref":"garmin-cartas","t":"Cartas do plotter desatualizadas; a atualização está na agenda.","d":"28/08","iso":"2026-08-28T16:25:00-03:00"},{"id":"d09","diasAtras":39,"h":"09:00","sys":"Documentos","tom":"ok","who":"Lucas","pend":false,"ref":"laudo","t":"Vistoria anual feita; laudo arquivado no Drive.","d":"18/08","iso":"2026-08-18T09:00:00-03:00"}],
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

    // nivel(campo, q): a regra única do CONTRATO §3.3 sobre D.replay.limites, escrita uma vez aqui e uma vez em Python (confere.nivel, que o
    // gerador usa nas janelas). {nivel: 'normal' | 'aviso' | 'critico', limite?, regime?} ou null (não avalia). As comparações são estritas e
    // sobre o valor como a tela mostra (as casas do D.campos); em /SOS-/ não lê o replay.
    function casasDe(c) { var d = D.campos && D.campos[c]; return d && typeof d.casas === 'number' ? d.casas : 0; }
    function numero(x) { return typeof x === 'number' && isFinite(x); }
    function fora(lim, v) {
      if (!lim) return null;
      if (lim.abaixo !== undefined && v < lim.abaixo) return lim.abaixo;
      if (lim.acima !== undefined && v > lim.acima) return lim.acima;
      return null;
    }
    function nivel(campo, q) {
      try {
        if (EM_SOS || !q) return null;
        var L = D.replay && D.replay.limites && D.replay.limites[campo], a, x, v, R, idx = null, k, g, r, lc, la, o;
        if (!L) return null;
        a = L.ativo_se;
        if (a) {
          x = q[a.campo];
          if (a.acima !== undefined) { if (!numero(x) || !(arred(x, casasDe(a.campo)) > a.acima)) return null; }
          else if (a.igual !== undefined) { if (x !== a.igual) return null; }
        }
        v = q[campo];
        if (!numero(v)) return null;
        v = arred(v, casasDe(campo));
        R = L;
        if (L.regimes) {
          R = null;
          for (k = 0; k < L.regimes.length; k++) {
            g = L.regimes[k]; r = q[g.rpm_campo];
            if (!numero(r)) continue;
            r = arred(r, 0);
            if ((g.rpm_de === undefined || g.rpm_de <= r) && (g.rpm_ate === undefined || r < g.rpm_ate)) { R = g; idx = k; break; }
          }
          if (!R) return null;
        }
        lc = fora(R.critico, v);
        la = lc === null ? fora(R.aviso, v) : null;
        o = lc !== null ? { nivel: 'critico', limite: lc } : la !== null ? { nivel: 'aviso', limite: la } : { nivel: 'normal' };
        if (idx !== null) o.regime = idx;
        return o;
      } catch (e) { return null; }
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

    A.off = off; A.ancora = ancora; A.prazoDe = prazoDe; A.docDe = docDe; A.rebase = rebase; A.nivel = nivel; A.trava = trava; A.contagens = contagens; A.instante = instante;
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
