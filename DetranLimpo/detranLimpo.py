# -*- coding: utf-8 -*-
import os
import re
import json
import shutil
import unicodedata
import pandas as pd
from pathlib import Path
from datetime import datetime

try:
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
    _GEOPY_OK = True
except ImportError:
    _GEOPY_OK = False

PASTA_ENTRADA = Path('entrada')
PASTA_BACKUP  = Path('backup')
PASTA_SAIDA   = Path('resultados')
CACHE_FILE    = Path('cache_ruas.json')
CIDADE        = 'Niterói, RJ, Brasil'

# Tudo a partir de marcador de posição: OP., OP. OP., OPOSTO, LADO OP., AO LADO DO
_RE_SUFIXO = re.compile(
    r'[\s,]+(?:NO?\s+)?(?:LADO\s+)?OP(?:OSTO)?\b.*$|'
    r'[\s,]+AO\s+LADO\b.*$|'
    r'[\s,]+OPOSTO\b.*$',
    re.IGNORECASE
)

# PRÓXIMO / PROX (+ tudo que vier depois)
_RE_PROXIMO = re.compile(
    r'[\s,]+PR[OÓ]XIMO\b.*$|'
    r'[\s,]+PROX\.?\b.*$',
    re.IGNORECASE
)

# Nº / N° / N NNN no final
_RE_NUM_ABREV = re.compile(
    r'[\s,]+N[º°oa]?\.?\s*\d+\b.*$',
    re.IGNORECASE
)

# Cruzamentos: "COM RUA", "C/ R.", "C RUA", "CRUZAMENTO COM"
_RE_CRUZAMENTO = re.compile(
    r'\s+(?:CRUZAMENTO\b.*|C(?:OM\s+|/\s*|\s+)(?:R\.?|RUA|AV\.?|AVENIDA)\b.*)$',
    re.IGNORECASE
)

# Prefixo inválido antes de tipo de logradouro: "ZRUA" → "RUA", "BAV" → "AV"
_RE_PREFIXO = re.compile(
    r'^[A-Z]{1,3}(?=\b(?:RUA|AV|AVENIDA|AL|ALAMEDA|TRAVESSA|ESTRADA|PRACA)\b)',
    re.IGNORECASE
)
# ─── Estado global do geocoder ────────────────────────────────────────────────
_geocode_fn  = None
_cache_ruas  = {}


def _normalizar(texto):
    return unicodedata.normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode().lower()


def _carregar_cache():
    global _cache_ruas
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                _cache_ruas = json.load(f) # Carregamento direto, sem loop de auto-cura
            print(f'  Cache carregado: {len(_cache_ruas)} ruas prontas.')
        except Exception as e:
            print(f"  Erro ao carregar cache: {e}")
            _cache_ruas = {}


def _salvar_cache():
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_cache_ruas, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _get_geocode():
    global _geocode_fn
    if _geocode_fn is None:
        geolocator = Nominatim(user_agent="detran_limpo_nittrans_v2")
        _geocode_fn = RateLimiter(geolocator.geocode, min_delay_seconds=1.2,
                                  swallow_exceptions=True)
    return _geocode_fn


def _corrigir_por_api(rua):
    if len(rua) < 10 or ' ' not in rua:
        return rua
    """Consulta Nominatim e devolve o nome oficial da rua em Niterói/RJ."""
    if not rua or len(rua) < 4:
        return rua

    chave = rua.upper().strip()
    if chave in _cache_ruas:
        return _cache_ruas[chave]

    try:
        location = _get_geocode()(f"{rua}, {CIDADE}", addressdetails=True, timeout=10)
        if location:
            addr = location.raw.get('address', {})
            road = (addr.get('road') or addr.get('pedestrian')
                    or addr.get('footway') or addr.get('residential'))
            if road:
                _cache_ruas[chave] = road
                return road
    except Exception:
        pass

    _cache_ruas[chave] = rua
    return rua


