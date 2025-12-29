# PROMPTS.md — Codex Build History

This file records major Codex prompts used to build the project.
It exists for reproducibility and future reference.

---

## Prompt 001 — Project Bootstrap + DRF Health Check

**Date:** 2025-12-27  
**Tasks:** CODEX_TASKS.md — Task 0.1, 0.3, 0.4

### Prompt


You are working in a new repository for the BC Baseball Transfer Portal.

Follow CODEX_TASKS.md strictly.

Implement Task 0.1, Task 0.3, and Task 0.4.

Requirements:
- Create a new Django project using Python 3.13.
- Add Django REST Framework.
- Set up a versioned API base at /api/v1/.
- Implement a health endpoint at GET /api/v1/health/ that returns { "status": "ok" }.
- Configure API authentication using JWT (djangorestframework-simplejwt).
- Ensure the development server runs successfully.

Project constraints:
- Keep code simple and idiomatic.
- Do not implement any business logic yet.
- Do not add unnecessary apps or models.
- Follow the documentation in README.md, SETUP.md, ARCHITECTURE.md, MVP_SCOPE.md, and CODEX_TASKS.md.

Deliverables:
- requirements.txt updated
- Django project scaffold created
- DRF installed and configured
- JWT auth endpoints configured
- Health endpoint working

After implementation:
- Briefly summarize what was added.
- Explain how to run the server and verify the health endpoint.

## Prompt 002 — Regions + Subdomain Middleware + Region-Aware API Context

**Date:** 2025-12-27  
**Tasks:** CODEX_TASKS.md — Task 1.1, 1.2, 1.3

### Prompt
Implement Task 1.1, Task 1.2, and Task 1.3 from CODEX_TASKS.md.

Goal:
- Add Region model and admin registration.
- Seed/create the BC region (code='bc').
- Add subdomain middleware that sets request.region based on host (e.g., bc.localhost -> 'bc').
- Ensure DRF endpoints can access request.region and apply region scoping helpers.

Requirements:
1) Create a Django app named `regions` (if it doesn’t exist yet).
2) Implement Region model with at minimum:
   - code (slug-like, unique, lowercase e.g. 'bc')
   - name (e.g. 'British Columbia')
   - is_active (default True)
3) Add Region to Django admin.
4) Create a simple, repeatable way to ensure Region(code='bc') exists:
   - Either a data migration OR a fixture + documented load command.
   - Prefer a data migration if simple.
5) Create middleware that:
   - Parses request.get_host()
   - Extracts left-most subdomain
   - If subdomain matches an active Region.code, sets request.region_code and request.region (Region object or code)
   - If no matching region, default to 'bc' for MVP
6) Add a helper for DRF viewsets like `get_request_region(request)` and a base mixin `RegionScopedQuerysetMixin` that filters querysets by request.region where the model has a `region` field. (If model does not have region, mixin should be unused.)
7) Add/adjust tests:
   - Request to bc.localhost sets request.region_code == 'bc'
   - Request to localhost defaults to bc
   - If a Region 'on' exists and host is on.localhost, request.region_code == 'on'

Constraints:
- Keep everything minimal and MVP-safe.
- Don’t implement associations/teams yet.
- Don’t change existing DRF endpoints besides adding region context support.

Deliverables:
- regions app + model + admin + migration/seed
- middleware wired into settings
- helper/mixin for region scoping in DRF
- tests passing

After:
- Summarize changes
- Show how to verify region behavior with curl.


### Outcome
- Added `regions` app with `Region` model + admin registration
- Seeded `Region(code='bc')` via data migration (`0002_seed_bc_region.py`)
- Added `RegionMiddleware` to set `request.region_code` / `request.region` from host (e.g. `bc.localhost`)
- Added DRF helper/mixin for region-scoped querysets
- Added middleware tests for `bc`, `localhost`, and `on` hosts

### Verification
- `python manage.py migrate`
- `python manage.py test`
- `curl -i http://bc.localhost:8000/api/v1/health/`
- `curl -i -H "Host: bc.localhost:8000" http://localhost:8000/api/v1/health/`

---

## Prompt 003 — Accounts, Roles, Coach Approval, and /api/v1/me/

**Date:** 2025-12-27  
**Tasks:** CODEX_TASKS.md — Task 2.1, 2.2, 2.3, 2.4

### Prompt
Implement Task 2.1, 2.2, 2.3, and 2.4 from CODEX_TASKS.md.

Goal:
- Add roles (player/parent, coach/manager, admin) and coach approval.
- Add API endpoints for authentication context: /api/v1/me/
- Add DRF permission classes for RBAC and approval checks.
- Keep it minimal and MVP-safe.

