# -*- coding: utf-8 -*-
import os
import re
import json
import shutil
import unicodedata
import pandas as pd
from pathlib import Path
from datetime import datetime
from thefuzz import process, fuzz

# Configuração de Pastas
PASTA_ENTRADA = Path('entrada')
PASTA_BACKUP  = Path('backup')
PASTA_SAIDA   = Path('resultados')
BASE_OFICIAL  = Path('ruas_oficiais_niteroi.json')

_dicionario_oficial = {}
_chaves_oficiais = []
_memoria_rapida = {} 

# A TESOURA REGEX 
_RE_LIXO_FINAL = re.compile(
    r'[\s,]+(?:'
    r's/?n|ap(?:t|to)?\.?|bl(?:oco)?\.?|c(?:a)?s(?:a)?\.?|fundos|'
    r'qd\.?|quadra|lt\.?|lote|km|loja|sala|'
    r'(?<!\b(?:br|rj)\s)\d+[a-z]?\b(?!\s+(?:de|da|do|das|dos)\b)' 
    r').*$', 
    re.IGNORECASE
)

# Filtros Básicos
_RE_SUFIXO = re.compile(r'[\s,]+(?:NO?\s+)?(?:LADO\s+)?OP(?:OSTO)?\b.*$|[\s,]+AO\s+LADO\b.*$|[\s,]+OPOSTO\b.*$', re.IGNORECASE)
_RE_PROXIMO = re.compile(r'[\s,]+PR[OÓ]XIMO\b.*$|[\s,]+PROX\.?\b.*$', re.IGNORECASE)
_RE_CRUZAMENTO = re.compile(r'\s+(?:CRUZAMENTO\b.*|C(?:OM\s+|/\s*|\s+)(?:R\.?|RUA|AV\.?|AVENIDA)\b.*)$', re.IGNORECASE)

def _normalizar(texto):
    return unicodedata.normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode().upper().strip()

def carregar_base_oficial():
    global _dicionario_oficial, _chaves_oficiais
    if BASE_OFICIAL.exists():
        with open(BASE_OFICIAL, 'r', encoding='utf-8') as f:
            _dicionario_oficial = json.load(f)
            _chaves_oficiais = list(_dicionario_oficial.keys())
        print(f"Base Oficial carregada com {len(_chaves_oficiais)} ruas.")
    else:
        print("AVISO: A Base Oficial JSON de Niterói não foi encontrada na pasta.")

def padronizar_prefixos(texto):
    """Expande abreviações para o nome oficial, ajudando a IA a comparar melhor"""
    t = re.sub(r'^\b(?:R|R\.|RUA)\b', 'RUA', texto, flags=re.IGNORECASE)
    t = re.sub(r'^\b(?:AV|AV\.|AVEN|AVENIDA)\b', 'AVENIDA', t, flags=re.IGNORECASE)
    
    # ── CORREÇÃO DE PREFIXO ADICIONADA: 'STRADA' ──
    t = re.sub(r'^\b(?:EST|EST\.|ESTR|ESTRADA|STRADA)\b', 'ESTRADA', t, flags=re.IGNORECASE)
    
    t = re.sub(r'^\b(?:TV|TV\.|TRAV|TRAVESSA)\b', 'TRAVESSA', t, flags=re.IGNORECASE)
    t = re.sub(r'^\b(?:AL|AL\.|ALAM|ALAMEDA)\b', 'ALAMEDA', t, flags=re.IGNORECASE)
    t = re.sub(r'^\b(?:PR|PR\.|PCA|PÇA|PRACA|PRAÇA)\b', 'PRACA', t, flags=re.IGNORECASE)
    t = re.sub(r'^\b(?:B|B\.|BECO)\b', 'BECO', t, flags=re.IGNORECASE)
    t = re.sub(r'^\b(?:LAD|LAD\.|LADEIRA)\b', 'LADEIRA', t, flags=re.IGNORECASE)
    
    # ── CORREÇÕES FONÉTICAS E ORTOGRÁFICAS COMUNS ──
    # Ensina a IA a tratar erros de digitação clássicos antes da matemática do Fuzzy
    foneticas = {
        r'\bFLEXA\b': 'FLECHA',
        r'\bFLEXAS\b': 'FLECHAS',
        r'\bFROIS\b': 'FROES',                # Leopoldo Fróes escrito com I
        r'\bWASHIN?G?T?O[NM]\b': 'WASHINGTON', # Cobre Washigton, Washinton, Washigton...
        r'\bNILCON\b': 'NILKON',              # Nilkon Vianna
        r'\bTHEOFILO FRANCISCO\b': 'FRANCISCO',# Ignora o 'Theofilo' antigo
        r'\bSTRADA\b': 'ESTRADA'               # Cobre 'Strada' se for digitado no meio do texto
    }
    
    for errado, certo in foneticas.items():
        t = re.sub(errado, certo, t, flags=re.IGNORECASE)
        
    return t

def limpar_logradouro(texto):
    texto = str(texto).strip()
    if not texto or texto.lower() == 'nan': return ''
    
    limpo = padronizar_prefixos(texto)
    limpo = _RE_SUFIXO.sub('', limpo).strip()
    limpo = _RE_PROXIMO.sub('', limpo).strip()
    limpo = _RE_CRUZAMENTO.sub('', limpo).strip()
    limpo = _RE_LIXO_FINAL.sub('', limpo).strip() 
    
    palavras = limpo.lower().split()
    excecoes = ["de", "da", "do", "das", "dos", "em"]
    final = [p if i > 0 and p in excecoes else p.capitalize() for i, p in enumerate(palavras)]
    return " ".join(final).strip()

