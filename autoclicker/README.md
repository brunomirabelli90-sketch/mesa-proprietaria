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
