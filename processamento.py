import os
import shutil
import threading
import platform
import sys
import time
from tkinter import filedialog

from LatitudeLongitude.enderecos import processar_sistema_pastas as _fn_enderecos
from LimpezaArquivo.limpeza import processar_pasta as _fn_limpeza
from OrganizadorTxtDetran.decifradorTxt import processar_arquivos as _fn_detran
from PdfExcelMultas.pdfDeferidoIndeferido import rodar_automacao as _fn_pdf
from ProcessosAbertos.processosAbertos import rodar_processos_abertos as _fn_processos
from DetranLimpo.detranLimpo import rodar_detran_limpo as _fn_detran_limpo

# Mapeamento: nome do script → função principal do módulo
FERRAMENTAS = {
    "enderecos.py":             _fn_enderecos,
    "limpeza.py":               _fn_limpeza,
    "decifradorTxt.py":         _fn_detran,
    "pdfDeferidoIndeferido.py": _fn_pdf,
    "processosAbertos.py":      _fn_processos,
    "detranLimpo.py":           _fn_detran_limpo,
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

        os.makedirs(pasta_entrada, exist_ok=True)

        # Limpa a pasta de entrada antes de copiar o novo arquivo, para não
        # reprocessar arquivos de execuções anteriores que ficaram acumulados.
        for f in os.listdir(pasta_entrada):
            caminho_f = os.path.join(pasta_entrada, f)
            if os.path.isfile(caminho_f):
                os.remove(caminho_f)

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
        dir_original     = os.getcwd()
        pasta_resultados = os.path.join(caminho_da_pasta, "resultados")

        # Marca o instante em que o processamento começa. Em vez de comparar
        # nomes de arquivo (que falha quando o arquivo de saída é sobrescrito
        # com o mesmo nome de uma execução anterior), consideramos "gerado
        # com sucesso" qualquer arquivo em resultados/ cujo horário de
        # modificação seja posterior a este instante.
        inicio = time.time()

        try:
            os.chdir(caminho_da_pasta)
            FERRAMENTAS[nome_do_arquivo]()

            arquivos_gerados = []
            if os.path.exists(pasta_resultados):
                for f in os.listdir(pasta_resultados):
                    if f.startswith("progresso"):
                        continue
                    caminho_f = os.path.join(pasta_resultados, f)
                    if os.path.isfile(caminho_f) and os.path.getmtime(caminho_f) >= inicio:
                        arquivos_gerados.append(f)

            if arquivos_gerados:
                self.callback_sucesso(pasta)
            else:
                self.callback_erro(
                    "Nenhum dado válido encontrado.\n"
                    "Verifique se o arquivo está no formato correto para esta ferramenta."
                )
        except Exception as e:
            self.callback_erro(str(e))
        finally:
            os.chdir(dir_original)
            self._em_execucao = False

    def exportar_resultado(self, pasta):
        caminho_da_pasta  = os.path.join(obter_diretorio_base(), pasta)
        pasta_resultados  = os.path.join(caminho_da_pasta, "resultados")

        # Localiza automaticamente o arquivo mais recente em resultados/
        arquivo_gerado = None
        if os.path.exists(pasta_resultados):
            candidatos = [
                os.path.join(pasta_resultados, f)
                for f in os.listdir(pasta_resultados)
                if os.path.isfile(os.path.join(pasta_resultados, f))
                and not f.startswith("progresso")
            ]
            if candidatos:
                arquivo_gerado = max(candidatos, key=os.path.getmtime)

        if not arquivo_gerado:
            self.callback_erro("Nenhum arquivo encontrado em resultados/.")
            return False

        nome_original = os.path.basename(arquivo_gerado)
        ext = os.path.splitext(nome_original)[1]
        destino_salvar = filedialog.asksaveasfilename(
            title="Salvar resultado",
            initialfile=nome_original,
            defaultextension=ext,
            filetypes=[(f"Arquivo {ext.upper()}", f"*{ext}"), ("Todos", "*.*")]
        )

        if destino_salvar:
            try:
                shutil.copy(arquivo_gerado, destino_salvar)
                self.callback_status("Exportado com sucesso!", cor="#059669")
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