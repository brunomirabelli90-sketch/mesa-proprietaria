# Painel BMT - Leilão (Filtro Macro)

Painel visual pro "filtro macro" do leilão do mini índice (WINFUT): soma a
variação de ativos que costumam puxar o Ibovespa/WIN junto e vira um
veredito de COMPRA/VENDA/NEUTRO.

**Não depende de Excel, Profit nem BlackArrow** — a versão anterior lia o
gap do leilão via RTD numa planilha, mas isso foi removido (a conexão via
Excel travava com frequência). Agora todo dado vem de fora, direto por
código, sem precisar montar planilha nenhuma.

**Regra:**

```
score = Petróleo + Minério + S&P500 - Índice Dólar - VIX
```

Petróleo, Minério e S&P500 em alta ajudam o Ibovespa/WIN, por isso somam;
Dólar e VIX em alta costumam ser ruins pra bolsa/commodities emergentes,
por isso entram invertidos (subtraindo). Score acima de `+1.0` mostra
**COMPRA**; abaixo de `-1.0` mostra **VENDA**; entre os dois, **NEUTRO**.
Esse limiar (`estrategia_leilao.LIMIAR_SCORE_MACRO`) é só um chute inicial
razoável — ajusta no arquivo conforme for validando se ajuda de verdade.

**Isso é experimental** — é uma ideia parecida com um painel de terceiro
que o Bruno viu por aí, ainda sendo validada. Guarda as leituras (botão
"Salvar leitura") pra poder olhar depois se bateu ou não.

## Requisitos

- Windows (testado pra isso — usa `os.startfile` pra abrir o histórico)
- Python 3.9+
- Internet liberada na máquina (todos os dados vêm de fora)

```
pip install -r requirements.txt
```

## Uso

```
python painel_leilao.py
```

Ou dá duplo clique em **`abrir_painel_leilao.bat`** — abre sem janela de
console atrás e com o nome/ícone certo na barra de tarefas (rodar
`python painel_leilao.py` direto mostra "Python" genérico ali, porque é o
próprio interpretador aparecendo, não o programa).

O painel atualiza sozinho a cada 1,5s (lendo o cache que os loops de fundo
mantêm — ver abaixo), sem precisar de nada aberto além dele mesmo.

### De onde vêm os dados

Tudo via Yahoo Finance (`yfinance`), rodando em loops de fundo separados
(`mercado_externo.py` e `mercado_macro.py`) que buscam a cada 60s e
guardam num cache — o ciclo rápido da tela (1,5s) só lê esse cache, nunca
trava esperando rede:

| Ativo         | Fonte                          | Entra no score? |
|---------------|---------------------------------|:---:|
| VIX           | Yahoo Finance (`^VIX`)          | Sim (invertido) |
| Índice Dólar  | Yahoo Finance (`DX-Y.NYB`)      | Sim (invertido) |
| S&P500        | Yahoo Finance (`ES=F`, futuros) | Sim |
| Nasdaq        | Yahoo Finance (`NQ=F`, futuros) | Não (só informativo) |
| Dow Jones     | Yahoo Finance (`YM=F`, futuros) | Não (só informativo) |
| Petróleo      | Yahoo Finance (`BZ=F`, Brent)   | Sim |
| Minério       | **Scraping** de uma página pública (não há API gratuita confiável pra isso) | Sim |

Por serem dados gratuitos, têm um atraso de alguns minutos (não é tempo
real tick a tick) — aceitável pra um filtro macro, que não precisa de
precisão de segundo. Se a internet cair ou alguma fonte falhar, o campo
correspondente mostra "-" e o resto do painel continua funcionando.

O **minério** é a parte mais frágil: como não há fonte gratuita
confiável por API, o painel faz scraping de uma página pública
(`mercado_macro.URL_MINERIO_PADRAO`). Se o site mudar de layout, esse
campo especificamente para de funcionar (vira "-", não trava o resto). Se
isso acontecer, dá pra trocar o link com
`mercado_macro.definir_url_minerio("outro link")` ou editando a
constante no arquivo.

### Salvar leituras (histórico)

Botão **"Salvar leitura"** grava data/hora + o valor de cada ativo + o
score + o veredito num arquivo `historico_macro.csv`, na mesma pasta —
um "banco de dados" simples que abre em qualquer Excel/planilha pra você
olhar depois quais leituras bateram ou não. Cada clique acrescenta uma
linha nova; nada é sobrescrito.

Botão **"Ver histórico"** abre esse CSV no programa padrão do Windows
(geralmente o Excel).

### Modo live (esconder a estratégia)

Checkbox **"Modo live (ocultar estratégia)"** no topo esconde tudo que
revela como o veredito é calculado — os ativos individuais e o score —
tudo vira `••••`. O **badge grande (COMPRA/VENDA/NEUTRO/AGUARDANDO)**
continua visível e atualizando, porque é a parte que faz sentido mostrar
numa live. Liga/desliga na hora, sem esperar o próximo ciclo.

## Compilando pra `.exe`

```
pip install pyinstaller
python -m PyInstaller --onefile --windowed --icon=icone.ico --name PainelLeilao painel_leilao.py
```

`--windowed` evita abrir uma janela de console preta atrás do painel.

## Arquivos

- `estrategia_leilao.py` — lógica pura do cálculo do score/veredito (sem
  depender de rede/Windows), testável isoladamente.
- `mercado_externo.py` — busca VIX, Índice Dólar, S&P500, Nasdaq e Dow
  (Yahoo Finance) num loop de fundo.
- `mercado_macro.py` — busca Petróleo (Yahoo Finance) e Minério de ferro
  (scraping) num loop de fundo.
- `historico_macro.py` — salva/lê o `historico_macro.csv` com as leituras
  salvas manualmente.
- `painel_leilao.py` — a interface gráfica (Tkinter).
- `icone.ico` — ícone do programa (janela e `.exe` compilado).
- `excel_leitor.py` — **não é mais usado** pelo painel (ficou da versão
  anterior, que lia o gap do leilão via Excel/RTD). Deixei o arquivo no
  projeto caso essa parte volte a ser útil no futuro.
