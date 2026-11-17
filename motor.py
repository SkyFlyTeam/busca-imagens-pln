"""Motor de busca: classifica a intenção e executa a SQL correspondente.

Fluxo:
  1. pipeline de PLN gera o BOW da pergunta;
  2. TF-IDF + cosseno ranqueia as intenções;
  3. entidades extraídas (categoria/origem/ano/data) restringem os candidatos;
  4. a melhor intenção compatível tem sua SQL executada.
"""
import os

import psycopg2
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from entidades import (
    ROTULO_CATEGORIA, ROTULO_MES, ROTULO_ORIGEM, extrair_entidades,
)
from intencoes import INTENCOES
from pln import detalhar, processar

load_dotenv()

LIMIAR = float(os.getenv("LIMIAR", "0.30"))

# Para responder, a pergunta precisa ter ao menos uma palavra de conteúdo
# do domínio. Sem isso, "qual a capital da França?" seria confundida com
# uma pergunta sobre o catálogo só por causa do "qual".
CONTEUDO = {
    "imag", "vegetaca", "agu", "solo_expost", "dron", "satelit",
    "orig", "ano", "dat", "recent", "antig", "tod", "categ", "tip",
    "me",  # stem RSLP de "mes" (marco, julho, 03/2024 viram "mes")
}

# perguntas de outro domínio que usam palavras do nosso (ex.: "quanto custa
# um drone?") não devem ser respondidas como consulta ao catálogo.
FORA_DOMINIO = {"cust", "prec", "valor", "compr", "vend", "alug"}

DESCRICAO = {
    "contar_total": "contar todas as imagens",
    "listar_todas": "listar todas as imagens",
    "listar_categoria": "listar por categoria",
    "listar_origem": "listar por origem",
    "listar_ano": "listar por ano",
    "listar_data": "listar por data exata",
    "listar_categoria_origem": "listar por categoria e origem",
    "listar_categoria_ano": "listar por categoria e ano",
    "listar_origem_ano": "listar por origem e ano",
    "listar_categoria_origem_ano": "listar por categoria, origem e ano",
    "contar_categoria": "contar por categoria",
    "contar_origem": "contar por origem",
    "contar_ano": "contar por ano",
    "contar_categoria_origem": "contar por categoria e origem",
    "contar_origem_ano": "contar por origem e ano",
    "contar_categoria_ano": "contar por categoria e ano",
    "contar_categoria_origem_ano": "contar por categoria, origem e ano",
    "contar_data": "contar por data exata",
    "listar_mes": "listar por mês",
    "contar_mes": "contar por mês",
    "origens_disponiveis": "listar as origens disponíveis",
    "categorias_disponiveis": "listar as categorias disponíveis",
    "contar_por_categoria": "contar imagens por categoria",
    "contar_por_origem": "contar imagens por origem",
    "mais_recentes": "listar as imagens mais recentes",
    "mais_antigas": "listar as imagens mais antigas",
}

# condição SQL de cada entidade (sempre parametrizada com %s)
CONDICAO_SQL = {
    "categoria": "categoria = %s",
    "origem": "origem = %s",
    "ano": "EXTRACT(YEAR FROM data_imagem) = %s",
    "data": "data_imagem = %s",
    "mes": "EXTRACT(MONTH FROM data_imagem) = %s",
}

NOME_FILTRO = {
    "categoria": "categoria",
    "origem": "origem",
    "ano": "ano",
    "data": "data",
    "mes": "mês",
}


def _montar_vetorizador():
    textos, mapa = [], []
    for intencao in INTENCOES:
        for parafrase in intencao["parafrases"]:
            textos.append(processar(parafrase))
            mapa.append(intencao)

    vetorizador = TfidfVectorizer(
        lowercase=False,
        tokenizer=str.split,
        preprocessor=None,
        token_pattern=None,
    )
    matriz = vetorizador.fit_transform(textos)
    return vetorizador, matriz, mapa


