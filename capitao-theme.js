/* Capitão IA — tema claro/escuro.
   Toda cor das telas usa var(--cap-*, <cor do tema escuro>). Escuro = sem variáveis (o fallback é a cor exata).
   Claro = as variáveis abaixo no :root. Preferência por aparelho em localStorage (capitao.tema.v1).
   Paleta: manual da marca WonderHUB.AI (26/09/2026) — ciano #00F4FD (foco: telemetria, voz), azul #00A1FE (ação),
   violeta #A22BFD (acentos), azul profundo #050816 (fundo), branco. Estados (ok/atenção/crítico) são funcionais.
   No claro, ciano, azul e violeta ficam mais escuros para manter contraste ≥ 4,5:1 sobre o branco.
   Violeta no escuro: texto e ícone usam --cap-violeta (#b45cff, tom da marca legível sobre #050816); brilhos e gradientes
   usam --cap-violeta-rgb (162,43,253 = #A22BFD exato). */
(function () {
  if (window.CapitaoTheme) return;
  var KEY = 'capitao.tema.v1';
  var LIGHT = {
    '--cap-bg': '#f3f6fc', '--cap-bg-rgb': '243,246,252', '--cap-bar': '#e7ecf6', '--cap-bar-rgb': '231,236,246',
    '--cap-card': '#ffffff', '--cap-card-rgb': '255,255,255', '--cap-card2-rgb': '244,247,252', '--cap-card3-rgb': '255,255,255',
    '--cap-elev': '#edf1f8', '--cap-row': '#f4f7fc', '--cap-modal': '#ffffff',
    '--cap-line': '#d5dcea', '--cap-line2': '#bfc9dc', '--cap-dash': '#8f9ab2', '--cap-track': '#dfe5f0',
    '--cap-ink': '#081026', '--cap-ink2': '#2c3857', '--cap-ink2-rgb': '44,56,87', '--cap-ink3': '#414e6d', '--cap-ink3-rgb': '65,78,109',
    '--cap-ink4': '#56627f', '--cap-ph': '#7b86a2', '--cap-greet': '#56627f', '--cap-hi': '#081026', '--cap-hl-rgb': '8,16,38',
    '--cap-wm-top': '#081026', '--cap-wm-bot': '#6d7896', '--cap-plat': '#5d6a8a', '--cap-plat-rgb': '80,92,122',
    '--cap-accent': '#0068c9', '--cap-accent-rgb': '0,104,201', '--cap-accent-hi': '#1f86e6', '--cap-accent-soft': '#0059ad',
    '--cap-link-hover': '#00539f', '--cap-on-accent': '#ffffff', '--cap-on-accent2': '#d6e9ff',
    '--cap-tele': '#00798a', '--cap-tele-rgb': '0,121,138', '--cap-violeta': '#7d16d6', '--cap-violeta-rgb': '125,22,214',
    '--cap-ok': '#12804a', '--cap-ok-rgb': '18,128,74', '--cap-warn': '#9c5a00', '--cap-warn-rgb': '156,90,0',
    '--cap-crit': '#c42a20', '--cap-crit-rgb': '196,42,32', '--cap-crit-fill': '#c42a20', '--cap-critfill-rgb': '196,42,32',
    '--cap-shadow-rgb': '22,32,60', '--cap-shadow-k': '0.28'
  };
  function get() { try { return localStorage.getItem(KEY) === 'claro' ? 'claro' : 'escuro'; } catch (e) { return 'escuro'; } }
  function apply(t) {
    var r = document.documentElement; if (!r) return;
    for (var k in LIGHT) { if (t === 'claro') r.style.setProperty(k, LIGHT[k]); else r.style.removeProperty(k); }
    r.setAttribute('data-capitao-tema', t);
    r.style.colorScheme = t === 'claro' ? 'light' : 'dark';
    var tc = document.querySelector('meta[name="theme-color"]'); if (tc) tc.setAttribute('content', t === 'claro' ? '#f3f6fc' : '#050816');
    try { window.dispatchEvent(new CustomEvent('capitao-tema', { detail: t })); } catch (e) {}
  }
  function set(t) { t = t === 'claro' ? 'claro' : 'escuro'; try { localStorage.setItem(KEY, t); } catch (e) {} apply(t); }
  function toggle() { set(get() === 'claro' ? 'escuro' : 'claro'); }
  window.addEventListener('storage', function (e) { if (!e || e.key === KEY || e.key === null) apply(get()); });
  window.CapitaoTheme = { KEY: KEY, get: get, set: set, toggle: toggle, apply: apply };
  apply(get());

  var SUN = 'M12 4v2 M12 18v2 M4 12h2 M18 12h2 M6.3 6.3l1.4 1.4 M16.3 16.3l1.4 1.4 M6.3 17.7l1.4-1.4 M16.3 7.7l1.4-1.4 M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7z';
  var MOON = 'M19.5 14.2A7.6 7.6 0 0 1 9.8 4.5a7.6 7.6 0 1 0 9.7 9.7z';
  if (!window.customElements || customElements.get('capitao-theme-toggle')) return;
  var NS = 'http://www.w3.org/2000/svg';
  // <capitao-theme-toggle size="40"> — sol/lua; alvo de toque ≥ 44 px mesmo quando o círculo é menor.
  customElements.define('capitao-theme-toggle', class extends HTMLElement {
    connectedCallback() {
      if (!this._b) this.build();
      this._on = this.render.bind(this);
      window.addEventListener('capitao-tema', this._on);
      this.render();
    }
    disconnectedCallback() { window.removeEventListener('capitao-tema', this._on); }
    build() {
      var size = Math.max(24, parseInt(this.getAttribute('size') || '40', 10) || 40);
      var hit = Math.max(size, 44), pad = (hit - size) / 2;
      this.style.cssText = 'display:inline-flex;flex-shrink:0;width:' + size + 'px;height:' + size + 'px;';
      var b = document.createElement('button');
      b.type = 'button';
      b.style.cssText = 'width:' + hit + 'px;height:' + hit + 'px;margin:-' + pad + 'px;padding:0;border:0;background:transparent;display:flex;align-items:center;justify-content:center;cursor:pointer;-webkit-tap-highlight-color:transparent;font:inherit;';
      var c = document.createElement('span');
      c.style.cssText = 'box-sizing:border-box;width:' + size + 'px;height:' + size + 'px;border-radius:50%;border:1px solid var(--cap-line, #1a2240);background:var(--cap-card, #0d1329);color:var(--cap-ink2, #b1bdd6);display:flex;align-items:center;justify-content:center;transition:border-color .25s, color .25s;';
      var svg = document.createElementNS(NS, 'svg'); var ic = Math.round(size * 0.46);
      svg.setAttribute('width', ic); svg.setAttribute('height', ic); svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('fill', 'none'); svg.setAttribute('aria-hidden', 'true');
      svg.style.flexShrink = '0';
      var p = document.createElementNS(NS, 'path');
      p.setAttribute('stroke', 'currentColor'); p.setAttribute('stroke-width', '1.8'); p.setAttribute('stroke-linecap', 'round'); p.setAttribute('stroke-linejoin', 'round');
      svg.appendChild(p); c.appendChild(svg); b.appendChild(c); this.appendChild(b);
      b.addEventListener('click', function () { toggle(); });
      b.addEventListener('mouseenter', function () { c.style.borderColor = 'rgba(var(--cap-plat-rgb, 211,220,239), 0.55)'; c.style.color = 'var(--cap-ink, #eaf1ff)'; });
      b.addEventListener('mouseleave', function () { c.style.borderColor = 'var(--cap-line, #1a2240)'; c.style.color = 'var(--cap-ink2, #b1bdd6)'; });
      b.addEventListener('focus', function () { c.style.borderColor = 'var(--cap-accent, #00a1fe)'; });
      b.addEventListener('blur', function () { c.style.borderColor = 'var(--cap-line, #1a2240)'; });
      this._b = b; this._p = p;
    }
    render() {
      var claro = get() === 'claro';
      this._p.setAttribute('d', claro ? MOON : SUN);
      this._b.setAttribute('aria-pressed', claro ? 'true' : 'false');
      this._b.setAttribute('aria-label', claro ? 'Tema claro ativo — mudar para escuro' : 'Tema escuro ativo — mudar para claro');
      this._b.title = claro ? 'Tema escuro' : 'Tema claro';
    }
  });
})();
