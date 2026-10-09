# Trechos reais do Diário Oficial de 2026, encurtados.
# Rodar: python test_portarias.py
from diarioOficial import extrair_portarias

TEXTO = """PORTARIA SMA Nº 264/2026 - SECRETÁRIA MUNICIPAL DE ADMINISTRAÇÃO, no uso de suas atribuições legais, RESOLVE:
Art. 1º Conceder aposentadoria.
Página 3
08/10/2026
NITERÓI TRÂNSITO S/A- NITTRANS
Atos do Presidente
PORTARIA NITTRANS nº 619/2026- O Presidente da Niterói Trânsito S.A. - NITTRANS, no uso de suas atribuições legais, e
Considerando o processo administrativo NIT-050103/000581/2026
Página 4
08/10/2026
RESOLVE:
Art. 1º - Proibir o estacionamento de veículos na Rua Tenente Mesquita, no trecho compreendido entre a Rua Presidente Baker e a Rua Lopes
Trovão - Santa Rosa;
Art. 2º - Esta Portaria entrará em vigor na data de sua publicação, revogadas as disposições em contrário.
EXTRATO DE CONTRATO
Contrato nº 10/2026 –. Partes: NITERÓI TRÂNSITO S.A.
PORTARIA NITTRANS Nº 539/2026- O Presidente da Niterói Trânsito S.A. - NITTRANS, conforme a Portaria NITTRANS nº 12/2025,
Portaria NITTRANS nº 12/2025 citada no meio do texto, e
RESOLVE:
Art. 1º- Interditar a Rua Professor Plínio Leite, no dia 30/08/2026, das 14h à 00h;
EXTRATO DE TERMO DE APOSTILAMENTO Nº 21/2026
Primeiro Termo de Apostilamento do Contrato nº 01/2026.
EMPRESA DE INFRAESTRUTURA E OBRAS DE NITERÓI – ION
PORTARIA Nº. 114/2026- Designar Priscila Freitas Sepulveda (Mat.1735), como Gestora.
PORTARIA NITTRANS nº 408- O Presidente da Niterói Trânsito S/A- NITTRANS, RESOLVE: Exonerar Fulano.
PORTARIA NITTRANS nº 417O Presidente da Niterói Trânsito S/A- NITTRANS, RESOLVE: Exonerar Beltrano.
PORTARIA NITTRANS nº340/2026- Nomear, a contar de 19 de junho de 2026, Ciclano.
Portaria NITTRANS nº 594/2026
O Presidente da Niterói Trânsito S.A. - NITTRANS, considerando a
Portaria NITTRANS nº 011/2022, publicada em 26 de fevereiro de 2022, RESOLVE:
Art. 1º - Revogar a Portaria 444/2026.
Página 5
"""

portarias = extrair_portarias(TEXTO, 2026)

# Só as da NITTRANS; citações no meio do texto não abrem portaria nova.
# Sem o ano no cabeçalho, vale o ano da edição.
assert [numero for numero, _, _ in portarias] == [
    '619/2026', '539/2026', '408/2026', '417/2026', '340/2026', '594/2026'
], [numero for numero, _, _ in portarias]
assert portarias[3][2].startswith('O Presidente')
assert portarias[5][2].startswith('O Presidente')
assert 'nº 011/2022, publicada' in portarias[5][2]

# Página em que cada uma começa: a 619 começa na 4 e continua na 5
assert [pagina for _, pagina, _ in portarias] == [4, 5, 5, 5, 5, 5]

p619 = portarias[0][2]
assert p619.startswith('O Presidente da Niterói Trânsito')
assert 'Página 4' not in p619 and '08/10/2026' not in p619   # rodapé de página
assert 'Lopes Trovão - Santa Rosa' in p619                      # linha quebrada juntada
assert p619.endswith('revogadas as disposições em contrário.')  # corta na vigência
assert '\nRESOLVE:\nArt. 1º' in p619                            # parágrafos

# Publicada sem a frase de vigência: termina no título da seção seguinte
p539 = portarias[1][2]
assert p539.endswith('das 14h à 00h;'), p539[-80:]

print("OK")
