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


  ---

## Prompt 007 — Contact Requests + Audit Logging (API Only)


**Date:** 2025-12-29
**Tasks:** CODEX_TASKS.md — Task 7.1, 7.1A, 7.2A, 9.1

## Prompt 007 — Player Open Status (Availability) + Allow-list Visibility

### Prompt

  Implement Task 7.1, 7.2, and 7.3 from CODEX_TASKS.md.

Goal:
- Allow teams/coaches to request contact with Open players.
- Allow players to approve or decline contact.
- Record all actions in an audit log to prevent abuse or disputes.

Constraints:
- Keep everything region-aware using request.region.
- Do NOT implement chat or messaging yet.
- Do NOT expose player contact details until approval.
- Keep the system auditable and privacy-safe.

Requirements:

1) Data models

Create a new app: `contacts`.

ContactRequest
- id
- player (FK to User / AccountProfile)
- requesting_team (FK to Team)
- requested_by (FK to User — coach)
- region (FK to Region)
- status (PENDING, APPROVED, DECLINED)
- message (optional short text)
- created_at
- responded_at (nullable)

Rules:
- Only ONE active PENDING request per (player, team).
- ContactRequest.region must match request.region.
- Coach must be approved and associated with requesting_team.
- Player must currently be Open (availability.is_open == True).

AuditLog
- id
- actor (User)
- action (string / enum)
- target_type (string)
- target_id
- region (FK to Region)
- metadata (JSONField, optional)
- created_at

Actions to log:
- CONTACT_REQUEST_CREATED
- CONTACT_REQUEST_APPROVED
- CONTACT_REQUEST_DECLINED

2) Admin
- Register ContactRequest and AuditLog in Django admin (read-only for AuditLog).
- Admins can view all activity.

3) API

Endpoint: `/api/v1/contact-requests/`

Methods:
- POST (coach/admin only):
  - Create a contact request for an Open player
- GET:
  - Player: list requests addressed to them
  - Coach/Admin: list requests they created

Endpoint: `/api/v1/contact-requests/<id>/respond/`

Methods:
- POST (player only):
  - Approve or decline a contact request

Behavior:
- Player contact info is NOT returned until approved.
- Declined requests cannot be re-opened.
- Approved requests expose minimal contact metadata only.

4) Permissions
- Only approved coaches or admins can create requests.
- Only the target player can approve/decline.
- Anonymous users have no access.
- Region isolation enforced everywhere.

5) Tests
- Coach cannot request contact for a non-open player.
- Duplicate pending requests are blocked.
- Player can approve/decline only their own requests.
- AuditLog entries created for each action.
- Region isolation enforced.

Deliverables:
- contacts app with models + migrations
- admin registration
- serializers + views
- permissions
- audit logging
- tests passing

After:
- Summarize changes
- Show curl examples for:
  - Coach creating a request
  - Player approving/declining

---

### Codex

I checked codex_tasks.md: Task 7.2 and 7.3 are web UI tasks (coach send request UI, player accept/decline UI), while the API work is in Task 7.1A and 7.2A. Your request includes API endpoints + audit logging, which maps to 7.1/7.1A/7.2A/9.1.

Do you want me to:

Implement the data model + API + audit logging only (skip UI for now), or
Also build the web UI flows for coaches/players (Task 7.2 and 7.3)?
Tell me which option to proceed with.

---

### Prompt
Proceed with data model + API + audit logging only. Skip all web UI work for now.

Implement CODEX_TASKS.md:
- Task 7.1
- Task 7.1A
- Task 7.2A
- Task 9.1 (AuditLog)

Do NOT implement:
- Task 7.2 (coach UI)
- Task 7.3 (player UI)

Scope requirements:
- Region-aware everywhere (request.region / request.region_code)
- Coaches must be approved and linked to the requesting team (use existing TeamCoach if present)
- Player must be Open to receive a request (use availability app)
- Prevent duplicate pending requests per (player, team)
- Provide endpoints:
  - POST/GET /api/v1/contact-requests/
  - POST /api/v1/contact-requests/<id>/respond/
- Do not expose player contact details until approved
- Write AuditLog entries for create/approve/decline

Add tests for:
- non-open player blocked
- duplicate pending blocked
- permissions and region isolation
- audit log entries created

