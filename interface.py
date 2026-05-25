import customtkinter as ctk
import os
from PIL import Image
from processamento import GerenciadorProcessos, obter_diretorio_base

# --- PALETA DE CORES INSTITUCIONAL ---
COR_LARANJA_PRINCIPAL = "#FF8C00" # Laranja vibrante (estilo trânsito)
COR_LARANJA_HOVER = "#CC7000"     # Laranja um pouco mais escuro para o clique
COR_TEXTO_BOTAO = "black"         # Preto contrasta muito bem com o laranja
COR_FUNDO_PASTA = "#4A4A4A"       # Cinza escuro para o botão de abrir pasta

class HubApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.geometry("450x600") # Aumentei um pouco para caber o logo confortavelmente
        self.title("Hub de Ferramentas - Gestão e Modernização")
        ctk.set_appearance_mode("dark")
        
        self.logica = GerenciadorProcessos(
            callback_sucesso=self.ao_finalizar_sucesso,
            callback_erro=self.ao_dar_erro,
            callback_status=self.atualizar_status
        )

        self._construir_interface()

    def _construir_interface(self):
        # --- CARREGAMENTO DO LOGOTIPO ---
        # Busca o Logo.png na pasta do projeto (dev) e em _internal/ (PyInstaller 6+)
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
                    size=(370, 105)
                )
                lbl_logo = ctk.CTkLabel(self, image=imagem_logo, text="")
                lbl_logo._logo_ref = imagem_logo  # evita garbage collection
                lbl_logo.pack(pady=(20, 5))
            except Exception:
                caminho_logo = None

        if not caminho_logo:
            lbl_placeholder = ctk.CTkLabel(self, text="[ LOGO NITTRANS ]", font=("Arial", 16, "italic"), text_color="gray")
            lbl_placeholder.pack(pady=(20, 5))

        # Título Principal
        self.titulo = ctk.CTkLabel(self, text="Central de Ferramentas", font=("Arial", 20, "bold"))
        self.titulo.pack(pady=(0, 20))

        # Criação dos botões customizados com as cores laranja
        self._criar_botao_ferramenta("1. Latitude e Longitude", "LatitudeLongitude", "enderecos.py")
        self._criar_botao_ferramenta("2. Limpeza de Arquivos", "LimpezaArquivo", "limpeza.py")
        self._criar_botao_ferramenta("3. Organizador TXT Detran", "OrganizadorTxtDetran", "decifradorTxt.py")
        self._criar_botao_ferramenta("4. PDF e Excel Multas", "PdfExcelMultas", "pdfDeferidoIndeferido.py")

        # Área de Status (Rodapé)
        self.frame_status = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_status.pack(side="bottom", pady=20, fill="x")

        self.lbl_status = ctk.CTkLabel(self.frame_status, text="", font=("Arial", 14, "bold"))
        self.lbl_status.pack(pady=5)

        self.btn_exportar = ctk.CTkButton(self.frame_status, text="💾 Exportar Arquivo Pronto", 
                                          fg_color="#28a745", hover_color="#218838", height=40, text_color="white")

    def _criar_botao_ferramenta(self, texto, pasta, script):
        frame_linha = ctk.CTkFrame(self, fg_color="transparent")
        frame_linha.pack(pady=10, padx=40, fill="x")

        # Botão Principal Laranja
        btn_principal = ctk.CTkButton(frame_linha, text=texto, height=45,
                                      font=("Arial", 14, "bold"),
                                      fg_color=COR_LARANJA_PRINCIPAL, 
                                      hover_color=COR_LARANJA_HOVER,
                                      text_color=COR_TEXTO_BOTAO,
                                      command=lambda: self.preparar_ferramenta(pasta, script))
        btn_principal.pack(side="left", expand=True, fill="x", padx=(0, 10))

        # Botão para abrir a pasta
        btn_pasta = ctk.CTkButton(frame_linha, text="📁", width=45, height=45,
                                  font=("Arial", 18),
                                  fg_color=COR_FUNDO_PASTA, 
                                  hover_color="#333333",
                                  command=lambda: self.logica.abrir_pasta(pasta))
        btn_pasta.pack(side="right")

    def preparar_ferramenta(self, pasta, script):
        self.lbl_status.configure(text="")
        self.btn_exportar.pack_forget()
        self.logica.iniciar_tarefa(pasta, script)

    def atualizar_status(self, mensagem, cor=COR_LARANJA_PRINCIPAL):
        self.lbl_status.configure(text=mensagem, text_color=cor)

    def ao_finalizar_sucesso(self, pasta):
        self.after(0, self._exibir_botao_exportacao, pasta)

    def _exibir_botao_exportacao(self, pasta):
        self.lbl_status.configure(text=f"📄 Arquivo Pronto: {pasta}", text_color="#28a745")
        self.btn_exportar.configure(command=lambda: self.executar_exportacao(pasta))
        self.btn_exportar.pack(pady=10)

    def ao_dar_erro(self, erro):
        self.after(0, self._exibir_erro, erro)

    def _exibir_erro(self, erro):
        self.lbl_status.configure(text=f"❌ {erro}", text_color="red")
        self.btn_exportar.pack_forget()

    def executar_exportacao(self, pasta):
        sucesso = self.logica.exportar_resultado(pasta)
        if sucesso:
            self.btn_exportar.pack_forget()