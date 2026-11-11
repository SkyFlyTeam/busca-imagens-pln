"""Avaliação do motor com perguntas NOVAS (não presentes no catálogo).

Gera:
  - acurácia geral e por grupo
  - acurácia por intenção
  - confusões mais comuns
  - ablação (contribuição de cada etapa de PLN)
  - curva do limiar
  - resultados_avaliacao.md
"""
from collections import Counter, defaultdict

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import motor
from corretor import corrigir_texto
from entidades import canonizar
from intencoes import INTENCOES
from pln import STOP, canonizar_intencao, stemmer, substituir_numeros
from texto import normalizar

LIMIAR_PADRAO = motor.LIMIAR

# (pergunta, intenção esperada ou None, grupo)
CASOS = [
    # contar_total
    ("me fala quantas imagens tem no banco", "contar_total", "normal"),
    ("qual o numero de imagens cadastradas", "contar_total", "normal"),
    ("o banco tem quantas fotos", "contar_total", "normal"),
    ("quantas imagens foram catalogadas", "contar_total", "normal"),
    ("me diz o total de imagens", "contar_total", "normal"),
    # listar_todas
    ("me mostra tudo que esta cadastrado", "listar_todas", "normal"),
    ("quero ver o catalogo inteiro", "listar_todas", "normal"),
    ("exiba o acervo completo", "listar_todas", "normal"),
    ("liste o acervo", "listar_todas", "normal"),
    ("mostre todas as fotos", "listar_todas", "normal"),
    # listar_categoria
    ("tem foto de floresta", "listar_categoria", "normal"),
    ("quero imagens do rio", "listar_categoria", "normal"),
    ("me mostra o solo nu", "listar_categoria", "normal"),
    ("imagens com vegetacao", "listar_categoria", "normal"),
    ("quero ver fotos de lago", "listar_categoria", "normal"),
    # listar_origem
    ("o que veio de drone", "listar_origem", "normal"),
    ("imagens orbitais", "listar_origem", "normal"),
    ("fotos de vant", "listar_origem", "normal"),
    ("capturas de satelite", "listar_origem", "normal"),
    ("imagens feitas por drone", "listar_origem", "normal"),
    # listar_ano
    ("o que tem de 2024", "listar_ano", "normal"),
    ("imagens capturadas em 2023", "listar_ano", "normal"),
    ("acervo de 2022", "listar_ano", "normal"),
    ("fotos do ano de 2021", "listar_ano", "normal"),
    ("imagens de 2025", "listar_ano", "normal"),
    # listar_data
    ("fotos de 10/10/2024", "listar_data", "normal"),
    ("o que foi tirado em 03/07/2022", "listar_data", "normal"),
    ("imagens do dia 22/02/2023", "listar_data", "normal"),
    ("capturas de 15/09/2021", "listar_data", "normal"),
    ("fotos de 30/12/2020", "listar_data", "normal"),
    # listar_categoria_origem
    ("vegetacao vista por drone", "listar_categoria_origem", "normal"),
    ("agua capturada por satelite", "listar_categoria_origem", "normal"),
    ("solo exposto de drone", "listar_categoria_origem", "normal"),
    ("mata registrada por satelite", "listar_categoria_origem", "normal"),
    ("fotos de rio feitas por drone", "listar_categoria_origem", "normal"),
    # listar_categoria_ano
    ("vegetacao de 2024", "listar_categoria_ano", "normal"),
    ("solo exposto em 2023", "listar_categoria_ano", "normal"),
    ("agua do ano de 2022", "listar_categoria_ano", "normal"),
    ("fotos de mata de 2021", "listar_categoria_ano", "normal"),
    ("imagens de floresta em 2025", "listar_categoria_ano", "normal"),
    # listar_origem_ano
    ("drone em 2022", "listar_origem_ano", "normal"),
    ("satelite de 2025", "listar_origem_ano", "normal"),
    ("fotos de drone de 2023", "listar_origem_ano", "normal"),
    ("imagens orbitais de 2024", "listar_origem_ano", "normal"),
    ("capturas de vant em 2021", "listar_origem_ano", "normal"),
    # listar_categoria_origem_ano
    ("vegetacao de drone em 2024", "listar_categoria_origem_ano", "normal"),
    ("agua de satelite em 2023", "listar_categoria_origem_ano", "normal"),
    ("solo exposto por drone em 2022", "listar_categoria_origem_ano", "normal"),
    ("mata de satelite em 2021", "listar_categoria_origem_ano", "normal"),
    ("fotos de rio por drone em 2025", "listar_categoria_origem_ano", "normal"),
    # contar_categoria
    ("quantas fotos de vegetacao", "contar_categoria", "normal"),
    ("numero de imagens de agua", "contar_categoria", "normal"),
    ("total de fotos de solo exposto", "contar_categoria", "normal"),
    ("quantas imagens de mata existem", "contar_categoria", "normal"),
    ("me diz quantas fotos de rio ha", "contar_categoria", "normal"),
    # contar_origem
    ("quantas fotos de drone", "contar_origem", "normal"),
    ("numero de imagens de satelite", "contar_origem", "normal"),
    ("total de imagens orbitais", "contar_origem", "normal"),
    ("quantas imagens de vant existem", "contar_origem", "normal"),
    ("me diz quantas fotos de drone ha", "contar_origem", "normal"),
    # contar_ano
    ("quantas imagens de 2024", "contar_ano", "normal"),
    ("numero de fotos de 2023", "contar_ano", "normal"),
    ("total de imagens de 2022", "contar_ano", "normal"),
    ("quantas fotos de 2021 existem", "contar_ano", "normal"),
    ("me diz quantas imagens de 2025 ha", "contar_ano", "normal"),
    # contar_categoria_origem
    ("quantas imagens de vegetacao por drone", "contar_categoria_origem", "normal"),
    ("numero de fotos de agua de satelite", "contar_categoria_origem", "normal"),
    ("total de imagens de solo exposto por drone", "contar_categoria_origem", "normal"),
    ("quantas fotos de mata de satelite existem", "contar_categoria_origem", "normal"),
    ("me diz quantas imagens de rio por drone ha", "contar_categoria_origem", "normal"),
    # origens_disponiveis
    ("quais fontes existem", "origens_disponiveis", "normal"),
    ("me diz as origens", "origens_disponiveis", "normal"),
    ("quais sensores foram usados", "origens_disponiveis", "normal"),
    ("de onde vem as imagens", "origens_disponiveis", "normal"),
    ("lista as origens disponiveis", "origens_disponiveis", "normal"),
    # mais_recentes
    ("o que ha de mais novo", "mais_recentes", "normal"),
    ("imagens recentes", "mais_recentes", "normal"),
    ("ultimas fotos", "mais_recentes", "normal"),
    ("qual a foto mais nova", "mais_recentes", "normal"),
    ("me mostra as imagens mais recentes", "mais_recentes", "normal"),
    # mais_antigas
    ("qual a imagem mais antiga", "mais_antigas", "normal"),
    ("quero ver as fotos mais antigas", "mais_antigas", "normal"),
    ("imagens mais velhas do acervo", "mais_antigas", "normal"),
    # contar_origem_ano
    ("quantas imagens de drone em 2024", "contar_origem_ano", "normal"),
    ("numero de fotos de satelite de 2023", "contar_origem_ano", "normal"),
    ("total de imagens de drone de 2022", "contar_origem_ano", "normal"),
    # contar_categoria_ano
    ("quantas imagens de solo exposto em 2022", "contar_categoria_ano", "normal"),
    ("numero de fotos de agua de 2023", "contar_categoria_ano", "normal"),
    ("total de imagens de vegetacao de 2024", "contar_categoria_ano", "normal"),
    # contar_categoria_origem_ano
    ("quantas imagens de vegetacao por satelite em 2024",
     "contar_categoria_origem_ano", "normal"),
    ("numero de fotos de agua de drone de 2023",
     "contar_categoria_origem_ano", "normal"),
    ("total de imagens de solo exposto por drone de 2022",
     "contar_categoria_origem_ano", "normal"),
    # erros de digitação
    ("quantas imagems existem", "contar_total", "typo"),
    ("imagens de vejetacao", "listar_categoria", "typo"),
    ("fotos de drono", "listar_origem", "typo"),
    ("quais as origen das imagens", "origens_disponiveis", "typo"),
    ("imagens de solo exposto por sateliti", "listar_categoria_origem", "typo"),
    ("quantas imagens de aguá", "contar_categoria", "typo"),
    ("imagens de vejetassao por drono em 2024", "listar_categoria_origem_ano", "typo"),
    ("quantas fotos de drono existem", "contar_origem", "typo"),
    ("mostre as imagems mais recentes", "mais_recentes", "typo"),
    ("quais imagens de mata por sateliti em 2023", "listar_categoria_origem_ano", "typo"),
    # fora do domínio
    ("qual a capital da Franca", None, "fora"),
    ("previsao do tempo para amanha", None, "fora"),
    ("quem descobriu o Brasil", None, "fora"),
    ("como fazer bolo de cenoura", None, "fora"),
    ("qual a melhor serie da Netflix", None, "fora"),
    ("me conte uma piada", None, "fora"),
    ("como esta a bolsa de valores", None, "fora"),
    ("qual o significado da vida", None, "fora"),
    ("traduza bom dia para ingles", None, "fora"),
    ("quanto custa um carro", None, "fora"),
    ("quanto custa um drone", None, "fora"),
]