After implementing, summarize changes and provide curl examples.

### Outcome
- Added `contacts` app implementing the contact request workflow
- Coaches (approved and team-linked) can create contact requests for Open players
- Players can approve or decline requests via API
- Duplicate pending requests per (player, team) are blocked
- Player contact details remain hidden until approval
- Added `AuditLog` model with entries for create/approve/decline actions
- Region isolation enforced across all contact request operations
- Fixed conditional unique constraint to safely reference pending status
- All tests pass after fix


### Verification
- `python manage.py migrate`
- `python manage.py test`
- Coach creates a request:
- `curl -X POST http://localhost:8000/api/v1/contact-requests/ -H "Authorization: Bearer <coach_access_token>" -H "Content-Type: application/json" -H "Host: bc.localhost:8000" -d '{"player_id":12,"requesting_team_id":3,"message":"We would like to connect."}'`
- Player responds:
- `curl -X POST http://localhost:8000/api/v1/contact-requests/42/respond/ -H "Authorization: Bearer <player_access_token>" -H "Content-Type: application/json" -H "Host: bc.localhost:8000" -d '{"status":"approved"}'`


---

## Prompt 008 — PlayerProfile (Global) + /api/v1/profile/me/ + Privacy Defaults


**Date:** 2025-12-29
**Tasks:** CODEX_TASKS.md — Task 5.1, 5.1A, 5.2


### Prompt

Implement CODEX_TASKS.md Task 5.1, Task 5.1A, and Task 5.2 (PlayerProfile core MVP).

Scope: API-first (no web UI for now).

Goal:
- Create a global PlayerProfile that belongs to a user (one profile per user).
- Provide /api/v1/profile/me/ so the current user can GET/PATCH their profile.
- Keep profiles private by default (no public directory; only self + admin can view).

Constraints:
- Keep it minimal and MVP-safe.
- Do NOT add public profile browsing endpoints.
- Do NOT modify existing region middleware.
- Keep region out of PlayerProfile (global identity).
- Use existing AccountProfile role logic: only role=PLAYER should create/edit a PlayerProfile by default.
- Admin users can view/edit via admin.

Requirements:

1) Create a new Django app: `profiles`.

2) Model: PlayerProfile (Global)
Fields (MVP):
- user (OneToOne to auth.User, unique)
- display_name (string; allow initials)
- birth_year OR age_group (choose one, but keep it simple; prefer birth_year int)
- positions (simple JSONField list of strings OR comma-separated string)
- bats (choice: R/L/S; optional)
- throws (choice: R/L; optional)
- created_at / updated_at

Rules:
- One profile per user.
- Default: profile exists or is auto-created on first GET/PUT/PATCH of /profile/me/ (choose a simple pattern and document it).
- Profiles are private by default.

3) Admin:
- Register PlayerProfile in Django admin.

4) API:
Create endpoint: /api/v1/profile/me/
- GET: return current user’s PlayerProfile (create one if missing OR return 404; choose one approach and be consistent)
- PATCH: update safe fields only (display_name, birth_year/age_group, positions, bats, throws)
Permissions:
- Only authenticated user with role=PLAYER can access /profile/me/ (self-only).
- Admins may access any profile via admin only (no public API for listing).

5) Privacy defaults (Task 5.2):
- Ensure there is NO endpoint like /api/v1/profiles/ listing all profiles.
- Ensure no public player directory exists.
- Ensure any accidental access to other users’ profiles is blocked.

6) Tests:
- Player can GET/PATCH /api/v1/profile/me/
- Non-player roles cannot create/update PlayerProfile via /me endpoint (coach/admin user via API should be blocked; admin can use admin site)
- Profile is not publicly listable (no list route; or returns 404 if someone tries).
- Self-only access enforced.

Deliverables:
- profiles app with model + migrations
- admin registration
- serializer + view + urls wiring under /api/v1/
- tests passing

After:
- Summarize changes
- Provide curl examples for GET and PATCH /api/v1/profile/me/

### Outcome
- Added `profiles` app with a global `PlayerProfile` model
- Registered PlayerProfile in Django admin
- Implemented `/api/v1/profile/me/` GET/PATCH endpoint
- Auto-creates a profile on first access
- Enforced **player-only** access (non-player roles receive 403)
- Confirmed no public list route exists (`/api/v1/profiles/` returns 404)
- Tests added; all tests pass after adjusting the endpoint guard to match expected behavior


