import pdfplumber
import pandas as pd
import re
import shutil
from pathlib import Path

# ==========================================
# 1. Configuração dos Diretórios
# ==========================================
PASTA_ENTRADA = Path("entrada")
PASTA_BACKUP = Path("backup")
PASTA_RESULTADOS = Path("resultados")

# Vai no fim do nome da planilha, depois do nome do PDF de origem.
SUFIXO_SAIDA = "_Extraido"

COLUNAS_SAIDA = ['Arquivo', 'Página', 'CPF/CNPJ', 'Proprietário', 'Placa',
                 'Processo', 'Data de Abertura', 'Data Resultado', 'Resultado',
                 'Relator']

# As pastas são criadas dentro de rodar_automacao(), NÃO aqui.
# Criá-las na importação do módulo as fazia nascer no diretório do
# executável (que é o diretório atual naquele momento) em vez da pasta da
# ferramenta. Depois, ao rodar, o backup/ e o resultados/ certos não
# existiam e o shutil.move falhava com "[WinError 3] O sistema não pode
# encontrar o caminho especificado".

# ==========================================
# Regex usados em vários lugares (compilados 1x)
# ==========================================
RE_PLACA = re.compile(r'\b[A-Z]{3}[0-9][A-Z0-9][0-9]{2}\b')
RE_DATA = re.compile(r'\b\d{2}/\d{2}/\d{4}\b')
RE_RESULTADO = re.compile(r'\b(Deferido|Indeferido)\b', re.IGNORECASE)
RE_CPF = re.compile(r'\d{3}\.\d{3}\.\d{3}-\d{2}')
RE_CNPJ = re.compile(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}')
# CNPJ pode quebrar a linha em dois lugares:
#   '30.069.314/0001-' no fim da linha + '01' na linha seguinte, OU
#   '21.314.559/0001-RELATOR...' (CNPJ truncado seguido de outro texto)
#                    + '66' em linha solta abaixo
# A regex casa as duas formas (sem o '$').
RE_CNPJ_PARCIAL = re.compile(r'(\d{2}\.\d{3}\.\d{3}/\d{4})-')
RE_RELATOR = re.compile(r'RELATOR\s*:\s*(.*?)(?=\s*INFRA[CÇ][AÃ]O\s*:|$)', re.IGNORECASE)
RE_INFRACAO = re.compile(r'INFRA[CÇ][AÃ]O\s*:\s*(.*)', re.IGNORECASE)

# Linhas de cabeçalho/rodapé que devem ser totalmente ignoradas
RE_RUIDO_LINHA = re.compile(
    r'EMISS[AÃ]O\s*:|SISTEMA DE MONITORAMENTO|AUTOS JULGADOS|'
    r'ORDEM\s*:|P[áa]gina\s*:|CPF/CNPJ\s+PROPRIET|NITEROI\s*-\s*PMNIT|'
    r'http://gaide|^\s*Page\s+\d+\s+of|TOTAL DE PROCESSOS|TOTAL GERAL|'
    r'USU[ÁA]RIO\s*:|ORG[ÃA]O LOTA|DETRAN',
    re.IGNORECASE
)


# ==========================================
# 2. Normalização
# ==========================================
def normalizar_nome(nome):
    if not nome:
        return ''
    nome = nome.upper().strip()
    nome = re.sub(r'\s+', ' ', nome)
    return nome


# ==========================================
# 3. Pré-processamento: achatar e juntar linhas-continuação
# ==========================================
def coletar_linhas_uteis(pdf):
    """
    Lê o PDF inteiro, descarta cabeçalhos/rodapés e devolve uma lista de
    (num_pagina, linha) — sem layout=True, pois isso embaralhava o texto.
    """
    linhas = []
    for num_pagina, pagina in enumerate(pdf.pages, start=1):
        texto = pagina.extract_text()
        if not texto:
            continue
        for linha in texto.split('\n'):
            if not linha.strip():
                continue
            if RE_RUIDO_LINHA.search(linha):
                continue
            # cabeçalho de bloco USERNAME — também não interessa pra extração de dados
            if re.search(r'^\s*USERNAME\s*:', linha, re.IGNORECASE):
                continue
            linhas.append((num_pagina, linha))
    return linhas


