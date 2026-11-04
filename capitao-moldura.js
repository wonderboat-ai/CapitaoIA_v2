/* Capitão IA — moldura comum das telas do console (web) e do app.
   Um lugar só para o que se repete em toda tela; o conteúdo de cada tela fica na própria prancheta.
   Web (1440 × 900):
     <capitao-cabecalho>            marca · embarcação e registro · estado e posição · leitura (SNAPSHOT/AO VIVO) · tema · avatar (68 px)
     <capitao-trilho ativo="manut">  trilho de 9 seções: Início · Gestão · Telemetria · Manutenção · Documentos · Abastecer · Diário · FAQ · Equipe
     <capitao-faixa>                faixa de leitura: SOG · PROA · VENTO · 24 V · ÁGUA DOCE · DIESEL (com hora) · estado · hora · INÍCIO ›
     <capitao-sos-web>              SOS circular no canto (acima da faixa)
   App (390 × 844):
     <capitao-topo-app titulo="…" voltar="…">  cabeçalho de 44 px: voltar · marca · título · leitura · tema · avatar
     <capitao-sos-app>              barra SOS · EMERGÊNCIA (acima da barra do assistente)
   Dados: capitao-dados.js (snapshot com hora) ou capitao-telemetria.js (ao vivo, se ligada). Sem dado → "—" / SEM DADOS.
   Tudo em light DOM (sem shadow): o tema chega pelas variáveis --cap-* e o SOS flutuante (capitao-app.js) acha o link do SOS.
   Montagem: o cabeçalho, a faixa e o topo do app montam o HTML UMA vez (connectedCallback) e guardam os nós de texto; a cada tique do motor
   (1 s) só trocam o `data` do nó que mudou (e atributos/LED só quando o valor muda). Nada de textContent/innerText/innerHTML no tique: eles geram
   mutação childList, que dispara o fit() do capitao-app.js e recria o <capitao-theme-toggle> e o avatar (o botão do tema perderia o foco do teclado). */
