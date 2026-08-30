"""
Leitura ao vivo de um Excel ja aberto (ligado por RTD no Profit/BlackArrow).

Usa win32com pra conectar na instancia do Excel que ja esta rodando, em vez
de abrir o arquivo de novo - abrir de novo criaria uma copia sem o link RTD
ao vivo (as celulas ficariam paradas).

Layout esperado no arquivo (ver README.md pra montar):
  Aba "WINFUT":  B2=Fechamento Anterior, C2=Aj. Anterior, D2=Preco Teorico
  Aba "INDICES": B2=Variacao MESFUT, B3=Variacao MNQFUT, B4=Variacao MYMFUT
"""
import win32com.client
import pywintypes

NOME_ARQUIVO = "Painel BMT Leilao.xlsx"


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

        sp500 = aba_indices.Range("B2").Value
        nasdaq = aba_indices.Range("B3").Value
        dow = aba_indices.Range("B4").Value
    except pywintypes.com_error:
        return None

    return {
        "fechamento": fechamento,
        "ajuste": ajuste,
        "teorico": teorico,
        "sp500": sp500,
        "nasdaq": nasdaq,
        "dow": dow,
    }
