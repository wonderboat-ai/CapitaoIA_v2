# -*- coding: utf-8 -*-
"""Capitão IA — teste do cérebro (roteamento, fonte em toda resposta, SEM DADOS sem fonte, registro só com comando).

Uso (com o site servido em http://127.0.0.1:8765):
    python -m http.server 8765 --bind 127.0.0.1      (na raiz do repositório, em outro terminal)
    python testes/cerebro.py
Navegador: Edge instalado (Playwright com channel="msedge"); troque CANAL para "chrome" se preferir.
"""
import json
import sys
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8765/'
CANAL = 'msedge'

# (pergunta, chave esperada)
CASOS = [
    ('', 'saudacao'), ('oi, bom dia', 'saudacao'),
    ('MAYDAY, homem ao mar!', 'sos'), ('tem fogo na praça de máquinas', 'sos'), ('está entrando água no casco', 'sos'),
    ('fumaça no escapamento do motor', 'motores'),
    ('pressão de óleo baixa no motor BB', 'oleo'), ('qual a pressão do óleo?', 'oleoLeitura'), ('alarme de óleo acendeu', 'oleo'),
    ('Registre no diário: saída com 4 pessoas', 'diario'), ('vou registrar no diário depois', 'diarioLer'),
    ('não registre isso', 'fallback'), ('é seguro sair hoje?', 'seguro'), ('para onde vamos hoje?', 'destinos'),
    ('próximas manutenções', 'manutencao'), ('autonomia', 'autonomia'), ('maré agora', 'mare'), ('clima e vento', 'clima'),
    ('roteiro do canal 16', 'canal16'), ('checklist de saída', 'checklist'), ('checklist de chegada', 'checklistChegada'),
    ('consumo de diesel', 'consumo'), ('nível dos tanques', 'tanques'), ('quem chamar da equipe?', 'contatos'),
    ('pendências abertas', 'anomalias'), ('bombas de porão', 'porao'), ('como ligar o gerador?', 'base'),
    ('quantas horas tem o gerador', 'gerador'), ('posição agora', 'posicao'), ('documentos vencendo', 'docsvenc'),
    ('horímetros', 'horimetros'), ('estabilizador Seakeeper', 'estabilizador'), ('climatização', 'climatizacao'),
    ('alarme de fluxo da climatização', 'base'), ('plotter garmin', 'eletronicos'), ('parear bluetooth no fusion', 'base'),
    ('dessalinizador', 'dessalinizador'), ('bateria 24 v', 'eletrico'), ('onde fica o EPIRB?', 'epirb'), ('onde fica o seafire', 'seafire'),
    ('âncora garrando?', 'ancora'), ('manual do gerador', 'gerador'), ('guias de bordo', 'manual'), ('diário de bordo', 'diarioLer'),
    ('qual o preço do dólar?', 'fallback'), ('quem ganhou o jogo ontem', 'fallback'),
    ('motores volvo penta', 'motores'), ('Telemetria agora', 'telemetria'), ('como está o barco?', 'telemetria'), ('troca do rotor do gerador', 'base'),
    ('Oque você faz?', 'saudacao'), ('o que vc sabe fazer?', 'saudacao'), ('quem é vc?', 'saudacao'), ('como você funciona?', 'saudacao'),
    ('pra que serve esse app?', 'saudacao'),
    ('diagnóstico', 'diagnostico'), ('status da IA', 'diagnostico'), ('a IA está ligada?', 'diagnostico'), ('teste da IA', 'diagnostico'),
    ('qual o diagnóstico do gerador?', 'gerador'),
]
# IA na nuvem (quando a tela chama a IA, com o aparelho ativado): SEM DADOS, trecho do guia e pergunta sobre o app — nunca
# emergência, óleo, registro no diário, resposta pronta ou só um cumprimento.
PEDE_IA = {
    'Oque você faz?': True, 'o que vc sabe fazer?': True, 'como ligar o gerador?': True, 'qual o preço do dólar?': True, 'não registre isso': True,
    '': False, 'oi, bom dia': False, 'MAYDAY, homem ao mar!': False, 'pressão de óleo baixa no motor BB': False,
    'Registre no diário: saída com 4 pessoas': False, 'autonomia': False, 'é seguro sair hoje?': False, 'diagnóstico': False,
}


