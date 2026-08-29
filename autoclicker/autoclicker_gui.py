"""
Interface grafica simples pro autoclicker: mesma logica de autoclicker.py
(mesmo config, mesmos hotkeys), so que com botoes clicaveis e status visivel
numa janela, alem dos hotkeys globais continuarem funcionando.

Uso:
    python autoclicker_gui.py [config1.json] [config2.json ...]
"""
import sys
import tkinter as tk
from tkinter import scrolledtext

import keyboard

import autoclicker as core
from licenca import validar_licenca


class App:
    def __init__(self, root, caminhos_config):
        self.root = root
        root.title("Autoclicker multi-conta")

        core.carregar_perfis(caminhos_config)
        core.IMPRIMIR = self._log

        self.status = tk.Label(root, text="", justify="left", anchor="w",
                                font=("Consolas", 10), padx=8, pady=4)
        self.status.pack(fill="x")

        botoes = tk.Frame(root)
        botoes.pack(padx=8, pady=4)

        self.btn_armar = tk.Button(botoes, text="Armar / Desarmar (F9)",
                                    width=36, command=self.armar)
        self.btn_armar.grid(row=0, column=0, columnspan=2, pady=4)

        tk.Button(botoes, text="Compra (F1)", width=17, bg="#f5a623",
                  command=lambda: self.disparar("compra")).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(botoes, text="Venda (F2)", width=17, bg="#2ecc71",
                  command=lambda: self.disparar("venda")).grid(row=1, column=1, padx=2, pady=2)
        tk.Button(botoes, text="Zerar (F3)", width=17, bg="#e74c3c", fg="white",
                  command=lambda: self.disparar("zerar")).grid(row=2, column=0, padx=2, pady=2)
        tk.Button(botoes, text="Cancelar+Zerar (F4)", width=17,
                  command=lambda: self.disparar("cancelar_zerar")).grid(row=2, column=1, padx=2, pady=2)

        if len(core.PERFIS) > 1:
            tk.Button(botoes, text="Trocar perfil (F10)", width=36,
                      command=self.trocar_perfil).grid(row=3, column=0, columnspan=2, pady=4)

        self.log = scrolledtext.ScrolledText(root, width=64, height=18, font=("Consolas", 9))
        self.log.pack(padx=8, pady=6)

        self._registrar_hotkeys()
        self._atualizar_status()

    def _log(self, texto):
        def inserir():
            self.log.insert("end", str(texto) + "\n")
            self.log.see("end")
        self.root.after(0, inserir)

    def _atualizar_status(self):
        config = core.config_atual()
        caminho_perfil = core.PERFIS[core.INDICE_PERFIL][0]
        texto = (
            f"Perfil: {caminho_perfil}\n"
            f"Armado: {'SIM' if core.ARMADO else 'nao'}    "
            f"Modo: {'SIMULACAO' if config.get('modo_simulacao', True) else 'REAL'}\n"
            f"Contas: {[b.get('nome') for b in config['boletas']]}"
        )
        self.status.config(text=texto)

    def armar(self):
        core.alternar_armado()
        self._atualizar_status()

    def disparar(self, acao):
        core.executar_acao(acao)
        self._atualizar_status()

    def trocar_perfil(self):
        core.trocar_perfil()
        self._atualizar_status()

    def _registrar_hotkeys(self):
        hotkeys = core.config_atual()["hotkeys"]

        for acao in ("compra", "venda", "zerar", "cancelar_zerar"):
            tecla = hotkeys.get(acao)
            if tecla:
                keyboard.add_hotkey(tecla, lambda a=acao: self.root.after(0, lambda: self.disparar(a)))

        keyboard.add_hotkey(hotkeys["armar_desarmar"], lambda: self.root.after(0, self.armar))

        if len(core.PERFIS) > 1:
            tecla_perfil = hotkeys.get("trocar_perfil", "f10")
            keyboard.add_hotkey(tecla_perfil, lambda: self.root.after(0, self.trocar_perfil))


def main():
    ok, motivo = validar_licenca()
    if not ok:
        print(f"Licenca: {motivo}")
        print("Autoclicker bloqueado.")
        sys.exit(1)

    caminhos = sys.argv[1:] if len(sys.argv) > 1 else ["config.json"]

    root = tk.Tk()
    App(root, caminhos)
    root.mainloop()


if __name__ == "__main__":
    main()
