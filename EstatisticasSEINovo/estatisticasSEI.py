# -*- coding: utf-8 -*-
"""
Consolida os relatórios "Estatísticas da Unidade" do SEI de várias unidades
numa planilha só.

Cada PDF exportado pelo SEI é de uma unidade. Esta ferramenta lê todos os
PDFs da pasta 'entrada' — um por unidade — e monta um Excel com as unidades
lado a lado, para comparar o volume de processos gerados no período.

Seis seções do relatório são lidas, mais a unidade (do texto entre
parênteses na legenda das tabelas):

  Processos gerados no período
  Processos com tramitação no período
  Processos com andamento aberto na unidade ao final do período
  Processos com andamento fechado na unidade ao final do período
  Documentos gerados no período
  Documentos externos no período

Ficam de fora só os tempos médios de tramitação, que medem duração e não
quantidade.

A planilha sai com duas abas, ambas no formato longo — uma linha por
unidade e tipo, com a unidade escrita na própria linha, que é o formato
que a tabela dinâmica do Excel espera:

  Processos   coluna Situação separando Gerados, Tramitados, Abertos e
              Fechados, mais a classificação interna da PROTOCOLO
  Documentos  coluna Origem separando Gerados de Externos

Processos e documentos ficam em abas diferentes porque são contagens
distintas: o mesmo nome ('Decreto', 'Despacho') aparece nas duas com
significados diferentes, e somá-los daria um número sem sentido. Pela
mesma razão as situações do processo convivem numa coluna e não em linhas
soltas: um processo gerado também tramita e, ao final do período, está
aberto ou fechado na unidade — somar as quatro contaria o mesmo processo
mais de uma vez.

Sobre a nomenclatura interna da PROTOCOLO: essa unidade chama os tipos por
outros nomes ("Requerimento Geral" é o que ela trata como "Auto de
Infração", e assim por diante). A coluna principal traz sempre o nome do
SEI, para as unidades continuarem comparáveis entre si; a tradução da
PROTOCOLO sai numa coluna à parte, preenchida só nas linhas dela.

Diferenças em relação à versão anterior (pasta EstatisticasSEIAtual):
  - lê todos os PDFs da pasta, e não só o primeiro
  - a lista de tipos vem do PDF, em vez de uma lista fixa de seis
  - não gera mais o gráfico PNG
  - o nome da planilha leva a competência e nunca sobrescreve a anterior

Tudo o que não deu para ler é listado no terminal, nunca omitido em
silêncio.
"""

import json
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import pdfplumber
import pymupdf
import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

PASTA_ENTRADA = Path("entrada")
PASTA_BACKUP = Path("backup")
PASTA_RESULTADOS = Path("resultados")

NOME_SAIDA = "Estatisticas_SEI"
SUFIXO_SAIDA = "Extraido"

# Subpasta da biblioteca sincronizada onde a planilha pronta é deixada,
# além da pasta 'resultados' local. Trocar aqui para mudar o destino.
SUBPASTA_RESULTADO = "Consolidados"

COLUNA_DATA = "Data"
COLUNA_TIPO = "Tipo de Processo (SEI)"
COLUNA_INTERNA = "Classificação Interna (PROTOCOLO)"
COLUNA_SITUACAO = "Situação"
COLUNA_ORIGEM = "Origem"
COLUNA_TIPO_DOC = "Tipo de Documento (SEI)"

COLUNAS_PROCESSOS = [COLUNA_DATA, "Unidade", COLUNA_SITUACAO, COLUNA_TIPO,
                     COLUNA_INTERNA, "Quantidade"]
COLUNAS_DOCUMENTOS = [COLUNA_DATA, "Unidade", COLUNA_ORIGEM, COLUNA_TIPO_DOC,
                      "Quantidade"]

ABA_PROCESSOS = "Processos"
ABA_DOCUMENTOS = "Documentos"

# A interface preenche isto com uma função que pergunta ao usuário se a
# planilha deve ser gerada mesmo faltando unidades; ela recebe a lista de
# faltantes e a competência, e devolve True para seguir. Rodando fora do
# Hub (linha de comando) fica None, e a consolidação segue direto.
confirmar_faltantes = None

# Gravado pelo seletor com a competência escolhida na janela, logo antes
# de rodar. Ver competencia_escolhida().
ARQUIVO_CONFIG = "config.json"

# As unidades da NITTRANS que devem entregar estatística todo mês, na
# ordem hierárquica. É por esta lista que se sabe quem não entregou: os
# PDFs ficam todos soltos na pasta do mês, então a ausência de um arquivo
# não aponta unidade nenhuma por si só.
# Ao criar ou extinguir unidade no SEI, atualizar aqui.
UNIDADES_NITTRANS = (
    "NIT-NITTRANS-PRES",
    "NIT-NITTRANS-CHEFGAB",
    "NIT-NITTRANS-DEPGM",
    "NIT-NITTRANS-DIVEST",
    "NIT-NITTRANS-DEPCS",
    "NIT-NITTRANS-COORJUR",
    "NIT-NITTRANS-DEPJUR",
    "NIT-NITTRANS-DIVAPRO",
    "NIT-NITTRANS-COORGOV",
    "NIT-NITTRANS-DIVPS",
    "NIT-NITTRANS-DIVTO",
    "NIT-NITTRANS-DIRFIN",
    "NIT-NITTRANS-DEPPO",
    "NIT-NITTRANS-DEPPCF",
    "NIT-NITTRANS-DIVARC",
    "NIT-NITTRANS-DIVGF",
    "NIT-NITTRANS-COORCI",
    "NIT-NITTRANS-DEPCST",
    "NIT-NITTRANS-DIRADM",
    "NIT-NITTRANS-DEPADM",
    "NIT-NITTRANS-DIVAO",
    "NIT-NITTRANS-PROTOCOLO",
    "NIT-NITTRANS-DEPCLC",
    "NIT-NITTRANS-DIVPL",
    "NIT-NITTRANS-DIVCC",
    "NIT-NITTRANS-DIVC",
    "NIT-NITTRANS-DEPRH",
    "NIT-NITTRANS-DIVGP",
    "NIT-NITTRANS-SEGTRB",
    "NIT-NITTRANS-DEPTI",
    "NIT-NITTRANS-DIRTRAN",
    "NIT-NITTRANS-DEPRT",
    "NIT-NITTRANS-DEPOT",
    "NIT-NITTRANS-AGNTMT",
    "NIT-NITTRANS-DEPIRA",
    "NIT-NITTRANS-DIVAJARI",
    "NIT-NITTRANS-DIVREC",
    "NIT-NITTRANS-DIVIT",
    "NIT-NITTRANS-DEPET",
    "NIT-NITTRANS-DEPDET",
    "NIT-NITTRANS-DEPDOIV",
)

# A única unidade que usa nomenclatura própria. A comparação é feita com o
# nome normalizado, sem o sufixo do órgão.
UNIDADE_CLASSIFICACAO_INTERNA = "NIT/NITTRANS/PROTOCOLO"

# Nome do tipo no SEI -> nome como a PROTOCOLO o trata internamente.
CLASSIFICACAO_INTERNA_PROTOCOLO = {
    "Administrativo: Defesa Prévia": "Defesa Prévia",
    "Administrativo: Troca de Real Infrator": "Trocar de Real Infrator",
    "Administrativo: Auto de Infração": "Decreto N° 743/2026 Rotativo",
    "Administrativo: Recursos": "Defesa 1° e 2° Instancia",
    "Financeiro: Cancelamento de Lançamentos": "Formulário de Ajuste de Recurso",
    "Administrativo: Requerimento Geral/Envio de Expedientes Diversos":
        "Auto de Infração",
}

