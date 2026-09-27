/* Capitão IA — núcleo de voz (HUD do cérebro da embarcação).
   Escuta os eventos 'capitao-voz' que o capitao-brain.js emite e mostra, por cima da tela, o núcleo da IA:
   anéis graduados girando devagar, espectro radial discreto que acompanha a voz e "IA" no centro.
   Cores da marca: ESCUTA ciano (#00F4FD) · PROCESSANDO violeta (#A22BFD) · RESPOSTA azul (#00A1FE).
   - ESCUTA (pergunta): o espectro sobe a cada trecho reconhecido; mostra a transcrição.
   - PROCESSANDO: anéis aceleram enquanto a resposta é montada (esperando a IA na nuvem, fica até a resposta ser falada).
   - RESPOSTA: o espectro acompanha a fala; mostra a frase dita.
   Tocar no núcleo: escuta → envia agora; resposta → interrompe e volta a ouvir. ENCERRAR (ou Esc) desliga.
   SOS sempre no canto. */
(function () {
  if (window.CapitaoVoz) return;
  var d = document, raiz = null, el = {}, estado = 'livre', some = 0, raf = 0, energia = 0, t0 = 0, barras = [];
  var reduz = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  var N = 48, R0 = 84; // barras do espectro e raio onde começam
  var COR = {
    ouvindo: { g: '0,244,253', rot: 'ESCUTA ATIVA', modo: 'MODO · ESCUTA', dica: 'TOQUE NO NÚCLEO PARA ENVIAR' },
    pensando: { g: '162,43,253', rot: 'PROCESSANDO', modo: 'MODO · ANÁLISE', dica: '' },
    falando: { g: '0,161,254', rot: 'CAPITÃO IA', modo: 'MODO · RESPOSTA', dica: 'TOQUE NO NÚCLEO PARA INTERROMPER' }
  };
  var MONO = 'ui-monospace,"SF Mono",Menlo,Consolas,monospace';
  var FONTE = '"Nimbus Sans","Helvetica Neue",Helvetica,Arial,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif';

  var CSS = [
    '.cpz{position:fixed;inset:0;z-index:70;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:max(20px,env(safe-area-inset-top)) 18px max(22px,env(safe-area-inset-bottom));box-sizing:border-box;font-family:' + FONTE + ';color:#eaf6ff;opacity:0;pointer-events:none;transition:opacity .25s ease;-webkit-tap-highlight-color:transparent;--cpz-g:0,244,253}',
    '.cpz.on{opacity:1;pointer-events:auto}',
    '.cpz{overflow-y:auto;justify-content:safe center}',
    '@media (max-height:720px){.cpz-hud,.cpz-canto{display:none}.cpz{gap:10px}}',
    '.cpz-fundo{position:absolute;inset:0;background:radial-gradient(ellipse 55% 40% at 50% 40%,rgba(var(--cpz-g),0.10) 0%,rgba(var(--cpz-g),0) 70%),rgba(5,8,22,0.95);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px)}',
    '.cpz-hud{position:absolute;font:600 10px/1.55 ' + MONO + ';letter-spacing:0.12em;color:rgba(var(--cpz-g),0.85);pointer-events:none;white-space:nowrap}',
    '.cpz-hud b{color:#fff;font-weight:700}',
    '.cpz-tl{top:max(66px,calc(env(safe-area-inset-top) + 58px));left:18px}.cpz-tr{top:max(66px,calc(env(safe-area-inset-top) + 58px));right:18px;text-align:right}',
    '.cpz-palco{position:relative;width:min(64vmin,36vh,300px);height:min(64vmin,36vh,300px);flex-shrink:0}',
    '.cpz-palco svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}',
    '.cpz-canto{position:absolute;width:22px;height:22px;border:solid rgba(var(--cpz-g),0.7);pointer-events:none}',
    '.cpz-c1{top:-6px;left:-6px;border-width:2px 0 0 2px}.cpz-c2{top:-6px;right:-6px;border-width:2px 2px 0 0}.cpz-c3{bottom:-6px;left:-6px;border-width:0 0 2px 2px}.cpz-c4{bottom:-6px;right:-6px;border-width:0 2px 2px 0}',
    '.cpz-gira{transform-box:view-box;transform-origin:150px 150px}',
    '.cpz-r1{animation:cpzRoda 180s linear infinite}.cpz-r2{animation:cpzRoda 40s linear infinite reverse}.cpz-r3{animation:cpzRoda 30s linear infinite}',
    '.cpz.pensando .cpz-r2{animation-duration:8s}.cpz.pensando .cpz-r3{animation-duration:6s}',
    '@keyframes cpzRoda{to{transform:rotate(360deg)}}',
    '.cpz-nucleo{transform-box:view-box;transform-origin:150px 150px;transform:scale(calc(0.98 + var(--cpz-e,0) * 0.04))}',
    '.cpz-btn{position:absolute;left:50%;top:50%;width:44%;height:44%;margin:-22% 0 0 -22%;border:0;padding:0;background:transparent;border-radius:50%;cursor:pointer;outline:none;-webkit-tap-highlight-color:transparent}',
    '.cpz-btn:focus-visible{box-shadow:0 0 0 2px rgba(var(--cpz-g),0.9)}',
    '.cpz-rot{position:relative;font:800 12px/1 ' + MONO + ';letter-spacing:0.3em;color:rgb(var(--cpz-g));text-shadow:0 0 14px rgba(var(--cpz-g),0.8);min-height:14px;display:flex;align-items:center;gap:10px}',
    '.cpz-rot:before,.cpz-rot:after{content:"";width:34px;height:1px;background:linear-gradient(90deg,rgba(var(--cpz-g),0),rgba(var(--cpz-g),0.9))}.cpz-rot:after{transform:scaleX(-1)}',
    '.cpz-txt{position:relative;max-width:min(580px,92vw);min-height:1.5em;font-size:clamp(15px,2vw,18px);line-height:1.5;text-align:center;color:#f2f8ff;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}',
    '.cpz-txt.vazio{color:rgba(var(--cpz-g),0.7);font-family:' + MONO + ';font-size:13px;letter-spacing:0.08em}',
    '.cpz-dica{position:relative;font:700 10px/1 ' + MONO + ';letter-spacing:0.2em;color:rgba(234,246,255,0.55);min-height:12px}',
    '.cpz-acoes{position:relative;display:flex;gap:10px}',
    '.cpz-fim{height:48px;padding:0 22px;border-radius:12px;border:1px solid rgba(var(--cpz-g),0.45);background:rgba(var(--cpz-g),0.08);color:#eaf6ff;font:800 12px/1 ' + MONO + ';letter-spacing:0.2em;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:10px}',
    '.cpz-fim:hover,.cpz-fim:focus-visible{border-color:rgb(var(--cpz-g));box-shadow:0 0 18px rgba(var(--cpz-g),0.35);outline:none}',
    '.cpz-sos{position:absolute;top:max(14px,env(safe-area-inset-top));left:16px;height:40px;padding:0 16px;border-radius:12px;background:#d32f27;color:#fff;font:800 13px/1 ' + FONTE + ';letter-spacing:0.1em;display:flex;align-items:center;text-decoration:none;box-shadow:0 0 0 3px rgba(255,59,48,0.25)}',
    '@media (prefers-reduced-motion: reduce){.cpz-r1,.cpz-r2,.cpz-r3{animation:none}}'
  ].join('\n');

  function arco(r, a0, a1) {
    var p = function (a) { var t = (a - 90) * Math.PI / 180; return (150 + r * Math.cos(t)).toFixed(2) + ' ' + (150 + r * Math.sin(t)).toFixed(2); };
    return 'M' + p(a0) + ' A' + r + ' ' + r + ' 0 ' + (a1 - a0 > 180 ? 1 : 0) + ' 1 ' + p(a1);
  }
  function svg() {
    var s = '<svg viewBox="0 0 300 300" aria-hidden="true"><defs>' +
      '<radialGradient id="cpzNuc"><stop offset="0" stop-color="#fff" stop-opacity="0.95"/><stop offset="0.35" style="stop-color:rgb(var(--cpz-g))" stop-opacity="0.75"/><stop offset="1" style="stop-color:rgb(var(--cpz-g))" stop-opacity="0"/></radialGradient>' +
      '<linearGradient id="cpzIA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#00F4FD"/><stop offset="0.5" stop-color="#00A1FE"/><stop offset="1" stop-color="#A22BFD"/></linearGradient></defs>';
    // anel externo graduado (120 marcas, maiores a cada 30°) — gira devagar
    s += '<g class="cpz-gira cpz-r1" style="stroke:rgba(var(--cpz-g),0.55)">';
    for (var i = 0; i < 120; i++) { var a = i * 3, m = i % 10 === 0, t = (a - 90) * Math.PI / 180, r1 = 146, r2 = m ? 136 : 141;
      s += '<line x1="' + (150 + r1 * Math.cos(t)).toFixed(2) + '" y1="' + (150 + r1 * Math.sin(t)).toFixed(2) + '" x2="' + (150 + r2 * Math.cos(t)).toFixed(2) + '" y2="' + (150 + r2 * Math.sin(t)).toFixed(2) + '" stroke-width="' + (m ? 1.6 : 0.8) + '"/>'; }
    s += '</g><circle cx="150" cy="150" r="148.5" fill="none" style="stroke:rgba(var(--cpz-g),0.25)" stroke-width="0.8"/>';
    // anel de segmentos (gira ao contrário)
    s += '<g class="cpz-gira cpz-r2" fill="none" stroke-linecap="round" style="stroke:rgb(var(--cpz-g))">' +
      '<path d="' + arco(126, 10, 70) + '" stroke-width="3"/><path d="' + arco(126, 130, 150) + '" stroke-width="3" opacity="0.6"/>' +
      '<path d="' + arco(126, 190, 280) + '" stroke-width="3"/><path d="' + arco(126, 300, 330) + '" stroke-width="3" opacity="0.6"/>' +
      '<path d="' + arco(119, 40, 160) + '" stroke-width="1" opacity="0.5"/><path d="' + arco(119, 220, 340) + '" stroke-width="1" opacity="0.5"/></g>';
    // espectro radial (barras montadas no JS)
    s += '<g class="cpz-esp" stroke-linecap="round" style="stroke:rgb(var(--cpz-g))"></g>';
    // anel interno tracejado
    s += '<g class="cpz-gira cpz-r3"><circle cx="150" cy="150" r="76" fill="none" style="stroke:rgba(var(--cpz-g),0.7)" stroke-width="1.2" stroke-dasharray="2 5"/></g>';
    // núcleo + "IA" no gradiente da marca
    s += '<g class="cpz-nucleo"><circle cx="150" cy="150" r="70" fill="url(#cpzNuc)" opacity="0.55"/>' +
      '<circle cx="150" cy="150" r="54" fill="rgba(5,8,22,0.88)" style="stroke:rgb(var(--cpz-g))" stroke-width="1.6"/>' +
      '<circle cx="150" cy="150" r="47" fill="none" style="stroke:rgba(var(--cpz-g),0.35)" stroke-width="0.8"/>' +
      '<text x="150" y="163" text-anchor="middle" font-family=\'' + FONTE.replace(/"/g, '') + '\' font-weight="800" font-size="38" letter-spacing="4" fill="url(#cpzIA)" style="filter:drop-shadow(0 0 5px rgba(var(--cpz-g),0.6))">IA</text></g>';
    return s + '</svg>';
  }
  // HUD: posição da leitura ao vivo (se ligada) ou do snapshot fixo, sempre com a origem.
  function hudPosicao() {
    var T = window.CapitaoTelemetria, v = T && T.atual ? T.atual() : null, D = window.CapitaoDados;
    if (v) { var p = T.posicao(v).split(' '); return p[0] + '<br>' + p[1] + '<br>AO VIVO ' + T.hora(v); }
    var g = D && D.snapshot && D.snapshot.gps;
    if (!g || !g.texto) return 'POSIÇÃO<br>SEM LEITURA';
    var q = g.texto.split(' ');
    return q[0] + '<br>' + q[1] + '<br>' + (D.demo ? 'DEMO · ' : '') + D.snapshot.hora;
  }

  function monta() {
    if (raiz) return;
    var st = d.createElement('style'); st.textContent = CSS; d.head.appendChild(st);
    raiz = d.createElement('div'); raiz.className = 'cpz'; raiz.setAttribute('role', 'dialog'); raiz.setAttribute('aria-label', 'Conversa por voz'); raiz.setAttribute('aria-hidden', 'true');
    raiz.innerHTML = '<div class="cpz-fundo"></div>' +
      '<a class="cpz-sos" aria-label="SOS — emergência">SOS</a>' +
      '<div class="cpz-hud cpz-tl">CAPITÃO IA · NÚCLEO<br><span class="cpz-modo"></span><br>SINAL <b class="cpz-sinal">000</b></div>' +
      '<div class="cpz-hud cpz-tr"><b class="cpz-hora">--:--</b><br><span class="cpz-pos"></span></div>' +
      '<div class="cpz-palco"><span class="cpz-canto cpz-c1"></span><span class="cpz-canto cpz-c2"></span><span class="cpz-canto cpz-c3"></span><span class="cpz-canto cpz-c4"></span>' + svg() +
      '<button type="button" class="cpz-btn"></button></div>' +
      '<div class="cpz-rot" aria-live="polite"></div><div class="cpz-txt"></div><div class="cpz-dica"></div>' +
      '<div class="cpz-acoes"><button type="button" class="cpz-fim"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true" style="flex-shrink:0"><path d="M6 6l12 12 M18 6L6 18" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/></svg>ENCERRAR</button></div>';
    d.body.appendChild(raiz);
    el = { btn: raiz.querySelector('.cpz-btn'), rot: raiz.querySelector('.cpz-rot'), txt: raiz.querySelector('.cpz-txt'), dica: raiz.querySelector('.cpz-dica'), fim: raiz.querySelector('.cpz-fim'), sos: raiz.querySelector('.cpz-sos'), modo: raiz.querySelector('.cpz-modo'), sinal: raiz.querySelector('.cpz-sinal'), hora: raiz.querySelector('.cpz-hora'), pos: raiz.querySelector('.cpz-pos') };
    // espectro: N barras saindo do anel interno
    var g = raiz.querySelector('.cpz-esp'), NS = 'http://www.w3.org/2000/svg';
    for (var i = 0; i < N; i++) {
      var t = (i * 360 / N - 90) * Math.PI / 180, ln = d.createElementNS(NS, 'line'), c = Math.cos(t), sn = Math.sin(t);
      ln.setAttribute('x1', (150 + R0 * c).toFixed(2)); ln.setAttribute('y1', (150 + R0 * sn).toFixed(2));
      ln.setAttribute('stroke-width', '2.2'); g.appendChild(ln); barras.push({ el: ln, c: c, s: sn });
    }
    el.btn.addEventListener('click', function () {
      var B = window.CapitaoBrain; if (!B) return;
      if (estado === 'ouvindo' && B.vozEnviar) B.vozEnviar();
      else if (estado === 'falando' && B.pularFala) B.pularFala();
    });
    el.fim.addEventListener('click', encerrar);
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && raiz.classList.contains('on')) encerrar(); });
  }
  function encerrar() { var B = window.CapitaoBrain; if (B && B.vozEncerrar) B.vozEncerrar(); esconde(); }

  function pinta(e) {
    var c = COR[e]; if (!c) return;
    raiz.style.setProperty('--cpz-g', c.g);
    raiz.classList.toggle('pensando', e === 'pensando');
    el.rot.textContent = c.rot; el.dica.textContent = c.dica; el.modo.textContent = c.modo;
    el.btn.setAttribute('aria-label', e === 'ouvindo' ? 'Terminei de falar — enviar agora' : e === 'falando' ? 'Interromper a resposta e falar' : 'Processando');
  }
  function texto(t, vazio) { el.txt.textContent = t || vazio || ''; el.txt.classList.toggle('vazio', !t); }
  function mostra() {
    clearTimeout(some); some = 0;
    if (raiz.classList.contains('on')) return;
    var sos = d.querySelector('#dc-root a[href*="SOS-"]') || d.querySelector('a[href*="SOS-"]:not(.cpz-sos)');
    el.sos.href = sos ? sos.getAttribute('href') : (innerWidth < 600 ? 'S2-SOS-Mobile.dc.html' : 'S1-SOS-Web.dc.html');
    el.hora.textContent = window.CapitaoClima ? window.CapitaoClima.hora() : new Date().toTimeString().slice(0, 5);
    el.pos.innerHTML = hudPosicao();
    raiz.classList.add('on'); raiz.setAttribute('aria-hidden', 'false');
    t0 = performance.now();
    if (!raf) raf = requestAnimationFrame(quadro);
  }
  function esconde() {
    clearTimeout(some); some = 0; estado = 'livre';
    if (!raiz) return;
    raiz.classList.remove('on'); raiz.setAttribute('aria-hidden', 'true');
    if (raiz.contains(d.activeElement)) try { d.activeElement.blur(); } catch (e) {}
  }
  // Energia 0–1: cai sozinha; sobe com cada trecho ouvido/palavra falada. Na resposta, uma oscilação imita o ritmo da fala.
  function quadro(ts) {
    raf = 0;
    if (!raiz.classList.contains('on')) { energia = 0; return; }
    var t = (ts - t0) / 1000, base = 0.08 + 0.04 * Math.sin(t * 2.1);
    if (estado === 'falando') base = 0.3 + 0.45 * Math.abs(Math.sin(t * 8.3)) * (0.55 + 0.45 * Math.abs(Math.sin(t * 2.9 + 1.3)));
    else if (estado === 'pensando') base = 0.2 + 0.08 * Math.sin(t * 6);
    if (reduz) base = Math.min(base, 0.25);
    energia = Math.max(base, energia * 0.9);
    raiz.style.setProperty('--cpz-e', energia.toFixed(3));
    for (var i = 0; i < N; i++) {
      var k = Math.min(i, N - i), // espelhado: simétrico dos dois lados
        ruido = 0.5 + 0.5 * Math.sin(t * 7.1 + k * 0.55) * Math.sin(t * 3.3 + k * 1.37),
        len = 2 + energia * 20 * (0.35 + 0.65 * ruido), b = barras[i];
      if (estado === 'pensando') len = 2 + 8 * Math.max(0, Math.sin(t * 4 - i * 0.3));
      b.el.setAttribute('x2', (150 + (R0 + len) * b.c).toFixed(1)); b.el.setAttribute('y2', (150 + (R0 + len) * b.s).toFixed(1));
      b.el.setAttribute('stroke-opacity', (0.3 + Math.min(0.5, len / 30)).toFixed(2));
    }
    var sn = String(Math.round(energia * 100)); el.sinal.textContent = ('00' + sn).slice(-3);
    raf = requestAnimationFrame(quadro);
  }
  function pulso(forca) { energia = Math.min(1, energia + (forca || 0.5)); }

  window.addEventListener('capitao-voz', function (ev) {
    var x = (ev && ev.detail) || {}, e = x.estado;
    if (!d.body) return;
    monta();
    if (e === 'pulso') { pulso(0.35); return; }
    if (e === 'livre') { // some com atraso: na conversa o microfone religa logo depois e o overlay não pisca
      if (!some && raiz.classList.contains('on')) some = setTimeout(esconde, 900);
      return;
    }
    if (!COR[e]) return;
    var novo = e !== estado; estado = e;
    if (novo) pinta(e);
    if (e === 'ouvindo') { texto(x.texto, 'AGUARDANDO COMANDO DE VOZ…'); if (x.texto) pulso(0.55); }
    else if (e === 'pensando') {
      texto(x.texto || '', 'CRUZANDO TELEMETRIA · AGENDA · DOCUMENTOS…'); el.dica.textContent = x.segura ? 'CONSULTANDO A IA DE BORDO…' : COR.pensando.dica; mostra();
      if (!x.segura) some = setTimeout(esconde, 2500); // sem resposta falada (voz→texto): some sozinho; esperando a IA (segura): fica até a fala
      return;
    }
    else if (e === 'falando') { texto(x.texto, ''); pulso(0.4); }
    mostra();
  });
  window.addEventListener('pagehide', esconde);

  window.CapitaoVoz = { esconde: esconde };
})();
