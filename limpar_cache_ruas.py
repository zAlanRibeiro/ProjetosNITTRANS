# -*- coding: utf-8 -*-
"""
Limpa o cache_ruas.json do DetranLimpo aplicando as regras atuais.
Execute uma vez após copiar o cache gerado pelo app instalado.
"""
import json
import re
from pathlib import Path

CACHE = Path("DetranLimpo/cache_ruas.json")

# Tudo a partir de LADO / OPOSTO / OP (qualquer forma) inclusive o que vem depois
_RE_POSICAO   = re.compile(
    r'[\s,]+(?:NO?\s+)?(?:LADO\s+)?OP(?:OSTO)?\b.*$|'
    r'[\s,]+OPOSTO\b.*$|'
    r'[\s,]+LADO\s+(?:DIR|ESQ|OP|OPOSTO)\b.*$',
    re.IGNORECASE
)
# PRÓXIMO / PROX (+ o que vier depois)
_RE_PROXIMO   = re.compile(
    r'[\s,]+PR[OÓ]XIMO\b.*$|[\s,]+PROX\.?\b.*$',
    re.IGNORECASE
)
# Nº / N° / N NNN no final ou seguido de lixo
_RE_NUM_ABREV = re.compile(r'[\s,]+N[º°oa]?\.?\s*\d+\b.*$', re.IGNORECASE)
# Cruzamentos
_RE_CRUZAM    = re.compile(
    r'\s+(?:CRUZAMENTO\b.*|C(?:OM\s+|/\s*|\s+)(?:R\.?|RUA|AV\.?|AVENIDA)\b.*)$',
    re.IGNORECASE
)
# Prefixo inválido colado: ZRUA → RUA
_RE_PREFIXO   = re.compile(
    r'^[A-Z]{1,3}(?=RUA\b|AV\b|AVENIDA\b|AL\b|ALAMEDA\b|TRAVESSA\b|ESTRADA\b|PRAC[AÇ])',
    re.IGNORECASE
)
# Prefixo duplicado: AL AL. → AL.
_RE_DUPLO     = re.compile(r'^(AL|AV|R)\s+(?=\1[\.\s])', re.IGNORECASE)


def limpar(texto):
    t = str(texto).strip()
    if not t or t.lower() == 'nan':
        return ''
    t = _RE_POSICAO.sub('', t).strip()
    t = _RE_PROXIMO.sub('', t).strip()
    t = _RE_NUM_ABREV.sub('', t).strip()
    t = _RE_CRUZAM.sub('', t).strip()
    t = _RE_DUPLO.sub('', t).strip()
    t = _RE_PREFIXO.sub('', t).strip()
    # remove número simples no final
    m = re.match(r'^(.*?),?\s*(\d+\s+[Aa][Oo]\s+\d+)\s*$', t)
    if m:
        return re.sub(r'\s+N\.?\s*$', '', m.group(1).strip(), flags=re.IGNORECASE)
    m = re.match(r'^(.*?),?\s*(\d+[\w-]*)\s*$', t)
    if m:
        return re.sub(r'\s+N\.?\s*$', '', m.group(1).strip(), flags=re.IGNORECASE)
    return t


with open(CACHE, 'r', encoding='utf-8') as f:
    cache = json.load(f)

novo = {}
alterados = 0

for chave, valor in cache.items():
    # Se a API encontrou um nome diferente, mantém o nome oficial
    # Se não encontrou (valor == chave), aplica a limpeza
    if valor.strip().upper() == chave.strip().upper():
        valor_limpo = limpar(valor)
    else:
        valor_limpo = valor  # nome oficial da API — já está correto

    # Também limpa a chave para bater com o que o novo código vai procurar
    chave_limpa = limpar(chave).upper().strip()

    if not chave_limpa:
        continue

    if valor_limpo != valor or chave_limpa != chave.strip().upper():
        alterados += 1

    novo[chave_limpa] = valor_limpo

with open(CACHE, 'w', encoding='utf-8') as f:
    json.dump(novo, f, ensure_ascii=False, indent=2)

print(f"Cache limpo: {len(novo)} entradas ({alterados} corrigidas).")
print(f"Salvo em: {CACHE}")