# -*- coding: utf-8 -*-
"""
Extrai os relatórios de AUTOS PAGOS do SMIT (Gerencial) em PDF e gera uma
planilha Excel com uma linha por auto pago.

O SMIT emite três relatórios diferentes com o mesmo nome de família, e as
colunas mudam entre eles:

  1. AUTOS PAGOS RENAINF - <UF>  -> tem UF de pagamento, matrícula e FUNSET
  2. AUTOS PAGOS RENAINF         -> só até a UF de pagamento (sem matrícula
                                    nem FUNSET); a UF varia por linha
  3. AUTOS PAGOS                 -> tem valor acumulado, matrícula e FUNSET,
                                    e não tem UF

O layout é detectado pelo título impresso em cada página, então dá para
jogar os três tipos (e vários meses) na pasta de entrada de uma vez: cada
tipo vai para uma aba própria da planilha.

Diferente dos outros leitores de PDF do hub, estes relatórios são tabelas
regulares: cada linha do PDF já é um registro completo. A dificuldade é o
oposto — campos que vêm EM BRANCO (data de vencimento ou matrícula do
agente) fazem a linha "encolher", e uma leitura por ordem das palavras
colocaria o valor na coluna errada. Por isso a extração é feita pela
COORDENADA X de cada palavra.
"""

import re
import shutil
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import pandas as pd
import pdfplumber
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

PASTA_ENTRADA = Path("entrada")
PASTA_BACKUP = Path("backup")
PASTA_RESULTADOS = Path("resultados")

# ==========================================
# 1. Tipos de campo
# ==========================================
# Formato aceito em cada coluna. Uma linha cujo conteúdo não bata com isso
# é descartada e reportada — assim uma mudança de layout aparece na hora,
# em vez de virar dado trocado de coluna na planilha.
TIPOS = {
    'seq': re.compile(r'^\d+$'),
    'auto': re.compile(r'^\S+$'),
    'data': re.compile(r'^\d{2}/\d{2}/\d{4}$'),
    'valor': re.compile(r'^[\d.]+,\d{2}$'),
    'uf': re.compile(r'^[A-Z]{2}$'),
    # A matrícula vem em dígitos, às vezes com dígito verificador
    # ('236165-7'). Fora disso o SMIT ocasionalmente imprime pontuação
    # estranha nela (ex.: '3,09' onde as vizinhas são '309'): como a posição
    # já garante que o valor está na coluna certa, o auto é mantido com o
    # valor original do PDF e apenas sinalizado no relatório de conferência.
    'matricula': re.compile(r'^[\d.,\-]+$'),
}

RE_MATRICULA_OK = re.compile(r'^\d+(-\d+)?$')

# ==========================================
# 2. Layouts conhecidos
# ==========================================
# 'colunas': (nome na planilha, tipo, aceita vir em branco)
# 'limites': fronteiras em X (pontos do PDF) que separam as colunas.
#            Medidas sobre os relatórios reais; nenhuma coluna encosta na
#            vizinha, a menor folga é de ~10pt.
LAYOUTS = [
    {
        'chave': 'renainf_uf',
        'titulo': re.compile(
            r'AUTOS PAGOS RENAINF\s*-\s*(?P<uf>[A-Z]{2})\s*-\s*'
            r'(?P<competencia>\d{2}/\d{4})'
        ),
        'aba': 'Autos Pagos Renainf {uf}',
        'colunas': [
            ('SEQ', 'seq', False),
            ('Nº Auto', 'auto', False),
            ('Data Infração', 'data', False),
            ('Data Vencimento', 'data', True),
            ('Data Pagamento', 'data', False),
            ('Valor Pago (R$)', 'valor', False),
            ('UF de Pgto.', 'uf', False),
            ('Matrícula Agente', 'matricula', True),
            ('FUNSET (R$)', 'valor', False),
        ],
        'limites': [65, 127, 194, 260, 323, 391, 448, 515],
    },
    {
        'chave': 'renainf',
        'titulo': re.compile(
            r'AUTOS PAGOS RENAINF\s*-\s*(?P<competencia>\d{2}/\d{4})'
        ),
        'aba': 'Autos Pagos Renainf',
        'colunas': [
            ('SEQ', 'seq', False),
            ('Nº Auto', 'auto', False),
            ('Data Infração', 'data', False),
            ('Data Vencimento', 'data', True),
            ('Data Pagamento', 'data', False),
            ('Valor Pago (R$)', 'valor', False),
            ('UF de Pgto.', 'uf', False),
        ],
        'limites': [77, 152, 232, 311, 405, 510],
    },
    {
        'chave': 'autos_pagos',
        'titulo': re.compile(
            r'AUTOS PAGOS\s*-\s*(?P<competencia>\d{2}/\d{4})'
        ),
        'aba': 'Autos Pagos',
        'colunas': [
            ('SEQ', 'seq', False),
            ('Nº Auto', 'auto', False),
            ('Data Infração', 'data', False),
            ('Data Vencimento', 'data', True),
            ('Data Pagamento', 'data', False),
            ('Valor Pago (R$)', 'valor', False),
            ('Valor Acumulado (R$)', 'valor', False),
            ('Matrícula Agente', 'matricula', True),
            ('FUNSET (R$)', 'valor', False),
        ],
        'limites': [60, 121, 186, 251, 328, 397, 465, 529],
    },
]

