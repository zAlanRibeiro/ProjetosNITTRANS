# Texto real do PDF da DIVARC de agosto/2026, salvo no layout de celular.
# Rodar: python test_layout_empilhado.py
from pathlib import Path

from estatisticasSEI import _ler_layout_empilhado, _linhas_do_ocr

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
print("ok")
