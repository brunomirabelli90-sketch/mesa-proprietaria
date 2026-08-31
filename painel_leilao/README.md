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
- Mostra também **VIX** e **Índice Dólar (DXY)**, vindos do Yahoo Finance
  (não saem nem do Profit nem do BlackArrow) — também só informativo, com
  um pequeno atraso (não é tick a tick, ver seção abaixo).
- Mostra **Preço Atual (Último)** do WINFUT, disponível o pregão inteiro
  (diferente do Preço Teórico, que só existe durante a janela do leilão e
  fica 0 no resto do dia).
- Mostra **VWAP Mensal** e **VWAP Semanal** do WINFUT (vem do Profit, igual
  Fechamento/Ajuste/Preço Teórico), cada uma com a tendência ao lado —
  **ALTA** (verde) se o preço atual estiver acima da VWAP, **BAIXA**
  (vermelho) se estiver abaixo. Isso usa o preço **atual**, não o teórico,
  justamente pra funcionar o dia todo, não só na janela do leilão. Não
  entra em nenhum cálculo do sinal de compra/venda, é só leitura de
  tendência. Se essas colunas não estiverem na planilha, o painel mostra
  "-" nelas e continua funcionando normal.

**Fora da v1** (fica pra depois, quando tiver regra objetiva definida):
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
   as colunas **Último**, **Fechamento Anterior**, **Aj. Anterior**,
   **Preço Teórico**, **VWAP Mensal** e **VWAP Semanal** → **Copiar**. Cola
   na célula **A1** dessa aba.

3. Cria uma segunda aba chamada **`INDICES`**. No BlackArrow, com os
   ativos MESFUT (S&P500), MNQFUT (Nasdaq) e MYMFUT (Dow Jones) abertos:
   mesmo processo, RTD, coluna **Variação**, Copiar, cola na célula **A1**
   dessa aba.

4. Confirma que ficou assim (linha 2 em diante já vem com as fórmulas
   `=RTD(...)` que atualizam sozinhas):

   **Aba WINFUT**
   | Asset  | Último | Fechamento Anterior | Aj. Anterior | Preço Teórico | VWAP Mensal | VWAP Semanal |
   |--------|--------|---------------------|--------------|----------------|-------------|--------------|
   | WINFUT | 179765 | 177725              | 177822       | 0              | 176900      | 177400       |

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

Com o Excel montado e aberto (ver acima), duas formas de abrir:

```
python painel_leilao.py
```

Ou dá duplo clique em **`abrir_painel_leilao.bat`** — abre sem janela de
console atrás e com o nome/ícone certo na barra de tarefas (rodar
`python painel_leilao.py` direto mostra "Python 3.14" genérico ali, porque
é o próprio interpretador aparecendo, não o programa).

O painel atualiza sozinho a cada 1,5s. Se não achar o Excel aberto, mostra
"Excel não encontrado" e fica tentando reconectar sem precisar reiniciar o
programa.

### VIX e Índice Dólar (DXY)

Esses dois não vêm do Excel — são buscados direto do Yahoo Finance
(biblioteca `yfinance`), porque nem o Profit nem o BlackArrow exportam
DXY, e o VIX não estava sendo puxado por RTD. Rodam num loop separado, a
cada 60s (`mercado_externo.INTERVALO_ATUALIZACAO_S`), e não travam o painel
esperando rede — o ciclo de 1,5s só lê o último valor já buscado.

Por serem dados gratuitos do Yahoo, têm um atraso de alguns minutos (não é
tempo real tick a tick). Isso é aceitável porque são só informativos, igual
S&P500/Nasdaq/Dow — não entram no cálculo do sinal de compra/venda.
Precisa de internet liberada na máquina pra esses dois funcionarem; se não
tiver, o painel continua funcionando normal, só mostra "-" nesses campos.

### Modo live (esconder a estratégia)

Checkbox **"Modo live (ocultar estratégia)"** no topo esconde tudo que
revela como o sinal é calculado — valores e nomes de Fechamento, Ajuste,
Preço Teórico, os dois gaps, a linha de confirma/diverge, e os índices lá
fora — tudo vira `••••`. O **badge grande (COMPRA/VENDA/AGUARDANDO)**
continua visível e atualizando, porque é a parte que faz sentido mostrar
numa live. Liga/desliga na hora, sem esperar o próximo ciclo.

## Compilando pra `.exe`

```
pip install pyinstaller
python -m PyInstaller --onefile --windowed --icon=icone.ico --name PainelLeilao painel_leilao.py
```

`--windowed` evita abrir uma janela de console preta atrás do painel.

## Arquivos

- `estrategia_leilao.py` — lógica pura do cálculo do sinal (sem depender
  de Excel/Windows), testável isoladamente.
- `excel_leitor.py` — conecta na instância do Excel já aberta (via
  `pywin32`) e lê as células.
- `painel_leilao.py` — a interface gráfica (Tkinter).
- `icone.ico` — ícone do programa (janela e `.exe` compilado).
