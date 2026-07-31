import os
import re
import textwrap
import pdfplumber
import pandas as pd

# Configura o Matplotlib para NÃO usar o Tkinter (evita o erro 'main thread is not in main loop')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

def eh_linha_de_processo(linha, nome_celula):
    """Filtra cabeçalhos/rodapés da tabela, deixando passar só linhas de tipo de processo."""
    # Todo tipo de processo do SEI vem como "Categoria: Nome" (ex.: "Administrativo: Comunicado").
    # Cabeçalhos como 'Tipo' / 'Quantidade' não têm ':' e são descartados aqui
    # (o cabeçalho 'Tipo' vinha com o ano na coluna ao lado e virava uma barra falsa).
    if ':' not in nome_celula or len(nome_celula) < 4:
        return False

    if nome_celula.upper().startswith(('TOTAL', 'GERAL')):
        return False

    # Precisa ter algum número na linha, senão não é uma linha de contagem
    return any(str(item).replace('\n', '').strip().isdigit() for item in linha if item)

def extrair_e_verificar_dados(caminho_arquivo):
    unidade = "Unidade Não Identificada"

    processos = {
        'Administrativo: Auto de Infração': 0,
        'Administrativo: Defesa Prévia': 0,
        'Administrativo: Troca de Real Infrator': 0,
        'Administrativo: Recursos': 0,
        'Financeiro: Cancelamento de Lançamentos': 0,
        'Administrativo: Requerimento Geral/Envio de Expedientes Diversos': 0
    }

    # Tipos de processo que aparecem no PDF mas não estão na lista acima
    processos_extras = {}

    doc_auto_sei = 0
    doc_decreto_sei = 0
    total_processos_gerados = 0

    texto_completo = ""
    with pdfplumber.open(caminho_arquivo) as pdf:
        for page in pdf.pages:
            try:
                texto_completo += page.extract_text() + "\n"
            except:
                pass
            
    match_unidade = re.search(r'no per[ií]odo\s*\((.*?)\)', texto_completo, re.IGNORECASE)
    if match_unidade:
        unidade_bruta = match_unidade.group(1).strip()
        unidade = re.split(r'\s*/\s*NITEROI', unidade_bruta, flags=re.IGNORECASE)[0].strip()

    todas_as_tabelas = []
    with pdfplumber.open(caminho_arquivo) as pdf:
        for page in pdf.pages:
            tabelas = page.extract_tables()
            if tabelas:
                todas_as_tabelas.extend(tabelas)

    tabela_processos_lida = False
    tabela_documentos_lida = False

    for tabela in todas_as_tabelas:
        tabela_flat = " ".join([str(item) for row in tabela for item in row if item])
        
        if 'Administrativo:' in tabela_flat and not tabela_processos_lida:
            tabela_processos_lida = True
            
            for row in tabela:
                if not row or row[0] is None: continue
                
                nome_celula = str(row[0]).replace('\n', ' ').strip()
                nome_celula = re.sub(r'\s+', ' ', nome_celula) 
                
                def pegar_valor(linha):
                    for item in reversed(linha):
                        if item:
                            txt = str(item).replace('\n', '').strip()
                            if txt.isdigit():
                                return int(txt)
                    return 0

                if 'TOTAL:' in nome_celula.upper():
                    total_processos_gerados = pegar_valor(row)
                else:
                    chave_encontrada = None
                    for chave in processos.keys():
                        if chave in nome_celula:
                            chave_encontrada = chave
                            break

                    if chave_encontrada:
                        processos[chave_encontrada] = pegar_valor(row)
                    elif eh_linha_de_processo(row, nome_celula):
                        # Tipo não previsto no mapeamento: guarda o nome real vindo do PDF
                        processos_extras[nome_celula] = processos_extras.get(nome_celula, 0) + pegar_valor(row)


        elif 'Auto de Infração' in tabela_flat and 'Administrativo:' not in tabela_flat and not tabela_documentos_lida:
            tabela_documentos_lida = True
            
            for row in tabela:
                if not row or row[0] is None: continue
                
                nome_celula = str(row[0]).replace('\n', ' ').strip()
                nome_celula = re.sub(r'\s+', ' ', nome_celula)
                
                def pegar_valor(linha):
                    for item in reversed(linha):
                        if item:
                            txt = str(item).replace('\n', '').strip()
                            if txt.isdigit():
                                return int(txt)
                    return 0

                if 'Auto de Infração' in nome_celula:
                    doc_auto_sei = pegar_valor(row)
                elif 'Decreto' in nome_celula:
                    doc_decreto_sei = pegar_valor(row)

    return processos, processos_extras, unidade, doc_auto_sei, doc_decreto_sei, total_processos_gerados

