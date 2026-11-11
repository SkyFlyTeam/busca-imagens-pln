"""Correção ortográfica contra um léxico fechado do domínio.

Usa distância de edição (Levenshtein, via rapidfuzz). O léxico é montado
automaticamente a partir das paráfrases do catálogo e dos sinônimos de
entidades, então não precisa ser mantido à mão.
"""
from rapidfuzz import fuzz, process

from texto import normalizar

# palavras extras que podem aparecer nas perguntas dos usuários
EXTRA = {
    "foto", "fotos", "imagem", "imagens", "mostrar", "mostre", "liste",
    "exiba", "quero", "ver", "quantas", "quantos", "total", "ha", "tem",
    "existe", "existem", "sistema", "banco", "catalogo", "acervo",
    "capturada", "capturadas", "capturado", "capturados", "tirada",
    "tiradas", "tirado", "tirados", "feita", "feitas", "feito", "feitos",
    "obtida", "obtidas", "registrada", "registradas", "recente",
    "recentes", "ultima", "ultimas", "novo", "novos", "nova", "novas",
    "categoria", "origem", "origens", "fonte", "fontes", "sensor",
    "sensores", "dia", "ano", "data", "drone", "drono", "satelite",
}


def _construir_lexico() -> list[str]:
    # import local para evitar ciclo de importação
    from entidades import SINONIMOS_CATEGORIA, SINONIMOS_ORIGEM
    from intencoes import INTENCOES
    from lexico import SINONIMOS_INTENCAO

    palavras = set(EXTRA)

    for sinonimos in SINONIMOS_INTENCAO.values():
        for sinonimo in sinonimos:
            palavras.update(normalizar(sinonimo).split())

    for intencao in INTENCOES:
        for parafrase in intencao["parafrases"]:
            palavras.update(normalizar(parafrase).split())

    for dicionario in (SINONIMOS_CATEGORIA, SINONIMOS_ORIGEM):
        for chave, sinonimos in dicionario.items():
            palavras.add(normalizar(chave))
            for sinonimo in sinonimos:
                palavras.update(normalizar(sinonimo).split())

    return sorted(p for p in palavras if p)


LEXICO = _construir_lexico()


def corrigir_token(token: str) -> str:
    if not token or token in LEXICO or token.isdigit() or "/" in token:
        return token

    # palavras muito curtas geram falsos positivos (ex.: "a", "de")
    if len(token) < 4:
        return token

    # candidatos com a mesma letra inicial e tamanho parecido
    candidatos = [
        p for p in LEXICO
        if p and p[0] == token[0] and abs(len(p) - len(token)) <= 3
    ]
    if not candidatos:
        return token

    match = process.extractOne(token, candidatos, scorer=fuzz.ratio)

    # palavras longas toleram mais erro; curtas exigem quase igualdade
    limite = 73 if len(token) >= 6 else 85
    if match and match[1] >= limite:
        return match[0]
    return token


def corrigir_texto(texto: str) -> str:
    return " ".join(corrigir_token(t) for t in texto.split())
