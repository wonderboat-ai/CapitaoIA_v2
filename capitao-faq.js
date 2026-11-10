/* Capitão IA — FAQ dos equipamentos (PARIDADE F10; CONTRATO-DADOS §1.6; PROMPT Fase 4): o modelo das duas telas F6 (web e app) sobre o faq-equipamentos.json.
   O arquivo (91 itens: os cartões de emergência EM-01…09 e uma pergunta por seção dos guias de bordo) é carregado, indexado e buscado pelo CÉREBRO
   (B.carregaFaq · B.faqDados · B.faqItem · B.faqBusca: a mesma busca e o mesmo item do chat); aqui só a tela: os filtros por seção, a lista, o detalhe do
   item, o glossário e o link do toque numa pergunta para o chat (`Main.dc.html#q=<pergunta>&faq=<código>`: o cérebro responde com o item, o código e a fonte).
   Só mostra o texto do arquivo gerado: nenhum dado de bordo, nenhuma leitura, nenhum rótulo. O cartão de emergência abre local e o toque nele nunca chama a IA
   (o cérebro marca `seguranca`; a tela de chat não pergunta à IA quando vem do FAQ). Nada aqui grava, fala, troca de tela sozinho nem mexe no registro.
   Fora do SOS: numa rota /SOS- o arquivo sai sem definir nada.

   API (window.CapitaoFAQ; todas devolvem valor seguro e nunca lançam erro):
     carrega()            Promise<dados|null> — pede o arquivo ao cérebro (uma busca só) e avisa com o evento 'capitao-faq'
     pronto()             true depois de carregado
     dados()              o JSON inteiro (ou null)
     item(id)             o item pelo código ('EM-01', 'MO-02'…) ou null
     busca(q, n, sec)     [{ it, nota, cobre }] — o código (EM-06) acha o item; senão a busca do cérebro (BM25 com sinônimos); uma palavra só, que o cérebro não busca,
                          casa o texto no título, na pergunta, nas variantes ou no equipamento. `sec`: número da seção, lista de números ou 0 (todas)
     estadoInicial()      { q, sec, sel } do endereço: #id=EM-01 · #s=6 ou #s=6,7 (várias seções) · #busca=texto · #glossario
     chatHref(it, plat)   o link que abre o chat com a pergunta do item e o código (#q=…&faq=…)
     tela(st, plat, set)  o modelo das telas: filtros, lista, detalhe e glossário (`plat`: 'web' | 'app'; `set(parcial)` troca o estado e redesenha) */
