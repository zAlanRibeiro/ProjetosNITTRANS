# -*- coding: utf-8 -*-
"""Gera o manual de uso do Hub de Ferramentas NITTRANS.

O visual vem de doc_modelo.py, que monta o documento em cima do modelo
"FERRAMENTA ESTATÍSTICAS SEI.docx".
"""
import os

from doc_modelo import DocumentoModelo

SAIDA = 'FERRAMENTAS HUB NITTRANS.docx'
DATA_DOC = 'Niterói, 29 de julho de 2026'

d = DocumentoModelo()

d.titulo('HUB DE FERRAMENTAS NITTRANS')
d.data(DATA_DOC)

d.doc.add_paragraph('Detalhamento:')
d.corpo(
    'O Hub de Ferramentas NITTRANS é um aplicativo para Windows que reúne, em uma única '
    'tela, as onze automações de dados usadas no dia a dia do Departamento de Gestão e '
    'Modernização. Cada ferramenta resolve uma tarefa que antes era feita à mão — '
    'converter coordenadas em endereços, limpar planilhas do DETRAN, ler relatórios em '
    'PDF do GAIDE e do SEI, tarjar dados pessoais, proteger arquivos com senha — e '
    'entrega o resultado já pronto para uso.'
)
d.corpo('De modo geral, o uso de qualquer ferramenta do Hub se resume a três coisas:')
d.marcador('escolher a ferramenta na tela principal;')
d.marcador('indicar o arquivo que será processado;')
d.marcador('salvar o resultado onde quiser.')
d.corpo(
    'Não é preciso instalar Python nem nenhuma outra dependência: tudo já vem embutido no '
    'instalador do Hub, que também não exige privilégios de administrador. Ao passar o '
    'mouse sobre qualquer botão, aparece uma dica resumindo o que aquela ferramenta faz.'
)
d.observacao(
    'Nenhuma ferramenta altera o arquivo original selecionado. O Hub trabalha sempre '
    'sobre uma cópia e grava o resultado em um arquivo novo.'
)

# ─────────────────────────────────────────────────────────────────────────────
d.h3('Como a tela do Hub é organizada')
d.corpo(
    'A janela principal tem os botões numerados de 1 a 11, na ordem em que aparecem. As '
    'oito primeiras ferramentas processam arquivos e ficam na parte de cima; abaixo da '
    'linha divisória fica a área "Segurança", com as três ferramentas que abrem uma '
    'janela própria.'
)
d.tabela(
    ['Nº', 'Ferramenta', 'Para que serve'],
    [
        ['1', 'Latitude e Longitude',
         'Transforma coordenadas geográficas em endereços completos'],
        ['2', 'Limpeza de Arquivos',
         'Corrige texto com acentuação quebrada e padroniza logradouros'],
        ['3', 'Organizador Txt Detran',
         'Converte o .txt do DETRAN/RJ em planilha Excel legível'],
        ['4', 'Organizador Detran Limpo',
         'Cria a coluna "Rua" com o logradouro sem número e sem cruzamentos'],
        ['5', 'PDF e Excel Multas',
         'Extrai processos deferidos/indeferidos dos PDFs do GAIDE'],
        ['6', 'Processos Abertos',
         'Lê o relatório de Processos Abertos — 1ª Instância em PDF'],
        ['7', 'Estatísticas SEI',
         'Lê o relatório de Estatísticas da Unidade do SEI e gera gráfico e planilha'],
        ['8', 'Mesclar e Remover Duplicadas',
         'Junta várias planilhas em uma só, sem linhas repetidas'],
        ['9', 'Criptografar Arquivos',
         'Protege um arquivo com senha e gera um HTML que só abre com ela'],
        ['10', 'Tarjar PDF',
         'Oculta CPF, RG, e-mail, CNPJ e palavras escolhidas em PDFs (LGPD)'],
        ['11', 'Bloquear Planilha',
         'Formata a planilha, destaca o cabeçalho e protege a aba com senha'],
    ],
    larguras=[1.2, 5.3, 9.0],
)
d.observacao(
    'A numeração dos botões é apenas a ordem na tela — não existe sequência obrigatória. '
    'Cada ferramenta funciona sozinha, na ordem que o trabalho pedir.'
)