def processar_ablation(
    texto: str,
    norm: bool = True,
    stop: bool = True,
    stem: bool = True,
    canon: bool = True,
    corr: bool = True,
    num: bool = True,
) -> str:
    """Pipeline completo, com a possibilidade de desligar uma etapa."""
    t = normalizar(texto) if norm else texto.lower()
    if corr:
        t = corrigir_texto(t)
    if canon:
        t = canonizar_intencao(canonizar(t))
    if num:
        t = substituir_numeros(t)

    tokens = [x for x in t.split() if len(x) > 1]
    if stop:
        tokens = [x for x in tokens if x not in STOP]
    if stem:
        tokens = [stemmer.stem(x) for x in tokens]
    return " ".join(tokens)


def _melhor_por_intencao(scores, donos: list[str]) -> dict[str, float]:
    melhor: dict[str, float] = {}
    for indice, dono in enumerate(donos):
        if dono not in melhor or scores[indice] > melhor[dono]:
            melhor[dono] = float(scores[indice])
    return melhor


def avaliar_final() -> list[dict]:
    resultados = []
    for pergunta, esperado, grupo in CASOS:
        classificacao = motor.classificar(pergunta)
        previsto = (
            classificacao["intencao"]["id"]
            if classificacao["intencao"] else None
        )
        resultados.append(
            {
                "pergunta": pergunta,
                "esperado": esperado,
                "previsto": previsto,
                "grupo": grupo,
                "score": classificacao["score"],
                "entidades": classificacao["entidades"],
                "debug": classificacao["debug"],
            }
        )
    return resultados


