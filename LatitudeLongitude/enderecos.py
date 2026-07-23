import pandas as pd
import time
import os
import shutil
import json
import sys
import tkinter as tk
from tkinter import filedialog

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from tqdm import tqdm


CACHE_FILE = 'cache_enderecos.json'
INTERVALO_SAVE_CACHE = 10


def padronizar_coordenada(valor, tipo):
    """
    Extrai apenas os números e reconstrói forçando o formato exato 00.0000
    para contornar bugs de exportação do sistema.
    """
    val_str = str(valor)
    if val_str.lower() in ['nan', 'none', '', 'nat']:
        return None
    
    # Isola os números, descartando pontos e vírgulas ruins da planilha original
    digitos = ''.join([c for c in val_str if c.isdigit()])
    if not digitos:
        return None
        
    prefixo = "22" if tipo == "lat" else "43"
    
    if digitos.startswith(prefixo):
        resto = digitos[len(prefixo):]
    else:
        resto = digitos
        
    # Garante as 4 casas decimais exatas
    resto = resto.ljust(4, '0')
        
    try:
        return float(f"-{prefixo}.{resto}")
    except ValueError:
        return None


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


def _processar_arquivo(caminho_completo, cache, reverse):
    nome_arquivo = os.path.basename(caminho_completo)

    print("\n========================================")
    print(f"LENDO ARQUIVO: {nome_arquivo}")
    print("========================================")

    extensao = os.path.splitext(nome_arquivo)[1].lower()

    if extensao == '.csv':
        df = ler_csv_automatico(caminho_completo)
    elif extensao in ['.xlsx', '.xls']:
        df = pd.read_excel(caminho_completo)
        print("Excel carregado com sucesso.")
    else:
        print("Formato não suportado.")
        return None, nome_arquivo

    lat_col, lon_col = identificar_colunas(df)

    if not lat_col or not lon_col:
        print("\nNão foi possível identificar Latitude/Longitude.")
        return None, nome_arquivo

    print(f"Coordenadas identificadas - Latitude: {lat_col} | Longitude: {lon_col}")

    # Limpeza bruta e forçada para contornar a desformatação da base original
    df['lat_aux'] = df[lat_col].apply(lambda x: padronizar_coordenada(x, 'lat'))
    df['lon_aux'] = df[lon_col].apply(lambda x: padronizar_coordenada(x, 'lon'))

    coordenadas_invalidas = df[df['lat_aux'].isna() | df['lon_aux'].isna()]
    if len(coordenadas_invalidas) > 0:
        print(f"\nAviso: Foram encontradas {len(coordenadas_invalidas)} linhas com coordenadas inválidas ou em branco.")

    df_coords = df[['lat_aux', 'lon_aux']].reset_index(drop=True)

    print(f"Buscando endereços para {len(df_coords)} linhas...")

    ruas, bairros, numeros, cidades, ceps, estados = [], [], [], [], [], []
    nao_encontrados = []
    novos_no_cache = 0

    _sem_console = sys.stderr is None or sys.stdout is None
    for _, row in tqdm(df_coords.iterrows(), total=len(df_coords), disable=_sem_console):
        lat = row['lat_aux']
        lon = row['lon_aux']

        if pd.isna(lat) or pd.isna(lon):
            ruas.append(''); bairros.append(''); numeros.append('')
            cidades.append(''); ceps.append(''); estados.append('')
            continue

        # Mantém a chave de pesquisa perfeita
        lat_round = round(lat, 4)
        lon_round = round(lon, 4)
        chave = f"{lat_round:.4f},{lon_round:.4f}"

        if chave in cache:
            resultado = cache[chave]
        else:
            resultado = {'rua': '', 'bairro': '', 'numero': '', 'cidade': '', 'cep': '', 'estado': ''}
            try:
                location = reverse((lat_round, lon_round), language='pt', timeout=30)
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
                print(f"\nErro coordenada: {lat_round:.4f}, {lon_round:.4f} — {erro}")

            cache[chave] = resultado
            novos_no_cache += 1
            if novos_no_cache % INTERVALO_SAVE_CACHE == 0:
                _salvar_cache(cache)

        if not str(resultado['rua']).strip() and not str(resultado['bairro']).strip():
            nao_encontrados.append(f"Arquivo: {nome_arquivo} | Latitude: {lat_round:.4f} | Longitude: {lon_round:.4f}")

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

    # A FORMATAÇÃO: Força estritamente string com ponto e 4 casas
    df['Latitude_Formatada'] = df['lat_aux'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "")
    df['Longitude_Formatada'] = df['lon_aux'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "")
    
    df['Endereco_Rua'] = ruas
    df['Bairro'] = bairros
    df['Numero_Imovel'] = numeros
    df['Cidade'] = cidades
    df['CEP'] = ceps
    df['Estado'] = estados
    
    df = df.drop(columns=['lat_aux', 'lon_aux'])
    
    # Copia o arquivo original para a pasta backup
    caminho_backup = os.path.join('backup', nome_arquivo)
    if os.path.exists(caminho_backup):
        caminho_backup = os.path.join('backup', f"{int(time.time())}_{nome_arquivo}")
    shutil.copy2(caminho_completo, caminho_backup)

    return df, nome_arquivo


