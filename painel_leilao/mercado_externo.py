"""
Leitura periodica de VIX e DXY (Indice Dolar) via Yahoo Finance (yfinance).

Complementa os indices que ja vem do Excel (RTD do Profit/BlackArrow), que
nao exportam esses dois. Diferente do resto do painel, aqui tem uma chamada
de rede - por isso roda num loop de fundo (thread separada), buscando de
tempos em tempos e guardando o ultimo valor num cache. O ciclo rapido do
painel (a cada 1,5s) so le esse cache, nunca espera a rede.

Sao dados so informativos (igual S&P500/Nasdaq/Dow), com um atraso tipico
de alguns minutos no plano gratuito do Yahoo - aceitavel aqui porque nao
alimentam o calculo do sinal, so dao contexto visual.
"""
import threading
import time

import yfinance as yf

TICKERS = {"vix": "^VIX", "dxy": "DX-Y.NYB"}
INTERVALO_ATUALIZACAO_S = 60

_lock = threading.Lock()
_ultimo = {"vix": None, "dxy": None}
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
