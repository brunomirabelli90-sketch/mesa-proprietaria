"""
Leitura ao vivo de um Excel ja aberto (ligado por RTD no Profit/BlackArrow).

Usa win32com pra conectar na instancia do Excel que ja esta rodando, em vez
de abrir o arquivo de novo - abrir de novo criaria uma copia sem o link RTD
ao vivo (as celulas ficariam paradas).

Layout esperado no arquivo (ver README.md pra montar):
  Aba "WINFUT":  B2=Fechamento Anterior, C2=Aj. Anterior, D2=Preco Teorico,
                 E2=VWAP Mensal, F2=VWAP Semanal
  Aba "INDICES": B2=Variacao MESFUT, B3=Variacao MNQFUT, B4=Variacao MYMFUT
"""
import win32com.client
import pywintypes

NOME_ARQUIVO = "Painel BMT Leilao.xlsx"


def _paranum(valor):
    """Alguns campos do RTD do Profit vem como texto ja formatado (ex:
    "173.157" usando ponto como separador de milhar, ao inves do numero
    173157), dependendo do formato da celula. Converte pro numero real;
    se nao for possivel, devolve None (o painel trata como sem dado)."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip()
    if not texto:
        return None
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def conectar_workbook(nome_arquivo=NOME_ARQUIVO):
    """Acha o Workbook desse nome numa instancia do Excel ja aberta.
    Retorna None se o Excel nao estiver aberto ou o arquivo nao estiver
    entre as planilhas abertas (sem levantar excecao - quem chama decide
    o que fazer, tipo mostrar 'aguardando Excel' e tentar de novo)."""
    try:
        excel = win32com.client.GetActiveObject("Excel.Application")
    except pywintypes.com_error:
        return None

    try:
        for wb in excel.Workbooks:
            if wb.Name == nome_arquivo:
                return wb
    except pywintypes.com_error:
        return None

    return None


def ler_dados(workbook):
    """Le as celulas que o painel precisa. Retorna dict, ou None se a
    leitura falhar no meio (ex: Excel fechou, aba renomeada)."""
    try:
        aba_winfut = workbook.Sheets("WINFUT")
        aba_indices = workbook.Sheets("INDICES")

        fechamento = aba_winfut.Range("B2").Value
        ajuste = aba_winfut.Range("C2").Value
        teorico = aba_winfut.Range("D2").Value
        vwap_mensal = aba_winfut.Range("E2").Value
        vwap_semanal = aba_winfut.Range("F2").Value

        sp500 = aba_indices.Range("B2").Value
        nasdaq = aba_indices.Range("B3").Value
        dow = aba_indices.Range("B4").Value
    except pywintypes.com_error:
        return None

    return {
        "fechamento": _paranum(fechamento),
        "ajuste": _paranum(ajuste),
        "teorico": _paranum(teorico),
        "vwap_mensal": _paranum(vwap_mensal),
        "vwap_semanal": _paranum(vwap_semanal),
        "sp500": _paranum(sp500),
        "nasdaq": _paranum(nasdaq),
        "dow": _paranum(dow),
    }
