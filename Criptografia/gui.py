import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from cryptography.fernet import InvalidToken

try:
    from Criptografia.crypto import descriptografar_enc
    from Criptografia.html_builder import gerar_html
except ImportError:
    from crypto import descriptografar_enc
    from html_builder import gerar_html

# ── Paleta idêntica ao Hub ──────────────────────────────────────────────────
_FUNDO    = "#EEF2F7"
_AZUL     = "#1B5299"
_AZUL_SUB = "#DBEAFE"
_LARANJA  = "#F97316"
_LAR_HOV  = "#EA580C"
_BRANCO   = "#FFFFFF"
_BORDA    = "#E2E8F0"
_TEXTO    = "#1A202C"
_TEXTO_S  = "#64748B"
_SUCESSO  = "#059669"
_ERRO     = "#DC2626"
_FONTE    = "Segoe UI"

TIPOS_ABRIR = [
    ("Todos os arquivos suportados", "*.txt *.xlsx *.xls *.docx *.doc *.enc"),
    ("Arquivos de texto", "*.txt"),
    ("Planilhas Excel", "*.xlsx *.xls"),
    ("Documentos Word", "*.docx *.doc"),
    ("Arquivos criptografados (.enc)", "*.enc"),
    ("Todos os arquivos", "*.*"),
]


