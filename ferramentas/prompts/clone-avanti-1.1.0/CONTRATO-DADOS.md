# Contrato de dados 1.1.0 — `window.CapitaoDados` (final da Fase 1)

> Desenhado na sessão de 22/10/2026 por 3 projetistas independentes, 2 juízes e um crítico de completude, a partir do PROMPT, da PARIDADE e do código da 1.0.9 + Fase 0b.
> Os scripts de conferência citados (`laco.py`, `revisao2-scripts/…`) ficaram fora do repositório; os números que eles mediram estão aqui.
> Os pontos do §8.2 foram resolvidos pelo orquestrador com a proposta de cada linha (ver a PARIDADE.md, Andamento da Fase 1).


Síntese das três propostas da Fase 1. A base é a de **segurança e travas primeiro**, com os enxertos aprovados pelos juízes e a correção de todos os erros graves apontados (§7). Este texto vale sozinho: nenhuma seção depende de outro documento.

- Nada foi escrito em `/home/user/CapitaoIA_v2` nem na pasta do Avanti.
- Os números das §2, §3 e §5 saíram de scripts de desenho rodados no rascunho, em `scratchpad/fase1/sintese-scripts/` e, na 2ª revisão do crítico, em `scratchpad/fase1/revisao2-scripts/`:
  - `laco.py`: quadros-chave, ruído por hash, janela do alarme, emenda e contadores;
  - `rota.py` e `quadro.py`: pernas, fator do dia, guinada limitada, corrente, ETA linearizada, vento aparente e o quadro completo em 4 instantes;
  - `emenda.py` e `emenda2.py`: `circuitos_dia` primo com 576, folga de cada chegada até a emenda de 150 s e o quadro de 12:01:00 / 12:01:45 com 19 circuitos;
  - `textos3.py`: 233 textos deste contrato contra as 8 regex do `termos.json` (cada uma com a sua flag) e contra as travas extras da §6.3. Resultado: **0 casamentos**. `textos4.py`: os textos novos da revisão do crítico, mais a `AFIRMA_REAL` nova (com fim de palavra) e a regex de coordenada do §2.8: **0 casamentos**;
  - `colisao.py`: cada nome escolhido contado **por substring** (o modelo, cada parte dele e a base) na pasta do Avanti e nas duas listas privadas, imprimindo só contagens. Resultado: 0 para todos, menos `Seakeeper 3` (1; exceção para o ok, §8.2). É a asserção `COLISAO_MODELOS` (§6.3);
  - `cambio.py` (revisão 2): a emenda do `c[âa]mbio` no DINHEIRO contra os 7 casos que barram e os 23 que passam do `termos-casos.json` (nenhum muda) e contra os casos novos do §8.2;
  - `mede.py` (revisão 2, só leitura, servindo a árvore de hoje): a ficha de hoje tem **9.319** letras (por bloco no §6.1);
  - `textos5.py` (revisão 2): os 140 textos novos (agenda, `palavras`, checklist, sensores, `snapshot.quadro`, guia do estabilizador, a linha do CONCLUIR) contra as 8 regex, a `AFIRMA_REAL`, a coordenada do §2.8 e a `emergencia()` portada com a lista ampliada: **0 casamentos**; e a conta da agenda: 14 de 14 com `DIAS_MESES`, 3 atrasadas, a mesma ordem por `dn`;
  - `ficha.py` e `tamanho.py`: crescimento da ficha e tamanho do `capitao-dados.js`.
- Do Avanti 1.24.0 entrou só a **forma** dos dados (FAQ, sensores, checklists, gráficos, peças, prestadores). Nenhum valor dele aparece aqui.

---

## 0. Princípios (decidem cada campo)

1. **SOS fora de tudo.** S1/S2 leem só `D.embarcacao.nome` e `D.protocolos`, e se comportam igual com `simulacao` `true` ou `false`. Em `/SOS-/`, `CapitaoAgora.instante()` devolve `null`: nem o cérebro que o SOS carrega acha um quadro (§1.3). Em `/SOS-/` ninguém lê `D.simulacao` (nem a microtarefa do rodapé nem o `addDiario`), e a linha que o SOS grava no diário nunca leva `sim` (§1.25, §4.1).
2. **Identificação de rádio e de socorro nunca é gerada.** Indicativo, HEX ID, telefone e lugar de equipamento de salvatagem não existem como campo. Existe só o texto de instrução, numa fonte só (`D.protocolos`).
3. **Dois MMSI com nomes diferentes.** `embarcacao.mmsi` é o `MMSI_NUM` (710123456). `protocolos.mmsiRadio` é o `MMSI_RADIO` (só texto). Nove dígitos fora de `embarcacao.mmsi` fazem o gerador falhar.
4. **Identificador gerado não imita outro.** O registro não casa inscrição numérica, placa de carro (3 formatos), HIN, MMSI, telefone, CPF/CNPJ nem HEX ID. O que não precisa de número fica sem número: o campo é omitido.
5. **Número de procedimento vem do guia de bordo gerado.** Do fabricante só entram números públicos, com "cerca de". Nada de capacidade, torque, código de alarme ou página de manual inventados.
6. **Nenhum texto denuncia o fictício nem afirma o real.** A única frase sobre isso é a da `sobreDados`, e ela fica no cérebro.
7. **As 8 regex valem sobre todo o `D`**, o `base-conhecimento.json`, o `faq-equipamentos.json` e `ferramentas/demo/fontes/**`. As invariantes extras (§6.3) são asserções do gerador, não lista de termos.
8. **Coordenada só em campo numérico** (`posicaoRef`, `mar`, `rota`, `snapshot.gps.lat/lon`, `snapshot.quadro` e o quadro em execução). A única exceção é o texto legado `snapshot.gps.texto` **(L)**, enquanto houver leitor (§1.17; asserção `COORD_TEXTO`). A série pública da pasta 05 vai sem posição.
9. **O laço é função pura do instante absoluto.** Há uma âncora só (07:00 no fuso), um formatador só e um instante só (`CapitaoAgora.instante()`). O gerador manda e o cliente só expande.
10. **Coerência por construção.** Janelas de alarme, faixas e textos dos guias saem de uma constante só e do mesmo algoritmo, com asserção no gerador.
11. **Compatibilidade de fase.** Campo que um leitor de hoje usa fica na forma de hoje (marcado **(L)**) até a fase que reescreve o leitor. Nenhuma quebra fora da tabela da Fase 7.
12. **Modo real intacto.** O caminho `null → SEM DADOS / SEM LEITURA` continua nos leitores. O gerador da próxima embarcação recusa emitir o que só existe na simulação.

---

## 1. Árvore de campos e APIs

### 1.0 Convenções

- **(R)**: o rebase do rodapé reescreve o campo. O gerador grava também o valor calculado com a data de referência fixa (`REF` = 26/09/2026), como **reserva**: se o rodapé falhar, as telas mostram as datas da `REF`.
- **Sem reserva, de propósito:** `abastecimentos` (lista vazia), d01, d02 e a nota fiscal do abastecimento. Só existem na simulação e entram pela microtarefa (`D.replay.diaDeBordo`, §4.1). Sem o rodapé (ou com `simulacao: false`), os leitores dessas listas caem no caminho vazio do modo real: a G2 mostra "ÚLTIMO ABASTECIMENTO SEM DADOS · nenhum registro" (o caminho de hoje, que só aparece na simulação se o rodapé falhar) e o cérebro omite a linha "Abastecimentos registrados" (guarda de 1 linha no `consumo`, C8; a ficha já tem, `capitao-brain.js:595-596`).
- **(L)**: legado, na forma de hoje, até a fase indicada.
- **Nenhum valor é `null`, `''`, `NaN` ou `-0`.** O que não se aplica é omitido. A única lista vazia permitida no arquivo gerado é `abastecimentos`, que a microtarefa do rodapé preenche antes de qualquer leitor, só com `simulacao: true` e fora do SOS (§1.10, §4.1).
- **Vale também para o `D` em execução**, que o `replay.py` percorre depois do rodapé:
  - o rebase **omite** `dn`, `vence`, o `st` de prazo e `emitido` quando o item não tem o deslocamento (nunca grava `null` nem `''`); o gerador também não grava `dn: None` na reserva, como faz hoje com os documentos sem validade (`gerar_demo.py:422`);
  - o `snapshot.quadro` não leva `alarmes` (ausência = sem alarme; o leitor usa `q.alarmes || []`);
  - o rebase e a `insereDiaDeBordo()` mudam as listas **no lugar**: `sort` no próprio array e `splice` para inserir ou substituir, em `agenda`, `tarefasEquipe`, `documentos`, `diario` e `abastecimentos`. Telas e cérebro guardam a referência; nenhum `D.<lista> = …` a troca, e a virada das 07:00 com a página aberta vale para todos.
- Os deslocamentos de data são **positivos para o passado** (`ultimaHa`, `emitidoHa`, `diasAtras` = "há N dias") e com sinal para o futuro (`venceEm` negativo = atrasado).
- Duas bases de data:
  - **hoje** (calendário do aparelho no fuso): agenda, tarefas da equipe, documentos, o **diário fixo** (d03–d09) e `versao`;
  - **dia de bordo** (data da âncora; antes das 07:00, a de ontem): as linhas do dia de bordo (d01, d02, `ab-0…ab-2` e a nota fiscal do abastecimento) e `serie24v`;
  - o diário fixo vai na base **hoje** porque as linhas com `ref` têm de cair no mesmo dia do alvo também das 00:00 às 07:00: d06 = `ultima` do `epirb-teste`, d09 = `emitido` do laudo, d03 = `vence` do `gerador-rotor`. A ordem do diário não muda: a linha fixa mais nova (d03, hoje − 2 às 17:10) fica sempre abaixo da d01 (dia de bordo às 07:00), antes e depois das 07:00. Teste em 06:59:59 e 07:00:01 (§4.1, §6.5).
- Todo texto passa pelas 8 regex e pelas invariantes da §6.3.
- Serializador: dicionários indentados até a profundidade 2, listas numa linha, chaves em ordem fixa e `repr` de float do Python.

### 1.1 Flags e metadados

| Caminho | Tipo | Valor | Quem lê (fase) | Trava |
|---|---|---|---|---|
| `simulacao` | bool | `true` | replay (2), cérebro e telas (3/4), cliente da IA (6), `replay.py` (7) | lida a cada chamada, nunca guardada na carga; S1/S2 não leem, nem o rodapé e o `addDiario` quando rodam em `/SOS-/` (§1.3). O texto `"simulacao": true` aparece **uma vez** no arquivo (asserção) |
| `demo` | bool | `false` | as 36 leituras de `D.demo`; rodapé do `capitao-auth.js` | some o "(DEMO)" de uma vez (b) |
| `selo`, `aviso` | — | **omitidos** | — | nenhum campo de selo (b) |
| `versao` | 'dd/mm/aaaa' **(R)** | hoje | G1 "prazos contados a partir de" (já lê: `G1-Documentos-Web.dc.html:237`, `G1-Documentos-Mobile.dc.html:186`); no C7, `C1-Leme-Web.dc.html:214`, `C2-Leme-Mobile.dc.html:137` e `B1-Carta-Web.dc.html:317` passam a ler `D.versao` (guarda de 1 linha, §6.2) | base hoje |
| `posicaoRef`, `mar` | iguais a hoje | GeoNames 3471039 | clima e maré **reais** (§2.5 do PROMPT) | nunca no texto da ficha |
| `drive` | `{raiz, pastas, arquivos}` | §1.5 | "Fonte:" de todas as telas | nome de arquivo sem "DEMO" nem "snapshot" |
| `agendaFonte`, `docsFonte`, `abastFonte`, `diarioFonte` | str | `<título de drive.arquivos> · Drive › Capitão IA v2 › <pasta>`: `Agenda preditiva · Drive › Capitão IA v2 › 03 Agenda de manutenção` · `Controle de documentos · Drive › Capitão IA v2 › 02 Documentos` · `Registro de abastecimento · Drive › Capitão IA v2 › 06 Abastecimento` · `Diário de bordo · Drive › Capitão IA v2 › 04 Diário de bordo` | 12, 10, 6 e 7 leituras (lista abaixo); sem o campo, o leitor cai em "SEM DADOS" | mesmo nome de hoje; só o "(DEMO)" sai (C2) |

Leitores dos quatro `*Fonte` (grep de `D.<campo>` fora do `capitao-dados.js`):
- `agendaFonte` (12): A1-Ponte-Web:372, A2-Ponte-Mobile:254, B1-Carta-Web:320/:321/:326, B2-Carta-Mobile:124/:181, C1-Leme-Web:214, C2-Leme-Mobile:137, G4-Equipe-Web:332, G4-Equipe-Mobile:298 e `capitao-brain.js:101`;
- `docsFonte` (10): A2:254, B1:329, B2:181, G1-Documentos-Web:219/:248/:264, G1-Documentos-Mobile:169/:199/:215 e `capitao-brain.js:102`;
- `abastFonte` (6): B1:339, G2-Abastecimento-Web:238, G2-Abastecimento-Mobile:199, G4-Web:332, G4-Mobile:298 e `capitao-brain.js:103`;
- `diarioFonte` (7): A2:254, B1:345, B2:181, G3-Diario-Web:185, G3-Diario-Mobile:157 e `capitao-brain.js:72`/`:104`.

### 1.2 `embarcacao`

| Caminho | Tipo / un. | Valor | Quem lê (fase) | Trava |
|---|---|---|---|---|
| `nome` | str | `Capitão IA` | tudo | **único dado do barco que o SOS mostra** |
| `fabricante` | str | `Estaleiro Marévia` | rota `embarcacao`, `## Embarcação`, Embarcação e Documentos (3/4) | marca fictícia sem colisão (§2.1) |
| `modelo` | str | `Marévia 40 HT` | idem | — |
| `rotulo` | str pronta | `Marévia 40 HT · 12,40 m · 2023` | moldura (4), ficha (3) | gerada dos campos abaixo |
| `motorizacao` | str pronta | `2 × Cummins QSB6.7 305 · eixo` | moldura (4), rota `embarcacao` (3) | idem |
| `ano` | int | `2023` | idem | — |
| `registro` | str | `CIA-23-0417` | idem; = `documentos[tie].numero` | **nunca** em S1/S2; formato da §2.3 |
| `comprimento` | number, m | `12.4` | rota `embarcacao` (3) | — |
| `boca` | number, m | `3.95` | idem | — |
| `calado` | number, m (**nome fixo**) | `1.1` | rotas `embarcacao` e `profundidade` (3); `replay.py` modo real (`calado = null` → SEM DADOS) | a palavra "calado" fica **fora de todo trecho da base até a Fase 3** (§6.3 `CALADO_FORA`) |
| `deslocamento` | number, t | `10.4` | rota `embarcacao` (3) | cabe no Seakeeper 3 (até cerca de 10,5 t; revisão 2 do C4, §2.1) |
| `lotacao` | int | `12` | rota `embarcacao` (3) | **nunca** em `salvatagem`, `sos` nem roteiro |
| `pessoasBordo` | int | `4` | rota `pessoas`, `## Navegação agora` (3) | = o número da linha de saída do diário (asserção). **Nunca** nas chaves do §2.2, no `## Emergência` nem no diário com alerta. **Fora do quadro** |
| `tanques` | obj | `{diesel_l: 1600, diesel_n: 2, agua_l: 400, cinzas_l: 100, negras_l: 100}` | diesel BB/BE, "≈ N L" (2/4) | — |
| `un` | `{campo: unidade}` | `{comprimento: 'm', boca: 'm', calado: 'm', deslocamento: 't', lotacao: 'pessoas', pessoasBordo: 'pessoas'}` | formatador (3/4) | — |
| `proprietario`, `base`, `fuso` | str | iguais a hoje; `fuso: 'America/Sao_Paulo'` | rodapé, ficha | `base` sai do cabeçalho do SOS na 1b |
| `mmsi` | str (`MMSI_NUM`) | `'710123456'` | **só** Embarcação, Documentos, F3 web e app ("MMSI (cadastro do app)"), `## Embarcação` e a 2ª linha da rota `mmsi` | nunca na mesma frase que "programe", "DSC", "AIS" ou "rádio" |
| `mmsiNota` | str | `fictício · demonstração` **até a 1b**, que a apaga | S1:156, S2:131, cérebro:202, `F3-FAQ-Eletronicos-Web.dc.html:223` e `F3-FAQ-Eletronicos.dc.html:217` (`linha('MMSI da embarcação (DSC)', E.mmsi \|\| SD, E.mmsiNota \|\| 'MMSI ' + SD, …)`) | única exceção da varredura de termos na Fase 1. No commit da 1b, as duas F3 trocam essa linha: rótulo `protocolos.mmsiRotulo`, valor `E.mmsi`, nota `'No MAYDAY e no DSC: ' + protocolos.mmsiRadio` (frase à parte do número). Sem isso, a F3 passaria a mostrar "MMSI SEM DADOS" ao lado do rótulo que o §2.2 do PROMPT tira |
| `indicativo` | — | **chave inexistente** | — | prefixos PP–PY e ZV–ZZ são reais; o texto fica em `protocolos.indicativo` |
| `fonte` | str | `cadastro da embarcação no app (proprietário)` | ficha | sem "fictício" |

### 1.3 `protocolos` (fonte única do SOS, do roteiro, dos cartões EM e da página EMERGÊNCIA do Guia)

Gerado no commit C6. Os leitores mudam na 1b.

| Caminho | Tipo | Valor (texto final, conferido) |
|---|---|---|
| `rotulo` | str | `procedimento padrão — confirmar com o protocolo de bordo` (EXCEÇÃO do §3) |
| `fonte` | str | `Protocolo de emergência — procedimento padrão · Drive › Capitão IA v2 › 07 Protocolos de emergência` |
| `mmsiRadio` | str | `MMSI do rádio de bordo (etiqueta / Licença de Estação)` |
| `mmsiRotulo` | str | `MMSI (cadastro do app)` |
| `indicativo` | str | `o da Licença de Estação (no rádio)` |
| `plotter` | str | `POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER · PESSOAS: CONTE AGORA` (troca do `emergenciaAte`, §2.2 do PROMPT) |
| `hud` | str | `POSIÇÃO · LEIA NO PLOTTER` (HUD com `alerta: true`) |
| `canal16` | obj | `{canal: '16', mhz: '156,800', fonte: 'Protocolo de emergência — procedimento padrão · MAYDAY · canal 16'}` |
| `roteiro[8]` | str[] | `MAYDAY, MAYDAY, MAYDAY` · `AQUI É CAPITÃO IA, CAPITÃO IA, CAPITÃO IA` · `MMSI — LEIA NA ETIQUETA DO RÁDIO (Licença de Estação)` · `POSIÇÃO — LEIA NO PLOTTER AGORA` · `NATUREZA DO PERIGO: ________` · `PESSOAS A BORDO: conte agora` · `AUXÍLIO NECESSÁRIO: ________` · `CÂMBIO` |
| `mob[3]` | str[] | "Grite HOMEM AO MAR e o lado (bombordo ou boreste). Jogue a boia ou qualquer objeto que flutue." · "Uma pessoa só aponta para quem caiu, sem perder de vista. Marque MOB no plotter." · "Volte devagar, com o motor em neutro perto da pessoa (hélice). Se perder de vista: MAYDAY no canal 16 com a posição da marca MOB lida no plotter." |
| `seafire.passos[5]` | str[] | "Fogo no motor ou alarme do sistema fixo: desligue motores e gerador e corte a ventilação do motor." · "Se o sistema não disparou sozinho e há fogo no motor, use o disparo manual." · "Não abra o acesso ao motor depois da descarga: espere o tempo indicado na etiqueta do sistema e o motor esfriar." · "Fogo pequeno fora do motor: extintor portátil na base das chamas, de costas para a saída." · "Fogo que não apaga: MAYDAY no canal 16 e prepare o abandono." |
| `seafire.nota`, `epirb.nota` | str | `modelo, validade e acionamento: veja a etiqueta do equipamento` |
| `epirb.passos[4]` | str[] | "Só em perigo grave e iminente, depois do MAYDAY (ou sem rádio)." · "Acione conforme a etiqueta do equipamento e deixe a antena para cima, com céu aberto." · "Leve o EPIRB para a balsa ou mantenha-o flutuando preso por um cabo. Não desligue até o resgate." · "Disparo por engano: desligue e avise no canal 16." |
| `epirb.teste[2]` | str[] | "Teste da baliza (EPIRB): faça o autoteste conforme a etiqueta. O teste não envia alerta." · "Confira na etiqueta a validade da bateria e do disparador hidrostático." |
| `alagamento[1]` | str[] | "Água entrando: ligue as bombas de porão no manual, procure a entrada (válvulas de fundo, mangueiras, eixos) e feche o que puder. Água subindo mesmo assim: MAYDAY no canal 16." |
| `abandono[1]` | str[] | "Abandono: só quando não houver como manter o barco. Antes, MAYDAY no canal 16. Coletes em todos; leve o EPIRB e o VHF portátil; embarque na balsa sem pular na água." |
| `oleo[4]` | str[] | "Reduza para marcha lenta e confira o manômetro agora." · "Compare BB e BE no mesmo giro: só um lado baixo aponta o motor." · "Com o motor parado, procure vazamento e confira o nível de óleo na vareta." · "Se continuar baixa, desligue o motor afetado, siga com o outro e chame a oficina dos motores." (o `OLEO_PASSOS` da 1b; sem marca) |
| `salvatagem` | str | o texto fixo do §2.3 do PROMPT, igual letra por letra |
| `panpan` | str | "Urgência sem perigo imediato de vida (pane, sem governo, alguém ferido sem risco de morte): PAN-PAN, PAN-PAN, PAN-PAN no canal 16, no mesmo formato da chamada MAYDAY." |
| `dsc` | str | "O botão DISTRESS envia o alerta com a identificação programada no rádio: é o MMSI do rádio de bordo (etiqueta / Licença de Estação). Depois do alerta, faça o MAYDAY por voz no canal 16." |

Regras (todas viram asserção):
- Nenhuma string tem ` bar`, `%`, "nós", "mn", 9 dígitos, graus, posição, nome de lugar a bordo, número de pessoas, tempo em minutos, fabricante ou modelo de equipamento gerado. A regex de emergência do PROMPT (Fase 7) roda sobre cada uma.
- **Revisão 2 do C4:** nem dado gerado da embarcação além do nome (trava §2.1 do PROMPT): registro (com qualquer separador ou sem), fabricante, modelo, a marca (palavra do fabricante que está no modelo), `rotulo`, `motorizacao` e o motor dela, `base`, ano, comprimento, boca, calado, deslocamento e tanques, sem distinguir maiúsculas nem acentos. A lista sai do próprio `D` (`confere.barco_sos`); o `verificar.py` usa a mesma em S1/S2 (sem os números, porque a tela mostra o clima real, e sem a `base` até a 1b).
- Nas frases com colete, balsa, boia, extintor, sinalizador, foguete, facho, EPIRB, radiobaliza, Seafire ou kit, nenhuma palavra de lugar do LOCAL_SEGURANCA. Por isso o passo do Seafire diz "acesso ao motor", nunca "compartimento".
- Grafia **"Seafire"** em todo dado (é a do sistema no app desde a 1.0.0).
- Textos curtos: a `FALA_INTEIRA` lê tudo a 1,15×.
- **Indicativo no `canal16`:** no commit da 1b, o `canal16` (e o `SOS_PASSOS`, se citar) escreve o indicativo como `protocolos.indicativo`; sai o `' · indicativo ' + (E.indicativo || SD)` do `capitao-brain.js:282`. O `cerebro.py` confere que a resposta `canal16` não tem "SEM DADOS".

**Contrato de leitura do SOS (S1/S2), conferido na 1b:**
- **pode** ler `D.embarcacao.nome` e `D.protocolos.*`, e os telefones guardados no aparelho;
- **não pode** ler `D.snapshot`, `D.replay`, `D.rota`, `D.campos`, `D.embarcacao.{registro, mmsi, base, modelo, fabricante}`, `D.equipamentos`, `D.guias`, `D.simulacao`, `CapitaoAgora.instante()`, `CapitaoTelemetria` nem `CapitaoReplay`;
- e, como o SOS carrega o cérebro (a S1 direto, `S1-SOS-Web.dc.html:17`; a S2 o injeta, `S2-SOS-Mobile.dc.html:102`) e grava pelo `B.addDiario` (`S1-SOS-Web.dc.html:136`, `S2-SOS-Mobile.dc.html:111`), a trava também vale **dentro** do rodapé e do cérebro:
  - `CapitaoAgora.instante()` devolve `null` quando `/SOS-/.test(location.pathname)`, **antes** de qualquer leitura (nem `D.snapshot.quadro`). A guarda está no `rodape.js` desde o C7;
  - a microtarefa do dia de bordo sai em `/SOS-/` **antes** de ler `D.simulacao` (§4.1, desde o C7). O rebase roda (não lê a flag);
  - o `B.addDiario` não lê `D.simulacao` em `/SOS-/`: a linha do SOS (`src` começando por `web · SOS` ou `app · SOS`) **nunca leva `sim`**. Com `simulacao: false`, o selo "apresentação" e a saída da ficha nunca valem para ela (§1.25). Assim um MAYDAY ou um MOB gravado no aparelho de apresentação continua no registro e na ficha como qualquer linha real;
  - o cérebro lê o `D.snapshot` na carga (`capitao-brain.js:15`, e o `SNAP`, `M`, `G`, `DI` e `T` de `:89-98`). **No commit da 1b** entra a guarda de 1 linha `S = /SOS-/.test(location.pathname) ? {} : (D.snapshot || {})`: em S1/S2, `S` e tudo o que sai dele ficam vazios. Até a 1b, o cérebro carregado pelo SOS ainda lê o snapshot legado, mas as funções que o SOS chama (`addDiario`, `now`, `loadDiario`, `loadEquipe`) não o usam (§6.6);
  - com o instante nulo, o `B.instante()` da Fase 3 também é nulo, o `resumoAgora()` devolve `protocolos.plotter` e o `addDiario()` nunca anexa quadro, `resumo` nem posição do snapshot ou da rota;
  - a posição da linha do SOS é só a do GPS do aparelho ou "posição: ler no plotter" (§2.1 do PROMPT).
- Conferência (1b e `replay.py`): em S1/S2, `CapitaoAgora.instante() === null`; sem permissão de GPS, a linha gravada pelo SOS contém "plotter" e não casa a regex de coordenada do §2.8; com `set_geolocation`, a única coordenada da linha é a do aparelho (o ponto do teste), nunca a do `snapshot.gps` nem a da `rota`; a linha gravada pelo SOS **não tem `sim`**, com `simulacao` `true` e `false`; `D.simulacao` não é lida em `/SOS-/` (teste com um getter que conta as leituras).

### 1.4 `equipamentos[16]` e `equipNota`

Forma: `{id, nome, fabricante, modelo, qtd: number, lados?, guia, palavras[], nominal?, validade?, seguranca?, nota?, fonte}`.

- **O `id` é o sistema.** O campo `sistema` de `agenda`, `tarefasEquipe`, `replay.alertas` e `alarmes[]` do quadro tem o vocabulário fechado `ids de equipamentos ∪ {'casco', 'tanques'}` (`casco` e `tanques` não são equipamento). Quem precisa do equipamento usa `D.equipamentos.find(e => e.id === sistema)`, nunca `D.equipamentos[sistema]` (a lista não é mapa); com `casco` ou `tanques`, não acha nada e a tela omite a linha do fabricante. Asserção `IDS`.

- `palavras`: fabricante, modelo, nome comum e erros prováveis do ditado (F31). Ficam no gerador, para a próxima embarcação não editar o cérebro. Palavra que cabe dentro de outra vai com espaço (`' onan '`).
- `nominal`: números públicos do fabricante, para o cérebro e a ficha citarem com fonte. O do estabilizador é só a regra do guia (`pct_estabiliza`: cerca de 85 %, o ponto de estabilização da folha pública do fabricante; revisão 2 do C5), sem rotação nem minutos do fabricante (§2.5).
- `validade`: id do documento ou da tarefa que guarda o prazo (uma fonte só, rebaseada uma vez).
- `seguranca: true` (EPIRB e Seafire), com `nota` = `NOTA_ETIQUETA` ("modelo, validade e acionamento: veja a etiqueta do equipamento"). É a mesma constante do gerador que vira `protocolos.seafire.nota` e `protocolos.epirb.nota` no C6 (asserção `NOTA_ETIQUETA`), e existe já no C5, antes do `protocolos`.
- Fabricante, modelo e validade desses dois só **podem** aparecer em Equipamentos, Leme e Documentos, que são:
  - B1/B2 (Gestão: inventário de equipamentos);
  - C1/C2 (Manutenção). A C3 é alerta de motor e não mostra equipamento de segurança;
  - G1 web e app (Documentos: `doc-epirb`).
- Em todo o resto, fabricante e modelo trocam por `nota`:
  - a ficha e as respostas `sos`, `epirb` e `seafire` (filtro de uma linha na 1b);
  - F1-FAQ-Hub web e app (`F1-FAQ-Hub-Web.dc.html:186` e `F1-FAQ-Hub.dc.html:166` mostram `fabricante · modelo · qtd` de todo equipamento) e E2 (`E2-Navegando-Sintoma.dc.html:169`), com guarda de 1 linha **no C5**: `e.seguranca ? e.nota : <fabricante · modelo>`. A1/A2 compõem fabricante e modelo só por id de equipamento que não é de segurança (conferir com grep no C5). Na E2 e no `fabMod` do cérebro, o fabricante não se repete quando o modelo já começa por ele, como no `equip_de` do gerador (revisão do C5: "Estabilizador giroscópico Seakeeper 3", nunca "Seakeeper Seakeeper 3" no título, no aria-label, na linha que a E2 grava no diário nem na 1ª linha falada da resposta `estabilizador`). Com 16 cartões, a grade da F1 web rola (revisão do C5): cada cartão tem pelo menos a altura do conteúdo, como na F1 app, e nenhum perde a pergunta, a `Fonte:`, a ação ou a nota;
  - nas F1, a mesma guarda vale **para os links do chat**, que levam o fabricante para a pergunta: `this.chat(e.nome + (e.fabricante ? ' ' + e.fabricante : ''))` (`F1-FAQ-Hub-Web.dc.html:206`, `F1-FAQ-Hub.dc.html:186`) e `this.chat(e.fabricante || e.nome)` (`:210`, `:190`) passam a `this.chat(perguntaEq(e, …))` (revisão do C5; antes, `e.seguranca ? e.nome : …`):
    - equipamento de segurança pede uma frase sem o fabricante **e sem palavra da lista `SOS`**, que cai na chave dele: o EPIRB pede "EPIRB" (rota `epirb`) e o Seafire "sistema fixo de supressão" (rota `seafire`, pelo `supressao` do §2.3 do PROMPT, antecipado na revisão do C5). O `nome` "Sistema fixo de supressão de incêndio" tem "incêndio" e abriria o SOS, como o `t` da agenda (§1.7);
    - nenhuma pergunta de cartão cai numa chave de emergência (`sos`, `oleo`, `canal16`, `epirb`, `seafire`: as que ligam o `emergenciaAte` na Fase 3), fora a do próprio equipamento de segurança. O AIS pede "transponder <fabricante>" (o ` ais ` é a rota `canal16`, o roteiro MAYDAY) e o guincho "como lançar com o guincho <fabricante>" (o ` corrente` é a rota da maré, e o ` ancora ` a resposta pronta `ancora`, com a posição do snapshot e o texto antigo do §3; revisão 2 do C5);
    - **revisão 2 do C5:** fora os de segurança, a pergunta do cartão cai numa resposta cuja fonte é o guia do próprio equipamento (o cartão diz "Fonte: <guia>"). Nome + fabricante não basta no radar e no piloto ("radar" e "piloto" são a resposta pronta `eletronicos`, que não fala deles): o radar pede "como ligar o radar <fabricante>" (`g_radar §1`) e o piloto "como engatar o piloto automático <fabricante>" (`g_piloto §1`). A tabela `PERGUNTA_EQ` da F1 (por id) guarda essas cinco frases; os outros cartões continuam com nome + fabricante. Ficam de fora até a Fase 3 o dessalinizador, o porão e o sistema elétrico, cujas respostas prontas são de antes do C5 (§6.6);
    - teste (revisão do C5): o `verificar.py` passa a pergunta de cada cartão pelo cérebro, com as regras acima, e o `cerebro.py` tem as cinco frases (o guincho, o radar e o piloto com o guia deles no topo do `buscaBase`);
  - e o link direto do VHF e do áudio para a pergunta do FAQ de eletrônicos não se perde: o `kw = norm(e.modelo || e.fabricante || e.nome)` (`F1-FAQ-Hub-Web.dc.html:196`, `F1-FAQ-Hub.dc.html:176`) não casaria os modelos novos, e passa a casar **qualquer uma das `e.palavras`** contra `' ' + norm(título + seções) + ' '` (palavras com espaço nas pontas continuam valendo). Os títulos das perguntas do `D.faq.eletronicos` mantêm "Rádio VHF" e "Áudio Fusion" (§1.6). Teste (C5): na F1 web e app, o cartão do VHF e o do áudio abrem a pergunta certa (índice > 0 no `href`), e nenhum `href` de chat do EPIRB ou do Seafire tem fabricante;
  - os itens SF/EP do FAQ, os trechos e o `equip` da base (§1.5, §1.6) e as tarefas de salvatagem da agenda (§1.7).
- A **validade** desses dois (a data do `doc-epirb` e o `vence` do `seafire-inspecao`) segue a mesma regra: só nas telas acima. Fora delas, a data troca por `nota`, com o filtro de 1 linha da 1b **dentro** do `docsvenc` (e, a partir da Fase 3, de toda resposta que liste a agenda inteira). Como os blocos `## Documentos` e `## Manutenção` da ficha são essas respostas (`capitao-brain.js:598` e `:592`), a ficha fica coberta pelo mesmo filtro (§1.8).
- A F30 nunca envia à IA item nem trecho com `seguranca: true` (não só os EM).
- `fonte`: `Inventário de bordo · Drive › Capitão IA v2 › 01 Manuais e guias de bordo`.
- **`equipNota` fica** até a Fase 4 reescrever F1–F5, com texto neutro: `Inventário de bordo · 16 equipamentos · Drive › Capitão IA v2 › 01 Manuais e guias de bordo`. Sem ela, F2–F5 (web e app) mostrariam "Fonte: lista de equipamentos SEM DADOS".

| id | nome | fabricante | modelo | qtd | lados | guia | nominal / observação |
|---|---|---|---|---|---|---|---|
| `motores` | Motores | Cummins | QSB6.7 305 | 2 | BB e BE | g_motores | `{potencia_cv: 305, rpm_max: 2600, rpm_cruzeiro: 2050, rpm_lenta: 700, transmissao: 'eixo'}` |
| `gerador` | Gerador | Onan | QD 9 | 1 | — | g_gerador | `{kw: 9, hz: 60, rpm: 1800}` |
| `estabilizador` | Estabilizador giroscópico | Seakeeper | Seakeeper 3 | 1 | — | g_seakeeper | `{pct_estabiliza: 85}` (regra do guia: cerca de 85 %, o ponto de estabilização da folha do fabricante, revisão 2 do C5; **sem** rotação de operação nem minutos do fabricante, §2.5) |
| `climatizacao` | Climatização | Webasto | FCF Platinum 16000 e 12000 | 3 | — | g_clima | `{btu_h_total: 40000}` (1 de 16000 no salão, 2 de 12000 nas cabines) |
| `eletronicos` | Plotters | Garmin | GPSMAP 1243xsv | 2 | — | g_eletronicos | posto de comando e hard-top |
| `audio` | Áudio | Fusion | MS-UD755 | 1 | — | g_eletronicos | `{zonas: 2}` |
| `vhf` | Rádios VHF | Icom | IC-M510 e IC-M37 | 2 | — | g_eletronicos | fixo com DSC e portátil |
| `epirb` | EPIRB | Ocean Signal | SafeSea E100G | 1 | — | g_epirb | `validade: 'doc-epirb'`, `seguranca: true` |
| `seafire` | Sistema fixo de supressão de incêndio | Seafire | FD 300M | 1 | — | g_seafire | `validade: 'seafire-inspecao'`, `seguranca: true`; nome sem lugar |
| `dessalinizador` | Dessalinizador | Schenker | Zen 30 | 1 | — | g_dessalinizador | `{lph: 30}` |
| `porao` | Bombas de porão | Rule | Rule 2000 (24 V) | 2 | BB e BE | g_porao | automáticas, com **sensor de nível** (nunca "chave-boia") |
| `ancora` | Guincho e contador de corrente | Lewmar | V2 · contador AA150 | 1 | — | g_ancora | `{corrente_m: 60}` |
| `piloto` | Piloto automático | Raymarine | Evolution EV-1 · ACU-400 | 1 | — | g_piloto | direção hidráulica (bomba conforme o cilindro do leme) |
| `radar` | Radar | Garmin | GMR 24 xHD3 | 1 | — | g_radar | domo de 24" |
| `ais` | AIS (classe B) | em-trak | B954 | 1 | — | g_ais | transponder classe B |
| `eletrico` | Baterias (24 V e 12 V) | Victron Energy | AGM Super Cycle 12 V 230 Ah | 8 | — | g_eletrico | `{bancos: [{id: 'servico', v: 24, n: 4, campo: 'bateria_0_tensao_v'}, {id: 'partida', v: 24, n: 2, campo: 'bateria_1_tensao_v'}, {id: 'eletronica', v: 12, n: 2, campo: 'bateria_2_tensao_v'}]}` (o 16º, que a B2 pede); o banco `eletronica` (12 V, as 2 em paralelo) alimenta também o estabilizador, que é de 12 V DC (§2.5) |