# ─────────────────────────────────────────────────────────────────────────────
d.h3('Fluxo comum das ferramentas 1 a 8')
d.corpo(
    'As oito primeiras ferramentas se comportam exatamente da mesma forma. Aprendendo o '
    'caminho uma vez, ele vale para todas — muda apenas o tipo de arquivo que se '
    'seleciona e o resultado que sai no fim.'
)

d.h4('Passo 1 — Abrir a ferramenta')
d.corpo(
    'Na tela principal do Hub, clique no botão da ferramenta desejada. Ao passar o mouse '
    'sobre o botão antes de clicar, aparece uma dica com o resumo do que ela faz.'
)

d.h4('Passo 2 — Selecionar o arquivo de entrada')
d.corpo(
    'Uma janela do Windows é aberta com o título "Selecione o arquivo de ENTRADA para:" '
    'seguido do nome da pasta da ferramenta. Navegue até onde o arquivo está, selecione-o '
    'e confirme.'
)
d.observacao(
    'Duas ferramentas aceitam vários arquivos de uma vez: a 1 (Latitude e Longitude) e a '
    '8 (Mesclar e Remover Duplicadas). Nelas, segure Ctrl para marcar mais de um arquivo '
    'na janela de seleção. As demais processam um arquivo por vez.'
)
d.observacao(
    'Se a janela for fechada sem escolher nada, nada acontece — basta clicar de novo no '
    'botão da ferramenta para tentar outra vez.'
)

d.h4('Passo 3 — Aguardar o processamento')
d.corpo(
    'O Hub copia o arquivo escolhido para a pasta de trabalho da ferramenta e começa a '
    'processá-lo em segundo plano, sem travar a tela. Durante esse tempo aparece um '
    'indicador girando com a mensagem "Processando", o percentual e o tempo decorrido, '
    'junto de uma barra de progresso laranja.'
)
d.observacao(
    'A duração varia muito conforme a ferramenta. A maioria leva poucos segundos; as que '
    'consultam endereços pela internet (1 e 2) podem levar vários minutos, porque '
    'respeitam o limite de uma consulta por vez ao serviço gratuito do OpenStreetMap.'
)

d.h4('Passo 4 — Ver o resultado')
d.corpo('Quando o processamento termina, a tela do Hub mostra:')
d.marcador('a mensagem "✔ Concluído em [tempo] — [nome da ferramenta]", em verde;')
d.marcador('o botão verde "Exportar Arquivo Pronto", logo abaixo.')
d.corpo(
    'Na ferramenta 7 (Estatísticas SEI) há um extra: o gráfico gerado abre sozinho no '
    'visualizador de imagens padrão do Windows, sem precisar de nenhum clique.'
)

d.h4('Passo 5 — Exportar o arquivo pronto')
d.corpo(
    'Clique em "Exportar Arquivo Pronto" para abrir a janela "Salvar como" do Windows e '
    'escolher onde guardar o arquivo gerado. O nome já vem preenchido e pode ser alterado '
    'na hora de salvar.'
)
d.observacao(
    'Exportar é uma cópia, não uma mudança de lugar: o arquivo continua guardado na pasta '
    'da ferramenta dentro do Hub. Para chegar até ele mais tarde, clique no ícone de '
    'pasta ao lado do botão da ferramenta — o Explorer do Windows abre direto ali.'
)

d.subtitulo('Resumo visual do fluxo')
d.codigo([
    '[Arquivo de entrada]',
    '        |',
    '        v',
    '[Hub NITTRANS] --clique--> botao da ferramenta (1 a 8)',
    '        |',
    '        v',
    'Selecionar o arquivo na janela do Windows',
    '        |',
    '        v',
    'Processamento automatico (barra de progresso)',
    '        |',
    '        v',
    '"Concluido" + botao "Exportar Arquivo Pronto"',
    '        |',
    '        v',
    'Salvar o resultado onde quiser',
])