def main():
    falhas = 0
    with sync_playwright() as p:
        b = p.chromium.launch(channel=CANAL, headless=True)
        pg = b.new_page()
        erros = []
        pg.on('pageerror', lambda e: erros.append(str(e)))
        pg.goto(BASE + 'base-conhecimento.json')  # mesma origem, sem a porta de login
        pg.add_script_tag(url=BASE + 'capitao-dados.js')
        pg.add_script_tag(url=BASE + 'capitao-brain.js')
        pg.evaluate("() => new Promise(r => { window.CapitaoBrain.carregaBase(); setTimeout(r, 800); })")
        res = pg.evaluate("""(casos) => { const B = window.CapitaoBrain; localStorage.clear();
          return casos.map(([q, k]) => { const a = B.answer(q, { platform: 'app' }); return { q, esperado: k, key: a.key, src: a.src, text: a.text, curta: B.falaCurta(a), ia: B.pedeIA(a, q) }; }); }""", CASOS)
        diario = pg.evaluate("() => window.CapitaoBrain.loadDiario().length")
        for r in res:
            ok = r['key'] == r['esperado']
            fonte = bool(r['src']) and r['src'].startswith('Fonte')
            semdados = r['key'] != 'fallback' or 'SEM DADOS' in r['text']
            ia = r['q'] not in PEDE_IA or r['ia'] == PEDE_IA[r['q']]
            if not (ok and fonte and semdados and ia):
                falhas += 1
                print('FALHA', json.dumps({k: r[k] for k in ('q', 'esperado', 'key', 'ia', 'src')}, ensure_ascii=False))
        print('%d perguntas · %d falhas · linhas gravadas no diário: %d (esperado: 1, só o comando explícito)' % (len(res), falhas, diario))
        if diario != 1:
            falhas += 1
        # Ficha de bordo que vai para a IA: todos os blocos, rótulo DEMO, SEM DADOS honesto, sem coordenadas e cabendo no proxy.
        f = pg.evaluate("() => window.CapitaoBrain.ficha('app')")
        blocos = ['## Agora', '## Sobre o app', '## Embarcação', '## Equipamentos', '## Telemetria', '## Manutenção', '## Horímetros', '## Autonomia e consumo',
                  '## Documentos', '## Pendências', '## Diário de bordo', '## Equipe e contatos', '## Clima e maré', '## Guias de bordo', '## Emergência']
        faltam = [x for x in blocos if x not in f]
        coord = [x for x in ("26°59", "048°36", "-26.99", "-48.6") if x in f]
        voz = pg.evaluate("() => window.CapitaoBrain.falaCurta({ key: 'ia', text: 'Sou o Capitão IA.\\nRespondo sobre telemetria, manutenção e documentos, sempre com a fonte.\\n• item\\nFonte: Sobre o app' })")
        x = pg.evaluate("""() => { const B = window.CapitaoBrain, r = (q) => { const a = B.answer(q, { platform: 'app', commit: false }); return { a, f: B.ficha('app', q, a), voz: B.falaCurta(a) }; };
            const meta = r('Oque você faz?'), base = r('como ligar o gerador?'), sd = r('qual o calado do barco?'), oi = r('oi'), dg = r('diagnóstico');
            return { metaF: meta.f, baseF: base.f, sdF: sd.f, metaVoz: meta.voz, oiVoz: oi.voz, dgTexto: dg.a.text, dgSrc: dg.a.src, versao: B.VERSAO }; }""")
        for nome, cond, extra in [
            ('ficha resumida para pergunta sobre o app e para trecho do guia (sem telemetria, < 4 mil letras)', '## Ficha resumida' in x['metaF'] and '## Telemetria' not in x['metaF'] and len(x['metaF']) < 4000 and '## Ficha resumida' in x['baseF'], (len(x['metaF']), len(x['baseF']))),
            ('ficha completa para SEM DADOS', '## Telemetria' in x['sdF'] and '## Ficha resumida' not in x['sdF'], len(x['sdF'])),
            ('voz de "Oque você faz?" sem a IA diz o que o Capitão faz (não repete a abertura)', x['metaVoz'].startswith('Respondo sobre telemetria') and x['oiVoz'] == 'Capitão IA online. Que precisa?', (x['metaVoz'][:60], x['oiVoz'])),
            ('diagnóstico local: versões, internet, fonte "este aparelho"', 'Diagnóstico do Capitão IA neste aparelho' in x['dgTexto'] and 'cérebro ' + x['versao'] in x['dgTexto'] and x['dgSrc'].startswith('Fonte: este aparelho'), x['dgTexto'][:200]),
            ('ficha com todos os blocos', not faltam, faltam),
            ('ficha sem coordenadas do barco', not coord, coord),
            ('ficha com rótulo DEMO e SEM DADOS', 'DEMO' in f and 'SEM DADOS' in f, ''),
            ('ficha entre 3.000 e 10.000 letras (o proxy aceita 12.000)', 3000 <= len(f) <= 10000, len(f)),
            ('voz da resposta da IA: 1ª frase curta + a seguinte, sem a fonte', voz == 'Sou o Capitão IA. Respondo sobre telemetria, manutenção e documentos, sempre com a fonte.', voz),
        ]:
            if not cond:
                falhas += 1
                print('FALHA', nome, extra)
        print('ficha de bordo: %d letras' % len(f))
        if '-v' in sys.argv:
            print(f)
        if erros:
            falhas += 1
            print('ERROS DE SCRIPT:', erros)
        if '-v' in sys.argv:
            for r in res:
                print('\n## ' + r['q'] + ' → ' + r['key'] + '\n' + r['text'] + '\n' + r['src'] + '\n[voz] ' + r['curta'])
        b.close()
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