Constraints:
- Do NOT implement leagues/teams/tryouts yet.
- Do NOT change region middleware behavior.
- Keep Django’s default User model unless you strongly need a custom user model. Prefer a UserProfile/AccountProfile linked OneToOne to User for role/approval fields.
- Ensure all endpoints are region-safe (they can read request.region_code but do not need to filter by region yet).

Requirements:

1) Create an `accounts` app (if missing).

2) Data model:
- Create an AccountProfile model linked OneToOne to Django User with fields:
  - role: choices = PLAYER, COACH, ADMIN (default PLAYER)
  - is_coach_approved: boolean (default False)
  - created_at, updated_at
- Ensure profile is created automatically for new users (signal).
- Admin users:
  - If user.is_staff or user.is_superuser, treat them as ADMIN role in logic (or sync role automatically).

3) Admin:
- Register AccountProfile in Django admin.
- Allow admin to set role and approve coaches from admin panel easily.

4) API:
- Add endpoint GET /api/v1/me/ returning:
  - user id, username, email
  - role
  - is_coach_approved
  - region_code (from request.region_code)
- Add endpoint PATCH /api/v1/me/ to allow user to update safe fields only (MVP-safe):
  - email (optional)
  - (Do NOT allow role changes via API)

5) Permissions (DRF):
- Create permission classes:
  - IsAdminRole: true if user.is_staff/superuser OR profile.role == ADMIN
  - IsCoachRole: profile.role == COACH
  - IsApprovedCoach: IsCoachRole AND profile.is_coach_approved is True
  - IsSelf: object-level for user-owned resources (useful later)

6) Wire RBAC defaults:
- Keep REST_FRAMEWORK default permission as IsAuthenticated (already).
- Ensure /api/v1/health/ remains AllowAny.
- /api/v1/auth/token and refresh must remain accessible without being authenticated (make sure global default permissions do not block them).

7) Tests:
- Creating a user creates AccountProfile automatically with role PLAYER.
- /api/v1/me/ requires auth and returns correct role/approval/region_code.
- Coach role without approval fails IsApprovedCoach check (unit test the permission).
- Staff/superuser passes IsAdminRole.

Deliverables:
- accounts app with models, signals, admin
- api endpoint /api/v1/me/ (serializer + view)
- permissions module
- tests passing

After:
- Summarize changes
- Show curl examples for /api/v1/me/ using JWT.


### Outcome
- Added `accounts` app with `AccountProfile` (role + coach approval) linked to User
- Implemented automatic profile creation via signals
- Registered AccountProfile in Django admin for role management and coach approval
- Added RBAC permission classes (admin, coach, approved coach, self)
- Implemented `/api/v1/me/` endpoint returning user info + `region_code`
- Fixed `/api/v1/me/` GET to use instance-mode serialization (PATCH uses data + validation)
- All tests pass after serializer fix

### Verification
- `python manage.py migrate`
- `python manage.py test`
- Obtain JWT token via `/api/v1/auth/token/`
- Call `/api/v1/me/` with Authorization header and confirm role, approval, and region_code

---

## Prompt 004 — Associations & Teams (Region-Scoped)

**Date:** 2025-12-28  
**Tasks:** CODEX_TASKS.md — Task 3.1, 3.2, 3.3

### Prompt
Implement Task 3.1, 3.2, and 3.3 from CODEX_TASKS.md.

Goal:
- Introduce region-scoped Associations and Teams.
- Establish clean ownership and permission boundaries.
- Do NOT implement tryouts, rosters, or players-on-teams yet.

Constraints:
- Keep everything region-aware using request.region.
- Do NOT change existing auth, region middleware, or RBAC logic.
- Use Django ORM + DRF best practices.
- Keep the schema minimal and MVP-safe.

Requirements:

1) Create a new Django app: `organizations` (or `associations` if already named in CODEX_TASKS.md).

2) Models:

Association
- id
- region (FK to Region, required)
- name
- short_name (optional)
- is_active (default True)
- created_at / updated_at

Team
- id
- region (FK to Region, required)
- association (FK to Association)
- name
- age_group (e.g. "13U", "15U")
- level (optional: e.g. A, AA, AAA)
- is_active (default True)
- created_at / updated_at

Rules:
- Association.region must match Team.region
- All queries must be region-scoped

3) Admin:
- Register Association and Team in Django admin
- Admin can create/edit associations and teams
- Enforce region consistency (validation)

4) Permissions:
- Only ADMIN users can create/update associations
- Only ADMIN users can create teams
- Coaches will be linked to teams later (do not implement now)

5) API (read-only for MVP):
- GET /api/v1/associations/
- GET /api/v1/teams/

Behavior:
- Responses must only include objects in request.region
- Use the RegionScopedQuerysetMixin where applicable

6) Tests:
- Associations and Teams are filtered by region
- Cross-region data is not visible
- Region mismatch validation is enforced
- Non-admin users cannot create/update associations or teams

