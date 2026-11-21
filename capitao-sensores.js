/* Capitão IA — os sensores do barco sobre o desenho (telas A4-Sensores-Web e A5-Sensores-Mobile; PARIDADE F08; CONTRATO-DADOS §1.19).
   O desenho é próprio e genérico (assets/sensores-perfil.svg e assets/sensores-planta.svg, no tamanho e na referência do D.sensores); as posições, os campos e os blocos vêm do D.sensores
   gerado, e o valor de cada sensor é o do instante do CapitaoAgora (replay, coletor ou a última leitura salva): o mesmo texto da moldura, do cérebro e da Ponte (CapitaoAgora.fmt.campo).
     CapitaoSensores.vistas(modo)   → { perfil, planta } (só dado, sem elemento): cada vista { img, w, h, pontos: [{ n, id, rotulo, curto, onde, vista, x, y, campos, itens: [{k, v}], linha1, linha2,
                                      titulo, cor, rgb, tem, nivel, bloco: [bx, by, lado] }] } e, no pai, { hora, fonte, reserva }; `modo` é 'web' ou 'app' (o bloco e o tamanho do texto)
     CapitaoSensores.elemento(vista, { altura, modo })  → o desenho com os pontos, as linhas e os miniblocos, como elemento React (nada de {{…}} em atributo de SVG: é HTML posicionado)
     CapitaoSensores.contagem()     → { total, comValor }: quantos pontos do D.sensores têm algum campo no quadro de agora
   Os miniblocos ficam na faixa de cima ou de baixo do desenho (D.sensores.pontos[].bloco), ligados ao ponto por uma linha fina; o ponto é desenhado POR CIMA do bloco (alguns sensores do alto, como o
   radar e a estação meteorológica, ficam sob a faixa de cima: o ponto nunca some). Roll, pitch e yaw no inclinômetro (jogo, caimento e proa). Sem equipamento de salvatagem nem de incêndio entre os pontos.
   Com a simulação o valor sempre existe; o caminho `null` → SEM DADOS / SEM LEITURA é do ramo simulacao:false (falta()). No SOS o arquivo nem se define. Nunca lança erro. */
