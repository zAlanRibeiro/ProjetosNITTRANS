import pandas as pd
import os
import sys
import gc 

def obter_diretorio_base():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def caminho_livre(caminho):
    """
    Nunca sobrescreve um arquivo já existente: se o nome estiver ocupado,
    acrescenta ' (2)', ' (3)'... como o Windows faz. Assim uma mesclagem
    nova não apaga o consolidado anterior.
    """
    if not os.path.exists(caminho):
        return caminho
    raiz, ext = os.path.splitext(caminho)
    contador = 2
    while os.path.exists(f"{raiz} ({contador}){ext}"):
        contador += 1
    return f"{raiz} ({contador}){ext}"

def mesclar_arquivos_excel():
    base = obter_diretorio_base()
    pasta_entrada = os.path.join(base, "RemovedorDuplicadasDetran", "entrada")
    pasta_resultados = os.path.join(base, "RemovedorDuplicadasDetran", "resultados")
    
    os.makedirs(pasta_entrada, exist_ok=True)
    os.makedirs(pasta_resultados, exist_ok=True)
    
    arquivos = [os.path.join(pasta_entrada, f) for f in os.listdir(pasta_entrada) if f.endswith(('.xlsx', '.xls', '.csv'))]
    
    if not arquivos:
        raise FileNotFoundError("Nenhum arquivo encontrado na pasta de entrada.")

    # Cria uma base vazia para ir acumulando os dados
    df_consolidado = pd.DataFrame()
    
    for arquivo in arquivos:
        print(f"Lendo e cruzando arquivo: {os.path.basename(arquivo)}...")
        
        # 1. Lê apenas UM arquivo por vez
        if arquivo.endswith('.csv'):
            df_temp = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig', low_memory=False)
        else:
            df_temp = pd.read_excel(arquivo)
        
        # 2. Junta o arquivo novo com a base acumulada
        df_consolidado = pd.concat([df_consolidado, df_temp], ignore_index=True)
        
        # 3. MÁGICA: Remove as duplicadas que vieram entre os arquivos AGORA, aliviando a memória
        df_consolidado.drop_duplicates(inplace=True)
        
        # 4. Exclui o arquivo temporário lido da memória RAM à força
        del df_temp 
        gc.collect()

    if not df_consolidado.empty:
        print("Salvando arquivo final em formato CSV...")
        caminho_salvar = caminho_livre(
            os.path.join(pasta_resultados, "Estatisticas_Niteroi_Consolidado.csv")
        )
        df_consolidado.to_csv(caminho_salvar, index=False, sep=';', encoding='utf-8-sig') 
        print(f"Sucesso! Arquivo final salvo: {os.path.basename(caminho_salvar)}")
    else:
        raise ValueError("Nenhum dado válido para mesclar.")