def metricas(resultados: list[dict]) -> dict:
    def acertos(grupo=None):
        filtrados = [
            r for r in resultados
            if grupo is None or r["grupo"] == grupo
        ]
        certos = sum(r["esperado"] == r["previsto"] for r in filtrados)
        return certos, len(filtrados)

    total_certos, total = acertos()
    normal_certos, normal = acertos("normal")
    typo_certos, typo = acertos("typo")
    fora_certos, fora = acertos("fora")
    fallback = sum(r["previsto"] is None for r in resultados)

    return {
        "acuracia": total_certos / total,
        "acuracia_normal": normal_certos / normal,
        "acuracia_typo": typo_certos / typo,
        "acuracia_fora": fora_certos / fora,
        "fallback": fallback / total,
        "total": total,
        "detalhe": {
            "normal": (normal_certos, normal),
            "typo": (typo_certos, typo),
            "fora": (fora_certos, fora),
        },
    }


def _avaliar_pipeline(flags: dict, classe, in_domain: list) -> float:
    textos, donos = [], []
    for intencao in INTENCOES:
        for parafrase in intencao["parafrases"]:
            textos.append(processar_ablation(parafrase, **flags))
            donos.append(intencao["id"])

    vetorizador = classe(
        lowercase=False, tokenizer=str.split, preprocessor=None,
        token_pattern=None,
    )
    matriz = vetorizador.fit_transform(textos)

    certos = 0
    for pergunta, esperado, _ in in_domain:
        vetor = vetorizador.transform(
            [processar_ablation(pergunta, **flags)]
        )
        scores = cosine_similarity(vetor, matriz)[0]
        melhor = _melhor_por_intencao(scores, donos)
        previsto = max(melhor, key=melhor.get)
        certos += previsto == esperado

    return certos / len(in_domain)


