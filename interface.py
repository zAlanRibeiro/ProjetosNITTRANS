# -*- coding: utf-8 -*-
import tkinter as tk
import customtkinter as ctk
import os
import time
from PIL import Image
from processamento import GerenciadorProcessos, obter_diretorio_base

SPINNER = ["◐", "◓", "◑", "◒"]

# ── Paleta ────────────────────────────────────────────────────────────────────
COR_FUNDO         = "#EEF2F7"
COR_TOPBAR        = "#FFFFFF"
COR_AZUL          = "#1B5299"
COR_AZUL_SUBTITULO= "#DBEAFE"
COR_LARANJA       = "#F97316"
COR_LARANJA_HOVER = "#EA580C"
COR_CARD          = "#FFFFFF"
COR_CARD_SHADOW   = "#C8D3E0"
COR_DIVIDER       = "#E2E8F0"
COR_PASTA_BORDER  = "#CBD5E0"
COR_PASTA_HOVER   = "#F1F5F9"
COR_PASTA_ICONE   = "#64748B"
COR_TEXTO         = "#1A202C"
COR_TEXTO_SUAVE   = "#64748B"
COR_SUCESSO       = "#059669"
COR_ERRO          = "#DC2626"
COR_FOOTER        = "#475569"

FONTE = "Segoe UI"

ICONES = {
    "enderecos.py":             "📍",
    "limpeza.py":               "🔍",
    "decifradorTxt.py":         "📋",
    "detranLimpo.py":           "✂",
    "pdfDeferidoIndeferido.py": "📑",
    "processosAbertos.py":      "📂",
    "criptografia":             "🔒",
}

DICAS = {
    "enderecos.py":             "Converte coordenadas geográficas em endereços completos via OpenStreetMap.",
    "limpeza.py":               "Corrige encoding, padroniza logradouros e valida endereços em planilhas.",
    "decifradorTxt.py":         "Converte arquivos .txt posicionais do DETRAN/RJ em planilha Excel.",
    "detranLimpo.py":           "Limpa coluna de endereço removendo números, OP., OPOSTO e cruzamentos.",
    "pdfDeferidoIndeferido.py": "Extrai processos deferidos/indeferidos de PDFs do sistema GAIDE.",
    "processosAbertos.py":      "Lê relatórios PDF de Processos Abertos 1ª Instância e exporta para Excel.",
    "criptografia":             "Criptografa arquivos com AES-256-GCM e gera HTML autocontido com senha.",
}


class _Tooltip:
    def __init__(self, widget, texto):
        self._widget = widget
        self._texto  = texto
        self._janela = None
        self._after  = None
        widget.bind("<Enter>", self._agendar, add="+")
        widget.bind("<Leave>", self._esconder, add="+")

    def _agendar(self, event=None):
        # Aguarda 500ms antes de mostrar — evita tooltip piscando ao passar rapidamente
        self._after = self._widget.after(500, self._mostrar)

    def _mostrar(self):
        if self._janela:
            return
        self._widget.update_idletasks()
        x  = self._widget.winfo_rootx()
        y  = self._widget.winfo_rooty() + self._widget.winfo_height() + 6
        sw = self._widget.winfo_screenwidth()

        self._janela = tk.Toplevel()
        self._janela.wm_overrideredirect(True)
        self._janela.attributes("-topmost", True)

        # Borda externa (efeito de sombra sutil)
        borda = tk.Frame(self._janela, bg="#475569", padx=1, pady=1)
        borda.pack()

        # Conteúdo
        tk.Label(
            borda, text=self._texto,
            background="#1E293B", foreground="#E2E8F0",
            font=(FONTE, 10), padx=14, pady=9,
            wraplength=340, justify="left", relief="flat", bd=0
        ).pack()

        self._janela.update_idletasks()
        w = self._janela.winfo_reqwidth()
        if x + w > sw - 12:
            x = sw - w - 12
        self._janela.wm_geometry(f"+{x}+{y}")

    def _esconder(self, event=None):
        if self._after:
            self._widget.after_cancel(self._after)
            self._after = None
        if self._janela:
            self._janela.destroy()
            self._janela = None


class HubApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("light")
        self.configure(fg_color=COR_FUNDO)
        self.geometry("460x730")
        self.resizable(False, False)
        self.title("Hub de Ferramentas — NITTRANS")

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

        # ── Rodapé (pack first so it stays at bottom) ─────────────────────────
        footer = ctk.CTkFrame(self, fg_color=COR_TOPBAR, corner_radius=0, height=34)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)
        ctk.CTkFrame(footer, fg_color=COR_DIVIDER, corner_radius=0, height=1).pack(fill="x")
        ctk.CTkLabel(
            footer,
            text="NITTRANS  ·  Niterói Transporte e Trânsito  ·  Prefeitura Municipal de Niterói",
            font=(FONTE, 8), text_color=COR_FOOTER
        ).pack(expand=True)

        # ── Topbar ────────────────────────────────────────────────────────────
        topbar = ctk.CTkFrame(self, fg_color=COR_TOPBAR, corner_radius=0, height=76)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        base = obter_diretorio_base()
        for caminho in [os.path.join(base, "Logo.png"),
                        os.path.join(base, "_internal", "Logo.png")]:
            if os.path.exists(caminho):
                try:
                    img = ctk.CTkImage(
                        light_image=Image.open(caminho),
                        dark_image=Image.open(caminho),
                        size=(220, 52)
                    )
                    lbl = ctk.CTkLabel(topbar, image=img, text="", fg_color="transparent")
                    lbl._img_ref = img
                    lbl.pack(expand=True)
                    break
                except Exception:
                    pass
        else:
            ctk.CTkLabel(topbar, text="NITTRANS",
                         font=(FONTE, 24, "bold"), text_color=COR_AZUL).pack(expand=True)

        # Linha azul 3 px
        ctk.CTkFrame(self, fg_color=COR_AZUL, corner_radius=0, height=3).pack(fill="x")

        # ── Área principal ────────────────────────────────────────────────────
        main = ctk.CTkFrame(self, fg_color=COR_FUNDO, corner_radius=0)
        main.pack(fill="both", expand=True, padx=20, pady=16)

        # Card externo (azul = cabeçalho, borda limpa)
        card_ext = ctk.CTkFrame(main, fg_color=COR_AZUL, corner_radius=10,
                                border_width=1, border_color="#1A4F8A")
        card_ext.pack(fill="x")

        # Cabeçalho do card
        hdr = ctk.CTkFrame(card_ext, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(14, 12))

        ctk.CTkLabel(hdr,
                     text="Departamento de Gestão e Modernização — NITTRANS",
                     font=(FONTE, 14, "bold"), text_color="#FFFFFF",
                     wraplength=360, justify="left",
                     fg_color="transparent").pack(anchor="w")
        ctk.CTkLabel(hdr,
                     text="Hub de Ferramentas",
                     font=(FONTE, 14, "bold"), text_color=COR_AZUL_SUBTITULO,
                     fg_color="transparent").pack(anchor="w", pady=(4, 0))

        # Corpo branco
        card_body = ctk.CTkFrame(card_ext, fg_color=COR_CARD, corner_radius=9)
        card_body.pack(fill="x", padx=2, pady=(0, 2))

        btn_area = ctk.CTkFrame(card_body, fg_color="transparent")
        btn_area.pack(fill="x", padx=14, pady=12)

        tools = [
            ("1. Latitude e Longitude",    "LatitudeLongitude",   "enderecos.py"),
            ("2. Limpeza de Arquivos",      "LimpezaArquivo",      "limpeza.py"),
            ("3. Organizador Txt Detran",   "OrganizadorTxtDetran","decifradorTxt.py"),
            ("4. Organizador Detran Limpo", "DetranLimpo",         "detranLimpo.py"),
            ("5. PDF e Excel Multas",       "PdfExcelMultas",      "pdfDeferidoIndeferido.py"),
            ("6. Processos Abertos",        "ProcessosAbertos",    "processosAbertos.py"),
        ]
        for nome, pasta, script in tools:
            self._criar_botao(btn_area, nome, pasta, script)

        # Separador antes do Criptografar
        sep_frame = ctk.CTkFrame(btn_area, fg_color="transparent")
        sep_frame.pack(fill="x", pady=(6, 0))
        ctk.CTkFrame(sep_frame, fg_color=COR_DIVIDER, corner_radius=0, height=1).pack(fill="x")
        ctk.CTkLabel(sep_frame, text="Segurança", font=(FONTE, 9, "bold"),
                     text_color=COR_TEXTO_SUAVE, fg_color="transparent").pack(anchor="w", pady=(4, 2))

        # Botão Criptografar (sem pasta, largura total)
        frame_c = ctk.CTkFrame(btn_area, fg_color="transparent")
        frame_c.pack(fill="x", pady=(0, 2))
        btn_c = ctk.CTkButton(
            frame_c,
            text="  7. Criptografar Arquivos",
            anchor="w", height=38, corner_radius=6,
            font=(FONTE, 12, "bold"),
            fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER,
            text_color="#FFFFFF",
            command=self._abrir_criptografia
        )
        btn_c.pack(fill="x")
        _Tooltip(btn_c, DICAS["criptografia"])

        # ── Área de status ────────────────────────────────────────────────────
        self.frame_status = ctk.CTkFrame(main, fg_color="transparent")
        self.frame_status.pack(fill="x", pady=(12, 0))

        # Linha: spinner + tempo decorrido
        self.lbl_spinner = ctk.CTkLabel(
            self.frame_status, text="",
            font=(FONTE, 12, "bold"), text_color=COR_LARANJA
        )
        self.lbl_spinner.pack()

        # Barra de progresso determinada (0 → 100%)
        self.progress_bar = ctk.CTkProgressBar(
            self.frame_status,
            mode="determinate",
            progress_color=COR_LARANJA,
            fg_color=COR_DIVIDER,
            height=6, corner_radius=3
        )
        self.progress_bar.set(0)

        # Mensagem de resultado (sucesso ou erro)
        self.lbl_status = ctk.CTkLabel(
            self.frame_status, text="",
            font=(FONTE, 11), text_color=COR_TEXTO_SUAVE,
            wraplength=410, justify="left"
        )
        self.lbl_status.pack()

        self.btn_exportar = ctk.CTkButton(
            self.frame_status,
            text="💾   Exportar Arquivo Pronto",
            fg_color=COR_SUCESSO, hover_color="#047857",
            text_color="white", height=62, corner_radius=6,
            font=(FONTE, 13, "bold")
        )

        # Estado interno do spinner / progresso
        self._spinner_after  = None
        self._progress_after = None
        self._start_time     = None
        self._spinner_idx    = 0
        self._progress_val   = 0.0
        self._pasta_atual    = ""

    def _criar_botao(self, parent, nome, pasta, script):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=3)

        btn = ctk.CTkButton(
            frame,
            text=f"  {nome}",
            anchor="w", height=38, corner_radius=6,
            font=(FONTE, 12, "bold"),
            fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER,
            text_color="#FFFFFF",
            command=lambda p=pasta, s=script: self.preparar_ferramenta(p, s)
        )
        btn.pack(side="left", expand=True, fill="x", padx=(0, 6))

        if script in DICAS:
            _Tooltip(btn, DICAS[script])

        btn_pasta = ctk.CTkButton(
            frame, text="📁", width=38, height=38,
            corner_radius=6,
            fg_color="transparent",
            border_width=1, border_color=COR_PASTA_BORDER,
            hover_color=COR_PASTA_HOVER,
            text_color=COR_PASTA_ICONE,
            font=(FONTE, 14),
            command=lambda p=pasta: self.logica.abrir_pasta(p)
        )
        btn_pasta.pack(side="right")

    def _abrir_criptografia(self):
        from Criptografia.gui import AppToplevel
        AppToplevel(self)

    # ── Spinner / progresso ───────────────────────────────────────────────────
    def _iniciar_animacao(self, nome):
        self._start_time    = time.time()
        self._spinner_idx   = 0
        self._progress_val  = 0.0
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(4, 2))
        self._tick_spinner(nome)
        self._tick_progress()

    def _tick_spinner(self, nome):
        frame  = SPINNER[self._spinner_idx % len(SPINNER)]
        elapsed = int(time.time() - self._start_time)
        mins, secs = divmod(elapsed, 60)
        tempo = f"{mins}m {secs:02d}s" if mins else f"{secs}s"
        pct   = int(self._progress_val * 100)
        self.lbl_spinner.configure(
            text=f"{frame}  Processando {nome}...  {pct}%  ({tempo})"
        )
        self._spinner_idx  += 1
        self._spinner_after = self.after(120, self._tick_spinner, nome)

    def _tick_progress(self):
        # Avança de forma assintótica: rápido no início, lento perto de 92%
        if self._progress_val < 0.92:
            delta = max((0.92 - self._progress_val) * 0.035, 0.001)
            self._progress_val = min(self._progress_val + delta, 0.92)
            self.progress_bar.set(self._progress_val)
        self._progress_after = self.after(350, self._tick_progress)

    def _parar_animacao(self, sucesso=True):
        if self._spinner_after:
            self.after_cancel(self._spinner_after)
            self._spinner_after = None
        if self._progress_after:
            self.after_cancel(self._progress_after)
            self._progress_after = None
        self.lbl_spinner.configure(text="")
        if sucesso:
            self.progress_bar.set(1.0)
            self.after(600, lambda: self.progress_bar.pack_forget())
        else:
            self.progress_bar.pack_forget()

    # ── Callbacks de processamento ────────────────────────────────────────────
    def preparar_ferramenta(self, pasta, script):
        # Só limpa a UI — animação inicia DEPOIS do arquivo ser escolhido
        self._pasta_atual = pasta
        self.lbl_status.configure(text="")
        self.btn_exportar.pack_forget()
        self.logica.iniciar_tarefa(pasta, script)

    def atualizar_status(self, mensagem, cor=COR_LARANJA):
        # Chamado pelo processamento.py apenas após arquivo escolhido e thread iniciada
        self._iniciar_animacao(self._pasta_atual)

    def ao_finalizar_sucesso(self, pasta):
        self.after(0, self._exibir_sucesso, pasta)

    def _exibir_sucesso(self, pasta):
        elapsed = int(time.time() - self._start_time) if self._start_time else 0
        mins, secs = divmod(elapsed, 60)
        tempo = f"{mins}m {secs:02d}s" if mins else f"{secs}s"
        self._parar_animacao(sucesso=True)
        self.lbl_status.configure(
            text=f"✔  Concluído em {tempo} — {pasta}",
            text_color=COR_SUCESSO
        )
        self.btn_exportar.configure(command=lambda: self.executar_exportacao(pasta))
        self.btn_exportar.pack(fill="x", pady=(8, 0))

    def ao_dar_erro(self, erro):
        self.after(0, self._exibir_erro, erro)

    def _exibir_erro(self, erro):
        self._parar_animacao(sucesso=False)
        # Mostra até 3 linhas do erro; erros longos são truncados com reticências
        linhas = str(erro).strip().splitlines()
        resumo = "\n".join(linhas[:3])
        if len(linhas) > 3:
            resumo += f"\n… (+{len(linhas)-3} linha(s))"
        self.lbl_status.configure(
            text=f"✖  Erro ao processar:\n{resumo}",
            text_color=COR_ERRO
        )
        self.btn_exportar.pack_forget()

    def executar_exportacao(self, pasta):
        if self.logica.exportar_resultado(pasta):
            self.btn_exportar.pack_forget()
