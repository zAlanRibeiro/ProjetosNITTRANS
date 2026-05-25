# **Manual de Uso — Limpeza de Planilhas**



##### 1\. Instalação das dependências



Para o sistema funcionar corretamente, é necessário instalar as bibliotecas utilizadas pelo projeto.

Abra o CMD dentro da pasta:



"LimpezaArquivo"



e execute o comando:



pip install -r requirements.txt



##### 2\. Adicionar a planilha



Coloque o arquivo que deseja limpar dentro da pasta:



"planilhas\_para\_limpar"



O sistema aceita arquivos:



.csv

.xlsx

.xls



##### 3\. Executar o sistema



Abra novamente o CMD dentro da pasta:



"LimpezaArquivo"



e execute:



python limpeza.py



##### 4\. Processamento



Durante a execução será exibida uma barra de progresso indicando o andamento da limpeza da planilha.



Velocidade média:



aproximadamente 100 linhas por minuto



O tempo pode variar dependendo:



do tamanho do arquivo

da quantidade de correções

da validação de endereços via internet



##### 5\. Resultado final



Ao finalizar, o sistema irá:



informar que o processamento foi concluído

indicar possíveis resíduos para verificação manual

gerar o arquivo limpo automaticamente



Os arquivos serão salvos na pasta:



"planilhas limpas"



##### 6\. Arquivos gerados



O sistema gera:



Arquivo	Descrição

\*\_LIMPO.xlsx	Planilha limpa e corrigida

\*\_RELATORIO.xlsx	Relatório contendo todas as alterações realizadas



##### 7\. Recursos do sistema



O sistema realiza automaticamente:



correção de acentuação corrompida

correção de encoding (UTF-8 / CP1252 / Latin-1)

remoção de caracteres inválidos

remoção de espaços e quebras de linha

padronização textual

correção de grafia de endereços

validação de endereços via internet

geração de backup automático

geração de relatório de auditoria



##### 8\. Observações importantes



Mesmo que o sistema indique “possíveis resíduos”, normalmente o arquivo já estará correto.

Em casos raros, arquivos extremamente corrompidos podem exigir validação manual.

Os arquivos originais nunca são alterados diretamente. Uma cópia de segurança é criada automaticamente.



By: Alan Doyle Costa Ribeiro