`palavras` (exemplos): motores `['cummins', 'kamins', 'comins', 'qsb', 'motor', 'motores']` · gerador `[' onan ', 'gerador', 'qd 9', 'qd nove']` · estabilizador `['seakeeper', 'sikiper', 'giroscopio', 'estabilizador']` · ais `[' ais ', 'em-trak', 'emtrak', 'transponder']` · vhf `['vhf', 'radio vhf', 'icom', 'canal 16']` · audio `['fusion', 'audio', ' som ', 'bluetooth']` (as duas últimas casam os títulos do FAQ de eletrônicos, para o link direto da F1).

### 1.5 `guias`, `drive.arquivos` e `base-conhecimento.json`

**`D.guias`** (chave → título; formato `Guia de bordo — <Equipamento> <Fabricante>`, sem "(DEMO)"; os de segurança **sem fabricante**):

| chave | título | seções (n · título) | `seguranca: true` |
|---|---|---|---|
| `g_motores` | Guia de bordo — Motores Cummins | 1 Antes da partida · 2 Partida · 3 Aquecimento · 4 Pressão de óleo baixa · 5 Temperatura alta · 6 Parada · 7 Manutenção na agenda · 8 Horímetros · 9 Faixas de operação · 10 Consumo | §4 |
| `g_gerador` | Guia de bordo — Gerador Onan | 1 Antes de ligar · **2 Ligar** (no mesmo lugar: `FONTE_IA` do `chat_ia.py:30/:152`; o texto mantém "PARTIDA" e "gerador", ver abaixo) · 3 Água no escapamento · 4 Desligar · 5 Alarme de alta temperatura · 6 Alarme de baixa pressão de óleo · 7 Manutenção na agenda · 8 Horímetro · 9 Potência e carga | — |
| `g_seakeeper` | Guia de bordo — Estabilizador Seakeeper | 1 Energia · 2 Ligar antes de sair · 3 Estabilizar · 4 Desligar ao atracar · 5 Segurança · 6 Alarmes · 7 Manutenção na agenda · 8 Faixas | — |
| `g_clima` | Guia de bordo — Climatização Webasto | 1 Ligar · 2 Modos e temperatura · 3 Alarme de fluxo · 4 Fluxo de ar fraco · 5 Desligar · 6 Manutenção na agenda | — |
| `g_eletronicos` | Guia de bordo — Eletrônicos Garmin, áudio Fusion e rádios Icom | 1 Plotter: homem ao mar · 2 Piloto automático · 3 Alarme de âncora · 4 Rádio VHF: escuta · 5 Rádio VHF: DSC · 6 Áudio Fusion: Bluetooth · 7 Atualizações · 8 Sonda | §1, §5 |
| `g_eletrico` | Guia de bordo — Sistema elétrico 24 V e 12 V | 1 Bancos · 2 Faixas · 3 Verificação | — |
| `g_dessalinizador` | Guia de bordo — Dessalinizador Schenker | 1 Ligar · 2 Produção · 3 Desligar e lavar · 4 Manutenção | — |
| `g_porao` | Guia de bordo — Bombas de porão Rule | 1 Funcionamento · 2 Faixas · 3 Teste mensal · 4 Água entrando | §4 |
| `g_ancora` | Guia de bordo — Guincho e corrente Lewmar | 1 Lançar · 2 Contador de corrente · 3 Recolher e travar · 4 Manutenção | — |
| `g_piloto` | Guia de bordo — Piloto automático Raymarine | 1 Engatar · 2 Espera ao manobrar · 3 Assumir no timão · 4 Alarmes | — |
| `g_radar` | Guia de bordo — Radar Garmin | 1 Ligar e transmitir · 2 Zona de guarda · 3 Neblina e noite · 4 Segurança | — |
| `g_ais` | Guia de bordo — AIS em-trak | 1 Alvos no plotter · 2 Identificação · 3 Modo silencioso | §2 |
| `g_seafire` | Guia de bordo — Sistema fixo de incêndio | 1 Em caso de fogo · 2 Disparo manual · 3 Depois da descarga · 4 Inspeção anual | todas |
| `g_epirb` | Guia de bordo — EPIRB | 1 Acionar · 2 Teste da baliza · 3 Disparo por engano · 4 Validade | todas |
| `checklist` | Checklist de bordo | Saída · 1 a 3 · Saída · 4 a 6 · Saída · antes de largar · Chegada · Abastecimento · Tanques · Fundeio | "Saída · antes de largar" |
| `protocolo` | Protocolo de emergência — procedimento padrão | MAYDAY · canal 16 · PAN-PAN · DSC · Homem ao mar · Incêndio · Seafire · EPIRB · Água entrando · Abandono · Salvatagem | todas |

São 91 trechos. Cada seção de guia ou do checklist vira também um item do FAQ (82 itens), e as 9 do protocolo viram os cartões EM (§1.6).

**Rótulo nos guias de segurança.** Todo trecho, item do FAQ e página de fonte de `g_seafire`, `g_epirb` e da seção Salvatagem do `protocolo` termina com o rótulo `protocolos.rotulo` (inicial maiúscula) e com "Modelo, validade e acionamento: veja a etiqueta do equipamento." É o "procedimento padrão rotulado" que a Fase 1 do PROMPT pede para `g_seafire` e `g_epirb`.
- O trecho Salvatagem é `protocolos.salvatagem` letra por letra, seguido do rótulo. A resposta `salvatagem` continua só com o texto fixo.
- Os trechos do `protocolo` já levam o rótulo hoje.
- Asserção `ROTULO_SEGURANCA` (§6.3).
- **Inteiro na tela e na voz (revisão 4 do C5):** o `respostaBase` do cérebro mostra o trecho de segurança sem o corte de 480 letras (até 1.500), e a `falaCurta` lê o trecho inteiro, sem a linha "Veja também". Antes, o §1 do Seafire e o protocolo (560 letras) saíam sem o rótulo e sem a nota da etiqueta, o §3 (492) sem a nota, e a voz parava na 2ª frase. A asserção `SEGURANCA_CURTA` (§6.3) limita o trecho com `seguranca` a 800 letras.
- **Fora do índice da busca (revisão 3 do C5):** o rótulo, a nota da etiqueta e o "do equipamento" depois de "etiqueta" ficam no texto do trecho, mas o `carregaBase` do cérebro não os conta (`indexavel`). Repetidos em trechos curtos, punham o `g_epirb §4` no topo de "quais equipamentos tem a bordo?", "equipamentos do barco" e "modelo dos equipamentos", e o trecho de segurança do topo barrava a IA; elas voltam ao `fallback` com a IA, como antes do C5 (teste no `cerebro.py`).
- **O trecho de segurança só entra na busca se a pergunta o nomeia (revisão 4 do C5).** Mesmo sem a repetição, o passo a passo do protocolo (§1 do `g_seafire` e o trecho "Incêndio · Seafire" do protocolo, letra por letra) tem palavras comuns (desligue, gerador, ventilação, depois, esfriar, acesso ao motor) e casava "como desligar a ventilação", "como religar o gerador depois de desligar" e "como abrir o acesso ao motor". O `buscaBase` do cérebro exige, num trecho com `seguranca`, que alguma palavra da pergunta (ou sinônimo) esteja na **identidade** dele: as palavras da `fonte`, do `equip` e do título da seção, menos "guia", "bordo", "protocolo", "emergência", "procedimento", "padrão", "confirmar", "sistema", "depois", "caso" e "antes". "Sistema fixo", "baliza", "disparo manual", "descarga", "inspeção anual" e "DSC" nomeiam; "ventilação", "gerador", "desligar" e "sistema" sozinhos não. Os `SINONIMOS` ganharam `distress` → `dsc` ("botão distress" é o DSC do rádio), `descarregou` → `descarga` ("o sistema descarregou" é o §3) e `trocar` ↔ `troca` ("quando trocar o óleo do motor?" acha a agenda, o `g_motores §7`). Efeito: a pergunta comum volta à resposta pronta, ao guia certo ou à IA (como antes do C5), e só o trecho que a pergunta nomeia barra a IA. O que a pergunta não nomeia e fica sem trecho (balsa, colete, boia…) tem rota própria na 1b (`salvatagem`).
- **Palavras de acionamento: `ident` e `identCom` (revisões 5 e 6 do C5).** A identidade da revisão 4 (fonte, `equip` e título) tirou do trecho do protocolo a pergunta escrita com as palavras do próprio trecho: "pessoa caiu da lancha", "não vejo a pessoa que caiu" (título "Homem ao mar"), "sem governo", "barco sem governo" (título "PAN-PAN"; o texto diz "pane, sem governo, alguém ferido") passavam de resposta local a IA na nuvem (fallback, `pedeIA` true), contra a trava §2.3 do PROMPT. O gerador põe em `ident` as palavras com que a pessoa conta a situação e que o título não diz: `Homem ao mar` (protocolo) → `caiu cair queda vista mar`; `PAN-PAN` (protocolo) → `pane governo ferido urgência`; `1 · Plotter: homem ao mar` (`g_eletronicos`) → `caiu cair queda` (constante `IDENT_ACIONAMENTO`). O `carregaBase` do cérebro guarda as palavras de `ident` à parte da identidade do título (`d._ia`), e o `buscaBase` só deixa o trecho de segurança entrar quando a pergunta o nomeia (`d._id`, pelo título, a fonte e o `equip`) ou traz uma palavra de `ident`; isso não muda a nota do BM25, e o trecho ainda tem de cobrir 60 % das palavras da pergunta e ao menos 2. Por isso "pessoa" (sozinha, "quantas pessoas a bordo?"), "alguém" e verbos de operação ("desligar", "abrir") nunca entram em `ident`: sequestrariam pergunta comum, como o passo a passo do Seafire na revisão 4. "Ferido" fica no `PAN-PAN` até a 1b, que manda ` ferid` para o SOS (aí a pergunta vira `sos`). Continuam fora do trecho local, e ainda vão à IA em toda árvore, "alguém caiu", "estamos sem governo" e "perdi o governo do barco" (só 1 das 2 palavras está no trecho): são da lista `SOS` ampliada da 1b.
  - **`identCom` (revisão 6 do C5).** "Caiu" também é o uso comum para disjuntor, energia e sinal: "o disjuntor caiu, qual o procedimento", "o plotter caiu, como resolver" e "o motor caiu, como resolver" devolviam o protocolo de homem ao mar, com `seguranca`, e barravam a IA (a 2ª palavra que fechava os 60 % era "procedimento", da fonte de todo trecho do protocolo, ou "plotter", do texto). As palavras de quem cai (`caiu cair queda vista mar`) valem então só junto de uma palavra de pessoa na pergunta: `identCom` = `pessoa quem alguém gente homem tripulante criança` (constante `IDENT_PESSOA`) nos dois trechos de homem ao mar; o `PAN-PAN` não tem `identCom`. "Pessoa caiu da lancha", "perdemos de vista quem caiu", "não vejo a pessoa que caiu", "o que fazer se alguém cair" e "pessoa ao mar" seguem locais; "o disjuntor caiu", "a energia caiu", "a temperatura do mar caiu" e "tem vista para o mar?" voltam à resposta pronta ou à IA. A palavra de pessoa só destrava a identidade; a cobertura da busca (2 palavras, 60 %) segue valendo, e "alguém caiu", "tripulante ao mar" e "criança ao mar" continuam com a lista `SOS` da 1b.
  - **Palavras comuns demais para nomear (revisão 6 do C5).** "manual" (título "2 · Disparo manual") e "mar" (título "Homem ao mar") entram nas `IDENT_GENERICAS` do cérebro, junto de "guia", "sistema", "depois"…: "onde fica o manual do motor" e "como acho o manual do motor" devolviam o disparo manual do Seafire (e voltam à resposta pronta `manual`); "tem vista para o mar?" e "a temperatura do mar caiu", o homem ao mar. "disparo" e "homem" continuam nomeando os trechos; "mar" sozinho já não vale, mas "pessoa ao mar" nomeia o protocolo pelo `ident` (`mar`) junto do `identCom` (`pessoa`). "homem ao mar" e "MOB" são `sos` desde antes.
- **Resposta pronta × trecho do guia (revisão 5 do C5).** A resposta pronta de equipamento (a chave está em `GENERICAS`: gerador, motores, áudio, estabilizador, eletrônicos, climatização, dessalinizador, elétrico, porão, âncora, manual) cede ao trecho do topo da busca quando a pergunta é específica ("como", "trocar", "alarme"…; `ESPECIFICA`). Com 91 trechos, "como", "sistema" e "ligar" (sinônimo de "partida") casavam seções sem relação, e o trecho de OUTRO equipamento tomava o lugar da resposta certa: "como ligar o plotter" → o "Ligar e transmitir" do radar ("ligue o radar pelo plotter"); "como ligar o sistema de som" e "…de áudio" → o §1 dos bancos de bateria; "como funciona o sistema elétrico" → o §3 de verificação; "como ligar o carregador" → o §2 do Seakeeper; "como desligar a bomba" → o §5 da climatização; "alarme de temperatura do motor" → o §5 do gerador. O `trechoServe` do cérebro olha os 3 primeiros trechos da busca e usa o primeiro que passa nas três condições (o trecho de segurança que abre a busca, nomeado pela pergunta, passa direto): **(1)** o guia do trecho é um dos do equipamento da resposta (tabela `FAMILIA`: o de eletrônicos inclui piloto, radar e AIS; o de âncora inclui o `g_eletronicos`, porque o alarme de âncora está no plotter, §3; `manual` não tem família); **(2)** se a pergunta diz o nome de algum equipamento (palavra **exata** da fonte ou do `equip` de algum trecho: "plotter" não vale por "garmin"), o trecho é de um equipamento que ela nomeia (fonte, `equip` ou título da seção: o "Piloto automático" do `g_eletronicos` §2 vale); **(3)** a pergunta traz algo além do nome do equipamento e de "funciona": uma palavra, ou sinônimo, que está no título ou no texto do trecho ("como funciona o sistema elétrico" e "como está o sistema elétrico" só dizem o nome). Nenhum dos 3 passa, fica a resposta pronta, como antes do C5 (e, se outro dos 3 é do assunto, vale ele: "alarme de temperatura do motor" vai ao `g_motores` §5 e "seakeeper temperatura alta" ao `g_seakeeper` §6, não ao §5 do gerador). Pergunta sem resposta pronta (`fallback`) não passa por aqui. **"ar":** o filtro de tamanho do `tokens()` tirava toda palavra de até 2 letras, inclusive o "ar" do `SINONIMOS.ar`; "como ligar o ar" virava só "ligar" e achava o radar. Agora o "ar" entra na busca, e "ar condicionado" vale pela palavra "condicionado" (sinônimo de climatização), para não puxar o §4 "Fluxo de ar fraco". **Não volta à resposta pronta:** "como ligar o carregador de bateria" e "…o carregador" ficam no `g_eletrico` §1 · Bancos ("o carregador de bordo repõe os três bancos"): o trecho é do mesmo guia da resposta pronta e cita o carregador, e a IA responde a partir dele; o §2 do Seakeeper, que vinha antes no "…o carregador", sai. A diferença para "como ligar o gerador" é de significado, não de regra.
  - **A rota `porao` e a bateria de partida (revisão 6 do C5).** A rota `porao` do `route()` dava a toda "bomba" a resposta pronta do porão ("Teste de bombas de porão e alarmes… SEM LEITURA"), e o `trechoServe` (tabela `FAMILIA`, condição 1) recusava o guia do outro equipamento: "como trocar o rotor da bomba de água salgada" (g_motores §7), "alarme da bomba de água salgada" (g_clima §3), "como ligar a bomba de água salgada" (g_clima §1) e "como trocar o rotor da bomba do gerador" (g_gerador §7) mostravam a resposta do porão, sem IA; antes do C5, e na revisão 4, iam ao guia certo. Agora "bomba" sozinha segue sendo a de porão ("como desligar a bomba" → `porao`), mas com o nome de outra bomba (`OUTRA_BOMBA`: água salgada, rotor, impeller, circulação, arrefecimento, climatização, gerador, motor, estabilizador, piloto, dessalinizador, óleo, pressão…) a pergunta segue a rota do outro assunto ("a bomba da climatização" → `climatizacao`, "a bomba do gerador" → `gerador`) ou, sem rota, o `fallback` e o guia. Igual para "bateria de partida": a palavra "partida" levava ao `motores` (g_motores), recusando o g_eletrico §1 · Bancos; "bateria" com "partida" e sem "motor" vai ao `eletrico`. A bateria de outro equipamento ("do estabilizador", "do piloto", "da âncora", "do motor") continua com o equipamento que a pergunta nomeia: é a condição 2 da revisão 5, que impede "como ligar o sistema de som" de mostrar os bancos de bateria.
- **Divisão do `g_seafire` (revisões 2 a 4 do C5):** o §1 tem os 5 passos de `protocolos.seafire.passos`, na ordem do protocolo, letra por letra; o §2 é só o disparo manual ("Se o sistema não acionou sozinho e há fogo no motor, use o disparo manual, com motores e gerador desligados e a ventilação do motor cortada."); o §3 diz "Depois do disparo do sistema (disparou ou descarregou, sozinho ou no disparo manual): confirme motores, gerador e ventilação desligados; não abra o acesso ao motor; espere o tempo indicado na etiqueta do sistema e só então libere o acesso, com o extintor portátil à mão; se o fogo voltar, MAYDAY no canal 16. Registre no diário e chame o técnico de bordo para a recarga.", com as palavras do relato. Depois do disparo, o topo da busca é o §3 ou o §1 ("o sistema fixo disparou", "…descarregou", "o que fazer depois do disparo do sistema fixo", "alarme do sistema fixo", "o sistema descarregou"), e os dois levam o "não abra o acesso ao motor" e o desligamento de motores, gerador e ventilação (teste no `cerebro.py`). Os passos do §1.3 não mudam. **Revisão 4 do C5:** as revisões 2 e 3 repetiam o "desligue motores e gerador e corte a ventilação", o "não abra o acesso ao motor" e o "motor esfriar" nas três seções, para qualquer uma delas servir de topo depois do disparo. Como o trecho é de segurança (e barra a IA), isso sequestrava perguntas comuns: "como religar o gerador depois de desligar", "como abrir o motor", "como desligar a ventilação", "como esfriar o motor depois de navegar". O §2 perdeu o "disparou" ("não acionou sozinho"), o "depois" e o passo seguinte; o §3 perdeu o "motor esfriar" e o "ao abrir" (agora "só então libere o acesso"); o resto fica com a identidade do trecho (abaixo). O `g_motores §6` passou a "Depois de navegar, deixe de 2 a 3 minutos em marcha lenta antes de desligar, para o motor esfriar por igual.", que tem 3 das 4 palavras de "como esfriar o motor depois de navegar".

**`g_gerador §2 · Ligar` não pode perder o 1º lugar** (seria quebra fora da tabela da Fase 7):
- o texto mantém "PARTIDA" e a palavra "gerador", e a fonte mantém "Gerador";
- com 91 trechos, as seções novas de ligar e de partida (`g_motores §2`, `g_clima §1`, `g_dessalinizador §1`, `g_radar §1`) entram no mesmo BM25, que indexa também `fonte` e `equip` (`capitao-brain.js:470`);
- o C5 confere que, para "como ligar o gerador?", o 1º trecho de `buscaBase` é o `g_gerador §2`, e que as 5 asserções do `chat_ia.py` que dependem dele continuam verdes: `:211` ("Gerador" na fonte do 1º trecho) e `:229`, `:234`, `:236`, `:385` ("PARTIDA" no texto local). Se outro trecho passar à frente, muda o texto do guia novo, nunca o teste.

**Textos com número** (saem da constante `LIMITES` do gerador, formatada em pt-BR; teste: o §n citado em cada `limites[c].fonte` contém os números):
- `g_motores §9 · Faixas de operação`: "Faixas de operação (motor aquecido). Rotação: marcha lenta 650 a 750 rpm; cruzeiro 2.050 rpm (18 nós); até 2.600 rpm. Pressão de óleo: abaixo de 1.000 rpm, normal de 1,0 a 6,0 bar; a partir de 1.000 rpm, normal de 2,4 a 6,0 bar. Aviso abaixo do normal ou acima de 6,0 bar. Crítico abaixo de 0,6 bar (abaixo de 1.000 rpm) ou de 1,4 bar (a partir de 1.000 rpm). Líquido de arrefecimento: normal até 88 °C (em cruzeiro, 80 a 85 °C); aviso acima de 88 °C; crítico acima de 97 °C. Carga: aviso acima de 90 %. Praça de máquinas: aviso acima de 60 °C."
- `g_motores §10 · Consumo`: "Consumo dos dois motores: cerca de 6,2 L/h em marcha lenta (700 rpm, 5 nós), 68 L/h em cruzeiro (2.050 rpm, 18 nós) e 111 L/h na rotação máxima."
- `g_motores §7`: "Troca de óleo e filtros: 12 meses ou 450 h (o que vier antes). Rotor da bomba de água salgada: a cada 12 meses. Revisão anual pela oficina de motores." · `§4`: os passos de `protocolos.oleo`.
- `g_gerador §9 · Potência e carga`: "Potência nominal 9 kW (60 Hz, 1.800 rpm). Carga: normal até 8,1 kW; aviso acima de 8,1 kW (90 % da nominal). Com a climatização ligada, o normal é 5,5 a 6,5 kW." · `§7`: "Óleo e filtros: 12 meses ou 1.300 h (o que vier antes). Rotor (impeller): inspeção a cada 12 meses." · `§8`: "O horímetro aparece no painel do gerador e na telemetria." (sem número)
- `g_seakeeper §1 · Energia` (sem número; revisão 3 do C4: o Seakeeper 3 é só 12 V DC, §2.5, e o texto é o do gerador desde então): "O estabilizador é alimentado pelo banco de 12 V. Para acelerar o volante, mantenha o banco carregado, com o carregador ligado ao gerador ou ao cais. Com tensão baixa no 12 V, o display avisa e o volante não acelera."
- `g_seakeeper §2`: "Ligue pelo display com antecedência, com o banco de 12 V carregado (carregador ligado ao gerador ou ao cais). O volante estabiliza a partir de cerca de 85 % da rotação de operação; o display mostra a rotação e indica quando a estabilização está disponível. Espere a indicação antes de sair." (**sem** rotação nem minutos do fabricante: os minutos repetiriam números do contexto do estabilizador na pasta do Avanti, conferido por contagem, §2.5) · `§8`: "Volante: estabiliza a partir de cerca de 85 % da rotação de operação; aviso abaixo de 85 % (sem estabilização)." (Revisão 2 do C5: era 60 %, abaixo do ponto de estabilização da folha pública do Seakeeper 3, §2.5.)
- `g_seakeeper §6 · Alarmes` (**mensagens do display, sem código numérico**; desvio para o ok, §8): "Mensagens do display e o que fazer: tensão baixa no 12 V (ligue o carregador ao gerador ou ao cais); arrefecimento do estabilizador (confira a bomba e a válvula de fundo); temperatura alta (desligue e chame o técnico); volante abaixo de 85 % (sem estabilização até o volante acelerar). O display mostra a mensagem e o código: anote no diário com a hora." (Revisão 3 do C4: o §2 dizia "com energia AC" e o §6 "falta de energia AC (ligue o gerador ou a tomada do cais)"; o Seakeeper 3 não usa energia AC, §2.5.)
- `g_eletrico §2`: "Bancos de 24 V (serviço e partida): normal de 24,4 a 29,4 V; aviso abaixo de 24,4 V ou acima de 29,4 V; crítico abaixo de 23,6 V. Banco de 12 V: normal de 12,2 a 14,7 V; aviso abaixo de 12,2 V ou acima de 14,7 V; crítico abaixo de 11,8 V."
- `g_porao §2`: "Nível normal no poço das bombas: até 5 cm; aviso acima de 5 cm; crítico acima de 10 cm. As bombas ligam sozinhas pelo sensor de nível." · `§4`: o texto de `protocolos.alagamento`.
- `g_eletronicos §8 · Sonda`: "Profundidade mínima de navegação: 3,0 m na sonda (aviso abaixo de 3,0 m; crítico abaixo de 2,0 m)." (sem a palavra "calado")
- `g_eletronicos §5 · DSC` = `protocolos.dsc`. `g_ais §2`: "O AIS transmite a identificação programada no transponder; o MMSI é o do rádio de bordo (etiqueta / Licença de Estação)." Nunca o número.
- `g_eletronicos §3`: "Ao fundear, ative o alarme de âncora no plotter e defina o raio conforme a corrente lançada. O contador de corrente mostra os metros lançados no controle do guincho."
- `g_dessalinizador §2`: "Produção nominal: 30 L/h. Descarte a água dos primeiros minutos depois de ligar." · `g_ancora §1`: "Lance de 3 a 5 vezes a profundidade."
- `checklist · Abastecimento`: "Diesel: abastecer antes de 25 % do total dos tanques (400 L de 1.600 L); reserva técnica de 10 % (160 L)." (revisão 2 do C5: dizia "25 % (400 L) em qualquer tanque", mas 25 % de um tanque de 800 L são 200 L, e o `diesel_litros` do §3.3 avalia o total) · `checklist · Tanques`: "Tanques: água doce, aviso abaixo de 15 %; águas cinzas e negras, aviso acima de 80 %. Na marina, antes da saída: água completada e servidas esvaziadas."
- `checklist · Saída · 1 a 3` (sem número de limite; revisão 3 do C4): o item 2 é "Estabilizador: ligue com antecedência, com o banco de 12 V carregado." (antes, "precisa de AC").
- `checklist · Saída · antes de largar`: "Coletes: um por pessoa — conte as pessoas a bordo agora; balsa, boia e extintores conforme a placa de salvatagem. Previsão do dia consultada (vento e mar) — confira o boletim da Marinha antes de sair." (sai o "Amarração e fechamento: A CONFIRMAR").

**Proibido no texto dos guias:** "SEM DADOS", "MANUAL NO DRIVE", "A CONFIRMAR", "indisponível", "de demonstração", "fictício", "a definir"; números do snapshot; **"calado" até a Fase 3**; código numérico de alarme de modelo real; capacidade de óleo, torque ou especificação de fluido ("até a marca da vareta", "conforme a etiqueta"); "Seakeeper" seguido de outro número que não o do modelo escolhido (a conferência de modelos é por substring); energia AC ("AC", "CA", corrente ou energia alternada) em texto do estabilizador, que é de 12 V DC (revisão 3 do C4, asserção `ESTABILIZADOR_12V`, §6.3). A climatização e o gerador continuam com a energia AC deles.

**`base-conhecimento.json`** = `{versao: '<8 hex do hash do conteúdo>', aviso, trechos[]}`.
- Trecho: `{fonte, secao, texto, equip, seguranca?, ident?, identCom?}`. O `pag: null` sai. `ident` (revisão 5 do C5, abaixo) é string de palavras e só existe em trecho com `seguranca`; `identCom` (revisão 6 do C5) é a string de palavras de pessoa que destravam o `ident`, e só existe junto dele; a IA não recebe nenhum dos dois (o `capitao-ia.js` manda `fonte`, `pag`, `secao` e `texto`).
- `equip` = `<nome> <fabricante> <modelo>` (ex.: `Gerador Onan QD 9`), menos nos de segurança: `Sistema fixo de supressão de incêndio` e `EPIRB`.
- `aviso`: "Trechos dos guias de bordo da embarcação Capitão IA (Drive › Capitão IA v2). Sem documentos pessoais, fiscais ou contratuais."
- **Invariante `SEGURANCA_MARCADA`:** o gerador marca `seguranca: true` em todo trecho **e** todo item do FAQ (CK-xx inclusive) cujo texto, passado pelo `pad()` portado, casa uma palavra da constante única `SEGURANCA_PALAVRAS`, montada com as mesmas listas do cérebro (portadas para Python como na `SEM_EMERGENCIA`):
  1. a lista `SOS` ampliada da 1b: a de hoje (`capitao-brain.js:123-125`) mais as do §2.3 do PROMPT (`alagament`, `afogament`, `inundac`, `adernand`, `adernad`, `adernou`, `emborc`, ` ferid`, `machuc`, `se feriu`, `sangra`, `desmai`, `inconscien`, `infart`, `convuls`, `queimadura`, `choque eletric`, `agua no porao`, `porao cheio`, `porao enchendo`, `bomba de porao nao para`, `barco virou`, `virou o barco`, ` a deriva `, `monoxido`, `alarme de gas`), e `fumaca` sem `escap`, como no `emergencia()`;
  2. as palavras da rota `salvatagem` (§2.3 do PROMPT): `colete`, `salva-vida`, `salva vida`, `balsa`, `bote salva`, `boia circular`, `boia salva`, ` boia ` (com as mesmas exclusões: amarra, poita, canal, baliza, cardinal, luz), `sinalizador`, `foguete`, `pirotecn`, `facho`, `salvatagem`, `equipamento de seguranca`, `equipamentos de seguranca`, `kit de seguranca`, `sobreviv`, ` plb `, ` sart `, e `extintor` (aqui com ou sem fogo);
  3. `epirb`, `radiobaliza`, `baliza`, `seafire`, `supressao`, `mayday`, `distress`, ` dsc `, `pan-pan`, `pan pan`, `homem ao mar`.
  - A coluna `seguranca: true` da tabela acima é o mínimo: a marcação pode pegar mais seções, nunca menos. Ex.: o CK-05 (com "extintor portátil à mão") fica com `seguranca: true` e não vai à IA (F30 e `pedeIA`).
  - A partir da 1b, o `cerebro.py` extrai do `capitao-brain.js` as listas `SOS` e a da `salvatagem` e confere que são iguais às do gerador (uma fonte de verdade por lista, sem cópia que divirja).
  - Se a marcação pegar um trecho que o `cerebro.py` exige com PEDE_IA True (ex.: "como ligar o gerador?" → `g_gerador §2`), muda o texto do trecho, nunca a lista.

**`drive.arquivos`** (a chave fica; o valor perde "(DEMO)" e "snapshot"):
`leiame: 'LEIA-ME — Capitão IA v2'` · os 16 títulos acima · `inventario: 'Inventário de bordo'` · `documentos: 'Controle de documentos'` · `agenda: 'Agenda preditiva'` · `diario: 'Diário de bordo'` · `abast: 'Registro de abastecimento'` · `snapshot: 'Leitura do coletor NMEA — 26-09-2026 10h12.json'` (até a Fase 3) · `serie: 'Série do coletor NMEA — 150 s.csv'` · `formato: 'Formato do quadro do coletor.csv'`.

### 1.6 FAQ: `D.faq` (L, F2–F5) e `faq-equipamentos.json` (F10)

**`D.faq` (L até a Fase 4):** forma de hoje (`gerador`, `estabilizador`, `eletronicos`, `climatizacao` → `{status: 'PRONTO', fonte, equip, modelo, perguntas[{q, passos[{n, t, secao}]}]}`), com `modelo` preenchido (`QD 9`, `Seakeeper 3`, `GPSMAP 1243xsv · MS-UD755 · IC-M510`, `FCF Platinum`) e `equip` sem "(modelo SEM DADOS)". Os passos saem das mesmas seções dos guias. Os títulos das perguntas do `D.faq.eletronicos` mantêm "Rádio VHF" (canal 16 e DSC) e "Áudio Fusion" (Bluetooth): é por eles que a F1 abre a pergunta certa (§1.4).

**`faq-equipamentos.json`** (arquivo próprio na raiz, gerado no C11):
- **CORE desde a Fase 3.** A F10 responde pelo FAQ já na Fase 3 (PARIDADE: fases 1 + 3 + 4). Por isso o arquivo entra no `CORE` do `sw.js`, na lista do `index.html` e na conferência offline **no mesmo commit da Fase 3 em que o cérebro faz o 1º `fetch` dele**, e não com a F6. Se o `fetch` falhar, o cérebro segue com o BM25 da base. A F6 (Fase 4) usa o arquivo já guardado;
- topo: `{versao: '<hash>', total, secoes: [{n, titulo, ids[]}], itens[], glossario: [{termo, texto, fonte}]}`. Sem `conf`, `edicao`, `origem`, `selos`, `decisoes` nem `limites`;
- item: `{id, titulo, pergunta, variantes[3], resposta, passos[], acao?, atencao?, senao?, obs?, fontes: [{tipo, texto}], secao, equip, emerg, seguranca?, ver[]?}`. Sem `conf` e sem `lacuna`;
- `id` = prefixo do guia + número da seção: MO-01…10, GE-01…09, SK-01…08, CL-01…06, EL-01…08, EE-01…03, DS-01…04, PO-01…04, AN-01…04, PI-01…04, RA-01…04, AI-01…03, SF-01…04, EP-01…04, CK-01…07;
- cartões **EM-01…EM-09** (MAYDAY, PAN-PAN, DSC, homem ao mar, incêndio, água entrando, abandono, EPIRB, salvatagem): textos de `D.protocolos`, rótulo do procedimento padrão, `MMSI_RADIO`, `emerg: true`, `seguranca: true`; sem posição, pessoas nem lugar;
- itens **SF-xx e EP-xx**: `equip` = `Sistema fixo de supressão de incêndio` / `EPIRB`, sem fabricante nem modelo; `seguranca: true`; resposta com o rótulo do §1.5 no fim;
- **nada com `seguranca: true` vai à IA** (F30): EM, SF, EP, CK-03 e todo item que a `SEGURANCA_MARCADA` marcar (CK-05 inclusive), não só os EM;
- `fontes[].tipo` ∈ {`Guia de bordo`, `Protocolo`, `Boa prática`}; nunca "Manual" nem "Foto";
- omitidos: `lacuna`, `lacunas`, `divergencias`, `invalidos` e todo campo vazio. `total` sai da contagem;
- glossário: SOG, STW, COG, HDG, TWS, TWA, AWA, DPT, ETA, MOB, DSC, MMSI (texto `MMSI_RADIO`), EPIRB, BB/BE.

**Port do módulo de FAQ, da F6 (Fase 4) e da leitura do FAQ no cérebro (Fase 3).** O módulo do Avanti lê a confiabilidade por item (`it.conf`, num vocabulário próprio de 3 níveis, com um texto padrão que manda confirmar a bordo), os anexos de lacunas, divergências e decisões, alertas e inválidos, e tem total e edição padrão fixos no código. No port:
- **sai o chip de confiabilidade**: todo item vem do guia de bordo gerado, um nível só não informa nada, e o texto padrão seria rótulo novo em dado de bordo (decisão 3; pede ok, §8.2). O cérebro também não lê `conf`;
- saem os anexos de lacunas, divergências e decisões, alertas e inválidos. Fica só o glossário. O catálogo de alertas é o `D.replay.alertas`, mostrado na C3;
- `total` = `itens.length` do arquivo, sem padrão fixo (carregando = nada);
- a edição mostrada é `CapitaoDados.versao` (com rebase), não um campo do arquivo.

### 1.7 `agenda[14]` e `tarefasEquipe[2]`

Forma gerada: `{id, t, curto, equip, sistema, quem, intervalo, meses, ultimaHa, venceEm, horas?: {limite, campos[], atual, faltam}, seguranca?, palavras[], fonte}`. O rebase escreve **(R)** `ultima`, `vence` ('dd/mm/aaaa'), `dn`, `st`, `rot`, `tom`, e ordena por `dn` (estável, depois por `id`).

- `sistema` ∈ o vocabulário do §1.4 (ids de equipamentos ∪ {`casco`, `tanques`}).
- `intervalo` é o texto de hoje (`mensal`, `6 meses`, `12 meses`, `12 meses ou 450 h (o que vier antes)`, `12 meses ou 1.300 h`), e `meses` dá os dias pela constante `DIAS_MESES = {1: 31, 6: 184, 12: 365}`.
- `palavras` são frases normalizadas (minúsculas, sem acento, como o `norm()` do cérebro) que ligam um texto à tarefa: o cérebro as usa para achar a tarefa no chat, e a F20 para fechar a pendência que cita a tarefa (§1.9). Nenhuma é palavra solta genérica ("motor", "filtro"): cada uma identifica a tarefa sozinha.
- Nenhum `t` tem palavra da lista `SOS` ampliada (asserção `AGENDA`): um link ou uma pergunta feita com o texto da tarefa nunca abre o SOS. Por isso o Seafire é "sistema fixo de supressão" no `t`, e "incêndio" fica só no `equip`.

- Os 11 ids de hoje ficam (telas e `capitao.executado.v1` usam o id). Entram `epirb-teste`, `motores-rotor` e `seafire-inspecao`.
- `AGENDA_FALTA` e `D.agendaFalta` saem no C7, com uma guarda de 1 linha em cada um dos 4 leitores (grep de `agendaFalta` na árvore):
  - `capitao-brain.js:270`: `(D.agendaFalta && D.agendaFalta.length ? '\nFalta registrar: ' + D.agendaFalta.join(' · ') + '.' : '')`, para não sair "Falta registrar: .";
  - `B1-Carta-Web.dc.html:320` (`manutSub`): o trecho " · falta registrar: … (SEM DADOS)" só entra com a lista cheia, para não sair "falta registrar: nada (SEM DADOS)";
  - `C1-Leme-Web.dc.html:213` e `C2-Leme-Mobile.dc.html:136`: `temFalta: !!(D.agendaFalta || []).length`, e o `<span>` FALTA REGISTRAR (C1:111, C2:67) vai dentro de `<sc-if value="{{temFalta}}">`, para não sair "FALTA REGISTRAR · nada".
