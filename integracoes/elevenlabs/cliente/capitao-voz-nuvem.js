/* Capitão IA — voz em nuvem (ElevenLabs via proxy `capitao-voz`) · lado do app · OPCIONAL.
   ESTRUTURA — DESLIGADA e NÃO CARREGADA por nenhuma tela. Hoje a voz é a do aparelho (CapitaoBrain.speak, Web Speech).
   Sem URL configurada, nada é buscado. Erro, demora (> 9 s) ou sem internet → a tela usa a voz do aparelho.
   Emergência continua na voz do aparelho (funciona offline). A chave do ElevenLabs nunca passa por aqui.
   Para ligar: ver integracoes/elevenlabs/README.md. */
(function () {
  if (window.CapitaoVozNuvem) return;
  var URL_PROXY = ''; // ex.: 'https://capitao-voz.<conta>.workers.dev'
  // Teste num aparelho: localStorage 'capitao.voz.url.v1'. Só vale com URL_PROXY vazio e só para o próprio Worker no workers.dev.
  if (!URL_PROXY) { try { var teste = localStorage.getItem('capitao.voz.url.v1') || ''; if (/^https:\/\/capitao\-voz\.[a-z0-9-]+\.workers\.dev\/?$/.test(teste)) URL_PROXY = teste; } catch (e) {} }
  if (!/^https:\/\/[^\s]+$/.test(URL_PROXY)) URL_PROXY = '';
  var KC = 'capitao.voz.chave.v1', ESPERA = 9000, tocando = null;
  // #voz=<chave> guarda a chave neste aparelho e limpa o endereço; #voz=sair apaga.
  try {
    var m = location.hash.match(/(?:^#|&)voz=([^&]+)/);
    if (m) {
      var c = decodeURIComponent(m[1]);
      if (c === 'sair') localStorage.removeItem(KC); else localStorage.setItem(KC, c);
      // Tira só o par voz=…; os outros parâmetros do endereço (#q=, #tele=, #ia=…) continuam no hash.
      var resto = location.hash.slice(1).split('&').filter(function (p) { return p && p.indexOf('voz=') !== 0; }).join('&');
      history.replaceState(null, '', location.pathname + location.search + (resto ? '#' + resto : ''));
    }
  } catch (e) {}
  function chave() { try { return localStorage.getItem(KC) || ''; } catch (e) { return ''; } }
  function ativa() { return !!(URL_PROXY && chave()) && !(navigator && navigator.onLine === false); }

  // falar(texto) → Promise<boolean>: true se tocou o áudio da nuvem até o fim; false → a tela usa CapitaoBrain.speak.
  function falar(texto) {
    if (!ativa() || !window.fetch || !window.Audio) return Promise.resolve(false);
    parar();
    var ctl = window.AbortController ? new AbortController() : null, t = setTimeout(function () { if (ctl) ctl.abort(); }, ESPERA);
    return fetch(URL_PROXY, { method: 'POST', cache: 'no-store', signal: ctl ? ctl.signal : undefined, headers: { 'Content-Type': 'application/json', 'X-Capitao-Chave': chave() }, body: JSON.stringify({ texto: String(texto || '').slice(0, 1200) }) })
      .then(function (r) { clearTimeout(t); if (!r.ok) throw new Error('HTTP ' + r.status); return r.blob(); })
      .then(function (b) {
        return new Promise(function (ok) {
          var a = tocando = new Audio(URL.createObjectURL(b));
          a.onended = function () { URL.revokeObjectURL(a.src); ok(true); };
          a.onerror = function () { ok(false); };
          a.play().catch(function () { ok(false); });
        });
      }, function () { clearTimeout(t); return false; });
  }
  function parar() { if (tocando) { try { tocando.pause(); } catch (e) {} tocando = null; } }

  window.CapitaoVozNuvem = { ativa: ativa, falar: falar, parar: parar };
})();
