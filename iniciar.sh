#!/usr/bin/env bash
# Sobe o banco (Docker), prepara o ambiente, popula os dados e inicia o site.
# Uso: ./iniciar.sh
set -euo pipefail
cd "$(dirname "$0")"

PORTA="${PORT:-5000}"

if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "============================================================"
echo "  Busca de Imagens — PLN (BOW + cosseno)"
echo "============================================================"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERRO: Docker não encontrado. Instale o Docker para rodar o PostgreSQL."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERRO: o Docker não está rodando. Inicie o Docker e tente novamente."
  exit 1
fi

if docker inspect pgsem >/dev/null 2>&1; then
  docker start pgsem >/dev/null 2>&1 || true
else
  echo "Criando o container PostgreSQL (só na primeira vez)..."
  docker run -d --name pgsem --restart unless-stopped \
    -e POSTGRES_USER=sem -e POSTGRES_PASSWORD=sem123 \
    -e POSTGRES_DB=imagens_db -p 5433:5432 postgres:16 >/dev/null
fi

echo -n "Aguardando o PostgreSQL"
pronto=0
for _ in $(seq 1 40); do
  if docker exec pgsem pg_isready -U sem -d imagens_db >/dev/null 2>&1; then
    echo " pronto."
    pronto=1
    break
  fi
  echo -n "."
  sleep 1
done
if [ "$pronto" -ne 1 ]; then
  echo
  echo "ERRO: o PostgreSQL não respondeu em 40 segundos."
  echo "Verifique com: docker logs pgsem"
  exit 1
fi

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" >/dev/null 2>&1; then
  echo "ERRO: Python 3.12+ é necessário. Instale uma versão mais recente."
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  echo "Criando ambiente Python..."
  python3 -m venv .venv
fi

if ! .venv/bin/python -c "import flask, psycopg2, sklearn, nltk, rapidfuzz" >/dev/null 2>&1; then
  echo "Instalando dependências..."
  .venv/bin/pip install --quiet -r requirements.txt
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Populando o banco e gerando as imagens de exemplo..."
python seed.py

echo
echo "Abra no navegador:  http://127.0.0.1:${PORTA}"
echo "Para encerrar:      Ctrl+C"
echo

# abre o navegador depois de 2 segundos, sem travar o servidor
(
  sleep 2
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://127.0.0.1:${PORTA}" >/dev/null 2>&1 || true
  fi
) &

exec flask --app app run --host 127.0.0.1 --port "${PORTA}"