def juntar_cnpj_quebrado(linhas):
    """
    O PDF imprime CNPJs como '30.069.314/0001-' + '01' em linhas separadas.
    Dois padrões aparecem:
      a) '...0001-'                              (no fim da linha)
         '01 ...resto...'                        (próxima linha começa com 2 dígitos)
      b) '21.314.559/0001-RELATOR : ...'         (CNPJ no MEIO, sem sufixo)
         '66'                                    (próxima linha solta com 2 dígitos)
    Em ambos os casos, o sufixo de 2 dígitos pode estar até 3 linhas adiante
    porque o PDF intercala texto da coluna INFRAÇÃO.
    """
    resultado = list(linhas)
    i = 0
    while i < len(resultado):
        pag, linha = resultado[i]
        m = RE_CNPJ_PARCIAL.search(linha)
        if m:
            base = m.group(1)        # ex: '21.314.559/0001'
            inicio_m, fim_m = m.span()  # posição de '...0001-' na linha
            for offset in range(1, 4):
                if i + offset >= len(resultado):
                    break
                prox_pag, prox = resultado[i + offset]
                m2 = re.match(r'^\s*(\d{2})\b\s*(.*)', prox)
                if m2:
                    final_cnpj, resto = m2.groups()
                    # injeta o sufixo dentro da linha original (preservando o que vem depois)
                    nova_linha = linha[:fim_m] + final_cnpj + linha[fim_m:]
                    resultado[i] = (pag, nova_linha)
                    # a linha que tinha só o sufixo perde os 2 dígitos iniciais
                    resultado[i + offset] = (prox_pag, resto.strip())
                    break
        i += 1
    # remove linhas que ficaram vazias
    resultado = [(p, l) for p, l in resultado if l.strip()]
    return resultado


# Sobrenomes conhecidos que costumam quebrar para a próxima linha após
# "RELATOR : ...". Aumente esta lista conforme aparecerem outros casos.
SOBRENOMES_QUE_QUEBRAM = {'MUCHADJI'}


def juntar_placa_isolada(linhas):
    """
    Caso patológico (raro): a linha "NOME + DATAS + RESULTADO" vem solta,
    e a placa fica isolada na linha de baixo. Quando isso acontece, fundimos
    as duas, inserindo a placa logo após o nome.
        'WASHINGTON LUIZ TEIXEIRA NETTO 29/07/2025 15/01/2026 Indeferido'
        'PVX1G58'
                 ↓
        'WASHINGTON LUIZ TEIXEIRA NETTO PVX1G58 29/07/2025 15/01/2026 Indeferido'
    """
    resultado = []
    i = 0
    while i < len(linhas):
        pag, linha = linhas[i]
        # linha que parece placa solta?
        strip = linha.strip()
        if (re.fullmatch(r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}', strip)
                and resultado
                and RE_DATA.search(resultado[-1][1])
                and not RE_PLACA.search(resultado[-1][1])
                and RE_RESULTADO.search(resultado[-1][1])):
            # funde: insere placa antes da primeira data
            ant_pag, ant_linha = resultado[-1]
            m_data = RE_DATA.search(ant_linha)
            nova = ant_linha[:m_data.start()].rstrip() + ' ' + strip + ' ' + ant_linha[m_data.start():]
            resultado[-1] = (ant_pag, nova)
            i += 1
            continue
        resultado.append((pag, linha))
        i += 1
    return resultado


def juntar_continuacao_relator(linhas):
    """
    Caso clássico no PDF do DETRAN:
        'RELATOR : SAMANTHA CYNTHIA M. P. DE A. LIXA'   (linha N)
        'MUCHADJI'                                       (linha N+1, sozinha)
    Em vez de tentar adivinhar pelo formato (o que fundia demais com
    texto de infração à direita), juntamos APENAS quando a próxima linha
    é exatamente um dos sobrenomes conhecidos. É restritivo de propósito.
    """
    resultado = []
    i = 0
    while i < len(linhas):
        pag, linha = linhas[i]
        if (re.search(r'RELATOR\s*:', linha, re.IGNORECASE)
                and i + 1 < len(linhas)):
            _, prox = linhas[i + 1]
            prox_strip = prox.strip()
            if prox_strip.upper() in SOBRENOMES_QUE_QUEBRAM:
                linha = linha.rstrip() + ' ' + prox_strip
                resultado.append((pag, linha))
                i += 2
                continue
        resultado.append((pag, linha))
        i += 1
    return resultado