VETORIZADOR, X_REFERENCIA, MAPA = _montar_vetorizador()

INDICES_POR_INTENCAO: dict[str, list[int]] = {}
for _i, _intencao in enumerate(MAPA):
    INDICES_POR_INTENCAO.setdefault(_intencao["id"], []).append(_i)


def _rotulo_categoria(valor: str) -> str:
    return ROTULO_CATEGORIA.get(valor, valor)


def _rotulo_origem(valor: str) -> str:
    return ROTULO_ORIGEM.get(valor, valor)


def _entidades_para_match(entidades: dict) -> set[str]:
    conjunto = set(entidades)
    conjunto.discard("data_invalida")  # tratada à parte em buscar()
    # uma data completa já implica o ano; não penalizar duas vezes
    if "data" in conjunto:
        conjunto.discard("ano")
    return conjunto


def _score_por_intencao(scores) -> dict[str, float]:
    return {
        intencao["id"]: float(
            max(scores[i] for i in INDICES_POR_INTENCAO[intencao["id"]])
        )
        for intencao in INTENCOES
    }


def _ranquear(scores, detalhe: dict, entidades: dict):
    """Ranqueia intenções combinando cosseno + compatibilidade de entidades."""
    scores_por_intencao = _score_por_intencao(scores)
    E = _entidades_para_match(entidades)
    stems = set(detalhe["stems"])
    quer_contar = "cont" in stems

    candidatos = []
    for intencao in INTENCOES:
        params = set(intencao["parametros"])
        aceitos = params | set(intencao.get("opcionais", []))

        # não faz sentido escolher uma intenção que exige um dado ausente
        if not params <= E:
            continue

        ajuste = 0.0

        # família contar vs listar ("agrupado" também é uma contagem)
        conta = intencao["tipo"] in ("contagem", "agrupado")
        if quer_contar:
            ajuste += 0.18 if conta else -0.18
        else:
            ajuste += 0.18 if not conta else -0.18

        # entidades extras (que a intenção ignoraria) pesam contra;
        # filtros opcionais não contam como extras, pois entram no WHERE
        ajuste -= 0.20 * len(E - aceitos)
        if E <= aceitos:
            ajuste += 0.05

        # palavras-chave muito discriminativas
        if "orig" in stems and "origem" not in E:
            ajuste += 0.20 if intencao["id"] in (
                "origens_disponiveis", "contar_por_origem") else -0.05
        if ("categ" in stems or "tip" in stems) and "categoria" not in E:
            ajuste += 0.20 if intencao["id"] in (
                "categorias_disponiveis", "contar_por_categoria") else -0.05
        if "recent" in stems:
            ajuste += 0.20 if intencao["id"] == "mais_recentes" else -0.05
        if "antig" in stems:
            ajuste += 0.20 if intencao["id"] == "mais_antigas" else -0.05
        if "data" in E:
            ajuste += 0.15 if "data" in params else -0.10

        candidatos.append(
            (scores_por_intencao[intencao["id"]] + ajuste,
             intencao, scores_por_intencao[intencao["id"]], ajuste)
        )

    if not candidatos:
        # nenhum candidato compatível: cai no BOW puro
        melhor = max(INTENCOES, key=lambda i: scores_por_intencao[i["id"]])
        return [(
            scores_por_intencao[melhor["id"]], melhor,
            scores_por_intencao[melhor["id"]], 0.0,
        )]

    return sorted(candidatos, key=lambda x: x[0], reverse=True)


def _debug_base(detalhe: dict, scores, limiar: float) -> dict:
    scores_por_intencao = _score_por_intencao(scores)
    top = sorted(
        (
            {
                "intencao": intencao["id"],
                "descricao": DESCRICAO.get(intencao["id"], intencao["id"]),
                "score": round(scores_por_intencao[intencao["id"]], 4),
            }
            for intencao in INTENCOES
        ),
        key=lambda item: item["score"],
        reverse=True,
    )[:3]

    return {
        "normalizado": detalhe["normalizado"],
        "corrigido": detalhe["corrigido"],
        "canonico": detalhe["canonico"],
        "tokens": detalhe["tokens_sem_stopwords"],
        "stems": detalhe["stems"],
        "bow": detalhe["bow"],
        "top": top,
        "limiar": limiar,
        "entidades": {},
        "sql": None,
        "params": [],
        "escolha_final": None,
    }


