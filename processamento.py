import os
import shutil
import threading
import platform
import sys
import time
from tkinter import filedialog
import pdfplumber
import pandas as pd

# Importações das suas ferramentas existentes
from LatitudeLongitude.enderecos import processar_sistema_pastas as _fn_enderecos
from LimpezaArquivo.limpeza import processar_pasta as _fn_limpeza
from OrganizadorTxtDetran.decifradorTxt import processar_arquivos as _fn_detran
from PdfExcelMultas.pdfDeferidoIndeferido import rodar_automacao as _fn_pdf
from ProcessosAbertos.processosAbertos import rodar_processos_abertos as _fn_processos
from DetranLimpo.detranLimpo import rodar_detran_limpo as _fn_detran_limpo

def obter_diretorio_base():
    """Garante que o caminho raiz seja sempre a pasta onde o .exe ou .py está rodando."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(os.path.dirname(__file__))

# Lógica incorporada diretamente para evitar erro de importação
class ProcessadorSEI:
    @staticmethod
    @staticmethod
    @staticmethod
    def processar_pdf(caminho_pdf, destino_xlsx):
        import pdfplumber
        import pandas as pd

        linhas_excel = []

        with pdfplumber.open(caminho_pdf) as pdf:

            for pagina in pdf.pages:

                # Todas as palavras da página com posição
                palavras = pagina.extract_words(
                    x_tolerance=2,
                    y_tolerance=2,
                    keep_blank_chars=False
                )

                # Todas as tabelas encontradas
                tabelas = pagina.find_tables()

                for tabela in tabelas:

                    # Onde a tabela começa
                    x0, top, x1, bottom = tabela.bbox

                    # Procura o texto imediatamente acima da tabela
                    acima = [p for p in palavras if p["bottom"] < top]

                    titulo = "Tabela"

                    if acima:

                        # Agrupa palavras por linha (posição Y)
                        linhas = {}

                        for p in acima:
                            y = round(p["top"], 1)
                            linhas.setdefault(y, []).append(p)

                        ultima_linha = max(linhas.keys())

                        palavras_linha = sorted(
                            linhas[ultima_linha],
                            key=lambda x: x["x0"]
                        )

                        titulo = " ".join(p["text"] for p in palavras_linha)

                    # Escreve o título
                    linhas_excel.append([titulo])
                    linhas_excel.append(["-" * 80])

                    dados = tabela.extract()

                    if not dados:
                        continue

                    # Cabeçalho
                    linhas_excel.append(dados[0])

                    # Dados
                    for linha in dados[1:]:

                        if not linha:
                            continue

                        if all(c is None or str(c).strip() == "" for c in linha):
                            continue

                        linhas_excel.append(linha)

                    # Linha em branco entre tabelas
                    linhas_excel.append([])

        if not linhas_excel:
            return False, None

        largura = max(len(l) for l in linhas_excel)

        linhas_padronizadas = []

        for linha in linhas_excel:
            linha = list(linha)
            while len(linha) < largura:
                linha.append("")
            linhas_padronizadas.append(linha)

        df = pd.DataFrame(linhas_padronizadas)

        df.to_excel(destino_xlsx, index=False, header=False)

        return True, destino_xlsx

    @staticmethod
    def rodar_sei_estatisticas():
        # Caminho raiz e subpastas
        pasta_raiz = os.path.join(obter_diretorio_base(), "EstatisticasSEI")
        pasta_entrada = os.path.join(pasta_raiz, "entrada")
        pasta_resultados = os.path.join(pasta_raiz, "resultados")
        
        # CRÍTICO: Garante que as pastas existem antes de tentar usá-las
        os.makedirs(pasta_entrada, exist_ok=True)
        os.makedirs(pasta_resultados, exist_ok=True)
        
        # Agora sim, lista os arquivos com segurança
        arquivos = [f for f in os.listdir(pasta_entrada) if f.endswith(".pdf")]
        
        if not arquivos:
            # Se não houver arquivo, avisa onde você deve colocar o PDF
            raise FileNotFoundError(f"Coloque o arquivo PDF na pasta:\n{pasta_entrada}")
        
        caminho_pdf = os.path.join(pasta_entrada, arquivos[0])
        caminho_saida = os.path.join(pasta_resultados, "Relatorio_Consolidado.xlsx")
        
        # Executa o processamento
        ok, _ = ProcessadorSEI.processar_pdf(caminho_pdf, caminho_saida)

        if not ok:
            raise Exception("Nenhuma tabela foi encontrada no PDF.")

class GerenciadorProcessos:
    def __init__(self, callback_sucesso, callback_erro, callback_status):
        self.callback_sucesso = callback_sucesso
        self.callback_erro = callback_erro
        self.callback_status = callback_status
        self._em_execucao = False

    def iniciar_tarefa(self, pasta, nome_do_arquivo):
        """Prepara o diretório de entrada e inicia a thread de processamento."""
        if self._em_execucao:
            self.callback_erro("Aguarde o processamento atual terminar.")
            return

        # 1. Abre a janela de seleção de arquivos
        caminho_arquivo_origem = filedialog.askopenfilename(
            title=f"Selecione o arquivo de ENTRADA para: {pasta}",
            filetypes=[("Arquivos compatíveis", "*.xlsx *.xls *.csv *.pdf *.txt")]
        )

        if not caminho_arquivo_origem:
            return

        # 2. Define os caminhos absolutos
        caminho_da_pasta = os.path.join(obter_diretorio_base(), pasta)
        pasta_entrada = os.path.join(caminho_da_pasta, "entrada")
        os.makedirs(pasta_entrada, exist_ok=True)

        print(f"DEBUG: Pasta de entrada mapeada em: {pasta_entrada}")

        # 3. Limpeza e Cópia com verificação de erros
        try:
            # Remove arquivos antigos para evitar conflitos
            for f in os.listdir(pasta_entrada):
                caminho_antigo = os.path.join(pasta_entrada, f)
                if os.path.isfile(caminho_antigo):
                    os.remove(caminho_antigo)
            
            # Copia o arquivo selecionado para a pasta da ferramenta
            shutil.copy(caminho_arquivo_origem, pasta_entrada)
            print(f"DEBUG: Arquivo copiado com sucesso para {pasta_entrada}")
            
            # 4. Inicia o processamento em background
            self._em_execucao = True
            self.callback_status(f"⏳ Processando {pasta}...")

            thread = threading.Thread(
                target=self._executar_ferramenta,
                args=(pasta, nome_do_arquivo, caminho_da_pasta)
            )
            thread.daemon = True
            thread.start()

        except Exception as e:
            print(f"ERRO CRÍTICO NO INICIAR_TAREFA: {e}")
            self._em_execucao = False
            self.callback_erro(f"Erro ao preparar arquivo: {str(e)}")

    def _executar_ferramenta(self, pasta, nome_do_arquivo, caminho_da_pasta):
        dir_original = os.getcwd()
        pasta_resultados = os.path.join(caminho_da_pasta, "resultados")
        inicio = time.time()

        try:
            os.chdir(caminho_da_pasta)
            FERRAMENTAS[nome_do_arquivo]()

            arquivos_gerados = []
            if os.path.exists(pasta_resultados):
                for f in os.listdir(pasta_resultados):
                    if f.startswith("progresso"): continue
                    caminho_f = os.path.join(pasta_resultados, f)
                    if os.path.isfile(caminho_f) and os.path.getmtime(caminho_f) >= inicio:
                        arquivos_gerados.append(f)

            if arquivos_gerados:
                self.callback_sucesso(pasta)
            else:
                self.callback_erro("Nenhum dado válido encontrado.")
        except Exception as e:
            self.callback_erro(str(e))
        finally:
            os.chdir(dir_original)
            self._em_execucao = False

    def exportar_resultado(self, pasta):
        caminho_da_pasta = os.path.join(obter_diretorio_base(), pasta)
        pasta_resultados = os.path.join(caminho_da_pasta, "resultados")
        arquivo_gerado = None
        if os.path.exists(pasta_resultados):
            candidatos = [os.path.join(pasta_resultados, f) for f in os.listdir(pasta_resultados) 
                          if os.path.isfile(os.path.join(pasta_resultados, f)) and not f.startswith("progresso")]
            if candidatos: arquivo_gerado = max(candidatos, key=os.path.getmtime)
        
        if not arquivo_gerado:
            self.callback_erro("Nenhum arquivo encontrado em resultados/.")
            return False
        
        nome_original = os.path.basename(arquivo_gerado)
        ext = os.path.splitext(nome_original)[1]
        destino_salvar = filedialog.asksaveasfilename(initialfile=nome_original, defaultextension=ext)
        if destino_salvar:
            try:
                shutil.copy(arquivo_gerado, destino_salvar)
                self.callback_status("Exportado!", cor="#059669")
                return True
            except Exception as e:
                self.callback_erro(f"Erro: {str(e)}")
                return False
        return False

    def abrir_pasta(self, pasta):
        caminho_da_pasta = os.path.join(obter_diretorio_base(), pasta)
        os.makedirs(caminho_da_pasta, exist_ok=True)
        try:
            if platform.system() == "Windows": os.startfile(caminho_da_pasta)
            else:
                import subprocess
                subprocess.Popen(["xdg-open", caminho_da_pasta])
        except Exception as e:
            self.callback_erro(f"Erro: {e}")

# Mapeamento definido no final para garantir que as funções existem
FERRAMENTAS = {
    "enderecos.py":             _fn_enderecos,
    "limpeza.py":               _fn_limpeza,
    "decifradorTxt.py":         _fn_detran,
    "pdfDeferidoIndeferido.py": _fn_pdf,
    "processosAbertos.py":      _fn_processos,
    "detranLimpo.py":           _fn_detran_limpo,
    "sei_estatisticas":         ProcessadorSEI.rodar_sei_estatisticas,
}