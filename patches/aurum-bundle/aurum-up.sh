#!/usr/bin/env bash
# Bring Aurum back after reboot / sleep. Safe to run every time.
# Does NOT rebuild images, does NOT touch volumes, does NOT rewrite .env.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ ! -f docker-compose.yml ]]; then
  echo "aurum-up: run this from your Aurum checkout (missing docker-compose.yml)" >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "aurum-up: missing .env — copy from .env.example once, then keep .env forever." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "aurum-up: Docker is not running. On Mac: open Docker Desktop, wait until it is idle, then re-run:" >&2
  echo "  $ROOT/aurum-up.sh" >&2
  exit 1
fi

# restart: unless-stopped already in compose — this just ensures the stack is up.
docker compose up -d

PORT="$(grep -E '^AURUM_WEB_PORT=' .env | cut -d= -f2- || true)"
PORT="${PORT:-3000}"
BIND="$(grep -E '^AURUM_BIND_ADDRESS=' .env | cut -d= -f2- || true)"
BIND="${BIND:-127.0.0.1}"
URL="http://${BIND}:${PORT}"

echo "Waiting for ${URL}/api/health ..."
ok=0
for _ in $(seq 1 40); do
  code="$(curl -sS -o /dev/null -w '%{http_code}' "${URL}/api/health" 2>/dev/null || true)"
  if [[ "$code" == "200" ]]; then
    ok=1
    break
  fi
  # Backend may still be restarting (e.g. right after Docker Desktop wakes).
  sleep 1
done

docker compose ps
echo

if [[ "$ok" -eq 1 ]]; then
  echo "Aurum is up: ${URL}"
  exit 0
fi

echo "aurum-up: health check failed (got HTTP ${code:-none})." >&2
echo "If backend is Restarting with InvalidPasswordError, sync once:" >&2
echo "  PW=\$(grep '^AURUM_POSTGRES_PASSWORD=' .env | cut -d= -f2-)" >&2
echo "  docker compose exec db psql -U aurum -d aurum -c \"ALTER USER aurum WITH PASSWORD '\$PW';\"" >&2
echo "  docker compose up -d --force-recreate backend" >&2
echo "Logs: docker compose logs backend --tail 60" >&2
exit 1
