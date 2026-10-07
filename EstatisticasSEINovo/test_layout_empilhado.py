# Texto real do PDF da DIVARC de agosto/2026, salvo no layout de celular.
# Rodar: python test_layout_empilhado.py
from pathlib import Path

from estatisticasSEI import (_desembrulhar_continuacao, _inicio_dos_dados,
                             _ler_layout_empilhado, _limpar, _linhas_do_ocr,
                             _pedacos)

TEXTO = """16/09/2026, 10:47 SEI - Estatísticas da Unidade
Processos com andamento fechado na unidade ao final do período:
TIPO Administrativo: Comunicado
QUANTIDADE 1
TIPO TOTAL:
QUANTIDADE 1
Processos com andamento fechado na unidade ao final do período (NIT/NITTRANS/DIVARC / NITEROI)
Tempos médios de tramitação no período:
TIPO Administrativo: Comunicado
TEMPO MÉDIO 4h 48m 16s
Documentos gerados no período:
Ago
TIPO Despacho de Encaminhamento de Documento
2026 25
25
AGO Despacho de Encaminhamento de Processo
TIPO 20
2026 20
TOTAL:
AGO 45
TIPO 45
Documentos gerados no período (NIT/NITTRANS/DIVARC / NITEROI)
Documentos externos no período:
Ago
https://leste.sei.rj.gov.br/sei/controlador.php?acao=gerar 4/6
16/09/2026, 10:47 SEI - Estatísticas da Unidade
TIPO Autorização
2026 3
3
AGO Comprovante
TIPO 4
2026 4
Documento
AGO 1
TIPO 1
2026 Guia
2
AGO TOTAL:
Documentos externos no período (NIT/NITTRANS/DIVARC / NITEROI)
"""

avisos = []
secoes, competencias = _ler_layout_empilhado(TEXTO, Path("x.pdf"), avisos)
assert competencias == ["2026-08"], competencias
assert secoes["processos_fechados"] == ({"Administrativo: Comunicado": 1}, 1)
assert secoes["documentos_gerados"] == ({
    "Despacho de Encaminhamento de Documento": 25,
    "Despacho de Encaminhamento de Processo": 20}, 45)
assert secoes["documentos_externos"] == ({
    "Autorização": 3, "Comprovante": 4, "Documento": 1, "Guia": 2}, None)
assert set(secoes) == {"processos_fechados", "documentos_gerados",
                       "documentos_externos"}
assert avisos == [], avisos

# Palavras do OCR do PDF da DEPTI (x0, y0, x1, y1, texto, bloco, linha):
# nome quebrado em três linhas, TOTAL lido errado ('TATA!'), quantidade
# lida como lixo ('Fe)') e seta de navegação na beirada ('>»').
PALAVRAS = [
    (488, 24, 572, 30, "Processos gerados no período:", 0, 0),
    (228, 39, 241, 43, "2026", 1, 0),
    (56, 47, 67, 52, "Tipo", 2, 0),
    (229, 55, 240, 61, "Ago", 3, 0),
    (3, 70, 118, 76, "Administrativo: Elaboração de Memorando", 4, 0),
    (234, 70, 235, 76, "1", 5, 0),
    (459, 70, 460, 76, "Fe)", 6, 0),
    (4, 85, 92, 90, "Contratação: Realizar Gestão de", 7, 0),
    (4, 93, 116, 99, "Contratos: Aditivo", 7, 1),
    (234, 93, 235, 99, "1", 8, 0),
    (459, 93, 460, 99, "1", 9, 0),
    (3, 102, 76, 108, "e/ou Prorrogação", 7, 2),
    (98, 138, 119, 146, "TATA!", 10, 0),
    (233, 138, 236, 146, "2", 11, 0),
    (458, 138, 461, 146, "2", 12, 0),
    (591, 151, 594, 155, ">»", 13, 0),
    (84, 160, 242, 165, "Processos gerados no período (NIT/NITTRANS/DEPTI)", 14, 0),
]
PALAVRAS = [p + (0,) for p in PALAVRAS]
texto = "\n".join(_linhas_do_ocr(PALAVRAS, 595))
secoes, competencias = _ler_layout_empilhado(texto, Path("x.pdf"), avisos)
assert competencias == ["2026-08"], competencias
assert secoes == {"processos": ({
    "Administrativo: Elaboração de Memorando": 1,
    "Contratação: Realizar Gestão de Contratos: Aditivo e/ou Prorrogação": 1},
    2)}, secoes
assert avisos == [], avisos

