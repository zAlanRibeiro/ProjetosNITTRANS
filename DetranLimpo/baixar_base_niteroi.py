# -*- coding: utf-8 -*-
import json
import requests
import unicodedata
from pathlib import Path

ARQUIVO_BASE = Path('ruas_oficiais_niteroi.json')

def baixar_todas_as_ruas():
    print("Conectando aos servidores do OpenStreetMap (Overpass API)...")
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    overpass_query = """
    [out:json][timeout:90];
    area["wikidata"="Q178725"]->.searchArea;
    (
      way["highway"]["name"](area.searchArea);
    );
    out tags;
    """
    
    # O "Crachá" de identificação para o servidor não bloquear o Python
    headers = {
        "User-Agent": "Sistema_NitTrans_Offline_Builder/1.0",
        "Accept": "application/json"
    }
    
    try:
        resposta = requests.post(
            overpass_url, 
            data={'data': overpass_query}, 
            headers=headers,
            timeout=100
        )
        resposta.raise_for_status()
        dados = resposta.json()
    except Exception as e:
        print(f"Erro na conexão: {e}")
        if 'resposta' in locals():
            print(f"Detalhe do servidor: {resposta.text}")
        return

    ruas_oficiais = set()
    
    print("Download concluído! Extraindo e organizando os nomes...")
    
    for elemento in dados.get('elements', []):
        tags = elemento.get('tags', {})
        nome_rua = tags.get('name')
        if nome_rua:
            ruas_oficiais.add(nome_rua)

    print(f"Total de ruas únicas encontradas em Niterói: {len(ruas_oficiais)}")

    dicionario_niteroi = {}
    for rua in sorted(ruas_oficiais):
        chave = unicodedata.normalize('NFKD', rua).encode('ascii', 'ignore').decode().upper()
        dicionario_niteroi[chave] = rua

    with open(ARQUIVO_BASE, 'w', encoding='utf-8') as f:
        json.dump(dicionario_niteroi, f, ensure_ascii=False, indent=2)

    print(f"\n✅ SUCESSO! Arquivo '{ARQUIVO_BASE.name}' gerado com perfeição.")
    print("O seu sistema agora tem a malha viária de Niterói 100% offline!")

if __name__ == "__main__":
    baixar_todas_as_ruas()