# ─────────────────────────────────────────────────────────────────────────────
d.h3('Como funcionam as ferramentas de segurança (9, 10 e 11)')
d.corpo(
    'As três ferramentas da área "Segurança" seguem um caminho diferente: em vez de '
    'processar em segundo plano e liberar o botão de exportar, elas abrem uma janela '
    'própria, onde o usuário escolhe o arquivo, define as opções e manda executar ali '
    'mesmo.'
)
d.passos([
    'Clicar no botão da ferramenta (9, 10 ou 11) — abre a janela dedicada.',
    'Selecionar o arquivo dentro dessa janela, pelo botão "Selecionar".',
    'Preencher o que a ferramenta pedir: senha, no caso das 9 e 11; o que deve ser tarjado, no caso da 10.',
    'Clicar no botão de ação da janela e aguardar a mensagem de conclusão.',
])
d.observacao(
    'Nessas três ferramentas o botão "Exportar Arquivo Pronto" do Hub não é usado. As '
    'ferramentas 9 e 11 já perguntam onde salvar durante a execução, e a 10 grava o PDF '
    'tarjado na mesma pasta do arquivo original.'
)

# ─────────────────────────────────────────────────────────────────────────────
d.h3('Ferramenta por ferramenta')

d.h4('1 — Latitude e Longitude')
d.corpo(
    'Recebe uma planilha que contenha colunas de latitude e longitude e devolve a mesma '
    'planilha com o endereço de cada coordenada preenchido, consultando o serviço público '
    'OpenStreetMap. As colunas acrescentadas são Endereco_Rua, Bairro, Numero_Imovel, '
    'Cidade, CEP e Estado.'
)
d.marcador(
    'As colunas de coordenada são reconhecidas pelo nome (latitude, lat, y, longitude, '
    'lon, lng, x) ou pela faixa de valores, então não é preciso renomear nada antes.'
)
d.marcador(
    'Coordenadas já consultadas antes ficam guardadas em um cache local e não são '
    'buscadas de novo — rodadas seguintes ficam bem mais rápidas.'
)
d.marcador(
    'Coordenadas sem endereço encontrado são listadas no arquivo '
    'coordenadas_nao_encontradas.txt, junto do resultado.'
)
d.marcador(
    'Se o arquivo vier com as colunas de latitude e longitude trocadas, a ferramenta '
    'percebe e inverte sozinha antes de buscar os endereços.'
)
d.marcador(
    'As colunas do arquivo original nunca são substituídas: quando o nome já existe na '
    'planilha (o caso mais comum é "Bairro"), o dado encontrado entra em uma coluna '
    'nova, com o final _OSM.'
)
d.observacao('Esta ferramenta precisa de internet para funcionar.')

d.h4('2 — Limpeza de Arquivos')
d.corpo(
    'Feita para planilhas de cadastro e fiscalização que chegam com problemas de '
    'formatação. Corrige texto com acentuação quebrada (o famoso "Ã§" no lugar do "ç"), '
    'padroniza a escrita dos logradouros, ajusta maiúsculas e minúsculas e confere o nome '
    'oficial da rua em Niterói.'
)
d.marcador('Descobre sozinha a codificação e o separador do arquivo, testando as combinações mais comuns.')
d.marcador('Expande abreviações: R. vira Rua, Estr. vira Estrada, Tv. vira Travessa, Pça. vira Praça.')
d.marcador('Mantém artigos em minúsculo na capitalização: "Rua do Ouvidor", e não "Rua Do Ouvidor".')
d.corpo(
    'Gera dois arquivos: a planilha limpa e um relatório com cada alteração feita, campo '
    'a campo, mostrando o valor antes e depois. Esse relatório serve de conferência antes '
    'de dar o dado por bom.'
)