def processar_sistema_pastas():
    # Cria apenas as pastas de saída e backup
    for pasta in ['backup', 'resultados']:
        if not os.path.exists(pasta):
            os.makedirs(pasta)

    extensoes_validas = ('.csv', '.xlsx', '.xls')
    pasta_entrada = 'entrada'

    # Se o Hub já copiou arquivo(s) para a pasta "entrada" (fluxo normal via
    # interface.py), usa esses arquivos diretamente e NÃO abre janela nenhuma
    # aqui — quem já pediu a seleção (múltipla) foi o próprio Hub.
    arquivos_selecionados = []
    if os.path.exists(pasta_entrada):
        arquivos_selecionados = [
            os.path.join(pasta_entrada, f)
            for f in sorted(os.listdir(pasta_entrada))
            if f.lower().endswith(extensoes_validas)
        ]

    if not arquivos_selecionados:
        # Modo standalone: script rodado sozinho (fora do Hub), sem pasta
        # "entrada" com arquivos. Aí sim abre a janela de seleção própria,
        # permitindo escolher um ou vários arquivos de uma vez.
        root = tk.Tk()
        root.withdraw()  # Oculta a janela principal do tkinter
        root.attributes('-topmost', True)  # Garante que o diálogo apareça na frente
        root.update()

        arquivos_selecionados = filedialog.askopenfilenames(
            parent=root,
            title="Selecione a(s) planilha(s) para processar (1 ou mais)",
            filetypes=[("Arquivos suportados", "*.csv *.xlsx *.xls"), ("Todos os arquivos", "*.*")]
        )

        root.destroy()  # Fecha e libera a janela tkinter corretamente

    if not arquivos_selecionados:
        print("\nNenhum arquivo foi selecionado. Encerrando o programa.")
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

    dfs_processados = []

    # Processa os arquivos selecionados
    for caminho_arquivo in arquivos_selecionados:
        df_processado, nome_arquivo = _processar_arquivo(caminho_arquivo, cache, reverse)
        if df_processado is not None:
            dfs_processados.append((df_processado, nome_arquivo))

    _salvar_cache(cache)

    # Verifica quantos arquivos tiveram sucesso para decidir como salvar
    if len(dfs_processados) == 1:
        print("\n========================================")
        print("SALVANDO ARQUIVO ÚNICO...")
        print("========================================")
        
        df_final = dfs_processados[0][0]
        nome_original = dfs_processados[0][1]
        nome_base, _ = os.path.splitext(nome_original)
        caminho_saida = os.path.join('resultados', f"{nome_base}_corrigido.xlsx")
        
    elif len(dfs_processados) > 1:
        print("\n========================================")
        print("CONSOLIDANDO ARQUIVOS...")
        print("========================================")
        
        # Junta todas as planilhas lidas em uma só
        apenas_dfs = [item[0] for item in dfs_processados]
        df_final = pd.concat(apenas_dfs, ignore_index=True)
        caminho_saida = os.path.join('resultados', 'planilha_consolidada_corrigida.xlsx')
        
    else:
        print("\nNenhum arquivo válido foi processado.")
        return

    # Tenta salvar o resultado final (seja único ou consolidado)
    try:
        df_final.to_excel(caminho_saida, index=False)
        print(f"[✓] Processamento concluído. Salvo em:")
        print(f"-> {caminho_saida}")
        print("========================================")
        print("PROCESSO FINALIZADO COM SUCESSO")
        
    except PermissionError:
        print("\n❌ ERRO DE PERMISSÃO")
        print(f"O arquivo '{caminho_saida}' está aberto no Excel.")
        print("Feche o arquivo e rode o código novamente para salvar.")


if __name__ == "__main__":
    processar_sistema_pastas()