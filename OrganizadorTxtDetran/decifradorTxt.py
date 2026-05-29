import os
import re
import shutil
import sys
import pandas as pd
from tqdm import tqdm

PASTA_ENTRADA = 'entrada'
PASTA_BACKUP = 'backup'
PASTA_SAIDA = 'resultados'


def formatar_data(d):
    if len(d) == 8 and d.isdigit():
        return f"{d[6:8]}/{d[4:6]}/{d[0:4]}"
    return d


def formatar_hora(h):
    if len(h) == 6 and h.isdigit():
        return f"{h[0:2]}:{h[2:4]}:{h[4:6]}"
    return h


def separar_logradouro(texto):
    texto = texto.strip()
    # Remove sufixos de posição do final: "OP.", "OP. OP.", "OPOSTO", "LADO OP."
    limpo = re.sub(r'[\s,]+(LADO\s+)?OP\.?(\s+OP\.?)*\s*$', '', texto, flags=re.IGNORECASE).strip()
    limpo = re.sub(r'\s+OPOSTO\s*$', '', limpo, flags=re.IGNORECASE).strip()
    # Faixa: "151 AO 251"
    m = re.match(r'^(.*?),?\s*(\d+\s+[Aa][Oo]\s+\d+)\s*$', limpo)
    if m:
        nome = re.sub(r'\s+N\.?\s*$', '', m.group(1).strip(), flags=re.IGNORECASE)
        return nome, m.group(2).strip()
    # Número simples com sufixo opcional: "123", "45A", "12-B"
    m = re.match(r'^(.*?),?\s*(\d+[\w-]*)\s*$', limpo)
    if m:
        nome = re.sub(r'\s+N\.?\s*$', '', m.group(1).strip(), flags=re.IGNORECASE)
        return nome, m.group(2).strip()
    return texto, ''


def formatar_valor(v):
    if v and v.isdigit():
        valor_float = int(v) / 100
        return f"R$ {valor_float:.2f}".replace('.', ',')
    return v


def ler_arquivo_txt(caminho):
    encodings = ['utf-8', 'latin1', 'cp1252']
    for enc in encodings:
        try:
            with open(caminho, 'r', encoding=enc) as f:
                linhas = f.readlines()
            print(f"Arquivo lido com encoding: {enc}")
            return linhas
        except UnicodeDecodeError:
            print(f"Falha ao ler com encoding: {enc}")
    raise Exception(f"Não foi possível ler o arquivo: {caminho}")


def processar_arquivos():
    for pasta in [PASTA_ENTRADA, PASTA_BACKUP, PASTA_SAIDA]:
        if not os.path.exists(pasta):
            os.makedirs(pasta)
            print(f"Pasta '{pasta}' criada.")

    arquivos_txt = [f for f in os.listdir(PASTA_ENTRADA) if f.endswith('.txt')]

    if not arquivos_txt:
        print(f"\nNenhum arquivo .txt encontrado em '{PASTA_ENTRADA}'.")
        return

    _sem_console = sys.stderr is None or sys.stdout is None
    for nome_arquivo in tqdm(arquivos_txt, desc="Processando arquivos", colour="green", disable=_sem_console):
        caminho_txt = os.path.join(PASTA_ENTRADA, nome_arquivo)
        nome_base = os.path.splitext(nome_arquivo)[0]
        caminho_excel = os.path.join(PASTA_SAIDA, f"{nome_base}_normalizado.xlsx")
        dados_normalizados = []

        try:
            linhas = ler_arquivo_txt(caminho_txt)

            for linha in tqdm(linhas, desc=f"Lendo {nome_arquivo}", leave=False, colour="cyan", disable=_sem_console):
                linha = linha.replace('\n', '')
                if not linha.strip():
                    continue

                registro = {
                    "Cód do Orgão Atuador":                 linha[0:6].strip(),
                    "Código da Infração":                   linha[6:9].strip(),
                    "DV Infração":                          linha[9:10].strip(),
                    "Desdobramento Infração":               linha[10:11].strip(),
                    "Descrição da Infração":                linha[11:71].strip(),
                    "Tipo de enquadramento":                linha[71:91].strip(),
                    "Auto":                                 linha[91:103].strip(),
                    "Data":                                 formatar_data(linha[103:111].strip()),
                    "Hora":                                 formatar_hora(linha[111:117].strip()),
                    "Cód Classe do Agente":                 linha[117:132].strip(),
                    "Data do Status":                       formatar_data(linha[132:140].strip()),
                    "Cód. do Status":                       linha[140:142].strip(),
                    "Data do Vencimento da Infração":       formatar_data(linha[142:150].strip()),
                    "Data do Pagamento da Infração":        formatar_data(linha[150:158].strip()),
                    "Valor da Infração":                    formatar_valor(linha[158:167].strip()),
                    "Situação":                             linha[167:174].strip(),
                    "Placa do Veículo Infrator":            linha[174:181].strip(),
                    "Renavam do Veículo":                   linha[181:192].strip(),
                    "Marca/Modelo do veículo":              linha[192:217].strip(),
                    "tipo de pessoa":                       linha[217:219].strip(),
                    "identidade":                           linha[219:233].strip(),
                    "nome":                                 linha[233:293].strip(),
                    "nome do logradouro do infrator":       linha[293:337].strip(),
                    "CEP":                                  linha[337:345].strip(),
                    "Cód. do Município":                    linha[345:348].strip(),
                    "Município":                            linha[348:388].strip(),
                    "Descrição do Município do Endereço":   linha[388:].strip(),
                    "Descrição do Município do Endereço (sem número)": separar_logradouro(linha[388:])[0],
                }
                dados_normalizados.append(registro)

            df = pd.DataFrame(dados_normalizados)
            df.to_excel(caminho_excel, index=False)
            print(f"\nSUCESSO: '{nome_arquivo}' convertido!")
            print(f"{len(df)} registros processados.")

            caminho_backup = os.path.join(PASTA_BACKUP, nome_arquivo)
            if os.path.exists(caminho_backup):
                os.remove(caminho_backup)
            shutil.move(caminho_txt, caminho_backup)
            print(f"Arquivo movido para '{PASTA_BACKUP}'.")

        except Exception as e:
            print(f"\nERRO ao processar '{nome_arquivo}'")
            print(f"Detalhes: {e}")

    print("\nFim da execução do robô.")


if __name__ == "__main__":
    processar_arquivos()
