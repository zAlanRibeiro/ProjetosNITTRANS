# -*- coding: utf-8 -*-
"""Gera a documentação técnica do Hub de Ferramentas NITTRANS.

Mesmo conteúdo da Documentacao_HubNITTRANS (visão geral, estrutura de pastas,
fluxo, ferramenta por ferramenta, dependências e build), atualizado para a
versão 5.1 — 11 ferramentas — e organizado no padrão visual do modelo
"FERRAMENTA ESTATÍSTICAS SEI.docx".
"""
import os

from doc_modelo import DocumentoModelo

SAIDA = 'DOCUMENTACAO TECNICA HUB NITTRANS.docx'

d = DocumentoModelo()

# =============================================================================
# ABERTURA
# =============================================================================
d.titulo('DOCUMENTAÇÃO TÉCNICA — HUB DE FERRAMENTAS NITTRANS')
d.data('Niterói, 29 de julho de 2026')
d.ficha([
    ('Sistema', 'Hub de Ferramentas — Gestão e Modernização'),
    ('Órgão', 'NITTRANS — Niterói Transporte S.A. / Prefeitura de Niterói/RJ'),
    ('Versão', '5.1'),
    ('Tecnologia',
     'Python 3.13 · CustomTkinter · pandas · pdfplumber · PyMuPDF · Tesseract OCR · '
     'matplotlib · cryptography · PyInstaller · Inno Setup'),
    ('Ano', '2026'),
    ('Desenvolvedor', 'Alan Doyle Costa Ribeiro'),
    ('Cargo', 'Estagiário — Gestão e Modernização'),
])

# =============================================================================
d.h3('1. Visão Geral')
d.corpo(
    'O Hub de Ferramentas NITTRANS é uma aplicação desktop Windows com interface '
    'gráfica que centraliza onze automações de dados usadas internamente pela equipe '
    'técnica. Cada ferramenta opera de forma independente: o usuário seleciona o arquivo '
    'de entrada, a ferramenta processa e gera o resultado, que pode ser exportado para '
    'qualquer destino.'
)
d.corpo(
    'A aplicação não exige instalação de Python nem de nenhuma dependência: tudo está '
    'empacotado no instalador .exe, que instala sem necessidade de privilégios de '
    'administrador. Ao passar o mouse sobre qualquer botão, uma dica resumida descreve o '
    'que aquela ferramenta faz.'
)
d.corpo(
    'A arquitetura separa três responsabilidades: main.py apenas inicia a aplicação, '
    'interface.py desenha a tela e trata os eventos, e processamento.py orquestra a '
    'execução — seleção de arquivos, preparo das pastas e disparo da thread de trabalho. '
    'Cada ferramenta é um módulo isolado, exposto por uma única função de entrada.'
)

d.subtitulo('Ferramentas disponíveis')
d.tabela(
    ['Nº', 'Nome', 'Módulo', 'Função resumida'],
    [
        ['1', 'Latitude e Longitude', 'LatitudeLongitude/enderecos.py',
         'Converte coordenadas em endereços via OpenStreetMap'],
        ['2', 'Limpeza de Arquivos', 'LimpezaArquivo/limpeza.py',
         'Corrige encoding e padroniza logradouros em planilhas'],
        ['3', 'Organizador TXT Detran', 'OrganizadorTxtDetran/decifradorTxt.py',
         'Converte .txt posicional do DETRAN em Excel estruturado'],
        ['4', 'Organizador Detran Limpo', 'DetranLimpo/detranLimpo.py',
         'Limpa coluna de endereço removendo números e sufixos'],
        ['5', 'PDF e Excel Multas', 'PdfExcelMultas/pdfDeferidoIndeferido.py',
         'Extrai processos deferidos/indeferidos de PDFs GAIDE'],
        ['6', 'Processos Abertos', 'ProcessosAbertos/processosAbertos.py',
         'Lê relatórios PDF de Processos Abertos e exporta para Excel'],
        ['7', 'Estatísticas SEI', 'EstatisticasSEI/sei_estatisticas.py',
         'Lê o relatório de Estatísticas da Unidade do SEI e gera gráfico e planilha'],
        ['8', 'Mesclar e Remover Duplicadas', 'RemovedorDuplicadasDetran/removerDuplicada.py',
         'Consolida várias planilhas em um CSV único sem linhas repetidas'],
        ['9', 'Criptografar Arquivos', 'Criptografia/crypto.py, html_builder.py, gui.py',
         'Criptografa arquivos com AES-256-GCM e gera HTML autocontido'],
        ['10', 'Tarjar PDF', 'TarjarPDF/logica.py, interface_tarjar.py',
         'Oculta CPF, RG, CNPJ e e-mails de PDFs para adequação à LGPD'],
        ['11', 'Bloquear Planilha', 'BloquearPlanilha/bloqueador.py, gui.py',
         'Formata a planilha e protege a aba com senha'],
    ],
    larguras=[1.0, 3.6, 5.2, 5.7],
)
d.observacao(
    'As ferramentas 1 a 8 seguem o fluxo padrão do orquestrador. As ferramentas 9, 10 e '
    '11 abrem uma janela própria (CTkToplevel) e não passam pelo GerenciadorProcessos.'
)

