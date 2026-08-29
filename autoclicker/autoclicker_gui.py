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

# Paleta escura (mesma linha do meta_plano_risco.html do projeto).
COR_FUNDO = "#0f1419"
COR_PAINEL = "#1a1f2e"
COR_TEXTO = "#e0e0e0"
COR_TEXTO_FRACO = "#8ea0b5"
COR_ACENTO = "#00d4ff"
COR_LOG_FUNDO = "#05080c"
COR_LOG_TEXTO = "#00ff9d"


class App:
    def __init__(self, root, caminhos_config):
        self.root = root
        root.title("Autoclicker multi-conta")
        root.configure(bg=COR_FUNDO)

        core.carregar_perfis(caminhos_config)
        core.IMPRIMIR = self._log

        self.status = tk.Label(
            root, text="", justify="left", anchor="w",
            font=("Consolas", 10), padx=10, pady=8,
            bg=COR_PAINEL, fg=COR_TEXTO,
        )
        self.status.pack(fill="x", padx=10, pady=(10, 6))

        botoes = tk.Frame(root, bg=COR_FUNDO)
        botoes.pack(padx=10, pady=4)

        estilo_botao = dict(
            font=("Segoe UI", 10, "bold"), bd=0, relief="flat",
            activeforeground=COR_TEXTO, cursor="hand2",
        )

        self.btn_armar = tk.Button(
            botoes, text="Armar / Desarmar (F9)", width=36, height=1,
            bg=COR_PAINEL, fg=COR_ACENTO, activebackground="#242b3d",
            command=self.armar, **estilo_botao,
        )
        self.btn_armar.grid(row=0, column=0, columnspan=2, pady=(0, 6))

        tk.Button(botoes, text="Compra (F1)", width=17, bg="#cc7a00", fg="white",
                  activebackground="#e68a00",
                  command=lambda: self.disparar("compra"), **estilo_botao
                  ).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(botoes, text="Venda (F2)", width=17, bg="#1f8a4c", fg="white",
                  activebackground="#25a15a",
                  command=lambda: self.disparar("venda"), **estilo_botao
                  ).grid(row=1, column=1, padx=2, pady=2)
        tk.Button(botoes, text="Zerar (F3)", width=17, bg="#b03030", fg="white",
                  activebackground="#c93a3a",
                  command=lambda: self.disparar("zerar"), **estilo_botao
                  ).grid(row=2, column=0, padx=2, pady=2)
        tk.Button(botoes, text="Cancelar+Zerar (F4)", width=17,
                  bg=COR_PAINEL, fg=COR_TEXTO, activebackground="#242b3d",
                  command=lambda: self.disparar("cancelar_zerar"), **estilo_botao
                  ).grid(row=2, column=1, padx=2, pady=2)

        if len(core.PERFIS) > 1:
            tk.Button(
                botoes, text="Trocar perfil (F10)", width=36,
                bg=COR_PAINEL, fg=COR_ACENTO, activebackground="#242b3d",
                command=self.trocar_perfil, **estilo_botao,
            ).grid(row=3, column=0, columnspan=2, pady=(6, 0))

        self.log = scrolledtext.ScrolledText(
            root, width=64, height=18, font=("Consolas", 9),
            bg=COR_LOG_FUNDO, fg=COR_LOG_TEXTO, insertbackground=COR_LOG_TEXTO,
            bd=0, relief="flat",
        )
        self.log.pack(padx=10, pady=(6, 10))

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
