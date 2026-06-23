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
            texto_pagina = pagina.get_text("text")
            
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
                        total_tarjas += 1
            
            # 2. Manual (Lista com Inteligência de Palavras Isoladas)
            palavras_da_pagina = pagina.get_text("words") # Extrai as palavras separadamente
            
            for texto in lista_textos_manuais:
                termo = texto.strip()
                if not termo:
                    continue
                
                # Se for uma única palavra (não contém espaços)
                if " " not in termo:
                    # Busca exata comparando palavra por palavra da página
                    for w in palavras_da_pagina:
                        # w[4] é o texto puro. Limpamos pontuações nas bordas para comparar de forma justa
                        palavra_limpa = re.sub(r"^[^\w]+|[^\w]+$", "", w[4])
                        
                        # Compara ignorando maiúsculas/minúsculas para manter a facilidade de uso
                        if palavra_limpa.lower() == termo.lower():
                            # w[:4] contém as coordenadas exatas daquela palavra
                            area_palavra = fitz.Rect(w[:4])
                            pagina.add_redact_annot(area_palavra, fill=(0, 0, 0))
                            total_tarjas += 1
                else:
                    # Se for um nome/frase composta (ex: "João da Silva"), usamos a busca normal e segura
                    areas = pagina.search_for(termo)
                    for area in areas:
                        pagina.add_redact_annot(area, fill=(0, 0, 0))
                        total_tarjas += 1
            
            pagina.apply_redactions()
            
        doc.save(caminho_saida)
        doc.close()
        return True, f"Sucesso! {total_tarjas} informações ocultadas."
    except Exception as e:
        return False, f"Erro: {str(e)}"