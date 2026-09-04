"""
Painel do Filtro Macro pro leilao do mini indice (WINFUT): soma a variacao
de ativos que costumam puxar o Ibovespa/WIN (Petroleo, Minerio, S&P500) e
subtrai os "risk-off" (Dolar, VIX), virando um veredito de COMPRA/VENDA.

Uso:
    python painel_leilao.py

Nao depende mais de Excel/Profit/BlackArrow (essa parte foi removida por
ser instavel - "sempre bugava no Excel"). Todos os dados vem de fora,
via mercado_externo.py (VIX, Indice Dolar) e mercado_macro.py (Petroleo,
Minerio, e o resto que ja vinha de la).
"""
import os
import subprocess
import tkinter as tk
from tkinter import messagebox

import estrategia_leilao as estrategia
import historico_macro
import mercado_externo
import mercado_macro

CAMINHO_ICONE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icone.ico")

INTERVALO_ATUALIZACAO_MS = 1500

# Paleta escura "premium" - mesma linha visual do resto do projeto.
COR_FUNDO = "#0b0f14"
COR_PAINEL = "#161c26"
COR_TEXTO = "#e8edf2"
COR_TEXTO_FRACO = "#7c8a99"
COR_ACENTO = "#00d4ff"
COR_VERDE = "#1f8a4c"
COR_VERMELHO = "#c0392b"
COR_AMARELO = "#d4a017"
COR_CINZA = "#3a4552"

CORES_SINAL = {
    estrategia.COMPRA: COR_VERDE,
    estrategia.VENDA: COR_VERMELHO,
    estrategia.NEUTRO: COR_AMARELO,
    estrategia.SEM_DADO: COR_CINZA,
    None: COR_CINZA,
}


def formatar_variacao(valor):
    if valor is None:
        return "-", COR_TEXTO_FRACO
    cor = COR_VERDE if valor > 0 else (COR_VERMELHO if valor < 0 else COR_TEXTO_FRACO)
    sinal = "+" if valor > 0 else ""
    return f"{sinal}{valor:.2f}%", cor


