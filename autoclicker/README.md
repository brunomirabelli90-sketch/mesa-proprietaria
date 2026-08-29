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
| F10   | Trocar perfil (só com múltiplos configs) |
| F11   | Alternar modo simulação / real |
| F12   | Sair                         |

O autoclicker sempre começa **desarmado**: hotkeys de ação são ignoradas até
você pressionar F9. Isso evita disparo acidental ao testar outras teclas.

## Segurança

- `pyautogui.FAILSAFE` está ativo: jogar o mouse pro canto superior esquerdo
  da tela em qualquer momento aborta a sequência de cliques em andamento.
- Há debounce de 0,5s por ação, pra segurar tecla pressionada não disparar
  clique repetido.
- Recomenda-se manter `Qtd` baixo (ex: 1) em todas as boletas ao testar.

## Histórico de cliques

Toda ação disparada (real ou simulada, inclusive as puladas por não bater a
cor) é registrada com data/hora em `historico.log`, na mesma pasta. Formato:

```
2026-08-29 14:32:10  [compra] Conta1: CLICADO em (2068, 235)
2026-08-29 14:32:10  [compra] Conta2: PULADO (cor nao bate em 2408,245)
```

Esse arquivo só cresce (nunca é apagado automaticamente) — pode abrir com
qualquer editor de texto pra conferir o que foi disparado e quando.

## Verificação de cor antes de clicar

`calibrar.py` já grava a cor do pixel de cada botão no momento da captura.
Pra ativar a verificação, no `config.json`:

```json
"verificar_cor": true,
"tolerancia_cor": 30
```

Com isso ligado (e fora do modo simulação), antes de cada clique real o
autoclicker confere se a cor daquele ponto na tela ainda bate com a
capturada na calibração (dentro da tolerância, por canal RGB). Se mudou
demais — janela moveu, mudou de leilão pra normal, tema mudou — ele **pula
aquele clique** em vez de arriscar clicar no lugar errado, e registra o
motivo no `historico.log`. `tolerancia_cor` maior = mais permissivo; muito
baixo pode gerar falso positivo (pular clique válido) se a cor piscar/mudar
levemente (ex: seleção, hover).

Configs antigos (sem essa checagem) continuam funcionando normalmente —
`verificar_cor` é `false` por padrão.

## Perfis (ex: layout normal vs. layout de leilão)

Se o layout das boletas muda em algum momento do dia (o Profit costuma
empurrar a boleta pra baixo durante o leilão), calibre um `config.json`
separado pra cada situação e rode o autoclicker apontando pros dois:

```
python autoclicker.py config_normal.json config_leilao.json
```

Com mais de um config na linha de comando, a hotkey **F10** (`trocar_perfil`
no `config.json`) alterna entre eles em tempo real, sem fechar o programa —
o terminal mostra qual perfil ficou ativo e as contas dele.

## Interface gráfica (opcional)

Além do modo terminal, tem uma janela simples com botões, pros mesmos
hotkeys (F1-F4, F9, F10) e um log visível na tela — útil pra quem não quer
ficar olhando texto em janela preta:

```
python autoclicker_gui.py [config1.json] [config2.json ...]
```

Mesmas regras de licença, modo simulação, armar/desarmar e perfis do modo
terminal — só muda a apresentação.

## Som de confirmação

Toda vez que uma ação é disparada com sucesso (armado, real ou simulação),
toca um beep curto (`winsound.Beep`) — ajuda a perceber que disparou sem
precisar ficar olhando a tela o tempo todo.

## Alternar simulação / real sem editar o arquivo

Em vez de abrir o `config.json` no Bloco de Notas toda vez, a hotkey **F11**
(`alternar_modo_simulacao`) troca `modo_simulacao` entre `true`/`false` na
hora, já salvando no arquivo. Na interface gráfica tem um botão pra isso
também. O terminal (ou o log da janela) mostra pra qual modo mudou.

## Licença (pra compartilhar com outra pessoa)

O `autoclicker.py` exige um `licenca.lic` válido pra rodar — amarrado ao PC
de destino e com data de validade. **Isso é uma trava simples (evita cópia
casual), não é proteção contra engenharia reversa avançada.**

Faltando 3 dias ou menos pra expirar, a mensagem de licença já vem com um
aviso (`ATENCAO: expira em N dia(s)!`) — aparece no terminal, no painel da
interface gráfica, e como um popup ao abrir o `autoclicker_gui.py`. Se já
expirou, o programa bloqueia como sempre.

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
pyinstaller --onefile --icon=icone.ico --name Autoclicker autoclicker.py
```

O executável fica em `dist\Autoclicker.exe`, já com o ícone `icone.ico` do
projeto. Distribua esse `.exe` junto com `config.json` (já calibrado ou pra
a pessoa calibrar com `calibrar.py`) e o `licenca.lic` gerado pra ela. Não é
preciso compilar `calibrar.py` — ele não faz nenhuma checagem de licença
nem tem nada sensível.

Pra compilar a versão com interface gráfica também (mesmo ícone, e
`--windowed` pra não abrir uma janela de console preta atrás do painel):
```
pyinstaller --onefile --windowed --icon=icone.ico --name AutoclickerGUI autoclicker_gui.py
```

Rodando direto com `python autoclicker_gui.py` (sem compilar), o console
também some usando `abrir_autoclicker_gui.bat` — ele chama `pythonw` (a
versão do Python sem janela de console) em vez de `python`.

### Ícone no atalho do `.bat`

Os lançadores `abrir_autoclicker.bat` / `abrir_autoclicker_gui.bat` não
carregam ícone próprio (arquivo `.bat` sempre usa o ícone do terminal). Pra
usar o `icone.ico` num atalho: cria um atalho do `.bat` (botão direito →
Enviar para → Área de trabalho), depois botão direito no atalho →
Propriedades → **Alterar Ícone** → aponta pra `icone.ico`.