# =============================================================================
d.h3('2. Estrutura de Pastas')
d.codigo([
    'ProjetosNITTRANS/',
    '|-- main.py                       <- Ponto de entrada',
    '|-- interface.py                  <- Interface grafica (CustomTkinter)',
    '|-- processamento.py              <- Orquestrador (threads e pastas)',
    '|-- doc_modelo.py                 <- Blocos de montagem dos documentos .docx',
    '|-- gerar_doc_hub.py              <- Gera o manual de uso',
    '|-- gerar_doc_tecnico.py          <- Gera esta documentacao tecnica',
    '|-- limpar_cache_ruas.py          <- Manutencao do cache de ruas do Detran Limpo',
    '|-- hub.spec                      <- Configuracao do PyInstaller',
    '|-- version_info.txt              <- Metadados de autoria do .exe (v5.1)',
    '|-- build.ps1                     <- Script de build automatizado',
    '|-- requirements.txt              <- Dependencias de desenvolvimento',
    '|-- logo.ico / LogoNittrans.jpeg  <- Identidade visual',
    '|-- FundoAplicativoNITTRANS.png   <- Fundo das janelas',
    '|-- installer/setup.iss           <- Script do Inno Setup',
    '|',
    '|-- LatitudeLongitude/',
    '|   |-- enderecos.py              <- Ferramenta 1',
    '|   |-- cache_enderecos.json      <- Cache de geocodificacao (pre-preenchido)',
    '|-- LimpezaArquivo/',
    '|   |-- limpeza.py                <- Ferramenta 2',
    '|-- OrganizadorTxtDetran/',
    '|   |-- decifradorTxt.py          <- Ferramenta 3',
    '|-- DetranLimpo/',
    '|   |-- detranLimpo.py            <- Ferramenta 4',
    '|   |-- ruas_oficiais_niteroi.json <- Base de ruas de Niteroi',
    '|   |-- baixar_base_niteroi.py    <- Baixa a base de ruas (OpenStreetMap)',
    '|   |-- minerados_api_ruas.py     <- Enriquece a base via Nominatim',
    '|-- PdfExcelMultas/',
    '|   |-- pdfDeferidoIndeferido.py  <- Ferramenta 5',
    '|-- ProcessosAbertos/',
    '|   |-- processosAbertos.py       <- Ferramenta 6',
    '|-- EstatisticasSEI/',
    '|   |-- sei_estatisticas.py       <- Ferramenta 7',
    '|-- RemovedorDuplicadasDetran/',
    '|   |-- removerDuplicada.py       <- Ferramenta 8',
    '|-- Criptografia/',
    '|   |-- criptografia.py           <- Ferramenta 9 (entrada standalone)',
    '|   |-- gui.py                    <- Interface do criptografador',
    '|   |-- crypto.py                 <- AES-256-GCM e PBKDF2-SHA256',
    '|   |-- html_builder.py           <- Gerador do HTML autocontido',
    '|-- TarjarPDF/',
    '|   |-- interface_tarjar.py       <- Interface do tarjador',
    '|   |-- logica.py                 <- Ferramenta 10 (redacao + OCR)',
    '|   |-- tesseract/                <- Tesseract OCR embutido (por + eng)',
    '|-- BloquearPlanilha/',
    '    |-- gui.py                    <- Interface do bloqueador',
    '    |-- bloqueador.py             <- Ferramenta 11',
])
d.corpo('Cada ferramenta de 1 a 8 cria automaticamente três subpastas ao ser executada:')
d.tabela(
    ['Subpasta', 'Função'],
    [
        ['entrada/', 'Arquivo enviado pelo usuário para processar'],
        ['backup/', 'Cópia do arquivo original após o processamento'],
        ['resultados/', 'Arquivo(s) gerado(s) pela ferramenta'],
    ],
    larguras=[4.0, 11.5],
)
d.observacao(
    'A pasta entrada/ é limpa a cada execução: o orquestrador remove os arquivos antigos '
    'antes de copiar os novos, evitando que uma sobra de execução anterior seja '
    'reprocessada.'
)