def classificar(pergunta: str) -> dict:
    detalhe = detalhar(pergunta)
    vetor = VETORIZADOR.transform([detalhe["bow"]])
    scores = cosine_similarity(vetor, X_REFERENCIA)[0]
    debug = _debug_base(detalhe, scores, LIMIAR)
    # usa o texto já corrigido: assim "vejetassao" vira "vegetacao"
    entidades = extrair_entidades(detalhe["corrigido"])
    debug["entidades"] = entidades

    if not detalhe["bow"]:
        return {
            "intencao": None,
            "score": 0.0,
            "entidades": entidades,
            "faltando": [],
            "debug": debug,
        }

    stems = set(detalhe["stems"])
    if not (stems & CONTEUDO):
        debug["motivo_rejeicao"] = "sem palavra de conteúdo do domínio"
        return {
            "intencao": None,
            "score": float(scores.max()),
            "entidades": entidades,
            "faltando": [],
            "debug": debug,
        }

    if stems & FORA_DOMINIO:
        debug["motivo_rejeicao"] = "pergunta fora do domínio (preço/compra)"
        return {
            "intencao": None,
            "score": float(scores.max()),
            "entidades": entidades,
            "faltando": [],
            "debug": debug,
        }

    ranking = _ranquear(scores, detalhe, entidades)
    score_ajustado, intencao, score_bow, ajuste = ranking[0]

    debug["escolha_final"] = {
        "intencao": intencao["id"],
        "descricao": DESCRICAO.get(intencao["id"], intencao["id"]),
        "score_bow": round(score_bow, 4),
        "score_ajustado": round(score_ajustado, 4),
        "ajuste": round(ajuste, 4),
    }

    if score_bow < LIMIAR:
        return {
            "intencao": None,
            "score": score_bow,
            "entidades": entidades,
            "faltando": [],
            "debug": debug,
        }

    faltando = [p for p in intencao["parametros"] if p not in entidades]
    return {
        "intencao": intencao,
        "score": score_bow,
        "entidades": entidades,
        "faltando": faltando,
        "debug": debug,
    }


def _sufixo_filtros(entidades: dict, plural: bool = True) -> str:
    partes = []
    if "categoria" in entidades:
        partes.append(f"de {_rotulo_categoria(entidades['categoria'])}")
    if "origem" in entidades:
        verbo = "capturadas" if plural else "capturada"
        partes.append(f"{verbo} por {_rotulo_origem(entidades['origem'])}")
    if "data" in entidades:
        ano, mes, dia = entidades["data"].split("-")
        partes.append(f"de {dia}/{mes}/{ano}")
    elif "mes" in entidades and "ano" in entidades:
        partes.append(f"de {ROTULO_MES[entidades['mes']]} de {entidades['ano']}")
    elif "ano" in entidades:
        partes.append(f"de {entidades['ano']}")
    elif "mes" in entidades:
        partes.append(f"de {ROTULO_MES[entidades['mes']]}")
    return (" " + " ".join(partes)) if partes else ""


def _resposta(intencao, score, mensagem, resultados, debug):
    return {
        "intencao": intencao["id"] if intencao else None,
        "descricao_intencao": DESCRICAO.get(intencao["id"]) if intencao else None,
        "score": round(float(score), 4),
        "mensagem": mensagem,
        "resultados": resultados,
        "debug": debug,
    }


