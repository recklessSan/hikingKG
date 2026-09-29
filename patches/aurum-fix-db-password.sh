#!/usr/bin/env bash
# One-time: set Postgres password to match .env (does not delete data).
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /path/to/Aurum" >&2
  exit 1
fi

AURUM="$(cd "$1" && pwd)"
cd "$AURUM"

if [[ ! -f .env ]]; then
  echo "Missing $AURUM/.env" >&2
  exit 1
fi

USER_NAME="$(grep -E '^AURUM_POSTGRES_USER=' .env | cut -d= -f2- || true)"
USER_NAME="${USER_NAME:-aurum}"
DB_NAME="$(grep -E '^AURUM_POSTGRES_DB=' .env | cut -d= -f2- || true)"
DB_NAME="${DB_NAME:-aurum}"
PW="$(grep -E '^AURUM_POSTGRES_PASSWORD=' .env | cut -d= -f2-)"

if [[ -z "$PW" ]]; then
  echo "AURUM_POSTGRES_PASSWORD is empty in .env" >&2
  exit 1
fi

echo "Setting password for role ${USER_NAME} in database ${DB_NAME} (data kept)..."
docker compose exec -T db psql -U "$USER_NAME" -d "$DB_NAME" \
  -c "ALTER USER ${USER_NAME} WITH PASSWORD '${PW}';"

docker compose up -d --force-recreate backend
echo "Done. Run: ${AURUM}/aurum-up.sh"