(function () {
  var EM_SOS = false;
  try { EM_SOS = /SOS-/.test(location.pathname); } catch (e) {}
  if (EM_SOS || window.CapitaoFAQ) return;

  var GRUPOS = { '6,7': 'Eletrônicos' };   // o cartão «Eletrônicos» do hub abre as seções 6 e 7 juntas (#s=6,7)
  var COD = /^([A-Z]{2})-(\d{1,2})$/;
  var PARADAS = ' a o as os um uma de da do das dos em no na nos nas por para pra com sem se que qual quais quando como onde quanto eu me meu minha tem ter faco fazer faz pode posso ' ;

  var CACHE = null;   // o arquivo já lido: o <head> da tela pode rodar o capitao-brain.js duas vezes e a 2ª cópia assume o window.CapitaoBrain sem o FAQ (a tela não volta a «Carregando…»)
  function B() { return window.CapitaoBrain || null; }
  function norm(s) { return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); }
  function doCerebro() { var b = B(); try { var d = b && typeof b.faqDados === 'function' ? b.faqDados() : null; return d && Array.isArray(d.itens) ? d : null; } catch (e) { return null; } }
  function dados() { var d = doCerebro(); if (d) CACHE = d; return d || CACHE; }
  function pronto() { return !!dados(); }
  function avisa() { try { window.dispatchEvent(new CustomEvent('capitao-faq')); } catch (e) {} }
  // O cérebro de AGORA precisa ter o arquivo carregado (a busca é dele): pede a ele e, se a cópia do cérebro mudou no meio do caminho, pede de novo à nova (até 3 vezes); guarda o arquivo e avisa a tela
  function carrega() {
    var tent = 0;
    function uma() {
      var b = B();
      if (!b || typeof b.carregaFaq !== 'function') return Promise.resolve(CACHE);
      try {
        return b.carregaFaq().then(function () {
          var d = doCerebro();
          if (!d && tent++ < 3) return uma();
          if (d) { CACHE = d; avisa(); }
          return d || CACHE;
        }, function () { return CACHE; });
      } catch (e) { return Promise.resolve(CACHE); }
    }
    return uma();
  }
  // o cérebro trocou de cópia e a nova ainda não leu o arquivo: a busca dele só vale depois de ler (pede e a tela redesenha com o evento)
  var sincronizando = false;
  function sincroniza() {
    var b = B();
    if (sincronizando || !CACHE || !b || typeof b.faqPronto !== 'function' || b.faqPronto()) return;
    sincronizando = true;
    carrega().then(function () { sincronizando = false; avisa(); });
  }
  function item(id) {
    var b = B(), k = String(id || '').toUpperCase().trim(), x = null;
    try { x = b && typeof b.faqItem === 'function' ? b.faqItem(k) : null; } catch (e) { x = null; }
    if (!x && CACHE) x = CACHE.itens.filter(function (it) { return it.id === k; })[0] || null;
    return x;
  }

  function naSecao(it, sec) { return !sec || (Array.isArray(sec) ? sec.indexOf(it.secao) !== -1 : it.secao === sec); }
  // uma palavra só (o cérebro não busca): todas as palavras no texto do item; o título pesa mais
  function porTexto(q, d) {
    var ws = norm(q).replace(/[^a-z0-9]+/g, ' ').split(' ').filter(function (w) { return w && PARADAS.indexOf(' ' + w + ' ') === -1 && (w.length > 1 || /\d/.test(w)); });
    if (!ws.length) return [];
    return d.itens.map(function (it, k) {
      var t = norm(it.titulo + ' ' + it.pergunta), r = norm((it.variantes || []).join(' ') + ' ' + (it.equip || '')), nota = 0, todos = true;
      ws.forEach(function (w) { if (t.indexOf(w) !== -1) nota += 3; else if (r.indexOf(w) !== -1) nota += 1; else todos = false; });
      return todos ? { it: it, nota: nota - k / 1000, cobre: 1 } : null;
    }).filter(Boolean).sort(function (x, y) { return y.nota - x.nota; });
  }
  function busca(q, n, sec) {
    var d = dados(), t = String(q || '').trim(), m, x, achados = [], b = B();
    if (!d || !t) return [];
    m = COD.exec(t.toUpperCase());
    if (m) { x = item(m[1] + '-' + (m[2].length < 2 ? '0' : '') + m[2]); return x && naSecao(x, sec) ? [{ it: x, nota: 99, cobre: 1 }] : []; }
    sincroniza();
    try { achados = b && typeof b.faqBusca === 'function' ? b.faqBusca(t, 100) : []; } catch (e) { achados = []; }
    achados = (achados || []).filter(function (r) { return r && r.it && r.cobre >= 0.5; });
    if (!achados.length) achados = porTexto(t, d);
    return achados.filter(function (r) { return naSecao(r.it, sec); }).slice(0, n || 40);
  }

  // o endereço: #id=EM-01 · #s=6,7 · #busca=texto · #glossario
  function estadoInicial() {
    var st = { q: '', sec: 0, sel: null }, h = '';
    try { h = (location.hash || '').replace(/^#/, ''); } catch (e) {}
    h.split('&').forEach(function (kv) {
      var i = kv.indexOf('='), k = i < 0 ? kv : kv.slice(0, i), v = '';
      if (i >= 0) { try { v = decodeURIComponent(kv.slice(i + 1).replace(/\+/g, '%20')); } catch (e) { v = kv.slice(i + 1); } }
      if (k === 'id' && COD.test(v.toUpperCase().trim())) st.sel = v.toUpperCase().trim();
      else if (k === 's') {
        var ns = v.split(',').map(function (x) { return Math.max(0, Math.min(99, parseInt(x, 10) || 0)); }).filter(function (x, j, a) { return x && a.indexOf(x) === j; }).sort(function (p, q) { return p - q; });
        st.sec = ns.length > 1 ? ns : (ns[0] || 0);
      } else if (k === 'busca') st.q = v.slice(0, 120);
      else if (k === 'glossario') st.sec = 'glossario';
    });
    return st;
  }
  function chatHref(it, plat) { return (plat === 'app' ? 'H2-Home-Mobile.dc.html' : 'Main.dc.html') + '#q=' + encodeURIComponent(it.pergunta || it.titulo || '') + '&faq=' + encodeURIComponent(it.id); }

  function linha(it, set) {
    return { id: it.id, titulo: it.titulo, sub: it.acao || it.resposta, equip: it.equip, emerg: !!it.emerg, seg: !!it.seguranca && !it.emerg, abre: function () { set({ sel: it.id }); } };
  }
  function tela(st, plat, set) {
    var app = plat === 'app', d = dados(), q = String(st.q || '').trim(), sec = typeof st.sec === 'number' || Array.isArray(st.sec) ? st.sec : 0, gloss = st.sec === 'glossario', ed = '';
    try { ed = (window.CapitaoDados || {}).versao || ''; } catch (e) {}
    var vm = { carregando: !d, total: d ? d.itens.length : 0, edicao: ed, q: q, temQ: !!q, lista: [], vazio: false, detalhe: false, glossario: gloss, listaVisivel: true,
      onQ: function (e) { set({ q: e.target.value, sel: null }); }, limpa: function () { set({ q: '', sel: null }); } };
    if (!d) { vm.filtros = []; return vm; }
    // seção que o arquivo não tem (#s=99) vale como todas; uma só seção da lista vale como o número
    var conhecidas = (d.secoes || []).map(function (s) { return s.n; });
    if (Array.isArray(sec)) sec = sec.filter(function (n) { return conhecidas.indexOf(n) !== -1; });
    if (Array.isArray(sec) && sec.length < 2) sec = sec[0] || 0;
    if (typeof sec === 'number' && sec && conhecidas.indexOf(sec) === -1) sec = 0;
    var secs = (d.secoes || []).map(function (s) { return { l: s.titulo, v: s.n, emerg: s.n === 1 }; });
    vm.filtros = [{ l: 'Todas', v: 0 }].concat(secs, [{ l: 'Glossário', v: 'glossario' }]).map(function (s) {
      var on = s.v === 'glossario' ? gloss : !gloss && (Array.isArray(sec) ? sec.indexOf(s.v) !== -1 && sec.length === 1 : sec === s.v);
      return { l: s.l, v: s.v, ativo: on, onClick: function () { set({ sec: s.v, sel: null }); },
        linha: on ? 'rgba(var(--cap-accent-rgb, 0,161,254), 0.55)' : s.emerg ? 'rgba(var(--cap-crit-rgb, 255,59,48), 0.40)' : 'var(--cap-line2, #27315a)',
        fundo: on ? 'rgba(var(--cap-accent-rgb, 0,161,254), 0.14)' : 'transparent', cor: on ? 'var(--cap-accent, #00a1fe)' : s.emerg ? 'var(--cap-crit, #ff3b30)' : 'var(--cap-ink2, #b1bdd6)' };
    });
    var grupo = Array.isArray(sec) ? sec.join(',') : '';
    if (grupo) vm.filtros.splice(1, 0, { l: GRUPOS[grupo] || 'Seções ' + sec.join(' e '), v: sec, ativo: true, onClick: function () { set({ sec: sec, sel: null }); }, linha: 'rgba(var(--cap-accent-rgb, 0,161,254), 0.55)', fundo: 'rgba(var(--cap-accent-rgb, 0,161,254), 0.14)', cor: 'var(--cap-accent, #00a1fe)' });
    if (gloss) {
      var qt = norm(q).replace(/[^a-z0-9]+/g, ' ').split(' ').filter(Boolean);
      vm.termos = (d.glossario || []).filter(function (g) { var tx = norm(g.termo + ' ' + g.texto); return qt.every(function (w) { return tx.indexOf(w) !== -1; }); })
        .map(function (g) { return { t: g.termo, s: g.texto, f: g.fonte ? 'Fonte: ' + g.fonte : '' }; });
      vm.vazio = !vm.termos.length; vm.listaVisivel = false;
      vm.contagem = 'Glossário · ' + vm.termos.length + (vm.termos.length === 1 ? ' termo' : ' termos');
    } else {
      var achados = q ? busca(q, 40, sec).map(function (r) { return r.it; }) : d.itens.filter(function (it) { return naSecao(it, sec); });
      vm.lista = achados.map(function (it) { return linha(it, set); });
      vm.vazio = !vm.lista.length;
      var nEm = d.itens.filter(function (it) { return it.emerg; }).length;
      vm.contagem = q ? (vm.lista.length ? vm.lista.length + (vm.lista.length === 40 ? '+' : '') + (vm.lista.length === 1 ? ' resultado' : ' resultados') : 'nada encontrado')
        : Array.isArray(sec) ? (GRUPOS[grupo] || 'Seções') + ' · seções ' + sec.join(' e ') + ' · ' + vm.lista.length + ' itens'
        : sec ? sec + '. ' + ((d.secoes || [])[sec - 1] || {}).titulo + ' · ' + vm.lista.length + ' itens'
        : d.itens.length + ' itens · ' + nEm + ' cartões de emergência e ' + (d.itens.length - nEm) + ' perguntas';
    }
    var it = st.sel ? item(st.sel) : null;
    if (it) {
      vm.detalhe = true;
      vm.d = { id: it.id, titulo: it.titulo, secao: it.secao + '. ' + (((d.secoes || [])[it.secao - 1] || {}).titulo || ''), equip: it.equip, emerg: !!it.emerg, seg: !!it.seguranca && !it.emerg,
        acao: it.acao || '', temAcao: !!it.acao, pergunta: it.pergunta, resposta: it.resposta,
        variantes: (it.variantes || []).map(function (v) { return '“' + v + '”'; }).join(' · '), temVariantes: !!(it.variantes || []).length,
        passos: (it.passos || []).map(function (p, i) { return { n: String(i + 1), t: p }; }), temPassos: !!(it.passos || []).length,
        atencao: it.atencao || '', temAtencao: !!it.atencao, senao: it.senao || '', temSenao: !!it.senao, obs: it.obs || '', temObs: !!it.obs,
        fontes: (it.fontes || []).map(function (f) { return { tipo: String(f.tipo || '').toUpperCase(), t: f.texto }; }),
        ver: (it.ver || []).map(function (v) { var o = item(v); return o ? { id: v, t: o.titulo, abre: function () { set({ sel: v }); } } : null; }).filter(Boolean),
        fecha: function () { set({ sel: null }); }, sos: app ? 'S2-SOS-Mobile.dc.html' : 'S1-SOS-Web.dc.html', chat: chatHref(it, plat) };
      vm.d.temVer = vm.d.ver.length > 0;
      vm.listaVisivel = !app;   // no app a lista e o detalhe se alternam (uma coluna); na web ficam lado a lado
    }
    return vm;
  }

  window.CapitaoFAQ = { carrega: carrega, pronto: pronto, dados: dados, item: item, busca: busca, estadoInicial: estadoInicial, chatHref: chatHref, tela: tela, GRUPOS: GRUPOS };
})();
