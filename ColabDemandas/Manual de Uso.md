# **Manual de Uso — Demandas Colab (CSV para Excel)**

##### **1. Para que serve**

O Colab exporta o relatório de demandas e atendimentos **picado em seis arquivos CSV**, cada um com um recorte diferente. Esta ferramenta junta os seis numa única planilha Excel, com **uma aba para cada recorte**, já tratados e traduzidos para português.

##### **2. Instalação das dependências**

Abra o CMD dentro da pasta do projeto e execute:

pip install -r requirements.txt

Conteúdo do requirements.txt:

pandas>=2.0.0

openpyxl>=3.1.0

##### **3. Adicionar os arquivos**

Pelo hub, o botão **10. Demandas Colab** abre uma janela que aceita **vários CSVs de uma vez** (segure Ctrl ou Shift, ou Ctrl+A para marcar todos).

Pelo CMD, coloque os arquivos .csv dentro da pasta "entrada".

Não precisa renomear nem ordenar nada: a ferramenta identifica cada arquivo pelo **número no nome** (`...data-0`, `...data-1`, e assim por diante), então os sufixos de download que o Colab acrescenta — `(1)`, `(2)` — não atrapalham.

##### **4. Executar**

Pelo hub: botão **10. Demandas Colab**.

Pelo CMD, dentro da pasta da ferramenta:

python colabDemandas.py

##### **5. As seis abas**

Arquivo | Aba | Conteúdo

data-0 | Demandas | Data, Hora e Plataforma — uma linha por demanda

data-1 | Status por Categoria | Categoria, Status, Total

data-2 | Tempo por Categoria | Categoria, Tempo de Atendimento, Total, Total da Categoria

data-3 | Bairros (Colab) | Bairro, Total, Resolvidas, Taxa de Resolução

data-4 | Bairros (cdo) | Bairro, Total, Resolvidas, Taxa de Resolução

data-5 | Status por Bairro | Bairro, Status, Total

A planilha tem **exatamente essas seis abas**, nada além disso. Toda aba já vem com filtro automático, cabeçalho congelado, datas como data de verdade, totais como número e a taxa de resolução em formato de porcentagem.

##### **6. Bairros (Colab) e Bairros (cdo): a diferença**

Os arquivos data-3 e data-4 têm exatamente as mesmas colunas, e o Colab não diz qual é qual. A diferença é a **plataforma de origem** da demanda: a soma de cada arquivo bate exatamente com a contagem por plataforma do data-0 — 5.809 para "Colab" e 2.566 para "cdo" na amostra analisada.

##### **7. A coluna Resolvidas**

Não é estimativa: no arquivo original, `total × rate` dá **número inteiro exato em todas as linhas**, e a soma das resolvidas das duas plataformas bate, bairro a bairro, com o total de "Resolvida" da aba Status por Bairro. Ou seja, a taxa é resolvidas ÷ total, e a coluna só recupera o número que estava implícito.

##### **8. Tratamento dos dados**

Tudo o que a ferramenta corrige aparece no terminal, no bloco **DADOS TRATADOS**. Nada é corrigido em silêncio.

**Espaços sobrando** — o Colab exporta categorias como `'Evento irregular '`, com espaço no fim. No Excel isso vira uma categoria diferente de `'Evento irregular'` e quebra qualquer tabela dinâmica. A ferramenta tira os espaços das pontas e junta espaços repetidos no meio.

**Números ilegíveis** — linha cujo total ou taxa não for um número válido (ou estiver fora da faixa: total negativo, taxa fora de 0 a 100%) é **descartada e reportada**, com o valor que causou o problema. Virar zero calado falsearia os somatórios.

**Datas ilegíveis** — mesma regra: a linha é descartada e reportada.

O terminal também informa quantas linhas cada aba perdeu, por exemplo: `-> aba "Status por Bairro": 104 linhas (2 descartada(s))`.

##### **9. Fuso horário**

O Colab grava os horários em **UTC**. A ferramenta converte para o horário de Niterói (America/Sao_Paulo) antes de separar Data e Hora — sem isso, uma demanda registrada às 21h cairia no dia seguinte na planilha.

##### **10. Se faltar algum arquivo**

A planilha sai assim mesmo, só que sem a aba correspondente, e o terminal lista o que faltou em **RECORTES QUE NÃO VIERAM**. Arquivo que não for um dos seis recortes é listado em **ARQUIVOS IGNORADOS** e não entra na planilha.

##### **11. Pastas do sistema**

Pasta | Descrição

entrada | Arquivos CSV a processar

resultados | Planilhas Excel geradas

backup | Backup automático dos CSVs já processados

##### **12. Arquivo gerado**

Colab\_Demandas\_Extraido.xlsx

**Nada é sobrescrito.** Rodando de novo, a planilha anterior é preservada e a nova sai como `Colab_Demandas_Extraido (2).xlsx`, `(3)`, e assim por diante.

##### **13. Uma observação sobre o arquivo data-2**

O total do data-2 (Tempo por Categoria) é bem menor que o dos demais: 1.782 demandas, contra 8.375 do total geral. Ele cobre 57 das 89 categorias, e em cada uma o número é menor ou igual ao do data-1. O critério que o Colab usa para esse recorte não dá para deduzir só pelos dados — vale conferir na plataforma antes de comparar esses números com os das outras abas.

By: Alan Doyle Costa Ribeiro
