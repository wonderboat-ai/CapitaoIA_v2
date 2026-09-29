/* Capitão IA — service worker (rede primeiro; cache só como reserva offline).
   Instala já com todas as telas: a 1ª tela aberta carrega antes do SW e nunca entraria no cache.
   Offline sem a página no cache → aviso fixo com SOS (nunca o index.html, que redireciona e podia entrar em laço).
   Lançar versão: CACHE aqui = VERSAO em capitao-auth.js = VERSAO em capitao-brain.js e capitao-ia.js = tabela do README.
   Arquivo novo usado offline → CORE/TELAS. */
const CACHE = 'capitao-site-v1.0.9';
const TELAS = [
  'Main', 'H2-Home-Mobile', 'S1-SOS-Web', 'S2-SOS-Mobile', 'C3-Leme-Alerta', 'Manual-Capitao-IA',
  'A1-Ponte-Web', 'A2-Ponte-Mobile', 'A3-Ponte-Editar', 'B1-Carta-Web', 'B2-Carta-Mobile', 'B3-Carta-Resposta',
  'C1-Leme-Web', 'C2-Leme-Mobile', 'E1-Navegando-Gatilhos', 'E2-Navegando-Sintoma',
  'F1-FAQ-Hub-Web', 'F1-FAQ-Hub', 'F2-FAQ-Estabilizador-Web', 'F2-FAQ-Estabilizador', 'F3-FAQ-Eletronicos-Web', 'F3-FAQ-Eletronicos',
  'F4-FAQ-Gerador-Web', 'F4-FAQ-Gerador', 'F5-FAQ-Climatizacao-Web', 'F5-FAQ-Climatizacao',
  'G1-Documentos-Web', 'G1-Documentos-Mobile', 'G2-Abastecimento-Web', 'G2-Abastecimento-Mobile',
  'G3-Diario-Web', 'G3-Diario-Mobile', 'G4-Equipe-Web', 'G4-Equipe-Mobile', 'H3-Atalhos-Editar-Web', 'H3-Atalhos-Editar'
];
const CORE = [
  './', './index.html', './login.html', './support.js', './capitao-dados.js', './capitao-auth.js', './capitao-app.js', './capitao-theme.js', './capitao-brain.js',
  './capitao-clima.js', './capitao-voz.js', './capitao-barra.js', './capitao-telemetria.js', './capitao-moldura.js', './capitao-ia.js', './base-conhecimento.json',
  './capitao-simbolo.js', './capitao-rosto.js', './deck-stage.js', './manifest.webmanifest',
  './assets/wonderhub-simbolo.png', './assets/wonderhub-assinatura.jpg', './assets/logo-wonderboat-240.png', './assets/wonderhub-favicon.ico',
  './assets/wonderhub-apple-touch-icon.png', './assets/wonderhub-icon-192.png'
].concat(TELAS.map((t) => './' + t + '.dc.html'));
// React (unpkg, versão fixa): sem ele nenhuma tela abre offline. Melhor esforço — se falhar aqui, entra no cache no próximo uso online.
const CDN = [
  'https://unpkg.com/react@18.3.1/umd/react.production.min.js',
  'https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js'
];
// Melhor esforço, fora do "tudo ou nada" e fora da instalação: o PDF do Guia rápido (1,7 MB) atrasava — ou, com a conexão
// caindo no meio, derrubava — a instalação de versão nova no 4G. Idem as imagens grandes que não servem à emergência (a
// logo Wonder BOAT do fecho do Manual e os ícones 512 do app instalado). Baixados depois de a versão ativar.
const EXTRA = ['./assets/logo-wonderboat.png', './assets/wonderhub-icon-512.png', './assets/wonderhub-icon-maskable-512.png', './Guia-Rapido-Capitao-IA.pdf'];
self.addEventListener('install', (e) => {
  self.skipWaiting();
  // Arquivos do site: tudo ou nada (se um falhar, a instalação falha e o navegador tenta de novo na próxima visita).
  // React (versão fixa): reaproveita a cópia de qualquer versão anterior; sem ela, busca com prazo (não prende a instalação).
  e.waitUntil(caches.open(CACHE).then((c) => Promise.all([
    c.addAll(CORE.map((u) => new Request(u, { cache: 'no-cache' }))),
    Promise.all(CDN.map((u) => comPrazo(caches.match(u).then((hit) => hit ? c.put(u, hit) : c.add(new Request(u, { mode: 'cors' }))), 8000).catch(() => null)))
  ])));
});
// Versão nova assumiu: apaga o cache da anterior e passa a controlar as telas abertas. Cada tela precisa recarregar para
// rodar os arquivos novos — no celular, o app instalado fica vivo na memória com o código anterior. O SW avisa
// ('nova-versao'): a tela da 1.0.7 em diante responde ('versao-ok') e recarrega sozinha num momento seguro (sem texto sendo
// digitado, conversa por voz ou resposta a caminho — capitao-app.js); a tela que não responde em 3 s (versão anterior, que
// não sabe se recarregar) o SW recarrega. O SOS nunca. Na 1ª instalação (sem cache anterior) nada recarrega. A navegação
// fica fora do waitUntil (ela espera a própria ativação e travaria). O #… sai do endereço (#q= refaria a pergunta).
const confirmadas = new Set();
self.addEventListener('message', (e) => { if (e.data && e.data.tipo === 'versao-ok' && e.source && e.source.id) confirmadas.add(e.source.id); });
self.addEventListener('activate', (e) => {
  const feito = caches.keys().then((ks) => {
    const atualizou = ks.some((k) => k !== CACHE && k.indexOf('capitao-site-') === 0);
    return Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))).then(() => self.clients.claim()).then(() => atualizou);
  });
  e.waitUntil(feito);
  feito.then((atualizou) => {
    if (!atualizou) return;
    return self.clients.matchAll({ type: 'window' }).then((cs) => {
      const abertas = cs.filter((c) => !/SOS-/.test(c.url));
      abertas.forEach((c) => { try { c.postMessage({ tipo: 'nova-versao' }); } catch (x) {} });
      return new Promise((ok) => setTimeout(ok, 3000)).then(() => abertas.forEach((c) => {
        if (confirmadas.has(c.id) || !c.navigate) return;
        c.navigate(c.url.split('#')[0]).catch(() => {});
      }));
    });
  }).catch(() => {});
  feito.then(() => caches.open(CACHE)).then((c) => Promise.all(EXTRA.map((u) => c.match(u).then((hit) => hit || c.add(new Request(u, { cache: 'no-cache' }))).catch(() => null)))).catch(() => {});
});
function semInternet() {
  const b = self.registration.scope;
  const a = 'display:inline-flex;align-items:center;min-height:48px;padding:0 20px;border-radius:14px;border:1px solid #1a2240;background:#0d1329;color:#eaf1ff;font-weight:700;font-size:14px;text-decoration:none';
  const html = '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
    + '<meta name="theme-color" content="#050816"><title>Sem internet · Capitão IA</title></head>'
    + '<body style="margin:0;background:#050816;color:#eaf1ff;font-family:\'Nimbus Sans\',\'Helvetica Neue\',Helvetica,Arial,sans-serif">'
    + '<main style="max-width:520px;margin:0 auto;padding:40px 16px;display:flex;flex-direction:column;gap:16px">'
    + '<h1 style="margin:0;font-size:22px;font-weight:800">Sem internet</h1>'
    + '<p style="margin:0;font-size:15px;line-height:1.5;color:#97a3c0">Esta tela ainda não está salva neste aparelho. Ela passa a abrir offline depois de aberta uma vez com internet. O SOS abre offline.</p>'
    + '<p style="margin:0;display:flex;gap:10px;flex-wrap:wrap">'
    + '<a href="' + b + 'S2-SOS-Mobile.dc.html" style="' + a + ';background:#d32f27;border-color:#d32f27;color:#fff">SOS · emergência</a>'
    + '<a href="' + b + 'index.html" style="' + a + '">Início</a>'
    + '<a href="" onclick="location.reload();return false" style="' + a + '">Tentar de novo</a></p></main></body></html>';
  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } });
}
// Rede primeiro DE VERDADE: o GitHub Pages manda "max-age=600", e fetch(req) comum podia devolver por até 10 min a cópia do
// cache HTTP do aparelho — depois de publicar, o celular rodava arquivo velho (ou velho misturado com novo). Arquivo do
// próprio site sempre confere com o servidor (no-cache: pergunta com o ETag; sem mudança, volta 304 e sai do cache).
// Pedido que já veio com cache 'reload'/'no-store' (recarga de versão do capitao-app.js) mantém o modo dele.
function daRede(req, same) {
  if (!same) return fetch(req);
  const modo = req.cache === 'reload' || req.cache === 'no-store' ? req.cache : 'no-cache';
  // Navegador antigo que não aceita copiar um pedido de navegação com opções: segue com o pedido original.
  try { return fetch(new Request(req, { cache: modo })); } catch (err) { return fetch(req); }
}
// Sinal fraco a bordo: conferir com o servidor não pode travar o app. Arquivo do site que não chega em 4 s sai da cópia
// guardada (a busca segue e atualiza a cópia); sem cópia, continua esperando a rede.
const PRAZO = 4000;
function comPrazo(p, ms) {
  return new Promise((ok, falha) => { const t = setTimeout(() => falha(new Error('prazo')), ms); p.then((r) => { clearTimeout(t); ok(r); }, (err) => { clearTimeout(t); falha(err); }); });
}
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const same = url.origin === self.location.origin;
  const cdn = /(^|\.)unpkg\.com$/.test(url.hostname);
  if (!same && !cdn) return; // clima, maré e proxies: sempre da rede (sem cache aqui)
  const guardado = () => caches.match(req, { ignoreSearch: same });
  const buscar = () => daRede(req, same).then((res) => {
    // Guarda sem o #…: nada do endereço depois do # vai para o cache.
    if (res && (res.ok || res.type === 'opaque')) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(same ? url.origin + url.pathname + url.search : req, copy)).catch(() => {}); }
    return res;
  });
  // React da CDN: versão fixa (com SRI), não muda — cópia guardada primeiro; sem ela, a rede. Com sinal fraco, o SOS e as
  // outras telas montam sem esperar o unpkg.
  if (cdn) { e.respondWith(guardado().then((hit) => hit || buscar())); return; }
  const rede = buscar();
  rede.catch(() => {}); // a busca que perdeu para a cópia guardada pode falhar depois: sem erro solto
  e.waitUntil(rede.catch(() => {})); // a cópia se atualiza mesmo quando a resposta saiu da reserva
  const semRede = () => guardado().then((hit) => hit || (req.mode === 'navigate' ? semInternet() : Response.error()));
  // SOS: abre na hora pela cópia guardada (a rede atualiza a cópia em segundo plano).
  if (same && req.mode === 'navigate' && /SOS-/.test(url.pathname)) { e.respondWith(guardado().then((hit) => hit || rede.catch(semRede))); return; }
  e.respondWith(comPrazo(rede, PRAZO).catch(() => guardado().then((hit) => hit || rede.catch(semRede))));
});
