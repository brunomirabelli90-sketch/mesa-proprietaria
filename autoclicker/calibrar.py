"""
Calibrador de coordenadas para o autoclicker.

Uso:
    python calibrar.py

Para cada conta/botao pedido, posicione o mouse sobre o botao na tela
e pressione a tecla de captura (F8). O resultado e salvo em config.json.
"""
import json
import sys
import time

import keyboard
import pyautogui

TECLA_CAPTURA = "f8"
TECLA_PULAR = "f7"
BOTOES_PADRAO = ["compra", "venda", "zerar", "cancelar_zerar"]
DEBOUNCE_CAPTURA_S = 0.4

_ultima_captura_ts = 0.0


def capturar_posicao(rotulo):
    global _ultima_captura_ts
    print(f"  Posicione o mouse sobre '{rotulo}' e pressione "
          f"[{TECLA_CAPTURA.upper()}] para capturar (ou [{TECLA_PULAR.upper()}] para pular).")
    while True:
        evento = keyboard.read_event(suppress=False)
        # keyboard.read_key() tambem devolve o evento de soltar a tecla (e
        # possivel auto-repeat do Windows), o que fazia uma unica tecla
        # fisica contar como 2-3 capturas em sequencia. Aqui so reagimos
        # a tecla pressionada (KEY_DOWN) e ainda assim com debounce.
        if evento.event_type != keyboard.KEY_DOWN:
            continue
        if evento.name not in (TECLA_CAPTURA, TECLA_PULAR):
            continue

        agora = time.monotonic()
        if agora - _ultima_captura_ts < DEBOUNCE_CAPTURA_S:
            continue
        _ultima_captura_ts = agora

        if evento.name == TECLA_CAPTURA:
            x, y = pyautogui.position()
            print(f"    -> capturado em ({x}, {y})")
            return [x, y]
        print("    -> pulado")
        return None


def main():
    try:
        n_contas = int(input("Quantas contas/boletas vai calibrar? ").strip())
    except ValueError:
        print("Numero invalido.")
        sys.exit(1)

    boletas = []
    for i in range(1, n_contas + 1):
        nome = input(f"Nome da conta {i} (ex: Conta {i}): ").strip() or f"Conta {i}"
        print(f"\nCalibrando '{nome}'")
        botoes = {}
        for botao in BOTOES_PADRAO:
            pos = capturar_posicao(f"{nome} / {botao}")
            if pos is not None:
                botoes[botao] = pos
        boletas.append({"nome": nome, "botoes": botoes})

    config = {
        "modo_simulacao": True,
        "delay_entre_cliques_ms": 80,
        "hotkeys": {
            "compra": "f1",
            "venda": "f2",
            "zerar": "f3",
            "cancelar_zerar": "f4",
            "armar_desarmar": "f9",
            "sair": "f12",
        },
        "boletas": boletas,
    }

    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print("\nConfig salva em config.json (modo_simulacao=true por padrao).")
    print("Confira/ajuste o arquivo, teste com o autoclicker em modo simulacao,")
    print("e so depois mude modo_simulacao para false.")


if __name__ == "__main__":
    main()
