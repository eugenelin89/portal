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

print(f"export SANITY_ADMIN_USERNAME={ADMIN_USERNAME}")
print(f"export SANITY_ADMIN_PASSWORD={ADMIN_PASSWORD}")
print(f"export SANITY_PLAYER_USERNAME={PLAYER_USERNAME}")
print(f"export SANITY_PLAYER_PASSWORD={PLAYER_PASSWORD}")
print(f"export SANITY_COACH_USERNAME={COACH_USERNAME}")
print(f"export SANITY_COACH_PASSWORD={COACH_PASSWORD}")
print(f"export SANITY_PLAYER_ID={player.id}")
print(f"export SANITY_TEAM_ID={team_bc.id}")
print(f"export SANITY_TRYOUT_ID={tryout.id}")
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
python manage.py runserver 8000 --noreload >/tmp/portal_runserver.log 2>&1 &
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

print_step 29 "Seed Demo Data" "Prompt #10"
check_command_success "seed_demo runs successfully" python manage.py seed_demo

print_step 30 "Load Demo Fixtures" "Prompt #10"
demo_exports=$(python - <<'PY'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transferportal.settings")
django.setup()

from contacts.models import ContactRequest
from organizations.models import Team
from django.contrib.auth import get_user_model

User = get_user_model()

player = User.objects.get(username="player1")
team = Team.objects.get(name="VMB 13U AAA")

ContactRequest.objects.filter(
    player=player,
    requesting_team=team,
    status=ContactRequest.Status.PENDING,
).delete()

print(f"DEMO_PLAYER_ID={player.id}")
print(f"DEMO_TEAM_ID={team.id}")
PY
)

if [[ -n "$demo_exports" ]]; then
  eval "$demo_exports"
  report "demo IDs loaded" "player_id=$DEMO_PLAYER_ID, team_id=$DEMO_TEAM_ID" "yes"
else
  report "demo IDs loaded" "failed to load demo IDs" "no"
  exit 1
fi

print_step 31 "Seeded Tryouts (Public)" "Prompt #10"
check_http 200 http://localhost:8000/api/v1/tryouts/ \
  -H "Host: bc.localhost:8000"

print_step 32 "Seeded Open Players (Coach)" "Prompt #10"
DEMO_COACH_TOKEN=$(get_token "coach1" "coachpass123")
check_http 200 http://localhost:8000/api/v1/open-players/ \
  -H "Authorization: Bearer ${DEMO_COACH_TOKEN}" \
  -H "Host: bc.localhost:8000"