def limpar_logradouro(texto):
    """Limpa um endereço e aplica o formato de Primeira Letra Maiúscula."""
    texto = str(texto).strip()
    if not texto or texto.lower() == 'nan':
        return ''

    # ... (suas limpezas de regex existentes aqui: _RE_SUFIXO, _RE_PREFIXO, etc.)
    limpo = _RE_SUFIXO.sub('', texto).strip()
    limpo = _RE_PROXIMO.sub('', limpo).strip()
    limpo = _RE_NUM_ABREV.sub('', limpo).strip()
    limpo = _RE_CRUZAMENTO.sub('', limpo).strip()
    limpo = _RE_PREFIXO.sub('', limpo).strip()
    
    # 1. Aplica o formato Title Case (Primeira letra maiúscula)
    # O .title() do Python às vezes falha com nomes como "Rua De" 
    # (ele colocaria "Rua De" em vez de "Rua de").
    # Uma forma melhor é usar .capitalize() para cada palavra:
    palavras = limpo.lower().split()
    limpo = " ".join([p.capitalize() for p in palavras])

    # 2. Correção de exceções específicas (opcional)
    # Isso garante que "De", "Da", "Do" fiquem em minúsculo, mantendo o padrão brasileiro
    excecoes = ["De", "Da", "Do", "Das", "Dos", "Em"]
    final = []
    for i, p in enumerate(palavras):
        palavra_formatada = p.capitalize()
        if i > 0 and palavra_formatada in excecoes:
            final.append(palavra_formatada.lower())
        else:
            final.append(palavra_formatada)
            
    return " ".join(final).strip()

def _encontrar_coluna(df):
    """Verifica colunas de forma flexível: aceita qualquer termo relacionado a endereço."""
    termos_busca = ['ender', 'logradouro', 'rua', 'local']
    for col in df.columns:
        n = _normalizar(col)
        # Se qualquer termo de busca estiver no nome da coluna, ela é aceita
        if any(termo in n for termo in termos_busca):
            print(f"  Coluna '{col}' aceita.") # Feedback visual no terminal
            return col
    return None


def _ler_arquivo(caminho):
    ext = caminho.suffix.lower()
    if ext == '.csv':
        for sep in [';', ',']:
            for enc in ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']:
                try:
                    df = pd.read_csv(caminho, sep=sep, encoding=enc,
                                     dtype=str, on_bad_lines='skip')
                    if len(df.columns) > 1:
                        return df
                except Exception:
                    continue
        return None
    return pd.read_excel(caminho, dtype=str)


def rodar_detran_limpo():
    for pasta in [PASTA_ENTRADA, PASTA_BACKUP, PASTA_SAIDA]:
        pasta.mkdir(exist_ok=True)

    extensoes = {'.xlsx', '.xls', '.csv'}
    arquivos = [f for f in PASTA_ENTRADA.iterdir() if f.suffix.lower() in extensoes]

    if not arquivos:
        print(f"Nenhum arquivo encontrado em '{PASTA_ENTRADA}'.")
        return

    _carregar_cache()

    for arquivo in arquivos:
        print(f"\nProcessando: {arquivo.name}")
        try:
            df = _ler_arquivo(arquivo)
            if df is None or df.empty:
                print("  Não foi possível ler o arquivo.")
                continue

            col = _encontrar_coluna(df)
            if not col:
                print(f"  Coluna de endereço não encontrada.")
                continue

            print(f"  Coluna encontrada: '{col}'")

            # Passo 1 — limpeza local (regex)
            rua_limpa = df[col].apply(limpar_logradouro)

            # Passo 2 — Mapeamento via Cache (Sem API para evitar erro 429)
            unicas = [r for r in rua_limpa.dropna().unique() if r and len(r) >= 4]
            print(f"  Aplicando cache existente para {len(unicas)} ruas...")
            
            mapa = {rua: _cache_ruas.get(rua.upper().strip(), rua) for rua in unicas}
            rua_limpa = rua_limpa.map(lambda r: mapa.get(r, r))
            
            print("  Aplicação do cache concluída.")

            # Insere ou sobrescreve coluna "Rua"
            col_rua = next((c for c in df.columns if _normalizar(c) == 'rua'), None)
            if col_rua is None:
                pos = df.columns.get_loc(col) + 1
                df.insert(pos, 'Rua', rua_limpa)
            else:
                df[col_rua] = rua_limpa

            data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_saida = PASTA_SAIDA / f"{arquivo.stem}_limpo_{data_hora}.xlsx"
            df.to_excel(nome_saida, index=False)
            print(f"  {len(df)} registros → {nome_saida.name}")

            shutil.move(str(arquivo), str(PASTA_BACKUP / arquivo.name))

        except Exception as e:
            print(f"  Erro no processamento: {e}")

    print("\nConcluído.")


if __name__ == "__main__":
    rodar_detran_limpo()
