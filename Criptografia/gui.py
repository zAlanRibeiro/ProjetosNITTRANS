import os
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

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

LARANJA       = "#F97316"
LARANJA_HOVER = "#C2610F"

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
        self.title("Criptografador de Arquivos")
        self.geometry("500x390")
        self.resizable(False, False)
        self._caminho = ""
        self._after_progresso: str | None = None
        self._build_ui()
        self._centralizar()

    def _centralizar(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # ── Cabeçalho ──────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Criptografador de Arquivos",
                     font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=24, pady=(24, 2))

        ctk.CTkLabel(self,
                     text="O HTML gerado abre em qualquer navegador — sem instalação.",
                     font=ctk.CTkFont(size=12), text_color="gray60").grid(
            row=1, column=0, padx=24, pady=(0, 16))

        # ── Card: Arquivo ──────────────────────────────────────────────────────
        card_arquivo = ctk.CTkFrame(self)
        card_arquivo.grid(row=2, column=0, padx=24, pady=(0, 10), sticky="ew")
        card_arquivo.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card_arquivo, text="Arquivo",
                     font=ctk.CTkFont(size=12), text_color="gray70").grid(
            row=0, column=0, padx=14, pady=(10, 4), sticky="w")

        linha_arquivo = ctk.CTkFrame(card_arquivo, fg_color="transparent")
        linha_arquivo.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        linha_arquivo.grid_columnconfigure(0, weight=1)

        self.entry_arquivo = ctk.CTkEntry(linha_arquivo,
                                          placeholder_text="Nenhum arquivo selecionado",
                                          state="disabled")
        self.entry_arquivo.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(linha_arquivo, text="Selecionar", width=100,
                      fg_color=LARANJA, hover_color=LARANJA_HOVER,
                      command=self._selecionar).grid(row=0, column=1)

        # ── Card: Senha ────────────────────────────────────────────────────────
        card_senha = ctk.CTkFrame(self)
        card_senha.grid(row=3, column=0, padx=24, pady=(0, 16), sticky="ew")
        card_senha.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card_senha, text="Senha",
                     font=ctk.CTkFont(size=12), text_color="gray70").grid(
            row=0, column=0, padx=14, pady=(10, 4), sticky="w")

        linha_senha = ctk.CTkFrame(card_senha, fg_color="transparent")
        linha_senha.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        linha_senha.grid_columnconfigure(0, weight=1)

        self.var_senha = tk.StringVar()
        self.entry_senha = ctk.CTkEntry(linha_senha, textvariable=self.var_senha,
                                        show="●", placeholder_text="Digite a senha")
        self.entry_senha.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.var_mostrar = tk.BooleanVar()
        ctk.CTkCheckBox(linha_senha, text="Mostrar", variable=self.var_mostrar,
                        command=self._toggle_senha, width=90,
                        fg_color=LARANJA, hover_color=LARANJA_HOVER).grid(row=0, column=1)

        # ── Botão de ação ──────────────────────────────────────────────────────
        ctk.CTkButton(self, text="🔒  Criptografar → HTML",
                      fg_color=LARANJA, hover_color=LARANJA_HOVER,
                      command=self._criptografar).grid(
            row=4, column=0, padx=24, pady=(0, 14), sticky="ew")

        # ── Barra de progresso ─────────────────────────────────────────────────
        self.progress = ctk.CTkProgressBar(self, mode="determinate",
                                           progress_color=LARANJA)
        self.progress.grid(row=5, column=0, padx=24, pady=(0, 8), sticky="ew")
        self.progress.set(0)

        # ── Status ─────────────────────────────────────────────────────────────
        self.var_status = tk.StringVar(value="Selecione um arquivo para começar.")
        ctk.CTkLabel(self, textvariable=self.var_status,
                     text_color="gray60", wraplength=450,
                     font=ctk.CTkFont(size=11)).grid(
            row=6, column=0, padx=24, pady=(0, 20))

    # ── Helpers de progresso ───────────────────────────────────────────────────

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

    # ── Helpers de UI ──────────────────────────────────────────────────────────

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

    def _validar(self) -> tuple[str, str] | None:
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

        # Pede o local de salvamento antes de iniciar o processamento
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
                    f"Arquivo criptografado!\n\n"
                    f"Salvo em:\n  {destino}\n\n"
                    "Envie o .html para a pessoa — ela abre no navegador,\n"
                    "digita a senha e baixa o arquivo original."))
            except Exception as e:
                self.after(0, lambda: self._erro_progresso("Erro ao criptografar."))
                self.after(50, lambda: messagebox.showerror("Erro", str(e)))

        threading.Thread(target=tarefa, daemon=True).start()

    def _descriptografar(self):
        r = self._validar()
        if not r:
            return
        caminho, senha = r

        if not caminho.endswith(".enc"):
            messagebox.showwarning("Aviso",
                "Este botão é para arquivos .enc (formato legado).\n\n"
                "Para arquivos .html criptografados, basta abri-los no navegador.")
            return

        self._iniciar_progresso()
        self.var_status.set("Descriptografando…")

        def tarefa():
            try:
                destino = descriptografar_enc(caminho, senha)
                nome = os.path.basename(destino)
                self.after(0, lambda: self._finalizar_progresso(f"✔ Finalizado: {nome}"))
                self.after(50, lambda: messagebox.showinfo("Sucesso",
                    f"Arquivo restaurado:\n{destino}"))
            except InvalidToken:
                self.after(0, lambda: self._erro_progresso("Senha incorreta."))
                self.after(50, lambda: messagebox.showerror("Senha incorreta",
                    "Senha incorreta ou arquivo corrompido."))
            except Exception as e:
                self.after(0, lambda: self._erro_progresso("Erro."))
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

        threading.Thread(target=tarefa, daemon=True).start()
