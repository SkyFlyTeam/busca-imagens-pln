"""Pipeline de PLN: normalização, correção, sinônimos, stopwords e stemming.

Etapas (nesta ordem):
  1. normalização        -> minúsculas, sem acento, sem pontuação
  2. correção ortográfica -> léxico fechado do domínio (rapidfuzz)
  3. canonização          -> sinônimos viram a forma canônica (mata -> vegetacao)
  4. números              -> 2024 vira "ano"; dd/mm/aaaa vira "data"
  5. tokenização
  6. remoção de stopwords (preservando palavras de intenção)
  7. stemming RSLP        -> imagens vira "imag"

O resultado final é o texto que entra no Bag of Words.
"""
import os
import re
from pathlib import Path

# NLTK precisa do diretório local de dados (RSLP). Fica dentro do projeto.
os.environ["NLTK_DATA"] = str(Path(__file__).parent / "nltk_data")

import nltk  # noqa: E402
from nltk.stem import RSLPStemmer  # noqa: E402

from corretor import corrigir_texto  # noqa: E402
from entidades import canonizar  # noqa: E402
from lexico import SINONIMOS_INTENCAO  # noqa: E402
from texto import normalizar  # noqa: E402

# Stopwords em português (lista local, para funcionar sem internet).
_ARQUIVO_STOP = Path(__file__).parent / "stopwords_pt.txt"
STOP_BASE = {
    normalizar(linha)
    for linha in _ARQUIVO_STOP.read_text(encoding="utf-8").splitlines()
    if normalizar(linha)
}
STOP_BASE |= {
    "diga", "diz", "possuem", "possui", "possuir", "sao", "foram", "esta",
    "estao", "estava", "estavam", "veio", "vem", "usado", "usados",
}

# Palavras que parecem stopwords, mas carregam intenção neste domínio.
MANTER = {
    "quantas", "quantos", "total", "numero", "ha", "existe", "existem",
    "mostre", "mostrar", "liste", "exiba", "quero", "ver",
    "quais", "qual", "todas", "todos", "acervo", "catalogo",
    "recente", "recentes", "ultima", "ultimas", "novo", "nova",
    "mais", "categoria", "origem", "origens", "fonte", "fontes",
    "sensor", "sensores", "capturada", "capturadas", "tirada", "tiradas",
    "feita", "feitas", "obtida", "obtidas", "sistema", "banco", "possui",
    "dia", "ano", "data",
}

STOP = STOP_BASE - MANTER
stemmer = RSLPStemmer()

_RE_DATA = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")
_RE_ANO = re.compile(r"\b(19|20)\d{2}\b")

# Canonização das palavras de intenção (mostre/liste/quais -> listar).
_MAPA_INTENCAO: dict[str, str] = {}
for _canonico, _sinonimos in SINONIMOS_INTENCAO.items():
    for _sinonimo in _sinonimos:
        _MAPA_INTENCAO[normalizar(_sinonimo)] = _canonico

_PADROES_INTENCAO = sorted(_MAPA_INTENCAO, key=len, reverse=True)
_REGEX_INTENCAO = re.compile(
    r"\b(" + "|".join(re.escape(p) for p in _PADROES_INTENCAO) + r")\b"
)


def canonizar_intencao(texto: str) -> str:
    return _REGEX_INTENCAO.sub(lambda m: _MAPA_INTENCAO[m.group(0)], texto)


def substituir_numeros(texto: str) -> str:
    texto = _RE_DATA.sub(" data ", texto)
    texto = _RE_ANO.sub(" ano ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def detalhar(texto: str) -> dict:
    """Devolve cada etapa do pipeline (usado no debug da interface)."""
    normalizado = normalizar(texto)
    corrigido = corrigir_texto(normalizado)
    canonico_entidades = canonizar(corrigido)
    canonico = canonizar_intencao(canonico_entidades)
    sem_numeros = substituir_numeros(canonico)

    tokens = [t for t in sem_numeros.split() if len(t) > 1]
    sem_stop = [t for t in tokens if t not in STOP]
    stems = [stemmer.stem(t) for t in sem_stop]

    return {
        "entrada": texto,
        "normalizado": normalizado,
        "corrigido": corrigido,
        "canonico_entidades": canonico_entidades,
        "canonico": canonico,
        "tokens": tokens,
        "tokens_sem_stopwords": sem_stop,
        "stems": stems,
        "bow": " ".join(stems),
    }


def processar(texto: str) -> str:
    """Texto cru -> string de stems pronta para o vetorizador."""
    return detalhar(texto)["bow"]
