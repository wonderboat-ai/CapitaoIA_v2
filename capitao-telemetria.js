/* Capitão IA — telemetria ao vivo do coletor (coletor NMEA → Drive → proxy protegido → app).
   DESLIGADA por padrão: sem URL configurada, nada é buscado e o app segue com o snapshot do capitao-dados.js.
   Para ligar (junto com o login no servidor): publicar o Worker de integracoes/telemetria-worker/, pôr a URL em URL_PROXY
   e abrir o app uma vez por aparelho com #tele=<chave> no fim do endereço (a chave fica só no aparelho).
   Nunca aponte para um link público do Drive: o arquivo tem a posição do barco. */
(function () {
  if (window.CapitaoTelemetria) return;
  var URL_PROXY = ''; // ex.: 'https://capitao-telemetria.<conta>.workers.dev'
  // Teste num aparelho antes de publicar: localStorage 'capitao.telemetria.url.v1' = URL do proxy. Só vale com URL_PROXY vazio e só
  // para o próprio Worker no workers.dev: outro site da mesma origem não consegue desviar o app para outro servidor.
  if (!URL_PROXY) { try { var teste = localStorage.getItem('capitao.telemetria.url.v1') || ''; if (/^https:\/\/capitao\-telemetria\.[a-z0-9-]+\.workers\.dev\/?$/.test(teste)) URL_PROXY = teste; } catch (e) {} }
  if (!/^https:\/\/[^\s]+$/.test(URL_PROXY)) URL_PROXY = '';
  var KC = 'capitao.telemetria.chave.v1', KD = 'capitao.telemetria.ultima.v1';
  var D = window.CapitaoDados || {}, TZ = (D.embarcacao && D.embarcacao.fuso) || 'America/Sao_Paulo';
  var VELHA = 10 * 60000; // leitura com mais de 10 min não conta como "ao vivo"
  // Cadência por estado (padrão do template): navegando (SOG ≥ 1 nó) 30 s até 5 nós, 10 s até 12 nós, 5 s acima;
  // atracado/fundeado 2 min nos primeiros 30 min, 5 min até 1 h, 10 min depois disso.
  var NAVEGA = 1, atracadoDesde = 0;
  function intervalo() {
    var s = ultima && idade() < VELHA ? +ultima.sog_nos : NaN;
    if (s >= NAVEGA) { atracadoDesde = 0; return s > 12 ? 5000 : s > 5 ? 10000 : 30000; }
    if (!atracadoDesde) atracadoDesde = Date.now();
    var t = Date.now() - atracadoDesde;
    return t < 30 * 60000 ? 120000 : t < 60 * 60000 ? 300000 : 600000;
  }

  // #tele=<chave> no endereço: guarda a chave neste aparelho e limpa o endereço (não fica no histórico).
  try {
    var m = location.hash.match(/(?:^#|&)tele=([^&]+)/);
    if (m) {
      var c = decodeURIComponent(m[1]);
      if (c === 'sair') localStorage.removeItem(KC); else localStorage.setItem(KC, c);
      // Tira só o par tele=…; os outros parâmetros do endereço (#q=, #tele=, #ia=…) continuam no hash.
      var resto = location.hash.slice(1).split('&').filter(function (p) { return p && p.indexOf('tele=') !== 0; }).join('&');
      history.replaceState(null, '', location.pathname + location.search + (resto ? '#' + resto : ''));
    }
  } catch (e) {}
  function chave() { try { return localStorage.getItem(KC) || ''; } catch (e) { return ''; } }
  function ativa() { return !!(URL_PROXY && chave()); }

  var ultima = null;
  try { ultima = ativa() ? JSON.parse(localStorage.getItem(KD) || 'null') : null; } catch (e) {}
  function idade() { return ultima && ultima.timestamp_utc ? Date.now() - Date.parse(ultima.timestamp_utc) : Infinity; }
  function atual() { return ativa() && idade() < VELHA ? ultima : null; }
  function avisa() { try { window.dispatchEvent(new CustomEvent('capitao-telemetria', { detail: ultima })); } catch (e) {} }

  var busy = false, tempo = 0;
  function busca() {
    clearTimeout(tempo);
    if (!ativa() || busy || document.hidden || (navigator && navigator.onLine === false)) { tempo = setTimeout(busca, intervalo()); return; }
    busy = true;
    var ctl = window.AbortController ? new AbortController() : null, corta = ctl ? setTimeout(function () { ctl.abort(); }, 8000) : 0;
    fetch(URL_PROXY, { headers: { 'X-Capitao-Chave': chave() }, cache: 'no-store', signal: ctl ? ctl.signal : undefined })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (j) {
        if (!j || !j.timestamp_utc) return;
        ultima = j; try { localStorage.setItem(KD, JSON.stringify(j)); } catch (e) {}
        avisa();
      })
      .catch(function () {}) // erro, demora ou sem internet → segue com o snapshot local
      .then(function () { clearTimeout(corta); busy = false; tempo = setTimeout(busca, intervalo()); });
  }
  if (ativa()) { busca(); document.addEventListener('visibilitychange', function () { if (!document.hidden) busca(); }); }

  // 26°59,58'S 048°36,84'W
  function coord(v, pos, neg, g) {
    var a = Math.abs(v), d = Math.floor(a), mn = (a - d) * 60;
    return (g === 3 ? ('00' + d).slice(-3) : d) + '°' + mn.toFixed(2).replace('.', ',').padStart(5, '0') + "'" + (v < 0 ? neg : pos);
  }
  function posicao(t) { return coord(t.lat, 'N', 'S', 2) + ' ' + coord(t.lon, 'E', 'W', 3); }
  function hora(t) {
    try { return new Intl.DateTimeFormat('pt-BR', { timeZone: TZ, hour: '2-digit', minute: '2-digit' }).format(new Date(t.timestamp_utc)); } catch (e) { return ''; }
  }

  window.CapitaoTelemetria = { ativa: ativa, atual: atual, idade: idade, posicao: posicao, hora: hora, busca: busca, coord: coord };
})();
