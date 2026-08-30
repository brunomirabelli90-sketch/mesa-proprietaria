"""
Interface grafica simples pro autoclicker: mesma logica de autoclicker.py
(mesmo config, mesmos hotkeys), so que com botoes clicaveis e status visivel
numa janela, alem dos hotkeys globais continuarem funcionando.

Uso:
    python autoclicker_gui.py [config1.json] [config2.json ...]
"""
import os
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext

import keyboard

import autoclicker as core
from licenca import validar_licenca

CAMINHO_ICONE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icone.ico")

# Paleta escura (mesma linha do meta_plano_risco.html do projeto).
COR_FUNDO = "#0f1419"
COR_PAINEL = "#1a1f2e"
COR_TEXTO = "#e0e0e0"
COR_TEXTO_FRACO = "#8ea0b5"
COR_ACENTO = "#00d4ff"
COR_LOG_FUNDO = "#05080c"
COR_LOG_TEXTO = "#00ff9d"

NOMES_ACAO = {
    "compra": "Compra",
    "venda": "Venda",
    "zerar": "Zerar",
    "cancelar_zerar": "Cancelar + Zerar",
    "armar_desarmar": "Armar / Desarmar",
    "trocar_perfil": "Trocar perfil",
    "alternar_modo_simulacao": "Modo Simulacao / Real",
}


