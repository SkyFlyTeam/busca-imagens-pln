"""Catálogo de intenções.

Cada intenção tem:
  - id: identificador usado nos testes e no debug
  - parafrases: formas diferentes de fazer a mesma pergunta
  - sql: consulta parametrizada
  - tipo: "contagem" | "lista" | "origens"
  - parametros: nomes das entidades extraídas que entram na SQL, na ordem

Intenções com filtros opcionais (ex.: "mais recentes" + "de vegetação")
não têm "sql" pronta. Elas têm:
  - opcionais: entidades que, se aparecerem na pergunta, viram filtro extra
  - sql_select: início da consulta (SELECT ... FROM ...)
  - sql_final: o que vem depois do WHERE (ORDER BY, GROUP BY, LIMIT)
O motor monta o WHERE com os parâmetros obrigatórios + opcionais presentes.
"""

_COLUNAS = "id, categoria, data_imagem, origem, caminho_arquivo"

INTENCOES = [
    {
        "id": "contar_total",
        "parafrases": [
            "quantas imagens estao catalogadas",
            "ha quantas imagens",
            "quantas imagens existem",
            "total de imagens no banco",
            "me diga o numero total de imagens",
            "quantas imagens o sistema possui",
            "quantas fotos foram cadastradas",
        ],
        "sql": "SELECT count(*) FROM metadata_table;",
        "tipo": "contagem",
        "parametros": [],
    },
    {
        "id": "listar_todas",
        "parafrases": [
            "mostre todas as imagens",
            "liste todas as imagens",
            "quais imagens existem",
            "exiba todas as fotos",
            "quero ver todas as imagens",
            "mostre o catalogo completo",
            "me mostre o acervo inteiro",
        ],
        "sql": (
            f"SELECT {_COLUNAS} FROM metadata_table "
            "ORDER BY data_imagem DESC LIMIT 60;"
        ),
        "tipo": "lista",
        "parametros": [],
    },
    {
        "id": "listar_categoria",
        "parafrases": [
            "quais imagens possuem vegetacao",
            "mostre imagens de agua",
            "liste as imagens de solo exposto",
            "quero ver imagens com vegetacao",
            "exiba as fotos de agua",
            "imagens da categoria vegetacao",
            "me mostre fotos de solo exposto",
        ],
        "sql": (
            f"SELECT {_COLUNAS} FROM metadata_table "
            "WHERE categoria = %s ORDER BY data_imagem DESC LIMIT 60;"
        ),
        "tipo": "lista",
        "parametros": ["categoria"],
    },
    {
        "id": "listar_origem",
        "parafrases": [
            "imagens de drone",
            "quais imagens foram capturadas por satelite",
            "mostre imagens de satelite",
            "imagens registradas por drone",
            "imagens feitas por drone",
            "fotos obtidas por satelite",
            "imagens capturadas por drone",
        ],
        "sql": (
            f"SELECT {_COLUNAS} FROM metadata_table "
            "WHERE origem = %s ORDER BY data_imagem DESC LIMIT 60;"
        ),
        "tipo": "lista",
        "parametros": ["origem"],
    },
    {
        "id": "listar_ano",
        "parafrases": [
            "imagens de 2024",
            "imagens do ano de 2023",
            "quais fotos foram tiradas em 2022",
            "mostre imagens de 2025",
            "imagens capturadas no ano de 2021",
            "fotos de 2020",
            "imagens do acervo de 2024",
        ],
        "sql_select": f"SELECT {_COLUNAS} FROM metadata_table",
        "sql_final": "ORDER BY data_imagem DESC LIMIT 60",
        "tipo": "lista",
        "parametros": ["ano"],
        "opcionais": ["mes"],
    },
    {
        "id": "listar_data",
        "parafrases": [
            "imagens de 12/03/2024",
            "fotos tiradas em 05/01/2023",
            "quais imagens sao de 20/11/2022",
            "mostre as imagens de 01/06/2025",
            "imagens capturadas em 15/08/2021",
            "fotos do dia 30/12/2020",
            "imagens do dia 10/10/2023",
        ],
        "sql_select": f"SELECT {_COLUNAS} FROM metadata_table",
        "sql_final": "ORDER BY data_imagem DESC LIMIT 60",
        "tipo": "lista",
        "parametros": ["data"],
        "opcionais": ["categoria", "origem"],
    },
    {
        "id": "contar_data",
        "parafrases": [
            "quantas imagens de 12/03/2024",
            "quantas fotos foram tiradas em 05/01/2023",
            "qual o total de imagens do dia 20/11/2022",
            "me diga quantas imagens sao de 01/06/2025",
            "quantas imagens foram capturadas em 15/08/2021",
            "quantas fotos do dia 30/12/2020 existem",
        ],
        "sql_select": "SELECT count(*) FROM metadata_table",
        "sql_final": "",
        "tipo": "contagem",
        "parametros": ["data"],
        "opcionais": ["categoria", "origem"],
    },
    {
        "id": "listar_mes",
        "parafrases": [
            "imagens de marco",
            "fotos de janeiro",
            "quais imagens foram tiradas em julho",
            "mostre as imagens do mes de outubro",
            "imagens capturadas em dezembro",
            "fotos do mes de maio",
            "imagens de agua de setembro",
        ],
        "sql_select": f"SELECT {_COLUNAS} FROM metadata_table",
        "sql_final": "ORDER BY data_imagem DESC LIMIT 60",
        "tipo": "lista",
        "parametros": ["mes"],
        "opcionais": ["categoria", "origem", "ano"],
    },
    {
        "id": "contar_mes",
        "parafrases": [
            "quantas imagens de marco",
            "quantas fotos foram tiradas em janeiro",
            "qual o total de imagens do mes de julho",
            "me diga quantas imagens sao de outubro",
            "quantas imagens foram capturadas em dezembro",
            "quantas fotos do mes de maio existem",
        ],
        "sql_select": "SELECT count(*) FROM metadata_table",
        "sql_final": "",
        "tipo": "contagem",
        "parametros": ["mes"],
        "opcionais": ["categoria", "origem", "ano"],
    },
    {
        "id": "listar_categoria_origem",
        "parafrases": [
            "imagens de vegetacao por drone",
            "mostre imagens de agua de satelite",
            "fotos de solo exposto feitas por drone",
            "quais imagens de vegetacao foram capturadas por satelite",
            "imagens de agua por drone",
            "exiba fotos de solo exposto de satelite",
            "imagens de vegetacao feitas por drone",
        ],
        "sql": (
            f"SELECT {_COLUNAS} FROM metadata_table "
            "WHERE categoria = %s AND origem = %s "
            "ORDER BY data_imagem DESC LIMIT 60;"
        ),
        "tipo": "lista",
        "parametros": ["categoria", "origem"],
    },
    {
        "id": "listar_categoria_ano",
        "parafrases": [
            "imagens de vegetacao em 2024",
            "fotos de agua de 2023",
            "quais imagens de solo exposto foram tiradas em 2022",
            "mostre imagens de vegetacao do ano de 2025",
            "imagens de agua capturadas em 2021",
            "fotos de solo exposto de 2020",
            "imagens de vegetacao tiradas em 2023",
        ],
        "sql_select": f"SELECT {_COLUNAS} FROM metadata_table",
        "sql_final": "ORDER BY data_imagem DESC LIMIT 60",
        "tipo": "lista",
        "parametros": ["categoria", "ano"],
        "opcionais": ["mes"],
    },
    {
        "id": "listar_origem_ano",
        "parafrases": [
            "imagens de drone em 2024",
            "fotos de satelite de 2023",
            "quais imagens de drone foram tiradas em 2022",
            "mostre imagens de satelite do ano de 2025",
            "imagens de drone capturadas em 2021",
            "fotos de satelite de 2020",
            "imagens de drone tiradas em 2023",
        ],
        "sql_select": f"SELECT {_COLUNAS} FROM metadata_table",
        "sql_final": "ORDER BY data_imagem DESC LIMIT 60",
        "tipo": "lista",
        "parametros": ["origem", "ano"],
        "opcionais": ["mes"],
    },
    {
        "id": "listar_categoria_origem_ano",
        "parafrases": [
            "imagens de vegetacao por drone em 2024",
            "fotos de agua de satelite em 2023",
            "quais imagens de solo exposto por drone foram tiradas em 2022",
            "mostre imagens de vegetacao de satelite do ano de 2025",
            "imagens de agua por drone capturadas em 2021",
            "fotos de solo exposto de satelite de 2020",
            "imagens de vegetacao por satelite em 2022",
        ],
        "sql_select": f"SELECT {_COLUNAS} FROM metadata_table",
        "sql_final": "ORDER BY data_imagem DESC LIMIT 60",
        "tipo": "lista",
        "parametros": ["categoria", "origem", "ano"],
        "opcionais": ["mes"],
    },
    {
        "id": "contar_categoria",
        "parafrases": [
            "quantas imagens de vegetacao existem",
            "quantas fotos de agua ha",
            "qual o total de imagens de solo exposto",
            "me diga quantas imagens de vegetacao estao catalogadas",
            "quantas fotos de agua o sistema possui",
            "total de imagens de solo exposto no banco",
            "quantas imagens de vegetacao foram cadastradas",
        ],
        "sql": "SELECT count(*) FROM metadata_table WHERE categoria = %s;",
        "tipo": "contagem",
        "parametros": ["categoria"],
    },
    {
        "id": "contar_origem",
        "parafrases": [
            "quantas imagens de drone existem",
            "quantas fotos de satelite ha",
            "qual o total de imagens de drone",
            "me diga quantas imagens de satelite estao catalogadas",
            "quantas fotos de drone o sistema possui",
            "quantas imagens de satelite foram cadastradas",
        ],
        "sql": "SELECT count(*) FROM metadata_table WHERE origem = %s;",
        "tipo": "contagem",
        "parametros": ["origem"],
    },
    {
        "id": "contar_ano",
        "parafrases": [
            "quantas imagens de 2024 existem",
            "quantas fotos foram tiradas em 2023",
            "qual o total de imagens de 2022",
            "me diga quantas imagens de 2021 estao catalogadas",
            "quantas fotos de 2025 o sistema possui",
            "quantas imagens de 2020 foram cadastradas",
        ],
        "sql_select": "SELECT count(*) FROM metadata_table",
        "sql_final": "",
        "tipo": "contagem",
        "parametros": ["ano"],
        "opcionais": ["mes"],
    },
    {
        "id": "contar_categoria_origem",
        "parafrases": [
            "quantas imagens de vegetacao por drone existem",
            "quantas fotos de agua de satelite ha",
            "qual o total de imagens de solo exposto por drone",
            "me diga quantas imagens de vegetacao por satelite estao catalogadas",
            "quantas fotos de agua por drone o sistema possui",
            "quantas imagens de solo exposto de satelite foram cadastradas",
        ],
        "sql": (
            "SELECT count(*) FROM metadata_table "
            "WHERE categoria = %s AND origem = %s;"
        ),
        "tipo": "contagem",
        "parametros": ["categoria", "origem"],
    },
    {
        "id": "contar_origem_ano",
        "parafrases": [
            "quantas imagens de drone em 2024 existem",
            "quantas fotos de satelite de 2023 ha",
            "qual o total de imagens de drone de 2022",
            "me diga quantas imagens de satelite de 2021 estao catalogadas",
            "quantas fotos de drone de 2025 o sistema possui",
            "quantas imagens de satelite de 2020 foram cadastradas",
        ],
        "sql_select": "SELECT count(*) FROM metadata_table",
        "sql_final": "",
        "tipo": "contagem",
        "parametros": ["origem", "ano"],
        "opcionais": ["mes"],
    },
    {
        "id": "contar_categoria_ano",
        "parafrases": [
            "quantas imagens de vegetacao em 2024 existem",
            "quantas fotos de agua de 2023 ha",
            "qual o total de imagens de solo exposto de 2022",
            "me diga quantas imagens de vegetacao de 2021 estao catalogadas",
            "quantas fotos de agua de 2025 o sistema possui",
            "quantas imagens de solo exposto de 2020 foram cadastradas",
        ],
        "sql_select": "SELECT count(*) FROM metadata_table",
        "sql_final": "",
        "tipo": "contagem",
        "parametros": ["categoria", "ano"],
        "opcionais": ["mes"],
    },
    {
        "id": "contar_categoria_origem_ano",
        "parafrases": [
            "quantas imagens de vegetacao por drone em 2024 existem",
            "quantas fotos de agua de satelite de 2023 ha",
            "qual o total de imagens de solo exposto por drone de 2022",
            "me diga quantas imagens de vegetacao por satelite de 2021 estao catalogadas",
            "quantas fotos de agua por drone de 2025 o sistema possui",
            "quantas imagens de solo exposto de satelite de 2020 foram cadastradas",
        ],
        "sql_select": "SELECT count(*) FROM metadata_table",
        "sql_final": "",
        "tipo": "contagem",
        "parametros": ["categoria", "origem", "ano"],
        "opcionais": ["mes"],
    },
    {
        "id": "origens_disponiveis",
        "parafrases": [
            "quais origens existem",
            "quais sao as origens das imagens",
            "de onde vem as imagens",
            "quais fontes de imagem o sistema possui",
            "liste as origens disponiveis",
            "que origens estao catalogadas",
            "quais sensores foram usados",
        ],
        "sql_select": "SELECT DISTINCT origem FROM metadata_table",
        "sql_final": "ORDER BY origem",
        "tipo": "origens",
        "parametros": [],
        "opcionais": ["categoria", "ano", "mes"],
    },
    {
        "id": "categorias_disponiveis",
        "parafrases": [
            "quais categorias existem",
            "quais sao as categorias das imagens",
            "quais tipos de imagem existem",
            "liste as categorias disponiveis",
            "que categorias estao catalogadas",
            "quais os tipos de imagem do sistema",
            "que tipos de imagem o banco possui",
        ],
        "sql_select": "SELECT DISTINCT categoria FROM metadata_table",
        "sql_final": "ORDER BY categoria",
        "tipo": "categorias",
        "parametros": [],
        "opcionais": ["origem", "ano", "mes"],
    },
    {
        "id": "contar_por_categoria",
        "parafrases": [
            "quantas imagens de cada categoria",
            "quantas imagens por categoria",
            "total de imagens por categoria",
            "numero de imagens de cada tipo",
            "quantas fotos de cada tipo de imagem",
            "quantas imagens tem cada categoria",
        ],
        "sql_select": "SELECT categoria, count(*) FROM metadata_table",
        "sql_final": "GROUP BY categoria ORDER BY categoria",
        "tipo": "agrupado",
        "parametros": [],
        "opcionais": ["origem", "ano", "mes"],
    },
    {
        "id": "contar_por_origem",
        "parafrases": [
            "quantas imagens de cada origem",
            "quantas imagens por origem",
            "total de imagens por fonte",
            "numero de imagens por sensor",
            "quantas fotos de cada fonte",
            "quantas imagens tem cada origem",
        ],
        "sql_select": "SELECT origem, count(*) FROM metadata_table",
        "sql_final": "GROUP BY origem ORDER BY origem",
        "tipo": "agrupado",
        "parametros": [],
        "opcionais": ["categoria", "ano", "mes"],
    },
    {
        "id": "mais_recentes",
        "parafrases": [
            "qual a imagem mais recente",
            "quais sao as imagens mais recentes",
            "mostre as ultimas imagens",
            "ultimas fotos capturadas",
            "imagens mais novas do catalogo",
            "me mostre as imagens recentes",
            "quais imagens foram tiradas por ultimo",
        ],
        "sql_select": f"SELECT {_COLUNAS} FROM metadata_table",
        "sql_final": "ORDER BY data_imagem DESC LIMIT 6",
        "tipo": "lista",
        "parametros": [],
        "opcionais": ["categoria", "origem", "ano", "mes"],
    },
    {
        "id": "mais_antigas",
        "parafrases": [
            "qual a imagem mais antiga",
            "quais sao as imagens mais antigas",
            "mostre as primeiras imagens",
            "fotos mais antigas do catalogo",
            "imagens mais velhas do acervo",
            "me mostre as imagens antigas",
            "quais imagens foram tiradas primeiro",
        ],
        "sql_select": f"SELECT {_COLUNAS} FROM metadata_table",
        "sql_final": "ORDER BY data_imagem ASC LIMIT 6",
        "tipo": "lista",
        "parametros": [],
        "opcionais": ["categoria", "origem", "ano", "mes"],
    },
]


def resumo_catalogo() -> list[dict]:
    return [
        {"id": i["id"], "parafrases": len(i["parafrases"]), "parametros": i["parametros"]}
        for i in INTENCOES
    ]
