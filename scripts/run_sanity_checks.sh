#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TMP_BODY="$(mktemp)"

report() {
  echo "Expected: $1"
  echo "Result: $2"
  echo "Meets expected: $3"
}

print_step() {
  echo
  if [[ -n "${3:-}" ]]; then
    echo "Step $1 ($3): $2"
  else
    echo "Step $1: $2"
  fi
}

check_http() {
  local expected_codes="$1"
  shift
  local http_code
  http_code=$(curl -s -o "$TMP_BODY" -w "%{http_code}" "$@")

  local ok="no"
  if [[ "$expected_codes" == *"|"* ]]; then
    IFS='|' read -r -a codes <<< "$expected_codes"
    for code in "${codes[@]}"; do
      if [[ "$http_code" == "$code" ]]; then
        ok="yes"
      fi
    done
  else
    if [[ "$http_code" == "$expected_codes" ]]; then
      ok="yes"
    fi
  fi

  report "HTTP $expected_codes" "HTTP $http_code" "$ok"
  if [[ "$ok" != "yes" ]]; then
    exit 1
  fi
}

check_command_success() {
  local expected="$1"
  shift
  echo "Expected: $expected"
  set +e
  "$@"
  local status=$?
  set -e
  if [[ $status -eq 0 ]]; then
    report "$expected" "success" "yes"
  else
    report "$expected" "failed (exit $status)" "no"
    exit $status
  fi
}

check_json_empty_array() {
  local expected="$1"
  local result
  result=$(python - <<'PY'
import json
import os

path = os.environ["TMP_BODY_PATH"]
with open(path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)

if isinstance(payload, list) and len(payload) == 0:
    print("yes")
else:
    print("no")
PY
  )
  if [[ "$result" == "yes" ]]; then
    report "$expected" "empty list" "yes"
  else
    report "$expected" "non-empty list" "no"
    exit 1
  fi
}

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID"
  fi
  rm -f "$TMP_BODY"
}
trap cleanup EXIT

print_step 1 "Environment & Dependencies" "Prompt #1"
python_path=$(command -v python || true)
python_version=$(python --version 2>&1 || true)
expected="python on PATH and version >= 3.10"

set +e
python - <<'PY'
import sys
ok = sys.version_info >= (3, 10)
raise SystemExit(0 if ok else 1)
PY
version_status=$?
set -e

if [[ -n "$python_path" && $version_status -eq 0 ]]; then
  report "$expected" "path=$python_path, version=$python_version" "yes"
else
  report "$expected" "path=$python_path, version=$python_version" "no"
  exit 1
fi

print_step 2 "Install & Migrate" "Prompt #1"
check_command_success "Dependencies installed and migrations applied" \
  bash -c "python -m pip install -r requirements.txt && python manage.py migrate"

print_step 3 "Run Tests" "Prompt #1"
check_command_success "All tests pass" python manage.py test

print_step 4 "Create Sanity Fixtures" "Prompt #1"
expected="sanity users, regions, orgs, teams, tryout, availability are ready"
fixture_exports=$(python - <<'PY'
import os
from datetime import date

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transferportal.settings")
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import AccountProfile
from availability.models import PlayerAvailability
from organizations.models import Association, Team, TeamCoach
from regions.models import Region
from tryouts.models import TryoutEvent
from contacts.models import ContactRequest

User = get_user_model()

ADMIN_USERNAME = os.getenv("SANITY_ADMIN_USERNAME", "sanity_admin")
ADMIN_PASSWORD = os.getenv("SANITY_ADMIN_PASSWORD", "sanitypass")
PLAYER_USERNAME = os.getenv("SANITY_PLAYER_USERNAME", "sanity_player")
PLAYER_PASSWORD = os.getenv("SANITY_PLAYER_PASSWORD", "sanitypass")
COACH_USERNAME = os.getenv("SANITY_COACH_USERNAME", "sanity_coach")
COACH_PASSWORD = os.getenv("SANITY_COACH_PASSWORD", "sanitypass")


def get_or_create_user(username, password, is_staff=False):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": f"{username}@example.com"},
    )
    if created:
        user.set_password(password)
    if is_staff:
        user.is_staff = True
        user.is_superuser = True
    user.save()
    return user


player = get_or_create_user(PLAYER_USERNAME, PLAYER_PASSWORD)
player.profile.role = AccountProfile.Roles.PLAYER
player.profile.save()

coach = get_or_create_user(COACH_USERNAME, COACH_PASSWORD)
coach.profile.role = AccountProfile.Roles.COACH
coach.profile.is_coach_approved = True
coach.profile.save()

admin = get_or_create_user(ADMIN_USERNAME, ADMIN_PASSWORD, is_staff=True)

bc = Region.objects.get(code="bc")
on, _ = Region.objects.get_or_create(code="on", defaults={"name": "Ontario", "is_active": True})

