import pandas as pd
import time
import os
import shutil
import json
import sys
import tkinter as tk
from tkinter import filedialog

from geopy.exc import (
    GeocoderInsufficientPrivileges, GeocoderRateLimited, GeocoderTimedOut,
    GeocoderUnavailable,
)
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from tqdm import tqdm


CACHE_FILE = 'cache_enderecos.json'
INTERVALO_SAVE_CACHE = 10

# Esperas (em segundos) antes de repetir uma consulta que o servidor recusou
# ou deixou sem resposta. Esgotadas todas, a execução para de consultar.
ESPERAS_NOVA_TENTATIVA = (5, 15, 30)
ERROS_DO_SERVIDOR = (
    GeocoderRateLimited, GeocoderTimedOut, GeocoderUnavailable,
    GeocoderInsufficientPrivileges,
)
MOTIVO_SERVIDOR_INDISPONIVEL = (
    "OpenStreetMap recusando consultas — rode o arquivo novamente mais tarde"
)

# Faixas do território brasileiro, usadas para detectar colunas trocadas
FAIXA_LAT_BR = (-34.0, 6.0)
FAIXA_LON_BR = (-74.0, -33.0)


def _texto_para_float(val_str):
    """Converte o texto em número, aceitando vírgula como separador decimal."""
    val_str = val_str.replace(' ', '').replace('°', '')
    if ',' in val_str and '.' in val_str:
        # "1.234,56" -> ponto é separador de milhar
        val_str = val_str.replace('.', '').replace(',', '.')
    else:
        val_str = val_str.replace(',', '.')
    try:
        return float(val_str)
    except ValueError:
        return None


def _reinserir_ponto_decimal(val_str):
    """Recupera coordenadas exportadas sem o separador decimal.

    Alguns sistemas exportam "-22941649" no lugar de "-22.941649". Os dois
    primeiros dígitos viram os graus e o restante, as casas decimais.
    """
    digitos = ''.join(c for c in val_str if c.isdigit())
    if len(digitos) < 3:
        return None

    graus, decimais = digitos[:2], digitos[2:]
    try:
        numero = float(f"{graus}.{decimais}")
    except ValueError:
        return None

    # Coordenadas de Niterói são sempre sul/oeste, então o sinal é negativo
    # mesmo quando a exportação vem sem ele
    return -numero


def padronizar_coordenada(valor, tipo=None):
    """Converte o valor lido da planilha em coordenada decimal.

    O parâmetro `tipo` ('lat' ou 'lon') é usado só para validar a faixa —
    a conversão em si não presume onde a coordenada fica.
    """
    val_str = str(valor).strip()
    if val_str.lower() in ['nan', 'none', '', 'nat']:
        return None

    numero = _texto_para_float(val_str)

    # Fora de qualquer faixa possível: provavelmente perdeu o separador decimal
    if numero is None or abs(numero) > 180:
        numero = _reinserir_ponto_decimal(val_str)
        if numero is None:
            return None

    limite = 90 if tipo == 'lat' else 180
    if abs(numero) > limite:
        return None

    return numero


def _dentro(valor, faixa):
    return faixa[0] <= valor <= faixa[1]


