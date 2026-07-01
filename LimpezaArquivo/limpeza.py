import os
import glob
import shutil
import hashlib
import pandas as pd
import re
import sys
import unicodedata

from tqdm import tqdm
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


PASTA_ENTRADA = "entrada"
PASTA_SAIDA = "resultados"
PASTA_BACKUP = "backup"

CIDADE_BUSCA = "Niterói, RJ, Brasil"

ENCODINGS = ["utf-8", "utf-8-sig", "cp1252", "latin-1", "iso-8859-1"]
SEPARADORES = [";", ","]

COLUNAS_PRI_MAIUSCULA_POSICAO = [
    1,   # TITULO
    6,   # ENDERECO
    14   # BAIRRO
]

_geolocator = None
_geocode_fn = None
cache_enderecos = {}


def _get_geocode():
    global _geolocator, _geocode_fn
    if _geocode_fn is None:
        _geolocator = Nominatim(user_agent="validador_posicional_nittrans_vFinal")
        _geocode_fn = RateLimiter(_geolocator.geocode, min_delay_seconds=1.2, swallow_exceptions=True)
    return _geocode_fn


def gerar_hash_arquivo(caminho):
    sha256 = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(4096), b""):
            sha256.update(bloco)
    return sha256.hexdigest()


def possui_mojibake(texto):
    padroes = ["Ã", "Â", "â", ""]
    return any(p in str(texto) for p in padroes)