# Vai no fim do nome da planilha, depois do nome do PDF de origem.
SUFIXO_SAIDA = '_Extraido'

COLUNAS_META = ['Arquivo', 'Página', 'Competência', 'Órgão', 'Cód. Agente']

COLUNAS_DATA = {'Data Infração', 'Data Vencimento', 'Data Pagamento'}
# 'Valor Acumulado' é um saldo corrente do relatório, não uma parcela:
# entra na planilha como número, mas nunca é somado no resumo.
COLUNAS_VALOR = {'Valor Pago (R$)', 'FUNSET (R$)', 'Valor Acumulado (R$)'}
COLUNAS_SOMAVEIS = ['Valor Pago (R$)', 'FUNSET (R$)']

# ==========================================
# 3. Regex de cabeçalho de página
# ==========================================
# Parte dos PDFs do SMIT vem com a acentuação quebrada na extração de texto
# ('ÓRGÃO' sai como '?RG?O'), e parte vem correta. Os padrões abaixo evitam
# acentos e usam '.' onde o caractere pode vir corrompido.
RE_LINHA_DADOS = re.compile(r'^\s*\d+\s+\S+\s+\d{2}/\d{2}/\d{4}')
RE_ORGAO = re.compile(r'RG.O\s*:\s*(\S.*?)\s*$')
RE_COD_AGENTE = re.compile(r'COD\.\s*AGENTE\s*:\s*(\S+)')


def _coluna_de(x_centro, limites):
    """Devolve o índice da coluna em que cai uma palavra, pelo seu centro."""
    for indice, limite in enumerate(limites):
        if x_centro < limite:
            return indice
    return len(limites)


def _agrupar_em_linhas(palavras):
    """
    Agrupa as palavras da página por linha (mesma coordenada vertical).
    Devolve uma lista de listas de palavras, de cima para baixo.
    """
    linhas = {}
    for palavra in palavras:
        linhas.setdefault(round(palavra['top']), []).append(palavra)
    return [linhas[chave] for chave in sorted(linhas)]


def _identificar_layout(texto):
    """Devolve (layout, dados_do_titulo) ou (None, None)."""
    for layout in LAYOUTS:
        encontrado = layout['titulo'].search(texto)
        if encontrado:
            return layout, encontrado.groupdict()
    return None, None


def _para_data(texto):
    # Campos em branco chegam aqui como NaN depois de virarem coluna do
    # DataFrame, por isso o teste de tipo em vez de só 'if not texto'.
    if not isinstance(texto, str) or not texto:
        return None
    try:
        return datetime.strptime(texto, '%d/%m/%Y').date()
    except ValueError:
        return None


def _para_numero(texto):
    """'1.234,56' -> 1234.56 (formato brasileiro)."""
    if not isinstance(texto, str) or not texto:
        return None
    try:
        return float(texto.replace('.', '').replace(',', '.'))
    except ValueError:
        return None


