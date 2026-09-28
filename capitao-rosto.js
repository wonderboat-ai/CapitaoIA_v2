/* Capitão IA — rosto que fala (núcleo de voz) · versão final (malha 3D).
   Cabeça de perfil olhando para a direita, feita de uma grade regular de pontos sobre uma superfície 3D: perfil do meio
   em curvas Bézier (testa inclinada, nariz, lábios, queixo e pescoço longo), seções transversais para dar volume, luz
   pela normal e contorno ciano na frente; por dentro vai para violeta, com magenta na maçã do rosto; a nuca e o alto da
   cabeça somem no escuro. Por baixo da malha, uma névoa pré-desenhada (a própria malha desfocada) dá o brilho neon.
   - OUVINDO (ciano): o rosto respira; partículas finas chegam da direita (rajada a cada trecho reconhecido) e são
     absorvidas; cada trecho manda uma onda de brilho pela malha e acende a borda.
   - PENSANDO (violeta): turbilhão de neurônios no crânio (o centro gira mais rápido), com rastros, disparos e ligações
     curtas entre vizinhos; névoa do "cérebro" pulsando atrás; ondas recolhidas.
   - FALANDO (azul): a boca abre e fecha (a mandíbula gira na articulação) num ciclo por sílaba enquanto há som; cada
     palavra (pulso) recomeça a abertura com a força dela, e sem onboundary (vozes do Android) as sílabas seguem sozinhas;
     entre sílabas e sem som ela fecha. Da boca sai uma fita de senoides finas entrelaçadas (ciano → azul → violeta →
     magenta) com faíscas e arcos de frente de onda até a borda direita; a borda do perfil acende com a voz.
   - LIVRE: tudo esmaece e o laço para.
   Uso: CapitaoRosto.preparar(prazo)  (opcional, com o app ocioso: calcula a malha antes do 1º núcleo; com o IdleDeadline,
        em pedaços — devolve false enquanto faltar)
        var r = CapitaoRosto.criar(canvas, { reduzido, dprMax: 2, fpsMax: 60, crescer: 0.35 });
        r.estado('ouvindo'|'pensando'|'falando'|'livre'); r.pulso(0..1); r.som(true|false);
        r.palco(x, y, w, h); r.redimensionar(); r.pausar(); r.retomar(); r.destruir(); r.quadro(t) (só teste); r.ms
        r.aquecer() (escondido e pausado: adianta o 1º quadro em passos; true = pronto)
   'crescer': quanto o rosto pode subir além do palco (fração do palco), sem entrar na coluna do SOS/HUD.
   Desempenho: um só requestAnimationFrame (limitador que acompanha telas de 60/75/90/120 Hz), para com a aba escondida,
   em pausar() e no 'livre'; DPR ≤ 2. A malha (~3.000 pontos) é calculada uma vez por escala e guardada (girar o celular
   não refaz). Os pontos são carimbados em JS em buffers de pixels (putImageData; nada de arc nem shadowBlur por quadro):
   um fixo por estado, carimbado uma vez por layout (a troca de estado cruza dois drawImage, sem recarimbar a malha) e,
   falando, só o pedaço da boca é recarimbado. Arcos e partículas ficam na faixa entre o HUD e o rótulo. Névoa, halo e
   degradês são pré-desenhados; faíscas, partículas, cintilar e neurônios vão em lotes (rect + um fill por cor/nível). Quadro caro
   (> 5 ms): a boca vai a 30 Hz; > 12 ms: menos fios/faíscas, sem cintilar e sem brilho difuso, depois 30 fps.
   r.tempos(), r.nivel(), r.pontos(): diagnóstico para o teste de desempenho. */