d.h4('3 — Organizador Txt Detran')
d.corpo(
    'Converte os arquivos .txt exportados pelo sistema do DETRAN/RJ — aqueles em que tudo '
    'vem grudado em uma linha só — em uma planilha Excel com uma coluna para cada '
    'informação: órgão atuador, código e descrição da infração, auto, data, hora, valor, '
    'placa, nome do infrator, logradouro e município.'
)
d.marcador('Data e hora saem já formatadas (DD/MM/AAAA e HH:MM:SS), e o valor da infração convertido de centavos para reais.')
d.marcador('Cria também a coluna "Descrição sem Número", com o logradouro limpo, logo ao lado da coluna original.')

d.h4('4 — Organizador Detran Limpo')
d.corpo(
    'Recebe uma planilha que tenha uma coluna de endereço — normalmente a saída da '
    'ferramenta 3 ou um arquivo exportado do GAIDE — e cria a coluna "Rua" com o '
    'logradouro limpo, pronto para agrupamentos e contagens por rua.'
)
d.corpo('São removidos do endereço:')
d.marcador('o número no fim: "AV. BRASIL 341" vira "AV. BRASIL";')
d.marcador('faixas de números, como "151 AO 251";')
d.marcador('sufixos de posição: OP., OPOSTO, LADO OP.;')
d.marcador('referências de cruzamento: "COM RUA SÃO PEDRO", "C/ R. BARÃO…", "CRUZAMENTO COM…".')
d.observacao(
    'Se a coluna "Rua" já existir na planilha, ela é sempre sobrescrita com o valor '
    'recalculado. Se não existir, é criada logo após a coluna de endereço.'
)

d.h4('5 — PDF e Excel Multas')
d.corpo(
    'Lê os relatórios em PDF de processos julgados do sistema GAIDE/Niterói e consolida '
    'todos os registros em uma única planilha, com as colunas Arquivo, Página, CPF/CNPJ, '
    'Proprietário, Placa, Processo, Data de Abertura, Data Resultado, Resultado e Relator.'
)
d.corpo(
    'A ferramenta já trata sozinha as quebras típicas desse PDF: CNPJ partido em duas '
    'linhas, placa isolada abaixo do nome do proprietário, sobrenome do relator em linha '
    'separada e texto de infração espalhado por várias linhas.'
)

d.h4('6 — Processos Abertos')
d.corpo(
    'Lê o "Relatório de Processos Abertos — 1ª Instância" exportado em PDF e gera uma '
    'planilha organizada por data de abertura, com as colunas Data de Abertura, SEQ, '
    'Requerimento, Nº Processo, Nº Auto, Login e Arquivo.'
)

d.h4('7 — Estatísticas SEI')
d.corpo(
    'Lê o relatório "Estatísticas da Unidade" exportado do SEI em PDF e gera, de uma vez '
    'só, um gráfico de barras pronto para colar em apresentações e uma planilha '
    'consolidada com as mesmas informações. A unidade é identificada automaticamente a '
    'partir do texto do relatório — não existe tela para escolhê-la.'
)
d.corpo(
    'Para gerar o PDF de entrada: acessar o SEI, abrir "Estatísticas da Unidade", '
    'selecionar o período desejado e salvar a página como PDF pela opção de impressão do '
    'navegador.'
)
d.corpo(
    'O nome que aparece em cada barra depende da unidade identificada no relatório:'
)
d.marcador(
    'na unidade NIT/NITTRANS/DIVDOC, os tipos de processo são exibidos com a nomenclatura '
    'interna da divisão (por exemplo, "Administrativo: Requerimento Geral/Envio de '
    'Expedientes Diversos" aparece como "Auto de Infração");'
)
d.marcador(
    'em qualquer outra unidade, cada tipo aparece com o nome original do SEI, sem '
    'tradução.'
)
d.corpo(
    'Tipos de processo que não fazem parte da lista interna da DIVDOC aparecem no gráfico '
    'com o nome real que veio do PDF, em laranja, para ficarem fáceis de identificar. O '
    'que sobrar do total do relatório sem se encaixar em nenhum tipo é somado à barra '
    'cinza "Outros (Não Listados)".'
)
d.observacao(
    'Ao final, o gráfico abre sozinho no visualizador de imagens do Windows. A planilha '
    'fica disponível pelo botão "Exportar Arquivo Pronto".'
)