assoc_bc, _ = Association.objects.get_or_create(region=bc, name="Sanity Assoc BC")
team_bc, _ = Team.objects.get_or_create(
    region=bc,
    association=assoc_bc,
    name="Sanity Team BC",
    age_group="13U",
)
TeamCoach.objects.get_or_create(user=coach, team=team_bc, defaults={"is_active": True})

assoc_on, _ = Association.objects.get_or_create(region=on, name="Sanity Assoc ON")
Team.objects.get_or_create(
    region=on,
    association=assoc_on,
    name="Sanity Team ON",
    age_group="13U",
)

tryout, _ = TryoutEvent.objects.get_or_create(
    region=bc,
    association=assoc_bc,
    name="Sanity Tryout",
    defaults={
        "start_date": date(2026, 1, 10),
        "end_date": date(2026, 1, 10),
        "location": "Sanity Field",
        "registration_url": "https://example.com",
    },
)

availability, _ = PlayerAvailability.objects.get_or_create(
    player=player,
    defaults={"region": bc},
)
availability.region = bc
availability.is_open = True
availability.is_committed = False
availability.committed_at = None
availability.expires_at = None
availability.save()
availability.allowed_teams.set([team_bc])

ContactRequest.objects.filter(
    player=player,
    requesting_team=team_bc,
).delete()

print(f"SANITY_ADMIN_USERNAME={ADMIN_USERNAME}")
print(f"SANITY_ADMIN_PASSWORD={ADMIN_PASSWORD}")
print(f"SANITY_PLAYER_USERNAME={PLAYER_USERNAME}")
print(f"SANITY_PLAYER_PASSWORD={PLAYER_PASSWORD}")
print(f"SANITY_COACH_USERNAME={COACH_USERNAME}")
print(f"SANITY_COACH_PASSWORD={COACH_PASSWORD}")
print(f"SANITY_PLAYER_ID={player.id}")
print(f"SANITY_TEAM_ID={team_bc.id}")
print(f"SANITY_TRYOUT_ID={tryout.id}")
PY
)

if [[ -n "$fixture_exports" ]]; then
  eval "$fixture_exports"
  report "$expected" "fixtures ready" "yes"
else
  report "$expected" "fixture creation failed" "no"
  exit 1
fi

print_step 5 "Start Server + Health/Auth Checks" "Prompt #1"
expected="server starts and responds to health check"
echo "Expected: $expected"
python manage.py runserver 8000 >/tmp/portal_runserver.log 2>&1 &
SERVER_PID=$!

for i in {1..20}; do
  if curl -s -o /dev/null http://bc.localhost:8000/api/v1/health/; then
    break
  fi
  sleep 0.25
  if [ "$i" -eq 20 ]; then
    report "$expected" "server did not start" "no"
    echo "Check /tmp/portal_runserver.log"
    exit 1
  fi
done
report "$expected" "server started" "yes"

print_step 6 "Health Endpoint" "Prompt #1"
check_http 200 http://bc.localhost:8000/api/v1/health/