# ==========================================
# 4. Detectar onde começa um novo registro
# ==========================================
def eh_inicio_registro(linha):
    """
    Um novo registro começa numa linha que contém uma PLACA.
    Mas atenção: a linha pode ter só o nome do proprietário (se o PDF
    quebrou nome+placa em duas linhas). Tratamos isso no loop principal.
    """
    return bool(RE_PLACA.search(linha))


# ==========================================
# 5. Extrair dados de um bloco de linhas que pertence a um registro
# ==========================================
def extrair_dado(bloco_linhas, nome_arquivo):
    """
    bloco_linhas: lista de (pagina, linha) — todas as linhas do registro
    """
    texto_completo = ' '.join(linha for _, linha in bloco_linhas)
    primeira_pagina = bloco_linhas[0][0]

    dado = {
        'Arquivo': nome_arquivo,
        'Página': primeira_pagina,
        'CPF/CNPJ': 'N/A',
        'Proprietário': 'N/A',
        'Placa': 'N/A',
        'Processo': 'N/A',
        'Data de Abertura': 'N/A',
        'Data Resultado': 'N/A',
        'Resultado': 'N/A',
        'Relator': 'N/A',
    }

    # ---------- CPF / CNPJ ----------
    m_cnpj = RE_CNPJ.search(texto_completo)
    m_cpf = RE_CPF.search(texto_completo)
    if m_cnpj:
        dado['CPF/CNPJ'] = m_cnpj.group(0)
    elif m_cpf:
        dado['CPF/CNPJ'] = m_cpf.group(0)

    # ---------- A linha da PLACA é a "linha mestra" do registro ----------
    linha_placa = None
    for _, linha in bloco_linhas:
        if RE_PLACA.search(linha):
            linha_placa = linha
            break
    if not linha_placa:
        return None  # registro sem placa não é um registro válido

    m_placa = RE_PLACA.search(linha_placa)
    dado['Placa'] = m_placa.group(0)

    # ---------- Proprietário: o que vem ANTES da placa, na linha da placa ----------
    pre_placa = linha_placa[:m_placa.start()].strip()
    # tira CPF/CNPJ caso tenha vindo grudado
    pre_placa = RE_CPF.sub('', pre_placa)
    pre_placa = RE_CNPJ.sub('', pre_placa)
    pre_placa = re.sub(r'(?i)USERNAME:\s*\w*', '', pre_placa)
    pre_placa = re.sub(r'\s+', ' ', pre_placa).strip()
    if pre_placa:
        dado['Proprietário'] = pre_placa

    # ---------- Datas e Resultado: na linha da placa ----------
    datas = RE_DATA.findall(linha_placa)
    if len(datas) >= 1:
        dado['Data de Abertura'] = datas[0]
    if len(datas) >= 2:
        dado['Data Resultado'] = datas[1]

    m_res = RE_RESULTADO.search(linha_placa)
    if m_res:
        dado['Resultado'] = m_res.group(0).capitalize()

    # ---------- Relator ----------
    # IMPORTANTE: buscar linha-a-linha (não no texto concatenado), porque
    # pdfplumber empilha o texto da coluna 'INFRAÇÃO' depois da linha do
    # relator, e isso faria o regex engolir a infração inteira.
    for _, linha in bloco_linhas:
        m_rel = RE_RELATOR.search(linha)
        if m_rel:
            relator = m_rel.group(1)
            # corta em qualquer próximo marcador que tenha vazado na mesma linha
            relator = re.split(
                r'\b(?:RELATOR|INFRA[CÇ][AÃ]O|CPF|CNPJ)\b', 
                relator, maxsplit=1, flags=re.IGNORECASE
            )[0]
            # remove tudo que não for letra/acentos/ponto/espaço
            relator = re.sub(r'[^A-Za-zÀ-ÖØ-öø-ÿ\.\s]', '', relator)
            relator = re.sub(r'\s+', ' ', relator).strip()
            if relator:
                dado['Relator'] = relator
            break  # primeiro relator do bloco já basta

    # ---------- Infração / Processo ----------
    # Também linha-a-linha. A infração pode quebrar em 2-3 linhas no PDF
    # (ex: "INFRAÇÃO : 55412 - ESTACIONAR EM..." / "ESTACIONAMENT").
    # Estratégia: ao encontrar uma linha com "INFRAÇÃO :", capturar o texto
    # daquela linha e continuar concatenando linhas seguintes que pareçam
    # continuação (texto contínuo sem placas/CPF/datas/RELATOR/INFRAÇÃO),
    # até o fim do bloco.
    for k, (_, linha) in enumerate(bloco_linhas):
        m_inf = RE_INFRACAO.search(linha)
        if m_inf:
            processo = m_inf.group(1).strip()
            # tenta puxar continuações
            for _, prox in bloco_linhas[k + 1:]:
                prox_strip = prox.strip()
                if not prox_strip:
                    continue
                if (RE_PLACA.search(prox_strip) or RE_CPF.search(prox_strip)
                        or RE_CNPJ.search(prox_strip) or RE_DATA.search(prox_strip)
                        or re.search(r'\b(RELATOR|INFRA[CÇ][AÃ]O)\b', prox_strip, re.IGNORECASE)):
                    break
                processo += ' ' + prox_strip
            # limpezas
            processo = re.split(r'\bRELATOR\s*:', processo, flags=re.IGNORECASE)[0]
            processo = RE_DATA.sub('', processo)
            processo = RE_RESULTADO.sub('', processo)
            processo = RE_PLACA.sub('', processo)
            # remove sobrenomes de relator que possam ter vazado no fim
            for sobrenome in SOBRENOMES_QUE_QUEBRAM:
                processo = re.sub(r'\b' + sobrenome + r'\b', '', processo, flags=re.IGNORECASE)
            processo = re.sub(r'^(\d+)\s*-\s*', r'\1 - ', processo)
            processo = re.sub(r'\s+', ' ', processo).strip()
            if processo:
                dado['Processo'] = processo
            break

    return dado