print_step 33 "Seeded Contact Request" "Prompt #10"
check_http 201 http://localhost:8000/api/v1/contact-requests/ \
  -X POST \
  -H "Authorization: Bearer ${DEMO_COACH_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d "{\"player_id\":${DEMO_PLAYER_ID},\"requesting_team_id\":${DEMO_TEAM_ID},\"message\":\"Seed demo contact.\"}"

echo
echo "All sanity checks passed through Prompt #10."

print_step 34 "Isolation Tests (Suite)" "Prompt #11"
check_command_success "permission/isolation tests pass" python manage.py test

echo
echo "All sanity checks passed through Prompt #11."

# -----------------------------------------------------------------------------
# Prompt #12 — Web UI (Bootstrap, responsive templates, dashboards)
# Append-only section: add new checks AFTER Prompt #11.
# -----------------------------------------------------------------------------

print_step 35 "Web UI: Landing Page" "Prompt #12"
check_http 200 http://bc.localhost:8000/

print_step 36 "Web UI: Tryouts List" "Prompt #12"
check_http 200 http://bc.localhost:8000/tryouts/

print_step 37 "Web UI: Tryouts Detail (BC)" "Prompt #12"
check_http 200 "http://bc.localhost:8000/tryouts/${SANITY_TRYOUT_ID}/"

print_step 38 "Web UI: Region Isolation (Tryouts Detail should not leak)" "Prompt #12"
# Same ID under a different host must NOT show BC tryout.
# Depending on implementation, could be 404 or a redirect back to list.
check_http "404|302" "http://localhost:8000/tryouts/${SANITY_TRYOUT_ID}/" \
  -H "Host: on.localhost:8000"

print_step 39 "Web UI: Mobile Viewport Meta Present" "Prompt #12"
# Basic check that templates are mobile-aware (Bootstrap requires viewport meta).
# We check the homepage HTML contains the viewport meta tag.
expected="<meta name=\"viewport\""
set +e
curl -s http://bc.localhost:8000/ | grep -q "<meta name=\"viewport\"" 
viewport_status=$?
set -e
if [[ $viewport_status -eq 0 ]]; then
  report "$expected" "found" "yes"
else
  report "$expected" "missing" "no"
  exit 1
fi

print_step 40 "Web UI: Login Page Loads" "Prompt #12"
# The project may use /accounts/login/ or /login/ depending on urlconf.
# Try both and accept whichever exists.
login_code_a=$(curl -s -o "$TMP_BODY" -w "%{http_code}" http://bc.localhost:8000/accounts/login/)
login_code_b=$(curl -s -o "$TMP_BODY" -w "%{http_code}" http://bc.localhost:8000/login/)
expected="HTTP 200 for /accounts/login/ OR /login/"
result="/accounts/login/=$login_code_a, /login/=$login_code_b"
if [[ "$login_code_a" == "200" || "$login_code_b" == "200" ]]; then
  report "$expected" "$result" "yes"
else
  report "$expected" "$result" "no"
  exit 1
fi

print_step 41 "Web UI: Dashboard Routing (role-aware)" "Prompt #12"
# Use Django test client so we can do a real login + follow redirects.
# This avoids dealing with cookies/CSRF in curl.
check_command_success "dashboard redirects to /player/ for player and /coach/ for coach" \
  python - <<'PY'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transferportal.settings")
django.setup()

from django.test import Client

player_user = os.environ.get("SANITY_PLAYER_USERNAME")
player_pass = os.environ.get("SANITY_PLAYER_PASSWORD")
coach_user = os.environ.get("SANITY_COACH_USERNAME")
coach_pass = os.environ.get("SANITY_COACH_PASSWORD")

assert player_user and player_pass and coach_user and coach_pass

# Player -> /dashboard/ should land on /player/
client = Client(HTTP_HOST="bc.localhost")
logged_in = client.login(username=player_user, password=player_pass)
assert logged_in, "player login failed"
resp = client.get("/dashboard/", follow=False)
assert resp.status_code in (302, 301), f"expected redirect for player, got {resp.status_code}"
loc = resp.get("Location", "")
assert "/player" in loc, f"expected player dashboard redirect, got Location={loc}"

# Coach -> /dashboard/ should land on /coach/
client = Client(HTTP_HOST="bc.localhost")
logged_in = client.login(username=coach_user, password=coach_pass)
assert logged_in, "coach login failed"
resp = client.get("/dashboard/", follow=False)
assert resp.status_code in (302, 301), f"expected redirect for coach, got {resp.status_code}"
loc = resp.get("Location", "")
assert "/coach" in loc, f"expected coach dashboard redirect, got Location={loc}"

print("ok")
PY

print_step 42 "Web UI: Anonymous Dashboard Requires Login" "Prompt #12"
# Anonymous users should be redirected to login.
# Location may include ?next=/dashboard/
check_http "302|301" http://bc.localhost:8000/dashboard/

print_step 43 "Web UI: Tryouts Page Contains Seeded Content" "Prompt #12"
# Soft check that UI list renders something meaningful.
# If seed_demo ran, the demo tryout name should be present.
set +e
curl -s http://bc.localhost:8000/tryouts/ | grep -q "Tryout" 
tryout_grep_status=$?
set -e
if [[ $tryout_grep_status -eq 0 ]]; then
  report "Tryouts list contains visible content" "found 'Tryout'" "yes"
else
  report "Tryouts list contains visible content" "no obvious content" "no"
  exit 1
fi

# End of Prompt #12 section





############################################

# Prompt #13 — Web UI Sanity Checks

############################################

print_step 44 "Web UI Fixture Setup" "Prompt #13"
check_command_success "web UI fixtures ready" \
  python - <<'PY'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transferportal.settings")
django.setup()

from django.contrib.auth import get_user_model
from availability.models import PlayerAvailability
from contacts.models import ContactRequest
from organizations.models import Team
from profiles.models import PlayerProfile
from regions.models import Region

User = get_user_model()

player_user = os.environ.get("SANITY_PLAYER_USERNAME")
team_id = int(os.environ.get("SANITY_TEAM_ID", "0"))

player = User.objects.get(username=player_user)
team = Team.objects.get(id=team_id)
region = Region.objects.get(code="bc")

profile, _ = PlayerProfile.objects.get_or_create(user=player)
if not profile.display_name:
    profile.display_name = "Sanity Player"
    profile.save(update_fields=["display_name"])

availability, _ = PlayerAvailability.objects.get_or_create(player=player, defaults={"region": region})
availability.region = region
availability.is_open = True
availability.is_committed = False
availability.expires_at = None
availability.save(update_fields=["region", "is_open", "is_committed", "expires_at"])
availability.allowed_teams.set([team.id])

ContactRequest.objects.filter(player=player, requesting_team=team).delete()
PY

print_step 45 "Landing Page (Public)" "Prompt #13"
check_http 200 http://bc.localhost:8000/

print_step 46 "Landing Page Mobile Viewport" "Prompt #13"
viewport_check=$(curl -s http://bc.localhost:8000/ | grep -i "viewport" || true)
if [[ -n "$viewport_check" ]]; then
  report "viewport meta tag present" "found" "yes"
else
  report "viewport meta tag present" "missing" "no"
  exit 1
fi

print_step 47 "Public Tryouts Page (Web UI)" "Prompt #13"
check_http 200 http://bc.localhost:8000/tryouts/

print_step 48 "Tryout Detail (Region Isolated)" "Prompt #13"
check_http 200 "http://bc.localhost:8000/tryouts/${SANITY_TRYOUT_ID}/"

print_step 49 "Tryout Detail Cross-Region Block" "Prompt #13"
cross_region_code=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Host: on.localhost:8000" \
  "http://localhost:8000/tryouts/${SANITY_TRYOUT_ID}/")
if [[ "$cross_region_code" == "404" || "$cross_region_code" == "302" ]]; then
  report "cross-region tryout blocked" "HTTP $cross_region_code" "yes"
else
  report "cross-region tryout blocked" "HTTP $cross_region_code" "no"
  exit 1
fi

print_step 50 "Login Page" "Prompt #13"
check_http 200 http://bc.localhost:8000/accounts/login/

print_step 51 "Dashboard Redirect (Anonymous)" "Prompt #13"
check_http "302|301" http://bc.localhost:8000/dashboard/

print_step 52 "Player & Coach Web Flows" "Prompt #13"
check_command_success "player/coach web flows work" \
  python - <<'PY'
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transferportal.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from availability.models import PlayerAvailability
from contacts.models import ContactRequest
from organizations.models import Team

User = get_user_model()

player_user = os.environ.get("SANITY_PLAYER_USERNAME")
player_pass = os.environ.get("SANITY_PLAYER_PASSWORD")
coach_user = os.environ.get("SANITY_COACH_USERNAME")
coach_pass = os.environ.get("SANITY_COACH_PASSWORD")
team_id = int(os.environ.get("SANITY_TEAM_ID", "0"))

player = User.objects.get(username=player_user)
coach = User.objects.get(username=coach_user)
team = Team.objects.get(id=team_id)

client = Client(HTTP_HOST="bc.localhost")
assert client.login(username=player_user, password=player_pass)
resp = client.get("/player/profile/")
assert resp.status_code == 200, f"player profile expected 200, got {resp.status_code}"
resp = client.get("/player/availability/")
assert resp.status_code == 200, f"player availability expected 200, got {resp.status_code}"

resp = client.post(
    "/player/availability/",
    {
        "is_open": "on",
        "positions": ["OF"],
        "levels": ["AAA"],
        "allowed_teams": [team.id],
    },
)
assert resp.status_code in (302, 303), f"availability update expected redirect, got {resp.status_code}"

resp = client.post("/player/availability/commit/", {"action": "commit"})
assert resp.status_code in (302, 303), f"commit expected redirect, got {resp.status_code}"
availability = PlayerAvailability.objects.get(player=player)
assert availability.is_committed is True and availability.is_open is False

resp = client.post("/player/availability/commit/", {"action": "uncommit"})
assert resp.status_code in (302, 303), f"uncommit expected redirect, got {resp.status_code}"
availability.refresh_from_db()
assert availability.is_committed is False
availability.is_open = True
availability.save(update_fields=["is_open"])

client = Client(HTTP_HOST="bc.localhost")
assert client.login(username=coach_user, password=coach_pass)
resp = client.get("/coach/")
assert resp.status_code == 200, f"coach dashboard expected 200, got {resp.status_code}"
resp = client.get("/coach/teams/")
assert resp.status_code == 200, f"coach teams expected 200, got {resp.status_code}"
resp = client.get("/coach/open-players/")
assert resp.status_code == 200, f"coach open players expected 200, got {resp.status_code}"
resp = client.get("/coach/requests/new/")
assert resp.status_code == 200, f"new request form expected 200, got {resp.status_code}"

resp = client.post(
    "/coach/requests/new/",
    {"player": str(player.id), "requesting_team": team.id, "message": "Sanity request"},
)
assert resp.status_code in (302, 303), f"request create expected redirect, got {resp.status_code}"

request_obj = ContactRequest.objects.filter(player=player, requesting_team=team).order_by("-created_at").first()
assert request_obj is not None, "request not created"

client = Client(HTTP_HOST="bc.localhost")
assert client.login(username=player_user, password=player_pass)
resp = client.get("/player/requests/")
assert resp.status_code == 200, f"player requests expected 200, got {resp.status_code}"

resp = client.post(f"/player/requests/{request_obj.id}/respond/", {"status": "approved"})
assert resp.status_code in (302, 303), f"request respond expected redirect, got {resp.status_code}"
request_obj.refresh_from_db()
assert request_obj.status == "approved"

client = Client(HTTP_HOST="bc.localhost")
assert client.login(username=player_user, password=player_pass)
resp = client.get("/coach/")
assert resp.status_code in (302, 403), f"player should be blocked from coach, got {resp.status_code}"

client = Client(HTTP_HOST="bc.localhost")
assert client.login(username=coach_user, password=coach_pass)
resp = client.get("/player/profile/")
assert resp.status_code in (302, 403), f"coach should be blocked from player, got {resp.status_code}"

print("ok")
PY

echo
echo "Web UI sanity checks passed (Prompt #13)."