Deliverables:
- organizations app with models, migrations, admin
- DRF serializers + viewsets (read-only)
- Permissions enforced
- Tests passing

After:
- Summarize changes
- Show curl examples for listing associations and teams under bc.localhost


### Outcome
- Added new `organizations` app with region-scoped `Association` and `Team` models
- Added minimal `TeamCoach` model (for future coach↔team linking)
- Registered Association/Team (and TeamCoach if applicable) in Django admin
- Enforced region consistency validation (Association.region must match Team.region)
- Implemented read-only DRF endpoints:
  - `GET /api/v1/associations/`
  - `GET /api/v1/teams/`
- Applied region filtering via `RegionScopedQuerysetMixin` using `request.region`
- Added serializers + viewsets + router wiring
- Added tests covering:
  - region filtering / isolation
  - region mismatch validation
  - write restrictions (non-admin cannot create/update)

### Verification
- `python manage.py migrate`
- `python manage.py test`
- Obtain JWT token via `/api/v1/auth/token/`
- List associations (JWT required):
  - `curl http://localhost:8000/api/v1/associations/ -H "Authorization: Bearer <access_token>" -H "Host: bc.localhost:8000"`
- List teams (JWT required):
  - `curl http://localhost:8000/api/v1/teams/ -H "Authorization: Bearer <access_token>" -H "Host: bc.localhost:8000"`

---

## Prompt 005 — Tryouts Listings (Region-Scoped, Public Read)


**Date:** 2025-12-28
**Tasks:** CODEX_TASKS.md — Task 4.1, 4.2, 4.3

### Prompt

Implement Task 4.1, 4.2, and 4.3 from CODEX_TASKS.md.

Goal:
- Introduce region-scoped Tryout listings.
- Allow associations/teams to post tryout dates and registration links.
- Allow families to discover tryouts without phone calls or private outreach.

Constraints:
- Keep everything region-aware using request.region.
- Do NOT implement player “Open” status yet.
- Do NOT implement applications, rosters, or acceptance flows yet.
- Keep APIs read-only for non-admin users.
- Keep schema minimal and MVP-safe.

Requirements:

1) Create a new Django app: `tryouts`.

2) Models:

TryoutEvent
- id
- region (FK to Region, required)
- association (FK to Association, required)
- team (FK to Team, nullable)
- name (e.g. “13U AAA Tryouts”)
- start_date
- end_date
- location (text)
- registration_url (URLField)
- notes (optional text)
- is_active (default True)
- created_at / updated_at

Rules:
- TryoutEvent.region must match Association.region
- If team is set, Team.region must match TryoutEvent.region

3) Admin:
- Register TryoutEvent in Django admin
- Enforce region consistency validation
- Admin users can create/edit tryouts

4) API:
- GET /api/v1/tryouts/
- GET /api/v1/tryouts/<id>/

Behavior:
- Results filtered by request.region
- Only active tryouts returned by default
- Sorted by start_date ascending
- No authentication required for GET (AllowAny)

5) Permissions:
- Read-only for all users (including anonymous)
- Write operations restricted to ADMIN users only

6) Tests:
- Tryouts are filtered by region
- Inactive tryouts are excluded
- Region mismatch validation enforced
- Anonymous users can list and view tryouts
- Non-admin users cannot create/update tryouts

Deliverables:
- tryouts app with models, migrations, admin
- DRF serializers + viewsets
- URL routing
- Permissions enforced
- Tests passing

After:
- Summarize changes
- Show curl examples for listing tryouts under bc.localhost

### Outcome
- Added `tryouts` app with region-scoped `TryoutEvent` model
- Registered TryoutEvent in Django admin
- Enforced region consistency validation (TryoutEvent.region matches Association.region; Team.region matches if set)
- Implemented public, read-only DRF endpoints filtered by `request.region` and `is_active`
- Wired `/api/v1/tryouts/` routes
- Added tests for:
- region filtering
- active-only behavior
- validation rules
- permissions (anonymous reads allowed; non-admin writes blocked)


### Verification
- `python manage.py migrate`
- `python manage.py test`
- List tryouts (public):
- `curl http://localhost:8000/api/v1/tryouts/ -H "Host: bc.localhost:8000"`
- Retrieve a tryout (public):
- `curl http://localhost:8000/api/v1/tryouts/1/ -H "Host: bc.localhost:8000"`

---

## Prompt 006 — Player Open Status (Availability) + Allow-list Visibility

**Date:** 2025-12-28  
**Tasks:** CODEX_TASKS.md — Task 6.1, 6.1A (and 6.2 if it is visibility allow-list)

### Prompt

Implement Task 5.1, 5.2, and 5.3 from CODEX_TASKS.md.

