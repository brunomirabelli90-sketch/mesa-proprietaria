# Autoclicker multi-conta

Autoclicker visual: clica em coordenadas de tela pré-calibradas, replicando
uma ação (compra/venda/zerar) em várias janelas de boleta ao mesmo tempo.
Não lê nem se conecta a nenhuma plataforma — só move o mouse e clica, como
você faria manualmente.

**Antes de usar em conta real:** confirme no regulamento da sua mesa que
operar as mesmas contas simultaneamente é permitido. A ferramenta não sabe
disso, só executa cliques.

## Requisitos

- Windows (testado para isso; usa `pyautogui` + `keyboard`)
- Python 3.9+

```
pip install -r requirements.txt
```

`keyboard` registra hooks globais de teclado. Se o Profit/ProfitOne estiver
rodando como Administrador e os hotkeys não responderem, rode o terminal
também como Administrador (janelas elevadas ignoram entrada de processos
não elevados no Windows).

Se as janelas estiverem em monitores com escala de DPI diferente, ou se
mudar a escala do Windows entre a calibração e o uso, as coordenadas vão
ficar erradas — recalibre nesse caso.

## Uso

1. Abra as boletas na tela, na mesma posição/tamanho que vai usar depois.
2. Calibre as coordenadas dos botões:

   ```
   python calibrar.py
   ```

   Para cada conta e botão pedido, passe o mouse em cima do botão real na
   tela e pressione **F8** para capturar (ou **F7** para pular um botão que
   aquela boleta não tem). Isso gera `config.json`.

3. Revise o `config.json` gerado. Ele começa com `"modo_simulacao": true`.

4. Rode o autoclicker:

   ```
   python autoclicker.py
   ```

5. Teste primeiro em modo simulação: pressione **F9** para armar, depois
   **F1**/**F2**/**F3**/**F4** (compra/venda/zerar/cancelar+zerar) e
   confira no terminal se ele "clicaria" nos pontos certos, na conta certa.

6. Só depois de validar, edite `config.json` e mude
   `"modo_simulacao"` para `false` para os cliques passarem a ser reais.

## Hotkeys padrão (editáveis em `config.json`)

| Tecla | Ação                         |
|-------|------------------------------|
| F1    | Compra em todas as contas    |
| F2    | Venda em todas as contas     |
| F3    | Zerar em todas as contas     |
| F4    | Cancelar ordens + zerar      |
| F9    | Armar / desarmar             |
| F12   | Sair                         |

O autoclicker sempre começa **desarmado**: hotkeys de ação são ignoradas até
você pressionar F9. Isso evita disparo acidental ao testar outras teclas.

## Segurança

- `pyautogui.FAILSAFE` está ativo: jogar o mouse pro canto superior esquerdo
  da tela em qualquer momento aborta a sequência de cliques em andamento.
- Há debounce de 0,5s por ação, pra segurar tecla pressionada não disparar
  clique repetido.
- Recomenda-se manter `Qtd` baixo (ex: 1) em todas as boletas ao testar.

## Licença (pra compartilhar com outra pessoa)

O `autoclicker.py` exige um `licenca.lic` válido pra rodar — amarrado ao PC
de destino e com data de validade. **Isso é uma trava simples (evita cópia
casual), não é proteção contra engenharia reversa avançada.**

Antes de gerar qualquer licença: troque o valor de `SEGREDO` em `licenca.py`
por algo só seu, e **nunca** compartilhe `licenca.py` nem `gerar_licenca.py`
com quem vai receber — só o `licenca.lic` gerado e o autoclicker (de
preferência já compilado, veja abaixo).

Passo a passo:

1. A pessoa que vai usar roda, na máquina dela:
   ```
   python obter_id_maquina.py
   ```
   e te manda o ID impresso.

2. Você (com `licenca.py` e `gerar_licenca.py` na sua máquina) roda:
   ```
   python gerar_licenca.py <id_que_ela_mandou> <AAAA-MM-DD>
   ```
   Isso gera `licenca.lic`, válido só pra aquele PC até aquela data.

3. Manda esse `licenca.lic` pra ela colocar na mesma pasta do autoclicker.

Sua própria máquina também precisa de um `licenca.lic` — rode
`obter_id_maquina.py` nela e gere a licença pra si mesmo do mesmo jeito.

### Compilando pra `.exe` (esconde o código-fonte)

Rode isso na própria máquina Windows onde vai gerar o executável final
(PyInstaller não faz cross-compile — rode no Windows pra gerar `.exe`):

```
pip install pyinstaller
pyinstaller --onefile --name Autoclicker autoclicker.py
```

O executável fica em `dist\Autoclicker.exe`. Distribua esse `.exe` junto
com `config.json` (já calibrado ou pra a pessoa calibrar com `calibrar.py`)
e o `licenca.lic` gerado pra ela. Não é preciso compilar `calibrar.py` —
ele não faz nenhuma checagem de licença nem tem nada sensível.
