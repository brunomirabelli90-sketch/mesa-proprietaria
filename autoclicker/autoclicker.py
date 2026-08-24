"""
Autoclicker visual multi-conta.

Le config.json e registra hotkeys globais. Ao pressionar uma hotkey de acao
(compra/venda/zerar/cancelar_zerar), clica no botao correspondente de cada
conta cadastrada, na ordem em que aparecem no config.

Uso:
    python autoclicker.py [caminho_config.json]

Seguranca:
- Comeca DESARMADO. Pressione a hotkey 'armar_desarmar' (padrao F9) para
  armar antes de qualquer acao funcionar.
- modo_simulacao=true no config faz o script so imprimir o que faria,
  sem clicar de verdade. Use isso para validar a calibracao primeiro.
- pyautogui.FAILSAFE fica ligado: jogar o mouse para o canto superior
  esquerdo da tela aborta a acao em andamento.
"""
import json
import sys
import time

import keyboard
import pyautogui

from licenca import validar_licenca

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

ARMADO = False
ULTIMO_DISPARO = {}
DEBOUNCE_S = 0.5


def carregar_config(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def pode_disparar(acao):
    agora = time.monotonic()
    ultimo = ULTIMO_DISPARO.get(acao, 0)
    if agora - ultimo < DEBOUNCE_S:
        return False
    ULTIMO_DISPARO[acao] = agora
    return True


def executar_acao(acao, config):
    global ARMADO

    if not pode_disparar(acao):
        return

    if not ARMADO:
        print(f"[{acao}] ignorado: autoclicker desarmado (pressione "
              f"{config['hotkeys']['armar_desarmar'].upper()} para armar).")
        return

    simulacao = config.get("modo_simulacao", True)
    delay_s = config.get("delay_entre_cliques_ms", 80) / 1000.0

    print(f"[{acao}] disparando em {len(config['boletas'])} conta(s) "
          f"({'SIMULACAO' if simulacao else 'REAL'})...")

    for boleta in config["boletas"]:
        nome = boleta.get("nome", "?")
        pos = boleta.get("botoes", {}).get(acao)
        if pos is None:
            print(f"  - {nome}: sem coordenada cadastrada para '{acao}', pulando.")
            continue

        x, y = pos
        if simulacao:
            print(f"  - {nome}: clicaria em ({x}, {y})")
        else:
            pyautogui.click(x, y)
            print(f"  - {nome}: clicado em ({x}, {y})")

        time.sleep(delay_s)


def alternar_armado(config):
    global ARMADO
    ARMADO = not ARMADO
    estado = "ARMADO" if ARMADO else "desarmado"
    print(f"\n*** Autoclicker {estado} ***\n")


def main():
    ok, motivo = validar_licenca()
    print(f"Licenca: {motivo}")
    if not ok:
        print("Autoclicker bloqueado.")
        sys.exit(1)

    caminho_config = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    config = carregar_config(caminho_config)
    hotkeys = config["hotkeys"]

    print("Autoclicker carregado.")
    print(f"Contas configuradas: {[b.get('nome') for b in config['boletas']]}")
    print(f"Modo simulacao: {config.get('modo_simulacao', True)}")
    print("Hotkeys:")
    for acao, tecla in hotkeys.items():
        print(f"  {tecla.upper():>6}  ->  {acao}")
    print(f"\nComecando DESARMADO. Pressione {hotkeys['armar_desarmar'].upper()} para armar.\n")

    for acao in ("compra", "venda", "zerar", "cancelar_zerar"):
        tecla = hotkeys.get(acao)
        if tecla:
            keyboard.add_hotkey(tecla, executar_acao, args=(acao, config))

    keyboard.add_hotkey(hotkeys["armar_desarmar"], alternar_armado, args=(config,))

    print(f"Pressione {hotkeys['sair'].upper()} para sair.")
    keyboard.wait(hotkeys["sair"])
    print("Encerrado.")


if __name__ == "__main__":
    main()
