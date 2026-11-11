"""Cria a tabela, popula o banco e gera imagens de exemplo.

Uso:
    python seed.py

É determinístico: rodar de novo recria exatamente o mesmo catálogo.
"""
import os
import random
from datetime import date
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFilter, ImageFont

load_dotenv()

BASE = Path(__file__).parent
PASTA_IMAGENS = BASE / "static" / "imagens"
PASTA_IMAGENS.mkdir(parents=True, exist_ok=True)

URL = os.getenv(
    "DATABASE_URL", "postgresql://sem:sem123@localhost:5433/imagens_db"
)

CATEGORIAS = ["vegetacao", "solo_exposto", "agua"]
ORIGENS = ["satelite", "drone"]

PALETAS = {
    "vegetacao": [
        (28, 78, 42), (42, 102, 52), (62, 122, 58),
        (24, 66, 36), (82, 132, 66), (36, 90, 48),
    ],
    "agua": [
        (16, 54, 104), (22, 74, 132), (30, 96, 156),
        (12, 42, 84), (40, 108, 168), (24, 86, 144),
    ],
    "solo_exposto": [
        (118, 88, 54), (148, 114, 74), (98, 72, 44),
        (168, 138, 98), (88, 64, 40), (136, 104, 66),
    ],
}

CODIGO = {"vegetacao": "VEG", "solo_exposto": "SOL", "agua": "AGU"}

# Fontes comuns em Linux e Windows. Se nenhuma existir, usa a fonte padrão do
# Pillow (menor, mas mantém o script funcionando em qualquer sistema).
FONTES_NEGRITO = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
]
FONTES_NORMAL = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/calibri.ttf",
]


def _carregar_fonte(candidatos: list[str], tamanho: int):
    for caminho in candidatos:
        try:
            return ImageFont.truetype(caminho, tamanho)
        except OSError:
            continue
    return ImageFont.load_default()


FONTE = _carregar_fonte(FONTES_NEGRITO, 24)
FONTE_PEQUENA = _carregar_fonte(FONTES_NORMAL, 13)


def gerar_imagem(categoria: str, indice: int, data_img: date, origem: str) -> Path:
    """Gera um tile sintético com aparência de imagem de sensoriamento remoto."""
    rng = random.Random(indice * 7919)
    largura, altura = 480, 320
    paleta = PALETAS[categoria]

    img = Image.new("RGB", (largura, altura), paleta[0])
    draw = ImageDraw.Draw(img, "RGBA")

    # textura de terreno
    for _ in range(180):
        x = rng.randint(-30, largura + 30)
        y = rng.randint(-30, altura + 30)
        rx = rng.randint(8, 55)
        ry = rng.randint(6, 40)
        cor = rng.choice(paleta)
        alpha = rng.randint(30, 110)
        draw.ellipse((x - rx, y - ry, x + rx, y + ry), fill=(*cor, alpha))

    if categoria == "agua":
        # faixas horizontais lembrando ondas/correntes
        for y in range(0, altura, 14):
            desloc = rng.randint(-3, 3)
            draw.line(
                [(0, y + desloc), (largura, y + desloc + rng.randint(-2, 2))],
                fill=(*rng.choice(paleta), 40),
                width=rng.randint(1, 3),
            )

    img = img.filter(ImageFilter.GaussianBlur(radius=0.7))
    draw = ImageDraw.Draw(img)

    # grade sutil de tile de satélite
    for x in range(0, largura, 80):
        draw.line([(x, 0), (x, altura)], fill=(255, 255, 255, 16), width=1)
    for y in range(0, altura, 80):
        draw.line([(0, y), (largura, y)], fill=(255, 255, 255, 16), width=1)

    # barra inferior com metadados
    draw.rectangle((0, altura - 46, largura, altura), fill=(0, 0, 0, 135))
    titulo = f"{CODIGO[categoria]}-{indice:02d}"
    draw.text((12, altura - 40), titulo, font=FONTE, fill=(255, 255, 255))
    info = f"{data_img.strftime('%d/%m/%Y')}  |  {origem}"
    draw.text((120, altura - 33), info, font=FONTE_PEQUENA, fill=(235, 235, 235))

    caminho = PASTA_IMAGENS / f"img_{indice:02d}.jpg"
    img.save(caminho, quality=88)
    return caminho


def main() -> None:
    random.seed(42)

    conn = psycopg2.connect(URL)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute((BASE / "schema.sql").read_text(encoding="utf-8"))

    registros = []
    for i in range(60):
        numero = i + 1
        categoria = CATEGORIAS[i % 3]
        origem = ORIGENS[(i // 3) % 2]
        ano = 2021 + (i // 6) % 5
        mes = (i % 12) + 1
        dia = (i * 7) % 27 + 1
        data_img = date(ano, mes, dia)
        caminho = f"static/imagens/img_{numero:02d}.jpg"

        registros.append((categoria, data_img, origem, caminho))
        gerar_imagem(categoria, numero, data_img, origem)

    cur.executemany(
        "INSERT INTO metadata_table "
        "(categoria, data_imagem, origem, caminho_arquivo, descricao) "
        "VALUES (%s, %s, %s, %s, %s)",
        [
            (
                categoria,
                data_img,
                origem,
                caminho,
                f"Imagem de {categoria} capturada por {origem} "
                f"em {data_img.strftime('%d/%m/%Y')}.",
            )
            for categoria, data_img, origem, caminho in registros
        ],
    )

    cur.execute("SELECT count(*) FROM metadata_table;")
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT categoria, count(*) FROM metadata_table GROUP BY categoria "
        "ORDER BY categoria;"
    )
    por_categoria = cur.fetchall()

    cur.execute(
        "SELECT origem, count(*) FROM metadata_table GROUP BY origem "
        "ORDER BY origem;"
    )
    por_origem = cur.fetchall()

    cur.close()
    conn.close()

    print(f"Banco populado: {total} imagens.")
    print("Por categoria:", dict(por_categoria))
    print("Por origem:   ", dict(por_origem))
    print(f"Imagens geradas em: {PASTA_IMAGENS}")


if __name__ == "__main__":
    main()
