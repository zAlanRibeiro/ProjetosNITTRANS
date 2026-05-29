# -*- coding: utf-8 -*-
import os
import re
import shutil
import unicodedata
import pandas as pd
from pathlib import Path
from datetime import datetime

PASTA_ENTRADA = Path('entrada')
PASTA_BACKUP  = Path('backup')
PASTA_SAIDA   = Path('resultados')

_RE_SUFIXO = re.compile(
    r'[\s,]+(LADO\s+)?OP\.?(\s+OP\.?)*\s*$|'
    r'\s+OPOSTO\s*$',
    re.IGNORECASE
)

# Cruzamentos: "COM RUA SAO PEDRO", "C/ R. BARAO", "CRUZAMENTO COM..."
_RE_CRUZAMENTO = re.compile(
    r'\s+(?:CRUZAMENTO\b.*|C(?:OM\s+|/\s*)(?:R\.?|RUA|AV\.?|AVENIDA)\b.*)$',
    re.IGNORECASE
)


def _normalizar(texto):
    return unicodedata.normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode().lower()


def _encontrar_coluna(df):
    """Localiza a coluna de endereço independente de encoding ou variações de nome."""
    for col in df.columns:
        n = _normalizar(col)
        if ('descri' in n or 'munic' in n) and 'ender' in n:
            return col
    return None


def limpar_logradouro(texto):
    """Remove número e sufixos de posição (OP., OPOSTO, N 340…) do endereço."""
    texto = str(texto).strip()
    if not texto or texto.lower() == 'nan':
        return ''

    limpo = _RE_SUFIXO.sub('', texto).strip()
    limpo = _RE_CRUZAMENTO.sub('', limpo).strip()

    # Faixa: "151 AO 251"
    m = re.match(r'^(.*?),?\s*(\d+\s+[Aa][Oo]\s+\d+)\s*$', limpo)
    if m:
        return re.sub(r'\s+N\.?\s*$', '', m.group(1).strip(), flags=re.IGNORECASE)

    # Número simples: "123", "45A", "12-B"
    m = re.match(r'^(.*?),?\s*(\d+[\w-]*)\s*$', limpo)
    if m:
        return re.sub(r'\s+N\.?\s*$', '', m.group(1).strip(), flags=re.IGNORECASE)

    return limpo


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
                print(f"  Colunas disponíveis: {list(df.columns)}")
                continue

            print(f"  Coluna encontrada: '{col}'")

            rua_limpa = df[col].apply(limpar_logradouro)

            # Detecta se já existe coluna "Rua"
            col_rua = next(
                (c for c in df.columns if _normalizar(c) == 'rua'),
                None
            )

            if col_rua is None:
                pos = df.columns.get_loc(col) + 1
                df.insert(pos, 'Rua', rua_limpa)
            else:
                # Sempre sobrescreve — garante que valores truncados ou incompletos sejam corrigidos
                df[col_rua] = rua_limpa

            print(f"  Coluna 'Rua': {len(df)} linha(s) atualizadas")

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