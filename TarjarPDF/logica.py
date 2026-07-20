# -*- coding: utf-8 -*-
import fitz  # PyMuPDF
import re
import os
import sys

def _configurar_tesseract_local():
    """
    Aponta o PyMuPDF para a pasta 'tesseract' embutida dentro do projeto,
    em vez de depender de uma instalação do Tesseract no sistema.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Executando como .exe (PyInstaller)
        # O hub.spec empacotou o tesseract dentro da subpasta TarjarPDF
        pasta_tesseract = os.path.join(sys._MEIPASS, "TarjarPDF", "tesseract")
    else:
        # Executando como script Python normal (modo de desenvolvimento)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        pasta_tesseract = os.path.join(base_dir, "tesseract")

    pasta_tessdata = os.path.join(pasta_tesseract, "tessdata")

    if os.path.isdir(pasta_tessdata):
        # tessdata: onde ficam os arquivos .traineddata (por.traineddata, eng.traineddata)
        os.environ["TESSDATA_PREFIX"] = pasta_tessdata
        # PATH: para o Windows encontrar as DLLs do Tesseract (libtesseract, leptonica etc.)
        os.environ["PATH"] = pasta_tesseract + os.pathsep + os.environ.get("PATH", "")
    else:
        print(
            f"Aviso: pasta 'tesseract/tessdata' não encontrada em {pasta_tesseract}. "
            "O OCR em PDFs escaneados não vai funcionar. "
            "Copie a pasta do Tesseract-OCR para dentro do projeto (veja instruções)."
        )

_configurar_tesseract_local()

def processar_pdf_lgpd(caminho_entrada, tarjar_cpf=True, tarjar_email=True, tarjar_rg=True, lista_textos_manuais=None, tarjar_cnpj=False):
    if not caminho_entrada or not os.path.exists(caminho_entrada):
        return False, "Selecione um arquivo válido."

    diretorio, nome_arquivo = os.path.split(caminho_entrada)
    nome_sem_ext, ext = os.path.splitext(nome_arquivo)
    caminho_saida = os.path.join(diretorio, f"{nome_sem_ext}_higienizado{ext}")

    padroes_ativos = {}
    
    # ── REGEX COM LIMITADORES EXATOS ──────────────────────────────────────────
    if tarjar_cpf: 
        padroes_ativos["CPF"] = r"(?<!\d)(?:\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})(?!\d)"
        
    if tarjar_email: 
        padroes_ativos["E-mail"] = r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
        
    if tarjar_rg: 
        # Primeiro grupo aceita 1 a 3 dígitos (cobre "22.116.876-8" e também o formato do
        # DETRAN-RJ com 3 dígitos no primeiro grupo, ex: "010.932.234-7", que antes não batia)
        padroes_ativos["RG"] = r"(?<!\d)(?:\d{1,3}\.\d{3}\.\d{3}-[0-9Xx]|\d{4}\.\d{3}-[0-9Xx]|\d{7,9}-[0-9Xx]|\d{8,9})(?!\d)"

    if tarjar_cnpj:
        padroes_ativos["CNPJ"] = r"(?<!\d)(?:\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14})(?!\d)"

    if lista_textos_manuais is None: 
        lista_textos_manuais = []

    try:
        doc = fitz.open(caminho_entrada)
        total_tarjas = 0
        
        for pagina in doc:
            
            # ── ENCAPSULAMENTO DA LÓGICA DE BUSCA E TARJA ──
            # Agora aceita uma "textpage" opcional (usada para injetar o resultado do OCR).
            # Sem isso, get_text()/search_for() sempre leem a camada de texto nativa,
            # que é vazia em PDFs escaneados — por isso o OCR nunca era de fato usado.
            def buscar_e_tarjar(textpage=None):
                tarjas_encontradas = 0
                texto_pagina = pagina.get_text("text", textpage=textpage)
                palavras_da_pagina = pagina.get_text("words", textpage=textpage)
                
                # 1. Automático (Regex)
                for categoria, padrao in padroes_ativos.items():
                    ocorrencias = list(set(re.findall(padrao, texto_pagina)))
                    for oco in ocorrencias:
                        
                        # ── REGRA DE EXCEÇÃO INTELIGENTE PARA MATRÍCULAS NITTRANS ──────
                        if categoria == "RG" and re.fullmatch(r"1\.?\d{3}\.?\d{3}-\d", oco):
                            continue # Ignora se for a matrícula do servidor
                        # ───────────────────────────────────────────────────────────────

                        areas = pagina.search_for(oco, textpage=textpage)
                        for area in areas:
                            pagina.add_redact_annot(area, fill=(0, 0, 0))
                            tarjas_encontradas += 1
                
                # 2. Manual (Lista com Inteligência de Palavras Isoladas)
                for texto in lista_textos_manuais:
                    termo = texto.strip()
                    if not termo:
                        continue
                    
                    if " " not in termo:
                        for w in palavras_da_pagina:
                            palavra_limpa = re.sub(r"^[^\w]+|[^\w]+$", "", w[4])
                            if palavra_limpa.lower() == termo.lower():
                                area_palavra = fitz.Rect(w[:4])
                                pagina.add_redact_annot(area_palavra, fill=(0, 0, 0))
                                tarjas_encontradas += 1
                    else:
                        areas = pagina.search_for(termo, textpage=textpage)
                        for area in areas:
                            pagina.add_redact_annot(area, fill=(0, 0, 0))
                            tarjas_encontradas += 1
                            
                return tarjas_encontradas, texto_pagina

            # ── MÉTODO 1: TEXTO SELECIONADO NATIVO ──
            tarjas_na_pagina, texto_extraido = buscar_e_tarjar()
            
            # ── MÉTODO 2: FALLBACK PARA OCR (IMAGENS) ──
            # Aciona quando: (a) a página não tiver texto extraível legível (< 50 caracteres,
            # PDF 100% escaneado), OU (b) a página tiver alguma imagem embutida — mesmo que já
            # exista bastante texto digitado nela (ex: formulário com uma foto de CPF/RG colada
            # dentro). Sem o item (b), uma foto de documento dentro de uma página com texto
            # nunca era verificada pelo OCR.
            tem_imagem = len(pagina.get_images(full=True)) > 0
            precisa_ocr = len(texto_extraido.strip()) < 50 or tem_imagem

            if precisa_ocr:
                try:
                    # Roda o OCR na página e GUARDA o textpage retornado — este era o bug:
                    # antes o resultado do OCR era descartado e as buscas seguintes
                    # continuavam lendo a camada nativa (vazia).
                    # dpi mais alto = OCR mais preciso em digitalizações.
                    # full=True força o OCR na página inteira (não só em áreas sem texto).
                    textpage_ocr = pagina.get_textpage_ocr(
                        language="por",
                        dpi=300,
                        full=True,
                        tessdata=os.environ.get("TESSDATA_PREFIX"),
                    )

                    # Busca de novo, agora passando explicitamente o textpage com OCR.
                    tarjas_ocr, _ = buscar_e_tarjar(textpage=textpage_ocr)
                    tarjas_na_pagina += tarjas_ocr
                except Exception as e:
                    print(f"Aviso: Não foi possível realizar OCR na página {pagina.number}. Erro: {e}")

            # Se encontrou alguma coisa na página (seja no Método 1 ou Método 2), aplica as tarjas pretas
            if tarjas_na_pagina > 0:
                pagina.apply_redactions()
                total_tarjas += tarjas_na_pagina
        
        doc.save(caminho_saida)
        doc.close()
        
        return True, f"Sucesso! {total_tarjas} informações ocultadas."
    
    except Exception as e:
        return False, f"Erro: {str(e)}"