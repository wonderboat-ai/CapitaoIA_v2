/* capitao-simbolo.js — <capitao-simbolo>: o símbolo ∞ da WonderHUB.AI (o PNG ORIGINAL, sem redesenho) com as cores
   da própria logo correndo pelo infinito — o ciano perseguindo o violeta.
   Onde: botão CONVERSA do Main (web, 56 px), do dock da H2 (62 px) e da barra do assistente (capitao-barra.js, 54 px —
   a barra carrega este arquivo nas telas que não o têm no <helmet>).
   Como funciona (fidelidade exata):
     1. o PNG é desenhado no tamanho final (imageSmoothingQuality 'high') → pixels ORIG;
     2. cada pixel ganha t ∈ [0,1) = posição ao longo da linha central do ∞ (uma volta, proporcional ao comprimento);
     3. C(t) = cor média (OKLab, ponderada pelo alfa) das cores ORIGINAIS por faixa de t (512 faixas), vazias preenchidas
        por interpolação circular e suavizadas em círculo;
     4. a cada quadro, com fase φ: pixel = ORIG + (C(t+φ) − C(t)) em OKLab, alfa original.
   φ = 0 devolve o PNG exato; sombreado 3D, dobra e faixa escura ficam no lugar, só as cores andam.
   Cruzamento: a faixa de cima (faixa larga + vão + dobra, o ramo que DESCE do alto do laço esquerdo) usa o t desse
   ramo; o resto usa o ramo mais próximo. t cresce no sentido extremo esquerdo → base esquerda → (por baixo) → alto
   direito → extremo direito → base direita → (por cima) → alto esquerdo, e as cores andam no sentido contrário:
   por cima do cruzamento, do laço esquerdo (ciano) para o direito.
   Atributos: src (padrão assets/wonderhub-simbolo.png) · fluxo="on|off" (off = PNG parado) ·
              ritmo="repouso|ativo" (uma volta em 8 s | 3,5 s).
   Desempenho: um só requestAnimationFrame para todas as instâncias, em cadência regular (1 a cada n batidas da tela):
   15 quadros/s no repouso, 30 no ativo; para fora da tela (IntersectionObserver), com a aba escondida, com o núcleo de
   voz por cima (CapitaoSimbolo.coberto) e com prefers-reduced-motion (aí fica o PNG parado). t e deslocamentos são
   calculados só quando o tamanho muda; a cada quadro só o canvas muda (nada no DOM).
   Nitidez: o canvas tem exatamente os pixels da tela que ocupa (ResizeObserver device-pixel-content-box no Chromium,
   retângulo × devicePixelRatio nos outros), também sob o zoom da prancheta do capitao-app.js.
   Botão redondo: classes .cps-* (CSS injetado uma vez em <style id="capitao-simbolo-css">):
     <button class="cps-botao" style="--cps-d:56px" aria-label="…"><capitao-simbolo></capitao-simbolo></button>
     ativo = classe .cps-ativo ou aria-pressed="true" no botão + ritmo="ativo" no símbolo (CapitaoSimbolo.ativar faz os três).
   Teste: window.CapitaoSimbolo.fase = 0…1 fixa a fase (null volta ao normal); .stats mede o tempo de quadro (ms: media,
   tabela, pixels, put); .mapa(el) pinta o mapa de t (diagnóstico); .render(el, fase) desenha já. */
