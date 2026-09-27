/* Capitão IA — dados da embarcação (GERADO por ferramentas/demo/gerar_demo.py — não editar à mão).
   DEMO · DADOS FICTÍCIOS: Demonstração da plataforma Capitão IA: embarcação, leituras, agenda, documentos, diário, abastecimentos e guias de bordo são fictícios. Procedimentos de emergência são o padrão internacional, a confirmar com o protocolo de bordo. Modelos dos equipamentos, registro, Seafire e EPIRB: SEM DADOS.
   null = SEM DADOS (ou SEM LEITURA, em sensor). Cada grupo traz a fonte (arquivo no Drive › Capitão IA v2). */
window.CapitaoDados = {
 "versao": "26/09/2026",
 "demo": true,
 "selo": "DEMO · DADOS FICTÍCIOS",
 "aviso": "Demonstração da plataforma Capitão IA: embarcação, leituras, agenda, documentos, diário, abastecimentos e guias de bordo são fictícios. Procedimentos de emergência são o padrão internacional, a confirmar com o protocolo de bordo. Modelos dos equipamentos, registro, Seafire e EPIRB: SEM DADOS.",
 "embarcacao": {
  "nome": "Capitão IA",
  "modelo": null,
  "registro": null,
  "proprietario": "Lucas Araújo",
  "base": "Balneário Camboriú (SC)",
  "fuso": "America/Sao_Paulo",
  "mmsi": "710123456",
  "mmsiNota": "fictício · demonstração",
  "indicativo": null,
  "fonte": "dados informados pelo proprietário (26/09/2026) · MMSI fictício de demonstração"
 },
 "posicaoRef": {
  "lat": -26.99056,
  "lon": -48.63472,
  "nome": "Balneário Camboriú (centro)",
  "fonte": "Open-Meteo Geocoding (GeoNames 3471039)"
 },
 "mar": [
  [
   -26.99056,
   -48.63472
  ],
  [
   -26.995,
   -48.6
  ],
  [
   -27.0,
   -48.55
  ]
 ],
 "drive": {
  "raiz": "Drive › Capitão IA v2",
  "pastas": {
   "manuais": "01 Manuais e guias de bordo",
   "docs": "02 Documentos",
   "agenda": "03 Agenda de manutenção",
   "diario": "04 Diário de bordo",
   "tele": "05 Telemetria — coletor NMEA",
   "abast": "06 Abastecimento",
   "protocolos": "07 Protocolos de emergência"
  },
  "arquivos": {
   "leiame": "LEIA-ME — Capitão IA v2 (DEMO)",
   "g_gerador": "Guia de bordo (DEMO) — Gerador Onan",
   "g_seakeeper": "Guia de bordo (DEMO) — Estabilizador Seakeeper",
   "g_clima": "Guia de bordo (DEMO) — Climatização",
   "g_eletronicos": "Guia de bordo (DEMO) — Eletrônicos Garmin, áudio Fusion e VHF 315",
   "g_motores": "Guia de bordo (DEMO) — Motores Volvo Penta",
   "checklist": "Checklist de saída e chegada (DEMO)",
   "inventario": "Inventário de bordo (DEMO)",
   "documentos": "Controle de documentos (DEMO)",
   "agenda": "Agenda preditiva (DEMO)",
   "diario": "Diário de bordo (DEMO)",
   "snapshot": "snapshot_demo_20260926_1012.json",
   "abast": "Registro de abastecimento (DEMO)",
   "protocolo": "Protocolo de emergência — procedimento padrão"
  }
 },
 "equipamentos": [
  {
   "id": "motores",
   "nome": "Motores",
   "fabricante": "Volvo Penta",
   "modelo": null,
   "qtd": "2",
   "lados": "BB e BE",
   "guia": "g_motores"
  },
  {
   "id": "gerador",
   "nome": "Gerador",
   "fabricante": "Onan",
   "modelo": null,
   "qtd": "1",
   "guia": "g_gerador"
  },
  {
   "id": "estabilizador",
   "nome": "Estabilizador giroscópico",
   "fabricante": "Seakeeper",
   "modelo": null,
   "qtd": "1",
   "guia": "g_seakeeper"
  },
  {
   "id": "climatizacao",
   "nome": "Climatização",
   "fabricante": null,
   "modelo": null,
   "qtd": "SEM DADOS",
   "guia": "g_clima"
  },
  {
   "id": "eletronicos",
   "nome": "Eletrônicos de navegação",
   "fabricante": "Garmin",
   "modelo": null,
   "qtd": "SEM DADOS",
   "guia": "g_eletronicos"
  },
  {
   "id": "audio",
   "nome": "Áudio",
   "fabricante": "Fusion",
   "modelo": null,
   "qtd": "SEM DADOS",
   "guia": "g_eletronicos"
  },
  {
   "id": "vhf",
   "nome": "Rádios VHF",
   "fabricante": null,
   "modelo": "VHF 315",
   "qtd": "SEM DADOS",
   "guia": "g_eletronicos"
  },
  {
   "id": "epirb",
   "nome": "EPIRB",
   "fabricante": null,
   "modelo": null,
   "qtd": "SEM DADOS",
   "guia": null
  },
  {
   "id": "seafire",
   "nome": "Sistema de incêndio",
   "fabricante": "Seafire",
   "modelo": null,
   "qtd": "SEM DADOS",
   "guia": null
  }
 ],
 "equipNota": "Lista informada pelo proprietário (com \"…\": pode haver mais equipamentos). Modelos: SEM DADOS.",
 "snapshot": {
  "quando": "26/09/2026 10:12",
  "hora": "10:12",
  "dia": "26/09",
  "iso": "2026-09-26T10:12:00-03:00",
  "fonte": "coletor NMEA (DEMO) · snapshot_demo_20260926_1012.json",
  "estado": "Fundeado",
  "local": "enseada de Balneário Camboriú",
  "gps": {
   "lat": -26.993,
   "lon": -48.614,
   "texto": "26°59,58'S 048°36,84'W",
   "satelites": 26
  },
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
  "tanques": {
   "agua": 68.5,
   "cinzas": 21.0,
   "negras": 34.5
  },
  "diesel": {
   "bb": 54.0,
   "be": 52.0,
   "litros": 848,
   "capacidade": 1600,
   "tanques": "2 × 800 L",
   "hora": "26/09 09:31",
   "nota": "última leitura com motores ligados"
  },
  "motores": {
   "hora": "26/09 09:31",
   "estado": "desligados desde 09:31",
   "rpm": [
    700,
    690
   ],
   "oleo": [
    3.4,
    3.3
   ],
   "arref": [
    79,
    78
   ],
   "horimetro": [
    412.6,
    409.8
   ],
   "marcha": "neutro"
  },
  "gerador": {
   "estado": "ligado desde 09:35",
   "horas": 1236.4,
   "hora": "26/09 10:12"
  },
  "seakeeper": {
   "estado": "ligado",
   "hora": "26/09 10:12"
  },
  "porao": null,
  "ancora": null
 },
 "consumo": {
  "cruzeiro": {
   "nos": 18,
   "rpm": 2050,
   "lph": 68
  },
  "lenta": {
   "lph": 6.2
  },
  "periodo": "01/08–26/09/2026",
  "fonte": "telemetria (DEMO) · taxa de combustível dos dois motores",
  "desdeAbast": {
   "litros": 192,
   "desde": "12/09/2026",
   "horas": "2,8 h de motor por lado"
  }
 },
 "reserva": 0.1,
 "autonomia": {
  "horas": 11.2,
  "mn": 202,
  "lenta": 123
 },
 "serie24v": [
  {
   "d": "20/09",
   "min": 26.1,
   "max": 28.4
  },
  {
   "d": "21/09",
   "min": 26.0,
   "max": 28.6
  },
  {
   "d": "22/09",
   "min": 25.9,
   "max": 27.2
  },
  {
   "d": "23/09",
   "min": 25.8,
   "max": 27.0
  },
  {
   "d": "24/09",
   "min": 25.7,
   "max": 28.5
  },
  {
   "d": "25/09",
   "min": 25.9,
   "max": 27.1
  },
  {
   "d": "26/09",
   "min": 26.0,
   "max": 27.4
  }
 ],
 "agenda": [
  {
   "id": "porao-teste",
   "t": "Teste das bombas de porão e alarmes",
   "equip": "Bombas de porão",
   "quem": "técnico",
   "intervalo": "mensal",
   "ultima": "01/08/2026",
   "vence": "01/09/2026",
   "dn": -25,
   "st": "ATRASADA",
   "rot": "ATRASADA · 25 D",
   "tom": "crit",
   "fonte": "Agenda preditiva (DEMO)"
  },
  {
   "id": "clima-filtro",
   "t": "Limpeza do filtro de água salgada da climatização",
   "equip": "Climatização (fabricante SEM DADOS)",
   "quem": "marina",
   "intervalo": "mensal",
   "ultima": "10/08/2026",
   "vence": "10/09/2026",
   "dn": -16,
   "st": "ATRASADA",
   "rot": "ATRASADA · 16 D",
   "tom": "crit",
   "fonte": "Agenda preditiva (DEMO)"
  },
  {
   "id": "gerador-rotor",
   "t": "Inspeção do rotor (impeller) do gerador",
   "equip": "Gerador Onan",
   "quem": "técnico",
   "intervalo": "12 meses",
   "ultima": "24/09/2025",
   "vence": "24/09/2026",
   "dn": -2,
   "st": "ATRASADA",
   "rot": "ATRASADA · 2 D",
   "tom": "crit",
   "fonte": "Agenda preditiva (DEMO)"
  },
  {
   "id": "casco-anodos",
   "t": "Limpeza de casco e troca de anodos",
   "equip": "Casco",
   "quem": "marina",
   "intervalo": "6 meses",
   "ultima": "05/04/2026",
   "vence": "05/10/2026",
   "dn": 9,
   "st": "D-30",
   "rot": "D-9",
   "tom": "warn",
   "fonte": "Agenda preditiva (DEMO)"
  },
  {
   "id": "motores-oleo",
   "t": "Troca de óleo e filtros dos motores",
   "equip": "Motores Volvo Penta",
   "quem": "oficina Volvo Penta",
   "intervalo": "12 meses ou 450 h (o que vier antes)",
   "ultima": "13/10/2025",
   "vence": "13/10/2026",
   "horas": {
    "limite": 450,
    "atual": 412.6,
    "faltam": 37.4
   },
   "dn": 17,
   "st": "D-30",
   "rot": "D-17",
   "tom": "warn",
   "fonte": "Agenda preditiva (DEMO)"
  },
  {
   "id": "gerador-revisao",
   "t": "Revisão do gerador: óleo e filtros",
   "equip": "Gerador Onan",
   "quem": "técnico",
   "intervalo": "12 meses ou 1.300 h",
   "ultima": "20/10/2025",
   "vence": "20/10/2026",
   "horas": {
    "limite": 1300,
    "atual": 1236.4,
    "faltam": 63.6
   },
   "dn": 24,
   "st": "D-30",
   "rot": "D-24",
   "tom": "warn",
   "fonte": "Agenda preditiva (DEMO)"
  },
  {
   "id": "seakeeper-anodo",
   "t": "Anodo do trocador de calor do estabilizador",
   "equip": "Estabilizador Seakeeper",
   "quem": "técnico",
   "intervalo": "6 meses",
   "ultima": "30/04/2026",
   "vence": "31/10/2026",
   "dn": 35,
   "st": "D-60",
   "rot": "D-35",
   "tom": "tele",
   "fonte": "Agenda preditiva (DEMO)"
  },
  {
   "id": "baterias",
   "t": "Verificação do banco de baterias e conexões",
   "equip": "Sistema elétrico 24 V / 12 V",
   "quem": "técnico",
   "intervalo": "6 meses",
   "ultima": "15/05/2026",
   "vence": "15/11/2026",
   "dn": 50,
   "st": "D-60",
   "rot": "D-50",
   "tom": "tele",
   "fonte": "Agenda preditiva (DEMO)"
  },
  {
   "id": "garmin-cartas",
   "t": "Atualização de cartas e software dos eletrônicos",
   "equip": "Eletrônicos Garmin",
   "quem": "Lucas",
   "intervalo": "12 meses",
   "ultima": "01/12/2025",
   "vence": "01/12/2026",
   "dn": 66,
   "st": "D-90",
   "rot": "D-66",
   "tom": "accent",
   "fonte": "Agenda preditiva (DEMO)"
  },
  {
   "id": "clima-revisao",
   "t": "Revisão anual da climatização",
   "equip": "Climatização (fabricante SEM DADOS)",
   "quem": "marina",
   "intervalo": "12 meses",
   "ultima": "21/12/2025",
   "vence": "21/12/2026",
   "dn": 86,
   "st": "D-90",
   "rot": "D-86",
   "tom": "accent",
   "fonte": "Agenda preditiva (DEMO)"
  },
  {
   "id": "motores-revisao",
   "t": "Revisão anual dos motores",
   "equip": "Motores Volvo Penta",
   "quem": "oficina Volvo Penta",
   "intervalo": "12 meses",
   "ultima": "16/01/2026",
   "vence": "16/01/2027",
   "dn": 112,
   "st": "EM DIA",
   "rot": "D-112",
   "tom": "ok",
   "fonte": "Agenda preditiva (DEMO)"
  }
 ],
 "agendaFalta": [
  "EPIRB: teste e validade da bateria — equipamento SEM DADOS",
  "Seafire: inspeção e validade da carga — SEM DADOS"
 ],
 "agendaFonte": "Agenda preditiva (DEMO) · Drive › Capitão IA v2 › 03 Agenda de manutenção",
 "documentos": [
  {
   "n": "Título de Inscrição da Embarcação (TIE)",
   "cat": "Registro",
   "vence": null,
   "st": "SEM DADOS",
   "nota": "registro não informado",
   "dn": null,
   "fonte": "Controle de documentos (DEMO)"
  },
  {
   "n": "Seguro da embarcação",
   "cat": "Seguro",
   "vence": "15/10/2026",
   "nota": "apólice no Drive (DEMO)",
   "dn": 19,
   "st": "VENCE EM 19 D",
   "fonte": "Controle de documentos (DEMO)"
  },
  {
   "n": "Licença de estação de rádio (VHF)",
   "cat": "Licenças",
   "vence": "30/11/2026",
   "nota": "rádios VHF 315",
   "dn": 65,
   "st": "VENCE EM 65 D",
   "fonte": "Controle de documentos (DEMO)"
  },
  {
   "n": "Laudo de vistoria anual",
   "cat": "Laudos",
   "vence": "18/08/2027",
   "nota": "vistoria de 18/08/2026",
   "dn": 326,
   "st": "EM DIA",
   "fonte": "Controle de documentos (DEMO)"
  },
  {
   "n": "Garantia do estabilizador Seakeeper",
   "cat": "Garantias",
   "vence": "20/03/2027",
   "nota": "modelo SEM DADOS",
   "dn": 175,
   "st": "EM DIA",
   "fonte": "Controle de documentos (DEMO)"
  },
  {
   "n": "Garantia dos eletrônicos Garmin",
   "cat": "Garantias",
   "vence": "10/02/2027",
   "nota": "modelos SEM DADOS",
   "dn": 137,
   "st": "EM DIA",
   "fonte": "Controle de documentos (DEMO)"
  },
  {
   "n": "Certificado do EPIRB",
   "cat": "Segurança",
   "vence": null,
   "st": "SEM DADOS",
   "nota": "EPIRB sem dados",
   "dn": null,
   "fonte": "Controle de documentos (DEMO)"
  },
  {
   "n": "Nota fiscal de abastecimento · 12/09/2026",
   "cat": "Notas",
   "vence": null,
   "st": "A CONFERIR",
   "nota": "foto no Drive (DEMO) · sem valores no app",
   "dn": null,
   "fonte": "Controle de documentos (DEMO)"
  }
 ],
 "docsFonte": "Controle de documentos (DEMO) · Drive › Capitão IA v2 › 02 Documentos",
 "abastecimentos": [
  {
   "d": "12/09/2026",
   "litros": 620,
   "combustivel": "diesel",
   "local": "posto da marina · Balneário Camboriú",
   "st": "CONFERIDO",
   "nivelDepois": 65,
   "nota": "NF no Drive (DEMO)"
  },
  {
   "d": "02/08/2026",
   "litros": 540,
   "combustivel": "diesel",
   "local": "posto da marina · Balneário Camboriú",
   "st": "CONFERIDO",
   "nivelDepois": 71,
   "nota": "NF no Drive (DEMO)"
  }
 ],
 "abastFonte": "Registro de abastecimento (DEMO) · Drive › Capitão IA v2 › 06 Abastecimento",
 "regraAbast": "abastecer antes de 25 % em qualquer tanque (regra de bordo DEMO)",
 "diario": [
  {
   "d": "26/09",
   "h": "09:31",
   "iso": "2026-09-26T09:31:00-03:00",
   "sys": "Navegação",
   "tom": "tele",
   "who": "Lucas",
   "pend": false,
   "t": "Fundeado na enseada de Balneário Camboriú após 1 h 10 min de navegação. Motores desligados; gerador e Seakeeper ligados."
  },
  {
   "d": "26/09",
   "h": "08:20",
   "iso": "2026-09-26T08:20:00-03:00",
   "sys": "Navegação",
   "tom": "tele",
   "who": "Lucas",
   "pend": false,
   "t": "Saída da base com 4 pessoas a bordo. Checklist de saída feito; teste das bombas de porão continua pendente."
  },
  {
   "d": "24/09",
   "h": "17:10",
   "iso": "2026-09-24T17:10:00-03:00",
   "sys": "Manutenção",
   "tom": "warn",
   "who": "técnico",
   "pend": true,
   "t": "Inspeção do rotor do gerador não feita no prazo — reagendar."
  },
  {
   "d": "20/09",
   "h": "11:05",
   "iso": "2026-09-20T11:05:00-03:00",
   "sys": "Equipamentos",
   "tom": "accent",
   "who": "Lucas",
   "pend": true,
   "t": "Climatização da cabine de proa com fluxo fraco. Suspeita: filtro de água salgada sujo (limpeza atrasada)."
  },
  {
   "d": "12/09",
   "h": "15:40",
   "iso": "2026-09-12T15:40:00-03:00",
   "sys": "Combustível",
   "tom": "ok",
   "who": "Lucas",
   "pend": false,
   "t": "Abastecimento de 620 L de diesel no posto da marina; tanques em ≈ 65 %. NF no Drive."
  },
  {
   "d": "05/09",
   "h": "10:00",
   "iso": "2026-09-05T10:00:00-03:00",
   "sys": "Segurança",
   "tom": "crit",
   "who": "técnico",
   "pend": true,
   "t": "Teste das bombas de porão adiado por chuva."
  },
  {
   "d": "28/08",
   "h": "16:25",
   "iso": "2026-08-28T16:25:00-03:00",
   "sys": "Eletrônicos",
   "tom": "accent",
   "who": "Lucas",
   "pend": false,
   "t": "Cartas do plotter Garmin desatualizadas; atualização entra na agenda de dezembro."
  },
  {
   "d": "18/08",
   "h": "09:00",
   "iso": "2026-08-18T09:00:00-03:00",
   "sys": "Documentos",
   "tom": "ok",
   "who": "Lucas",
   "pend": false,
   "t": "Vistoria anual feita; laudo arquivado no Drive."
  }
 ],
 "diarioFonte": "Diário de bordo (DEMO) · Drive › Capitão IA v2 › 04 Diário de bordo",
 "equipe": {
  "perfis": [
   {
    "id": "lucas",
    "nome": "Lucas Araújo",
    "ini": "LA",
    "papel": "proprietário",
    "acesso": "total"
   }
  ],
  "apoio": [
   {
    "id": "marina",
    "papel": "Marina da base",
    "onde": "Balneário Camboriú",
    "para": "casco, filtros, vaga"
   },
   {
    "id": "oficina",
    "papel": "Oficina Volvo Penta",
    "onde": "SEM DADOS",
    "para": "motores"
   },
   {
    "id": "tecnico",
    "papel": "Técnico de bordo",
    "onde": "SEM DADOS",
    "para": "gerador, Seakeeper, elétrica, porão"
   },
   {
    "id": "posto",
    "papel": "Posto de combustível",
    "onde": "marina da base",
    "para": "diesel"
   }
  ],
  "nota": "Telefones: A CADASTRAR em Equipe (ficam só no aparelho)."
 },
 "faq": {
  "gerador": {
   "status": "PRONTO",
   "fonte": "Guia de bordo (DEMO) — Gerador Onan",
   "equip": "Gerador Onan",
   "modelo": null,
   "perguntas": [
    {
     "q": "Como ligar o gerador?",
     "passos": [
      {
       "n": "1",
       "t": "Com o gerador parado, confira o nível de óleo e o líquido de arrefecimento. Abra a válvula de fundo da entrada de água salgada e confira se o filtro de água salgada está limpo. Ligue a ventilação do compartimento por alguns minutos se houver cheiro de combustível.",
       "secao": "1 · Antes de ligar"
      },
      {
       "n": "2",
       "t": "No painel do gerador, pressione e segure PARTIDA até o motor pegar. Aguarde a tensão e a frequência estabilizarem no painel. Só depois transfira as cargas no quadro elétrico, uma de cada vez; ligue a climatização por último.",
       "secao": "2 · Ligar"
      },
      {
       "n": "3",
       "t": "Com o gerador ligado, confira a saída de água pelo escapamento. Sem água saindo, desligue na hora: é sinal de falta de refrigeração (válvula de fundo fechada, filtro entupido ou rotor danificado).",
       "secao": "3 · Água no escapamento"
      }
     ]
    },
    {
     "q": "Como desligar o gerador?",
     "passos": [
      {
       "n": "1",
       "t": "Retire as cargas no quadro elétrico. Deixe o gerador funcionar de 3 a 5 minutos sem carga para esfriar e pressione PARADA. Feche a válvula de fundo se o barco for ficar parado por vários dias.",
       "secao": "4 · Desligar"
      }
     ]
    },
    {
     "q": "Alarme de alta temperatura",
     "passos": [
      {
       "n": "1",
       "t": "Desligue o gerador. Verifique a válvula de fundo, o filtro de água salgada e o rotor (impeller). Nunca abra a tampa do arrefecimento com o motor quente. Registre o alarme no diário.",
       "secao": "5 · Alarme de alta temperatura"
      }
     ]
    },
    {
     "q": "Alarme de baixa pressão de óleo",
     "passos": [
      {
       "n": "1",
       "t": "Desligue o gerador e confira o nível de óleo com ele parado. Se o nível estiver correto e o alarme voltar, não religue: chame o técnico de bordo.",
       "secao": "6 · Alarme de baixa pressão de óleo"
      }
     ]
    },
    {
     "q": "Quantas horas tem e quando revisar?",
     "passos": [
      {
       "n": "1",
       "t": "O horímetro aparece no painel do gerador e na telemetria. No snapshot de demonstração de 26/09/2026 10:12: 1.236,4 h, gerador ligado desde 09:35.",
       "secao": "8 · Horímetro"
      },
      {
       "n": "2",
       "t": "Óleo e filtros: 12 meses ou 1.300 h (o que vier antes). Rotor (impeller): inspeção a cada 12 meses. Os intervalos oficiais estão no manual do fabricante — modelo SEM DADOS: confirmar.",
       "secao": "7 · Manutenção na agenda"
      }
     ]
    }
   ]
  },
  "estabilizador": {
   "status": "PRONTO",
   "fonte": "Guia de bordo (DEMO) — Estabilizador Seakeeper",
   "equip": "Estabilizador Seakeeper",
   "modelo": null,
   "perguntas": [
    {
     "q": "Como ligar antes de sair?",
     "passos": [
      {
       "n": "1",
       "t": "O estabilizador precisa de energia AC para acelerar o volante: gerador ligado ou tomada do cais. Sem AC, o display avisa e o volante não acelera.",
       "secao": "1 · Energia"
      },
      {
       "n": "2",
       "t": "Ligue pelo display com antecedência: a estabilização só começa quando o volante chega à rotação de operação e o display indica pronto. O tempo de aceleração depende do modelo — SEM DADOS neste guia.",
       "secao": "2 · Ligar antes de sair"
      },
      {
       "n": "3",
       "t": "O botão de estabilização liga e desliga o efeito sem parar o volante. Em manobra de marina, deixe a estabilização desligada se o display recomendar.",
       "secao": "3 · Estabilizar"
      }
     ]
    },
    {
     "q": "Como desligar ao atracar?",
     "passos": [
      {
       "n": "1",
       "t": "Desligue pelo display. O volante continua girando por muito tempo depois de desligado; mantenha a energia até o display indicar que parou.",
       "secao": "4 · Desligar ao atracar"
      },
      {
       "n": "2",
       "t": "Nunca abra tampas nem faça manutenção com o volante girando. Confira no display que a rotação está em zero antes de qualquer serviço.",
       "secao": "5 · Segurança"
      }
     ]
    },
    {
     "q": "Apareceu um alarme",
     "passos": [
      {
       "n": "1",
       "t": "Anote o código mostrado no display e registre no diário com a hora. A tabela de códigos está no manual do fabricante — MANUAL NO DRIVE (não carregado na demonstração).",
       "secao": "6 · Alarmes"
      }
     ]
    },
    {
     "q": "Manutenção",
     "passos": [
      {
       "n": "1",
       "t": "Anodo do trocador de calor: a cada 6 meses (agenda de demonstração). Outros itens: manual do fabricante, modelo SEM DADOS.",
       "secao": "7 · Manutenção na agenda"
      }
     ]
    }
   ]
  },
  "eletronicos": {
   "status": "PRONTO",
   "fonte": "Guia de bordo (DEMO) — Eletrônicos Garmin, áudio Fusion e VHF 315",
   "equip": "Eletrônicos Garmin · Fusion · VHF 315",
   "modelo": null,
   "perguntas": [
    {
     "q": "Homem ao mar no plotter",
     "passos": [
      {
       "n": "1",
       "t": "Ao ver alguém cair na água, acione a função MOB do plotter Garmin: a posição fica marcada e o plotter mostra o rumo de volta. Veja também o protocolo de emergência.",
       "secao": "1 · Plotter Garmin: homem ao mar"
      }
     ]
    },
    {
     "q": "Piloto automático",
     "passos": [
      {
       "n": "1",
       "t": "Deixe o piloto automático em espera (standby) antes de manobrar na marina e sempre que houver gente na água. Engate só em área livre, com a rota conferida no plotter.",
       "secao": "2 · Piloto automático"
      }
     ]
    },
    {
     "q": "Alarme de âncora",
     "passos": [
      {
       "n": "1",
       "t": "Ao fundear, ative o alarme de âncora no plotter e defina o raio conforme o cabo lançado e o espaço de giro. O barco não tem sensor de âncora: a posição do ferro fica SEM LEITURA.",
       "secao": "3 · Alarme de âncora"
      }
     ]
    },
    {
     "q": "Rádio VHF 315: canal 16 e DSC",
     "passos": [
      {
       "n": "1",
       "t": "Mantenha o canal 16 em escuta permanente. A dupla escuta acompanha o canal 16 e um canal de trabalho ao mesmo tempo.",
       "secao": "4 · Rádio VHF 315: escuta"
      },
      {
       "n": "2",
       "t": "O botão de socorro DSC (DISTRESS) só envia a identificação se o MMSI estiver programado no rádio. Na demonstração o MMSI 710123456 é fictício; no barco real, programe o MMSI do registro.",
       "secao": "5 · Rádio VHF 315: DSC"
      }
     ]
    },
    {
     "q": "Parear o celular no áudio Fusion",
     "passos": [
      {
       "n": "1",
       "t": "Para parear o celular: escolha a fonte Bluetooth no controle Fusion, deixe o aparelho visível e selecione o Fusion na lista de Bluetooth do celular. O volume é ajustado por zona.",
       "secao": "6 · Áudio Fusion: Bluetooth"
      }
     ]
    }
   ]
  },
  "climatizacao": {
   "status": "PRONTO",
   "fonte": "Guia de bordo (DEMO) — Climatização",
   "equip": "Climatização",
   "modelo": null,
   "perguntas": [
    {
     "q": "Como ligar a climatização?",
     "passos": [
      {
       "n": "1",
       "t": "Confira a válvula de fundo aberta e o filtro de água salgada limpo. Com energia AC (gerador ou cais), ligue a bomba de água salgada no painel e depois o controle da cabine.",
       "secao": "1 · Ligar"
      },
      {
       "n": "2",
       "t": "No controle de cada cabine escolha frio, calor ou ventilação e ajuste a temperatura desejada. Com o gerador, ligue as cabines uma de cada vez.",
       "secao": "2 · Modos e temperatura"
      }
     ]
    },
    {
     "q": "Alarme de fluxo",
     "passos": [
      {
       "n": "1",
       "t": "Alarme de fluxo ou de alta pressão quase sempre é falta de água salgada: filtro sujo, válvula de fundo fechada ou bomba desligada. Desligue a unidade, limpe o filtro e religue.",
       "secao": "3 · Alarme de fluxo"
      }
     ]
    },
    {
     "q": "Ar fraco na cabine",
     "passos": [
      {
       "n": "1",
       "t": "Fluxo de ar fraco na cabine: limpe o filtro de ar da unidade daquela cabine. Se continuar, registre no diário e chame a marina.",
       "secao": "4 · Fluxo de ar fraco"
      }
     ]
    },
    {
     "q": "Como desligar?",
     "passos": [
      {
       "n": "1",
       "t": "Desligue pelo controle das cabines e depois a bomba de água salgada. Ao deixar o barco, feche a válvula de fundo se a climatização não for usada.",
       "secao": "5 · Desligar"
      }
     ]
    }
   ]
  }
 },
 "guias": {
  "g_gerador": "Guia de bordo (DEMO) — Gerador Onan",
  "g_seakeeper": "Guia de bordo (DEMO) — Estabilizador Seakeeper",
  "g_clima": "Guia de bordo (DEMO) — Climatização",
  "g_eletronicos": "Guia de bordo (DEMO) — Eletrônicos Garmin, áudio Fusion e VHF 315",
  "g_motores": "Guia de bordo (DEMO) — Motores Volvo Penta",
  "checklist": "Checklist de saída e chegada (DEMO)",
  "protocolo": "Protocolo de emergência — procedimento padrão"
 },
 "protocolos": {
  "rotulo": "procedimento padrão — confirmar com o protocolo de bordo",
  "fonte": "Protocolo de emergência — procedimento padrão · Drive › Capitão IA v2 › 07 Protocolos de emergência",
  "canal16": {
   "canal": "16",
   "mhz": "156,800",
   "fonte": "canal 16 e MMSI informados pelo proprietário (MMSI fictício de demonstração)"
  },
  "roteiro": [
   "MAYDAY, MAYDAY, MAYDAY",
   "AQUI É CAPITÃO IA, CAPITÃO IA, CAPITÃO IA",
   "MMSI 710123456 (FICTÍCIO · DEMONSTRAÇÃO)",
   "POSIÇÃO — LEIA NO PLOTTER AGORA",
   "NATUREZA DO PERIGO: ________",
   "PESSOAS A BORDO: ________",
   "AUXÍLIO NECESSÁRIO: ________",
   "CÂMBIO"
  ],
  "mob": [
   "Grite HOMEM AO MAR e o lado (bombordo ou boreste). Jogue a boia ou qualquer objeto que flutue.",
   "Uma pessoa só aponta para quem caiu, sem perder de vista. Marque MOB no plotter Garmin.",
   "Volte devagar, com o motor em neutro perto da pessoa (hélice). Se perder de vista: MAYDAY no canal 16 com a posição da marca MOB."
  ],
  "seafire": null,
  "epirb": null
 }
};