MESES = {
    "jan": "01", "fev": "02", "mar": "03", "abr": "04",
    "mai": "05", "jun": "06", "jul": "07", "ago": "08",
    "set": "09", "out": "10", "nov": "11", "dez": "12",
}

MESES_NOME = {
    "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
    "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
    "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro",
}

# Separadores aceitos entre o número do mês e o resto do nome da pasta,
# para '08', '08 - Agosto' e '08_Agosto' valerem igual.
SEPARADORES_PASTA = (" ", "-", "_", ".")

# Onde os PDFs ficam no SharePoint (site NittransDGM):
#   Documentos Compartilhados / Nittrans / EstatisticaSEI
# Sincronizada, a biblioteca vira uma pasta no perfil do usuário com nome
# montado pelo OneDrive ('<Organização>/<Site> - <Biblioteca>'), que varia
# conforme o tenant. Por isso a busca é pelo trecho final, que é estável.
SUBCAMINHO_BIBLIOTECA = ("Nittrans", "EstatisticaSEI")
NOME_PASTA_ALVO = "estatisticasei"

# Pastas padrão do Windows: uma biblioteca sincronizada nunca cai dentro
# delas, e varrê-las deixaria a busca lenta à toa.
PASTAS_IGNORADAS = {
    "appdata", "desktop", "downloads", "documents", "documentos",
    "pictures", "imagens", "music", "músicas", "musicas", "videos",
    "vídeos", "links", "favorites", "favoritos", "contacts", "contatos",
    "searches", "pesquisas", "saved games", "3d objects", "objetos 3d",
    "onedrive", "área de trabalho", "area de trabalho",
}

# A legenda vem logo abaixo da tabela: "Processos gerados no período
# (NIT/NITTRANS/DIVEST / NITEROI)". As outras tabelas do PDF têm legendas
# parecidas, por isso a expressão específica é tentada primeiro.
RE_UNIDADE = re.compile(
    r"Processos gerados no per[ií]odo\s*\(([^)]*)\)", re.IGNORECASE)
RE_UNIDADE_GENERICA = re.compile(r"no per[ií]odo\s*\(([^)]*)\)", re.IGNORECASE)
RE_ORGAO = re.compile(r"\s*/\s*NITEROI\b.*$", re.IGNORECASE)
RE_ANO = re.compile(r"^(19|20)\d{2}$")
RE_COPIA_WINDOWS = re.compile(r"\s*\(\d+\)$")
RE_TEM_CONTEUDO = re.compile(r"[0-9A-Za-zÀ-ÿ]")
# Layout de celular (PDF salvo com a janela estreita): cada célula vem com o
# rótulo da coluna na frente ('TIPO Comunicado', 'QUANTIDADE 1', '2026 25',
# 'AGO 25'). Ver _ler_layout_empilhado().
RE_ROTULO_EMPILHADO = re.compile(
    r"^(TIPO|QUANTIDADE|(19|20)\d{2}|" + "|".join(m.upper() for m in MESES)
    + r")(\s+|$)")
RE_TITULO_QUALQUER = re.compile(r"per[ií]odo\s*:$", re.IGNORECASE)
RE_LEGENDA_QUALQUER = re.compile(r"per[ií]odo\s*\(", re.IGNORECASE)
RE_CABECALHO_PAGINA = re.compile(r"^(\d{2}/\d{2}/\d{4}, \d{2}:\d{2}|https?://)")

# OCR para o PDF sem texto (impresso com 'Microsoft Print to PDF', que
# grava as letras como desenho). O MuPDF já traz o motor do Tesseract e só
# precisa do arquivo de idioma 'por.traineddata' — o mesmo que o TarjarPDF
# usa e que o hub.spec empacota junto (TarjarPDF/tesseract).
PASTA_TESSDATA = (Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
                  / "TarjarPDF" / "tesseract" / "tessdata")
# 400 foi a resolução que leu certo todos os números do relatório de teste;
# 300 e 600 trocaram dígitos.
DPI_OCR = 400
PALAVRAS_CABECALHO = {"tipo", "quantidade", "tempo", "médio"}

# As três seções do relatório que interessam, reconhecidas pelo título
# acima da tabela. Os dois-pontos no fim são o que distingue o título da
# legenda que vem abaixo da tabela, com a unidade entre parênteses.
TITULOS_SECAO = {
    "processos": re.compile(r"Processos gerados no per[ií]odo\s*:",
                            re.IGNORECASE),
    "processos_tramitados": re.compile(
        r"Processos com tramita[çc][ãa]o no per[ií]odo\s*:", re.IGNORECASE),
    # Os títulos de 'aberto' e 'fechado' só diferem nessa palavra, e nem
    # todo relatório traz as duas seções: a PROTOCOLO veio só com a de
    # fechado, e o PDF de exemplo só com a de aberto.
    "processos_abertos": re.compile(
        r"Processos com andamento aberto na unidade ao final do"
        r" per[ií]odo\s*:", re.IGNORECASE),
    "processos_fechados": re.compile(
        r"Processos com andamento fechado na unidade ao final do"
        r" per[ií]odo\s*:", re.IGNORECASE),
    "documentos_gerados": re.compile(r"Documentos gerados no per[ií]odo\s*:",
                                     re.IGNORECASE),
    "documentos_externos": re.compile(r"Documentos externos no per[ií]odo\s*:",
                                      re.IGNORECASE),
}
# Altura, em pontos, da faixa acima da tabela onde o título é procurado.
ALTURA_TITULO = 30

NOME_SECAO = {
    "processos": "Processos gerados no período",
    "processos_tramitados": "Processos com tramitação no período",
    "processos_abertos": "Processos com andamento aberto ao final do período",
    "processos_fechados": "Processos com andamento fechado ao final do período",
    "documentos_gerados": "Documentos gerados no período",
    "documentos_externos": "Documentos externos no período",
}

# Como cada seção aparece na coluna que a identifica dentro da aba.
SITUACAO_PROCESSO = {
    "processos": "Gerados",
    "processos_tramitados": "Tramitados",
    "processos_abertos": "Abertos",
    "processos_fechados": "Fechados",
}
ORIGEM_DOCUMENTO = {
    "documentos_gerados": "Gerado",
    "documentos_externos": "Externo",
}

# Ordem de leitura, que não é a alfabética: um processo é gerado, depois
# tramita, e ao final do período está aberto ou fechado na unidade.
ORDEM_SITUACAO = {"Gerados": 0, "Tramitados": 1, "Abertos": 2, "Fechados": 3}
ORDEM_ORIGEM = {"Gerado": 0, "Externo": 1}

# Formato de unidade aceito quando o nome vem do arquivo, e não do PDF:
# códigos como 'PROTOCOLO' ou 'NIT/NITTRANS/DIVEST'. Serve para descartar o
# resto do nome do arquivo ('Estatísticas da Unidade'), que não é unidade.
RE_CODIGO_UNIDADE = re.compile(r"^[A-Z0-9][A-Z0-9/\-. ]{1,}$")

COR_CABECALHO = "1F4E78"


# ==========================================
# 1. Localização dos PDFs na pasta sincronizada
# ==========================================
# O fluxo do Power Automate grava numa biblioteca do SharePoint; o usuário
# sincroniza essa biblioteca e ela vira um caminho local comum. A partir
# daí é só montar '<raiz>/<ano>/<mês>' — sem login e sem API.
def _normalizar(nome):
    """'Estatística SEI' e 'EstatisticaSEI' viram a mesma coisa."""
    sem_acento = unicodedata.normalize("NFKD", nome)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", sem_acento.lower())