def ablacao() -> list[tuple[str, float]]:
    """Ablação: parte do sistema completo e desliga uma etapa por vez."""
    in_domain = [c for c in CASOS if c[2] != "fora"]

    # sistema completo, com as regras de entidades
    certos = 0
    for pergunta, esperado, _ in in_domain:
        classificacao = motor.classificar(pergunta)
        previsto = (
            classificacao["intencao"]["id"]
            if classificacao["intencao"] else None
        )
        certos += previsto == esperado

    base = {
        "norm": True, "stop": True, "stem": True,
        "canon": True, "corr": True, "num": True,
    }

    linhas = [("Sistema completo (com regras)", certos / len(in_domain))]
    linhas.append((
        "Sem regras de entidades",
        _avaliar_pipeline(base, TfidfVectorizer, in_domain),
    ))

    remocoes = [
        ("Sem normalização", "norm"),
        ("Sem stopwords", "stop"),
        ("Sem stemming", "stem"),
        ("Sem substituição de números", "num"),
        ("Sem canonização de sinônimos", "canon"),
        ("Sem corretor ortográfico", "corr"),
    ]
    for nome, chave in remocoes:
        flags = {**base, chave: False}
        linhas.append((
            nome,
            _avaliar_pipeline(flags, TfidfVectorizer, in_domain),
        ))

    linhas.append((
        "Sem TF-IDF (BOW puro)",
        _avaliar_pipeline(base, CountVectorizer, in_domain),
    ))

    return linhas


def curva_limiar() -> list[tuple[float, float, float, float]]:
    linhas = []
    for limiar in [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60]:
        motor.LIMIAR = limiar
        resultados = avaliar_final()
        total_certos = sum(r["esperado"] == r["previsto"] for r in resultados)
        fallback = sum(r["previsto"] is None for r in resultados)
        in_domain = [r for r in resultados if r["grupo"] != "fora"]
        in_certos = sum(r["esperado"] == r["previsto"] for r in in_domain)
        ood = [r for r in resultados if r["grupo"] == "fora"]
        ood_rejeitados = sum(r["previsto"] is None for r in ood)
        linhas.append((
            limiar,
            total_certos / len(resultados),
            in_certos / len(in_domain),
            fallback / len(resultados),
        ))
        # a última coluna (OOD) é derivada no relatório
        linhas[-1] = (*linhas[-1], ood_rejeitados / len(ood))
    motor.LIMIAR = LIMIAR_PADRAO
    return linhas


def _tabela_confusoes(resultados: list[dict]) -> list[str]:
    confusoes = Counter(
        (r["esperado"] or "NENHUMA", r["previsto"] or "NENHUMA")
        for r in resultados
        if r["esperado"] != r["previsto"]
    )
    if not confusoes:
        return ["Nenhuma confusão."]

    linhas = ["| Esperado | Previsto | Ocorrências |", "|---|---|---|"]
    for (esperado, previsto), quantidade in confusoes.most_common():
        linhas.append(f"| {esperado} | {previsto} | {quantidade} |")
    return linhas


def _tabela_por_intencao(resultados: list[dict]) -> list[str]:
    por_intencao = defaultdict(lambda: [0, 0])
    for r in resultados:
        if r["esperado"] is None:
            continue
        por_intencao[r["esperado"]][1] += 1
        if r["esperado"] == r["previsto"]:
            por_intencao[r["esperado"]][0] += 1

    linhas = ["| Intenção | Acertos | Total | Acurácia |", "|---|---|---|---|"]
    for intencao in sorted(por_intencao):
        certos, total = por_intencao[intencao]
        linhas.append(
            f"| {intencao} | {certos} | {total} | "
            f"{100 * certos / total:.0f}% |"
        )
    return linhas


