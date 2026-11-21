/* Capitão IA — API única de alertas (CONTRATO-DADOS §1.16 e §1.24; PROMPT Fase 2, F05).
   window.CapitaoAlertas: a lista dos alertas abertos no instante, igual para a faixa do topo, a lista da Ponte, a C3, a E1, a E2 e o chat.
   Só a API, sem tela: nada aqui desenha, fala, grava no diário, abre o SOS ou a C3 nem troca de tela. Quem desenha (Fases 3 e 4) lê daqui.
   Não depende do capitao-brain.js. Fonte: CapitaoReplay.alarmes() (id, nivel, sistema, lado?, campo, valor, limite, desde — o nível já vem da
   CapitaoAgora.nivel sobre D.replay.limites; este arquivo NÃO avalia limite nenhum) + o catálogo D.replay.alertas (um id por campo: título, guia,
   seção, passos e fonte). Com o cenário 'aviso' nada crítico existe; no 'alarme-critico' o mesmo id vai aviso → crítico → aviso.

   API (todas devolvem valor seguro e nunca lançam erro; `ms` é opcional e vale o instante do replay: o fixado por fixar() ou agora):
     ativo()          true se a API anda: D.simulacao === true (lido a CADA chamada), CapitaoReplay presente e ativo, fora de /SOS-/
     ativos(ms?)      [alerta] do instante, o mais grave primeiro (crítico antes de aviso) e, no mesmo nível, o mais antigo primeiro; [] se inerte ou sem alarme
     porId(id, ms?)   o alerta ativo com esse id, ou null (id fora do catálogo, 'constructor' e afins incluídos, ou alerta que não está ativo)
     tocando(ms?)     o primeiro de ativos() — o que a faixa mostra — ou null; serve também como booleano
     contagem(ms?)    { total, aviso, critico, maior: 'critico' | 'aviso' | null }
     anunciado(id)    true se o id já foi anunciado nesta sessão
     anunciar(id)     marca o id como anunciado e devolve true SÓ na 1ª vez da sessão (false se já estava, se o id não existe ou se a API está inerte):
                      quem anuncia (a faixa da Fase 4) chama quando vai mostrar o alerta de verdade; os demais leitores só leem
     novos(ms?)       os ativos() ainda não anunciados
     NIVEL            { aviso: {peso, rotulo, cor, rgb}, critico: {…} }: rótulo e tokens de cor do tema (--cap-warn, --cap-crit) por nível
   Cada alerta: { id, nivel, rotulo, cor, rgb, sistema, lado? (só quando se aplica), campo, titulo, valor, limite, un, valorTxt, limiteTxt, texto,
                  desde (ISO), desdeMs, hora ('HH:MM:SS' de desde), seg (segundos desde o início), guia, secao, fonte, passos[], detalhe }.
   Quem quiser reagir assina o evento do replay, 'capitao-alerta' ({fase: 'inicio' | 'nivel' | 'fim', alarme}); o 1º tique da página sai antes de
   qualquer ouvinte, então a tela lê ativos() ao montar e depois acompanha os eventos. Não há evento próprio: o replay basta.

   Anunciado: sessionStorage 'capitao.alertas.anunciados' = {<id>: true}, sempre em try/catch; se o navegador negar o sessionStorage, vale a memória
   desta página (a faixa anuncia 1× por id por carga em vez de por sessão). Nunca esquece um id: o AVISO volta a cada volta e não se anuncia de novo.
   Travas: em /SOS-/ o arquivo sai sem definir nada (S1/S2 nem o carregam); com D.simulacao !== true tudo é inerte. */