def _pastas_candidatas(perfil):
    """
    Pastas do perfil onde uma biblioteca sincronizada pode estar: a raiz do
    perfil e um nível abaixo. O OneDrive cria '<Organização>/<Site> -
    <Biblioteca>', então dois níveis dão conta.
    """
    try:
        primeiro_nivel = [p for p in Path(perfil).iterdir()
                          if p.is_dir()
                          and p.name.lower() not in PASTAS_IGNORADAS
                          and not p.name.startswith(".")]
    except OSError:
        return []

    candidatas = list(primeiro_nivel)
    for pasta in primeiro_nivel:
        try:
            candidatas.extend(p for p in pasta.iterdir() if p.is_dir())
        except OSError:
            continue
    return candidatas


def detectar_pasta_sincronizada(perfil=None):
    """
    Acha sozinha a pasta EstatisticaSEI da biblioteca sincronizada.

    Cobre os dois jeitos de sincronizar: a biblioteca inteira (a pasta
    'Nittrans/EstatisticaSEI' fica lá dentro) ou só a subpasta
    EstatisticaSEI. Devolve None quando nada bate — que é o caso enquanto
    a biblioteca não tiver sido sincronizada na máquina.
    """
    perfil = Path(perfil) if perfil else Path.home()

    for candidata in _pastas_candidatas(perfil):
        completo = candidata.joinpath(*SUBCAMINHO_BIBLIOTECA)
        if completo.is_dir():
            return completo
        # O OneDrive prefixa a pasta com o nome do site, virando
        # 'Nittrans DGM - EstatisticaSEI'. Por isso a comparação é pelo
        # fim do nome, não por igualdade.
        if _normalizar(candidata.name).endswith(NOME_PASTA_ALVO):
            return candidata
    return None


def anos_disponiveis(raiz):
    """Anos que existem como pasta dentro da raiz, do mais recente ao mais antigo."""
    raiz = Path(raiz)
    if not raiz.is_dir():
        return []
    return sorted((p.name for p in raiz.iterdir()
                   if p.is_dir() and RE_ANO.match(p.name)), reverse=True)


def resolver_pasta_competencia(raiz, ano, mes):
    """
    Acha a pasta do mês dentro de '<raiz>/<ano>'.

    Aceita a pasta nomeada só com o número ('08'), com o número e o nome
    ('08 - Agosto') ou só com o nome ('Agosto'), porque quem cria essas
    pastas é uma pessoa e a convenção escorrega na prática.
    """
    pasta_ano = Path(raiz) / str(ano)
    if not pasta_ano.is_dir():
        return None

    numero = f"{int(mes):02d}"
    nome = _normalizar(MESES_NOME[numero])

    for pasta in sorted(pasta_ano.iterdir()):
        if not pasta.is_dir():
            continue
        candidato = pasta.name.strip().lower()
        if candidato in (numero, str(int(mes))):
            return pasta
        if any(candidato.startswith(numero + s) for s in SEPARADORES_PASTA):
            return pasta
        # Comparação sem acento: a biblioteca usa o mês por extenso, e
        # 'Março' escrito sem cedilha continua sendo março.
        if _normalizar(pasta.name).startswith(nome):
            return pasta
    return None


def _config():
    """Escolhas da janela, gravadas pelo seletor logo antes de rodar."""
    try:
        with open(ARQUIVO_CONFIG, encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, ValueError):
        return {}


def competencia_escolhida():
    """
    Ano e mês escolhidos na janela ('2026-08').

    É essa a competência que rotula a planilha, e não a que vem do
    cabeçalho do PDF: quem define de que mês é o relatório é a pasta onde
    ele foi guardado. O período escolhido na exportação do SEI nem sempre
    coincide — já apareceu relatório de dois meses dentro da pasta de um.

    Devolve None quando os PDFs foram escolhidos à mão, sem pasta de mês.
    """
    return _config().get("competencia_escolhida") or None


def _nome_de_unidade(codigo):
    """
    O código da unidade como ela aparece no relatório.

    A lista usa hífen ('NIT-NITTRANS-DIVAO'), que é como o SEI nomeia a
    unidade fora do sistema, mas a legenda do PDF usa barra. Sem
    uniformizar, a mesma unidade sairia escrita de dois jeitos: um nos
    meses em que entregou o relatório, outro nos meses em que faltou.
    """
    return codigo.replace("-", "/") if "/" not in codigo else codigo


def listar_pdfs(pasta):
    """
    PDFs da competência.

    Os relatórios ficam soltos na pasta do mês. A varredura também desce
    um nível porque os meses anteriores a agosto de 2026 foram organizados
    com uma subpasta por unidade, e essas pastas continuam lá.
    """
    if not pasta:
        return []
    pasta = Path(pasta)
    return sorted(pasta.glob("*.pdf")) + sorted(pasta.glob("*/*.pdf"))


# ==========================================
# 2. Leitura do PDF
# ==========================================
def _texto(celula):
    """Célula da tabela como texto de uma linha só."""
    return re.sub(r"\s+", " ", str(celula or "")).strip()


def _valor(linha):
    """
    Quantidade da linha: o último número dela.

    O SEI monta a tabela com uma coluna por mês e uma de total no fim.
    Pegar o último número dá o total do período, e não o de um mês só,
    o que mantém o resultado correto quando o relatório cobre mais de um mês.
    """
    for celula in reversed(linha):
        texto = _texto(celula).replace(".", "")
        if texto.isdigit():
            return int(texto)
    return None


def _e_linha_de_total(nome):
    return nome.upper().startswith(("TOTAL", "GERAL"))


def _tem_cabecalho_de_periodo(tabela):
    """
    Cabeçalho 'Tipo' com o ano numa linha e o(s) mês(es) na de baixo — o
    formato das seções de contagem por período. Só nelas dá para ler a
    competência do próprio relatório.
    """
    if len(tabela) < 3:
        return False
    cabecalho = [_texto(c) for c in tabela[0]]
    if not cabecalho or cabecalho[0].lower() != "tipo":
        return False
    return any(RE_ANO.match(c) for c in cabecalho)


def _tem_cabecalho_tipo(tabela):
    """A tabela começa com o cabeçalho 'Tipo' — ou seja, não é continuação."""
    if not tabela or not tabela[0]:
        return False
    return _texto(tabela[0][0]).lower() == "tipo"


def _parece_continuacao(tabela):
    """
    Reconhece o pedaço que a quebra de página jogou para a página
    seguinte: vem sem cabeçalho e sem título, mas com linhas de verdade —
    nome de tipo e quantidade.

    O relatório também traz as caixas de gráfico, que o pdfplumber devolve
    como tabelas sem cabeçalho e sem conteúdo; elas não têm nenhuma linha
    assim e ficam de fora.
    """
    for linha in tabela or []:
        if not linha:
            continue
        nome = _texto(linha[0])
        if nome and RE_TEM_CONTEUDO.search(nome) and _valor(linha) is not None:
            return True
    return False


