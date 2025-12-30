#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python >/dev/null 2>&1; then
  echo "python not found on PATH"
  exit 1
fi

python -m pip install -r requirements.txt
python manage.py migrate
python manage.py test

echo "Starting dev server for health/auth checks..."
python manage.py runserver 8000 >/tmp/portal_runserver.log 2>&1 &
SERVER_PID=$!

cleanup() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID"
  fi
}
trap cleanup EXIT

for i in {1..20}; do
  if curl -s -o /dev/null http://bc.localhost:8000/api/v1/health/; then
    break
  fi
  sleep 0.25
  if [ "$i" -eq 20 ]; then
    echo "Server did not start. Check /tmp/portal_runserver.log"
    exit 1
  fi
done

curl -s -i http://bc.localhost:8000/api/v1/health/

if [[ -n "${SANITY_USERNAME:-}" && -n "${SANITY_PASSWORD:-}" ]]; then
  token_response=$(curl -s -X POST http://bc.localhost:8000/api/v1/auth/token/ \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${SANITY_USERNAME}\",\"password\":\"${SANITY_PASSWORD}\"}")

  access_token=$(TOKEN_RESPONSE="$token_response" python - <<'PY'
import json
import os

payload = json.loads(os.environ.get("TOKEN_RESPONSE", "{}"))
print(payload.get("access", ""))
PY
  )

  if [[ -n "$access_token" ]]; then
    curl -s http://bc.localhost:8000/api/v1/protected/ \
      -H "Authorization: Bearer $access_token"
  else
    echo "Could not parse access token. Response: $token_response"
  fi
else
  echo "Set SANITY_USERNAME and SANITY_PASSWORD to run JWT protected check."
fi
