/* Capitão IA — gráfico do histórico e da janela de 150 s (PARIDADE F07 e F33; PROMPT Fase 4 «Gráficos»).
   Um gráfico só para a Ponte (A1, A2) e o Abastecimento (G2): um elemento React (nunca {{…}} em atributo de SVG: a tela entrega o elemento pronto no lugar do `{{grafico}}`).
     CapitaoGrafico.elemento({ metrica, janela, altura?, largura?, compacto? })   → o gráfico (função de componente: guarda o cursor e a largura, ouve 'capitao-telemetria')
     CapitaoGrafico.dados(metrica, janela, ms?)  → { ok, motivo?, paineis: [{ series: [{ campo, n, pts: [{ms, v, min, max}], agora }], lo, hi, passo }], t0, t1 } (o mesmo que o gráfico desenha)
     CapitaoGrafico.METRICAS / ORDEM / JANELAS · janelaValida(metrica, janela) · so150(metrica) · rotulo(metrica)
   Métricas: baterias (3 séries: serviço e partida de 24 V num painel, o banco de 12 V em outro), temperaturas (praça de máquinas, ar e água), vento, pressão, água, servidas
   (cinzas e negras), diesel (o serrote do dia com a reserva), e as do laço de 150 s: rotação, óleo e arrefecimento dos motores. Janelas: 150 s (a volta do replay, um ponto
   por segundo), 1 D, 7 D, 30 D e 1 A (D.historico). As séries vêm todas do CapitaoReplay.serie(campo, janela): o último ponto é o quadro de agora (o ponto «agora» do gráfico,
   marcado e legendado), linha contínua, sem NaN. As métricas do laço (rotação, óleo, arrefecimento) só têm a janela de 150 s: nas longas a volta se repete e a linha sairia reta.
   Cursor (mouse, dedo ou teclado de ponteiro): linha no instante, pontos nas séries e uma caixa com a hora e os valores. Claro e escuro pelas variáveis --cap-*.
   Sem o replay (modo real: simulacao false, ou sem tabela) a série não existe: o gráfico diz SEM DADOS e a leitura de agora, e nada é desenhado (o caminho `null` não se apaga).
   Nenhum timer: o gráfico ouve o 'capitao-telemetria' (1 s, parado com a página oculta). Nunca lança erro. No SOS o arquivo nem se define (o SOS não lê a reprodução). */