Goal:
- Allow players to declare themselves “Open” (available) in a controlled, private way.
- Enable teams to discover Open players without stigma or public exposure.
- Keep everything opt-in, region-aware, and auditable.

Constraints:
- Do NOT implement messaging or contact requests yet.
- Do NOT expose Open status publicly.
- Do NOT build a social feed.
- Keep all logic MVP-safe and reversible.
- Reuse existing AccountProfile / Player role logic.

Requirements:

1) Data model

Create a new app: `availability`.

Create model: PlayerAvailability
- id
- player (OneToOne to User or AccountProfile; one active record per player)
- region (FK to Region, required)
- is_open (boolean, default False)
- positions (optional text or JSONField)
- levels (optional text or JSONField)
- expires_at (nullable datetime)
- created_at / updated_at

Rules:
- Only users with role = PLAYER may have availability records.
- Availability.region must match request.region.
- Only ONE availability record per player.
- Expired availability is treated as not open.

2) Admin
- Register PlayerAvailability in Django admin
- Admin can view but not arbitrarily toggle player openness

3) API

Endpoint: `/api/v1/availability/me/`

Methods:
- GET: return the player’s own availability status
- PATCH: allow player to:
  - toggle is_open
  - update positions, levels, expires_at
- Only the authenticated player can access their own record

Endpoint: `/api/v1/availability/search/`

Behavior:
- Accessible ONLY to:
  - ADMIN users
  - Approved COACH users
- Returns players where:
  - is_open = True
  - not expired
  - region == request.region
- Do NOT expose player email by default
- Include minimal safe fields:
  - player id
  - positions
  - levels
  - age group (if available)
  - region_code

4) Permissions
- Enforce role-based access:
  - Players → self only
  - Coaches → search only (if approved)
  - Admin → everything
- Anonymous users have NO access

5) Tests
- Player can toggle own Open status
- Player cannot view other players’ availability
- Coach cannot view availability unless approved
- Approved coach can search Open players
- Expired availability is excluded
- Region filtering enforced

Deliverables:
- availability app with model + migrations
- admin registration
- serializers + views
- permissions
- tests passing

After:
- Summarize changes
- Show curl examples for:
  - Player toggling Open
  - Coach searching Open players

--- 
### Codex

I checked codex_tasks.md and Task 5 is PlayerProfile (5.1/5.1A/5.2), while your request is for Open status/availability, which matches Task 6.1 and 6.1A (and 6.2 for allowed teams). Task 5.3 doesn’t exist in CODEX_TASKS.

Do you want me to proceed with the availability work as Task 6.1/6.1A (and possibly 6.2), or should I implement Task 5 (PlayerProfile) instead?
---

### Prompt
Proceed with the “Open status / availability” work.

Implement CODEX_TASKS.md:
- Task 6.1 and Task 6.1A for Player Availability (“Open” status).
- Also implement Task 6.2 ONLY if it is specifically about visibility controls (allowed teams / allow-list). If 6.2 is something else, skip it.

Do NOT implement Task 5 (PlayerProfile) yet.

Keep it MVP-safe:
- Open status must not be public.
- Search is restricted to ADMIN and Approved COACH only.
- Region filtering enforced.
- Expiration support.
- Provide /api/v1/availability/me/ (GET/PATCH) and /api/v1/availability/search/ (GET).
- Add tests for permissions, expiration, and region isolation.

After implementing, summarize changes and provide curl examples.

### Requirements summary:
- Add `availability` app + `PlayerAvailability` model (region-aware, expiration-aware).
- Allow-list visibility controls (teams allowed to see a player’s Open status).
- API:
  - `GET/PATCH /api/v1/availability/me/` (player manages own status)
  - `GET /api/v1/availability/search/` (restricted to ADMIN + approved COACH)
- Enforce: region isolation, expiration filtering, and team allow-list enforcement.
- Add tests for permissions, expiration, and region isolation.

### Outcome
- Added `availability` app for player Open status with region-aware access and allow-listed visibility controls
- `/api/v1/availability/me/` allows players to view/update their own Open status
- `/api/v1/availability/search/` restricted to ADMIN + approved COACH, filtered by region + expiration, and enforces team allow-list
- Admin is view-only for availability records
- Added tests for permissions, expiration, and region isolation

### Verification
- `python manage.py migrate`
- `python manage.py test`
- Player toggles Open:
  - `curl -X PATCH http://localhost:8000/api/v1/availability/me/ -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" -H "Host: bc.localhost:8000" -d '{"is_open": true, "positions": ["OF"], "levels": ["AAA"]}'`
- Approved coach searches Open players:
  - `curl http://localhost:8000/api/v1/availability/search/ -H "Authorization: Bearer <access_token>" -H "Host: bc.localhost:8000"`


  

