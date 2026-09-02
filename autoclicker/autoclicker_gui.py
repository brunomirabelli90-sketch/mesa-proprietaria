"""
Interface grafica simples pro autoclicker: mesma logica de autoclicker.py
(mesmo config, mesmos hotkeys), so que com botoes clicaveis e status visivel
numa janela, alem dos hotkeys globais continuarem funcionando.

Uso:
    python autoclicker_gui.py [config1.json] [config2.json ...]

Se existir um perfis.json na pasta (gerado pelo botao "+ Novo perfil" da
propria interface), ele manda na lista de perfis em vez dos argumentos
acima - ver ARQUIVO_PERFIS mais abaixo.
"""
import json
import os
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog, ttk

import keyboard

import autoclicker as core
from licenca import validar_licenca

CAMINHO_ICONE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icone.ico")
ARQUIVO_PERFIS = "perfis.json"

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
    "apregoar_compra": "Apregoar Compra",
    "apregoar_venda": "Apregoar Venda",
    "armar_desarmar": "Armar / Desarmar",
    "trocar_perfil": "Trocar perfil",
    "alternar_modo_simulacao": "Modo Simulacao / Real",
}

# fallback pros hotkeys novos em configs antigos (calibrados antes dessa
# funcionalidade existir, que por isso nao tem essas chaves em "hotkeys").
HOTKEYS_PADRAO_EXTRAS = {
    "alternar_modo_simulacao": "f11",
    "apregoar_compra": "f5",
    "apregoar_venda": "f6",
}


