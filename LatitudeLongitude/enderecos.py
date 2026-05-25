import pandas as pd
import time
import os
import shutil
import json
import sys

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from tqdm import tqdm


CACHE_FILE = 'cache_enderecos.json'
INTERVALO_SAVE_CACHE = 10


def ler_csv_automatico(caminho_arquivo):
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    for enc in encodings:
        try:
            print(f"-> Tentando encoding: {enc}")
            df = pd.read_csv(caminho_arquivo, sep=';', encoding=enc, low_memory=False)
            print(f"[✓] Arquivo carregado com sucesso usando: {enc}")
            return df
        except UnicodeDecodeError:
            print(f"[X] Falha no encoding: {enc}")
    raise Exception("Não foi possível ler o arquivo CSV.")


def identificar_colunas(df):
    nome_col_lat = None
    nome_col_lon = None
    colunas_minusculo = [str(c).lower().strip() for c in df.columns]
    nomes_lat = ['latitude', 'lat', 'y']
    nomes_lon = ['longitude', 'lon', 'lng', 'long', 'x']

    for nome in nomes_lat:
        if nome in colunas_minusculo:
            nome_col_lat = df.columns[colunas_minusculo.index(nome)]
            break

    for nome in nomes_lon:
        if nome in colunas_minusculo:
            nome_col_lon = df.columns[colunas_minusculo.index(nome)]
            break

    if not nome_col_lat or not nome_col_lon:
        print("\n-> Detectando coordenadas automaticamente...")
        for col in df.columns:
            try:
                serie = df[col].dropna()
                if len(serie) == 0:
                    continue
                valor_num = float(str(serie.iloc[0]).replace(',', '.').strip())
                if -35 < valor_num < 5 and not nome_col_lat:
                    nome_col_lat = col
                if -75 < valor_num < -30 and not nome_col_lon:
                    nome_col_lon = col
            except (ValueError, TypeError):
                continue

    return nome_col_lat, nome_col_lon


