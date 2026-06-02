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
    r'^[A-Z]{1,3}(?=RUA\b|AV\b|AVENIDA\b|AL\b|ALAMEDA\b|TRAVESSA\b|ESTRADA\b|PRAC[AÇ])',
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
                raw = json.load(f)
            # Auto-cura: re-chaveado e valores limpos
            _cache_ruas = {}
            for k, v in raw.items():
                chave = limpar_logradouro(k).upper().strip()
                valor = limpar_logradouro(v) if v.upper().strip() == k.upper().strip() else v
                if chave:
                    _cache_ruas[chave] = valor
            print(f'  Cache de ruas: {len(_cache_ruas)} entradas carregadas.')
        except Exception:
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
    """Limpa um endereço removendo número, sufixos e corrigindo prefixo."""
    texto = str(texto).strip()
    if not texto or texto.lower() == 'nan':
        return ''

    limpo = _RE_SUFIXO.sub('', texto).strip()
    limpo = _RE_PROXIMO.sub('', limpo).strip()
    limpo = _RE_NUM_ABREV.sub('', limpo).strip()
    limpo = _RE_CRUZAMENTO.sub('', limpo).strip()
    limpo = _RE_PREFIXO.sub('', limpo).strip()

    # Faixa: "151 AO 251"
    m = re.match(r'^(.*?),?\s*(\d+\s+[Aa][Oo]\s+\d+)\s*$', limpo)
    if m:
        return re.sub(r'\s+N\.?\s*$', '', m.group(1).strip(), flags=re.IGNORECASE)

    # Número simples no final: "123", "45A", "12-B"
    m = re.match(r'^(.*?),?\s*(\d+[\w-]*)\s*$', limpo)
    if m:
        return re.sub(r'\s+N\.?\s*$', '', m.group(1).strip(), flags=re.IGNORECASE)

    return limpo


def _encontrar_coluna(df):
    for col in df.columns:
        n = _normalizar(col)
        if ('descri' in n or 'munic' in n) and 'ender' in n:
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
                print(f"  Colunas: {list(df.columns)}")
                continue

            print(f"  Coluna encontrada: '{col}'")

            # Passo 1 — limpeza local (regex)
            rua_limpa = df[col].apply(limpar_logradouro)

            # Passo 2 — correção via API (apenas se geopy disponível)
            if _GEOPY_OK:
                unicas = [r for r in rua_limpa.dropna().unique() if r and len(r) >= 4]
                total = len(unicas)
                print(f"  Consultando API para {total} rua(s) única(s)...")

                progresso_path = PASTA_SAIDA / 'progresso_api.txt'
                mapa = {}
                for i, rua in enumerate(unicas, 1):
                    mapa[rua] = _corrigir_por_api(rua)

                    # Atualiza arquivo de progresso a cada rua
                    try:
                        progresso_path.write_text(
                            f"Processando via API...\n"
                            f"{i} de {total} ruas consultadas\n"
                            f"Ultima: {rua}\n",
                            encoding='utf-8'
                        )
                    except Exception:
                        pass

                    # Salva cache a cada 50 ruas
                    if i % 50 == 0:
                        _salvar_cache()
                        print(f"  {i}/{total} ruas consultadas...")

                rua_limpa = rua_limpa.map(lambda r: mapa.get(r, r))
                _salvar_cache()

                try:
                    progresso_path.write_text("Consulta API concluida!\n", encoding='utf-8')
                except Exception:
                    pass
            else:
                print("  geopy não disponível — usando apenas limpeza local.")

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
            print(f"  Erro: {e}")

    print("\nConcluído.")


if __name__ == "__main__":
    rodar_detran_limpo()