# ==========================================
# 4. Extração
# ==========================================
def _ler_linha_de_dados(palavras, layout):
    """
    Distribui as palavras de uma linha pelas colunas do layout.
    Devolve (campos, erro) — 'erro' é None quando a linha está válida.
    """
    colunas = layout['colunas']
    campos = [''] * len(colunas)

    for palavra in palavras:
        indice = _coluna_de((palavra['x0'] + palavra['x1']) / 2,
                            layout['limites'])
        if campos[indice]:
            return None, 'duas palavras na mesma coluna'
        campos[indice] = palavra['text']

    invalidos = []
    for i, (nome, tipo, opcional) in enumerate(colunas):
        valor = campos[i]
        if not valor:
            if not opcional:
                invalidos.append(nome)
        elif not TIPOS[tipo].match(valor):
            invalidos.append(nome)

    if invalidos:
        return None, 'campo fora do padrão: ' + ', '.join(invalidos)
    return campos, None


def extrair_dados_pdf(caminho_pdf):
    """
    Devolve (registros, descartes).
    registros: lista de dicionários, cada um com a chave '_layout'.
    descartes: lista de (arquivo, página, texto_da_linha, motivo).
    """
    nome_arquivo = Path(caminho_pdf).name
    registros = []
    descartes = []

    with pdfplumber.open(str(caminho_pdf)) as pdf:
        total_paginas = len(pdf.pages)

        for num_pagina, pagina in enumerate(pdf.pages, start=1):
            palavras = pagina.extract_words()
            if not palavras:
                continue

            # Cabeçalho da página: layout, competência, órgão e código do
            # agente. Lidos por página porque o relatório troca de agente no
            # meio do documento (e a SEQ reinicia junto).
            layout = dados_titulo = None
            orgao = cod_agente = None

            for linha in _agrupar_em_linhas(palavras):
                linha.sort(key=lambda p: p['x0'])
                texto = ' '.join(p['text'] for p in linha)

                if not RE_LINHA_DADOS.match(texto):
                    if layout is None:
                        layout, dados_titulo = _identificar_layout(texto)
                    encontrado = RE_COD_AGENTE.search(texto)
                    if encontrado:
                        cod_agente = encontrado.group(1)
                    # 'ORGÃO LOTAÇÃO' é do rodapé de usuário, não do órgão
                    if 'LOTA' not in texto.upper():
                        encontrado = RE_ORGAO.search(texto)
                        if encontrado:
                            orgao = encontrado.group(1)
                    continue

                if layout is None:
                    descartes.append((nome_arquivo, num_pagina, texto,
                                      'layout do relatório não reconhecido'))
                    continue

                campos, erro = _ler_linha_de_dados(linha, layout)
                if erro:
                    descartes.append((nome_arquivo, num_pagina, texto, erro))
                    continue

                registro = {
                    '_layout': layout['chave'],
                    '_aba': layout['aba'].format(**dados_titulo),
                    'Arquivo': nome_arquivo,
                    'Página': num_pagina,
                    'Competência': dados_titulo.get('competencia'),
                    'Órgão': orgao,
                    'Cód. Agente': cod_agente,
                }
                for i, (nome, _, _) in enumerate(layout['colunas']):
                    registro[nome] = campos[i] or None
                registros.append(registro)

        print(f"  {total_paginas} páginas, {len(registros)} autos.")

    return registros, descartes


