# **Manual de Uso — Autos Pagos Renainf (PDF para Excel)**

##### **1. Para que serve**

Converte os relatórios de **AUTOS PAGOS** do SMIT (Gerencial), emitidos em PDF, em uma planilha Excel com uma linha por auto pago.

O SMIT emite **três relatórios diferentes** com nomes parecidos, e as colunas mudam entre eles:

Relatório | Colunas próprias

AUTOS PAGOS RENAINF - <UF> | UF de pagamento, matrícula do agente e FUNSET

AUTOS PAGOS RENAINF | vai só até a UF de pagamento (sem matrícula e sem FUNSET); a UF varia de linha para linha

AUTOS PAGOS | valor acumulado, matrícula do agente e FUNSET (não tem UF)

A ferramenta **identifica sozinha** qual é o relatório, pelo título impresso em cada página. Por isso dá para jogar os três tipos, e vários meses, na mesma execução.

Cada PDF gera a **sua própria planilha**, com o nome do arquivo de origem mais um sufixo que identifica o relatório. Nada é misturado entre arquivos.

##### **2. Instalação das dependências**

Abra o CMD dentro da pasta do projeto e execute:

pip install -r requirements.txt

Conteúdo do requirements.txt:

pdfplumber>=0.10.0

pandas>=2.0.0

openpyxl>=3.1.0

##### **3. Adicionar os arquivos PDF**

Pelo hub, o botão **9. Autos Pagos Renainf** abre uma janela que aceita **vários PDFs de uma vez** (segure Ctrl ou Shift para selecionar mais de um).

Pelo CMD, coloque os arquivos .pdf dentro da pasta "entrada". Todos os .pdf encontrados são processados na mesma execução.

##### **4. Executar**

Pelo hub: botão **9. Autos Pagos Renainf**.

Pelo CMD, dentro da pasta da ferramenta:

python autosPagos.py

##### **5. Nomes das planilhas geradas**

Uma planilha por PDF, sempre com o nome do arquivo de origem mais o sufixo **\_Extraido**:

PDF de origem | Planilha gerada

Abril Autos Pagos Renainf RJ.pdf | Abril Autos Pagos Renainf RJ**\_Extraido**.xlsx

Abril Autos Pagos Renainf.pdf | Abril Autos Pagos Renainf**\_Extraido**.xlsx

Abril Autos Pagos.pdf | Abril Autos Pagos**\_Extraido**.xlsx

**Nada é sobrescrito.** Se você processar o mesmo PDF de novo, a planilha anterior é preservada e a nova sai com um número no fim, como o Windows faz:

Abril Autos Pagos\_Extraido.xlsx | 1ª execução

Abril Autos Pagos\_Extraido (2).xlsx | 2ª execução

Abril Autos Pagos\_Extraido (3).xlsx | 3ª execução

Isso permite comparar o resultado novo com o anterior. Em compensação, a pasta "resultados" vai acumulando arquivos — apague os que não precisar mais.

Como o sufixo é o mesmo para os três relatórios, quem identifica o tipo é o **nome da aba de dados** dentro da planilha (ver item 6).

##### **6. Abas de cada planilha**

**Aba de dados** (o nome varia com o relatório) — Arquivo, Página, Competência, Órgão, Cód. Agente, SEQ, Nº Auto, Data Infração, Data Vencimento, Data Pagamento, Valor Pago (R$) e, conforme o relatório:

Autos Pagos Renainf <UF> | + UF de Pgto., Matrícula Agente, FUNSET (R$)

Autos Pagos Renainf | + UF de Pgto.

Autos Pagos | + Valor Acumulado (R$), Matrícula Agente, FUNSET (R$)

**Aba Resumo** — quantidade de autos, valor pago e FUNSET totalizados por competência e código de agente, mais uma linha de TOTAL GERAL.

As datas saem como data de verdade e os valores como número, prontos para soma, filtro e tabela dinâmica no Excel. Toda aba já vem com filtro automático e cabeçalho congelado.

##### **7. Cuidado: Valor Acumulado não deve ser somado**

Na aba **Autos Pagos**, a coluna **Valor Acumulado (R$)** é um saldo corrente do próprio relatório, não uma parcela de cada auto. Somar essa coluna não significa nada. Por isso ela entra na planilha como número, para conferência, mas **fica de fora dos totais do Resumo**.

##### **8. Importante: a SEQ reinicia a cada agente**

Os relatórios são divididos por **COD. AGENTE**, e a numeração SEQ começa do 1 em cada bloco. Portanto a SEQ sozinha **não** identifica um auto — use a combinação **Cód. Agente + SEQ**, ou o **Nº Auto**, que é único.

##### **9. Conferência no terminal**

Conforme cada PDF é lido, o sistema exibe abaixo dele os avisos daquele arquivo:

**Campos em branco no PDF de origem** — autos em que o próprio PDF não trouxe a data de vencimento ou a matrícula do agente, com a página e o nº do auto para conferência manual.

**Matrículas fora do padrão** — matrículas que não são só dígitos nem dígitos com verificador (ex.: "3,09" onde as vizinhas são "309"). O auto é mantido com o valor original do PDF, sem correção automática, e apenas sinalizado.

**Linhas descartadas** — linhas cujo conteúdo não bateu com o formato esperado das colunas. Em PDFs no padrão normal esta lista vem vazia; se aparecer algo, é sinal de que o layout do relatório mudou.

No fim, um quadro lista todas as planilhas geradas com a quantidade de autos e o valor pago de cada uma, que servem para bater com os PDFs originais.

##### **10. Pastas do sistema**

Pasta | Descrição

entrada | Arquivos PDF a processar

resultados | Planilhas Excel geradas

backup | Backup automático dos PDFs já processados

##### **11. Arquivos gerados**

"nome do PDF"\_Extraido.xlsx | Uma planilha por PDF processado (ver item 5)

##### **12. Backup automático**

Após a leitura, os PDFs originais são movidos de "entrada" para "backup". Isso evita processamento duplicado e preserva o arquivo original, que nunca é alterado.

##### **13. Como a leitura funciona (e por que ela é confiável)**

Estes relatórios são tabelas regulares: cada linha do PDF já é um registro completo. A dificuldade é que o SMIT às vezes imprime a **data de vencimento** ou a **matrícula do agente** em branco. Quando isso acontece a linha "encolhe", e uma leitura pela ordem das palavras encaixaria a data de pagamento na coluna de vencimento, sem dar erro nenhum.

Por isso a extração usa a **coordenada horizontal de cada valor na página**, e não a ordem em que aparecem. Além disso, cada campo passa por uma validação de formato: se o layout mudar, a linha vai para a lista de **linhas descartadas** em vez de virar dado trocado de coluna na planilha.

By: Alan Doyle Costa Ribeiro