# =============================================================================
d.h3('3. Fluxo de Uso (Ferramentas 1 a 8)')
d.passos([
    'O usuário clica em uma das ferramentas na tela principal.',
    'Um diálogo de seleção de arquivo abre — askopenfilename, ou askopenfilenames nas ferramentas 1 e 8, que aceitam vários arquivos.',
    'O arquivo escolhido é copiado para a pasta entrada/ da ferramenta.',
    'O processamento roda em uma thread separada, com o diretório de trabalho apontado para a pasta da ferramenta (a interface não trava).',
    'Ao finalizar, o orquestrador confere se algum arquivo novo apareceu em resultados/; havendo, exibe "Concluído" e o botão "Exportar Arquivo Pronto".',
    'O usuário salva o resultado onde quiser via diálogo de salvamento — o arquivo mais recente de resultados/ é copiado para o destino.',
    'O botão de pasta ao lado de cada ferramenta abre o Explorer na pasta da ferramenta.',
])
d.observacao(
    'O orquestrador aceita uma execução por vez: enquanto uma ferramenta estiver rodando, '
    'novos cliques retornam "Aguarde o processamento atual terminar."'
)
d.corpo(
    'Ferramentas 9 (Criptografar), 10 (Tarjar PDF) e 11 (Bloquear Planilha) abrem uma '
    'janela própria dentro do Hub, com interface dedicada. Elas não usam as pastas '
    'entrada/, backup/ e resultados/ nem o botão de exportar: as 9 e 11 pedem o destino '
    'em um diálogo de salvamento, e a 10 grava o PDF ao lado do arquivo original.'
)

# =============================================================================
d.h3('4. Ferramentas')

# ── 4.1 ──────────────────────────────────────────────────────────────────────
d.h4('4.1  Latitude e Longitude')
d.rotulo('Arquivo', 'LatitudeLongitude/enderecos.py')
d.h5('O que faz')
d.corpo(
    'Recebe uma planilha com coordenadas geográficas (latitude/longitude) e enriquece '
    'cada linha com o endereço completo correspondente (rua, bairro, número, cidade, CEP, '
    'estado) via geocodificação reversa usando a API pública OpenStreetMap/Nominatim.'
)
d.h5('Arquivos aceitos')
d.tabela(
    ['Formato', 'Extensão'],
    [
        ['Planilha Excel', '.xlsx, .xls'],
        ['CSV com separador ponto-e-vírgula', '.csv'],
    ],
    larguras=[8.0, 7.5],
)
d.h5('Como processa')
d.marcadores([
    'Identifica colunas de latitude e longitude por nome (latitude, lat, y, longitude, lon, lng, x) ou por faixa de valores.',
    'Usa a API Nominatim com RateLimiter (mínimo 1,2 s entre requisições) para respeitar os limites da API gratuita.',
    'Mantém cache local (cache_enderecos.json) — coordenadas já consultadas não são buscadas novamente. O instalador inclui cache pré-preenchido.',
    'O cache é salvo a cada 10 novas entradas para evitar perda em caso de interrupção.',
    'Coordenadas sem endereço encontrado são registradas em coordenadas_nao_encontradas.txt.',
    'Aceita seleção múltipla: vários arquivos processados na mesma execução são consolidados em uma planilha única.',
    'Detecta pela mediana de cada coluna quando o arquivo veio com latitude e longitude trocadas, inverte os valores antes da consulta e avisa no log.',
    'Nenhuma coluna do arquivo original é sobrescrita: havendo conflito de nome, o dado do OpenStreetMap recebe o sufixo _OSM.',
])
d.h5('Colunas adicionadas')
d.tabela(
    ['Coluna', 'Conteúdo'],
    [
        ['Endereco_Rua', 'Nome da rua/logradouro'],
        ['Bairro', 'Bairro — vira Bairro_OSM quando a planilha já tem uma coluna com esse nome'],
        ['Numero_Imovel', 'Número do imóvel'],
        ['Cidade', 'Município'],
        ['CEP', 'Código postal'],
        ['Estado', 'Estado'],
    ],
    larguras=[5.0, 10.5],
)
d.h5('Saída gerada')
d.tabela(
    ['Arquivo', 'Quando é gerado'],
    [
        ['{nome}_corrigido.xlsx', 'Um único arquivo de entrada'],
        ['planilha_consolidada_corrigida.xlsx', 'Vários arquivos processados juntos'],
        ['coordenadas_nao_encontradas.txt', 'Sempre que alguma coordenada não retornar endereço'],
    ],
    larguras=[6.5, 9.0],
)
d.observacao('Depende de conexão com a internet.')

