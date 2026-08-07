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
from AutosPagosRenainf.autosPagos import rodar_autos_pagos as _fn_autos_pagos
from DetranLimpo.detranLimpo import rodar_detran_limpo as _fn_detran_limpo
from RemovedorDuplicadasDetran.removerDuplicada import mesclar_arquivos_excel as _fn_remover_duplicadas
from EstatisticasSEI.sei_estatisticas import rodar_sei_estatisticas as _fn_sei
from BloquearPlanilha.bloqueador import rodar_bloqueio as _fn_bloqueio

# Ferramentas que aceitam vários arquivos de uma vez:
#   nome do script -> (título da janela, tipos de arquivo)
SELECAO_MULTIPLA = {
    "removerDuplicada.py": (
        "Selecione os arquivos Excel para mesclar",
        [("Arquivos Excel", "*.xlsx *.xls")],
    ),
    "enderecos.py": (
        "Selecione a(s) planilha(s) para processar (1 ou mais)",
        [("Arquivos compatíveis", "*.xlsx *.xls *.csv")],
    ),
    "autosPagos.py": (
        "Selecione o(s) relatório(s) PDF de Autos Pagos (1 ou mais)",
        [("Arquivos PDF", "*.pdf")],
    ),
    "processosAbertos.py": (
        "Selecione o(s) relatório(s) PDF de Processos Abertos (1 ou mais)",
        [("Arquivos PDF", "*.pdf")],
    ),
    "pdfDeferidoIndeferido.py": (
        "Selecione o(s) relatório(s) PDF de Autos Julgados (1 ou mais)",
        [("Arquivos PDF", "*.pdf")],
    ),
}


def obter_diretorio_base():
    """Garante que o caminho raiz seja sempre a pasta onde o .exe ou .py está rodando."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(os.path.dirname(__file__))

# Lógica incorporada diretamente para evitar erro de importação

class GerenciadorProcessos:
    def __init__(self, callback_sucesso, callback_erro, callback_status):
        self.callback_sucesso = callback_sucesso
        self.callback_erro = callback_erro
        self.callback_status = callback_status
        self._em_execucao = False
        # Arquivos gerados na última execução. Ferramentas que produzem uma
        # planilha por arquivo de entrada geram vários de uma vez.
        self._ultimos_gerados = []

    def iniciar_tarefa(self, pasta, nome_do_arquivo):
        """Prepara o diretório de entrada e inicia a thread de processamento."""
        if self._em_execucao:
            self.callback_erro("Aguarde o processamento atual terminar.")
            return

        arquivos_para_copiar = []
        
        # 1. Abre a janela de seleção de arquivos (Múltipla ou Única)
        if nome_do_arquivo in SELECAO_MULTIPLA:
            titulo, filetypes = SELECAO_MULTIPLA[nome_do_arquivo]
            caminhos = filedialog.askopenfilenames(
                title=titulo,
                filetypes=filetypes
            )
            if not caminhos:
                return # Usuário cancelou
            arquivos_para_copiar = list(caminhos)
        else:
            caminho = filedialog.askopenfilename(
                title=f"Selecione o arquivo de ENTRADA para: {pasta}",
                filetypes=[("Arquivos compatíveis", "*.xlsx *.xls *.csv *.pdf *.txt")]
            )
            if not caminho:
                return # Usuário cancelou
            arquivos_para_copiar = [caminho]

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
            
            # Copia os arquivos selecionados para a pasta da ferramenta
            for arq in arquivos_para_copiar:
                shutil.copy(arq, pasta_entrada)
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
            self.callback_erro(f"Erro ao preparar arquivo(s): {str(e)}")

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

            self._ultimos_gerados = [
                os.path.join(pasta_resultados, f) for f in arquivos_gerados
            ]

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

        # Quando a execução gerou mais de um arquivo (uma planilha por PDF,
        # por exemplo), exportar só o mais recente deixaria o resto para trás:
        # pede uma pasta de destino e copia todos.
        gerados = [c for c in self._ultimos_gerados if os.path.isfile(c)]
        if len(gerados) > 1:
            destino_pasta = filedialog.askdirectory(
                title=f"Selecione a pasta para salvar os {len(gerados)} arquivos"
            )
            if not destino_pasta:
                return False
            try:
                for caminho in gerados:
                    shutil.copy(caminho, destino_pasta)
                self.callback_status(
                    f"{len(gerados)} arquivos exportados!", cor="#059669"
                )
                return True
            except Exception as e:
                self.callback_erro(f"Erro: {str(e)}")
                return False

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
    "autosPagos.py":            _fn_autos_pagos,
    "detranLimpo.py":           _fn_detran_limpo,
    "sei_estatisticas":         _fn_sei,
    "removerDuplicada.py":      _fn_remover_duplicadas,
}