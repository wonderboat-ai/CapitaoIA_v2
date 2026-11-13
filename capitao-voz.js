/* Capitão IA — núcleo de voz (HUD do cérebro da embarcação).
   Escuta os eventos 'capitao-voz' {estado, texto, segura, som, alerta} que o capitao-brain.js emite e mostra, por cima da tela, o
   núcleo da IA: anéis desenhados num <canvas> em tela cheia (atrás do HUD, da legenda, do ENCERRAR e do SOS), centrados no palco,
   com o ∞ da marca no meio (assets/wonderhub-simbolo.png, o mesmo do capitao-simbolo.js; sem a imagem, o ∞ é traçado).
   De fora para dentro: anel graduado de 120 marcas (maiores a cada 30°) girando devagar · anel de segmentos em arco girando ao
   contrário · espectro radial de 48 barras · anel interno tracejado · núcleo com brilho, disco e o ∞ · colchetes nos 4 cantos do palco.
   Cores da marca (WonderHUB.AI): ESCUTA ciano (#00F4FD, com #00A1FE) · PROCESSANDO violeta (#A22BFD, com #CD3AFE) · RESPOSTA azul
   (#00A1FE, com #1F53FA).
   - ESCUTA (pergunta): o núcleo respira; cada trecho reconhecido dá um pulso no espectro; mostra a transcrição.
   - PROCESSANDO: os anéis aceleram e uma varredura percorre as barras enquanto a resposta é montada (esperando a IA na nuvem, fica até a
     resposta ser falada).
   - RESPOSTA: o espectro e o brilho acompanham a voz — só com som (som: true do cérebro; 'pulso' a cada palavra); 'livre' zera na hora.
   HUD: SINAL (energia da voz) à esquerda; à direita, a cada 1 s e só com a camada ligada, o quadro do instante (CapitaoAgora: a mesma
   fonte e os mesmos formatadores das telas) — hora, posição, SOG, rpm e diesel — em nós Text (.data). Com `alerta` no evento ou com a
   janela de conversa em emergência valendo (CapitaoEmergencia), só «POSIÇÃO · LEIA NO PLOTTER» (CLAUDE.md 10).
   Desempenho: um requestAnimationFrame só com a camada ligada, razão de pixels até 2, pausa com a camada escondida ou a aba oculta;
   prefers-reduced-motion = quadro parado. Nenhuma mutação de DOM por quadro além dos nós Text do HUD.
   Tocar no núcleo: escuta → envia agora; resposta → interrompe e volta a ouvir. ENCERRAR (ou Esc) desliga. SOS sempre no canto.
   window.CapitaoVoz = { esconde, nucleo }: nucleo() → { quadro(t), estado() }; quadro(t) desenha o quadro do instante t (segundos), sempre
   igual para o mesmo estado, e deixa o núcleo parado nele até a camada sumir (foto do guia e testes). */
