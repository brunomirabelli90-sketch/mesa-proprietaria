"""
Petroleo (Brent) e Minerio de ferro - fontes extras pro "filtro macro" do
leilao (ver estrategia_leilao.calcular_score_macro), alem de DX/VIX
(mercado_externo.py) e S&P500 (Excel/BlackArrow).

Petroleo vem do Yahoo Finance (yfinance), igual VIX/DXY. Minerio de ferro
NAO tem fonte gratuita por API confiavel, entao aqui e' scraping direto de
uma pagina publica - por isso e' a parte mais fragil desse painel: se o
site mudar de layout, PADRAO_PERCENTUAL para de achar o numero e o campo
fica "-" (nao trava o resto do painel, so esse valor).

Roda num loop de fundo separado (igual mercado_externo.py), buscando de
tempos em tempos - o ciclo rapido da tela (1,5s) so le o cache.
"""
import re
import threading
import time
import urllib.request

import yfinance as yf

TICKER_PETROLEO = "BZ=F"  # Brent Crude Oil futures
URL_MINERIO_PADRAO = "https://www.chinaitools.com/iron/"
INTERVALO_ATUALIZACAO_S = 60

# primeiro numero no formato "12,34%" ou "-1.2%" que aparecer na pagina.
PADRAO_PERCENTUAL = re.compile(r"([+-]?\d+[.,]\d+)\s*%")

_lock = threading.Lock()
_ultimo = {"petroleo": None, "minerio": None}
_thread_iniciada = False
_url_minerio = URL_MINERIO_PADRAO


def definir_url_minerio(url):
    """Troca o link do minerio em tempo de execucao, sem editar o arquivo -
    util se o site padrao mudar de endereco."""
    global _url_minerio
    _url_minerio = url


def _variacao_petroleo():
    try:
        info = yf.Ticker(TICKER_PETROLEO).fast_info
        preco = info.last_price
        fechamento_anterior = info.previous_close
    except Exception:
        return None
    if not preco or not fechamento_anterior:
        return None
    return (preco - fechamento_anterior) / fechamento_anterior * 100


def _variacao_minerio():
    try:
        req = urllib.request.Request(_url_minerio, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None

    m = PADRAO_PERCENTUAL.search(html)
    if not m:
        return None
    texto = m.group(1).replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _loop_atualizacao():
    while True:
        novo = {"petroleo": _variacao_petroleo(), "minerio": _variacao_minerio()}
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
