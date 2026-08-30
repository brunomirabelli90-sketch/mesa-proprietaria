"""
Calibrador de coordenadas para o autoclicker.

Uso:
    python calibrar.py

Para cada conta/botao pedido, posicione o mouse sobre o botao na tela
e pressione a tecla de captura (F8). O resultado e salvo em config.json.
"""
import json
import os
import sys
import time

import keyboard
import pyautogui

TECLA_CAPTURA = "f8"
TECLA_PULAR = "f7"
BOTOES_PADRAO = ["compra", "venda", "zerar", "cancelar_zerar"]
DEBOUNCE_CAPTURA_S = 0.4
ARQUIVO_CONFIG = "config.json"

_ultima_captura_ts = 0.0


def _esperar_tecla_captura_ou_pular():
    global _ultima_captura_ts
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
        return evento.name


def capturar_posicao(rotulo):
    while True:
        print(f"  Posicione o mouse sobre '{rotulo}' e pressione "
              f"[{TECLA_CAPTURA.upper()}] para capturar (ou [{TECLA_PULAR.upper()}] para pular).")
        tecla = _esperar_tecla_captura_ou_pular()

        if tecla == TECLA_PULAR:
            print("    -> pulado")
            return None

        x, y = pyautogui.position()
        resp = input(f"    -> capturado em ({x}, {y}). ENTER confirma, "
                      "'r' + ENTER refaz este ponto: ").strip().lower()
        if resp == "r":
            print("    -> refazendo esse botao...")
            continue
        try:
            cor = list(pyautogui.pixel(x, y))
        except Exception:
            cor = None
        return {"pos": [x, y], "cor": cor}


def calibrar_contas(n_contas, inicio=1):
    boletas = []
    for i in range(inicio, inicio + n_contas):
        nome = input(f"Nome da conta {i} (ex: Conta {i}): ").strip() or f"Conta {i}"
        print(f"\nCalibrando '{nome}'")
        botoes = {}
        for botao in BOTOES_PADRAO:
            pos = capturar_posicao(f"{nome} / {botao}")
            if pos is not None:
                botoes[botao] = pos
        boletas.append({"nome": nome, "botoes": botoes})
    return boletas


def config_padrao(boletas):
    return {
        "modo_simulacao": True,
        "verificar_cor": False,
        "tolerancia_cor": 30,
        "delay_entre_cliques_ms": 80,
        "hotkeys": {
            "compra": "f1",
            "venda": "f2",
            "zerar": "f3",
            "cancelar_zerar": "f4",
            "armar_desarmar": "f9",
            "trocar_perfil": "f10",
            "alternar_modo_simulacao": "f11",
            "sair": "f12",
        },
        "boletas": boletas,
    }


def recalibrar_uma_conta(config_existente):
    boletas = config_existente["boletas"]
    nomes = [b.get("nome") for b in boletas]
    print("Contas existentes:")
    for i, nome in enumerate(nomes, start=1):
        print(f"  {i}. {nome}")

    escolha = input("Qual conta recalibrar (numero ou nome)? ").strip()
    indice = None
    if escolha.isdigit() and 1 <= int(escolha) <= len(boletas):
        indice = int(escolha) - 1
    elif escolha in nomes:
        indice = nomes.index(escolha)

    if indice is None:
        print("Conta nao encontrada.")
        sys.exit(1)

    nome = nomes[indice]
    print(f"\nRecalibrando '{nome}'")
    botoes = {}
    for botao in BOTOES_PADRAO:
        pos = capturar_posicao(f"{nome} / {botao}")
        if pos is not None:
            botoes[botao] = pos
    boletas[indice]["botoes"] = botoes

    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config_existente, f, indent=2, ensure_ascii=False)
    print(f"\n{ARQUIVO_CONFIG} atualizado - '{nome}' recalibrada, as demais contas ficaram como estavam.")


def main():
    config_existente = None
    if os.path.exists(ARQUIVO_CONFIG):
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            config_existente = json.load(f)
        nomes = [b.get("nome") for b in config_existente.get("boletas", [])]
        print(f"Ja existe um {ARQUIVO_CONFIG} com {len(nomes)} conta(s): {nomes}")
        resp = input(
            "Adicionar novas contas a ele (a), recalibrar uma conta existente (r) "
            "ou comecar do zero (z)? [a/r/z]: "
        ).strip().lower()

        if resp == "r":
            recalibrar_uma_conta(config_existente)
            return

        if resp != "z":
            try:
                n_novas = int(input("Quantas contas novas vai calibrar? ").strip())
            except ValueError:
                print("Numero invalido.")
                sys.exit(1)
            novas_boletas = calibrar_contas(n_novas, inicio=len(nomes) + 1)
            config_existente["boletas"].extend(novas_boletas)
            with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
                json.dump(config_existente, f, indent=2, ensure_ascii=False)
            print(f"\n{ARQUIVO_CONFIG} atualizado, agora com "
                  f"{len(config_existente['boletas'])} conta(s).")
            return

    try:
        n_contas = int(input("Quantas contas/boletas vai calibrar? ").strip())
    except ValueError:
        print("Numero invalido.")
        sys.exit(1)

    boletas = calibrar_contas(n_contas)
    config = config_padrao(boletas)

    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\nConfig salva em {ARQUIVO_CONFIG} (modo_simulacao=true por padrao).")
    print("Confira/ajuste o arquivo, teste com o autoclicker em modo simulacao,")
    print("e so depois mude modo_simulacao para false.")


if __name__ == "__main__":
    main()
