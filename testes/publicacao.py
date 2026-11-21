"""Publicação de verdade, com service worker e cache HTTP reais (Edge headless) — não chama o Worker, não gasta cota.
Servidor local imita o GitHub Pages (Cache-Control max-age + ETag/304). Versões: A = a publicada (padrão origin/main) ·
B = esta árvore de trabalho · B2 = B com a versão trocada para '<versão>-teste' (outra publicação). Cenários:
 1) app aberto e usado na A; publica B; reabre (navegação servida pelo SW velho, arquivos do cache HTTP) → o SW novo
    ativa e recarrega a tela sozinho → roda B inteira ("Oque você faz?" = saudação). Pulado se A e B têm a mesma versão.
 2) app aberto na B; publica B2; a tela volta para a frente (visibilitychange) → procura versão → recarrega em B2.
 2b) versão nova com texto sendo digitado: a tela espera; enquanto espera, o cache da versão nova já tem o React (CORE).
 3) sem internet: SOS e início abrem do cache.
 4) sinal fraco (servidor demora 8 s): a tela abre da cópia guardada em ~4 s.
 4b) sinal fraco só no React (assets/vendor, versão fixa no caminho): sai da cópia guardada sem esperar a rede.
 Da B em diante, unpkg.com fora do ar (React do próprio site, paridade Avanti 1.24.0): nenhum pedido a ele.
 5) A instalada; publica B e a conexão cai logo depois do support.js da B (o SW da B não instala, o da A fica com o support.js
    novo sem o React de assets/vendor) → sem internet, o SOS abre (reserva do support.js: o React do unpkg, com o mesmo SRI,
    que o cache da A guarda). Pulado se A e B têm o mesmo support.js.

    python -X utf8 testes/publicacao.py [ref-publicada]        (antes do merge: compara com a versão no ar)
"""
import hashlib, http.server, io, mimetypes, os, shutil, subprocess, sys, tarfile, tempfile, threading, time, urllib.parse
from playwright.sync_api import sync_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = sys.argv[1] if len(sys.argv) > 1 else 'origin/main'
TMP = tempfile.mkdtemp(prefix='pub_')
A, B, B2, B3 = os.path.join(TMP, 'A'), REPO, os.path.join(TMP, 'B2'), os.path.join(TMP, 'B3')
os.makedirs(A)
tar = subprocess.run(['git', '-C', REPO, 'archive', REF], capture_output=True, check=True).stdout
tarfile.open(fileobj=io.BytesIO(tar)).extractall(A, filter='data')
for destino in (B2, B3):
    shutil.copytree(REPO, destino, ignore=shutil.ignore_patterns('.git', 'testes', 'ferramentas', 'integracoes', 'guia-rapido'))
import re
VA = re.search(r"v: '([^']+)'", open(os.path.join(A, 'capitao-auth.js'), encoding='utf-8').read()).group(1)
VB = re.search(r"v: '([^']+)'", open(os.path.join(REPO, 'capitao-auth.js'), encoding='utf-8').read()).group(1)
VB2, VB3 = VB + '-teste', VB + '-teste2'
for pasta, vn in ((B2, VB2), (B3, VB3)):
    for arq, velho, novo in [('sw.js', 'capitao-site-v' + VB, 'capitao-site-v' + vn), ('capitao-auth.js', "v: '%s'" % VB, "v: '%s'" % vn),
                             ('capitao-brain.js', "var VERSAO = '%s'" % VB, "var VERSAO = '%s'" % vn), ('capitao-ia.js', "var VERSAO = '%s'" % VB, "var VERSAO = '%s'" % vn)]:
        p = os.path.join(pasta, arq); s = open(p, encoding='utf-8').read(); assert velho in s, arq; open(p, 'w', encoding='utf-8', newline='\n').write(s.replace(velho, novo))

