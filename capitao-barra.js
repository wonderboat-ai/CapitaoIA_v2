/* capitao-barra.js — <capitao-barra-chat>: a barra do assistente, igual em todas as telas do app.
   Mesmo padrão do cartão de chat da home (H2): campo "Pergunte ao barco…" + enviar; embaixo TEXTO · VOZ→TEXTO · CONVERSA · FOTO · VÍDEO.
   CONVERSA = círculo de 54 px com o ∞ da WonderHUB.AI (<capitao-simbolo>, classes .cps-*): o capitao-simbolo.js é carregado
   aqui, uma vez, se a tela ainda não o tiver; até ele chegar, fica o disco escuro.
   Fora da home, tudo leva à conversa da home (H2-Home-Mobile.dc.html):
     - enviar  → #q=<pergunta>   (a home responde na hora)
     - modos   → #mode=voz|conversa|foto|video|texto (voz e conversa já ligam o microfone: a origem arma 'capitao.modo' no sessionStorage)
   Atributos opcionais:
     placeholder="…"  texto do campo (padrão "Pergunte ao barco…")
     prefixo="…"      antecede a pergunta (ex.: "Registre no diário: ")
   Antes de navegar, dispara window 'capitao-barra' (cancelável, detail {texto, modo}); a tela pode tratar e chamar preventDefault(). */