def _inicio_dos_dados(tabela):
    """
    Em que linha começam os dados, ou None se a tabela não é de contagem.

    O relatório usa dois formatos. As seções por período gastam duas
    linhas de cabeçalho (ano e mês) e começam na terceira; as de
    tramitação e andamento vêm como 'Tipo | Quantidade' e começam na
    segunda. As de tempo médio têm 'Tipo | Tempo Médio' e ficam de fora,
    porque medem duração, não quantidade.
    """
    if len(tabela) < 2:
        return None
    cabecalho = [_texto(c) for c in tabela[0]]
    if not cabecalho or cabecalho[0].lower() != "tipo":
        return None
    if _tem_cabecalho_de_periodo(tabela):
        return 2
    if len(cabecalho) > 1 and cabecalho[1].lower() == "quantidade":
        return 1
    return None


def _secao_da_tabela(pagina, tabela):
    """
    Descobre a que seção a tabela pertence pelo título logo acima dela.

    'Documentos gerados' e 'Documentos externos' são idênticas em formato
    — mesmo cabeçalho, mesmo tipo de conteúdo —, então só o texto acima
    distingue uma da outra. Também não dá para usar a ordem das páginas:
    num dos relatórios reais os documentos externos estavam na página 2,
    e noutro na 3.

    O título tem dois-pontos no fim ('Documentos gerados no período:'),
    enquanto a legenda abaixo da tabela vem com a unidade entre
    parênteses. É o que evita confundir o título de uma com a legenda da
    anterior.
    """
    topo = max(0, tabela.bbox[1] - ALTURA_TITULO)
    acima = pagina.crop((0, topo, pagina.width, tabela.bbox[1]))
    texto = re.sub(r"\s+", " ", acima.extract_text() or "")
    for secao, padrao in TITULOS_SECAO.items():
        if padrao.search(texto):
            return secao
    return None


def _desembrulhar(dados):
    """
    Tira a tabela de dentro da que o navegador às vezes põe em volta da
    página inteira. Aí a primeira linha é o texto da página até a tabela,
    com o resto das seções anteriores, e o cabeçalho 'Tipo' vem logo
    depois; o título da tabela é o último que ficou sem legenda. No fim,
    depois da legenda, sobram pedaços das seções seguintes, que são
    cortados.

    Devolve (seção pelo título embutido, dados), ou (None, dados) intactos
    quando a tabela não está embrulhada.
    """
    if _tem_cabecalho_tipo(dados) or len(dados) < 2:
        return None, dados
    inicio = next((i for i in (1, 2) if _tem_cabecalho_tipo(dados[i:])), None)
    if inicio is None or not dados[0]:
        return None, dados
    secao = _secao_aberta_no_fim(dados[0][0])
    if secao is None:
        return None, dados
    fim = next((i for i in range(inicio, len(dados))
                if dados[i] and RE_LEGENDA_QUALQUER.search(_texto(dados[i][0]))),
               len(dados))
    return secao, dados[inicio:fim]


def _secao_aberta_no_fim(texto_da_pagina):
    """Seção cujo título ficou no fim da página sem a legenda embaixo."""
    aberta = None
    for linha in (texto_da_pagina or "").splitlines():
        linha = _texto(linha)
        if RE_TITULO_QUALQUER.search(linha):
            aberta = next((s for s, p in TITULOS_SECAO.items()
                           if p.search(linha)), None)
        elif RE_LEGENDA_QUALQUER.search(linha):
            aberta = None
    return aberta


def _ler_itens(pedacos, arquivo, avisos):
    """
    Tipos e quantidades de uma seção, juntando os pedaços em que a quebra
    de página a dividiu. Devolve (itens, total declarado).
    """
    itens = defaultdict(int)
    total = None
    for tabela, inicio in pedacos:
        for linha in tabela[inicio:]:
            if not linha:
                continue
            nome = _texto(linha[0])
            # Descarta a linha final de glifos de navegação da página, que
            # não tem letra nem número nenhum.
            if not nome or not RE_TEM_CONTEUDO.search(nome):
                continue
            if _e_linha_de_total(nome):
                total = _valor(linha)
                continue
            quantidade = _valor(linha)
            if quantidade is None:
                avisos.append((arquivo.name,
                               f"'{nome}' veio sem quantidade legível"
                               " — ficou de fora"))
                continue
            itens[nome] += quantidade
    return dict(itens), total


def _ler_layout_empilhado(texto, arquivo, avisos):
    """
    Plano B para o PDF salvo com a janela do navegador estreita: o SEI
    troca a tabela pelo layout de celular, uma célula por linha com o
    rótulo da coluna na frente, e o pdfplumber não acha tabela com
    cabeçalho 'Tipo'. A leitura então é pelo texto corrido.

    Tirados os rótulos, cada item é o nome seguido da(s) quantidade(s);
    como em _valor(), o último número é o total do período. A seção começa
    no título ('...no período:') e termina na legenda com a unidade ou no
    próximo título.

    Devolve ({seção: (itens, total declarado)}, competências).
    """
    secoes = {}
    secao = None
    nome = None
    anos, meses = set(), set()
    for linha in texto.splitlines():
        linha = _texto(linha)
        if not RE_TEM_CONTEUDO.search(linha) or RE_CABECALHO_PAGINA.match(linha):
            continue
        if RE_TITULO_QUALQUER.search(linha):
            secao = next((s for s, p in TITULOS_SECAO.items()
                          if p.search(linha)), None)
            if secao:
                secoes[secao] = {}
            nome = None
            continue
        if RE_LEGENDA_QUALQUER.search(linha):
            secao = None
            continue
        if secao is None:
            continue
        # Cabeçalho do mês, sozinho na linha ('Ago').
        if linha.lower() in MESES:
            meses.add(MESES[linha.lower()])
            continue
        rotulo = RE_ROTULO_EMPILHADO.match(linha)
        if rotulo:
            if RE_ANO.match(rotulo.group(1)):
                anos.add(rotulo.group(1))
            elif rotulo.group(1).lower() in MESES:
                meses.add(MESES[rotulo.group(1).lower()])
            linha = linha[rotulo.end():]
            if not linha:
                continue
        if linha.replace(".", "").isdigit():
            if nome:
                secoes[secao][nome] = int(linha.replace(".", ""))
        else:
            nome = linha
            secoes[secao].setdefault(nome, None)

    lidas = {}
    for secao, valores in secoes.items():
        total = None
        itens = {}
        for nome, quantidade in valores.items():
            if _e_linha_de_total(nome):
                total = quantidade
            elif quantidade is None:
                avisos.append((arquivo.name,
                               f"'{nome}' veio sem quantidade legível"
                               " — ficou de fora"))
            else:
                itens[nome] = quantidade
        lidas[secao] = (itens, total)

    competencias = ([f"{anos.pop()}-{m}" for m in sorted(meses)]
                    if len(anos) == 1 else [])
    return lidas, competencias