ESTADO = {'raiz': A, 'lento': 0, 'lento_vendor': 0, 'maxage': 60, 'cai_depois': '', 'caiu': False, 'sem_sw': False}
T0 = time.time()


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        try:
            self.responde()
        except (BrokenPipeError, ConnectionResetError):
            pass  # sinal fraco: o navegador desistiu da resposta lenta (a tela já abriu da cópia guardada)

    def responde(self):
        rel = urllib.parse.unquote(self.path.split('?')[0].split('#')[0].lstrip('/')) or 'index.html'
        if ESTADO['caiu'] or (ESTADO['sem_sw'] and rel == 'sw.js'):
            self.close_connection = True
            return  # conexão caiu (cenário 5): resposta vazia, erro de rede no navegador
        f = os.path.join(ESTADO['raiz'], rel)
        if ESTADO['lento'] and rel.endswith('.html'):
            time.sleep(ESTADO['lento'])
        if ESTADO['lento_vendor'] and rel.startswith('assets/vendor/'):
            time.sleep(ESTADO['lento_vendor'])
        if not os.path.isfile(f):
            self.send_response(404); self.end_headers(); return
        dados = open(f, 'rb').read()
        etag = '"' + hashlib.md5(dados).hexdigest() + '"'
        st = 304 if self.headers.get('If-None-Match') == etag else 200
        self.send_response(st)
        self.send_header('Cache-Control', 'max-age=%d' % ESTADO['maxage'])
        self.send_header('ETag', etag)
        if st == 200:
            ct = 'application/javascript; charset=utf-8' if f.endswith('.js') else 'text/html; charset=utf-8' if f.endswith('.html') else (mimetypes.guess_type(f)[0] or 'application/octet-stream')
            self.send_header('Content-Type', ct); self.send_header('Content-Length', str(len(dados))); self.end_headers(); self.wfile.write(dados)
        else:
            self.end_headers()
        if ESTADO['cai_depois'] and rel == ESTADO['cai_depois']:
            ESTADO['caiu'] = True


srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:%d/' % srv.server_address[1]
SESSAO = "(() => { const n = Date.now(); try { localStorage.setItem('capitao.sessao.v1', JSON.stringify({ u: 'lucas', em: n, exp: n + 3600e3 })); } catch (e) {} })()"
SONDA = """() => { let k = null; try { k = CapitaoBrain.answer('Oque você faz?', { platform: 'app', commit: false }).key; } catch (e) { k = 'erro'; }
  return { auth: window.CapitaoAuth && CapitaoAuth.VERSAO.v, brain: window.CapitaoBrain && (CapitaoBrain.VERSAO || (CapitaoBrain.pedeIA ? '1.0.5' : 'antes da 1.0.5')),
           ia: window.CapitaoIA && (CapitaoIA.VERSAO || (CapitaoIA.estado ? '1.0.5' : 'antes da 1.0.5')), oque: k, sw: !!navigator.serviceWorker.controller, marca: !!window.__marca }; }"""
# o React (assets/vendor) no cache da versão: só depois de a versão ativar (o cache anterior já apagado)
REACT_GUARDADO = """async (nome) => { const ks = await caches.keys(); if (ks.indexOf(nome) < 0) return { caches: ks };
  const c = await caches.open(nome);
  return { caches: ks, react: await Promise.all(['react.production.min.js', 'react-dom.production.min.js'].map((a) =>
    c.match(new URL('assets/vendor/react-18.3.1/' + a, location.href).href).then(Boolean))) }; }"""
# cenário 5: o que o cache da versão publicada guardou (sha-256 do support.js e se tem o React de assets/vendor)
CACHE_A = """async (nome) => { const ks = await caches.keys(); if (ks.indexOf(nome) < 0) return { caches: ks };
  const c = await caches.open(nome), s = await c.match(new URL('support.js', location.href).href);
  const h = s ? Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', await s.arrayBuffer()))).map((x) => x.toString(16).padStart(2, '0')).join('') : null;
  return { caches: ks, support: h, sw: !!navigator.serviceWorker.controller, vendor: await Promise.all(['react.production.min.js', 'react-dom.production.min.js'].map((a) =>
    c.match(new URL('assets/vendor/react-18.3.1/' + a, location.href).href).then(Boolean))) }; }"""