def corrigir_rua_offline(rua_suja):
    if not rua_suja or str(rua_suja).lower() == 'nan': return ""
    
    # Limpa os números e sujeiras, mantendo os prefixos padronizados
    rua_limpa = limpar_logradouro(rua_suja)
    
    if not _dicionario_oficial:
        return rua_limpa 

    chave_busca = _normalizar(rua_limpa)
    
    # 1. Consulta Rápida na Memória
    if chave_busca in _memoria_rapida:
        return _memoria_rapida[chave_busca]
        
    # 2. Busca Exata no Mapa
    if chave_busca in _dicionario_oficial:
        _memoria_rapida[chave_busca] = _dicionario_oficial[chave_busca]
        return _memoria_rapida[chave_busca]

    # 3. Busca Inteligente Estrita (Não inventa nomes)
    melhor_match = process.extractOne(chave_busca, _chaves_oficiais, scorer=fuzz.token_sort_ratio)
    
    if melhor_match:
        nome_achado, pontuacao = melhor_match
        # 82 é o ponto de equilíbrio perfeito para pegar erros de digitação sem alucinar
        if pontuacao >= 82:  
            oficial = _dicionario_oficial[nome_achado]
            _memoria_rapida[chave_busca] = oficial
            return oficial

    # Se a pontuação for baixa, significa que não achou no mapa. Devolve a rua apenas limpa.
    _memoria_rapida[chave_busca] = rua_limpa
    return rua_limpa

def _encontrar_coluna(df):
    # Prioriza colunas de endereço que tenham texto, ignorando colunas de códigos numéricos
    ordem_prioridade = ['ENDER', 'LOGRADOURO', 'DESCRI', 'LOCAL', 'INFRACAO', 'RUA']
    
    for palavra in ordem_prioridade:
        for col in df.columns:
            n = _normalizar(col)
            if palavra in n:
                # Verifica se a coluna possui letras (para não pegar colunas com números como "736")
                if df[col].astype(str).str.contains(r'[A-Za-z]', regex=True, na=False).any():
                    return col
    return None

def _ler_arquivo(caminho):
    ext = caminho.suffix.lower()
    if ext == '.csv':
        melhor_df = None
        max_cols = 0
        for sep in [';', ',', '\t', '|']:
            for enc in ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']:
                try:
                    df = pd.read_csv(caminho, sep=sep, encoding=enc, dtype=str, on_bad_lines='skip')
                    if len(df.columns) > max_cols:
                        max_cols = len(df.columns)
                        melhor_df = df
                except Exception:
                    continue
                    
        if melhor_df is not None and not melhor_df.empty:
            return melhor_df
        raise ValueError(f"Não foi possível extrair dados estruturados do CSV '{caminho.name}'.")
        
    return pd.read_excel(caminho, dtype=str)

def rodar_detran_limpo():
    try:
        for p in [PASTA_ENTRADA, PASTA_BACKUP, PASTA_SAIDA]: p.mkdir(exist_ok=True)
        arquivos = [f for f in PASTA_ENTRADA.iterdir() if f.suffix.lower() in {'.xlsx', '.xls', '.csv'}]
        
        if not arquivos:
            raise FileNotFoundError("Nenhum arquivo de leitura encontrado na pasta 'entrada'.")
            
        carregar_base_oficial()
        
        for arquivo in arquivos:
            print(f"\nProcessando: {arquivo.name}")
            df = _ler_arquivo(arquivo)
            
            if df is None or df.empty: 
                raise ValueError(f"O arquivo {arquivo.name} parece estar vazio ou não pôde ser lido corretamente.")
                
            col = _encontrar_coluna(df)
            if not col: 
                colunas_vistas = " | ".join(list(df.columns))
                raise ValueError(f"Não achei a coluna de endereço no arquivo '{arquivo.name}'. As colunas que o robô enxergou foram: [ {colunas_vistas} ]")

            print(f"  Iniciando a Correção Inteligente (Offline Mode) na coluna '{col}'...")
    
            # === CORREÇÃO DA IDENTAÇÃO AQUI ===
            # Cria a nova coluna com o nome limpo da rua (agora devidamente alinhada dentro do 'for')
            df['Rua'] = df[col].apply(corrigir_rua_offline)
            
            data_hora = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_saida = PASTA_SAIDA / f"{arquivo.stem}_limpo_{data_hora}.xlsx"
            df.to_excel(nome_saida, index=False)
            
            # A planilha já foi gravada; falhar o backup não invalida o
            # resultado, mas também não pode passar calado — o arquivo fica
            # em 'entrada' e seria reprocessado na próxima execução.
            try:
                shutil.move(str(arquivo), str(PASTA_BACKUP / arquivo.name))
            except OSError as erro:
                print(f"  ATENÇÃO: não foi possível mover '{arquivo.name}'"
                      f" para '{PASTA_BACKUP}': {erro}")
                print("  O arquivo continua em 'entrada'.")

            print(f"  Concluído com sucesso -> {nome_saida.name}")
            # ====================================

    except Exception as e:
        print(type(e))
        print(repr(e))
        raise e


if __name__ == "__main__":
    rodar_detran_limpo()