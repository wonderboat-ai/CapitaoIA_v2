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

  var K = { atalhos: 'capitao.atalhos.v1', diario: 'capitao.diario.v1', equipe: 'capitao.equipe.v1', exec: 'capitao.executado.v1', docs: 'capitao.docs.v1', abast: 'capitao.abast.v1', tickets: 'capitao.tickets.v1', tarefas: 'capitao.tarefas.v1', alarmes: 'capitao.alarmes.v1' };
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
  // O diário para LER (respostas, ficha): `ctx.semSim` tira as linhas do aparelho com `sim: true` (gravadas com a simulação ligada; com simulacao false saem da ficha, CLAUDE.md 14). Nunca para gravar:
  // o addDiario relê o diário inteiro (loadDiario), e o registro só cresce.
  function lerDiario(ctx) { var v = vigente(loadDiario()); return ctx && ctx.semSim ? v.filter(function (e) { return e.sim !== true; }) : v; }
  // A visão VIGENTE do diário (CONTRATO §1.25): as linhas de ação (`acao`: corrige, anula, resolve, reabre) não são registros, são o que se fez com um registro; a linha anulada sai da leitura e a corrigida
  // mostra o texto da última correção. Nada se apaga do que está guardado (o loadDiario devolve tudo); só as respostas e a ficha leem por aqui.
  function vigente(v) {
    var anula = {}, corr = {};
    v.forEach(function (x) { if (x.acao === 'anula' && typeof x.alvo === 'string') anula[x.alvo] = 1; else if (x.acao === 'corrige' && typeof x.alvo === 'string' && !corr[x.alvo]) corr[x.alvo] = x; });   // (mais nova primeiro: a 1ª correção de um alvo é a última)
    return v.filter(function (x) { return !x.acao && !anula[x.iso]; }).map(function (x) { return corr[x.iso] ? Object.assign({}, x, { t: corr[x.iso].t, corrigido: true }) : x; });
  }
  // `acao` (CONTRATO §1.25): corrige e anula têm por `alvo` o `iso` de uma linha do aparelho; resolve e reabre, a pendência (o id da gerada, d03/d05/d07, ou o `iso` de uma linha do aparelho com `pend`).
  // Linha de ação sem alvo que exista, ou com ação fora das quatro, NÃO é gravada (devolve null). O `iso` da linha nova é único (duas linhas no mesmo milissegundo não dividem o alvo).
  var ACOES = { corrige: 1, anula: 1, resolve: 1, reabre: 1 };
  // a chave é da tabela, não do protótipo: 'constructor', 'toString', 'hasOwnProperty' e '__proto__' não são ação, tipo de proposta, origem nem sistema (as tabelas abaixo são lidas por texto que vem de fora)
  function tem(tabela, k) { return typeof k === 'string' && Object.prototype.hasOwnProperty.call(tabela, k); }
  function alvoValido(e, list) {
    var linha, a = e.acao, alvo = e.alvo;
    if (!tem(ACOES, a) || typeof alvo !== 'string' || !alvo) return false;
    linha = list.filter(function (x) { return x.iso === alvo; })[0];
    if (a === 'corrige' || a === 'anula') return !!linha && !linha.acao && (a === 'anula' || !!String(e.t || '').trim());
    if (linha) return linha.pend === true && !linha.acao;
    return (D.diario || []).some(function (x) { return x && x.id === alvo && x.pend === true; });
  }
  // Carimbo `sim` (PROMPT §2.9, CLAUDE.md 14): a linha nova gravada com D.simulacao === true leva sim: true (lido AGORA, nunca na carga). O SOS não lê a flag (EM_SOS) e a linha do SOS (`src` web · SOS / app · SOS)
  // nunca leva `sim`, de qualquer tela; com simulacao false as linhas com `sim` ganham o selo «apresentação» (tela) e saem da ficha (lerDiario com semSim).
  function linhaDoSOS(e) { return /^(?:web|app) · SOS/.test(String(e && e.src || '')); }
  // `opts` (F20, F15): { pendencia: true } fecha a pendência que o texto cita com o verbo de conclusão (outra linha, acao 'resolve'); { agenda: true } abre a proposta que o texto faz (a tarefa feita ou o agendamento);
  // `chat: true` = o desfazer vale 10 min (na tela, 10 s). O retorno é a linha gravada e, com essas opções e um efeito, uma CÓPIA dela com `pendencia`, `ticket` ou `ambigua` (a linha guardada não os leva).
  function addDiario(e, opts) { return congela(function () { return addDiario1(e, opts); }); }
  function addDiario1(e, opts) { var n = now(); var list = loadDiario(); var entry, ms, ef;
    if (e && e.acao !== undefined && !alvoValido(e, list)) return null;
    entry = Object.assign({ d: n.d, t: n.t, iso: n.iso, sys: 'Diário', tone: 'var(--cap-accent, #00a1fe)', who: quem(), src: 'app · texto' }, e);
    ms = Date.parse(entry.iso);
    while (isFinite(ms) && list.some(function (x) { return x.iso === entry.iso; })) { ms++; entry.iso = new Date(ms).toISOString(); }
    if (sim() && !linhaDoSOS(entry) && entry.sim == null) entry.sim = true;
    list.unshift(entry); write(K.diario, list);
    if (opts && (opts.pendencia || opts.agenda) && !EM_SOS) { ef = efeitosDoRegistro(entry, opts); if (ef) return Object.assign({}, entry, ef); }
    return entry;
  }
  function diarioFonte() { return (D.diario || []).map(function (x) { return { d: x.d, h: x.h, t: x.t, iso: x.iso, sys: x.sys, tom: x.tom, who: x.who, pend: !!x.pend, src: (D.diarioFonte || 'diário') }; }); }
  function loadExec() { var v = read(K.exec, {}); return v && typeof v === 'object' && !Array.isArray(v) ? v : {}; }
  // A execução COMO AS RESPOSTAS A LEEM. Dentro da ficha com simulacao false, a execução com `sim: true` (gravada com a simulação ligada, CONTRATO §1.25) fica fora, como a linha do diário (CLAUDE.md 14): a tarefa
  // volta a atrasada para a IA. `EXEC_SEM_SIM` só liga dentro da ficha (síncrona; a ficha1 liga, a ficha desliga no fim); as respostas da tela e o resto do app leem o mapa inteiro. O mapa guardado nunca muda
  // (o registro só cresce; o markExec e o unmarkExec leem o `loadExec`, nunca esta visão).
  var EXEC_SEM_SIM = false;
  function execVisivel() { var m = loadExec(); if (!EXEC_SEM_SIM) return m; var r = {}; Object.keys(m).forEach(function (k) { if (!m[k] || m[k].sim !== true) r[k] = m[k]; }); return r; }
  function markExec(task) { var m = loadExec(); m[task] = Object.assign(now(), selaSim()); write(K.exec, m); return m; }   // (CONTRATO §1.25: a execução gravada com a simulação ligada leva sim: true)
  // Desfaz um Executado: relê a lista, tira só essa tarefa e grava (sem a tarefa ou com dado ruim, não grava nada)
  function unmarkExec(task) { var m = loadExec(); if (task != null && Object.prototype.hasOwnProperty.call(m, String(task))) { delete m[String(task)]; write(K.exec, m); } return m; }
  function loadEquipe() { var v = read(K.equipe, null); var o = v && typeof v === 'object' ? v : {}; return { fones: o.fones && typeof o.fones === 'object' && !Array.isArray(o.fones) ? o.fones : {}, convites: Array.isArray(o.convites) ? o.convites.filter(function (c) { return c && typeof c.nome === 'string'; }) : [] }; }
  function saveEquipe(v) { write(K.equipe, v); }
  function loadDocs() { var v = read(K.docs, []); return Array.isArray(v) ? v.filter(function (d) { return d && typeof d.n === 'string'; }) : []; }
  function addDoc(d) { var list = loadDocs(); list.unshift(carimba(d)); write(K.docs, list); return list; }
  function loadAbast() { var v = read(K.abast, []); return Array.isArray(v) ? v.filter(function (a) { return a && typeof a.n === 'string'; }) : []; }
  function addAbast(a) { var list = loadAbast(); list.unshift(carimba(a)); write(K.abast, list); return list; }
  // o registro novo (documento, abastecimento) gravado com a simulação ligada leva sim: true (o que a tela já mandou fica como está); fora da simulação e no SOS, nada muda
  function carimba(x) { return sim() && x && typeof x === 'object' && x.sim == null ? Object.assign({}, x, { sim: true }) : x; }

  // ——— Propostas A CONFIRMAR (F14; CONTRATO §1.25; PROMPT §2.9) ———
  // capitao.tickets.v1 = [{ id: 't…', k, origem, texto, prop, alvo: { tipo, id }, estado: 'aberto' | 'aceito' | 'recusado', dec: { quem, iso, ate? }, res: { tipo, id }, iso, who, sim? }]. Um ticket é a PROPOSTA de um
  // registro (do relato no chat, de uma regra do diário, de um alarme do replay): NADA vira dado sem um toque. Confirmar = 1 linha nova no diário (`res` guarda o `iso` dela); recusar = 0 linhas; ✎ (editar)
  // muda o texto antes de confirmar; desfazer (10 s na tela, 10 min no chat) escreve uma linha de ANULAÇÃO (o registro só cresce: a linha confirmada fica guardada e sai da leitura) e a proposta volta a «aberto».
  // A tela chama estas funções; o chat chama o aceitaTicket e o recusaTicket pelas rotas do relato. Nenhum ticket é gerado, e o replay nunca cria um (o alarme só vira proposta num gesto: propoeAlarme).
  // A gravação parte do que está guardado: linha de outra forma (de uma versão futura) fica como está.
  var TICKET_DESFAZ = 10e3, TICKET_DESFAZ_CHAT = 10 * 60e3;
  var ORIGEM_TICKET = { relato: 'Relato', telemetria: 'Telemetria', regra: 'Regra', ia: 'IA' };
  var SYS_TONE = { 'Segurança': 'var(--cap-crit, #ff3b30)', 'Anomalia': 'var(--cap-crit, #ff3b30)', 'Manutenção': 'var(--cap-warn, #f0a63a)', 'Combustível': 'var(--cap-warn, #f0a63a)', 'Navegação': 'var(--cap-tele, #00f4fd)' };
  function tomDe(sys) { return tem(SYS_TONE, sys) ? SYS_TONE[sys] : 'var(--cap-accent, #00a1fe)'; }
  function limpaT(s, n) { return String(s == null ? '' : s).replace(/\s+/g, ' ').trim().slice(0, n); }
  function ticketsCru() {
    var s = null, v = null;
    try { s = localStorage.getItem(K.tickets); v = s ? JSON.parse(s) : []; } catch (e) { v = null; }
    if (Array.isArray(v)) return v;
    try { if (s && localStorage.getItem(K.tickets + '.antes') === null) localStorage.setItem(K.tickets + '.antes', s); } catch (e) {}   // valor que não é uma lista (nem JSON): guardado ao lado, não pisado
    return [];
  }
  function ehTicket(t) { return !!t && typeof t === 'object' && typeof t.id === 'string' && /^t[A-Za-z0-9_-]{2,60}$/.test(t.id) && tem(TICKET_K, t.k) && typeof t.texto === 'string'; }
  function loadTickets() { return ticketsCru().filter(ehTicket); }
  function achaTicket(cru, id) { return cru.filter(function (t) { return ehTicket(t) && t.id === id; })[0] || null; }
  function novoIdTicket(cru) { var id; do { id = 't' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); } while (cru.some(function (t) { return t && t.id === id; })); return id; }
  // k → como a confirmação grava. O `diario` é a linha do diário com o texto do ticket (sys e tom da proposta); o `alarme` é a mesma linha, do alarme do replay. As propostas da agenda (F15) entram aqui.
  var TICKET_K = {
    diario: function (t, ext, opts) { var p = t.prop || {}, e = { sys: p.sys || 'Diário', tone: p.tone || tomDe(p.sys), t: t.texto, who: quem(), src: 'app · proposta confirmada (' + (tem(ORIGEM_TICKET, t.origem) ? ORIGEM_TICKET[t.origem] : 'Relato').toLowerCase() + ')' }; if (p.pend === true) e.pend = true; var lin = addDiario(e, t.origem === 'relato' ? { pendencia: true, agenda: true, chat: !!(opts && opts.chat) } : undefined); if (lin && lin.pendencia && ext) ext.pend = { alvo: lin.pendencia.alvo, iso: lin.pendencia.linha.iso }; return lin; },   // (F20/F15: o relato confirmado é um registro: fecha a pendência que cita e propõe a agenda; a linha devolvida leva `.pendencia`/`.ticket`)   // (o relato que conta um defeito abre pendência: `pend`, CONTRATO §1.9, F20)
    alarme: function (t) { var p = t.prop || {}; return addDiario({ sys: p.sys || 'Diário', tone: p.tone || tomDe(p.sys), t: t.texto, who: quem(), src: 'app · proposta confirmada (alarme)' }); },
    // F15 (diário → agenda; CONTRATO §1.7, §1.25). `exec`: a tarefa da agenda que o registro diz ter feito vira Executado (markExec, como o toque do C1) e ganha 1 linha «Executado: …» no diário; `tarefa`: o
    // agendamento vira a tarefa da equipe (capitao.tarefas.v1, vence em AAAA-MM-DD) e ganha 1 linha. O `ext` recebe o que o desfazer precisa para desmanchar (a execução e a tarefa que ESTA confirmação criou).
    exec: function (t, ext) {
      var p = t.prop || {}, ag = tarefa(p.tarefa), m, lin;
      if (!ag || loadExec()[ag.id]) return null;   // a tarefa não existe mais, ou já foi executada noutro canto: não há o que marcar
      m = markExec(ag.id);
      lin = addDiario({ sys: 'Manutenção', tone: tomDe('Manutenção'), t: t.texto, who: quem(), src: 'app · proposta confirmada (' + origemTxt(t) + ')', ref: ag.id });
      if (!lin) { unmarkExec(ag.id); return null; }
      ext.exec = { id: ag.id, iso: m[ag.id].iso };
      return lin;
    },
    tarefa: function (t, ext) {
      var p = t.prop || {}, r = criaTarefa({ n: p.n, vence: p.vence, quem: p.quem, sistema: p.sistema, origem: 'diario' }), lin;
      if (!r) return null;
      lin = addDiario({ sys: 'Manutenção', tone: tomDe('Manutenção'), t: t.texto, who: quem(), src: 'app · proposta confirmada (' + origemTxt(t) + ')', ref: r.item.id });
      if (!lin) { if (r.novo) removeTarefa(r.item.id); return null; }
      if (r.novo) ext.tarefa = r.item.id;
      return lin;
    }
  };
  function origemTxt(t) { return (tem(ORIGEM_TICKET, t && t.origem) ? ORIGEM_TICKET[t.origem] : 'Relato').toLowerCase(); }
  function addTicket(t) {
    var cru, texto, id, ja, item;
    if (EM_SOS) return null;   // o SOS não propõe nada
    t = t || {}; texto = limpaT(t.texto, 600);
    if (!tem(TICKET_K, t.k) || !texto) return null;
    cru = ticketsCru(); id = typeof t.id === 'string' && /^t[A-Za-z0-9_-]{2,60}$/.test(t.id) ? t.id : novoIdTicket(cru);
    ja = achaTicket(cru, id); if (ja) return ja;   // o id repetido não duplica
    item = { id: id, k: t.k, origem: tem(ORIGEM_TICKET, t.origem) ? t.origem : 'relato', texto: texto, prop: t.prop && typeof t.prop === 'object' ? t.prop : {}, estado: 'aberto', iso: new Date().toISOString(), who: quem() };
    if (t.alvo && typeof t.alvo.tipo === 'string' && typeof t.alvo.id === 'string' && t.alvo.id) item.alvo = { tipo: t.alvo.tipo, id: t.alvo.id };
    if (sim()) item.sim = true;
    cru.unshift(item); write(K.tickets, cru);
    return item;
  }
  // ✎ antes de confirmar: o texto (e/ou a proposta). Só a proposta aberta muda; a confirmada, a recusada e a que não existe devolvem null.
  function editaTicket(id, campos) {
    var cru = ticketsCru(), t = achaTicket(cru, id), tx;
    if (!t || t.estado !== 'aberto') return null;
    campos = campos || {};
    if (campos.texto != null) { tx = limpaT(campos.texto, 600); if (!tx) return null; t.texto = tx; }
    if (campos.prop && typeof campos.prop === 'object') t.prop = campos.prop;
    write(K.tickets, cru); return t;
  }
  // CONFIRMAR (um toque): grava a linha (1) e a decisão (quem, quando, o que criou). {id, k, ja: true} se já estava confirmada (não grava outra); null se não existe, se foi recusada (a recusa não ressuscita) ou se
  // a linha não pôde ser gravada. `opts.chat`: a confirmação veio do chat, e o desfazer vale por 10 min (na tela, 10 s).
  function aceitaTicket(id, opts) {
    var cru, t, lin, ate, ext;
    if (EM_SOS) return null;
    cru = ticketsCru(); t = achaTicket(cru, id);
    if (!t || t.estado === 'recusado') return null;
    if (t.estado === 'aceito') return { id: id, k: t.k, ja: true, dec: t.dec || null, res: t.res || null };
    ext = {}; lin = TICKET_K[t.k](t, ext, opts); if (!lin) return null;
    cru = ticketsCru(); t = achaTicket(cru, id) || t;   // (a confirmação pode ter aberto outras propostas — o registro propõe a agenda —: a decisão parte do que está guardado AGORA, nunca da lista de antes, que as perderia)
    ate = Date.now() + (opts && opts.chat ? TICKET_DESFAZ_CHAT : TICKET_DESFAZ);
    t.estado = 'aceito'; t.dec = { quem: quem(), iso: new Date().toISOString(), ate: ate }; t.res = Object.assign({ tipo: 'diario', id: lin.iso }, ext);
    write(K.tickets, cru);
    return { id: id, k: t.k, texto: t.texto, origem: t.origem, res: t.res, linha: lin, desfazAte: ate };
  }
  function recusaTicket(id) {
    var cru = ticketsCru(), t = achaTicket(cru, id);
    if (!t || t.estado !== 'aberto') return null;
    t.estado = 'recusado'; t.dec = { quem: quem(), iso: new Date().toISOString() }; write(K.tickets, cru);
    return { id: id, estado: 'recusado' };
  }
  // DESFAZER a confirmação, dentro da janela (10 s; 10 min se veio do chat): a linha que ela escreveu ganha uma linha de anulação (acao 'anula', alvo = o iso dela) e a proposta volta a «aberto» (confirmar de novo
  // escreve uma linha nova). Depois da janela, com a proposta aberta ou recusada, ou sem a linha, devolve null e não escreve nada. Aceita o id ou o resultado do aceitaTicket.
  function desfazTicket(r) {
    var id = r && typeof r === 'object' ? r.id : r, cru = ticketsCru(), t = achaTicket(cru, id), lin, an;
    if (EM_SOS || !t || t.estado !== 'aceito' || !t.res || t.res.tipo !== 'diario' || !t.dec || typeof t.dec.ate !== 'number' || Date.now() > t.dec.ate) return null;
    lin = loadDiario().filter(function (x) { return x.iso === t.res.id && !x.acao; })[0]; if (!lin) return null;
    an = addDiario({ sys: lin.sys, tone: lin.tone, t: 'Registro anulado (proposta desfeita): ' + limpaT(lin.t, 200), who: quem(), src: 'app · proposta desfeita', acao: 'anula', alvo: lin.iso });
    if (!an) return null;
    desfazExtra(t);   // (F15) a execução e a tarefa que a confirmação criou, e a pendência que ela fechou; as propostas que o registro abriu são recusadas (escrevem em tickets: a decisão parte do guardado de novo)
    cru = ticketsCru(); t = achaTicket(cru, id) || t;
    t.estado = 'aberto'; delete t.dec; delete t.res; write(K.tickets, cru);
    return { id: id, estado: 'aberto', anulada: an };
  }
  // O que a confirmação de uma proposta da agenda criou, desmanchado pelo desfazer: o Executado (só se ainda é o que ESTA confirmação marcou — uma execução nova feita noutro canto fica) e a tarefa da equipe
  function desfazExtra(t) {
    var r = t.res || {}, e;
    if (r.pend && typeof r.pend.alvo === 'string') desfazPendencia({ alvo: r.pend.alvo, linha: { iso: r.pend.iso }, desfazAte: Infinity });   // (o relato confirmado fechou uma pendência: desfeito o registro, ela reabre)
    if (r.id) ticketsAbertos().filter(function (x) { return x.origem === 'regra' && x.alvo && x.alvo.tipo === 'diario' && x.alvo.id === r.id; }).forEach(function (x) { recusaTicket(x.id); });   // (as propostas da agenda que o registro abriu perdem o registro de origem)
    if (t.k === 'exec' && r.exec && typeof r.exec.id === 'string') { e = loadExec()[r.exec.id]; if (e && e.iso === r.exec.iso) unmarkExec(r.exec.id); }
    else if (t.k === 'tarefa' && typeof r.tarefa === 'string') removeTarefa(r.tarefa);
  }
  // A proposta que a foto confirmou (F36: «sim, registra» junto com a foto): a linha da foto já leva o texto do relato, então a proposta fecha apontando essa linha, sem escrever outra
  function fechaTicketCom(id, lin) {
    var cru = ticketsCru(), t = achaTicket(cru, id);
    if (EM_SOS || !t || t.estado !== 'aberto' || !lin) return null;
    t.estado = 'aceito'; t.dec = { quem: quem(), iso: new Date().toISOString(), ate: Date.now() + TICKET_DESFAZ }; t.res = { tipo: 'diario', id: lin.iso }; write(K.tickets, cru);
    return t;
  }
  function ticketsAbertos() { return loadTickets().filter(function (t) { return t.estado === 'aberto'; }).sort(function (a, b) { return String(b.iso || '') < String(a.iso || '') ? -1 : String(b.iso || '') > String(a.iso || '') ? 1 : 0; }); }
  // o que a lista A CONFIRMAR mostra: o texto que o CONFIRMAR grava, a origem e o selo «apresentação» (sim, só com simulacao false)
  function ticketTela(t) { var tx = String((t && t.texto) || ''); return { texto: tx, origem: tem(ORIGEM_TICKET, t && t.origem) ? ORIGEM_TICKET[t.origem] : 'Relato', longo: tx.length > 220, apresentacao: !!(t && t.sim === true && !EM_SOS && D.simulacao === false) }; }
  // O alarme do replay vira PROPOSTA só depois de um gesto (o toque em «Registrar» da C3, que passa gesto === true): o replay, o evento 'capitao-alerta' e a faixa nunca criam proposta. Uma por alarme por dia de bordo
  // (o id do ticket traz o id do alarme e o dia): o gesto repetido devolve a mesma, aberta, aceita ou recusada. null = sem gesto, fora da simulação, no SOS ou sem alarme ativo com esse id agora.
  function propoeAlarme(id, gesto) {
    var AL = window.CapitaoAlertas, al = null, i, dia;
    if (gesto !== true || EM_SOS || !sim() || typeof id !== 'string' || !/^[a-z0-9_]{1,40}$/.test(id)) return null;
    i = instante(); if (!i) return null;
    try { al = AL && typeof AL.porId === 'function' ? AL.porId(id, i.ms) : null; } catch (e) { al = null; }
    if (!al) return null;
    try { dia = new Intl.DateTimeFormat('en-CA', { timeZone: E.fuso || 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(i.ms)).replace(/-/g, ''); } catch (e) { return null; }
    return addTicket({ id: 'tal_' + id + '_' + dia, k: 'alarme', origem: 'telemetria', texto: al.rotulo + ': ' + al.texto + ' desde ' + al.hora + '.', prop: { sys: al.sistema === 'motores' ? 'Motores' : 'Equipamentos', alarme: id, dia: dia, tone: al.nivel === 'critico' ? 'var(--cap-crit, #ff3b30)' : 'var(--cap-warn, #f0a63a)' }, alvo: { tipo: 'alarme', id: id } });
  }

  // ——— P3G · o que fica guardado no aparelho (F15 tarefas da equipe, F12 alarmes pedidos) ———
  // capitao.tarefas.v1 e capitao.alarmes.v1: a gravação parte do que está guardado (a linha de outra forma, de uma versão futura, fica como está) e o valor que não é lista é copiado para a chave `.antes`,
  // não pisado (a mesma regra do capitao.tickets.v1). O registro só cresce: nenhuma chave é apagada nem renomeada.
  function listaCru(chave) {
    var s = null, v = null;
    try { s = localStorage.getItem(chave); v = s ? JSON.parse(s) : []; } catch (e) { v = null; }
    if (Array.isArray(v)) return v;
    try { if (s && localStorage.getItem(chave + '.antes') === null) localStorage.setItem(chave + '.antes', s); } catch (e) {}   // valor que não é lista (nem JSON): guardado ao lado, não pisado
    return [];
  }
  // ——— Datas (F15): o dia do barco é o do instante (fuso do barco); 'AAAA-MM-DD' é a forma guardada da tarefa ———
  var MES_NUM = { janeiro: 1, fevereiro: 2, marco: 3, abril: 4, maio: 5, junho: 6, julho: 7, agosto: 8, setembro: 9, outubro: 10, novembro: 11, dezembro: 12 };
  function diaIso(n) { return new Date(n * 86400000).toISOString().slice(0, 10); }
  function brData(iso) { var m = /^(\d{4})-(\d\d)-(\d\d)$/.exec(String(iso || '')); return m ? m[3] + '/' + m[2] + '/' + m[1] : String(iso || ''); }
  // dia desde 1970 de uma data civil que existe (30/02 não existe: NaN)
  function dataCivil(a, m, d) { var t = Date.UTC(a, m - 1, d), x = new Date(t); return m >= 1 && m <= 12 && d >= 1 && x.getUTCFullYear() === a && x.getUTCMonth() === m - 1 && x.getUTCDate() === d ? Math.floor(t / 86400000) : NaN; }
  // «15/11» (sem ano: este ano, ou o próximo se já passou — agendar é futuro), «15/11/26», «15/11/2026». Com ano e no passado a data fica no passado (quem chama decide)
  function diaDigitado(d, m, a) {
    var hoje = diaDe(msAgora()), ano = a ? (+a < 100 ? 2000 + +a : +a) : +diaIso(hoje).slice(0, 4), n = dataCivil(ano, m, d);
    if (!a && !isNaN(n) && n < hoje) n = dataCivil(ano + 1, m, d);
    return n;
  }
  // ——— Tarefas da equipe (F15; CONTRATO §1.7, §1.25) ———
  // capitao.tarefas.v1 = [{ id: 'g…', n, vence: 'AAAA-MM-DD', quem, sistema?, meses?, obs?, origem, iso, who, sim? }]. As 2 geradas (D.tarefasEquipe, g01 e g02) ficam no arquivo de dados; as do aparelho entram aqui por
  // um toque (a tela) ou pelo CONFIRMAR de uma proposta (o agendamento do diário e do chat). O prazo é contado do dia do instante (CapitaoAgora.prazoDe), nunca guardado; CapitaoAgora.contagens() soma as
  // duas listas (as executadas não contam). Executado da tarefa = markExec(id), como o da agenda.
  var TAREFA_ID = /^g[A-Za-z0-9_-]{2,60}$/, ORIGEM_TAREFA = { chat: 1, diario: 1, tela: 1 };
  function ehTarefa(t) { return !!t && typeof t === 'object' && typeof t.id === 'string' && TAREFA_ID.test(t.id) && typeof t.n === 'string' && !!t.n.trim() && typeof t.vence === 'string' && /^\d{4}-\d\d-\d\d$/.test(t.vence) && !isNaN(diaData(t.vence)); }
  function loadTarefas() { return listaCru(K.tarefas).filter(ehTarefa); }
  // grava a tarefa; { item, novo }: a mesma tarefa (nome e dia) ainda aberta não duplica — devolve a que já está (novo false). null = dado inválido (sem nome, data que não existe) ou o SOS.
  function criaTarefa(x) {
    var cru, n, ex, ja, item, id;
    if (EM_SOS || !x || typeof x !== 'object') return null;
    n = limpaT(x.n, 120);
    if (!n || typeof x.vence !== 'string' || !/^\d{4}-\d\d-\d\d$/.test(x.vence) || diaIso(diaData(x.vence)) !== x.vence) return null;
    cru = listaCru(K.tarefas); ex = loadExec();
    ja = cru.filter(function (t) { return ehTarefa(t) && norm(t.n) === norm(n) && t.vence === x.vence && !ex[t.id]; })[0];
    if (ja) return { item: ja, novo: false };
    do { id = 'g' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5); } while (cru.some(function (t) { return t && t.id === id; }) || (D.tarefasEquipe || []).some(function (t) { return t.id === id; }));
    item = { id: id, n: n, vence: x.vence, quem: limpaT(x.quem, 40), origem: tem(ORIGEM_TAREFA, x.origem) ? x.origem : 'tela', iso: new Date().toISOString(), who: quem() };
    if (x.sistema) item.sistema = limpaT(x.sistema, 30);
    if (typeof x.meses === 'number' && isFinite(x.meses) && x.meses > 0) item.meses = Math.round(x.meses);
    if (x.obs) item.obs = limpaT(x.obs, 300);
    if (sim()) item.sim = true;
    cru.unshift(item); write(K.tarefas, cru);
    return { item: item, novo: true };
  }
  function addTarefa(x) { var r = criaTarefa(x); return r ? r.item : null; }
  // só o desfazer de uma proposta confirmada tira a tarefa (dentro da janela): a tela não apaga tarefa
  function removeTarefa(id) {
    var cru = listaCru(K.tarefas), k;
    if (EM_SOS) return false;
    for (k = 0; k < cru.length; k++) if (ehTarefa(cru[k]) && cru[k].id === id) { cru.splice(k, 1); write(K.tarefas, cru); return true; }
    return false;
  }
  // as tarefas da equipe (as 2 geradas e as do aparelho) com o prazo do dia do instante e se já foram executadas; `ctx.semSim`: as do aparelho gravadas com a simulação ligada ficam fora (simulacao false)
  function tarefasEquipe(ctx) {
    var ex = execVisivel(), semSim = !!(ctx && ctx.semSim);
    var ger = (D.tarefasEquipe || []).map(function (t) { return { id: t.id, n: t.n, vence: t.vence, quem: t.quem, sistema: t.sistema, origem: 'equipe', aparelho: false }; });
    var dev = loadTarefas().filter(function (t) { return !(semSim && t.sim === true); }).map(function (t) { return { id: t.id, n: t.n, vence: t.vence, quem: t.quem || '', sistema: t.sistema, origem: t.origem, aparelho: true, iso: t.iso, who: t.who }; });
    return ger.concat(dev).map(function (t) {
      var n = dnDe(t), d = isNaN(n) ? {} : prazoSt(n);
      t.dn = n; t.st = d.st; t.rot = d.rot; t.tom = d.tom; t.feita = !!ex[t.id];
      return t;
    }).sort(function (a, b) { return ((isNaN(a.dn) ? 1e9 : a.dn) - (isNaN(b.dn) ? 1e9 : b.dn)) || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0); });
  }
  // as tarefas do aparelho ainda abertas, para as respostas da agenda e da ficha («Tarefas da equipe agendadas: …»); as 2 geradas ficam com a tela da equipe
  function tarefasAgendadas(ctx) { return tarefasEquipe(ctx).filter(function (t) { return t.aparelho && !t.feita; }); }
  // ——— O que o texto de um registro diz (F20, F15) ———
  // «Frase de conclusão»: o verbo de quem FEZ o serviço (passado ou particípio), sem plano, dúvida, pergunta, negação nem defeito que continua. É a única regra que fecha uma pendência e que propõe o Executado;
  // na dúvida NÃO conclui (a tela tem o Resolver e o Executado de um toque). «Limpei o filtro» fecha; «vou limpar o filtro», «será que limpei o filtro?», «não limpei o filtro», «limpei o filtro, mas o fluxo
  // continua fraco», «limpei o filtro e o fluxo está fraco», «o filtro está limpo» (estado, não ato) e «testei a bomba e ela faz um ruído estranho» não. As linhas do próprio app («Executado: … nada se apaga»)
  // levam «nada» e nunca concluem.
  var FEITO = /\b(?:(?:limp|test|inspecion|revis|realiz|execut|finaliz|lav|ajust|instal|consert|atualiz|arrum|calibr|troc|verific)(?:ei|amos|ou|aram|ad[oa]s?)|troquei|verifiquei|fiz|fizemos|fez|fizeram|feit[oa]s?|conclu(?:i|imos|iu|iram|id[oa]s?)|substitu(?:i|imos|iu|iram|id[oa]s?)|corrig(?:i|imos|iu|iram|id[oa]s?)|resolv(?:i|emos|eu|eram|id[oa]s?)|limp[oa]s?|pront[oa]s?|normaliz(?:ou|aram|ad[oa]s?))\b/;
  var CONC_FUTURO = /\b(?:vou|vamos|vai|irei|iremos|iria|precis(?:a|o|amos|am|ar)|necessit\w*|tem que|temos que|tenho que|tenha que|devo|devemos|deve|deveria|deveriamos|poderia|poderiamos|posso|podemos|pretend\w*|planej\w*|quero|queremos|queria|gostaria|lembrar|lembrete|amanha|semana que vem|mes que vem|proxim[oa]|em breve|logo mais|falta|faltam|faltou|pendente|aguardando|esperando|a fazer|por fazer|ate (?:segunda|terca|quarta|quinta|sexta|sabado|domingo))\b/;
  var CONC_DUVIDA = /\?|\b(?:sera que|acho que|talvez|parece que|nao sei|duvid\w+|supostamente|aparentemente|creio que|imagino que|devo ter|deve ter|pode ser que|nao tenho certeza|nao lembro|quem sabe|se)\b/;
  var CONC_NEGA = /\b(?:nao|nunca|jamais|nem|ninguem|nada)\b/;
  // O DEFEITO que continua ou que o registro acabou de achar: as palavras de continuidade (continua, segue, ainda, mesmo assim, mas…), o sintoma dito (fraco, baixo, ruim, ruído, barulho, vazamento, estranho, quente…) e «está/ficou +
  // adjetivo de defeito» (está sujo, ficou travado). O defeito de ANTES («o filtro que estava sujo», «o fluxo estava fraco») sai antes de procurar (CONC_PASSADO): é o motivo do serviço, não o resultado dele.
  var CONC_DEFEITO = /\b(?:continu\w+|segue|seguem|persist\w+|voltou a|voltaram a|ainda|sem (?:sucesso|resultado|efeito|conseguir|solucao|melhora|melhoria|diferenca|mudanca|alteracao|progresso)|em vao|apesar de|mesmo assim|mesmo depois|pior\w*|danificad\w+|quebr\w+|entupid\w+|travad\w+|travou|trincad\w+|rachad\w+|vazand\w+|vazou|falhou|falhando|defeit\w+|fraco|fraca|fracos|fracas|baixo|baixa|baixos|baixas|ruim|ruins|lento|lenta|lentos|lentas|insuficiente\w*|ruidos?|barulh\w+|vazamentos?|estranh\w+|anormal\w*|anormais|esquisit\w+|quentes?|aquec\w+|superaquec\w+|esquent\w+|fumac\w+|fumegand\w+|cheiro|vibrac\w+|trepid\w+|instave\w+|oscil\w+|desgastad\w+|queimad\w+|furad\w+|corroid\w+|enferrujad\w+|emperrad\w+|permanec\w+|reapare\w+|retornou|retornaram|pouc[oa]s?|mornos?|mornas?|sem (?:gelar|funcionar|ligar|pegar|partir|pressao|agua|fluxo|ar|luz|som)|mas|porem|contudo|entretanto|todavia|(?:esta|estao|ta|tao|fica|ficam|ficou|ficaram|anda|andam)(?: (?:muito|bem|meio|bastante|um pouco|pouco))* (?:sujo|suja|sujos|sujas|cheio|cheia|vazio|vazia|parado|parada|desligado|desligada|solto|solta|frouxo|frouxa|morto|morta|gasto|gasta|com (?:um |uma )?(?:problema|defeito|falha|erro|folga)))\b/;
  var CONC_PASSADO = /\b(?:estava|estavam|era|eram)(?: (?:muito|bem|bastante|meio))? [a-z]+/g, CONC_ESTADO = /\b(?:esta|estao|ta|tao|estava|estavam|era|eram)(?: (?:ja|bem|todo|toda|muito|bastante|meio))? [a-z]+/g;
  // A AÇÃO que o texto diz e a da tarefa ou da pendência: limpar, trocar, testar, inspecionar/verificar, revisar, atualizar. O registro que diz OUTRA ação («limpei as bombas de porão» para o «Teste das bombas de
  // porão», «verifiquei o óleo dos motores» para a «Troca de óleo») não conclui. Sem ação conhecida (fiz, feito, concluí, realizei, resolvi…) de um lado ou do outro, vale. ACAO_BASTA: as ações do texto que
  // concluem a de cada tipo (a verificação conclui a limpeza, o teste e a revisão; a troca conclui a limpeza, a inspeção e a revisão).
  var ACAO_TIPOS = [['L', /\b(?:limp|lav)\w*/], ['T', /\b(?:troc(?!ador)|troq|substitu)\w*/], ['S', /\b(?:auto)?test\w*/], ['V', /\b(?:inspe|verific|verifiqu|confer|vistori|cheq|checa)\w*/], ['R', /\b(?:revis|manuten)\w*/], ['A', /\batualiz\w*/]];
  var ACAO_BASTA = { L: 'LTVR', T: 'TR', S: 'SVR', V: 'VRST', R: 'RVT', A: 'AV' };
  function acoesDe(texto) { var f = dobra(texto); return ACAO_TIPOS.filter(function (a) { return a[1].test(f); }).map(function (a) { return a[0]; }); }
  function acaoCombina(fTexto, fAlvo) {
    if (!fTexto.length || !fAlvo.length) return true;
    return fTexto.some(function (x) { return fAlvo.some(function (g) { return ACAO_BASTA[g].indexOf(x) !== -1; }); });
  }
  // o equipamento: o texto que nomeia um equipamento (D.equipamentos, menos os de segurança) e não o do sistema da tarefa («limpei o filtro de água salgada do GERADOR» para a limpeza da CLIMATIZAÇÃO) não conclui
  function equipamentosDoTexto(texto) {
    var tk = tokens(texto), ids = [];
    (D.equipamentos || []).forEach(function (e) {
      if (e.seguranca) return;
      if ([e.nome, e.fabricante, e.modelo].concat(e.palavras || []).some(function (x) { var ws = tokens(x); return ws.length && ws.every(function (w) { return tk.indexOf(w) !== -1; }); })) ids.push(e.id);
    });
    return ids;
  }
  function equipamentoCombina(texto, sistema) {
    var ids;
    if (!sistema || !equip(sistema)) return true;
    ids = equipamentosDoTexto(texto);
    return !ids.length || ids.indexOf(sistema) !== -1;
  }
  // o texto conclui o serviço de uma tarefa ou de uma pendência: a frase de conclusão, a ação dela e o equipamento (`titulo`: o texto da tarefa ou da pendência; `sistema`: o da tarefa)
  function concluiAlvo(texto, titulo, sistema) {
    return conclusao(texto) && acaoCombina(acoesDe(texto), acoesDe(titulo)) && equipamentoCombina(texto, sistema);
  }
  function conclusao(texto) {
    var raw = String(texto || ''), f = dobra(raw).replace(/[.,;:!()"“”]+/g, ' ').replace(/\s+/g, ' ');
    return FEITO.test(f.replace(CONC_ESTADO, ' ')) && !CONC_FUTURO.test(f) && !CONC_DUVIDA.test(f) && !CONC_NEGA.test(f) && !CONC_DEFEITO.test(f.replace(CONC_PASSADO, ' '));
  }
  // HH:MM de um instante ISO no fuso do barco (a linha do aparelho guarda o `iso`, não a hora); '' se não for data
  function horaDe(iso) { var ms = Date.parse(iso), A = window.CapitaoAgora; if (isNaN(ms)) return ''; try { return A.fmt.hora(ms, false); } catch (e) { return ''; } }
  // o texto dobrado letra a letra (sem acento, minúsculo, do MESMO tamanho): a posição achada nele vale no texto original, com os acentos e as maiúsculas do nome
  function dobra(raw) { return Array.prototype.map.call(String(raw || ''), function (c) { var x = norm(c); return x.length === 1 ? x : ' '; }).join(''); }
  // as palavras do texto sem o plural («filtros» = «filtro»): a frase da agenda e da pendência (palavras) casa em sequência, palavra a palavra
  function stem(w) { return w.length > 3 ? w.replace(/s$/, '') : w; }
  function raizes(s) { return norm(s).replace(/[^a-z0-9]+/g, ' ').trim().split(' ').filter(Boolean).map(stem); }
  function contemFrase(tk, frase) {
    var ft = raizes(frase), i, j;
    if (!ft.length) return false;
    for (i = 0; i + ft.length <= tk.length; i++) { for (j = 0; j < ft.length && tk[i + j] === ft[j]; j++); if (j === ft.length) return true; }
    return false;
  }
  function citaFrases(tk, frases) { return Array.isArray(frases) && frases.some(function (f) { return typeof f === 'string' && contemFrase(tk, f); }); }

  // ——— Pendências (F20; CONTRATO §1.9, §1.25) ———
  // A pendência é uma linha do diário com `pend: true`: as 3 do arquivo (d03, d05, d07, pelo id) e as do aparelho (pelo `iso`). O ESTADO vem das linhas de ação do aparelho (`acao`: resolve | reabre, `alvo`): vale a
  // mais nova por alvo, e nada se apaga — resolver, reabrir e desfazer são linhas NOVAS. Aberta = sem ação ou com a última «reabre». CapitaoAgora.contagens().pendencias conta do mesmo jeito.
  var PEND_OK = 'var(--cap-ok, #34c77a)';
  function acoesDePend(linhas) {
    var m = {};
    linhas.forEach(function (l) { if (l && (l.acao === 'resolve' || l.acao === 'reabre') && typeof l.alvo === 'string' && !tem(m, l.alvo)) m[l.alvo] = l; });   // (mais nova primeiro: a 1ª ação de um alvo é a última)
    return m;
  }
  function pendItem(x, alvo, origem, ac) {
    var a = tem(ac, alvo) ? ac[alvo] : null;
    return { alvo: alvo, origem: origem, id: origem === 'gerada' ? alvo : null, d: x.d, h: x.h || '', iso: x.iso, sys: x.sys || 'Diário', tom: x.tom || x.tone || 'accent', who: x.who || '', t: String(x.t),
      ref: typeof x.ref === 'string' ? x.ref : null, palavras: Array.isArray(x.palavras) ? x.palavras.filter(function (f) { return typeof f === 'string'; }) : [], aberta: !a || a.acao === 'reabre', acao: a ? a.acao : null, acaoIso: a ? a.iso : null, sim: x.sim === true };
  }
  // todas as pendências (abertas e resolvidas), as do arquivo primeiro; `ctx.semSim`: as do aparelho gravadas com a simulação ligada ficam fora (simulacao false, na ficha)
  function pendenciasLista(ctx) {
    var linhas = loadDiario(), ac = acoesDePend(linhas), out = [];
    (D.diario || []).forEach(function (x) { if (x && x.pend === true && typeof x.id === 'string') out.push(pendItem(x, x.id, 'gerada', ac)); });
    vigente(linhas).forEach(function (l) { if (l.pend === true && typeof l.iso === 'string' && !(ctx && ctx.semSim && l.sim === true)) out.push(pendItem(l, l.iso, 'aparelho', ac)); });
    return out;
  }
  function pendenciaDe(alvo, ctx) { return typeof alvo === 'string' ? pendenciasLista(ctx).filter(function (p) { return p.alvo === alvo; })[0] || null : null; }
  function fimPend(t) { return limpaT(t, 140).replace(/[\s.!;:—–-]+$/, ''); }   // (o texto da pendência sem o ponto final: a frase seguinte começa por « — » ou « .»)
  function linhaDePend(p, acao, extra) {
    var e = { acao: acao, alvo: p.alvo, sys: p.sys || 'Diário', tone: acao === 'resolve' ? PEND_OK : 'var(--cap-warn, #f0a63a)', who: quem() };
    return Object.assign(e, extra);
  }
  // RESOLVER (a tela, um toque; ou o registro que cita a pendência): linha nova `resolve`. null = a pendência não existe ou já está resolvida. `opts.de` = a linha do registro que a fechou.
  function resolvePendencia(alvo, opts) {
    var p = EM_SOS ? null : pendenciaDe(alvo), de = opts && opts.de, lin, e;
    if (!p || !p.aberta) return null;
    e = linhaDePend(p, 'resolve', { t: 'Pendência resolvida: ' + fimPend(p.t) + (de ? ' — fechada pelo registro de ' + de.d + (horaDe(de.iso) ? ' às ' + horaDe(de.iso) : '') + ' (' + (de.who || quem()) + ').' : ' — marcada como resolvida por ' + quem() + '.') + ' Linha nova, nada se apaga.',
      src: de ? 'app · pendência resolvida pelo registro' : 'app · pendência resolvida' });
    if (p.ref) e.ref = p.ref;
    if (de && de.iso) e.de = de.iso;
    lin = addDiario1(e);
    return lin ? { alvo: p.alvo, id: p.id, t: p.t, sys: p.sys, linha: lin, desfazAte: Date.now() + (opts && opts.chat ? TICKET_DESFAZ_CHAT : TICKET_DESFAZ) } : null;
  }
  // REABRIR (a tela): linha nova `reabre`. null = não existe ou já está aberta.
  function reabrePendencia(alvo) {
    var p = EM_SOS ? null : pendenciaDe(alvo), e, lin;
    if (!p || p.aberta) return null;
    e = linhaDePend(p, 'reabre', { t: 'Pendência reaberta: ' + fimPend(p.t) + ' — reaberta por ' + quem() + '. Linha nova, nada se apaga.', src: 'app · pendência reaberta' });
    if (p.ref) e.ref = p.ref;
    lin = addDiario1(e);
    return lin ? { alvo: p.alvo, id: p.id, t: p.t, sys: p.sys, linha: lin } : null;
  }
  // DESFAZER o fechamento (dentro da janela: 10 s na tela, 10 min no chat): linha nova `reabre`. Recebe o que o registro devolveu em `.pendencia` (alvo, a linha do fechamento, o fim da janela); só desfaz se o último
  // estado da pendência ainda é ESSE fechamento (uma ação mais nova, feita noutro canto, não é pisada). Fora da janela ou sem o fechamento: null, nada é escrito.
  function desfazPendencia(r) {
    var p = !EM_SOS && r && typeof r === 'object' ? pendenciaDe(r.alvo) : null, e, lin;
    if (!p || p.aberta || p.acao !== 'resolve' || !r.linha || p.acaoIso !== r.linha.iso || typeof r.desfazAte !== 'number' || Date.now() > r.desfazAte) return null;
    e = linhaDePend(p, 'reabre', { t: 'Pendência reaberta (fechamento desfeito): ' + fimPend(p.t) + '. Linha nova, nada se apaga.', src: 'app · pendência reaberta (desfeito)' });
    if (p.ref) e.ref = p.ref;
    lin = addDiario1(e);
    return lin ? { alvo: p.alvo, linha: lin } : null;
  }
  // as tarefas da equipe que o usuário agendou neste aparelho (F15) e ainda estão abertas: no fim da resposta da manutenção e da ficha (as 2 geradas da equipe ficam com a tela da equipe); nenhuma = nada
  function tarefasLinha() {
    var l = tarefasAgendadas({ semSim: EXEC_SEM_SIM });
    return l.length ? '\nTarefas da equipe agendadas (' + l.length + '): ' + l.slice(0, 5).map(function (t) { return t.n + ' — ' + (atrasadaN(t.dn) ? 'em atraso há ' + (-t.dn) + (t.dn === -1 ? ' dia' : ' dias') : brData(t.vence) + ' (' + emDias(diaData(t.vence)) + ')') + (t.quem ? ' · ' + t.quem : ''); }).join(' | ') + (l.length > 5 ? ' | … e mais ' + (l.length - 5) : '') + '.' : '';
  }
  function pendencias(ctx) { return pendenciasLista(ctx).filter(function (p) { return p.aberta; }); }
  // A pendência que o texto cita (as `palavras` dela; o plural vale): { p, fecha } com UMA citada, { ambigua } com duas ou mais abertas (nenhuma fecha; a resposta pergunta qual), null sem citação. Só as abertas contam.
  // (a tarefa da agenda que a pendência aponta pelo `ref` dá o sistema e o título que a frase de conclusão confere: o texto que nomeia OUTRO equipamento («filtro de água salgada do gerador») não fecha a da climatização)
  function alvoDaPend(p) { var t = p.ref ? tarefa(p.ref) : null; return { titulo: p.t + (t ? ' ' + t.t : ''), sistema: t ? t.sistema : '' }; }
  function achaPendencia(texto) {
    var tk = raizes(texto), cit = pendencias().filter(function (p) { return citaFrases(tk, p.palavras); }), a;
    if (!cit.length) return null;
    if (cit.length > 1) return conclusao(texto) ? { ambigua: cit } : null;   // (duas citadas e o texto não conclui nada: não há o que perguntar)
    a = alvoDaPend(cit[0]);
    return { p: cit[0], fecha: concluiAlvo(texto, a.titulo, a.sistema) };
  }

  // ——— Diário → agenda (F15) ———
  // «agendar|agende|marcar|programar X para dd/mm [com Fulano]» (ou «X agendada para dd/mm») → { n, vence ('AAAA-MM-DD'), quem } ou { passada: true }; a data pode ser dd/mm[/aa|/aaaa], «15 de novembro»,
  // «amanhã», «depois de amanhã», «daqui a N dias|semanas» e «dia 20». O pedido é o verbo no imperativo ou no infinitivo, sem pergunta (a cortesia «pode agendar…?» vale), sem negação e sem cancelamento.
  var AG_VERBO = /\b(agend(?:ar|e|a|amos|ei|ou|aram)|marc(?:ar|a|amos)|marque|program(?:ar|e|a|amos))\b/g, AG_FEITO = /\b(agendad[oa]s?|marcad[oa]s?|programad[oa]s?)\b/;
  var AG_AMBIGUO = /^(agenda|marca|programa)$/, AG_INICIO = /^[\s,]*(?:(?:por favor|favor|pode|poderia|voce|vc|consegue|da pra|da para|ok|entao|tambem|e|ai|capitao)[\s,]+)*$/, AG_NOME = /^\s+(de|do|da|dos|das)\b/, AG_ANOTA = /^\s*(?:(?:ai|la)\b|que\b|:)/;
  var AG_CORTESIA = /(?:^|[\s,])(?:pode|poderia|podia|consegue|conseguiria|da pra|da para|daria pra|daria para|tem como|seria possivel)(?:\s+(?:me|por favor|voce|vc))?[\s,]*$/, AG_ANTES = /\b(o|a|os|as|um|uma|do|da|dos|das|no|na|nos|nas|de|meu|minha|seu|sua|esse|essa|este|esta|pelo|pela)\s+$/;
  // A PERGUNTA sobre a agenda sem o «?» (o ditado e o teclado quase nunca o põem): «o que está agendado para amanhã», «tarefas agendadas para 15/11», «quais manutenções estão programadas para dia 20», «tem algo marcado para
  // dia 20», «como agendar a revisão para 15/11» não são pedido de agendar. O interrogativo na frente do verbo (AG_PERG), a listagem na frente do «agendada para» (AG_LISTA: tem, mostre, minhas…) e o nome que é só palavra genérica (AG_GENERICO: tarefas, manutenções, o que…) saem.
  var AG_PERG = /^[\s,]*(?:(?:e|entao|ai|capitao|por favor)[\s,]+)*(?:o que|oque|que|qual|quais|quando|quanto|quantos|quantas|quem|onde|como|por que|porque|sera que)\b/;
  var AG_LISTA = /^[\s,]*(?:(?:e|entao|ai|capitao|por favor)[\s,]+)*(?:tem|ha|existe|existem|temos|mostre|mostra|mostrar|liste|lista|listar|ver|veja|confira|conferir|diga|minhas?|meus)\b/;
  var AG_GENERICO = /^[\s,]*(?:(?:as|os|a|o|uns|umas|todas?|todos|minhas?|meus|nossas?|nossos|outras?|outros|essas?|esses|quais|que|alguma|algum|nenhuma|nenhum|tudo|algo|nada|coisa|coisas|tarefas?|manutencoes|manutencao|servicos?|compromissos?|itens?|revisoes|pendencias?|lembretes?|alertas?|avisos?|visitas|tem|ha)[\s,]*)+$/;
  // a primeira data do texto dobrado: { ini, fim, dia (desde 1970) } — dd/mm, «15 de novembro», «amanhã», «daqui a N dias», «dia 20»; null se não há; dia NaN se a data não existe
  function dataNoTexto(s) {
    var m, hoje = diaDe(msAgora()), p, mes;
    function r(grupo, dia) { var ini = m.index + m[0].length - grupo.length; return { ini: ini, fim: ini + grupo.length, dia: dia }; }
    if ((m = /(?:^|[^0-9\/])((\d{1,2})\/(\d{1,2})(?:\/(\d{4}|\d{2}))?)(?![0-9\/])/.exec(s))) return r(m[1], diaDigitado(+m[2], +m[3], m[4]));
    if ((m = /(?:^|[^0-9])((?:dia )?(\d{1,2}) de (janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)(?: de (\d{4}))?)(?![a-z0-9])/.exec(s))) return r(m[1], diaDigitado(+m[2], MES_NUM[m[3]], m[4]));
    if ((m = /(?:^|[^a-z])(depois de amanha|amanha)(?![a-z])/.exec(s))) return r(m[1], hoje + (m[1] === 'amanha' ? 1 : 2));
    if ((m = /(?:^|[^a-z0-9])((?:daqui a|em) (\d{1,3}) (dias?|semanas?))(?![a-z])/.exec(s))) return r(m[1], hoje + +m[2] * (/^semana/.test(m[3]) ? 7 : 1));
    if ((m = /(?:^|[^a-z0-9])((?:(?:no|o|pro|para o|ate o|até o) )?dia (\d{1,2}))(?![0-9\/])/.exec(s))) {
      p = +m[2]; mes = +diaIso(hoje).slice(5, 7);
      var ano = +diaIso(hoje).slice(0, 4), n = dataCivil(ano, mes, p);
      if (isNaN(n) || n < hoje) { mes++; if (mes > 12) { mes = 1; ano++; } n = dataCivil(ano, mes, p); }
      return r(m[1], n);
    }
    return null;
  }
  function achaAgendar(texto) {
    var raw = String(texto || '').slice(0, 1000), f = dobra(raw), re = new RegExp(AG_VERBO.source, 'g'), v = null, pp = null, x, dep, antes, ini, resto, d, hoje, n, depois, sem, q, quemT = '', w, lw;
    while ((x = re.exec(f))) {
      dep = f.slice(x.index + x[0].length); antes = f.slice(0, x.index);
      if (AG_AMBIGUO.test(x[1]) && (!AG_INICIO.test(antes.replace(/\?/g, ' ')) || AG_NOME.test(dep))) continue;   // «a agenda de manutenção», «o programa do plotter»
      if (/^mar[cq]/.test(x[1]) && AG_ANOTA.test(dep)) continue;   // «marca aí que troquei…» é anotar, não agendar
      v = x; break;
    }
    // pergunta: só o pedido educado («pode agendar … para 15/11?»); «quando agendar…?» não é pedido
    if (raw.indexOf('?') >= 0 && !(v && AG_CORTESIA.test(f.slice(0, v.index)) && f.slice(0, v.index).indexOf('?') < 0)) return null;
    if (!v) pp = AG_FEITO.exec(f);
    if (!v && !pp) return null;
    if (v && AG_PERG.test(f.slice(0, v.index))) return null;   // «como agendar a revisão para 15/11» (sem o «?»)
    if (pp && (AG_PERG.test(f.slice(0, pp.index)) || AG_LISTA.test(f.slice(0, pp.index)) || AG_GENERICO.test(f.slice(0, pp.index).replace(/(?:\s+(?:esta|estao|foi|foram|ficou|ficaram|fica|ja))+\s*$/, '')))) return null;   // «o que está agendado para amanhã», «tarefas agendadas para 15/11»
    if (/\b(nao|nunca)\b/.test(f.slice(0, v ? v.index : pp.index)) || /\b(cancel\w*|desmarc\w*)\b/.test(f)) return null;
    if (v && AG_ANTES.test(f.slice(0, v.index))) return null;   // «a marca», «o programa»: substantivo
    ini = v ? v.index + v[0].length : pp.index + pp[0].length; resto = f.slice(ini); d = dataNoTexto(resto);
    if (!d || isNaN(d.dia)) return null;
    hoje = diaDe(msAgora());
    if (d.dia < hoje) return v ? { passada: true, vence: diaIso(d.dia) } : null;   // «revisão marcada para 10/09» (fato) já passado = registro antigo, não pedido
    n = v ? raw.slice(ini, ini + d.ini) : raw.slice(0, pp.index).replace(/(?:\s+(?:est[áa]|est[ãa]o|foi|foram|ficou|ficaram|fica|j[áa]))+\s*$/i, '');   // («a revisão do gerador está agendada para 20/11»: o nome é «revisão do gerador»)
    depois = raw.slice(ini + d.fim).replace(/\?+\s*$/, '');
    sem = function (s) { return s.replace(/\s+(?:com|responsavel|responsável)\s*:?\s+.*$/i, ''); };
    n = limpaNome(sem(n.replace(/(?:\s+(?:para|pra|pro|em|no|na|o|a|ate|até|dia|de|do|da))+\s*$/i, '')));
    if (!n || n.length < 3) n = limpaNome(sem(depois));
    if (!n || n.length < 3) return null;
    // responsável: «com Rafael», «responsável: Lucas», «com a marina» (o papel conhecido ou o nome com maiúscula); «com urgência» não
    q = /(?:^|\s)(?:[Cc]om|[Rr]espons[aá]vel)\s*:?\s+(?:[oa]\s+)?([A-Za-zÀ-ÿ][\wÀ-ÿ.-]*(?:\s+[A-ZÀ-Ý][\wÀ-ÿ.-]*)?)/.exec(raw.slice(ini));
    if (q) { w = q[1]; lw = norm(w.split(/\s+/)[0]); if (/^(?:marina|tecnico|oficina|estaleiro|dealer|mecanico|eletricista|equipe)$/.test(lw)) quemT = lw === 'tecnico' ? 'técnico' : lw === 'mecanico' ? 'mecânico' : lw; else if (/^[A-ZÀ-Ý]/.test(w)) quemT = w; }
    n = n.slice(0, 120); n = n.charAt(0).toUpperCase() + n.slice(1);
    return { n: n, vence: diaIso(d.dia), quem: quemT.slice(0, 40) };
  }
  function limpaNome(s) { return String(s || '').replace(/^[\s,;:—–-]+|[\s,;:.!—–-]+$/g, '').replace(/^(?:(?:a|o|as|os|uma|um)\s+)/i, '').trim(); }
  // as tarefas da agenda (as 14 geradas, ainda não executadas) que o texto cita pelas `palavras` delas
  function tarefasDoTexto(texto) {
    var tk = raizes(texto), ex = loadExec();
    return (D.agenda || []).filter(function (t) { return !ex[t.id] && citaFrases(tk, t.palavras); });
  }
  var OUTRO_DIA = /\b(?:ontem|anteontem|semana passada|mes passado|ano passado|outro dia|ha (?:\w+ ){1,2}(?:dias?|semanas?|mes|meses|anos?)|(?:dias?|semanas?|meses) atras|(?:na |no |nesta |neste |nessa |nesse )?(?:segunda|terca|quarta|quinta|sexta|sabado|domingo)(?: passad[oa])?|dia \d{1,2}|\d{1,2}\/\d{1,2})\b/;
  // A proposta que o texto de um registro faz: agendar (a tarefa nova) vence «foi feito» (o Executado). O Executado é datado na confirmação (markExec): o texto que cita OUTRO dia («ontem», «dd/mm») não
  // propõe (a tela marca a tarefa com a data certa); e o texto que cita duas tarefas não propõe nenhuma.
  function propostaDoTexto(texto) {
    var ag = achaAgendar(texto), ts;
    if (ag) {
      if (ag.passada) return null;
      if (loadTarefas().some(function (t) { return norm(t.n) === norm(ag.n) && t.vence === ag.vence && !loadExec()[t.id]; })) return null;   // já está na agenda
      return { k: 'tarefa', prop: { n: ag.n, vence: ag.vence, quem: ag.quem, sistema: sistemaDoTexto(texto) || undefined } };
    }
    if (!conclusao(texto) || OUTRO_DIA.test(dobra(texto))) return null;
    ts = tarefasDoTexto(texto); if (ts.length !== 1) return null;   // (as já executadas não entram em tarefasDoTexto)
    if (!acaoCombina(acoesDe(texto), acoesDe(ts[0].t)) || !equipamentoCombina(texto, ts[0].sistema)) return null;   // («verifiquei o óleo dos motores» não é a «Troca de óleo e filtros»; «limpei o filtro do gerador» não é o da climatização)
    return { k: 'exec', prop: { tarefa: ts[0].id } };
  }
  function sistemaDoTexto(texto) { var e = equipamentoDoRelato(texto); return e ? e.id : ''; }
  // o texto da proposta = o que o CONFIRMAR grava no diário (ticketTela mostra este mesmo texto); a tela refaz o texto depois do ✎ (muda o prop) com B.textoTicket(k, prop)
  function textoTicket(k, prop) {
    var p = prop || {}, ag;
    if (k === 'exec') { ag = tarefa(p.tarefa); return ag ? 'Executado: ' + ag.t + ' (' + ag.equip + ') — marcado a partir do registro do diário. Linha nova, nada se apaga.' : ''; }
    if (k === 'tarefa') return p.n && p.vence ? 'Tarefa da equipe: ' + p.n + ' — vence ' + brData(p.vence) + (p.quem ? ' · responsável: ' + p.quem : '') + '. Agendada pelo diário — linha nova, nada se apaga.' : '';
    return '';
  }
  // a proposta da agenda ainda aberta que é a MESMA (a mesma tarefa a executar; o mesmo nome e dia a agendar): não se propõe duas vezes
  function ticketAberto(k, prop) {
    return ticketsAbertos().filter(function (t) { var tp = t.prop || {}; return t.k === k && ((k === 'exec' && tp.tarefa === prop.tarefa) || (k === 'tarefa' && norm(tp.n) === norm(prop.n) && tp.vence === prop.vence)); })[0] || null;
  }
  // a proposta de um registro já gravado (a linha do diário que a originou é o alvo): a mesma proposta ainda aberta não duplica. null = o texto não propõe nada.
  function ticketDoRegistro(e) {
    var p = e && !EM_SOS ? propostaDoTexto(e.t) : null, txt, ja;
    if (!p) return null;
    txt = textoTicket(p.k, p.prop); if (!txt) return null;
    ja = ticketAberto(p.k, p.prop);
    return ja || addTicket({ k: p.k, origem: 'regra', texto: txt, prop: p.prop, alvo: { tipo: 'diario', id: e.iso } });
  }
  // O que o registro faz depois de gravado (addDiario com opts): fecha a pendência que cita e/ou abre a proposta de agenda. Nada disso vale para a linha de ação, a do SOS nem o texto de emergência ou de
  // pressão de óleo (o diário com alerta traz os passos, não mexe na agenda). null = nenhum efeito.
  function efeitosDoRegistro(entry, opts) {
    var r = {}, n, pa, tk, feito = false;
    if (EM_SOS || !entry || entry.acao || linhaDoSOS(entry) || typeof entry.t !== 'string') return null;
    n = pad(entry.t);
    if (emergencia(n) || oleo(n) === 1) return null;
    if (opts.pendencia) {
      pa = achaPendencia(entry.t);
      if (pa && pa.ambigua) { r.ambigua = pa.ambigua; feito = true; }
      else if (pa && pa.fecha) { r.pendencia = resolvePendencia(pa.p.alvo, { de: entry, chat: !!opts.chat }); feito = feito || !!r.pendencia; }
    }
    if (opts.agenda) { tk = ticketDoRegistro(entry); if (tk) { r.ticket = tk; feito = true; } }
    return feito ? r : null;
  }
  // ——— A proposta que espera a resposta no chat (F15, F12) ———
  // UMA por vez: o alarme pedido («me avise se…») e a proposta da agenda (a tarefa feita, o agendamento). Vale 10 min; o «sim» e o «não» curtos só valem LOGO depois (a conversa dela, sem outra pergunta no meio);
  // «confirmar», «recusar» e os botões valem sempre dentro dos 10 min. `seq` identifica a proposta: o botão de uma antiga não age na nova. DESFAZ guarda o que acabou de ser confirmado ou fechado (10 min): «desfazer»
  // desmancha. A emergência, o NOVA e o ENCERRAR zeram as duas (limpaConversa). Nada é gravado sem o Confirmar; o pedido de link (commit false) não arma nada.
  var PEND_CHAT = null, DESFAZ = null, PROP_SEQ = 0, ALVO_PROP = null, PROP_VALE = 10 * 60e3;
  // quando o último pedido de alarme virou proposta (mesmo a de link, que não arma): 30 min de memória. O «confirmar alarme» e o «cancelar o alarme» escritos valem só nesse tempo — depois que a proposta venceu
  // (10 min), ou que a emergência/NOVA a zerou, ainda é a resposta local «nenhum alarme esperando»; sem pedido recente, «cancelar o alarme» é o alarme do barco e segue para as rotas de sempre
  var ALM_PEDIU = 0, ALM_MEMORIA = 30 * 60e3;
  function almPediuRecente() { return !!ALM_PEDIU && Date.now() - ALM_PEDIU < ALM_MEMORIA; }
  function armaProp(tipo, dados) { PROP_SEQ++; PEND_CHAT = Object.assign({ tipo: tipo, seq: PROP_SEQ, ate: Date.now() + PROP_VALE, n: undefined }, dados); return PEND_CHAT; }
  function armaDesfaz(tipo, dados, ate) { PROP_SEQ++; DESFAZ = Object.assign({ tipo: tipo, seq: PROP_SEQ, ate: ate, n: undefined }, dados); return DESFAZ; }
  function propVale() { return PEND_CHAT && Date.now() < PEND_CHAT.ate ? PEND_CHAT : null; }
  function desfazVale() { return DESFAZ && Date.now() < DESFAZ.ate ? DESFAZ : null; }
  function botoesProp(p) { return [{ l: 'Confirmar', href: '#capitao-prop-confirma-' + p.seq }, { l: 'Recusar', href: '#capitao-prop-recusa-' + p.seq }]; }
  function botaoDesfaz(d) { return { l: 'Desfazer', href: '#capitao-prop-desfaz-' + d.seq }; }
  // o botão tocado vale 5 s como alvo da proposta: se a proposta mudou desde que ele foi desenhado, a resposta diz que é antiga e não age na nova
  function alvoProp() { var a = ALVO_PROP; ALVO_PROP = null; return a && Date.now() - a.t < 5000 ? a : null; }
  var PC_CONFIRMA = /^ (?:(?:sim|ok|pode|por favor|entao|capitao|isso|claro|certo|ta|beleza|manda|vai|so|e) )*(?:confirm(?:a|e|ar|o)|cri(?:a|e|ar)|agend(?:a|e|ar)|marc(?:a|ar)|marque|ativ(?:a|e|ar))(?: (?:isso|esse|este|essa|esta|o|a|alarme|aviso|tarefa|proposta|executado|executada|feito|feita|como|na|agenda|mesmo|agora|por favor|ai|pra mim|para mim|ja|tudo))* $/;   // (sem «um»/«uma»: «criar um alarme» é um pedido NOVO, não a confirmação do que espera)
  var PC_SIM = /^ (?:(?:sim|pode|claro|confirmo|confirmado|pode ser|com certeza|positivo|perfeito|isso mesmo|por favor) ?)+ $/;
  var PC_RECUSA = /^ (?:(?:nao|ok|por favor|entao|capitao|sim) )*(?:recus(?:a|e|ar)|cancel(?:a|e|ar)|descart(?:a|e|ar)|esquec(?:a|e|er)|nao (?:crie|criar|agende|agendar|marque|marcar|quero|precisa|confirme|confirmar))(?: (?:isso|esse|este|essa|esta|o|a|um|uma|alarme|aviso|tarefa|proposta|executado|agenda|mesmo|agora|por favor|ai))* $/;
  var PC_NAO = /^ (?:nao|n|nope|negativo)(?: obrigad[oa])? $/;
  var PC_DESFAZ = /^ (?:(?:ok|por favor|entao|capitao|pode|quero|preciso|vou|sim) )*(?:desfaz(?:er)?|desfaca|volta(?:r)? atras|anula(?:r)?)(?: (?:isso|esse|este|essa|esta|o|a|ultimo|ultima|registro|pendencia|proposta|tarefa|executado|agenda|ai|por favor|mesmo|agora))* $/;
  // F26: «O que você pode fazer?», «quais são as suas funções?», «o que o app faz?»: a lista do que o app faz, local, sem IA e sem internet. A frase inteira (com cortesia): o que tem assunto («o que você pode fazer pelo
  // gerador?») segue a rota dele. «O que você faz?», «o que você sabe?», «quem é você?» e «como você funciona?» continuam a saudação (a IA pode contar mais).
  var CAP_PREF = '(?:(?:capitao|ia|oi|ola|entao|bom dia|boa tarde|boa noite|e|ai|me diga|me fala|me conta|diga|fale|conta|agora|por favor|quero saber|queria saber|gostaria de saber|pode me dizer|poderia me dizer|me explica|explica|me mostra|mostra) )*';
  var CAPACIDADES = new RegExp('^ ' + CAP_PREF + '(?:(?:o ?que|oq|q) (?:e que )?(?:voce|vc|tu|o capitao|o app|o aplicativo|a ia) (?:pode|consegue|e capaz de)(?: me)?(?: (?:fazer|ajudar|responder|me ajudar))*|do que (?:voce|vc|tu) e capaz|(?:o ?que|oq|q) (?:o capitao|o app|o aplicativo|a ia) faz|(?:quais|que) (?:sao )?(?:as )?(?:suas |tuas |as )?(?:funcoes|funcionalidades|capacidades|habilidades|comandos|recursos)(?: (?:do app|do aplicativo|do capitao|que (?:voce|vc) tem|disponiveis))?|(?:quais|que) funcoes (?:o app|o aplicativo|o capitao|voce|vc) tem|(?:o ?que|oq|q) (?:eu )?posso (?:te |lhe )?(?:perguntar|pedir)(?: (?:a voce|pra voce|para voce|ao capitao|ao app))?|(?:o ?que|oq|q) da pra fazer(?: (?:aqui|no app|neste app|nesse app))?|lista de funcoes(?: do app)?) (?:por favor )?$');
  function capacidadesPergunta(q) { return !EM_SOS && CAPACIDADES.test(q); }
  var PC_BTN_CONFIRMA = /^ confirmar a proposta $/, PC_BTN_RECUSA = /^ recusar a proposta $/;
  var PC_SO_CONFIRMA = /^ (?:(?:sim|ok|pode|por favor|entao|capitao) )*confirm(?:a|e|ar|o)(?: (?:isso|esse|a proposta|o agendamento|por favor))* $/, PC_SO_RECUSA = /^ (?:(?:nao|ok|por favor|entao|capitao) )*recus(?:a|e|ar)(?: (?:isso|essa|a proposta|o agendamento|por favor))* $/;
  var AL_CONFIRMA_EXP = /^ (?:(?:sim|ok|pode|por favor|entao|capitao) )*confirm(?:a|e|ar|o) (?:o )?alarme $/, AL_CANCELA_EXP = /^ (?:(?:nao|ok|por favor|entao|capitao) )*(?:cancel(?:a|e|ar)|recus(?:a|e|ar)|descart(?:a|e|ar)) (?:o )?(?:alarme|pedido de alarme) $/;
  // a resposta do usuário à proposta que espera (ou o «desfazer»): a chave, ou null. Roda depois da emergência e do óleo (a pergunta de emergência zera tudo).
  function propRota(qRaw, q) {
    var p = propVale(), logo = !!p && p.n === CONV.n && !CONV.pergunta;
    if (EM_SOS) return null;
    if (PC_DESFAZ.test(q)) return 'ticketDesfaz';   // (sem o que desfazer, a resposta diz isso)
    if (p) {
      if (PC_CONFIRMA.test(q) || (logo && PC_SIM.test(q))) return p.tipo === 'alarme' ? 'alarmeConfirma' : 'ticketConfirma';
      if (PC_RECUSA.test(q) || (logo && PC_NAO.test(q))) return p.tipo === 'alarme' ? 'alarmeCancela' : 'ticketRecusa';
    }
    if (AL_CONFIRMA_EXP.test(q) && almPediuRecente()) return 'alarmeConfirma';
    if (AL_CANCELA_EXP.test(q) && almPediuRecente()) return 'alarmeCancela';
    // a pergunta pronta de um botão velho (a proposta venceu, a página recarregou, outra pergunta zerou): a resposta local diz que não há proposta, nunca a IA
    if (PC_BTN_CONFIRMA.test(q) || PC_SO_CONFIRMA.test(q)) return 'ticketConfirma';   // («confirmar» sozinho, sem proposta esperando, é resposta local: não há o que confirmar)
    if (PC_BTN_RECUSA.test(q) || PC_SO_RECUSA.test(q)) return 'ticketRecusa';
    return null;
  }
  function brDia(n) { return brData(diaIso(n)); }
  function emDias(n) { var d = n - diaDe(msAgora()); return d === 0 ? 'hoje' : d === 1 ? 'amanhã' : d > 1 ? 'em ' + d + ' dias' : 'há ' + (-d) + (d === -1 ? ' dia' : ' dias'); }
  function respTxt(prop) { return prop && prop.quem ? ' · responsável: ' + prop.quem : ''; }
  // as linhas e os botões que um registro gravado acrescenta à resposta do chat (F20, F15): a pendência fechada (com o Desfazer), a citação ambígua e a proposta da agenda (com Confirmar e Recusar). Arma as duas
  // esperas. Devolve { linhas, botoes, fala }.
  function efeitosNoChat(reg, p) {
    var r = { linhas: [], botoes: [], fala: '' }, pd, tk, d, pe, ag, t;
    if (!reg) return r;
    if (reg.ambigua) {
      r.linhas.push('O registro cita mais de uma pendência aberta (' + reg.ambigua.map(function (x) { return limpaT(x.t, 60); }).join(' · ') + '): nenhuma foi fechada. Diga qual foi resolvida.');
      r.fala += ' Citou mais de uma pendência; diga qual foi resolvida.';
    }
    if ((pd = reg.pendencia)) {
      d = armaDesfaz('pend', { r: pd }, pd.desfazAte);
      r.linhas.push('Pendência fechada: ' + fimPend(pd.t) + ' — o registro conclui o serviço (linha nova no diário). Se não era isso, diga “desfazer” ou toque em Desfazer.');
      r.botoes.push(botaoDesfaz(d)); r.fala += ' Pendência fechada.';
    }
    if ((tk = reg.ticket)) {
      pe = armaProp('ticket', { id: tk.id });
      ag = tk.k === 'exec' ? tarefa(tk.prop && tk.prop.tarefa) : null;
      t = tk.k === 'exec' ? 'Proposta: marcar “' + (ag ? ag.t : '') + '” como executada na agenda' : 'Proposta: agendar “' + (tk.prop && tk.prop.n) + '” para ' + brData(tk.prop && tk.prop.vence) + respTxt(tk.prop) + ' na agenda da equipe';
      r.linhas.push(t + '. Nada é gravado sem o seu Confirmar: toque em Confirmar ou diga “confirmar” (ou “recusar”).');
      r.botoes = r.botoes.concat(botoesProp(pe));
      r.fala += tk.k === 'exec' ? ' Posso marcar a tarefa como executada. Confirma?' : ' Posso agendar a tarefa. Confirma?';
    }
    return r;
  }
  // ——— Alarmes pedidos no chat (F12; CONTRATO §1.21, §1.25) ———
  // «me avise se a pressão do óleo do BB cair abaixo de 2 bar» → uma PROPOSTA (nada é gravado) que vira regra só no Confirmar. A lista de medidas é FECHADA e vem do dado gerado (D.alarmesPedidos.metricas:
  // nome, palavras, unidade, casas, faixa aceita para o limite, sentidos); a regra é a faixa própria da medida, não o D.replay.limites. capitao.alarmes.v1 = linhas { id: 'usr_<n>', campo, op, limite, iso, who, sim?,
  // acao?: 'apaga' }: a linha mais nova de cada id é o estado, e apagar é uma linha NOVA (nada se apaga; o número não volta a ser usado). Avaliado no aparelho contra o quadro do instante (e, com o replay, os últimos
  // segundos): AVISO só na tela — nunca crítico, nunca abre o SOS nem a C3, nunca fala, nunca grava no diário, sem notificação. A faixa do topo (Fase 4) lê almAtivos().
  function almCfg() { var A = D.alarmesPedidos; return !EM_SOS && A && typeof A === 'object' && Array.isArray(A.metricas) ? A : null; }
  function almMetricas() {
    var A = almCfg();
    return A ? A.metricas.filter(function (m) { return m && typeof m.id === 'string' && Array.isArray(m.campos) && typeof m.campos[0] === 'string' && Array.isArray(m.faixa) && m.faixa.length === 2 && m.faixa[0] < m.faixa[1] && Array.isArray(m.ops) && Array.isArray(m.palavras) && typeof m.nome === 'string'; }) : [];
  }
  function almMetricaDeCampo(c) { return almMetricas().filter(function (m) { return m.campos[0] === c; })[0] || null; }
  function ehAlarme(l) { return !!l && typeof l === 'object' && typeof l.id === 'string' && /^usr_\d{1,6}$/.test(l.id) && typeof l.iso === 'string' && (l.acao === 'apaga' || (typeof l.campo === 'string' && (l.op === '<' || l.op === '>') && typeof l.limite === 'number' && isFinite(l.limite))); }
  function almN(l) { return +String(l.id).slice(4); }
  // as regras ATIVAS (a linha mais nova de cada id não é «apaga»), da mais antiga à mais nova, com a medida; `ctx.semSim`: as gravadas com a simulação ligada ficam fora (simulacao false, na ficha)
  function almVigentes(ctx) {
    var vistos = {}, out = [];
    if (!almCfg()) return out;
    listaCru(K.alarmes).filter(ehAlarme).forEach(function (l) { if (!tem(vistos, l.id)) { vistos[l.id] = 1; if (l.acao !== 'apaga') out.push(l); } });   // (mais nova primeiro: a 1ª linha de um id é o estado)
    return out.map(function (l) { var m = almMetricaDeCampo(l.campo); return m && !(ctx && ctx.semSim && l.sim === true) ? Object.assign({}, l, { n: almN(l), m: m }) : null; }).filter(Boolean).sort(function (a, b) { return a.n - b.n; });
  }
  function almProxN() { var mx = 0; listaCru(K.alarmes).forEach(function (l) { if (ehAlarme(l)) mx = Math.max(mx, almN(l)); }); return mx + 1; }
  function almIsoUnico(cru, ms) { var iso = new Date(ms).toISOString(); while (cru.some(function (x) { return x && x.iso === iso; })) iso = new Date(++ms).toISOString(); return iso; }
  // O CONFIRMAR: grava UMA linha por item ({ m, op, limite }); { criadas, erro } — erro 'max' (passa do máximo de ativos), 'indisponivel' (sem a lista, ou no SOS); o item fora da faixa, do sentido ou repetido não entra.
  function almCria(itens) {
    var A = almCfg(), cru, ativas, n, criadas = [];
    if (!A) return { criadas: [], erro: 'indisponivel' };
    ativas = almVigentes();
    if (ativas.length + itens.length > (typeof A.max === 'number' ? A.max : 10)) return { criadas: [], erro: 'max' };
    cru = listaCru(K.alarmes); n = almProxN();
    itens.forEach(function (it) {
      var lin;
      if (!it || !it.m || (it.op !== '<' && it.op !== '>') || it.m.ops.indexOf(it.op) === -1 || typeof it.limite !== 'number' || !isFinite(it.limite) || it.limite < it.m.faixa[0] || it.limite > it.m.faixa[1]) return;
      if (ativas.concat(criadas).some(function (a) { return a.campo === it.m.campos[0] && a.op === it.op && a.limite === it.limite; })) return;
      lin = { id: 'usr_' + n++, campo: it.m.campos[0], op: it.op, limite: it.limite, iso: almIsoUnico(cru, Date.now()), who: quem() };
      if (sim()) lin.sim = true;
      cru.unshift(lin); criadas.push(lin);
    });
    if (criadas.length) write(K.alarmes, cru);
    return { criadas: criadas.map(function (l) { return Object.assign({}, l, { n: almN(l), m: almMetricaDeCampo(l.campo) }); }) };
  }
  // APAGAR o alarme #n: linha nova «apaga» (nada se apaga). null = não existe, já foi apagado ou o SOS.
  function almApaga(n) {
    var v = almVigentes().filter(function (a) { return a.n === n; })[0], cru, lin;
    if (!v) return null;
    cru = listaCru(K.alarmes);
    lin = { id: v.id, acao: 'apaga', campo: v.campo, op: v.op, limite: v.limite, iso: almIsoUnico(cru, Math.max(Date.now(), Date.parse(v.iso) + 1)), who: quem() };
    if (sim()) lin.sim = true;
    cru.unshift(lin); write(K.alarmes, cru);
    return lin;
  }
  function almNum(x, c) { return c === 0 ? mil(x) : nb(x, c); }
  function almTxt(m, v) { return almNum(v, m.casas) + ' ' + m.un; }
  function almRegra(a) { return a.m.nome + ' ' + (a.op === '<' ? 'abaixo de ' : 'acima de ') + almTxt(a.m, a.limite); }
  function almMotorTxt(m) { return m.motor ? ' — só vale com o motor em cruzeiro (a partir de 1.000 rpm)' : ''; }
  // ——— entender o pedido ———
  var ALM_CRIA = '(?:cri(?:e|a|ar)|configur(?:e|a|ar)|colo(?:que|ca|car)|ativ(?:e|a|ar)|program(?:e|a|ar)|mont(?:e|a|ar)|adicion(?:e|a|ar)|defin(?:a|ir))';
  var ALM_GAT_A = / (?:me )?(?:avis(?:e|a|ar)|alert(?:e|a|ar)|notifi(?:que|ca|car))(?:-me| me)? /, ALM_COND = / (?:quando|se|caso|sempre que|assim que|toda vez que) /;
  var ALM_GAT_B = new RegExp('^ (?:(?:por favor|entao|capitao|pode|poderia|voce pode|quero|queria|gostaria de|preciso|me ajuda a|ajuda a|vamos|ok) )*' + ALM_CRIA + ' (?:[a-z0-9]+ ){0,3}(?:alarmes?|alertas?|avisos?) | (?:quero|queria|gostaria de|preciso de|me d[ae]|faz|fazer|faca) (?:(?:um|uma|outro|outra|mais um|mais uma|novo|nova) )+(?:alarme|alerta|aviso) ');
  var ALM_GAT_C = / (?:alarmes?|alertas?|avisos?) (?:quando|se|caso|sempre que|para quando) /;
  var ALM_LT = / (?:abaixo d[eoa]s?|menos d[eoa]s?|menor(?:es)? (?:que|do que|d[eoa]s?)|inferior(?:es)? a|ca(?:irem|ir|iam|ia|i) (?:abaixo|para|a)|baixa(?:rem|r)? (?:de|abaixo|para|a)|baix(?:e|em) (?:de|abaixo|para)|desc(?:erem|er|am|a) (?:abaixo|para|a)|fica(?:rem|r)? (?:abaixo|menor|menos)|fiqu(?:e|em) (?:abaixo|menor|menos)|estiver(?:em)? (?:abaixo|menor|menos)|pass(?:arem|ar|em|e) abaixo)(?= )/;
  var ALM_GT = / (?:acima d[eoa]s?|mais d[eoa]s?|maior(?:es)? (?:que|do que|d[eoa]s?)|superior(?:es)? a|pass(?:arem|ar|em|e) d[eoa]s?|pass(?:arem|ar|em|e) (?:acima|a)|ultrapass\w+|exced\w+|sub(?:irem|ir|am|a) (?:acima|para|a|de|ate)|fica(?:rem|r)? (?:acima|maior|mais)|fiqu(?:e|em) (?:acima|maior|mais)|estiver(?:em)? (?:acima|maior|mais))(?= )/;
  // quem RELATA (está, caiu, acendeu, disparou, agora, luz vermelha…) não está configurando: o relato de pressão de óleo segue a instrução de segurança (oleo), nunca a proposta de alarme
  var ALM_RELATO = / (?:esta|estao|ta|tao|estava|estavam|caiu|cairam|acendeu|acesa|acesas|disparou|soou|apagou|parou|agora|neste momento|nesse momento|urgente|socorro|ajuda|problema|falha|falhou|luz|vermelha|vermelho|zerou|zerada|sem pressao) /;
  var ALM_PERGUNTA = / (?:como|onde|quando|qual|quais|quanto|porque|por que|o que|quem|sera|posso|devo) /;
  function almGatilho(q) { return (ALM_GAT_A.test(q) && ALM_COND.test(q)) || ALM_GAT_B.test(q) || ALM_GAT_C.test(q); }
  // O relato junto do pedido («pressão do óleo baixa no BB, me avise se cair abaixo de 2 bar», «baixou», «caindo», «o manômetro marca 1 bar, me avise…») segue a instrução de segurança (oleo): o pedido de alarme só é
  // configuração quando a frase COMEÇA pelo pedido — antes do gatilho («me avise», «alerte», «crie um alarme», «se», «quando») só cortesia ou o motor/lado (“por favor”, “capitão”, “no motor de bombordo”) — e não traz
  // sinal do estado de agora: nenhum sintoma (baixa, baixou, fraca, caindo, perdendo, oscilando, marca, vazando, quente, ruído…) fora da própria condição («cair abaixo de 2») e nenhum número antes dela (a leitura
  // citada). Na dúvida, o oleo() vale (os passos de segurança, local, sem leitura).
  var ALM_SINTOMA = / (?:baix[oa]s?|baixou|baixaram|fraco|fraca|fracos|fracas|pouc[oa]s?|zero|oscil\w*|perd\w*|cain\w*|despenc\w*|sumi\w*|diminu\w*|reduziu|reduziram|zerand\w*|marca|marcam|marcando|marcou|marcava|apit\w*|piscand\w*|acendend\w*|pingand\w*|vazand\w*|vazou|vazamentos?|fumac\w*|fumegand\w*|quent\w*|aquec\w*|esquent\w*|ruidos?|barulh\w*|estranh\w*|anormal\w*|anormais|esquisit\w*|trepid\w*|falhand\w*|falhas|tremend\w*|instave\w*|cheiro|cheirando|pior\w*|ruim|ruins|travand\w*|engasg\w*|limite) /;
  var ALM_ABRE_OK = ' por favor gentileza favor entao capitao ok ei oi ola olha bom dia boa tarde noite e ai pode poderia voce quero que preciso gostaria queria vamos tambem agora me no na nos nas do da de para pra o a os as motor motores bb be bombordo boreste estibordo lado ';
  var ALM_COMP_NUM = new RegExp('(?:' + ALM_LT.source + '|' + ALM_GT.source + ')(?= *\\d)', 'g');
  function almSinalEstado(q) {
    var s = q.replace(ALM_COMP_NUM, ' | '), i = s.indexOf(' | '), gs = [ALM_GAT_A, ALM_GAT_B, ALM_GAT_C, ALM_COND].map(function (r) { var m = r.exec(q); return m ? m.index : -1; }).filter(function (k) { return k >= 0; });   // (a condição vira ' | ': o número ANTES dela é a leitura que o usuário cita — «a pressão do óleo do BB 1,5 bar, me avise se cair abaixo de 1 bar» —, não o limite)
    if (q.slice(0, gs.length ? Math.min.apply(null, gs) : 0).trim().split(/\s+/).some(function (w) { return w && ALM_ABRE_OK.indexOf(' ' + w + ' ') === -1; })) return true;   // texto de relato ANTES do pedido
    return ALM_SINTOMA.test(s) || (i > 0 && /\d/.test(s.slice(0, i)));
  }
  // o pedido COMPLETO na forma de configuração («me avise se … cair abaixo de 2 bar»): gatilho + sentido + número e nenhuma palavra de relato. É o que vale ANTES do óleo (o relato de queda de pressão
  // segue a instrução de segurança; a configuração da regra não é relato) e o que o oleo() deixa de tratar como queda
  function almPedidoLite(q) { return !EM_SOS && !!D.alarmesPedidos && almGatilho(q) && (ALM_LT.test(q) || ALM_GT.test(q)) && /\d/.test(q) && !ALM_RELATO.test(q); }
  // (A cabeça de emergência — socorro, salvatagem, MMSI, EPIRB/baliza, Seafire, canal 16/rádio/DSC — nunca vira proposta de alarme: a route() as entrega às rotas de emergência ANTES de chegar aqui, e o oleo() devolver 0 não tira
  // nada dessas perguntas, que o cabecaEmerg pega pelas outras palavras. O testes/cerebro.py (p3g_rotas) confere a pergunta mista, com o EPIRB, o Seafire, o rádio, a salvatagem e o perigo.)
  // O «criar um alarme» do começo da fala SEM sentido nem número: só vale sozinho («criar um alarme», «quero um alarme novo») ou com a medida da lista e mais nada («criar um alarme de diesel»): a resposta diz o que
  // falta. Com outro assunto («ativar o alarme ao fundear», «configurar o alarme do porão», «… de profundidade no plotter», «programar aviso de manutenção») o alarme é o do barco: segue para as rotas de sempre.
  var ALM_SOBRA_OK = ' de do da dos das para pra por um uma uns umas o a os as e ou que se no na nos nas em ao aos favor pedido novo nova outro outra mais aqui agora ja mesmo mim me voce motor motores bb be bombordo boreste estibordo ';
  function almSoGatilho(q) {
    var g = ALM_GAT_B.exec(q), tk, med;
    if (!g) return false;
    tk = raizes(q.slice(g.index + g[0].length));
    med = almMedida(q);
    (med.itens || []).forEach(function (m) { m.palavras.forEach(function (f) { var i = posFrase(tk, f), n = raizes(f).length; while (i >= 0) { tk.splice(i, n); i = posFrase(tk, f); } }); });
    return tk.every(function (w) { return ALM_SOBRA_OK.indexOf(' ' + w + ' ') !== -1; });
  }
  // o pedido de alarme em geral (incompleto também: a resposta diz o que falta): gatilho + (sentido com número, ou uma medida da lista) ou o «criar um alarme» do começo da fala; nunca pergunta nem relato
  function almPedido(q) {
    if (EM_SOS || !almCfg() || ALM_RELATO.test(q)) return false;
    if (ALM_GAT_B.test(q) && !ALM_PERGUNTA.test(q) && !/\?/.test(q) && (((ALM_LT.test(q) || ALM_GT.test(q)) && /\d/.test(q)) || almSoGatilho(q))) return true;
    if (!((ALM_GAT_A.test(q) && ALM_COND.test(q)) || ALM_GAT_C.test(q))) return false;
    return ((ALM_LT.test(q) || ALM_GT.test(q)) && /\d/.test(q)) || !!almMedida(q).itens;
  }
  function almLado(tk) {
    var bb = tk.indexOf('bb') !== -1 || tk.indexOf('bombordo') !== -1, be = tk.indexOf('be') !== -1 || tk.indexOf('boreste') !== -1 || tk.indexOf('estibordo') !== -1;
    return bb && !be ? 'bb' : be && !bb ? 'be' : null;
  }
  function posFrase(tk, frase) {
    var ft = raizes(frase), i, j;
    if (!ft.length) return -1;
    for (i = 0; i + ft.length <= tk.length; i++) { for (j = 0; j < ft.length && tk[i + j] === ft[j]; j++); if (j === ft.length) return i; }
    return -1;
  }
  // a medida que o texto nomeia: a frase mais longa das `palavras` ganha; as medidas irmãs (óleo BB e BE, o banco sem dizer qual, águas cinzas e negras) que dividem a frase valem todas, e o lado dito (BB, BE,
  // bombordo, boreste) escolhe uma. { itens: [metricas] } ou { erro: 'medida' | 'ambigua' } (nenhuma, ou duas medidas diferentes no mesmo pedido).
  function almMedida(pq) {
    var tk = raizes(pq), lado = almLado(tk), melhor = 0, ach = [], cands, lc, comum, span = {}, outra = false, esg;
    almMetricas().forEach(function (m) {
      m.palavras.forEach(function (f) { var ft = raizes(f), i = posFrase(tk, f); if (i >= 0) ach.push({ m: m, f: ft.join(' '), len: ft.length, ini: i }); });
    });
    // «tanque de água cinza|negra|servida»: a frase genérica da água doce («tanque de água», «nível de água») com o qualificador de OUTRO tanque colado (dentro dela ou logo depois) é desse tanque, não da água doce
    esg = ach.filter(function (a) { return /^tanque_(?:cinzas|negras)_pct$/.test(a.m.campos[0]); });
    if (esg.length) ach = ach.filter(function (a) { return a.m.campos[0] !== 'tanque_agua_pct' || !esg.some(function (e) { return e.ini >= a.ini && e.ini <= a.ini + a.len; }); });
    ach.forEach(function (a) { melhor = Math.max(melhor, a.len); });
    if (!melhor) return { erro: 'medida' };
    cands = []; ach.forEach(function (a) { if (a.len === melhor && !cands.some(function (c) { return c.m === a.m; })) cands.push({ m: a.m, fr: [] }); });
    ach.forEach(function (a) { if (a.len === melhor) cands.forEach(function (c) { if (c.m === a.m && c.fr.indexOf(a.f) === -1) c.fr.push(a.f); }); });
    if (lado) { lc = cands.filter(function (c) { return new RegExp('_' + lado + '$').test(c.m.id); }); if (lc.length) cands = lc; }
    if (cands.length > 1) { comum = cands[0].fr.filter(function (f) { return cands.every(function (c) { return c.fr.indexOf(f) !== -1; }); }); if (!comum.length) return { erro: 'ambigua' }; }
    ach.forEach(function (a) { if (cands.some(function (c) { return c.m === a.m; }) && a.len === melhor) for (var k = a.ini; k < a.ini + a.len; k++) span[k] = 1; });
    ach.forEach(function (a) { var k, livre = true; if (a.len >= 2 && !cands.some(function (c) { return c.m === a.m; })) { for (k = a.ini; k < a.ini + a.len; k++) if (span[k]) livre = false; if (livre) outra = true; } });
    return outra ? { erro: 'ambigua' } : { itens: cands.map(function (c) { return c.m; }) };
  }
  var ALM_NUM = /(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)(?: ?(%|por cento|porcento|bar|volts?|v|graus?|°c|c|rpm|nos|knots?|kt|metros?|m|hpa|litros?|l))?(?= |$)/;
  var ALM_UN = { '%': '%', 'por cento': '%', porcento: '%', bar: 'bar', volt: 'V', volts: 'V', v: 'V', grau: '°C', graus: '°C', '°c': '°C', c: '°C', rpm: 'rpm', nos: 'nós', knot: 'nós', knots: 'nós', kt: 'nós', metro: 'm', metros: 'm', m: 'm', hpa: 'hPa', litro: 'L', litros: 'L', l: 'L' };
  var ALM_UN_ALHEIA = /^(?:pes?|ft|feet|foot|jardas?|yd|polegadas?|pol|bracas?|cm|mm|km|quilometros?|milhas?|mn|km\/h|kmh|kph|mph|m\/s|psi|kpa|mpa|pa|atm|mmhg|inhg|torr|kgf|f|°f|fahrenheit|kelvin|k|bf|beaufort|gal|galao|galoes|gallons?|lbs?|libras?|kg|quilos?|ton|toneladas?|kw|w|hp|cv|amps?|amperes?|ah|mah|mv|kv|h|horas?|min|minutos?|segundos?|dias?)$/;
  function almValor(t) { return parseFloat(/^\d{1,3}(\.\d{3})+(,\d+)?$/.test(t) ? t.replace(/\./g, '').replace(',', '.') : t.replace(',', '.')); }
  // O pedido entendido: { ok: true, itens: [{ m, op, limite }] } ou { ok: false, motivo: 'sentido' | 'limite' | 'medida' | 'ambigua' | 'unidade' | 'faixa' | 'op', m? }. O texto original (com as vírgulas dos decimais) é o que se lê.
  function almParse(raw) {
    var s = ' ' + norm(raw).replace(/</g, ' menor que ').replace(/>/g, ' maior que ').replace(/[?!;:()"“”]+/g, ' ').replace(/\s+/g, ' ').trim() + ' ';
    var lt = ALM_LT.exec(s), gt = ALM_GT.exec(s), ref = lt || gt, op, nm, un, lim, med, i, m;
    if (!ref) return { ok: false, motivo: 'sentido' };
    if (lt && gt) return { ok: false, motivo: 'ambigua' };   // «cair abaixo de 60 ou passar de 90»: um alarme por pedido
    op = lt ? '<' : '>';
    nm = ALM_NUM.exec(s.slice(ref.index));
    if (!nm) return { ok: false, motivo: 'limite' };
    med = almMedida(pad(raw));
    if (!med.itens) return { ok: false, motivo: med.erro };
    lim = almValor(nm[1]); un = nm[2] ? ALM_UN[nm[2]] : null;
    // a unidade que o app não usa («10 pés», «25 km/h», «5 psi»): não vira o número da unidade da medida (10 pés não são 10 m); o app não converte, diz a unidade dela
    if (!nm[2] && ALM_UN_ALHEIA.test((s.slice(ref.index + nm.index + nm[0].length).trim().split(' ')[0]) || '')) return { ok: false, motivo: 'unidade', m: med.itens[0] };
    for (i = 0; i < med.itens.length; i++) {
      m = med.itens[i];
      if (un && un !== m.un) return { ok: false, motivo: 'unidade', m: m };
      if (m.ops.indexOf(op) === -1) return { ok: false, motivo: 'op', m: m };
      if (!(lim >= m.faixa[0] && lim <= m.faixa[1])) return { ok: false, motivo: 'faixa', m: m };
    }
    return { ok: true, itens: med.itens.map(function (m2) { return { m: m2, op: op, limite: lim }; }) };
  }
  // «apagar alarme #2», «remover o alarme 3», «excluir alarme usr_4»: o número; 0 sem número
  var ALM_APAGA = /(?:^| )(?:apag(?:ue|a|ar)|remov(?:a|e|er)|exclu(?:a|i|ir)|delet(?:e|a|ar)|tir(?:e|a|ar)|retir(?:e|a|ar)|cancel(?:e|a|ar)|desativ(?:e|a|ar)) (?:o |esse |este |um |todos os |todas as |os |as )?(?:alarmes?|alertas?|avisos?)(?: pedid\w+| criad\w+)?(?: (?:numero|n|no|num))? ?[#]? ?(?:usr_)?(\d{1,6})?(?![0-9])/;
  // só é o pedido de apagar quando traz o NÚMERO ou diz «pedido(s)/criado(s)»: «desligar o alarme», «apagar alarme» e «cancelar o alarme do porão» são do alarme do barco, nunca desta rota
  function almApagaN(raw) {
    var m = EM_SOS ? null : ALM_APAGA.exec(' ' + norm(raw).replace(/[?!;:()"“”]+/g, ' ').replace(/\s+/g, ' ').trim() + ' ');
    if (!m || !almCfg()) return -1;
    return m[1] ? +m[1] : / (?:pedid|criad)\w+/.test(m[0]) ? 0 : -1;   // -1 = não é o pedido de apagar
  }
  var ALM_LISTA = / (?:meus|minhas) (?:[a-z]+ ){0,2}(?:alarmes?|alertas?|avisos?) | (?:alarmes?|alertas?|avisos?) (?:pedid\w+|criad\w+|configurad\w+|programad\w+|que (?:eu|nos|a gente) (?:pedi|pedimos|criei|criamos|configurei|configuramos|programei)) | (?:quais|que|ver|mostr\w+|list\w+|tenho|temos|tem) (?:[a-z]+ ){0,3}alarmes? (?:eu|nos) (?:pedi|criei|tenho|temos|configurei) | lista de alarmes pedid\w+ /;
  function almLista(q) { return !EM_SOS && !!almCfg() && ALM_LISTA.test(q) && !ALM_RELATO.test(q); }
  // ——— avaliar contra o quadro (F12; CONTRATO §1.21: histerese de 10 s, `motor: true` só a partir de 1.000 rpm) ———
  function almCond(m, op, limite, q) {
    var v = q ? q[m.campos[0]] : null, A = window.CapitaoAgora, rk, rpm;
    if (typeof v !== 'number' || !isFinite(v)) return null;   // sem leitura: não avalia
    v = A && A.fmt && typeof A.fmt.arred === 'function' ? A.fmt.arred(v, m.casas) : v;   // (a regra única do quadro compara o valor com as casas do campo)
    if (m.motor) { rk = /^motor_(bb|be)_/.exec(m.campos[0]); rpm = rk ? q['motor_' + rk[1] + '_rpm'] : null; if (typeof rpm !== 'number' || rpm < 1000) return false; }
    return op === '<' ? v < limite : v > limite;
  }
  // os alarmes pedidos ATIVOS no instante `ms` (o do instante da pergunta, o fixado ou agora): [{ id, n, nivel: 'aviso', rotulo, cor, rgb, sistema, lado?, campo, titulo, valor, limite, un, valorTxt, limiteTxt, texto, desde, desdeMs,
  // hora, fonte, pedido: true, op }] — a forma dos alertas do CapitaoAlertas, para a faixa do topo (Fase 4) juntar à lista. Ativo = a condição vale agora ou valeu nos últimos `histerese_s` s (fecha só depois de 10 s
  // sem valer); `desde` = o começo dessa sequência (até 160 s para trás, só com o replay). Sem quadro vivo (replay ou coletor), no SOS ou sem regra: [].
  function almAtivos(ms) {
    var A = almCfg(), regras, i = instante(), R = window.CapitaoReplay, H, cache = {}, NIV = (window.CapitaoAlertas && window.CapitaoAlertas.NIVEL && window.CapitaoAlertas.NIVEL.aviso) || {};
    if (!A || !i || !i.q || VIVAS[i.fonte] !== 1) return [];
    regras = almVigentes(); if (!regras.length) return [];
    H = typeof A.histerese_s === 'number' && A.histerese_s >= 0 ? Math.min(A.histerese_s, 60) : 10;
    ms = typeof ms === 'number' && isFinite(ms) ? ms : i.ms;
    function quadro(k) { var t = ms - k * 1000; if (!tem(cache, 'k' + k)) cache['k' + k] = k === 0 && ms === i.ms ? i.q : (i.fonte === 'replay' && R && typeof R.em === 'function' ? R.em(t) : (k === 0 ? i.q : null)); return cache['k' + k]; }
    return regras.map(function (a) {
      var ser = [], k, ult, ini, gap, v, d, A2 = window.CapitaoAgora, lado = /^motor_(bb|be)_/.exec(a.campo), q0 = quadro(0);
      for (k = 0; k <= 160; k++) { ser.push(almCond(a.m, a.op, a.limite, quadro(k)) === true); if (k >= H && !ser.slice(0, k + 1).some(Boolean)) break; if (i.fonte !== 'replay' && k === 0) break; }
      ult = ser.indexOf(true);
      if (ult < 0 || ult > H) return null;
      ini = ult; gap = 0;
      for (k = ult + 1; k < ser.length; k++) { if (ser[k]) { ini = k; gap = 0; } else if (++gap > H) break; }
      v = q0 && typeof q0[a.campo] === 'number' ? q0[a.campo] : null;
      d = ms - ini * 1000;
      var normal = ult > 0;   // a condição já não vale agora: o aviso só fecha 10 s depois de normalizar
      return { id: a.id, n: a.n, nivel: 'aviso', rotulo: NIV.rotulo || 'AVISO', cor: NIV.cor || 'var(--cap-warn, #f0a63a)', rgb: NIV.rgb || 'var(--cap-warn-rgb, 240,166,58)', sistema: /^motor_/.test(a.campo) ? 'motores' : /^bateria_/.test(a.campo) ? 'elétrico' : /^tanque_/.test(a.campo) ? 'tanques' : a.campo === 'diesel_litros' ? 'combustível' : 'navegação',
        lado: lado ? lado[1].toUpperCase() : undefined, campo: a.campo, titulo: 'Alarme pedido #' + a.n + ': ' + a.m.nome, valor: v, limite: a.limite, un: a.m.un, valorTxt: v == null ? '' : almTxt(a.m, v), limiteTxt: almTxt(a.m, a.limite), op: a.op,
        normalizando: normal, texto: 'Alarme pedido #' + a.n + ' — ' + a.m.nome + (v == null ? '' : ': ' + almTxt(a.m, v)) + ' (' + (normal ? 'já voltou ' + (a.op === '<' ? 'acima' : 'abaixo') + ' de ' + almTxt(a.m, a.limite) + '; o aviso fecha ' + H + ' s depois de normalizar' : (a.op === '<' ? 'abaixo' : 'acima') + ' de ' + almTxt(a.m, a.limite)) + ')', desde: new Date(d).toISOString(), desdeMs: d, hora: A2 && A2.fmt ? A2.fmt.hora(d, true) : '',
        fonte: A.fonte || 'alarme pedido no chat · avaliado neste aparelho', pedido: true };
    }).filter(Boolean);
  }

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
  var QUADRO = { 'Telemetria': 1, 'Navegação agora': 1, 'Horímetros': 1, 'Autonomia e consumo': 1 };
  QUADRO['Alarmes pedidos'] = 1;   // (F12: a leitura dos alarmes pedidos é do quadro: a ficha de emergência não a leva)
  function emerg(a) { return !!a && typeof a === 'object' && (EMERG[a.key] === 1 || (a.key === 'faqEquip' && a.emerg === true)); }   // (o cartão EM-01…09 do FAQ também: sem quadro, sem hora, encerra o contexto)
  function casas(c) { var d = D.campos && D.campos[c]; return d && typeof d.casas === 'number' ? d.casas : 0; }
  function vivo() { var i = CONG.inst; return i && VIVAS[i.fonte] === 1 && i.q && i.txt ? i : null; }   // o instante com quadro vivo (replay ou coletor)
  // O sinal «+» colado a «55» e a mais um dígito («+551» rpm) é o prefixo de telefone da regex PESSOAIS do §3 (`\+55\s?\d`): só nesse caso um espaço fino separa o sinal do número (+ 551),
  // que a fala lê igual («mais 551») e a regex deixa passar. Todos os outros valores seguem o molde do contrato (+644, +0,5, −0,5).
  function sinal(x, c) { var A = window.CapitaoAgora, v = A.fmt.arred(x, c), n = A.fmt.nb(Math.abs(v), c); return (v > 0 ? '+' + (/^55\d/.test(n) ? '\u2009' : '') : v < 0 ? '−' : '') + n; }
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
  function agenda() { var ex = execVisivel(); return (D.agenda || []).filter(function (t) { return !ex[t.id]; }).sort(function (a, b) { return (dnDe(a) - dnDe(b)) || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0); }); }
  function atrasadas() { return agenda().filter(function (t) { return atrasadaN(dnDe(t)); }); }
  function tarefa(id) { return (D.agenda || []).filter(function (t) { return t.id === id; })[0] || null; }
  // «executada em 03/11 às 00:38» (a troca, a limpeza, a revisão, a inspeção) ou «executado em …» (o teste, o anodo): o gênero é o do título da tarefa; sem Executado, null
  function execTxt(t) {
    var f = t && execVisivel()[t.id];
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
  // «quanto falta para a troca de óleo?»: a 1ª linha, a falada, diz o quanto falta (as horas do instante e a data, o que vier antes) ou que a tarefa já foi executada, com a hora; a tarefa sem horas diz só o prazo
  function linhaFalta(t, nome) {
    if (!t) return '';
    var i = vivo(), fim = ' — ' + (i ? i.hora : 'leitura de ' + (SNAP.quando || '')) + '.', ex = execTxt(t), n = dnDe(t);
    if (ex) return cap1(nome) + ' foi ' + ex + fim;
    if (t.horas && typeof faltam(t) === 'number') return 'Faltam ' + nb(faltam(t)) + ' h para ' + nome + ' (limite de ' + mil(t.horas.limite) + ' h)' + (t.vence ? ' ou até ' + t.vence + ', o que vier antes' : '') + fim;
    return isNaN(n) ? '' : cap1(nome) + ': ' + prazoTxt(t) + fim;
  }
  // 1ª letra minúscula no meio da frase, menos a sigla («AIS (classe B)» não vira «aIS»)
  function min1(s) { s = String(s || ''); return /^[A-ZÀ-Ý]{2}/.test(s) ? s : s.charAt(0).toLowerCase() + s.slice(1); }

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
    if (almPedidoLite(q) && !almSinalEstado(q)) return 0;   // F12: «me avise se a pressão do óleo cair abaixo de 2 bar» CONFIGURA um alarme, não relata queda (o relato, com «está», «caiu», «agora», «acendeu», «baixa», «oscilando»…, segue em 1)
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
  // Infinitivo NO COMEÇO da frase (F17; «registrar no diário de bordo que hoje eu fiz o update…», dito na conversa por voz, caía na leitura do diário): com «no diário» vale seguido de «que», «:»/«—» ou do
  // conteúdo; sem «no diário», só com «que» ou «:»/«—» («registrar que a bomba foi testada», «anotar: troca do filtro») — «registrar no Google Agenda», «anotar na agenda…» e «registrar o alarme»
  // seguem nas rotas deles. gravar/lançar só com «no diário». Não vale: pergunta («Registrar no diário é obrigatório?»), conteúdo que começa por verbo de ligação, palavra de pergunta ou avaliação
  // («registrar no diário como faz»), nem «é» logo no começo. → 0 = não é pedido · 1 = pedido com o texto · 2 = pedido sem o texto («registrar no diário», «… que» cortado pela pausa da voz).
  var REG_INF = /^[\s"“”«»]*(?:(?:ok|sim|capit[aã]o|ent[aã]o|agora)[\s,;:.!—–-]+)*(registrar|anotar|gravar|lan[cç]ar)((?:\s+(?:isso|aqui|a[ií]|l[aá]))*)(\s+(?:no|em)\s+(?:o\s+)?di[aá]rio(?:\s+de\s+bordo)?)?(?:\s+(?:isso|aqui|a[ií]|l[aá]))*(?:\s*([:—–-]|,)|\s+(que)(?=\s|$)|(?=\s|$))\s*([\s\S]*)$/;
  var REG_INF_NAO = /^(?:e|eh|era|foi|sera|seria|serve|servia|funciona|adianta|vale|ajuda|demora|leva|precisa|deve|devo|pode|posso|podemos|tem|da|fica|faz|nao|so|como|onde|quando|qual|quais|quanto|quem|porque|por|pra|para|pelo|pela|tambem|ainda|sempre|direito|certo|errado|chato|facil|dificil|obrigatorio|importante|necessario|o que|oque)(?=\s|$)/;
  function infinitivoInicio(qRaw) {
    var s = String(qRaw || '').slice(0, 2000).toLowerCase().replace(/\s+/g, ' ').trim(), m = REG_INF.exec(s), verbo, diario, sep, resto;
    if (!m || /\?\s*$/.test(s)) return 0;
    verbo = norm(m[1]); diario = !!m[3]; sep = m[4] || m[5] || ''; resto = m[6].replace(/[\s.!…]+$/, '').trim();
    if (!diario && (/^(?:gravar|lancar)$/.test(verbo) || !sep || sep === ',')) return 0;   // «gravar um vídeo», «lançar a âncora», «registrar no Google Agenda»
    if (!resto) return 2;
    if ((!sep || sep === ',') && (REG_INF_NAO.test(norm(resto)) || /^(?:\S+\s+){0,3}é(?:\s|$)/.test(resto))) return 0;
    return 1;
  }
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
      if (/r$/.test(verbo) && !cortesia) { if (inicio && infinitivoInicio(raw)) return true; continue; } // "Registrar no diário é obrigatório?", "Vamos registrar…" (o infinitivo no começo vale: F17)
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
  // Pedido SEM o texto (F17): «registrar no diário que…» cortado pela pausa da voz, «anote no diário:», «registrar no diário». O app pergunta o que registrar e grava a PRÓXIMA frase (ESPERA_REG, 2 min); o
  // atalho e o «registre no diário» sozinho (imperativo) seguem gravando o resumo da telemetria. A espera vale uma vez: qualquer fala seguinte a consome, e só a que é o texto do registro é gravada.
  // A nota que sobra do comando só com palavras de ligação («registre no diário o», «anote que o», «registre no diário o que»: o ditado cortado no meio da frase) também PEDE o texto: nunca vira a linha «O» ou «O que».
  var REG_CORTA = ' o a os as um uma de do da dos das no na em ao que ';
  function notaCortada(nota) { var ws = norm(nota).replace(/[^a-z0-9]+/g, ' ').trim().split(' '); return ws.length > 0 && ws.length <= 3 && ws.every(function (w) { return REG_CORTA.indexOf(' ' + w + ' ') !== -1; }); }
  function pedeTexto(q) {
    var s = String(q || '').trim(), nota;
    if (!s) return false;
    nota = notaDoUsuario(s);
    if (nota) return notaCortada(nota);
    return infinitivoInicio(s) === 2 || /(?:^|\s)que[\s.…]*$|[:—–-][\s.…]*$/i.test(s);
  }
  var ESPERA_REG = null, ESPERA_VALE = 120e3;
  // cancelar, recusar e ADIAR («deixa quieto», «agora não», «depois eu falo», «deixa eu pensar», «um momento», «espera», «não sei»): a espera acaba e nada é gravado («Certo — nada registrado no diário.»)
  var CANCELA_REG = /^ (?:(?:nao|ok|nada) )?(?:cancela|cancelar|cancele|cancelado|esquece|esqueca|deixa|deixa pra la|deixa para la|nada|nao|nao precisa|nenhum|nenhuma|desisto|deixa quieto|deixa quieta|deixa isso|agora nao|nao agora|nao quero|depois|mais tarde|depois eu (?:falo|digo|conto|registro|anoto)|nada (?:a|para|pra) registrar|deixa pra depois|deixa para depois|deixa eu pensar|um momento|so um momento|um instante|so um instante|espera|espere|aguarda|aguarde|perai|pera ai|calma|nao sei|sei la) $/;
  // o reconhecimento («tá bom», «ok», «valeu», «entendi», «pode ser», «hã», «hum»): nunca vira o texto de um registro nem confirma uma proposta
  var ACK = /^ (?:sim|nao|ok|okay|obrigad[oa]|valeu|beleza|show|entendi|certo|perfeito|blz|tchau|ate mais|ta bom|ta certo|ta otimo|tudo bem|tranquilo|combinado|fechado|isso|isso mesmo|pode ser|talvez|ha|ah|eh|hum|hmm|aham|uhum|ata|uai)(?: (?:entendi|obrigad[oa]|valeu|brigad[oa]|capitao))* $/;
  // A fala depois de «o que devo registrar?»: vira o texto do registro (rota diario), salvo cancelar (relatoCancela, com ctx.espera), pergunta, reconhecimento, outro pedido de registro, emergência (que segue o SOS,
  // com os passos) ou o botão de uma proposta (a rota dele). null = segue a rota normal. A espera é consumida em toda chamada.
  // Aquilo que a fala depois do «o que devo registrar?» NÃO é: a que não fala do barco (falaDeBordo: o controle da conversa — «nova conversa», «parar», «silêncio» —, a despedida, «estou ouvindo», o volume, «tô pensando aqui»,
  // «tanto faz», «foi engano»), o pedido ao app («mostre a telemetria», «quero ver os documentos», «fica de olho no diesel») e a que não diz nada (menos de 2 palavras de conteúdo: «oi», «bom dia», «quero», «vamos»,
  // «autonomia»). O pedido de dado CURTO sem fato («telemetria agora», «nível dos tanques», «próximas manutenções», «previsão do tempo») também é do app; o curto com verbo de fato, número ou sem rota de dado («limpeza do
  // casco») é a nota, e a frase maior que fala do barco é sempre a nota («o gerador foi ligado às sete…»).
  var PEDIDO_REG = /^ (?:(?:por favor|entao|agora|capitao|me|nos|pode|poderia) )*(?:mostr[ae]r?|mostra|abr[ae]|abrir|ver|veja|list[ae]r?|diz|diga|fal[ae]r?|mand[ae]r?|envi[ae]r?|quero ver|queria ver|quero saber|gostaria de ver|gostaria de saber|preciso saber|checar|confira|conferir|verifique|verificar|consulte|consultar|calcule|calcular|ative|ativar|ligue|chame|chamar|inicie|iniciar|volte|voltar|leia|ler|repita|repetir|repete|resuma|resumir|d[ae] uma olhad\w*|ve(?= (?:o|a|os|as|isso|ai) )|fica de olho|fique de olho|me avis[ae]|avis[ae]|me lembr[ae]|lembr[ae]|toca|toque|liga|deslig[ae]|abaix[ae]|aument[ae]|cham[ae]|explic(?:a|ue|ar)|ensin(?:a|e|ar)|ajud(?:a|e|ar))(?= )/;
  var REG_FUNC = ' a o as os um uma uns umas de do da dos das no na nos nas em ao aos pelo pela por para pra com sem e ou que se eu me meu minha ele ela voce vc la ai aqui ja so mais muito bem nao sim ta eh vou vai ser pode posso isso isto esse essa agora hoje depois antes ainda mesmo tambem entao oi ola opa capitao ia tudo como ha ah hum hmm aham uhum ata uai ne ok okay valeu obrigado obrigada brigado ';
  // Evidência de que a fala É nota (revisão 2 da P3F): fala do barco ou da viagem — número, palavra de bordo (peça, equipamento do cadastro, lugar, manobra, combustível, tempo no mar) ou verbo de «nós» no passado
  // («chegamos», «saímos», «fundeamos»). Sem isso («tô pensando aqui», «tanto faz», «foi engano», «volto daqui a pouco») a fala é conversa: segue a rota dela e nada é gravado — o diário só cresce, e a linha errada não sai.
  var BORDO_REG = new RegExp(' (?:' + ['motor\\w*', 'gerador\\w*', 'casco', 'conves', 'proa', 'popa', 'boreste', 'bombordo', 'bb', 'be', 'porao', 'bomba\\w*', 'filtro\\w*', 'oleo', 'diesel', 'combustivel', 'tanque\\w*', 'bateria\\w*', 'ancora\\w*', 'guincho', 'helice\\w*', 'leme', 'rotor\\w*',
    'impeller', 'anodo\\w*', 'zinco\\w*', 'marina', 'pier', 'barra', 'enseada', 'baia', 'ilha', 'fundeio', 'fundead\\w*', 'atracad\\w*', 'atracacao', 'saida', 'chegada', 'partida', 'abasteci\\w*', 'manutencao', 'revisao', 'vistoria', 'inspecao', 'limpeza', 'lavagem', 'polimento', 'pintura', 'reparo', 'conserto',
    'troca', 'trocad\\w*', 'instalacao', 'instalad\\w*', 'documento\\w*', 'licenca', 'seguro', 'horimetro\\w*', 'litros', 'milhas', 'rpm', 'pressao', 'temperatura', 'arrefecimento', 'alarme\\w*', 'vazamento\\w*', 'cabine', 'convidad\\w*', 'tripulac\\w*', 'passageir\\w*', 'pessoas', 'equipe', 'tecnico\\w*',
    'estaleiro', 'mecanico\\w*', 'agua', 'vento\\w*', 'mar', 'ondas?', 'mare', 'chuva', 'neblina', 'previsao', 'rota', 'destino', 'travessia', 'passeio', 'navegacao', 'velocidade', 'cabos?', 'corrente', 'defensas?', 'inversor', 'painel', 'display', 'sensor\\w*', 'sonda', 'gps', 'antena', 'fusivel\\w*', 'disjuntor\\w*',
    'valvula\\w*', 'mangueira\\w*', 'geladeira', 'fogao', 'banheiro', 'luz', 'luzes', 'lampada\\w*', 'vela', 'climatizacao', 'condicionado', 'estabilizador', 'plotter', 'radar', 'vhf', 'radio', 'epirb', 'colete\\w*', 'extintor\\w*', 'salvatagem', 'piloto', 'dessalinizador',
    'novidade\\w*', 'visibilidade', 'barco', 'lancha', 'bote', 'tender', 'jet', 'ski', 'toldo', 'flybridge', 'escada', 'corrimao', 'parafuso\\w*', 'piso', 'timao', 'bussola', 'tv', 'televisao', 'freezer', 'churrasqueira', 'gelo', 'mantimentos', 'comida', 'bebidas', 'cozinheira', 'fiscal', 'capitania',
    'marinha', 'cliente\\w*', 'visita\\w*', 'lixo', 'golfinho\\w*', 'peixe\\w*', 'pescaria', 'mergulho', 'almoco', 'jantar', 'churrasco', 'festa', 'amigos', 'familia'].join('|') + ')(?= )');
  var NOS_PASSADO = / (?!estamos|podemos|devemos|queremos|precisamos|gostamos|sabemos|achamos|pensamos|vamos|temos|vemos|somos)[a-z]{2,}(?:amos|emos|imos)(?= )/;
  // o verbo no passado de quem conta o que houve («choveu bastante durante a noite», «a TV da sala quebrou», «cheguei às oito e saí às cinco»): 1ª ou 3ª pessoa, numa frase de 4 palavras ou mais; a fala que só conversa
  // («estou vendo aqui», «ainda estou vendo o que aconteceu», «eu mudei de ideia agora», «não entendi o que você disse») não vale
  var PASSADO_REG = / (?!(?:estou|falou|errei|aconteceu|mudei|pensei|entendi)(?= ))[a-z]{3,}(?:ou|eu|iu|ei|aram|eram|iram)(?= )/;
  function falaDeBordo(n) {
    var voc, ws, i;
    ws = n.trim().split(/\s+/);
    if (/\d/.test(n) || BORDO_REG.test(n) || NOS_PASSADO.test(n) || (ws.length >= 4 && PASSADO_REG.test(n))) return true;
    voc = vocabEquip();
    for (i = 0; i < ws.length; i++) if (voc[ws[i]]) return true;   // (nome, fabricante, modelo ou palavra do cadastro: «Garmin atualizado»)
    return false;
  }
  // A fala que CONVERSA com o app em vez de contar o que houve (revisão 3 da P3F): a dúvida, a pergunta, o pedido de ajuda, o «quero saber / conversar / pensar», o «para mim» (a ordem: «liga o gerador para mim»). O plano de
  // bordo («vou falar com o técnico amanhã», «vamos conferir o óleo») e o pedido a terceiros («pedimos ajuda ao mecânico») são nota. Junto do pedido ao app do começo da fala (PEDIDO_REG: mostre, liga, explica, ajuda…).
  var CONVERSA_REG = / (?:(?:tenho|tinha|tem|estou com|to com|com|so|apenas|outra) (?:uma |umas |a )?(?:duvidas?|perguntas?)|(?:duvidas?|perguntas?|questao|questoes) (?:sobre|do|da|de|no|na|com|a respeito|para|pra)|(?:preciso|precisamos|precisava|quero|queria|gostaria(?: de)?|posso|podemos|poderia) (?:te |lhe |so )?(?:de )?(?:ajuda|ajudar|saber|entender|conversar|perguntar|pensar|explicar)|(?:quero|queria|gostaria de|vamos|podemos) (?:falar|conversar) (?:sobre|do|da|de|um pouco)|nao (?:entendi|compreendi|ouvi|escutei)|(?:para|pra) mim)(?= )/;
  // «sem ocorrências», «nenhuma ocorrência a relatar», «sem avarias hoje»: a nota clássica de diário, de uma palavra só de conteúdo
  var NOTA_VAZIA = /^ (?:sem|nenhuma|nenhum|nao (?:houve|teve)) (?:nenhuma? )?(?:ocorrencias?|intercorrencias?|incidentes?|anomalias?|avarias?)(?: (?:a|para|pra) (?:relatar|registrar|declarar|reportar))?(?: (?:hoje|no dia|durante o dia|ate agora|na viagem|na travessia|na saida|no periodo))* $/;
  function textoDeRegistro(raw, n) {
    var ws = n.trim().split(/\s+/), conteudo = ws.filter(function (w) { return REG_FUNC.indexOf(' ' + w + ' ') === -1; }).length, fato = RELATO_FATO.test(n.replace(/ (?:que|quem)(?: [a-z]+){1,3}(?= )/g, ' '));
    if (NOTA_VAZIA.test(n)) return true;
    if (PEDIDO_REG.test(n) || CONVERSA_REG.test(n) || !falaDeBordo(n)) return false;
    if (SEGUE_E.test(n) && !fato && !/\d/.test(n)) return false;   // «e o motor de boreste», «e o gerador?»: a continuação de uma pergunta, não a nota («e o gerador foi ligado às sete» é nota)
    if (fato && ws.length >= 2) return true;
    return conteudo >= 2 && (/\d/.test(n) || ws.length > 3 || route(raw) === 'fallback');
  }
  // A fala SOBRE o registro, não o texto dele (revisão 2 da P3F): a recusa («não precisa registrar», «melhor não registrar», «não vou registrar nada», «nem precisa anotar»), o «já está no diário» («isso já está no diário»,
  // «já registrei»), a promessa ou o adiamento de quem fala («amanhã eu registro», «depois eu anoto», «a gente vê isso depois», «vou anotar mais tarde», «preciso ver uma coisa», «deixa eu ver») e a ordem de esperar ou
  // deixar («espera um pouco aí que eu já falo», «peraí que…», «deixa pra mais tarde isso»). Cancela a espera: nada é gravado («Certo — nada registrado no diário.»). Os verbos são o infinitivo, o imperativo e a 1ª pessoa
  // (registrar, registre, registro): «o sensor não registrou pressão» e «não precisa trocar o filtro ainda» são nota. O verbo de ver, pensar, lembrar, checar e conferir só vale no fim da fala ou antes de «isso», «uma coisa»,
  // «depois»…; «vou conferir o nível do óleo amanhã» é nota. «Espera de duas horas na marina» também (a ordem de esperar não leva «de»).
  var REG_FORMAS = '(?:registr(?:ar|e|a|o)|anot(?:ar|e|a|o)|grav(?:ar|e|a|o)|lanc(?:ar|e|a|o)|escrev(?:er|a|e|o))';
  var REG_META_FORTE = '(?:' + REG_FORMAS + '|fal(?:ar|o|amos|aremos)|diz(?:er|emos)|dig(?:o|amos)|cont(?:ar|o|amos)|avis(?:ar|o|amos)|volt(?:ar|o|amos)|mand(?:ar|o|amos))';
  var REG_META_FRACO = '(?:ve|vejo|vemos|ver|pens(?:ar|o|amos)|lembr(?:ar|o|amos)|cheq(?:uei|uemos|ar|o)|confer(?:ir|o|imos)|olh(?:ar|o|amos))(?= (?:isso|isto|uma coisa|um negocio|depois|aqui|ai|la|direito|primeiro|melhor|com calma|mais tarde|amanha|um pouco|so um)|$)';
  var REG_META = [
    new RegExp('(?:^| )(?:nao|nunca|jamais|nem|melhor nao|sem)(?: [a-z]+){0,3} ' + REG_FORMAS + '(?= |$)'),
    / ja (?:registr\w*|anot\w*|grav\w*|lanc\w*|escrev\w*)(?= |$)| ja (?:esta|foi|ta|tem|existe|consta|fica)(?: [a-z]+){0,3} (?:no diario|registrad\w*|anotad\w*|gravad\w*|lancad\w*|escrit\w*)(?= |$)/,
    new RegExp('(?:^| )(?:eu|a gente|nos|gente)(?: [a-z]+){0,3} (?:' + REG_META_FORTE + '|' + REG_META_FRACO + ')(?= |$)'),
    new RegExp('(?:^| )(?:vou|vamos|preciso|precisa|precisamos|tenho que|temos que|quero|queria|deixa eu|deixe eu|me deixa|deixa a gente)(?: [a-z]+){0,2} (?:' + REG_META_FORTE + '|' + REG_META_FRACO + ')(?= |$)'),
    /^ (?:(?:ahn|ahm|hm+|hum+|ei|opa|olha|bom|bem|entao|ta) )*(?:(?:espera|espere|esperar|aguarda|aguarde|aguardar)(?= (?:um|uns|so|ai|a|que|por favor|ate|pouco|momento|minuto|segundo|instante)| $)|perai|pera ai|calma|segura ai|deixa|deixe)(?= )/,
    /^ (?:por enquanto |agora |no momento |ate agora )?nada(?: (?:por enquanto|por agora|agora|disso|mais|no momento|obrigado|obrigada|nao))* $/,   // «nada por enquanto», «por enquanto nada», «nada disso» (e não «nada a relatar», que é nota)
    /^ (?:acho |eu acho )?melhor (?:deixar|esquecer|nao|parar|cancelar|ficar|esperar)(?= )/,
    /^ (?:(?:ainda|eu|sinceramente|pois) )*(?:nao sei|nao tenho ideia|nao lembro|nao me lembro|esqueci)(?: [a-z]+){0,5} $/,
    /^ (?:(?:ah|bom|entao|olha|ops|eh|nao) )*(?:mudei de ideia|pensei melhor|esquece|esqueca|esquecer|deixei pra la|deixa pra la)(?= )/
  ];
  function metaRegistro(n) { return REG_META.some(function (r) { return r.test(n); }); }
  function esperaRegistro(q, ctx) {
    var e = ESPERA_REG, raw, n;
    ESPERA_REG = null;
    if (!e || Date.now() - e.t > ESPERA_VALE || (ctx && (ctx.id || ctx.commit === false || ctx.faq))) return null;
    raw = String(q || '').trim(); n = pad(raw);
    if (!raw || querRegistrar(raw, n)) return null;
    if (CANCELA_REG.test(n) || metaRegistro(n)) return 'relatoCancela';
    if (/\?\s*$/.test(raw) || PERGUNTA.test(n) || ACK.test(n)) return null;
    if (emergencia(n) || oleo(n) === 1 || socorroImplicito(n) || cabecaEmerg(n)) return null;
    if (NAO_ESPERA[route(raw)] === 1) return null;
    if (textoDeRegistro(raw, n)) return 'diario';
    // A promessa da pergunta («a próxima frase é gravada») nunca fica no silêncio (revisão 3 da P3F): a fala que não é nota, nem pedido ao app, nem pergunta, e que a rota nenhuma responde (cairia no «Isso não está nas
    // fontes…» e na IA como se fosse uma consulta), recebe a frase local «Não registrei isso». O pedido, a dúvida e a continuação «e …» seguem a rota deles (e a IA, se for o caso).
    if (!PEDIDO_REG.test(n) && !CONVERSA_REG.test(n) && !SEGUE_E.test(n) && route(raw) === 'fallback') return 'relatoNaoGravou';
    return null;
  }
  // as rotas de ação e de emergência: a fala que cai nelas, depois do «o que devo registrar?», segue a rota (não vira o texto do registro)
  // a confirmação falada do registro (F17): «Registrado no diário de bordo.» e, se a nota é de emergência ou de pressão de óleo, a instrução de segurança (a fala não leva só a primeira linha)
  function falaRegistro(grava, alerta, pressao) {
    if (!grava) return 'Pedido vindo de link não grava no diário.';
    return 'Registrado no diário de bordo.' + (alerta ? ' Se a emergência é agora, abra o SOS.' : '') + (pressao ? ' Se a pressão de óleo está baixa agora, ' + min1((P.oleo && P.oleo[0]) || 'reduza para marcha lenta') + ' e siga os passos na tela.' : '');
  }
  // ——— O relato no chat vira PROPOSTA de registro (F16; Avanti 1.17.2) ———
  // A frase que CONTA um fato do barco — afirmação com verbo de fato (passado, «está …ndo», «não liga», «será necessário»), com 8 palavras ou mais, sem «?», sem palavra de pergunta nem pedido ao app, e sem
  // perigo — é relato: a resposta de sempre ganha uma PROPOSTA (um ticket k diario, origem relato, aberto) com os botões Registrar no diário / Não registrar (e O que verificar?, se conta um defeito); só o
  // «registrar» (ou o botão) grava, e é 1 linha. Pergunta, pedido, perigo (deriva, água, fogo, pessoa ferida, alarme, mar piorando), emergência e óleo NUNCA recebem a proposta: seguem a rota deles. O chat só
  // grava com comando explícito: a proposta não grava nada.
  var RELATO_FATO = new RegExp(' (?:' + [
    'fez|fizeram|fizemos|teve|tiveram|tivemos|houve|deu|deram|veio|vieram|viemos|trouxe|trouxeram|disse|disseram|foi|foram|fomos|puseram',
    '[a-z]{2,}(?:ou|aram|eram|iram|eu|iu)',   // passado: instalou, trocaram, desligou, apareceu, caiu, sumiu
    '[a-z]{3,}(?:amos|emos|imos)',   // 1ª do plural: chegamos, abastecemos, saímos (os modais — podemos, devemos… — ficam no RELATO_NAO)
    '(?:esta|estao|estava|estavam|ta|tava|tao|fica|ficou|ficam|ficaram|continua|continuam|segue|seguem|anda) [a-z]+ndo',   // está interferindo, continua vazando
    'nao (?:liga|ligou|funciona|funcionou|parte|partiu|carrega|carregou|conecta|conectou|responde|respondeu|sobe|desce|aparece|apareceu|acende|acendeu|segura|pega|pegou|abre|fecha)',
    'sem (?:sinal|comunicacao|conexao|internet|energia|leitura|resposta|carga)',
    '(?:sera|foi|vai ser|seria) (?:necessari[oa]|precis[oa])|vai precisar|vamos precisar|vai ter que|teremos que|precisara|precisarao',
    '(?:vem|vira|virao|vai vir|vao vir|chega|chegara|vai chegar) (?:amanha|hoje|segunda|terca|quarta|quinta|sexta|sabado|domingo|dia|as|na proxima|semana que vem)'
  ].join('|') + ')(?= )');
  // Pergunta ou pedido em qualquer ponto da frase («…, o que pode ser», «isso é normal», «me diga…», «então abre o checklist») e começo de pergunta ou imperativo ao app: não é relato. Voz não tem «?»: a
  // pergunta ditada com a marca no fim («… é grave», «… tem solução», «… pode ser a bateria») também sai.
  var RELATO_NAO = / (?:o que|oque|por que|qual|quais|quanto|quanta|quantos|quantas|quem|sera que|como (?:faco|faz|fazer|resolv\w*|consert\w*|arrum\w*|proced\w*|devo|posso|ligo|deslig\w*|configur\w*|ajust\w*|foi|foram|esta|estao|ficou|anda)|onde (?:fica|esta|estao|tem|acho|encontro)|duvida|me (?:diga|diz|fala|fale|mostra|mostre|explica|explique|ajuda|ajude|manda|mande|envia|envie|passa|passe|lembra|lembre|avisa|avise|informa|informe)|(?:voce|vc) (?:pode|poderia|consegue|sabe|acha|tem)|(?:quero|queria|gostaria|preciso|precisava|precisamos|querendo|queremos) (?:de )?(?:saber|entender)|saber (?:se|quando|onde|como|o que|qual)|pensando em|planejando|pretend\w*|sabe (?:se|quando|onde|como)|alguem sabe|nao sei (?:se|quando|onde|como)|e possivel|podemos|devemos|queremos|gostariamos|poderiamos|deveriamos|posso|devo|pode me|poderia|(?:isso )?(?:e|eh|seria) (?:o |um |uma )?(?:normal|grave|perigoso|seguro|comum|ruim|serio|problema)|faz sentido|tem (?:algum|alguma|solucao|conserto|jeito|como|problema|risco)|pode ser|isso (?:pode|e|eh|vai|tem)|pode (?:danificar|estragar|prejudicar|causar|dar problema)|preocup\w*|quando (?:mesmo|precisa|devo|vence|vai|sera|tem que|e a proxima)|(?:feit[oa]|trocad[oa]|foi) quando|em que (?:dia|data|mes|hora|ano)|expli(?:ca|que|car)|como se|como (?!sempre|combinado|de costume|previsto|planejado|o |a |os |as |um |uma )[a-z]+(?:o|ar|er|ir|amos|emos|imos)|acho que|acredito que|parece que|(?:queria|quero|gostaria|gostariamos) (?:o|a|os|as|um|uma|ver|que|de)|(?:preciso|precisamos|precisa|precisam) (?:de )?[a-z]+r|ou (?!(?:um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez|\d))[a-z0-9]+|(?:da|de) (?:pra|para)|isso da|vale a pena|(?:entao|agora|depois|por favor) (?:abre|abra|ativa|ative|mostra|mostre|liga|ligue|desliga|desligue|registra|registre|cria|crie|marca|marque|avisa|avise|manda|mande|confere|confira|verifica|verifique|calcula|calcule)) /;
  var RELATO_PEDIDO = /^ (?:(?:bom dia|boa tarde|boa noite|oi|ola|capitao|ok|entao|agora|e|por favor) )*(?:onde|quem|qual|quais|quanto|quanta|quantos|quantas|o que|oque|que|por que|porque|pq|cade|sera|voce|voces|vc|como|quando (?:e|foi|foram|sera|vence|venceu|vai|devo|posso|fica|abre|fecha|chega|tem|teve|aconteceu|acontece|ocorreu|comecou)|consumo|historico|ultim[oa]s?|tudo que|tudo o que|lista|resumo|relatorio|status|situacao|media|total|(?:mostr|abr|list|calcul|expli|verifi|confir|consult|procur|busc|chec|analis|compar|recomend|avali|ajud|cri|envi|mand|lig|cham|pergunt|lembr|avis|apag|remov|cancel|deslig|escrev|ger|prepar|planej|mont|inform)(?:a|e|ue|que|ca|ma|me|ar|ir|er)|abre|abra|diz|diga|dize|veja|ve|cheque|faca|faz|faze|sugira|desfaz|desfaca|exclua|exclui|resuma|traduza|tem|ha|existe|posso|pode|podemos|devo|preciso|precisamos|quero|queria|gostaria|vamos|vou)(?= )/;
  // Perigo agora (deriva, pedras, garrando, leme, queda, água subindo, porão, EPIRB, alarme, código no display): segue a rota de antes (SOS, passos, FAQ, IA) — a proposta de registro não pode tomar o lugar dos
  // passos. Defeito «agora» também (o passo a passo vem antes).
  var RELATO_PERIGO = / (?:deriv\w*|pedra\w*|garr\w*|sem governo|sem motor\w*|sem propuls\w*|sem controle|leme|cabeca|escorreg\w*|tropec\w*|caiu (?:d[ao]|n[ao]|entre|ao|pela|pelo)|queda|subindo|dando conta|porao|epirb|alarm\w*|apit\w*|sirene|buzzer|codigo|spn|fmi|fumac\w*|cheiro|faisca|choque|socorr\w*|doendo|dor|dores|sangue|sangr\w*|queimadura|desmai\w*|vomit\w*|engasg\w*|engoliu|tossindo|afog\w*|picad[oa]s?|agua-viva|agua viva|torceu|torci|fratur\w*|primeiros socorros|hospital|ambulancia|samu|medico|bombeiro\w*|rajada\w*|temporal|tempestade|mar grosso|mar agitado|ressaca|fundo|raso|rasa|profundidade|encalh\w*|neblina|cerracao|rota de colisao|em direcao (?:a|ao|as|aos|à|da|do)|(?:vindo|indo) (?:na|em) (?:nossa )?direcao|nao responde\w* (?:no|ao|pelo) radio|soltou|batendo (?:contra|no|na|nos|nas)|entrou (?:muita )?agua|entrando agua|agua (?:do mar |salgada |doce |preta )?(?:(?:esta|estava|estao|continua|continuam|vai|vem|comecou a|passou a) )?(?:entrando|subindo|vazando|invadindo|jorrando|brotando|entrar|subir)|agua (?:do mar |salgada )?(?:subiu|invadiu|entrou)|(?:nivel|altura) d[ae] agua (?:[a-z]+ ){0,5}(?:subiu|subindo|aument\w*|cresc\w*)|perdemos (?:[a-z]+ ){0,2}(?:governo|motores|motor|leme|controle|ancora|propulsao)|perdemos de vista|sendo (?:levad|arrastad|empurrad)\w*|(?:levando|arrastando|empurrando) (?:o barco|a gente|nos)|(?:para|contra) a costa|contra o pier|ventando|ventania|(?:abre|abra|mostra|mostre|chama|chame|liga|ligue|avisa|avise|manda|mande|marca|marque|agenda|agende|cria|crie|coloca|coloque|fecha|feche|atualiza|atualize|gera|gere) (?:o|a|os|as|pro|pra|para|com|me|um|uma)|me liga|virou|capot\w*|emborc\w*|nao responde (?:ao|o|a) (?:timao|joystick|leme|acelerador|manete|comando)|(?:acelerador|manete|timao|comando) (?:\w+ )?trav\w*|adern\w*|inclinando|enchendo|alagando|monoxido|detector|superficie|mergulhador|(?:os )?(?:dois|2|ambos os) motores (?:\w+ )?(?:falh|par|apag|morr|deslig|caiu|cair)\w*|motores (?:falharam|pararam|apagaram|morreram)|sem os motores|(?:foi|foram) (?:parar )?(?:na agua|no mar|pro mar|para o mar)|pulou (?:na agua|no mar)|sumiu|sumiram|nao (?:consegue|conseguia|consigo) respirar|alergic\w*|inchad\w*|esmag\w*|vaz\w* (?:de )?(?:diesel|combustivel|gas|oleo)|cheiro de gas|chama|chamas|entrando muita agua|alagou|desacordad\w*|inconsc\w*)(?= )/;
  // Pessoa em risco («o Lucas queimou a mão no escapamento», «a convidada torceu o tornozelo», «uma pessoa caiu entre o barco e o píer»): os passos / a IA, nunca só o «registrar?»
  var RELATO_PESSOA = / (?:pessoa|pessoas|crianca|criancas|convidad[oa]s?|marinheiro|tripulante|alguem|passageir[oa]s?|lucas|mulher|homem|senhor|senhora|menino|menina|filho|filha|ele|ela|eu|se)(?: [a-z]+){0,4} (?:caiu|cairam|cortou|cortaram|queimou|queimaram|quebrou|bateu|machuc\w*|feriu|ferid[oa]|passou mal|passando mal|mordid[oa]|bateram|escaldou)(?= )/;
  // Tempo piorando («o vento aumentou muito», «as ondas estão batendo forte»): segue para o clima e a IA; «vento fraco» é relato
  var RELATO_TEMPO = / (?:vento|ventos|onda|ondas|chuva|chovendo|barometro|tempo|mar)(?: [a-z]+){0,3} (?:forte|fortes|aument\w*|subindo|caiu|caindo|fechou|batendo|grande|grandes|alta|altas|piorou|piorando)(?= )/;
  var RELATO_FIM = / (?:sera|ne|nao e|certo|confere|nao|e agora|e ai|e entao|faz sentido|(?:e|eh) (?:o |um )?normal|(?:ainda )?(?:esta|ta) na garantia|tem garantia|cobre a garantia|da garantia|sera (?!necessari|precis)[a-z]+(?: [a-z]+){0,2}) $/;   // marca de pergunta no fim da frase ditada («… interferindo no GPS, será»)
  var RELATO_AGORA = / (?:agora|neste momento|nesse momento|agorinha)(?= )/, RELATO_DEFEITO = /(?:esquent|superaquec|apagou|apagaram|apagando|deslig(?:ou|a|ando|aram|ando) sozinh|parou de|parando de|vazand|vazament|nao liga|nao parte|nao funciona|falh|desarm|quebrou|quebrad[oa]|quebraram|trav(?:ou|ando|ado))/;
  var RELATO_ANOMALIA = / (?:nao (?:liga|ligou|funciona|funcionou|parte|carrega|conecta|responde|transmite|mostra|gela|esta (?:ligando|funcionando|transmitindo|mostrando|carregando|gelando|pegando))|sem (?:sinal|comunicacao|resposta|carga)|pingand\w*|gotej\w*|vibr\w*|barulho|ruido|estranh\w*|desengat\w*|caiu para|subiu para|marcando menos|ecos falsos|gastando mais|interfer\w*|erro)(?= )/;
  function relatoDiario(qRaw, q) {
    var raw = String(qRaw || '');
    if (EM_SOS || /\?/.test(raw) || raw.length > 1000) return false;
    q = q || pad(raw);
    if (q.trim().split(/\s+/).length < 8) return false;
    if (RELATO_PEDIDO.test(q) || RELATO_NAO.test(q) || RELATO_FIM.test(q) || RELATO_PERIGO.test(q) || RELATO_PESSOA.test(q) || RELATO_TEMPO.test(q) || (RELATO_AGORA.test(q) && RELATO_DEFEITO.test(q))) return false;
    if (emergencia(q) || oleo(q) === 1 || socorroImplicito(q) || cabecaEmerg(q) || SOBRE.test(q) || querRegistrar(raw, q) || foraBarcoPergunta(q) || TERMOS.DINHEIRO.test(raw)) return false;   // (dinheiro e o que é de fora do barco não viram proposta de registro)
    // verbo de fato fora de oração com «que» («consumo das saídas que fizemos em setembro», «anotações que o Lucas fez»: pedido de dado, não relato)
    return RELATO_FATO.test(q.replace(/ (?:que|quem)(?: [a-z]+){1,3}(?= )/g, ' '));
  }
  function notaRelato(raw) { var s = limpaT(raw, 1000).replace(/^[\s,;:.!—–-]+/, ''); return s.charAt(0).toUpperCase() + s.slice(1); }
  // categoria do relato (a mais grave vale): segurança, motores, combustível, manutenção, navegação, documentos; o defeito contado é de equipamento; o resto, Diário
  var CAT_RELATO = [['Segurança', /colete|extintor|epirb|seafire|salvatagem|sinalizador|balsa|man overboard/], ['Motores', /motor|motores|cummins|rpm|escapamento|turbo|helice/], ['Combustível', /diesel|combustivel|abasteci|tanque/],
    ['Manutenção', /troca|trocamos|trocou|trocaram|manutenc|revis|limpeza|limpamos|limpou|filtro|rotor|anodo|inspec/], ['Navegação', /saimos|saiu|chegamos|chegou|navegamos|fundeamos|atracamos|travessia|largamos|amarramos/], ['Documentos', /documento|licenca|vistoria|laudo|seguro do barco/]];
  function categoriaRelato(n, defeito) {
    var t = ' ' + n + ' ', k, sys = null;
    for (k = 0; k < CAT_RELATO.length; k++) if (CAT_RELATO[k][1].test(t)) { sys = CAT_RELATO[k][0]; break; }
    return sys || (defeito ? 'Equipamentos' : 'Diário');
  }
  // O que fala a proposta: só quando o relato é claramente passado (ontem, hoje cedo, dia 3…), sem urgência nem defeito, ela é falada e vai no alto; no resto vai no fim, calada, e só vale «registrar» ou o botão
  var RELATO_PASSADO = / (?:ontem|anteontem|hoje|semana passada|mes passado|feriado passado|ultimo feriado|fim de semana passado|ultimo fim de semana|de manha|pela manha|a tarde|a noite|mais cedo|ultima saida|dia \d+|ha \d+ (?:dias?|semanas?|meses))(?= )/;
  var RELATO_AGORA_PRES = / (?:agora|neste momento|nesse momento|estamos|ainda|(?:esta|estao|ta|tao|continua|continuam) [a-z]+ndo)(?= )/;
  var RELATO_URGENTE = / (?:sozinh[oa]s?|pres[oa]s?|trav\w*|sem (?:manobra|direcao|governo|instrumentos?|energia|luz|forca|comando|controle|leme|visibilidade|radar|freio)|nao (?:reduz|volta|desliga|obedece|segura|para|engata|corta|responde)|rodando|circulos?|solt[oa]s?|apag\w*|deslig\w*|dispar\w*|acelerou|arrebent\w*|romp\w*|estour\w*|jorr\w*|navegando|navegacao|travessia|no meio|canal|manobra|quase|bat(?:eu|emos|eram|endo|ida|ido)|enrosc\w*|abord\w*|inspecao|vapor|derret\w*|ferv\w*|estufad\w*)(?= )/;
  var RELATO_RISCO = / (?:agua|gas|fogo|chama\w*|fumac\w*|pessoa|crianca|convidad\w*|marinheiro|tripulante|passageir\w*|alguem|ferid\w*|machuc\w*)(?= )/;
  var RELATO_SEGURO = { porao: 1, canal16: 1, ancora: 1, seguro: 1, clima: 1, mare: 1, alarmes: 1, oleoLeitura: 1, epirb: 1, posicao: 1, navegacao: 1 };
  function relatoFalado(n, key, sys, defeito) { return !RELATO_SEGURO[key] && !RELATO_RISCO.test(n) && !RELATO_URGENTE.test(n) && !defeito && !/^(?:Segurança|Anomalia)$/.test(sys || '') && RELATO_PASSADO.test(n) && !RELATO_AGORA_PRES.test(n); }
  // as rotas que nunca recebem a proposta: emergência, o próprio registro, o diagnóstico, a saudação, o que não é do barco e a frase padrão sobre os dados
  var SEM_RELATO = { sos: 1, oleo: 1, canal16: 1, epirb: 1, seafire: 1, salvatagem: 1, mmsi: 1, diario: 1, diarioPede: 1, relatoRegistra: 1, relatoCancela: 1, saudacao: 1, diagnostico: 1, sobreDados: 1, foraBarco: 1, relatoVerifica: 1 };
  // P3G: o alarme pedido, a agenda (e o confirmar/recusar/desfazer) e o que o app faz não recebem a proposta do relato
  ['alarmePedido', 'alarmeConfirma', 'alarmeCancela', 'alarmesLista', 'alarmeApaga', 'agendar', 'ticketConfirma', 'ticketRecusa', 'ticketDesfaz', 'capacidades'].forEach(function (k) { SEM_RELATO[k] = 1; });
  var RELATO_VALE = 10 * 60e3, REL_VER = 'O que verificar e qual pode ser a causa: ';
  // A proposta do relato (um ticket aberto, k diario, origem relato); o mesmo texto ainda aberto não duplica. REL guarda a que espera o «registrar» (10 min): o botão leva o id do ticket (5 s: ALVO_REL)
  var REL = null, ALVO_REL = null;
  function relatoPendente() {
    var t;
    if (!REL || Date.now() >= REL.ate) return null;
    t = achaTicket(ticketsCru(), REL.id);
    return t && t.estado === 'aberto' && t.origem === 'relato' ? REL : null;
  }
  // o ticket que o botão tocado aponta (vale 5 s) ou, sem ele, o que espera. O botão de uma proposta que já foi decidida (registrada, descartada ou desfeita noutro canto) NÃO cai na que espera: seria a
  // proposta errada. Devolve { decidido, estado } e quem chama diz que nada mudou.
  function relatoAlvo() {
    var a = ALVO_REL, t;
    ALVO_REL = null;
    if (a && Date.now() - a.t < 5000) {
      t = achaTicket(ticketsCru(), a.id);
      if (t && t.estado === 'aberto' && t.origem === 'relato') return { id: t.id };
      return { decidido: true, estado: t ? t.estado : null };
    }
    return relatoPendente();
  }
  function relatoDecidido(rp, abrir) {
    var t = rp.estado === 'aceito' ? 'Esse relato já está registrado no diário; nada mudou.' : rp.estado === 'recusado' ? 'Esse relato já foi descartado; nada mudou.' : 'Esse relato não está mais esperando; nada mudou.';
    return { text: t, src: 'Fonte: diário de bordo do app', actions: abrir, fala: t };
  }
  function propoeRelato(nota, sys, defeito, q) {
    var abertos = ticketsAbertos().filter(function (x) { return x.origem === 'relato' && norm(x.texto) === norm(nota); }), t = abertos[0];
    if (!t) t = addTicket({ k: 'diario', origem: 'relato', texto: nota, prop: { sys: sys, tone: tomDe(sys), pend: defeito ? true : undefined, q0: limpaT(q, 200) } });
    if (!t) return null;
    REL = { id: t.id, ate: Date.now() + RELATO_VALE, n: CONV.n, q: limpaT(q, 500) };   // (q: a pergunta que a abriu, para o conversa() da IA realinhar o «sim» curto)
    return t;
  }
  // A proposta SOMA à resposta de sempre (texto, botões e, se for passado e sem urgência, a fala). Não age em pedido de link (commit false), de chip (id) nem de FAQ; nunca na emergência.
  function acrescentaRelato(a, key, q, ctx) {
    var n, nota, defeito, sys, t, bt, seg, f0, linha;
    if (!a || !q || EM_SOS || SEM_RELATO[key] || emerg(a) || a.seguranca || (ctx && (ctx.commit === false || ctx.id || ctx.faq))) return a;
    n = pad(q);
    if (!relatoDiario(q, n)) return a;
    nota = notaRelato(q); defeito = RELATO_DEFEITO.test(n) || RELATO_ANOMALIA.test(n); sys = categoriaRelato(n, defeito);
    t = propoeRelato(nota, sys, defeito, q); if (!t) return a;
    linha = 'Isto também parece um relato para o diário de bordo — registrar? Toque em Registrar no diário ou diga “registrar”.';
    bt = [{ l: 'Registrar no diário', href: '#capitao-relato-registra-' + t.id }, { l: 'Não registrar', href: '#capitao-relato-cancela-' + t.id }].concat(defeito ? [{ l: 'O que verificar?', href: '#capitao-relato-verifica-' + t.id }] : []);
    seg = !relatoFalado(n, key, sys, defeito); f0 = falaCurta(a);
    a.text = String(a.text || '') + '\n\n' + linha;
    a.actions = seg ? (a.actions || []).concat(bt) : bt.concat(a.actions || []);
    if (!seg) a.fala = f0 + ' Parece um relato para o diário; para registrar, diga registrar.';
    a.relato = { id: t.id, nota: nota, sys: sys, defeito: defeito, linha: linha, botoes: bt, falado: !seg };
    return a;
  }
  // O que o botão da proposta pergunta ao chat (a tela manda esta pergunta como se fosse digitada): registrar, não registrar, ou o que verificar (o relato vai à IA). Guarda o alvo por 5 s.
  function perguntaDoBotao(href) {
    var m = /#capitao-relato-(registra|cancela|verifica)-(t[A-Za-z0-9_-]{2,60})$/.exec(String(href || '')), t, b = /#capitao-prop-(confirma|recusa|desfaz)-(\d{1,9})$/.exec(String(href || ''));
    if (b) { ALVO_PROP = { seq: +b[2], t: Date.now() }; return b[1] === 'confirma' ? 'confirmar a proposta' : b[1] === 'recusa' ? 'recusar a proposta' : 'desfazer a proposta'; }   // (F15/F12: o botão leva o número da proposta; o de uma antiga não age na nova)
    if (!m) return '';
    ALVO_REL = { id: m[2], t: Date.now() };
    if (m[1] === 'registra') return 'registrar o relato';
    if (m[1] === 'cancela') return 'não registrar o relato';
    t = achaTicket(ticketsCru(), m[2]);
    return t ? (REL_VER + semCoord(t.texto.replace(/[\s.!]+$/, ''))).slice(0, 500) : '';   // (a pergunta vai à IA: sem coordenadas, PROMPT §2.8; o semCoord corta antes do limite)
  }
  // A pergunta pronta do botão «O que verificar?» (REL_VER + o texto do relato): é a rota `relatoVerifica`, não as rotas por palavra («gerador», «climatização»…), que só repetiriam a resposta pronta que o
  // relato já recebeu. Digitada à mão com perigo («… tem fogo no motor») a emergência vem antes (route()).
  function relatoVerificaPergunta(q) { var v = pad(REL_VER); return q.indexOf(v) === 0 && q.length > v.length; }
  if (!EM_SOS && !window.__capitaoBotoesRelato) {   // o toque num botão da proposta vira a pergunta digitada (a tela escuta 'capitao-chat-pergunta'); o link não navega
    window.__capitaoBotoesRelato = true;
    try { document.addEventListener('click', function (e) {
      var a = e.target && e.target.closest ? e.target.closest('a[href*="#capitao-relato-"], a[href*="#capitao-prop-"]') : null, q = a ? perguntaDoBotao(a.getAttribute('href')) : '';
      if (!q) return;
      e.preventDefault();
      try { window.dispatchEvent(new CustomEvent('capitao-chat-pergunta', { detail: { q: q } })); } catch (x) {}
    }); } catch (e) {}
  }
  // A resposta à proposta: «registrar» / «sim, registra» / «não registrar» / «cancelar». «ok», «certo» e «isso» são reconhecimento, não confirmação; o «sim» e o «não» curtos só valem logo depois da proposta
  // (REL.n = a conversa dela, sem outra pergunta no meio); fora disso só o pedido explícito (registrar, anotar, relato, diário) ou o botão.
  var RELATO_SIM = /^( (sim|ok|okay|pode|isso|claro|confirm\w*|registr\w*|anot\w*|grav\w*|salv\w*|no|o|a|diario|de|bordo|relato|por|favor|esse|este|mesmo|certo|ai|aqui|ta|bom|beleza|valeu|show|positivo|perfeito|obrigad[oa]|blz|fechado))+ $/, RELATO_SIM_TEM = / (sim|pode|claro|confirm\w*|registr\w*|anot\w*|grav\w*|salv\w*) /;
  var RELATO_NAO_RESP = /^( (nao|cancel\w*|deixa|pra|la|o|a|relato|registr\w*|precisa|agora|obrigado|esquece|melhor|nao quero|no|diario))+ $/, RELATO_NAO_TEM = / (nao|cancel\w*|deixa|esquece) /;
  function respostaRelato(q, rp) {
    var explicito = / (registr\w*|anot\w*|grav\w*|salv\w*|relato|diario) /.test(q), logo = rp && rp.n === CONV.n && !CONV.pergunta;
    if (!explicito && !logo) return null;
    if (RELATO_NAO_RESP.test(q) && RELATO_NAO_TEM.test(q)) return 'nao';
    if (RELATO_SIM.test(q) && RELATO_SIM_TEM.test(q)) return 'sim';
    return null;
  }
  // «registra agora», «registra pra mim», «anota isso», «pode lançar no diário»: com a proposta esperando, é a confirmação dela; «registra também que o gerador ficou ligado» soma o complemento ao relato;
  // «registra com a data de ontem» anota a data. Sobra com perigo, pessoa, emergência ou fato próprio (um registro novo) não confirma: segue a rota dela.
  var RELATO_CONF = /^ (?:(?:sim|ok|pode|por favor|entao|capitao|ta|beleza|claro|manda|vai|so|e) )*(?:registr(?:a|e|ar)|anot(?:a|e|ar)|lan[cç](?:a|e|ar)|grav(?:a|e|ar)|salv(?:a|e|ar))(?= )/;
  var RELATO_SOBRA = /^(?: (?:agora|ai|isso|isto|tudo|ja|entao|logo|por favor|pra mim|para mim|no|o|a|ele|ela|diario|de|bordo|com|foto|video|imagem|anexo|junto|essa|esse|esta|este|relato|mesmo|tambem|sim|ok|obrigad[oa]|valeu|segue|vai|pode|que|eu|disse|falei|contei|escrevi|relatei|dito|falado|contado|mencionado|acima|anterior|ultim[oa]|mensagem|problema|ocorrencia|informacao|fato|caso|registro|texto|assunto))* $/;
  var RELATO_COMPL = /^ (?:(?:e )?(?:tambem|alem disso)|e que)(?= )/, RELATO_DATA = /^ com (?:a )?data (?:de |do |da )?(?:ontem|anteontem|hoje|\d|dia|segunda|terca|quarta|quinta|sexta|sabado|domingo)/;
  function sobraRelato(qRaw, q) {
    var raw = String(qRaw || ''), resto, sobra, w, x;
    if (!RELATO_CONF.test(q) || /\?/.test(raw) || pedeTexto(raw)) return null;
    resto = raw.replace(/^[\s\S]*?(?:registr|anot|lan[cç]|grav|salv)[a-zà-ÿ]*/i, '').replace(/^[\s,;:.!—–-]*(?:(?:no|em|o) )?di[aá]rio(?: de bordo)?(?=[\s,;:.!—–-]|$)/i, '').replace(/^[\s,;:.!—–-]*(?:por favor|a[ií])(?=[\s,;:.!—–-]|$)/i, '');
    sobra = pad(resto); w = sobra.trim() ? sobra.trim().split(/\s+/).length : 0;
    if (!w || (RELATO_SOBRA.test(sobra) && !/\d/.test(sobra))) return { extra: '' };
    if (emergencia(sobra) || oleo(sobra) === 1 || socorroImplicito(sobra) || RELATO_PERIGO.test(sobra) || RELATO_PESSOA.test(sobra)) return null;
    if (RELATO_DATA.test(sobra) && w <= 9) return { extra: '(ocorrido ' + limpaT(resto.replace(/^[\s,;:.!—–-]*com\s+(?:a\s+)?data\s+(?:de\s+|do\s+|da\s+)?/i, ''), 60).replace(/[\s.]+$/, '') + ')' };
    if (RELATO_COMPL.test(sobra)) { x = limpaT(resto.replace(/^[\s,;:.!—–-]*(?:(?:e|também|tambem|além disso|alem disso|que)\s+)*/i, ''), 600); return { extra: x ? notaRelato(x) : '' }; }
    return null;
  }
  function comExtra(nota, sb) { var x = sb && sb.extra; return !x ? nota : (nota.replace(/[\s.]+$/, '') + (x.charAt(0) === '(' ? ' ' + x : '. ' + x)).slice(0, 600); }
  // os botões da proposta («registrar o relato», «não registrar o relato») valem sempre; com a proposta esperando, também o «registrar», o «sim», o «não», o «registra agora»… (a emergência e o óleo vêm antes)
  var RELATO_BTN = /^ (?:(?:sim|ok|pode|por favor) )*(?:registrar|registra|registre|anotar|anota|anote) (?:o |esse |este |um )?relato $/, RELATO_BTN_NAO = /^ (?:(?:nao|ok|por favor) )?(?:nao registrar|nao registra|nao registre|nao anotar|nao anote|cancelar|cancela|cancele) (?:o |esse |este |um )?relato $/;
  // O ADIAMENTO («registra depois», «anota mais tarde», «registrar amanhã», «depois eu registro», «registra por enquanto não», «agora não»): o oposto de registrar. Nada é gravado e a proposta que espera FICA (não é recusada);
  // «registra mais tarde» e «anota depois» não gravam o resumo da telemetria. Só vale com o verbo de registrar na fala (ou, sem ele, com a proposta esperando e um adiamento que não seja «amanhã» solto): «registra o
  // filtro de amanhã» e «anote que o rotor será trocado depois» são nota (têm conteúdo próprio). A pergunta («registro depois?») não é adiamento.
  var ADIA_FIM = '(?:depois|mais tarde|amanha(?: cedo| de manha| a tarde| a noite| de noite)?|outra hora|outro dia|em outro momento|num outro momento|por enquanto|ainda nao|agora nao|nao agora|daqui a pouco|mais pra frente|mais para frente|quando (?:der|puder|eu puder|chegar|a gente chegar)|na volta|na chegada|logo mais)';
  var ADIA_SO = new RegExp('^ (?:(?:sim|ok|ta|certo|entao|por favor|pode ser|isso|tudo|mas|eu|a gente|nos|ai|vou|vamos|posso|pode|preciso|quero|queria) )*(?:(?:registr\\w*|anot\\w*|grav\\w*|lanc\\w*) )?(?:(?:isso|tudo|aqui|ai|pra mim|para mim|(?:o |esse |este )?relato|o registro|o ocorrido) )*(?:(?:no|em) (?:o )?diario(?: de bordo)? )?(?:(?:isso|tudo|aqui|ai|pra mim|para mim|por favor) )*' + ADIA_FIM + '(?: (?:mesmo|por favor|obrigado|obrigada|nao|isso|tudo|eu|a gente|nos|ai|registro|registrar|registramos|anoto|anotar|anotamos|ta|ok|certo|ta bom|valeu))* $');
  var COMANDO_REG = /^ (?:(?:sim|ok|por favor|pode|poderia|entao|capitao) )*(?:registr|anot|grav|lanc)\w* /;
  var ADIA_SOLTO = / (?:depois|mais tarde|agora nao|nao agora|por enquanto|ainda nao|outra hora|daqui a pouco) /;
  function adiaRegistro(qRaw, q) {
    var raw = String(qRaw || ''), n = q || pad(raw);
    if (/\?/.test(raw) || raw.length > 200 || !ADIA_SO.test(n) || emergencia(n) || oleo(n) === 1) return false;
    if (querRegistrar(raw, n) || COMANDO_REG.test(n)) return true;   // o comando «registra depois» (que registraria o resumo) e «registrar amanhã»
    return !!relatoPendente() && (ADIA_SOLTO.test(n) || / (?:registr|anot|grav|lanc)\w* /.test(n));   // com a proposta esperando: «depois registro», «vou registrar depois», «agora não»
  }
  function relatoRota(qRaw, q) {
    var rp, r;
    if (RELATO_BTN_NAO.test(q)) return 'relatoCancela';
    if (RELATO_BTN.test(q)) return 'relatoRegistra';
    if (adiaRegistro(qRaw, q)) return 'relatoCancela';
    rp = relatoPendente(); if (!rp) return null;
    r = respostaRelato(q, rp);
    if (r === 'nao') return 'relatoCancela';
    if (r === 'sim' || sobraRelato(qRaw, q)) return 'relatoRegistra';
    return null;
  }
  var NAO_ESPERA = { sos: 1, oleo: 1, canal16: 1, epirb: 1, seafire: 1, salvatagem: 1, mmsi: 1, diagnostico: 1, saudacao: 1, diarioPede: 1, relatoRegistra: 1, relatoCancela: 1, relatoVerifica: 1 };
  ['alarmePedido', 'alarmeConfirma', 'alarmeCancela', 'alarmesLista', 'alarmeApaga', 'agendar', 'ticketConfirma', 'ticketRecusa', 'ticketDesfaz', 'capacidades'].forEach(function (k) { NAO_ESPERA[k] = 1; });   // (P3G: a espera do registro não engole o pedido de alarme, a agenda nem o «o que você pode fazer?»)

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

  // ——— Tendências (F11; CONTRATO §1.13, §1.23) ———
  // Achados por regra fixa, calculados neste aparelho (nenhuma IA, nenhuma rede): o histórico gerado do cruzeiro (D.historico.cruzeiro, 60 dias), a volta de hoje (a média da fase
  // de cruzeiro do replay), os contadores de horas (calc.faltam do instante) e o próprio instante (o arrefecimento agora contra a faixa e a tendência dos últimos 30 s). Os achados do
  // histórico e dos contadores são os mesmos em 12:01:00 e em 12:01:45; o do instante é o que muda. Cada achado leva a fonte. Nunca grava, nunca fala sozinho, nunca abre tela.
  var PRED_PESO = { acao: 3, atencao: 2, ok: 1 };
  var PRED_ROTULO = { acao: 'AÇÃO', atencao: 'ATENÇÃO', ok: 'ESTÁVEL' };
  var PRED_ORDEM = ['arref_agora', 'arref_cruzeiro', 'horas', 'oleo_cruzeiro', 'baterias'];   // no mesmo nível, o do instante vem primeiro
  // a fonte do histórico: com a simulação, o texto único das telas («telemetria»: nunca «coletor NMEA» com o quadro do replay); sem ela, a do próprio dado gerado
  function histFonte() { return sim() ? 'histórico de telemetria de bordo' : (D.historico && D.historico.fonte) || 'histórico'; }
  function mediaDe(xs) { var s = 0; xs.forEach(function (x) { s += x; }); return xs.length ? s / xs.length : NaN; }
  // a série de médias de cruzeiro por dia de bordo (do mais antigo até ontem), já em unidade de medida; null se falta ou não é número
  function cruzeiroSerie(campo) {
    var s = D.historico && D.historico.cruzeiro && D.historico.cruzeiro[campo], v;
    if (EM_SOS || !s || !Array.isArray(s.d) || s.d.length < 14 || !(s.escala > 0)) return null;
    v = s.d.map(function (x) { return x / s.escala; });
    return v.every(function (x) { return typeof x === 'number' && isFinite(x); }) ? v : null;
  }
  // a média do campo na fase de cruzeiro da volta de hoje (D.replay.fases), pelo mesmo replay das telas; null sem replay
  function cruzeiroHoje(campos) {
    var R = window.CapitaoReplay, fs = D.replay && D.replay.fases, f = null, o = {}, n = 0, t, q;
    if (EM_SOS || !sim() || !R || typeof R.quadro !== 'function' || !Array.isArray(fs)) return null;
    fs.forEach(function (x) { if (x && x.nome === 'cruzeiro') f = x; });
    if (!f) return null;
    try {
      campos.forEach(function (c) { o[c] = 0; });
      for (t = f.ini; t < f.fim; t++) {
        q = R.quadro(t);
        if (!q) return null;
        campos.forEach(function (c) { o[c] += q[c]; });
        n++;
      }
    } catch (e) { return null; }
    if (!n) return null;
    campos.forEach(function (c) { o[c] /= n; });
    return campos.every(function (c) { return isFinite(o[c]); }) ? o : null;
  }
  // a faixa normal do campo, do D.replay.limites («até 88 °C», «de 24,4 a 29,4 V»); '' se o campo não tem
  function faixaNormal(campo) {
    var L = limitesDe(campo), n = L && L.normal, un = L && L.un ? ' ' + L.un : '', d = decimais;
    if (!n) return '';
    if (typeof n.de === 'number' && typeof n.ate === 'number') return 'de ' + nb(n.de, d(n.de)) + ' a ' + nb(n.ate, d(n.ate)) + un;
    if (typeof n.ate === 'number') return 'até ' + nb(n.ate, d(n.ate)) + un;
    if (typeof n.de === 'number') return 'a partir de ' + nb(n.de, d(n.de)) + un;
    return '';
  }
  // arrefecimento em cruzeiro: a diferença entre os dois motores (hoje, pela volta) e como ela andou nos 60 dias do histórico
  function achadoArrefCruzeiro() {
    var bb = cruzeiroSerie('motor_bb_arref_c'), be = cruzeiroSerie('motor_be_arref_c'), hoje, dif, ini, fim, rumo, tend, quente, frio, n, abs;
    if (!bb || !be || bb.length !== be.length) return null;
    hoje = cruzeiroHoje(['motor_bb_arref_c', 'motor_be_arref_c']); n = bb.length;
    dif = bb.map(function (x, k) { return be[k] - x; });
    ini = mediaDe(dif.slice(0, 7)); fim = hoje ? hoje.motor_be_arref_c - hoje.motor_bb_arref_c : mediaDe(dif.slice(-7));
    abs = Math.abs(fim); rumo = abs - Math.abs(ini);
    tend = rumo >= 0.5 ? ', subindo há ' + n + ' dias' : rumo <= -0.5 ? ', caindo há ' + n + ' dias' : ', estável há ' + n + ' dias';
    quente = fim >= 0 ? 'BE' : 'BB'; frio = fim >= 0 ? 'BB' : 'BE';
    if (abs < 1) return { id: 'arref_cruzeiro', sistema: 'Motores', nivel: 'ok', titulo: 'Arrefecimento em cruzeiro', texto: 'Os dois motores esfriam igual em cruzeiro: diferença de ' + nb(abs, 1) + ' °C' + tend + '.', fonte: histFonte() + ' · cruzeiro dos últimos ' + n + ' dias' + (hoje ? ' e a volta de hoje' : '') };
    return { id: 'arref_cruzeiro', sistema: 'Motores', nivel: abs >= 2 || rumo >= 0.5 ? 'atencao' : 'ok', titulo: 'Arrefecimento em cruzeiro', texto: 'Motor ' + quente + ' ' + nb(abs, 1) + ' °C acima do ' + frio + ' em cruzeiro' + tend + '.', fonte: histFonte() + ' · cruzeiro dos últimos ' + n + ' dias' + (hoje ? ' e a volta de hoje' : '') };
  }
  // pressão de óleo em cruzeiro, por motor: estável ou caindo contra a primeira semana do histórico; a faixa normal é a do guia (a partir de 1.000 rpm)
  function achadoOleoCruzeiro() {
    var bb = cruzeiroSerie('motor_bb_oleo_bar'), be = cruzeiroSerie('motor_be_oleo_bar'), hoje, n, queda, vb, ve, mn, L, k, r, abaixo;
    if (!bb || !be) return null;
    hoje = cruzeiroHoje(['motor_bb_oleo_bar', 'motor_be_oleo_bar']); n = bb.length;
    queda = Math.max(mediaDe(bb.slice(0, 7)) - mediaDe(bb.slice(-7)), mediaDe(be.slice(0, 7)) - mediaDe(be.slice(-7)));
    vb = hoje ? hoje.motor_bb_oleo_bar : mediaDe(bb.slice(-7)); ve = hoje ? hoje.motor_be_oleo_bar : mediaDe(be.slice(-7));
    L = limitesDe('motor_bb_oleo_bar'); r = L && L.regimes; mn = null;
    if (r) for (k = 0; k < r.length; k++) if (r[k].rpm_de != null && r[k].normal && typeof r[k].normal.de === 'number') mn = r[k].normal.de;
    abaixo = mn !== null && Math.min(vb, ve) < mn;   // (estável ou não, a pressão abaixo do mínimo normal é ATENÇÃO e o texto diz «abaixo do mínimo normal»: nunca «estável» sem dizer isso)
    return { id: 'oleo_cruzeiro', sistema: 'Motores', nivel: queda >= 0.2 || abaixo ? 'atencao' : 'ok', titulo: 'Pressão de óleo em cruzeiro',
      texto: abaixo ? 'Pressão de óleo em cruzeiro abaixo do mínimo normal de ' + nb(mn, 1) + ' bar: BB ' + nb(vb, 1) + ' bar · BE ' + nb(ve, 1) + ' bar, ' + (queda >= 0.2 ? 'caindo' : 'estável') + ' há ' + n + ' dias.'
        : 'Pressão de óleo em cruzeiro ' + (queda >= 0.2 ? 'caindo' : 'estável') + ' há ' + n + ' dias: BB ' + nb(vb, 1) + ' bar · BE ' + nb(ve, 1) + ' bar' + (mn !== null ? ', com mínimo normal de ' + nb(mn, 1) + ' bar' : '') + '.',
      fonte: histFonte() + ' · cruzeiro dos últimos ' + n + ' dias' + (hoje ? ' e a volta de hoje' : '') + (L && L.fonte ? ' · ' + L.fonte : '') };
  }
  // os três bancos de baterias nos últimos 30 dias (CapitaoReplay.serie): estáveis ou com queda de 0,3 V ou mais
  function achadoBaterias() {
    var R = window.CapitaoReplay, F = window.CapitaoAgora, campos = ['bateria_0_tensao_v', 'bateria_1_tensao_v', 'bateria_2_tensao_v'], rot = ['serviço', 'partida', '12 V'], vistos = [], queda = 0, variacao = 0, i = vivo(), L;
    if (EM_SOS || !sim() || !i || !R || typeof R.serie !== 'function' || !F || !F.fmt) return null;
    try {
      campos.forEach(function (c, k) {
        var s = R.serie(c, '30D', i.ms), v, atual = F.fmt.campo(i.q, c);
        if (!Array.isArray(s) || s.length < 10 || atual === null) throw new Error('serie');
        v = s.map(function (p) { return p.v; });
        queda = Math.max(queda, mediaDe(v.slice(0, 5)) - mediaDe(v.slice(-5)));
        variacao = Math.max(variacao, Math.max.apply(null, v) - Math.min.apply(null, v));
        vistos.push(rot[k] + ' ' + atual + ' V');
      });
    } catch (e) { return null; }
    L = limitesDe('bateria_0_tensao_v');
    return { id: 'baterias', sistema: 'Elétrico', nivel: queda >= 0.3 ? 'atencao' : 'ok', titulo: 'Baterias nos últimos 30 dias',
      texto: queda >= 0.3 ? 'Banco de baterias caiu ' + nb(queda, 1) + ' V nos últimos 30 dias: ' + vistos.join(' · ') + '.' : 'Baterias estáveis nos últimos 30 dias: ' + vistos.join(' · ') + ', com variação de até ' + nb(variacao, 1) + ' V.',
      fonte: histFonte() + ' · 30 dias' + (L && L.fonte ? ' · ' + L.fonte : '') };
  }
  // horas até a troca de óleo dos motores e a revisão do gerador: os contadores do instante (calc.faltam) ou, sem eles, o que a agenda gerada traz
  var HORAS_NOME = { 'motores-oleo': 'a troca de óleo e filtros dos motores', 'gerador-revisao': 'a revisão do gerador' };
  function achadoHoras() {
    var ts = (D.agenda || []).filter(function (t) { return t.horas && typeof t.horas.limite === 'number' && !execVisivel()[t.id]; }), cl = [], menor = Infinity;
    if (EM_SOS || !ts.length) return null;
    ts.forEach(function (t) {
      var f = faltam(t);
      if (typeof f !== 'number' || !isFinite(f)) return;
      menor = Math.min(menor, f);
      cl.push(nb(f, 1) + ' h para ' + (HORAS_NOME[t.id] || 'a ' + min1(t.t)) + ' (limite de ' + mil(t.horas.limite) + ' h)');
    });
    if (!cl.length) return null;
    return { id: 'horas', sistema: 'Manutenção', nivel: menor <= 10 ? 'acao' : menor <= 50 ? 'atencao' : 'ok', titulo: 'Horas até a revisão', texto: 'Faltam ' + cl.join(' e ') + '.', fonte: FT.agenda.replace('Fonte: ', '') + (vivo() ? ' · horímetros: ' + SNAP.fonte : '') };
  }
  // o arrefecimento do motor mais quente AGORA contra a faixa do guia (CapitaoAgora.nivel) e a tendência de 30 s: o único achado que muda de um instante para o outro
  function achadoArrefAgora() {
    var i = vivo(), A = window.CapitaoAgora, q = i && i.q, lado, c, v, n, d, tx, al, desde = '', L;
    if (EM_SOS || !i || !A || !A.fmt || typeof q.motor_be_arref_c !== 'number' || typeof q.motor_bb_arref_c !== 'number') return null;
    lado = q.motor_be_arref_c >= q.motor_bb_arref_c ? 'BE' : 'BB'; c = lado === 'BE' ? 'motor_be_arref_c' : 'motor_bb_arref_c';
    n = A.nivel(c, q); v = campoTxt(i, c);
    if (!n || v === null) return null;
    tx = i.tend && typeof i.tend[c] === 'number' ? '; ' + sinal(i.tend[c], 1) + ' °C nos últimos 30 s' : '';
    L = limitesDe(c);
    if (n.nivel === 'normal') return { id: 'arref_agora', sistema: 'Motores', nivel: 'ok', titulo: 'Arrefecimento agora', texto: 'Arrefecimento do motor ' + lado + ' agora: ' + v + ' °C, dentro da faixa normal (' + faixaNormal(c) + ')' + tx + '.',
      fonte: i.fonteTxt + ' · ' + (L && L.fonte || '') };
    al = (alarmesDetalhe(i) || []).filter(function (a) { return a.campo === c; })[0]; if (al && al.hora) desde = ' desde ' + al.hora;
    d = typeof n.limite === 'number' ? ', ' + (q[c] > n.limite ? 'acima' : 'abaixo') + ' de ' + nb(n.limite, decimais(n.limite)) + ' °C' : '';
    return { id: 'arref_agora', sistema: 'Motores', nivel: n.nivel === 'critico' ? 'acao' : 'atencao', titulo: 'Arrefecimento agora', texto: 'Arrefecimento do motor ' + lado + ' agora: ' + v + ' °C' + d + ' — ' + (n.nivel === 'critico' ? 'CRÍTICO' : 'AVISO') + desde + tx + '.',
      fonte: i.fonteTxt + ' · ' + (L && L.fonte || '') };
  }
  // os achados, do mais grave ao estável (no mesmo nível, PRED_ORDEM); [] sem nenhum dado. Cada chamada refaz (nada fica guardado).
  function preditivaLista() {
    return congela(function () {
      var l = [achadoArrefAgora, achadoArrefCruzeiro, achadoHoras, achadoOleoCruzeiro, achadoBaterias].map(function (f) { try { return f(); } catch (e) { return null; } }).filter(Boolean);
      l.sort(function (a, b) { return (PRED_PESO[b.nivel] - PRED_PESO[a.nivel]) || (PRED_ORDEM.indexOf(a.id) - PRED_ORDEM.indexOf(b.id)); });
      return l.map(function (a) { return Object.assign({ rotulo: PRED_ROTULO[a.nivel] }, a); });
    });
  }
  // A pergunta sobre as tendências («quais as tendências?», «análise preditiva», «tendência do óleo», «as baterias estão perdendo capacidade?»). Como toda rota de leitura calma, só responde a pergunta
  // NEUTRA (lista branca PRED_OK, mais abaixo): o escopo é o dos achados (motores, óleo, arrefecimento, baterias, horas até a revisão, gerador) e a pergunta não leva outro assunto nem palavra de relato.
  // «Tendência do tempo / do mar / da água / da âncora / do rumo / de carga / do Flamengo», o relato («perdendo capacidade de governo», «tem tendência a adernar») e o pedido de socorro, de salvatagem,
  // de EPIRB, de Seafire, de canal 16 ou de MMSI têm palavra fora da lista: seguem a rota deles (a instrução de segurança local, o clima, a maré, o consumo, a âncora, o guia ou a IA) — a trava 10 não
  // depende da posição desta rota na route(). «Perdendo capacidade» só vale com a bateria. «Tendência da pressão» sozinha é a barométrica (fora); com o óleo é a do óleo.
  var PRED_PALAVRAS = ['preditiv', ' tendencia ', ' tendencias ', 'recomendacao da ia', 'recomendacoes da ia'];
  // («tendência de queda / de subida» é o substantivo, a pergunta da tendência; «a temperatura está subindo», «a bateria está caindo» e «queda de tensão» são o relato do sintoma e têm palavra fora da lista: seguem a rota do equipamento, o guia ou a IA)
  var PRED_TENDENCIA_DE = / tendencias? (?:de |a )(?:queda|quedas|subida|subidas) /g;
  function tendenciaPergunta(q) {
    if (cabecaEmerg(q)) return false;   // (a cabeça de emergência é do equipamento, local: guarda única do topo, antes da lista branca)
    return (has(q, PRED_PALAVRAS) || (has(q, ['perdendo capacidade']) && has(q, ['bateria']))) && leitura(q.replace(PRED_TENDENCIA_DE, ' tendencia '), PRED_OK) && !(has(q, ['pressao']) && !has(q, ['oleo']));
  }
  // O achado que a pergunta nomeia sobe para a 1ª linha (a falada): «qual a tendência do óleo?» abre com a pressão de óleo, não com o motor mais quente. Sem assunto, o mais grave.
  var PRED_FOCO = [[[' hora', 'revisao', 'troca', 'gerador'], ['horas']], [['oleo', 'pressao'], ['oleo_cruzeiro']], [['arrefec', 'temperatura', 'esquent'], ['arref_agora', 'arref_cruzeiro']], [['bateria'], ['baterias']]];
  function predFoco(q) {
    var n = pad(q), ids = [];
    PRED_FOCO.forEach(function (f) { if (!ids.length && has(n, f[0])) ids = f[1]; });
    return ids;
  }

  // ——— Peças e estoque (F22; CONTRATO §1.20, §1.25) ———
  // A base gerada (D.pecas: nome, quantidade, mínimo, local e as tarefas da agenda que usam; sem código de fabricante, sem R$ e sem peça de salvatagem) NUNCA se muta. O que este aparelho faz
  // fica em capitao.pecas.v1 = { novas: [peças cadastradas aqui], movs: [{ id, dq, iso, who, sim? }] }: a quantidade de uma peça é a da base (ou a da cadastrada) mais a soma dos
  // movimentos dela. O «−1 USADA» é um movimento de −1; o Desfazer é um movimento NOVO que devolve a unidade (só se ninguém mexeu na quantidade depois). O registro só cresce: nenhuma linha
  // se apaga nem se reescreve. Só um toque ou um comando explícito grava (as telas chamam usaPeca, desfazUsoPeca, ajustaPeca e addPeca); o chat só lê. Linha gravada com a simulação leva `sim: true`.
  var K_PECAS = 'capitao.pecas.v1';
  function selaSim() { return sim() ? { sim: true } : {}; }
  function pecasEstado() {   // JSON de outra forma vale como vazio (nunca lança)
    var v = read(K_PECAS, null), o = v && typeof v === 'object' && !Array.isArray(v) ? v : {};
    return {
      novas: Array.isArray(o.novas) ? o.novas.filter(function (x) { return x && typeof x.id === 'string' && x.id && typeof x.n === 'string' && x.n; }) : [],
      movs: Array.isArray(o.movs) ? o.movs.filter(function (m) { return m && typeof m.id === 'string' && typeof m.dq === 'number' && isFinite(m.dq); }) : []
    };
  }
  function nivelPeca(q, mn) { return q <= 0 ? 'zero' : mn > 0 && q <= mn ? 'baixa' : 'ok'; }
  function stPeca(q, mn) { return q <= 0 ? 'ZERADA' : mn > 0 && q < mn ? 'ABAIXO DO MÍNIMO' : mn > 0 && q === mn ? 'NO MÍNIMO' : 'OK'; }
  // As peças COMO AS RESPOSTAS LEEM: a base mais as cadastradas aqui, com a quantidade já somada. `ctx.semSim` (a ficha com simulacao false) deixa de fora o que tem `sim: true`. No SOS, nada.
  function pecasLista(ctx) {
    var est, soma = {}, semSim = !!(ctx && ctx.semSim), base;
    if (EM_SOS) return [];
    est = pecasEstado(); base = Array.isArray(D.pecas) ? D.pecas : [];
    est.movs.forEach(function (m) { if (!(semSim && m.sim === true)) soma[m.id] = (soma[m.id] || 0) + m.dq; });
    return base.map(function (x) { return Object.assign({}, x, { base: true }); }).concat(est.novas.filter(function (x) { return !(semSim && x.sim === true); }).map(function (x) { return Object.assign({}, x, { base: false }); }))
      .filter(function (x) { return x && typeof x.n === 'string' && x.n; })
      .map(function (x) {
        var q = Math.max(0, Math.round((typeof x.qtd === 'number' && isFinite(x.qtd) ? x.qtd : 0) + (soma[x.id] || 0))), mn = typeof x.min === 'number' && isFinite(x.min) ? x.min : 0;
        return { id: x.id, n: x.n, qtd: q, min: mn, local: x.local || '', obs: x.obs || '', tarefas: Array.isArray(x.tarefas) ? x.tarefas.slice() : [], base: x.base, nivel: nivelPeca(q, mn), st: stPeca(q, mn) };
      });
  }
  // O estoque na ficha da IA (bloco «## Peças»): só o que a IA precisa para não inventar — o total e as peças zeradas e no mínimo ou abaixo, com a quantidade a bordo e o mínimo («que peça acabou?»). Sem peça
  // cadastrada (ou no SOS), sem bloco. `semSim` (simulacao false) deixa de fora o que tem `sim: true`, como a lista.
  function fichaPecas(semSim) {
    var l = pecasLista({ semSim: semSim }), ps = l.filter(function (x) { return x.nivel !== 'ok'; }), z = ps.filter(function (x) { return x.nivel === 'zero'; }).length;
    if (!l.length) return null;
    return { text: l.length + (l.length === 1 ? ' peça cadastrada' : ' peças cadastradas') + (ps.length ? ' — ' + (z ? z + (z === 1 ? ' zerada' : ' zeradas') + (ps.length > z ? ' e ' : '') : '') + (ps.length > z ? (ps.length - z) + ' no mínimo ou abaixo' : '') + ':\n'
      + ps.map(function (x) { return '• ' + x.n + ': ' + x.qtd + ' a bordo' + (x.min > 0 ? ', mínimo ' + x.min : '') + ' — ' + x.st; }).join('\n') : ', todas acima do mínimo.'), src: 'Fonte: estoque de peças a bordo · cadastro do app' };
  }
  function txtPeca(v, max) { return String(v == null ? '' : v).replace(/\s+/g, ' ').trim().slice(0, max); }
  // o inteiro PURO de 0 a 999: o número inteiro, ou o texto de 1 a 3 dígitos (com espaço nas pontas). «1e2», «12abc», «3.7», «1,5», «-1», «0x10», o vazio e o número com fração são recusados (null): o estoque
  // não se grava com um número que a pessoa não escreveu (o <input type=number> aceita «1e2»)
  function intPeca(v) {
    var n = typeof v === 'number' ? v : typeof v === 'string' && /^\d{1,3}$/.test(v.trim()) ? parseInt(v.trim(), 10) : NaN;
    return Number.isInteger(n) && n >= 0 && n <= 999 ? n : null;
  }
  // a quantidade e o mínimo do + PEÇA são opcionais (sem eles, 0); com um valor que não é inteiro puro, o cadastro todo é recusado
  function intPecaOpc(v) { return v == null || (typeof v === 'string' && !v.trim()) ? 0 : intPeca(v); }
  // A GRAVAÇÃO parte do que está guardado, como está (o registro só cresce): nunca do estado filtrado que a leitura devolve. Uma linha que esta versão não entende (quantidade em texto, campo de outra versão,
  // cópia restaurada), uma chave de topo desconhecida e um valor de outra forma (lista, texto, JSON ruim) ficam onde estavam; só a linha nova entra no fim da lista. O que não é objeto fica em `antes`;
  // o campo que não é lista, em `<campo>Antes` (e o campo recomeça lista).
  function pecasCru() {
    var s = null, v;
    try { s = localStorage.getItem(K_PECAS); } catch (e) {}
    if (!s) return {};
    try { v = JSON.parse(s); } catch (e) { return { antes: s }; }
    return v === null || v === undefined ? {} : typeof v === 'object' && !Array.isArray(v) ? v : { antes: v };
  }
  function pecasLinhas(cru, campo) {
    var k = campo + 'Antes';
    if (Array.isArray(cru[campo])) return cru[campo];
    if (cru[campo] !== undefined && cru[campo] !== null) { while (cru[k] !== undefined) k += '_'; cru[k] = cru[campo]; }
    return (cru[campo] = []);
  }
  function pecaMov(id, dq) {   // grava UM movimento novo (iso único: o dados.html soma pelo iso) e devolve a linha
    var cru = pecasCru(), movs = pecasLinhas(cru, 'movs'), t = Date.now(), iso, m;
    do { iso = new Date(t++).toISOString(); } while (movs.some(function (x) { return x && x.iso === iso; }));
    m = Object.assign({ id: id, dq: dq, iso: iso, who: quem() }, selaSim());
    movs.push(m); write(K_PECAS, cru);
    return m;
  }
  // −1 USADA: tira uma do estoque. {id, ant, novo, iso} para o Desfazer; null se a peça não existe ou já está zerada.
  function usaPeca(id) {
    var p = pecasLista().filter(function (x) { return x.id === id; })[0], m;
    if (!p || !(p.qtd > 0)) return null;
    m = pecaMov(id, -1);
    return { id: id, ant: p.qtd, novo: p.qtd - 1, iso: m.iso };
  }
  // Desfazer: devolve a unidade com um movimento NOVO, e só se a quantidade ainda é a que o −1 deixou (ninguém mexeu depois). Devolve a peça, ou null.
  function desfazUsoPeca(u) {
    var p = u && pecasLista().filter(function (x) { return x.id === u.id; })[0];
    if (!p || typeof u.ant !== 'number' || typeof u.novo !== 'number' || p.qtd !== u.novo || u.ant === u.novo) return null;
    pecaMov(u.id, u.ant - u.novo);
    return pecasLista().filter(function (x) { return x.id === u.id; })[0] || null;
  }
  // ajuste da quantidade (o ✎ da tela): um movimento com a diferença; null se a peça não existe ou o número não é inteiro de 0 a 999
  function ajustaPeca(id, qtd) {
    var p = pecasLista().filter(function (x) { return x.id === id; })[0], n = intPeca(qtd);
    if (!p || n === null || n === p.qtd) return null;
    pecaMov(id, n - p.qtd);
    return pecasLista().filter(function (x) { return x.id === id; })[0] || null;
  }
  // + PEÇA: nome (obrigatório), quantas a bordo, mínimo, local, observação e as tarefas da agenda que a usam. Sem código de fabricante nem valor. Devolve a peça cadastrada, ou null.
  function addPeca(c) {
    var n = txtPeca(c && c.n, 80), est, novas, ids = {}, id, ag = {}, item, qtd, mn;
    if (EM_SOS || !n) return null;
    qtd = intPecaOpc(c.qtd); mn = intPecaOpc(c.min);
    if (qtd === null || mn === null) return null;
    est = pecasCru(); novas = pecasLinhas(est, 'novas');
    (D.pecas || []).forEach(function (x) { ids[x.id] = 1; }); novas.forEach(function (x) { if (x && x.id !== undefined) ids[x.id] = 1; }); (D.agenda || []).forEach(function (t) { ag[t.id] = 1; });
    do { id = 'u' + Date.now().toString(36) + Math.random().toString(36).slice(2, 4); } while (ids[id]);
    item = Object.assign({ id: id, n: n, qtd: qtd, min: mn }, c.local ? { local: txtPeca(c.local, 60) } : {}, c.obs ? { obs: txtPeca(c.obs, 200) } : {},
      Array.isArray(c.tarefas) && c.tarefas.filter(function (t) { return ag[t]; }).length ? { tarefas: c.tarefas.filter(function (t) { return ag[t]; }).slice(0, 10) } : {}, { iso: new Date().toISOString(), who: quem() }, selaSim());
    novas.push(item); write(K_PECAS, est);
    return item;
  }
  // as tarefas da agenda que a peça serve, com o prazo de hoje («Troca de óleo e filtros dos motores (D-17 · 20/11)»)
  function tarefasDaPeca(p) { return (p.tarefas || []).map(tarefa).filter(Boolean).map(function (t) { return { id: t.id, n: t.t, prazo: prazoTxt(t) }; }); }
  // a(s) tarefa(s) da agenda que a pergunta cita pelas palavras dela (D.agenda[].palavras: «rotor do gerador», «filtro da climatizacao»)
  function tarefasDaPergunta(q) {
    var n = pad(q);
    return (D.agenda || []).filter(function (t) { return (t.palavras || []).some(function (w) { w = norm(w).trim(); return w && n.indexOf(' ' + w + ' ') !== -1; }); });
  }
  var PECAS_GENERICAS = null;   // (montada na 1ª chamada: o tokens() usa a lista de palavras comuns, definida mais abaixo)
  // as palavras que dizem «estoque» e não nomeiam peça: o que se pergunta (tem, quantas, falta, onde fica, preciso, cadê), o que se fez (usei, gastei) e as de contexto (revisão, viagem, hoje, mais…). O que sobra
  // da pergunta é o NOME que a pessoa deu; nenhuma sobra = a pergunta é «as peças» em geral (a lista inteira, sem dizer que o nome não existe)
  var PECAS_GEN_TXT = 'pecas peca sobressalente sobressalentes estoque bordo barco lancha temos tem tenho tinha quais qual quanto quantas quantos minimo repor reposicao reserva reservas cadastradas cadastrada cadastro lista liste listar precisa precisamos preciso precisar precisando precisarei '
    + 'falta faltam faltando faltou acabando acabou acabaram acabar abaixo zerada zeradas zerou zerado sobra sobram sobrando sobrou restam resta restando onde fica ficam guardamos guardo guardado guardada guardadas guardados guardar cade usei usamos usou usado usada usadas usados uso usar '
    + 'tirei tiramos tirou gastei gastamos gastou algum alguma alguns algumas coisa coisas algo todas todos tudo outra outro outras outros mais menos mesmo ainda favor diga diz mostre mostra fale fala quero queria gostaria saber ver conferir conferencia '
    + 'revisao revisoes manutencao viagem viagens temporada saida chegada semana mes ano dia hoje agora proxima proximo proximas proximos vou vamos devo devemos posso podemos existe existem esta estao estamos sao ser ter haver ha comprar compra compro comprei';
  // (e as flexões dos verbos de estoque, pela raiz: precisa/precisam/precisamos, falta/faltam, repor/reposição, guardamos/guardado, usei/usamos…; e onde a peça fica: caixa, estante, armário)
  var PECAS_GEN_RAIZES = ['precis', 'falt', 'repo', 'reser', 'sobr', 'rest', 'acab', 'zer', 'guard', 'cadast', 'quant', 'usa', 'gast', 'compr', 'cabe', 'valor', 'armari', 'caixa', 'estante', 'tecnic', 'ferrament'];
  function pecasGenerica(w) {
    if (!PECAS_GENERICAS) { PECAS_GENERICAS = {}; tokens(PECAS_GEN_TXT).forEach(function (x) { PECAS_GENERICAS[x] = 1; }); }
    return PECAS_GENERICAS[w] === 1 || PECAS_GEN_RAIZES.some(function (r) { return w.indexOf(r) === 0; });
  }
  // as palavras da pergunta que podem ser o nome de uma peça (sem as de estoque), sem repetir
  function pecasPalavras(q) {
    return tokens(q).filter(function (w, k, a) { return a.indexOf(w) === k && !pecasGenerica(w); });
  }
  // o núcleo do nome da peça: até o primeiro «do/da/dos/das» («Filtro de óleo» do motor, «Rotor (impeller)» da bomba, «Correia» do alternador, «Jogo de anodos» do eixo), sem o que é só qualificador
  // ou comum demais para nomear («óleo», «água», «diesel», «combustível», «jogo», «pré»): «quanto óleo tem a bordo?» é o óleo, não o filtro
  var PECAS_AMBIGUAS = ' oleo agua diesel combustivel gasolina jogo pre ';
  // o singular e o plural casam («fusível»/«fusíveis»: o tokens() deixa «fusivel» e «fusivei»; «canal»/«canais»)
  function radicalPeca(w) { return w.length > 4 ? w.replace(/([aeou])i$/, '$1l') : w; }
  function nucleoPeca(n) {
    return tokens(String(n || '').split(/\s+d[oa]s?\s+/i)[0]).filter(function (w) { return !/^\d+$/.test(w) && PECAS_AMBIGUAS.indexOf(' ' + w + ' ') === -1; }).map(radicalPeca);
  }
  // «tela» sozinha é também a do plotter e a do radar (relato de falha: «zerou a tela do plotter»): só nomeia a peça («Tela do filtro de água salgada…») junto da palavra seguinte do nome
  var PECAS_NUCLEO_FRACO = { tela: 'filtro' };
  // as palavras da pergunta que podem nomear peça (sem as de estoque), no radical de peça, sem a palavra fraca que está sozinha
  function pecasPalavrasPeca(q) {
    var ws = pecasPalavras(q).map(radicalPeca);
    return ws.filter(function (w) { return !PECAS_NUCLEO_FRACO[w] || ws.indexOf(PECAS_NUCLEO_FRACO[w]) !== -1; });
  }
  // a pergunta nomeia uma peça cadastrada pelo núcleo do nome («rotor», «filtros», «anodos», «impellers», «correia», «fusível»)
  function nomeCadastrado(q) {
    var ws = pecasPalavrasPeca(q), l = pecasLista();
    return ws.length > 0 && l.some(function (x) { var nu = nucleoPeca(x.n); return ws.some(function (w) { return nu.indexOf(w) !== -1; }); });
  }
  // O OBJETO do verbo de estoque é a peça: a 1ª palavra depois de «falta», «acabou», «quantos», «tem»… (sem artigo, «de», «estoque», «mais») é o núcleo do nome de uma peça cadastrada. «Falta rotor?» e
  // «quantos filtros temos?» são o estoque; «falta imagem na tela do radar», «acabou a luz da tela», «falta água no rotor» e «faltando fluxo no filtro» são o relato de uma falha (o guia ou a IA), não a lista.
  var PECAS_ARTIGOS = ' o a os as um uma uns umas algum alguma alguns algumas mais outro outra outros outras de do da dos das estoque ';
  function objetoPeca(q, verbos) {
    var ps = q.trim().split(' '), ws = pecasPalavrasPeca(q), l = pecasLista(), k, j, w;
    for (k = 0; k < ps.length; k++) {
      if (verbos.indexOf(ps[k]) === -1) continue;
      for (j = k + 1; j < ps.length && PECAS_ARTIGOS.indexOf(' ' + ps[j] + ' ') !== -1; j++);
      w = j < ps.length ? tokens(ps[j])[0] : '';
      w = w ? radicalPeca(w) : '';
      if (w && ws.indexOf(w) !== -1 && l.some(function (x) { return nucleoPeca(x.n).indexOf(w) !== -1; })) return true;
    }
    return false;
  }
  // as palavras que o app conhece como nome de coisa de bordo (o nome e as palavras dos equipamentos e o nome das peças, no radical de peça), menos as de estoque: o eco do nome só repete palavra daqui
  // (a agenda fica de fora: os títulos dela trazem verbos e qualificadores — «limpeza», «validade conferida» — que não nomeiam coisa)
  function pecasVocabulario() {
    var v = {}, add = function (t) { tokens(t).forEach(function (w) { w = radicalPeca(w); if (/^[a-z]+$/.test(w) && !pecasGenerica(w)) v[w] = 1; }); };
    (D.equipamentos || []).forEach(function (e) { add(e.nome); (e.palavras || []).forEach(add); });
    (D.pecas || []).forEach(function (p) { add(p.n); });
    return v;
  }
  var PECAS_ECO_TERMOS = ['ROTULOS', 'AUTENTICIDADE', 'DINHEIRO', 'PESSOAIS', 'LOCAL_SEGURANCA', 'VAZIOS', 'VISIVEL'];   // (as regex do §3 que valem para texto de bordo, menos o ANEXO)
  // as palavras como a pessoa escreveu, para dizer «Nenhuma peça cadastrada com «guincho» no nome». Só palavra de letras (até 24: nada de número, telefone, preço nem coordenada) que o app conhece como coisa de
  // bordo (pecasVocabulario: «guincho», «radar», «plotter»; nunca «dizer», «atual», «indisponível», um e-mail nem o nome de um fornecedor) e que nenhuma regex do §3 casa; sem nenhuma, a resposta nem diz o nome
  function palavrasEscritas(q, ws) {
    var m = {}, voc = pecasVocabulario(), l;
    String(q || '').split(/[^A-Za-zÀ-ÿ0-9]+/).forEach(function (w) { var t = tokens(w)[0]; t = t && radicalPeca(t); if (t && !m[t]) m[t] = w.toLowerCase(); });
    l = ws.filter(function (t) { return voc[t] === 1; }).map(function (t) { return m[t] || t; }).filter(function (w) {
      return /^[a-zà-ÿ]{1,24}$/.test(w) && !/^(?:simul|fict|demo|invent|hipot|ilustr|exempl|roteir|laco|teste|snapshot)/.test(w) && !PECAS_ECO_TERMOS.some(function (k) { return TERMOS[k].test(w); });
    }).slice(0, 3);
    return l.length && !PECAS_ECO_TERMOS.some(function (k) { return TERMOS[k].test(l.join(' ')); }) ? l : [];
  }
  // as peças que a pergunta nomeia pelo nome («rotor», «filtro de óleo», «anodo», «rotor do gerador»): as que casam MAIS palavras do nome ganham («rotores do gerador» é o rotor do gerador, não o filtro do gerador
  // nem o rotor da bomba); a palavra da pergunta que é o NÚCLEO do nome de alguma peça (a peça: «correia», «rotor», «escova», «filtro») vale 100 e a que não é (o equipamento ou o lugar: «motor», «gerador»,
  // «estabilizador») vale 1: «tem correia sobressalente para o motor?» é a correia, não o filtro do motor nem o rotor dos motores (o «motor» da pergunta não empata com a peça); «quantos filtros temos?» segue
  // os 5 (a «tela do filtro» tem «filtro» no nome). { nome: false } se a pergunta só diz «peças» (a lista inteira); { nome: true, lista: [] } se há nome e nenhuma peça o tem
  function pecasDoNome(q, l) {
    var ws = pecasPalavrasPeca(q), pts, max, nucleos, pw;
    if (!ws.length) return { nome: false, palavras: [], lista: [] };
    nucleos = l.map(function (x) { return nucleoPeca(x.n); });
    pw = ws.filter(function (w) { return nucleos.some(function (nu) { return nu.indexOf(w) !== -1; }); });
    pts = l.map(function (x) {
      var nt = tokens(x.n).map(radicalPeca);
      return ws.reduce(function (soma, w) { return soma + (nt.indexOf(w) === -1 ? 0 : pw.indexOf(w) !== -1 ? 100 : 1); }, 0);
    });
    max = Math.max.apply(null, pts.concat(0));
    return { nome: true, palavras: palavrasEscritas(q, ws), lista: max ? l.filter(function (x, k) { return pts[k] === max; }) : [] };
  }
  // «peças» (plural) e «sobressalente» já são a pergunta do estoque; a forma no singular e «estoque» pedem também um verbo ou número de estoque («tem», «quantas», «falta», «a bordo»…)
  var PECAS_FORTES = [' pecas ', 'sobressalente'];
  var PECAS_FRACAS = [' peca de ', ' peca a bordo', ' peca para ', ' peca pra ', ' uma peca ', ' a peca ', ' qual peca', ' que peca', ' de peca ', ' da peca ', ' sem peca', ' alguma peca ',
    ' peca zerad', ' peca acab', ' peca esgot', ' peca falt', ' peca no minimo', ' peca abaixo'];   // («tem peça zerada?»: a peça no singular sem artigo, com o estado de estoque)
  var PECAS_PEDE = [' a bordo', ' estoque', ' temos ', ' tem ', ' ha ', 'quant', 'precis', ' falt', ' repor', 'reposicao', 'cadastr', ' lista', 'minimo', 'acabando', 'acabou', 'acabaram', 'esgot', 'zerad', ' quais '];
  // O estoque pelo NOME de uma peça cadastrada, sem a palavra «peça» («tem rotor de reposição?», «quantos filtros de óleo temos?», «temos anodo a bordo?», «falta rotor?»): só com um verbo ou número de
  // estoque junto, e a peça tem de ser o OBJETO do verbo (objetoPeca): «falta fluxo no filtro» e «acabou a luz da tela» são relato de falha. «Tem» e «há» sozinhos não bastam («o motor tem filtro?»): pedem o
  // «a bordo», o «em estoque» ou a reposição. «Preciso/falta repor alguma coisa» é o estoque sem nome.
  var PECAS_VERBOS_QUANT = ['quanto', 'quanta', 'quantos', 'quantas'], PECAS_VERBOS_TEM = ['temos', 'tenho', 'tem', 'ha'], PECAS_VERBOS_PRECISA = ['preciso', 'precisamos', 'precisa', 'precisar'];
  // «Tem correia do alternador?», «temos fusível de 24 V?», «tem fusível reserva?», «onde está o rotor do gerador?», «cadê o rotor?», «onde guardamos o impeller?»: a peça cadastrada é o OBJETO do verbo. O «tem» só vale
  // sem sujeito antes dele (os abridores abaixo: «ainda tem», «a gente tem», «e temos», «você tem»); com sujeito («o motor tem filtro?», «a bomba tem rotor?») é a pergunta do equipamento: o guia ou a IA. O
  // «reserva / sobressalente / reposição / extra» depois da peça diz que é o estoque, com ou sem sujeito. Com «no / na / em» + lugar («tem anodo no casco?») é a peça instalada, não o estoque («em estoque» fica).
  var PECAS_VERBOS_ONDE = ['esta', 'estao', 'fica', 'ficam', 'cade', 'guardamos', 'guardo', 'guardam', 'guarda', 'guardado', 'guardada', 'guardados', 'guardadas'];
  var PECAS_TEM_ABRE = /^ (?:(?:ainda|ja|sera que|a gente|voces?|vc|entao|e|mas|por acaso|aqui|ai|nos) )*(?:temos|tenho|tem|ha) /;
  var PECAS_RESERVA = / (?:reservas?|sobressalentes?|reposicao|reposicoes|extras?) /;
  var PECAS_LUGAR = / (?:no|na|nos|nas|dentro|embaixo|debaixo|sob|sobre) | em (?!estoque)/;
  // o relato de que a peça cadastrada falhou, com o pedido de outra («o fusível queimou, tem outro?»): é o estoque (a peça é o sujeito), não só o relato de falha que a lista PECAS_FORA manda ao guia
  var PECAS_RELATO_OUTRA = / (?:queimou|quebrou|estragou|furou|rompeu|trincou|estourou|rasgou|arrebentou)(?: .*)? (?:tem|temos|tenho|ha) (?:mais )?(?:outro|outra|outros|outras|um|uma|reservas?|sobressalentes?|de reposicao|de reserva) /;
  var PECAS_VERBOS_FALTA = ['falta', 'faltam', 'faltando', 'acabou', 'acabaram', 'acabando', 'zerou', 'repor', 'repomos', 'reposicao'];
  // A peça é o SUJEITO e o verbo é de estoque: «o rotor do gerador está zerado?», «por que o rotor do gerador está zerado?», «o filtro de óleo acabou?», «o anodo está no mínimo?». O sujeito é a 1ª palavra depois dos
  // artigos e do «por que» («o fluxo do filtro está zerado» e «a tela do plotter zerou» são relato de falha: o fluxo e a tela do plotter não são peça cadastrada).
  var PECAS_SEM_ESTOQUE = / (?:zerad[oa]s?|zerou|acabou|acabaram|esgotad[oa]s?|esgotou|no minimo|abaixo do minimo|em falta|sem estoque) /;
  var PECAS_ABRE = ' por que porque sera que ja ainda entao e mas ';
  function sujeitoPeca(q) {
    var ps = q.trim().split(' '), j = 0, w;
    while (j < ps.length && (PECAS_ARTIGOS + PECAS_ABRE).indexOf(' ' + ps[j] + ' ') !== -1) j++;
    w = j < ps.length ? tokens(ps[j])[0] : '';
    w = w ? radicalPeca(w) : '';
    return !!w && pecasPalavrasPeca(q).indexOf(w) !== -1 && pecasLista().some(function (x) { return nucleoPeca(x.n).indexOf(w) !== -1; });
  }
  function pecasNomePede(q) {
    return (/ quant[oa]s? .*\b(?:temos|tem|tenho|ha|sobraram|restam|faltam)\b/.test(q) && objetoPeca(q, PECAS_VERBOS_QUANT))
      || (PECAS_SEM_ESTOQUE.test(q) && sujeitoPeca(q))
      || (/ (?:preciso|precisamos|precisa|precisar) /.test(q) && objetoPeca(q, PECAS_VERBOS_PRECISA))
      || (/ (?:temos|tenho|tem|ha) .*(?:a bordo|no barco|na lancha|em estoque|de reposicao|de reserva|de sobressalente)/.test(q) && objetoPeca(q, PECAS_VERBOS_TEM))
      || (PECAS_TEM_ABRE.test(semVocativo(q)) && !PECAS_LUGAR.test(q) && objetoPeca(q, PECAS_VERBOS_TEM))
      || (/ (?:temos|tenho|tem|ha) /.test(q) && PECAS_RESERVA.test(q) && objetoPeca(q, PECAS_VERBOS_TEM))
      || (/ (?:onde|cade) /.test(q) && objetoPeca(q, PECAS_VERBOS_ONDE))
      || (/ de (?:reposicao|reserva) /.test(q) && nomeCadastrado(q))
      || (/ (?:falta|faltam|faltando|acabou|acabaram|acabando|zerou|repor|repomos|reposicao) /.test(q) && objetoPeca(q, PECAS_VERBOS_FALTA));
  }
  var PECAS_REPOR = / (?:alguma coisa|algo|o que|quais coisas) (?:para|pra|a|que|tem que|preciso|precisa|precisamos|devo|devemos) repor | (?:preciso|precisamos|precisa|devo|devemos|falta|faltam|tem|temos) (?:que )?repor /;
  // (o reparo, o código, a vida útil, a idade, o preço e a compra não são o estoque: seguem o guia, a rota do dinheiro ou a IA. O diesel e o combustível também, a menos que a pergunta nomeie uma peça
  // cadastrada — «quantos filtros de combustível temos?»)
  var PECAS_FORA = [' acabou de ', ' acabaram de ', 'gasolina', 'quebr', 'trav', 'defeit', 'vazament', 'vazando', 'falh', 'o que fazer', 'o que faco', 'como troc', 'como faz', 'como faco', 'como subst', ' pn ', 'codigo', 'part number',
    'recomend', 'suger', 'alarm', 'superaquec', 'disparou', ' parou', 'desligou', 'estour', 'queim', 'enchend', 'entrando', 'nao liga', 'nao parte', ' apit', 'fumac', 'esquent', 'quantas horas', ' dura ', 'vida util', 'manual',
    'quanto tempo', 'desde quando', 'quando troc', 'quando subst', 'ultima troca', 'temos que ', ' tem que ', ' tenho que ', 'quanto falta', ' falta para ', ' faltam para ', 'o que falta para', 'falta muito', 'falta troc', 'faltam troc', 'falta a troca', 'falta fazer', 'falta inspec', 'falta revis',
    ' preco ', ' precos ', ' valor ', ' valores ', 'custa', 'r$', 'comprar', ' compra ', ' compro ', 'cotacao', 'orcamento', ' reais '];
  var PECAS_COMBUSTIVEL = [' diesel', 'combustivel'];
  // quem vende, quem conserta, quem cuida: o telefone, o contato, o CNPJ e o e-mail de oficina, fornecedor e técnico têm a rota dos contatos (rota local, trava 13) ou a IA; a lista de estoque não os responde
  var PECAS_CONTATO = ['telefone', ' fone', 'contato', 'oficina', 'fornecedor', 'cnpj', 'cpf', 'email', 'e-mail', 'whats', 'tecnico', 'quem chamar', 'quem cuida', 'marina da base', 'quem vende', 'quem fornece', 'quem conserta'];
  var ESTOQUE_OUTRO = ['agua', 'gelo', 'comida', 'bebida', 'mantiment', 'potavel', 'cervej', 'refriger', 'lanche', 'racao'];
  // (a cabeça de emergência — o EPIRB e a baliza, o Seafire, o canal 16, o PAN-PAN, o DSC, o rádio/VHF, o botão DISTRESS, o MMSI, a salvatagem, o socorro — é do equipamento: «tem sobressalente do EPIRB?» segue a instrução
  // de segurança, local; trava 10. A guarda é a única do cabecaEmerg, no topo, antes de qualquer outra regra do estoque)
  function pecasPergunta(q) {
    if (cabecaEmerg(q)) return false;
    if (PECAS_RELATO_OUTRA.test(q) && sujeitoPeca(q) && !has(q, PECAS_CONTATO)) return true;
    if (has(q, PECAS_FORA) || has(q, PECAS_CONTATO)) return false;
    if (has(q, PECAS_COMBUSTIVEL) && !nomeCadastrado(q)) return false;
    if (has(q, PECAS_FORTES) || ((has(q, PECAS_FRACAS) || (has(q, [' estoque']) && !has(q, ESTOQUE_OUTRO))) && has(q, PECAS_PEDE))) return true;
    if (pecasNomePede(q)) return true;
    return PECAS_REPOR.test(q) && (pecasPalavras(q).length === 0 || objetoPeca(q, ['repor']));   // («preciso repor o gelo / o óleo» tem nome que não é peça: segue a rota dele)
  }

  // ——— Checklists guiados (F09; CONTRATO §1.18, §1.25) ———
  // Os 4 checklists (saída, chegada, abastecimento, fundeio) vêm do D.checklists gerado: cada item tem o rótulo curto (`c`), o texto (`t`), a FONTE (o «Guia de bordo — … §n», o «Checklist de bordo § …»
  // ou «boa prática») e, onde o quadro do instante permite julgar, uma verificação automática (`auto`): ✓ se o quadro confere (pela CapitaoAgora.nivel sobre as faixas do guia), ✗ se não,
  // «ler» se o item só mostra a leitura e pede a conferência da pessoa (previsão e maré, que são do mundo real e nunca dão ✓ sozinhas; o item `parcial`, que o quadro só confere em parte), e «sem»
  // sem leitura (o caminho null do modo real: SEM LEITURA). A pessoa marca ✓ (1) ou desmarca o ✓ do app ('n') em capitao.checklist.v1 = { <tipo>: { m: { <item>: 1 | 'n' }, em } },
  // que é só conveniência (some ao concluir). CONCLUIR grava UMA linha nova no diário (só com um toque ou um comando; o registro só cresce); a linha não casa a lista SOS nem o relato de óleo.
  var K_CHECK = 'capitao.checklist.v1';
  function checkTipos() { return EM_SOS || !D.checklists || !Array.isArray(D.checklists.tipos) ? [] : D.checklists.tipos; }
  function checkTipo(id) { return checkTipos().filter(function (t) { return t.id === id; })[0] || null; }
  function checkTodas() { var v = read(K_CHECK, null); return v && typeof v === 'object' && !Array.isArray(v) ? v : {}; }
  function checkMarcas(tipo) { var t = checkTodas()[tipo]; return t && typeof t === 'object' && t.m && typeof t.m === 'object' && !Array.isArray(t.m) ? t.m : {}; }
  function checkIds(tipo) { var tp = checkTipo(tipo), its = tp && D.checklists.itens && D.checklists.itens[tp.id]; return Array.isArray(its) ? its : []; }
  // marca (on true = ✓ da pessoa · 'n' = «não conferido», vence o ✓ do app · false = volta ao automático); recusa tipo ou item que não existe
  function checklistMarca(tipo, id, on) {
    var tp = checkTipo(tipo), o, t;
    if (!tp || !checkIds(tp.id).some(function (it) { return it.id === id; })) return null;
    o = checkTodas(); t = o[tp.id] && typeof o[tp.id] === 'object' ? o[tp.id] : (o[tp.id] = {});
    t.m = t.m && typeof t.m === 'object' && !Array.isArray(t.m) ? t.m : {}; t.em = t.em || new Date().toISOString();
    if (on === 'n') t.m[id] = 'n'; else if (on) t.m[id] = 1; else delete t.m[id];
    write(K_CHECK, o);
    return checkMarcas(tp.id);
  }
  function checklistZera(tipo) { var o = checkTodas(); if (o[tipo] !== undefined) { delete o[tipo]; write(K_CHECK, o); } }
  var R_ = function (estado, valor) { return { estado: estado, valor: valor }; };
  function ctxAuto() { var i = vivo(); return i ? { i: i, q: i.q, t: i.txt } : null; }
  function nv(x, campo) { var A = window.CapitaoAgora; try { var n = A.nivel(campo, x.q); return n ? n.nivel : null; } catch (e) { return null; } }
  function docsComPrazo() {
    var daEtiqueta = function (d) { return (D.equipamentos || []).some(function (e) { return e.seguranca === true && e.validade === d.id; }); };   // a validade de equipamento de segurança vai pela etiqueta, sem data
    return (D.documentos || []).filter(function (d) { return !daEtiqueta(d) && !isNaN(dnDe(d)); }).sort(function (a, b) { return dnDe(a) - dnDe(b); });
  }
  var AUTO = {
    tempo: function () {
      var pv = previsao();
      return R_('ler', pv ? 'previsão de hoje: ' + pv.vento + ' (' + pv.fonte + ')' : sim() ? semConexao() : 'previsão do dia: ' + SD + ' (sem leitura de hoje neste aparelho)');
    },
    mare: function () {
      var m = mareTexto(), pv = previsao();
      if (!m && !pv) return R_('ler', sim() ? semConexao() : 'previsão e maré: ' + SD + ' (sem leitura neste aparelho)');
      return R_('ler', [pv ? 'previsão de hoje: ' + pv.vento + ' (' + pv.fonte + ')' : '', m ? 'maré agora ' + m.agora + ' em relação ao nível médio do mar (modelo, não é a tábua oficial da Marinha)' : ''].filter(Boolean).join(' · '));
    },
    alertas: function (x) {
      var a = x && x.t.alarmes;
      if (!a) return R_('sem', SL);
      return a.indexOf('nenhum') === 0 ? R_('ok', 'nenhum alarme ativo') : R_('falta', a);
    },
    porao: function (x) {
      var bb = x && nv(x, 'porao_bb_nivel'), be = x && nv(x, 'porao_be_nivel'), t = tarefa('porao-teste'), L = limitesDe('porao_bb_nivel'), ate = L && L.normal && typeof L.normal.ate === 'number' ? ' (normal até ' + nb(L.normal.ate, 0) + ' cm)' : '';
      if (!x || !bb || !be) return R_('sem', SL);
      var niv = 'nível BB ' + campoTxt(x.i, 'porao_bb_nivel') + ' cm · BE ' + campoTxt(x.i, 'porao_be_nivel') + ' cm' + ate + (t ? ' · teste das bombas ' + prazoTxt(t) : '');
      return R_(bb === 'normal' && be === 'normal' ? 'ok' : 'falta', niv);
    },
    diesel: function (x) {
      var q = x && x.q, L = limitesDe('diesel_litros'), cap = E.tanques && E.tanques.diesel_l, min = L && L.normal && typeof L.normal.de === 'number' && cap ? L.normal.de / cap * 100 : 25;
      if (!x || !x.t.dieselLados || typeof q.diesel_bb_pct !== 'number' || typeof q.diesel_be_pct !== 'number') return R_('sem', SL);
      return R_(nv(x, 'diesel_litros') === 'normal' && q.diesel_bb_pct >= min && q.diesel_be_pct >= min ? 'ok' : 'falta', x.t.dieselLados + (x.t.diesel ? ' — ' + x.t.diesel : ''));
    },
    tanques: function (x) {
      var cs = ['tanque_agua_pct', 'tanque_cinzas_pct', 'tanque_negras_pct'], ns, ruim;
      if (!x || !x.t.tanques) return R_('sem', SL);
      ns = cs.map(function (c) { return nv(x, c); });
      if (ns.some(function (n) { return n === null; })) return R_('sem', SL);
      ruim = ['água doce', 'cinzas', 'negras'].filter(function (r, k) { return ns[k] !== 'normal'; });
      return R_(ruim.length ? 'falta' : 'ok', x.t.tanques + (ruim.length ? ' — fora da faixa: ' + ruim.join(', ') : ''));
    },
    baterias: function (x) {
      var cs = ['bateria_0_tensao_v', 'bateria_1_tensao_v', 'bateria_2_tensao_v'], ns;
      if (!x || !x.t.b24 || !x.t.b12) return R_('sem', SL);
      ns = cs.map(function (c) { return nv(x, c); });
      if (ns.some(function (n) { return n === null; })) return R_('sem', SL);
      return R_(ns.every(function (n) { return n === 'normal'; }) ? 'ok' : 'falta', x.t.b24 + ' · 12 V ' + x.t.b12);
    },
    seakeeper: function (x) {
      if (!x || typeof x.q.seakeeper_ativo !== 'boolean') return R_('sem', SL);
      if (x.q.seakeeper_ativo && nv(x, 'seakeeper_volante_pct') === 'normal') return R_('ok', x.t.seakeeper);
      return R_('ler', x.q.seakeeper_ativo ? x.t.seakeeper + ' — espere o display indicar pronto' : 'desligado — ligue com antecedência');
    },
    seakeeperOff: function (x) {
      if (!x || typeof x.q.seakeeper_ativo !== 'boolean') return R_('sem', SL);
      return x.q.seakeeper_ativo ? R_('falta', 'ainda ' + x.t.seakeeper) : R_('ok', 'desligado');
    },
    motoresOff: function (x) {
      if (!x || typeof x.q.motor_bb_rpm !== 'number' || typeof x.q.motor_be_rpm !== 'number') return R_('sem', SL);
      return x.q.motor_bb_rpm > 0 || x.q.motor_be_rpm > 0 ? R_('falta', 'motores ligados: ' + x.t.rpm) : R_('ok', 'motores desligados');
    },
    geradorOff: function (x) {
      if (!x || typeof x.q.gerador_ativo !== 'boolean') return R_('sem', SL);
      return x.q.gerador_ativo ? R_('falta', 'gerador ' + x.t.gerador) : R_('ok', 'gerador desligado');
    },
    documentos: function () {
      var com = docsComPrazo(), venc = com.filter(function (d) { return dnDe(d) < 0; }), pr = com.filter(function (d) { return dnDe(d) >= 0; })[0], n;
      if (venc.length) return R_('falta', 'vencido: ' + venc.map(function (d) { return d.n + ' (' + d.vence + ')'; }).join('; '));
      n = pr ? dnDe(pr) : null;
      return R_('ler', 'nenhum vencido (' + com.length + (com.length === 1 ? ' documento com prazo' : ' documentos com prazo') + ')' + (pr ? '; o mais próximo: ' + pr.n + ', ' + (n === 0 ? 'vence hoje' : 'em ' + n + (n === 1 ? ' dia' : ' dias')) : ''));
    },
    tarefas: function () {
      var at = agenda().filter(function (t) { return t.seguranca === true && atrasadaN(dnDe(t)); });
      return at.length ? R_('falta', at.map(function (t) { return min1(t.t) + ' (' + prazoTxt(t) + ')'; }).join('; ')) : R_('ok', 'nenhuma tarefa de segurança atrasada');
    },
    profundidade: function (x) {
      var n = x && nv(x, 'profundidade_m'), L = limitesDe('profundidade_m'), mn = L && L.normal && typeof L.normal.de === 'number' ? ' (mínimo ' + nb(L.normal.de, 0) + ' m)' : '';
      if (!x || !n || !x.t.prof) return R_('sem', SL);
      return R_(n === 'normal' ? 'ok' : 'falta', x.t.prof + mn);
    },
    deriva: function (x) {
      if (!x || typeof x.q.sog_nos !== 'number' || !x.t.sog) return R_('sem', SL);
      return x.q.sog_nos < 0.5 ? R_('ok', 'parado: velocidade sobre o fundo ' + x.t.sog) : R_('falta', 'navegando a ' + x.t.sog);
    }
  };
  // o item com a verificação de agora: { …item, auto: {estado, valor} | null, manual, anulado, porQuadro, feito }. O item `parcial` que o quadro confere vira «ler» (a pessoa confere o resto).
  function checklistItens(tipo) {
    var tp = checkTipo(tipo);
    if (!tp) return [];
    return congela(function () {
      var x = ctxAuto(), m = checkMarcas(tp.id);
      return checkIds(tp.id).map(function (it) {
        var a = null, manual = m[it.id] === 1 || m[it.id] === true, anulado = m[it.id] === 'n', ok;
        if (it.auto && AUTO[it.auto]) { try { a = AUTO[it.auto](x); } catch (e) { a = R_('sem', SL); } }
        if (it.parcial && a && a.estado === 'ok') a = R_('ler', a.valor + ' — o resto do item: confira');
        ok = !!(a && a.estado === 'ok');
        return Object.assign({}, it, { auto: a, manual: manual, anulado: anulado, porQuadro: ok && !manual && !anulado, feito: (ok && !anulado) || manual });
      });
    });
  }
  // A linha do diário ao concluir: «Checklist de saída concluído · 9/14 (7 pela telemetria) · pendentes: porão, documentos»
  function checklistLinha(tipo) {
    var tp = checkTipo(tipo), l, pq, pend;
    if (!tp) return null;
    l = checklistItens(tp.id); pq = l.filter(function (i) { return i.porQuadro; }).length; pend = l.filter(function (i) { return !i.feito; }).map(function (i) { return i.c; });
    return { tipo: tp.id, sys: tp.sys, feitos: l.length - pend.length, total: l.length, porQuadro: pq, pend: pend,
      t: tp.nome + ' concluído · ' + (l.length - pend.length) + '/' + l.length + (pq ? ' (' + pq + ' pela telemetria)' : '') + (pend.length ? ' · pendentes: ' + pend.join(', ') : ' · tudo conferido') };
  }
  // CONCLUIR: UMA linha nova no diário (a conveniência das marcas some); `ctx.commit === false` (pedido vindo de link) não grava. Devolve { …linha, entrada } ou null.
  function checklistConcluir(tipo, ctx) {
    var ln = checklistLinha(tipo), e;
    if (!ln || (ctx && ctx.commit === false)) return null;
    e = addDiario({ sys: ln.sys, t: ln.t, who: quem(), src: 'checklist de bordo' + (ln.porQuadro ? ' · telemetria' : '') });   // (o carimbo sim é do addDiario, P3F)
    checklistZera(ln.tipo);
    return Object.assign({ entrada: e }, ln);
  }
  // a resposta do chat: a 1ª linha (a falada) diz quantos itens estão conferidos pelo app ou por você, com a hora do instante, e os que não passaram; depois um item por linha (✓ conferido,
  // ✗ o app diz que não, • pede a sua conferência), cada um com a fonte e o código do FAQ. O guiado, item a item, é a tela do checklist (Fase 4).
  function checklistResposta(tipo, p) {
    var tp = checkTipo(tipo), l = checklistItens(tipo), i = vivo(), f, nao, mais, acoes;
    if (!tp || !l.length) return { text: 'Esse checklist não está cadastrado neste aparelho.', src: 'Fonte: nenhuma — ' + SD + ' de checklist', actions: act(p, [['FAQ de bordo', 'faq']]) };
    f = l.filter(function (x) { return x.feito; }).length; nao = l.filter(function (x) { return !x.feito && x.auto && x.auto.estado === 'falta'; }).map(function (x) { return x.c; });
    acoes = act(p, [['FAQ de bordo', 'faq']].concat(tipo === 'abastecimento' ? [['Abastecimento', 'abast']] : [], tipo === 'chegada' ? [['Fechar no diário', 'diario']] : [['Diário', 'diario']]));
    mais = l.map(function (x, k) {
      var m = x.feito ? '✓' : x.auto && x.auto.estado === 'falta' ? '✗' : '•', v = x.auto ? ' — ' + x.auto.valor : '', por = x.manual ? ' (conferido por você)' : '';
      return (k + 1) + '. ' + m + ' ' + (v ? x.t.replace(/\.$/, '') : x.t) + v + por + ' (' + x.fonte + (x.faq ? ' · FAQ ' + x.faq : '') + ')';
    });
    return { text: tp.nome + (i ? ' às ' + i.hora : '') + ': ' + f + ' de ' + l.length + ' conferidos' + (nao.length ? '; ' + (nao.length === 1 ? 'não passou: ' : 'não passaram: ') + nao.join(', ') : '') + '.\n' + mais.join('\n')
      + '\n✓ o app conferiu pelo quadro de bordo; ✗ o quadro diz que não; • pede a sua conferência a bordo.', src: 'Fonte: ' + (D.checklists.fonte || 'checklist de bordo') + ' · ' + FT.tele.replace('Fonte: ', ''), actions: acoes };
  }
  var CHECK_PALAVRAS = ['checklist', 'check list', 'lista de verificac'];
  // «saída» sem a palavra checklist só é o checklist de saída quando não é a pergunta do passado, do consumo, da duração, da distância, do horário nem de uma saída de coisa (ar, água, escape…): «como foi a saída de
  // ontem?», «quanto gastamos na saída?», «a que horas é a saída?» e «a saída de água do motor» seguem o diário, o consumo, o guia ou a IA. «Antes de largar/sair», «pré-saída» e «rotina de saída» são o checklist.
  var SAIDA_NAO_CHECK = ['como foi', 'resumo', 'ontem', 'ultima', 'anterior', 'passada', 'milhas', 'consumo', 'durou', 'quanto tempo', ' gast', 'fizemos', 'percorr', 'hoje cedo', 'amanha', 'vamos de', 'horario', 'que horas',
    ' saida de ar', ' saida de agua', ' saida do escape', ' saida de escape', ' saida de esgoto', ' saida de gas', ' saida de exaust', ' saida do tanque', ' saida da bomba'];
  var CHECK_ANTES = ['antes de largar', 'antes de sair', 'antes de zarpar', 'antes da saida'];
  // «pronto para sair?», «estamos prontos para largar?», «tudo pronto para zarpar?»: o checklist de saída (não o FAQ do Seakeeper nem o trecho de «antes de largar»); só a pergunta de conferir, neutra
  var PRONTO_SAIR = / prontos? (?:para|pra) (?:sair|largar|zarpar|a saida|a partida) /;
  function checkSaida(q) {
    return (has(q, [' saida']) && !has(q, SAIDA_NAO_CHECK)) || has(q, ['pre-saida', 'pre saida']) || (has(q, CHECK_ANTES) && leitura(q, CHECK_ANTES_OK)) || (PRONTO_SAIR.test(q) && leitura(q, CHECK_ANTES_OK));
  }

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
        var alerta = emergencia(pad(nota)), pressao = oleo(pad(nota)) === 1, reg = null, ef; // relato de emergência / pressão de óleo: grava a nota e traz os passos
        // F20/F15: o registro que conclui um serviço fecha a pendência que cita (com Desfazer) e propõe o Executado ou a tarefa; o texto de emergência, de pressão de óleo ou de cabeça de segurança (EPIRB, Seafire, rádio…) não mexe na agenda pelo chat
        reg = grava ? addDiario({ sys: 'Diário', t: nota, who: quem(), src: 'chat · voz/texto' }, alerta || pressao || cabecaEmerg(pad(nota)) ? undefined : { pendencia: true, agenda: true, chat: true }) : null;
        ef = efeitosNoChat(reg);
        return { text: (grava ? 'Registrado no diário de bordo · ' + n.d + ' ' + n.t + ' · ' + quem() + '\n“' + nota + '”\nLinha nova — nada se apaga.' : 'Não registrado — pedido vindo de link não grava no diário:\n“' + nota + '”\n' + como + '.') + (ef.linhas.length ? '\n' + ef.linhas.join('\n') : '') + (alerta ? '\nSe a emergência é agora: abra o SOS. ' + SOS_PASSOS : '') + (pressao ? '\nSe a pressão de óleo está baixa agora, verifique nesta ordem:\n' + OLEO_PASSOS : ''), src: 'Fonte: anotação de ' + quem() + ' · diário de bordo do app' + (pressao ? ' · ' + guia('g_motores') + ' §4' : ''), actions: ef.botoes.concat(act(p, (alerta ? [['Abrir SOS', 'sos']] : []).concat(pressao ? [['Contatos', 'equipe']] : [], [['Abrir diário', 'diario']]))),
          fala: falaRegistro(grava, alerta, pressao) + ef.fala };
      }
      var al = junto && emergencia(pad(nota)), pr = junto && oleo(pad(nota)) === 1;
      var passos = (al ? '\nSe a emergência é agora: abra o SOS. ' + SOS_PASSOS : '') + (pr ? '\nSe a pressão de óleo está baixa agora, verifique nesta ordem:\n' + OLEO_PASSOS : '');
      var acoes = (al ? [['Abrir SOS', 'sos']] : []).concat(pr ? [['Contatos', 'equipe']] : [], [['Abrir diário', 'diario']]);
      if (al || pr) {
        // «registre posição e hora, tem fogo no motor» (PROMPT §2.2, diário com alerta): a linha e a resposta NÃO usam o resumoAgora() (nada de coordenada, SOG, proa nem
        // leitura do quadro): a hora da linha, «posição: ler no plotter» no lugar da posição pedida, e os passos
        if (grava) addDiario({ sys: 'Diário', t: nota + ' · posição: ler no plotter', who: quem(), src: 'chat · voz/texto' });
        return { text: (grava ? 'Registrado no diário de bordo · ' + n.d + ' ' + n.t + ' · ' + quem() + '\n“' + nota + '”\nPosição: ler no plotter.\nLinha nova — nada se apaga.' : 'Não registrado — pedido vindo de link não grava no diário:\n“' + nota + '”\nPosição: ler no plotter.\n' + como + '.') + passos, src: 'Fonte: anotação de ' + quem() + ' · diário de bordo do app' + (pr ? ' · ' + guia('g_motores') + ' §4' : ''), actions: act(p, acoes), fala: falaRegistro(grava, al, pr) };
      }
      var t = resumoAgora();
      if (grava) addDiario({ sys: 'Navegação', tone: 'var(--cap-tele, #00f4fd)', t: (junto ? nota + ' · resumo: ' : 'Resumo registrado pelo atalho: ') + t, who: quem(), src: junto ? 'chat · voz/texto · telemetria' + demo() : 'atalho · telemetria' + demo() });
      return { text: (grava ? 'Registrado no diário de bordo · ' + n.d + ' ' + n.t + ' · ' + quem() + '\n' + (junto ? '“' + nota + '”\n' : '') + t + '\nLinha nova — nada se apaga.' : 'Não registrado — pedido vindo de link não grava no diário.\n' + (junto ? '“' + nota + '”\n' : '') + 'Resumo: ' + t + '\n' + como + ', ou toque no atalho DIÁRIO DE BORDO.') + passos, src: FT.tele + ' · diário de bordo do app' + (pr ? ' · ' + guia('g_motores') + ' §4' : ''), actions: act(p, acoes), fala: falaRegistro(grava, al, pr) };
    },
    // «O que devo registrar?» (F17): o pedido sem o texto; a próxima frase é gravada (ou «cancelar»). Pedido vindo de link não grava, então não arma a espera.
    diarioPede: function (p, ctx) {
      var grava = !ctx || ctx.commit !== false, abrir = act(p, [['Abrir diário', 'diario']]);
      if (grava) ESPERA_REG = { t: Date.now() };
      return grava ? { text: 'O que devo registrar no diário de bordo? Diga ou digite o texto agora — a próxima frase é gravada (ou diga “cancelar”).', src: 'Fonte: diário de bordo do app', actions: abrir, fala: 'O que devo registrar no diário?' }
        : { text: 'Não registrado — pedido vindo de link não grava no diário.\nPara registrar, diga ou digite aqui “registre no diário…” seguido do texto.', src: 'Fonte: diário de bordo do app', actions: abrir, fala: 'Pedido vindo de link não grava no diário.' };
    },
    // «registrar o relato» / «sim, registra» depois da proposta do relato (F16): confirma a proposta que espera (1 linha, com o complemento ou a data que a frase trouxe); sem proposta, diz que não há
    relatoRegistra: function (p, ctx, q) {
      var grava = !ctx || ctx.commit !== false, abrir = act(p, [['Abrir diário', 'diario']]), rp = grava ? relatoAlvo() : relatoPendente(), n = now(), sb, t, r, ex;
      var ef;
      if (!rp) return { text: 'Não há relato esperando para registrar. Para registrar, diga “registre no diário…” seguido do texto.', src: 'Fonte: diário de bordo do app', actions: abrir, fala: 'Não há relato esperando para registrar.' };
      if (rp.decidido) return relatoDecidido(rp, abrir);   // o botão velho de uma proposta já decidida: não registra a que espera
      if (!grava) return { text: 'Não registrado — pedido vindo de link não grava no diário.', src: 'Fonte: diário de bordo do app', actions: abrir, fala: 'Pedido vindo de link não grava no diário.' };
      sb = sobraRelato(q, pad(q)); t = achaTicket(ticketsCru(), rp.id);
      if (sb && sb.extra && t) { ex = comExtra(t.texto, sb); if (ex !== t.texto) editaTicket(t.id, { texto: ex }); }
      r = aceitaTicket(rp.id, { chat: true }); REL = null;
      if (!r) return { text: 'Esse relato não está mais esperando; nada foi registrado.', src: 'Fonte: diário de bordo do app', actions: abrir, fala: 'Esse relato não está mais esperando; nada foi registrado.' };
      if (r.ja) return { text: 'Esse relato já está registrado no diário.', src: 'Fonte: diário de bordo do app', actions: abrir, fala: 'Esse relato já está registrado.' };
      ef = efeitosNoChat(r.linha);   // F20/F15: o relato registrado fecha a pendência que cita e propõe a agenda
      return { text: 'Registrado no diário de bordo · ' + n.d + ' ' + n.t + ' · ' + quem() + '\n“' + r.linha.t + '”\nLinha nova — nada se apaga.' + (ef.linhas.length ? '\n' + ef.linhas.join('\n') : ''), src: 'Fonte: relato de ' + quem() + ' · diário de bordo do app', actions: ef.botoes.concat(abrir), fala: 'Registrado no diário de bordo.' + ef.fala };
    },
    // O botão «O que verificar?» do relato (F16): o item do FAQ ou o trecho dos guias que casa com o texto do relato; a tela também manda a pergunta à IA (pedeIA). Sem item, diz onde procurar. Os botões
    // Registrar / Não registrar seguem na resposta enquanto a proposta espera.
    relatoVerifica: function (p, ctx, q) {
      var nota = String(q || '').trim().replace(/^o que verificar e qual pode ser a causa[\s:,.—–-]*/i, ''), loc = null, al = ALVO_REL && Date.now() - ALVO_REL.t < 5000 ? achaTicket(ticketsCru(), ALVO_REL.id) : null, rp = al && al.estado === 'aberto' && al.origem === 'relato' ? { id: al.id } : relatoPendente();
      var acoes = rp ? [{ l: 'Registrar no diário', href: '#capitao-relato-registra-' + rp.id }, { l: 'Não registrar', href: '#capitao-relato-cancela-' + rp.id }] : [];
      try { loc = respostaFaq(nota, p) || respostaBase(nota, p, null) || respostaRelatoEquip(nota, p); } catch (e) { loc = null; }
      if (loc) return Object.assign({}, loc, { actions: acoes.concat(loc.actions || []) });
      return { text: 'O que verificar: esse relato é para a IA de bordo analisar (precisa de internet); o FAQ de bordo e os guias não têm um item que case com ele.\nPergunte pelo equipamento (“como limpar o filtro de água salgada?”) ou abra o FAQ de bordo.', src: 'Fonte: FAQ de bordo · guias de bordo', actions: acoes.concat(act(p, [['FAQ de bordo', 'faq']])) };
    },
    // «não registrar» / «cancelar» (F16, F17): descarta o que espera (a proposta do relato é recusada, 0 linhas) ou a espera do «o que devo registrar?»: nada é gravado
    relatoCancela: function (p, ctx, q) {
      var grava = !ctx || ctx.commit !== false, abrir = act(p, [['Abrir diário', 'diario']]), rp;
      if (!(ctx && ctx.espera) && adiaRegistro(q, pad(q))) {   // «registra depois»: nada é gravado, e a proposta que espera continua (com os botões)
        rp = relatoPendente();
        return rp ? { text: 'Certo — não registrei agora. A proposta do relato continua esperando: diga “registrar” quando quiser, ou “não registrar” para descartá-la.', src: 'Fonte: diário de bordo do app', actions: [{ l: 'Registrar no diário', href: '#capitao-relato-registra-' + rp.id }, { l: 'Não registrar', href: '#capitao-relato-cancela-' + rp.id }].concat(abrir), fala: 'Certo, não registrei agora. A proposta continua esperando.' }
          : { text: 'Certo — nada registrado agora. Quando quiser, diga ou digite “registre no diário…” seguido do texto.', src: 'Fonte: diário de bordo do app', actions: abrir, fala: 'Certo, nada registrado agora.' };
      }
      if (ctx && ctx.espera === 'nao') return { text: 'Não registrei isso no diário. Para registrar, diga ou digite “registre no diário…” seguido do texto.', src: 'Fonte: diário de bordo do app', actions: abrir, fala: 'Não registrei isso. Para registrar, diga registre no diário e o texto.' };
      if (ctx && ctx.espera) return { text: 'Certo — nada registrado no diário.', src: 'Fonte: diário de bordo do app', actions: abrir, fala: 'Certo, nada registrado.' };
      rp = grava ? relatoAlvo() : relatoPendente();
      if (!rp) return { text: 'Não há relato esperando; nada foi registrado.', src: 'Fonte: diário de bordo do app', actions: abrir, fala: 'Não há relato esperando; nada foi registrado.' };
      if (rp.decidido) return relatoDecidido(rp, abrir);   // o botão velho de uma proposta já decidida: não recusa a que espera
      if (grava) { recusaTicket(rp.id); REL = null; }
      return { text: 'Certo — relato não registrado; nada foi gravado no diário.', src: 'Fonte: diário de bordo do app', actions: abrir, fala: 'Certo, relato não registrado.' };
    },
    // F15 (diário → agenda): «agendar revisão do gerador para 15/11 com a marina» é a PROPOSTA da tarefa da equipe; nada é gravado sem o Confirmar (a tarefa em capitao.tarefas.v1 e 1 linha no diário)
    agendar: function (p, ctx, q) {
      var ag = achaAgendar(q), grava = !ctx || ctx.commit !== false, abrir = act(p, [['Abrir manutenção', 'manut']]), prop, sis, tk, pe, dia, fonte = 'Fonte: agenda da equipe do app';
      var como = 'Para agendar, diga “agendar <tarefa> para dd/mm” — por exemplo “agendar revisão do gerador para 15/11 com a marina”.';
      if (!ag) return { text: 'Não entendi a tarefa ou a data. ' + como, src: fonte, actions: abrir, fala: 'Não entendi a tarefa ou a data. Diga agendar, a tarefa e a data.' };
      if (ag.passada) return { text: 'A data ' + brData(ag.vence) + ' já passou — diga uma data de hoje em diante. ' + como, src: fonte, actions: abrir, fala: 'Essa data já passou. Diga uma data de hoje em diante.' };
      if (!grava) return { text: 'Não agendado — pedido vindo de link não grava na agenda.\n' + como, src: fonte, actions: abrir, fala: 'Pedido vindo de link não agenda.' };
      prop = { n: ag.n, vence: ag.vence, quem: ag.quem }; sis = sistemaDoTexto(q); if (sis) prop.sistema = sis;
      dia = diaData(ag.vence);
      if (loadTarefas().some(function (t) { return norm(t.n) === norm(ag.n) && t.vence === ag.vence && !loadExec()[t.id]; })) return { text: 'Já está na agenda da equipe: ' + ag.n + ' — vence ' + brData(ag.vence) + ' (' + emDias(dia) + '). Nada foi criado.', src: fonte, actions: abrir, fala: 'Essa tarefa já está na agenda para ' + brData(ag.vence) + '.' };
      tk = ticketAberto('tarefa', prop) || addTicket({ k: 'tarefa', origem: 'regra', texto: textoTicket('tarefa', prop), prop: prop });
      if (!tk) return { text: 'Não consegui montar a proposta de agendamento; nada foi gravado.', src: fonte, actions: abrir, fala: 'Não consegui montar a proposta.' };
      pe = armaProp('ticket', { id: tk.id });
      return { text: 'Posso agendar na equipe: ' + ag.n + ' — vence ' + brData(ag.vence) + ' (' + emDias(dia) + ')' + respTxt(prop) + '.\nNada é gravado sem o seu Confirmar (entra na agenda da equipe e 1 linha no diário): toque em Confirmar ou diga “confirmar”; para desistir, “recusar”.',
        src: fonte + ' · proposta ainda não gravada', actions: botoesProp(pe).concat(abrir), fala: 'Posso agendar ' + ag.n + ' para ' + brData(ag.vence) + ', ' + emDias(dia) + '. Confirma?' };
    },
    // CONFIRMAR a proposta da agenda (a tarefa feita ou o agendamento): aceitaTicket com o desfazer de 10 min; o botão de uma proposta antiga não age na nova
    ticketConfirma: function (p, ctx) {
      var grava = !ctx || ctx.commit !== false, pe = propVale(), al = alvoProp(), abrir = act(p, [['Abrir manutenção', 'manut']]), r, tk, d, f = 'Fonte: agenda do app · diário de bordo do app', ex, dia, lin;
      if (!pe || pe.tipo !== 'ticket') return { text: 'Não há proposta da agenda esperando confirmação. Para agendar, diga “agendar <tarefa> para dd/mm”.', src: f, actions: abrir, fala: 'Não há proposta esperando confirmação.' };
      if (al && al.seq !== pe.seq) return { text: 'Essa proposta é antiga: nada mudou. A mais recente continua esperando.', src: f, actions: botoesProp(pe).concat(abrir), fala: 'Essa proposta é antiga. A mais recente continua esperando.' };
      if (!grava) return { text: 'Não gravado — pedido vindo de link não confirma proposta.', src: f, actions: abrir, fala: 'Pedido vindo de link não confirma proposta.' };
      r = aceitaTicket(pe.id, { chat: true }); PEND_CHAT = null;
      if (!r) return { text: 'Não consegui gravar essa proposta (a tarefa já foi executada ou saiu da agenda); nada foi gravado.', src: f, actions: abrir, fala: 'Não consegui gravar essa proposta; nada foi gravado.' };
      if (r.ja) return { text: 'Essa proposta já foi confirmada.', src: f, actions: abrir, fala: 'Essa proposta já foi confirmada.' };
      tk = achaTicket(ticketsCru(), pe.id); d = armaDesfaz('ticket', { id: pe.id }, r.desfazAte);
      if (tk && tk.k === 'exec') { var ag = tarefa(tk.prop && tk.prop.tarefa); ex = ag ? loadExec()[ag.id] : null; return { text: 'Executado: ' + (ag ? ag.t : '') + (ag ? ' (' + ag.equip + ')' : '') + (ex ? ' — marcado em ' + ex.d + ' às ' + ex.t : '') + '. A tarefa saiu das pendentes da agenda e entrou 1 linha no diário (linha nova, nada se apaga).\nSe foi engano, diga “desfazer” ou toque em Desfazer.', src: f, actions: [botaoDesfaz(d)].concat(abrir), fala: 'Marcado como executado. Se foi engano, diga desfazer.' }; }
      lin = tk && tk.prop || {}; dia = diaData(lin.vence);
      return { text: 'Tarefa agendada: ' + lin.n + ' — vence ' + brData(lin.vence) + ' (' + emDias(dia) + ')' + respTxt(lin) + '. Entrou na agenda da equipe e 1 linha no diário (linha nova, nada se apaga).\nSe foi engano, diga “desfazer” ou toque em Desfazer.', src: f, actions: [botaoDesfaz(d)].concat(abrir), fala: 'Tarefa agendada para ' + brData(lin.vence) + '. Se foi engano, diga desfazer.' };
    },
    ticketRecusa: function (p, ctx) {
      var grava = !ctx || ctx.commit !== false, pe = propVale(), al = alvoProp(), abrir = act(p, [['Abrir manutenção', 'manut']]), f = 'Fonte: agenda do app';
      if (!pe || pe.tipo !== 'ticket') return { text: 'Não há proposta da agenda esperando; nada foi gravado.', src: f, actions: abrir, fala: 'Não há proposta esperando; nada foi gravado.' };
      if (al && al.seq !== pe.seq) return { text: 'Essa proposta é antiga: nada mudou. A mais recente continua esperando.', src: f, actions: botoesProp(pe).concat(abrir), fala: 'Essa proposta é antiga. A mais recente continua esperando.' };
      if (!grava) return { text: 'Pedido vindo de link não recusa proposta; nada mudou.', src: f, actions: abrir, fala: 'Pedido vindo de link não recusa proposta.' };
      recusaTicket(pe.id); PEND_CHAT = null;
      return { text: 'Certo — proposta recusada; nada foi gravado.', src: f, actions: abrir, fala: 'Certo, proposta recusada.' };
    },
    // DESFAZER o que acabou de ser confirmado ou fechado (10 min): a proposta da agenda volta a aberta (a tarefa sai ou volta para a agenda) ou a pendência fechada pelo registro reabre — sempre por linha nova
    ticketDesfaz: function (p, ctx) {
      var grava = !ctx || ctx.commit !== false, d = desfazVale(), al = alvoProp(), abrir = act(p, [['Abrir manutenção', 'manut']]), f = 'Fonte: diário de bordo do app · agenda do app', r, tk;
      if (!d) return { text: 'Não há nada para desfazer agora (o desfazer vale 10 minutos depois de confirmar uma proposta ou de fechar uma pendência).', src: f, actions: abrir, fala: 'Não há nada para desfazer agora.' };
      if (al && al.seq !== d.seq) return { text: 'Essa ação é antiga: nada mudou.', src: f, actions: abrir, fala: 'Essa ação é antiga; nada mudou.' };
      if (!grava) return { text: 'Pedido vindo de link não desfaz; nada mudou.', src: f, actions: abrir, fala: 'Pedido vindo de link não desfaz.' };
      DESFAZ = null;
      if (d.tipo === 'pend') {
        r = desfazPendencia(d.r);
        return r ? { text: 'Desfeito: a pendência “' + fimPend(d.r.t) + '” voltou a ficar aberta (linha nova no diário).', src: f, actions: act(p, [['Abrir diário', 'diario']]), fala: 'Desfeito. A pendência voltou a ficar aberta.' }
          : { text: 'Não deu para desfazer: a pendência mudou de estado depois do fechamento; nada foi alterado.', src: f, actions: act(p, [['Abrir diário', 'diario']]), fala: 'Não deu para desfazer; nada foi alterado.' };
      }
      tk = achaTicket(ticketsCru(), d.id); r = desfazTicket(d.id);
      return r ? { text: 'Desfeito: ' + (tk && tk.k === 'exec' ? 'a tarefa voltou para a agenda' : 'a tarefa saiu da agenda da equipe') + ' e a linha do diário foi anulada (linha nova). A proposta voltou a ficar aberta, mas só espera o Confirmar nas telas da agenda.', src: f, actions: abrir, fala: 'Desfeito.' }
        : { text: 'Não deu para desfazer: a janela de 10 minutos acabou ou a proposta mudou; nada foi alterado.', src: f, actions: abrir, fala: 'Não deu para desfazer; nada foi alterado.' };
    },
    // F12 (alarmes pedidos): «me avise se a pressão do óleo do BB cair abaixo de 2 bar» é a PROPOSTA da regra (nada é gravado até o Confirmar); o que falta ou está fora da faixa recebe a explicação, local, sem IA
    alarmePedido: function (p, ctx, q) {
      var grava = !ctx || ctx.commit !== false, abrir = act(p, [['Meus alarmes', askHref(p, 'meus alarmes')], ['Telemetria', 'console']]), pr = almParse(q), i = vivo(), A = almCfg(), max = A && typeof A.max === 'number' ? A.max : 10, ativas = almVigentes(), f = 'Fonte: alarmes pedidos neste aparelho' + (i ? ' · ' + i.fonteTxt : '');
      var ex = 'Exemplo: “me avise se a pressão do óleo do BB cair abaixo de 2 bar”.', pe, regras, dup, linhas;
      if (!A) return { text: 'Os alarmes pedidos não estão disponíveis neste aparelho.', src: f, actions: abrir, fala: 'Os alarmes pedidos não estão disponíveis.' };
      if (!pr.ok) {
        var m = pr.m, t = pr.motivo === 'sentido' ? 'Faltou o sentido: abaixo de quanto, ou acima de quanto? ' + ex
          : pr.motivo === 'limite' ? 'Faltou o valor do limite. ' + ex
          : pr.motivo === 'medida' ? 'Não achei a medida. Posso vigiar: ' + almMetricas().map(function (x) { return min1(x.nome); }).filter(function (x, k, v) { return v.indexOf(x) === k; }).join(' · ') + '. ' + ex
          : pr.motivo === 'ambigua' ? 'Um alarme por pedido: diga uma medida e um sentido (“abaixo de” ou “acima de”) de cada vez. ' + ex
          : pr.motivo === 'unidade' ? 'A unidade de ' + min1(m.nome) + ' é ' + m.un + '. ' + ex
          : pr.motivo === 'faixa' ? 'O limite de ' + min1(m.nome) + ' vai de ' + almTxt(m, m.faixa[0]) + ' a ' + almTxt(m, m.faixa[1]) + ' (a faixa que o app aceita para o alarme).'
          : m.nome + ' não aceita esse sentido. ' + ex;
        return { text: t, src: f, actions: abrir, fala: pr.motivo === 'faixa' ? 'Esse limite está fora da faixa. De ' + almTxt(m, m.faixa[0]) + ' a ' + almTxt(m, m.faixa[1]) + '.' : 'Não consegui montar o alarme. Diga a medida, abaixo ou acima de, e o valor.' };
      }
      dup = pr.itens.filter(function (it) { return ativas.some(function (a) { return a.campo === it.m.campos[0] && a.op === it.op && a.limite === it.limite; }); });
      if (dup.length === pr.itens.length) return { text: 'Esse alarme já existe: ' + ativas.filter(function (a) { return dup.some(function (it) { return a.campo === it.m.campos[0] && a.op === it.op && a.limite === it.limite; }); }).map(function (a) { return '#' + a.n + ' ' + almRegra(a); }).join(' · ') + '. Nada foi criado.', src: f, actions: abrir, fala: 'Esse alarme já existe. Nada foi criado.' };
      if (ativas.length + pr.itens.length - dup.length > max) return { text: 'Você já tem ' + ativas.length + ' de ' + max + ' alarmes pedidos: não cabe mais ' + (pr.itens.length - dup.length) + '. Apague um com “apagar alarme #n” (veja os números em “meus alarmes”).', src: f, actions: abrir, fala: 'Você já tem ' + ativas.length + ' alarmes pedidos; apague um antes de criar outro.' };
      regras = pr.itens.map(function (it) { return it.m.nome + ' ' + (it.op === '<' ? 'abaixo de ' : 'acima de ') + almTxt(it.m, it.limite); });
      linhas = pr.itens.map(function (it) { var v = i && i.q ? i.q[it.m.campos[0]] : null; return '• ' + regras[pr.itens.indexOf(it)] + almMotorTxt(it.m) + (typeof v === 'number' ? ' — agora ' + almTxt(it.m, v) + ' (' + i.hora + ')' : ''); });
      ALM_PEDIU = Date.now();
      pe = grava ? armaProp('alarme', { itens: pr.itens.map(function (it) { return { campo: it.m.campos[0], op: it.op, limite: it.limite }; }) }) : null;
      return { text: 'Posso criar ' + (pr.itens.length === 1 ? 'este alarme' : 'estes ' + pr.itens.length + ' alarmes') + ': ' + regras.join(' · ') + '.\n' + linhas.join('\n') + '\nAviso só na tela do app (nunca crítico: sem notificação, sem som, não abre o SOS nem grava no diário). ' + (grava ? 'Nada é gravado sem o seu Confirmar: toque em Confirmar ou diga “confirmar alarme”; para desistir, “cancelar”.' : 'Não criado — pedido vindo de link não cria alarme: digite o pedido aqui no chat para confirmar.') + ' Você tem ' + ativas.length + ' de ' + max + ' alarmes pedidos.',
        src: f, actions: (pe ? botoesProp(pe) : []).concat(abrir),
        fala: 'Posso criar ' + (pr.itens.length === 1 ? 'este alarme' : 'estes ' + pr.itens.length + ' alarmes') + ': ' + regras.join('; ') + '.' + (i && i.q && typeof i.q[pr.itens[0].m.campos[0]] === 'number' ? ' Leitura agora, às ' + i.hora + ': ' + almTxt(pr.itens[0].m, i.q[pr.itens[0].m.campos[0]]) + '.' : '') + (grava ? ' Confirma?' : ' Não criei nada: pedido vindo de link.') };
    },
    alarmeConfirma: function (p, ctx) {
      var grava = !ctx || ctx.commit !== false, pe = propVale(), al = alvoProp(), abrir = act(p, [['Meus alarmes', askHref(p, 'meus alarmes')], ['Telemetria', 'console']]), i = vivo(), f = 'Fonte: alarmes pedidos neste aparelho' + (i ? ' · ' + i.fonteTxt : ''), r, itens, A = almCfg(), max = A && typeof A.max === 'number' ? A.max : 10;
      if (!pe || pe.tipo !== 'alarme') return { text: 'Nenhum alarme esperando confirmação. Peça de novo, por exemplo: “me avise se a pressão do óleo do BB cair abaixo de 2 bar”.', src: f, actions: abrir, fala: 'Nenhum alarme esperando confirmação.' };
      if (al && al.seq !== pe.seq) return { text: 'Essa proposta é antiga: nada mudou. A mais recente continua esperando.', src: f, actions: botoesProp(pe).concat(abrir), fala: 'Essa proposta é antiga. A mais recente continua esperando.' };
      if (!grava) return { text: 'Não criado — pedido vindo de link não cria alarme.', src: f, actions: abrir, fala: 'Pedido vindo de link não cria alarme.' };
      itens = pe.itens.map(function (it) { return { m: almMetricaDeCampo(it.campo), op: it.op, limite: it.limite }; });
      r = almCria(itens); PEND_CHAT = null;
      if (r.erro === 'max') return { text: 'Não criei: você já tem ' + almVigentes().length + ' de ' + max + ' alarmes pedidos. Apague um com “apagar alarme #n”.', src: f, actions: abrir, fala: 'Não criei: o máximo de alarmes pedidos foi atingido.' };
      if (!r.criadas.length) return { text: 'Nenhum alarme novo: esse pedido já existia ou saiu da faixa aceita. Veja “meus alarmes”.', src: f, actions: abrir, fala: 'Nenhum alarme novo foi criado.' };
      return { text: 'Alarme criado: ' + r.criadas.map(function (a) { return '#' + a.n + ' ' + almRegra(a); }).join(' · ') + '.\nAviso só na tela do app (nunca crítico; sem notificação). Para ver: “meus alarmes”; para apagar: “apagar alarme #' + r.criadas[0].n + '”. Você tem ' + almVigentes().length + ' de ' + max + ' alarmes pedidos' + (i ? ' (' + i.hora + ')' : '') + '.',
        src: f, actions: abrir, fala: 'Alarme criado: ' + r.criadas.map(function (a) { return 'número ' + a.n + ', ' + almRegra(a); }).join('; ') + '.' };
    },
    alarmeCancela: function (p, ctx) {
      var grava = !ctx || ctx.commit !== false, pe = propVale(), al = alvoProp(), abrir = act(p, [['Meus alarmes', askHref(p, 'meus alarmes')]]), f = 'Fonte: alarmes pedidos neste aparelho';
      if (!pe || pe.tipo !== 'alarme') return { text: 'Nenhum alarme esperando confirmação; nada foi gravado.', src: f, actions: abrir, fala: 'Nenhum alarme esperando confirmação.' };
      if (al && al.seq !== pe.seq) return { text: 'Essa proposta é antiga: nada mudou. A mais recente continua esperando.', src: f, actions: botoesProp(pe).concat(abrir), fala: 'Essa proposta é antiga. A mais recente continua esperando.' };
      if (!grava) return { text: 'Pedido vindo de link não cancela proposta; nada mudou.', src: f, actions: abrir, fala: 'Pedido vindo de link não cancela proposta.' };
      PEND_CHAT = null;
      return { text: 'Certo — alarme cancelado; nada foi gravado.', src: f, actions: abrir, fala: 'Certo, alarme cancelado.' };
    },
    alarmesLista: function (p) {
      var v = almVigentes(), at = almAtivos(), i = vivo(), A = almCfg(), max = A && typeof A.max === 'number' ? A.max : 10, h = i ? ' às ' + i.hora : '', f = 'Fonte: alarmes pedidos neste aparelho' + (i ? ' · ' + i.fonteTxt : ''), abrir = act(p, [['Telemetria', 'console']]);
      if (!v.length) return { text: 'Você não tem alarmes pedidos' + h + ' (0 de ' + max + ').\nPara criar um: “me avise se a pressão do óleo do BB cair abaixo de 2 bar”.', src: f, actions: abrir, fala: 'Você não tem alarmes pedidos' + h + '.' };
      return { text: v.length + (v.length === 1 ? ' alarme pedido' : ' alarmes pedidos') + h + ' (de ' + max + ' possíveis)' + (at.length ? ', ' + at.length + (at.length === 1 ? ' ativo agora' : ' ativos agora') : ', nenhum ativo agora') + ':\n' + v.map(function (a) {
        var s = at.filter(function (x) { return x.id === a.id; })[0], val = i && i.q && typeof i.q[a.campo] === 'number' ? almTxt(a.m, i.q[a.campo]) : '';
        return '• #' + a.n + ' ' + almRegra(a) + (s ? ' — ATIVO desde ' + s.hora + (val ? ' (agora ' + val + ')' : '') : val ? ' — agora ' + val + ', sem disparar' : ' — sem leitura agora');
      }).join('\n') + '\nPara apagar: “apagar alarme #n”.', src: f, actions: abrir };
    },
    alarmeApaga: function (p, ctx, q) {
      var grava = !ctx || ctx.commit !== false, n = almApagaN(q), v = almVigentes(), f = 'Fonte: alarmes pedidos neste aparelho', abrir = act(p, [['Meus alarmes', askHref(p, 'meus alarmes')]]), lin, a, A = almCfg(), max = A && typeof A.max === 'number' ? A.max : 10;
      if (n <= 0) return { text: 'Qual alarme pedido apagar? Diga o número: “apagar alarme #2”.' + (v.length ? '\nVocê tem: ' + v.map(function (x) { return '#' + x.n + ' ' + almRegra(x); }).join(' · ') + '.' : '\nVocê não tem alarmes pedidos.'), src: f, actions: abrir, fala: v.length ? 'Qual alarme apagar? Diga o número.' : 'Você não tem alarmes pedidos.' };
      if (!grava) return { text: 'Não apagado — pedido vindo de link não apaga alarme.', src: f, actions: abrir, fala: 'Pedido vindo de link não apaga alarme.' };
      a = v.filter(function (x) { return x.n === n; })[0]; lin = a ? almApaga(n) : null;
      if (!lin) return { text: 'Não há alarme pedido #' + n + ' ativo (não existe ou já foi apagado).' + (v.length ? '\nVocê tem: ' + v.map(function (x) { return '#' + x.n + ' ' + almRegra(x); }).join(' · ') + '.' : ''), src: f, actions: abrir, fala: 'Não há alarme pedido número ' + n + ' ativo.' };
      return { text: 'Alarme #' + n + ' apagado: ' + almRegra(a) + '. Linha nova no registro dos alarmes (nada se apaga); o número não volta a ser usado. Restam ' + almVigentes().length + ' de ' + max + ' alarmes pedidos.', src: f, actions: abrir, fala: 'Alarme número ' + n + ' apagado.' };
    },
    // F26: o que o app faz, para quem pergunta «o que você pode fazer?». Local, sem internet e sem IA; cada função citada tem a rota dela (o testes/cerebro.py confere cada pergunta de exemplo entre aspas)
    capacidades: function (p) {
      return { text: 'Sou o Capitão IA, o assistente de bordo. Posso:\n'
        + '• Dizer como o barco está agora, com número e hora: “como está a navegação?”, “telemetria”, “posição agora”, “qual a profundidade?”, “qual a hora de chegada?”.\n'
        + '• Avisar quando você pedir, só na tela do app: “me avise se a temperatura do motor passar de 90 graus”, “meus alarmes”, “apagar alarme #1”.\n'
        + '• Mostrar os alarmes ativos e o que verificar primeiro: “tem algum alarme ativo?”; e as tendências dos motores e das baterias: “quais as tendências?”.\n'
        + '• Cuidar da manutenção: “próximas manutenções”, “horímetros”, “quais peças temos a bordo?”; e agendar uma tarefa da equipe: “agendar revisão do gerador para 15/11 com a marina”.\n'
        + '• Registrar no diário só quando você mandar: “registre no diário que limpamos o filtro de água salgada”. Se o registro conclui um serviço, fecho a pendência que ele cita e proponho marcar a tarefa como executada — tudo com Confirmar e Desfazer.\n'
        + '• Documentos, abastecimento, consumo e autonomia: “documentos vencendo”, “consumo de diesel”, “autonomia”.\n'
        + '• Checklists de saída, chegada, abastecimento e fundeio: “checklist de saída”.\n'
        + '• Passo a passo dos equipamentos e dos guias de bordo: “como ligar o gerador?”, “guias de bordo”.\n'
        + '• Clima e maré na posição de referência (precisam de internet) e a decisão de sair: “clima e vento”, “maré agora”, “é seguro sair hoje?”.\n'
        + '• Emergência: o SOS, o canal 16 e os procedimentos padrão — em perigo, abra o SOS; “canal 16” traz a ordem da chamada.\n'
        + 'O que está na lista acima funciona no aparelho, sem internet (menos o clima e a maré). Pergunta aberta, fora dela, vai para a IA de bordo quando há internet.',
        src: 'Fonte: funções do app Capitão IA', actions: act(p, [['Console completo', 'console'], ['Manutenção', 'manut'], ['FAQ de bordo', 'faq'], ['Abrir SOS', 'sos']]),
        fala: 'Respondo sobre a situação do barco agora, alarmes que você pedir, manutenção e agenda, diário, documentos, abastecimento, checklists, equipamentos, clima e maré, e emergência. A lista completa está na tela.' };
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
    // A 1ª linha responde ao que foi perguntado: «o rotor do gerador está atrasado?» nomeia a tarefa (só uma casa): «Sim — …» ou «Não — …» com o prazo e a hora; a pergunta geral abre pela lista das atrasadas
    manutencao: function (p, ctx, qq) {
      var at = atrasadas(), prox = agenda().filter(function (t) { return !atrasadaN(dnDe(t)); }).slice(0, 3), oleoM = tarefa('motores-oleo'), i = vivo(), alvo = tarefaPedida(qq), ql = pad(qq || ''), l1 = '';
      if (alvo) l1 = (/ (?:atrasad\w*|atraso) /.test(ql) ? (atrasadaN(dnDe(alvo)) ? 'Sim — ' : 'Não — ') : '') + linhaFalta(alvo, alvo.t + ' (' + alvo.equip + ')') + '\n';
      var linha = function (t) { return seg(t) ? '• ' + t.t + ' (' + t.quem + ') — ' + NOTA_ETIQUETA : '• ' + prazoTxt(t) + ' — ' + t.t + ' (' + t.quem + ')'; };
      return { text: l1 + (at.length ? 'Atrasadas (' + at.length + ')' + (i ? ' às ' + i.hora : '') + ':\n' + at.map(function (t) { return '• ' + t.t + ' · ' + t.equip + ' — ' + prazoTxt(t) + ' (' + t.quem + ')'; }).join('\n') : 'Nenhuma tarefa atrasada' + (i ? ' às ' + i.hora : '') + '.') + '\nPróximas:\n' + prox.map(linha).join('\n') + (oleoM && oleoM.horas && !execVisivel()[oleoM.id] ? '\nÓleo e filtros dos motores: ' + oleoM.vence + ' ou ' + oleoM.horas.limite + ' h — faltam ' + nb(faltam(oleoM)) + ' h.' : '') + tarefasLinha() + (D.agendaFalta && D.agendaFalta.length ? '\nFalta registrar: ' + D.agendaFalta.join(' · ') + '.' : ''), src: FT.agenda + ' · ' + (D.agenda || []).length + ' tarefas · horímetros ' + (M.hora || ''), actions: act(p, [['Abrir manutenção', 'manut']]) };
    },
    // A 1ª linha responde ao que foi perguntado: «quanto diesel tem?», «qual o nível do tanque de diesel?» abrem com o diesel a bordo (litros, % e a hora); a pergunta da autonomia, do alcance e do abastecimento, com a autonomia
    autonomia: function (p, ctx, qq) { var nivel = NIVEL_DIESEL.test(pad(qq || '')) && !has(pad(qq || ''), ['autonomia', 'alcance', 'abastec', 'nota fiscal', 'nf-e']), lDiesel = 'A bordo ≈ ' + mil(DI.litros) + ' L de ' + mil(DI.capacidade) + ' (BB ' + nb(DI.bb) + ' % · BE ' + nb(DI.be) + ' %) — ' + SNAP.dieselHora + '.'; return { text: (nivel ? lDiesel + '\n' : '') + 'Autonomia ≈ ' + nb(AUT.horas) + ' h · ≈ ' + AUT.mn + ' mn a ' + CON.cruzeiro.nos + ' nós (' + mil(CON.cruzeiro.rpm) + ' rpm · ' + CON.cruzeiro.lph + ' L/h, dois motores), com reserva de ' + reservaPct() + ' %.' + (nivel ? '' : '\n' + lDiesel) + '\nEm marcha lenta (' + nb(CON.lenta.lph) + ' L/h) ≈ ' + AUT.lenta + ' h. Consumido desde o abastecimento de ' + CON.desdeAbast.desde.slice(0, 5) + ': ≈ ' + litrosTxt(CON.desdeAbast.litros) + ' L (' + CON.desdeAbast.horas + ').', src: 'Fonte: ' + tele() + ' (taxa de combustível dos dois motores, ' + (vivo() ? CON.fonte : CON.periodo) + ') · ' + FT.abast.replace('Fonte: ', '') + ' — estimativa; a nota fiscal é a fonte oficial', actions: act(p, [['Abastecimento', 'abast']]) }; },
    // Maré: do mundo real (Open-Meteo Marine, modelo, não a tábua da Marinha). Sem conexão e sem leitura salva: a frase do §2.5 e a situação de bordo (decisão (g)).
    mare: function (p) {
      var m = mareTexto(), s = sim();
      if (!m) return s ? { text: semConexao() + '\nO app usa o modelo do Open-Meteo Marine na posição de referência (Balneário Camboriú) — não é a tábua oficial da Marinha (DHN).\n' + linhaBordo(), src: 'Fonte: nenhuma leitura de maré neste aparelho — Open-Meteo Marine sem resposta', actions: act(p, [['Registrar pendência', 'diario']]) }
        : { text: 'SEM DADOS de maré agora: sem internet e sem leitura salva neste aparelho.\nO app usa o modelo do Open-Meteo Marine na posição de referência (Balneário Camboriú) — não é a tábua oficial da Marinha (DHN).', src: 'Fonte: nenhuma disponível agora — Open-Meteo Marine sem resposta', actions: act(p, [['Registrar pendência', 'diario']]) };
      return { text: 'Maré agora ' + m.agora + ' em relação ao nível médio do mar (Balneário Camboriú).\nPróximas horas: ' + m.prox.join(' · ') + '.\nÉ modelo (≈ 8 km), não a tábua oficial da Marinha — não use para passar em canal raso. ' + (s ? 'Corrente: o modelo traz só a altura da maré.' : 'Corrente: ' + SD + '.'), src: 'Fonte: Open-Meteo Marine (sea_level_height_msl) · posição de referência ' + ((D.posicaoRef && D.posicaoRef.fonte) || '') + (s && mareLidaHM() ? ' · lida às ' + mareLidaHM() : ''), actions: act(p, [['Clima', askHref(p, 'Clima')]]) };
    },
    // Clima: a previsão do dia REAL (§2.5) e, à parte, o vento, a pressão, o ar, a água e as ondas «a bordo agora». Sem a leitura de hoje, a frase do §2.5 e a situação de bordo.
    clima: function (p, ctx, qq) {
      var pv = previsao(), s = sim(), i = vivo(), q = i && i.q, lv = linhasVento(qq, i), sq = pad(qq || '');
      // sem previsão (sem conexão), a pergunta do vento abre pelo vento do quadro «a bordo agora» (decisão 12) e não pela frase de falta de conexão; a de chuva diz de uma vez que o app não tem previsão de chuva
      if (!lv && !pv && s && i && i.txt.vento && has(sq, [' vento ', ' ventos ', ' ventando ', ' ventania ', ' rajada ', ' rajadas ']) && !has(sq, [' previsao ', ' amanha ', ' hoje ']) && leitura(sq, NEUTRAS_BASE + VENTO_OK_P)) lv = 'A bordo agora, vento verdadeiro ' + i.txt.vento + ' — ' + i.hora + '.' + (i.txt.ventoAp ? '\nVento aparente ' + i.txt.ventoAp + '.' : '');
      if (has(sq, [' chover ', ' chovendo ', ' chuva ', ' chuvas ', ' chuvoso ']) && !has(sq, [' agua da chuva '])) lv = 'O app não traz previsão de chuva — só temperatura e vento do dia: confira o boletim da Marinha ou o windy.com antes de sair.' + (lv ? '\n' + lv : '');
      var cab = pv ? 'Hoje em Balneário Camboriú: ' + pv.temp + ' · ' + pv.vento + ' (previsão ' + pv.fonte + ').' : s ? semConexao() + '\n' + linhaBordo() : 'Previsão do dia: ' + SD + ' (sem leitura de hoje neste aparelho).';
      var bordo = (i ? 'A bordo agora (' + SNAP.quando + '):' : 'Última leitura de bordo (' + SNAP.quando + '):') + '\n• vento verdadeiro ' + nb(S.vento) + ' nós de ' + grau3(S.ventoDe) + '\n• barômetro ' + nb(S.pressao, 0) + ' hPa\n• ar ' + nb(S.ar) + ' °C · água ' + nb(S.agua) + ' °C' + (i && q && typeof q.ondas_m === 'number' ? '\n• ondas ' + i.txt.ondas : '');
      var fim = s ? 'Para navegar, consulte a meteorologia marinha da Marinha do Brasil.' : pv ? 'Previsão do mar (ondas): ' + SD + ' no app — para navegar, consulte a meteorologia marinha da Marinha do Brasil.' : 'Previsão de vento e mar para navegar: ' + SD + ' no app — consulte a meteorologia marinha da Marinha do Brasil.';
      return { text: (lv ? lv + '\n' : '') + cab + '\n' + bordo + '\n' + fim, src: 'Fonte: ' + (pv ? 'previsão ' + pv.fonte + ' · ' : s ? '' : 'previsão Open-Meteo: sem leitura de hoje neste aparelho · ') + SNAP.fonte, actions: act(p, [['Telemetria', 'console']]).concat(pv ? [windy()] : []) };
    },
    canal16: function (p) {
      return { text: 'Em perigo grave e iminente: MAYDAY no canal 16 (156,800 MHz), em voz alta e devagar, até ter resposta.\n' + MMSI_RADIO + ' · indicativo: ' + INDICATIVO + ' · ' + min1(fabMod('vhf')) + '.\nRoteiro MAYDAY (' + ROTULO + '):\n' + (P.roteiro || []).join(' — ') + '.\n' + (P.panpan || 'Urgência sem perigo de vida: PAN-PAN ×3.'), src: FT.proto + ' · canal 16 e MMSI do rádio de bordo', actions: act(p, [['Abrir SOS', 'sos']]) };
    },
    // Checklists (F09): os itens do D.checklists, com a fonte e a verificação pelo quadro do instante (checklistResposta)
    checklist: function (p) { return checklistResposta('saida', p); },
    checklistChegada: function (p) { return checklistResposta('chegada', p); },
    checklistFundeio: function (p) { return checklistResposta('fundeio', p); },
    checklistAbastecimento: function (p) { return checklistResposta('abastecimento', p); },
    // A 1ª linha responde ao que foi perguntado: «quantos litros gastamos desde o último abastecimento?» abre com o consumido desde o abastecimento; as outras, com o consumo agora
    consumo: function (p, ctx, qq) {
      var ab = D.abastecimentos || [], i = vivo(), desde = / (?:desde|gastamos|gastos|gastou|consumimos|consumido|ultimo abastecimento) /.test(pad(qq || ''));
      var l0 = i ? 'Consumo agora (' + i.hora + '): ' + (i.txt.consumo || SD) + ' nos dois motores.' : 'Consumo observado (telemetria' + demo() + ' ' + CON.periodo + '):';
      var lc = '• cruzeiro — ' + CON.cruzeiro.lph + ' L/h (' + mil(CON.cruzeiro.rpm) + ' rpm · ' + CON.cruzeiro.nos + ' nós, dois motores)\n• marcha lenta — ' + nb(CON.lenta.lph) + ' L/h';
      var ld = 'Desde o abastecimento de ' + CON.desdeAbast.desde.slice(0, 5) + ': ≈ ' + litrosTxt(CON.desdeAbast.litros) + ' L (' + CON.desdeAbast.horas + ')';
      var la = ab.length ? '\nAbastecimentos registrados: ' + ab.map(function (a) { return a.d.slice(0, 5) + ' · ' + mil(a.litros) + ' L'; }).join(' · ') + '.' : '';
      return { text: (desde ? ld + (i ? ' — ' + i.hora : '') + '.\n' + l0 + '\n' + lc : l0 + '\n' + lc + '\n' + ld + '.') + la, src: 'Fonte: ' + CON.fonte + ' · ' + FT.abast.replace('Fonte: ', '') + comTele(), actions: act(p, [['Abastecimento', 'abast']]) };
    },
    tanques: function (p) { return { text: 'Tanques (' + quando() + '):\n• água doce ' + nb(T.agua) + ' %\n• águas cinzas ' + nb(T.cinzas) + ' %\n• águas negras ' + nb(T.negras) + ' %\n• diesel ' + SNAP.diesel + ' — ' + SNAP.dieselHora + '.', src: FT.tele + ' (diesel ' + (DI.hora || '') + ')', actions: act(p, [['Telemetria', 'console']]) }; },
    // Contatos: quem chamar. Os telefones ficam só neste aparelho (Equipe). Exceção da decisão (g): leva a situação de bordo sem posição.
    contatos: function (p, ctx) {
      var eq = D.equipe || {}, per = eq.perfis || [], ap = eq.apoio || [], f = loadEquipe().fones, cad = Object.keys(f).length;
      return { text: 'Acesso total: ' + per.map(function (x) { return x.nome + ' (' + x.papel + ')'; }).join(' · ') + '.\nApoio: ' + ap.map(function (a) { return min1(a.papel) + (a.para ? ' (' + a.para + ')' : ''); }).join(' · ') + '.\nTelefones: ' + (cad ? cad + ' cadastrado(s) neste aparelho — abra Equipe para ligar.' : 'ficam só neste aparelho (Equipe): cadastre ali para ligar direto.') + (ctx && ctx.semBordo ? '' : '\n' + linhaBordo()), src: 'Fonte: cadastro da equipe' + demo() + ' · telefones do aparelho', actions: act(p, [['Equipe e contatos', 'equipe']]) };
    },
    anomalias: function (p, ctx) {
      var pend = pendencias(ctx), mesmas = {}, app;   // F20: só as ABERTAS (as resolvidas por linha nova saem); as do aparelho com `pend` entram uma vez só
      pend.forEach(function (x) { if (x.origem === 'aparelho') mesmas[x.iso] = 1; });
      app = lerDiario(ctx).filter(function (e) { return /pend[eê]ncia|anomalia|A CONFIRMAR|A CONFERIR/i.test(e.t) && !tem(mesmas, e.iso); }).slice(0, 3);
      return { text: 'Pendências abertas (' + (pend.length + app.length) + '):\n' + pend.map(function (x) { return '• ' + x.d + ' · ' + x.sys + ' — ' + (x.origem === 'aparelho' ? String(x.t).slice(0, 110) + ' (app)' : x.t); }).concat(app.map(function (x) { return '• ' + x.d + ' · ' + (x.sys || 'Diário') + ' — ' + String(x.t).slice(0, 110) + ' (app)'; })).join('\n') + '\nAtrasadas na agenda: ' + atrasadas().length + ' (veja Manutenção).', src: FT.diario + ' · diário do app', actions: act(p, [['Abrir diário', 'diario'], ['Manutenção', 'manut']]) };
    },
    // Tendências (F11): os achados por regra fixa (preditivaLista), do mais grave ao estável; a 1ª linha, a falada, é o achado mais grave com a hora do instante — ou o que a pergunta nomeia («qual a
    // tendência do óleo?» abre com a pressão de óleo; se o nomeado está estável e outro pede atenção, a 1ª linha diz quantos). A lista de baixo segue a ordem de gravidade. Só lê: nada grava, nada abre.
    preditiva: function (p, ctx, q) {
      var i = vivo(), l = preditivaLista(), h = i ? ' às ' + i.hora : '', pedem = l.filter(function (a) { return a.nivel !== 'ok'; }).length, hist = histFonte();
      var ids = predFoco(q), topo = l.filter(function (a) { return ids.indexOf(a.id) !== -1; })[0] || l[0], n = l.length - 1;
      if (!l.length) return { text: 'Tendências' + h + ': ' + (sim() ? 'o aparelho ainda não tem histórico para calcular.' : SD + ' — sem histórico de cruzeiro neste aparelho.'), src: 'Fonte: nenhuma — sem histórico de cruzeiro neste aparelho', actions: act(p, [['Manutenção', 'manut']]) };
      return { text: 'Tendências' + h + ': ' + (pedem ? '' : 'nenhuma pede atenção. ') + topo.texto + (n ? ' Mais ' + n + (n === 1 ? ' achado' : ' achados') + ' na lista' + (topo.nivel === 'ok' && pedem ? ', ' + pedem + (pedem === 1 ? ' pede atenção.' : ' pedem atenção.') : '.') : '')
        + '\n' + l.map(function (a) { return '• ' + a.rotulo + ' · ' + a.sistema + ' — ' + a.texto + ' (' + a.fonte + ')'; }).join('\n'),
        src: 'Fonte: achados por regra fixa neste aparelho sobre ' + hist + ' · ' + FT.agenda.replace('Fonte: ', '') + comTele(), actions: act(p, [['Console', 'console'], ['Manutenção', 'manut']]) };
    },
    // Peças e estoque (F22): a lista (zeradas e no mínimo primeiro), as peças de uma tarefa da agenda ou as que o nome da pergunta cita; só lê, nunca grava (o −1 USADA é da tela)
    pecas: function (p, ctx, q) {
      var l = pecasLista(), tf = tarefasDaPergunta(q), acoes = act(p, [['Manutenção', 'manut'], ['Documentos', 'docs']]), src = 'Fonte: estoque de peças a bordo · cadastro do app';
      var onde = / (?:onde|cade) /.test(pad(q)), ord = { zero: 0, baixa: 1, ok: 2 }, linha = function (x) {
        var t = tarefasDaPeca(x);
        return '• ' + x.n + ' · ' + x.qtd + ' a bordo' + (x.min > 0 ? ' · mínimo ' + x.min : '') + (x.local ? ' · ' + x.local : '') + (x.nivel !== 'ok' ? ' — ' + x.st : '') + (t.length ? ' · para: ' + t.map(function (y) { return y.n + ' (' + y.prazo + ')'; }).join('; ') : '');
      };
      var resumo = function (xs) {
        var z = xs.filter(function (x) { return x.nivel === 'zero'; }).length, b = xs.filter(function (x) { return x.nivel === 'baixa'; }).length, ps = [];
        if (z) ps.push(z + (z === 1 ? ' zerada' : ' zeradas'));
        if (b) ps.push(b + ' no mínimo ou abaixo');
        return ps.length ? ' — ' + ps.join(' e ') + '.' : ', todas acima do mínimo.';
      };
      // a 1ª linha, a falada, diz QUAL peça e QUANTAS há («rotor do gerador, 0 a bordo, zerada, mínimo 1»): até 3 peças, cada uma; mais que isso, o total e as que pedem atenção (zeradas e no mínimo, até 3)
      var frase = function (x) {
        return min1(x.n) + ', ' + x.qtd + ' a bordo' + (x.nivel === 'zero' ? ', zerada' + (x.min > 0 ? ', mínimo ' + x.min : '') : x.nivel === 'baixa' ? (x.qtd < x.min ? ', abaixo do mínimo de ' + x.min : ', no mínimo') : x.min > 0 ? ', mínimo ' + x.min : '');
      };
      var corpo = function (xs) {
        var ps = xs.filter(function (x) { return x.nivel !== 'ok'; });
        if (xs.length <= 3) return xs.map(frase).join('; ') + '.';
        return xs.length + ' cadastradas' + (ps.length ? resumo(xs).replace(/\.$/, '') + ': ' + ps.slice(0, 3).map(frase).join('; ') + (ps.length > 3 ? ' e mais ' + (ps.length - 3) : '') + '.' : ', todas acima do mínimo.');
      };
      // «onde está / fica / guardamos / cadê <peça>?»: a 1ª linha, a falada, diz ONDE a peça é guardada (o local do cadastro) e quantas há (até 3 peças; mais que isso, a 1ª linha de sempre)
      var ondeFicam = function (xs) { return 'Onde ficam: ' + xs.map(function (x) { return min1(x.n) + ' — ' + (x.local || 'sem local cadastrado') + ' (' + x.qtd + ' a bordo' + (x.nivel === 'zero' ? ', zerada' : x.nivel === 'baixa' ? ', no mínimo ou abaixo' : '') + ')'; }).join('; ') + '.'; };
      if (!l.length) return { text: 'Não há peças cadastradas neste aparelho ainda — não invento estoque. Cadastre em Documentos: nome, quantas a bordo, mínimo, local e a tarefa da agenda que a usa.', src: 'Fonte: estoque de peças a bordo (vazio)', actions: acoes };
      if (tf.length) {
        var ids = tf.map(function (t) { return t.id; }), lig = l.filter(function (x) { return x.tarefas.some(function (t) { return ids.indexOf(t) !== -1; }); }).sort(function (a, b) { return ord[a.nivel] - ord[b.nivel]; });
        var nomes = tf.map(function (t) { return t.t; }).join(' e ');
        if (!lig.length) return { text: 'Nenhuma peça cadastrada para ' + min1(nomes) + '. Cadastre em Documentos a peça que ela usa.', src: src + ' · ' + FT.agenda.replace('Fonte: ', ''), actions: acoes };
        return { text: (onde && lig.length <= 3 ? ondeFicam(lig) : 'Peças para ' + min1(nomes).replace(/:\s*/g, ' — ') + ': ' + corpo(lig)) + '\n' + lig.map(linha).join('\n'), src: src + ' · ' + FT.agenda.replace('Fonte: ', ''), actions: acoes };
      }
      var nm = pecasDoNome(q, l), sai = src + ' · ' + FT.agenda.replace('Fonte: ', '');
      if (nm.lista.length) {
        nm.lista.sort(function (a, b) { return ord[a.nivel] - ord[b.nivel]; });
        return { text: (onde && nm.lista.length <= 3 ? ondeFicam(nm.lista) : 'Estoque de peças: ' + corpo(nm.lista)) + '\n' + nm.lista.map(linha).join('\n'), src: sai, actions: acoes };
      }
      var todas = l.slice().sort(function (a, b) { return ord[a.nivel] - ord[b.nivel]; });
      // (a palavra que a pessoa escreveu só é repetida se o app a conhece como coisa de bordo; «peças para o fim de semana» e «resumo das peças» abrem direto com a lista, sem negar nada)
      return { text: (nm.nome && nm.palavras.length ? 'Nenhuma peça cadastrada com «' + nm.palavras.join(' ') + '» no nome. ' : '') + 'Peças a bordo: ' + corpo(todas) + '\n' + todas.map(linha).join('\n'), src: sai, actions: acoes };   // (a 1ª linha, a falada, nomeia as zeradas e as no mínimo: «quais estão zeradas?» não responde só a contagem)
    },
    // Porão: o nível das bombas no quadro, a faixa do guia e o teste mensal; sem o dado do porão, SEM LEITURA (o caminho null)
    porao: function (p) {
      var t = tarefa('porao-teste'), niv = poraoTxt(), L = limitesDe('porao_bb_nivel'), ate = L && L.normal && typeof L.normal.ate === 'number' ? L.normal.ate : null, e = equip('porao');
      return { text: (niv ? 'Porão ' + (vivo() ? 'às ' + SNAP.quando : 'na ' + quando()) + ': nível ' + niv + (ate != null ? ' (normal até ' + nb(ate, 0) + ' cm)' : '') + '.' : 'Sem sensor de porão no barramento NMEA — SEM LEITURA.') + '\n' + (e ? fabMod('porao') + ': ligam sozinhas pelo sensor de nível (' + guia('g_porao') + ' §1–2).\n' : '') + 'Teste de bombas de porão e alarmes ' + (t ? prazoTxt(t) + ' (agenda: ' + t.quem + ' · ' + t.intervalo + ')' : SD) + '.\nAntes de sair: acione cada bomba manualmente e confira o alarme; registre o resultado no diário.', src: FT.agenda + ' · ' + SNAP.fonte, actions: act(p, [['Manutenção', 'manut']]) };
    },
    // Gerador: o estado e a hora na própria frase (a fala é a 1ª linha sem os parênteses: «ligado às 12:01:45», nunca «(ligado · … ao vivo …)»); sem o quadro vivo, a hora da leitura
    gerador: function (p, ctx, qq) { var r = tarefa('gerador-rotor'), rv = tarefa('gerador-revisao'), quand = vivo() ? 'às ' + SNAP.quando : 'na ' + quando(), sq = pad(qq || ''), f = has(sq, FALTA_PALAVRAS) ? (has(sq, ['rotor', 'impeller']) ? linhaFalta(r, 'a inspeção do rotor do gerador') : has(sq, ['revisao', 'oleo', 'filtro', 'troca', 'horas']) ? linhaFalta(rv, 'a revisão de óleo e filtros do gerador') : '') : ''; return { text: (f ? f + '\n' : '') + fabMod('gerador') + (G.estado ? ' ' + G.estado + ' ' + quand : ' · estado ' + SD) + (typeof G.kw === 'number' && G.estado !== 'desligado' ? ' · ' + nb(G.kw) + ' kW' : '') + ' · ' + horas(G.horas) + ' h.\nLigar: confira óleo, válvula de fundo e filtro de água salgada → segure PARTIDA → espere tensão e frequência estabilizarem → cargas uma a uma, climatização por último.\nDesligar: retire as cargas, 3 a 5 min sem carga, PARADA.' + (r ? '\n' + r.t + ': ' + prazoTxt(r) + '.' : '') + (rv && rv.horas ? ' Revisão (óleo e filtros): ' + (execTxt(rv) ? execTxt(rv) + '.' : rv.vence + ' ou ' + mil(rv.horas.limite) + ' h — faltam ' + nb(faltam(rv)) + ' h.') : ''), src: 'Fonte: ' + guia('g_gerador') + ' §1–4 · ' + FT.agenda.replace('Fonte: ', '') + (vivo() ? ' · horímetro: ' + SNAP.fonte : ' · horímetro na telemetria' + demo()), actions: act(p, [['Passo a passo', 'f4']]) }; },
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
    // A 1ª linha responde ao que foi perguntado: «quando vence o seguro?» abre com o seguro (o documento que a pergunta nomeia, e só um); sem documento nomeado, «Vencem primeiro»
    docsvenc: function (p, ctx, qq) {
      var segd = function (d) { return (D.equipamentos || []).some(function (e) { return e.seguranca && e.validade === d.id; }); };
      var todos = (D.documentos || []), segDocs = todos.filter(segd), ds = todos.filter(function (d) { return !segd(d); });
      var com = ds.filter(function (d) { return !isNaN(dnDe(d)); }).sort(function (a, b) { return dnDe(a) - dnDe(b); });
      var vence = com.filter(function (d) { return dnDe(d) <= 90; }), dia = com.filter(function (d) { return dnDe(d) > 90; }), sem = ds.filter(function (d) { return d.st === SD; }), conf = ds.filter(function (d) { return /A CONF/.test(d.st); });
      var prazo = function (d) { var n = dnDe(d); return n < 0 ? 'VENCIDO há ' + (-n) + (n === -1 ? ' dia' : ' dias') : 'D-' + n; };
      var alvo = docPedido(com, qq), l1 = alvo ? alvo.n + ' — ' + alvo.vence + ' (' + prazo(alvo) + ').\n' : '';
      return { text: l1 + 'Vencem primeiro:\n' + (vence.length ? vence.map(function (d) { return '• ' + d.n + ' — ' + d.vence + ' (' + prazo(d) + ')'; }).join('\n') : '• nenhum nos próximos 90 dias') + '\nEm dia: ' + dia.map(function (d) { return min1(d.n) + ' até ' + d.vence; }).join(' · ') + '.' + (sem.length ? '\n' + SD + ': ' + sem.map(function (d) { return d.n; }).join(' · ') + '.' : '') + (conf.length ? '\nA CONFERIR: ' + conf.map(function (d) { return d.n; }).join(' · ') + '.' : '') + (segDocs.length ? '\nSegurança: ' + segDocs.map(function (d) { return min1(d.n) + ' — ' + NOTA_ETIQUETA; }).join(' · ') + '.' : ''), src: FT.docs, actions: act(p, [['Documentos', 'docs']]) };
    },
    horimetros: function (p, ctx, qq) { var o = tarefa('motores-oleo'), rv = tarefa('gerador-revisao'), oEx = execTxt(o), rvEx = execTxt(rv), l1 = has(pad(qq || ''), FALTA_PALAVRAS) || has(pad(qq || ''), PROX_TROCA) ? linhaFalta(o, 'a troca de óleo e filtros dos motores') : ''; return { text: (l1 ? l1 + '\n' : '') + 'Horímetros ' + (vivo() ? 'às ' + SNAP.quando + ' (motores ' + (M.estado || SD) + ')' : '(motores: última leitura ligados ' + (M.hora || SD) + ' · gerador ' + (G.hora || SD) + ')') + ':\n• motor BB ' + horas(M.horimetro && M.horimetro[0]) + ' h\n• motor BE ' + horas(M.horimetro && M.horimetro[1]) + ' h\n• gerador ' + horas(G.horas) + ' h\n' + (oEx ? 'Troca de óleo dos motores: ' + oEx + '.' : 'Próxima troca de óleo dos motores: ' + (o ? o.vence + ' (' + prazoTxt(o).split(' · ')[0] + ') ou ' + o.horas.limite + ' h — faltam ' + nb(faltam(o)) + ' h; o que vier antes.' : SD)) + (rv ? '\nRevisão do gerador: ' + (rvEx ? rvEx + '.' : rv.vence + ' (' + prazoTxt(rv).split(' · ')[0] + ') ou ' + mil(rv.horas.limite) + ' h.') : ''), src: FT.tele + ' · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['Manutenção', 'manut']]) }; },
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
    oleoLeitura: function (p, ctx, q) {
      var i = vivo(), rpm = (vivo() ? vivo().txt.rpm || '— rpm' : (M.rpm ? M.rpm.join('/') : '—') + ' rpm'), fx = faixaOleo(i ? i.q.motor_bb_rpm : (M.rpm && typeof M.rpm[0] === 'number' ? M.rpm[0] : null)), lx = i ? ladoSeguinte(q) : null;
      var ol = M.oleo ? M.oleo.map(function (x) { return nb(x); }).join('/') : '—', ar = M.arref ? M.arref.join('/') : '—';
      return { text: (i ? (lx && campoTxt(i, 'motor_' + lx + '_oleo_bar') !== null ? 'Pressão do óleo do motor ' + lx.toUpperCase() + ' agora (' + i.hora + '): ' + campoTxt(i, 'motor_' + lx + '_oleo_bar') + ' bar, com o motor a ' + (campoTxt(i, 'motor_' + lx + '_rpm') || '—') + ' rpm.' : 'Pressão do óleo agora (' + i.hora + '): ' + (i.txt.oleo || '—') + ', com os motores a ' + rpm + '.') + '\nArrefecimento ' + (i.txt.arref || '—') + alarmesCl(i, ' · alarmes: ') + '.' : 'Motores ' + (M.estado || SD) + ' (' + quando() + '). Pressão do óleo na última leitura com motores ligados ' + (M.hora || SD) + ': ' + ol + ' bar · ' + rpm + (M.marcha ? ' em ' + M.marcha : '') + ' · arrefecimento ' + ar + ' °C.') + (fx ? '\nFaixa normal: ' + fx + '.' : '') + '\nSe cair abaixo da faixa ou o alarme acender, pergunte “pressão de óleo baixa” para o passo a passo.', src: FT.tele + ' · ' + guia('g_motores'), actions: act(p, [['Telemetria', 'console'], ['Pressão baixa: o que fazer', askHref(p, 'Pressão de óleo baixa: o que verificar primeiro?')]]) };
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
    diarioLer: function (p, ctx) {
      var mine = lerDiario(ctx), fonte = diarioFonte();
      var lines = mine.slice(0, 3).map(function (e) { return '• ' + (e.d || '') + ' · ' + (e.sys || 'Diário') + ' — ' + String(e.t || '').slice(0, 110) + ' (app)'; });
      var fixed = fonte.map(function (e) { return '• ' + e.d + ' ' + e.h + ' · ' + e.sys + ' — ' + e.t.slice(0, 110); });
      // a 1ª linha é a resposta numa frase falável (quantos registros e quantas pendências); os últimos registros vêm embaixo
      var tot = fonte.length + mine.length, pe = pendencias(ctx).length;
      return { text: 'Diário de bordo: ' + tot + (tot === 1 ? ' registro' : ' registros') + ' e ' + pe + (pe === 1 ? ' pendência aberta' : ' pendências abertas') + '.\nÚltimos registros:\n' + lines.concat(fixed).slice(0, 4).join('\n') + '\nPara registrar, diga “registre no diário…” ou toque no atalho DIÁRIO DE BORDO.', src: FT.diario + ' + registros do app', actions: act(p, [['Abrir diário', 'diario']]) };
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
      var i = vivo(), q = i && i.q, R = rotaDoPlano(), wp = i && /waypoint|proximo ponto/.test(norm(qq)), pc = i && /percorrid|navegad|odometro|navegamos|percorremos|resumo d|balanco d|relatorio d|como foi|como esta indo|como esta sendo|como foram/.test(norm(qq)), dest, ponto, perc, fonte, an, cit, outro = null;
      if (!i || typeof q.destino !== 'string') {
        return { text: sim() && i ? 'O quadro de ' + i.hora + ' não trouxe destino nem chegada prevista — confira a rota no plotter.' : 'Destino, chegada prevista e próximo ponto: ' + SD + ' (nenhuma rota ativa na ' + quando() + ') — confira a rota no plotter.',
          src: 'Fonte: ' + (i ? i.fonteTxt : SNAP.fonte), actions: act(p, [['Destinos', askHref(p, 'Para onde vamos hoje?')]]) };
      }
      an = (D.replay && D.replay.ancora_hora) || '07:00';
      dest = 'Chegada prevista em ' + q.destino + (q.eta ? ' às ' + q.eta : '') + (campoTxt(i, 'destino_mn') ? ', a ' + campoTxt(i, 'destino_mn') + ' mn' : '');
      ponto = q.wp_proximo ? 'Próximo ponto: ' + q.wp_proximo + (campoTxt(i, 'wp_mn') ? ', a ' + campoTxt(i, 'wp_mn') + ' mn' : '') : '';
      // O ponto que a pergunta cita nem é o destino nem o próximo ponto («quanto falta para o Estaleirinho?» com o barco voltando à Barra Sul): a 1ª linha diz isso e dá a chegada que o app tem, a do destino —
      // nunca a chegada de outro ponto como se fosse a do citado. O app só calcula a chegada no destino e no próximo ponto.
      cit = pontoCitado(qq || '');
      if (cit) { var nc = function (x) { return norm(String(x || '').split('(')[0]).replace(/\s+/g, ' ').trim(); };
        if (nc(cit) === nc(q.wp_proximo) && nc(cit) !== nc(q.destino)) wp = true;
        else if (nc(cit) !== nc(q.destino)) outro = cit; }
      perc = campoTxt(i, 'distancia_mn') ? 'Percorrido desde as ' + an + ': ' + campoTxt(i, 'distancia_mn') + ' mn' + (i.txt.sog ? ' · velocidade ' + i.txt.sog : '') + '.' : '';
      fonte = 'Fonte: ' + i.fonteTxt + ' · ' + (R && R.fonte ? R.fonte : 'rota em andamento');
      if (outro) {
        var dmn = campoTxt(i, 'destino_mn');
        return { text: 'O destino agora é ' + q.destino + (q.eta ? ', com chegada prevista às ' + q.eta : '') + (dmn ? ', a ' + dmn + ' mn' : '') + '; ' + outro + ' não é o destino nem o próximo ponto — ' + i.hora + '.' + (ponto ? '\n' + ponto + '.' : '') + (perc ? '\n' + perc : '')
          + '\nO app calcula a chegada só no destino e no próximo ponto da rota.', src: fonte, actions: act(p, [['Destinos', askHref(p, 'Para onde vamos hoje?')], ['Telemetria', 'console']]) };
      }
      return { text: pc && perc ? perc.replace(/\.$/, '') + ' — ' + i.hora + '.\n' + dest + '.' + (ponto ? '\n' + ponto + '.' : '')
        : (wp && ponto ? ponto + ' — ' + i.hora + '.\n' + dest + '.' : dest + ' — ' + i.hora + '.' + (ponto ? '\n' + ponto + '.' : '')) + (perc ? '\n' + perc : ''), src: fonte, actions: act(p, [['Destinos', askHref(p, 'Para onde vamos hoje?')], ['Telemetria', 'console']]) };
    },
    // Alarmes ativos do instante (a CapitaoAlertas quando a tela a traz, senão os do quadro): o nível e o texto na 1ª linha, o que verificar primeiro (os passos do guia, do catálogo D.replay.alertas) depois.
    // O alarme de uma volta do replay é sempre AVISO (o crítico só com cenario 'alarme-critico', desligado): esta resposta nunca abre o SOS nem a C3 sozinha.
    alarmes: function (p, ctx, qq) {
      var i = vivo(), lista = i ? alarmesDetalhe(i) : null, ale = catalogoAlertas(), n, partes = [], link = null, soa = alarmeSoando(qq || ''), conf = 'Confira também o painel dos motores e o plotter: o app só lê os alarmes do quadro de leitura.';
      if (!i || !lista) {
        return { text: sim() && i ? 'O coletor não trouxe a lista de alarmes às ' + i.hora + ' — confira o painel dos motores e o plotter.' : 'Alarmes: ' + SL + ' (o coletor não reporta alarmes) na ' + quando() + ' — confira o painel dos motores e o plotter.',
          src: 'Fonte: ' + (i ? i.fonteTxt : SNAP.fonte), actions: act(p, [['Telemetria', 'console'], ['Manutenção', 'manut']]) };
      }
      n = lista.length;
      if (!n) return { text: soa ? 'Confira o painel dos motores e o plotter: às ' + i.hora + ' o quadro de leitura não traz alarme ativo, e o app só lê os alarmes do quadro.' : 'Nenhum alarme ativo às ' + i.hora + '.', src: 'Fonte: ' + i.fonteTxt + ' · limites do guia de bordo', actions: act(p, [['Telemetria', 'console'], ['Manutenção', 'manut']]) };
      lista.forEach(function (a) {
        var c = ale[a.id] || {};
        partes.push((a.titulo || c.titulo || 'Alarme') + (a.hora ? ' (desde ' + a.hora + ')' : '') + ' — o que verificar primeiro:\n' + numerados(a.passos && a.passos.length ? a.passos : c.passos || []));
        if (!link && a.detalhe) link = a.detalhe;
      });
      return { text: (n === 1 ? 'Há 1 alarme ativo' : 'Há ' + n + ' alarmes ativos') + ' às ' + i.hora + ' — ' + i.txt.alarmes + '.\n' + partes.join('\n') + (soa ? '\n' + conf : ''),
        src: 'Fonte: ' + i.fonteTxt + ' · ' + lista.map(function (a) { return a.fonte || (ale[a.id] && ale[a.id].fonte) || ''; }).filter(function (x, k, v) { return x && v.indexOf(x) === k; }).join(' · '),
        actions: (link ? [{ l: 'Ver o alerta', href: link }] : []).concat(act(p, [['Telemetria', 'console'], ['Manutenção', 'manut']])) };
    },
    // Temperatura dos motores (o arrefecimento): a leitura, a faixa normal do guia dos motores §9 e a tendência de 30 s; fora da faixa, o alarme e o que verificar primeiro. Sem quadro vivo: a última leitura com motores ligados.
    arrefecimento: function (p, ctx, q) {
      var i = vivo(), A = window.CapitaoAgora, L = limitesDe('motor_bb_arref_c'), ate = L && L.normal && typeof L.normal.ate === 'number' ? L.normal.ate : null, fx = ate != null ? 'Faixa normal: até ' + nb(ate, 0) + ' °C (' + L.fonte + ').' : '';
      var ale = catalogoAlertas(), alr, lista, niv, fora = [], tend, l1, pass = '', lx;
      if (!i) {
        return { text: 'Arrefecimento ' + (M.arref ? M.arref.join('/') + ' °C na última leitura com motores ligados ' + (M.hora || SD) + ' (motores ' + (M.estado || SD) + ', ' + quando() + ').' : SL + ' (' + quando() + ').') + (fx ? '\n' + fx : ''),
          src: FT.tele + ' · ' + guia('g_motores') + ' §9', actions: act(p, [['Motores', askHref(p, 'motores')], ['Telemetria', 'console']]) };
      }
      ['bb', 'be'].forEach(function (l) {
        var v = i.q['motor_' + l + '_arref_c'];
        try { niv = A.nivel('motor_' + l + '_arref_c', i.q); } catch (e) { niv = null; }
        if (niv && niv.nivel && niv.nivel !== 'normal') fora.push(l.toUpperCase() + (typeof niv.limite === 'number' ? (v > niv.limite ? ' acima de ' : ' abaixo de ') + nb(niv.limite, 0) + ' °C' : ' fora da faixa') + ' (' + (niv.nivel === 'critico' ? 'CRÍTICO' : 'AVISO') + ')');
      });
      lx = ladoSeguinte(q);
      l1 = i.txt.arref ? 'Arrefecimento ' + (lx && campoTxt(i, 'motor_' + lx + '_arref_c') !== null ? 'do motor ' + lx.toUpperCase() + ' ' + campoTxt(i, 'motor_' + lx + '_arref_c') + ' °C (o outro lado: ' + (lx === 'be' ? 'BB ' + campoTxt(i, 'motor_bb_arref_c') : 'BE ' + campoTxt(i, 'motor_be_arref_c')) + ' °C)' : i.txt.arref) + ' às ' + i.hora + (fora.length ? ': ' + fora.join(' e ') : ate != null && i.q.motor_bb_rpm > 0 ? ', dentro da faixa normal (até ' + nb(ate, 0) + ' °C)' : '') + '.' : 'O quadro de ' + i.hora + ' não trouxe a temperatura dos motores.';
      tend = i.tend && 'motor_bb_arref_c' in i.tend && 'motor_be_arref_c' in i.tend ? 'Nos últimos 30 s: BB ' + sinal(i.tend.motor_bb_arref_c, 1) + ' · BE ' + sinal(i.tend.motor_be_arref_c, 1) + ' °C.' : '';
      lista = alarmesDetalhe(i) || [];
      alr = lista.filter(function (a) { return /arref/.test(a.campo || a.id || ''); });
      alr.forEach(function (a) { var c = ale[a.id] || {}; pass += '\n' + (a.titulo || c.titulo || 'Alarme') + ' — o que verificar primeiro:\n' + numerados(a.passos && a.passos.length ? a.passos : c.passos || []); });
      return { text: l1 + (tend ? '\n' + tend : '') + (fx ? '\n' + fx : '') + pass, src: 'Fonte: ' + i.fonteTxt + ' · ' + (L && L.fonte ? L.fonte : guia('g_motores') + ' §9'), actions: act(p, [['Motores', askHref(p, 'motores')], ['Telemetria', 'console']]) };
    },
    // A leitura pontual do quadro (a pergunta de UM dado: barômetro, satélites, inclinação, marcha, piloto, radar): a 1ª linha é o dado com a hora; o quadro não traz o estado do piloto (engajado ou em espera)
    leituraBordo: function (p, ctx, qq) {
      var i = vivo(), q = i && i.q, t = i && i.txt, k = leituraBordoDe(pad(qq || '')), l = null, fim = i ? ' — ' + i.hora + '.' : '';
      if (!i) return ANSWERS.telemetria(p, ctx, qq);
      if (k === 'pressao') l = t.pressao ? 'Barômetro a bordo agora: ' + t.pressao + fim : 'O barômetro não trouxe leitura às ' + i.hora + '.';
      else if (k === 'satelites') l = typeof q.gps_satelites === 'number' ? 'GPS com ' + q.gps_satelites + (q.gps_satelites === 1 ? ' satélite' : ' satélites') + fim : 'O GPS não trouxe a contagem de satélites às ' + i.hora + '.';
      else if (k === 'inclinacao') l = t.inclinacao ? 'Inclinação a bordo agora: ' + t.inclinacao + fim : 'Os sensores de inclinação não trouxeram leitura às ' + i.hora + '.';
      else if (k === 'marcha') l = q.marcha ? 'Marcha: ' + q.marcha + fim : 'O quadro não trouxe a marcha às ' + i.hora + '.';
      else if (k === 'piloto') {   // a pergunta do ESTADO («está ligado?», «engajado?») não recebe o rumo como se fosse a resposta: o quadro só traz o rumo do piloto, não se ele está engajado
        if (!t.piloto) l = 'O quadro não trouxe o rumo do piloto às ' + i.hora + '.';
        else if (ESTADO_PILOTO.test(pad(qq || ''))) l = 'O quadro traz o rumo do piloto automático, ' + t.piloto + ', mas não diz se está engajado ou em espera' + fim + '\nPara saber, veja no controle do piloto.';
        else l = 'Piloto automático com rumo ' + t.piloto + fim + '\nO quadro não traz se está engajado ou em espera: veja no controle do piloto.';
      }
      else if (k === 'radar') l = typeof q.radar_ativo === 'boolean' ? 'Radar ' + (q.radar_ativo ? 'ligado' : 'desligado') + fim : 'O quadro não trouxe o estado do radar às ' + i.hora + '.';
      return { text: l, src: 'Fonte: ' + i.fonteTxt + ' · sensor de bordo', actions: act(p, [['Telemetria', 'console'], ['FAQ eletrônicos', 'f3']]) };
    },
    // Estado do mar a bordo (as ondas do quadro): só «a bordo agora», nunca previsão (§2.5: a previsão de mar é do mundo real, e o app não a tem)
    ondas: function (p) {
      var i = vivo(), o = i ? i.txt.ondas : null, v = i ? i.txt.vento : typeof S.vento === 'number' ? nb(S.vento) + ' nós de ' + grau3(S.ventoDe) : null, s = sim();
      return { text: (o ? 'Ondas de ' + o + ' a bordo agora — ' + i.hora + '.' : s && i ? 'O sensor de ondas não trouxe leitura às ' + i.hora + '.' : 'Ondas a bordo: ' + SL + ' (o coletor não reporta a altura da onda) na ' + quando() + '.')
        + (v ? '\nVento verdadeiro ' + v + ', a bordo agora.' : '') + '\n' + (s ? 'Previsão de mar: o app não tem previsão de ondas — confira a previsão da Marinha antes de sair.' : 'Previsão de mar (ondas): ' + SD + ' no app — confira a previsão da Marinha antes de sair.'),
        src: 'Fonte: ' + (i ? i.fonteTxt : SNAP.fonte) + ' · a bordo, não é previsão', actions: act(p, [['Clima', askHref(p, 'Clima')], ['Telemetria', 'console']]) };
    },
    // Temperatura da água do mar a bordo (o sensor do quadro, preso à máxima e à mínima do dia da previsão real quando o aparelho a leu)
    // A 1ª linha responde ao que foi perguntado: a temperatura do AR («qual a temperatura do ar?», «… — e do ar?») abre com o ar externo; a da água (e as perguntas sem ar) abrem com a água do mar
    temperaturaAgua: function (p, ctx, q) {
      var i = vivo(), ag = i ? i.txt.agua : typeof S.agua === 'number' ? nb(S.agua) + ' °C' : null, ar = i ? i.txt.ar : typeof S.ar === 'number' ? nb(S.ar) + ' °C' : null, foco = focoArAgua(q);
      var lAgua = ag ? 'Água do mar a ' + ag + ' a bordo agora' + (i ? ' — ' + i.hora : ' (' + quando() + ')') + '.' : sim() && i ? 'O sensor de temperatura da água não trouxe leitura às ' + i.hora + '.' : 'Temperatura da água: ' + SL + ' (' + quando() + ').';
      if (foco === 'ar' && ar) return { text: 'Ar externo a ' + ar + ' a bordo agora' + (i ? ' — ' + i.hora : ' (' + quando() + ')') + '.' + (ag ? '\nÁgua do mar a ' + ag + '.' : ''),
        src: 'Fonte: ' + (i ? i.fonteTxt : SNAP.fonte) + ' · sensor de bordo, não é previsão', actions: act(p, [['Clima', askHref(p, 'Clima')], ['Telemetria', 'console']]) };
      return { text: lAgua + (ar ? '\nAr externo ' + ar + '.' : ''),
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
    mmsi: function (p, ctx, qq) {
      var pq = pad(qq || ''), ind = has(pq, ['indicativo', 'call sign', 'callsign']),   // («qual o MMSI e o indicativo?»: o indicativo nunca é gerado, é o da Licença de Estação)
        cad = !EM_SOS && mmsiNeutra(pq);   // (o do cadastro do app só vai para a pergunta NEUTRA do número («qual o MMSI do barco?»): perto de «colocar», «digitar», «cadastrar», do rádio, do AIS ou do plotter, só o da etiqueta)
      return { text: MMSI_USO + (ind ? ' Indicativo: ' + INDICATIVO + '.' : '') + (cad ? '\nCadastro do app: ' + mmsiNum() + '.' : ''), src: FT.proto + (cad ? ' · ' + (E.fonte || 'cadastro da embarcação') : ''), actions: act(p, [['Abrir SOS', 'sos'], ['Documentos', 'docs']]) };
    },
    // AIS: o transponder do cadastro e os alvos do quadro; a pergunta de procedimento (como, código, onde fica…) vai ao guia dele (GENERICAS/FAMILIA)
    ais: function (p) {
      if (EM_SOS) return { text: 'AIS: os alvos aparecem no plotter, com nome, rumo e velocidade.', src: 'Fonte: Guia de bordo — AIS §1', actions: [] };   // no SOS o cérebro não lê o cadastro de equipamentos nem o quadro
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
  // o banco de bateria que a pergunta pede: a fala nova da pergunta continuada («… — e a de partida?») ou, sem continuação, a pergunta inteira; serviço e partida juntos (ou nenhum) = null
  function bancoPedido(q) {
    var t = String(q || ''), k = t.lastIndexOf(' — '), n = pad(k < 0 ? t : t.slice(k + 3)), pt = / partida /.test(n), sv = / servico /.test(n);
    return pt && !sv ? 'partida' : sv && !pt ? 'servico' : !pt && !sv && / (?:12 ?v|12 volts?) /.test(n) ? '12' : null;
  }
  // a temperatura que a pergunta pede: «do ar» (o ar externo) sem a água nem o mar; a pergunta da água (e a sem ar) = null
  function focoArAgua(q) {
    var t = String(q || ''), k = t.lastIndexOf(' — '), n = pad(k < 0 ? t : t.slice(k + 3));
    return / (?:ar|la fora|fora) /.test(n) && !/ (?:agua|mar) /.test(n) ? 'ar' : null;
  }
  var VIVO = {
    // a 1ª linha é a resposta numa frase falável (diesel, água doce, cinzas e negras, com a hora); as linhas de baixo são o detalhe
    tanques: function (i) { var q = i.q; return { text: 'Tanques às ' + i.hora + ': ' + (i.txt.diesel ? 'diesel ' + i.txt.diesel + ' · ' : '') + 'água doce ' + nb(q.tanque_agua_pct) + ' % · águas cinzas ' + nb(q.tanque_cinzas_pct) + ' % · águas negras ' + nb(q.tanque_negras_pct) + ' %.\n• água doce ' + nb(q.tanque_agua_pct) + ' %\n• águas cinzas ' + nb(q.tanque_cinzas_pct) + ' %' + (q.tanque_cinzas_pct > 70 ? ' — atenção: programar esgoto' : '') + '\n• águas negras ' + nb(q.tanque_negras_pct) + ' %' + (q.tanque_negras_pct > 70 ? ' — atenção: programar esgoto' : '') + '\n• diesel: ' + SNAP.diesel + ' — ' + SNAP.dieselHora + '.' }; },
    // o banco pedido abre a linha (partida, serviço ou 12 V; a fala nova de «… — e a de partida?» é a que vale): sem banco na pergunta, a de sempre
    eletrico: function (i, base, qq) {
      var q = i.q, sv = nb(q.bateria_0_tensao_v, 2), pt = nb(q.bateria_1_tensao_v, 2), d12 = nb(q.bateria_2_tensao_v, 2), f = bancoPedido(qq), b24 = 'banco 24 V ' + sv + ' V', b12 = 'banco 12 V ' + d12 + ' V',
        l1 = f === 'partida' ? 'banco 24 V de partida ' + pt + ' V · banco 24 V de serviço ' + sv + ' V · ' + b12 : f === 'servico' ? 'banco 24 V de serviço ' + sv + ' V · banco 24 V de partida ' + pt + ' V · ' + b12 : f === '12' ? b12 + ' · ' + b24 : b24 + ' · ' + b12;
      return { text: 'Baterias agora: ' + l1 + ' (ao vivo ' + i.hora + ').\n' + base.text.split('\n').slice(2).join('\n') };
    },
    estabilizador: function (i, base) { var q = i.q; return { text: 'Seakeeper agora: ' + (typeof q.seakeeper_ativo !== 'boolean' ? 'SEM LEITURA' : q.seakeeper_ativo ? 'LIGADO' + (typeof q.seakeeper_volante_rpm === 'number' ? ' · volante ' + mil(q.seakeeper_volante_rpm) + ' rpm (' + nb(q.seakeeper_volante_pct, 0) + ' %)' : '') : 'desligado') + ' · ao vivo ' + i.hora + '.\n' + base.text.split('\n').slice(1).join('\n') }; }
  };
  Object.keys(VIVO).forEach(function (k) {
    var pronta = ANSWERS[k]; if (!pronta) return;
    ANSWERS[k] = function (p, ctx, q) {
      var base = pronta(p, ctx, q), i = vivo(); if (!i) return base;
      var r = VIVO[k](i, base, q);
      return { text: r.text, src: 'Fonte: ' + i.fonteTxt, actions: base.actions };
    };
  });
  // as chaves de ANSWERS (o teste varre uma pergunta de cada) e as que não levam a hora do instante na fonte (emergência, diagnóstico, saudação, checklists, registro)
  // F12: os alarmes que o usuário pediu e estão ATIVOS agora entram na resposta dos alarmes (os do barco continuam como estavam); sem alarme pedido ativo, a resposta é a de sempre, palavra por palavra
  (function () {
    var alarmes0 = ANSWERS.alarmes;
    ANSWERS.alarmes = function (p, ctx, qq) {
      var r = alarmes0(p, ctx, qq), pa = almAtivos(), i, lista, cab;
      if (!pa.length) return r;
      i = vivo(); lista = pa.map(function (x) { return '• ' + x.texto + ' — desde ' + x.hora; }).join('\n');
      cab = pa.length === 1 ? 'Há 1 alarme pedido por você ativo' : 'Há ' + pa.length + ' alarmes pedidos por você ativos';
      if (/^Nenhum alarme ativo às /.test(r.text)) r.text = r.text.replace(/^Nenhum alarme ativo às ([0-9:]+)\./, 'Nenhum alarme do barco ativo às $1; ' + cab.charAt(0).toLowerCase() + cab.slice(1) + ':') + '\n' + lista;
      else r.text = r.text + '\n' + cab + (i ? ' às ' + i.hora : '') + ':\n' + lista;
      r.src = (r.src || '') + ' · alarmes pedidos neste aparelho';
      return r;
    };
  })();
  var CHAVES = Object.keys(ANSWERS);
  // AIS: a pergunta de status («quantos alvos?», «tem AIS?», «está ligado?») fica na resposta pronta; qualquer outra (modo silencioso, identificação, alvos no plotter) vai ao trecho do g_ais quando ele serve
  var AIS_STATUS = /\b(?:quantos?|quantas?|quais|tem|temos|ha|algum|alguns|agora|ligado|ligada|funcionando|recebendo|vendo)\b/;
  // (a maré é do mundo real, §2.5: a hora dela é a da leitura salva, «lida às HH:MM» na fonte; o instante do replay nunca entra na fonte da maré)
  var SEM_HORA_NA_FONTE = { sos: 1, oleo: 1, canal16: 1, epirb: 1, seafire: 1, salvatagem: 1, mmsi: 1, diagnostico: 1, saudacao: 1, checklist: 1, checklistChegada: 1, diario: 1, diarioPede: 1, relatoRegistra: 1, relatoCancela: 1, relatoVerifica: 1, mare: 1 };
  SEM_HORA_NA_FONTE.sobreDados = 1;
  // P3G: as respostas de gestão (agendar e confirmar, apagar alarme, cancelar, desfazer, o que o app faz) não leem o quadro: sem «consultado às»; o pedido e a lista dos alarmes pedidos, que leem, trazem a hora no texto
  ['agendar', 'ticketConfirma', 'ticketRecusa', 'ticketDesfaz', 'alarmeCancela', 'alarmeApaga', 'capacidades'].forEach(function (k) { SEM_HORA_NA_FONTE[k] = 1; });   // (a frase padrão e a fonte «este aparelho · modo de apresentação» não levam o «consultado às»)

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
  // sobreDados (§2.6): pergunta direta sobre a autenticidade. ` real `, ` reais `, ` de verdade `, ` verdadeir… `, ` falso ` e ` fake ` são medida ou outro sentido em muita pergunta de bordo («velocidade real», «diesel real do
  // barco», «profundidade real», «em tempo real», «em reais», «norte verdadeiro», «alarme falso», «quanto diesel tem de verdade»): só valem como PREDICADO («é real?», «são reais?», «a lancha é real?», «você é uma IA de verdade?»,
  // «esses dados são de fato reais, certo?»: o verbo, até 3 palavras e o «real» fechando a pergunta, AUT_PRED), como o nome dos dados («dados reais?», «você usa dados reais?», «um barco real?»: AUT_NOME) ou na ordem
  // invertida («são reais esses dados?», AUT_INV). As palavras sem outro sentido (simulado, fictício, demonstração, inventado, de mentira) valem em qualquer posição. «Quanto/qual/quais», «em reais», «tempo real» e a
  // medida colada ao «real» («velocidade real», «consumo real») são a pergunta da medida, nunca a da autenticidade. Equipamento, salvatagem, EPIRB, Seafire, extintor, rádio e dinheiro nunca são a pergunta sobre os dados (nenhuma palavra deles está na lista branca da revisão 4, logo a sobreDados os deixa de fora).
  var AUT_FORTE = [' simulad', ' simulac', ' simulam ', ' simula ', ' simulou ', ' simuland', ' simulador', ' fictici', ' demo ', ' demonstracao ', ' inventad', ' inventou ', ' inventam ', ' inventaram ', ' de mentira '];
  var AUT_EXISTE = [' o barco existe ', ' a embarcacao existe ', ' isso existe ', ' esse barco existe ', ' este barco existe ', ' a lancha existe ', ' essa lancha existe ', ' essa embarcacao existe ', ' existe de verdade ', ' voce existe '];
  var AUT_ALVO = [' dado ', ' dados ', ' leitura ', ' leituras ', ' valores ', ' numeros ', ' telemetria ', ' isso ', ' isto ', ' barco ', ' embarcacao ', ' navegacao ', ' app ',
    ' alarme ', ' alarmes ', ' alerta ', ' alertas ', ' sensor ', ' sensores ', ' gps ', ' posicao ', ' rota ', ' viagem ',
    ' lancha ', ' lanchas ', ' voce ', ' vc ', ' capitao ', ' ia ', ' sistema ', ' aplicativo ', ' informacoes ', ' diesel ', ' combustivel ', ' velocidade ', ' rumo ', ' vento ', ' ondas ', ' profundidade ',
    ' consumo ', ' autonomia ', ' temperatura ', ' calado ', ' horimetros '];
  // (revisão 3) o alarme, o alerta, o sensor e o GPS com «falso/fake» são o falso alarme, nunca a autenticidade; «alarme/alerta/sensor DE <coisa>» é o equipamento (o guia), e quem pede ajuda ou diz que é risco não recebe a frase de apresentação
  var AUT_SENSOR = [' alarme ', ' alarmes ', ' alerta ', ' alertas ', ' sensor ', ' sensores ', ' gps '];
  var AUT_FALSO = / (?:fals[oa]s?|fake) /;
  var AUT_SENSOR_DE = / (?:alarmes?|alertas?|sensor(?:es)?) d[aeo]s? /;
  // o «real» da pergunta: as palavras da autenticidade que também são medida (real, reais, de verdade, verdadeiro) ou outro sentido (falso, fake)
  var AUT_AW = '(?:real|reais|de verdade|verdadeir[oa]s?|fals[oa]s?|fake)';
  var AUT_COP = '(?:e|eh|sao|foi|era|eram|seria|seriam|sera|serao|ser|parece|parecem|esta|estao|ta|tao|estava|estavam)';
  // o que pode vir depois do «real»: «certo», «mesmo», «né», «de verdade» (a cauda «ou simulado» é da ordem invertida e das palavras fortes)
  var AUT_CAUDA = '(?: (?:mesmo|ne|certo|de fato|de verdade|hein|ou nao|nao e|nao))*';
  var AUT_PRED = new RegExp(' ' + AUT_COP + ' (?:[a-z0-9]+ ){0,3}' + AUT_AW + AUT_CAUDA + ' $');
  var AUT_NOME = new RegExp(' (?:dado|dados|leitura|leituras|numeros|valores|informacoes|telemetria|navegacao|viagem|barco|embarcacao|lancha|app|aplicativo|sistema) ' + AUT_AW + AUT_CAUDA + ' $');
  var AUT_INV = new RegExp(' ' + AUT_COP + ' ' + AUT_AW + '(?: [a-z0-9]+){1,3} $');
  // «o que é real aqui?», «estamos navegando de verdade?»: sem a palavra do alvo
  var AUT_QUE_E = / (?:o que|oque|oq) (?:e|eh) (?:real|de verdade|verdadeir[oa]|simulad[oa]|fals[oa]|fake)(?: (?:aqui|ai|nisso|nisto|disso|no app|neste app|nesse app|a bordo|no barco))* $/;
  var AUT_NAVEGANDO = / (?:navegando|navegamos|viajando|viajamos) de verdade /;
  // a forma curta, sem a palavra do alvo: «é real?», «é de verdade?», «é simulado?», «está simulado?», «é uma demo?», «é só uma simulação?», «estamos em uma simulação?», «é um simulador?», «isso é fake?»
  var AUT_CURTA = /^ (?:(?:mas|entao|isso|isto|tudo|aqui|vc|voce|voces|vcs) )*(?:e|eh|sao|era|foi|esta|estao|ta|tao|estamos|estou|seria|sera) (?:(?:so|apenas|somente|tudo|isso|isto|mesmo|totalmente|realmente|muito|tao) )*(?:(?:em|numa|num|dentro de) )?(?:uma? )?(?:real|reais|de verdade|verdadeir[oa]s?|simulad[oa]s?|fictici[oa]s?|inventad[oa]s?|fals[oa]s?|fake|de mentira|simulacao|simulador|demonstracao|demo)(?: (?:mesmo|ne|certo|de verdade|de fato|ou nao|nao e|nao|ou (?:e |eh |esta )?(?:real|reais|de verdade|verdadeir[oa]s?|simulad[oa]s?|fictici[oa]s?|fals[oa]s?|fake|de mentira)))* $/;
  // a medida (ou a moeda) que usa as mesmas palavras: nunca a pergunta da autenticidade
  var AUT_MEDIDA = / (?:tempo|velocidade|vento|valor|consumo|diesel|combustivel|profundidade|calado|rumo|norte|estado|nivel|autonomia|pressao|temperatura|distancia|rpm|horas|horario|posicao|latitude|longitude|curso|proa|angulo|ondas?|mare|altura|peso|carga|tensao|corrente|horimetro|rotacao|alcance|capacidade|vazao|volume|quantidade|media|maxima|minima|giro|sog|cog|stw) (?:real|reais|verdadeir[oa]s?) | (?:em|de|mil|milhoes de) reais | (?:quanto|quanta|quantos|quantas|qual|quais) /;
  function medidaAut(q) {
    return AUT_MEDIDA.test(q)
      || (has(q, [' vento', 'rumo', 'norte', ' proa', ' curso ', 'marcacao']) && has(q, [' verdadeir'])) || (has(q, [' vento']) && has(q, [' real ', ' reais ']));   // («o vento é verdadeiro?» e «o rumo é verdadeiro?» são o vento e o rumo)
  }
  // Revisão 4 da P3C: LISTA BRANCA. A frase de apresentação e a situação de bordo (calma) só respondem a quem pergunta, e mais nada, sobre a autenticidade: toda palavra da pergunta é do vocabulário dela
  // (AUT_ALVO, as palavras da autenticidade, as neutras e as de «quero saber / preciso confirmar / é urgente»). Qualquer outra palavra — «o motor PAROU, os dados são reais?», «tem muita ÁGUA no barco, isso é
  // real?», «estamos PERDIDOS, isso é real?», «a situação é GRAVE», «o bote VIROU» — é relato de falha ou de perigo e segue a rota dele, nunca a leitura calma (trava 10: relato de falha sem leitura simulada).
  // «Preciso», «é sério» e «é urgente» DENTRO da pergunta sobre os dados (sem pedido de ajuda: esse é a rota sos, que vem antes) continuam sendo a pergunta sobre os dados.
  var AUT_VOCAB = null;   // (montada na 1ª chamada: NEUTRAS_BASE é definida mais abaixo)
  function autVocab() {
    return AUT_VOCAB || (AUT_VOCAB = NEUTRAS_BASE + AUT_ALVO.join('') + 'real reais verdade fato mentira teste treino demo demonstracao ambiente modo versao apresentacao plataforma programa exemplo treinamento genuino autentico oficial isso isto esse essa esses essas este estes estas tudo todo toda todos todas so apenas somente mesmo ou ne certo sim mas entao '
    + 'vc voce voces vcs nos eu usa usam usando usar mostra mostram mostrando tem sao eh era eram foi foram seria seriam sera serao ser parece parecem estava estavam tao fake estamos estou la realmente totalmente muito um uma uns umas numa num dentro com para pra '
    + 'que se oque oq conectado conectada navegando navegamos viajando viajamos existe existem preciso precisamos saber confirmar urgente serio relatorio decidir saio quero queria gostaria checar conferir verificar afinal pergunto duvida curiosidade ');
  }
  var AUT_RAIZ = /^(?:simul|fictici|inventa|inventou|verdadeir|fals[oa]|demonstra)/;
  // O «não» só vale nas caudas da pergunta («é real ou não?», «isso não é real?», «são reais, não é?», «os dados são reais não?»); em outro lugar é relato: «não tem mais diesel, os dados são reais?», «o alarme não para, isso é real?»
  var AUT_NAO = / (?:ou )?nao (?:e|eh|sao|foi|era)(?= )| ou nao(?= )| nao $/g;
  function soAutenticidade(q) { return q.replace(AUT_NAO, ' ').trim().split(/ +/).every(function (w) { return autVocab().indexOf(' ' + w + ' ') !== -1 || AUT_RAIZ.test(w) || /^\d+$/.test(w); }); }
  // («esses dados são reais? preciso decidir se saio»: o pedido que vem DEPOIS da pergunta não muda a estrutura dela; o pedido que tem a palavra da autenticidade — «preciso saber se os dados são reais» — é a pergunta e fica)
  var AUT_PEDIDO_FIM = /^( (?:[a-z0-9]+ )+?)((?:eu )?(?:preciso|precisamos|quero|queria|gostaria)(?:(?! (?:real|reais|verdade|verdadeir|simul|fictici|inventa|inventou|mentira|fals|fake|demo))(?: [a-z0-9]+)){0,6} )$/;
  function sobreDados(q) {
    if (AUT_SENSOR_DE.test(q) || (has(q, AUT_SENSOR) && AUT_FALSO.test(q)) || !soAutenticidade(q)) return false;
    q = q.replace(AUT_PEDIDO_FIM, '$1');
    if (AUT_CURTA.test(q) || AUT_QUE_E.test(q) || AUT_NAVEGANDO.test(q)) return true;
    if (has(q, AUT_ALVO) && (has(q, AUT_FORTE) || has(q, AUT_EXISTE))) return true;
    return !medidaAut(q) && (AUT_NOME.test(q) || (has(q, AUT_ALVO) && (AUT_PRED.test(q) || AUT_INV.test(q))));
  }
  // Vento a bordo (revisão 4 da P3C): «qual o vento a bordo agora?», «vento verdadeiro», «vento aparente», «o vento é verdadeiro ou aparente?», «qual o vento real no barco agora?» pedem o vento do quadro, não a previsão
  // do dia: a 1ª linha (a falada) é o vento verdadeiro (ou o aparente, ou os dois) «a bordo agora» com a hora; a previsão real e o resto do tempo a bordo seguem logo abaixo. Sem um dos sinais («a bordo», «agora», «verdadeiro»,
  // «aparente», «real», «no barco», «neste momento») ou com outra palavra (a previsão de hoje, o relato «o vento está forte») a pergunta é a de sempre: a previsão primeiro.
  function linhasVento(qq, i) {
    var sq = pad(qq || ''), t = i && i.txt;
    if (!t || !t.vento || !has(sq, [' vento ', ' ventando ']) || !has(sq, [' a bordo ', ' agora ', ' verdadeiro ', ' verdadeira ', ' aparente ', ' real ', ' no barco ', ' neste momento ', ' ventando ']) || !leitura(sq, NEUTRAS_BASE + VENTO_OK_P)) return '';
    var ap = has(sq, [' aparente ']), vd = has(sq, [' verdadeiro ', ' verdadeira ']), fim = ' — ' + i.hora + '.';
    if (ap && vd && t.ventoAp) return 'A bordo agora, vento verdadeiro ' + t.vento + ' e aparente ' + t.ventoAp + fim;
    if (ap && t.ventoAp) return 'A bordo agora, vento aparente ' + t.ventoAp + fim + '\nVento verdadeiro ' + t.vento + '.';
    return 'A bordo agora, vento verdadeiro ' + t.vento + fim + (t.ventoAp ? '\nVento aparente ' + t.ventoAp + '.' : '');
  }
  var VENTO_OK_P = 'ventando muito vento ventos verdadeiro verdadeira aparente real bordo barco lancha embarcacao neste nesse momento velocidade direcao intensidade forca nos marca marcando mostra mostrando indica indicando soprando ou ';
  // embarcacao: as dimensões, o calado, a lotação, o modelo e o registro do cadastro (D.embarcacao). A pergunta do calado é daqui (o calado tem dado desde a Fase 1).
  var EMB_PALAVRAS = [' calado', ' comprimento', 'dimensoes', ' boca do barco', ' boca da lancha', ' boca da embarcacao', 'largura do barco', 'largura da lancha', 'largura da embarcacao', 'tamanho do barco', 'tamanho da lancha',
    'tamanho da embarcacao', 'quantos metros tem o barco', 'deslocamento do barco', 'deslocamento da lancha', 'deslocamento da embarcacao', 'qual o deslocamento', 'peso do barco', ' lotacao', 'quantas pessoas cabem',
    'cabem quantas pessoas', 'modelo do barco', 'modelo da lancha', 'modelo da embarcacao', 'fabricante do barco', 'fabricante da lancha', 'qual o estaleiro', 'quem fabricou', 'ano do barco', 'ano de fabricacao',
    'registro do barco', 'registro da lancha', 'registro da embarcacao', 'numero de registro', 'numero do registro', 'ficha tecnica', 'que barco e esse', 'qual e o barco'];
  // as palavras do cadastro que também servem a OUTRA coisa a bordo («quem fabricou o motor», «o comprimento da sonda», «a lotação do bote», «quem fabricou o transdutor», «o comprimento da corrente da âncora»): nada além das palavras do
  // próprio cadastro e das de ligação pode sobrar (EMB_RESTO_OK; com «barco/lancha/embarcação» na pergunta, mais as neutras de NEUTRAS_BASE e os números). Qualquer outra palavra manda a pergunta à rota dela
  var EMB_RESTO_OK = ' qual quais e eh o a os as um uma de do da dos das no na nos nas em para pra por quanto quantos quantas tem ter ha meu minha nosso nossa seu sua esse essa este esta isso aqui ai agora hoje mesmo exatamente total maximo minimo certo oficial que me diga diz fala fale informe informa mostre mostra metros metro m pessoas pessoa cabem cabe lotacao calado comprimento dimensoes dimensao deslocamento peso quem fabricou fabricante modelo ano fabricacao numero registro ficha tecnica estaleiro boca largura tamanho altura capitao ia ';
  function embarcacaoPergunta(q) {
    if (!has(q, EMB_PALAVRAS)) return false;
    if (has(q, [' barco ', ' barcos ', ' lancha ', ' embarcacao '])) { var ok = EMB_RESTO_OK + NEUTRAS_BASE + 'barco barcos lancha embarcacao real sao maxima minima total '; return !DEFINICAO.test(q) && q.trim().split(' ').every(function (w) { return ok.indexOf(' ' + w + ' ') !== -1 || /^\d+$/.test(w); }); }
    return q.trim().split(' ').every(function (w) { return EMB_RESTO_OK.indexOf(' ' + w + ' ') !== -1; });
  }
  // pessoas a bordo: o número do registro de saída (embarcacao.pessoasBordo); a lotação («quantas pessoas cabem») é do cadastro (embarcacao)
  var PESSOAS_PALAVRAS = ['pessoas a bordo', 'quantas pessoas', 'quantos a bordo', 'gente a bordo', 'tripulantes a bordo', 'passageiros a bordo', 'quem esta a bordo', 'quantos tripulantes', 'quantos passageiros'];
  // («quanto de fundo tem aqui?», «qual o fundo?», «fundo», «sonda»: o jeito de bordo de perguntar a profundidade; a «válvula de fundo», o «fundo do casco» e o «fundear» têm palavra fora da lista branca)
  var PROFUNDIDADE_PALAVRAS = ['profundidade', 'ecobatimetro', 'sob a quilha', 'quanto fundo', ' fundo aqui', 'agua sob', 'de fundo tem', 'quanto de fundo', 'qual o fundo', ' fundo ', ' sonda '];
  var POUCO_FUNDO = /^ (?:e )?(?:tem|ha|temos|tenho) (?:muito |pouco |bastante )fundo(?: aqui| ai| agora)? $/;
  // A leitura (calma) só responde a pergunta NEUTRA: toda palavra da pergunta está na lista abaixo (e nenhum número). O relato com número ou estado («a sonda marca 2 metros de profundidade»,
  // «profundidade caindo», «profundidade zero», «encalhamos») tem outra palavra e segue o guia ou a IA, nunca «10,8 m» (trava 10: relato de falha sem leitura calma).
  function soNeutras(q, ok) { return q.trim().split(' ').every(function (w) { return ok.indexOf(' ' + w + ' ') !== -1; }); }
  var NEUTRAS_BASE = ' qual quais quanto quanta quantos quantas e eh o a os as de do da dos das no na nos nas em esta estao ta tem temos tenho ha como me diga diz fale fala mostra mostre informe passa passe agora hoje atual atuais aqui ai capitao ia por favor oi ola ';
  var PROFUNDIDADE_OK = NEUTRAS_BASE + 'profundidade fundo agua sob quilha ecobatimetro sonda leitura leituras marca marcando mostra mostrando indica indicando mede medindo real barco lancha embarcacao nosso nossa neste nesse momento ponto local lugar metros ';
  // (só a leitura do ecobatímetro: o alarme de profundidade, a mínima, o «como configurar», o relato, a de fundear, a do porão e a de OUTRO lugar têm palavra fora da lista e seguem o guia, a rota dele ou a IA)
  function profundidadePergunta(q) { return (has(q, PROFUNDIDADE_PALAVRAS) && soNeutras(q, PROFUNDIDADE_OK)) || POUCO_FUNDO.test(q); }
  // Revisão 3 da P3C: a leitura calma de TODA rota nova só responde a pergunta neutra (lista branca por rota). O relato de falha, o imperativo do plotter, o lugar fora da rota e a pergunta de definição têm palavra fora da lista e
  // seguem a rota do equipamento, o guia ou a IA, como antes da P3C (trava 10: relato de falha sem leitura calma). «O que é/significa …» é a pergunta do conceito (a IA), nunca a leitura.
  var DEFINICAO = / (?:o que|oque|oq) (?:e|eh|sao|significa|quer dizer) | significa | quer dizer | definicao | conceito /;
  function leitura(q, ok) { return !DEFINICAO.test(q) && soNeutras(q, ok); }
  var POSICAO_VELHAS = [' posicao', 'onde estou', 'onde esta o barco', 'coordenada', ' gps', ' proa', 'velocidade'];
  var POSICAO_NOVAS = ['onde estamos', ' rumo ', ' cog ', ' sog ', ' quantos nos ', 'milhas por hora'];
  var POSICAO_OK = NEUTRAS_BASE + 'que estamos onde estou posicao rumo cog sog curso fundo sobre verdadeiro nos milhas milha hora por fazendo navegando indo andando vamos barco lancha embarcacao nosso nossa meu minha ';
  function posicaoPergunta(q) { return !has(q, ['baliza']) && (has(q, POSICAO_VELHAS) || (has(q, POSICAO_NOVAS) && leitura(q, POSICAO_OK))); }   // («baliza fora de posição» é a boia de balizamento, não a posição do barco; a baliza do EPIRB é cabeça de emergência, antes desta rota)
  var ETA_OK = NEUTRAS_BASE + 'quando ja muito estamos eta chegada chegamos chegar chegaremos chega chegando vamos horario previsao prevista previsto tempo falta faltam milhas milha mn minutos horas hora destino waypoint waypoints ponto pontos proximo proxima distancia ate para pra percorrida percorridas percorremos percorrido navegadas navegamos navegado odometro gente rota viagem trajeto base marina que ou ';
  var ALARMES_OK = NEUTRAS_BASE + 'alarme alarmes alerta alertas ativo ativos ativa ativas aceso acesos acesa acesas tocando soando algum alguma alguns algumas nenhum nenhuma existe existem barco lancha embarcacao bordo neste momento ';
  var PESSOAS_OK = NEUTRAS_BASE + 'pessoas pessoa gente tripulantes tripulante passageiros passageiro bordo quem barco lancha embarcacao registro saida conosco ';
  var AIS_OK = NEUTRAS_BASE + 'ais alvos alvo transponder classe b ligado ligada funcionando recebendo vendo algum alguns quantidade quais situacao status estado barco lancha embarcacao nosso nossa temos ';
  var NAVEGACAO_OK = NEUTRAS_BASE + 'navegacao status resumo anda andamento viagem situacao geral barco lancha embarcacao ';
  // (tendências: os assuntos dos achados — motor, óleo, arrefecimento, bateria, horas até a revisão, gerador — e as palavras de pedir a tendência; «governo», «manobra», «adernar», «carga», «tempo», «mar», «água», «âncora», «rumo» não estão aqui)
  var PRED_OK = NEUTRAS_BASE + 'tendencia tendencias preditiva preditivo preditivas preditivos analise analises recomendacao recomendacoes algum alguma alguns algumas estavel estaveis motor motores oleo pressao arrefecimento temperatura bateria baterias banco bancos partida servico horas hora ate revisao troca gerador cruzeiro sistema sistemas geral manutencao barco lancha embarcacao perdendo capacidade sao existem existe bb be bombordo boreste ';
  // (o checklist de saída pelo «antes de largar»: só a pergunta de CONFERIR, neutra — «o que preciso conferir antes de largar?»; «antes de sair, confira o porão» tem palavra fora da lista e segue a rota do porão; 
  // «o que fazer antes de largar» segue o trecho do guia «Saída · antes de largar», como sempre)
  var CHECK_ANTES_OK = NEUTRAS_BASE + 'que preciso precisamos devo devemos tenho conferir verificar checar revisar lembrar antes largar sair zarpar saida barco lancha embarcacao para pra estamos pronto prontos tudo ja ';
  // Pedido de socorro que a lista SOS (a do gerador, que não muda aqui) não pega: «isso é real, preciso de ajuda», «isso não é um teste», «estamos em risco». Vai à rota sos; e a frase de apresentação (sobreDados, lista branca) nunca responde a quem pede ajuda.
  var SOCORRO_PEDE = /\b(?:preciso|precisamos|precisando|necessito|necessitamos) (?:de )?(?:muita )?(?:ajuda|socorro|auxilio|resgate)\b/;
  var SOCORRO_DECLARA = /\b(?:e|eh|era) (?:real|serio|de verdade)\b|\bnao (?:e|eh) (?:um |uma )?(?:teste|brincadeira|treino|exercicio)\b|\bem (?:risco|apuros)\b/;
  var NAO_TESTE = /\bnao (?:e|eh) (?:um |uma )?(?:teste|brincadeira|treino|exercicio)\b/;
  // (revisão 4: «correr risco» em todas as flexões — «estamos correndo risco», «o barco corre risco» —; o «risco DE <coisa>» só é socorro com a vida ou o perigo de bordo: «risco de chuva» e «o filtro está em risco de entupir» não são)
  var EM_RISCO = /\b(?:(?:estamos|estou|ficamos)(?: todos)? em (?:risco|apuros)|(?:corremos|corro|correndo|corre|correm|correu|corriam) risco|(?:o barco|a lancha|a embarcacao) (?:esta|ta) em (?:risco|apuros))\b(?! de (?!(?:vida|afund|naufrag|incend|fogo|colid|colis|encalh|morr|explod|emborc|alag|capot|virar)))/;
  // o pedido de ajuda no imperativo plural ou sem complemento: «me ajudem», «ajudem», «alguém me ajuda», «pelo amor de Deus, ajuda» (a «ajuda» sozinha continua sendo o menu; «alguém me ajuda a trocar o óleo» é rotina)
  var SOCORRO_AJUDA = /\bajudem\b|\balguem (?:me |nos )?(?:ajuda|ajude)(?: por favor| aqui| agora)? $|\bpelo amor de deus\b.*\b(?:ajuda|ajudem|ajude|socorro)\b/;
  // o pedido de ajuda junto de um dado que o MAYDAY pede (posição, rumo, ETA, pessoas a bordo) também é socorro: a posição é a do plotter, nunca a do quadro
  var DADOS_MAYDAY = ['posicao', 'onde estamos', 'onde estou', 'coordenada', 'latitude', 'longitude', ' rumo ', ' eta ', 'chegada', 'pessoas a bordo', 'quantas pessoas', 'quantos a bordo', 'quantos tripulantes', 'quantos passageiros'];
  function socorroImplicito(q) { return (SOCORRO_PEDE.test(q) && (SOCORRO_DECLARA.test(q) || has(q, DADOS_MAYDAY))) || NAO_TESTE.test(q) || EM_RISCO.test(q) || SOCORRO_AJUDA.test(q); }
  // O equipamento de segurança na pergunta (EPIRB, Seafire, canal 16, PAN-PAN, DSC): a pergunta mista («acionar o EPIRB, quantas pessoas a bordo?», «pan-pan, qual o ETA?») é do equipamento, com o procedimento e
  // a janela de emergência da chave dele; as rotas de dados da navegação e do cadastro (que levam ETA, pessoas, profundidade, alarmes…) não a tomam.
  var SEAFIRE_PALAVRAS = ['seafire', 'sea fire', 'sea-fire', 'sistema de incendio', 'supressao', 'disparo manual'];
  function seafirePergunta(q) { return has(q, SEAFIRE_PALAVRAS) || seafireDisparo(q); }
  var CANAL16_SEG = ['canal 16', 'pan-pan', 'pan pan', ' dsc', 'distress'];   // (o rádio VHF sozinho não entra: «alcance do rádio» não é o roteiro)
  // o que a route() manda para a rota canal16 (o roteiro MAYDAY)
  var CANAL16_ROTA = ['canal 16', ' vhf', ' radio', ' dsc', 'pan-pan', 'pan pan'];
  // ——— A CABEÇA DE EMERGÊNCIA (P3E, revisão 4) ———
  // UM predicado para tudo o que a route() entrega a uma rota de emergência (EMERG) ou ao trecho de segurança do DSC/da baliza: a lista SOS e o pedido de socorro, o relato de óleo, a salvatagem, o MMSI, o EPIRB
  // (as palavras e a baliza que disparou), a baliza do EPIRB, o Seafire e TODAS as palavras de CANAL16_SEG e de CANAL16_ROTA. Cada rota nova que lê o quadro ou a lista (os 4 checklists, o estoque de peças, as
  // tendências, o FAQ no lugar do fallback) abre com ele: a pergunta de cabeça de emergência nunca é delas, é local e não leva posição, rumo, SOG, ETA nem pessoas. O testes/cerebro.py lê estas listas do
  // próprio arquivo e gera a matriz cabeça × cauda: uma palavra nova aqui passa a ser testada sozinha.
  // A «baliza» do EPIRB: a palavra sozinha é também a de sinalização («a baliza do canal está apagada», «baliza cardinal», «a cor da baliza de boreste», «vi uma baliza apagada»), que não é emergência e vai à IA, que sabe de
  // balizamento. A baliza só é cabeça de emergência com UMA destas três provas, nunca pela palavra sozinha numa pergunta de outro assunto:
  //  (1) contexto de EPIRB na pergunta (BALIZA_CTX: o teste, a bateria, a validade, o acionamento, o perigo…; epirb/radiobaliza/autoteste/hidrostático/406 também);
  //  (2) a pergunta é só a baliza e palavras neutras («a baliza», «onde fica a baliza», «cadê a baliza»);
  //  (3) a baliza vem JUNTO de uma pergunta que tem rota própria («a baliza, checklist de saída», «nível dos tanques, a baliza»): a pergunta mista é do equipamento. A prova é a rota do que sobra tirando a palavra:
  //      sobra o fallback («qual a baliza de bombordo?» → «qual a de bombordo?») = a pergunta é de balizamento. (A baliza com palavra de sinalização e sem palavra só do EPIRB nunca conta, em nenhuma prova.)
  var BALIZA_CTX = {}; ['epirb', 'radiobaliza', 'autoteste', 'hidrostatico', '406', 'teste', 'testar', 'testo', 'testamos', 'testei', 'bateria', 'validade', 'vencimento', 'vence', 'venceu', 'acionar', 'acionamento', 'aciono', 'acionei',
    'ativar', 'ativacao', 'ativei', 'disparar', 'disparo', 'dispara', 'perigo', 'emergencia', 'socorro', 'resgate', 'sos', 'etiqueta', 'sobressalente', 'registro', 'hex'].forEach(function (w) { BALIZA_CTX[raiz(w)] = 1; });
  var BALIZA_OK = NEUTRAS_BASE + 'baliza onde fica ficam cade guardada guardado guardamos nosso nossa meu minha barco lancha embarcacao que ';
  var EM_BALIZA = false;   // (a prova 3 chama a route() sobre o que sobra SEM a palavra «baliza»: a guarda impede qualquer volta)
  function balizaEpirb(q) {
    var qs, resto, rota;
    if (EM_BALIZA || !has(q, ['baliza'])) return false;
    qs = tokens(q);
    if (qs.some(function (w) { return SINAL_RAIZES[w]; }) && !qs.some(function (w) { return EPIRB_SO[w]; })) return false;
    if (qs.some(function (w) { return BALIZA_CTX[w]; }) || soNeutras(semVocativo(q).replace(/ por favor /g, ' '), BALIZA_OK)) return true;
    resto = q.replace(/ (?:(?:a|as|da|das|na|nas|pela|uma|essa|esta|nossa|minha|de|do) )?baliza\w*(?= )/g, ' ');   // («a baliza», «da baliza», «uma baliza»: o artigo vai junto)
    if (!resto.trim()) return false;
    EM_BALIZA = true;
    try { rota = route(resto); } finally { EM_BALIZA = false; }
    return rota !== 'fallback';
  }
  function cabecaEmerg(q) {
    return emergencia(q) || oleo(q) === 1 || socorroImplicito(q) || salvatagem(q) || has(q, ['mmsi']) || epirbRelato(q) || balizaEpirb(q) || seafirePergunta(q) || has(q, CANAL16_SEG) || has(q, CANAL16_ROTA);
  }
  // as palavras do documento/licença (a «Licença de Estação» é papelada, não o roteiro MAYDAY): a rota docsvenc as toma antes do rádio, como sempre
  var DOC_PALAVRAS = ['document', 'licenc', ' tie ', 'titulo de inscricao', 'seguro da', 'apolice', 'laudo', 'vistoria', 'vencendo', 'certificado', 'garantia'];
  // A rota da cabeça de equipamento de segurança, ANTES de qualquer rota de dado sem lista branca (telemetria, autonomia, consumo, tanques, destinos, clima, maré…): essas levam o quadro (SOG, rumo, ETA,
  // diesel a «18 nós») e não podem tomar a pergunta do EPIRB, do Seafire, do canal 16, do PAN-PAN, do DSC, do rádio/VHF, nem a do botão DISTRESS e da baliza do EPIRB (que não têm rota própria: seguem o
  // fallback, onde o trecho de segurança deles responde, local — cabecaSemRota). null = não é cabeça de equipamento.
  function equipRota(q) {
    if (epirbRelato(q)) return 'epirb';
    if (seafirePergunta(q)) return 'seafire';
    if (has(q, DOC_PALAVRAS)) return null;   // («Licença de Estação do rádio» e «certificado do botão DISTRESS» são papelada: a rota docsvenc, mais abaixo)
    if (has(q, CANAL16_ROTA)) return 'canal16';
    if (cabecaSemRota(q) && !SOBRE.test(q) && !has(q, ['ajuda'])) return 'fallback';   // («como você me ajuda com o teste da baliza?» e «o que você sabe sobre o teste da baliza?» são a pergunta sobre o app: a rota delas, a saudação, local pelo pedeIA)
    return null;
  }
  // a pergunta do botão DISTRESS (a palavra de CANAL16_SEG que não é de CANAL16_ROTA: o DSC sem «DSC» na frase) e a da baliza do EPIRB: o que buscar no guia, só pela cabeça («botão distress» e «baliza» dão o
  // trecho de segurança); '' = não é. (Só vale depois do has(q, CANAL16_ROTA) da equipRota: com «canal 16», «PAN-PAN», «DSC», «VHF» ou «rádio» a rota é a canal16.)
  function cabecaSemRota(q) { return has(q, CANAL16_SEG) ? 'botao distress' : balizaEpirb(q) ? 'baliza' : ''; }
  // MMSI (CLAUDE.md 8): a pergunta do número do MMSI é a rota mmsi; a que tem outro assunto junto fica com a rota dele: o EPIRB, o Seafire, o roteiro de rádio (canal 16, PAN-PAN, DSC, socorro ou pane) e o vencimento
  // (documento). Assim o 710123456 do cadastro nunca vai para a pergunta do EPIRB nem do rádio, e o procedimento não se perde.
  // (a lista é BRANCA, não negra: nenhum verbo de pôr o número no aparelho, em nenhuma flexão, nem o rádio, o VHF, o AIS ou o plotter estão nela; «que MMSI eu coloco no rádio?» e «como cadastro o MMSI?» ficam só com o da etiqueta. O «por» sai da lista porque é também o «pôr»; o «por favor» sai da pergunta antes de conferir)
  var MMSI_OK = NEUTRAS_BASE.replace(' por ', ' ') + 'que mmsi barco lancha embarcacao cadastrado cadastrada registrado app aplicativo numero nosso nossa meu minha seu sua indicativo ';
  // («cadastro» sozinho é também o verbo, «como cadastro o MMSI?»: só vale como substantivo, «do/no/pelo cadastro»)
  function mmsiNeutra(pq) { return !pq.trim() || soNeutras(semVocativo(pq).replace(/ por favor /g, ' ').replace(/ (?:do|no|pelo|de) cadastro /g, ' cadastrado '), MMSI_OK); }
  var MMSI_VENCE = [' vence', 'vencim', 'vencid', 'vencend', 'validade', 'valido', 'expira'];
  var MMSI_PERIGO = ['socorro', 'ajuda', ' pane', ' parou', 'falha', 'quebr', 'avaria', 'problema', 'encalh', 'emergencia', 'urgencia', 'perigo', 'pedir', 'chamar'];
  function mmsiRota(q) {
    if (epirbRelato(q) || has(q, ['baliza'])) return 'epirb';
    if (seafirePergunta(q)) return 'seafire';
    if (has(q, CANAL16_SEG) || has(q, MMSI_PERIGO)) return 'canal16';
    if (has(q, MMSI_VENCE)) return 'docsvenc';
    return 'mmsi';
  }
  // ETA, distância e waypoint. «Quanto falta» só vale junto de chegar, chegada, destino, waypoint, ponto, ETA ou o nome de um ponto da rota (nunca «quanto falta para a troca de óleo?»);
  // a autonomia, o diesel, o alcance, o consumo e o checklist têm as rotas deles.
  var ETA_PALAVRAS = [' eta ', 'hora de chegada', 'horario de chegada', 'chegada prevista', 'previsao de chegada', 'quando chegamos', 'quando vamos chegar', 'quando a gente chega', 'que horas chegamos',
    'que horas chegaremos', 'que horas vamos chegar', 'que horas chega', 'tempo para chegar', 'tempo ate chegar', 'tempo de chegada', 'falta para chegar', 'faltam para chegar', 'waypoint', 'proximo ponto',
    'distancia ate', 'distancia para', 'distancia do destino', 'distancia percorrida', 'milhas percorridas', 'milhas navegadas', 'quantas milhas faltam', 'quantas milhas falta', 'quantas milhas ate', 'quantas milhas para',
    'quantas milhas percorr', 'quantas milhas naveg', 'quantas milhas ja naveg', 'quantas milhas ja percorr', 'quantas mn faltam', 'quantas mn ate', 'quantas mn percorr', 'quantas mn naveg', 'odometro',
    'vamos chegar a que horas', 'a que horas vamos chegar', 'a que horas chegamos', 'a que horas a gente chega', 'em quanto tempo chegamos', 'em quanto tempo vamos chegar', 'em quanto tempo a gente chega',
    'ja chegamos', 'estamos chegando', 'quanto tempo ate', 'quanto tempo para chegar', 'quanto tempo pra chegar', 'quanto tempo vamos levar', 'quanto tempo vai levar'];
  var FALTA_PALAVRAS = ['quanto falta', 'quanto tempo falta', 'quantas milhas faltam', 'quantos minutos faltam', 'quantas horas faltam', 'o que falta para', 'falta muito'];
  // a troca de óleo e a revisão dos motores (as horas que faltam): só a pergunta neutra; «trocar o filtro de água salgada» e «a revisão anual» são de outra tarefa da agenda e seguem o guia
  var FALTA_TROCA_OK = NEUTRAS_BASE + 'falta faltam muito para pra troca trocar trocamos revisao oleo filtro filtros motor motores horas hora proxima proximo ate quando ';
  var NIVEL_DIESEL = / (?:quanto|quantos litros) (?:de )?(?:diesel|combustivel)| nivel (?:do |de |dos )?(?:tanques? (?:de )?)?(?:diesel|combustivel)| diesel (?:tem|temos|resta|sobrou)| tanques? de (?:diesel|combustivel) /;
  var PROX_TROCA = ['proxima troca', 'quando e a troca', 'quando vence a troca', 'data da troca', 'quando e a proxima', 'quando e a revisao'];
  var FALTA_JUNTO = ['chegar', 'chegada', 'destino', 'waypoint', 'ponto', ' eta ', ' base ', ' marina '];
  // (o procedimento do plotter — «como criar/marcar/salvar um waypoint», «onde fica o botão» —, as milhas por litro, o alcance de um rádio e o resgate/socorro que se espera têm outra rota ou o guia: não estão na lista
  // branca ETA_OK, e a chegada é só a da rota do barco)
  // os nomes dos pontos da rota e dos destinos (D.rota, D.destinos; só com a simulação e nunca no SOS), sem o que vem entre parênteses
  function rotaDoPlano() { return EM_SOS ? null : D.rota; }   // no SOS nada lê a rota
  function lugaresRota() {
    var R = rotaDoPlano(), out = [];
    if (!sim() || !R) return out;
    try { [R.base].concat(R.pontos || [], D.destinos || []).forEach(function (x) { var n = x && x.nome ? norm(x.nome).split('(')[0].replace(/\s+/g, ' ').trim() : ''; if (n && out.indexOf(' ' + n + ' ') === -1) out.push(' ' + n + ' '); }); } catch (e) {}
    return out;
  }
  // o ponto da rota ou dos destinos que a pergunta cita («quanto falta para o Estaleirinho?»): o nome como está nos dados, sem o que vem entre parênteses; o mais comprido ganha («Ponta das Laranjeiras» sobre «Laranjeiras»)
  function pontoCitado(qq) {
    var R = rotaDoPlano(), q = pad(qq), achado = null;
    if (!sim() || !R) return null;
    try { [R.base].concat(R.pontos || [], D.destinos || []).forEach(function (x) {
      var nome = x && x.nome ? String(x.nome).split('(')[0].replace(/\s+/g, ' ').trim() : '', n = norm(nome);
      if (n && q.indexOf(' ' + n + ' ') !== -1 && (!achado || n.length > norm(achado).length)) achado = nome;
    }); } catch (e) {}
    return achado;
  }
  function etaPergunta(q) {
    if (!has(q, ETA_PALAVRAS) && !(has(q, FALTA_PALAVRAS) && (has(q, FALTA_JUNTO) || has(q, lugaresRota())))) return false;
    return leitura(q, ETA_OK + lugaresRota().join(''));   // (só o nome de um ponto da rota ou do destino entra: «até Itajaí», «crie um waypoint», «o ETA não atualiza» têm palavra fora da lista)
  }
  // alarmes ativos: «alarmes ativos», «tem algum alarme (ativo)?», «quais alarmes?», «o alarme está tocando». O «alarme de <equipamento>», «o alarme disparou» e «em caso de alarme» seguem as rotas deles.
  var FIM_ALARME = '(?: (?:estao|esta|sao))?(?: (?:ativos?|acesos?|tocando|soando|no barco|a bordo|agora|aqui|ai|hoje|neste momento))*';
  var ALARMES_REGEX = [
    / (?:alarmes?|alertas?) (?:ativos?|acesos?)(?: |$)/,
    new RegExp(' (?:tem|ha|existe|existem|temos) (?:algum |alguns )?(?:alarmes?|alertas?)' + FIM_ALARME + ' $'),
    new RegExp(' quais (?:sao |estao )?(?:os )?(?:alarmes|alertas)' + FIM_ALARME + ' $'),
    new RegExp('^ (?:e )?(?:os |o )?(?:alarmes?|alertas?)' + FIM_ALARME + ' $')
  ];
  // o alarme que está SOANDO (o ruído do painel): a mesma rota, mas a resposta manda conferir o painel primeiro e nunca diz «tudo normal» (o app só lê os alarmes do quadro de leitura, não o alarme sonoro de porão, fumaça ou gás).
  // Com o lugar ou o equipamento («alarmes tocando na cabine») a pergunta segue a rota dele.
  var ALARME_SOANDO = / alarmes? (?:esta |estao )?(?:tocando|soando) /;
  function alarmeSoando(q) { return / (?:tocando|soando|tocou|soou) /.test(pad(q)); }
  function alarmesPergunta(q) { return (ALARMES_REGEX.some(function (r) { return r.test(q); }) || ALARME_SOANDO.test(q)) && leitura(q, ALARMES_OK); }   // (o «alarme de <equipamento>», o «alarmes tocando na cabine» e o alarme de um lugar têm palavra fora da lista branca: seguem a rota deles)
  // temperatura do motor (o arrefecimento): só a pergunta NEUTRA pela leitura (soNeutras); o alarme, o relato, o «como» e a temperatura alta seguem o guia dos motores (a resposta pronta cede ao trecho)
  var ARREF_REGEX = / (?:temperaturas? (?:d[oae]s? )?(?:motor|motores|arrefecimento|bb|be|bombordo|boreste)|temperaturas? da agua d[oa]s? (?:motor|motores)|arrefecimento) /;
  var ARREF_OK = NEUTRAS_BASE + 'temperatura temperaturas motor motores arrefecimento agua bb be bombordo boreste estibordo esquerdo direito principal principais dois ambos graus marca marcando mostra mostrando indica indicando ';   // («está em 110», «no vermelho», «parou», «sem água», «chegou a»… não são neutras)
  // (o alarme, o relato, o «como», a temperatura alta, a normal/a faixa e o arrefecimento de OUTRO equipamento — gerador, Seakeeper, climatização — têm palavra fora da lista: o guia dos motores ou a rota do outro; a marca do motor entra pelas palavras do cadastro)
  function arrefOk() { var e = equip('motores'); return ARREF_OK + (e && e.palavras ? e.palavras.map(norm).join(' ') + ' ' : ''); }
  // «é o BE que está mais quente?», «qual motor está mais quente?»: a temperatura do arrefecimento (só a pergunta neutra; «quente demais», «esquentando» e o relato têm palavra fora da lista)
  var ARREF_QUENTE = / (?:motor|motores|bb|be|bombordo|boreste|estibordo|esquerdo|direito)(?: [a-z]+){0,5} (?:mais )?quentes? | (?:mais )?quentes? (?:[a-z]+ ){0,4}(?:motor|motores|bb|be|bombordo|boreste) /;
  function arrefecimentoPergunta(q) { return (ARREF_REGEX.test(q) && soNeutras(q, arrefOk())) || (ARREF_QUENTE.test(q) && soNeutras(q, arrefOk() + 'quente quentes mais menos que qual quais ')); }
  // temperatura da água do mar (o sensor de bordo); a «temperatura da água subindo» do relato é do motor (guia) e fica fora
  var AGUA_REGEX = / temperatura (?:da|do|de) (?:agua|mar)(?: do mar)? | agua do mar (?:esta|ta) | quantos graus (?:esta|ta) a agua | temperatura da agua do mar /;
  var AGUA_OK = NEUTRAS_BASE + 'temperatura agua mar graus fria gelada quente morna marca marcando mostra mostrando indica indicando ';
  // a temperatura do AR externo a bordo («qual a temperatura do ar?», «quantos graus está lá fora?»): a mesma rota, a 1ª linha é o ar. O «ar condicionado», o «ar do motor» e o relato têm palavra fora da lista.
  var AR_REGEX = / temperaturas? (?:do|de) ar(?: externo| ambiente| la fora)? | temperatura (?:la )?fora | ar externo | quantos graus (?:esta|ta|faz) (?:la fora|o ar|fora) /;
  var AR_OK = AGUA_OK + 'ar externo ambiente fora la faz ';
  function aguaPergunta(q) { return (AGUA_REGEX.test(q) && soNeutras(q, AGUA_OK)) || (AR_REGEX.test(q) && soNeutras(q, AR_OK)); }   // (a água que subiu, caiu ou esquentou, a do motor, do gerador e da climatização têm palavra fora da lista)
  // estado do mar a bordo (ondas do quadro); a previsão de mar é do mundo real (clima), e a maré tem a rota dela
  var ONDAS_PALAVRAS = [' ondas ', ' onda ', 'ondulacao', 'estado do mar', 'altura da onda', 'altura das ondas', 'como esta o mar', 'mar agitado', 'mar grosso', 'mar calmo', ' swell '];
  // o relato da onda («a onda bateu no casco», «as ondas molharam o convés», «ondas de 4 metros») não é pergunta do sensor: tem palavra fora da lista e segue a IA, como antes
  var ONDAS_OK = NEUTRAS_BASE + 'mar ondas onda ondulacao altura estado swell agitado grosso calmo bordo marca marcando mostra mostrando indica indicando ';
  function ondasPergunta(q) { return has(q, ONDAS_PALAVRAS) && soNeutras(q, ONDAS_OK); }
  // «como está a navegação», «situação agora»: o resumo narrado do instante. «Como estamos de diesel?» é a autonomia: a frase curta só vale inteira.
  var NAVEGACAO_PALAVRAS = ['como esta a navegacao', 'status da navegacao', 'navegacao agora', 'resumo da navegacao', 'como anda a navegacao'];
  var NAVEGACAO_CURTA = /^ (?:e )?(?:entao )?como (?:estamos|vamos|estao as coisas|esta tudo)(?: indo)?(?: agora| por ai| a bordo| ai)? $/;
  // «situação agora / atual / de bordo» só vale como a pergunta inteira («situação atual do gerador», «situação agora dos tanques» têm a rota do assunto)
  var NAVEGACAO_SITUACAO = /^ (?:e )?(?:entao )?(?:(?:qual|como|que) (?:e |esta )?)?(?:me (?:da|diga|fale|mostre|passa|passe) )?(?:a |o )?(?:situacao|status)(?: (?:geral|da navegacao|de bordo|do barco|da lancha|da embarcacao|a bordo|atual|agora|neste momento|por ai|ai))* $/;
  function navegacaoPergunta(q) { return NAVEGACAO_CURTA.test(q) || NAVEGACAO_SITUACAO.test(semVocativo(q)) || (has(q, NAVEGACAO_PALAVRAS) && leitura(q, NAVEGACAO_OK)); }   // («como está a navegação do piloto automático?», do documento, da manutenção ou do tanque tem palavra fora da lista branca: é do assunto)
  // foraBarco (§2.7): dinheiro, esporte, notícia, política. Depois de todas as rotas de bordo: «quanto custa o diesel em reais?» é do diesel
  // «câmbio» (a reversora), «jogo» (o balanço do barco, a folga de uma peça, o jogo de cabos) e «bolsa» (estanque, de primeiros socorros) têm outro sentido a bordo: só são dinheiro ou esporte sem o vocabulário de bordo junto
  var FORA_BARCO = [' dolar ', ' dolares ', ' cotacao ', ' cotacoes ', ' bitcoin ', ' preco ', ' precos ', 'quanto custa', ' placar ', ' placares ', ' campeonato ', ' campeonatos ', ' noticia ', ' noticias ', ' eleicao ', ' eleicoes ', ' euro ', ' euros ', 'quem venceu', 'quem ganhou'];   // (palavra inteira: «preco» está dentro de «preconizado» e «precoce»)
  var CAMBIO_BORDO = ['engat', 'marcha', 'reversor', 'reversora', 'embreagem', 'alavanca', 'manete', 'duro', 'dura ', 'trava', 'motor', 'helice', 'oleo', 'barulho', 'vibra', 'falha', 'defeito', 'problema', 'neutro', 'acelerador', 'solta', 'arranha',
    'troca', 'trocar', 'revisao', 'manutenc', 'conserto', 'reparo', 'ajust', 'regular', 'quebr', 'desligo', 'copiou', 'copiad', 'recebido', ' radio', ' vhf', 'canal', 'ouvindo', 'escuta'];   // (e o «câmbio, desligo» do rádio)
  var JOGO_BORDO = ['barco', 'lancha', 'embarcacao', 'casco', 'estabiliz', 'seakeeper', 'balan', 'rolagem', 'graus', 'inclina', 'folga', 'leme', 'ancora', 'amarra', 'corrente', 'guincho', 'bote', 'tender', 'eixo', 'helice', 'reversor', 'transmiss', 'volante', 'direcao', 'motor', 'gerador', 'cabo', 'mecanic', 'muito jogo', 'pouco jogo', 'jogo excessivo', 'jogo no ', 'jogo na ', 'jogo de ferrament', 'jogo de chave', 'jogo de cabo', 'jogo de vela', 'jogo de colete', 'jogo de bordo'];
  var BOLSA_BORDO = ['estanque', 'impermeavel', 'primeiros socorros', 'socorro', 'emergencia', 'abandono', 'sobreviv', 'gelo', 'termica', 'ferrament', 'colete', 'kit', 'mochila', 'bote', 'tender', 'ancora', 'amarra', 'cabo', 'barco', 'lancha', 'bordo'];
  function foraBarcoPergunta(q) {
    return has(q, FORA_BARCO) || (has(q, ['cambio']) && !has(q, CAMBIO_BORDO)) || (has(q, [' jogo ', ' jogos ']) && !has(q, JOGO_BORDO)) || (has(q, ['bolsa']) && !has(q, BOLSA_BORDO));
  }
  // O AIS «por perto» («tem barco por perto?», «tem algum navio perto?», «quantas embarcações próximas?»): a contagem de alvos do AIS, a mesma resposta do «quantos alvos?» (o app não vê o radar nem o plotter)
  var AIS_PERTO = / (?:barcos?|embarcacoes?|navios?|lanchas?|veleiros?|alvos?|trafego|movimento) (?:por perto|perto|proximos?|proximas?|aqui perto|ao redor|em volta|na area|por aqui|por ai)(?= )/;
  var AIS_PERTO_OK = AIS_OK + 'tem ha existe algum alguns outro outros por perto perto proximo proximos proxima proximas aqui ao redor em volta na area navio navios barcos veleiros lanchas embarcacoes trafego movimento quantos quantas quais ';
  function aisPergunta(q) { return (has(q, [' ais ']) && leitura(q, AIS_OK)) || (AIS_PERTO.test(q) && leitura(q, AIS_PERTO_OK)); }
  // A LEITURA PONTUAL do quadro (revisão 3 da P3F): a pergunta de UM dado do quadro que nenhuma outra rota abre pelo dado («qual a pressão barométrica?», «quantos satélites?», «qual a inclinação do barco?», «em que marcha
  // estamos?», «o piloto automático está ligado?», «qual o rumo do piloto?», «o radar está ligado?»). Só a pergunta NEUTRA (lista branca por dado): o relato, o «como» e o alarme seguem o guia ou a IA. Nunca no SOS.
  var LEITURA_BORDO = {
    pressao: [/ barometr\w* | pressao (?:atmosferica|do ar|barometrica) /, NEUTRAS_BASE + 'pressao barometrica barometro atmosferica ar hpa marca marcando mostra mostrando indica indicando bordo '],
    satelites: [/ satelites? /, NEUTRAS_BASE + 'satelites satelite gps quantos pegando captando vendo temos tem sinal com fixo '],
    inclinacao: [/ inclinacao | inclinado | caimento | angulo do barco /, NEUTRAS_BASE + 'inclinacao inclinado caimento barco lancha embarcacao angulo graus quantos marca marcando '],
    marcha: [/ (?:em )?que marcha | qual (?:e )?a marcha | marcha engatada /, NEUTRAS_BASE + 'marcha engatada estamos barco lancha em que qual '],
    piloto: [/ piloto (?:automatico )?(?:esta|ta) (?:ligado|engajado|ativo|ativado|em espera|standby|desligado|funcionando|engatado) | rumo (?:do piloto|ordenado)/, NEUTRAS_BASE + 'piloto automatico ligado engajado ativo ativado espera standby desligado funcionando engatado rumo ordenado '],
    radar: [/ radar (?:esta|ta) (?:ligado|ligada|desligado|desligada|transmitindo|ativo|funcionando) /, NEUTRAS_BASE + 'radar ligado ligada desligado desligada transmitindo ativo funcionando ']
  };
  var ESTADO_PILOTO = / (?:ligado|engajado|ativo|ativado|em espera|standby|desligado|funcionando|engatado) /;
  function leituraBordoDe(q) { var k, d; for (k in LEITURA_BORDO) { d = LEITURA_BORDO[k]; if (d[0].test(q) && soNeutras(q, d[1])) return k; } return null; }
  // O documento que a pergunta nomeia (o nome do cadastro tem a palavra dela; só um documento ganha): «quando vence o seguro?» → o seguro; «quais documentos vencem?» → nenhum
  var DOC_PARADA = ' quando qual quais vence vencem vencimento vencimentos vencer validade documento documentos renova renovar venceu vencendo esta estao barco embarcacao lancha proximo proxima situacao como para pelo pela que ';
  function itemPedido(lista, qq, parada, nomeDe) {
    var ts = norm(String(qq || '')).split(/[^a-z0-9]+/).filter(function (t) { return t.length >= 4 && parada.indexOf(' ' + t + ' ') === -1; }), melhor = null, pts = 0, empate = false;
    (lista || []).forEach(function (d) { var nome = norm(nomeDe(d)), k = ts.filter(function (t) { return nome.indexOf(t) !== -1; }).length; if (k > pts) { melhor = d; pts = k; empate = false; } else if (k === pts && k > 0) empate = true; });
    return pts > 0 && !empate ? melhor : null;
  }
  function docPedido(lista, qq) { return itemPedido(lista, qq, DOC_PARADA, function (d) { return d.n; }); }
  // A tarefa da agenda que a pergunta nomeia (palavras do título ou do equipamento; só uma casa e não é de segurança): «o rotor do gerador está atrasado?» → o rotor; «quais tarefas estão atrasadas?» → nenhuma
  var TAREFA_PARADA = ' quando qual quais esta estao estar atrasado atrasada atrasados atrasadas atraso tarefa tarefas manutencao manutencoes servico servicos proxima proximo proximas proximos vence vencem prazo prazos barco embarcacao lancha para pelo pela como que troca trocas trocar limpeza limpar revisao revisoes inspecao inspecoes teste testes testar verificacao verificar ';
  function tarefaPedida(qq) { var t = itemPedido(agenda(), qq, TAREFA_PARADA, function (x) { return x.t + ' ' + (x.equip || ''); }); return t && !seg(t) ? t : null; }
  // O resumo da viagem («resumo da viagem», «como foi a saída hoje?», «balanço do passeio»): o percorrido desde a âncora do dia e a chegada prevista, a rota `eta` pelo lado do percorrido
  var RESUMO_VIAGEM = / (?:resumo|balanco|relatorio) (?:da|do|de) (?:viagem|saida|passeio|travessia|navegacao|dia) | como (?:foi|esta indo|esta sendo|foram) (?:a |o |as |os )?(?:viagem|saida|passeio|travessia|navegacao) /;
  var RESUMO_VIAGEM_OK = NEUTRAS_BASE + 'resumo balanco relatorio viagem saida passeio travessia navegacao dia como foi esta indo sendo foram hoje ate agora ';
  function route(qRaw) {
    var q = pad(qRaw);
    if (!q.trim()) return 'saudacao';
    if (DIAGNOSTICO.test(semVocativo(q))) return 'diagnostico';
    // os botões da proposta do relato («registrar o relato», «não registrar o relato»): depois do diagnóstico, antes de qualquer pedido de registro; a emergência e o óleo vêm antes de tudo
    // F15/F12: a resposta à proposta que espera (confirmar, recusar, desfazer), no mesmo ponto e com a mesma guarda: a emergência e o óleo vêm antes de tudo
    if (!emergencia(q) && oleo(q) !== 1) { var rel = relatoRota(qRaw, q); if (rel) return rel; var prp = propRota(qRaw, q); if (prp) return prp; }
    if (querRegistrar(qRaw, q)) return pedeTexto(qRaw) ? 'diarioPede' : 'diario';
    if (emergencia(q)) return 'sos';
    // F12: o pedido de alarme na forma de CONFIGURAÇÃO («me avise se a pressão do óleo do BB cair abaixo de 2 bar») não é o relato de queda de pressão: o oleo() não o trata como queda (devolve 0) e a rota
    // alarmePedido o toma mais abaixo, depois da cabeça de emergência; o relato, com «está», «caiu», «agora», «acendeu»…, segue em `oleo` (a instrução de segurança)
    var ol = oleo(q);
    if (ol === 1) return 'oleo';
    // F11: «qual a tendência do óleo?» é a tendência (o histórico de cruzeiro), não a leitura do manômetro; o relato de queda segue acima, em `oleo`
    if (tendenciaPergunta(q)) return 'preditiva';
    // pedido de socorro que a lista SOS não pega («isso é real, preciso de ajuda», «isso não é um teste», «estamos em risco»): a instrução de segurança, local (revisão 3 da P3C)
    if (socorroImplicito(q)) return 'sos';
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
    if (has(q, ['mmsi'])) return mmsiRota(q);
    // P3E (revisão 4): a cabeça de equipamento de segurança antes de qualquer rota de dado (a pergunta mista é do equipamento, local, sem o quadro: trava 10)
    var eq = equipRota(q); if (eq) return eq;
    // F16: o botão «O que verificar?» do relato: a busca no FAQ e nos guias pelo texto do relato (e a IA, se a tela a chamar), antes das rotas por palavra (depois da emergência e da cabeça de segurança)
    if (relatoVerificaPergunta(q)) return 'relatoVerifica';
    if (ol) return 'oleoLeitura';   // a leitura calma da pressão de óleo (o relato, ol === 1, já saiu lá em cima): depois da cabeça de equipamento de segurança, que ela não toma («onde fica o EPIRB, qual a pressão do óleo?»)
    // F12/F15 (depois da cabeça de emergência: a pergunta de segurança nunca é delas): o pedido de alarme (incompleto também), o «apagar alarme #n», os alarmes pedidos e o «agendar … para dd/mm»
    if (almPedido(q)) return 'alarmePedido';
    if (almApagaN(qRaw) >= 0) return 'alarmeApaga';
    if (almLista(q)) return 'alarmesLista';
    if (!!achaAgendar(qRaw)) return 'agendar';
    if (capacidadesPergunta(q)) return 'capacidades';   // F26
    if (has(q, ['seguro para sair', 'posso sair', 'da pra sair', 'da para sair', 'seguro sair', 'avalie vento', 'sair hoje', 'seguro navegar', 'seguro para navegar', 'posso navegar', 'podemos sair', 'podemos navegar', 'da pra navegar', 'da para navegar'])) return 'seguro';
    // P3C: as rotas da navegação e do cadastro, depois do «seguro para sair» e antes da telemetria («leituras da profundidade» é a profundidade). Nenhuma toma «checklist de chegada»,
    // «alarme de óleo acendeu» (o óleo vem antes), «temperatura hoje» (o clima) nem «alarme de fluxo da climatização» (a resposta pronta cede ao trecho do guia).
    // (a pergunta mista com o EPIRB, o Seafire, o canal 16, o PAN-PAN ou o DSC segue a rota do equipamento, mais abaixo: as rotas de leitura calma — o AIS também — já a deixam de fora pela lista branca)
    if (navegacaoPergunta(q)) return 'navegacao';
    if (embarcacaoPergunta(q)) return 'embarcacao';   // «o deslocamento do Seakeeper» e «o registro do EPIRB» são do equipamento
    if (has(q, PESSOAS_PALAVRAS) && leitura(q, PESSOAS_OK)) return 'pessoas';   // «temos 6 pessoas a bordo» é relato (com número), não pergunta
    if (pecasPergunta(q)) return 'pecas';   // F22: o estoque de peças (a pergunta de reparo, de vida útil ou de código segue o guia ou a IA)
    if (profundidadePergunta(q)) return 'profundidade';   // (a profundidade, o motor, as ondas e a água do mar só respondem a pergunta NEUTRA: o EPIRB, o canal 16 etc. na pergunta já a deixam de fora)
    if (etaPergunta(q) || (RESUMO_VIAGEM.test(q) && soNeutras(q, RESUMO_VIAGEM_OK))) return 'eta';
    if (alarmesPergunta(q)) return 'alarmes';
    if (arrefecimentoPergunta(q)) return 'arrefecimento';
    if (!EM_SOS && leituraBordoDe(q)) return 'leituraBordo';
    // «quando é a próxima troca de óleo?»: a troca dos MOTORES (as horas e a data que faltam, dos horímetros); com o equipamento (gerador, Seakeeper…) a pergunta tem palavra fora da lista e é o guia dele
    if (has(q, PROX_TROCA) && has(q, ['oleo', 'revisao']) && leitura(q, FALTA_TROCA_OK + 'e eh vai vence ')) return 'horimetros';
    // «quanto falta para a troca de óleo / a revisão?»: as horas que faltam são dos horímetros (a manutenção, sem horas)
    if (has(q, FALTA_PALAVRAS) && has(q, ['troca', 'revisao', 'oleo', 'horas de motor']) && leitura(q, FALTA_TROCA_OK)) return 'horimetros';
    if (has(q, ['telemetria', 'leituras', 'sensores', 'como esta o barco', 'estado do barco', 'status do barco'])) return 'telemetria';
    if (has(q, ['anomalia', 'pendencia', 'problema aberto'])) return 'anomalias';
    if (has(q, ['diario'])) return 'diarioLer';
    // a corrente da âncora (a amarra, em metros no contador do guincho) não é a de maré: «quantos metros de corrente?», «quanta corrente tem lançada?», «corrente no contador» → ancora, antes da maré
    if (CORRENTE_ANCORA.test(q) && !has(q, [' mare', 'correnteza', 'corrente de mare'])) return 'ancora';
    if (has(q, [' mare', 'correnteza', 'corrente de mare']) || (has(q, [' corrente']) && !has(q, ['bateria', 'carregador', 'eletric', 'tensao', 'amper', 'alternada', 'continua', 'shore', 'tomada', ' ac ', ' dc ', 'ancora', 'amarra']))) return 'mare';
    if (has(q, [' clima ', 'climatic', 'tempo hoje', ' vento', ' ventando', ' ventania', 'chuva', 'chover', 'chovendo', 'meteor', 'temperatura hoje']) || (has(q, ['previsao']) && !has(q, [' revisao', 'manutenc', 'devoluc', 'entrega', 'chegada']))) return 'clima';
    if (ondasPergunta(q)) return 'ondas';
    if (aguaPergunta(q)) return 'temperaturaAgua';
    if (has(q, ['para onde', 'destino', 'passeio', 'onde vamos', 'melhor rota', 'rota para', 'rota ate'])) return 'destinos';
    // F09: os 4 checklists; «fundeio» e «abastecimento» antes da chegada e da saída («checklist ao fundear» não é o de saída). A cabeça de emergência (cabecaEmerg: o EPIRB e a baliza, o Seafire, o canal 16, o
    // PAN-PAN, o DSC, o rádio/VHF, o botão DISTRESS, o MMSI, a salvatagem, o socorro, o óleo) é do equipamento (a instrução de segurança, local, sem o quadro: trava 10): os checklists, que levam a velocidade e
    // o resto do quadro, não a tomam («checklist de fundeio, onde fica o EPIRB?»). A guarda é a MESMA das outras rotas novas e fica no topo, antes de qualquer outra regra delas.
    if (!cabecaEmerg(q)) {
      if (has(q, CHECK_PALAVRAS) && has(q, ['fundei', 'fundear', 'ancorar', 'ancoragem'])) return 'checklistFundeio';
      if (has(q, CHECK_PALAVRAS) && has(q, ['abastec'])) return 'checklistAbastecimento';
      if (has(q, ['checklist de chegada', 'chegada']) || (has(q, CHECK_PALAVRAS) && has(q, ['atrac', 'chegar']))) return 'checklistChegada';
      if (has(q, CHECK_PALAVRAS) || checkSaida(q)) return 'checklist';
    }
    if (has(q, ['autonomia']) || (has(q, ['alcance']) && !has(q, [' vhf', ' radio', 'radar', ' ais ', 'antena', 'sinal', 'wifi', 'wi-fi', 'bluetooth', 'celular']))) return 'autonomia';
    // "Situação e vencimento do documento: NF de abastecimento…" é documento: a palavra documento/licença/vencimento vence a do combustível
    if (has(q, ['document', 'licenc', 'vencimento']) && has(q, ['consumo', 'l/h', 'litros por hora', 'abastec', 'diesel', 'combustivel', 'nota fiscal', 'nf-e'])) return 'docsvenc';
    if (has(q, ['consumo', 'l/h', 'litros por hora']) || (has(q, [' consome ', ' consomem ', 'consumindo', 'consumimos', 'gastamos', 'gastando', 'litros gastos', ' gasta ']) && !has(q, ['oleo', 'agua', 'bateria', 'energia']))) return 'consumo';
    if (has(q, ['abastec', 'diesel', 'combustivel', 'nota fiscal', 'nf-e'])) return 'autonomia';
    if (has(q, ['tanque', 'agua doce', 'cinzas', 'negras'])) return 'tanques';
    // "próxima revisão" sem equipamento = motores; com equipamento, a rota dele (Seakeeper, climatização, gerador…)
    if (has(q, ['horimetro', 'horas de motor', 'horas do motor', 'horas dos motores']) || (has(q, ['proxima revisao']) && !has(q, EQUIP))) return 'horimetros';
    if (epirbRelato(q)) return 'epirb';
    // "supressão" (PROMPT §2.3): é o nome do Seafire nos dados ("sistema fixo de supressão", sem "incêndio", que abriria o SOS). 1b: o sistema
    // fixo que disparou ou descarregou também é do Seafire (o "não abra o acesso ao motor" e o desligamento são os passos de protocolos.seafire);
    // "extintor" saiu daqui para a salvatagem (sem fogo) ou para a SOS (com fogo)
    if (seafirePergunta(q)) return 'seafire';
    // documento/licença antes do rádio: "Licença de estação" é documento, não MAYDAY
    if (has(q, DOC_PALAVRAS)) return 'docsvenc';
    // «quando vence o seguro?», «a licença vence quando?»: o vencimento do papel é do documento (antes da agenda, que também tem «vence»); o «seguro para sair» é a rota `seguro`
    if (has(q, ['vence', 'vencimento', 'vencer', 'validade', 'renova', 'vencendo', 'venceu']) && has(q, [' seguro ', 'apolice', 'licenca', 'documento', 'certificado', ' tie ', 'habilitacao', 'capitania', 'registro do barco'])) return 'docsvenc';
    // o AIS tem a rota dele, antes do canal16 (PROMPT §2.2: a pergunta do AIS não é o roteiro MAYDAY nem liga a conversa em emergência); o MMSI foi para a rota mmsi, acima
    if (aisPergunta(q)) return 'ais';   // (só a pergunta NEUTRA do status; «o AIS parou», «sem sinal do AIS», «AIS desligado» seguem o guia ou a IA, nunca a contagem de alvos)
    if (has(q, CANAL16_ROTA)) return 'canal16';
    if (has(q, ['contato', 'telefone', 'equipe', 'oficina', 'quem chamar', 'tecnico de bordo', 'marina da base'])) return 'contatos';
    // "bomba" sozinha é a de porão. Com o nome de outra bomba (água salgada, rotor, impeller, climatização, gerador, motor, estabilizador…) a
    // pergunta segue a rota do outro assunto ou o guia dele: "como trocar o rotor da bomba de água salgada" é o g_motores §7, e a resposta
    // pronta do porão ("Teste de bombas de porão e alarmes… SEM LEITURA") não responde. (Revisão 6 do C5: o trechoServe barra o guia de outro
    // equipamento quando a chave é 'porao'; antes do C5, e na revisão 4, a pergunta ia ao guia certo.)
    // «o rotor do gerador está atrasado?», «a troca do filtro está em atraso?»: a agenda (a tarefa atrasada), não o guia nem a leitura do equipamento
    if (has(q, ['atrasad', 'em atraso']) && has(q, ['rotor', 'impeller', 'filtro', 'anodo', 'zinco', 'revisao', 'troca', 'tarefa', 'manutenc', 'servico', 'limpeza', 'teste', 'inspec', 'cartas', 'oleo']) && !has(q, [' como ', 'chegar', 'chegada'])) return 'manutencao';
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
    if (has(q, ['manutenc', 'atrasad', 'agenda', 'tarefa']) || (has(q, ['vence']) && !(has(q, ['venceu', 'vencedor', 'venceram']) && foraBarcoPergunta(q)))) return 'manutencao';
    if (has(q, ['bateria', '24 v', '24v', '12 v', '12v', 'eletric', 'tensao', 'voltagem', 'carregador'])) return 'eletrico';
    if (posicaoPergunta(q)) return 'posicao';
    // "Rajada" é a previsão do dia só em pergunta de previsão ("vai ter rajada hoje?", "como estão as rajadas?", "previsão de rajada"),
    // e depois das rotas de equipamento. "Hoje"/"agora" sozinhos não bastam: relato ("pegamos uma rajada agora e o barco adernou",
    // "a rajada de hoje arrancou o toldo", "a âncora garrou com a rajada"), pessoa em risco e limite do barco seguem o equipamento ou a IA.
    if (has(q, [' rajada']) && (RAJADA_SO.test(q) || has(q, ['previs', 'vai ter rajada', 'tem rajada', ' ha rajada', 'havera rajada', 'como estao as rajadas', 'como esta a rajada', 'como vao estar as rajadas']))
      && !has(q, RAJADA_RELATO)) return 'clima';
    // foraBarco (PROMPT §2.7): depois de todas as rotas de bordo e antes do fallback; local, sem IA, sem preço nem número
    if (foraBarcoPergunta(q)) return 'foraBarco';
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
  var SINAL_RAIZES = {}; ['canal', 'cardinal', 'lateral', 'farol', 'luz', 'barra', 'entrada', 'piscando', 'boia', 'boias', 'balizamento', 'balizar',
    // (revisão 5) o que descreve a boia de balizamento: a sinalização e o tipo (luminosa, náutica, perigo isolado), a cor e o lado (vermelha, verde, amarela, bombordo, boreste, estibordo) e o estado dela (apagada, torta, deslocada, fora do lugar)
    'sinalizacao', 'sinalizar', 'luminosa', 'luminoso', 'nautica', 'nautico', 'isolado', 'isolada', 'vermelha', 'vermelho', 'verde', 'amarela', 'amarelo', 'cor', 'cores', 'bombordo', 'boreste', 'estibordo',
    'apagada', 'apagado', 'apagou', 'torta', 'torto', 'deslocada', 'deslocado', 'fora', 'deriva', 'derivando'].forEach(function (w) { SINAL_RAIZES[raiz(w)] = 1; });
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

  // ——— FAQ dos equipamentos (F10; CONTRATO §1.6) ———
  // faq-equipamentos.json (gerado; 91 itens: os 9 cartões de emergência EM-01…09 e uma pergunta por seção dos guias) responde no chat com o CÓDIGO do item e a fonte dele. Três jeitos de chegar:
  //  (1) o item pedido pelo código (`ctx.faq`: o toque numa pergunta do FAQ, F6 na Fase 4): sempre o item, qualquer que seja o texto;
  //  (2) a pergunta digitada ou falada que NENHUMA resposta pronta nem trecho do guia responde (o `fallback`) e que casa, bem de perto, com um item: o item no lugar da IA;
  //  (3) nunca no lugar do que já responde (a resposta pronta, o trecho do guia, a emergência): essas rotas seguem como estavam.
  // O cartão de emergência (`emerg`) e todo item com `seguranca: true` é procedimento padrão: nunca vai à IA (pedeIA false) e a resposta de emergência não leva o quadro. O arquivo entra no CORE do sw.js
  // (abre offline). Sem o arquivo (rede, SOS), nada muda: o chat segue como antes. No SOS ele nem é pedido.
  var FAQ = { dados: null, itens: null, idx: null, df: {}, media: 1, carregando: null };
  function indexaFaq(lista) {
    var idx = {}, df = {}, soma = 0;
    lista.forEach(function (it) {
      var tf = {}, n = 0, campo = function (txt, peso, so) {
        tokens(txt).forEach(function (w) { tf[w] = (tf[w] || 0) + peso; n++; if (so) so[w] = 1; });
      }, t = {}, r = {};
      campo((it.titulo || '') + ' ' + (it.pergunta || '') + ' ' + (it.variantes || []).join(' ') + ' ' + (it.equip || ''), 3, t);
      campo((it.resposta || '') + ' ' + (it.acao || ''), 2, r);
      campo((it.passos || []).join(' ') + ' ' + (it.atencao || '') + ' ' + (it.senao || '') + ' ' + (it.obs || ''), 1, null);
      Object.keys(tf).forEach(function (w) { df[w] = (df[w] || 0) + 1; });
      idx[it.id] = { tf: tf, n: n, t: t, r: r }; soma += n;
    });
    FAQ.idx = idx; FAQ.df = df; FAQ.media = soma / lista.length;
  }
  // Promise: true quando o arquivo está carregado (uma busca só; sem rede devolve false e a próxima pergunta tenta de novo). No SOS nunca busca.
  function carregaFaq() {
    if (EM_SOS || !window.fetch) return Promise.resolve(false);
    if (FAQ.itens) return Promise.resolve(true);
    if (FAQ.carregando) return FAQ.carregando;
    FAQ.carregando = fetch('./faq-equipamentos.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
      if (!j || !Array.isArray(j.itens) || !j.itens.length) return false;
      indexaFaq(j.itens); FAQ.dados = j; FAQ.itens = j.itens;
      return true;
    }).catch(function () { return false; }).then(function (ok) { FAQ.carregando = null; return ok; });
    return FAQ.carregando;
  }
  function faqItem(id) { var l = FAQ.itens; if (EM_SOS || !l || typeof id !== 'string') return null; return l.filter(function (it) { return it.id === id; })[0] || null; }
  // até n itens { it, nota, cobre, titulo, principal } (BM25 com os sinônimos da base): cobre = a fração das palavras da pergunta que o item tem; titulo = as que estão no título, na pergunta, nas
  // variantes ou no equipamento; principal = essas ou na resposta e na ação. Pergunta de uma palavra só não busca (é vaga: «gerador» tem a rota dele).
  function faqBusca(q, n) {
    var qs, grupos, N, daBaliza, sinal, k1 = 1.2, b = 0.75, res = [];
    if (EM_SOS) return [];
    if (!FAQ.itens) { carregaFaq(); return []; }
    // sem as palavras genéricas da identidade da base («em CASO de alarme», «antes», «depois», «padrão», «protocolo»…): elas não dizem de que assunto a pergunta é, e «caso de alarme» abriria o item do fogo
    qs = tokens(q).filter(function (w, k, a) { return a.indexOf(w) === k && !IDENT_GENERICAS[w]; });
    if (qs.length < 2) return [];
    // a baliza de sinalização («a baliza do canal está apagada») não é o EPIRB, como na busca da base: sem a palavra que só o EPIRB tem, o item do EPIRB sai e «baliza» não vira «epirb»
    daBaliza = qs.some(function (w) { return BALIZA_RAIZES[w]; });
    sinal = daBaliza && qs.some(function (w) { return SINAL_RAIZES[w]; }) && !qs.some(function (w) { return EPIRB_SO[w]; });
    grupos = qs.map(function (w) { var g = {}; g[w] = 1; ((sinal && w === RAIZ_BALIZA) ? [] : (SINONIMOS[w] || (daBaliza && SINONIMOS_BALIZA[w]) || [])).forEach(function (x) { x = raiz(x); if (!g[x]) g[x] = 0.6; }); return g; });
    N = FAQ.itens.length;
    FAQ.itens.forEach(function (it) {
      var d = FAQ.idx[it.id], nota = 0, cobre = 0, titulo = 0, principal = 0;
      if (sinal && /EPIRB/.test(it.equip || '')) return;
      grupos.forEach(function (g) {
        var melhor = 0, tem = false, noT = false, noP = false, w, f;
        for (w in g) {
          f = d.tf[w]; if (!f) continue;
          tem = true; if (d.t[w]) { noT = true; noP = true; } if (d.r[w]) noP = true;
          melhor = Math.max(melhor, g[w] * Math.log(1 + (N - FAQ.df[w] + 0.5) / (FAQ.df[w] + 0.5)) * (f * (k1 + 1)) / (f + k1 * (1 - b + b * d.n / FAQ.media)));
        }
        if (tem) { cobre++; nota += melhor; } if (noT) titulo++; if (noP) principal++;
      });
      if (nota > 0) res.push({ it: it, nota: nota, cobre: cobre / grupos.length, titulo: titulo / grupos.length, principal: principal / grupos.length });
    });
    res.sort(function (x, y) { return y.nota - x.nota; });
    return res.slice(0, n || 3);
  }
  // O texto do item: a resposta (a 1ª linha, a falada; o cartão de emergência já traz o rótulo do procedimento padrão), os passos, a atenção, «se não resolver» e a observação; a fonte com o código.
  function faqResposta(it, p) {
    var passos = it.passos || [], max = 8, fs = (it.fontes || []).map(function (f) { return f.texto; });
    // a 1ª linha (a falada) abre com o TÍTULO do item (o assunto, o equipamento): vários itens começam com um verbo sem sujeito («Ligue pelo display…»), e o texto do chat não tem outro cabeçalho. O cartão de
    // emergência (EM-01…09) não: abre com a instrução de segurança, inteira (trava 10)
    var text = (it.titulo && !it.emerg ? it.titulo + ' — ' : '') + it.resposta + (passos.length ? '\n' + passos.slice(0, max).map(function (x, i) { return (i + 1) + '. ' + x; }).join('\n') + (passos.length > max ? '\n… mais ' + (passos.length - max) + ' passos no FAQ (' + it.id + ').' : '') : '')
      + (it.atencao ? '\nAtenção: ' + it.atencao : '') + (it.senao ? '\nSe não resolver: ' + it.senao : '') + (it.obs ? '\nObservação: ' + it.obs : '');
    return { key: 'faqEquip', text: text, src: 'Fonte: FAQ dos equipamentos ' + it.id + (fs.length ? ' · ' + fs.join(' · ') : ''), actions: act(p, [['FAQ de bordo', 'faq']].concat(it.emerg ? [['Abrir SOS', 'sos']] : [])),
      faq: it.id, emerg: !!it.emerg, seguranca: !!it.seguranca, ref: fs[0] || '' };
  }
  // A pergunta que casa BEM de perto com UM item: todas as palavras dela estão no item, a maioria no título, na pergunta ou nas variantes, e todas no título ou na resposta; e o 2º colocado, de
  // outra seção, não empata (pergunta genérica como «como silenciar o alarme?» fica com a IA). null = nenhum.
  function respostaFaq(q, p) {
    var rs = faqBusca(q, 3), r = rs[0];
    if (!r || r.cobre < 1 || r.principal < 1 || r.titulo < 0.6) return null;
    if (rs.length > 1 && rs[1].nota > r.nota * 0.85 && rs[1].it.secao !== r.it.secao) return null;
    return faqResposta(r.it, p);
  }
  // O botão «O que verificar?» de um relato de defeito que não casa de perto com nenhum item (a frase inteira — quando, onde, quantas vezes — dilui a busca): o equipamento que o relato nomeia (D.equipamentos, menos
  // os de segurança; o nome, o fabricante, o modelo ou uma das palavras do cadastro, com TODAS as palavras dela na frase — «bomba de porão» não é «a bomba de água doce» — e o que vem primeiro na frase) e, entre os
  // itens do FAQ DELE, o que mais casa com o relato. O item de alarme, temperatura, pressão, fluxo, mensagem ou água (é o que se confere num defeito) vale 1,5 vez e entra com pontuação 7; os outros, só com 11 (a
  // busca pesa o relato inteiro: abaixo disso o item só dividiria o assunto com o equipamento, e «o plotter não liga» viraria «Atualização de cartas»). Nunca o cartão de emergência. null = o relato não nomeia
  // um equipamento ou o FAQ dele não casa bem (a IA, se houver, responde).
  var FAQ_PROBLEMA = /alarme|temperatura alta|alta temperatura|pressao|pouco ar|fluxo|mensagem|engano|agua|falha/;
  function equipamentoDoRelato(nota) {
    var tk = tokens(nota), melhor = null, pos = 1e9;
    (D.equipamentos || []).forEach(function (e) {
      if (e.seguranca) return;
      [e.nome, e.fabricante, e.modelo].concat(e.palavras || []).forEach(function (x) {
        var ws = tokens(x), ks = ws.map(function (w) { return tk.indexOf(w); });
        if (ws.length && ks.every(function (k) { return k !== -1; }) && Math.min.apply(null, ks) < pos) { pos = Math.min.apply(null, ks); melhor = e; }
      });
    });
    return melhor;
  }
  function respostaRelatoEquip(nota, p) {
    var eq = equipamentoDoRelato(nota), pre, rs;
    if (EM_SOS || !eq) return null;
    pre = norm(eq.nome);
    rs = faqBusca(nota, 100).filter(function (r) { return !r.it.emerg && !r.it.seguranca && norm(r.it.equip || '').indexOf(pre) === 0; });
    rs.forEach(function (r) { r.problema = FAQ_PROBLEMA.test(norm(r.it.titulo)); r.pontos = r.nota * (r.problema ? 1.5 : 1); });
    rs = rs.filter(function (r) { return r.nota >= (r.problema ? 7 : 11); }).sort(function (x, y) { return y.pontos - x.pontos; });
    return rs.length ? faqResposta(rs[0].it, p) : null;
  }
  if (!EM_SOS) { if (window.requestIdleCallback) requestIdleCallback(carregaFaq, { timeout: 6000 }); else setTimeout(carregaFaq, 2500); }

  function responde(q, ctx, espera, fresco) {
    ctx = ctx || {};
    var p = ctx.platform || 'web';
    var key = null;
    if (espera) { key = espera === 'relatoNaoGravou' ? 'relatoCancela' : espera; if (espera === 'relatoCancela' || espera === 'relatoNaoGravou') ctx = Object.assign({}, ctx, { espera: espera === 'relatoCancela' ? true : 'nao' }); }   // F17: a fala depois de «o que devo registrar?» (a espera foi consumida em answer); `espera: 'nao'` = a fala que não foi gravada nem cancelou nada
    // F10 (1): o item do FAQ pedido pelo código (o toque numa pergunta do FAQ): é o item, qualquer que seja o texto da pergunta
    if (typeof ctx.faq === 'string' && !ctx.id) { var fi = faqItem(ctx.faq); if (fi) return faqResposta(fi, p); }
    if (!key && ctx.id && ANSWERS[ctx.id] && (!String(q || '').trim() || norm(q).trim() === CANON[ctx.id])) key = ctx.id;
    if (!key) key = route(q);
    if (!ANSWERS[key]) key = 'fallback';
    var a;
    try { a = ANSWERS[key](p, ctx, String(q || '').trim()); } catch (e) { key = 'fallback'; a = ANSWERS.fallback(p, ctx); }
    // toda resposta de dado de bordo leva a hora do instante (decisão 5): a que não a traz no texto nem na fonte ganha «consultado às HH:MM:SS» na fonte
    if (!SEM_HORA_NA_FONTE[key] && sim() && vivo() && a && a.src && !/\d\d:\d\d:\d\d/.test(a.text + '\n' + a.src)) a.src += ' · consultado às ' + vivo().hora;
    // Sem resposta pronta, ou pergunta específica sobre um equipamento (como, código, óleo, alarme, onde fica…): o trecho do guia vale mais que o resumo genérico.
    var rota0 = key;
    var qEsp = fresco != null ? fresco : q;   // (a pergunta continuada com assunto próprio — «… — e o gerador?» — é «específica» pela fala nova, não pelo «como» da pergunta de antes)
    if (key === 'fallback' || (GENERICAS[key] && (ESPECIFICA.test(' ' + norm(qEsp) + ' ') || (key === 'ais' && !AIS_STATUS.test(' ' + norm(qEsp) + ' '))))) { var kb = null; try { kb = respostaBase(q, p, key === 'fallback' ? null : key); } catch (e) {} if (kb) { a = kb; key = 'base'; } }
    // P3E (revisão 4): a cabeça de segurança sem rota própria (o botão DISTRESS, a baliza do EPIRB) com uma cauda que dilui a busca («o botão DISTRESS, checklist de saída»; ou que puxa um trecho de outro
    // assunto: «a baliza, nível dos tanques»): o trecho de segurança dela, pela cabeça, local (pedeIA false) — nunca o fallback, que iria à IA na nuvem, nem o trecho da cauda
    if (rota0 === 'fallback' && (key === 'fallback' || key === 'base') && !a.seguranca) { var cq = cabecaSemRota(pad(q)), kc = null; if (cq) { try { kc = respostaBase(cq, p, null); } catch (e) {} if (kc && kc.seguranca) { a = kc; key = 'base'; } } }
    // F10 (2): sem resposta pronta e sem trecho do guia (o fallback, que iria à IA), a pergunta que casa bem de perto com um item do FAQ é respondida por ele — menos a de cabeça de emergência (cabecaEmerg), que é do equipamento
    if (key === 'fallback' && !cabecaEmerg(pad(q))) { var fq = null; try { fq = respostaFaq(q, p); } catch (e) {} if (fq) { a = fq; key = 'faqEquip'; } }
    // P3E (revisão 5): a cabeça de emergência que ficou no fallback (o guia não carregou: o trecho de segurança do botão DISTRESS ou da baliza do EPIRB não veio, ou a cauda não o deixou subir) é a instrução de
    // segurança da família dela, local, e NUNCA o fallback, que leva a situação de bordo (SOG, proa, motores, a hora do quadro: trava 10). A baliza do EPIRB dá a resposta do EPIRB; o botão DISTRESS, a do canal 16.
    if (key === 'fallback' && cabecaEmerg(pad(q))) { var fam = cabecaSemRota(pad(q)); key = fam === 'baliza' ? 'epirb' : fam ? 'canal16' : 'sos'; try { a = ANSWERS[key](p, ctx, String(q || '').trim()); } catch (e) { key = 'sos'; a = ANSWERS.sos(p, ctx, ''); } }
    a.key = key;
    return a;
  }
  // a resposta leva o instante dela (fora do JSON): a ficha(p, q, a) e o resumoAgora(a) da MESMA pergunta o reaproveitam
  function marca(a) { if (a && typeof a === 'object' && !emerg(a)) { try { Object.defineProperty(a, '_inst', { value: CONG.inst, enumerable: false, configurable: true }); } catch (e) {} } return a; }
  // ——— Contexto da conversa (F31; o F18 da P3F o estende) ———
  // O mínimo para a fala que só diz o equipamento: a última pergunta e a resposta que o app deu, por 10 min. A resposta local nunca termina em pergunta; a da IA na nuvem pode («Qual equipamento?»),
  // e o cérebro não a vê: a tela a conta com B.conversa(pergunta, texto). «O gerador» depois de «Qual equipamento?» continua a pergunta anterior («como ligar? — o gerador»); sozinha, é a resposta
  // pronta do gerador. NOVA e ENCERRAR zeram (B.limpaConversa). O que o app não grava (commit false, link) e a emergência não entram.
  var CONV = { q: '', a: '', t: 0, pergunta: false, n: 0, reg: false };   // `reg`: a última fala foi um registro (a próxima é assunto novo)
  var CONV_VALE = 10 * 60e3;
  // O que a conversa guarda (a pergunta até 500 letras, a resposta até 600): SEM coordenadas, e o filtro vem ANTES do corte — cortar primeiro deixa meia coordenada («048°») que o semCoord não reconhece
  // (revisão 2 da P3F). O que o CONV guarda é o que vai à IA em `anterior` e em `junto`.
  function guardaConv(t, max) { return semCoord(String(t == null ? '' : t)).slice(0, max); }
  function limpaConversa() { CONV = { q: '', a: '', t: 0, pergunta: false, n: (CONV.n || 0) + 1, reg: false }; ESPERA_REG = null; REL = null; PEND_CHAT = null; DESFAZ = null; ALVO_PROP = null; }   // NOVA e ENCERRAR zeram também o «o que devo registrar?» e a proposta de relato que espera
  function terminaEmPergunta(t) {
    var ls = String(t || '').split(/\n+/).map(function (l) { return l.trim(); }).filter(Boolean);
    return ls.length > 0 && /\?["”')\]]*$/.test(ls[ls.length - 1]);
  }
  // A pergunta de emergência (SOS, óleo, canal 16, EPIRB, Seafire, salvatagem, MMSI do rádio): ela e a resposta dela nunca entram no contexto, e ENCERRAM o que havia (a fala «o gerador» depois de
  // «mayday» é a resposta pronta do gerador, nunca a continuação da pergunta de antes da emergência).
  function perguntaEmerg(q) { var n = pad(q); return !!(emergencia(n) || oleo(n) === 1 || cabecaEmerg(n) || EMERG[route(q)] === 1); }   // (a cabeça de segurança sem rota própria — o botão DISTRESS, a baliza do EPIRB — também: a resposta dela é a instrução de segurança)
  function conversa(q, texto) {
    if (EM_SOS || !String(q || '').trim()) return;
    if (perguntaEmerg(q)) { limpaConversa(); return; }
    // O relato que cai na IA (sem rota local) é respondido pela nuvem e a tela conta a conversa DEPOIS (esta função), que sobe o `n`: o «sim» curto da proposta (REL.n = a conversa dela) deixaria de valer. Realinha
    // só quando esta é a pergunta que abriu a proposta e nada mais foi respondido no meio (REL.n ainda é o da conversa de agora); outra pergunta no meio, ou outra pergunta agora, não realinha.
    var alinha = !!(REL && REL.q && REL.n === CONV.n && REL.q === limpaT(corrigeVoz(q), 500));
    CONV = { q: guardaConv(String(q).trim(), 500), a: guardaConv(texto, 600), t: Date.now(), pergunta: terminaEmPergunta(texto), n: (CONV.n || 0) + 1, reg: false };
    if (alinha) REL.n = CONV.n;
  }
  // o vocabulário de equipamento: nome, fabricante, modelo e as palavras do cadastro (D.equipamentos), normalizados
  var NOMEIA_LIGA = ' e eh sao era o a os as um uma uns umas do da dos das de no na nos nas sim nao acho que creio so mesmo isso esse essa este esta ele ela la aqui modelo marca tipo ';
  function vocabEquip() {
    var v = {};
    (D.equipamentos || []).forEach(function (e) {
      [e.nome, e.fabricante, e.modelo].concat(e.palavras || []).forEach(function (x) { norm(x).split(/[^a-z0-9]+/).forEach(function (w) { if (w.length >= 2 && NOMEIA_LIGA.indexOf(' ' + w + ' ') === -1) v[w] = 1; }); });
    });
    return v;
  }
  // Fala que só identifica o equipamento ou a marca: tirando os artigos, «é/são», «sim/não» e «acho que», sobram nomes de equipamento, marca, modelo ou código (letra com número).
  // Verbo ou outra palavra = fala com conteúdo próprio.
  function soNomeia(n) {
    var ws = n.trim().split(/\s+/), voc = vocabEquip(), tem = false, i, w;
    for (i = 0; i < ws.length; i++) {
      w = ws[i];
      if (NOMEIA_LIGA.indexOf(' ' + w + ' ') !== -1) continue;
      if (voc[w] || /^(?=[a-z\-]*\d)(?=[\d\-]*[a-z])[a-z\d\-]+$/.test(w) || /^\d+$/.test(w)) { tem = true; continue; }
      return false;
    }
    return tem;
  }
  // A pergunta que a fala continua, ou null. DUAS formas de continuar:
  //  (1) F31: a resposta anterior terminou em pergunta, a fala é curta, não é pergunta, nem correção («e o gerador», «não, o gerador»), não é emergência nem óleo, só identifica o equipamento ou a marca e a rota
  //      dela é a de um equipamento (GENERICAS) — a rota da pergunta anterior não pode ser de emergência nem o registro no diário.
  //  (2) F18: a fala que CONTINUA o assunto sem repeti-lo — «e boreste?», «e a de serviço?», «e amanhã?», «e o consumo?», «também no gerador?», «boreste?» — logo depois de uma pergunta de dado (10 min, sem registro
  //      no meio). Sem assunto próprio (a rota dela sozinha é o fallback), a resposta é a da rota da pergunta anterior, com a fala nova («qual a pressão do óleo do motor BB? — e boreste?» → o óleo do BE);
  //      com assunto próprio («e o consumo?», «e o gerador?») vale a rota dela, e a pergunta junta só serve quando a rota é a mesma (a busca no guia ganha o contexto). A pergunta raiz FICA (a cadeia «e boreste?»,
  //      «e o BB?» volta sempre à primeira). Emergência, óleo, registro, a fala que é pedido de registro e o que não é dado (saudação, fora do barco, diagnóstico) não continuam nada.
  var SEG = { raiz: false }, REG_KEYS = { diario: 1, diarioPede: 1, relatoRegistra: 1, relatoCancela: 1 };
  var SEGUE_E = /^ (?:e|tambem|mas) /, LADO_SOZINHO = /^ (?:(?:o|a|de|do|da|no|na|pelo|pela) )?(?:motor )?(?:bb|be|bombordo|boreste|estibordo|esquerdo|direito|outro|outra|o outro|a outra) $/;
  // as palavras de uma fala que só varia o lado, a hora, o dia ou o banco da pergunta anterior («e boreste?», «e amanhã?», «e a de serviço?», «e o outro?»)
  var SEGUE_OK = ' e tambem mas o a os as um uma de do da dos das no na nos nas em para pra por pelo pela bb be bombordo boreste estibordo esquerdo esquerda direito direita outro outra outros outras ambos ambas lado lados servico partida principal principais amanha ontem hoje agora depois antes semana mes dia noite manha tarde hora horas proximo proxima ultimo ultima mesmo mesma ';
  var BANCO_SEGUE = /^ (?:e|tambem|mas) .*? (?:servico|partida|12 ?v|12 volts?|24 ?v|24 volts?) /, AR_AGUA_SEGUE = /^ (?:e|tambem|mas) (?:(?:a|o|do|da|de) )*(?:ar|agua|mar)(?: (?:externo|do mar))? $/;
  var RAIZ_NAO = { fallback: 1, diario: 1, diarioPede: 1, relatoRegistra: 1, relatoCancela: 1, relatoVerifica: 1, sos: 1, oleo: 1, canal16: 1, epirb: 1, seafire: 1, salvatagem: 1, mmsi: 1, diagnostico: 1, saudacao: 1, foraBarco: 1, sobreDados: 1 };
  ['alarmePedido', 'alarmeConfirma', 'alarmeCancela', 'alarmesLista', 'alarmeApaga', 'agendar', 'ticketConfirma', 'ticketRecusa', 'ticketDesfaz', 'capacidades'].forEach(function (k) { RAIZ_NAO[k] = 1; });   // (P3G: «e boreste?» não continua um pedido de alarme, uma proposta nem a lista do que o app faz)
  function seguimento(q, ctx) {
    var n, rq, rr, w, junto;
    SEG.raiz = false;
    if (EM_SOS || !CONV.q || Date.now() - CONV.t > CONV_VALE || (ctx && (ctx.id || ctx.commit === false))) return null;
    n = pad(q); w = n.trim().split(/\s+/).length;
    if (CONV.pergunta) {   // (1)
      if (w > 8 || /\?\s*$/.test(String(q)) || /^ (?:e|nao)(?= )/.test(n) || !soNomeia(n) || emergencia(n) || oleo(n) === 1) return null;
      rq = route(q); rr = route(CONV.q);
      if (!GENERICAS[rq] || perguntaEmerg(CONV.q) || rr === 'diario' || rr === 'diarioPede' || rr === 'sobreDados' || rr === 'foraBarco') return null;
      return CONV.q + ' — ' + String(q).trim();
    }
    // (2)
    if (CONV.reg || w > 8 || !(SEGUE_E.test(n) || LADO_SOZINHO.test(n))) return null;
    if (emergencia(n) || oleo(n) === 1 || socorroImplicito(n) || cabecaEmerg(n) || perguntaEmerg(CONV.q)) return null;
    rr = route(CONV.q); if (RAIZ_NAO[rr] === 1) return null;
    rq = route(q);
    junto = CONV.q + ' — ' + String(q).trim();
    // o banco da bateria («e a de partida?», «e a de 12 volts?») e o ar ou a água («e do ar?») continuam a pergunta de antes mesmo quando a rota da fala nova é outra (partida → motores) ou nenhuma
    if (rr === 'eletrico' && BANCO_SEGUE.test(n) && soNeutras(n, SEGUE_OK + 'bateria baterias banco bancos volts v 12 24 ')) { SEG.raiz = true; return junto; }
    if (rr === 'temperaturaAgua' && AR_AGUA_SEGUE.test(n)) { SEG.raiz = true; return junto; }
    if (rq === 'fallback') { if (!soNeutras(n, SEGUE_OK)) return null; SEG.raiz = true; return junto; }   // a fala sem assunto só continua se for POBRE (lado, hora, dia, «o outro»): «e como se faz um nó lais?» é pergunta nova (a IA)
    return route(junto) === rq ? junto : null;
  }
  // O lado que a FALA NOVA pede numa pergunta continuada («… — e boreste?» → 'be'; «… — e o BB?» → 'bb'): só olha depois do último « — », então o lado da pergunta anterior não conta, e a pergunta que
  // não é continuação (sem « — ») não muda de resposta. Os dois lados juntos ou nenhum → null.
  function ladoSeguinte(q) {
    var t = String(q || ''), k = t.lastIndexOf(' — '), n, be, bb;
    if (k < 0) return null;
    n = pad(t.slice(k + 3)); be = / (?:boreste|estibordo|be|direito|direita) /.test(n); bb = / (?:bombordo|bb|esquerdo|esquerda) /.test(n);
    return be && !bb ? 'be' : bb && !be ? 'bb' : null;
  }
  // a pergunta e a resposta de antes (a IA e a rota recebem; sem coordenadas), só dentro dos 10 min e fora de pedido de link
  function anteriorDe(ctx) {
    if (EM_SOS || !CONV.q || Date.now() - CONV.t > CONV_VALE || (ctx && (ctx.id || ctx.commit === false))) return null;
    return { p: semCoord(CONV.q), r: semCoord(CONV.a) };
  }
  function answer(q, ctx) {
    return congela(function () {
      var q1 = corrigeVoz(q), espera = esperaRegistro(q1, ctx), junto = espera ? null : seguimento(q1, ctx), fresco = junto && !SEG.raiz && !CONV.pergunta && route(q1) !== route(CONV.q) ? q1 : null, ant = anteriorDe(ctx), a, pe;
      if (!espera && junto && SEG.raiz) espera = route(CONV.q);   // F18: «e boreste?» não tem assunto: é a rota da pergunta anterior, com a fala nova
      a = marca(responde(junto || q1, ctx, espera, fresco));   // (fresco: a fala nova de uma pergunta continuada (F18) com OUTRO assunto — o «como» ou o «alarme» da pergunta de antes não a torna «específica»; com o mesmo assunto, ou depois de «Qual equipamento?» (F31: «o gerador» continua «como ligar?»), a pergunta junta vale, como antes)
      // a hora do instante da resposta (HH:MM:SS), em campo comum: a tela copia a resposta (Object.assign) e a cópia perde o `_inst`, que não é enumerável; a fala precisa dela. Nunca na emergência.
      if (a && typeof a === 'object' && !emerg(a) && sim() && vivo()) a.hora = vivo().hora;
      // a resposta de emergência (qualquer chave de EMERG, com ou sem commit) encerra o contexto anterior; as outras o regravam, se o app grava
      // (pe: a PERGUNTA é de emergência — o «registre no diário: tem fogo no motor» responde `diario` com os passos do SOS, chave que não é de emergência, mas a conversa também acaba nele: nem a pergunta nem a resposta vão à IA)
      pe = !EM_SOS && perguntaEmerg(q1);
      if (!EM_SOS) {
        if (emerg(a) || pe) limpaConversa();
        else if (!ctx || ctx.commit !== false) CONV = { q: junto ? CONV.q : guardaConv(String(q1 == null ? '' : q1).trim(), 500), a: guardaConv(a.text, 600), t: Date.now(), pergunta: terminaEmPergunta(a.text), n: (CONV.n || 0) + 1, reg: REG_KEYS[a.key] === 1 };
        // a proposta que esta resposta armou (alarme pedido, agendamento) e o que ela acabou de confirmar/fechar valem a partir da conversa seguinte: o «sim» curto só vale LOGO depois
        if (PEND_CHAT && PEND_CHAT.n === undefined) PEND_CHAT.n = CONV.n;
        if (DESFAZ && DESFAZ.n === undefined) DESFAZ.n = CONV.n;
      }
      if (ant && !emerg(a) && !pe) { a.anterior = ant; a.junto = junto || ''; }   // F18: a pergunta e a resposta de antes vão com a resposta (a IA recebe; sem coordenadas); `junto` é a pergunta que a rota viu
      acrescentaRelato(a, a.key, String(q1 == null ? '' : q1).trim(), ctx);   // F16: o relato vira proposta (a hora do instante já está na resposta)
      return a;
    });
  }


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
    if (cabecaEmerg(pad(String(q || '')))) return false;   // P3E (revisão 4): a pergunta de cabeça de emergência é local, qualquer que seja a rota que a tenha tomado (trava 10: nunca na IA)
    if (k !== 'fallback' && k !== 'base' && k !== 'saudacao' && k !== 'faqEquip' && k !== 'relatoVerifica') return false;
    var topo = String(q || '').trim() ? buscaBase(q, 1)[0] : null;
    if (topo && topo.d.seguranca) return false;
    if (k === 'fallback' || k === 'base' || k === 'faqEquip' || k === 'relatoVerifica') return true;   // (o item de segurança do FAQ já saiu acima: a.seguranca)
    return !!String(q || '').trim() && !SO_OI.test(pad(q));
  }
  // O histórico que vai à IA (F18, PROMPT §2.8): as últimas 6 mensagens (não vazias) da conversa em {papel, texto}, cada texto SEM coordenadas (o semCoord corta antes do limite de 600 letras, para não deixar meia coordenada). A tela monta a lista (papel 'usuario' | 'capitao', ou role 'user' | 'bot'); aqui só se limpa. O cliente da IA repete o filtro antes de mandar (Fase 6).
  // A emergência NUNCA entra no histórico (PROMPT §2.2, trava 10): o turno do usuário que é pergunta de emergência (perguntaEmerg: SOS, óleo, canal 16, EPIRB, Seafire, salvatagem, MMSI do rádio, o botão DISTRESS, a baliza
  // do EPIRB, e o «registre no diário: tem fogo no motor», que responde com os passos do SOS) sai, com a(s) resposta(s) do capitão que o seguem; a resposta que traz a instrução de segurança (abre com «Emergência —»,
  // ou leva a ordem do MAYDAY ou os passos do óleo) sai mesmo que a pergunta dela tenha ficado fora da janela. Isto antes do corte nas 6 últimas.
  function respostaEmerg(t) { var s1 = SOS_PASSOS.slice(0, 60), s2 = OLEO_PASSOS.slice(0, 40); return /^\s*Emergência\s—/.test(t) || (!!s1 && t.indexOf(s1) !== -1) || (!!s2 && t.indexOf(s2) !== -1); }   // (o trecho vazio acharia-se em todo texto)
  function historicoIA(msgs) {
    var fora = false;
    return (Array.isArray(msgs) ? msgs : []).map(function (m) {
      var bot = m && (m.papel === 'capitao' || m.role === 'bot'), t = m ? (m.texto != null ? m.texto : m.text) : '', bruto = String(t == null ? '' : t);
      return { papel: bot ? 'capitao' : 'usuario', texto: semCoord(bruto).slice(0, 600), bruto: bruto };
    }).filter(function (m) {
      if (m.papel === 'usuario') fora = !!m.bruto.trim() && perguntaEmerg(m.bruto);
      return m.texto.trim() && !fora && !(m.papel === 'capitao' && respostaEmerg(m.bruto));
    }).map(function (m) { return { papel: m.papel, texto: m.texto }; }).slice(-6);
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
  // PROMPT §2.8 (vale nos dois modos: é privacidade, não simulação): graus-minutos com vírgula ou ponto, com ou sem espaço e sinal (26°59,6'S, -26°59.6', 26°59'S, 26°59'35"S, 26º 59,6),
  // decimais com 4 ou mais casas (-26.9931) ou em par (-26,993 / -48,614; -26.993,-48.614) — e NUNCA o milhar do pt-BR (1.236,4 h, 1.600 L, 2.050 rpm, 12.000). A mesma regra do R_COORD do
  // testes/cerebro.py e do gerador (ferramentas/demo/confere.py). O par de coordenadas que o texto traz vira UM aviso só.
  var COORD_RX = /-?\d{1,3}\s*[°º]\s*\d{1,2}\s*[,.]\s*\d+\s*['′’]?\s*[NSEWLO]?|-?\d{1,3}\s*[°º]\s*\d{1,2}\s*['′’]\s*(?:[NSEWLO]|\d{1,2}(?:[,.]\d+)?\s*(?:["″”]|''|’’))|-?\d{1,3}[.,]\d{4,}(?!\d)|-?\d{1,3}[.,]\d{3,}\s*[;\/]\s*-?\d{1,3}[.,]\d{3,}|-\d{1,3}[.,]\d{3,}\s*,\s*-?\d{1,3}[.,]\d{3,}/g;
  var SEM_COORD = '(coordenadas só na tela do app)', SEM_COORD_PAR = new RegExp('\\(coordenadas só na tela do app\\)(?:\\s*[,;/·]?\\s*\\(coordenadas só na tela do app\\))+', 'g');
  function semCoord(s) { return String(s || '').replace(COORD_RX, SEM_COORD).replace(SEM_COORD_PAR, SEM_COORD); }
  // Ficha de bordo para a IA na nuvem: o que o app sabe agora, bloco a bloco, com a fonte de cada um — os mesmos textos das
  // respostas prontas, então a IA e a tela dizem os mesmos números. Sem coordenadas e sem telefones. ~9 mil letras
  // (o proxy aceita até 12 mil). ficha(p, q, a): pergunta pura sobre o próprio app ("o que você faz?") leva só a ficha
  // RESUMIDA (agora, sobre o app, embarcação, equipamentos — ~3 mil letras). Com assunto ("o que você sabe sobre o
  // seguro?") ou trecho do guia ("quando foi a última troca de óleo?"), a completa: a resumida tirava o dado pedido (1.0.7).
  var ASSUNTO = / (?:sobre|de|do|da|dos|das|no|na|com|quando|qual|quais|quanto|onde) (?!(?:voce|vc|app|aplicativo|capitao|ia|mim|tudo|bordo) )[a-z]/;
  function fichaResumida(q, a) { var s = pad(q); return !!a && a.key === 'saudacao' && SOBRE.test(s) && !ASSUNTO.test(s.replace(SOBRE, ' ')); }
  function ficha(p, q, a) { try { return congela(function () { return ficha1(p, q, a); }, a && a._inst); } finally { EXEC_SEM_SIM = false; } }
  // O teto da ficha (letras). Decisão (i) do CLAUDE.md: se a ficha passa de ~11.500, o teto vai a 16.000. Medida nos 150 instantes do laço e em 4 instantes de cada uma das 576 voltas do dia:
  // 11.382 a 11.523 letras sem a previsão e a maré (a página sem o capitao-clima.js), 11.658 a 11.802 COM elas (o app real sempre as tem: o capitao-clima.js grava a leitura do dia e a série da maré) e
  // até 12.213 com 3 linhas longas de diário do aparelho; a resumida, 3.919 a 3.992. Então o teto é 16.000. O cliente (capitao-ia.js: `.slice(0, 12000)`) e os dois Workers cortam a ficha em 12.000
  // PELO FIM (Clima e maré e Guias de bordo caem primeiro) e sobem juntos para 16.000 na Fase 6: este valor é o que eles têm de acompanhar. O testes/cerebro.py (grupo ficha) cobra a regra: acima
  // de 11.500 este valor TEM de ser 16.000. Exposto em B.FICHA_MAX. O «## Emergência» fica perto do topo porque o corte do cliente é pelo fim.
  var FICHA_MAX = 16000;
  // «## Navegação agora» (PROMPT Fase 3 «ficha()»): a hora e a fase, SOG/STW, rumo/COG e proa, a posição relativa (§2.8: só com a simulação e só dos pontos com fonte, nunca coordenada),
  // profundidade, vento e mar a bordo (o vento verdadeiro, o aparente, as ondas e a água do mar do quadro vão sempre «a bordo agora», decisão 12: a IA não os dá como o tempo do dia), motores (rpm, óleo, arrefecimento, carga), consumo, diesel e autonomia, gerador, Seakeeper, baterias, porão e âncora, os alarmes e a tendência dos
  // últimos ~30 s. Cada medida é o texto ÚNICO do instante (inst.txt: o mesmo da Main, da A1, do HUD e da answer('telemetria')). Só existe com o quadro vivo (replay ou coletor): sem ele
  // (modo real sem coletor, a reserva do snapshot) o bloco «Telemetria» já diz a data da última leitura. No modo real o coletor não traz posição relativa, e o bloco vai sem ela.
  function navegacaoAgora() {
    var i = vivo(), t = i && i.txt, q = i && i.q, l = [], f = i && i.fase && i.fase.nome, un = function (rot, v) { return v ? rot + ' ' + v : ''; };
    var junta = function (xs) { var r = xs.filter(Boolean).join(' · '); if (r) l.push(r); };
    if (!i) return null;
    junta([cap1(q.estado || 'Navegando') + ' às ' + i.hora, f ? 'fase ' + f : '']);
    junta([un('SOG', t.sog), un('STW', t.stw), un('rumo (COG)', t.rumo), un('proa', t.proa), un('piloto', t.piloto), un('leme', t.leme), t.relativa, un('destino', t.destino), un('próximo ponto', t.wp), t.eta ? 'chegada prevista às ' + t.eta : '', un('percorrido', t.distancia)]);
    junta([un('profundidade', t.prof), t.vento ? 'vento a bordo agora ' + t.vento : '', un('vento aparente a bordo agora', t.ventoAp), un('ondas a bordo agora', t.ondas), un('água do mar a bordo agora', t.agua), un('ar', t.ar), un('pressão', t.pressao)]);
    junta([un('motores', t.rpm), un('óleo', t.oleo), un('arrefecimento', t.arref), un('carga', t.carga), un('praça de máquinas', t.praca)]);
    junta([un('consumo', t.consumo), un('diesel', t.diesel), un('tanques', t.dieselLados), un('autonomia', t.autonomia)]);
    junta([t.gerador ? 'gerador ' + t.gerador : '', t.seakeeper ? 'Seakeeper ' + t.seakeeper : '', un('banco 24 V', t.b24), un('banco 12 V', t.b12), un('porão', t.porao), un('âncora', t.ancora)]);
    junta([t.alarmes ? 'alarmes: ' + t.alarmes : '', t.tend ? 'tendência — ' + t.tend : '']);
    return l.length ? { text: l.join('\n'), src: 'Fonte: ' + i.fonteTxt } : null;
  }
  // A UMA linha de navegação da ficha resumida (< 4.000 letras): o estado e a hora, SOG, rumo, a posição relativa, os motores e os alarmes, com o texto do instante
  function linhaNavegacao() {
    var i = vivo(), t = i && i.txt, q = i && i.q, r;
    if (!i) return null;
    r = [cap1(q.estado || 'Navegando') + ' às ' + i.hora, t.sog ? 'SOG ' + t.sog : '', t.rumo ? 'rumo (COG) ' + t.rumo : '', t.relativa || '', t.rpm ? 'motores ' + t.rpm : '', t.alarmes ? 'alarmes: ' + t.alarmes : ''].filter(Boolean).join(' · ');
    return { text: r, src: 'Fonte: ' + i.fonteTxt };
  }
  function fichaAlarmes(semSim) {
    var v = almVigentes({ semSim: semSim }), at = almAtivos(), i = vivo();
    if (!v.length) return null;
    return { text: v.map(function (a) { var s = at.filter(function (x) { return x.id === a.id; })[0]; return '• #' + a.n + ' ' + almRegra(a) + (s ? ' — ATIVO desde ' + s.hora + (s.valorTxt ? ' (agora ' + s.valorTxt + ')' : '') : ''); }).join('\n') + (i ? '\n(às ' + i.hora + ')' : ''), src: 'Fonte: alarmes pedidos neste aparelho' };
  }
  function ficha1(p, q, a) {
    p = p || 'app';
    var out = [], emergencia = emerg(a), resumida = fichaResumida(q, a), semSim = !EM_SOS && D.simulacao === false;
    EXEC_SEM_SIM = semSim;   // a execução com `sim: true` também fica fora (as respostas deste bloco leem a agenda); a ficha() desliga no fim
    // (no SOS nada lê a flag, CONTRATO §1.3) resposta de emergência: a ficha sai sem os blocos do quadro (Telemetria, Navegação agora, Horímetros, Autonomia e consumo)
    var bloco = function (titulo, f) { if (emergencia && QUADRO[titulo]) return; try { var a = f(); if (a && a.text) out.push('## ' + titulo + '\n' + semCoord(a.text) + (a.src ? '\n(' + semCoord(a.src) + ')' : '')); } catch (e) {} };
    out.push('## Agora\n' + agoraBR() + ' · usuário: ' + quem());
    // logo depois do «## Agora»: a navegação de agora (a ficha resumida leva só UMA linha dela, o resumo do instante) e, perto do topo, a emergência (o corte do cliente é pelo fim)
    if (resumida) bloco('Navegação agora', linhaNavegacao);
    else {
      bloco('Navegação agora', navegacaoAgora);
      out.push('## Emergência\nAbrir o SOS do app. ' + SOS_FICHA + '\n(' + FT.proto + ')');
    }
    out.push('## Sobre o app\n' + sobreApp().join('\n'));
    out.push('## Embarcação\n' + (E.nome || SD) + ' · fabricante e modelo ' + (E.modelo || SD) + ' · registro ' + (E.registro || SD) + ' · proprietário ' + (E.proprietario || SD) + ' · base ' + (E.base || SD) + ' · ' + mmsiNum() + ' (cadastro do app) · indicativo: ' + INDICATIVO + '\n(Fonte: ' + (E.fonte || SD) + ')');
    out.push('## Equipamentos\n' + (D.equipamentos || []).map(function (e) { if (e.seguranca) return '• ' + e.nome + ': ' + (e.nota || NOTA_ETIQUETA); return '• ' + e.nome + ': ' + (e.fabricante || 'fabricante ' + SD) + ' · modelo ' + (e.modelo || SD) + (e.qtd && e.qtd !== SD ? ' · ' + e.qtd + (e.lados ? ' (' + e.lados + ')' : '') : ''); }).join('\n') + '\n(Fonte: Inventário de bordo' + demo() + (D.equipNota ? ' · ' + D.equipNota : '') + ')');
    if (resumida) {
      out.push('## Ficha resumida\nVeio só o resumo acima e, se houver, os trechos do guia: telemetria, manutenção, documentos, diário e equipe não vieram. Para um desses dados, diga que o app mostra ao perguntar pelo assunto (ex.: "telemetria", "próximas manutenções").');
      return semCoord(out.join('\n\n'));
    }
    bloco('Telemetria', function () { return ANSWERS.telemetria(p); });
    bloco('Manutenção', function () { return ANSWERS.manutencao(p); });
    bloco('Peças', function () { return fichaPecas(semSim); });
    bloco('Horímetros', function () { return ANSWERS.horimetros(p); });
    bloco('Autonomia e consumo', function () {
      var a = ANSWERS.autonomia(p), ab = D.abastecimentos || [];
      return { text: a.text + (ab.length ? '\nAbastecimentos registrados: ' + ab.map(function (x) { return x.d + ' · ' + mil(x.litros) + ' L de ' + (x.combustivel || 'diesel') + ' · ' + (x.local || SD) + (x.st ? ' · ' + x.st : ''); }).join(' | ') + '.\nRegra: ' + (D.regraAbast || SD) + '.' : ''), src: a.src };
    });
    bloco('Documentos', function () { return ANSWERS.docsvenc(p); });
    bloco('Pendências', function () { return ANSWERS.anomalias(p, { semSim: semSim }); });
    bloco('Alarmes pedidos', function () { return fichaAlarmes(semSim); });   // F12: as regras que o usuário pediu e as ativas agora (só existe com alarme pedido)   // simulacao false: as linhas do aparelho com `sim: true` (gravadas com a simulação ligada) ficam fora da ficha
    bloco('Diário de bordo', function () { return ANSWERS.diarioLer(p, { semSim: semSim }); });
    bloco('Equipe e contatos', function () { return ANSWERS.contatos(p, { semBordo: true }); });   // (a situação de bordo da resposta não vai na ficha: o bloco Telemetria já a traz, e a ficha de emergência não leva o quadro)
    bloco('Clima e maré', function () {
      var pv = previsao(), m = mareTexto(), s = sim();
      var l1 = pv ? 'Previsão de hoje em Balneário Camboriú (' + pv.fonte + '): ' + pv.temp + ' · ' + pv.vento + '. O app não tem limite de vento para dizer se é seguro sair.' : s ? semConexao() : 'Previsão do dia: ' + SD + ' (sem leitura de hoje neste aparelho).';
      var l2 = m ? 'Maré agora ' + m.agora + ' em relação ao nível médio do mar · próximas horas: ' + m.prox.join(' · ') + ' — modelo, não a tábua oficial da Marinha (DHN).' : s ? (pv ? 'Maré: sem conexão agora — confira a tábua da Marinha (DHN) antes de sair.' : '') : 'Maré: ' + SD + ' agora (Open-Meteo Marine sem resposta).';
      var l3 = s ? 'Ondas: o app não tem previsão de mar — meteorologia marinha da Marinha do Brasil.' : (pv ? 'Previsão do mar (ondas): ' : 'Previsão de vento e mar para navegar: ') + SD + ' no app — meteorologia marinha da Marinha do Brasil.';
      return { text: l1 + (l2 ? '\n' + l2 : '') + '\n' + l3, src: 'Fonte: ' + (pv ? 'previsão ' + pv.fonte : 'previsão Open-Meteo: sem leitura de hoje neste aparelho') + ' · maré Open-Meteo Marine · na posição de referência · vento, pressão e temperaturas de bordo no bloco Telemetria' };
    });
    bloco('Guias de bordo', function () { return ANSWERS.manual(p); });
    return semCoord(out.join('\n\n'));
  }

  // Anexos (foto/vídeo): não saem do aparelho — viram linha A CONFIRMAR no diário.
  function answerAttachment(kind, file, ctx) { return congela(function () { return marca(anexo1(kind, file, ctx)); }); }
  // O texto que vai JUNTO com a foto ou o vídeo (F36; ctx.texto): a linha do diário é UMA só, «<texto> · foto anexada pelo chat: … A CONFIRMAR». O arquivo não é lido (só nome e tamanho) e não sai do aparelho.
  // Entram na linha: a legenda (a frase que descreve a foto, sem pergunta), o pedido de registro («registre no diário: …»), o relato, a legenda depois do «o que devo registrar?» e o relato que esperava o
  // «registrar» («sim, registra» leva o relato junto e fecha a proposta; «não» só a descarta). A pergunta, o pedido ao app, o reconhecimento, o cancelar, a emergência e o óleo NÃO entram: a foto
  // vai sozinha e a conversa os responde. O perigo que a emergência não pega (deriva, água entrando, pessoa ferida: não é relato) entra só como legenda, com `pedido` FALSO: a tela responde ao texto. `pedido` verdadeiro = o texto já foi tratado (comando de registro, relato, legenda da espera, confirmação da proposta): a tela não o responde de novo (gravaria
  // outra linha). → { nota, pedido, doRelato?, descarta? } | null
  function textoDoAnexo(tx) {
    var raw = String(tx == null ? '' : tx).trim(), n, rp, r, sb, t, nota;
    if (!raw || EM_SOS) return null;
    raw = raw.slice(0, 600); n = pad(raw); rp = relatoPendente();
    if (adiaRegistro(raw, n)) return null;   // «registra depois»: a foto vai sozinha e a proposta fica (a tela responde ao texto)
    if (rp) {
      r = respostaRelato(n, rp); sb = sobraRelato(raw, n); t = achaTicket(ticketsCru(), rp.id);
      if (r === 'nao') return { nota: '', pedido: true, descarta: rp.id };
      if (t && (r === 'sim' || (sb && !sb.duvida))) return { nota: comExtra(t.texto, sb), pedido: true, doRelato: rp.id };
    }
    if (querRegistrar(raw, n)) { nota = notaDoUsuario(raw); return nota && !resumoMais(nota) && !emergencia(pad(nota)) && oleo(pad(nota)) !== 1 ? { nota: nota, pedido: true } : null; }
    if (emergencia(n) || oleo(n) === 1 || socorroImplicito(n) || cabecaEmerg(n) || /\?/.test(raw) || RELATO_PEDIDO.test(n) || RELATO_NAO.test(n) || ACK.test(n) || CANCELA_REG.test(n) || SOBRE.test(n)) return null;
    if (ESPERA_REG && Date.now() - ESPERA_REG.t <= ESPERA_VALE) { ESPERA_REG = null; return { nota: notaRelato(raw), pedido: true }; }
    if (relatoDiario(raw, n)) return { nota: notaRelato(raw), pedido: true };
    return { nota: notaRelato(raw), pedido: false };   // a legenda
  }
  function anexo1(kind, file, ctx) {
    var p = (ctx && ctx.platform) || 'web';
    var name = file && file.name ? file.name : (kind === 'video' ? 'vídeo' : 'foto');
    var kb = file && file.size ? Math.round(file.size / 1024) + ' KB' : '';
    var n = now(), grava = !ctx || ctx.commit !== false, nao = 'não anexei ao diário (pedido vindo de link).', tx = grava ? textoDoAnexo(ctx && ctx.texto) : null, nota = tx && tx.nota ? tx.nota : '', sys = 'Equipamentos', arq, reg = null, r;
    if (nota) { sys = categoriaRelato(pad(nota), false); if (sys === 'Diário') sys = 'Equipamentos'; }
    arq = (kind === 'video' ? 'Vídeo' : 'Foto') + ' anexada pelo chat: ' + name + (kb ? ' (' + kb + ')' : '') + ' — identificação A CONFIRMAR.';
    if (grava) {
      reg = addDiario({ sys: sys, tone: tomDe(sys), t: nota ? nota.replace(/[\s.]+$/, '') + ' · ' + arq.charAt(0).toLowerCase() + arq.slice(1) : arq, who: quem(), src: 'app · ' + kind, pend: true });   // (a foto fica A CONFIRMAR: abre pendência, F20)
      if (reg && tx && tx.doRelato) fechaTicketCom(tx.doRelato, reg);
      if (tx && tx.descarta) { recusaTicket(tx.descarta); REL = null; }
    }
    if (kind === 'video') r = { key: 'video', text: 'Vídeo recebido (' + name + (kb ? ' · ' + kb : '') + ') · ' + n.d + ' ' + n.t + '.\nO som e o comportamento não são analisados automaticamente: ' + (grava ? 'anexei ao diário como anomalia A CONFIRMAR.' : nao) + '\n' + linhaBordo() + '\nDescreva em uma frase o que você viu ou ouviu — respondo com o que verificar primeiro.', src: 'Fonte: anexo · diário de bordo', actions: act(p, [['Abrir diário', 'diario']]) };
    else r = { key: 'foto', text: 'Foto recebida (' + name + (kb ? ' · ' + kb : '') + ') · ' + n.d + ' ' + n.t + '.\nA leitura da imagem não é automática: ' + (grava ? 'anexei ao diário como A CONFIRMAR.' : nao) + ' Para etiqueta ou tela de alarme, digite o modelo/código que aparece e eu localizo o guia; para nota fiscal, registre em Abastecimento (fica A CONFIRMAR).\n' + linhaBordo(), src: 'Fonte: anexo · diário de bordo', actions: act(p, [['Abrir diário', 'diario'], ['Documentos', 'docs']]) };
    if (nota && reg) r.text = r.text.replace('\n', '\nSeu texto entrou na mesma linha do diário: “' + nota + '”\n');
    r.nota = nota; r.pedido = !!(tx && tx.pedido);   // `pedido`: o texto já foi tratado (a tela não o responde de novo); sem a linha (pedido de link) não há texto tratado
    return r;
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
  // ——— TERMOS (PROMPT §3) ———
  // A lista única de termos: as 8 regex do termos.json (cópia em testes/proibidos.json), com as MESMAS fontes dos Workers e do cliente da IA (Fase 6). Nenhuma usa lookbehind
  // (iOS < 16.4) nem \w para palavra em português. Exportadas em B.TERMOS (RegExp) e B.TERMOS_FONTES ({ src, flags }: o `.source` do RegExp escapa a «/» e não serve para
  // comparar as fontes). Aqui valem na trava de voz (só ROTULOS e AUTENTICIDADE, só com D.simulacao true) e são o que as varreduras do teste usam.
  var TERMOS_FONTES = {
    ROTULOS: { src: '\\bSEM (?:DADOS|LEITURA)\\b|\\bMANUAL NO DRIVE\\b|\\bDEMO\\b', flags: '' },
    AUTENTICIDADE: { src: '(?:^|[^A-Za-zÀ-ÿ])(?:dad|leitur|valor|n[uú]mer|telemetri|informa[çc])[A-Za-zÀ-ÿ]*\\s+(?:\\S+\\s+){0,3}?(?:fict[ií]ci|simulad|inventad|de demonstra[çc][ãa]o)|dados de teste|fict[ií]ci|inventad[oa]s?(?![A-Za-zÀ-ÿ])|(?:^|[^A-Za-zÀ-ÿ])(?:barc|embarca[çc]|navega[çc]|viage|rota|cen[áa]ri|agenda|guia|registro|mmsi)[A-Za-zÀ-ÿ]*\\s+(?:\\S+\\s+){0,3}?(?:simulad|de demonstra[çc][ãa]o|hipot[ée]tic|ilustrativ|de exemplo)|(?:^|[^A-Za-zÀ-ÿ])(?:é|são|foi|está|estão) (?:uma? )?(?:simula[çc][ãa]o|demonstra[çc][ãa]o)(?! d[oa]s? )|n[ãa]o (?:é|são) (?:reais?|verdadeir[A-Za-zÀ-ÿ]*|de verdade)(?![A-Za-zÀ-ÿ])|\\(demonstra[çc][ãa]o\\)|(?:^|[^A-Za-zÀ-ÿ])(?:na|da|para) demonstra[çc][ãa]o(?! d[oa]s? )|(?:^|[^A-Za-zÀ-ÿ])modo (?:de )?(?:demonstra[çc][ãa]o|simula[çc][ãa]o|demo)(?![A-Za-zÀ-ÿ])', flags: 'i' },
    DINHEIRO: { src: 'R\\$\\s?\\d|US\\$\\s?\\d|€\\s?\\d|\\d+(?:[.,]\\d+)?\\s?(?:mil\\s+|milh(?:ão|ões)\\s+)?(?:reais|d[óo]lar(?:es)?|euros?)(?![A-Za-zÀ-ÿ])|(?:d[óo]lar|euro|cota[çc][ãa]o|pre[çc]o|custa|custo)[^\\n\\d]{0,25}\\d|c[âa]mbio[^\\S\\n]+(?:do|da|de|est[áa]|hoje|comercial|turismo|oficial)(?![A-Za-zÀ-ÿ])[^\\n\\d]{0,25}\\d|c[âa]mbio(?:[^\\S\\n]*:[^\\S\\n]*\\d|(?:[^\\n]{0,24}?[^\\d\\n])?\\d{1,2}[.,]\\d)|\\d+[.,]\\d{2}\\s*(?:o|por|cada)\\s+litro', flags: 'i' },
    PESSOAIS: { src: '\\(?\\b\\d{2}\\)?\\s?9?\\d{4}[-\\s]\\d{4}\\b|\\+55\\s?\\d|[\\w.+-]+@[\\w-]+\\.[a-z]{2,}|\\b\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}\\b|\\b\\d{2}\\.\\d{3}\\.\\d{3}/\\d{4}-\\d{2}\\b', flags: 'i' },
    LOCAL_SEGURANCA: { src: '(?:colete|balsa|boia|extintor|sinalizador|foguete|facho|epirb|radiobaliza|sea[- \\u00a0\\u2010-\\u2014]?fire|kit)[^.\\n]{0,60}(?:popa|proa|paiol|arm[áa]rio|cabine|cockpit|pra[çc]a de m[áa]quinas|gaveta|compartimento|beliche|convés|flybridge|debaixo|embaixo|sob (?:o|a|os|as) )', flags: 'i' },
    VAZIOS: { src: '\\bn/?d\\b|n[ãa]o (?:informad|dispon[ií]vel|cadastrad)|A CADASTRAR|(?:^|[^A-Za-zÀ-ÿ])a definir(?![A-Za-zÀ-ÿ])|indispon[ií]vel|[:·]\\s*—\\s*(?=[·.,\\n]|$)', flags: '' },
    VISIVEL: { src: 'snapshot|ao vivo desligad|leitura fixa|modelo de alerta|nada o dispara', flags: 'i' },
    ANEXO: { src: '(?:^|[^A-Za-zÀ-ÿ])A (?:CONFERIR|CONFIRMAR)(?![A-Za-zÀ-ÿ])', flags: '' }
  };
  var TERMOS = {};
  Object.keys(TERMOS_FONTES).forEach(function (k) { TERMOS[k] = new RegExp(TERMOS_FONTES[k].src, TERMOS_FONTES[k].flags); });

  // ---- Voz (conversa ativa) ----
  // falavel(): texto de tela → português falado. Regras em ordem, guiadas pelas tabelas; sem lookbehind (Safari antigo).
  var MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
  var HEMI = { N: 'norte', S: 'sul', L: 'leste', E: 'leste', O: 'oeste', W: 'oeste' };
  var LET = 'A-Za-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u00FF', MAI = 'A-Z\\u00C0-\\u00D6\\u00D8-\\u00DE'; // letras latinas (em escape: não quebra se o .js vier sem UTF-8)
  // palavra inteira: o grupo 1 guarda o caractere anterior (reposto como $1)
  function rx(core) { return new RegExp('(^|[^' + LET + '\\d])(?:' + core + ')(?![' + LET + '\\d])', 'g'); }
  // ——— F31 (PARIDADE, Avanti 1.20.0 e 1.20.2): nomes de equipamento que o reconhecimento de voz erra ———
  // «ligar o siker» → «ligar o Seakeeper»; «garmim» → «Garmin»; «ploter» → «plotter». Cada linha é um id de D.equipamentos e tem dois donos:
  //  · o NOME CERTO é do cadastro (o fabricante, a 1ª palavra dele, na caixa dele; EPIRB, Seafire e plotter são o nome do sistema, nunca o fabricante) — a embarcação que não tem o
  //    equipamento não tem a linha;
  //  · as VARIANTES (o que o reconhecedor escreve no lugar do nome: sem acento ou com, palavra inteira, sem distinguir caixa; o nome certo também entra) são DESTA embarcação: soam como as
  //    marcas dela (Cummins, Onan, Seakeeper…) e ficam aqui, não no gerador. O `palavras` do D.equipamentos (CONTRATO §1.4) traz o nome, palavras comuns («motor», «bateria») e só alguns
  //    erros do ditado, sem marcar quais são erros: tirar a tabela dali trocaria «ligar o motor» por «ligar o Cummins». Por isso a linha de marca leva `marca` (o nome certo, em minúsculas e
  //    sem acento) e só vale enquanto o cadastro tem essa marca: com outro fabricante ela fica inerte (nunca «cummins» virando o fabricante novo), e o grupo voz do cerebro.py acusa a tabela velha.
  // PRÓXIMA EMBARCAÇÃO: troque as linhas pelas das marcas dela (docs_pendentes da Fase 3: o gerador passar a marcar as grafias erradas, e esta tabela sair do cérebro).
  // Vale no ditado, no início do answer() e (a tela) no texto que vai à IA: B.corrigeVoz.
  var VOZ_EQUIP = [
    { id: 'motores', marca: 'cummins', v: 'kamins|camins|comins|cumins|cumis|cummins' },
    { id: 'gerador', marca: 'onan', v: 'honan|onã|onam|onan' },
    { id: 'estabilizador', marca: 'seakeeper', v: 'siker|seker|sikeeper|seekeeper|sea\\s?keeper|si\\s?keeper|siquer|sikiper|seakeeper' },
    { id: 'estabilizador', marca: 'seakeeper', mantem: '(?:estabilizador|giroestabilizador)\\s+', v: 'skip|ski|squip' },
    { id: 'climatizacao', marca: 'webasto', v: 'vebasto|webasta|vebasta|webasto' },
    { id: 'eletronicos', marca: 'garmin', v: 'garmim|gármin|garmi|garmin' },
    { id: 'eletronicos', v: 'polter|poltergein|ploter|plóter|plotter', nome: 'plotter' },
    { id: 'audio', marca: 'fusion', v: 'fiuchon|fiúchon|fiuchion|fusion' },
    { id: 'vhf', marca: 'icom', v: 'aicom|aikom|icom' },
    { id: 'epirb', v: 'ipirb|ipirbi|epirbe|epirbi|e pirb|epirb', nome: 'EPIRB' },
    { id: 'seafire', v: 'sea\\s?fire|si\\s?fire|sifaire|sifai|cifire|seafire', nome: 'Seafire' },
    { id: 'dessalinizador', marca: 'schenker', v: 'shenker|schenquer|chenker|xenquer|schenker' },
    { id: 'ancora', marca: 'lewmar', v: 'leumar|lumar|luomar|leumer|lewmar' },
    { id: 'piloto', marca: 'raymarine', v: 'reimarine|reymarine|rei marine|ray marine|raymarine' },
    { id: 'ais', marca: 'em-trak', v: 'emtrak|em track|em trak|m trak|em-trak' },
    { id: 'eletrico', marca: 'victron', v: 'vitron|victor on|victron' }
  ].map(function (x) {
    x.re = new RegExp('(^|[^' + LET + '\\d])' + (x.mantem ? '(' + x.mantem + ')' : '') + '(?:' + x.v + ')(?![' + LET + '\\d])', 'gi');
    return x;
  });
  function corrigeVoz(t) {
    var s = String(t == null ? '' : t), eq;
    if (!s || EM_SOS) return s;   // (o SOS não lê o D.equipamentos, CONTRATO §1.3)
    eq = D.equipamentos || [];
    VOZ_EQUIP.forEach(function (x) {
      var e = eq.filter(function (y) { return y && y.id === x.id; })[0], nome = x.nome || (e && e.fabricante ? String(e.fabricante).split(' ')[0] : '');
      if (e && nome && (!x.marca || norm(nome) === x.marca)) s = s.replace(x.re, '$1' + (x.mantem ? '$2' : '') + nome);
    });
    return s;
  }
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
  // F32 (PARIDADE, Avanti 1.13.0): a sigla é dita como se fala a bordo, nunca soletrada (EPIRB = épirbi, MOB = móbi, NMEA = nêmea, kt = nós, hPa = hectopascal, rpm = rotações por
  // minuto) e as siglas da instrumentação do quadro (SOG, COG, STW, TWS, TWA, TWD, AWA, AWS, HDG, DPT, ETA) saem por extenso. Bombordo e boreste (BB, BE) já existiam.
  var SIGLAS = [
    ['NF-e', 'nota fiscal eletrônica'], ['NF', 'nota fiscal'], ['BB', 'bombordo'], ['BE', 'boreste'], ['SOG', 'velocidade sobre o fundo'],
    ['COG', 'rumo sobre o fundo'], ['STW', 'velocidade na água'], ['TWS', 'velocidade do vento verdadeiro'], ['TWA', 'ângulo do vento verdadeiro'], ['TWD', 'direção do vento verdadeiro'],
    ['AWA', 'ângulo do vento aparente'], ['AWS', 'velocidade do vento aparente'], ['HDG', 'proa'], ['DPT', 'profundidade'], ['ETA', 'chegada prevista'],
    ['STBY', 'standby'], ['MOB', 'móbi'], ['EPIRB', 'épirbi'], ['NMEA', 'nêmea'], ['AC', 'corrente alternada'], ['DC', 'corrente contínua'],
    ['KTS?|kts?|kn', 'nós'], ['km/h', 'quilômetros por hora'], ['hPa', 'hectopascal'], ['kPa', 'quilopascal'], ['rpm', 'rotações por minuto'],
    ['RPM', 'rotação'], ['PAN-PAN', 'pan pan'], ['[Nn][º°]', 'número'], ['IA', 'i a'], ['TIE', 'título de inscrição'], ['máx\\.?', 'máximo'], ['mín\\.?', 'mínimo'],
    ['Sr\\.', 'senhor'], ['Sra\\.', 'senhora'], ['ref\\.', 'referência'], ['cert\\.', 'certificado']
  ].map(function (x) { return [rx(x[0]), '$1' + x[1]]; });
  // símbolos → fala ou pausa
  var SIMB = [
    [/Rev\. ?(?=\d)/g, 'revisão '], [/§ ?/g, 'seção '], [/(\d)-(?=\d)/g, '$1 '], [/−(?=\d)/g, 'menos '],
    [/\s*±\s*/g, ' mais ou menos '], [/\s*[≈~]\s*/g, ' cerca de '], [/\s*≤\s*/g, ' até '], [/\s*≥\s*/g, ' pelo menos '],
    [new RegExp('(\\d)\\s*×\\s*(?=[' + LET + '])', 'g'), '$1 '], [/×\s*(\d+)/g, '$1 vezes'], [/\s*×\s*/g, ' vezes '],
    [/\s+\+\s+/g, ' mais '], [/(^|\s)\+(?=\d)/g, '$1mais '], [/\s*%/g, ' por cento'],
    [new RegExp('([' + LET + '])→(?=[' + LET + '])', 'g'), '$1 para '], [/\s*[•·→›|—–=()\[\]]\s*/g, ', '],
    [/\.(pdf|csv|jsonl?|jpe?g|png|mp4|mov|txt)(?![A-Za-z])/gi, function (m, e) { return ' ' + e.toUpperCase(); }], [/(?:\s*_)+\s*/g, ' '],
    [new RegExp('([' + LET + '])\\s*/\\s*(?=\\d)', 'g'), '$1 ou '], [/\s*\/\s*/g, ', ']
  ];
  // MAIÚSCULAS de 4+ letras viram minúsculas (senão o TTS soletra), com as palavrinhas do mesmo trecho; siglas lidas como tal ficam.
  var SIGLA_OK = ' VHF AIS GPS MMSI DHN SOS DSC ';
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
    // a hora que fecha a frase depois do travessão («… chegando — 12:01:00.») vira «, às 12:01:00»
    s = s.replace(/ [—–] (\d{1,2}:\d{2}(?::\d{2})?)(?![\d:])/g, ', às $1');
    // horário com segundos 12:01:05 → "12 horas, 1 minuto e 5 segundos" (segundos ":00" → "12 horas e 1 minuto"); vem antes do HH:MM, que não pega o que tem ":" depois
    s = s.replace(/(^|[^\d:,.])(\d{1,2}):(\d{2}):(\d{2})(?!\d|:\d|\.\d)/g, function (m, a, h, mi, se) {
      var p;
      h = +h; mi = +mi; se = +se;
      if (h > 23 || mi > 59 || se > 59) return m;
      p = [hora(h)];
      if (mi) p.push(mi + (mi === 1 ? ' minuto' : ' minutos'));
      if (se) p.push(se + (se === 1 ? ' segundo' : ' segundos'));
      return a + (p.length === 1 ? p[0] : p.length === 2 ? p[0] + ' e ' + p[1] : p[0] + ', ' + p[1] + ' e ' + p[2]);
    });
    // horário 13:23 / 23h01 (nunca razão: 3:00:15:20 fica) e duração 1 h 10 / 6 h 58 min; o «:» de pontuação depois da hora («desde as 07:00: 65 milhas») não impede a leitura
    s = s.replace(/(^|[^\d:,.])(\d{1,2})(?::|h)(\d{2})(?:min(?![A-Za-z]))?(?!\d|:\d|\.\d)/g, function (m, a, h, mi) {
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
    function atual() { return corrigeVoz((texto + ' ' + sessao).replace(/\s+/g, ' ').trim()); }   // F31: «ligar o siker» já sai «ligar o Seakeeper»
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
  // A fala (PROMPT Fase 3 «Voz»): falaBase() é a 1ª linha da resposta (ou as primeiras ressalvas/itens de uma lista), sem fontes e sem parênteses; falaCurta() a fecha com a hora do
  // instante, quando a frase não a diz, e passa pela trava de voz. As chaves de FALA_INTEIRA saem sempre inteiras, sem trava e sem hora (segurança vem antes).
  function falaBase(a) {
    if (a && typeof a === 'object' && a.fala) return a.fala; // resposta que já traz a fala certa (saudação vinda de pergunta)
    var t = a && typeof a === 'object' ? a.text : a;
    if (a && a.key && FALA_INTEIRA[a.key]) return String(t || '');
    // Trecho de segurança da base (Seafire, EPIRB, salvatagem, protocolo…): o trecho inteiro, com o rótulo e a nota da etiqueta
    // (sem a linha "Veja também"). Antes, a fala parava na 2ª frase e perdia o "não abra o acesso ao motor" e o rótulo.
    if (a && (a.key === 'base' || a.key === 'faqEquip') && a.seguranca && typeof t === 'string') return t.split(/\n+/)[0].trim();
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
  // A hora na fala (decisão 5: resposta com número e hora). A 1ª linha de uma resposta de dado de bordo diz a hora do instante («às 12:01:00»); a que a traz só entre parênteses (que a fala tira) ou na
  // fonte ganha «Às HH:MM:SS.» no fim. Ficam de fora as respostas sem dado do quadro ou com a hora própria: as de emergência e as chaves de SEM_HORA_NA_FONTE, as do tempo e da maré (hora da leitura
  // do mundo real, §2.5), a lista da equipe, as perguntas de fora do barco e sobre os dados, o fallback, o trecho do guia e as do cadastro sem quadro (áudio, guias). A hora é a do instante da
  // PRÓPRIA resposta (`a.hora`, posta pelo answer()): a fala é montada depois, com o relógio já andado, e a tela copia a resposta antes de falar.
  var FALA_SEM_HORA = { clima: 1, contatos: 1, foraBarco: 1, fallback: 1, sobreDados: 1, base: 1, faqEquip: 1, audio: 1, manual: 1, ia: 1, foto: 1, video: 1, relato: 1, diario: 1, diarioPede: 1, relatoRegistra: 1, relatoCancela: 1 };
  ['agendar', 'ticketConfirma', 'ticketRecusa', 'ticketDesfaz', 'alarmeCancela', 'alarmeApaga', 'capacidades'].forEach(function (k) { FALA_SEM_HORA[k] = 1; });   // (P3G: as respostas de gestão não leem o quadro: a fala não leva a hora)
  function comHoraNaFala(a, t) {
    var h = a && typeof a === 'object' && typeof a.hora === 'string' ? a.hora : '';
    if (!sim() || !/^\d\d:\d\d:\d\d$/.test(h) || !a.key || SEM_HORA_NA_FONTE[a.key] || FALA_SEM_HORA[a.key] || !t || /\d\d:\d\d:\d\d/.test(t)) return t;
    // «Pendências abertas: …» → «Pendências abertas, às 12:01:00: …» (a hora na abertura, antes da lista); sem os dois-pontos perto do começo, «… Às 12:01:00.» no fim
    var k = t.indexOf(': ');
    if (k > 0 && k < 140) return t.slice(0, k) + ', às ' + h + t.slice(k);
    return String(t).replace(/[\s.;:,]+$/, '') + '. Às ' + h + '.';
  }
  // Trava de voz (só com D.simulacao true): troca o termo que casa ROTULOS ou AUTENTICIDADE (§3) por uma expressão neutra, nunca suprime nem encurta a frase. É a última guarda: as respostas locais já
  // saem limpas (os testes varrem) e a da IA passa pelo filtro do Worker; aqui pega o que escapou (a nota do diário lida de volta, uma resposta antiga). Não vale para FALA_INTEIRA.
  // A troca é da PALAVRA inteira do termo («fictícios» → «de bordo», nunca «dado de bordoos»): o casamento da AUTENTICIDADE termina no radical (fict[ií]ci, simulad, inventad…), então o regex da trava
  // (só aqui no cérebro; TERMOS_FONTES fica como no §3) o estende até o fim da palavra e aos adjetivos coordenados («fictícios e simulados»). O substantivo («dados», «leituras») e o caractere que
  // antecede o termo ficam; «de bordo» não varia com o gênero nem com o número. O que não é adjetivo (é uma simulação, na demonstração, modo demo, não são reais) mantém o verbo ou a preposição.
  var VOZ_LET = 'A-Za-zÀ-ÿ', VOZ_NEUTRO = 'de bordo';
  var VOZ_ADJ = '(?:fict[ií]ci|simulad|inventad|hipot[ée]tic|ilustrativ)[' + VOZ_LET + ']*';
  var VOZ_ADJS = VOZ_ADJ + '(?:\\s*(?:,|e|ou)\\s+' + VOZ_ADJ + ')*';
  var VOZ_FIM_TERMO = new RegExp(VOZ_ADJS + '$|de (?:demonstra[çc][ãa]o|exemplo)$', 'i');
  function vozMaiuscula(t, de) { return /^[A-ZÀ-Ý]/.test(de) ? t.charAt(0).toUpperCase() + t.slice(1) : t; }
  function neutraAutenticidade(m) {
    var ini, r, x;
    if (/^\(demonstra/i.test(m)) return VOZ_NEUTRO;
    ini = /^[^A-Za-zÀ-ÿ]/.test(m) ? m.charAt(0) : ''; r = m.slice(ini.length);
    if (/^modo (?:de )?(?:demonstra[çc][ãa]o|simula[çc][ãa]o|demo)$/i.test(r)) return ini + r.slice(0, 4) + ' ' + VOZ_NEUTRO;
    if ((x = /^(é|são|foi|está|estão) (?:uma? )?(?:simula|demonstra)[çc][ãa]o$/i.exec(r))) return ini + x[1] + ' ' + VOZ_NEUTRO;
    if ((x = /^(n[ãa]o) (é|são) /i.exec(r))) return ini + x[1] + ' ' + x[2] + ' ' + VOZ_NEUTRO;   // a negação FICA («a leitura não é verdadeira» → «não é de bordo»): sem o «não» a frase afirmava o contrário
    if ((x = /^(na|da|para) demonstra[çc][ãa]o$/i.exec(r))) return ini + vozMaiuscula(/^da$/i.test(x[1]) ? VOZ_NEUTRO : 'a bordo', x[1]);
    if ((x = /^(dados) de teste$/i.exec(r))) return ini + x[1] + ' ' + VOZ_NEUTRO;
    x = VOZ_FIM_TERMO.exec(r);
    return ini + (x ? r.slice(0, x.index) : '') + VOZ_NEUTRO;
  }
  var VOZ_TERMOS = [
    [new RegExp(TERMOS_FONTES.ROTULOS.src, 'g' + TERMOS_FONTES.ROTULOS.flags), function (m) { return /^SEM/.test(m) ? 'sem informação' : /^MANUAL/.test(m) ? 'no guia de bordo' : VOZ_NEUTRO; }],
    [new RegExp('(?:' + TERMOS_FONTES.AUTENTICIDADE.src + ')[' + VOZ_LET + ']*(?:\\s*(?:,|e|ou)\\s+' + VOZ_ADJ + ')*', 'g' + TERMOS_FONTES.AUTENTICIDADE.flags), neutraAutenticidade]];
  function travaVoz(t) {
    var s = String(t == null ? '' : t), k, n, orig = s;
    if (!sim()) return s;
    for (n = 0; n < 4; n++) {
      var antes = s;
      for (k = 0; k < VOZ_TERMOS.length; k++) s = s.replace(VOZ_TERMOS[k][0], VOZ_TERMOS[k][1]);
      if (s === antes) break;
    }
    // (só no que a trava trocou) duas trocas seguidas dão «de bordo de bordo» / «de bordo e de bordo»: uma só
    return s === orig ? s : s.replace(/\bde bordo(?:\s+(?:e\s+)?de bordo)+/gi, VOZ_NEUTRO);
  }
  function falaCurta(a) {
    var t = falaBase(a);
    if (a && typeof a === 'object' && a.key && FALA_INTEIRA[a.key] === 1) return t;
    return travaVoz(comHoraNaFala(a, t));
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

  window.CapitaoBrain = { VERSAO: VERSAO, DADOS: D, BASE: BASE, buscaBase: buscaBase, carregaBase: carregaBase, DEFAULTS: DEFAULTS, BANK: BANK, ALL: ALL, HREF: HREF, loadShortcuts: loadShortcuts, saveShortcuts: saveShortcuts, resetShortcuts: resetShortcuts, bankFor: bankFor, loadDiario: loadDiario, addDiario: addDiario, diarioFonte: diarioFonte, loadExec: loadExec, markExec: markExec, unmarkExec: unmarkExec, loadEquipe: loadEquipe, saveEquipe: saveEquipe, loadDocs: loadDocs, addDoc: addDoc, loadAbast: loadAbast, addAbast: addAbast, loadTickets: loadTickets, addTicket: addTicket, editaTicket: editaTicket, aceitaTicket: aceitaTicket, recusaTicket: recusaTicket, desfazTicket: desfazTicket, ticketsAbertos: ticketsAbertos, ticketTela: ticketTela, propoeAlarme: propoeAlarme, perguntaDoBotao: perguntaDoBotao,
    // P3G (F15, F20, F12): a agenda (tarefas da equipe e propostas do diário), as pendências (resolver, reabrir, desfazer — linhas novas) e os alarmes pedidos (as regras, os ativos agora para a faixa)
    loadTarefas: loadTarefas, addTarefa: addTarefa, tarefasEquipe: tarefasEquipe, achaAgendar: achaAgendar, ticketDoRegistro: ticketDoRegistro, textoTicket: textoTicket, conclusao: conclusao,
    pendenciasLista: pendenciasLista, resolvePendencia: resolvePendencia, reabrePendencia: reabrePendencia, desfazPendencia: desfazPendencia, achaPendencia: achaPendencia,
    alarmesPedidos: almVigentes, alarmesPedidosAtivos: almAtivos, criaAlarmePedido: almCria, apagaAlarmePedido: almApaga, alarmeTexto: almRegra, historicoIA: historicoIA, answer: answer, answerAttachment: answerAttachment, pedeIA: pedeIA, ficha: ficha, instante: instante, resumoAgora: resumoAgora, preditiva: preditivaLista, carregaFaq: carregaFaq, faqPronto: function () { return !!FAQ.itens; }, faqDados: function () { return FAQ.dados; }, faqItem: faqItem, faqBusca: faqBusca, checklistTipos: checkTipos, checklistItens: checklistItens, checklistLinha: checklistLinha, checklistMarca: checklistMarca, checklistMarcas: checkMarcas, checklistZera: checklistZera, checklistConcluir: checklistConcluir, loadPecas: pecasEstado, pecas: pecasLista, usaPeca: usaPeca, desfazUsoPeca: desfazUsoPeca, ajustaPeca: ajustaPeca, addPeca: addPeca, semCoord: semCoord, TERMOS: TERMOS, TERMOS_FONTES: TERMOS_FONTES, FICHA_MAX: FICHA_MAX, CHAVES: CHAVES, SOBRE_DADOS: SOBRE_DADOS, vozPensando: vozPensando, quem: quem, route: route, parseHash: parseHash, clearHash: clearHash, recognizer: recognizer, ditado: ditado, linkConvite: linkConvite, speak: speak, stopSpeaking: stopSpeaking, abertura: abertura, falaCurta: falaCurta, travaVoz: travaVoz, corrigeVoz: corrigeVoz, conversa: conversa, limpaConversa: limpaConversa, FALA_INTEIRA: FALA_INTEIRA, vozEnviar: vozEnviar, pularFala: pularFala, vozEncerrar: vozEncerrar, falavel: falavel, voz: vozPtBr, now: now, askHref: askHref, nb: nb, mil: mil, horas: horas, grau3: grau3, SNAP: SNAP, SOS_PASSOS: SOS_PASSOS, OLEO_PASSOS: OLEO_PASSOS, MMSI: MMSI_RADIO, MMSI_RADIO: MMSI_RADIO, ROTULO: ROTULO,
    LISTAS: { SOS: SOS.slice(), SOS_REGEX: SOS_REGEX_FONTES.slice(), SALVATAGEM: SALVATAGEM.slice(), BOIA_FORA: BOIA_FORA.slice(), EPIRB: EPIRB_PALAVRAS.slice(), EPIRB_REGEX: EPIRB_REGEX_FONTE }, emergencia: emergencia };
  try { window.dispatchEvent(new CustomEvent('capitao-brain-ready')); } catch (e) {}
})();
