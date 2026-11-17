"""Extração de entidades (categoria, origem e data) fora do Bag of Words.

O BOW decide a INTENÇÃO. Este módulo decide os VALORES que entram na SQL.
"""
import re
from datetime import date

from texto import normalizar

SINONIMOS_CATEGORIA = {
    "vegetacao": ["vegetacao", "mata", "floresta", "verde", "vegetado", "bosque"],
    "solo_exposto": ["solo exposto", "solo", "terra", "deserto", "solo nu", "solo descoberto"],
    "agua": ["agua", "rio", "lago", "lagoa", "mar", "corpo d agua", "represa"],
}

SINONIMOS_ORIGEM = {
    "satelite": [
        "satelite", "satelites", "orbital", "orbitais", "sentinel",
        "landsat", "espacial", "espaciais",
    ],
    "drone": ["drone", "drono", "vant", "vants", "uav", "aerolevantamento"],
}

ROTULO_CATEGORIA = {
    "vegetacao": "vegetação",
    "solo_exposto": "solo exposto",
    "agua": "água",
}

ROTULO_ORIGEM = {
    "satelite": "satélite",
    "drone": "drone",
}

# nomes já normalizados (sem acento): "março" vira "marco"
MESES = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}

ROTULO_MES = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}

REGEX_NOME_MES = re.compile(r"\b(" + "|".join(MESES) + r")\b")
# "03/2024" ou "3/2024", mas não o "03/2024" de dentro de "12/03/2024"
REGEX_MES_ANO = re.compile(r"(?<![\d/])(\d{1,2})/(\d{4})\b")

# ---------------------------------------------------------------- sinônimos
# Um único passe de regex, com os padrões mais longos primeiro, para evitar
# substituições em cascata (ex.: "solo" dentro de "solo exposto").
_MAPA_SINONIMOS: dict[str, str] = {}
for _canonico, _sinonimos in {**SINONIMOS_CATEGORIA, **SINONIMOS_ORIGEM}.items():
    for _sinonimo in _sinonimos:
        _MAPA_SINONIMOS[normalizar(_sinonimo)] = _canonico

_PADROES = sorted(_MAPA_SINONIMOS, key=len, reverse=True)
_REGEX_SINONIMOS = re.compile(
    r"\b(" + "|".join(re.escape(p) for p in _PADROES) + r")\b"
)


def canonizar(texto: str) -> str:
    """Troca sinônimos pela forma canônica antes do Bag of Words."""
    return _REGEX_SINONIMOS.sub(lambda m: _MAPA_SINONIMOS[m.group(0)], texto)


def _regex_palavras(sinonimos: list[str]) -> re.Pattern:
    """Casa o sinônimo só como palavra inteira (aceitando plural).

    Sem o limite de palavra (\\b), "mar" casaria dentro de "marco" e
    "rio" dentro de "usuario" ou "horario", gerando categoria errada.
    """
    alternativas = sorted((normalizar(s) for s in sinonimos), key=len, reverse=True)
    return re.compile(
        r"\b(?:" + "|".join(re.escape(a) for a in alternativas) + r")(?:s|es)?\b"
    )


_REGEX_CATEGORIA = {c: _regex_palavras(s) for c, s in SINONIMOS_CATEGORIA.items()}
_REGEX_ORIGEM = {o: _regex_palavras(s) for o, s in SINONIMOS_ORIGEM.items()}


def extrair_entidades(texto: str) -> dict:
    texto = normalizar(texto)
    entidades: dict = {}

    for categoria, regex in _REGEX_CATEGORIA.items():
        if regex.search(texto):
            entidades["categoria"] = categoria
            break

    for origem, regex in _REGEX_ORIGEM.items():
        if regex.search(texto):
            entidades["origem"] = origem
            break

    m = re.search(r"\b(\d{2})/(\d{2})/(\d{4})\b", texto)
    if m:
        dia, mes, ano = m.group(1), m.group(2), m.group(3)
        try:
            date(int(ano), int(mes), int(dia))
        except ValueError:
            # ex.: 31/02/2024 — o PostgreSQL rejeitaria e a busca daria erro 500
            entidades["data_invalida"] = f"{dia}/{mes}/{ano}"
            return entidades
        entidades["data"] = f"{ano}-{mes}-{dia}"
        entidades["ano"] = int(ano)
        return entidades

    m = re.search(r"\b(19|20)\d{2}\b", texto)
    if m:
        entidades["ano"] = int(m.group(0))

    # mês: por nome ("marco de 2024") ou no formato mm/aaaa ("03/2024")
    m = REGEX_MES_ANO.search(texto)
    if m:
        if not 1 <= int(m.group(1)) <= 12:
            # ex.: 13/2024 — avisar em vez de ignorar o mês em silêncio
            entidades["data_invalida"] = f"{m.group(1)}/{m.group(2)}"
            return entidades
        entidades["mes"] = int(m.group(1))
    else:
        m = REGEX_NOME_MES.search(texto)
        if m:
            entidades["mes"] = MESES[m.group(1)]

    return entidades