# Continuação da tabela embrulhada na tabela da página (DEPDOIV, set/2026):
# a primeira coluna é o texto da página inteira.
EMBRULHADA = [
    ["Ouvidoria: Manifestação - Reclamação, Sugestão,\n1\nSolicitação e Elogio"
     "\nTOTAL: 31\nProcessos com andamento fechado na unidade ao final do"
     " período (NIT/NITTRAN",
     "Ouvidoria: Manifestação - Reclamação, Sugestão,\nSolicitação e Elogio",
     "1", ""],
    [None, "TOTAL:", "31", None],
    [None, None, "", None],
]
assert _desembrulhar_continuacao(EMBRULHADA) == [
    ["Ouvidoria: Manifestação - Reclamação, Sugestão,\nSolicitação e Elogio",
     "1", ""],
    ["TOTAL:", "31", None],
    [None, "", None],
]
COMUM = [["Administrativo: Obras", "2026", "1"], ["TOTAL:", "1", "1"]]
assert _desembrulhar_continuacao(COMUM) == COMUM

# Cabeçalho desmontado pelo pdfplumber: seta de rolagem grudada no 'Tipo'
# (PROTOCOLO, set/2026), 'Quantidade' numa linha e 'Tipo' na de baixo
# (DIVAPRO, set/2026) e palavra partida em colunas (DIVC, jul/2026).
assert _limpar([["Ti", "po", "2026", ""],
                ["Anexo", None, "24", "24"]]) == [
    ["Tipo", None, "2026", None], ["Anexo", None, "24", "24"]]
assert _limpar([["", "", "", "Quantidade"], [None, "Tipo", "", None],
                ["Administrativo: Obras", "", "", "1"]]) == [
    ["Tipo", "Quantidade", None, None], [None, None, None, None],
    ["Administrativo: Obras", "", "", "1"]]
assert _limpar([["Tipo", "", "Q", "uantidade"]])[0][:2] == ["Tipo", "Quantidade"]

# Cabeçalho repetido no topo da página, sem a linha do mês, e o mês
# depois de uma linha vazia: os dados começam logo depois dos dois.
assert _inicio_dos_dados([["Tipo", "2026", ""], ["Decreto", "6", "6"]]) == 1
assert _inicio_dos_dados([["Tipo", None, "2026"], ["", None, ""],
                          ["Set", None, "24 24\n1 1"],
                          ["Anexo", None, "24"]]) == 3

# Duas tabelas do relatório empilhadas numa só do pdfplumber (AGNTMT,
# ago/2026), com a página inteira numa célula no começo (DEPCLC, set/2026):
# a legenda no meio da célula grande não fecha nada, a do começo fecha.
EMPILHADA = [
    ["07/10/2026, 11:36 SEI - Estatísticas da Unidade\nDocumentos gerados no"
     " período:\n...\nDocumentos gerados no período (NIT/NITTRANS/X)", None],
    ["Tipo", "2026"], ["Ago", None], ["Despacho", "4"], ["TOTAL:", "4"],
    ["", ""], ["Documentos gerados no período (NIT/NITTRANS/X", None],
    ["Tipo", "2026"], ["Ago", None], ["Registro", "1"], ["TOTAL:", "1"],
]
assert [(c, len(ls), f) for c, ls, f in _pedacos(EMPILHADA)] == [
    (None, 1, False), (1, 4, True), (7, 4, True)]

# OCR do PDF impresso com margem (DIVC, set/2026): nomes em x=32, TOTAL
# bem à direita, e a seta de rolagem '«' lida como '4' na coluna dos nomes.
PALAVRAS = [
    (476, 49, 546, 53, "Processos gerados no período:", 0, 0),
    (32, 87, 84, 92, "Financeiro: Pagamento", 4, 0),
    (240, 87, 242, 92, "4", 4, 1), (443, 87, 446, 92, "4", 4, 2),
    (32, 99, 104, 103, "Material: Controlar Bens Móveis", 5, 0),
    (240, 99, 242, 103, "8", 5, 1), (443, 99, 446, 103, "8", 5, 2),
    (118, 111, 136, 117, "TOTAL:", 6, 0),
    (239, 111, 243, 117, "12", 6, 1), (442, 111, 447, 117, "12", 6, 2),
    (31, 121, 33, 125, "4", 7, 0),
]
PALAVRAS = [p + (0,) for p in PALAVRAS]
texto = "\n".join(_linhas_do_ocr(PALAVRAS, 595))
secoes, _ = _ler_layout_empilhado(texto, Path("x.pdf"), avisos)
assert secoes == {"processos": ({"Financeiro: Pagamento": 4,
                                 "Material: Controlar Bens Móveis": 8}, 12)}
print("ok")