def main() -> None:
    resultados = avaliar_final()
    m = metricas(resultados)

    print("=" * 72)
    print("AVALIAÇÃO FINAL")
    print("=" * 72)
    print(f"Acurácia geral:      {100 * m['acuracia']:.1f}%")
    print(f"  perguntas normais: {100 * m['acuracia_normal']:.1f}% "
          f"({m['detalhe']['normal'][0]}/{m['detalhe']['normal'][1]})")
    print(f"  com erro de digitação: {100 * m['acuracia_typo']:.1f}% "
          f"({m['detalhe']['typo'][0]}/{m['detalhe']['typo'][1]})")
    print(f"  fora do domínio:   {100 * m['acuracia_fora']:.1f}% "
          f"({m['detalhe']['fora'][0]}/{m['detalhe']['fora'][1]})")
    print(f"Taxa de fallback:    {100 * m['fallback']:.1f}%")

    erros = [r for r in resultados if r["esperado"] != r["previsto"]]
    if erros:
        print("\nERROS:")
        for r in erros:
            print(
                f"  {r['pergunta']!r}\n"
                f"    esperado={r['esperado']} previsto={r['previsto']} "
                f"score={r['score']:.3f} entidades={r['entidades']}"
            )

    print("\nABLAÇÃO (somente perguntas do domínio):")
    abl = ablacao()
    for nome, acuracia in abl:
        print(f"  {nome:32s} {100 * acuracia:5.1f}%")

    print("\nCURVA DO LIMIAR:")
    curva = curva_limiar()
    print("  limiar | geral | domínio | fallback | OOD rejeitado")
    for limiar, geral, dominio, fallback, ood in curva:
        print(f"  {limiar:6.2f} | {100*geral:5.1f}% | {100*dominio:6.1f}% | "
              f"{100*fallback:7.1f}% | {100*ood:5.1f}%")

    # ------------------------------------------------------------ markdown
    linhas = [
        "# Resultados da avaliação",
        "",
        "Perguntas de teste **novas**, que não estão no catálogo de referência.",
        "",
        f"- Total de perguntas: **{m['total']}**",
        f"- Acurácia geral: **{100 * m['acuracia']:.1f}%**",
        f"- Acurácia em perguntas normais: **{100 * m['acuracia_normal']:.1f}%**",
        f"- Acurácia com erro de digitação: **{100 * m['acuracia_typo']:.1f}%**",
        f"- Acerto no rejeite de perguntas fora do domínio: "
        f"**{100 * m['acuracia_fora']:.1f}%**",
        f"- Taxa de fallback: **{100 * m['fallback']:.1f}%**",
        "",
        "## Acurácia por intenção",
        "",
        *_tabela_por_intencao(resultados),
        "",
        "## Confusões",
        "",
        *_tabela_confusoes(resultados),
        "",
        "## Erros detalhados",
        "",
    ]

    if erros:
        for r in erros:
            linhas += [
                f"### `{r['pergunta']}`",
                "",
                f"- Esperado: `{r['esperado']}`",
                f"- Previsto: `{r['previsto']}`",
                f"- Score de cosseno: `{r['score']:.3f}`",
                f"- Entidades: `{r['entidades']}`",
                f"- BOW: `{r['debug']['bow']}`",
                "",
            ]
    else:
        linhas.append("Nenhum erro.")
        linhas.append("")

    linhas += [
        "## Ablação (contribuição de cada etapa)",
        "",
        "| Configuração | Acurácia (domínio) |",
        "|---|---|",
    ]
    for nome, acuracia in abl:
        linhas.append(f"| {nome} | {100 * acuracia:.1f}% |")

    linhas += [
        "",
        "## Curva do limiar",
        "",
        "| Limiar | Acurácia geral | Acurácia domínio | Fallback | "
        "OOD rejeitado |",
        "|---|---|---|---|---|",
    ]
    for limiar, geral, dominio, fallback, ood in curva:
        linhas.append(
            f"| {limiar:.2f} | {100*geral:.1f}% | {100*dominio:.1f}% | "
            f"{100*fallback:.1f}% | {100*ood:.1f}% |"
        )

    linhas += [
        "",
        "## Conclusão",
        "",
        "O limiar escolhido foi **0.30**, que mantém boa acurácia no domínio e "
        "rejeita perguntas fora do domínio. A tabela acima permite justificar "
        "a escolha com números.",
        "",
    ]

    with open("resultados_avaliacao.md", "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas))

    print("\nArquivo gerado: resultados_avaliacao.md")
    print("=" * 72)


if __name__ == "__main__":
    main()
