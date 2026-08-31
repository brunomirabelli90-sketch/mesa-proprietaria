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


def tendencia_vwap(preco_teorico, vwap):
    """Compara o Preco Teorico com uma VWAP (mensal ou semanal): preco
    acima da VWAP = tendencia de ALTA, preco abaixo = tendencia de BAIXA.
    Isso e' so leitura de tendencia (onde o preco esta em relacao a media),
    sem relacao com o sinal de compra/venda do leilao (que e' baseado no
    gap contra o fechamento/ajuste anterior)."""
    if not preco_teorico or not vwap:
        return None
    if preco_teorico > vwap:
        return ALTA
    if preco_teorico < vwap:
        return BAIXA
    return None
