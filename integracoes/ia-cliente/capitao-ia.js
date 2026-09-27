/* Capitão IA — IA na nuvem (Claude API via proxy protegido) · lado do app.
   ESTRUTURA — DESLIGADA e NÃO CARREGADA por nenhuma tela. Mesmo padrão do capitao-telemetria.js:
   sem URL configurada, nada é buscado e o chat segue 100% local (respostas prontas + base de bordo + SEM DADOS).
   Para ligar (depois do login no servidor): ver integracoes/claude-api/README.md.
   A chave da Claude API nunca passa por aqui: o app só conhece a URL do proxy e a CHAVE_APP deste aparelho. */
(function () {
  if (window.CapitaoIA) return;
  var URL_PROXY = ''; // ex.: 'https://capitao-ia.<conta>.workers.dev'
  // Teste num aparelho antes de publicar: localStorage 'capitao.ia.url.v1' = URL do proxy.
  try { URL_PROXY = localStorage.getItem('capitao.ia.url.v1') || URL_PROXY; } catch (e) {}
  if (!/^https:\/\/[^\s]+$/.test(URL_PROXY)) URL_PROXY = '';
  var KC = 'capitao.ia.chave.v1';
  var ESPERA = 20000; // sem resposta nesse tempo → o chat fica com a resposta local

  // #ia=<chave> no endereço: guarda a chave neste aparelho e limpa o endereço (não fica no histórico). #ia=sair apaga.
  try {
    var m = location.hash.match(/(?:^#|&)ia=([^&]+)/);
    if (m) {
      var c = decodeURIComponent(m[1]);
      if (c === 'sair') localStorage.removeItem(KC); else localStorage.setItem(KC, c);
      history.replaceState(null, '', location.pathname + location.search + location.hash.replace(/(^#|&)ia=[^&]+/, '').replace(/^#&?$/, ''));
    }
  } catch (e) {}
  function chave() { try { return localStorage.getItem(KC) || ''; } catch (e) { return ''; } }
  function ativa() { return !!(URL_PROXY && chave()) && !(navigator && navigator.onLine === false); }

  // perguntar(pergunta, hits, contexto) → Promise<{ text, src, key: 'ia' } | null>
  //   hits: o retorno de CapitaoBrain.buscaBase(pergunta, 3) — [{ d: { fonte, pag, secao, texto }, nota }]
  //   null = IA desligada, sem rede, demora, recusa ou erro → a tela mantém a resposta local.
  function perguntar(pergunta, hits, contexto) {
    if (!ativa() || !window.fetch) return Promise.resolve(null);
    var trechos = (hits || []).slice(0, 3).map(function (h) { var d = h && h.d ? h.d : h; return { fonte: d.fonte, pag: d.pag, secao: d.secao, texto: d.texto }; });
    var ctl = window.AbortController ? new AbortController() : null, t = setTimeout(function () { if (ctl) ctl.abort(); }, ESPERA);
    return fetch(URL_PROXY, {
      method: 'POST', cache: 'no-store', signal: ctl ? ctl.signal : undefined,
      headers: { 'Content-Type': 'application/json', 'X-Capitao-Chave': chave() },
      body: JSON.stringify({ pergunta: String(pergunta || '').slice(0, 500), trechos: trechos, contexto: contexto ? String(contexto).slice(0, 2000) : '' })
    }).then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (j) {
        clearTimeout(t);
        if (!j || typeof j.texto !== 'string' || !j.texto.trim()) return null;
        return { text: j.texto.trim(), src: 'Fonte: IA na nuvem (Claude) · só com as fontes enviadas pelo app', key: 'ia' };
      }, function () { clearTimeout(t); return null; });
  }

  window.CapitaoIA = { ativa: ativa, perguntar: perguntar };
})();
