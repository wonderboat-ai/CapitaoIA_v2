# -*- coding: utf-8 -*-
"""Capitão IA — gera os ícones dos atalhos do app instalado (manifest.webmanifest → shortcuts: SOS, Console, Diário).

Sem ícone, o Android mostrava os atalhos como quadrado cinza ao segurar o ícone do app (paridade Avanti 1.24.0; o desenho e as
cores são nossos). Desenho em SVG (192 × 192, centro em 96, 96): traço branco sobre o fundo #050816 da marca WonderHUB.AI; o SOS
leva o vermelho do SOS do app (#d32f27, o --cap-crit-fill). Boia salva-vidas (SOS), timão (Console) e livro aberto com marcador
(Diário de bordo). Rasteriza no navegador (Playwright), sem Pillow:
    assets/atalho-<nome>-<96|192>.png        purpose any: disco #050816, cantos transparentes (no Android o atalho é redondo)
    assets/atalho-<nome>-mask-<96|192>.png   purpose maskable: fundo inteiro, desenho dentro da zona segura (círculo de 80 %)
Determinístico: sem sorteio nem data; o mesmo navegador dá os mesmos bytes.

Uso, na raiz do repositório:
    python ferramentas/icones/gerar_atalhos.py
Navegador: Edge instalado (channel="msedge"); troque CANAL para "chrome" se preferir.
Não mexe no manifest.webmanifest (os 12 arquivos já estão em shortcuts[].icons); o testes/verificar.py confere caminho, tamanho,
zona segura e centro.
"""
import math
import os
from playwright.sync_api import sync_playwright

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SAIDA = os.path.join(RAIZ, 'assets')
CANAL = 'msedge'
LADOS = (96, 192)
FUNDO, BRANCO, VERMELHO = '#050816', '#ffffff', '#d32f27'
T = 'fill="none" stroke="%s" stroke-linecap="round" stroke-linejoin="round"' % BRANCO
# O desenho cabe num círculo de raio ≈ 66 em volta do centro. No any ele vai inteiro (disco de raio 96); no maskable, a 84 %
# (raio ≈ 56, folgado dentro da zona segura de 0,4 × 192 = 76,8: a máscara do aparelho pode cortar tudo o que passa dela).
ESCALA_MASK = 0.84


def n(v):
    """Número curto e estável no SVG (2 casas, sem zero à direita)."""
    s = ('%.2f' % v).rstrip('0').rstrip('.')
    return '0' if s == '-0' else s


def ponto(r, graus):
    a = math.radians(graus)
    return n(96 + r * math.cos(a)) + ' ' + n(96 + r * math.sin(a))


def boia():
    """Boia salva-vidas: anel de contorno branco com 4 faixas vermelhas nas diagonais e o cabo em 4 laços por fora."""
    fora, dentro, meia = 46, 24, 22  # raios do anel e meia largura (em graus) de cada faixa vermelha
    s = ''
    for c in (45, 135, 225, 315):
        a0, a1 = c - meia, c + meia
        s += ('<path d="M%s A%d %d 0 0 1 %s L%s A%d %d 0 0 0 %s Z" fill="%s"/>'
              % (ponto(fora, a0), fora, fora, ponto(fora, a1), ponto(dentro, a1), dentro, dentro, ponto(dentro, a0), VERMELHO))
    s += '<circle cx="96" cy="96" r="%d" %s stroke-width="5"/><circle cx="96" cy="96" r="%d" %s stroke-width="5"/>' % (fora, T, dentro, T)
    # cabo: preso no meio de cada faixa vermelha, cai num laço entre duas faixas (pontos de controle bem por fora do anel)
    for c in (45, 135, 225, 315):
        s += '<path d="M%s C%s %s %s" %s stroke-width="3.5"/>' % (ponto(fora + 2, c), ponto(72, c + 30), ponto(72, c + 60), ponto(fora + 2, c + 90), T)
        s += '<circle cx="%s" cy="%s" r="3.5" fill="%s"/>' % (tuple(ponto(fora + 2, c).split()) + (BRANCO,))
    return s


