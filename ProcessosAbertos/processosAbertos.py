# -*- coding: utf-8 -*-
import pdfplumber
import pandas as pd
import re
import shutil
from pathlib import Path

PASTA_ENTRADA   = Path("entrada")
PASTA_BACKUP    = Path("backup")
PASTA_RESULTADOS = Path("resultados")

# Vai no fim do nome da planilha, depois do nome do PDF de origem.
SUFIXO_SAIDA = "_Extraido"

COLUNAS_SAIDA = ['Arquivo', 'Tipo', 'Período', 'Data de Abertura', 'SEQ',
                 'Requerimento', 'Nº Processo', 'Nº Auto', 'Login']

RE_DATA_ABERTURA = re.compile(r'DATA DE ABERTURA[:\s]+(\d{2}/\d{2}/\d{4})', re.IGNORECASE)

# O código do requerimento muda com o tipo de relatório:
#   1P / 1C -> 1ª Instância        DP / DC -> Defesa Prévia
# Por isso aceita letra OU dígito na primeira posição; exigir dígito fazia o
# relatório de Defesa Prévia inteiro sair vazio, sem erro nenhum.
RE_LINHA_DADOS = re.compile(
    r'^\s*(\d+)\s+([A-Z0-9][PC])\s+(\S+)\s+(N\d+)\s+([A-Z]+)\s*$'
)

# Cabeçalho: identificam de qual relatório e de que período são as linhas.
# Sem isso, ao juntar meses e tipos não dá para distinguir uma linha da outra.
RE_TIPO = re.compile(
    r'(1a\.\s*INST[AÂ]NCIA)|(DEFESA\s+PR[EÉ]VIA)', re.IGNORECASE
)
RE_PERIODO = re.compile(
    r'(\d{2}/\d{2}/\d{4})\s+A\s+(\d{2}/\d{2}/\d{4})'
)

RE_RUIDO = re.compile(
    r'EMISS[AÃ]O\s*:|SISTEMA DE MONITORAMENTO|RELAT[OÓ]RIO DE PROCESSOS|'
    r'1a\.\s*INST[AÂ]NCIA|P[áa]gina\s*:|http://|UÁRIO\s*:|ORG[ÃA]O LOTA|'
    r'SEQ\s+REQUERIMENTO|Total de Processos|TOTAL DE PROCESSOS|'
    r'Page\s+\d+|NITEROI|DETRAN|\d{2}/\d{2}/\d{4}\s+A\s+\d{2}/\d{2}/\d{4}',
    re.IGNORECASE
)


def _caminho_livre(caminho):
    """
    Nunca sobrescreve uma planilha já existente: se o nome estiver ocupado,
    acrescenta ' (2)', ' (3)'... como o Windows faz. Assim, reprocessar o
    mesmo PDF preserva o resultado anterior para comparação.
    """
    if not caminho.exists():
        return caminho
    contador = 2
    while True:
        candidato = caminho.with_name(
            f'{caminho.stem} ({contador}){caminho.suffix}'
        )
        if not candidato.exists():
            return candidato
        contador += 1


def _processar_pdf(caminho_pdf, nome_arquivo):
    dados = []
    data_atual = None
    tipo_atual = None
    periodo_atual = None

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

                # Tipo e período são lidos ANTES do filtro de ruído, que
                # descarta justamente essas duas linhas do cabeçalho.
                m_tipo = RE_TIPO.search(linha_strip)
                if m_tipo:
                    tipo_atual = ('1ª Instância' if m_tipo.group(1)
                                  else 'Defesa Prévia')
                m_periodo = RE_PERIODO.search(linha_strip)
                if m_periodo:
                    periodo_atual = f'{m_periodo.group(1)} a {m_periodo.group(2)}'

                if RE_RUIDO.search(linha_strip):
                    continue

                m = RE_LINHA_DADOS.match(linha_strip)
                if m and data_atual:
                    dados.append({
                        'Arquivo':          nome_arquivo,
                        'Tipo':             tipo_atual,
                        'Período':          periodo_atual,
                        'Data de Abertura': data_atual,
                        'SEQ':              m.group(1),
                        'Requerimento':     m.group(2),
                        'Nº Processo':      m.group(3),
                        'Nº Auto':          m.group(4),
                        'Login':            m.group(5),
                    })

    return dados


def rodar_processos_abertos():
    for pasta in [PASTA_ENTRADA, PASTA_BACKUP, PASTA_RESULTADOS]:
        pasta.mkdir(exist_ok=True)

    arquivos_pdf = list(PASTA_ENTRADA.glob("*.pdf"))
    if not arquivos_pdf:
        print(f"Nenhum PDF encontrado em '{PASTA_ENTRADA}'.")
        return

    # Cada PDF gera a sua própria planilha, com o nome do arquivo de origem
    # mais o sufixo. Nada é misturado entre arquivos: meses e tipos de
    # relatório diferentes continuam em planilhas diferentes.
    geradas = []
    vazios = []

    for arquivo in sorted(arquivos_pdf):
        print(f"\nProcessando: {arquivo.name}")
        dados = _processar_pdf(arquivo, arquivo.name)

        if dados:
            df = pd.DataFrame(dados, columns=COLUNAS_SAIDA)
            caminho_saida = _caminho_livre(
                PASTA_RESULTADOS / f"{arquivo.stem}{SUFIXO_SAIDA}.xlsx"
            )
            df.to_excel(caminho_saida, index=False)
            geradas.append((caminho_saida, df))

            tipos = sorted({d['Tipo'] or '(tipo não identificado)' for d in dados})
            print(f"  {len(dados)} registros extraídos. Tipo: {', '.join(tipos)}")
            print(f"  -> {caminho_saida.name}")
        else:
            # Um PDF que não rende nenhuma linha quase nunca é um relatório
            # vazio: normalmente é um layout que a ferramenta não entendeu.
            # Antes isso passava calado e o arquivo sumia no backup.
            vazios.append(arquivo.name)
            print("  ATENÇÃO: nenhum registro extraído deste arquivo.")

        destino = PASTA_BACKUP / arquivo.name
        shutil.move(str(arquivo), str(destino))

    if vazios:
        print("\n" + "=" * 60)
        print("ARQUIVOS SEM NENHUM REGISTRO (conferir)")
        print("=" * 60)
        for nome in vazios:
            print(f"  {nome}")
        print("Se o PDF tem dados, o layout dele não é o esperado por esta")
        print("ferramenta. Confira o relatório antes de considerar concluído.")
        print("=" * 60)

    if not geradas:
        print("\nNenhum dado válido encontrado nos PDFs.")
        return

    print("\n" + "=" * 60)
    print(f"Concluído! {len(geradas)} planilha(s) em {PASTA_RESULTADOS}:")
    for caminho, df in geradas:
        tipos = ', '.join(sorted(df['Tipo'].dropna().unique()))
        periodos = ', '.join(sorted(df['Período'].dropna().unique()))
        print(f"  {caminho.name}: {len(df)} processos"
              f" | {tipos} | {periodos}")
    print(f"  TOTAL: {sum(len(df) for _, df in geradas)} processos")
    print("=" * 60)


if __name__ == "__main__":
    rodar_processos_abertos()