# CODEX_TASKS.md — MVP Build Plan (BC Baseball Transfer Portal)

Use this as the **single source of truth** for Codex/agent work. Tasks are ordered to keep the project runnable end-to-end as early as possible.

**Day 1 decision:** Build **DRF endpoints from day 1** alongside the Django web UI. The API becomes the source-of-truth for data access and permissions, enabling a future mobile app without rewrites.

Each task includes:
- **Goal** (what “done” means)
- **Files/Areas** (where changes likely happen)
- **Acceptance Checks** (how to verify)

---

## 0. Repo Bootstrap

### Task 0.1 — Initialize Django Project
**Goal:** A running Django project with a home page.
- Create repo structure
- Add `.gitignore`, `requirements.txt`, `manage.py`
- Create project `transferportal` (or `config`) and app skeletons

**Files/Areas:** `manage.py`, `transferportal/settings.py`, `urls.py`, `templates/`

**Acceptance Checks:**
- `python manage.py runserver` works
- Visiting `http://bc.localhost:8000/` returns a simple page

---

### Task 0.2 — Add Base UI + Mobile-Responsive Layout
**Goal:** A base template and simple navigation that looks OK on mobile.

**Files/Areas:** `templates/base.html`, `static/`, CSS framework choice (Bootstrap or Tailwind)

**Acceptance Checks:**
- Nav works on mobile width
- No broken styling
- Homepage includes association dropdown for the current region
- Homepage includes a hero banner image

---

### Task 0.3 — Add Django REST Framework + API Skeleton (Day 1)
**Goal:** DRF installed and a versioned API base is live.

**Includes:**
- Add `djangorestframework` to `requirements.txt`
- Create `api` app
- Add `/api/v1/health/` endpoint
- Add router structure for viewsets

**Files/Areas:** `requirements.txt`, `transferportal/settings.py`, `api/urls.py`, `transferportal/urls.py`

**Acceptance Checks:**
- `GET /api/v1/health/` returns `{ "status": "ok" }`

---

### Task 0.4 — API Authentication (Day 1)
**Goal:** API supports authentication for protected endpoints.

**MVP choice (pick one):**
- **Option A:** DRF Token Auth (fastest)
- **Option B:** JWT (SimpleJWT) (best for mobile)

**Files/Areas:** auth endpoints, settings, minimal docs

**Acceptance Checks:**
- Can obtain token/JWT and call a protected endpoint

---

## 1. Regional Subdomain Foundation (MVP: BC only)

### Task 1.1 — Implement Region Model (BC only)
**Goal:** Add `Region` model and seed BC region.

**Files/Areas:** `regions/models.py`, `regions/admin.py`, `migrations/`, optional `fixtures/`

**Acceptance Checks:**
- `Region(code='bc')` exists after setup (fixture or admin)

---

### Task 1.2 — Subdomain Middleware (request.region)
**Goal:** Parse host (e.g., `bc.localhost`) and set `request.region='bc'`.

**Files/Areas:** `middleware/region.py`, `settings.MIDDLEWARE`

**Acceptance Checks:**
- Requests to `bc.localhost` set region=bc
- Non-region hosts still work (fallback to bc or show landing)

---

### Task 1.3 — Region-Aware API Context
**Goal:** DRF requests also have region context for filtering.

**Approach:**
- Ensure DRF views run after middleware
- Provide a helper (e.g., `get_request_region(request)`) used by viewsets

**Acceptance Checks:**
- API list endpoints return only region-scoped objects for the current subdomain

---

## 2. Accounts & Roles

### Task 2.1 — Custom User Model (Optional) OR Role Profile
**Goal:** Support roles: Player/Parent, Coach/Manager, Admin.

**Approach:**
- Option A: Extend Django User with a Profile model holding role
- Option B: Custom User model with role field (if starting fresh)

**Files/Areas:** `accounts/models.py`, `settings.AUTH_USER_MODEL` (if custom)

**Acceptance Checks:**
- New users can register and log in
- Role stored and retrievable

---

### Task 2.2 — Coach Approval Workflow
**Goal:** Coach accounts require admin approval before posting tryouts.

**Files/Areas:** `accounts/models.py` (e.g., `is_approved`), `admin.py`, view guards

**Acceptance Checks:**
- Coach cannot access tryout create until approved
- Admin can approve coach in Django admin

---

### Task 2.3 — API Auth Endpoints
**Goal:** API endpoints for login/session equivalent.

**Includes:**
- Token/JWT obtain endpoints
- Optional: `/api/v1/me/` returns current user + role + approval status

**Acceptance Checks:**
- Mobile client can authenticate and fetch `/api/v1/me/`

---

### Task 2.4 — API Permissions (RBAC)
**Goal:** DRF permission classes enforce roles and coach approval.

**Examples:**
- Admin-only endpoints
- Approved-coach-required endpoints
- Self-only endpoints for player profile and availability

**Acceptance Checks:**
- Unauthorized calls return 401/403 appropriately