def buscar(pergunta: str) -> dict:
    classificacao = classificar(pergunta)
    intencao = classificacao["intencao"]
    score = classificacao["score"]
    entidades = classificacao["entidades"]
    debug = classificacao["debug"]

    if "data_invalida" in entidades:
        return _resposta(
            None,
            score,
            f"A data {entidades['data_invalida']} não existe. "
            "Use o formato dd/mm/aaaa com uma data válida.",
            [],
            debug,
        )

    if intencao is None:
        if not debug["bow"]:
            mensagem = (
                "Não consegui identificar palavras na sua pergunta. "
                "Tente: 'quantas imagens existem?'"
            )
        else:
            mensagem = (
                "Não entendi a pergunta. Tente algo como: "
                "'quantas imagens existem?' ou 'imagens de vegetação'."
            )
        return _resposta(None, score, mensagem, [], debug)

    if classificacao["faltando"]:
        return _resposta(
            intencao,
            score,
            "Entendi a intenção, mas não identifiquei: "
            + ", ".join(classificacao["faltando"])
            + ".",
            [],
            debug,
        )

    unica = (
        intencao["id"] in ("mais_recentes", "mais_antigas")
        and _pede_uma_imagem(debug["corrigido"])
    )
    sql, params, aplicados = _montar_sql(intencao, entidades, unica)
    debug["sql"] = sql
    debug["params"] = params

    # entidades que a pergunta tinha, mas que esta intenção não usa
    ignorados = _entidades_para_match(entidades) - set(
        intencao["parametros"] + intencao.get("opcionais", [])
    )
    aviso = ""
    if ignorados:
        nomes = ", ".join(NOME_FILTRO[i] for i in sorted(ignorados))
        aviso = f" (Obs.: o filtro de {nomes} não foi usado nesta busca.)"

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        linhas = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    filtros = _sufixo_filtros(aplicados)

    if intencao["tipo"] == "contagem":
        total = int(linhas[0][0])
        if intencao["id"] == "contar_total":
            mensagem = f"No total, há {total} imagens cadastradas."
        else:
            palavra = "imagem" if total == 1 else "imagens"
            mensagem = f"Há {total} {palavra}{filtros}."
        return _resposta(intencao, score, mensagem + aviso, [], debug)

    if intencao["tipo"] == "agrupado":
        rotulo = (
            _rotulo_categoria if intencao["id"] == "contar_por_categoria"
            else _rotulo_origem
        )
        nome = "categoria" if intencao["id"] == "contar_por_categoria" else "origem"
        if not linhas:
            mensagem = f"Não encontrei imagens{filtros}."
        else:
            partes = [f"{rotulo(valor)}: {int(n)}" for valor, n in linhas]
            mensagem = f"Imagens{filtros} por {nome}: {_juntar(partes)}."
        return _resposta(intencao, score, mensagem + aviso, [], debug)

    if intencao["tipo"] in ("origens", "categorias"):
        if intencao["tipo"] == "origens":
            valores = [_rotulo_origem(linha[0]) for linha in linhas]
            titulo = "As origens disponíveis"
        else:
            valores = [_rotulo_categoria(linha[0]) for linha in linhas]
            titulo = "As categorias disponíveis"
        if not valores:
            mensagem = f"Não encontrei imagens{filtros}."
        else:
            mensagem = f"{titulo}{_filtros_para_lista(aplicados)} são: {_juntar(valores)}."
        return _resposta(intencao, score, mensagem + aviso, [], debug)

    resultados = [
        {
            "id": linha[0],
            "categoria": _rotulo_categoria(linha[1]),
            "categoria_id": linha[1],
            "data": linha[2].strftime("%d/%m/%Y"),
            "origem": _rotulo_origem(linha[3]),
            "origem_id": linha[3],
            "url": "/" + linha[4],
        }
        for linha in linhas
    ]

    if not resultados:
        mensagem = f"Não encontrei imagens{filtros}."
    elif intencao["id"] in ("mais_recentes", "mais_antigas"):
        qual = "recente" if intencao["id"] == "mais_recentes" else "antiga"
        if unica:
            r = resultados[0]
            mensagem = (
                f"A imagem mais {qual}{_sufixo_filtros(aplicados, plural=False)} "
                f"é de {r['data']} ({r['categoria']}, {r['origem']})."
            )
        elif len(resultados) == 1:
            mensagem = f"Só há 1 imagem{_sufixo_filtros(aplicados, plural=False)}."
        else:
            mensagem = (
                f"Estas são as {len(resultados)} imagens mais {qual}s{filtros}."
            )
    else:
        mensagem = f"Encontrei {len(resultados)} imagem(ns){filtros}."

    return _resposta(intencao, score, mensagem + aviso, resultados, debug)


