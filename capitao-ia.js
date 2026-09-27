/* Capitão IA — IA na nuvem via proxy protegido (Worker `capitao-ia`) · lado do app.
   LIGADO NA DEMONSTRAÇÃO (1.0.4): carregado pelo Main e pelo H2. Cópia de integracoes/ia-cliente/capitao-ia.js com a URL
   do Worker preenchida (o teste testes/chat_ia.py confere que só essa linha difere). Sem a CHAVE_APP no aparelho
   (#ia=ativar, depois do login), nada é buscado e o chat segue 100% local (respostas prontas + base de bordo + SEM DADOS).
   Serve aos dois proxies (mesmo contrato): integracoes/workers-ai/ (gratuito) ou integracoes/claude-api/ (pago).
   Como foi ligado e como ativar um aparelho: integracoes/workers-ai/README.md.
   Nenhuma chave de provedor passa por aqui: o app só conhece a URL do proxy e a CHAVE_APP deste aparelho. */
(function () {
  if (window.CapitaoIA) return;
  var URL_PROXY = 'https://capitao-ia.luka-araujos.workers.dev'; // Worker capitao-ia (Workers AI) — ligado na demonstração em 27/09/2026
  // Teste num aparelho antes de publicar: localStorage 'capitao.ia.url.v1' = URL do proxy. Só vale com URL_PROXY vazio e só
  // para o próprio Worker no workers.dev: outro site da mesma origem não consegue desviar o app para outro servidor.
  if (!URL_PROXY) { try { var teste = localStorage.getItem('capitao.ia.url.v1') || ''; if (/^https:\/\/capitao\-ia\.[a-z0-9-]+\.workers\.dev\/?$/.test(teste)) URL_PROXY = teste; } catch (e) {} }
  if (!/^https:\/\/[^\s]+$/.test(URL_PROXY)) URL_PROXY = '';
  var KC = 'capitao.ia.chave.v1';
  var ESPERA = 20000; // sem resposta nesse tempo → o chat fica com a resposta local

  // Ativar este aparelho: abrir com #ia=ativar e colar a CHAVE_APP na caixa que aparece. A chave NUNCA passa pelo
  // endereço (o endereço fica no histórico do navegador, que pode sincronizar entre aparelhos). #ia=sair apaga a chave.
  // Qualquer outro valor em #ia= é ignorado. O par ia=… sai do endereço; os outros (#q=, #tele=…) continuam.
  try {
    var m = location.hash.match(/(?:^#|&)ia=([^&]+)/);
    if (m) {
      var resto = location.hash.slice(1).split('&').filter(function (p) { return p && p.indexOf('ia=') !== 0; }).join('&');
      history.replaceState(null, '', location.pathname + location.search + (resto ? '#' + resto : ''));
      var c = decodeURIComponent(m[1]);
      if (c === 'sair') localStorage.removeItem(KC);
      else if (c === 'ativar') {
        var dig = window.prompt('Cole a chave da IA na nuvem (CHAVE_APP). Ela fica só neste aparelho.');
        if (dig && dig.trim()) localStorage.setItem(KC, dig.trim());
      }
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
        if (j.parou === 'max_tokens') return null; // cortada: não passa por resposta completa (a local vem inteira)
        if (/^\s*\**\s*SEM DADOS/i.test(j.texto)) return null; // a IA achou que os trechos não respondem: fica a local, que tem o trecho e a fonte
        // Provedor e modelo vêm do proxy (Workers AI · llama-3.3-70b-…, Claude API · claude-opus-5); sem eles, só "IA na nuvem".
        var quem = [j.provedor, j.modelo].filter(function (x) { return typeof x === 'string' && x; }).map(function (x) { return x.replace(/^@cf\/[^/]+\//, '').slice(0, 60); }).join(' · ');
        return { text: j.texto.trim(), src: 'Fonte: IA na nuvem' + (quem ? ' (' + quem + ')' : '') + ' · só com as fontes enviadas pelo app', key: 'ia' };
      }, function () { clearTimeout(t); return null; });
  }

  window.CapitaoIA = { ativa: ativa, perguntar: perguntar };
})();
