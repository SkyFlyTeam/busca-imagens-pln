"""Mostra o pipeline de PLN passo a passo no terminal."""
from pln import detalhar

FRASES = [
    "Quais imagens possuem vegetação?",
    "Imagens de vejetassão por drono em 2024",
    "Quantas imagens de água existem?",
]


def main() -> None:
    for frase in FRASES:
        d = detalhar(frase)
        print("=" * 70)
        print("Entrada:            ", d["entrada"])
        print("1. normalizada:     ", d["normalizado"])
        print("2. corrigida:       ", d["corrigido"])
        print("3. canônica:        ", d["canonico"])
        print("4. tokens:          ", d["tokens"])
        print("5. sem stopwords:   ", d["tokens_sem_stopwords"])
        print("6. stems (BOW):     ", d["stems"])
        print("7. texto do BOW:    ", d["bow"])
    print("=" * 70)


if __name__ == "__main__":
    main()
