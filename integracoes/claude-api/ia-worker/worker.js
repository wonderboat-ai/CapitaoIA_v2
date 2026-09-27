/* Capitão IA — proxy da IA na nuvem (Claude API) · Cloudflare Worker `capitao-ia`.
   ESTRUTURA — DESLIGADA. Nenhuma tela chama este proxy. Nada foi publicado.
   Mesmo padrão dos outros proxies do projeto: o site é público, então a chave da API NUNCA vai para o repositório nem
   para o navegador — fica só aqui, como segredo.

   Recebe POST { pergunta, trechos?, contexto? } do site e devolve { texto, modelo, parou }.
     pergunta   texto do usuário (até 500 letras — o limite do campo do chat)
     trechos    até 3 trechos da base de bordo já achados no aparelho (CapitaoBrain.buscaBase): [{ fonte, pag, secao, texto }]
     contexto   leitura que a tela já mostra (snapshot ou telemetria ao vivo), em texto curto
   A IA só responde com o que vier aqui. Sem fonte → "SEM DADOS" (regra do projeto).

   Segredos/variáveis (Cloudflare › Workers › capitao-ia › Settings › Variables):
     ANTHROPIC_API_KEY  (segredo)  chave da Claude API
     CHAVE_APP          (segredo)  chave longa e aleatória que o app manda no cabeçalho X-Capitao-Chave
     MODELO             (variável) padrão claude-opus-5
     ESFORCO            (opcional) low | medium | high | xhigh | max — ajuste depois de medir custo e qualidade
     ORIGENS            (opcional) sites autorizados, separados por vírgula
   Proteções: só as ORIGENS, só com a CHAVE_APP, no máximo 30 perguntas por minuto por IP.
   Defina também um limite de gasto no Console da Anthropic. */
import Anthropic from '@anthropic-ai/sdk';

const PADRAO_ORIGENS = 'https://wonderboat-ai.github.io';
const LIMITE_PERGUNTA = 500, LIMITE_TRECHO = 1200, MAX_TRECHOS = 3, LIMITE_CONTEXTO = 2000, LIMITE_MIN = 30;
const ESFORCOS = ['low', 'medium', 'high', 'xhigh', 'max'];
const usos = new Map(); // por instância do Worker: freio simples contra abuso, não substitui o limite de gasto

// Regras do projeto (CLAUDE.md · "Como falar com o usuário"). Texto fixo, sem data nem nada variável: fica no cache de prompt.
const SISTEMA = [
  'Você é o Capitão IA, o cérebro operacional da embarcação Capitão IA. Esta embarcação é uma demonstração da plataforma: os dados dela são fictícios e vêm rotulados DEMO.',
  'Responda em português do Brasil, direto. A primeira linha é a resposta; detalhes depois, só se necessário. Nunca pergunte o óbvio.',
  'Emergência (SOS, homem ao mar, incêndio, pressão de óleo, EPIRB, entrada de água): ignore a concisão e dê o passo a passo completo.',
  'Use SOMENTE os trechos e a leitura enviados nesta mensagem. Nunca invente número, data, peça ou procedimento.',
  'Sem fonte para o que foi perguntado: responda "SEM DADOS" e diga onde buscar (guia no Drive, diário, equipe).',
  'Cite fabricante e modelo do equipamento (se o modelo não vier na fonte, escreva "modelo SEM DADOS") e termine com uma linha "Fonte: …" usando a fonte e a seção ou página do trecho usado.',
  'Estados honestos: SEM LEITURA (sensor não chega na rede), SEM DADOS (não há fonte), MANUAL NO DRIVE (passo a passo não confirmado), A CONFERIR / A CONFIRMAR (entrou por foto ou nota).',
  'Procedimento de emergência que vier como padrão internacional deve continuar rotulado "procedimento padrão — confirmar com o protocolo de bordo".',
  'Se as fontes divergirem, vale esta ordem: manual oficial › registro oficial › laudo › diário › foto › nota informal.',
  'Nunca escreva no diário: o registro só acontece com comando explícito no app ("registre no diário…").'
].join('\n');