# ==========================================
# 5. Montagem das tabelas
# ==========================================
def _montar_tabelas(registros):
    """
    Agrupa os registros de UM PDF por layout e devolve um OrderedDict
    {nome_da_aba: DataFrame}, na ordem de LAYOUTS. Na prática cada PDF traz
    um único layout, mas o agrupamento cobre o caso de um arquivo misto sem
    misturar colunas de relatórios diferentes na mesma planilha.
    """
    por_saida = OrderedDict()

    for layout in LAYOUTS:
        do_layout = [r for r in registros if r['_layout'] == layout['chave']]
        if not do_layout:
            continue

        colunas = COLUNAS_META + [nome for nome, _, _ in layout['colunas']]
        for aba in dict.fromkeys(r['_aba'] for r in do_layout):
            linhas = [r for r in do_layout if r['_aba'] == aba]
            df = pd.DataFrame(linhas, columns=colunas)
            df['SEQ'] = pd.to_numeric(df['SEQ'], errors='coerce').astype('Int64')
            for coluna in df.columns:
                if coluna in COLUNAS_DATA:
                    df[coluna] = df[coluna].map(_para_data)
                elif coluna in COLUNAS_VALOR:
                    df[coluna] = df[coluna].map(_para_numero)
            por_saida[aba] = df

    return por_saida


def _montar_resumo(df):
    """Totais por competência e código de agente, com linha de total geral."""
    agregacoes = {'Qtd. Autos': ('Nº Auto', 'count')}
    for coluna in COLUNAS_SOMAVEIS:
        if coluna in df.columns:
            agregacoes[coluna] = (coluna, 'sum')

    resumo = (
        df.groupby(['Competência', 'Cód. Agente'], dropna=False)
        .agg(**agregacoes)
        .reset_index()
    )
    # groupby ordena o código como texto ('18' antes de '2'); reordena por número
    resumo = resumo.sort_values(
        ['Competência', 'Cód. Agente'],
        key=lambda coluna: (pd.to_numeric(coluna, errors='coerce')
                            if coluna.name == 'Cód. Agente' else coluna),
    ).reset_index(drop=True)

    total = {'Competência': 'TOTAL GERAL',
             'Qtd. Autos': resumo['Qtd. Autos'].sum()}
    for coluna in COLUNAS_SOMAVEIS:
        if coluna in resumo.columns:
            total[coluna] = resumo[coluna].sum()
    return pd.concat([resumo, pd.DataFrame([total])], ignore_index=True)


# ==========================================
# 6. Geração da planilha
# ==========================================
COR_CABECALHO = '1F4E78'


def _formatar_aba(ws, colunas):
    """Cabeçalho azul, formato de data/moeda, largura e congelamento."""
    fonte_cabecalho = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    fill_cabecalho = PatternFill(
        start_color=COR_CABECALHO, end_color=COR_CABECALHO, fill_type='solid'
    )
    borda_fina = Side(border_style='thin', color='D3D3D3')
    borda = Border(left=borda_fina, right=borda_fina,
                   top=borda_fina, bottom=borda_fina)

    for indice, nome in enumerate(colunas, start=1):
        letra = get_column_letter(indice)
        celula = ws.cell(row=1, column=indice)
        celula.font = fonte_cabecalho
        celula.fill = fill_cabecalho
        celula.alignment = Alignment(
            horizontal='center', vertical='center', wrap_text=True
        )
        celula.border = borda

        if nome in COLUNAS_DATA:
            formato, largura = 'DD/MM/YYYY', 14
        elif nome in COLUNAS_VALOR:
            formato, largura = '#,##0.00', 15
        elif nome == 'Qtd. Autos':
            formato, largura = '#,##0', 13
        else:
            formato, largura = None, max(len(nome) + 4, 12)

        ws.column_dimensions[letra].width = largura
        if formato:
            for linha in range(2, ws.max_row + 1):
                ws.cell(row=linha, column=indice).number_format = formato

    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions


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


def _gerar_excel(df, aba, caminho_saida):
    """Uma planilha com a aba de dados e a aba Resumo."""
    resumo = _montar_resumo(df)
    with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=aba[:31])
        resumo.to_excel(writer, index=False, sheet_name='Resumo')
        _formatar_aba(writer.sheets[aba[:31]], list(df.columns))
        _formatar_aba(writer.sheets['Resumo'], list(resumo.columns))


