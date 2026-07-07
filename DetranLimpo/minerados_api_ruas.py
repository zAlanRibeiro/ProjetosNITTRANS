# -*- coding: utf-8 -*-
import json
import time
import re
import unicodedata
import pandas as pd
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderRateLimited, GeocoderTimedOut, GeocoderUnavailable

CACHE_FILE = Path('cache_ruas.json')
PASTA_ENTRADA = Path('entrada')
CIDADE = 'Niterói, RJ, Brasil'

# O NOVO SUPER-FILTRO: Corta números de porta, apartamentos, lotes e lixo final
_RE_LIXO_FINAL = re.compile(
    r'[\s,]+(?:'
    r's/?n|ap(?:t|to)?\.?|bl(?:oco)?\.?|c(?:a)?s(?:a)?\.?|fundos|'
    r'qd\.?|quadra|lt\.?|lote|km|loja|sala|'
    r'(?<!\b(?:br|rj)\s)\d+[a-z]?\b(?!\s+(?:de|da|do|das|dos)\b)' # Corta a partir do 1º número isolado
    r').*$', 
    re.IGNORECASE
)

# Filtros antigos mantidos para segurança
_RE_SUFIXO = re.compile(r'[\s,]+(?:NO?\s+)?(?:LADO\s+)?OP(?:OSTO)?\b.*$|[\s,]+AO\s+LADO\b.*$|[\s,]+OPOSTO\b.*$', re.IGNORECASE)
_RE_PROXIMO = re.compile(r'[\s,]+PR[OÓ]XIMO\b.*$|[\s,]+PROX\.?\b.*$', re.IGNORECASE)
_RE_CRUZAMENTO = re.compile(r'\s+(?:CRUZAMENTO\b.*|C(?:OM\s+|/\s*|\s+)(?:R\.?|RUA|AV\.?|AVENIDA)\b.*)$', re.IGNORECASE)
_RE_PREFIXO = re.compile(r'^[A-Z]{1,3}(?=\b(?:RUA|AV|AVENIDA|AL|ALAMEDA|TRAVESSA|ESTRADA|PRACA)\b)', re.IGNORECASE)


def _normalizar(texto):
    return unicodedata.normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode().lower()


def limpar_logradouro(texto):
    texto = str(texto).strip()
    if not texto or texto.lower() == 'nan': return ''
    
    # 1. Aplica limpeza básica
    limpo = _RE_SUFIXO.sub('', texto).strip()
    limpo = _RE_PROXIMO.sub('', limpo).strip()
    limpo = _RE_CRUZAMENTO.sub('', limpo).strip()
    
    # 2. Aplica a TESOURA (Corta tudo do número da casa em diante)
    limpo = _RE_LIXO_FINAL.sub('', limpo).strip()
    
    limpo = _RE_PREFIXO.sub('', limpo).strip()
    
    # 3. Formata para Primeira Letra Maiúscula
    palavras = limpo.lower().split()
    excecoes = ["de", "da", "do", "das", "dos", "em"]
    final = [p if i > 0 and p in excecoes else p.capitalize() for i, p in enumerate(palavras)]
    return " ".join(final).strip()


def _encontrar_coluna(df):
    for col in df.columns:
        n = _normalizar(col)
        if any(t in n for t in ['ender', 'logradouro', 'rua', 'local']): return col
    return None


def _ler_arquivo(caminho):
    ext = caminho.suffix.lower()
    if ext == '.csv':
        for sep in [';', ',', '\t']:
            for enc in ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']:
                try:
                    df = pd.read_csv(caminho, sep=sep, encoding=enc, dtype=str, on_bad_lines='skip')
                    if len(df.columns) > 1: return df
                except Exception:
                    continue
        return None
    return pd.read_excel(caminho, dtype=str)


def carregar_cache():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def salvar_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def minerar_dados():
    print("A iniciar Minerador de Endereços via API (Modo Resiliente com Tesoura)...")
    cache_ruas = carregar_cache()
    print(f"Cache atual contém {len(cache_ruas)} ruas validadas.")

    arquivos = [f for f in PASTA_ENTRADA.iterdir() if f.suffix.lower() in {'.xlsx', '.xls', '.csv'}]
    if not arquivos:
        print("Nenhum ficheiro na pasta 'entrada'.")
        return

    ruas_unicas = set()
    for arquivo in arquivos:
        df = _ler_arquivo(arquivo)
        if df is not None:
            col = _encontrar_coluna(df)
            if col:
                ruas_limpas = df[col].apply(limpar_logradouro).dropna()
                ruas_unicas.update(ruas_limpas.unique())

    para_consultar = [r for r in ruas_unicas if r.upper().strip() not in cache_ruas and len(r) >= 4]
    
    total = len(para_consultar)
    print(f"Total de ruas limpas a validar na API: {total}\n")

    if total == 0:
        print("Todas as ruas já estão validadas no JSON!")
        return

    geolocator = Nominatim(user_agent="detran_minerador_nittrans_oficial")
    
    i = 0
    while i < total:
        rua = para_consultar[i]
        chave = rua.upper().strip()
        
        try:
            time.sleep(1.5)  
            
            location = geolocator.geocode(f"{rua}, {CIDADE}", addressdetails=True, timeout=10)
            if location:
                addr = location.raw.get('address', {})
                road = addr.get('road') or addr.get('pedestrian') or addr.get('residential')
                if road:
                    cache_ruas[chave] = road
                    print(f"[{i+1}/{total}] ✅ Validado: '{rua}' -> '{road}'")
                else:
                    cache_ruas[chave] = rua
                    print(f"[{i+1}/{total}] ⚠️ Sem nome exato: Mantido '{rua}'")
            else:
                cache_ruas[chave] = rua
                print(f"[{i+1}/{total}] ❌ Não encontrado: Mantido '{rua}'")

            if (i + 1) % 10 == 0:
                salvar_cache(cache_ruas)

            i += 1 

        except GeocoderRateLimited:
            print("\n[!] ERRO 429: Limite da API atingido.")
            print("[!] O minerador vai dormir por 15 minutos e tentará novamente...")
            salvar_cache(cache_ruas)
            time.sleep(900) 
            
        except (GeocoderTimedOut, GeocoderUnavailable):
            print("\n[!] Servidor instável. A aguardar 30 segundos...")
            time.sleep(30)
            
        except Exception as e:
            print(f"[{i+1}/{total}] Erro ({e}) - A saltar rua.")
            cache_ruas[chave] = rua
            i += 1

    salvar_cache(cache_ruas)
    print("\nMineração concluída com sucesso!")


if __name__ == "__main__":
    minerar_dados()