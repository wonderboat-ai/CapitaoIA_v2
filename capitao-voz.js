/* Capitão IA — núcleo de voz (HUD do cérebro da embarcação).
   Escuta os eventos 'capitao-voz' que o capitao-brain.js emite e mostra, por cima da tela, o núcleo da IA: um rosto de
   perfil feito de partículas (capitao-rosto.js), num <canvas> em tela cheia atrás do HUD, dos textos, do ENCERRAR e do SOS.
   Cores da marca: ESCUTA ciano (#00F4FD) · PROCESSANDO violeta (#A22BFD) · RESPOSTA azul (#00A1FE).
   - ESCUTA (pergunta): o rosto respira; cada trecho reconhecido chega como partículas; mostra a transcrição.
   - PROCESSANDO: neurônios girando no crânio enquanto a resposta é montada (esperando a IA na nuvem, fica até a resposta ser falada).
   - RESPOSTA: a boca acompanha a voz (som: true/false do cérebro; 'pulso' a cada palavra) e as ondas saem dela; mostra a frase dita.
   O rosto vem à parte, com o app ocioso; se não chegar (offline sem cópia), o núcleo funciona só com os textos.
   Tocar no rosto: escuta → envia agora; resposta → interrompe e volta a ouvir. ENCERRAR (ou Esc) desliga.
   SOS sempre no canto. */