# ── 4.2 ──────────────────────────────────────────────────────────────────────
d.h4('4.2  Limpeza de Arquivos')
d.rotulo('Arquivo', 'LimpezaArquivo/limpeza.py')
d.h5('O que faz')
d.corpo(
    'Recebe planilhas de cadastro ou fiscalização e realiza limpeza profunda dos dados: '
    'corrige texto mal codificado (mojibake), padroniza nomes de logradouros, normaliza '
    'capitalização, valida endereços via geocodificação e gera relatório de todas as '
    'alterações realizadas.'
)
d.h5('Como processa')
d.marcadores([
    'Tenta automaticamente múltiplas combinações de encoding (utf-8, cp1252, latin-1) e separador até encontrar leitura válida (mínimo 15 colunas).',
    'Calcula hash SHA-256 do arquivo original para rastreabilidade.',
    'Corrige mojibake por re-decodificação latin1→utf-8, com até 5 passagens iterativas.',
    'Aplica capitalização inteligente — artigos "da", "de", "do" ficam em minúsculo.',
    'Expande abreviações: R. → Rua, Av. → Av., Estr. → Estrada, Tv. → Travessa, Pça. → Praça.',
    'Valida endereço e bairro via Nominatim para obter o nome oficial do logradouro em Niterói/RJ.',
])
d.h5('Saídas geradas')
d.tabela(
    ['Arquivo', 'Conteúdo'],
    [
        ['{nome}_LIMPO.xlsx', 'Planilha com todos os dados corrigidos'],
        ['{nome}_RELATORIO.xlsx', 'Registro de cada alteração: campo, valor original e corrigido'],
    ],
    larguras=[6.0, 9.5],
)

# ── 4.3 ──────────────────────────────────────────────────────────────────────
d.h4('4.3  Organizador TXT Detran')
d.rotulo('Arquivo', 'OrganizadorTxtDetran/decifradorTxt.py')
d.h5('O que faz')
d.corpo(
    'Converte arquivos .txt de posição fixa exportados pelo sistema do DETRAN/RJ em '
    'planilhas Excel estruturadas e legíveis, extraindo cada campo pela sua posição exata '
    'no layout do arquivo. Cria também uma coluna "Descrição sem Número" com o logradouro '
    'limpo logo após a coluna original.'
)
d.h5('Layout — campos por posição de caractere')
d.tabela(
    ['Posição', 'Campo'],
    [
        ['0 – 6', 'Código do Órgão Atuador'],
        ['6 – 9', 'Código da Infração'],
        ['11 – 71', 'Descrição da Infração'],
        ['71 – 91', 'Tipo de Enquadramento'],
        ['91 – 103', 'Auto'],
        ['103 – 111', 'Data (AAAAMMDD → DD/MM/AAAA)'],
        ['111 – 117', 'Hora (HHMMSS → HH:MM:SS)'],
        ['158 – 167', 'Valor da Infração (centavos → R$ 0,00)'],
        ['174 – 181', 'Placa do Veículo'],
        ['233 – 293', 'Nome do Infrator'],
        ['293 – 337', 'Logradouro'],
        ['388 +', 'Descrição do Município do Endereço + coluna extra sem número'],
    ],
    larguras=[4.0, 11.5],
)
d.h5('Saída gerada')
d.corpo('{nome}_normalizado.xlsx, com uma coluna para cada campo do layout.')

# ── 4.4 ──────────────────────────────────────────────────────────────────────
d.h4('4.4  Organizador Detran Limpo')
d.rotulo('Arquivo', 'DetranLimpo/detranLimpo.py')
d.h5('O que faz')
d.corpo(
    'Recebe planilhas que contenham uma coluna de endereço (por exemplo, a saída do '
    'Organizador TXT Detran ou arquivos exportados diretamente do sistema GAIDE) e cria '
    'ou atualiza uma coluna "Rua" com o logradouro limpo, sem número e sem referências de '
    'cruzamento ou sufixos de posição.'
)
d.h5('Arquivos aceitos')
d.tabela(
    ['Formato', 'Extensão'],
    [['Planilha Excel', '.xlsx, .xls'], ['CSV', '.csv']],
    larguras=[8.0, 7.5],
)
d.h5('Regras de limpeza')
d.marcadores([
    'Remove número do final do endereço: "AV. BRASIL 341" → "AV. BRASIL".',
    'Remove "N" abreviado de número: "RUA BARÃO DO AMAZONAS N 340" → "RUA BARÃO DO AMAZONAS".',
    'Remove sufixos de posição: OP., OP. OP., OPOSTO, LADO OP.',
    'Remove referências de cruzamento: "COM RUA SÃO PEDRO", "C/ R. BARÃO…", "CRUZAMENTO COM…".',
    'Reconhece faixas de números: "151 AO 251" e remove o intervalo inteiro.',
])
d.h5('Comportamento da coluna Rua')
d.tabela(
    ['Situação', 'Ação'],
    [
        ['Coluna "Rua" não existe', 'Cria a coluna logo após o campo de endereço'],
        ['Coluna "Rua" existe (qualquer valor)', 'Sempre sobrescreve com o valor limpo do endereço'],
    ],
    larguras=[6.0, 9.5],
)
d.h5('Base de apoio')
d.corpo(
    'A pasta da ferramenta traz ruas_oficiais_niteroi.json, com os logradouros oficiais do '
    'município. Os scripts baixar_base_niteroi.py (consulta ao OpenStreetMap) e '
    'minerados_api_ruas.py (enriquecimento via Nominatim) são utilitários de manutenção '
    'dessa base — não são chamados pelo Hub durante o uso normal.'
)
d.observacao(
    'Se a coluna de endereço não for localizada, o erro exibido lista todas as colunas que '
    'a ferramenta enxergou no arquivo, o que facilita identificar planilha fora do padrão.'
)