def carregar_registro_perfis():
    """Le o perfis.json (lista de {"nome":..., "arquivo":...}). Devolve
    None se o arquivo nao existir - quem chama decide o fallback (argv ou
    o config.json padrao)."""
    if not os.path.exists(ARQUIVO_PERFIS):
        return None
    try:
        with open(ARQUIVO_PERFIS, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    return dados.get("perfis", [])


def salvar_registro_perfis(perfis):
    with open(ARQUIVO_PERFIS, "w", encoding="utf-8") as f:
        json.dump({"perfis": perfis}, f, indent=2, ensure_ascii=False)


class App:
    def __init__(self, root, entradas_perfis, motivo_licenca=""):
        self.root = root
        self.motivo_licenca = motivo_licenca
        root.title("Autoclicker multi-conta")
        root.configure(bg=COR_FUNDO)
        if os.path.exists(CAMINHO_ICONE):
            try:
                root.iconbitmap(CAMINHO_ICONE)
            except tk.TclError:
                pass

        core.carregar_perfis_nomeados(entradas_perfis)
        core.IMPRIMIR = self._log
        core.AO_DISPARAR = self._flash

        self._hotkey_handlers = {}  # acao -> handler do keyboard.add_hotkey

        topo_frame = tk.Frame(root, bg=COR_FUNDO)
        topo_frame.pack(fill="x", padx=10, pady=(10, 0))

        self.var_sempre_topo = tk.BooleanVar(value=False)
        tk.Checkbutton(
            topo_frame, text="Sempre no topo", variable=self.var_sempre_topo,
            command=self._alternar_sempre_topo, bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
            selectcolor=COR_PAINEL, activebackground=COR_FUNDO,
            activeforeground=COR_TEXTO, font=("Segoe UI", 9),
        ).pack(side="right")

        perfil_frame = tk.Frame(root, bg=COR_FUNDO)
        perfil_frame.pack(fill="x", padx=10, pady=(6, 0))
        tk.Label(
            perfil_frame, text="Perfil:", bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
            font=("Segoe UI", 9),
        ).pack(side="left")
        self.combo_perfil = ttk.Combobox(perfil_frame, state="readonly", width=22)
        self.combo_perfil.pack(side="left", padx=(4, 6))
        self.combo_perfil.bind("<<ComboboxSelected>>", self._ao_selecionar_perfil)
        tk.Button(
            perfil_frame, text="+ Novo perfil", bg=COR_PAINEL, fg=COR_TEXTO,
            activebackground="#242b3d", bd=0, relief="flat", cursor="hand2",
            font=("Segoe UI", 9), command=self.novo_perfil,
        ).pack(side="left")
        self._atualizar_lista_perfis()

        self.status = tk.Label(
            root, text="", justify="left", anchor="w",
            font=("Consolas", 10), padx=10, pady=8,
            bg=COR_PAINEL, fg=COR_TEXTO,
        )
        self.status.pack(fill="x", padx=10, pady=(4, 6))

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

        tk.Button(botoes, text="Apregoar Compra (F5)", width=17,
                  bg="#8a5a00", fg="white", activebackground="#a56d00",
                  command=lambda: self.disparar_apregoar("compra"), **self.estilo_botao
                  ).grid(row=3, column=0, padx=2, pady=2)
        tk.Button(botoes, text="Apregoar Venda (F6)", width=17,
                  bg="#155c33", fg="white", activebackground="#1c7141",
                  command=lambda: self.disparar_apregoar("venda"), **self.estilo_botao
                  ).grid(row=3, column=1, padx=2, pady=2)

        linha_extra = 4

        tk.Button(
            botoes, text="Modo Simulacao / Real (F11)", width=36,
            bg=COR_PAINEL, fg=COR_ACENTO, activebackground="#242b3d",
            command=self.alternar_modo, **self.estilo_botao,
        ).grid(row=linha_extra, column=0, columnspan=2, pady=(6, 0))
        linha_extra += 1

        tk.Button(
            botoes, text="Configuracoes (atalhos e tempos)", width=36,
            bg=COR_PAINEL, fg=COR_TEXTO_FRACO, activebackground="#242b3d",
            command=self.abrir_configuracoes, **self.estilo_botao,
        ).grid(row=linha_extra, column=0, columnspan=2, pady=(6, 0))
        linha_extra += 1

        tk.Button(
            botoes, text="Ver historico completo", width=17,
            bg=COR_PAINEL, fg=COR_TEXTO_FRACO, activebackground="#242b3d",
            command=self.ver_historico, **self.estilo_botao,
        ).grid(row=linha_extra, column=0, padx=2, pady=2)
        tk.Button(
            botoes, text="Resumo do historico", width=17,
            bg=COR_PAINEL, fg=COR_TEXTO_FRACO, activebackground="#242b3d",
            command=self.ver_resumo_historico, **self.estilo_botao,
        ).grid(row=linha_extra, column=1, padx=2, pady=2)

        self.log = scrolledtext.ScrolledText(
            root, width=64, height=18, font=("Consolas", 9),
            bg=COR_LOG_FUNDO, fg=COR_LOG_TEXTO, insertbackground=COR_LOG_TEXTO,
            bd=0, relief="flat",
        )
        self.log.pack(padx=10, pady=(6, 10))

        self._registrar_hotkeys()
        self._atualizar_status()
        self._agendar_verificacao_auto_desarme()

    def _alternar_sempre_topo(self):
        self.root.attributes("-topmost", self.var_sempre_topo.get())

    def _agendar_verificacao_auto_desarme(self):
        armado_antes = core.ARMADO
        core.verificar_auto_desarme()
        if armado_antes != core.ARMADO:
            self._atualizar_status()
        self.root.after(15000, self._agendar_verificacao_auto_desarme)

    def _flash(self):
        cor_original = self.status.cget("bg")

        def restaurar():
            self.status.config(bg=cor_original)

        self.status.config(bg=COR_ACENTO)
        self.root.after(150, restaurar)

    def ver_historico(self):
        caminho = os.path.abspath(core.CAMINHO_LOG)
        if not os.path.exists(caminho):
            messagebox.showinfo("Historico", "Ainda nao existe historico.log (nenhuma acao disparada armado).")
            return
        try:
            os.startfile(caminho)
        except AttributeError:
            subprocess.Popen(["xdg-open", caminho])

    def ver_resumo_historico(self):
        resumo = core.resumir_historico(core.CAMINHO_LOG)
        if not resumo:
            messagebox.showinfo("Resumo", "Ainda nao ha nada registrado no historico.log.")
            return

        janela = tk.Toplevel(self.root)
        janela.title("Resumo do historico")
        janela.configure(bg=COR_FUNDO)
        if os.path.exists(CAMINHO_ICONE):
            try:
                janela.iconbitmap(CAMINHO_ICONE)
            except tk.TclError:
                pass

        texto = scrolledtext.ScrolledText(
            janela, width=50, height=20, font=("Consolas", 9),
            bg=COR_LOG_FUNDO, fg=COR_LOG_TEXTO, bd=0, relief="flat",
        )
        texto.pack(padx=10, pady=10)

        por_conta_acao = {}
        for (acao, conta, resultado), qtd in sorted(resumo.items()):
            por_conta_acao.setdefault((acao, conta), {})[resultado] = qtd

        for (acao, conta), resultados in sorted(por_conta_acao.items()):
            partes = ", ".join(f"{r}: {q}" for r, q in resultados.items())
            texto.insert("end", f"[{acao}] {conta}: {partes}\n")

        total_geral = sum(resumo.values())
        texto.insert("end", f"\nTotal de eventos no log: {total_geral}\n")
        texto.config(state="disabled")

    def _log(self, texto):
        def inserir():
            self.log.insert("end", str(texto) + "\n")
            self.log.see("end")
        self.root.after(0, inserir)

    def _atualizar_status(self):
        config = core.config_atual()
        caminho_perfil = core.PERFIS[core.INDICE_PERFIL][0]
        contadores = " ".join(f"{a}={n}" for a, n in core.CONTADORES.items())
        texto = (
            f"Perfil: {core.nome_perfil(caminho_perfil)}\n"
            f"Armado: {'SIM' if core.ARMADO else 'nao'}    "
            f"Modo: {'SIMULACAO' if config.get('modo_simulacao', True) else 'REAL'}\n"
            f"Contas: {[b.get('nome') for b in config['boletas']]}\n"
            f"Disparos na sessao: {contadores}"
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

    def disparar_apregoar(self, direcao):
        core.executar_apregoar(direcao)
        self._atualizar_status()

    def trocar_perfil(self):
        core.trocar_perfil()
        self._atualizar_lista_perfis()
        self._atualizar_status()

    def _atualizar_lista_perfis(self):
        nomes = [core.nome_perfil(caminho) for caminho, _ in core.PERFIS]
        self.combo_perfil["values"] = nomes
        if nomes:
            self.combo_perfil.current(core.INDICE_PERFIL)

    def _ao_selecionar_perfil(self, event=None):
        indice = self.combo_perfil.current()
        if indice == core.INDICE_PERFIL:
            return
        core.selecionar_perfil(indice)
        self._atualizar_status()

    def novo_perfil(self):
        nome = simpledialog.askstring(
            "Novo perfil", "Nome do novo perfil (ex: Leilao, Apregoado):",
            parent=self.root,
        )
        if not nome or not nome.strip():
            return
        nome = nome.strip()
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", nome).strip("_").lower() or "perfil"
        caminho = f"config_{slug}.json"

        if os.path.exists(caminho):
            if not messagebox.askyesno(
                "Arquivo ja existe",
                f"Ja existe um '{caminho}'. Abrir a calibracao nele mesmo "
                "assim? (da pra adicionar/recalibrar contas sem apagar as "
                "que ja tem).",
            ):
                return

        try:
            processo = self._abrir_calibrador(caminho)
        except FileNotFoundError as e:
            messagebox.showerror("Calibrador nao encontrado", str(e))
            return

        self._log(f"Calibracao do perfil '{nome}' aberta numa janela separada "
                   f"({caminho}). Preencha ela e feche quando terminar.")

        def esperar():
            processo.wait()
            self.root.after(0, lambda: self._perfil_calibrado(nome, caminho))

        threading.Thread(target=esperar, daemon=True).start()

    def _abrir_calibrador(self, caminho_config):
        """Abre o calibrador (script ou exe compilado, dependendo de como o
        Autoclicker esta rodando) numa janela de console separada, apontado
        pro arquivo de config desse novo perfil."""
        if getattr(sys, "frozen", False):
            pasta_base = os.path.dirname(os.path.abspath(sys.argv[0]))
        else:
            pasta_base = os.path.dirname(os.path.abspath(__file__))

        flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

        if getattr(sys, "frozen", False):
            exe_calibrar = os.path.join(pasta_base, "Calibrar.exe")
            if not os.path.exists(exe_calibrar):
                raise FileNotFoundError(
                    f"'{exe_calibrar}' nao encontrado. Compile tambem o "
                    "calibrador (python -m PyInstaller --onefile --name "
                    "Calibrar calibrar.py) e deixe o Calibrar.exe na mesma "
                    "pasta do AutoclickerGUI.exe."
                )
            comando = [exe_calibrar, caminho_config]
        else:
            executavel = sys.executable
            if executavel.lower().endswith("pythonw.exe"):
                candidato = executavel[:-len("pythonw.exe")] + "python.exe"
                if os.path.exists(candidato):
                    executavel = candidato
            script_calibrar = os.path.join(pasta_base, "calibrar.py")
            if not os.path.exists(script_calibrar):
                raise FileNotFoundError(f"'{script_calibrar}' nao encontrado.")
            comando = [executavel, script_calibrar, caminho_config]

        return subprocess.Popen(comando, cwd=pasta_base, creationflags=flags)

    def _perfil_calibrado(self, nome, caminho):
        if not os.path.exists(caminho):
            self._log(f"Calibracao de '{nome}' fechada sem gerar '{caminho}' - "
                       "perfil nao adicionado.")
            return

        registro = carregar_registro_perfis()
        if registro is None:
            registro = [
                {"nome": core.nome_perfil(c), "arquivo": c} for c, _ in core.PERFIS
            ]
        registro = [p for p in registro if p.get("arquivo") != caminho]
        registro.append({"nome": nome, "arquivo": caminho})
        salvar_registro_perfis(registro)

        self._log(f"Perfil '{nome}' ({caminho}) calibrado e salvo em {ARQUIVO_PERFIS}.")
        messagebox.showinfo(
            "Perfil criado",
            f"Perfil '{nome}' calibrado e salvo.\n"
            "Feche e abra o Autoclicker de novo pra ele aparecer na lista de perfis.",
        )

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
        if acao.startswith("apregoar_"):
            direcao = acao.split("_", 1)[1]
            return lambda d=direcao: self.disparar_apregoar(d)
        return lambda a=acao: self.disparar(a)

    def _registrar_hotkeys(self):
        hotkeys = core.config_atual()["hotkeys"]

        for acao in ("compra", "venda", "zerar", "cancelar_zerar", "armar_desarmar",
                     "alternar_modo_simulacao", "apregoar_compra", "apregoar_venda"):
            tecla = hotkeys.get(acao) or HOTKEYS_PADRAO_EXTRAS.get(acao)
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
            tecla = hotkeys.get(acao) or HOTKEYS_PADRAO_EXTRAS.get(acao, "?")
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

        linha = len(acoes_visiveis) + 1
        tk.Frame(janela, bg=COR_TEXTO_FRACO, height=1).grid(
            row=linha, column=0, columnspan=3, sticky="ew", padx=10, pady=6
        )
        linha += 1

        config = core.config_atual()

        tk.Label(
            janela, text="Delay entre cliques (ms)", bg=COR_FUNDO, fg=COR_TEXTO,
            font=("Segoe UI", 10), anchor="w", width=22,
        ).grid(row=linha, column=0, padx=(10, 4), pady=3, sticky="w")
        var_delay = tk.StringVar(value=str(config.get("delay_entre_cliques_ms", 80)))
        tk.Entry(
            janela, textvariable=var_delay, width=8, bg=COR_PAINEL, fg=COR_ACENTO,
            insertbackground=COR_ACENTO, bd=0, font=("Consolas", 10),
        ).grid(row=linha, column=1, padx=4, pady=3)
        linha += 1

        tk.Label(
            janela, text="Auto-desarmar apos (min, 0=off)", bg=COR_FUNDO, fg=COR_TEXTO,
            font=("Segoe UI", 10), anchor="w", width=22,
        ).grid(row=linha, column=0, padx=(10, 4), pady=3, sticky="w")
        var_auto_desarme = tk.StringVar(value=str(config.get("auto_desarmar_minutos", 0)))
        tk.Entry(
            janela, textvariable=var_auto_desarme, width=8, bg=COR_PAINEL, fg=COR_ACENTO,
            insertbackground=COR_ACENTO, bd=0, font=("Consolas", 10),
        ).grid(row=linha, column=1, padx=4, pady=3)
        linha += 1

        def salvar_tempos():
            try:
                delay = int(var_delay.get())
                auto_desarme = float(var_auto_desarme.get())
            except ValueError:
                messagebox.showwarning("Valor invalido", "Delay e auto-desarme precisam ser numeros.")
                return
            config["delay_entre_cliques_ms"] = delay
            config["auto_desarmar_minutos"] = auto_desarme
            caminho_perfil = core.PERFIS[core.INDICE_PERFIL][0]
            core.salvar_config(caminho_perfil, config)
            self._log(f"Delay={delay}ms, auto-desarme={auto_desarme}min salvos.")

        tk.Button(
            janela, text="Salvar tempos", bg=COR_PAINEL, fg=COR_TEXTO,
            activebackground="#242b3d", bd=0, relief="flat", cursor="hand2",
            command=salvar_tempos,
        ).grid(row=linha, column=0, columnspan=3, pady=(4, 8))
        linha += 1

        tk.Button(
            janela, text="Fechar", bg=COR_PAINEL, fg=COR_TEXTO,
            activebackground="#242b3d", bd=0, relief="flat", cursor="hand2",
            command=janela.destroy,
        ).grid(row=linha, column=0, columnspan=3, pady=(0, 10))

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

    registro = carregar_registro_perfis()
    entradas = []
    if registro:
        entradas = [
            (p["nome"], p["arquivo"]) for p in registro
            if os.path.exists(p.get("arquivo", ""))
        ]
    if not entradas:
        caminhos_argv = sys.argv[1:]
        if caminhos_argv:
            entradas = [(os.path.splitext(os.path.basename(c))[0], c) for c in caminhos_argv]
        else:
            entradas = [("Padrão", "config.json")]

    root = tk.Tk()
    App(root, entradas, motivo_licenca=motivo)
    if "ATENCAO" in motivo:
        messagebox.showwarning("Licenca", motivo)
    root.mainloop()


if __name__ == "__main__":
    main()