- `equip` sem "(fabricante SEM DADOS)" (ex.: `Gerador Onan QD 9`). Nas tarefas de salvatagem, `equip` sem fabricante nem modelo (`EPIRB`, `Sistema fixo de supressão de incêndio`), porque a agenda vai também à resposta `manutencao` e à ficha (§1.4). `quem` = papel (`marina`, `técnico`, `oficina de motores`, `Lucas`), nunca nome de terceiro.
- `seguranca: true` em `epirb-teste`, `seafire-inspecao` e `porao-teste` (o teste das bombas já é Segurança no diário, d07; pede ok, §8.2). É o conjunto do item s12 do checklist (§1.18): com o `porao-teste` atrasado, o s12 fica pendente, como a d01 diz.
- `horas.atual`/`horas.faltam` gerados = valores na âncora (reserva). Na simulação, o tique do replay os reescreve a partir de `CapitaoAgora.instante().calc.faltam` (um cálculo só, duas exposições), e as 10 telas que leem `t.horas.faltam` não mudam.

| id | t | curto | equip | sistema | quem | intervalo · meses | venceEm | ultimaHa | horas | palavras |
|---|---|---|---|---|---|---|---|---|---|---|
| porao-teste | Teste das bombas de porão e alarmes | TESTE | Bombas de porão Rule 2000 | porao | técnico | mensal · 1 | −25 | 56 | — | `bombas de porao`, `bomba de porao`, `teste das bombas` |
| clima-filtro | Limpeza do filtro de água salgada da climatização | FILTRO | Climatização Webasto FCF Platinum | climatizacao | marina | mensal · 1 | −16 | 47 | — | `filtro de agua salgada`, `filtro da climatizacao`, `filtro do ar condicionado`, `filtro do ar-condicionado` |
| gerador-rotor | Inspeção do rotor (impeller) do gerador | ROTOR | Gerador Onan QD 9 | gerador | técnico | 12 meses · 12 | −2 | 367 | — | `rotor do gerador`, `impeller do gerador`, `rotor impeller do gerador` |
| casco-anodos | Limpeza de casco e troca de anodos | ANODOS | Casco | casco | marina | 6 meses · 6 | +9 | **175** | — | `limpeza de casco`, `limpeza do casco`, `anodos do casco`, `troca de anodos` |
| epirb-teste | Autoteste do EPIRB e validade conferida na etiqueta | AUTOTESTE | EPIRB | epirb | Lucas | mensal · 1 | **+13** | 18 | — | `autoteste do epirb`, `teste do epirb`, `teste da baliza`, `autoteste da baliza` |
| motores-oleo | Troca de óleo e filtros dos motores | ÓLEO | Motores Cummins QSB6.7 305 | motores | oficina de motores | 12 meses ou 450 h (o que vier antes) · 12 | +17 | 348 | `{limite: 450, campos: ['motor_bb_horimetro_h', 'motor_be_horimetro_h']}` (vale o maior) | `oleo dos motores`, `oleo do motor`, `filtros dos motores` |
| gerador-revisao | Revisão do gerador: óleo e filtros | REVISÃO | Gerador Onan QD 9 | gerador | técnico | 12 meses ou 1.300 h · 12 | +24 | 341 | `{limite: 1300, campos: ['gerador_horimetro_h']}` | `revisao do gerador`, `oleo do gerador`, `filtros do gerador` |
| seakeeper-anodo | Anodo do trocador de calor do estabilizador | ANODO | Estabilizador Seakeeper 3 | estabilizador | técnico | 6 meses · 6 | +35 | 149 | — | `anodo do estabilizador`, `anodo do seakeeper`, `anodo do trocador` |
| motores-rotor | Troca do rotor da bomba de água salgada dos motores | ROTOR | Motores Cummins QSB6.7 305 | motores | oficina de motores | 12 meses · 12 | +41 | 324 | — (conversa com o AVISO do BE e a F11) | `rotor da bomba de agua salgada`, `rotor dos motores`, `impeller dos motores`, `rotor do motor` |
| baterias | Verificação do banco de baterias e conexões | VERIFICAÇÃO | Baterias Victron Energy (24 V e 12 V) | eletrico | técnico | 6 meses · 6 | +50 | 134 | — | `banco de baterias`, `conexoes das baterias`, `verificacao das baterias` |
| garmin-cartas | Atualização de cartas e software dos eletrônicos | CARTAS | Plotters Garmin GPSMAP 1243xsv | eletronicos | Lucas | 12 meses · 12 | +66 | 299 | — | `cartas do plotter`, `cartas nauticas`, `atualizacao das cartas`, `software dos eletronicos` |
| clima-revisao | Revisão anual da climatização | REVISÃO | Climatização Webasto FCF Platinum | climatizacao | marina | 12 meses · 12 | +86 | 279 | — | `revisao da climatizacao`, `revisao do ar condicionado` |
| motores-revisao | Revisão anual dos motores | REVISÃO | Motores Cummins QSB6.7 305 | motores | oficina de motores | 12 meses · 12 | +112 | 253 | — | `revisao dos motores`, `revisao anual dos motores` |
| seafire-inspecao | Inspeção anual do sistema fixo de supressão | INSPEÇÃO | Sistema fixo de supressão de incêndio | seafire | técnico | 12 meses · 12 | +140 | 225 | — | `inspecao do sistema fixo`, `sistema fixo de supressao`, `inspecao do seafire` |

- Os `t` das 11 tarefas de hoje ficam iguais (só o `equip` e o `quem` mudam); os 3 novos estão na tabela. `fonte` = `agendaFonte` (§1.1).
- `ultimaHa + venceEm` = `DIAS_MESES[meses]`, conferido nas 14 pela asserção `AGENDA`. Nesta revisão: `casco-anodos` 175 + 9 = 184 (era 174, que dava 183) e `epirb-teste` 18 + 13 = 31 (era +12, que dava 30; o `ultimaHa` 18 continua igual ao `diasAtras` da d06). A ordem por `dn` não muda: `epirb-teste` (+13) continua antes de `motores-oleo` (+17), e as 3 atrasadas são as mesmas.
- **3 atrasadas**, como hoje. Folga das horas: 37,4 h (óleo) e 63,6 h (gerador) na âncora; 13,4 h e 39,6 h às 06:59:59. Fica > 0 o dia todo e ≥ 24 h na âncora (asserção).
- **Nenhuma tarefa de salvatagem atrasada** (asserção: `epirb-*` e `seafire-*` com `venceEm > 0`).
- `tarefasEquipe` (F15): `{id, n, venceEm, quem, meses, sistema, origem: 'equipe'}` com `g01` "Revisar mangueiras do dessalinizador" (+20, `técnico`, 6, `dessalinizador`) e `g02` "Lavar o convés e o hard-top" (+5, `marina`, 1, `casco`). O rebase escreve `vence` ('AAAA-MM-DD', a forma do `capitao.tarefas.v1`), `dn`, `st`, `rot`, `tom`.

### 1.8 `documentos[7]` e a nota fiscal do dia de bordo

Forma gerada: `{id, n, cat, venceEm?, emitidoHa?, numero?, ref?, st?, nota, fonte}`. O rebase escreve **(R)** `vence`, `dn`, `st` e `emitido`. `st` sem validade só para a nota fiscal.

| id | n | cat | venceEm | emitidoHa | numero | nota |
|---|---|---|---|---|---|---|
| tie | Título de Inscrição da Embarcação (TIE) | Registro | +646 | 1180 | `CIA-23-0417` (= `embarcacao.registro`) | renovação a cada 5 anos |
| seguro | Seguro da embarcação | Seguro | +19 | 346 | — | apólice guardada a bordo e no Drive |
| licenca | Licença de Estação de rádio (VHF) | Licenças | +65 | — | — | rádios VHF fixo e portátil |
| laudo | Laudo de vistoria anual | Laudos | +326 | 39 | — | laudo arquivado no Drive |
| gar-estab | Garantia do estabilizador | Garantias | +175 | — | — | Seakeeper 3 |
| gar-eletr | Garantia dos eletrônicos | Garantias | +137 | — | — | plotters e radar Garmin |
| doc-epirb | Certificado do EPIRB (bateria e disparador hidrostático) | Segurança | +540 | — | — | validade conferida também na etiqueta do equipamento |

**Nota fiscal do dia de bordo** (só simulação): fica em `D.replay.diaDeBordo.documento` e **não** em `documentos` do arquivo gerado. A microtarefa a insere em `documentos` por id (`splice`, sem duplicar), junto com `ab-0`, d01 e d02 (§4.1): `{id: 'nf-abast', n: 'Nota fiscal do abastecimento', cat: 'Notas', emitidoHa: 0, st: 'CONFERIDA', ref: 'ab-0', nota: 'abastecimento das 07:00 · sem valores no app', fonte: docsFonte}`, com `emitido` na base **dia de bordo**. Assim o `ref` só existe quando o `ab-0` existe: com `simulacao: false` (ou sem o rodapé), nenhum documento aponta para um abastecimento que não existe nem fala do "abastecimento das 07:00", e o `SIMULACAO = False` do gerador não a emite (§4.3).

- **Só o TIE tem número.** Apólice, licença, laudo e nota fiscal não ganham número nem emissor.
- Asserção `IDS`: o `ref` da nota fiscal e o da d02 ∈ `ab-0…ab-(diaDeBordo.dias − 1)`, os ids que a microtarefa vai criar (derivados de `replay.diaDeBordo.dias`); os `ref` do diário fixo existem na agenda ou nos documentos do arquivo gerado.
- `st` ∈ {`EM DIA`, `VENCE EM N D` (≤ 90), `VENCIDO`, `CONFERIDA`}. Nenhum `SEM DADOS` nem `A CONFERIR`.
- TIE emitido há 1.180 dias (2023, o ano do barco) e válido por 5 anos: coerente com `ano`.
- Sem `venceEm`, o rebase **omite** `vence`, `dn` e o `st` de prazo: a nota fiscal fica com o `st: 'CONFERIDA'` gerado e o `emitido` do dia de bordo (§1.0).
- `doc-epirb` (e o `vence` do `seafire-inspecao`, §1.7): a data aparece só em G1 (Documentos) e, para a tarefa, em C1/C2. O filtro de 1 linha da 1b fica **dentro** do `docsvenc` (`capitao-brain.js:312-316`): o documento ligado a um equipamento com `seguranca` (`equipamentos.some(e => e.seguranca && e.validade === d.id)`) sai como `d.n + ' — ' + protocolos.epirb.nota`, sem a data. Como o bloco `## Documentos` da ficha **é** o `docsvenc` (`capitao-brain.js:598`), a ficha fica coberta pelo mesmo filtro, que entra junto com o de `## Equipamentos` (§1.4). `cerebro.py` (1b): a ficha e a resposta `docsvenc` sem a data (dd/mm/aaaa) do `doc-epirb`; G1 com a data (`verificar.py`). O `manutencao` de hoje lista só as 3 próximas e nunca chega ao `seafire-inspecao` (+140); a Fase 3 leva o mesmo filtro a toda resposta que liste a agenda inteira.

### 1.9 `diario[7]` (fixo) e o dia de bordo (só simulação)

Forma gerada: `{id, diasAtras, h, sys, tom, who, pend, t, ref?, palavras?}`. O rebase escreve **(R)** `d` ('dd/mm') e `iso` (com o deslocamento do fuso): na base **hoje** para o diário fixo (d03–d09) e na base **dia de bordo** para d01 e d02 (§1.0).

| id | diasAtras | h | sys | tom | who | pend | ref | t |
|---|---|---|---|---|---|---|---|---|
| d03 | 2 | 17:10 | Manutenção | warn | técnico | sim | gerador-rotor | "Inspeção do rotor do gerador não feita no prazo — reagendar; rotor de reserva em falta no estoque." |
| d04 | 3 | 19:30 | Motores | accent | Lucas | não | motores-rotor | "Motor BE 1 a 2 °C acima do BB em cruzeiro nos últimos dias, com picos acima de 88 °C — acompanhar; rotor da bomba de água salgada dos motores na agenda." |
| d05 | 6 | 11:05 | Equipamentos | accent | Lucas | sim | clima-filtro | "Climatização da cabine de proa com fluxo fraco. Suspeita: filtro de água salgada sujo (limpeza atrasada)." |
| d06 | 18 | 08:30 | Segurança | ok | Lucas | não | epirb-teste | "Autoteste do EPIRB feito: luz de teste conforme a etiqueta." |
| d07 | 21 | 10:00 | Segurança | crit | técnico | sim | porao-teste | "Teste das bombas de porão adiado por chuva." |
| d08 | 29 | 16:25 | Eletrônicos | accent | Lucas | não | garmin-cartas | "Cartas do plotter desatualizadas; a atualização está na agenda." |
| d09 | 39 | 09:00 | Documentos | ok | Lucas | não | laudo | "Vistoria anual feita; laudo arquivado no Drive." |

**Dia de bordo** (`D.replay.diaDeBordo`; inserido pela microtarefa do rodapé **só com `D.simulacao === true`**, §4.1):
- `d01` · 0 · 07:00 · Navegação · tele · Lucas: "Saída da Barra Sul às 07:00 com 4 pessoas a bordo: passeio Barra Sul ⇄ Estaleirinho pela Interpraias. Checklist de saída feito; o teste das bombas de porão continua pendente."
- `d02` · 0 · 07:00 · Combustível · ok · Lucas · `ref: 'ab-0'`: "Abastecimento de 1.086 L de diesel no posto da marina da base para a saída das 07:00, com água completada e servidas esvaziadas; tanques de diesel em 97,5 %."
- d01 e d02 têm o mesmo `h` (07:00 = `ancora_hora`). O rebase escreve o `iso` com segundos: d02 = âncora (07:00:00) e d01 = âncora + 1 s. A microtarefa põe a d01 antes da d02 no topo, e quem ordena por `iso` (o mais novo no topo) chega à mesma ordem: a saída fica acima do abastecimento.

**Pendências e F20** (Resolver / Reabrir; registro que cita a pendência a fecha, com Desfazer):
- toda linha `pend: true` leva `palavras` = `agenda[ref].palavras` (o gerador copia; uma fonte só, §1.7): d03 → `gerador-rotor`, d05 → `clima-filtro`, d07 → `porao-teste`. É por elas que um registro novo cita a pendência. O verbo de conclusão e a recusa de futuro, dúvida e defeito são do cérebro (Fase 3); um texto que casa duas pendências abertas não fecha nenhuma (a resposta pergunta qual);
- o estado vem das linhas de ação do aparelho (`acao: 'resolve' | 'reabre'`, `alvo: 'd03'`; §1.25): o arquivo gerado nunca muda. As linhas do aparelho que abrem pendência (`pend: true`, F14/F36) são o `alvo` pelo `iso` delas;
- asserção `IDS`: `pend` ⇒ `ref` na agenda e `palavras` não vazias e iguais às da tarefa.

Regras:
- Pendências abertas no arquivo gerado: d03, d05, d07 (3). `CapitaoAgora.contagens().pendencias` conta só as abertas depois de aplicar as ações do aparelho (§1.23).
- Sai a linha "Fundeado… motores desligados" e a do abastecimento antigo de 620 L, que contradizem o modelo de 24 h.
- `who` sempre preenchido. `pessoasBordo` = 4 = o número da d01 (asserção).
- `diasAtras = 0 ⇒ h ≤ ancora_hora` (asserção: nada "hoje" no futuro às 07:02).
- **Nenhuma linha descreve emergência**, alarme crítico, MOB, incêndio ou água no porão acima do normal: `emergencia()` e `oleo() === 1`, portados para Python com a lista `SOS` ampliada da 1b, não casam nenhum `t` (asserção).

### 1.10 `abastecimentos` e `regraAbast`

- Gerado: **`abastecimentos: []`** na simulação (a única lista vazia permitida no arquivo). A microtarefa insere **3 linhas**, uma por dia de bordo (`diasAtras` 0, 1 e 2), a partir de `D.replay.diaDeBordo.abastecimento`:
  `{id: 'ab-<k>', diasAtras: k, h: '07:00', litros: 1086, combustivel: 'diesel', local: 'posto da marina da base', st: 'CONFERIDO', nivelAntes: 29.6, nivelDepois: 97.5, nota: 'para a saída das 07:00 · nota fiscal conferida (Documentos)'}` + `d` **(R)** ('dd/mm/aaaa').
- `litros` = `round(replay.por_dia.diesel_l)` = 1.086 L. `nivelAntes` = fim do dia anterior pelo modelo de 24 h = (1.560 − 1.086,2) / 16 = 29,6 %. `nivelDepois` = 1.560 / 16 = 97,5 % (asserções).
- **`h` = `ancora_hora` (07:00)**, como o PROMPT manda ("o abastecimento das 07:00 entra em `D.abastecimentos` pelo rebase"): o abastecimento é o próprio salto do contador na virada, `em(A − 1 s)` → `em(A)`. Linha, contador, gráfico 1 D da G2, autonomia e IA dizem o mesmo no mesmo instante. Uma linha às 06:45 diria 97,5 % enquanto o replay ainda mostra o barco chegando à base com ~474–485 L (29,6 %). Asserção `DIA_DE_BORDO`.
- São 3 linhas, e não 7, para a ficha caber no teto da asserção «ficha entre 3.000 e 10.000 letras» do `cerebro.py` até a Fase 3 (§6.1). O gráfico de diesel (7 D, 30 D, 1 A) mostra o serrote de todos os dias pelo modelo; a lista mostra os 3 últimos. Na Fase 4, com a G2 nova, o número pode subir para 7 (`diaDeBordo.dias`).
- As linhas antigas (620 L e 540 L) saem: contavam outra rotina que a dos contadores.
- **Lista vazia** (sem o rodapé, com `simulacao: false` ou no SOS): o `consumo` do cérebro (`capitao-brain.js:286`) escreveria "Abastecimentos registrados: ." e ganha no C8 a guarda de 1 linha `(ab.length ? '\nAbastecimentos registrados: ' + … + '.' : '')`, como a ficha já faz (`:595-596`). A G2 cai no caminho vazio de hoje ("ÚLTIMO ABASTECIMENTO SEM DADOS · nenhum registro"), que é o do modo real: na simulação só aparece se o rodapé falhar, e não inventa nada.
- `regraAbast`: "abastecer antes de 25 % do total dos tanques, 400 L de 1.600 L (Checklist de bordo § Abastecimento)", a mesma regra do texto do checklist e do `diesel_litros` (revisão 2 do C5; antes, "em qualquer tanque"). Sai o "(regra de bordo DEMO)". O primeiro número com "%" continua sendo o 25, que a A1 e a G2 leem do texto.
- A IA e o cérebro respondem "quanto consumimos ontem" pelo `por_dia`, nunca pela diferença entre linhas.

### 1.11 `equipe` (F21, prestadores)

- `perfis`: igual a hoje (o proprietário). O convidado continua fora (`convidado: true` no auth).
- `apoio[]`: `{id, papel, onde, para, servico}`. `para` e `servico` têm o mesmo texto até a Fase 4 (compatibilidade com quem lê `para`). **Sem nome de pessoa ou empresa e sem telefone.**

| id | papel | onde | para / servico |
|---|---|---|---|
| marina | Marina da base | Balneário Camboriú (SC) | casco, filtros, vaga |
| oficina | Oficina de motores diesel | atende na marina da base | motores e gerador |
| tecnico | Técnico de bordo | atende na marina da base | estabilizador, elétrica, porão |
| eletronica | Técnico de eletrônicos | atende na marina da base | plotters, rádios, piloto, radar, AIS |
| refrigeracao | Técnico de refrigeração | atende na marina da base | climatização, dessalinizador |
| posto | Posto de combustível | na marina da base | diesel |

- Nenhum papel diz "autorizada <marca>": o app não afirma que um revendedor real atende o barco.
- `nota`: "Telefones: ficam só no aparelho (Equipe)." Sai o "A CADASTRAR".

### 1.12 `consumo`, `reserva`, `autonomia`, `destinos`

| Caminho | Valor | Quem lê |
|---|---|---|
| `consumo.cruzeiro` / `.lenta` / `.maxima` | `{nos: 18, rpm: 2050, lph: 68}` / `{nos: 5, rpm: 700, lph: 6.2}` / `{nos: 25, rpm: 2600, lph: 111}` | autonomia, seguro, destinos, F23 |
| `consumo.gerador_lph` | `2.3` | soma do diesel (o gerador gira 24 h e consome) |
| `consumo.faixas[5]` | `[{rpm_de: 600, rpm_ate: 1000, nome: 'marcha lenta'}, {1000, 1500, 'deslocamento'}, {1500, 1800, 'transição'}, {1800, 2000, 'planeio'}, {2000, 2600, 'cruzeiro'}]` | G2 aba Consumo (F23): os L/h e as horas de cada faixa saem da tabela de 150 s × voltas (`CapitaoReplay.porFaixa()`), nunca de série à parte |
| `consumo.fonte` | `Guia de bordo — Motores Cummins §10 · Consumo` | "Fonte:" |
| `consumo.margemManobra_l` | `60` | destinos, seguro |
| `consumo.periodo`, `consumo.desdeAbast` | **(L até a Fase 3)** forma e valores de hoje | cérebro de hoje |
| `reserva` | `0.10` | autonomia |
| `autonomia` | **(L até a Fase 3)** a de hoje (11,2 h · 202 mn, do snapshot legado) | a asserção do «≈ 11,2 h» do `chat_ia.py` (a `:254` da tabela da Fase 7; hoje `:256`) só muda na Fase 3 |
| `destinos[]` | `{id, nome, mn}` a partir da base, pela rota: Ilha das Cabras 1,0 · Ponta das Laranjeiras 3,4 · Taquaras 5,1 · Estaleirinho 7,4 | rota `destinos` (3): tempo = mn / 18; litros = h × 68; juízo contra `diesel × (1 − reserva) − margem` |

Fórmula única da autonomia (gerador, rodapé e cérebro): `h = L × (1 − reserva) / cruzeiro.lph` (1 casa) · `mn = round(h × cruzeiro.nos)` · `lenta = round(L × (1 − reserva) / lenta.lph)`. Sem R$ em lugar nenhum.

### 1.13 `historico` (F07, F11, G2)

O modelo de 24 h se repete todo dia de bordo, e cada balde de 900, 3.600, 21.600 ou 86.400 s é múltiplo de 150 s e alinhado às 07:00. Então o gerador só guarda o que **não** é laço nem contador: a variação lenta de tempo, temperaturas e baterias, dia a dia, a curva do ano do ar e da água, e as médias de cruzeiro da F11.

```
historico: {
  fim: 'ancora',                         // o último dia guardado termina na âncora do dia de bordo atual
  passo_dias: 2, n: 183,                 // um desvio a cada 2 dias de bordo, do mais antigo (366 dias) até 2 dias atrás
  desvios: {                             // desvio em relação a hoje (hoje = 0), inteiros com escala
    vento_verdadeiro_nos:    {escala: 10,  d: [...183]},     // ±4 nós
    pressao_barometrica_hpa: {escala: 10,  d: [...183]},     // ±7 hPa
    bateria_0_tensao_v:      {escala: 100, d: [...183]},     // ±0,06 V
    bateria_1_tensao_v:      {escala: 100, d: [...183]},
    bateria_2_tensao_v:      {escala: 100, d: [...183]},
    temp_ar_externo_c:       {escala: 10,  d: [...183]},     // ±1,5 °C de um dia para outro
    temp_agua_c:             {escala: 10,  d: [...183]}      // ±0,4 °C
  },
  sazonal: { passo_dias: 5, n: 73,       // curva do ano por dia do calendário (1º de janeiro = índice 0), em relação à média do ano
    temp_ar_externo_c: {escala: 10, d: [...73]},   // +4,5 °C em meados de janeiro, −4,5 °C em meados de julho
    temp_agua_c:       {escala: 10, d: [...73]} }, // +3,5 °C em meados de fevereiro, −3,5 °C em meados de agosto
  cruzeiro: { dias: 60,                  // médias de cruzeiro por dia de bordo, de 60 dias atrás até ontem (F11)
    motor_bb_arref_c: {escala: 10, d: [...60]},   // 82,0 ± 0,2
    motor_be_arref_c: {escala: 10, d: [...60]},   // sobe de ~82,4 a ~83,9 (hoje: 84,5 pelo laço, com os picos)
    motor_bb_oleo_bar: {escala: 100, d: [...60]}, motor_be_oleo_bar: {escala: 100, d: [...60]} },
  janelas: {'150S': {passo_s: 1, n: 150}, '1D': {passo_s: 900, n: 96}, '7D': {passo_s: 3600, n: 168}, '30D': {passo_s: 21600, n: 120}, '1A': {passo_s: 86400, n: 365}},
  metricas: { b24: ['bateria_0_tensao_v', 'bateria_1_tensao_v'], b12: ['bateria_2_tensao_v'],
              tanques: ['tanque_agua_pct', 'tanque_cinzas_pct', 'tanque_negras_pct'], vento: ['vento_verdadeiro_nos'],
              pressao: ['pressao_barometrica_hpa'], diesel: ['diesel_litros'],
              temperaturas: ['temp_praca_maquinas_c', 'temp_ar_externo_c', 'temp_agua_c'],
              motores: ['motor_bb_rpm', 'motor_be_rpm'], oleo: ['motor_bb_oleo_bar', 'motor_be_oleo_bar'],
              arref: ['motor_bb_arref_c', 'motor_be_arref_c'], navegacao: ['sog_nos', 'stw_nos'], consumo: ['consumo_lph'] },
  so150: ['motores', 'oleo', 'arref', 'navegacao', 'consumo'],   // grupos só do laço: só a janela '150S' (nas longas, a volta se repete e a linha sairia reta)
  fonte: 'coletor NMEA de bordo · histórico'
}
```

Como o cliente expande (`CapitaoReplay.serie(campo, janela, ms)`, Fase 2, O(1) por balde):
- **janela '150S'** (a "janela de 150 s" dos gráficos da Fase 4, F07, e as séries do laço da A1, MAPA §2): os 150 valores `em(ms − 149 s)` … `em(ms)`, um por segundo, para qualquer métrica (O(1) cada). Os grupos `so150` (rpm, óleo, arrefecimento, SOG/STW e consumo) só têm essa janela. O último ponto é o quadro; sem NaN;
- **campo do laço** (baterias, vento, pressão): min/média/máx da volta (pré-calculados na carga) + o desvio do dia, interpolado linearmente entre os pontos de 2 em 2 dias até 0 na âncora de hoje. A curva é contínua na virada e o quadro de hoje não muda;
- **ar e água** (`temperaturas`; no laço ficam constantes, 22,6 e 20,1 °C, e sem isto o gráfico de 30 D ou 1 A sairia reto): quadro de hoje + [`sazonal`(dia) − `sazonal`(hoje)] + o desvio do dia, interpolado até 0 hoje. A tabela é por dia do calendário, interpolada linearmente (sem `Math.sin`). O último ponto é o quadro, com a trava do ar **e da água** do §1.22: o "quadro de hoje" que serve de base à curva já passa pela `CapitaoAgora.trava` (a mesma do `instante()`), e a série inteira acompanha, contínua. A praça de máquinas é campo do laço mais o desvio do ar, sazonal e do dia (a praça acompanha o ar externo). No gráfico, as três séries são "a bordo" (sensor), nunca previsão nem clima da cidade (§2.5);
- **campo de contador** (diesel, tanques): `contadoresEm(início)` e `contadoresEm(fim)` do balde, pelo mesmo modelo de 24 h. O gráfico de diesel mostra o mesmo serrote que a G2 e as linhas de abastecimento;
- o balde que contém "agora" termina no **quadro atual** (último ponto = quadro);
- nenhum `NaN` nem `null`; nenhuma série de maré (é só a real, §2.5).

**F11:** três achados por regra fixa, cada um com a fonte:
1. histórico (`cruzeiro` mais a média de cruzeiro de hoje, pelo laço): "Motor BE 2,5 °C acima do BB em cruzeiro, subindo há 60 dias";
2. contadores: "faltam 32,4 h para a troca de óleo" (e 58,6 h para a revisão do gerador);
3. **instante** (`instante().q`, `instante().tend` e `D.replay.limites`, §1.23): o arrefecimento do BE agora contra a faixa e a tendência de 30 s. É este que muda entre t = 60 e t = 105, o teste da PARIDADE:
   - 12:01:00 (t = 60): "Arrefecimento do motor BE agora: 82,1 °C, dentro da faixa normal (até 88 °C); +2,8 °C nos últimos 30 s."
   - 12:01:45 (t = 105): "Arrefecimento do motor BE agora: 89,6 °C, acima de 88 °C — AVISO desde 12:01:39; +7,5 °C nos últimos 30 s."

Os achados 1 e 2 são iguais nos dois instantes: em 45 s, as horas que faltam não mudam com 1 casa (32,4 h nos dois).

**`serie24v` (L até a Fase 4):** 7 itens `{diasAtras: 6…0, min, max}` = min/máx da volta do banco de serviço + o desvio do dia, e **(R)** `d` ('dd/mm', base dia de bordo).

Asserção: com os desvios, nenhum valor de histórico cruza limite (baterias ≥ 24,4 + 0,05; vento ≥ 0; praça ≤ 60 − 0,05).

### 1.14 `rota` (decisão j)

```
rota: {
  fonte: 'Plano de navegação de bordo · Barra Sul ⇄ Estaleirinho',
  base:    {id: 'base', nome: 'Barra Sul (saída do Rio Camboriú)', rel: 'da Barra Sul', perto: 'na saída da Barra Sul', lat, lon, prof_m: 8},
  pontos:  [{id, nome, rel, perto, lat, lon, prof_m} ×7],   // ordem do circuito depois da base; o último liga de volta à base; rel = 'da Ponta das Laranjeiras', 'de Taquaras'… (para a `relativa`)
  destino: {id: 'estaleirinho', nome: 'Estaleirinho', caminho: 'a caminho do Estaleirinho'},
  volta:   {nome: 'Barra Sul (base)', caminho: 'a caminho da Barra Sul'},
  pernas:  [{de, para, mn, rumo, ini_mn} ×8],          // pré-calculadas: o cliente não recalcula distância
  distancia_mn: 15.42, ida_mn: 7.37,
  circuitos_dia: 19, fator: 0.9407,    // primo com as 576 voltas do dia; a posição anda distancia_mn × fator: o dia fecha 19 circuitos e o barco está na base às 06:59:59
  guinada_max_gps: 3,                   // °/s a 18 nós: arco de |Δ|/3 × 18/3600 mn em volta de cada ponto
  corrente: {nos: 0.3, para_graus: 200} // STW e proa (§1.22)
}
```

- Pontos, rumos e distâncias: §2.6. Os nomes são lugares públicos da costa: nenhuma marina, empresa ou pessoa.
- **Por que 19 circuitos, e não 20.** Com 20, cada circuito tem 28,8 voltas e 5 circuitos são 144 voltas exatas. A chegada à base cairia exatamente numa emenda N·150 às 13:00, 19:00 e 01:00, com `destino`, `destino_mn` (≈ 0 → 7,4), `eta` e `wp_*` trocando em degrau no segundo da emenda. Com `circuitos_dia` primo com 576 (= 2⁶ · 3²), `k · 576 / 19` só é inteiro em k = 19, a âncora. Medido em `emenda.py`/`emenda2.py`:
  - 151 chegadas a ponto e 37 trocas de destino por dia; a chegada a ponto mais perto de uma emenda fica a 1 s dela, e a troca de destino mais perto, a 3 s;
  - nas 575 emendas fora da âncora, o maior passo de `destino_mn` e `wp_mn` (0,1), COG (1°), profundidade (0,4) e `piloto_rumo` (0) é o de qualquer segundo da volta, e a ETA não muda.
- **Custo do fator 0,9407:** a posição anda ~6 % menos que a soma do SOG (o odômetro `distancia_mn` dá 311,5 mn por dia; a rota, 293,0). Para ter fator perto de 1 com os mesmos 19 circuitos, basta alongar o circuito para ~16,4 mn no portão manual (§2.6); o gerador recalcula o resto (pede ok, §8.2).
- **`local` e `relativa`:**
  - `local` = `perto` do ponto nomeado mais perto + ", " + `caminho` do destino. Quando o ponto mais perto é o próprio destino: `perto` + ", chegando" (ex.: "na saída da Barra Sul, chegando");
  - `relativa` = "a <wp_mn> mn " + `rel` do próximo ponto + ", " + `caminho`, ou + ", chegando" quando o próximo ponto é o destino (ex.: "a 0,5 mn da Barra Sul, chegando");
  - `local` troca no meio da perna e pode cair numa emenda: é texto, não é distância nem ETA, e a `EMENDA_ROTA` não o cobra.
- `prof_m` entre 8 e 22 m; a profundidade do quadro é interpolada na perna, com ruído pequeno (asserção: mínimo ≥ `calado` + 4 m).
- **Privacidade:** as coordenadas ficam só aqui e no quadro. Ficha, `resumo`, série da pasta 05 e todo texto levam só nome e distância.
- Com `SIMULACAO = False`, o gerador **não emite** `rota` (rota real num repositório público entrega os lugares de costume do barco).

### 1.15 `campos` (catálogo único do quadro)

`D.campos = {<campo>: {rotulo, un, casas, origem, sentido?, mil?, ang?, desc?}}`, uma entrada por campo do quadro (§1.22), no topo do `D` (vale nos dois modos e para o coletor real da Fase 8).
- `origem` ∈ {`laço`, `rota`, `contador`, `derivado`, `fixo`, `relógio`, `janela`}.
- `sentido` ∈ {+1, −1}, só (e sempre) nos de origem `contador`: +1 em `motor_bb_horimetro_h`, `motor_be_horimetro_h`, `gerador_horimetro_h`, `distancia_mn`, `tanque_cinzas_pct` e `tanque_negras_pct`; −1 em `diesel_litros` e `tanque_agua_pct`. É por ele que o `replay.py` confere "contadores sem voltar": fora do par `A − 1 s` × `A`, `sentido · (v(ms + 1 s) − v(ms)) ≥ 0` (no valor arredondado).
- `casas` é a fonte única do arredondamento: o formatador, a cor, a avaliação de alarme e o gerador (janelas) usam o valor **como a tela mostra**: `floor(x · 10^casas + 0,5) / 10^casas`, com `-0` → `0`.
- **Conferência quadro ⇔ catálogo** (`replay.py`, e a `LACO` no gerador): roda sobre `CapitaoReplay.em(ms)`, nos dois sentidos (todo campo do quadro está no catálogo, e todo campo do catálogo está no quadro). Sobre o `snapshot.quadro`, num sentido só: todo campo dele está no catálogo, e os que faltam são só de origem `rota` ou `janela` (§1.17). O `simulado: true` que o `CapitaoTelemetria.atual()` acrescenta é marca, não leitura: fica **fora** do catálogo, e a conferência não roda sobre o `atual()`.
- O gerador escreve o `Formato do quadro do coletor.csv` (pasta 05) a partir dele.

### 1.16 `replay` (quadros-chave; o motor é da Fase 2)

| Caminho | Tipo | Valor | Quem usa |
|---|---|---|---|
| `duracao`, `passo`, `passo_chave` | int s | 150, 1, 5 | 30 quadros-chave, t = 0, 5, …, 145; o segmento 145 → 150 usa o t = 0 |
| `cenario` | 'aviso' \| 'alarme-critico' | `'aviso'` (decisão c) | informativo: o gerador já escolheu chaves e janelas; o cliente nunca decide alarme |
| `ancora_hora` | 'HH:MM' | `'07:00'` (no `embarcacao.fuso`) | `CapitaoAgora.ancora()`, a mesma para rebase e replay |
| `voltas_fixo` | int | `120` | `fixar(60)` = `fixar('60')` = âncora + 120 voltas + 60 s = **12:01:00**; `'60@K'` usa K voltas; `fixar(null)` solta (§1.24) |
| `velocidade_media_nos` | number | `12.21` | ETA: velocidade média de rota na volta (SOG médio 12,98 × fator 0,9407) |
| `fases[5]` | `{ini, fim, nome}` | 0–20 marcha lenta · 20–50 aceleração · 50–120 cruzeiro · 120–135 redução · 135–150 marcha lenta | `fase()`, ficha, `resumo()`. Nomes sem "simulação", "roteiro", "laço", "cenário" nem "150 s" |
| `chaves` | `{campo: number[30]}` | §3.1 (colunas, uma linha cada) | interpolação |
| `ruido` | `{campo: [amplitude, semente]}` | §3.2 | ruído por hash, periódico em t |
| `fixos` | obj | `{marcha: 'avante', estado: 'Navegando', gerador_ativo: true, seakeeper_ativo: true, ancora_estado: 'recolhida', bomba_porao_ciclos: 0, gps_satelites: 18, climatizacao_ativa: true, dessalinizador_ativo: false, radar_ativo: true, ais_alvos: 4}` | quadro |
| `contadores_base` | obj | `{motor_bb_horimetro_h: 412.6, motor_be_horimetro_h: 409.8, gerador_horimetro_h: 1236.4, diesel_litros: 1560, distancia_mn: 0, tanque_agua_pct: 92, tanque_cinzas_pct: 8, tanque_negras_pct: 5}` (valores **na âncora**) | `contadores()` |
| `taxas_h` | obj | `{tanque_agua_pct: -1.2, tanque_cinzas_pct: 1.4, tanque_negras_pct: 0.9}` (por hora desde a âncora) | tanques |
| `por_volta` | obj | `{diesel_l: 1.8857, motores_l: 1.7899, gerador_l: 0.0958, distancia_mn: 0.5408, motor_h: 0.041667, gerador_h: 0.041667}` | paridade gerador × cliente |
| `por_dia` | obj | `{voltas: 576, diesel_l: 1086.2, distancia_mn: 311.5, motor_h: 24, gerador_h: 24}` | abastecimento, asserções |
| `diesel_piso_l` | number | `400` (regra de 25 %) | corte de segurança; asserção: 1.560 − 1.086,2 = 473,8 ≥ 400 + 50, o piso nunca age |
| `limites` | §3.3 | — | C3, cores, `capitao-alertas`, F09, F11, F12, ficha; vale também no modo real. Avaliados **só** pela `CapitaoAgora.nivel` (§1.23) e pelo port dela no gerador |
| `alertas` | catálogo abaixo | — | C3 (`#alarme=<id>` e `#a=<id>`), `capitao-alertas`, E1, ficha |
| `janelas[]` | `{id, campo, nivel, ini, fim}` | **derivadas pelo gerador**: `[{id: 'arref_be', campo: 'motor_be_arref_c', nivel: 'aviso', ini: 99, fim: 116}]` | `alarmes()`, faixa, C3, E1 |
| `diaDeBordo` | obj | `{dias: 3, abastecimento: {...}, documento: {nf-abast}, diario: [d01, d02]}` (§1.8–§1.10) | microtarefa do rodapé |