# ── 4.5 ──────────────────────────────────────────────────────────────────────
d.h4('4.5  PDF e Excel Multas')
d.rotulo('Arquivo', 'PdfExcelMultas/pdfDeferidoIndeferido.py')
d.h5('O que faz')
d.corpo(
    'Extrai dados de processos julgados (Deferido/Indeferido) a partir de relatórios PDF '
    'gerados pelo sistema GAIDE/Niterói e consolida todos os registros em uma única '
    'planilha Excel.'
)
d.h5('Desafios do PDF e como são tratados')
d.marcadores([
    'CNPJ quebrado em duas linhas: reunificado antes da extração.',
    'Placa isolada abaixo do nome do proprietário: fundida à linha correta.',
    'Sobrenome do relator em linha separada: lista configurável de sobrenomes conhecidos.',
    'Texto de infração espalhado por múltiplas linhas: concatenado até o próximo marcador.',
    'Linhas de cabeçalho e rodapé descartadas por regex.',
])
d.h5('Saída gerada')
d.tabela(
    ['Arquivo', 'Colunas'],
    [['relatorio_processos_{data_hora}.xlsx',
      'Arquivo, Página, CPF/CNPJ, Proprietário, Placa, Processo, Data de Abertura, '
      'Data Resultado, Resultado, Relator']],
    larguras=[6.0, 9.5],
)

# ── 4.6 ──────────────────────────────────────────────────────────────────────
d.h4('4.6  Processos Abertos')
d.rotulo('Arquivo', 'ProcessosAbertos/processosAbertos.py')
d.h5('O que faz')
d.corpo(
    'Lê o relatório "Relatório de Processos Abertos — 1ª Instância" exportado pelo sistema '
    'GAIDE/DETRAN em formato PDF e extrai todos os registros organizados por data de '
    'abertura, gerando uma planilha Excel estruturada.'
)
d.h5('Colunas do arquivo de saída')
d.tabela(
    ['Coluna', 'Conteúdo'],
    [
        ['Data de Abertura', 'Data no formato DD/MM/AAAA'],
        ['SEQ', 'Número sequencial do registro'],
        ['Requerimento', 'Tipo: 0P, 1P, 2C, etc.'],
        ['Nº Processo', 'Número do processo administrativo'],
        ['Nº Auto', 'Número do auto de infração'],
        ['Login', 'Login do usuário responsável'],
        ['Arquivo', 'Nome do PDF de origem'],
    ],
    larguras=[4.0, 11.5],
)
d.corpo('Saída: processos_abertos_{data_hora}.xlsx.')

# ── 4.7 ──────────────────────────────────────────────────────────────────────
d.h4('4.7  Estatísticas SEI')
d.rotulo('Arquivo', 'EstatisticasSEI/sei_estatisticas.py')
d.h5('O que faz')
d.corpo(
    'Lê o relatório "Estatísticas da Unidade" exportado do SEI em PDF e gera, na mesma '
    'execução, um gráfico de barras horizontais (.png) e uma planilha consolidada (.xlsx) '
    'com a quantidade de processos por tipo.'
)
d.h5('Como processa')
d.marcadores([
    'Usa pdfplumber para extrair o texto e as tabelas do PDF.',
    'Identifica a unidade por expressão regular sobre o trecho "no período (…)", descartando o sufixo "/NITEROI".',
    'Localiza a tabela de processos pela presença do prefixo "Administrativo:" e a de documentos pela ausência dele.',
    'Reconhece uma linha como tipo de processo pelo padrão "Categoria: Nome" — o que descarta cabeçalhos como "Tipo", cuja coluna ao lado traz o ano e virava uma barra falsa.',
    'Renderiza o gráfico com matplotlib no backend Agg, sem abrir janela (evita o erro "main thread is not in main loop" ao rodar em thread).',
])
d.h5('Nomenclatura das categorias')
d.corpo(
    'A tradução para a nomenclatura interna vale apenas para a unidade '
    'NIT/NITTRANS/DIVDOC. Nas demais divisões, cada tipo é exibido com o nome original do '
    'SEI e os tipos zerados são omitidos, já que ali a lista vem dos dados e não é fixa.'
)
d.tabela(
    ['Categoria no relatório do SEI', 'Nome usado no gráfico/Excel (apenas DIVDOC)'],
    [
        ['Administrativo: Defesa Prévia', 'Defesa Prévia'],
        ['Administrativo: Troca de Real Infrator', 'Trocar de Real Infrator'],
        ['Administrativo: Auto de Infração', 'Decreto N° 743/2026 Rotativo'],
        ['Administrativo: Recursos', 'Defesa 1° e 2° Instancia'],
        ['Financeiro: Cancelamento de Lançamentos', 'Formulário de Ajuste de Recurso'],
        ['Administrativo: Requerimento Geral/Envio de Expedientes Diversos', 'Auto de Infração'],
    ],
    larguras=[8.5, 7.0],
)
d.corpo(
    'Tipos de processo fora desse mapeamento entram no gráfico com o nome real lido do '
    'PDF, em laranja, ordenados do maior para o menor. O que restar do total do relatório '
    'sem se encaixar em nenhum tipo é somado à barra cinza "Outros (Não Listados)".'
)
d.h5('Escala do gráfico')
d.corpo(
    'As marcas do eixo horizontal são definidas por MaxNLocator (no máximo dez marcas '
    'inteiras) e a altura da figura cresce conforme o número de barras. A versão anterior '
    'fixava ax.set_xticks(range(0, max+2)), o que gerava centenas de marcas sobrepostas '
    'quando algum tipo passava da casa das dezenas.'
)
d.h5('Saídas geradas')
d.tabela(
    ['Arquivo', 'Conteúdo'],
    [
        ['Grafico_Estatisticas.png',
         'Gráfico de barras horizontais, 300 dpi, com o título "Estatísticas da Unidade" '
         'seguido do nome da unidade'],
        ['Relatorio_Consolidado.xlsx',
         'Colunas Unidade, Tipo de Processo e Quantidade'],
    ],
    larguras=[5.5, 10.0],
)
d.observacao(
    'Ao final, o gráfico é aberto no visualizador padrão do Windows via os.startfile. Se o '
    'Excel de saída estiver aberto em outro programa, a gravação falha com "O arquivo '
    'Excel antigo está aberto!".'
)