res = []


def ok(nome, cond, extra=''):
    res.append((nome, bool(cond), str(extra)[:400]))


def pronta(pg, t=20000):
    pg.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0 && !!window.CapitaoBrain", timeout=t)


with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
    ctx.add_init_script(SESSAO)
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append(str(e)[:200]))

    def espera_versao(v, segundos=25):
        """A tela recarrega sozinha: espera até auth, cérebro e cliente da IA estarem na versão v."""
        fim, s = time.time() + segundos, {}
        while time.time() < fim:
            try:
                pronta(pg, 5000); s = pg.evaluate(SONDA)
                if s['auth'] == v and s['brain'] == v and s['ia'] == v:
                    break
            except Exception:
                pass
            time.sleep(1)
        return s

    # React do próprio site: da B em diante, unpkg.com fora do ar e nenhum pedido a ele. A publicada (A) pode ser anterior e
    # ainda usar o unpkg — o cenário 1 roda antes do corte.
    unpkg = []
    def corta_unpkg():
        ctx.on('request', lambda r: unpkg.append(r.url) if re.search(r'(^|\.)unpkg\.com$', urllib.parse.urlparse(r.url).hostname or '') else None)
        ctx.route('https://unpkg.com/**', lambda rt: rt.abort('connectionrefused'))

    if VA != VB:
        # 1) A instalada e usada (SW da A + cache HTTP fresco dos arquivos da A)
        pg.goto(BASE + 'H2-Home-Mobile.dc.html'); pronta(pg)
        pg.wait_for_function('() => navigator.serviceWorker.ready.then(() => true)', timeout=20000)
        pg.reload(); pronta(pg); pg.wait_for_timeout(1500)
        s = pg.evaluate(SONDA)
        ok('1) antes: app na %s com SW controlando' % VA, s['auth'] == VA and s['sw'], s)
        # publica B e "reabre" o app (nova navegação para a mesma tela, dentro do max-age)
        ESTADO['raiz'] = B
        pg.evaluate('() => { window.__marca = true; }')
        pg.goto(BASE + 'H2-Home-Mobile.dc.html'); pronta(pg)
        s0 = pg.evaluate(SONDA)
        s = espera_versao(VB)
        ok('1) logo depois de publicar, a 1ª abertura ainda pode vir velha (servida pelo SW da %s com o cache HTTP)' % VA, True, s0)
        ok('1) sem tocar em nada, a tela se recarrega sozinha e roda a %s inteira (SW novo ativa e recarrega)' % VB, s.get('auth') == VB and s.get('brain') == VB and s.get('ia') == VB and s.get('oque') == 'saudacao', s)
        corta_unpkg()
    else:
        print('(cenário 1 pulado: %s já tem a versão %s desta árvore)' % (REF, VB))
        corta_unpkg()
        ESTADO['raiz'] = B
        pg.goto(BASE + 'H2-Home-Mobile.dc.html'); pronta(pg)
        pg.wait_for_function('() => navigator.serviceWorker.ready.then(() => true)', timeout=20000)
        pg.reload(); pronta(pg); pg.wait_for_timeout(1500)

    # 2) app aberto na B; publica B2; a tela volta para a frente → procura versão → recarrega em B2
    time.sleep(1.5)
    ESTADO['raiz'] = B2
    pg.evaluate("() => { window.__marca = true; document.dispatchEvent(new Event('visibilitychange')); }")
    s = espera_versao(VB2)
    ok('2) app aberto; publica outra versão; ao voltar para a frente, procura, acha e recarrega sozinho nela', s.get('auth') == VB2 and s.get('brain') == VB2 and s.get('ia') == VB2 and not s.get('marca'), s)

    # 2b) versão nova chega com texto sendo digitado: a tela NÃO recarrega (não perde o texto); esvaziou o campo, recarrega
    time.sleep(1.5)
    pg.fill('#pergunta-m', 'texto que o usuário está digitando')
    ESTADO['raiz'] = B3
    pg.evaluate("() => { window.__marca = true; navigator.serviceWorker.getRegistration().then((r) => r && r.update()); }")
    time.sleep(9)
    try:
        s = pg.evaluate(SONDA); campo = pg.evaluate("() => document.querySelector('#pergunta-m').value")
    except Exception as e:
        s, campo = {'marca': False, 'erro': str(e)[:100]}, ''
    ok('2b) versão nova com texto sendo digitado: a tela espera (não recarrega nem perde o texto)', s.get('marca') and campo == 'texto que o usuário está digitando', (s, campo))
    # React no CORE do sw.js: a B3 ativou (o cache da B2 já foi apagado) e a tela ainda não recarregou — nenhuma tela pediu o
    # React à B3, então só a instalação pode tê-lo guardado. Sem o CORE, o cache HTTP esconderia a falta nos cenários offline.
    try:
        g = pg.evaluate(REACT_GUARDADO, 'capitao-site-v' + VB3)
    except Exception as e:
        g = {'erro': str(e)[:100]}
    ok('2b) a versão nova ativa já com o React no cache (CORE do sw.js, instalação tudo ou nada)', g.get('caches') == ['capitao-site-v' + VB3] and g.get('react') == [True, True], g)
    pg.fill('#pergunta-m', '')
    s = espera_versao(VB3)
    ok('2b) campo vazio: recarrega sozinha na versão nova', s.get('auth') == VB3 and s.get('brain') == VB3 and not s.get('marca'), s)

    # visita o SOS uma vez com internet (fica guardado também pelo precache)
    pg.goto(BASE + 'S2-SOS-Mobile.dc.html'); pg.wait_for_timeout(2500)

    # 3) sem internet: SOS e início abrem do cache
    ctx.set_offline(True)
    pg.goto(BASE + 'S2-SOS-Mobile.dc.html'); pg.wait_for_timeout(2500)
    t = pg.evaluate('() => document.body.innerText')
    ok('3) sem internet: o SOS abre do cache', 'CANAL 16' in t.upper() or 'MAYDAY' in t.upper(), t[:200])
    pg.goto(BASE + 'H2-Home-Mobile.dc.html')
    try:
        pronta(pg, 15000); t = 'ok'
    except Exception:
        t = pg.evaluate('() => document.body.innerText')[:200]
    ok('3) sem internet: o início abre do cache', t == 'ok', t)
    ctx.set_offline(False)

    # 4) sinal fraco: o servidor demora 8 s nas telas; a tela abre da cópia guardada em ~4 s
    ESTADO['lento'] = 8
    t1 = time.time()
    pg.goto(BASE + 'H2-Home-Mobile.dc.html', timeout=30000)
    try:
        pronta(pg, 20000)
    except Exception:
        pass
    dt = time.time() - t1
    ESTADO['lento'] = 0
    ok('4) sinal fraco (servidor 8 s): a tela abre da cópia guardada em menos de 7 s', dt < 7, '%.1f s' % dt)

    # 4b) sinal fraco só no React: versão fixa no caminho, sai da cópia guardada na hora (sem mais um prazo de 4 s)
    ESTADO['lento_vendor'] = 8
    t1 = time.time()
    pg.goto(BASE + 'H2-Home-Mobile.dc.html', timeout=30000)
    try:
        pronta(pg, 20000)
    except Exception:
        pass
    dt = time.time() - t1
    ESTADO['lento_vendor'] = 0
    ok('4b) sinal fraco no React (servidor 8 s em assets/vendor): sai da cópia guardada, a tela abre em menos de 4 s', dt < 4, '%.1f s' % dt)
    ok('da %s em diante, com o unpkg fora do ar, nenhum pedido a ele (React de assets/vendor)' % VB, not unpkg, '; '.join(unpkg[:3]))
    ok('sem erro de script', not erros, '; '.join(erros))

    # 5) troca de versão com a conexão caindo logo depois do support.js novo, noutro contexto (SW e caches próprios). O SW da A
    # guarda arquivo por arquivo: fica com o support.js da B e sem o React de assets/vendor (só a instalação da B o traria, e
    # ela não acontece). Sem internet, o SOS tem de abrir assim mesmo. Roda depois de todos os outros: o servidor é um só.
    sup = lambda d: open(os.path.join(d, 'support.js'), 'rb').read()
    if sup(A) == sup(B):
        print('(cenário 5 pulado: %s tem o mesmo support.js desta árvore)' % REF)
    else:
        c5 = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        c5.add_init_script(SESSAO)
        p5 = c5.new_page()
        erros5 = []
        p5.on('pageerror', lambda e: erros5.append(str(e)[:200]))
        ESTADO['raiz'] = A
        p5.goto(BASE + 'H2-Home-Mobile.dc.html'); pronta(p5)
        p5.wait_for_function('() => navigator.serviceWorker.ready.then(() => true)', timeout=20000)
        p5.reload(); pronta(p5); p5.wait_for_timeout(1500)
        # publica B; o app abre uma vez com sinal fraco: o sw.js novo não chega e a conexão cai logo depois do support.js
        ESTADO.update(raiz=B, sem_sw=True, cai_depois='support.js')
        try:
            p5.goto(BASE + 'Main.dc.html', timeout=15000)
        except Exception:
            pass
        p5.wait_for_timeout(4000)
        try:
            g = p5.evaluate(CACHE_A, 'capitao-site-v' + VA)
        except Exception as e:
            g = {'erro': str(e)[:100]}
        # A sem o React no CORE (1.0.x, React do unpkg): o cache dela tem de ter ficado sem ele — é o risco que o cenário prova
        sem_core = 'assets/vendor/' not in open(os.path.join(A, 'sw.js'), encoding='utf-8').read()
        ok('5) conexão caiu logo depois do support.js novo: o SW publicado (%s, %s) segue no controle e o cache dele ficou com esse support.js%s' % (REF, VA, ' e sem o React de assets/vendor' if sem_core else ''),
           ESTADO['caiu'] and g.get('sw') and g.get('caches') == ['capitao-site-v' + VA] and g.get('support') == hashlib.sha256(sup(B)).hexdigest()
           and (not sem_core or g.get('vendor') == [False, False]), g)
        erros5.clear()
        c5.set_offline(True)
        try:
            p5.goto(BASE + 'S2-SOS-Mobile.dc.html')
            p5.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
            p5.wait_for_timeout(1000)
            t = p5.evaluate("() => (window.React && window.ReactDOM ? 'react ' : 'sem React ') + document.body.innerText")
        except Exception:
            t = 'não montou: ' + p5.evaluate('() => document.body.innerText')[:200].replace('\n', ' · ')
        ok('5) sem internet, o SOS abre mesmo assim (React de assets/vendor ou, sem ele no cache, a reserva do unpkg com o mesmo SRI)',
           t.startswith('react ') and ('CANAL 16' in t.upper() or 'MAYDAY' in t.upper()), t[:200])
        ok('5) SOS sem erro de script', not erros5, '; '.join(erros5))
        c5.close()
        ESTADO.update(raiz=B, sem_sw=False, cai_depois='', caiu=False)
    b.close()
srv.shutdown()
shutil.rmtree(TMP, ignore_errors=True)
for nome, bom, extra in res:
    print(('OK    ' if bom else 'FALHA ') + nome + ('  → ' + extra if (not bom or nome.startswith('1) logo')) else ''))
print('%d conferências · %d falhas' % (len(res), len([r for r in res if not r[1]])))
sys.exit(1 if any(not r[1] for r in res) else 0)