(function () {
  if (window.CapitaoRosto) return;
  var PI = Math.PI, TAU = 2 * PI;
  function lim(v, a, b) { return v < a ? a : v > b ? b : v; }
  function suave(a, b, v) { var t = lim((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); }
  function mis(a, b, t) { return a + (b - a) * t; }
  function gerador(s) { // números "aleatórios" com semente: quadro(t) sai sempre igual
    return function () { s = (s + 0x6D2B79F5) | 0; var t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }

  // ---------- cores da marca (WonderHUB.AI) — sem dourado ----------
  var CIANO = [0, 244, 253], AZUL = [0, 161, 254], VIOLETA = [162, 43, 253], INDIGO = [31, 83, 250], INDIGO2 = [21, 53, 254], MAGENTA = [196, 62, 251], MAGENTA2 = [205, 58, 254], BRANCO = [255, 255, 255];
  function cmis(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
  function rgb(c, k) { k = k == null ? 1 : k; return 'rgb(' + Math.round(lim(c[0] * k, 0, 255)) + ',' + Math.round(lim(c[1] * k, 0, 255)) + ',' + Math.round(lim(c[2] * k, 0, 255)) + ')'; }
  function rgba(c, a) { return 'rgba(' + Math.round(c[0]) + ',' + Math.round(c[1]) + ',' + Math.round(c[2]) + ',' + lim(a, 0, 1).toFixed(3) + ')'; }
  function degrade(stops, h, o) { // h 0..1 sobre paradas igualmente espaçadas (o = vetor de saída, opcional)
    var f = lim(h, 0, 1) * (stops.length - 1), i = Math.min(stops.length - 2, Math.floor(f)), t = f - i, a = stops[i], b = stops[i + 1];
    o = o || [0, 0, 0]; o[0] = a[0] + (b[0] - a[0]) * t; o[1] = a[1] + (b[1] - a[1]) * t; o[2] = a[2] + (b[2] - a[2]) * t; return o;
  }

  // ---------- geometria da cabeça (unidades: 1 = raiz do cabelo → queixo; x para a frente, y para baixo, z para o lado visível) ----------
  // perfil do meio (frente), de cima para baixo: [x, y, tensão] — cada trecho vira uma Bézier cúbica
  var FRENTE = [
    [-0.48, -0.255], [-0.30, -0.230], [-0.17, -0.155], [-0.09, -0.060],                                            // alto da cabeça
    [-0.045, 0.040], [-0.015, 0.140], [0.005, 0.240], [0.018, 0.300], [0.012, 0.345], [-0.002, 0.372, 0.6],        // testa (~10°), glabela, násio
    [0.012, 0.410], [0.045, 0.460], [0.085, 0.510], [0.125, 0.550], [0.160, 0.578], [0.182, 0.598],               // dorso do nariz
    [0.184, 0.613], [0.170, 0.627], [0.135, 0.638], [0.095, 0.646], [0.062, 0.657, 0.5],                           // ponta, columela, subnasal
    [0.058, 0.675], [0.064, 0.700], [0.076, 0.724], [0.086, 0.740, 0.7], [0.082, 0.753], [0.066, 0.763], [0.052, 0.768, 0.3], // lábio de cima, estômio
    [0.064, 0.776], [0.078, 0.792], [0.080, 0.808], [0.070, 0.828], [0.048, 0.848], [0.034, 0.866, 0.7],          // lábio de baixo, sulco
    [0.040, 0.892], [0.052, 0.925], [0.048, 0.955], [0.028, 0.985], [-0.010, 1.008],                               // queixo, mento
    [-0.070, 1.024], [-0.150, 1.040], [-0.215, 1.062, 0.8], [-0.245, 1.100], [-0.255, 1.180], [-0.250, 1.280], [-0.242, 1.450], [-0.240, 1.560] // pescoço longo
  ];
  // perfil de trás (nuca), de cima para baixo
  var NUCA = [
    [-0.48, -0.255], [-0.66, -0.210], [-0.82, -0.120], [-0.94, 0.020], [-1.005, 0.200], [-1.02, 0.380], [-0.99, 0.560],
    [-0.93, 0.720], [-0.875, 0.860], [-0.85, 1.0], [-0.84, 1.2], [-0.845, 1.42], [-0.85, 1.56]
  ];
  var TOPO = -0.255, BASE = 1.40, Y_EST = 0.768;

  function curva(p, n) { // Bézier cúbica por trecho (tangentes de Catmull-Rom; tensão 0 = quina)
    var out = [], i, k;
    for (i = 0; i < p.length - 1; i++) {
      var a = p[i - 1] || p[i], b = p[i], c = p[i + 1], d = p[i + 2] || c;
      var t1 = b[2] == null ? 1 : b[2], t2 = c[2] == null ? 1 : c[2];
      var c1x = b[0] + (c[0] - a[0]) / 6 * t1, c1y = b[1] + (c[1] - a[1]) / 6 * t1;
      var c2x = c[0] - (d[0] - b[0]) / 6 * t2, c2y = c[1] - (d[1] - b[1]) / 6 * t2;
      for (k = 0; k < n; k++) {
        var t = k / n, u = 1 - t, A = u * u * u, B = 3 * u * u * t, C = 3 * u * t * t, D = t * t * t;
        out.push([A * b[0] + B * c1x + C * c2x + D * c[0], A * b[1] + B * c1y + C * c2y + D * c[1]]);
      }
    }
    var f = p[p.length - 1]; out.push([f[0], f[1]]);
    return out;
  }
  function tabela(poly, y0, y1, n) { // x(y) com passo fixo (curva monótona em y)
    var t = new Float32Array(n + 1), j = 0, i;
    for (i = 0; i <= n; i++) {
      var y = y0 + (y1 - y0) * i / n;
      while (j < poly.length - 2 && poly[j + 1][1] < y) j++;
      var a = poly[j], b = poly[j + 1], k = b[1] === a[1] ? 0 : lim((y - a[1]) / (b[1] - a[1]), 0, 1);
      t[i] = a[0] + (b[0] - a[0]) * k;
    }
    return { t: t, y0: y0, y1: y1, n: n };
  }
  function le(tb, y) {
    var f = lim((y - tb.y0) / (tb.y1 - tb.y0), 0, 1) * tb.n, i = Math.floor(f);
    if (i >= tb.n) return tb.t[tb.n];
    return tb.t[i] + (tb.t[i + 1] - tb.t[i]) * (f - i);
  }
  function funcao(nos) { // função suave de y a partir de nós [y, valor]
    var p = [], i; for (i = 0; i < nos.length; i++) p.push([nos[i][1], nos[i][0]]);
    return tabela(curva(p, 12), nos[0][0], nos[nos.length - 1][0], 700);
  }
  var POLY_F = curva(FRENTE, 16), POLY_N = curva(NUCA, 16);
  var T_FRENTE = tabela(POLY_F, TOPO, 1.56, 1600), T_NUCA = tabela(POLY_N, TOPO, 1.56, 1600);
  // plano do rosto sem nariz/lábios/queixo (o que sobra vira relevo no meio)
  var T_PLANO = funcao([[0.18, 0.08], [0.24, 0.045], [0.30, -0.012], [0.36, -0.048], [0.46, -0.058], [0.58, -0.052], [0.66, -0.042], [0.76, -0.034], [0.88, -0.030], [0.96, -0.022], [1.02, -0.03]]);
  // meia largura lateral do relevo do meio (nariz estreito, boca e queixo mais largos)
  var T_SIG = funcao([[0.18, 0.26], [0.27, 0.20], [0.335, 0.10], [0.37, 0.066], [0.45, 0.054], [0.56, 0.058], [0.61, 0.068], [0.645, 0.078], [0.672, 0.100], [0.70, 0.118], [0.75, 0.126], [0.80, 0.120], [0.86, 0.106], [0.93, 0.100], [1.02, 0.100]]);
  // meia largura da cabeça (seção principal)
  var T_W = funcao([[TOPO, 0.0], [-0.245, 0.11], [-0.215, 0.19], [-0.15, 0.27], [-0.06, 0.335], [0.04, 0.372], [0.18, 0.395], [0.35, 0.400], [0.50, 0.390], [0.64, 0.368], [0.76, 0.342], [0.84, 0.312], [0.90, 0.272], [0.95, 0.215], [0.985, 0.145], [1.006, 0.02]]);
  // trás da seção principal: crânio até 0,55; depois recua para o ramo e a borda da mandíbula
  var T_COSTAS = funcao([[0.50, -0.955], [0.60, -0.905], [0.70, -0.78], [0.78, -0.64], [0.84, -0.53], [0.90, -0.37], [0.95, -0.215], [0.985, -0.09], [1.006, -0.02]]);
  // expoente da frente (maior = rosto mais chapado na frente) e posição do ponto mais largo
  var T_NF = funcao([[TOPO, 2.0], [-0.1, 2.1], [0.1, 2.3], [0.30, 2.45], [0.55, 2.55], [0.75, 2.4], [0.9, 2.1], [1.006, 2.0]]);
  var T_KAP = funcao([[TOPO, 0.5], [0.2, 0.44], [0.6, 0.42], [0.84, 0.36], [1.006, 0.34]]);
  var T_NB = funcao([[0.55, 2.0], [0.74, 2.0], [0.86, 1.45], [1.006, 1.35]]);
  // pescoço: frente (escondida sob a mandíbula até o mento), meia largura e ponta da frente
  var T_PFRENTE = funcao([[0.60, -0.44], [0.75, -0.37], [0.86, -0.30], [0.93, -0.20], [0.975, -0.09], [1.003, -0.006]]);
  var T_PW = funcao([[0.60, 0.20], [0.80, 0.245], [0.95, 0.262], [1.05, 0.268], [1.15, 0.272], [1.40, 0.278]]);
  var T_PKAP = funcao([[0.60, 0.30], [0.80, 0.36], [0.95, 0.45], [1.08, 0.47], [1.2, 0.5], [1.40, 0.5]]);
  var T_PNF = funcao([[0.60, 1.5], [0.85, 1.8], [0.99, 2.1], [1.06, 2.1], [1.15, 2.2], [1.40, 2.2]]);

  // relevos locais (gaussianas 3D sobre a seção principal): [x, y, z, sx, sy, sz, altura]
  var RELEVOS = [
    [-0.105, 0.405, 0.160, 0.080, 0.056, 0.080, -0.026], // órbita do olho (rasa: sem "viseira")
    [-0.050, 0.330, 0.160, 0.110, 0.060, 0.120, 0.009],  // arco da sobrancelha (suave)
    [-0.290, 0.210, 0.385, 0.110, 0.110, 0.110, -0.018], // têmpora
    [-0.190, 0.505, 0.330, 0.090, 0.075, 0.090, 0.022],  // maçã do rosto
    [-0.220, 0.675, 0.330, 0.090, 0.080, 0.090, -0.012], // bochecha abaixo da maçã
    [-0.052, 0.776, 0.150, 0.030, 0.026, 0.030, -0.018], // canto da boca
    [-0.020, 0.700, 0.135, 0.030, 0.040, 0.030, -0.008], // sulco nasolabial (leve)
    [-0.050, 0.632, 0.080, 0.024, 0.034, 0.024, -0.020]  // vinco atrás da asa do nariz
  ];
  // volumes somados à superfície (elipsoides): [x, y, z, rx, ry, rz]
  var VOLUMES = [
    [0.032, 0.626, 0.050, 0.064, 0.040, 0.048], // asa do nariz
    [-0.148, 0.416, 0.165, 0.058, 0.050, 0.060] // globo do olho sob a pálpebra fechada
  ];
  var XA = -0.45, NT = 360, DT = PI / NT, TF = 0.55; // eixo das seções, resolução angular, quanto do lado de lá entra
  var YAW = 10 * PI / 180, PITCH = 8 * PI / 180; // rosto levemente virado para quem olha
  var CY = Math.cos(YAW), SY = Math.sin(YAW), CP = Math.cos(PITCH), SP = Math.sin(PITCH);
  function vista(x, y, z, o) { // modelo → vista (ortográfica); o = [X, Y, Z]
    var x1 = x * CY - z * SY, z1 = x * SY + z * CY;
    o[0] = x1; o[1] = y * CP - z1 * SP; o[2] = y * SP + z1 * CP; return o;
  }
  // canto da boca e articulação da mandíbula (pivô da abertura)
  var CANTO = [-0.052, 0.776, 0.150], ATM = [-0.50, 0.47];
  function bordaMand(y) { return le(T_COSTAS, y); }

  function polar(pts, n, out) { // polilinha (x, z) → raio máximo por ângulo em torno do eixo
    var ta = 0, ra = 0, i, j;
    for (i = 0; i < n; i++) {
      var dx = pts[2 * i] - XA, dz = pts[2 * i + 1], tb = Math.atan2(dz, dx), rb = Math.sqrt(dx * dx + dz * dz);
      if (tb < 0) tb = 0;
      if (i > 0) {
        var a = ta, b = tb, r1 = ra, r2 = rb, s;
        if (b < a) { s = a; a = b; b = s; s = r1; r1 = r2; r2 = s; }
        var j0 = Math.ceil(a / DT), j1 = Math.min(NT, Math.floor(b / DT));
        for (j = j0; j <= j1; j++) { var r = b > a ? r1 + (r2 - r1) * (j * DT - a) / (b - a) : Math.max(r1, r2); if (r > out[j]) out[j] = r; }
      }
      ta = tb; ra = rb;
    }
  }
  function smax(a, b, k) { var h = Math.max(k - Math.abs(a - b), 0) / k; return Math.max(a, b) + h * h * k * 0.25; }
  var PTS = new Float32Array(1200);
  function superelipse(xf, xb, W, nf, kap, dl, sg, nb) { // meia seção (z ≥ 0): frente achatada + relevo do meio; volta nº de pontos
    var cx = xb + (xf - xb) * kap, af = xf - cx, ab = cx - xb, n = 0, i, M = 240, e = 2 / nf, eb = 2 / (nb || 2);
    for (i = 0; i <= M; i++) {
      var ph = Math.pow(i / M, 1.35) * PI / 2, z = W * Math.pow(Math.sin(ph), e), x = cx + af * Math.pow(Math.cos(ph), e);
      if (dl > 0) x += dl * Math.exp(-(z * z) / (sg * sg));
      PTS[n++] = x; PTS[n++] = z;
    }
    for (i = 1; i <= 90; i++) { var q = PI / 2 + i / 90 * PI / 2; PTS[n++] = cx - ab * Math.pow(-Math.cos(q), eb); PTS[n++] = W * Math.pow(Math.sin(q), eb); }
    return n / 2;
  }
  function fatia(y) { // raio r(θ) da seção horizontal na altura y (θ = 0 é a frente)
    var r = new Float32Array(NT + 1), rp, rv, j, n, k;
    if (y > TOPO && y < 1.006) { // crânio + rosto + mandíbula
      var xp = le(T_FRENTE, y), pl = le(T_PLANO, y), xf = Math.min(xp, pl), xb = y < 0.5 ? le(T_NUCA, y) : le(T_COSTAS, y);
      if (y >= 0.5 && y < 0.6) xb = mis(le(T_NUCA, y), le(T_COSTAS, y), suave(0.5, 0.6, y));
      var W = le(T_W, y);
      if (W > 0.004 && xf > xb) {
        n = superelipse(xf, xb, W, le(T_NF, y), le(T_KAP, y), xp - xf, le(T_SIG, y), y > 0.55 ? le(T_NB, y) : 2);
        polar(PTS, n, r);
        for (k = 0; k < RELEVOS.length; k++) { // relevos só na seção principal
          var R = RELEVOS[k], gy = (y - R[1]) / R[4]; gy *= gy; if (gy > 9) continue;
          for (j = 0; j <= NT; j++) {
            if (r[j] <= 0) continue;
            var th = j * DT, px = XA + r[j] * Math.cos(th), pz = r[j] * Math.sin(th), gx = (px - R[0]) / R[3], gz = (pz - R[2]) / R[5], g = gx * gx + gy + gz * gz;
            if (g < 9) r[j] += R[6] * Math.exp(-g);
          }
        }
      }
    }
    if (y >= 0.6) { // pescoço (frente em ponta sob o queixo, arredondada na garganta); união larga com a mandíbula (sem "colar")
      rp = new Float32Array(NT + 1);
      var nf = y >= 1.003 ? Math.min(le(T_FRENTE, y), -0.006) : le(T_PFRENTE, y), nb = le(T_NUCA, y);
      n = superelipse(nf, nb, le(T_PW, y), le(T_PNF, y), le(T_PKAP, y), 0, 1);
      polar(PTS, n, rp);
      for (j = 0; j <= NT; j++) r[j] = smax(r[j], rp[j], 0.07);
    }
    for (k = 0; k < VOLUMES.length; k++) { // asa do nariz, olho
      var V = VOLUMES[k], q = (y - V[1]) / V[4]; if (q * q >= 1) continue;
      var s = Math.sqrt(1 - q * q), ax = V[3] * s, az = V[5] * s; n = 0;
      for (j = 0; j <= 48; j++) { var a = j / 48 * TAU; PTS[n++] = V[0] + ax * Math.cos(a); PTS[n++] = Math.max(0, V[2] + az * Math.sin(a)); }
      rv = new Float32Array(NT + 1); polar(PTS, n / 2, rv);
      for (j = 0; j <= NT; j++) if (rv[j] > 0) r[j] = smax(r[j], rv[j], 0.012);
    }
    return r;
  }
  function pesoMand(x, y, z) { // quanto o ponto acompanha a mandíbula (0 = parado, 1 = gira junto)
    var d, mole;
    if (x > CANTO[0]) { var q = z / 0.15; d = y - (Y_EST + 0.007 * q * q); mole = 0.004 + 0.01 * lim(q - 0.8, 0, 1); }
    else {
      var dx = ATM[0] - CANTO[0], dy = ATM[1] - CANTO[1], L = Math.sqrt(dx * dx + dy * dy), rx = x - CANTO[0], ry = y - CANTO[1];
      d = (dy * rx - dx * ry) / L; mole = 0.008 + lim((rx * dx + ry * dy) / (L * L), 0, 1) * 0.16;
    }
    var w = suave(-mole, mole, d) * suave(-0.60, -0.47, x); // atrás do ramo da mandíbula (orelha, nuca) nada se mexe
    w *= 1 - suave(1.0, 1.2, y);
    if (y > 0.78) w *= 1 - suave(-0.06, 0.2, bordaMand(y) - x) * suave(0.78, 0.86, y); // a pele sob a mandíbula estica (sem dobra)
    var ra = Math.sqrt((x - ATM[0]) * (x - ATM[0]) + (y - ATM[1]) * (y - ATM[1]));
    return w * suave(0.05, 0.25, ra);
  }

  // Malha: linhas horizontais igualmente espaçadas; em cada linha, pontos a cada h de arco medidos a partir do lado (θ = 90°).
  // Devolve pontos em unidades de cabeça já na vista, com normal.
  function alturas(h) { // alturas das linhas (seções) da malha de espaçamento h
    var y0 = Y_EST - h * 0.5, k0 = Math.floor((y0 - TOPO) / h), ys = [], i;
    for (i = -k0 - 1; ; i++) { var yy = y0 + i * h; if (yy > BASE + h) break; ys.push(yy); }
    return ys;
  }
  var JF = Math.round(TF / DT), NJ = NT + JF + 1, SARR = new Float32Array(NJ), VL = [0, 0, 0];
  function constroi(h) {
    var ys = alturas(h), R = [], P = [], i;
    for (i = 0; i < ys.length; i++) R.push(fatia(ys[i]));
    for (i = 1; i < ys.length - 1; i++) linha(R, ys, i, h, P);
    return P;
  }
  function linha(R, ys, i, h, P) { // pontos da linha i (usa as seções i − 1, i e i + 1)
    var j, v = VL, sArr = SARR;
    var r = R[i], y = ys[i];
    if (r[NT >> 1] <= 0) return;
    var ok = true; for (j = 0; j <= NT; j++) if (r[j] <= 0) { ok = false; break; }
    if (!ok) return;
    // comprimento de arco de θ = −TF até π
    var px0 = 0, pz0 = 0;
    for (j = 0; j < NJ; j++) {
      var jj = j - JF, th = jj * DT, rr = r[Math.abs(jj)], px = XA + rr * Math.cos(th), pz = rr * Math.sin(th);
      sArr[j] = j ? sArr[j - 1] + Math.sqrt((px - px0) * (px - px0) + (pz - pz0) * (pz - pz0)) : 0; px0 = px; pz0 = pz;
    }
    var sRef = sArr[JF + (NT >> 1)], kmin = Math.ceil((0 - sRef) / h), kmax = Math.floor((sArr[NJ - 1] - sRef) / h), a = 0;
    for (var kk = kmin; kk <= kmax; kk++) {
      var s = sRef + kk * h;
      while (a < NJ - 2 && sArr[a + 1] < s) a++;
      var f = sArr[a + 1] > sArr[a] ? (s - sArr[a]) / (sArr[a + 1] - sArr[a]) : 0, ja = a - JF, jb = ja + 1;
      var t = (ja + f) * DT, ra = r[Math.abs(ja)], rb = r[Math.abs(jb)], rr2 = ra + (rb - ra) * f;
      if (t < 0 && y > 0.99) continue; // sob o queixo, o lado de lá não entra (sem ganchos na borda)
      var up = R[i - 1], dn = R[i + 1], rU = up[Math.abs(ja)] + (up[Math.abs(jb)] - up[Math.abs(ja)]) * f, rD = dn[Math.abs(ja)] + (dn[Math.abs(jb)] - dn[Math.abs(ja)]) * f;
      var rt = (rb - ra) / DT, ry = (rD - rU) / (2 * h);
      if (rU <= 0) ry = (rD - rr2) / h; else if (rD <= 0) ry = (rr2 - rU) / h;
      var ct = Math.cos(t), st = Math.sin(t), x = XA + rr2 * ct, z = rr2 * st;
      var tx = rt * ct - rr2 * st, tz = rt * st + rr2 * ct, yx = ry * ct, yz = ry * st;
      var nx = tz, ny = tx * yz - tz * yx, nz = -tx, nl = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
      nx /= nl; ny /= nl; nz /= nl;
      vista(nx, ny, nz, v); var vnx = v[0], vny = v[1], vnz = v[2];
      if (vnz < 0.03) continue; // de costas para a câmera
      vista(x, y, z, v);
      P.push({ x: x, y: y, z: z, X: v[0], Y: v[1], nx: vnx, ny: vny, nz: vnz });
    }
  }

  // ---------- traços finos em 3D: olho fechado, asa do nariz, linha dos lábios ----------
  function cilios() { // pálpebra fechada: linha dos cílios (curva para baixo), pontas dos cílios e vinco da pálpebra
    var E = VOLUMES[1], pts = [], i, v = [0, 0, 0];
    for (i = 0; i <= 16; i++) {
      var t = i / 16, a = mis(-0.80, 1.95, t), sag = Math.sin(PI * Math.pow(t, 0.85));
      var R = 1.06 + 0.10 * t, x = E[0] + E[3] * R * Math.cos(a) - 0.012 * t, z = E[2] + E[5] * R * Math.sin(a), y = E[1] + 0.002 + 0.016 * sag - 0.006 * t;
      vista(x, y, z, v); var m = [v[0], v[1]];
      var L = 0.010 + 0.016 * Math.pow(sag, 0.7); // cílio: para fora, para baixo e um pouco à frente
      vista(x + L * (0.55 * Math.cos(a) + 0.35), y + L * 0.9, z + L * 0.55 * Math.sin(a), v); var pc = [v[0], v[1]];
      vista(E[0] + E[3] * (1.15 + 0.1 * t) * Math.cos(a * 0.95) - 0.01 * t, E[1] - 0.026 - 0.012 * sag + 0.008 * t, E[2] + E[5] * 1.15 * Math.sin(a * 0.95), v); // vinco
      pts.push({ x: m[0], y: m[1], px: pc[0], py: pc[1], vx: v[0], vy: v[1], w: sag });
    }
    return pts;
  }
  function asa() { // vinco da asa do nariz (curva em C em volta da asa, vista de lado)
    var A = VOLUMES[0], pts = [], i, v = [0, 0, 0];
    for (i = 0; i <= 12; i++) {
      var a = mis(0.52, 1.38, i / 12) * PI; // de cima, por trás, até a base da narina (um C aberto para a frente)
      vista(A[0] - 0.006 + A[3] * 0.80 * Math.cos(a), A[1] + 0.004 - A[4] * 0.85 * Math.sin(a), A[2] + A[5] * 0.8, v);
      pts.push([v[0], v[1]]);
    }
    return pts;
  }
  function fenda() { // linha dos lábios (estômio → canto da boca) sobre a própria superfície; w = quanto segue a mandíbula
    var r = fatia(Y_EST), pts = [], i, v = [0, 0, 0], tc = Math.atan2(CANTO[2], CANTO[0] - XA);
    for (i = 0; i <= 12; i++) {
      var t = i / 12, th = tc * t, rr = r[Math.min(NT, Math.round(th / DT))] - 0.003;
      vista(XA + rr * Math.cos(th), Y_EST + 0.008 * t * t, rr * Math.sin(th), v);
      pts.push({ X: v[0], Y: v[1], w: 1 - 0.6 * t });
    }
    return pts;
  }
  function bochecha(x, y) { // maçã do rosto e bochecha: volume magenta (como na 3.webp)
    var a = (x + 0.19) / 0.15, b = (y - 0.57) / 0.13, c = (x - 0.01) / 0.09, d = (y - 0.72) / 0.07;
    return Math.max(Math.exp(-(a * a + b * b)), 0.5 * Math.exp(-(c * c + d * d)));
  }

  // ---------- malha guardada por escala (girar o celular não refaz; CapitaoRosto.preparar() adianta) ----------
  var LUZ = (function () { var l = [0.80, -0.30, 0.45], n = Math.sqrt(l[0] * l[0] + l[1] * l[1] + l[2] * l[2]); return [l[0] / n, l[1] / n, l[2] / n]; })();
  var NH = 12; // faixas de cor dos pontos
  var H_MALHA = 0.0212; // espaçamento padrão da grade (unidades de cabeça): ~2.900 pontos
  var MALHAS = {};
  function guardada(h) { // serve uma malha guardada se a escala mudou menos de 18%
    for (var k in MALHAS) if (Math.abs(MALHAS[k].h - h) / h < 0.18) return MALHAS[k];
    return null;
  }
  function acha(h) { return guardada(h) || malha(h); }
  function malha(h) {
    var chave = 'h' + Math.round(h * 20000);
    if (MALHAS[chave]) return MALHAS[chave];
    var P = constroi(h), lista = [], i;
    for (i = 0; i < P.length; i++) luz(P[i], lista);
    return fecha(h, lista);
  }
  // preparar(prazo), com o app ocioso: a mesma malha, em pedaços (seções → linhas → luz) que cabem no tempo livre que o
  // navegador dá (IdleDeadline) — um toque na tela não espera o cálculo inteiro. false = falta (chamar no próximo ocioso).
  var PREP = null;
  function preparar(prazo) {
    var h = H_MALHA, st = PREP;
    if (guardada(h)) { PREP = null; return true; }
    if (!prazo || typeof prazo.timeRemaining !== 'function') { acha(h); PREP = null; return true; }
    if (!st || st.h !== h) st = PREP = { h: h, ys: alturas(h), R: [], i: 1, P: [], k: 0, lista: [] };
    var falta = function () { return prazo.timeRemaining() < 3; };
    while (st.R.length < st.ys.length) { st.R.push(fatia(st.ys[st.R.length])); if (falta()) return false; }
    while (st.i < st.ys.length - 1) { linha(st.R, st.ys, st.i++, h, st.P); if (falta()) return false; }
    while (st.k < st.P.length) { luz(st.P[st.k++], st.lista); if ((st.k & 63) === 0 && falta()) return false; }
    if (!st.luz) { st.luz = true; return false; } // o fechamento (ordenar, vetores, perfil) num ocioso só dele
    fecha(h, st.lista);
    PREP = null; return true;
  }
  function luz(p, lista) { // cor, brilho e grupo de um ponto da malha (entra na lista se aparece)
    var nx = p.nx, ny = p.ny, nz = p.nz;
    var facing = nz, rim = Math.pow(1 - facing, 2.4) * suave(0.1, 0.7, nx);
    var topo = Math.pow(1 - facing, 3) * suave(0.1, 0.8, -ny) * 0.35;
    var dif = Math.max(0, (nx * LUZ[0] + ny * LUZ[1] + nz * LUZ[2] + 0.35) / 1.35); // luz "envolvente": sombra suave
    var xr = Math.min(le(T_FRENTE, Math.min(p.y, 0.98)), le(T_PLANO, p.y) + 0.02);
    var u = lim((xr - p.x) / 0.95, 0, 1.2);
    // a nuca e o alto da cabeça somem no escuro (em diagonal: sem corte reto em cima); o pescoço apaga antes do rótulo
    var fade = suave(-0.98, -0.30, p.x - 0.6 * Math.max(0, 0.16 - p.y) - 0.45 * Math.max(0, p.y - 0.72)) * suave(TOPO + 0.01, -0.02, p.y) * (1 - suave(1.04, 1.36, p.y));
    // luz principal + contorno + luz rebatida por baixo (a parte de baixo da mandíbula não vira faixa escura)
    var b = (0.2 + 0.8 * dif + 1.1 * rim + topo + 0.45 * Math.max(0, ny)) * fade;
    b *= 0.72 + 0.28 * Math.sqrt(Math.max(facing, 0.05)) + 0.35 * rim; // borda densa não estoura
    if (b < 0.05) return;
    var boch = bochecha(p.x, p.y) * (1 - rim) * suave(0.05, 0.2, p.z);
    var hue = lim(u * 2.5 - rim * 0.9 - dif * 0.1 + 0.10 + boch * 0.65, 0, 1);
    var jw = pesoMand(p.x, p.y, p.z);
    var lab = 0; // lábio inferior (1) desce um pouco mais; superior (−1) sobe um pouco
    if (p.x > CANTO[0] - 0.02 && p.z < 0.16) { if (p.y > Y_EST && p.y < 0.86) lab = 1 - suave(0.80, 0.86, p.y); else if (p.y < Y_EST && p.y > 0.70) lab = -suave(0.70, 0.75, p.y); }
    var dmx = p.x - 0.06, dmy = p.y - Y_EST, md = Math.exp(-(dmx * dmx + dmy * dmy) / 0.012);
    var grupo = boch > 0.35 ? 3 : (u < 0.1 || rim > 0.3) ? 0 : u < 0.3 ? 1 : 2; // cor da névoa: frente, meio, fundo, maçã
    lista.push({ X: p.X, Y: p.Y, b: Math.min(b, 1.6), hb: Math.min(NH - 1, Math.floor(hue * NH)), u: u, j: jw, l: lab, m: md, w: rim, g: grupo });
  }
  function fecha(h, lista) { // lista de pontos → malha guardada (vetores por faixa de cor, grupos, perfil, traços finos)
    var chave = 'h' + Math.round(h * 20000), i, v = [0, 0, 0];
    lista.sort(function (a, b) { return a.hb - b.hb; });
    var n = lista.length, M = { h: h, N: n, X: new Float32Array(n), Y: new Float32Array(n), b: new Float32Array(n), u: new Float32Array(n), j: new Float32Array(n), l: new Float32Array(n), m: new Float32Array(n), ph: new Float32Array(n), g: new Uint8Array(n), bin: new Int32Array(NH + 1), alvos: [] };
    for (i = 0; i <= NH; i++) M.bin[i] = n;
    for (i = n - 1; i >= 0; i--) {
      var q = lista[i]; M.bin[q.hb] = i;
      M.X[i] = q.X; M.Y[i] = q.Y; M.b[i] = q.b; M.u[i] = q.u; M.j[i] = q.j; M.l[i] = q.l; M.m[i] = q.m; M.g[i] = q.g;
      M.ph[i] = ((i * 2654435761) % 1000) / 1000; // fase do cintilar
      if (q.w > 0.35 && q.Y > 0.1 && q.Y < 1.0) M.alvos.push(i);
    }
    for (i = NH - 1; i >= 0; i--) if (M.bin[i] > M.bin[i + 1]) M.bin[i] = M.bin[i + 1];
    // dois grupos: o que fica parado e o que mexe com a boca (mandíbula, lábios e o brilho da boca)
    M.sub = [0, 1].map(function (g) {
      var idx = [], bin = new Int32Array(NH + 1), b;
      for (b = 0; b < NH; b++) {
        bin[b] = idx.length;
        for (var k = M.bin[b]; k < M.bin[b + 1]; k++) { var mexe = M.j[k] > 0.06 || M.l[k] !== 0 || M.m[k] > 0.05; if (mexe === !!g) idx.push(k); }
      }
      bin[NH] = idx.length;
      return { idx: new Int32Array(idx), bin: bin };
    });
    // linha do meio (luz de contorno), do alto da cabeça ao fim do pescoço
    M.perfil = [];
    for (var y = -0.20; y <= 1.40; y += 0.006) {
      var x = le(T_FRENTE, y); vista(x, y, 0, v);
      M.perfil.push({ X: v[0], Y: v[1], j: pesoMand(x - 0.004, y, 0), yy: y, l: 1 - suave(0.80, 0.86, y) });
    }
    M.asa = asa(); M.cil = cilios(); M.fenda = fenda();
    return (MALHAS[chave] = M);
  }

  // ---------- paletas por estado ----------
  var EST = {
    ouvindo: { rosto: [CIANO, cmis(CIANO, AZUL, 0.55), cmis(AZUL, INDIGO, 0.55), cmis(INDIGO, VIOLETA, 0.7), MAGENTA], borda: CIANO, brilho: 1.0, ondas: 0, neur: 0, entrada: 1, respira: 1.0, halo: CIANO },
    pensando: { rosto: [cmis(AZUL, VIOLETA, 0.5), cmis(INDIGO, VIOLETA, 0.55), VIOLETA, cmis(VIOLETA, MAGENTA, 0.5), MAGENTA], borda: cmis(AZUL, VIOLETA, 0.6), brilho: 0.72, ondas: 0, neur: 1, entrada: 0, respira: 0.6, halo: VIOLETA },
    falando: { rosto: [cmis(CIANO, AZUL, 0.75), AZUL, cmis(INDIGO2, VIOLETA, 0.3), VIOLETA, MAGENTA2], borda: cmis(CIANO, AZUL, 0.65), brilho: 1.0, ondas: 1, neur: 0, entrada: 0, respira: 0.35, halo: AZUL },
    livre: { rosto: [cmis(CIANO, AZUL, 0.75), AZUL, cmis(INDIGO2, VIOLETA, 0.3), VIOLETA, MAGENTA2], borda: cmis(CIANO, AZUL, 0.65), brilho: 0.10, ondas: 0, neur: 0, entrada: 0, respira: 0.5, halo: AZUL } // paleta do falando, apagada
  };
  var NOMES = ['ouvindo', 'pensando', 'falando', 'livre'];
  var ONDA_CORES = [CIANO, AZUL, VIOLETA, MAGENTA2];
  var FAISCA_COR = [0, 1, 2].map(function (j) { return rgb(cmis(degrade(ONDA_CORES, (j + 0.5) / 3), BRANCO, 0.22)); });
  var FIOS = [ // fios da fita: amplitude, comprimento de onda, velocidade de fase (ondas/s), fase, largura da fita, torção
    { a: 1.00, l: 1.00, v: 0.62, f: 0.0, w: 0.34, tw: 0.90, al: 1.0 },
    { a: 0.80, l: 0.83, v: 0.78, f: 2.1, w: 0.26, tw: 1.35, al: 0.85 },
    { a: 0.64, l: 1.24, v: 0.48, f: 4.0, w: 0.30, tw: 0.72, al: 0.75 },
    { a: 0.90, l: 0.69, v: 0.92, f: 5.3, w: 0.20, tw: 1.60, al: 0.8 },
    { a: 0.52, l: 1.52, v: 0.40, f: 1.2, w: 0.24, tw: 1.10, al: 0.6 }
  ];
  // neurônios do "pensando": raio relativo, ângulo, ritmo de disparo e fase (fixos: quadro(t) sai sempre igual)
  var NN = 120, NR = new Float32Array(NN), NA = new Float32Array(NN), NFQ = new Float32Array(NN), NPH = new Float32Array(NN);
  var NW = new Float32Array(NN); // giro de cada nó (rad/s): o centro gira mais rápido
  (function () {
    var g = gerador(77);
    for (var i = 0; i < NN; i++) { NR[i] = 0.08 + 0.92 * Math.sqrt(g()); NA[i] = g() * TAU; NFQ[i] = 0.45 + g() * 1.2; NPH[i] = g() * TAU; NW[i] = 0.95 - 0.55 * NR[i]; }
  })();
  var CEREBRO = [-0.40, 0.15, 0.30, 0.22]; // centro e raios do turbilhão (unidades de cabeça): no crânio, acima do olho

  function pix(r, g, b) { // cor → pixel RGBA de 32 bits (little-endian); alfa = 2 × azul (o azul é o canal mais forte da paleta)
    r = r > 255 ? 255 : r | 0; g = g > 255 ? 255 : g | 0; b = b > 255 ? 255 : b | 0; var a = b << 1; if (a > 255) a = 255;
    return ((a << 24) | (b << 16) | (g << 8) | r) >>> 0;
  }

  function criar(canvas, opcoes) {
    opcoes = opcoes || {};
    var ctx = canvas.getContext('2d');
    var reduzido = !!opcoes.reduzido, dprMax = opcoes.dprMax || 2, fpsMax = opcoes.fpsMax || 60, crescer = opcoes.crescer == null ? 0.35 : Math.max(0, +opcoes.crescer || 0);
    var r = { ms: 0 }, vivo = true, pausado = false, manual = false, raf = 0, ultimo = 0, proxT = 0;
    var W = 0, H = 0, dpr = 1, palcoR = null, S = 100, OX = 0, OY = 0, hPx = 4, MA = null, faixaY0 = 0, faixaY1 = 1e4; // faixa (px CSS) onde arcos e partículas podem ir
    var nivel = 0, lentos = 0, rapidos = 0, tempos = [];
    var aleat = gerador((Math.random() * 1e9) | 0);
    // estado animado
    var T = 0, alvo = 'livre', peso = { ouvindo: 0, pensando: 0, falando: 0, livre: 1 };
    var energia = 0, somAlvo = 0, somNivel = 0, boca = 0, vozAtual = 0, vozS = 0, eo = 0, rajada = 0, bocaY = 0;
    var silF = 0, silA = 0.7, silN = 0, palT = -9, palEnv = 0; // ciclo de sílaba da boca, força dele, última palavra
    var HIST = new Float32Array(512), histI = -1;
    var pensaT = -9, ondasMalha = [], arcos = [], faiscas = [], chegando = [], claroes = [], entradaAcum = 0, faiscaAcum = 0;
    // geometria na tela
    var N = 0, gx = null, gy = null, gb, gh, gu, gj, gl, gm, binIni, alvos = [], perfilV = [], ciliosV = [], fendaV = [];
    var piv = [0, 0], boc = [0, 0], cabC = [0, 0], cer = [0, 0, 1, 1], asaV = [];
    var sprites = {}, bufs = null, caixa = null, caixaM = null, nevoa = null, COR3 = [0, 0, 0], OYC = new Float32Array(400), OHW = new Float32Array(400), OXS = new Float32Array(400);
    var EX = new Float32Array(160), EY = new Float32Array(160), EX0 = new Float32Array(160), EY0 = new Float32Array(160), EA = new Float32Array(160), ET = new Float32Array(160);
    var LOTE = new Int16Array(6 * 96), NLOTE = new Int16Array(6);
    var npx = new Float32Array(NN), npy = new Float32Array(NN), nbr = new Float32Array(NN), npi = new Float32Array(NN);
    var parA = new Int16Array(NN * 8), parB = new Int16Array(NN * 8), parN = new Uint8Array(NN * 8);

    // ---------- tamanho e posição ----------
    function redimensionar() {
      var b = canvas.getBoundingClientRect();
      W = Math.max(1, b.width || canvas.clientWidth || innerWidth); H = Math.max(1, b.height || canvas.clientHeight || innerHeight);
      dpr = Math.min(window.devicePixelRatio || 1, dprMax);
      canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
      arruma();
    }
    function palcoPadrao() { var s = Math.min(Math.min(W, H) * 0.64, H * 0.36, 300); return { x: (W - s) / 2, y: (H - s) / 2, w: s, h: s }; }
    var sujo = true, agEst = 0;
    function arruma() { // só marca; a geometria é refeita uma vez antes do próximo desenho
      sujo = true;
      if (reduzido) { if (!agEst) agEst = requestAnimationFrame(function () { agEst = 0; if (vivo) desenhaEstatico(); }); }
      else liga();
    }
    function garante() { if (sujo) { sujo = false; calcula(); } if (!nevoa) preparaNevoa(); }
    function calcula() {
      var p = palcoR || palcoPadrao(), ALTO = 1.42, s0 = p.h / ALTO, s = s0, nariz = 0, topo = 12, it;
      // do alto da testa (−0,12) ao fim do pescoço (1,30) cabe no palco; pode subir além dele até 'crescer' × palco.
      // Se o alto da cabeça cair na coluna do SOS/HUD (x < 150), fica abaixo deles: 118 px com o HUD (tela > 720 px), 70 px sem
      for (it = 0; it < 2; it++) {
        var extra = Math.max(0, Math.min(crescer * p.h, p.y - topo - 0.1 * s0));
        s = Math.min((p.h + extra) / ALTO, W * 0.62 / 0.85);
        nariz = Math.min(p.x + p.w * 0.5 + 0.45 * s, W * 0.56); // retrato estreito: rosto mais à esquerda, sobra espaço às ondas
        if (nariz - 0.74 * s < 150) topo = H > 720 ? 118 : 70; else break;
      }
      S = s; OX = nariz - 0.18 * S; OY = p.y + p.h - 1.30 * S;
      faixaY0 = H > 720 ? 126 : 8; faixaY1 = p.y + p.h + 0.04 * S; // abaixo do HUD e acima do rótulo/legenda/ENCERRAR
      hPx = Math.max(2.8, S * H_MALHA); // espaçamento da grade: nunca menos de 2,8 px
      var h = hPx / S;
      if (!MA || Math.abs(h - MA.h) / MA.h > 0.18) MA = acha(h);
      geometria();
    }

    function geometria() { // malha guardada → tela (barato: só escala e posição)
      var M = MA, n = M.N, i, v = [0, 0, 0];
      N = n; gb = M.b; gu = M.u; gj = M.j; gl = M.l; gm = M.m; gh = M.ph; binIni = M.bin; alvos = M.alvos;
      if (!gx || gx.length !== n) { gx = new Float32Array(n); gy = new Float32Array(n); }
      for (i = 0; i < n; i++) { gx[i] = (OX + M.X[i] * S) * dpr; gy[i] = (OY + M.Y[i] * S) * dpr; }
      function tela(x, y, z) { vista(x, y, z, v); return [(OX + v[0] * S) * dpr, (OY + v[1] * S) * dpr]; }
      piv = tela(ATM[0], ATM[1], 0.3); boc = tela(le(T_FRENTE, Y_EST) - 0.004, Y_EST, 0); cabC = tela(-0.35, 0.45, 0.2);
      var cc = tela(CEREBRO[0], CEREBRO[1], 0.15); cer = [cc[0], cc[1], CEREBRO[2] * S * dpr, CEREBRO[3] * S * dpr];
      perfilV = M.perfil.map(function (q) { return { x: (OX + q.X * S) * dpr, y: (OY + q.Y * S) * dpr, j: q.j, yy: q.yy, l: q.l }; });
      asaV = M.asa.map(function (q) { return [(OX + q[0] * S) * dpr, (OY + q[1] * S) * dpr]; });
      ciliosV = M.cil.map(function (c) { return { x: (OX + c.x * S) * dpr, y: (OY + c.y * S) * dpr, px: (OX + c.px * S) * dpr, py: (OY + c.py * S) * dpr, vx: (OX + c.vx * S) * dpr, vy: (OY + c.vy * S) * dpr, w: c.w }; });
      fendaV = M.fenda.map(function (q) { return { x: (OX + q.X * S) * dpr, y: (OY + q.Y * S) * dpr, w: q.w }; });
      caminhoPerfil = null; gradK = ''; haloK = ''; sprites = {}; SPR_NEU = null;
      for (i = 0; i <= 28; i++) { var yb = -0.14 + i * 0.05; vista(Math.min(le(T_FRENTE, Math.min(yb, 0.98)), le(T_PLANO, yb) + 0.02), yb, 0.12, v); FBX[i] = (OX + v[0] * S) * dpr; FBY[i] = (OY + v[1] * S) * dpr; } // base da onda de brilho
      montaBuffer();
      nevoa = null; // refeita no garante() (o aquecer() a faz num passo à parte)
    }
    // Buffers de pixels do rosto: cada ponto é carimbado em JS (sem uma chamada de canvas por ponto) e entra na tela com um
    // putImageData + drawImage; o brilho difuso sai de uma cópia reduzida (1/3). São dois: 'fixo' (o que não mexe, já
    // misturado à névoa, um por estado: carimbado uma vez por layout na paleta do estado; a troca de estado cruza dois
    // drawImage, sem recarimbar a malha a cada quadro; respiração, cintilar e onda de brilho vão por cima) e 'mexe'
    // (mandíbula, lábios e boca, na cor da mistura: refeito quando a boca mexe ou a cor muda).
    function caixaDe(sub, m, gira) { // retângulo (px do canvas) que os pontos do grupo ocupam, com a boca fechada e toda aberta
      var x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9, k, i, idx = sub.idx, a = 0.11, ab = S * dpr * 0.016, so = S * dpr * 0.005;
      for (k = 0; k < idx.length; k++) {
        i = idx[k]; if (gb[i] < 0.1) continue;
        var x = gx[i], y = gy[i];
        if (gira) { // boca toda aberta: gira na articulação, lábio de baixo desce, o de cima sobe
          var q = gj[i] > 0.06 ? a * gj[i] : 0, dx = x - piv[0], dy = y - piv[1], l = gl[i];
          var xa = piv[0] + dx * Math.cos(q) - dy * Math.sin(q), ya = piv[1] + dx * Math.sin(q) + dy * Math.cos(q) + (l > 0 ? ab * l : l < 0 ? so * l : 0);
          if (xa < x0) x0 = xa; if (xa > x1) x1 = xa; if (ya < y0) y0 = ya; if (ya > y1) y1 = ya;
        }
        if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
      }
      if (x0 > x1) { x0 = y0 = 0; x1 = y1 = 4; }
      x0 = Math.max(0, Math.floor(x0 - m)); y0 = Math.max(0, Math.floor(y0 - m)); x1 = Math.min(canvas.width, Math.ceil(x1 + m)); y1 = Math.min(canvas.height, Math.ceil(y1 + m));
      return { ox: x0, oy: y0, w: Math.max(4, x1 - x0), h: Math.max(4, y1 - y0) };
    }
    function novoBuffer(sub, R, final) { // final: guarda o quadro pronto de cada estado (criado no 1º uso)
      var c = document.createElement('canvas'); c.width = R.w; c.height = R.h;
      var cx = c.getContext('2d'), img = cx.createImageData(R.w, R.h), b1 = document.createElement('canvas');
      b1.width = Math.ceil(R.w / 3); b1.height = Math.ceil(R.h / 3);
      return { c: c, x: cx, img: img, d32: new Uint32Array(img.data.buffer), w: R.w, h: R.h, ox: R.ox, oy: R.oy, b1: b1, x1: b1.getContext('2d'), sub: sub, f: final ? [null, null, null] : null, xf: [null, null, null], pronto: [0, 0, 0] };
    }
    function soltaBufs() { // devolve a memória (o Safari conta cada canvas)
      if (bufs) for (var i = 0; i < 2; i++) { bufs[i].c.width = bufs[i].b1.width = 0; if (bufs[i].f) for (var e = 0; e < 3; e++) if (bufs[i].f[e]) bufs[i].f[e].width = 0; }
    }
    function montaBuffer() {
      soltaBufs();
      var a = caixaDe(MA.sub[0], 4, false), b = caixaDe(MA.sub[1], 4, true), u = S * dpr;
      // caixa do fixo: todos os pontos + folga para o brilho da borda (mais na frente e em cima, onde a luz de contorno brilha)
      var x0 = Math.max(0, Math.min(a.ox, b.ox) - Math.round(0.02 * u)), y0 = Math.max(0, Math.min(a.oy, b.oy) - Math.round(0.07 * u));
      var x1 = Math.min(canvas.width, Math.max(a.ox + a.w, b.ox + b.w) + Math.round(0.09 * u)), y1 = Math.min(canvas.height, Math.max(a.oy + a.h, b.oy + b.h) + Math.round(0.02 * u));
      caixa = { ox: x0, oy: y0, w: x1 - x0, h: y1 - y0 };
      bufs = [novoBuffer(MA.sub[0], caixa, true), novoBuffer(MA.sub[1], b, false)];
      var m = Math.round(0.09 * u); // névoa da mandíbula: caixa do que mexe + folga do desfoque
      caixaM = { ox: Math.max(0, b.ox - m), oy: Math.max(0, b.oy - m), w: Math.min(canvas.width, b.ox + b.w + m) - Math.max(0, b.ox - m), h: Math.min(canvas.height, b.oy + b.h + m) - Math.max(0, b.oy - m) };
      mandAng = -1; lutK = ''; mexeK = '';
    }
    // Névoa: a própria malha espalhada e desfocada em 1/4 da resolução (shadowBlur só aqui, no pré-desenho), com a luz de
    // contorno difusa da testa ao pescoço; o alto e o fim do pescoço são apagados. Uma por estado, em duas partes: a fixa
    // entra no próprio buffer fixo (misturada ao carimbar) e a da mandíbula é desenhada girando junto com a boca.
    var KN = 0.25;
    function preparaNevoa() {
      var e, g, q, i, mj, fb, w, h, OFF, c, cv, tem;
      var lado = Math.max(1.2, hPx * dpr * KN * 1.15), bl = Math.max(2, S * dpr * KN * 0.045);
      var AL = [0.34, 0.2, 0.12, 0.27], NV = [0.3, 0.62, 1], topo = (OY - 0.22 * S) * dpr, base = (OY + 1.36 * S) * dpr;
      // 1) máscaras desfocadas (brancas) por parte e grupo de cor — o shadowBlur roda só aqui, uma vez por layout
      var masc = [];
      for (mj = 0; mj < 2; mj++) {
        fb = mj ? caixaM : caixa; w = Math.max(8, Math.ceil(fb.w * KN)); h = Math.max(8, Math.ceil(fb.h * KN)); OFF = w + 64;
        var lista = [];
        for (g = 0; g < 5; g++) {
          cv = document.createElement('canvas'); cv.width = w; cv.height = h; c = cv.getContext('2d');
          c.globalCompositeOperation = 'lighter'; c.shadowOffsetX = OFF; c.fillStyle = '#000'; c.strokeStyle = '#000';
          if (g < 4) for (q = 0; q < 3; q++) { // um preenchimento por nível de brilho: só a sombra (desfocada) aparece
            c.beginPath(); tem = false;
            for (i = 0; i < N; i++) {
              var bi = gb[i]; if (bi < 0.14 || MA.g[i] !== g || (gj[i] > 0.5 ? 1 : 0) !== mj || (bi < 0.4 ? 0 : bi < 0.8 ? 1 : 2) !== q) continue;
              c.rect((gx[i] - fb.ox) * KN - lado / 2 - OFF, (gy[i] - fb.oy) * KN - lado / 2, lado, lado); tem = true;
            }
            if (tem) { c.shadowColor = 'rgba(255,255,255,' + (AL[g] * NV[q]).toFixed(3) + ')'; c.shadowBlur = bl; c.fill(); }
          }
          else { // luz de contorno difusa (halo neon da borda)
            c.beginPath(); var ab = false;
            for (i = 0; i < perfilV.length; i++) {
              var pv = perfilV[i]; if (pv.yy < -0.12 || pv.yy > 1.3 || (pv.j > 0.5 ? 1 : 0) !== mj) { ab = false; continue; }
              var X = (pv.x - fb.ox) * KN - OFF, Y = (pv.y - fb.oy) * KN;
              if (ab) c.lineTo(X, Y); else { c.moveTo(X, Y); ab = true; }
            }
            c.lineJoin = 'round'; c.lineCap = 'round'; c.lineWidth = Math.max(1, S * dpr * KN * 0.014);
            c.shadowColor = 'rgba(255,255,255,0.6)'; c.shadowBlur = bl * 0.8; c.stroke();
          }
          lista.push(cv);
        }
        masc.push({ l: lista, fb: fb, w: w, h: h });
      }
      // 2) por estado: cada máscara ganha a cor do grupo (source-in num rascunho) e soma; o alto e o fim do pescoço somem
      var tmp = document.createElement('canvas'), tx;
      nevoa = [];
      for (e = 0; e < 3; e++) {
        var pal = EST[NOMES[e]], cores = [pal.borda, degrade(pal.rosto, 0.4), degrade(pal.rosto, 0.8), MAGENTA, pal.borda], par = [];
        for (mj = 0; mj < 2; mj++) {
          var Mk = masc[mj]; fb = Mk.fb; w = Mk.w; h = Mk.h;
          if (tmp.width !== w || tmp.height !== h) { tmp.width = w; tmp.height = h; } tx = tmp.getContext('2d');
          cv = document.createElement('canvas'); cv.width = w; cv.height = h; c = cv.getContext('2d'); c.globalCompositeOperation = 'lighter';
          for (g = 0; g < 5; g++) {
            tx.globalCompositeOperation = 'copy'; tx.drawImage(Mk.l[g], 0, 0);
            tx.globalCompositeOperation = 'source-in'; tx.fillStyle = rgb(cores[g]); tx.fillRect(0, 0, w, h);
            c.drawImage(tmp, 0, 0);
          }
          c.globalCompositeOperation = 'destination-out';
          var y0 = (topo - fb.oy) * KN, y1 = (base - fb.oy) * KN, gt = c.createLinearGradient(0, y0, 0, y0 + 0.24 * S * dpr * KN);
          gt.addColorStop(0, 'rgba(0,0,0,1)'); gt.addColorStop(1, 'rgba(0,0,0,0)'); c.fillStyle = gt; c.fillRect(0, 0, w, y0 + 0.24 * S * dpr * KN);
          var gbx = c.createLinearGradient(0, y1 - 0.3 * S * dpr * KN, 0, y1);
          gbx.addColorStop(0, 'rgba(0,0,0,0)'); gbx.addColorStop(1, 'rgba(0,0,0,1)'); c.fillStyle = gbx; c.fillRect(0, y1 - 0.3 * S * dpr * KN, w, h);
          par.push(cv);
        }
        nevoa.push(par);
      }
      tmp.width = tmp.height = 0;
      for (mj = 0; mj < 2; mj++) for (g = 0; g < 5; g++) masc[mj].l[g].width = 0; // devolve a memória (Safari conta cada canvas)
    }

    // ---------- sprites de brilho (pré-desenhados) ----------
    function sprite(c, macio, tam) { // tam: tamanho exato (px) quando o brilho é pequeno e numeroso (desenhado sem escala)
      var k = c.join(',') + (macio ? 'm' : '') + (tam || ''); if (sprites[k]) return sprites[k];
      var s = document.createElement('canvas'), n = tam || Math.max(16, Math.round(32 * dpr)); s.width = s.height = n;
      var g = s.getContext('2d'), gr = g.createRadialGradient(n / 2, n / 2, 0, n / 2, n / 2, n / 2);
      if (macio) { gr.addColorStop(0, rgba(c, 0.55)); gr.addColorStop(0.45, rgba(c, 0.22)); gr.addColorStop(1, rgba(c, 0)); }
      else { gr.addColorStop(0, rgba(cmis(c, BRANCO, 0.35), 0.9)); gr.addColorStop(0.25, rgba(c, 0.45)); gr.addColorStop(1, rgba(c, 0)); }
      g.fillStyle = gr; g.fillRect(0, 0, n, n);
      return (sprites[k] = s);
    }

    // ---------- simulação ----------
    var MIX = { rosto: [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]], brilho: 0, ondas: 0, neur: 0, entrada: 0, respira: 0, borda: [0, 0, 0], halo: [0, 0, 0] };
    function mistura() { // parâmetros atuais, misturando os estados pelo peso (sem criar objetos por quadro)
      var o = MIX, tot = 0, i, k, s;
      o.brilho = o.ondas = o.neur = o.entrada = o.respira = 0;
      for (k = 0; k < 5; k++) o.rosto[k][0] = o.rosto[k][1] = o.rosto[k][2] = 0;
      for (s = 0; s < 3; s++) o.borda[s] = o.halo[s] = 0;
      for (i = 0; i < NOMES.length; i++) tot += peso[NOMES[i]];
      for (i = 0; i < NOMES.length; i++) {
        var w = peso[NOMES[i]] / tot, e = EST[NOMES[i]]; if (!w) continue;
        o.brilho += e.brilho * w; o.ondas += e.ondas * w; o.neur += e.neur * w; o.entrada += e.entrada * w; o.respira += e.respira * w;
        for (k = 0; k < 5; k++) for (s = 0; s < 3; s++) o.rosto[k][s] += e.rosto[k][s] * w;
        for (s = 0; s < 3; s++) { o.borda[s] += e.borda[s] * w; o.halo[s] += e.halo[s] * w; }
      }
      return o;
    }
    function silaba(t) { // oscilação sintética do ritmo da fala (~4,5 sílabas/s) para a energia das ondas
      var a = 0.5 + 0.5 * Math.sin(TAU * 4.4 * t + 1.1 * Math.sin(TAU * 1.3 * t));
      return Math.pow(a, 1.4) * (0.72 + 0.28 * Math.sin(TAU * 0.83 * t + 1.0));
    }
    function vozEm(tt) { // energia de voz no instante tt (buffer a 60 Hz)
      var f = tt * 60, i = Math.floor(f), k = f - i;
      if (i < 0 || i > histI || i < histI - 500) return 0;
      var a = HIST[i & 511], b = i + 1 <= histI ? HIST[(i + 1) & 511] : a;
      return a + (b - a) * k;
    }
    function passo(dt) {
      T += dt;
      var i, k = 1 - Math.exp(-dt / 0.16); // transição de estado ~500 ms
      for (i = 0; i < NOMES.length; i++) { var n = NOMES[i], a = n === alvo ? 1 : 0; peso[n] += (a - peso[n]) * k; if (Math.abs(peso[n] - a) < 0.002) peso[n] = a; }
      energia *= Math.exp(-dt / 0.22); eo *= Math.exp(-dt / 0.5);
      somNivel += (somAlvo - somNivel) * (1 - Math.exp(-dt / (somAlvo > somNivel ? 0.06 : 0.28)));
      var fal = peso.falando;
      // boca: um ciclo abre-fecha por sílaba (~3,4/s). Cada palavra (pulso) recomeça o ciclo e dá a força dele; sem
      // onboundary (vozes do Android), os ciclos seguem sozinhos enquanto há som. Entre sílabas e sem som, fecha de verdade.
      silF += dt * 3.4;
      if (silF >= 1) { // sílaba seguinte: mais fraca dentro da mesma palavra; sem palavras, força variada (fixa por ciclo)
        silF -= Math.floor(silF); silN++;
        var hs = (Math.sin(silN * 12.9898) * 43758.5453) % 1; if (hs < 0) hs += 1;
        silA = T - palT < 0.45 ? silA * 0.7 : 0.5 + 0.45 * hs;
      }
      palEnv *= Math.exp(-dt / 0.3);
      var ab = Math.sin(PI * Math.pow(silF, 0.6)); ab = ab * Math.sqrt(ab); // perfil do ciclo: abre rápido (~90 ms) e fecha mais devagar
      var bAlvo = fal * Math.max(somNivel, palEnv) * silA * ab;
      boca += (bAlvo - boca) * (1 - Math.exp(-dt / (bAlvo > boca ? 0.03 : 0.05)));
      // energia das ondas: sopra com o som, no ritmo das sílabas da boca, mais os pulsos
      var voz = somNivel * (0.3 + 0.7 * silA * ab) * (0.85 + 0.15 * silaba(T));
      vozAtual = lim(0.8 * voz + 0.75 * energia, 0, 1) * fal;
      vozS += (vozAtual - vozS) * (1 - Math.exp(-dt / 0.25));
      // histórico para as ondas viajarem
      var hi = Math.floor(T * 60);
      if (histI < 0) histI = hi - 1;
      while (histI < hi) { histI++; HIST[histI & 511] = vozAtual; }
      // ondas de brilho pela malha (ouvindo; no pensando, uma lenta de vez em quando)
      for (i = ondasMalha.length - 1; i >= 0; i--) if (T - ondasMalha[i].t0 > 1.4) ondasMalha.splice(i, 1);
      if (peso.pensando > 0.5 && T - pensaT > 1.5) { pensaT = T; if (ondasMalha.length < 5) ondasMalha.push({ t0: T, f: 0.28 }); }
      for (i = arcos.length - 1; i >= 0; i--) if (T - arcos[i].t0 > arcos[i].vida) arcos.splice(i, 1);
      simFaiscas(dt, fal); simChegando(dt);
      for (i = claroes.length - 1; i >= 0; i--) if (T - claroes[i].t0 > 0.35) claroes.splice(i, 1);
    }
    // faíscas soltas pela fita
    function onda(fio, d, L, A0, lam, tt) { // y relativo ao centro da fita
      var p = d / L, v = vozEm(tt - d / velOnda(L)), env = suave(0, 0.16, p) * (0.5 + 0.5 * p);
      return A0 * env * v * fio.a * Math.sin(TAU * (d / (lam * fio.l) - fio.v * tt) + fio.f) - A0 * 0.18 * p * Math.sin(TAU * (0.35 * p - 0.07 * tt));
    }
    function velOnda(L) { return Math.max(230, L / 1.45); }
    function geomOnda() {
      var x0 = boc[0] / dpr + 2, L = Math.max(40, W - x0), A0 = Math.min(0.30 * S, 0.22 * L + 0.10 * S, 0.12 * H), lam = lim(L / (W > 700 ? 3.3 : 2.6), 50, 230);
      return { x0: x0, y0: boc[1] / dpr, dy: bocaY, L: L, A0: A0, lam: lam };
    }
    function simFaiscas(dt, fal) {
      var G = geomOnda(), cap = nivel ? 90 : W > 700 ? 240 : 150, i;
      faiscaAcum += dt * (20 + 150 * vozAtual) * (W > 700 ? 1.7 : 1) * fal * (vozAtual > 0.04 ? 1 : 0);
      while (faiscaAcum >= 1) {
        faiscaAcum -= 1; if (faiscas.length >= cap) continue;
        var p = 0.05 + 0.95 * Math.pow(aleat(), 0.8), d = p * G.L, fio = FIOS[Math.floor(aleat() * 4)];
        if (aleat() > vozEm(T - d / velOnda(G.L)) * 2) continue; // só onde a onda já chegou
        var yy = G.y0 + onda(fio, d, G.L, G.A0, G.lam, T) + (aleat() - 0.5) * (4 + G.A0 * 0.25);
        faiscas.push({ x: G.x0 + d, y: yy, vx: 12 + aleat() * 55, vy: (aleat() - 0.5) * 34, t0: T, vida: 0.5 + aleat() * 1.1, s: aleat() < 0.14 ? 2 : 1, c: p, b: Math.min(2, Math.floor(p * 3)) });
      }
      for (i = faiscas.length - 1; i >= 0; i--) {
        var f = faiscas[i]; f.x += f.vx * dt; f.y += f.vy * dt; f.vy *= 0.985;
        if (T - f.t0 > f.vida || f.x > W + 4) { faiscas[i] = faiscas[faiscas.length - 1]; faiscas.pop(); }
      }
    }
    // partículas que chegam da direita (ouvindo): fluxo contínuo + rajada a cada trecho; trajetória em Bézier que acelera
    function simChegando(dt) {
      var e = peso.ouvindo, cap = nivel ? 80 : 150, i;
      entradaAcum += dt * 30 * e;
      if (e < 0.05) rajada = 0;
      while ((entradaAcum >= 1 || rajada >= 1) && alvos.length) {
        if (entradaAcum >= 1) entradaAcum -= 1; else rajada -= 1;
        if (chegando.length >= cap) continue;
        var ti = alvos[Math.floor(aleat() * alvos.length)], tx = gx[ti] / dpr + 1.5, ty = gy[ti] / dpr;
        var sx = W + 4 + 30 * aleat(), sy = ty + (aleat() - 0.5) * S * (0.35 + 0.6 * aleat());
        if (sy < faixaY0) sy = faixaY0 + aleat() * Math.max(24, ty - faixaY0); else if (sy > faixaY1) sy = faixaY1 - aleat() * Math.max(24, faixaY1 - ty); // nem no HUD da direita, nem na legenda (sorteia de novo entre a borda e o alvo)
        chegando.push({ sx: sx, sy: sy, mx: tx + (sx - tx) * (0.35 + 0.25 * aleat()), my: sy, tx: tx, ty: ty, t0: T, vida: lim((sx - tx) / (S * (0.9 + 0.8 * aleat())), 0.9, 3.4), f: 0.45 + 0.55 * aleat(), tm: 0.9 + 0.9 * aleat() });
      }
      for (i = chegando.length - 1; i >= 0; i--) {
        var c = chegando[i];
        if (T - c.t0 >= c.vida) { if (claroes.length < 40) claroes.push({ x: c.tx, y: c.ty, t0: T, f: c.f }); eo = Math.min(1, eo + 0.015); chegando[i] = chegando[chegando.length - 1]; chegando.pop(); }
      }
    }

    // ---------- desenho ----------
    function desenha() {
      garante();
      var P = mistura(), c = ctx;
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.globalCompositeOperation = 'source-over'; c.globalAlpha = 1;
      c.clearRect(0, 0, canvas.width, canvas.height);
      c.globalCompositeOperation = 'lighter';
      var resp = Math.sin(TAU * T / 4.6) * P.respira;
      halo(P, resp);
      if (P.neur > 0.03) neuronios(P);
      rosto(P, resp);
      borda(P);
      if (P.ondas > 0.01) ondas(P);
      if (P.entrada > 0.01 || chegando.length) entrada(P);
      arcosDesenha(P);
      c.globalAlpha = 1; c.globalCompositeOperation = 'source-over';
    }
    var haloG = [null, null, null], haloK = '';
    function halo(P, resp) { // brilho difuso atrás do rosto (um degradê guardado por estado)
      var c = ctx, R = S * dpr * 0.95, cx = cabC[0] + S * dpr * 0.25, cy = cabC[1], k = R + ':' + cx + ':' + cy, i;
      if (k !== haloK) {
        haloK = k;
        for (i = 0; i < 3; i++) { var hc = EST[NOMES[i]].halo, g = c.createRadialGradient(cx, cy, 0, cx, cy, R); g.addColorStop(0, rgba(hc, 1)); g.addColorStop(0.45, rgba(hc, 0.4)); g.addColorStop(1, rgba(hc, 0)); haloG[i] = g; }
      }
      for (i = 0; i < 3; i++) {
        var w = peso[NOMES[i]] + (i === 2 ? peso.livre : 0); if (w < 0.01) continue;
        c.globalAlpha = lim(0.09 * w * P.brilho * (1 + 0.15 * resp), 0, 1); c.fillStyle = haloG[i]; c.fillRect(cx - R, cy - R, R * 2, R * 2);
      }
    }
    function mandibula() { return boca * 0.11; } // ângulo (rad) de abertura: até ~6°, visível num palco de 250 px
    var nQuadro = 0, mexeK = '', mexeBr = 0, mandAng = -1, mandAbre = 0, mandVoz = 0, fbAng = 0, fbAbre = 0;
    var NL = 48, LUT = new Uint32Array(NH * NL * 3), lutK = '';
    function montaLUT(pal) { // tabela de pixels por faixa de cor (paleta do rosto): centro, lados e cantos do ponto em NL níveis
      var k2 = dpr >= 1.5 ? 0.62 : 0.42, k3 = dpr >= 1.5 ? 0.30 : 0.16, ganho = 1.05, b, lv; // ponto 3 × 3
      for (b = 0; b < NH; b++) {
        var cor = degrade(pal, (b + 0.5) / NH, COR3), cr = cor[0] * ganho, cg = cor[1] * ganho, cb = cor[2] * ganho, base = b * NL * 3;
        for (lv = 0; lv < NL; lv++) { var av = (lv + 0.5) * 1.3 / NL, o3 = base + lv * 3; LUT[o3] = pix(cr * av, cg * av, cb * av); LUT[o3 + 1] = pix(cr * av * k2, cg * av * k2, cb * av * k2); LUT[o3 + 2] = pix(cr * av * k3, cg * av * k3, cb * av * k3); }
      }
    }
    function pesoFixo(e) { // peso do quadro fixo de cada estado; o 'livre' é o do falando bem apagado (mesma paleta)
      return e === 2 ? peso.falando + peso.livre * EST.livre.brilho / EST.falando.brilho : peso[NOMES[e]];
    }
    function carimbaFixo(e) { // fixo do estado e: pontos na paleta dele + névoa + brilho difuso, num canvas só
      var F = bufs[0], pal = EST[NOMES[e]], xf;
      montaLUT(pal.rosto); lutK = ''; // a LUT da mistura é refeita logo depois
      carimba(F, 0, 0, 0, pal.brilho * 1.09);
      if (!F.f[e]) { F.f[e] = document.createElement('canvas'); F.f[e].width = F.w; F.f[e].height = F.h; F.xf[e] = F.f[e].getContext('2d'); }
      xf = F.xf[e];
      xf.globalCompositeOperation = 'copy'; xf.globalAlpha = 1; xf.drawImage(F.c, 0, 0);
      xf.globalCompositeOperation = 'lighter'; xf.imageSmoothingEnabled = true;
      xf.globalAlpha = lim(pal.brilho * 1.03, 0, 1); xf.drawImage(nevoa[e][0], 0, 0, nevoa[e][0].width / KN, nevoa[e][0].height / KN);
      if (nivel < 2) { xf.globalAlpha = 0.7; xf.drawImage(F.b1, 0, 0, F.w, F.h); }
      xf.globalCompositeOperation = 'source-over'; xf.globalAlpha = 1;
      F.pronto[e] = nivel < 2 ? 2 : 1;
    }
    function rosto(P, resp) {
      // os buffers são carimbados no brilho máximo da respiração; a respiração entra no globalAlpha (sem recarimbar)
      var ang = mandibula(), abre = boca, br = P.brilho * 1.09, R = P.rosto, e, pr = nivel < 2 ? 2 : 1;
      nQuadro++;
      for (e = 0; e < 3; e++) if (pesoFixo(e) > 0.004 && bufs[0].pronto[e] !== pr) carimbaFixo(e); // 1ª vez do estado neste layout
      var ck = Math.round(R[0][0] + R[1][1] * 3 + R[2][2] * 7 + R[3][0] * 11 + R[4][1] * 13) + ':' + dpr; // só muda na troca de estado
      var caro = !manual && r.ms > 5, vez = !caro || (nQuadro & 1) === 0; // quadro caro: o que mexe vai a 30 Hz
      // na troca de estado a cor da mandíbula acompanha a 30 Hz (a mudança é lenta); no fim da troca, sempre
      var corMuda = (ck !== mexeK || Math.abs(br - mexeBr) > 0.004) && (manual || (nQuadro & 1) === 0 || peso[alvo] === 1);
      var refazMexe = manual || corMuda || (vez && (Math.abs(ang - mandAng) > 0.0004 || Math.abs(abre - mandAbre) > 0.003 || (P.ondas > 0.01 && Math.abs(vozAtual - mandVoz) > 0.02)));
      if (refazMexe) {
        if (ck !== lutK) { lutK = ck; montaLUT(R); }
        carimba(bufs[1], P.ondas, ang, abre, br); mexeK = ck; mexeBr = br; mandAng = ang; mandAbre = abre; mandVoz = vozAtual;
      }
      fbAng = mandAng; fbAbre = mandAbre;
      desenhaBuffer(ctx, P, fbAng, fbAbre, (1 + 0.09 * resp) / 1.09);
      if (ondasMalha.length) ondasBrilho((1 + 0.09 * resp) / 1.09);
      if (!nivel) cintila(P, fbAng, fbAbre, (1 + 0.09 * resp) / 1.09);
    }
    // onda de brilho pela malha (cada trecho ouvido; no pensando, uma lenta de vez em quando): uma faixa que corre da frente
    // para a nuca; os pontos do rosto são redesenhados recortados pela faixa (três faixas encaixadas: borda macia)
    var FBX = new Float32Array(29), FBY = new Float32Array(29); // frente do rosto (na tela) de onde a faixa parte
    function ondasBrilho(kr) {
      var c = ctx, k, j, i, e, F = bufs[0], M = bufs[1], n = ondasMalha.length, ux = -CY * S * dpr, uy = SY * SP * S * dpr; // recuo de 1 unidade na vista
      for (k = 0; k < n; k++) {
        var o = ondasMalha[k], fr = (T - o.t0) * 0.95 - 0.05, forca = o.f * 1.45 * (1 - fr * 0.6) * suave(-0.12, 0.02, fr);
        if (forca < 0.02) continue;
        for (j = 0; j < 3; j++) {
          var lg = [0.11, 0.07, 0.035][j];
          c.save(); c.beginPath();
          var d1 = 0.95 * (fr - lg), d2 = 0.95 * (fr + lg);
          for (i = 0; i <= 28; i++) c.lineTo(FBX[i] + d1 * ux, FBY[i] + d1 * uy);
          for (i = 28; i >= 0; i--) c.lineTo(FBX[i] + d2 * ux, FBY[i] + d2 * uy);
          c.closePath(); c.clip();
          for (e = 0; e < 3; e++) { var wf = pesoFixo(e); if (wf < 0.004 || !F.f[e]) continue; c.globalAlpha = lim(forca * 0.32 * kr * wf, 0, 1); c.drawImage(F.f[e], F.ox, F.oy); } // rosto do estado
          c.globalAlpha = lim(forca * 0.45 * kr, 0, 1); c.drawImage(M.c, M.ox, M.oy);
          c.restore();
        }
      }
    }
    // cintilar: a cada instante ~4% dos pontos piscam (um quadradinho claro por cima, em 3 lotes de cor); fica fora do
    // buffer, então o rosto parado não precisa ser recarimbado
    var CIN = [rgb([0, 0, 0]), rgb([0, 0, 0]), rgb([0, 0, 0])], cinK = '';
    var CX = new Float32Array(3 * 200), CYY = new Float32Array(3 * 200), CZ = new Float32Array(3 * 200), CNT = new Int16Array(3);
    function cintila(P, ang, abre, k) {
      var c = ctx, i, g, j, n = N, t = T, pxv = piv[0], pyv = piv[1], abaixa = S * dpr * 0.016 * abre, s = (dpr >= 1.5 ? 2.2 : 1.6);
      if (cinK !== lutK) { cinK = lutK; for (g = 0; g < 3; g++) CIN[g] = rgb(cmis(degrade(P.rosto, 0.12 + g * 0.36), BRANCO, 0.45)); }
      CNT[0] = CNT[1] = CNT[2] = 0;
      for (i = 0; i < n; i += 2) { // metade dos pontos pode cintilar; cada um vai para o lote da sua cor
        var ph = t * (0.25 + gh[i] * 0.35) + gh[i] * 17; ph -= ph | 0; if (ph >= 0.04 || gb[i] < 0.2) continue;
        var hu = gu[i] * 2.5 + 0.1; g = hu < 0.45 ? 0 : hu < 0.8 ? 1 : 2; if (CNT[g] >= 200) continue;
        var x = gx[i], y = gy[i], w = gj[i];
        if (w > 0.06 && ang > 0) { var q = ang * w, dx = x - pxv, dy = y - pyv; x = pxv + dx - dy * q; y = pyv + dx * q + dy; }
        if (gl[i] > 0) y += abaixa * gl[i];
        j = g * 200 + CNT[g]++; CX[j] = x; CYY[j] = y; CZ[j] = s * (1 - ph * 12);
      }
      for (g = 0; g < 3; g++) {
        if (!CNT[g]) continue;
        c.beginPath();
        for (i = 0; i < CNT[g]; i++) { j = g * 200 + i; c.rect(CX[j] - CZ[j] / 2, CYY[j] - CZ[j] / 2, CZ[j], CZ[j]); }
        c.fillStyle = CIN[g]; c.globalAlpha = lim(0.55 * P.brilho * k, 0, 1); c.fill();
      }
    }
    function carimba(B, fal, ang, abre, br) { // fal: quanto o brilho da boca entra (só nos pontos do grupo que mexe)
      var i, b, k, idx = B.sub.idx, bin = B.sub.bin, pxv = piv[0], pyv = piv[1], vz = vozAtual;
      var abaixa = S * dpr * 0.016 * abre, sobe = S * dpr * 0.005 * abre;
      var d = B.d32, fw = B.w, fh = B.h, ox = B.ox, oy = B.oy, L3 = LUT, topoL = NL * 3 - 3;
      var q, dx, dy, ix, iy, p, c1, c2, c3, lv;
      d.fill(0);
      for (b = 0; b < NH; b++) {
        var k0 = bin[b], k1 = bin[b + 1], base = b * NL * 3; if (k1 <= k0) continue;
        for (k = k0; k < k1; k++) {
          i = idx[k];
          var a = gb[i] * br;
          if (fal > 0.01 && gm[i] > 0.05) a += gm[i] * vz * fal * 0.9; // brilho da boca (só nos pontos do grupo que mexe)
          if (a < 0.02) continue;
          var x = gx[i], y = gy[i], w = gj[i];
          if (w > 0.06 && ang > 0) { q = ang * w; dx = x - pxv; dy = y - pyv; var cs = 1 - q * q * 0.5; x = pxv + dx * cs - dy * q; y = pyv + dx * q + dy * cs; }
          var l = gl[i]; if (l > 0) y += abaixa * l; else if (l < 0) y += sobe * l;
          // ponto 3 × 3 carimbado como pixels de 32 bits; onde dois pontos se tocam fica o mais claro (compara pelo alfa)
          ix = (x - ox + 0.5) | 0; iy = (y - oy + 0.5) | 0;
          if (ix < 1 || iy < 1 || ix > fw - 2 || iy > fh - 2) continue;
          lv = ((a * NL / 1.3) | 0) * 3; if (lv > topoL) lv = topoL; lv += base;
          c1 = L3[lv]; c2 = L3[lv + 1]; c3 = L3[lv + 2];
          p = iy * fw + ix;
          if (d[p] < c1) d[p] = c1;
          if (d[p - 1] < c2) d[p - 1] = c2; if (d[p + 1] < c2) d[p + 1] = c2; if (d[p - fw] < c2) d[p - fw] = c2; if (d[p + fw] < c2) d[p + fw] = c2;
          if (d[p - fw - 1] < c3) d[p - fw - 1] = c3; if (d[p - fw + 1] < c3) d[p - fw + 1] = c3; if (d[p + fw - 1] < c3) d[p + fw - 1] = c3; if (d[p + fw + 1] < c3) d[p + fw + 1] = c3;
        }
      }
      B.x.putImageData(B.img, 0, 0);
      B.x1.globalCompositeOperation = 'copy'; B.x1.imageSmoothingEnabled = true; B.x1.drawImage(B.c, 0, 0, B.b1.width, B.b1.height); // cópia reduzida → brilho difuso
    }
    function desenhaBuffer(c, P, ang, abre, kr) {
      var fal = P.ondas, e;
      // centro da boca aberta (as ondas saem daqui): meio caminho até o lábio de baixo
      bocaY = 0.5 * ((boc[0] - piv[0]) * Math.sin(ang) + S * dpr * 0.016 * abre) / dpr;
      c.globalCompositeOperation = 'lighter'; c.imageSmoothingEnabled = true;
      var F = bufs[0], M = bufs[1];
      for (e = 0; e < 3; e++) { // fixo de cada estado (pontos + névoa + brilho difuso): na troca, os dois se cruzam
        var wf = pesoFixo(e); if (wf < 0.004 || !F.f[e]) continue;
        c.globalAlpha = lim(wf * kr, 0, 1); c.drawImage(F.f[e], F.ox, F.oy);
      }
      // névoa da mandíbula (volume e halo neon do queixo), girando com a boca
      if (ang > 0.0005) { c.translate(piv[0], piv[1]); c.rotate(ang); c.translate(-piv[0], -piv[1]); }
      for (e = 0; e < 3; e++) {
        var wgt = peso[NOMES[e]] + (e === 2 ? peso.livre : 0); if (wgt < 0.01) continue;
        c.globalAlpha = lim(wgt * P.brilho * (0.85 + 0.25 * vozS), 0, 1); c.drawImage(nevoa[e][1], caixaM.ox, caixaM.oy, nevoa[e][1].width / KN, nevoa[e][1].height / KN);
      }
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.globalAlpha = kr; c.drawImage(M.c, M.ox, M.oy);
      if (nivel < 2) { c.globalAlpha = 0.7 * kr; c.drawImage(M.b1, M.ox, M.oy, M.w, M.h); }
      // boca aberta: brilho que sai de dentro, proporcional à abertura
      if (abre > 0.02 && fal > 0.01) {
        var sp = sprite(cmis(CIANO, AZUL, 0.25)), R = S * dpr * (0.05 + 0.07 * abre), bx = boc[0] - S * dpr * 0.018, by = boc[1] + bocaY * dpr;
        c.globalAlpha = lim(fal * (0.2 + 0.6 * abre + 0.25 * vozS), 0, 1); c.drawImage(sp, bx - R, by - R * 0.75, R * 2, R * 1.5);
      }
    }
    var caminhoPerfil = null, chavePerfil = '', gradB = null, gradK = '';
    function borda(P) { // luz de contorno ciano/azul no perfil: um caminho (refeito só quando a boca mexe), degradê guardado
      var c = ctx, ang = fbAng, abre = fbAbre, n = perfilV.length, i, pass, br = P.brilho;
      if (!n) return;
      var desce = S * dpr * 0.016 * abre, sobe = S * dpr * 0.005 * abre;
      var chave = ang.toFixed(4) + ':' + abre.toFixed(3);
      if (chave !== chavePerfil || !caminhoPerfil) {
        var pa = new Path2D(), sup = true;
        for (i = 0; i < n; i++) {
          var p = perfilV[i], x = p.x, y = p.y;
          if (p.j > 0.002 && ang > 0) { var qa = ang * p.j, dx = x - piv[0], dy = y - piv[1], cq = Math.cos(qa), sq = Math.sin(qa); x = piv[0] + dx * cq - dy * sq; y = piv[1] + dx * sq + dy * cq + desce * p.l * p.j; }
          if (sup && p.yy > Y_EST) { sup = false; pa.moveTo(x, y); continue; } // quebra no estômio
          if (i === 0) pa.moveTo(x, y); else pa.lineTo(x, y);
        }
        caminhoPerfil = pa; chavePerfil = chave;
      }
      var bc = P.borda, gk = Math.round(bc[0]) + ',' + Math.round(bc[1]) + ',' + Math.round(bc[2]);
      if (gk !== gradK) { // degradê refeito só quando a cor ou o layout mudam: some no alto da cabeça e no fim do pescoço
        gradK = gk;
        gradB = c.createLinearGradient(0, perfilV[0].y, 0, perfilV[n - 1].y);
        gradB.addColorStop(0, rgba(bc, 0)); gradB.addColorStop(0.075, rgba(bc, 0.35)); gradB.addColorStop(0.16, rgba(bc, 0.95)); gradB.addColorStop(0.72, rgba(bc, 1));
        gradB.addColorStop(0.81, rgba(bc, 0.6)); gradB.addColorStop(0.93, rgba(bc, 0.1)); gradB.addColorStop(1, rgba(bc, 0));
      }
      c.strokeStyle = gradB; c.lineJoin = 'round'; c.lineCap = 'round';
      var passes = [[5, 0.08], [1.1, 0.6]]; // o halo largo já vem da névoa
      for (pass = 0; pass < passes.length; pass++) { c.lineWidth = passes[pass][0] * dpr; c.globalAlpha = passes[pass][1] * br; c.stroke(caminhoPerfil); }
      // borda viva: acende com a voz (falando) e com cada trecho ouvido (ouvindo)
      var viva = (0.5 * vozS * peso.falando + 0.25 * eo * peso.ouvindo) * br;
      if (viva > 0.02) { c.lineWidth = 3 * dpr; c.globalAlpha = lim(viva * 0.45, 0, 1); c.stroke(caminhoPerfil); }
      // asa do nariz: vinco discreto
      c.strokeStyle = rgb(bc); c.lineWidth = 0.9 * dpr; c.globalAlpha = 0.24 * br; c.beginPath();
      for (i = 0; i < asaV.length; i++) if (i) c.lineTo(asaV[i][0], asaV[i][1]); else c.moveTo(asaV[i][0], asaV[i][1]);
      c.stroke();
      // olho fechado: vinco (fraco), linha dos cílios (halo + fio) e cílios
      var cc = cmis(bc, BRANCO, 0.25), nc = ciliosV.length;
      c.strokeStyle = rgb(cc);
      c.globalAlpha = 0.22 * br; c.lineWidth = 0.9 * dpr; c.beginPath();
      for (i = 2; i < nc - 2; i++) { var q0 = ciliosV[i]; if (i > 2) c.lineTo(q0.vx, q0.vy); else c.moveTo(q0.vx, q0.vy); }
      c.stroke();
      var lw = [[2.6, 0.10], [1.0, 0.62]];
      for (pass = 0; pass < 2; pass++) {
        c.lineWidth = lw[pass][0] * dpr; c.globalAlpha = lw[pass][1] * br; c.beginPath();
        for (i = 0; i < nc; i++) { var q = ciliosV[i]; if (i) c.lineTo(q.x, q.y); else c.moveTo(q.x, q.y); }
        c.stroke();
      }
      c.globalAlpha = 0.5 * br; c.lineWidth = 0.7 * dpr; c.beginPath();
      for (i = 1; i < nc - 1; i++) { var q2 = ciliosV[i]; c.moveTo(q2.x, q2.y); c.lineTo(q2.px, q2.py); }
      c.stroke();
      // linha neon dos lábios: a de cima fica (sobe um pouco), a de baixo acompanha a mandíbula
      var nfv = fendaV.length; if (!nfv) return;
      var meio = Math.round(nfv * 0.5), cf = cmis(bc, BRANCO, 0.2), af = 0.36 * br, parte;
      c.strokeStyle = rgb(cf);
      for (parte = 0; parte < 2; parte++) { // metade da frente forte, metade de trás fraca (a linha some antes do canto)
        var i0 = parte ? meio : 0, i1 = parte ? nfv - 1 : meio, k2 = parte ? 0.3 : 1;
        c.beginPath();
        for (i = i0; i <= i1; i++) {
          var f = fendaV[i], xa = f.x, ya = f.y - sobe * f.w;
          if (i === i0) c.moveTo(xa, ya); else c.lineTo(xa, ya);
        }
        for (i = i0; i <= i1; i++) {
          var f2 = fendaV[i], qq = ang * f2.w, ddx = f2.x - piv[0], ddy = f2.y - piv[1];
          var xb = piv[0] + ddx * Math.cos(qq) - ddy * Math.sin(qq), yb = piv[1] + ddx * Math.sin(qq) + ddy * Math.cos(qq) + desce * f2.w;
          if (i === i0) c.moveTo(xb, yb); else c.lineTo(xb, yb);
        }
        c.lineWidth = 3 * dpr; c.globalAlpha = af * 0.22 * k2; c.stroke();
        c.lineWidth = 0.9 * dpr; c.globalAlpha = af * k2; c.stroke();
      }
    }
    function ondas(P) { // fita de senoides finas da boca até a borda direita
      var c = ctx, G = geomOnda(), fl = P.ondas, K = nivel ? 3 : W > 700 ? 5 : 4, R = nivel ? 3 : W > 700 ? 6 : 5, k, j, i, lv;
      var passo = Math.max(W > 700 ? 4.5 : 6, Math.min(9, G.L / 60)), M = Math.ceil(G.L / passo) + 1, vel = velOnda(G.L), perto = 0.3 * S;
      // cor ao longo da fita (ciano → azul → violeta → magenta) e transparência pela energia que já saiu da boca
      var gr = c.createLinearGradient(G.x0 * dpr, 0, W * dpr, 0), vtot = 0;
      for (i = 0; i <= 12; i++) {
        var pp = i / 12, vv = vozEm(T - pp * G.L / vel); vtot += vv;
        gr.addColorStop(pp, rgba(degrade(ONDA_CORES, pp), lim(vv * 1.8, 0, 1) * (i ? 1 : 0.5) * (i === 12 ? 0.7 : 1)));
      }
      var fitas = vtot >= 0.02;
      c.strokeStyle = gr; c.lineJoin = 'round'; c.lineCap = 'round';
      if (M > OYC.length) { OYC = new Float32Array(M + 50); OHW = new Float32Array(M + 50); OXS = new Float32Array(M + 50); }
      var yc = OYC, hw = OHW, xs = OXS;
      for (k = 0; fitas && k < K; k++) {
        var fio = FIOS[k], vmax = 0;
        for (i = 0; i < M; i++) {
          var d = Math.min(G.L, i * passo), p = d / G.L, v = vozEm(T - d / vel), env = suave(0, 0.16, p) * (0.5 + 0.5 * p);
          var A = G.A0 * env * v * fio.a;
          xs[i] = (G.x0 + d) * dpr;
          yc[i] = (G.y0 + G.dy * Math.exp(-d / perto) + A * Math.sin(TAU * (d / (G.lam * fio.l) - fio.v * T) + fio.f) - G.A0 * 0.18 * p * Math.sin(TAU * (0.35 * p - 0.07 * T))) * dpr;
          hw[i] = (0.6 + suave(0, 0.1, p) * 1.2 + A * fio.w) * Math.cos(TAU * (d / (G.lam * fio.tw)) - 2.1 * T + fio.f * 1.7) * dpr;
          if (v > vmax) vmax = v;
        }
        if (vmax < 0.01) continue;
        var al = fl * fio.al * (0.3 + 0.7 * Math.min(1, vmax * 1.3));
        // halo do fio
        c.globalAlpha = 0.085 * al; c.lineWidth = (W > 700 ? 9 : 7) * dpr; c.beginPath(); curvaSuave(c, xs, yc, hw, 0, M);
        c.stroke();
        // fios finos da fita (um só caminho por fio; curvas quadráticas pelos pontos médios, sem quinas)
        c.lineWidth = 0.9 * dpr; c.globalAlpha = al * 0.36; c.beginPath();
        for (j = 0; j < R; j++) curvaSuave(c, xs, yc, hw, R > 1 ? j / (R - 1) * 2 - 1 : 0, M);
        c.stroke();
      }
      // faíscas: pontos finos em lotes (3 cores × 2 níveis de brilho, um fill por lote); as maiores ganham um brilho redondo
      var nf = Math.min(faiscas.length, LOTE.length);
      for (i = 0; i < 6; i++) NLOTE[i] = 0;
      for (i = 0; i < nf; i++) { // uma passada: cada faísca vai para o lote da sua cor e nível de brilho
        var f = faiscas[i], t = (T - f.t0) / f.vida, a = t < 0.15 ? t / 0.15 : 1 - (t - 0.15) / 0.85; if (a <= 0.05) continue;
        var g = f.b * 2 + (a > 0.5 ? 1 : 0); LOTE[g * 96 + Math.min(95, NLOTE[g]++)] = i;
      }
      for (j = 0; j < 6; j++) { // núcleo fino de cada faísca e, nas maiores e mais vivas, um halo fraco em volta (sem sprite)
        var nl = Math.min(96, NLOTE[j]); if (!nl) continue;
        c.beginPath();
        for (k = 0; k < nl; k++) { var f1 = faiscas[LOTE[j * 96 + k]], s = (0.75 + 0.45 * f1.s) * dpr; c.rect(f1.x * dpr - s / 2, f1.y * dpr - s / 2, s, s); }
        c.fillStyle = FAISCA_COR[j >> 1]; c.globalAlpha = fl * (j & 1 ? 0.95 : 0.45); c.fill();
        if (!(j & 1)) continue;
        c.beginPath(); var tem = false;
        for (k = 0; k < nl; k++) { var f3 = faiscas[LOTE[j * 96 + k]]; if (f3.s < 2) continue; var h3 = 1.5 * dpr; c.rect(f3.x * dpr - h3, f3.y * dpr - h3, 2 * h3, 2 * h3); tem = true; } // poucas: halo em quadrado (sem arc por ponto)
        if (tem) { c.globalAlpha = fl * 0.2; c.fill(); }
      }
      // brilho na boca de onde a fita nasce
      if (vozAtual > 0.02) {
        var sp2 = sprite(cmis(CIANO, AZUL, 0.3)), s2 = S * dpr * (0.10 + 0.10 * vozAtual);
        c.globalAlpha = fl * 0.5 * vozAtual; c.drawImage(sp2, G.x0 * dpr - s2 / 2, (G.y0 + G.dy) * dpr - s2 / 2, s2, s2);
      }
    }
    function curvaSuave(c, xs, yc, hw, o, M) {
      var i, y0 = yc[0] + hw[0] * o, y1;
      c.moveTo(xs[0], y0);
      for (i = 1; i < M - 1; i++) { y0 = yc[i] + hw[i] * o; y1 = yc[i + 1] + hw[i + 1] * o; c.quadraticCurveTo(xs[i], y0, (xs[i] + xs[i + 1]) * 0.5, (y0 + y1) * 0.5); }
      c.lineTo(xs[M - 1], yc[M - 1] + hw[M - 1] * o);
    }
    function arcosDesenha(P) { // arcos finos de frente de onda (saindo a cada palavra; chegando a cada trecho ouvido)
      var c = ctx, G = geomOnda(), i, k;
      c.lineWidth = 0.9 * dpr;
      for (i = 0; i < arcos.length; i++) {
        var a = arcos[i], t = (T - a.t0) / a.vida, rr, al, cx = (G.x0 - S * 0.05) * dpr, cy = (G.y0 + G.dy) * dpr, cor, meia = Math.max(4, Math.min(cy - faixaY0 * dpr, faixaY1 * dpr - cy));
        if (a.sai) { rr = (14 + t * (G.L + 30)) * dpr; al = a.f * 0.55 * Math.pow(1 - t, 1.4) * suave(0, 0.05, t) * P.ondas; cor = degrade(ONDA_CORES, t); }
        else { rr = (8 + (1 - t) * G.L * 0.95) * dpr; al = a.f * 0.35 * Math.sin(PI * t) * peso.ouvindo; cor = CIANO; }
        if (al < 0.01) continue;
        c.strokeStyle = rgb(cor); // a altura do arco não passa da faixa livre (HUD em cima; rótulo e legenda embaixo)
        for (k = 0; k < 2; k++) { // o arco da frente e, num traço só, os dois de trás (mais fracos)
          c.beginPath();
          for (var m = k; m < (k ? 3 : 1); m++) { var r2 = rr - m * 5 * dpr; if (r2 <= 2) continue; var ab = Math.min(0.46, S * 0.8 * dpr / r2, Math.asin(Math.min(1, meia / r2))) - m * 0.03; if (ab <= 0.01) continue; c.moveTo(cx + r2 * Math.cos(-ab), cy + r2 * Math.sin(-ab)); c.arc(cx, cy, r2, -ab, ab); }
          c.globalAlpha = al * (k ? 0.55 : 1); c.stroke();
        }
      }
    }
    var COR_ENT = [rgb(cmis(CIANO, AZUL, 0.45)), rgb(cmis(CIANO, AZUL, 0.15)), rgb(cmis(CIANO, BRANCO, 0.3))], A_RAS = [0.16, 0.28, 0.45], A_CAB = [0.35, 0.6, 0.95];
    function entrada(P) { // partículas finas que chegam da direita, aceleram (rastro cresce) e são absorvidas pelo rosto
      var c = ctx, i, lv, e = peso.ouvindo * P.brilho, n = Math.min(chegando.length, EX.length), lw = dpr * lim(S / 220, 0.75, 1.3);
      for (i = 0; i < n; i++) {
        var p = chegando[i], tau = lim((T - p.t0) / p.vida, 0, 1), u = 0.55 * tau + 0.45 * tau * tau, m1 = 1 - u;
        var hx = m1 * m1 * p.sx + 2 * m1 * u * p.mx + u * u * p.tx, hy = m1 * m1 * p.sy + 2 * m1 * u * p.my + u * u * p.ty;
        var vx = m1 * (p.mx - p.sx) + u * (p.tx - p.mx), vy = m1 * (p.my - p.sy) + u * (p.ty - p.my), vn = Math.sqrt(vx * vx + vy * vy) || 1, rl = (5 + 9 * tau) * p.tm * lw / dpr / vn;
        EX[i] = hx * dpr; EY[i] = hy * dpr; EX0[i] = (hx - vx * rl) * dpr; EY0[i] = (hy - vy * rl) * dpr; ET[i] = p.tm;
        EA[i] = suave(0, 0.2, tau) * (0.35 + 0.65 * tau) * p.f * (1 - suave(0.95, 1, tau));
      }
      c.lineCap = 'round';
      for (lv = 0; lv < 3; lv++) { // 3 níveis de brilho: rastros num traço só e cabeças num fill só
        c.beginPath(); var tem = false;
        for (i = 0; i < n; i++) { if (EA[i] < 0.06 || (EA[i] > 0.62 ? 2 : EA[i] > 0.32 ? 1 : 0) !== lv) continue; c.moveTo(EX0[i], EY0[i]); c.lineTo(EX[i], EY[i]); tem = true; }
        if (!tem) continue;
        c.strokeStyle = COR_ENT[lv]; c.lineWidth = 0.8 * lw; c.globalAlpha = A_RAS[lv] * e; c.stroke();
        c.beginPath();
        for (i = 0; i < n; i++) { if (EA[i] < 0.06 || (EA[i] > 0.62 ? 2 : EA[i] > 0.32 ? 1 : 0) !== lv) continue; var tm = (0.75 + 0.35 * lv) * lw * ET[i]; c.rect(EX[i] - tm / 2, EY[i] - tm / 2, tm, tm); }
        c.fillStyle = COR_ENT[lv]; c.globalAlpha = A_CAB[lv] * e; c.fill();
      }
      var sp = sprite(CIANO);
      for (i = 0; i < claroes.length; i++) { // absorção: um brilho curto no ponto do rosto
        var q = claroes[i], k = (T - q.t0) / 0.35, rg = S * dpr * (0.012 + 0.02 * k); if (k < 0 || k > 1) continue;
        c.globalAlpha = (1 - k) * 0.6 * q.f * e; c.drawImage(sp, q.x * dpr - rg, q.y * dpr - rg, rg * 2, rg * 2);
      }
    }
    // ---------- pensando: neurônios em turbilhão no crânio (o centro gira mais rápido), com rastro curto ----------
    var nca = new Float32Array(NN), nsa = new Float32Array(NN), nrr = new Float32Array(NN), ativos = new Int16Array(NN);
    var CD = Math.cos(0.07), SD = Math.sin(0.07), SPR_NEU = null; // passo do rastro; sprites do pensando (refeitos com o layout)
    var COR_NEU = [rgb(cmis(VIOLETA, AZUL, 0.3)), rgb(cmis(VIOLETA, BRANCO, 0.25)), rgb(cmis(VIOLETA, BRANCO, 0.3))]; // sem núcleo branco estourado
    function neuronios(P) {
      var c = ctx, a = P.neur, t = T, i, j, k, lv, tem, lw = dpr * lim(S / 220, 0.75, 1.3), ax = cer[2], ay = cer[3], na = 0;
      if (!SPR_NEU) SPR_NEU = [sprite(VIOLETA, true), sprite(MAGENTA, true), sprite(cmis(VIOLETA, MAGENTA, 0.3))];
      // névoa do "cérebro" pulsando atrás da rede
      var pul = 0.75 + 0.25 * Math.sin(t * 2.3);
      c.globalAlpha = lim(a * 0.34 * pul, 0, 1); c.drawImage(SPR_NEU[0], cer[0] - ax * 1.7, cer[1] - ay * 2, ax * 3.4, ay * 4);
      c.globalAlpha = lim(a * 0.2 * (1.2 - pul * 0.4), 0, 1); c.drawImage(SPR_NEU[1], cer[0] - ax * 0.9, cer[1] - ay * 1.1, ax * 1.8, ay * 2.2);
      for (i = 0; i < NN; i++) { // posição na órbita (o centro gira mais rápido) e disparo; potências por quadrados (sem Math.pow)
        var an = NA[i] + NW[i] * t, rr = NR[i] * (1 + 0.05 * Math.sin(t * 0.9 + NPH[i])), ca = Math.cos(an), sa = Math.sin(an);
        nca[i] = ca; nsa[i] = sa; nrr[i] = rr;
        var x = cer[0] + ca * rr * ax, y = cer[1] + sa * rr * ay; npx[i] = x; npy[i] = y;
        var s1 = Math.sin(t * NFQ[i] * 2.1 + NPH[i]), s2 = Math.sin(t * 2.2 - NR[i] * 8), p1 = 0, p2 = 0, q4;
        if (s1 > 0) { p1 = s1 * s1; p1 *= p1; p1 *= p1; p1 *= p1; } // ^16
        if (s2 > 0) { q4 = s2 * s2; q4 *= q4; p2 = q4 * q4; p2 *= p2; p2 *= q4; } // ^20
        var pis = Math.min(1.2, p1 + 0.7 * p2), bb = (0.32 + 0.85 * pis) * suave(-0.9, -0.6, (x / dpr - OX) / S) * suave(-0.14, 0.02, (y / dpr - OY) / S); // somem na nuca e no alto, como a malha
        npi[i] = pis; nbr[i] = bb;
        if (pis > 0.03 && bb > 0.05) ativos[na++] = i; // só estes podem acender ligações
      }
      // rastros das órbitas (4 amostras de 0,07 rad para trás, girando cos/sen): dão a sensação de giro
      for (lv = 0; lv < 2; lv++) {
        c.beginPath(); tem = false;
        for (i = 0; i < NN; i++) {
          if (nbr[i] < 0.05 || (nbr[i] > 0.55 ? 1 : 0) !== lv) continue;
          var cx = nca[i], sy = nsa[i], rx = nrr[i] * ax, ry = nrr[i] * ay;
          c.moveTo(npx[i], npy[i]);
          for (k = 1; k <= 4; k++) { var cn = cx * CD + sy * SD; sy = sy * CD - cx * SD; cx = cn; c.lineTo(cer[0] + cx * rx, cer[1] + sy * ry); }
          tem = true;
        }
        if (tem) { c.strokeStyle = COR_NEU[lv]; c.lineWidth = (lv ? 1 : 0.7) * lw; c.globalAlpha = lim(a * (lv ? 0.4 : 0.2), 0, 1); c.stroke(); }
      }
      // ligações só entre vizinhos próximos (< 0,08 da cabeça), acesas pelo disparo; 3 níveis de brilho.
      // Só os nós que disparam procuram vizinhos (par de dois que disparam conta uma vez)
      var lm = 0.08 * S * dpr, lm2 = lm * lm, np = 0, n0 = parA.length;
      for (k = 0; k < na && np < n0; k++) {
        i = ativos[k]; var x0 = npx[i], y0 = npy[i], pi0 = npi[i], b0 = nbr[i];
        for (j = 0; j < NN; j++) {
          var bj = nbr[j]; if (j === i || bj < 0.05 || (j < i && npi[j] > 0.03)) continue;
          var dx = x0 - npx[j], dy = y0 - npy[j], d2 = dx * dx + dy * dy; if (d2 > lm2) continue;
          var f = (1 - Math.sqrt(d2) / lm) * (pi0 > npi[j] ? pi0 : npi[j]) * (b0 < bj ? b0 : bj) * 2, nv = f > 0.5 ? 2 : f > 0.22 ? 1 : f > 0.07 ? 0 : 3;
          if (nv > 2) continue;
          parA[np] = i; parB[np] = j; parN[np] = nv; if (++np >= n0) break;
        }
      }
      for (lv = 0; lv < 3; lv++) {
        c.beginPath(); tem = false;
        for (k = 0; k < np; k++) if (parN[k] === lv) { c.moveTo(npx[parA[k]], npy[parA[k]]); c.lineTo(npx[parB[k]], npy[parB[k]]); tem = true; }
        if (tem) { c.strokeStyle = COR_NEU[lv]; c.lineWidth = (0.6 + lv * 0.3) * lw; c.globalAlpha = lim(a * [0.22, 0.42, 0.6][lv], 0, 1); c.stroke(); }
      }
      // nós (3 níveis de brilho, um fill por nível) e brilho redondo nos que disparam (no máximo 14)
      for (lv = 0; lv < 3; lv++) {
        c.beginPath(); tem = false;
        for (i = 0; i < NN; i++) {
          var bn = nbr[i]; if (bn < 0.06 || (bn > 0.75 ? 2 : bn > 0.4 ? 1 : 0) !== lv) continue;
          var s = (0.8 + 0.35 * lv + 0.45 * npi[i]) * lw; c.rect(npx[i] - s / 2, npy[i] - s / 2, s, s); tem = true;
        }
        if (tem) { c.fillStyle = COR_NEU[lv]; c.globalAlpha = lim(a * [0.35, 0.6, 0.85][lv], 0, 1); c.fill(); }
      }
      var ns = 0;
      for (k = 0; k < na && ns < 14; k++) {
        i = ativos[k]; if (npi[i] < 0.4 || nbr[i] < 0.2) continue; ns++;
        var rg = (0.012 + 0.02 * Math.min(1, npi[i])) * S * dpr; c.globalAlpha = lim(a * nbr[i] * 0.5, 0, 1); c.drawImage(SPR_NEU[2], npx[i] - rg, npy[i] - rg, rg * 2, rg * 2);
      }
    }

    // ---------- laço ----------
    function medir(ms) {
      r.ms = r.ms ? r.ms * 0.92 + ms * 0.08 : ms;
      tempos.push(ms); if (tempos.length > 600) tempos.shift();
      if (manual) return;
      if (r.ms > 12) { lentos++; rapidos = 0; if (lentos > 45 && nivel < 2) { nivel++; lentos = 0; r.ms = 0; } }
      else if (r.ms < 5 && nivel > 0) { rapidos++; lentos = 0; if (rapidos > 240) { nivel--; rapidos = 0; } }
      else { lentos = 0; rapidos = 0; }
    }
    function laco(ts) {
      raf = 0;
      if (!vivo || pausado || manual) return;
      // limitador que acompanha telas de 75/90/120 Hz: marca o próximo instante alvo em passos fixos de 1/fps
      var iv = 1000 / Math.min(fpsMax, nivel >= 2 ? 30 : 60);
      if (proxT && ts < proxT + iv - 1.5) { raf = requestAnimationFrame(laco); return; }
      proxT = proxT && ts - proxT < 2 * iv ? proxT + iv : ts;
      var dt = ultimo ? Math.min(0.05, (ts - ultimo) / 1000) : 1 / 60; ultimo = ts;
      garante();
      var a = performance.now();
      passo(dt); desenha();
      medir(performance.now() - a);
      if (peso.livre >= 0.999 && alvo === 'livre' && !faiscas.length && !chegando.length) return; // apagado e parado: não gasta
      raf = requestAnimationFrame(laco);
    }
    function liga() { if (!raf && vivo && !pausado && !manual && !reduzido && !document.hidden) { ultimo = 0; proxT = 0; raf = requestAnimationFrame(laco); } }
    function vis() { if (document.hidden) { if (raf) cancelAnimationFrame(raf); raf = 0; } else liga(); }
    document.addEventListener('visibilitychange', vis);

    // ---------- quadro determinístico (teste) e estático (movimento reduzido) ----------
    function reinicia(semente) {
      aleat = gerador(semente); T = 0; energia = 0; somNivel = 0; somAlvo = 0; boca = 0; vozAtual = 0; vozS = 0; eo = 0; rajada = 0; histI = -1; HIST.fill(0);
      silF = 0; silA = 0.7; silN = 0; palT = -9; palEnv = 0;
      ondasMalha = []; arcos = []; faiscas = []; chegando = []; claroes = []; entradaAcum = 0; faiscaAcum = 0; pensaT = -9;
      for (var i = 0; i < NOMES.length; i++) peso[NOMES[i]] = NOMES[i] === alvo ? 1 : 0;
    }
    function simula(t) { // roteiro fixo por estado: blocos de fala com palavras a cada ~0,3 s; trechos ouvidos
      var dt = 1 / 60, forcas = [0.75, 0.45, 0.85, 0.5, 0.62, 0.95, 0.4, 0.7, 0.55, 0.9, 0.48, 0.66], prox = 0.08, np = 0, ouv = [0.35, 1.05, 1.75, 2.45];
      reinicia(12345);
      var pre = alvo === 'falando' ? 0.6 : 2.2; // aquece partículas antes do instante zero
      T = -pre; histI = -1;
      var somOn = false;
      while (T < t - 1e-6) {
        var tt = T;
        if (alvo === 'falando' && tt >= 0) {
          var bl = tt % 2.8, dentro = bl < 2.5;
          if (dentro !== somOn) { somOn = dentro; somAlvo = dentro ? 1 : 0; }
          if (tt >= prox) { if (dentro) { var f = forcas[np++ % forcas.length]; pulsoInt(f); } prox += 0.3; }
        }
        if (alvo === 'ouvindo' && np < ouv.length && tt >= ouv[np]) { pulsoInt(0.85); np++; }
        passo(Math.min(dt, t - T));
      }
    }
    function quadro(t) { manual = true; if (raf) cancelAnimationFrame(raf); raf = 0; garante(); var nv = nivel; nivel = 0; simula(Math.max(0, t)); var a = performance.now(); desenha(); medir(performance.now() - a); nivel = nv; }
    function desenhaEstatico() { var m = manual; manual = true; garante(); simula(alvo === 'falando' ? 1.62 : alvo === 'ouvindo' ? 2.05 : 1.3); desenha(); manual = m; }

    // ---------- API ----------
    function pulsoInt(f) {
      f = lim(f == null ? 0.5 : f, 0, 1);
      if (alvo === 'falando') {
        energia = Math.min(1, energia + f * 0.6); if (arcos.length < 10) arcos.push({ t0: T, f: f, sai: true, vida: 1.5 });
        // palavra nova: a boca recomeça o ciclo (se já passou da abertura) com a força da palavra
        var nova = silF > 0.3; if (nova) silF = 0;
        silA = Math.max(nova ? 0 : silA, 0.55 + 0.45 * f); palT = T; palEnv = 1;
      }
      else if (alvo === 'ouvindo') {
        eo = Math.min(1, eo + f); rajada = Math.min(150, rajada + 10 + 16 * f);
        if (ondasMalha.length < 5) ondasMalha.push({ t0: T, f: f }); if (arcos.length < 10) arcos.push({ t0: T, f: f, sai: false, vida: 1.0 });
      }
      else energia = Math.min(1, energia + f * 0.3);
    }
    r.estado = function (n) {
      if (!EST[n]) return; var novo = n !== alvo; alvo = n;
      if (n !== 'falando') somAlvo = 0;
      if (reduzido) { if (novo) desenhaEstatico(); return; }
      liga();
    };
    r.pulso = function (f) { if (reduzido) return; pulsoInt(f); liga(); };
    r.som = function (on) { somAlvo = on ? 1 : 0; if (!reduzido) liga(); };
    r.palco = function (x, y, w, h) { palcoR = { x: +x || 0, y: +y || 0, w: Math.max(10, +w || 0), h: Math.max(10, +h || 0) }; arruma(); };
    r.redimensionar = redimensionar;
    // aquecer(): com o rosto ainda escondido e o app ocioso, adianta o trabalho do 1º quadro, um passo por chamada (um toque
    // não espera tudo): geometria e buffers → névoa → fixo do 'ouvindo'. true = não falta nada.
    r.aquecer = function () {
      if (!vivo) return true;
      if (sujo) { sujo = false; calcula(); return false; }
      if (!nevoa) { preparaNevoa(); return false; }
      if (bufs[0].pronto[0] !== (nivel < 2 ? 2 : 1)) carimbaFixo(0);
      return true;
    };
    r.pausar = function () { pausado = true; if (raf) cancelAnimationFrame(raf); raf = 0; };
    r.retomar = function () { pausado = false; manual = false; liga(); };
    r.destruir = function () {
      vivo = false; if (raf) cancelAnimationFrame(raf); if (agEst) cancelAnimationFrame(agEst); raf = agEst = 0;
      document.removeEventListener('visibilitychange', vis);
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, canvas.width, canvas.height);
      soltaBufs(); bufs = null; nevoa = null; sprites = {}; faiscas = []; chegando = []; arcos = [];
    };
    r.quadro = quadro;
    // diagnóstico (teste de desempenho): tempos dos últimos quadros, nível de detalhe e nº de pontos da malha
    r.tempos = function () { return tempos.slice(); };
    r.nivel = function () { return nivel; };
    r.pontos = function () { return N; };
    redimensionar();
    return r;
  }
  // preparar(prazo): calcula a malha padrão com o app ocioso, em pedaços (o 1º núcleo abre sem o travão do cálculo)
  window.CapitaoRosto = { criar: criar, preparar: preparar };
})();