---

## 3. Associations, Teams (Region-Scoped)

### Task 3.1 — Association + Team Models
**Goal:** Add region-scoped `Association` and `Team`.

**Fields (suggested):**
- Association: `name`, `region`, optional public info (website, description, contact)
- Team: `association`, `name`, `age_group`, `level`, `region` (derived or explicit)

**Files/Areas:** `leagues/models.py` (or `orgs/models.py`), `admin.py`

**Acceptance Checks:**
- Admin can create associations and teams for BC

### Task 3.3 — Association Info Page (Web UI)
**Goal:** Public association detail page with admin-managed details.

**Files/Areas:** `organizations/models.py`, `organizations/admin.py`, `organizations/web_views.py`, templates

**Acceptance Checks:**
- Association page renders in the current region
- Links appear from tryout list/detail and coach teams
- Association page lists upcoming tryouts (if any)
- Logo displays when URL is set (recommended square, 200–800px)

---

### Task 3.2 — Coach-Team Membership
**Goal:** Restrict coaches to teams they are assigned to.

**Files/Areas:** membership model (e.g., `TeamCoach`), admin, query helpers

**Acceptance Checks:**
- Coach can only post tryouts for assigned team

---

## 4. Tryout Listings (Core MVP)

### Task 4.1 — TryoutEvent Model (Region-Scoped)
**Goal:** Create tryout event model tied to team + region.

**Fields (suggested):**
- `team`, `region`, `title` (optional)
- `start_datetime`, `end_datetime` (optional)
- `location_name`, `address` (optional)
- `registration_url`
- `notes`
- audit fields: `created_by`, `updated_at`

**Files/Areas:** `tryouts/models.py`, `admin.py`, migrations

**Acceptance Checks:**
- Admin can create TryoutEvent in admin

---

### Task 4.2 — Tryout CRUD (Coach) — Web UI
**Goal:** Approved coaches can create/edit/cancel tryouts for their teams (web UI).

**Files/Areas:** `tryouts/views.py`, `tryouts/forms.py`, `tryouts/urls.py`, templates

**Acceptance Checks:**
- Coach can create tryout
- Coach can edit their tryout
- Coach cannot edit other coaches’ teams

---

### Task 4.2A — TryoutEvent API (ViewSet)
**Goal:** DRF CRUD endpoints for tryouts.

**Includes:**
- Serializer
- ViewSet with region filtering
- Permissions: approved coach + team membership for writes
- Router registration: `/api/v1/tryouts/`

**Acceptance Checks:**
- `GET /api/v1/tryouts/` lists region tryouts
- Coach can `POST/PUT/PATCH/DELETE` only for their teams

---

### Task 4.3 — Tryout Browse + Filters — Web UI
**Goal:** Mobile-friendly list page with basic filters.

**Filters:** age group, level, date range

**Files/Areas:** `tryouts/views.py`, templates

**Acceptance Checks:**
- Visit `/tryouts/` shows upcoming events
- Filters work
- Registration link opens external page

---

### Task 4.3A — Tryout Filters API
**Goal:** Filtering via query params.

**Examples:**
- `/api/v1/tryouts/?age_group=13U&level=AAA`
- `/api/v1/tryouts/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`

**Acceptance Checks:**
- API filtering returns expected subset

---

## 5. Player Profile (Core MVP)

### Task 5.1 — PlayerProfile Model (Global)
**Goal:** Create a global player profile.

**Fields (MVP):**
- `user`, `display_name` (or initials)
- `birth_year` or `age_group`
- `positions` (simple string or many-to-many later)
- `bats`, `throws`

**Files/Areas:** `profiles/models.py`, `admin.py`, migrations

**Acceptance Checks:**
- Player can create/edit profile

---

### Task 5.1A — PlayerProfile API (Me Endpoint)
**Goal:** Provide API endpoints for the current user’s profile.

**Includes:**
- `/api/v1/profile/me/` GET/PUT/PATCH
- Permissions: user can only access their own

**Acceptance Checks:**
- Authenticated user can fetch and update their profile via API

---

### Task 5.2 — Profile Privacy Defaults
**Goal:** Profile is private by default (not publicly browsable).

**Files/Areas:** `profiles/views.py`, permissions

**Acceptance Checks:**
- No public player directory
- Profile accessible to the player only (and admin)

---

## 6. Open Status (MVP)

### Task 6.1 — AvailabilityStatus Model
**Goal:** Player can toggle Open/Not Open and add optional metadata.

**Fields (MVP):**
- `player_profile`
- `is_open`
- `desired_levels` (optional)
- `positions_willing` (optional)
- `updated_at`

**Files/Areas:** `portal/models.py` (or `availability/models.py`)

**Acceptance Checks:**
- Player can toggle Open on their dashboard

---

### Task 6.1A — Availability API (Me Endpoint)
**Goal:** API for player to manage their own Open status.