d.h4('8 — Mesclar e Remover Duplicadas')
d.corpo(
    'Junta várias planilhas em um único arquivo e descarta as linhas repetidas, '
    'comparando a linha inteira. É a ferramenta usada para consolidar bases que chegam '
    'divididas por mês, por lote ou por origem.'
)
d.marcador('Aceita vários arquivos de uma vez — segure Ctrl na janela de seleção.')
d.marcador('A remoção de duplicadas acontece a cada arquivo lido, o que permite consolidar bases grandes sem estourar a memória.')
d.marcador('O resultado sai em CSV separado por ponto-e-vírgula, que abre direto no Excel.')

d.h4('9 — Criptografar Arquivos')
d.corpo(
    'Protege um arquivo com senha e devolve um arquivo .html. Esse HTML pode ser enviado '
    'por e-mail, WhatsApp ou pendrive: quem recebe abre o arquivo em qualquer navegador, '
    'digita a senha combinada e o documento original é baixado já aberto na máquina dele. '
    'Nada é enviado para nenhum servidor — a abertura acontece dentro do próprio '
    'navegador de quem recebeu.'
)
d.corpo(
    'A proteção usa AES-256-GCM, o mesmo padrão de bancos e de sites com cadeado, com a '
    'senha reforçada por 480 mil rodadas de embaralhamento. Cada senha errada dobra o '
    'tempo de espera para a tentativa seguinte e, após dez erros, o arquivo é bloqueado '
    'naquele navegador.'
)
d.observacao(
    'A senha é a única chave: se ela for perdida, não existe forma de recuperar o '
    'conteúdo. Combine a senha por um canal diferente daquele em que o arquivo foi '
    'enviado.'
)

d.h4('10 — Tarjar PDF')
d.corpo(
    'Oculta dados pessoais em PDFs com tarjas pretas, para adequação à LGPD. Na janela da '
    'ferramenta há quatro caixas de seleção — CPF, RG, E-mail e CNPJ — e um campo livre '
    'para digitar palavras a serem tarjadas, uma por linha (nomes, números de processo, '
    'placas).'
)
d.marcador('As quatro caixas começam desmarcadas: marque o que precisa ser ocultado antes de executar.')
d.marcador(
    'Funciona também em PDFs escaneados: quando a página é uma imagem, a ferramenta faz o '
    'reconhecimento de texto automaticamente antes de procurar os dados.'
)
d.marcador(
    'Matrículas de servidor da NITTRANS são reconhecidas e preservadas, mesmo tendo '
    'formato parecido com o de RG.'
)
d.corpo(
    'Ao terminar, a janela informa quantas informações foram ocultadas e o arquivo '
    'tarjado é salvo na mesma pasta do original, com o sufixo _higienizado no nome.'
)
d.observacao(
    'A tarja é definitiva: o texto é removido do PDF, não apenas coberto por um retângulo '
    'preto. Confira o resultado antes de enviar.'
)

d.h4('11 — Bloquear Planilha')
d.corpo(
    'Aplica uma formatação padronizada na planilha e protege a aba com senha, impedindo '
    'que quem receber altere o conteúdo sem conhecê-la. Na janela da ferramenta são '
    'informados o arquivo, a senha e a confirmação da senha.'
)
d.corpo('A formatação aplicada é:')
d.marcador('primeira linha destacada como cabeçalho: fundo azul-escuro, texto branco em negrito e centralizado;')
d.marcador('fonte Calibri 11 nas demais células;')
d.marcador('bordas finas em toda a área preenchida;')
d.marcador('números alinhados à direita e textos à esquerda;')
d.marcador('largura das colunas ajustada ao maior conteúdo de cada uma.')
d.observacao(
    'A proteção vale para a aba ativa da planilha. Ao executar, o Windows já pergunta '
    'onde salvar, sugerindo o nome original com o prefixo protegido_.'
)

