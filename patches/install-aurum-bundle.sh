#!/usr/bin/env bash
# Copy Aurum feature files into an Aurum repo checkout (no git apply).
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /path/to/Aurum"
  exit 1
fi

AURUM="$(cd "$1" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE="$SCRIPT_DIR/aurum-bundle"

if [[ ! -d "$BUNDLE" ]]; then
  echo "Missing bundle at $BUNDLE"
  exit 1
fi

if [[ ! -f "$AURUM/docker-compose.yml" ]] || [[ ! -d "$AURUM/frontend" ]] || [[ ! -d "$AURUM/backend" ]]; then
  echo "Does not look like an Aurum repo: $AURUM"
  exit 1
fi

echo "Installing into $AURUM"
cd "$BUNDLE"
find . -type f | while read -r f; do
  rel="${f#./}"

  # Never overwrite local secrets / env the user already tuned.
  case "$rel" in
    .env|.env.local|.env.*.local)
      echo "  skip $rel (local secrets)"
      continue
      ;;
    .env.example)
      if [[ -f "$AURUM/$rel" ]]; then
        echo "  skip $rel (already exists — not overwriting your template)"
        continue
      fi
      ;;
  esac

  mkdir -p "$AURUM/$(dirname "$rel")"
  cp "$rel" "$AURUM/$rel"
  echo "  wrote $rel"
done

echo
echo "Done. Your .env was left untouched."
echo "Rebuild:"
echo "  cd \"$AURUM\" && docker compose up -d --build"
