import os
import shutil
import threading
import platform
import sys
from tkinter import filedialog

from LatitudeLongitude.enderecos import processar_sistema_pastas as _fn_enderecos
from LimpezaArquivo.limpeza import processar_pasta as _fn_limpeza
from OrganizadorTxtDetran.decifradorTxt import processar_arquivos as _fn_detran
from PdfExcelMultas.pdfDeferidoIndeferido import rodar_automacao as _fn_pdf

# Mapeamento: nome do script → função principal do módulo
FERRAMENTAS = {
    "enderecos.py":             _fn_enderecos,
    "limpeza.py":               _fn_limpeza,
    "decifradorTxt.py":         _fn_detran,
    "pdfDeferidoIndeferido.py": _fn_pdf,
}


def obter_diretorio_base():
    """Garante que o caminho raiz seja sempre a pasta onde o .exe ou .py está rodando."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(os.path.dirname(__file__))


class GerenciadorProcessos:
    def __init__(self, callback_sucesso, callback_erro, callback_status):
        self.callback_sucesso = callback_sucesso
        self.callback_erro = callback_erro
        self.callback_status = callback_status
        self._em_execucao = False

    def iniciar_tarefa(self, pasta, nome_do_arquivo):
        if self._em_execucao:
            self.callback_erro("Aguarde o processamento atual terminar.")
            return

        caminho_arquivo_origem = filedialog.askopenfilename(
            title=f"Selecione o arquivo de ENTRADA para: {pasta}",
            filetypes=[("Todos os arquivos", "*.*")]
        )

        if not caminho_arquivo_origem:
            return

        caminho_da_pasta = os.path.join(obter_diretorio_base(), pasta)
        pasta_entrada = os.path.join(caminho_da_pasta, "entrada")

        if not os.path.exists(pasta_entrada):
            os.makedirs(pasta_entrada)

        try:
            shutil.copy(caminho_arquivo_origem, pasta_entrada)
            self._em_execucao = True
            self.callback_status(f"⏳ Processando {pasta}...")

            thread = threading.Thread(
                target=self._executar_ferramenta,
                args=(pasta, nome_do_arquivo, caminho_da_pasta)
            )
            thread.daemon = True
            thread.start()

        except Exception as e:
            self._em_execucao = False
            self.callback_erro(str(e))

    def _executar_ferramenta(self, pasta, nome_do_arquivo, caminho_da_pasta):
        dir_original = os.getcwd()
        try:
            os.chdir(caminho_da_pasta)
            FERRAMENTAS[nome_do_arquivo]()
            self.callback_sucesso(pasta)
        except Exception as e:
            self.callback_erro(str(e))
        finally:
            os.chdir(dir_original)
            self._em_execucao = False

    def exportar_resultado(self, pasta):
        caminho_da_pasta = os.path.join(obter_diretorio_base(), pasta)

        arquivo_gerado = filedialog.askopenfilename(
            initialdir=caminho_da_pasta,
            title="1. Selecione o arquivo GERADO pela ferramenta",
        )

        if not arquivo_gerado:
            return False

        nome_original = os.path.basename(arquivo_gerado)
        destino_salvar = filedialog.asksaveasfilename(
            title="2. Escolha onde salvar o resultado",
            initialfile=nome_original,
            defaultextension=".*"
        )

        if destino_salvar:
            try:
                shutil.copy(arquivo_gerado, destino_salvar)
                self.callback_status("✅ Exportado com Sucesso!", cor="#28a745")
                return True
            except Exception as e:
                self.callback_erro(f"Erro ao exportar: {str(e)}")
                return False
        return False

    def abrir_pasta(self, pasta):
        caminho_da_pasta = os.path.join(obter_diretorio_base(), pasta)
        os.makedirs(caminho_da_pasta, exist_ok=True)

        try:
            if platform.system() == "Windows":
                os.startfile(caminho_da_pasta)
            elif platform.system() == "Darwin":
                import subprocess
                subprocess.Popen(["open", caminho_da_pasta])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", caminho_da_pasta])
        except Exception as e:
            self.callback_erro(f"Erro ao abrir pasta: {e}")