### Verification
- `python manage.py migrate`
- `python manage.py test`


GET profile:
- `curl http://localhost:8000/api/v1/profile/me/ -H "Authorization: Bearer <player_access_token>"`


PATCH profile:
- `curl -X PATCH http://localhost:8000/api/v1/profile/me/ -H "Authorization: Bearer <player_access_token>" -H "Content-Type: application/json" -d '{"display_name":"J. Player","birth_year":2011,"positions":["OF"],"bats":"R","throws":"R"}'`


Privacy check:
- `curl -i http://localhost:8000/api/v1/profiles/` (expected 404)


---

## Prompt 009 — Committed Status (API Only)

**Date:** 2025-12-30  
**Tasks:** CODEX_TASKS.md — Task 8.1

### Prompt
Implement CODEX_TASKS.md Task 8.1 (Committed Status).

Scope: API-first (no web UI for now).

Goal:
- Allow a player to mark themselves "Committed".
- A committed player must not appear in any Open player search results.
- Committed should effectively end recruiting visibility (MVP safety).

Constraints:
- Keep it minimal and MVP-safe.
- Do NOT change region middleware.
- Do NOT add public endpoints.
- Preserve privacy rules and region isolation.

Design choice (pick the simplest consistent approach):
- Option A (preferred): Add `is_committed` boolean + `committed_at` to the existing availability model (PlayerAvailability / AvailabilityStatus).
- OR Option B: Add a separate small model if needed.
Prefer Option A unless there is a strong reason not to.

Requirements:

1) Data model
- Add fields:
  - is_committed (boolean, default False)
  - committed_at (nullable datetime)
- Rules:
  - If is_committed == True:
    - is_open must be treated as False (either force-set or excluded in queries)
    - availability search endpoints must exclude the player
    - contact request creation must be blocked for that player (even if an old record shows is_open True)
  - Committed is controlled by the player only (self).

2) API
Extend `/api/v1/availability/me/`:
- PATCH supports setting:
  - is_committed (true/false)
  - When set true: set committed_at = now, set is_open = false
  - When set false: committed_at cleared (optional) and player may manually set is_open later
Keep permissions self-only (player).

3) Enforcement updates
- Update `GET /api/v1/availability/search/` and/or `GET /api/v1/open-players/` (whichever exists) to exclude committed players.
- Update `POST /api/v1/contact-requests/` to block requests to committed players.

4) Audit logging (if present)
- If you already have AuditLog in contacts, add a new action:
  - COMMITTED_SET (and optionally COMMITTED_CLEARED)
- Log when player commits/uncommits.

5) Tests
Add tests to verify:
- Player can set is_committed via `/availability/me/`
- Committing forces is_open false
- Committed players do not appear in open player search endpoints
- Contact request creation fails for committed players
- Region isolation remains enforced
- (If audit logging added) audit entry is created

Deliverables:
- migration(s)
- updated serializers/views/permissions as needed
- tests passing

After:
- Summarize changes
- Provide curl examples for:
  - player committing via PATCH /api/v1/availability/me/
  - coach open players search excluding committed
  - coach contact request blocked for committed player

### Outcome
- Added `is_committed` and `committed_at` to PlayerAvailability
- Committing forces `is_open` false and logs COMMITTED_SET/COMMITTED_CLEARED
- Open player searches exclude committed players
- Contact requests to committed players are blocked
- Tests added for commit behavior and exclusions

### Verification
- `python manage.py migrate`
- `python manage.py test`


Commit:
- `curl -X PATCH http://localhost:8000/api/v1/availability/me/ -H "Authorization: Bearer <player_access_token>" -H "Content-Type: application/json" -H "Host: bc.localhost:8000" -d '{"is_committed": true}'`

Open players search (coach/admin):
- `curl http://localhost:8000/api/v1/open-players/ -H "Authorization: Bearer <coach_access_token>" -H "Host: bc.localhost:8000"`

Contact request blocked:
- `curl -X POST http://localhost:8000/api/v1/contact-requests/ -H "Authorization: Bearer <coach_access_token>" -H "Content-Type: application/json" -H "Host: bc.localhost:8000" -d '{"player_id":12,"requesting_team_id":3,"message":"We would like to connect."}'`


