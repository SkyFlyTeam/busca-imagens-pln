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

from entidades import ROTULO_CATEGORIA, ROTULO_ORIGEM, extrair_entidades
from intencoes import INTENCOES
from pln import detalhar, processar

load_dotenv()

LIMIAR = float(os.getenv("LIMIAR", "0.30"))

# Para responder, a pergunta precisa ter ao menos uma palavra de conteúdo
# do domínio. Sem isso, "qual a capital da França?" seria confundida com
# uma pergunta sobre o catálogo só por causa do "qual".
CONTEUDO = {
    "imag", "vegetaca", "agu", "solo_expost", "dron", "satelit",
    "orig", "ano", "dat", "recent", "antig", "tod",
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
    "origens_disponiveis": "listar as origens disponíveis",
    "mais_recentes": "listar as imagens mais recentes",
    "mais_antigas": "listar as imagens mais antigas",
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

        # não faz sentido escolher uma intenção que exige um dado ausente
        if not params <= E:
            continue

        ajuste = 0.0

        # família contar vs listar
        if quer_contar:
            ajuste += 0.18 if intencao["tipo"] == "contagem" else -0.18
        else:
            ajuste += 0.18 if intencao["tipo"] != "contagem" else -0.18

        # entidades extras (que a intenção ignoraria) pesam contra
        ajuste -= 0.20 * len(E - params)
        if params == E:
            ajuste += 0.05

        # palavras-chave muito discriminativas
        if "orig" in stems and not E:
            ajuste += 0.20 if intencao["id"] == "origens_disponiveis" else -0.05
        if "recent" in stems:
            ajuste += 0.20 if intencao["id"] == "mais_recentes" else -0.05
        if "antig" in stems:
            ajuste += 0.20 if intencao["id"] == "mais_antigas" else -0.05
        if "data" in E:
            ajuste += 0.15 if intencao["id"] == "listar_data" else -0.10

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


def _sufixo_filtros(entidades: dict) -> str:
    partes = []
    if "categoria" in entidades:
        partes.append(f"de {_rotulo_categoria(entidades['categoria'])}")
    if "origem" in entidades:
        partes.append(f"capturadas por {_rotulo_origem(entidades['origem'])}")
    if "data" in entidades:
        ano, mes, dia = entidades["data"].split("-")
        partes.append(f"de {dia}/{mes}/{ano}")
    elif "ano" in entidades:
        partes.append(f"de {entidades['ano']}")
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

    params = [entidades[p] for p in intencao["parametros"]]
    debug["sql"] = intencao["sql"]
    debug["params"] = params

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        cur = conn.cursor()
        cur.execute(intencao["sql"], params)
        linhas = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    if intencao["tipo"] == "contagem":
        total = int(linhas[0][0])
        if intencao["id"] == "contar_total":
            mensagem = f"No total, há {total} imagens cadastradas."
        else:
            mensagem = f"Há {total} imagens{_sufixo_filtros(entidades)}."
        return _resposta(intencao, score, mensagem, [], debug)

    if intencao["tipo"] == "origens":
        origens = [_rotulo_origem(linha[0]) for linha in linhas]
        if len(origens) == 1:
            lista = origens[0]
        else:
            lista = ", ".join(origens[:-1]) + " e " + origens[-1]
        return _resposta(
            intencao,
            score,
            f"As origens disponíveis são: {lista}.",
            [],
            debug,
        )

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

    if intencao["id"] == "mais_recentes":
        mensagem = f"Estas são as {len(resultados)} imagens mais recentes."
    elif intencao["id"] == "mais_antigas":
        mensagem = f"Estas são as {len(resultados)} imagens mais antigas."
    elif resultados:
        mensagem = (
            f"Encontrei {len(resultados)} imagem(ns)"
            f"{_sufixo_filtros(entidades)}."
        )
    else:
        mensagem = f"Não encontrei imagens{_sufixo_filtros(entidades)}."

    return _resposta(intencao, score, mensagem, resultados, debug)


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
