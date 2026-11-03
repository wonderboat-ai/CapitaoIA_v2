/* Capitão IA — cérebro: atalhos, diário, respostas canônicas, base de bordo e voz.
   Os dados vêm de capitao-dados.js (window.CapitaoDados), com a fonte de cada um (Drive › Capitão IA v2), e do quadro do instante (CapitaoAgora.instante():
   replay, coletor ou snapshot). Com D.simulacao true as respostas saem completas, com número e hora e sem rótulo de dado ausente; com simulacao false volta a
   regra «Nada inventado»: sem dado → SEM DADOS; sensor ausente → SEM LEITURA (o caminho null do dado não se apaga). Foto e nota viram linha A CONFIRMAR no diário.
   Tempo e maré são do mundo real (Open-Meteo); sem conexão, a frase do PROMPT §2.5.
   Pipeline: answer(q, ctx) → route(q) (emergência e óleo no topo) → ANSWERS[chave] { text, src, actions }
             → buscaBase(q) (BM25 com sinônimos PT/EN sobre base-conhecimento.json) → fallback (a IA na nuvem, quando liga).
   IA na nuvem (capitao-ia.js): as telas de chat chamam a IA quando pedeIA(a, q) — pergunta sem rota, trecho do guia ou pergunta sobre o próprio app —,
   mandando a ficha(): o que o app sabe agora, cada bloco com a fonte.
   Emergência, óleo, registro no diário e respostas prontas ficam no aparelho. */