def _linhas_do_ocr(palavras, largura):
    """
    Remonta as linhas da tabela a partir das palavras do OCR, no formato
    que _ler_layout_empilhado() lê: o nome do tipo numa linha e cada
    quantidade na sua.

    O Tesseract devolve cada célula como uma linha à parte, então nome e
    quantidades de uma mesma linha da tabela são juntados pela altura. O
    nome que quebrou em duas ou três linhas dentro da célula fica centrado
    na linha do número, e cada pedaço vai para a linha com número mais
    próxima. O TOTAL é reconhecido pela posição (é o único nome fora da
    margem esquerda), porque o OCR costuma ler a palavra errado.
    """
    if not palavras:
        return []
    alturas = sorted(p[3] - p[1] for p in palavras)
    altura = alturas[len(alturas) // 2]
    margem = largura * 0.015

    celulas = defaultdict(list)
    for x0, y0, x1, y1, palavra, bloco, linha, _ in palavras:
        # Gráficos (letras gigantes) e setas de navegação (na beirada).
        if y1 - y0 > 3 * altura or x1 < margem or x0 > largura - margem:
            continue
        celulas[bloco, linha].append((x0, y0, x1, y1, palavra))

    # (centro vertical, x, tipo, texto) de cada célula.
    pedacos = []
    for ws in celulas.values():
        texto = " ".join(w[4] for w in ws)
        x0 = min(w[0] for w in ws)
        centro = (min(w[1] for w in ws) + max(w[3] for w in ws)) / 2
        # O ano e o mês do cabeçalho passam adiante como estão, para a
        # competência. ponytail: uma quantidade que por acaso seja um ano
        # (2026) e caia sozinha numa célula seria lida como cabeçalho.
        if (RE_TITULO_QUALQUER.search(texto) or RE_LEGENDA_QUALQUER.search(texto)
                or RE_ANO.match(texto) or texto.lower() in MESES):
            tipo = "marco"
        elif set(texto.lower().split()) <= PALAVRAS_CABECALHO:
            continue
        elif texto.replace(".", "").isdigit():
            tipo = "numero"
        elif len(texto) <= 3:
            continue  # número lido como lixo ('Fe)'); o do mês ao lado basta
        else:
            tipo = "nome"
        pedacos.append((centro, x0, tipo, texto))
    pedacos.sort()

    # Agrupa em linhas da tabela pela altura.
    linhas = []
    for pedaco in pedacos:
        if linhas and pedaco[0] - linhas[-1][0][0] <= altura * 0.6:
            linhas[-1].append(pedaco)
        else:
            linhas.append([pedaco])

    def tem(linha, tipo):
        return any(p[2] == tipo for p in linha)

    # Pedaço de nome sem número vai para a linha com número mais próxima,
    # sem atravessar título ou legenda.
    destino = {}
    for i, linha in enumerate(linhas):
        if tem(linha, "numero") or tem(linha, "marco"):
            continue
        candidatas = []
        for passo in (-1, 1):
            j = i + passo
            while 0 <= j < len(linhas) and not tem(linhas[j], "marco"):
                if tem(linhas[j], "numero"):
                    candidatas.append((abs(linhas[j][0][0] - linha[0][0]), j))
                    break
                j += passo
        perto = [c for c in candidatas if c[0] <= 2.2 * altura]
        if perto:
            destino[i] = min(perto)[1]

    saida = []
    for i, linha in enumerate(linhas):
        if i in destino:
            continue
        if tem(linha, "marco") or not tem(linha, "numero"):
            saida += [p[3] for p in sorted(linha, key=lambda p: p[1])]
            continue
        nomes = [p for p in linha if p[2] == "nome"]
        if nomes and min(p[1] for p in nomes) > largura * 0.05:
            nome = "TOTAL:"
        else:
            partes = [linhas[j] for j in sorted(
                [i] + [k for k, d in destino.items() if d == i])]
            nome = " ".join(p[3] for parte in partes
                            for p in sorted(parte, key=lambda p: p[1])
                            if p[2] == "nome")
        if nome:
            saida.append(nome)
        saida += [p[3] for p in sorted(linha, key=lambda p: p[1])
                  if p[2] == "numero"]
    return saida


def _texto_por_ocr(arquivo):
    """
    Texto do PDF sem camada de texto, lido por OCR e já no formato de
    _ler_layout_empilhado(). None quando falta o português do Tesseract.
    """
    if not (PASTA_TESSDATA / "por.traineddata").exists():
        return None
    linhas = []
    with pymupdf.open(arquivo) as documento:
        for pagina in documento:
            leitura = pagina.get_textpage_ocr(language="por", dpi=DPI_OCR,
                                              full=True,
                                              tessdata=str(PASTA_TESSDATA))
            linhas += _linhas_do_ocr(pagina.get_text("words", textpage=leitura),
                                     pagina.rect.width)
    return "\n".join(linhas)


def _competencia_do_cabecalho(tabela):
    """
    Monta a competência ('2026-07') a partir das duas linhas de cabeçalho:
    a primeira traz o ano, a segunda os meses. Num relatório de mais de um
    mês vêm vários, e cada mês fica sob o ano da coluna correspondente.
    """
    linha_ano, linha_mes = tabela[0], tabela[1]

    anos = {i: _texto(c) for i, c in enumerate(linha_ano)
            if RE_ANO.match(_texto(c))}
    if not anos:
        return []

    def ano_da_coluna(indice):
        anteriores = [i for i in anos if i <= indice]
        return anos[max(anteriores)] if anteriores else anos[min(anos)]

    competencias = []
    for indice, celula in enumerate(linha_mes):
        mes = MESES.get(_texto(celula)[:3].lower())
        if mes:
            competencias.append(f"{ano_da_coluna(indice)}-{mes}")
    return sorted(set(competencias))


def _unidade_do_texto(texto):
    """Unidade da legenda da tabela, sem o sufixo do órgão."""
    achado = RE_UNIDADE.search(texto) or RE_UNIDADE_GENERICA.search(texto)
    if not achado:
        return None
    unidade = RE_ORGAO.sub("", achado.group(1)).strip()
    return unidade or None


def _unidade_do_nome(arquivo):
    """
    Plano B para a unidade: o trecho depois do último ' - ' no nome do
    arquivo, quando ele tem cara de código de unidade.

    Cobre as duas convenções que apareceram: o nome inteiro sendo a
    unidade ('NIT-NITTRANS-PROTOCOLO.pdf', usada desde agosto de 2026) e a
    unidade no fim ('SEI - Estatísticas da Unidade - PROTOCOLO.pdf'). O nome
    padrão do SEI, sem unidade nenhuma, não bate no formato e é
    descartado — senão 'Estatísticas da Unidade' viraria nome de unidade.
    """
    candidatos = [arquivo.stem]
    if " - " in arquivo.stem:
        candidatos.insert(0, arquivo.stem.rsplit(" - ", 1)[1])
    for candidato in candidatos:
        limpo = RE_COPIA_WINDOWS.sub("", candidato).strip()
        if RE_CODIGO_UNIDADE.match(limpo):
            return limpo
    return None


def _chave_unidade(unidade):
    """
    Forma comparável do nome da unidade: só letras e números.

    'NIT/NITTRANS/PROTOCOLO' (legenda do PDF) e 'NIT-NITTRANS-PROTOCOLO'
    (lista e nome de arquivo) são a mesma unidade escrita de dois jeitos.
    """
    return re.sub(r"[^A-Z0-9]", "", (unidade or "").upper())


def _mesma_unidade(uma, outra):
    return _chave_unidade(uma) == _chave_unidade(outra)


def ler_pdf(arquivo, avisos):
    """
    Extrai de um PDF a unidade, a competência e as três seções de contagem
    do relatório: processos gerados, documentos gerados e documentos
    externos, todas do período.

    Devolve None quando nenhuma das três seções foi encontrada.
    """
    texto = ""
    paginas_sem_texto = []
    # Seção -> pedaços dela, na ordem em que aparecem. Mais de um pedaço
    # quando a quebra de página corta a tabela ao meio.
    fragmentos = {}
    secao_aberta = None
    achou_cabecalho = False

    with pdfplumber.open(arquivo) as pdf:
        for numero, pagina in enumerate(pdf.pages, start=1):
            # extract_text() devolve None em página digitalizada ou só com
            # imagem. É dela que sai a legenda com o nome da unidade.
            conteudo = pagina.extract_text()
            if conteudo:
                texto += conteudo + "\n"
            else:
                paginas_sem_texto.append(numero)

            for tabela in pagina.find_tables():
                secao_embrulhada, dados = _desembrulhar(tabela.extract())

                if _tem_cabecalho_tipo(dados):
                    achou_cabecalho = True
                    inicio = _inicio_dos_dados(dados)
                    secao = ((secao_embrulhada
                              or _secao_da_tabela(pagina, tabela))
                             if inicio is not None else None)
                    # Toda tabela com cabeçalho encerra a anterior, mesmo
                    # sendo de uma seção que não interessa (tempos médios):
                    # senão a continuação dela entraria na seção de cima.
                    secao_aberta = secao
                    if secao is None:
                        continue
                    if secao in fragmentos:
                        avisos.append((arquivo.name,
                                       f"a seção '{NOME_SECAO[secao]}'"
                                       " apareceu mais de uma vez — só a"
                                       " primeira foi usada"))
                        secao_aberta = None
                        continue
                    fragmentos[secao] = [(dados, inicio)]
                    continue

                # Sem cabeçalho: é o resto da tabela anterior, que a quebra
                # de página empurrou para cá. Já aconteceu de a seção
                # inteira estar do outro lado da quebra, com só o cabeçalho
                # sobrando na página anterior.
                if secao_aberta and _parece_continuacao(dados):
                    fragmentos.setdefault(secao_aberta, []).append((dados, 0))

            # A página que termina num título sem a legenda embaixo deixa
            # essa seção aberta para a próxima, mesmo quando o cabeçalho
            # dela não virou tabela própria (veio dentro da tabela que o
            # navegador põe em volta da página).
            secao_aberta = _secao_aberta_no_fim(conteudo) or secao_aberta

    if paginas_sem_texto:
        avisos.append((arquivo.name,
                       f"{len(paginas_sem_texto)} página(s) sem texto"
                       f" extraível: {', '.join(map(str, paginas_sem_texto))}"
                       " — provavelmente digitalizada(s)"))

    # Seção -> (itens, total declarado). Sem tabela nenhuma com cabeçalho
    # 'Tipo', o PDF pode estar no layout de celular do SEI ou sem texto
    # nenhum; nos dois casos a leitura é pelo texto corrido.
    secoes = None
    por_ocr = False
    if not achou_cabecalho:
        if not texto.strip():
            texto = _texto_por_ocr(arquivo)
            if texto is None:
                avisos.append((arquivo.name,
                               "sem texto e sem OCR disponível — falta"
                               f" {PASTA_TESSDATA / 'por.traineddata'}"))
                return None
            por_ocr = True
        secoes, competencias = _ler_layout_empilhado(texto, arquivo, avisos)
        if not secoes:
            return None
        avisos.append((arquivo.name,
                       "PDF sem texto (provavelmente 'Microsoft Print to"
                       " PDF') — lido por OCR; vale conferir os números"
                       if por_ocr else
                       "PDF no layout de celular do SEI (salvo com a janela"
                       " do navegador estreita) — lido pelo texto; vale"
                       " conferir os números"))

    unidade = _unidade_do_texto(texto)
    unidade_do_nome = _unidade_do_nome(arquivo)
    if por_ocr and unidade_do_nome:
        # O OCR costuma trocar a barra da legenda por 'I'
        # ('NITINITTRANS'); o nome do arquivo é mais confiável.
        unidade = _nome_de_unidade(unidade_do_nome)
    elif not unidade:
        unidade = unidade_do_nome
        if unidade:
            avisos.append((arquivo.name, "a legenda com a unidade não foi"
                                         f" encontrada; usado o nome do"
                                         f" arquivo: '{unidade}'"))
    elif unidade_do_nome and not _mesma_unidade(unidade, unidade_do_nome):
        # A pasta da biblioteca diz uma unidade e o relatório diz outra:
        # quase sempre é PDF salvo na pasta errada. Vale o que está dentro
        # do PDF, mas calar isso deixaria o número na unidade errada.
        avisos.append((arquivo.name,
                       f"a pasta indica '{unidade_do_nome}', mas o relatório"
                       f" por dentro é da unidade '{unidade}' — o PDF pode"
                       " estar guardado na pasta errada. Valeu a unidade do"
                       " relatório."))

    # Só as seções por período trazem ano e mês no cabeçalho; as de
    # tramitação e andamento vêm sem. Todas cobrem o mesmo período, então
    # basta a primeira que tiver o cabeçalho completo.
    if secoes is None:
        competencias = []
        for pedacos in fragmentos.values():
            if _tem_cabecalho_de_periodo(pedacos[0][0]):
                competencias = _competencia_do_cabecalho(pedacos[0][0])
                if competencias:
                    break
        secoes = {secao: _ler_itens(pedacos, arquivo, avisos)
                  for secao, pedacos in fragmentos.items()}
    if not competencias:
        avisos.append((arquivo.name,
                       "não deu para ler a competência no cabeçalho"))

    lidas = {}
    for secao, (itens, total_declarado) in secoes.items():
        lidas[secao] = itens
        soma = sum(itens.values())
        if total_declarado is not None and total_declarado != soma:
            avisos.append((arquivo.name,
                           f"em '{NOME_SECAO[secao]}', a soma dos tipos"
                           f" ({soma}) não bate com o TOTAL do PDF"
                           f" ({total_declarado}) — conferir"))

    registro = {
        "arquivo": arquivo.name,
        "unidade": unidade,
        "competencias": competencias,
        "total": sum(lidas.get("processos", {}).values()),
    }
    for secao in TITULOS_SECAO:
        registro[secao] = lidas.get(secao, {})
    return registro


# ==========================================
# 3. Montagem da tabela
# ==========================================
def _usa_classificacao_interna(unidade):
    return unidade.strip().upper().endswith(UNIDADE_CLASSIFICACAO_INTERNA)


def montar_tabela(dados, competencia=None, faltantes=()):
    """
    Uma linha por unidade e tipo de processo, com a unidade escrita na
    própria linha.

    É o formato que a tabela dinâmica do Excel espera. A alternativa —
    uma coluna por unidade — foi descartada: com 39 unidades a planilha
    fica larga demais para ler, e cada mês novo mudaria as colunas.

    'competencia' é o ano e mês da pasta. Quando não vem (seleção manual
    de PDFs), a data cai para o período lido do próprio relatório.

    'faltantes' são as unidades sem relatório no mês. Elas entram com
    tipo e quantidade em branco — e não com zero, que afirmaria que a
    unidade não gerou processo nenhum, quando o que se sabe é apenas que
    o relatório não foi entregue.
    """
    linhas = []
    for registro in dados:
        interno = _usa_classificacao_interna(registro["unidade"])
        data = competencia or (" e ".join(registro["competencias"])
                               or "Não identificada")
        for secao, situacao in SITUACAO_PROCESSO.items():
            for tipo, quantidade in registro.get(secao, {}).items():
                linhas.append({
                    COLUNA_DATA: data,
                    "Unidade": registro["unidade"],
                    COLUNA_SITUACAO: situacao,
                    COLUNA_TIPO: tipo,
                    COLUNA_INTERNA: (CLASSIFICACAO_INTERNA_PROTOCOLO.get(tipo, "")
                                     if interno else ""),
                    "Quantidade": quantidade,
                })

    for unidade in faltantes:
        linhas.append({
            COLUNA_DATA: competencia or "Não identificada",
            "Unidade": unidade,
            COLUNA_SITUACAO: "",
            COLUNA_TIPO: "",
            COLUNA_INTERNA: "",
            "Quantidade": "",
        })

    return _ordenar(pd.DataFrame(linhas, columns=COLUNAS_PROCESSOS),
                    COLUNA_SITUACAO, ORDEM_SITUACAO, COLUNA_TIPO)


def montar_tabela_documentos(dados, competencia=None, faltantes=()):
    """
    Os documentos gerados e os externos na mesma tabela, separados pela
    coluna Origem.

    Ficam fora da aba de processos porque são outra contagem: o mesmo nome
    ('Decreto', 'Despacho') aparece nas duas seções significando coisas
    diferentes, e somá-los junto com processos daria um número sem sentido.
    """
    linhas = []
    for registro in dados:
        data = competencia or (" e ".join(registro["competencias"])
                               or "Não identificada")
        for secao, origem in ORIGEM_DOCUMENTO.items():
            for tipo, quantidade in registro.get(secao, {}).items():
                linhas.append({
                    COLUNA_DATA: data,
                    "Unidade": registro["unidade"],
                    COLUNA_ORIGEM: origem,
                    COLUNA_TIPO_DOC: tipo,
                    "Quantidade": quantidade,
                })

    for unidade in faltantes:
        linhas.append({
            COLUNA_DATA: competencia or "Não identificada",
            "Unidade": unidade,
            COLUNA_ORIGEM: "",
            COLUNA_TIPO_DOC: "",
            "Quantidade": "",
        })

    return _ordenar(pd.DataFrame(linhas, columns=COLUNAS_DOCUMENTOS),
                    COLUNA_ORIGEM, ORDEM_ORIGEM, COLUNA_TIPO_DOC)


def _ordenar(tabela, coluna_grupo, ordem_grupo, coluna_tipo):
    """
    Ordena por unidade, depois pela ordem de leitura do grupo, e dentro
    dele da maior quantidade para a menor.

    As duas chaves auxiliares existem porque nenhuma das duas colunas
    ordena direto: a do grupo sairia em ordem alfabética (Abertos antes de
    Gerados) e a de Quantidade mistura número com branco, o que quebraria
    a comparação. Nenhuma das duas vai para o Excel.
    """
    if tabela.empty:
        return tabela
    tabela = tabela.copy()
    tabela["_grupo"] = [ordem_grupo.get(valor, len(ordem_grupo))
                        for valor in tabela[coluna_grupo]]
    tabela["_ordem"] = [q if isinstance(q, int) else -1
                        for q in tabela["Quantidade"]]
    tabela = tabela.sort_values(
        ["Unidade", "_grupo", "_ordem", coluna_tipo],
        ascending=[True, True, False, True],
    )
    return tabela.drop(columns=["_grupo", "_ordem"]).reset_index(drop=True)


# ==========================================
# 4. Geração da planilha
# ==========================================
def _caminho_livre(caminho):
    """
    Nunca sobrescreve uma planilha já existente: se o nome estiver ocupado,
    acrescenta ' (2)', ' (3)'... como o Windows faz.
    """
    if not caminho.exists():
        return caminho
    contador = 2
    while True:
        candidato = caminho.with_name(
            f"{caminho.stem} ({contador}){caminho.suffix}")
        if not candidato.exists():
            return candidato
        contador += 1


def _formatar_aba(ws, colunas):
    fonte_cabecalho = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    fill_cabecalho = PatternFill(
        start_color=COR_CABECALHO, end_color=COR_CABECALHO, fill_type="solid")
    borda_fina = Side(border_style="thin", color="D3D3D3")
    borda = Border(left=borda_fina, right=borda_fina,
                   top=borda_fina, bottom=borda_fina)

    for indice, nome in enumerate(colunas, start=1):
        letra = get_column_letter(indice)
        celula = ws.cell(row=1, column=indice)
        celula.font = fonte_cabecalho
        celula.fill = fill_cabecalho
        celula.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True)
        celula.border = borda

        if nome in (COLUNA_TIPO, COLUNA_INTERNA, COLUNA_TIPO_DOC):
            largura = 58
        elif nome == "Unidade":
            largura = 30
        else:
            largura = max(len(nome) + 4, 14)
        ws.column_dimensions[letra].width = largura

        if nome == "Quantidade":
            for linha in range(2, ws.max_row + 1):
                ws.cell(row=linha, column=indice).number_format = "#,##0"

    # Congela o cabeçalho e as duas primeiras colunas (Data e Unidade),
    # que são a referência ao rolar a lista.
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions


def copiar_para_biblioteca(caminho_saida):
    """
    Deixa uma cópia da planilha na biblioteca sincronizada.

    Gravar ali não é apenas salvar em disco: o cliente do OneDrive sobe o
    arquivo para o SharePoint, e ele passa a ser visto por quem tem acesso
    à biblioteca. Por isso a cópia só acontece no fluxo da pasta do mês —
    na seleção manual de PDFs a planilha fica só em 'resultados'.

    Devolve o caminho da cópia, ou None quando não deu para copiar. Falhar
    aqui não invalida a execução: a planilha local já está gravada.
    """
    raiz = _config().get("pasta_raiz")
    if not raiz:
        return None

    destino = Path(raiz) / SUBPASTA_RESULTADO
    if not destino.is_dir():
        print(f"\n  Aviso: a pasta '{SUBPASTA_RESULTADO}' não existe em"
              f" {raiz}.")
        print("  A planilha ficou só na pasta 'resultados'.")
        return None

    try:
        alvo = _caminho_livre(destino / caminho_saida.name)
        shutil.copy(caminho_saida, alvo)
        return alvo
    except OSError as erro:
        print(f"\n  Aviso: não consegui copiar para a biblioteca: {erro}")
        print("  A planilha ficou só na pasta 'resultados'.")
        return None


