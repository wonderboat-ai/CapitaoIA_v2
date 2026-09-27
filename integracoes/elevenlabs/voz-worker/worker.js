/* Capitão IA — proxy da voz em nuvem (Cloudflare Worker `capitao-voz`) · OPCIONAL.
   ESTRUTURA — DESLIGADA. Hoje o app fala com a voz do próprio aparelho (Web Speech, grátis, offline). Nada publicado.
   O site é público: a chave do ElevenLabs NUNCA vai para o repositório nem para o navegador. Ela fica só aqui, como segredo.
   Recebe POST { texto } do site e devolve o áudio MP3.

   Segredos/variáveis (Cloudflare › Workers › capitao-voz › Settings › Variables):
     ELEVENLABS_API_KEY   (segredo)  chave da API do ElevenLabs
     CHAVE_APP            (segredo)  chave longa e aleatória que o app manda no cabeçalho X-Capitao-Chave
     ELEVENLABS_VOICE_ID  (variável) ID da voz escolhida (voz pt-BR da Voice Library ou voz clonada COM consentimento de quem grava)
     MODELO               (opcional) padrão eleven_multilingual_v2; eleven_flash_v2_5 responde mais rápido
     ORIGENS              (opcional) sites autorizados, separados por vírgula
   Proteções: só as ORIGENS, só com a CHAVE_APP, texto de até 1.200 letras e no máximo 30 falas por minuto por IP.
   Defina também um limite de gasto no ElevenLabs. */
const PADRAO_ORIGENS = 'https://wonderboat-ai.github.io';
const LIMITE_TEXTO = 1200, LIMITE_MIN = 30;
const usos = new Map(); // por instância do Worker: freio simples contra abuso, não substitui o limite de gasto

function cors(origem) {
  return { 'Access-Control-Allow-Origin': origem, 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, X-Capitao-Chave', 'Access-Control-Max-Age': '86400', 'Vary': 'Origin' };
}
function erro(status, msg, h) { return new Response(JSON.stringify({ erro: msg }), { status, headers: { ...h, 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' } }); }
function iguais(a, b) { a = String(a || ''); b = String(b || ''); if (a.length !== b.length) return false; let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0; }

export default {
  async fetch(req, env) {
    const origens = String(env.ORIGENS || PADRAO_ORIGENS).split(',').map((s) => s.trim()).filter(Boolean);
    const origem = req.headers.get('Origin') || '';
    if (!origens.includes(origem)) return erro(403, 'origem não autorizada', {});
    const h = cors(origem);
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: h });
    if (req.method !== 'POST') return erro(405, 'use POST', h);
    if (!env.CHAVE_APP || !iguais(req.headers.get('X-Capitao-Chave'), env.CHAVE_APP)) return erro(401, 'chave inválida', h);
    if (!env.ELEVENLABS_API_KEY || !env.ELEVENLABS_VOICE_ID) return erro(500, 'faltam ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID', h);

    const ip = req.headers.get('CF-Connecting-IP') || '?', agora = Date.now();
    const lista = (usos.get(ip) || []).filter((t) => agora - t < 60000);
    if (lista.length >= LIMITE_MIN) return erro(429, 'muitas falas por minuto', h);
    lista.push(agora); usos.set(ip, lista);

    let texto = '';
    try { texto = String((await req.json()).texto || '').trim(); } catch (e) { return erro(400, 'JSON inválido', h); }
    if (!texto) return erro(400, 'texto vazio', h);
    if (texto.length > LIMITE_TEXTO) texto = texto.slice(0, LIMITE_TEXTO);

    const modelo = env.MODELO || 'eleven_multilingual_v2';
    const corpo = { text: texto, model_id: modelo, voice_settings: { stability: 0.5, similarity_boost: 0.8, style: 0.2, use_speaker_boost: true, speed: 1.0 } };
    if (!/multilingual_v2/.test(modelo)) corpo.language_code = 'pt'; // o multilingual_v2 não aceita language_code
    let r;
    try {
      r = await fetch('https://api.elevenlabs.io/v1/text-to-speech/' + encodeURIComponent(env.ELEVENLABS_VOICE_ID) + '?output_format=mp3_44100_64', {
        method: 'POST',
        headers: { 'xi-api-key': env.ELEVENLABS_API_KEY, 'Content-Type': 'application/json', 'Accept': 'audio/mpeg' },
        body: JSON.stringify(corpo)
      });
    } catch (e) { return erro(502, 'sem conexão com o ElevenLabs', h); }
    if (!r.ok) return erro(502, 'ElevenLabs respondeu ' + r.status, h); // o site cai na voz do aparelho
    return new Response(r.body, { status: 200, headers: { ...h, 'Content-Type': 'audio/mpeg', 'Cache-Control': 'no-store' } });
  }
};