(function () {
  'use strict';
  if (!window.customElements || customElements.get('capitao-simbolo')) return;

  var SRC = 'assets/wonderhub-simbolo.png';
  var IW = 821, IH = 350;             // PNG original: proporção e sistema de coordenadas da geometria abaixo. O arquivo servido
                                      // é a cópia reduzida (352×150, mesma proporção, 44 KB): o ∞ é desenhado no tamanho final
  var PERIODO = { repouso: 8000, ativo: 3500 };
  var QUADRO = { repouso: 1000 / 15, ativo: 1000 / 30 }; // limite: 15 quadros/s no repouso (8 s/volta já corre liso), 30 no ativo
  var NB = 512, NT = 2048, SIGMA = 10, KS = 16;

  // Linha central do ∞ (Catmull-Rom fechada, x/y normalizados 0-1 na imagem), ajustada ao desenho real:
  // começa no extremo esquerdo e segue no sentido de t crescente (ver acima).
  var P = [.0529,.5765,.0578,.6308,.0674,.6817,.081,.7275,.0978,.7674,.1171,.8008,.1383,.8273,.1608,.8466,.1843,.8584,
    .2082,.8625,.2323,.8598,.256,.8509,.2793,.8364,.3021,.8173,.3242,.7944,.3457,.7683,.3665,.739,.3864,.7068,.4055,.6717,
    .4239,.6348,.4419,.5966,.4593,.5572,.4762,.5164,.4929,.4751,.5098,.4343,.5272,.3947,.5451,.3565,.5638,.3206,.5836,.2878,
    .6041,.2578,.6253,.2301,.647,.2047,.6692,.1822,.692,.1633,.7153,.1486,.7391,.1386,.7632,.1334,.7873,.1337,.8112,.1404,
    .8346,.1538,.8571,.1736,.8784,.1998,.8981,.2321,.9159,.2701,.9314,.3131,.9439,.3609,.9529,.4127,.9579,.4674,.9589,.5234,
    .9559,.579,.9489,.6325,.9382,.6827,.9242,.7281,.9073,.7678,.888,.8013,.8669,.8284,.8445,.8492,.8212,.8639,.7974,.873,
    .7733,.8766,.7493,.8743,.7255,.8658,.702,.8519,.6792,.8335,.657,.811,.6355,.785,.6146,.7561,.5943,.7249,.5747,.6917,
    .5554,.6571,.5366,.6213,.518,.5848,.4995,.548,.481,.5111,.4625,.4743,.4438,.4382,.4247,.4031,.4052,.3691,.3853,.3368,
    .3648,.3067,.3435,.2794,.3216,.2555,.299,.2354,.2758,.2197,.2521,.2099,.2281,.2072,.2041,.2114,.1804,.222,.1574,.2388,
    .1355,.2619,.1149,.2913,.0963,.3267,.0801,.368,.067,.4149,.0578,.4663,.053,.5209];
  // Cruzamento: faixa de x (normalizada) e bordas da faixa de cima a cada 10 px da imagem — bU = borda de cima da faixa
  // larga, bL = borda de baixo da dobra (y normalizado). Onde encostam no ramo de baixo (oU, oL), a borda é de oclusão
  // e o pixel da fronteira mistura os dois ramos pela cobertura; no resto, dá para o fundo (folga de 2 px).
  var Z = [.29294, .70706], TO = [.6135, .887], OU = [.49269, .5609], OL = [.38551, .46711];
  var BU = [.0245,.031,.0384,.0469,.0579,.0687,.0822,.0968,.1135,.1306,.1506,.1706,.1926,.2159,.2412,.2663,.2932,.3208,
    .3491,.3778,.4069,.4359,.4652,.4932,.5222,.5484,.575,.6,.6227,.6454,.6654,.6847,.702,.7161,.7305];
  var BL = [.4329,.4448,.4599,.4763,.4923,.5116,.5306,.552,.5735,.5956,.6183,.6412,.6643,.6875,.7105,.7335,.7557,.777,
    .7982,.8176,.8367,.854,.871,.8857,.9001,.9134,.9262,.9371,.9467,.9557,.9638,.9704,.977,.9807,.9837];

  // ---------- geometria (uma vez) ----------
  var M = 0, SX, SY, ST, O0, O1;
  function geo() {
    if (M) return;
    var n = P.length / 2, i, j, k = 0;
    M = n * KS; SX = new Float64Array(M); SY = new Float64Array(M); ST = new Float64Array(M + 1);
    for (i = 0; i < n; i++) {
      var a = ((i + n - 1) % n) * 2, b = i * 2, c = ((i + 1) % n) * 2, d = ((i + 2) % n) * 2;
      var x0 = P[a] * IW, y0 = P[a + 1] * IH, x1 = P[b] * IW, y1 = P[b + 1] * IH;
      var x2 = P[c] * IW, y2 = P[c + 1] * IH, x3 = P[d] * IW, y3 = P[d + 1] * IH;
      for (j = 0; j < KS; j++) {
        var s = j / KS, s2 = s * s, s3 = s2 * s;
        SX[k] = 0.5 * (2 * x1 + (x2 - x0) * s + (2 * x0 - 5 * x1 + 4 * x2 - x3) * s2 + (3 * x1 - x0 - 3 * x2 + x3) * s3);
        SY[k] = 0.5 * (2 * y1 + (y2 - y0) * s + (2 * y0 - 5 * y1 + 4 * y2 - y3) * s2 + (3 * y1 - y0 - 3 * y2 + y3) * s3);
        k++;
      }
    }
    var tot = 0; ST[0] = 0;
    for (k = 1; k <= M; k++) { var m = k % M; tot += Math.sqrt((SX[m] - SX[k - 1]) * (SX[m] - SX[k - 1]) + (SY[m] - SY[k - 1]) * (SY[m] - SY[k - 1])); ST[k] = tot; }
    for (k = 1; k <= M; k++) ST[k] /= tot;
    for (O0 = 0; ST[O0] < TO[0]; O0++);
    for (O1 = O0; ST[O1] < TO[1]; O1++);
  }

  // t do ponto (x, y) (px da imagem): amostra mais próxima entre [a, b) de 8 em 8, depois projeção nos segmentos vizinhos
  function proj(x, y, a, b, preso) {
    var best = 1e30, bk = a, k, m, dx, dy, d;
    for (k = a; k < b; k += 8) { dx = x - SX[k]; dy = y - SY[k]; d = dx * dx + dy * dy; if (d < best) { best = d; bk = k; } }
    var lo = bk - 10, hi = bk + 10, bt = 0;
    if (preso) { if (lo < a) lo = a; if (hi > b - 1) hi = b - 1; }
    best = 1e30;
    for (k = lo; k < hi; k++) {
      m = k < 0 ? k + M : k >= M ? k - M : k;
      var n = m + 1 === M ? 0 : m + 1, ax = SX[m], ay = SY[m], vx = SX[n] - ax, vy = SY[n] - ay;
      var u = ((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy);
      u = u < 0 ? 0 : u > 1 ? 1 : u;
      dx = x - ax - u * vx; dy = y - ay - u * vy; d = dx * dx + dy * dy;
      if (d < best) { best = d; bt = ST[m] + u * (ST[m + 1] - ST[m]); }
    }
    return bt >= 1 ? bt - 1 : bt;
  }

  // borda do cruzamento em x (px da imagem): [y em px, cosseno da inclinação]
  var ZS = (Z[1] - Z[0]) / (BU.length - 1), BR = [0, 0];
  function borda(tab, x) {
    var f = (x / IW - Z[0]) / ZS, i;
    if (f < 0) f = 0; if (f > tab.length - 1) f = tab.length - 1;
    i = Math.min(f | 0, tab.length - 2);
    var sl = (tab[i + 1] - tab[i]) * IH / (ZS * IW);
    BR[0] = (tab[i] + (tab[i + 1] - tab[i]) * (f - i)) * IH; BR[1] = 1 / Math.sqrt(1 + sl * sl);
    return BR;
  }

  // ---------- cor: sRGB ↔ OKLab ----------
  var DEC = new Float64Array(256), ENC = new Float64Array(4098);
  (function () {
    var i, c;
    for (i = 0; i < 256; i++) { c = i / 255; DEC[i] = c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
    for (i = 0; i < 4098; i++) { c = Math.min(i / 4096, 1); ENC[i] = 255 * (c <= 0.0031308 ? c * 12.92 : 1.055 * Math.pow(c, 1 / 2.4) - 0.055); }
  })();
  function enc(v) { if (v <= 0) return 0; if (v >= 1) return 255; var f = v * 4096, i = f | 0; return ENC[i] + (ENC[i + 1] - ENC[i]) * (f - i); }
  var RGB = new Float64Array(3); // saída de lab2rgb (0-255, sem arredondar); vetor tipado evita criar número a cada pixel
  function lab2rgb(L, A, B) {
    var l = L + 0.3963377774 * A + 0.2158037573 * B, m = L - 0.1055613458 * A - 0.0638541728 * B, s = L - 0.0894841775 * A - 1.2914855480 * B;
    l = l * l * l; m = m * m * m; s = s * s * s;
    RGB[0] = enc(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s);
    RGB[1] = enc(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s);
    RGB[2] = enc(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s);
  }

  // ---------- CSS (uma vez) ----------
  var CORES = '#00F4FD 0deg,#00A1FE 62deg,#1F53FA 118deg,#A22BFD 172deg,#CD3AFE 222deg,#00F4FD 360deg';
  function css() {
    if (document.getElementById('capitao-simbolo-css')) return;
    var s = document.createElement('style'); s.id = 'capitao-simbolo-css';
    s.textContent =
      '@keyframes cpsPulso{0%,100%{opacity:1}50%{opacity:.55}}' +
      '@keyframes cpsBrilho{0%,100%{opacity:.62}50%{opacity:.22}}' +
      '@keyframes cpsBrilhoAtivo{0%,100%{opacity:1}50%{opacity:.45}}' +
      '@keyframes cpsBrilhoClaro{0%,100%{opacity:.38}50%{opacity:.14}}' +
      '@keyframes cpsBrilhoClaroAtivo{0%,100%{opacity:.62}50%{opacity:.28}}' +
      'capitao-simbolo{display:inline-block;position:relative;vertical-align:middle;line-height:0;aspect-ratio:821/350}' +
      'capitao-simbolo>canvas{position:absolute;left:0;top:0;width:100%;height:100%;display:block}' +
      // disco: fundo #050816 fixo nos dois temas; o ∞ ocupa 72% do diâmetro na largura
      '.cps-botao{--cps-d:56px;position:relative;isolation:isolate;box-sizing:border-box;width:var(--cps-d);height:var(--cps-d);flex-shrink:0;border-radius:50%;border:none;padding:0;margin:0;background:#050816;display:flex;align-items:center;justify-content:center;cursor:pointer;overflow:visible;-webkit-tap-highlight-color:transparent;font:inherit;color:inherit;transition:transform .3s;box-shadow:0 6px 16px rgba(var(--cap-shadow-rgb,0,0,0),calc(.45*var(--cap-shadow-k,1)))}' +
      '.cps-botao capitao-simbolo{width:calc(var(--cps-d)*.72);height:calc(var(--cps-d)*.3069);pointer-events:none}' +
      // caixa em px inteiros e com a mesma paridade do disco (centro exato): com px quebrado o navegador reamostra o
      // canvas. Só com round() (sem ele, var() inválido na hora do cálculo zeraria a largura — por isso o @supports)
      '@supports (width:round(1.5px,1px)){.cps-botao capitao-simbolo{width:round(calc(var(--cps-d)*.72),2px);height:round(calc(var(--cps-d)*.3069),2px)}}' +
      // borda fina (≈2 px) em degradê cônico parado, pulsando em opacidade (100% ↔ 55%)
      '.cps-botao::before{content:"";position:absolute;left:0;top:0;right:0;bottom:0;border-radius:50%;pointer-events:none;background:conic-gradient(from 270deg,' + CORES + ');' +
        '-webkit-mask:radial-gradient(closest-side,transparent calc(100% - 2.5px),#000 calc(100% - 1.75px));mask:radial-gradient(closest-side,transparent calc(100% - 2.5px),#000 calc(100% - 1.75px));animation:cpsPulso 4s ease-in-out infinite}' +
      // brilho externo contido: anel suave pré-desenhado, só a opacidade anda (na mesma cadência)
      '.cps-botao::after{content:"";position:absolute;left:-8px;top:-8px;right:-8px;bottom:-8px;border-radius:50%;z-index:-1;pointer-events:none;background:conic-gradient(from 270deg,' + CORES + ');' +
        '-webkit-mask:radial-gradient(closest-side,transparent calc(100% - 8.5px),rgba(0,0,0,.6) calc(100% - 6.5px),rgba(0,0,0,.2) calc(100% - 3.5px),transparent 100%);mask:radial-gradient(closest-side,transparent calc(100% - 8.5px),rgba(0,0,0,.6) calc(100% - 6.5px),rgba(0,0,0,.2) calc(100% - 3.5px),transparent 100%);animation:cpsBrilho 4s ease-in-out infinite;transition:transform .3s}' +
      '.cps-botao.cps-ativo::before,.cps-botao[aria-pressed="true"]::before{animation-duration:2s}' +
      '.cps-botao.cps-ativo::after,.cps-botao[aria-pressed="true"]::after{animation:cpsBrilhoAtivo 2s ease-in-out infinite}' +
      // tema claro (capitao-theme.js marca <html data-capitao-tema="claro">): sobre fundo branco o halo colorido pesa
      // mais — fica em ~60% (o disco, a borda e o pulso não mudam)
      '[data-capitao-tema="claro"] .cps-botao::after{animation-name:cpsBrilhoClaro}' +
      '[data-capitao-tema="claro"] .cps-botao.cps-ativo::after,[data-capitao-tema="claro"] .cps-botao[aria-pressed="true"]::after{animation-name:cpsBrilhoClaroAtivo}' +
      // passar o mouse: sobe 2 px e o brilho abre um pouco (só em aparelho com mouse, para não grudar no toque)
      '@media (hover:hover){.cps-botao:hover{transform:translateY(-2px)}.cps-botao:hover::after{transform:scale(1.07)}}' +
      '.cps-botao:focus-visible{outline:2px solid var(--cap-accent,#00a1fe);outline-offset:3px}' +
      '.cps-botao:active{transform:translateY(0) scale(.97)}' +
      // anel de separação quando o botão sai de cima de um dock/cartão
      '.cps-botao.cps-sep{box-shadow:0 0 0 3px rgb(var(--cap-card2-rgb,10,15,32)),0 6px 16px rgba(var(--cap-shadow-rgb,0,0,0),calc(.45*var(--cap-shadow-k,1)))}' +
      '@media (prefers-reduced-motion:reduce){.cps-botao::before,.cps-botao::after{animation:none!important}.cps-botao::before{opacity:1}.cps-botao::after{opacity:.5}[data-capitao-tema="claro"] .cps-botao::after{opacity:.3}.cps-botao,.cps-botao::after{transition:none}}';
    var h = document.head || document.documentElement;
    h.insertBefore(s, h.firstChild); // no começo: as regras da tela (mesma especificidade) prevalecem
  }

  // ---------- imagens (uma por endereço) ----------
  var IMGS = {};
  function imagem(src, cb) {
    var e = IMGS[src];
    if (!e) {
      e = IMGS[src] = { img: new Image(), ok: false, erro: false, fila: [] };
      e.img.decoding = 'async';
      e.img.onload = function () { e.ok = true; var f = e.fila; e.fila = []; f.forEach(function (g) { g(); }); };
      e.img.onerror = function () { e.erro = true; e.fila = []; };
      e.img.src = src;
    }
    if (e.ok) cb(); else if (!e.erro) e.fila.push(cb);
    return e;
  }

  // ---------- laço único ----------
  var TODOS = [], raf = 0, ultimo = 0, fixa = null, vsync = 1000 / 60, conta = 0;
  var REDUZ = false, mq = window.matchMedia ? matchMedia('(prefers-reduced-motion: reduce)') : null;
  if (mq) {
    REDUZ = mq.matches;
    var mudou = function () { REDUZ = mq.matches; TODOS.forEach(function (el) { el._quadro(); }); agenda(); };
    if (mq.addEventListener) mq.addEventListener('change', mudou); else if (mq.addListener) mq.addListener(mudou);
  }
  var STATS = { quadros: 0, ms: 0, media: 0, ultimo: 0, tabela: 0, pixels: 0, put: 0, px: 0,
    zera: function () { STATS.quadros = 0; STATS.ms = 0; STATS.media = 0; STATS.tabela = 0; STATS.pixels = 0; STATS.put = 0; STATS.px = 0; } };

  var coberto = false; // o núcleo de voz (capitao-voz.js) cobre a tela: o ∞ fica parado no último quadro
  function anda(el) { return !coberto && el._fluxo && el._visivel && el._w > 0 && !REDUZ && fixa === null && !el._diag && !el._semFluxo; }
  function agenda() {
    if (raf || document.hidden) return;
    for (var i = 0; i < TODOS.length; i++) if (anda(TODOS[i])) { raf = requestAnimationFrame(tick); return; }
  }
  function tick(now) {
    raf = 0;
    if (document.hidden) return;
    var i, el, algum = false, q = QUADRO.repouso;
    for (i = 0; i < TODOS.length; i++) if (anda(TODOS[i])) { algum = true; if (TODOS[i]._ritmo === 'ativo') { q = QUADRO.ativo; break; } }
    if (!algum) { ultimo = 0; return; }
    raf = requestAnimationFrame(tick);
    // cadência regular: desenha 1 a cada n batidas da tela (30 quadros/s: 60 Hz → 2, 90 → 3, 120 → 4, 144 → 5, 75 → 3;
    // 15 quadros/s: o dobro). O marca-passo fixo de 33 ms alternava 27/40 ms em 75 e 144 Hz (tranco visível).
    var d = ultimo ? now - ultimo : 0; ultimo = now;
    if (d > 3 && d < 60) vsync += (d - vsync) * 0.1; // intervalo médio entre batidas
    if (++conta < Math.max(1, Math.ceil(q / vsync - 0.15))) return;
    conta = 0;
    var t0 = performance.now();
    var dpr = Math.min(window.devicePixelRatio || 1, 3);
    for (i = 0; i < TODOS.length; i++) {
      el = TODOS[i];
      if (!anda(el)) continue;
      if (el._dpr !== dpr) el._medir();
      var dt = el._t ? Math.min(now - el._t, 100) : 0; el._t = now;
      el._fase = (el._fase + dt / PERIODO[el._ritmo]) % 1;
      el._quadro();
    }
    var ms = performance.now() - t0;
    STATS.quadros++; STATS.ms += ms; STATS.media = STATS.ms / STATS.quadros; STATS.ultimo = ms;
  }
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) { if (raf) { cancelAnimationFrame(raf); raf = 0; } }
    else { TODOS.forEach(function (el) { el._t = 0; }); agenda(); }
  });

  var io = window.IntersectionObserver ? new IntersectionObserver(function (es) {
    es.forEach(function (e) { var el = e.target; el._visivel = e.isIntersecting; if (el._visivel) { el._t = 0; el._quadro(); } });
    agenda();
  }, { rootMargin: '48px' }) : null;
  // observa o canvas: no Chromium vem junto o tamanho em pixels reais da tela (device-pixel-content-box), já com o
  // zoom da prancheta (capitao-app.js) e o encaixe na grade de pixels — canvas 1:1 com a tela = ∞ nítido
  var ro = window.ResizeObserver ? new ResizeObserver(function (es) {
    es.forEach(function (e) {
      var el = e.target._dono, d = e.devicePixelContentBoxSize && e.devicePixelContentBoxSize[0];
      if (!el) return;
      el._dpx = d ? [d.inlineSize, d.blockSize] : null;
      el._medir();
    });
    agenda();
  }) : null;
  // janela mudou: o capitao-app.js refaz o zoom da prancheta num rAF, e fora do Chromium o ResizeObserver não vê
  // zoom — mede de novo um pouco depois (só compara; refaz o canvas apenas se o tamanho em pixels mudou)
  var remede = 0;
  window.addEventListener('resize', function () {
    clearTimeout(remede);
    remede = setTimeout(function () { TODOS.forEach(function (el) { el._medir(); }); agenda(); }, 150);
  });

  // ---------- o elemento ----------
  customElements.define('capitao-simbolo', class extends HTMLElement {
    static get observedAttributes() { return ['src', 'fluxo', 'ritmo']; }
    constructor() {
      super();
      this._fase = 0; this._t = 0; this._w = 0; this._h = 0; this._dpr = 0; this._visivel = !io;
      this._fluxo = true; this._ritmo = 'repouso'; this._pronto = false; this._diag = false;
    }
    connectedCallback() {
      css(); geo();
      if (!this._cv) {
        this._cv = document.createElement('canvas');
        this._cv._dono = this;
        this._cv.setAttribute('aria-hidden', 'true');
        this.appendChild(this._cv);
        if (!this.hasAttribute('aria-hidden') && !this.hasAttribute('aria-label') && !this.hasAttribute('role')) this.setAttribute('aria-hidden', 'true');
      }
      this._ler();
      if (TODOS.indexOf(this) < 0) TODOS.push(this);
      if (io) io.observe(this);
      if (ro) { try { ro.observe(this._cv, { box: 'device-pixel-content-box' }); } catch (e) { ro.observe(this._cv); } } // Safari: sem essa caixa
      this._medir();
      this._carregar();
      agenda();
    }
    disconnectedCallback() {
      var i = TODOS.indexOf(this); if (i >= 0) TODOS.splice(i, 1);
      if (io) io.unobserve(this);
      if (ro) ro.unobserve(this._cv);
    }
    attributeChangedCallback(n) {
      if (!this._cv) return;
      this._ler();
      if (n === 'src') this._carregar();
      else if (n === 'ritmo') agenda(); // a fase segue contínua, só muda a velocidade (sem quadro parado na troca)
      else { this._t = 0; this._quadro(); agenda(); }
    }
    _ler() {
      this._fluxo = this.getAttribute('fluxo') !== 'off';
      this._ritmo = this.getAttribute('ritmo') === 'ativo' ? 'ativo' : 'repouso';
    }
    _carregar() {
      var self = this, src = this.getAttribute('src') || SRC;
      if (this._src === src) return;
      this._src = src; this._pronto = false; this._orig = null; this._origBase = null;
      this._img = imagem(src, function () { if (self._src === src) { self._sujo = true; self._quadro(); agenda(); } });
    }
    // tamanho do canvas em pixels da tela. clientWidth arredonda para px inteiro de CSS e ignora o zoom da prancheta:
    // o canvas saía 1-10% maior que a caixa real e o navegador o reamostrava (∞ borrado). Agora: retângulo real × dpr,
    // e, no Chromium, o valor exato do ResizeObserver quando bate com essa conta (o emulador de DPR informa px de CSS).
    _medir() {
      var dpr = Math.min(window.devicePixelRatio || 1, 3), r = this.getBoundingClientRect(), d = this._dpx;
      var w = Math.round(r.width * dpr), h = Math.round(r.height * dpr);
      if (d && Math.abs(d[0] - r.width * dpr) <= Math.max(2, w * 0.15) && Math.abs(d[1] - r.height * dpr) <= Math.max(2, h * 0.15)) { w = d[0]; h = d[1]; }
      if (w === this._w && h === this._h && dpr === this._dpr) return;
      this._w = w; this._h = h; this._dpr = dpr; this._sujo = true; this._pronto = false;
      if (w > 0 && h > 0) { this._cv.width = w; this._cv.height = h; this._quadro(); }
    }
    // PNG no tamanho final, centrado (proporção preservada)
    _caixa() {
      var w = this._w, h = this._h, ar = IW / IH, dw = w, dh = w / ar;
      if (dh > h) { dh = h; dw = h * ar; }
      return { x: (w - dw) / 2, y: (h - dh) / 2, w: dw, h: dh };
    }
    // PNG reduzido ao tamanho final (ORIG), uma vez por tamanho, num canvas de leitura. O quadro parado e o fluxo saem
    // destes MESMOS pixels: drawImage direto no canvas visível usa outro caminho de reamostragem (GPU) e as bordas
    // mudavam até ~70/255 de alfa ao começar/parar o fluxo.
    _base() {
      var o = this._origBase, w = this._w, h = this._h;
      if (o && o.width === w && o.height === h) return o;
      if (this._semFluxo) return null; // já sabemos que não dá para ler os pixels
      var b = this._caixa(), oc = document.createElement('canvas'); oc.width = w; oc.height = h;
      var ox = oc.getContext('2d', { willReadFrequently: true });
      ox.imageSmoothingEnabled = true; ox.imageSmoothingQuality = 'high';
      ox.drawImage(this._img.img, b.x, b.y, b.w, b.h);
      try { o = ox.getImageData(0, 0, w, h); } catch (e) { o = null; if (e && e.name === 'SecurityError') this._semFluxo = true; } // canvas contaminado (file://)
      return (this._origBase = o);
    }
    _estatico() {
      var c = this._cv.getContext('2d'), o = this._base();
      if (o) { c.putImageData(o, 0, 0); return; }
      var b = this._caixa(); // sem leitura de pixels (file://): desenha o PNG direto, parado
      c.clearRect(0, 0, this._w, this._h);
      c.imageSmoothingEnabled = true; c.imageSmoothingQuality = 'high';
      c.drawImage(this._img.img, b.x, b.y, b.w, b.h);
    }
    // pré-cálculo (só quando o tamanho muda): t por pixel, perfil C(t), OKLab e correção de arredondamento
    _preparar() {
      this._sujo = false; this._pronto = false;
      var w = this._w, h = this._h, b = this._caixa();
      var orig = this._base();
      if (!orig) return; // canvas contaminado (file://): fica o PNG parado
      var D = orig.data, n = 0, i, k, x, y;
      for (i = 3; i < D.length; i += 4) if (D[i]) n++;
      var OFF = new Int32Array(n), Q = new Uint16Array(n), Q2 = new Uint16Array(n), W2 = new Uint8Array(n);
      var V = new Float32Array(n * 6); // por pixel, juntos: L, a, b (OKLab do original) e a correção de arredondamento R, G, B
      var sx = IW / b.w, sy = IH / b.h, zx0 = Z[0] * IW, zx1 = Z[1] * IW, ou0 = OU[0] * IW, ou1 = OU[1] * IW, ol0 = OL[0] * IW, ol1 = OL[1] * IW;
      var soma = new Float64Array(NB * 4), T1 = new Float32Array(n);
      k = 0;
      for (y = 0; y < h; y++) for (x = 0; x < w; x++) {
        var o = (y * w + x) * 4, al = D[o + 3];
        if (!al) continue;
        var ix = (x + 0.5 - b.x) * sx, iy = (y + 0.5 - b.y) * sy;
        var t1 = proj(ix, iy, 0, M, false), t2 = t1, w2 = 0;
        if (ix >= zx0 && ix <= zx1) {
          // faixa de cima do cruzamento (faixa larga + vão + dobra): distância perpendicular para dentro, em px da imagem
          var bu = borda(BU, ix), yu = bu[0], cu = bu[1], bl = borda(BL, ix), yl = bl[0], cl = bl[1];
          var du = (iy - yu) * cu, dl = (yl - iy) * cl, cima = du < dl;
          var din = cima ? du + (ix >= ou0 && ix <= ou1 ? 0 : 2) : dl + (ix >= ol0 && ix <= ol1 ? 0 : 2);
          var cob = 0.5 + din / sx; // cobertura do pixel pela faixa de cima
          if (cob > 0) {
            var to = proj(ix, iy, O0, O1, true);
            if (cob >= 1) t1 = to; else { t2 = t1; t1 = to; w2 = Math.round((1 - cob) * 255); }
          }
        }
        OFF[k] = o; T1[k] = t1;
        Q[k] = Math.round(t1 * NT) % NT; Q2[k] = Math.round(t2 * NT) % NT; W2[k] = w2;
        // OKLab do pixel original
        var r = DEC[D[o]], g = DEC[D[o + 1]], bb = DEC[D[o + 2]];
        var l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * bb);
        var m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * bb);
        var s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * bb);
        var j6 = k * 6;
        V[j6] = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s;
        V[j6 + 1] = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s;
        V[j6 + 2] = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s;
        // correção: o quadro φ = 0 devolve exatamente o pixel original
        lab2rgb(V[j6], V[j6 + 1], V[j6 + 2]);
        V[j6 + 3] = D[o] - RGB[0]; V[j6 + 4] = D[o + 1] - RGB[1]; V[j6 + 5] = D[o + 2] - RGB[2];
        // perfil: média ponderada pelo alfa por faixa de t
        var f = ((t1 * NB) | 0) % NB, a = al / 255;
        soma[f * 4] += a; soma[f * 4 + 1] += a * V[j6]; soma[f * 4 + 2] += a * V[j6 + 1]; soma[f * 4 + 3] += a * V[j6 + 2];
        k++;
      }
      this._perfil(soma);
      this._n = n; this._OFF = OFF; this._Q = Q; this._Q2 = Q2; this._W2 = W2; this._T1 = T1;
      this._V = V;
      this._orig = orig;
      this._out = new ImageData(new Uint8ClampedArray(D), w, h);
      this._dT = new Float64Array(NT * 3);
      this._pronto = true;
    }
    // C(t): faixas vazias por interpolação circular + suavização gaussiana circular; guarda C nas NT posições
    _perfil(soma) {
      var C = [new Float64Array(NB), new Float64Array(NB), new Float64Array(NB)], cheio = [], i, j, c;
      for (i = 0; i < NB; i++) if (soma[i * 4] > 0) { cheio.push(i); for (c = 0; c < 3; c++) C[c][i] = soma[i * 4 + 1 + c] / soma[i * 4]; }
      if (!cheio.length) cheio.push(0);
      for (j = 0; j < cheio.length; j++) {
        var a = cheio[j], b = cheio[(j + 1) % cheio.length], gap = (b - a + NB) % NB || NB;
        for (i = 1; i < gap; i++) for (c = 0; c < 3; c++) C[c][(a + i) % NB] = C[c][a] + (C[c][b] - C[c][a]) * i / gap;
      }
      var R = Math.ceil(SIGMA * 3), ker = [], ks = 0;
      for (i = -R; i <= R; i++) { ker.push(Math.exp(-0.5 * i * i / (SIGMA * SIGMA))); ks += ker[ker.length - 1]; }
      var S = [new Float64Array(NB), new Float64Array(NB), new Float64Array(NB)];
      for (c = 0; c < 3; c++) for (i = 0; i < NB; i++) { var v = 0; for (j = -R; j <= R; j++) v += C[c][(i + j + NB) % NB] * ker[j + R]; S[c][i] = v / ks; }
      this._C = S;
      // C(t) já nas NT posições de t (a parte fixa do deslocamento)
      this._C0 = [new Float64Array(NT), new Float64Array(NT), new Float64Array(NT)];
      for (c = 0; c < 3; c++) for (i = 0; i < NT; i++) this._C0[c][i] = this._cor(c, i / NT);
    }
    // C(t) interpolado (faixa i cobre [i/NB, (i+1)/NB), centro em (i+0.5)/NB)
    _cor(c, t) {
      var f = t * NB - 0.5; f -= Math.floor(f / NB) * NB;
      var i = f | 0, j = i + 1 === NB ? 0 : i + 1, C = this._C[c];
      return C[i] + (C[j] - C[i]) * (f - i);
    }
    _quadro() {
      if (!this._cv || !this._w || !this._h || !this._img || !this._img.ok) return;
      var fase = fixa !== null ? fixa : this._fase;
      if (this._diag) return;
      if (!this._fluxo || REDUZ || this._semFluxo || (fase === 0 && !this._forca)) { this._estatico(); return; }
      if (this._sujo) this._preparar();
      if (this._semFluxo) { this._estatico(); return; }
      if (!this._pronto) { this._estatico(); return; }
      var t0 = performance.now();
      // deslocamento por posição: C(t+φ) − C(t); C já está nas NT posições, então basta deslocar φ·NT posições
      var T = this._dT, L0 = this._C0[0], A0 = this._C0[1], B0 = this._C0[2];
      var sh = fase * NT, si = Math.floor(sh), sf = sh - si, q, a, b;
      for (q = 0; q < NT; q++) {
        a = (q + si) & (NT - 1); b = (a + 1) & (NT - 1);
        T[q * 3] = L0[a] + (L0[b] - L0[a]) * sf - L0[q];
        T[q * 3 + 1] = A0[a] + (A0[b] - A0[a]) * sf - A0[q];
        T[q * 3 + 2] = B0[a] + (B0[b] - B0[a]) * sf - B0[q];
      }
      var t1 = performance.now();
      var n = this._n, OFF = this._OFF, Q = this._Q, Q2 = this._Q2, W2 = this._W2, V = this._V;
      var D = this._out.data, E = ENC, k, j, L, A, B, w, q2, o, l, m, s, r, g, u, f, i;
      for (k = 0, j = 0; k < n; k++, j += 6) {
        q = Q[k] * 3; L = V[j] + T[q]; A = V[j + 1] + T[q + 1]; B = V[j + 2] + T[q + 2];
        if (W2[k]) { q2 = Q2[k] * 3; w = W2[k] / 255; L += w * (T[q2] - T[q]); A += w * (T[q2 + 1] - T[q + 1]); B += w * (T[q2 + 2] - T[q + 2]); }
        // mesma conta do lab2rgb()/enc(), escrita aqui dentro por desempenho — tem de ficar idêntica (φ = 0 devolve o original exato)
        l = L + 0.3963377774 * A + 0.2158037573 * B; m = L - 0.1055613458 * A - 0.0638541728 * B; s = L - 0.0894841775 * A - 1.2914855480 * B;
        l = l * l * l; m = m * m * m; s = s * s * s;
        r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s;
        g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s;
        u = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s;
        if (r <= 0) r = 0; else if (r >= 1) r = 255; else { f = r * 4096; i = f | 0; r = E[i] + (E[i + 1] - E[i]) * (f - i); }
        if (g <= 0) g = 0; else if (g >= 1) g = 255; else { f = g * 4096; i = f | 0; g = E[i] + (E[i + 1] - E[i]) * (f - i); }
        if (u <= 0) u = 0; else if (u >= 1) u = 255; else { f = u * 4096; i = f | 0; u = E[i] + (E[i + 1] - E[i]) * (f - i); }
        o = OFF[k]; D[o] = r + V[j + 3]; D[o + 1] = g + V[j + 4]; D[o + 2] = u + V[j + 5];
      }
      var t2 = performance.now();
      this._cv.getContext('2d').putImageData(this._out, 0, 0);
      var t3 = performance.now();
      STATS.tabela += t1 - t0; STATS.pixels += t2 - t1; STATS.put += t3 - t2; STATS.px += n;
    }
  });

  // ---------- API ----------
  function arco(t) { // arco-íris (0 = vermelho) para o mapa de t
    var h = t * 6, i = Math.floor(h), f = h - i;
    return [[1, f, 0], [1 - f, 1, 0], [0, 1, f], [0, 1 - f, 1], [f, 0, 1], [1, 0, 1 - f]][i % 6];
  }
  var API = {
    stats: STATS,
    // liga/desliga o estado ativo do botão (classe, aria-pressed e ritmo do símbolo) numa chamada
    ativar: function (botao, on) {
      if (!botao) return;
      botao.classList.toggle('cps-ativo', !!on);
      if (botao.hasAttribute('aria-pressed')) botao.setAttribute('aria-pressed', on ? 'true' : 'false');
      [].forEach.call(botao.querySelectorAll('capitao-simbolo'), function (s) { s.setAttribute('ritmo', on ? 'ativo' : 'repouso'); });
    },
    // o núcleo de voz cobriu a tela (true) ou saiu (false): o ∞ para por baixo dele (o IntersectionObserver não vê a
    // camada por cima) e volta sem pulo de cor
    coberto: function (on) {
      on = !!on; if (on === coberto) return; coberto = on;
      if (on) { if (raf) { cancelAnimationFrame(raf); raf = 0; } ultimo = 0; }
      else { TODOS.forEach(function (el) { el._t = 0; }); agenda(); }
    },
    // prontos para teste: todas as instâncias com imagem e pré-cálculo
    pronto: function () {
      return TODOS.every(function (el) { if (el._img && el._img.ok && el._sujo && el._w) el._preparar(); return el._pronto || !el._w; });
    },
    // mapa de t pintado em arco-íris sobre o símbolo, com a linha central (diagnóstico)
    mapa: function (el) {
      if (!el || !el._img || !el._img.ok || !el._w || !el._h) return false;
      if (el._sujo || !el._pronto) el._preparar();
      if (!el._pronto) return !!el._semFluxo;
      el._diag = true;
      var c = el._cv.getContext('2d'), im = new ImageData(new Uint8ClampedArray(el._orig.data), el._w, el._h), D = im.data, O = el._orig.data;
      for (var k = 0; k < el._n; k++) {
        var o = el._OFF[k], t = el._T1[k], v = arco(t), w = el._W2[k] / 255;
        if (w) { var v2 = arco(el._Q2[k] / NT); v = [v[0] * (1 - w) + v2[0] * w, v[1] * (1 - w) + v2[1] * w, v[2] * (1 - w) + v2[2] * w]; }
        var lum = (O[o] + O[o + 1] + O[o + 2]) / 765, s = 0.55 + 0.45 * lum;
        D[o] = v[0] * s * 255; D[o + 1] = v[1] * s * 255; D[o + 2] = v[2] * s * 255;
      }
      c.putImageData(im, 0, 0);
      var b = el._caixa(), kx = b.w / IW, ky = b.h / IH;
      c.save(); c.lineWidth = Math.max(1, el._dpr); c.strokeStyle = '#fff'; c.beginPath();
      for (var j = 0; j <= M; j++) { var m = j % M; if (j) c.lineTo(b.x + SX[m] * kx, b.y + SY[m] * ky); else c.moveTo(b.x + SX[m] * kx, b.y + SY[m] * ky); }
      c.stroke();
      c.fillStyle = '#000';
      for (j = 0; j < P.length; j += 2) c.fillRect(b.x + P[j] * IW * kx - 2 * el._dpr, b.y + P[j + 1] * IH * ky - 2 * el._dpr, 4 * el._dpr, 4 * el._dpr);
      c.restore();
      return true;
    },
    // desenha já, na fase dada (teste)
    render: function (el, fase) { el._forca = true; var f = fixa; fixa = fase; el._quadro(); fixa = f; el._forca = false; }
  };
  // fase fixa para teste: CapitaoSimbolo.fase = 0…1 (desenha na hora) · null volta ao normal
  Object.defineProperty(API, 'fase', {
    get: function () { return fixa; },
    set: function (v) {
      fixa = v === null || v === undefined || isNaN(v) ? null : ((+v % 1) + 1) % 1;
      TODOS.forEach(function (el) { el._forca = fixa !== null; el._quadro(); el._forca = false; el._t = 0; });
      agenda();
    }
  });
  window.CapitaoSimbolo = API;
})();