def _juntar(itens: list[str]) -> str:
    """["a", "b", "c"] -> "a, b e c"."""
    if len(itens) == 1:
        return itens[0]
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def _filtros_para_lista(aplicados: dict) -> str:
    """Filtros para frases como "As origens disponíveis para água em 2024"."""
    partes = []
    if "categoria" in aplicados:
        partes.append(f"para {_rotulo_categoria(aplicados['categoria'])}")
    if "origem" in aplicados:
        partes.append(f"para {_rotulo_origem(aplicados['origem'])}")
    if "mes" in aplicados and "ano" in aplicados:
        partes.append(f"em {ROTULO_MES[aplicados['mes']]} de {aplicados['ano']}")
    elif "ano" in aplicados:
        partes.append(f"em {aplicados['ano']}")
    elif "mes" in aplicados:
        partes.append(f"em {ROTULO_MES[aplicados['mes']]}")
    return (" " + " ".join(partes)) if partes else ""


# Pistas de que a pessoa quer UMA imagem ("qual a imagem mais recente")
# ou várias ("quais as imagens mais recentes").
_SINGULAR = {"imagem", "foto", "fotografia", "recente", "ultima", "ultimo",
             "antiga", "antigo", "primeira", "primeiro"}
_PLURAL = {"imagens", "fotos", "fotografias", "recentes", "ultimas", "ultimos",
           "antigas", "antigos", "primeiras", "primeiros", "quais"}


def _pede_uma_imagem(texto_corrigido: str) -> bool:
    palavras = set(texto_corrigido.split())
    return bool(palavras & _SINGULAR) and not (palavras & _PLURAL)


def _montar_sql(intencao: dict, entidades: dict, unica: bool = False):
    """Devolve (sql, parametros, filtros_aplicados).

    Intenções simples já têm a SQL pronta. As que aceitam filtros opcionais
    têm o WHERE montado aqui, sempre com %s (sem concatenar valores).
    """
    if "sql" in intencao:
        aplicados = {p: entidades[p] for p in intencao["parametros"]}
        if "data" in aplicados:
            aplicados.pop("ano", None)
        return intencao["sql"], list(aplicados.values()), aplicados

    nomes = list(intencao["parametros"])
    for opcional in intencao.get("opcionais", []):
        if opcional in entidades and opcional not in nomes:
            # a data completa já implica o ano
            if opcional == "ano" and "data" in entidades:
                continue
            nomes.append(opcional)

    aplicados = {n: entidades[n] for n in nomes}
    sql = intencao["sql_select"]
    if nomes:
        sql += " WHERE " + " AND ".join(CONDICAO_SQL[n] for n in nomes)
    final = intencao["sql_final"]
    if unica:
        final = final.replace("LIMIT 6", "LIMIT 1")
    if final:
        sql += " " + final
    return sql + ";", list(aplicados.values()), aplicados


def estatisticas() -> dict:
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM metadata_table;")
        total = int(cur.fetchone()[0])
        cur.execute(
            "SELECT categoria, count(*) FROM metadata_table "
            "GROUP BY categoria ORDER BY categoria;"
        )
        por_categoria = {c: int(n) for c, n in cur.fetchall()}
        cur.close()
    finally:
        conn.close()
    return {"total": total, "por_categoria": por_categoria}
