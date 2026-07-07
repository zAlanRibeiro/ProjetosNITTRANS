# -*- coding: utf-8 -*-
import tkinter as tk
import customtkinter as ctk
import os
import time
from PIL import Image, ImageDraw, ImageTk
from processamento import GerenciadorProcessos, obter_diretorio_base
from TarjarPDF.interface_tarjar import JanelaHigienizar # Importação que você adicionou

SPINNER = ["◐", "◓", "◑", "◒"]

# ── Paleta ────────────────────────────────────────────────────────────────────
COR_VIDRO_BLENDED = "#0A2548" 
COR_FUNDO         = "#EEF2F7"
COR_AZUL          = "#1B5299"
COR_LARANJA       = "#F97316"
COR_LARANJA_HOVER = "#EA580C"
COR_DIVIDER       = "#E2E8F0"
COR_PASTA_BORDER  = "#CBD5E0"
COR_PASTA_HOVER   = "#1C4473" 
COR_PASTA_ICONE   = "#64748B"
COR_SUCESSO       = "#059669"
COR_ERRO          = "#DC2626"

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
    "tarjar":                   "Oculta CPFs, e-mails e telefones de PDFs para adequação à LGPD.", # [NOVO] Dica adicionada
    "sei_estatisticas":         "Extrai dados de tabelas de estatísticas do SEI para Excel."
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

        borda = tk.Frame(self._janela, bg="#475569", padx=1, pady=1)
        borda.pack()

        tk.Label(
            borda, text=self._texto,
            background="#1E293B", foreground="#E2E8F0",
            font=(FONTE, 11), padx=14, pady=9,
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
        self.configure(fg_color=COR_VIDRO_BLENDED) 
        # [MODIFICADO] Altura esticada para 820 para dar "respiro" no layout
        self.geometry("460x820") 
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
        base = obter_diretorio_base()
        
        # ── A MÁGICA DA TRANSPARÊNCIA: O CANVAS ────────────────────────────────
        # [MODIFICADO] Altura do canvas ajustada para 820
        self.canvas = tk.Canvas(self, width=460, height=820, bg=COR_VIDRO_BLENDED, highlightthickness=0)
        self.canvas.place(x=0, y=0)

        # ── IMAGEM DE FUNDO ───────────────────────────────────────────────────
        for caminho_fundo in [os.path.join(base, "FundoAplicativoNITTRANS.png"),
                              os.path.join(base, "_internal", "FundoAplicativoNITTRANS.png")]:
            if os.path.exists(caminho_fundo):
                try:
                    img_original = Image.open(caminho_fundo).convert("RGBA")
                    # [MODIFICADO] Resize ajustado para acompanhar a nova altura
                    img_original = img_original.resize((460, 820), Image.LANCZOS)

                    camada_overlay = Image.new("RGBA", img_original.size, (0, 0, 0, 0))
                    draw = ImageDraw.Draw(camada_overlay)

                    # Caixa semi-transparente do vidro (Aumentada até 780)
                    cor_azul_nittrans_transparente = (8, 25, 55, 110) 
                    draw.rounded_rectangle((10, 100, 450, 780), radius=15, fill=cor_azul_nittrans_transparente)

                    img_mesclada = Image.alpha_composite(img_original, camada_overlay)

                    # Salva em ImageTk e desenha no fundo do Canvas
                    self.tk_fundo = ImageTk.PhotoImage(img_mesclada)
                    self.canvas.create_image(0, 0, anchor="nw", image=self.tk_fundo)
                    break
                except Exception as e:
                    print(f"Erro ao gerar fundo: {e}")
                    pass

        # ── Topbar (Banner Logo Aumentado) ────────────────────────────────────
        for ext in ["jpeg", "jpg", "png"]:
            for caminho in [os.path.join(base, f"LogoNittrans.{ext}"),
                            os.path.join(base, "_internal", f"LogoNittrans.{ext}")]:
                if os.path.exists(caminho):
                    try:
                        img_logo = Image.open(caminho).resize((460, 100), Image.LANCZOS)
                        self.tk_logo = ImageTk.PhotoImage(img_logo)
                        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_logo)
                        break
                    except Exception:
                        pass
            else:
                continue
            break

        # ── Textos de Cabeçalho (Desenhados DIRETAMENTE sobre a imagem) ───────
        self.canvas.create_text(230, 125, text="Departamento de Gestão e Modernização", 
                                font=(FONTE, 15, "bold"), fill="#FFFFFF", anchor="center")
        
        self.canvas.create_text(230, 150, text="Hub de Ferramentas", 
                                font=(FONTE, 15, "bold"), fill="#A3C2F0", anchor="center")

        # ── Botões das Ferramentas (Flutuando sobre o Canvas) ─────────────────
        tools = [
            ("1. Latitude e Longitude",    "LatitudeLongitude",   "enderecos.py",             "normal"),
            ("2. Limpeza de Arquivos",     "LimpezaArquivo",      "limpeza.py",               "normal"),
            ("3. Organizador Txt Detran",  "OrganizadorTxtDetran","decifradorTxt.py",         "normal"),
            ("4. Organizador Detran Limpo","DetranLimpo",         "detranLimpo.py",           "normal"),
            ("5. PDF e Excel Multas",      "PdfExcelMultas",      "pdfDeferidoIndeferido.py", "normal"),
            ("6. Processos Abertos",       "ProcessosAbertos",    "processosAbertos.py",      "normal"),
            ("7. Estatísticas SEI",        "EstatisticasSEI",     "sei_estatisticas",         "normal"),
        ]
        
        start_y = 175
        for i, (nome, pasta, script, estado) in enumerate(tools):
            y_pos = start_y + (i * 52) 
            self._criar_botao_flutuante(nome, pasta, script, y_pos, estado)

        # ── Área de Segurança ─────────────────────────────────────────────────
        # [MODIFICADO] Linha divisória rebaixada para dar margem
        sep_y = 560
        # Linha branca e Texto desenhados diretamente
        self.canvas.create_line(20, sep_y, 440, sep_y, fill="#FFFFFF", width=2)
        self.canvas.create_text(20, sep_y + 15, text="Segurança", font=(FONTE, 11, "bold"), fill="#FFFFFF", anchor="w")

        # Botão 8: Criptografia (Ex 7)
        btn_c = ctk.CTkButton(
            self, text="  8. Criptografar Arquivos", anchor="w", height=45, width=420, corner_radius=10,
            font=(FONTE, 13, "bold"), fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, text_color="#FFFFFF",
            bg_color=COR_VIDRO_BLENDED, command=self._abrir_criptografia
        )
        btn_c.place(x=20, y=sep_y + 35)
        _Tooltip(btn_c, DICAS["criptografia"])

        # Botão 9: Tarjar PDF (Ex 8)
        btn_t = ctk.CTkButton(
            self, text="  9. Tarjar PDF", anchor="w", height=45, width=420, corner_radius=10,
            font=(FONTE, 13, "bold"), fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER, text_color="#FFFFFF",
            bg_color=COR_VIDRO_BLENDED, command=self._abrir_tarjar
        )
        btn_t.place(x=20, y=sep_y + 87)
        _Tooltip(btn_t, DICAS["tarjar"])

        # ── Status e Progresso (Textos Nativos do Canvas) ─────────────────────
        # [MODIFICADO] Descidos bastante (de 650 para 700) para criar o "respiro"
        self.id_spinner = self.canvas.create_text(20, 700, text="", font=(FONTE, 13, "bold"), fill="#FFB347", anchor="w")
        self.id_status = self.canvas.create_text(20, 715, text="", font=(FONTE, 12), fill="#FFFFFF", anchor="nw", width=420)

        self.progress_bar = ctk.CTkProgressBar(self, mode="determinate", progress_color=COR_LARANJA, fg_color="#FFFFFF", height=8, corner_radius=4, bg_color=COR_VIDRO_BLENDED, width=420)
        self.progress_bar.set(0)

        self.btn_exportar = ctk.CTkButton(
            self, text="💾   Exportar Arquivo Pronto", fg_color=COR_SUCESSO, hover_color="#047857",
            text_color="white", height=45, width=420, corner_radius=6, font=(FONTE, 14, "bold"), bg_color=COR_VIDRO_BLENDED
        )

        # ── Rodapé ────────────────────────────────────────────────────────────
        # [MODIFICADO] Descido para a nova base da tela (785 a 820)
        self.canvas.create_rectangle(0, 785, 460, 820, fill="#0A1E3F", outline="")
        self.canvas.create_text(230, 802, text="NITTRANS  ·  Niterói Transporte e Trânsito  ·  Prefeitura Municipal de Niterói", 
                                font=(FONTE, 9), fill="#FFFFFF", anchor="center")

        # ── Variáveis de Estado ───────────────────────────────────────────────
        self._spinner_after  = None
        self._progress_after = None
        self._start_time     = None
        self._spinner_idx    = 0
        self._progress_val   = 0.0
        self._pasta_atual    = ""

    def _criar_botao_flutuante(self, nome, pasta, script, y_pos, estado="normal"):
        btn = ctk.CTkButton(
            self, text=f"  {nome}", anchor="w", height=45, width=370, corner_radius=10,
            font=(FONTE, 13, "bold"), fg_color=COR_LARANJA, hover_color=COR_LARANJA_HOVER,
            text_color="#FFFFFF", bg_color=COR_VIDRO_BLENDED,
            command=lambda p=pasta, s=script: self.preparar_ferramenta(p, s),
            state=estado
        )
        btn.place(x=20, y=y_pos)
        if script in DICAS: _Tooltip(btn, DICAS[script])

        btn_pasta = ctk.CTkButton(
            self, text="📁", width=45, height=45, corner_radius=10,
            fg_color="transparent", bg_color=COR_VIDRO_BLENDED, border_width=1, border_color="#FFFFFF",
            hover_color=COR_PASTA_HOVER, text_color="#FFFFFF", font=(FONTE, 16),
            command=lambda p=pasta: self.logica.abrir_pasta(p),
            state=estado 
        )
        btn_pasta.place(x=395, y=y_pos)

    def _abrir_criptografia(self):
        from Criptografia.gui import AppToplevel
        AppToplevel(self)

    def _abrir_tarjar(self):
        JanelaHigienizar(self)

    def _iniciar_animacao(self, nome):
        self._start_time    = time.time()
        self._spinner_idx   = 0
        self._progress_val  = 0.0
        self.progress_bar.set(0)
        # [MODIFICADO] Barra de progresso reposicionada para acompanhar o novo layout
        self.progress_bar.place(x=20, y=715)
        self._tick_spinner(nome)
        self._tick_progress()

    def _tick_spinner(self, nome):
        frame  = SPINNER[self._spinner_idx % len(SPINNER)]
        elapsed = int(time.time() - self._start_time)
        mins, secs = divmod(elapsed, 60)
        tempo = f"{mins}m {secs:02d}s" if mins else f"{secs}s"
        pct   = int(self._progress_val * 100)
        
        self.canvas.itemconfig(self.id_spinner, text=f"{frame}  Processando {nome}...  {pct}%  ({tempo})")
        
        self._spinner_idx  += 1
        self._spinner_after = self.after(120, self._tick_spinner, nome)

    def _tick_progress(self):
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
            
        self.canvas.itemconfig(self.id_spinner, text="")
        
        if sucesso:
            self.progress_bar.set(1.0)
            self.after(600, lambda: self.progress_bar.place_forget())
        else:
            self.progress_bar.place_forget()

    def preparar_ferramenta(self, pasta, script):
        self._pasta_atual = pasta
        self.canvas.itemconfig(self.id_status, text="")
        self.btn_exportar.place_forget()
        self.logica.iniciar_tarefa(pasta, script)

    def atualizar_status(self, mensagem, cor=COR_LARANJA):
        self._iniciar_animacao(self._pasta_atual)

    def ao_finalizar_sucesso(self, pasta):
        self.after(0, self._exibir_sucesso, pasta)

    def _exibir_sucesso(self, pasta):
        elapsed = int(time.time() - self._start_time) if self._start_time else 0
        mins, secs = divmod(elapsed, 60)
        tempo = f"{mins}m {secs:02d}s" if mins else f"{secs}s"
        self._parar_animacao(sucesso=True)
        
        self.canvas.itemconfig(self.id_status, text=f"✔  Concluído em {tempo} — {pasta}", fill="#4ADE80")
        self.btn_exportar.configure(command=lambda: self.executar_exportacao(pasta))
        # [MODIFICADO] Botão de Exportar centralizado com espaçamento
        self.btn_exportar.place(x=20, y=735)

    def ao_dar_erro(self, erro):
        self.after(0, self._exibir_erro, erro)

    def _exibir_erro(self, erro):
        self._parar_animacao(sucesso=False)
        linhas = str(erro).strip().splitlines()
        resumo = "\n".join(linhas[:3])
        if len(linhas) > 3:
            resumo += f"\n… (+{len(linhas)-3} linha(s))"
            
        self.canvas.itemconfig(self.id_status, text=f"✖  Erro ao processar:\n{resumo}", fill="#F87171")
        self.btn_exportar.place_forget()

    def executar_exportacao(self, pasta):
        if self.logica.exportar_resultado(pasta):
            self.btn_exportar.place_forget()