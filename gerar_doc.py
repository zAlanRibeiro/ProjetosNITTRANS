# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

LARANJA     = RGBColor(0xFF, 0x8C, 0x00)
AZUL_ESCURO = RGBColor(0x1F, 0x35, 0x64)

doc = Document()

for section in doc.sections:
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin   = Cm(3)
    section.right_margin  = Cm(2.5)

normal = doc.styles['Normal']
normal.font.name = 'Calibri'
normal.font.size = Pt(11)


def add_heading(text, level=1, color=AZUL_ESCURO):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18 if level == 1 else 12)
    p.paragraph_format.space_after  = Pt(6)
    run = p.add_run(text)
    run.bold = True
    run.font.color.rgb = color
    run.font.size = Pt({1: 16, 2: 13, 3: 12}.get(level, 11))
    run.font.name = 'Calibri'
    return p


def add_para(text='', parts=None, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if parts:
        for t, b in parts:
            r = p.add_run(t)
            r.bold = b
            r.font.name = 'Calibri'
            r.font.size = Pt(11)
    else:
        r = p.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(11)
    return p


def add_bullet(text):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(11)
    return p


def add_code(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after  = Pt(1)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.left_indent  = Cm(1)
    r = p.add_run(text)
    r.font.name = 'Courier New'
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x20, 0x20, 0x20)
    return p


def shade_cell(cell, fill_hex):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  fill_hex)
    tcPr.append(shd)