**`alertas`** (id estável por campo; o nível sai de `limites`):
`{id: {campo, sistema, lado?, titulo, guia, secao, passos[], fonte}}` com os ids `arref_bb`, `arref_be`, `oleo_bb`, `oleo_be`, `rpm_bb`, `rpm_be`, `carga_bb`, `carga_be`, `praca`, `b24s` (serviço), `b24p` (partida), `b12`, `porao_bb`, `porao_be`, `profundidade`, `diesel`, `gerador`, `seakeeper`, `agua`, `cinzas`, `negras`.
- Ex.: `arref_be: {campo: 'motor_be_arref_c', sistema: 'motores', lado: 'be', titulo: 'Temperatura do motor BE', guia: 'g_motores', secao: '5 · Temperatura alta', passos: [3 passos do §5], fonte: 'Guia de bordo — Motores Cummins §5 · Temperatura alta'}`.
- `oleo_bb.passos` = `oleo_be.passos` = `protocolos.oleo`. O fabricante na C3 sai de `D.equipamentos.find(e => e.id === alerta.sistema)` (§1.4).
- `sistema` de cada alerta: `motores` (arref, oleo, rpm, carga, praca) · `eletrico` (b24s, b24p, b12) · `porao` (porao_bb, porao_be) · `eletronicos` (profundidade, a sonda dos plotters) · `tanques` (diesel, agua, cinzas, negras) · `gerador` · `estabilizador` (seakeeper). O mesmo valor vai para `alarmes[].sistema` do quadro.
- Um id por campo, com o nível conforme o valor (aviso → crítico → aviso). A faixa anuncia **uma vez por id por sessão**; a fase `'nivel'` do evento marca a troca de nível.

Com `CENARIO = 'aviso'`, o gerador **não emite** nada do crítico: o cliente nunca tem o que ligar. Com `SIMULACAO = False`, `replay` sai só com `limites` e `alertas`.

### 1.17 `snapshot` (reserva aninhada e modo real; o rebase nunca toca)

- **Fase 1 (L):** forma e números de hoje (26/09/2026 10:12, fundeado, 848 L), sem `null` e sem rótulo:
  - `fonte`: `coletor NMEA · leitura de 26/09/2026 10:12` (sem "snapshot" nem "(DEMO)");
  - `porao: {bb_cm: 1.2, be_cm: 0.9, ciclos_h: 0}` e `ancora: {estado: 'lançada', cabo_m: 30}` (o enum do quadro; coerente com fundeado);
  - `seakeeper: {estado: 'ligado', volante_rpm: 8420, volante_pct: 100, hora}`; `gerador.kw: 5.6`;
  - **`snapshot.quadro`** novo: o mesmo instante no formato plano do quadro (motores parados: rpm 0, `marcha: 'neutro'`, `estado: 'Fundeado'`, `ancora_estado: 'lançada'`; os campos de rota que não se aplicam fundeado, como `destino`, `eta` e `wp_*`, são omitidos, e `alarmes` também, porque a ausência quer dizer sem alarme, §1.0), para o `instante()` cair nele com `fonte: 'snapshot'` (nunca em S1/S2). Valores (26/09/2026 10:12, fundeado), um por campo do catálogo:
    `timestamp_utc: '2026-09-26T13:12:00Z'` · `lat: -26.993`, `lon: -48.614` · `cog_graus: 71` · `proa_graus: 71` · `leme_graus: 0` · `sog_nos: 0.1` · `stw_nos: 0.3` (corrente de 0,3 nó, a do §1.14) · `profundidade_m: 7.4` · `motor_bb_rpm: 0`, `motor_be_rpm: 0` · `motor_bb_oleo_bar: 0`, `motor_be_oleo_bar: 0` · `motor_bb_arref_c: 54`, `motor_be_arref_c: 53` · `motor_bb_carga_pct: 0`, `motor_be_carga_pct: 0` · `marcha: 'neutro'` · `consumo_lph: 0` · `diesel_litros: 848`, `diesel_bb_pct: 54`, `diesel_be_pct: 52` · `distancia_mn: 11.6` · `motor_bb_horimetro_h: 412.6`, `motor_be_horimetro_h: 409.8` · `gerador_ativo: true`, `gerador_kw: 5.6`, `gerador_horimetro_h: 1236.4` · `seakeeper_ativo: true`, `seakeeper_volante_rpm: 8420`, `seakeeper_volante_pct: 100` · `bateria_0_tensao_v: 27.42`, `bateria_1_tensao_v: 27.2`, `bateria_2_tensao_v: 13.18` · `tanque_agua_pct: 68.5`, `tanque_cinzas_pct: 21`, `tanque_negras_pct: 34.5` · `porao_bb_nivel: 1.2`, `porao_be_nivel: 0.9`, `bomba_porao_ciclos: 0` · `ancora_estado: 'lançada'` · `ondas_m: 0.5` · `vento_verdadeiro_nos: 9.2`, `vento_verdadeiro_angulo: 58`, `vento_aparente_nos: 9.2`, `vento_aparente_angulo: -13` · `pressao_barometrica_hpa: 1017` · `temp_ar_externo_c: 22.6`, `temp_agua_c: 20.1` · `temp_praca_maquinas_c: 38` · `jogo_graus: 0.6`, `caimento_graus: 0.4` · `gps_satelites: 26` · `climatizacao_ativa: true`, `dessalinizador_ativo: false`, `radar_ativo: false`, `ais_alvos: 3` · `estado: 'Fundeado'` · `local: 'na enseada de Balneário Camboriú'`.
    Omitidos (origem `rota` sem destino, ou `janela`): `piloto_rumo`, `destino`, `destino_mn`, `wp_proximo`, `wp_mn`, `eta` e `alarmes`. Os números batem com o snapshot aninhado (848 L = (54 + 52) × 8; horímetros, gerador, volante, baterias de serviço e 12 V, tanques, porão, vento, ar, água, satélites e posição iguais); o que o aninhado não tem (arrefecimento e praça com os motores parados há 41 min, banco de partida, ondas, inclinação, STW) é coerente com o barco fundeado e o gerador ligado. Pela `nivel` (§3.3), todo campo dá `normal` ou não avalia (motores com rpm 0 ficam fora pelo `ativo_se`).
  - **`snapshot.gps.texto` (L)** é o único texto de coordenada do `D` e a única exceção da `COORD_TEXTO` (§6.3). Fica enquanto houver leitor:
    - `S1-SOS-Web.dc.html:145` e `S2-SOS-Mobile.dc.html:120` (saem na 1b);
    - `capitao-brain.js:92` (Fase 3);
    - `A1-Ponte-Web.dc.html:264/:318`, `E1-Navegando-Gatilhos.dc.html:164`, `E2-Navegando-Sintoma.dc.html:246`, `F3-FAQ-Eletronicos-Web.dc.html:221`, `F3-FAQ-Eletronicos.dc.html:215` e `capitao-moldura.js:46` (Fase 4);
    - `capitao-voz.js:59-61` (HUD, Fase 5).
    No commit que troca o último leitor, o gerador deixa de emitir o texto e a exceção sai. Quem precisar dele usa `CapitaoAgora.fmt.coord(lat, lon)`, só na tela. A leitura da pasta 05 já não tem o texto (só `lat`/`lon` numéricos).
  - **No mesmo commit**, as guardas de 1 linha nos três leitores que fariam `[object Object]`: `B2-Carta-Mobile.dc.html:158` (`'porão: ' + S.porao`), `F3-FAQ-Eletronicos-Web.dc.html:222` e `F3-FAQ-Eletronicos.dc.html:216` (`String(S.ancora)`). A1:328-329, A2:221 e E1:183 já tratam objeto.
  - Assim o «≈ 11,2 h» do `chat_ia.py` e as respostas que leem `SNAP` não quebram antes da Fase 3.
- **Fase 3**, no commit que troca a asserção do «≈ 11,2 h»: o snapshot (aninhado e `quadro`) passa a ser o **quadro da âncora** (07:00, t = 0, navegando, 1.560 L, saindo da Barra Sul), com `quando: '07:00'` sem data. A reserva conta a mesma história do replay. O arquivo da pasta 05 vira `Leitura do coletor NMEA — início do dia de bordo (07:00).json`.
- **Travas:**
  - S1/S2 não leem `snapshot`;
  - o `rebase()` não escreve em `D.snapshot`. A única referência do `rodape.js` ao snapshot é a leitura de `D.snapshot.quadro` dentro de `instante()`, que em S1/S2 devolve `null` antes de ler (§1.23; asserção `RODAPE_SNAPSHOT`);
  - um teste compara `JSON.stringify(D.snapshot)` antes e depois do rodapé e do rebase (06:59:59, 07:00:01, 23:59).

### 1.18 `checklists` (F09)

Forma: `{fonte: 'Checklist de bordo', tipos: [{id, l, aba, nome, sys}], itens: {<tipo>: [{id, c, t, fonte, auto?, parcial?, faq?, link?}]}}`. `faq` é id que existe no `faq-equipamentos.json`; `fonte` é um §n que existe ou "boa prática" (asserções).

- `tipos` (4, nesta ordem): `{id: 'saida', l: 'Saída', aba: 'antes de largar', nome: 'Checklist de saída', sys: 'Navegação'}` · `{id: 'chegada', l: 'Chegada', aba: 'ao atracar', nome: 'Checklist de chegada', sys: 'Navegação'}` · `{id: 'abastecimento', l: 'Abastecimento', aba: 'no posto', nome: 'Checklist de abastecimento', sys: 'Combustível'}` · `{id: 'fundeio', l: 'Fundeio', aba: 'ao fundear', nome: 'Checklist de fundeio', sys: 'Navegação'}`. `l` é o rótulo da aba, `aba` a linha curta embaixo dele, `nome` o título da tela e `sys` a categoria (as do diário de hoje) da linha que o CONCLUIR grava.
- `c` é o rótulo curto do item: é o que entra na lista de pendentes da linha do CONCLUIR. Sem número, sem lugar a bordo e sem palavra da `SOS` ampliada (asserção `SEM_EMERGENCIA`, que passa a cobrir `c`):
  - saída: s01 `previsão` · s02 `alertas` · s03 `motores frios` · s04 `porão` · s05 `diesel` · s06 `tanques` · s07 `baterias` · s08 `gerador` · s09 `estabilizador` · s10 `plotter e VHF` · s11 `documentos` · s12 `tarefas de segurança` · s13 `coletes e salvatagem` · s14 `cabos e defensas`;
  - chegada: c01 `piloto` · c02 `estabilizador` · c03 `motores` · c04 `gerador` · c05 `climatização` · c06 `porão` · c07 `cabos e defensas` · c08 `diário`;
  - abastecimento: a01 `motores` · a02 `gerador` · a03 `nível antes` · a04 `sem fumar` · a05 `bocal e tampa` · a06 `nível depois` · a07 `regra do diesel`;
  - fundeio: f01 `profundidade` · f02 `corrente` · f03 `alarme de âncora` · f04 `deriva` · f05 `guincho` · f06 `maré e vento`.
- Os `t` abreviados na tabela abaixo ficam por extenso: c06 "Porão conferido: nível normal e bombas no automático." · c07 "Cabos e defensas prontos antes de atracar." · a07 "Diesel acima de 25 % em cada tanque antes de sair." (`fonte` `Checklist de bordo § Abastecimento`, `faq` CK-05).

| tipo | itens (id · texto · auto · faq) |
|---|---|
| `saida` (14) | s01 "Previsão do dia consultada (vento e mar) — confira o boletim da Marinha antes de sair." · `tempo`, `parcial` · s02 "Nenhum alerta ativo no painel." · `alertas` · s03 "Óleo, arrefecimento, correias e válvulas de fundo conferidos com os motores frios." · MO-01 · s04 "Porão seco e bombas testadas no manual." · `porao`, `parcial` (nível pelo quadro; o teste das bombas só com o toque, porque o `porao-teste` está atrasado e a d01 diz que o teste continua pendente) · PO-03 · s05 "Diesel acima de 25 % em cada tanque." · `diesel` · s06 "Água doce acima de 15 %; servidas abaixo de 80 %." · `tanques` · s07 "Bancos de 24 V e 12 V dentro da faixa." · `baterias` · EE-02 · s08 "Gerador ligado: água saindo pelo escapamento." · GE-03 · s09 "Estabilizador ligado com antecedência (o display indica quando está pronto)." · `seakeeper` · SK-02 · s10 "Plotter ligado, piloto em espera e VHF no canal 16." · EL-04 · s11 "Documentos em dia (TIE, seguro, Licença de Estação)." · `documentos`, `parcial` · s12 "Nenhuma tarefa de segurança atrasada." · `tarefas` (sobre `agenda[].seguranca`: `epirb-teste`, `seafire-inspecao`, `porao-teste`; §1.7) · s13 "Coletes: um por pessoa — conte as pessoas a bordo agora; balsa, boia e extintores conforme a placa de salvatagem." · EM-09 · s14 "Cabos e defensas recolhidos depois de largar." (boa prática) |
| `chegada` (8) | c01 "Piloto em espera antes de manobrar." · EL-02 · c02 "Estabilizador desligado ao atracar; energia até o volante parar." · `seakeeperOff` · SK-04 · c03 "Motores 2 a 3 min em marcha lenta antes de desligar." · `motoresOff` · MO-06 · c04 "Gerador sem cargas, alguns minutos para esfriar e desligado." · `geradorOff` · GE-04 · c05 "Climatização desligada e válvula de fundo fechada se o barco ficar parado." · CL-05 · c06 porão conferido · `porao` · c07 cabos e defensas · c08 "Saída fechada no diário: horas, consumo e pendências." · `link` diário |
| `abastecimento` (7) | a01 "Motores desligados." · `motoresOff` · a02 "Gerador desligado." · `geradorOff` · a03 "Nível de diesel anotado antes." · `diesel` · a04 "Sem fumar a bordo; extintor portátil à mão." · a05 "Bocal certo (diesel) e tampa do tanque fechada depois." · a06 "Nível depois anotado em Abastecimento." · `link` G2 · a07 regra dos 25 % (CK-05) |
| `fundeio` (6) | f01 "Profundidade conferida na sonda." · `profundidade` · EL-08 · f02 "Corrente: lance de 3 a 5 vezes a profundidade." · AN-01 · f03 "Alarme de âncora ativado no plotter, com o raio." · EL-03 · f04 "Motores em neutro e deriva conferida." · `deriva` · f05 "Guincho desligado e trava da corrente." · AN-03 · f06 "Maré e vento conferidos (previsão da Marinha)." · `mare` |

Travas:
- `tempo` e `mare` **nunca dão ✓ sozinhos**: mostram a leitura real do `CapitaoClima` e pedem o toque (§2.5).
- Nenhum item tem lugar de salvatagem nem número de pessoas. Nenhum casa `emergencia()` nem `oleo() === 1` (asserção: o CONCLUIR grava 1 linha no diário e essa linha não pode virar diário com alerta).
- Com `simulacao: false`, o `auto` sem leitura volta ao estado "sem" (SEM DADOS) do modo real.

**Estado esperado de cada item `auto`** (só o s02 muda de estado entre os dois instantes; é o teste "item conferido muda com o replay" da F09):

| item | 12:01:00 (t = 60) | 12:01:45 (t = 105) |
|---|---|---|
| s01 `tempo`, f06 `mare` | pedem o toque (mostram a previsão e a maré reais, ou "sem conexão") | idem |
| s02 `alertas` | ✓ nenhum alerta | ✗ AVISO `arref_be` (89,6 °C) |
| s04 `porao` (parcial) | nível ✓ (1,1 / 0,9 cm); o teste pede o toque (atrasado na agenda) | idem (1,2 / 0,9 cm) |
| s05 `diesel` | ✓ 83,7 / 82,9 % | ✓ 83,6 / 82,9 % |
| s06 `tanques` | ✓ água 86,0 %, cinzas 15,0 %, negras 9,5 % | idem |
| s07 `baterias` | ✓ 27,79 · 27,95 · 13,69 V | ✓ 27,80 · 27,97 · 13,69 V |
| s09 `seakeeper` | ✓ volante 100 % | idem |
| s11 `documentos` (parcial) | nenhum vencido (o seguro vence em 19 D); pede o toque | idem |
| s12 `tarefas` | ✗ `porao-teste` atrasado | idem |
| c02 `seakeeperOff`, c03 e a01 `motoresOff`, c04 e a02 `geradorOff` | ✗ ligados (navegando) | idem |
| c06 `porao` | ✓ nível | idem |
| a03 `diesel` | ✓ 1.333 L (83,3 %) | ✓ 1.332 L (83,3 %) |
| f01 `profundidade` | ✓ 10,0 m | ✓ 9,0 m |
| f04 `deriva` | ✗ navegando (18,1 nós) | ✗ navegando (18,0 nós) |

### 1.19 `sensores` (F08)

Forma: `{perfil: {img, w, h}, planta: {img, w, h}, referencia: {popa_x: 0.04, proa_x: 0.95, quilha_y: 0.92, topo_y: 0.08, eixo_y: 0.5, meia_boca: 0.32}, pontos: [{n, id, vista, l, a?, b?, x, y, rotulo, onde, campos[], bloco: {web: [bx, by, lado], app: [bx, by, lado]}}]}`.
- `l` = posição longitudinal (0 popa → 1 proa); perfil `a` (0 quilha → 1 topo); planta `b` (−1 BB → +1 BE). O gerador calcula `x = popa_x + l·(proa_x − popa_x)`, perfil `y = quilha_y + a·(topo_y − quilha_y)`, planta `y = eixo_y + b·meia_boca`. O desenho é próprio e genérico (Fase 4) e segue a `referencia`.
- `perfil: {img: 'assets/sensores-perfil.svg', w: 1200, h: 360}` e `planta: {img: 'assets/sensores-planta.svg', w: 1200, h: 420}`. O contrato fixa caminho e tamanho; o desenho da Fase 4 é feito nesse tamanho (viewBox `0 0 w h`) e nessa `referencia`, e entra no `CORE` e na conferência offline. O gerador não lê o arquivo. `x`, `y`, `bx` e `by` são frações da largura e da altura da imagem.
- `bloco` (gerado, por regra): por vista, os pontos em ordem de `x`; `lado` alterna `'cima'` e `'baixo'`; dentro do lado, o bloco vai na 1ª fileira em que fica a ≥ 0,10 do bloco anterior dessa fileira. Web: `by` 0,05 ou 0,15 (cima), 0,85 ou 0,95 (baixo). App: 0,04 ou 0,13, 0,87 ou 0,96. `bx` = `x` limitado a [0,06, 0,94]. Asserção `IDS`: dois blocos da mesma fileira nunca a menos de 0,10. A Fase 4 confere a sobreposição na tela (`verificar.py` A4/A5).

| n | id | vista | l / a ou b | rótulo | onde | campos |
|---|---|---|---|---|---|---|
| 1 | gps | perfil | 0,55 / 0,95 | Antena GPS | hard-top | `gps_satelites` |
| 2 | radar | perfil | 0,52 / 1,0 | Radar | mastro do radar | `radar_ativo` |
| 3 | meteo | perfil | 0,48 / 1,0 | Estação meteorológica | mastro do radar | `vento_verdadeiro_nos`, `vento_verdadeiro_angulo`, `vento_aparente_nos`, `vento_aparente_angulo`, `temp_ar_externo_c`, `pressao_barometrica_hpa` (a F33 com TWA: `vento_verdadeiro_angulo − proa_graus`, derivado, sem campo; o ar com a trava do §1.22) |
| 4 | sonda | perfil | 0,62 / 0,05 | Sonda | casco · meia-nau | `profundidade_m`, `temp_agua_c` |
| 5 | inclinometro | perfil | 0,50 / 0,35 | Inclinômetro | meia-nau | `jogo_graus` (roll), `caimento_graus` (pitch), `proa_graus` (yaw): o roll/pitch/yaw da F08 |
| 6 | estabilizador | perfil | 0,45 / 0,20 | Estabilizador | praça de máquinas · centro | `seakeeper_volante_rpm`, `seakeeper_volante_pct` |
| 7 | praca | perfil | 0,25 / 0,30 | Praça de máquinas | praça de máquinas | `temp_praca_maquinas_c` |
| 8 | motor_bb | planta | 0,25 / −0,40 | Motor BB | praça de máquinas · BB | `motor_bb_rpm`, `motor_bb_oleo_bar`, `motor_bb_arref_c`, `motor_bb_carga_pct`, `motor_bb_horimetro_h` |
| 9 | motor_be | planta | 0,25 / +0,40 | Motor BE | praça de máquinas · BE | idem BE |
| 10 | gerador | planta | 0,18 / 0 | Gerador | praça de máquinas · ré | `gerador_kw`, `gerador_horimetro_h` |
| 11 | diesel_bb | planta | 0,38 / −0,60 | Tanque de diesel BB | meia-nau · BB | `diesel_bb_pct` |
| 12 | diesel_be | planta | 0,38 / +0,60 | Tanque de diesel BE | meia-nau · BE | `diesel_be_pct` |
| 13 | agua | planta | 0,60 / 0 | Tanque de água doce | meia-nau | `tanque_agua_pct` |
| 14 | servidas | planta | 0,70 / +0,30 | Tanques de servidas | meia-nau · BE | `tanque_cinzas_pct`, `tanque_negras_pct` |
| 15 | b24s | planta | 0,30 / −0,15 | Banco de serviço 24 V | praça de máquinas · BB | `bateria_0_tensao_v` |
| 16 | b24p | planta | 0,30 / +0,15 | Banco de partida 24 V | praça de máquinas · BE | `bateria_1_tensao_v` |
| 17 | b12 | planta | 0,55 / +0,20 | Banco 12 V | painel do comando | `bateria_2_tensao_v` |
| 18 | porao_bb | planta | 0,22 / −0,25 | Sensor de nível do porão BB | praça de máquinas · BB | `porao_bb_nivel` |
| 19 | porao_be | planta | 0,22 / +0,25 | Sensor de nível do porão BE | praça de máquinas · BE | `porao_be_nivel`, `bomba_porao_ciclos` |
| 20 | leme | planta | 0,04 / 0 | Leme | popa | `leme_graus`, `piloto_rumo` |
| 21 | guincho | planta | 0,95 / 0 | Guincho e contador de corrente | proa · guincho da âncora | `ancora_estado` |
| 22 | dessal | planta | 0,33 / +0,20 | Dessalinizador | praça de máquinas · BE | `dessalinizador_ativo` |

Travas: **nenhum ponto é equipamento de salvatagem nem de incêndio** (asserção por `id` e `rotulo`); `onde` de vocabulário fechado e sem "boia"; `campos` ⊂ `D.campos`, e a união deles cobre os da F08 (`jogo_graus`, `caimento_graus`, `proa_graus`) e da estação da F33 (vento verdadeiro e aparente, `temp_ar_externo_c`, `pressao_barometrica_hpa`); `bloco` pela regra acima, com o lado alternado (conferido na Fase 4).

### 1.20 `pecas` (F22)

Forma: `{id, n, qtd, min, local, tarefas?: [ids da agenda], obs?}`. **Sem `pn`** (código inventado de fabricante real leva à compra errada) e sem R$.

| id | n | qtd / mín | local | tarefas |
|---|---|---|---|---|
| p01 | Filtro de óleo do motor | 4 / 2 | estante técnica 1 | motores-oleo |
| p02 | Filtro de combustível (separador de água) dos motores | 4 / 2 | estante técnica 1 | motores-revisao |
| p03 | Rotor (impeller) da bomba de água salgada dos motores | **1 / 2** (BAIXA) | caixa de sobressalentes A | motores-rotor |
| p04 | Correia do alternador | 2 / 1 | caixa de sobressalentes A | motores-revisao |
| p05 | Rotor (impeller) do gerador | **0 / 1** (ZERO; = a d03) | caixa de sobressalentes B | gerador-rotor |
| p06 | Filtro de óleo do gerador | 2 / 1 | estante técnica 2 | gerador-revisao |
| p07 | Anodo do trocador de calor do estabilizador | 2 / 1 | caixa de sobressalentes B | seakeeper-anodo |
| p08 | Jogo de anodos do eixo e do casco | 1 / 1 | estante técnica 3 | casco-anodos |
| p09 | Tela do filtro de água salgada da climatização | 1 / 1 | caixa de sobressalentes C | clima-filtro |
| p10 | Pré-filtro do dessalinizador | 2 / 2 | caixa de sobressalentes C | — |
| p11 | Jogo de fusíveis de 24 V | 1 / 1 | armário de ferramentas | baterias |
| p12 | Escova do limpador do para-brisa | 2 / 1 | armário de ferramentas | — |

Travas: nenhuma peça de salvatagem; `local` de vocabulário fechado (estante técnica 1–3, caixa de sobressalentes A–C, armário de ferramentas); nunca "kit"; `tarefas` ⊂ ids da agenda; movimentos do aparelho em `capitao.pecas.v1` (a base gerada não se muta).

### 1.21 `alarmesPedidos` (F12, lista fechada)

```
alarmesPedidos = { chave: 'capitao.alarmes.v1', max: 10, histerese_s: 10, nivel: 'aviso',
  fonte: 'alarme pedido no chat · avaliado neste aparelho',
  metricas: [ {id, campos[], nome, palavras[], un, casas, faixa: [min, max], ops: ['<', '>'], motor?: true} … ] }
```
- Métricas: óleo BB/BE, arrefecimento BB/BE, rpm BB/BE (todas `motor: true`), banco de serviço 24 V, banco de partida 24 V, banco 12 V, profundidade, vento, SOG, pressão barométrica, temperatura da água do mar, diesel (L), água doce, cinzas e negras.
- **A regra é a `faixa` própria de cada métrica, não o `D.replay.limites`.** `faixa: [min, max]` é o intervalo aceito para o limite pedido (validação do "me avise se…"). Vento, SOG, pressão e temperatura da água não têm limite de alarme no guia e entram assim. Faixas: óleo 0,5–6,0 bar · arrefecimento 60–100 °C · rpm 500–2.600 · 24 V 22,0–30,0 V · 12 V 11,0–15,0 V · profundidade 1–50 m · vento 5–50 nós · SOG 1–30 nós · pressão 980–1.040 hPa · água do mar 10–32 °C · diesel 100–1.600 L · água doce, cinzas e negras 5–100 %. Asserção `IDS`: `metricas[].campos ⊂ D.campos` e `faixa[0] < faixa[1]`.
- **Nível só `aviso`**: o alarme pedido nunca vira crítico (§2.4). Nunca abre SOS nem C3, nunca fala, nunca grava no diário.
- `motor: true` só vale com rpm a partir de 1.000 (o regime de cruzeiro da faixa de óleo): sem isso, um limite dentro da faixa da lenta dispararia a cada 150 s.
- Uma abertura por id por volta. Grava só no Confirmar, com linhas novas (apagar = linha de anulação).

### 1.22 O quadro (`CapitaoReplay.em(ms)` → `CapitaoTelemetria.atual()` com `simulado: true`)

Plano, snake_case com a unidade no nome. Os nomes do JSON do coletor de hoje (`gerar_demo.py:505-518`) se mantêm. Exemplos conferidos em `quadro.py` e `emenda.py` (com `circuitos_dia` = 19) com `fixar('60')` = **12:01:00** e `fixar('105')` = **12:01:45**. Nesses instantes o barco está na última perna do circuito, chegando à base.

| Campo | un · casas | origem | 12:01:00 | 12:01:45 | Trava / nota |
|---|---|---|---|---|---|
| `timestamp_utc` | ISO Z | relógio | `…T15:01:00Z` | `…T15:01:45Z` | instante fixado ou agora |
| `lat`, `lon` | graus · 5 | rota (`distancia_mn × fator` mod 15,42, reta na perna) | perna Ilha das Cabras (volta) → Barra Sul | idem | **nunca** em texto, na rede nem na ficha |
| `cog_graus` | ° · 0 | rota, arco de guinada ≤ 3°/s (função de `s`, sem estado) | 248 | 248 | fora das chaves do §2.2 |
| `proa_graus` | ° · 0 | derivado: `cog − asin(c·sen(para − cog)/stw)` + ruído 0,4 | 249 | 249 | idem |
| `piloto_rumo` | ° · 0 | rota (rumo da perna, degrau no ponto) | 248 | 248 | o degrau nunca cai numa emenda, fora a virada em A |
| `leme_graus` | ° · 1 (BB −, BE +) | laço (base ±0,4) + rota (5 × taxa de guinada, até ±25) | 0,3 | 0,2 | — |
| `sog_nos` | nós · 1 | laço | 18,1 | 18,0 | mín. 4,9 no laço: E1 fica NAVEGANDO |
| `stw_nos` | nós · 1 | derivado: `sog − c·cos(cog − para)` (corrente 0,3 nó para 200°) | 17,9 | 17,8 | — |
| `profundidade_m` | m · 1 | rota (`prof_m` interpolada) + ruído 0,2 | 10,0 | 9,0 | ≥ calado + 4 m |
| `motor_bb_rpm` / `motor_be_rpm` | rpm · 0 (mil) | laço | 2.049 / 2.038 | 2.049 / 2.036 | mesmo texto em todas as superfícies |
| `motor_bb_oleo_bar` / `be` | bar · 1 | laço | 3,9 / 3,8 | 3,9 / 3,8 | **nunca** na resposta `oleo` (relato) nem nas chaves do §2.2 |
| `motor_bb_arref_c` / `be` | °C · 1 | laço | 82,0 / 82,1 | 81,9 / **89,6** | janela do AVISO 99–116 s |
| `motor_bb_carga_pct` / `be` | % · 0 | laço | 62 / 61 | 62 / 61 | ≤ 90 |
| `marcha` | 'avante' \| 'neutro' \| 'ré' | fixo | avante | avante | — |
| `consumo_lph` | L/h · 1 (dois motores) | laço, sem ruído | 68,0 | 68,0 | é o que se integra no diesel |
| `diesel_litros` | L · 0 (mil) | contador | 1.333 | 1.332 | piso 400 L |
| `diesel_bb_pct` / `diesel_be_pct` | % · 1 | derivado: `(L/2 ± 3)/800 × 100` | 83,7 / 82,9 | 83,6 / 82,9 | (bb + be) × 8 = litros ± 1 |
| `distancia_mn` | mn · 1 | contador (Σ SOG desde as 07:00) | 65,1 | 65,3 | — |
| `motor_bb_horimetro_h` / `be` | h · 1 (mil) | contador | 417,6 / 414,8 | idem | agenda (`calc.faltam`) |
| `gerador_ativo`, `gerador_kw`, `gerador_horimetro_h` | bool · kW 1 · h 1 (mil) | fixo · laço · contador | true · 6,4 · 1.241,4 | true · 6,2 · 1.241,4 | ≤ 8,1 kW |
| `seakeeper_ativo`, `seakeeper_volante_rpm`, `_pct` | bool · rpm 0 (mil) · % 0 | fixo · laço · laço | true · 8.426 · 100 | true · 8.416 · 100 | nunca `null` |
| `bateria_0_tensao_v` (serviço 24 V), `bateria_1_tensao_v` (partida 24 V), `bateria_2_tensao_v` (12 V) | V · 2 | laço | 27,79 · 27,95 · 13,69 | 27,80 · 27,97 · 13,69 | **3 séries** (F07/F33) |
| `tanque_agua_pct`, `tanque_cinzas_pct`, `tanque_negras_pct` | % · 1 | contador (taxa por hora desde a âncora) | 86,0 · 15,0 · 9,5 | idem | serrote diário, coerente com a d02 |
| `porao_bb_nivel` / `porao_be_nivel` | cm · 1 | laço | 1,1 / 0,9 | 1,2 / 0,9 | ≤ 5 cm; **nunca** na resposta ao relato de água |
| `bomba_porao_ciclos` | ciclos na última hora · 0 | fixo | 0 | 0 | não é contador |
| `ancora_estado` | 'recolhida' \| 'lançada' | fixo | recolhida | recolhida | — |
| `ondas_m` | m · 1 | laço | 0,8 | 0,8 | "a bordo agora"; **fora** do "seguro para sair" |
| `vento_verdadeiro_nos` / `_angulo` | nós · 1 / ° · 0 (de onde vem, norte verdadeiro) | laço | 11,3 / 059 | 9,8 / 054 | idem |
| `vento_aparente_nos` / `_angulo` | nós · 1 / ° · 0 (relativo à proa, −180…180, + BE) | derivado (soma vetorial com SOG/COG) | 7,2 / 13 (13° BE) | 8,8 / 15 | TWA da F33 = `angulo verdadeiro − proa`, sem campo |
| `pressao_barometrica_hpa` | hPa · 1 (mil) | laço | 1.017,1 | 1.017,1 | — |
| `temp_ar_externo_c` / `temp_agua_c` | °C · 1 | laço; **os dois** ficam presos na máx/mín de hoje da leitura salva `capitao.clima.v1`, só no `instante()` (abaixo) | 22,6 / 20,1 | idem | §2.5 |
| `temp_praca_maquinas_c` | °C · 0 | laço | 46 | 46 | ≤ 60 |
| `jogo_graus` / `caimento_graus` | ° · 1 | laço | 0,5 / 3,1 | 0,3 / 3,2 | A4/A5 (F08) |
| `gps_satelites` | int | fixo | 18 | 18 | sempre finito |
| `climatizacao_ativa`, `dessalinizador_ativo`, `radar_ativo`, `ais_alvos` | bool · int | fixo | true · false · true · 4 | idem | tiram SEM LEITURA das respostas de hoje |
| `estado` | 'Navegando' \| 'Fundeado' \| 'Atracado' | fixo | Navegando | Navegando | coerente com SOG ≥ 1 |
| `local` | texto sem dígito | rota (ponto nomeado mais perto + `caminho`) | "na saída da Barra Sul, chegando" (regra no §1.14) | idem | sem "simulada"/"de exemplo" |
| `destino`, `destino_mn` | texto · mn 1 | rota | Barra Sul (base) · 0,5 | Barra Sul (base) · 0,3 | troca em degrau na chegada, que nunca cai numa emenda (fora a virada em A) |
| `wp_proximo`, `wp_mn` | texto · mn 1 | rota | Barra Sul (saída do Rio Camboriú) · 0,5 | idem · 0,3 | o cérebro não reconstrói a rota |
| `eta` | 'HH:MM' local | rota: âncora + `s_destino / velocidade_media_nos`, pela distância **linearizada** | 12:03 | 12:03 | constante na ida (e na volta), sem pulo na emenda; fora do §2.2 |
| `alarmes[]` | `[{id, nivel, sistema, lado?, campo, valor, limite, desde}]` | janela | `[]` | `[{id: 'arref_be', nivel: 'aviso', sistema: 'motores', lado: 'be', campo: 'motor_be_arref_c', valor: 89.6, limite: 88, desde: '…T15:01:39Z'}]` | nunca abre SOS/C3, nunca fala, nunca grava; omitido no `snapshot.quadro` |
| `simulado` | bool | — (marca, **fora** do catálogo `D.campos`; só o `CapitaoTelemetria.atual()` a põe) | true | true | identificador; nunca mostrado nem enviado. A conferência do catálogo roda sobre o `em()`, que não a tem (§1.15) |

- `campo` em `alarmes[]` é acréscimo à lista do PROMPT: sem ele, a C3 não acha o limite nem a tendência. `lado` é omitido quando não se aplica.
- **Fora do quadro, de propósito:** `pessoasBordo`, `mmsi`, `registro`, indicativo e qualquer texto de protocolo. Nenhum tique, HUD, E2/B3 ou "segundo do quadro" carrega dado de socorro.
- **Trava do ar e da água** (§2.5 do PROMPT, trava inegociável: "com rede, o ar e a água do quadro ficam dentro da máx/mín do dia que o chip mostra"). Só Main, H2 e S1 carregam o `capitao-clima.js`, então a fonte do limite não pode ser o chip da tela:
  - a função única é `CapitaoAgora.trava(q)` (§1.23): em toda tela, sem rede e com try/catch, lê `localStorage 'capitao.clima.v1'` (`{em, dia, max, min, …}`, gravado pelo `capitao-clima.js`);
  - se `dia` = `relogio.hojeIso` e `min ≤ max`, prende `temp_ar_externo_c` **e** `temp_agua_c` em [min, max], em `q` e em `txt.ar`/`txt.agua`. Sem leitura de hoje, nada muda;
  - `em()` continua puro: a trava é do instante atual (`instante()` a chama) e da base da curva do histórico (§1.13), com o mesmo resultado. A1, E1, C3, HUD, A4/A5 e cérebro mostram o mesmo texto porque todos leem o `instante()`;
  - teste (Fase 4, `verificar.py`, e `replay.py`): com `{dia: <hoje>, max: 21, min: 15}` injetado no `localStorage`, `txt.ar` = "21,0 °C" e `txt.agua` = "20,1 °C"; com `{dia: <hoje>, max: 19, min: 15}`, `txt.ar` = "19,0 °C" e `txt.agua` = "19,0 °C"; iguais na A1 e na Main, e o último ponto das séries de ar e água é o valor preso.