def colunas_estao_invertidas(lats, lons):
    """Detecta, pelo conjunto do arquivo, se as duas colunas vieram trocadas.

    A decisão é tomada uma vez por arquivo, pela mediana de cada coluna, e não
    linha a linha — assim o arquivo inteiro sai coerente.
    """
    lats = sorted(v for v in lats if v is not None)
    lons = sorted(v for v in lons if v is not None)
    if not lats or not lons:
        return False

    mediana_lat = lats[len(lats) // 2]
    mediana_lon = lons[len(lons) // 2]

    parece_trocado = (
        not _dentro(mediana_lat, FAIXA_LAT_BR) and _dentro(mediana_lat, FAIXA_LON_BR)
        and not _dentro(mediana_lon, FAIXA_LON_BR) and _dentro(mediana_lon, FAIXA_LAT_BR)
    )
    return parece_trocado


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


def coluna_de_saida(df, nome):
    """Escolhe o nome da coluna de resultado sem sobrescrever o arquivo original.

    Se a planilha já traz uma coluna com esse nome (é comum ter "Bairro"), o
    dado do OpenStreetMap vai para uma coluna própria com o sufixo _OSM e as
    duas convivem no resultado. Não havendo conflito, mantém o nome de sempre.
    """
    return nome if nome not in df.columns else f"{nome}_OSM"


class ConsultaNominatim:
    """Consulta endereços no Nominatim respeitando o limite do servidor.

    Quando o servidor recusa (erro 429, bloqueio do IP) ou não responde, espera
    e repete a mesma consulta algumas vezes. Se continuar recusando, marca o
    servidor como indisponível e a execução segue sem consultar o restante.
    Antes, com 5 novas tentativas por coordenada, cada uma podia gastar quase
    um minuto: um arquivo de 200 linhas levava horas e as coordenadas saíam
    sem endereço do mesmo jeito.
    """

    def __init__(self):
        geolocator = Nominatim(user_agent="geo_automacao_nittrans", timeout=10)
        self._reverse = RateLimiter(
            geolocator.reverse,
            min_delay_seconds=1.2,
            max_retries=0,
            swallow_exceptions=False
        )
        self.servidor_indisponivel = False

    def buscar(self, lat, lon):
        """Devolve o resultado do geopy, ou None se não há endereço no ponto.

        Uma falha de consulta levanta a exceção do geopy, para que a coordenada
        não vá para o cache como se não tivesse endereço.
        """
        for espera in (*ESPERAS_NOVA_TENTATIVA, None):
            try:
                return self._reverse((lat, lon), language='pt')
            except ERROS_DO_SERVIDOR as erro:
                if espera is None:
                    self.servidor_indisponivel = True
                    raise
                print(f"\n[!] O OpenStreetMap recusou a consulta ({erro}). Nova tentativa em {espera}s...")
                time.sleep(espera)


def _salvar_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _processar_arquivo(caminho_completo, cache, consulta):
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

    df['lat_aux'] = df[lat_col].apply(lambda x: padronizar_coordenada(x, 'lat'))
    df['lon_aux'] = df[lon_col].apply(lambda x: padronizar_coordenada(x, 'lon'))

    # Arquivos exportados com as duas colunas trocadas são corrigidos aqui,
    # antes da consulta de endereços
    if colunas_estao_invertidas(df['lat_aux'], df['lon_aux']):
        print(
            f"\n[!] As colunas '{lat_col}' e '{lon_col}' vieram trocadas neste arquivo"
            " — os valores foram invertidos automaticamente."
        )
        df['lat_aux'], df['lon_aux'] = df['lon_aux'], df['lat_aux']

    coordenadas_invalidas = df[df['lat_aux'].isna() | df['lon_aux'].isna()]
    if len(coordenadas_invalidas) > 0:
        print(f"\nAviso: Foram encontradas {len(coordenadas_invalidas)} linhas com coordenadas inválidas ou em branco.")

    df_coords = df[['lat_aux', 'lon_aux']].reset_index(drop=True)

    print(f"Buscando endereços para {len(df_coords)} linhas...")

    ruas, bairros, numeros, cidades, ceps, estados = [], [], [], [], [], []
    nao_encontrados = []
    novos_no_cache = 0
    linhas_com_falha = 0

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

        motivo_falha = ''
        if chave in cache:
            resultado = cache[chave]
        else:
            resultado = {'rua': '', 'bairro': '', 'numero': '', 'cidade': '', 'cep': '', 'estado': ''}
            if consulta.servidor_indisponivel:
                motivo_falha = MOTIVO_SERVIDOR_INDISPONIVEL
            else:
                try:
                    location = consulta.buscar(lat_round, lon_round)
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
                    motivo_falha = (
                        MOTIVO_SERVIDOR_INDISPONIVEL if consulta.servidor_indisponivel
                        else f"erro na consulta ({erro})"
                    )

            # Falhas de consulta não entram no cache: gravadas como endereço
            # vazio, nunca mais seriam consultadas, nem depois que o servidor
            # voltasse a responder.
            if not motivo_falha:
                cache[chave] = resultado
                novos_no_cache += 1
                if novos_no_cache % INTERVALO_SAVE_CACHE == 0:
                    _salvar_cache(cache)

        if not str(resultado['rua']).strip() and not str(resultado['bairro']).strip():
            linha = f"Arquivo: {nome_arquivo} | Latitude: {lat_round:.4f} | Longitude: {lon_round:.4f}"
            if motivo_falha:
                linha += f" | Motivo: {motivo_falha}"
                linhas_com_falha += 1
            nao_encontrados.append(linha)

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

    if linhas_com_falha:
        print(
            f"\n[!] {linhas_com_falha} linha(s) ficaram sem endereço por falha na consulta"
            " e estão em resultados/coordenadas_nao_encontradas.txt. Rode o arquivo"
            " novamente mais tarde: o que já foi encontrado vem do cache e só essas"
            " coordenadas serão consultadas."
        )

    # A FORMATAÇÃO: Força estritamente string com ponto e 4 casas
    df['Latitude_Formatada'] = df['lat_aux'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "")
    df['Longitude_Formatada'] = df['lon_aux'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "")
    
    for nome, valores in [
        ('Endereco_Rua', ruas),
        ('Bairro', bairros),
        ('Numero_Imovel', numeros),
        ('Cidade', cidades),
        ('CEP', ceps),
        ('Estado', estados),
    ]:
        df[coluna_de_saida(df, nome)] = valores


    df = df.drop(columns=['lat_aux', 'lon_aux'])
    
    # Copia o arquivo original para a pasta backup
    caminho_backup = os.path.join('backup', nome_arquivo)
    if os.path.exists(caminho_backup):
        caminho_backup = os.path.join('backup', f"{int(time.time())}_{nome_arquivo}")
    shutil.copy2(caminho_completo, caminho_backup)

    return df, nome_arquivo


def processar_sistema_pastas(permitir_janela_propria=False):
    """
    permitir_janela_propria só é ligado quando o script roda sozinho, pelo
    __main__. Pelo Hub ele fica desligado de propósito: o Hub executa as
    ferramentas numa thread secundária, e criar um segundo tk.Tk() fora da
    thread principal pode congelar ou derrubar a janela do Hub.
    """
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

    if not arquivos_selecionados and not permitir_janela_propria:
        # Chamado pelo Hub: a seleção já foi feita lá. Se nada válido chegou
        # em "entrada", é erro de verdade — avisa em vez de abrir janela.
        raise FileNotFoundError(
            "Nenhuma planilha (.csv, .xlsx ou .xls) foi encontrada na pasta"
            " 'entrada'. Selecione o arquivo novamente."
        )

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
        # Versões anteriores gravavam falhas de consulta como endereço vazio.
        # Como não dá para diferenciá-las de um ponto realmente sem endereço,
        # toda entrada vazia é consultada de novo (uma vez por execução)
        cache = {chave: valor for chave, valor in cache.items() if any(valor.values())}
    else:
        cache = {}

    consulta = ConsultaNominatim()

    dfs_processados = []

    # Processa os arquivos selecionados
    for caminho_arquivo in arquivos_selecionados:
        df_processado, nome_arquivo = _processar_arquivo(caminho_arquivo, cache, consulta)
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
    # Rodando sozinho: aqui a thread é a principal, então a janela de
    # seleção própria é segura.
    processar_sistema_pastas(permitir_janela_propria=True)