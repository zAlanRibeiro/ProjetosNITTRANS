# **Manual de Uso — Conversor de Processos PDF para Excel**



##### **1. Instalação das dependências**



Para o sistema funcionar corretamente, é necessário instalar as bibliotecas utilizadas pelo projeto.



Abra o CMD dentro da pasta do projeto e execute o comando:



pip install -r requirements.txt



##### **2. Conteúdo do arquivo requirements.txt**



O arquivo requirements.txt deve conter:



pdfplumber>=0.10.0

pandas>=2.0.0

openpyxl>=3.1.0

tqdm>=4.66.0



##### **3. Adicionar os arquivos PDF**



Coloque os arquivos .pdf que deseja converter dentro da pasta:



"entrada\_pdfs"



O sistema processa automaticamente todos os arquivos .pdf encontrados na pasta.



##### **4. Executar o sistema**



Abra novamente o CMD dentro da pasta do projeto e execute:



python extrator\_pdf.py



##### **5. Processamento**



Durante a execução será exibida uma indicação no CMD informando:



processamento dos arquivos (qual arquivo está sendo lido)

andamento da conversão

relatório de campos ausentes (N/A) e suas respectivas páginas para correção



O sistema realiza automaticamente:



leitura contínua das páginas do PDF (ignorando quebras de página)

reconstrução de CNPJs e CPFs divididos em múltiplas linhas

associação de dados ausentes com base em proprietários recorrentes (herança)

agrupamento de descrições de infrações longas

filtro de ruídos (cabeçalhos, rodapés, links e numerações de página)

tratamento de nomes isolados e anomalias de formatação



##### **6. Conversão dos dados**



O sistema converte automaticamente os registros dos relatórios em PDF para planilhas Excel (.xlsx).



Os seguintes dados são organizados automaticamente:



Arquivo

Página

CPF/CNPJ

Proprietário

Placa

Processo

Data de Abertura

Data Resultado

Resultado

Relator



##### **7. Resultado final**



Ao finalizar o processamento, o sistema irá:



informar que a automação foi concluída

exibir um relatório visual no CMD indicando exatamente onde estão os campos vazios (N/A)

gerar automaticamente os arquivos Excel



##### **8. Pastas do sistema**



Pasta | Descrição



dados\_entrada | Arquivos PDF originais

resultados | Arquivos Excel convertidos

backup\_pdfs | Backup automático dos arquivos PDF



##### **9. Arquivos gerados**



O sistema gera:



Arquivo | Descrição



relatorio\_processos\_\*.xlsx | Planilha Excel convertida e organizada com data e hora da extração



##### **10. Backup automático**



Após a conversão:



os arquivos PDF originais são movidos automaticamente para a pasta:



"backup\_pdfs"



Isso evita:



processamento duplicado

perda de arquivos originais

sobrescrita acidental



##### **11. Observações importantes**



O sistema foi desenvolvido especificamente para os relatórios de infração em PDF do Detran.

Cada bloco iniciado por uma placa de veículo representa um registro completo.



Caso algum arquivo possua estrutura diferente do padrão esperado, o sistema preencherá o campo com N/A e avisará no terminal para facilitar a auditoria manual.



Os arquivos originais nunca são alterados diretamente.



By: Alan Doyle Costa Ribeiro

