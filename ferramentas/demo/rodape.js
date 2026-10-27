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
