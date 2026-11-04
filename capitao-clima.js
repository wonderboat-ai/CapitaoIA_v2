/* Capitão IA — hora local, previsão do dia e maré no cabeçalho.
   <capitao-hora-clima tamanho="13"> → 10:12 · ☀ 29°/17° · ≋ NE 12/19 KT · 〰 +0,4m
   - Hora: relógio do aparelho no fuso do barco (capitao-dados.js › embarcacao.fuso), atualiza sozinha.
   - Clima: máxima e mínima de hoje e vento (máximo, rajada máxima e direção dominante, em nós) do modelo ECMWF (o padrão do
     windy.com), via Open-Meteo — grátis, sem chave. Rajada que o ECMWF não trouxer vem do melhor modelo do Open-Meteo (dito no
     title). É previsão do mundo real, nunca leitura de bordo: o app não tem limite de vento para dizer se é seguro sair.
   - Maré: altura agora em relação ao nível médio do mar (Open-Meteo Marine, sea_level_height_msl), interpolada hora a hora.
     NÃO é a tábua oficial da Marinha (DHN): serve de referência rápida, não para passar em canal raso.
   Posição: a de referência do capitao-dados.js (centro de Balneário Camboriú — Open-Meteo Geocoding), não o GPS do barco.
   Sem internet: usa a última leitura salva (clima e vento do mesmo dia, com a hora da leitura; maré enquanto a série de 48 h
   cobrir a hora). Sem dado → "—". Tocar no clima, no vento ou na maré abre o windy.com na posição de referência (nova aba).
   Celular (tamanho < 13): duas linhas — hora e maré em cima, temperatura e vento embaixo; numa linha só não cabe com o vento. */
