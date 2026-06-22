# -*- coding: utf-8 -*-
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk

import customtkinter as ctk

try:
    from Criptografia.crypto import descriptografar_enc
    from Criptografia.html_builder import gerar_html
except ImportError:
    from crypto import descriptografar_enc
    from html_builder import gerar_html

# ── Paleta idêntica ao Hub ──────────────────────────────────────────────────
COR_VIDRO_BLENDED = "#0A2548" # Camuflagem perfeita para o vidro
_FUNDO    = "#EEF2F7"
_AZUL     = "#1B5299"
_AZUL_SUB = "#A3C2F0"
_LARANJA  = "#F97316"
_LAR_HOV  = "#EA580C"
_BRANCO   = "#FFFFFF"
_BORDA    = "#E2E8F0"
_TEXTO    = "#1A202C"
_TEXTO_S  = "#A3C2F0"
_SUCESSO  = "#4ADE80"
_ERRO     = "#F87171"
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
        self.geometry("480x480") # Ajustado para caber o novo design
        self.resizable(False, False)
        # Cor de fundo camuflada com o vidro
        self.configure(fg_color=COR_VIDRO_BLENDED)

        # CTkToplevel reinicia internamente ~200ms após criar — define o ícone antes e depois
        self.after(50,  self._aplicar_icone)
        self.after(400, self._aplicar_icone)

        self._caminho = ""
        self._after_progresso = None
        self._build_ui()
        self._centralizar()

    def _obter_caminho_recurso(self, nome_arquivo):
        # Procura na pasta atual, na pasta pai ou no _internal do executável
        caminhos = [
            nome_arquivo,
            os.path.join("..", nome_arquivo),
            os.path.join(os.path.dirname(__file__), "..", nome_arquivo),
            os.path.join(getattr(sys, '_MEIPASS', ''), nome_arquivo),
            os.path.join(os.path.dirname(sys.executable), "_internal", nome_arquivo)
        ]
        for p in caminhos:
            if os.path.exists(p): return p
        return nome_arquivo

    def _aplicar_icone(self):
        try:
            ico = self._obter_caminho_recurso("logo.ico")
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
        # ── CANVAS (O PINTOR) ──────────────────────────────────────────────────
        self.canvas = tk.Canvas(self, width=480, height=480, bg=COR_VIDRO_BLENDED, highlightthickness=0)
        self.canvas.place(x=0, y=0)

        # ── PROCESSAMENTO DO FUNDO ─────────────────────────────────────────────
        caminho_fundo = self._obter_caminho_recurso("FundoAplicativoNITTRANS.png")
        if os.path.exists(caminho_fundo):
            try:
                img_original = Image.open(caminho_fundo).convert("RGBA")
                img_original = img_original.resize((480, 480), Image.LANCZOS)

                camada_overlay = Image.new("RGBA", img_original.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(camada_overlay)

                # Vidro fumê
                draw.rounded_rectangle((15, 15, 465, 465), radius=15, fill=(8, 25, 55, 110))

                img_mesclada = Image.alpha_composite(img_original, camada_overlay)
                self.tk_fundo = ImageTk.PhotoImage(img_mesclada)
                self.canvas.create_image(0, 0, anchor="nw", image=self.tk_fundo)
            except Exception as e:
                print(f"Erro ao carregar fundo: {e}")

        # ── TEXTOS NATIVOS NO CANVAS (Sem blocos escuros) ──────────────────────
        self.canvas.create_text(40, 50, text="Criptografar Arquivos", 
                                font=(_FONTE, 18, "bold"), fill=_BRANCO, anchor="w")
        
        self.canvas.create_text(40, 75, text="Proteja arquivos com senha — HTML autocontido", 
                                font=(_FONTE, 11), fill=_AZUL_SUB, anchor="w")

        self.canvas.create_text(40, 130, text="Arquivo", font=(_FONTE, 12, "bold"), fill=_BRANCO, anchor="w")
        self.canvas.create_text(40, 215, text="Senha de acesso", font=(_FONTE, 12, "bold"), fill=_BRANCO, anchor="w")

        # Status Label nativo do Canvas
        self.id_status = self.canvas.create_text(240, 435, text="Selecione um arquivo para começar.", 
                                                 font=(_FONTE, 11), fill=_TEXTO_S, anchor="center")

        # ── WIDGETS FLUTUANTES ─────────────────────────────────────────────────
        # Arquivo
        self.entry_arquivo = ctk.CTkEntry(
            self, placeholder_text="Nenhum arquivo selecionado",
            state="disabled", height=40, width=280, corner_radius=8,
            fg_color=_BRANCO, border_color=_BORDA, text_color=_TEXTO, bg_color=COR_VIDRO_BLENDED)
        self.entry_arquivo.place(x=40, y=145)

        ctk.CTkButton(self, text="Selecionar", width=110, height=40,
                      fg_color=_LARANJA, hover_color=_LAR_HOV,
                      text_color="white", font=(_FONTE, 12, "bold"),
                      corner_radius=8, bg_color=COR_VIDRO_BLENDED,
                      command=self._selecionar).place(x=330, y=145)

        # Senha
        self.var_senha = tk.StringVar()
        self.entry_senha = ctk.CTkEntry(
            self, textvariable=self.var_senha, width=310,
            show="●", placeholder_text="Digite a senha", height=40, corner_radius=8,
            fg_color=_BRANCO, border_color=_BORDA, text_color=_TEXTO, bg_color=COR_VIDRO_BLENDED)
        self.entry_senha.place(x=40, y=230)
        self.entry_senha.bind("<Return>", lambda e: self._criptografar())

        self.var_mostrar = tk.BooleanVar()
        ctk.CTkCheckBox(self, text="Mostrar", variable=self.var_mostrar,
                        command=self._toggle_senha, width=80,
                        fg_color=_LARANJA, hover_color=_LAR_HOV, bg_color=COR_VIDRO_BLENDED,
                        text_color=_BRANCO, checkmark_color="white").place(x=365, y=238)

        # Botão Criptografar
        ctk.CTkButton(self, text="🔒   Criptografar → HTML", width=400,
                      fg_color=_LARANJA, hover_color=_LAR_HOV,
                      text_color="white", height=48, corner_radius=8,
                      font=(_FONTE, 14, "bold"), bg_color=COR_VIDRO_BLENDED,
                      command=self._criptografar).place(x=40, y=305)

        # Progresso
        self.progress = ctk.CTkProgressBar(self, mode="determinate", width=400,
                                           progress_color=_LARANJA, bg_color=COR_VIDRO_BLENDED,
                                           fg_color=_BRANCO, height=6, corner_radius=3)
        self.progress.place(x=40, y=390)
        self.progress.set(0)


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
        self.canvas.itemconfig(self.id_status, text=mensagem, fill=_SUCESSO)
        self.after(3000, lambda: self.progress.set(0))

    def _erro_progresso(self, mensagem: str):
        if self._after_progresso:
            self.after_cancel(self._after_progresso)
            self._after_progresso = None
        self.progress.set(0)
        self.canvas.itemconfig(self.id_status, text=mensagem, fill=_ERRO)

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
            self.canvas.itemconfig(self.id_status, text=f"Arquivo: {os.path.basename(caminho)}", fill=_TEXTO_S)

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
        self.canvas.itemconfig(self.id_status, text="Criptografando…", fill=_TEXTO_S)

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