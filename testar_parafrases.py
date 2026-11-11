"""Sanidade do catálogo: cada paráfrase deve eleger a própria intenção.

Isto NÃO mede generalização (a paráfrase está no próprio catálogo).
A avaliação com perguntas novas está em avaliacao.py.
"""
from intencoes import INTENCOES
from motor import classificar


def main() -> None:
    total = 0
    erros = 0

    for intencao in INTENCOES:
        for parafrase in intencao["parafrases"]:
            total += 1
            resultado = classificar(parafrase)
            previsto = (
                resultado["intencao"]["id"] if resultado["intencao"] else None
            )
            if previsto != intencao["id"]:
                erros += 1
                print(
                    f"ERRO: {intencao['id']:32s} -> {str(previsto):32s} "
                    f"| {parafrase}"
                )

    acertos = total - erros
    print(f"\n{acertos}/{total} paráfrases corretas "
          f"({100 * acertos / total:.1f}%)")


if __name__ == "__main__":
    main()
