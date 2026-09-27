/* Capitão IA — service worker (rede primeiro; cache só como reserva offline).
   Instala já com todas as telas: a 1ª tela aberta carrega antes do SW e nunca entraria no cache.
   Offline sem a página no cache → aviso fixo com SOS (nunca o index.html, que redireciona e podia entrar em laço).
   Lançar versão: CACHE aqui = VERSAO em capitao-auth.js = tabela do README. Arquivo novo usado offline → CORE/TELAS. */
const CACHE = 'capitao-site-v1.0.3';
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
  './capitao-clima.js', './capitao-voz.js', './capitao-barra.js', './capitao-telemetria.js', './capitao-moldura.js', './base-conhecimento.json',
  './deck-stage.js', './manifest.webmanifest', './Guia-Rapido-Capitao-IA.pdf',
  './assets/logo-wonderboat.png', './assets/icon-192.png', './assets/icon-512.png', './assets/icon-maskable-512.png', './assets/favicon_64.png', './assets/apple-touch-icon.png'
].concat(TELAS.map((t) => './' + t + '.dc.html'));
// React (unpkg, versão fixa): sem ele nenhuma tela abre offline. Melhor esforço — se falhar aqui, entra no cache no próximo uso online.
const CDN = [
  'https://unpkg.com/react@18.3.1/umd/react.production.min.js',
  'https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js'
];
self.addEventListener('install', (e) => {
  self.skipWaiting();
  // Arquivos do site: tudo ou nada (se um falhar, a instalação falha e o navegador tenta de novo na próxima visita).
  e.waitUntil(caches.open(CACHE).then((c) => Promise.all([
    c.addAll(CORE.map((u) => new Request(u, { cache: 'no-cache' }))),
    Promise.all(CDN.map((u) => c.match(u).then((hit) => hit || c.add(new Request(u, { mode: 'cors' }))).catch(() => null)))
  ])));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
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
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const same = url.origin === self.location.origin;
  const cdn = /(^|\.)unpkg\.com$/.test(url.hostname);
  if (!same && !cdn) return; // clima, maré e proxies: sempre da rede (sem cache aqui)
  e.respondWith(
    fetch(req).then((res) => {
      if (res && (res.ok || res.type === 'opaque')) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {}); }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: same }).then((hit) => hit || (req.mode === 'navigate' ? semInternet() : Response.error())))
  );
});