# ── 4.8 ──────────────────────────────────────────────────────────────────────
d.h4('4.8  Mesclar e Remover Duplicadas')
d.rotulo('Arquivo', 'RemovedorDuplicadasDetran/removerDuplicada.py')
d.h5('O que faz')
d.corpo(
    'Consolida várias planilhas em um único arquivo, descartando as linhas repetidas. '
    'Aceita seleção múltipla de arquivos na janela do Hub.'
)
d.h5('Como processa')
d.marcadores([
    'Lê um arquivo por vez e concatena na base acumulada, em vez de carregar tudo de uma só vez.',
    'Aplica drop_duplicates a cada arquivo incorporado — a base intermediária nunca cresce mais que o necessário.',
    'Libera o DataFrame temporário da memória a cada iteração (del + garbage collector), o que permite consolidar bases grandes.',
    'A comparação de duplicidade considera a linha inteira, não uma coluna-chave.',
])
d.h5('Saída gerada')
d.corpo(
    'Estatisticas_Niteroi_Consolidado.csv — CSV com separador ponto-e-vírgula e encoding '
    'utf-8-sig, que abre diretamente no Excel com os acentos corretos.'
)

# ── 4.9 ──────────────────────────────────────────────────────────────────────
d.h4('4.9  Criptografar Arquivos')
d.rotulo('Arquivos', 'Criptografia/crypto.py, html_builder.py, gui.py')
d.h5('O que faz')
d.corpo(
    'Criptografa qualquer tipo de arquivo (Excel, PDF, Word, TXT) com uma senha definida '
    'pelo usuário e gera um arquivo HTML autocontido. O destinatário abre o HTML em '
    'qualquer navegador, digita a senha e o arquivo original é baixado já descriptografado '
    'diretamente na máquina dele — sem passar por nenhum servidor.'
)
d.h5('Fluxo completo')
d.passos([
    'Usuário seleciona o arquivo e digita uma senha (com confirmação).',
    'O app gera um arquivo .html com os dados cifrados embutidos.',
    'O .html é enviado ao destinatário (e-mail, WhatsApp, pendrive etc.).',
    'O destinatário abre o .html no navegador e digita a senha.',
    'O arquivo original é baixado diretamente pelo navegador — sem servidor intermediário.',
])
d.h5('Camadas de segurança')
d.tabela(
    ['Camada', 'Técnica', 'Por que protege'],
    [
        ['Derivação de senha', 'PBKDF2-SHA256, 480.000 iterações',
         'Torna ataques de força bruta extremamente lentos — testar milhões de senhas por '
         'segundo se torna inviável'],
        ['Sal aleatório', '16 bytes aleatórios por arquivo',
         'Mesmo cifrando o mesmo arquivo com a mesma senha duas vezes, os resultados são '
         'completamente diferentes. Elimina ataques por tabela pré-calculada'],
        ['Cifra simétrica', 'AES-256-GCM',
         'Padrão usado por governos e bancos. O modo GCM autentica os dados: qualquer '
         'alteração no arquivo cifrado é detectada imediatamente'],
        ['Processamento local', 'Web Crypto API (nativa do navegador)',
         'A descriptografia ocorre 100% no navegador do destinatário. O arquivo nunca '
         'trafega pela rede em aberto'],
    ],
    larguras=[3.3, 3.7, 8.5],
)
d.h5('Proteção contra tentativas repetidas')
d.corpo(
    'O HTML gerado possui bloqueio progressivo embutido: cada senha errada dobra o tempo '
    'de espera até a próxima tentativa (2 s, 4 s, 8 s…). Após 10 tentativas erradas, o '
    'arquivo é bloqueado permanentemente naquele navegador. O estado é salvo no '
    'localStorage, portanto fechar e reabrir o navegador não reseta o contador.'
)
d.h5('Limitações conhecidas')
d.marcadores([
    'Senha fraca anula a proteção — a força está na senha escolhida pelo usuário.',
    'O bloqueio por tentativas é por navegador, não por arquivo. Um atacante com acesso ao .html pode tentá-lo em outro navegador.',
    'Máquina comprometida com malware pode capturar o arquivo após a descriptografia.',
])
d.corpo(
    'Para uso interno da NITTRANS — compartilhamento de planilhas e documentos por e-mail '
    'ou aplicativos de mensagem — o nível de segurança oferecido é equivalente ao usado em '
    'HTTPS e em cofres de senha profissionais.'
)