class PainelLeilao:
    def __init__(self, root):
        self.root = root
        root.title("Painel BMT - Leilao")
        root.configure(bg=COR_FUNDO)
        if os.path.exists(CAMINHO_ICONE):
            try:
                root.iconbitmap(CAMINHO_ICONE)
            except tk.TclError:
                pass

        self._cache_dados = {}
        self._cache_resultado = {"score": None, "veredito": estrategia.SEM_DADO}

        cabecalho = tk.Frame(root, bg=COR_FUNDO)
        cabecalho.pack(fill="x", padx=16, pady=(16, 0))
        tk.Label(
            cabecalho, text="LEILÃO · FILTRO MACRO", font=("Segoe UI", 12, "bold"),
            bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
        ).pack(side="left")

        linha_live = tk.Frame(root, bg=COR_FUNDO)
        linha_live.pack(fill="x", padx=16, pady=(2, 8))
        self.var_modo_live = tk.BooleanVar(value=False)
        tk.Checkbutton(
            linha_live, text="Modo live (ocultar estratégia)",
            variable=self.var_modo_live, command=self._rerender,
            bg=COR_FUNDO, fg=COR_TEXTO_FRACO, selectcolor=COR_PAINEL,
            activebackground=COR_FUNDO, activeforeground=COR_TEXTO,
            font=("Segoe UI", 9),
        ).pack(side="right")

        # Badge grande com o veredito (COMPRA/VENDA/NEUTRO/AGUARDANDO)
        self.frame_badge = tk.Frame(root, bg=COR_CINZA, height=110)
        self.frame_badge.pack(fill="x", padx=16, pady=6)
        self.frame_badge.pack_propagate(False)
        self.lbl_sinal = tk.Label(
            self.frame_badge, text=estrategia.SEM_DADO, font=("Segoe UI", 30, "bold"),
            bg=COR_CINZA, fg="white",
        )
        self.lbl_sinal.pack(expand=True)

        # Score (detalhe do calculo do veredito acima)
        score_frame = tk.Frame(root, bg=COR_PAINEL)
        score_frame.pack(fill="x", padx=16, pady=(0, 12))
        self.lbl_score_macro = tk.Label(
            score_frame, text="Score: -", font=("Consolas", 12, "bold"),
            bg=COR_PAINEL, fg=COR_TEXTO, anchor="w",
        )
        self.lbl_score_macro.pack(side="left", padx=10, pady=8)

        # Separador
        tk.Frame(root, bg=COR_CINZA, height=1).pack(fill="x", padx=16)

        # "La fora" - ativos usados no score, mais os indices so informativos
        tk.Label(
            root, text="ATIVOS (informativo)", font=("Segoe UI", 10, "bold"),
            bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
        ).pack(anchor="w", padx=16, pady=(10, 4))

        externos_frame = tk.Frame(root, bg=COR_FUNDO)
        externos_frame.pack(fill="x", padx=16, pady=(0, 16))

        self.rotulos_indices = []  # (label_widget, texto_original)

        self.lbl_sp500 = self._criar_bloco_indice(externos_frame, "S&P 500", destaque=True)
        self.lbl_nasdaq = self._criar_bloco_indice(externos_frame, "Nasdaq")
        self.lbl_dow = self._criar_bloco_indice(externos_frame, "Dow Jones")

        externos_frame2 = tk.Frame(root, bg=COR_FUNDO)
        externos_frame2.pack(fill="x", padx=16, pady=(0, 16))

        self.lbl_vix = self._criar_bloco_indice(externos_frame2, "VIX")
        self.lbl_dxy = self._criar_bloco_indice(externos_frame2, "Índice Dólar")

        externos_frame3 = tk.Frame(root, bg=COR_FUNDO)
        externos_frame3.pack(fill="x", padx=16, pady=(0, 16))

        self.lbl_petroleo = self._criar_bloco_indice(externos_frame3, "Petróleo")
        self.lbl_minerio = self._criar_bloco_indice(externos_frame3, "Minério")

        # Botoes de historico ("banco de dados" das leituras)
        botoes_frame = tk.Frame(root, bg=COR_FUNDO)
        botoes_frame.pack(fill="x", padx=16, pady=(0, 16))
        self.estilo_botao = dict(
            font=("Segoe UI", 9, "bold"), bd=0, relief="flat", cursor="hand2",
        )
        tk.Button(
            botoes_frame, text="Salvar leitura", bg=COR_ACENTO, fg="#04141a",
            activebackground="#33dfff", command=self.salvar_leitura, **self.estilo_botao,
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))
        tk.Button(
            botoes_frame, text="Ver histórico", bg=COR_PAINEL, fg=COR_TEXTO,
            activebackground="#242b3d", command=self.ver_historico, **self.estilo_botao,
        ).pack(side="left", expand=True, fill="x", padx=(4, 0))

        mercado_externo.iniciar()
        mercado_macro.iniciar()
        self._agendar_atualizacao()

    def _criar_bloco_indice(self, container, nome, destaque=False):
        frame = tk.Frame(container, bg=COR_PAINEL)
        frame.pack(side="left", expand=True, fill="x", padx=(0, 8))
        lbl_nome = tk.Label(
            frame, text=nome, font=("Segoe UI", 9 if not destaque else 10, "bold"),
            bg=COR_PAINEL, fg=COR_TEXTO_FRACO,
        )
        lbl_nome.pack(pady=(8, 0))
        self.rotulos_indices.append((lbl_nome, nome))
        lbl = tk.Label(
            frame, text="-", font=("Consolas", 16 if destaque else 12, "bold"),
            bg=COR_PAINEL, fg=COR_TEXTO_FRACO,
        )
        lbl.pack(pady=(0, 8))
        return lbl

    def _agendar_atualizacao(self):
        self._atualizar()
        self.root.after(INTERVALO_ATUALIZACAO_MS, self._agendar_atualizacao)

    def _atualizar(self):
        dados = {}
        dados.update(mercado_externo.obter_ultimo())
        dados.update(mercado_macro.obter_ultimo())
        self._cache_dados = dados
        self._cache_resultado = estrategia.calcular_score_macro(
            petroleo=dados.get("petroleo"), minerio=dados.get("minerio"),
            dxy=dados.get("dxy"), vix=dados.get("vix"), sp500=dados.get("sp500"),
        )
        self._rerender()

    def _rerender(self):
        """Redesenha a tela com os ultimos dados lidos, respeitando o modo
        live (chamada tanto apos buscar dados novos quanto ao ligar/desligar
        o checkbox, pra reagir na hora sem esperar o proximo ciclo)."""
        self._atualizar_rotulos()
        self._atualizar_badge(self._cache_resultado)
        self._atualizar_indices(self._cache_dados)
        self._atualizar_score(self._cache_resultado)

    def _atualizar_rotulos(self):
        oculto = self.var_modo_live.get()
        for lbl, texto_original in self.rotulos_indices:
            lbl.config(text="•••" if oculto else texto_original)

    def _atualizar_badge(self, r):
        # o veredito final fica sempre visivel, inclusive no modo live - e'
        # o que faz sentido mostrar numa live. O que se esconde e' o "porque"
        # (os ativos e o score que embasam ele).
        veredito = r["veredito"]
        cor = CORES_SINAL.get(veredito, COR_CINZA)
        self.frame_badge.config(bg=cor)
        self.lbl_sinal.config(bg=cor, text=veredito)

    def _atualizar_indices(self, dados):
        blocos = (
            (self.lbl_sp500, "sp500"), (self.lbl_nasdaq, "nasdaq"), (self.lbl_dow, "dow"),
            (self.lbl_vix, "vix"), (self.lbl_dxy, "dxy"),
            (self.lbl_petroleo, "petroleo"), (self.lbl_minerio, "minerio"),
        )
        if self.var_modo_live.get():
            for lbl, _ in blocos:
                lbl.config(text="••••", fg=COR_TEXTO_FRACO)
            return

        for lbl, chave in blocos:
            texto, cor = formatar_variacao(dados.get(chave))
            lbl.config(text=texto, fg=cor)

    def _atualizar_score(self, r):
        if self.var_modo_live.get():
            self.lbl_score_macro.config(text="Score: ••••", fg=COR_TEXTO_FRACO)
            return
        texto_score, cor_score = formatar_variacao(r["score"])
        self.lbl_score_macro.config(text=f"Score: {texto_score}", fg=cor_score)

    def salvar_leitura(self):
        if self._cache_resultado.get("score") is None:
            if not messagebox.askyesno(
                "Sem dados ainda",
                "Ainda não tem nenhuma leitura completa (score em branco).\n"
                "Salvar assim mesmo (com os campos que já tiverem valor)?",
            ):
                return
        linha = historico_macro.salvar_leitura(self._cache_dados, self._cache_resultado)
        messagebox.showinfo(
            "Salvo",
            f"Leitura salva às {linha['data_hora']} em "
            f"{historico_macro.ARQUIVO_HISTORICO} (veredito: {linha['veredito']}).",
        )

    def ver_historico(self):
        caminho = os.path.abspath(historico_macro.ARQUIVO_HISTORICO)
        if not os.path.exists(caminho):
            messagebox.showinfo(
                "Histórico",
                "Ainda não tem nenhuma leitura salva - clica em 'Salvar leitura' primeiro.",
            )
            return
        try:
            os.startfile(caminho)
        except AttributeError:
            subprocess.Popen(["xdg-open", caminho])


def main():
    root = tk.Tk()
    root.geometry("440x680")
    root.resizable(False, False)
    PainelLeilao(root)
    root.mainloop()


if __name__ == "__main__":
    main()