def gerar_excel(processos, documentos, caminho_saida):
    with pd.ExcelWriter(caminho_saida, engine="openpyxl") as writer:
        for aba, tabela in ((ABA_PROCESSOS, processos),
                            (ABA_DOCUMENTOS, documentos)):
            tabela.to_excel(writer, index=False, sheet_name=aba)
            _formatar_aba(writer.sheets[aba], list(tabela.columns))


# ==========================================
# 5. Função principal
# ==========================================
def _resolver_unidades(dados, avisos):
    """
    Deixa cada PDF distinguível na coluna Unidade.

    Dois PDFs da mesma unidade (o mesmo mês baixado duas vezes, por
    exemplo) virariam linhas idênticas, e somar por unidade contaria o
    mesmo processo duas vezes sem ninguém perceber. Aqui o segundo ganha
    sufixo e o caso é reportado.
    """
    vistas = {}
    for indice, registro in enumerate(dados, start=1):
        unidade = registro["unidade"] or f"Unidade não identificada {indice}"
        if registro["unidade"] is None:
            avisos.append((registro["arquivo"],
                           "a unidade não foi identificada nem na legenda"
                           " nem no nome do arquivo"))
        if unidade in vistas:
            vistas[unidade] += 1
            avisos.append((registro["arquivo"],
                           f"a unidade '{unidade}' já tinha vindo em outro"
                           f" PDF — esta entrou como"
                           f" '{unidade} ({vistas[unidade]})'"))
            unidade = f"{unidade} ({vistas[unidade]})"
        else:
            vistas[unidade] = 1
        registro["unidade"] = unidade
    return dados


