"""Normalização de texto usada por todo o pipeline.

Mantém dígitos e a barra "/" para que datas no formato dd/mm/aaaa possam ser
extraídas depois por expressão regular.
"""
import re
import unicodedata


def normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9\s/]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()