# ── 4.10 ─────────────────────────────────────────────────────────────────────
d.h4('4.10  Tarjar PDF')
d.rotulo('Arquivos', 'TarjarPDF/logica.py, TarjarPDF/interface_tarjar.py')
d.h5('O que faz')
d.corpo(
    'Recebe um arquivo PDF e oculta com bloco preto as informações pessoais sensíveis '
    'selecionadas, para adequação à LGPD. A tarja é destrutiva: o texto é removido do '
    'documento pelo apply_redactions do PyMuPDF, não apenas coberto por um retângulo.'
)
d.h5('Campos tarjados')
d.tabela(
    ['Campo', 'O que reconhece'],
    [
        ['CPF', 'Com ou sem pontuação (000.000.000-00 ou 11 dígitos seguidos)'],
        ['RG', 'Formatos com 1 a 3 dígitos no primeiro grupo, incluindo o padrão do DETRAN-RJ, e variantes com dígito X'],
        ['E-mail', 'Qualquer endereço no formato usuario@dominio.ext'],
        ['CNPJ', 'Com ou sem pontuação (00.000.000/0000-00 ou 14 dígitos seguidos)'],
        ['Palavras manuais', 'Lista livre digitada pelo usuário, uma por linha'],
    ],
    larguras=[4.0, 11.5],
)
d.h5('Como processa')
d.marcadores([
    'Varre o texto de cada página em busca dos padrões marcados, via expressões regulares com limitadores para não capturar números maiores por engano.',
    'Aplica uma exceção para não tarjar matrículas funcionais da NITTRANS, que seguem formato parecido com o de RG.',
    'Termos manuais de uma palavra são comparados token a token, o que evita tarjar trechos maiores que contenham o termo; termos com espaço são buscados como frase.',
    'Aciona OCR (Tesseract em português, 300 dpi) quando a página tem menos de 50 caracteres extraíveis ou contém alguma imagem embutida — cobre tanto o PDF 100% escaneado quanto a foto de documento colada em página com texto.',
    'O resultado do OCR é reaproveitado como textpage na busca, e não descartado.',
    'As tarjas só são aplicadas nas páginas em que algo foi encontrado.',
])
d.h5('Saída gerada')
d.corpo(
    '{nome}_higienizado.pdf, gravado na mesma pasta do arquivo original. Ao final, a '
    'janela informa quantas ocorrências foram ocultadas.'
)
d.observacao(
    'As quatro caixas de seleção começam desmarcadas. O Tesseract é distribuído dentro de '
    'TarjarPDF/tesseract e apontado por variáveis de ambiente em tempo de execução — não '
    'depende de instalação no sistema.'
)

