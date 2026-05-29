# -*- coding: utf-8 -*-
import tkinter as tk
import customtkinter as ctk
import os
from PIL import Image
from processamento import GerenciadorProcessos, obter_diretorio_base

COR_LARANJA_PRINCIPAL = "#FF8C00"
COR_LARANJA_HOVER = "#CC7000"
COR_TEXTO_BOTAO = "black"
COR_FUNDO_PASTA = "#4A4A4A"

DICAS = {
    "enderecos.py":             "Converte coordenadas geograficas (latitude/longitude) em enderecos completos via OpenStreetMap. Aceita CSV e Excel.",
    "limpeza.py":               "Corrige encoding, padroniza logradouros e valida enderecos em planilhas CSV/Excel. Gera relatorio de alteracoes.",
    "decifradorTxt.py":         "Converte arquivos .txt de posicao fixa exportados pelo DETRAN/RJ em planilha Excel estruturada com todos os campos separados.",
    "detranLimpo.py":           "Limpa a coluna de endereco de planilhas Excel, removendo numeros, sufixos (OP., OPOSTO) e referencias de cruzamento.",
    "pdfDeferidoIndeferido.py": "Extrai dados de processos julgados (Deferido/Indeferido) de PDFs do sistema GAIDE e consolida em uma planilha Excel.",
    "processosAbertos.py":      "Le relatorios PDF de Processos Abertos da 1a. Instancia (GAIDE/DETRAN) e exporta todos os registros para Excel.",
    "criptografia":             "Criptografa qualquer arquivo com senha (AES-256-GCM) e gera um HTML autocontido — o destinatario abre no navegador e baixa o arquivo.",
}


class _Tooltip:
    def __init__(self, widget, texto):
        self._widget = widget
        self._texto = texto
        self._janela = None
        widget.bind("<Enter>", self._mostrar, add="+")
        widget.bind("<Leave>", self._esconder, add="+")

    def _mostrar(self, event=None):
        if self._janela:
            return
        x = self._widget.winfo_rootx()
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 6
        self._janela = tk.Toplevel(self._widget)
        self._janela.wm_overrideredirect(True)
        self._janela.wm_geometry(f"+{x}+{y}")
        self._janela.attributes("-topmost", True)
        tk.Label(
            self._janela, text=self._texto,
            background="#222222", foreground="#FFFFFF",
            font=("Arial", 10), padx=10, pady=6,
            wraplength=360, justify="left",
            relief="flat", bd=0
        ).pack()

    def _esconder(self, event=None):
        if self._janela:
            self._janela.destroy()
            self._janela = None


class HubApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.geometry("450x840")
        self.title("Hub de Ferramentas - Gestao e Modernizacao")
        ctk.set_appearance_mode("dark")

        base = obter_diretorio_base()
        for ico in [os.path.join(base, "logo.ico"),
                    os.path.join(base, "_internal", "logo.ico")]:
            if os.path.exists(ico):
                try:
                    self.iconbitmap(ico)
                except Exception:
                    pass
                break

        self.logica = GerenciadorProcessos(
            callback_sucesso=self.ao_finalizar_sucesso,
            callback_erro=self.ao_dar_erro,
            callback_status=self.atualizar_status
        )

        self._construir_interface()

    def _construir_interface(self):
        base = obter_diretorio_base()
        candidatos = [
            os.path.join(base, "Logo.png"),
            os.path.join(base, "_internal", "Logo.png"),
        ]
        caminho_logo = next((p for p in candidatos if os.path.exists(p)), None)

        if caminho_logo:
            try:
                imagem_logo = ctk.CTkImage(
                    light_image=Image.open(caminho_logo),
                    dark_image=Image.open(caminho_logo),
                    size=(384, 90)
                )
                lbl_logo = ctk.CTkLabel(self, image=imagem_logo, text="")
                lbl_logo._logo_ref = imagem_logo
                lbl_logo.pack(pady=(20, 5))
            except Exception:
                caminho_logo = None

        if not caminho_logo:
            lbl_placeholder = ctk.CTkLabel(self, text="[ LOGO NITTRANS ]",
                                           font=("Arial", 16, "italic"), text_color="gray")
            lbl_placeholder.pack(pady=(20, 5))

        self.titulo = ctk.CTkLabel(self, text="Central de Ferramentas", font=("Arial", 20, "bold"))
        self.titulo.pack(pady=(0, 20))

        self._criar_botao_ferramenta("1. Latitude e Longitude",    "LatitudeLongitude",   "enderecos.py")
        self._criar_botao_ferramenta("2. Limpeza de Arquivos",     "LimpezaArquivo",      "limpeza.py")
        self._criar_botao_ferramenta("3. Organizador TXT Detran",  "OrganizadorTxtDetran","decifradorTxt.py")
        self._criar_botao_ferramenta("4. Organizador Detran Limpo","DetranLimpo",         "detranLimpo.py")
        self._criar_botao_ferramenta("5. PDF e Excel Multas",      "PdfExcelMultas",      "pdfDeferidoIndeferido.py")
        self._criar_botao_ferramenta("6. Processos Abertos",       "ProcessosAbertos",    "processosAbertos.py")

        frame_cripto = ctk.CTkFrame(self, fg_color="transparent")
        frame_cripto.pack(pady=10, padx=40, fill="x")
        btn_cripto = ctk.CTkButton(frame_cripto, text="7. Criptografar Arquivos", height=45,
                                   font=("Arial", 14, "bold"),
                                   fg_color=COR_LARANJA_PRINCIPAL,
                                   hover_color=COR_LARANJA_HOVER,
                                   text_color=COR_TEXTO_BOTAO,
                                   command=self._abrir_criptografia)
        btn_cripto.pack(fill="x")
        _Tooltip(btn_cripto, DICAS["criptografia"])

        self.frame_status = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_status.pack(side="bottom", pady=20, fill="x")

        self.lbl_status = ctk.CTkLabel(self.frame_status, text="", font=("Arial", 14, "bold"))
        self.lbl_status.pack(pady=5)

        self.btn_exportar = ctk.CTkButton(self.frame_status, text="Exportar Arquivo Pronto",
                                          fg_color="#28a745", hover_color="#218838",
                                          height=40, text_color="white")

    def _criar_botao_ferramenta(self, texto, pasta, script):
        frame_linha = ctk.CTkFrame(self, fg_color="transparent")
        frame_linha.pack(pady=10, padx=40, fill="x")

        btn_principal = ctk.CTkButton(frame_linha, text=texto, height=45,
                                      font=("Arial", 14, "bold"),
                                      fg_color=COR_LARANJA_PRINCIPAL,
                                      hover_color=COR_LARANJA_HOVER,
                                      text_color=COR_TEXTO_BOTAO,
                                      command=lambda p=pasta, s=script: self.preparar_ferramenta(p, s))
        btn_principal.pack(side="left", expand=True, fill="x", padx=(0, 10))

        if script in DICAS:
            _Tooltip(btn_principal, DICAS[script])

        btn_pasta = ctk.CTkButton(frame_linha, text="📁", width=45, height=45,
                                  font=("Arial", 18),
                                  fg_color=COR_FUNDO_PASTA,
                                  hover_color="#333333",
                                  command=lambda p=pasta: self.logica.abrir_pasta(p))
        btn_pasta.pack(side="right")

    def _abrir_criptografia(self):
        from Criptografia.gui import AppToplevel
        AppToplevel(self)

    def preparar_ferramenta(self, pasta, script):
        self.lbl_status.configure(text="")
        self.btn_exportar.pack_forget()
        self.logica.iniciar_tarefa(pasta, script)

    def atualizar_status(self, mensagem, cor=COR_LARANJA_PRINCIPAL):
        self.lbl_status.configure(text=mensagem, text_color=cor)

    def ao_finalizar_sucesso(self, pasta):
        self.after(0, self._exibir_botao_exportacao, pasta)

    def _exibir_botao_exportacao(self, pasta):
        self.lbl_status.configure(text=f"Arquivo Pronto: {pasta}", text_color="#28a745")
        self.btn_exportar.configure(command=lambda: self.executar_exportacao(pasta))
        self.btn_exportar.pack(pady=10)

    def ao_dar_erro(self, erro):
        self.after(0, self._exibir_erro, erro)

    def _exibir_erro(self, erro):
        self.lbl_status.configure(text=f"Erro: {erro}", text_color="red")
        self.btn_exportar.pack_forget()

    def executar_exportacao(self, pasta):
        sucesso = self.logica.exportar_resultado(pasta)
        if sucesso:
            self.btn_exportar.pack_forget()