"""
Logica pura da estrategia de leilao (sem dependencia de Excel/Windows),
separada do resto pra dar pra testar isoladamente.

Regra:
- Preco Teorico > Fechamento Anterior  -> GAP DE ALTA  -> sinal base VENDA
- Preco Teorico < Fechamento Anterior  -> GAP DE BAIXA  -> sinal base COMPRA
- Preco Teorico == Fechamento Anterior -> NEUTRO (sem gap)

O Ajuste Anterior e' comparado da mesma forma contra o Preco Teorico. Se
apontar pra mesma direcao do sinal base, "confirma". Se apontar pro lado
oposto, "diverge". Isso e' so informativo por enquanto (o proprio Bruno
ainda esta validando se ajuda ou atrapalha) - o painel mostra os dois,
nao trava um veredito unico sozinho.
"""

SEM_DADO = "AGUARDANDO"
COMPRA = "COMPRA"
VENDA = "VENDA"
NEUTRO = "NEUTRO"
ALTA = "ALTA"
BAIXA = "BAIXA"


def direcao(gap):
    if gap > 0:
        return VENDA
    if gap < 0:
        return COMPRA
    return NEUTRO


def calcular_sinal(fechamento, ajuste, teorico):
    """fechamento/ajuste/teorico podem vir None ou 0 (leilao ainda nao
    comecou, ou celula vazia) - nesse caso devolve status AGUARDANDO."""
    if not fechamento or not teorico:
        return {
            "status": SEM_DADO,
            "sinal_base": None,
            "sinal_ajuste": None,
            "confirma": None,
            "gap_fechamento": None,
            "gap_ajuste": None,
        }

    gap_fechamento = teorico - fechamento
    sinal_base = direcao(gap_fechamento)

    gap_ajuste = None
    sinal_ajuste = None
    confirma = None
    if ajuste:
        gap_ajuste = teorico - ajuste
        sinal_ajuste = direcao(gap_ajuste)
        confirma = sinal_ajuste == sinal_base and sinal_base != NEUTRO

    return {
        "status": sinal_base,
        "sinal_base": sinal_base,
        "sinal_ajuste": sinal_ajuste,
        "confirma": confirma,
        "gap_fechamento": gap_fechamento,
        "gap_ajuste": gap_ajuste,
    }


def tendencia_vwap(preco_atual, vwap):
    """Compara o preco atual do indice com uma VWAP (mensal ou semanal):
    preco acima da VWAP = tendencia de ALTA, preco abaixo = tendencia de
    BAIXA. Isso e' so leitura de tendencia (onde o preco esta em relacao a
    media), sem relacao com o sinal de compra/venda do leilao (que e'
    baseado no gap do Preco Teorico contra o fechamento/ajuste anterior,
    e so existe durante a janela do leilao)."""
    if not preco_atual or not vwap:
        return None
    if preco_atual > vwap:
        return ALTA
    if preco_atual < vwap:
        return BAIXA
    return None


LIMIAR_SCORE_MACRO = 1.0


def calcular_score_macro(petroleo, minerio, dxy, vix, sp500):
    """Filtro macro EXPERIMENTAL, separado do sinal principal do leilao
    (que continua sendo so o gap vs fechamento/ajuste). Soma a variacao %
    de ativos que costumam puxar o Ibovespa/WIN, invertendo o sinal dos
    dois que sao "risk-off" (dolar forte e VIX em alta prejudicam bolsa
    emergente e commodities):

        score = petroleo + minerio + sp500 - dxy - vix

    petroleo/minerio em alta, dolar/VIX em baixa e S&P em alta -> score
    positivo -> veredito COMPRA. Cada perna e' opcional (usa so as que
    tiverem dado); se nenhuma tiver, devolve SEM_DADO."""
    valores = {"petroleo": petroleo, "minerio": minerio, "dxy": dxy, "vix": vix, "sp500": sp500}
    if all(v is None for v in valores.values()):
        return {"score": None, "veredito": SEM_DADO}

    score = 0.0
    for chave in ("petroleo", "minerio", "sp500"):
        if valores[chave] is not None:
            score += valores[chave]
    for chave in ("dxy", "vix"):
        if valores[chave] is not None:
            score -= valores[chave]

    if score > LIMIAR_SCORE_MACRO:
        veredito = COMPRA
    elif score < -LIMIAR_SCORE_MACRO:
        veredito = VENDA
    else:
        veredito = NEUTRO

    return {"score": score, "veredito": veredito}
