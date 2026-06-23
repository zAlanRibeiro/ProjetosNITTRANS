# -*- coding: utf-8 -*-
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageTk
import os

# Importando a regra de negócio e funções auxiliares
from .logica import processar_pdf_lgpd
from processamento import obter_diretorio_base

class JanelaHigienizar(ctk.CTkToplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        self.title("Tarjar PDF — NITTRANS")
        self.geometry("460x650") 
        self.resizable(False, False)
        self.grab_set()
        
        self.caminho_arquivo = None
        base = obter_diretorio_base()

        # ── ÍCONE DA JANELA ───────────────────────────────────────────────────
        for ico in [os.path.join(base, "logo.ico"),
                    os.path.join(base, "_internal", "logo.ico")]:
            if os.path.exists(ico):
                try:
                    self.after(200, lambda i=ico: self.iconbitmap(i))
                except Exception:
                    pass
                break

        # ── CANVAS DE FUNDO (IDENTIDADE VISUAL) ────────────────────────────────
        self.canvas = tk.Canvas(self, width=460, height=650, bg="#0A2548", highlightthickness=0)
        self.canvas.place(x=0, y=0)

        # ── LOGO E FUNDO ──────────────────────────────────────────────────────
        for caminho_fundo in [os.path.join(base, "FundoAplicativoNITTRANS.png"),
                              os.path.join(base, "_internal", "FundoAplicativoNITTRANS.png")]:
            if os.path.exists(caminho_fundo):
                img = Image.open(caminho_fundo).convert("RGBA").resize((460, 650), Image.LANCZOS)
                overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(overlay)
                
                # Caixa de vidro centralizada
                draw.rounded_rectangle((20, 110, 440, 600), radius=15, fill=(8, 25, 55, 110))
                
                self.tk_fundo = ImageTk.PhotoImage(Image.alpha_composite(img, overlay))
                self.canvas.create_image(0, 0, anchor="nw", image=self.tk_fundo)
                break

        # Cor base para mesclar os widgets CTk sobre o vidro
        COR_FUNDO_VIDRO = "#0C2340"

        # Banner Superior
        self.canvas.create_text(230, 135, text="Tarjar PDF", font=("Segoe UI", 18, "bold"), fill="#FFFFFF")

        # ── COMPONENTES INTERATIVOS ───────────────────────────────────────────
        self.id_arquivo = self.canvas.create_text(230, 170, text="Selecione um arquivo...", 
                                                  font=("Segoe UI", 12), fill="#A3C2F0", anchor="center")

        btn_sel = ctk.CTkButton(self, text="📁 Selecionar Arquivo", command=self.selecionar, 
                                fg_color="#1B5299", hover_color="#153E75", height=35, bg_color=COR_FUNDO_VIDRO)
        btn_sel.place(x=230, y=215, anchor="center")

        # ── CHECKBOXES (Esticado proporcionalmente de ponta a ponta) ──────────
        self.frame_chk = ctk.CTkFrame(self, width=380, height=35, 
                                      fg_color=COR_FUNDO_VIDRO, bg_color=COR_FUNDO_VIDRO)
        self.frame_chk.place(x=230, y=265, anchor="center")
        
        # Trava o tamanho do frame para respeitar os 380px de largura
        self.frame_chk.grid_propagate(False) 
        
        # Distribui uniformemente as 4 colunas dentro do espaço esticado
        self.frame_chk.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.v_cpf = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.frame_chk, text="CPF", variable=self.v_cpf, text_color="#FFFFFF",
                        fg_color="#F97316", bg_color=COR_FUNDO_VIDRO).grid(row=0, column=0, pady=4)
        
        self.v_rg = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.frame_chk, text="RG", variable=self.v_rg, text_color="#FFFFFF",
                        fg_color="#F97316", bg_color=COR_FUNDO_VIDRO).grid(row=0, column=1, pady=4)
        
        self.v_em = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.frame_chk, text="E-mail", variable=self.v_em, text_color="#FFFFFF",
                        fg_color="#F97316", bg_color=COR_FUNDO_VIDRO).grid(row=0, column=2, pady=4)

        self.v_cnpj = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.frame_chk, text="CNPJ", variable=self.v_cnpj, text_color="#FFFFFF",
                        fg_color="#F97316", bg_color=COR_FUNDO_VIDRO).grid(row=0, column=3, pady=4)
        # ──────────────────────────────────────────────────────────────────────

        # Caixa Multi-linha
        self.canvas.create_text(50, 310, text="Palavras Manuais (uma por linha):", 
                                font=("Segoe UI", 10, "bold"), fill="#FFFFFF", anchor="w")
        self.txt_manual = ctk.CTkTextbox(self, width=380, height=120, border_width=1, 
                                         bg_color=COR_FUNDO_VIDRO, fg_color="#FFFFFF", text_color="#000000")
        self.txt_manual.place(x=40, y=325)

        # Botão Laranja NITTRANS
        self.btn_exec = ctk.CTkButton(self, text="EXECUTAR TARJA", font=("Segoe UI", 14, "bold"),
                                      fg_color="#F97316", hover_color="#EA580C", height=45, width=380,
                                      bg_color=COR_FUNDO_VIDRO, command=self.executar)
        self.btn_exec.place(x=230, y=490, anchor="center")

        # Texto Status
        self.id_status = self.canvas.create_text(230, 540, text="", font=("Segoe UI", 11, "bold"), 
                                                 fill="#FFFFFF", anchor="center", width=420)

    def selecionar(self):
        c = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if c:
            self.caminho_arquivo = c
            self.canvas.itemconfig(self.id_arquivo, text=os.path.basename(c), fill="#FFFFFF")

    def ejecutar(self):
        if not self.caminho_arquivo:
            self.canvas.itemconfig(self.id_status, text="Erro: Selecione um arquivo!", fill="#F87171")
            return
        
        texto = self.txt_manual.get("0.0", "end").split('\n')
        lista = [l.strip() for l in texto if l.strip()]
        
        self.canvas.itemconfig(self.id_status, text="Processando...", fill="#FFB347")
        self.update()
        
        # Chamada com o parâmetro CNPJ integrado
        ok, msg = processar_pdf_lgpd(
            self.caminho_arquivo, 
            self.v_cpf.get(), 
            self.v_em.get(), 
            self.v_rg.get(), 
            lista,
            tarjar_cnpj=self.v_cnpj.get()
        )
        
        cor_status = "#4ADE80" if ok else "#F87171"
        self.canvas.itemconfig(self.id_status, text=msg, fill=cor_status)