# ─────────────────────────────────────────────────────────────────────────────
d.h3('Entrada e saída de cada ferramenta')
d.corpo(
    'Resumo do que selecionar e do que é gerado. Nos nomes de arquivo, {nome} é o nome do '
    'arquivo enviado e {data_hora} é o momento do processamento.'
)
d.tabela(
    ['Ferramenta', 'O que selecionar', 'O que é gerado'],
    [
        ['1 — Latitude e Longitude', 'Planilha .xlsx, .xls ou .csv (1 ou mais)',
         '{nome}_corrigido.xlsx — ou planilha_consolidada_corrigida.xlsx, quando vários '
         'arquivos são enviados juntos'],
        ['2 — Limpeza de Arquivos', 'Planilha .xlsx, .xls ou .csv',
         '{nome}_LIMPO.xlsx e {nome}_RELATORIO.xlsx'],
        ['3 — Organizador Txt Detran', 'Arquivo .txt do DETRAN/RJ',
         '{nome}_normalizado.xlsx'],
        ['4 — Organizador Detran Limpo', 'Planilha .xlsx, .xls ou .csv com coluna de endereço',
         '{nome}_limpo_{data_hora}.xlsx'],
        ['5 — PDF e Excel Multas', 'PDF de processos julgados do GAIDE',
         'relatorio_processos_{data_hora}.xlsx'],
        ['6 — Processos Abertos', 'PDF do Relatório de Processos Abertos — 1ª Instância',
         'processos_abertos_{data_hora}.xlsx'],
        ['7 — Estatísticas SEI', 'PDF de Estatísticas da Unidade do SEI',
         'Grafico_Estatisticas.png e Relatorio_Consolidado.xlsx'],
        ['8 — Mesclar e Remover Duplicadas', 'Duas ou mais planilhas .xlsx ou .xls',
         'Estatisticas_Niteroi_Consolidado.csv'],
        ['9 — Criptografar Arquivos', 'Qualquer arquivo (PDF, Excel, Word, TXT) + senha',
         'Arquivo .html protegido, salvo onde o usuário escolher'],
        ['10 — Tarjar PDF', 'Arquivo .pdf + o que deve ser tarjado',
         '{nome}_higienizado.pdf, na mesma pasta do original'],
        ['11 — Bloquear Planilha', 'Planilha .xlsx ou .xls + senha',
         'protegido_{nome}.xlsx, salvo onde o usuário escolher'],
    ],
    larguras=[4.2, 5.3, 6.0],
)

# ─────────────────────────────────────────────────────────────────────────────
d.h3('Onde os arquivos ficam guardados')
d.corpo(
    'Cada uma das ferramentas de 1 a 8 tem sua própria pasta dentro do Hub e, dentro '
    'dela, três subpastas criadas automaticamente:'
)
d.tabela(
    ['Subpasta', 'O que fica nela'],
    [
        ['entrada', 'A cópia do arquivo enviado para processar'],
        ['backup', 'A cópia do arquivo original, preservada após o processamento'],
        ['resultados', 'Os arquivos gerados pela ferramenta'],
    ],
    larguras=[4.0, 11.3],
)
d.observacao(
    'A pasta entrada é esvaziada a cada nova execução da mesma ferramenta, e o conteúdo '
    'de resultados é substituído pelo processamento seguinte. Se o resultado precisa ser '
    'guardado, exporte-o antes de rodar de novo.'
)