def add_table(headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.LEFT

    hdr_row = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.paragraphs[0].clear()
        run = cell.paragraphs[0].add_run(h)
        run.bold = True
        run.font.name = 'Calibri'
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade_cell(cell, 'FF8C00')

    for ri, row_data in enumerate(rows):
        row = table.rows[ri + 1]
        fill = 'F5F5F5' if ri % 2 == 0 else 'FFFFFF'
        for ci, val in enumerate(row_data):
            cell = row.cells[ci]
            cell.paragraphs[0].clear()
            run = cell.paragraphs[0].add_run(val)
            run.font.name = 'Calibri'
            run.font.size = Pt(10)
            shade_cell(cell, fill)

    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Cm(w)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return table


# =============================================================
# CAPA
# =============================================================
doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('Hub de Ferramentas NITTRANS')
r.bold = True
r.font.size = Pt(26)
r.font.color.rgb = LARANJA
r.font.name = 'Calibri'

p2 = doc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r2 = p2.add_run('Documentacao Tecnica')
r2.font.size = Pt(16)
r2.font.color.rgb = AZUL_ESCURO
r2.font.name = 'Calibri'

doc.add_paragraph()
for chave, valor in [
    ('Sistema',    'Hub de Ferramentas - Gestao e Modernizacao'),
    ('Orgao',      'NITTRANS - Niteroi Transporte S.A. / Prefeitura de Niteroi/RJ'),
    ('Versao',     '1.0'),
    ('Tecnologia', 'Python 3.13 - CustomTkinter - PyInstaller - Inno Setup'),
    ('Ano',        '2026'),
    ('Desenvolvedor', 'Alan Doyle Costa Ribeiro'),
    ('Cargo',      'Estagiario - Gestao e Modernizacao'),
]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p.add_run(f'{chave}: ')
    r1.bold = True
    r1.font.name = 'Calibri'
    r1.font.size = Pt(11)
    r2 = p.add_run(valor)
    r2.font.name = 'Calibri'
    r2.font.size = Pt(11)

doc.add_page_break()

# =============================================================
# 1. VISAO GERAL
# =============================================================
add_heading('1. Visao Geral', 1)
add_para(
    'O Hub de Ferramentas NITTRANS e uma aplicacao desktop Windows com interface grafica '
    '(modo escuro) que centraliza cinco automacoes de dados utilizadas internamente pela '
    'equipe tecnica. Cada ferramenta opera de forma independente: o usuario seleciona o '
    'arquivo de entrada, a ferramenta processa e gera o resultado, que pode ser exportado '
    'para qualquer destino.'
)
add_para(
    'A aplicacao nao exige instalacao de Python nem de nenhuma dependencia: tudo esta '
    'empacotado no instalador .exe, que instala sem necessidade de privilegios de administrador.'
)

# =============================================================
# 2. ESTRUTURA DE PASTAS
# =============================================================
add_heading('2. Estrutura de Pastas', 1)
for linha in [
    'ProjetosNITTRANS/',
    '|-- main.py                       <- Ponto de entrada',
    '|-- interface.py                  <- Interface grafica (CustomTkinter)',
    '|-- processamento.py              <- Orquestrador (threads e pastas)',
    '|-- hub.spec                      <- Configuracao do PyInstaller',
    '|-- version_info.txt              <- Metadados de autoria do .exe',
    '|-- build.ps1                     <- Script de build automatizado',
    '|-- Logo.png / logo.ico           <- Identidade visual',
    '|',
    '|-- LatitudeLongitude/',
    '|   |-- enderecos.py              <- Ferramenta 1',
    '|   |-- cache_enderecos.json      <- Cache de geocodificacao (pre-preenchido)',
    '|-- LimpezaArquivo/',
    '|   |-- limpeza.py               <- Ferramenta 2',
    '|-- OrganizadorTxtDetran/',
    '|   |-- decifradorTxt.py         <- Ferramenta 3',
    '|-- PdfExcelMultas/',
    '|   |-- pdfDeferidoIndeferido.py <- Ferramenta 4',
    '|-- ProcessosAbertos/',
    '    |-- processosAbertos.py      <- Ferramenta 5',
]:
    add_code(linha)

doc.add_paragraph()
add_para('Cada ferramenta cria automaticamente tres subpastas ao ser executada:')
add_table(
    ['Subpasta', 'Funcao'],
    [
        ['entrada/',     'Arquivo enviado pelo usuario para processar'],
        ['backup/',      'Copia do arquivo original apos o processamento'],
        ['resultados/',  'Arquivo(s) gerado(s) pela ferramenta'],
    ],
    col_widths=[4, 11]
)

# =============================================================
# 3. FLUXO DE USO
# =============================================================
add_heading('3. Fluxo de Uso', 1)
for passo in [
    '1. Usuario clica em uma das ferramentas na tela principal.',
    '2. Um dialogo de selecao de arquivo abre.',
    '3. O arquivo escolhido e copiado para a pasta entrada/ da ferramenta.',
    '4. O processamento roda em uma thread separada (interface nao trava).',
    '5. Ao finalizar, aparece o botao "Exportar Arquivo Pronto".',
    '6. O usuario salva o resultado onde quiser via dialogo de salvamento.',
    '7. O botao de pasta ao lado de cada ferramenta abre o Explorer na pasta da ferramenta.',
]:
    add_bullet(passo)
doc.add_paragraph()

# =============================================================
# 4. FERRAMENTAS
# =============================================================
add_heading('4. Ferramentas', 1)

# --- 4.1 ---
add_heading('4.1  Latitude e Longitude', 2, LARANJA)
add_para(parts=[('Arquivo: ', True), ('LatitudeLongitude/enderecos.py', False)])

add_heading('O que faz', 3)
add_para(
    'Recebe uma planilha com coordenadas geograficas (latitude/longitude) e enriquece '
    'cada linha com o endereco completo correspondente (rua, bairro, numero, cidade, '
    'CEP, estado) via geocodificacao reversa usando a API publica OpenStreetMap/Nominatim.'
)

add_heading('Arquivos aceitos', 3)
add_table(
    ['Formato', 'Extensao'],
    [
        ['Planilha Excel', '.xlsx, .xls'],
        ['CSV com separador ponto-e-virgula', '.csv'],
    ],
    col_widths=[8, 7]
)

add_heading('Como processa', 3)
add_bullet('Identifica as colunas de latitude e longitude por nome (latitude, lat, y, longitude, lon, lng, x) ou por faixa de valores numericos quando os nomes nao sao padrao.')
add_bullet('Usa a API Nominatim (OpenStreetMap) com RateLimiter (minimo 1,2 s entre requisicoes) para respeitar os limites da API gratuita.')
add_bullet('Mantem cache local (cache_enderecos.json) — coordenadas ja consultadas nao sao buscadas novamente, poupando tempo em reprocessamentos. O instalador ja inclui um cache pre-preenchido com enderecos ja conhecidos.')
add_bullet('O cache e salvo a cada 10 novas entradas para evitar perda em caso de interrupcao.')
add_bullet('Coordenadas sem endereco encontrado sao registradas em coordenadas_nao_encontradas.txt.')

add_heading('Colunas adicionadas ao arquivo de saida', 3)
add_table(
    ['Coluna', 'Conteudo'],
    [
        ['Endereco_Rua',  'Nome da rua/logradouro'],
        ['Bairro',        'Bairro'],
        ['Numero_Imovel', 'Numero do imovel'],
        ['Cidade',        'Municipio'],
        ['CEP',           'Codigo postal'],
        ['Estado',        'Estado'],
    ],
    col_widths=[5, 10]
)

# --- 4.2 ---
add_heading('4.2  Limpeza de Arquivos', 2, LARANJA)
add_para(parts=[('Arquivo: ', True), ('LimpezaArquivo/limpeza.py', False)])

add_heading('O que faz', 3)
add_para(
    'Recebe planilhas de cadastro ou fiscalizacao e realiza limpeza profunda dos dados: '
    'corrige texto mal codificado (mojibake), padroniza nomes de logradouros, normaliza '
    'capitalizacao, valida enderecos via geocodificacao e gera relatorio de todas as '
    'alteracoes realizadas.'
)

add_heading('Arquivos aceitos', 3)
add_table(
    ['Formato', 'Extensao'],
    [
        ['Planilha Excel', '.xlsx, .xls'],
        ['CSV (separadores ; ou ,)', '.csv'],
    ],
    col_widths=[8, 7]
)

add_heading('Como processa', 3)
add_bullet('Tenta automaticamente multiplas combinacoes de encoding (utf-8, cp1252, latin-1) e separador ate encontrar leitura valida (minimo 15 colunas).')
add_bullet('Calcula hash SHA-256 do arquivo original para rastreabilidade.')
add_bullet('Corrige mojibake por re-decodificacao latin1-utf-8, com ate 5 passagens iterativas.')
add_bullet('Aplica capitalizacao inteligente nas colunas de Titulo (pos. 1), Endereco (pos. 6) e Bairro (pos. 14) — artigos "da", "de", "do" ficam em minusculo.')
add_bullet('Expande abreviacoes: R. -> Rua, Av. -> Av., Estr. -> Estrada, Tv. -> Travessa, Pca. -> Praca.')
add_bullet('Valida endereco e bairro via Nominatim para obter o nome oficial do logradouro em Niteroi/RJ.')
add_bullet('Detecta corrupcao residual ao final, alertando colunas com padroes suspeitos.')

add_heading('Saidas geradas', 3)
add_table(
    ['Arquivo', 'Conteudo'],
    [
        ['{nome}_LIMPO.xlsx',     'Planilha com todos os dados corrigidos'],
        ['{nome}_RELATORIO.xlsx', 'Registro de cada alteracao: campo, valor original e corrigido'],
    ],
    col_widths=[6, 9]
)

# --- 4.3 ---
add_heading('4.3  Organizador TXT Detran', 2, LARANJA)
add_para(parts=[('Arquivo: ', True), ('OrganizadorTxtDetran/decifradorTxt.py', False)])

add_heading('O que faz', 3)
add_para(
    'Converte arquivos .txt de posicao fixa exportados pelo sistema do DETRAN/RJ '
    'em planilhas Excel estruturadas e legiveis, extraindo cada campo pela sua '
    'posicao exata no layout do arquivo.'
)

add_heading('Arquivos aceitos', 3)
add_table(
    ['Formato', 'Extensao'],
    [['Arquivo de texto posicional (layout fixo)', '.txt']],
    col_widths=[10, 5]
)

add_heading('Layout do arquivo — campos por posicao de caractere', 3)
add_table(
    ['Posicao', 'Campo'],
    [
        ['0 - 6',     'Codigo do Orgao Atuador'],
        ['6 - 9',     'Codigo da Infracao'],
        ['11 - 71',   'Descricao da Infracao'],
        ['71 - 91',   'Tipo de Enquadramento'],
        ['91 - 103',  'Auto'],
        ['103 - 111', 'Data (AAAAMMDD -> DD/MM/AAAA)'],
        ['111 - 117', 'Hora (HHMMSS -> HH:MM:SS)'],
        ['158 - 167', 'Valor da Infracao (centavos -> R$ 0,00)'],
        ['167 - 174', 'Situacao'],
        ['174 - 181', 'Placa do Veiculo'],
        ['181 - 192', 'Renavam'],
        ['192 - 217', 'Marca/Modelo'],
        ['219 - 233', 'CPF/Identidade'],
        ['233 - 293', 'Nome do Infrator'],
        ['293 - 337', 'Logradouro'],
        ['337 - 345', 'CEP'],
        ['345 - 388', 'Municipio'],
    ],
    col_widths=[4, 11]
)

add_heading('Saida gerada', 3)
add_table(
    ['Arquivo', 'Conteudo'],
    [['{nome}_normalizado.xlsx', 'Planilha com todos os campos em colunas separadas']],
    col_widths=[6, 9]
)

# --- 4.4 ---
add_heading('4.4  PDF e Excel Multas', 2, LARANJA)
add_para(parts=[('Arquivo: ', True), ('PdfExcelMultas/pdfDeferidoIndeferido.py', False)])

add_heading('O que faz', 3)
add_para(
    'Extrai dados de processos julgados (Deferido/Indeferido) a partir de relatorios PDF '
    'gerados pelo sistema GAIDE/NITEROI e consolida todos os registros em uma unica '
    'planilha Excel.'
)

add_heading('Arquivos aceitos', 3)
add_table(
    ['Formato', 'Extensao'],
    [['Relatorio PDF do sistema GAIDE', '.pdf']],
    col_widths=[10, 5]
)

add_heading('Desafios do PDF e como sao tratados', 3)
add_bullet('CNPJ quebrado em duas linhas (ex: 30.069.314/0001- + 01): reunificado antes da extracao.')
add_bullet('Placa isolada abaixo do nome do proprietario: fundida a linha correta.')
add_bullet('Sobrenome do relator em linha separada: lista configuravel de sobrenomes conhecidos.')
add_bullet('Texto de infracao espalhado por multiplas linhas: concatenado ate o proximo marcador.')
add_bullet('Linhas de cabecalho e rodape (emissao, pagina, usuario, DETRAN) descartadas por regex.')

add_heading('Como processa', 3)
add_bullet('Le todas as paginas do PDF com pdfplumber.')
add_bullet('Aplica as correcoes de quebra de linha em sequencia.')
add_bullet('Particiona o texto em blocos por registro — cada bloco inicia na linha onde aparece uma placa (formato AAA0A00 ou AAA0000).')
add_bullet('Extrai de cada bloco: CPF/CNPJ, Proprietario, Placa, Processo, Datas, Resultado e Relator.')
add_bullet('Propaga CPF/CNPJ para registros consecutivos do mesmo proprietario sem o campo explicito.')
add_bullet('Processa todos os PDFs da pasta entrada/ e consolida em um unico arquivo.')

add_heading('Saida gerada', 3)
add_table(
    ['Arquivo', 'Colunas'],
    [['relatorio_processos_{data_hora}.xlsx',
      'Arquivo, Pagina, CPF/CNPJ, Proprietario, Placa, Processo, '
      'Data de Abertura, Data Resultado, Resultado, Relator']],
    col_widths=[6, 9]
)

# --- 4.5 ---
add_heading('4.5  Processos Abertos', 2, LARANJA)
add_para(parts=[('Arquivo: ', True), ('ProcessosAbertos/processosAbertos.py', False)])

add_heading('O que faz', 3)
add_para(
    'Le o relatorio "Relatorio de Processos Abertos - 1a. Instancia" exportado pelo '
    'sistema GAIDE/DETRAN em formato PDF e extrai todos os registros organizados por '
    'data de abertura, gerando uma planilha Excel estruturada.'
)

add_heading('Arquivos aceitos', 3)
add_table(
    ['Formato', 'Extensao'],
    [['Relatorio PDF - Processos Abertos 1a. Instancia (GAIDE/DETRAN)', '.pdf']],
    col_widths=[10, 5]
)

add_heading('Estrutura do relatorio PDF', 3)
add_para(
    'O relatorio agrupa os registros por data de abertura. Cada secao comeca com '
    '"DATA DE ABERTURA: DD/MM/AAAA" seguida de linhas no formato:'
)
add_code('SEQ   REQUERIMENTO   N. PROCESSO   N. AUTO   LOGIN')
add_para('')

add_heading('Como processa', 3)
add_bullet('Le todas as paginas do PDF com pdfplumber e extrai o texto linha a linha.')
add_bullet('Detecta a data de abertura de cada secao pela expressao "DATA DE ABERTURA: DD/MM/AAAA".')
add_bullet('Filtra linhas de cabecalho, rodape, paginacao e ruido por regex antes de tentar extrair dados.')
add_bullet('Cada linha de dado e validada pelo padrao: numero sequencial, tipo de requerimento (0P/1P/2C etc.), numero do processo, numero do auto (N...) e login do usuario.')
add_bullet('Move os PDFs processados para a pasta backup/ apos a extracao.')

add_heading('Colunas do arquivo de saida', 3)
add_table(
    ['Coluna', 'Conteudo'],
    [
        ['Data de Abertura', 'Data no formato DD/MM/AAAA'],
        ['SEQ',             'Numero sequencial do registro'],
        ['Requerimento',    'Tipo: 0P, 1P, 2C, etc.'],
        ['N. Processo',     'Numero do processo administrativo'],
        ['N. Auto',         'Numero do auto de infracao'],
        ['Login',           'Login do usuario responsavel'],
        ['Arquivo',         'Nome do PDF de origem'],
    ],
    col_widths=[4, 11]
)

add_heading('Saida gerada', 3)
add_table(
    ['Arquivo', 'Conteudo'],
    [['processos_abertos_{data_hora}.xlsx', 'Planilha com todos os registros de todos os PDFs consolidados']],
    col_widths=[6, 9]
)

# =============================================================
# 5. DEPENDENCIAS
# =============================================================
add_heading('5. Dependencias e Bibliotecas', 1)
add_table(
    ['Biblioteca', 'Uso'],
    [
        ['customtkinter', 'Interface grafica dark mode'],
        ['Pillow (PIL)',   'Carregamento e processamento de imagens'],
        ['pandas',        'Leitura, manipulacao e exportacao de planilhas'],
        ['openpyxl',      'Escrita de arquivos .xlsx'],
        ['xlrd',          'Leitura de arquivos .xls (formato legado)'],
        ['geopy',         'Geocodificacao via Nominatim (OpenStreetMap)'],
        ['pdfplumber',    'Extracao de texto de PDFs (Ferramentas 4 e 5)'],
        ['tqdm',          'Barra de progresso (ativa apenas no terminal)'],
    ],
    col_widths=[5, 10]
)

# =============================================================
# 6. BUILD E DISTRIBUICAO
# =============================================================
add_heading('6. Build e Distribuicao', 1)
add_para('O script build.ps1 automatiza todo o processo de empacotamento:')
for passo in [
    '1. Verifica se PyInstaller esta instalado.',
    '2. Verifica se logo.ico (engrenagem laranja) existe.',
    '3. Remove builds anteriores (build/ e dist/).',
    '4. Empacota com PyInstaller — gera dist/HubNITTRANS/. Os metadados de autoria (version_info.txt) sao embutidos diretamente no .exe e ficam visiveis em Propriedades > Detalhes no Windows Explorer.',
    '5. Compila o instalador com Inno Setup — gera installer/Output/Setup_HubNITTRANS_v1.0.exe.',
    '6. O instalador inclui o cache de geocodificacao pre-preenchido (cache_enderecos.json). Em instalacoes novas o cache e copiado automaticamente; em reinstalacoes o cache acumulado do usuario e preservado.',
]:
    add_bullet(passo)

doc.add_paragraph()
add_table(
    ['Item', 'Detalhe'],
    [
        ['Tamanho do instalador',      '~44 MB'],
        ['Diretorio de instalacao',    '%LOCALAPPDATA%\\Programs\\HubNITTRANS\\'],
        ['Requer administrador?',      'Nao'],
        ['Atalho na area de trabalho', 'Opcional (marcado por padrao no instalador)'],
        ['Metadados de autoria',       'Visiveis em Propriedades > Detalhes do HubNITTRANS.exe'],
        ['Desinstalacao',              'Configuracoes > Aplicativos > Hub de Ferramentas NITTRANS'],
    ],
    col_widths=[6, 9]
)

doc.save('Documentacao_HubNITTRANS.docx')
print('Arquivo salvo: Documentacao_HubNITTRANS.docx')