function cors(origem) {
  return { 'Access-Control-Allow-Origin': origem, 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, X-Capitao-Chave', 'Access-Control-Max-Age': '86400', 'Vary': 'Origin' };
}
function resp(status, corpo, h) { return new Response(JSON.stringify(corpo), { status, headers: { ...h, 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' } }); }
function iguais(a, b) { a = String(a || ''); b = String(b || ''); if (a.length !== b.length) return false; let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0; }
function corta(s, n) { s = String(s || '').replace(/\s+/g, ' ').trim(); return s.length > n ? s.slice(0, n) : s; }

// Mensagem do usuário: trechos com a fonte, leitura atual e a pergunta por último (o que varia fica depois do system em cache).
function montaMensagem(pergunta, trechos, contexto) {
  const partes = [];
  trechos.forEach((t, i) => {
    const fonte = corta(t.fonte, 160) + (t.pag ? ', p. ' + t.pag : t.secao ? ' · ' + corta(t.secao, 120) : '');
    partes.push('<trecho n="' + (i + 1) + '" fonte="' + fonte.replace(/"/g, "'") + '">\n' + corta(t.texto, LIMITE_TRECHO) + '\n</trecho>');
  });
  if (contexto) partes.push('<leitura_atual>\n' + contexto + '\n</leitura_atual>');
  if (!partes.length) partes.push('<sem_fontes/>');
  partes.push('Pergunta: ' + pergunta);
  return partes.join('\n\n');
}

export default {
  async fetch(req, env) {
    const origens = String(env.ORIGENS || PADRAO_ORIGENS).split(',').map((s) => s.trim()).filter(Boolean);
    const origem = req.headers.get('Origin') || '';
    if (!origens.includes(origem)) return resp(403, { erro: 'origem não autorizada' }, {});
    const h = cors(origem);
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: h });
    if (req.method !== 'POST') return resp(405, { erro: 'use POST' }, h);
    if (!env.CHAVE_APP || !iguais(req.headers.get('X-Capitao-Chave'), env.CHAVE_APP)) return resp(401, { erro: 'chave inválida' }, h);
    if (!env.ANTHROPIC_API_KEY) return resp(500, { erro: 'falta ANTHROPIC_API_KEY' }, h);

    const ip = req.headers.get('CF-Connecting-IP') || '?', agora = Date.now();
    const lista = (usos.get(ip) || []).filter((t) => agora - t < 60000);
    if (lista.length >= LIMITE_MIN) return resp(429, { erro: 'muitas perguntas por minuto' }, h);
    lista.push(agora); usos.set(ip, lista);

    let corpo;
    try { corpo = await req.json(); } catch (e) { return resp(400, { erro: 'JSON inválido' }, h); }
    const pergunta = corta(corpo && corpo.pergunta, LIMITE_PERGUNTA);
    if (!pergunta) return resp(400, { erro: 'pergunta vazia' }, h);
    const trechos = Array.isArray(corpo.trechos) ? corpo.trechos.filter((t) => t && typeof t.texto === 'string').slice(0, MAX_TRECHOS) : [];
    const contexto = corta(corpo.contexto, LIMITE_CONTEXTO);

    const client = new Anthropic({ apiKey: env.ANTHROPIC_API_KEY });
    const pedido = {
      model: env.MODELO || 'claude-opus-5',
      max_tokens: 16000,
      thinking: { type: 'adaptive' },
      // Recusa por política: a própria API refaz a pergunta no modelo reserva recomendado para a categoria da recusa.
      betas: ['server-side-fallback-2026-07-01'],
      fallbacks: 'default',
      // Regras fixas primeiro, com cache (abaixo do mínimo do modelo o cache é ignorado, sem erro).
      system: [{ type: 'text', text: SISTEMA, cache_control: { type: 'ephemeral' } }],
      messages: [{ role: 'user', content: montaMensagem(pergunta, trechos, contexto) }]
    };
    if (ESFORCOS.includes(env.ESFORCO)) pedido.output_config = { effort: env.ESFORCO };
    let r;
    try {
      r = await client.beta.messages.create(pedido);
    } catch (e) {
      // qualquer erro: o site mantém a resposta local (base de bordo / SEM DADOS)
      if (e instanceof Anthropic.AuthenticationError) return resp(500, { erro: 'chave da Claude API recusada' }, h);
      if (e instanceof Anthropic.RateLimitError) return resp(429, { erro: 'limite da Claude API — tente de novo' }, h);
      if (e instanceof Anthropic.APIConnectionError) return resp(502, { erro: 'sem conexão com a Claude API' }, h);
      if (e instanceof Anthropic.APIError) return resp(502, { erro: 'Claude API respondeu ' + e.status }, h);
      return resp(502, { erro: 'falha ao consultar a IA' }, h);
    }
    // stop_reason 'refusal' no fim = toda a cadeia (modelo + reserva) recusou: o app fica com a resposta local.
    if (r.stop_reason === 'refusal') return resp(422, { erro: 'pergunta recusada pela IA', categoria: (r.stop_details && r.stop_details.category) || null }, h);
    const texto = (r.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('').trim();
    if (!texto) return resp(502, { erro: 'resposta vazia' }, h);
    return resp(200, { texto, modelo: r.model, parou: r.stop_reason }, h);
  }
};