# ── 4.11 ─────────────────────────────────────────────────────────────────────
d.h4('4.11  Bloquear Planilha')
d.rotulo('Arquivos', 'BloquearPlanilha/bloqueador.py, BloquearPlanilha/gui.py')
d.h5('O que faz')
d.corpo(
    'Aplica formatação padronizada em uma planilha Excel e protege a aba com senha, '
    'usando openpyxl. A janela pede o arquivo, a senha e a confirmação da senha antes de '
    'abrir o diálogo de salvamento.'
)
d.h5('Formatação aplicada')
d.marcadores([
    'Primeira linha tratada como cabeçalho: preenchimento 1F4E78, fonte Calibri 11 branca em negrito e alinhamento centralizado.',
    'Demais células em Calibri 11, com bordas finas (D3D3D3) em toda a área preenchida.',
    'Números alinhados à direita e textos à esquerda, ambos centralizados na vertical.',
    'Largura de cada coluna ajustada ao maior conteúdo, com mínimo de 12 caracteres.',
    'Linhas de grade mantidas visíveis.',
])
d.h5('Proteção')
d.corpo(
    'A proteção é aplicada na aba ativa (ws.protection.sheet = True) com a senha '
    'informada. O parâmetro modo_bloqueio já existe na assinatura da função, com "total" '
    'como padrão e "parcial" reservado para uma futura opção de bloqueio por intervalo.'
)
d.observacao(
    'A proteção de planilha do Excel evita edição acidental, mas não criptografa o '
    'conteúdo — para sigilo real do arquivo, use a ferramenta 9.'
)

# =============================================================================
d.h3('5. Dependências e Bibliotecas')
d.tabela(
    ['Biblioteca', 'Uso'],
    [
        ['customtkinter', 'Interface gráfica das janelas do Hub'],
        ['Pillow (PIL)', 'Carregamento e composição das imagens de fundo e logos'],
        ['pandas', 'Leitura, manipulação e exportação de planilhas'],
        ['openpyxl', 'Escrita de .xlsx, formatação e proteção de planilha (ferramenta 11)'],
        ['xlrd', 'Leitura de arquivos .xls (formato legado)'],
        ['geopy', 'Geocodificação via Nominatim/OpenStreetMap (ferramentas 1, 2 e 4)'],
        ['pdfplumber', 'Extração de texto e tabelas de PDFs (ferramentas 5, 6 e 7)'],
        ['PyMuPDF (fitz)', 'Redação de PDFs e OCR integrado (ferramenta 10)'],
        ['Tesseract OCR', 'Reconhecimento de texto em PDFs escaneados — embutido no projeto'],
        ['matplotlib', 'Geração do gráfico de barras, backend Agg (ferramenta 7)'],
        ['cryptography', 'AES-256-GCM e PBKDF2-SHA256 (ferramenta 9)'],
        ['requests', 'Download da base de ruas de Niterói (utilitário do Detran Limpo)'],
        ['tqdm', 'Barra de progresso (ativa apenas no terminal)'],
        ['unicodedata', 'Normalização de texto e correção de encoding (stdlib)'],
    ],
    larguras=[4.0, 11.5],
)
d.observacao(
    'O requirements.txt cobre as dependências de desenvolvimento mais usadas, mas não '
    'lista cryptography, PyMuPDF, xlrd e requests, que também são necessárias para rodar o '
    'projeto a partir do código-fonte. No executável isso não afeta nada: o PyInstaller '
    'resolve as dependências pelo hub.spec.'
)

# =============================================================================
d.h3('6. Build e Distribuição')
d.corpo('O script build.ps1 automatiza todo o processo de empacotamento:')
d.passos([
    'Verifica se o PyInstaller está instalado.',
    'Verifica se logo.ico existe.',
    'Remove builds anteriores (build/ e dist/).',
    'Empacota com PyInstaller a partir do hub.spec — gera dist/HubNITTRANS/. Os metadados de autoria definidos em version_info.txt são embutidos no .exe e ficam visíveis em Propriedades → Detalhes no Windows Explorer.',
    'Compila o instalador com Inno Setup — gera installer/Output/Setup_HubNITTRANS_v5.1.exe.',
    'O instalador inclui os caches pré-preenchidos. Em instalações novas eles são copiados; em reinstalações o cache acumulado do usuário é preservado (flag onlyifdoesntexist).',
])
d.corpo(
    'O hub.spec empacota como dados a pasta TarjarPDF/tesseract, o fundo das janelas, a '
    'logo e o ícone, e declara como hiddenimports os módulos que o PyInstaller não '
    'descobre sozinho por serem importados dinamicamente.'
)
d.tabela(
    ['Item', 'Detalhe'],
    [
        ['Versão atual', '5.1'],
        ['Tamanho do instalador', '~116 MB'],
        ['Compressão', 'lzma2/ultra64'],
        ['Diretório de instalação', '%LOCALAPPDATA%\\Programs\\HubNITTRANS\\'],
        ['Requer administrador?', 'Não (PrivilegesRequired=lowest)'],
        ['Idioma do instalador', 'Português do Brasil'],
        ['Atalho na área de trabalho', 'Opcional (marcado por padrão no instalador)'],
        ['Metadados de autoria', 'Visíveis em Propriedades → Detalhes do HubNITTRANS.exe'],
        ['Desinstalação', 'Configurações → Aplicativos → Hub de Ferramentas NITTRANS'],
    ],
    larguras=[5.0, 10.5],
)

d.salvar(SAIDA)
print(f'Documento gerado: {os.path.abspath(SAIDA)}')
