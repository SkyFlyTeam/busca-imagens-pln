"""Sinônimos de intenção.

São palavras que significam a mesma coisa para o motor de busca.
Canonizá-las antes do BOW reduz a variação e melhora o cosseno.
Exemplo: "mostre", "liste", "exiba" e "quais" viram todas "listar".
"""

SINONIMOS_INTENCAO = {
    "contar": [
        "quantas", "quantos", "total", "numero", "ha", "contar",
    ],
    "listar": [
        "mostre", "mostrar", "mostra", "liste", "listar", "lista",
        "exiba", "exibir", "exibe", "quero ver", "me mostre",
        "quais", "qual", "ver",
    ],
    "imagem": [
        "imagem", "imagens", "foto", "fotos", "fotografia", "fotografias",
    ],
    "todos": [
        "todas", "todos", "tudo", "catalogo", "acervo", "inteiro", "inteira",
        "completo", "completa",
    ],
    "recente": [
        "recente", "recentes", "ultima", "ultimas", "ultimo", "ultimos",
        "novo", "nova", "novos", "novas", "mais recente", "mais recentes",
        "mais novo", "mais nova", "mais novos", "mais novas",
        "o que ha de mais novo", "ha de mais novo",
    ],
    "antiga": [
        "antiga", "antigas", "antigo", "antigos",
        "mais antiga", "mais antigas", "mais antigo", "mais antigos",
    ],
    "capturar": [
        "capturada", "capturadas", "capturado", "capturados",
        "tirada", "tiradas", "tirado", "tirados",
        "feita", "feitas", "feito", "feitos",
        "obtida", "obtidas", "registrada", "registradas", "capturar",
    ],
    "origem": [
        "origem", "origens", "fonte", "fontes", "sensor", "sensores",
        "de onde vem", "onde vem", "de onde veio", "onde veio",
    ],
}