(function () {
  var EM_SOS = false;
  try { EM_SOS = /SOS-/.test(location.pathname); } catch (e) {}
  if (EM_SOS || window.CapitaoSensores) return;

  function D() { return window.CapitaoDados || {}; }
  function A() { return window.CapitaoAgora || null; }
  function num(x) { return typeof x === 'number' && isFinite(x); }
  var SD = 'SEM DADOS', SL = 'SEM LEITURA';
  function falta(rot) { return D().simulacao === true ? '—' : rot; }
  // nome curto do bloco (o bloco tem ~0,1 da largura do desenho); sem ele vale o `rotulo` do D.sensores
  var CURTO = { meteo: 'Meteorologia', estabilizador: 'Estabilizador', praca: 'Praça de máq.', inclinometro: 'Inclinômetro', diesel_bb: 'Diesel BB', diesel_be: 'Diesel BE', agua: 'Água doce', servidas: 'Servidas',
    b24s: 'Serviço 24 V', b24p: 'Partida 24 V', b12: 'Banco 12 V', porao_bb: 'Porão BB', porao_be: 'Porão BE', guincho: 'Guincho', dessal: 'Dessalinizador', motor_bb: 'Motor BB', motor_be: 'Motor BE' };

  function instante() { try { var a = A(); return a && typeof a.instante === 'function' ? a.instante() : null; } catch (e) { return null; } }
  // o valor do campo como a tela mostra, com a unidade; ligado/desligado nos booleanos; null se o quadro não tem o campo
  function valorCampo(q, campo) {
    var a = A(), F = a && a.fmt, c = D().campos && D().campos[campo], v = q ? q[campo] : undefined, t, un;
    if (typeof v === 'boolean') return v ? 'ligado' : 'desligado';
    if (!F || typeof F.campo !== 'function') return null;
    t = F.campo(q, campo);
    if (t === null || t === undefined) return null;
    if (typeof v === 'string') return t;
    un = c && c.un ? c.un : '';
    return t + (un === '°' ? '°' : un ? ' ' + un : '');
  }
  function rotuloCampo(campo) { var c = D().campos && D().campos[campo]; return c && c.rotulo ? c.rotulo : campo; }
  function pior(q, campos) {   // o pior nível (faixa do guia) entre os campos do ponto: 'critico' | 'aviso' | 'normal'
    var a = A(), out = 'normal', i, r;
    for (i = 0; i < campos.length; i++) {
      try { r = a && typeof a.nivel === 'function' && q ? a.nivel(campos[i], q) : null; } catch (e) { r = null; }
      if (r && r.nivel === 'critico') return 'critico';
      if (r && r.nivel === 'aviso') out = 'aviso';
    }
    return out;
  }
  var COR = { normal: ['var(--cap-ok, #34c77a)', 'var(--cap-ok-rgb, 52,199,122)'], aviso: ['var(--cap-warn, #f0a63a)', 'var(--cap-warn-rgb, 240,166,58)'], critico: ['var(--cap-crit, #ff3b30)', 'var(--cap-crit-rgb, 255,59,48)'],
    sem: ['var(--cap-ink3, #97a3c0)', 'var(--cap-ink3-rgb, 151,163,192)'] };

  // os itens da lista de valores e da dica (rótulo e valor de cada campo): nos liga/desliga o rótulo do campo já carrega o estado («Radar transmitindo», «Dessalinizador ligado»), então fica só o nome e o
  // valor (ligado/desligado) diz o resto, sem «ligado desligado»; dois campos do mesmo equipamento com o mesmo rótulo («Volante do estabilizador» em rpm e em %) viram um item só, com os dois valores
  function itensTexto(itens) {
    var out = [], i, it, k, j, achou;
    for (i = 0; i < itens.length; i++) {
      it = itens[i]; k = it.b ? it.k.replace(/\s+(ligad[oa]s?|transmitindo)$/i, '') : it.k; achou = null;
      for (j = 0; j < out.length; j++) if (out[j].k === k) achou = out[j];
      if (achou) achou.v += ' · ' + it.v; else out.push({ k: k, v: it.v });
    }
    return out;
  }

  function ponto(p, q, modo) {
    var itens = [], tem = false, i, v, linha2, inc = p.id === 'inclinometro', nv, txt;
    for (i = 0; i < (p.campos || []).length; i++) {
      v = valorCampo(q, p.campos[i]);
      if (v !== null) tem = true;
      itens.push({ k: rotuloCampo(p.campos[i]), v: v === null ? falta(SL) : v, c: p.campos[i], cru: v, b: !!q && typeof q[p.campos[i]] === 'boolean' });
    }
    if (inc) {   // roll, pitch e yaw (F08): jogo, caimento e proa, cada um como a tela mostra
      var j = valorCampo(q, 'jogo_graus'), c = valorCampo(q, 'caimento_graus'), y = valorCampo(q, 'proa_graus');
      linha2 = j !== null && c !== null && y !== null ? 'R ' + j + ' P ' + c + ' Y ' + y : falta(SL);
      itens.forEach(function (it) { it.k = it.c === 'jogo_graus' ? 'Roll (jogo)' : it.c === 'caimento_graus' ? 'Pitch (caimento)' : it.c === 'proa_graus' ? 'Yaw (proa)' : it.k; });
    } else {
      var vals = itens.filter(function (it) { return it.cru !== null; }).map(function (it) { return it.v; });
      linha2 = vals.length ? (modo === 'app' ? vals.slice(0, 1) : vals.slice(0, 2)).join(' · ') : falta(SL);
    }
    nv = tem ? pior(q, p.campos || []) : 'sem';
    txt = itensTexto(itens);
    return { n: p.n, id: p.id, rotulo: p.rotulo, curto: CURTO[p.id] || p.rotulo, onde: p.onde, vista: p.vista, x: p.x, y: p.y, campos: p.campos || [], itens: txt,
      linha1: CURTO[p.id] || p.rotulo, linha2: linha2, titulo: p.rotulo + ' · ' + p.onde + ': ' + txt.map(function (it) { return it.k + ' ' + it.v; }).join(' · '),
      cor: COR[nv][0], rgb: COR[nv][1], tem: tem, nivel: nv, bloco: (p.bloco && (p.bloco[modo] || p.bloco.web)) || null };
  }
  function vistas(modo) {
    try {
      var S = D().sensores, I = instante(), q = I && I.q ? I.q : null, out = { perfil: null, planta: null, hora: I ? (I.fonte === 'snapshot' ? String(I.fonteTxt || '').replace(/^.*leitura de /, '') : I.hhmm) : '—', fonte: I ? String(I.fonteTxt || '').replace(/(\d\d:\d\d):\d\d/, '$1') : falta(SD), reserva: !!(I && I.fonte === 'snapshot') };
      if (!S || !Array.isArray(S.pontos)) return out;
      modo = modo === 'app' ? 'app' : 'web';
      ['perfil', 'planta'].forEach(function (k) {
        var vw = S[k];
        if (!vw) return;
        out[k] = { img: vw.img, w: vw.w, h: vw.h, pontos: S.pontos.filter(function (p) { return p.vista === k; }).map(function (p) { return ponto(p, q, modo); }) };
      });
      return out;
    } catch (e) { return { perfil: null, planta: null, hora: '—', fonte: '', reserva: false }; }
  }
  function contagem() {
    var S = D().sensores, I = instante(), q = I && I.q ? I.q : null, tem = 0;
    if (!S || !Array.isArray(S.pontos)) return { total: 0, comValor: 0 };
    S.pontos.forEach(function (p) { if ((p.campos || []).some(function (c) { return valorCampo(q, c) !== null; })) tem++; });
    return { total: S.pontos.length, comValor: tem };
  }

  // o desenho com os pontos, as linhas e os miniblocos: HTML posicionado em px (a caixa tem a proporção do desenho, a altura vem da tela).
  // A faixa de cima e a de baixo dos blocos sobem ou descem, em passos de 1 % da altura, até nenhum bloco cobrir um ponto (o radar e a estação meteorológica, no alto do perfil, ficariam
  // debaixo da faixa de cima); a caixa ganha a folga que os blocos pedem, em cima e embaixo.
  function elemento(v, o) {
    var React = window.React, h, alt, app, W, H, bw, bh, kids = [], fs, r, padH;
    try {
      if (!v || !React) return null;
      h = React.createElement; o = o || {}; app = o.modo === 'app'; alt = o.altura || (app ? 330 : 300);
      H = alt; W = Math.round(alt * v.w / v.h); fs = app ? 9.5 : 10; r = app ? 4.5 : 5.5; padH = app ? 4 : 4;
      bh = Math.floor((app ? 0.09 : 0.1) * H) - 3; bw = Math.floor(0.1 * W) - 4;
      var pts = v.pontos.filter(function (p) { return !!p.bloco; });
      var rect = function (p, sh) {
        var b = p.bloco, bx = Math.max(bw / 2 + 2, Math.min(W - bw / 2 - 2, b[0] * W)), by = b[1] * H, cima = b[2] === 'cima', top = cima ? by - bh - sh : by + sh;
        return { l: bx - bw / 2, t: top, r: bx + bw / 2, b: top + bh, bx: bx, ay: cima ? by - sh : by + sh, cima: cima };
      };
      var livre = function (sh, lado) {   // nenhum bloco da faixa `lado` cobre um ponto, nem o dele
        var m = r + 3, i, k, q, p;
        for (i = 0; i < pts.length; i++) {
          p = pts[i]; if ((p.bloco[2] === 'cima') !== (lado === 'cima')) continue;
          q = rect(p, sh);
          for (k = 0; k < v.pontos.length; k++) { var x = v.pontos[k].x * W, y = v.pontos[k].y * H; if (x > q.l - m && x < q.r + m && y > q.t - m && y < q.b + m) return false; }
        }
        return true;
      };
      var passo = Math.max(2, Math.round(0.01 * H)), sc = 0, sb = 0;
      while (!livre(sc, 'cima') && sc < 0.2 * H) sc += passo;
      while (!livre(sb, 'baixo') && sb < 0.2 * H) sb += passo;
      var rs = pts.map(function (p) { return rect(p, p.bloco[2] === 'cima' ? sc : sb); });
      var topo = Math.min.apply(null, [0].concat(rs.map(function (q) { return q.t; }))), fundo = Math.max.apply(null, [H].concat(rs.map(function (q) { return q.b; })));
      var mt = Math.ceil(-topo) + 4, mb = Math.ceil(fundo - H) + 4;
      var url = 'url(' + v.img + ')';
      kids.push(h('div', { key: 'traco', 'aria-hidden': 'true', style: { position: 'absolute', left: 0, top: 0, width: W, height: H, background: 'var(--cap-ink3, #97a3c0)', opacity: 0.72, WebkitMaskImage: url, maskImage: url, WebkitMaskSize: '100% 100%', maskSize: '100% 100%', WebkitMaskRepeat: 'no-repeat', maskRepeat: 'no-repeat' } }));
      pts.forEach(function (p, n) {
        var q = rs[n], px = p.x * W, py = p.y * H, dx = q.bx - px, dy = q.ay - py, len = Math.sqrt(dx * dx + dy * dy), ang = Math.atan2(dy, dx) * 180 / Math.PI;
        var cap = (bw - 2 * padH - 2) / (fs * 0.53), f2 = p.linha2.length > cap ? Math.max(8.5, fs * cap / p.linha2.length) : fs;
        if (len > 3) kids.push(h('div', { key: 'l' + p.id, 'aria-hidden': 'true', 'data-linha': p.id, style: { position: 'absolute', left: px, top: py - 0.5, width: len, height: 1, background: 'rgba(' + p.rgb + ', 0.55)', transformOrigin: '0 50%', transform: 'rotate(' + ang.toFixed(2) + 'deg)', zIndex: 1 } }));
        kids.push(h('div', { key: 'b' + p.id, 'data-bloco': p.id, title: p.titulo, style: { position: 'absolute', left: q.l, top: q.t, width: bw, height: bh, boxSizing: 'border-box', padding: (app ? 2 : 3) + 'px ' + padH + 'px', overflow: 'hidden', zIndex: 2, borderRadius: app ? 7 : 9,
          background: 'rgba(var(--cap-card-rgb, 13,19,41), 0.86)', border: '1px solid rgba(' + p.rgb + ', 0.4)', color: 'var(--cap-ink, #eaf1ff)', fontSize: fs, lineHeight: '1.15', textAlign: 'center', display: 'flex', flexDirection: 'column', justifyContent: 'center' } },
          h('span', { key: 'a', 'data-l1': '1', style: { display: 'block', fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' } }, p.linha1),
          h('span', { key: 'c', 'data-l2': '1', style: { display: 'block', fontSize: f2, fontWeight: 500, color: 'var(--cap-ink2, #b1bdd6)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontVariantNumeric: 'tabular-nums' } }, p.linha2)));
      });
      v.pontos.forEach(function (p) {
        kids.push(h('div', { key: 'p' + p.id, 'data-ponto': p.id, 'data-nivel': p.nivel, title: p.titulo, style: { position: 'absolute', left: p.x * W - r, top: p.y * H - r, width: 2 * r, height: 2 * r, boxSizing: 'border-box', borderRadius: '50%', background: p.cor, zIndex: 3,
          boxShadow: '0 0 0 2px rgba(var(--cap-card-rgb, 13,19,41), 1), 0 0 0 ' + (app ? 5 : 6) + 'px rgba(' + p.rgb + ', 0.28)' } }));
      });
      return h('div', { role: 'group', 'aria-label': o.rotulo || 'Desenho esquemático do barco com os sensores e o valor de agora', 'data-desenho': v.img, style: { position: 'relative', flexShrink: 0, width: W, height: H, margin: mt + 'px 0 ' + mb + 'px' } }, kids);
    } catch (e) { return null; }
  }

  window.CapitaoSensores = { vistas: vistas, elemento: elemento, contagem: contagem, valorCampo: valorCampo };
})();