class _AppMixin:
    """Lógica e UI compartilhadas — funciona em CTk e CTkToplevel."""

    def _init_common(self):
        self.title("Criptografar Arquivos — NITTRANS")
        self.geometry("480x430")
        self.resizable(False, False)
        self.configure(fg_color=_FUNDO)

        # CTkToplevel reinicia internamente ~200ms após criar — define o ícone antes e depois
        self.after(50,  self._aplicar_icone)
        self.after(400, self._aplicar_icone)

        self._caminho = ""
        self._after_progresso = None
        self._build_ui()
        self._centralizar()

    def _aplicar_icone(self):
        try:
            if getattr(sys, 'frozen', False):
                # Rodando como .exe — logo.ico está em _internal/ ao lado do executável
                ico = os.path.join(os.path.dirname(sys.executable), "_internal", "logo.ico")
            else:
                # Rodando direto do Python — logo.ico está na raiz do projeto
                ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logo.ico")
            if os.path.exists(ico):
                self.iconbitmap(ico)
        except Exception:
            pass

    def _centralizar(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # ── Card azul (header + body) ─────────────────────────────────────────
        card = ctk.CTkFrame(self, fg_color=_AZUL, corner_radius=10,
                            border_width=1, border_color="#1A4F8A")
        card.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=20, pady=(14, 12), sticky="w")

        ctk.CTkLabel(hdr, text="Criptografar Arquivos",
                     font=(_FONTE, 15, "bold"), text_color="#FFFFFF",
                     fg_color="transparent").pack(anchor="w")
        ctk.CTkLabel(hdr, text="Proteja arquivos com senha — HTML autocontido",
                     font=(_FONTE, 10), text_color=_AZUL_SUB,
                     fg_color="transparent").pack(anchor="w", pady=(3, 0))

        # Corpo branco
        body = ctk.CTkFrame(card, fg_color=_BRANCO, corner_radius=9)
        body.grid(row=1, column=0, padx=2, pady=(0, 2), sticky="ew")
        body.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(body, fg_color="transparent")
        inner.grid(row=0, column=0, padx=18, pady=16, sticky="ew")
        inner.grid_columnconfigure(0, weight=1)

        # ── Arquivo ───────────────────────────────────────────────────────────
        ctk.CTkLabel(inner, text="Arquivo", font=(_FONTE, 11, "bold"),
                     text_color=_TEXTO, fg_color="transparent").grid(
            row=0, column=0, sticky="w", pady=(0, 5))

        row_arq = ctk.CTkFrame(inner, fg_color="transparent")
        row_arq.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        row_arq.grid_columnconfigure(0, weight=1)

        self.entry_arquivo = ctk.CTkEntry(
            row_arq, placeholder_text="Nenhum arquivo selecionado",
            state="disabled", height=36,
            fg_color=_BRANCO, border_color=_BORDA, text_color=_TEXTO)
        self.entry_arquivo.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(row_arq, text="Selecionar", width=105, height=36,
                      fg_color=_LARANJA, hover_color=_LAR_HOV,
                      text_color="white", font=(_FONTE, 12, "bold"),
                      corner_radius=6,
                      command=self._selecionar).grid(row=0, column=1)

        # ── Senha ─────────────────────────────────────────────────────────────
        ctk.CTkLabel(inner, text="Senha de acesso", font=(_FONTE, 11, "bold"),
                     text_color=_TEXTO, fg_color="transparent").grid(
            row=2, column=0, sticky="w", pady=(0, 5))

        row_senha = ctk.CTkFrame(inner, fg_color="transparent")
        row_senha.grid(row=3, column=0, sticky="ew", pady=(0, 16))
        row_senha.grid_columnconfigure(0, weight=1)

        self.var_senha = tk.StringVar()
        self.entry_senha = ctk.CTkEntry(
            row_senha, textvariable=self.var_senha,
            show="●", placeholder_text="Digite a senha", height=36,
            fg_color=_BRANCO, border_color=_BORDA, text_color=_TEXTO)
        self.entry_senha.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.entry_senha.bind("<Return>", lambda e: self._criptografar())

        self.var_mostrar = tk.BooleanVar()
        ctk.CTkCheckBox(row_senha, text="Mostrar", variable=self.var_mostrar,
                        command=self._toggle_senha, width=90,
                        fg_color=_LARANJA, hover_color=_LAR_HOV,
                        text_color=_TEXTO, checkmark_color="white").grid(
            row=0, column=1)

        # ── Botão principal ───────────────────────────────────────────────────
        ctk.CTkButton(inner, text="🔒   Criptografar → HTML",
                      fg_color=_LARANJA, hover_color=_LAR_HOV,
                      text_color="white", height=44, corner_radius=6,
                      font=(_FONTE, 13, "bold"),
                      command=self._criptografar).grid(
            row=4, column=0, sticky="ew", pady=(0, 10))

        # ── Progresso ─────────────────────────────────────────────────────────
        self.progress = ctk.CTkProgressBar(inner, mode="determinate",
                                           progress_color=_LARANJA,
                                           fg_color=_BORDA, height=5, corner_radius=3)
        self.progress.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        self.progress.set(0)

        # ── Status ────────────────────────────────────────────────────────────
        self.var_status = tk.StringVar(value="Selecione um arquivo para começar.")
        ctk.CTkLabel(inner, textvariable=self.var_status,
                     text_color=_TEXTO_S, wraplength=400,
                     fg_color="transparent",
                     font=(_FONTE, 11)).grid(row=6, column=0, pady=(0, 2))

    # ── Progresso ─────────────────────────────────────────────────────────────

    def _iniciar_progresso(self):
        self.progress.set(0)
        self._progresso_val = 0.0
        self._avancar_progresso()

    def _avancar_progresso(self):
        if self._progresso_val < 0.85:
            self._progresso_val = min(self._progresso_val + 0.018, 0.85)
            self.progress.set(self._progresso_val)
            self._after_progresso = self.after(30, self._avancar_progresso)

    def _finalizar_progresso(self, mensagem: str):
        if self._after_progresso:
            self.after_cancel(self._after_progresso)
            self._after_progresso = None
        self.progress.set(1.0)
        self.var_status.set(mensagem)
        self.after(3000, lambda: self.progress.set(0))

    def _erro_progresso(self, mensagem: str):
        if self._after_progresso:
            self.after_cancel(self._after_progresso)
            self._after_progresso = None
        self.progress.set(0)
        self.var_status.set(mensagem)

    # ── UI helpers ─────────────────────────────────────────────────────────────

    def _toggle_senha(self):
        self.entry_senha.configure(show="" if self.var_mostrar.get() else "●")

    def _set_arquivo(self, caminho: str):
        self._caminho = caminho
        self.entry_arquivo.configure(state="normal")
        self.entry_arquivo.delete(0, "end")
        self.entry_arquivo.insert(0, os.path.basename(caminho))
        self.entry_arquivo.configure(state="disabled")

    def _selecionar(self):
        caminho = filedialog.askopenfilename(title="Selecione o arquivo",
                                             filetypes=TIPOS_ABRIR)
        if caminho:
            self._set_arquivo(caminho)
            self.var_status.set(f"Arquivo: {os.path.basename(caminho)}")

    def _validar(self):
        if not self._caminho:
            messagebox.showwarning("Aviso", "Selecione um arquivo.")
            return None
        if not os.path.isfile(self._caminho):
            messagebox.showerror("Erro", "Arquivo não encontrado.")
            return None
        senha = self.var_senha.get()
        if not senha:
            messagebox.showwarning("Aviso", "Digite uma senha.")
            return None
        return self._caminho, senha

    def _resetar_campos(self):
        self._caminho = ""
        self.entry_arquivo.configure(state="normal")
        self.entry_arquivo.delete(0, "end")
        self.entry_arquivo.configure(state="disabled")
        self.var_senha.set("")

    # ── Ações ──────────────────────────────────────────────────────────────────

    def _criptografar(self):
        r = self._validar()
        if not r:
            return
        caminho, senha = r

        if caminho.endswith(".enc"):
            messagebox.showwarning("Aviso",
                "Selecione um arquivo original para criptografar, não um .enc.")
            return

        nome_sugerido = os.path.basename(caminho) + ".html"
        destino = filedialog.asksaveasfilename(
            title="Salvar arquivo criptografado como",
            initialfile=nome_sugerido,
            defaultextension=".html",
            filetypes=[("Arquivo HTML", "*.html"), ("Todos os arquivos", "*.*")],
        )
        if not destino:
            return

        self._iniciar_progresso()
        self.var_status.set("Criptografando…")

        def tarefa():
            try:
                gerar_html(caminho, senha, destino)
                nome = os.path.basename(destino)
                self.after(0, lambda: self._finalizar_progresso(f"✔ Finalizado: {nome}"))
                self.after(0, self._resetar_campos)
                self.after(50, lambda: messagebox.showinfo("Sucesso",
                    f"Arquivo criptografado!\n\nSalvo em:\n  {destino}\n\n"
                    "Envie o .html — o destinatário abre no navegador,\n"
                    "digita a senha e baixa o arquivo original."))
            except Exception as e:
                self.after(0, lambda: self._erro_progresso("✖ Erro ao criptografar."))
                self.after(50, lambda: messagebox.showerror("Erro", str(e)))

        threading.Thread(target=tarefa, daemon=True).start()


class App(_AppMixin, ctk.CTk):
    """Janela standalone — usada ao rodar criptografia.py diretamente."""
    def __init__(self):
        ctk.CTk.__init__(self)
        self._init_common()


class AppToplevel(_AppMixin, ctk.CTkToplevel):
    """Janela filha — usada quando integrada ao Hub de Ferramentas."""
    def __init__(self, master):
        ctk.CTkToplevel.__init__(self, master)
        self._init_common()