(function () {
  if (window.CapitaoVoz) return;
  var d = document, raiz = null, el = {}, estado = 'livre', some = 0, relogio = 0, ultTexto = '', temSom = false, quieto = true, alertaEv = false, solto = false;
  var reduz = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  var EM_SOS = false; try { EM_SOS = /SOS-/.test(location.pathname); } catch (e) {}
  var COR = {
    ouvindo: { g: '0,244,253', g2: '0,161,254', rot: 'ESCUTA ATIVA', modo: 'MODO · ESCUTA', dica: 'TOQUE NO NÚCLEO PARA ENVIAR' },
    pensando: { g: '162,43,253', g2: '205,58,254', rot: 'PROCESSANDO', modo: 'MODO · ANÁLISE', dica: '' },
    falando: { g: '0,161,254', g2: '31,83,250', rot: 'CAPITÃO IA', modo: 'MODO · RESPOSTA', dica: 'TOQUE NO NÚCLEO PARA INTERROMPER' }
  };
  var MONO = 'ui-monospace,"SF Mono",Menlo,Consolas,monospace';
  var FONTE = '"Nimbus Sans","Helvetica Neue",Helvetica,Arial,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif';
  // o ∞ da marca mora em assets/, ao lado deste arquivo
  var SIMBOLO_SRC = (function () {
    var s = d.currentScript && d.currentScript.src;
    return s && /capitao-voz\.js/.test(s) ? s.replace(/capitao-voz\.js[^\/]*$/, 'assets/wonderhub-simbolo.png') : 'assets/wonderhub-simbolo.png';
  })();

  var CSS = [
    '.cpz{position:fixed;inset:0;z-index:70;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:max(20px,env(safe-area-inset-top)) 18px max(22px,env(safe-area-inset-bottom));box-sizing:border-box;font-family:' + FONTE + ';color:#eaf6ff;opacity:0;pointer-events:none;transition:opacity .25s ease;-webkit-tap-highlight-color:transparent;--cpz-g:0,244,253}',
    '.cpz.on{opacity:1;pointer-events:auto}',
    '.cpz{overflow-y:auto;justify-content:safe center}',
    '@media (max-height:720px){.cpz-hud{display:none}.cpz{gap:10px}}',
    '@media (max-height:760px) and (max-width:600px){.cpz-hud{display:none}}', // tela estreita e baixa: o HUD de 5 linhas encostaria no anel
    '.cpz-fundo{position:absolute;inset:0;background:radial-gradient(ellipse 55% 40% at 50% 40%,rgba(var(--cpz-g),0.06) 0%,rgba(var(--cpz-g),0) 70%),rgba(5,8,22,0.95);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px)}',
    '.cpz-tela{position:absolute;inset:0;width:100%;height:100%;display:block;pointer-events:none}',
    '.cpz-hud{position:absolute;font:600 10px/1.55 ' + MONO + ';letter-spacing:0.12em;color:rgba(var(--cpz-g),0.85);pointer-events:none;white-space:nowrap}',
    '.cpz-hud b{color:#fff;font-weight:700}',
    '.cpz-tl{top:max(66px,calc(env(safe-area-inset-top) + 58px));left:18px}.cpz-tr{top:max(66px,calc(env(safe-area-inset-top) + 58px));right:18px;text-align:right}',
    // o palco é a caixa de medida do núcleo (o canvas desenha os anéis no centro dela) e a área de toque
    '.cpz-palco{position:relative;width:min(64vmin,36vh,300px);height:min(64vmin,36vh,300px);flex-shrink:0}',
    '.cpz-btn{position:absolute;inset:0;border:0;padding:0;background:transparent;border-radius:50%;cursor:pointer;outline:none;-webkit-tap-highlight-color:transparent}',
    '.cpz-btn:focus-visible{box-shadow:0 0 0 2px rgba(var(--cpz-g),0.9)}',
    '.cpz-rot{position:relative;font:800 12px/1 ' + MONO + ';letter-spacing:0.3em;color:rgb(var(--cpz-g));text-shadow:0 0 14px rgba(var(--cpz-g),0.8);min-height:14px;display:flex;align-items:center;gap:10px}',
    '.cpz-rot:before,.cpz-rot:after{content:"";width:34px;height:1px;background:linear-gradient(90deg,rgba(var(--cpz-g),0),rgba(var(--cpz-g),0.9))}.cpz-rot:after{transform:scaleX(-1)}',
    // legenda com altura fixa de 3 linhas (também no texto vazio, menor): o palco não anda quando ela muda de linhas
    '.cpz-txt{position:relative;flex-shrink:0;max-width:min(580px,92vw);height:calc(4.5 * clamp(15px,2vw,18px));font-size:clamp(15px,2vw,18px);line-height:1.5;text-align:center;color:#f2f8ff;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}',
    '.cpz-txt.vazio{color:rgba(var(--cpz-g),0.7);font-family:' + MONO + ';font-size:13px;letter-spacing:0.08em}',
    '.cpz-dica{position:relative;font:700 10px/1 ' + MONO + ';letter-spacing:0.2em;color:rgba(234,246,255,0.55);min-height:12px;text-align:center}',
    '.cpz-acoes{position:relative;display:flex;gap:10px}',
    '.cpz-fim{height:48px;padding:0 22px;border-radius:12px;border:1px solid rgba(var(--cpz-g),0.45);background:rgba(var(--cpz-g),0.08);color:#eaf6ff;font:800 12px/1 ' + MONO + ';letter-spacing:0.2em;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:10px}',
    '.cpz-fim:hover,.cpz-fim:focus-visible{border-color:rgb(var(--cpz-g));box-shadow:0 0 18px rgba(var(--cpz-g),0.35);outline:none}',
    '.cpz-sos{position:absolute;top:max(14px,env(safe-area-inset-top));left:16px;z-index:2;height:40px;padding:0 16px;border-radius:12px;background:#d32f27;color:#fff;font:800 13px/1 ' + FONTE + ';letter-spacing:0.1em;display:flex;align-items:center;text-decoration:none;box-shadow:0 0 0 3px rgba(255,59,48,0.25)}'
  ].join('\n');

  function ligada() { return !!raiz && raiz.classList.contains('on'); }

  // ---------- HUD: o quadro do instante, a cada 1 s e só com a camada ligada ----------
  // A mesma fonte (CapitaoAgora.instante: o replay, o coletor ou a última leitura salva) e os mesmos formatadores (CapitaoAgora.fmt.campo, .nb,
  // .coord, com as casas do D.campos) da faixa de leitura da Main e da moldura: o texto sai igual ao das telas no mesmo segundo.
  // Em alerta (o evento trouxe `alerta`, a janela de conversa em emergência vale, ou a tela é do SOS): só a instrução do plotter — nenhuma
  // coordenada, velocidade, rumo, distância nem leitura do quadro (CLAUDE.md 10).
  var HUD_N = 5;
  function emAlerta() {
    if (alertaEv || EM_SOS) return true;
    try { var E = window.CapitaoEmergencia; return !!(E && E.valendo()); } catch (e) { return false; }
  }
  function plotter() { var D = window.CapitaoDados, P = D && D.protocolos; return (P && typeof P.hud === 'string' && P.hud) || 'POSIÇÃO · LEIA NO PLOTTER'; }
  function relogioTxt() { // sem instante: o relógio do aparelho no fuso da embarcação
    try { var A = window.CapitaoAgora; if (A && A.fmt && typeof A.fmt.hora === 'function') return A.fmt.hora(Date.now(), true); } catch (e) {}
    return new Date().toTimeString().slice(0, 8);
  }
  function hudLinhas() {
    if (emAlerta()) return [plotter(), '', '', '', ''];
    var D = window.CapitaoDados || {}, sim = D.simulacao === true, falta = sim ? '—' : 'SEM LEITURA', A = window.CapitaoAgora, I = null, f = null, nbf = null, cf = null;
    try { I = A && typeof A.instante === 'function' ? A.instante() : null; f = A && A.fmt && A.fmt.campo; nbf = A && A.fmt && A.fmt.nb; cf = A && A.fmt && A.fmt.coord; } catch (e) { I = null; }
    // sem leitura (modo real sem coletor, ou o rodapé ausente); o instante do replay não vale com a simulação desligada
    if (!(I && I.q && typeof f === 'function' && !(I.fonte === 'replay' && !sim))) return [relogioTxt(), 'POSIÇÃO', falta, '', ''];
    var q = I.q, c = function (nome, un) { var t = f(q, nome); return t === null || t === undefined ? falta : t + (un || ''); };
    var litros = f(q, 'diesel_litros'), pct = I.calc && typeof I.calc.diesel_pct === 'number' && typeof nbf === 'function' ? nbf(I.calc.diesel_pct, 1) : null;
    var bb = f(q, 'motor_bb_rpm'), be = f(q, 'motor_be_rpm'), vivo = !I.selo || I.selo.tom === 'ok';
    return [vivo ? (I.hora || relogioTxt()) : I.selo.texto,   // leitura salva: a hora DELA, nunca como se fosse agora
      typeof q.lat === 'number' && typeof q.lon === 'number' && typeof cf === 'function' ? cf(q.lat, q.lon) : 'POSIÇÃO ' + falta,
      'SOG ' + c('sog_nos', ' NÓS'),
      'RPM ' + (bb === null || bb === undefined ? falta : bb + ' · ' + (be === null || be === undefined ? '—' : be)),
      'DIESEL ' + (litros === null || litros === undefined ? falta : litros + ' L' + (pct ? ' (' + pct + ' %)' : ''))];
  }
  function hud() { // só troca o .data do nó que mudou (não aciona o MutationObserver do capitao-app.js)
    if (!el.hud) return;
    var l; try { l = hudLinhas(); } catch (e) { l = [plotter(), '', '', '', '']; }
    for (var i = 0; i < HUD_N; i++) { var t = String(l[i] == null ? '' : l[i]); if (el.hud[i].data !== t) el.hud[i].data = t; }
  }

  function monta() {
    if (raiz) return;
    var st = d.createElement('style'); st.textContent = CSS; d.head.appendChild(st);
    raiz = d.createElement('div'); raiz.className = 'cpz'; raiz.setAttribute('role', 'dialog'); raiz.setAttribute('aria-label', 'Conversa por voz'); raiz.setAttribute('aria-hidden', 'true');
    raiz.inert = true; // escondida: os botões dela fora do Tab
    raiz.innerHTML = '<div class="cpz-fundo"></div><canvas class="cpz-tela" aria-hidden="true"></canvas>' +
      '<a class="cpz-sos" aria-label="SOS — emergência">SOS</a>' +
      '<div class="cpz-hud cpz-tl">CAPITÃO IA · NÚCLEO<br><span class="cpz-modo"></span><br>SINAL <b class="cpz-sinal">000</b></div>' +
      '<div class="cpz-hud cpz-tr"></div>' +
      '<div class="cpz-palco"><button type="button" class="cpz-btn"></button></div>' +
      '<div class="cpz-rot" aria-live="polite"></div><div class="cpz-txt"></div><div class="cpz-dica"></div>' +
      '<div class="cpz-acoes"><button type="button" class="cpz-fim"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true" style="flex-shrink:0"><path d="M6 6l12 12 M18 6L6 18" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/></svg>ENCERRAR</button></div>';
    d.body.appendChild(raiz);
    el = { btn: raiz.querySelector('.cpz-btn'), rot: raiz.querySelector('.cpz-rot'), txt: raiz.querySelector('.cpz-txt'), dica: raiz.querySelector('.cpz-dica'), fim: raiz.querySelector('.cpz-fim'), sos: raiz.querySelector('.cpz-sos'), modo: raiz.querySelector('.cpz-modo'), sinal: raiz.querySelector('.cpz-sinal'), tela: raiz.querySelector('.cpz-tela'), palco: raiz.querySelector('.cpz-palco') };
    el.sinalT = el.sinal.firstChild;
    // HUD da direita: 5 linhas, cada uma um nó Text criado uma vez (a 1ª em negrito); o tique só troca o .data
    var caixa = raiz.querySelector('.cpz-tr'), b = d.createElement('b'); el.hud = [b.appendChild(d.createTextNode(''))]; caixa.appendChild(b);
    for (var i = 1; i < HUD_N; i++) { caixa.appendChild(d.createElement('br')); el.hud.push(caixa.appendChild(d.createTextNode(''))); }
    try { ctx = el.tela.getContext('2d'); } catch (e) { ctx = null; }
    simbolo();
    el.btn.addEventListener('click', function () {
      var B = window.CapitaoBrain; if (!B) return;
      if (estado === 'ouvindo' && B.vozEnviar) B.vozEnviar();
      else if (estado === 'falando' && B.pularFala) B.pularFala();
    });
    el.fim.addEventListener('click', encerrar);
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && raiz.classList.contains('on')) encerrar(); });
  }
  function encerrar() { var B = window.CapitaoBrain; if (B && B.vozEncerrar) B.vozEncerrar(); esconde(); }
  // o ∞ do botão CONVERSA (capitao-simbolo.js) para enquanto a camada cobre a tela
  function cobre(on) { var S = window.CapitaoSimbolo; if (S && S.coberto) try { S.coberto(on); } catch (e) {} }

  // ---------- núcleo de anéis (canvas) ----------
  // Geometria numa caixa de 300 × 300 (u = raio do palco / 150), centrada no .cpz-palco. Ângulos em graus a partir do topo, sentido horário.
  var N = 48, R0 = 84, DPR_MAX = 2, RAD = Math.PI / 180;
  var ctx = null, esc = 1, larg = 0, alt = 0, cx = 0, cy = 0, R = 0, cantos = true, limpa = true;
  var raf = 0, ult = 0, tt = 0, a1 = 0, a2 = 0, a3 = 0, v2 = 9, v3 = 12, energia = 0, fixo = false, tFixo = 0, quadros = 0, sinalEm = 0;
  var cor = COR.ouvindo; // a cor em uso (fica a do último estado enquanto a camada some)
  var MC = [], MS = [], BC = [], BS = [], i0;
  for (i0 = 0; i0 < 120; i0++) { MC.push(Math.cos((i0 * 3 - 90) * RAD)); MS.push(Math.sin((i0 * 3 - 90) * RAD)); }
  for (i0 = 0; i0 < N; i0++) { BC.push(Math.cos((i0 * 360 / N - 90) * RAD)); BS.push(Math.sin((i0 * 360 / N - 90) * RAD)); }
  // o ∞ da marca: carregado uma vez; ainda não chegou ou ausente (offline sem cópia) → o ∞ traçado (infinito())
  var img = null, imgOk = false;
  function simbolo() {
    if (img) return;
    try {
      img = new Image();
      img.onload = function () { imgOk = img.naturalWidth > 0; if (!ligada()) return; if (fixo) quadroFixo(tFixo); else if (reduz) parado(); };
      img.onerror = function () { imgOk = false; };
      img.src = SIMBOLO_SRC;
    } catch (e) { img = null; imgOk = false; }
  }
  // tamanho do canvas = a caixa dele na tela × a razão de pixels (até 2); o palco em px CSS relativos ao canvas
  function ajusta() {
    if (!ctx) return;
    var b = el.tela.getBoundingClientRect(), r = Math.min(DPR_MAX, window.devicePixelRatio || 1);
    if (!b.width || !b.height) return;
    var W = Math.round(b.width * r), H = Math.round(b.height * r);
    if (el.tela.width !== W || el.tela.height !== H) { el.tela.width = W; el.tela.height = H; limpa = true; } // trocar o tamanho apaga o canvas
    esc = W / b.width; larg = b.width; alt = b.height;
    var a = el.palco.getBoundingClientRect(), x = a.left - b.left + a.width / 2, y = a.top - b.top + a.height / 2, raio = a.width / 2;
    if (x !== cx || y !== cy || raio !== R) { cx = x; cy = y; R = raio; limpa = true; }
    cantos = window.innerHeight > 720;
  }
  // energia de fundo do estado (0–1), função só do tempo: a respiração na escuta, o trabalho no processando e, na resposta, o ritmo da
  // fala — só com a voz tocando (som true). Sem som e no 'livre', repouso.
  function fundo(t) {
    if (quieto) return 0;
    var b = 0.08 + 0.04 * Math.sin(t * 2.1);
    if (estado === 'falando') { if (temSom) b = 0.3 + 0.45 * Math.abs(Math.sin(t * 8.3)) * (0.55 + 0.45 * Math.abs(Math.sin(t * 2.9 + 1.3))); }
    else if (estado === 'pensando') b = 0.2 + 0.08 * Math.sin(t * 6);
    return reduz ? Math.min(b, 0.25) : b;
  }
  function arco(r, de, ate) { ctx.beginPath(); ctx.arc(0, 0, r, (de - 90) * RAD, (ate - 90) * RAD); ctx.stroke(); }
  function infinito(w) { // o ∞ traçado (lemniscata) com as cores da marca: só enquanto a imagem não chega
    var a = w / 2, k, t, q, g = ctx.createLinearGradient(-a, 0, a, 0);
    g.addColorStop(0, '#00F4FD'); g.addColorStop(0.5, '#1F53FA'); g.addColorStop(1, '#CD3AFE');
    ctx.beginPath();
    for (k = 0; k <= 64; k++) { t = k / 64 * 2 * Math.PI; q = 1 + Math.sin(t) * Math.sin(t); if (k) ctx.lineTo(a * Math.cos(t) / q, a * Math.sin(t) * Math.cos(t) / q); else ctx.moveTo(a * Math.cos(t) / q, 0); }
    ctx.closePath(); ctx.strokeStyle = g; ctx.lineWidth = Math.max(2, w * 0.07); ctx.lineJoin = 'round'; ctx.stroke();
  }
  function desenha() {
    if (!ctx || !R) return;
    var u = R / 150, e = energia, g = cor.g, g2 = cor.g2, pens = estado === 'pensando', M = R + 16, i, k, len, ruido, gr, sc, w, p;
    ctx.setTransform(esc, 0, 0, esc, 0, 0);
    if (limpa) { ctx.clearRect(0, 0, larg, alt); limpa = false; } else ctx.clearRect(cx - M, cy - M, 2 * M, 2 * M);
    ctx.save(); ctx.translate(cx, cy); ctx.lineCap = 'butt';
    // brilho de fundo (cresce com a energia)
    gr = ctx.createRadialGradient(0, 0, 30 * u, 0, 0, 118 * u);
    gr.addColorStop(0, 'rgba(' + g + ',' + (0.10 + 0.22 * e).toFixed(3) + ')'); gr.addColorStop(1, 'rgba(' + g + ',0)');
    ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(0, 0, 118 * u, 0, 2 * Math.PI); ctx.fill();
    // aro fino de fora
    ctx.strokeStyle = 'rgba(' + g + ',0.25)'; ctx.lineWidth = Math.max(0.75, 0.8 * u); arco(148.5 * u, 0, 360);
    // anel graduado: 120 marcas, maiores a cada 30° — gira devagar
    ctx.save(); ctx.rotate(a1 * RAD);
    ctx.beginPath(); for (i = 0; i < 120; i++) if (i % 10) { ctx.moveTo(146 * u * MC[i], 146 * u * MS[i]); ctx.lineTo(141 * u * MC[i], 141 * u * MS[i]); }
    ctx.strokeStyle = 'rgba(' + g + ',0.55)'; ctx.lineWidth = Math.max(0.75, 0.8 * u); ctx.stroke();
    ctx.beginPath(); for (i = 0; i < 120; i += 10) { ctx.moveTo(146 * u * MC[i], 146 * u * MS[i]); ctx.lineTo(136 * u * MC[i], 136 * u * MS[i]); }
    ctx.strokeStyle = 'rgba(' + g + ',0.95)'; ctx.lineWidth = Math.max(1.4, 1.8 * u); ctx.stroke();
    ctx.restore();
    // anel de segmentos em arco — gira ao contrário (acelera no processando)
    ctx.save(); ctx.rotate(a2 * RAD); ctx.lineCap = 'round';
    ctx.lineWidth = Math.max(1.6, 3 * u);
    ctx.strokeStyle = 'rgb(' + g + ')'; arco(126 * u, 10, 70); arco(126 * u, 190, 280);
    ctx.strokeStyle = 'rgba(' + g2 + ',0.85)'; arco(126 * u, 130, 150); arco(126 * u, 300, 330);
    ctx.lineWidth = Math.max(0.75, u); ctx.strokeStyle = 'rgba(' + g + ',0.5)'; arco(119 * u, 40, 160); arco(119 * u, 220, 340);
    ctx.restore();
    // espectro radial: 48 barras espelhadas; no processando, uma varredura percorre as barras
    ctx.lineCap = 'round'; ctx.lineWidth = Math.max(1.2, 2 * u);
    for (i = 0; i < N; i++) {
      k = Math.min(i, N - i);
      if (pens) len = 2 + 8 * Math.max(0, Math.sin(tt * 4 - i * 0.3));
      else { ruido = 0.5 + 0.5 * Math.sin(tt * 7.1 + k * 0.55) * Math.sin(tt * 3.3 + k * 1.37); len = 2 + e * 20 * (0.35 + 0.65 * ruido); }
      ctx.strokeStyle = 'rgba(' + g + ',' + (0.3 + Math.min(0.5, len / 30)).toFixed(2) + ')';
      ctx.beginPath(); ctx.moveTo(R0 * u * BC[i], R0 * u * BS[i]); ctx.lineTo((R0 + len) * u * BC[i], (R0 + len) * u * BS[i]); ctx.stroke();
    }
    // anel interno tracejado
    ctx.save(); ctx.rotate(a3 * RAD); ctx.lineCap = 'butt'; ctx.setLineDash([2 * u, 5 * u]);
    ctx.strokeStyle = 'rgba(' + g + ',0.7)'; ctx.lineWidth = Math.max(0.9, 1.2 * u); arco(76 * u, 0, 360);
    ctx.restore();
    // núcleo: brilho, disco e o ∞ da marca (pulsa de leve com a energia)
    sc = 0.98 + e * 0.04;
    gr = ctx.createRadialGradient(0, 0, 0, 0, 0, 70 * u * sc);
    gr.addColorStop(0, 'rgba(255,255,255,0.52)'); gr.addColorStop(0.35, 'rgba(' + g + ',0.41)'); gr.addColorStop(1, 'rgba(' + g + ',0)');
    ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(0, 0, 70 * u * sc, 0, 2 * Math.PI); ctx.fill();
    ctx.fillStyle = 'rgba(5,8,22,0.88)'; ctx.beginPath(); ctx.arc(0, 0, 54 * u * sc, 0, 2 * Math.PI); ctx.fill();
    ctx.lineCap = 'butt'; ctx.strokeStyle = 'rgb(' + g + ')'; ctx.lineWidth = Math.max(1.2, 1.6 * u); arco(54 * u * sc, 0, 360);
    ctx.strokeStyle = 'rgba(' + g + ',0.35)'; ctx.lineWidth = Math.max(0.75, 0.8 * u); arco(47 * u * sc, 0, 360);
    w = 80 * u * sc;
    ctx.save(); ctx.shadowColor = 'rgba(' + g + ',0.8)'; ctx.shadowBlur = 5 * u * esc;
    if (imgOk) { try { ctx.drawImage(img, -w / 2, -w * img.naturalHeight / img.naturalWidth / 2, w, w * img.naturalHeight / img.naturalWidth); } catch (x) { imgOk = false; infinito(w); } }
    else infinito(w);
    ctx.restore();
    // colchetes nos 4 cantos do palco (somem, com o HUD, na tela baixa)
    if (cantos) {
      p = R + 5; ctx.strokeStyle = 'rgba(' + g + ',0.7)'; ctx.lineWidth = 2; ctx.lineCap = 'butt'; ctx.lineJoin = 'miter';
      ctx.beginPath();
      ctx.moveTo(-p, -p + 22); ctx.lineTo(-p, -p); ctx.lineTo(-p + 22, -p);
      ctx.moveTo(p - 22, -p); ctx.lineTo(p, -p); ctx.lineTo(p, -p + 22);
      ctx.moveTo(p, p - 22); ctx.lineTo(p, p); ctx.lineTo(p - 22, p);
      ctx.moveTo(-p + 22, p); ctx.lineTo(-p, p); ctx.lineTo(-p, p - 22);
      ctx.stroke();
    }
    ctx.restore();
    quadros++;
  }
  // SINAL do HUD: a energia 0–1 da voz, no máximo 10×/s, direto no nó de texto
  function sinal() {
    var n = ('00' + Math.round(Math.max(0, Math.min(1, energia)) * 100)).slice(-3);
    if (el.sinalT && el.sinalT.data !== n) el.sinalT.data = n;
  }
  function laco(ts) {
    raf = 0;
    if (!ligada() || d.hidden || fixo || reduz) return;
    var dt = ult ? Math.min(0.1, Math.max(0, (ts - ult) / 1000)) : 0, pens = estado === 'pensando', k = Math.min(1, dt * 4);
    ult = ts; tt += dt;
    v2 += ((pens ? 45 : 9) - v2) * k; v3 += ((pens ? 60 : 12) - v3) * k; // os anéis aceleram no processando, sem tranco
    a1 = (a1 + dt * 2) % 360; a2 = (a2 - dt * v2) % 360; a3 = (a3 + dt * v3) % 360;
    energia = Math.max(fundo(tt), energia * Math.exp(-6 * dt)); // cai sozinha; sobe com cada trecho ouvido / palavra falada
    desenha();
    if (ts - sinalEm >= 100) { sinalEm = ts; sinal(); }
    raf = requestAnimationFrame(laco);
  }
  function para() { if (raf) { cancelAnimationFrame(raf); raf = 0; } }
  function parado() { tt = 0; a1 = a2 = a3 = 0; energia = fundo(0); desenha(); sinal(); } // movimento reduzido: um quadro só, a cada mudança
  // liga a animação: um requestAnimationFrame só, com a camada ligada e a aba à vista
  function anima() {
    if (!ligada() || fixo) return;
    if (reduz) { parado(); return; }
    if (!raf && !d.hidden) { ult = 0; raf = requestAnimationFrame(laco); }
  }
  // quadro(t): o quadro do instante t (s), função só de t e do estado; o núcleo fica parado nele até a camada sumir
  function quadroFixo(t) {
    if (!d.body) return false;
    monta();
    t = typeof t === 'number' && isFinite(t) ? t : 0;
    var pens = estado === 'pensando';
    fixo = true; tFixo = t; para(); ajusta();
    tt = t; v2 = pens ? 45 : 9; v3 = pens ? 60 : 12; a1 = (t * 2) % 360; a2 = -(t * v2) % 360; a3 = (t * v3) % 360;
    energia = fundo(t); limpa = true; desenha(); sinal();
    return true;
  }
  function estadoNucleo() {
    return { estado: estado, som: temSom, alerta: emAlerta(), energia: energia, ligado: ligada(), parado: fixo, laco: !!raf, reduzido: reduz, quadros: quadros,
      simbolo: imgOk, razao: esc, x: cx, y: cy, raio: R };
  }
  var agAjuste = 0;
  function aoRedimensionar() { // tela girou ou mudou de tamanho (escondida: ajusta ao aparecer)
    if (agAjuste) return;
    agAjuste = requestAnimationFrame(function () {
      agAjuste = 0;
      if (!ligada()) return;
      if (fixo) quadroFixo(tFixo); else { ajusta(); if (reduz) parado(); }
    });
  }
  window.addEventListener('resize', aoRedimensionar);
  window.addEventListener('orientationchange', aoRedimensionar);
  d.addEventListener('visibilitychange', function () { if (d.hidden) para(); else anima(); }); // aba oculta: o laço para
  // o ∞ fica pronto antes da 1ª conversa (com o app ocioso; o capitao-simbolo.js do botão CONVERSA já pede o mesmo arquivo)
  function preCarga() { var f = function () { simbolo(); }; if (window.requestIdleCallback) requestIdleCallback(f, { timeout: 4000 }); else setTimeout(f, 1500); }
  if (d.readyState === 'complete') preCarga(); else window.addEventListener('load', preCarga);

  function pinta(e) {
    var c = COR[e]; if (!c) return;
    cor = c;
    raiz.style.setProperty('--cpz-g', c.g);
    el.rot.textContent = c.rot; el.dica.textContent = c.dica; el.modo.textContent = c.modo;
    el.btn.setAttribute('aria-label', e === 'ouvindo' ? 'Terminei de falar — enviar agora' : e === 'falando' ? 'Interromper a resposta e falar' : 'Processando');
  }
  function texto(t, vazio) {
    var novo = t || vazio || '';
    if (el.txt.textContent !== novo) el.txt.textContent = novo;
    el.txt.classList.toggle('vazio', !t);
  }
  // 1 s: o HUD lê o quadro do instante; o palco é conferido (se andou, o canvas se ajusta)
  function tique() {
    if (!ligada()) return;
    hud();
    if (!fixo) { ajusta(); if (reduz && limpa) parado(); } // movimento reduzido: só repinta se o palco andou
  }
  function mostra() {
    clearTimeout(some); some = 0;
    if (ligada()) { hud(); anima(); return; }
    var sos = d.querySelector('#dc-root a[href*="SOS-"]') || d.querySelector('a[href*="SOS-"]:not(.cpz-sos)');
    el.sos.href = sos ? sos.getAttribute('href') : (innerWidth < 600 ? 'S2-SOS-Mobile.dc.html' : 'S1-SOS-Web.dc.html');
    raiz.classList.add('on'); raiz.setAttribute('aria-hidden', 'false'); raiz.inert = false; fixo = false;
    cobre(true);
    hud();
    if (!relogio) relogio = setInterval(tique, 1000);
    ajusta(); limpa = true; desenha(); // o 1º quadro já sai agora (a camada aparece em 0,25 s)
    anima();
  }
  function esconde() {
    clearTimeout(some); some = 0; estado = 'livre'; ultTexto = ''; temSom = false; quieto = true; alertaEv = false; solto = false; energia = 0; fixo = false;
    if (!raiz) return;
    raiz.classList.remove('on'); raiz.setAttribute('aria-hidden', 'true');
    cobre(false);
    if (raiz.contains(d.activeElement)) try { d.activeElement.blur(); } catch (e) {}
    raiz.inert = true;
    clearInterval(relogio); relogio = 0;
    para(); // o último quadro esmaece junto com a camada (0,25 s)
  }
  function pulso(forca) { energia = Math.min(1, energia + (forca || 0.5)); }

  window.addEventListener('capitao-voz', function (ev) {
    var x = (ev && ev.detail) || {}, e = x.estado;
    if (!d.body) return;
    monta();
    if (e === 'pulso') { if (estado === 'falando' && temSom && !quieto) pulso(0.35); return; } // cada palavra falada: só com a voz tocando
    if (e === 'livre') { // some com atraso: na conversa o microfone religa logo depois e o overlay não pisca
      temSom = false; quieto = true; solto = true; energia = 0; // a voz parou (fim, interrupção ou erro): o espectro e o brilho zeram já, sem esperar o sumiço
      if (ligada()) { sinal(); if (reduz && !fixo) parado(); }
      if (!some && ligada()) some = setTimeout(esconde, 900);
      return;
    }
    if (!COR[e]) return;
    var novo = e !== estado; estado = e; quieto = false;
    if (novo) { pinta(e); ultTexto = ''; if (e !== 'falando') temSom = false; }
    // alerta: vale enquanto o estado segue (as linhas de uma mesma fala, os trechos de uma mesma escuta); estado novo, fala nova (depois de um
    // 'livre') ou escuta nova recomeçam. O evento sem o campo (a tela esperando a IA: vozPensando) não mexe nele.
    var comeca = novo || solto || (e === 'ouvindo' && !x.texto); solto = false;
    if ('alerta' in x) alertaEv = comeca ? !!x.alerta : alertaEv || !!x.alerta;
    if (e === 'ouvindo') {
      texto(x.texto, 'AGUARDANDO COMANDO DE VOZ…');
      if (x.texto && x.texto !== ultTexto) pulso(0.55); // trecho novo reconhecido
      ultTexto = x.texto || '';
    }
    else if (e === 'pensando') {
      texto(x.texto || '', 'CRUZANDO TELEMETRIA · AGENDA · DOCUMENTOS…'); el.dica.textContent = x.segura ? 'CONSULTANDO A IA DE BORDO…' : COR.pensando.dica; mostra();
      if (!x.segura) some = setTimeout(esconde, 2500); // sem resposta falada (voz→texto): some sozinho; esperando a IA (segura): fica até a fala
      return;
    }
    else if (e === 'falando') {
      texto(x.texto, '');
      // som: a voz está tocando (onstart) ou parou (antes de falar, fim do bloco). Sem o campo (emissor antigo): 'falando' = tocando.
      if ('som' in x) temSom = !!x.som; else if (novo) temSom = true;
      if (temSom) pulso(0.4);
    }
    mostra();
  });
  // a janela de emergência abriu ou fechou, ou o motor deu o tique do segundo (o mesmo das telas): o HUD acompanha na hora
  window.addEventListener('capitao-emergencia', function () { if (ligada()) hud(); });
  window.addEventListener('capitao-telemetria', function () { if (ligada()) hud(); });
  window.addEventListener('pagehide', esconde);

  window.CapitaoVoz = { esconde: esconde, nucleo: function () { return { quadro: quadroFixo, estado: estadoNucleo }; } };
})();