def _competencia_geral(dados, avisos, competencia_da_pasta=None):
    """
    Competência que rotula a planilha: a da pasta, quando há.

    Com a pasta definida, o período lido de cada PDF vira conferência: se
    o relatório não cobre o mês da pasta, o número está sendo contado no
    mês errado, e isso precisa ser dito.
    """
    if competencia_da_pasta:
        for registro in dados:
            periodo = registro["competencias"]
            if periodo and competencia_da_pasta not in periodo:
                avisos.append((registro["arquivo"],
                               f"está na pasta de {competencia_da_pasta},"
                               f" mas o relatório é de {' e '.join(periodo)}"
                               " — confira o período usado na exportação"
                               " do SEI"))
        return competencia_da_pasta

    # Sem pasta (seleção manual): a competência sai do próprio relatório.
    todas = sorted({c for registro in dados for c in registro["competencias"]})
    if not todas:
        return None
    if len(todas) > 1:
        avisos.append(("(geral)",
                       "os PDFs são de competências diferentes ("
                       + ", ".join(todas)
                       + ") — a planilha soma todas elas"))
        return f"{todas[0]} a {todas[-1]}"
    return todas[0]


def rodar_estatisticas_sei():
    for pasta in (PASTA_ENTRADA, PASTA_BACKUP, PASTA_RESULTADOS):
        pasta.mkdir(exist_ok=True)

    arquivos = sorted(PASTA_ENTRADA.glob("*.pdf"))
    if not arquivos:
        raise FileNotFoundError(
            "Coloque o(s) PDF(s) de Estatísticas da Unidade na pasta:\n"
            f"{PASTA_ENTRADA.resolve()}")

    dados = []
    ignorados = []
    avisos = []

    for arquivo in arquivos:
        try:
            registro = ler_pdf(arquivo, avisos)
        except Exception as erro:
            ignorados.append((arquivo.name, f"não foi possível abrir: {erro}"))
            continue

        if registro is None:
            ignorados.append((arquivo.name,
                              "não tem a tabela 'Processos gerados no"
                              " período' — não parece um relatório de"
                              " Estatísticas da Unidade"))
            continue

        dados.append(registro)
        competencia = " e ".join(registro["competencias"]) or "sem competência"
        print(f"  {arquivo.name}")
        print(f"    -> {registro['unidade'] or 'unidade não identificada'}"
              f" | {competencia} | {len(registro['processos'])} tipo(s),"
              f" {registro['total']} processo(s)")

    if ignorados:
        print("\n" + "=" * 60)
        print("ARQUIVOS IGNORADOS")
        print("=" * 60)
        for nome, motivo in ignorados:
            print(f"  {nome}: {motivo}")
        print("=" * 60)

    if not dados:
        raise Exception(
            "Nenhum dos PDFs tem a tabela 'Processos gerados no período'."
            " Confira se são os relatórios de Estatísticas da Unidade do SEI.")

    dados = _resolver_unidades(dados, avisos)
    competencia_da_pasta = competencia_escolhida()
    competencia = _competencia_geral(dados, avisos, competencia_da_pasta)

    if avisos:
        print("\n" + "=" * 60)
        print("PONTOS PARA CONFERIR")
        print("=" * 60)
        for nome, mensagem in avisos:
            print(f"  [{nome}] {mensagem}")
        print("=" * 60)

    # Quem não entregou: as unidades da lista que não apareceram em
    # relatório nenhum. A conferência só faz sentido quando o mês inteiro
    # foi lido; na seleção manual de PDFs não há mês, e cobrar as 41
    # unidades de uma escolha avulsa só geraria ruído.
    faltantes = []
    if competencia_da_pasta:
        presentes = {_chave_unidade(registro["unidade"]) for registro in dados}
        faltantes = [_nome_de_unidade(codigo) for codigo in UNIDADES_NITTRANS
                     if _chave_unidade(codigo) not in presentes]

        desconhecidas = sorted(
            registro["unidade"] for registro in dados
            if _chave_unidade(registro["unidade"])
            not in {_chave_unidade(c) for c in UNIDADES_NITTRANS})
        if desconhecidas:
            avisos.append(("(geral)",
                           "unidade fora da lista da NITTRANS: "
                           + ", ".join(desconhecidas)
                           + " — se for unidade nova, incluir em"
                             " UNIDADES_NITTRANS"))

    if faltantes:
        print("\n" + "=" * 60)
        print(f"UNIDADES SEM RELATÓRIO EM {competencia or 'no período'}:"
              f" {len(faltantes)} de {len(UNIDADES_NITTRANS)}"
              " — entraram em branco na planilha")
        print("=" * 60)
        for unidade in faltantes:
            print(f"  {unidade}")
        print("=" * 60)

        # Confirma antes de gerar: a planilha de um mês incompleto é fácil
        # de confundir com a definitiva, e o desconto costuma ser de quem
        # ainda vai entregar, não de quem não tem o que reportar.
        if confirmar_faltantes and not confirmar_faltantes(faltantes,
                                                           competencia):
            raise Exception(
                f"Cancelado: {len(faltantes)} unidade(s) sem relatório."
                " Nenhuma planilha foi gerada e os PDFs continuam na pasta"
                " de entrada.")

    tabela = montar_tabela(dados, competencia, faltantes)
    documentos = montar_tabela_documentos(dados, competencia, faltantes)

    nome_arquivo = "_".join(
        parte for parte in (NOME_SAIDA, competencia, SUFIXO_SAIDA) if parte)
    caminho_saida = _caminho_livre(PASTA_RESULTADOS / f"{nome_arquivo}.xlsx")

    try:
        gerar_excel(tabela, documentos, caminho_saida)
    except PermissionError:
        raise Exception("O arquivo Excel antigo está aberto! Feche-o e tente"
                        " novamente.")

    # A cópia para a biblioteca só no fluxo da pasta do mês: é o mesmo
    # sinal usado para conferir as unidades, e evita publicar no SharePoint
    # o resultado de uma conferência avulsa feita com PDFs escolhidos à mão.
    copia_biblioteca = (copiar_para_biblioteca(caminho_saida)
                        if competencia_da_pasta else None)

    for arquivo in arquivos:
        shutil.move(str(arquivo), str(PASTA_BACKUP / arquivo.name))

    total_geral = sum(registro["total"] for registro in dados)
    tipos_distintos = len({tipo for registro in dados
                           for tipo in registro["processos"]})
    def somar(secao):
        return sum(quantidade for registro in dados
                   for quantidade in registro.get(secao, {}).values())

    print("\n" + "=" * 60)
    print(f"Concluído! Planilha: {caminho_saida}")
    if copia_biblioteca:
        print(f"  Cópia na biblioteca: {copia_biblioteca}")
        print("  O OneDrive envia essa cópia para o SharePoint, onde ela"
              " fica visível para quem tem acesso à pasta.")
    print(f"  {len(dados)} unidade(s) com relatório.")
    print(f"  Aba {ABA_PROCESSOS} ({len(tabela)} linhas,"
          f" {tipos_distintos} tipo(s) gerados):")
    for secao, situacao in SITUACAO_PROCESSO.items():
        print(f"     {situacao}: {somar(secao)}")
    print(f"  Aba {ABA_DOCUMENTOS} ({len(documentos)} linhas):")
    for secao, origem in ORIGEM_DOCUMENTO.items():
        print(f"     {origem}: {somar(secao)}")
    if faltantes:
        print(f"  {len(faltantes)} unidade(s) sem relatório, em branco nas"
              " duas abas.")
    print("=" * 60)


if __name__ == "__main__":
    rodar_estatisticas_sei()
