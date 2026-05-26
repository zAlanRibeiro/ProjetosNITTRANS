# -*- coding: utf-8 -*-
import pdfplumber
import pandas as pd
import re
import shutil
from pathlib import Path
from datetime import datetime

PASTA_ENTRADA   = Path("entrada")
PASTA_BACKUP    = Path("backup")
PASTA_RESULTADOS = Path("resultados")

RE_DATA_ABERTURA = re.compile(r'DATA DE ABERTURA[:\s]+(\d{2}/\d{2}/\d{4})', re.IGNORECASE)

RE_LINHA_DADOS = re.compile(
    r'^\s*(\d+)\s+(\d[PC])\s+(\S+)\s+(N\d+)\s+([A-Z]+)\s*$'
)

RE_RUIDO = re.compile(
    r'EMISS[AÃ]O\s*:|SISTEMA DE MONITORAMENTO|RELAT[OÓ]RIO DE PROCESSOS|'
    r'1a\.\s*INST[AÂ]NCIA|P[áa]gina\s*:|http://|UÁRIO\s*:|ORG[ÃA]O LOTA|'
    r'SEQ\s+REQUERIMENTO|Total de Processos|TOTAL DE PROCESSOS|'
    r'Page\s+\d+|NITEROI|DETRAN|\d{2}/\d{2}/\d{4}\s+A\s+\d{2}/\d{2}/\d{4}',
    re.IGNORECASE
)


def _processar_pdf(caminho_pdf, nome_arquivo):
    dados = []
    data_atual = None

    with pdfplumber.open(str(caminho_pdf)) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto:
                continue

            for linha in texto.split('\n'):
                linha_strip = linha.strip()
                if not linha_strip:
                    continue

                m_data = RE_DATA_ABERTURA.search(linha_strip)
                if m_data:
                    data_atual = m_data.group(1)
                    continue

                if RE_RUIDO.search(linha_strip):
                    continue

                m = RE_LINHA_DADOS.match(linha_strip)
                if m and data_atual:
                    dados.append({
                        'Data de Abertura': data_atual,
                        'SEQ':              m.group(1),
                        'Requerimento':     m.group(2),
                        'Nº Processo':      m.group(3),
                        'Nº Auto':          m.group(4),
                        'Login':            m.group(5),
                        'Arquivo':          nome_arquivo,
                    })

    return dados


def rodar_processos_abertos():
    for pasta in [PASTA_ENTRADA, PASTA_BACKUP, PASTA_RESULTADOS]:
        pasta.mkdir(exist_ok=True)

    arquivos_pdf = list(PASTA_ENTRADA.glob("*.pdf"))
    if not arquivos_pdf:
        print(f"Nenhum PDF encontrado em '{PASTA_ENTRADA}'.")
        return

    todos_dados = []

    for arquivo in arquivos_pdf:
        print(f"\nProcessando: {arquivo.name}")
        dados = _processar_pdf(arquivo, arquivo.name)
        todos_dados.extend(dados)
        print(f"  {len(dados)} registros extraídos.")

        destino = PASTA_BACKUP / arquivo.name
        shutil.move(str(arquivo), str(destino))

    if not todos_dados:
        print("\nNenhum dado válido encontrado nos PDFs.")
        return

    colunas = ['Data de Abertura', 'SEQ', 'Requerimento', 'Nº Processo', 'Nº Auto', 'Login', 'Arquivo']
    df = pd.DataFrame(todos_dados, columns=colunas)

    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_saida = PASTA_RESULTADOS / f"processos_abertos_{data_hora}.xlsx"
    df.to_excel(nome_saida, index=False)

    print(f"\nConcluído! {len(df)} registros salvos em: {nome_saida}")


if __name__ == "__main__":
    rodar_processos_abertos()