---

## Prompt 010 — Seed Script / Fixtures (Minimal Demo Data)

**Date:** 2025-12-30  
**Tasks:** CODEX_TASKS.md — Task 10.1

### Prompt
Implement CODEX_TASKS.md Task 10.1 — Seed Script / Fixtures (Minimal Demo Data).

Goal:
- Make it possible to set up a clean demo environment from an empty DB with one command.
- Seed enough data to demonstrate the MVP loop without manual admin clicking.

Constraints:
- Keep it minimal and deterministic (no random generation).
- Must be safe to run multiple times (idempotent).
- Do not change existing models/permissions unless absolutely necessary.
- Keep region-aware data scoped to BC region (code='bc').

Seed data required:
1) Region
- Ensure Region(code='bc', name='British Columbia') exists (should already via migration; verify).

2) Associations / Teams
- Create 1 Association in BC (e.g. "Vancouver Minor Baseball", short_name="VMB").
- Create 3 Teams in BC under that association, e.g.:
  - "VMB 13U AAA" (age_group="13U", level="AAA")
  - "VMB 13U AA" (age_group="13U", level="AA")
  - "VMB 15U AAA" (age_group="15U", level="AAA")

3) Users + roles
Create 3 users with known credentials (document them in output):
- Admin user (superuser):
  - username: admin
  - email: admin@example.com
  - password: adminpass123
- Coach user (approved coach role):
  - username: coach1
  - email: coach1@example.com
  - password: coachpass123
  - AccountProfile role=COACH, is_coach_approved=True
- Player user (player role):
  - username: player1
  - email: player1@example.com
  - password: playerpass123
  - AccountProfile role=PLAYER

4) Coach-team membership
- Link coach1 to one of the teams (e.g. VMB 13U AAA) via TeamCoach.

5) Player profile + availability
- Create PlayerProfile for player1 with:
  - display_name "J. Player"
  - birth_year 2011
  - positions ["OF"]
  - bats "R", throws "R"
- Create availability for player1 in region BC:
  - is_open = True
  - allow-list visibility includes the coach’s team (the one coach1 belongs to)
  - expiration either null or in the future

6) Tryout(s)
- Create 1 TryoutEvent for the coach’s team in BC with:
  - name "13U AAA Tryouts"
  - start_date/end_date within next 2 weeks
  - registration_url set to a placeholder URL
  - is_active = True

7) Contact request (optional but helpful)
- Optionally create a pending ContactRequest from coach’s team to player1,
  OR provide documented curl steps to create it during demo.

Implementation approach:
- Add a management command: `python manage.py seed_demo`
  OR a deterministic script under `scripts/seed_demo.py` plus documented command.
- Prefer management command (standard Django).

Acceptance checks:
- From a clean DB:
  - `python manage.py migrate`
  - `python manage.py seed_demo`
  - `python manage.py test` still passes
- API demo checks:
  - Public tryouts list works for bc.localhost
  - Coach can search open players and see player1
  - Coach can create contact request to player1 (if not pre-seeded)
  - Player can approve/decline the request

Deliverables:
- Seed command/script + documentation (README snippet or in SETUP.md)
- Idempotent behavior (running twice does not duplicate records)
- Short summary of created objects + credentials printed at the end of the seed command

### Outcome
- Added `python manage.py seed_demo` management command
- Seeds BC region, one association, three teams, demo users, and a tryout
- Creates player profile + availability allow-listed to coach team
- Idempotent (safe to run multiple times)

### Verification
- `python manage.py migrate`
- `python manage.py seed_demo`
- `python manage.py test`

Demo:
- `curl -X POST http://bc.localhost:8000/api/v1/contact-requests/ -H "Authorization: Bearer <coach_access_token>" -H "Content-Type: application/json" -d '{"player_id":<player_id>,"requesting_team_id":<team_id>,"message":"We would like to connect."}'`

---

## Prompt 011 — Permission & Isolation Hardening (No New Features)

**Date:** 2025-12-31
**Tasks:** CODEX_TASKS.md — Task 11.1

### Prompt

Implement CODEX_TASKS.md **Task 11.1 — Permission / Isolation Tests & Hardening**.

This prompt is **hardening-only**. Do **not** introduce new features, models, or endpoints unless required to fix a failing test.

