"""
Painel do leilao do mini indice (WINFUT): mostra em tempo real se o gap
favorece compra ou venda, com base no Excel ligado por RTD no Profit
(WINFUT) e no BlackArrow (indices internacionais).

Uso:
    python painel_leilao.py

Requisitos: o Excel "Painel BMT Leilao.xlsx" (ou o nome passado em
excel_leitor.NOME_ARQUIVO) precisa estar ABERTO, com as formulas RTD já
coladas (ver README.md pra montar isso).
"""
import os
import tkinter as tk

import excel_leitor
import estrategia_leilao as estrategia

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


def formatar_gap(gap):
    if gap is None:
        return "-"
    sinal = "+" if gap > 0 else ""
    return f"{sinal}{gap:.0f} pts"


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

        self.workbook = None
        self._cache_dados = None
        self._cache_resultado = None

        cabecalho = tk.Frame(root, bg=COR_FUNDO)
        cabecalho.pack(fill="x", padx=16, pady=(16, 0))
        tk.Label(
            cabecalho, text="WINFUT · LEILÃO", font=("Segoe UI", 12, "bold"),
            bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
        ).pack(side="left")
        self.lbl_status_conexao = tk.Label(
            cabecalho, text="conectando...", font=("Segoe UI", 9),
            bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
        )
        self.lbl_status_conexao.pack(side="right")

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

        # Badge grande com o sinal
        self.frame_badge = tk.Frame(root, bg=COR_CINZA, height=110)
        self.frame_badge.pack(fill="x", padx=16, pady=6)
        self.frame_badge.pack_propagate(False)
        self.lbl_sinal = tk.Label(
            self.frame_badge, text="AGUARDANDO", font=("Segoe UI", 30, "bold"),
            bg=COR_CINZA, fg="white",
        )
        self.lbl_sinal.pack(expand=True)

        # Dados do gap
        dados_frame = tk.Frame(root, bg=COR_PAINEL)
        dados_frame.pack(fill="x", padx=16, pady=6)

        self.linhas_dados = {}
        for i, (chave, rotulo) in enumerate([
            ("fechamento", "Fechamento Anterior"),
            ("ajuste", "Aj. Anterior"),
            ("teorico", "Preço Teórico"),
            ("gap_fechamento", "Gap (vs Fechamento)"),
            ("gap_ajuste", "Gap (vs Ajuste)"),
        ]):
            tk.Label(
                dados_frame, text=rotulo, font=("Segoe UI", 10),
                bg=COR_PAINEL, fg=COR_TEXTO_FRACO, anchor="w", width=22,
            ).grid(row=i, column=0, sticky="w", padx=(10, 4), pady=3)
            lbl_valor = tk.Label(
                dados_frame, text="-", font=("Consolas", 11, "bold"),
                bg=COR_PAINEL, fg=COR_TEXTO, anchor="e", width=14,
            )
            lbl_valor.grid(row=i, column=1, sticky="e", padx=(4, 10), pady=3)
            self.linhas_dados[chave] = lbl_valor

        # Confirmacao do ajuste
        self.lbl_confirmacao = tk.Label(
            root, text="", font=("Segoe UI", 10, "italic"),
            bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
        )
        self.lbl_confirmacao.pack(fill="x", padx=16, pady=(2, 8))

        # Separador
        tk.Frame(root, bg=COR_CINZA, height=1).pack(fill="x", padx=16)

        # "La fora"
        tk.Label(
            root, text="LÁ FORA (informativo)", font=("Segoe UI", 10, "bold"),
            bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
        ).pack(anchor="w", padx=16, pady=(10, 4))

        externos_frame = tk.Frame(root, bg=COR_FUNDO)
        externos_frame.pack(fill="x", padx=16, pady=(0, 16))

        self.lbl_sp500 = self._criar_bloco_indice(externos_frame, "S&P 500", destaque=True)
        self.lbl_nasdaq = self._criar_bloco_indice(externos_frame, "Nasdaq")
        self.lbl_dow = self._criar_bloco_indice(externos_frame, "Dow Jones")

        self._agendar_atualizacao()

    def _criar_bloco_indice(self, container, nome, destaque=False):
        frame = tk.Frame(container, bg=COR_PAINEL)
        frame.pack(side="left", expand=True, fill="x", padx=(0, 8))
        tk.Label(
            frame, text=nome, font=("Segoe UI", 9 if not destaque else 10, "bold"),
            bg=COR_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(pady=(8, 0))
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
        if self.workbook is None:
            self.workbook = excel_leitor.conectar_workbook()

        if self.workbook is None:
            self.lbl_status_conexao.config(text="⚠ Excel não encontrado", fg=COR_AMARELO)
            return

        dados = excel_leitor.ler_dados(self.workbook)
        if dados is None:
            self.lbl_status_conexao.config(text="⚠ perdeu conexão, tentando de novo...", fg=COR_AMARELO)
            self.workbook = None
            return

        self.lbl_status_conexao.config(text="● conectado", fg=COR_VERDE)

        resultado = estrategia.calcular_sinal(
            dados["fechamento"], dados["ajuste"], dados["teorico"]
        )
        self._cache_dados = dados
        self._cache_resultado = resultado
        self._rerender()

    def _rerender(self):
        """Redesenha a tela com os ultimos dados lidos, respeitando o modo
        live (chamada tanto apos ler o Excel quanto ao ligar/desligar o
        checkbox, pra reagir na hora sem esperar o proximo ciclo)."""
        if self._cache_resultado is not None:
            self._atualizar_badge(self._cache_resultado)
        if self._cache_dados is not None and self._cache_resultado is not None:
            self._atualizar_dados(self._cache_dados, self._cache_resultado)
            self._atualizar_indices(self._cache_dados)

    def _atualizar_badge(self, r):
        # o sinal final fica sempre visivel, inclusive no modo live - e'
        # o que o Bruno quer mostrar; o que se esconde e' o "porque".
        sinal = r["sinal_base"] or r["status"]
        cor = CORES_SINAL.get(sinal, COR_CINZA)
        self.frame_badge.config(bg=cor)
        self.lbl_sinal.config(bg=cor, text=sinal)

        if self.var_modo_live.get():
            self.lbl_confirmacao.config(text="", fg=COR_TEXTO_FRACO)
            return

        if r["confirma"] is True:
            self.lbl_confirmacao.config(
                text="✓ Ajuste confirma a mesma direção.", fg=COR_VERDE
            )
        elif r["confirma"] is False:
            self.lbl_confirmacao.config(
                text="⚠ Ajuste diverge da direção do fechamento.", fg=COR_AMARELO
            )
        else:
            self.lbl_confirmacao.config(text="", fg=COR_TEXTO_FRACO)

    def _atualizar_dados(self, dados, r):
        if self.var_modo_live.get():
            for lbl in self.linhas_dados.values():
                lbl.config(text="••••••", fg=COR_TEXTO_FRACO)
            return

        self.linhas_dados["fechamento"].config(text=self._fmt(dados["fechamento"]), fg=COR_TEXTO)
        self.linhas_dados["ajuste"].config(text=self._fmt(dados["ajuste"]), fg=COR_TEXTO)
        self.linhas_dados["teorico"].config(text=self._fmt(dados["teorico"]), fg=COR_TEXTO)
        self.linhas_dados["gap_fechamento"].config(text=formatar_gap(r["gap_fechamento"]), fg=COR_TEXTO)
        self.linhas_dados["gap_ajuste"].config(text=formatar_gap(r["gap_ajuste"]), fg=COR_TEXTO)

    def _atualizar_indices(self, dados):
        if self.var_modo_live.get():
            for lbl in (self.lbl_sp500, self.lbl_nasdaq, self.lbl_dow):
                lbl.config(text="••••", fg=COR_TEXTO_FRACO)
            return

        for lbl, chave in ((self.lbl_sp500, "sp500"), (self.lbl_nasdaq, "nasdaq"), (self.lbl_dow, "dow")):
            texto, cor = formatar_variacao(dados.get(chave))
            lbl.config(text=texto, fg=cor)

    @staticmethod
    def _fmt(valor):
        if not valor:
            return "-"
        return f"{valor:.0f}"


def main():
    root = tk.Tk()
    root.geometry("380x560")
    root.resizable(False, False)
    PainelLeilao(root)
    root.mainloop()


if __name__ == "__main__":
    main()
