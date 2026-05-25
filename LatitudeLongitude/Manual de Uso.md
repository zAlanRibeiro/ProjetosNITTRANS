### **Manual de Uso — Sistema de Geolocalização de Planilhas**



##### **1. Instalação das dependências**



Para o sistema funcionar corretamente, é necessário instalar as bibliotecas utilizadas pelo projeto.

Abra o CMD dentro da pasta:



"LatitudeLongitude"



e execute o comando:



pip install -r requirements.txt





##### **2. Adicionar a planilha**



Coloque o arquivo que deseja processar dentro da pasta:



"entrada"



O sistema aceita arquivos:



.csv

.xlsx

.xls





##### **3. Executar o sistema**



Abra novamente o CMD dentro da pasta:



"LatitudeLongitude"



e execute:



python limpeza.py





##### **4. Processamento**



Durante a execução será exibida uma barra de progresso indicando o andamento da busca de endereços da planilha.



Velocidade média:



aproximadamente 40 a 80 coordenadas por minuto



O tempo pode variar dependendo:



da velocidade da internet

da quantidade de coordenadas

da resposta do servidor OpenStreetMap

da quantidade de coordenadas repetidas





##### **5. Resultado final**



Ao finalizar, o sistema irá:



informar que o processamento foi concluído

gerar automaticamente a planilha corrigida

mover o arquivo original para backup

gerar lista de coordenadas não encontradas

avisar coordenadas inválidas no terminal

manter todas as linhas originais da planilha



Os arquivos serão salvos na pasta:



"arquivo\_modificado"





##### **6. Arquivos gerados**



O sistema gera:



Arquivo                                 Descrição

\*\_corrigido.xlsx / .csv                Planilha com endereços preenchidos automaticamente

coordenadas\_nao\_encontradas.txt        Lista de coordenadas não localizadas

cache\_enderecos.json                   Cache local das consultas realizadas





##### **7. Recursos do sistema**



O sistema realiza automaticamente:



leitura automática de encoding

correção de encoding (UTF-8 / CP1252 / Latin-1)

compatibilidade com CSV e Excel

identificação automática de latitude e longitude

verificação de coordenadas inválidas

consulta de endereços via internet

preenchimento automático de rua, bairro, cidade e CEP

cache inteligente de consultas

tolerância a timeout da internet

tentativa automática de reconexão

geração de backup automático

geração de TXT com coordenadas não encontradas

manutenção de todas as linhas originais

repetição automática de endereços em coordenadas duplicadas





##### **8. Observações importantes**



Mesmo que algumas coordenadas não sejam encontradas, normalmente a maior parte da planilha será preenchida corretamente.

Em alguns casos, o OpenStreetMap pode não possuir número do imóvel cadastrado.

Coordenadas inválidas não são removidas da planilha. O sistema apenas informa no terminal.

Os arquivos originais nunca são alterados diretamente. Uma cópia de segurança é criada automaticamente.

O sistema utiliza cache local para acelerar futuras execuções.

Coordenadas duplicadas permanecem no arquivo final normalmente.





By: Alan Doyle Costa Ribeiro