# ==========================================
# 6. Função principal de extração
# ==========================================
def extrair_dados_pdf(caminho_pdf):
    nome_arquivo = Path(caminho_pdf).name
    dados = []

    with pdfplumber.open(caminho_pdf) as pdf:
        linhas = coletar_linhas_uteis(pdf)
        linhas = juntar_cnpj_quebrado(linhas)
        linhas = juntar_placa_isolada(linhas)
        linhas = juntar_continuacao_relator(linhas)

        # Particionar em blocos: cada registro vai da linha da PLACA atual
        # ATÉ antes da próxima linha de PLACA. O CPF, RELATOR e INFRAÇÃO
        # SEMPRE vêm DEPOIS da linha da placa do registro
        # NÃO incluímos linhas anteriores à placa no
        # bloco — elas pertencem ao registro anterior.
        indices_placa = [i for i, (_, l) in enumerate(linhas) if RE_PLACA.search(l)]

        for k, idx in enumerate(indices_placa):
            inicio = idx  # começa NA linha da placa, não antes
            fim = indices_placa[k + 1] if k + 1 < len(indices_placa) else len(linhas)
            bloco = linhas[inicio:fim]

            # Caso especial: a linha da placa não tem o nome do proprietário
            # (raro — ocorre quando o nome ficou numa linha acima, isolada,
            # ou quando há quebra de página entre nome e placa).
            pag_placa, linha_placa = linhas[idx]
            m_placa = RE_PLACA.search(linha_placa)
            pre = linha_placa[:m_placa.start()].strip()
            pre = RE_CPF.sub('', pre)
            pre = RE_CNPJ.sub('', pre)
            pre = re.sub(r'\s+', ' ', pre).strip()

            if not pre:
                # procurar nome em até 2 linhas acima (não no bloco — porque
                # essas linhas não estão no bloco), só pra extração não falhar
                for offset in range(1, 3):
                    j = idx - offset
                    if j < 0:
                        break
                    _, candidata = linhas[j]
                    cand = candidata.strip()
                    if (cand
                            and not RE_PLACA.search(cand)
                            and not RE_DATA.search(cand)
                            and not RE_CPF.search(cand)
                            and not RE_CNPJ.search(cand)
                            and 'RELATOR' not in cand.upper()
                            and 'INFRA' not in cand.upper()
                            and re.fullmatch(r'[A-ZÀ-Ÿ\.\s]+', cand)
                            and len(cand) >= 5):
                        # injeta o nome na linha da placa (cópia do bloco)
                        nova = cand + ' ' + linha_placa
                        bloco = [(pag_placa, nova)] + list(bloco[1:])
                        break

            dado = extrair_dado(bloco, nome_arquivo)
            if dado is not None:
                dados.append(dado)

    return dados


