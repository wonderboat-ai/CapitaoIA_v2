/* Capitão IA — publicação (GitHub Pages · app instalável).
   1) Garante as metas de app em toda prancheta (viewport, manifest, ícones, iOS).
   2) No site publicado (janela de topo): ajusta a prancheta à janela —
      celular = ocupa a largura da tela (rola se precisar; deitado fica em 1:1); computador/tablet = cabe inteira, centralizada.
   3) Registra o service worker no site publicado e em localhost (testes) — abre offline depois da 1ª visita.
   4) Põe o rodapé (versão · selo DEMO · usuário · crédito) logo abaixo da prancheta — definido em capitao-auth.js.
   5) Celular: SOS flutuante quando o SOS da tela sai da vista.
   Dentro do editor (iframe) só faz o passo 1. */
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
  link('icon', './assets/favicon_64.png', 'image/png');
  link('apple-touch-icon', './assets/apple-touch-icon.png');

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
    location.replace(alvo + '.dc.html' + location.hash);
    function safe(s) { try { return decodeURIComponent(s); } catch (e) { return s; } }
  })();

  // Service worker: site publicado (GitHub Pages ou domínio próprio) e testes locais.
  var HOSTS = /(^|\.)(wonderboat-ai\.github\.io|capitaoia\.com\.br)$|^(localhost|127\.0\.0\.1|\[::1\])$/i;
  if ('serviceWorker' in navigator && HOSTS.test(location.hostname)) {
    window.addEventListener('load', function () { navigator.serviceWorker.register('./sw.js').catch(function () {}); });
  }

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
    if (!phone) vh = Math.max(200, vh - rh); // no computador o rodapé fica visível sob a prancheta
    var z = phone ? (vw > vh ? Math.min(vw / W, 1) : vw / W) : Math.min(vw / W, vh / H);
    z = Math.max(0.25, Math.min(z, 2));
    if (Math.abs(z - 1) < 0.005) z = 1;
    var zs = z === 1 ? '' : String(Math.floor(z * 1000) / 1000); // para baixo: nunca passa 1px da tela (barra de rolagem à toa)
    if (el.style.zoom !== zs) el.style.zoom = zs;
    var mt = phone ? 0 : Math.max(0, Math.floor((vh - H * z) / 2));
    var mts = mt ? (mt / z).toFixed(2) + 'px' : '';
    if (el.style.marginTop !== mts) el.style.marginTop = mts;
    if (el.style.marginLeft !== 'auto') { el.style.marginLeft = 'auto'; el.style.marginRight = 'auto'; }
    if (olhaEstilo) olhaEstilo.takeRecords(); // o que este fit() escreveu não chama outro fit() (senão oscila com barra de rolagem)
    if (phone) sosFixo(el);
  }
  // Celular: a prancheta tem altura fixa e, com a barra do navegador, o SOS da tela pode ficar abaixo da dobra.
  // Enquanto o SOS da página não estiver à vista, um SOS fixo no canto leva à mesma tela de emergência.
  var sosEl = null, sosVisto = null, sosObs = null;
  function sosFixo(el) {
    // A barra SOS da tela (fixa, acima do assistente) manda; link de SOS dentro do conteúdo rolável só na falta dela.
    var alvo = el.querySelector('capitao-sos-app a[href*="SOS-"]') || el.querySelector('a[href*="SOS-"]');
    if (!alvo || !window.IntersectionObserver) return;
    if (!sosEl) {
      sosEl = d.createElement('a'); sosEl.textContent = 'SOS'; sosEl.setAttribute('aria-label', 'SOS — emergência');
      sosEl.style.cssText = 'position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom, 0px));z-index:50;width:64px;height:64px;border-radius:50%;background:var(--cap-crit-fill, #d32f27);color:#fff;display:none;align-items:center;justify-content:center;text-decoration:none;font:800 16px/1 "Nimbus Sans","Helvetica Neue",Helvetica,Arial,sans-serif;letter-spacing:.08em;box-shadow:0 0 0 4px rgba(255,59,48,.3),0 10px 28px rgba(211,47,39,.5);';
      d.body.appendChild(sosEl);
      sosObs = new IntersectionObserver(function (es) { var v = es[es.length - 1].isIntersecting; sosEl.style.display = v ? 'none' : 'flex'; });
    }
    sosEl.href = alvo.getAttribute('href');
    if (sosVisto !== alvo) { if (sosVisto) sosObs.unobserve(sosVisto); sosVisto = alvo; sosObs.observe(alvo); }
  }
  function schedule() { if (!raf) raf = requestAnimationFrame(fit); }
  window.addEventListener('resize', schedule);
  window.addEventListener('orientationchange', schedule);
  function start() {
    if (!/Manual-/.test(location.pathname) && !d.querySelector('deck-stage') && window.customElements && customElements.get('capitao-rodape') && !d.querySelector('capitao-rodape')) {
      rodape = d.createElement('capitao-rodape'); d.body.appendChild(rodape);
    }
    schedule();
    if (window.MutationObserver) { new MutationObserver(schedule).observe(d.body, { childList: true, subtree: true }); olhaEstilo = new MutationObserver(schedule); }
  }
  if (d.body) start(); else d.addEventListener('DOMContentLoaded', start);
})();
