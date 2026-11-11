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
     busca(q, n, sec)     [{ it, nota, cobre }] — o código (EM-06) acha o item; senão a busca do cérebro (BM25 com sinônimos), REORDENADA aqui: primeiro o equipamento que a pergunta nomeia, depois quem tem
                          mais das palavras no título, na pergunta, nas variantes ou no equipamento (com o mesmo radical: «liga» e «ligar»), por último a nota; havendo item com todas as palavras, só esses;
                          uma palavra só, que o cérebro não busca, casa o começo de uma palavra do título, da pergunta, das variantes ou do equipamento; «sos», «socorro», «mayday», «emergência», «ajuda» e «perigo»,
                          sozinhas, abrem os cartões de emergência (os achados primeiro). EMERGÊNCIA ACIMA DE TUDO: a pergunta que o cérebro roteia para o SOS («fogo no motor», «água entrando no motor», «alguém caiu»,
                          «barco afundando») traz na frente os cartões de emergência (EM-xx) de maior cobertura — nunca filtrados nem enterrados pelo equipamento que a frase nomeia — e, se nenhum casou, os 9 cartões.
                          `sec`: número da seção, lista de números ou 0 (todas)
     estadoInicial()      { q, sec, sel } do endereço: #id=EM-01 · #s=6 ou #s=6,7 (várias seções) · #busca=texto · #glossario
     chatHref(it, plat)   o link que abre o chat com a pergunta do item e o código (#q=…&faq=…)
     tela(st, plat, set)  o modelo das telas: filtros, lista, detalhe e glossário (`plat`: 'web' | 'app'; `set(parcial)` troca o estado e redesenha) */
(function () {
  var EM_SOS = false;
  try { EM_SOS = /SOS-/.test(location.pathname); } catch (e) {}
  if (EM_SOS || window.CapitaoFAQ) return;

  var GRUPOS = { '6,7': 'Eletrônicos' };   // o cartão «Eletrônicos» do hub abre as seções 6 e 7 juntas (#s=6,7)
  var COD = /^([A-Z]{2})-(\d{1,2})$/;
  var PARADAS = ' a o as os um uma de da do das dos em no na nos nas por para pra com sem se que qual quais quando como onde quanto eu me meu minha tem ter faco fazer faz pode posso nao ' ;
  var EMERGENCIA = ' sos socorro mayday emergencia ajuda perigo ';   // a busca só dessas palavras abre os cartões de emergência (EM-xx), os achados primeiro

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
  function palavras(q) { return norm(q).replace(/[^a-z0-9]+/g, ' ').split(' ').filter(function (w) { return w && PARADAS.indexOf(' ' + w + ' ') === -1 && (w.length > 1 || /\d/.test(w)); }); }
  // a palavra do texto começa pela palavra buscada (não é um pedaço no meio: «sos» não está em «pa-SSOS»)
  function temPalavra(texto, w) { return (' ' + texto.replace(/[^a-z0-9]+/g, ' ') + ' ').indexOf(' ' + w) !== -1; }
  // o mesmo radical: «liga» e «ligar», «gerador» e «geradores», «ligado» e «ligar» (4 letras de começo e, no máximo, 1 letra a mais na menor); palavra curta, só igual
  function mesmoRadical(a, b) {
    if (a === b) return true;
    var n = Math.min(a.length, b.length), k = 0;
    if (n < 4) return false;
    while (k < n && a.charAt(k) === b.charAt(k)) k++;
    return k >= 4 && k >= n - 1;
  }
  // uma palavra só (o cérebro não busca): todas as palavras no texto do item; o título pesa mais
  function porTexto(q, d) {
    var ws = palavras(q);
    if (!ws.length) return [];
    return d.itens.map(function (it, k) {
      var t = norm(it.titulo + ' ' + it.pergunta), r = norm((it.variantes || []).join(' ') + ' ' + (it.equip || '')), nota = 0, todos = true;
      ws.forEach(function (w) { if (temPalavra(t, w)) nota += 3; else if (temPalavra(r, w)) nota += 1; else todos = false; });
      return todos ? { it: it, nota: nota - k / 1000, cobre: 1 } : null;
    }).filter(Boolean).sort(function (x, y) { return y.nota - x.nota; });
  }
  // a fração das palavras da pergunta que estão no título, na pergunta, nas variantes ou no equipamento do item (com o mesmo radical)
  function cobreTitulo(it, ws, sin) {
    var tx = norm(it.titulo + ' ' + it.pergunta + ' ' + (it.variantes || []).join(' ') + ' ' + (it.equip || '')).replace(/[^a-z0-9]+/g, ' ').split(' ').filter(Boolean);
    function tem(w) { return tx.some(function (x) { return mesmoRadical(w, x); }); }
    return ws.filter(function (w) { return tem(w) || (sin && sinonimos(w).some(tem)); }).length / ws.length;
  }
  // o vocabulário de emergência que os cartões dizem de outro jeito («afundando» é «alagamento», «fumaça» é «fogo»): só para achar o cartão de uma pergunta de emergência (frenteEmergencia)
  var SIN_EMERG = { afund: ['alagamento'], naufrag: ['alagamento'], alag: ['alagamento'], fumac: ['fogo', 'incendio'] };
  function sinonimos(w) { var k; for (k in SIN_EMERG) if (w.indexOf(k) === 0) return SIN_EMERG[k]; return []; }
  // A nota do cérebro (BM25) pesa a palavra rara, e «liga» (que o índice não liga a «ligar») subia o item de OUTRO equipamento («gerador não liga» abria o estabilizador): na tela mandam, nesta ordem, o equipamento
  // que a pergunta nomeia («gerador», «plotter»: o item é dele), as palavras da pergunta que estão no título, na pergunta, nas variantes ou no equipamento do item, e só por último a nota. Havendo item com todas
  // as palavras, só esses ficam; havendo item do equipamento nomeado, os dos outros equipamentos só entram se cobrirem todas as palavras. O cartão de emergência NÃO passa por esse funil (ver frenteEmergencia):
  // o equipamento nomeado («fogo no MOTOR») nunca o esconde.
  function reordena(achados, ws, emer) {
    if (!ws.length) return achados;
    var m = achados.map(function (r, k) {
      var tc = cobreTitulo(r.it, ws), eqp = norm(r.it.equip || '').replace(/[^a-z0-9]+/g, ' ').split(' ').filter(Boolean);
      return { r: r, k: k, tc: tc, c: Math.max(r.cobre, tc), eq: ws.some(function (w) { return eqp.some(function (x) { return mesmoRadical(w, x); }); }) };
    });
    function funil(l) { l.sort(function (x, y) { return y.c - x.c || y.tc - x.tc || x.k - y.k; }); return l.length && l[0].c >= 1 ? l.filter(function (x) { return x.c >= 1; }) : l; }
    var com = funil(m.filter(function (x) { return x.eq; })), sem = funil(m.filter(function (x) { return !x.eq; }));
    if (com.length) sem = sem.filter(function (x) { return x.c >= 1; });
    // (na pergunta de emergência, quem tem TODAS as palavras vai na frente de quem só nomeia o equipamento: «fogo no motor» abre com o item do sistema fixo de incêndio, não com os 10 itens dos motores; fora da
    // emergência o equipamento nomeado manda — «o plotter não liga» abre com os plotters)
    return com.concat(sem).map(function (x, i) { return { x: x, i: i }; })
      .sort(function (a, b) { return emer ? (b.x.c >= 1) - (a.x.c >= 1) || a.i - b.i : a.i - b.i; })
      .map(function (o) { return o.x.r; });
  }
  // A pergunta de emergência: a que o cérebro roteia para o SOS (a mesma decisão do chat: «fogo no motor», «água entrando no motor», «alguém caiu», «barco afundando», «fumaça no motor»…). Só o cérebro decide;
  // sem ele (cópia antiga) a tela não adivinha: as palavras de socorro sozinhas seguem valendo (EMERGENCIA).
  function deEmergencia(t) {
    var b = B(), r = '';
    try { r = b && typeof b.route === 'function' ? b.route(t) : ''; } catch (e) { r = ''; }
    return r === 'sos';
  }
  // Os cartões de emergência (EM-xx) de uma pergunta de emergência: os de MAIOR cobertura das palavras da pergunta (até 3). A cobertura é a maior entre a da busca do cérebro (que acha o sinônimo, «alagamento»,
  // mesmo com 1 palavra de 3: «incêndio na praça de máquinas» → EM-05) e a do título, da pergunta, das variantes e do equipamento do cartão (com «afundando» = «alagamento»); «barco», «bordo» e «lancha» não
  // dizem de que emergência é a pergunta. Empatados, na ordem da busca e depois na do arquivo. Se nenhum casou («barco afundando» sem o cartão, «ajuda»), os cartões da seção, na ordem do arquivo. O botão SOS
  // continua à vista; a lista nunca deixa o socorro de fora.
  var GENERICAS = ' barco bordo embarcacao lancha ';
  function frenteEmergencia(todos, ws, d, sec) {
    var wsE = ws.filter(function (w) { return GENERICAS.indexOf(' ' + w + ' ') === -1; }), achou = {}, cand, top = 0;
    todos.forEach(function (r, k) { if (r.it.emerg && r.cobre > 0 && !achou[r.it.id]) achou[r.it.id] = { r: r, k: k }; });
    cand = d.itens.filter(function (it) { return it.emerg && naSecao(it, sec); }).map(function (it, i) {
      var a = achou[it.id], c = Math.max(a ? a.r.cobre : 0, wsE.length ? cobreTitulo(it, wsE, true) : 0);
      return { r: a ? a.r : { it: it, nota: 0, cobre: c }, c: c, k: a ? a.k : 1e4 + i };
    }).filter(function (x) { return x.c > 0; });
    if (!cand.length) return d.itens.filter(function (it) { return it.emerg && naSecao(it, sec); }).map(function (it) { return { it: it, nota: 0, cobre: 1 }; });
    cand.forEach(function (x) { top = Math.max(top, x.c); });
    return cand.filter(function (x) { return x.c >= top; }).sort(function (x, y) { return x.k - y.k; }).slice(0, 3).map(function (x) { return x.r; });
  }
  function busca(q, n, sec) {
    var d = dados(), t = String(q || '').trim(), m, x, todos = [], achados = [], b = B(), ws, ems, puras, emer, frente = [];
    if (!d || !t) return [];
    m = COD.exec(t.toUpperCase());
    if (m) { x = item(m[1] + '-' + (m[2].length < 2 ? '0' : '') + m[2]); return x && naSecao(x, sec) ? [{ it: x, nota: 99, cobre: 1 }] : []; }
    sincroniza();
    ws = palavras(t);
    puras = ws.length > 0 && ws.every(function (w) { return EMERGENCIA.indexOf(' ' + w + ' ') !== -1; });
    try { todos = b && typeof b.faqBusca === 'function' ? b.faqBusca(t, 100) : []; } catch (e) { todos = []; }
    todos = (todos || []).filter(function (r) { return r && r.it; });
    emer = !puras && ws.length > 0 && deEmergencia(t);
    if (emer) frente = frenteEmergencia(todos, ws, d, sec);
    achados = todos.filter(function (r) { return r.cobre >= 0.5 && frente.indexOf(r) === -1 && naSecao(r.it, sec); });
    if (achados.length) achados = reordena(achados, ws, emer);
    else if (!todos.some(function (r) { return r.cobre >= 0.5; })) achados = porTexto(t, d).filter(function (r) { return naSecao(r.it, sec) && frente.every(function (f) { return f.it !== r.it; }); });
    // «sos», «socorro», «mayday», «emergência», «ajuda» e «perigo», sozinhas: os cartões de emergência, os que a busca achou primeiro (o procedimento padrão abre local, nunca vai à IA)
    if (puras) {
      ems = d.itens.filter(function (it) { return it.emerg && naSecao(it, sec); }).map(function (it) {
        var a = achados.filter(function (r) { return r.it === it; })[0];
        return a || { it: it, nota: 0, cobre: 1 };
      });
      ems.sort(function (p, q2) { return q2.nota - p.nota; });
      achados = ems.concat(achados.filter(function (r) { return !r.it.emerg; }));
    } else achados = frente.concat(achados);
    return achados.slice(0, n || 40);
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
    // `q` (aparada) é o que se busca e vai ao endereço; o campo recebe o texto CRU (`vm.q`): o campo é controlado e aparar o que a pessoa digita comia o espaço entre as palavras
    var app = plat === 'app', d = dados(), q = String(st.q || '').trim(), sec = typeof st.sec === 'number' || Array.isArray(st.sec) ? st.sec : 0, gloss = st.sec === 'glossario', ed = '';
    try { ed = (window.CapitaoDados || {}).versao || ''; } catch (e) {}
    var vm = { carregando: !d, total: d ? d.itens.length : 0, edicao: ed, q: String(st.q || ''), temQ: !!q, lista: [], vazio: false, detalhe: false, glossario: gloss, listaVisivel: true,
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