def corrigir_mojibake_profundo(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip()
    if texto == "":
        return ""

    for _ in range(5):
        try:
            novo = texto.encode("latin1").decode("utf-8")
            if novo == texto:
                break
            texto = novo
        except Exception:
            break

    texto = unicodedata.normalize("NFKC", texto)
    texto = texto.replace("", "")
    texto = re.sub(r"[\x00-\x1F\x7F]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def excel_arrumar(texto):
    if pd.isna(texto):
        return ""
    texto = corrigir_mojibake_profundo(texto)
    texto = texto.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def excel_pri_maiuscula(texto):
    if pd.isna(texto):
        return ""
    texto = corrigir_mojibake_profundo(texto)

    palavras_minusculas = {"da", "de", "do", "das", "dos", "e"}
    palavras = str(texto).split()
    resultado = []

    for i, palavra in enumerate(palavras):
        palavra = palavra.lower()
        if "'" in palavra:
            partes = palavra.split("'")
            partes = [p.capitalize() for p in partes]
            palavra = "'".join(partes)
        elif palavra.startswith("mc") and len(palavra) > 2:
            palavra = "Mc" + palavra[2:].capitalize()
        else:
            palavra = palavra.capitalize()

        if i > 0 and palavra.lower() in palavras_minusculas:
            palavra = palavra.lower()
        resultado.append(palavra)

    return " ".join(resultado)


def remover_caracteres_invalidos(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto)
    texto = texto.replace("", "")
    texto = re.sub(r"[\x00-\x1F\x7F]", "", texto)
    return texto.strip()


def formatar_endereco(texto):
    texto = excel_arrumar(texto)
    texto = remover_caracteres_invalidos(texto)

    substituicoes = {
        r"\bR\b\.?": "Rua",
        r"\bAl\b\.?": "Alameda",
        r"\bEstr\b\.?": "Estrada",
        r"\bTv\b\.?": "Travessa",
        r"\bPça\b\.?": "Praça",
        r"\bPr\b\.?": "Praça",
        r"\bAv\b\.?": "Av.",
    }

    for padrao, novo in substituicoes.items():
        texto = re.sub(padrao, novo, texto, flags=re.IGNORECASE)

    texto = re.sub(r"\bAv\.\.", "Av.", texto)
    texto = excel_pri_maiuscula(texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def limpar_nomes_colunas(df):
    novas_colunas = []
    for col in df.columns:
        col = corrigir_mojibake_profundo(col)
        col = excel_arrumar(col)
        col = excel_pri_maiuscula(col)
        novas_colunas.append(col)
    df.columns = novas_colunas
    return df


def validar_dataframe(df):
    if df is None:
        return False, "DataFrame inválido"
    if df.empty:
        return False, "Planilha vazia"
    if df.shape[1] < 15:
        return False, "Menos de 15 colunas"
    return True, ""


def ler_csv_seguro(caminho):
    for sep in SEPARADORES:
        for enc in ENCODINGS:
            try:
                # Alterações de segurança: 
                # 1. on_bad_lines="warn" para alertar sobre quebras em vez de apagar em silêncio.
                # 2. quotechar='"' para entender os blocos de texto do agente.
                # 3. Omitido engine="python" para usar o motor C nativo, que lê os Enters perfeitamente.
                df = pd.read_csv(
                    caminho, sep=sep, encoding=enc,
                    on_bad_lines="warn", dtype=str, quotechar='"'
                )
                valido, _ = validar_dataframe(df)
                if valido:
                    return df
            except Exception:
                continue
    return None


def ler_planilha(caminho):
    extensao = os.path.splitext(caminho)[1].lower()
    try:
        if extensao == ".csv":
            return ler_csv_seguro(caminho)
        elif extensao in [".xlsx", ".xls"]:
            return pd.read_excel(caminho, dtype=str)
    except Exception as e:
        print(f"Erro ao abrir arquivo: {e}")
    return None


def detectar_corrupcao(df):
    problemas = []
    for col in df.columns:
        possui = df[col].astype(str).str.contains(r"[Ã]|[Â]", regex=True, na=False).any()
        if possui:
            problemas.append(col)
    return problemas


def buscar_endereco_oficial(endereco, bairro):
    chave = f"{endereco}|{bairro}"
    if chave in cache_enderecos:
        return cache_enderecos[chave]

    query = f"{endereco}, {bairro}, {CIDADE_BUSCA}"
    try:
        geocode = _get_geocode()
        location = geocode(query, addressdetails=True, timeout=10)
        if not location:
            cache_enderecos[chave] = endereco
            return endereco

        detalhes = location.raw.get("address", {})
        rua = detalhes.get("road")
        if not rua:
            cache_enderecos[chave] = endereco
            return endereco

        rua = formatar_endereco(rua)
        cache_enderecos[chave] = rua
        return rua
    except Exception:
        cache_enderecos[chave] = endereco
        return endereco


def aplicar_correcoes_especiais(df):
    substituicoes = {
        "ComentÃ¡rio": "Comentário",
        "HistÃ³rico": "Histórico",
        "OperaÃ§Ã£o": "Operação",
        "AÃÇÃO": "AÇÃO",
        "SÃ£o": "São",
        "NiterÃ³i": "Niterói",
        "InformaÃ§Ã£o": "Informação",
        "FiscalizaÃ§Ã£o": "Fiscalização",
        "VeÃ­culo": "Veículo",
        "ColisÃ£o": "Colisão",
        "SituaÃ§Ã£o": "Situação",
    }

    for col in df.columns:
        df[col] = df[col].astype(str)
        for errado, correto in substituicoes.items():
            df[col] = df[col].str.replace(errado, correto, regex=False)
    return df


def processar_arquivo(caminho_arquivo):
    nome_arquivo = os.path.basename(caminho_arquivo)
    print(f"\n--- PROCESSANDO {nome_arquivo} ---")

    hash_original = gerar_hash_arquivo(caminho_arquivo)
    backup_destino = os.path.join(PASTA_BACKUP, nome_arquivo)
    shutil.copy2(caminho_arquivo, backup_destino)

    df = ler_planilha(caminho_arquivo)
    valido, motivo = validar_dataframe(df)
    if not valido:
        print(f"Arquivo inválido: {motivo}")
        return None

    df = limpar_nomes_colunas(df)

    for col in df.columns:
        df[col] = df[col].astype(str)
        df[col] = df[col].apply(corrigir_mojibake_profundo)
        df[col] = df[col].apply(excel_arrumar)

        indice_coluna = df.columns.get_loc(col)
        if indice_coluna in COLUNAS_PRI_MAIUSCULA_POSICAO:
            df[col] = df[col].apply(excel_pri_maiuscula)

    df = aplicar_correcoes_especiais(df)

    nome_col_id = df.columns[0]
    nome_col_endereco = df.columns[6]
    nome_col_bairro = df.columns[14]
    relatorio = []

    _sem_console = sys.stderr is None or sys.stdout is None
    for index, row in tqdm(df.iterrows(), total=len(df), desc=nome_arquivo, disable=_sem_console):
        try:
            id_registro = row[nome_col_id]
            endereco_original = str(row[nome_col_endereco])
            bairro_original = str(row[nome_col_bairro])

            endereco = formatar_endereco(endereco_original)
            bairro = excel_pri_maiuscula(bairro_original)
            endereco_oficial = buscar_endereco_oficial(endereco, bairro)

            if endereco_oficial:
                endereco = endereco_oficial

            endereco = excel_pri_maiuscula(endereco)
            bairro = excel_pri_maiuscula(bairro)

            if endereco != endereco_original:
                relatorio.append({
                    "Arquivo": nome_arquivo, "ID": id_registro,
                    "Coluna": nome_col_endereco, "Original": endereco_original,
                    "Corrigido": endereco, "Tipo": "Endereco"
                })
                df.at[index, nome_col_endereco] = endereco

            if bairro != bairro_original:
                relatorio.append({
                    "Arquivo": nome_arquivo, "ID": id_registro,
                    "Coluna": nome_col_bairro, "Original": bairro_original,
                    "Corrigido": bairro, "Tipo": "Bairro"
                })
                df.at[index, nome_col_bairro] = bairro

        except Exception as e:
            relatorio.append({
                "Arquivo": nome_arquivo, "ID": "ERRO", "Coluna": "GERAL",
                "Original": "", "Corrigido": "", "Tipo": str(e)
            })

    colunas_com_problema = detectar_corrupcao(df)
    if colunas_com_problema:
        print("\n⚠ POSSÍVEL CORRUPÇÃO RESIDUAL:")
        for c in colunas_com_problema:
            print(f" - {c}")

    nome_puro = os.path.splitext(nome_arquivo)[0]
    caminho_saida = os.path.join(PASTA_SAIDA, f"{nome_puro}_LIMPO.xlsx")
    df.to_excel(caminho_saida, index=False, engine="openpyxl")

    hash_final = gerar_hash_arquivo(caminho_saida)
    print(f"\n✓ Arquivo salvo: {caminho_saida}")
    print(f"Hash Original: {hash_original}")
    print(f"Hash Final:    {hash_final}")

    if relatorio:
        caminho_relatorio = os.path.join(PASTA_SAIDA, f"{nome_puro}_RELATORIO.xlsx")
        pd.DataFrame(relatorio).to_excel(caminho_relatorio, index=False)
        print(f"✓ Relatório salvo: {caminho_relatorio}")

    return True


def processar_pasta():
    for pasta in [PASTA_ENTRADA, PASTA_SAIDA, PASTA_BACKUP]:
        os.makedirs(pasta, exist_ok=True)

    arquivos = glob.glob(os.path.join(PASTA_ENTRADA, "*.*"))
    arquivos_validos = [
        a for a in arquivos
        if os.path.splitext(a)[1].lower() in [".csv", ".xlsx", ".xls"]
    ]

    if not arquivos_validos:
        print(f"Nenhum arquivo encontrado em '{PASTA_ENTRADA}'")
        return

    for arquivo in arquivos_validos:
        try:
            processar_arquivo(arquivo)
        except Exception as e:
            print(f"\nERRO CRÍTICO EM {arquivo}: {e}")

    print("\n====================================")
    print("PROCESSAMENTO FINALIZADO")
    print("====================================")


if __name__ == "__main__":
    processar_pasta()