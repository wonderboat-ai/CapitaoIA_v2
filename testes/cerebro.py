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
    ('motores volvo penta', 'motores'), ('troca do rotor do gerador', 'base'),
]


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
          return casos.map(([q, k]) => { const a = B.answer(q, { platform: 'app' }); return { q, esperado: k, key: a.key, src: a.src, text: a.text, curta: B.falaCurta(a) }; }); }""", CASOS)
        diario = pg.evaluate("() => window.CapitaoBrain.loadDiario().length")
        for r in res:
            ok = r['key'] == r['esperado']
            fonte = bool(r['src']) and r['src'].startswith('Fonte')
            semdados = r['key'] != 'fallback' or 'SEM DADOS' in r['text']
            if not (ok and fonte and semdados):
                falhas += 1
                print('FALHA', json.dumps({k: r[k] for k in ('q', 'esperado', 'key', 'src')}, ensure_ascii=False))
        print('%d perguntas · %d falhas · linhas gravadas no diário: %d (esperado: 1, só o comando explícito)' % (len(res), falhas, diario))
        if diario != 1:
            falhas += 1
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
