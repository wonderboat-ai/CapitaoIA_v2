/* Capitão IA — IA na nuvem via proxy protegido (Worker `capitao-ia`) · lado do app.
   LIGADO NA DEMONSTRAÇÃO (1.0.4; ficha de bordo, histórico e conversa por voz na 1.0.5): carregado pelo Main e pelo H2.
   Cópia de integracoes/ia-cliente/capitao-ia.js com a URL do Worker preenchida (o teste testes/chat_ia.py confere que só essa
   linha difere). Sem a CHAVE_APP no aparelho (#ia=ativar ou o botão "Ativar IA na nuvem" do chat, depois do login), nada é
   buscado e o chat segue 100% local (respostas prontas + base de bordo + SEM DADOS), com o aviso na linha da fonte.
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
  var ESPERA = 15000; // sem resposta nesse tempo → o chat fica com a resposta local
  var ULTIMA = { falha: '' };

  // Ativar este aparelho: abrir com #ia=ativar (ou tocar em "Ativar IA na nuvem" no chat) e colar a CHAVE_APP na caixa que
  // aparece. A chave NUNCA passa pelo endereço (o endereço fica no histórico do navegador, que pode sincronizar entre
  // aparelhos). #ia=sair apaga a chave. Qualquer outro valor em #ia= é ignorado. O par ia=… sai do endereço; os outros
  // (#q=, #tele=…) continuam. Vale ao abrir a tela e também depois (hashchange: o botão do chat, o app instalado sem barra).
  function lerHash() {
    try {
      var m = location.hash.match(/(?:^#|&)ia=([^&]+)/);
      if (!m) return;
      var resto = location.hash.slice(1).split('&').filter(function (p) { return p && p.indexOf('ia=') !== 0; }).join('&');
      history.replaceState(null, '', location.pathname + location.search + (resto ? '#' + resto : ''));
      var c = decodeURIComponent(m[1]);
      if (c === 'sair') localStorage.removeItem(KC);
      else if (c === 'ativar') {
        var dig = window.prompt('Cole a chave da IA na nuvem (CHAVE_APP). Ela fica só neste aparelho.');
        if (dig && dig.trim()) localStorage.setItem(KC, dig.trim());
      }
    } catch (e) {}
  }
  lerHash();
  window.addEventListener('hashchange', lerHash);
  function chave() { try { return localStorage.getItem(KC) || ''; } catch (e) { return ''; } }
  // 'ligada' · 'sem-chave' (aparelho não ativado) · 'sem-rede' · 'desligada' (sem URL do proxy)
  function estado() { if (!URL_PROXY) return 'desligada'; if (!chave()) return 'sem-chave'; if (navigator && navigator.onLine === false) return 'sem-rede'; return 'ligada'; }
  function ativa() { return estado() === 'ligada'; }
  // Frase curta para a linha da fonte quando a IA não entrou (a tela mostra a resposta local e o porquê).
  function aviso() { var e = estado(); return e === 'sem-chave' ? 'IA na nuvem desligada neste aparelho' : e === 'sem-rede' ? 'sem internet: IA na nuvem fora' : ''; }
  function falha() { return ULTIMA.falha; }
  function motivo(e) {
    var s = e && e.status, j = e && e.j, m = j && typeof j.erro === 'string' ? j.erro.replace(/\s+/g, ' ').slice(0, 90) : '';
    if (e && e.name === 'AbortError') return 'IA na nuvem demorou demais';
    if (s === 401) return 'IA na nuvem recusou a chave deste aparelho — ative de novo';
    if (s === 429) return 'IA na nuvem: limite de perguntas atingido — tente daqui a pouco';
    if (s === 503) return 'IA na nuvem fora agora' + (m ? ': ' + m : '');
    if (s) return 'IA na nuvem não respondeu (' + s + (m ? ': ' + m : '') + ')';
    return 'sem conexão com a IA na nuvem';
  }
  // Texto simples na tela e na voz: sem negrito, título, crase de código; lista "- x" vira "• x".
  function limpaMd(s) {
    return String(s).replace(/\r/g, '').replace(/\*\*([^*\n]+)\*\*/g, '$1').replace(/__([^_\n]+)__/g, '$1').replace(/`([^`\n]+)`/g, '$1')
      .replace(/^[ \t]{0,3}#{1,6}[ \t]+/gm, '').replace(/^[ \t]*[-*][ \t]+/gm, '• ').replace(/\n{3,}/g, '\n\n').trim();
  }

  // perguntar(pergunta, hits, contexto, extra) → Promise<{ text, src, key: 'ia', semDados } | null>
  //   hits: o retorno de CapitaoBrain.buscaBase(pergunta, 3) — [{ d: { fonte, pag, secao, texto }, nota }]
  //   contexto: leitura que a tela já mostra, em texto curto (pode ser '')
  //   extra: { ficha: CapitaoBrain.ficha() — o que o app sabe agora, com as fontes; historico: [{ papel: 'usuario'|'capitao', texto }] }
  //   null = IA desligada, sem rede, demora, recusa ou erro → a tela mantém a resposta local; falha() diz o porquê.
  //   semDados = a IA também não achou (a tela decide: com trecho do guia na resposta local, fica a local).
  function perguntar(pergunta, hits, contexto, extra) {
    ULTIMA.falha = '';
    if (!ativa() || !window.fetch) { ULTIMA.falha = aviso(); return Promise.resolve(null); }
    extra = extra || {};
    var trechos = (hits || []).slice(0, 3).map(function (h) { var d = h && h.d ? h.d : h; return { fonte: d.fonte, pag: d.pag, secao: d.secao, texto: d.texto }; });
    var historico = (Array.isArray(extra.historico) ? extra.historico : []).slice(-6).map(function (x) { return { papel: x && x.papel === 'capitao' ? 'capitao' : 'usuario', texto: String((x && x.texto) || '').slice(0, 600) }; }).filter(function (x) { return x.texto.trim(); });
    var ctl = window.AbortController ? new AbortController() : null, t = setTimeout(function () { if (ctl) ctl.abort(); }, ESPERA);
    return fetch(URL_PROXY, {
      method: 'POST', cache: 'no-store', signal: ctl ? ctl.signal : undefined,
      headers: { 'Content-Type': 'application/json', 'X-Capitao-Chave': chave() },
      body: JSON.stringify({ pergunta: String(pergunta || '').slice(0, 500), trechos: trechos, contexto: contexto ? String(contexto).slice(0, 2000) : '', ficha: extra.ficha ? String(extra.ficha).slice(0, 12000) : '', historico: historico })
    }).then(function (r) {
      return r.json().catch(function () { return null; }).then(function (j) { if (!r.ok) { var e = new Error('HTTP ' + r.status); e.status = r.status; e.j = j; throw e; } return j; });
    }).then(function (j) {
      clearTimeout(t);
      if (!j || typeof j.texto !== 'string' || !j.texto.trim()) { ULTIMA.falha = 'IA na nuvem sem resposta'; return null; }
      if (j.parou === 'max_tokens') { ULTIMA.falha = 'resposta da IA cortada no limite'; return null; } // a local vem inteira
      // A linha "Fonte: …" da IA sai do texto e vai para a linha da fonte, junto com quem respondeu.
      var linhas = limpaMd(j.texto).split('\n'), fonte = '';
      for (var i = linhas.length - 1; i >= 0; i--) {
        var f = linhas[i].match(/^\s*fontes?\s*:\s*(.+)$/i);
        if (f) { fonte = f[1].trim(); linhas.splice(i, 1); break; }
        if (linhas[i].trim()) break; // só a última linha com texto
      }
      var texto = linhas.join('\n').trim();
      if (!texto) { ULTIMA.falha = 'IA na nuvem sem resposta'; return null; }
      // Provedor e modelo vêm do proxy (Workers AI · llama-3.3-70b-…, Claude API · claude-opus-5); sem eles, só "IA na nuvem".
      var quem = [j.provedor, j.modelo].filter(function (x) { return typeof x === 'string' && x; }).map(function (x) { return x.replace(/^@cf\/[^/]+\//, '').slice(0, 60); }).join(' · ');
      return { text: texto, src: 'Fonte: ' + (fonte ? fonte.slice(0, 220) + ' · via ' : '') + 'IA na nuvem' + (quem ? ' (' + quem + ')' : ''), key: 'ia', semDados: /^\s*SEM DADOS/i.test(texto) };
    }, function (e) { clearTimeout(t); ULTIMA.falha = motivo(e); return null; })
      .catch(function () { clearTimeout(t); ULTIMA.falha = 'IA na nuvem sem resposta'; return null; });
  }

  window.CapitaoIA = { ativa: ativa, estado: estado, aviso: aviso, falha: falha, perguntar: perguntar };
})();