(function () {
  if (window.CapitaoVoz) return;
  var d = document, raiz = null, el = {}, estado = 'livre', some = 0, energia = 0, t0 = 0, relogio = 0, ultTexto = '', temSom = false;
  var reduz = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  var COR = {
    ouvindo: { g: '0,244,253', rot: 'ESCUTA ATIVA', modo: 'MODO · ESCUTA', dica: 'TOQUE NO NÚCLEO PARA ENVIAR' },
    pensando: { g: '162,43,253', rot: 'PROCESSANDO', modo: 'MODO · ANÁLISE', dica: '' },
    falando: { g: '0,161,254', rot: 'CAPITÃO IA', modo: 'MODO · RESPOSTA', dica: 'TOQUE NO NÚCLEO PARA INTERROMPER' }
  };
  var MONO = 'ui-monospace,"SF Mono",Menlo,Consolas,monospace';
  var FONTE = '"Nimbus Sans","Helvetica Neue",Helvetica,Arial,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif';
  // capitao-rosto.js mora ao lado deste arquivo
  var ROSTO_SRC = (function () {
    var s = d.currentScript && d.currentScript.src;
    return s && /capitao-voz\.js/.test(s) ? s.replace(/capitao-voz\.js[^\/]*$/, 'capitao-rosto.js') : 'capitao-rosto.js';
  })();

  var CSS = [
    '.cpz{position:fixed;inset:0;z-index:70;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:max(20px,env(safe-area-inset-top)) 18px max(22px,env(safe-area-inset-bottom));box-sizing:border-box;font-family:' + FONTE + ';color:#eaf6ff;opacity:0;pointer-events:none;transition:opacity .25s ease;-webkit-tap-highlight-color:transparent;--cpz-g:0,244,253}',
    '.cpz.on{opacity:1;pointer-events:auto}',
    '.cpz{overflow-y:auto;justify-content:safe center}',
    '@media (max-height:720px){.cpz-hud{display:none}.cpz{gap:10px}}',
    '.cpz-fundo{position:absolute;inset:0;background:radial-gradient(ellipse 55% 40% at 50% 40%,rgba(var(--cpz-g),0.06) 0%,rgba(var(--cpz-g),0) 70%),rgba(5,8,22,0.95);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px)}',
    '.cpz-tela{position:absolute;inset:0;width:100%;height:100%;display:block;pointer-events:none}',
    '.cpz-hud{position:absolute;font:600 10px/1.55 ' + MONO + ';letter-spacing:0.12em;color:rgba(var(--cpz-g),0.85);pointer-events:none;white-space:nowrap}',
    '.cpz-hud b{color:#fff;font-weight:700}',
    '.cpz-tl{top:max(66px,calc(env(safe-area-inset-top) + 58px));left:18px}.cpz-tr{top:max(66px,calc(env(safe-area-inset-top) + 58px));right:18px;text-align:right}',
    // o palco é a caixa de medida do rosto e a área de toque (o rosto pode subir além dele)
    '.cpz-palco{position:relative;width:min(64vmin,36vh,300px);height:min(64vmin,36vh,300px);flex-shrink:0}',
    '.cpz-btn{position:absolute;inset:0;border:0;padding:0;background:transparent;border-radius:50%;cursor:pointer;outline:none;-webkit-tap-highlight-color:transparent}',
    '.cpz-btn:focus-visible{box-shadow:0 0 0 2px rgba(var(--cpz-g),0.9)}',
    '.cpz-rot{position:relative;font:800 12px/1 ' + MONO + ';letter-spacing:0.3em;color:rgb(var(--cpz-g));text-shadow:0 0 14px rgba(var(--cpz-g),0.8);min-height:14px;display:flex;align-items:center;gap:10px}',
    '.cpz-rot:before,.cpz-rot:after{content:"";width:34px;height:1px;background:linear-gradient(90deg,rgba(var(--cpz-g),0),rgba(var(--cpz-g),0.9))}.cpz-rot:after{transform:scaleX(-1)}',
    // legenda com altura fixa de 3 linhas (também no texto vazio, menor): o palco não anda quando ela muda de linhas —
    // senão o rosto refazia a geometria inteira (malha, névoa) a cada trecho ouvido
    '.cpz-txt{position:relative;flex-shrink:0;max-width:min(580px,92vw);height:calc(4.5 * clamp(15px,2vw,18px));font-size:clamp(15px,2vw,18px);line-height:1.5;text-align:center;color:#f2f8ff;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}',
    '.cpz-txt.vazio{color:rgba(var(--cpz-g),0.7);font-family:' + MONO + ';font-size:13px;letter-spacing:0.08em}',
    '.cpz-dica{position:relative;font:700 10px/1 ' + MONO + ';letter-spacing:0.2em;color:rgba(234,246,255,0.55);min-height:12px;text-align:center}',
    '.cpz-acoes{position:relative;display:flex;gap:10px}',
    '.cpz-fim{height:48px;padding:0 22px;border-radius:12px;border:1px solid rgba(var(--cpz-g),0.45);background:rgba(var(--cpz-g),0.08);color:#eaf6ff;font:800 12px/1 ' + MONO + ';letter-spacing:0.2em;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:10px}',
    '.cpz-fim:hover,.cpz-fim:focus-visible{border-color:rgb(var(--cpz-g));box-shadow:0 0 18px rgba(var(--cpz-g),0.35);outline:none}',
    '.cpz-sos{position:absolute;top:max(14px,env(safe-area-inset-top));left:16px;z-index:2;height:40px;padding:0 16px;border-radius:12px;background:#d32f27;color:#fff;font:800 13px/1 ' + FONTE + ';letter-spacing:0.1em;display:flex;align-items:center;text-decoration:none;box-shadow:0 0 0 3px rgba(255,59,48,0.25)}'
  ].join('\n');

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
    raiz.inert = true; // escondida (ela já fica montada com o app ocioso): os botões dela fora do Tab
    raiz.innerHTML = '<div class="cpz-fundo"></div><canvas class="cpz-tela" aria-hidden="true"></canvas>' +
      '<a class="cpz-sos" aria-label="SOS — emergência">SOS</a>' +
      '<div class="cpz-hud cpz-tl">CAPITÃO IA · NÚCLEO<br><span class="cpz-modo"></span><br>SINAL <b class="cpz-sinal">000</b></div>' +
      '<div class="cpz-hud cpz-tr"><b class="cpz-hora">--:--</b><br><span class="cpz-pos"></span></div>' +
      '<div class="cpz-palco"><button type="button" class="cpz-btn"></button></div>' +
      '<div class="cpz-rot" aria-live="polite"></div><div class="cpz-txt"></div><div class="cpz-dica"></div>' +
      '<div class="cpz-acoes"><button type="button" class="cpz-fim"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true" style="flex-shrink:0"><path d="M6 6l12 12 M18 6L6 18" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/></svg>ENCERRAR</button></div>';
    d.body.appendChild(raiz);
    el = { btn: raiz.querySelector('.cpz-btn'), rot: raiz.querySelector('.cpz-rot'), txt: raiz.querySelector('.cpz-txt'), dica: raiz.querySelector('.cpz-dica'), fim: raiz.querySelector('.cpz-fim'), sos: raiz.querySelector('.cpz-sos'), modo: raiz.querySelector('.cpz-modo'), sinal: raiz.querySelector('.cpz-sinal'), hora: raiz.querySelector('.cpz-hora'), pos: raiz.querySelector('.cpz-pos'), tela: raiz.querySelector('.cpz-tela'), palco: raiz.querySelector('.cpz-palco') };
    el.sinalT = el.sinal.firstChild;
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

  // ---------- rosto (capitao-rosto.js): carregado uma vez com o app ocioso; antes do 1º núcleo, também com o app ocioso e em
  // pedaços (um toque nunca espera o cálculo inteiro): a malha, a camada montada escondida com o rosto criado nela e o 1º
  // quadro adiantado — o toque no CONVERSA só liga a camada ----------
  var rosto = null, carga = 0, ajustar = false, medida = '', agMede = 0, pausa = 0; // carga: 0 nada · 1 carregando · 2 pronto · 3 falhou
  function ocioso(fn, ms) { if (window.requestIdleCallback) requestIdleCallback(fn, { timeout: ms }); else setTimeout(fn, 1500); }
  function prazoDe(p) { // tempo livre que o navegador deu; vencido o prazo do ocioso (app sempre ocupado), um pedaço de ~5 ms
    if (!p || typeof p.timeRemaining !== 'function') return p;
    var t0 = performance.now();
    return { timeRemaining: function () { return p.didTimeout ? 8 - (performance.now() - t0) : p.timeRemaining(); } };
  }
  function prepara(p) {
    if (rosto || !window.CapitaoRosto || (raiz && raiz.classList.contains('on'))) return;
    var feito = true;
    try { feito = window.CapitaoRosto.preparar(prazoDe(p)) !== false; } catch (e) { return; }
    ocioso(feito ? preCria : prepara, 1000);
  }
  function preCria() {
    if (rosto || !window.CapitaoRosto || !d.body || d.hidden) return; // aba escondida: o rosto nasce na 1ª abertura
    if (!raiz) { monta(); ocioso(preCria, 1000); return; }
    if (raiz.classList.contains('on')) return;
    criaRosto();
    if (!rosto) return;
    rosto.pausar(); ocioso(aquece, 1000);
  }
  function aquece() {
    if (!rosto || !rosto.aquecer || raiz.classList.contains('on')) return; // abriu: o laço do rosto faz o resto
    var feito = true;
    try { feito = rosto.aquecer(); } catch (e) {}
    if (!feito) ocioso(aquece, 1000);
  }
  function carregaRosto() {
    if (window.CapitaoRosto) { carga = 2; return; }
    if (carga === 1) return;
    carga = 1;
    var s = d.createElement('script'); s.src = ROSTO_SRC; s.async = true;
    s.onload = function () {
      carga = window.CapitaoRosto ? 2 : 3; if (carga !== 2) return;
      if (raiz && raiz.classList.contains('on')) criaRosto(); // o núcleo abriu antes de o rosto chegar: cria agora
      else ocioso(prepara, 3000);
    };
    s.onerror = function () { carga = 3; if (s.parentNode) s.parentNode.removeChild(s); }; // sem rede e sem cópia: só os textos (tenta de novo na próxima abertura)
    (d.head || d.documentElement).appendChild(s);
  }
  function criaRosto() {
    if (rosto || !raiz || !window.CapitaoRosto) return;
    try {
      rosto = window.CapitaoRosto.criar(el.tela, { reduzido: reduz, dprMax: 2, fpsMax: 60, crescer: 0.35 });
      mede(true, true);
      if (COR[estado]) { rosto.estado(estado); if (estado === 'falando') rosto.som(temSom); }
    } catch (e) { rosto = null; }
  }
  // palco (caixa .cpz-palco) em px CSS relativos ao canvas; só avisa o rosto se mudou (ele refaz a geometria). escondido: na
  // criação — a camada montada já tem o layout de quando aparece (a legenda tem altura fixa)
  function mede(forca, escondido) {
    agMede = 0;
    if (!rosto || (!escondido && !raiz.classList.contains('on'))) return;
    var a = el.palco.getBoundingClientRect(), b = el.tela.getBoundingClientRect(), x = a.left - b.left, y = a.top - b.top;
    var k = Math.round(x) + ',' + Math.round(y) + ',' + Math.round(a.width) + ',' + Math.round(a.height);
    if (!forca && k === medida) return;
    medida = k; rosto.palco(x, y, a.width, a.height);
  }
  function remede() { if (rosto && !agMede) agMede = requestAnimationFrame(function () { mede(false); }); } // o texto mudou: confere o palco
  function ajusta() { // tela girou ou mudou de tamanho
    if (!rosto) return;
    if (!raiz.classList.contains('on')) { ajustar = true; return; } // escondido: ajusta ao aparecer
    ajustar = false; rosto.redimensionar(); mede(true);
  }
  var agAjuste = 0;
  function aoRedimensionar() { if (!agAjuste) agAjuste = requestAnimationFrame(function () { agAjuste = 0; ajusta(); }); }
  window.addEventListener('resize', aoRedimensionar);
  window.addEventListener('orientationchange', aoRedimensionar);
  function preCarga() { ocioso(carregaRosto, 4000); }
  if (d.readyState === 'complete') preCarga(); else window.addEventListener('load', preCarga);

  function pinta(e) {
    var c = COR[e]; if (!c) return;
    raiz.style.setProperty('--cpz-g', c.g);
    el.rot.textContent = c.rot; el.dica.textContent = c.dica; el.modo.textContent = c.modo;
    el.btn.setAttribute('aria-label', e === 'ouvindo' ? 'Terminei de falar — enviar agora' : e === 'falando' ? 'Interromper a resposta e falar' : 'Processando');
  }
  function texto(t, vazio) {
    var novo = t || vazio || '';
    if (el.txt.textContent !== novo) { el.txt.textContent = novo; remede(); }
    el.txt.classList.toggle('vazio', !t);
  }
  function mostra() {
    clearTimeout(some); some = 0;
    if (raiz.classList.contains('on')) return;
    var sos = d.querySelector('#dc-root a[href*="SOS-"]') || d.querySelector('a[href*="SOS-"]:not(.cpz-sos)');
    el.sos.href = sos ? sos.getAttribute('href') : (innerWidth < 600 ? 'S2-SOS-Mobile.dc.html' : 'S1-SOS-Web.dc.html');
    el.hora.textContent = window.CapitaoClima ? window.CapitaoClima.hora() : new Date().toTimeString().slice(0, 5);
    el.pos.innerHTML = hudPosicao();
    raiz.classList.add('on'); raiz.setAttribute('aria-hidden', 'false'); raiz.inert = false;
    cobre(true);
    t0 = performance.now();
    if (!relogio) relogio = setInterval(sinal, 100);
    if (rosto) {
      clearTimeout(pausa); pausa = 0;
      if (ajustar) { ajustar = false; rosto.redimensionar(); mede(true); } else mede(false);
      rosto.retomar();
    } else if (window.CapitaoRosto) criaRosto();
    else if (carga !== 1) carregaRosto(); // ainda não veio (ou falhou): pede agora; o rosto entra quando chegar
  }
  function esconde() {
    clearTimeout(some); some = 0; estado = 'livre'; ultTexto = ''; temSom = false;
    if (!raiz) return;
    raiz.classList.remove('on'); raiz.setAttribute('aria-hidden', 'true');
    cobre(false);
    if (raiz.contains(d.activeElement)) try { d.activeElement.blur(); } catch (e) {}
    raiz.inert = true;
    clearInterval(relogio); relogio = 0; energia = 0;
    if (rosto) { // esmaece junto com a camada (0,25 s) e para
      rosto.estado('livre'); clearTimeout(pausa);
      pausa = setTimeout(function () { pausa = 0; if (rosto && !raiz.classList.contains('on')) rosto.pausar(); }, 300);
    }
  }
  // SINAL do HUD: energia 0–1 da voz — cai sozinha; sobe com cada trecho ouvido/palavra falada; com a voz tocando, uma
  // oscilação imita o ritmo da fala. No máximo 10×/s, direto no nó de texto (não aciona o MutationObserver do capitao-app.js).
  function sinal() {
    if (!raiz.classList.contains('on')) return;
    var t = (performance.now() - t0) / 1000, base = 0.08 + 0.04 * Math.sin(t * 2.1);
    if (estado === 'falando') base = temSom ? 0.3 + 0.45 * Math.abs(Math.sin(t * 8.3)) * (0.55 + 0.45 * Math.abs(Math.sin(t * 2.9 + 1.3))) : 0.1;
    else if (estado === 'pensando') base = 0.2 + 0.08 * Math.sin(t * 6);
    if (reduz) base = Math.min(base, 0.25);
    energia = Math.max(base, energia * 0.55);
    var n = ('00' + Math.round(energia * 100)).slice(-3);
    if (el.sinalT && el.sinalT.data !== n) el.sinalT.data = n;
  }
  function pulso(forca) { energia = Math.min(1, energia + (forca || 0.5)); }

  window.addEventListener('capitao-voz', function (ev) {
    var x = (ev && ev.detail) || {}, e = x.estado;
    if (!d.body) return;
    monta();
    if (e === 'pulso') { pulso(0.35); if (rosto) rosto.pulso(0.55); return; }
    if (e === 'livre') { // some com atraso: na conversa o microfone religa logo depois e o overlay não pisca
      temSom = false; if (rosto) rosto.som(false); // a voz parou (fim, interrupção ou erro): a boca fecha já, sem esperar o sumiço
      if (!some && raiz.classList.contains('on')) some = setTimeout(esconde, 900);
      return;
    }
    if (!COR[e]) return;
    var novo = e !== estado; estado = e;
    if (novo) { pinta(e); ultTexto = ''; if (e !== 'falando') temSom = false; }
    if (rosto) rosto.estado(e);
    if (e === 'ouvindo') {
      texto(x.texto, 'AGUARDANDO COMANDO DE VOZ…');
      if (x.texto && x.texto !== ultTexto) { pulso(0.55); if (rosto) rosto.pulso(0.7); } // trecho novo reconhecido
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
      if (rosto) rosto.som(temSom);
      if (temSom) pulso(0.4);
    }
    mostra();
  });
  window.addEventListener('pagehide', esconde);

  // rosto(): o rosto criado (ou null: ainda não chegou / sem canvas) — para os testes
  window.CapitaoVoz = { esconde: esconde, rosto: function () { return rosto; } };
})();