Goal:

* Ensure strict **cross-region**, **cross-team**, and **cross-role** isolation.
* Treat all permission leaks as **MVP blockers**.

Scope:

* API-first only (no Web UI work).
* Focus on permissions, query filtering, and negative tests.

Requirements:

1. Coach / Team Isolation

* A coach must NOT be able to:

  * create contact requests for teams they are not assigned to
  * view Open players unless allowed by availability allow-list
* Enforce at both:

  * serializer / queryset level
  * permission class level

2. Region Isolation

* No object created or queried under one region may be:

  * listed
  * retrieved
  * mutated
    from another region subdomain
* Add explicit tests for cross-region leakage attempts

3. Player Privacy

* Players must NOT:

  * view other players’ profiles
  * view other players’ availability
  * view contact requests not addressed to them

4. Admin Scope

* Admins may bypass role restrictions but:

  * MUST still respect region isolation

5. Tests (Required)
   Add tests that assert **denial**, not just success:

* Coach blocked from unassigned team actions
* Coach blocked from Open players not allow-listed
* Player blocked from accessing other players’ data
* Cross-region access returns empty results or 403

6. No Regressions

* All existing tests must continue to pass
* Seed demo data must still work

Deliverables:

* Additional permission/isolation tests
* Any minimal fixes required to pass those tests

After:

* Summarize what was hardened
* Explicitly list what is now impossible to do (security guarantees)

---

### Expected Outcome

* Zero cross-team data leaks
* Zero cross-region data leaks
* Strict privacy-by-default for players
* MVP considered **security-complete** after this prompt

---

## Prompt 012 — Web UI Foundation + Public Tryouts (Professional + Mobile-Friendly)

**Date:** 2025-01-XX  
**Tasks:** Web UI Phase 1 (post–Task 11.1)

### Prompt

## Prompt 012 — Web UI Foundation + Public Tryouts (Professional + Mobile-Friendly)

You are working in the BC Baseball Transfer Portal repo.

Implement the first slice of the Web UI so the product is usable in a browser and looks professional AND mobile-friendly.

Scope rules:
- Web UI only (Django templates/views). Do NOT change existing API endpoints unless necessary for correctness.
- Reuse existing models and region middleware (`request.region_code` / `request.region`) for all queries.
- Keep UI professional, consistent, and responsive.
- Use Bootstrap 5 (CDN) + a tiny custom stylesheet for polish.
- No SPA framework. Server-rendered Django templates only.

Deliverables (must complete all):

1) Base UI / Design System (Responsive)
- Create `templates/base.html` with:
  - `<meta name="viewport" content="width=device-width, initial-scale=1">`
  - Responsive navbar (Bootstrap):
    - Collapses into hamburger menu on mobile
    - Brand: “BC Baseball Transfer Portal”
    - Links: Tryouts (public), Dashboard (auth only), Admin (staff only)
    - Login/Logout buttons depending on auth state
  - A consistent page container + page header pattern (title + optional subtitle + optional actions)
  - Bootstrap alerts for Django messages (success/error/info)
  - Footer (small, muted)
- Add `static/css/app.css` with small, tasteful defaults:
  - subtle background, card spacing, improved form spacing
  - ensure tap targets (buttons/links) are comfortably sized on mobile
- Ensure templates are found (DIRS in settings if needed) without breaking existing setup.

2) Home / Landing Page (Mobile-first)
- Route: `GET /`
- Polished hero section that stacks nicely on mobile:
  - Short explanation (“Privacy-first transfer portal for BC baseball tryouts and recruiting”)
  - Primary CTA button to “Browse Tryouts”
  - Secondary CTA to “Sign in”
- Must render correctly on small screens without horizontal scrolling.

3) Authentication UI (Minimal, Professional, Mobile-friendly)
- Implement login/logout using Django’s built-in auth views (recommended).
- Routes:
  - `/accounts/login/`
  - `/accounts/logout/`
- Use templates extending `base.html`.
- Login form must:
  - be centered and readable on mobile
  - have clear error display
  - use proper input sizing and spacing (Bootstrap form controls)
- Do NOT implement registration unless it already exists.

