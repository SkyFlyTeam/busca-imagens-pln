"""Compara Bag of Words puro (contagem) com TF-IDF usando cosseno."""
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from intencoes import INTENCOES
from pln import processar

PERGUNTA = "Mostre imagens com vegetação"


def avaliar(nome: str, vetorizador) -> None:
    textos, donos = [], []
    for intencao in INTENCOES:
        for parafrase in intencao["parafrases"]:
            textos.append(processar(parafrase))
            donos.append(intencao["id"])

    matriz = vetorizador.fit_transform(textos)
    vetor = vetorizador.transform([processar(PERGUNTA)])
    scores = cosine_similarity(vetor, matriz)[0]

    melhor_por_intencao: dict[str, float] = {}
    for i, dono in enumerate(donos):
        melhor_por_intencao[dono] = max(
            melhor_por_intencao.get(dono, 0.0), float(scores[i])
        )

    ranking = sorted(
        melhor_por_intencao.items(), key=lambda item: item[1], reverse=True
    )[:3]

    print(f"\n=== {nome} ===")
    print("pergunta processada:", processar(PERGUNTA))
    for intencao, score in ranking:
        print(f"  {intencao:35s} {score:.3f}")
    print("  vencedor:", ranking[0][0])


def main() -> None:
    avaliar(
        "BOW puro (CountVectorizer)",
        CountVectorizer(
            lowercase=False, tokenizer=str.split, preprocessor=None,
            token_pattern=None,
        ),
    )
    avaliar(
        "TF-IDF",
        TfidfVectorizer(
            lowercase=False, tokenizer=str.split, preprocessor=None,
            token_pattern=None,
        ),
    )


if __name__ == "__main__":
    main()