# ─────────────────────────────────────────────────────────────────────────────
d.h3('Mensagens que podem aparecer')
d.tabela(
    ['Situação', 'O que a tela mostra', 'O que fazer'],
    [
        ['Processando',
         '"Processando [ferramenta]…" com indicador girando, percentual e tempo',
         'Apenas aguardar'],
        ['Concluído',
         '"✔ Concluído em [tempo] — [ferramenta]", em verde, com o botão de exportar',
         'Clicar em "Exportar Arquivo Pronto" e escolher onde salvar'],
        ['Duas execuções ao mesmo tempo',
         '"Aguarde o processamento atual terminar."',
         'Esperar a ferramenta em andamento terminar antes de clicar em outra'],
        ['Nenhum arquivo válido na entrada',
         '"✖ Erro ao processar: Coloque o arquivo…" ou "Nenhum arquivo encontrado…"',
         'Repetir o Passo 2 selecionando o arquivo no formato que a ferramenta espera'],
        ['Arquivo de saída aberto no Excel',
         '"✖ Erro ao processar: O arquivo Excel antigo está aberto!"',
         'Fechar a planilha gerada anteriormente e executar de novo'],
        ['Sem dados aproveitáveis no arquivo',
         '"Nenhum dado válido encontrado."',
         'Conferir se o arquivo enviado é mesmo o relatório esperado por aquela ferramenta'],
        ['Coluna de endereço não localizada (ferramenta 4)',
         '"Não achei a coluna de endereço no arquivo…", seguido das colunas encontradas',
         'Conferir na lista exibida se a planilha realmente tem a coluna de endereço'],
        ['Senhas diferentes (ferramentas 9 e 11)',
         '"As senhas digitadas não coincidem."',
         'Redigitar a senha nos dois campos'],
    ],
    larguras=[4.0, 5.8, 5.5],
)

# ─────────────────────────────────────────────────────────────────────────────
d.h3('Possíveis perguntas')

d.h5('Preciso preparar o arquivo antes de enviar?')
d.corpo(
    'Não. Cada ferramenta reconhece sozinha o formato que espera — colunas, codificação e '
    'separador. Basta selecionar o arquivo do jeito que ele foi exportado do sistema de '
    'origem.'
)

d.h5('O Hub altera meu arquivo original?')
d.corpo(
    'Não. O arquivo selecionado é copiado para a pasta da ferramenta e o resultado é '
    'sempre gravado em um arquivo novo. O original permanece intacto onde estava.'
)

d.h5('Posso rodar a mesma ferramenta várias vezes?')
d.corpo(
    'Pode. Cada execução processa o arquivo escolhido naquele momento e substitui o '
    'resultado anterior na pasta da ferramenta. Se quiser manter o histórico, exporte '
    'cada resultado com um nome diferente antes de rodar de novo.'
)

d.h5('Posso usar duas ferramentas ao mesmo tempo?')
d.corpo(
    'Não. Enquanto uma ferramenta estiver processando, o Hub avisa "Aguarde o '
    'processamento atual terminar." ao clicar em outra. A tela continua respondendo '
    'normalmente durante o processamento.'
)

d.h5('Preciso de internet?')
d.corpo(
    'Só as ferramentas 1 e 2, que consultam endereços no OpenStreetMap. Todas as outras '
    'funcionam sem conexão.'
)

d.h5('Onde encontro um resultado que esqueci de exportar?')
d.corpo(
    'Clique no ícone de pasta ao lado do botão da ferramenta: o Explorer do Windows abre '
    'na pasta dela, e o arquivo está dentro da subpasta resultados — desde que a '
    'ferramenta não tenha sido executada de novo depois.'
)

d.h5('O que fazer quando aparece uma mensagem de erro em vermelho?')
d.corpo(
    'A mensagem indica o motivo logo depois de "Erro ao processar". Os casos mais comuns '
    'são planilha de saída aberta no Excel e arquivo de entrada em formato diferente do '
    'esperado. A tabela "Mensagens que podem aparecer" lista o que fazer em cada '
    'situação.'
)

d.salvar(SAIDA)
print(f'Documento gerado: {os.path.abspath(SAIDA)}')
