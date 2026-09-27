/* Capitão IA — proxy da telemetria ao vivo (Cloudflare Worker `capitao-telemetria`).
   PREPARADO — DESLIGADO: nada publicado; o app só usa se `URL_PROXY` estiver preenchido em capitao-telemetria.js.
   Lê o JSON do coletor no Google Drive com uma conta de serviço e entrega ao app, só para quem manda a chave certa.
   O arquivo do Drive continua PRIVADO (nunca use link público: tem a posição do barco).

   Segredos/variáveis (Cloudflare › Workers › capitao-telemetria › Settings › Variables):
     GOOGLE_SA_EMAIL  e-mail da conta de serviço (…@….iam.gserviceaccount.com)
     GOOGLE_SA_KEY    (segredo) chave privada PEM da conta de serviço ("-----BEGIN PRIVATE KEY-----…")
     DRIVE_FILE_ID    (segredo recomendado) ID do JSON do coletor no Drive — nunca no repositório
     CHAVE_APP        (segredo) chave longa e aleatória que o app manda no cabeçalho X-Capitao-Chave
     ORIGENS          (opcional) sites autorizados, separados por vírgula
   Proteções: só as ORIGENS, só com a CHAVE_APP, no máximo 120 leituras por minuto por IP, cache de 4 s.
   No Drive: compartilhar o JSON do coletor com o e-mail da conta de serviço (Leitor) — só esse arquivo. */
const PADRAO_ORIGENS = 'https://v2.capitaoia.com.br'; // só o app: o github.io é dividido com os outros sites da conta
const LIMITE_MIN = 120; // cadência mais rápida do app: 5 s (12/min) — folga para vários aparelhos atrás do mesmo IP
const usos = new Map(); // por instância do Worker: freio simples contra abuso
let token = null, tokenAte = 0, cache = null, cacheEm = 0;

function b64url(buf) {
  const s = typeof buf === 'string' ? btoa(buf) : btoa(String.fromCharCode(...new Uint8Array(buf)));
  return s.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
async function tokenGoogle(env) {
  if (token && Date.now() < tokenAte - 60000) return token;
  const agora = Math.floor(Date.now() / 1000);
  const cab = b64url(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const corpo = b64url(JSON.stringify({ iss: env.GOOGLE_SA_EMAIL, scope: 'https://www.googleapis.com/auth/drive.readonly', aud: 'https://oauth2.googleapis.com/token', iat: agora, exp: agora + 3600 }));
  const pem = String(env.GOOGLE_SA_KEY).replace(/\\n/g, '\n').replace(/-----[^-]+-----/g, '').replace(/\s+/g, '');
  const der = Uint8Array.from(atob(pem), (c) => c.charCodeAt(0));
  const k = await crypto.subtle.importKey('pkcs8', der, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
  const assin = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', k, new TextEncoder().encode(cab + '.' + corpo));
  const r = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion=' + cab + '.' + corpo + '.' + b64url(assin)
  });
  if (!r.ok) throw new Error('token Google ' + r.status);
  const j = await r.json();
  token = j.access_token; tokenAte = Date.now() + (j.expires_in || 3600) * 1000;
  return token;
}
function iguais(a, b) { a = String(a || ''); b = String(b || ''); if (a.length !== b.length) return false; let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0; }
function resp(status, corpo, h) { return new Response(typeof corpo === 'string' ? corpo : JSON.stringify(corpo), { status, headers: { ...h, 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' } }); }

export default {
  async fetch(req, env) {
    const origens = String(env.ORIGENS || PADRAO_ORIGENS).split(',').map((s) => s.trim()).filter(Boolean);
    const origem = req.headers.get('Origin') || '';
    if (!origens.includes(origem)) return resp(403, { erro: 'origem não autorizada' }, {});
    const h = { 'Access-Control-Allow-Origin': origem, 'Access-Control-Allow-Methods': 'GET, OPTIONS', 'Access-Control-Allow-Headers': 'X-Capitao-Chave', 'Access-Control-Max-Age': '86400', 'Vary': 'Origin' };
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: h });
    if (req.method !== 'GET') return resp(405, { erro: 'use GET' }, h);
    if (!env.CHAVE_APP || !iguais(req.headers.get('X-Capitao-Chave'), env.CHAVE_APP)) return resp(401, { erro: 'chave inválida' }, h);
    if (!env.DRIVE_FILE_ID || !env.GOOGLE_SA_EMAIL || !env.GOOGLE_SA_KEY) return resp(500, { erro: 'proxy sem configuração do Drive' }, h);

    const ip = req.headers.get('CF-Connecting-IP') || '?', agora = Date.now();
    const lista = (usos.get(ip) || []).filter((t) => agora - t < 60000);
    if (lista.length >= LIMITE_MIN) return resp(429, { erro: 'muitas leituras por minuto' }, h);
    lista.push(agora); usos.set(ip, lista);

    // o coletor grava a cada ~10 s: guarda 4 s para não martelar o Drive
    if (cache && agora - cacheEm < 4000) return resp(200, cache, h);
    try {
      const t = await tokenGoogle(env);
      const r = await fetch('https://www.googleapis.com/drive/v3/files/' + encodeURIComponent(env.DRIVE_FILE_ID) + '?alt=media', { headers: { Authorization: 'Bearer ' + t } });
      if (!r.ok) return resp(502, { erro: 'Drive respondeu ' + r.status }, h);
      const j = await r.json();
      delete j.sentencas_no_intervalo; delete j.fonte; delete j._aviso; // só o que o app usa (sem IP interno da rede de bordo)
      cache = JSON.stringify(j); cacheEm = Date.now();
      return resp(200, cache, h);
    } catch (e) {
      return resp(502, { erro: 'falha ao ler o Drive' }, h); // o app segue com o snapshot local
    }
  }
};
