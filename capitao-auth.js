/* Capitão IA — acesso, usuário logado e rodapé com a versão.
   Entra no <head> de toda tela, antes do support.js: sem sessão válida, troca a página por login.html antes de desenhar.
   ATENÇÃO: é uma porta de entrada, não segurança real. O site é estático e público — quem lê o código pode pular esta
   tela. Por isso a senha não fica aqui: só o hash PBKDF2-SHA-256 com sal por usuário (senhas combinadas fora do repositório).
   Dentro do editor de pranchetas (iframe fora do site publicado) não pede login e assume o proprietário. */
(function () {
  if (window.CapitaoAuth) return;

  var VERSAO = { v: '1.0.1', data: '27/09/2026' };
  var CREDITO = 'Wonder BOAT | WonderHUB.AI';
  var PUBLICADO = /(^|\.)(wonderboat-ai\.github\.io|xn--capitoia-vza\.com\.br)$/i; // GitHub Pages e www.capitãoia.com.br

  // Senha verificada por PBKDF2 (210.000 iterações, SHA-256, 32 bytes). Trocar senha = gerar sal e hash novos
  // com ferramentas/gerar-senha.html e colar a linha aqui.
  var ITER = 210000;
  var USUARIOS = {
    lucas: { nome: 'Lucas', completo: 'Lucas Araújo', ini: 'LA', papel: 'proprietário', sal: 'EKrlCoN+cQlXyjhXlmd6Zw==', hash: 's+iHyh01QjnN1ZqdV7UOWm+b/y6xlP91Sfxv6/fHV1Y=' }
  };
  var DONO = 'lucas';

  var K = 'capitao.sessao.v1', KT = 'capitao.login.tentativas.v1';
  var DIA = 86400000, LONGA = 30 * DIA, CURTA = 12 * 3600000;
  var PAGINA = /^[A-Za-z0-9][A-Za-z0-9._-]*\.html$/;

  function arquivo(path) { var m = String(path || '').match(/([^\/]*)$/); var f = m ? m[1] : ''; try { f = decodeURIComponent(f); } catch (e) {} return f || 'index.html'; }
  function ehLogin() { return arquivo(location.pathname) === 'login.html'; }
  // SOS abre sem login: numa emergência ninguém pode ficar preso na senha (sessão vencida, tripulante sem acesso).
  function livre() { return /^(S1-SOS-Web|S2-SOS-Mobile)\.dc\.html$/.test(arquivo(location.pathname)); }
  function noEditor() {
    var framed = true; try { framed = window.top !== window.self; } catch (e) {}
    return framed && !PUBLICADO.test(location.hostname);
  }
  function fuso() { var D = window.CapitaoDados; return (D && D.embarcacao && D.embarcacao.fuso) || 'America/Sao_Paulo'; }

  // Sessão só no localStorage: vale para todas as abas, e Sair/expiração chegam a todas. Com "manter conectado" 30 dias; sem, 12 h.
  function lerSessao() {
    var raw = null; try { raw = localStorage.getItem(K); } catch (e) {}
    if (!raw) return null;
    var s = null; try { s = JSON.parse(raw); } catch (e) {}
    var agora = Date.now();
    if (!s || typeof s !== 'object' || typeof s.u !== 'string' || !Object.prototype.hasOwnProperty.call(USUARIOS, s.u) ||
      typeof s.exp !== 'number' || !(s.exp > agora) || s.exp - agora > LONGA + DIA) { limpar(); return null; }
    return s;
  }
  function limpar() { try { localStorage.removeItem(K); } catch (e) {} }

  function publico(id) {
    var u = USUARIOS[id]; if (!u) return null;
    return { id: id, nome: u.nome, completo: u.completo, ini: u.ini, papel: u.papel };
  }
  // Sem sessão numa tela protegida (expirou com a página aberta): volta ao login — nada é assinado em nome de outro.
  function usuario() {
    var s = lerSessao();
    if (s) return publico(s.u);
    if (noEditor()) return publico(DONO);
    if (!ehLogin() && !livre()) paraLogin();
    return null;
  }
  function nome() { var u = usuario(); return u ? u.nome : 'sem sessão'; }
  function lista() { return Object.keys(USUARIOS).map(publico); }

  // Destino depois do login: só telas deste site (sem outro domínio, sem javascript:, sem subpasta).
  function destinoSeguro(next) {
    var fallback = 'index.html';
    if (typeof next !== 'string' || !next || next.length > 600) return fallback;
    var url; try { url = new URL(next, location.href); } catch (e) { return fallback; }
    if (url.origin !== location.origin) return fallback;
    var base = location.pathname.replace(/[^\/]*$/, '');
    if (url.pathname.indexOf(base) !== 0) return fallback;
    var f = url.pathname.slice(base.length) || 'index.html';
    if (!PAGINA.test(f) || f === 'login.html') return fallback;
    return f + url.search + url.hash;
  }

  function b64(buf) { var s = '', b = new Uint8Array(buf); for (var i = 0; i < b.length; i++) s += String.fromCharCode(b[i]); return btoa(s); }
  function deB64(s) { var r = atob(s), b = new Uint8Array(r.length); for (var i = 0; i < r.length; i++) b[i] = r.charCodeAt(i); return b; }
  function iguais(a, b) { if (a.length !== b.length) return false; var d = 0; for (var i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0; }

  // Trava no máximo 15 min, mesmo se o relógio do aparelho for corrigido para trás; erro de mais de 1 h atrás não conta.
  var TETO = 15 * 60000;
  function tentativas() {
    var t = null; try { t = JSON.parse(localStorage.getItem(KT) || 'null'); } catch (e) {}
    var agora = Date.now(), zero = { n: 0, ate: 0, ult: 0 };
    if (!t || typeof t.n !== 'number' || typeof t.ate !== 'number' || typeof t.ult !== 'number') return zero;
    if (t.ate - agora > TETO || t.ult - agora > TETO || agora - t.ult > 3600000) return zero;
    return t;
  }
  function bloqueadoAte() { var t = tentativas(); return t.ate > Date.now() ? t.ate : 0; }
  function falhou() {
    var t = tentativas(); t.n += 1; t.ult = Date.now();
    if (t.n >= 5) { t.ate = Date.now() + Math.min(TETO, 30000 * Math.pow(2, t.n - 5)); }
    try { localStorage.setItem(KT, JSON.stringify(t)); } catch (e) {}
  }

  // Resolve { ok: true, usuario } ou { ok: false, motivo: 'credenciais' | 'bloqueado' | 'navegador' | 'armazenamento', ate }.
  function entrar(login, senha, manter) {
    var ate = bloqueadoAte();
    if (ate) return Promise.resolve({ ok: false, motivo: 'bloqueado', ate: ate });
    var id = String(login || '').trim().toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').split(/\s+/)[0] || '';
    var u = Object.prototype.hasOwnProperty.call(USUARIOS, id) ? USUARIOS[id] : null;
    var subtle = window.crypto && window.crypto.subtle;
    if (!subtle || !window.TextEncoder) return Promise.resolve({ ok: false, motivo: 'navegador' });
    // Usuário inexistente também calcula o hash: mesma demora, sem revelar quais nomes existem.
    var alvo = u || USUARIOS[DONO];
    return subtle.importKey('raw', new TextEncoder().encode(String(senha || '')), 'PBKDF2', false, ['deriveBits'])
      .then(function (key) { return subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt: deB64(alvo.sal), iterations: ITER }, key, 256); })
      .then(function (bits) {
        if (!u || !iguais(b64(bits), u.hash)) { falhou(); var a = bloqueadoAte(); return a ? { ok: false, motivo: 'bloqueado', ate: a } : { ok: false, motivo: 'credenciais' }; }
        try { localStorage.removeItem(KT); } catch (e) {}
        limpar();
        var s = JSON.stringify({ u: id, em: Date.now(), exp: Date.now() + (manter ? LONGA : CURTA) });
        try { localStorage.setItem(K, s); } catch (e) {}
        if (!lerSessao()) return { ok: false, motivo: 'armazenamento' }; // navegador bloqueia dados do site
        avisar();
        return { ok: true, usuario: publico(id) };
      }, function () { return { ok: false, motivo: 'navegador' }; });
  }

  var saindo = false;
  function paraLogin() {
    if (saindo) return; saindo = true;
    try { document.documentElement.style.visibility = 'hidden'; } catch (e) {}
    var aqui = arquivo(location.pathname) + location.search + location.hash;
    location.replace('login.html?next=' + encodeURIComponent(aqui));
  }
  function sair() { limpar(); avisar(); try { sessionStorage.removeItem('capitao.lista'); } catch (e) {} saindo = true; location.replace('login.html'); }

  function avisar() { try { window.dispatchEvent(new CustomEvent('capitao-sessao')); } catch (e) {} }
  window.addEventListener('storage', function (e) {
    if (e && e.key !== K && e.key !== null) return;
    avisar();
    if (!ehLogin() && !livre() && !noEditor() && !lerSessao()) paraLogin(); // saiu em outra aba
  });
  // Expirou com a tela aberta: confere ao voltar para a aba, ao focar e na hora exata do vencimento.
  var vigia = 0;
  function vigiar() {
    if (ehLogin() || livre() || noEditor()) return;
    var s = lerSessao(); clearTimeout(vigia);
    if (!s) { paraLogin(); return; }
    vigia = setTimeout(vigiar, Math.max(1000, Math.min(s.exp - Date.now() + 500, DIA)));
  }
  document.addEventListener('visibilitychange', function () { if (!document.hidden) vigiar(); });
  window.addEventListener('focus', vigiar);
  // Voltar depois de Sair pode restaurar a página da memória (bfcache) sem rodar este script de novo.
  window.addEventListener('pageshow', function (e) {
    if (e && e.persisted && !ehLogin() && !livre() && !noEditor() && !lerSessao()) paraLogin();
  });

  // Saudação: uma frase sorteada a cada carregamento de página (nunca a mesma da vez anterior neste aparelho).
  var FRASES = ['Bons ventos!', 'Terra à vista!', 'Navegar é preciso.', 'Leme firme, rumo certo.', 'Vento em popa!',
    'O mar hoje está para almirante?', 'Tudo pronto para largar?', 'Mar calmo nunca fez bom marinheiro.',
    'Quem tem um não tem nenhum.', 'Tecnologia a bordo, decisão no leme.'];
  var fraseDaVez = null;
  function frase() {
    if (fraseDaVez) return fraseDaVez;
    var KS = 'capitao.saudacao.v1', ant = -1;
    try { ant = parseInt(localStorage.getItem(KS), 10); } catch (e) {}
    var i = Math.floor(Math.random() * (FRASES.length - 1));
    if (i >= ant && ant >= 0 && ant < FRASES.length) i++; // pula a anterior sem viciar o sorteio
    try { localStorage.setItem(KS, String(i)); } catch (e) {}
    return (fraseDaVez = FRASES[i]);
  }
  // Bom dia / Boa tarde / Boa noite pela hora do barco
  function periodo() {
    var h = new Date().getHours();
    try { h = parseInt(new Intl.DateTimeFormat('pt-BR', { timeZone: fuso(), hour: '2-digit', hour12: false }).format(new Date()), 10) % 24; } catch (e) {}
    return h >= 5 && h < 12 ? 'Bom dia' : h >= 12 && h < 18 ? 'Boa tarde' : 'Boa noite';
  }

  function logado() { return !!lerSessao(); }
  window.CapitaoAuth = { VERSAO: VERSAO, CREDITO: CREDITO, usuario: usuario, nome: nome, lista: lista, logado: logado, entrar: entrar, sair: sair, destinoSeguro: destinoSeguro, bloqueadoAte: bloqueadoAte, ehLogin: ehLogin, livre: livre, noEditor: noEditor, frase: frase, periodo: periodo, FRASES: FRASES };

  // Porta: sem sessão → login, antes de qualquer desenho.
  if (!ehLogin() && !livre() && !noEditor() && !lerSessao()) { paraLogin(); return; }
  vigiar();

  if (!window.customElements) return;

  // <capitao-usuario campo="ini|nome|completo"> — texto do usuário logado; acompanha login/logout em outra aba.
  if (!customElements.get('capitao-usuario')) customElements.define('capitao-usuario', class extends HTMLElement {
    connectedCallback() { this._on = this.render.bind(this); window.addEventListener('capitao-sessao', this._on); this.render(); }
    disconnectedCallback() { window.removeEventListener('capitao-sessao', this._on); }
    render() {
      var u = usuario() || publico(DONO);
      var c = this.getAttribute('campo'); var t = c === 'ini' ? u.ini : c === 'completo' ? u.completo : u.nome;
      if (this.textContent !== t) this.textContent = t;
    }
  });

  // <capitao-saudacao> — “Olá, Lucas. Bons ventos!”: nome do usuário logado + a frase sorteada neste carregamento.
  if (!customElements.get('capitao-saudacao')) customElements.define('capitao-saudacao', class extends HTMLElement {
    connectedCallback() { this._on = this.render.bind(this); window.addEventListener('capitao-sessao', this._on); this.render(); }
    disconnectedCallback() { window.removeEventListener('capitao-sessao', this._on); }
    render() {
      var u = usuario() || publico(DONO);
      var t = '“Olá, ' + u.nome + '. ' + frase() + '”';
      if (this.textContent !== t) this.textContent = t;
    }
  });

  // <capitao-periodo> — “Bom dia” / “Boa tarde” / “Boa noite” pela hora do barco.
  if (!customElements.get('capitao-periodo')) customElements.define('capitao-periodo', class extends HTMLElement {
    connectedCallback() { this.render(); this._t = setInterval(this.render.bind(this), 60000); }
    disconnectedCallback() { clearInterval(this._t); }
    render() { var t = periodo(); if (this.textContent !== t) this.textContent = t; }
  });

  // <capitao-rodape> — versão, selo DEMO, usuário (com Sair) e crédito. Quebra em linhas no celular.
  if (!customElements.get('capitao-rodape')) customElements.define('capitao-rodape', class extends HTMLElement {
    connectedCallback() { if (!this._b) this.build(); this._on = this.render.bind(this); window.addEventListener('capitao-sessao', this._on); this.render(); }
    disconnectedCallback() { window.removeEventListener('capitao-sessao', this._on); }
    build() {
      this.setAttribute('role', 'contentinfo');
      this.style.cssText = 'display:flex;flex-wrap:wrap;align-items:center;justify-content:center;column-gap:14px;row-gap:2px;box-sizing:border-box;width:100%;min-height:32px;padding:3px 16px calc(3px + env(safe-area-inset-bottom, 0px));font:500 11px/1.5 "Nimbus Sans","Helvetica Neue",Helvetica,Arial,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;letter-spacing:0.06em;color:var(--cap-ink4, #7985a6);text-align:center;';
      var d = document;
      var ver = d.createElement('span'); ver.textContent = 'Capitão IA · v' + VERSAO.v + ' · ' + VERSAO.data;
      var D = window.CapitaoDados;
      var demo = null;
      if (D && D.demo) {
        demo = d.createElement('span'); demo.textContent = D.selo || 'DEMO · DADOS FICTÍCIOS'; demo.title = D.aviso || '';
        demo.style.cssText = 'font-weight:700;letter-spacing:0.12em;color:var(--cap-violeta, #b45cff);';
      }
      var quem = d.createElement('span'); quem.style.cssText = 'display:inline-flex;align-items:center;gap:6px;';
      var nomeEl = d.createElement('b'); nomeEl.style.cssText = 'font-weight:700;color:var(--cap-ink3, #97a3c0);';
      var btn = d.createElement('button'); btn.type = 'button'; btn.textContent = 'Sair';
      btn.style.cssText = 'font:inherit;letter-spacing:inherit;color:var(--cap-accent, #00a1fe);background:transparent;border:0;padding:0 6px;margin:0;cursor:pointer;min-height:26px;';
      btn.addEventListener('click', sair);
      quem.appendChild(nomeEl); quem.appendChild(btn);
      var cred = d.createElement('span'); cred.textContent = CREDITO;
      this.appendChild(ver); if (demo) this.appendChild(demo); this.appendChild(quem); this.appendChild(cred);
      // Só nas telas iniciais (web e app): ícone discreto para baixar o Guia rápido em PDF.
      if (/(^|\/)(Main|H2-Home-Mobile)\.dc\.html$/.test(location.pathname)) {
        var guia = d.createElement('a'); guia.href = 'Guia-Rapido-Capitao-IA.pdf'; guia.setAttribute('download', 'Guia-Rapido-Capitao-IA.pdf');
        guia.title = 'Baixar o Guia rápido (PDF)'; guia.setAttribute('aria-label', 'Baixar o Guia rápido em PDF');
        guia.style.cssText = 'display:inline-flex;align-items:center;gap:5px;color:inherit;text-decoration:none;min-height:26px;opacity:0.85;';
        guia.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true" style="flex-shrink:0"><path d="M12 4v11 M7 10l5 5 5-5 M5 20h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg><span>Guia</span>';
        this.appendChild(guia);
      }
      this._b = btn; this._n = nomeEl; this._q = quem;
    }
    render() {
      var s = lerSessao(); var u = usuario();
      this._q.style.display = u ? 'inline-flex' : 'none';
      this._n.textContent = u ? u.nome : '';
      this._b.style.display = s ? '' : 'none';
      this._b.setAttribute('aria-label', u ? 'Sair — encerrar a sessão de ' + u.nome : 'Sair');
    }
  });
})();