(function () {
  if (!window.customElements || customElements.get('capitao-barra-chat')) return;
  var HOME = 'H2-Home-Mobile.dc.html';
  var ICON = {
    texto: 'M3 6h18v12H3z M7 10h.01 M11 10h.01 M15 10h.01 M8 14h8',
    voz: 'M12 3a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3z M5 11a7 7 0 0 0 14 0 M12 18v3',
    foto: 'M4 8h3l2-2h6l2 2h3v11H4z M12 16a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4z',
    video: 'M3 7h11v10H3z M14 11l6-3.5v9L14 13z',
    enviar: 'M4 12h14 M13 6l6 6-6 6'
  };
  var FONTE = '"Nimbus Sans","Helvetica Neue",Helvetica,Arial,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif';
  function css() {
    if (document.getElementById('capitao-barra-css')) return;
    var s = document.createElement('style'); s.id = 'capitao-barra-css';
    s.textContent =
      'capitao-barra-chat{display:block;box-sizing:border-box;width:100%;font-family:' + FONTE + '}' +
      '.cpb-card{display:flex;flex-direction:column;background:linear-gradient(180deg,rgba(var(--cap-card3-rgb,20,28,54),.96) 0%,rgba(var(--cap-card2-rgb,10,15,32),.97) 100%);border:1px solid rgba(var(--cap-plat-rgb,211,220,239),.40);border-radius:18px;position:relative;box-shadow:inset 0 1px 0 rgba(255,255,255,.12),0 0 0 3px rgba(var(--cap-plat-rgb,211,220,239),.05),0 10px 28px rgba(var(--cap-shadow-rgb,0,0,0),calc(.45*var(--cap-shadow-k,1)))}' +
      '.cpb-top{display:flex;align-items:center;gap:6px;padding:6px 6px 6px 16px}' +
      '.cpb-in{flex-grow:1;min-width:0;background:none;border:none;outline:none;color:var(--cap-ink,#eaf1ff);font:inherit;font-size:16px;padding:11px 0}' +
      '.cpb-in::placeholder{color:var(--cap-ph,#4a5578)}' +
      '.cpb-go{width:44px;height:44px;flex-shrink:0;border-radius:12px;border:none;background:linear-gradient(180deg,var(--cap-accent-hi,#4dbcff) 0%,var(--cap-accent,#00a1fe) 100%);box-shadow:inset 0 1px 0 rgba(255,255,255,.35);color:var(--cap-on-accent,#050816);display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0}' +
      '.cpb-modos{display:grid;grid-template-columns:repeat(2,minmax(0,1fr)) 76px repeat(2,minmax(0,1fr));border-top:1px solid rgba(var(--cap-hl-rgb,255,255,255),.07)}' +
      '.cpb-m{height:50px;border:none;background:transparent;color:var(--cap-ink3,#97a3c0);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;cursor:pointer;padding:0;min-width:0;font:inherit}' +
      '.cpb-m span{font-size:8.5px;letter-spacing:.08em;font-weight:700;white-space:nowrap}' +
      '.cpb-m:focus-visible,.cpb-go:focus-visible,.cpb-conv:focus-visible{outline:2px solid var(--cap-accent,#00a1fe);outline-offset:2px}' +
      '.cpb-c{position:relative;height:50px;display:flex;align-items:flex-end;justify-content:center;padding-bottom:6px;box-sizing:border-box}' +
      '.cpb-c>span{font-size:8.5px;letter-spacing:.14em;font-weight:800;color:var(--cap-tele,#00f4fd);white-space:nowrap}' +
      // o resto do botão (borda, brilho, ∞) vem do .cps-botao do capitao-simbolo.js; aqui só a posição e o disco de espera
      '.cpb-conv{--cps-d:54px;position:absolute;left:50%;top:-22px;margin-left:-27px;width:54px;height:54px;box-sizing:border-box;border-radius:50%;border:none;padding:0;background:#050816;cursor:pointer}';
    document.head.appendChild(s);
  }
  // <capitao-simbolo> vem do capitao-simbolo.js — as telas com a barra não o carregam: põe a tag uma vez
  function simbolo() {
    if (window.CapitaoSimbolo || (window.customElements && customElements.get('capitao-simbolo')) || document.querySelector('script[src*="capitao-simbolo.js"]')) return;
    var s = document.createElement('script'); s.src = './capitao-simbolo.js';
    (document.head || document.documentElement).appendChild(s);
  }
  function svg(d, n) {
    return '<svg width="' + n + '" height="' + n + '" viewBox="0 0 24 24" fill="none" aria-hidden="true" style="flex-shrink:0"><path d="' + d + '" stroke="currentColor" stroke-width="' + (d === ICON.enviar ? 2.2 : 1.8) + '" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  }
  function modo(m, label, aria) {
    return '<button type="button" class="cpb-m" data-m="' + m + '" aria-label="' + aria + '">' + svg(ICON[m], 19) + '<span>' + label + '</span></button>';
  }
  customElements.define('capitao-barra-chat', class extends HTMLElement {
    connectedCallback() {
      if (this._ok) return; this._ok = true; css(); simbolo();
      var ph = this.getAttribute('placeholder') || 'Pergunte ao barco…';
      this.innerHTML =
        '<div class="cpb-card" role="group" aria-label="Assistente de bordo">' +
          '<form class="cpb-top"><label style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">Pergunta</label>' +
            '<input class="cpb-in" maxlength="500" autocomplete="off" enterkeyhint="send" placeholder="' + ph.replace(/"/g, '&quot;') + '">' +
            '<button type="submit" class="cpb-go" aria-label="Enviar">' + svg(ICON.enviar, 18) + '</button>' +
          '</form>' +
          '<div class="cpb-modos">' +
            modo('texto', 'TEXTO', 'Digitar a pergunta') +
            modo('voz', 'VOZ→TEXTO', 'Falar — a pergunta é transcrita e respondida') +
            '<div class="cpb-c"><button type="button" class="cpb-conv cps-botao cps-sep" data-m="conversa" aria-label="Conversa contínua por voz" title="Conversa contínua por voz"><capitao-simbolo></capitao-simbolo></button><span>CONVERSA</span></div>' +
            modo('foto', 'FOTO', 'Enviar foto — etiqueta, alarme, nota ou página de manual') +
            modo('video', 'VÍDEO', 'Enviar vídeo de 10 s — som ou comportamento anormal') +
          '</div>' +
        '</div>';
      var self = this, input = this.querySelector('.cpb-in');
      this.querySelector('form').addEventListener('submit', function (e) {
        e.preventDefault();
        var t = input.value.trim();
        if (!t) { input.focus(); return; }
        self.ir({ texto: (self.getAttribute('prefixo') || '') + t });
      });
      [].forEach.call(this.querySelectorAll('[data-m]'), function (b) {
        b.addEventListener('click', function () {
          var m = b.getAttribute('data-m');
          if (m === 'texto') { input.focus(); return; }
          self.ir({ modo: m });
        });
      });
    }
    ir(d) {
      var ev; try { ev = new CustomEvent('capitao-barra', { detail: d, cancelable: true }); } catch (e) { ev = null; }
      if (ev && !window.dispatchEvent(ev)) return; // a tela tratou
      if (d.modo === 'voz' || d.modo === 'conversa') { try { sessionStorage.setItem('capitao.modo', d.modo); } catch (e) {} }
      location.href = HOME + '#' + (d.texto ? 'q=' + encodeURIComponent(d.texto) : 'mode=' + d.modo);
    }
  });
})();
