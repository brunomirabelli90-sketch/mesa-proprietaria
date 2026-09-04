"""
Historico das leituras do Filtro Macro - "banco de dados" simples em CSV
(abre em qualquer Excel/planilha), sem depender de nada alem da biblioteca
padrao do Python. Cada linha e' uma leitura salva manualmente (botao
"Salvar" no painel), com data/hora, o valor de cada ativo e o veredito.
"""
import csv
import datetime
import os

ARQUIVO_HISTORICO = "historico_macro.csv"

CAMPOS = [
    "data_hora", "petroleo", "minerio", "dxy", "vix", "sp500", "nasdaq", "dow",
    "score_macro", "veredito",
]


def salvar_leitura(dados, resultado, caminho=ARQUIVO_HISTORICO):
    """Acrescenta uma linha no CSV com a leitura atual. 'dados' e' o dict
    de mercado (petroleo/minerio/dxy/vix/sp500/...), 'resultado' e' o dict
    devolvido por estrategia_leilao.calcular_score_macro. Cria o arquivo
    (com cabecalho) na primeira vez; so' acrescenta depois disso."""
    arquivo_novo = not os.path.exists(caminho)
    linha = {
        "data_hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "petroleo": dados.get("petroleo"),
        "minerio": dados.get("minerio"),
        "dxy": dados.get("dxy"),
        "vix": dados.get("vix"),
        "sp500": dados.get("sp500"),
        "nasdaq": dados.get("nasdaq"),
        "dow": dados.get("dow"),
        "score_macro": resultado.get("score"),
        "veredito": resultado.get("veredito"),
    }
    with open(caminho, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        if arquivo_novo:
            writer.writeheader()
        writer.writerow(linha)
    return linha


def ler_historico(caminho=ARQUIVO_HISTORICO):
    """Le todas as linhas salvas. Devolve lista de dicts (vazia se o
    arquivo ainda nao existir)."""
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