class App:
    def __init__(self, root, caminhos_config, motivo_licenca=""):
        self.root = root
        self.motivo_licenca = motivo_licenca
        root.title("Autoclicker multi-conta")
        root.configure(bg=COR_FUNDO)
        if os.path.exists(CAMINHO_ICONE):
            try:
                root.iconbitmap(CAMINHO_ICONE)
            except tk.TclError:
                pass

        core.carregar_perfis(caminhos_config)
        core.IMPRIMIR = self._log

        self._hotkey_handlers = {}  # acao -> handler do keyboard.add_hotkey

        self.status = tk.Label(
            root, text="", justify="left", anchor="w",
            font=("Consolas", 10), padx=10, pady=8,
            bg=COR_PAINEL, fg=COR_TEXTO,
        )
        self.status.pack(fill="x", padx=10, pady=(10, 6))

        botoes = tk.Frame(root, bg=COR_FUNDO)
        botoes.pack(padx=10, pady=4)

        self.estilo_botao = dict(
            font=("Segoe UI", 10, "bold"), bd=0, relief="flat",
            activeforeground=COR_TEXTO, cursor="hand2",
        )

        self.btn_armar = tk.Button(
            botoes, text="Armar / Desarmar (F9)", width=36, height=1,
            bg=COR_PAINEL, fg=COR_ACENTO, activebackground="#242b3d",
            command=self.armar, **self.estilo_botao,
        )
        self.btn_armar.grid(row=0, column=0, columnspan=2, pady=(0, 6))

        tk.Button(botoes, text="Compra (F1)", width=17, bg="#cc7a00", fg="white",
                  activebackground="#e68a00",
                  command=lambda: self.disparar("compra"), **self.estilo_botao
                  ).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(botoes, text="Venda (F2)", width=17, bg="#1f8a4c", fg="white",
                  activebackground="#25a15a",
                  command=lambda: self.disparar("venda"), **self.estilo_botao
                  ).grid(row=1, column=1, padx=2, pady=2)
        tk.Button(botoes, text="Zerar (F3)", width=17, bg="#b03030", fg="white",
                  activebackground="#c93a3a",
                  command=lambda: self.disparar("zerar"), **self.estilo_botao
                  ).grid(row=2, column=0, padx=2, pady=2)
        tk.Button(botoes, text="Cancelar+Zerar (F4)", width=17,
                  bg=COR_PAINEL, fg=COR_TEXTO, activebackground="#242b3d",
                  command=lambda: self.disparar("cancelar_zerar"), **self.estilo_botao
                  ).grid(row=2, column=1, padx=2, pady=2)

        linha_extra = 3

        if len(core.PERFIS) > 1:
            tk.Button(
                botoes, text="Trocar perfil (F10)", width=36,
                bg=COR_PAINEL, fg=COR_ACENTO, activebackground="#242b3d",
                command=self.trocar_perfil, **self.estilo_botao,
            ).grid(row=linha_extra, column=0, columnspan=2, pady=(6, 0))
            linha_extra += 1

        tk.Button(
            botoes, text="Modo Simulacao / Real (F11)", width=36,
            bg=COR_PAINEL, fg=COR_ACENTO, activebackground="#242b3d",
            command=self.alternar_modo, **self.estilo_botao,
        ).grid(row=linha_extra, column=0, columnspan=2, pady=(6, 0))
        linha_extra += 1

        tk.Button(
            botoes, text="Configuracoes (atalhos)", width=36,
            bg=COR_PAINEL, fg=COR_TEXTO_FRACO, activebackground="#242b3d",
            command=self.abrir_configuracoes, **self.estilo_botao,
        ).grid(row=linha_extra, column=0, columnspan=2, pady=(6, 0))

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
        if "ATENCAO" in self.motivo_licenca:
            texto += f"\n{self.motivo_licenca}"
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

    def alternar_modo(self):
        core.alternar_modo_simulacao()
        self._atualizar_status()

    def _callback_para(self, acao):
        if acao == "armar_desarmar":
            return self.armar
        if acao == "alternar_modo_simulacao":
            return self.alternar_modo
        if acao == "trocar_perfil":
            return self.trocar_perfil
        return lambda a=acao: self.disparar(a)

    def _registrar_hotkeys(self):
        hotkeys = core.config_atual()["hotkeys"]

        for acao in ("compra", "venda", "zerar", "cancelar_zerar", "armar_desarmar",
                     "alternar_modo_simulacao"):
            tecla = hotkeys.get(acao) or ("f11" if acao == "alternar_modo_simulacao" else None)
            if tecla:
                self._vincular(acao, tecla)

        if len(core.PERFIS) > 1:
            tecla_perfil = hotkeys.get("trocar_perfil", "f10")
            self._vincular("trocar_perfil", tecla_perfil)

    def _vincular(self, acao, tecla):
        callback = self._callback_para(acao)
        handler = keyboard.add_hotkey(tecla, lambda: self.root.after(0, callback))
        self._hotkey_handlers[acao] = handler

    def _desvincular(self, acao):
        handler = self._hotkey_handlers.pop(acao, None)
        if handler is not None:
            try:
                keyboard.remove_hotkey(handler)
            except (KeyError, ValueError):
                pass

    def abrir_configuracoes(self):
        janela = tk.Toplevel(self.root)
        janela.title("Configuracoes - atalhos")
        janela.configure(bg=COR_FUNDO)
        if os.path.exists(CAMINHO_ICONE):
            try:
                janela.iconbitmap(CAMINHO_ICONE)
            except tk.TclError:
                pass

        tk.Label(
            janela, text="Clique em 'Alterar' e pressione a tecla nova.",
            bg=COR_FUNDO, fg=COR_TEXTO_FRACO, font=("Segoe UI", 9),
        ).grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 6), sticky="w")

        hotkeys = core.config_atual()["hotkeys"]
        acoes_visiveis = list(NOMES_ACAO.keys())
        if len(core.PERFIS) <= 1:
            acoes_visiveis.remove("trocar_perfil")

        self._labels_tecla = {}

        for i, acao in enumerate(acoes_visiveis, start=1):
            tecla = hotkeys.get(acao, "f11" if acao == "alternar_modo_simulacao" else "?")
            tk.Label(
                janela, text=NOMES_ACAO[acao], bg=COR_FUNDO, fg=COR_TEXTO,
                font=("Segoe UI", 10), anchor="w", width=22,
            ).grid(row=i, column=0, padx=(10, 4), pady=3, sticky="w")

            lbl_tecla = tk.Label(
                janela, text=tecla.upper(), bg=COR_PAINEL, fg=COR_ACENTO,
                font=("Consolas", 10, "bold"), width=8,
            )
            lbl_tecla.grid(row=i, column=1, padx=4, pady=3)
            self._labels_tecla[acao] = lbl_tecla

            tk.Button(
                janela, text="Alterar", bg=COR_PAINEL, fg=COR_TEXTO,
                activebackground="#242b3d", bd=0, relief="flat", cursor="hand2",
                command=lambda a=acao, lbl=lbl_tecla: self._capturar_tecla(janela, a, lbl),
            ).grid(row=i, column=2, padx=(4, 10), pady=3)

        tk.Button(
            janela, text="Fechar", bg=COR_PAINEL, fg=COR_TEXTO,
            activebackground="#242b3d", bd=0, relief="flat", cursor="hand2",
            command=janela.destroy,
        ).grid(row=len(acoes_visiveis) + 1, column=0, columnspan=3, pady=(8, 10))

    def _capturar_tecla(self, janela, acao, lbl_tecla):
        texto_original = lbl_tecla.cget("text")
        lbl_tecla.config(text="...", fg=COR_TEXTO_FRACO)
        janela.focus_force()

        def ao_pressionar(event):
            janela.unbind("<KeyPress>")
            nova_tecla = event.keysym.lower()

            hotkeys = core.config_atual()["hotkeys"]
            conflito = next(
                (a for a, t in hotkeys.items() if t == nova_tecla and a != acao), None
            )
            if conflito:
                messagebox.showwarning(
                    "Tecla em uso",
                    f"'{nova_tecla.upper()}' ja esta em uso por '{NOMES_ACAO.get(conflito, conflito)}'.",
                )
                lbl_tecla.config(text=texto_original, fg=COR_ACENTO)
                return

            self._desvincular(acao)
            hotkeys[acao] = nova_tecla
            caminho_perfil = core.PERFIS[core.INDICE_PERFIL][0]
            core.salvar_config(caminho_perfil, core.config_atual())
            self._vincular(acao, nova_tecla)

            lbl_tecla.config(text=nova_tecla.upper(), fg=COR_ACENTO)
            self._log(f"Atalho de '{NOMES_ACAO.get(acao, acao)}' alterado para {nova_tecla.upper()}.")

        janela.bind("<KeyPress>", ao_pressionar)


def main():
    ok, motivo = validar_licenca()

    if not ok:
        # console pode estar escondido (pythonw/--windowed), entao o aviso
        # precisa aparecer numa janela, nao so no terminal.
        root_erro = tk.Tk()
        root_erro.withdraw()
        messagebox.showerror("Autoclicker bloqueado", motivo)
        sys.exit(1)

    caminhos = sys.argv[1:] if len(sys.argv) > 1 else ["config.json"]

    root = tk.Tk()
    App(root, caminhos, motivo_licenca=motivo)
    if "ATENCAO" in motivo:
        messagebox.showwarning("Licenca", motivo)
    root.mainloop()


if __name__ == "__main__":
    main()