(function () {
  if (window.CapitaoClima) return;
  var D = window.CapitaoDados || {};
  var ref = D.posicaoRef || null;
  var POS = ref && typeof ref.lat === 'number' && typeof ref.lon === 'number' ? { lat: ref.lat, lon: ref.lon } : null;
  // A grade do modelo de mar (≈ 8 km) pode tratar a costa como terra: tenta a referência, a enseada e o mar aberto, nessa ordem.
  var MAR = Array.isArray(D.mar) && D.mar.length ? D.mar : (POS ? [[POS.lat, POS.lon]] : []);
  var TZ = (D.embarcacao && D.embarcacao.fuso) || 'America/Sao_Paulo';
  var K = { clima: 'capitao.clima.v1', mare: 'capitao.mare.v1' };
  var WINDY = POS ? 'https://www.windy.com/' + POS.lat.toFixed(3) + '/' + POS.lon.toFixed(3) + '?' + POS.lat.toFixed(3) + ',' + POS.lon.toFixed(3) + ',11' : 'https://www.windy.com/';
  var H_CLIMA = 3600e3, H_MARE = 3 * 3600e3, H_ERRO = 5 * 60e3;

  function ler(k) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : null; } catch (e) { return null; } }
  function grava(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  var fmtHora = null, fmtDia = null;
  try {
    fmtHora = new Intl.DateTimeFormat('pt-BR', { timeZone: TZ, hour: '2-digit', minute: '2-digit', hour12: false });
    fmtDia = new Intl.DateTimeFormat('en-CA', { timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit' });
  } catch (e) {}
  function hora() { var d = new Date(); return fmtHora ? fmtHora.format(d) : ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
  function hoje() { var d = new Date(); return fmtDia ? fmtDia.format(d) : d.toISOString().slice(0, 10); } // AAAA-MM-DD no fuso do barco

  var E = { clima: ler(K.clima), mare: ler(K.mare), busca: {}, falhou: {} };
  var ouvintes = [];
  function avisa() { ouvintes.forEach(function (f) { try { f(); } catch (e) {} }); }

  function pega(url) {
    return fetch(url, { cache: 'no-store' }).then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
  }
  function buscaClima() {
    if (E.busca.clima || !POS) return;
    var base = 'https://api.open-meteo.com/v1/forecast?latitude=' + POS.lat + '&longitude=' + POS.lon +
      '&daily=temperature_2m_max,temperature_2m_min,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant&wind_speed_unit=kn&timezone=' + encodeURIComponent(TZ) + '&forecast_days=1';
    var num = function (d, k) { var v = d && d[k] && d[k][0]; return typeof v === 'number' && isFinite(v) ? v : null; };
    var ecmwf = true;
    E.busca.clima = pega(base + '&models=ecmwf_ifs025').catch(function () { ecmwf = false; return pega(base); }) // modelo indisponível → o melhor disponível
      .then(function (j) {
        var d = j && j.daily, mx = num(d, 'temperature_2m_max'), mn = num(d, 'temperature_2m_min');
        if (mx == null || mn == null) throw new Error('sem dado');
        var c = { em: Date.now(), dia: (d.time && d.time[0]) || hoje(), max: mx, min: mn, vento: num(d, 'wind_speed_10m_max'), raj: num(d, 'wind_gusts_10m_max'), dir: num(d, 'wind_direction_10m_dominant'), modelo: ecmwf ? 'ECMWF' : 'Open-Meteo' };
        // Rajada fora do ECMWF: completa com o melhor modelo (marcado em rajModelo), sem perder a temperatura e o vento já lidos.
        return (c.raj == null && ecmwf ? pega(base).then(function (k) { var g = num(k && k.daily, 'wind_gusts_10m_max'); if (g != null) { c.raj = g; c.rajModelo = 'Open-Meteo'; } }, function () {}) : Promise.resolve())
          .then(function () { E.clima = c; grava(K.clima, E.clima); E.falhou.clima = 0; avisa(); });
      }).catch(function () { E.falhou.clima = Date.now(); })
      .then(function () { E.busca.clima = null; });
  }
  function buscaMare() {
    if (E.busca.mare || !MAR.length) return;
    var url = 'https://marine-api.open-meteo.com/v1/marine?latitude=' + MAR.map(function (p) { return p[0]; }).join(',') + '&longitude=' + MAR.map(function (p) { return p[1]; }).join(',') + '&hourly=sea_level_height_msl&timeformat=unixtime&timezone=GMT&past_days=1&forecast_days=2';
    E.busca.mare = pega(url).then(function (j) {
      var locais = Array.isArray(j) ? j : [j], serie = null;
      for (var i = 0; i < locais.length && !serie; i++) {
        var h = locais[i] && locais[i].hourly, t = h && h.time, v = h && h.sea_level_height_msl, s = [];
        if (!t || !v) continue;
        for (var k = 0; k < t.length; k++) if (typeof v[k] === 'number' && typeof t[k] === 'number') s.push([t[k] * 1000, v[k]]);
        if (s.length > 12) serie = s;
      }
      if (!serie) throw new Error('sem dado');
      E.mare = { em: Date.now(), serie: serie };
      grava(K.mare, E.mare); E.falhou.mare = 0; avisa();
    }).catch(function () { E.falhou.mare = Date.now(); })
      .then(function () { E.busca.mare = null; });
  }
  function atualiza() {
    if (window.navigator && navigator.onLine === false) return;
    var c = E.clima, m = E.mare, agora = Date.now();
    // leitura salva antes do vento (sem a chave vento): busca de novo já, sem esperar a hora
    if ((!c || c.dia !== hoje() || agora - c.em > H_CLIMA || c.vento === undefined) && !(E.falhou.clima && agora - E.falhou.clima < H_ERRO)) buscaClima();
    if ((!m || agora - m.em > H_MARE) && !(E.falhou.mare && agora - E.falhou.mare < H_ERRO)) buscaMare();
  }

  function clima() { var c = E.clima; return c && c.dia === hoje() ? c : null; }
  // Altura agora: interpola entre as duas horas vizinhas da série.
  function mareAgora() {
    var s = E.mare && E.mare.serie, t = Date.now();
    if (!s || !s.length) return null;
    for (var i = 1; i < s.length; i++) {
      if (s[i][0] >= t && s[i - 1][0] <= t) {
        var a = s[i - 1], b = s[i], f = (t - a[0]) / Math.max(1, b[0] - a[0]);
        return a[1] + (b[1] - a[1]) * f;
      }
    }
    return null;
  }
  // Próximas horas (para a resposta de maré do chat): [{ ms, m }] a partir de agora, de hora em hora.
  function mareProximas(horas) {
    var s = E.mare && E.mare.serie, t = Date.now(), out = [];
    if (!s) return out;
    for (var i = 0; i < s.length && out.length < (horas || 6) + 1; i++) if (s[i][0] >= t - 3600e3) out.push({ ms: s[i][0], m: s[i][1] });
    return out;
  }
  function grau(x) { return Math.round(x) + '°'; }
  var RUMOS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']; // notação dos boletins da Marinha (Meteoromarinha) e do windy.com
  function rumo(g) { return typeof g === 'number' && isFinite(g) ? RUMOS[Math.round((((g % 360) + 360) % 360) / 45) % 8] : ''; } // de onde vem (convenção do vento)
  function nos(x) { return typeof x === 'number' && isFinite(x) ? String(Math.round(x)) : '—'; }
  function horaDe(ms) { var d = new Date(ms); return fmtHora ? fmtHora.format(d) : ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
  // Fonte da leitura, com a hora (sem rede, a hora diz de quando é a cópia salva). Leitura sem o modelo gravado: só "Open-Meteo".
  function fonte(c) {
    var m = c.modelo === 'ECMWF' ? 'ECMWF via Open-Meteo' : c.modelo ? 'melhor modelo do Open-Meteo (o ECMWF não respondeu)' : 'Open-Meteo';
    return m + (typeof c.em === 'number' ? ', lida às ' + horaDe(c.em) : '');
  }
  function metro(x) {
    var r = Math.round(x * 10) / 10; // −0,04 → "0,0m", nunca "-0,0m"
    return (r > 0 ? '+' : r < 0 ? '−' : '') + Math.abs(r).toFixed(1).replace('.', ',') + 'm';
  }

  // Um relógio para todos os elementos da página: acorda a cada virada de minuto.
  var tique = 0;
  function agenda() {
    clearTimeout(tique);
    if (!ouvintes.length) return;
    var ms = 60000 - (Date.now() % 60000) + 50;
    tique = setTimeout(function () { avisa(); atualiza(); agenda(); }, ms);
  }
  document.addEventListener('visibilitychange', function () { if (!document.hidden) { avisa(); atualiza(); agenda(); } });
  window.addEventListener('online', atualiza);
  window.addEventListener('storage', function (e) {
    if (!e || e.key === K.clima || e.key === K.mare) { E.clima = ler(K.clima); E.mare = ler(K.mare); avisa(); }
  });

  window.CapitaoClima = { POS: POS, TZ: TZ, WINDY: WINDY, hora: hora, horaDe: horaDe, clima: clima, rumo: rumo, fonte: fonte, mareAgora: mareAgora, mareProximas: mareProximas, metro: metro, atualiza: atualiza, fonteRef: ref ? ref.nome + ' — ' + ref.fonte : 'SEM DADOS' };

  if (!window.customElements || customElements.get('capitao-hora-clima')) return;
  var NS = 'http://www.w3.org/2000/svg';
  function icone(d, cor) {
    var s = document.createElementNS(NS, 'svg'); s.setAttribute('width', '13'); s.setAttribute('height', '13'); s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('fill', 'none'); s.setAttribute('aria-hidden', 'true');
    s.style.cssText = 'flex-shrink:0;display:block;';
    var p = document.createElementNS(NS, 'path'); p.setAttribute('d', d); p.setAttribute('stroke-width', '2'); p.setAttribute('stroke-linecap', 'round'); p.setAttribute('stroke-linejoin', 'round');
    p.style.stroke = cor; s.appendChild(p); return s;
  }
  var SOL = 'M12 3v2 M12 19v2 M3 12h2 M19 12h2 M5.6 5.6l1.4 1.4 M17 17l1.4 1.4 M5.6 18.4L7 17 M17 7l1.4-1.4 M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z';
  var VENTO = 'M2 9h11.5a2.5 2.5 0 1 0-2.5-2.5 M2 13h16.5a2.5 2.5 0 1 1-2.5 2.5 M2 17h7';
  var ONDA = 'M2 9c2.5-2.5 5-2.5 7.5 0s5 2.5 7.5 0 3.5-1.5 5-1 M2 16c2.5-2.5 5-2.5 7.5 0s5 2.5 7.5 0 3.5-1.5 5-1';
  customElements.define('capitao-hora-clima', class extends HTMLElement {
    connectedCallback() {
      if (!this._h) this.build();
      this._on = this.render.bind(this);
      ouvintes.push(this._on);
      this.render(); atualiza(); agenda();
    }
    disconnectedCallback() { ouvintes = ouvintes.filter(function (f) { return f !== this._on; }, this); if (!ouvintes.length) clearTimeout(tique); }
    build() {
      var d = document, tam = Math.max(10, parseFloat(this.getAttribute('tamanho') || '13') || 13), peq = Math.max(9.5, tam - 2), cel = tam < 13;
      // Celular: grade de duas linhas (hora e maré · temperatura e vento), alvos de 20 px com 3 px entre as linhas — cabe nos 43 px
      // do cabeçalho de 44 (1 px é a borda).
      this.style.cssText = cel ? 'display:inline-grid;grid-template-columns:auto auto;align-items:center;justify-items:start;column-gap:8px;row-gap:3px;flex-shrink:0;white-space:nowrap;line-height:1.1;'
        : 'display:inline-flex;align-items:center;gap:12px;flex-shrink:0;white-space:nowrap;';
      var h = d.createElement('b'); h.style.cssText = 'font-variant-numeric:tabular-nums;font-size:' + tam + 'px;letter-spacing:0.04em;font-weight:700;color:var(--cap-ink, #eaf1ff);';
      var link = 'display:inline-flex;align-items:center;gap:4px;text-decoration:none;font-variant-numeric:tabular-nums;font-size:' + peq + 'px;letter-spacing:0.02em;font-weight:700;border-radius:6px;min-height:' + (cel ? 20 : 24) + 'px;';
      var c = d.createElement('a'); c.href = WINDY; c.target = '_blank'; c.rel = 'noopener'; c.style.cssText = link + 'color:var(--cap-ink2, #b1bdd6);';
      var cMax = d.createElement('span'), cBar = d.createElement('span'), cMin = d.createElement('span');
      cMax.style.color = 'var(--cap-ink, #eaf1ff)'; cBar.textContent = '/'; cBar.style.cssText = 'color:var(--cap-ink4, #7985a6);font-weight:500;'; cMin.style.color = 'var(--cap-ink3, #97a3c0)';
      c.appendChild(icone(SOL, 'var(--cap-warn, #f0a63a)')); c.appendChild(cMax); c.appendChild(cBar); c.appendChild(cMin);
      // Vento previsto: direção dominante, máximo e rajada máxima do dia, em nós; o toque abre o windy.com.
      var w = d.createElement('a'); w.href = WINDY; w.target = '_blank'; w.rel = 'noopener'; w.style.cssText = link + 'color:var(--cap-ink2, #b1bdd6);';
      var rotulo = 'font-size:' + Math.max(8, peq - 3) + 'px;font-weight:700;letter-spacing:0.08em;color:var(--cap-ink4, #7985a6);';
      var wD = d.createElement('span'), wV = d.createElement('span'), wBar = d.createElement('span'), wR = d.createElement('span'), wU = d.createElement('span');
      wD.style.cssText = rotulo; wV.style.color = 'var(--cap-ink, #eaf1ff)'; wBar.textContent = '/'; wBar.style.cssText = 'color:var(--cap-ink4, #7985a6);font-weight:500;';
      wR.style.color = 'var(--cap-ink3, #97a3c0)'; wU.textContent = 'KT'; wU.style.cssText = rotulo;
      w.appendChild(icone(VENTO, 'var(--cap-accent, #00a1fe)')); w.appendChild(wD); w.appendChild(wV); w.appendChild(wBar); w.appendChild(wR); w.appendChild(wU);
      var m = d.createElement('a'); m.href = WINDY; m.target = '_blank'; m.rel = 'noopener'; m.style.cssText = link + 'color:var(--cap-tele, #00f4fd);';
      var mV = d.createElement('span');
      m.appendChild(icone(ONDA, 'var(--cap-tele, #00f4fd)')); m.appendChild(mV);
      if (cel) { this.appendChild(h); this.appendChild(m); this.appendChild(c); this.appendChild(w); }
      else { this.appendChild(h); this.appendChild(c); this.appendChild(w); this.appendChild(m); }
      this._h = h; this._c = c; this._cMax = cMax; this._cMin = cMin; this._m = m; this._mV = mV;
      this._w = w; this._wD = wD; this._wV = wV; this._wR = wR;
    }
    render() {
      var t = hora(); if (this._h.textContent !== t) this._h.textContent = t;
      this._h.setAttribute('aria-label', 'Hora local ' + t);
      var c = clima();
      this._cMax.textContent = c ? grau(c.max) : '—'; this._cMin.textContent = c ? grau(c.min) : '—';
      var tc = c ? 'Previsão de hoje em Balneário Camboriú · máx ' + grau(c.max) + ' · mín ' + grau(c.min) + ' (' + fonte(c) + ') — abrir o windy.com' : 'Previsão de hoje: SEM DADOS (sem internet ou sem posição) — abrir o windy.com';
      this._c.title = tc; this._c.setAttribute('aria-label', tc);
      var temV = c && typeof c.vento === 'number', dr = temV ? rumo(c.dir) : '', temR = temV && typeof c.raj === 'number';
      this._wD.textContent = dr; this._wD.style.display = dr ? '' : 'none';
      this._wV.textContent = temV ? nos(c.vento) : '—'; this._wR.textContent = temR ? nos(c.raj) : '—';
      var tw = temV ? 'Vento previsto hoje em Balneário Camboriú: até ' + nos(c.vento) + ' nós' + (dr ? ' de ' + dr : '') +
        (temR ? ', rajadas até ' + nos(c.raj) + ' nós' + (c.rajModelo ? ' (rajada: melhor modelo do Open-Meteo — o ECMWF não trouxe)' : '') : ', rajadas: SEM DADOS') +
        ' (' + fonte(c) + ') — abrir o windy.com' : 'Vento previsto: SEM DADOS' + (c ? ' (a leitura de hoje não traz o vento)' : ' (sem internet ou sem posição)') + ' — abrir o windy.com';
      this._w.title = tw; this._w.setAttribute('aria-label', tw);
      var x = mareAgora();
      this._mV.textContent = x == null ? '—' : metro(x);
      var tm = x == null ? 'Maré agora: SEM DADOS — abrir o windy.com' : 'Maré agora ' + metro(x) + ' em relação ao nível médio do mar (modelo Open-Meteo, não é a tábua da Marinha) — abrir o windy.com';
      this._m.title = tm; this._m.setAttribute('aria-label', tm);
    }
  });
})();