Outros instantes conferidos:
- **07:00:00**: na base (s = 0, no meio da guinada da saída), 1.560 L (97,5 %), horímetros 412,6 / 409,8 / 1.236,4, tanques 92 / 8 / 5, destino Estaleirinho a 7,4 mn, próximo ponto Ilha das Cabras a 1,0 mn, ETA 07:36.
- **06:59:59**: chegando à base, 473,8 L (29,6 %), 311,5 mn, horímetros 436,6 / 433,8 / 1.260,4, tanques 63,2 / 41,6 / 26,6, folgas 13,4 h e 39,6 h, destino Barra Sul a 0,0 mn, ETA 07:00.
- **A virada em A (06:59:59 → 07:00:00)** é a única descontinuidade permitida. A posição e o COG são contínuos (o fator fecha 19 circuitos). O salto permitido é o dos contadores e tanques **e** o da rota que recomeça: `destino` (Barra Sul → Estaleirinho), `destino_mn` (0,0 → 7,4), `eta` (07:00 → 07:36), `wp_proximo`/`wp_mn` (Barra Sul 0,0 → Ilha das Cabras 1,0), `piloto_rumo` (248° → 050°) e `local`.

### 1.23 `CapitaoAgora` (rodapé gerado; global fora do `D`, que continua só dado)

O código fica em `ferramentas/demo/rodape.js` (não servido) e o `gera_js` o anexa sem mudança ao fim do `capitao-dados.js`. Roda em toda tela, no `cerebro.py`, no `chat_ia.py` e no `gerar_guia.py`, sem mexer em `<head>`, CORE nem teste. Envolto em try/catch: um erro nunca impede o SOS de montar. Sem lookbehind e sem `\w`.

| Membro | Contrato | Fase que usa |
|---|---|---|
| `fuso`, `off(ms)` | deslocamento pelo `Intl.DateTimeFormat(…).formatToParts`, com cache por hora e `hour % 24`; reserva de −180 min (sem horário de verão desde 2019) | 1 |
| `ancora(ms)` | 07:00 de hoje no fuso; antes das 07:00, a de ontem. **A mesma função para rebase e replay** | 1, 2 |
| `relogio` | `{ms, hoje, hojeIso, diaBordo, diaBordoIso, ancoraMs, off}`, refeito pelo rebase | 1, 4 |
| `prazoDe(dn)` | `{st, rot, tom}`: port do `status_prazo` (ATRASADA · N D / D-30 / D-60 / D-90 / EM DIA; `crit`, `warn`, `tele`, `accent`, `ok`) | 1, 3, 4 (F15) |
| `docDe(dn)` | `{st, tom}`: VENCIDO / VENCE EM N D (≤ 90) / EM DIA | 1, 4 |
| `rebase(ms, forca?)` | §4.1; idempotente; devolve `true` se mudou algo | 1, 2 (virada e `fixar`) |
| `fmt` | `{arred(x, c), nb(x, c), mil(x), grau3(x), hora(ms, comSeg), coord(lat, lon), campo(q, nome), texto(inst), resumo(inst, {semPosicao})}`. `coord` tem a guarda 59,995′ → grau seguinte e é só para tela. `campo` devolve `null` se o valor falta: o leitor mantém o seu `SD`/`SL` (o arquivo de dados não tem rótulo) | 2, 3, 4, 5 |
| `instante()` | §abaixo; nunca lança erro; **`null` em `/SOS-/`** | 2 (motor), 3 (cérebro congela 1×/pergunta), 4, 5 |
| `contagens()` | `{atrasadas, d30, d60, d90, emDia, docsVencidos, docsVencem90, pendencias, tarefasEquipe}`, somando agenda gerada, `capitao.executado.v1` e `capitao.tarefas.v1` (try/catch). `pendencias` = as do diário (geradas e do aparelho com `pend`) ainda abertas depois de aplicar as linhas `acao: 'resolve' \| 'reabre'` do `capitao.diario.v1` (vale a última por `alvo`, §1.25) | 3, 4 (A1, C1, H2, Main, G4) |
| `nivel(campo, q)` | `{nivel: 'normal' \| 'aviso' \| 'critico', limite?, regime?}` ou `null` (não avalia): a regra única do §3.3 sobre `D.replay.limites[campo]`, com as `casas` do `D.campos`. É a mesma em `alarmes()` do replay, `capitao-alertas`, cores, C3, F09, F11 e modo real; o gerador tem o port em Python (paridade, §6.5) | 1 (C8), 2, 3, 4 |
| `trava(q)` | prende `temp_ar_externo_c` e `temp_agua_c` na máx/mín de hoje (§1.22); devolve uma cópia rasa de `q` | 2, 4 |
| `assinatura` | `hoje` + `'\|'` + `diaBordo` do último rebase | 1, 2 |

**`instante()`** (guardado por segundo inteiro, ou pelo instante fixado):

```
{ ms, q,                                    // quadro plano (§1.22)
  fonte: 'replay' | 'coletor' | 'snapshot',
  fonteTxt: 'telemetria ao vivo · 12:01:00' | 'coletor NMEA · ao vivo 12:01:00' | 'coletor NMEA · leitura de 26/09 10:12',
  selo: {tom: 'ok', texto: 'AO VIVO · 12:01:00'} | {tom: 'warn', texto: 'ÚLTIMA LEITURA · 26/09 10:12'},   // F06
  hora: '12:01:00', hhmm: '12:01', seg: 60 (só replay), fase: {nome, ini, fim} (só replay),
  calc: { autonomia: {horas: 17.6, mn: 318, lenta: 194},
          faltam: {'motores-oleo': 32.4, 'gerador-revisao': 58.6},
          desdeAbast: {litros: 227, desde: 'dd/mm/aaaa', h: '07:00'},
          diesel_pct: 83.3 },
  tend: { motor_bb_rpm: 644, motor_be_rpm: 648, motor_bb_oleo_bar: 0.5, motor_be_oleo_bar: 0.5,   // Δ de 30 s: q(ms) − q(ms − 30 s)
          motor_bb_arref_c: 2.9, motor_be_arref_c: 2.8, sog_nos: 8.1, diesel_litros: -0.5 },      // só com o replay (ou um coletor que guarde 30 s)
  txt: { hora, sog, stw, rumo, proa, piloto, leme, prof, rpm, oleo, arref, carga, consumo, diesel, dieselLados, distancia,
         horimetros, gerador, seakeeper, b24, b12, tanques, porao, ancora, vento, ventoAp, ondas, pressao, ar, agua,
         praca, inclinacao, local, destino, wp, eta, alarmes, relativa, autonomia, desdeAbast, tend, resumo, resumoSemPosicao } }
```
- Ordem da fonte, **fora do SOS**: `CapitaoTelemetria.atual()` (proxy real recente; senão o replay com `simulado: true`) → `CapitaoReplay.em(agora)` (tela sem o `capitao-telemetria.js`) → `D.snapshot.quadro`.
- **Em `/SOS-/.test(location.pathname)`, `instante()` devolve `null` antes de qualquer leitura.** Sem essa guarda, o SOS entregaria a posição do snapshot ao diário: a S1 carrega o `capitao-brain.js` e a S2 o injeta, o SOS grava pelo `B.addDiario`, o cérebro da Fase 3 congela o instante em `answer`, `resumoAgora` e `addDiario`, e, sem replay nem telemetria na tela, a ordem acima cairia no `snapshot.quadro`, que tem `lat`/`lon` (§2.1 do PROMPT: "nunca `D.snapshot.gps`"). Com o instante nulo, `resumoAgora()` e `addDiario()` não anexam quadro (§1.3).
- `txt` é o **único** texto que Main, A1, E1, HUD, `answer('telemetria')` e `## Navegação agora` mostram (ex.: `rpm` "BB 2.049 · BE 2.038 rpm", `diesel` "1.333 L (83,3 %)", `sog` "18,1 nós").
- `resumo` ≤ 300 letras, sem coordenadas; `resumoSemPosicao` para as exceções da decisão (g); `relativa` = "a 0,5 mn da Barra Sul, chegando" em 12:01:00 (só com `D.simulacao`; regra no §1.14).
- **`tend`** (tendência dos últimos ~30 s; uma fórmula só para a C3, para o `## Navegação agora` da ficha e para a F11):
  - Δ = `q(ms) − q(ms − 30 000)`, com `q(ms − 30 000)` = `CapitaoReplay.em(ms − 30 000)` (função pura, O(1)), nos campos `motor_*_rpm`, `motor_*_oleo_bar`, `motor_*_arref_c`, `sog_nos` e `diesel_litros`;
  - arredondado com as `casas` do `D.campos`; o diesel vai com 1 casa, porque em 30 s o consumo fica abaixo de 1 L;
  - 12:01:00: rpm +644 / +648, óleo +0,5 / +0,5, arrefecimento +2,9 / +2,8, SOG +8,1, diesel −0,5. 12:01:45: rpm −4 / −8, óleo 0,0 / 0,0, arrefecimento 0,0 / +7,5, SOG 0,0, diesel −0,6;
  - `txt.tend` = "últimos 30 s: rpm BB +644 · BE +648 · óleo +0,5 / +0,5 bar · arrefecimento +2,9 / +2,8 °C · SOG +8,1 nós · diesel −0,5 L" (12:01:00);
  - **virada das 07:00:** quando `ms − 30 000 < ancora(ms)`, os contadores (`diesel_litros`) saem de `tend` e de `txt.tend`: a diferença atravessaria o abastecimento (cerca de +1.086 L) e apareceria na C3, no `## Navegação agora` e na F11. rpm, óleo, arrefecimento e SOG ficam, porque o laço é contínuo em A (a âncora é início de volta). Ex.: 07:00:10 → `tend` sem `diesel_litros` e `txt.tend` sem "diesel" (§6.5);
  - com o coletor real, só se ele guardar os últimos 30 s. No modo real sem histórico, `tend` e `txt.tend` são omitidos.

### 1.24 APIs das Fases 2–3 que este contrato fixa

- **`window.CapitaoReplay`** (Fase 2; global separado, **nunca** `window.CapitaoTelemetria`): `{DURACAO: 150, ativo(), agora(), t(ms?), em(ms), quadro(t?), contadores(ms?), contadoresEm(ms), alarmes(ms?), janela(id, ms?), fase(ms?), resumo(ms?), serie(campo, janela, ms?), porFaixa(), fixar(x), fixo()}`.
  - `em(ms)` é função pura do instante absoluto: laço + rota + contadores + alarmes. A tabela de 150 s e as somas acumuladas se calculam uma vez, na carga.
  - `janela(id, ms)` → `{ativo, desde, ate}` desta volta ou da anterior: o "NORMALIZADO às HH:MM" da C3.
  - `serie(campo, janela, ms)`: `janela` ∈ chaves de `historico.janelas` (`'150S'` inclusive, §1.13); `alarmes()` avalia pela `CapitaoAgora.nivel`.
  - `quadro(t)` = `em(início da volta atual + t·1000)`, na volta do instante fixado (ou de agora): contadores e rota vêm dessa volta. `quadro()` sem argumento = `em(agora())`. A paridade Python × JS (§6.5) usa `quadro(t)`, t = 0…149.
  - `fixar(x)`: número (`60`) ou string (`'60'`, `'60@K'`) fixa o instante absoluto = âncora + K voltas + x s (K = `voltas_fixo` sem o `@`). `fixar(null)` solta: limpa `capitao.replay.fixo`, chama `CapitaoAgora.rebase(Date.now())` e emite `'capitao-rebase'`. É o `fixar(seg|null)` do PROMPT, aceitando também a string.
  - `localStorage 'capitao.replay.fixo'` e `#replay=60` (try/catch) fixam o **instante absoluto** do mesmo jeito; `fixar` chama `CapitaoAgora.rebase(T)` e emite `'capitao-rebase'`.
  - `localStorage 'capitao.replay.sobre'` (JSON parcial mesclado ao quadro) só vale **com o instante fixado**: é o gancho de teste da troca NAVEGANDO → FUNDEADO da E1, e nunca age no uso normal.
  - Eventos: `'capitao-telemetria'` a cada 1 s (pausado com `document.hidden`; tique imediato na volta à frente); `'capitao-alerta'` `{fase: 'inicio' | 'nivel' | 'fim', alarme}`; `'capitao-rebase'` na virada das 07:00 ou da meia-noite.
  - Sai em `/SOS-/` e com `D.simulacao !== true` (lido a cada chamada). Falha → `quadro()`/`em()` devolvem `null`. Nunca devolve o `D.snapshot`. Nunca muta o `D.snapshot`.
- **`CapitaoTelemetria`**: `atual()` = proxy real se `ativa()` e recente; senão `CapitaoReplay.quadro()` com `simulado: true`. `fonte()` ∈ {`'coletor'`, `'replay'`, `null`}. `ativa()` continua querendo dizer "proxy real".
- **Cérebro (Fase 3)**: `B.instante()` congela `CapitaoAgora.instante()` uma vez por pergunta (no início de `answer`, `ficha`, `answerAttachment` e `resumoAgora`); `B.resumoAgora()` = `inst.txt.resumoSemPosicao`/`resumo`. Em `/SOS-/`, `B.instante()` = `null`, `B.resumoAgora()` = `protocolos.plotter`, e o `addDiario()` grava sem quadro.

### 1.25 Dados do aparelho (`localStorage`; nenhuma chave muda de nome)

| Chave | Forma | Trava |
|---|---|---|
| `capitao.diario.v1` | `{d, t, iso, sys, tone, who, src, sim?, ref?, pend?, acao?: 'corrige' \| 'anula' \| 'resolve' \| 'reabre', alvo?, foto?}` | só cresce; ✎/🗑 = linha nova (PARIDADE §6.2). **`alvo`**: o `iso` da linha (corrige, anula) ou a pendência (resolve, reabre): o id da linha gerada (`d03`, `d05`, `d07`) ou o `iso` de uma linha do aparelho com `pend`. **Desfazer** = linha nova que reverte (resolve ↔ reabre; corrige com o texto anterior). **Estado** = a última ação por `alvo` (uma conta para o texto, outra para a pendência); nada se apaga. O `addDiario` recusa `acao` sem `alvo` que exista (linha do aparelho pelo `iso`, ou pendência gerada pelo id) — teste do `cerebro.py` na Fase 3, com a frase de conclusão que fecha e as de futuro, dúvida e defeito que não fecham. **`sim`**: o `addDiario` carimba `sim: true` lendo `D.simulacao` na hora, **fora do SOS**. Em `/SOS-/` ele não lê a flag, e a linha do SOS (`src` começando por `web · SOS` ou `app · SOS`) nunca leva `sim`. Com `simulacao: false`, o selo "apresentação" e a saída da ficha valem para as linhas com `sim` e **nunca** para as do SOS (§1.3) |
| `capitao.executado.v1` | `{<id da tarefa>: {d, t, iso, h?, quem?, sim?}}` | os ids das 11 tarefas ficam; o `markExec` grava `sim: true` com `D.simulacao` |
| `capitao.docs.v1` (já existe) | `[{n, s, dd, st: 'A CONFERIR', cat, fonte, sim?}]` (envio em G1; o arquivo não sai do aparelho) | só cresce; o `addDoc` grava `sim: true` com `D.simulacao` |
| `capitao.abast.v1` (já existe) | `[{n, d, st: 'A CONFIRMAR', fonte, sim?}]` (foto da NF em G2) | só cresce; o `addAbast` grava `sim: true` com `D.simulacao` |
| `capitao.equipe.v1` (já existe) | `{fones, convites}` | telefones só no aparelho |
| `capitao.tickets.v1` (F14) | `{id: 't…', k, origem, texto, prop, alvo: {tipo, id}, estado, dec, res, iso, who, sim}` | nenhum ticket gerado; proposta de alarme: 1 por id por dia, só depois de um gesto |
| `capitao.tarefas.v1` (F15) | `{id: 'g…', n, vence: 'AAAA-MM-DD', quem, meses, sistema, obs?, origem, iso, who, sim}` | status por `CapitaoAgora.prazoDe` |
| `capitao.pecas.v1` (F22) | `{novas: [], movs: [{id, dq, iso, who, sim}]}` | a base gerada não se muta |
| `capitao.alarmes.v1` (F12) | linhas `{id: 'usr_<n>', campo, op, limite, iso, who, sim, acao?}` | só no Confirmar |
| `capitao.checklist.v1` (F09) | `{<tipo>: {m: {<item>: 1 \| 'n'}, em}}` | conveniência; CONCLUIR = 1 linha no diário |
| `capitao.prestadores.v1` (F21) | `{novos: [{id: 'r…', n, role, s, iso, who, sim}], fixos: {<id>: {n?, role?, oculto?}}}` | telefones continuam em `capitao.equipe.v1` |
| `capitao.replay.fixo` | `'60'` \| `'60@120'` | try/catch |
| `capitao.replay.sobre` | JSON parcial | só com o instante fixado (teste) |
| `sessionStorage capitao.alertas.anunciados` | `{<id>: true}` | anúncio da faixa 1× por id por sessão |
| `sessionStorage capitao.sos.v1` (já existe) | `{em, t}` | F04: grava só na ação (MAYDAY, MOB, ligar) |

**Cópia de dados (F25, `dados.html`, Fase 0b):**
- exporta e restaura **só somando** (linha que já existe, pelo `id` ou pelo `iso`, não duplica; nada é apagado) as chaves de registro: `capitao.diario.v1`, `capitao.executado.v1`, `capitao.docs.v1`, `capitao.abast.v1`, `capitao.tickets.v1`, `capitao.tarefas.v1`, `capitao.pecas.v1`, `capitao.alarmes.v1` e `capitao.prestadores.v1`;
- e as do aparelho que já existem: `capitao.equipe.v1` (telefones e convites, mesclados por chave), `capitao.checklist.v1`, `capitao.atalhos.v1`, `capitao.blocos.v1` e `capitao.tema.v1`;
- ficam **fora**: `capitao.replay.*` (restaurar um instante fixado congelaria o app), `capitao.ia.chave.v1`, `capitao.voz.chave.v1`, `capitao.telemetria.chave.v1`, `capitao.sessao.v1`, `capitao.login.tentativas.v1`, os endereços (`capitao.ia.url.v1`, `capitao.voz.url.v1`, `capitao.telemetria.url.v1`), os caches (`capitao.clima.v1`, `capitao.mare.v1`, `capitao.telemetria.ultima.v1`), os de estado (`capitao.ia.ativar`, `capitao.modo`, `capitao.lista`, `capitao.plataforma.v1`, `capitao.saudacao.v1`, `capitao.recarga.v1`) e todo o `sessionStorage`;
- restaurar não mexe no `sim` das linhas: a cópia diz o que cada linha era;
- regra por forma de chave: nas **listas** (diário, docs, abast, tickets, tarefas, `pecas.novas`/`.movs`, alarmes, `prestadores.novos`), união pelo `id` (ou pelo `iso`), sem duplicar; nos **mapas** (`capitao.executado.v1`, `capitao.prestadores.v1.fixos`, `capitao.equipe.v1.fones` e `.convites`, `capitao.checklist.v1`, `capitao.atalhos.v1`, `capitao.blocos.v1`) e nos valores soltos (`capitao.tema.v1`), **o valor do aparelho ganha** e só as chaves que faltam são acrescentadas. Nada é apagado nem sobrescrito. Teste (Fase 0b, `dados.html`): restaurar uma cópia com um telefone diferente para o mesmo papel mantém o do aparelho e acrescenta os papéis que faltavam.

---

## 2. Decisão (e): as escolhas e por quê

### 2.1 Barco: **Estaleiro Marévia · Marévia 40 HT** (2023)

- **Marca fictícia**, como o §1 do PROMPT diz ("a embarcação, a marca do barco e os dados são fictícios por construção"). Um barco real exigiria as dimensões publicadas e ligaria registro, casco e manutenção ao produto de uma empresa real.
- **Colisão:** nenhuma ocorrência de "Marévia"/"Marevia" como estaleiro, modelo ou empresa (busca de 22/10/2026); não é nome de pessoa nem de lugar; contagem 0 na pasta do Avanti e nas duas listas privadas.
- **HT (hard-top), não "Fly":** "flybridge" está na lista de lugares do LOCAL_SEGURANCA, e em barcos com flybridge é lá que costumam ficar balsa e EPIRB.
- **Dimensões:** comprimento 12,40 m (40,7 pés) · boca 3,95 m · calado 1,10 m (eixo e hélices) · deslocamento 10,4 t carregado · lotação 12 · pessoas a bordo 4 · tanques de diesel 2 × 800 L, água 400 L, cinzas 100 L, negras 100 L.
- **Revisão 2 do C4 (23/10/2026):** o deslocamento era 11,8 t, acima do que o Seakeeper 3 cobre (barcos de cerca de 10,5–12,5 m, ou 35–41 pés, e até cerca de 10,5 t na página do fabricante; cerca de 11 t pelo distribuidor). Com 10,4 t ele cobre as duas medidas (§8.2, item 9), e o barco fica no peso de um 40 pés de planeio com 2 × QSB6.7 (cerca de 8,3 t leve, mais cerca de 1,7 t de diesel e água cheios e o resto em gente e equipamento).
- Pela fórmula de Crouch (C de 150 a 165, casco de planeio): ~300 cv no eixo em cruzeiro sobre ~22.900 lb (10,4 t) dão de 17,2 a 18,9 nós (18 nós com C ≈ 157); 610 cv na máxima dão de 24,5 a 26,9 nós. 68 L/h a 18 nós fecha.

### 2.2 Motores: **Cummins QSB6.7 305** ×2 (troca o fabricante de hoje; pede ok, §8)

- O PROMPT fixa 2.050 rpm em cruzeiro a 18 nós com 68 L/h, e o modelo de 24 h pede ~43 L/h na média do laço (1.086 L/dia num tanque de 1.600 L).
- O QSB6.7 de 305 cv tem rotação nominal de 2.600 rpm e ~55,6 L/h por motor na nominal (folha do fabricante). 2.050 rpm = 79 % da rotação ≈ 50 % da potência pela lei do hélice ≈ 30–34 L/h por motor: os 68 L/h totais fecham, e a carga de cruzeiro fica em 62 %.
- **Por que sai a marca de hoje (Volvo Penta):** os diesel dela nessa faixa de potência giram até ~3.500 rpm. A 2.050 rpm, 18 nós e 68 L/h seriam incoerentes para quem conhece o motor ("denuncia o fictício").
- Custo: os textos com a marca antiga fixos no código (cérebro `motores`, C3, G4) mudam nas Fases 3 e 4. O `OLEO_PASSOS` deixa de citar marca **já na 1b** (vem de `protocolos.oleo`). O caso `('motores volvo penta', 'motores')` do `cerebro.py` continua roteando por "motores".

### 2.3 Registro: **`CIA-23-0417`**

- Formato `^[A-Z]{3}-\d{2}-\d{4}$` (asserção). "CIA" lembra Capitão IA sem dizer "fictício".
- Não imita nenhuma família de identificador:
  - inscrição da Autoridade Marítima (sequência numérica): 3 letras na frente a tiram desse formato;
  - placa de veículo: o formato antigo `AAA-0000`, o anterior a 1990 (2 letras + 4 dígitos) e o Mercosul `AAA0A00`. Aqui não há 4 dígitos logo depois das letras;
  - HIN (12 caracteres com código de fabricante), MMSI (`\b\d{9}\b`), telefone, CPF/CNPJ e HEX ID (15 hexadecimais): não casa nenhum (conferido em `textos3.py`).
- Igual ao `numero` do TIE. **Nunca em S1/S2.** Se o proprietário quiser só dígitos, o risco de colisão volta.

### 2.4 Lotação e pessoas a bordo

Lotação 12 (típica de 40 pés de esporte e recreio) e 4 pessoas a bordo (o número que o diário já usa). Nenhum dos dois vai para `salvatagem`, `sos`, roteiro, quadro ou HUD: a salvatagem diz "veja a placa de lotação" e "conte as pessoas a bordo agora".

### 2.5 Modelos dos equipamentos

Critério: os fabricantes informados pelo proprietário ficam (menos o dos motores, §2.2); modelo real e atual, do porte de 40 pés; **nenhum modelo das duas listas privadas**; e **contagem 0 por substring** na pasta do Avanti, sem distinguir maiúsculas, para cada parte do modelo e para a base dela (as duas primeiras palavras; fabricante + parte quando a parte tem menos de 4 caracteres ou não tem dígito, como `Lewmar V2` e `Raymarine Evolution`). É a asserção `COLISAO_MODELOS` (§6.3), que imprime só contagens.

**Correção da revisão 2:** a versão anterior dizia "contagem 0 para cada modelo escolhido", mas a conferência olhava só as listas privadas. Por substring, dois dos candidatos da versão anterior tinham ocorrências na pasta (49 e 1), e os dois foram trocados. Hoje dá 0 em todos, menos `Seakeeper 3` (1 ocorrência), que vai como exceção para o ok (§8.2): é exceção ao critério deste contrato, não à trava §2.10, porque o modelo é outro.

| Equipamento | Escolha | Por quê / trava |
|---|---|---|
| Gerador | Onan **QD 9** (9 kW, 60 Hz, 1.800 rpm) | fabricante informado; linha QD, de família diferente; 60 Hz como a rede do Brasil; o laço usa 5,6–6,4 kW (< 8,1 kW = 90 %) |
| Estabilizador | **Seakeeper 3** | fabricante informado; modelo escolhido pela contagem por substring na pasta (§2.5) e pelas listas privadas. **Nenhum número do fabricante** no guia, na `nominal` e no checklist: saem a rotação de operação e os minutos para estabilizar, porque os minutos repetiriam números do contexto do estabilizador na pasta do Avanti (conferido por contagem). Fica só a regra do guia e "o display indica quando está pronto". **Revisão 2 do C5:** a regra era "volante a partir de 60 %", que a folha pública desmente: o manual de operação do Seakeeper 3 dá a estabilização em 7.185 de 8.450 rpm, cerca de 85 % (o distribuidor dá cerca de 75 %). Passou a "cerca de 85 %" no guia (§2, §6 e §8), na `nominal` e no aviso da `LIMITES` (§3.3): número público, com "cerca de", e contagem 0 de "85 %" no contexto do estabilizador na pasta do Avanti (só contagem, como os 60 % antes); a rotação e os minutos continuam fora. Cobertura conferida na revisão 2 do C4: cerca de 10,5–12,5 m e até cerca de 10,5 t, com rotação nominal de 8.450 rpm; o deslocamento passou a 10,4 t (§2.1, §8.2). **Alimentação, conferida na revisão 3 do C4:** só 12 V DC, de um banco de 12 V de ciclo profundo (de cerca de 11 a 15 V na entrada, AGM recomendado), sem energia AC; mínimo de cerca de 200 Ah no banco, pela página do fabricante. Aqui é o banco `eletronica` de 12 V (2 × 230 Ah em paralelo, cerca de 460 Ah), que divide o banco com a eletrônica de 12 V (o fabricante recomenda o banco combinado), carregado pelo carregador no gerador ou no cais; as faixas do 12 V (§1.5 `g_eletrico §2`, 12,2 a 14,7 V) ficam dentro da entrada do estabilizador, e o laço (13,55 a 13,69 V, com o gerador ligado) também. O guia (§1, §2 e §6), o checklist e o cérebro falam do banco de 12 V, nunca de energia AC (§1.5) |
| Climatização | Webasto **FCF Platinum** 16000 + 2 × 12000 | o fabricante era nulo; linha autocontida comum em 40 pés |
| Plotters | Garmin **GPSMAP 1243xsv** ×2 | fabricante informado; família 12x3 |
| Áudio | Fusion **MS-UD755** (2 zonas) | fabricante informado; linha UD |
| VHF | Icom **IC-M510** (fixo, DSC) + **IC-M37** (portátil) | troca o modelo de hoje, que estava numa lista privada (PARIDADE §6) |
| EPIRB | Ocean Signal **SafeSea E100G** | categoria II com GPS. Modelo e validade só em Equipamentos, Leme e Documentos |
| Incêndio | Seafire **FD 300M** (automático com disparo manual) | linha FD; grafia "Seafire" sem hífen em todo dado (§8) |
| Dessalinizador | Schenker **Zen 30** (30 L/h) | — |
| Bombas de porão | Rule **Rule 2000** (24 V) ×2 | BB e BE, como os campos `porao_*`; "sensor de nível" |
| Âncora | Lewmar **V2** + contador **AA150** | o "sensor de âncora" é o contador de corrente |
| Piloto | Raymarine **Evolution** (EV-1 · ACU-400, bomba hidráulica) | eixo com direção hidráulica pede piloto hidráulico; o GHP 20 exige direção eletrônica, então o piloto é de outro fabricante que o dos plotters (pede ok, §8) |
| Radar | Garmin **GMR 24 xHD3** | domo de 24"; contagem 0 (o de 18" tinha 1 ocorrência) |
| AIS | em-trak **B954** (classe B) | o guia **não** cita o MMSI numérico |
| Baterias | Victron Energy **AGM Super Cycle 12 V 230 Ah** ×8 | 3 bancos: serviço 24 V (4), partida 24 V (2) e 12 V (2, em paralelo: estabilizador e eletrônica de 12 V) |

Mitigação de "especificação gerada para modelo real": só entram os números públicos citados, com "cerca de"; as faixas são **regra de bordo do guia**, mais conservadoras que os alarmes do próprio equipamento; nada de capacidade de óleo, torque, código de alarme ou página de manual. A leitura do volante no quadro (~8.420 rpm, §3.1) é leitura do laço, não ficha do fabricante: não aparece em guia, `nominal` nem checklist. Revisão 2 do C4: era ~10.350 rpm, acima da rotação nominal do Seakeeper 3 (8.450 rpm na folha do fabricante), o que denunciaria o fictício; com o ruído de 12 rpm, o laço fica entre 8.408 e 8.432 rpm, abaixo da nominal (contagem 0 de 8420 na pasta do Avanti). As faixas também não coincidem com as do guia do Avanti (conferido, sem citar os números).

### 2.6 Base e waypoints (só a rota simulada; **nunca no SOS**)

| # | id | nome (`perto`) | lat | lon | prof. (m) | perna seguinte |
|---|---|---|---|---|---|---|
| 0 | base | Barra Sul (saída do Rio Camboriú) · "na saída da Barra Sul" | −26,9985 | −48,6160 | 8 | 0,98 mn · 050° |
| 1 | cabras | Ilha das Cabras · "ao largo da Ilha das Cabras" | −26,9880 | −48,6020 | 12 | 2,40 mn · 117° |
| 2 | laranjeiras | Ponta das Laranjeiras · "ao largo da Ponta das Laranjeiras" | −27,0060 | −48,5620 | 16 | 1,70 mn · 148° |
| 3 | taquaras | Taquaras · "ao largo de Taquaras" | −27,0300 | −48,5450 | 19 | 2,30 mn · 173° |
| 4 | estaleirinho (destino) | Estaleirinho · "ao largo do Estaleirinho" | −27,0680 | −48,5400 | 21 | 1,48 mn · 021° |
| 5 | pinho | Praia do Pinho · "ao largo da Praia do Pinho" | −27,0450 | −48,5300 | 22 | 3,08 mn · 336° |
| 6 | laranjeiras_v | Laranjeiras · "ao largo de Laranjeiras" | −26,9980 | −48,5530 | 18 | 2,28 mn · 281° |
| 7 | cabras_v | Ilha das Cabras · "ao largo da Ilha das Cabras" | −26,9910 | −48,5950 | 13 | 1,21 mn · 248° → base |

- **Circuito** 15,42 mn (ida 7,37 mn), ~76 min a 12,21 nós de média de rota, ~30,3 voltas de 150 s. São 311,5 mn de SOG por dia → **19 circuitos** (primo com as 576 voltas do dia, §1.14) com `fator` 0,9407: às 06:59:59 o barco está na base, a virada das 07:00 não move a posição, e nenhuma chegada cai numa emenda de 150 s.
- **Guinadas:** 26° a 67° nos pontos intermediários, 152° no Estaleirinho e 162° na base. A 3°/s e 18 nós, o maior arco é 0,27 mn, menos de um terço da perna mais curta (0,98 mn): o gerador confere (perna > 2 × arco).
- **Critérios:** mar aberto da Interpraias, sem o canal do porto de Itajaí, sem área protegida e sem marina com nome; **volta por fora** (~1,5–2,5 km de terra); pontos longe da faixa de banhistas.
- **Portão manual antes do commit da rota:** conferir cada ponto e cada perna numa carta (OpenSeaMap ou plotter). O que ficar a menos de 0,4 mn de terra, ilha, parcel ou laje — atenção aos dois pontos da Ilha das Cabras — vai para o largo, mantendo o nome, e o gerador é rodado de novo: pernas, fator, velocidade de rota e os exemplos da §1.22 se recalculam sozinhos, e a `EMENDA_ROTA` (§6.3) roda de novo. Se uma chegada cair numa emenda, muda-se um pouco o circuito (um ponto mais ao largo), nunca a asserção. Nenhum teste automático pega a distância de terra.
- **Às 07:00** o barco está na base (`distancia_mn` = 0), o que bate com a d01. **Posição relativa** (só com `D.simulacao`): a partir desses pontos ou da `posicaoRef`.

### 2.7 MMSI e indicativo

O MMSI 710123456 fica (decisão e), **só** como `MMSI_NUM` e com o rótulo `protocolos.mmsiRotulo`, nos lugares do §2.2. Indicativo: **nunca gerado**; fica o texto `protocolos.indicativo`.

---

## 3. O laço de 150 s

### 3.1 Quadros-chave (cenário `aviso`; o segmento 145 → 150 usa o t = 0)