def timao():
    """Timão: aro duplo, cubo com eixo, 6 raios (um na vertical) e as manetes por fora do aro."""
    s = '<circle cx="96" cy="96" r="44" %s stroke-width="5"/><circle cx="96" cy="96" r="33" %s stroke-width="5"/>' % (T, T)
    for i in range(6):
        g = -90 + 60 * i
        s += '<line x1="%s" y1="%s" x2="%s" y2="%s" %s stroke-width="5"/>' % (tuple(ponto(13, g).split()) + tuple(ponto(50, g).split()) + (T,))
        s += '<line x1="%s" y1="%s" x2="%s" y2="%s" %s stroke-width="9"/>' % (tuple(ponto(53, g).split()) + tuple(ponto(61, g).split()) + (T,))
    s += '<circle cx="96" cy="96" r="13" %s stroke-width="5"/><circle cx="96" cy="96" r="4.5" fill="%s"/>' % (T, BRANCO)
    return s


def diario():
    """Diário de bordo: livro aberto (capa por baixo, duas páginas curvas), linhas escritas e o marcador pendurado na lombada.
    Sobe 5 para o conjunto (com o marcador) ficar no centro."""
    return '<g transform="translate(0 -5)">' + (
        # capa: aparece por baixo das páginas, dos lados e embaixo
        '<path d="M44 66 L44 134 C64 130 84 132 96 140 C108 132 128 130 148 134 L148 66" %s stroke-width="5"/>' % T
        # páginas
        + '<path d="M96 60 C84 52 66 50 52 54 L52 126 C66 122 84 124 96 132 Z" %s stroke-width="5"/>' % T
        + '<path d="M96 60 C108 52 126 50 140 54 L140 126 C126 122 108 124 96 132 Z" %s stroke-width="5"/>' % T
        # linhas: 3 na esquerda, 3 na direita (a última mais curta: o registro do dia)
        + ''.join('<path d="M61 %d C69 %d 79 %d 87 %d" %s stroke-width="4"/>' % (y, y - 3, y - 2, y + 2, T) for y in (74, 88, 102))
        + ''.join('<path d="M105 %d C113 %d 123 %d 131 %d" %s stroke-width="4"/>' % (y + 2, y - 2, y - 3, y, T) for y in (74, 88))
        + '<path d="M105 104 C110 101 114 100 118 100" %s stroke-width="4"/>' % T
        # marcador (fita) saindo da lombada por baixo
        + '<path d="M91 136 L91 152 L96 147 L101 152 L101 136" %s stroke-width="3.5"/>' % T
    ) + '</g>'


DESENHO = {'sos': boia, 'console': timao, 'diario': diario}


def svg(nome, mask, lado):
    if mask:
        fundo = '<rect width="192" height="192" fill="%s"/>' % FUNDO
        grupo = '<g transform="translate(96 96) scale(%s) translate(-96 -96)">%s</g>' % (n(ESCALA_MASK), DESENHO[nome]())
    else:
        fundo = '<circle cx="96" cy="96" r="96" fill="%s"/>' % FUNDO
        grupo = DESENHO[nome]()
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 192 192" style="display:block">%s%s</svg>'
            % (lado, lado, fundo, grupo))


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel=CANAL, headless=True)
        for lado in LADOS:
            pg = b.new_page(viewport={'width': lado, 'height': lado}, device_scale_factor=1)
            for nome in DESENHO:
                for mask in (False, True):
                    pg.set_content('<!doctype html><html><body style="margin:0;background:transparent">%s</body></html>' % svg(nome, mask, lado))
                    arq = os.path.join(SAIDA, 'atalho-%s%s-%d.png' % (nome, '-mask' if mask else '', lado))
                    pg.locator('svg').screenshot(path=arq, omit_background=True, animations='disabled')
                    print('  ', os.path.relpath(arq, RAIZ).replace(os.sep, '/'))
            pg.close()
        b.close()


if __name__ == '__main__':
    main()
