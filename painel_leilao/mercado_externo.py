"""
Leitura periodica de VIX, DXY (Indice Dolar) e os futuros de indices
americanos (S&P500/Nasdaq/Dow) via Yahoo Finance (yfinance).

Antes S&P500/Nasdaq/Dow vinham do Excel (RTD do BlackArrow) - isso foi
removido (o Excel travava direto), entao agora os cinco vem todos daqui.
Diferente do resto do painel, aqui tem chamada de rede - por isso roda
num loop de fundo (thread separada), buscando de tempos em tempos e
guardando o ultimo valor num cache. O ciclo rapido do painel (a cada
1,5s) so le esse cache, nunca espera a rede.

Tem um atraso tipico de alguns minutos no plano gratuito do Yahoo. VIX,
DXY, S&P500 sao informativos ou entram no score do Filtro Macro (ver
estrategia_leilao.calcular_score_macro); Nasdaq/Dow sao so informativos.
"""
import threading
import time

import yfinance as yf

TICKERS = {
    "vix": "^VIX",
    "dxy": "DX-Y.NYB",
    "sp500": "ES=F",   # E-mini S&P 500 futures
    "nasdaq": "NQ=F",  # E-mini Nasdaq-100 futures
    "dow": "YM=F",     # E-mini Dow futures
}
INTERVALO_ATUALIZACAO_S = 60

_lock = threading.Lock()
_ultimo = {chave: None for chave in TICKERS}
_thread_iniciada = False


def _variacao_percentual(ticker):
    try:
        info = yf.Ticker(ticker).fast_info
        preco = info.last_price
        fechamento_anterior = info.previous_close
    except Exception:
        return None
    if not preco or not fechamento_anterior:
        return None
    return (preco - fechamento_anterior) / fechamento_anterior * 100


def _loop_atualizacao():
    while True:
        novo = {chave: _variacao_percentual(ticker) for chave, ticker in TICKERS.items()}
        with _lock:
            _ultimo.update(novo)
        time.sleep(INTERVALO_ATUALIZACAO_S)


def iniciar():
    """Inicia o loop de atualizacao em background. Chamar uma vez so; uma
    segunda chamada nao faz nada (evita threads duplicadas)."""
    global _thread_iniciada
    if _thread_iniciada:
        return
    _thread_iniciada = True
    threading.Thread(target=_loop_atualizacao, daemon=True).start()


def obter_ultimo():
    """Leitura thread-safe do ultimo valor buscado. Nunca bloqueia nem
    acessa rede - so le o cache que o loop de fundo mantem atualizado."""
    with _lock:
        return dict(_ultimo)