| t | fase | rpm BB/BE | SOG | L/h | óleo BB/BE | arref. BB/BE | carga BB/BE | 24 V serv./part. · 12 V | ger. kW | vento nós/de | caimento/jogo | praça |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | lenta | 700/695 | 5,0 | 6,2 | 2,80/2,70 | 78,0/78,0 | 10/9 | 27,30/27,40 · 13,55 | 6,0 | 10,5/058 | 0,8/0,0 | 41 |
| 5 | lenta | 700/695 | 5,0 | 6,2 | 2,80/2,70 | 78,0/78,0 | 10/9 | 27,30/27,40 · 13,55 | 6,2 | 10,7/059 | 0,8/0,4 | 41 |
| 10 | lenta | 705/700 | 5,0 | 6,3 | 2,80/2,70 | 78,0/78,0 | 10/9 | 27,30/27,40 · 13,55 | 6,3 | 11,0/060 | 0,8/0,6 | 41 |
| 15 | lenta | 700/695 | 5,0 | 6,2 | 2,80/2,70 | 78,0/78,0 | 10/9 | 27,30/27,40 · 13,55 | 6,3 | 11,2/060 | 0,8/0,6 | 41 |
| 20 | aceleração | 710/705 | 5,1 | 6,4 | 2,80/2,70 | 78,0/78,0 | 10/9 | 27,30/27,40 · 13,55 | 6,2 | 11,4/061 | 0,9/0,4 | 41 |
| 25 | aceleração | 1.100/1.090 | 7,6 | 14,0 | 3,13/3,03 | 78,0/78,0 | 25/24 | 27,45/27,56 · 13,59 | 6,0 | 11,5/061 | 2,6/0,0 | 41 |
| 30 | aceleração | 1.400/1.390 | 10,0 | 24,0 | 3,37/3,27 | 79,2/79,2 | 37/36 | 27,56/27,69 · 13,63 | 5,8 | 11,6/062 | 4,8/−0,4 | 41 |
| 35 | aceleração | 1.650/1.640 | 12,6 | 36,0 | 3,57/3,47 | 80,1/80,1 | 47/46 | 27,65/27,79 · 13,66 | 5,7 | 11,7/062 | 5,1/−0,6 | 42 |
| 40 | aceleração | 1.850/1.840 | 15,0 | 48,0 | 3,74/3,64 | 80,8/80,8 | 54/53 | 27,73/27,87 · 13,68 | 5,7 | 11,7/062 | 4,4/−0,6 | 44 |
| 45 | aceleração | 1.980/1.970 | 16,9 | 60,0 | 3,84/3,74 | 81,4/81,4 | 59/58 | 27,77/27,92 · 13,69 | 5,8 | 11,6/062 | 3,6/−0,4 | 45 |
| 50 | cruzeiro | 2.050/2.040 | 18,0 | 68,0 | 3,90/3,80 | 81,8/81,8 | 62/61 | 27,80/27,95 · 13,70 | 6,0 | 11,5/061 | 3,2/0,0 | 45 |
| 55–90 | cruzeiro | 2.050/2.040 | 18,0 | 68,0 | 3,90/3,80 | 82,0/82,0 | 62/61 | 27,80/27,95 · 13,70 | 5,7–6,3 | 9,8–11,4 / 056–061 | 3,2/±0,6 | 46 |
| 95 | cruzeiro | 2.050/2.040 | 18,0 | 68,0 | 3,90/3,80 | 82,0/**86,2** | 62/61 | 27,80/27,95 · 13,70 | 5,8 | 9,6/055 | 3,2/−0,4 | 46 |
| 100 | cruzeiro · AVISO BE | 2.050/2.040 | 18,0 | 68,0 | 3,90/3,80 | 82,0/**89,0** | 62/61 | 27,80/27,95 · 13,70 | 6,0 | 9,5/055 | 3,2/0,0 | 46 |
| 105 | cruzeiro · AVISO BE | 2.050/2.040 | 18,0 | 68,0 | 3,90/3,80 | 82,0/**89,6** | 62/61 | 27,80/27,95 · 13,70 | 6,2 | 9,4/054 | 3,2/0,4 | 46 |
| 110 | cruzeiro · AVISO BE | 2.050/2.040 | 18,0 | 68,0 | 3,90/3,80 | 82,0/**89,6** | 62/61 | 27,80/27,95 · 13,70 | 6,3 | 9,3/054 | 3,2/0,6 | 46 |
| 115 | cruzeiro · AVISO BE | 2.050/2.040 | 18,0 | 68,0 | 3,90/3,80 | 82,0/**89,0** | 62/61 | 27,80/27,95 · 13,70 | 6,3 | 9,3/054 | 3,2/0,6 | 46 |
| 120 | redução | 2.050/2.040 | 18,0 | 68,0 | 3,90/3,80 | 82,0/**85,8** | 62/61 | 27,80/27,95 · 13,70 | 6,2 | 9,4/054 | 3,2/0,4 | 46 |
| 125 | redução | 1.450/1.440 | 10,4 | 26,0 | 3,41/3,31 | 82,0/82,0 | 39/38 | 27,58/27,71 · 13,63 | 6,0 | 9,5/055 | 2,4/0,0 | 46 |
| 130 | redução | 950/945 | 6,6 | 10,5 | 3,00/2,90 | 80,2/80,2 | 20/19 | 27,39/27,50 · 13,58 | 5,8 | 9,6/055 | 1,2/−0,4 | 46 |
| 135 | lenta | 710/705 | 5,1 | 6,4 | 2,80/2,70 | 78,7/78,7 | 10/9 | 27,30/27,40 · 13,55 | 5,7 | 9,8/056 | 0,9/−0,6 | 44 |
| 140 | lenta | 705/700 | 5,0 | 6,3 | 2,80/2,70 | 78,0/78,0 | 10/9 | 27,30/27,40 · 13,55 | 5,7 | 10,0/056 | 0,8/−0,6 | 42 |
| 145 | lenta | 700/695 | 5,0 | 6,2 | 2,80/2,70 | 78,0/78,0 | 10/9 | 27,30/27,40 · 13,55 | 5,8 | 10,3/057 | 0,8/−0,4 | 41 |

Outros campos com chave: gerador 5,6–6,4 kW · volante 8.420 rpm, 100 % (abaixo da nominal do Seakeeper 3; revisão 2 do C4) · porão BB 1,2 e BE 0,9 cm · ondas 0,7 (abaixo de 10 nós) e 0,8 · pressão 1.017,1 hPa · ar 22,6 °C · água 20,1 °C · leme base ±0,4°.
Os campos que **não** estão nos quadros-chave (decisão j) saem da rota, dos contadores e do relógio: posição, COG, proa, piloto, `local`, `destino`, `eta`, profundidade, contadores e tanques.

### 3.2 Algoritmo (idêntico em Python e JS; paridade testada)

```
k = floor(t/5); f = (t − 5k)/5; a = chaves[c][k]; b = chaves[c][(k+1) % 30]
linear:  x = a + (b − a)·f                ângulo: x = a + (((b − a + 540) % 360) − 180)·f
x = x + amp_c · u(sem_c, t)               u(s, t) = h32(s·1000003 + t) / 4294967295 · 2 − 1     (ruído periódico em t)
x = floor(x·10^casas + 0,5) / 10^casas    ângulo: ((x % 360) + 360) % 360;   −0 → 0
h32: x ^= 0x9E3779B9; x ^= x>>>16; x = imul(x, 0x85EBCA6B); x ^= x>>>13; x = imul(x, 0xC2B2AE35); x ^= x>>>16   (>>> 0 a cada passo; Python: & 0xFFFFFFFF)
```
- `ruido` (amplitude, semente): rpm 6 · SOG 0,1 · consumo 0 · óleo 0,03 · arrefecimento 0,1 · carga 0,6 · gerador 0,1 · baterias 0,02 (12 V 0,01) · ondas 0,05 · vento 0,4 nó e 2° · pressão 0,05 · ar e água 0 · porão 0,1 · volante 12 rpm · jogo 0,3 · caimento 0,1 · praça 0,2 · leme 0,4; sementes 1100 + n, fixas no `ruido`.
- Sem `Math.sin` no cliente e sem o `round()` do Python (que arredonda pelo par): V8 e CPython dão os mesmos doubles.
- Ruído da rota (proa, profundidade) usa o segundo absoluto, porque a rota não é periódica em 150 s.
- **Contadores:** `valor = contadores_base + voltas·por_volta + soma_parcial[t]`, com somas acumuladas da tabela de 150 s (consumo por segundo + gerador; distância = Σ SOG/3600). Horímetros: base + (T − A)/3600. Tanques: base + taxa × (T − A)/3600. O(1) por tique.

### 3.3 Faixas e limites (`D.replay.limites`), com a fonte no guia gerado

Forma (fechada; uma chave por campo do quadro, **sem curinga**: `motor_bb_oleo_bar` e `motor_be_oleo_bar` são duas entradas):

```
limites: { <campo>: {
  un, fonte,
  normal?: {de?, ate?}, aviso?: {abaixo?, acima?}, critico?: {abaixo?, acima?},   // sem regimes
  regimes?: [ {rpm_campo, rpm_de?, rpm_ate?, normal, aviso?, critico?} … ],      // com regimes, o topo não tem normal/aviso/critico
  ativo_se?: {campo, acima: 0} | {campo, igual: true} } }
```

**Regra única** (`CapitaoAgora.nivel(campo, q)`, §1.23; escrita uma vez em JS no rodapé e uma vez em Python no gerador, que a usa em `JANELA` e `FIO`):
1. `L = limites[campo]`; sem `L` → `null`.
2. `ativo_se`: com `acima`, exige `arred(q[ativo_se.campo], casas) > acima`; com `igual`, exige `q[ativo_se.campo] === igual`. Se não (ou se o campo falta) → `null`: não avalia, sem cor e sem alarme.
3. `v = arred(q[campo], casas do campo)`; ausente ou não finito → `null`.
4. Sem `regimes`, `R = L`. Com `regimes`, `R` = o 1º regime `g` com `g.rpm_de ≤ r < g.rpm_ate` (o limite que falta fica aberto), sendo `r = arred(q[g.rpm_campo], 0)`; nenhum → `null`.
5. `critico` se `v < R.critico.abaixo` ou `v > R.critico.acima`; senão `aviso` se `v < R.aviso.abaixo` ou `v > R.aviso.acima`; senão `normal`. Comparações **estritas** sobre o valor arredondado; limite que falta não compara.
6. Devolve `{nivel, limite, regime}`: `limite` é o número cruzado (o `alarmes[].limite` do quadro) e `regime` o índice.

- **O normal termina exatamente no limite do aviso** (asserção `LIMITES_FORMA`: `normal.de = aviso.abaixo` e `normal.ate = aviso.acima` quando os dois existem, em cada regime): dentro do normal ⇔ sem alarme.
- `ativo_se`: `motor_bb_oleo_bar`, `motor_bb_arref_c` e `motor_bb_carga_pct` → `{campo: 'motor_bb_rpm', acima: 0}` (o BE com `motor_be_rpm`); `gerador_kw` → `{campo: 'gerador_ativo', igual: true}`; `seakeeper_volante_pct` → `{campo: 'seakeeper_ativo', igual: true}`.
- Exemplo, óleo BB: `regimes: [{rpm_campo: 'motor_bb_rpm', rpm_ate: 1000, normal: {de: 1.0, ate: 6.0}, aviso: {abaixo: 1.0, acima: 6.0}, critico: {abaixo: 0.6}}, {rpm_campo: 'motor_bb_rpm', rpm_de: 1000, normal: {de: 2.4, ate: 6.0}, aviso: {abaixo: 2.4, acima: 6.0}, critico: {abaixo: 1.4}}]`.
- **Paridade Python × JS** (C8 no gerador; Fase 2 no Edge): `nivel` campo a campo nos 150 quadros da volta e nos casos de borda de cada limite (valor = limite → `normal`; limite ± 1 unidade da última casa → o nível de fora; rpm 999 e 1.000 no óleo; rpm 0 → `null`), com o mesmo resultado nos dois.

Na tabela, uma linha pode cobrir as duas chaves de um par (BB e BE); no `D`, são entradas separadas.

| Campo | normal | aviso | crítico | Fonte |
|---|---|---|---|---|
| `motor_bb_oleo_bar`, `motor_be_oleo_bar` (`regimes` por `motor_bb_rpm` / `motor_be_rpm`) | abaixo de 1.000 rpm: 1,0–6,0 · a partir de 1.000 rpm: 2,4–6,0 | abaixo do normal ou acima de 6,0 | abaixo de 0,6 / de 1,4 | Guia de bordo — Motores Cummins §9 · Faixas de operação |
| `motor_bb_arref_c`, `motor_be_arref_c` | até 88 °C | acima de 88 | acima de 97 | idem |
| `motor_bb_rpm`, `motor_be_rpm` | até 2.600 | acima de 2.600 | — | idem |
| `motor_bb_carga_pct`, `motor_be_carga_pct` | até 90 % | acima de 90 | — | idem |
| `temp_praca_maquinas_c` | até 60 °C | acima de 60 | — | idem |
| `bateria_0_tensao_v`, `bateria_1_tensao_v` | 24,4–29,4 V | abaixo de 24,4 ou acima de 29,4 | abaixo de 23,6 | Guia de bordo — Sistema elétrico 24 V e 12 V §2 · Faixas |
| `bateria_2_tensao_v` | 12,2–14,7 V | abaixo de 12,2 ou acima de 14,7 | abaixo de 11,8 | idem |
| `porao_bb_nivel`, `porao_be_nivel` | até 5 cm | acima de 5 | acima de 10 | Guia de bordo — Bombas de porão Rule §2 · Faixas |
| `profundidade_m` | a partir de 3,0 m | abaixo de 3,0 | abaixo de 2,0 | Guia de bordo — Eletrônicos … §8 · Sonda |
| `diesel_litros` | a partir de 400 L | abaixo de 400 (25 %) | abaixo de 160 (reserva de 10 %) | Checklist de bordo § Abastecimento |
| `gerador_kw` | até 8,1 kW | acima de 8,1 (90 %) | — | Guia de bordo — Gerador Onan §9 · Potência e carga |
| `seakeeper_volante_pct` | a partir de 85 % | abaixo de 85 (sem estabilização; revisão 2 do C5, era 60) | — | Guia de bordo — Estabilizador Seakeeper §8 · Faixas |
| `tanque_agua_pct` | a partir de 15 % | abaixo de 15 | — | Checklist de bordo § Tanques |
| `tanque_cinzas_pct`, `tanque_negras_pct` | até 80 % | acima de 80 | — | idem |

- Os limites são do Capitão: não são as constantes de regra do Avanti nem os números do guia dele (conferido).
- O `oleo` (relato de queda) **nunca** mostra faixa nem leitura: só os passos e "confira o manômetro agora". A faixa fica no `oleoLeitura` (pergunta neutra). O `cerebro.py` confere que "alarme de óleo acendeu" e "tem água no porão" não contêm ` bar` nem `%` em t = 60 e t = 105.

### 3.4 Resultado medido (`laco.py`, ruído incluído)

- **Janela do AVISO** (`motor_be_arref_c` > 88,0 no valor mostrado): **99 a 116 s**, contínua, 18 s. Em 98 s, 87,9 °C (normal); em 99 s, 88,5 °C (AVISO); em 116 s, 88,4 °C; em 117 s, 87,7 °C (normal).
  - Máximo 89,7 °C, abaixo do crítico de 97. O BB nunca passa de 82,1 °C. `t = 60` fora, `t = 105` dentro.
  - Os quadros-chave 95 e 120 ficam abaixo do limite: as passagens caem dentro de 95–120, longe do quadro-chave.
- **Nenhum valor por segundo a menos de 0,05 de um limite** (sem fio de navalha no arredondamento).
- **Óleo:** 2,8–3,9 bar (BB) e 2,7–3,8 (BE), sempre dentro do regime do rpm do mesmo lado; o cenário `aviso` não toca no óleo.
- **Demais faixas:** baterias 27,28–27,82 · 27,38–27,97 · 13,54–13,71 V; gerador 5,6–6,4 kW; porão 0,8–1,3 cm; praça 41–46 °C; carga 9–63 %.
- **Emenda do laço:** nenhum campo do laço reprova `|v(149) − v(0)| ≤ maior passo de 1 s` (ângulo pelo arco menor). Como o laço é periódico, isso é o mesmo que comparar segundos consecutivos na emenda.
- **Emenda da rota e dos contadores** (`emenda2.py`, `circuitos_dia` = 19): a comparação é sempre entre **segundos consecutivos**, `em(N·150 − 1 s)` × `em(N·150)`, nunca `quadro(149)` × `quadro(0)` da mesma volta, que nos contadores difere de uma volta inteira de diesel e de distância. Nas 575 emendas do dia fora da âncora:
  - os contadores sobem só o passo de 1 s;
  - `destino_mn` e `wp_mn` (0,1), COG (1°), profundidade (0,4) e `piloto_rumo` (0) ficam dentro do maior passo de 1 s da volta;
  - `destino`, `wp_proximo` e a ETA não mudam.
- **Contadores:** por volta 1,8857 L (motores 1,7899 + gerador 0,0958) e 0,5408 mn (SOG médio 12,98 nós); por dia (576 voltas) 1.086,2 L e 311,5 mn. Diesel: 1.560 L (97,5 %) às 07:00 → 473,8 L (29,6 %) às 06:59:59. Acima da regra de 25 % (400 L) e da reserva (160 L): o piso nunca age, e o "seguro para sair" não ressalva o diesel nem de madrugada.

### 3.5 Cenário `alarme-critico` (só mudando a constante no gerador; decisão c: desligado)

- Óleo BB em 95/100/105/110/115/120: 3,0 · 1,2 · 1,1 · 1,1 · 1,2 · 3,0 bar, no regime de cruzeiro (aviso abaixo de 2,4, crítico abaixo de 1,4).
- Janelas derivadas do mesmo jeito, com o mesmo id `oleo_bb`: aviso → crítico → aviso, tudo dentro de 95–120. O AVISO do BE continua.
- Mesmo crítico, a faixa fica vermelha e nada mais: nunca abre SOS nem C3, nunca fala, nunca grava.

---

## 4. Rebase e modo real

### 4.1 Rebase (rodapé gerado; port do `status_prazo`)

```
(function () { try {
  var D = window.CapitaoDados, A = window.CapitaoAgora = { … };     // fuso, off, ancora, relogio, prazoDe, docDe, fmt, instante, contagens
  // instante(): if (/SOS-/.test(location.pathname)) return null;  — antes de ler qualquer fonte (§1.3, §1.23)
  // hoje no fuso: Intl.DateTimeFormat('en-CA', {timeZone, …}).formatToParts (cache por hora); sem Intl: −180 min fixo
  function rebase(ms, forca) {
    var hoje = dia(ms), bordo = dia(A.ancora(ms));
    if (!forca && A.assinatura === hoje + '|' + bordo) return false;           // idempotente
    // só campos derivados, a partir de deslocamentos que nunca reescreve:
    agenda, tarefasEquipe          → ultima, vence, dn, prazoDe(dn)            (base hoje); agenda ordenada NO LUGAR (sort do próprio array) por dn, id
    documentos                     → vence, dn, docDe(dn); emitido            (base hoje; a NF do dia de bordo: base dia de bordo)
    diario fixo (d03–d09)          → d, iso                                    (base hoje: o dia do alvo do ref, §1.0)
    d01, d02, abastecimentos, serie24v → d, iso                                (base dia de bordo)
    item SEM deslocamento (data absoluta: modo real, próxima embarcação) → só dn/st/rot/tom contra hoje
    item SEM data nenhuma (a nota fiscal) → vence, dn e st de prazo OMITIDOS (nunca null nem '')
    versao = hoje;  relogio = {…};  assinatura = hoje + '|' + bordo;
    // NUNCA toca D.snapshot, D.protocolos, D.embarcacao, D.replay, D.rota, D.historico, D.campos
    return true;
  }
  A.rebase = rebase; rebase(Date.now());
  // Dia de bordo: lido DEPOIS do resto do arquivo (microtarefa), para a injeção "simulacao = false" no fim do arquivo valer.
  Promise.resolve().then(function () { try {
    if (/SOS-/.test(location.pathname)) return;          // o SOS nunca lê a flag (§1.3); antes de qualquer leitura de D.simulacao
    if (D.simulacao === true) { insereDiaDeBordo(); rebase(Date.now(), true); } } catch (e) {} });
} catch (e) {} })();
```

- **Por que a microtarefa:** o teste do modo real acrescenta `window.CapitaoDados.simulacao = false;` ao fim do `capitao-dados.js`, depois do rodapé. A microtarefa roda logo depois do script inteiro e antes do próximo `<script>` (checkpoint do HTML). Assim as linhas do dia de bordo só entram se a flag ainda for `true`, e o teste testa de verdade.
- **`insereDiaDeBordo()`:** põe `ab-0…ab-2` em `abastecimentos`, `d01`, `d02` no topo do `diario` e a nota fiscal do dia de bordo (`diaDeBordo.documento`) em `documentos`, **por id** (rodar de novo substitui, nunca duplica), com `splice` no mesmo array (§1.0). Em `/SOS-/` não roda (sai antes de ler a flag). A d01 entra antes da d02, as duas às 07:00, com `iso` d01 = âncora + 1 s (§1.9). Não grava no `localStorage` nem cria linha no diário do aparelho: é dado gerado, não registro.
- **Virada com a página aberta** (07:00 ou meia-noite): o `capitao-replay.js` chama `CapitaoAgora.rebase(agora)` quando `ancora(agora)` ou o dia mudam, e emite `'capitao-rebase'`. O rebase e a `insereDiaDeBordo()` mexem nas mesmas listas, no lugar (§1.0): quem guardou `D.agenda` ou `D.diario` vê a virada sem recarregar. As linhas do dia de bordo têm `diasAtras` fixo: mudam de data, não de número.
- **`fixar(T)`** chama `rebase(T)`: entre 00:00 e 07:00, o instante congelado é "ontem 12:01" e os prazos acompanham.
- **Reserva:** o gerador grava os derivados contados da `REF` (26/09/2026). Se o rodapé falhar, as telas mostram as datas da `REF`. As linhas do dia de bordo não têm reserva (§1.0): sem o rodapé, a G2 cai no caminho vazio do modo real e o cérebro omite a linha dos abastecimentos (guarda do C8).
- **Testes** (C7): `Date` congelado num `add_init_script` em 06:59:59, 07:00:01 e 23:59 e com `Intl` removido → âncora de ontem/hoje, `dn` e `d` certos, 3 atrasadas; `rebase` 2× = 1×; `JSON.stringify(D.snapshot)` igual antes e depois; com `simulacao = false` acrescentado ao fim do arquivo, nenhuma linha do dia de bordo; `D.agenda`, `D.diario`, `D.documentos` e `D.abastecimentos` são o mesmo objeto (`===`) antes e depois do rebase; nenhum `null` nem `''` no `D` depois do rebase; em `/SOS-/`, `instante() === null`, nenhuma linha do dia de bordo e nenhuma leitura de `D.simulacao` (getter que conta); em 06:59:59 e 07:00:01, d06.`d` = `ultima` do `epirb-teste`, d09.`d` = `emitido` do laudo e d03.`d` = `vence` do `gerador-rotor` (dd/mm), e a d01 acima da d03 no diário.

### 4.2 Modo real (`simulacao: false`) continua com `null` → SEM DADOS

- **Cliente:**
  - nada do caminho `null → SD/SL` é apagado em cérebro e telas; `CapitaoAgora.fmt.campo` devolve `null` e o leitor decide o rótulo;
  - o replay sai em `/SOS-/` e com `simulacao !== true` (lido a cada chamada): não monta tabela, não dispara evento, `em()`/`quadro()` devolvem `null`, e o `atual()` não cai nele;
  - `instante()` = coletor real recente ou `D.snapshot.quadro` (que pode ter `null`), fora do SOS; em `/SOS-/`, `null` nos dois modos;
  - o rebase é guiado pelo dado nos dois modos: só recalcula o que tem deslocamento, e o que tem data absoluta ganha só o status;
  - as linhas do dia de bordo não entram (microtarefa).
- **Teste do modo real** (Fase 7): `simulacao = false` e `embarcacao.calado = null` injetados → replay parado; "qual o calado?" → SEM DADOS; ficha sem `## Navegação agora`; pedido à IA sem `modo`; histórico com resposta de posição sem coordenada. O `replay.py` pode também trocar o texto `"simulacao": true` → `false` no `page.route` (o gerador garante uma ocorrência só).
- **S1/S2:** idênticas nos dois modos (não leem a flag). É a propriedade de segurança mais importante do contrato.

### 4.3 O gerador na próxima embarcação (`SIMULACAO = False`)

O gerador **recusa** (asserção):
- emitir `replay` além de `limites` e `alertas`, `rota`, `historico` simulado ou `diaDeBordo` (e com ele a nota fiscal do abastecimento das 07:00);
- emitir valor do barco real sem `fonte`;
- enquanto o repositório for público: emitir `snapshot.gps`, `snapshot.quadro` com posição ou série com posição (é o "link público com a posição do barco" que o `CLAUDE.md` proíbe; volta só com o Cloudflare Access).

Nos dois modos, mesmo com o MMSI real: o roteiro continua com `MMSI_RADIO` e o indicativo continua sem campo.

**Docstring REGRAS do `gerar_demo.py`** (`:10-22`, reescrita no C1; hoje diz "Tudo aqui é FICTÍCIO e vai rotulado DEMO" e "None = SEM DADOS", o contrário da Decisão 1.1.0). As regras de privacidade (`:16-17`) e a de não copiar o Avanti ficam:

```
REGRAS (Decisão do proprietário 1.1.0 · modo simulação; ver o CLAUDE.md)
- SIMULACAO = True: dados completos da embarcação de apresentação, sem selo nem rótulo (DEMO, SEM DADOS, SEM LEITURA,
  MANUAL NO DRIVE, A CONFERIR/A CONFIRMAR). O rodapé gerado faz o rebase dos prazos e o capitao-replay.js lê D.replay.
  Nenhum texto gerado afirma nem nega que os dados são reais (a frase da sobreDados fica no cérebro).
- SIMULACAO = False (próxima embarcação): só dado com fonte; None = SEM DADOS. O gerador recusa replay além de limites
  e alertas, rota, histórico simulado e dia de bordo e, enquanto o repositório for público, a posição do barco.
- Nunca gerados: indicativo, HEX ID, telefone, lugar de equipamento de salvatagem.
- Nada copiado da Avanti Vessel (nomes, modelos, registro, MMSI, IDs, leituras, valores, textos).
- Sem valores em dinheiro, CPF/CNPJ, telefones, e-mails ou nomes de terceiros — nem na simulação (a mesma regra
  vale para o barco real que vier depois).
- Procedimentos de emergência: "procedimento padrão — confirmar com o protocolo de bordo" (decisão do proprietário).
```

---

## 5. Tamanhos estimados

Estimativa de `tamanho.py`, com blocos simulados do tamanho real e o serializador compacto:

| Arquivo | Hoje | 1.1.0 (estimado) | Orçamento (o gerador falha acima) | Carregado por |
|---|---|---|---|---|
| `capitao-dados.js` | 25,7 KB | **~105–122 KB** (dados ~94–110 KB + rodapé ~11–12 KB; ~30 KB com gzip, o que o Pages manda). A revisão 2 soma ~5 KB: `palavras` da agenda, `c` e `tipos` do checklist, `bloco` dos sensores, `limites` por lado, o `snapshot.quadro` completo e a `nivel`/`trava` no rodapé | **120 KB** | **todas** as telas, inclusive o SOS offline |
| `base-conhecimento.json` | 17,9 KB (46 trechos) | **~40–50 KB** (16 guias, 91 trechos) | 80 KB | cérebro (BM25) |
| `faq-equipamentos.json` (novo) | — | **~55–70 KB** (82 itens + 9 cartões EM + glossário) | 100 KB | F6, cérebro (F10); fora do SOS |
| `ferramentas/demo/fontes/**` | 14 arquivos | **25 arquivos** (15 guias e o inventário na 01; documentos; agenda; diário; leitura, série de 150 linhas e formato na 05; abastecimento; protocolo na 07; LEIA-ME) | — | Drive (o proprietário reenvia) |

Maiores blocos do `capitao-dados.js`: `replay` ~23 KB (chaves, limites por lado, alertas), `faq` legado ~13 KB, `checklists` ~10 KB, `historico` ~8 KB (desvios a cada 2 dias, com ar e água, e a tabela `sazonal`), `campos` ~8 KB, `agenda` ~9 KB (com `palavras`), `sensores` ~7 KB. A faixa de cima passa do orçamento: o `TAMANHO` decide no C9, e acima de 120 KB o passo (1) do plano B entra no próprio C9.

**Fontes do Drive com prazos relativos** (desde o C7). O app mostra datas recalculadas para hoje e cita esses arquivos como "Fonte:"; uma fonte estática com as datas da `REF` contaria outra história. Por isso:
- os CSV das pastas 02, 03, 04 e 06 não trazem data absoluta nem cabeçalho com data. Saem o "Situação em 26/09/2026" e o "Prazo em 26/09/2026" (`gerar_demo.py:492`, `:495`) e as datas da reserva;
- colunas: "Emitido há (dias)" e "Vence em (dias, contados de hoje no app)" (02); "Última (há N dias)", "Vence em (dias; negativo = atrasada)" e o limite de horas (03); "Dia de bordo (0 = hoje; o dia de bordo começa às 07:00)" e a hora (04 e 06; as linhas do dia de bordo entram com 0, 1 e 2);
- sem coluna de situação: quem calcula é o app;
- o LEIA-ME explica numa linha: "Datas relativas: o app conta os prazos a partir de hoje e o diário a partir do dia de bordo, que começa às 07:00.";
- a leitura da pasta 05 fica com a data dela (26/09 10:12) até a Fase 3, que a troca pelo início do dia de bordo (§1.17);
- asserção `FONTES_RELATIVAS` (§6.3). O proprietário reenvia as pastas ao Drive depois do C12.

**Plano B mecânico** (se passar de 120 KB), nesta ordem, cada passo um commit: (1) `historico` para `capitao-historico.js` (`window.CapitaoDados.historico = …`), carregado só por A1, A2, G2, `relatorio.html` e, sob demanda, pelo cérebro; (2) `checklists` e `sensores` para `capitao-dados-funcoes.js`, carregado por C4 ×2, A4/A5 e o cérebro. O caminho `D.<bloco>` não muda; o arquivo novo entra no CORE e ganha conferência offline. O SOS nunca carrega nenhum dos dois.

---

## 6. Plano de implementação da Fase 1

### 6.1 Regras gerais

- Antes de **cada** commit: `git grep -n -i -F -f "$TEMP/paridade-avanti/valores.txt"` = 0. Depois do C5 (e de S1/S2 a partir da 1b): `git grep -n -i -F -f "$TEMP/paridade-avanti/modelos-avanti.txt"` = 0.
- Depois de cada commit do gerador: rodar o gerador de novo e conferir `git status --porcelain -- capitao-dados.js base-conhecimento.json faq-equipamentos.json ferramentas/demo/fontes` vazio.
- Suíte de cada commit: `cerebro.py` + `chat_ia.py` (em segundo plano) + `verificar.py` das telas tocadas, com `--offline`.
- **Asserções citadas pelo texto.** Os números de linha da tabela da Fase 7 são os da 1.0.9 e já andaram com a Fase 0b. Este contrato cita a asserção pelo texto e põe a linha de hoje entre parênteses: no `cerebro.py`, «ficha com rótulo DEMO e SEM DADOS» (`:101` da tabela; hoje `:112`) e «ficha entre 3.000 e 10.000 letras (o proxy aceita 12.000)» (`:102`; hoje `:113`); no `chat_ia.py`, «trecho do guia leva a ficha COMPLETA…», com o `'DEMO' in f` (`:210`; hoje `:212`), o `FONTE_IA` (`:30`; hoje `:31`), a fonte do Worker simulado (`:152`; hoje `:154`), «resposta da IA na tela, com a fonte dela…» (`:205`; hoje `:207`) e a do «≈ 11,2 h» (`:254`; hoje `:256`).
- Asserção quebrada muda **no mesmo commit**, com comentário de motivo. As únicas quebras da Fase 1 são as da tabela da Fase 7: a «ficha com rótulo DEMO e SEM DADOS» do `cerebro.py`; no `chat_ia.py`, o `'DEMO' in f` do «trecho do guia leva a ficha COMPLETA…», o `FONTE_IA`, a fonte do Worker simulado e a «resposta da IA na tela, com a fonte dela…»; e o `verificar.py` do login (k). Qualquer outra é regressão.
- **Ficha até a Fase 3:** ≤ 9.800 letras (margem sobre o teto de 10.000 da asserção «ficha entre 3.000 e 10.000 letras»). **Medida de hoje** (22/10, depois da F13, `revisao2-scripts/mede.py`, só leitura): **9.319** (Agora 397 · Sobre o app 1.518 · Embarcação 291 · Equipamentos 601 · Telemetria 790 · Manutenção 850 · Horímetros 431 · Autonomia e consumo 793 · Documentos 488 · Pendências 453 · Diário de bordo 769 · Equipe e contatos 349 · Clima e maré 414 · Guias de bordo 538 · Emergência 609). Estimativa por commit:

  | Commit | Variação | Ficha |
  |---|---|---|
  | C1 | −315 (selo e "(DEMO)" das respostas) | ≈ 9.000 |
  | C2 | ≈ −100 (títulos e fontes sem "(DEMO)") | ≈ 8.900 |
  | C5 | +477 (16 equipamentos com fabricante e modelo) | ≈ 9.380 |
  | C7 | −110 ("Falta registrar" sai; `equip` e `quem` novos) +80 (documentos) +132 (prestadores) | ≈ 9.480 |
  | C8 | +49 (3 abastecimentos) +60 (d01 e d02 no `## Diário de bordo`) | ≈ 9.590 |
  | 1b | ≈ +100 (a `nota` do EPIRB e do Seafire, no lugar de fabricante, modelo e data, é mais longa) | **≈ 9.700** |

  Faixa de 9.600 a 9.800: ~100 de margem até 9.800 e ~300 até o teto. **Medir em todo commit, desde o C1.** Se passar de 9.800, cortar nesta ordem, no mesmo commit: (1) o `para` dos prestadores (≈ −60); (2) o `local` dos abastecimentos, "posto da marina" (≈ −25); (3) o texto da d01 (≈ −40); (4) a `nota` dos documentos (≈ −50). Nunca mexer na asserção antes da Fase 3.

### 6.2 Commits, nesta ordem

| # | Commit | O que muda | Teste / conferência | Asserções que quebram |
|---|---|---|---|---|
| **P0** | `CLAUDE.md: decisão do proprietário 1.1.0` | só o `CLAUDE.md`: a seção da §6.7 logo abaixo do título e "(substituído pela Decisão 1.1.0)" no fim das linhas do MAPA §9 (confirmar com grep) | grep dos valores = 0 | nenhuma |
| **C1** | `Flags 1.1.0, convidado (k) e selos` | gerador: `simulacao: True`, `demo: False`, sem `selo`/`aviso`, cabeçalho do `gera_js` neutro · `capitao-auth.js`: rodapé sem selo (:224-229); `demo: {nome: 'Convidado', papel: 'convidado', convidado: true}` (sal e hash intactos); `publico()` expõe o id; normalização exportada, com o apelido `convidado` → `demo` · `login.html`: `data-u` = id, texto = nome; sai o :107 · `index.html:78` sai · guardas de 1 linha em `Main.dc.html:420` e `H2-Home-Mobile.dc.html:405`: com `demo: false` o selo mostra `ÚLTIMA LEITURA · 26/09 10:12` (nunca "SNAPSHOT" nem um selo vazio) · `S1-SOS-Web.dc.html`: sai o selo `{{demo}}` do cabeçalho (`:48` e o `demo:` da `:173`), que com `demo: false` viraria uma caixa vazia no SOS (o resto da S1 fica para a 1b) · `gerar_demo.py:10-22`: a docstring REGRAS reescrita com a Decisão 1.1.0 (texto no §4.3) | `verificar.py login Main H2-Home-Mobile G4-Equipe-Web G4-Equipe-Mobile --offline`: o botão põe "demo"; "demo", "Demo", " DEMO ", "Convidado" e o valor do botão dão o mesmo id, **sem senha** (`deriveBits` simulado no init script); a trava de 5 tentativas não sobe ao digitar "Convidado"; nenhum selo; `verificar.py S1-SOS-Web --offline` sem a caixa do selo; **medir a ficha** (≈ 9.000) | `verificar.py` do login (k). A «ficha com rótulo DEMO e SEM DADOS» do `cerebro.py` e o `'DEMO' in f` do «trecho do guia leva a ficha COMPLETA…» do `chat_ia.py` ainda passam (os títulos têm "(DEMO)" até o C2) |
| **C2** | `Gerador: rótulos fora dos títulos e das fontes` | `ARQ` sem "(DEMO)"; `DRIVE`/fontes sem DEMO; `drive.arquivos` (§1.5); `aviso` da base; LEIA-ME sem a regra antiga, sem "fictício" e sem IDs; `embarcacao.fonte`; `REGRA_ABAST`; `canal16.fonte` | `cerebro.py` e `chat_ia.py`; medir a ficha | `cerebro.py` «ficha com rótulo DEMO e SEM DADOS» → `'DEMO' not in f` (a exigência de SEM DADOS sai com o comentário "volta invertida na Fase 3"); `chat_ia.py` «trecho do guia leva a ficha COMPLETA…» → `'DEMO' not in f` (o "26°59" fica); o `FONTE_IA`, a fonte do Worker simulado e a «resposta da IA na tela, com a fonte dela…» (`FONTE_IA` = "Guia de bordo — Gerador Onan · 2 · Ligar · via IA…"). As linhas de hoje estão no §6.1 |
| **C3** | `Gerador: --saida, determinismo e confere()` | `--saida <pasta>` (padrão: a raiz); apaga em `<saida>/ferramentas/demo/fontes/` só o que não gera mais (realpath dentro da pasta, sem seguir link); `git rm` dos antigos; serializador compacto; nenhuma data do sistema; `testes/proibidos.json` e `proibidos-casos.json` copiados do `termos.json`; `confere()` com as asserções da §6.3 (as estruturais falham; a varredura de termos fica **em modo relatório** até o C12); leitura opcional das listas privadas por `CAPITAO_LISTAS_PRIVADAS`, imprimindo só contagens | gerador com `--saida "$TEMP/g1"` = árvore byte a byte (diff só de formato neste commit); `confere()` falha numa amostra plantada de cada regra | nenhuma |
| **C4** | `Gerador: embarcação, registro e dimensões` | §1.2 (o `mmsiNota` fica até a 1b) · `S1-SOS-Web.dc.html`: sai o `REG. {{reg}}` (`:50` e o `reg:` da `:173`), porque este commit preenche `embarcacao.registro` e a trava §2.1 tira o registro do SOS (2 linhas; o resto da S1 fica para a 1b) | asserções do registro e de `lotacao ≥ pessoasBordo`; "qual o calado do barco?" continua `fallback`; `verificar.py S1-SOS-Web --offline` sem `CIA-23-0417` nem "REG." no `innerText`; medir a ficha | nenhuma |
| **C5** | `Gerador: equipamentos, modelos e guias; troca do VHF do Avanti` | 16 equipamentos (§1.4) com `palavras`, `nominal`, `seguranca`; `equipNota` neutra; 16 guias com `LIMITES` única; trechos com `seguranca`; `g_eletronicos §5` e `g_ais §2` com `MMSI_RADIO`; os §8 sem números; `D.faq.*.modelo`; os literais do VHF antigo em `Main.dc.html`, `H2-Home-Mobile.dc.html`, `capitao-brain.js`, `README.md`, `Manual-Capitao-IA.dc.html` e `integracoes/google-drive/README.md` (S1/S2 na 1b); `equipamentos[epirb\|seafire].nota` = `NOTA_ETIQUETA`; guardas de 1 linha em `F1-FAQ-Hub-Web.dc.html:186`, `F1-FAQ-Hub.dc.html:166` e `E2-Navegando-Sintoma.dc.html:169` (equipamento com `seguranca` mostra `nota` no lugar de fabricante e modelo, §1.4), e nas F1 também nos links do chat (`:206`/`:210` web, `:186`/`:190` app) e no link direto do VHF e do áudio pelas `palavras` (`:196`/`:176`); trechos de `g_seafire`/`g_epirb` com o rótulo do §1.5; `SEGURANCA_PALAVRAS` marcando trechos e itens (§1.5); `COLISAO_MODELOS` (§6.3) | `cerebro.py`: os `base` (`:27`/`:30`/`:34`/`:93`: "como ligar o gerador?", "alarme de fluxo da climatização", "parear bluetooth no fusion", "troca do rotor do gerador", "Quando foi a última troca de óleo do motor?") continuam `base`; "qual o calado do barco?", "qual o preço do dólar?", "quem ganhou o jogo ontem" e "como se faz um nó lais de guia?" continuam `fallback`; PEDE_IA igual; teste `limites[c].fonte` ⇔ texto do §n; para "como ligar o gerador?", o 1º trecho de `buscaBase` é o `g_gerador §2`, e o `chat_ia.py` `:211`, `:229`, `:234`, `:236` e `:385` fica verde; `verificar.py F1-FAQ-Hub F1-FAQ-Hub-Web E2-Navegando-Sintoma` sem modelo de EPIRB nem de Seafire no `innerText` e nos `href` de chat, com o VHF e o áudio abrindo a pergunta certa; `COLISAO_MODELOS` = 0 com `CAPITAO_AVANTI`, fora a exceção do §8.2; **medir a ficha** | nenhuma. Se um `base` mudar de chave, é regressão: ajustar o texto do guia, não o teste |
| **C6** | `Gerador: protocolos` | `D.protocolos` completo (§1.3); `seafire`/`epirb` deixam de ser `null`, com `nota` = `NOTA_ETIQUETA` (a mesma do C5); roteiro com `MMSI_RADIO` e "PESSOAS A BORDO: conte agora"; `mob` sem marca | asserções da §1.3; `publicacao.py`: o SOS offline continua com CANAL 16 / MAYDAY. S1/S2 ainda leem `P.roteiro` (o "último fix" colado sai na 1b) | nenhuma |
| **C7** | `Gerador: prazos relativos, rodapé e CapitaoAgora` | deslocamentos (§1.7–§1.9) com reserva da `REF`, com o diário fixo na base hoje (§1.0); `ferramentas/demo/rodape.js` (§1.23, §4.1, com a microtarefa já pronta); agenda (14), documentos (8, o TIE com `id: 'tie'` e `numero` = `embarcacao.registro`; **sai a linha `REGISTRO` da PENDENTES** do `confere.py`), diário fixo (§1.9), `tarefasEquipe`, `equipe.apoio` (§1.11); `AGENDA_FALTA` sai + as 4 guardas do §1.7 (`capitao-brain.js:270`, `B1-Carta-Web.dc.html:320`, `C1-Leme-Web.dc.html:213`, `C2-Leme-Mobile.dc.html:136`); `agenda[].seguranca`; `D.versao` com guarda de 1 linha em `C1-Leme-Web.dc.html:214`, `C2-Leme-Mobile.dc.html:137` e `B1-Carta-Web.dc.html:317` (`D.versao \|\| (S.quando ? S.quando.slice(0, 10) : SD)`, como a G1:237), porque elas escrevem "prazos contados a partir de" com a data do snapshot; `rodape.js` já com a guarda `/SOS-/` do `instante()` e da microtarefa (antes de ler `D.simulacao`), a `trava` (§1.23) e o rebase sem `null` e no lugar (§1.0); `gera_fontes` das pastas 02, 03, 04 e 06 com prazos relativos (§5). **Transição:** as duas linhas antigas de abastecimento, a do diário de 620 L e a saída das 08:20 viram deslocamentos e ficam até o C8 (a nota fiscal aponta para a de 620 L); sai só a "Fundeado…" | testes do §4.1 (Playwright, `Date` congelado, `Intl` removido, idempotência, snapshot igual, injeção do modo real, os pares por `ref` em 06:59:59 e 07:00:01, a microtarefa que não lê a flag em `/SOS-/`); `AGENDA` com `DIAS_MESES` e as `palavras`; 3 atrasadas; `diasAtras 0 ⇒ h ≤ 07:00`; `verificar.py A1-Ponte-Web B1-Carta-Web C1-Leme-Web C2-Leme-Mobile G1-Documentos-Web G3-Diario-Web G4-Equipe-Web`, com "prazos contados a partir de" = a data de hoje em C1, C2, B1 e G1 e sem "Falta registrar: .", "FALTA REGISTRAR · nada" nem "falta registrar: nada"; listas do `D` iguais por referência (`===`) antes e depois do rebase; `FONTES_RELATIVAS`; medir a ficha | nenhuma |
| **C8** | `Gerador: rota, replay, campos, alertas, dia de bordo e snapshot sem null` | `D.rota` (**portão manual: pontos e pernas na carta**; `circuitos_dia` 19), `D.destinos`, `D.campos`, `D.replay` (§1.16, com `janelas` derivadas e `diaDeBordo`); no mesmo commit, saem as linhas de transição do C7 e `abastecimentos` passa a `[]` (a microtarefa insere `ab-0…ab-2`, `d01`, `d02` e a nota fiscal do dia de bordo, que sai de `documentos` e vai para `diaDeBordo.documento` com `ref: 'ab-0'`); guarda de 1 linha no `consumo` do cérebro (`capitao-brain.js:286`) para a lista vazia (§1.10); `CapitaoAgora.nivel` no rodapé e o port dela em Python (§3.3), com `limites` por lado; `D.campos` com `sentido` e sem `simulado`; `consumo.faixas`/`maxima`/`gerador_lph`; `snapshot` (L) sem `null` + `snapshot.quadro` (os valores do §1.17, sem `alarmes`) + as guardas de B2:158, F3-Web:222 e F3:216; pasta 05: `Série do coletor NMEA — 150 s.csv` (`t_s` 0–149 + campos do laço, sem data e sem lat/lon), `Formato do quadro do coletor.csv` e a leitura renomeada (sem `_aviso`) | asserções do laço e da rota (§6.3), com `EMENDA_ROTA` e `DIA_DE_BORDO` (abastecimento às 07:00, no salto do contador); `verificar.py B2-Carta-Mobile F3-FAQ-Eletronicos F3-FAQ-Eletronicos-Web A1-Ponte-Web E1-Navegando-Gatilhos G2-Abastecimento-Web` (sem `[object Object]`; G2 com as 3 linhas); paridade da `nivel` (§3.3) e `LIMITES_FORMA`; `IDS` dos `ref` do dia de bordo; com `simulacao = false` injetado, nenhuma nota fiscal do abastecimento e o `consumo` sem "Abastecimentos registrados: ."; medir a ficha | nenhuma: o «≈ 11,2 h» do `chat_ia.py` continua (`autonomia` e `snapshot.diesel` são L) |
| **C9** | `Gerador: histórico` | `D.historico` (§1.13, com `temperaturas`: ar, água e a tabela `sazonal`; a janela `'150S'` e os grupos `so150`) e `serie24v` (L) | sem NaN; nenhum valor de histórico cruza limite (praça ≤ 60 − 0,05); último ponto = quadro; `TAMANHO` (acima de 120 KB, o passo 1 do plano B do §5 entra neste commit) | nenhuma |
| **C10** | `Paridade Avanti 1.24.0: dados de checklists, sensores, peças e alarmes pedidos (F08, F09, F12, F22)` | §1.18–§1.21 (`tipos` e `c` do checklist; s04 parcial; s09 sem minutos; s12 sobre `agenda[].seguranca`; sensores com a estação meteorológica, o `proa_graus`, `perfil`/`planta` e o `bloco` por regra; `faixa` própria em cada alarme pedido) | asserções de ids (`faq`, `tarefas`, `campos` com a cobertura da F08 e da F33, `faixa`, `bloco`, `c` e `tipos`), nenhum ponto/peça de salvatagem, nenhum item que case `emergencia()`/`oleo()`, nível só aviso; a tabela de estados do §1.18 vira teste na Fase 3 (`cerebro.py`) e na Fase 4 (C4); medir a ficha | nenhuma |
| **C11** | `Paridade Avanti 1.24.0: faq-equipamentos.json (F10)` | §1.6 (sem `conf`, `edicao` nem anexos; SF/EP sem modelo e com o rótulo; fora do `CORE` até a Fase 3) | ids únicos; `total`; nenhum `fontes[].tipo` "Manual"; vazios omitidos; nenhum `conf`; EM, SF, EP e CK-03 com `seguranca`; `ROTULO_SEGURANCA` | nenhuma |
| **C12** | `Gerador: fontes do Drive, varredura obrigatória e PARIDADE` | fontes sem DEMO; a varredura de termos passa a **reprovar** o gerador, com uma exceção só: `embarcacao.mmsiNota` (sai na 1b); lista da §8 e Andamento na PARIDADE.md | determinismo (2 rodadas = 0 diferença); grep final do §3 em `fontes/**` limpo; suíte da fase. **Sem push**: a Fase 1 vai para o remoto junto com a 1b (§6.6) | — |
| **1b** | `SOS fora da simulação (Fase 1b)` | sai o `mmsiNota` (e a exceção do C12); S1/S2: sem telemetria no helmet, `pos()` = GPS do aparelho, `MMSI_RADIO`, roteiro sem "último fix", Seafire/EPIRB de `D.protocolos`, sem faixa/`local` (o selo saiu no C1 e o REG no C4), fonte só `protocolos.fonte`, literais do VHF antigo, F04 · F3 web e app: a linha do MMSI com `protocolos.mmsiRotulo` e a nota `mmsiRadio` (§1.2) · cérebro (só emergência): `SOS_PASSOS`, `sos`, `canal16` (com `protocolos.indicativo`), `epirb`, `seafire`, `OLEO_PASSOS` = `protocolos.oleo`, lista `SOS` ampliada, `salvatagem` = `protocolos.salvatagem`, `pedeIA` false com trecho `seguranca` (já na revisão do C5, com o `supressao` na rota `seafire`), "sistema fixo", "descarga do sistema", "depois do disparo", `descarreg`, "depois da descarga" e "disparou o sistema" / "sistema … disparou" na rota `seafire` (§6.6; os três últimos da revisão 3 do C5), `SINONIMOS` baliza/testar, ficha `## Equipamentos` com o filtro `seguranca`, `docsvenc` sem a data do `doc-epirb` (§1.8), a guarda de `S` vazio em `/SOS-/` (§1.3) · **push** da Fase 1 junto com este commit | conferência Playwright do PROMPT (sem login, `localStorage` vazio, também offline): `innerText` e atributos de S1/S2 sem `\b\d{9}\b`, coordenada, `snapshot.local`/`.estado`, "SNAPSHOT", SOG/PROA numéricos, registro gerado e o resto do dado gerado da embarcação (o `problemas_barco_sos` do C4 passa a ler também a `base`: `confere.barco_sos(E, numeros=False)`), `tel:` do dado, maré ou previsão simulada, **nem fabricante/modelo de equipamento**; `CapitaoAgora.instante() === null` em S1/S2 e o cérebro com `S` vazio; a linha gravada pelo SOS sem `sim` e sem leitura de `D.simulacao`; sem GPS, a linha gravada pelo SOS contém "plotter" e não casa a regex de coordenada do §2.8 (com `set_geolocation`, só a coordenada do aparelho); `cerebro.py`: `canal16` sem "SEM DADOS"; ficha e `docsvenc` sem a data do `doc-epirb`; as listas `SOS` e `salvatagem` iguais às do gerador (§1.5); `verificar.py S1-SOS-Web S2-SOS-Mobile F3-FAQ-Eletronicos F3-FAQ-Eletronicos-Web --offline` (F3 com "MMSI (cadastro do app)", sem "MMSI SEM DADOS" nem "MMSI da embarcação (DSC)") | as do SOS que citam MMSI, posição ou SEM DADOS; `cerebro.py` "onde fica o EPIRB?"/"onde fica o seafire" mantêm a chave |

**Por que esta ordem:** C1 tira o selo e muda o convidado de uma vez (o botão com o id errado contaria tentativa); C3 vem antes das renomeações que dependem da limpeza de `fontes/`; a rota (C8) só depois da carta; a varredura de termos só reprova no C12, quando o único rótulo que sobra é o `mmsiNota`; Seafire e EPIRB chegam aos leitores juntos com a regra do `pedeIA` (1b). A guarda do trecho do topo entrou antes, na revisão do C5, junto com os trechos de `g_seafire` e `g_epirb` (o `respostaBase` marca `a.seguranca` e o `pedeIA` devolve false), e na revisão 2 do C5 passou a valer qualquer que seja a chave (o `pedeIA` olha o 1º trecho do `buscaBase(q, 1)`: a saudação com assunto, "como você me ajuda com o teste da baliza?", levava o `g_epirb §2` no topo): nunca há uma janela em que o trecho de segurança do topo iria à IA. O 2º e o 3º trechos que a Main e a H2 mandam junto ficam para a F30 (Fase 6, §6.6). O push sai só com a 1b: as janelas do §6.6 (o cérebro do SOS ainda lendo o snapshot, fabricante, modelo e validade do EPIRB e do Seafire na ficha) nunca chegam ao remoto.

### 6.3 Asserções do gerador (`confere()`; falham no `python ferramentas/demo/gerar_demo.py`)

| Nome | Regra |
|---|---|
| `TERMOS` | as 8 regex do `termos.json` (cada uma com a sua flag) sobre todo valor string do `D`, da base, do FAQ e de `fontes/**`, fora as EXCECOES do §3 (o rótulo do procedimento padrão e identificadores); até a 1b, mais a exceção `embarcacao.mmsiNota` |
| `NULO` | nenhum `None`, `''`, `NaN`, `-0` nem lista vazia, fora `abastecimentos`, no arquivo gerado **e** no `D` depois do rodapé e do rebase (o `replay.py` repete): `snapshot.quadro` sem `alarmes`; sem deslocamento, `dn`/`vence` omitidos |
| `SIMULACAO_UNICA` | o texto `"simulacao": true` aparece uma vez no `capitao-dados.js` |
| `TAMANHO` | `capitao-dados.js` ≤ 120 KB; base ≤ 80 KB; FAQ ≤ 100 KB |
| `MMSI9` | `\b\d{9}\b` só em `embarcacao.mmsi` |
| `REGISTRO` | `^[A-Z]{3}-\d{2}-\d{4}$`; não casa placa (`\b[A-Z]{2,3}-?\d{4}\b`, `\b[A-Z]{3}\d[A-Z]\d{2}\b`), HIN, `\b\d{9,11}\b` nem PESSOAIS; `documentos[tie].numero` = `embarcacao.registro` (§1.8): na simulação, sem o documento de `id` `tie` ela reprova (revisão final do C4), e o dado de hoje fica congelado na PENDENTES até o C7; com mais de um `tie`, reprova |
| `HEX15` | nenhum `\b[0-9A-F]{15}\b` |
| `SEM_INDICATIVO` | nenhuma chave `indicativo` fora de `protocolos`; nenhum `\bP[P-Y]\d[A-Z]{2,3}\b` nem `\bZ[V-Z]\d[A-Z]{2,3}\b` |
| `AFIRMA_REAL` | nenhum `(?:^\|[^A-Za-zÀ-ÿ])(?:dados?\|leituras?\|barco\|embarca[çc][ãa]o\|navega[çc][ãa]o)\s+(?:\S+\s+){0,2}(?:reais?\|verdadeir[A-Za-zÀ-ÿ]*\|oficia(?:l\|is))(?![A-Za-zÀ-ÿ])` (flag `i`). Com o fim de palavra, "realizado" e "oficina" não casam |
| `PROTOCOLO_LIMPO` | strings de `protocolos` sem ` bar`, `%`, nós, mn, graus, `\d+\s*(?:min\|minutos)`, fabricante ou modelo de `equipamentos`, nem dado gerado da embarcação além do nome (`barco_sos`, §1.3; revisão 2 do C4); a regex de emergência do PROMPT não casa |
| `LOCAL_VOCAB` | "boia" vale **por origem**: só em texto que vem de `protocolos.mob`, de `protocolos.salvatagem` ou do texto do checklist "Saída · antes de largar" (s13 e o §1.5), em qualquer cópia: os trechos e as páginas de fonte do `protocolo` (§ Homem ao mar, § Salvatagem) e do checklist (§ Saída · antes de largar), os cartões EM-04 e EM-09 e o item CK-03 do FAQ. "kit" proibido em `pecas`, `sensores` e `checklists`; `onde`/`local` de vocabulário fechado |
| `SEGURANCA_MARCADA` | trecho **ou item do FAQ** (CK-xx inclusive) que casa a `SEGURANCA_PALAVRAS` (§1.5: a `SOS` ampliada da 1b, a `salvatagem` com `extintor`, EPIRB, Seafire, MAYDAY, DSC, homem ao mar) ⇒ `seguranca: true`. Desde a 1b, o `cerebro.py` confere que as listas são as do `capitao-brain.js` |
| `SEM_SALVATAGEM_EM` | `sensores.pontos[].id/rotulo` e `pecas[].n` sem epirb, seafire, balsa, colete, extintor nem boia |
| `CALADO_FORA` | (até a Fase 3) nenhum trecho da base nem item do FAQ com "calado" |
| `MODELOS_AVANTI` | com `CAPITAO_LISTAS_PRIVADAS`: `grep -F -i` das duas listas sobre toda a saída = 0 (só contagens) |
| `COLISAO_MODELOS` | com `CAPITAO_AVANTI` (a pasta do Avanti; opcional, como as listas): cada parte de `equipamentos[].modelo` (separada por ` · `, ` e ` e ` + `) e a base dela (§2.5) contadas por substring, sem distinguir maiúsculas, nos arquivos de texto da pasta (fora `CLAUDE.md`, `.claude/` e `.git/`), imprimindo só contagens; 0 em todas, menos as da `EXCECOES_MODELO` (hoje `{'Seakeeper 3': 1}`, com o ok do §8.2). A `nominal` do estabilizador só tem `pct_estabiliza` |
| `FONTE_LIMITES` | cada `limites[c].fonte` aponta para um §n que existe, e o texto contém os números em pt-BR |
| `EQUIP` | fabricante, modelo, `qtd` número e `guia` ∈ `D.guias` em todos |
| `IDS` | `checklists.faq` ⊂ ids do FAQ; `pecas.tarefas` ⊂ ids da agenda; `sensores.campos` e `alarmesPedidos.metricas[].campos` ⊂ `D.campos`, e os `sensores.campos` cobrem os da F08 e da F33 (§1.19); `faixa[0] < faixa[1]` em cada métrica; `sistema` de `agenda`, `tarefasEquipe` e `replay.alertas` ∈ ids de `equipamentos` ∪ {`casco`, `tanques`}; os `ref` de `documentos` e do diário fixo existem; os `ref` do dia de bordo (d02, nota fiscal) ∈ `ab-0…ab-(diaDeBordo.dias − 1)`; `pend` ⇒ `ref` na agenda e `palavras` = `agenda[ref].palavras`, não vazias; `checklists` com os 4 `tipos` e `c` em todo item; nenhum par de `bloco` da mesma fileira a menos de 0,10 |
| `LACO` | cada `chaves[c]` com 30 números finitos; `D.campos` ⇔ o quadro do `em()` portado, nos dois sentidos (`simulado` fora); `snapshot.quadro` ⊂ `D.campos`, com omitidos só de origem `rota` ou `janela`; `sentido` em todo `contador` e só neles; todo campo da Fase 1 do PROMPT existe |
| `LIMITES_FORMA` | chaves de `limites` sem `*` e todas em `D.campos`; com `regimes`, o topo sem `normal`/`aviso`/`critico`; o normal termina no aviso em cada regime; `ativo_se` com `acima` ou `igual`; o port Python da `nivel` dá o resultado dos casos de borda do §3.3 (a Fase 2 repete no Edge contra o JS) |
| `JANELA` | avaliada pela `nivel` portada; cada janela ⊂ [95, 120] e ≥ 10 s; `t = 60` fora e `t = 105` dentro; máximo abaixo do crítico; com `aviso`, nenhum crítico; fora das janelas, todo valor por segundo dentro do normal |
| `FIO` | nenhum valor por segundo a menos de 0,05 de um limite do regime em vigor (pela `nivel` portada) |
| `EMENDA` | só campos do laço: `\|v(149) − v(0)\| ≤` o maior passo de 1 s, campo a campo |
| `EMENDA_ROTA` | `gcd(circuitos_dia, 576) = 1`; nas 576 emendas do dia, segundos consecutivos `em(N·150 − 1 s)` × `em(N·150)`. Fora da âncora: nenhuma chegada (ponto, destino ou base) cai no par; `destino`, `wp_proximo` e ETA iguais; `lat`, `lon`, COG, proa, `piloto_rumo`, profundidade, `destino_mn`, `wp_mn` e contadores com passo ≤ o maior passo de 1 s da volta. Em A, além disso, só os campos da virada do §1.22 |
| `PISO` | `contadores_base.diesel_litros − por_dia.diesel_l ≥ diesel_piso_l + 50` |
| `HORAS` | para cada tarefa por horas: `limite − base ≥ 24` e `limite − (base + 24) > 0` |
| `ROTA` | pernas > 2 × arco de guinada; profundidade ≥ calado + 4 m; nomes, `rel` e `perto` sem dígito; `circuitos_dia × distancia_mn = por_dia × fator` |
| `DIA_DE_BORDO` | a nota fiscal do abastecimento só em `diaDeBordo.documento`, nunca em `documentos` do arquivo gerado; `diasAtras 0 ⇒ h ≤ ancora_hora`; abastecimento (`ab-k` e d02) com `h = ancora_hora`; litros = `round(por_dia)` = o salto do contador entre `A − 1 s` e `A`; `nivelAntes`/`nivelDepois` = o diesel % de `em(A − 1 s)` e de `em(A)`; d01 depois da d02 pelo `iso`; `pessoasBordo` = o número da d01 |
| `SEM_EMERGENCIA` | `emergencia()` e `oleo() === 1` (portados, com a lista `SOS` ampliada) não casam nenhum `diario[].t`, `diaDeBordo.diario[].t`, item de checklist (`t` e `c`) nem `agenda[].t` |
| `AGENDA` | `ultimaHa + venceEm` = `DIAS_MESES[meses]` (31, 184, 365); `palavras` não vazias e sem palavra solta genérica; 3 atrasadas; nenhuma de salvatagem atrasada; `seguranca` só em `epirb-teste`, `seafire-inspecao` e `porao-teste`; `equip` das de salvatagem sem fabricante nem modelo |
| `HISTORICO` | sem NaN; nenhum valor cruza limite (praça + desvio do ar ≤ 60 − 0,05); todas as `metricas` ⊂ `D.campos`; `janelas['150S'] = {passo_s: 1, n: 150}`; `so150` ⊂ grupos de `metricas`, todos de campos do laço; `sazonal` com 73 pontos por campo |
| `COORD_TEXTO` | as regex de coordenada do §2.8 do PROMPT (graus-minutos com vírgula ou ponto; decimal com 4 ou mais casas, ou em par) sobre todo **valor string** do `D`, da base, do FAQ e de `fontes/**` (número do JSON não entra; milhar do pt-BR fica intacto). A única exceção é `snapshot.gps.texto` (L), enquanto houver leitor (§1.17). Estrutural desde o C3 |
| `ROTULO_SEGURANCA` | todo trecho, item do FAQ e página de fonte de `g_seafire`, `g_epirb` e da seção Salvatagem termina com o rótulo do procedimento padrão e "Modelo, validade e acionamento: veja a etiqueta do equipamento." (§1.5) |
| `SEGURANCA_CURTA` | (revisão 4 do C5) todo trecho com `seguranca` tem até 800 letras: o `respostaBase` e a `falaCurta` do cérebro leem o trecho inteiro (teto de 1.500 no cérebro), para o rótulo e a nota da etiqueta nunca ficarem de fora (§1.5) |
| `IDENT_BASE` | (revisões 5 e 6 do C5) `ident` só em trecho com `seguranca`: de 1 a 6 palavras minúsculas de 3 letras ou mais, sem verbo de operação com qualquer flexão (raízes `lig`, `deslig`, `abr`, `fech`, `acion`…: `ligue`, `desligue`, `abra`), sem nome de equipamento ou de sistema e sem "pessoa"/"alguém" (sem distinguir acento). O conjunto de nomes sai do dado: nome, fabricante, modelo e `palavras` de cada equipamento; fonte e `equip` de cada trecho; títulos dos guias; título de toda seção sem `ident`; mais a lista fixa de piso (`ligar`, `sistema`, `gerador`, `motor`, `ventilação`, `alarme`, `disparo`, `bateria`, `plotter`, `manutenção`, `partida`…). `ident` com palavra de queda ou de vista (`caiu`, `cair`, `queda`, `vista`, `mar`) pede `identCom`: de 1 a 8 palavras da lista fechada de pessoa (`pessoa`, `quem`, `alguém`, `gente`, `homem`, `mulher`, `tripulante`, `criança`, `passageiro`, `marinheiro`, `filho`, `filha`, `menino`, `menina`, `amigo`); `identCom` sem `ident` reprova (§1.5). Amostras plantadas em `testes/gerador.py`: 26 nomes e verbos (`plotter`, `ligue`, `garmin`, `bateria`, `manutenção`…), `pessoa`, `alguém`, queda sem `identCom`, `identCom` sem `ident`, fora da lista e vazio |
| `NOTA_ETIQUETA` | `equipamentos[epirb].nota` = `equipamentos[seafire].nota` = `protocolos.seafire.nota` = `protocolos.epirb.nota` (uma constante; antes do C6, só a primeira igualdade) |
| `RODAPE_SNAPSHOT` | o `rodape.js` não atribui a `D.snapshot` nem a nada dentro dele; `snapshot` só aparece dentro de `instante()` (a leitura de `D.snapshot.quadro` e o valor `fonte: 'snapshot'`), depois da guarda `/SOS-/` |
| `FONTES_RELATIVAS` | nos CSV das pastas 02, 03, 04 e 06, nenhuma data `dd/mm/aaaa` nem cabeçalho com data; prazos em dias relativos (§5). Desde o C7 |
| `ESTABILIZADOR_12V` | (revisão 3 do C4) nenhum texto do estabilizador com "AC" ou "CA" (palavra inteira, em maiúsculas), corrente ou energia alternada: inteiros, o trecho e o item do FAQ cuja `fonte` ou `equip` é o estabilizador e todo texto cujo caminho o cita (a página de fonte do guia, `D.faq.estabilizador`, `snapshot.seakeeper`); no resto do `D`, da base, do FAQ e das fontes, a frase que cita estabiliz, Seakeeper ou giroscóp. O Seakeeper 3 é de 12 V DC (§2.5) |

### 6.4 Trava → campo → teste

| Trava (PROMPT) | Campos | Asserção do gerador | Teste na execução |
|---|---|---|---|
| §2.1 SOS fora da simulação | `protocolos`, `embarcacao.nome` | `PROTOCOLO_LIMPO`, `MMSI9` | 1b (Playwright), `replay.py`, `verificar.py S1/S2 --offline`; em S1/S2, `CapitaoAgora.instante() === null`, o cérebro com `S` vazio, nenhuma leitura de `D.simulacao` e a linha gravada pelo SOS sem coordenada (sem GPS) ou só com a do aparelho, e sem `sim`; S1 e S2 sem o registro, o fabricante, o modelo, a marca, o `rotulo` e a `motorizacao` desde o C4 (a `base` entra na 1b) |
| §2.1 rebase nunca toca o snapshot | `snapshot` | `RODAPE_SNAPSHOT`: nenhuma escrita em `D.snapshot`; a única referência é a leitura de `D.snapshot.quadro` dentro de `instante()`, nunca em S1/S2 | `JSON.stringify(D.snapshot)` igual antes e depois do rebase (C7) |
| §2.2 `MMSI_NUM` × `MMSI_RADIO` | `embarcacao.mmsi`, `protocolos.mmsiRadio/mmsiRotulo` | `MMSI9`; nada de "programe" perto de MMSI | `cerebro.py`: chaves do §2.2 sem 710123456 em t = 60/105; rota `mmsi` com as duas linhas; `canal16` sem "SEM DADOS" (1b); F3 web e app com "MMSI (cadastro do app)" (1b) |
| §2.2 indicativo, HEX, telefone, local nunca gerados | — | `SEM_INDICATIVO`, `HEX15`, `TERMOS` (PESSOAIS, LOCAL_SEGURANCA) | `replay.py` (percorre o `D`); filtro de saída (Fase 6) |
| §2.2 relato de falha sem leitura | `limites` (só no `oleoLeitura`) | — | `cerebro.py` (` bar`/`%` ausentes em `oleo` e porão) |
| §2.3 salvatagem e `seguranca` | `protocolos.salvatagem`, trechos, itens do FAQ, `equipamentos[].seguranca` | `SEGURANCA_MARCADA` (com as listas do cérebro), `LOCAL_VOCAB` | `cerebro.py` (salvatagem; "como testar a baliza?" → PEDE_IA False; um trecho com "extintor" → PEDE_IA False; desde a revisão do C5, "teste da baliza", "como acionar o disparo manual do sistema fixo?", "supressão" e "botão distress" → PEDE_IA False; desde a revisão 2, também a saudação com o trecho de segurança no topo ("como você me ajuda com o teste da baliza?") e o "não abra o acesso ao motor" no topo depois do disparo do sistema fixo; desde a revisão 3, o topo depois do disparo também manda desligar motores, gerador e ventilação, e a pergunta genérica sobre os equipamentos ("quais equipamentos tem a bordo?") volta ao `fallback` com a IA, sem o `g_epirb` nem o protocolo no topo; desde a revisão 4, a pergunta comum que não nomeia o assunto do trecho ("como religar o gerador depois de desligar", "como abrir o motor", "como desligar a ventilação", "como esfriar o motor depois de navegar", "o alarme disparou") nunca traz trecho de segurança ao topo nem à resposta (`gerador`/`motores`, `fallback` ou `base` do guia certo, com PEDE_IA como antes do C5), "quando trocar o óleo do motor?" vai ao `g_motores §7` com PEDE_IA True, "botão distress" e "o sistema descarregou" continuam locais, e o trecho de segurança sai inteiro na tela e na `falaCurta`, com o rótulo (e a nota, no Seafire e no EPIRB) no fim; na 1b, "disparou o sistema da casa de máquinas" e "quanto tempo esperar para abrir a praça de máquinas depois da descarga" → `seafire` e "como testar a baliza?" → `base` ou `epirb`, todos com PEDE_IA False; listas iguais às do gerador) |
| §2.3 EPIRB/Seafire no procedimento padrão | `protocolos.seafire/epirb`, `documentos[doc-epirb]` | `PROTOCOLO_LIMPO`, `ROTULO_SEGURANCA`, `NOTA_ETIQUETA`; agenda de salvatagem em dia | `cerebro.py`: `epirb`/`seafire` sem dd/mm/aaaa e sem o modelo; ficha e `docsvenc` sem a data do `doc-epirb` (1b); F1 e E2 sem modelo de segurança, também nos links do chat (C5) |
| §2.4 replay sem emergência | `replay.cenario`, `janelas`, `diario` | `JANELA`, `SEM_EMERGENCIA`; porão ≤ 5 cm | `replay.py` (alarme só na janela) |
| §2.5 tempo e maré reais | (nada gerado) | nenhum campo de previsão ou maré; `historico` sem maré; trava do ar **e da água** pela leitura salva `capitao.clima.v1` (`CapitaoAgora.trava`, no `instante()` e na base do histórico, §1.22) | `chat_ia.py`/`replay.py` com Open-Meteo bloqueado; ar e água presos e com o mesmo texto na A1 e na Main com a leitura salva injetada, inclusive com a máxima abaixo de 20,1 °C (Fase 4) |
| §2.6 nunca afirma nem denuncia | todos os textos | `TERMOS` (AUTENTICIDADE), `AFIRMA_REAL` | grep final; `replay.py` |
| §2.7 dinheiro e terceiros | `documentos`, `equipe`, `pecas`, `abastecimentos` | `TERMOS` (DINHEIRO, PESSOAIS); papéis em lista fechada; sem número de apólice, NF ou licença | grep final; filtro da IA |
| §2.8 coordenadas | `rota`, quadro `lat/lon` | `COORD_TEXTO` (exceção só `snapshot.gps.texto`, enquanto houver leitor); série da 05 sem posição | `cerebro.py`/`chat_ia.py` (`semCoord`, corpo enviado) |
| §2.9 registro só cresce | `localStorage` (§1.25) | nenhum ticket, alarme pedido ou linha de aparelho gerado | `replay.py` (`sim: true` nas linhas gravadas do diário, **menos as do SOS**, que nunca o levam, e em executado, docs e abast; com `simulacao: false`, o selo "apresentação" nunca numa linha do SOS); F25 restaura só somando (nos mapas, o valor do aparelho ganha) |
| §2.10 fonte técnica, modelos, registro | `limites[].fonte`, `equipamentos[].modelo`, `registro` | `FONTE_LIMITES`, `MODELOS_AVANTI`, `COLISAO_MODELOS`, `REGISTRO` | C5; `git grep -F -f` das duas listas |
| §3 termos | tudo | `TERMOS` | `proibidos.py`, `replay.py`, grep final |

### 6.5 Testes que as Fases 2–7 herdam deste contrato

- **Paridade Python × JS:** `quadro(t)` (= `em(início da volta + t s)`, §1.24) campo a campo do laço = a linha t da série de 150 s, para t = 0…149; Σ de 150 s = `por_volta`; `contadoresEm(A + 576·150 − 1)` = base + `por_dia` (± arredondamento).
- **Emenda absoluta** (segundos consecutivos, `em(N·150 − 1 s)` × `em(N·150)`, nas 576 emendas do dia): sem pulo em contadores, `lat/lon`, COG, proa, `piloto_rumo`, profundidade, ETA, `destino_mn` e `wp_mn`. O único salto é entre `A − 1 s` e `A`, nos contadores, nos tanques e nos campos da rota que recomeça (`destino`, `destino_mn`, `eta`, `wp_*`, `piloto_rumo`, `local`).
- **Tendência:** `instante().tend` em 12:01:00 e 12:01:45 = os valores do §1.23; C3, ficha e F11 mostram o mesmo número. **Na virada:** em 07:00:10, `tend` sem `diesel_litros` e `txt.tend` sem "diesel" (rpm, óleo, arrefecimento e SOG presentes).
- **SOS:** em S1/S2, `CapitaoAgora.instante() === null`, `B.resumoAgora()` = `protocolos.plotter`, nenhuma leitura de `D.simulacao` e a linha gravada sem `sim`.
- **`nivel`:** Python = JS nos 150 quadros e nos casos de borda do §3.3; C3, cores, `capitao-alertas`, F09 e F11 dão o mesmo nível no mesmo instante.
- **Contadores sem voltar:** pelo `D.campos[c].sentido`, fora do par `A − 1 s` × `A`.
- **Pares por `ref` na madrugada:** em 06:59:59 e 07:00:01, d06, d09 e d03 no dia do alvo (§1.0).
- **Janela de 150 s:** `serie(c, '150S')` com 150 pontos, sem NaN, último = quadro.
- **Um instante só:** com `fixar('60')`, `inst.txt.rpm`, `.sog` e `.diesel` iguais na Main, A1, E1, HUD, `answer('telemetria')` e `## Navegação agora`.
- **Catálogo:** campos do `em()` ⇔ `D.campos` (sem `simulado`); `snapshot.quadro` ⊂ catálogo; alarme avaliado no valor arredondado.
- **Âncora única:** `CapitaoAgora.ancora` é a função que o replay usa (o mesmo objeto, sem cópia).
- **Histórico:** `serie()` sem NaN; o último ponto = o quadro; o serrote do diesel = as linhas de abastecimento; `temperaturas` com a curva do ano (30 D e 1 A não saem retos).

### 6.6 Inconsistências temporárias conhecidas (não são quebra; cada fase resolve a sua)

- **Nenhuma janela abaixo vai para o remoto antes da 1b:** os commits C1–C12 ficam locais e o push da Fase 1 sai junto com a 1b (o site é a `main` e não muda, mas o branch é público).
- Até a Fase 3, o cérebro conta a história do snapshot de 26/09 (848 L, fundeado, consumo desde 12/09), enquanto diário, abastecimentos e prazos já estão em datas de hoje.
- Do C1 à 1b, o cérebro que o SOS carrega ainda lê o `D.snapshot` legado na carga (`capitao-brain.js:15`, `:89-98`); as funções que o SOS chama não o usam, e a guarda de `S` vazio entra na 1b (§1.3).
- S1 do C1/C4 à 1b: já sem o selo (C1) e sem o REG (C4), mas ainda com a faixa do snapshot, o "último fix" e o VHF antigo (1b).
- Do C5 à 1b, a ficha `## Equipamentos` leva fabricante e modelo do EPIRB e do Seafire; do C7 à 1b, o `docsvenc` e a ficha levam a data do `doc-epirb`. A 1b fecha as duas.
- Textos "Volvo Penta" fixos no cérebro, na C3 e na G4 (Fases 3 e 4); o modelo antigo do VHF em S1/S2 (1b).
- Até a Fase 6 (F30), a Main e a H2 mandam à IA os 3 primeiros trechos do `buscaBase`. Desde a revisão do C5 o `pedeIA` barra o trecho de segurança do topo (desde a revisão 2, qualquer que seja a chave: também na saudação com assunto), mas, com o topo sem `seguranca`, um 2º ou 3º trecho com `seguranca` ainda vai junto (ex.: "como ligar o gerador?" leva o `g_gerador §1`, marcado pelo "cheiro de combustível").
- Pergunta digitada ou falada com "AIS" cai na rota `canal16` (o ` ais ` da rota, de antes da 1.1.0) e devolve o roteiro MAYDAY. O cartão da F1 já não pergunta assim (revisão do C5); a Fase 3 dá ao AIS uma rota própria antes de o `canal16` ligar o `emergenciaAte` (PROMPT §2.2).
- As respostas prontas `dessalinizador` ("não consta na lista de equipamentos"), `climatizacao` ("fabricante e modelo SEM DADOS") e `audio` ("modelo SEM DADOS") ainda são as de antes do C5, e o cartão do dessalinizador na F1 cai na primeira (Fase 3). Também de antes do C5, e contra o inventário (revisão 2 do C5): a `ancora` ("Sem sensor de âncora na rede NMEA — SEM LEITURA do ferro", "conforme o cabo lançado"), quando o `ancora` tem o contador de corrente (§2.5) e o `g_eletronicos §3` fala da corrente lançada e do contador; a `porao` ("Sem sensor de porão… SEM LEITURA"), com as bombas Rule de sensor de nível; a `estabilizador` ("Tempo de aceleração e códigos de alarme: MANUAL NO DRIVE (modelo SEM DADOS)"); e a `eletronicos`, que não fala do radar nem do piloto, para onde vai o texto digitado com "radar" ou "piloto" ("zona de guarda do radar", "como funciona o radar?"). A Fase 3 reescreve as quatro e dá ao radar e ao piloto a rota do guia deles (ou o `base`). Os cartões da F1 do guincho, do radar e do piloto já perguntam o procedimento e caem no guia (revisão 2 do C5, §1.4); os do porão e do sistema elétrico ainda caem nas respostas prontas (o `verificar.py` os deixa de fora até a Fase 3).
- Até a Fase 6 (§2.8 do PROMPT), o `historico` que a Main e a H2 mandam à IA leva o texto das respostas anteriores sem o `semCoord`: depois de uma resposta `ancora` ou `posicao`, que mostram as coordenadas do snapshot, a pergunta seguinte que vai à IA leva a coordenada (lacuna de antes da 1.1.0, que a Fase 6 fecha no ponto único do cliente; desde a revisão 2 do C5, nenhum cartão da F1 cai nessas duas respostas).
- "Posso abrir o acesso ao motor depois do disparo?" cai na rota `motores` (desde a revisão 4 do C5, o trecho do `g_seafire §3` nem aparece nos hits: a pergunta não nomeia o sistema fixo, §1.5; com "do sistema fixo" no fim, o §3 vem ao topo). Na 1b, a rota `seafire` ganha "sistema fixo", "descarga do sistema" e "depois do disparo" (antes de `motores`, como as outras palavras dela), e os casos do disparo do `cerebro.py` (hoje `base`, com o "não abra o acesso ao motor" e o desligamento de motores, gerador e ventilação no topo) passam à chave `seafire`, com os passos de `protocolos.seafire`. Revisão 3 do C5: essas três palavras não pegam todo relato de descarga. Hoje (e antes do C5), "disparou o sistema da casa de máquinas" e "quanto tempo esperar para abrir a praça de máquinas depois da descarga" caem no `fallback` sem trecho e vão à IA, e "como testar a baliza?" também (o `testar` não casa o "teste" do `g_epirb §2` sem os `SINONIMOS`). Sem trecho no topo, a guarda do `pedeIA` não age. Na 1b, a rota `seafire` ganha também `descarreg`, "depois da descarga" e "disparou o sistema" / "sistema … disparou" (ou "disparo" junto de "sistema"), e o `cerebro.py` ganha os três casos com PEDE_IA False: os dois primeiros na chave `seafire`, e "como testar a baliza?" na `base` ou na `epirb` (depois dos `SINONIMOS` baliza/testar).
- A A1 e a G2 comparam cada tanque com o 25 % da `regraAbast` (a A1 pinta cada barra; a G2 olha o menor dos dois), e a regra é do total dos tanques desde a revisão 2 do C5 (§1.10). Com os tanques iguais dá o mesmo; a Fase 4 passa as duas ao `nivel` do `diesel_litros`.
- `docsvenc` ainda escreve "SEM DADOS: ." com a lista vazia; `## Embarcação` ainda escreve "indicativo SEM DADOS" (Fase 3). O `canal16` já sai sem ele na 1b.
- `snapshot.gps.texto` (L) continua no `D` até o último leitor (Fase 5, `capitao-voz.js:59-61`): é a exceção única da `COORD_TEXTO`.
- A leitura da pasta 05 fica com a data de 26/09 até a Fase 3; as outras fontes do Drive já têm prazos relativos desde o C7.
- Do C4 ao C7, o registro `CIA-23-0417` já está preenchido (C4) e o documento do TIE ainda é o de antes (sem `id`, `st: 'SEM DADOS'`, "registro não informado"): a ficha que vai à IA leva `## Embarcação … registro CIA-23-0417` e "SEM DADOS: Título de Inscrição da Embarcação (TIE)" ao mesmo tempo, e a G1 mostra "registro não informado" ao lado do "REG. CIA-23-0417" do cabeçalho da Main e da moldura. A asserção `REGISTRO` congela a falta do documento em `PENDENTES['REGISTRO']['C7']` (revisão final do C4); o C7 grava `id: 'tie'` e `numero` = `embarcacao.registro` (§1.8) e tira a linha: sem tirá-la, o gerador reprova (pendência que não ocorre mais).
- Telas que leem `D.snapshot` mostram a leitura de 26/09 (Fase 4). `liveTip` da H2 ainda diz "snapshot" no `title` (Fase 4).
- `SOBRE_APP` antigo (Fase 3).
- F2 web e app (`F2-FAQ-Estabilizador*.dc.html`, `geradorAC()`) mostram "Gerador Onan (energia AC)" entre as leituras do estabilizador. Com o Seakeeper 3 de 12 V DC (revisão 3 do C4, §2.5), a leitura certa é o banco de 12 V (`bateria_2_tensao_v`), e o gerador só como fonte do carregador (Fase 4).

### 6.7 Rascunho do passo 0 (≤ 25 linhas)

```
## Decisão do proprietário — 1.1.0 · modo simulação (<data do início da Fase 1>)
1. Paridade com o Avanti Vessel 1.24.0 (motor, estrutura, telas, integrações); nenhum dado dele. avanti-* → capitao-*; cache capitao-site-.
2. CONVERSA do Avanti: núcleo de anéis em <canvas>, cores WonderHUB, ∞ no centro; sai o rosto; contrato .cpz mantido.
3. Dados completos e nenhum selo: sem DEMO, SEM DADOS, SEM LEITURA, MANUAL NO DRIVE ou A CONFERIR/A CONFIRMAR em dado de bordo (anexos à parte).
4. Navegação simulada: laço de 150 s (capitao-replay.js), âncora 07:00 America/Sao_Paulo, posição contínua pela rota; tudo lê o mesmo instante.
5. Respostas com número e hora; nunca "fictício/simulado/DEMO"; nunca afirma que é real (sobreDados: frase padrão do PROMPT §2.6).
6. D.simulacao gerado. false = replay inerte, caminho null → SEM DADOS, IA sem modo, filtros de simulação desligados (coordenadas continuam).
Travas (ganham de qualquer decisão):
7. SOS (S1/S2) fora da simulação: só nome e protocolos; posição = GPS do aparelho ou LEIA NO PLOTTER; offline, sem login, nunca recarrega.
8. MAYDAY em todo lugar com MMSI_RADIO; 710123456 só em Embarcação, Documentos, F3, ## Embarcação e 2ª linha da rota mmsi.
9. Nunca gerar indicativo, HEX ID, telefone ou lugar de equipamento de salvatagem.
10. Emergência local, nunca na IA; relato de falha sem leitura simulada; 15 min de conversa em emergência sem posição/rumo/SOG/ETA/pessoas.
11. O replay não gera emergência: só AVISO; crítico só com cenario 'alarme-critico' (desligado). Nunca abre SOS/C3, fala ou grava sozinho.
12. Tempo e maré sempre reais; vento e mar do quadro só "a bordo agora".
13. Fora do barco e dinheiro: rota local; nunca preço, telefone, e-mail, CPF/CNPJ ou nome de terceiro.
14. Coordenadas nunca saem do aparelho (os dois modos). Registro só cresce; linhas com sim: true.
15. Faixas do "Guia de bordo — <equipamento> §n"; modelos de mercado diferentes dos do Avanti; registro sem colisão.
16. support.js e deck-stage.js não se editam à mão; nunca {{…}} em atributo de SVG; Worker real só com motivo.
(a) núcleo do Avanti em canvas · (b) nenhum selo · (c) crítico desligado · (d) 1.1.0 · (e) barco, registro e rota escolhidos pelo Claude (PARIDADE)
(f) frase padrão da sobreDados · (g) exceções do "toda resposta com dado" · (h) runtime atual · (i) ficha até 16.000 se passar de ~11.500
(j) posição contínua pela rota · (k) convidado: chave demo, nome Convidado, papel convidado.
Vale sobre as linhas marcadas abaixo enquanto simulacao: true; com simulacao: false volta a regra Nada inventado.
```

---

## 7. Decisões tomadas e porquê

**Base e enxertos**
1. **Base: a proposta de travas.** É a que menos viola trava, privacidade e verossimilhança: motores coerentes, registro sem colisão, contrato de leitura do SOS e nenhuma quebra fora da tabela da Fase 7.
2. **Porta única e formatador único (do consumidor), fora do `D` (do gerador e de travas).** `CapitaoAgora.instante()`, `fmt` e `contagens()` moram num global do rodapé, e o `D` continua só dado. Assim o "mesmo texto em seis superfícies" sai por construção, a varredura do `replay.py` não esbarra em funções e o cérebro da Fase 3 só congela o instante (o PROMPT põe o `instante()` no cérebro: ele vira um envoltório desse).
3. **`D.campos` é o esquema único** (rótulo, unidade, casas, origem) para formatador, cores, alarme, gerador e coletor real. Era enxerto de duas propostas (catálogo do consumidor e `replay.campos` do gerador). Fica no topo do `D` porque o modo real também o usa. O ruído fica em `replay.ruido`, só da simulação.
4. **Laço pelo gerador:** ruído por hash inteiro, arredondamento explícito, janelas derivadas no valor mostrado, asserção de 0,05 do limite, `"simulacao": true` único e emenda conferida.

**Erros graves corrigidos**
5. **3ª bateria gerada** (`bateria_1_tensao_v`, banco de partida 24 V). A PARIDADE aprovada (F07, F33) pede 3 séries, e o coletor de hoje já tem o buraco no índice 1. O corte para 2 bancos não tinha ok.
6. **Campos das F08 e F33 já na Fase 1:** `jogo_graus`, `caimento_graus`, `temp_praca_maquinas_c`, `vento_aparente_*`, `destino_mn`, `wp_*` e os estados de climatização, dessalinizador, radar e AIS. Sem eles, A4/A5 e a estação meteorológica imprimiriam "—" (VAZIOS). Na revisão 2, o inclinômetro ganhou o `proa_graus` (o yaw da F08) e a estação, o ar externo e a pressão (F33).
7. **Abastecimento coerente com o contador:** litros = `por_dia` (1.086 L), às **07:00** (`ancora_hora`), no mesmo instante do salto do contador, como o PROMPT manda. Nível de antes = fim do dia anterior (29,6 %), inserido pela microtarefa só com `simulacao`. A d01 (saída) fica depois da d02 pelo `iso`. As linhas antigas de 620 e 540 L saem: contavam outra rotina. Às 06:45, a linha diria 97,5 % enquanto o replay mostra ~474–485 L chegando à base.
8. **Sinal dos deslocamentos convencionado** (positivo = há N dias): as tabelas de travas tinham −47, −14 etc., o que punha datas no futuro.
9. **Sem faixa cinza:** o normal termina no limite do aviso em todas as faixas (as de bateria tinham 24,8 × 24,4 e 29,2 × 29,6). O formato `{de?, ate?}` permite faixa aberta de um lado.
10. **Faixas próprias, verossímeis e longe das do Avanti:** a de óleo depende do regime (1,0 bar na lenta, 2,4 bar a partir de 1.000 rpm), o que tira o "3,0 bar em qualquer regime"; arrefecimento com aviso acima de 88 °C e crítico acima de 97 °C. Nenhum número coincide com o guia do Avanti (conferido sem citá-lo).
11. **Enum do quadro também no snapshot:** `ancora.estado: 'lançada'` (era "fundeado", fora do enum). **Guardas de [object Object]** em B2:158 e F3 :216/:222, no mesmo commit em que porão e âncora viram objeto.
12. **Modelos que colidiam trocados:** cinco candidatos de equipamento tinham ocorrência por substring na pasta e foram trocados (§2.5). Os de hoje (em-trak B954, GMR 24 xHD3, MS-UD755 e os demais) têm contagem 0 na pasta e nas listas. O gerador fica na linha QD (o mesmo fabricante informado, família diferente): é essa a justificativa, e não "fica longe".
13. **Piloto hidráulico:** o GHP 20 exige direção eletrônica, que um barco de eixo com direção hidráulica não tem. Fica um piloto hidráulico de outro fabricante (pede ok, §8).
14. **Registro `CIA-23-0417`:** os outros dois candidatos casavam formato de placa de carro (um deles, placa válida de outro estado).
15. **Seafire:** grafia sem hífen em todo dado (com hífen, a palavra escapa da regex `seafire` do LOCAL_SEGURANCA); passos sem "compartimento" (colado em "Incêndio · Seafire:", casaria o filtro). A emenda do LOCAL_SEGURANCA no `termos.json` (`sea-?fire`, revista para `sea[- \u00a0\u2010-\u2014]?fire`, §8.2 ponto 2) pede ok (§8).
16. **"calado" fora dos trechos até a Fase 3:** com ele num trecho, "qual o calado do barco?" sairia do `fallback` para `base` e quebraria as asserções da Fase 3 (`cerebro.py:87/:96` e `chat_ia.py:217–:291`, linhas da tabela da Fase 7) antes da hora.
17. **Snapshot e autonomia legados até a Fase 3:** a asserção do «≈ 11,2 h» do `chat_ia.py` só muda quando a tabela da Fase 7 manda.
18. **Ficha dentro do teto até a Fase 3:** 3 linhas de abastecimento (não 7) e medição em todo commit desde o C1; a asserção do tamanho da ficha não muda antes da Fase 3. Estimativa: ~9.700 letras, a partir das 9.319 medidas hoje (§6.1).
19. **`equipNota` neutra fica** até a Fase 4. Sem ela, F2–F5 mostrariam "lista de equipamentos SEM DADOS", que é rótulo novo em dado de bordo (decisão 3).
20. **Códigos de alarme do Seakeeper:** o PROMPT pede "códigos"; o contrato traz as mensagens do display e o que fazer, sem número. Inventar código de um modelo real é atribuir ao manual algo não verificado (§2.10). É desvio, e vai para o ok (§8).

**Escolhas de desenho**
21. **Histórico expandido pelo cliente:** como cada dia de bordo repete o modelo de 24 h e os baldes são múltiplos de 150 s alinhados às 07:00, o gerador guarda só os desvios lentos de tempo e baterias (a cada 2 dias) e as médias de cruzeiro da F11. Fica ~6 KB no lugar de ~100 KB, com o último ponto igual ao quadro e o serrote do diesel igual às linhas de abastecimento. Nada de "uso normal" contando outra história que os contadores.
22. **Tanques como contador:** água cai e servidas sobem desde a âncora, e voltam na virada (água completada e servidas esvaziadas na marina, como diz a d02). Constantes por um ano dariam um gráfico chapado de 1 A.
23. **19 circuitos por dia e fator 0,9407:** 19 é primo com as 576 voltas, então nenhuma chegada cai numa emenda de 150 s (com 20, a chegada à base caía no segundo da emenda às 13:00, 19:00 e 01:00). O barco está na base às 06:59:59, a virada das 07:00 não move a posição nem o COG, e bate com a saída da Barra Sul na d01. Custo: a posição anda ~6 % menos que o SOG (§1.14, pede ok).
24. **ETA pela distância linearizada** e **STW e proa pela corrente vetorial**: o HH:MM não pisca dentro da volta e o STW depende do rumo.
25. **Carga de cruzeiro em 62 %**, coerente com ~34 L/h por motor (≈ 61 % do consumo nominal).
26. **`capitao.replay.sobre` só com o instante fixado:** é gancho de teste da E1 e nunca age no uso normal.
27. **`#a=` aceito junto com `#alarme=`** na C3: o dado só tem o id; aceitar os dois não custa nada.
28. **Guias de segurança sem fabricante** (`Guia de bordo — Sistema fixo de incêndio`, `Guia de bordo — EPIRB`) e trechos de segurança sem modelo no `equip`: nenhuma "Fonte:" de resposta de emergência leva marca ou modelo.
29. **`fmt.campo` devolve `null`** quando falta o valor: o arquivo de dados fica sem "SEM DADOS"/"SEM LEITURA", e o caminho `null → SD` continua nos leitores (decisão 6).
30. **Orçamento de 120 KB com plano B mecânico** (histórico e depois checklists/sensores em arquivo à parte), porque o SOS carrega o `capitao-dados.js`.
31. **Peças:** sem `pn`; o rotor do gerador zerado (bate com a d03) e o da bomba de água salgada dos motores abaixo do mínimo (bate com a d04 e a F11).

**Revisão do crítico (lacunas corrigidas)**
32. **SOS sem quadro:** `CapitaoAgora.instante()` devolve `null` em `/SOS-/`. O SOS carrega o cérebro e grava pelo `B.addDiario`; sem a guarda, a ordem de fonte cairia no `snapshot.quadro` e a posição dele iria para o diário do SOS.
33. **Todos os leitores contados por grep:** `mmsiNota` (mais as duas F3, trocadas na 1b), `agendaFalta` (4 leitores, cada um com a sua guarda), os quatro `*Fonte` (35 leituras), `snapshot.gps.texto` (11 leituras em 10 arquivos, até a Fase 5) e o "prazos contados a partir de" de C1, C2 e B1 (C7).
34. **Tendência de 30 s numa fórmula só** (`instante().tend`), para a C3, a ficha e a F11. A F11 ganha um achado do instante, que muda entre t = 60 e t = 105.
35. **Trava do ar e da água pela leitura salva** (`capitao.clima.v1`, lida pela `CapitaoAgora.trava` no `instante()` de toda tela e na base do histórico). Na revisão 2, a água deixou de ser exceção: a trava do §2.5 é inegociável e prender a água custa o mesmo que prender o ar.
36. **Temperaturas no histórico** com a curva do ano numa tabela (sem `Math.sin`) e o último ponto igual ao quadro.
37. **FAQ sem o chip de confiabilidade e sem os anexos do Avanti**, no `CORE` já na Fase 3, quando o cérebro passa a ler o arquivo.
38. **Alarmes pedidos pela `faixa` própria**, não pelo `limites`: vento, SOG, pressão e água do mar não têm limite de alarme no guia.
39. **Checklist coerente com agenda e diário:** s04 parcial; `agenda[].seguranca` define o s12, que fica pendente com o teste do porão atrasado.
40. **Fontes do Drive com prazos relativos**, como o app; **F25** com a lista fechada de chaves.
41. **Asserções sem falso positivo:** `LOCAL_VOCAB` por origem e `AFIRMA_REAL` com fim de palavra.

**Revisão 2 do crítico (lacunas corrigidas)**
42. **SOS sem a flag:** em `/SOS-/`, nem a microtarefa nem o `addDiario` leem `D.simulacao`, e a linha do SOS nunca leva `sim`; o selo "apresentação" e a saída da ficha nunca valem para ela. A guarda de `S` vazio do cérebro entra na 1b (§1.3). Fica para o ok (§8.2) se o proprietário preferir o `sim` nas linhas do SOS.
43. **Agenda que fecha a conta:** `casco-anodos` 175 e `epirb-teste` +13; `DIAS_MESES` explícito (§1.7).
44. **F20 com contrato de dado:** `acao` `resolve`/`reabre`, `alvo`, Desfazer como linha nova, estado pela última ação, `palavras` da pendência = as da tarefa, `contagens().pendencias` só com as abertas (§1.9, §1.25).
45. **Registro fora do SOS desde o C4** (e o selo desde o C1), e o push da Fase 1 só com a 1b (§6.2, §6.6).
46. **Água presa como o ar** (§1.22), com o caso de máxima abaixo de 20,1 °C no teste.
47. **Sensores completos para a F08 e a F33:** `proa_graus` no inclinômetro; estação meteorológica com ar e pressão (§1.19).
48. **Janela de 150 s** no histórico, com os grupos do laço (§1.13).
49. **`limites` de forma fechada e regra única** (`CapitaoAgora.nivel`, com port em Python e paridade, §3.3).
50. **Nota fiscal do dia de bordo pela microtarefa** e `IDS` contra os ids que ela cria; reserva corrigida e guarda do `consumo` para a lista vazia (§1.8, §1.10).
51. **Tendência sem atravessar a virada:** contadores fora do `tend` nos 30 s depois das 07:00 (§1.23).
52. **`SEGURANCA_MARCADA` com as listas do cérebro** (SOS ampliada, salvatagem com extintor, EPIRB, Seafire) e sobre itens do FAQ também (§1.5).
53. **Contagem de modelos por substring** (`COLISAO_MODELOS`); estabilizador e radar trocados; o estabilizador sem números do fabricante (§2.5).
54. **Campos que o gerador teria de inventar, escritos:** as 3 tarefas novas, `sistema` fechado, `c` e `tipos` do checklist, `perfil`/`planta` e `bloco`, e o `snapshot.quadro` campo a campo (§1.4, §1.7, §1.17–§1.19).
55. **Validade do EPIRB fora da ficha:** o filtro da 1b fica dentro do `docsvenc`, que é o bloco `## Documentos` da ficha (§1.8).
56. **F1 sem fabricante de segurança no chat** e com o link direto do VHF e do áudio pelas `palavras` (§1.4).
57. **`CÂMBIO` do rádio fora do DINHEIRO** (emenda para o ok, §8.2).
58. **Ficha medida (9.319) e estimativa refeita;** asserções citadas pelo texto (§6.1).
59. **`simulado` fora do catálogo e `sentido` nos contadores** (§1.15).
60. **Diário fixo na base hoje:** os pares por `ref` no mesmo dia também de madrugada (§1.0).
61. **Docstring do gerador e regra de restauração por chave** (§4.3, §1.25).

---

## 8. Lista da decisão (e) para a PARIDADE.md

### 8.1 Escolhas (só para conferência)

| Item | Escolha |
|---|---|
| Barco | Estaleiro Marévia · Marévia 40 HT · 2023 (marca fictícia, sem colisão) |
| Dimensões | 12,40 m · boca 3,95 m · calado 1,10 m · 10,4 t · tanques 2 × 800 L de diesel, 400 L de água, 100 + 100 L de servidas |
| Lotação / a bordo | 12 / 4 |
| Registro | CIA-23-0417 (= número do TIE; nunca no SOS) |
| MMSI / indicativo | 710123456 só nos lugares do §2.2 / nunca gerado |
| Motores | 2 × Cummins QSB6.7 305 (eixo) |
| Gerador | Onan QD 9 (9 kW, 60 Hz) |
| Estabilizador | Seakeeper 3 (12 V DC, no banco de 12 V; sem números do fabricante no guia; exceção de contagem para o ok, §8.2) |
| Climatização | Webasto FCF Platinum 16000 + 2 × 12000 |
| Plotters / radar | Garmin GPSMAP 1243xsv ×2 / Garmin GMR 24 xHD3 |
| Áudio / VHF | Fusion MS-UD755 / Icom IC-M510 + IC-M37 |
| EPIRB / incêndio | Ocean Signal SafeSea E100G / Seafire FD 300M |
| Dessalinizador / bombas / guincho | Schenker Zen 30 / Rule 2000 (24 V) ×2 / Lewmar V2 + AA150 |
| Piloto / AIS | Raymarine Evolution (EV-1 · ACU-400) / em-trak B954 |
| Baterias | Victron Energy AGM Super Cycle 12 V 230 Ah ×8 (serviço 24 V, partida 24 V, 12 V) |
| Base e waypoints | 19 circuitos por dia (fator 0,9407) · Barra Sul → Ilha das Cabras → Ponta das Laranjeiras → Taquaras → **Estaleirinho** → Praia do Pinho → Laranjeiras → Ilha das Cabras → base; 15,42 mn; coordenadas na §2.6, **a conferir na carta antes do commit** |

### 8.2 Pontos que pedem o ok do proprietário (registrar junto)

| # | Ponto | Proposta |
|---|---|---|
| 1 | Códigos de alarme do Seakeeper (PROMPT Fase 1) | mensagens do display e o que fazer, sem código numérico (§2.10) |
| 2 | Emenda do `termos.json`, numa só: (a) `seafire` → `sea-?fire` no LOCAL_SEGURANCA, com o caso que barra "O Sea-Fire fica na praça de máquinas."; (b) no DINHEIRO, o `c[âa]mbio` sai da lista de palavras de preço e vira `c[âa]mbio\s+(?:do\|da\|de\|est[áa]\|hoje\|comercial\|turismo\|oficial)(?![A-Za-zÀ-ÿ])[^\n\d]{0,25}\d`, com os casos que passam "AUXÍLIO NECESSÁRIO — CÂMBIO. Canal 16 em escuta." e "Termine com câmbio e aguarde a resposta no canal 16." e o que barra "O câmbio do dólar hoje está em 5,40." | aplicar. (a): o filtro da IA pega a grafia do fabricante. (b): hoje o "CÂMBIO" do roteiro seguido de "Canal 16" na mesma linha casa o DINHEIRO; o filtro de saída da IA (Fase 6) devolveria 502 numa explicação comum de chamada no VHF, e o grep final acusaria o S1 e a página EMERGÊNCIA do Guia. Nos casos, a emenda não afrouxa o dinheiro: os 7 casos que barram e os 23 que passam do `termos-casos.json` dão o mesmo resultado (`revisao2-scripts/cambio.py`), sem lookbehind e sem `\w`. Com o ok, entra **antes do C3** (que copia o `termos.json` para `testes/proibidos.json`), com os casos novos no `termos-casos.json`; as cópias do cérebro, dos Workers e do cliente nascem dela (Fases 3 e 6), e o `proibidos.py` confere que as fontes são iguais. **Revisão (22/10/2026):** fora dos casos, a troca afrouxava o dinheiro ("Câmbio: 5,40.", "O câmbio fechou em 5,40.", "câmbio a 5,40" barravam e passaram a passar); entrou também `c[âa]mbio(?:\s*:\s*\d\|[^\n\d]{0,25}\d{1,2}[.,]\d{2})`, sem tocar na alternativa acima, com 8 casos novos (85 no total; 0 falhas em Python 3 e no Chromium; nenhum caso antigo muda). **Revisão 2 (23/10/2026):** a frase anterior ("ainda passa só o câmbio seguido de número inteiro ou com uma casa") não era verdadeira, e o `\s` saía da linha. Passavam também os números com uma casa ("O câmbio fechou a 5,4.", que barrava antes da emenda) e os com 3 ou mais algarismos antes da vírgula. Barravam a explicação de VHF com lista na linha de baixo (`diga câmbio:\n1. Solte o PTT.`) e o roteiro com a linha seguinte começando por palavra da lista (`CÂMBIO\nDe 2 em 2 minutos, repita o MAYDAY no canal 16.`), que passavam antes da emenda. Agora: a lista é `c[âa]mbio[^\S\n]+(?:do\|…\|oficial)…`, a revisão era `c[âa]mbio(?:[^\S\n]*:[^\S\n]*\d\|[^\n\d]{0,25}\d{1,2}[.,]\d)` (a segunda parte foi trocada na Revisão 3, abaixo) e o LOCAL_SEGURANCA é `sea[- \u00a0\u2010-\u2014]?fire`, que pega também "Sea Fire" com espaço (grafia que a rota `seafire` do cérebro já aceita), o espaço fixo e os hífens tipográficos. Entram 7 casos novos (92 no total; 0 falhas em Python 3 e no Chromium; nenhum dos 85 muda). Na mesma linha e sem palavra da lista, passa o câmbio seguido de número inteiro, sem ':' logo depois da palavra (canal 16; por isso também "O câmbio fechou em 5." e "Câmbio paralelo: 5.") ou de número com 3 ou mais algarismos antes da vírgula (156,800 MHz; por isso também "Câmbio em 100,00 ienes."). Para o canal 16, só o inteiro é necessário; os 3 algarismos são o que deixa passar a frequência. "Câmbio: 16 é o canal de escuta." continua barrando, como antes da emenda: com `\d(?!\d)` depois do ':', passaria também "Câmbio: 150 ienes por dólar." (caso novo que barra), e a trava 13 ganha. Custo: barra também texto de rádio com valor de uma casa em até 25 letras depois de câmbio ("Diga câmbio e aguarde 1,5 min no canal 16."). **Revisão 3 (27/10/2026, revisão final):** (1) cinco das oito palavras da lista não tinham caso que as prendesse (tirar `do`, `da`, `de`, `está` ou `oficial` não reprovava nada, porque a alternativa do dólar ou a do decimal casavam as frases dos casos): entram cinco casos que barram, um por palavra, que só a lista pega ("O câmbio do dia passou de 6.", "O câmbio da semana passou de 6.", "O câmbio de hoje é 6.", "O câmbio está acima de 6.", "O câmbio oficial passou de 6."). (2) o decimal só era barrado se fosse o primeiro número depois de câmbio (`[^\n\d]{0,25}` não aceita algarismo): "Câmbio (14:32): 5,40.", "O câmbio em 23/10 fechou a 5,40." e "O câmbio em 2026 já subiu de 5,10 para 5,40." passavam, brecha na trava 13 que a Revisão 2 não descrevia. A segunda parte da alternativa passa a `(?:[^\n]{0,24}?[^\d\n])?\d{1,2}[.,]\d`: até 25 caracteres da mesma linha entre câmbio e o valor, com algarismos permitidos, e o valor começa logo depois de câmbio ou depois de um caractere que não é algarismo, para que 156,800 não vire 56,8. Barra tudo o que a Revisão 2 barrava (inclusive "Câmbio5,4.", texto sem espaço) e mais o valor depois de data, hora, ano ou contagem; o 156,800 MHz, o canal 16 e os textos de rádio de duas linhas continuam passando. Custo: um número de milhar nos 25 caracteres depois de câmbio ("1.600") também barra, como já barrava, e passam os mesmos "O câmbio fechou em 5." e "Câmbio em 100,00 ienes." da Revisão 2. (3) Sea-Fire: os casos só prendiam o U+2011 do intervalo `\u2010-\u2014`; entram o U+2010, o U+2012, o U+2013 e o U+2014. Casos de borda das regras que mudaram: o decimal a 25 caracteres de câmbio (barra) e a 26 (passa, "Diga câmbio e aguarde, repita a cada 1,5 min."), o 156,800 depois de uma hora (passa), a lista com o número longe (passa), o decimal na linha de baixo (passa), o ponto e os dois algarismos antes da vírgula (barram). Casos: 113 (os 92 mais 21; 0 falhas em Python 3 e no Chromium 141, sem divergência entre eles; nenhum dos 92 muda de resultado). Conferências: 0 diferença contra a Revisão 2 nos blocos de 3 linhas dos arquivos rastreados e da pasta do Avanti (só lida), fora o próprio `termos-casos.json`; Python e Chromium coincidem em 60.000 textos gerados; as oito palavras da lista, o `[.,]`, o 1 ou 2 algarismos, o início fora de número e cada hífen reprovam ao menos um caso quando são tirados ou mudados (a frase da Revisão 3 que dizia o mesmo de "cada parte da regra" era maior do que os casos: ver a Revisão 4). **Revisão 4 (27/10/2026, revisão final):** a janela da lista (24 e 26 em vez de 25), a lista cruzando a linha, o espaço antes e depois do ':' (tirado ou `?`), o `[^\S\n]` trocado por espaço comum e o 'cambio' sem acento não reprovavam nenhum caso (mutantes que escapavam com os 113 casos e 0 falhas). Entram 12 casos (125 no total; 0 falhas em Python 3 e no Chromium 141, sem divergência entre eles; nenhum dos 113 muda de resultado; a regex não muda, nem o `termos.json`). Barram: "O câmbio de " + 24 `x` + "6." (a lista, a 25 caracteres do número); "Câmbio : 150 ienes por dólar."; o mesmo com 2 espaços antes do ':' e com 2 depois; com espaço fixo (U+00A0) antes e depois do ':'; "O câmbio" + espaço fixo + "do dia passou de 6."; e "cambio" sem acento nas duas alternativas ("O cambio do dia passou de 6.", "Cambio: 150 ienes por dólar."). Passam: "O câmbio de " + 25 `x` + "6." (a 26); "Termine com câmbio de" + quebra de linha + "6 passos." (a lista não cruza a linha); "Termine a chamada com CÂMBIO" + quebra + "Espere 1,5 minuto e repita o MAYDAY." (o decimal não cruza a linha, longe do câmbio); "Diga câmbio" + quebra + ": 1 vez e solte o PTT." (o ':' não cruza a linha). Conferência por mutantes: 52 mudanças de uma peça só nas duas alternativas do câmbio (cada palavra da lista, a guarda de letra, cada `[^\S\n]` trocado por `\s` ou por espaço comum, `?` no lugar do `*`, as janelas de 24 e 25, a linha, o início fora de número, o 1 ou 2 algarismos, o `[.,]`, a casa decimal, a alternativa do ':', o acento); 48 reprovam ao menos um caso. Escapam 4, que a regra não pede para prender: o guloso no lugar do preguiçoso (`{0,24}`) e o `[^\n]` no lugar do `[^\n\d]` na janela da lista (equivalentes: 400.000 textos gerados sem nenhuma diferença), o `+` da lista trocado por `*` (só muda "câmbiodo", palavra que não existe) e o `{1,2}` trocado por `{0,2}` (só muda "câmbio,5", sem espaço). **Revisão 5 (27/10/2026, revisão final):** entram 9 casos (134 no total; 0 falhas em Python 3 e no Chromium 141; a regex não muda, nem o `termos.json`). Barram: "Câmbio 5,40." (a janela mínima do decimal), "Câmbio:150 ienes por dólar." (sem espaço depois do ':'), "O câmbio  do dia passou de 6." (dois espaços comuns), "O câmbio está 6." e "O cambio esta acima de 6." (a lista com e sem acento). Passam: "Câmbio paralelo: 5.", "Diga câmbio no canal: 16.", "Diga câmbio: canal 16 em escuta." e "Diga câmbio na versão v.2 do manual." (esta é a que prende o `\d{1,2}` antes do `[.,]`: com `{0,2}` ela passaria a barrar; a explicação anterior, de que o `{0,2}` só mudava "câmbio,5", estava errada). Critério de parada: um mutante de uma peça só que escape tem de ser equivalente ou texto que não existe. |
| 3 | Grafia "Seafire" (sem hífen) em todo dado | manter, como o app usa desde a 1.0.0 |
| 4 | Fabricante dos motores informado (Volvo Penta) → Cummins | trocar: 2.050 rpm a 18 nós é incoerente com a marca nessa potência |
| 5 | Piloto automático de fabricante diferente do dos plotters (Raymarine) | aceitar: direção hidráulica pede piloto hidráulico |
| 6 | `porao-teste` como tarefa de segurança: o s12 ("Nenhuma tarefa de segurança atrasada") fica pendente enquanto o teste estiver atrasado | aceitar: o diário já trata o teste como Segurança (d07) |
| 7 | 19 circuitos por dia, com a posição ~6 % abaixo do SOG (fator 0,9407) | aceitar, ou alongar o circuito para ~16,4 mn no portão manual |
| 8 | FAQ sem o chip de confiabilidade do Avanti e sem os anexos de decisões e divergências | aceitar: todo item vem do guia de bordo gerado |
| 9 | Estabilizador **Seakeeper 3**: 1 ocorrência por substring na pasta do Avanti (exceção ao critério "contagem 0" do §2.5, não à trava §2.10: o modelo não está nas listas privadas). Sem rotação nem minutos do fabricante no guia, na `nominal` e no checklist | aceitar, depois de conferir na folha pública do fabricante, antes do C5, que o modelo cobre 12,4 m e 11,8 t e que a leitura do volante do laço (~10.350 rpm) é plausível; se não cobrir, o proprietário escolhe outro modelo da linha (o gerador recalcula, e a `COLISAO_MODELOS` roda de novo). **Conferido na revisão 2 do C4 (23/10/2026):** cobre os 12,4 m (cerca de 10,5–12,5 m), mas não as 11,8 t (até cerca de 10,5 t na página do fabricante, cerca de 11 t pelo distribuidor), e a nominal é 8.450 rpm. Em vez de trocar o modelo, mudou o dado que é escolha nossa (decisão e): deslocamento 10,4 t (§2.1) e volante 8.420 rpm (§3.1, §1.17, §1.22, no C8). O Seakeeper 3 fica. **Revisão 3 do C4 (23/10/2026):** a conferência da revisão 2 olhou só porte, peso e rotação. O Seakeeper 3 é só 12 V DC (manual de instalação e de operação do fabricante; distribuidor), e o guia mandava ligar com energia AC. O §1, o §2 e o §6 do guia e o checklist de saída passam ao banco de 12 V, que tem o mínimo do fabricante (§1.5, §2.5); a asserção `ESTABILIZADOR_12V` reprova energia AC em texto do estabilizador. O Seakeeper 3 fica. **Revisão 2 do C5 (23/10/2026):** porte, peso, 12 V e rotação nominal conferem de novo, mas a regra do guia "volante a partir de 60 %" contradizia o manual de operação do fabricante (estabilização em cerca de 85 % da rotação de operação). Passa a cerca de 85 % no guia, na `nominal` e no aviso da `LIMITES` (§2.5, §3.3), antes do C8, que nasce desse limite. O Seakeeper 3 fica |
| 10 | Linha do SOS no diário **sem `sim`** (exceção ao §2.9 do PROMPT, pela trava §2.1): com `simulacao: false`, um MAYDAY ou MOB gravado no aparelho de apresentação não vira "apresentação" nem sai da ficha | aceitar. Se o proprietário preferir o `sim` nas linhas do SOS, `D.simulacao` sai da lista do que o SOS não pode ler (§1.3), a microtarefa e o `addDiario` voltam a ler a flag em `/SOS-/`, e a decisão fica registrada no `CLAUDE.md` |
