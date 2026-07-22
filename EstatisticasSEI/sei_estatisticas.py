import os
import re
import pdfplumber
import pandas as pd

# Configura o Matplotlib para NÃO usar o Tkinter (evita o erro 'main thread is not in main loop')
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

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
                    for chave in processos.keys():
                        if chave in nome_celula:
                            processos[chave] = pegar_valor(row)
                            break
                            
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

    return processos, unidade, doc_auto_sei, doc_decreto_sei, total_processos_gerados

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
    processos, unidade, doc_auto_sei, doc_decreto_sei, total_processos_gerados = extrair_e_verificar_dados(caminho_pdf)

    # 2. Preparar Dados
    soma_mapeados = sum(processos.values())
    outros = max(0, total_processos_gerados - soma_mapeados)

    mapeamento_nomes = {
        'Administrativo: Defesa Prévia': 'Defesa Prévia',
        'Administrativo: Troca de Real Infrator': 'Trocar de Real Infrator',
        'Administrativo: Auto de Infração': 'Decreto N° 743/2026 Rotativo',
        'Administrativo: Recursos': 'Defesa 1° e 2° Instancia',
        'Financeiro: Cancelamento de Lançamentos': 'Formulário de Ajuste de Recurso',
        'Administrativo: Requerimento Geral/Envio de Expedientes Diversos': 'Auto de Infração'
    }

    categorias = []
    valores = []

    for chave_sei, nome_convertido in mapeamento_nomes.items():
        quantidade = processos[chave_sei]
        categorias.append(nome_convertido)
        valores.append(quantidade)

    categorias.append('Outros (Não Listados)')
    valores.append(outros)

    # 3. Configurar a Interface Visual Matplotlib (Rodando em Background)
    fig, ax = plt.subplots(figsize=(12, 7.5))
    fig.patch.set_facecolor('#f4f6f9') 
    ax.set_facecolor('#ffffff')        
    plt.subplots_adjust(left=0.32, bottom=0.22, top=0.85, right=0.92)

    cores = ['#2980b9'] * len(mapeamento_nomes) + ['#95a5a6'] 
    bars = ax.barh(categorias, valores, color=cores, height=0.6)

    for bar in bars:
        ax.text(
            bar.get_width() + 0.05, 
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
    if valores and max(valores) > 0:
        ax.set_xlim(0, max(valores) + (max(valores) * 0.15 + 1))
        ax.set_xticks(range(0, max(valores) + 2))

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
    df = pd.DataFrame({
        'Unidade': [unidade] * len(categorias), 
        'Tipo de Processo (Classificação Interna)': categorias,
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