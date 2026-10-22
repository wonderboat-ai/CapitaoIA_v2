# -*- coding: utf-8 -*-
"""Capitão IA — matriz de verificação das telas (critérios de aceite).

Cada tela × tema (escuro, claro) × tamanho (web 1440×900 · 1280×720 · 1920×1080 · 1024×768;
app 390×844 · 360×640 · 430×932 · 844×390). Confere: erro de script, rolagem lateral, imagem/ícone
deformado (proporção exibida × natural) e se a prancheta desenhou. Opcional: offline depois da 1ª visita.
React do próprio site (assets/vendor): com o unpkg.com fora do ar, o início (web e app) e o SOS montam, sem erro de script e
sem nenhum pedido ao unpkg; no teste offline, nenhum pedido ao unpkg (instalação do SW inclusive) e a instalação já
guarda os dois arquivos do React (CORE do sw.js, tudo ou nada). Reserva da troca de versão: com o assets/vendor fora, o SOS
monta com o React do endereço do unpkg e o mesmo SRI (o cache do SW da 1.0.x tem essa cópia; aqui o teste a serve).
Também o login e a lista (index.html?v=lista), fora das TELAS do sw.js, em todos os tamanhos: sem erro, sem rolagem
lateral, sem imagem deformada; no login, o ENTRAR na 1ª tela (altura ≥ 640) e o crédito inteiro (altura ≥ 844).
Vento e rajada do dia no cabeçalho (paridade Avanti 1.24.0), em Main, H2-Home-Mobile e S1-SOS-Web, com o Open-Meteo simulado
(JSON fixo no route; nenhum pedido sai para a internet): direção e "n/n KT", os três toques abrindo o windy.com na posição de
referência (nova aba, noopener), nada cortado nem sobreposto no cabeçalho (web 1440×900 e 1024×768, app 390×844 e 360×640, dois
temas); sem rede e sem leitura do dia, "—" (nunca o vento do snapshot); sem rede com a leitura salva de hoje, ela com a hora dela;
rajada que o ECMWF não trouxe vem do melhor modelo, dito no title. Na B3-Carta-Resposta (responde ali mesmo, sem o cabeçalho do
clima), a leitura de hoje salva entra no clima e no "seguro para sair?" como na home, com fonte, hora e o windy.com em nova aba;
sem ela, SEM DADOS e nenhum vento previsto.
Ícones dos atalhos do app instalado (paridade Avanti 1.24.0, desenho próprio), em toda rodada (é o manifest, não uma tela):
cada shortcut tem ícone any e maskable; cada src responde 200 e o PNG tem o tamanho declarado (cabeçalho lido com struct, sem
Pillow); desenho centrado e, no maskable, fundo inteiro e desenho dentro da zona segura de 80 %.

Uso (site servido em http://127.0.0.1:8765):
    python testes/verificar.py                     todas as telas, todos os tamanhos e temas
    python testes/verificar.py Main S2-SOS-Mobile  só essas telas (login e index: as páginas fora das TELAS)
    python testes/verificar.py --fotos             salva capturas em testes/saida/
    python testes/verificar.py --offline           testa a abertura offline depois da 1ª visita
    python testes/verificar.py --so-offline        só o teste offline (sem a matriz)
Navegador: Edge instalado (channel="msedge").
"""
import json
import os
import re
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8765/'
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SAIDA = os.path.join(os.path.dirname(__file__), 'saida')
WEB = [(1440, 900), (1280, 720), (1920, 1080), (1024, 768)]
APP = [(390, 844), (360, 640), (430, 932), (844, 390)]
MOBILE_UA = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Mobile Safari/537.36'
# React do próprio site (paridade Avanti 1.24.0): estas telas montam com o unpkg.com fora do ar.
SEM_UNPKG = ['Main', 'H2-Home-Mobile', 'S2-SOS-Mobile']
# Telas com o <capitao-hora-clima> no cabeçalho (o SOS também: só previsão real ou a última leitura salva).
CLIMA = ['Main', 'H2-Home-Mobile', 'S1-SOS-Web']
# Telas que respondem ali mesmo sem o <capitao-hora-clima>: a previsão salva pelo cabeçalho entra na resposta como na home.
RESPOSTA_CLIMA = ['B3-Carta-Resposta']
REACT_LOCAL = BASE + 'assets/vendor/react-18.3.1/'
REACT_ARQS = ['react.production.min.js', 'react-dom.production.min.js']
# reserva do support.js quando a cópia local falha (troca de versão com o SW da 1.0.x): endereço do unpkg → arquivo local (mesmos bytes)
REACT_RESERVA = {'https://unpkg.com/react@18.3.1/umd/react.production.min.js': 'react.production.min.js',
                 'https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js': 'react-dom.production.min.js'}


def telas():
    sw = open(os.path.join(RAIZ, 'sw.js'), encoding='utf-8').read()
    m = re.search(r'const TELAS = \[(.*?)\];', sw, re.S)
    return re.findall(r"'([^']+)'", m.group(1))


def eh_app(t):
    return not (t == 'Main' or t.endswith('-Web') or t.startswith('D-') or t.startswith('Manual-'))