def _salvar_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _processar_arquivo(nome_arquivo, cache, reverse):
    caminho_entrada = os.path.join('entrada', nome_arquivo)

    print("\n========================================")
    print(f"ARQUIVO: {nome_arquivo}")
    print("========================================")

    extensao = os.path.splitext(nome_arquivo)[1].lower()

    if extensao == '.csv':
        df = ler_csv_automatico(caminho_entrada)
    elif extensao in ['.xlsx', '.xls']:
        df = pd.read_excel(caminho_entrada)
        print("Excel carregado com sucesso.")
    else:
        print("Formato não suportado.")
        return

    lat_col, lon_col = identificar_colunas(df)

    if not lat_col or not lon_col:
        print("\nNão foi possível identificar Latitude/Longitude.")
        return

    print(f"\nCoordenadas identificadas:")
    print(f"Latitude : {lat_col}")
    print(f"Longitude: {lon_col}")

    df['lat_aux'] = pd.to_numeric(
        df[lat_col].astype(str).str.replace(',', '.', regex=False).str.strip(),
        errors='coerce'
    )
    df['lon_aux'] = pd.to_numeric(
        df[lon_col].astype(str).str.replace(',', '.', regex=False).str.strip(),
        errors='coerce'
    )

    coordenadas_invalidas = df[df['lat_aux'].isna() | df['lon_aux'].isna()]
    if len(coordenadas_invalidas) > 0:
        print("\n========================================")
        print("COORDENADAS INVÁLIDAS ENCONTRADAS")
        print("========================================")
        for idx, row in coordenadas_invalidas.iterrows():
            print(f"Linha {idx + 1} -> Latitude: {row[lat_col]} | Longitude: {row[lon_col]}")
    else:
        print("\nNenhuma coordenada inválida encontrada.")

    df_coords = df[['lat_aux', 'lon_aux']].reset_index(drop=True)

    print(f"\nTotal linhas      : {len(df)}")
    print(f"Total coordenadas : {len(df_coords)}")

    ruas, bairros, numeros, cidades, ceps, estados = [], [], [], [], [], []
    nao_encontrados = []
    novos_no_cache = 0

    print("\n========================================")
    print("BUSCANDO ENDEREÇOS")
    print("========================================")

    _sem_console = sys.stderr is None or sys.stdout is None
    for _, row in tqdm(df_coords.iterrows(), total=len(df_coords), disable=_sem_console):
        lat = row['lat_aux']
        lon = row['lon_aux']

        if pd.isna(lat) or pd.isna(lon):
            ruas.append(''); bairros.append(''); numeros.append('')
            cidades.append(''); ceps.append(''); estados.append('')
            continue

        chave = f"{lat},{lon}"

        if chave in cache:
            resultado = cache[chave]
        else:
            resultado = {'rua': '', 'bairro': '', 'numero': '', 'cidade': '', 'cep': '', 'estado': ''}
            try:
                location = reverse((lat, lon), language='pt', timeout=30)
                if location and 'address' in location.raw:
                    address = location.raw['address']
                    resultado['rua'] = (
                        address.get('road') or address.get('pedestrian')
                        or address.get('footway') or address.get('residential')
                        or address.get('path') or ''
                    )
                    resultado['bairro'] = (
                        address.get('suburb') or address.get('neighbourhood')
                        or address.get('city_district') or address.get('quarter') or ''
                    )
                    resultado['numero'] = address.get('house_number') or ''
                    resultado['cidade'] = (
                        address.get('city') or address.get('town')
                        or address.get('municipality') or ''
                    )
                    resultado['cep'] = address.get('postcode') or ''
                    resultado['estado'] = address.get('state') or ''
            except Exception as erro:
                print(f"\nErro coordenada: {lat}, {lon} — {erro}")

            cache[chave] = resultado
            novos_no_cache += 1
            if novos_no_cache % INTERVALO_SAVE_CACHE == 0:
                _salvar_cache(cache)

        if not str(resultado['rua']).strip() and not str(resultado['bairro']).strip():
            nao_encontrados.append(f"Arquivo: {nome_arquivo} | Latitude: {lat} | Longitude: {lon}")

        ruas.append(resultado['rua'])
        bairros.append(resultado['bairro'])
        numeros.append(resultado['numero'])
        cidades.append(resultado['cidade'])
        ceps.append(resultado['cep'])
        estados.append(resultado['estado'])

    if nao_encontrados:
        caminho_txt = os.path.join('resultados', 'coordenadas_nao_encontradas.txt')
        with open(caminho_txt, 'a', encoding='utf-8') as f:
            f.write('\n'.join(nao_encontrados) + '\n')
        print(f"\nCoordenadas não encontradas registradas em: {caminho_txt}")
    else:
        print("\nTodas as coordenadas foram encontradas.")

    df['Endereco_Rua'] = ruas
    df['Bairro'] = bairros
    df['Numero_Imovel'] = numeros
    df['Cidade'] = cidades
    df['CEP'] = ceps
    df['Estado'] = estados
    df = df.drop(columns=['lat_aux', 'lon_aux'])

    nome_base, extensao = os.path.splitext(nome_arquivo)
    caminho_saida = os.path.join('resultados', f"{nome_base}_corrigido{extensao}")

    if extensao == '.csv':
        df.to_csv(caminho_saida, sep=';', index=False, encoding='utf-8-sig')
    else:
        df.to_excel(caminho_saida, index=False)

    print("\n========================================")
    print("ARQUIVO SALVO")
    print("========================================")
    print(caminho_saida)

    caminho_backup = os.path.join('backup', nome_arquivo)
    if os.path.exists(caminho_backup):
        caminho_backup = os.path.join('backup', f"{int(time.time())}_{nome_arquivo}")
    shutil.move(caminho_entrada, caminho_backup)
    print(f"\nArquivo original movido para backup: {caminho_backup}")


def processar_sistema_pastas():
    for pasta in ['entrada', 'backup', 'resultados']:
        if not os.path.exists(pasta):
            os.makedirs(pasta)

    arquivos = [
        f for f in os.listdir('entrada')
        if f.lower().endswith(('.csv', '.xlsx', '.xls'))
    ]

    if not arquivos:
        print("\nNenhum arquivo encontrado.")
        print("Coloque um CSV ou XLSX na pasta 'entrada'.")
        return

    if os.path.exists(CACHE_FILE):
        print("\n[✓] Cache encontrado.")
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
    else:
        cache = {}

    geolocator = Nominatim(user_agent="geo_automacao_nittrans")
    reverse = RateLimiter(
        geolocator.reverse,
        min_delay_seconds=1.2,
        max_retries=5,
        error_wait_seconds=5,
        swallow_exceptions=True
    )

    for nome_arquivo in arquivos:
        _processar_arquivo(nome_arquivo, cache, reverse)

    _salvar_cache(cache)

    print("\n========================================")
    print("PROCESSO FINALIZADO COM SUCESSO")
    print("========================================")


if __name__ == "__main__":
    processar_sistema_pastas()
