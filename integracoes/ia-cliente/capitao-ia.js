/* Capitão IA — IA na nuvem via proxy protegido (Worker `capitao-ia`) · lado do app.
   MODELO do cliente: a cópia ligada é a da raiz (capitao-ia.js), com a URL do Worker preenchida — o teste testes/chat_ia.py
   confere que só essa linha difere. Aqui, sem URL configurada, nada é buscado e o chat segue 100% local (respostas prontas +
   base de bordo + SEM DADOS).
   Serve aos dois proxies (mesmo contrato): integracoes/workers-ai/ (gratuito) ou integracoes/claude-api/ (pago).
   Nenhuma chave de provedor passa por aqui: o app só conhece a URL do proxy e a CHAVE_APP deste aparelho. */
(function () {
  if (window.CapitaoIA) return;
  var URL_PROXY = ''; // ex.: 'https://capitao-ia.<conta>.workers.dev'
  // Teste num aparelho antes de publicar: localStorage 'capitao.ia.url.v1' = URL do proxy. Só vale com URL_PROXY vazio e só
  // para o próprio Worker no workers.dev: outro site da mesma origem não consegue desviar o app para outro servidor.
  if (!URL_PROXY) { try { var teste = localStorage.getItem('capitao.ia.url.v1') || ''; if (/^https:\/\/capitao\-ia\.[a-z0-9-]+\.workers\.dev\/?$/.test(teste)) URL_PROXY = teste; } catch (e) {} }
  if (!/^https:\/\/[^\s]+$/.test(URL_PROXY)) URL_PROXY = '';
  var VERSAO = '1.0.8'; // = VERSAO do capitao-auth.js e do capitao-brain.js (o capitao-app.js recarrega se vierem misturados)
  var KC = 'capitao.ia.chave.v1';
  var ESPERA = 15000; // sem resposta nesse tempo → o chat fica com a resposta local
  var ULTIMA = { falha: '' };
  var ORIGEM_APP = 'https://v2.capitaoia.com.br'; // a única origem que o Worker aceita (ORIGENS): outra dá erro de CORS, que parece "sem conexão"
  var abriuCaixa = false; // a caixa da chave já abriu nesta tela (não abre de novo pela intenção guardada)

  // A CHAVE_APP é um token longo (letras, números, - e _). Colada do WhatsApp, de notas ou do arquivo, costuma vir com
  // "CHAVE_APP:", aspas, espaços, quebra de linha ou caracteres invisíveis: fica só o token. Texto sem token longo passa
  // só aparado (chave de teste).
  function normalizaChave(s) {
    s = String(s == null ? '' : s).replace(/[\u00AD\u200B-\u200F\u202A-\u202E\u2060-\u2064\uFEFF]/g, '').replace(/\u00A0/g, ' ');
    var m = s.match(/CHAVE_APP\s*[:=]?\s*["'`\u201C\u201D\u2018\u2019]?([A-Za-z0-9_-]{32,})/i); // linha do arquivo colada inteira
    if (m) return m[1];
    var t = (s.match(/[A-Za-z0-9_-]{32,}/g) || []).sort(function (a, b) { return b.length - a.length; })[0];
    return t || s.replace(/^[\s"'`\u201C\u201D\u2018\u2019]+|[\s"'`\u201C\u201D\u2018\u2019]+$/g, '');
  }
  // Onde a chave fica: o app instalado (tela de início) e o navegador guardam à parte, mesmo no mesmo celular.
  function onde() { try { return (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone ? 'no app instalado' : 'neste navegador'; } catch (e) { return 'neste navegador'; } }
  // Chave que dá para mandar no cabeçalho: só ASCII visível, 8 a 256 letras (acento ou símbolo fora disso faz o fetch falhar).
  function chaveValida(k) { return /^[\x21-\x7e]{8,256}$/.test(k); }

  // Ativar este aparelho: abrir com #ia=ativar (ou tocar em "Ativar IA na nuvem" no chat) e colar a CHAVE_APP na caixa que
  // aparece. A chave NUNCA passa pelo endereço (o endereço fica no histórico do navegador, que pode sincronizar entre
  // aparelhos). #ia=sair apaga a chave. Qualquer outro valor em #ia= é ignorado. O par ia=… sai do endereço; os outros
  // (#q=, #tele=…) continuam. Vale ao abrir a tela e também depois (hashchange: o botão do chat, o app instalado sem barra).
  // Depois de colar, a chave é testada no servidor (sem gastar a cota da IA) e o resultado aparece numa caixa.
  function lerHash() {
    try {
      var m = location.hash.match(/(?:^#|&)ia=([^&]+)/);
      if (!m) return;
      var resto = location.hash.slice(1).split('&').filter(function (p) { return p && p.indexOf('ia=') !== 0; }).join('&');
      history.replaceState(null, '', location.pathname + location.search + (resto ? '#' + resto : ''));
      var c = decodeURIComponent(m[1]);
      if (c === 'sair') { localStorage.removeItem(KC); avisa('IA na nuvem desligada ' + onde() + '.'); }
      else if (c === 'ativar') { try { sessionStorage.setItem('capitao.ia.ativar', '1'); } catch (e) {} ativar(); }
    } catch (e) {}
  }
  // A chave colada é TESTADA ANTES de ser guardada: chave recusada nunca apaga uma que funcionava. Sem rede para testar,
  // só guarda se não havia chave. A caixa fechada sem resposta pode ser a tela recarregando (versão nova): o pedido de
  // ativar só é esquecido depois de 1,5 s — se a tela sumiu antes, ele continua e a caixa reabre na tela recarregada.
  function ativar() {
    abriuCaixa = true;
    var anterior = chave();
    var dig = window.prompt('Cole a chave da IA na nuvem (CHAVE_APP). Ela fica guardada ' + onde() + '.');
    if (dig == null) { setTimeout(esquece, 1500); return; }
    esquece();
    var k = normalizaChave(dig);
    if (!chaveValida(k)) { avisa('Isso não parece a chave da IA na nuvem: cole só a CHAVE_APP (letras, números, - e _), sem nome nem aspas. ' + (anterior ? 'A chave anterior continua guardada.' : 'Nada foi guardado.')); return; }
    testar(k).then(function (t) {
      if (!(t.ok || t.status === 429 || t.semServidor || (t.rede && !anterior))) { avisa(t.texto + (anterior ? ' A chave anterior continua guardada.' : ' Nada foi guardado.')); return; }
      try { localStorage.setItem(KC, k); } catch (e) { avisa('Este navegador não deixou guardar a chave (armazenamento bloqueado).'); return; }
      try { window.dispatchEvent(new CustomEvent('capitao-ia', { detail: { estado: 'ativada' } })); } catch (e) {}
      var aqui = onde();
      avisa(t.ok ? 'IA na nuvem ativada ' + aqui + ' ✓ — o servidor aceitou a chave. Pode perguntar.' + (aqui === 'neste navegador' ? ' Se você usa o app instalado na tela de início, ative também por lá: ele guarda à parte.' : '')
        : 'Chave guardada ' + aqui + '. ' + t.texto);
    });
  }
  function esquece() { try { sessionStorage.removeItem('capitao.ia.ativar'); } catch (e) {} }
  function avisa(msg) { setTimeout(function () { try { window.alert(msg); } catch (e) {} }, 0); }
  if (!window.CapitaoRedirecionando) lerHash();
  var api = {}; // preenchido no fim; o #ia= que chega depois vale só para o cliente em uso (window.CapitaoIA)
  window.addEventListener('hashchange', function () { if (window.CapitaoIA === api) lerHash(); });
  // Link #ia=ativar aberto sem sessão: o login tira o #ia= do endereço (nada de chave no ?next=), mas guarda a intenção
  // (capitao-auth.js, sessionStorage 'capitao.ia.ativar'). Voltando logado a uma tela de chat, a caixa abre. O mesmo vale
  // para a caixa fechada por uma recarga de versão (ativar()).
  try { if (!window.CapitaoRedirecionando && !abriuCaixa && sessionStorage.getItem('capitao.ia.ativar') === '1' && (!window.CapitaoAuth || !window.CapitaoAuth.logado || window.CapitaoAuth.logado())) setTimeout(function () { if (!abriuCaixa && window.CapitaoIA === api) ativar(); }, 600); } catch (e) {}
  // Chave guardada antes da 1.0.6 também passa pela limpeza (uma chave colada com "CHAVE_APP:" volta a valer).
  function chave() { try { return normalizaChave(localStorage.getItem(KC) || ''); } catch (e) { return ''; } }
  // 'ligada' · 'sem-chave' (aparelho não ativado) · 'chave-invalida' (guardada, mas não dá para mandar) · 'sem-rede' ·
  // 'desligada' (sem URL do proxy)
  function estado() {
    if (!URL_PROXY) return 'desligada';
    var k = chave(); if (!k) return 'sem-chave'; if (!chaveValida(k)) return 'chave-invalida';
    if (navigator && navigator.onLine === false) return 'sem-rede';
    return 'ligada';
  }
  function ativa() { return estado() === 'ligada'; }
  // Frase curta para a linha da fonte quando a IA não entrou (a tela mostra a resposta local e o porquê). As que pedem
  // ativação falam em "chave" ou "desligada neste aparelho" (a tela mostra o botão Ativar IA na nuvem).
  function aviso() {
    var e = estado();
    return e === 'sem-chave' ? 'IA na nuvem desligada neste aparelho' : e === 'chave-invalida' ? 'a chave guardada neste aparelho é inválida — ative de novo' : e === 'sem-rede' ? 'sem internet: IA na nuvem fora' : '';
  }
  function falha() { return ULTIMA.falha; }
  function motivo(e) {
    var s = e && e.status, j = e && e.j, m = j && typeof j.erro === 'string' ? j.erro.replace(/\s+/g, ' ').slice(0, 90) : '';
    if (e && e.name === 'AbortError') return 'IA na nuvem demorou demais';
    if (s === 401) return 'IA na nuvem recusou a chave deste aparelho — ative de novo';
    if (s === 429) return 'IA na nuvem: limite de perguntas atingido — tente daqui a pouco';
    if (s === 503) return 'IA na nuvem fora agora' + (m ? ': ' + m : '');
    if (s) return 'IA na nuvem não respondeu (' + s + (m ? ': ' + m : '') + ')';
    return 'sem conexão com a IA na nuvem' + (location.origin !== ORIGEM_APP ? ' — este endereço não é o do app (' + ORIGEM_APP + ')' : '');
  }
  // Teste da chave e do caminho até o Worker SEM gastar a cota da IA: pergunta sem ficha, sem trecho e sem leitura → o
  // Worker confere origem e chave e responde 422 (sem_fontes) antes de chamar o modelo. 422 = tudo certo; 401 = chave
  // recusada; sem resposta = sem conexão (ou origem que não é a do app: o CORS falha antes). Nunca rejeita.
  // testar(cand): testa a chave candidata (antes de guardar); sem argumento, a chave guardada.
  function testar(cand) {
    var k = cand == null ? chave() : cand;
    if (!URL_PROXY) return Promise.resolve({ ok: false, status: 0, semServidor: true, texto: 'IA na nuvem sem endereço neste app.' });
    if (!k) return Promise.resolve({ ok: false, status: 0, texto: 'Nenhuma chave guardada neste aparelho: toque em Ativar IA na nuvem e cole a CHAVE_APP.' });
    if (!chaveValida(k)) return Promise.resolve({ ok: false, status: 0, texto: 'A chave guardada neste aparelho tem caracteres que não servem: toque em Ativar IA na nuvem e cole só a CHAVE_APP.' });
    if (!window.fetch) return Promise.resolve({ ok: false, status: 0, texto: 'Este navegador não consegue falar com a IA na nuvem.' });
    var ctl = window.AbortController ? new AbortController() : null, t = setTimeout(function () { if (ctl) ctl.abort(); }, ESPERA);
    return fetch(URL_PROXY, {
      method: 'POST', cache: 'no-store', signal: ctl ? ctl.signal : undefined,
      headers: { 'Content-Type': 'application/json', 'X-Capitao-Chave': k },
      body: JSON.stringify({ pergunta: 'teste da chave', trechos: [], contexto: '', ficha: '', historico: [] })
    }).then(function (r) {
      clearTimeout(t);
      if (r.status === 422) return { ok: true, status: 422, texto: 'Chave aceita pelo servidor da IA na nuvem ✓ (teste sem gastar a cota).' };
      if (r.status === 401) return { ok: false, status: 401, texto: 'O servidor RECUSOU a chave deste aparelho: confira a CHAVE_APP e cole de novo em Ativar IA na nuvem.' };
      if (r.status === 403) return { ok: false, status: 403, texto: 'O servidor recusou este endereço do app (origem): abra por https://v2.capitaoia.com.br.' };
      if (r.status === 429) return { ok: false, status: 429, texto: 'Chave ok, mas o limite de perguntas por minuto foi atingido: tente daqui a pouco.' };
      return { ok: false, status: r.status, texto: 'O servidor da IA respondeu ' + r.status + ' ao teste.' };
    }, function (e) {
      clearTimeout(t);
      return { ok: false, status: 0, rede: true, texto: e && e.name === 'AbortError' ? 'O servidor da IA demorou demais para responder ao teste.' : 'Sem conexão com o servidor da IA na nuvem (internet, bloqueio de rede ou navegador).' + (location.origin !== ORIGEM_APP ? ' Este endereço (' + location.origin + ') não é o do app: o servidor só aceita ' + ORIGEM_APP + '.' : '') };
    });
  }
  // Linhas para o "diagnóstico" do chat: versão deste cliente, estado, chave (só o tamanho) e o motivo da última falha.
  function diagnostico() {
    var k = chave(), e = estado();
    return [
      '• Cliente da IA ' + VERSAO + ' · endereço do servidor ' + (URL_PROXY ? 'configurado' : 'SEM (IA desligada neste app)'),
      '• IA na nuvem: ' + (e === 'ligada' ? 'LIGADA ' + onde() : e === 'sem-chave' ? 'DESLIGADA ' + onde() + ' (sem chave)' : e === 'chave-invalida' ? 'DESLIGADA (chave guardada inválida)' : e === 'sem-rede' ? 'sem internet' : 'desligada'),
      '• Chave: ' + (k ? 'guardada (' + k.length + ' caracteres)' : 'nenhuma'),
      '• Última falha: ' + (ULTIMA.falha || 'nenhuma nesta sessão')
    ];
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

  window.CapitaoIA = Object.assign(api, { VERSAO: VERSAO, ativa: ativa, estado: estado, aviso: aviso, falha: falha, perguntar: perguntar, testar: testar, diagnostico: diagnostico, normalizaChave: normalizaChave, chaveValida: chaveValida });
})();
