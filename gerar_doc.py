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
r2 = p2.add_run('Documentação Técnica')
r2.font.size = Pt(16)
r2.font.color.rgb = AZUL_ESCURO
r2.font.name = 'Calibri'

doc.add_paragraph()
for chave, valor in [
    ('Sistema',       'Hub de Ferramentas — Gestão e Modernização'),
    ('Órgão',         'NITTRANS — Niterói Transporte S.A. / Prefeitura de Niterói/RJ'),
    ('Versão',        '2.0'),
    ('Tecnologia',    'Python 3.13 · CustomTkinter · PyInstaller · Inno Setup · cryptography'),
    ('Ano',           '2026'),
    ('Desenvolvedor', 'Alan Doyle Costa Ribeiro'),
    ('Cargo',         'Estagiário — Gestão e Modernização'),
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
# 1. VISÃO GERAL
# =============================================================
add_heading('1. Visão Geral', 1)
add_para(
    'O Hub de Ferramentas NITTRANS é uma aplicação desktop Windows com interface gráfica '
    '(modo escuro) que centraliza sete automações de dados utilizadas internamente pela '
    'equipe técnica. Cada ferramenta opera de forma independente: o usuário seleciona o '
    'arquivo de entrada, a ferramenta processa e gera o resultado, que pode ser exportado '
    'para qualquer destino.'
)
add_para(
    'A aplicação não exige instalação de Python nem de nenhuma dependência: tudo está '
    'empacotado no instalador .exe, que instala sem necessidade de privilégios de administrador. '
    'Ao passar o mouse sobre qualquer botão, uma dica resumida descreve o que aquela ferramenta faz.'
)

add_heading('Ferramentas disponíveis', 2)
add_table(
    ['Nº', 'Nome', 'Função resumida'],
    [
        ['1', 'Latitude e Longitude',     'Converte coordenadas em endereços via OpenStreetMap'],
        ['2', 'Limpeza de Arquivos',      'Corrige encoding e padroniza logradouros em planilhas'],
        ['3', 'Organizador TXT Detran',   'Converte .txt posicional do DETRAN em Excel estruturado'],
        ['4', 'Organizador Detran Limpo', 'Limpa coluna de endereço removendo números e sufixos'],
        ['5', 'PDF e Excel Multas',       'Extrai processos deferidos/indeferidos de PDFs GAIDE'],
        ['6', 'Processos Abertos',        'Lê relatórios PDF de Processos Abertos e exporta para Excel'],
        ['7', 'Criptografar Arquivos',    'Criptografa arquivos com AES-256 e gera HTML autocontido'],
    ],
    col_widths=[1, 5, 9]
)

# =============================================================
# 2. ESTRUTURA DE PASTAS
# =============================================================
add_heading('2. Estrutura de Pastas', 1)
for linha in [
    'ProjetosNITTRANS/',
    '|-- main.py                       <- Ponto de entrada',
    '|-- interface.py                  <- Interface gráfica (CustomTkinter)',
    '|-- processamento.py              <- Orquestrador (threads e pastas)',
    '|-- hub.spec                      <- Configuração do PyInstaller',
    '|-- version_info.txt              <- Metadados de autoria do .exe (v2.0)',
    '|-- build.ps1                     <- Script de build automatizado',
    '|-- Logo.png / logo.ico           <- Identidade visual',
    '|',
    '|-- LatitudeLongitude/',
    '|   |-- enderecos.py              <- Ferramenta 1',
    '|   |-- cache_enderecos.json      <- Cache de geocodificação (pré-preenchido)',
    '|-- LimpezaArquivo/',
    '|   |-- limpeza.py               <- Ferramenta 2',
    '|-- OrganizadorTxtDetran/',
    '|   |-- decifradorTxt.py         <- Ferramenta 3',
    '|-- DetranLimpo/',
    '|   |-- detranLimpo.py           <- Ferramenta 4',
    '|-- PdfExcelMultas/',
    '|   |-- pdfDeferidoIndeferido.py <- Ferramenta 5',
    '|-- ProcessosAbertos/',
    '|   |-- processosAbertos.py      <- Ferramenta 6',
    '|-- Criptografia/',
    '    |-- criptografia.py          <- Ferramenta 7 (ponto de entrada standalone)',
    '    |-- gui.py                   <- Interface gráfica do criptografador',
    '    |-- crypto.py                <- Lógica de criptografia (AES-256-GCM)',
    '    |-- html_builder.py          <- Gerador do HTML autocontido',
]:
    add_code(linha)

doc.add_paragraph()
add_para('Cada ferramenta (1–6) cria automaticamente três subpastas ao ser executada:')
add_table(
    ['Subpasta', 'Função'],
    [
        ['entrada/',    'Arquivo enviado pelo usuário para processar'],
        ['backup/',     'Cópia do arquivo original após o processamento'],
        ['resultados/', 'Arquivo(s) gerado(s) pela ferramenta'],
    ],
    col_widths=[4, 11]
)

# =============================================================
# 3. FLUXO DE USO
# =============================================================
add_heading('3. Fluxo de Uso (Ferramentas 1–6)', 1)
for passo in [
    '1. Usuário clica em uma das ferramentas na tela principal.',
    '2. Um diálogo de seleção de arquivo abre.',
    '3. O arquivo escolhido é copiado para a pasta entrada/ da ferramenta.',
    '4. O processamento roda em uma thread separada (interface não trava).',
    '5. Ao finalizar, aparece o botão "Exportar Arquivo Pronto".',
    '6. O usuário salva o resultado onde quiser via diálogo de salvamento.',
    '7. O botão de pasta ao lado de cada ferramenta abre o Explorer na pasta da ferramenta.',
]:
    add_bullet(passo)
doc.add_paragraph()
add_para('Ferramenta 7 (Criptografar): abre uma janela própria dentro do hub com interface dedicada.')

# =============================================================
# 4. FERRAMENTAS
# =============================================================
add_heading('4. Ferramentas', 1)

# --- 4.1 ---
add_heading('4.1  Latitude e Longitude', 2, LARANJA)
add_para(parts=[('Arquivo: ', True), ('LatitudeLongitude/enderecos.py', False)])
add_heading('O que faz', 3)
add_para(
    'Recebe uma planilha com coordenadas geográficas (latitude/longitude) e enriquece '
    'cada linha com o endereço completo correspondente (rua, bairro, número, cidade, '
    'CEP, estado) via geocodificação reversa usando a API pública OpenStreetMap/Nominatim.'
)
add_heading('Arquivos aceitos', 3)
add_table(
    ['Formato', 'Extensão'],
    [
        ['Planilha Excel', '.xlsx, .xls'],
        ['CSV com separador ponto-e-vírgula', '.csv'],
    ],
    col_widths=[8, 7]
)
add_heading('Como processa', 3)
add_bullet('Identifica colunas de latitude e longitude por nome (latitude, lat, y, longitude, lon, lng, x) ou por faixa de valores.')
add_bullet('Usa a API Nominatim com RateLimiter (mínimo 1,2 s entre requisições) para respeitar os limites da API gratuita.')
add_bullet('Mantém cache local (cache_enderecos.json) — coordenadas já consultadas não são buscadas novamente. O instalador inclui cache pré-preenchido.')
add_bullet('O cache é salvo a cada 10 novas entradas para evitar perda em caso de interrupção.')
add_bullet('Coordenadas sem endereço encontrado são registradas em coordenadas_nao_encontradas.txt.')
add_heading('Colunas adicionadas', 3)
add_table(
    ['Coluna', 'Conteúdo'],
    [
        ['Endereco_Rua',  'Nome da rua/logradouro'],
        ['Bairro',        'Bairro'],
        ['Numero_Imovel', 'Número do imóvel'],
        ['Cidade',        'Município'],
        ['CEP',           'Código postal'],
        ['Estado',        'Estado'],
    ],
    col_widths=[5, 10]
)

# --- 4.2 ---
add_heading('4.2  Limpeza de Arquivos', 2, LARANJA)
add_para(parts=[('Arquivo: ', True), ('LimpezaArquivo/limpeza.py', False)])
add_heading('O que faz', 3)
add_para(
    'Recebe planilhas de cadastro ou fiscalização e realiza limpeza profunda dos dados: '
    'corrige texto mal codificado (mojibake), padroniza nomes de logradouros, normaliza '
    'capitalização, valida endereços via geocodificação e gera relatório de todas as '
    'alterações realizadas.'
)
add_heading('Como processa', 3)
add_bullet('Tenta automaticamente múltiplas combinações de encoding (utf-8, cp1252, latin-1) e separador até encontrar leitura válida (mínimo 15 colunas).')
add_bullet('Calcula hash SHA-256 do arquivo original para rastreabilidade.')
add_bullet('Corrige mojibake por re-decodificação latin1→utf-8, com até 5 passagens iterativas.')
add_bullet('Aplica capitalização inteligente — artigos "da", "de", "do" ficam em minúsculo.')
add_bullet('Expande abreviações: R. → Rua, Av. → Av., Estr. → Estrada, Tv. → Travessa, Pça. → Praça.')
add_bullet('Valida endereço e bairro via Nominatim para obter o nome oficial do logradouro em Niterói/RJ.')
add_heading('Saídas geradas', 3)
add_table(
    ['Arquivo', 'Conteúdo'],
    [
        ['{nome}_LIMPO.xlsx',     'Planilha com todos os dados corrigidos'],
        ['{nome}_RELATORIO.xlsx', 'Registro de cada alteração: campo, valor original e corrigido'],
    ],
    col_widths=[6, 9]
)

# --- 4.3 ---
add_heading('4.3  Organizador TXT Detran', 2, LARANJA)
add_para(parts=[('Arquivo: ', True), ('OrganizadorTxtDetran/decifradorTxt.py', False)])
add_heading('O que faz', 3)
add_para(
    'Converte arquivos .txt de posição fixa exportados pelo sistema do DETRAN/RJ '
    'em planilhas Excel estruturadas e legíveis, extraindo cada campo pela sua '
    'posição exata no layout do arquivo. Cria também uma coluna "Descrição sem Número" '
    'com o logradouro limpo logo após a coluna original.'
)
add_heading('Layout — campos por posição de caractere', 3)
add_table(
    ['Posição', 'Campo'],
    [
        ['0 – 6',     'Código do Órgão Atuador'],
        ['6 – 9',     'Código da Infração'],
        ['11 – 71',   'Descrição da Infração'],
        ['71 – 91',   'Tipo de Enquadramento'],
        ['91 – 103',  'Auto'],
        ['103 – 111', 'Data (AAAAMMDD → DD/MM/AAAA)'],
        ['111 – 117', 'Hora (HHMMSS → HH:MM:SS)'],
        ['158 – 167', 'Valor da Infração (centavos → R$ 0,00)'],
        ['174 – 181', 'Placa do Veículo'],
        ['233 – 293', 'Nome do Infrator'],
        ['293 – 337', 'Logradouro'],
        ['388 +',     'Descrição do Município do Endereço + coluna extra sem número'],
    ],
    col_widths=[4, 11]
)

# --- 4.4 ---
add_heading('4.4  Organizador Detran Limpo', 2, LARANJA)
add_para(parts=[('Arquivo: ', True), ('DetranLimpo/detranLimpo.py', False)])
add_heading('O que faz', 3)
add_para(
    'Recebe planilhas Excel que contenham uma coluna de endereço (por exemplo, a saída '
    'do Organizador TXT Detran ou arquivos exportados diretamente do sistema GAIDE) e '
    'cria ou atualiza uma coluna "Rua" com o logradouro limpo, sem número e sem '
    'referências de cruzamento ou sufixos de posição.'
)
add_heading('Arquivos aceitos', 3)
add_table(
    ['Formato', 'Extensão'],
    [
        ['Planilha Excel', '.xlsx, .xls'],
        ['CSV', '.csv'],
    ],
    col_widths=[8, 7]
)
add_heading('Regras de limpeza', 3)
add_bullet('Remove número do final do endereço: "AV. BRASIL 341" → "AV. BRASIL".')
add_bullet('Remove "N" abreviado de número: "RUA BARÃO DO AMAZONAS N 340" → "RUA BARÃO DO AMAZONAS".')
add_bullet('Remove sufixos de posição: OP., OP. OP., OPOSTO, LADO OP.')
add_bullet('Remove referências de cruzamento: "COM RUA SÃO PEDRO", "C/ R. BARÃO...", "CRUZAMENTO COM...".')
add_bullet('Reconhece faixas de números: "151 AO 251" e remove o intervalo inteiro.')
add_heading('Comportamento da coluna Rua', 3)
add_table(
    ['Situação', 'Ação'],
    [
        ['Coluna "Rua" não existe',            'Cria a coluna logo após o campo de endereço'],
        ['Coluna "Rua" existe (qualquer valor)', 'Sempre sobrescreve com o valor limpo do endereço'],
    ],
    col_widths=[6, 9]
)

# --- 4.5 ---
add_heading('4.5  PDF e Excel Multas', 2, LARANJA)
add_para(parts=[('Arquivo: ', True), ('PdfExcelMultas/pdfDeferidoIndeferido.py', False)])
add_heading('O que faz', 3)
add_para(
    'Extrai dados de processos julgados (Deferido/Indeferido) a partir de relatórios PDF '
    'gerados pelo sistema GAIDE/NITERÓI e consolida todos os registros em uma única planilha Excel.'
)
add_heading('Desafios do PDF e como são tratados', 3)
add_bullet('CNPJ quebrado em duas linhas: reunificado antes da extração.')
add_bullet('Placa isolada abaixo do nome do proprietário: fundida à linha correta.')
add_bullet('Sobrenome do relator em linha separada: lista configurável de sobrenomes conhecidos.')
add_bullet('Texto de infração espalhado por múltiplas linhas: concatenado até o próximo marcador.')
add_bullet('Linhas de cabeçalho e rodapé descartadas por regex.')
add_heading('Saída gerada', 3)
add_table(
    ['Arquivo', 'Colunas'],
    [['relatorio_processos_{data_hora}.xlsx',
      'Arquivo, Página, CPF/CNPJ, Proprietário, Placa, Processo, '
      'Data de Abertura, Data Resultado, Resultado, Relator']],
    col_widths=[6, 9]
)

# --- 4.6 ---
add_heading('4.6  Processos Abertos', 2, LARANJA)
add_para(parts=[('Arquivo: ', True), ('ProcessosAbertos/processosAbertos.py', False)])
add_heading('O que faz', 3)
add_para(
    'Lê o relatório "Relatório de Processos Abertos — 1ª Instância" exportado pelo '
    'sistema GAIDE/DETRAN em formato PDF e extrai todos os registros organizados por '
    'data de abertura, gerando uma planilha Excel estruturada.'
)
add_heading('Colunas do arquivo de saída', 3)
add_table(
    ['Coluna', 'Conteúdo'],
    [
        ['Data de Abertura', 'Data no formato DD/MM/AAAA'],
        ['SEQ',              'Número sequencial do registro'],
        ['Requerimento',     'Tipo: 0P, 1P, 2C, etc.'],
        ['Nº Processo',      'Número do processo administrativo'],
        ['Nº Auto',          'Número do auto de infração'],
        ['Login',            'Login do usuário responsável'],
        ['Arquivo',          'Nome do PDF de origem'],
    ],
    col_widths=[4, 11]
)

# --- 4.7 ---
add_heading('4.7  Criptografar Arquivos', 2, LARANJA)
add_para(parts=[('Arquivos: ', True), ('Criptografia/crypto.py, html_builder.py, gui.py', False)])
add_heading('O que faz', 3)
add_para(
    'Criptografa qualquer tipo de arquivo (Excel, PDF, Word, TXT) com uma senha definida '
    'pelo usuário e gera um arquivo HTML autocontido. O destinatário abre o HTML em '
    'qualquer navegador, digita a senha e o arquivo original é baixado já descriptografado '
    'diretamente na máquina dele — sem passar por nenhum servidor.'
)

add_heading('Fluxo completo', 3)
for passo in [
    '1. Usuário seleciona o arquivo e digita uma senha.',
    '2. O app gera um arquivo .html com os dados cifrados embutidos.',
    '3. O .html é enviado ao destinatário (e-mail, WhatsApp, pendrive etc.).',
    '4. O destinatário abre o .html no navegador e digita a senha.',
    '5. O arquivo original é baixado diretamente pelo navegador — sem servidor intermediário.',
]:
    add_bullet(passo)

add_heading('Camadas de segurança', 3)
add_table(
    ['Camada', 'Técnica', 'Por que protege'],
    [
        ['Derivação de senha',
         'PBKDF2-SHA256\n480.000 iterações',
         'Torna ataques de força bruta extremamente lentos — testar milhões de senhas por segundo se torna inviável'],
        ['Sal aleatório',
         '16 bytes aleatórios por arquivo',
         'Mesmo cifrando o mesmo arquivo com a mesma senha duas vezes, os resultados são completamente diferentes. Elimina ataques por tabela pré-calculada (rainbow table)'],
        ['Cifra simétrica',
         'AES-256-GCM',
         'Padrão usado por governos e bancos. O modo GCM autentica os dados: qualquer alteração no arquivo cifrado é detectada imediatamente'],
        ['Processamento local',
         'Web Crypto API (nativa do navegador)',
         'A descriptografia ocorre 100% no navegador do destinatário. O arquivo nunca trafega pela rede em aberto'],
    ],
    col_widths=[3.5, 4, 7.5]
)

add_heading('Proteção contra tentativas repetidas', 3)
add_para(
    'O HTML gerado possui bloqueio progressivo embutido: cada senha errada dobra o tempo '
    'de espera até a próxima tentativa (2 s, 4 s, 8 s…). Após 10 tentativas erradas, '
    'o arquivo é bloqueado permanentemente naquele navegador. O estado é salvo no '
    'localStorage, portanto fechar e reabrir o navegador não reseta o contador.'
)

add_heading('Limitações conhecidas', 3)
add_bullet('Senha fraca anula a proteção — a força está na senha escolhida pelo usuário.')
add_bullet('O bloqueio por tentativas é por navegador, não por arquivo. Um atacante com acesso ao .html pode tentá-lo em outro navegador.')
add_bullet('Máquina comprometida com malware pode capturar o arquivo após a descriptografia.')
add_para(
    'Para uso interno da NITTRANS — compartilhamento de planilhas e documentos por '
    'e-mail ou aplicativos de mensagem — o nível de segurança oferecido é equivalente '
    'ao usado em HTTPS e em cofres de senha profissionais.'
)

# =============================================================
# 5. DEPENDÊNCIAS
# =============================================================
add_heading('5. Dependências e Bibliotecas', 1)
add_table(
    ['Biblioteca', 'Uso'],
    [
        ['customtkinter', 'Interface gráfica dark mode'],
        ['Pillow (PIL)',   'Carregamento e processamento de imagens'],
        ['pandas',        'Leitura, manipulação e exportação de planilhas'],
        ['openpyxl',      'Escrita de arquivos .xlsx'],
        ['xlrd',          'Leitura de arquivos .xls (formato legado)'],
        ['geopy',         'Geocodificação via Nominatim (OpenStreetMap)'],
        ['pdfplumber',    'Extração de texto de PDFs (Ferramentas 5 e 6)'],
        ['cryptography',  'AES-256-GCM e PBKDF2-SHA256 (Ferramenta 7)'],
        ['tqdm',          'Barra de progresso (ativa apenas no terminal)'],
        ['unicodedata',   'Normalização de texto e correção de encoding (stdlib)'],
    ],
    col_widths=[4, 11]
)

# =============================================================
# 6. BUILD E DISTRIBUIÇÃO
# =============================================================
add_heading('6. Build e Distribuição', 1)
add_para('O script build.ps1 automatiza todo o processo de empacotamento:')
for passo in [
    '1. Verifica se PyInstaller está instalado.',
    '2. Verifica se logo.ico (engrenagem laranja) existe.',
    '3. Remove builds anteriores (build/ e dist/).',
    '4. Empacota com PyInstaller — gera dist/HubNITTRANS/. Os metadados de autoria definidos em version_info.txt são embutidos no .exe e ficam visíveis em Propriedades → Detalhes no Windows Explorer.',
    '5. Compila o instalador com Inno Setup — gera installer/Output/Setup_HubNITTRANS_v2.0.exe.',
    '6. O instalador inclui o cache de geocodificação pré-preenchido. Em instalações novas o cache é copiado; em reinstalações o cache acumulado do usuário é preservado.',
]:
    add_bullet(passo)

doc.add_paragraph()
add_table(
    ['Item', 'Detalhe'],
    [
        ['Versão atual',               '2.0'],
        ['Tamanho do instalador',      '~46 MB'],
        ['Diretório de instalação',    '%LOCALAPPDATA%\\Programs\\HubNITTRANS\\'],
        ['Requer administrador?',      'Não'],
        ['Atalho na área de trabalho', 'Opcional (marcado por padrão no instalador)'],
        ['Metadados de autoria',       'Visíveis em Propriedades → Detalhes do HubNITTRANS.exe'],
        ['Tooltips',                   'Descrição resumida aparece ao passar o mouse sobre cada botão'],
        ['Desinstalação',              'Configurações → Aplicativos → Hub de Ferramentas NITTRANS'],
    ],
    col_widths=[5, 10]
)

doc.save('Documentacao_HubNITTRANS_v2.docx')
print('Arquivo salvo: Documentacao_HubNITTRANS.docx')