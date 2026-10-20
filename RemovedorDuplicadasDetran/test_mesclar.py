# Mescla dois arquivos que se sobrepõem, como os do Detran de meses seguidos.
# Rodar: python test_mesclar.py
import os
import tempfile

import openpyxl
import pandas as pd

import removerDuplicada

base = tempfile.mkdtemp()
entrada = os.path.join(base, "RemovedorDuplicadasDetran", "entrada")
os.makedirs(entrada)
removerDuplicada.obter_diretorio_base = lambda: base
removerDuplicada.LINHAS_POR_ABA = 2

julho = [{"Renavam": "00949484890", "identidade": "00301951799"},
         {"Renavam": "01143123456", "identidade": "30082312000155"}]
agosto = julho + [{"Renavam": "00956266061", "identidade": "03535814707"}]
pd.DataFrame(julho).to_excel(os.path.join(entrada, "julho.xlsx"), index=False)
pd.DataFrame(agosto).to_excel(os.path.join(entrada, "agosto.xlsx"), index=False)

removerDuplicada.mesclar_arquivos_excel()

livro = openpyxl.load_workbook(os.path.join(
    base, "RemovedorDuplicadasDetran", "resultados", "Estatisticas_Niteroi_Consolidado.xlsx"))
assert livro.sheetnames == ["Dados 1", "Dados 2"], livro.sheetnames
celulas = [c for aba in livro for linha in aba.iter_rows(min_row=2) for c in linha]
assert all(c.data_type == "s" for c in celulas), [(c.value, c.data_type) for c in celulas]
assert sorted(c.value for c in celulas if c.column == 2) == [
    "00301951799", "03535814707", "30082312000155"]
print("ok")