print_step 7 "Region / Subdomain Verification" "Prompt #2"
bc_code=$(curl -s -o "$TMP_BODY" -w "%{http_code}" -H "Host: bc.localhost:8000" http://localhost:8000/api/v1/health/)
local_code=$(curl -s -o "$TMP_BODY" -w "%{http_code}" -H "Host: localhost:8000" http://localhost:8000/api/v1/health/)
on_code=$(curl -s -o "$TMP_BODY" -w "%{http_code}" -H "Host: on.localhost:8000" http://localhost:8000/api/v1/health/)
expected="HTTP 200 for bc, localhost, and on"
result="bc=$bc_code, localhost=$local_code, on=$on_code"
if [[ "$bc_code" == "200" && "$local_code" == "200" && "$on_code" == "200" ]]; then
  report "$expected" "$result" "yes"
else
  report "$expected" "$result" "no"
  exit 1
fi

print_step 8 "ALLOWED_HOSTS" "Prompt #2"
allowed_hosts=$(python - <<'PY'
from transferportal.settings import ALLOWED_HOSTS
print(",".join(ALLOWED_HOSTS))
PY
)
set +e
python - <<'PY'
from transferportal.settings import ALLOWED_HOSTS
required = {".localhost", "localhost", "127.0.0.1"}
raise SystemExit(0 if required.issubset(set(ALLOWED_HOSTS)) else 1)
PY
hosts_status=$?
set -e
if [[ $hosts_status -eq 0 ]]; then
  report "ALLOWED_HOSTS includes .localhost, localhost, 127.0.0.1" "$allowed_hosts" "yes"
else
  report "ALLOWED_HOSTS includes .localhost, localhost, 127.0.0.1" "$allowed_hosts" "no"
  exit 1
fi

get_token() {
  local username="$1"
  local password="$2"
  local response
  response=$(curl -s -X POST http://bc.localhost:8000/api/v1/auth/token/ \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${username}\",\"password\":\"${password}\"}")
  TOKEN_RESPONSE="$response" python - <<'PY'
import json
import os

payload = json.loads(os.environ.get("TOKEN_RESPONSE", "{}"))
print(payload.get("access", ""))
PY
}

SANITY_USERNAME=${SANITY_USERNAME:-$SANITY_ADMIN_USERNAME}
SANITY_PASSWORD=${SANITY_PASSWORD:-$SANITY_ADMIN_PASSWORD}
SANITY_ACCESS_TOKEN=${SANITY_ACCESS_TOKEN:-""}
SANITY_PLAYER_TOKEN=${SANITY_PLAYER_TOKEN:-""}
SANITY_COACH_TOKEN=${SANITY_COACH_TOKEN:-""}
SANITY_NON_PLAYER_TOKEN=${SANITY_NON_PLAYER_TOKEN:-""}

if [[ -z "$SANITY_ACCESS_TOKEN" ]]; then
  SANITY_ACCESS_TOKEN=$(get_token "$SANITY_ADMIN_USERNAME" "$SANITY_ADMIN_PASSWORD")
fi
if [[ -z "$SANITY_PLAYER_TOKEN" ]]; then
  SANITY_PLAYER_TOKEN=$(get_token "$SANITY_PLAYER_USERNAME" "$SANITY_PLAYER_PASSWORD")
fi
if [[ -z "$SANITY_COACH_TOKEN" ]]; then
  SANITY_COACH_TOKEN=$(get_token "$SANITY_COACH_USERNAME" "$SANITY_COACH_PASSWORD")
fi
if [[ -z "$SANITY_NON_PLAYER_TOKEN" ]]; then
  SANITY_NON_PLAYER_TOKEN="$SANITY_COACH_TOKEN"
fi

print_step 9 "JWT Protected Endpoint" "Prompt #1"
if [[ -n "$SANITY_ACCESS_TOKEN" ]]; then
  check_http 200 http://bc.localhost:8000/api/v1/protected/ \
    -H "Authorization: Bearer $SANITY_ACCESS_TOKEN"
else
  report "HTTP 200" "token missing" "no"
  exit 1
fi

print_step 10 "/api/v1/me/" "Prompt #3"
check_http 200 http://bc.localhost:8000/api/v1/me/ \
  -H "Authorization: Bearer $SANITY_ACCESS_TOKEN"

print_step 11 "Associations (BC)" "Prompt #4"
check_http 200 http://localhost:8000/api/v1/associations/ \
  -H "Authorization: Bearer ${SANITY_ACCESS_TOKEN}" \
  -H "Host: bc.localhost:8000"

print_step 12 "Teams (BC)" "Prompt #4"
check_http 200 http://localhost:8000/api/v1/teams/ \
  -H "Authorization: Bearer ${SANITY_ACCESS_TOKEN}" \
  -H "Host: bc.localhost:8000"

print_step 13 "Associations (ON)" "Prompt #4"
check_http 200 http://localhost:8000/api/v1/associations/ \
  -H "Authorization: Bearer ${SANITY_ACCESS_TOKEN}" \
  -H "Host: on.localhost:8000"

print_step 14 "Tryouts List (BC)" "Prompt #5"
check_http 200 http://localhost:8000/api/v1/tryouts/ \
  -H "Host: bc.localhost:8000"

print_step 15 "Tryouts Detail (BC)" "Prompt #5"
check_http 200 "http://localhost:8000/api/v1/tryouts/${SANITY_TRYOUT_ID}/" \
  -H "Host: bc.localhost:8000"

print_step 16 "Tryouts List (ON)" "Prompt #5"
check_http 200 http://localhost:8000/api/v1/tryouts/ \
  -H "Host: on.localhost:8000"

print_step 17 "Tryouts Write Restriction" "Prompt #5"
check_http "401|403" http://localhost:8000/api/v1/tryouts/ \
  -X POST \
  -H "Host: bc.localhost:8000" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Tryout","start_date":"2026-01-10","end_date":"2026-01-10","location":"Test","registration_url":"https://example.com","association":1,"region":1}'

print_step 18 "Availability Me (Player)" "Prompt #6"
check_http 200 http://localhost:8000/api/v1/availability/me/ \
  -X PATCH \
  -H "Authorization: Bearer ${SANITY_PLAYER_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d '{"is_open": true, "positions": ["OF"], "levels": ["AAA"]}'

print_step 19 "Availability Search (Coach/Admin)" "Prompt #6"
check_http 200 http://localhost:8000/api/v1/availability/search/ \
  -H "Authorization: Bearer ${SANITY_COACH_TOKEN}" \
  -H "Host: bc.localhost:8000"

print_step 20 "Contact Request Create" "Prompt #7"
contact_create_code=$(curl -s -o "$TMP_BODY" -w "%{http_code}" \
  -X POST http://localhost:8000/api/v1/contact-requests/ \
  -H "Authorization: Bearer ${SANITY_COACH_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d "{\"player_id\":${SANITY_PLAYER_ID},\"requesting_team_id\":${SANITY_TEAM_ID},\"message\":\"We would like to connect.\"}")
if [[ "$contact_create_code" == "201" ]]; then
  SANITY_CONTACT_REQUEST_ID=$(TMP_BODY_PATH="$TMP_BODY" python - <<'PY'
import json

import os

with open(os.environ["TMP_BODY_PATH"], "r", encoding="utf-8") as handle:
    payload = json.load(handle)
print(payload.get("id", ""))
PY
  )
  report "HTTP 201" "HTTP $contact_create_code" "yes"
else
  report "HTTP 201" "HTTP $contact_create_code" "no"
  exit 1
fi

print_step 21 "Contact Request Respond (Approve)" "Prompt #7"
check_http 200 http://localhost:8000/api/v1/contact-requests/${SANITY_CONTACT_REQUEST_ID}/respond/ \
  -X POST \
  -H "Authorization: Bearer ${SANITY_PLAYER_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d '{"status":"approved"}'

print_step 22 "Contact Request Respond (Decline)" "Prompt #7"
contact_decline_code=$(curl -s -o "$TMP_BODY" -w "%{http_code}" \
  -X POST http://localhost:8000/api/v1/contact-requests/ \
  -H "Authorization: Bearer ${SANITY_COACH_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d "{\"player_id\":${SANITY_PLAYER_ID},\"requesting_team_id\":${SANITY_TEAM_ID},\"message\":\"Second request.\"}")
if [[ "$contact_decline_code" == "201" ]]; then
  decline_id=$(TMP_BODY_PATH="$TMP_BODY" python - <<'PY'
import json

import os

with open(os.environ["TMP_BODY_PATH"], "r", encoding="utf-8") as handle:
    payload = json.load(handle)
print(payload.get("id", ""))
PY
  )
  check_http 200 http://localhost:8000/api/v1/contact-requests/${decline_id}/respond/ \
    -X POST \
    -H "Authorization: Bearer ${SANITY_PLAYER_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Host: bc.localhost:8000" \
    -d '{"status":"declined"}'
else
  report "HTTP 201" "HTTP $contact_decline_code" "no"
  exit 1
fi

print_step 23 "Profile Me (Player)" "Prompt #8"
check_http 200 http://localhost:8000/api/v1/profile/me/ \
  -H "Authorization: Bearer ${SANITY_PLAYER_TOKEN}" \
  -H "Host: bc.localhost:8000"
check_http 200 http://localhost:8000/api/v1/profile/me/ \
  -X PATCH \
  -H "Authorization: Bearer ${SANITY_PLAYER_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d '{"display_name":"J. Player","birth_year":2011,"positions":["OF"],"bats":"R","throws":"R"}'

print_step 24 "Profile Me (Non-Player)" "Prompt #8"
check_http 403 http://localhost:8000/api/v1/profile/me/ \
  -H "Authorization: Bearer ${SANITY_NON_PLAYER_TOKEN}" \
  -H "Host: bc.localhost:8000"

print_step 25 "Profiles List (Should 404)" "Prompt #8"
check_http 404 http://localhost:8000/api/v1/profiles/

print_step 26 "Committed: Player Commits" "Prompt #9"
check_http 200 http://localhost:8000/api/v1/availability/me/ \
  -X PATCH \
  -H "Authorization: Bearer ${SANITY_PLAYER_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d '{"is_committed": true}'

print_step 27 "Committed: Open Players Search Excludes Committed" "Prompt #9"
open_players_code=$(curl -s -o "$TMP_BODY" -w "%{http_code}" \
  http://localhost:8000/api/v1/open-players/ \
  -H "Authorization: Bearer ${SANITY_COACH_TOKEN}" \
  -H "Host: bc.localhost:8000")
if [[ "$open_players_code" == "200" ]]; then
  TMP_BODY_PATH="$TMP_BODY" check_json_empty_array "Empty list (committed excluded)"
else
  report "HTTP 200" "HTTP $open_players_code" "no"
  exit 1
fi

print_step 28 "Committed: Contact Request Blocked" "Prompt #9"
check_http 400 http://localhost:8000/api/v1/contact-requests/ \
  -X POST \
  -H "Authorization: Bearer ${SANITY_COACH_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d "{\"player_id\":${SANITY_PLAYER_ID},\"requesting_team_id\":${SANITY_TEAM_ID},\"message\":\"Committed check.\"}"

echo
echo "All sanity checks passed."