# ==========================================
# 7. Relatórios de conferência no terminal
# ==========================================
def _relatar_conferencia(df, descartes):
    """Avisos de um único PDF. Devolve True se imprimiu alguma coisa."""
    imprimiu = False

    opcionais = [c for c in ('Data Vencimento', 'Matrícula Agente')
                 if c in df.columns]
    faltando = df[df[opcionais].isna().any(axis=1)] if opcionais else df.iloc[0:0]
    if not faltando.empty:
        imprimiu = True
        print(f'  Campos em branco no PDF de origem'
              f' ({len(faltando)} de {len(df)} autos):')
        for _, linha in faltando.iterrows():
            vazios = [c for c in opcionais if pd.isna(linha[c])]
            print(f"    pág {linha['Página']:>3} | auto {linha['Nº Auto']}"
                  f" | faltou: {', '.join(vazios)}")

    if 'Matrícula Agente' in df.columns:
        matriculas = df['Matrícula Agente'].dropna()
        fora = matriculas[~matriculas.str.match(RE_MATRICULA_OK)]
        if not fora.empty:
            imprimiu = True
            print('  Matrículas fora do padrão (conferir no PDF):')
            for indice in fora.index:
                linha = df.loc[indice]
                print(f"    pág {linha['Página']:>3} | auto {linha['Nº Auto']}"
                      f" | matrícula: {linha['Matrícula Agente']}")

    if descartes:
        imprimiu = True
        print('  Linhas descartadas (layout inesperado):')
        for _, pagina, texto, motivo in descartes[:30]:
            print(f'    pág {pagina:>3} | {motivo}')
            print(f'        {texto}')
        if len(descartes) > 30:
            print(f'    ... e mais {len(descartes) - 30} linha(s).')

    return imprimiu


# ==========================================
# 8. Função principal
# ==========================================
def rodar_autos_pagos():
    for pasta in [PASTA_ENTRADA, PASTA_BACKUP, PASTA_RESULTADOS]:
        pasta.mkdir(exist_ok=True)

    arquivos_pdf = sorted(PASTA_ENTRADA.glob('*.pdf'))
    if not arquivos_pdf:
        print(f"Nenhum PDF encontrado em '{PASTA_ENTRADA}'.")
        return

    # Cada PDF gera a sua própria planilha, com o nome do arquivo de origem
    # mais o sufixo. Nada é misturado entre arquivos: meses diferentes
    # continuam em planilhas diferentes.
    geradas = []

    for numero, arquivo in enumerate(arquivos_pdf, start=1):
        print(f'\n[{numero}/{len(arquivos_pdf)}] Processando: {arquivo.name}')
        registros, descartes = extrair_dados_pdf(arquivo)

        if not registros:
            print('  Nenhum dado válido encontrado neste arquivo.')
            _relatar_conferencia(pd.DataFrame(), descartes)
            shutil.move(str(arquivo), str(PASTA_BACKUP / arquivo.name))
            continue

        tabelas = _montar_tabelas(registros)
        for aba, df in tabelas.items():
            caminho_saida = _caminho_livre(
                PASTA_RESULTADOS / f'{arquivo.stem}{SUFIXO_SAIDA}.xlsx'
            )
            _gerar_excel(df, aba, caminho_saida)
            geradas.append((caminho_saida, df))
            print(f'  -> {caminho_saida.name}'
                  f" | {len(df)} autos | R$ {df['Valor Pago (R$)'].sum():,.2f}")
            _relatar_conferencia(df, [])

        # Os descartes são do arquivo inteiro, não de uma tabela específica
        _relatar_conferencia(pd.DataFrame(), descartes)
        shutil.move(str(arquivo), str(PASTA_BACKUP / arquivo.name))

    if not geradas:
        print('\nNenhum dado válido encontrado nos PDFs.')
        return

    print('\n' + '=' * 60)
    print(f'Concluído! {len(geradas)} planilha(s) em {PASTA_RESULTADOS}:')
    for caminho, df in geradas:
        print(f"  {caminho.name}: {len(df)} autos"
              f" | R$ {df['Valor Pago (R$)'].sum():,.2f}")
    total_autos = sum(len(df) for _, df in geradas)
    total_valor = sum(df['Valor Pago (R$)'].sum() for _, df in geradas)
    print(f'  TOTAL: {total_autos} autos | R$ {total_valor:,.2f}')
    print('=' * 60)


if __name__ == '__main__':
    rodar_autos_pagos()