4) Public Tryouts Web UI (Core, Responsive)
- Implement a public tryouts browse page using DB queries (not calling the API):
  - Route: `GET /tryouts/`
  - Uses `TryoutEvent`
  - Region-scoped by `request.region` (fallback to BC like middleware)
  - Only active tryouts, ordered by start_date ascending

- Filters via query params, designed mobile-first:
  - age_group (dropdown)
  - level (dropdown)
  - date_from / date_to (date inputs)
  - “Apply” button and “Clear filters” link/button
  - On desktop: filters can sit in a sidebar card (col-md-3) with results beside it
  - On mobile: filters must stack ABOVE results and remain usable without tiny controls

- Results display must be responsive:
  - Use cards (preferred) so it looks good on mobile
  - Each tryout card includes:
    - name
    - age_group + level badges (if available)
    - date range
    - location
    - prominent “Register” button linking to registration_url (new tab)
    - optional notes (muted, trimmed)
- Include a polished empty state when no results.

5) Optional Tryout Detail Page (Responsive)
- Route: `GET /tryouts/<id>/`
- Same region/active checks as list page
- Show full info + register button
- Return 404 if tryout not in region or inactive
- Layout must be mobile-friendly (single-column stack on small screens).

6) Role-Aware Dashboard Router (Thin)
- Route: `GET /dashboard/` (login required)
- Behavior:
  - If user role is PLAYER -> redirect to `/player/` (placeholder page for now)
  - If user role is COACH -> redirect to `/coach/` (placeholder page for now)
  - If ADMIN/staff -> redirect to `/admin/`
- Create placeholder pages (mobile-friendly):
  - `GET /player/` -> “Player Dashboard (Coming next)” with placeholder links
  - `GET /coach/` -> “Coach Dashboard (Coming next)” with placeholder links
- Do not implement player/coach flows yet in this prompt.

7) Mobile Responsiveness Acceptance (Required)
Implement at least these responsive behaviors:
- Navbar collapses correctly on small screens
- No horizontal scrolling on iPhone-sized widths
- Buttons are not tiny; tap targets are comfortable
- Tryouts list is readable on mobile (cards, good spacing)
- Forms are readable and usable on mobile

8) Tests (Minimal)
- Add lightweight Django tests:
  - `/` returns 200
  - `/tryouts/` returns 200 for anonymous users
  - `/dashboard/` redirects to login when anonymous
  - Tryout detail is region-isolated (wrong region host returns 404) if feasible via Host header tests

Acceptance checks (manual):
- `python manage.py migrate`
- `python manage.py seed_demo`
- `python manage.py runserver`
- Verify on desktop and by resizing browser to mobile width:
  - `http://bc.localhost:8000/` looks good
  - `http://bc.localhost:8000/tryouts/` shows seeded tryout and filters work
  - Login with seeded users and visit `/dashboard/`:
    - player1 -> /player/
    - coach1 -> /coach/
    - admin -> /admin/
  - Navbar collapses and UI remains usable on small width

After implementation:
- Summarize what was added and which files were created/modified.
- Provide a short “How to run + verify” checklist.


---

### Outcome
- Implemented the first Web UI slice using **Bootstrap 5** with a professional, mobile-friendly design system.
- Added a responsive base layout with navbar, footer, alerts, and consistent page headers.
- Built a polished landing page and authentication UI (login/logout) using Django’s built-in auth views.
- Implemented **public, region-scoped Tryouts pages**:
  - `/tryouts/` list view with responsive cards
  - `/tryouts/<id>/` detail view with region isolation
- Added **role-aware dashboard routing**:
  - `/dashboard/` redirects players → `/player/`, coaches → `/coach/`, admins → `/admin/`
- Added placeholder Player and Coach dashboards to establish navigation flow.
- Added minimal UI tests, including a region-isolation test for tryout detail pages.
- Configured login redirect behavior to land users on `/dashboard/` after sign-in.
- Ensured all pages are usable on mobile widths (collapsed navbar, stacked layouts, readable cards).

### Files Created / Modified
- `urls.py`
- `settings.py`
- `views.py`
- `web_views.py`
- `templates/base.html`
- `templates/home.html`
- `templates/login.html`
- `templates/tryouts/list.html`
- `templates/tryouts/detail.html`
- `templates/player.html`
- `templates/coach.html`
- `static/css/app.css`
- `tests.py`

### Verification
```bash
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
