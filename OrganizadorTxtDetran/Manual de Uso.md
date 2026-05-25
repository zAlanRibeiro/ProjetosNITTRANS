# **Manual de Uso — Conversor de Infrações TXT para Excel**



##### **1. Instalação das dependências**



Para o sistema funcionar corretamente, é necessário instalar as bibliotecas utilizadas pelo projeto.



Abra o CMD dentro da pasta do projeto e execute o comando:



pip install -r requirements.txt



##### **2. Conteúdo do arquivo requirements.txt**



O arquivo requirements.txt deve conter:



pandas>=2.0.0

openpyxl>=3.1.0

tqdm>=4.66.0



##### **3. Adicionar os arquivos TXT**



Coloque os arquivos .txt que deseja converter dentro da pasta:



"dados\_entrada"



O sistema processa automaticamente todos os arquivos .txt encontrados na pasta.



##### **4. Executar o sistema**



Abra novamente o CMD dentro da pasta do projeto e execute:



python decifradorTxt.py



##### **5. Processamento**



Durante a execução será exibida uma barra de progresso indicando:



processamento dos arquivos

leitura dos registros

andamento da conversão



O sistema realiza automaticamente:



leitura de arquivos com encoding UTF-8

leitura de arquivos CP1252

leitura de arquivos Latin-1

tratamento de dados corrompidos

padronização de datas

padronização de horários

padronização de valores monetários



##### **6. Conversão dos dados**



O sistema converte automaticamente os registros do arquivo TXT para planilhas Excel (.xlsx).



Os seguintes dados são organizados automaticamente:



Cód do Orgão Atuador

Código da Infração

DV Infração

Desdobramento Infração

Descrição da Infração

Tipo de enquadramento

Auto

Data

Hora

Cód Classe do Agente

Data do Status

Cód. do Status

Valor da Infração

Data do Vencimento da Infração

Data do Pagamento da Infração

Situação

Marca/Modelo do veículo

Renavam do Veículo

Placa do Veículo Infrator

tipo de pessoa

identidade

nome

nome do logradouro do infrator

CEP

Cód. do Município

Município

Descrição do Município do Endereço



##### **7. Resultado final**



Ao finalizar o processamento, o sistema irá:



informar que a conversão foi concluída

mostrar a quantidade de registros processados

gerar automaticamente os arquivos Excel



##### **8. Pastas do sistema**



Pasta	Descrição



dados\_entrada	Arquivos TXT originais

arquivo\_organizado	Arquivos Excel convertidos

backup	Backup automático dos arquivos TXT



##### **9. Arquivos gerados**



O sistema gera:



Arquivo	Descrição



\*\_normalizado.xlsx	Planilha Excel convertida e organizada



##### **10. Backup automático**



Após a conversão:



os arquivos TXT originais são movidos automaticamente para a pasta:



"backup"



Isso evita:



processamento duplicado

perda de arquivos originais

sobrescrita acidental



##### **11. Observações importantes**



O sistema foi desenvolvido para arquivos TXT de largura fixa.

Cada linha do arquivo representa um registro completo de infração.



Caso algum arquivo possua estrutura diferente do padrão esperado, poderá ocorrer desalinhamento de colunas.



Os arquivos originais nunca são alterados diretamente.



By: Alan Doyle Costa Ribeiro

