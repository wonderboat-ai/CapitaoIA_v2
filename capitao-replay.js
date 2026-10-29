/* Capitão IA — motor da reprodução de navegação (CONTRATO-DADOS §1.24, §3.2, §1.22, §1.13; PROMPT Fase 2).
   Sem VERSAO própria: acompanha o capitao-dados.js, que traz o D.replay (quadros-chave a cada 5 s, ruído, faixas, janelas de alarme),
   o D.rota, o D.campos (catálogo do quadro) e o D.historico. A tabela de 150 s e as somas acumuladas se calculam UMA vez, na carga;
   depois, em(ms) é função pura do instante absoluto (laço + rota + contadores + alarmes) e O(1). Tudo o que o app mostra, fala e manda
   à IA lê o mesmo instante: o CapitaoAgora.instante() (rodape do capitao-dados.js) chama CapitaoTelemetria.atual() → CapitaoReplay.quadro().
   Paridade Python × JS: as contas são as de ferramentas/demo/confere.py (em, laco_valor, desvio_em), na mesma ordem e com as mesmas
   constantes (radianos = x·(π/180), como o CPython); testes/replay.py compara campo a campo.

   API (window.CapitaoReplay; global SEPARADO — nunca se registra como window.CapitaoTelemetria):
     DURACAO              150 (s da volta)
     ativo()              true se o replay anda: D.simulacao === true (lido a CADA chamada), fora de /SOS-/, com tabela montada
     agora()              o instante em ms: o fixado por fixar() ou Date.now()
     t(ms?)               segundo da volta (0…149) do instante (padrão: agora)
     em(ms)               quadro plano do instante absoluto (CONTRATO §1.22), com alarmes[]; null se inerte ou em falha
     quadro(t?)           sem argumento: em(agora()); com t: o segundo t (0…149) da volta do instante fixado (ou de agora)
     contadores(ms?)      {horímetros, diesel_litros, distancia_mn, tanques} do instante (padrão: agora)
     contadoresEm(ms)     o mesmo, para um instante qualquer (diferenças dão consumo e distância)
     alarmes(ms?)         alarmes[] do instante (id, nivel, sistema, lado?, campo, valor, limite, desde); nunca 'critico' fora do
                          cenario 'alarme-critico'
     janela(id, ms?)      {ativo, desde, ate} em ms da janela do alarme `id` desta volta ou da anterior (o "NORMALIZADO às HH:MM" da C3);
                          `ate` é null enquanto está ativo
     fase(ms?)            {nome, ini, fim} de D.replay.fases para o instante
     resumo(ms?)          uma linha (≤ 300 letras) do instante, SEM coordenadas e sem posição relativa
     serie(campo, janela, ms?)   pontos {ms, v, min, max} do mais antigo ao mais novo; janela ∈ chaves de D.historico.janelas; o último é o
                          quadro de agora; null para campo/janela que o histórico não cobre
     porFaixa(ms?)        consumo dos motores por faixa de rpm (D.consumo.faixas): por volta e desde a âncora do instante
     fixar(x)             x = segundos (60), '60' ou '60@K' (K voltas desde a âncora; padrão D.replay.voltas_fixo): congela o instante
                          absoluto = âncora + K·150 s + x s (fixar(60) = 12:01:00); fixar(null) solta
     fixo()               o ms fixado ou null

   Congelamento (testes e capturas), tudo em try/catch: localStorage 'capitao.replay.fixo' ('60' | '60@120'), ou #replay=<x> no endereço
   (só vale nesta carga, não vai para o localStorage; #replay=sair solta). 'capitao.replay.sobre' (JSON parcial mesclado ao quadro) só vale
   com o instante fixado, no próprio instante fixado: é o gancho de teste da troca NAVEGANDO → FUNDEADO da E1.

   Eventos (window): 'capitao-telemetria' a cada 1 s, alinhado ao segundo, pausado com document.hidden e com tique imediato na volta à frente
   (detail = o quadro, com simulado: true); 'capitao-alerta' {fase: 'inicio' | 'nivel' | 'fim', alarme}; 'capitao-rebase' {ms} na virada das
   07:00 ou da meia-noite (também na página que carregou oculta e só depois voltou à frente) e em fixar(). O 1º tique de cada página sai já na
   carga, antes de qualquer ouvinte: quem ouve lê o estado ao montar (alarmes(), quadro()) e depois acompanha os eventos. O replay só emite
   evento: NUNCA abre SOS/C3, troca de tela, fala nem grava.

   Travas: em /SOS-/ o arquivo sai sem definir nada; com D.simulacao !== true tudo é inerte (null, nenhum evento, nenhum timer); nunca lança
   erro (falhou → null, e quem chama cai no D.snapshot); nunca lê, devolve nem muta o D.snapshot; um timer só por página. */
