"""Aplicação Flask de página única."""
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

from motor import buscar, estatisticas  # noqa: E402

app = Flask(__name__)
app.json.ensure_ascii = False

EXEMPLOS = [
    "Quantas imagens existem?",
    "Quais imagens possuem vegetação?",
    "Imagens de drone em 2024",
    "Imagens de água por satélite",
    "Quantas imagens de solo exposto existem?",
    "Qual a imagem mais recente?",
    "Quais origens existem?",
    "Imagens de vegetação por drone em 2023",
    "Imagens de vejetassão por drono em 2024",
    "Qual a capital da França?",
]


@app.get("/")
def index():
    return render_template("index.html", exemplos=EXEMPLOS)


@app.get("/api/health")
def health():
    try:
        return jsonify({"status": "ok", **estatisticas()})
    except Exception as erro:  # pragma: no cover
        app.logger.exception("Falha no health check")
        return jsonify({"status": "erro", "detalhe": str(erro)}), 500


@app.get("/api/exemplos")
def exemplos():
    return jsonify(EXEMPLOS)


@app.post("/api/busca")
def api_busca():
    dados = request.get_json(silent=True) or {}
    pergunta = (dados.get("pergunta") or "").strip()

    if not pergunta:
        return jsonify({"erro": "Digite uma pergunta."}), 400
    if len(pergunta) > 300:
        return jsonify({"erro": "Pergunta muito longa."}), 400

    try:
        return jsonify(buscar(pergunta))
    except Exception:  # pragma: no cover
        app.logger.exception("Erro na busca")
        return jsonify({"erro": "Erro interno ao consultar o banco."}), 500


if __name__ == "__main__":
    porta = int(os.getenv("PORT", "5000"))
    app.run(host="127.0.0.1", port=porta, debug=True)