(function () {
  var EM_SOS = false;
  try { EM_SOS = /SOS-/.test(location.pathname); } catch (e) {}
  if (EM_SOS || window.CapitaoGrafico) return;

  var COR = ['var(--cap-accent, #00a1fe)', 'var(--cap-tele, #00f4fd)', 'var(--cap-violeta, #b45cff)'];
  var COR_NOME = ['azul', 'ciano', 'violeta'];
  var JANELAS = {
    '150S': { rot: '150 s', nome: 'últimos 150 s', media: 'um ponto por segundo' },
    '1D': { rot: '1 D', nome: 'últimas 24 h', media: 'média a cada 15 min' },
    '7D': { rot: '7 D', nome: 'últimos 7 dias', media: 'média por hora' },
    '30D': { rot: '30 D', nome: 'últimos 30 dias', media: 'média a cada 6 h' },
    '1A': { rot: '1 A', nome: 'último ano', media: 'média por dia' }
  };
  var ORDEM = ['baterias', 'temperaturas', 'vento', 'pressao', 'agua', 'servidas', 'diesel', 'rpm', 'oleo', 'arref'];
  // paineis: cada um tem a escala dele (as baterias de 24 V e a de 12 V não cabem na mesma). `min`: a menor amplitude da escala (sem ela o ruído viraria montanha);
  // `zero`: a escala parte do zero; `fixo`: escala fixa; `ref`: o campo cuja faixa do guia vira uma linha de referência (D.replay.limites).
  var METRICAS = {
    baterias: { rot: 'Baterias', paineis: [
      { min: 0.6, series: [{ campo: 'bateria_0_tensao_v', n: 'serviço 24 V' }, { campo: 'bateria_1_tensao_v', n: 'partida 24 V' }] },
      { min: 0.6, series: [{ campo: 'bateria_2_tensao_v', n: 'banco 12 V' }] }] },
    temperaturas: { rot: 'Temperaturas', paineis: [{ min: 6, series: [{ campo: 'temp_praca_maquinas_c', n: 'praça de máquinas' }, { campo: 'temp_ar_externo_c', n: 'ar' }, { campo: 'temp_agua_c', n: 'água do mar' }] }] },
    vento: { rot: 'Vento', paineis: [{ min: 5, zero: true, series: [{ campo: 'vento_verdadeiro_nos', n: 'vento verdadeiro' }] }] },
    pressao: { rot: 'Pressão', paineis: [{ min: 6, series: [{ campo: 'pressao_barometrica_hpa', n: 'barômetro' }] }] },
    agua: { rot: 'Água', paineis: [{ fixo: [0, 100], series: [{ campo: 'tanque_agua_pct', n: 'água doce' }] }] },
    servidas: { rot: 'Servidas', paineis: [{ fixo: [0, 100], series: [{ campo: 'tanque_cinzas_pct', n: 'cinzas' }, { campo: 'tanque_negras_pct', n: 'negras' }] }] },
    diesel: { rot: 'Diesel', paineis: [{ fixo: 'diesel', ref: { campo: 'diesel_litros', lado: 'de', n: 'reserva' }, series: [{ campo: 'diesel_litros', n: 'diesel a bordo' }] }] },
    rpm: { rot: 'Rotação', so150: true, paineis: [{ min: 500, zero: true, series: [{ campo: 'motor_bb_rpm', n: 'motor BB' }, { campo: 'motor_be_rpm', n: 'motor BE' }] }] },
    oleo: { rot: 'Óleo', so150: true, paineis: [{ min: 2, zero: true, series: [{ campo: 'motor_bb_oleo_bar', n: 'motor BB' }, { campo: 'motor_be_oleo_bar', n: 'motor BE' }] }] },
    arref: { rot: 'Arrefecimento', so150: true, paineis: [{ min: 20, ref: { campo: 'motor_bb_arref_c', lado: 'ate', n: 'aviso' }, series: [{ campo: 'motor_bb_arref_c', n: 'motor BB' }, { campo: 'motor_be_arref_c', n: 'motor BE' }] }] }
  };

  function D() { return window.CapitaoDados || {}; }
  function A() { return window.CapitaoAgora || null; }
  function num(x) { return typeof x === 'number' && isFinite(x); }
  function p2(n) { return (n < 10 ? '0' : '') + n; }
  function desloc(ms) { var a = A(); try { return a && typeof a.off === 'function' ? a.off(ms) : -180; } catch (e) { return -180; } }
  function loc(ms) { return ms + desloc(ms) * 60000; }   // a hora de parede do barco: os campos UTC do resultado são os da parede
  function hhmm(ms, seg) { var d = new Date(loc(ms)); return p2(d.getUTCHours()) + ':' + p2(d.getUTCMinutes()) + (seg ? ':' + p2(d.getUTCSeconds()) : ''); }
  function ddmm(ms) { var d = new Date(loc(ms)); return p2(d.getUTCDate()) + '/' + p2(d.getUTCMonth() + 1); }
  var MES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

  function janelaValida(met, jan) { var m = METRICAS[met]; return m && m.so150 ? '150S' : JANELAS[jan] ? jan : '7D'; }
  function so150(met) { return !!(METRICAS[met] && METRICAS[met].so150); }
  function rotulo(met) { return METRICAS[met] ? METRICAS[met].rot : ''; }

  // o número como a tela mostra (as casas e o milhar do D.campos, a mesma regra do CapitaoAgora.fmt.campo), ou null
  function casasDe(campo) { var c = D().campos && D().campos[campo]; return c && num(c.casas) ? c.casas : 0; }
  function valTxt(campo, v, comUn) {
    var c = D().campos && D().campos[campo], a = A(), t;
    if (!num(v) || !a || !a.fmt) return null;
    t = a.fmt.nb(v, casasDe(campo), !!(c && c.mil));
    return t === null || t === undefined ? null : t + (comUn !== false && c && c.un ? ' ' + c.un : '');
  }
  function unDe(campo) { var c = D().campos && D().campos[campo]; return c && c.un ? c.un : ''; }

  // limite do guia como linha de referência (D.replay.limites; o valor na escala do campo)
  function refDe(ref) {
    var L = D().replay && D().replay.limites && D().replay.limites[ref.campo], n = L && L.normal, v = n ? n[ref.lado] : null;
    return num(v) ? { v: v, n: ref.n + ' ' + (ref.lado === 'de' ? '' : 'acima de ') + String(v).replace('.', ',') + ' ' + unDe(ref.campo) } : null;
  }

  // escala «redonda» do painel: passos 0,1 · 0,2 · 0,25 · 0,5 · 1 · 2 · 2,5 · 5 · 10 … até 4 intervalos (menos em painel baixo)
  var PASSOS = [0.01, 0.02, 0.025, 0.05, 0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10, 20, 25, 50, 100, 200, 250, 400, 500, 1000];
  function escala(pn, vals, ref, alvo) {
    var lo = Infinity, hi = -Infinity, i, c, p, fx = pn.fixo;
    if (fx === 'diesel') { var cap = D().embarcacao && D().embarcacao.tanques && D().embarcacao.tanques.diesel_l; fx = num(cap) && cap > 0 ? [0, cap] : null; }
    if (Array.isArray(fx)) { lo = fx[0]; hi = fx[1]; }
    else {
      for (i = 0; i < vals.length; i++) { if (vals[i] < lo) lo = vals[i]; if (vals[i] > hi) hi = vals[i]; }
      if (ref) { lo = Math.min(lo, ref.v); hi = Math.max(hi, ref.v); }
      if (pn.zero) lo = Math.min(lo, 0);
      if (hi - lo < (pn.min || 0)) { c = (hi + lo) / 2; lo = c - pn.min / 2; hi = c + pn.min / 2; if (pn.zero && lo < 0) { hi -= lo; lo = 0; } }
    }
    p = PASSOS[PASSOS.length - 1];
    for (i = 0; i < PASSOS.length; i++) if ((hi - lo) / PASSOS[i] <= alvo) { p = PASSOS[i]; break; }
    if (!Array.isArray(fx)) { lo = Math.floor(lo / p + 1e-9) * p; hi = Math.ceil(hi / p - 1e-9) * p; }
    if (!(hi > lo)) hi = lo + p;
    return { lo: lo, hi: hi, passo: p };
  }

  // Os dados do gráfico: cada série do replay na janela, com a escala do painel. ok false (e o motivo) quando falta qualquer coisa: nada é desenhado pela metade.
  function dados(met, jan, ms, altura) {
    var M = METRICAS[met], R = window.CapitaoReplay, out = { met: met, jan: jan, ok: false, motivo: '', paineis: [], t0: 0, t1: 0 }, k, j, pn, s, pts, i, vals, e, p, gi = 0;
    try {
      if (!M || !JANELAS[jan]) { out.motivo = 'metrica'; return out; }
      if (M.so150 && jan !== '150S') { out.motivo = 'so150'; return out; }
      if (!R || typeof R.serie !== 'function') { out.motivo = 'sem-replay'; return out; }
      for (k = 0; k < M.paineis.length; k++) {
        pn = M.paineis[k]; p = { series: [], lo: 0, hi: 1, passo: 1, ref: null }; vals = [];
        for (j = 0; j < pn.series.length; j++) {
          s = pn.series[j]; pts = R.serie(s.campo, jan, ms);
          if (!Array.isArray(pts) || pts.length < 2) { out.motivo = 'sem-serie'; return out; }
          for (i = 0; i < pts.length; i++) {
            e = pts[i];
            if (!e || !num(e.ms) || !num(e.v) || !num(e.min) || !num(e.max)) { out.motivo = 'sem-serie'; return out; }
            vals.push(e.min, e.max, e.v);
          }
          p.series.push({ campo: s.campo, n: s.n, pts: pts, agora: pts[pts.length - 1], cor: COR[gi % 3], corNome: COR_NOME[gi % 3] }); gi++;
        }
        if (pn.ref) p.ref = refDe(pn.ref);
        e = escala(pn, vals, p.ref, Math.max(2, Math.min(4, Math.floor(((altura || 150) - 38 - (M.paineis.length - 1) * 20) / M.paineis.length / 26))));
        p.lo = e.lo; p.hi = e.hi; p.passo = e.passo;
        out.paineis.push(p);
      }
      out.t0 = out.paineis[0].series[0].pts[0].ms; out.t1 = out.paineis[0].series[0].pts[out.paineis[0].series[0].pts.length - 1].ms;
      if (!(out.t1 > out.t0)) { out.motivo = 'sem-serie'; return out; }
      out.ok = true;
      return out;
    } catch (err) { out.ok = false; out.motivo = 'erro'; return out; }
  }

  // marcas do eixo do tempo, em horas redondas do barco: 150 s a cada 30 s, 1 D a cada 4 h, 7 D por dia, 30 D a cada 5 dias, 1 A por mês
  function marcas(t0, t1, jan) {
    var out = [], passo, t, d, L0 = loc(t0), L1 = loc(t1), y, m;
    if (jan === '1A') {
      d = new Date(L0); y = d.getUTCFullYear(); m = d.getUTCMonth() + 1;
      for (t = Date.UTC(y, m, 1); t < L1; m++, t = Date.UTC(y, m, 1)) out.push({ ms: t - (loc(t0) - t0), l: MES[new Date(t).getUTCMonth()] + '/' + String(new Date(t).getUTCFullYear()).slice(-2) });
      return out;
    }
    passo = jan === '150S' ? 30000 : jan === '1D' ? 4 * 3600000 : jan === '7D' ? 86400000 : 5 * 86400000;
    for (t = Math.ceil(L0 / passo) * passo; t < L1; t += passo) out.push({ ms: t - (L0 - t0), l: jan === '150S' ? hhmm(t - (L0 - t0), true) : jan === '1D' ? hhmm(t - (L0 - t0)) : ddmm(t - (L0 - t0)) });
    return out;
  }
  function horaDe(ms, jan) { return jan === '150S' ? hhmm(ms, true) : jan === '1D' ? ddmm(ms) + ' ' + hhmm(ms) : ddmm(ms) + (jan === '1A' ? '' : ' ' + hhmm(ms)); }

  var X0 = 40;   // a margem da esquerda (os números do eixo)
  var Comp = null;
  function componente() {
    if (Comp) return Comp;
    var React = window.React, h = React.createElement;
    Comp = function CapitaoGraficoC(props) {
      var a = React.useState(null), cur = a[0], setCur = a[1];
      var b = React.useState(0), tique = b[0], setTique = b[1];
      var c = React.useState(num(props.largura) ? props.largura : 480), larg = c[0], setLarg = c[1];
      var ref = React.useRef(null), svgRef = React.useRef(null), fim = React.useRef(0);
      React.useEffect(function () {
        var on = function () { if (!document.hidden) setTique(function (t) { return t + 1; }); };
        window.addEventListener('capitao-telemetria', on);
        return function () { window.removeEventListener('capitao-telemetria', on); clearTimeout(fim.current); };
      }, []);
      React.useEffect(function () {
        var el = ref.current, mede = function () { var w = el ? el.clientWidth : 0; if (w > 0) { var n = Math.max(240, Math.round(w / 4) * 4); setLarg(function (v) { return v === n ? v : n; }); } };
        mede();
        if (window.ResizeObserver && el) { var ro = new ResizeObserver(mede); ro.observe(el); return function () { ro.disconnect(); }; }
        window.addEventListener('resize', mede); return function () { window.removeEventListener('resize', mede); };
      }, []);
      var met = METRICAS[props.metrica] ? props.metrica : 'baterias', jan = janelaValida(met, props.janela), W = larg, H = props.altura || 150, fs = props.compacto || W < 420 ? 9.5 : 10.5;
      var d = React.useMemo(function () { return dados(met, jan, undefined, H); }, [met, jan, tique, H]);   // `tique` força a releitura a cada segundo (a série anda com o replay)
      var raiz = { ref: ref, 'data-capitao-grafico': met, 'data-janela': jan, style: { position: 'relative', width: '100%', minWidth: 0, display: 'flex', flexDirection: 'column', gap: 6 } };
      if (!d.ok) return h('div', raiz, vazio(h, d, met, jan, H));
      var n = d.paineis.length, YT = 18, YB = H - 20, folga = 20, ph = (YB - YT - (n - 1) * folga) / n, X1 = W - 8, kids = [], k, j, i, pn, pts, serie0;
      var xdoT = function (t) { return X0 + (t - d.t0) / (d.t1 - d.t0) * (X1 - X0); };
      var ink4 = { fill: 'var(--cap-ink4, #7985a6)' };
      var mk = marcas(d.t0, d.t1, jan), ultX = -1e9, folgaMarca = jan === '150S' ? 58 : jan === '1D' ? 44 : 38;
      for (k = 0; k < n; k++) {
        pn = d.paineis[k];
        var topo = YT + k * (ph + folga), base = topo + ph, yv = (function (p, t0, hh) { return function (v) { return t0 + hh - (v - p.lo) / (p.hi - p.lo) * hh; }; })(pn, topo, ph);
        kids.push(h('text', { key: 'u' + k, x: X0 - 6, y: topo - 7, fontSize: fs, fontWeight: 700, textAnchor: 'end', style: ink4 }, unDe(pn.series[0].campo)));
        for (var v = pn.lo; v <= pn.hi + pn.passo * 1e-6; v += pn.passo) {
          var yy = yv(v);
          kids.push(h('line', { key: 'g' + k + '_' + v.toFixed(3), x1: X0, x2: X1, y1: yy, y2: yy, strokeWidth: 1, style: { stroke: 'var(--cap-line, #1a2240)' } }));
          kids.push(h('text', { key: 'e' + k + '_' + v.toFixed(3), x: X0 - 6, y: yy + 3.5, fontSize: fs, textAnchor: 'end', style: ink4 }, (pn.passo >= 1 ? String(Math.round(v)) : v.toFixed(pn.passo === 0.25 || pn.passo < 0.1 ? 2 : 1).replace('.', ',')).replace(/\B(?=(\d{3})+(?!\d))/g, '.')));
        }
        if (pn.ref && pn.ref.v >= pn.lo && pn.ref.v <= pn.hi) {
          var yr = yv(pn.ref.v);
          kids.push(h('line', { key: 'rf' + k, x1: X0, x2: X1, y1: yr, y2: yr, strokeWidth: 1.2, strokeDasharray: '4 3', style: { stroke: 'var(--cap-warn, #f0a63a)' } }));
          kids.push(h('text', { key: 'rt' + k, x: X1 - 2, y: yr - 3, fontSize: fs - 0.5, fontWeight: 700, textAnchor: 'end', style: { fill: 'var(--cap-warn, #f0a63a)' } }, pn.ref.n));
        }
        // faixa mín/máx do balde (a série de cima do painel): o que a média esconde
        serie0 = pn.series[0];
        if (jan !== '150S' && serie0.pts.some(function (e) { return e.max - e.min > (pn.hi - pn.lo) * 0.004; })) {
          var cima = serie0.pts.map(function (e, q) { return (q ? 'L' : 'M') + xdoT(e.ms).toFixed(1) + ',' + yv(e.max).toFixed(1); }).join('');
          var baixo = serie0.pts.slice().reverse().map(function (e) { return 'L' + xdoT(e.ms).toFixed(1) + ',' + yv(e.min).toFixed(1); }).join('');
          kids.push(h('path', { key: 'b' + k, d: cima + baixo + 'Z', strokeWidth: 0, style: { fill: serie0.cor, opacity: 0.16 } }));
        }
        for (j = pn.series.length - 1; j >= 0; j--) {
          var s = pn.series[j], dd = s.pts.map(function (e, q) { return (q ? 'L' : 'M') + xdoT(e.ms).toFixed(1) + ',' + yv(e.v).toFixed(1); }).join('');
          kids.push(h('path', { key: 'l' + k + '_' + j, d: dd, fill: 'none', strokeWidth: 2, strokeLinejoin: 'round', strokeLinecap: 'round', style: { stroke: s.cor } }));
        }
        for (j = 0; j < pn.series.length; j++) {   // o ponto «agora»: o último, que é o quadro do replay
          var sa = pn.series[j], ua = sa.agora;
          kids.push(h('circle', { key: 'a' + k + '_' + j, cx: xdoT(ua.ms), cy: yv(ua.v), r: 3.6, strokeWidth: 1.5, 'data-agora': valTxt(sa.campo, ua.v, false), 'data-campo': sa.campo, style: { fill: sa.cor, stroke: 'var(--cap-card, #0d1329)' } }));
        }
      }
      for (i = 0; i < mk.length; i++) {
        var mx = xdoT(mk[i].ms);
        if (mx < X0 + 12 || mx > X1 - 12 || mx - ultX < folgaMarca) continue;
        ultX = mx;
        kids.push(h('line', { key: 'mt' + i, x1: mx, x2: mx, y1: YB, y2: YB + 4, strokeWidth: 1, style: { stroke: 'var(--cap-line2, #27315a)' } }));
        kids.push(h('text', { key: 'mx' + i, x: mx, y: H - 4, fontSize: fs, textAnchor: 'middle', style: ink4 }, mk[i].l));
      }
      // cursor: o ponto mais próximo no tempo, em todas as séries
      var sel = null;
      if (cur !== null && cur >= 0) {
        pts = d.paineis[0].series[0].pts; sel = Math.max(0, Math.min(pts.length - 1, cur));
        var xc = xdoT(pts[sel].ms);
        kids.push(h('line', { key: 'cl', x1: xc, x2: xc, y1: YT - 4, y2: YB, strokeWidth: 1, style: { stroke: 'var(--cap-ink2, #b1bdd6)' } }));
        d.paineis.forEach(function (pp, kk) {
          var tp = YT + kk * (ph + folga);
          pp.series.forEach(function (ss, jj) { kids.push(h('circle', { key: 'cp' + kk + '_' + jj, cx: xc, cy: tp + ph - (ss.pts[sel].v - pp.lo) / (pp.hi - pp.lo) * ph, r: 3.4, style: { fill: ss.cor } })); });
        });
      }
      var aoPonteiro = function (e) {
        var el = svgRef.current; if (!el) return;
        var r = el.getBoundingClientRect(); if (!r.width) return;
        var x = (e.clientX - r.left) * W / r.width, p0 = d.paineis[0].series[0].pts, t = d.t0 + (x - X0) / (X1 - X0) * (d.t1 - d.t0), best = 0, bd = Infinity, q;
        if (x < X0 - 6 || x > X1 + 6) { setCur(null); return; }
        for (q = 0; q < p0.length; q++) { var dist = Math.abs(p0[q].ms - t); if (dist < bd) { bd = dist; best = q; } }
        setCur(best);
      };
      var caixa = null;
      if (sel !== null) {
        var linhas = [h('b', { key: 'h' }, horaDe(d.paineis[0].series[0].pts[sel].ms, jan))], px = xdoT(d.paineis[0].series[0].pts[sel].ms) / W * 100;
        d.paineis.forEach(function (pp) { pp.series.forEach(function (ss) { linhas.push(h('span', { key: ss.campo, style: { display: 'block' } }, h('span', { style: { color: ss.cor } }, '● '), ss.n + ': ', h('b', null, valTxt(ss.campo, ss.pts[sel].v)))); }); });
        caixa = h('div', { 'data-cursor': 'caixa', style: { position: 'absolute', top: 2, left: px > 55 ? 'auto' : px + '%', right: px > 55 ? (100 - px) + '%' : 'auto', marginLeft: px > 55 ? 0 : 10, marginRight: px > 55 ? 10 : 0, pointerEvents: 'none', zIndex: 3, padding: '5px 9px', borderRadius: 8, fontSize: 11, lineHeight: 1.45, whiteSpace: 'nowrap', background: 'var(--cap-card, #0d1329)', border: '1px solid var(--cap-line2, #27315a)', boxShadow: '0 4px 14px rgba(0,0,0,0.3)', color: 'var(--cap-ink, #eaf1ff)' } }, linhas);
      }
      // legenda curta: a cor de cada série com o valor de agora, o intervalo da janela e o que a linha significa
      var todas = []; d.paineis.forEach(function (pp) { pp.series.forEach(function (ss) { todas.push(ss); }); });
      var s0 = todas[0], mn = Math.min.apply(null, s0.pts.map(function (e) { return e.min; })), mxv = Math.max.apply(null, s0.pts.map(function (e) { return e.max; }));
      var textoAria = M_rot(met) + ', ' + JANELAS[jan].nome + ': ' + todas.map(function (ss) { return ss.n + ' ' + valTxt(ss.campo, ss.agora.v); }).join(', ');
      var leg = todas.map(function (ss, q) { return h('span', { key: 'lg' + q, style: { display: 'inline-flex', alignItems: 'baseline', gap: 4, whiteSpace: 'nowrap' } }, h('span', { 'aria-hidden': 'true', style: { color: ss.cor } }, '●'), ss.n + ' ', h('b', { style: { color: 'var(--cap-ink2, #b1bdd6)' } }, valTxt(ss.campo, ss.agora.v))); });
      var minmax = 'mín ' + valTxt(s0.campo, mn, false) + ' · máx ' + valTxt(s0.campo, mxv) + (todas.length > 1 ? ' (' + s0.n + ')' : '');
      var titulo = textoAria + ' · ' + minmax + ' · ' + JANELAS[jan].media + ' · ' + todas.map(function (ss) { return ss.corNome + ' = ' + ss.n; }).join('; ');
      return h('div', raiz,
        h('svg', { ref: svgRef, viewBox: '0 0 ' + W + ' ' + H, width: '100%', role: 'img', 'aria-label': textoAria, onPointerMove: aoPonteiro, onPointerDown: aoPonteiro, onPointerLeave: function () { setCur(null); },
          onPointerUp: function (e) { if (e.pointerType && e.pointerType !== 'mouse') { clearTimeout(fim.current); fim.current = setTimeout(function () { setCur(null); }, 2500); } },
          style: { display: 'block', touchAction: 'pan-y', maxWidth: '100%', height: 'auto', overflow: 'visible' } }, kids),
        caixa,
        h('span', { title: titulo, 'data-legenda': 'curta', style: { display: 'flex', flexWrap: 'wrap', columnGap: 12, rowGap: 1, fontSize: 11, lineHeight: 1.4, color: 'var(--cap-ink3, #97a3c0)' } }, leg, h('span', { key: 'mm', style: { whiteSpace: 'nowrap' } }, minmax)));
    };
    return Comp;
  }
  function M_rot(met) { return METRICAS[met] ? METRICAS[met].rot : ''; }
  // sem série (modo real, ou o replay inerte): SEM DADOS e a leitura de agora; a janela que a métrica não tem (as do laço de 150 s nas longas) é só uma nota
  function vazio(h, d, met, jan, H) {
    var I = null, txt = '', real = D().simulacao !== true;
    try { I = A() && A().instante ? A().instante() : null; } catch (e) {}
    if (d.motivo === 'so150') txt = M_rot(met) + ' só tem a janela de 150 s: nas outras a volta se repete e a linha sairia reta.';
    else if (I && I.q) { var c = METRICAS[met] && METRICAS[met].paineis[0].series[0]; txt = c ? 'Leitura de agora: ' + c.n + ' ' + (valTxt(c.campo, I.q[c.campo]) || '') : ''; }
    return h('div', { 'data-vazio': d.motivo, style: { height: H, boxSizing: 'border-box', border: '1px dashed var(--cap-dash, #34406a)', borderRadius: 14, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 6, padding: '0 24px', textAlign: 'center' } },
      h('span', { style: { fontSize: 11.5, letterSpacing: '0.16em', fontWeight: 800, color: 'var(--cap-warn, #f0a63a)' } }, real ? 'SEM DADOS' : 'SÉRIE INDISPONÍVEL AGORA'),
      h('span', { style: { fontSize: 12, color: 'var(--cap-ink2, #b1bdd6)', lineHeight: 1.45 } }, d.motivo === 'so150' ? txt : (real ? 'Série não gravada neste aparelho. ' : 'A série volta no próximo segundo. ') + txt));
  }

  window.CapitaoGrafico = {
    JANELAS: JANELAS, METRICAS: METRICAS, ORDEM: ORDEM, COR: COR,
    elemento: function (p) { try { return window.React.createElement(componente(), p || {}); } catch (e) { return null; } },
    dados: dados, janelaValida: janelaValida, so150: so150, rotulo: rotulo, marcas: marcas
  };
})();
