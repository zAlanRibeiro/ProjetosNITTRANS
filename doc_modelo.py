# -*- coding: utf-8 -*-
"""Blocos de montagem dos documentos no padrão visual da NITTRANS.

O padrão é o do arquivo "FERRAMENTA ESTATÍSTICAS SEI.docx", usado aqui como
template: o conteúdo dele é descartado e só os estilos, as margens, o cabeçalho
com as logos, o rodapé e as definições de lista são reaproveitados.

Usado por gerar_doc_hub.py (manual de uso) e gerar_doc_tecnico.py
(documentação técnica).
"""
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

MODELO = 'FERRAMENTA ESTATÍSTICAS SEI.docx'

LARANJA = RGBColor(0xFF, 0x8B, 0x00)
AZUL = RGBColor(0x1F, 0x35, 0x63)
CINZA = RGBColor(0x40, 0x40, 0x40)
CODIGO = RGBColor(0x1F, 0x1F, 0x1F)
BRANCO = RGBColor(0xFF, 0xFF, 0xFF)

# abstractNumId reaproveitados do modelo: 0 = marcador, 22 = numeração decimal
ABS_MARCADOR = '0'
ABS_NUMERO = '22'


class DocumentoModelo:
    """Documento novo, em branco, com o visual do modelo."""

    def __init__(self, modelo=MODELO):
        self.doc = Document(modelo)

        corpo = self.doc.element.body
        for filho in list(corpo):
            if not filho.tag.endswith('}sectPr'):
                corpo.remove(filho)

        self._numbering = self.doc.part.numbering_part.element
        self._proximo_num_id = max(
            int(n) for n in re.findall(r'<w:num w:numId="(\d+)"', self._numbering.xml)
        ) + 1
        self._num_marcador = self.nova_lista(ABS_MARCADOR)

    # ── listas ───────────────────────────────────────────────────────────────
    def nova_lista(self, abstract_id):
        """Cria uma lista nova apontando para um formato já existente no modelo.

        Necessário para que cada sequência numerada recomece do 1 em vez de
        continuar a contagem da lista anterior.
        """
        num = OxmlElement('w:num')
        num.set(qn('w:numId'), str(self._proximo_num_id))
        abstract = OxmlElement('w:abstractNumId')
        abstract.set(qn('w:val'), abstract_id)
        num.append(abstract)
        self._numbering.append(num)
        self._proximo_num_id += 1
        return self._proximo_num_id - 1

    def _item(self, texto, num_id, nivel=0):
        p = self.doc.add_paragraph(style='List Paragraph')
        pPr = p._p.get_or_add_pPr()
        numPr = OxmlElement('w:numPr')
        ilvl = OxmlElement('w:ilvl')
        ilvl.set(qn('w:val'), str(nivel))
        numId = OxmlElement('w:numId')
        numId.set(qn('w:val'), str(num_id))
        numPr.append(ilvl)
        numPr.append(numId)
        pPr.append(numPr)
        p.add_run(texto)
        return p

    def marcador(self, texto):
        return self._item(texto, self._num_marcador)

    def marcadores(self, itens):
        for item in itens:
            self.marcador(item)

    def passos(self, itens):
        """Lista numerada que recomeça do 1 a cada chamada."""
        num_id = self.nova_lista(ABS_NUMERO)
        for item in itens:
            self._item(item, num_id)

    # ── texto ────────────────────────────────────────────────────────────────
    def titulo(self, texto):
        p = self.doc.add_paragraph(style='Title')
        r = p.add_run(texto)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(14)
        return p

    def data(self, texto):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.add_run(texto)
        return p

    def ficha(self, pares):
        """Linhas "Rótulo: valor" da abertura, com o rótulo em negrito."""
        for rotulo, valor in pares:
            p = self.doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(f'{rotulo}: ')
            r.bold = True
            p.add_run(valor)
        self.doc.add_paragraph()

    def h3(self, texto):
        return self.doc.add_paragraph(texto, style='Heading 3')

    def h4(self, texto):
        p = self.doc.add_paragraph(style='Heading 4')
        r = p.add_run(texto)
        r.font.color.rgb = LARANJA
        return p

    def h5(self, texto):
        return self.doc.add_paragraph(texto, style='Heading 5')

    def corpo(self, texto):
        return self.doc.add_paragraph(texto, style='Body Text')

    def rotulo(self, rotulo, valor):
        """Parágrafo curto do tipo "Arquivo: caminho/do/modulo.py"."""
        p = self.doc.add_paragraph(style='Body Text')
        r = p.add_run(f'{rotulo}: ')
        r.bold = True
        p.add_run(valor)
        return p

    def observacao(self, texto, prefixo='Observação: '):
        p = self.doc.add_paragraph()
        r = p.add_run(prefixo)
        r.bold = True
        r.font.size = Pt(10.5)
        r.font.color.rgb = LARANJA
        r2 = p.add_run(texto)
        r2.font.size = Pt(10.5)
        r2.font.color.rgb = CINZA
        return p

    def subtitulo(self, texto):
        p = self.doc.add_paragraph()
        r = p.add_run(texto)
        r.bold = True
        r.font.size = Pt(13)
        r.font.color.rgb = AZUL
        return p

    def codigo(self, linhas):
        for linha in linhas:
            p = self.doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(0)
            r = p.add_run(linha)
            r.font.name = 'Courier New'
            r.font.size = Pt(9)
            r.font.color.rgb = CODIGO
        self.doc.add_paragraph()

    def espaco(self):
        return self.doc.add_paragraph()

    # ── tabelas ──────────────────────────────────────────────────────────────
    @staticmethod
    def _pintar(celula, cor_hex):
        tcPr = celula._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), cor_hex)
        tcPr.append(shd)

    @staticmethod
    def _escrever(celula, texto, negrito=False, cor=None):
        r = celula.paragraphs[0].add_run(texto)
        r.bold = negrito
        r.font.size = Pt(10)
        if cor is not None:
            r.font.color.rgb = cor

    def tabela(self, cabecalhos, linhas, larguras=None):
        t = self.doc.add_table(rows=1 + len(linhas), cols=len(cabecalhos))
        t.style = 'Table Grid'

        for i, texto in enumerate(cabecalhos):
            celula = t.rows[0].cells[i]
            self._escrever(celula, texto, negrito=True, cor=BRANCO)
            self._pintar(celula, 'FF8B00')

        for li, linha in enumerate(linhas):
            for ci, valor in enumerate(linha):
                celula = t.rows[li + 1].cells[ci]
                self._escrever(celula, valor)
                self._pintar(celula, 'F5F5F5' if li % 2 == 0 else 'FFFFFF')

        if larguras:
            t.autofit = False
            for linha in t.rows:
                for i, largura in enumerate(larguras):
                    linha.cells[i].width = Cm(largura)

        self.doc.add_paragraph()
        return t

    # ── saída ────────────────────────────────────────────────────────────────
    def salvar(self, caminho):
        self.doc.save(caminho)
        return caminho