(function () {
  var EM_SOS = false;
  try { EM_SOS = /SOS-/.test(location.pathname); } catch (e) {}
  if (EM_SOS || window.CapitaoReplay) return;

  var DURACAO = 150, MS_DIA = 86400000, CHAVE_FIXO = 'capitao.replay.fixo', CHAVE_SOBRE = 'capitao.replay.sobre';
  var DESEQUILIBRIO_DIESEL_L = 3;   // os dois tanques de diesel diferem de 3 L (confere.DESEQUILIBRIO_DIESEL_L)
  var RAD = Math.PI / 180, GRAUS = 180 / Math.PI;   // as constantes do CPython: x·(π/180) e x·(180/π), não x·π/180

  // ——— utilidades ———
  function D() { return window.CapitaoDados || null; }
  function Ag() { var A = window.CapitaoAgora; return A && typeof A.ancora === 'function' && typeof A.nivel === 'function' ? A : null; }
  function num(x) { return typeof x === 'number' && isFinite(x); }
  function pmod(x, m) { var r = x % m; return r !== 0 && (r < 0) !== (m < 0) ? r + m : r; }   // o % do Python (sinal do divisor)
  function arred(x, c) { var p = Math.pow(10, c || 0), v = Math.floor(x * p + 0.5) / p; return v === 0 ? 0 : v; }   // como a tela mostra, sem -0
  function iso(ms) { return new Date(ms).toISOString().replace(/\.\d{3}Z$/, 'Z'); }
  function copia(o) { var c = {}, k; for (k in o) if (Object.prototype.hasOwnProperty.call(o, k)) c[k] = o[k]; return c; }
  function ls(f) { try { return f(); } catch (e) { return null; } }
  function emite(nome, detail) { try { window.dispatchEvent(new CustomEvent(nome, { detail: detail })); } catch (e) {} }

  // ruído por hash, periódico em t (§3.2): h32 e u(s, t) idênticos aos de confere.py
  function h32(x) {
    x = (x ^ 0x9E3779B9) >>> 0;
    x = (x ^ (x >>> 16)) >>> 0; x = Math.imul(x, 0x85EBCA6B) >>> 0;
    x = (x ^ (x >>> 13)) >>> 0; x = Math.imul(x, 0xC2B2AE35) >>> 0;
    return (x ^ (x >>> 16)) >>> 0;
  }
  function ruido(semente, t) { return h32(semente * 1000003 + t) / 4294967295 * 2 - 1; }
  function casasDe(C, c) { var d = C[c]; return d && typeof d.casas === 'number' ? d.casas : 0; }
  function wrap(x) { return pmod(x + 540, 360) - 180; }

  // ——— a tabela de 150 s (uma vez) ———
  // Valor do campo c no segundo t (0…149) da volta: interpolação das chaves (o segmento 145 → 150 usa o t = 0), ruído e arredondamento;
  // ângulo pelo arco menor e em [0, 360).
  function laco(R, C, c, t) {
    var ch = R.chaves[c], passo = R.passo_chave || 5, k = Math.floor(t / passo), f = (t - passo * k) / passo, n = ch.length;
    var a = ch[k % n], b = ch[(k + 1) % n], ang = !!(C[c] && C[c].ang), x, r = R.ruido && R.ruido[c];
    x = a + (ang ? (pmod(b - a + 540, 360) - 180) * f : (b - a) * f);
    if (r && r[0]) x = x + r[0] * ruido(r[1], t);
    x = arred(x, casasDe(C, c));
    if (ang) x = pmod(pmod(x, 360) + 360, 360);
    return x === 0 ? 0 : x;
  }

  var P = null, falhou = null;   // tabela montada e a referência do D.replay que falhou (para não remontar à toa)
  function monta(d) {
    var R = d.replay, rota = d.rota, C = d.campos, cons = d.consumo || {}, n = R.duracao, ch = Object.keys(R.chaves || {}), fx = R.fixos || {};
    var Q = [], cumD = [0], cumM = [0], ger = cons.gerador_lph || 0, t, i, q, k, pernas, arcos = [], g, nos, pontos = {}, alertaDe = {}, tq, ids;
    if (n !== DURACAO || !rota || !rota.pernas || !rota.pernas.length || !C || !R.contadores_base || !R.por_volta || !R.taxas_h) return null;
    for (t = 0; t < n; t++) {
      q = {};
      for (i = 0; i < ch.length; i++) q[ch[i]] = laco(R, C, ch[i], t);
      for (k in fx) if (Object.prototype.hasOwnProperty.call(fx, k)) q[k] = fx[k];
      Q.push(q);
      cumD.push(cumD[t] + (q.consumo_lph + ger) / 3600);
      cumM.push(cumM[t] + q.sog_nos / 3600);
    }
    pernas = rota.pernas;
    g = rota.guinada_max_gps || 3; nos = (cons.cruzeiro && cons.cruzeiro.nos) || 18;
    for (i = 0; i < pernas.length; i++) {   // arco de guinada em volta de cada ponto: [início da perna, Δrumo, comprimento do arco em mn, rumo anterior]
      var dd = wrap(pernas[i].rumo - pernas[(i + pernas.length - 1) % pernas.length].rumo);
      arcos.push([pernas[i].ini_mn, dd, Math.abs(dd) / g * nos / 3600, pernas[(i + pernas.length - 1) % pernas.length].rumo]);
    }
    pontos[rota.base.id] = rota.base;
    (rota.pontos || []).forEach(function (p) { pontos[p.id] = p; });
    ids = Object.keys(R.alertas || {});
    for (i = 0; i < ids.length; i++) alertaDe[R.alertas[ids[i]].campo] = ids[i];
    tq = (d.embarcacao && d.embarcacao.tanques) || {};
    return { R: R, rota: rota, C: C, consumo: d.consumo, n: n, Q: Q, cumD: cumD, cumM: cumM, tot: rota.distancia_mn, ida: rota.ida_mn, pontos: pontos,
             pernas: pernas, arcos: arcos, alertaDe: alertaDe, tanqueL: (tq.diesel_l || 0) / (tq.diesel_n || 2), ordem: Object.keys(C),
             grupos: gruposJanela(R), stats: {}, faixas: null };
  }
  // janelas de alarme por id, juntando as contíguas (aviso → crítico → aviso do cenário 'alarme-critico' é um alarme só)
  function gruposJanela(R) {
    var por = {}, js = (R.janelas || []).slice().sort(function (a, b) { return a.ini - b.ini || a.fim - b.fim; });
    js.forEach(function (j) {
      var l = por[j.id] || (por[j.id] = []), u = l[l.length - 1];
      if (u && j.ini <= u.fim + 1) u.fim = Math.max(u.fim, j.fim); else l.push({ ini: j.ini, fim: j.fim });
    });
    return por;
  }
  // a tabela vale enquanto o D.replay, a rota e o catálogo forem os mesmos objetos; o D.simulacao é lido a cada chamada
  function tabela() {
    var d = null;
    try {
      d = D();
      if (!d || d.simulacao !== true || !d.replay || !d.rota || !d.campos || !Ag()) return null;
      if (P && P.R === d.replay && P.rota === d.rota && P.C === d.campos && P.consumo === d.consumo) return P;
      if (falhou === d.replay) return null;
      P = monta(d);
      if (!P) falhou = d.replay;
      return P;
    } catch (e) { P = null; try { falhou = d && d.replay; } catch (x) {} return null; }   // dado quebrado: não remonta a cada chamada
  }

  // ——— rota ———
  // (COG em graus, graus por mn) na posição s do circuito (0 ≤ s < circuito): a perna, ou o arco de guinada em volta do ponto
  function cogEm(p, s) {
    var tot = p.tot, i, j, a, bases, pernas = p.pernas;
    for (i = 0; i < p.arcos.length; i++) {
      a = p.arcos[i];
      if (a[2] <= 0) continue;
      bases = [a[0], a[0] + tot, a[0] - tot];
      for (j = 0; j < 3; j++) if (Math.abs(s - bases[j]) < a[2] / 2) return [pmod(a[3] + a[1] * ((s - bases[j]) + a[2] / 2) / a[2], 360), a[1] / a[2]];
    }
    for (i = 0; i < pernas.length; i++) if (pernas[i].ini_mn <= s && s < pernas[i].ini_mn + pernas[i].mn) return [pernas[i].rumo, 0];
    return [pernas[pernas.length - 1].rumo, 0];
  }

  // ——— contadores (valor = base + voltas · por_volta + soma parcial da tabela; horímetros e tanques pelo relógio) ———
  function contSeg(p, seg) {
    var R = p.R, cb = R.contadores_base, pv = R.por_volta, tx = R.taxas_h, t = seg % p.n, v = Math.floor(seg / p.n), h = seg / 3600, k;
    var diesel = Math.max(cb.diesel_litros - (v * pv.diesel_l + p.cumD[t]), R.diesel_piso_l || 0);   // o piso (regra de 25 %) corta a segurança
    var dist = cb.distancia_mn + v * pv.distancia_mn + p.cumM[t], bruto = { diesel_litros: diesel, distancia_mn: dist }, val = {};
    bruto.motor_bb_horimetro_h = cb.motor_bb_horimetro_h + h;
    bruto.motor_be_horimetro_h = cb.motor_be_horimetro_h + h;
    bruto.gerador_horimetro_h = cb.gerador_horimetro_h + h;
    for (k in tx) if (Object.prototype.hasOwnProperty.call(tx, k)) bruto[k] = cb[k] + tx[k] * h;
    for (k in bruto) val[k] = arred(bruto[k], casasDe(p.C, k));
    return { bruto: bruto, val: val };
  }

  // ——— o quadro de um segundo do dia de bordo (port de confere.em) ———
  function calc(p, seg, anc, comAlarmes) {
    var R = p.R, rota = p.rota, C = p.C, n = p.n, t = seg % n, q0 = p.Q[t], o = copia(q0), k, c;
    var cs = contSeg(p, seg), diesel = cs.bruto.diesel_litros, dist = cs.bruto.distancia_mn;
    var cas = function (nome) { return casasDe(C, nome); };
    for (k in cs.val) o[k] = cs.val[k];
    o.diesel_bb_pct = arred((diesel / 2 + DESEQUILIBRIO_DIESEL_L) / p.tanqueL * 100, cas('diesel_bb_pct'));
    o.diesel_be_pct = arred((diesel / 2 - DESEQUILIBRIO_DIESEL_L) / p.tanqueL * 100, cas('diesel_be_pct'));
    // rota: posição, perna e rumo
    var tot = p.tot, ida = p.ida, s = dist * rota.fator, sm = pmod(s, tot), pernas = p.pernas, i = pernas.length - 1;
    for (k = 0; k < pernas.length; k++) if (sm < pernas[k].ini_mn + pernas[k].mn) { i = k; break; }
    var pe = pernas[i], x = Math.min(Math.max(sm - pe.ini_mn, 0), pe.mn), a = p.pontos[pe.de], b = p.pontos[pe.para], f = x / pe.mn;
    o.lat = arred(a.lat + (b.lat - a.lat) * f, cas('lat'));
    o.lon = arred(a.lon + (b.lon - a.lon) * f, cas('lon'));
    var cg = cogEm(p, sm), cog = cg[0], gpm = cg[1], sog = q0.sog_nos, cor = rota.corrente;
    var stw = sog - cor.nos * Math.cos((cog - cor.para_graus) * RAD);
    var delta = Math.asin(cor.nos * Math.sin((cor.para_graus - cog) * RAD) / stw) * GRAUS;
    var rp = (R.ruido && R.ruido.proa_graus) || [0, 0], rf = (R.ruido && R.ruido.profundidade_m) || [0, 0];
    var proa = pmod(cog - delta + rp[0] * ruido(rp[1], seg), 360);
    o.cog_graus = pmod(arred(cog, cas('cog_graus')), 360);
    o.proa_graus = pmod(arred(proa, cas('proa_graus')), 360);
    o.piloto_rumo = pmod(arred(pe.rumo, cas('piloto_rumo')), 360);
    o.stw_nos = arred(stw, cas('stw_nos'));
    o.leme_graus = arred(Math.max(-25, Math.min(25, 5 * (gpm * sog / 3600))) + q0.leme_graus, cas('leme_graus'));
    o.profundidade_m = arred(a.prof_m + (b.prof_m - a.prof_m) * f + rf[0] * ruido(rf[1], seg), cas('profundidade_m'));
    // vento aparente: soma vetorial do vento verdadeiro com o movimento do barco; ângulo relativo à proa, + a boreste
    var tws = q0.vento_verdadeiro_nos, twd = q0.vento_verdadeiro_angulo;
    var ax = tws * Math.sin((twd + 180) * RAD) - sog * Math.sin(cog * RAD), ay = tws * Math.cos((twd + 180) * RAD) - sog * Math.cos(cog * RAD);
    o.vento_aparente_nos = arred(Math.sqrt(ax * ax + ay * ay), cas('vento_aparente_nos'));
    o.vento_aparente_angulo = arred(wrap(pmod(Math.atan2(ax, ay) * GRAUS + 180, 360) - proa), cas('vento_aparente_angulo'));
    // destino, distância, próximo ponto e ETA (posição LINEARIZADA: o HH:MM é constante em cada perna do circuito)
    var vel = R.velocidade_media_nos, slin = seg * vel / 3600, nc = Math.floor(slin / tot + 1e-12), vai = (slin - nc * tot) < ida;
    var sdest = nc * tot + (vai ? ida : tot);
    o.destino = vai ? rota.destino.nome : rota.volta.nome;
    o.destino_mn = arred(Math.max(0, sdest - s), cas('destino_mn'));
    o.wp_proximo = b.nome;
    o.wp_mn = arred(Math.max(0, pe.mn - x), cas('wp_mn'));
    var ah = String(R.ancora_hora || '07:00'), iniMin = parseInt(ah.slice(0, 2), 10) * 60 + parseInt(ah.slice(3), 10);
    var etaMin = Math.floor(sdest / (vel / 3600) / 60 + 0.5), tm = iniMin + etaMin;
    o.eta = ('0' + (Math.floor(tm / 60) % 24)).slice(-2) + ':' + ('0' + (tm % 60)).slice(-2);
    var perto = x < pe.mn - x ? a : b;
    o.local = perto.perto + (perto.id === (vai ? rota.destino.id : rota.base.id) ? ', chegando' : ', ' + (vai ? rota.destino.caminho : rota.volta.caminho));
    o.timestamp_utc = iso(anc + seg * 1000);
    // na ordem do catálogo; o que sobrar vem depois
    var res = {};
    for (k = 0; k < p.ordem.length; k++) if (p.ordem[k] in o) res[p.ordem[k]] = o[p.ordem[k]];
    for (c in o) if (!(c in res)) res[c] = o[c];
    return res;
  }

  // alarmes: a CapitaoAgora.nivel sobre D.replay.limites no valor mostrado; o `desde` vem da janela do gerador desta volta
  function alarmesDe(p, res, t, v, anc) {
    var A = Ag(), lim = p.R.limites || {}, alertas = p.R.alertas || {}, js = p.R.janelas || [], out = [], campo, nv, aid, al, ale, j, k, critico = p.R.cenario === 'alarme-critico';
    for (campo in lim) {
      if (!Object.prototype.hasOwnProperty.call(lim, campo)) continue;
      nv = A.nivel(campo, res);
      if (!nv || nv.nivel === 'normal') continue;
      if (nv.nivel === 'critico' && !critico) nv = rebaixa(lim[campo], nv, res[campo]);   // o replay só avisa (decisão c)
      aid = p.alertaDe[campo] !== undefined ? p.alertaDe[campo] : campo;
      ale = alertas[aid] || {};
      al = { id: aid, nivel: nv.nivel };
      if (ale.sistema) al.sistema = ale.sistema;
      if (ale.lado) al.lado = ale.lado;
      j = null;
      for (k = 0; k < js.length; k++) if (js[k].id === aid && js[k].nivel === nv.nivel && js[k].ini <= t && t <= js[k].fim) { j = js[k]; break; }
      al.campo = campo; al.valor = res[campo]; al.limite = nv.limite;
      al.desde = iso(anc + (v * p.n + (j ? j.ini : t)) * 1000);
      out.push(al);
    }
    return out;
  }
  function rebaixa(L, nv, v) {   // crítico fora do cenário 'alarme-critico': vira AVISO, com o limite do aviso quando houver
    var R = L && (L.regimes ? L.regimes[nv.regime] : L), a = R && R.aviso, lim = nv.limite;
    if (a) { if (a.abaixo !== undefined && v < a.abaixo) lim = a.abaixo; else if (a.acima !== undefined && v > a.acima) lim = a.acima; }
    return { nivel: 'aviso', limite: lim };
  }

  // ——— relógio e congelamento ———
  var fixoMs = null, iniciado = false;
  function agoraMs() { return fixoMs !== null && ativo() ? fixoMs : Date.now(); }
  function ancoraDe(ms) { var a = Ag(), r = a ? a.ancora(ms) : NaN; return num(r) ? r : null; }
  function segDe(ms) {   // segundo do dia de bordo (0…86.399) e a âncora desse dia
    var anc = ancoraDe(ms);
    if (anc === null) return null;
    var seg = Math.floor((ms - anc) / 1000);
    return seg >= 0 ? { seg: seg, anc: anc } : null;
  }
  function msDe(ms) { return ms === undefined || ms === null ? agoraMs() : (num(ms) ? ms : null); }
  function especificacao(x) {   // 60 | '60' | '60@K' → {s, k, texto}; só instantes dentro de um ano (o resto é engano, não instante)
    var d = D(), k = d && d.replay && num(d.replay.voltas_fixo) ? d.replay.voltas_fixo : 120, m, s, e;
    if (typeof x === 'number') { if (!isFinite(x)) return null; e = { s: Math.floor(x), k: k, texto: String(x) }; }
    else if (typeof x === 'string') {
      m = /^\s*(-?\d+(?:\.\d+)?)\s*(?:@\s*(\d+))?\s*$/.exec(x);
      if (!m) return null;
      s = Math.floor(+m[1]);
      e = { s: s, k: m[2] !== undefined ? +m[2] : k, texto: x.replace(/\s+/g, '') };
    } else return null;
    return Math.abs(e.s) <= 366 * 86400 && e.k >= 0 && e.k <= 366 * 86400 / DURACAO ? e : null;
  }
  function aplicaFixo(x, persistir) {   // fixa o instante absoluto = âncora de hoje + K voltas + x s; o rodapé refaz os prazos para esse dia
    var e = especificacao(x), anc = e ? ancoraDe(Date.now()) : null, T, A = Ag();
    if (!e || anc === null) return null;
    T = anc + (e.k * DURACAO + e.s) * 1000;
    fixoMs = T;
    if (persistir) ls(function () { localStorage.setItem(CHAVE_FIXO, e.texto); });
    ls(function () { A.rebase(T, true); });
    emite('capitao-rebase', { ms: T });
    return T;
  }
  function solta() {
    fixoMs = null;
    ls(function () { localStorage.removeItem(CHAVE_FIXO); });
    ls(function () { Ag().rebase(Date.now(), true); });
    emite('capitao-rebase', { ms: Date.now() });
  }
  function sobre() {   // JSON parcial do 'capitao.replay.sobre' (objeto simples); só chamado com o instante fixado
    var raw = ls(function () { return localStorage.getItem(CHAVE_SOBRE); }), j;
    if (!raw) return null;
    j = ls(function () { return JSON.parse(raw); });
    return j && typeof j === 'object' && !Array.isArray(j) ? j : null;
  }

  // ——— API ———
  function ativo() { try { return !!tabela(); } catch (e) { return false; } }

  // o quadro do instante `ms` (sem arredondar o instante: o segundo inteiro manda); null se inerte ou em falha
  function quadroEm(ms, comAlarmes) {
    var p = tabela(), s, res, so, k;
    if (!p || !num(ms)) return null;
    s = segDe(ms);
    if (!s) return null;
    res = calc(p, s.seg, s.anc, comAlarmes);
    if (fixoMs !== null && Math.floor(ms / 1000) === Math.floor(fixoMs / 1000) && (so = sobre())) for (k in so) if (Object.prototype.hasOwnProperty.call(so, k) && k !== '__proto__' && k !== 'alarmes') res[k] = so[k];
    if (comAlarmes) {
      res.alarmes = alarmesDe(p, res, s.seg % p.n, Math.floor(s.seg / p.n), s.anc);
      if (so && Array.isArray(so.alarmes)) res.alarmes = soAviso(p, so.alarmes);   // a lista literal do 'sobre' (vazia vale: suprime o alarme) passa pela mesma trava
    }
    return res;
  }
  // o gancho 'sobre' não fura a decisão (c): fora do cenário 'alarme-critico' todo alarme dele é AVISO, qualquer que seja o `nivel` escrito; só objetos entram
  function soAviso(p, lista) {
    var out = [], i, a;
    for (i = 0; i < lista.length; i++) {
      if (!lista[i] || typeof lista[i] !== 'object') continue;
      a = copia(lista[i]);
      if (p.R.cenario !== 'alarme-critico') a.nivel = 'aviso';
      out.push(a);
    }
    return out;
  }
  function em(ms) { try { return quadroEm(ms, true); } catch (e) { return null; } }
  function quadro(t) {
    try {
      var ms = agoraMs(), s, p = tabela();
      if (t === undefined || t === null) return quadroEm(ms, true);
      if (!p || !num(t)) return null;
      s = segDe(ms);
      return s ? quadroEm(s.anc + (Math.floor(s.seg / p.n) * p.n + Math.floor(t)) * 1000, true) : null;
    } catch (e) { return null; }
  }
  function tFase(ms) {
    try {
      var p = tabela(), s;
      ms = msDe(ms);
      if (!p || ms === null) return null;
      s = segDe(ms);
      return s ? s.seg % p.n : null;
    } catch (e) { return null; }
  }
  function contadoresEm(ms) {
    try {
      var p = tabela(), s;
      if (!p || !num(ms)) return null;
      s = segDe(ms);
      return s ? contSeg(p, s.seg).val : null;
    } catch (e) { return null; }
  }
  function contadores(ms) { ms = msDe(ms); return ms === null ? null : contadoresEm(ms); }
  function alarmes(ms) {
    try { ms = msDe(ms); var q = ms === null ? null : quadroEm(ms, true); return q ? q.alarmes : null; } catch (e) { return null; }
  }
  function janela(id, ms) {
    try {
      var p = tabela(), s, G, t, base, k, g;
      ms = msDe(ms);
      if (!p || ms === null) return null;
      G = Object.prototype.hasOwnProperty.call(p.grupos, id) ? p.grupos[id] : null;
      s = segDe(ms);
      if (!G || !G.length || !s) return null;
      t = s.seg % p.n; base = s.anc + Math.floor(s.seg / p.n) * p.n * 1000;
      for (k = G.length - 1; k >= 0; k--) {   // a última janela que já começou nesta volta…
        g = G[k];
        if (g.ini <= t) { var ativa = t <= g.fim; return { ativo: ativa, desde: base + g.ini * 1000, ate: ativa ? null : base + (g.fim + 1) * 1000 }; }
      }
      g = G[G.length - 1]; base -= p.n * 1000;   // …ou, se nenhuma começou, a da volta anterior
      return { ativo: false, desde: base + g.ini * 1000, ate: base + (g.fim + 1) * 1000 };
    } catch (e) { return null; }
  }
  function fase(ms) {
    try {
      var t = tFase(ms), fs = D().replay.fases || [], i;
      if (t === null) return null;
      for (i = 0; i < fs.length; i++) if (fs[i].ini <= t && t < fs[i].fim) return { nome: fs[i].nome, ini: fs[i].ini, fim: fs[i].fim };
      return null;
    } catch (e) { return null; }
  }

  // uma linha do instante, sem coordenadas nem posição relativa (o cérebro monta a posição à parte, quando a regra deixa)
  function resumo(ms) {
    try {
      var A = Ag(), p = tabela(), q, f, partes = [], c, ale, i, al, un;
      ms = msDe(ms);
      if (!p || ms === null) return null;
      q = quadroEm(ms, true); f = fase(ms);
      if (!q) return null;
      c = function (nome) { return A.fmt.campo(q, nome); };
      partes.push(A.fmt.hora(ms, true) + ' · ' + (q.estado || 'Navegando') + (f ? ', ' + f.nome : ''));
      if (c('sog_nos')) partes.push('SOG ' + c('sog_nos') + ' nós');
      if (c('motor_bb_rpm') && c('motor_be_rpm')) partes.push('rpm BB ' + c('motor_bb_rpm') + ' / BE ' + c('motor_be_rpm'));
      if (c('motor_bb_oleo_bar') && c('motor_be_oleo_bar')) partes.push('óleo ' + c('motor_bb_oleo_bar') + ' / ' + c('motor_be_oleo_bar') + ' bar');
      if (c('motor_bb_arref_c') && c('motor_be_arref_c')) partes.push('arrefecimento ' + c('motor_bb_arref_c') + ' / ' + c('motor_be_arref_c') + ' °C');
      if (c('diesel_litros')) partes.push('diesel ' + c('diesel_litros') + ' L');
      ale = p.R.alertas || {};
      for (i = 0; i < (q.alarmes || []).length; i++) {
        al = q.alarmes[i]; un = p.C[al.campo] && p.C[al.campo].un;
        partes.push((al.nivel === 'critico' ? 'ALERTA' : 'AVISO') + ': ' + ((ale[al.id] && ale[al.id].titulo) || al.id) + ' em ' + c(al.campo) + (un ? ' ' + un : '') + ' (limite ' + A.fmt.nb(al.limite, al.limite === Math.floor(al.limite) ? 0 : casasDe(p.C, al.campo), false) + (un ? ' ' + un : '') + ')');
      }
      return partes.join(' · ').slice(0, 300);
    } catch (e) { return null; }
  }

  // consumo dos motores por faixa de rpm (D.consumo.faixas): a média dos dois motores a cada segundo da tabela de 150 s. Por volta e desde a âncora
  // do instante (voltas inteiras + parte da volta atual), pelas mesmas somas dos contadores; o gerador entra à parte (consumo.gerador_lph)
  function porFaixa(ms) {
    try {
      var p = tabela(), fs = p && p.consumo && p.consumo.faixas, s, t, v, i, k, q, r, ger = (p && p.consumo && p.consumo.gerador_lph) || 0;
      ms = msDe(ms);
      if (!p || !fs || ms === null) return null;
      s = segDe(ms);
      if (!s) return null;
      if (!p.faixas) {
        p.faixas = fs.map(function () { return { seg: 0, cumS: [0], cumL: [0] }; });
        for (t = 0; t < p.n; t++) {
          q = p.Q[t]; r = (q.motor_bb_rpm + q.motor_be_rpm) / 2; k = -1;
          for (i = 0; i < fs.length; i++) if (fs[i].rpm_de <= r && (r < fs[i].rpm_ate || (i === fs.length - 1 && r <= fs[i].rpm_ate))) { k = i; break; }
          for (i = 0; i < fs.length; i++) {
            var dentro = i === k;
            p.faixas[i].cumS.push(p.faixas[i].cumS[t] + (dentro ? 1 : 0));
            p.faixas[i].cumL.push(p.faixas[i].cumL[t] + (dentro ? q.consumo_lph / 3600 : 0));
          }
        }
        for (i = 0; i < fs.length; i++) p.faixas[i].seg = p.faixas[i].cumS[p.n];
      }
      t = s.seg % p.n; v = Math.floor(s.seg / p.n);
      return fs.map(function (f, j) {
        var F = p.faixas[j], segs = v * F.seg + F.cumS[t], litros = v * F.cumL[p.n] + F.cumL[t];
        return { nome: f.nome, rpm_de: f.rpm_de, rpm_ate: f.rpm_ate, seg: F.seg, pct: arred(F.seg / p.n * 100, 1),
                 lph: F.seg ? arred(F.cumL[p.n] / (F.seg / 3600), 1) : 0, litros_volta: arred(F.cumL[p.n], 3),
                 horas: arred(segs / 3600, 2), litros: arred(litros, 1), gerador_litros: arred(ger * segs / 3600, 1) };
      });
    } catch (e) { return null; }
  }

  // ——— histórico: séries por janela (CONTRATO §1.13) ———
  function grupoDe(H, campo) {
    var m = H.metricas || {}, g;
    for (g in m) if (Object.prototype.hasOwnProperty.call(m, g) && m[g].indexOf(campo) >= 0) return g;
    return null;
  }
  // desvio do campo, em unidades reais, a `dias` dias da âncora de hoje (port de confere.desvio_em): linear entre os pontos de passo_dias em
  // passo_dias dias (d[0] a n·passo dias atrás … d[n−1] a passo dias atrás) e 0 na âncora
  function desvio(H, campo, dias) {
    var s = H.desvios && H.desvios[campo], d, n, passo, pos, i, a, b;
    if (!s || dias <= 0) return 0;
    d = s.d; n = H.n; passo = H.passo_dias;
    pos = n - dias / passo;
    if (pos <= 0) return d[0] / s.escala;
    i = Math.floor(pos);
    a = i < n ? d[i] : 0; b = i + 1 < n ? d[i + 1] : 0;
    return (a + (b - a) * (pos - i)) / s.escala;
  }
  // curva do ano (em relação à média): tabela por dia do calendário (1º de janeiro = índice 0), interpolada linearmente e fechando o ano
  function sazonal(H, campo, ms) {
    var z = H.sazonal, s = z && z[campo], A = Ag(), dt, doy, pos, i, n, f;
    if (!s || !A) return 0;
    dt = new Date(ms + A.off(ms) * 60000);
    doy = Math.floor((Date.UTC(dt.getUTCFullYear(), dt.getUTCMonth(), dt.getUTCDate()) - Date.UTC(dt.getUTCFullYear(), 0, 1)) / MS_DIA);
    n = s.d.length; pos = doy / (z.passo_dias || 5); i = Math.floor(pos); f = pos - i;
    return (s.d[i % n] + (s.d[(i + 1) % n] - s.d[i % n]) * f) / s.escala;
  }
  function estatLaco(p, campo) {   // mín/média/máx do campo na volta de 150 s (calculado uma vez por campo)
    var e = p.stats[campo], t, x, soma = 0, mn = Infinity, mx = -Infinity;
    if (e) return e;
    for (t = 0; t < p.n; t++) { x = p.Q[t][campo]; soma += x; if (x < mn) mn = x; if (x > mx) mx = x; }
    return (p.stats[campo] = { min: mn, mean: soma / p.n, max: mx });
  }
  function limitesClima() {   // máx/mín de hoje da leitura salva do clima, pela mesma CapitaoAgora.trava (nada de cópia da regra)
    var A = Ag(), lo = A.trava({ temp_ar_externo_c: -1e9 }).temp_ar_externo_c, hi = A.trava({ temp_ar_externo_c: 1e9 }).temp_ar_externo_c;
    return lo > -1e9 && hi < 1e9 ? { min: lo, max: hi } : null;
  }
  function serie(campo, janelaId, ms) {
    try {
      var p = tabela(), d = D(), H, J, agoraS, pts = [], i, j, m, q, v, cl, ehTemp, cont, anc, passo, S, fim, ini, dias, mid, grupo, dev, mn, mx, base, nowQ, ar, st, c0, c1, ca;
      ms = msDe(ms);
      if (!p || ms === null || !d.historico) return null;
      H = d.historico; J = H.janelas && H.janelas[janelaId];
      if (!J || !p.C[campo] || !num(J.n) || !num(J.passo_s)) return null;
      agoraS = Math.floor(ms / 1000) * 1000;
      ehTemp = campo === 'temp_ar_externo_c' || campo === 'temp_agua_c';
      cl = ehTemp ? limitesClima() : null;
      if (janelaId === '150S') {   // um ponto por segundo: o quadro de cada instante (o ar e a água presos na máx/mín de hoje, como o instante())
        for (i = 0; i < J.n; i++) {
          m = agoraS - (J.n - 1 - i) * J.passo_s * 1000;
          q = quadroEm(m, false);
          if (!q || !num(q[campo])) return null;
          v = cl ? Math.min(cl.max, Math.max(cl.min, q[campo])) : q[campo];
          pts.push({ ms: m, v: v, min: v, max: v });
        }
        return pts;
      }
      // janelas longas: só os grupos de métrica que não são "só do laço" (nas longas a volta se repete e a linha sairia reta)
      grupo = grupoDe(H, campo);
      if (!grupo || (H.so150 || []).indexOf(grupo) >= 0) return null;
      anc = ancoraDe(agoraS); passo = J.passo_s * 1000;
      nowQ = quadroEm(agoraS, false);
      if (anc === null || !nowQ || !num(nowQ[campo])) return null;
      S = anc + Math.floor((agoraS - anc) / passo) * passo;   // início do balde que contém agora (os baldes são alinhados à âncora)
      cont = p.C[campo].origem === 'contador';
      ar = campo === 'temp_praca_maquinas_c' ? 'temp_ar_externo_c' : campo;   // a praça acompanha o ar externo (desvio e curva do ano)
      ca = casasDe(p.C, campo);
      for (i = 0; i < J.n; i++) {
        j = J.n - 1 - i;   // baldes para trás; o balde 0 contém agora e termina no quadro atual
        fim = j === 0 ? agoraS : S - (j - 1) * passo; ini = S - j * passo;
        mid = j === 0 ? agoraS : (ini + fim) / 2;
        dias = (anc - mid) / MS_DIA;
        if (cont) {   // diesel e tanques: o contador no começo e no fim do balde (o fim é o último segundo dentro dele)
          c0 = contadoresEm(ini)[campo]; c1 = j === 0 ? nowQ[campo] : contadoresEm(fim - 1000)[campo];
          v = c1; mn = Math.min(c0, c1); mx = Math.max(c0, c1);
        } else if (ehTemp) {   // ar e água: o quadro de hoje (preso na máx/mín do dia) + a curva do ano + o desvio do dia
          base = cl ? Math.min(cl.max, Math.max(cl.min, nowQ[campo])) : nowQ[campo];
          v = arred(base + (sazonal(H, campo, mid) - sazonal(H, campo, agoraS)) + desvio(H, campo, dias), ca);
          mn = mx = v;
        } else {   // campo do laço: mín/média/máx da volta + o desvio do dia (a praça, o do ar e a curva do ano)
          dev = campo === 'temp_praca_maquinas_c' ? (sazonal(H, ar, mid) - sazonal(H, ar, agoraS)) + desvio(H, ar, dias) : desvio(H, campo, dias);
          st = estatLaco(p, campo);
          mn = arred(st.min + dev, ca); mx = arred(st.max + dev, ca);
          v = j === 0 ? nowQ[campo] : arred(st.mean + dev, ca);
          if (v < mn) mn = v;
          if (v > mx) mx = v;
        }
        pts.push({ ms: fim, v: v, min: mn, max: mx });
      }
      return pts;
    } catch (e) { return null; }
  }

  // ——— tique de 1 s, alertas e virada ———
  var meu = (window.__capitaoReplayGen = (window.__capitaoReplayGen || 0) + 1), timer = 0, vivos = null;
  function atual() { return window.__capitaoReplayGen === meu; }   // uma recarga do arquivo na mesma página deixa só o timer da cópia nova
  function agenda(ms) {
    clearTimeout(timer); clearTimeout(window.__capitaoReplayTimer);
    timer = window.__capitaoReplayTimer = setTimeout(tique, ms);
  }
  function alertasDiff(lista) {   // inicio / nivel / fim por id do alarme, contra o tique anterior
    var novo = {}, i, a, velho;
    for (i = 0; i < lista.length; i++) novo[lista[i].id] = lista[i];
    if (vivos) {
      for (a in novo) {
        if (!Object.prototype.hasOwnProperty.call(novo, a)) continue;
        if (!vivos[a]) emite('capitao-alerta', { fase: 'inicio', alarme: novo[a] });
        else if (vivos[a].nivel !== novo[a].nivel) emite('capitao-alerta', { fase: 'nivel', alarme: novo[a] });
      }
      for (velho in vivos) if (Object.prototype.hasOwnProperty.call(vivos, velho) && !novo[velho]) emite('capitao-alerta', { fase: 'fim', alarme: vivos[velho] });
    } else {   // 1º tique da página: o alarme que já está ativo conta como início (a faixa anuncia uma vez por id por sessão)
      for (a in novo) if (Object.prototype.hasOwnProperty.call(novo, a)) emite('capitao-alerta', { fase: 'inicio', alarme: novo[a] });
    }
    vivos = novo;
  }
  var emTique = false;
  function tique() {
    if (emTique) return;   // um ouvinte que chama fixar() de dentro do evento não reentra: o próximo tique (≤ 1 s) alcança
    emTique = true;
    try {
      if (!atual()) return;
      clearTimeout(timer);
      if (!ativo()) { timer = 0; iniciado = false; return; }   // inerte (D.simulacao mudou): para; o próximo uso da API religa
      if (!document.hidden) {
        var ms = agoraMs(), q = quadroEm(ms, true);
        if (q) {
          // virada das 07:00 ou da meia-noite: o rebase é idempotente e só devolve true quando o dia de bordo ou o dia mudou. Vale também para a
          // página que carregou oculta e só agora volta à frente (nenhum estado do tique anterior) e para o fixar(), que já refez o rodapé
          if (ls(function () { return Ag().rebase(ms); })) emite('capitao-rebase', { ms: ms });
          var detalhe = copia(q); detalhe.simulado = true;
          emite('capitao-telemetria', detalhe);
          alertasDiff(q.alarmes || []);
        }
      }
      agenda(1000 - (Date.now() % 1000) + 2);   // alinhado ao segundo
    } catch (e) { try { agenda(1000); } catch (x) {} }
    finally { emTique = false; }
  }
  function aoVoltar() {
    if (!atual()) { document.removeEventListener('visibilitychange', aoVoltar); return; }
    if (!document.hidden) { ls(inicia); tique(); }   // volta à frente: tique imediato
  }

  function inicia() {   // 1ª vez que o replay está ativo: lê o congelamento, monta o tique
    if (iniciado || !ativo()) return;
    iniciado = true;
    var h = null, s = null;
    try { h = /(?:^#|&)replay=([^&]*)/.exec(location.hash || ''); } catch (e) {}
    if (h) { ls(function () { s = decodeURIComponent(h[1]); }); if (/^(sair|solta|livre)$/i.test(s || '')) { solta(); s = null; } else if (s !== null) aplicaFixo(s, false); }
    else { s = ls(function () { return localStorage.getItem(CHAVE_FIXO); }); if (s) aplicaFixo(s, false); }
    tique();
  }

  function fixar(x) {
    try {
      if (!ativo()) return null;
      if (x === undefined) return fixoMs;
      if (x === null) { solta(); tique(); return null; }
      var T = aplicaFixo(x, true);
      if (T !== null) tique();
      return T;
    } catch (e) { return null; }
  }
  function fixo() { try { return ativo() ? fixoMs : null; } catch (e) { return null; } }

  // toda chamada da API religa o motor se ele ainda não começou (D.simulacao pode virar true depois da carga)
  function guarda(f) { return function () { try { if (!iniciado && ativo()) inicia(); } catch (e) {} return f.apply(null, arguments); }; }
  window.CapitaoReplay = {
    DURACAO: DURACAO,
    ativo: guarda(ativo), agora: guarda(agoraMs), t: guarda(tFase), em: guarda(em), quadro: guarda(quadro),
    contadores: guarda(contadores), contadoresEm: guarda(contadoresEm), alarmes: guarda(alarmes), janela: guarda(janela), fase: guarda(fase),
    resumo: guarda(resumo), serie: guarda(serie), porFaixa: guarda(porFaixa), fixar: guarda(fixar), fixo: fixo
  };
  try { document.addEventListener('visibilitychange', aoVoltar); } catch (e) {}
  try { if (ativo()) inicia(); } catch (e) {}
})();
