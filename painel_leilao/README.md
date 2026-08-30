# Painel BMT - Leilão

Painel visual pra estratégia de leilão do mini índice (WINFUT): mostra em
tempo real se o gap favorece compra ou venda, lendo dados que o Profit e o
BlackArrow exportam ao vivo pra um Excel (via RTD).

**Regra da v1:**
- Preço Teórico > Fechamento Anterior → **gap de alta** → sinal base **VENDA**
- Preço Teórico < Fechamento Anterior → **gap de baixa** → sinal base **COMPRA**
- Compara também o Preço Teórico com o **Ajuste Anterior**: se apontar pra
  mesma direção do sinal base, mostra "confirma"; se for pro lado oposto,
  mostra "diverge". **Isso é só informativo por enquanto** — o painel não
  trava um veredito único sozinho, porque essa combinação ainda está sendo
  validada.
- Mostra a variação do S&P500 (destaque), Nasdaq e Dow Jones, também só
  informativo, pra correlacionar visualmente.

**Fora da v1** (fica pra depois, quando tiver regra objetiva definida):
DXY (não sai nem do Profit nem do BlackArrow, precisaria de fonte externa) e
o filtro de "macro" no diário/semanal/mensal.

## Requisitos

- Windows, com Profit e BlackArrow (Nelogica) instalados
- Microsoft Excel
- Python 3.9+

```
pip install -r requirements.txt
```

## Montando o Excel (uma vez só, antes de operar)

1. Cria um Excel novo, salva como **`Painel BMT Leilao.xlsx`** (esse nome
   exato, ou ajusta `NOME_ARQUIVO` em `excel_leitor.py`) e deixa aberto.

2. Renomeia a primeira aba pra **`WINFUT`**. No Profit, com o WINFUT
   aberto: **Exportar em Tempo Real (RTD/DDE)** → marca **RTD** → seleciona
   as colunas **Fechamento Anterior**, **Aj. Anterior** e **Preço
   Teórico** → **Copiar**. Cola na célula **A1** dessa aba.

3. Cria uma segunda aba chamada **`INDICES`**. No BlackArrow, com os
   ativos MESFUT (S&P500), MNQFUT (Nasdaq) e MYMFUT (Dow Jones) abertos:
   mesmo processo, RTD, coluna **Variação**, Copiar, cola na célula **A1**
   dessa aba.

4. Confirma que ficou assim (linha 2 em diante já vem com as fórmulas
   `=RTD(...)` que atualizam sozinhas):

   **Aba WINFUT**
   | Asset  | Fechamento Anterior | Aj. Anterior | Preço Teórico |
   |--------|---------------------|--------------|----------------|
   | WINFUT | 177725              | 177822       | 0              |

   **Aba INDICES**
   | Asset  | Variação |
   |--------|----------|
   | MESFUT | 0        |
   | MNQFUT | 0        |
   | MYMFUT | 0        |

5. Salva e **deixa o Excel aberto** — o painel conecta nessa instância já
   rodando (não abre uma cópia nova, porque isso perderia o link RTD ao
   vivo).

Se o Profit ou o BlackArrow estiverem em Replay, cuidado: eles podem gerar
uma linha extra tipo `[R] WINFUT` — apague essa linha ou garanta que a
linha 2 é sempre o ativo real, já que o painel sempre lê a **linha 2**.

## Uso

Com o Excel montado e aberto (ver acima):

```
python painel_leilao.py
```

O painel atualiza sozinho a cada 1,5s. Se não achar o Excel aberto, mostra
"Excel não encontrado" e fica tentando reconectar sem precisar reiniciar o
programa.

## Arquivos

- `estrategia_leilao.py` — lógica pura do cálculo do sinal (sem depender
  de Excel/Windows), testável isoladamente.
- `excel_leitor.py` — conecta na instância do Excel já aberta (via
  `pywin32`) e lê as células.
- `painel_leilao.py` — a interface gráfica (Tkinter).