# ==========================================
# 7. Herdar CPF/CNPJ apenas quando o mesmo proprietário aparece em sequência
# ==========================================
def validar_cpfs(dados):
    ultimo_proprietario = None
    ultimo_cpf = None
    for dado in dados:
        proprietario_atual = normalizar_nome(dado.get('Proprietário', ''))
        cpf_atual = dado.get('CPF/CNPJ', 'N/A')
        if cpf_atual != 'N/A':
            ultimo_proprietario = proprietario_atual
            ultimo_cpf = cpf_atual
        else:
            if proprietario_atual and proprietario_atual == ultimo_proprietario and ultimo_cpf:
                dado['CPF/CNPJ'] = ultimo_cpf
    return dados


# ==========================================
# 8. Nome da planilha e relatório de conferência
# ==========================================
def _caminho_livre(caminho):
    """
    Nunca sobrescreve uma planilha já existente: se o nome estiver ocupado,
    acrescenta ' (2)', ' (3)'... como o Windows faz. Assim, reprocessar o
    mesmo PDF preserva o resultado anterior para comparação.
    """
    if not caminho.exists():
        return caminho
    contador = 2
    while True:
        candidato = caminho.with_name(
            f'{caminho.stem} ({contador}){caminho.suffix}'
        )
        if not candidato.exists():
            return candidato
        contador += 1


def _relatar_ausentes(dados):
    """Lista os campos que ficaram como N/A, para conferência manual."""
    faltantes = [
        (d, [k for k, v in d.items() if v == 'N/A']) for d in dados
    ]
    faltantes = [(d, f) for d, f in faltantes if f]
    if not faltantes:
        return
    print(f"  Campos ausentes em {len(faltantes)} de {len(dados)} registros:")
    for d, faltando in faltantes:
        print(f"    pág {d['Página']:>3} | placa {d['Placa']}"
              f" | faltou: {', '.join(faltando)}")


# ==========================================
# 9. Função principal
# ==========================================
def rodar_automacao():
    for pasta in [PASTA_ENTRADA, PASTA_BACKUP, PASTA_RESULTADOS]:
        pasta.mkdir(exist_ok=True)

    arquivos_pdf = list(PASTA_ENTRADA.glob("*.pdf"))
    if not arquivos_pdf:
        print(f"Nenhum PDF encontrado em '{PASTA_ENTRADA}'.")
        return

    # Cada PDF gera a sua própria planilha, com o nome do arquivo de origem
    # mais o sufixo. Nada é misturado entre arquivos.
    geradas = []
    vazios = []

    for numero, arquivo in enumerate(sorted(arquivos_pdf), start=1):
        print(f"\n[{numero}/{len(arquivos_pdf)}] A processar: {arquivo.name}")
        dados = extrair_dados_pdf(arquivo)

        # A herança de CPF/CNPJ é feita POR ARQUIVO: um proprietário repetido
        # só empresta o documento dele dentro do mesmo relatório.
        dados = validar_cpfs(dados)

        if dados:
            _relatar_ausentes(dados)

            df = pd.DataFrame(dados, columns=COLUNAS_SAIDA)
            caminho_saida = _caminho_livre(
                PASTA_RESULTADOS / f"{arquivo.stem}{SUFIXO_SAIDA}.xlsx"
            )
            df.to_excel(caminho_saida, index=False)
            geradas.append((caminho_saida, df))
            print(f"  {len(df)} registros -> {caminho_saida.name}")
        else:
            vazios.append(arquivo.name)
            print("  ATENÇÃO: nenhum registro extraído deste arquivo.")

        shutil.move(str(arquivo), str(PASTA_BACKUP / arquivo.name))

    if vazios:
        print("\n" + "=" * 60)
        print("ARQUIVOS SEM NENHUM REGISTRO (conferir)")
        print("=" * 60)
        for nome in vazios:
            print(f"  {nome}")
        print("Se o PDF tem dados, o layout dele não é o esperado por esta")
        print("ferramenta. Confira o relatório antes de considerar concluído.")
        print("=" * 60)

    if not geradas:
        print("\nNenhum dado válido encontrado.")
        return

    print("\n" + "=" * 60)
    print(f"Concluído! {len(geradas)} planilha(s) em {PASTA_RESULTADOS}:")
    for caminho, df in geradas:
        print(f"  {caminho.name}: {len(df)} registros")
    print(f"  TOTAL: {sum(len(df) for _, df in geradas)} registros")
    print("=" * 60)


if __name__ == "__main__":
    rodar_automacao()