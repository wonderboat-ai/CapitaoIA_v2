/* Capitão IA — cérebro: atalhos, diário, respostas canônicas, base de bordo e voz.
   Os dados vêm de capitao-dados.js (window.CapitaoDados) — hoje a embarcação de DEMONSTRAÇÃO, com dados fictícios
   rotulados e a fonte de cada um (Drive › Capitão IA v2). Nada inventado aqui: sem dado → SEM DADOS; sensor ausente →
   SEM LEITURA; manual não confirmado → MANUAL NO DRIVE; foto/nota → A CONFERIR / A CONFIRMAR.
   Pipeline: answer(q, ctx) → route(q) (emergência e óleo no topo) → ANSWERS[chave] { text, src, actions }
             → buscaBase(q) (BM25 com sinônimos PT/EN sobre base-conhecimento.json) → SEM DADOS.
   IA na nuvem (capitao-ia.js, ligada na demonstração): as telas de chat chamam a IA quando pedeIA(a, q) — SEM DADOS local,
   trecho do guia ou pergunta sobre o próprio app —, mandando a ficha(): o que o app sabe agora, cada bloco com a fonte.
   Emergência, óleo, registro no diário e respostas prontas ficam no aparelho. */
(function () {
  var VERSAO = '1.0.9'; // = VERSAO do capitao-auth.js e do capitao-ia.js (o capitao-app.js recarrega se vierem misturados)
  var norm = function (s) { return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); };
  var has = function (q, list) { return list.some(function (k) { return q.indexOf(k) !== -1; }); };
  var D = window.CapitaoDados || {};
  // No SOS (S1 e S2 carregam este cérebro para gravar no diário e ler os telefones do aparelho), o snapshot fica vazio: nada do dado
  // gerado da embarcação sai de lá (PROMPT §2.1; CONTRATO §1.3). Em /SOS-/ nada aqui lê o snapshot, o replay nem o MMSI gerado.
  var EM_SOS = false; try { EM_SOS = /SOS-/.test(location.pathname); } catch (e) {}
  var E = D.embarcacao || {}, S = EM_SOS ? {} : (D.snapshot || {}), AUT = D.autonomia || {}, CON = D.consumo || {};
  var DEMO = D.demo ? ' (DEMO)' : '';
  var DEMO_ = D.demo ? ' DEMO' : ''; // dentro de parênteses: "(snapshot DEMO 26/09 10:12)", sem parêntese aninhado
  var SD = 'SEM DADOS';

  var HREF = {
    web: { home: 'Main.dc.html', console: 'A1-Ponte-Web.dc.html', gestao: 'B1-Carta-Web.dc.html', manut: 'C1-Leme-Web.dc.html', docs: 'G1-Documentos-Web.dc.html', abast: 'G2-Abastecimento-Web.dc.html', diario: 'G3-Diario-Web.dc.html', equipe: 'G4-Equipe-Web.dc.html', faq: 'F1-FAQ-Hub-Web.dc.html', f2: 'F2-FAQ-Estabilizador-Web.dc.html', f3: 'F3-FAQ-Eletronicos-Web.dc.html', f4: 'F4-FAQ-Gerador-Web.dc.html', f5: 'F5-FAQ-Climatizacao-Web.dc.html', sos: 'S1-SOS-Web.dc.html', atalhos: 'H3-Atalhos-Editar-Web.dc.html' },
    app: { home: 'H2-Home-Mobile.dc.html', console: 'A2-Ponte-Mobile.dc.html', gestao: 'B2-Carta-Mobile.dc.html', manut: 'C2-Leme-Mobile.dc.html', docs: 'G1-Documentos-Mobile.dc.html', abast: 'G2-Abastecimento-Mobile.dc.html', diario: 'G3-Diario-Mobile.dc.html', equipe: 'G4-Equipe-Mobile.dc.html', faq: 'F1-FAQ-Hub.dc.html', f2: 'F2-FAQ-Estabilizador.dc.html', f3: 'F3-FAQ-Eletronicos.dc.html', f4: 'F4-FAQ-Gerador.dc.html', f5: 'F5-FAQ-Climatizacao.dc.html', sos: 'S2-SOS-Mobile.dc.html', atalhos: 'H3-Atalhos-Editar.dc.html' }
  };

  var DEFAULTS = [
    { id: 'diario', l: 'DIÁRIO DE BORDO', q: 'Registre no diário o resumo da navegação de agora e confirme.' },
    { id: 'seguro', l: 'SEGURO PARA SAIR?', q: 'Avalie vento, mar, motores e pendências — sim ou não, e por quê.' },
    { id: 'destinos', l: 'PARA ONDE VAMOS HOJE?', q: 'Destinos saindo daqui, com distância, tempo e diesel.' },
    { id: 'manutencao', l: 'PRÓXIMAS MANUTENÇÕES', q: 'O que vence primeiro, o que está atrasado, o que falta registrar.' },
    { id: 'autonomia', l: 'AUTONOMIA', q: 'Autonomia com reserva de 10% pelo diesel a bordo.' },
    { id: 'mare', l: 'MARÉ AGORA', q: 'Maré agora e nas próximas 6 h na posição de referência.' }
  ];
  var BANK = [
    { id: 'clima', l: 'CLIMA', q: 'Clima e vento agora e hoje na posição de referência.' },
    { id: 'canal16', l: 'CANAL 16', q: 'Roteiro de chamada no VHF canal 16 com os dados do barco.' },
    { id: 'checklist', l: 'CHECKLIST DE SAÍDA', q: 'Checklist de saída com o que está catalogado a bordo.' },
    { id: 'consumo', l: 'CONSUMO', q: 'Consumo de diesel observado por regime e desde o último abastecimento.' },
    { id: 'tanques', l: 'TANQUES', q: 'Nível de todos os tanques agora.' },
    { id: 'contatos', l: 'CONTATOS', q: 'Equipe, oficina, marina e prestadores — quem chamar.' },
    { id: 'anomalias', l: 'ANOMALIAS ABERTAS', q: 'Anomalias registradas e pendências abertas no diário.' },
    { id: 'porao', l: 'PORÃO', q: 'Situação das bombas de porão e do teste mensal.' },
    { id: 'gerador', l: 'GERADOR', q: 'Como ligar e desligar o gerador e quantas horas ele tem.' },
    { id: 'posicao', l: 'POSIÇÃO AGORA', q: 'Posição, proa e velocidade agora.' },
    { id: 'docsvenc', l: 'DOCUMENTOS VENCENDO', q: 'Quais documentos e licenças vencem primeiro.' },
    { id: 'horimetros', l: 'HORÍMETROS', q: 'Horas dos motores e do gerador e a próxima revisão.' }
  ];
  var ALL = DEFAULTS.concat(BANK);

  var K = { atalhos: 'capitao.atalhos.v1', diario: 'capitao.diario.v1', equipe: 'capitao.equipe.v1', exec: 'capitao.executado.v1', docs: 'capitao.docs.v1', abast: 'capitao.abast.v1' };
  function read(key, fallback) { try { var v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; } }
  function write(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {} }

  function cleanShortcut(x) { return x && typeof x.l === 'string' && typeof x.q === 'string' && x.l.trim() && x.q.trim() ? { id: String(x.id || ('custom-' + Math.random().toString(36).slice(2, 8))), l: x.l.trim().slice(0, 28), q: x.q.trim().slice(0, 240) } : null; }
  function loadShortcuts() {
    var v = read(K.atalhos, null);
    if (Array.isArray(v)) {
      var seen = {}; var list = v.map(cleanShortcut).filter(function (x) { if (!x || seen[x.id]) return false; seen[x.id] = 1; return true; }).slice(0, 8);
      if (list.length || !v.length) return list;
    }
    return DEFAULTS.map(function (x) { return Object.assign({}, x); });
  }
  function saveShortcuts(list) { write(K.atalhos, list); }
  function resetShortcuts() { try { localStorage.removeItem(K.atalhos); } catch (e) {} return loadShortcuts(); }
  function bankFor(list) { var ids = list.map(function (x) { return x.id; }); return ALL.filter(function (x) { return ids.indexOf(x.id) === -1; }); }

  // Usuário logado (capitao-auth.js): CapitaoAuth.nome() devolve quem entrou e manda ao login se a sessão expirou.
  function quem() { if (!window.CapitaoAuth) return 'Lucas'; try { return String(window.CapitaoAuth.nome()); } catch (e) { return 'sem sessão'; } }
  function now() { var d = new Date(); var p = function (n) { return (n < 10 ? '0' : '') + n; }; return { d: p(d.getDate()) + '/' + p(d.getMonth() + 1), t: p(d.getHours()) + ':' + p(d.getMinutes()), iso: d.toISOString() }; }
  // Diário: só cresce. Linhas do app (localStorage, mais nova primeiro) + linhas da fonte (Diário de bordo DEMO no Drive).
  function loadDiario() { var v = read(K.diario, []); return Array.isArray(v) ? v.filter(function (e) { return e && typeof e.t === 'string'; }) : []; }
  function addDiario(e) { var n = now(); var list = loadDiario(); var entry = Object.assign({ d: n.d, t: n.t, iso: n.iso, sys: 'Diário', tone: 'var(--cap-accent, #00a1fe)', who: quem(), src: 'app · texto' }, e); list.unshift(entry); write(K.diario, list); return entry; }
  function diarioFonte() { return (D.diario || []).map(function (x) { return { d: x.d, h: x.h, t: x.t, iso: x.iso, sys: x.sys, tom: x.tom, who: x.who, pend: !!x.pend, src: (D.diarioFonte || 'diário') }; }); }
  function loadExec() { var v = read(K.exec, {}); return v && typeof v === 'object' && !Array.isArray(v) ? v : {}; }
  function markExec(task) { var m = loadExec(); m[task] = now(); write(K.exec, m); return m; }
  // Desfaz um Executado: relê a lista, tira só essa tarefa e grava (sem a tarefa ou com dado ruim, não grava nada)
  function unmarkExec(task) { var m = loadExec(); if (task != null && Object.prototype.hasOwnProperty.call(m, String(task))) { delete m[String(task)]; write(K.exec, m); } return m; }
  function loadEquipe() { var v = read(K.equipe, null); var o = v && typeof v === 'object' ? v : {}; return { fones: o.fones && typeof o.fones === 'object' && !Array.isArray(o.fones) ? o.fones : {}, convites: Array.isArray(o.convites) ? o.convites.filter(function (c) { return c && typeof c.nome === 'string'; }) : [] }; }
  function saveEquipe(v) { write(K.equipe, v); }
  function loadDocs() { var v = read(K.docs, []); return Array.isArray(v) ? v.filter(function (d) { return d && typeof d.n === 'string'; }) : []; }
  function addDoc(d) { var list = loadDocs(); list.unshift(d); write(K.docs, list); return list; }
  function loadAbast() { var v = read(K.abast, []); return Array.isArray(v) ? v.filter(function (a) { return a && typeof a.n === 'string'; }) : []; }
  function addAbast(a) { var list = loadAbast(); list.unshift(a); write(K.abast, list); return list; }

  // ——— números e textos a partir dos dados ———
  function nb(x, d) { return typeof x === 'number' && isFinite(x) ? x.toFixed(d == null ? 1 : d).replace('.', ',') : '—'; }
  function mil(x) { return typeof x === 'number' ? String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g, '.') : '—'; }
  function grau3(x) { return typeof x === 'number' ? ('00' + Math.round(((x % 360) + 360) % 360)).slice(-3) + '°' : '—'; }
  function horas(x) { if (typeof x !== 'number' || !isFinite(x)) return '—'; var s = x.toFixed(1).split('.'); return mil(+s[0]) + ',' + s[1]; }
  var M = S.motores || {}, G = S.gerador || {}, DI = S.diesel || {}, T = S.tanques || {};
  var SNAP = {
    quando: S.quando || SD, hora: S.hora || '', dia: S.dia || '',
    pos: S.gps && S.gps.texto ? S.gps.texto : 'posição SEM LEITURA',
    local: (S.estado || SD) + ' · ' + (S.local || SD),
    diesel: DI.bb != null ? 'BB ' + nb(DI.bb) + ' % · BE ' + nb(DI.be) + ' % (≈ ' + mil(DI.litros) + ' L de ' + mil(DI.capacidade) + ')' : SD,
    dieselHora: (DI.nota || 'última leitura') + ' · ' + (DI.hora || SD),
    motores: M.rpm ? 'motores ' + (M.estado || 'desligados') + ' — última leitura com motores ligados ' + M.hora + ' (marcha lenta, ' + (M.marcha || 'neutro') + '): ' + M.rpm.join('/') + ' rpm · óleo ' + M.oleo.map(function (x) { return nb(x); }).join('/') + ' bar · arrefecimento ' + M.arref.join('/') + ' °C' : 'motores: ' + SD,
    fonte: 'coletor NMEA' + DEMO + ' · snapshot ' + (S.quando || SD)
  };
  var FT = {
    tele: 'Fonte: ' + SNAP.fonte,
    agenda: 'Fonte: ' + (D.agendaFonte || 'agenda de manutenção'),
    docs: 'Fonte: ' + (D.docsFonte || 'controle de documentos'),
    abast: 'Fonte: ' + (D.abastFonte || 'registro de abastecimento'),
    diario: 'Fonte: ' + (D.diarioFonte || 'diário de bordo'),
    proto: 'Fonte: ' + ((D.protocolos && D.protocolos.fonte) || 'protocolo de emergência')
  };
  function guia(k) { return (D.guias && D.guias[k]) || SD; }
  function equip(id) { return (D.equipamentos || []).filter(function (e) { return e.id === id; })[0] || null; }
  // "Gerador Onan QD 9" — sempre fabricante e modelo, com o que faltar marcado; o fabricante não se repete quando o modelo já começa
  // por ele ("Estabilizador giroscópico Seakeeper 3", não "Seakeeper Seakeeper 3"), como o equip_de do gerador
  function fabMod(id) {
    var e = equip(id); if (!e) return SD;
    var f = e.fabricante, m = e.modelo;
    return e.nome + (f && m && m.toLowerCase().indexOf(f.toLowerCase()) === 0 ? '' : ' ' + (f || '(fabricante ' + SD + ')')) + (m ? ' ' + m : ' · modelo ' + SD);
  }
  function agenda() { return D.agenda || []; }
  function atrasadas() { return agenda().filter(function (t) { return t.dn < 0; }); }
  function tarefa(id) { return agenda().filter(function (t) { return t.id === id; })[0] || null; }
  function prazoTxt(t) { return t ? (t.dn < 0 ? 'em atraso há ' + (-t.dn) + (t.dn === -1 ? ' dia' : ' dias') : 'D-' + t.dn + ' · ' + t.vence.slice(0, 5)) : SD; }
  function min1(s) { s = String(s || ''); return s.charAt(0).toLowerCase() + s.slice(1); }
  function pendencias() { return diarioFonte().filter(function (x) { return x.pend; }); }

  // Frase normalizada com espaço nas pontas (palavra inteira = ' x ').
  function pad(s) { return ' ' + norm(s).replace(/[?!.,;:()"“”]+/g, ' ').replace(/\s+/g, ' ').trim() + ' '; }
  // Lista SOS: a de antes mais a ampliação da 1b (PROMPT §2.3; frases de queda de pessoa, perda de governo e água a bordo que a revisão do C5
  // mediu indo à IA, contra a trava "emergência local, nunca na IA"). UMA lista só com a SEGURANCA_PALAVRAS do gerador
  // (ferramentas/demo/confere.py): o testes/cerebro.py confere que as duas são iguais.
  var SOS = ['mayday', 'emergenc', 'incendio', ' fogo', 'homem ao mar', ' mob ', ' sos ', 'socorro', 'naufrag', 'caiu no mar', 'caiu ao mar', 'caiu na agua', 'pessoa na agua', 'alguem na agua', 'crianca na agua', 'afogad', 'afogand',
    'afund', 'entrando agua', 'agua entrando', 'entrada de agua', 'alagad', 'alagand', 'inundad', 'inundand', 'abandon', 'colisao', 'colidi', 'abalro', 'encalh', 'explos',
    'vazamento de combustivel', 'vazando combustivel', 'vazamento de diesel', 'vazando diesel', 'vazamento de gas', 'vazando gas', 'cheiro de combustivel', 'cheiro de diesel', 'cheiro de gas', 'cheiro de queimado',
    // 1b (PROMPT §2.3)
    'alagament', 'afogament', 'inundac', 'adernand', 'adernad', 'adernou', 'emborc', ' ferid', 'machuc', 'se feriu',
    'desmai', 'inconscien', 'infart', 'convuls', 'queimadura', 'choque eletric', 'agua no porao', 'porao cheio', 'porao enchendo',
    'bomba de porao nao para', 'barco virou', 'virou o barco', ' a deriva ', 'monoxido', 'alarme de gas',
    // 1b, revisão do C5: pessoa na água ou fora do barco, água entrando, perda de governo, eixo e mangueira (as frases ficam por inteiro:
    // ' entrou agua ' não pega "entrou aguardando"). A batida ("bateu em…") saiu da lista: ' bateu em ' pegava "bateu em 3 bar"; ver SOS_REGEX, abaixo.
    'caiu do barco', 'caiu da lancha', 'gente na agua', 'homem na agua', 'tripulante na agua', 'pulou do barco', 'de vista na agua',
    'perdi o leme', 'leme quebrou', 'eixo quebrou', 'quebrou o eixo',
    // 1b, §8.2 item 11 (o subconjunto sem "sem governo" e "água subindo", que pegariam "sem governo federal" e a temperatura da água)
    'alguem caiu', 'caiu alguem', 'crianca caiu', 'tripulante caiu', 'tripulante ao mar', 'crianca ao mar', 'alguem ao mar', 'alguem foi ao mar',
    'perdi o governo', 'perdemos o governo', 'estamos sem governo', 'leme travou',
    // 1b, revisão da revisão: as formas vizinhas que ainda iam à IA. Pessoa que cai (o presente, "pro mar", "para quem caiu"), água a bordo e perda de
    // governo ou eixo. "pro mar" sozinho não entra ("vamos pro mar"): só com o verbo, "caiu pro mar". "pessoa ao mar" fica de fora, como estava.
    ' cai na agua', ' cai no mar', ' cai ao mar', ' cai do barco', ' cai da lancha', 'caiu pro mar', 'caiu pra agua', 'caiu para o mar', 'caiu para a agua', ' para quem caiu', ' de quem caiu', ' ate quem caiu',
    'gente ao mar', 'passageiro ao mar', 'marinheiro ao mar', 'vitima ao mar', 'filho ao mar', 'filha ao mar',
    'agua subindo no porao', 'agua subiu no porao', 'porao subindo', 'bomba do porao nao para', 'bomba nao da conta', 'bombas nao dao conta',
    'bomba sem dar conta', 'bombas sem dar conta', 'porao nao da conta', 'porao sem dar conta',
    'perdemos o leme', 'leme nao responde', 'leme partiu', 'eixo partiu', 'partiu o eixo',
    // 1b, segunda revisão: as formas-espelho que ainda iam à IA. Governo e eixo («quebrou o leme», «leme quebrado»), casco furado, rachado ou aberto,
    // fundo tocado, mais de uma pessoa na água («caíram na água», «caímos do barco»), sangue e hemorragia (o sangramento técnico, «do ar», «do
    // combustível», fica na regex abaixo), fogo sem a palavra fogo (chamas, labaredas, faísca, curto-circuito, cheiro de plástico ou fio queimado)
    'quebrou o leme', 'quebramos o leme', 'quebrei o leme', 'partiu o leme', 'rompeu o leme', 'leme rompeu', 'leme quebrad', 'leme partid',
    'rompeu o eixo', 'furou o casco', 'furaram o casco', 'casco furou', 'casco furad', 'casco rachou', 'casco rachad', 'rachou o casco', 'casco trincou', 'trincou o casco',
    'tocou o fundo', 'tocamos o fundo', 'tocou no fundo', 'tocamos no fundo',
    'cairam na agua', 'cairam no mar', 'cairam ao mar', 'cairam do barco', 'cairam da lancha', 'caimos na agua', 'caimos no mar', 'caimos do barco', 'caimos da lancha',
    'hemorrag', 'labared', 'faisc', ' chamas ', 'curto circuito', 'curto-circuito', 'cheiro de queima', 'plastico derretid', 'fumeg', 'dor no peito',
    'sem leme', 'helice quebrou', 'quebrou a helice', 'perdemos a helice', 'perdi a helice', 'helice soltou', 'helice partiu'];
  // Frases com contexto, que a lista de palavras não alcança sem pegar o resto: "meu filho está na água", "o passageiro caiu", "alguém foi jogado ao
  // mar", "o barco está tomando água", "bateu numa pedra" (e não "bateu em 3 bar"), "ele está sangrando" (e não "sangrando o ar do sistema").
  // Segunda revisão da 1b: o que a regex alcança vem de LISTA POSITIVA (o que foi atingido: pedra, cais, outro barco, o casco, "nós"; quem está no
  // barco ou na água), nunca de "qualquer coisa menos unidade": «o consumo bateu num recorde», «a pressão bateu num valor alto» e «o dessalinizador
  // está fazendo água» são leitura e equipamento, não emergência. As frases fracas ("bateu forte", "em cheio", "em mim") só valem com o barco,
  // alguém ou ninguém de sujeito (BATE_INI); o casco, o banco e o fundo levam a guarda GUARDA_BATE: onda, vento, chuva, ponteiro, nível, pix ou valor de sujeito não é batida. O que a regex não alcança fica local por outro caminho ou vai ao guia: o
  // sangramento do ar e do combustível, a água do dessalinizador e do ar-condicionado, a água no tanque de água doce.
  // As fontes (`source`) são iguais às do gerador (confere.py: SOS_REGEX): o testes/cerebro.py confere. Sem lookbehind (Safari antigo).
  var PESSOA = '(?:alguem|gente|pessoas?|criancas?|tripulantes?|passageir[oa]s?|marinheiros?|homens?|mulher(?:es)?|vitimas?|filh[oa]s?|menin[oa]s?|cara|rapaz|moco|moca)';
  // parente, amigo e quem está a bordo pelo papel: «meu marido caiu na água», «o pai caiu», «perdi o meu amigo de vista». Sem «capitão» (é o nome do app)
  var PARENTE = '(?:idos[oa]s?|amig[oa]s?|colegas?|maes?|pai|marido|esposa|esposo|namorad[oa]s?|irma[o]?|irmaos|netos?|netas?|sobrinh[oa]s?|hospedes?|convidad[oa]s?|mergulhador(?:es)?|nadador(?:es)?|comandante|skipper|vizinh[oa]s?)';
  var DET = '(?:(?:um|uma|o|a|os|as|meu|minha|nosso|nossa|esse|essa) )*';
  var NO_MAR = '(?:no mar|na agua|pro mar|para o mar|pra agua)';
  var FORA = '(?:ao mar|no mar|na agua|pro mar|pra agua|para o mar|para fora|pela borda)';
  var CAIU = '(?:cai|caiu|cairam|caem|caindo|pulou|pularam|sumiu|sumiram|desapareceu|desapareceram)';
  var BARCOS = '(?:barco|lancha|embarcacao|iate|bote|veleiro|jet ski|jetski|navio|rebocador|traineira|catamara|escuna|canoa|caiaque|semirrigido)';
  var PARTES = '(?:casco|popa|proa|costado|quilha|helice|leme|bombordo|boreste)';
  var VERBO_BATIDA = '(?:bateu|batemos|bati|bateram|batendo|(?:acabamos|acabei|acabaram|acabou) de bater)';
  var BATE_ADV = '(?:(?:forte|feio|de lado|de frente|de proa|de popa|de raspao|de leve|em cheio|com forca) )*';
  var BATE_EM = '(?:em|n[oa]s?|nu(?:m|ma|ns|mas)) (?:(?:o|a|os|as|um|uma|outro|outra|outros|outras|nosso|nossa|nossos|nossas|meu|minha|esse|essa|aquele|aquela|mesmo|mesma) )*(?:[a-z]+ )?';
  var BATE_COM = '(?:com (?:(?:o|a|um|uma|nosso|nossa|meu|minha) )*(?:' + BARCOS + '|' + PARTES + ')(?: [a-z0-9]+){0,2} )?';
  var DURO_MAR = '(?:pedras?|rochas?|rochedos?|lajes?|baixios?|recifes?|corais?|troncos?|toras?|baleias?|destrocos|containers?)';
  var DURO = '(?:pedras?|rochas?|rochedos?|lajes?|baixios?|cais|troncos?|toras?|piers?|recifes?|costao|ilhas?|muros?|docas?|estacas?|boias?|areia|corais?|pontes?|containers?|objetos?|madeiras?|tocos?|baleias?|destrocos|naufragio)';
  var NAO_BARCO = '(?:ondas?|marolas?|banzeiros?|ressacas?|ventos?|rajadas?|chuvas?|mar|agua|espuma|respingos?|sol|luz|coracao|portas?|janelas?|escotilhas?|tampas?|toldo|bimini|relogio|sino|portao|previsao|palpite|aposta|calculo|estimativa|meta|resultado|nivel|tanques?|ponteiro|medidor|indicador|display|contador|consumo|pressao|temperatura|bateria|tensao|rotacao|horimetro|valor|saldo|pagamento|pix|transferencia|boleto|dinheiro|deposito|salario|conta|fatura|cartao|cheque|fornecedor)';
  var GUARDA_BATE = '^(?!.* ' + NAO_BARCO + ' (?:[a-z0-9]+ ){0,2}(?:bateu|bateram|batendo|batem|bate) ).* ';
  var BATE_FRACO = '(?:forte|feio|de lado|de frente|de proa|de popa|de raspao|de leve)';
  // as frases fracas («bateu forte», «bateu em cheio», «bateu em mim») só valem sem sujeito ou com o barco, alguém, «ele» ou «nós» («a gente») de sujeito:
  // «o motor bateu forte» (batendo pino), «o preço bateu em cheio» e «o vento bateu em mim» não são batida
  var BATE_INI = '^ (?:(?:ai|agora|la|acabou de|acabaram de|acho que|parece que|entao|olha|gente) )*(?:(?:(?:o|a|um|uma|nosso|nossa|outro|outra|esse|essa|aquele|aquela) )*(?:' + BARCOS + '|alguem|ele|ela|eles|elas|isso|nos)(?: [a-z0-9]+){0,5} )?';
  var SUJ_BARCO = '(?:barco|lancha|casco|embarcacao|iate|bote|veleiro|porao|estamos|nos)';
  var SEM_EQUIP_AGUA = '^(?!.*(?:dessalin|condicionad|climatiz))(?!.* (?:geladeira|frigobar|freezer|bebedouro|purificador|chuveiro|torneira|ducha|pia|ralo|sanitario|banheiro|lavabo|gelo) ).* ';
  var SEM_AGUA_DOCE = '^(?!.* (?:tanques? de agua|doce|potavel|olhos?|ouvidos?|nariz|boca|botas?|sapatos?|celular|telefone|geladeira|frigobar|freezer|pia|chuveiro|torneira|filtro|purificador|bebedouro|garrafa|copo|mala|mochila|bolsa) )(?!.*(?:dessalin|condicionad|climatiz)).* ';
  var SEM_MANGUEIRA_DE_USO = '^(?!.* (?:lavagem|lavar|chuveiro|ducha|pia|torneira|jardim|piscina|geladeira|frigobar|bebedouro) )(?!.*condicionad).* ';
  // sangramento técnico (o ar, o combustível, as linhas, o sistema…) não é ferimento: «sangrando o ar do sistema», «sangramento do combustível»
  var TECNICO = '(?:(?:o|a|os|as|um|uma|do|da|dos|das|no|na) )?(?:ar|combustivel|diesel|sistema|linhas?|bombas?|circuito|filtros?|racor|arrefecimento|freios?|radiador|tubulacao|injetor[a-z]*|bicos?|pre-?filtros?|respiro|aquecedor|turbo|embreagem|direcao|reversor|atuador|cilindro|tanques?|separador|decantador|motor|motores|gerador|hidraulic[a-z]*|oleo|cano|tubo|valvulas?|mangueiras?)';
  var ALVO_FOGO = '(?:motor|motores|painel|quadro|fio|fios|cabo|cabos|bateria|baterias|gerador|compressor|inversor|carregador|tomada|isolamento|resistencia)';
  var SOS_REGEX_FONTES = [
    ' ' + PESSOA + '(?: (?:esta|estao|ta|tao|foi|foram|ficou|ficaram))? ' + NO_MAR + ' ',
    ' (?:' + PESSOA + ' ' + CAIU + '|' + CAIU + ' ' + DET + PESSOA + '|(?:perdi|perdemos|perdeu|perderam) de vista ' + DET + PESSOA +
      '|(?:perdi|perdemos|perdeu|perderam) ' + DET + '(?:tripulantes?|marinheiros?|criancas?|filh[oa]s?|menin[oa]s?)) ',
    ' (?:' + PARENTE + ' ' + CAIU + ' (?:na agua|no mar|ao mar|do barco|da lancha|da embarcacao|pro mar|para o mar|pra agua|para fora|fora)|(?:perdi|perdemos|perdeu|perderam) de vista ' + DET + PARENTE +
      '|' + PARENTE + ' (?:esta|estao|ta|tao|foi|foram|ficou|ficaram) ' + NO_MAR + ') ',
    ' (?:derrubou|jogou|empurrou|arrastou|derrubaram|jogaram|empurraram) ' + DET + PESSOA + ' ' + FORA + ' ',
    ' ' + PESSOA + ' (?:foi|foram) (?:jogad[oa]s?|derrubad[oa]s?|arrastad[oa]s?|empurrad[oa]s?) ' + FORA + ' ',
    // água a bordo: o barco ou "nós" fazendo/tomando água (não a água doce, quente ou potável; não o dessalinizador nem o ar-condicionado)
    SEM_EQUIP_AGUA + SUJ_BARCO + '(?: [a-z0-9]+){0,3} (?:fazendo|faz|fez|fazer|tomando|toma|tomou|tomar|puxando|puxou|puxar) (?:muita |bastante |demais )?agua (?!(?:doce|potavel|quente|fria|gelada|mineral|filtrada|com|para|pro|pra)\\b)',
    SEM_EQUIP_AGUA + 'estou(?: [a-z0-9]+){0,2} (?:fazendo|fazer) (?:muita |bastante |demais )?agua (?!(?:doce|potavel|quente|fria|gelada|mineral|filtrada|com|para|pro|pra)\\b)',
    ' fazendo agua (?:no|na|pelo|pela|pelos|pelas|em) (?:porao|casco|fundo|quilha|popa|proa|costado|eixo|helice|leme|casa de maquinas|sala de maquinas|praca de maquinas|passa casco|passacasco|valvula|gaveta) ',
    SEM_AGUA_DOCE + '(?:entrou|comecou a entrar|comecando a entrar|voltou a entrar|comecaram a entrar) (?:muita |bastante |mais )?agua ',
    SEM_AGUA_DOCE + 'agua (?:entrou|comecou a entrar|comecou a subir) ',
    SEM_AGUA_DOCE + 'agua (?:esta |ta )?(?:subindo|subiu|sobe|enchendo|encheu) (?:rapido |rapidamente |muito )?(?:no|na|dentro d[oa]|em) (?:barco|lancha|embarcacao|cabine|salao|camarote|sala de maquinas|casa de maquinas|praca de maquinas) ',
    SEM_AGUA_DOCE + '(?:tem|ha|tinha|temos) agua dentro d[oa] (?:barco|lancha|embarcacao|casco|cabine|salao|camarote|sala de maquinas|casa de maquinas|praca de maquinas) ',
    // batida: o que foi atingido vem de lista positiva (coisa dura, outro barco, o casco, "nós")
    ' ' + VERBO_BATIDA + ' ' + BATE_ADV + BATE_COM + BATE_EM + DURO + ' ',
    ' (?:raspou|raspamos|raspei|esbarrou|esbarramos|esbarrei|tocou|tocamos|toquei) ' + BATE_ADV + BATE_COM + BATE_EM + DURO_MAR + ' ',
    GUARDA_BATE + VERBO_BATIDA + ' ' + BATE_ADV + BATE_COM + BATE_EM + '(?:' + BARCOS + '|' + PARTES + '|bancos?|fundo|algo|alguma coisa|alguem) ',
    BATE_INI + VERBO_BATIDA + '(?: ' + BATE_FRACO + ')* (?:em nos|em mim|na gente|em cheio) ',
    ' (?:batemos|bati)(?: (?:' + BATE_FRACO + '|em cheio))* $',
    BATE_INI + '(?:bateu|bateram)(?: ' + BATE_FRACO + ')+ $',
    ' (?:atingid|colhid|prensad)[oa]s? por (?:(?:um|uma|o|a|outro|outra) )*(?:' + BARCOS + '|raio) ',
    // ferimento: sangramento, sangrar, sangue (o técnico, "do ar" e "do combustível", não)
    ' sangramento (?!' + TECNICO + ' )',
    ' sangr(?:a|ando|ou|am|aram|ava|avam) (?!' + TECNICO + ' )',
    ' (?:parar de|para de|pare de|parou de|comecou a|continua a|continuou a|voltou a) sangrar ',
    ' sangrar (?:muito|sem parar|bastante|demais) ',
    '^(?!.* (?:tipo|exame|exames|doacao|doar|doador|teste|testes|pressao|laboratorio|azul) )(?!.* sangue frio ).* sangue ',
    // casco aberto («rombo no casco», «o casco está furado», «rachadura no casco») e pancada na cabeça
    ' rombo (?:no|na) (?:casco|barco|lancha|embarcacao|costado|proa|popa|fundo|quilha) ',
    ' casco (?:esta |ta |ficou |foi )?(?:furad[oa]|rachad[oa]|trincad[oa]|rompid[oa]|aberto|amassad[oa]|danificad[oa]) ',
    ' (?:rachadura|trinca|fissura|buraco|furo|rasgo) (?:no|na) (?:casco|costado|quilha|popa|proa) ',
    ' (?:bateu|bati|bateram|batemos) (?:com )?(?:a|na|no|o) (?:cabeca|nuca|testa) ',
    // fogo sem a palavra "fogo": chama, queimando o motor ou o painel, choque no painel
    ' (?:uma|vi|vimos|vejo|surgiu|apareceu|saindo|sai|saiu) chama ',
    ' (?:motor|motores|painel|quadro|fio|fios|cabo|cabos|bateria|baterias|gerador|barco|lancha|cozinha|fogao|casco|compressor|bomba|inversor|carregador|tomada|geladeira|cabine|camarote|praca de maquinas|sala de maquinas|casa de maquinas|isolamento|resistencia|ar condicionado)(?: [a-z0-9]+){0,2} queimando (?!(?:oleo|diesel|combustivel|muito|pouco|mais|menos|litros?|[0-9]+) )',
    ' queimando (?:(?:o|os|a|as) )?' + ALVO_FOGO + ' ',
    ' (?:levou|tomou|tomei|levei|levando|tomando) (?:um |o )?choque ',
    ' (?:tomada|painel|quadro|cabo|fio|fios|bateria|carregador|inversor|casco|corrimao|motor|gerador|torneira|chuveiro|pia|geladeira|barco|lancha|agua|cais|pier)(?: [a-z0-9]+){0,2} (?:dando|deu|da) (?:um |o )?choque ',
    ' choque (?:no|na|do|da|de|pelo|pela) (?:painel|quadro|cabo|fio|fios|bateria|baterias|barco|motor|gerador|tomada|inversor|carregador|casco|agua|mar) ',
    ' cheiro (?:de |do |da |no |na )?(?:[a-z]+ ){0,2}queimad[oa]s? ',
    // mangueira que estoura, solta ou fura (não a de lavagem, a do chuveiro nem a do ar-condicionado); eixo que quebra
    SEM_MANGUEIRA_DE_USO + 'mangueira(?: [a-z0-9]+){0,4} (?:estourou|estourada|soltou|rompeu|rompida|furou|furada|partiu|rasgou) ',
    SEM_MANGUEIRA_DE_USO + '(?:estourou|soltou|rompeu|furou|partiu|rasgou) (?:a|uma|essa|aquela|nossa|minha) mangueira ',
    ' eixo(?: [a-z0-9]+){0,3} (?:quebrou|quebrado|quebrada|partiu|partido|rompeu|empenou) '
  ];
  var SOS_REGEX = SOS_REGEX_FONTES.map(function (f) { return new RegExp(f); });
  // "a gente" é "nós", não a pessoa de "gente na água"/"gente cai": troca por "nos" antes de conferir
  function emergencia(q) {
    q = q.split(' a gente ').join(' nos ');
    return has(q, SOS) || SOS_REGEX.some(function (r) { return r.test(q); }) || (has(q, ['fumaca']) && !has(q, ['escap'])); // fumaça no escapamento é do motor, não SOS
  }
  // Rota salvatagem (PROMPT §2.3): ' boia ' só sem as palavras de boia de sinalização (amarra, poita, canal, baliza, cardinal, luz) nem de boia de
  // nível ou de âncora (revisão da 1b: a boia do porão, a do tanque e a de ancoragem não são salvatagem); "extintor" aqui sem fogo, fumaça nem
  // incêndio (com eles a SOS já respondeu, acima). ' colete ' e ' balsa ' com espaços: "coletei os dados" e "o bálsamo" não são salvatagem.
  var SALVATAGEM = [' colete ', ' coletes ', 'salva-vida', 'salva vida', ' balsa ', ' balsas ', 'bote salva', 'boia circular', 'boia salva', 'sinalizador', 'foguete', 'pirotecn', 'facho', 'salvatagem',
    'equipamento de seguranca', 'equipamentos de seguranca', 'kit de seguranca', 'sobreviv', ' plb ', ' sart '];
  var BOIA_FORA = ['amarra', 'poita', 'canal', 'baliza', 'cardinal', 'luz', 'nivel', 'porao', 'bomba', 'tanque', 'vaso', 'sanitario', 'combustivel', 'sensor', 'chave', 'ancor', 'fundei'];
  function salvatagem(q) { return has(q, SALVATAGEM) || (q.indexOf(' boia ') !== -1 && !has(q, BOIA_FORA)) || q.indexOf('extintor') !== -1; }
  // EPIRB (rota epirb): a baliza que disparou e o disparador hidrostático são do EPIRB, local, nunca da IA (a pergunta do botão da G1 do
  // certificado, "…disparador hidrostático", vai antes, para o docsvenc)
  var EPIRB_PALAVRAS = ['epirb', 'radiobaliza', 'baliza disparou', 'disparador hidrostatico'];
  // O sistema fixo que disparou ou descarregou (1b, §6.6 do contrato): "sistema fixo", "descarga do sistema", "depois do disparo", "descarreg…",
  // "depois da descarga", "disparou o sistema" e "sistema … disparou/disparo". Revisão da 1b: essas palavras sozinhas pegavam o alarme do porão,
  // o Seakeeper, o arrefecimento, a descarga do vaso e "descarregar as compras", e mandavam desligar motores e gerador. Agora (1) "sistema fixo"
  // vale sempre; (2) "o sistema disparou/descarregou", com a palavra colada ao "o sistema", é o fixo; (3) as demais só junto de uma âncora de
  // combate a incêndio (extinção, casa ou praça de máquinas, compartimento ou acesso ao motor). Fora a eletricidade: a bateria
  // que descarregou, o disjuntor do sistema elétrico que disparou, o carregador, o som e o plotter não são o Seafire.
  var ELETRICO = ['bateria', 'carregador', 'pilha', 'celular', 'tensao', 'volt', 'eletric', 'disjuntor', 'inversor', 'tomada', 'amper', ' som ', 'audio', 'musica',
    'bluetooth', 'plotter', 'radar', 'wifi', 'internet', 'climatiza', 'condicionado'];
  // (incêndio, supressão e Seafire já têm rota própria antes, na route(): aqui só o que ainda precisa de âncora)
  var FOGO_ANCORA = ['extin', 'maquinas', 'compartimento do motor', 'compartimento dos motores', 'compartimento de motor', 'acesso ao motor', 'abrir o motor', 'abrir o acesso'];
  var FOGO_GATILHO = ['descarga do sistema', 'depois do disparo', 'descarreg', 'depois da descarga', 'disparou o sistema'];
  var SISTEMA_SOZINHO = / o sistema (?:ja |todo |inteiro )?(?:disparou|disparado|descarregou|descarregado) /; // "o sistema…": "alarme de sistema disparou" e "o alarme do sistema disparou" não
  var DISPARO_SISTEMA = / sistema(?: [a-z0-9]+){0,6} (?:disparou|disparo|disparar|disparado) /;
  function seafireDisparo(q) {
    if (q.indexOf('sistema fixo') !== -1) return true;
    if (has(q, ELETRICO)) return false;
    if (SISTEMA_SOZINHO.test(q)) return true;
    return has(q, FOGO_ANCORA) && (has(q, FOGO_GATILHO) || DISPARO_SISTEMA.test(q));
  }
  // Óleo: 1 = queda/alarme relatado (passo a passo); 2 = só pergunta de pressão (leitura); 0 = outro assunto.
  // Exige "óleo" na frase (nunca "pressão baixa" sozinha: barômetro, água, chuveiro). Conservador: pressão do óleo sem ser pergunta simples
  // (qual/como/normal/faixa…) já é relato → passo a passo. Porão/vazamento só saem daqui sem pressão/alarme/luz; gerador, só sem "motor".
  var OLEO_QUEDA = / (?:baix|abaixo|cai |caiu|caind|cair|qued|alarm|alert|luz|acend|acesa|sem |zer|perd|despenc|sum|diminu|oscil|vermelh|fora d|nao esta |nao ta |saiu|menor|anormal)/;
  var OLEO_SINAL = / (?:pressao|alarm|alert|luz|acend|acesa)/, OLEO_NEUTRO = / (?:qual|quais|quanto|quanta|como|normal|faixa|alta|alto|ok|esta boa|ta boa|esta bom|ta bom) /;
  var OLEO_TOPICO = /^ (?:e )?(?:a )?pressao d[eo] oleo(?: d[oa]s? motor(?:es)?)?(?: (?:de )?(?:bb|be|bombordo|boreste))? $/;
  function oleo(q) {
    q = q.replace(/ oleo (?:diesel|combustivel)(?= )/g, ' diesel'); // "óleo diesel" é combustível, não óleo do motor
    if (!has(q, [' oleo']) || has(q, ['barometr', 'atmosf', 'hpa', 'pneu', 'hidraul'])) return 0;
    if (!OLEO_SINAL.test(q) && has(q, ['porao', 'vazament', 'vazand', 'pingand'])) return 0; // óleo no porão / vazamento: rota própria
    if (has(q, ['gerador', ' onan ']) && !has(q, ['motor'])) return 0; // óleo do gerador: rota do gerador (' onan ': 'funcionando' contém 'onan')
    var pressao = has(q, ['pressao']);
    if (OLEO_QUEDA.test(q)) return pressao || !has(q, ['troca']) ? 1 : 0;
    if (!pressao) return 0;
    return OLEO_NEUTRO.test(q) || OLEO_TOPICO.test(q) ? 2 : 1;
  }
  // Pedido de registro = comando explícito: imperativo (registre/registra/anote/anota; lance/grave só com "no diário") no começo da frase
  // ou de uma oração (depois de , ; : . ! ?, "por favor" ou "e"); infinitivo só depois de pode/poderia/quero/queria/por favor.
  // No meio, só "… registre no diário …" ou "…, anote aí" no fim, e nunca em pergunta. Não grava: negação antes do verbo ("não registre"),
  // sujeito/modal antes ("vou registrar", "o Lucas registra"), "<verbo>?" solto e pergunta sobre o recurso ("Gravar no diário funciona…?").
  var REG_VERBO = / ((?:(?:capitao|ok|sim|entao|agora|por favor|pode|poderia|quero|queria) (?:\| )?)*)(registre|registra|anote|anota|lance|lanca|grave|grava|registrar|anotar|gravar|lancar)((?: isso| aqui| ai| la)*)( no diario(?: de bordo)?)?(?= )/gi;
  var REG_NEGA = / (?:nao|nunca|jamais|sem)(?: \|)?(?: [a-z]+){0,2} (?:registre|registra|anote|anota|lance|lanca|grave|grava|registrar|anotar|gravar|lancar) /i;
  var REG_SUJEITO = /(?:^| )(?:vou|vamos|vai|tenho que|tem que|temos que|preciso|precisa|precisamos|pediu para|pediu pra|esqueci de|esqueceu de|a gente|ele|ela|eles|elas|eu|o lucas|lucas|o tecnico|a marina)(?= |$)/i;
  var REG_NOME = /(?:^| )(?:[Oo]s?|[Aa]s?) [A-Z][a-z]/, REG_VOCATIVO = /(?:^|\|) (?:o |a )?(?:lucas|capitao) \|$/i;
  var PERGUNTA = /^ (?:onde|quando|quem|como|qual|quais|quanto|quantos|quantas|o que|oque|que|por que|porque|pq|cade|sera|ja|eu ja|voce|voces) /;
  function querRegistrar(qRaw, q) {
    var raw = String(qRaw || '').slice(0, 2000), pergunta = /\?\s*$/.test(raw), m; // as telas já cortam em 500; teto contra texto enorme
    // sem acento, com a caixa original; pontuação vira fronteira de oração " | "
    var c = ' ' + raw.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/["“”«»()\[\]]/g, ' ').replace(/\s[-—–]+\s|[,;:.!?…—–]+/g, ' | ').replace(/\s+/g, ' ').trim() + ' ';
    if (REG_NEGA.test(c)) return false; // "não registre", "Não, registre", "nunca anote", "não precisa registrar" (na mesma oração)
    REG_VERBO.lastIndex = 0;
    while ((m = REG_VERBO.exec(c))) {
      var antes = c.slice(0, m.index), verbo = m[2].toLowerCase(), diario = !!m[4], resto = c.slice(m.index + m[0].length);
      var inicio = /^[\s|]*$/.test(antes), duro = /\|$/.test(antes), mole = /(?:^| )(?:e|por favor)$/i.test(antes) || /^por favor/i.test(m[1]);
      var oracao = (antes + ' ' + m[1]).split('|').pop(), cortesia = /(?:pode|poderia|quero|queria|por favor)[\s|]*$/i.test(antes + ' ' + m[1]);
      if (!inicio && !duro && !mole) continue; // verbo no meio da oração: "vou registrar", "Lucas registra", "esqueci de registrar"
      if (REG_SUJEITO.test(oracao) || REG_NOME.test(oracao) || (duro && REG_VOCATIVO.test(antes))) continue;
      if (/r$/.test(verbo) && !cortesia) continue; // "Registrar no diário é obrigatório?", "Vamos registrar…"
      if (!diario && !/^(?:registre|registra|anote|anota|anotar)$/.test(verbo)) continue; // "Grave problema no motor", "Lance a âncora"
      if (!inicio && (pergunta || PERGUNTA.test(q) || (!diario && !/^[\s|]*(?:por favor[\s|]*)*$/i.test(resto)))) continue;
      if (pergunta && (!cortesia || /^[\s|]*$/.test(resto))) continue; // "Anota?", "Registra aí?", "Pode anotar isso?"
      return true;
    }
    return false;
  }
  // Texto do usuário sem o comando ("Registre no diário: X" / "X, anote aí" → X)
  var CMD = '(?:registre|registra|registrar|anote|anota|anotar|lance|lança|lanca|lançar|lancar|grave|grava|gravar)(?![a-zà-ÿ])';
  var LUGAR = '(?:\\s+(?:isso|aqui|aí|ai|por favor))*(?:\\s+(?:no|em)\\s+(?:o\\s+)?di[aá]rio(?:\\s+de\\s+bordo)?)?(?:\\s+(?:isso|aqui|aí|ai|por favor))*';
  var CMD_INI = new RegExp('^[\\s,;:.!—–-]*(?:(?:por favor|pode|poderia|capit[aã]o|ok|sim|quero|queria|vamos)[\\s,;:.!—–-]+)*' + CMD + LUGAR + '(?:\\s*[:,;.!—–-]+|\\s+que(?=\\s|$))?\\s*', 'i');
  var CMD_FIM = new RegExp('(?:^|[\\s,;:.!—–-]+)(?:e\\s+)?(?:(?:por favor|pode|poderia|quero|queria)[\\s,]+)*' + CMD + LUGAR + '[\\s.!]*$', 'i');
  var NO_DIARIO = /\s+(?:no|em)\s+(?:o\s+)?di[aá]rio(?:\s+de\s+bordo)?[\s.!?]*$/i, POR_FAVOR_FIM = /[\s,;:—–-]+por favor[\s.!?]*$/i, SOBRA_INI = /^(?:(?:por favor|que)(?:[\s,;:.!—–-]+|$))+/i;
  var DIARIO_INI = /^(?:no|em)\s+(?:o\s+)?di[aá]rio(?:\s+de\s+bordo)?(?:[\s,;:.!—–-]+|$)/i; // "Registre, no diário, a saída" → "a saída"
  // "posição e hora", "posição, hora e rumo", "a posição atual", "o evento" (texto dos próprios avisos do app) = resumo da telemetria
  var ITEM_RESUMO = '(?:(?:o|a) )?(?:posicao|hora|horario|evento|rumo|proa)(?: (?:atual|de agora|agora|do barco|do evento))?';
  var RESUMO = new RegExp('^(?:(?:o|a|um|uma) )?resumo(?: |$)|^' + ITEM_RESUMO + '(?:(?:,? e |, )' + ITEM_RESUMO + ')*$');
  // "posição e hora do MOB", "posição e hora, homem ao mar": grava o resumo da telemetria junto com as palavras do usuário
  var RESUMO_MAIS = new RegExp('^(?:' + ITEM_RESUMO + '(?:(?:,? e |, )' + ITEM_RESUMO + ')+,? |' + ITEM_RESUMO + ', )(?=[a-z0-9])');
  function resumoMais(nota) { return !!nota && RESUMO_MAIS.test(norm(nota)); }
  function notaDoUsuario(q) {
    var s = String(q || '').replace(/^[\s"“”«»]+|[\s"“”«»]+$/g, ''); // “registre posição e hora” dito entre aspas
    if (!s || norm(s).trim() === CANON.diario) return '';
    s = s.replace(/[\s?]+$/, '').replace(POR_FAVOR_FIM, ''); // "…?" e "…, por favor" no fim
    s = CMD_INI.test(s) ? s.replace(CMD_INI, '').replace(SOBRA_INI, '').replace(DIARIO_INI, '').replace(SOBRA_INI, '').replace(NO_DIARIO, '')
      : s.replace(CMD_FIM, '').replace(POR_FAVOR_FIM, '').replace(NO_DIARIO, ''); // "…, por favor registre" / "posição e hora no diário, registre"
    s = s.replace(/^[\s,;:.!—–"“”«»-]+|[\s,;:—–"“”«»-]+$/g, '');
    if (!s || RESUMO.test(norm(s).replace(/[.!?;:]+/g, ' ').replace(/\s*,\s*/g, ', ').replace(/\s+/g, ' ').trim())) return ''; // "registre o resumo / posição e hora" = atalho
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  function A(platform, key) { return (HREF[platform] || HREF.web)[key]; }
  function act(platform, pairs) { return pairs.map(function (p) { return { l: p[0], href: p[1].indexOf('.html') !== -1 || p[1].indexOf('#') === 0 ? p[1] : A(platform, p[1]) }; }); }
  function askHref(platform, q) { return A(platform, 'home') + '#q=' + encodeURIComponent(q); }

  var P = D.protocolos || {};
  var ROTULO = P.rotulo || 'procedimento padrão — confirmar com o protocolo de bordo';
  // MMSI_RADIO (PROMPT §2.2): em todo texto de emergência e de rádio o MMSI é o da etiqueta do rádio (Licença de Estação); o número do
  // cadastro do app (E.mmsi) só na Embarcação, nos Documentos, na F3 e no `## Embarcação` da ficha — lido na hora (mmsiNum), nunca na carga,
  // porque o SOS carrega este arquivo. Indicativo: o da Licença de Estação, nunca gerado.
  var MMSI_RADIO = P.mmsiRadio || 'MMSI do rádio de bordo (etiqueta / Licença de Estação)';
  var INDICATIVO = P.indicativo || 'o da Licença de Estação (no rádio)';
  function mmsiNum() { return E.mmsi ? 'MMSI ' + E.mmsi : 'MMSI ' + SD; }
  // Os passos vêm do D.protocolos (fonte única do SOS, dos guias e dos cartões): mob, seafire.passos, epirb.passos, oleo. Nada de posição,
  // rumo, SOG, ETA, pessoas a bordo do quadro, MMSI gerado, modelo, validade nem lugar de equipamento de salvatagem (trava 17).
  var NOTA_ETIQUETA = (P.seafire && P.seafire.nota) || (P.epirb && P.epirb.nota) || 'modelo, validade e acionamento: veja a etiqueta do equipamento';
  function passosDe(x) { return (x && x.passos) || []; }
  function maius1(t) { t = String(t || ''); return t.charAt(0).toUpperCase() + t.slice(1); }
  function numerados(xs, ini) { return xs.map(function (t, i) { return ((ini || 1) + i) + '. ' + t; }).join('\n'); }
  var MOB = P.mob || [], SEAFIRE_PASSOS = passosDe(P.seafire), EPIRB_PASSOS = passosDe(P.epirb);
  // Passos do SOS: resposta sos e, inteiros, no registro de diário que cita emergência. Chat nunca grava sozinho — só "registre no diário…".
  // Posição do MAYDAY é a do plotter na hora da chamada. Seafire e EPIRB: só o procedimento padrão, com a etiqueta do equipamento.
  var SOS_PASSOS = 'Ordem (' + ROTULO + '):\n1. VHF canal 16 · MAYDAY — nome ×3, ' + MMSI_RADIO + ', posição lida no plotter, perigo, pessoas a bordo (conte agora), auxílio\n2. Homem ao mar: ' + MOB.join(' ') +
    '\n3. Incêndio · Seafire: ' + [SEAFIRE_PASSOS[0], SEAFIRE_PASSOS[4]].filter(Boolean).join(' ') + '\n4. EPIRB: ' + (EPIRB_PASSOS[0] || '');
  // O que a ficha da IA leva da emergência: a ordem e o MMSI do rádio, sem os passos (emergência não vai à IA; os passos estão nas respostas
  // locais, na tela SOS e nos guias). Mantém a ficha dentro do teto de 9.800 letras do contrato (§6.1).
  var SOS_FICHA = 'Ordem (' + ROTULO + '): 1. VHF canal 16 · MAYDAY com o ' + MMSI_RADIO + ' e a posição lida no plotter; 2. homem ao mar; 3. incêndio · Seafire; 4. EPIRB. Os passos estão nas respostas locais (sos, seafire, epirb), na tela SOS e nos guias; emergência não vai à IA.';
  // Passos da pressão de óleo baixa: resposta oleo e, inteiros, no registro de diário que relata queda/alarme de pressão. Sem leitura do quadro.
  var OLEO_PASSOS = numerados(P.oleo || []);
  // Base completa externa (NotebookLM) não configurada nesta embarcação: o fallback leva a pendência e FAQ.
  var BASE = null;
  // Texto de emergência não manda gravar o resumo da telemetria (nada de posição, rumo nem velocidade do quadro): o relato vai em palavras, a posição se lê no plotter.
  var GRAVAR_AGORA = 'Para registrar no diário: diga “registre no diário…” e o que aconteceu; a posição, leia no plotter.';
  var LOCAL_PLACA = 'no local da placa de salvatagem e do plano de segurança de bordo — confira na saída';   // a frase da salvatagem (protocolos.salvatagem), sem lugar inventado
  var LOCAL_PLANO = 'no local indicado no plano de segurança de bordo — confira na saída';
  function resumoAgora() {
    return SNAP.local + ' · ' + SNAP.pos + ' · SOG ' + nb(S.sog) + ' nó · proa ' + grau3(S.proa) + ' · ' + SNAP.motores + ' · gerador ' + (G.estado || SD) + ' (' + horas(G.horas) + ' h) · Seakeeper ' + ((S.seakeeper && S.seakeeper.estado) || SD) + ' · banco 24 V ' + nb(S.bat24, 2) + ' V · vento ' + nb(S.vento) + ' nós de ' + grau3(S.ventoDe) + ' · diesel ' + SNAP.diesel + ' (' + SNAP.dieselHora + ') — snapshot' + DEMO_ + ' ' + SNAP.quando + '.';
  }
  function mareTexto() {
    var C = window.CapitaoClima; var x = C && C.mareAgora ? C.mareAgora() : null;
    if (x == null) return null;
    var prox = (C.mareProximas ? C.mareProximas(6) : []).filter(function (p, i) { return i % 2 === 0; }).map(function (p) {
      var h = new Date(p.ms); var hh = ('0' + h.getHours()).slice(-2) + 'h';
      try { hh = new Intl.DateTimeFormat('pt-BR', { timeZone: C.TZ, hour: '2-digit' }).format(h) + 'h'; } catch (e) {}
      return hh + ' ' + C.metro(p.m);
    });
    return { agora: C.metro(x), prox: prox };
  }
  // Previsão de hoje do cabeçalho (capitao-clima.js: ECMWF via Open-Meteo, mundo real — nunca o snapshot), com a fonte e a hora da
  // leitura (sem rede, a da cópia salva do dia). null = sem leitura de hoje neste aparelho (as telas de pergunta livre carregam o
  // capitao-clima.js: Main, H2 e B3). O vento previsto é informação com fonte: o app não tem limite de vento para dizer se é
  // seguro sair. Direção por extenso (o TTS lê "NE" como "né").
  var RUMO_NOME = { N: 'norte', NE: 'nordeste', E: 'leste', SE: 'sudeste', S: 'sul', SW: 'sudoeste', W: 'oeste', NW: 'noroeste' };
  function previsao() {
    var C = window.CapitaoClima, c = C && C.clima ? C.clima() : null;
    if (!c || typeof c.max !== 'number' || typeof c.min !== 'number') return null;
    var n0 = function (x) { return typeof x === 'number' && isFinite(x) ? String(Math.round(x)) : null; }, dr = RUMO_NOME[C.rumo ? C.rumo(c.dir) : ''] || '';
    var vento = n0(c.vento) ? 'vento até ' + n0(c.vento) + ' nós' + (dr ? ' de ' + dr : '') + (n0(c.raj) ? ', rajadas até ' + n0(c.raj) + ' nós' + (c.rajModelo ? ' (rajada do melhor modelo do Open-Meteo; o ECMWF não trouxe)' : '') : ', rajadas ' + SD) : 'vento ' + SD;
    return { temp: 'máx ' + n0(c.max) + '° · mín ' + n0(c.min) + '°', vento: vento, fonte: C.fonte ? C.fonte(c) : 'Open-Meteo' };
  }
  function windy() { var C = window.CapitaoClima; return { l: 'Abrir o windy.com', href: (C && C.WINDY) || 'https://www.windy.com/', ext: true }; }

  var ANSWERS = {
    // Pergunta sobre o app sem a IA ("o que você faz?"): a voz não repete a abertura ("Capitão IA online. Que precisa?"),
    // que soava como se a pergunta fosse ignorada — fala o que o Capitão faz.
    saudacao: function (p, ctx, q) { return { fala: q && !SO_OI.test(pad(q)) ? 'Respondo sobre telemetria, manutenção, documentos, abastecimento, diário de bordo e os passos de cada equipamento, sempre citando a fonte.' : '', text: 'Capitão IA online. Que precisa?\nOlá, ' + quem() + '. ' + (window.CapitaoAuth && window.CapitaoAuth.frase ? window.CapitaoAuth.frase() : '') + '\nRespondo sobre telemetria, manutenção, documentos, abastecimento, diário de bordo e os passos de cada equipamento — sempre citando a fonte.' + (D.demo ? '\n' + (D.selo || 'DEMO') + ': esta embarcação é de demonstração.' : ''), src: FT.tele + (D.selo ? ' · ' + D.selo : ''), actions: act(p, [['Console completo', 'console'], ['FAQ de bordo', 'faq']]) }; },
    // Grava as palavras do usuário; sem texto (ou atalho DIÁRIO DE BORDO) grava o resumo da telemetria. commit:false (veio de link) não grava.
    diario: function (p, ctx, q) {
      var n = now(), grava = !ctx || ctx.commit !== false, nota = notaDoUsuario(q);
      var como = 'Para registrar, diga ou digite aqui “registre no diário…” seguido do texto';
      var junto = resumoMais(nota); // nota que pede posição/hora: resumo + nota numa linha só
      if (nota && !junto) {
        var alerta = emergencia(pad(nota)), pressao = oleo(pad(nota)) === 1; // relato de emergência / pressão de óleo: grava a nota e traz os passos
        if (grava) addDiario({ sys: 'Diário', t: nota, who: quem(), src: 'chat · voz/texto' });
        return { text: (grava ? 'Registrado no diário de bordo · ' + n.d + ' ' + n.t + ' · ' + quem() + '\n“' + nota + '”\nLinha nova — nada se apaga.' : 'Não registrado — pedido vindo de link não grava no diário:\n“' + nota + '”\n' + como + '.') + (alerta ? '\nSe a emergência é agora: abra o SOS. ' + SOS_PASSOS : '') + (pressao ? '\nSe a pressão de óleo está baixa agora, verifique nesta ordem:\n' + OLEO_PASSOS : ''), src: 'Fonte: anotação de ' + quem() + ' · diário de bordo do app' + (pressao ? ' · ' + guia('g_motores') + ' §4' : ''), actions: act(p, (alerta ? [['Abrir SOS', 'sos']] : []).concat(pressao ? [['Contatos', 'equipe']] : [], [['Abrir diário', 'diario']])) };
      }
      var t = resumoAgora();
      var al = junto && emergencia(pad(nota)), pr = junto && oleo(pad(nota)) === 1;
      var passos = (al ? '\nSe a emergência é agora: abra o SOS. ' + SOS_PASSOS : '') + (pr ? '\nSe a pressão de óleo está baixa agora, verifique nesta ordem:\n' + OLEO_PASSOS : '');
      var acoes = (al ? [['Abrir SOS', 'sos']] : []).concat(pr ? [['Contatos', 'equipe']] : [], [['Abrir diário', 'diario']]);
      if (grava) addDiario({ sys: 'Navegação', tone: 'var(--cap-tele, #00f4fd)', t: (junto ? nota + ' · resumo: ' : 'Resumo registrado pelo atalho: ') + t, who: quem(), src: junto ? 'chat · voz/texto · telemetria' + DEMO : 'atalho · telemetria' + DEMO });
      return { text: (grava ? 'Registrado no diário de bordo · ' + n.d + ' ' + n.t + ' · ' + quem() + '\n' + (junto ? '“' + nota + '”\n' : '') + t + '\nLinha nova — nada se apaga.' : 'Não registrado — pedido vindo de link não grava no diário.\n' + (junto ? '“' + nota + '”\n' : '') + 'Resumo: ' + t + '\n' + como + ', ou toque no atalho DIÁRIO DE BORDO.') + passos, src: FT.tele + ' · diário de bordo do app' + (pr ? ' · ' + guia('g_motores') + ' §4' : ''), actions: act(p, acoes) };
    },
    seguro: function (p) {
      var at = atrasadas(), porao = tarefa('porao-teste');
      var ress = [];
      if (porao && porao.dn < 0) ress.push('(segurança): teste das bombas de porão e alarmes ' + prazoTxt(porao) + ' — acione cada bomba manualmente antes de largar.');
      at.filter(function (x) { return x.id !== 'porao-teste'; }).forEach(function (x) { ress.push(x.t + ' — ' + prazoTxt(x) + '.'); });
      var pv = previsao();
      ress.push(pv ? 'Previsão de hoje em Balneário Camboriú (' + pv.fonte + '): ' + pv.vento + ' · mar (ondas): ' + SD + ' no app — confira a previsão da Marinha antes de sair.' : 'Sem previsão de vento e mar carregada (' + SD + ') — confira a previsão da Marinha antes de sair.');
      return { text: 'Sim, com ' + ress.length + ' ressalvas — a primeira é de segurança.\n• Condições a bordo (snapshot' + DEMO_ + ' ' + SNAP.quando + '): vento ' + nb(S.vento) + ' nós de ' + grau3(S.ventoDe) + ' · barômetro ' + nb(S.pressao, 0) + ' hPa · ' + ((S.gps && S.gps.satelites) || '—') + ' satélites · banco 24 V ' + nb(S.bat24, 2) + ' V.\n• Diesel ≈ ' + mil(DI.litros) + ' L (' + SNAP.diesel.split(' (')[0] + ') → ≈ ' + nb(AUT.horas) + ' h a ' + ((CON.cruzeiro && CON.cruzeiro.nos) || '—') + ' nós com reserva de 10 %.\n' + ress.map(function (r, i) { return '• Ressalva ' + (i + 1) + (r.charAt(0) === '(' ? ' ' : ': ') + r; }).join('\n') + '\n' + SNAP.motores.charAt(0).toUpperCase() + SNAP.motores.slice(1) + ' · sem alarmes.', src: FT.tele + ' · ' + FT.agenda.replace('Fonte: ', '') + (pv ? ' · previsão ' + pv.fonte : ''), actions: act(p, [['Ver manutenção', 'manut'], ['Checklist de saída', askHref(p, 'Checklist de saída')]]).concat(pv ? [windy()] : []) };
    },
    destinos: function (p) { return { text: 'SEM DADOS de rotas: nenhum roteiro ou destino cadastrado nas fontes (' + ((D.drive && D.drive.raiz) || 'Drive') + ').\nAlcance com o diesel a bordo: ≈ ' + AUT.mn + ' mn (≈ ' + nb(AUT.horas) + ' h a ' + CON.cruzeiro.nos + ' nós, reserva de 10 %) — ida e volta até ≈ ' + Math.floor(AUT.mn / 2) + ' mn da posição atual.\nCadastre os destinos (nome e posição) para eu calcular distância, tempo e diesel de cada um.', src: 'Fonte: telemetria' + DEMO + ' · consumo observado ' + (CON.periodo || '') + ' · roteiros: nenhum', actions: act(p, [['Autonomia', askHref(p, 'Autonomia')], ['Registrar pendência', 'diario']]) }; },
    manutencao: function (p) {
      var at = atrasadas(), prox = agenda().filter(function (t) { return t.dn >= 0; }).slice(0, 3), oleoM = tarefa('motores-oleo');
      return { text: 'Atrasadas (' + at.length + '):\n' + at.map(function (t) { return '• ' + t.t + ' · ' + t.equip + ' — ' + prazoTxt(t) + ' (' + t.quem + ')'; }).join('\n') + '\nPróximas:\n' + prox.map(function (t) { return '• D-' + t.dn + ' · ' + t.vence.slice(0, 5) + ' — ' + t.t + ' (' + t.quem + ')'; }).join('\n') + (oleoM && oleoM.horas ? '\nÓleo e filtros dos motores: ' + oleoM.vence + ' ou ' + oleoM.horas.limite + ' h — faltam ' + nb(oleoM.horas.faltam) + ' h.' : '') + (D.agendaFalta && D.agendaFalta.length ? '\nFalta registrar: ' + D.agendaFalta.join(' · ') + '.' : ''), src: FT.agenda + ' · ' + agenda().length + ' tarefas · horímetros ' + (M.hora || ''), actions: act(p, [['Abrir manutenção', 'manut']]) };
    },
    autonomia: function (p) { return { text: '≈ ' + nb(AUT.horas) + ' h · ≈ ' + AUT.mn + ' mn a ' + CON.cruzeiro.nos + ' nós (' + mil(CON.cruzeiro.rpm) + ' rpm · ' + CON.cruzeiro.lph + ' L/h, dois motores), com reserva de 10 %.\nA bordo ≈ ' + mil(DI.litros) + ' L de ' + mil(DI.capacidade) + ' (BB ' + nb(DI.bb) + ' % · BE ' + nb(DI.be) + ' %) — ' + SNAP.dieselHora + '.\nEm marcha lenta (' + nb(CON.lenta.lph) + ' L/h) ≈ ' + AUT.lenta + ' h. Consumido desde o abastecimento de ' + CON.desdeAbast.desde.slice(0, 5) + ': ≈ ' + CON.desdeAbast.litros + ' L (' + CON.desdeAbast.horas + ').', src: 'Fonte: telemetria' + DEMO + ' (taxa de combustível dos dois motores, ' + CON.periodo + ') · ' + FT.abast.replace('Fonte: ', '') + ' — estimativa; a nota fiscal é a fonte oficial', actions: act(p, [['Abastecimento', 'abast']]) }; },
    mare: function (p) {
      var m = mareTexto();
      if (!m) return { text: 'SEM DADOS de maré agora: sem internet e sem leitura salva neste aparelho.\nO app usa o modelo do Open-Meteo Marine na posição de referência (Balneário Camboriú) — não é a tábua oficial da Marinha (DHN).', src: 'Fonte: nenhuma disponível agora — Open-Meteo Marine sem resposta', actions: act(p, [['Registrar pendência', 'diario']]) };
      return { text: 'Maré agora ' + m.agora + ' em relação ao nível médio do mar (Balneário Camboriú).\nPróximas horas: ' + m.prox.join(' · ') + '.\nÉ modelo (≈ 8 km), não a tábua oficial da Marinha — não use para passar em canal raso. Corrente: ' + SD + '.', src: 'Fonte: Open-Meteo Marine (sea_level_height_msl) · posição de referência ' + ((D.posicaoRef && D.posicaoRef.fonte) || ''), actions: act(p, [['Clima', askHref(p, 'Clima')]]) };
    },
    clima: function (p) {
      var pv = previsao();
      return { text: (pv ? 'Hoje em Balneário Camboriú: ' + pv.temp + ' · ' + pv.vento + ' (previsão ' + pv.fonte + ').' : 'Previsão do dia: ' + SD + ' (sem leitura de hoje neste aparelho).') + '\nLeitura de bordo (snapshot' + DEMO_ + ' ' + SNAP.quando + '):\n• vento verdadeiro ' + nb(S.vento) + ' nós de ' + grau3(S.ventoDe) + '\n• barômetro ' + nb(S.pressao, 0) + ' hPa\n• ar ' + nb(S.ar) + ' °C · água do mar ' + nb(S.agua) + ' °C\n' + (pv ? 'Previsão do mar (ondas): ' + SD + ' no app — para navegar, consulte a meteorologia marinha da Marinha do Brasil.' : 'Previsão de vento e mar para navegar: ' + SD + ' no app — consulte a meteorologia marinha da Marinha do Brasil.'), src: 'Fonte: ' + (pv ? 'previsão ' + pv.fonte : 'previsão Open-Meteo: sem leitura de hoje neste aparelho') + ' · ' + SNAP.fonte, actions: act(p, [['Telemetria', 'console']]).concat(pv ? [windy()] : []) };
    },
    canal16: function (p) {
      return { text: 'Em perigo grave e iminente: MAYDAY no canal 16 (156,800 MHz), em voz alta e devagar, até ter resposta.\n' + MMSI_RADIO + ' · indicativo: ' + INDICATIVO + ' · ' + min1(fabMod('vhf')) + '.\nRoteiro MAYDAY (' + ROTULO + '):\n' + (P.roteiro || []).join(' — ') + '.\nUrgência sem perigo de vida: PAN-PAN ×3.', src: FT.proto + ' · canal 16 e MMSI do rádio de bordo', actions: act(p, [['Abrir SOS', 'sos']]) };
    },
    checklist: function (p) { var porao = tarefa('porao-teste'); return { text: 'Checklist de saída — do que está catalogado:\n1. Gerador Onan: depois de ligar, confira água no escapamento.\n2. Estabilizador Seakeeper: ligue com antecedência, com o banco de 12 V carregado.\n3. Climatização: filtro de água salgada limpo antes de ligar' + (tarefa('clima-filtro') && tarefa('clima-filtro').dn < 0 ? ' (limpeza ' + prazoTxt(tarefa('clima-filtro')) + ')' : '') + '.\n4. Eletrônicos: plotter ligado, piloto em espera até sair da marina, VHF no canal 16.\n5. Bombas de porão: acione cada uma manualmente e confira o alarme' + (porao && porao.dn < 0 ? ' (teste ' + prazoTxt(porao) + ')' : '') + '.\n6. Diesel BB ' + nb(DI.bb, 0) + ' % · BE ' + nb(DI.be, 0) + ' % — regra: ' + (D.regraAbast || SD) + '.\nAmarração e fechamento: A CONFIRMAR (sem checklist oficial do estaleiro).', src: 'Fonte: ' + guia('checklist') + ' · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['FAQ de bordo', 'faq']]) }; },
    checklistChegada: function (p) { return { text: 'Checklist de chegada — do que está catalogado:\n1. Piloto em espera antes de manobrar.\n2. Estabilizador: desligar ao atracar e manter energia até o volante parar.\n3. Gerador: retirar cargas, 3 a 5 min sem carga, desligar.\n4. Climatização: desligar e fechar a válvula de fundo se o barco ficar parado.\n5. Fechar a saída no diário: horas, consumo e pendências.', src: 'Fonte: ' + guia('checklist') + ' (Chegada)', actions: act(p, [['Fechar no diário', 'diario']]) }; },
    consumo: function (p) { var ab = D.abastecimentos || []; return { text: 'Consumo observado (telemetria' + DEMO + ' ' + CON.periodo + '):\n• cruzeiro — ' + CON.cruzeiro.lph + ' L/h (' + mil(CON.cruzeiro.rpm) + ' rpm · ' + CON.cruzeiro.nos + ' nós, dois motores)\n• marcha lenta — ' + nb(CON.lenta.lph) + ' L/h\nDesde o abastecimento de ' + CON.desdeAbast.desde.slice(0, 5) + ': ≈ ' + CON.desdeAbast.litros + ' L (' + CON.desdeAbast.horas + ').' + (ab.length ? '\nAbastecimentos registrados: ' + ab.map(function (a) { return a.d.slice(0, 5) + ' · ' + mil(a.litros) + ' L'; }).join(' · ') + '.' : ''), src: 'Fonte: ' + CON.fonte + ' · ' + FT.abast.replace('Fonte: ', ''), actions: act(p, [['Abastecimento', 'abast']]) }; },
    tanques: function (p) { return { text: 'Tanques (snapshot' + DEMO_ + ' ' + SNAP.quando + '):\n• água doce ' + nb(T.agua) + ' %\n• águas cinzas ' + nb(T.cinzas) + ' %\n• águas negras ' + nb(T.negras) + ' %\n• diesel ' + SNAP.diesel + ' — ' + SNAP.dieselHora + '.', src: FT.tele + ' (diesel ' + (DI.hora || '') + ')', actions: act(p, [['Telemetria', 'console']]) }; },
    contatos: function (p) {
      var eq = D.equipe || {}, per = eq.perfis || [], ap = eq.apoio || [], f = loadEquipe().fones, cad = Object.keys(f).length;
      return { text: 'Acesso total: ' + per.map(function (x) { return x.nome + ' (' + x.papel + ')'; }).join(' · ') + '.\nApoio: ' + ap.map(function (a) { return min1(a.papel) + (a.para ? ' (' + a.para + ')' : ''); }).join(' · ') + '.\nTelefones: ' + (cad ? cad + ' cadastrado(s) neste aparelho — abra Equipe para ligar.' : 'A CADASTRAR em Equipe (ficam só neste aparelho).'), src: 'Fonte: cadastro da equipe' + DEMO + ' · telefones do aparelho', actions: act(p, [['Equipe e contatos', 'equipe']]) };
    },
    anomalias: function (p) {
      var pend = pendencias(), app = loadDiario().filter(function (e) { return /pend[eê]ncia|anomalia|A CONFIRMAR|A CONFERIR/i.test(e.t); }).slice(0, 3);
      return { text: 'Pendências abertas (' + (pend.length + app.length) + '):\n' + pend.map(function (x) { return '• ' + x.d + ' · ' + x.sys + ' — ' + x.t; }).concat(app.map(function (x) { return '• ' + x.d + ' · ' + (x.sys || 'Diário') + ' — ' + String(x.t).slice(0, 110) + ' (app)'; })).join('\n') + '\nAtrasadas na agenda: ' + atrasadas().length + ' (veja Manutenção).', src: FT.diario + ' · diário do app', actions: act(p, [['Abrir diário', 'diario'], ['Manutenção', 'manut']]) };
    },
    porao: function (p) { var t = tarefa('porao-teste'); return { text: 'Teste de bombas de porão e alarmes ' + (t ? prazoTxt(t) + ' (agenda: ' + t.quem + ' · ' + t.intervalo + ')' : SD) + '.\nSem sensor de porão no barramento NMEA — SEM LEITURA.\nAntes de sair: acione cada bomba manualmente e confira o alarme; registre o resultado no diário.', src: FT.agenda + ' · coletor NMEA' + DEMO + ' (sem sentença de porão)', actions: act(p, [['Manutenção', 'manut']]) }; },
    gerador: function (p) { var r = tarefa('gerador-rotor'), rv = tarefa('gerador-revisao'); return { text: fabMod('gerador') + ' · ' + horas(G.horas) + ' h (' + (G.estado || SD) + ' · snapshot' + DEMO_ + ' ' + SNAP.quando + ').\nLigar: confira óleo, válvula de fundo e filtro de água salgada → segure PARTIDA → espere tensão e frequência estabilizarem → cargas uma a uma, climatização por último.\nDesligar: retire as cargas, 3 a 5 min sem carga, PARADA.' + (r ? '\n' + r.t + ': ' + prazoTxt(r) + '.' : '') + (rv && rv.horas ? ' Revisão (óleo e filtros): ' + rv.vence + ' ou ' + mil(rv.horas.limite) + ' h — faltam ' + nb(rv.horas.faltam) + ' h.' : ''), src: 'Fonte: ' + guia('g_gerador') + ' §1–4 · ' + FT.agenda.replace('Fonte: ', '') + ' · horímetro na telemetria' + DEMO, actions: act(p, [['Passo a passo', 'f4']]) }; },
    telemetria: function (p) {
      var T = S.tanques || {}, G = S.gerador || {}, K = S.seakeeper || {};
      return { text: 'Snapshot' + DEMO + ' de ' + SNAP.quando + ': ' + min1(SNAP.local) + '. Telemetria ao vivo desligada.'
        + '\n• Posição ' + SNAP.pos + ' · SOG ' + nb(S.sog) + ' nó · proa ' + grau3(S.proa) + ' · profundidade ' + nb(S.profundidade) + ' m'
        + '\n• Vento ' + nb(S.vento) + ' nós de ' + grau3(S.ventoDe) + ' · pressão ' + nb(S.pressao, 0) + ' hPa · ar ' + nb(S.ar) + ' °C · mar ' + nb(S.agua) + ' °C'
        + '\n• Baterias 24 V ' + nb(S.bat24, 2) + ' V · 12 V ' + nb(S.bat12, 2) + ' V'
        + '\n• Tanques: água doce ' + nb(T.agua) + ' % · cinzas ' + nb(T.cinzas) + ' % · negras ' + nb(T.negras) + ' %'
        + '\n• Diesel ' + SNAP.diesel + ' — ' + SNAP.dieselHora
        + '\n• ' + SNAP.motores.charAt(0).toUpperCase() + SNAP.motores.slice(1)
        + '\n• Gerador ' + (G.estado || SD) + ' · ' + (G.horas != null ? horas(G.horas) + ' h' : 'horímetro ' + SD) + ' · Seakeeper ' + (K.estado || SD)
        + '\n• Porão e âncora: SEM LEITURA.',
        src: FT.tele, actions: act(p, [['Telemetria', 'console'], ['Manutenção', 'manut']]) };
    },
    posicao: function (p) { return { text: SNAP.pos + ' · ' + (S.estado || SD).toLowerCase() + ' · ' + (S.local || SD) + '\nSOG ' + nb(S.sog) + ' nó · proa ' + grau3(S.proa) + ' · ' + ((S.gps && S.gps.satelites) || '—') + ' satélites · profundidade ' + nb(S.profundidade) + ' m · snapshot' + DEMO_ + ' ' + SNAP.quando + '.', src: 'Fonte: GPS na rede NMEA 2000 · ' + SNAP.fonte, actions: act(p, [['Telemetria', 'console']]) }; },
    docsvenc: function (p) {
      // Documento ligado a um equipamento de segurança (o certificado do EPIRB): sem a data nem o D-n; a etiqueta do equipamento vale (1b, trava 17)
      var seg = function (d) { return (D.equipamentos || []).some(function (e) { return e.seguranca && e.validade === d.id; }); };
      var todos = (D.documentos || []), segDocs = todos.filter(seg), ds = todos.filter(function (d) { return !seg(d); });
      var com = ds.filter(function (d) { return d.dn != null; }).sort(function (a, b) { return a.dn - b.dn; });
      var vence = com.filter(function (d) { return d.dn <= 90; }), dia = com.filter(function (d) { return d.dn > 90; }), sem = ds.filter(function (d) { return d.st === SD; }), conf = ds.filter(function (d) { return /A CONF/.test(d.st); });
      return { text: 'Vencem primeiro:\n' + (vence.length ? vence.map(function (d) { return '• ' + d.n + ' — ' + d.vence + ' (D-' + d.dn + ')'; }).join('\n') : '• nenhum nos próximos 90 dias') + '\nEm dia: ' + dia.map(function (d) { return min1(d.n) + ' até ' + d.vence; }).join(' · ') + '.\n' + SD + ': ' + sem.map(function (d) { return d.n; }).join(' · ') + '.' + (conf.length ? '\nA CONFERIR: ' + conf.map(function (d) { return d.n; }).join(' · ') + '.' : '') + (segDocs.length ? '\nSegurança: ' + segDocs.map(function (d) { return min1(d.n) + ' — ' + NOTA_ETIQUETA; }).join(' · ') + '.' : ''), src: FT.docs, actions: act(p, [['Documentos', 'docs']]) };
    },
    horimetros: function (p) { var o = tarefa('motores-oleo'), rv = tarefa('gerador-revisao'); return { text: 'Horímetros (motores: última leitura ligados ' + (M.hora || SD) + ' · gerador ' + (G.hora || SD) + '):\n• motor BB ' + horas(M.horimetro && M.horimetro[0]) + ' h\n• motor BE ' + horas(M.horimetro && M.horimetro[1]) + ' h\n• gerador ' + horas(G.horas) + ' h\nPróxima troca de óleo dos motores: ' + (o ? o.vence + ' (D-' + o.dn + ') ou ' + o.horas.limite + ' h — faltam ' + nb(o.horas.faltam) + ' h; o que vier antes.' : SD) + (rv ? '\nRevisão do gerador: ' + rv.vence + ' (D-' + rv.dn + ') ou ' + mil(rv.horas.limite) + ' h.' : ''), src: FT.tele + ' · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['Manutenção', 'manut']]) }; },
    motores: function (p) { var e = equip('motores'); return { text: 'Motores ' + (e && e.qtd ? e.qtd + ' × ' : '') + 'Volvo Penta' + (e && e.lados ? ' (' + e.lados + ')' : '') + ' · modelo ' + SD + '.\n' + SNAP.motores.charAt(0).toUpperCase() + SNAP.motores.slice(1) + ' · sem alarme.\nHorímetros BB ' + horas(M.horimetro && M.horimetro[0]) + ' h · BE ' + horas(M.horimetro && M.horimetro[1]) + ' h · troca de óleo ' + prazoTxt(tarefa('motores-oleo')) + ' ou 450 h.\nPartida, aquecimento e parada: ' + guia('g_motores') + '. Faixas oficiais: manual do fabricante — modelo ' + SD + '.', src: 'Fonte: ' + guia('g_motores') + ' · ' + SNAP.fonte, actions: act(p, [['Manutenção', 'manut'], ['FAQ de bordo', 'faq']]) }; },
    estabilizador: function (p) { var an = tarefa('seakeeper-anodo'); return { text: fabMod('estabilizador') + ' · ' + ((S.seakeeper && S.seakeeper.estado) || SD) + ' (snapshot' + DEMO_ + ' ' + SNAP.quando + ').\n• Funciona no banco de 12 V: acelera com o banco carregado (carregador ligado ao gerador ou ao cais); estabiliza quando o display indicar pronto.\n• Ao atracar: desligue e mantenha a energia até o volante parar.\n• Nunca faça manutenção com o volante girando.\nTempo de aceleração e códigos de alarme: MANUAL NO DRIVE (modelo ' + SD + ').' + (an ? '\n' + an.t + ': ' + prazoTxt(an) + '.' : ''), src: 'Fonte: ' + guia('g_seakeeper') + ' §1–6 · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['Passo a passo', 'f2']]) }; },
    climatizacao: function (p) { var f = tarefa('clima-filtro'); return { text: 'Climatização · fabricante e modelo ' + SD + '.\n' + (f ? 'Filtro de água salgada: limpeza ' + prazoTxt(f) + ' — e há fluxo fraco na cabine de proa desde 20/09 (diário).\n' : '') + 'Ligar: válvula de fundo aberta e filtro limpo → bomba de água salgada → controle da cabine.\nAlarme de fluxo: quase sempre falta de água salgada (filtro sujo, válvula fechada, bomba desligada).', src: 'Fonte: ' + guia('g_clima') + ' · ' + FT.agenda.replace('Fonte: ', '') + ' · ' + FT.diario.replace('Fonte: ', '') + ' 20/09', actions: act(p, [['Passo a passo', 'f5']]) }; },
    eletronicos: function (p) { var c = tarefa('garmin-cartas'); return { text: [fabMod('eletronicos'), min1(fabMod('audio')), min1(fabMod('vhf'))].join(' · ') + '.\n• Homem ao mar: função MOB do plotter Garmin marca a posição.\n• Piloto automático: em espera antes de manobrar na marina.\n• VHF: canal 16 em escuta; o DSC só identifica o barco com o MMSI programado.' + (c ? '\nCartas desatualizadas (diário 28/08) — atualização ' + prazoTxt(c) + '.' : ''), src: 'Fonte: ' + guia('g_eletronicos') + ' · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['FAQ eletrônicos', 'f3']]) }; },
    audio: function (p) { return { text: 'Áudio Fusion · modelo ' + SD + '.\nParear: fonte Bluetooth no controle Fusion → aparelho visível → selecione o Fusion na lista de Bluetooth do celular. Volume ajustado por zona.', src: 'Fonte: ' + guia('g_eletronicos') + ' §6', actions: act(p, [['FAQ eletrônicos', 'f3']]) }; },
    dessalinizador: function (p) { return { text: SD + ' — dessalinizador não consta na lista de equipamentos.\nSe houver a bordo, envie a foto da etiqueta (modelo e número de série) para catalogar.', src: 'Fonte: Inventário de bordo' + DEMO + ' — equipamento não listado', actions: act(p, [['Enviar foto', A(p, 'home') + '#mode=foto']]) }; },
    eletrico: function (p) { var ser = D.serie24v || [], mn = Math.min.apply(null, ser.map(function (x) { return x.min; })), mx = Math.max.apply(null, ser.map(function (x) { return x.max; })), b = tarefa('baterias'); return { text: 'Banco 24 V: ' + nb(S.bat24, 2) + ' V (' + (G.estado ? 'gerador ' + G.estado : '') + ' · snapshot' + DEMO_ + ' ' + SNAP.quando + ')' + (ser.length ? ' · 7 dias entre ' + nb(mn) + ' e ' + nb(mx) + ' V' : '') + '.\nBanco 12 V: ' + nb(S.bat12, 2) + ' V.' + (b ? '\n' + b.t + ': ' + prazoTxt(b) + ' (' + b.quem + ').' : ''), src: FT.tele + ' · série 24 V · 7 dias · ' + FT.agenda.replace('Fonte: ', ''), actions: act(p, [['Telemetria', 'console']]) }; },
    // epirb e seafire (trava 17): só o procedimento padrão do D.protocolos, com a etiqueta do equipamento; fabricante, modelo, validade e lugar a bordo
    // não aparecem aqui (só em Equipamentos, Leme e Documentos). A 1ª linha é a instrução de segurança; a conversa toda é lida (FALA_INTEIRA).
    epirb: function (p) { return { text: 'EPIRB — ' + min1(EPIRB_PASSOS[0] || '') + '\n' + numerados(EPIRB_PASSOS.slice(1), 2) + '\n' + maius1(NOTA_ETIQUETA) + ' (' + ROTULO + ').\nOnde fica: ' + LOCAL_PLACA + '.', src: FT.proto, actions: act(p, [['Abrir SOS', 'sos']]) }; },
    seafire: function (p) { return { text: 'Seafire — ' + (SEAFIRE_PASSOS[0] || '') + '\n' + numerados(SEAFIRE_PASSOS.slice(1), 2) + '\n' + maius1(NOTA_ETIQUETA) + ' (' + ROTULO + ').\nOnde fica: ' + LOCAL_PLANO + '.', src: FT.proto, actions: act(p, [['Abrir SOS', 'sos']]) }; },
    // Salvatagem (PROMPT §2.3): o texto fixo do D.protocolos, sem número de pessoas, sem lugar (paiol, armário, proa, popa) e sem IA
    salvatagem: function (p) { return { fala: P.salvatagem || '', text: (P.salvatagem || '') + '\n(' + ROTULO + ')', src: FT.proto, actions: act(p, [['Abrir SOS', 'sos'], ['Checklist de saída', 'checklist']]) }; },
    // sos/óleo não gravam nada: pergunta informativa não vira linha permanente. Gravar = atalho DIÁRIO DE BORDO ou "registre posição e hora".
    sos: function (p) { return { text: 'Emergência — abra o SOS. ' + SOS_PASSOS + '\nSeafire e EPIRB: ' + NOTA_ETIQUETA + '.\n' + GRAVAR_AGORA, src: FT.proto, actions: act(p, [['Abrir SOS', 'sos'], ['Registrar no diário', 'diario']]) }; },
    oleo: function (p) { return { text: 'Se a pressão de óleo cair ou o alarme acender, verifique nesta ordem:\n' + OLEO_PASSOS + '\n' + GRAVAR_AGORA, src: 'Fonte: ' + guia('g_motores') + ' §4', actions: act(p, [['Registrar no diário', 'diario'], ['Contatos', 'equipe']]) }; },
    oleoLeitura: function (p) { return { text: 'Motores desligados no snapshot' + DEMO_ + ' de ' + SNAP.quando + '. Pressão do óleo na última leitura com motores ligados ' + (M.hora || SD) + ': ' + (M.oleo ? M.oleo.map(function (x) { return nb(x); }).join('/') : '—') + ' bar · ' + (M.rpm ? M.rpm.join('/') : '—') + ' rpm em neutro · arrefecimento ' + (M.arref ? M.arref.join('/') : '—') + ' °C · sem alarme.\nFaixa normal: manual Volvo Penta — modelo ' + SD + '.\nSe cair abaixo da faixa ou o alarme acender, pergunte “pressão de óleo baixa” para o passo a passo.', src: FT.tele + ' · ' + guia('g_motores'), actions: act(p, [['Telemetria', 'console'], ['Pressão baixa: o que fazer', askHref(p, 'Pressão de óleo baixa: o que verificar primeiro?')]]) }; },
    ancora: function (p) { return { text: 'Sem sensor de âncora na rede NMEA — SEM LEITURA do ferro.\n' + (S.estado || SD) + ' · ' + (S.local || SD) + ' · ' + SNAP.pos + ' · profundidade ' + nb(S.profundidade) + ' m (snapshot' + DEMO_ + ' ' + SNAP.quando + ').\nAlarme de âncora: ative no plotter e defina o raio conforme o cabo lançado e o espaço de giro.', src: 'Fonte: ' + guia('g_eletronicos') + ' §3 · ' + SNAP.fonte, actions: act(p, [['FAQ eletrônicos', 'f3']]) }; },
    // Revisão do C5: todos os guias do D.guias (16, um por equipamento, mais o checklist e o protocolo), sem o prefixo "Guia de bordo — ";
    // sai a lista fixa de 6 com "modelos não informados" e "Seafire e EPIRB: SEM DADOS", que a ficha mandava ao lado do ## Equipamentos.
    manual: function (p) { var g = D.guias || {}, ks = Object.keys(g); return { text: 'Guias de bordo carregados' + DEMO + (ks.length ? ' (' + ks.length + ')' : '') + ' — orientação de bordo, não substituem o manual do fabricante:\n' + (ks.length ? ks.map(function (k) { return '• ' + String(g[k]).replace(/^Guia de bordo — /, ''); }).join('\n') : SD), src: 'Fonte: ' + ((D.drive && D.drive.raiz) || 'Drive') + ' › ' + ((D.drive && D.drive.pastas && D.drive.pastas.manuais) || ''), actions: act(p, [['FAQ de bordo', 'faq']]) }; },
    diarioLer: function (p) {
      var mine = loadDiario(), fonte = diarioFonte();
      var lines = mine.slice(0, 3).map(function (e) { return '• ' + (e.d || '') + ' · ' + (e.sys || 'Diário') + ' — ' + String(e.t || '').slice(0, 110) + ' (app)'; });
      var fixed = fonte.map(function (e) { return '• ' + e.d + ' ' + e.h + ' · ' + e.sys + ' — ' + e.t.slice(0, 110); });
      return { text: 'Últimos registros do diário de bordo (' + (fonte.length + mine.length) + ' no total · ' + pendencias().length + ' pendências abertas):\n' + lines.concat(fixed).slice(0, 4).join('\n') + '\nPara registrar, diga “registre no diário…” ou toque no atalho DIÁRIO DE BORDO.', src: FT.diario + ' + registros do app', actions: act(p, [['Abrir diário', 'diario']]) };
    },
    // Diagnóstico deste aparelho: versões, internet, IA na nuvem e chave (só o tamanho). A tela de chat acrescenta o teste da
    // chave no servidor (CapitaoIA.testar), que não gasta a cota da IA.
    diagnostico: function (p) {
      var AU = window.CapitaoAuth, IA = window.CapitaoIA, app = AU && AU.VERSAO ? AU.VERSAO.v : SD, cli = IA ? (IA.VERSAO || 'antigo, sem versão') : 'não usado nesta tela (fica na tela inicial)';
      var sw = !!(window.navigator && navigator.serviceWorker && navigator.serviceWorker.controller);
      var linhas = ['Diagnóstico do Capitão IA neste aparelho:', '• Versões: app ' + app + ' · cérebro ' + VERSAO + ' · cliente da IA ' + cli];
      if (app !== VERSAO || (IA && cli !== VERSAO)) linhas.push('• ATENÇÃO: arquivos de versões diferentes — feche o app por completo e abra de novo.');
      linhas.push('• Internet: ' + (window.navigator && navigator.onLine === false ? 'sem conexão' : 'conectado') + ' · app offline (service worker): ' + (sw ? 'ativo' : 'não'));
      if (IA && IA.diagnostico) { try { linhas = linhas.concat(IA.diagnostico()); } catch (e) {} }
      // Na voz: o que importa é se a IA está ligada (a tela acrescenta o resultado do teste da chave).
      var linhaIA = linhas.filter(function (l) { return /IA na nuvem:/.test(l); })[0] || '';
      var fala = (linhaIA ? linhaIA.replace(/^•\s*/, '') + '.' : 'Nesta tela a IA na nuvem não é carregada: ela fica na tela inicial.') + (app !== VERSAO || (IA && cli !== VERSAO) ? ' Atenção: arquivos de versões diferentes, feche o app e abra de novo.' : '');
      return { text: linhas.join('\n'), fala: fala, src: 'Fonte: este aparelho' + (IA && IA.testar ? ' · teste da chave no servidor, sem gastar a cota da IA' : ''), actions: act(p, [['Ativar IA na nuvem', IA ? '#ia=ativar' : A(p, 'home') + '#ia=ativar']]) };
    },
    fallback: function (p) { return { text: 'Não encontrei esse dado nas fontes de bordo — telemetria, agenda, documentos, diário e guias de bordo. SEM DADOS.\nPosso registrar como pendência no diário, ou você envia uma foto (etiqueta, tela, nota) para eu identificar.', src: 'Fonte: nenhuma — hierarquia: manual oficial › registro oficial › laudo › diário › foto › nota informal', actions: (BASE ? [BASE] : []).concat(act(p, [['Registrar pendência', 'diario'], ['FAQ de bordo', 'faq']])) }; }
  };

  // ——— Telemetria ao vivo (capitao-telemetria.js) ———
  // Com o coletor conectado e a leitura com menos de 10 min, posição, tanques, tempo, baterias e Seakeeper saem da leitura real;
  // sem isso (padrão de hoje), as respostas continuam com o snapshot do capitao-dados.js.
  function vivo() { var TL = window.CapitaoTelemetria; return TL && TL.atual ? TL.atual() : null; }
  var VIVO = {
    posicao: function (v) { var TL = window.CapitaoTelemetria; return { text: TL.posicao(v) + (v.sog_nos < 0.5 ? ' · parado' : '') + '\nSOG ' + nb(v.sog_nos) + ' nós · proa ' + grau3(v.proa_graus) + ' · ' + nb(v.gps_satelites, 0) + ' satélites · profundidade ' + nb(v.profundidade_m) + ' m · ao vivo ' + TL.hora(v) + '.' }; },
    tanques: function (v) { return { text: 'Tanques agora:\n• água doce ' + nb(v.tanque_agua_pct) + ' %\n• águas cinzas ' + nb(v.tanque_cinzas_pct) + ' %' + (v.tanque_cinzas_pct > 70 ? ' — atenção: programar esgoto' : '') + '\n• águas negras ' + nb(v.tanque_negras_pct) + ' %' + (v.tanque_negras_pct > 70 ? ' — atenção: programar esgoto' : '') + '\n• diesel: ' + SNAP.diesel + ' — ' + SNAP.dieselHora + '.' }; },
    clima: function (v, base) { return { text: 'Agora a bordo (ao vivo ' + window.CapitaoTelemetria.hora(v) + '):\n• vento verdadeiro ' + nb(v.vento_verdadeiro_nos) + ' nós de ' + grau3(v.vento_verdadeiro_angulo) + '\n• barômetro ' + nb(v.pressao_barometrica_hpa, 0) + ' hPa\n• ar ' + nb(v.temp_ar_externo_c) + ' °C · água ' + nb(v.temp_agua_c) + ' °C\n' + base.text.split('\n')[0] }; },
    eletrico: function (v, base) { return { text: 'Baterias agora: banco 24 V ' + nb(v.bateria_0_tensao_v, 2) + ' V · banco 12 V ' + nb(v.bateria_2_tensao_v, 2) + ' V (ao vivo ' + window.CapitaoTelemetria.hora(v) + ').\n' + base.text.split('\n').slice(2).join('\n') }; },
    estabilizador: function (v, base) { return { text: 'Seakeeper agora: ' + (v.seakeeper_ativo ? 'LIGADO' + (typeof v.seakeeper_volante_rpm === 'number' ? ' · volante ' + nb(v.seakeeper_volante_rpm, 0) + ' rpm (' + nb(v.seakeeper_volante_pct, 0) + ' %)' : '') : 'desligado') + ' · ao vivo ' + window.CapitaoTelemetria.hora(v) + '.\n' + base.text.split('\n').slice(1).join('\n') }; }
  };
  Object.keys(VIVO).forEach(function (k) {
    var pronta = ANSWERS[k]; if (!pronta) return;
    ANSWERS[k] = function (p, ctx, q) {
      var base = pronta(p, ctx, q), v = vivo(); if (!v) return base;
      var r = VIVO[k](v, base);
      return { text: r.text, src: 'Fonte: coletor NMEA · ao vivo ' + window.CapitaoTelemetria.hora(v), actions: base.actions };
    };
  });

  // Nomes de outra bomba que não a de porão (rota 'porao', abaixo): o app não tem resposta pronta para elas, e o guia delas está na base.
  // Revisão 7 do C5: "esgoto" saiu. "Bomba de esgoto" também é a de esgotamento do porão em português de bordo, e "a bomba de esgoto não
  // para" é relato de água a bordo: tem de seguir a rota 'porao' (local, sem IA), não ir à nuvem. "Água doce" saiu por ser código morto
  // (a rota 'tanques', mais acima, já pega a pergunta). Quem fica tem guia na base (por si ou por sinônimo: impelidor = impeller/rotor) ou é
  // outra bomba sem relação com o porão (circulação, resfriamento, pressurização): essas vão ao guia ou à IA, e não à resposta do porão.
  var OUTRA_BOMBA = ['salgada', 'rotor', 'impeller', 'impelidor', 'circulacao', 'arrefecimento', 'refrigeracao', 'resfriamento', 'climatiza', 'condicionado', 'gerador', ' onan ',
    'motor', 'seakeeper', 'estabilizador', 'giroscop', 'piloto', 'hidraulic', 'dessaliniz', 'lavagem', 'pressuriz', 'oleo', 'pressao'];
  var EQUIP = ['seakeeper', 'estabilizador', 'climatiza', 'ar condicionado', 'ar-condicionado', 'gerador', ' onan ', 'piloto', 'plotter', 'radar', 'garmin', ' vhf', ' ais ', 'epirb', 'fusion', 'audio', 'dessaliniz', 'bomba', 'porao', 'casco', 'anodo', 'zinco', 'bateria', 'tensao', 'tensoes', 'seafire', 'volvo'];
  // "diagnóstico", "status da IA", "teste da IA", "a IA está ligada?" — a frase inteira, para não pegar pergunta comum.
  var DIAGNOSTICO = /^ (?:(?:fazer |faz |faca |rodar |roda |rode |mostrar |mostra |mostre |me mostra |me mostre |me da |ver )?(?:o |um )?diagnostico(?: da ia| do app| do aplicativo| do capitao| completo)?|(?:qual e |qual )?(?:o )?(?:status|estado) (?:da ia|do app|do aplicativo)|teste da ia|testar a ia|testa a ia|teste a ia|(?:a )?(?:ia|inteligencia artificial)(?: na nuvem)? (?:(?:esta|ta) )?(?:ligada|funcionando|ativa|ativada|on)|(?:a )?(?:ia|inteligencia artificial)(?: na nuvem)? (?:nao )?(?:(?:esta|ta) )?(?:funciona|funcionando|responde|respondendo)) $/;
  // tira "capitão,"/"capitão IA," do começo e "por favor" do fim antes de conferir (jeito comum de falar com o app)
  function semVocativo(q) { return q.replace(/^ (?:ei |oi |ola )?capitao(?: ia)? /, ' ').replace(/ por favor $/, ' '); }
  function route(qRaw) {
    var q = pad(qRaw);
    if (!q.trim()) return 'saudacao';
    if (DIAGNOSTICO.test(semVocativo(q))) return 'diagnostico';
    if (querRegistrar(qRaw, q)) return 'diario';
    if (emergencia(q)) return 'sos';
    var ol = oleo(q);
    if (ol) return ol === 1 ? 'oleo' : 'oleoLeitura';
    // "Situação e vencimento do documento: <nome>" é a pergunta do botão "Perguntar sobre" da G1 (web e app): papelada, seja qual for o nome.
    // Com o doc-epirb (C7, "Certificado do EPIRB…") ela caía na rota `epirb` (a resposta do procedimento e, depois da 1b, a que liga a
    // conversa em emergência por 15 min: um toque na papelada abriria o modo emergência). Vem depois da emergência e do óleo (segurança
    // acima de tudo) e antes de qualquer rota de assunto. Pergunta digitada com "EPIRB" segue a rota do EPIRB.
    if (/^ situacao e vencimento do documento /.test(q)) return 'docsvenc';
    // Salvatagem (PROMPT §2.3): colete, balsa, boia, sinalizador, extintor sem fogo… logo depois da emergência e do óleo, antes das rotas de
    // assunto (epirb, seafire, canal16): resposta fixa, local, sem número de pessoas e sem lugar a bordo
    if (salvatagem(q)) return 'salvatagem';
    if (has(q, ['seguro para sair', 'posso sair', 'da pra sair', 'da para sair', 'seguro sair', 'avalie vento', 'sair hoje', 'seguro navegar', 'seguro para navegar', 'posso navegar', 'podemos sair', 'podemos navegar', 'da pra navegar', 'da para navegar'])) return 'seguro';
    if (has(q, ['telemetria', 'leituras', 'sensores', 'como esta o barco', 'estado do barco', 'status do barco'])) return 'telemetria';
    if (has(q, ['anomalia', 'pendencia', 'problema aberto'])) return 'anomalias';
    if (has(q, ['diario'])) return 'diarioLer';
    if (has(q, [' mare', 'correnteza', 'corrente de mare']) || (has(q, [' corrente']) && !has(q, ['bateria', 'carregador', 'eletric', 'tensao', 'amper', 'alternada', 'continua', 'shore', 'tomada', ' ac ', ' dc ', 'ancora', 'amarra']))) return 'mare';
    if (has(q, [' clima ', 'climatic', 'tempo hoje', ' vento', 'chuva', 'meteor', 'temperatura hoje']) || (has(q, ['previsao']) && !has(q, [' revisao', 'manutenc', 'devoluc', 'entrega', 'chegada']))) return 'clima';
    if (has(q, ['para onde', 'destino', 'passeio', 'onde vamos', 'melhor rota', 'rota para', 'rota ate'])) return 'destinos';
    if (has(q, ['checklist de chegada', 'chegada'])) return 'checklistChegada';
    if (has(q, ['checklist', 'check list', ' saida'])) return 'checklist';
    if (has(q, ['autonomia']) || (has(q, ['alcance']) && !has(q, [' vhf', ' radio', 'radar', ' ais ', 'antena', 'sinal', 'wifi', 'wi-fi', 'bluetooth', 'celular']))) return 'autonomia';
    // "Situação e vencimento do documento: NF de abastecimento…" é documento: a palavra documento/licença/vencimento vence a do combustível
    if (has(q, ['document', 'licenc', 'vencimento']) && has(q, ['consumo', 'l/h', 'litros por hora', 'abastec', 'diesel', 'combustivel', 'nota fiscal', 'nf-e'])) return 'docsvenc';
    if (has(q, ['consumo', 'l/h', 'litros por hora'])) return 'consumo';
    if (has(q, ['abastec', 'diesel', 'combustivel', 'nota fiscal', 'nf-e'])) return 'autonomia';
    if (has(q, ['tanque', 'agua doce', 'cinzas', 'negras'])) return 'tanques';
    // "próxima revisão" sem equipamento = motores; com equipamento, a rota dele (Seakeeper, climatização, gerador…)
    if (has(q, ['horimetro', 'horas de motor', 'horas do motor', 'horas dos motores']) || (has(q, ['proxima revisao']) && !has(q, EQUIP))) return 'horimetros';
    if (has(q, EPIRB_PALAVRAS)) return 'epirb';
    // "supressão" (PROMPT §2.3): é o nome do Seafire nos dados ("sistema fixo de supressão", sem "incêndio", que abriria o SOS). 1b: o sistema
    // fixo que disparou ou descarregou também é do Seafire (o "não abra o acesso ao motor" e o desligamento são os passos de protocolos.seafire);
    // "extintor" saiu daqui para a salvatagem (sem fogo) ou para a SOS (com fogo)
    if (has(q, ['seafire', 'sea fire', 'sea-fire', 'sistema de incendio', 'supressao', 'disparo manual']) || seafireDisparo(q)) return 'seafire';
    // documento/licença antes do rádio: "Licença de estação" é documento, não MAYDAY
    if (has(q, ['document', 'licenc', ' tie ', 'titulo de inscricao', 'seguro da', 'apolice', 'laudo', 'vistoria', 'vencendo', 'certificado', 'garantia'])) return 'docsvenc';
    if (has(q, ['canal 16', ' vhf', ' radio', ' ais ', 'mmsi', ' dsc', 'pan-pan', 'pan pan'])) return 'canal16';
    if (has(q, ['contato', 'telefone', 'equipe', 'oficina', 'quem chamar', 'tecnico de bordo', 'marina da base'])) return 'contatos';
    // "bomba" sozinha é a de porão. Com o nome de outra bomba (água salgada, rotor, impeller, climatização, gerador, motor, estabilizador…) a
    // pergunta segue a rota do outro assunto ou o guia dele: "como trocar o rotor da bomba de água salgada" é o g_motores §7, e a resposta
    // pronta do porão ("Teste de bombas de porão e alarmes… SEM LEITURA") não responde. (Revisão 6 do C5: o trechoServe barra o guia de outro
    // equipamento quando a chave é 'porao'; antes do C5, e na revisão 4, a pergunta ia ao guia certo.)
    if (has(q, ['porao']) || (has(q, ['bomba']) && !has(q, OUTRA_BOMBA))) return 'porao';
    if (has(q, ['gerador', ' onan '])) return 'gerador';
    if (has(q, ['quantas horas'])) return 'horimetros';
    if (has(q, ['estabilizador', 'seakeeper'])) return 'estabilizador';
    if (has(q, ['rotacao', 'rotacoes', ' rpm ', 'giro do motor', 'giro dos motores', 'giro de motor'])) return 'motores';
    if (has(q, [' giro', 'giroscop'])) return 'estabilizador';
    if (has(q, ['climatiza', 'ar condicionado', 'ar-condicionado', 'setpoint', 'cabine'])) return 'climatizacao';
    if (has(q, [' ancora ', 'garrand', 'garrou', 'fundead', 'fundear', ' ferro '])) return 'ancora';
    if (has(q, ['piloto', 'plotter', 'radar', 'garmin', 'eletronic', 'autopilot', ' rota ', ' rotas ', 'standby', 'stby', 'cartas nauticas'])) return 'eletronicos';
    if (has(q, ['audio', 'fusion', ' som ', 'bluetooth', 'musica'])) return 'audio';
    if (has(q, ['dessalinizador', 'watermaker', 'water maker'])) return 'dessalinizador';
    if (has(q, ['manual', 'guia de bordo', 'guias de bordo'])) return 'manual';
    // revisão/inspeção de casco, anodos, zincos → agenda; de bateria/tensões → elétrico — não é revisão dos motores
    if (has(q, [' revisao', 'inspec'])) {
      if (has(q, ['casco', 'anodo', 'zinco'])) return 'manutencao';
      if (has(q, ['bateria', 'tensao', 'tensoes'])) return 'eletrico';
    }
    // "bateria de partida" é o banco de baterias (g_eletrico §1), não a partida do motor (revisão 6 do C5: caía na resposta pronta dos motores)
    if (has(q, ['bateria']) && has(q, ['partida']) && !has(q, ['motor', 'volvo', 'penta'])) return 'eletrico';
    if (has(q, ['motor', 'partida', 'volvo', 'penta', ' revisao'])) return 'motores';
    if (has(q, ['manutenc', 'vence', 'atrasad', 'agenda', 'tarefa'])) return 'manutencao';
    if (has(q, ['bateria', '24 v', '24v', '12 v', '12v', 'eletric', 'tensao', 'voltagem', 'carregador'])) return 'eletrico';
    if (has(q, ['posicao', 'onde estou', 'onde esta o barco', 'coordenada', ' gps', ' proa', 'velocidade'])) return 'posicao';
    // "Rajada" é a previsão do dia só em pergunta de previsão ("vai ter rajada hoje?", "como estão as rajadas?", "previsão de rajada"),
    // e depois das rotas de equipamento. "Hoje"/"agora" sozinhos não bastam: relato ("pegamos uma rajada agora e o barco adernou",
    // "a rajada de hoje arrancou o toldo", "a âncora garrou com a rajada"), pessoa em risco e limite do barco seguem o equipamento ou a IA.
    if (has(q, [' rajada']) && (RAJADA_SO.test(q) || has(q, ['previs', 'vai ter rajada', 'tem rajada', ' ha rajada', 'havera rajada', 'como estao as rajadas', 'como esta a rajada', 'como vao estar as rajadas']))
      && !has(q, RAJADA_RELATO)) return 'clima';
    if (has(q, [' oi ', ' ola ', 'bom dia', 'boa tarde', 'boa noite', 'ajuda', 'o que voce faz', 'quem e voce']) || SOBRE.test(q)) return 'saudacao';
    return 'fallback';
  }
  // Pergunta sobre o próprio Capitão IA, com os jeitos comuns de digitar e falar: "Oque você faz?", "o que vc sabe", "quem é vc",
  // "como você funciona", "pra que serve".
  var SOBRE = / (?:o ?que|oq|q) (?:e que )?(?:voce|vc|tu) (?:faz|sabe|pode|consegue|responde)| quem (?:e|eh) (?:voce|vc|tu) | quem (?:voce|vc) e | como (?:voce|vc) funciona| como (?:funciona|uso|usar) (?:o |este |esse )?(?:app|aplicativo|capitao)| (?:para|pra) que (?:voce |vc )?serve/;
  // Só a palavra: "rajada?", "e as rajadas?", "rajada máxima".
  var RAJADA_SO = /^ (?:e )?(?:as? )?rajadas?(?: maximas?)? $/;
  // Relato, pessoa em risco ou limite do barco junto de "rajada": nunca a previsão do dia.
  var RAJADA_RELATO = ['aguent', 'suport', 'resist', 'limite', 'derrub', 'quebr', 'rasg', 'arrebent', 'arranc', 'voou', 'apag', 'deslig', 'virou',
    'adern', 'caiu', 'feri', 'machuc', 'pegamos', 'pegou', 'bateu', 'jogou', 'garr', 'alguem', 'tripulante', 'pessoa', 'o que faco', 'entrando'];

  var CANON = {}; ALL.forEach(function (x) { CANON[x.id] = norm(x.q).trim(); });

  // ——— Base de conhecimento de bordo (base-conhecimento.json) ———
  // Trechos dos guias de bordo (hoje, DEMO). Quando a resposta pronta não tem o dado, o chat e a voz buscam aqui
  // (BM25 com sinônimos PT/EN) e respondem com o trecho e a fonte. Carrega em segundo plano; funciona offline (cache do SW).
  var KB = { docs: null, carregando: false, df: {}, media: 1, nomes: {} };
  var PARADAS = ' a o e as os um uma uns umas de da do das dos em no na nos nas por para pra com sem se que qual quais quando como onde quanto quantos quantas e ou ao aos a is the of to and in on for with is are be it this that from at by an or eu voce vc me meu minha tem ter tenho ha esta estao fica ser sao era foi faz fazer posso pode sobre mais muito barco embarcacao capitao demo nao isso aqui registre registra registrar anote anota anotar grave gravar diario '.split(' ').reduce(function (m, w) { if (w) m[w] = 1; return m; }, {});
  var SINONIMOS = {
    gerador: ['onan', 'generator', 'genset'], estabilizador: ['seakeeper', 'gyro', 'giroscopio', 'stabilizer', 'volante'], giroscopio: ['seakeeper', 'gyro', 'estabilizador'],
    piloto: ['autopilot', 'automatico'], automatico: ['autopilot', 'piloto'], oleo: ['oil', 'lubrificante'], filtro: ['filter'], combustivel: ['fuel', 'diesel'], diesel: ['fuel', 'combustivel'],
    motor: ['engine', 'volvo', 'penta'], motores: ['engine', 'volvo', 'penta'], rotor: ['impeller'], impelidor: ['impeller', 'rotor'], impeller: ['rotor'], bomba: ['pump'], porao: ['bilge'],
    ar: ['climatizacao', 'condicionado'], climatizacao: ['condicionado', 'cabine'], condicionado: ['climatizacao'], incendio: ['fire', 'seafire'], fogo: ['fire', 'seafire'],
    bateria: ['battery', 'baterias'], baterias: ['battery', 'bateria'], ancora: ['anchor', 'ferro', 'fundear'], fundear: ['ancora'], ferro: ['ancora'],
    falha: ['fault', 'erro', 'alarme'], erro: ['fault', 'falha', 'alarme'], alarme: ['alarm', 'falha', 'codigo'], codigo: ['code', 'alarme'], temperatura: ['temperature'], pressao: ['pressure'],
    arrefecimento: ['coolant', 'refrigerante'], refrigerante: ['coolant', 'arrefecimento'], agua: ['water'], zinco: ['anode', 'anodo'], anodo: ['anode', 'zinco'],
    radar: ['garmin'], plotter: ['garmin', 'chartplotter'], som: ['fusion', 'audio'], audio: ['fusion', 'som'], radio: ['vhf'], vhf: ['radio', 'dsc'], ligar: ['partida', 'start', 'ligue'],
    partida: ['ligar', 'start'], desligar: ['parada', 'stop', 'parar', 'desligue'], manutencao: ['maintenance', 'revisao', 'agenda'], revisao: ['manutencao', 'service'], limpeza: ['limpe', 'cleaning'],
    capacidade: ['capacity', 'litros', 'volume'], superaquecer: ['temperatura', 'overheat', 'arrefecimento'], superaquecimento: ['temperatura', 'overheat', 'arrefecimento'], esquentando: ['temperatura', 'arrefecimento'],
    parear: ['emparelhar', 'pairing', 'conectar', 'bluetooth'], emparelhar: ['parear', 'bluetooth'], alarm: ['alarme'], lubrificante: ['oil', 'oleo'], tanque: ['tank'], mob: ['homem', 'mar'], homem: ['mob'],
    // Revisão 4 do C5: "quando trocar o óleo do motor?" achava só o §4 (pressão de óleo baixa) e não a agenda "Troca de óleo e filtros" (§7);
    // "botão distress" é o DSC do rádio e "o sistema descarregou" é o §3 "Depois da descarga" (a identidade do trecho de segurança,
    // abaixo, é o título dele). As chaves são a raiz() da palavra: distres = raiz('distress').
    trocar: ['troca', 'substituir'], troca: ['trocar'], distres: ['dsc'], descarregou: ['descarga'],
    // 1b (PROMPT §2.3): "baliza" é o EPIRB e "testar a baliza" é o teste dele (o §2 do g_epirb traz «teste» e «baliza»)
    baliza: ['epirb', 'radiobaliza']
  };
  // "testar" é "teste" só junto de baliza/EPIRB (o g_epirb §2 traz «teste» e «baliza»). Em geral não: "como testar as bombas de porão" voltava do g_porao §3
  // à resposta pronta do porão, local, e passou a ir à IA (revisão da 1b).
  var SINONIMOS_BALIZA = { testar: ['teste', 'autoteste'] };
  var BALIZA_RAIZES = {}; ['baliza', 'epirb', 'radiobaliza'].forEach(function (w) { BALIZA_RAIZES[raiz(w)] = 1; });
  function raiz(w) { if (/^\d/.test(w)) return w; w = w.replace(/coes$/, 'cao').replace(/oes$/, 'ao').replace(/aes$/, 'ao'); return w.length > 4 ? w.replace(/(es|s)$/, '') : w; }
  // "ar" (2 letras) é palavra da busca ("como ligar o ar" é a climatização; o SINONIMOS.ar existia, mas o filtro de tamanho o tirava);
  // as demais palavras de até 2 letras seguem fora.
  // "ar condicionado" vale pela palavra "condicionado" (sinônimo de climatização): o "ar" sozinho puxaria o §4 "Fluxo de ar fraco".
  function tokens(t) {
    return norm(t).replace(/\bar[\s-]+condicionado\b/g, 'condicionado').replace(/[^a-z0-9]+/g, ' ').split(' ').filter(function (w) { return w && !PARADAS[w] && (w.length > 2 || w === 'ar' || /\d/.test(w)); }).map(raiz);
  }
  // Frases fixas que ficam no texto do trecho mas não entram no índice (revisão 3 do C5): o rótulo do procedimento padrão e a
  // nota da etiqueta (CONTRATO §1.5), no fim de todo trecho de g_seafire, g_epirb, Salvatagem e protocolo, e o "do equipamento"
  // depois de "etiqueta" (o equipamento do trecho já está na fonte). Repetidas em trechos curtos, punham o g_epirb §4 no topo de
  // "quais equipamentos tem a bordo?" e de "modelo dos equipamentos", e o trecho de segurança do topo barrava a IA.
  // (NOTA_ETIQUETA vem do D.protocolos, acima: o SOS carrega este arquivo e não lê o D.equipamentos; o gerador prende as duas notas iguais.)
  var FORA_DO_INDICE = [ROTULO, NOTA_ETIQUETA].map(function (f) { return norm(f); });
  function indexavel(t) {
    t = norm(t);
    FORA_DO_INDICE.forEach(function (f) { t = t.split(f).join(' '); });
    return t.replace(/\betiqueta do equipamento\b/g, 'etiqueta');
  }
  // Identidade do trecho de segurança (revisão 4 do C5): as palavras da fonte, do equipamento e do título da seção, menos as que só
  // dizem "guia", "protocolo", "sistema" ou "depois" ("sistema fixo" pesa pelo "fixo"; "como ligar o sistema de ventilação" não é o
  // Seafire). O trecho de segurança (g_seafire, g_epirb, protocolo, §4 dos motores e do porão…) só entra na busca se a pergunta nomeia
  // o assunto dele. Sem isso, os passos dele (desligue motores e gerador, corte a ventilação, não abra o acesso ao motor, depois da
  // descarga) casavam perguntas comuns ("como desligar a ventilação", "como religar o gerador depois de desligar"), mostravam o
  // procedimento de incêndio e, por ser de segurança, barravam a IA (pedeIA).
  // Palavras de acionamento (revisão 5 do C5): o trecho do protocolo que descreve uma situação (homem ao mar, pane) também é nomeado pelas
  // palavras com que a pessoa conta essa situação e que não estão no título ("caiu", "sem governo"); o gerador as põe em `ident`.
  // Revisão 6 do C5: "caiu" é o uso comum para disjuntor, energia e sinal ("o plotter caiu, como resolver" devolvia o protocolo de homem
  // ao mar, sem IA). O `ident` que conta uma pessoa em risco só vale junto de uma palavra de pessoa (`identCom`: pessoa, quem, alguém,
  // homem, tripulante…); sozinho, "caiu" não nomeia o trecho.
  // "manual" (título "Disparo manual") e "mar" ("Homem ao mar") são palavras comuns demais para nomear: "onde fica o manual do motor"
  // devolvia o disparo manual do Seafire e "tem vista para o mar?", o homem ao mar. "disparo" e "homem" continuam nomeando; "pessoa ao
  // mar" é o `ident` do protocolo com `identCom`.
  // Revisão 7 do C5: a identidade depende do guia. Num guia TODO de segurança (g_seafire, g_epirb, protocolo: todo trecho da fonte tem
  // `seguranca`) o equipamento é o assunto, e fonte, equip e título nomeiam o trecho. Num guia MISTO (o §4 dos motores e do porão, o §1 e o
  // §5 dos eletrônicos, o §2 do AIS, o checklist de saída) a seção de segurança é uma entre várias: o nome do equipamento não a nomeia, só o
  // título dela, sem o nome do equipamento. Antes, "onde fica o plotter", "como ver o radar" e "como ver o garmin" (o equip do g_eletronicos
  // traz Garmin, Fusion e Icom) devolviam o §1 "Plotter: homem ao mar", e "onde fica o motor", o §4 da pressão de óleo, com `seguranca`:
  // trecho de segurança no topo barra a IA, e a fala lê o trecho inteiro.
  var IDENT_GENERICAS = {}; tokens('guia bordo depois caso antes sistema procedimento padrao confirmar protocolo emergencia manual mar').forEach(function (w) { IDENT_GENERICAS[w] = 1; });
  function carregaBase() {
    if (KB.docs || KB.carregando || !window.fetch) return;
    KB.carregando = true;
    fetch('./base-conhecimento.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
      var lista = j && j.trechos; if (!lista || !lista.length) return;
      var soma = 0, df = {}, nomes = {}, todoSeguro = {};
      lista.forEach(function (d) { if (todoSeguro[d.fonte] !== 0) todoSeguro[d.fonte] = d.seguranca ? 1 : 0; });
      lista.forEach(function (d) {
        var sec = d.secao || '', tf = {}, tk = tokens(sec + ' ' + sec + ' ' + sec + ' ' + indexavel(d.texto) + ' ' + (d.fonte || '') + ' ' + (d.equip || ''));
        d._lista = /invent[aá]rio|cat[aá]logo|[íi]ndice/i.test(d.fonte || '');
        d._eq = {}; tokens((d.fonte || '') + ' ' + (d.equip || '')).forEach(function (w) { if (!IDENT_GENERICAS[w] && !/^\d/.test(w)) { d._eq[w] = 1; nomes[w] = 1; } });
        d._id = {};
        if (todoSeguro[d.fonte]) tokens((d.fonte || '') + ' ' + (d.equip || '') + ' ' + sec).forEach(function (w) { if (!IDENT_GENERICAS[w]) d._id[w] = 1; });
        else tokens(sec).forEach(function (w) { if (!IDENT_GENERICAS[w] && !d._eq[w]) d._id[w] = 1; });
        // `ident` = palavras de acionamento (valem mesmo as genéricas, como "mar" em "pessoa ao mar"); com `identCom`, só junto de uma delas na pergunta
        d._ia = {}; tokens(d.ident || '').forEach(function (w) { d._ia[w] = 1; });
        d._ic = null; if (d.identCom) { d._ic = {}; tokens(d.identCom).forEach(function (w) { d._ic[w] = 1; }); }
        d._en = (' ' + d.texto.toLowerCase() + ' ').split(/\b(?:the|and|with|to|of|is|are|your|from)\b/).length > 6;
        tk.forEach(function (w) { tf[w] = (tf[w] || 0) + 1; });
        Object.keys(tf).forEach(function (w) { df[w] = (df[w] || 0) + 1; });
        d._tf = tf; d._n = tk.length; soma += tk.length;
      });
      KB.df = df; KB.media = soma / lista.length; KB.nomes = nomes; KB.docs = lista;
    }).catch(function () {}).then(function () { KB.carregando = false; });
  }
  // Devolve até n trechos { d, nota } ou [] se nada for relevante o bastante.
  var PROCEDIMENTO = /\b(como|o que fazer|procedimento|passo|trocar|troca|ligar|desligar|parear|alarme|falha|codigo|superaquec\w*|oleo|capacidade)\b/;
  function buscaBase(q, n) {
    if (!KB.docs) { carregaBase(); return []; }
    var qs = tokens(q).filter(function (w, k, a) { return a.indexOf(w) === k; });
    if (!qs.length) return [];
    // cada palavra da pergunta vira um grupo (ela + sinônimos); o trecho precisa cobrir a maioria dos grupos
    var daBaliza = qs.some(function (w) { return BALIZA_RAIZES[w]; });
    var grupos = qs.map(function (w) { var g = {}; g[w] = 1; (SINONIMOS[w] || (daBaliza && SINONIMOS_BALIZA[w]) || []).forEach(function (x) { x = raiz(x); if (!g[x]) g[x] = 0.6; }); return g; });
    var N = KB.docs.length, k1 = 1.2, b = 0.75, res = [], proc = PROCEDIMENTO.test(' ' + norm(q) + ' ');
    KB.docs.forEach(function (d) {
      var nota = 0, bateu = 0, secao = d._sec || (d._sec = ' ' + tokens(d.secao || '').join(' ') + ' '), naSecao = 0, nomeia = !d.seguranca, aciona = false;
      grupos.forEach(function (g) {
        var melhor = 0;
        for (var w in g) {
          var f = d._tf[w]; if (!f) continue;
          var idf = Math.log(1 + (N - KB.df[w] + 0.5) / (KB.df[w] + 0.5));
          melhor = Math.max(melhor, g[w] * idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * d._n / KB.media)));
          if (secao.indexOf(' ' + w + ' ') !== -1) naSecao++;
          if (d._id[w]) nomeia = true;
          if (d._ia[w]) aciona = true;
        }
        if (melhor > 0) { bateu++; nota += melhor; }
      });
      // palavra de acionamento ("caiu", "pane"): nomeia o trecho; se ele pede uma palavra de pessoa, a pergunta tem de trazê-la
      if (aciona && (!d._ic || qs.some(function (w) { return d._ic[w]; }))) nomeia = true;
      if (!nomeia) return; // trecho de segurança que a pergunta não nomeia (identidade, acima)
      if (naSecao >= grupos.length) nota *= 1.6; // o título da seção cobre a pergunta inteira
      if (d._lista && proc) nota *= 0.45;
      if (nota > 0 && bateu >= Math.min(2, grupos.length) && bateu >= Math.ceil(grupos.length * 0.6)) res.push({ d: d, nota: nota });
    });
    res.sort(function (x, y) { return y.nota - x.nota; });
    return res.slice(0, n || 3);
  }
  function citaFonte(d) { return d.fonte + (d.pag ? ', p. ' + d.pag : d.secao ? ' · §' + d.secao : ''); }
  function trechoCurto(t, max) {
    t = String(t || '').replace(/\s+/g, ' ').trim(); max = max || 480;
    if (t.length <= max) return t;
    var c = t.slice(0, max), m = c.match(/^[\s\S]*[.!?;](?=\s)/);
    return (m && m[0].length > max * 0.5 ? m[0] : c.slice(0, c.lastIndexOf(' ')) + '…');
  }
  var MAX_SEGURANCA = 1500;
  var GENERICAS = { gerador: 1, motores: 1, audio: 1, estabilizador: 1, eletronicos: 1, climatizacao: 1, dessalinizador: 1, eletrico: 1, porao: 1, ancora: 1, manual: 1, clima: 0 };
  var ESPECIFICA = /\b(como|trocar|troca|substitu\w*|parear|pareamento|conectar|codigo|codigos|alarme|alarmes|erro|falha|falhas|defeito|superaquec\w*|oleo|filtro|impeller|impelidor|rotor|capacidade|litros|pressao|temperatura|onde fica|localiza\w*|procedimento|passo|reset\w*|calibr\w*|configur\w*|limp\w*|intervalo|torque|especifica\w*|viscosidade|bluetooth|dsc|mob|zinco|anodo|fusivel|disjuntor|fluxo)\b/;
  // Resposta pronta de equipamento × trecho do guia (revisão 5 do C5). A resposta pronta (GENERICAS) só cede ao trecho do topo quando ele é
  // do assunto perguntado. Com os 91 trechos, "como ligar o plotter" trazia o "Ligar e transmitir" do radar ("ligue o radar pelo plotter"),
  // "como ligar o sistema de som" o §1 dos bancos de bateria ("sistema" e "ligar", por sinônimo de "partida") e "como funciona o sistema
  // elétrico" o §3 de verificação. Três condições:
  //  (1) o guia é um dos do equipamento da resposta (FAMILIA; sem entrada, qualquer guia);
  //  (2) se a pergunta diz o nome de algum equipamento (palavra exata da fonte ou do equip de algum trecho: "plotter" não vale por
  //      "garmin"), o trecho é de um equipamento que ela nomeia (na fonte, no equip ou no título da seção);
  //  (3) a pergunta traz algo além do nome do equipamento: uma palavra, ou sinônimo, que está no título ou no texto ("funciona" só vale
  //      se o título do trecho for o funcionamento).
  // Vale o 1º dos 3 trechos da busca que passa nas três; nenhum passa, fica a resposta pronta, como antes do C5. O trecho de segurança que
  // abre a busca (a pergunta o nomeia) não passa por aqui, e a pergunta sem resposta pronta (fallback) também não.
  // (a âncora também é do g_eletronicos: o alarme de âncora está no plotter, §3)
  var FAMILIA = { gerador: ['g_gerador'], motores: ['g_motores'], estabilizador: ['g_seakeeper'], climatizacao: ['g_clima'], dessalinizador: ['g_dessalinizador'],
    eletrico: ['g_eletrico'], porao: ['g_porao'], ancora: ['g_ancora', 'g_eletronicos'], audio: ['g_eletronicos'], eletronicos: ['g_eletronicos', 'g_piloto', 'g_radar', 'g_ais'] };
  var SEM_ASSUNTO = {}; tokens('funciona funcionamento').forEach(function (w) { SEM_ASSUNTO[w] = 1; });
  function trechoServe(key, q, d) {
    var fam = FAMILIA[key];
    if (fam && !fam.some(function (g) { return d.fonte === guia(g); })) return false;
    var ws = tokens(q).filter(function (w, k, a) { return a.indexOf(w) === k && !IDENT_GENERICAS[w]; });
    var nomes = ws.filter(function (w) { return KB.nomes[w]; });
    var secao = d._sec || (d._sec = ' ' + tokens(d.secao || '').join(' ') + ' '); // o título também nomeia ("Piloto automático" no g_eletronicos §2)
    if (nomes.length && !nomes.some(function (w) { return d._eq[w] || secao.indexOf(' ' + w + ' ') !== -1; })) return false;
    // palavra que é nome do equipamento do trecho (ela ou um sinônimo dela está na fonte ou no equip: "ar" e "condicionado" são a
    // "climatização"; "som" é o "Fusion") não conta como assunto
    var nome = function (w) { return d._eq[w] || (SINONIMOS[w] || []).some(function (x) { return d._eq[raiz(x)]; }); };
    // "funciona" só conta como assunto se o título do trecho for o funcionamento ("Funcionamento" do porão); as outras, no título ou no texto
    return ws.some(function (w) {
      if (nome(w)) return false;
      if (SEM_ASSUNTO[w]) return secao.indexOf(' funcionamento ') !== -1;
      return d._tf[w] || (SINONIMOS[w] || []).some(function (x) { return d._tf[raiz(x)]; });
    });
  }
  function respostaBase(q, p, key) {
    var hits = buscaBase(q, 3); if (!hits.length) return null;
    // com resposta pronta (key), vale o 1º dos 3 trechos que serve ao assunto; o de segurança do topo (a pergunta o nomeia) passa direto
    var topo = !key || hits[0].d.seguranca ? hits[0] : hits.filter(function (x) { return trechoServe(key, q, x.d); })[0];
    if (!topo) return null;
    var h = topo.d, outros = hits.filter(function (x) { return x !== topo && (x.d.fonte !== h.fonte || x.d.secao !== h.secao); });
    // Trecho de segurança sai inteiro, com o rótulo do procedimento padrão e a nota da etiqueta no fim (CONTRATO §1.5): o corte de
    // 480 letras tirava os dois do §1 e do protocolo do Seafire (560) e a nota do §3 (492). O gerador limita esses trechos a 800.
    var text = trechoCurto(h.texto, h.seguranca ? MAX_SEGURANCA : 480) + (outros.length ? '\nVeja também: ' + outros.map(function (x) { return citaFonte(x.d); }).join(' · ') : '');
    // seguranca: o trecho do topo é de segurança (EPIRB, Seafire, salvatagem, protocolo…; o gerador marca) — o pedeIA não chama a IA
    return { text: text, src: 'Fonte: ' + citaFonte(h) + ' — base de conhecimento de bordo' + (h.equip ? ' · ' + h.equip : ''), actions: act(p, [['FAQ de bordo', 'faq']]), ref: citaFonte(h), ingles: !!h._en, seguranca: !!h.seguranca };
  }
  if (window.requestIdleCallback) requestIdleCallback(carregaBase, { timeout: 4000 }); else setTimeout(carregaBase, 1500);

  function answer(q, ctx) {
    ctx = ctx || {};
    var p = ctx.platform || 'web';
    var key = null;
    if (ctx.id && ANSWERS[ctx.id] && (!String(q || '').trim() || norm(q).trim() === CANON[ctx.id])) key = ctx.id;
    if (!key) key = route(q);
    if (!ANSWERS[key]) key = 'fallback';
    var a;
    try { a = ANSWERS[key](p, ctx, String(q || '').trim()); } catch (e) { key = 'fallback'; a = ANSWERS.fallback(p, ctx); }
    // Sem resposta pronta, ou pergunta específica sobre um equipamento (como, código, óleo, alarme, onde fica…): o trecho do guia vale mais que o resumo genérico.
    if (key === 'fallback' || (GENERICAS[key] && ESPECIFICA.test(' ' + norm(q) + ' '))) { var kb = null; try { kb = respostaBase(q, p, key === 'fallback' ? null : key); } catch (e) {} if (kb) { a = kb; key = 'base'; } }
    a.key = key;
    return a;
  }

  // ——— IA na nuvem (capitao-ia.js) ———
  // Quando a tela chama a IA: sem resposta pronta (SEM DADOS), trecho do guia (a IA responde a partir dele) ou pergunta sobre o
  // próprio app que vai além do cumprimento. Emergência, óleo, registro no diário e respostas prontas ficam 100% no aparelho:
  // rápidas, offline e com a fonte. "Oi", "bom dia, capitão" também — a saudação pronta basta e não gasta a cota.
  var SO_OI = /^(?: (?:oi|ola|opa|e ai|eai|hey|hello|hi|alo|bom dia|boa tarde|boa noite|tudo bem|tudo bom|td bem|beleza|capitao|ia))+ $/;
  // Trecho de segurança no topo (a.seguranca, do respostaBase) nunca vai à IA: fica o trecho local, com a fonte (PROMPT §2.3).
  // Revisão do C5: vale qualquer que seja a chave. A tela manda junto o buscaBase(q, 3), e uma saudação com assunto ("como você me
  // ajuda com o teste da baliza?") levava o g_epirb §2 no topo; o respostaBase só marca a chave base.
  function pedeIA(a, q) {
    var k = a && a.key;
    if (a && a.seguranca) return false;
    if (k !== 'fallback' && k !== 'base' && k !== 'saudacao') return false;
    var topo = String(q || '').trim() ? buscaBase(q, 1)[0] : null;
    if (topo && topo.d.seguranca) return false;
    if (k === 'fallback' || k === 'base') return true;
    return !!String(q || '').trim() && !SO_OI.test(pad(q));
  }
  // O que o app faz, para a IA responder "o que você faz?", "como registro?", "onde vejo os documentos?".
  var SOBRE_APP = [
    'O Capitão IA é o assistente de bordo desta embarcação: um app no celular e no computador, em português, que responde sempre com a fonte.',
    'Responde sobre: telemetria (snapshot do coletor NMEA; ao vivo quando o coletor estiver ligado), manutenção e agenda (atrasadas, próximas, horímetros), documentos e vencimentos, abastecimento, consumo e autonomia, diário de bordo (ler e registrar), equipe e contatos, clima e maré na posição de referência (Open-Meteo), passo a passo dos equipamentos (gerador Onan, estabilizador Seakeeper, climatização, eletrônicos Garmin, áudio Fusion, rádios VHF Icom, motores Volvo Penta) e checklist de saída e chegada.',
    'Jeitos de perguntar: digitar; VOZ→TEXTO (a fala vira texto); CONVERSA (voz contínua, sem tocar na tela: toque no núcleo para interromper, ENCERRAR para sair); FOTO e VÍDEO (não saem do aparelho e entram no diário como A CONFIRMAR); atalhos de um toque na home, editáveis em EDITAR ATALHOS.',
    'Registrar no diário: dizer ou digitar "registre no diário …" (o chat só grava com esse comando; o diário só cresce, nada se apaga). O atalho DIÁRIO DE BORDO grava o resumo da telemetria.',
    'Emergência: botão SOS em todas as telas — abre sem login e sem internet; VHF canal 16.',
    'Telas: Console (telemetria), Carta (gestão), Leme (manutenção), Documentos, Abastecimento, Diário, Equipe, FAQ de bordo por equipamento, SOS.',
    'Regra da casa: nada inventado. Cada número vem com a fonte; sem fonte = SEM DADOS; sensor ausente = SEM LEITURA; foto ou nota = A CONFERIR / A CONFIRMAR.'
  ];
  function agoraBR() {
    try { return new Intl.DateTimeFormat('pt-BR', { timeZone: E.fuso || 'America/Sao_Paulo', weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date()) + ' (horário de Brasília)'; } catch (e) { var n = now(); return n.d + ' ' + n.t; }
  }
  // Coordenadas não saem do aparelho (posição do barco só depois do login no servidor).
  function semCoord(s) { return String(s || '').replace(/\d{1,3}\s?°\s?\d{1,2}(?:,\d+)?\s?['′]\s?[NSLOEW]\s*\d{1,3}\s?°\s?\d{1,2}(?:,\d+)?\s?['′]\s?[NSLOEW]/g, '(coordenadas só na tela do app)'); }
  // Ficha de bordo para a IA na nuvem: o que o app sabe agora, bloco a bloco, com a fonte de cada um — os mesmos textos das
  // respostas prontas, então a IA e a tela dizem os mesmos números. Sem coordenadas e sem telefones. ~9 mil letras
  // (o proxy aceita até 12 mil). ficha(p, q, a): pergunta pura sobre o próprio app ("o que você faz?") leva só a ficha
  // RESUMIDA (agora, sobre o app, embarcação, equipamentos — ~3 mil letras). Com assunto ("o que você sabe sobre o
  // seguro?") ou trecho do guia ("quando foi a última troca de óleo?"), a completa: a resumida tirava o dado pedido (1.0.7).
  var ASSUNTO = / (?:sobre|de|do|da|dos|das|no|na|com|quando|qual|quais|quanto|onde) (?!(?:voce|vc|app|aplicativo|capitao|ia|mim|tudo|bordo) )[a-z]/;
  function fichaResumida(q, a) { var s = pad(q); return !!a && a.key === 'saudacao' && SOBRE.test(s) && !ASSUNTO.test(s.replace(SOBRE, ' ')); }
  function ficha(p, q, a) {
    p = p || 'app';
    var out = [];
    var bloco = function (titulo, f) { try { var a = f(); if (a && a.text) out.push('## ' + titulo + '\n' + semCoord(a.text) + (a.src ? '\n(' + semCoord(a.src) + ')' : '')); } catch (e) {} };
    out.push('## Agora\n' + agoraBR() + ' · usuário: ' + quem() + (D.demo ? '\n' + (D.selo || 'DEMO') + ': ' + (D.aviso || '') : ''));
    out.push('## Sobre o app\n' + SOBRE_APP.join('\n'));
    out.push('## Embarcação\n' + (E.nome || SD) + ' · fabricante e modelo ' + (E.modelo || SD) + ' · registro ' + (E.registro || SD) + ' · proprietário ' + (E.proprietario || SD) + ' · base ' + (E.base || SD) + ' · ' + mmsiNum() + ' (cadastro do app) · indicativo: ' + INDICATIVO + '\n(Fonte: ' + (E.fonte || SD) + ')');
    out.push('## Equipamentos\n' + (D.equipamentos || []).map(function (e) { if (e.seguranca) return '• ' + e.nome + ': ' + (e.nota || NOTA_ETIQUETA); return '• ' + e.nome + ': ' + (e.fabricante || 'fabricante ' + SD) + ' · modelo ' + (e.modelo || SD) + (e.qtd && e.qtd !== SD ? ' · ' + e.qtd + (e.lados ? ' (' + e.lados + ')' : '') : ''); }).join('\n') + '\n(Fonte: Inventário de bordo' + DEMO + (D.equipNota ? ' · ' + D.equipNota : '') + ')');
    if (fichaResumida(q, a)) {
      out.push('## Ficha resumida\nEsta pergunta veio só com o resumo acima (sobre o app e o barco) e, se houver, os trechos do guia. Telemetria, manutenção, documentos, diário e equipe não vieram: para um dado desses, diga que o app mostra ao perguntar pelo assunto (ex.: "telemetria", "próximas manutenções").');
      return out.join('\n\n');
    }
    bloco('Telemetria', function () { return ANSWERS.telemetria(p); });
    bloco('Manutenção', function () { return ANSWERS.manutencao(p); });
    bloco('Horímetros', function () { return ANSWERS.horimetros(p); });
    bloco('Autonomia e consumo', function () {
      var a = ANSWERS.autonomia(p), ab = D.abastecimentos || [];
      return { text: a.text + (ab.length ? '\nAbastecimentos registrados: ' + ab.map(function (x) { return x.d + ' · ' + mil(x.litros) + ' L de ' + (x.combustivel || 'diesel') + ' · ' + (x.local || SD) + (x.st ? ' · ' + x.st : ''); }).join(' | ') + '.\nRegra: ' + (D.regraAbast || SD) + '.' : ''), src: a.src };
    });
    bloco('Documentos', function () { return ANSWERS.docsvenc(p); });
    bloco('Pendências', function () { return ANSWERS.anomalias(p); });
    bloco('Diário de bordo', function () { return ANSWERS.diarioLer(p); });
    bloco('Equipe e contatos', function () { return ANSWERS.contatos(p); });
    bloco('Clima e maré', function () {
      var pv = previsao(), m = mareTexto();
      return { text: (pv ? 'Previsão de hoje em Balneário Camboriú (' + pv.fonte + '): ' + pv.temp + ' · ' + pv.vento + '. O app não tem limite de vento para dizer se é seguro sair.' : 'Previsão do dia: ' + SD + ' (sem leitura de hoje neste aparelho).') + '\n' + (m ? 'Maré agora ' + m.agora + ' em relação ao nível médio do mar · próximas horas: ' + m.prox.join(' · ') + ' — modelo, não a tábua oficial da Marinha (DHN).' : 'Maré: ' + SD + ' agora (Open-Meteo Marine sem resposta).') + '\n' + (pv ? 'Previsão do mar (ondas): ' : 'Previsão de vento e mar para navegar: ') + SD + ' no app — meteorologia marinha da Marinha do Brasil.', src: 'Fonte: ' + (pv ? 'previsão ' + pv.fonte : 'previsão Open-Meteo: sem leitura de hoje neste aparelho') + ' · maré Open-Meteo Marine · na posição de referência · vento, pressão e temperaturas de bordo no bloco Telemetria' };
    });
    bloco('Guias de bordo', function () { return ANSWERS.manual(p); });
    out.push('## Emergência\nAbrir o SOS do app. ' + SOS_FICHA + '\n(' + FT.proto + ')');
    return out.join('\n\n');
  }

  // Anexos (foto/vídeo): não saem do aparelho — viram linha A CONFIRMAR no diário.
  function answerAttachment(kind, file, ctx) {
    var p = (ctx && ctx.platform) || 'web';
    var name = file && file.name ? file.name : (kind === 'video' ? 'vídeo' : 'foto');
    var kb = file && file.size ? Math.round(file.size / 1024) + ' KB' : '';
    var n = now(), grava = !ctx || ctx.commit !== false, nao = 'não anexei ao diário (pedido vindo de link).';
    if (grava) addDiario({ sys: 'Equipamentos', tone: 'var(--cap-accent, #00a1fe)', t: (kind === 'video' ? 'Vídeo' : 'Foto') + ' anexada pelo chat: ' + name + (kb ? ' (' + kb + ')' : '') + ' — identificação A CONFIRMAR.', who: quem(), src: 'app · ' + kind });
    if (kind === 'video') return { key: 'video', text: 'Vídeo recebido (' + name + (kb ? ' · ' + kb : '') + ') · ' + n.d + ' ' + n.t + '.\nO som e o comportamento não são analisados automaticamente: ' + (grava ? 'anexei ao diário como anomalia A CONFIRMAR, com o estado do snapshot' + DEMO_ + ' (' + SNAP.local.toLowerCase() + ' · motores desligados · gerador ligado).' : nao) + '\nDescreva em uma frase o que você viu ou ouviu — respondo com o que verificar primeiro.', src: 'Fonte: anexo · diário de bordo', actions: act(p, [['Abrir diário', 'diario']]) };
    return { key: 'foto', text: 'Foto recebida (' + name + (kb ? ' · ' + kb : '') + ') · ' + n.d + ' ' + n.t + '.\nA leitura da imagem não é automática: ' + (grava ? 'anexei ao diário como A CONFIRMAR.' : nao) + ' Para etiqueta ou tela de alarme, digite o modelo/código que aparece e eu localizo o guia; para nota fiscal, registre em Abastecimento (fica A CONFIRMAR).', src: 'Fonte: anexo · diário de bordo', actions: act(p, [['Abrir diário', 'diario'], ['Documentos', 'docs']]) };
  }

  function safeDecode(s) { try { return decodeURIComponent(String(s).replace(/\+/g, '%20')); } catch (e) { return String(s); } }
  function parseHash() {
    var raw = (location.hash || '').replace(/^#/, '');
    var out = {};
    if (!raw) return out;
    raw.split('&').forEach(function (kv) {
      var i = kv.indexOf('=');
      if (i > 0) out[safeDecode(kv.slice(0, i))] = safeDecode(kv.slice(i + 1));
      else if (kv) out[safeDecode(kv)] = true;
    });
    if (typeof out.q === 'string') out.q = out.q.slice(0, 500); else delete out.q;
    return out;
  }
  function clearHash() { try { history.replaceState(null, '', location.pathname + location.search); } catch (e) {} }

  function recognizer(opts) {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return null;
    var r = new SR();
    r.lang = 'pt-BR'; r.interimResults = true; r.continuous = !!(opts && opts.continuous); r.maxAlternatives = 1;
    return r;
  }
  // ---- Voz (conversa ativa) ----
  // falavel(): texto de tela → português falado. Regras em ordem, guiadas pelas tabelas; sem lookbehind (Safari antigo).
  var MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
  var HEMI = { N: 'norte', S: 'sul', L: 'leste', E: 'leste', O: 'oeste', W: 'oeste' };
  var LET = 'A-Za-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u00FF', MAI = 'A-Z\\u00C0-\\u00D6\\u00D8-\\u00DE'; // letras latinas (em escape: não quebra se o .js vier sem UTF-8)
  // palavra inteira: o grupo 1 guarda o caractere anterior (reposto como $1)
  function rx(core) { return new RegExp('(^|[^' + LET + '\\d])(?:' + core + ')(?![' + LET + '\\d])', 'g'); }
  // unidades — só logo depois de número: [símbolo, singular, plural]; as mais longas primeiro
  var UNID = [
    ['km/h', 'quilômetro por hora', 'quilômetros por hora'], ['L/h', 'litro por hora', 'litros por hora'], ['kWh', 'quilowatt-hora', 'quilowatts-hora'],
    ['kW', 'quilowatt', 'quilowatts'], ['km', 'quilômetro', 'quilômetros'], ['hPa', 'hectopascal', 'hectopascais'], ['MHz', 'megahertz', 'megahertz'],
    ['kHz', 'quilohertz', 'quilohertz'], ['rpm|RPM', 'rotação por minuto', 'rotações por minuto'], ['min', 'minuto', 'minutos'],
    ['mn|NM|MN', 'milha náutica', 'milhas náuticas'], ['kts?|kn|nós|nó', 'nó', 'nós'], ['KB', 'quilobyte', 'quilobytes'], ['MB', 'megabyte', 'megabytes'],
    ['Ah', 'ampère-hora', 'ampères-hora'], ['bar', 'bar', 'bar'], ['L', 'litro', 'litros'], ['h', 'hora', 'horas'], ['m', 'metro', 'metros'], ['s', 'segundo', 'segundos'],
    ['d', 'dia', 'dias'], ['V', 'volt', 'volts'], ['W', 'watt', 'watts'], ['A(?!\\s+[' + MAI + ']{2})', 'ampère', 'ampères']
  ].map(function (u) { return { re: new RegExp('(^|[^' + LET + '\\d.,])(\\d+(?:[.,]\\d+)*)\\s?(?:' + u[0] + ')(\\+?)(?![' + LET + '\\d])', 'g'), um: u[1], varios: u[2] }; });
  // siglas e abreviações por extenso (palavra inteira, maiúsculas exatas)
  var SIGLAS = [
    ['NF-e', 'nota fiscal eletrônica'], ['NF', 'nota fiscal'], ['BB', 'bombordo'], ['BE', 'boreste'], ['SOG', 'velocidade sobre o fundo'],
    ['COG', 'rumo sobre o fundo'], ['STBY', 'standby'], ['MOB', 'homem ao mar'], ['AC', 'corrente alternada'], ['DC', 'corrente contínua'],
    ['RPM', 'rotação'], ['PAN-PAN', 'pan pan'], ['[Nn][º°]', 'número'], ['IA', 'i a'], ['TIE', 'título de inscrição'], ['máx\\.?', 'máximo'], ['mín\\.?', 'mínimo'],
    ['Sr\\.', 'senhor'], ['Sra\\.', 'senhora'], ['ref\\.', 'referência'], ['cert\\.', 'certificado']
  ].map(function (x) { return [rx(x[0]), '$1' + x[1]]; });
  // símbolos → fala ou pausa
  var SIMB = [
    [/Rev\. ?(?=\d)/g, 'revisão '], [/§ ?/g, 'seção '], [/(\d)-(?=\d)/g, '$1 '],
    [/\s*±\s*/g, ' mais ou menos '], [/\s*[≈~]\s*/g, ' cerca de '], [/\s*≤\s*/g, ' até '], [/\s*≥\s*/g, ' pelo menos '],
    [new RegExp('(\\d)\\s*×\\s*(?=[' + LET + '])', 'g'), '$1 '], [/×\s*(\d+)/g, '$1 vezes'], [/\s*×\s*/g, ' vezes '],
    [/\s+\+\s+/g, ' mais '], [/(^|\s)\+(?=\d)/g, '$1mais '], [/\s*%/g, ' por cento'],
    [new RegExp('([' + LET + '])→(?=[' + LET + '])', 'g'), '$1 para '], [/\s*[•·→›|—–=()\[\]]\s*/g, ', '],
    [/\.(pdf|csv|jsonl?|jpe?g|png|mp4|mov|txt)(?![A-Za-z])/gi, function (m, e) { return ' ' + e.toUpperCase(); }], [/(?:\s*_)+\s*/g, ' '],
    [new RegExp('([' + LET + '])\\s*/\\s*(?=\\d)', 'g'), '$1 ou '], [/\s*\/\s*/g, ', ']
  ];
  // MAIÚSCULAS de 4+ letras viram minúsculas (senão o TTS soletra), com as palavrinhas do mesmo trecho; siglas lidas como tal ficam.
  var SIGLA_OK = ' VHF AIS GPS MMSI EPIRB NMEA DHN SOS DSC ';
  var MIUDAS = ' A O E É AS OS DE DA DO DAS DOS EM NA NO NAS NOS AO AOS À ÀS UM UMA SEM COM POR PARA OU QUE SE SÓ JÁ NÃO HÁ ';
  var CAIXA = new RegExp('(^|[^' + LET + '\\d-])([' + MAI + ']+(?: [' + MAI + ']+)*)(?![' + LET + '\\d-])', 'g');
  function minusculas(s) {
    var grande = function (w) { return w.length >= 4 && /[AEIOUÁÉÍÓÚÂÊÔÃÕÀ]/.test(w) && SIGLA_OK.indexOf(' ' + w + ' ') === -1; };
    return s.replace(CAIXA, function (m, a, run) {
      var ws = run.split(' ');
      if (!ws.some(grande)) return m;
      return a + ws.map(function (w) { return grande(w) || MIUDAS.indexOf(' ' + w + ' ') !== -1 ? w.toLowerCase() : w; }).join(' ');
    });
  }
  var FRACAO = { '1/2': 'meio', '1/3': 'um terço', '2/3': 'dois terços', '1/4': 'um quarto', '3/4': 'três quartos' };
  var DATA_ANTES = new RegExp('(?:^|[^' + LET + '])(?:em|dia|até|ate|desde|de|data|prazo|vence|venceu|vencimento) $', 'i'), DATA_FRACA = new RegExp('(?:^|[^' + LET + '])(?:de|até|ate) $', 'i');
  // fração antes de unidade: 1/2 h → meia hora, 1/2 L → meio litro, 1/2 milha → meia milha, 1/4 L → um quarto de litro
  var FRACAO_UNID = { 'L/h': 'litro por hora', L: 'litro', h: 'hora', mn: 'milha náutica', NM: 'milha náutica', hora: 'hora', milha: 'milha', volta: 'volta', polegada: 'polegada' }, FEM = /^(?:hora|milha|volta|polegada)/;
  var FRACAO_UN = new RegExp('(^|[^\\d\\/,.])([123])\\/([234]) ?(L\\/h|L|h|mn|NM|hora|milha|volta|polegada)(?![' + LET + '\\d\\/])', 'g');
  function hora(h) { return h + (h < 2 ? ' hora' : ' horas'); }
  // Horário: "13:23" → "13 horas e 23 minutos" (":00" → "13 horas"); duração "1 h 10" → "1 hora e 10 minutos".
  function falavel(text) {
    // teto de 4.000 letras (fala longa não trava a tela); espaços repetidos viram um só antes das regras
    var s = String(text == null ? '' : text).slice(0, 4000).replace(/[“”"«»]/g, '').replace(/[ \t]/g, ' ').replace(/…/g, ', ');
    // linha = frase; marcador de lista no começo da linha some (a quebra já é pausa)
    s = s.split(/\r?\n/).map(function (l) { return l.replace(/^[\s•·→›—–]+/, '').trim(); }).filter(Boolean)
      .map(function (l, i, a) { return i < a.length - 1 && !/[.!?:;,]$/.test(l) ? l + '.' : l; }).join(' ').replace(/\s+/g, ' ');
    // coordenadas 26°59,58'S → 26 graus e 59 vírgula 58 minutos sul
    s = s.replace(/(\d{1,3}) ?° ?(\d{1,2})(?:,(\d+))? ?['′] ?([NSLOEW])(?![A-Za-z])/g, function (m, g, mi, fr, h) {
      g = +g; mi = +mi;
      return g + (g === 1 ? ' grau e ' : ' graus e ') + mi + (fr ? ' vírgula ' + fr + ' minutos ' : mi === 1 ? ' minuto ' : ' minutos ') + HEMI[h];
    }).replace(/(minutos? (?:norte|sul|leste|oeste)) (?=\d)/g, '$1, ');
    // dinheiro R$ 5.480,50 → 5.480 reais e 50 centavos
    s = s.replace(/R\$ ?(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{2}))?(?!\d)/g, function (m, r, c) {
      var cv = c ? +c : 0, cent = cv ? cv + (cv === 1 ? ' centavo' : ' centavos') : '';
      return r === '0' && cent ? cent : r + (r === '1' ? ' real' : ' reais') + (cent ? ' e ' + cent : '');
    });
    // intervalos 8–14 / 8-14 → 8 a 14 (hífen só entre números curtos); escala 1:50.000 → 1 para 50.000; data + hora ganha "às"
    s = s.replace(/(\d) ?– ?(?=\d)/g, '$1 a ').replace(new RegExp('(^|[^' + LET + '\\d-])(\\d{1,3})-(\\d{1,3})(?![\\d-])', 'g'), '$1$2 a $3')
      .replace(/(^|[^\d:,.])(\d+):(\d{1,3}(?:\.\d{3})+|\d{3,})(?![\d:])/g, '$1$2 para $3').replace(/(\d{1,2}\/\d{1,2}(?:\/\d{4})?) (?=\d{1,2}:\d{2}(?!\d))/g, '$1 às ');
    s = s.replace(FRACAO_UN, function (m, a, d, me, u) {
      var fr = FRACAO[d + '/' + me], nome = FRACAO_UNID[u];
      if (!fr) return m;
      return a + (fr === 'meio' ? (FEM.test(nome) ? 'meia ' : 'meio ') + nome : fr + ' de ' + nome);
    });
    // datas 20/09 → 20 de setembro; 16/01/2027; jan/2031. d/m de um dígito só é data com ano, hora ou palavra de data antes;
    // 1/4 de volta → um quarto de volta; 24/7 → 24 por 7; outro par curto → 5 barra 6.
    s = s.replace(/(^|[^\d\/])(\d{1,2})\/(\d{1,2})(?:\/(\d{4}))?(?![\d\/])/g, function (m, a, d, me, y, i, all) {
      var dd = +d, mm = +me, data = dd >= 1 && dd <= 31 && mm >= 1 && mm <= 12, fr = d.length === 1 && me.length === 1 && FRACAO[d + '/' + me];
      var ctx = (i > 24 ? 'x' : '') + all.slice(Math.max(0, i - 24), i + a.length), antes = DATA_ANTES.test(ctx), depois = all.slice(i + m.length, i + m.length + 12);
      if (!y && !antes && d === '24' && me === '7') return a + '24 por 7';
      if (!y && d.length === 1 && me.length === 1 && !/^ às? \d/.test(depois)) {
        if (fr && /^ d(?:e|o|a|os|as) (?!\d)/.test(depois) && (!antes || DATA_FRACA.test(ctx))) return a + fr;
        if (!antes || !data) return a + (fr || d + ' barra ' + me);
      }
      return data ? a + (dd === 1 ? 'primeiro' : dd) + ' de ' + MESES[mm - 1] + (y ? ' de ' + y : '') : m;
    }).replace(new RegExp('(^|[^' + LET + '])(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)/(\\d{4})(?!\\d)', 'gi'), function (m, a, me, y) {
      return a + MESES['janfevmarabrmaijunjulagosetoutnovdez'.indexOf(me.toLowerCase()) / 3] + ' de ' + y;
    });
    // horário 13:23 / 23h01 (nunca razão) e duração 1 h 10 / 6 h 58 min
    s = s.replace(/(^|[^\d:,.])(\d{1,2})(?::|h)(\d{2})(?:min(?![A-Za-z]))?(?![\d:]|\.\d)/g, function (m, a, h, mi) {
      h = +h; mi = +mi;
      return h > 23 || mi > 59 ? m : a + hora(h) + (mi ? ' e ' + mi + (mi === 1 ? ' minuto' : ' minutos') : '');
    }).replace(/ às ([01] hora)(?!s)/g, ' à $1').replace(/(^|[^\d,.])(\d+) ?h ?(\d{1,2})(?: ?min(?![A-Za-z])|(?![\d,.:\/]\d|\d| ?[A-Za-z%°]))/g, function (m, a, h, mi) {
      mi = +mi;
      return a + hora(+h) + (mi ? ' e ' + mi + (mi === 1 ? ' minuto' : ' minutos') : '');
    });
    // graus: 22,6 °C → graus Celsius; proa 071° → 71 graus
    s = s.replace(/(^|[^\d,])(\d+(?:,\d+)?) ?° ?C(?![A-Za-z])/g, function (m, a, n) { return a + n + (n === '1' ? ' grau' : ' graus') + ' Celsius'; })
      .replace(/(^|[^\d,])(\d+)(,\d+)? ?°/g, function (m, a, n, f) { n = +n + (f || ''); return a + n + (n === '1' ? ' grau' : ' graus'); });
    // D-17 (dias até) → D menos 17; MMSI dígito a dígito, como no rádio
    s = s.replace(new RegExp('(^|[^' + LET + '\\d])D-(\\d+)(?!\\d)', 'g'), '$1D menos $2')
      .replace(/MMSI:? ?(\d{9})(?!\d)/g, function (m, n) { return 'MMSI ' + n.split('').join(' '); });
    // decimal sem zeros à direita (34,0 → 34; 156,800 → 156,8), depois unidades, siglas e símbolos
    s = s.replace(/(\d),(\d*?)0+(?!\d)/g, function (m, a, b) { return b ? a + ',' + b : a; });
    UNID.forEach(function (u) { s = s.replace(u.re, function (m, a, n, mais) { return a + n + ' ' + (n === '1' ? u.um : u.varios) + (mais ? ' ou mais' : ''); }); });
    SIGLAS.forEach(function (x) { s = s.replace(x[0], x[1]); });
    s = s.replace(/°/g, ' graus');
    s = s.replace(/\s+/g, ' ');
    SIMB.forEach(function (x) { s = s.replace(x[0], x[1]); });
    s = minusculas(s);
    // 3.2 → 3 ponto 2 (milhar 1.500 fica); 27,42 → 27 vírgula 42
    s = s.replace(/(^|[^\d.])(\d+(?:\.\d+)+)/g, function (m, a, n) { var g = n.split('.'); return a + (g.slice(1).every(function (x) { return x.length === 3; }) ? n : g.join(' ponto ')); })
      .replace(/(\d),(?=\d)/g, '$1 vírgula ');
    // pontuação: um só sinal por pausa (o mais forte), sem ". ." nem ", :"
    return s.replace(/\s+/g, ' ').replace(/\s*([,;:.!?](?:\s*[,;:.!?])*)\s*/g, function (m, p, i, all) {
      if (m.length === 1 && /\d/.test(all.charAt(i - 1)) && /\d/.test(all.charAt(i + 1))) return m;
      return (/[?!]/.test(p) ? p.match(/[?!]/)[0] : p.indexOf('.') !== -1 ? '.' : /[:;]/.test(p) ? p.match(/[:;]/)[0] : ',') + ' ';
    }).replace(/^[\s,;:.!?]+|[\s,;:]+$/g, '');
  }

  // Melhor voz pt-BR: neural/online › Google › Apple premium/enhanced › Luciana/Felipe › qualquer pt-BR › qualquer pt. Nunca outro idioma.
  var VOZ = { v: null, on: null, ruim: {} };
  var VOZ_PREF = [[/natural|neural/i, 600], [/online/i, 550], [/google/i, 500], [/premium/i, 450], [/enhanced|aprimorad|melhorad/i, 400], [/luciana|felipe/i, 300]];
  function notaVoz(v, on) {
    var lang = String(v.lang || '').replace(/_/g, '-').toLowerCase(), nome = String(v.name || ''), id = nome + ' ' + (v.voiceURI || '');
    if (!/^(pt|por)(-|$)/.test(lang) || VOZ.ruim[nome]) return 0;
    var n = /-bra?$/.test(lang) || (/^(pt|por)$/.test(lang) && /bra[sz]il/i.test(nome)) ? 2000 : 1000;
    for (var j = 0; j < VOZ_PREF.length; j++) if (VOZ_PREF[j][0].test(id)) { n += VOZ_PREF[j][1]; break; }
    if (!on && v.localService === false) n -= 700; // sem internet a voz de rede não fala
    if (/eloquence/i.test(v.voiceURI || '') || /^(eddy|flo|grandma|grandpa|reed|rocko|sandy|shelley)\b/i.test(nome)) n -= 50; // vozes-novidade da Apple
    // voz masculina ganha de voz feminina do mesmo nível (natural/online), mas nunca de uma voz bem mais natural
    return n + (/antonio|felipe|donato|fabio|humberto|julio|nicolau|valerio|daniel|ricardo/i.test(nome) ? 120 : 0) + (v.default ? 1 : 0);
  }
  function vozPtBr() {
    var ss = window.speechSynthesis, on = !(window.navigator && window.navigator.onLine === false), lista = [], best = null, nota = 0;
    if (VOZ.v && VOZ.on === on) return VOZ.v;
    try { lista = (ss && ss.getVoices && ss.getVoices()) || []; } catch (e) {}
    for (var j = 0; j < lista.length; j++) { var n = notaVoz(lista[j], on); if (n > nota) { nota = n; best = lista[j]; } }
    VOZ.v = best; VOZ.on = on;
    return best;
  }
  // as vozes chegam depois (Chrome começa com lista vazia): pede já e refaz a escolha quando a lista mudar
  (function () {
    var ss = window.speechSynthesis, zera = function () { VOZ.v = null; };
    if (!ss) return;
    try { ss.getVoices(); if (ss.addEventListener) ss.addEventListener('voiceschanged', zera); else if (!ss.onvoiceschanged) ss.onvoiceschanged = zera; } catch (e) {}
  })();
  // Frases inteiras em blocos de até ~200 letras: prosódia melhor e sem o corte do Chrome em falas longas (~15 s).
  function blocos(s) {
    var MAX = 200, out = [];
    (function junta(partes, sep, nivel) {
      var cur = '';
      partes.forEach(function (p) {
        if (!p) return;
        if (p.length > MAX && nivel < 2) { if (cur) out.push(cur); cur = ''; junta(nivel ? p.split(' ') : p.split(/,\s+/), nivel ? ' ' : ', ', nivel + 1); return; }
        if (cur && (cur + sep + p).length > MAX) { out.push(cur); cur = p; } else cur = cur ? cur + sep + p : p;
      });
      if (cur) out.push(cur);
    })(s.replace(/([.!?;])\s+/g, '$1\n').split('\n'), ' ', 0);
    return out;
  }
  // Vigia de cada bloco calculada a 1x: 95 ms/letra (folga) + 250 ms/dígito, porque número falado é longo. A voz vai a
  // 1,15x (RATE), então a fala acaba antes e a vigia só fica mais folgada.
  function estimaMs(t) { return Math.min(60000, 2000 + t.length * 95 + (t.match(/\d/g) || []).length * 250); }
  var FALA = { gen: 0, timer: null, vivo: null, fila: [] };
  var RATE = 1.15; // velocidade da voz em TODA fala, inclusive emergência (SOS, óleo, EPIRB, Seafire) — decisão do proprietário
  function calaTimers() { clearTimeout(FALA.timer); clearInterval(FALA.vivo); FALA.timer = FALA.vivo = null; }
  // Eventos 'capitao-voz' ({ estado: ouvindo | pensando | falando | pulso | livre, texto, segura?, som? }) — núcleo de IA
  // (capitao-voz.js). segura: esperando a IA na nuvem (vozPensando). som (no 'falando'): a voz está tocando (true, no onstart)
  // ou calada (false: antes de o bloco começar e no fim dele) — o rosto abre a boca e solta as ondas só com som.
  function evVoz(estado, texto, extra) {
    var det = { estado: estado, texto: texto || '' };
    if (extra) for (var k in extra) if (Object.prototype.hasOwnProperty.call(extra, k)) det[k] = extra[k];
    try { window.dispatchEvent(new CustomEvent('capitao-voz', { detail: det })); } catch (e) {}
  }
  var ESCUTA = { rec: null };
  // Ditado: escuta até a pessoa parar de falar por `pausa` ms (ou tocar de novo). Junta todos os trechos — o reconhecedor
  // fecha um "resultado final" a cada respiro e, no Android, encerra a cada frase: aqui ele religa sozinho sem perder o texto.
  // o = { pausa, espera (ms sem ouvir nada até desistir), max, parcial(texto), fim(texto), erro(codigo) }. Retorna { parar, cancelar } ou null.
  function ditado(o) {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition; if (!SR) return null;
    o = o || {};
    var pausa = o.pausa || 2500, feito = false, texto = '', sessao = '', r = null, t = 0, tMax = 0, ouviu = false, rapidas = 0, ini = 0;
    function atual() { return (texto + ' ' + sessao).replace(/\s+/g, ' ').trim(); }
    // O Chrome do Android devolve resultados acumulados ("você", "você tem", "você tem banco"…): somar tudo repetia palavras.
    // Cada sessão é remontada do zero a partir de todos os resultados, e um trecho que continua o anterior o substitui.
    function junta(lista, seg) {
      var n = norm(seg).replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim(); if (!n) return;
      var ult = lista.length ? norm(lista[lista.length - 1]).replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim() : null;
      if (ult !== null && n.indexOf(ult) === 0) lista[lista.length - 1] = seg.trim();
      else if (ult !== null && ult.indexOf(n) === 0) return;
      else lista.push(seg.trim());
    }
    function arma() { clearTimeout(t); t = setTimeout(function () { fim(); }, ouviu ? pausa : (o.espera || 8000)); }
    function solta() { clearTimeout(t); clearTimeout(tMax); var x = r; r = null; if (x) { try { x.onresult = x.onend = x.onerror = null; x.abort(); } catch (e) {} } }
    function fim() { if (feito) return; feito = true; var txt = atual(); solta(); solto(); evVoz(txt ? 'pensando' : 'livre', txt); if (o.fim) o.fim(txt); }
    function falha(e) { if (feito) return; feito = true; solta(); solto(); evVoz('livre'); if (o.erro) o.erro(e); }
    function solto() { if (ESCUTA.rec === h) ESCUTA.rec = null; }
    function liga() {
      var x = r = new SR(); x.lang = 'pt-BR'; x.continuous = true; x.interimResults = true; x.maxAlternatives = 1; ini = Date.now();
      x.onresult = function (ev) {
        if (x !== r) return;
        var partes = [];
        for (var i = 0; i < ev.results.length; i++) junta(partes, String(ev.results[i][0].transcript || ''));
        sessao = partes.join(' ');
        if (atual()) { ouviu = true; rapidas = 0; }
        if (o.parcial) o.parcial(atual()); evVoz('ouvindo', atual()); arma();
      };
      x.onerror = function (ev) { var e = ev && ev.error; if (x === r && (e === 'not-allowed' || e === 'service-not-allowed' || e === 'audio-capture')) falha(e); };
      x.onend = function () { // fim de sessão do navegador (não da pessoa): guarda o que ouviu e religa
        if (x !== r || feito) return;
        texto = atual(); sessao = '';
        rapidas = Date.now() - ini < 400 ? rapidas + 1 : 0;
        if (rapidas >= 4) { if (ouviu) fim(); else falha('no-speech'); return; }
        try { liga(); } catch (e) { fim(); }
      };
      x.start();
    }
    var h = { parar: fim, cancelar: function () { if (feito) return; feito = true; solta(); solto(); evVoz('livre'); } };
    try { liga(); } catch (e) { return null; }
    arma(); tMax = setTimeout(fim, o.max || 90000);
    ESCUTA.rec = h; evVoz('ouvindo', '');
    return h;
  }
  // Convite: o site não tem servidor — o convite sai pelo WhatsApp (celular) ou e-mail do próprio aparelho, com o link de acesso.
  // contato = celular com DDD (8–15 dígitos; sem +55 assume Brasil) ou e-mail. Retorna { href, canal, contato } ou null se inválido.
  function linkConvite(nome, contato, acesso) {
    var c = String(contato || '').trim(), url = location.href.replace(/[^\/]*$/, '') + 'login.html';
    var msg = 'Olá, ' + nome + '! Você foi convidado(a) para o Capitão IA — embarcação ' + (E.nome || 'Capitão IA') + (D.demo ? ' (demonstração)' : '') + ', acesso ' + (acesso || 'total') + '.\nEntre por: ' + url + '\nO usuário e a senha são passados pelo proprietário.';
    if (/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(c)) return { canal: 'e-mail', contato: c, href: 'mailto:' + encodeURIComponent(c) + '?subject=' + encodeURIComponent('Convite · Capitão IA') + '&body=' + encodeURIComponent(msg) };
    if (!/^\+?[\d ().-]+$/.test(c)) return null;
    var d = c.replace(/\D/g, ''); if (d.length < 10 || d.length > 15) return null;
    if (c.charAt(0) !== '+' && d.length <= 11) d = '55' + d.replace(/^0+/, '');
    return { canal: 'WhatsApp', contato: c, href: 'https://wa.me/' + d + '?text=' + encodeURIComponent(msg) };
  }
  // Legendas do núcleo de voz: o texto original (com siglas e números como na tela), linha a linha.
  function legendas(text) {
    var out = [];
    String(text || '').split(/\n+/).forEach(function (l) { l = l.trim(); if (l) out = out.concat(blocos(l)); });
    return out;
  }
  // onEnd dispara uma única vez, depois do último bloco (ou por erro/vigia). Nova fala ou stopSpeaking() trocam a geração: o onEnd antigo nunca dispara.
  function speak(text, onEnd) {
    var gen = ++FALA.gen, done = false, ss = window.speechSynthesis, i = 0, atual = null, tentou = {}, voz = null, partes = [], leg = legendas(text);
    var fin = function () { if (done || gen !== FALA.gen) return; done = true; calaTimers(); FALA.fila = []; FALA.pula = null; evVoz('livre'); if (onEnd) onEnd(); };
    var vale = function (u) { return !done && gen === FALA.gen && u === atual; };
    var legenda = function (k, n) { return leg.length ? leg[Math.min(leg.length - 1, Math.floor(k * leg.length / Math.max(1, n)))] : ''; };
    calaTimers(); FALA.fila = [];
    // Tocar no núcleo enquanto fala: encerra esta fala como se tivesse terminado (a conversa volta a ouvir).
    FALA.pula = function () { if (done || gen !== FALA.gen) return; try { if (ss) ss.cancel(); } catch (e) {} fin(); };
    function vigia(u, ms) { clearTimeout(FALA.timer); FALA.timer = setTimeout(function () { if (vale(u)) avanca(); }, ms); }
    function avanca() { if (++i >= partes.length) return fin(); try { fala(i); } catch (e) { fin(); } }
    function fala(k) {
      var u = new SpeechSynthesisUtterance(partes[k]), est = estimaMs(partes[k]);
      u.lang = voz && voz.lang ? String(voz.lang).replace(/_/g, '-') : 'pt-BR'; if (voz) u.voice = voz; u.rate = RATE;
      u.onstart = function () { if (vale(u)) { vigia(u, est); evVoz('falando', legenda(k, partes.length), { som: true }); } };
      u.onboundary = function (e) { if (vale(u) && (!e || e.name !== 'sentence')) evVoz('pulso'); };
      u.onend = function () { if (vale(u)) { evVoz('falando', legenda(k, partes.length), { som: false }); avanca(); } };
      u.onerror = function (e) {
        if (!vale(u)) return;
        var err = e && e.error;
        if (err === 'interrupted' || err === 'canceled') return fin(); // cancelada por fora
        if (voz && voz.localService === false && !tentou[k]) { // voz de rede falhou (sem internet): troca de voz e repete o bloco
          tentou[k] = 1; VOZ.ruim[voz.name] = 1; VOZ.v = null; voz = vozPtBr();
          try { return fala(k); } catch (x) { return fin(); }
        }
        avanca();
      };
      atual = u; FALA.fila.push(u); vigia(u, est + 4000);
      evVoz('falando', legenda(k, partes.length), { som: false }); // som só no onstart (a voz pode demorar a começar)
      ss.speak(u);
    }
    function doAparelho() {
      if (done || gen !== FALA.gen) return false;
      if (!ss || !window.SpeechSynthesisUtterance) { setTimeout(fin, 0); return false; }
      try {
        partes = blocos(falavel(text)); voz = vozPtBr(); i = 0;
        ss.cancel(); if (ss.paused) ss.resume();
        if (!partes.length) { setTimeout(fin, 0); return false; }
        fala(0);
        // keep-alive do Chrome desktop só p/ voz Google de rede (a que corta em ~15 s)
        if (!done && voz && /google/i.test(voz.name) && voz.localService === false && !/android/i.test((window.navigator && window.navigator.userAgent) || ''))
          FALA.vivo = setInterval(function () { try { if (gen === FALA.gen && ss.speaking && !ss.paused) { ss.pause(); ss.resume(); } } catch (e) {} }, 10000);
        return true;
      } catch (e) { calaTimers(); setTimeout(fin, 0); return false; }
    }
    return doAparelho();
  }
  function stopSpeaking() { FALA.gen++; calaTimers(); FALA.fila = []; FALA.pula = null; try { window.speechSynthesis && window.speechSynthesis.cancel(); } catch (e) {} evVoz('livre'); }
  // Abertura da conversa (persona): curta, sem cerimônia.
  function abertura() { return 'Capitão IA online. Que precisa?'; }
  // Fala direta: na voz vai só o essencial (a 1ª linha da resposta, sem fontes); o texto completo fica na tela.
  // Emergência (SOS, pressão de óleo, EPIRB, incêndio) é lida inteira — segurança vem antes da concisão.
  var FALA_INTEIRA = { sos: 1, oleo: 1, epirb: 1, seafire: 1 };
  function falaCurta(a) {
    if (a && typeof a === 'object' && a.fala) return a.fala; // resposta que já traz a fala certa (saudação vinda de pergunta)
    var t = a && typeof a === 'object' ? a.text : a;
    if (a && a.key && FALA_INTEIRA[a.key]) return String(t || '');
    // Trecho de segurança da base (Seafire, EPIRB, salvatagem, protocolo…): o trecho inteiro, com o rótulo e a nota da etiqueta
    // (sem a linha "Veja também"). Antes, a fala parava na 2ª frase e perdia o "não abra o acesso ao motor" e o rótulo.
    if (a && a.key === 'base' && a.seguranca && typeof t === 'string') return t.split(/\n+/)[0].trim();
    if (a && a.key === 'base' && a.ingles) return 'Está no ' + String(a.ref || 'manual').replace(/, p\. /, ', página ').replace(/ · .*$/, '') + ', em inglês. Mostrei o trecho na tela.';
    // Tira parênteses da fala, inclusive aninhados: "(… snapshot (DEMO) …)" sai inteiro, sem sobra.
    var semPar = function (s) { var a; do { a = s; s = s.replace(/\s*\([^()]*\)/g, ''); } while (s !== a); return s.replace(/\s*[()]/g, ''); };
    var item = function (l) { return semPar(l.replace(/^(\d+[.)]|•|-)\s*/, '')).trim(); };
    var ls = String(t || '').split(/\n+/).map(function (l) { return l.trim(); }).filter(function (l) { return l && !/^fonte\b/i.test(l); });
    var r = semPar(ls[0] || ''), extra = [], lim = 220;
    // Resposta da IA: conversa — a 1ª frase curta ganha a seguinte ("Sou o Capitão IA. Respondo sobre…"), até ~320 letras.
    if (a && a.key === 'ia') { lim = 320; if (ls.length > 1 && r.length < 90 && !/:$/.test(r) && !/^(\d+[.)]|•|-)/.test(ls[1])) r = (/[.!?]$/.test(r) ? r : r + '.') + ' ' + semPar(ls[1]); }
    if (/ressalva/i.test(r)) extra = ls.filter(function (l) { return /ressalva\s*\d/i.test(l); }).map(function (l) { return item(l).replace(/^ressalva\s*\d+:\s*/i, '').split(' — ')[0]; });
    else if (/:$/.test(r)) { r = r.replace(/:$/, ''); extra = ls.slice(1, 3).filter(function (l) { return /^(\d+[.)]|•|-)/.test(l); }).map(item); }
    extra = extra.map(function (x) { return x.replace(/[\s.;:,]+$/, ''); }).filter(Boolean);
    if (extra.length) r = r.replace(/[.]$/, '') + ': ' + extra.join('; ') + '.';
    if (r.length > lim) { var m = r.slice(0, lim).match(/^[\s\S]*[.!?;]/); r = m ? m[0].replace(/;$/, '.') : r.slice(0, r.lastIndexOf(' ', lim)) + '.'; }
    return r;
  }
  // A tela avisa o núcleo de voz que espera a IA na nuvem: ele fica em PROCESSANDO até a resposta ser falada (sem sumir em 2,5 s).
  function vozPensando(texto) { try { window.dispatchEvent(new CustomEvent('capitao-voz', { detail: { estado: 'pensando', texto: texto || '', segura: true } })); } catch (e) {} }

  // Controles do overlay de voz (capitao-voz.js)
  function vozEnviar() { if (ESCUTA.rec) ESCUTA.rec.parar(); }
  function pularFala() { if (FALA.pula) FALA.pula(); }
  function vozEncerrar() {
    try { window.dispatchEvent(new CustomEvent('capitao-voz-encerrar')); } catch (e) {} // a tela desliga a conversa e limpa o estado
    var r = ESCUTA.rec; ESCUTA.rec = null; if (r) try { r.cancelar(); } catch (e) {}
    stopSpeaking();
  }

  window.CapitaoBrain = { VERSAO: VERSAO, DADOS: D, BASE: BASE, buscaBase: buscaBase, carregaBase: carregaBase, DEFAULTS: DEFAULTS, BANK: BANK, ALL: ALL, HREF: HREF, loadShortcuts: loadShortcuts, saveShortcuts: saveShortcuts, resetShortcuts: resetShortcuts, bankFor: bankFor, loadDiario: loadDiario, addDiario: addDiario, diarioFonte: diarioFonte, loadExec: loadExec, markExec: markExec, unmarkExec: unmarkExec, loadEquipe: loadEquipe, saveEquipe: saveEquipe, loadDocs: loadDocs, addDoc: addDoc, loadAbast: loadAbast, addAbast: addAbast, answer: answer, answerAttachment: answerAttachment, pedeIA: pedeIA, ficha: ficha, vozPensando: vozPensando, quem: quem, route: route, parseHash: parseHash, clearHash: clearHash, recognizer: recognizer, ditado: ditado, linkConvite: linkConvite, speak: speak, stopSpeaking: stopSpeaking, abertura: abertura, falaCurta: falaCurta, vozEnviar: vozEnviar, pularFala: pularFala, vozEncerrar: vozEncerrar, falavel: falavel, voz: vozPtBr, now: now, askHref: askHref, nb: nb, mil: mil, horas: horas, grau3: grau3, SNAP: SNAP, SOS_PASSOS: SOS_PASSOS, OLEO_PASSOS: OLEO_PASSOS, MMSI: MMSI_RADIO, MMSI_RADIO: MMSI_RADIO, ROTULO: ROTULO,
    LISTAS: { SOS: SOS.slice(), SOS_REGEX: SOS_REGEX_FONTES.slice(), SALVATAGEM: SALVATAGEM.slice(), BOIA_FORA: BOIA_FORA.slice(), EPIRB: EPIRB_PALAVRAS.slice() }, emergencia: emergencia };
  try { window.dispatchEvent(new CustomEvent('capitao-brain-ready')); } catch (e) {}
})();