**Includes:**
- `/api/v1/availability/me/` GET/PUT/PATCH

**Acceptance Checks:**
- Authenticated player can toggle Open via API

---

### Task 6.2 — Allowed Associations Visibility (MVP Choice)
**Goal:** Player can select which associations may view Open status.

**Implementation options:**
- ManyToMany: `AvailabilityStatus.allowed_associations`
- Or separate model: `OpenVisibilityPermit(player, association)`

**Files/Areas:** models + forms + UI

**Acceptance Checks:**
- Player can add/remove allowed associations
- Only allowed associations can see the player in Open searches

---

### Task 6.2A — Open Visibility API
**Goal:** API endpoints to manage allowed associations.

**Examples:**
- `GET /api/v1/availability/allowed-associations/` (list)
- `POST /api/v1/availability/allowed-associations/` (add by `association_id`)
- `DELETE /api/v1/availability/allowed-associations/<association_id>/` (remove)

**Acceptance Checks:**
- Allowed associations list updates correctly

---

## 7. Contact Request Workflow

### Task 7.1 — ContactRequest Model (Region-Scoped)
**Goal:** Teams can request contact with an Open player.

**Fields (MVP):**
- `team`, `region`, `player_profile`
- `status` (PENDING/ACCEPTED/DECLINED)
- `message` (optional)
- timestamps

**Files/Areas:** `requests/models.py` (or `portal/models.py`)

**Acceptance Checks:**
- Create pending request
- Update status

---

### Task 7.1A — ContactRequest API (Coach + Player Actions)
**Goal:** API endpoints for creating requests and updating status.

**Includes:**
- Coach: `POST /api/v1/contact-requests/`
- Player: `GET /api/v1/contact-requests/` (inbox for players, sent for coaches)
- Player: `POST /api/v1/contact-requests/<id>/respond/` with status `approved` or `declined`

**Acceptance Checks:**
-- Coach can create only if permitted (allowed associations visibility)
- Player can accept/decline only their own requests

---

### Task 7.2 — Coach UI: Send Contact Request
**Goal:** Coach can search Open players they’re allowed to see and send a request (web UI).

**Files/Areas:** views/templates, query filtering by allowed associations

**Acceptance Checks:**
- Coach sees list of Open players permitted
- Coach sends request -> player sees it

---

### Task 7.2A — Open Players Search API (Coach)
**Goal:** API endpoint for a coach to list Open players they are permitted to view.

**Endpoint:**
- `GET /api/v1/open-players/`

**Rules:**
- Returns only players who are Open
- Returns only players who permit the coach’s team(s)
- Region-scoped by current subdomain

**Acceptance Checks:**
- Coach sees only permitted players

---

### Task 7.3 — Player UI: Accept / Decline
**Goal:** Player can accept or decline requests (web UI).

**Behavior:**
- On accept: reveal contact details (MVP: show email address)
- On decline: request closes

**Files/Areas:** player dashboard views/templates

**Acceptance Checks:**
- Player accepts → coach sees accepted
- Player declines → coach sees declined

---

## 8. Commitment (MVP)

### Task 8.1 — Committed Status
**Goal:** Player can mark themselves Committed (hides from Open search).

**Files/Areas:** AvailabilityStatus field or separate state; UI + API

**Acceptance Checks:**
- Committed player does not appear in Open list

---

## 9. Audit Logging (Minimal)

### Task 9.1 — AuditLogEntry (Append-Only)
**Goal:** Log sensitive actions: tryout create/edit, contact request, accept/decline.

**Fields:** actor, action, object ref, timestamp, region

**Files/Areas:** `audit/models.py`, helper function

**Acceptance Checks:**
- Actions create log entries

---

## 10. Admin Seed + Demo Data

### Task 10.1 — Seed Script / Fixtures
**Goal:** Create minimal demo data for presentation.

**Data:**
- Region: BC
- 1–2 Associations
- 3–5 Teams
- 1 Coach account
- 1 Player account

**Acceptance Checks:**
- Demo can be run from a clean DB

---

## 11. Tests (Must Have)

### Task 11.1 — Permission/Isolation Tests
**Goal:** Prevent cross-team and cross-region leaks.

**Tests:**
- Coach cannot post for unassigned team
- Coach cannot view Open players not permitted
- Player cannot see other players’ private profiles

**Acceptance Checks:**
- `python manage.py test` passes

---

## 12. MVP Demo Checklist (Final)
- Coach posts a tryout
- Player browses tryouts
- Player marks Open
- Player allows a specific team
- Coach sends contact request
- Player accepts/declines

---

## Suggested Codex Prompt Template
Copy/paste this for each task:

**Prompt:**
"Implement Task X.Y from CODEX_TASKS.md. Follow existing project conventions. Build both **Django web UI** and **DRF API** (serializers, viewsets, routers) where indicated. Enforce region scoping via `request.region` and privacy-first access controls. Include migrations and tests for permissions and filtering. Provide a short summary of changes and how to run/verify."
