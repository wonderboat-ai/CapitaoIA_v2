/* Capitão IA — publicação (GitHub Pages · app instalável).
   1) Garante as metas de app em toda prancheta (viewport, manifest, ícones, iOS).
   2) No site publicado (janela de topo): ajusta a prancheta à janela —
      celular = ocupa a largura da tela (rola se precisar; deitado fica em 1:1); computador/tablet = cabe inteira, centralizada.
   3) Registra o service worker no site publicado e em localhost (testes) — abre offline depois da 1ª visita.
   4) Põe o rodapé (versão · usuário · crédito) logo abaixo da prancheta — definido em capitao-auth.js.
   5) Celular: SOS flutuante quando o SOS da tela sai da vista.
   6) Faixa global de alerta (F05): o alerta aberto no topo de toda tela de uso, «ABRIR ›» → C3; a prancheta começa abaixo dela (nunca no SOS, no Manual nem na C3).
   7) `window.CapitaoEmergencia`: a marca ÚNICA da janela de conversa em emergência (15 min), que as telas de conversa gravam e a faixa lê (trava 10).
   Dentro do editor (iframe) só faz o passo 1 (e define a marca do passo 7, que não toca a tela). */
(function () {
  if (window.__capitaoApp) return; window.__capitaoApp = true;
  var d = document, head = d.head || d.documentElement;
  var ua = navigator.userAgent || '';
  var iOS = /iPhone|iPad|iPod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  function meta(name, content, overwrite) {
    var m = d.querySelector('meta[name="' + name + '"]');
    if (m && !overwrite) return;
    if (!m) { m = d.createElement('meta'); m.setAttribute('name', name); head.appendChild(m); }
    m.setAttribute('content', content);
  }
  function link(rel, href, type) {
    if (d.querySelector('link[rel="' + rel + '"]')) return;
    var l = d.createElement('link'); l.rel = rel; l.href = href; if (type) l.type = type; head.appendChild(l);
  }
  // iOS: maximum-scale evita o zoom automático ao tocar em campos (o gesto de pinça continua funcionando).
  meta('viewport', 'width=device-width, initial-scale=1, viewport-fit=cover' + (iOS ? ', maximum-scale=1' : ''), true);
  meta('theme-color', d.documentElement.getAttribute('data-capitao-tema') === 'claro' ? '#f3f6fc' : '#050816');
  meta('apple-mobile-web-app-capable', 'yes');
  meta('mobile-web-app-capable', 'yes');
  meta('apple-mobile-web-app-status-bar-style', 'black');
  meta('apple-mobile-web-app-title', 'Capitão IA');
  link('manifest', './manifest.webmanifest');
  link('icon', './assets/wonderhub-favicon.ico'); // ∞ WonderHUB.AI, 16/32/48 px
  link('apple-touch-icon', './assets/wonderhub-apple-touch-icon.png');

  // ——— A marca da janela de conversa em emergência (P4A; PROMPT §2.2; CLAUDE.md 10) ———
  // Depois de uma resposta que traz `a.abreJanela === true` (sos, oleo, canal16, epirb, seafire, diário com alerta, cartão EM do FAQ), a TELA DE CONVERSA chama CapitaoEmergencia.marca() (agora + 15 min,
  // B.JANELA_EMERG_MS) e CapitaoEmergencia.zera() em NOVA e ENCERRAR; enquanto valendo() é true ela passa `{ emergencia: true }` ao cérebro (answer, pedeIA, ficha, resumoAgora, …). É a mesma marca para
  // todo mundo: a faixa global lê aqui (não tem a tela de conversa por perto) e passa `{ emergencia: true }` a B.alarmesPedidosAtivos — o alarme pedido de velocidade sai sem limite nem leitura. A marca vale
  // pela aba (sessionStorage `capitao.emergenciaAte`, o fim em ms; sem storage, só nesta página), com o relógio de verdade (Date.now: a janela é de conversa, não do quadro) e avisa com o evento
  // 'capitao-emergencia' {ate, valendo}. Nada é gravado em localStorage, no registro nem fora do aparelho.
  (function () {
    var K = 'capitao.emergenciaAte', JANELA = 15 * 60 * 1000, mem = 0;
    function le() {
      var v = mem;
      try { var s = sessionStorage.getItem(K); if (s !== null && s !== '') { var n = Number(s); if (isFinite(n) && n > v) v = n; } } catch (e) {}
      return v > 0 ? v : 0;
    }
    function avisa() { try { window.dispatchEvent(new CustomEvent('capitao-emergencia', { detail: { ate: le(), valendo: valendo() } })); } catch (e) {} }
    function valendo() { return le() > Date.now(); }
    function marca(ate) {   // sem argumento: agora + 15 min; com um número (ms do relógio), esse fim (nunca mais de 15 min adiante)
      var t = Date.now(), n = typeof ate === 'number' && isFinite(ate) ? Math.min(ate, t + JANELA) : t + JANELA;
      mem = n; try { sessionStorage.setItem(K, String(n)); } catch (e) {}
      avisa(); return n;
    }
    function zera() { mem = 0; try { sessionStorage.removeItem(K); } catch (e) {} avisa(); }
    window.CapitaoEmergencia = { JANELA_MS: JANELA, CHAVE: K, ate: le, valendo: valendo, marca: marca, zera: zera };
  })();

  var topWin = true; try { topWin = window.top === window.self; } catch (e) { topWin = false; }
  if (!topWin) return;

  // Fundo fora do <x-dc>: o boot do support.js troca o <x-dc> (e o <style> do helmet) pelo #dc-root — sem isto pisca um quadro branco.
  var fundo = d.createElement('style'); fundo.textContent = 'html{background:var(--cap-bg,#050816)}'; head.appendChild(fundo);

  // Celular abrindo uma tela web → vai para a tela equivalente do app.
  // Respeita a escolha "Sempre web" (index.html?v=web) e quem veio da lista de telas (?v=lista).
  (function () {
    var K = 'capitao.plataforma.v1';
    var pick = null, lista = false;
    try { pick = localStorage.getItem(K); lista = sessionStorage.getItem('capitao.lista') === '1'; } catch (e) {}
    var v = new URLSearchParams(location.search).get('v');
    if (v === 'web' || v === 'app') { pick = v; try { localStorage.setItem(K, v); } catch (e) {} }
    if (pick === 'web' || lista) return;
    var APP = {
      'Main': 'H2-Home-Mobile', 'A1-Ponte-Web': 'A2-Ponte-Mobile', 'B1-Carta-Web': 'B2-Carta-Mobile', 'C1-Leme-Web': 'C2-Leme-Mobile',
      'F1-FAQ-Hub-Web': 'F1-FAQ-Hub', 'F2-FAQ-Estabilizador-Web': 'F2-FAQ-Estabilizador', 'F3-FAQ-Eletronicos-Web': 'F3-FAQ-Eletronicos',
      'F4-FAQ-Gerador-Web': 'F4-FAQ-Gerador', 'F5-FAQ-Climatizacao-Web': 'F5-FAQ-Climatizacao',
      'G1-Documentos-Web': 'G1-Documentos-Mobile', 'G2-Abastecimento-Web': 'G2-Abastecimento-Mobile', 'G3-Diario-Web': 'G3-Diario-Mobile',
      'G4-Equipe-Web': 'G4-Equipe-Mobile', 'H3-Atalhos-Editar-Web': 'H3-Atalhos-Editar', 'S1-SOS-Web': 'S2-SOS-Mobile'
    };
    var m = location.pathname.match(/([^\/]+)\.dc\.html$/);
    var alvo = m && APP[safe(m[1])];
    if (!alvo) return;
    if (pick !== 'app') {
      var uad = navigator.userAgentData;
      var mobileUA = uad && typeof uad.mobile === 'boolean' ? uad.mobile : /Android.+Mobile|iPhone|iPod|Windows Phone|IEMobile|Opera Mini/i.test(ua);
      var shortSide = Math.min(screen.width || 9999, screen.height || 9999);
      var coarse = !!(window.matchMedia && matchMedia('(pointer: coarse)').matches);
      var estreita = Math.min(window.innerWidth || 9999, d.documentElement.clientWidth || 9999) < 900; // tablet em pé / janela pequena
      if (!(mobileUA || (coarse && shortSide < 600) || estreita)) return;
    }
    window.CapitaoRedirecionando = true; // esta tela está sendo trocada: o capitao-ia.js não abre a caixa da chave aqui
    location.replace(alvo + '.dc.html' + location.hash);
    function safe(s) { try { return decodeURIComponent(s); } catch (e) { return s; } }
  })();

  // Service worker: site publicado (GitHub Pages ou domínio próprio) e testes locais.
  var HOSTS = /(^|\.)(wonderboat-ai\.github\.io|capitaoia\.com\.br)$|^(localhost|127\.0\.0\.1|\[::1\])$/i;
  if ('serviceWorker' in navigator && HOSTS.test(location.hostname)) {
    window.addEventListener('load', function () { navigator.serviceWorker.register('./sw.js').catch(function () {}); });
    // App instalado fica aberto dias (o Android traz a mesma tela ao tocar no ícone, sem recarregar): ao voltar para a
    // frente, procura versão nova (no máximo 1 vez por minuto). Achando, o SW novo instala, assume e recarrega as telas
    // abertas (sw.js › activate).
    var procurou = 0, recarregar = false;
    d.addEventListener('visibilitychange', function () {
      if (d.visibilityState !== 'visible') { if (recarregar && !/SOS-/.test(location.pathname)) location.reload(); return; }
      if (!navigator.serviceWorker.getRegistration) return;
      var agora = new Date().getTime(); if (agora - procurou < 60000) return; procurou = agora;
      navigator.serviceWorker.getRegistration().then(function (r) { if (r) return r.update(); }).catch(function () {});
    });
    // Versão nova ativou (sw.js › activate avisa 'nova-versao'): esta tela responde que cuida da recarga e recarrega num
    // momento seguro — com a tela no fundo, ou sem texto sendo digitado, conversa por voz aberta ou resposta a caminho.
    // Assim a recarga não fecha a caixa da chave nem apaga o que o usuário escrevia. Tela que não responde (versão
    // anterior) o SW recarrega sozinho. O SOS nunca recarrega sozinho.
    navigator.serviceWorker.addEventListener('message', function (e) {
      if (!e.data || e.data.tipo !== 'nova-versao') return;
      try { if (e.source && e.source.postMessage) e.source.postMessage({ tipo: 'versao-ok' }); } catch (x) {}
      if (/SOS-/.test(location.pathname)) return;
      recarregar = true; quandoPuder();
    });
  }
  function ocupado() {
    if (d.querySelector('.cpz.on') || d.querySelector('[data-capitao-pensando]')) return true; // conversa por voz / resposta a caminho
    var campos = d.querySelectorAll('input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=file]), textarea');
    for (var i = 0; i < campos.length; i++) if (String(campos[i].value || '').trim()) return true; // texto digitado
    var a = d.activeElement; return !!(a && a.isContentEditable);
  }
  function quandoPuder() {
    if (d.visibilityState !== 'visible' || !ocupado()) { location.reload(); return; }
    setTimeout(quandoPuder, 3000);
  }

  // ——— Faixa global de alerta (F05; PROMPT Fase 4 «Faixa global de alerta») ———
  // Faixa fixa no topo de toda tela de uso com o alerta mais grave aberto (os do CapitaoAlertas — o replay — mais os alarmes pedidos no chat, B.alarmesPedidosAtivos,
  // quando o cérebro está na tela), «ABRIR ›» → C3-Leme-Alerta.dc.html#alarme=<id> (o alarme pedido não tem tela de detalhe: vai para a lista de alertas da Ponte). Empurra a
  // prancheta (fit() reserva a altura dela) e nunca a cobre. Só AVISO: o crítico existe apenas com `cenario: 'alarme-critico'` no gerador (desligado). Nunca troca de tela,
  // nunca abre a C3 sozinha, nunca fala (nada de speechSynthesis), nunca grava no registro e não tem timer: acompanha o 'capitao-telemetria' (1 s) e o 'capitao-alerta' do replay.
  // Fora: S1/S2 (nem carregam o capitao-alertas.js: o SOS nunca muda de lugar), o Manual, a própria C3, o deck-stage e as páginas que não são tela. Com a CONVERSA aberta
  // (ocupado()) a faixa se mantém e as regiões do leitor de tela calam até ela fechar. Os textos entram em nós Text (a troca de caractere não dispara o fit() do MutationObserver).
  var FX = 'capitao-faixa-alertas', ARQ = '', faixa = null, fx = null, fxStatus = null, fxAlerta = null, fxAltura = -1, fxSig = '', fxFalado = '', fxEm = false, fxDitos = Object.create(null);
  try { ARQ = decodeURIComponent(location.pathname.split('/').pop() || ''); } catch (e) { ARQ = ''; }
  var FX_CSS = '#' + FX + '{position:fixed;left:0;right:0;top:0;z-index:60;box-sizing:border-box;margin:0;padding-top:env(safe-area-inset-top,0px);font:600 13.5px/1.3 "Nimbus Sans","Helvetica Neue",Helvetica,Arial,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;letter-spacing:0;text-align:left;color:var(--cap-ink,#eaf1ff);background:linear-gradient(rgba(var(--cap-warn-rgb,240,166,58),.16),rgba(var(--cap-warn-rgb,240,166,58),.16)),var(--cap-card,#0d1329);box-shadow:inset 0 -2px 0 var(--cap-warn,#f0a63a),0 6px 18px rgba(0,0,0,.22)}' +
    '#' + FX + '[hidden]{display:none}' +
    '#' + FX + '[data-nivel="critico"]{background:var(--cap-crit-fill,#d32f27);color:#fff;box-shadow:0 6px 18px rgba(0,0,0,.28)}' +
    '#' + FX + ' .cpf-ic,#' + FX + ' .cpf-n{color:var(--cap-warn,#f0a63a)}#' + FX + '[data-nivel="critico"] .cpf-ic,#' + FX + '[data-nivel="critico"] .cpf-n{color:#fff}' +
    '#' + FX + ' a{display:block;min-height:44px;box-sizing:border-box;padding:6px max(16px,env(safe-area-inset-right,0px)) 6px max(16px,env(safe-area-inset-left,0px));color:inherit;text-decoration:none;cursor:pointer;-webkit-tap-highlight-color:transparent}' +
    '#' + FX + ' a:focus{outline:none}#' + FX + ' a:focus-visible{outline:2px solid currentColor;outline-offset:-4px;border-radius:8px}' +
    '#' + FX + ' a:hover .cpf-abrir{text-decoration:underline}' +
    '.cpf-in{display:flex;align-items:center;gap:10px;max-width:1100px;min-height:30px;margin:0 auto}.cpf-ic{flex-shrink:0;width:18px;height:18px}' +
    '.cpf-t{flex:1 1 auto;min-width:0;display:flex;flex-wrap:wrap;align-items:baseline;column-gap:6px;row-gap:1px}' +
    '.cpf-x{min-width:0;overflow:hidden;overflow-wrap:anywhere;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2}.cpf-n{font-weight:800;letter-spacing:.08em}' +
    '.cpf-s{flex-shrink:0;font-weight:500;font-size:12px;opacity:.9;white-space:nowrap}' +
    '.cpf-mais{flex-shrink:0;font-weight:800;font-size:12px;line-height:1;padding:3px 7px;border:1.5px solid currentColor;border-radius:999px}.cpf-mais:empty{display:none}' +
    '.cpf-abrir{flex-shrink:0;display:inline-flex;align-items:center;font-weight:800;font-size:12.5px;letter-spacing:.1em;white-space:nowrap}' +
    '.cpf-sr{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0 0 0 0)!important;clip-path:inset(50%)!important;white-space:nowrap!important;border:0!important}' +
    '@media (min-width:600px){.cpf-s::before{content:"· "}}@media print{#' + FX + '{display:none!important}}';
  var FX_ICONE = 'M12 4 21 20H3z M12 10v4 M12 17h.01';
  // só a tela de uso já listada: o SOS, o Manual (apresentação), a C3 (a própria tela do alerta) e o deck-stage ficam sem faixa, e sem a API de alertas também (o SOS nunca a carrega)
  function temFaixa() { return /\.dc\.html$/.test(ARQ) && !/^(Manual-|C3-|S[12]-SOS-)/.test(ARQ) && !/SOS-/.test(location.pathname) && !d.querySelector('deck-stage') && !!window.CapitaoAlertas; }
  function conversaAberta() { return !!d.querySelector('.cpz.on'); }
  function larguraArt() { var el = art(); return el ? parseFloat(el.style.width) : 0; }
  function ponte() { return (larguraArt() > 0 && larguraArt() <= 430 ? 'A2-Ponte-Mobile.dc.html' : 'A1-Ponte-Web.dc.html') + '#alertas'; }
  function fxPeso(n) { return n === 'critico' ? 2 : 1; }
  function fxAntes(x, y) {   // crítico antes de aviso; no mesmo nível o mais antigo (o que não tem começo conhecido — desdeMs null — vai para o fim); por fim o id
    var dx = x.desdeMs === null ? Infinity : x.desdeMs, dy = y.desdeMs === null ? Infinity : y.desdeMs;
    return fxPeso(y.nivel) - fxPeso(x.nivel) || (dx < dy ? -1 : dx > dy ? 1 : 0) || (x.id < y.id ? -1 : x.id > y.id ? 1 : 0);
  }
  function fxPedidos() {   // alarmes pedidos no chat só se houver algum guardado (a conta varre até 160 s por regra: não roda à toa a cada segundo)
    var B = window.CapitaoBrain, v = '';
    if (!B || typeof B.alarmesPedidosAtivos !== 'function') return [];
    try { v = localStorage.getItem('capitao.alarmes.v1') || ''; } catch (e) { return []; }
    if (v.length < 3) return [];
    try { var l = B.alarmesPedidosAtivos(undefined, { emergencia: emergenciaValendo() }); return Array.isArray(l) ? l : []; } catch (e) { return []; }   // com a janela de emergência valendo a velocidade sai sem limite nem leitura (CLAUDE.md 10)
  }
  function emergenciaValendo() { var E = window.CapitaoEmergencia; try { return !!(E && E.valendo()); } catch (e) { return false; } }
  function fxLista() {
    var A = window.CapitaoAlertas, l = [];
    try { l = A && typeof A.ativos === 'function' ? A.ativos() : []; } catch (e) { l = []; }
    l = (Array.isArray(l) ? l : []).filter(function (a) { return a && typeof a.id === 'string' && a.id && (a.nivel === 'aviso' || a.nivel === 'critico'); })
      .map(function (a) { return { id: a.id, nivel: a.nivel, rotulo: a.rotulo || (a.nivel === 'critico' ? 'CRÍTICO' : 'AVISO'), texto: String(a.texto || ''), desdeMs: typeof a.desdeMs === 'number' ? a.desdeMs : null, desdeTxt: typeof a.desdeMs === 'number' && a.hora ? 'desde ' + a.hora : 'agora', detalhe: typeof a.detalhe === 'string' ? a.detalhe : '', pedido: false }; });
    fxPedidos().forEach(function (a) {
      if (!a || typeof a.id !== 'string' || !a.id || a.nivel !== 'aviso') return;   // o alarme pedido é sempre AVISO
      l.push({ id: a.id, nivel: 'aviso', rotulo: a.rotulo || 'AVISO', texto: String(a.texto || ''), desdeMs: typeof a.desdeMs === 'number' ? a.desdeMs : null, desdeTxt: String(a.desdeTxt || ''), detalhe: typeof a.detalhe === 'string' ? a.detalhe : '', pedido: true });
    });
    return l.sort(fxAntes);
  }
  function fxEstilo() {
    if (d.getElementById('capitao-faixa-css')) return;
    var st = d.createElement('style'); st.id = 'capitao-faixa-css'; st.textContent = FX_CSS; head.appendChild(st);
  }
  function fxMonta() {
    if (faixa) return;
    fxEstilo();
    faixa = d.createElement('div'); faixa.id = FX; faixa.hidden = true;   // sem role: o leitor de tela é avisado pela região escondida (o texto da faixa muda a cada segundo)
    faixa.innerHTML = '<a href="#"><span class="cpf-in"><svg class="cpf-ic" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="' + FX_ICONE + '" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></svg>' +
      '<span class="cpf-t"><span class="cpf-x"><b class="cpf-n"></b> <span class="cpf-tx"></span></span><span class="cpf-s"></span></span><span class="cpf-mais" aria-hidden="true"></span>' +
      '<span class="cpf-abrir">ABRIR ›</span></span></a>';
    var q = function (s) { var e = faixa.querySelector(s), t = d.createTextNode(''); e.appendChild(t); return t; };
    fx = { a: faixa.firstChild, nivel: q('.cpf-n'), texto: q('.cpf-tx'), desde: q('.cpf-s'), mais: q('.cpf-mais'), maisEl: faixa.querySelector('.cpf-mais'), desdeEl: faixa.querySelector('.cpf-s') };
    fx.a.addEventListener('click', function () { fx.a.href = fxDestino(fx.alerta); });   // o destino na hora do toque
    d.body.insertBefore(faixa, d.body.firstChild);   // a 1ª parada do Tab
  }
  function fxDestino(a) { return a ? (a.detalhe || ponte()) : ponte(); }
  function fxEscreve(t, v) { if (t.data !== v) t.data = v; }
  function fxAtr(e, k, v) { if (e.getAttribute(k) !== v) e.setAttribute(k, v); }
  // as duas regiões para o leitor de tela existem desde o início (região viva precisa estar no documento antes do texto)
  function fxRegioes() {
    if (fxStatus) return;
    fxEstilo();
    fxStatus = d.createElement('div'); fxStatus.id = 'capitao-faixa-status'; fxStatus.className = 'cpf-sr'; fxStatus.setAttribute('role', 'status'); fxStatus.setAttribute('aria-live', 'polite');
    fxAlerta = d.createElement('div'); fxAlerta.id = 'capitao-faixa-anuncio'; fxAlerta.className = 'cpf-sr'; fxAlerta.setAttribute('role', 'alert');
    d.body.appendChild(fxStatus); d.body.appendChild(fxAlerta);
  }
  // reserva a altura da faixa no fit() e reajusta a prancheta na hora em que ela aparece, some ou muda de altura (um fit() só por mudança: o schedule junta os pedidos)
  function fxPosiciona() {
    if (!faixa) return;
    var h = faixa.hidden ? 0 : faixa.offsetHeight;
    if (h !== fxAltura) { fxAltura = h; try { window.dispatchEvent(new CustomEvent('capitao-topo')); } catch (e) {} }
  }
  function fxEsconde() { if (faixa && !faixa.hidden) { faixa.hidden = true; fxPosiciona(); } fxSig = ''; }
  // quem é novo para o leitor de tela: o id que o CapitaoAlertas ainda não anunciou nesta sessão (anunciar() devolve true só na 1ª vez) e o alarme pedido que esta página ainda não disse
  function fxNovos(l) {
    var A = window.CapitaoAlertas;
    return l.filter(function (a) {
      if (a.pedido) { if (fxDitos[a.id]) return false; fxDitos[a.id] = true; return true; }
      try { return !!(A && typeof A.anunciar === 'function' && A.anunciar(a.id)); } catch (e) { return false; }
    });
  }
  function fxFrase(a) { return (a.nivel === 'critico' ? 'Alerta crítico: ' : 'Aviso: ') + a.texto + (a.desdeTxt ? ', ' + a.desdeTxt : '') + '.'; }
  function fxRenderiza() {
    if (!d.body) return;
    if (!temFaixa()) { fxEsconde(); return; }
    var l = fxLista(), a = l[0], n, sig, novos, msg, em = emergenciaValendo();
    if (em !== fxEm) {   // a janela de emergência abriu ou fechou: o que as regiões do leitor de tela disseram antes (com a leitura de velocidade) sai de lá; limpar não anuncia nada
      fxEm = em;
      if (fxStatus) fxStatus.textContent = '';
      if (fxAlerta) fxAlerta.textContent = '';
    }
    if (!l.length) { fxEsconde(); return; }
    fxMonta(); fxRegioes();
    n = l.length - 1; fx.alerta = a;
    fxAtr(faixa, 'data-nivel', a.nivel);
    fxEscreve(fx.nivel, a.rotulo);
    fxEscreve(fx.texto, a.texto);
    fxEscreve(fx.desde, a.desdeTxt);
    fx.desdeEl.hidden = !a.desdeTxt;
    fxEscreve(fx.mais, n > 0 ? '+' + n : '');
    fxAtr(fx.a, 'href', fxDestino(a));
    fxAtr(fx.a, 'aria-label', 'Abrir o alerta: ' + a.texto + (n > 0 ? ', e mais ' + n + (n === 1 ? ' alerta' : ' alertas') : ''));
    if (faixa.hidden) faixa.hidden = false;
    fxPosiciona();
    // leitor de tela: a região educada diz o 1º alerta (e quantos mais) só quando ele muda; o crítico novo sai assertivo, uma vez; com a CONVERSA aberta nada é dito
    sig = a.id + '|' + a.nivel + '|' + l.length;
    if (conversaAberta()) return;   // (antes do fxNovos: o que ficou calado continua novo e é dito quando a conversa fechar)
    novos = fxNovos(l);
    msg = fxFrase(a) + (n > 0 ? ' E mais ' + n + (n === 1 ? ' alerta.' : ' alertas.') : '');
    if (sig !== fxSig || novos.length) {
      fxSig = sig;
      if (novos.some(function (x) { return x.nivel === 'critico'; })) { if (fxFalado !== 'c' + sig) { fxFalado = 'c' + sig; fxAlerta.textContent = ''; fxAlerta.textContent = msg; } }
      else if (novos.length && fxFalado !== 's' + sig) { fxFalado = 's' + sig; fxStatus.textContent = ''; fxStatus.textContent = msg; }
    }
  }
  function fxLiga() {
    if (!d.body || !temFaixa()) return;
    fxRegioes();
    ['capitao-telemetria', 'capitao-alerta', 'capitao-rebase', 'capitao-sessao', 'capitao-emergencia'].forEach(function (e) { window.addEventListener(e, fxRenderiza); });
    d.addEventListener('visibilitychange', function () { if (!d.hidden) fxRenderiza(); });
    window.addEventListener('resize', fxPosiciona);
    fxRenderiza();   // o 1º tique da página sai antes de qualquer ouvinte: lê já o que está aberto
  }

  // Versões misturadas: logo depois de publicar, o celular podia rodar o capitao-auth.js novo (rodapé com a versão nova) com
  // o capitao-brain.js ou o capitao-ia.js velhos, vindos do cache HTTP do aparelho (o GitHub Pages manda "max-age=600").
  // Resultado: a IA nem era chamada e voltava o SEM DADOS de antes. Na 1ª vez que isso aparece nesta sessão, busca de novo
  // na rede (cache 'reload') os arquivos e a tela, e recarrega. Não repete na mesma sessão (sem laço se a rede falhar).
  // O SOS fica de fora: ele funciona com versões misturadas e nunca vale recarregar no meio de uma emergência. Só recarrega
  // se ao menos um arquivo chegou da rede; senão libera nova tentativa na próxima abertura.
  window.addEventListener('load', function () {
    setTimeout(function () {
      var A = window.CapitaoAuth, B = window.CapitaoBrain, I = window.CapitaoIA, v = A && A.VERSAO && A.VERSAO.v;
      if (!v || /SOS-/.test(location.pathname)) return;
      var arq = [];
      if (B && B.VERSAO !== v) arq.push('./capitao-brain.js');
      if (I && I.VERSAO !== v) arq.push('./capitao-ia.js');
      if (!arq.length) return;
      var K = 'capitao.recarga.v1';
      try { if (sessionStorage.getItem(K) === v) return; sessionStorage.setItem(K, v); } catch (e) { return; }
      arq = arq.concat(['./capitao-auth.js', './capitao-app.js', location.pathname]);
      Promise.all(arq.map(function (u) { return fetch(u, { cache: 'reload', credentials: 'same-origin' }).catch(function () { return null; }); }))
        .then(function (rs) {
          if (rs.some(function (r) { return r && r.ok; })) location.reload();
          else { try { sessionStorage.removeItem(K); } catch (e) {} }
        });
    }, 1200);
  });

  var raf = 0, rodape = null, atual = null, olhaEstilo = null;
  // Só a prancheta já desenhada (#dc-root): mexer no modelo escondido dentro do <x-dc> fazia o React apagar o zoom depois.
  function art() {
    var c = d.querySelectorAll('#dc-root [style*="width: 1440px"],#dc-root [style*="width: 390px"],#dc-root [style*="width: 2380px"]');
    for (var i = 0; i < c.length; i++) {
      var s = c[i].style;
      if (/px$/.test(s.width) && parseFloat(s.height) >= 600) return c[i];
    }
    return null;
  }
  // Altura ocupada no topo pela faixa de alerta (a base dela); 0 sem faixa à vista. O ResizeObserver só pede novo ajuste quando a altura muda (texto que quebra em 2 linhas).
  var olhaTopo = null, topoVisto = null, topoAltura = -1;
  function topo() {
    var e = d.getElementById(FX);
    if (!e || e.hidden || !e.offsetHeight) { topoAltura = 0; return 0; }
    if (window.ResizeObserver && topoVisto !== e) {
      if (olhaTopo) olhaTopo.disconnect();
      olhaTopo = new ResizeObserver(function () { if (e.offsetHeight !== topoAltura) schedule(); });
      olhaTopo.observe(e); topoVisto = e;
    }
    topoAltura = e.offsetHeight;
    return Math.max(0, Math.ceil(e.getBoundingClientRect().bottom));
  }
  function fit() {
    raf = 0;
    // A apresentação escala sozinha. Sem a trilha de miniaturas do editor: aqui ninguém aplica excluir/duplicar/mover e ela travaria.
    var ds = d.querySelector('deck-stage');
    if (ds) { if (!ds.hasAttribute('no-rail')) ds.setAttribute('no-rail', ''); return; }
    var el = art(); if (!el) return;
    // Se um novo desenho do React reescrever o style da prancheta, ajusta de novo.
    if (el !== atual && olhaEstilo) { atual = el; olhaEstilo.disconnect(); olhaEstilo.observe(el, { attributes: true, attributeFilter: ['style'] }); }
    var W = parseFloat(el.style.width), H = parseFloat(el.style.height);
    var de = d.documentElement;
    var vw = de.clientWidth || window.innerWidth, vh = de.clientHeight || window.innerHeight;
    // Celular deitado (tela de toque baixa) continua celular; janela baixa no computador segue cabendo inteira.
    var phone = W <= 430 && (vw < 600 || (vh < 600 && !!(window.matchMedia && matchMedia('(pointer: coarse)').matches)));
    var rh = rodape && rodape.isConnected ? Math.max(rodape.offsetHeight, rodape.scrollHeight) : 0;
    var tp = topo(); // a faixa de alerta fixa no topo (se houver): a prancheta começa abaixo dela, no celular e no computador
    if (!phone) vh = Math.max(200, vh - rh - tp); // no computador o rodapé fica visível sob a prancheta
    var z = phone ? (vw > vh ? Math.min(vw / W, 1) : vw / W) : Math.min(vw / W, vh / H);
    z = Math.max(0.25, Math.min(z, 2));
    if (Math.abs(z - 1) < 0.005) z = 1;
    var zs = z === 1 ? '' : String(Math.floor(z * 1000) / 1000); // para baixo: nunca passa 1px da tela (barra de rolagem à toa)
    if (el.style.zoom !== zs) el.style.zoom = zs;
    var mt = (phone ? 0 : Math.max(0, Math.floor((vh - H * z) / 2))) + tp;
    var mts = mt ? (mt / z).toFixed(2) + 'px' : '';
    if (el.style.marginTop !== mts) el.style.marginTop = mts;
    if (el.style.marginLeft !== 'auto') { el.style.marginLeft = 'auto'; el.style.marginRight = 'auto'; }
    if (olhaEstilo) olhaEstilo.takeRecords(); // o que este fit() escreveu não chama outro fit() (senão oscila com barra de rolagem)
    if (phone) sosFixo(el);
  }
  // Celular: a prancheta tem altura fixa e, com a barra do navegador, o SOS da tela pode ficar abaixo da dobra.
  // Enquanto o SOS da página não estiver à vista, um SOS fixo no canto leva à mesma tela de emergência.
  var sosEl = null, sosVisto = null, sosObs = null, SOS_VISTA = 0.95;
  function sosFixo(el) {
    // A barra SOS da tela (fixa, acima do assistente) manda; link de SOS dentro do conteúdo rolável só na falta dela.
    var alvo = el.querySelector('capitao-sos-app a[href*="SOS-"]') || el.querySelector('a[href*="SOS-"]');
    if (!alvo || !window.IntersectionObserver) return;
    if (!sosEl) {
      sosEl = d.createElement('a'); sosEl.textContent = 'SOS'; sosEl.setAttribute('aria-label', 'SOS — emergência');
      sosEl.style.cssText = 'position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom, 0px));z-index:50;width:64px;height:64px;border-radius:50%;background:var(--cap-crit-fill, #d32f27);color:#fff;display:none;align-items:center;justify-content:center;text-decoration:none;font:800 16px/1 "Nimbus Sans","Helvetica Neue",Helvetica,Arial,sans-serif;letter-spacing:.08em;box-shadow:0 0 0 4px rgba(255,59,48,.3),0 10px 28px rgba(211,47,39,.5);';
      d.body.appendChild(sosEl);
      // A barra só conta como «à vista» quando está (quase) inteira: com a faixa de alerta empurrando a prancheta, ou numa tela mais baixa, sobra um filete dela na dobra (isIntersecting já é true com
      // 1 px) e o SOS fixo ficava escondido justamente nessa hora. 0,95 e não 1: a zoom da prancheta arredonda a borda em meio pixel.
      sosObs = new IntersectionObserver(function (es) { var e = es[es.length - 1], v = e.isIntersecting && e.intersectionRatio >= SOS_VISTA; sosEl.style.display = v ? 'none' : 'flex'; }, { threshold: [0, 0.25, 0.5, 0.75, 0.9, SOS_VISTA, 1] });
    }
    sosEl.href = alvo.getAttribute('href');
    if (sosVisto !== alvo) { if (sosVisto) sosObs.unobserve(sosVisto); sosVisto = alvo; sosObs.observe(alvo); }
  }
  function schedule() { if (!raf) raf = requestAnimationFrame(fit); }
  window.addEventListener('resize', schedule);
  window.addEventListener('orientationchange', schedule);
  window.addEventListener('capitao-topo', schedule);   // a faixa de alerta apareceu, sumiu ou mudou de altura (junta com os outros pedidos num fit() só)
  function start() {
    if (!/Manual-/.test(location.pathname) && !d.querySelector('deck-stage') && window.customElements && customElements.get('capitao-rodape') && !d.querySelector('capitao-rodape')) {
      rodape = d.createElement('capitao-rodape'); d.body.appendChild(rodape);
    }
    schedule();
    fxLiga();
    if (window.MutationObserver) { new MutationObserver(schedule).observe(d.body, { childList: true, subtree: true }); olhaEstilo = new MutationObserver(schedule); }
  }
  if (d.body) start(); else d.addEventListener('DOMContentLoaded', start);
})();
