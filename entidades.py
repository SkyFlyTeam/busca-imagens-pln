"""Extração de entidades (categoria, origem e data) fora do Bag of Words.

O BOW decide a INTENÇÃO. Este módulo decide os VALORES que entram na SQL.
"""
import re

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


def extrair_entidades(texto: str) -> dict:
    texto = normalizar(texto)
    entidades: dict = {}

    for categoria, sinonimos in SINONIMOS_CATEGORIA.items():
        if any(s in texto for s in sinonimos):
            entidades["categoria"] = categoria
            break

    for origem, sinonimos in SINONIMOS_ORIGEM.items():
        if any(s in texto for s in sinonimos):
            entidades["origem"] = origem
            break

    m = re.search(r"\b(\d{2})/(\d{2})/(\d{4})\b", texto)
    if m:
        dia, mes, ano = m.group(1), m.group(2), m.group(3)
        entidades["data"] = f"{ano}-{mes}-{dia}"
        entidades["ano"] = int(ano)
    else:
        m = re.search(r"\b(19|20)\d{2}\b", texto)
        if m:
            entidades["ano"] = int(m.group(0))

    return entidades
