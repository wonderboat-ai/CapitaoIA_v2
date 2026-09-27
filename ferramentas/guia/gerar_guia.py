# -*- coding: utf-8 -*-
"""Capitão IA — gera as capturas do Guia rápido e do Manual e o PDF A4 do Guia (Playwright).

Uso, na raiz do repositório:
    python ferramentas/guia/gerar_guia.py            capturas + PDF
    python ferramentas/guia/gerar_guia.py --so-pdf   só o PDF (usa as capturas que já existem)
Saída: guia-rapido/img/*.jpg (tema claro) e Guia-Rapido-Capitao-IA.pdf (A4, fundo impresso).
Navegador: Edge instalado (channel="msedge"); troque CANAL para "chrome" se preferir.
Sobe um servidor local próprio (porta livre) — não depende de outro servidor rodando.
"""
import functools
import http.server
import os
import socketserver
import sys
import threading
from playwright.sync_api import sync_playwright

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
IMG = os.path.join(RAIZ, 'guia-rapido', 'img')
HTML = os.path.join(RAIZ, 'guia-rapido', 'Guia-Rapido-Capitao-IA.html')
PDF = os.path.join(RAIZ, 'Guia-Rapido-Capitao-IA.pdf')
CANAL = 'msedge'
MOBILE_UA = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Mobile Safari/537.36'
SESSAO = "(() => { const n = Date.now(); localStorage.setItem('capitao.sessao.v1', JSON.stringify({ u: 'lucas', em: n, exp: n + 3600e3 })); localStorage.setItem('capitao.tema.v1', 'claro'); localStorage.setItem('capitao.saudacao.v1', '3'); })()"


class Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def servidor():
    h = functools.partial(Silencioso, directory=RAIZ)
    s = socketserver.ThreadingTCPServer(('127.0.0.1', 0), h)
    s.daemon_threads = True
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, 'http://127.0.0.1:%d/' % s.server_address[1]


def sem_ia(ctx):
    """Capturas com o app só no aparelho: o cliente da IA sem URL (a resposta da IA varia e o aparelho de captura não tem a
    chave — sem isto, a resposta do guia sairia com "IA na nuvem desligada neste aparelho" e o botão de ativar)."""
    cliente = os.path.join(RAIZ, 'integracoes', 'ia-cliente', 'capitao-ia.js')
    ctx.route('**/capitao-ia.js', lambda rt: rt.fulfill(path=cliente, content_type='text/javascript; charset=utf-8'))


def pronta(pg):
    pg.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=20000)
    pg.wait_for_timeout(1400)


def capturas(b, base):
    os.makedirs(IMG, exist_ok=True)

    def app(nome, tela, antes=None, recorte=None, sessao=True):
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True, user_agent=MOBILE_UA, service_workers='block')
        ctx.add_init_script(SESSAO if sessao else "localStorage.setItem('capitao.tema.v1', 'claro');")
        sem_ia(ctx)
        pg = ctx.new_page()
        pg.goto(base + tela, wait_until='load')
        if tela.endswith('.dc.html'):
            pronta(pg)
        else:
            pg.wait_for_timeout(900)
        if antes:
            antes(pg)
        kw = {'path': os.path.join(IMG, nome), 'type': 'jpeg', 'quality': 82}
        if recorte:
            kw['clip'] = recorte
        pg.screenshot(**kw)
        ctx.close()
        print('  ', nome)

    def web(nome, tela, antes=None):
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1, service_workers='block')
        ctx.add_init_script(SESSAO)
        sem_ia(ctx)
        pg = ctx.new_page()
        pg.goto(base + tela, wait_until='load')
        pronta(pg)
        if antes:
            antes(pg)
        pg.screenshot(path=os.path.join(IMG, nome), type='jpeg', quality=82)
        ctx.close()
        print('  ', nome)

    def pergunta(q):
        def f(pg):
            pg.fill('#pergunta-m', q)
            pg.press('#pergunta-m', 'Enter')
            pg.wait_for_timeout(1500)
        return f

    def voz(estado, texto):
        def f(pg):
            pg.evaluate("([e, t]) => window.dispatchEvent(new CustomEvent('capitao-voz', { detail: { estado: e, texto: t } }))", [estado, texto])
            pg.wait_for_timeout(1200)
        return f

    def resposta_voz(pg):
        t = pg.evaluate("() => window.CapitaoBrain.falaCurta(window.CapitaoBrain.answer('Quantas horas tem o gerador?', { platform: 'app', commit: false }))")
        voz('falando', t)(pg)

    app('login-app.jpg', 'login.html', sessao=False)
    app('inicio-app.jpg', 'H2-Home-Mobile.dc.html')
    app('resposta-gerador-app.jpg', 'H2-Home-Mobile.dc.html', pergunta('Como ligar o gerador?'))
    app('resposta-semdados-app.jpg', 'H2-Home-Mobile.dc.html', pergunta('Qual o preço do diesel hoje?'))
    app('voz-escuta-app.jpg', 'H2-Home-Mobile.dc.html', voz('ouvindo', 'Quantas horas tem o gerador?'))
    app('voz-resposta-app.jpg', 'H2-Home-Mobile.dc.html', resposta_voz)
    app('console-app.jpg', 'A2-Ponte-Mobile.dc.html')
    app('editar-atalhos-app.jpg', 'H3-Atalhos-Editar.dc.html')
    app('faq-gerador-app.jpg', 'F4-FAQ-Gerador.dc.html')
    app('diario-app.jpg', 'G3-Diario-Mobile.dc.html')
    app('sos-app.jpg', 'S2-SOS-Mobile.dc.html')
    app('rodape-app.jpg', 'H2-Home-Mobile.dc.html', recorte={'x': 0, 'y': 800, 'width': 390, 'height': 44}, antes=lambda pg: pg.evaluate("() => window.scrollTo(0, document.body.scrollHeight)"))
    web('inicio-web.jpg', 'Main.dc.html')
    web('manutencao-web.jpg', 'C1-Leme-Web.dc.html')
    web('telemetria-web.jpg', 'A1-Ponte-Web.dc.html')
    web('documentos-web.jpg', 'G1-Documentos-Web.dc.html')


def pdf(b, base):
    ctx = b.new_context()
    pg = ctx.new_page()
    pg.goto(base + 'guia-rapido/Guia-Rapido-Capitao-IA.html', wait_until='load')
    pg.wait_for_timeout(800)
    pg.emulate_media(media='print')
    pg.pdf(path=PDF, format='A4', print_background=True, margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'}, prefer_css_page_size=True)
    ctx.close()
    print('   PDF:', os.path.relpath(PDF, RAIZ), '%.0f KB' % (os.path.getsize(PDF) / 1024))


def main():
    s, base = servidor()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel=CANAL, headless=True)
            if '--so-pdf' not in sys.argv:
                print('capturas (tema claro):')
                capturas(b, base)
            pdf(b, base)
            b.close()
    finally:
        s.shutdown()


if __name__ == '__main__':
    main()