(function () {
  if (window.CapitaoMoldura) return;
  var FONTE = '"Nimbus Sans","Helvetica Neue",Helvetica,Arial,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif';
  var MONO = 'ui-monospace,"SF Mono",Menlo,Consolas,monospace';
  var SECOES = [
    { k: 'inicio', l: 'Início', web: 'Main.dc.html', app: 'H2-Home-Mobile.dc.html', d: 'M4 11l8-7 8 7v9H4z' },
    { k: 'gestao', l: 'Gestão', web: 'B1-Carta-Web.dc.html', app: 'B2-Carta-Mobile.dc.html', d: 'M4 5h16v14H4z M4 10h16 M9 10v9' },
    { k: 'telemetria', l: 'Telemetria', web: 'A1-Ponte-Web.dc.html', app: 'A2-Ponte-Mobile.dc.html', d: 'M3 16c2-3 4-3 6 0s4 3 6 0 4-3 6 0M3 9c2-3 4-3 6 0s4 3 6 0 4-3 6 0' },
    { k: 'manut', l: 'Manutenção', web: 'C1-Leme-Web.dc.html', app: 'C2-Leme-Mobile.dc.html', d: 'M14.7 6.3a4 4 0 0 0-5.4 5.4L4 17v3h3l5.3-5.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.5-.5-.5-2.5z' },
    { k: 'docs', l: 'Documentos', web: 'G1-Documentos-Web.dc.html', app: 'G1-Documentos-Mobile.dc.html', d: 'M6 3h8l4 4v14H6z M14 3v4h4' },
    { k: 'abast', l: 'Abastecer', web: 'G2-Abastecimento-Web.dc.html', app: 'G2-Abastecimento-Mobile.dc.html', d: 'M5 20V6a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v14 M4 20h12 M15 9h2a2 2 0 0 1 2 2v5a1.5 1.5 0 0 0 3 0V8l-3-3 M8 8h4' },
    { k: 'diario', l: 'Diário', web: 'G3-Diario-Web.dc.html', app: 'G3-Diario-Mobile.dc.html', d: 'M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z M8 20a3 3 0 0 1 0-6h11' },
    { k: 'faq', l: 'FAQ', web: 'F1-FAQ-Hub-Web.dc.html', app: 'F1-FAQ-Hub.dc.html', d: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 .9-1 1.7 M12 17h.01' },
    { k: 'equipe', l: 'Equipe', web: 'G4-Equipe-Web.dc.html', app: 'G4-Equipe-Mobile.dc.html', d: 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M3 20a6 6 0 0 1 12 0 M16 11a3 3 0 1 0 0-6 M21 20a6 6 0 0 0-5-5.9' }
  ];
  var PIN = 'M12 21s6-6 6-11a6 6 0 0 0-12 0c0 5 6 11 6 11z M12 12a2 2 0 1 0 0-4 2 2 0 0 0 0 4z';
  var ANCORA = 'M12 2.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z M12 7.5V21 M4 13a8 8 0 0 0 16 0 M2.5 13H6 M18 13h3.5';
  var VOLTAR = 'M15 5l-7 7 7 7';

  function D() { return window.CapitaoDados || {}; }
  function nb(x, d) { return typeof x === 'number' && isFinite(x) ? x.toFixed(d == null ? 1 : d).replace('.', ',') : '—'; }
  function g3(x) { return typeof x === 'number' ? ('00' + Math.round(((x % 360) + 360) % 360)).slice(-3) + '°' : '—'; }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function svg(d, n, sw, cor) { return '<svg width="' + n + '" height="' + n + '" viewBox="0 0 24 24" fill="none" aria-hidden="true" style="flex-shrink:0;display:block"><path d="' + d + '" stroke="' + (cor || 'currentColor') + '" stroke-width="' + (sw || 1.8) + '" stroke-linecap="round" stroke-linejoin="round"/></svg>'; }

  // Leitura para cabeçalho e faixa: ao vivo (< 10 min) ou snapshot, sempre com hora e origem.
  function leitura() {
    var d = D(), S = d.snapshot || {}, T = window.CapitaoTelemetria, v = T && T.atual ? T.atual() : null, di = S.diesel || {};
    var diesel = typeof di.bb === 'number' ? Math.round((di.bb + di.be) / 2) + '% · ' + (di.hora || '') : 'SEM DADOS';
    if (v) return { vivo: true, hora: T.hora(v), rotulo: 'Ao vivo · ' + T.hora(v), pos: T.posicao(v), estado: (v.sog_nos >= 1 ? 'Navegando' : 'Parado'), local: '',
      faixa: [['SOG', nb(v.sog_nos) + ' NÓ'], ['PROA', g3(v.proa_graus)], ['VENTO', nb(v.vento_verdadeiro_nos) + ' NÓS'], ['24 V', nb(v.bateria_0_tensao_v, 2) + ' V'], ['ÁGUA DOCE', Math.round(v.tanque_agua_pct) + '%'], ['DIESEL', diesel]] };
    var tq = S.tanques || {};
    return { vivo: false, hora: S.hora || '—', rotulo: 'Snapshot' + (d.demo ? ' DEMO' : '') + ' · ' + (S.quando ? S.quando.slice(0, 5) + ' ' + S.hora : 'SEM DADOS'),
      pos: (S.gps && S.gps.texto) || 'SEM LEITURA', estado: S.estado || 'SEM DADOS', local: S.local || '',
      faixa: [['SOG', nb(S.sog) + ' NÓ'], ['PROA', g3(S.proa)], ['VENTO', nb(S.vento) + ' NÓS'], ['24 V', nb(S.bat24, 2) + ' V'], ['ÁGUA DOCE', typeof tq.agua === 'number' ? Math.round(tq.agua) + '%' : '—'], ['DIESEL', diesel]] };
  }

  function css() {
    if (document.getElementById('capitao-moldura-css')) return;
    var s = document.createElement('style'); s.id = 'capitao-moldura-css';
    s.textContent =
      '@keyframes capMolduraVivo{0%,100%{opacity:1}50%{opacity:.25}}' +
      'capitao-cabecalho,capitao-trilho,capitao-faixa,capitao-topo-app,capitao-sos-app{display:block;box-sizing:border-box;font-family:' + FONTE + '}' +
      '.cpm-a:focus-visible,.cpm-nav a:focus-visible{outline:2px solid var(--cap-accent,#00a1fe);outline-offset:2px}' +
      '.cpm-nav a:hover{background:rgba(var(--cap-plat-rgb,211,220,239),.08);color:var(--cap-ink,#eaf1ff)}' +
      '@media (prefers-reduced-motion:reduce){.cpm-led{animation:none!important}}';
    document.head.appendChild(s);
  }
  // Ouvintes: um par por instância (cabeçalho e faixa da web são duas). Idempotente: ligar de novo desliga o anterior; desligar sem ter ligado não faz nada.
  function viva(el) { morta(el); el._on = function () { el.atualiza(); }; window.addEventListener('capitao-telemetria', el._on); window.addEventListener('capitao-sessao', el._on); }
  function morta(el) { if (!el._on) return; window.removeEventListener('capitao-telemetria', el._on); window.removeEventListener('capitao-sessao', el._on); el._on = null; }
  // Nós de texto: `no` põe um nó Text vazio dentro do elemento marcado com data-cpm="k"; `poe` só escreve quando o valor mudou (escrever o mesmo valor
  // também gera mutação de caractere); `atr` faz o mesmo com um atributo; `troca` substitui um nó por outro montado do HTML (o LED, só quando o estado vira).
  function no(raiz, k) { var e = raiz.querySelector('[data-cpm="' + k + '"]'), t = document.createTextNode(''); e.appendChild(t); return t; }
  function poe(t, v) { if (t.data !== v) t.data = v; }
  function atr(e, k, v) { if (e.getAttribute(k) !== v) e.setAttribute(k, v); }
  function cria(html) { var m = document.createElement('template'); m.innerHTML = html; return m.content.firstChild; }
  function troca(velho, html) { var novo = cria(html); velho.parentNode.replaceChild(novo, velho); return novo; }
  function led(vivo, n) {
    return vivo ? '<span class="cpm-led" aria-hidden="true" style="width:' + n + 'px;height:' + n + 'px;flex-shrink:0;border-radius:50%;background:var(--cap-ok,#34c77a);box-shadow:0 0 0 4px rgba(var(--cap-ok-rgb,52,199,122),.22);animation:capMolduraVivo 2s ease-in-out infinite"></span>'
      : '<span aria-hidden="true" style="width:' + n + 'px;height:' + n + 'px;flex-shrink:0;box-sizing:border-box;border-radius:50%;border:1.5px solid var(--cap-ink3,#97a3c0)"></span>';
  }
  function avatar(n, fs) { return '<a class="cpm-a" href="' + (n > 34 ? 'G4-Equipe-Web.dc.html' : 'G4-Equipe-Mobile.dc.html') + '" aria-label="Perfil — equipe e acessos" style="width:' + n + 'px;height:' + n + 'px;flex-shrink:0;box-sizing:border-box;border-radius:50%;border:1.5px solid var(--cap-accent,#00a1fe);background:var(--cap-card,#0d1329);color:var(--cap-accent,#00a1fe);font-size:' + fs + 'px;font-weight:800;display:flex;align-items:center;justify-content:center;text-decoration:none"><capitao-usuario campo="ini"></capitao-usuario></a>'; }

  function define(nome, C) { if (window.customElements && !customElements.get(nome)) customElements.define(nome, C); }

  // ——— Web · cabeçalho (68 px) ———
  var DEMO_HTML = '<span style="font-size:10px;letter-spacing:.14em;font-weight:800;color:var(--cap-violeta,#b45cff);border:1px solid rgba(var(--cap-violeta-rgb,162,43,253),.55);background:rgba(var(--cap-violeta-rgb,162,43,253),.10);border-radius:6px;padding:4px 8px;white-space:nowrap">DEMO</span>';
  function pilula(vivo) { return 'display:flex;align-items:center;gap:8px;padding:8px 14px;background:' + (vivo ? 'rgba(var(--cap-ok-rgb,52,199,122),.10)' : 'var(--cap-card,#0d1329)') + ';border:1px solid ' + (vivo ? 'transparent' : 'var(--cap-line,#1a2240)') + ';border-radius:999px;white-space:nowrap'; }
  function pilulaTexto(vivo) { return 'font-size:12.5px;font-weight:600;color:' + (vivo ? 'var(--cap-ok,#34c77a)' : 'var(--cap-ink2,#b1bdd6)'); }
  define('capitao-cabecalho', class extends HTMLElement {
    connectedCallback() { css(); if (!this._n) this.monta(leitura()); viva(this); this.atualiza(); }
    disconnectedCallback() { morta(this); }
    monta(L) {   // uma vez: o HTML com os lugares do texto vazios (data-cpm) e o estado do LED de agora; atualiza() preenche
      this.style.cssText = 'height:68px;flex-shrink:0;border-bottom:1px solid rgba(var(--cap-accent-rgb,0,161,254),.28);';
      this.innerHTML =
        '<header style="height:68px;box-sizing:border-box;display:flex;align-items:center;gap:18px;padding:0 28px">' +
          '<div style="display:flex;align-items:center;gap:14px">' +
            '<a class="cpm-a" href="Main.dc.html" aria-label="Início" style="display:flex;align-items:center;text-decoration:none"><img src="assets/wonderhub-simbolo.png" alt="WonderHUB.AI" style="height:32px;width:75px;object-fit:contain;flex-shrink:0"></a>' +
            '<span style="width:1px;height:30px;background:var(--cap-line2,#27315a)"></span>' +
            '<div style="display:flex;flex-direction:column">' +
              '<span style="font-size:17px;font-weight:800;letter-spacing:.02em;color:var(--cap-ink,#eaf1ff)">Capitão IA</span>' +
              '<span data-cpm="emb" style="font-size:11.5px;font-weight:500;color:var(--cap-ink3,#97a3c0)"></span>' +
            '</div>' +
          '</div>' +
          '<div style="flex-grow:1;display:flex;justify-content:center;min-width:0">' +
            '<div style="display:flex;align-items:center;gap:10px;padding:9px 16px;background:var(--cap-card,#0d1329);border:1px solid var(--cap-line,#1a2240);border-radius:999px;white-space:nowrap;color:var(--cap-ink2,#b1bdd6)">' + svg(PIN, 16, 1.7) +
              '<span data-cpm="estado" style="font-size:13px;font-weight:600;color:var(--cap-ink,#eaf1ff)"></span>' +
              '<span style="width:1px;height:14px;background:var(--cap-line2,#27315a)"></span>' +
              '<span data-cpm="pos" style="font-family:' + MONO + ';font-size:12px"></span>' +
            '</div>' +
          '</div>' +
          '<div data-cpm="dir" style="display:flex;align-items:center;gap:12px">' +
            '<span data-cpm="pilula" title="' + (L.vivo ? 'Telemetria ao vivo do coletor' : 'Telemetria ao vivo desligada — leitura fixa do coletor') + '" style="' + pilula(L.vivo) + '">' + led(L.vivo, 8) +
              '<span data-cpm="rotulo" style="' + pilulaTexto(L.vivo) + '"></span></span>' +
            '<capitao-theme-toggle size="40"></capitao-theme-toggle>' + avatar(40, 13) +
          '</div>' +
        '</header>';
      this._vivo = L.vivo; this._demo = null;
      this._n = { emb: no(this, 'emb'), estado: no(this, 'estado'), pos: no(this, 'pos'), rotulo: no(this, 'rotulo'), pilula: this.querySelector('[data-cpm="pilula"]'), dir: this.querySelector('[data-cpm="dir"]') };
    }
    atualiza() {   // a cada tique: só os nós cujo valor mudou
      var d = D(), E = d.embarcacao || {}, L = leitura(), n = this._n;
      poe(n.emb, 'Embarcação ' + (E.nome || 'SEM DADOS') + ' · registro ' + (E.registro || 'SEM DADOS'));
      poe(n.estado, L.estado + (L.local ? ' · ' + L.local : ''));
      poe(n.pos, L.pos);
      poe(n.rotulo, L.rotulo);
      if (this._vivo !== L.vivo) {   // virou ao vivo ↔ leitura fixa: LED, cor e dica da pílula (nunca no tique de rotina)
        this._vivo = L.vivo;
        n.pilula.setAttribute('title', L.vivo ? 'Telemetria ao vivo do coletor' : 'Telemetria ao vivo desligada — leitura fixa do coletor');
        n.pilula.setAttribute('style', pilula(L.vivo));
        troca(n.pilula.firstElementChild, led(L.vivo, 8));
        n.rotulo.parentNode.setAttribute('style', pilulaTexto(L.vivo));
      }
      if (d.demo && !this._demo) this._demo = n.dir.insertBefore(cria(DEMO_HTML), n.dir.firstChild);   // selo DEMO: só enquanto D.demo (a Fase 4 o tira das telas)
      else if (!d.demo && this._demo) { n.dir.removeChild(this._demo); this._demo = null; }
      if (this._demo) atr(this._demo, 'title', d.aviso || '');
    }
  });

  // ——— Web · trilho de 9 seções ———
  define('capitao-trilho', class extends HTMLElement {
    connectedCallback() { css(); this.render(); }
    static get observedAttributes() { return ['ativo']; }
    attributeChangedCallback() { if (this.isConnected) this.render(); }
    render() {
      var at = this.getAttribute('ativo') || '';
      this.style.cssText = 'width:96px;flex-shrink:0;box-sizing:border-box;border-right:1px solid var(--cap-line,#1a2240);';
      this.innerHTML = '<nav class="cpm-nav" aria-label="Seções" style="display:flex;flex-direction:column;align-items:center;padding:16px 0;gap:6px">' + SECOES.map(function (s) {
        var on = s.k === at;
        return '<a href="' + s.web + '"' + (on ? ' aria-current="page"' : '') + ' style="width:76px;box-sizing:border-box;display:flex;flex-direction:column;align-items:center;gap:5px;padding:10px 4px;border-radius:14px;text-decoration:none;background:' + (on ? 'rgba(var(--cap-accent-rgb,0,161,254),.14)' : 'transparent') + ';color:' + (on ? 'var(--cap-accent,#00a1fe)' : 'var(--cap-ink2,#b1bdd6)') + ';transition:background .25s,color .25s">' + svg(s.d, 22, 1.7) + '<span style="font-size:10.5px;font-weight:600">' + s.l + '</span></a>';
      }).join('') + '</nav>';
    }
  });

  // ——— Web · faixa de leitura (44 px) ———
  define('capitao-faixa', class extends HTMLElement {
    connectedCallback() { css(); if (!this._n) this.monta(leitura()); viva(this); this.atualiza(); }
    disconnectedCallback() { morta(this); }
    monta(L) {   // uma vez (e de novo só se o conjunto de rótulos mudar): um nó de texto por valor da faixa e um para o estado
      this.style.cssText = 'height:44px;flex-shrink:0;';
      this.innerHTML = '<footer style="height:44px;box-sizing:border-box;display:flex;align-items:center;gap:18px;padding:0 26px;border-top:1px solid rgba(var(--cap-hl-rgb,255,255,255),.05);font-size:11px;letter-spacing:.14em;color:var(--cap-ink4,#7985a6);white-space:nowrap;overflow:hidden">' +
        L.faixa.map(function (f) { return '<span>' + esc(f[0]) + ' <b data-cpm="f" style="color:var(--cap-ink3,#97a3c0)"></b></span>'; }).join('') +
        '<span data-cpm="estado" style="overflow:hidden;text-overflow:ellipsis"></span>' +
        '<span style="flex-grow:1"></span>' +
        '<a class="cpm-a" href="Main.dc.html" style="color:var(--cap-ink3,#97a3c0);font-weight:700;display:flex;align-items:center;gap:8px;text-decoration:none;min-height:44px;letter-spacing:.16em">' + svg(ANCORA, 15, 1.8, 'var(--cap-accent,#00a1fe)') + ' INÍCIO ›</a>' +
        '</footer>';
      this._rot = L.faixa.map(function (f) { return f[0]; }).join('|');
      this._n = { f: Array.prototype.map.call(this.querySelectorAll('[data-cpm="f"]'), function (b) { var t = document.createTextNode(''); b.appendChild(t); return t; }), estado: no(this, 'estado') };
    }
    atualiza() {   // a cada tique: só os nós cujo valor mudou
      var d = D(), L = leitura(), rot = L.faixa.map(function (f) { return f[0]; }).join('|');
      if (rot !== this._rot) this.monta(L);   // outro conjunto de campos (raro; nunca no tique de rotina)
      var n = this._n;
      L.faixa.forEach(function (f, i) { poe(n.f[i], f[1]); });
      poe(n.estado, (L.estado + (L.local ? ' · ' + L.local.replace(/^enseada de /i, '') : '')).toUpperCase() + ' · ' + L.hora + (L.vivo ? ' · AO VIVO' : d.demo ? ' · DEMO' : ''));
    }
  });

  // ——— Web · SOS circular (acima da faixa) ———
  define('capitao-sos-web', class extends HTMLElement {
    connectedCallback() {
      css();
      this.style.cssText = 'position:absolute;right:26px;bottom:62px;z-index:30;display:block;';
      this.innerHTML = '<a class="cpm-a" href="S1-SOS-Web.dc.html" aria-label="SOS — emergência" style="width:78px;height:78px;border-radius:50%;background:var(--cap-crit-fill,#d32f27);color:#fff;display:flex;align-items:center;justify-content:center;text-decoration:none;box-shadow:0 0 0 4px rgba(var(--cap-crit-rgb,255,59,48),.30),0 0 0 10px rgba(var(--cap-crit-rgb,255,59,48),.10),0 12px 32px rgba(var(--cap-critfill-rgb,211,47,39),.45)"><span style="font-size:18px;font-weight:800;letter-spacing:.10em;line-height:1;font-family:' + FONTE + '">SOS</span></a>';
    }
  });

  // ——— App · topo (44 px) ———
  define('capitao-topo-app', class extends HTMLElement {
    connectedCallback() { css(); if (!this._n) this.monta(leitura()); viva(this); this.atualiza(); }
    disconnectedCallback() { morta(this); }
    static get observedAttributes() { return ['titulo', 'voltar']; }
    attributeChangedCallback() { if (this.isConnected && this._n) this.atualiza(); }   // troca só o título ou o href (nós/atributos que já existem)
    monta(L) {   // uma vez: o HTML com o título vazio e o LED de agora; atualiza() preenche
      this.style.cssText = 'height:44px;flex-shrink:0;position:relative;';
      this.innerHTML = '<header style="height:44px;box-sizing:border-box;display:flex;align-items:center;gap:6px;padding:0 10px 0 4px;background:rgba(var(--cap-bar-rgb,10,15,34),.82);border-bottom:1px solid rgba(var(--cap-plat-rgb,211,220,239),.12);white-space:nowrap">' +
        '<a class="cpm-a" data-cpm="voltar" href="H2-Home-Mobile.dc.html" aria-label="Voltar" style="width:44px;height:44px;flex-shrink:0;display:flex;align-items:center;justify-content:center;color:var(--cap-ink2,#b1bdd6);text-decoration:none">' + svg(VOLTAR, 20, 2.2) + '</a>' +
        '<a class="cpm-a" href="H2-Home-Mobile.dc.html" aria-label="Início" style="height:44px;display:flex;align-items:center;flex-shrink:0;text-decoration:none"><img src="assets/wonderhub-simbolo.png" alt="WonderHUB.AI" style="height:20px;width:47px;object-fit:contain;flex-shrink:0"></a>' +
        '<span data-cpm="titulo" style="flex-grow:1;min-width:0;overflow:hidden;text-overflow:ellipsis;padding-left:6px;font-size:15px;font-weight:800;letter-spacing:.01em;color:var(--cap-ink,#eaf1ff)"></span>' +
        '<span data-cpm="led" role="img" aria-label="' + esc(L.rotulo) + '" title="' + esc(L.rotulo) + '" style="display:flex;align-items:center;padding:0 4px">' + led(L.vivo, 7) + '</span>' +
        '<capitao-theme-toggle size="30"></capitao-theme-toggle>' + avatar(30, 9.5) +
        '</header>';
      this._vivo = L.vivo;
      this._n = { titulo: no(this, 'titulo'), voltar: this.querySelector('[data-cpm="voltar"]'), led: this.querySelector('[data-cpm="led"]') };
    }
    atualiza() {   // a cada tique: o título e o href só se o atributo mudou; o rótulo do LED (muda 1×/min); o LED só quando vira
      var L = leitura(), n = this._n;
      poe(n.titulo, this.getAttribute('titulo') || '');
      atr(n.voltar, 'href', this.getAttribute('voltar') || 'H2-Home-Mobile.dc.html');
      atr(n.led, 'aria-label', L.rotulo);
      atr(n.led, 'title', L.rotulo);
      if (this._vivo !== L.vivo) { this._vivo = L.vivo; troca(n.led.firstElementChild, led(L.vivo, 7)); }
    }
  });

  // ——— App · barra SOS ———
  define('capitao-sos-app', class extends HTMLElement {
    connectedCallback() {
      css();
      this.style.cssText = 'flex-shrink:0;padding:0 16px 12px;';
      this.innerHTML = '<a class="cpm-a" href="S2-SOS-Mobile.dc.html" style="height:56px;border-radius:16px;background:var(--cap-crit-fill,#d32f27);color:#fff;display:flex;align-items:center;justify-content:center;gap:10px;text-decoration:none;box-shadow:0 0 0 3px rgba(var(--cap-crit-rgb,255,59,48),.28),0 10px 26px rgba(var(--cap-critfill-rgb,211,47,39),.40);font-family:' + FONTE + '"><span style="font-size:19px;font-weight:800;letter-spacing:.12em;line-height:1">SOS</span><span style="width:1px;height:22px;background:rgba(255,255,255,.4)"></span><span style="font-size:13px;font-weight:700;letter-spacing:.10em">EMERGÊNCIA</span></a>';
    }
  });

  window.CapitaoMoldura = { SECOES: SECOES, leitura: leitura };
})();
