# -*- coding: utf-8 -*-
import fitz  # PyMuPDF
import re
import os

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
        padroes_ativos["RG"] = r"(?<!\d)(?:\d{1,2}\.\d{3}\.\d{3}-[0-9Xx]|\d{4}\.\d{3}-[0-9Xx]|\d{7,9}-[0-9Xx]|\d{8,9})(?!\d)"

    if tarjar_cnpj:
        padroes_ativos["CNPJ"] = r"(?<!\d)(?:\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14})(?!\d)"

    if lista_textos_manuais is None: 
        lista_textos_manuais = []

    try:
        doc = fitz.open(caminho_entrada)
        total_tarjas = 0
        
        for pagina in doc:
            
            # ── ENCAPSULAMENTO DA LÓGICA DE BUSCA E TARJA ──
            def buscar_e_tarjar():
                tarjas_encontradas = 0
                texto_pagina = pagina.get_text("text")
                palavras_da_pagina = pagina.get_text("words")
                
                # 1. Automático (Regex)
                for categoria, padrao in padroes_ativos.items():
                    ocorrencias = list(set(re.findall(padrao, texto_pagina)))
                    for oco in ocorrencias:
                        
                        # ── REGRA DE EXCEÇÃO INTELIGENTE PARA MATRÍCULAS NITTRANS ──────
                        if categoria == "RG" and re.fullmatch(r"1\.?\d{3}\.?\d{3}-\d", oco):
                            continue # Ignora se for a matrícula do servidor
                        # ───────────────────────────────────────────────────────────────

                        areas = pagina.search_for(oco)
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
                        areas = pagina.search_for(termo)
                        for area in areas:
                            pagina.add_redact_annot(area, fill=(0, 0, 0))
                            tarjas_encontradas += 1
                            
                return tarjas_encontradas, texto_pagina

            # ── MÉTODO 1: TEXTO SELECIONADO NATIVO ──
            tarjas_na_pagina, texto_extraido = buscar_e_tarjar()
            
            # ── MÉTODO 2: FALLBACK PARA OCR (IMAGENS) ──
            # Aciona apenas se não achar nada E a página não tiver texto extraível legível (< 50 caracteres)
            if tarjas_na_pagina == 0 and len(texto_extraido.strip()) < 50:
                try:
                    # Roda o OCR na página para construir as coordenadas fantasma
                    pagina.get_textpage_ocr(language="por")
                    
                    # Tenta realizar a busca de novo, agora com o OCR ativo
                    tarjas_na_pagina, _ = buscar_e_tarjar()
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