def rodar_sei_estatisticas():
    pasta_entrada = "entrada"
    pasta_resultados = "resultados"
    
    os.makedirs(pasta_entrada, exist_ok=True)
    os.makedirs(pasta_resultados, exist_ok=True)
    
    arquivos = [f for f in os.listdir(pasta_entrada) if f.endswith(".pdf")]
    
    if not arquivos:
        raise FileNotFoundError(f"Coloque o arquivo PDF na pasta:\n{os.path.abspath(pasta_entrada)}")
    
    caminho_pdf = os.path.join(pasta_entrada, arquivos[0])
    
    # 1. Extração
    processos, processos_extras, unidade, doc_auto_sei, doc_decreto_sei, total_processos_gerados = extrair_e_verificar_dados(caminho_pdf)

    # 2. Preparar Dados
    soma_mapeados = sum(processos.values())
    soma_extras = sum(processos_extras.values())
    outros = max(0, total_processos_gerados - soma_mapeados - soma_extras)

    # Única unidade que usa a nomenclatura interna do mapeamento abaixo
    UNIDADE_CLASSIFICACAO_INTERNA = 'NIT/NITTRANS/DIVDOC'

    mapeamento_nomes = {
        'Administrativo: Defesa Prévia': 'Defesa Prévia',
        'Administrativo: Troca de Real Infrator': 'Trocar de Real Infrator',
        'Administrativo: Auto de Infração': 'Decreto N° 743/2026 Rotativo',
        'Administrativo: Recursos': 'Defesa 1° e 2° Instancia',
        'Financeiro: Cancelamento de Lançamentos': 'Formulário de Ajuste de Recurso',
        'Administrativo: Requerimento Geral/Envio de Expedientes Diversos': 'Auto de Infração'
    }

    # A classificação interna (os nomes traduzidos acima) só faz sentido no DIVDOC.
    # Nas demais divisões o gráfico sai com o nome original do tipo de processo no SEI.
    usar_classificacao_interna = unidade.strip().upper() == UNIDADE_CLASSIFICACAO_INTERNA

    categorias = []
    valores = []

    if usar_classificacao_interna:
        for chave_sei, nome_convertido in mapeamento_nomes.items():
            quantidade = processos[chave_sei]
            categorias.append(nome_convertido)
            valores.append(quantidade)

        qtd_mapeados = len(categorias)

        # Tipos não previstos entram com o nome real que veio do PDF (maior primeiro)
        for nome_original, quantidade in sorted(processos_extras.items(), key=lambda x: -x[1]):
            categorias.append(nome_original)
            valores.append(quantidade)
    else:
        # Sem as pré-definidas: todo tipo entra com o nome do SEI, do maior para o menor.
        # Tipos zerados são omitidos porque aqui a lista vem dos dados, não é fixa.
        todos_os_tipos = {**processos, **processos_extras}
        for nome_original, quantidade in sorted(todos_os_tipos.items(), key=lambda x: -x[1]):
            if quantidade > 0:
                categorias.append(nome_original)
                valores.append(quantidade)

        qtd_mapeados = len(categorias)

    categorias.append('Outros (Não Listados)')
    valores.append(outros)

    # Quebra rótulos longos em várias linhas para não estourar a margem esquerda
    rotulos = [textwrap.fill(c, 32) for c in categorias]

    # 3. Configurar a Interface Visual Matplotlib (Rodando em Background)
    # Altura cresce conforme a quantidade de barras (evita rótulos espremidos)
    altura_fig = max(7.5, 1.05 * len(categorias) + 2.0)
    fig, ax = plt.subplots(figsize=(12, altura_fig))
    fig.patch.set_facecolor('#f4f6f9')
    ax.set_facecolor('#ffffff')
    plt.subplots_adjust(left=0.32, bottom=0.22, top=0.85, right=0.92)

    # Azul para os tipos mapeados, laranja para os não previstos, cinza para o resíduo.
    # Fora do DIVDOC não há "não previsto": todos usam o nome do SEI, então tudo fica azul.
    qtd_extras = len(categorias) - qtd_mapeados - 1  # -1 = barra 'Outros (Não Listados)'
    cores = (['#2980b9'] * qtd_mapeados
             + ['#e67e22'] * qtd_extras
             + ['#95a5a6'])
    bars = ax.barh(rotulos, valores, color=cores, height=0.6)

    maior_valor = max(valores) if valores else 0
    afastamento = maior_valor * 0.01 + 0.05  # proporcional à escala, não fixo

    for bar in bars:
        ax.text(
            bar.get_width() + afastamento,
            bar.get_y() + bar.get_height()/2,
            str(int(bar.get_width())),
            va='center',
            fontsize=12,
            fontweight='bold',
            color='#2c3e50'
        )

    ax.set_title(f'Estatísticas da Unidade\n{unidade}', fontsize=16, pad=20, fontweight='bold', color='#2c3e50')
    ax.set_xlabel('Quantidade de Processos', fontsize=12, fontweight='bold', color='#34495e', labelpad=10)
    
    ax.invert_yaxis()
    if maior_valor > 0:
        ax.set_xlim(0, maior_valor + (maior_valor * 0.15 + 1))
        # Deixa o Matplotlib escolher no máximo ~10 marcas inteiras.
        # Fixar range(0, max+2) gerava centenas de ticks sobrepostos (eixo virava um borrão).
        ax.xaxis.set_major_locator(MaxNLocator(nbins=10, integer=True))

    ax.xaxis.grid(True, linestyle='--', alpha=0.6, color='#bdc3c7')
    ax.set_axisbelow(True) 
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#bdc3c7')
    ax.spines['bottom'].set_color('#bdc3c7')
    ax.tick_params(axis='both', labelsize=11, colors='#2c3e50')

    # 4. Salvar Gráfico como Imagem
    caminho_grafico = os.path.join(pasta_resultados, "Grafico_Estatisticas.png")
    plt.savefig(caminho_grafico, dpi=300, bbox_inches='tight')
    plt.close(fig) # Importante para liberar a memória já que não vamos mostrar a janela do plot!

    # 5. Salvar Excel com tratamento de erro (se o Excel estiver aberto)
    coluna_tipo = ('Tipo de Processo (Classificação Interna)' if usar_classificacao_interna
                   else 'Tipo de Processo (SEI)')
    df = pd.DataFrame({
        'Unidade': [unidade] * len(categorias),
        coluna_tipo: categorias,
        'Quantidade': valores
    })
    caminho_saida = os.path.join(pasta_resultados, "Relatorio_Consolidado.xlsx")
    
    try:
        df.to_excel(caminho_saida, index=False)
    except PermissionError:
        raise Exception("O arquivo Excel antigo está aberto! Feche-o e tente novamente.")

    # 6. Abre a imagem usando o programa de fotos padrão do Windows!
    try:
        os.startfile(caminho_grafico)
    except Exception as e:
        print(f"Não foi possível abrir a imagem automaticamente: {e}")