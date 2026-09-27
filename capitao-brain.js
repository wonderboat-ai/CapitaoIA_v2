/* Capitão IA — cérebro: atalhos, diário, respostas canônicas, base de bordo e voz.
   Os dados vêm de capitao-dados.js (window.CapitaoDados) — hoje a embarcação de DEMONSTRAÇÃO, com dados fictícios
   rotulados e a fonte de cada um (Drive › Capitão IA v2). Nada inventado aqui: sem dado → SEM DADOS; sensor ausente →
   SEM LEITURA; manual não confirmado → MANUAL NO DRIVE; foto/nota → A CONFERIR / A CONFIRMAR.
   Pipeline: answer(q, ctx) → route(q) (emergência e óleo no topo) → ANSWERS[chave] { text, src, actions }
             → buscaBase(q) (BM25 com sinônimos PT/EN sobre base-conhecimento.json) → SEM DADOS.
   [estrutura] IA na nuvem (integracoes/claude-api) entraria antes do SEM DADOS — não ligada. */
(function () {
  var norm = function (s) { return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); };
  var has = function (q, list) { return list.some(function (k) { return q.indexOf(k) !== -1; }); };
  var D = window.CapitaoDados || {};
  var E = D.embarcacao || {}, S = D.snapshot || {}, AUT = D.autonomia || {}, CON = D.consumo || {};
  var DEMO = D.demo ? ' (DEMO)' : '';
  var SD = 'SEM DADOS';

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
  function addDiario(e) { var n = now(); var list = loadDiario(); var entry = Object.assign({ d: n.d, t: n.t, iso: n.iso, sys: 'Diário', tone: 'var(--cap-accent, #00a1fe)', who: quem(), src: 'app · texto' }, e); list.unshift(entry); write(K.diario, list); return entry; }
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
  function grau3(x) { return typeof x === 'number' ? ('00' + Math.round(((x % 360) + 360) % 360)).slice(-3) + '°' : '—'; }
  function horas(x) { if (typeof x !== 'number' || !isFinite(x)) return '—'; var s = x.toFixed(1).split('.'); return mil(+s[0]) + ',' + s[1]; }
  var M = S.motores || {}, G = S.gerador || {}, DI = S.diesel || {}, T = S.tanques || {};
  var SNAP = {
    quando: S.quando || SD, hora: S.hora || '', dia: S.dia || '',
    pos: S.gps && S.gps.texto ? S.gps.texto : 'posição SEM LEITURA',
    local: (S.estado || SD) + ' · ' + (S.local || SD),
    diesel: DI.bb != null ? 'BB ' + nb(DI.bb) + ' % · BE ' + nb(DI.be) + ' % (≈ ' + mil(DI.litros) + ' L de ' + mil(DI.capacidade) + ')' : SD,
    dieselHora: (DI.nota || 'última leitura') + ' · ' + (DI.hora || SD),
    motores: M.rpm ? 'motores ' + (M.estado || 'desligados') + ' — última leitura com motores ligados ' + M.hora + ' (marcha lenta, ' + (M.marcha || 'neutro') + '): ' + M.rpm.join('/') + ' rpm · óleo ' + M.oleo.map(function (x) { return nb(x); }).join('/') + ' bar · arrefecimento ' + M.arref.join('/') + ' °C' : 'motores: ' + SD,
    fonte: 'coletor NMEA' + DEMO + ' · snapshot ' + (S.quando || SD)
  };
  var FT = {
    tele: 'Fonte: ' + SNAP.fonte,
    agenda: 'Fonte: ' + (D.agendaFonte || 'agenda de manutenção'),
    docs: 'Fonte: ' + (D.docsFonte || 'controle de documentos'),
    abast: 'Fonte: ' + (D.abastFonte || 'registro de abastecimento'),
    diario: 'Fonte: ' + (D.diarioFonte || 'diário de bordo'),
    proto: 'Fonte: ' + ((D.protocolos && D.protocolos.fonte) || 'protocolo de emergência')
  };
  function guia(k) { return (D.guias && D.guias[k]) || SD; }
  function equip(id) { return (D.equipamentos || []).filter(function (e) { return e.id === id; })[0] || null; }
  // "Gerador Onan · modelo SEM DADOS" — sempre fabricante e modelo, com o que faltar marcado
  function fabMod(id) {
    var e = equip(id); if (!e) return SD;
    return e.nome + ' ' + (e.fabricante || '(fabricante ' + SD + ')') + (e.modelo ? ' ' + e.modelo : ' · modelo ' + SD);
  }
  function agenda() { return D.agenda || []; }
  function atrasadas() { return agenda().filter(function (t) { return t.dn < 0; }); }
  function tarefa(id) { return agenda().filter(function (t) { return t.id === id; })[0] || null; }
  function prazoTxt(t) { return t ? (t.dn < 0 ? 'em atraso há ' + (-t.dn) + (t.dn === -1 ? ' dia' : ' dias') : 'D-' + t.dn + ' · ' + t.vence.slice(0, 5)) : SD; }
  function min1(s) { s = String(s || ''); return s.charAt(0).toLowerCase() + s.slice(1); }
  function pendencias() { return diarioFonte().filter(function (x) { return x.pend; }); }

  // Frase normalizada com espaço nas pontas (palavra inteira = ' x ').
  function pad(s) { return ' ' + norm(s).replace(/[?!.,;:()"“”]+/g, ' ').replace(/\s+/g, ' ').trim() + ' '; }
  var SOS = ['mayday', 'emergenc', 'incendio', ' fogo', 'homem ao mar', ' mob ', ' sos ', 'socorro', 'naufrag', 'caiu no mar', 'caiu ao mar', 'caiu na agua', 'pessoa na agua', 'alguem na agua', 'crianca na agua', 'afogad', 'afogand',
    'afund', 'entrando agua', 'agua entrando', 'entrada de agua', 'alagad', 'alagand', 'inundad', 'inundand', 'abandon', 'colisao', 'colidi', 'abalroa', 'encalh', 'explos',
    'vazamento de combustivel', 'vazando combustivel', 'vazamento de diesel', 'vazando diesel', 'vazamento de gas', 'vazando gas', 'cheiro de combustivel', 'cheiro de diesel', 'cheiro de gas', 'cheiro de queimado'];
  function emergencia(q) { return has(q, SOS) || (has(q, ['fumaca']) && !has(q, ['escap'])); } // fumaça no escapamento é do motor, não SOS
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
    if (has(q, ['gerador', 'onan']) && !has(q, ['motor'])) return 0; // óleo do gerador: rota do gerador
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
  var MMSI = E.mmsi ? 'MMSI ' + E.mmsi + (E.mmsiNota ? ' (' + E.mmsiNota + ')' : '') : 'MMSI ' + SD;
  // Passos do SOS: resposta sos e, inteiros, no registro de diário que cita emergência. Chat nunca grava sozinho — só "registre no diário…".
  // Posição do MAYDAY é a do plotter na hora da chamada — o GPS do snapshot é só o último fix.
  var SOS_PASSOS = 'Ordem (' + ROTULO + '):\n1. VHF canal 16 · MAYDAY — nome ×3, ' + MMSI + ', posição lida no plotter, perigo, pessoas a bordo, auxílio\n2. Homem ao mar: grite e aponte, jogue a boia, marque MOB no plotter Garmin, volte com o motor em neutro perto da pessoa\n3. Incêndio · Seafire: ' + SD + ' — procedimento do sistema não carregado\n4. EPIRB: ' + SD + ' — modelo, localização e acionamento não carregados';
  // Passos da pressão de óleo baixa: resposta oleo e, inteiros, no registro de diário que relata queda/alarme de pressão.
  var OLEO_PASSOS = '1. Reduza para marcha lenta e observe se a pressão sobe.\n2. Compare BB e BE no mesmo giro — só um lado baixo aponta o motor.\n3. Com o motor parado: procure vazamento e confira o nível de óleo.\n4. Persistindo: desligue o motor afetado, siga com o outro e chame a oficina Volvo Penta.';
  // Base completa externa (NotebookLM) não configurada nesta embarcação: o fallback leva a pendência e FAQ.
  var BASE = null;
  var GRAVAR_AGORA = 'Para gravar posição e hora: toque em DIÁRIO DE BORDO ou diga “registre posição e hora”.';
  function resumoAgora() {
    return SNAP.local + ' · ' + SNAP.pos + ' · SOG ' + nb(S.sog) + ' nó · proa ' + grau3(S.proa) + ' · ' + SNAP.motores + ' · gerador ' + (G.estado || SD) + ' (' + horas(G.horas) + ' h) · Seakeeper ' + ((S.seakeeper && S.seakeeper.estado) || SD) + ' · banco 24 V ' + nb(S.bat24, 2) + ' V · vento ' + nb(S.vento) + ' nós de ' + grau3(S.ventoDe) + ' · diesel ' + SNAP.diesel + ' (' + SNAP.dieselHora + ') — snapshot' + DEMO + ' ' + SNAP.quando + '.';
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

  var ANSWERS = {
    saudacao: function (p) { return { text: 'Capitão IA online. Que precisa?\nOlá, ' + quem() + '. ' + (window.CapitaoAuth && window.CapitaoAuth.frase ? window.CapitaoAuth.frase() : '') + '\nRespondo sobre telemetria, manutenção, documentos, abastecimento, diário de bordo e os passos de cada equipamento — sempre citando a fonte.' + (D.demo ? '\n' + (D.selo || 'DEMO') + ': esta embarcação é de demonstração.' : ''), src: FT.tele + ' · ' + (D.selo || ''), actions: act(p, [['Console completo', 'console'], ['FAQ de bordo', 'faq']]) }; },
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
      var t = resumoAgora();
      var al = junto && emergencia(pad(nota)), pr = junto && oleo(pad(nota)) === 1;
      var passos = (al ? '\nSe a emergência é agora: abra o SOS. ' + SOS_PASSOS : '') + (pr ? '\nSe a pressão de óleo está baixa agora, verifique nesta ordem:\n' + OLEO_PASSOS : '');
      var acoes = (al ? [['Abrir SOS', 'sos']] : []).concat(pr ? [['Contatos', 'equipe']] : [], [['Abrir diário', 'diario']]);
      if (grava) addDiario({ sys: 'Navegação', tone: 'var(--cap-tele, #00f4fd)', t: (junto ? nota + ' · resumo: ' : 'Resumo registrado pelo atalho: ') + t, who: quem(), src: junto ? 'chat · voz/texto · telemetria' + DEMO : 'atalho · telemetria' + DEMO });
      return { text: (grava ? 'Registrado no diário de bordo · ' + n.d + ' ' + n.t + ' · ' + quem() + '\n' + (junto ? '“' + nota + '”\n' : '') + t + '\nLinha nova — nada se apaga.' : 'Não registrado — pedido vindo de link não grava no diário.\n' + (junto ? '“' + nota + '”\n' : '') + 'Resumo: ' + t + '\n' + como + ', ou toque no atalho DIÁRIO DE BORDO.') + passos, src: FT.tele + ' · diário de bordo do app' + (pr ? ' · ' + guia('g_motores') + ' §4' : ''), actions: act(p, acoes) };
    },
    seguro: function (p) {
      var at = atrasadas(), porao = tarefa('porao-teste');
      var ress = [];
      if (porao && porao.dn < 0) ress.push('(segurança) teste das bombas de porão e alarmes ' + prazoTxt(porao) + ' — acione cada bomba manualmente antes de largar.');
      at.filter(function (x) { return x.id !== 'porao-teste'; }).forEach(function (x) { ress.push(x.t + ' — ' + prazoTxt(x) + '.'); });
      ress.push('Sem previsão de vento e mar carregada (' + SD + ') — confira a previsão da Marinha antes de sair.');
      return { text: 'Sim, com ' + ress.length + ' ressalvas — a primeira é de segurança.\n• Condições a bordo (snapshot' + DEMO + ' ' + SNAP.quando + '): vento ' + nb(S.vento) + ' nós de ' + grau3(S.ventoDe) + ' · barômetro ' + nb(S.pressao, 0) + ' hPa · ' + ((S.gps && S.gps.satelites) || '—') + ' satélites · banco 24 V ' + nb(S.bat24, 2) + ' V.\n• Diesel ≈ ' + mil(DI.litros) + ' L (' + SNAP.diesel.split(' (')[0] + ') → ≈ ' + nb(AUT.horas) + ' h a ' + ((CON.cruzeiro && CON.cruzeiro.nos) || '—') + ' nós com reserva de 10 %.\n' + ress.map(function (r, i) { return '• Ressalva ' + (i + 1) + (r.charAt(0) === '(' ? ' ' : ': ') + r; }).join('\n') + '\n' + SNAP.motores.charAt(0).toUpperCase() + SNAP.motores.slice(1) + ' · sem alarmes.', src: FT.tele + ' · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['Ver manutenção', 'manut'], ['Checklist de saída', askHref(p, 'Checklist de saída')]]) };
    },
    destinos: function (p) { return { text: 'SEM DADOS de rotas: nenhum roteiro ou destino cadastrado nas fontes (' + ((D.drive && D.drive.raiz) || 'Drive') + ').\nAlcance com o diesel a bordo: ≈ ' + AUT.mn + ' mn (≈ ' + nb(AUT.horas) + ' h a ' + CON.cruzeiro.nos + ' nós, reserva de 10 %) — ida e volta até ≈ ' + Math.floor(AUT.mn / 2) + ' mn da posição atual.\nCadastre os destinos (nome e posição) para eu calcular distância, tempo e diesel de cada um.', src: 'Fonte: telemetria' + DEMO + ' · consumo observado ' + (CON.periodo || '') + ' · roteiros: nenhum', actions: act(p, [['Autonomia', askHref(p, 'Autonomia')], ['Registrar pendência', 'diario']]) }; },
    manutencao: function (p) {
      var at = atrasadas(), prox = agenda().filter(function (t) { return t.dn >= 0; }).slice(0, 3), oleoM = tarefa('motores-oleo');
      return { text: 'Atrasadas (' + at.length + '):\n' + at.map(function (t) { return '• ' + t.t + ' · ' + t.equip + ' — ' + prazoTxt(t) + ' (' + t.quem + ')'; }).join('\n') + '\nPróximas:\n' + prox.map(function (t) { return '• D-' + t.dn + ' · ' + t.vence.slice(0, 5) + ' — ' + t.t + ' (' + t.quem + ')'; }).join('\n') + (oleoM && oleoM.horas ? '\nÓleo e filtros dos motores: ' + oleoM.vence + ' ou ' + oleoM.horas.limite + ' h — faltam ' + nb(oleoM.horas.faltam) + ' h.' : '') + '\nFalta registrar: ' + (D.agendaFalta || []).join(' · ') + '.', src: FT.agenda + ' · ' + agenda().length + ' tarefas · horímetros ' + (M.hora || ''), actions: act(p, [['Abrir manutenção', 'manut']]) };
    },
    autonomia: function (p) { return { text: '≈ ' + nb(AUT.horas) + ' h · ≈ ' + AUT.mn + ' mn a ' + CON.cruzeiro.nos + ' nós (' + mil(CON.cruzeiro.rpm) + ' rpm · ' + CON.cruzeiro.lph + ' L/h, dois motores), com reserva de 10 %.\nA bordo ≈ ' + mil(DI.litros) + ' L de ' + mil(DI.capacidade) + ' (BB ' + nb(DI.bb) + ' % · BE ' + nb(DI.be) + ' %) — ' + SNAP.dieselHora + '.\nEm marcha lenta (' + nb(CON.lenta.lph) + ' L/h) ≈ ' + AUT.lenta + ' h. Consumido desde o abastecimento de ' + CON.desdeAbast.desde.slice(0, 5) + ': ≈ ' + CON.desdeAbast.litros + ' L (' + CON.desdeAbast.horas + ').', src: 'Fonte: telemetria' + DEMO + ' (taxa de combustível dos dois motores, ' + CON.periodo + ') · ' + FT.abast.replace('Fonte: ', '') + ' — estimativa; a nota fiscal é a fonte oficial', actions: act(p, [['Abastecimento', 'abast']]) }; },
    mare: function (p) {
      var m = mareTexto();
      if (!m) return { text: 'SEM DADOS de maré agora: sem internet e sem leitura salva neste aparelho.\nO app usa o modelo do Open-Meteo Marine na posição de referência (Balneário Camboriú) — não é a tábua oficial da Marinha (DHN).', src: 'Fonte: nenhuma disponível agora — Open-Meteo Marine sem resposta', actions: act(p, [['Registrar pendência', 'diario']]) };
      return { text: 'Maré agora ' + m.agora + ' em relação ao nível médio do mar (Balneário Camboriú).\nPróximas horas: ' + m.prox.join(' · ') + '.\nÉ modelo (≈ 8 km), não a tábua oficial da Marinha — não use para passar em canal raso. Corrente: ' + SD + '.', src: 'Fonte: Open-Meteo Marine (sea_level_height_msl) · posição de referência ' + ((D.posicaoRef && D.posicaoRef.fonte) || ''), actions: act(p, [['Clima', askHref(p, 'Clima')]]) };
    },
    clima: function (p) {
      var C = window.CapitaoClima, c = C && C.clima ? C.clima() : null;
      return { text: (c ? 'Hoje em Balneário Camboriú: máx ' + Math.round(c.max) + '° · mín ' + Math.round(c.min) + '° (ECMWF via Open-Meteo).' : 'Previsão do dia: ' + SD + ' (sem internet e sem leitura salva).') + '\nLeitura de bordo (snapshot' + DEMO + ' ' + SNAP.quando + '):\n• vento verdadeiro ' + nb(S.vento) + ' nós de ' + grau3(S.ventoDe) + '\n• barômetro ' + nb(S.pressao, 0) + ' hPa\n• ar ' + nb(S.ar) + ' °C · água do mar ' + nb(S.agua) + ' °C\nPrevisão de vento e mar para navegar: ' + SD + ' no app — consulte a meteorologia marinha da Marinha do Brasil.', src: 'Fonte: Open-Meteo (ECMWF) · ' + SNAP.fonte, actions: act(p, [['Telemetria', 'console']]) };
    },
    canal16: function (p) { return { text: 'VHF canal 16 (156,800 MHz) — socorro, urgência e chamada.\n' + MMSI + ' · indicativo ' + (E.indicativo || SD) + ' · rádios VHF 315 (fabricante ' + SD + ').\nRoteiro MAYDAY (' + ROTULO + '), só em perigo grave e iminente:\nMAYDAY, MAYDAY, MAYDAY — AQUI É CAPITÃO IA, CAPITÃO IA, CAPITÃO IA — ' + MMSI + ' — POSIÇÃO: LEIA NO PLOTTER AGORA (último fix ' + SNAP.pos + ' · snapshot' + DEMO + ' ' + SNAP.quando + ') — NATUREZA DO PERIGO — PESSOAS A BORDO — AUXÍLIO NECESSÁRIO — CÂMBIO.\nUrgência sem perigo de vida: PAN-PAN ×3.', src: FT.proto + ' · canal e MMSI informados pelo proprietário', actions: act(p, [['Abrir SOS', 'sos']]) }; },
    checklist: function (p) { var porao = tarefa('porao-teste'); return { text: 'Checklist de saída — do que está catalogado:\n1. Gerador Onan: depois de ligar, confira água no escapamento.\n2. Estabilizador Seakeeper: ligue com antecedência (precisa de AC).\n3. Climatização: filtro de água salgada limpo antes de ligar' + (tarefa('clima-filtro') && tarefa('clima-filtro').dn < 0 ? ' (limpeza ' + prazoTxt(tarefa('clima-filtro')) + ')' : '') + '.\n4. Eletrônicos: plotter ligado, piloto em espera até sair da marina, VHF no canal 16.\n5. Bombas de porão: acione cada uma manualmente e confira o alarme' + (porao && porao.dn < 0 ? ' (teste ' + prazoTxt(porao) + ')' : '') + '.\n6. Diesel BB ' + nb(DI.bb, 0) + ' % · BE ' + nb(DI.be, 0) + ' % — regra: ' + (D.regraAbast || SD) + '.\nAmarração e fechamento: A CONFIRMAR (sem checklist oficial do estaleiro).', src: 'Fonte: ' + guia('checklist') + ' · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['FAQ de bordo', 'faq']]) }; },
    checklistChegada: function (p) { return { text: 'Checklist de chegada — do que está catalogado:\n1. Piloto em espera antes de manobrar.\n2. Estabilizador: desligar ao atracar e manter energia até o volante parar.\n3. Gerador: retirar cargas, 3 a 5 min sem carga, desligar.\n4. Climatização: desligar e fechar a válvula de fundo se o barco ficar parado.\n5. Fechar a saída no diário: horas, consumo e pendências.', src: 'Fonte: ' + guia('checklist') + ' (Chegada)', actions: act(p, [['Fechar no diário', 'diario']]) }; },
    consumo: function (p) { var ab = D.abastecimentos || []; return { text: 'Consumo observado (telemetria' + DEMO + ' ' + CON.periodo + '):\n• cruzeiro — ' + CON.cruzeiro.lph + ' L/h (' + mil(CON.cruzeiro.rpm) + ' rpm · ' + CON.cruzeiro.nos + ' nós, dois motores)\n• marcha lenta — ' + nb(CON.lenta.lph) + ' L/h\nDesde o abastecimento de ' + CON.desdeAbast.desde.slice(0, 5) + ': ≈ ' + CON.desdeAbast.litros + ' L (' + CON.desdeAbast.horas + ').\nAbastecimentos registrados: ' + ab.map(function (a) { return a.d.slice(0, 5) + ' · ' + mil(a.litros) + ' L'; }).join(' · ') + '.', src: 'Fonte: ' + CON.fonte + ' · ' + FT.abast.replace('Fonte: ', ''), actions: act(p, [['Abastecimento', 'abast']]) }; },
    tanques: function (p) { return { text: 'Tanques (snapshot' + DEMO + ' ' + SNAP.quando + '):\n• água doce ' + nb(T.agua) + ' %\n• águas cinzas ' + nb(T.cinzas) + ' %\n• águas negras ' + nb(T.negras) + ' %\n• diesel ' + SNAP.diesel + ' — ' + SNAP.dieselHora + '.', src: FT.tele + ' (diesel ' + (DI.hora || '') + ')', actions: act(p, [['Telemetria', 'console']]) }; },
    contatos: function (p) {
      var eq = D.equipe || {}, per = eq.perfis || [], ap = eq.apoio || [], f = loadEquipe().fones, cad = Object.keys(f).length;
      return { text: 'Acesso total: ' + per.map(function (x) { return x.nome + ' (' + x.papel + ')'; }).join(' · ') + '.\nApoio: ' + ap.map(function (a) { return min1(a.papel) + (a.para ? ' (' + a.para + ')' : ''); }).join(' · ') + '.\nTelefones: ' + (cad ? cad + ' cadastrado(s) neste aparelho — abra Equipe para ligar.' : 'A CADASTRAR em Equipe (ficam só neste aparelho).'), src: 'Fonte: cadastro da equipe' + DEMO + ' · telefones do aparelho', actions: act(p, [['Equipe e contatos', 'equipe']]) };
    },
    anomalias: function (p) {
      var pend = pendencias(), app = loadDiario().filter(function (e) { return /pend[eê]ncia|anomalia|A CONFIRMAR|A CONFERIR/i.test(e.t); }).slice(0, 3);
      return { text: 'Pendências abertas (' + (pend.length + app.length) + '):\n' + pend.map(function (x) { return '• ' + x.d + ' · ' + x.sys + ' — ' + x.t; }).concat(app.map(function (x) { return '• ' + x.d + ' · ' + (x.sys || 'Diário') + ' — ' + String(x.t).slice(0, 110) + ' (app)'; })).join('\n') + '\nAtrasadas na agenda: ' + atrasadas().length + ' (veja Manutenção).', src: FT.diario + ' · diário do app', actions: act(p, [['Abrir diário', 'diario'], ['Manutenção', 'manut']]) };
    },
    porao: function (p) { var t = tarefa('porao-teste'); return { text: 'Teste de bombas de porão e alarmes ' + (t ? prazoTxt(t) + ' (agenda: ' + t.quem + ' · ' + t.intervalo + ')' : SD) + '.\nSem sensor de porão no barramento NMEA — SEM LEITURA.\nAntes de sair: acione cada bomba manualmente e confira o alarme; registre o resultado no diário.', src: FT.agenda + ' · coletor NMEA' + DEMO + ' (sem sentença de porão)', actions: act(p, [['Manutenção', 'manut']]) }; },
    gerador: function (p) { var r = tarefa('gerador-rotor'), rv = tarefa('gerador-revisao'); return { text: fabMod('gerador') + ' · ' + horas(G.horas) + ' h (' + (G.estado || SD) + ' · snapshot' + DEMO + ' ' + SNAP.quando + ').\nLigar: confira óleo, válvula de fundo e filtro de água salgada → segure PARTIDA → espere tensão e frequência estabilizarem → cargas uma a uma, climatização por último.\nDesligar: retire as cargas, 3 a 5 min sem carga, PARADA.' + (r ? '\n' + r.t + ': ' + prazoTxt(r) + '.' : '') + (rv && rv.horas ? ' Revisão (óleo e filtros): ' + rv.vence + ' ou ' + mil(rv.horas.limite) + ' h — faltam ' + nb(rv.horas.faltam) + ' h.' : ''), src: 'Fonte: ' + guia('g_gerador') + ' §1–4 · ' + FT.agenda.replace('Fonte: ', '') + ' · horímetro na telemetria' + DEMO, actions: act(p, [['Passo a passo', 'f4']]) }; },
    telemetria: function (p) {
      var T = S.tanques || {}, G = S.gerador || {}, K = S.seakeeper || {};
      return { text: 'Snapshot' + DEMO + ' de ' + SNAP.quando + ': ' + min1(SNAP.local) + '. Telemetria ao vivo desligada.'
        + '\n• Posição ' + SNAP.pos + ' · SOG ' + nb(S.sog) + ' nó · proa ' + grau3(S.proa) + ' · profundidade ' + nb(S.profundidade) + ' m'
        + '\n• Vento ' + nb(S.vento) + ' nós de ' + grau3(S.ventoDe) + ' · pressão ' + nb(S.pressao, 0) + ' hPa · ar ' + nb(S.ar) + ' °C · mar ' + nb(S.agua) + ' °C'
        + '\n• Baterias 24 V ' + nb(S.bat24, 2) + ' V · 12 V ' + nb(S.bat12, 2) + ' V'
        + '\n• Tanques: água doce ' + nb(T.agua) + ' % · cinzas ' + nb(T.cinzas) + ' % · negras ' + nb(T.negras) + ' %'
        + '\n• Diesel ' + SNAP.diesel + ' — ' + SNAP.dieselHora
        + '\n• ' + SNAP.motores.charAt(0).toUpperCase() + SNAP.motores.slice(1)
        + '\n• Gerador ' + (G.estado || SD) + ' · ' + (G.horas != null ? horas(G.horas) + ' h' : 'horímetro ' + SD) + ' · Seakeeper ' + (K.estado || SD)
        + '\n• Porão e âncora: SEM LEITURA.',
        src: FT.tele, actions: act(p, [['Telemetria', 'console'], ['Manutenção', 'manut']]) };
    },
    posicao: function (p) { return { text: SNAP.pos + ' · ' + (S.estado || SD).toLowerCase() + ' · ' + (S.local || SD) + '\nSOG ' + nb(S.sog) + ' nó · proa ' + grau3(S.proa) + ' · ' + ((S.gps && S.gps.satelites) || '—') + ' satélites · profundidade ' + nb(S.profundidade) + ' m · snapshot' + DEMO + ' ' + SNAP.quando + '.', src: 'Fonte: GPS na rede NMEA 2000 · ' + SNAP.fonte, actions: act(p, [['Telemetria', 'console']]) }; },
    docsvenc: function (p) {
      var ds = (D.documentos || []), com = ds.filter(function (d) { return d.dn != null; }).sort(function (a, b) { return a.dn - b.dn; });
      var vence = com.filter(function (d) { return d.dn <= 90; }), dia = com.filter(function (d) { return d.dn > 90; }), sem = ds.filter(function (d) { return d.st === SD; }), conf = ds.filter(function (d) { return /A CONF/.test(d.st); });
      return { text: 'Vencem primeiro:\n' + (vence.length ? vence.map(function (d) { return '• ' + d.n + ' — ' + d.vence + ' (D-' + d.dn + ')'; }).join('\n') : '• nenhum nos próximos 90 dias') + '\nEm dia: ' + dia.map(function (d) { return min1(d.n) + ' até ' + d.vence; }).join(' · ') + '.\n' + SD + ': ' + sem.map(function (d) { return d.n; }).join(' · ') + '.' + (conf.length ? '\nA CONFERIR: ' + conf.map(function (d) { return d.n; }).join(' · ') + '.' : ''), src: FT.docs, actions: act(p, [['Documentos', 'docs']]) };
    },
    horimetros: function (p) { var o = tarefa('motores-oleo'), rv = tarefa('gerador-revisao'); return { text: 'Horímetros (motores: última leitura ligados ' + (M.hora || SD) + ' · gerador ' + (G.hora || SD) + '):\n• motor BB ' + horas(M.horimetro && M.horimetro[0]) + ' h\n• motor BE ' + horas(M.horimetro && M.horimetro[1]) + ' h\n• gerador ' + horas(G.horas) + ' h\nPróxima troca de óleo dos motores: ' + (o ? o.vence + ' (D-' + o.dn + ') ou ' + o.horas.limite + ' h — faltam ' + nb(o.horas.faltam) + ' h; o que vier antes.' : SD) + (rv ? '\nRevisão do gerador: ' + rv.vence + ' (D-' + rv.dn + ') ou ' + mil(rv.horas.limite) + ' h.' : ''), src: FT.tele + ' · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['Manutenção', 'manut']]) }; },
    motores: function (p) { var e = equip('motores'); return { text: 'Motores ' + (e && e.qtd ? e.qtd + ' × ' : '') + 'Volvo Penta' + (e && e.lados ? ' (' + e.lados + ')' : '') + ' · modelo ' + SD + '.\n' + SNAP.motores.charAt(0).toUpperCase() + SNAP.motores.slice(1) + ' · sem alarme.\nHorímetros BB ' + horas(M.horimetro && M.horimetro[0]) + ' h · BE ' + horas(M.horimetro && M.horimetro[1]) + ' h · troca de óleo ' + prazoTxt(tarefa('motores-oleo')) + ' ou 450 h.\nPartida, aquecimento e parada: ' + guia('g_motores') + '. Faixas oficiais: manual do fabricante — modelo ' + SD + '.', src: 'Fonte: ' + guia('g_motores') + ' · ' + SNAP.fonte, actions: act(p, [['Manutenção', 'manut'], ['FAQ de bordo', 'faq']]) }; },
    estabilizador: function (p) { var an = tarefa('seakeeper-anodo'); return { text: fabMod('estabilizador') + ' · ' + ((S.seakeeper && S.seakeeper.estado) || SD) + ' (snapshot' + DEMO + ' ' + SNAP.quando + ').\n• Só acelera com AC (gerador ou cais); estabiliza quando o display indicar pronto.\n• Ao atracar: desligue e mantenha a energia até o volante parar.\n• Nunca faça manutenção com o volante girando.\nTempo de aceleração e códigos de alarme: MANUAL NO DRIVE (modelo ' + SD + ').' + (an ? '\n' + an.t + ': ' + prazoTxt(an) + '.' : ''), src: 'Fonte: ' + guia('g_seakeeper') + ' §1–6 · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['Passo a passo', 'f2']]) }; },
    climatizacao: function (p) { var f = tarefa('clima-filtro'); return { text: 'Climatização · fabricante e modelo ' + SD + '.\n' + (f ? 'Filtro de água salgada: limpeza ' + prazoTxt(f) + ' — e há fluxo fraco na cabine de proa desde 20/09 (diário).\n' : '') + 'Ligar: válvula de fundo aberta e filtro limpo → bomba de água salgada → controle da cabine.\nAlarme de fluxo: quase sempre falta de água salgada (filtro sujo, válvula fechada, bomba desligada).', src: 'Fonte: ' + guia('g_clima') + ' · ' + FT.agenda.replace('Fonte: ', '') + ' · ' + FT.diario.replace('Fonte: ', '') + ' 20/09', actions: act(p, [['Passo a passo', 'f5']]) }; },
    eletronicos: function (p) { var c = tarefa('garmin-cartas'); return { text: 'Eletrônicos Garmin · áudio Fusion · rádios VHF 315 — modelos ' + SD + '.\n• Homem ao mar: função MOB do plotter Garmin marca a posição.\n• Piloto automático: em espera antes de manobrar na marina.\n• VHF: canal 16 em escuta; o DSC só identifica o barco com o MMSI programado.' + (c ? '\nCartas desatualizadas (diário 28/08) — atualização ' + prazoTxt(c) + '.' : ''), src: 'Fonte: ' + guia('g_eletronicos') + ' · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['FAQ eletrônicos', 'f3']]) }; },
    audio: function (p) { return { text: 'Áudio Fusion · modelo ' + SD + '.\nParear: fonte Bluetooth no controle Fusion → aparelho visível → selecione o Fusion na lista de Bluetooth do celular. Volume ajustado por zona.', src: 'Fonte: ' + guia('g_eletronicos') + ' §6', actions: act(p, [['FAQ eletrônicos', 'f3']]) }; },
    dessalinizador: function (p) { return { text: SD + ' — dessalinizador não consta na lista de equipamentos.\nSe houver a bordo, envie a foto da etiqueta (modelo e número de série) para catalogar.', src: 'Fonte: Inventário de bordo' + DEMO + ' — equipamento não listado', actions: act(p, [['Enviar foto', A(p, 'home') + '#mode=foto']]) }; },
    eletrico: function (p) { var ser = D.serie24v || [], mn = Math.min.apply(null, ser.map(function (x) { return x.min; })), mx = Math.max.apply(null, ser.map(function (x) { return x.max; })), b = tarefa('baterias'); return { text: 'Banco 24 V: ' + nb(S.bat24, 2) + ' V (' + (G.estado ? 'gerador ' + G.estado : '') + ' · snapshot' + DEMO + ' ' + SNAP.quando + ')' + (ser.length ? ' · 7 dias entre ' + nb(mn) + ' e ' + nb(mx) + ' V' : '') + '.\nBanco 12 V: ' + nb(S.bat12, 2) + ' V.' + (b ? '\n' + b.t + ': ' + prazoTxt(b) + ' (' + b.quem + ').' : ''), src: FT.tele + ' · série 24 V · 7 dias · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['Telemetria', 'console']]) }; },
    epirb: function (p) { return { text: 'EPIRB: ' + SD + ' — modelo, localização a bordo, acionamento e validade da bateria não foram carregados.\nEnvie a foto da etiqueta e do certificado para completar o SOS.\n' + MMSI + '.', src: 'Fonte: Inventário de bordo' + DEMO + ' · ' + FT.proto.replace('Fonte: ', '') + ' (EPIRB: ' + SD + ')', actions: act(p, [['Abrir SOS', 'sos'], ['Documentos', 'docs']]) }; },
    seafire: function (p) { return { text: 'Sistema de incêndio Seafire: ' + SD + ' — localização, acionamento automático ou manual e tempo de espera não foram carregados.\nEm incêndio agora: abra o SOS e chame no canal 16.\nEnvie o manual ou o protocolo de bordo do Seafire para completar o passo a passo.', src: 'Fonte: Inventário de bordo' + DEMO + ' · ' + FT.proto.replace('Fonte: ', '') + ' (Seafire: ' + SD + ')', actions: act(p, [['Abrir SOS', 'sos']]) }; },
    // sos/óleo não gravam nada: pergunta informativa não vira linha permanente. Gravar = atalho DIÁRIO DE BORDO ou "registre posição e hora".
    sos: function (p) { return { text: 'Emergência — abra o SOS. ' + SOS_PASSOS + '\n' + GRAVAR_AGORA, src: FT.proto + ' · Seafire e EPIRB: ' + SD, actions: act(p, [['Abrir SOS', 'sos'], ['Registrar no diário', 'diario']]) }; },
    oleo: function (p) { return { text: 'Se a pressão de óleo cair ou o alarme acender, verifique nesta ordem:\n' + OLEO_PASSOS + '\nNo snapshot' + DEMO + ' de ' + SNAP.quando + ' os motores estão desligados; última leitura com motores ligados ' + (M.hora || SD) + ' (marcha lenta, neutro): óleo ' + (M.oleo ? M.oleo.map(function (x) { return nb(x); }).join('/') : '—') + ' bar, sem alarme.\nFaixa normal: manual do fabricante — modelo ' + SD + '.\n' + GRAVAR_AGORA, src: 'Fonte: ' + guia('g_motores') + ' §4 · ' + SNAP.fonte, actions: act(p, [['Registrar no diário', 'diario'], ['Contatos', 'equipe']]) }; },
    oleoLeitura: function (p) { return { text: 'Motores desligados no snapshot' + DEMO + ' de ' + SNAP.quando + '. Pressão do óleo na última leitura com motores ligados ' + (M.hora || SD) + ': ' + (M.oleo ? M.oleo.map(function (x) { return nb(x); }).join('/') : '—') + ' bar · ' + (M.rpm ? M.rpm.join('/') : '—') + ' rpm em neutro · arrefecimento ' + (M.arref ? M.arref.join('/') : '—') + ' °C · sem alarme.\nFaixa normal: manual Volvo Penta — modelo ' + SD + '.\nSe cair abaixo da faixa ou o alarme acender, pergunte “pressão de óleo baixa” para o passo a passo.', src: FT.tele + ' · ' + guia('g_motores'), actions: act(p, [['Telemetria', 'console'], ['Pressão baixa: o que fazer', askHref(p, 'Pressão de óleo baixa: o que verificar primeiro?')]]) }; },
    ancora: function (p) { return { text: 'Sem sensor de âncora na rede NMEA — SEM LEITURA do ferro.\n' + (S.estado || SD) + ' · ' + (S.local || SD) + ' · ' + SNAP.pos + ' · profundidade ' + nb(S.profundidade) + ' m (snapshot' + DEMO + ' ' + SNAP.quando + ').\nAlarme de âncora: ative no plotter e defina o raio conforme o cabo lançado e o espaço de giro.', src: 'Fonte: ' + guia('g_eletronicos') + ' §3 · ' + SNAP.fonte, actions: act(p, [['FAQ eletrônicos', 'f3']]) }; },
    manual: function (p) { var g = D.guias || {}; return { text: 'Guias de bordo carregados' + DEMO + ' — orientação genérica, não substituem o manual do fabricante:\n' + ['g_gerador', 'g_seakeeper', 'g_clima', 'g_eletronicos', 'g_motores', 'checklist'].map(function (k) { return '• ' + (g[k] || SD); }).join('\n') + '\nManuais dos fabricantes: ' + SD + ' (modelos não informados). Seafire e EPIRB: ' + SD + '.', src: 'Fonte: ' + ((D.drive && D.drive.raiz) || 'Drive') + ' › ' + ((D.drive && D.drive.pastas && D.drive.pastas.manuais) || ''), actions: act(p, [['FAQ de bordo', 'faq']]) }; },
    diarioLer: function (p) {
      var mine = loadDiario(), fonte = diarioFonte();
      var lines = mine.slice(0, 3).map(function (e) { return '• ' + (e.d || '') + ' · ' + (e.sys || 'Diário') + ' — ' + String(e.t || '').slice(0, 110) + ' (app)'; });
      var fixed = fonte.map(function (e) { return '• ' + e.d + ' ' + e.h + ' · ' + e.sys + ' — ' + e.t.slice(0, 110); });
      return { text: 'Últimos registros do diário de bordo (' + (fonte.length + mine.length) + ' no total · ' + pendencias().length + ' pendências abertas):\n' + lines.concat(fixed).slice(0, 4).join('\n') + '\nPara registrar, diga “registre no diário…” ou toque no atalho DIÁRIO DE BORDO.', src: FT.diario + ' + registros do app', actions: act(p, [['Abrir diário', 'diario']]) };
    },
    fallback: function (p) { return { text: 'Não encontrei esse dado nas fontes de bordo — telemetria, agenda, documentos, diário e guias de bordo. SEM DADOS.\nPosso registrar como pendência no diário, ou você envia uma foto (etiqueta, tela, nota) para eu identificar.', src: 'Fonte: nenhuma — hierarquia: manual oficial › registro oficial › laudo › diário › foto › nota informal', actions: (BASE ? [BASE] : []).concat(act(p, [['Registrar pendência', 'diario'], ['FAQ de bordo', 'faq']])) }; }
  };

  // ——— Telemetria ao vivo (capitao-telemetria.js) ———
  // Com o coletor conectado e a leitura com menos de 10 min, posição, tanques, tempo, baterias e Seakeeper saem da leitura real;
  // sem isso (padrão de hoje), as respostas continuam com o snapshot do capitao-dados.js.
  function vivo() { var TL = window.CapitaoTelemetria; return TL && TL.atual ? TL.atual() : null; }
  var VIVO = {
    posicao: function (v) { var TL = window.CapitaoTelemetria; return { text: TL.posicao(v) + (v.sog_nos < 0.5 ? ' · parado' : '') + '\nSOG ' + nb(v.sog_nos) + ' nós · proa ' + grau3(v.proa_graus) + ' · ' + nb(v.gps_satelites, 0) + ' satélites · profundidade ' + nb(v.profundidade_m) + ' m · ao vivo ' + TL.hora(v) + '.' }; },
    tanques: function (v) { return { text: 'Tanques agora:\n• água doce ' + nb(v.tanque_agua_pct) + ' %\n• águas cinzas ' + nb(v.tanque_cinzas_pct) + ' %' + (v.tanque_cinzas_pct > 70 ? ' — atenção: programar esgoto' : '') + '\n• águas negras ' + nb(v.tanque_negras_pct) + ' %' + (v.tanque_negras_pct > 70 ? ' — atenção: programar esgoto' : '') + '\n• diesel: ' + SNAP.diesel + ' — ' + SNAP.dieselHora + '.' }; },
    clima: function (v, base) { return { text: 'Agora a bordo (ao vivo ' + window.CapitaoTelemetria.hora(v) + '):\n• vento verdadeiro ' + nb(v.vento_verdadeiro_nos) + ' nós de ' + grau3(v.vento_verdadeiro_angulo) + '\n• barômetro ' + nb(v.pressao_barometrica_hpa, 0) + ' hPa\n• ar ' + nb(v.temp_ar_externo_c) + ' °C · água ' + nb(v.temp_agua_c) + ' °C\n' + base.text.split('\n')[0] }; },
    eletrico: function (v, base) { return { text: 'Baterias agora: banco 24 V ' + nb(v.bateria_0_tensao_v, 2) + ' V · banco 12 V ' + nb(v.bateria_2_tensao_v, 2) + ' V (ao vivo ' + window.CapitaoTelemetria.hora(v) + ').\n' + base.text.split('\n').slice(2).join('\n') }; },
    estabilizador: function (v, base) { return { text: 'Seakeeper agora: ' + (v.seakeeper_ativo ? 'LIGADO' + (typeof v.seakeeper_volante_rpm === 'number' ? ' · volante ' + nb(v.seakeeper_volante_rpm, 0) + ' rpm (' + nb(v.seakeeper_volante_pct, 0) + ' %)' : '') : 'desligado') + ' · ao vivo ' + window.CapitaoTelemetria.hora(v) + '.\n' + base.text.split('\n').slice(1).join('\n') }; }
  };
  Object.keys(VIVO).forEach(function (k) {
    var pronta = ANSWERS[k]; if (!pronta) return;
    ANSWERS[k] = function (p, ctx, q) {
      var base = pronta(p, ctx, q), v = vivo(); if (!v) return base;
      var r = VIVO[k](v, base);
      return { text: r.text, src: 'Fonte: coletor NMEA · ao vivo ' + window.CapitaoTelemetria.hora(v), actions: base.actions };
    };
  });

  var EQUIP = ['seakeeper', 'estabilizador', 'climatiza', 'ar condicionado', 'ar-condicionado', 'gerador', 'onan', 'piloto', 'plotter', 'radar', 'garmin', ' vhf', ' ais ', 'epirb', 'fusion', 'audio', 'dessaliniz', 'bomba', 'porao', 'casco', 'anodo', 'zinco', 'bateria', 'tensao', 'tensoes', 'seafire', 'volvo'];
  function route(qRaw) {
    var q = pad(qRaw);
    if (!q.trim()) return 'saudacao';
    if (querRegistrar(qRaw, q)) return 'diario';
    if (emergencia(q)) return 'sos';
    var ol = oleo(q);
    if (ol) return ol === 1 ? 'oleo' : 'oleoLeitura';
    if (has(q, ['seguro para sair', 'posso sair', 'da pra sair', 'da para sair', 'seguro sair', 'avalie vento', 'sair hoje', 'seguro navegar', 'seguro para navegar', 'posso navegar', 'podemos sair', 'podemos navegar', 'da pra navegar', 'da para navegar'])) return 'seguro';
    if (has(q, ['telemetria', 'leituras', 'sensores', 'como esta o barco', 'estado do barco', 'status do barco'])) return 'telemetria';
    if (has(q, ['anomalia', 'pendencia', 'problema aberto'])) return 'anomalias';
    if (has(q, ['diario'])) return 'diarioLer';
    if (has(q, [' mare', 'correnteza', 'corrente de mare']) || (has(q, [' corrente']) && !has(q, ['bateria', 'carregador', 'eletric', 'tensao', 'amper', 'alternada', 'continua', 'shore', 'tomada', ' ac ', ' dc ', 'ancora', 'amarra']))) return 'mare';
    if (has(q, [' clima ', 'climatic', 'tempo hoje', ' vento', 'chuva', 'meteor', 'temperatura hoje']) || (has(q, ['previsao']) && !has(q, [' revisao', 'manutenc', 'devoluc', 'entrega', 'chegada']))) return 'clima';
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
    if (has(q, ['epirb', 'radiobaliza'])) return 'epirb';
    if (has(q, ['seafire', 'sea fire', 'sea-fire', 'extintor', 'sistema de incendio'])) return 'seafire';
    // documento/licença antes do rádio: "Licença de estação" é documento, não MAYDAY
    if (has(q, ['document', 'licenc', ' tie ', 'titulo de inscricao', 'seguro da', 'apolice', 'laudo', 'vistoria', 'vencendo', 'certificado', 'garantia'])) return 'docsvenc';
    if (has(q, ['canal 16', ' vhf', ' radio', ' ais ', 'mmsi', ' dsc', 'pan-pan', 'pan pan'])) return 'canal16';
    if (has(q, ['contato', 'telefone', 'equipe', 'oficina', 'quem chamar', 'tecnico de bordo', 'marina da base'])) return 'contatos';
    if (has(q, ['porao', 'bomba'])) return 'porao';
    if (has(q, ['gerador', 'onan'])) return 'gerador';
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
    if (has(q, ['motor', 'partida', 'volvo', 'penta', ' revisao'])) return 'motores';
    if (has(q, ['manutenc', 'vence', 'atrasad', 'agenda', 'tarefa'])) return 'manutencao';
    if (has(q, ['bateria', '24 v', '24v', '12 v', '12v', 'eletric', 'tensao', 'voltagem', 'carregador'])) return 'eletrico';
    if (has(q, ['posicao', 'onde estou', 'onde esta o barco', 'coordenada', ' gps', ' proa', 'velocidade'])) return 'posicao';
    if (has(q, [' oi ', ' ola ', 'bom dia', 'boa tarde', 'boa noite', 'ajuda', 'o que voce faz', 'quem e voce'])) return 'saudacao';
    return 'fallback';
  }

  var CANON = {}; ALL.forEach(function (x) { CANON[x.id] = norm(x.q).trim(); });

  // ——— Base de conhecimento de bordo (base-conhecimento.json) ———
  // Trechos dos guias de bordo (hoje, DEMO). Quando a resposta pronta não tem o dado, o chat e a voz buscam aqui
  // (BM25 com sinônimos PT/EN) e respondem com o trecho e a fonte. Carrega em segundo plano; funciona offline (cache do SW).
  var KB = { docs: null, carregando: false, df: {}, media: 1 };
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
    parear: ['emparelhar', 'pairing', 'conectar', 'bluetooth'], emparelhar: ['parear', 'bluetooth'], alarm: ['alarme'], lubrificante: ['oil', 'oleo'], tanque: ['tank'], mob: ['homem', 'mar'], homem: ['mob']
  };
  function raiz(w) { if (/^\d/.test(w)) return w; w = w.replace(/coes$/, 'cao').replace(/oes$/, 'ao').replace(/aes$/, 'ao'); return w.length > 4 ? w.replace(/(es|s)$/, '') : w; }
  function tokens(t) {
    return norm(t).replace(/[^a-z0-9]+/g, ' ').split(' ').filter(function (w) { return w && !PARADAS[w] && (w.length > 2 || /\d/.test(w)); }).map(raiz);
  }
  function carregaBase() {
    if (KB.docs || KB.carregando || !window.fetch) return;
    KB.carregando = true;
    fetch('./base-conhecimento.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
      var lista = j && j.trechos; if (!lista || !lista.length) return;
      var soma = 0, df = {};
      lista.forEach(function (d) {
        var sec = d.secao || '', tf = {}, tk = tokens(sec + ' ' + sec + ' ' + sec + ' ' + d.texto + ' ' + (d.fonte || '') + ' ' + (d.equip || ''));
        d._lista = /invent[aá]rio|cat[aá]logo|[íi]ndice/i.test(d.fonte || '');
        d._en = (' ' + d.texto.toLowerCase() + ' ').split(/\b(?:the|and|with|to|of|is|are|your|from)\b/).length > 6;
        tk.forEach(function (w) { tf[w] = (tf[w] || 0) + 1; });
        Object.keys(tf).forEach(function (w) { df[w] = (df[w] || 0) + 1; });
        d._tf = tf; d._n = tk.length; soma += tk.length;
      });
      KB.df = df; KB.media = soma / lista.length; KB.docs = lista;
    }).catch(function () {}).then(function () { KB.carregando = false; });
  }
  // Devolve até n trechos { d, nota } ou [] se nada for relevante o bastante.
  var PROCEDIMENTO = /\b(como|o que fazer|procedimento|passo|trocar|troca|ligar|desligar|parear|alarme|falha|codigo|superaquec\w*|oleo|capacidade)\b/;
  function buscaBase(q, n) {
    if (!KB.docs) { carregaBase(); return []; }
    var qs = tokens(q).filter(function (w, k, a) { return a.indexOf(w) === k; });
    if (!qs.length) return [];
    // cada palavra da pergunta vira um grupo (ela + sinônimos); o trecho precisa cobrir a maioria dos grupos
    var grupos = qs.map(function (w) { var g = {}; g[w] = 1; (SINONIMOS[w] || []).forEach(function (x) { x = raiz(x); if (!g[x]) g[x] = 0.6; }); return g; });
    var N = KB.docs.length, k1 = 1.2, b = 0.75, res = [], proc = PROCEDIMENTO.test(' ' + norm(q) + ' ');
    KB.docs.forEach(function (d) {
      var nota = 0, bateu = 0, secao = d._sec || (d._sec = ' ' + tokens(d.secao || '').join(' ') + ' '), naSecao = 0;
      grupos.forEach(function (g) {
        var melhor = 0;
        for (var w in g) {
          var f = d._tf[w]; if (!f) continue;
          var idf = Math.log(1 + (N - KB.df[w] + 0.5) / (KB.df[w] + 0.5));
          melhor = Math.max(melhor, g[w] * idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * d._n / KB.media)));
          if (secao.indexOf(' ' + w + ' ') !== -1) naSecao++;
        }
        if (melhor > 0) { bateu++; nota += melhor; }
      });
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
  var GENERICAS = { gerador: 1, motores: 1, audio: 1, estabilizador: 1, eletronicos: 1, climatizacao: 1, dessalinizador: 1, eletrico: 1, porao: 1, ancora: 1, manual: 1, clima: 0 };
  var ESPECIFICA = /\b(como|trocar|troca|substitu\w*|parear|pareamento|conectar|codigo|codigos|alarme|alarmes|erro|falha|falhas|defeito|superaquec\w*|oleo|filtro|impeller|impelidor|rotor|capacidade|litros|pressao|temperatura|onde fica|localiza\w*|procedimento|passo|reset\w*|calibr\w*|configur\w*|limp\w*|intervalo|torque|especifica\w*|viscosidade|bluetooth|dsc|mob|zinco|anodo|fusivel|disjuntor|fluxo)\b/;
  function respostaBase(q, p) {
    var hits = buscaBase(q, 3); if (!hits.length) return null;
    var h = hits[0].d, outros = hits.slice(1).filter(function (x) { return x.d.fonte !== h.fonte || x.d.secao !== h.secao; });
    var text = trechoCurto(h.texto) + (outros.length ? '\nVeja também: ' + outros.map(function (x) { return citaFonte(x.d); }).join(' · ') : '');
    return { text: text, src: 'Fonte: ' + citaFonte(h) + ' — base de conhecimento de bordo' + (h.equip ? ' · ' + h.equip : ''), actions: act(p, [['FAQ de bordo', 'faq']]), ref: citaFonte(h), ingles: !!h._en };
  }
  if (window.requestIdleCallback) requestIdleCallback(carregaBase, { timeout: 4000 }); else setTimeout(carregaBase, 1500);

  function answer(q, ctx) {
    ctx = ctx || {};
    var p = ctx.platform || 'web';
    var key = null;
    if (ctx.id && ANSWERS[ctx.id] && (!String(q || '').trim() || norm(q).trim() === CANON[ctx.id])) key = ctx.id;
    if (!key) key = route(q);
    if (!ANSWERS[key]) key = 'fallback';
    var a;
    try { a = ANSWERS[key](p, ctx, String(q || '').trim()); } catch (e) { key = 'fallback'; a = ANSWERS.fallback(p, ctx); }
    // Sem resposta pronta, ou pergunta específica sobre um equipamento (como, código, óleo, alarme, onde fica…): o trecho do guia vale mais que o resumo genérico.
    if (key === 'fallback' || (GENERICAS[key] && ESPECIFICA.test(' ' + norm(q) + ' '))) { var kb = null; try { kb = respostaBase(q, p); } catch (e) {} if (kb) { a = kb; key = 'base'; } }
    a.key = key;
    return a;
  }

  // Anexos (foto/vídeo): não saem do aparelho — viram linha A CONFIRMAR no diário.
  function answerAttachment(kind, file, ctx) {
    var p = (ctx && ctx.platform) || 'web';
    var name = file && file.name ? file.name : (kind === 'video' ? 'vídeo' : 'foto');
    var kb = file && file.size ? Math.round(file.size / 1024) + ' KB' : '';
    var n = now(), grava = !ctx || ctx.commit !== false, nao = 'não anexei ao diário (pedido vindo de link).';
    if (grava) addDiario({ sys: 'Equipamentos', tone: 'var(--cap-accent, #00a1fe)', t: (kind === 'video' ? 'Vídeo' : 'Foto') + ' anexada pelo chat: ' + name + (kb ? ' (' + kb + ')' : '') + ' — identificação A CONFIRMAR.', who: quem(), src: 'app · ' + kind });
    if (kind === 'video') return { key: 'video', text: 'Vídeo recebido (' + name + (kb ? ' · ' + kb : '') + ') · ' + n.d + ' ' + n.t + '.\nO som e o comportamento não são analisados automaticamente: ' + (grava ? 'anexei ao diário como anomalia A CONFIRMAR, com o estado do snapshot' + DEMO + ' (' + SNAP.local.toLowerCase() + ' · motores desligados · gerador ligado).' : nao) + '\nDescreva em uma frase o que você viu ou ouviu — respondo com o que verificar primeiro.', src: 'Fonte: anexo · diário de bordo', actions: act(p, [['Abrir diário', 'diario']]) };
    return { key: 'foto', text: 'Foto recebida (' + name + (kb ? ' · ' + kb : '') + ') · ' + n.d + ' ' + n.t + '.\nA leitura da imagem não é automática: ' + (grava ? 'anexei ao diário como A CONFIRMAR.' : nao) + ' Para etiqueta ou tela de alarme, digite o modelo/código que aparece e eu localizo o guia; para nota fiscal, registre em Abastecimento (fica A CONFIRMAR).', src: 'Fonte: anexo · diário de bordo', actions: act(p, [['Abrir diário', 'diario'], ['Documentos', 'docs']]) };
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
  // Vigia de cada bloco a 1x: 95 ms/letra (folga) + 250 ms/dígito, porque número falado é longo.
  function estimaMs(t) { return Math.min(60000, 2000 + t.length * 95 + (t.match(/\d/g) || []).length * 250); }
  var FALA = { gen: 0, timer: null, vivo: null, fila: [] };
  function calaTimers() { clearTimeout(FALA.timer); clearInterval(FALA.vivo); FALA.timer = FALA.vivo = null; }
  // Eventos 'capitao-voz' ({ estado: ouvindo | pensando | falando | pulso | livre, texto }) — núcleo de IA (capitao-voz.js).
  function evVoz(estado, texto) { try { window.dispatchEvent(new CustomEvent('capitao-voz', { detail: { estado: estado, texto: texto || '' } })); } catch (e) {} }
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
    var msg = 'Olá, ' + nome + '! Você foi convidado(a) para o Capitão IA — embarcação ' + (E.nome || 'Capitão IA') + (D.demo ? ' (demonstração)' : '') + ', acesso ' + (acesso || 'total') + '.\nEntre por: ' + url + '\nO usuário e a senha são passados pelo proprietário.';
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
      u.lang = voz && voz.lang ? String(voz.lang).replace(/_/g, '-') : 'pt-BR'; if (voz) u.voice = voz; u.rate = 1;
      u.onstart = function () { if (vale(u)) { vigia(u, est); evVoz('falando', legenda(k, partes.length)); } };
      u.onboundary = function (e) { if (vale(u) && (!e || e.name !== 'sentence')) evVoz('pulso'); };
      u.onend = function () { if (vale(u)) avanca(); };
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
      evVoz('falando', legenda(k, partes.length));
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
    var t = a && typeof a === 'object' ? a.text : a;
    if (a && a.key && FALA_INTEIRA[a.key]) return String(t || '');
    if (a && a.key === 'base' && a.ingles) return 'Está no ' + String(a.ref || 'manual').replace(/, p\. /, ', página ').replace(/ · .*$/, '') + ', em inglês. Mostrei o trecho na tela.';
    var item = function (l) { return l.replace(/^(\d+[.)]|•|-)\s*/, '').replace(/\s*\([^)]*\)/g, '').trim(); };
    var ls = String(t || '').split(/\n+/).map(function (l) { return l.trim(); }).filter(function (l) { return l && !/^fonte\b/i.test(l); });
    var r = (ls[0] || '').replace(/\s*\([^)]*\)/g, ''), extra = [];
    if (/ressalva/i.test(r)) extra = ls.filter(function (l) { return /ressalva\s*\d/i.test(l); }).map(function (l) { return item(l).replace(/^ressalva\s*\d+:\s*/i, '').split(' — ')[0]; });
    else if (/:$/.test(r)) { r = r.replace(/:$/, ''); extra = ls.slice(1, 3).filter(function (l) { return /^(\d+[.)]|•|-)/.test(l); }).map(item); }
    if (extra.length) r = r.replace(/[.]$/, '') + ': ' + extra.join('; ') + '.';
    if (r.length > 220) { var m = r.slice(0, 220).match(/^[\s\S]*[.!?;]/); r = m ? m[0] : r.slice(0, r.lastIndexOf(' ', 220)) + '.'; }
    return r;
  }

  // Controles do overlay de voz (capitao-voz.js)
  function vozEnviar() { if (ESCUTA.rec) ESCUTA.rec.parar(); }
  function pularFala() { if (FALA.pula) FALA.pula(); }
  function vozEncerrar() {
    try { window.dispatchEvent(new CustomEvent('capitao-voz-encerrar')); } catch (e) {} // a tela desliga a conversa e limpa o estado
    var r = ESCUTA.rec; ESCUTA.rec = null; if (r) try { r.cancelar(); } catch (e) {}
    stopSpeaking();
  }

  window.CapitaoBrain = { DADOS: D, BASE: BASE, buscaBase: buscaBase, carregaBase: carregaBase, DEFAULTS: DEFAULTS, BANK: BANK, ALL: ALL, HREF: HREF, loadShortcuts: loadShortcuts, saveShortcuts: saveShortcuts, resetShortcuts: resetShortcuts, bankFor: bankFor, loadDiario: loadDiario, addDiario: addDiario, diarioFonte: diarioFonte, loadExec: loadExec, markExec: markExec, unmarkExec: unmarkExec, loadEquipe: loadEquipe, saveEquipe: saveEquipe, loadDocs: loadDocs, addDoc: addDoc, loadAbast: loadAbast, addAbast: addAbast, answer: answer, answerAttachment: answerAttachment, quem: quem, route: route, parseHash: parseHash, clearHash: clearHash, recognizer: recognizer, ditado: ditado, linkConvite: linkConvite, speak: speak, stopSpeaking: stopSpeaking, abertura: abertura, falaCurta: falaCurta, vozEnviar: vozEnviar, pularFala: pularFala, vozEncerrar: vozEncerrar, falavel: falavel, voz: vozPtBr, now: now, askHref: askHref, nb: nb, mil: mil, horas: horas, grau3: grau3, SNAP: SNAP, SOS_PASSOS: SOS_PASSOS, MMSI: MMSI, ROTULO: ROTULO };
  try { window.dispatchEvent(new CustomEvent('capitao-brain-ready')); } catch (e) {}
})();