(function () {
  var VERSAO = '1.0.9'; // = VERSAO do capitao-auth.js e do capitao-ia.js (o capitao-app.js recarrega se vierem misturados)
  var norm = function (s) { return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); };
  var has = function (q, list) { return list.some(function (k) { return q.indexOf(k) !== -1; }); };
  var D = window.CapitaoDados || {};
  // No SOS (S1 e S2 carregam este cérebro para gravar no diário e ler os telefones do aparelho), o snapshot fica vazio: nada do dado
  // gerado da embarcação sai de lá (PROMPT §2.1; CONTRATO §1.3). Em /SOS-/ nada aqui lê o snapshot, o replay nem o MMSI gerado.
  var EM_SOS = false; try { EM_SOS = /SOS-/.test(location.pathname); } catch (e) {}
  var E = D.embarcacao || {}, S = EM_SOS ? {} : (D.snapshot || {}), AUT = D.autonomia || {}, CON = D.consumo || {};
  var SD = 'SEM DADOS', SL = 'SEM LEITURA';
  // Decisão 6: a simulação é a flag gerada D.simulacao, lida a cada chamada (nunca guardada na carga) e nunca no SOS. A flag antiga D.demo só põe o rótulo (DEMO) de antes sem a simulação.
  function sim() { return !EM_SOS && D.simulacao === true; }
  function demo() { return D.demo && !sim() ? ' (DEMO)' : ''; }
  function demo_() { return D.demo && !sim() ? ' DEMO' : ''; }   // dentro de parênteses: "(leitura DEMO 26/09 10:12)", sem parêntese aninhado

  var HREF = {
    web: { home: 'Main.dc.html', console: 'A1-Ponte-Web.dc.html', gestao: 'B1-Carta-Web.dc.html', manut: 'C1-Leme-Web.dc.html', docs: 'G1-Documentos-Web.dc.html', abast: 'G2-Abastecimento-Web.dc.html', diario: 'G3-Diario-Web.dc.html', equipe: 'G4-Equipe-Web.dc.html', faq: 'F1-FAQ-Hub-Web.dc.html', f2: 'F2-FAQ-Estabilizador-Web.dc.html', f3: 'F3-FAQ-Eletronicos-Web.dc.html', f4: 'F4-FAQ-Gerador-Web.dc.html', f5: 'F5-FAQ-Climatizacao-Web.dc.html', sos: 'S1-SOS-Web.dc.html', atalhos: 'H3-Atalhos-Editar-Web.dc.html' },
    app: { home: 'H2-Home-Mobile.dc.html', console: 'A2-Ponte-Mobile.dc.html', gestao: 'B2-Carta-Mobile.dc.html', manut: 'C2-Leme-Mobile.dc.html', docs: 'G1-Documentos-Mobile.dc.html', abast: 'G2-Abastecimento-Mobile.dc.html', diario: 'G3-Diario-Mobile.dc.html', equipe: 'G4-Equipe-Mobile.dc.html', faq: 'F1-FAQ-Hub.dc.html', f2: 'F2-FAQ-Estabilizador.dc.html', f3: 'F3-FAQ-Eletronicos.dc.html', f4: 'F4-FAQ-Gerador.dc.html', f5: 'F5-FAQ-Climatizacao.dc.html', sos: 'S2-SOS-Mobile.dc.html', atalhos: 'H3-Atalhos-Editar.dc.html' }
  };

  var DEFAULTS = [
    { id: 'diario', l: 'DIÁRIO DE BORDO', q: 'Registre no diário o resumo da navegação de agora e confirme.' },
    { id: 'seguro', l: 'SEGURO PARA SAIR?', q: 'Avalie vento, mar, motores e pendências — sim ou não, e por quê.' },
    { id: 'destinos', l: 'PARA ONDE VAMOS HOJE?', q: 'Destinos saindo daqui, com distância, tempo e diesel.' },
    { id: 'manutencao', l: 'PRÓXIMAS MANUTENÇÕES', q: 'O que vence primeiro, o que está atrasado, o que falta registrar.' },
    { id: 'autonomia', l: 'AUTONOMIA', q: 'Autonomia com reserva de 10% pelo diesel a bordo.' },
    { id: 'mare', l: 'MARÉ AGORA', q: 'Maré agora e nas próximas 6 h na posição de referência.' }
  ];
  var BANK = [
    { id: 'clima', l: 'CLIMA', q: 'Clima e vento agora e hoje na posição de referência.' },
    { id: 'canal16', l: 'CANAL 16', q: 'Roteiro de chamada no VHF canal 16 com os dados do barco.' },
    { id: 'checklist', l: 'CHECKLIST DE SAÍDA', q: 'Checklist de saída com o que está catalogado a bordo.' },
    { id: 'consumo', l: 'CONSUMO', q: 'Consumo de diesel observado por regime e desde o último abastecimento.' },
    { id: 'tanques', l: 'TANQUES', q: 'Nível de todos os tanques agora.' },
    { id: 'contatos', l: 'CONTATOS', q: 'Equipe, oficina, marina e prestadores — quem chamar.' },
    { id: 'anomalias', l: 'ANOMALIAS ABERTAS', q: 'Anomalias registradas e pendências abertas no diário.' },
    { id: 'porao', l: 'PORÃO', q: 'Situação das bombas de porão e do teste mensal.' },
    { id: 'gerador', l: 'GERADOR', q: 'Como ligar e desligar o gerador e quantas horas ele tem.' },
    { id: 'posicao', l: 'POSIÇÃO AGORA', q: 'Posição, proa e velocidade agora.' },
    { id: 'docsvenc', l: 'DOCUMENTOS VENCENDO', q: 'Quais documentos e licenças vencem primeiro.' },
    { id: 'horimetros', l: 'HORÍMETROS', q: 'Horas dos motores e do gerador e a próxima revisão.' }
  ];
  var ALL = DEFAULTS.concat(BANK);

  var K = { atalhos: 'capitao.atalhos.v1', diario: 'capitao.diario.v1', equipe: 'capitao.equipe.v1', exec: 'capitao.executado.v1', docs: 'capitao.docs.v1', abast: 'capitao.abast.v1' };
  function read(key, fallback) { try { var v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; } }
  function write(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {} }

  function cleanShortcut(x) { return x && typeof x.l === 'string' && typeof x.q === 'string' && x.l.trim() && x.q.trim() ? { id: String(x.id || ('custom-' + Math.random().toString(36).slice(2, 8))), l: x.l.trim().slice(0, 28), q: x.q.trim().slice(0, 240) } : null; }
  function loadShortcuts() {
    var v = read(K.atalhos, null);
    if (Array.isArray(v)) {
      var seen = {}; var list = v.map(cleanShortcut).filter(function (x) { if (!x || seen[x.id]) return false; seen[x.id] = 1; return true; }).slice(0, 8);
      if (list.length || !v.length) return list;
    }
    return DEFAULTS.map(function (x) { return Object.assign({}, x); });
  }
  function saveShortcuts(list) { write(K.atalhos, list); }
  function resetShortcuts() { try { localStorage.removeItem(K.atalhos); } catch (e) {} return loadShortcuts(); }
  function bankFor(list) { var ids = list.map(function (x) { return x.id; }); return ALL.filter(function (x) { return ids.indexOf(x.id) === -1; }); }

  // Usuário logado (capitao-auth.js): CapitaoAuth.nome() devolve quem entrou e manda ao login se a sessão expirou.
  function quem() { if (!window.CapitaoAuth) return 'Lucas'; try { return String(window.CapitaoAuth.nome()); } catch (e) { return 'sem sessão'; } }
  function now() { var d = new Date(); var p = function (n) { return (n < 10 ? '0' : '') + n; }; return { d: p(d.getDate()) + '/' + p(d.getMonth() + 1), t: p(d.getHours()) + ':' + p(d.getMinutes()), iso: d.toISOString() }; }
  // Diário: só cresce. Linhas do app (localStorage, mais nova primeiro) + linhas da fonte (Diário de bordo DEMO no Drive).
  function loadDiario() { var v = read(K.diario, []); return Array.isArray(v) ? v.filter(function (e) { return e && typeof e.t === 'string'; }) : []; }
  function addDiario(e) { return congela(function () { return addDiario1(e); }); }
  function addDiario1(e) { var n = now(); var list = loadDiario(); var entry = Object.assign({ d: n.d, t: n.t, iso: n.iso, sys: 'Diário', tone: 'var(--cap-accent, #00a1fe)', who: quem(), src: 'app · texto' }, e); list.unshift(entry); write(K.diario, list); return entry; }
  function diarioFonte() { return (D.diario || []).map(function (x) { return { d: x.d, h: x.h, t: x.t, iso: x.iso, sys: x.sys, tom: x.tom, who: x.who, pend: !!x.pend, src: (D.diarioFonte || 'diário') }; }); }
  function loadExec() { var v = read(K.exec, {}); return v && typeof v === 'object' && !Array.isArray(v) ? v : {}; }
  function markExec(task) { var m = loadExec(); m[task] = now(); write(K.exec, m); return m; }
  // Desfaz um Executado: relê a lista, tira só essa tarefa e grava (sem a tarefa ou com dado ruim, não grava nada)
  function unmarkExec(task) { var m = loadExec(); if (task != null && Object.prototype.hasOwnProperty.call(m, String(task))) { delete m[String(task)]; write(K.exec, m); } return m; }
  function loadEquipe() { var v = read(K.equipe, null); var o = v && typeof v === 'object' ? v : {}; return { fones: o.fones && typeof o.fones === 'object' && !Array.isArray(o.fones) ? o.fones : {}, convites: Array.isArray(o.convites) ? o.convites.filter(function (c) { return c && typeof c.nome === 'string'; }) : [] }; }
  function saveEquipe(v) { write(K.equipe, v); }
  function loadDocs() { var v = read(K.docs, []); return Array.isArray(v) ? v.filter(function (d) { return d && typeof d.n === 'string'; }) : []; }
  function addDoc(d) { var list = loadDocs(); list.unshift(d); write(K.docs, list); return list; }
  function loadAbast() { var v = read(K.abast, []); return Array.isArray(v) ? v.filter(function (a) { return a && typeof a.n === 'string'; }) : []; }
  function addAbast(a) { var list = loadAbast(); list.unshift(a); write(K.abast, list); return list; }

  // ——— números e textos a partir dos dados ———
  function nb(x, d) { return typeof x === 'number' && isFinite(x) ? x.toFixed(d == null ? 1 : d).replace('.', ',') : '—'; }
  function mil(x) { return typeof x === 'number' ? String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g, '.') : '—'; }
  // litros desde o abastecimento: número com o ponto de milhar (≈ 1.086 L, como o txt do instante e a linha dos abastecimentos); texto (SEM DADOS) como está
  function litrosTxt(n) { return typeof n === 'number' ? mil(n) : n; }
  function grau3(x) { return typeof x === 'number' ? ('00' + Math.round(((x % 360) + 360) % 360)).slice(-3) + '°' : '—'; }
  function horas(x) { if (typeof x !== 'number' || !isFinite(x)) return '—'; var s = x.toFixed(1).split('.'); return mil(+s[0]) + ',' + s[1]; }
  var M = S.motores || {}, G = S.gerador || {}, DI = S.diesel || {}, T = S.tanques || {};
  function montaSnap() { return {
    quando: S.quando || SD, hora: S.hora || '', dia: S.dia || '',
    pos: S.gps && S.gps.texto ? S.gps.texto : 'posição SEM LEITURA',
    local: (S.estado || SD) + ' · ' + (S.local || SD),
    diesel: DI.bb != null ? 'BB ' + nb(DI.bb) + ' % · BE ' + nb(DI.be) + ' % (≈ ' + mil(DI.litros) + ' L de ' + mil(DI.capacidade) + ')' : SD,
    dieselHora: (DI.nota || 'última leitura') + ' · ' + (DI.hora || SD),
    motores: M.rpm ? 'motores ' + (M.estado || 'desligados') + ' — última leitura com motores ligados ' + M.hora + ' (' + (M.marcha || 'neutro') + '): ' + M.rpm.join('/') + ' rpm · óleo ' + M.oleo.map(function (x) { return nb(x); }).join('/') + ' bar · arrefecimento ' + M.arref.join('/') + ' °C' : 'motores: ' + SD,
    fonte: 'coletor NMEA' + demo() + ' · leitura de ' + (S.quando || SD)
  }; }
  var SNAP = montaSnap();
  var FT = {
    tele: 'Fonte: ' + SNAP.fonte,
    agenda: 'Fonte: ' + (D.agendaFonte || 'agenda de manutenção'),
    docs: 'Fonte: ' + (D.docsFonte || 'controle de documentos'),
    abast: 'Fonte: ' + (D.abastFonte || 'registro de abastecimento'),
    diario: 'Fonte: ' + (D.diarioFonte || 'diário de bordo'),
    proto: 'Fonte: ' + ((D.protocolos && D.protocolos.fonte) || 'protocolo de emergência')
  };
  // ——— O instante (CONTRATO §1.23, §1.24; PROMPT Fase 3 «Instante») ———
  // Um instante por pergunta. B.instante() é o do CapitaoAgora (rodapé do capitao-dados.js) com `tend` e `txt` (a tendência dos últimos 30 s e o texto
  // único de cada medida) quando o rodapé ainda não os traz. Fica congelado no começo da chamada mais externa de answer, ficha, answerAttachment,
  // resumoAgora e addDiario e é solto num finally (também com exceção); as chamadas aninhadas (answer → ANSWERS → ficha → …) usam o mesmo. A resposta
  // que sai de uma pergunta leva o instante dela (`_inst`, fora do JSON): a ficha(p, q, a) e o resumoAgora(a) da MESMA pergunta o reaproveitam, mesmo que o
  // relógio tenha andado entre uma chamada e outra. O cérebro deixou de ler o D.snapshot na carga: S, AUT, CON, M, G, DI, T, SNAP e FT.tele são refeitos
  // a cada pergunta por recarrega(), do quadro do instante (replay ou coletor) ou, sem quadro vivo, do D.snapshot aninhado como na 1.0.9 (modo real com
  // simulacao false, tela sem replay): o caminho null → SEM DADOS segue intacto. Em /SOS-/ o instante é nulo antes de qualquer leitura.
  var CONG = { n: 0, inst: null }, CACHE = { base: null, inst: null }, VIVAS = { replay: 1, coletor: 1 };
  var S0 = S, AUT0 = AUT, CON0 = CON;
  // As chaves cuja resposta não lê o quadro (CLAUDE.md 10; PROMPT §2.2, §2.3): sos, canal16, epirb, seafire, salvatagem, mmsi e o `oleo` (queda ou alarme: relato de falha
  // não recebe leitura; a leitura fica no oleoLeitura). A resposta delas NÃO leva o instante (`_inst` tem o quadro, com lat e lon), o resumoAgora(a) delas é a instrução do
  // plotter e a ficha(p, q, a) sai sem os blocos do quadro (QUADRO): a trava é da API, não de cada chamador (a IA, o diário, a CONVERSA).
  var EMERG = { sos: 1, oleo: 1, canal16: 1, epirb: 1, seafire: 1, salvatagem: 1, mmsi: 1 };
  var QUADRO = { 'Telemetria': 1, 'Horímetros': 1, 'Autonomia e consumo': 1 };
  function emerg(a) { return !!a && typeof a === 'object' && EMERG[a.key] === 1; }
  function casas(c) { var d = D.campos && D.campos[c]; return d && typeof d.casas === 'number' ? d.casas : 0; }
  function vivo() { var i = CONG.inst; return i && VIVAS[i.fonte] === 1 && i.q && i.txt ? i : null; }   // o instante com quadro vivo (replay ou coletor)
  function sinal(x, c) { var A = window.CapitaoAgora, v = A.fmt.arred(x, c); return (v > 0 ? '+' : v < 0 ? '−' : '') + A.fmt.nb(Math.abs(v), c); }
  // tendência dos últimos 30 s (CONTRATO §1.23): q(ms) − q(ms − 30 s) do replay, com as casas do D.campos; o diesel é a soma do consumo dos motores e do gerador
  // no mesmo trecho (o quadro arredonda os litros, e em 30 s o consumo fica abaixo de 1 L: 1 casa). Na virada das 07:00 o diesel sai (o abastecimento
  // atravessaria os 30 s); sem replay (coletor sem histórico, reserva) não há tendência.
  var TEND_CAMPOS = ['motor_bb_rpm', 'motor_be_rpm', 'motor_bb_oleo_bar', 'motor_be_oleo_bar', 'motor_bb_arref_c', 'motor_be_arref_c', 'sog_nos'];
  function tendencia(i) {
    var R = window.CapitaoReplay, A = window.CapitaoAgora, o = {}, agora, antes, s = 0, k, q, n = 0;
    if (i.fonte !== 'replay' || !R || typeof R.em !== 'function' || !A || !A.fmt) return undefined;
    try {
      agora = R.em(i.ms); antes = R.em(i.ms - 30000);
      if (!agora || !antes) return undefined;
      TEND_CAMPOS.forEach(function (c) { if (typeof agora[c] === 'number' && typeof antes[c] === 'number') { o[c] = A.fmt.arred(agora[c] - antes[c], casas(c)); n++; } });
      if (i.ms - 30000 >= A.ancora(i.ms)) {
        for (k = 1; k <= 30; k++) { q = R.em(i.ms - k * 1000); if (!q || typeof q.consumo_lph !== 'number') { s = null; break; } s += (q.consumo_lph + ((D.consumo && D.consumo.gerador_lph) || 0)) / 3600; }
        if (s !== null) { o.diesel_litros = A.fmt.arred(-s, 1); n++; }
      }
      return n ? o : undefined;
    } catch (e) { return undefined; }
  }
  // "a 0,5 mn da Barra Sul, chegando": a posição relativa, só com a simulação e só dos pontos com fonte (a rota gerada); nunca coordenada
  function relativaDe(q) {
    var R = D.rota, A = window.CapitaoAgora, pts, wp = null, k, volta, dest, caminho;
    if (D.simulacao !== true || !R || !R.base || typeof q.wp_proximo !== 'string' || typeof q.wp_mn !== 'number') return null;
    pts = [R.base].concat(R.pontos || []);
    for (k = 0; k < pts.length; k++) if (pts[k] && pts[k].nome === q.wp_proximo) { wp = pts[k]; break; }
    if (!wp || !wp.rel) return null;
    volta = !!(R.volta && q.destino === R.volta.nome); dest = !volta && !!(R.destino && q.destino === R.destino.nome);
    caminho = volta ? R.volta.caminho : dest ? R.destino.caminho : null;
    if (!caminho) return null;
    return 'a ' + A.fmt.nb(q.wp_mn, casas('wp_mn')) + ' mn ' + wp.rel + ', ' + ((volta ? wp.id === 'base' : wp.nome === R.destino.nome) ? 'chegando' : caminho);
  }
  // alarmes do instante: o texto único é o da CapitaoAlertas (a lista da faixa, da C3 e do chat: «AVISO: Temperatura do motor BE: 89,6 °C (acima de 88 °C)») quando
  // a tela a traz e o quadro é o do replay (os alarmes dela são os do replay); sem ela, os do próprio quadro, no MESMO molde (rótulo: título: valor (acima|abaixo de limite)),
  // para o texto não mudar conforme o script carregado. O limite leva as casas que ele tem (88, não 88,0), como na CapitaoAlertas.
  function decimais(x) { var t = String(x), k = t.indexOf('.'); return k < 0 ? 0 : Math.min(t.length - k - 1, 3); }
  function alarmesTxt(i) {
    var AL = window.CapitaoAlertas, lista = null, q = i.q.alarmes, F = window.CapitaoAgora.fmt, ale = (D.replay && D.replay.alertas) || {};
    try { if (i.fonte === 'replay' && AL && typeof AL.ativos === 'function') lista = AL.ativos(i.ms); } catch (e) {}
    if (Array.isArray(lista)) return lista.length ? lista.map(function (a) { return a.rotulo + ': ' + a.texto; }).join(' · ') : 'nenhum alarme ativo';
    if (!Array.isArray(q)) return null;   // um coletor que não reporta alarmes não diz «nenhum alarme ativo»: sem o campo não há texto (alarmesCl: a cláusula some na simulação, SEM LEITURA sem ela)
    if (!q.length) return 'nenhum alarme ativo';
    return q.map(function (a) {
      var c = D.campos && D.campos[a.campo], un = c && c.un ? ' ' + c.un : '', ml = !!(c && c.mil), ti = (ale[a.id] && ale[a.id].titulo) || (c && c.rotulo) || a.id;
      var vt = F.nb(a.valor, casas(a.campo), ml), lt = F.nb(a.limite, decimais(a.limite), ml);
      return (a.nivel === 'critico' ? 'CRÍTICO' : 'AVISO') + ': ' + ti + (vt ? ': ' + vt + un + (lt ? ' (' + (a.valor > a.limite ? 'acima' : 'abaixo') + ' de ' + lt + un + ')' : '') : '');
    }).join(' · ');
  }
  // o catálogo de alertas do replay (título, passos e fonte de cada alarme); no SOS nada lê o D.replay
  function catalogoAlertas() { return EM_SOS ? {} : (D.replay && D.replay.alertas) || {}; }
  // o campo do quadro como as telas o mostram (CapitaoAgora.fmt.campo: as casas e o milhar do D.campos), ou null se falta
  function campoTxt(i, c) { try { return window.CapitaoAgora.fmt.campo(i.q, c); } catch (e) { return null; } }
  // os alarmes do instante com o que a resposta de alarmes precisa (título, passos do guia, fonte, hora desde e o detalhe da C3; o texto do alarme é o `txt.alarmes` do instante): a CapitaoAlertas
  // quando a tela a traz e o quadro é o do replay; senão os do próprio quadro com o catálogo D.replay.alertas. null = o quadro não reporta alarmes (um coletor sem o campo).
  function alarmesDetalhe(i) {
    var AL = window.CapitaoAlertas, ativos = null, ale = catalogoAlertas(), F = window.CapitaoAgora.fmt, doQuadro = i.q.alarmes;
    try { ativos = i.fonte === 'replay' && AL && typeof AL.ativos === 'function' ? AL.ativos(i.ms) : null; } catch (e) { ativos = null; }
    if (Array.isArray(ativos)) return ativos.map(function (a) { return { id: a.id, campo: a.campo, titulo: a.titulo, hora: a.hora, passos: (a.passos || []).slice(), fonte: a.fonte, detalhe: a.detalhe }; });
    if (!Array.isArray(doQuadro)) return null;
    return doQuadro.map(function (a) {
      var c = D.campos && D.campos[a.campo], cat = ale[a.id] || {}, ms = Date.parse(a.desde);
      return { id: a.id, campo: a.campo, titulo: cat.titulo || (c && c.rotulo) || a.id, hora: isFinite(ms) ? F.hora(ms, true) : '', passos: (cat.passos || []).slice(), fonte: cat.fonte, detalhe: cat.passos ? 'C3-Leme-Alerta.dc.html#alarme=' + a.id : '' };
    });
  }
  // O texto único de cada medida (CONTRATO §1.23: Main, A1, E1, HUD, answer('telemetria') e `## Navegação agora` mostram este). Só o que o quadro tem; sem coordenada.
  function textos(i) {
    var A = window.CapitaoAgora, F = A.fmt, q = i.q, t = {}, c = i.calc || {}, cp = function (n) { return F.campo(q, n); };
    var com = function (v, suf) { return v === null ? null : v + (suf || ''); };
    var par = function (a, b, suf) { var x = cp(a), y = cp(b); return x !== null && y !== null ? 'BB ' + x + ' · BE ' + y + suf : null; };
    var lig = function (v) { return v === true ? 'ligado' : v === false ? 'desligado' : null; };
    var lado = function (v) { return typeof v === 'number' ? (v < 0 ? ' por bombordo' : v > 0 ? ' por boreste' : '') : ''; };
    var ang = function (n) { var v = cp(n); return v === null ? null : v + '°'; };
    var duo = function (a, b, suf) { var x = cp(a), y = cp(b); return x !== null && y !== null ? x + ' / ' + y + suf : null; };
    t.hora = i.hora;
    t.sog = com(cp('sog_nos'), ' nós'); t.stw = com(cp('stw_nos'), ' nós');
    t.rumo = ang('cog_graus'); t.proa = ang('proa_graus'); t.piloto = ang('piloto_rumo');
    t.leme = typeof q.leme_graus === 'number' ? (F.arred(q.leme_graus, 1) === 0 ? 'no centro' : F.nb(Math.abs(q.leme_graus), 1) + '° a ' + (q.leme_graus < 0 ? 'bombordo' : 'boreste')) : null;
    t.prof = com(cp('profundidade_m'), ' m');
    t.rpm = par('motor_bb_rpm', 'motor_be_rpm', ' rpm'); t.oleo = par('motor_bb_oleo_bar', 'motor_be_oleo_bar', ' bar');
    t.arref = par('motor_bb_arref_c', 'motor_be_arref_c', ' °C'); t.carga = par('motor_bb_carga_pct', 'motor_be_carga_pct', ' %');
    t.consumo = com(cp('consumo_lph'), ' L/h');
    t.diesel = cp('diesel_litros') !== null ? cp('diesel_litros') + ' L' + (typeof c.diesel_pct === 'number' ? ' (' + F.nb(c.diesel_pct, 1) + ' %)' : '') : null;
    t.dieselLados = cp('diesel_bb_pct') !== null && cp('diesel_be_pct') !== null ? 'BB ' + cp('diesel_bb_pct') + ' % · BE ' + cp('diesel_be_pct') + ' %' : null;
    t.distancia = com(cp('distancia_mn'), ' mn');
    t.horimetros = [['motor BB ', 'motor_bb_horimetro_h'], ['motor BE ', 'motor_be_horimetro_h'], ['gerador ', 'gerador_horimetro_h']].filter(function (x) { return cp(x[1]) !== null; })
      .map(function (x) { return x[0] + cp(x[1]) + ' h'; }).join(' · ') || null;
    t.gerador = lig(q.gerador_ativo) ? lig(q.gerador_ativo) + (q.gerador_ativo && cp('gerador_kw') !== null ? ' · ' + cp('gerador_kw') + ' kW' : '') + (cp('gerador_horimetro_h') !== null ? ' · ' + cp('gerador_horimetro_h') + ' h' : '') : null;
    t.seakeeper = lig(q.seakeeper_ativo) ? lig(q.seakeeper_ativo) + (q.seakeeper_ativo && cp('seakeeper_volante_rpm') !== null ? ' · volante ' + cp('seakeeper_volante_rpm') + ' rpm' + (cp('seakeeper_volante_pct') !== null ? ' (' + cp('seakeeper_volante_pct') + ' %)' : '') : '') : null;
    t.b24 = cp('bateria_0_tensao_v') !== null ? 'serviço ' + cp('bateria_0_tensao_v') + ' V' + (cp('bateria_1_tensao_v') !== null ? ' · partida ' + cp('bateria_1_tensao_v') + ' V' : '') : null;
    t.b12 = com(cp('bateria_2_tensao_v'), ' V');
    t.tanques = [['água doce ', 'tanque_agua_pct'], ['cinzas ', 'tanque_cinzas_pct'], ['negras ', 'tanque_negras_pct']].filter(function (x) { return cp(x[1]) !== null; })
      .map(function (x) { return x[0] + cp(x[1]) + ' %'; }).join(' · ') || null;
    t.porao = cp('porao_bb_nivel') !== null && cp('porao_be_nivel') !== null ? 'BB ' + cp('porao_bb_nivel') + ' cm · BE ' + cp('porao_be_nivel') + ' cm' + (typeof q.bomba_porao_ciclos === 'number' ? ' · ' + q.bomba_porao_ciclos + (q.bomba_porao_ciclos === 1 ? ' ciclo' : ' ciclos') + ' da bomba na última hora' : '') : null;
    t.ancora = typeof q.ancora_estado === 'string' ? q.ancora_estado : null;
    t.vento = cp('vento_verdadeiro_nos') !== null && cp('vento_verdadeiro_angulo') !== null ? cp('vento_verdadeiro_nos') + ' nós de ' + cp('vento_verdadeiro_angulo') + '°' : null;
    t.ventoAp = cp('vento_aparente_nos') !== null && typeof q.vento_aparente_angulo === 'number' ? cp('vento_aparente_nos') + ' nós a ' + Math.abs(F.arred(q.vento_aparente_angulo, 0)) + '°' + lado(q.vento_aparente_angulo) : null;
    t.ondas = com(cp('ondas_m'), ' m'); t.pressao = com(cp('pressao_barometrica_hpa'), ' hPa');
    t.ar = com(cp('temp_ar_externo_c'), ' °C'); t.agua = com(cp('temp_agua_c'), ' °C'); t.praca = com(cp('temp_praca_maquinas_c'), ' °C');
    t.inclinacao = cp('jogo_graus') !== null && cp('caimento_graus') !== null ? 'jogo ' + cp('jogo_graus') + '° · caimento ' + cp('caimento_graus') + '°' : null;
    t.local = typeof q.local === 'string' ? q.local : null;
    t.destino = typeof q.destino === 'string' ? q.destino + (cp('destino_mn') !== null ? ' a ' + cp('destino_mn') + ' mn' : '') : null;
    t.wp = typeof q.wp_proximo === 'string' ? q.wp_proximo + (cp('wp_mn') !== null ? ' a ' + cp('wp_mn') + ' mn' : '') : null;
    t.eta = typeof q.eta === 'string' ? q.eta : null;
    t.alarmes = alarmesTxt(i);
    t.relativa = relativaDe(q);
    t.autonomia = c.autonomia ? '≈ ' + F.nb(c.autonomia.horas, 1) + ' h · ≈ ' + c.autonomia.mn + ' mn a ' + ((D.consumo && D.consumo.cruzeiro && D.consumo.cruzeiro.nos) || '—') + ' nós, com reserva de ' + Math.round((typeof D.reserva === 'number' ? D.reserva : 0.1) * 100) + ' %' : null;
    t.desdeAbast = c.desdeAbast ? '≈ ' + F.nb(c.desdeAbast.litros, 0, true) + ' L desde o abastecimento de ' + String(c.desdeAbast.desde || '').slice(0, 5) + (c.desdeAbast.h ? ' às ' + c.desdeAbast.h : '') : null;
    if (i.tend) {
      var d = i.tend, p = [];
      if ('motor_bb_rpm' in d && 'motor_be_rpm' in d) p.push('rpm BB ' + sinal(d.motor_bb_rpm, 0) + ' · BE ' + sinal(d.motor_be_rpm, 0));
      if ('motor_bb_oleo_bar' in d && 'motor_be_oleo_bar' in d) p.push('óleo ' + sinal(d.motor_bb_oleo_bar, 1) + ' / ' + sinal(d.motor_be_oleo_bar, 1) + ' bar');
      if ('motor_bb_arref_c' in d && 'motor_be_arref_c' in d) p.push('arrefecimento ' + sinal(d.motor_bb_arref_c, 1) + ' / ' + sinal(d.motor_be_arref_c, 1) + ' °C');
      if ('sog_nos' in d) p.push('SOG ' + sinal(d.sog_nos, 1) + ' nós');
      if ('diesel_litros' in d) p.push('diesel ' + sinal(d.diesel_litros, 1) + ' L');
      t.tend = p.length ? 'últimos 30 s: ' + p.join(' · ') : null;
    }
    // resumo (diário e contexto da IA): até 300 letras, sem coordenadas; o «sem posição» não leva o local (as exceções da decisão (g))
    var resumo = function (comLocal) {
      var estado = typeof q.estado === 'string' ? q.estado : '', itens = [], fim = ' — ' + i.hora + '.', s, ale = t.alarmes && t.alarmes.indexOf('nenhum') !== 0 ? t.alarmes : null;
      itens.push(comLocal && t.local ? (estado ? estado + ' ' : '') + t.local : estado);
      if (t.sog) itens.push('SOG ' + t.sog);
      if (t.proa) itens.push('proa ' + t.proa);
      if (t.rpm) itens.push('motores ' + t.rpm);
      if (ale) itens.push(ale);
      if (t.diesel) itens.push('diesel ' + t.diesel);
      if (t.oleo) itens.push('óleo ' + t.oleo);
      if (t.arref) itens.push('arrefecimento ' + t.arref);
      if (t.vento) itens.push('vento ' + t.vento);
      if (t.gerador) itens.push('gerador ' + t.gerador.split(' · ')[0]);
      if (t.seakeeper) itens.push('Seakeeper ' + t.seakeeper.split(' · ')[0]);
      if (cp('bateria_0_tensao_v') !== null) itens.push('banco 24 V ' + cp('bateria_0_tensao_v') + ' V');
      s = '';
      itens.filter(Boolean).forEach(function (x) { if ((s ? s + ' · ' + x : x).length + fim.length <= 300) s = s ? s + ' · ' + x : x; });
      return s + fim;
    };
    t.resumo = resumo(true); t.resumoSemPosicao = resumo(false);
    Object.keys(t).forEach(function (k) { if (t[k] === null || t[k] === undefined) delete t[k]; });
    return t;
  }
  // O rodapé guarda o objeto por segundo; a cópia com `tend` e `txt` também (o objeto do rodapé fica como está, outras telas o leem)
  function enriquece(i) {
    var c = {}, k, t;
    if (i.txt) return i;   // o rodapé já traz o texto do instante (a mesma fonte das telas): vale o dele
    if (CACHE.base === i) return CACHE.inst;
    for (k in i) if (Object.prototype.hasOwnProperty.call(i, k)) c[k] = i[k];
    if (c.tend === undefined && (t = tendencia(c))) c.tend = t;
    c.txt = textos(c);
    CACHE.base = i; CACHE.inst = c;
    return c;
  }
  // sem o CapitaoAgora (ou sem quadro nele): a reserva, como antes da 1.1.0 (o D.snapshot aninhado), com fonte `snapshot`
  function instanteReserva() { var sn = D.snapshot || {}; return { ms: Date.now(), q: sn.quadro || null, fonte: 'snapshot', fonteTxt: sn.fonte || '', hora: sn.hora || '', hhmm: sn.hora || '' }; }
  function lerInstante() {
    var A, i;
    if (EM_SOS) return null;   // o SOS não tem instante: nem quadro, nem resumo, nem posição (a guarda é a do rodapé; aqui antes de qualquer leitura)
    try {
      A = window.CapitaoAgora; i = A && typeof A.instante === 'function' ? A.instante() : null;
      if (!i || typeof i !== 'object' || !i.q || typeof i.q !== 'object') return instanteReserva();
      if (i.fonte === 'replay' && D.simulacao !== true) return instanteReserva();   // o rodapé guarda 1 s: a flag pode ter virado depois
      return enriquece(i);
    } catch (e) { return null; }
  }
  function instante() { try { return CONG.n ? CONG.inst : lerInstante(); } catch (e) { return null; } }
  // Congela UM instante na chamada mais externa (`de`: o da resposta que a ficha ou o resumo acompanham) e o solta no finally, também com exceção
  function congela(f, de) {
    if (CONG.n === 0) {
      CONG.inst = de || lerInstante();
      // se a recarrega lança, os dados voltam ao snapshot E o instante também (a reserva): nada de «ao vivo» com o dado de 26/09
      try { recarrega(CONG.inst); } catch (e) { CONG.inst = EM_SOS ? null : instanteReserva(); try { recarrega(null); } catch (e2) {} }
    }
    CONG.n++;
    try { return f(); } finally { if (--CONG.n === 0) CONG.inst = null; }
  }
  function troca(alvo, novo) { var k; for (k in alvo) if (Object.prototype.hasOwnProperty.call(alvo, k)) delete alvo[k]; for (k in novo) if (Object.prototype.hasOwnProperty.call(novo, k)) alvo[k] = novo[k]; }
  // Refaz o que o cérebro lia uma vez na carga. Quadro vivo (replay ou coletor): a forma aninhada de antes, preenchida do quadro do instante;
  // senão o D.snapshot (1.0.9). Em /SOS-/ o S0 é vazio.
  function recarrega(i) {
    var v = i && VIVAS[i.fonte] === 1 && i.q && i.txt ? i : null, q, t, A, cap, lig, ab;
    if (!v) {
      S = S0; AUT = AUT0; CON = CON0;
      M = S.motores || {}; G = S.gerador || {}; DI = S.diesel || {}; T = S.tanques || {};
      troca(SNAP, montaSnap()); FT.tele = 'Fonte: ' + SNAP.fonte;
      return;
    }
    q = v.q; t = v.txt; A = window.CapitaoAgora; cap = E.tanques && E.tanques.diesel_l; lig = q.motor_bb_rpm > 0 || q.motor_be_rpm > 0;
    // quadro parcial (um coletor sem o motor, o gerador, o Seakeeper ou o diesel): o que o quadro não traz fica sem valor (SEM DADOS na resposta), nunca «desligado»
    // nem o dado do snapshot de 26/09 com a fonte do coletor. Com o quadro cheio do replay nada muda.
    var tem = function (x) { return typeof x === 'number' && isFinite(x); }, bool = function (x) { return typeof x === 'boolean'; };
    var temRpm = tem(q.motor_bb_rpm) || tem(q.motor_be_rpm), temHor = tem(q.motor_bb_horimetro_h) || tem(q.motor_be_horimetro_h), temDie = tem(q.diesel_bb_pct) || tem(q.diesel_be_pct) || tem(q.diesel_litros);
    var dieselN = E.tanques && E.tanques.diesel_n ? E.tanques.diesel_n + ' × ' + Math.round(cap / E.tanques.diesel_n) + ' L' : '';
    S = { quando: v.hora, hora: v.hora, dia: '', estado: q.estado, local: q.local,
      gps: { lat: q.lat, lon: q.lon, texto: typeof q.lat === 'number' && typeof q.lon === 'number' ? A.fmt.coord(q.lat, q.lon) : 'posição ' + SD, satelites: q.gps_satelites },
      sog: q.sog_nos, proa: q.proa_graus, profundidade: q.profundidade_m, vento: q.vento_verdadeiro_nos, ventoDe: q.vento_verdadeiro_angulo, pressao: q.pressao_barometrica_hpa,
      ar: q.temp_ar_externo_c, agua: q.temp_agua_c, bat24: q.bateria_0_tensao_v, bat12: q.bateria_2_tensao_v,
      tanques: { agua: q.tanque_agua_pct, cinzas: q.tanque_cinzas_pct, negras: q.tanque_negras_pct },
      diesel: temDie ? { bb: q.diesel_bb_pct, be: q.diesel_be_pct, litros: q.diesel_litros, capacidade: cap, tanques: dieselN, hora: v.hora, nota: 'leitura' } : { capacidade: cap, tanques: dieselN },
      motores: temRpm || temHor ? { hora: v.hora, estado: temRpm ? (lig ? 'ligados' : 'desligados') : undefined, rpm: temRpm ? [A.fmt.campo(q, 'motor_bb_rpm'), A.fmt.campo(q, 'motor_be_rpm')] : undefined,
        oleo: temRpm ? [q.motor_bb_oleo_bar, q.motor_be_oleo_bar] : undefined, arref: temRpm ? [A.fmt.campo(q, 'motor_bb_arref_c'), A.fmt.campo(q, 'motor_be_arref_c')] : undefined,
        horimetro: temHor ? [q.motor_bb_horimetro_h, q.motor_be_horimetro_h] : undefined, marcha: q.marcha } : {},
      gerador: bool(q.gerador_ativo) || tem(q.gerador_horimetro_h) ? { estado: bool(q.gerador_ativo) ? (q.gerador_ativo ? 'ligado' : 'desligado') : undefined, horas: q.gerador_horimetro_h, kw: q.gerador_kw, hora: v.hora } : {},
      seakeeper: bool(q.seakeeper_ativo) ? { estado: q.seakeeper_ativo ? 'ligado' : 'desligado', volante_rpm: q.seakeeper_volante_rpm, volante_pct: q.seakeeper_volante_pct, hora: v.hora } : {},
      porao: { bb_cm: q.porao_bb_nivel, be_cm: q.porao_be_nivel, ciclos_h: q.bomba_porao_ciclos }, ancora: { estado: q.ancora_estado } };
    M = S.motores; G = S.gerador; DI = S.diesel; T = S.tanques;
    // autonomia e «desde o abastecimento» são contas do diesel do instante (calc); sem o diesel no quadro, SEM DADOS (e não a conta do snapshot)
    AUT = v.calc && v.calc.autonomia ? { horas: v.calc.autonomia.horas, mn: v.calc.autonomia.mn, lenta: v.calc.autonomia.lenta } : { horas: null, mn: SD, lenta: SD };
    ab = v.calc && v.calc.desdeAbast;
    CON = Object.assign({}, CON0, { desdeAbast: ab ? { litros: ab.litros, desde: ab.desde, horas: ab.h ? 'desde as ' + ab.h : '' } : { litros: SD, desde: '—', horas: SD } });
    troca(SNAP, { quando: v.hora, hora: v.hora, dia: '', pos: S.gps.texto, local: q.estado || q.local ? (q.estado || SD) + ' · ' + (q.local || SD) : 'estado e local: ' + SD,
      diesel: temDie ? 'BB ' + nb(q.diesel_bb_pct) + ' % · BE ' + nb(q.diesel_be_pct) + ' % (≈ ' + mil(q.diesel_litros) + ' L de ' + mil(cap) + ')' : SD,
      dieselHora: temDie ? DI.nota + ' · ' + DI.hora : SD,
      motores: temRpm ? 'motores ' + M.estado + ' — ' + (t.rpm || '—') + ' · óleo ' + (t.oleo || '—') + ' · arrefecimento ' + (t.arref || '—') : 'motores: ' + SD,
      fonte: v.fonteTxt });
    FT.tele = 'Fonte: ' + SNAP.fonte;
  }
  // a fonte do instante nas respostas de dado de bordo que não passam pelo FT.tele: «telemetria ao vivo · hora» (ou a do coletor), no lugar do «telemetria» do snapshot
  function tele() { return vivo() ? SNAP.fonte : 'telemetria' + demo(); }
  function comTele() { return vivo() ? ' · ' + SNAP.fonte : ''; }
  // quanto falta para o limite de horas da tarefa: o do instante (os horímetros andam) ou, sem quadro vivo, o da agenda
  function faltam(t) { var i = vivo(), f = i && i.calc && i.calc.faltam && i.calc.faltam[t.id]; return typeof f === 'number' ? f : t.horas.faltam; }

  function guia(k) { return (D.guias && D.guias[k]) || SD; }
  function equip(id) { return (D.equipamentos || []).filter(function (e) { return e.id === id; })[0] || null; }
  // "Gerador Onan QD 9" — sempre fabricante e modelo, com o que faltar marcado; o fabricante não se repete quando o modelo já começa
  // por ele ("Estabilizador giroscópico Seakeeper 3", não "Seakeeper Seakeeper 3"), como o equip_de do gerador
  function fabMod(id) {
    var e = equip(id); if (!e) return SD;
    var f = e.fabricante, m = e.modelo;
    return e.nome + (f && m && m.toLowerCase().indexOf(f.toLowerCase()) === 0 ? '' : ' ' + (f || '(fabricante ' + SD + ')')) + (m ? ' ' + m : ' · modelo ' + SD);
  }
  // ——— Prazos em tempo de execução (P3B) ———
  // O dn (dias até o vencimento; negativo = atrasado) é contado da DATA de vencimento contra o dia do INSTANTE no fuso do barco, nunca do dn que o dado traz: o
  // rebase do rodapé o refaz ao carregar e na virada do dia, e uma tela aberta desde ontem sem o replay ficaria um dia atrás. A classificação é a do
  // CapitaoAgora.prazoDe; a tarefa executada (capitao.executado.v1) sai da agenda, como na contagem das telas; a tarefa de um equipamento de segurança (EPIRB,
  // Seafire) vai sem a data e sem o D-n: a nota da etiqueta (CONTRATO §1.4, §6.6 «Revisão do C7»).
  function msAgora() { var i = CONG.inst; return i && typeof i.ms === 'number' ? i.ms : Date.now(); }
  function diaDe(ms) { var A = window.CapitaoAgora, o = -180; try { if (A && typeof A.off === 'function') o = A.off(ms); } catch (e) {} return Math.floor((ms + o * 60000) / 86400000); }
  function diaData(s) {   // 'dd/mm/aaaa' ou 'aaaa-mm-dd' → dia desde 1970; NaN se não for data
    var m = /^(\d\d)\/(\d\d)\/(\d{4})$/.exec(s || ''), n = null;
    if (m) n = [m[3], m[2], m[1]]; else if ((m = /^(\d{4})-(\d\d)-(\d\d)/.exec(s || ''))) n = [m[1], m[2], m[3]];
    return n ? Math.floor(Date.UTC(+n[0], +n[1] - 1, +n[2]) / 86400000) : NaN;
  }
  function dnDe(x) { var n = x ? diaData(x.vence) - diaDe(msAgora()) : NaN; return isNaN(n) ? (x && typeof x.dn === 'number' ? x.dn : NaN) : n; }
  function prazoSt(n) { var A = window.CapitaoAgora; try { if (A && typeof A.prazoDe === 'function') return A.prazoDe(n); } catch (e) {} return { st: n < 0 ? 'ATRASADA' : 'EM DIA' }; }
  function atrasadaN(n) { return !isNaN(n) && prazoSt(n).st === 'ATRASADA'; }
  function seg(t) { var e = t && equip(t.sistema); return !!(e && e.seguranca); }
  function agenda() { var ex = loadExec(); return (D.agenda || []).filter(function (t) { return !ex[t.id]; }).sort(function (a, b) { return (dnDe(a) - dnDe(b)) || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0); }); }
  function atrasadas() { return agenda().filter(function (t) { return atrasadaN(dnDe(t)); }); }
  function tarefa(id) { return (D.agenda || []).filter(function (t) { return t.id === id; })[0] || null; }
  // «executada em 03/11 às 00:38» (a troca, a limpeza, a revisão, a inspeção) ou «executado em …» (o teste, o anodo): o gênero é o do título da tarefa; sem Executado, null
  function execTxt(t) {
    var f = t && loadExec()[t.id];
    return f ? (/^(troca|inspecao|limpeza|revisao|atualizacao|verificacao|manutencao|calibragem|calibracao)\b/.test(norm(t.t || '')) ? 'executada' : 'executado') + ' em ' + f.d + ' às ' + f.t : null;
  }
  function prazoTxt(t) {
    if (!t) return SD;
    var ex = execTxt(t), n = dnDe(t);
    if (ex) return ex;
    if (isNaN(n)) return SD;
    if (atrasadaN(n)) return 'em atraso há ' + (-n) + (n === -1 ? ' dia' : ' dias');
    return seg(t) ? NOTA_ETIQUETA : 'D-' + n + ' · ' + String(t.vence).slice(0, 5);
  }
  // 1ª letra minúscula no meio da frase, menos a sigla («AIS (classe B)» não vira «aIS»)
  function min1(s) { s = String(s || ''); return /^[A-ZÀ-Ý]{2}/.test(s) ? s : s.charAt(0).toLowerCase() + s.slice(1); }
  function pendencias() { return diarioFonte().filter(function (x) { return x.pend; }); }

  // Frase normalizada com espaço nas pontas (palavra inteira = ' x ').
  function pad(s) { return ' ' + norm(s).replace(/[?!.,;:()"“”]+/g, ' ').replace(/\s+/g, ' ').trim() + ' '; }
  // Lista SOS: a de antes mais a ampliação da 1b (PROMPT §2.3; frases de queda de pessoa, perda de governo e água a bordo que a revisão do C5
  // mediu indo à IA, contra a trava "emergência local, nunca na IA"). UMA lista só com a SEGURANCA_PALAVRAS do gerador
  // (ferramentas/demo/confere.py): o testes/cerebro.py confere que as duas são iguais.
  var SOS = ['mayday', 'emergenc', 'incendio', ' fogo', 'homem ao mar', ' mob ', ' sos ', 'socorro', 'naufrag', 'caiu no mar', 'caiu ao mar', 'caiu na agua', 'pessoa na agua', 'alguem na agua', 'crianca na agua', 'afogad', 'afogand',
    'afund', 'entrando agua', 'agua entrando', 'entrada de agua', 'alagad', 'alagand', 'inundad', 'inundand', 'abandon', 'colisao', 'colidi', 'abalro', 'encalh', 'explos',
    'vazamento de combustivel', 'vazando combustivel', 'vazamento de diesel', 'vazando diesel', 'vazamento de gas', 'vazando gas', 'cheiro de combustivel', 'cheiro de diesel', 'cheiro de gas', 'cheiro de queimado',
    // 1b (PROMPT §2.3)
    'alagament', 'afogament', 'inundac', 'adernand', 'adernad', 'adernou', 'emborc', ' ferid', 'machuc', 'se feriu',
    'desmai', 'inconscien', 'infart', 'convuls', 'queimadura', 'choque eletric', 'agua no porao', 'porao cheio', 'porao enchendo',
    'bomba de porao nao para', 'barco virou', 'virou o barco', ' a deriva ', 'monoxido', 'alarme de gas',
    // 1b, revisão do C5: pessoa na água ou fora do barco, água entrando, perda de governo, eixo e mangueira (as frases ficam por inteiro:
    // ' entrou agua ' não pega "entrou aguardando"). A batida ("bateu em…") saiu da lista: ' bateu em ' pegava "bateu em 3 bar"; ver SOS_REGEX, abaixo.
    'caiu do barco', 'caiu da lancha', 'gente na agua', 'homem na agua', 'tripulante na agua', 'pulou do barco', 'pulou da lancha', 'de vista na agua',
    'perdi o leme', 'leme quebrou', 'eixo quebrou', 'quebrou o eixo',
    // 1b, §8.2 item 11 (o subconjunto sem "sem governo" e "água subindo", que pegariam "sem governo federal" e a temperatura da água)
    'alguem caiu', 'caiu alguem', 'crianca caiu', 'tripulante caiu', 'tripulante ao mar', 'crianca ao mar', 'alguem ao mar', 'alguem foi ao mar',
    'perdi o governo', 'perdemos o governo', 'estamos sem governo', 'leme travou',
    // 1b, revisão da revisão: as formas vizinhas que ainda iam à IA. Pessoa que cai (o presente, "pro mar", "para quem caiu"), água a bordo e perda de
    // governo ou eixo. "pro mar" sozinho não entra ("vamos pro mar"): só com o verbo, "caiu pro mar". "pessoa ao mar" fica de fora, como estava.
    ' cai na agua', ' cai no mar', ' cai ao mar', ' cai do barco', ' cai da lancha', 'caiu pro mar', 'caiu pra agua', 'caiu para o mar', 'caiu para a agua', ' para quem caiu', ' de quem caiu', ' ate quem caiu',
    'gente ao mar', 'passageiro ao mar', 'marinheiro ao mar', 'vitima ao mar', 'filho ao mar', 'filha ao mar',
    'agua subindo no porao', 'agua subiu no porao', 'porao subindo', 'bomba do porao nao para', 'bomba nao da conta', 'bombas nao dao conta',
    'bomba sem dar conta', 'bombas sem dar conta', 'porao nao da conta', 'porao sem dar conta',
    'perdemos o leme', 'leme nao responde', 'leme partiu', 'eixo partiu', 'partiu o eixo',
    // 1b, segunda revisão: as formas-espelho que ainda iam à IA. Governo e eixo («quebrou o leme», «leme quebrado»), casco furado, rachado ou aberto,
    // fundo tocado, mais de uma pessoa na água («caíram na água», «caímos do barco»), sangue e hemorragia (o sangramento técnico, «do ar», «do
    // combustível», fica na regex abaixo), fogo sem a palavra fogo (chamas, labaredas, faísca, curto-circuito, cheiro de plástico ou fio queimado)
    'quebrou o leme', 'quebramos o leme', 'quebrei o leme', 'partiu o leme', 'rompeu o leme', 'leme rompeu', 'leme quebrad', 'leme partid',
    'rompeu o eixo', 'furou o casco', 'furaram o casco', 'casco furou', 'casco furad', 'casco rachou', 'casco rachad', 'rachou o casco', 'casco trincou', 'trincou o casco',
    'cairam na agua', 'cairam no mar', 'cairam ao mar', 'cairam do barco', 'cairam da lancha', 'caimos na agua', 'caimos no mar', 'caimos do barco', 'caimos da lancha',
    'hemorrag', 'labared', 'faisc', ' chamas ', 'curto circuito', 'curto-circuito', 'cheiro de queima', 'plastico derretid', 'fumeg', 'dor no peito',
    'sem leme', 'helice quebrou', 'quebrou a helice', 'perdemos a helice', 'perdi a helice', 'helice soltou', 'helice partiu',
    // 1b, quarta revisão: a vizinhança das frases pedidas que ainda ia à IA. Perigo e risco de vida; quem se afoga, não respira, tem parada cardíaca, fratura,
    // ferimento ou passa mal (quebrar, cortar e queimar o corpo, engasgo e «não respira» ficam na regex, com o sujeito: «o motor engasgou» e «o respiro do
    // tanque não respira» são do motor); explosão; perda de governo ou de propulsão; combustível e gás que vazam (a ordem inversa das frases acima)
    ' em perigo ', 'perigo de vida', 'risco de vida', 'perigo de morte', 'risco de morte', 'perdidos no mar', 'perdido no mar',
    'se afogou', 'se afogaram', 'afogou se', 'afogaram se', 'afogou-se', 'afogaram-se', 'parou de respirar', 'parar de respirar', 'sem respirar', 'dificuldade para respirar', 'dificuldade de respirar', 'dificuldade em respirar', 'nao consegue respirar',
    'parada cardi', 'ataque cardi', 'crise cardi', 'ataque do coracao', 'enfart', ' avc ', 'sufoc', 'fratur', 'ferimento', 'hipotermi', 'anafil', 'passando mal', 'passou mal',
    'mal subito', 'desacordad', 'corte profundo', 'corte feio', 'cortou fundo',
    'explod', 'perda de governo', 'perda do governo', 'perda de propulsao', 'perdemos a propulsao', 'perdi a propulsao', 'sem propulsao', ' derivamos ', 'quem caiu',
    ' diesel vazando', ' combustivel vazando', 'gas vazando', 'diesel esta vazando', 'combustivel esta vazando', 'gas esta vazando', 'vazou diesel', 'vazou combustivel', 'vazou gas',
    'diesel no porao', 'combustivel no porao', 'gas no porao', 'cheiro de gasolina'];
  // Frases com contexto, que a lista de palavras não alcança sem pegar o resto: "meu filho está na água", "o passageiro caiu", "alguém foi jogado ao
  // mar", "o barco está tomando água", "bateu numa pedra" (e não "bateu em 3 bar"), "ele está sangrando" (e não "sangrando o ar do sistema").
  // Segunda revisão da 1b: o que a regex alcança vem de LISTA POSITIVA (o que foi atingido: pedra, cais, outro barco, o casco, "nós"; quem está no
  // barco ou na água), nunca de "qualquer coisa menos unidade": «o consumo bateu num recorde», «a pressão bateu num valor alto» e «o dessalinizador
  // está fazendo água» são leitura e equipamento, não emergência. As frases fracas ("bateu forte", "em cheio", "em mim") só valem com o barco,
  // alguém ou ninguém de sujeito (BATE_INI); o casco, o banco e o fundo levam a guarda GUARDA_BATE: onda, vento, chuva, ponteiro, nível, pix ou valor de sujeito não é batida. O que a regex não alcança fica local por outro caminho ou vai ao guia: o
  // sangramento do ar e do combustível, a água do dessalinizador e do ar-condicionado, a água no tanque de água doce.
  // As fontes (`source`) são iguais às do gerador (confere.py: SOS_REGEX): o testes/cerebro.py confere. Sem lookbehind (Safari antigo).
  var PESSOA = '(?:alguem|gente|pessoas?|criancas?|tripulantes?|passageir[oa]s?|marinheiros?|homem|homens|mulher(?:es)?|vitimas?|filh[oa]s?|menin[oa]s?|cara|rapaz|moco|moca)';
  // parente, amigo e quem está a bordo pelo papel: «meu marido caiu na água», «o pai caiu», «perdi o meu amigo de vista». Sem «capitão» (é o nome do app)
  var PARENTE = '(?:idos[oa]s?|amig[oa]s?|colegas?|maes?|pai|marido|esposa|esposo|namorad[oa]s?|irma[o]?|irmaos|netos?|netas?|sobrinh[oa]s?|hospedes?|convidad[oa]s?|mergulhador(?:es)?|nadador(?:es)?|comandante|skipper|vizinh[oa]s?)';
  var DET = '(?:(?:um|uma|o|a|os|as|meu|minha|nosso|nossa|esse|essa) )*';
  var NO_MAR = '(?:no mar|na agua|pro mar|para o mar|pra agua|ao mar)';   // «ao mar» (4ª revisão da 1b): «mulher ao mar», «o tripulante foi ao mar»
  var FORA = '(?:ao mar|no mar|na agua|pro mar|pra agua|para o mar|para fora|pela borda)';
  var CAIU = '(?:cai|caiu|cairam|caem|caindo|pulou|pularam|sumiu|sumiram|desapareceu|desapareceram)';
  var BARCOS = '(?:barco|lancha|embarcacao|iate|bote|veleiro|jet ski|jetski|navio|rebocador|traineira|catamara|escuna|canoa|caiaque|semirrigido)';
  var PARTES = '(?:casco|popa|proa|costado|quilha|helice|leme|bombordo|boreste)';
  var VERBO_BATIDA = '(?:bateu|batemos|bati|bateram|batendo|(?:acabamos|acabei|acabaram|acabou) de bater)';
  var BATE_ADV = '(?:(?:forte|feio|de lado|de frente|de proa|de popa|de raspao|de leve|em cheio|com forca) )*';
  var BATE_EM = '(?:em|n[oa]s?|nu(?:m|ma|ns|mas)) (?:(?:o|a|os|as|um|uma|outro|outra|outros|outras|nosso|nossa|nossos|nossas|meu|minha|esse|essa|aquele|aquela|mesmo|mesma) )*(?:[a-z]+ )?';
  var BATE_COM = '(?:com (?:(?:o|a|um|uma|nosso|nossa|meu|minha) )*(?:' + BARCOS + '|' + PARTES + ')(?: [a-z0-9]+){0,2} )?';
  var DURO_MAR = '(?:pedras?|rochas?|rochedos?|lajes?|baixios?|recifes?|corais?|troncos?|toras?|baleias?|destrocos|containers?)';
  var DURO = '(?:pedras?|rochas?|rochedos?|lajes?|baixios?|cais|troncos?|toras?|piers?|recifes?|costao|ilhas?|muros?|docas?|estacas?|boias?|areia|corais?|pontes?|containers?|objetos?|madeiras?|tocos?|baleias?|destrocos|naufragio)';
  var NAO_BARCO = '(?:ondas?|marolas?|banzeiros?|ressacas?|ventos?|rajadas?|chuvas?|mar|agua|espuma|respingos?|sol|luz|coracao|portas?|janelas?|escotilhas?|tampas?|toldo|bimini|relogio|sino|portao|previsao|palpite|aposta|calculo|estimativa|meta|resultado|nivel|tanques?|ponteiro|medidor|indicador|display|contador|consumo|pressao|temperatura|bateria|tensao|rotacao|horimetro|valor|saldo|pagamento|pix|transferencia|boleto|dinheiro|deposito|salario|conta|fatura|cartao|cheque|fornecedor)';
  var GUARDA_BATE = '^(?!.* ' + NAO_BARCO + ' (?:[a-z0-9]+ ){0,2}(?:bateu|bateram|batendo|batem|bate) ).* ';
  var BATE_FRACO = '(?:forte|feio|de lado|de frente|de proa|de popa|de raspao|de leve)';
  // as frases fracas («bateu forte», «bateu em cheio», «bateu em mim») só valem sem sujeito ou com o barco, alguém, «ele» ou «nós» («a gente») de sujeito:
  // «o motor bateu forte» (batendo pino), «o preço bateu em cheio» e «o vento bateu em mim» não são batida
  var BATE_INI = '^ (?:(?:ai|agora|la|acabou de|acabaram de|acho que|parece que|entao|olha|gente) )*(?:(?:(?:o|a|um|uma|nosso|nossa|outro|outra|esse|essa|aquele|aquela) )*(?:' + BARCOS + '|alguem|ele|ela|eles|elas|isso|nos)(?: [a-z0-9]+){0,5} )?';
  var SUJ_BARCO = '(?:barco|lancha|casco|embarcacao|iate|bote|veleiro|porao|estamos|nos)';
  // Guardas de água a bordo (revisão da revisão da 1b): LOCAIS, presas ao verbo, não à frase inteira. Quem relata alagamento cita o que molhou («entrou água no
  // barco e molhou o celular», «estamos fazendo água e a geladeira parou»): uma palavra de contexto em qualquer lugar da frase não pode calar o SOS.
  // (1) o equipamento que «faz água» é o SUJEITO do verbo, logo antes dele («a geladeira está fazendo água», «o ar-condicionado do barco faz água»); a geladeira
  // que parou numa oração e o barco que faz água na outra é alagamento.
  var EQUIP_AGUA = '(?:dessalin[a-z]*|ar condicionado|[a-z]*-?condicionad[a-z]*|climatiza[a-z]*|ar|geladeira|frigobar|freezer|bebedouro|purificador|chuveiro|torneira|ducha|pia|ralo|sanitario|banheiro|lavabo|gelo)';
  var VERBO_AGUA = '(?:fazendo|faz|fez|fazer|tomando|toma|tomou|tomar|puxando|puxou|puxar|pegando|pega|pegou|pegar)';
  var SEM_EQUIP_AGUA = '^(?!.* ' + EQUIP_AGUA + '(?: d[oae]s? [a-z0-9]+(?: d[oae]s? [a-z0-9]+)?)?(?: (?:esta|estao|ta|tao|vai|ficou|comecou a|continua|ainda|agora|so|tambem))* ' + VERBO_AGUA + ' ).* ';
  // (2) a água que não é a do casco vem logo DEPOIS da palavra «água» («água doce», «água no ouvido», «na bota», «no tanque de água», «na geladeira»)
  var AGUA_FIM = '(?!(?:doce|potavel|quente|fria|gelada|mineral|filtrada|com|para|pro|pra)\\b)';
  var AGUA_ENTRA_FIM = '(?!(?:doce|potavel|quente|fria|gelada|mineral|filtrada)\\b)(?!(?:n[oa]s?|em|pel[oa]s?|dentro d[oa]s?) (?:olhos?|ouvidos?|nariz|boca|botas?|sapatos?|tanques? de agua|celular|telefone|geladeira|frigobar|freezer|pia|chuveiro|torneira|filtro|purificador|bebedouro|garrafa|copo|mala|mochila|bolsa|dessalin[a-z]*|ar condicionado|ar-condicionado|climatiza[a-z]*) )';
  // «a temperatura da água subindo no barco» (e a pressão, a salinidade, a vazão) é leitura, não alagamento
  var SEM_MEDIDA_AGUA = '^(?!.* (?:temperatura|pressao|salinidade|vazao|fluxo) d[ae] agua ).* ';
  var LUGAR_BORDO = '(?:barco|lancha|embarcacao|casco|porao|cabine|salao|camarote|sala de maquinas|casa de maquinas|praca de maquinas|iate|bote|veleiro)';
  // a âncora (o ferro, a poita, a corrente, a sonda, o ponteiro) que «toca o fundo» ou «raspa numa pedra» é fundeio de rotina, não batida do barco
  var SEM_ANCORA = '^(?!.* (?:ancoras?|ferro|poita|corrente|amarra|cabo|chumbo|prumo|sonda|ecobatimetro|ponteiro|mergulhador|ancorote)(?: [a-z0-9]+){0,3} (?:tocou|tocaram|raspou|esbarrou|encostou) ).* ';
  // a mangueira de uso (lavagem, chuveiro, pia, ar-condicionado…) traz o uso JUNTO da palavra «mangueira» (local, não a frase inteira: «a mangueira de combustível estourou e molhou a pia» é emergência)
  var MANGUEIRA_USO = '(?:lavagem|lavar|chuveiro|ducha|pia|torneira|jardim|piscina|geladeira|frigobar|bebedouro|[a-z]*-?condicionad[a-z]*|climatiza[a-z]*)';
  // sangramento técnico (o ar, o combustível, as linhas, o sistema…) não é ferimento: «sangrando o ar do sistema», «sangramento do combustível»
  var TECNICO = '(?:(?:o|a|os|as|um|uma|do|da|dos|das|no|na) )?(?:ar|combustivel|diesel|sistema|linhas?|bombas?|circuito|filtros?|racor|arrefecimento|freios?|radiador|tubulacao|injetor[a-z]*|bicos?|pre-?filtros?|respiro|aquecedor|turbo|embreagem|direcao|reversor|atuador|cilindro|tanques?|separador|decantador|motor|motores|gerador|hidraulic[a-z]*|oleo|cano|tubo|valvulas?|mangueiras?)';
  var ALVO_FOGO = '(?:motor|motores|painel|quadro|fio|fios|cabo|cabos|bateria|baterias|gerador|compressor|inversor|carregador|tomada|isolamento|resistencia)';
  // 1b, quarta revisão: o corpo de quem quebra, corta, queima ou prende (sem «cabeça»: «queimar a cabeça» é pensar demais) e o sujeito de quem se engasga ou não respira
  var CORPO = '(?:bracos?|pernas?|maos?|dedos?|costelas?|nariz|ombros?|joelhos?|tornozelos?|pulsos?|punhos?|claviculas?|bacia|coluna|pescoco|dentes?|rosto|testa|barriga|olhos?|pele|costas|antebraco|lingua|boca|garganta|pes?)';
  var POSSE = '(?:(?:o|a|os|as|meu|minha|seu|sua|um|uma|nosso|nossa) )*';
  // o «braço» (e o «pé», a «mão») de uma peça de bordo não é o de uma pessoa: «quebrou o braço do guincho»
  var PECA = '(?!d[oae]s? (?:guincho|limpador|radar|guindaste|davit|mesa|cadeira|banco|tripe|suporte|apoio|lanterna|mastro|ancora|piloto|motor|porta|escotilha|antena|toldo|bimini|sofa|gaveta|armario|cabo|leme|gerador|painel|plotter) )';
  var ELE = '(?:' + PESSOA + '|' + PARENTE + '|ele|ela|eles|elas|ninguem|bebe)';
  var SOS_REGEX_FONTES = [
    ' ' + PESSOA + '(?: (?:esta|estao|ta|tao|foi|foram|ficou|ficaram))? ' + NO_MAR + ' ',
    ' (?:' + PESSOA + ' ' + CAIU + '|' + CAIU + ' ' + DET + PESSOA + '|(?:perdi|perdemos|perdeu|perderam) de vista ' + DET + PESSOA +
      '|(?:perdi|perdemos|perdeu|perderam) ' + DET + '(?:tripulantes?|marinheiros?|criancas?|filh[oa]s?|menin[oa]s?)' +
      '|(?:perdi|perdemos|perdeu|perderam) ' + DET + PESSOA + ' de vista|' + PESSOA + ' (?:que|q) ' + CAIU + ') ',
    ' (?:' + PARENTE + ' ' + CAIU + ' (?:na agua|no mar|ao mar|do barco|da lancha|da embarcacao|pro mar|para o mar|pra agua|para fora|fora)|(?:perdi|perdemos|perdeu|perderam) de vista ' + DET + PARENTE +
      '|(?:perdi|perdemos|perdeu|perderam) ' + DET + PARENTE + ' de vista|' + PARENTE + ' (?:que|q) ' + CAIU +
      '|' + PARENTE + ' (?:esta|estao|ta|tao|foi|foram|ficou|ficaram) ' + NO_MAR + ') ',
    ' (?:derrubou|jogou|empurrou|arrastou|derrubaram|jogaram|empurraram) ' + DET + PESSOA + ' ' + FORA + ' ',
    ' ' + PESSOA + ' (?:foi|foram) (?:jogad[oa]s?|derrubad[oa]s?|arrastad[oa]s?|empurrad[oa]s?) ' + FORA + ' ',
    // água a bordo: o barco ou "nós" fazendo/tomando água, ou «fazendo água» sem sujeito (não a água doce, quente ou potável; não o equipamento que faz água: a guarda
    // olha só o sujeito do verbo, nunca a frase inteira)
    SEM_EQUIP_AGUA + SUJ_BARCO + '(?: [a-z0-9]+){0,3} ' + VERBO_AGUA + ' (?:muita |bastante |demais )?agua ' + AGUA_FIM,
    SEM_EQUIP_AGUA + 'estou(?: [a-z0-9]+){0,2} (?:fazendo|fazer) (?:muita |bastante |demais )?agua ' + AGUA_FIM,
    SEM_EQUIP_AGUA + 'fazendo (?:muita |bastante )?agua ' + AGUA_FIM + '(?!(?:de|na boca)\\b)(?!n[oa]s? (?:pia|chuveiro|banheiro|lavabo|sanitario|torneira|ducha|ralo|geladeira|frigobar|freezer|copa) )',
    ' fazendo agua (?:no|na|pelo|pela|pelos|pelas|em) (?:porao|casco|fundo|quilha|popa|proa|costado|eixo|helice|leme|casa de maquinas|sala de maquinas|praca de maquinas|passa casco|passacasco|valvula|gaveta) ',
    ' (?:entrou|comecou a entrar|comecando a entrar|voltou a entrar|comecaram a entrar) (?:muita |bastante |mais )?agua ' + AGUA_ENTRA_FIM,
    ' agua (?:entrou|comecou a entrar|comecou a subir) ' + AGUA_ENTRA_FIM,
    ' agua (?:(?:esta|ta|vem|continua|segue|estava|tava) )?(?:a )?entrando ' + AGUA_ENTRA_FIM,
    ' entrando (?:(?:muita|bastante|tanta|mais) )+agua ' + AGUA_ENTRA_FIM,
    ' (?:nao|n) (?:para|parou) de entrar agua ',
    ' agua (?:nao|n) (?:para|parou) de entrar ',
    SEM_MEDIDA_AGUA + 'agua (?:esta |ta )?(?:subindo|subiu|sobe|enchendo|encheu) (?:(?:rapido|rapidamente|muito|bem|bastante|demais|mais) )*(?:no|na|dentro d[oa]|em) (?:barco|lancha|embarcacao|cabine|salao|camarote|sala de maquinas|casa de maquinas|praca de maquinas) ',
    ' (?:tem|ha|tinha|temos) agua dentro d[oa] (?:barco|lancha|embarcacao|casco|cabine|salao|camarote|sala de maquinas|casa de maquinas|praca de maquinas) ',
    ' ' + LUGAR_BORDO + '(?: (?:esta|ta|ficou|foi|vai|comecou a))? (?:cheio|cheia|enchendo|encheu|encher) (?:de|com) agua (?!(?:doce|potavel|quente|fria|gelada|mineral|filtrada)\\b)',
    // porão (PROMPT §2.2: o relato do porão é sos): cheio, enchendo, alagando ou subindo com «está/tá» no meio; a água que sobe ou entra no porão; a bomba que não para ou não dá conta;
    // o alarme do porão que disparou (relato; «testar o alarme de porão» e «nível normal do porão» seguem a rota do porão)
    ' porao (?:esta |ta |continua |vai |ja |ficou |foi )?(?:cheio|cheia|enchendo|encheu|alagando|alagado|alagou|subindo|subiu|inundado|inundou|transbordando|transbordou) ',
    ' agua (?:esta |ta |vem )?(?:subindo|entrando|enchendo|vazando|aparecendo|surgindo|brotando) (?:no|pelo|pelos|dentro d[oa]|do) porao ',
    ' bombas? (?:de |do |da )?porao (?:(?:nao|n) (?:esta |estao |ta |tao )?(?:para|param|parando|desliga|desligam|desligando|da conta|dao conta|dando conta|consegue|conseguem|conseguindo|segura|seguram|vence|vencem|aguenta|aguentam)|(?:esta|estao|ta|tao) (?:ligad[oa]s?|funcionando|trabalhando|rodando|acionad[oa]s?) (?:direto|sem parar|o tempo todo|toda hora|toda a hora)) ',
    // (4ª revisão: até 3 palavras entre «alarme» e «porão» — «alarme de nível do porão», «alarme do painel do porão» —, e o alarme que tocou NO porão)
    ' (?:alarme|alerta|sirene)(?: [a-z0-9]+){0,3} porao (?:disparou|tocou|soou|acendeu|acionou|ativou|(?:esta|ta) (?:tocando|soando|disparando|disparado|aceso)|tocando|soando|disparando) ',
    ' (?:disparou|tocou|soou|acendeu|acionou|ativou) (?:o |um |a )?(?:alarme|alerta|sirene)(?: [a-z0-9]+){0,3} porao ',
    ' (?:alarme|alerta|sirene) (?:disparou|tocou|soou|acendeu|acionou|ativou) (?:no|do|na|dentro d[oa]) porao ',
    // a frase inteira «alarme do porão» (quem digita só o substantivo): relato, local
    '^ (?:(?:o|um|esse|aquele) )?alarme (?:d[eoa]s? )(?:bombas? (?:d[eo] )?)?porao $',
    // o barco que toca o fundo (a âncora, o ferro, a poita, a corrente e a sonda tocam o fundo no fundeio: SEM_ANCORA)
    SEM_ANCORA + '(?:tocou|tocamos|toquei|tocaram|raspou|raspamos|raspei|encostou|encostamos|encostei) (?:o|no) fundo ',
    // batida: o que foi atingido vem de lista positiva (coisa dura, outro barco, o casco, "nós")
    ' ' + VERBO_BATIDA + ' ' + BATE_ADV + BATE_COM + BATE_EM + DURO + ' ',
    SEM_ANCORA + '(?:raspou|raspamos|raspei|esbarrou|esbarramos|esbarrei|tocou|tocamos|toquei|encostou|encostamos|encostei) ' + BATE_ADV + BATE_COM + BATE_EM + DURO_MAR + ' ',
    // o barco que está em cima da pedra e a batida que vem aí («vamos bater», «vamos bater numa pedra», «prestes a colidir»)
    ' (?:estamos|ficamos|paramos|fiquei|parei|ficou|parou) (?:em cima d[eao]|sobre|em|n[oa]s?|nu(?:m|ma)) (?:(?:um|uma|o|a|essa|aquela) )*(?:pedras?|rochas?|rochedos?|lajes?|baixios?) ',
    ' (?:vamos|vai|iremos) bater (?:(?:forte|feio|em cheio) )?(?:em|n[oa]s?|nu(?:m|ma|ns|mas)) (?:(?:o|a|um|uma|outro|outra|essa|aquela) )*(?:' + DURO + '|' + BARCOS + '|' + PARTES + ') ',
    '^ (?:(?:ai|gente|socorro|cuidado|meu deus|nossa) )*(?:vamos|vai) bater(?: (?:forte|feio))? $',
    ' (?:prestes a|quase) (?:colidir|encalhar|afundar|naufragar|virar|alagar) ',
    GUARDA_BATE + VERBO_BATIDA + ' ' + BATE_ADV + BATE_COM + BATE_EM + '(?:' + BARCOS + '|' + PARTES + '|bancos?|fundo|algo|alguma coisa|alguem) ',
    BATE_INI + VERBO_BATIDA + '(?: ' + BATE_FRACO + ')* (?:em nos|em mim|na gente|em cheio) ',
    ' (?:batemos|bati)(?: (?:' + BATE_FRACO + '|em cheio))* $',
    BATE_INI + '(?:bateu|bateram)(?: ' + BATE_FRACO + ')+ $',
    ' (?:atingid|colhid|prensad)[oa]s? por (?:(?:um|uma|o|a|outro|outra) )*(?:' + BARCOS + '|raio) ',
    // ferimento: sangramento, sangrar, sangue (o técnico, "do ar" e "do combustível", não)
    ' sangramento (?!' + TECNICO + ' )',
    ' sangr(?:a|ando|ou|am|aram|ava|avam) (?!' + TECNICO + ' )',
    ' (?:parar de|para de|pare de|parou de|comecou a|continua a|continuou a|voltou a) sangrar ',
    ' sangrar (?:muito|sem parar|bastante|demais) ',
    '^(?!.* (?:tipo|exame|exames|doacao|doar|doador|teste|testes|pressao|laboratorio|azul) )(?!.* sangue frio ).* sangue ',
    // casco aberto («rombo no casco», «o casco está furado», «rachadura no casco») e pancada na cabeça
    ' rombo (?:no|na) (?:casco|barco|lancha|embarcacao|costado|proa|popa|fundo|quilha) ',
    ' casco (?:esta |ta |ficou |foi )?(?:furad[oa]|rachad[oa]|trincad[oa]|rompid[oa]|aberto|amassad[oa]|danificad[oa]) ',
    ' (?:rachadura|trinca|fissura|buraco|furo|rasgo) (?:no|na) (?:casco|costado|quilha|popa|proa) ',
    ' (?:bateu|bati|bateram|batemos) (?:com )?(?:a|na|no|o) (?:cabeca|nuca|testa) ',
    // fogo sem a palavra "fogo": chama, queimando o motor ou o painel, choque no painel
    ' (?:uma|vi|vimos|vejo|surgiu|apareceu|saindo|sai|saiu|tem|temos|ha|tinha|teve|pegou|pegando|muita|alguma) chama (?!(?:d[eoa]|n[oa]) (?:fogao|fogareiro|churrasqueira|cooktop|isqueiro|vela|piloto|macarico) )',
    ' chama (?:n[oa]s?|d[oa]s?|em|pel[oa]s?) (?:motor|motores|painel|quadro|fio|fios|cabo|cabos|bateria|baterias|gerador|compressor|inversor|carregador|tomada|geladeira|barco|lancha|casco|cozinha|cabine|camarote|praca de maquinas|sala de maquinas|casa de maquinas|popa|proa|conves|iate|veleiro|bote|lixeira) ',
    ' (?:motor|motores|painel|quadro|fio|fios|cabo|cabos|bateria|baterias|gerador|barco|lancha|cozinha|fogao|casco|compressor|bomba|inversor|carregador|tomada|geladeira|cabine|camarote|praca de maquinas|sala de maquinas|casa de maquinas|isolamento|resistencia|ar condicionado)(?: [a-z0-9]+){0,2} queimando (?!(?:oleo|diesel|combustivel|muito|pouco|mais|menos|litros?|[0-9]+) )',
    ' queimando (?:(?:o|os|a|as) )?' + ALVO_FOGO + ' ',
    ' (?:levou|tomou|tomei|levei|levando|tomando) (?:um |o )?choque ',
    ' (?:tomada|painel|quadro|cabo|fio|fios|bateria|carregador|inversor|casco|corrimao|motor|gerador|torneira|chuveiro|pia|geladeira|barco|lancha|agua|cais|pier)(?: [a-z0-9]+){0,2} (?:dando|deu|da) (?:um |o )?choque ',
    ' choque (?:no|na|do|da|de|pelo|pela) (?:painel|quadro|cabo|fio|fios|bateria|baterias|barco|motor|gerador|tomada|inversor|carregador|casco|agua|mar) ',
    ' cheiro (?:de |do |da |no |na )?(?:[a-z]+ ){0,2}queimad[oa]s? ',
    // mangueira que estoura, solta ou fura (não a de lavagem, a do chuveiro nem a do ar-condicionado); eixo que quebra
    ' mangueira(?: (?!' + MANGUEIRA_USO + ' )[a-z0-9-]+){0,4} (?:estourou|estourada|soltou|rompeu|rompida|furou|furada|partiu|rasgou) ',
    ' (?:estourou|soltou|rompeu|furou|partiu|rasgou) (?:a|uma|essa|aquela|nossa|minha) mangueira (?!(?:(?:d[eoa]s?|para|pra) )?' + MANGUEIRA_USO + ' )',
    ' eixo(?: [a-z0-9]+){0,6} (?:quebrou|quebrado|quebrada|partido|rompeu|empenou) ',
    ' eixo(?: [a-z0-9]+){0,3} partiu ',
    ' eixo(?: [a-z0-9]+){0,3} (?:soltou|solto|solta|travou|travado|travada|emperrou|emperrado|emperrada|entortou|torto|empenado|empenada|rachou) ',
    // leme com palavras no meio («o leme do barco quebrou», «o leme da lancha travou agora») e o leme perdido («perdi totalmente o leme»)
    ' leme(?: [a-z0-9]+){0,5} (?:quebrou|quebrado|quebrada|partido|partida|rompeu|rompido|rompida|travou|travado|travada|soltou) ',
    ' leme(?: [a-z0-9]+){0,3} partiu ',
    ' leme(?: [a-z0-9]+){0,3} (?:emperrou|emperrado|emperrada|preso|presa|caiu|saiu|desprendeu|falhou|bloqueou|bloqueado|bloqueada|enroscou|enroscado|enroscada|sumiu) ',
    ' helice(?: [a-z0-9]+){0,3} (?:enroscou|enroscada|enroscado|travou|travada|travado|soltou|solta|solto|quebrou|quebrada|quebrado|partiu|partida|partido|emperrou|emperrada|emperrado|bloqueou|bloqueada|bloqueado|perdeu|danificou|danificada|danificado|amassou|amassada|amassado|entortou|entortada|entortado) ',
    ' (?:perdi|perdemos) (?:(?:totalmente|completamente|de vez|agora|todo|toda|todos|o|a|os|as|dois|duas|ambos) )*(?:leme|governo|controle do leme|comando do leme|controle do barco|controle da lancha|controle da embarcacao|direcao|timao|propulsao|motor|motores|helice|helices) ',
    // o barco que não obedece ao leme, que não governa, que está sem controle; os dois motores que pararam; o vento ou a corrente que levam o barco às pedras
    ' (?:nao|n) (?:obedece|responde|reage|atende) (?:mais )?(?:ao |a |o |no |na )?(?:leme|timao|direcao|governo) ',
    ' (?:nao|n) (?:governa|governando|governou|esta governando) ',
    ' (?:estamos|ficamos|barco|lancha|embarcacao|iate|bote|nos)(?: (?:esta|ta|ficou))? (?:totalmente |completamente )?(?:sem controle|fora de controle|descontrolad[oa]s?) (?!remoto|d[oa] (?:ar|tv|som))',
    ' (?:os )?(?:dois|2|ambos os|ambos|todos os) motores (?:pararam|apagaram|morreram|falharam|travaram|pifaram) ',
    ' (?:estamos|ficamos|estou|fiquei) derivando ',
    ' (?:vento|corrente|correnteza|mare|mar|ondas?|deriva)(?: [a-z0-9]+){0,3} (?:levando|levou|jogando|jogou|empurrando|empurrou|arrastando|arrastou|joga|leva|empurra|arrasta) (?:(?:nos|a gente|o barco|a lancha|a embarcacao) )?(?:para|pra|contra) (?:as |a |os )?(?:pedras?|rochas?|costao|laje|lajes|recifes?|rebentacao|arrebentacao|baixios?) ',
    // água que entra no presente («entra água pelo casco») e a baliza disparada pela frente do verbo («disparou a baliza», «acionei a baliza»)
    ' entra agua (?:pel[oa]s?|por|no|na|em) (?:casco|barco|lancha|porao|cabine|fundo|quilha|popa|proa|costado|eixo|helice|leme|vigia|escotilha|janela|sala de maquinas|casa de maquinas|praca de maquinas|todo lado|todos os lados|tudo) ',
    // 1b, quarta revisão. O corpo: quebrar, luxar, cortar, queimar, esmagar, prender («quebrou o braço», «cortou a mão feio», «queimou a mão no escapamento», «prendeu a mão
    // no cabo»), o membro que fica quebrado, cortado ou queimado, e quem foi atingido («o cabo estourou e acertou alguém»)
    ' (?:quebrou|quebrei|quebraram|fraturou|fraturei|luxou|luxei|deslocou|desloquei|cortou|cortei|cortaram|queimou|queimei|queimaram|esmagou|esmagaram|amassou|prendeu|arrancou) ' + POSSE + CORPO + ' ' + PECA,
    ' ' + CORPO + '(?: (?:esta|estao|ta|tao|ficou|ficaram|foi|foram))? (?:quebrad[oa]s?|fraturad[oa]s?|luxad[oa]s?|deslocad[oa]s?|cortad[oa]s?|queimad[oa]s?|esmagad[oa]s?|prensad[oa]s?) ',
    ' (?:acertou|atingiu|esmagou|prendeu|machucou) ' + POSSE + '(?:alguem|pessoa|tripulante|passageiro|marinheiro|crianca|homem|mulher|cara|filho|filha) ',
    ' (?:me queimei|se cortou|me cortei) ',
    // quem se engasga e quem não respira (o sujeito é pessoa: «o motor engasgou» e «o respiro do tanque não respira» são do motor)
    ' ' + ELE + ' (?:(?:esta|estao|ta|tao|se) )*engasg(?:ad[oa]s?|ou|ando|aram) ',
    ' ' + ELE + '(?: [a-z]+)? (?:nao|n) (?:(?:esta|estao|ta|tao|consegue|conseguem) )?(?:respira|respirando|respirar) ',
    // combustível e gás: o tanque, a linha ou o vazamento por dentro («o tanque de diesel está vazando», «vazamento no tanque de diesel», «cheiro forte de gás»); o tanque
    // de água doce que vaza não entra
    ' tanque d[eo] (?:diesel|combustivel)(?: [a-z0-9]+){0,3} (?:vazando|vazou|vaza|furou|furado|furada|rachou|rachado|rachada|trincou|trincado|trincada|rompeu|rompido|rompida) ',
    ' vazamento (?:no|na|nos|nas|do|da|dos|das|de|em)(?: [a-z0-9]+){0,3} (?:diesel|combustivel|gas|gasolina) ',
    ' cheiro (?:(?:forte|muito|intenso|estranho|esquisito|ruim) )+(?:de |do |da )?(?:gas|diesel|combustivel|gasolina|queimado|fumaca) ',
    // pedido de ajuda urgente («preciso de ajuda urgente», «preciso urgente de ajuda»)
    ' (?:ajuda|socorro|auxilio|resgate)(?: [a-z]+){0,2} urgente ',
    ' urgente(?: [a-z]+){0,2} (?:ajuda|socorro|auxilio|resgate) '
  ];
  var SOS_REGEX = SOS_REGEX_FONTES.map(function (f) { return new RegExp(f); });
  // "a gente" é "nós", não a pessoa de "gente na água"/"gente cai": troca por "nos" antes de conferir
  function emergencia(q) {
    q = q.split(' a gente ').join(' nos ');
    return has(q, SOS) || SOS_REGEX.some(function (r) { return r.test(q); }) || (has(q, ['fumaca']) && !has(q, ['escap'])); // fumaça no escapamento é do motor, não SOS
  }
  // Rota salvatagem (PROMPT §2.3): ' boia ' só sem as palavras de boia de sinalização (amarra, poita, canal, baliza, cardinal, luz) nem de boia de
  // nível ou de âncora (revisão da 1b: a boia do porão, a do tanque e a de ancoragem não são salvatagem); "extintor" aqui sem fogo, fumaça nem
  // incêndio (com eles a SOS já respondeu, acima). ' colete ' e ' balsa ' com espaços: "coletei os dados" e "o bálsamo" não são salvatagem.
  var SALVATAGEM = [' colete ', ' coletes ', 'salva-vida', 'salva vida', ' balsa ', ' balsas ', 'bote salva', 'boia circular', 'boia salva', 'sinalizador', 'foguete', 'pirotecn', 'facho', 'salvatagem',
    'equipamento de seguranca', 'equipamentos de seguranca', 'kit de seguranca', 'sobreviv', ' plb ', ' sart '];
  var BOIA_FORA = ['amarra', 'poita', 'canal', 'baliza', 'cardinal', 'luz', 'nivel', 'porao', 'bomba', 'tanque', 'vaso', 'sanitario', 'combustivel', 'sensor', 'chave', 'ancor', 'fundei'];
  function salvatagem(q) { return has(q, SALVATAGEM) || (q.indexOf(' boia ') !== -1 && !has(q, BOIA_FORA)) || q.indexOf('extintor') !== -1; }
  // EPIRB (rota epirb): a baliza que disparou e o disparador hidrostático são do EPIRB, local, nunca da IA (a pergunta do botão da G1 do
  // certificado, "…disparador hidrostático", vai antes, para o docsvenc)
  var EPIRB_PALAVRAS = ['epirb', 'radiobaliza', 'baliza disparou', 'disparador hidrostatico'];
  // «a baliza do barco disparou sozinha», «a baliza ativou», «a baliza foi acionada»: a baliza (o EPIRB) com até 3 palavras antes do verbo. «Baliza» sozinha é sinalização.
  // A fonte é a mesma do gerador (confere.py: EPIRB_REGEX); o testes/cerebro.py compara.
  var EPIRB_REGEX_FONTE = ' (?:baliza(?: [a-z0-9]+){0,3} (?:disparou|disparada|disparado|disparando|ativou|ativada|ativado|ativando|acionou|acionada|acionado|acionando)|(?:disparou|ativou|acionou|disparei|ativei|acionei|disparamos|ativamos|acionamos) (?:a |essa |aquela )?baliza) ';
  var EPIRB_REGEX = new RegExp(EPIRB_REGEX_FONTE);
  function epirbRelato(q) { return has(q, EPIRB_PALAVRAS) || EPIRB_REGEX.test(q); }
  // O sistema fixo que disparou ou descarregou (1b, §6.6 do contrato): "sistema fixo", "descarga do sistema", "depois do disparo", "descarreg…",
  // "depois da descarga", "disparou o sistema" e "sistema … disparou/disparo". Revisão da 1b: essas palavras sozinhas pegavam o alarme do porão,
  // o Seakeeper, o arrefecimento, a descarga do vaso e "descarregar as compras", e mandavam desligar motores e gerador. Agora (1) "sistema fixo"
  // vale sempre; (2) "o sistema disparou/descarregou", com a palavra colada ao "o sistema", é o fixo; (3) as demais só junto de uma âncora de
  // combate a incêndio (extinção, casa ou praça de máquinas, compartimento ou acesso ao motor). Fora a eletricidade: a bateria
  // que descarregou, o disjuntor do sistema elétrico que disparou, o carregador, o som e o plotter não são o Seafire.
  var ELETRICO = ['bateria', 'carregador', 'pilha', 'celular', 'tensao', 'volt', 'eletric', 'disjuntor', 'inversor', 'tomada', 'amper', ' som ', 'audio', 'musica',
    'bluetooth', 'plotter', 'radar', 'wifi', 'internet', 'climatiza', 'condicionado'];
  // (incêndio, supressão e Seafire já têm rota própria antes, na route(): aqui só o que ainda precisa de âncora)
  var FOGO_ANCORA = ['extin', 'maquinas', 'compartimento do motor', 'compartimento dos motores', 'compartimento de motor', 'acesso ao motor', 'abrir o motor', 'abrir o acesso'];
  var FOGO_GATILHO = ['descarga do sistema', 'depois do disparo', 'descarreg', 'depois da descarga', 'disparou o sistema'];
  var SISTEMA_SOZINHO = / o sistema (?:ja |todo |inteiro )?(?:disparou|disparado|descarregou|descarregado) /; // "o sistema…": "alarme de sistema disparou" e "o alarme do sistema disparou" não
  var DISPARO_SISTEMA = / sistema(?: [a-z0-9]+){0,6} (?:disparou|disparo|disparar|disparado) /;
  function seafireDisparo(q) {
    if (q.indexOf('sistema fixo') !== -1) return true;
    if (has(q, ELETRICO)) return false;
    if (SISTEMA_SOZINHO.test(q)) return true;
    return has(q, FOGO_ANCORA) && (has(q, FOGO_GATILHO) || DISPARO_SISTEMA.test(q));
  }
  // Óleo: 1 = queda/alarme relatado (passo a passo); 2 = só pergunta de pressão (leitura); 0 = outro assunto.
  // Exige "óleo" na frase (nunca "pressão baixa" sozinha: barômetro, água, chuveiro). Conservador: pressão do óleo sem ser pergunta simples
  // (qual/como/normal/faixa…) já é relato → passo a passo. Porão/vazamento só saem daqui sem pressão/alarme/luz; gerador, só sem "motor".
  var OLEO_QUEDA = / (?:baix|abaixo|cai |caiu|caind|cair|qued|alarm|alert|luz|acend|acesa|sem |zer|perd|despenc|sum|diminu|oscil|vermelh|fora d|nao esta |nao ta |saiu|menor|anormal)/;
  var OLEO_SINAL = / (?:pressao|alarm|alert|luz|acend|acesa)/, OLEO_NEUTRO = / (?:qual|quais|quanto|quanta|como|normal|faixa|alta|alto|ok|esta boa|ta boa|esta bom|ta bom) /;
  var OLEO_TOPICO = /^ (?:e )?(?:a )?pressao d[eo] oleo(?: d[oa]s? motor(?:es)?)?(?: (?:de )?(?:bb|be|bombordo|boreste))? $/;
  function oleo(q) {
    q = q.replace(/ oleo (?:diesel|combustivel)(?= )/g, ' diesel'); // "óleo diesel" é combustível, não óleo do motor
    if (!has(q, [' oleo']) || has(q, ['barometr', 'atmosf', 'hpa', 'pneu', 'hidraul'])) return 0;
    if (!OLEO_SINAL.test(q) && has(q, ['porao', 'vazament', 'vazand', 'pingand'])) return 0; // óleo no porão / vazamento: rota própria
    if (has(q, ['gerador', ' onan ']) && !has(q, ['motor'])) return 0; // óleo do gerador: rota do gerador (' onan ': 'funcionando' contém 'onan')
    var pressao = has(q, ['pressao']);
    if (OLEO_QUEDA.test(q)) return pressao || !has(q, ['troca']) ? 1 : 0;
    if (!pressao) return 0;
    return OLEO_NEUTRO.test(q) || OLEO_TOPICO.test(q) ? 2 : 1;
  }
  // Pedido de registro = comando explícito: imperativo (registre/registra/anote/anota; lance/grave só com "no diário") no começo da frase
  // ou de uma oração (depois de , ; : . ! ?, "por favor" ou "e"); infinitivo só depois de pode/poderia/quero/queria/por favor.
  // No meio, só "… registre no diário …" ou "…, anote aí" no fim, e nunca em pergunta. Não grava: negação antes do verbo ("não registre"),
  // sujeito/modal antes ("vou registrar", "o Lucas registra"), "<verbo>?" solto e pergunta sobre o recurso ("Gravar no diário funciona…?").
  var REG_VERBO = / ((?:(?:capitao|ok|sim|entao|agora|por favor|pode|poderia|quero|queria) (?:\| )?)*)(registre|registra|anote|anota|lance|lanca|grave|grava|registrar|anotar|gravar|lancar)((?: isso| aqui| ai| la)*)( no diario(?: de bordo)?)?(?= )/gi;
  var REG_NEGA = / (?:nao|nunca|jamais|sem)(?: \|)?(?: [a-z]+){0,2} (?:registre|registra|anote|anota|lance|lanca|grave|grava|registrar|anotar|gravar|lancar) /i;
  var REG_SUJEITO = /(?:^| )(?:vou|vamos|vai|tenho que|tem que|temos que|preciso|precisa|precisamos|pediu para|pediu pra|esqueci de|esqueceu de|a gente|ele|ela|eles|elas|eu|o lucas|lucas|o tecnico|a marina)(?= |$)/i;
  var REG_NOME = /(?:^| )(?:[Oo]s?|[Aa]s?) [A-Z][a-z]/, REG_VOCATIVO = /(?:^|\|) (?:o |a )?(?:lucas|capitao) \|$/i;
  var PERGUNTA = /^ (?:onde|quando|quem|como|qual|quais|quanto|quantos|quantas|o que|oque|que|por que|porque|pq|cade|sera|ja|eu ja|voce|voces) /;
  function querRegistrar(qRaw, q) {
    var raw = String(qRaw || '').slice(0, 2000), pergunta = /\?\s*$/.test(raw), m; // as telas já cortam em 500; teto contra texto enorme
    // sem acento, com a caixa original; pontuação vira fronteira de oração " | "
    var c = ' ' + raw.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/["“”«»()\[\]]/g, ' ').replace(/\s[-—–]+\s|[,;:.!?…—–]+/g, ' | ').replace(/\s+/g, ' ').trim() + ' ';
    if (REG_NEGA.test(c)) return false; // "não registre", "Não, registre", "nunca anote", "não precisa registrar" (na mesma oração)
    REG_VERBO.lastIndex = 0;
    while ((m = REG_VERBO.exec(c))) {
      var antes = c.slice(0, m.index), verbo = m[2].toLowerCase(), diario = !!m[4], resto = c.slice(m.index + m[0].length);
      var inicio = /^[\s|]*$/.test(antes), duro = /\|$/.test(antes), mole = /(?:^| )(?:e|por favor)$/i.test(antes) || /^por favor/i.test(m[1]);
      var oracao = (antes + ' ' + m[1]).split('|').pop(), cortesia = /(?:pode|poderia|quero|queria|por favor)[\s|]*$/i.test(antes + ' ' + m[1]);
      if (!inicio && !duro && !mole) continue; // verbo no meio da oração: "vou registrar", "Lucas registra", "esqueci de registrar"
      if (REG_SUJEITO.test(oracao) || REG_NOME.test(oracao) || (duro && REG_VOCATIVO.test(antes))) continue;
      if (/r$/.test(verbo) && !cortesia) continue; // "Registrar no diário é obrigatório?", "Vamos registrar…"
      if (!diario && !/^(?:registre|registra|anote|anota|anotar)$/.test(verbo)) continue; // "Grave problema no motor", "Lance a âncora"
      if (!inicio && (pergunta || PERGUNTA.test(q) || (!diario && !/^[\s|]*(?:por favor[\s|]*)*$/i.test(resto)))) continue;
      if (pergunta && (!cortesia || /^[\s|]*$/.test(resto))) continue; // "Anota?", "Registra aí?", "Pode anotar isso?"
      return true;
    }
    return false;
  }
  // Texto do usuário sem o comando ("Registre no diário: X" / "X, anote aí" → X)
  var CMD = '(?:registre|registra|registrar|anote|anota|anotar|lance|lança|lanca|lançar|lancar|grave|grava|gravar)(?![a-zà-ÿ])';
  var LUGAR = '(?:\\s+(?:isso|aqui|aí|ai|por favor))*(?:\\s+(?:no|em)\\s+(?:o\\s+)?di[aá]rio(?:\\s+de\\s+bordo)?)?(?:\\s+(?:isso|aqui|aí|ai|por favor))*';
  var CMD_INI = new RegExp('^[\\s,;:.!—–-]*(?:(?:por favor|pode|poderia|capit[aã]o|ok|sim|quero|queria|vamos)[\\s,;:.!—–-]+)*' + CMD + LUGAR + '(?:\\s*[:,;.!—–-]+|\\s+que(?=\\s|$))?\\s*', 'i');
  var CMD_FIM = new RegExp('(?:^|[\\s,;:.!—–-]+)(?:e\\s+)?(?:(?:por favor|pode|poderia|quero|queria)[\\s,]+)*' + CMD + LUGAR + '[\\s.!]*$', 'i');
  var NO_DIARIO = /\s+(?:no|em)\s+(?:o\s+)?di[aá]rio(?:\s+de\s+bordo)?[\s.!?]*$/i, POR_FAVOR_FIM = /[\s,;:—–-]+por favor[\s.!?]*$/i, SOBRA_INI = /^(?:(?:por favor|que)(?:[\s,;:.!—–-]+|$))+/i;
  var DIARIO_INI = /^(?:no|em)\s+(?:o\s+)?di[aá]rio(?:\s+de\s+bordo)?(?:[\s,;:.!—–-]+|$)/i; // "Registre, no diário, a saída" → "a saída"
  // "posição e hora", "posição, hora e rumo", "a posição atual", "o evento" (texto dos próprios avisos do app) = resumo da telemetria
  var ITEM_RESUMO = '(?:(?:o|a) )?(?:posicao|hora|horario|evento|rumo|proa)(?: (?:atual|de agora|agora|do barco|do evento))?';
  var RESUMO = new RegExp('^(?:(?:o|a|um|uma) )?resumo(?: |$)|^' + ITEM_RESUMO + '(?:(?:,? e |, )' + ITEM_RESUMO + ')*$');
  // "posição e hora do MOB", "posição e hora, homem ao mar": grava o resumo da telemetria junto com as palavras do usuário
  var RESUMO_MAIS = new RegExp('^(?:' + ITEM_RESUMO + '(?:(?:,? e |, )' + ITEM_RESUMO + ')+,? |' + ITEM_RESUMO + ', )(?=[a-z0-9])');
  function resumoMais(nota) { return !!nota && RESUMO_MAIS.test(norm(nota)); }
  function notaDoUsuario(q) {
    var s = String(q || '').replace(/^[\s"“”«»]+|[\s"“”«»]+$/g, ''); // “registre posição e hora” dito entre aspas
    if (!s || norm(s).trim() === CANON.diario) return '';
    s = s.replace(/[\s?]+$/, '').replace(POR_FAVOR_FIM, ''); // "…?" e "…, por favor" no fim
    s = CMD_INI.test(s) ? s.replace(CMD_INI, '').replace(SOBRA_INI, '').replace(DIARIO_INI, '').replace(SOBRA_INI, '').replace(NO_DIARIO, '')
      : s.replace(CMD_FIM, '').replace(POR_FAVOR_FIM, '').replace(NO_DIARIO, ''); // "…, por favor registre" / "posição e hora no diário, registre"
    s = s.replace(/^[\s,;:.!—–"“”«»-]+|[\s,;:—–"“”«»-]+$/g, '');
    if (!s || RESUMO.test(norm(s).replace(/[.!?;:]+/g, ' ').replace(/\s*,\s*/g, ', ').replace(/\s+/g, ' ').trim())) return ''; // "registre o resumo / posição e hora" = atalho
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  function A(platform, key) { return (HREF[platform] || HREF.web)[key]; }
  function act(platform, pairs) { return pairs.map(function (p) { return { l: p[0], href: p[1].indexOf('.html') !== -1 || p[1].indexOf('#') === 0 ? p[1] : A(platform, p[1]) }; }); }
  function askHref(platform, q) { return A(platform, 'home') + '#q=' + encodeURIComponent(q); }

  var P = D.protocolos || {};
  var ROTULO = P.rotulo || 'procedimento padrão — confirmar com o protocolo de bordo';
  // MMSI_RADIO (PROMPT §2.2): em todo texto de emergência e de rádio o MMSI é o da etiqueta do rádio (Licença de Estação); o número do
  // cadastro do app (E.mmsi) só na Embarcação, nos Documentos, na F3 e no `## Embarcação` da ficha — lido na hora (mmsiNum), nunca na carga,
  // porque o SOS carrega este arquivo. Indicativo: o da Licença de Estação, nunca gerado.
  var MMSI_RADIO = P.mmsiRadio || 'MMSI do rádio de bordo (etiqueta / Licença de Estação)';
  var INDICATIVO = P.indicativo || 'o da Licença de Estação (no rádio)';
  function mmsiNum() { return E.mmsi ? 'MMSI ' + E.mmsi : 'MMSI ' + SD; }
  // a 1ª linha da rota mmsi (PROMPT §2.2): o MMSI do MAYDAY e do DSC é o da etiqueta do rádio; o do cadastro do app só vem na 2ª linha, sem instrução de programar
  var MMSI_USO = 'No MAYDAY e no DSC, use o MMSI da etiqueta do rádio (Licença de Estação).';
  // Os passos vêm do D.protocolos (fonte única do SOS, dos guias e dos cartões): mob, seafire.passos, epirb.passos, oleo. Nada de posição,
  // rumo, SOG, ETA, pessoas a bordo do quadro, MMSI gerado, modelo, validade nem lugar de equipamento de salvatagem (trava 17).
  var NOTA_ETIQUETA = (P.seafire && P.seafire.nota) || (P.epirb && P.epirb.nota) || 'modelo, validade e acionamento: veja a etiqueta do equipamento';
  function passosDe(x) { return (x && x.passos) || []; }
  function maius1(t) { t = String(t || ''); return t.charAt(0).toUpperCase() + t.slice(1); }
  function numerados(xs, ini) { return xs.map(function (t, i) { return ((ini || 1) + i) + '. ' + t; }).join('\n'); }
  var MOB = P.mob || [], SEAFIRE_PASSOS = passosDe(P.seafire), EPIRB_PASSOS = passosDe(P.epirb);
  // Passos do SOS: resposta sos e, inteiros, no registro de diário que cita emergência. Chat nunca grava sozinho — só "registre no diário…".
  // Posição do MAYDAY é a do plotter na hora da chamada. Seafire e EPIRB: só o procedimento padrão, com a etiqueta do equipamento.
  var SOS_PASSOS = 'Ordem (' + ROTULO + '):\n1. VHF canal 16 · MAYDAY — nome ×3, ' + MMSI_RADIO + ', posição lida no plotter, perigo, pessoas a bordo (conte agora), auxílio\n2. Homem ao mar: ' + MOB.join(' ') +
    '\n3. Incêndio · Seafire: ' + [SEAFIRE_PASSOS[0], SEAFIRE_PASSOS[4]].filter(Boolean).join(' ') + '\n4. EPIRB: ' + (EPIRB_PASSOS[0] || '');
  // O que a ficha da IA leva da emergência: a ordem e o MMSI do rádio, sem os passos (emergência não vai à IA; os passos estão nas respostas
  // locais, na tela SOS e nos guias). Mantém a ficha dentro do teto de 9.800 letras do contrato (§6.1).
  var SOS_FICHA = 'Ordem (' + ROTULO + '): 1. VHF canal 16 · MAYDAY com o ' + MMSI_RADIO + ' e a posição lida no plotter; 2. homem ao mar; 3. incêndio · Seafire; 4. EPIRB. Os passos estão nas respostas locais (sos, seafire, epirb), na tela SOS e nos guias; emergência não vai à IA.';
  // Passos da pressão de óleo baixa: resposta oleo e, inteiros, no registro de diário que relata queda/alarme de pressão. Sem leitura do quadro.
  var OLEO_PASSOS = numerados(P.oleo || []);
  // O passo do relato (4ª revisão da 1b; PROMPT §2.2: o relato de água a bordo e do porão vai para `sos` COM o passo a passo): água entrando, porão cheio, casco aberto →
  // protocolos.alagamento; abandono → protocolos.abandono. Texto fixo do gerador (sem nível, ciclo nem leitura), antes da ordem geral. A água em que a pessoa cai («caiu na água»)
  // não é água a bordo; combustível ou gás no porão não manda ligar as bombas.
  var AGUA_BORDO = / (?:alagad|alagand|alagament|inundad|inundand|inundac|afund|naufrag|rombo)| porao |(?:entrando|entrou|entra|entrada de|subindo|subiu|sobe|enchendo|encheu|fazendo|faz|fez|tomando|toma|tomou|pegando|puxando|cheio de|cheia de|vazando) (?:(?:muita|bastante|demais|mais) )*agua | agua (?:(?:esta|ta|vem|continua|segue) )?(?:entrando|entrou|entra|subindo|subiu|sobe|enchendo|encheu|vazando)|casco (?:esta |ta |ficou |foi )?(?:furad|rachad|trincad|rompid|abert|amassad|danificad)|(?:furou|furaram|rachou|trincou|rompeu) o casco /;
  function sosEspecifico(q) {
    var s = pad(q), out = [];
    if (s.indexOf('abandon') !== -1 && P.abandono && P.abandono[0]) out.push(P.abandono[0]);
    if (AGUA_BORDO.test(s) && !has(s, ['diesel', 'combustivel', 'gasolina', ' gas ', ' oleo']) && P.alagamento && P.alagamento[0]) out.push(P.alagamento[0]);
    return out;
  }
  // Base completa externa (NotebookLM) não configurada nesta embarcação: o fallback leva a pendência e FAQ.
  var BASE = null;
  // Texto de emergência não manda gravar o resumo da telemetria (nada de posição, rumo nem velocidade do quadro): o relato vai em palavras, a posição se lê no plotter.
  var GRAVAR_AGORA = 'Para registrar no diário: diga “registre no diário…” e o que aconteceu; a posição, leia no plotter.';
  var LOCAL_PLACA = 'no local da placa de salvatagem e do plano de segurança de bordo — confira na saída';   // a frase da salvatagem (protocolos.salvatagem), sem lugar inventado
  var LOCAL_PLANO = 'no local indicado no plano de segurança de bordo — confira na saída';
  // O resumo sem quadro vivo (modo real, tela sem replay ou sem CapitaoAgora): o do snapshot de antes, mas SEM a posição (nunca coordenada em resumo: o diário e o
  // contexto da IA usam este texto) e com até 300 letras: o item que não cabe sai inteiro, a fonte («snapshot … hora») fica. `semLocal`: só o estado, sem o lugar.
  function resumoReserva(semLocal) {
    var fim = ' — leitura' + demo_() + ' de ' + SNAP.quando + '.', r = '';
    [semLocal ? (S.estado || '') : SNAP.local, 'SOG ' + nb(S.sog) + ' nó', 'proa ' + grau3(S.proa), SNAP.motores, 'diesel ' + SNAP.diesel + ' (' + SNAP.dieselHora + ')',
      'gerador ' + (G.estado || SD) + ' (' + horas(G.horas) + ' h)', 'Seakeeper ' + ((S.seakeeper && S.seakeeper.estado) || SD), 'banco 24 V ' + nb(S.bat24, 2) + ' V',
      'vento ' + nb(S.vento) + ' nós de ' + grau3(S.ventoDe)].forEach(function (x) { if (x && (r ? r + ' · ' + x : x).length + fim.length <= 300) r = r ? r + ' · ' + x : x; });
    return r + fim;
  }
  // O resumo do instante (CONTRATO §1.23): até 300 letras, sem coordenadas. Com `{ semPosicao: true }` sem o lugar (as exceções da decisão (g)); com a resposta da
  // pergunta (`resumoAgora(a)`), o instante dela. Em /SOS-/ e com a resposta de uma chave de emergência (EMERG): a instrução do plotter, nunca quadro. Sem quadro vivo
  // (modo real), o do snapshot, sem coordenada.
  function resumoAgora(x) {
    if (emerg(x)) return P.plotter || 'POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER';
    return congela(function () {
      var i = vivo();
      if (EM_SOS) return P.plotter || 'POSIÇÃO, RUMO E VELOCIDADE: LEIA NO PLOTTER';
      if (i) return x && x.semPosicao ? i.txt.resumoSemPosicao : i.txt.resumo;
      return resumoReserva(!!(x && x.semPosicao));
    }, x && x._inst);
  }
  function mareTexto() {
    var C = window.CapitaoClima; var x = C && C.mareAgora ? C.mareAgora() : null;
    if (x == null) return null;
    var prox = (C.mareProximas ? C.mareProximas(6) : []).filter(function (p, i) { return i % 2 === 0; }).map(function (p) {
      var h = new Date(p.ms); var hh = ('0' + h.getHours()).slice(-2) + 'h';
      try { hh = new Intl.DateTimeFormat('pt-BR', { timeZone: C.TZ, hour: '2-digit' }).format(h) + 'h'; } catch (e) {}
      return hh + ' ' + C.metro(p.m);
    });
    return { agora: C.metro(x), prox: prox };
  }
  // Previsão de hoje do cabeçalho (capitao-clima.js: ECMWF via Open-Meteo, mundo real — nunca o snapshot), com a fonte e a hora da
  // leitura (sem rede, a da cópia salva do dia). null = sem leitura de hoje neste aparelho (as telas de pergunta livre carregam o
  // capitao-clima.js: Main, H2 e B3). O vento previsto é informação com fonte: o app não tem limite de vento para dizer se é
  // seguro sair. Direção por extenso (o TTS lê "NE" como "né").
  var RUMO_NOME = { N: 'norte', NE: 'nordeste', E: 'leste', SE: 'sudeste', S: 'sul', SW: 'sudoeste', W: 'oeste', NW: 'noroeste' };
  function previsao() {
    var C = window.CapitaoClima, c = C && C.clima ? C.clima() : null;
    if (!c || typeof c.max !== 'number' || typeof c.min !== 'number') return null;
    var n0 = function (x) { return typeof x === 'number' && isFinite(x) ? String(Math.round(x)) : null; }, dr = RUMO_NOME[C.rumo ? C.rumo(c.dir) : ''] || '', s = sim();
    // a leitura do dia pode vir sem a rajada ou sem o vento (o Open-Meteo não trouxe): com simulacao true a frase só não diz o que a leitura não tem (sem SEM DADOS, decisão 3);
    // com simulacao false volta a regra «Nada inventado» (rajadas SEM DADOS · vento SEM DADOS)
    var vento = n0(c.vento) ? 'vento até ' + n0(c.vento) + ' nós' + (dr ? ' de ' + dr : '') + (n0(c.raj) ? ', rajadas até ' + n0(c.raj) + ' nós' + (c.rajModelo ? ' (rajada do melhor modelo do Open-Meteo; o ECMWF não trouxe)' : '') : s ? '' : ', rajadas ' + SD) : s ? 'sem previsão de vento nesta leitura' : 'vento ' + SD;
    return { temp: 'máx ' + n0(c.max) + '° · mín ' + n0(c.min) + '°', vento: vento, fonte: C.fonte ? C.fonte(c) : 'Open-Meteo' };
  }
  function windy() { var C = window.CapitaoClima; return { l: 'Abrir o windy.com', href: (C && C.WINDY) || 'https://www.windy.com/', ext: true }; }

  // ——— O que as respostas de dado de bordo dizem (P3B) ———
  // Com D.simulacao true nenhuma resposta traz rótulo de dado ausente (SEM DADOS, SEM LEITURA, MANUAL NO DRIVE, A CADASTRAR, "snapshot"): o dado vem do quadro do
  // instante (recarrega) e a hora dele está na resposta. O caminho null do dado fica: um campo que falta no cadastro ou na leitura segue dizendo SEM DADOS / SEM LEITURA
  // (decisão 6), e com simulacao false o cérebro lê o snapshot e a regra «Nada inventado» volta inteira. Tempo e maré são do mundo real (PROMPT §2.5): previsão de
  // vento e maré do Open-Meteo com a hora da leitura; sem conexão, a frase do §2.5. Vento e ondas do quadro vão como «a bordo agora» e não entram na decisão de sair.
  function quando() { return vivo() ? 'ao vivo ' + SNAP.quando : 'leitura de ' + SNAP.quando; }   // «ao vivo 12:01:00» · «leitura de 26/09/2026 10:12»
  function cap1(s) { s = String(s || ''); return s.charAt(0).toUpperCase() + s.slice(1); }
  // a cláusula dos alarmes do instante («· alarmes: nenhum alarme ativo», «\n• Alarmes: AVISO: …»): o texto é o do quadro. Um coletor que não reporta o campo `alarmes` não tem
  // texto (alarmesTxt devolve null): com a simulação a cláusula some, sem ela a regra «Nada inventado» (sensor ausente → SEM LEITURA); nunca «nenhum alarme ativo» sem dado.
  function alarmesCl(i, rot) { var a = i && i.txt && i.txt.alarmes; return a ? rot + a : sim() ? '' : rot + SL; }
  function reservaPct() { return Math.round((typeof D.reserva === 'number' ? D.reserva : 0.1) * 100); }
  function limitesDe(campo) { if (EM_SOS) return null; var L = D.replay && D.replay.limites; return L && L[campo] ? L[campo] : null; }   // (no SOS nada lê o D.replay: CONTRATO §6.5)
  // a faixa normal da pressão do óleo para esse giro, do D.replay.limites (a do guia dos motores §9): «de 2,4 a 6,0 bar a partir de 1.000 rpm»
  function faixaOleo(rpm) {
    var L = limitesDe('motor_bb_oleo_bar'), r = L && L.regimes, k, x, n;
    if (!r || typeof rpm !== 'number') return '';
    for (k = 0; k < r.length; k++) {
      x = r[k];
      if ((x.rpm_ate == null || rpm <= x.rpm_ate) && (x.rpm_de == null || rpm >= x.rpm_de) && (n = x.normal)) return 'de ' + nb(n.de) + ' a ' + nb(n.ate) + ' bar ' + (x.rpm_de != null ? 'a partir de ' + mil(x.rpm_de) + ' rpm' : 'abaixo de ' + mil(x.rpm_ate) + ' rpm') + ' (' + L.fonte + ')';
    }
    return '';
  }
  // a hora (HH:MM) no fuso do barco, e a da última leitura salva do tempo ou da maré (de qualquer dia: capitao.clima.v1 e capitao.mare.v1 guardam o `em`), ou '' se o aparelho nunca leu
  function fmtHM(ms) { var A = window.CapitaoAgora; try { if (A && A.fmt && typeof A.fmt.hora === 'function') return A.fmt.hora(ms); } catch (e) {} var d = new Date(ms); return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
  // a hora da leitura da maré salva neste aparelho (o `em` do capitao.mare.v1), «HH:MM»; '' se não há
  function mareLidaHM() { var v = read('capitao.mare.v1', null); return v && typeof v.em === 'number' && isFinite(v.em) ? fmtHM(v.em) : ''; }
  function ultimaLeitura() { var ms = 0; ['capitao.clima.v1', 'capitao.mare.v1'].forEach(function (k) { var v = read(k, null); if (v && typeof v.em === 'number' && isFinite(v.em) && v.em > ms) ms = v.em; }); return ms ? fmtHM(ms) : ''; }
  // sem conexão e sem leitura de hoje: a frase do §2.5 (a única de tempo e maré que não é leitura)
  function semConexao() { var h = ultimaLeitura(); return 'Previsão e maré: sem conexão agora' + (h ? ' (última às ' + h + ')' : '') + ' — confira o boletim da Marinha antes de sair.'; }
  var MAR_SIM = ' · ondas: o app não tem previsão de mar — confira a previsão da Marinha antes de sair.';
  // a situação de bordo sem posição, para as respostas que a decisão (g) manda levar (tempo e maré sem conexão, contatos, fallback, anexos)
  function linhaBordo() { return (vivo() ? 'Situação de bordo agora: ' : 'Última situação de bordo: ') + resumoAgora({ semPosicao: true }); }
  // «Posição 26°59,46'S 048°36,71'W.» (a 2ª linha da posição, só no texto da tela); o dado que falta já vem como «posição SEM LEITURA» (o caminho null), sem repetir a palavra
  function posicaoTxt() { return (/^posi/.test(SNAP.pos) ? '' : 'Posição ') + SNAP.pos + '.\n'; }
  function poraoTxt() { var PO = S.porao || {}; return typeof PO.bb_cm === 'number' && typeof PO.be_cm === 'number' ? 'BB ' + nb(PO.bb_cm) + ' cm · BE ' + nb(PO.be_cm) + ' cm' + (typeof PO.ciclos_h === 'number' ? ' · ' + (PO.ciclos_h ? PO.ciclos_h + (PO.ciclos_h === 1 ? ' ciclo' : ' ciclos') : 'nenhum ciclo') + ' da bomba na última hora' : '') : null; }
  // «Motores Cummins QSB6.7 305 · 2 unidades (BB e BE)»: do cadastro (D.equipamentos), nunca um fabricante fixo no código
  function motoresTxt() { var e = equip('motores'); return fabMod('motores') + (e && e.qtd ? ' · ' + e.qtd + (e.qtd === 1 ? ' unidade' : ' unidades') : '') + (e && e.lados ? ' (' + e.lados + ')' : ''); }

  var ANSWERS = {
    // Pergunta sobre o app sem a IA ("o que você faz?"): a voz não repete a abertura ("Capitão IA online. Que precisa?"),
    // que soava como se a pergunta fosse ignorada — fala o que o Capitão faz.
    saudacao: function (p, ctx, q) { return { fala: q && !SO_OI.test(pad(q)) ? 'Respondo sobre telemetria, manutenção, documentos, abastecimento, diário de bordo e os passos de cada equipamento, sempre citando a fonte.' : '', text: 'Capitão IA online. Que precisa?\nOlá, ' + quem() + '. ' + (window.CapitaoAuth && window.CapitaoAuth.frase ? window.CapitaoAuth.frase() : '') + '\nRespondo sobre telemetria' + (sim() ? ' ao vivo' : '') + ', manutenção, documentos, abastecimento, diário de bordo e os passos de cada equipamento — sempre citando a fonte.' + (D.demo && !sim() ? '\n' + (D.selo || 'DEMO') + ': esta embarcação é de demonstração.' : ''), src: FT.tele + (D.selo && !sim() ? ' · ' + D.selo : ''), actions: act(p, [['Console completo', 'console'], ['FAQ de bordo', 'faq']]) }; },
    // Grava as palavras do usuário; sem texto (ou atalho DIÁRIO DE BORDO) grava o resumo da telemetria. commit:false (veio de link) não grava.
    diario: function (p, ctx, q) {
      var n = now(), grava = !ctx || ctx.commit !== false, nota = notaDoUsuario(q);
      var como = 'Para registrar, diga ou digite aqui “registre no diário…” seguido do texto';
      var junto = resumoMais(nota); // nota que pede posição/hora: resumo + nota numa linha só
      if (nota && !junto) {
        var alerta = emergencia(pad(nota)), pressao = oleo(pad(nota)) === 1; // relato de emergência / pressão de óleo: grava a nota e traz os passos
        if (grava) addDiario({ sys: 'Diário', t: nota, who: quem(), src: 'chat · voz/texto' });
        return { text: (grava ? 'Registrado no diário de bordo · ' + n.d + ' ' + n.t + ' · ' + quem() + '\n“' + nota + '”\nLinha nova — nada se apaga.' : 'Não registrado — pedido vindo de link não grava no diário:\n“' + nota + '”\n' + como + '.') + (alerta ? '\nSe a emergência é agora: abra o SOS. ' + SOS_PASSOS : '') + (pressao ? '\nSe a pressão de óleo está baixa agora, verifique nesta ordem:\n' + OLEO_PASSOS : ''), src: 'Fonte: anotação de ' + quem() + ' · diário de bordo do app' + (pressao ? ' · ' + guia('g_motores') + ' §4' : ''), actions: act(p, (alerta ? [['Abrir SOS', 'sos']] : []).concat(pressao ? [['Contatos', 'equipe']] : [], [['Abrir diário', 'diario']])) };
      }
      var al = junto && emergencia(pad(nota)), pr = junto && oleo(pad(nota)) === 1;
      var passos = (al ? '\nSe a emergência é agora: abra o SOS. ' + SOS_PASSOS : '') + (pr ? '\nSe a pressão de óleo está baixa agora, verifique nesta ordem:\n' + OLEO_PASSOS : '');
      var acoes = (al ? [['Abrir SOS', 'sos']] : []).concat(pr ? [['Contatos', 'equipe']] : [], [['Abrir diário', 'diario']]);
      if (al || pr) {
        // «registre posição e hora, tem fogo no motor» (PROMPT §2.2, diário com alerta): a linha e a resposta NÃO usam o resumoAgora() (nada de coordenada, SOG, proa nem
        // leitura do quadro): a hora da linha, «posição: ler no plotter» no lugar da posição pedida, e os passos
        if (grava) addDiario({ sys: 'Diário', t: nota + ' · posição: ler no plotter', who: quem(), src: 'chat · voz/texto' });
        return { text: (grava ? 'Registrado no diário de bordo · ' + n.d + ' ' + n.t + ' · ' + quem() + '\n“' + nota + '”\nPosição: ler no plotter.\nLinha nova — nada se apaga.' : 'Não registrado — pedido vindo de link não grava no diário:\n“' + nota + '”\nPosição: ler no plotter.\n' + como + '.') + passos, src: 'Fonte: anotação de ' + quem() + ' · diário de bordo do app' + (pr ? ' · ' + guia('g_motores') + ' §4' : ''), actions: act(p, acoes) };
      }
      var t = resumoAgora();
      if (grava) addDiario({ sys: 'Navegação', tone: 'var(--cap-tele, #00f4fd)', t: (junto ? nota + ' · resumo: ' : 'Resumo registrado pelo atalho: ') + t, who: quem(), src: junto ? 'chat · voz/texto · telemetria' + demo() : 'atalho · telemetria' + demo() });
      return { text: (grava ? 'Registrado no diário de bordo · ' + n.d + ' ' + n.t + ' · ' + quem() + '\n' + (junto ? '“' + nota + '”\n' : '') + t + '\nLinha nova — nada se apaga.' : 'Não registrado — pedido vindo de link não grava no diário.\n' + (junto ? '“' + nota + '”\n' : '') + 'Resumo: ' + t + '\n' + como + ', ou toque no atalho DIÁRIO DE BORDO.') + passos, src: FT.tele + ' · diário de bordo do app' + (pr ? ' · ' + guia('g_motores') + ' §4' : ''), actions: act(p, acoes) };
    },
    // Seguro para sair: as ressalvas (segurança primeiro), os alarmes do quadro e a previsão REAL de vento (§2.5); o vento e as ondas do quadro vão como «a bordo agora» e
    // não entram na decisão. O app não tem limite de vento com fonte: ele não diz «não» pelo vento. Alarme crítico ativo diz «Não».
    seguro: function (p) {
      var at = atrasadas(), porao = tarefa('porao-teste'), i = vivo(), s = sim(), ress = [], pv = previsao(), primeiraSeg = false;
      var crit = !!(i && Array.isArray(i.q.alarmes) && i.q.alarmes.some(function (a) { return a.nivel === 'critico'; })), al = i && i.txt.alarmes && i.txt.alarmes.indexOf('nenhum') !== 0 ? i.txt.alarmes : null;
      if (porao && at.indexOf(porao) !== -1) { primeiraSeg = true; ress.push('(segurança): teste das bombas de porão e alarmes ' + prazoTxt(porao) + ' — acione cada bomba manualmente antes de largar.'); }
      if (al) ress.push('Alarme ativo a bordo agora: ' + al + '.');   // logo depois da de segurança: a fala lê as primeiras ressalvas e o alarme ativo não pode ficar de fora
      at.filter(function (x) { return x.id !== 'porao-teste'; }).forEach(function (x) { ress.push(x.t + ' — ' + prazoTxt(x) + '.'); });
      ress.push(pv ? 'Previsão de hoje em Balneário Camboriú (' + pv.fonte + '): ' + pv.vento + (s ? MAR_SIM : ' · mar (ondas): ' + SD + ' no app — confira a previsão da Marinha antes de sair.') : s ? semConexao() : 'Sem previsão de vento e mar carregada (' + SD + ') — confira a previsão da Marinha antes de sair.');
      return { text: (crit ? 'Não saia agora: há alarme crítico ativo (' + al + '), com ' + ress.length + (ress.length === 1 ? ' ressalva.' : ' ressalvas.') : 'Sim, com ' + ress.length + (ress.length === 1 ? ' ressalva' : ' ressalvas') + (primeiraSeg ? ' — a primeira é de segurança.' : '.')) + '\n• Condições a bordo ' + (i ? 'agora (' + SNAP.quando + ')' : 'na ' + quando()) + ': vento ' + nb(S.vento) + ' nós de ' + grau3(S.ventoDe) + (i && i.txt.ondas ? ' · ondas ' + i.txt.ondas : '') + ' · barômetro ' + nb(S.pressao, 0) + ' hPa · ' + ((S.gps && S.gps.satelites) || '—') + ' satélites · banco 24 V ' + nb(S.bat24, 2) + ' V.\n• Diesel ≈ ' + mil(DI.litros) + ' L (' + SNAP.diesel.split(' (')[0] + ') → ≈ ' + nb(AUT.horas) + ' h a ' + ((CON.cruzeiro && CON.cruzeiro.nos) || '—') + ' nós com reserva de ' + reservaPct() + ' %.\n' + ress.map(function (r, k) { return '• Ressalva ' + (k + 1) + (r.charAt(0) === '(' ? ' ' : ': ') + r; }).join('\n') + '\n' + cap1(SNAP.motores) + (i ? alarmesCl(i, ' · alarmes: ') : '') + '.', src: FT.tele + ' · ' + FT.agenda.replace('Fonte: ', '') + (pv ? ' · previsão ' + pv.fonte : ''), actions: act(p, [['Ver manutenção', 'manut'], ['Checklist de saída', askHref(p, 'Checklist de saída')]]).concat(pv ? [windy()] : []) };
    },
    // Destinos: a rota em andamento (destino, distância e ETA do quadro) e os destinos da base com tempo e diesel (a 18 nós, 68 L/h do guia dos motores §10); o juízo
    // compara a ida e volta com o diesel a bordo menos a reserva e a margem de manobra
    destinos: function (p) {
      var i = vivo(), q = i && i.q, t = i && i.txt, c = CON.cruzeiro || {}, lista = D.destinos || [], R = EM_SOS ? null : D.rota, nos = c.nos, lph = c.lph, margem = typeof CON.margemManobra_l === 'number' ? CON.margemManobra_l : 0;
      var emRota = !!(t && t.destino && t.eta), util = typeof DI.litros === 'number' ? DI.litros * (1 - (typeof D.reserva === 'number' ? D.reserva : 0.1)) - margem : null;
      // o cruzeiro (nós e L/h do guia dos motores §10) que falta no dado: com a simulação o trecho some; no modo real é SEM DADOS (nunca «undefined nós»)
      var nosOk = typeof nos === 'number' && nos > 0, lphOk = typeof lph === 'number' && lph > 0, s = sim();
      var nosTxt = nosOk ? nos + ' nós' : s ? '' : SD + ' nós', lphTxt = lphOk ? lph + ' L/h' : s ? '' : SD + ' L/h';
      var vel = nosTxt ? ', a ' + nosTxt + (lphTxt ? ' (' + lphTxt + ')' : '') : lphTxt ? ', ' + lphTxt : '';
      var cab = emRota ? 'Indo para ' + t.destino + ', chegada prevista às ' + t.eta + ' — ' + i.hora + '.' : 'Alcance com o diesel a bordo: ≈ ' + AUT.mn + ' mn (≈ ' + nb(AUT.horas) + ' h' + (nosTxt ? ' a ' + nosTxt : '') + ', reserva de ' + reservaPct() + ' %) — ida e volta até ≈ ' + (typeof AUT.mn === 'number' ? Math.floor(AUT.mn / 2) : SD) + ' mn da posição atual.';
      var tempo = function (h) { var m = Math.round(h * 60); return m >= 60 ? Math.floor(m / 60) + ' h ' + ('0' + (m % 60)).slice(-2) + ' min' : m + ' min'; };
      var ls = lista.map(function (d, k) {
        var h = nosOk ? d.mn / nos : null, l = h != null && lphOk ? Math.round(h * lph) : null, iv = l != null ? 2 * l : null;
        return (k + 1) + '. ' + d.nome + ' — ≈ ' + nb(d.mn) + ' mn' + (h != null ? ' · ≈ ' + tempo(h) : s ? '' : ' · tempo ' + SD) + (l != null ? ' · ≈ ' + l + ' L' : s ? '' : ' · diesel ' + SD) + (iv != null && util != null ? '; ida e volta ≈ ' + iv + ' L — ' + (iv <= util ? 'cabe no diesel a bordo' : 'pede abastecer antes') : '');
      });
      var fonte = 'Fonte: ' + tele() + ' · ' + (R && R.fonte ? R.fonte : 'rotas: nenhuma') + ' · ' + (vivo() ? CON.fonte : 'consumo observado ' + (CON.periodo || ''));
      if (!lista.length) return { text: cab + (emRota ? '' : '\n' + SD + ' de rotas: nenhum roteiro ou destino cadastrado nas fontes (' + ((D.drive && D.drive.raiz) || 'Drive') + ').\nCadastre os destinos (nome e posição) para eu calcular distância, tempo e diesel de cada um.'), src: fonte, actions: act(p, [['Autonomia', askHref(p, 'Autonomia')], ['Registrar pendência', 'diario']]) };
      return { text: cab + '\nDestinos a partir ' + ((R && R.base && R.base.rel) || 'da base') + vel + ', só ida:\n' + ls.join('\n') + '\nDistâncias pela rota planejada — confirme a rota no plotter.', src: fonte, actions: act(p, [['Autonomia', askHref(p, 'Autonomia')], ['Registrar pendência', 'diario']]) };
    },
    // Manutenção: as atrasadas (a mais atrasada primeiro) e as 3 próximas, com o prazo contado do dia do instante; a tarefa de um equipamento de segurança (EPIRB, Seafire)
    // vai sem a data (a nota da etiqueta). A tarefa executada (Executado) sai.
    manutencao: function (p) {
      var at = atrasadas(), prox = agenda().filter(function (t) { return !atrasadaN(dnDe(t)); }).slice(0, 3), oleoM = tarefa('motores-oleo'), i = vivo();
      var linha = function (t) { return seg(t) ? '• ' + t.t + ' (' + t.quem + ') — ' + NOTA_ETIQUETA : '• ' + prazoTxt(t) + ' — ' + t.t + ' (' + t.quem + ')'; };
      return { text: (at.length ? 'Atrasadas (' + at.length + ')' + (i ? ' às ' + i.hora : '') + ':\n' + at.map(function (t) { return '• ' + t.t + ' · ' + t.equip + ' — ' + prazoTxt(t) + ' (' + t.quem + ')'; }).join('\n') : 'Nenhuma tarefa atrasada' + (i ? ' às ' + i.hora : '') + '.') + '\nPróximas:\n' + prox.map(linha).join('\n') + (oleoM && oleoM.horas && !loadExec()[oleoM.id] ? '\nÓleo e filtros dos motores: ' + oleoM.vence + ' ou ' + oleoM.horas.limite + ' h — faltam ' + nb(faltam(oleoM)) + ' h.' : '') + (D.agendaFalta && D.agendaFalta.length ? '\nFalta registrar: ' + D.agendaFalta.join(' · ') + '.' : ''), src: FT.agenda + ' · ' + (D.agenda || []).length + ' tarefas · horímetros ' + (M.hora || ''), actions: act(p, [['Abrir manutenção', 'manut']]) };
    },
    autonomia: function (p) { return { text: '≈ ' + nb(AUT.horas) + ' h · ≈ ' + AUT.mn + ' mn a ' + CON.cruzeiro.nos + ' nós (' + mil(CON.cruzeiro.rpm) + ' rpm · ' + CON.cruzeiro.lph + ' L/h, dois motores), com reserva de ' + reservaPct() + ' %.\nA bordo ≈ ' + mil(DI.litros) + ' L de ' + mil(DI.capacidade) + ' (BB ' + nb(DI.bb) + ' % · BE ' + nb(DI.be) + ' %) — ' + SNAP.dieselHora + '.\nEm marcha lenta (' + nb(CON.lenta.lph) + ' L/h) ≈ ' + AUT.lenta + ' h. Consumido desde o abastecimento de ' + CON.desdeAbast.desde.slice(0, 5) + ': ≈ ' + litrosTxt(CON.desdeAbast.litros) + ' L (' + CON.desdeAbast.horas + ').', src: 'Fonte: ' + tele() + ' (taxa de combustível dos dois motores, ' + (vivo() ? CON.fonte : CON.periodo) + ') · ' + FT.abast.replace('Fonte: ', '') + ' — estimativa; a nota fiscal é a fonte oficial', actions: act(p, [['Abastecimento', 'abast']]) }; },
    // Maré: do mundo real (Open-Meteo Marine, modelo, não a tábua da Marinha). Sem conexão e sem leitura salva: a frase do §2.5 e a situação de bordo (decisão (g)).
    mare: function (p) {
      var m = mareTexto(), s = sim();
      if (!m) return s ? { text: semConexao() + '\nO app usa o modelo do Open-Meteo Marine na posição de referência (Balneário Camboriú) — não é a tábua oficial da Marinha (DHN).\n' + linhaBordo(), src: 'Fonte: nenhuma leitura de maré neste aparelho — Open-Meteo Marine sem resposta', actions: act(p, [['Registrar pendência', 'diario']]) }
        : { text: 'SEM DADOS de maré agora: sem internet e sem leitura salva neste aparelho.\nO app usa o modelo do Open-Meteo Marine na posição de referência (Balneário Camboriú) — não é a tábua oficial da Marinha (DHN).', src: 'Fonte: nenhuma disponível agora — Open-Meteo Marine sem resposta', actions: act(p, [['Registrar pendência', 'diario']]) };
      return { text: 'Maré agora ' + m.agora + ' em relação ao nível médio do mar (Balneário Camboriú).\nPróximas horas: ' + m.prox.join(' · ') + '.\nÉ modelo (≈ 8 km), não a tábua oficial da Marinha — não use para passar em canal raso. ' + (s ? 'Corrente: o modelo traz só a altura da maré.' : 'Corrente: ' + SD + '.'), src: 'Fonte: Open-Meteo Marine (sea_level_height_msl) · posição de referência ' + ((D.posicaoRef && D.posicaoRef.fonte) || '') + (s && mareLidaHM() ? ' · lida às ' + mareLidaHM() : ''), actions: act(p, [['Clima', askHref(p, 'Clima')]]) };
    },
    // Clima: a previsão do dia REAL (§2.5) e, à parte, o vento, a pressão, o ar, a água e as ondas «a bordo agora». Sem a leitura de hoje, a frase do §2.5 e a situação de bordo.
    clima: function (p) {
      var pv = previsao(), s = sim(), i = vivo(), q = i && i.q;
      var cab = pv ? 'Hoje em Balneário Camboriú: ' + pv.temp + ' · ' + pv.vento + ' (previsão ' + pv.fonte + ').' : s ? semConexao() + '\n' + linhaBordo() : 'Previsão do dia: ' + SD + ' (sem leitura de hoje neste aparelho).';
      var bordo = (i ? 'A bordo agora (' + SNAP.quando + '):' : 'Última leitura de bordo (' + SNAP.quando + '):') + '\n• vento verdadeiro ' + nb(S.vento) + ' nós de ' + grau3(S.ventoDe) + '\n• barômetro ' + nb(S.pressao, 0) + ' hPa\n• ar ' + nb(S.ar) + ' °C · água ' + nb(S.agua) + ' °C' + (i && q && typeof q.ondas_m === 'number' ? '\n• ondas ' + i.txt.ondas : '');
      var fim = s ? 'Para navegar, consulte a meteorologia marinha da Marinha do Brasil.' : pv ? 'Previsão do mar (ondas): ' + SD + ' no app — para navegar, consulte a meteorologia marinha da Marinha do Brasil.' : 'Previsão de vento e mar para navegar: ' + SD + ' no app — consulte a meteorologia marinha da Marinha do Brasil.';
      return { text: cab + '\n' + bordo + '\n' + fim, src: 'Fonte: ' + (pv ? 'previsão ' + pv.fonte + ' · ' : s ? '' : 'previsão Open-Meteo: sem leitura de hoje neste aparelho · ') + SNAP.fonte, actions: act(p, [['Telemetria', 'console']]).concat(pv ? [windy()] : []) };
    },
    canal16: function (p) {
      return { text: 'Em perigo grave e iminente: MAYDAY no canal 16 (156,800 MHz), em voz alta e devagar, até ter resposta.\n' + MMSI_RADIO + ' · indicativo: ' + INDICATIVO + ' · ' + min1(fabMod('vhf')) + '.\nRoteiro MAYDAY (' + ROTULO + '):\n' + (P.roteiro || []).join(' — ') + '.\n' + (P.panpan || 'Urgência sem perigo de vida: PAN-PAN ×3.'), src: FT.proto + ' · canal 16 e MMSI do rádio de bordo', actions: act(p, [['Abrir SOS', 'sos']]) };
    },
    // Checklist de saída: o que está catalogado nos guias; o último item é o «antes de largar» do guia (salvatagem conforme a placa, previsão do dia)
    checklist: function (p) { var porao = tarefa('porao-teste'), cl = tarefa('clima-filtro'); return { text: 'Checklist de saída — do que está catalogado:\n1. Gerador Onan: depois de ligar, confira água no escapamento.\n2. Estabilizador Seakeeper: ligue com antecedência, com o banco de 12 V carregado.\n3. Climatização: filtro de água salgada limpo antes de ligar' + (cl && atrasadas().indexOf(cl) !== -1 ? ' (limpeza ' + prazoTxt(cl) + ')' : '') + '.\n4. Eletrônicos: plotter ligado, piloto em espera até sair da marina, VHF no canal 16.\n5. Bombas de porão: acione cada uma manualmente e confira o alarme' + (porao && atrasadas().indexOf(porao) !== -1 ? ' (teste ' + prazoTxt(porao) + ')' : '') + '.\n6. Diesel BB ' + nb(DI.bb, 0) + ' % · BE ' + nb(DI.be, 0) + ' % — regra: ' + (D.regraAbast || SD) + '.\n7. Antes de largar: coletes, um por pessoa — conte as pessoas a bordo agora; balsa, boia e extintores conforme a placa de salvatagem; previsão do dia consultada (vento e mar) — confira o boletim da Marinha antes de sair.', src: 'Fonte: ' + guia('checklist') + ' · ' + FT.agenda.replace('Fonte: ', '') + comTele(), actions: act(p, [['FAQ de bordo', 'faq']]) }; },
    checklistChegada: function (p) { return { text: 'Checklist de chegada — do que está catalogado:\n1. Piloto em espera antes de manobrar.\n2. Estabilizador: desligar ao atracar e manter energia até o volante parar.\n3. Gerador: retirar cargas, 3 a 5 min sem carga, desligar.\n4. Climatização: desligar e fechar a válvula de fundo se o barco ficar parado.\n5. Fechar a saída no diário: horas, consumo e pendências.', src: 'Fonte: ' + guia('checklist') + ' (Chegada)', actions: act(p, [['Fechar no diário', 'diario']]) }; },
    consumo: function (p) { var ab = D.abastecimentos || [], i = vivo(); return { text: (i ? 'Consumo agora (' + i.hora + '): ' + (i.txt.consumo || SD) + ' nos dois motores.' : 'Consumo observado (telemetria' + demo() + ' ' + CON.periodo + '):') + '\n• cruzeiro — ' + CON.cruzeiro.lph + ' L/h (' + mil(CON.cruzeiro.rpm) + ' rpm · ' + CON.cruzeiro.nos + ' nós, dois motores)\n• marcha lenta — ' + nb(CON.lenta.lph) + ' L/h\nDesde o abastecimento de ' + CON.desdeAbast.desde.slice(0, 5) + ': ≈ ' + litrosTxt(CON.desdeAbast.litros) + ' L (' + CON.desdeAbast.horas + ').' + (ab.length ? '\nAbastecimentos registrados: ' + ab.map(function (a) { return a.d.slice(0, 5) + ' · ' + mil(a.litros) + ' L'; }).join(' · ') + '.' : ''), src: 'Fonte: ' + CON.fonte + ' · ' + FT.abast.replace('Fonte: ', '') + comTele(), actions: act(p, [['Abastecimento', 'abast']]) }; },
    tanques: function (p) { return { text: 'Tanques (' + quando() + '):\n• água doce ' + nb(T.agua) + ' %\n• águas cinzas ' + nb(T.cinzas) + ' %\n• águas negras ' + nb(T.negras) + ' %\n• diesel ' + SNAP.diesel + ' — ' + SNAP.dieselHora + '.', src: FT.tele + ' (diesel ' + (DI.hora || '') + ')', actions: act(p, [['Telemetria', 'console']]) }; },
    // Contatos: quem chamar. Os telefones ficam só neste aparelho (Equipe). Exceção da decisão (g): leva a situação de bordo sem posição.
    contatos: function (p, ctx) {
      var eq = D.equipe || {}, per = eq.perfis || [], ap = eq.apoio || [], f = loadEquipe().fones, cad = Object.keys(f).length;
      return { text: 'Acesso total: ' + per.map(function (x) { return x.nome + ' (' + x.papel + ')'; }).join(' · ') + '.\nApoio: ' + ap.map(function (a) { return min1(a.papel) + (a.para ? ' (' + a.para + ')' : ''); }).join(' · ') + '.\nTelefones: ' + (cad ? cad + ' cadastrado(s) neste aparelho — abra Equipe para ligar.' : 'ficam só neste aparelho (Equipe): cadastre ali para ligar direto.') + (ctx && ctx.semBordo ? '' : '\n' + linhaBordo()), src: 'Fonte: cadastro da equipe' + demo() + ' · telefones do aparelho', actions: act(p, [['Equipe e contatos', 'equipe']]) };
    },
    anomalias: function (p) {
      var pend = pendencias(), app = loadDiario().filter(function (e) { return /pend[eê]ncia|anomalia|A CONFIRMAR|A CONFERIR/i.test(e.t); }).slice(0, 3);
      return { text: 'Pendências abertas (' + (pend.length + app.length) + '):\n' + pend.map(function (x) { return '• ' + x.d + ' · ' + x.sys + ' — ' + x.t; }).concat(app.map(function (x) { return '• ' + x.d + ' · ' + (x.sys || 'Diário') + ' — ' + String(x.t).slice(0, 110) + ' (app)'; })).join('\n') + '\nAtrasadas na agenda: ' + atrasadas().length + ' (veja Manutenção).', src: FT.diario + ' · diário do app', actions: act(p, [['Abrir diário', 'diario'], ['Manutenção', 'manut']]) };
    },
    // Porão: o nível das bombas no quadro, a faixa do guia e o teste mensal; sem o dado do porão, SEM LEITURA (o caminho null)
    porao: function (p) {
      var t = tarefa('porao-teste'), niv = poraoTxt(), L = limitesDe('porao_bb_nivel'), ate = L && L.normal && typeof L.normal.ate === 'number' ? L.normal.ate : null, e = equip('porao');
      return { text: (niv ? 'Porão ' + (vivo() ? 'às ' + SNAP.quando : 'na ' + quando()) + ': nível ' + niv + (ate != null ? ' (normal até ' + nb(ate, 0) + ' cm)' : '') + '.' : 'Sem sensor de porão no barramento NMEA — SEM LEITURA.') + '\n' + (e ? fabMod('porao') + ': ligam sozinhas pelo sensor de nível (' + guia('g_porao') + ' §1–2).\n' : '') + 'Teste de bombas de porão e alarmes ' + (t ? prazoTxt(t) + ' (agenda: ' + t.quem + ' · ' + t.intervalo + ')' : SD) + '.\nAntes de sair: acione cada bomba manualmente e confira o alarme; registre o resultado no diário.', src: FT.agenda + ' · ' + SNAP.fonte, actions: act(p, [['Manutenção', 'manut']]) };
    },
    // Gerador: o estado e a hora na própria frase (a fala é a 1ª linha sem os parênteses: «ligado às 12:01:45», nunca «(ligado · … ao vivo …)»); sem o quadro vivo, a hora da leitura
    gerador: function (p) { var r = tarefa('gerador-rotor'), rv = tarefa('gerador-revisao'), quand = vivo() ? 'às ' + SNAP.quando : 'na ' + quando(); return { text: fabMod('gerador') + (G.estado ? ' ' + G.estado + ' ' + quand : ' · estado ' + SD) + (typeof G.kw === 'number' && G.estado !== 'desligado' ? ' · ' + nb(G.kw) + ' kW' : '') + ' · ' + horas(G.horas) + ' h.\nLigar: confira óleo, válvula de fundo e filtro de água salgada → segure PARTIDA → espere tensão e frequência estabilizarem → cargas uma a uma, climatização por último.\nDesligar: retire as cargas, 3 a 5 min sem carga, PARADA.' + (r ? '\n' + r.t + ': ' + prazoTxt(r) + '.' : '') + (rv && rv.horas ? ' Revisão (óleo e filtros): ' + (execTxt(rv) ? execTxt(rv) + '.' : rv.vence + ' ou ' + mil(rv.horas.limite) + ' h — faltam ' + nb(faltam(rv)) + ' h.') : ''), src: 'Fonte: ' + guia('g_gerador') + ' §1–4 · ' + FT.agenda.replace('Fonte: ', '') + (vivo() ? ' · horímetro: ' + SNAP.fonte : ' · horímetro na telemetria' + demo()), actions: act(p, [['Passo a passo', 'f4']]) }; },
    // Telemetria: a situação (1ª linha) e o que o quadro do instante tem; porão e âncora do quadro (o dado que falta segue SEM LEITURA); os alarmes do instante
    telemetria: function (p) {
      var T = S.tanques || {}, G = S.gerador || {}, K = S.seakeeper || {}, i = vivo(), t = i && i.txt, po = poraoTxt(), AN = S.ancora || {};
      var cab = i ? cap1(i.q.estado || 'Navegando') + (t.local ? ' ' + t.local : '') + (t.sog ? ', a ' + t.sog : '') + (t.rpm ? ', com os motores a ' + t.rpm : '') + ' — ' + i.hora + '.' : 'Leitura de ' + SNAP.quando + ': ' + min1(SNAP.local) + '.';
      return { text: cab
        + '\n• Posição ' + SNAP.pos + ' · SOG ' + nb(S.sog) + ' nós · proa ' + grau3(S.proa) + ' · profundidade ' + nb(S.profundidade) + ' m'
        + '\n• Vento ' + nb(S.vento) + ' nós de ' + grau3(S.ventoDe) + ' · pressão ' + nb(S.pressao, 0) + ' hPa · ar ' + nb(S.ar) + ' °C · mar ' + nb(S.agua) + ' °C'
        + '\n• Baterias 24 V ' + nb(S.bat24, 2) + ' V · 12 V ' + nb(S.bat12, 2) + ' V'
        + '\n• Tanques: água doce ' + nb(T.agua) + ' % · cinzas ' + nb(T.cinzas) + ' % · negras ' + nb(T.negras) + ' %'
        + '\n• Diesel ' + SNAP.diesel + ' — ' + SNAP.dieselHora
        + '\n• ' + SNAP.motores.charAt(0).toUpperCase() + SNAP.motores.slice(1)
        + '\n• Gerador ' + (G.estado || SD) + ' · ' + (G.horas != null ? horas(G.horas) + ' h' : 'horímetro ' + SD) + ' · Seakeeper ' + (K.estado || SD)
        + '\n• Porão ' + (po || 'SEM LEITURA') + ' · âncora ' + (AN.estado ? AN.estado + (typeof AN.cabo_m === 'number' ? ', ' + mil(AN.cabo_m) + ' m de corrente' : '') : 'SEM LEITURA')
        + (i ? alarmesCl(i, '\n• Alarmes: ') + (t.tend ? '\n• Tendência — ' + t.tend : '') : ''),
        src: FT.tele, actions: act(p, [['Telemetria', 'console'], ['Manutenção', 'manut']]) };
    },
    // Posição (PROMPT §2.8): a 1ª linha, a falada, é a posição RELATIVA («a 0,5 mn da Barra Sul, chegando»: só com a simulação, só de pontos com fonte) com o rumo e a velocidade; as coordenadas ficam
    // na 2ª linha, só no texto da tela. Sem quadro vivo (modo real): o estado e o lugar do snapshot, sem posição relativa (a rota não existe), e as coordenadas na 2ª linha.
    posicao: function (p) {
      var i = vivo(), q = i && i.q, t = i && i.txt, parado, onde, l1, coord;
      if (i) {
        parado = typeof q.sog_nos === 'number' && q.sog_nos < 0.5; onde = t.relativa || t.local;
        l1 = cap1(q.estado || 'Navegando') + (t.sog ? ' a ' + t.sog : '') + (!parado && t.rumo ? ', rumo ' + t.rumo : t.proa ? ', proa ' + t.proa : '') + (onde ? ', ' + onde : '') + ' — ' + i.hora + '.';
        coord = typeof q.lat === 'number' && typeof q.lon === 'number' ? posicaoTxt() : '';
      } else {
        l1 = cap1(S.estado || SD) + (S.local ? ' — ' + S.local : '') + ', SOG ' + nb(S.sog) + ' nós, proa ' + grau3(S.proa) + ' — ' + quando() + '.';
        coord = posicaoTxt();
      }
      return { text: l1 + '\n' + coord + 'SOG ' + nb(S.sog) + ' nós · proa ' + grau3(S.proa) + ' · ' + ((S.gps && S.gps.satelites) || '—') + ' satélites · profundidade ' + nb(S.profundidade) + ' m · ' + quando() + '.',
        src: i ? 'Fonte: ' + i.fonteTxt : 'Fonte: GPS na rede NMEA 2000 · ' + SNAP.fonte, actions: act(p, [['Telemetria', 'console']]) };
    },
    // Documentos: o prazo contado do dia do instante; o documento de um equipamento de segurança (o certificado do EPIRB) sem a data, com a nota da etiqueta; a linha do que
    // falta (SEM DADOS) só existe quando há documento sem dado
    docsvenc: function (p) {
      var segd = function (d) { return (D.equipamentos || []).some(function (e) { return e.seguranca && e.validade === d.id; }); };
      var todos = (D.documentos || []), segDocs = todos.filter(segd), ds = todos.filter(function (d) { return !segd(d); });
      var com = ds.filter(function (d) { return !isNaN(dnDe(d)); }).sort(function (a, b) { return dnDe(a) - dnDe(b); });
      var vence = com.filter(function (d) { return dnDe(d) <= 90; }), dia = com.filter(function (d) { return dnDe(d) > 90; }), sem = ds.filter(function (d) { return d.st === SD; }), conf = ds.filter(function (d) { return /A CONF/.test(d.st); });
      var prazo = function (d) { var n = dnDe(d); return n < 0 ? 'VENCIDO há ' + (-n) + (n === -1 ? ' dia' : ' dias') : 'D-' + n; };
      return { text: 'Vencem primeiro:\n' + (vence.length ? vence.map(function (d) { return '• ' + d.n + ' — ' + d.vence + ' (' + prazo(d) + ')'; }).join('\n') : '• nenhum nos próximos 90 dias') + '\nEm dia: ' + dia.map(function (d) { return min1(d.n) + ' até ' + d.vence; }).join(' · ') + '.' + (sem.length ? '\n' + SD + ': ' + sem.map(function (d) { return d.n; }).join(' · ') + '.' : '') + (conf.length ? '\nA CONFERIR: ' + conf.map(function (d) { return d.n; }).join(' · ') + '.' : '') + (segDocs.length ? '\nSegurança: ' + segDocs.map(function (d) { return min1(d.n) + ' — ' + NOTA_ETIQUETA; }).join(' · ') + '.' : ''), src: FT.docs, actions: act(p, [['Documentos', 'docs']]) };
    },
    horimetros: function (p) { var o = tarefa('motores-oleo'), rv = tarefa('gerador-revisao'), oEx = execTxt(o), rvEx = execTxt(rv); return { text: 'Horímetros ' + (vivo() ? 'às ' + SNAP.quando + ' (motores ' + (M.estado || SD) + ')' : '(motores: última leitura ligados ' + (M.hora || SD) + ' · gerador ' + (G.hora || SD) + ')') + ':\n• motor BB ' + horas(M.horimetro && M.horimetro[0]) + ' h\n• motor BE ' + horas(M.horimetro && M.horimetro[1]) + ' h\n• gerador ' + horas(G.horas) + ' h\n' + (oEx ? 'Troca de óleo dos motores: ' + oEx + '.' : 'Próxima troca de óleo dos motores: ' + (o ? o.vence + ' (' + prazoTxt(o).split(' · ')[0] + ') ou ' + o.horas.limite + ' h — faltam ' + nb(faltam(o)) + ' h; o que vier antes.' : SD)) + (rv ? '\nRevisão do gerador: ' + (rvEx ? rvEx + '.' : rv.vence + ' (' + prazoTxt(rv).split(' · ')[0] + ') ou ' + mil(rv.horas.limite) + ' h.') : ''), src: FT.tele + ' · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['Manutenção', 'manut']]) }; },
    // Motores: o cadastro (fabricante e modelo de D.equipamentos), o estado e os números do instante, os alarmes do quadro e a troca de óleo pela agenda (data ou horas)
    motores: function (p) { var o = tarefa('motores-oleo'), i = vivo(); return { text: (i ? 'Motores ' + (M.estado || SD) + ' às ' + i.hora + ': ' + (i.txt.rpm || '—') + alarmesCl(i, ' · alarmes: ') + '.\n' : '') + SNAP.motores.charAt(0).toUpperCase() + SNAP.motores.slice(1) + '.\n' + motoresTxt() + '.\nHorímetros BB ' + horas(M.horimetro && M.horimetro[0]) + ' h · BE ' + horas(M.horimetro && M.horimetro[1]) + ' h' + (o ? ' · troca de óleo ' + (execTxt(o) || prazoTxt(o) + (o.horas ? ' ou ' + o.horas.limite + ' h' : '')) : '') + '.\nPartida, aquecimento e parada: ' + guia('g_motores') + ' §1–3 e §6. Faixas de operação: §9.', src: 'Fonte: ' + guia('g_motores') + ' · ' + SNAP.fonte, actions: act(p, [['Manutenção', 'manut'], ['FAQ de bordo', 'faq']]) }; },
    estabilizador: function (p) { var an = tarefa('seakeeper-anodo'); return { text: fabMod('estabilizador') + ' · ' + ((S.seakeeper && S.seakeeper.estado) || SD) + ' (' + quando() + ').\n• Funciona no banco de 12 V: acelera com o banco carregado (carregador ligado ao gerador ou ao cais); estabiliza quando o display indicar pronto.\n• Ao atracar: desligue e mantenha a energia até o volante parar.\n• Nunca faça manutenção com o volante girando.\nAceleração do volante e mensagens do display: ' + guia('g_seakeeper') + ' §2 e §6.' + (an ? '\n' + an.t + ': ' + prazoTxt(an) + '.' : ''), src: 'Fonte: ' + guia('g_seakeeper') + ' §1–6 · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['Passo a passo', 'f2']]) }; },
    climatizacao: function (p) {
      var f = tarefa('clima-filtro'), i = vivo(), d = (D.diario || []).filter(function (x) { return f && x.ref === f.id; })[0];
      return { text: fabMod('climatizacao') + (i && typeof i.q.climatizacao_ativa === 'boolean' ? (i.q.climatizacao_ativa ? ' ligada' : ' desligada') + ' às ' + i.hora : '') + '.\n' + (f ? 'Filtro de água salgada: limpeza ' + prazoTxt(f) + '.' + (d ? ' Diário de ' + d.d + ': ' + d.t : '') + '\n' : '') + 'Ligar: válvula de fundo aberta e filtro limpo → bomba de água salgada → controle da cabine.\nAlarme de fluxo: quase sempre falta de água salgada (filtro sujo, válvula fechada, bomba desligada).', src: 'Fonte: ' + guia('g_clima') + ' · ' + FT.agenda.replace('Fonte: ', '') + (d ? ' · ' + FT.diario.replace('Fonte: ', '') + ' ' + d.d : ''), actions: act(p, [['Passo a passo', 'f5']]) };
    },
    // Eletrônicos: o cadastro (plotters, áudio, rádios, piloto, radar, AIS) e o guia de cada um; o piloto e o radar têm o guia deles. Radar e AIS do instante.
    eletronicos: function (p) {
      var c = tarefa('garmin-cartas'), i = vivo(), q = i && i.q;
      var est = i ? ' Às ' + i.hora + ': radar ' + (q.radar_ativo ? 'ligado' : 'desligado') + (typeof q.ais_alvos === 'number' ? ' · AIS com ' + q.ais_alvos + (q.ais_alvos === 1 ? ' alvo' : ' alvos') : '') + '.' : '';
      return { text: [fabMod('eletronicos'), min1(fabMod('audio')), min1(fabMod('vhf'))].join(' · ') + '.' + est + '\n• Homem ao mar: função MOB do plotter Garmin marca a posição.\n• ' + fabMod('piloto') + ': em espera antes de manobrar na marina (' + guia('g_piloto') + ' §1–3).\n• ' + fabMod('radar') + ': ligar e transmitir, zona de guarda e uso com neblina (' + guia('g_radar') + ' §1–3).\n• VHF: canal 16 em escuta; o DSC só identifica o barco com o MMSI programado no rádio.' + (c ? '\nAtualização de cartas e software dos eletrônicos: ' + prazoTxt(c) + '.' : ''), src: 'Fonte: ' + guia('g_eletronicos') + ' · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['FAQ eletrônicos', 'f3']]) };
    },
    audio: function (p) { var e = equip('audio'); return { text: fabMod('audio') + (e && e.nominal && e.nominal.zonas ? ' · ' + e.nominal.zonas + ' zonas' : '') + '.\nParear: fonte Bluetooth no controle Fusion → aparelho visível → selecione o Fusion na lista de Bluetooth do celular. Volume ajustado por zona.', src: 'Fonte: ' + guia('g_eletronicos') + ' §6', actions: act(p, [['FAQ eletrônicos', 'f3']]) }; },
    dessalinizador: function (p) {
      var e = equip('dessalinizador'), i = vivo();
      if (!e) return { text: SD + ' — dessalinizador não consta na lista de equipamentos.\nSe houver a bordo, envie a foto da etiqueta (modelo e número de série) para catalogar.', src: 'Fonte: Inventário de bordo' + demo() + ' — equipamento não listado', actions: act(p, [['Enviar foto', A(p, 'home') + '#mode=foto']]) };
      return { text: fabMod('dessalinizador') + (i && typeof i.q.dessalinizador_ativo === 'boolean' ? (i.q.dessalinizador_ativo ? ' ligado' : ' desligado') + ' às ' + i.hora : '') + (e.nominal && e.nominal.lph ? ' · produção nominal ' + e.nominal.lph + ' L/h' : '') + '.\nLigar, produção e lavagem: ' + guia('g_dessalinizador') + ' §1–3 — descarte a água dos primeiros minutos depois de ligar.', src: 'Fonte: ' + guia('g_dessalinizador') + ' · ' + (e.fonte || 'Inventário de bordo'), actions: act(p, [['FAQ de bordo', 'faq']]) };
    },
    eletrico: function (p) { var ser = D.serie24v || [], mn = Math.min.apply(null, ser.map(function (x) { return x.min; })), mx = Math.max.apply(null, ser.map(function (x) { return x.max; })), b = tarefa('baterias'); return { text: 'Banco 24 V: ' + nb(S.bat24, 2) + ' V (' + (G.estado ? 'gerador ' + G.estado + ' · ' : '') + quando() + ')' + (ser.length ? ' · 7 dias entre ' + nb(mn) + ' e ' + nb(mx) + ' V' : '') + '.\nBanco 12 V: ' + nb(S.bat12, 2) + ' V.' + (b ? '\n' + b.t + ': ' + prazoTxt(b) + ' (' + b.quem + ').' : ''), src: FT.tele + ' · série 24 V · 7 dias · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['Telemetria', 'console']]) }; },
    // epirb e seafire (trava 17): só o procedimento padrão do D.protocolos, com a etiqueta do equipamento; fabricante, modelo, validade e lugar a bordo
    // não aparecem aqui (só em Equipamentos, Leme e Documentos). A 1ª linha é a instrução de segurança; a conversa toda é lida (FALA_INTEIRA).
    epirb: function (p) { return { text: 'EPIRB — ' + min1(EPIRB_PASSOS[0] || '') + '\n' + numerados(EPIRB_PASSOS.slice(1), 2) + '\n' + maius1(NOTA_ETIQUETA) + ' (' + ROTULO + ').\nOnde fica: ' + LOCAL_PLACA + '.', src: FT.proto, actions: act(p, [['Abrir SOS', 'sos']]) }; },
    seafire: function (p) { return { text: 'Seafire — ' + (SEAFIRE_PASSOS[0] || '') + '\n' + numerados(SEAFIRE_PASSOS.slice(1), 2) + '\n' + maius1(NOTA_ETIQUETA) + ' (' + ROTULO + ').\nOnde fica: ' + LOCAL_PLANO + '.', src: FT.proto, actions: act(p, [['Abrir SOS', 'sos']]) }; },
    // Salvatagem (PROMPT §2.3): o texto fixo do D.protocolos, sem número de pessoas, sem lugar (paiol, armário, proa, popa) e sem IA
    salvatagem: function (p) { return { fala: P.salvatagem || '', text: (P.salvatagem || '') + '\n(' + ROTULO + ')', src: FT.proto, actions: act(p, [['Abrir SOS', 'sos'], ['Checklist de saída', 'checklist']]) }; },
    // sos/óleo não gravam nada: pergunta informativa não vira linha permanente. Gravar = atalho DIÁRIO DE BORDO ou "registre posição e hora".
    sos: function (p, ctx, q) { var esp = sosEspecifico(q); return { text: 'Emergência — abra o SOS.' + (esp.length ? '\n' + esp.join('\n') + '\n' : ' ') + SOS_PASSOS + '\nSeafire e EPIRB: ' + NOTA_ETIQUETA + '.\n' + GRAVAR_AGORA, src: FT.proto, actions: act(p, [['Abrir SOS', 'sos'], ['Registrar no diário', 'diario']]) }; },
    oleo: function (p) { return { text: 'Se a pressão de óleo cair ou o alarme acender, verifique nesta ordem:\n' + OLEO_PASSOS + '\n' + GRAVAR_AGORA, src: 'Fonte: ' + guia('g_motores') + ' §4', actions: act(p, [['Registrar no diário', 'diario'], ['Contatos', 'equipe']]) }; },
    // Pressão do óleo (pergunta neutra): a leitura do quadro de agora, a faixa normal do guia dos motores §9 e o passo para o relato (a leitura nunca vai no relato de falha)
    oleoLeitura: function (p) {
      var i = vivo(), rpm = (vivo() ? vivo().txt.rpm || '— rpm' : (M.rpm ? M.rpm.join('/') : '—') + ' rpm'), fx = faixaOleo(i ? i.q.motor_bb_rpm : (M.rpm && typeof M.rpm[0] === 'number' ? M.rpm[0] : null));
      var ol = M.oleo ? M.oleo.map(function (x) { return nb(x); }).join('/') : '—', ar = M.arref ? M.arref.join('/') : '—';
      return { text: (i ? 'Pressão do óleo agora (' + i.hora + '): ' + (i.txt.oleo || '—') + ', com os motores a ' + rpm + '.\nArrefecimento ' + (i.txt.arref || '—') + alarmesCl(i, ' · alarmes: ') + '.' : 'Motores ' + (M.estado || SD) + ' (' + quando() + '). Pressão do óleo na última leitura com motores ligados ' + (M.hora || SD) + ': ' + ol + ' bar · ' + rpm + (M.marcha ? ' em ' + M.marcha : '') + ' · arrefecimento ' + ar + ' °C.') + (fx ? '\nFaixa normal: ' + fx + '.' : '') + '\nSe cair abaixo da faixa ou o alarme acender, pergunte “pressão de óleo baixa” para o passo a passo.', src: FT.tele + ' · ' + guia('g_motores'), actions: act(p, [['Telemetria', 'console'], ['Pressão baixa: o que fazer', askHref(p, 'Pressão de óleo baixa: o que verificar primeiro?')]]) };
    },
    // Âncora: o estado do quadro e o contador de corrente do guincho (guia de eletrônicos §3 e do guincho §1); sem o dado da âncora, SEM LEITURA (o caminho null)
    ancora: function (p) {
      var AN = S.ancora || {}, i = vivo(), prof = S.profundidade, rec = AN.estado === 'recolhida', e = equip('ancora');
      var l1 = AN.estado ? 'Âncora ' + AN.estado + (rec ? ', sem corrente lançada no contador do guincho' : typeof AN.cabo_m === 'number' ? ', com ' + mil(AN.cabo_m) + ' m de corrente no contador do guincho' : '') + ' — ' + quando() + '.' : 'Sem sensor de âncora na rede NMEA — SEM LEITURA do ferro.';
      return { text: l1 + '\n' + (S.estado || SD) + ' · ' + ((i && i.txt.relativa) || S.local || SD) + ' · profundidade ' + nb(prof) + ' m (' + quando() + ').\nAlarme de âncora: ative no plotter e defina o raio conforme a corrente lançada; o contador de corrente mostra os metros lançados no controle do guincho (' + guia('g_eletronicos') + ' §3).' + (rec && typeof prof === 'number' ? '\nPara fundear aqui: lance de 3 a 5 vezes a profundidade (' + guia('g_ancora') + ' §1), de ' + Math.round(3 * prof) + ' a ' + Math.round(5 * prof) + ' m de corrente.' : ''), src: 'Fonte: ' + guia('g_eletronicos') + ' §3 · ' + (e ? guia('g_ancora') + ' · ' : '') + SNAP.fonte, actions: act(p, [['FAQ eletrônicos', 'f3']]) };
    },
    // Revisão do C5: todos os guias do D.guias (16, um por equipamento, mais o checklist e o protocolo), sem o prefixo "Guia de bordo — ";
    // sai a lista fixa de 6 com "modelos não informados" e "Seafire e EPIRB: SEM DADOS", que a ficha mandava ao lado do ## Equipamentos.
    manual: function (p) { var g = D.guias || {}, ks = Object.keys(g); return { text: 'Guias de bordo carregados' + demo() + (ks.length ? ' (' + ks.length + ')' : '') + ' — orientação de bordo, não substituem o manual do fabricante:\n' + (ks.length ? ks.map(function (k) { return '• ' + String(g[k]).replace(/^Guia de bordo — /, ''); }).join('\n') : SD), src: 'Fonte: ' + ((D.drive && D.drive.raiz) || 'Drive') + ' › ' + ((D.drive && D.drive.pastas && D.drive.pastas.manuais) || ''), actions: act(p, [['FAQ de bordo', 'faq']]) }; },
    diarioLer: function (p) {
      var mine = loadDiario(), fonte = diarioFonte();
      var lines = mine.slice(0, 3).map(function (e) { return '• ' + (e.d || '') + ' · ' + (e.sys || 'Diário') + ' — ' + String(e.t || '').slice(0, 110) + ' (app)'; });
      var fixed = fonte.map(function (e) { return '• ' + e.d + ' ' + e.h + ' · ' + e.sys + ' — ' + e.t.slice(0, 110); });
      return { text: 'Últimos registros do diário de bordo (' + (fonte.length + mine.length) + ' no total · ' + pendencias().length + ' pendências abertas):\n' + lines.concat(fixed).slice(0, 4).join('\n') + '\nPara registrar, diga “registre no diário…” ou toque no atalho DIÁRIO DE BORDO.', src: FT.diario + ' + registros do app', actions: act(p, [['Abrir diário', 'diario']]) };
    },
    // Diagnóstico deste aparelho: versões, internet, IA na nuvem e chave (só o tamanho). A tela de chat acrescenta o teste da
    // chave no servidor (CapitaoIA.testar), que não gasta a cota da IA.
    diagnostico: function (p) {
      var AU = window.CapitaoAuth, IA = window.CapitaoIA, app = AU && AU.VERSAO ? AU.VERSAO.v : 'não carregado nesta tela', cli = IA ? (IA.VERSAO || 'antigo, sem versão') : 'não usado nesta tela (fica na tela inicial)';
      var sw = !!(window.navigator && navigator.serviceWorker && navigator.serviceWorker.controller);
      var linhas = ['Diagnóstico do Capitão IA neste aparelho:', '• Versões: app ' + app + ' · cérebro ' + VERSAO + ' · cliente da IA ' + cli];
      if (app !== VERSAO || (IA && cli !== VERSAO)) linhas.push('• ATENÇÃO: arquivos de versões diferentes — feche o app por completo e abra de novo.');
      linhas.push('• Internet: ' + (window.navigator && navigator.onLine === false ? 'sem conexão' : 'conectado') + ' · app offline (service worker): ' + (sw ? 'ativo' : 'não'));
      if (IA && IA.diagnostico) { try { linhas = linhas.concat(IA.diagnostico()); } catch (e) {} }
      // Na voz: o que importa é se a IA está ligada (a tela acrescenta o resultado do teste da chave).
      var linhaIA = linhas.filter(function (l) { return /IA na nuvem:/.test(l); })[0] || '';
      var fala = (linhaIA ? linhaIA.replace(/^•\s*/, '') + '.' : 'Nesta tela a IA na nuvem não é carregada: ela fica na tela inicial.') + (app !== VERSAO || (IA && cli !== VERSAO) ? ' Atenção: arquivos de versões diferentes, feche o app e abra de novo.' : '');
      return { text: linhas.join('\n'), fala: fala, src: 'Fonte: este aparelho' + (IA && IA.testar ? ' · teste da chave no servidor, sem gastar a cota da IA' : ''), actions: act(p, [['Ativar IA na nuvem', IA ? '#ia=ativar' : A(p, 'home') + '#ia=ativar']]) };
    },
    // ——— P3C: navegação, cadastro e perguntas sobre os dados ———
    // Profundidade: o ecobatímetro do quadro e o calado do cadastro (a folga de água sob a quilha depende da posição do transdutor: não se calcula). Sem o dado, SEM LEITURA no modo real.
    profundidade: function (p) {
      var i = vivo(), prof = i ? i.txt.prof : typeof S.profundidade === 'number' ? nb(S.profundidade) + ' m' : null, cal = EM_SOS ? null : E.calado;
      var l1 = prof ? 'Profundidade de ' + prof + (i ? ' às ' + i.hora : ' na ' + quando()) + '.' : sim() && i ? 'O sensor de profundidade não trouxe leitura às ' + i.hora + '.' : 'Profundidade: ' + SL + ' (o ecobatímetro não está na rede NMEA).';
      return { text: l1 + '\nCalado do barco: ' + (typeof cal === 'number' ? nb(cal, 2) + ' m (cadastro)' : SD) + '.', src: 'Fonte: ' + (i ? i.fonteTxt : SNAP.fonte) + ' · profundidade na rede NMEA 2000 · ' + (E.fonte || 'cadastro da embarcação'), actions: act(p, [['Telemetria', 'console']]) };
    },
    // Chegada prevista, distância ao destino e ao próximo ponto, e o percorrido desde as 07:00 (rota em andamento do quadro). Sem rota no quadro (modo real, coletor sem destino): SEM DADOS.
    eta: function (p, ctx, qq) {
      var i = vivo(), q = i && i.q, R = rotaDoPlano(), wp = i && /waypoint|proximo ponto/.test(norm(qq)), pc = i && /percorrid|navegad|odometro|navegamos|percorremos/.test(norm(qq)), dest, ponto, perc, fonte, an;
      if (!i || typeof q.destino !== 'string') {
        return { text: sim() && i ? 'O quadro de ' + i.hora + ' não trouxe destino nem chegada prevista — confira a rota no plotter.' : 'Destino, chegada prevista e próximo ponto: ' + SD + ' (nenhuma rota ativa na ' + quando() + ') — confira a rota no plotter.',
          src: 'Fonte: ' + (i ? i.fonteTxt : SNAP.fonte), actions: act(p, [['Destinos', askHref(p, 'Para onde vamos hoje?')]]) };
      }
      an = (D.replay && D.replay.ancora_hora) || '07:00';
      dest = 'Chegada prevista em ' + q.destino + (q.eta ? ' às ' + q.eta : '') + (campoTxt(i, 'destino_mn') ? ', a ' + campoTxt(i, 'destino_mn') + ' mn' : '');
      ponto = q.wp_proximo ? 'Próximo ponto: ' + q.wp_proximo + (campoTxt(i, 'wp_mn') ? ', a ' + campoTxt(i, 'wp_mn') + ' mn' : '') : '';
      perc = campoTxt(i, 'distancia_mn') ? 'Percorrido desde as ' + an + ': ' + campoTxt(i, 'distancia_mn') + ' mn' + (i.txt.sog ? ' · velocidade ' + i.txt.sog : '') + '.' : '';
      fonte = 'Fonte: ' + i.fonteTxt + ' · ' + (R && R.fonte ? R.fonte : 'rota em andamento');
      return { text: pc && perc ? perc.replace(/\.$/, '') + ' — ' + i.hora + '.\n' + dest + '.' + (ponto ? '\n' + ponto + '.' : '')
        : (wp && ponto ? ponto + ' — ' + i.hora + '.\n' + dest + '.' : dest + ' — ' + i.hora + '.' + (ponto ? '\n' + ponto + '.' : '')) + (perc ? '\n' + perc : ''), src: fonte, actions: act(p, [['Destinos', askHref(p, 'Para onde vamos hoje?')], ['Telemetria', 'console']]) };
    },
    // Alarmes ativos do instante (a CapitaoAlertas quando a tela a traz, senão os do quadro): o nível e o texto na 1ª linha, o que verificar primeiro (os passos do guia, do catálogo D.replay.alertas) depois.
    // O alarme de uma volta do replay é sempre AVISO (o crítico só com cenario 'alarme-critico', desligado): esta resposta nunca abre o SOS nem a C3 sozinha.
    alarmes: function (p) {
      var i = vivo(), lista = i ? alarmesDetalhe(i) : null, ale = catalogoAlertas(), n, partes = [], link = null;
      if (!i || !lista) {
        return { text: sim() && i ? 'O coletor não trouxe a lista de alarmes às ' + i.hora + ' — confira o painel dos motores e o plotter.' : 'Alarmes: ' + SL + ' (o coletor não reporta alarmes) na ' + quando() + ' — confira o painel dos motores e o plotter.',
          src: 'Fonte: ' + (i ? i.fonteTxt : SNAP.fonte), actions: act(p, [['Telemetria', 'console'], ['Manutenção', 'manut']]) };
      }
      n = lista.length;
      if (!n) return { text: 'Nenhum alarme ativo às ' + i.hora + '.', src: 'Fonte: ' + i.fonteTxt + ' · limites do guia de bordo', actions: act(p, [['Telemetria', 'console'], ['Manutenção', 'manut']]) };
      lista.forEach(function (a) {
        var c = ale[a.id] || {};
        partes.push((a.titulo || c.titulo || 'Alarme') + (a.hora ? ' (desde ' + a.hora + ')' : '') + ' — o que verificar primeiro:\n' + numerados(a.passos && a.passos.length ? a.passos : c.passos || []));
        if (!link && a.detalhe) link = a.detalhe;
      });
      return { text: (n === 1 ? 'Há 1 alarme ativo' : 'Há ' + n + ' alarmes ativos') + ' às ' + i.hora + ' — ' + i.txt.alarmes + '.\n' + partes.join('\n'),
        src: 'Fonte: ' + i.fonteTxt + ' · ' + lista.map(function (a) { return a.fonte || (ale[a.id] && ale[a.id].fonte) || ''; }).filter(function (x, k, v) { return x && v.indexOf(x) === k; }).join(' · '),
        actions: (link ? [{ l: 'Ver o alerta', href: link }] : []).concat(act(p, [['Telemetria', 'console'], ['Manutenção', 'manut']])) };
    },
    // Temperatura dos motores (o arrefecimento): a leitura, a faixa normal do guia dos motores §9 e a tendência de 30 s; fora da faixa, o alarme e o que verificar primeiro. Sem quadro vivo: a última leitura com motores ligados.
    arrefecimento: function (p) {
      var i = vivo(), A = window.CapitaoAgora, L = limitesDe('motor_bb_arref_c'), ate = L && L.normal && typeof L.normal.ate === 'number' ? L.normal.ate : null, fx = ate != null ? 'Faixa normal: até ' + nb(ate, 0) + ' °C (' + L.fonte + ').' : '';
      var ale = catalogoAlertas(), alr, lista, niv, fora = [], tend, l1, pass = '';
      if (!i) {
        return { text: 'Arrefecimento ' + (M.arref ? M.arref.join('/') + ' °C na última leitura com motores ligados ' + (M.hora || SD) + ' (motores ' + (M.estado || SD) + ', ' + quando() + ').' : SL + ' (' + quando() + ').') + (fx ? '\n' + fx : ''),
          src: FT.tele + ' · ' + guia('g_motores') + ' §9', actions: act(p, [['Motores', askHref(p, 'motores')], ['Telemetria', 'console']]) };
      }
      ['bb', 'be'].forEach(function (l) {
        var v = i.q['motor_' + l + '_arref_c'];
        try { niv = A.nivel('motor_' + l + '_arref_c', i.q); } catch (e) { niv = null; }
        if (niv && niv.nivel && niv.nivel !== 'normal') fora.push(l.toUpperCase() + (typeof niv.limite === 'number' ? (v > niv.limite ? ' acima de ' : ' abaixo de ') + nb(niv.limite, 0) + ' °C' : ' fora da faixa') + ' (' + (niv.nivel === 'critico' ? 'CRÍTICO' : 'AVISO') + ')');
      });
      l1 = i.txt.arref ? 'Arrefecimento ' + i.txt.arref + ' às ' + i.hora + (fora.length ? ': ' + fora.join(' e ') : ate != null && i.q.motor_bb_rpm > 0 ? ', dentro da faixa normal (até ' + nb(ate, 0) + ' °C)' : '') + '.' : 'O quadro de ' + i.hora + ' não trouxe a temperatura dos motores.';
      tend = i.tend && 'motor_bb_arref_c' in i.tend && 'motor_be_arref_c' in i.tend ? 'Nos últimos 30 s: BB ' + sinal(i.tend.motor_bb_arref_c, 1) + ' · BE ' + sinal(i.tend.motor_be_arref_c, 1) + ' °C.' : '';
      lista = alarmesDetalhe(i) || [];
      alr = lista.filter(function (a) { return /arref/.test(a.campo || a.id || ''); });
      alr.forEach(function (a) { var c = ale[a.id] || {}; pass += '\n' + (a.titulo || c.titulo || 'Alarme') + ' — o que verificar primeiro:\n' + numerados(a.passos && a.passos.length ? a.passos : c.passos || []); });
      return { text: l1 + (tend ? '\n' + tend : '') + (fx ? '\n' + fx : '') + pass, src: 'Fonte: ' + i.fonteTxt + ' · ' + (L && L.fonte ? L.fonte : guia('g_motores') + ' §9'), actions: act(p, [['Motores', askHref(p, 'motores')], ['Telemetria', 'console']]) };
    },
    // Estado do mar a bordo (as ondas do quadro): só «a bordo agora», nunca previsão (§2.5: a previsão de mar é do mundo real, e o app não a tem)
    ondas: function (p) {
      var i = vivo(), o = i ? i.txt.ondas : null, v = i ? i.txt.vento : typeof S.vento === 'number' ? nb(S.vento) + ' nós de ' + grau3(S.ventoDe) : null, s = sim();
      return { text: (o ? 'Ondas de ' + o + ' a bordo agora — ' + i.hora + '.' : s && i ? 'O sensor de ondas não trouxe leitura às ' + i.hora + '.' : 'Ondas a bordo: ' + SL + ' (o coletor não reporta a altura da onda) na ' + quando() + '.')
        + (v ? '\nVento verdadeiro ' + v + ', a bordo agora.' : '') + '\n' + (s ? 'Previsão de mar: o app não tem previsão de ondas — confira a previsão da Marinha antes de sair.' : 'Previsão de mar (ondas): ' + SD + ' no app — confira a previsão da Marinha antes de sair.'),
        src: 'Fonte: ' + (i ? i.fonteTxt : SNAP.fonte) + ' · a bordo, não é previsão', actions: act(p, [['Clima', askHref(p, 'Clima')], ['Telemetria', 'console']]) };
    },
    // Temperatura da água do mar a bordo (o sensor do quadro, preso à máxima e à mínima do dia da previsão real quando o aparelho a leu)
    temperaturaAgua: function (p) {
      var i = vivo(), ag = i ? i.txt.agua : typeof S.agua === 'number' ? nb(S.agua) + ' °C' : null, ar = i ? i.txt.ar : typeof S.ar === 'number' ? nb(S.ar) + ' °C' : null;
      return { text: (ag ? 'Água do mar a ' + ag + ' a bordo agora' + (i ? ' — ' + i.hora : ' (' + quando() + ')') + '.' : sim() && i ? 'O sensor de temperatura da água não trouxe leitura às ' + i.hora + '.' : 'Temperatura da água: ' + SL + ' (' + quando() + ').') + (ar ? '\nAr externo ' + ar + '.' : ''),
        src: 'Fonte: ' + (i ? i.fonteTxt : SNAP.fonte) + ' · sensor de bordo, não é previsão', actions: act(p, [['Clima', askHref(p, 'Clima')], ['Telemetria', 'console']]) };
    },
    // Como está a navegação / situação agora: o resumo narrado do instante (estado, velocidade, rumo, lugar, chegada) e, em linhas, os motores, o diesel, os equipamentos, o tempo a bordo, os alarmes e a tendência.
    // Sem quadro vivo (modo real), é a telemetria do snapshot.
    navegacao: function (p, ctx, q) {
      var i = vivo(), t = i && i.txt, qd = i && i.q, ls = [], parado, onde, l1;
      if (!i) return ANSWERS.telemetria(p, ctx, q);
      parado = typeof qd.sog_nos === 'number' && qd.sog_nos < 0.5; onde = t.relativa || t.local;
      l1 = cap1(qd.estado || 'Navegando') + (t.sog ? ' a ' + t.sog : '') + (!parado && t.rumo ? ', rumo ' + t.rumo : '') + (onde ? ', ' + onde : '') + (t.eta ? '; chegada prevista às ' + t.eta : '') + ' — ' + i.hora + '.';
      if (t.rpm) ls.push('• Motores ' + t.rpm + (t.oleo ? ' · óleo ' + t.oleo : '') + (t.arref ? ' · arrefecimento ' + t.arref : ''));
      if (t.diesel) ls.push('• Diesel ' + t.diesel + (t.consumo ? ' · consumo ' + t.consumo : '') + (t.autonomia ? ' · autonomia ' + t.autonomia : ''));
      if (t.gerador || t.seakeeper) ls.push('• ' + [t.gerador ? 'Gerador ' + t.gerador : '', t.seakeeper ? 'Seakeeper ' + t.seakeeper : ''].filter(Boolean).join(' · '));
      if (t.vento || t.ondas || t.prof) ls.push('• ' + [t.vento ? 'Vento ' + t.vento : '', t.ondas ? 'ondas ' + t.ondas : '', t.prof ? 'profundidade ' + t.prof : ''].filter(Boolean).join(' · ') + ' (a bordo agora)');
      if (t.alarmes) ls.push('• Alarmes: ' + t.alarmes);
      if (t.tend) ls.push('• Tendência — ' + t.tend);
      return { text: l1 + (ls.length ? '\n' + ls.join('\n') : ''), src: 'Fonte: ' + i.fonteTxt, actions: act(p, [['Telemetria', 'console'], ['Destinos', askHref(p, 'Para onde vamos hoje?')]]) };
    },
    // Pessoas a bordo: o número do registro de saída do cadastro (nunca nas chaves de emergência, nem no quadro) e a lotação do barco
    pessoas: function (p) {
      var n = EM_SOS ? null : E.pessoasBordo, lot = EM_SOS ? null : E.lotacao, i = vivo();
      return { text: typeof n === 'number' ? n + (n === 1 ? ' pessoa a bordo' : ' pessoas a bordo') + ', pelo registro de saída' + (typeof lot === 'number' ? ' (lotação ' + lot + ')' : '') + (i ? ' — ' + i.hora : '') + '.\nSe alguém embarcou ou desembarcou depois da saída, conte de novo.' : 'Pessoas a bordo: ' + SD + ' (o registro de saída não traz o número).',
        src: 'Fonte: ' + (E.fonte || 'cadastro da embarcação') + ' · ' + FT.diario.replace('Fonte: ', ''), actions: act(p, [['Abrir diário', 'diario']]) };
    },
    // Embarcação (o cadastro): dimensões, calado, lotação, modelo e registro. A 1ª linha responde ao que foi perguntado (calado, comprimento, lotação, registro, modelo); sem foco, o resumo.
    embarcacao: function (p, ctx, qq) {
      if (EM_SOS) return { text: (E.nome || SD) + '.', src: 'Fonte: cadastro da embarcação', actions: [] };   // no SOS o cérebro não lê o cadastro além do nome
      var s = pad(qq), nm = function (k, c) { return typeof E[k] === 'number' ? nb(E[k], c) + ' ' + ((E.un && E.un[k]) || '') : SD; }, i = vivo(), h = i ? ' — ' + i.hora : '', mod = E.modelo ? E.modelo + (E.fabricante ? ', do ' + E.fabricante : '') : SD, l1;
      if (s.indexOf(' calado') !== -1) l1 = 'O calado do barco é ' + nm('calado', 2) + h + '.';
      else if (s.indexOf(' comprimento') !== -1) l1 = 'O comprimento do barco é ' + nm('comprimento', 2) + h + '.';
      else if (has(s, [' boca ', 'largura'])) l1 = 'A boca do barco é ' + nm('boca', 2) + h + '.';
      else if (has(s, ['deslocamento', 'peso'])) l1 = 'O deslocamento do barco é ' + nm('deslocamento', 1) + h + '.';
      else if (has(s, ['lotacao', 'cabem'])) l1 = 'A lotação do barco é de ' + (typeof E.lotacao === 'number' ? E.lotacao + ' pessoas' : SD) + h + '.';
      else if (has(s, ['registro'])) l1 = 'O registro do barco é ' + (E.registro || SD) + h + '.';
      else if (has(s, ['modelo', 'fabricante', 'estaleiro', 'fabricou', 'que barco', 'qual e o barco'])) l1 = 'O barco é o ' + mod + (E.ano ? ', de ' + E.ano : '') + h + '.';
      else l1 = (E.nome || 'O barco') + ': ' + mod + ', ' + nm('comprimento', 2) + ' de comprimento, boca de ' + nm('boca', 2) + ' e calado de ' + nm('calado', 2) + h + '.';
      return { text: l1 + (E.rotulo ? '\n' + E.rotulo + (E.motorizacao ? ' · ' + E.motorizacao : '') : '') + '\nComprimento ' + nm('comprimento', 2) + ' · boca ' + nm('boca', 2) + ' · calado ' + nm('calado', 2) + ' · deslocamento ' + nm('deslocamento', 1)
        + ' · lotação ' + (typeof E.lotacao === 'number' ? E.lotacao + ' pessoas' : SD) + ' · registro ' + (E.registro || SD) + '.', src: 'Fonte: ' + (E.fonte || 'cadastro da embarcação'), actions: act(p, [['Documentos', 'docs'], ['Equipamentos', 'manut']]) };
    },
    // MMSI (CLAUDE.md 8): a 1ª linha manda usar o MMSI da etiqueta do rádio (Licença de Estação); a 2ª diz o do cadastro do app. Nunca com instrução de programar, nunca com posição ou pessoas.
    mmsi: function (p) {
      return { text: MMSI_USO + (EM_SOS ? '' : '\nCadastro do app: ' + mmsiNum() + '.'), src: FT.proto + (EM_SOS ? '' : ' · ' + (E.fonte || 'cadastro da embarcação')), actions: act(p, [['Abrir SOS', 'sos'], ['Documentos', 'docs']]) };
    },
    // AIS: o transponder do cadastro e os alvos do quadro; a pergunta de procedimento (como, código, onde fica…) vai ao guia dele (GENERICAS/FAMILIA)
    ais: function (p) {
      var i = vivo(), a = i && i.q.ais_alvos;
      return { text: fabMod('ais') + (typeof a === 'number' ? ' com ' + a + (a === 1 ? ' alvo' : ' alvos') + ' às ' + i.hora : ' · alvos: ' + (sim() && i ? 'o quadro não trouxe leitura às ' + i.hora : SL + ' (' + quando() + ')')) + '.\nOs alvos aparecem no plotter, com nome, rumo e velocidade (' + guia('g_ais') + ' §1).',
        src: 'Fonte: ' + guia('g_ais') + ' · ' + (i ? i.fonteTxt : SNAP.fonte), actions: act(p, [['FAQ eletrônicos', 'f3']]) };
    },
    // Pergunta direta sobre os dados (PROMPT §2.6, decisão (f)): a frase padrão e a situação de bordo sem posição. Local, sem IA, nunca afirma que é real. Com simulacao false, que é uma embarcação de verdade, a regra «Nada inventado».
    sobreDados: function (p) {
      var s = sim();
      return { text: (s ? SOBRE_DADOS : 'Cada número vem de uma fonte, com a hora da leitura: o coletor NMEA de bordo, a agenda, os documentos e o diário. O que não tem fonte aparece como ' + SD + ' e o sensor ausente como ' + SL + '.') + '\n' + linhaBordo(),
        src: s ? 'Fonte: este aparelho · modo de apresentação' : 'Fonte: este aparelho · regra da casa: cada dado com a fonte', actions: act(p, [['Telemetria', 'console'], ['FAQ de bordo', 'faq']]) };
    },
    // Fora do barco e dinheiro (PROMPT §2.7): local, sem IA, sem preço, telefone nem nome de terceiro; a situação de bordo (sem posição) com o número e a hora
    foraBarco: function (p) {
      return { text: 'Isso fica fora do barco.\n' + linhaBordo(), src: 'Fonte: fontes de bordo consultadas' + (vivo() ? ' às ' + vivo().hora : ''), actions: act(p, [['FAQ de bordo', 'faq'], ['Telemetria', 'console']]) };
    },
    // Sem rota (pergunta fora das fontes de bordo): o fallback não diz SEM DADOS (decisão 5) e leva a situação de bordo sem posição (a IA responde por cima, quando liga)
    fallback: function (p) { return { text: 'Isso não está nas fontes de bordo que o app consulta — telemetria, agenda, documentos, diário e guias de bordo.\nPosso registrar como pendência no diário, ou você envia uma foto (etiqueta, tela, nota) para eu identificar.\n' + linhaBordo(), src: 'Fonte: fontes de bordo consultadas' + (vivo() ? ' às ' + vivo().hora : '') + ' — hierarquia: manual oficial › registro oficial › laudo › diário › foto › nota informal', actions: (BASE ? [BASE] : []).concat(act(p, [['Registrar pendência', 'diario'], ['FAQ de bordo', 'faq']])) }; }
  };

  // ——— Telemetria ao vivo ———
  // Com quadro vivo no instante (o do replay ou o do coletor, capitao-telemetria.js), tanques, baterias e Seakeeper saem da leitura do instante (a posição tem a resposta própria, que trata o quadro vivo e a reserva) e a fonte
  // é a dele (`fonteTxt`: «telemetria ao vivo · hora» para o replay, «coletor NMEA · ao vivo hora» só para o coletor de verdade). O resto das respostas de dado de
  // bordo lê o mesmo instante por S, M, G, DI, T, SNAP, AUT e CON (recarrega). Sem quadro vivo (modo real sem coletor, tela sem replay) valem os textos do snapshot,
  // como antes. Fora daqui, por decisão: sos, canal16, epirb, seafire, salvatagem, mmsi e óleo nunca leem o quadro.
  var VIVO = {
    tanques: function (i) { var q = i.q; return { text: 'Tanques agora:\n• água doce ' + nb(q.tanque_agua_pct) + ' %\n• águas cinzas ' + nb(q.tanque_cinzas_pct) + ' %' + (q.tanque_cinzas_pct > 70 ? ' — atenção: programar esgoto' : '') + '\n• águas negras ' + nb(q.tanque_negras_pct) + ' %' + (q.tanque_negras_pct > 70 ? ' — atenção: programar esgoto' : '') + '\n• diesel: ' + SNAP.diesel + ' — ' + SNAP.dieselHora + '.' }; },
    eletrico: function (i, base) { var q = i.q; return { text: 'Baterias agora: banco 24 V ' + nb(q.bateria_0_tensao_v, 2) + ' V · banco 12 V ' + nb(q.bateria_2_tensao_v, 2) + ' V (ao vivo ' + i.hora + ').\n' + base.text.split('\n').slice(2).join('\n') }; },
    estabilizador: function (i, base) { var q = i.q; return { text: 'Seakeeper agora: ' + (typeof q.seakeeper_ativo !== 'boolean' ? 'SEM LEITURA' : q.seakeeper_ativo ? 'LIGADO' + (typeof q.seakeeper_volante_rpm === 'number' ? ' · volante ' + mil(q.seakeeper_volante_rpm) + ' rpm (' + nb(q.seakeeper_volante_pct, 0) + ' %)' : '') : 'desligado') + ' · ao vivo ' + i.hora + '.\n' + base.text.split('\n').slice(1).join('\n') }; }
  };
  Object.keys(VIVO).forEach(function (k) {
    var pronta = ANSWERS[k]; if (!pronta) return;
    ANSWERS[k] = function (p, ctx, q) {
      var base = pronta(p, ctx, q), i = vivo(); if (!i) return base;
      var r = VIVO[k](i, base);
      return { text: r.text, src: 'Fonte: ' + i.fonteTxt, actions: base.actions };
    };
  });
  // as chaves de ANSWERS (o teste varre uma pergunta de cada) e as que não levam a hora do instante na fonte (emergência, diagnóstico, saudação, checklists, registro)
  var CHAVES = Object.keys(ANSWERS);
  // AIS: a pergunta de status («quantos alvos?», «tem AIS?», «está ligado?») fica na resposta pronta; qualquer outra (modo silencioso, identificação, alvos no plotter) vai ao trecho do g_ais quando ele serve
  var AIS_STATUS = /\b(?:quantos?|quantas?|quais|tem|temos|ha|algum|alguns|agora|ligado|ligada|funcionando|recebendo|vendo)\b/;
  // (a maré é do mundo real, §2.5: a hora dela é a da leitura salva, «lida às HH:MM» na fonte; o instante do replay nunca entra na fonte da maré)
  var SEM_HORA_NA_FONTE = { sos: 1, oleo: 1, canal16: 1, epirb: 1, seafire: 1, salvatagem: 1, mmsi: 1, diagnostico: 1, saudacao: 1, checklist: 1, checklistChegada: 1, diario: 1, mare: 1 };
  SEM_HORA_NA_FONTE.sobreDados = 1;   // (a frase padrão e a fonte «este aparelho · modo de apresentação» não levam o «consultado às»)

  // Nomes de outra bomba que não a de porão (rota 'porao', abaixo): o app não tem resposta pronta para elas, e o guia delas está na base.
  // Revisão 7 do C5: "esgoto" saiu. "Bomba de esgoto" também é a de esgotamento do porão em português de bordo, e "a bomba de esgoto não
  // para" é relato de água a bordo: tem de seguir a rota 'porao' (local, sem IA), não ir à nuvem. "Água doce" saiu por ser código morto
  // (a rota 'tanques', mais acima, já pega a pergunta). Quem fica tem guia na base (por si ou por sinônimo: impelidor = impeller/rotor) ou é
  // outra bomba sem relação com o porão (circulação, resfriamento, pressurização): essas vão ao guia ou à IA, e não à resposta do porão.
  var OUTRA_BOMBA = ['salgada', 'rotor', 'impeller', 'impelidor', 'circulacao', 'arrefecimento', 'refrigeracao', 'resfriamento', 'climatiza', 'condicionado', 'gerador', ' onan ',
    'motor', 'seakeeper', 'estabilizador', 'giroscop', 'piloto', 'hidraulic', 'dessaliniz', 'lavagem', 'pressuriz', 'oleo', 'pressao'];
  var EQUIP = ['seakeeper', 'estabilizador', 'climatiza', 'ar condicionado', 'ar-condicionado', 'gerador', ' onan ', 'piloto', 'plotter', 'radar', 'garmin', ' vhf', ' ais ', 'epirb', 'fusion', 'audio', 'dessaliniz', 'bomba', 'porao', 'casco', 'anodo', 'zinco', 'bateria', 'tensao', 'tensoes', 'seafire', 'volvo'];
  // a corrente da âncora, pelo jeito de pedir o número: «N metros de corrente», «quanta corrente», «corrente lançada/no guincho/no contador», «lançar a corrente»
  var CORRENTE_ANCORA = /\b(?:metros?|m) de corrente\b|\bquant[oa]s? (?:de )?corrente\b|\bcorrente (?:[a-z]+ ){0,3}(?:lancad[ao]s?|no guincho|do guincho|no contador|do contador)\b|\b(?:lancar|soltar|solta|lance) (?:[a-z]+ ){0,3}corrente\b/;
  // "diagnóstico", "status da IA", "teste da IA", "a IA está ligada?" — a frase inteira, para não pegar pergunta comum.
  var DIAGNOSTICO = /^ (?:(?:fazer |faz |faca |rodar |roda |rode |mostrar |mostra |mostre |me mostra |me mostre |me da |ver )?(?:o |um )?diagnostico(?: da ia| do app| do aplicativo| do capitao| completo)?|(?:qual e |qual )?(?:o )?(?:status|estado) (?:da ia|do app|do aplicativo)|teste da ia|testar a ia|testa a ia|teste a ia|(?:a )?(?:ia|inteligencia artificial)(?: na nuvem)? (?:(?:esta|ta) )?(?:ligada|funcionando|ativa|ativada|on)|(?:a )?(?:ia|inteligencia artificial)(?: na nuvem)? (?:nao )?(?:(?:esta|ta) )?(?:funciona|funcionando|responde|respondendo)) $/;
  // tira "capitão,"/"capitão IA," do começo e "por favor" do fim antes de conferir (jeito comum de falar com o app)
  function semVocativo(q) { return q.replace(/^ (?:ei |oi |ola )?capitao(?: ia)? /, ' ').replace(/ por favor $/, ' '); }

  // ——— Rotas novas da navegação, do cadastro e de fora do barco (P3C; PROMPT Fase 3 «Rotas novas», §2.3, §2.6, §2.7) ———
  // Todas entram depois da emergência e do óleo (route() as chama nessa ordem) e só com palavra inteira em pad(q). A resposta de cada uma abre com a própria resposta, numa frase falável com o
  // dado e a hora do instante; a situação de bordo vem na linha seguinte onde a decisão (g) manda (sobreDados, foraBarco).
  //
  // sobreDados (§2.6): pergunta direta sobre a autenticidade. ` real ` sozinho é medida em muita pergunta de bordo («velocidade real», «consumo real», «em tempo real», «em reais»,
  // «norte verdadeiro»): AUT_MEDIDA tira essas frases antes da conferência. Equipamento, salvatagem, EPIRB, Seafire, extintor e dinheiro nunca são a pergunta sobre os dados.
  var AUT_MEDIDA = / (?:tempo|velocidade|vento|valor|consumo|autonomia|distancia|posicao|rumo|hora|horario|custo|preco|tensao|temperatura|pressao|carga|nivel|rotacao|rpm|vazao|fluxo|giro|curso|volume|peso|altura|angulo|direcao|forca|alcance|raio|trajeto|rota|tendencia|norte|cota) (?:real|reais|verdadeir[oa]s?) | (?:em|de|mil|milhoes de) reais /g;
  var AUT_FORTE = [' real ', ' reais ', ' de verdade ', ' verdadeir', ' simulad', ' simulac', ' fictici', ' demo ', ' demonstracao ', ' inventad', ' de mentira '];
  var AUT_EXISTE = [' o barco existe ', ' a embarcacao existe ', ' isso existe '];
  var AUT_ALVO = [' dado ', ' dados ', ' leitura ', ' leituras ', ' valores ', ' numeros ', ' telemetria ', ' isso ', ' isto ', ' barco ', ' embarcacao ', ' navegacao ', ' app ',
    ' alarme ', ' alarmes ', ' alerta ', ' alertas ', ' sensor ', ' sensores ', ' gps ', ' posicao ', ' rota ', ' viagem '];
  var AUT_FORA = ['preco', 'custa', 'custo', 'pagar', 'r$', 'extintor', 'seafire', 'sea fire', 'sea-fire'];
  // a forma curta, sem a palavra do alvo: «é real?», «é de verdade?», «é simulado?»
  var AUT_CURTA = /^ (?:(?:mas|entao|isso|isto|tudo|aqui) )*(?:e|eh|sao|era|foi) (?:(?:tudo|isso|isto|mesmo|totalmente|realmente|muito) )*(?:real|reais|de verdade|verdadeir[oa]s?|simulad[oa]s?|fictici[oa]s?|inventad[oa]s?|de mentira|uma simulacao|simulacao|uma demonstracao|demonstracao) $/;
  function sobreDados(q) {
    if (has(q, AUT_FORA) || has(q, EQUIP) || salvatagem(q) || epirbRelato(q)) return false;
    if (AUT_CURTA.test(q)) return true;
    var s = q.replace(AUT_MEDIDA, ' ');
    return (has(s, AUT_FORTE) || has(s, AUT_EXISTE)) && has(s, AUT_ALVO);
  }
  // embarcacao: as dimensões, o calado, a lotação, o modelo e o registro do cadastro (D.embarcacao). A pergunta do calado é daqui (o calado tem dado desde a Fase 1).
  var EMB_PALAVRAS = [' calado', ' comprimento', 'dimensoes', ' boca do barco', ' boca da lancha', ' boca da embarcacao', 'largura do barco', 'largura da lancha', 'largura da embarcacao', 'tamanho do barco', 'tamanho da lancha',
    'tamanho da embarcacao', 'quantos metros tem o barco', 'deslocamento do barco', 'deslocamento da lancha', 'deslocamento da embarcacao', 'qual o deslocamento', 'peso do barco', ' lotacao', 'quantas pessoas cabem',
    'cabem quantas pessoas', 'modelo do barco', 'modelo da lancha', 'modelo da embarcacao', 'fabricante do barco', 'fabricante da lancha', 'qual o estaleiro', 'quem fabricou', 'ano do barco', 'ano de fabricacao',
    'registro do barco', 'registro da lancha', 'registro da embarcacao', 'numero de registro', 'ficha tecnica', 'que barco e esse', 'qual e o barco'];
  // pessoas a bordo: o número do registro de saída (embarcacao.pessoasBordo); a lotação («quantas pessoas cabem») é do cadastro (embarcacao)
  var PESSOAS_PALAVRAS = ['pessoas a bordo', 'quantas pessoas', 'quantos a bordo', 'gente a bordo', 'tripulantes a bordo', 'passageiros a bordo', 'quem esta a bordo', 'quantos tripulantes', 'quantos passageiros'];
  var PROFUNDIDADE_PALAVRAS = ['profundidade', 'ecobatimetro', 'sob a quilha', 'quanto fundo', ' fundo aqui', 'agua sob'];
  // só a leitura do ecobatímetro: o alarme de profundidade, a profundidade mínima, o «como», o relato («sonda mostrando pouca profundidade») e a de fundear seguem o guia ou a IA
  var PROFUNDIDADE_FORA = ['minim', 'alarme', 'alerta', 'aviso', 'como ', 'configur', 'ajust', 'defin', 'limite', 'pouca', 'rasa', 'raso', 'segur', 'recomend', 'ideal', 'quanto preciso', 'fundear', 'ancorar', 'lancar', 'sonda mostrando'];
  // ETA, distância e waypoint. «Quanto falta» só vale junto de chegar, chegada, destino, waypoint, ponto, ETA ou o nome de um ponto da rota (nunca «quanto falta para a troca de óleo?»);
  // a autonomia, o diesel, o alcance, o consumo e o checklist têm as rotas deles.
  var ETA_PALAVRAS = [' eta ', 'hora de chegada', 'horario de chegada', 'chegada prevista', 'previsao de chegada', 'quando chegamos', 'quando vamos chegar', 'quando a gente chega', 'que horas chegamos',
    'que horas chegaremos', 'que horas vamos chegar', 'que horas chega', 'tempo para chegar', 'tempo ate chegar', 'tempo de chegada', 'falta para chegar', 'faltam para chegar', 'waypoint', 'proximo ponto',
    'distancia ate', 'distancia para', 'distancia do destino', 'distancia percorrida', 'milhas percorridas', 'milhas navegadas', 'quantas milhas', 'quantas mn', 'odometro'];
  var FALTA_PALAVRAS = ['quanto falta', 'quanto tempo falta', 'quantas milhas faltam', 'quantos minutos faltam', 'quantas horas faltam', 'o que falta para'];
  var FALTA_JUNTO = ['chegar', 'chegada', 'destino', 'waypoint', 'ponto', ' eta '];
  var ETA_FORA = ['autonomia', 'alcance', 'diesel', 'combustivel', 'checklist', 'abastec', 'consumo', 'tecnico', 'oficina', 'entrega', 'pedido', 'encomenda', 'peca', 'prestador', 'visita'];
  // os nomes dos pontos da rota e dos destinos (D.rota, D.destinos; só com a simulação e nunca no SOS), sem o que vem entre parênteses
  function rotaDoPlano() { return EM_SOS ? null : D.rota; }   // no SOS nada lê a rota
  function lugaresRota() {
    var R = rotaDoPlano(), out = [];
    if (!sim() || !R) return out;
    try { [R.base].concat(R.pontos || [], D.destinos || []).forEach(function (x) { var n = x && x.nome ? norm(x.nome).split('(')[0].replace(/\s+/g, ' ').trim() : ''; if (n && out.indexOf(' ' + n + ' ') === -1) out.push(' ' + n + ' '); }); } catch (e) {}
    return out;
  }
  function etaPergunta(q) {
    if (has(q, ETA_FORA)) return false;
    if (has(q, ETA_PALAVRAS)) return true;
    return has(q, FALTA_PALAVRAS) && (has(q, FALTA_JUNTO) || has(q, lugaresRota()));
  }
  // alarmes ativos: «alarmes ativos», «tem algum alarme (ativo)?», «quais alarmes?», «o alarme está tocando». O «alarme de <equipamento>», «o alarme disparou» e «em caso de alarme» seguem as rotas deles.
  var FIM_ALARME = '(?: (?:estao|esta|sao))?(?: (?:ativos?|acesos?|tocando|soando|no barco|a bordo|agora|aqui|ai|hoje|neste momento))*';
  var ALARMES_REGEX = [
    / (?:alarmes?|alertas?) (?:ativos?|acesos?)(?: |$)/,
    new RegExp(' (?:tem|ha|existe|existem|temos) (?:algum |alguns )?(?:alarmes?|alertas?)' + FIM_ALARME + ' $'),
    new RegExp(' quais (?:sao |estao )?(?:os )?(?:alarmes|alertas)' + FIM_ALARME + ' $'),
    new RegExp('^ (?:e )?(?:os |o )?(?:alarmes?|alertas?)' + FIM_ALARME + ' $'),
    / alarmes? (?:esta |estao )?(?:tocando|soando) /
  ];
  function alarmesPergunta(q) { return ALARMES_REGEX.some(function (r) { return r.test(q); }); }
  // temperatura do motor (o arrefecimento): a pergunta neutra pela leitura; o alarme, o relato, o «como» e a temperatura alta seguem o guia dos motores (a resposta pronta cede ao trecho)
  var ARREF_REGEX = / (?:temperaturas? (?:d[oae]s? )?(?:motor|motores|arrefecimento|bb|be|bombordo|boreste)|temperaturas? da agua d[oa]s? (?:motor|motores)|arrefecimento) /;
  var ARREF_FORA = ['alarme', 'alerta', 'disparou', 'disparo', ' alta ', ' alto ', 'altas', 'subindo', 'subiu', ' sobe ', 'superaquec', 'esquent', 'aquec', 'quente', 'problema', 'pane', 'falha', 'vazament', 'bomba', 'rotor',
    'filtro', 'troca', 'trocar', 'manutenc', 'aditivo', 'liquido', 'nivel', 'sistema de arrefecimento', 'o que fazer', 'o que faco', 'por que', 'porque', 'resolver', 'baixar', 'esfriar', 'evitar', 'diminuir', 'reduzir', 'limpar', 'fazer', 'ligar',
    'rotacao', 'oleo', 'pressao', 'normal', 'normais', 'faixa', 'limite', 'maxim', 'minim', 'ideal', 'quais'];
  function arrefecimentoPergunta(q) { return ARREF_REGEX.test(q) && !has(q, ARREF_FORA); }
  // temperatura da água do mar (o sensor de bordo); a «temperatura da água subindo» do relato é do motor (guia) e fica fora
  var AGUA_REGEX = / temperatura (?:da|do|de) (?:agua|mar)(?: do mar)? | agua do mar (?:esta|ta) | quantos graus (?:esta|ta) a agua | temperatura da agua do mar /;
  var AGUA_FORA = ['motor', 'arrefec', 'subindo', 'subiu', ' sobe ', ' alta ', ' alto ', 'esquent', 'aquec', 'quente demais', 'gerador', 'climatiza', 'condicionado', 'dessaliniz', 'chuveiro', 'tanque', 'potavel', 'doce'];
  function aguaPergunta(q) { return AGUA_REGEX.test(q) && !has(q, AGUA_FORA); }
  // estado do mar a bordo (ondas do quadro); a previsão de mar é do mundo real (clima), e a maré tem a rota dela
  var ONDAS_PALAVRAS = [' ondas ', 'ondulacao', 'estado do mar', 'altura da onda', 'altura das ondas', 'como esta o mar', 'mar agitado', 'mar grosso', 'mar calmo', ' swell '];
  // o relato da onda («a onda bateu no casco», «as ondas molharam o convés») não é pergunta do sensor: segue a IA, como antes
  var ONDAS_FORA = [' bateu', ' bateram', ' batendo', ' bate ', ' batem ', 'quebr', ' jogou', ' jogaram', 'molh', 'derrub', 'adern', 'entrou', 'entraram', 'cobr'];
  // «como está a navegação», «situação agora»: o resumo narrado do instante. «Como estamos de diesel?» é a autonomia: a frase curta só vale inteira.
  var NAVEGACAO_PALAVRAS = ['como esta a navegacao', 'situacao agora', 'situacao atual', 'situacao de bordo', 'situacao da navegacao', 'status da navegacao', 'navegacao agora', 'resumo da navegacao', 'como anda a navegacao'];
  var NAVEGACAO_CURTA = /^ (?:e )?(?:entao )?como (?:estamos|vamos|estao as coisas|esta tudo)(?: agora| por ai| a bordo| ai)? $/;
  // foraBarco (§2.7): dinheiro, esporte, notícia, política. Depois de todas as rotas de bordo: «quanto custa o diesel em reais?» é do diesel
  var FORA_BARCO = ['dolar', 'cotacao', 'cambio', 'bolsa', 'bitcoin', 'preco', 'quanto custa', 'placar', 'campeonato', 'noticia', 'eleicao', ' euro ', ' euros ', ' jogo ', ' jogos '];
  function route(qRaw) {
    var q = pad(qRaw);
    if (!q.trim()) return 'saudacao';
    if (DIAGNOSTICO.test(semVocativo(q))) return 'diagnostico';
    if (querRegistrar(qRaw, q)) return 'diario';
    if (emergencia(q)) return 'sos';
    var ol = oleo(q);
    if (ol) return ol === 1 ? 'oleo' : 'oleoLeitura';
    // "Situação e vencimento do documento: <nome>" é a pergunta do botão "Perguntar sobre" da G1 (web e app): papelada, seja qual for o nome.
    // Com o doc-epirb (C7, "Certificado do EPIRB…") ela caía na rota `epirb` (a resposta do procedimento e, depois da 1b, a que liga a
    // conversa em emergência por 15 min: um toque na papelada abriria o modo emergência). Vem depois da emergência e do óleo (segurança
    // acima de tudo) e antes de qualquer rota de assunto. Pergunta digitada com "EPIRB" segue a rota do EPIRB.
    if (/^ situacao e vencimento do documento /.test(q)) return 'docsvenc';
    // Salvatagem (PROMPT §2.3): colete, balsa, boia, sinalizador, extintor sem fogo… logo depois da emergência e do óleo, antes das rotas de
    // assunto (epirb, seafire, canal16): resposta fixa, local, sem número de pessoas e sem lugar a bordo
    if (salvatagem(q)) return 'salvatagem';
    // sobreDados (PROMPT §2.6): depois da emergência, do óleo e da salvatagem e antes de epirb, seafire e canal16; local, sem IA, nunca afirma que é real
    if (sobreDados(q)) return 'sobreDados';
    // mmsi (CLAUDE.md 8): a pergunta do MMSI não é o roteiro MAYDAY; a 1ª linha manda usar o MMSI da etiqueta do rádio, a 2ª diz o do cadastro do app
    if (has(q, ['mmsi'])) return 'mmsi';
    if (has(q, ['seguro para sair', 'posso sair', 'da pra sair', 'da para sair', 'seguro sair', 'avalie vento', 'sair hoje', 'seguro navegar', 'seguro para navegar', 'posso navegar', 'podemos sair', 'podemos navegar', 'da pra navegar', 'da para navegar'])) return 'seguro';
    // P3C: as rotas da navegação e do cadastro, depois do «seguro para sair» e antes da telemetria («leituras da profundidade» é a profundidade). Nenhuma toma «checklist de chegada»,
    // «alarme de óleo acendeu» (o óleo vem antes), «temperatura hoje» (o clima) nem «alarme de fluxo da climatização» (a resposta pronta cede ao trecho do guia).
    if (has(q, NAVEGACAO_PALAVRAS) || NAVEGACAO_CURTA.test(q)) return 'navegacao';
    if (has(q, EMB_PALAVRAS)) return 'embarcacao';
    if (has(q, PESSOAS_PALAVRAS) && !/\d/.test(q)) return 'pessoas';   // «temos 6 pessoas a bordo» é relato (com número), não pergunta
    if (has(q, PROFUNDIDADE_PALAVRAS) && !has(q, PROFUNDIDADE_FORA)) return 'profundidade';
    if (etaPergunta(q)) return 'eta';
    if (alarmesPergunta(q)) return 'alarmes';
    if (arrefecimentoPergunta(q)) return 'arrefecimento';
    // «quanto falta para a troca de óleo / a revisão?»: as horas que faltam são dos horímetros (a manutenção, sem horas)
    if (has(q, FALTA_PALAVRAS) && has(q, ['troca', 'revisao', 'oleo', 'horas de motor']) && !has(q, EQUIP)) return 'horimetros';
    if (has(q, ['telemetria', 'leituras', 'sensores', 'como esta o barco', 'estado do barco', 'status do barco'])) return 'telemetria';
    if (has(q, ['anomalia', 'pendencia', 'problema aberto'])) return 'anomalias';
    if (has(q, ['diario'])) return 'diarioLer';
    // a corrente da âncora (a amarra, em metros no contador do guincho) não é a de maré: «quantos metros de corrente?», «quanta corrente tem lançada?», «corrente no contador» → ancora, antes da maré
    if (CORRENTE_ANCORA.test(q) && !has(q, [' mare', 'correnteza', 'corrente de mare'])) return 'ancora';
    if (has(q, [' mare', 'correnteza', 'corrente de mare']) || (has(q, [' corrente']) && !has(q, ['bateria', 'carregador', 'eletric', 'tensao', 'amper', 'alternada', 'continua', 'shore', 'tomada', ' ac ', ' dc ', 'ancora', 'amarra']))) return 'mare';
    if (has(q, [' clima ', 'climatic', 'tempo hoje', ' vento', 'chuva', 'meteor', 'temperatura hoje']) || (has(q, ['previsao']) && !has(q, [' revisao', 'manutenc', 'devoluc', 'entrega', 'chegada']))) return 'clima';
    if (has(q, ONDAS_PALAVRAS) && !has(q, ONDAS_FORA)) return 'ondas';
    if (aguaPergunta(q)) return 'temperaturaAgua';
    if (has(q, ['para onde', 'destino', 'passeio', 'onde vamos', 'melhor rota', 'rota para', 'rota ate'])) return 'destinos';
    if (has(q, ['checklist de chegada', 'chegada'])) return 'checklistChegada';
    if (has(q, ['checklist', 'check list', ' saida'])) return 'checklist';
    if (has(q, ['autonomia']) || (has(q, ['alcance']) && !has(q, [' vhf', ' radio', 'radar', ' ais ', 'antena', 'sinal', 'wifi', 'wi-fi', 'bluetooth', 'celular']))) return 'autonomia';
    // "Situação e vencimento do documento: NF de abastecimento…" é documento: a palavra documento/licença/vencimento vence a do combustível
    if (has(q, ['document', 'licenc', 'vencimento']) && has(q, ['consumo', 'l/h', 'litros por hora', 'abastec', 'diesel', 'combustivel', 'nota fiscal', 'nf-e'])) return 'docsvenc';
    if (has(q, ['consumo', 'l/h', 'litros por hora'])) return 'consumo';
    if (has(q, ['abastec', 'diesel', 'combustivel', 'nota fiscal', 'nf-e'])) return 'autonomia';
    if (has(q, ['tanque', 'agua doce', 'cinzas', 'negras'])) return 'tanques';
    // "próxima revisão" sem equipamento = motores; com equipamento, a rota dele (Seakeeper, climatização, gerador…)
    if (has(q, ['horimetro', 'horas de motor', 'horas do motor', 'horas dos motores']) || (has(q, ['proxima revisao']) && !has(q, EQUIP))) return 'horimetros';
    if (epirbRelato(q)) return 'epirb';
    // "supressão" (PROMPT §2.3): é o nome do Seafire nos dados ("sistema fixo de supressão", sem "incêndio", que abriria o SOS). 1b: o sistema
    // fixo que disparou ou descarregou também é do Seafire (o "não abra o acesso ao motor" e o desligamento são os passos de protocolos.seafire);
    // "extintor" saiu daqui para a salvatagem (sem fogo) ou para a SOS (com fogo)
    if (has(q, ['seafire', 'sea fire', 'sea-fire', 'sistema de incendio', 'supressao', 'disparo manual']) || seafireDisparo(q)) return 'seafire';
    // documento/licença antes do rádio: "Licença de estação" é documento, não MAYDAY
    if (has(q, ['document', 'licenc', ' tie ', 'titulo de inscricao', 'seguro da', 'apolice', 'laudo', 'vistoria', 'vencendo', 'certificado', 'garantia'])) return 'docsvenc';
    // o AIS tem a rota dele, antes do canal16 (PROMPT §2.2: a pergunta do AIS não é o roteiro MAYDAY nem liga a conversa em emergência); o MMSI foi para a rota mmsi, acima
    if (has(q, [' ais '])) return 'ais';
    if (has(q, ['canal 16', ' vhf', ' radio', ' dsc', 'pan-pan', 'pan pan'])) return 'canal16';
    if (has(q, ['contato', 'telefone', 'equipe', 'oficina', 'quem chamar', 'tecnico de bordo', 'marina da base'])) return 'contatos';
    // "bomba" sozinha é a de porão. Com o nome de outra bomba (água salgada, rotor, impeller, climatização, gerador, motor, estabilizador…) a
    // pergunta segue a rota do outro assunto ou o guia dele: "como trocar o rotor da bomba de água salgada" é o g_motores §7, e a resposta
    // pronta do porão ("Teste de bombas de porão e alarmes… SEM LEITURA") não responde. (Revisão 6 do C5: o trechoServe barra o guia de outro
    // equipamento quando a chave é 'porao'; antes do C5, e na revisão 4, a pergunta ia ao guia certo.)
    if (has(q, ['porao']) || (has(q, ['bomba']) && !has(q, OUTRA_BOMBA))) return 'porao';
    if (has(q, ['gerador', ' onan '])) return 'gerador';
    if (has(q, ['quantas horas'])) return 'horimetros';
    if (has(q, ['estabilizador', 'seakeeper'])) return 'estabilizador';
    if (has(q, ['rotacao', 'rotacoes', ' rpm ', 'giro do motor', 'giro dos motores', 'giro de motor'])) return 'motores';
    if (has(q, [' giro', 'giroscop'])) return 'estabilizador';
    if (has(q, ['climatiza', 'ar condicionado', 'ar-condicionado', 'setpoint', 'cabine'])) return 'climatizacao';
    if (has(q, [' ancora ', 'garrand', 'garrou', 'fundead', 'fundear', ' ferro '])) return 'ancora';
    if (has(q, ['piloto', 'plotter', 'radar', 'garmin', 'eletronic', 'autopilot', ' rota ', ' rotas ', 'standby', 'stby', 'cartas nauticas'])) return 'eletronicos';
    if (has(q, ['audio', 'fusion', ' som ', 'bluetooth', 'musica'])) return 'audio';
    if (has(q, ['dessalinizador', 'watermaker', 'water maker'])) return 'dessalinizador';
    if (has(q, ['manual', 'guia de bordo', 'guias de bordo'])) return 'manual';
    // revisão/inspeção de casco, anodos, zincos → agenda; de bateria/tensões → elétrico — não é revisão dos motores
    if (has(q, [' revisao', 'inspec'])) {
      if (has(q, ['casco', 'anodo', 'zinco'])) return 'manutencao';
      if (has(q, ['bateria', 'tensao', 'tensoes'])) return 'eletrico';
    }
    // "bateria de partida" é o banco de baterias (g_eletrico §1), não a partida do motor (revisão 6 do C5: caía na resposta pronta dos motores)
    if (has(q, ['bateria']) && has(q, ['partida']) && !has(q, ['motor', 'volvo', 'penta'])) return 'eletrico';
    if (has(q, ['motor', 'partida', 'volvo', 'penta', ' revisao'])) return 'motores';
    if (has(q, ['manutenc', 'vence', 'atrasad', 'agenda', 'tarefa'])) return 'manutencao';
    if (has(q, ['bateria', '24 v', '24v', '12 v', '12v', 'eletric', 'tensao', 'voltagem', 'carregador'])) return 'eletrico';
    if (has(q, ['posicao', 'onde estou', 'onde estamos', 'onde esta o barco', 'coordenada', ' gps', ' proa', ' rumo', ' cog ', ' sog ', 'quantos nos', 'velocidade'])) return 'posicao';
    // "Rajada" é a previsão do dia só em pergunta de previsão ("vai ter rajada hoje?", "como estão as rajadas?", "previsão de rajada"),
    // e depois das rotas de equipamento. "Hoje"/"agora" sozinhos não bastam: relato ("pegamos uma rajada agora e o barco adernou",
    // "a rajada de hoje arrancou o toldo", "a âncora garrou com a rajada"), pessoa em risco e limite do barco seguem o equipamento ou a IA.
    if (has(q, [' rajada']) && (RAJADA_SO.test(q) || has(q, ['previs', 'vai ter rajada', 'tem rajada', ' ha rajada', 'havera rajada', 'como estao as rajadas', 'como esta a rajada', 'como vao estar as rajadas']))
      && !has(q, RAJADA_RELATO)) return 'clima';
    // foraBarco (PROMPT §2.7): depois de todas as rotas de bordo e antes do fallback; local, sem IA, sem preço nem número
    if (has(q, FORA_BARCO)) return 'foraBarco';
    if (has(q, [' oi ', ' ola ', 'bom dia', 'boa tarde', 'boa noite', 'ajuda', 'o que voce faz', 'quem e voce']) || SOBRE.test(q)) return 'saudacao';
    return 'fallback';
  }
  // Pergunta sobre o próprio Capitão IA, com os jeitos comuns de digitar e falar: "Oque você faz?", "o que vc sabe", "quem é vc",
  // "como você funciona", "pra que serve".
  var SOBRE = / (?:o ?que|oq|q) (?:e que )?(?:voce|vc|tu) (?:faz|sabe|pode|consegue|responde)| quem (?:e|eh) (?:voce|vc|tu) | quem (?:voce|vc) e | como (?:voce|vc) funciona| como (?:funciona|uso|usar) (?:o |este |esse )?(?:app|aplicativo|capitao)| (?:para|pra) que (?:voce |vc )?serve/;
  // Só a palavra: "rajada?", "e as rajadas?", "rajada máxima".
  var RAJADA_SO = /^ (?:e )?(?:as? )?rajadas?(?: maximas?)? $/;
  // Relato, pessoa em risco ou limite do barco junto de "rajada": nunca a previsão do dia.
  var RAJADA_RELATO = ['aguent', 'suport', 'resist', 'limite', 'derrub', 'quebr', 'rasg', 'arrebent', 'arranc', 'voou', 'apag', 'deslig', 'virou',
    'adern', 'caiu', 'feri', 'machuc', 'pegamos', 'pegou', 'bateu', 'jogou', 'garr', 'alguem', 'tripulante', 'pessoa', 'o que faco', 'entrando'];

  var CANON = {}; ALL.forEach(function (x) { CANON[x.id] = norm(x.q).trim(); });

  // ——— Base de conhecimento de bordo (base-conhecimento.json) ———
  // Trechos dos guias de bordo (hoje, DEMO). Quando a resposta pronta não tem o dado, o chat e a voz buscam aqui
  // (BM25 com sinônimos PT/EN) e respondem com o trecho e a fonte. Carrega em segundo plano; funciona offline (cache do SW).
  var KB = { docs: null, carregando: false, df: {}, media: 1, nomes: {} };
  var PARADAS = ' a o e as os um uma uns umas de da do das dos em no na nos nas por para pra com sem se que qual quais quando como onde quanto quantos quantas e ou ao aos a is the of to and in on for with is are be it this that from at by an or eu voce vc me meu minha tem ter tenho ha esta estao fica ser sao era foi faz fazer posso pode sobre mais muito barco embarcacao capitao demo nao isso aqui registre registra registrar anote anota anotar grave gravar diario '.split(' ').reduce(function (m, w) { if (w) m[w] = 1; return m; }, {});
  var SINONIMOS = {
    gerador: ['onan', 'generator', 'genset'], estabilizador: ['seakeeper', 'gyro', 'giroscopio', 'stabilizer', 'volante'], giroscopio: ['seakeeper', 'gyro', 'estabilizador'],
    piloto: ['autopilot', 'automatico'], automatico: ['autopilot', 'piloto'], oleo: ['oil', 'lubrificante'], filtro: ['filter'], combustivel: ['fuel', 'diesel'], diesel: ['fuel', 'combustivel'],
    motor: ['engine', 'volvo', 'penta'], motores: ['engine', 'volvo', 'penta'], rotor: ['impeller'], impelidor: ['impeller', 'rotor'], impeller: ['rotor'], bomba: ['pump'], porao: ['bilge'],
    ar: ['climatizacao', 'condicionado'], climatizacao: ['condicionado', 'cabine'], condicionado: ['climatizacao'], incendio: ['fire', 'seafire'], fogo: ['fire', 'seafire'],
    bateria: ['battery', 'baterias'], baterias: ['battery', 'bateria'], ancora: ['anchor', 'ferro', 'fundear'], fundear: ['ancora'], ferro: ['ancora'],
    falha: ['fault', 'erro', 'alarme'], erro: ['fault', 'falha', 'alarme'], alarme: ['alarm', 'falha', 'codigo'], codigo: ['code', 'alarme'], temperatura: ['temperature'], pressao: ['pressure'],
    arrefecimento: ['coolant', 'refrigerante'], refrigerante: ['coolant', 'arrefecimento'], agua: ['water'], zinco: ['anode', 'anodo'], anodo: ['anode', 'zinco'],
    radar: ['garmin'], plotter: ['garmin', 'chartplotter'], som: ['fusion', 'audio'], audio: ['fusion', 'som'], radio: ['vhf'], vhf: ['radio', 'dsc'], ligar: ['partida', 'start', 'ligue'],
    partida: ['ligar', 'start'], desligar: ['parada', 'stop', 'parar', 'desligue'], manutencao: ['maintenance', 'revisao', 'agenda'], revisao: ['manutencao', 'service'], limpeza: ['limpe', 'cleaning'],
    capacidade: ['capacity', 'litros', 'volume'], superaquecer: ['temperatura', 'overheat', 'arrefecimento'], superaquecimento: ['temperatura', 'overheat', 'arrefecimento'], esquentando: ['temperatura', 'arrefecimento'],
    parear: ['emparelhar', 'pairing', 'conectar', 'bluetooth'], emparelhar: ['parear', 'bluetooth'], alarm: ['alarme'], lubrificante: ['oil', 'oleo'], tanque: ['tank'], mob: ['homem', 'mar'], homem: ['mob'],
    // Revisão 4 do C5: "quando trocar o óleo do motor?" achava só o §4 (pressão de óleo baixa) e não a agenda "Troca de óleo e filtros" (§7);
    // "botão distress" é o DSC do rádio e "o sistema descarregou" é o §3 "Depois da descarga" (a identidade do trecho de segurança,
    // abaixo, é o título dele). As chaves são a raiz() da palavra: distres = raiz('distress').
    trocar: ['troca', 'substituir'], troca: ['trocar'], distres: ['dsc'], descarregou: ['descarga'],
    // 1b (PROMPT §2.3): "baliza" é o EPIRB e "testar a baliza" é o teste dele (o §2 do g_epirb traz «teste» e «baliza»)
    baliza: ['epirb', 'radiobaliza']
  };
  // "testar" é "teste" só junto de baliza/EPIRB (o g_epirb §2 traz «teste» e «baliza»). Em geral não: "como testar as bombas de porão" voltava do g_porao §3
  // à resposta pronta do porão, local, e passou a ir à IA (revisão da 1b).
  var SINONIMOS_BALIZA = { testar: ['teste', 'autoteste'] };
  var BALIZA_RAIZES = {}; ['baliza', 'epirb', 'radiobaliza'].forEach(function (w) { BALIZA_RAIZES[raiz(w)] = 1; });
  // Baliza de sinalização não é o EPIRB (revisão da 1b, 4ª): com «canal», «cardinal», «lateral», «farol», «luz», «barra», «entrada», «piscando» ou «boia» na pergunta e sem palavra que
  // só o EPIRB tem (epirb, radiobaliza, autoteste, hidrostático, 406), o guia do EPIRB sai da busca. Sem isto, «por que a baliza do canal está piscando?» devolvia o «Disparo por engano:
  // desligue e avise no canal 16» (o sinônimo baliza→epirb e o «canal» fechavam os 60 %) e, por ser trecho de segurança, barrava a IA, que sabe de balizamento.
  var RAIZ_BALIZA = raiz('baliza');
  var SINAL_RAIZES = {}; ['canal', 'cardinal', 'lateral', 'farol', 'luz', 'barra', 'entrada', 'piscando', 'boia', 'boias', 'balizamento', 'balizar'].forEach(function (w) { SINAL_RAIZES[raiz(w)] = 1; });
  var EPIRB_SO = {}; ['epirb', 'radiobaliza', 'autoteste', 'hidrostatico', '406'].forEach(function (w) { EPIRB_SO[raiz(w)] = 1; });
  function raiz(w) { if (/^\d/.test(w)) return w; w = w.replace(/coes$/, 'cao').replace(/oes$/, 'ao').replace(/aes$/, 'ao'); return w.length > 4 ? w.replace(/(es|s)$/, '') : w; }
  // "ar" (2 letras) é palavra da busca ("como ligar o ar" é a climatização; o SINONIMOS.ar existia, mas o filtro de tamanho o tirava);
  // as demais palavras de até 2 letras seguem fora.
  // "ar condicionado" vale pela palavra "condicionado" (sinônimo de climatização): o "ar" sozinho puxaria o §4 "Fluxo de ar fraco".
  function tokens(t) {
    return norm(t).replace(/\bar[\s-]+condicionado\b/g, 'condicionado').replace(/[^a-z0-9]+/g, ' ').split(' ').filter(function (w) { return w && !PARADAS[w] && (w.length > 2 || w === 'ar' || /\d/.test(w)); }).map(raiz);
  }
  // Frases fixas que ficam no texto do trecho mas não entram no índice (revisão 3 do C5): o rótulo do procedimento padrão e a
  // nota da etiqueta (CONTRATO §1.5), no fim de todo trecho de g_seafire, g_epirb, Salvatagem e protocolo, e o "do equipamento"
  // depois de "etiqueta" (o equipamento do trecho já está na fonte). Repetidas em trechos curtos, punham o g_epirb §4 no topo de
  // "quais equipamentos tem a bordo?" e de "modelo dos equipamentos", e o trecho de segurança do topo barrava a IA.
  // (NOTA_ETIQUETA vem do D.protocolos, acima: o SOS carrega este arquivo e não lê o D.equipamentos; o gerador prende as duas notas iguais.)
  var FORA_DO_INDICE = [ROTULO, NOTA_ETIQUETA].map(function (f) { return norm(f); });
  function indexavel(t) {
    t = norm(t);
    FORA_DO_INDICE.forEach(function (f) { t = t.split(f).join(' '); });
    return t.replace(/\betiqueta do equipamento\b/g, 'etiqueta');
  }
  // Identidade do trecho de segurança (revisão 4 do C5): as palavras da fonte, do equipamento e do título da seção, menos as que só
  // dizem "guia", "protocolo", "sistema" ou "depois" ("sistema fixo" pesa pelo "fixo"; "como ligar o sistema de ventilação" não é o
  // Seafire). O trecho de segurança (g_seafire, g_epirb, protocolo, §4 dos motores e do porão…) só entra na busca se a pergunta nomeia
  // o assunto dele. Sem isso, os passos dele (desligue motores e gerador, corte a ventilação, não abra o acesso ao motor, depois da
  // descarga) casavam perguntas comuns ("como desligar a ventilação", "como religar o gerador depois de desligar"), mostravam o
  // procedimento de incêndio e, por ser de segurança, barravam a IA (pedeIA).
  // Palavras de acionamento (revisão 5 do C5): o trecho do protocolo que descreve uma situação (homem ao mar, pane) também é nomeado pelas
  // palavras com que a pessoa conta essa situação e que não estão no título ("caiu", "sem governo"); o gerador as põe em `ident`.
  // Revisão 6 do C5: "caiu" é o uso comum para disjuntor, energia e sinal ("o plotter caiu, como resolver" devolvia o protocolo de homem
  // ao mar, sem IA). O `ident` que conta uma pessoa em risco só vale junto de uma palavra de pessoa (`identCom`: pessoa, quem, alguém,
  // homem, tripulante…); sozinho, "caiu" não nomeia o trecho.
  // "manual" (título "Disparo manual") e "mar" ("Homem ao mar") são palavras comuns demais para nomear: "onde fica o manual do motor"
  // devolvia o disparo manual do Seafire e "tem vista para o mar?", o homem ao mar. "disparo" e "homem" continuam nomeando; "pessoa ao
  // mar" é o `ident` do protocolo com `identCom`.
  // Revisão 7 do C5: a identidade depende do guia. Num guia TODO de segurança (g_seafire, g_epirb, protocolo: todo trecho da fonte tem
  // `seguranca`) o equipamento é o assunto, e fonte, equip e título nomeiam o trecho. Num guia MISTO (o §4 dos motores e do porão, o §1 e o
  // §5 dos eletrônicos, o §2 do AIS, o checklist de saída) a seção de segurança é uma entre várias: o nome do equipamento não a nomeia, só o
  // título dela, sem o nome do equipamento. Antes, "onde fica o plotter", "como ver o radar" e "como ver o garmin" (o equip do g_eletronicos
  // traz Garmin, Fusion e Icom) devolviam o §1 "Plotter: homem ao mar", e "onde fica o motor", o §4 da pressão de óleo, com `seguranca`:
  // trecho de segurança no topo barra a IA, e a fala lê o trecho inteiro.
  var IDENT_GENERICAS = {}; tokens('guia bordo depois caso antes sistema procedimento padrao confirmar protocolo emergencia manual mar').forEach(function (w) { IDENT_GENERICAS[w] = 1; });
  function carregaBase() {
    if (KB.docs || KB.carregando || !window.fetch) return;
    KB.carregando = true;
    fetch('./base-conhecimento.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
      var lista = j && j.trechos; if (!lista || !lista.length) return;
      var soma = 0, df = {}, nomes = {}, todoSeguro = {};
      lista.forEach(function (d) { if (todoSeguro[d.fonte] !== 0) todoSeguro[d.fonte] = d.seguranca ? 1 : 0; });
      lista.forEach(function (d) {
        var sec = d.secao || '', tf = {}, tk = tokens(sec + ' ' + sec + ' ' + sec + ' ' + indexavel(d.texto) + ' ' + (d.fonte || '') + ' ' + (d.equip || ''));
        d._lista = /invent[aá]rio|cat[aá]logo|[íi]ndice/i.test(d.fonte || '');
        d._eq = {}; tokens((d.fonte || '') + ' ' + (d.equip || '')).forEach(function (w) { if (!IDENT_GENERICAS[w] && !/^\d/.test(w)) { d._eq[w] = 1; nomes[w] = 1; } });
        d._id = {};
        if (todoSeguro[d.fonte]) tokens((d.fonte || '') + ' ' + (d.equip || '') + ' ' + sec).forEach(function (w) { if (!IDENT_GENERICAS[w]) d._id[w] = 1; });
        else tokens(sec).forEach(function (w) { if (!IDENT_GENERICAS[w] && !d._eq[w]) d._id[w] = 1; });
        // `ident` = palavras de acionamento (valem mesmo as genéricas, como "mar" em "pessoa ao mar"); com `identCom`, só junto de uma delas na pergunta
        d._ia = {}; tokens(d.ident || '').forEach(function (w) { d._ia[w] = 1; });
        d._ic = null; if (d.identCom) { d._ic = {}; tokens(d.identCom).forEach(function (w) { d._ic[w] = 1; }); }
        d._en = (' ' + d.texto.toLowerCase() + ' ').split(/\b(?:the|and|with|to|of|is|are|your|from)\b/).length > 6;
        tk.forEach(function (w) { tf[w] = (tf[w] || 0) + 1; });
        Object.keys(tf).forEach(function (w) { df[w] = (df[w] || 0) + 1; });
        d._tf = tf; d._n = tk.length; soma += tk.length;
      });
      KB.df = df; KB.media = soma / lista.length; KB.nomes = nomes; KB.docs = lista;
    }).catch(function () {}).then(function () { KB.carregando = false; });
  }
  // Devolve até n trechos { d, nota } ou [] se nada for relevante o bastante.
  var PROCEDIMENTO = /\b(como|o que fazer|procedimento|passo|trocar|troca|ligar|desligar|parear|alarme|falha|codigo|superaquec\w*|oleo|capacidade)\b/;
  function buscaBase(q, n) {
    if (!KB.docs) { carregaBase(); return []; }
    var qs = tokens(q).filter(function (w, k, a) { return a.indexOf(w) === k; });
    if (!qs.length) return [];
    // cada palavra da pergunta vira um grupo (ela + sinônimos); o trecho precisa cobrir a maioria dos grupos
    var daBaliza = qs.some(function (w) { return BALIZA_RAIZES[w]; });
    var sinalizacao = daBaliza && qs.some(function (w) { return SINAL_RAIZES[w]; }) && !qs.some(function (w) { return EPIRB_SO[w]; }), fonteEpirb = guia('g_epirb');
    var grupos = qs.map(function (w) { var g = {}; g[w] = 1; ((sinalizacao && w === RAIZ_BALIZA) ? [] : (SINONIMOS[w] || (daBaliza && SINONIMOS_BALIZA[w]) || [])).forEach(function (x) { x = raiz(x); if (!g[x]) g[x] = 0.6; }); return g; });
    var N = KB.docs.length, k1 = 1.2, b = 0.75, res = [], proc = PROCEDIMENTO.test(' ' + norm(q) + ' ');
    KB.docs.forEach(function (d) {
      if (sinalizacao && d.fonte === fonteEpirb) return; // baliza de sinalização: o guia do EPIRB não responde (e «baliza» não vira «epirb», abaixo)
      var nota = 0, bateu = 0, secao = d._sec || (d._sec = ' ' + tokens(d.secao || '').join(' ') + ' '), naSecao = 0, nomeia = !d.seguranca, aciona = false;
      grupos.forEach(function (g) {
        var melhor = 0;
        for (var w in g) {
          var f = d._tf[w]; if (!f) continue;
          var idf = Math.log(1 + (N - KB.df[w] + 0.5) / (KB.df[w] + 0.5));
          melhor = Math.max(melhor, g[w] * idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * d._n / KB.media)));
          if (secao.indexOf(' ' + w + ' ') !== -1) naSecao++;
          if (d._id[w]) nomeia = true;
          if (d._ia[w]) aciona = true;
        }
        if (melhor > 0) { bateu++; nota += melhor; }
      });
      // palavra de acionamento ("caiu", "pane"): nomeia o trecho; se ele pede uma palavra de pessoa, a pergunta tem de trazê-la
      if (aciona && (!d._ic || qs.some(function (w) { return d._ic[w]; }))) nomeia = true;
      if (!nomeia) return; // trecho de segurança que a pergunta não nomeia (identidade, acima)
      if (naSecao >= grupos.length) nota *= 1.6; // o título da seção cobre a pergunta inteira
      if (d._lista && proc) nota *= 0.45;
      if (nota > 0 && bateu >= Math.min(2, grupos.length) && bateu >= Math.ceil(grupos.length * 0.6)) res.push({ d: d, nota: nota });
    });
    res.sort(function (x, y) { return y.nota - x.nota; });
    return res.slice(0, n || 3);
  }
  function citaFonte(d) { return d.fonte + (d.pag ? ', p. ' + d.pag : d.secao ? ' · §' + d.secao : ''); }
  function trechoCurto(t, max) {
    t = String(t || '').replace(/\s+/g, ' ').trim(); max = max || 480;
    if (t.length <= max) return t;
    var c = t.slice(0, max), m = c.match(/^[\s\S]*[.!?;](?=\s)/);
    return (m && m[0].length > max * 0.5 ? m[0] : c.slice(0, c.lastIndexOf(' ')) + '…');
  }
  var MAX_SEGURANCA = 1500;
  var GENERICAS = { gerador: 1, motores: 1, audio: 1, estabilizador: 1, eletronicos: 1, climatizacao: 1, dessalinizador: 1, eletrico: 1, porao: 1, ancora: 1, ais: 1, manual: 1, clima: 0 };
  var ESPECIFICA = /\b(como|trocar|troca|substitu\w*|parear|pareamento|conectar|codigo|codigos|alarme|alarmes|erro|falha|falhas|defeito|superaquec\w*|oleo|filtro|impeller|impelidor|rotor|capacidade|litros|pressao|temperatura|onde fica|localiza\w*|procedimento|passo|reset\w*|calibr\w*|configur\w*|limp\w*|intervalo|torque|especifica\w*|viscosidade|bluetooth|dsc|mob|zinco|anodo|fusivel|disjuntor|fluxo)\b/;
  // Resposta pronta de equipamento × trecho do guia (revisão 5 do C5). A resposta pronta (GENERICAS) só cede ao trecho do topo quando ele é
  // do assunto perguntado. Com os 91 trechos, "como ligar o plotter" trazia o "Ligar e transmitir" do radar ("ligue o radar pelo plotter"),
  // "como ligar o sistema de som" o §1 dos bancos de bateria ("sistema" e "ligar", por sinônimo de "partida") e "como funciona o sistema
  // elétrico" o §3 de verificação. Três condições:
  //  (1) o guia é um dos do equipamento da resposta (FAMILIA; sem entrada, qualquer guia);
  //  (2) se a pergunta diz o nome de algum equipamento (palavra exata da fonte ou do equip de algum trecho: "plotter" não vale por
  //      "garmin"), o trecho é de um equipamento que ela nomeia (na fonte, no equip ou no título da seção);
  //  (3) a pergunta traz algo além do nome do equipamento: uma palavra, ou sinônimo, que está no título ou no texto ("funciona" só vale
  //      se o título do trecho for o funcionamento).
  // Vale o 1º dos 3 trechos da busca que passa nas três; nenhum passa, fica a resposta pronta, como antes do C5. O trecho de segurança que
  // abre a busca (a pergunta o nomeia) não passa por aqui, e a pergunta sem resposta pronta (fallback) também não.
  // (a âncora também é do g_eletronicos: o alarme de âncora está no plotter, §3)
  var FAMILIA = { gerador: ['g_gerador'], motores: ['g_motores'], estabilizador: ['g_seakeeper'], climatizacao: ['g_clima'], dessalinizador: ['g_dessalinizador'],
    eletrico: ['g_eletrico'], porao: ['g_porao'], ancora: ['g_ancora', 'g_eletronicos'], ais: ['g_ais'], audio: ['g_eletronicos'], eletronicos: ['g_eletronicos', 'g_piloto', 'g_radar', 'g_ais'] };
  var SEM_ASSUNTO = {}; tokens('funciona funcionamento').forEach(function (w) { SEM_ASSUNTO[w] = 1; });
  function trechoServe(key, q, d) {
    var fam = FAMILIA[key];
    if (fam && !fam.some(function (g) { return d.fonte === guia(g); })) return false;
    var ws = tokens(q).filter(function (w, k, a) { return a.indexOf(w) === k && !IDENT_GENERICAS[w]; });
    var nomes = ws.filter(function (w) { return KB.nomes[w]; });
    var secao = d._sec || (d._sec = ' ' + tokens(d.secao || '').join(' ') + ' '); // o título também nomeia ("Piloto automático" no g_eletronicos §2)
    if (nomes.length && !nomes.some(function (w) { return d._eq[w] || secao.indexOf(' ' + w + ' ') !== -1; })) return false;
    // palavra que é nome do equipamento do trecho (ela ou um sinônimo dela está na fonte ou no equip: "ar" e "condicionado" são a
    // "climatização"; "som" é o "Fusion") não conta como assunto
    var nome = function (w) { return d._eq[w] || (SINONIMOS[w] || []).some(function (x) { return d._eq[raiz(x)]; }); };
    // "funciona" só conta como assunto se o título do trecho for o funcionamento ("Funcionamento" do porão); as outras, no título ou no texto
    return ws.some(function (w) {
      if (nome(w)) return false;
      if (SEM_ASSUNTO[w]) return secao.indexOf(' funcionamento ') !== -1;
      return d._tf[w] || (SINONIMOS[w] || []).some(function (x) { return d._tf[raiz(x)]; });
    });
  }
  function respostaBase(q, p, key) {
    var hits = buscaBase(q, 3); if (!hits.length) return null;
    // com resposta pronta (key), vale o 1º dos 3 trechos que serve ao assunto; o de segurança do topo (a pergunta o nomeia) passa direto
    var topo = !key || hits[0].d.seguranca ? hits[0] : hits.filter(function (x) { return trechoServe(key, q, x.d); })[0];
    if (!topo) return null;
    var h = topo.d, outros = hits.filter(function (x) { return x !== topo && (x.d.fonte !== h.fonte || x.d.secao !== h.secao); });
    // Trecho de segurança sai inteiro, com o rótulo do procedimento padrão e a nota da etiqueta no fim (CONTRATO §1.5): o corte de
    // 480 letras tirava os dois do §1 e do protocolo do Seafire (560) e a nota do §3 (492). O gerador limita esses trechos a 800.
    var text = trechoCurto(h.texto, h.seguranca ? MAX_SEGURANCA : 480) + (outros.length ? '\nVeja também: ' + outros.map(function (x) { return citaFonte(x.d); }).join(' · ') : '');
    // seguranca: o trecho do topo é de segurança (EPIRB, Seafire, salvatagem, protocolo…; o gerador marca) — o pedeIA não chama a IA
    return { text: text, src: 'Fonte: ' + citaFonte(h) + ' — base de conhecimento de bordo' + (h.equip ? ' · ' + h.equip : ''), actions: act(p, [['FAQ de bordo', 'faq']]), ref: citaFonte(h), ingles: !!h._en, seguranca: !!h.seguranca };
  }
  if (window.requestIdleCallback) requestIdleCallback(carregaBase, { timeout: 4000 }); else setTimeout(carregaBase, 1500);

  function responde(q, ctx) {
    ctx = ctx || {};
    var p = ctx.platform || 'web';
    var key = null;
    if (ctx.id && ANSWERS[ctx.id] && (!String(q || '').trim() || norm(q).trim() === CANON[ctx.id])) key = ctx.id;
    if (!key) key = route(q);
    if (!ANSWERS[key]) key = 'fallback';
    var a;
    try { a = ANSWERS[key](p, ctx, String(q || '').trim()); } catch (e) { key = 'fallback'; a = ANSWERS.fallback(p, ctx); }
    // toda resposta de dado de bordo leva a hora do instante (decisão 5): a que não a traz no texto nem na fonte ganha «consultado às HH:MM:SS» na fonte
    if (!SEM_HORA_NA_FONTE[key] && sim() && vivo() && a && a.src && !/\d\d:\d\d:\d\d/.test(a.text + '\n' + a.src)) a.src += ' · consultado às ' + vivo().hora;
    // Sem resposta pronta, ou pergunta específica sobre um equipamento (como, código, óleo, alarme, onde fica…): o trecho do guia vale mais que o resumo genérico.
    if (key === 'fallback' || (GENERICAS[key] && (ESPECIFICA.test(' ' + norm(q) + ' ') || (key === 'ais' && !AIS_STATUS.test(' ' + norm(q) + ' '))))) { var kb = null; try { kb = respostaBase(q, p, key === 'fallback' ? null : key); } catch (e) {} if (kb) { a = kb; key = 'base'; } }
    a.key = key;
    return a;
  }
  // a resposta leva o instante dela (fora do JSON): a ficha(p, q, a) e o resumoAgora(a) da MESMA pergunta o reaproveitam
  function marca(a) { if (a && typeof a === 'object' && !emerg(a)) { try { Object.defineProperty(a, '_inst', { value: CONG.inst, enumerable: false, configurable: true }); } catch (e) {} } return a; }
  function answer(q, ctx) { return congela(function () { return marca(responde(q, ctx)); }); }

  // ——— IA na nuvem (capitao-ia.js) ———
  // Quando a tela chama a IA: sem resposta pronta (SEM DADOS), trecho do guia (a IA responde a partir dele) ou pergunta sobre o
  // próprio app que vai além do cumprimento. Emergência, óleo, registro no diário e respostas prontas ficam 100% no aparelho:
  // rápidas, offline e com a fonte. "Oi", "bom dia, capitão" também — a saudação pronta basta e não gasta a cota.
  var SO_OI = /^(?: (?:oi|ola|opa|e ai|eai|hey|hello|hi|alo|bom dia|boa tarde|boa noite|tudo bem|tudo bom|td bem|beleza|capitao|ia))+ $/;
  // Trecho de segurança no topo (a.seguranca, do respostaBase) nunca vai à IA: fica o trecho local, com a fonte (PROMPT §2.3).
  // Revisão do C5: vale qualquer que seja a chave. A tela manda junto o buscaBase(q, 3), e uma saudação com assunto ("como você me
  // ajuda com o teste da baliza?") levava o g_epirb §2 no topo; o respostaBase só marca a chave base.
  function pedeIA(a, q) {
    var k = a && a.key;
    if (a && a.seguranca) return false;
    if (k !== 'fallback' && k !== 'base' && k !== 'saudacao') return false;
    var topo = String(q || '').trim() ? buscaBase(q, 1)[0] : null;
    if (topo && topo.d.seguranca) return false;
    if (k === 'fallback' || k === 'base') return true;
    return !!String(q || '').trim() && !SO_OI.test(pad(q));
  }
  // O que o app faz, para a IA responder "o que você faz?", "como registro?", "onde vejo os documentos?".
  // A frase padrão de quem pergunta se os dados ou o barco são reais (decisão (f); PROMPT §2.6): a resposta da rota sobreDados (P3C) e o fecho do «Sobre o app» da ficha,
  // que o SISTEMA da IA manda usar. Nunca afirma que é real.
  var SOBRE_DADOS = 'Esta é a embarcação de apresentação da plataforma Capitão IA: as leituras seguem o roteiro de navegação e mudam a cada segundo. Numa embarcação do cliente, os mesmos painéis leem o coletor NMEA de bordo.';
  // (uma função: o SOS carrega este arquivo e não lê o D.equipamentos, nem na carga)
  function sobreApp() {
    var sm = sim(), eqs = (D.equipamentos || []).filter(function (e) { return !e.seguranca && e.id !== 'eletrico'; }).map(function (e) { return min1(e.nome + (e.fabricante ? ' ' + e.fabricante : '')); }).join(', ');
    return [
      'O Capitão IA é o assistente de bordo desta embarcação: um app no celular e no computador, em português, que responde sempre com ' + (sm ? 'o número, a hora e a fonte.' : 'a fonte.'),
      // com simulacao false volta o «Sobre o app» da 1.0.9: o snapshot do coletor (ao vivo só com o coletor ligado) e a regra da casa «Nada inventado» (decisão 6)
      'Responde sobre: ' + (sm ? 'telemetria ao vivo do coletor NMEA de bordo (posição, rumo, velocidade, motores, óleo, arrefecimento, tanques, baterias, gerador, Seakeeper, porão, âncora), alarmes e a situação agora, manutenção e agenda (atrasadas, próximas, horímetros), documentos e vencimentos, abastecimento, consumo e autonomia, destinos e hora de chegada, diário de bordo (ler e registrar), equipe e contatos, clima e maré na posição de referência (Open-Meteo, tempo real)'
        : 'telemetria (snapshot do coletor NMEA; ao vivo quando o coletor estiver ligado), manutenção e agenda (atrasadas, próximas, horímetros), documentos e vencimentos, abastecimento, consumo e autonomia, diário de bordo (ler e registrar), equipe e contatos, clima e maré na posição de referência (Open-Meteo)')
        + ', passo a passo dos equipamentos (' + eqs + ') e checklist de saída e chegada.',
      'Jeitos de perguntar: digitar; VOZ→TEXTO (a fala vira texto); CONVERSA (voz contínua, sem tocar na tela, com o núcleo de anéis e o ∞ ao centro: toque nele para interromper, ENCERRAR para sair); FOTO e VÍDEO (não saem do aparelho e entram no diário como A CONFIRMAR); atalhos de um toque na home, editáveis em EDITAR ATALHOS.',
      'Registrar no diário: dizer ou digitar "registre no diário …" (o chat só grava com esse comando; o diário só cresce, nada se apaga). O atalho DIÁRIO DE BORDO grava o resumo da telemetria.',
      'Emergência: botão SOS em todas as telas — abre sem login e sem internet; VHF canal 16. Posição, rumo e velocidade na emergência: leia no plotter.',
      'Telas: Console (telemetria), Carta (gestão), Leme (manutenção), Documentos, Abastecimento, Diário, Equipe, FAQ de bordo por equipamento, SOS.',
      sm ? 'Sobre os dados: ' + SOBRE_DADOS : 'Regra da casa: nada inventado. Cada número vem com a fonte; sem fonte = SEM DADOS; sensor ausente = SEM LEITURA; foto ou nota = A CONFERIR / A CONFIRMAR.'
    ];
  }
  function agoraBR() {
    var ms = CONG.inst && CONG.inst.ms;   // a hora da ficha é a do instante da pergunta (a mesma da telemetria)
    try { return new Intl.DateTimeFormat('pt-BR', { timeZone: E.fuso || 'America/Sao_Paulo', weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(typeof ms === 'number' ? new Date(ms) : new Date()) + ' (horário de Brasília)'; } catch (e) { var n = now(); return n.d + ' ' + n.t; }
  }
  // Coordenadas não saem do aparelho (posição do barco só depois do login no servidor).
  function semCoord(s) { return String(s || '').replace(/\d{1,3}\s?°\s?\d{1,2}(?:,\d+)?\s?['′]\s?[NSLOEW]\s*\d{1,3}\s?°\s?\d{1,2}(?:,\d+)?\s?['′]\s?[NSLOEW]/g, '(coordenadas só na tela do app)'); }
  // Ficha de bordo para a IA na nuvem: o que o app sabe agora, bloco a bloco, com a fonte de cada um — os mesmos textos das
  // respostas prontas, então a IA e a tela dizem os mesmos números. Sem coordenadas e sem telefones. ~9 mil letras
  // (o proxy aceita até 12 mil). ficha(p, q, a): pergunta pura sobre o próprio app ("o que você faz?") leva só a ficha
  // RESUMIDA (agora, sobre o app, embarcação, equipamentos — ~3 mil letras). Com assunto ("o que você sabe sobre o
  // seguro?") ou trecho do guia ("quando foi a última troca de óleo?"), a completa: a resumida tirava o dado pedido (1.0.7).
  var ASSUNTO = / (?:sobre|de|do|da|dos|das|no|na|com|quando|qual|quais|quanto|onde) (?!(?:voce|vc|app|aplicativo|capitao|ia|mim|tudo|bordo) )[a-z]/;
  function fichaResumida(q, a) { var s = pad(q); return !!a && a.key === 'saudacao' && SOBRE.test(s) && !ASSUNTO.test(s.replace(SOBRE, ' ')); }
  function ficha(p, q, a) { return congela(function () { return ficha1(p, q, a); }, a && a._inst); }
  function ficha1(p, q, a) {
    p = p || 'app';
    var out = [], emergencia = emerg(a);   // resposta de emergência: a ficha sai sem os blocos do quadro (Telemetria, Horímetros, Autonomia e consumo)
    var bloco = function (titulo, f) { if (emergencia && QUADRO[titulo]) return; try { var a = f(); if (a && a.text) out.push('## ' + titulo + '\n' + semCoord(a.text) + (a.src ? '\n(' + semCoord(a.src) + ')' : '')); } catch (e) {} };
    out.push('## Agora\n' + agoraBR() + ' · usuário: ' + quem() + (D.demo && !sim() ? '\n' + (D.selo || 'DEMO') + ': ' + (D.aviso || '') : ''));
    out.push('## Sobre o app\n' + sobreApp().join('\n'));
    out.push('## Embarcação\n' + (E.nome || SD) + ' · fabricante e modelo ' + (E.modelo || SD) + ' · registro ' + (E.registro || SD) + ' · proprietário ' + (E.proprietario || SD) + ' · base ' + (E.base || SD) + ' · ' + mmsiNum() + ' (cadastro do app) · indicativo: ' + INDICATIVO + '\n(Fonte: ' + (E.fonte || SD) + ')');
    out.push('## Equipamentos\n' + (D.equipamentos || []).map(function (e) { if (e.seguranca) return '• ' + e.nome + ': ' + (e.nota || NOTA_ETIQUETA); return '• ' + e.nome + ': ' + (e.fabricante || 'fabricante ' + SD) + ' · modelo ' + (e.modelo || SD) + (e.qtd && e.qtd !== SD ? ' · ' + e.qtd + (e.lados ? ' (' + e.lados + ')' : '') : ''); }).join('\n') + '\n(Fonte: Inventário de bordo' + demo() + (D.equipNota ? ' · ' + D.equipNota : '') + ')');
    if (fichaResumida(q, a)) {
      out.push('## Ficha resumida\nEsta pergunta veio só com o resumo acima (sobre o app e o barco) e, se houver, os trechos do guia. Telemetria, manutenção, documentos, diário e equipe não vieram: para um dado desses, diga que o app mostra ao perguntar pelo assunto (ex.: "telemetria", "próximas manutenções").');
      return out.join('\n\n');
    }
    bloco('Telemetria', function () { return ANSWERS.telemetria(p); });
    bloco('Manutenção', function () { return ANSWERS.manutencao(p); });
    bloco('Horímetros', function () { return ANSWERS.horimetros(p); });
    bloco('Autonomia e consumo', function () {
      var a = ANSWERS.autonomia(p), ab = D.abastecimentos || [];
      return { text: a.text + (ab.length ? '\nAbastecimentos registrados: ' + ab.map(function (x) { return x.d + ' · ' + mil(x.litros) + ' L de ' + (x.combustivel || 'diesel') + ' · ' + (x.local || SD) + (x.st ? ' · ' + x.st : ''); }).join(' | ') + '.\nRegra: ' + (D.regraAbast || SD) + '.' : ''), src: a.src };
    });
    bloco('Documentos', function () { return ANSWERS.docsvenc(p); });
    bloco('Pendências', function () { return ANSWERS.anomalias(p); });
    bloco('Diário de bordo', function () { return ANSWERS.diarioLer(p); });
    bloco('Equipe e contatos', function () { return ANSWERS.contatos(p, { semBordo: true }); });   // (a situação de bordo da resposta não vai na ficha: o bloco Telemetria já a traz, e a ficha de emergência não leva o quadro)
    bloco('Clima e maré', function () {
      var pv = previsao(), m = mareTexto(), s = sim();
      var l1 = pv ? 'Previsão de hoje em Balneário Camboriú (' + pv.fonte + '): ' + pv.temp + ' · ' + pv.vento + '. O app não tem limite de vento para dizer se é seguro sair.' : s ? semConexao() : 'Previsão do dia: ' + SD + ' (sem leitura de hoje neste aparelho).';
      var l2 = m ? 'Maré agora ' + m.agora + ' em relação ao nível médio do mar · próximas horas: ' + m.prox.join(' · ') + ' — modelo, não a tábua oficial da Marinha (DHN).' : s ? (pv ? 'Maré: sem conexão agora — confira a tábua da Marinha (DHN) antes de sair.' : '') : 'Maré: ' + SD + ' agora (Open-Meteo Marine sem resposta).';
      var l3 = s ? 'Ondas: o app não tem previsão de mar — meteorologia marinha da Marinha do Brasil.' : (pv ? 'Previsão do mar (ondas): ' : 'Previsão de vento e mar para navegar: ') + SD + ' no app — meteorologia marinha da Marinha do Brasil.';
      return { text: l1 + (l2 ? '\n' + l2 : '') + '\n' + l3, src: 'Fonte: ' + (pv ? 'previsão ' + pv.fonte : 'previsão Open-Meteo: sem leitura de hoje neste aparelho') + ' · maré Open-Meteo Marine · na posição de referência · vento, pressão e temperaturas de bordo no bloco Telemetria' };
    });
    bloco('Guias de bordo', function () { return ANSWERS.manual(p); });
    out.push('## Emergência\nAbrir o SOS do app. ' + SOS_FICHA + '\n(' + FT.proto + ')');
    return out.join('\n\n');
  }

  // Anexos (foto/vídeo): não saem do aparelho — viram linha A CONFIRMAR no diário.
  function answerAttachment(kind, file, ctx) { return congela(function () { return marca(anexo1(kind, file, ctx)); }); }
  function anexo1(kind, file, ctx) {
    var p = (ctx && ctx.platform) || 'web';
    var name = file && file.name ? file.name : (kind === 'video' ? 'vídeo' : 'foto');
    var kb = file && file.size ? Math.round(file.size / 1024) + ' KB' : '';
    var n = now(), grava = !ctx || ctx.commit !== false, nao = 'não anexei ao diário (pedido vindo de link).';
    if (grava) addDiario({ sys: 'Equipamentos', tone: 'var(--cap-accent, #00a1fe)', t: (kind === 'video' ? 'Vídeo' : 'Foto') + ' anexada pelo chat: ' + name + (kb ? ' (' + kb + ')' : '') + ' — identificação A CONFIRMAR.', who: quem(), src: 'app · ' + kind });
    if (kind === 'video') return { key: 'video', text: 'Vídeo recebido (' + name + (kb ? ' · ' + kb : '') + ') · ' + n.d + ' ' + n.t + '.\nO som e o comportamento não são analisados automaticamente: ' + (grava ? 'anexei ao diário como anomalia A CONFIRMAR.' : nao) + '\n' + linhaBordo() + '\nDescreva em uma frase o que você viu ou ouviu — respondo com o que verificar primeiro.', src: 'Fonte: anexo · diário de bordo', actions: act(p, [['Abrir diário', 'diario']]) };
    return { key: 'foto', text: 'Foto recebida (' + name + (kb ? ' · ' + kb : '') + ') · ' + n.d + ' ' + n.t + '.\nA leitura da imagem não é automática: ' + (grava ? 'anexei ao diário como A CONFIRMAR.' : nao) + ' Para etiqueta ou tela de alarme, digite o modelo/código que aparece e eu localizo o guia; para nota fiscal, registre em Abastecimento (fica A CONFIRMAR).\n' + linhaBordo(), src: 'Fonte: anexo · diário de bordo', actions: act(p, [['Abrir diário', 'diario'], ['Documentos', 'docs']]) };
  }

  function safeDecode(s) { try { return decodeURIComponent(String(s).replace(/\+/g, '%20')); } catch (e) { return String(s); } }
  function parseHash() {
    var raw = (location.hash || '').replace(/^#/, '');
    var out = {};
    if (!raw) return out;
    raw.split('&').forEach(function (kv) {
      var i = kv.indexOf('=');
      if (i > 0) out[safeDecode(kv.slice(0, i))] = safeDecode(kv.slice(i + 1));
      else if (kv) out[safeDecode(kv)] = true;
    });
    if (typeof out.q === 'string') out.q = out.q.slice(0, 500); else delete out.q;
    return out;
  }
  function clearHash() { try { history.replaceState(null, '', location.pathname + location.search); } catch (e) {} }

  function recognizer(opts) {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return null;
    var r = new SR();
    r.lang = 'pt-BR'; r.interimResults = true; r.continuous = !!(opts && opts.continuous); r.maxAlternatives = 1;
    return r;
  }
  // ---- Voz (conversa ativa) ----
  // falavel(): texto de tela → português falado. Regras em ordem, guiadas pelas tabelas; sem lookbehind (Safari antigo).
  var MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
  var HEMI = { N: 'norte', S: 'sul', L: 'leste', E: 'leste', O: 'oeste', W: 'oeste' };
  var LET = 'A-Za-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u00FF', MAI = 'A-Z\\u00C0-\\u00D6\\u00D8-\\u00DE'; // letras latinas (em escape: não quebra se o .js vier sem UTF-8)
  // palavra inteira: o grupo 1 guarda o caractere anterior (reposto como $1)
  function rx(core) { return new RegExp('(^|[^' + LET + '\\d])(?:' + core + ')(?![' + LET + '\\d])', 'g'); }
  // unidades — só logo depois de número: [símbolo, singular, plural]; as mais longas primeiro
  var UNID = [
    ['km/h', 'quilômetro por hora', 'quilômetros por hora'], ['L/h', 'litro por hora', 'litros por hora'], ['kWh', 'quilowatt-hora', 'quilowatts-hora'],
    ['kW', 'quilowatt', 'quilowatts'], ['km', 'quilômetro', 'quilômetros'], ['hPa', 'hectopascal', 'hectopascais'], ['MHz', 'megahertz', 'megahertz'],
    ['kHz', 'quilohertz', 'quilohertz'], ['rpm|RPM', 'rotação por minuto', 'rotações por minuto'], ['min', 'minuto', 'minutos'],
    ['mn|NM|MN', 'milha náutica', 'milhas náuticas'], ['kts?|kn|nós|nó', 'nó', 'nós'], ['KB', 'quilobyte', 'quilobytes'], ['MB', 'megabyte', 'megabytes'],
    ['Ah', 'ampère-hora', 'ampères-hora'], ['bar', 'bar', 'bar'], ['L', 'litro', 'litros'], ['h', 'hora', 'horas'], ['m', 'metro', 'metros'], ['s', 'segundo', 'segundos'],
    ['d', 'dia', 'dias'], ['V', 'volt', 'volts'], ['W', 'watt', 'watts'], ['A(?!\\s+[' + MAI + ']{2})', 'ampère', 'ampères']
  ].map(function (u) { return { re: new RegExp('(^|[^' + LET + '\\d.,])(\\d+(?:[.,]\\d+)*)\\s?(?:' + u[0] + ')(\\+?)(?![' + LET + '\\d])', 'g'), um: u[1], varios: u[2] }; });
  // siglas e abreviações por extenso (palavra inteira, maiúsculas exatas)
  var SIGLAS = [
    ['NF-e', 'nota fiscal eletrônica'], ['NF', 'nota fiscal'], ['BB', 'bombordo'], ['BE', 'boreste'], ['SOG', 'velocidade sobre o fundo'],
    ['COG', 'rumo sobre o fundo'], ['STBY', 'standby'], ['MOB', 'homem ao mar'], ['AC', 'corrente alternada'], ['DC', 'corrente contínua'],
    ['RPM', 'rotação'], ['PAN-PAN', 'pan pan'], ['[Nn][º°]', 'número'], ['IA', 'i a'], ['TIE', 'título de inscrição'], ['máx\\.?', 'máximo'], ['mín\\.?', 'mínimo'],
    ['Sr\\.', 'senhor'], ['Sra\\.', 'senhora'], ['ref\\.', 'referência'], ['cert\\.', 'certificado']
  ].map(function (x) { return [rx(x[0]), '$1' + x[1]]; });
  // símbolos → fala ou pausa
  var SIMB = [
    [/Rev\. ?(?=\d)/g, 'revisão '], [/§ ?/g, 'seção '], [/(\d)-(?=\d)/g, '$1 '],
    [/\s*±\s*/g, ' mais ou menos '], [/\s*[≈~]\s*/g, ' cerca de '], [/\s*≤\s*/g, ' até '], [/\s*≥\s*/g, ' pelo menos '],
    [new RegExp('(\\d)\\s*×\\s*(?=[' + LET + '])', 'g'), '$1 '], [/×\s*(\d+)/g, '$1 vezes'], [/\s*×\s*/g, ' vezes '],
    [/\s+\+\s+/g, ' mais '], [/(^|\s)\+(?=\d)/g, '$1mais '], [/\s*%/g, ' por cento'],
    [new RegExp('([' + LET + '])→(?=[' + LET + '])', 'g'), '$1 para '], [/\s*[•·→›|—–=()\[\]]\s*/g, ', '],
    [/\.(pdf|csv|jsonl?|jpe?g|png|mp4|mov|txt)(?![A-Za-z])/gi, function (m, e) { return ' ' + e.toUpperCase(); }], [/(?:\s*_)+\s*/g, ' '],
    [new RegExp('([' + LET + '])\\s*/\\s*(?=\\d)', 'g'), '$1 ou '], [/\s*\/\s*/g, ', ']
  ];
  // MAIÚSCULAS de 4+ letras viram minúsculas (senão o TTS soletra), com as palavrinhas do mesmo trecho; siglas lidas como tal ficam.
  var SIGLA_OK = ' VHF AIS GPS MMSI EPIRB NMEA DHN SOS DSC ';
  var MIUDAS = ' A O E É AS OS DE DA DO DAS DOS EM NA NO NAS NOS AO AOS À ÀS UM UMA SEM COM POR PARA OU QUE SE SÓ JÁ NÃO HÁ ';
  var CAIXA = new RegExp('(^|[^' + LET + '\\d-])([' + MAI + ']+(?: [' + MAI + ']+)*)(?![' + LET + '\\d-])', 'g');
  function minusculas(s) {
    var grande = function (w) { return w.length >= 4 && /[AEIOUÁÉÍÓÚÂÊÔÃÕÀ]/.test(w) && SIGLA_OK.indexOf(' ' + w + ' ') === -1; };
    return s.replace(CAIXA, function (m, a, run) {
      var ws = run.split(' ');
      if (!ws.some(grande)) return m;
      return a + ws.map(function (w) { return grande(w) || MIUDAS.indexOf(' ' + w + ' ') !== -1 ? w.toLowerCase() : w; }).join(' ');
    });
  }
  var FRACAO = { '1/2': 'meio', '1/3': 'um terço', '2/3': 'dois terços', '1/4': 'um quarto', '3/4': 'três quartos' };
  var DATA_ANTES = new RegExp('(?:^|[^' + LET + '])(?:em|dia|até|ate|desde|de|data|prazo|vence|venceu|vencimento) $', 'i'), DATA_FRACA = new RegExp('(?:^|[^' + LET + '])(?:de|até|ate) $', 'i');
  // fração antes de unidade: 1/2 h → meia hora, 1/2 L → meio litro, 1/2 milha → meia milha, 1/4 L → um quarto de litro
  var FRACAO_UNID = { 'L/h': 'litro por hora', L: 'litro', h: 'hora', mn: 'milha náutica', NM: 'milha náutica', hora: 'hora', milha: 'milha', volta: 'volta', polegada: 'polegada' }, FEM = /^(?:hora|milha|volta|polegada)/;
  var FRACAO_UN = new RegExp('(^|[^\\d\\/,.])([123])\\/([234]) ?(L\\/h|L|h|mn|NM|hora|milha|volta|polegada)(?![' + LET + '\\d\\/])', 'g');
  function hora(h) { return h + (h < 2 ? ' hora' : ' horas'); }
  // Horário: "13:23" → "13 horas e 23 minutos" (":00" → "13 horas"); duração "1 h 10" → "1 hora e 10 minutos".
  function falavel(text) {
    // teto de 4.000 letras (fala longa não trava a tela); espaços repetidos viram um só antes das regras
    var s = String(text == null ? '' : text).slice(0, 4000).replace(/[“”"«»]/g, '').replace(/[ \t]/g, ' ').replace(/…/g, ', ');
    // linha = frase; marcador de lista no começo da linha some (a quebra já é pausa)
    s = s.split(/\r?\n/).map(function (l) { return l.replace(/^[\s•·→›—–]+/, '').trim(); }).filter(Boolean)
      .map(function (l, i, a) { return i < a.length - 1 && !/[.!?:;,]$/.test(l) ? l + '.' : l; }).join(' ').replace(/\s+/g, ' ');
    // coordenadas 26°59,58'S → 26 graus e 59 vírgula 58 minutos sul
    s = s.replace(/(\d{1,3}) ?° ?(\d{1,2})(?:,(\d+))? ?['′] ?([NSLOEW])(?![A-Za-z])/g, function (m, g, mi, fr, h) {
      g = +g; mi = +mi;
      return g + (g === 1 ? ' grau e ' : ' graus e ') + mi + (fr ? ' vírgula ' + fr + ' minutos ' : mi === 1 ? ' minuto ' : ' minutos ') + HEMI[h];
    }).replace(/(minutos? (?:norte|sul|leste|oeste)) (?=\d)/g, '$1, ');
    // dinheiro R$ 5.480,50 → 5.480 reais e 50 centavos
    s = s.replace(/R\$ ?(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{2}))?(?!\d)/g, function (m, r, c) {
      var cv = c ? +c : 0, cent = cv ? cv + (cv === 1 ? ' centavo' : ' centavos') : '';
      return r === '0' && cent ? cent : r + (r === '1' ? ' real' : ' reais') + (cent ? ' e ' + cent : '');
    });
    // intervalos 8–14 / 8-14 → 8 a 14 (hífen só entre números curtos); escala 1:50.000 → 1 para 50.000; data + hora ganha "às"
    s = s.replace(/(\d) ?– ?(?=\d)/g, '$1 a ').replace(new RegExp('(^|[^' + LET + '\\d-])(\\d{1,3})-(\\d{1,3})(?![\\d-])', 'g'), '$1$2 a $3')
      .replace(/(^|[^\d:,.])(\d+):(\d{1,3}(?:\.\d{3})+|\d{3,})(?![\d:])/g, '$1$2 para $3').replace(/(\d{1,2}\/\d{1,2}(?:\/\d{4})?) (?=\d{1,2}:\d{2}(?!\d))/g, '$1 às ');
    s = s.replace(FRACAO_UN, function (m, a, d, me, u) {
      var fr = FRACAO[d + '/' + me], nome = FRACAO_UNID[u];
      if (!fr) return m;
      return a + (fr === 'meio' ? (FEM.test(nome) ? 'meia ' : 'meio ') + nome : fr + ' de ' + nome);
    });
    // datas 20/09 → 20 de setembro; 16/01/2027; jan/2031. d/m de um dígito só é data com ano, hora ou palavra de data antes;
    // 1/4 de volta → um quarto de volta; 24/7 → 24 por 7; outro par curto → 5 barra 6.
    s = s.replace(/(^|[^\d\/])(\d{1,2})\/(\d{1,2})(?:\/(\d{4}))?(?![\d\/])/g, function (m, a, d, me, y, i, all) {
      var dd = +d, mm = +me, data = dd >= 1 && dd <= 31 && mm >= 1 && mm <= 12, fr = d.length === 1 && me.length === 1 && FRACAO[d + '/' + me];
      var ctx = (i > 24 ? 'x' : '') + all.slice(Math.max(0, i - 24), i + a.length), antes = DATA_ANTES.test(ctx), depois = all.slice(i + m.length, i + m.length + 12);
      if (!y && !antes && d === '24' && me === '7') return a + '24 por 7';
      if (!y && d.length === 1 && me.length === 1 && !/^ às? \d/.test(depois)) {
        if (fr && /^ d(?:e|o|a|os|as) (?!\d)/.test(depois) && (!antes || DATA_FRACA.test(ctx))) return a + fr;
        if (!antes || !data) return a + (fr || d + ' barra ' + me);
      }
      return data ? a + (dd === 1 ? 'primeiro' : dd) + ' de ' + MESES[mm - 1] + (y ? ' de ' + y : '') : m;
    }).replace(new RegExp('(^|[^' + LET + '])(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)/(\\d{4})(?!\\d)', 'gi'), function (m, a, me, y) {
      return a + MESES['janfevmarabrmaijunjulagosetoutnovdez'.indexOf(me.toLowerCase()) / 3] + ' de ' + y;
    });
    // horário 13:23 / 23h01 (nunca razão) e duração 1 h 10 / 6 h 58 min
    s = s.replace(/(^|[^\d:,.])(\d{1,2})(?::|h)(\d{2})(?:min(?![A-Za-z]))?(?![\d:]|\.\d)/g, function (m, a, h, mi) {
      h = +h; mi = +mi;
      return h > 23 || mi > 59 ? m : a + hora(h) + (mi ? ' e ' + mi + (mi === 1 ? ' minuto' : ' minutos') : '');
    }).replace(/ às ([01] hora)(?!s)/g, ' à $1').replace(/(^|[^\d,.])(\d+) ?h ?(\d{1,2})(?: ?min(?![A-Za-z])|(?![\d,.:\/]\d|\d| ?[A-Za-z%°]))/g, function (m, a, h, mi) {
      mi = +mi;
      return a + hora(+h) + (mi ? ' e ' + mi + (mi === 1 ? ' minuto' : ' minutos') : '');
    });
    // graus: 22,6 °C → graus Celsius; proa 071° → 71 graus
    s = s.replace(/(^|[^\d,])(\d+(?:,\d+)?) ?° ?C(?![A-Za-z])/g, function (m, a, n) { return a + n + (n === '1' ? ' grau' : ' graus') + ' Celsius'; })
      .replace(/(^|[^\d,])(\d+)(,\d+)? ?°/g, function (m, a, n, f) { n = +n + (f || ''); return a + n + (n === '1' ? ' grau' : ' graus'); });
    // D-17 (dias até) → D menos 17; MMSI dígito a dígito, como no rádio
    s = s.replace(new RegExp('(^|[^' + LET + '\\d])D-(\\d+)(?!\\d)', 'g'), '$1D menos $2')
      .replace(/MMSI:? ?(\d{9})(?!\d)/g, function (m, n) { return 'MMSI ' + n.split('').join(' '); });
    // decimal sem zeros à direita (34,0 → 34; 156,800 → 156,8), depois unidades, siglas e símbolos
    s = s.replace(/(\d),(\d*?)0+(?!\d)/g, function (m, a, b) { return b ? a + ',' + b : a; });
    UNID.forEach(function (u) { s = s.replace(u.re, function (m, a, n, mais) { return a + n + ' ' + (n === '1' ? u.um : u.varios) + (mais ? ' ou mais' : ''); }); });
    SIGLAS.forEach(function (x) { s = s.replace(x[0], x[1]); });
    s = s.replace(/°/g, ' graus');
    s = s.replace(/\s+/g, ' ');
    SIMB.forEach(function (x) { s = s.replace(x[0], x[1]); });
    s = minusculas(s);
    // 3.2 → 3 ponto 2 (milhar 1.500 fica); 27,42 → 27 vírgula 42
    s = s.replace(/(^|[^\d.])(\d+(?:\.\d+)+)/g, function (m, a, n) { var g = n.split('.'); return a + (g.slice(1).every(function (x) { return x.length === 3; }) ? n : g.join(' ponto ')); })
      .replace(/(\d),(?=\d)/g, '$1 vírgula ');
    // pontuação: um só sinal por pausa (o mais forte), sem ". ." nem ", :"
    return s.replace(/\s+/g, ' ').replace(/\s*([,;:.!?](?:\s*[,;:.!?])*)\s*/g, function (m, p, i, all) {
      if (m.length === 1 && /\d/.test(all.charAt(i - 1)) && /\d/.test(all.charAt(i + 1))) return m;
      return (/[?!]/.test(p) ? p.match(/[?!]/)[0] : p.indexOf('.') !== -1 ? '.' : /[:;]/.test(p) ? p.match(/[:;]/)[0] : ',') + ' ';
    }).replace(/^[\s,;:.!?]+|[\s,;:]+$/g, '');
  }

  // Melhor voz pt-BR: neural/online › Google › Apple premium/enhanced › Luciana/Felipe › qualquer pt-BR › qualquer pt. Nunca outro idioma.
  var VOZ = { v: null, on: null, ruim: {} };
  var VOZ_PREF = [[/natural|neural/i, 600], [/online/i, 550], [/google/i, 500], [/premium/i, 450], [/enhanced|aprimorad|melhorad/i, 400], [/luciana|felipe/i, 300]];
  function notaVoz(v, on) {
    var lang = String(v.lang || '').replace(/_/g, '-').toLowerCase(), nome = String(v.name || ''), id = nome + ' ' + (v.voiceURI || '');
    if (!/^(pt|por)(-|$)/.test(lang) || VOZ.ruim[nome]) return 0;
    var n = /-bra?$/.test(lang) || (/^(pt|por)$/.test(lang) && /bra[sz]il/i.test(nome)) ? 2000 : 1000;
    for (var j = 0; j < VOZ_PREF.length; j++) if (VOZ_PREF[j][0].test(id)) { n += VOZ_PREF[j][1]; break; }
    if (!on && v.localService === false) n -= 700; // sem internet a voz de rede não fala
    if (/eloquence/i.test(v.voiceURI || '') || /^(eddy|flo|grandma|grandpa|reed|rocko|sandy|shelley)\b/i.test(nome)) n -= 50; // vozes-novidade da Apple
    // voz masculina ganha de voz feminina do mesmo nível (natural/online), mas nunca de uma voz bem mais natural
    return n + (/antonio|felipe|donato|fabio|humberto|julio|nicolau|valerio|daniel|ricardo/i.test(nome) ? 120 : 0) + (v.default ? 1 : 0);
  }
  function vozPtBr() {
    var ss = window.speechSynthesis, on = !(window.navigator && window.navigator.onLine === false), lista = [], best = null, nota = 0;
    if (VOZ.v && VOZ.on === on) return VOZ.v;
    try { lista = (ss && ss.getVoices && ss.getVoices()) || []; } catch (e) {}
    for (var j = 0; j < lista.length; j++) { var n = notaVoz(lista[j], on); if (n > nota) { nota = n; best = lista[j]; } }
    VOZ.v = best; VOZ.on = on;
    return best;
  }
  // as vozes chegam depois (Chrome começa com lista vazia): pede já e refaz a escolha quando a lista mudar
  (function () {
    var ss = window.speechSynthesis, zera = function () { VOZ.v = null; };
    if (!ss) return;
    try { ss.getVoices(); if (ss.addEventListener) ss.addEventListener('voiceschanged', zera); else if (!ss.onvoiceschanged) ss.onvoiceschanged = zera; } catch (e) {}
  })();
  // Frases inteiras em blocos de até ~200 letras: prosódia melhor e sem o corte do Chrome em falas longas (~15 s).
  function blocos(s) {
    var MAX = 200, out = [];
    (function junta(partes, sep, nivel) {
      var cur = '';
      partes.forEach(function (p) {
        if (!p) return;
        if (p.length > MAX && nivel < 2) { if (cur) out.push(cur); cur = ''; junta(nivel ? p.split(' ') : p.split(/,\s+/), nivel ? ' ' : ', ', nivel + 1); return; }
        if (cur && (cur + sep + p).length > MAX) { out.push(cur); cur = p; } else cur = cur ? cur + sep + p : p;
      });
      if (cur) out.push(cur);
    })(s.replace(/([.!?;])\s+/g, '$1\n').split('\n'), ' ', 0);
    return out;
  }
  // Vigia de cada bloco calculada a 1x: 95 ms/letra (folga) + 250 ms/dígito, porque número falado é longo. A voz vai a
  // 1,15x (RATE), então a fala acaba antes e a vigia só fica mais folgada.
  function estimaMs(t) { return Math.min(60000, 2000 + t.length * 95 + (t.match(/\d/g) || []).length * 250); }
  var FALA = { gen: 0, timer: null, vivo: null, fila: [] };
  var RATE = 1.15; // velocidade da voz em TODA fala, inclusive emergência (SOS, óleo, EPIRB, Seafire) — decisão do proprietário
  function calaTimers() { clearTimeout(FALA.timer); clearInterval(FALA.vivo); FALA.timer = FALA.vivo = null; }
  // Eventos 'capitao-voz' ({ estado: ouvindo | pensando | falando | pulso | livre, texto, segura?, som? }) — núcleo de IA
  // (capitao-voz.js). segura: esperando a IA na nuvem (vozPensando). som (no 'falando'): a voz está tocando (true, no onstart)
  // ou calada (false: antes de o bloco começar e no fim dele) — o rosto abre a boca e solta as ondas só com som.
  function evVoz(estado, texto, extra) {
    var det = { estado: estado, texto: texto || '' };
    if (extra) for (var k in extra) if (Object.prototype.hasOwnProperty.call(extra, k)) det[k] = extra[k];
    try { window.dispatchEvent(new CustomEvent('capitao-voz', { detail: det })); } catch (e) {}
  }
  var ESCUTA = { rec: null };
  // Ditado: escuta até a pessoa parar de falar por `pausa` ms (ou tocar de novo). Junta todos os trechos — o reconhecedor
  // fecha um "resultado final" a cada respiro e, no Android, encerra a cada frase: aqui ele religa sozinho sem perder o texto.
  // o = { pausa, espera (ms sem ouvir nada até desistir), max, parcial(texto), fim(texto), erro(codigo) }. Retorna { parar, cancelar } ou null.
  function ditado(o) {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition; if (!SR) return null;
    o = o || {};
    var pausa = o.pausa || 2500, feito = false, texto = '', sessao = '', r = null, t = 0, tMax = 0, ouviu = false, rapidas = 0, ini = 0;
    function atual() { return (texto + ' ' + sessao).replace(/\s+/g, ' ').trim(); }
    // O Chrome do Android devolve resultados acumulados ("você", "você tem", "você tem banco"…): somar tudo repetia palavras.
    // Cada sessão é remontada do zero a partir de todos os resultados, e um trecho que continua o anterior o substitui.
    function junta(lista, seg) {
      var n = norm(seg).replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim(); if (!n) return;
      var ult = lista.length ? norm(lista[lista.length - 1]).replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim() : null;
      if (ult !== null && n.indexOf(ult) === 0) lista[lista.length - 1] = seg.trim();
      else if (ult !== null && ult.indexOf(n) === 0) return;
      else lista.push(seg.trim());
    }
    function arma() { clearTimeout(t); t = setTimeout(function () { fim(); }, ouviu ? pausa : (o.espera || 8000)); }
    function solta() { clearTimeout(t); clearTimeout(tMax); var x = r; r = null; if (x) { try { x.onresult = x.onend = x.onerror = null; x.abort(); } catch (e) {} } }
    function fim() { if (feito) return; feito = true; var txt = atual(); solta(); solto(); evVoz(txt ? 'pensando' : 'livre', txt); if (o.fim) o.fim(txt); }
    function falha(e) { if (feito) return; feito = true; solta(); solto(); evVoz('livre'); if (o.erro) o.erro(e); }
    function solto() { if (ESCUTA.rec === h) ESCUTA.rec = null; }
    function liga() {
      var x = r = new SR(); x.lang = 'pt-BR'; x.continuous = true; x.interimResults = true; x.maxAlternatives = 1; ini = Date.now();
      x.onresult = function (ev) {
        if (x !== r) return;
        var partes = [];
        for (var i = 0; i < ev.results.length; i++) junta(partes, String(ev.results[i][0].transcript || ''));
        sessao = partes.join(' ');
        if (atual()) { ouviu = true; rapidas = 0; }
        if (o.parcial) o.parcial(atual()); evVoz('ouvindo', atual()); arma();
      };
      x.onerror = function (ev) { var e = ev && ev.error; if (x === r && (e === 'not-allowed' || e === 'service-not-allowed' || e === 'audio-capture')) falha(e); };
      x.onend = function () { // fim de sessão do navegador (não da pessoa): guarda o que ouviu e religa
        if (x !== r || feito) return;
        texto = atual(); sessao = '';
        rapidas = Date.now() - ini < 400 ? rapidas + 1 : 0;
        if (rapidas >= 4) { if (ouviu) fim(); else falha('no-speech'); return; }
        try { liga(); } catch (e) { fim(); }
      };
      x.start();
    }
    var h = { parar: fim, cancelar: function () { if (feito) return; feito = true; solta(); solto(); evVoz('livre'); } };
    try { liga(); } catch (e) { return null; }
    arma(); tMax = setTimeout(fim, o.max || 90000);
    ESCUTA.rec = h; evVoz('ouvindo', '');
    return h;
  }
  // Convite: o site não tem servidor — o convite sai pelo WhatsApp (celular) ou e-mail do próprio aparelho, com o link de acesso.
  // contato = celular com DDD (8–15 dígitos; sem +55 assume Brasil) ou e-mail. Retorna { href, canal, contato } ou null se inválido.
  function linkConvite(nome, contato, acesso) {
    var c = String(contato || '').trim(), url = location.href.replace(/[^\/]*$/, '') + 'login.html';
    var msg = 'Olá, ' + nome + '! Você foi convidado(a) para o Capitão IA — embarcação ' + (E.nome || 'Capitão IA') + (D.demo && !sim() ? ' (demonstração)' : '') + ', acesso ' + (acesso || 'total') + '.\nEntre por: ' + url + '\nO usuário e a senha são passados pelo proprietário.';
    if (/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(c)) return { canal: 'e-mail', contato: c, href: 'mailto:' + encodeURIComponent(c) + '?subject=' + encodeURIComponent('Convite · Capitão IA') + '&body=' + encodeURIComponent(msg) };
    if (!/^\+?[\d ().-]+$/.test(c)) return null;
    var d = c.replace(/\D/g, ''); if (d.length < 10 || d.length > 15) return null;
    if (c.charAt(0) !== '+' && d.length <= 11) d = '55' + d.replace(/^0+/, '');
    return { canal: 'WhatsApp', contato: c, href: 'https://wa.me/' + d + '?text=' + encodeURIComponent(msg) };
  }
  // Legendas do núcleo de voz: o texto original (com siglas e números como na tela), linha a linha.
  function legendas(text) {
    var out = [];
    String(text || '').split(/\n+/).forEach(function (l) { l = l.trim(); if (l) out = out.concat(blocos(l)); });
    return out;
  }
  // onEnd dispara uma única vez, depois do último bloco (ou por erro/vigia). Nova fala ou stopSpeaking() trocam a geração: o onEnd antigo nunca dispara.
  function speak(text, onEnd) {
    var gen = ++FALA.gen, done = false, ss = window.speechSynthesis, i = 0, atual = null, tentou = {}, voz = null, partes = [], leg = legendas(text);
    var fin = function () { if (done || gen !== FALA.gen) return; done = true; calaTimers(); FALA.fila = []; FALA.pula = null; evVoz('livre'); if (onEnd) onEnd(); };
    var vale = function (u) { return !done && gen === FALA.gen && u === atual; };
    var legenda = function (k, n) { return leg.length ? leg[Math.min(leg.length - 1, Math.floor(k * leg.length / Math.max(1, n)))] : ''; };
    calaTimers(); FALA.fila = [];
    // Tocar no núcleo enquanto fala: encerra esta fala como se tivesse terminado (a conversa volta a ouvir).
    FALA.pula = function () { if (done || gen !== FALA.gen) return; try { if (ss) ss.cancel(); } catch (e) {} fin(); };
    function vigia(u, ms) { clearTimeout(FALA.timer); FALA.timer = setTimeout(function () { if (vale(u)) avanca(); }, ms); }
    function avanca() { if (++i >= partes.length) return fin(); try { fala(i); } catch (e) { fin(); } }
    function fala(k) {
      var u = new SpeechSynthesisUtterance(partes[k]), est = estimaMs(partes[k]);
      u.lang = voz && voz.lang ? String(voz.lang).replace(/_/g, '-') : 'pt-BR'; if (voz) u.voice = voz; u.rate = RATE;
      u.onstart = function () { if (vale(u)) { vigia(u, est); evVoz('falando', legenda(k, partes.length), { som: true }); } };
      u.onboundary = function (e) { if (vale(u) && (!e || e.name !== 'sentence')) evVoz('pulso'); };
      u.onend = function () { if (vale(u)) { evVoz('falando', legenda(k, partes.length), { som: false }); avanca(); } };
      u.onerror = function (e) {
        if (!vale(u)) return;
        var err = e && e.error;
        if (err === 'interrupted' || err === 'canceled') return fin(); // cancelada por fora
        if (voz && voz.localService === false && !tentou[k]) { // voz de rede falhou (sem internet): troca de voz e repete o bloco
          tentou[k] = 1; VOZ.ruim[voz.name] = 1; VOZ.v = null; voz = vozPtBr();
          try { return fala(k); } catch (x) { return fin(); }
        }
        avanca();
      };
      atual = u; FALA.fila.push(u); vigia(u, est + 4000);
      evVoz('falando', legenda(k, partes.length), { som: false }); // som só no onstart (a voz pode demorar a começar)
      ss.speak(u);
    }
    function doAparelho() {
      if (done || gen !== FALA.gen) return false;
      if (!ss || !window.SpeechSynthesisUtterance) { setTimeout(fin, 0); return false; }
      try {
        partes = blocos(falavel(text)); voz = vozPtBr(); i = 0;
        ss.cancel(); if (ss.paused) ss.resume();
        if (!partes.length) { setTimeout(fin, 0); return false; }
        fala(0);
        // keep-alive do Chrome desktop só p/ voz Google de rede (a que corta em ~15 s)
        if (!done && voz && /google/i.test(voz.name) && voz.localService === false && !/android/i.test((window.navigator && window.navigator.userAgent) || ''))
          FALA.vivo = setInterval(function () { try { if (gen === FALA.gen && ss.speaking && !ss.paused) { ss.pause(); ss.resume(); } } catch (e) {} }, 10000);
        return true;
      } catch (e) { calaTimers(); setTimeout(fin, 0); return false; }
    }
    return doAparelho();
  }
  function stopSpeaking() { FALA.gen++; calaTimers(); FALA.fila = []; FALA.pula = null; try { window.speechSynthesis && window.speechSynthesis.cancel(); } catch (e) {} evVoz('livre'); }
  // Abertura da conversa (persona): curta, sem cerimônia.
  function abertura() { return 'Capitão IA online. Que precisa?'; }
  // Fala direta: na voz vai só o essencial (a 1ª linha da resposta, sem fontes); o texto completo fica na tela.
  // Emergência (SOS, pressão de óleo, EPIRB, incêndio) é lida inteira — segurança vem antes da concisão.
  var FALA_INTEIRA = { sos: 1, oleo: 1, epirb: 1, seafire: 1 };
  function falaCurta(a) {
    if (a && typeof a === 'object' && a.fala) return a.fala; // resposta que já traz a fala certa (saudação vinda de pergunta)
    var t = a && typeof a === 'object' ? a.text : a;
    if (a && a.key && FALA_INTEIRA[a.key]) return String(t || '');
    // Trecho de segurança da base (Seafire, EPIRB, salvatagem, protocolo…): o trecho inteiro, com o rótulo e a nota da etiqueta
    // (sem a linha "Veja também"). Antes, a fala parava na 2ª frase e perdia o "não abra o acesso ao motor" e o rótulo.
    if (a && a.key === 'base' && a.seguranca && typeof t === 'string') return t.split(/\n+/)[0].trim();
    if (a && a.key === 'base' && a.ingles) return 'Está no ' + String(a.ref || 'manual').replace(/, p\. /, ', página ').replace(/ · .*$/, '') + ', em inglês. Mostrei o trecho na tela.';
    // Tira parênteses da fala, inclusive aninhados: "(… snapshot (DEMO) …)" sai inteiro, sem sobra.
    var semPar = function (s) { var a; do { a = s; s = s.replace(/\s*\([^()]*\)/g, ''); } while (s !== a); return s.replace(/\s*[()]/g, ''); };
    var item = function (l) { return semPar(l.replace(/^(\d+[.)]|•|-)\s*/, '')).trim(); };
    var ls = String(t || '').split(/\n+/).map(function (l) { return l.trim(); }).filter(function (l) { return l && !/^fonte\b/i.test(l); });
    var r = semPar(ls[0] || ''), extra = [], lim = 220;
    // Resposta da IA: conversa — a 1ª frase curta ganha a seguinte ("Sou o Capitão IA. Respondo sobre…"), até ~320 letras.
    if (a && a.key === 'ia') { lim = 320; if (ls.length > 1 && r.length < 90 && !/:$/.test(r) && !/^(\d+[.)]|•|-)/.test(ls[1])) r = (/[.!?]$/.test(r) ? r : r + '.') + ' ' + semPar(ls[1]); }
    var ressalvas = /ressalva/i.test(r), resto = 0;
    if (ressalvas) extra = ls.filter(function (l) { return /ressalva\s*\d/i.test(l); }).map(function (l) { return item(l).replace(/^ressalva\s*\d+:\s*/i, '').split(' — ')[0]; });
    else if (/:$/.test(r)) { r = r.replace(/:$/, ''); extra = ls.slice(1, 3).filter(function (l) { return /^(\d+[.)]|•|-)/.test(l); }).map(item); }
    extra = extra.map(function (x) { return x.replace(/[\s.;:,]+$/, ''); }).filter(Boolean);
    if (extra.length) {
      var cab = r.replace(/[.]$/, ''), junta = function () { return cab + ': ' + extra.join('; ') + (resto ? '; e mais ' + resto + (resto === 1 ? ' ressalva' : ' ressalvas') + ' na tela' : '') + '.'; };
      // as ressalvas que passam do limite ficam na tela, e a fala diz quantas ("com 5 ressalvas" nunca lê 3 sem avisar)
      while (ressalvas && extra.length > 1 && junta().length > lim) { extra.pop(); resto++; }
      r = junta();
    }
    if (r.length > lim) { var m = r.slice(0, lim).match(/^[\s\S]*[.!?;]/); r = m ? m[0].replace(/;$/, '.') : r.slice(0, r.lastIndexOf(' ', lim)) + '.'; }
    return r;
  }
  // A tela avisa o núcleo de voz que espera a IA na nuvem: ele fica em PROCESSANDO até a resposta ser falada (sem sumir em 2,5 s).
  function vozPensando(texto) { try { window.dispatchEvent(new CustomEvent('capitao-voz', { detail: { estado: 'pensando', texto: texto || '', segura: true } })); } catch (e) {} }

  // Controles do overlay de voz (capitao-voz.js)
  function vozEnviar() { if (ESCUTA.rec) ESCUTA.rec.parar(); }
  function pularFala() { if (FALA.pula) FALA.pula(); }
  function vozEncerrar() {
    try { window.dispatchEvent(new CustomEvent('capitao-voz-encerrar')); } catch (e) {} // a tela desliga a conversa e limpa o estado
    var r = ESCUTA.rec; ESCUTA.rec = null; if (r) try { r.cancelar(); } catch (e) {}
    stopSpeaking();
  }

  window.CapitaoBrain = { VERSAO: VERSAO, DADOS: D, BASE: BASE, buscaBase: buscaBase, carregaBase: carregaBase, DEFAULTS: DEFAULTS, BANK: BANK, ALL: ALL, HREF: HREF, loadShortcuts: loadShortcuts, saveShortcuts: saveShortcuts, resetShortcuts: resetShortcuts, bankFor: bankFor, loadDiario: loadDiario, addDiario: addDiario, diarioFonte: diarioFonte, loadExec: loadExec, markExec: markExec, unmarkExec: unmarkExec, loadEquipe: loadEquipe, saveEquipe: saveEquipe, loadDocs: loadDocs, addDoc: addDoc, loadAbast: loadAbast, addAbast: addAbast, answer: answer, answerAttachment: answerAttachment, pedeIA: pedeIA, ficha: ficha, instante: instante, resumoAgora: resumoAgora, CHAVES: CHAVES, SOBRE_DADOS: SOBRE_DADOS, vozPensando: vozPensando, quem: quem, route: route, parseHash: parseHash, clearHash: clearHash, recognizer: recognizer, ditado: ditado, linkConvite: linkConvite, speak: speak, stopSpeaking: stopSpeaking, abertura: abertura, falaCurta: falaCurta, vozEnviar: vozEnviar, pularFala: pularFala, vozEncerrar: vozEncerrar, falavel: falavel, voz: vozPtBr, now: now, askHref: askHref, nb: nb, mil: mil, horas: horas, grau3: grau3, SNAP: SNAP, SOS_PASSOS: SOS_PASSOS, OLEO_PASSOS: OLEO_PASSOS, MMSI: MMSI_RADIO, MMSI_RADIO: MMSI_RADIO, ROTULO: ROTULO,
    LISTAS: { SOS: SOS.slice(), SOS_REGEX: SOS_REGEX_FONTES.slice(), SALVATAGEM: SALVATAGEM.slice(), BOIA_FORA: BOIA_FORA.slice(), EPIRB: EPIRB_PALAVRAS.slice(), EPIRB_REGEX: EPIRB_REGEX_FONTE }, emergencia: emergencia };
  try { window.dispatchEvent(new CustomEvent('capitao-brain-ready')); } catch (e) {}
})();