(function () {
  var EM_SOS = false;
  try { EM_SOS = /SOS-/.test(location.pathname); } catch (e) {}
  if (EM_SOS || window.CapitaoAlertas) return;

  var CHAVE = 'capitao.alertas.anunciados';
  var memoria = Object.create(null);   // só quando o sessionStorage nega; com ele funcionando, fica vazia (sem protótipo: um id '__proto__' é chave comum)
  var NIVEL = {
    aviso: { peso: 1, rotulo: 'AVISO', cor: 'var(--cap-warn, #f0a63a)', rgb: 'var(--cap-warn-rgb, 240,166,58)' },
    critico: { peso: 2, rotulo: 'CRÍTICO', cor: 'var(--cap-crit, #ff3b30)', rgb: 'var(--cap-crit-rgb, 255,59,48)' }
  };
  try { Object.freeze(NIVEL.aviso); Object.freeze(NIVEL.critico); Object.freeze(NIVEL); } catch (e) {}

  function D() { return window.CapitaoDados || null; }
  function dono(o, k) { return !!o && typeof o === 'object' && Object.prototype.hasOwnProperty.call(o, k); }
  function num(x) { return typeof x === 'number' && isFinite(x); }
  function replay() { var R = window.CapitaoReplay; return R && typeof R.alarmes === 'function' && typeof R.ativo === 'function' && typeof R.agora === 'function' ? R : null; }

  function ativo() {
    try {
      var d = D(), R = replay();
      return !!(d && d.simulacao === true && d.replay && R && R.ativo());
    } catch (e) { return false; }
  }

  // ——— texto ———
  function decimais(x) { var s = String(x), i = s.indexOf('.'); return i < 0 ? 0 : Math.min(s.length - i - 1, 3); }
  function numTxt(campo, x, casas) {   // o número como a tela mostra (CapitaoAgora.fmt); sem ele, o número cru
    try {
      var A = window.CapitaoAgora, c = D().campos && D().campos[campo], t = A && A.fmt && A.fmt.nb(x, casas, !!(c && c.mil));
      if (typeof t === 'string' && t !== '') return t;
    } catch (e) {}
    return String(x);
  }
  function horaTxt(ms) {
    try { var A = window.CapitaoAgora, t = A && A.fmt && A.fmt.hora(ms, true); if (typeof t === 'string' && t !== '') return t; } catch (e) {}
    return '';
  }

  // um alarme do replay + o catálogo → o alerta da API (cópia: quem recebe pode mexer sem mexer no D)
  function monta(al, ms) {
    var d = D(), cat = d.replay.alertas, e = dono(cat, al.id) ? cat[al.id] : null, c = (d.campos && d.campos[al.campo]) || null, n = NIVEL[al.nivel];
    var titulo = (e && e.titulo) || (c && c.rotulo) || al.id, un = (c && c.un) || '', casas = c && num(c.casas) ? c.casas : 0;
    var a = { id: al.id, nivel: al.nivel, rotulo: n.rotulo, cor: n.cor, rgb: n.rgb }, desdeMs = typeof al.desde === 'string' ? Date.parse(al.desde) : NaN, vt = '', lt = '';
    if (al.sistema || (e && e.sistema)) a.sistema = al.sistema || e.sistema;
    if (al.lado || (e && e.lado)) a.lado = al.lado || e.lado;
    a.campo = al.campo; a.titulo = titulo;
    a.valor = al.valor; a.limite = al.limite; a.un = un;
    if (num(al.valor)) vt = numTxt(al.campo, al.valor, casas) + (un ? ' ' + un : '');
    if (num(al.limite)) lt = numTxt(al.campo, al.limite, decimais(al.limite)) + (un ? ' ' + un : '');
    a.valorTxt = vt; a.limiteTxt = lt;
    a.texto = titulo + (vt ? ': ' + vt + (lt ? ' (' + (al.valor > al.limite ? 'acima' : 'abaixo') + ' de ' + lt + ')' : '') : '');
    a.desde = typeof al.desde === 'string' ? al.desde : '';
    a.desdeMs = isFinite(desdeMs) ? desdeMs : null;
    a.hora = a.desdeMs === null ? '' : horaTxt(a.desdeMs);
    a.seg = a.desdeMs === null ? 0 : Math.max(0, Math.floor((ms - a.desdeMs) / 1000));
    a.guia = (e && e.guia) || ''; a.secao = (e && e.secao) || ''; a.fonte = (e && e.fonte) || '';
    a.passos = e && Array.isArray(e.passos) ? e.passos.slice() : [];
    a.detalhe = 'C3-Leme-Alerta.dc.html#alarme=' + encodeURIComponent(al.id);
    return a;
  }
  function antes(x, y) {   // crítico antes de aviso; no mesmo nível, o mais antigo; por fim o id (ordem estável)
    var dx = x.desdeMs === null ? Infinity : x.desdeMs, dy = y.desdeMs === null ? Infinity : y.desdeMs;
    return NIVEL[y.nivel].peso - NIVEL[x.nivel].peso || (dx < dy ? -1 : dx > dy ? 1 : 0) || (x.id < y.id ? -1 : x.id > y.id ? 1 : 0);
  }

  function ativos(ms) {
    try {
      if (!ativo()) return [];
      var R = replay(), t = num(ms) ? ms : R.agora(), lista = R.alarmes(t), por = Object.create(null), ids, i, al, a;   // o mesmo ms para a lista e para o `seg`
      if (!Array.isArray(lista)) return [];
      for (i = 0; i < lista.length; i++) {
        al = lista[i];
        if (!al || typeof al.id !== 'string' || al.id === '' || !dono(NIVEL, al.nivel)) continue;
        a = monta(al, t);
        if (!dono(por, al.id) || NIVEL[a.nivel].peso > NIVEL[por[al.id].nivel].peso) por[al.id] = a;   // um id por campo: se o replay repetir, fica o mais grave
      }
      ids = Object.keys(por);
      return ids.map(function (k) { return por[k]; }).sort(antes);
    } catch (e) { return []; }
  }
  function porId(id, ms) {
    try {
      if (typeof id !== 'string') return null;
      var l = ativos(ms), i;
      for (i = 0; i < l.length; i++) if (l[i].id === id) return l[i];
      return null;
    } catch (e) { return null; }
  }
  function tocando(ms) { try { return ativos(ms)[0] || null; } catch (e) { return null; } }
  function contagem(ms) {
    var o = { total: 0, aviso: 0, critico: 0, maior: null };
    try {
      var l = ativos(ms), i;
      for (i = 0; i < l.length; i++) { o.total++; o[l[i].nivel]++; }
      o.maior = o.critico ? 'critico' : o.aviso ? 'aviso' : null;
    } catch (e) {}
    return o;
  }

  // ——— anunciado (uma vez por id por sessão) ———
  function lido() {   // o mapa do sessionStorage, só com os valores true ({} se negar ou vier de outra forma); sem protótipo
    var raw, o, m = Object.create(null), k;
    try { raw = sessionStorage.getItem(CHAVE); o = raw ? JSON.parse(raw) : null; } catch (e) { o = null; }
    if (o && typeof o === 'object' && !Array.isArray(o)) for (k in o) if (dono(o, k) && o[k] === true) m[k] = true;
    return m;
  }
  function conhecido(id) {   // id do catálogo ou de um alerta ativo agora
    var d = D(), i, l;
    if (typeof id !== 'string' || id === '') return false;
    if (d && d.replay && dono(d.replay.alertas, id)) return true;
    l = ativos();
    for (i = 0; i < l.length; i++) if (l[i].id === id) return true;
    return false;
  }
  function anunciado(id) {
    try {
      if (!ativo() || typeof id !== 'string') return false;
      var o = lido();
      return o[id] === true || memoria[id] === true;
    } catch (e) { return false; }
  }
  function anunciar(id) {
    try {
      if (!ativo() || !conhecido(id) || anunciado(id)) return false;
      var o = lido();
      o[id] = true;
      try { sessionStorage.setItem(CHAVE, JSON.stringify(o)); } catch (e) { memoria[id] = true; }
      return true;
    } catch (e) { return false; }
  }
  function novos(ms) {
    try {
      return ativos(ms).filter(function (a) { return !anunciado(a.id); });
    } catch (e) { return []; }
  }

  window.CapitaoAlertas = { ativo: ativo, ativos: ativos, porId: porId, tocando: tocando, contagem: contagem, anunciado: anunciado, anunciar: anunciar, novos: novos, NIVEL: NIVEL };
})();
