import csv

def encontrar_linhas_quebradas(caminho_arquivo, separador=";"):
    print(f"Analisando o arquivo: {caminho_arquivo}\n")
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8-sig') as f:
            # Lê todas as linhas do arquivo de uma vez
            linhas = f.readlines()
            
        # O cabeçalho dita a regra matemática
        cabecalho = linhas[0].strip('\n').split(separador)
        qtd_esperada = len(cabecalho)
        
        print(f"📌 O cabeçalho exige exatamente {qtd_esperada} colunas (separadas por '{separador}').\n")
        
        erros_encontrados = 0
        
        # Verifica linha por linha
        for num_linha, texto_linha in enumerate(linhas[1:], start=2):
            # Limpa quebras de linha e divide a linha usando o ponto e vírgula
            colunas = texto_linha.strip('\n').split(separador)
            
            # Se a conta não fechar, achamos o erro!
            if len(colunas) != qtd_esperada:
                erros_encontrados += 1
                print(f"❌ ERRO NA LINHA {num_linha}:")
                print(f"   - O script encontrou {len(colunas)} colunas em vez de {qtd_esperada}.")
                print(f"   - Conteúdo: {texto_linha.strip()}")
                print("-" * 70)
                
        if erros_encontrados == 0:
            print("✅ Nenhuma linha quebrada encontrada! O arquivo está perfeito.")
        else:
            print(f"\n🚨 Total de linhas corrompidas: {erros_encontrados}")
            print("DICA: Abra o arquivo no Excel ou Bloco de Notas, vá nessas linhas e apague o ';' extra.")
            
    except Exception as e:
        print(f"Erro ao abrir o arquivo: {e}")

# Substitua pelo nome exato do CSV que você quer investigar
encontrar_linhas_quebradas("incidents-2026-06-01_01-00-01 (1).csv")