def eh_unpkg(url):
    return bool(re.search(r'(^|\.)unpkg\.com$', urllib.parse.urlparse(url).hostname or ''))


def corta_unpkg(ctx):
    """unpkg.com fora do ar no contexto (o route mais novo ganha do que já houver); devolve a lista dos pedidos que tentaram ir para lá."""
    pedidos = []
    ctx.on('request', lambda r: pedidos.append(r.url) if eh_unpkg(r.url) else None)
    ctx.route('https://unpkg.com/**', lambda rt: rt.abort('connectionrefused'))
    return pedidos


SESSAO = "(() => { const n = Date.now(); localStorage.setItem('capitao.sessao.v1', JSON.stringify({ u: 'lucas', em: n, exp: n + 3600e3 })); })()"
# páginas fora das TELAS do sw.js: nome → (endereço, com sessão). O login com sessão redireciona; a lista precisa de ?v=lista.
PAGINAS = {'login': ('login.html', False), 'index': ('index.html?v=lista', True)}
MEDE_LOGIN = """() => { const q = (s) => { const e = document.querySelector(s); return e ? e.getBoundingClientRect().bottom : null; };
  return { go: q('#go'), credito: q('.credito') }; }"""
CHECA = """() => {
  const de = document.documentElement, root = document.getElementById('dc-root');
  const lateral = Math.max(de.scrollWidth, document.body ? document.body.scrollWidth : 0) - de.clientWidth;
  const deform = [];
  document.querySelectorAll('img').forEach((im) => {
    const r = im.getBoundingClientRect(); if (!im.naturalWidth || r.width < 2 || r.height < 2) return;
    const fit = getComputedStyle(im).objectFit;
    if (fit === 'contain' || fit === 'cover') return;
    const a = im.naturalWidth / im.naturalHeight, b = r.width / r.height;
    if (Math.abs(a - b) / a > 0.04) deform.push((im.getAttribute('src') || '') + ' ' + a.toFixed(2) + '→' + b.toFixed(2));
  });
  document.querySelectorAll('svg').forEach((s) => {
    const r = s.getBoundingClientRect(), vb = s.viewBox && s.viewBox.baseVal;
    if (!vb || !vb.width || r.width < 4 || r.height < 4) return;
    const par = s.getAttribute('preserveAspectRatio');
    if (par && par !== 'none') return;
    const a = vb.width / vb.height, b = r.width / r.height;
    if (par === 'none' && Math.abs(a - b) / a > 0.04) deform.push('svg ' + a.toFixed(2) + '→' + b.toFixed(2));
  });
  const prancheta = !!(root && root.querySelector('[style*="width: 1440px"],[style*="width: 390px"],[style*="width: 2380px"],deck-stage'));
  return { lateral: lateral, deform: deform, prancheta: prancheta, titulo: document.title };
}"""


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    fotos = '--fotos' in sys.argv
    offline = '--offline' in sys.argv or '--so-offline' in sys.argv
    so_offline = '--so-offline' in sys.argv  # pula a matriz, só o teste offline
    lista = [a for a in args if a not in PAGINAS] if args else telas()
    paginas = [a for a in args if a in PAGINAS] if args else list(PAGINAS)
    if fotos:
        os.makedirs(SAIDA, exist_ok=True)
    falhas, total = [], 0
    t0 = time.time()
    with sync_playwright() as p:
        b = p.chromium.launch(channel='msedge', headless=True)
        for tema in (() if so_offline else ('escuro', 'claro')):
            for tela in lista:
                tamanhos = APP if eh_app(tela) else WEB
                for (w, h) in tamanhos:
                    total += 1
                    movel = eh_app(tela)  # celular, inclusive deitado (844×390): toque + UA móvel
                    ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None,
                                        is_mobile=movel, has_touch=movel, service_workers='block')
                    ctx.add_init_script(SESSAO + ";localStorage.setItem('capitao.tema.v1', '" + tema + "');localStorage.setItem('capitao.plataforma.v1', '" + ('app' if eh_app(tela) else 'web') + "');")
                    pg = ctx.new_page()
                    erros = []
                    pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
                    pg.on('console', lambda m: erros.append('console: ' + m.text[:300]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
                    pg.goto(BASE + tela + '.dc.html', wait_until='load')
                    try:
                        pg.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
                    except Exception:
                        erros.append('prancheta não desenhou em 15 s')
                    pg.wait_for_timeout(900)
                    r = pg.evaluate(CHECA)
                    url = pg.url
                    prob = []
                    if erros: prob += erros
                    if r['lateral'] > 1: prob.append('rolagem lateral de %d px' % r['lateral'])
                    if r['deform']: prob.append('deformado: ' + '; '.join(r['deform'][:4]))
                    if not r['prancheta']: prob.append('prancheta ausente')
                    if not url.split('#')[0].endswith(tela + '.dc.html'): prob.append('redirecionou para ' + url)
                    if fotos:
                        pg.screenshot(path=os.path.join(SAIDA, '%s_%s_%dx%d.png' % (tela, tema, w, h)))
                    if prob:
                        falhas.append({'tela': tela, 'tema': tema, 'tam': '%dx%d' % (w, h), 'prob': prob})
                        print('FALHA', tela, tema, '%dx%d' % (w, h), ' | '.join(prob))
                    ctx.close()
            for nome in paginas:
                end, com_sessao = PAGINAS[nome]
                for (w, h) in WEB + APP:
                    total += 1
                    movel = (w, h) in APP
                    ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None,
                                        is_mobile=movel, has_touch=movel, service_workers='block')
                    ctx.add_init_script((SESSAO + ';' if com_sessao else '') + "localStorage.setItem('capitao.tema.v1', '" + tema + "');")
                    pg = ctx.new_page()
                    erros = []
                    pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
                    pg.on('console', lambda m: erros.append('console: ' + m.text[:300]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
                    pg.goto(BASE + end, wait_until='load')
                    pg.wait_for_timeout(500)
                    r = pg.evaluate(CHECA)
                    prob = list(erros)
                    if r['lateral'] > 1: prob.append('rolagem lateral de %d px' % r['lateral'])
                    if r['deform']: prob.append('deformado: ' + '; '.join(r['deform'][:4]))
                    if not pg.url.split('#')[0].endswith(end): prob.append('redirecionou para ' + pg.url)
                    if nome == 'login':
                        m = pg.evaluate(MEDE_LOGIN)
                        if h >= 640 and (m['go'] is None or m['go'] > h): prob.append('ENTRAR fora da 1ª tela (borda %s > %d)' % (m['go'], h))
                        if h >= 844 and (m['credito'] is None or m['credito'] > h): prob.append('crédito cortado (borda %s > %d)' % (m['credito'], h))
                    if fotos:
                        pg.screenshot(path=os.path.join(SAIDA, '%s_%s_%dx%d.png' % (nome, tema, w, h)))
                    if prob:
                        falhas.append({'tela': nome, 'tema': tema, 'tam': '%dx%d' % (w, h), 'prob': prob})
                        print('FALHA', nome, tema, '%dx%d' % (w, h), ' | '.join(prob))
                    ctx.close()
        if not so_offline:
            for tela in [t for t in SEM_UNPKG if t in lista]:
                total += 1
                prob = teste_sem_unpkg(b, tela)
                if prob:
                    falhas.append({'tela': tela, 'tema': 'sem unpkg', 'prob': prob})
                    print('FALHA sem unpkg', tela, ' | '.join(prob))
            for tela in [t for t in CLIMA if t in lista]:
                total += 1
                prob = teste_clima(b, tela)
                if prob:
                    falhas.append({'tela': tela, 'tema': 'vento no cabeçalho', 'prob': prob})
                    print('FALHA vento no cabeçalho', tela, ' | '.join(prob))
            for tela in [t for t in RESPOSTA_CLIMA if t in lista]:
                total += 1
                prob = teste_resposta_clima(b, tela)
                if prob:
                    falhas.append({'tela': tela, 'tema': 'previsão na resposta', 'prob': prob})
                    print('FALHA previsão na resposta', tela, ' | '.join(prob))
            if 'S2-SOS-Mobile' in lista:
                total += 1
                prob = teste_reserva(b, 'S2-SOS-Mobile')
                if prob:
                    falhas.append({'tela': 'S2-SOS-Mobile', 'tema': 'reserva do React', 'prob': prob})
                    print('FALHA reserva do React', ' | '.join(prob))
            for nome, prob in teste_atalhos(b).items():  # sempre: é o manifest, não uma tela
                total += 1
                if prob:
                    falhas.append({'tela': 'manifest', 'tema': 'atalho ' + nome, 'prob': prob})
                    print('FALHA atalho', nome, ' | '.join(prob))
        if offline:
            total += 1
            prob = teste_offline(b, lista)
            if prob:
                falhas.append({'tela': 'offline', 'prob': prob}); print('FALHA offline', ' | '.join(prob))
        b.close()
    print('%d verificações · %d falhas · %.0f s' % (total, len(falhas), time.time() - t0))
    with open(os.path.join(RAIZ, 'testes', 'saida-ultima.json'), 'w', encoding='utf-8') as f:
        json.dump({'total': total, 'falhas': falhas}, f, ensure_ascii=False, indent=1)
    sys.exit(1 if falhas else 0)


def teste_sem_unpkg(b, tela):
    """unpkg.com abortado: a tela monta (dc-root com filhos), sem erro de script, com o React de assets/vendor e sem pedido ao unpkg."""
    movel = eh_app(tela)
    w, h = (APP if movel else WEB)[0]
    ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None,
                        is_mobile=movel, has_touch=movel, service_workers='block')
    ctx.add_init_script(SESSAO)
    unpkg = corta_unpkg(ctx)
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
    pg.on('console', lambda m: erros.append('console: ' + m.text[:300]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    prob = []
    pg.goto(BASE + tela + '.dc.html', wait_until='load')
    try:
        pg.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
    except Exception:
        prob.append('não montou em 15 s')
    pg.wait_for_timeout(900)
    r = pg.evaluate("""() => ({ react: !!(window.React && window.ReactDOM),
  src: [...document.scripts].map((s) => s.src).filter((s) => /\\/react(-dom)?\\.production\\.min\\.js$/.test(s)) })""")
    if not r['react']: prob.append('sem React')
    if len(r['src']) != 2 or not all(s.startswith(REACT_LOCAL) for s in r['src']): prob.append('React fora de assets/vendor: %s' % r['src'])
    if erros: prob += erros
    if unpkg: prob.append('%d pedido(s) ao unpkg: %s' % (len(unpkg), unpkg[0]))
    ctx.close()
    return prob


# Previsão de hoje como o Open-Meteo devolve (daily, nós). A data entra no teste (hoje no fuso do barco); 48° = NE.
PREVISAO = {'temperature_2m_max': [27.4], 'temperature_2m_min': [18.2], 'wind_speed_10m_max': [12.3], 'wind_gusts_10m_max': [19.4],
            'wind_direction_10m_dominant': [48]}
WINDY_REF = 'https://www.windy.com/-26.991/-48.635?-26.991,-48.635,11'  # posição de referência (GeoNames 3471039), 3 casas
DIA_BARCO = """(ms) => new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(Date.now() + ms))"""
LE_CLIMA = """() => {
  const el = document.querySelector('capitao-hora-clima'); if (!el || el.children.length < 4) return null;
  const hd = el.closest('header'), H = hd.getBoundingClientRect(), prob = [];
  const plano = (p) => [...p.children].flatMap((k) => getComputedStyle(k).display === 'contents' ? plano(k) : [k]);
  const itens = plano(hd).map((k) => ({ k, r: k.getBoundingClientRect() })).filter((x) => x.r.width > 0 && x.r.height > 0).sort((a, b) => a.r.left - b.r.left);
  const nome = (k) => (k.tagName.toLowerCase() + ' ' + (k.textContent || '').trim()).slice(0, 40);
  itens.forEach((x, i) => {
    if (x.r.left < H.left - 0.5 || x.r.right > H.right + 0.5 || x.r.top < H.top - 0.5 || x.r.bottom > H.bottom + 0.5) prob.push('fora do cabeçalho: ' + nome(x.k));
    // só onde há texto: o botão do tema tem alvo de 44 px com margem negativa (de propósito) e passa da caixa de 34
    if ((x.k.textContent || '').trim() && x.k.scrollWidth > x.k.clientWidth + 1) prob.push('texto cortado: ' + nome(x.k));
    const y = itens[i + 1]; if (y && x.r.right > y.r.left + 0.5) prob.push('sobreposto: ' + nome(x.k) + ' × ' + nome(y.k));
  });
  [...el.querySelectorAll('a')].forEach((a) => { if (a.scrollWidth > a.clientWidth + 1) prob.push('texto cortado: ' + nome(a)); });
  const de = document.documentElement, links = [...el.querySelectorAll('a')], vento = links.find((a) => /KT/.test(a.textContent));
  const r = el.getBoundingClientRect(), hora = el.querySelector('b').getBoundingClientRect(), vr = vento ? vento.getBoundingClientRect() : null;
  return { prob, lateral: de.scrollWidth - de.clientWidth, vento: vento ? vento.textContent : null, titulo: vento ? vento.title : '',
           titulos: links.map((a) => a.title), links: links.map((a) => [a.href, a.target, a.rel]), texto: el.textContent,
           duasLinhas: !!vr && vr.top > hora.bottom - 1, altura: r.height / (H.height || 1) };
}"""


def teste_clima(b, tela):
    """Vento e rajada do dia no cabeçalho, com o Open-Meteo simulado (JSON fixo; marine com a maré). Ver o cabeçalho do arquivo."""
    movel = eh_app(tela)
    prob = []
    pg0 = b.new_page()
    hoje, ontem = pg0.evaluate(DIA_BARCO, 0), pg0.evaluate(DIA_BARCO, -86400e3)
    pg0.close()
    t0 = int(time.time()) // 3600 * 3600
    mare = {'hourly': {'time': [t0 + 3600 * i for i in range(-24, 48)], 'sea_level_height_msl': [0.42] * 72}}

    def abre(w, h, tema, modo, salva=None):
        ctx = b.new_context(viewport={'width': w, 'height': h}, user_agent=MOBILE_UA if movel else None,
                            is_mobile=movel, has_touch=movel, service_workers='block')
        ctx.add_init_script(SESSAO + ";localStorage.setItem('capitao.tema.v1', '" + tema + "');")
        if salva:  # leitura salva (sem a data e a hora, que o próprio navegador põe: dia no fuso do barco, em = 3 h atrás)
            ctx.add_init_script("(() => { const c = %s; c.em = Date.now() - 3 * 3600e3; localStorage.setItem('capitao.clima.v1', JSON.stringify(c)); })()" % json.dumps(salva))
        pedidos = []

        def rota(rt):
            url = rt.request.url
            pedidos.append(url)
            if modo == 'sem rede':
                return rt.abort('internetdisconnected')
            if 'marine-api.' in url:
                corpo = mare
            else:
                d = dict(PREVISAO, time=[hoje])
                if modo == 'sem rajada no ECMWF' and 'models=ecmwf' in url:
                    d['wind_gusts_10m_max'] = [None]
                elif modo == 'sem rajada no ECMWF':
                    d['wind_gusts_10m_max'] = [21.2]  # melhor modelo do Open-Meteo
                corpo = {'daily': d}
            rt.fulfill(status=200, content_type='application/json', body=json.dumps(corpo), headers={'access-control-allow-origin': '*'})
        ctx.route('https://*.open-meteo.com/**', rota)
        pg = ctx.new_page()
        pg.goto(BASE + tela + '.dc.html', wait_until='load')
        try:
            pg.wait_for_function("() => { const e = document.querySelector('capitao-hora-clima'); return e && e.children.length >= 4; }", timeout=15000)
        except Exception:
            ctx.close()
            return None, pedidos
        pg.wait_for_timeout(1200)
        r = pg.evaluate(LE_CLIMA)
        if r is not None and salva:
            r['hora_salva'] = pg.evaluate("() => new Intl.DateTimeFormat('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(JSON.parse(localStorage.getItem('capitao.clima.v1')).em))")
        ctx.close()
        return r, pedidos

    tams = [(390, 844), (360, 640)] if movel else [(1440, 900), (1024, 768)]
    for tema in ('escuro', 'claro'):
        for (w, h) in tams:
            tag = '%s %dx%d' % (tema, w, h)
            r, pedidos = abre(w, h, tema, 'json fixo')
            if r is None:
                prob.append(tag + ': o cabeçalho não montou'); continue
            if r['vento'] != 'NE12/19KT': prob.append(tag + ': vento no cabeçalho %r (esperado NE 12/19 KT)' % r['vento'])
            if any(x != [WINDY_REF, '_blank', 'noopener'] for x in r['links']) or len(r['links']) != 3:
                prob.append(tag + ': toques do clima, vento e maré não abrem o windy.com na referência em nova aba: %s' % r['links'])
            if 'ECMWF via Open-Meteo, lida às' not in r['titulo'] or 'até 12 nós de NE, rajadas até 19 nós' not in r['titulo']:
                prob.append(tag + ': title do vento sem fonte e hora: ' + r['titulo'])
            if r['prob']: prob.append(tag + ': ' + '; '.join(r['prob'][:4]))
            if r['lateral'] > 1: prob.append(tag + ': rolagem lateral de %d px' % r['lateral'])
            if movel and not r['duasLinhas']: prob.append(tag + ': no celular o vento vai na 2ª linha')
            if movel and r['altura'] > 1: prob.append(tag + ': clima mais alto que o cabeçalho (%.2f)' % r['altura'])
            if any('open-meteo.com' not in u for u in pedidos) or not any('models=ecmwf_ifs025' in u and 'wind_gusts_10m_max' in u and 'wind_speed_unit=kn' in u for u in pedidos):
                prob.append(tag + ': pedido fora do esperado (ECMWF com vento e rajada em nós): %s' % pedidos[:3])
    w, h = tams[0]
    # sem rede e só a leitura de ontem: "—" em tudo (nem a leitura velha nem o vento do snapshot)
    r, _ = abre(w, h, 'escuro', 'sem rede', {'dia': ontem, 'max': 30, 'min': 20, 'vento': 25, 'raj': 33, 'dir': 180, 'modelo': 'ECMWF'})
    if r is None:
        prob.append('sem rede: o cabeçalho não montou')
    else:
        if r['vento'] != '—/—KT': prob.append('sem rede, sem leitura de hoje: vento %r (esperado —/— KT)' % r['vento'])
        if any(ch.isdigit() for ch in r['texto'][5:]): prob.append('sem rede, sem leitura de hoje: número fora da hora (HH:MM): %r' % r['texto'])
        if 'SEM DADOS' not in r['titulo']: prob.append('sem rede: title do vento sem SEM DADOS: ' + r['titulo'])
    # sem rede com a leitura salva de hoje: ela, com a hora dela
    r, _ = abre(w, h, 'claro', 'sem rede', {'dia': hoje, 'max': 26, 'min': 17, 'vento': 8.4, 'raj': 14.6, 'dir': 200, 'modelo': 'ECMWF'})
    if r is None:
        prob.append('sem rede com leitura salva: o cabeçalho não montou')
    elif r['vento'] != 'S8/15KT' or ('lida às ' + r['hora_salva']) not in r['titulo']:
        prob.append('sem rede com a leitura salva de hoje: %r · %s (esperado S 8/15 KT, lida às %s)' % (r['vento'], r['titulo'], r['hora_salva']))
    # ECMWF sem rajada: a rajada vem do melhor modelo do Open-Meteo, dito no title
    r, pedidos = abre(w, h, 'escuro', 'sem rajada no ECMWF')
    if r is None:
        prob.append('ECMWF sem rajada: o cabeçalho não montou')
    elif r['vento'] != 'NE12/21KT' or 'rajada: melhor modelo do Open-Meteo' not in r['titulo']:
        prob.append('ECMWF sem rajada: %r · %s' % (r['vento'], r['titulo']))
    return prob


def teste_resposta_clima(b, tela):
    """Previsão do dia na resposta de uma tela sem o cabeçalho do clima (B3): a leitura salva de hoje (capitao.clima.v1, como o
    capitao-clima.js grava) entra no clima e no "seguro para sair?", com fonte e hora; sem ela, SEM DADOS. Open-Meteo fora (abort)."""
    movel = eh_app(tela)
    prob = []
    pg0 = b.new_page()
    hoje = pg0.evaluate(DIA_BARCO, 0)
    pg0.close()
    salva = {'dia': hoje, 'max': 27.4, 'min': 18.2, 'vento': 12.3, 'raj': 19.4, 'dir': 48, 'modelo': 'ECMWF'}
    vento = 'vento até 12 nós de nordeste, rajadas até 19 nós'
    for semeada in (True, False):
        for q in ('é seguro sair hoje?', 'como está o vento hoje?'):
            tag = '%s (%s)' % (q, 'leitura de hoje salva' if semeada else 'sem leitura')
            ctx = b.new_context(viewport={'width': 390, 'height': 844}, user_agent=MOBILE_UA if movel else None,
                                is_mobile=movel, has_touch=movel, service_workers='block')
            ctx.add_init_script(SESSAO)
            if semeada:
                ctx.add_init_script("(() => { const c = %s; c.em = Date.now() - 3 * 3600e3; localStorage.setItem('capitao.clima.v1', JSON.stringify(c)); })()" % json.dumps(salva))
            ctx.route('https://*.open-meteo.com/**', lambda rt: rt.abort('internetdisconnected'))
            pg = ctx.new_page()
            erros = []
            pg.on('pageerror', lambda e: erros.append(str(e)[:200]))
            pg.goto(BASE + tela + '.dc.html#q=' + urllib.parse.quote(q), wait_until='load')
            try:
                pg.wait_for_function("() => /Fonte:/.test(document.body.innerText)", timeout=15000)
            except Exception:
                prob.append(tag + ': a resposta não apareceu'); ctx.close(); continue
            r = pg.evaluate("""() => ({ texto: document.body.innerText, hora: (() => { const c = JSON.parse(localStorage.getItem('capitao.clima.v1') || 'null');
              return c ? new Intl.DateTimeFormat('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(c.em)) : ''; })(),
              windy: [...document.querySelectorAll('a')].filter((a) => a.href.startsWith('https://www.windy.com/')).map((a) => [a.href, a.target, a.rel]) })""")
            ctx.close()
            t = r['texto']
            if erros: prob.append(tag + ': erro de script ' + '; '.join(erros[:2]))
            if semeada:
                if vento not in t or ('ECMWF via Open-Meteo, lida às ' + r['hora']) not in t:
                    prob.append(tag + ': sem o vento previsto com fonte e hora: ' + t[:300].replace('\n', ' / '))
                if r['windy'] != [[WINDY_REF, '_blank', 'noopener']]:
                    prob.append(tag + ': atalho do windy.com fora do esperado: %s' % r['windy'])
            else:
                if 'SEM DADOS' not in t or 'vento até' in t or 'rajadas até' in t or r['windy']:
                    prob.append(tag + ': inventou vento ou perdeu o SEM DADOS: ' + t[:300].replace('\n', ' / '))
            if 'sem internet e sem leitura salva' in t:
                prob.append(tag + ': diz "sem internet" sem saber (o Open-Meteo nem foi consultado)')
    return prob


def teste_reserva(b, tela):
    """Troca de versão com o SW da 1.0.x: o cache dele pode ficar com o support.js novo sem o assets/vendor. Com a cópia local
    fora, a tela (o SOS) monta com o React da reserva — o endereço do unpkg, com o mesmo SRI —, sem erro de script. O teste
    serve a reserva com os bytes de assets/vendor (os do pacote npm): não depende da internet."""
    ctx = b.new_context(viewport={'width': APP[0][0], 'height': APP[0][1]}, user_agent=MOBILE_UA, is_mobile=True, has_touch=True,
                        service_workers='block')
    ctx.add_init_script(SESSAO)
    pedidos = []

    def unpkg(rt):
        pedidos.append(rt.request.url)
        arq = REACT_RESERVA.get(rt.request.url)
        if not arq:
            return rt.abort('connectionrefused')
        rt.fulfill(path=os.path.join(RAIZ, 'assets', 'vendor', 'react-18.3.1', arq), status=200,
                   headers={'content-type': 'text/javascript; charset=utf-8', 'access-control-allow-origin': '*'})
    ctx.route('https://unpkg.com/**', unpkg)
    ctx.route(REACT_LOCAL + '**', lambda rt: rt.abort('connectionrefused'))
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append('pageerror: ' + str(e)[:300]))
    pg.on('console', lambda m: erros.append('console: ' + m.text[:300]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    prob = []
    pg.goto(BASE + tela + '.dc.html', wait_until='load')
    try:
        pg.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
    except Exception:
        prob.append('não montou em 15 s com a cópia local fora')
    pg.wait_for_timeout(900)
    r = pg.evaluate("() => ({ react: !!(window.React && window.ReactDOM && window.ReactDOM.createRoot), texto: document.body.innerText.toUpperCase() })")
    if not r['react']: prob.append('sem React')
    if 'CANAL 16' not in r['texto'] and 'MAYDAY' not in r['texto']: prob.append('SOS sem CANAL 16 / MAYDAY: ' + r['texto'][:120])
    if sorted(pedidos) != sorted(REACT_RESERVA): prob.append('reserva fora do esperado: %s' % pedidos)
    if erros: prob += erros
    ctx.close()
    return prob


def tamanho_png(dados):
    """(largura, altura) do cabeçalho IHDR do PNG, lido com struct (sem Pillow); None se não for PNG."""
    if len(dados) < 24 or dados[:8] != b'\x89PNG\r\n\x1a\n' or dados[12:16] != b'IHDR':
        return None
    return struct.unpack('>II', dados[16:24])


# Desenho de um ícone de atalho, no navegador (o PNG do mesmo site não "suja" o canvas): pixels do desenho (opacos e longe do
# fundo #050816; a borda suavizada do disco do any fica de fora), retângulo que os contém, quantos saem da zona segura do
# maskable (círculo de raio 0,4 × lado) e quantos pixels são opacos.
DESENHO_ATALHO = """async ([src, lado]) => {
  const im = new Image(); im.src = src; await im.decode();
  const c = document.createElement('canvas'); c.width = c.height = lado;
  const g = c.getContext('2d'); g.drawImage(im, 0, 0);
  const d = g.getImageData(0, 0, lado, lado).data, m = lado / 2, zona = 0.4 * lado;
  let n = 0, fora = 0, opacos = 0, x0 = lado, y0 = lado, x1 = -1, y1 = -1;
  for (let y = 0; y < lado; y++) for (let x = 0; x < lado; x++) {
    const i = (y * lado + x) * 4;
    if (d[i + 3] === 255) opacos++;
    if (d[i + 3] < 128 || Math.abs(d[i] - 5) + Math.abs(d[i + 1] - 8) + Math.abs(d[i + 2] - 22) < 60) continue;
    n++; x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y);
    if (Math.hypot(x + 0.5 - m, y + 0.5 - m) > zona) fora++;
  }
  return { n, fora, opacos, caixa: [x0, y0, x1 + 1, y1 + 1] };
}"""


def teste_atalhos(b):
    """Ícones dos atalhos do app instalado (paridade Avanti 1.24.0, desenho próprio: ferramentas/icones/gerar_atalhos.py).
    Cada shortcut do manifest.webmanifest tem ícone any e maskable (image/png); cada src responde 200 no servidor local e o PNG
    tem exatamente o tamanho declarado em sizes (cabeçalho lido com struct). No navegador: há desenho, centrado (a caixa dele a
    no máximo 4 % do centro); no any ele não encosta na borda; no maskable o fundo é inteiro (todo pixel opaco) e o desenho fica
    dentro da zona segura. Devolve {nome do atalho: [problemas]}."""
    man = json.load(open(os.path.join(RAIZ, 'manifest.webmanifest'), encoding='utf-8'))
    sem_proxy = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    ctx = b.new_context(viewport={'width': 400, 'height': 300}, device_scale_factor=1, service_workers='block')
    ctx.route(BASE + '__atalhos__', lambda rt: rt.fulfill(status=200, content_type='text/html; charset=utf-8', body='<!doctype html><title>atalhos</title>'))
    pg = ctx.new_page()
    pg.goto(BASE + '__atalhos__')
    res = {}
    for sc in man.get('shortcuts') or [{'short_name': '(nenhum shortcut no manifest)'}]:
        nome = sc.get('short_name') or sc.get('name')
        prob = res[nome] = []
        icones = sc.get('icons') or []
        for pp in ('any', 'maskable'):
            if not any(pp in (i.get('purpose') or 'any').split() for i in icones):
                prob.append('sem ícone %s' % pp)
        for i in icones:
            src, sizes = i.get('src') or '', i.get('sizes') or ''
            tag = src or '(sem src)'
            if i.get('type') != 'image/png':
                prob.append('%s: type %r (esperado image/png)' % (tag, i.get('type')))
            m = re.fullmatch(r'(\d+)x(\d+)', sizes)
            if not m:
                prob.append('%s: sizes %r fora do formato LxA' % (tag, sizes)); continue
            decl = (int(m.group(1)), int(m.group(2)))
            try:
                with sem_proxy.open(BASE + src, timeout=10) as r:
                    st, dados = r.status, r.read()
            except urllib.error.HTTPError as e:
                st, dados = e.code, b''
            except Exception as e:
                prob.append('%s: %s' % (tag, str(e)[:120])); continue
            if st != 200:
                prob.append('%s: HTTP %s' % (tag, st)); continue
            real = tamanho_png(dados)
            if real != decl:
                prob.append('%s: PNG %s, declarado %s' % (tag, 'x'.join(map(str, real)) if real else 'inválido', sizes)); continue
            lado = decl[0]
            mask = 'maskable' in (i.get('purpose') or '').split()
            d = pg.evaluate(DESENHO_ATALHO, [BASE + src, lado])
            if d['n'] < 0.03 * lado * lado:
                prob.append('%s: quase sem desenho (%d pixels)' % (tag, d['n'])); continue
            x0, y0, x1, y1 = d['caixa']
            desvio = max(abs((x0 + x1) / 2 - lado / 2), abs((y0 + y1) / 2 - lado / 2))
            if desvio > 0.04 * lado:
                prob.append('%s: desenho fora do centro (caixa %s, desvio %.1f px)' % (tag, d['caixa'], desvio))
            if mask and d['opacos'] != lado * lado:
                prob.append('%s: maskable com fundo transparente (%d de %d pixels opacos)' % (tag, d['opacos'], lado * lado))
            if mask and d['fora']:
                prob.append('%s: %d pixel(s) do desenho fora da zona segura de 80 %%' % (tag, d['fora']))
            if not mask and min(x0, y0, lado - x1, lado - y1) < 0.1 * lado:
                prob.append('%s: desenho encostando na borda (caixa %s)' % (tag, d['caixa']))
    ctx.close()
    return res


def teste_offline(b, lista):
    """1ª visita com internet (SW instala), depois abre cada tela sem rede. unpkg.com fora do ar o tempo todo: nenhum pedido a ele."""
    prob = []
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script(SESSAO)
    unpkg = corta_unpkg(ctx)
    pg = ctx.new_page()
    pg.goto(BASE + 'Main.dc.html', wait_until='load')
    try:
        pg.wait_for_function("() => navigator.serviceWorker && navigator.serviceWorker.controller", timeout=30000)
    except Exception:
        ctx.close()
        return ['service worker não instalou em 30 s (arquivo do CORE faltando? ex.: Guia-Rapido-Capitao-IA.pdf)']
    pg.wait_for_timeout(1500)
    # React no CORE do sw.js: a 1ª visita carregou o React antes de o SW controlar a tela, então só a instalação o põe no
    # cache. Sem esta conferência a falta passaria: offline, o cache HTTP do navegador ainda serve o React ao SW.
    guardou = pg.evaluate('(us) => Promise.all(us.map((u) => caches.match(u).then(Boolean)))', [REACT_LOCAL + arq for arq in REACT_ARQS])
    if guardou != [True, True]:
        prob.append('React fora do CORE do sw.js: a instalação não guardou %s' % ', '.join(arq for arq, g in zip(REACT_ARQS, guardou) if not g))
    ctx.set_offline(True)
    for tela in lista:
        erros = []
        pg2 = ctx.new_page()
        pg2.on('pageerror', lambda e: erros.append(str(e)[:200]))
        try:
            pg2.goto(BASE + tela + '.dc.html', wait_until='load', timeout=20000)
            pg2.wait_for_function("() => document.getElementById('dc-root') && document.getElementById('dc-root').children.length > 0", timeout=15000)
        except Exception as e:
            prob.append(tela + ' não abriu offline: ' + str(e)[:120])
        # marca (assets/) e o ∞ do botão CONVERSA também saem da cópia guardada (CORE do sw.js)
        try:
            pg2.wait_for_timeout(600)
            falta = pg2.evaluate("""async () => {
  const f = [...document.images].filter((i) => /\\/assets\\//.test(i.src) && i.complete && !i.naturalWidth).map((i) => i.src.split('/').pop());
  if (document.querySelector('capitao-simbolo')) {
    for (let n = 0; n < 50 && !customElements.get('capitao-simbolo'); n++) await new Promise((ok) => setTimeout(ok, 100));
    if (!customElements.get('capitao-simbolo')) f.push('capitao-simbolo.js');
  }
  return f;
}""")
            if falta:
                prob.append(tela + ' offline sem: ' + ', '.join(falta))
        except Exception as e:
            prob.append(tela + ' offline: ' + str(e)[:120])
        if erros:
            prob.append(tela + ' offline com erro: ' + erros[0])
        pg2.close()
    # lista (index.html): a assinatura sai da cópia guardada (CORE)
    pg4 = ctx.new_page()
    try:
        pg4.goto(BASE + 'index.html?v=lista', wait_until='load', timeout=20000)
        falta = pg4.evaluate("() => [...document.images].filter((i) => i.src.indexOf('/assets/') >= 0 && (!i.complete || !i.naturalWidth)).map((i) => i.src.split('/').pop())")
        if falta:
            prob.append('lista offline sem: ' + ', '.join(falta))
    except Exception as e:
        prob.append('lista offline: ' + str(e)[:120])
    pg4.close()
    # rosto da conversa por voz: entra à parte (capitao-voz.js), tem de vir da cópia guardada
    pg3 = ctx.new_page()
    try:
        pg3.goto(BASE + 'S2-SOS-Mobile.dc.html', wait_until='load', timeout=20000)
        st = pg3.evaluate("() => fetch('./capitao-rosto.js').then((r) => r.status, () => 'falhou')")
        if st != 200:
            prob.append('capitao-rosto.js offline: ' + str(st))
    except Exception as e:
        prob.append('capitao-rosto.js offline: ' + str(e)[:120])
    pg3.close()
    ctx.close()
    if unpkg:
        prob.append('%d pedido(s) ao unpkg no teste offline (o React sai da cópia guardada de assets/vendor): %s' % (len(unpkg), unpkg[0]))
    return prob


if __name__ == '__main__':
    main()
