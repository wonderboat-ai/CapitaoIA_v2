"""Publicação de verdade, com service worker e cache HTTP reais (Edge headless) — não chama o Worker, não gasta cota.
Servidor local imita o GitHub Pages (Cache-Control max-age + ETag/304). Versões: A = a publicada (padrão origin/main) ·
B = esta árvore de trabalho · B2 = B com a versão trocada para '<versão>-teste' (outra publicação). Cenários:
 1) app aberto e usado na A; publica B; reabre (navegação servida pelo SW velho, arquivos do cache HTTP) → o SW novo
    ativa e recarrega a tela sozinho → roda B inteira ("Oque você faz?" = saudação). Pulado se A e B têm a mesma versão.
 2) app aberto na B; publica B2; a tela volta para a frente (visibilitychange) → procura versão → recarrega em B2.
 3) sem internet: SOS e início abrem do cache.
 4) sinal fraco (servidor demora 8 s): a tela abre da cópia guardada em ~4 s.

    python -X utf8 testes/publicacao.py [ref-publicada]        (antes do merge: compara com a versão no ar)
"""
import hashlib, http.server, io, mimetypes, os, shutil, subprocess, sys, tarfile, tempfile, threading, time, urllib.parse
from playwright.sync_api import sync_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = sys.argv[1] if len(sys.argv) > 1 else 'origin/main'
TMP = tempfile.mkdtemp(prefix='pub_')
A, B, B2 = os.path.join(TMP, 'A'), REPO, os.path.join(TMP, 'B2')
os.makedirs(A)
tar = subprocess.run(['git', '-C', REPO, 'archive', REF], capture_output=True, check=True).stdout
tarfile.open(fileobj=io.BytesIO(tar)).extractall(A, filter='data')
shutil.copytree(REPO, B2, ignore=shutil.ignore_patterns('.git', 'testes', 'ferramentas', 'integracoes', 'guia-rapido'))
import re
VA = re.search(r"v: '([^']+)'", open(os.path.join(A, 'capitao-auth.js'), encoding='utf-8').read()).group(1)
VB = re.search(r"v: '([^']+)'", open(os.path.join(REPO, 'capitao-auth.js'), encoding='utf-8').read()).group(1)
VB2 = VB + '-teste'
for arq, velho, novo in [('sw.js', 'capitao-site-v' + VB, 'capitao-site-v' + VB2), ('capitao-auth.js', "v: '%s'" % VB, "v: '%s'" % VB2),
                         ('capitao-brain.js', "var VERSAO = '%s'" % VB, "var VERSAO = '%s'" % VB2), ('capitao-ia.js', "var VERSAO = '%s'" % VB, "var VERSAO = '%s'" % VB2)]:
    p = os.path.join(B2, arq); s = open(p, encoding='utf-8').read(); assert velho in s, arq; open(p, 'w', encoding='utf-8', newline='\n').write(s.replace(velho, novo))

ESTADO = {'raiz': A, 'lento': 0, 'maxage': 60}
T0 = time.time()


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        rel = urllib.parse.unquote(self.path.split('?')[0].split('#')[0].lstrip('/')) or 'index.html'
        f = os.path.join(ESTADO['raiz'], rel)
        if ESTADO['lento'] and rel.endswith('.html'):
            time.sleep(ESTADO['lento'])
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


srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:%d/' % srv.server_address[1]
SESSAO = "(() => { const n = Date.now(); try { localStorage.setItem('capitao.sessao.v1', JSON.stringify({ u: 'lucas', em: n, exp: n + 3600e3 })); } catch (e) {} })()"
SONDA = """() => { let k = null; try { k = CapitaoBrain.answer('Oque você faz?', { platform: 'app', commit: false }).key; } catch (e) { k = 'erro'; }
  return { auth: window.CapitaoAuth && CapitaoAuth.VERSAO.v, brain: window.CapitaoBrain && (CapitaoBrain.VERSAO || (CapitaoBrain.pedeIA ? '1.0.5' : 'antes da 1.0.5')),
           ia: window.CapitaoIA && (CapitaoIA.VERSAO || (CapitaoIA.estado ? '1.0.5' : 'antes da 1.0.5')), oque: k, sw: !!navigator.serviceWorker.controller, marca: !!window.__marca }; }"""
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
    else:
        print('(cenário 1 pulado: %s já tem a versão %s desta árvore)' % (REF, VB))
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
    ok('sem erro de script', not erros, '; '.join(erros))
    b.close()
srv.shutdown()
shutil.rmtree(TMP, ignore_errors=True)
for nome, bom, extra in res:
    print(('OK    ' if bom else 'FALHA ') + nome + ('  → ' + extra if (not bom or nome.startswith('1) logo')) else ''))
print('%d conferências · %d falhas' % (len(res), len([r for r in res if not r[1]])))
sys.exit(1 if any(not r[1] for r in res) else 0)
