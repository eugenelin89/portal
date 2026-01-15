# SANITY_CHECKLIST.md — Incremental Verification Gates

This document defines **incremental sanity checks after each major Codex prompt**.

Each section is **append-only when possible**.

* New prompts add new sections at the bottom.
* Minor corrections may be applied to earlier sections to keep checks accurate.


This allows safe progression without rewriting prior verification steps.

---

When using `scripts/run_sanity_checks.sh`, the script prints which sanity check
it is running to match the sections below.

## Sanity Check — After Prompt #1 (Django + DRF + JWT Bootstrap)

These checks verify that the core Django + DRF + JWT foundation is correct.

### 1. Environment & Dependencies

* Virtual environment is active in VS Code terminal:

  ```
  (venv) portal %
  ```
* Python executable points to venv:

  ```bash
  which python
  # .../venv/bin/python
  ```
* Python version is 3.10+ (tested on 3.13):

  ```bash
  python --version
  ```

---

### 2. Install & Migrate

```bash
pip install -r requirements.txt
python manage.py migrate
```

Expected:

* No install errors
* Migrations apply cleanly

---

### 3. Run Server

```bash
python manage.py runserver
```

Expected:

* Server starts without errors
* No startup warnings related to DRF or auth

---

### 4. Health Endpoint (Core Check)

```bash
curl -i http://bc.localhost:8000/api/v1/health/
```

Expected:

* HTTP 200
* Body:

  ```json
  {"status": "ok"}
  ```

This confirms:

* Django routing works
* DRF is installed
* Versioned API base is live

> Health must remain **public (AllowAny)** even though DRF defaults to `IsAuthenticated`.

---

### 5. Admin & JWT Smoke Test

```bash
python manage.py createsuperuser
```

```bash
curl -s -X POST http://bc.localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"<user>","password":"<pass>"}'
```

```bash
curl -s http://bc.localhost:8000/api/v1/protected/ \
  -H "Authorization: Bearer <access_token>"
```

Expected:

* Token issuance works
* Protected endpoint returns HTTP 200

---

### Exit Gate — Prompt #1

You may proceed to **Prompt #2** only if:

* Health endpoint returns HTTP 200
* JWT auth works
* Server runs cleanly
* Changes are committed

---

## Sanity Check — After Prompt #2 (Regions + Subdomain Middleware)

These checks verify region identity, host parsing, and region-aware API context.

---

### 6. Migrate & Run Tests

```bash
python manage.py migrate
python manage.py test
```

Expected:

* Region seed migration runs successfully (BC exists)
* Middleware tests pass for `bc`, `localhost`, and alternate regions

---

### 7. Region / Subdomain Verification (Manual)

```bash
curl -i -H "Host: bc.localhost:8000" http://localhost:8000/api/v1/health/
```

```bash
curl -i -H "Host: localhost:8000" http://localhost:8000/api/v1/health/
```

Optional (if Region exists):

```bash
curl -i -H "Host: on.localhost:8000" http://localhost:8000/api/v1/health/
```

Expected:

* All return HTTP 200
* Region resolution is asserted via automated tests

---

### 8. Host / Deployment Readiness

Verify `ALLOWED_HOSTS` includes `.localhost`:

```python
ALLOWED_HOSTS = [".localhost", "localhost", "127.0.0.1"]
```

This ensures compatibility with subdomain routing and future deployment (e.g. `bc.transferportal.ca`).

---

### Exit Gate — Prompt #2

You may proceed to **Prompt #3 (Accounts & Roles)** only if:

* All Prompt #1 checks remain green
* Region middleware behaves correctly
* Tests pass
* Changes are committed

---

## Future Prompts

For each new major prompt:

* Append a new **Sanity Check — After Prompt #N** section
* Do **not** modify earlier sections
* Treat each section as an immutable verification gate

---

This checklist is intentionally append-only and audit-friendly.

---

## Prompt 003 — Accounts, Roles, Coach Approval, and /api/v1/me/

**Date:** 2025-12-27
**Tasks:** CODEX_TASKS.md — Task 2.1, 2.2, 2.3, 2.4

### Prompt

Implement Task 2.1, 2.2, 2.3, and 2.4 from CODEX_TASKS.md.

Goal:

* Add roles (player/parent, coach/manager, admin) and coach approval.
* Add API endpoint /api/v1/me/ exposing authentication context.
* Add DRF permission classes for RBAC and approval checks.

Key requirements:

* Use Django’s default User model.
* Create an AccountProfile (OneToOne with User) to store role and coach approval.
* Automatically create AccountProfile on user creation.
* Admins can manage roles and approve coaches via Django admin.
* /api/v1/me/ supports:

  * GET: return user identity, role, approval status, and region_code.
  * PATCH: allow safe self-updates (no role changes).
* Keep /api/v1/health/ public (AllowAny).
* Keep JWT auth endpoints accessible without authentication.
* Add tests for profile creation, RBAC permissions, and /api/v1/me/ behavior.

Constraints:

* Do not introduce leagues, teams, or tryouts.
* Do not modify region middleware behavior.
* Keep implementation minimal and MVP-safe.

Deliverables:

* accounts app with models, signals, and admin registration
* RBAC permission classes
* /api/v1/me/ API endpoint (serializer + view)
* Tests passing

---

### Outcome

* Added `accounts` app with `AccountProfile` (role + coach approval) linked to User
* Implemented automatic profile creation via signals
* Registered AccountProfile in Django admin for role management and coach approval
* Added RBAC permission classes (admin, coach, approved coach, self)
* Implemented `/api/v1/me/` endpoint returning user info + `region_code`
* Fixed `/api/v1/me/` GET to use **instance-mode serialization** (PATCH uses data + validation)
* All tests pass after serializer fix

### Verification

* `python manage.py migrate`
* `python manage.py test`
* Obtain JWT token via `/api/v1/auth/token/`
* Call `/api/v1/me/` with Authorization header and confirm role, approval, and region_code

## Sanity Check — After Prompt #3 (Accounts, Roles, Coach Approval, /api/v1/me/)

These checks verify user roles, coach approval flow, RBAC permissions, and the `/api/v1/me/` endpoint.

---

### 9. Migrate & Run Tests

```bash
python manage.py migrate
python manage.py test
```

Expected:

* AccountProfile migrations apply cleanly
* All tests pass, including:

  * automatic profile creation
  * RBAC permission checks
  * `/api/v1/me/` behavior

---

### 10. Verify /api/v1/me/ Endpoint

#### Obtain JWT token

```bash
curl -s -X POST http://bc.localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"<user>","password":"<pass>"}'
```

#### Call /me

```bash
curl -i http://bc.localhost:8000/api/v1/me/ \
  -H "Authorization: Bearer <access_token>"
```

Expected:

* HTTP 200
* Response includes:

  * `id`
  * `username`
  * `email`
  * `role`
  * `is_coach_approved`
  * `region_code`

---

### 11. Coach Approval Logic (Sanity)

* Newly created users default to:

  * role = PLAYER
  * is_coach_approved = false
* Users with role = COACH are **not** considered approved unless explicitly set in admin
* Staff/superusers are treated as ADMIN in permission logic

---

### 12. Serializer Correctness

* `/api/v1/me/` GET uses **instance-mode serialization**
* `/api/v1/me/` PATCH (if enabled) uses `data=` with validation
* No `.is_valid()` is required for GET requests

---

### Exit Gate — Prompt #3

You may proceed to **Prompt #4 (Associations & Teams)** only if:

* All Prompt #1 and #2 checks remain green
* All tests pass
* `/api/v1/me/` returns correct role and region context
* Changes are committed

---

## Sanity Check — After Prompt #4 (Associations & Teams, Region-Scoped)

These checks verify the region-scoped Association and Team domain model, admin wiring, permissions, and read-only APIs.

---

### 13. Migrate & Run Tests

```bash
python manage.py migrate
python manage.py test
```

Expected:

* organizations app migrations apply cleanly
* All tests pass, including:

  * region-based filtering for associations and teams
  * region consistency validation (Association.region == Team.region)
  * write restrictions for non-admin users

---

### 14. Admin Sanity (Manual)

* Log into Django admin
* Verify you can:

  * Create an Association with a Region
  * Create a Team linked to that Association
* Verify validation prevents:

  * Creating a Team whose Region does not match its Association’s Region

---

### 15. Read-only API Verification (JWT Required)

#### List associations (BC region)

```bash
curl http://localhost:8000/api/v1/associations/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Host: bc.localhost:8000"
```

Expected:

* HTTP 200
* Only associations belonging to the `bc` region are returned

#### List teams (BC region)

```bash
curl http://localhost:8000/api/v1/teams/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Host: bc.localhost:8000"
```

Expected:

* HTTP 200
* Only teams belonging to the `bc` region are returned

---

### 16. Cross-Region Isolation

If another Region exists (e.g. `on`):

```bash
curl http://localhost:8000/api/v1/associations/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Host: on.localhost:8000"
```

Expected:

* HTTP 200
* No `bc` associations or teams appear in the response

---

### Exit Gate — Prompt #4

You may proceed to **Prompt #5 (Tryouts & Listings)** only if:

* All Prompt #1–#3 checks remain green
* All tests pass
* Associations and Teams are correctly filtered by region
* Admin validation prevents cross-region mismatches
* Changes are committed

---


## Sanity Check — After Prompt #5 (Tryouts Listings, Public Read)

These checks verify the public, region-scoped tryouts listing endpoints and the TryoutEvent model rules.

---

### 17. Migrate & Run Tests

```bash
python manage.py migrate
python manage.py test
````

Expected:

* tryouts migrations apply cleanly
* All tests pass, including:

  * region filtering for tryouts
  * active-only behavior
  * validation rules
  * permissions (anonymous reads allowed; non-admin writes blocked)

---

### 18. Public Tryouts API (No Auth Required)

#### List tryouts (BC region)

```bash
curl -i http://localhost:8000/api/v1/tryouts/ \
  -H "Host: bc.localhost:8000"
```

Expected:

* HTTP 200
* Response is filtered to the current region (bc)
* Only `is_active=true` tryouts appear

#### Retrieve a tryout (BC region)

```bash
curl -i http://localhost:8000/api/v1/tryouts/1/ \
  -H "Host: bc.localhost:8000"
```

Expected:

* HTTP 200 (if tryout exists in bc)

---

### 19. Cross-Region Isolation (If another Region exists)

```bash
curl -i http://localhost:8000/api/v1/tryouts/ \
  -H "Host: on.localhost:8000"
```

Expected:

* HTTP 200
* No `bc` tryouts appear

---

### 20. Write Restrictions (Sanity)

Writes should be blocked for non-admin/anonymous.

```bash
curl -i -X POST http://localhost:8000/api/v1/tryouts/ \
  -H "Host: bc.localhost:8000" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Tryout","start_date":"2026-01-10","end_date":"2026-01-10","location":"Test","registration_url":"https://example.com","association":1,"region":1}'
```

Expected:

* HTTP 401 (anonymous) or HTTP 403 (authenticated but non-admin)

---

### Exit Gate — Prompt #5

You may proceed to **Prompt #6 (Player Open Status / Transfer Portal Core)** only if:

* All Prompt #1–#4 checks remain green
* All tests pass
* `/api/v1/tryouts/` is public and region-filtered
* Only active tryouts are returned by default
* Changes are committed

---

## Sanity Check — After Prompt #6 (Player Open Status / Availability)

These checks verify player Open status, restricted search, allow-list visibility, region isolation, and expiration behavior.

---

### 21. Migrate & Run Tests

```bash
python manage.py migrate
python manage.py test
````

Expected:

* availability migrations apply cleanly
* All tests pass, including:

  * player self access to `/availability/me/`
  * coach search restricted to approved coaches/admin
  * region isolation
  * expiration filtering
  * allow-list enforcement

---

### 22. Player Can Manage Own Availability

1. Obtain JWT token via `/api/v1/auth/token/`

2. Toggle Open status:

```bash
curl -i -X PATCH http://localhost:8000/api/v1/availability/me/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d '{"is_open": true, "positions": ["OF"], "levels": ["AAA"]}'
```

Expected:

* HTTP 200
* Response shows `is_open=true`

---

### 23. Coach Search is Restricted

Unapproved coach:

* Expected HTTP 403 (or equivalent denial)

Approved coach or admin:

```bash
curl -i http://localhost:8000/api/v1/availability/search/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Host: bc.localhost:8000"
```

Expected:

* HTTP 200
* Results are filtered to:

  * `is_open=true`
  * not expired
  * request.region only
  * visibility allow-list rules

---

### 24. Exit Gate — Prompt #6

You may proceed to the next MVP prompt only if:

* All Prompt #1–#5 checks remain green
* All tests pass
* Open status is NOT publicly accessible
* Search is restricted to ADMIN + approved COACH
* Region + expiration + allow-list enforcement behaves correctly
* Changes are committed

---


## Sanity Check — After Prompt #7 (Contact Requests + Audit Logging)

These checks verify the end-to-end contact request flow, permissions, audit logging, and region isolation.

---

### 25. Migrate & Run Tests

```bash
python manage.py migrate
python manage.py test
```

Expected:

* contacts migrations apply cleanly
* All tests pass, including:

  * duplicate pending request prevention
  * non-open player blocked
  * coach approval + team membership enforcement
  * player-only approve/decline
  * audit log entries created

---

### 26. Coach Creates Contact Request

```bash
curl -i -X POST http://localhost:8000/api/v1/contact-requests/ \
  -H "Authorization: Bearer <coach_access_token>" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d '{"player_id":12,"requesting_team_id":3,"message":"We would like to connect."}'
```

Expected:

* HTTP 201
* status = `PENDING`
* Player contact details NOT exposed

---

### 27. Duplicate Pending Request Blocked

Repeat the same POST request.

Expected:

* HTTP 400 or 409
* Error indicating duplicate pending request

---

### 28. Player Responds to Contact Request

Approve:

```bash
curl -i -X POST http://localhost:8000/api/v1/contact-requests/<id>/respond/ \
  -H "Authorization: Bearer <player_access_token>" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d '{"status":"approved"}'
```

Decline:

```bash
curl -i -X POST http://localhost:8000/api/v1/contact-requests/<id>/respond/ \
  -H "Authorization: Bearer <player_access_token>" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d '{"status":"declined"}'
```

Expected:

* HTTP 200
* status updated
* responded_at populated

---

### 29. Audit Log Verification

In Django admin:

* Verify AuditLog entries exist for:

  * CONTACT_REQUEST_CREATED
  * CONTACT_REQUEST_APPROVED or CONTACT_REQUEST_DECLINED
* Entries include actor, target, region, timestamp

---

### 30. Region Isolation

* Create request under `bc.localhost`
* Attempt access under a different region host

Expected:

* Request not visible
* Access denied or empty result

---

### Exit Gate — Prompt #7

You may proceed only if:

* All Prompt #1–#6 checks remain green
* Contact requests are fully permission-gated
* Player consent is enforced
* Audit logging is complete and accurate
* Region isolation is intact
* Changes are committed

---



## Sanity Check — After Prompt #8 (PlayerProfile + /api/v1/profile/me/ + Privacy Defaults)

These checks verify global player profiles, self-only access, role gating, and privacy-by-default (no public listing).

---

### 31. Migrate & Run Tests

```bash
python manage.py migrate
python manage.py test
```

Expected:

* profiles migrations apply cleanly
* All tests pass, including non-player role blocking for `/api/v1/profile/me/`

---

### 32. Player Can GET Their Profile (Auto-Creates)

```bash
curl -i http://localhost:8000/api/v1/profile/me/ \
  -H "Authorization: Bearer <player_access_token>" \
  -H "Host: bc.localhost:8000"
```

Expected:

* HTTP 200
* A profile object is returned
* If this is first access, profile is auto-created

---

### 33. Player Can PATCH Their Profile

```bash
curl -i -X PATCH http://localhost:8000/api/v1/profile/me/ \
  -H "Authorization: Bearer <player_access_token>" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d '{"display_name":"J. Player","birth_year":2011,"positions":["OF"],"bats":"R","throws":"R"}'
```

Expected:

* HTTP 200
* Returned profile reflects updates

---

### 34. Non-Player Roles Are Blocked

Using a coach/admin/staff token:

```bash
curl -i http://localhost:8000/api/v1/profile/me/ \
  -H "Authorization: Bearer <non_player_access_token>" \
  -H "Host: bc.localhost:8000"
```

Expected:

* HTTP 403

---

### 35. Privacy Defaults — No Public Listing

```bash
curl -i http://localhost:8000/api/v1/profiles/
```

Expected:

* HTTP 404
* Confirms there is no public directory/list endpoint

---

### Exit Gate — Prompt #8

You may proceed only if:

* All Prompt #1–#7 checks remain green
* All tests pass
* `/api/v1/profile/me/` is self-only and player-only
* No public profile listing exists
* Changes are committed

---

## Sanity Check — After Prompt #9 (Committed Status)

These checks verify committed status behavior, exclusion from open searches, and contact request blocking.

---

### 36. Migrate & Run Tests

```bash
python manage.py migrate
python manage.py test
```

Expected:

* availability migrations apply cleanly
* All tests pass, including:
  * commit/uncommit behavior
  * committed exclusion from open searches
  * contact request blocking for committed players

---

### 37. Player Commits (Self Only)

```bash
curl -i -X PATCH http://localhost:8000/api/v1/availability/me/ \
  -H "Authorization: Bearer <player_access_token>" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d '{"is_committed": true}'
```

Expected:

* HTTP 200
* `is_committed=true`
* `is_open=false`
* `committed_at` populated

---

### 38. Open Players Search Excludes Committed

```bash
curl -i http://localhost:8000/api/v1/open-players/ \
  -H "Authorization: Bearer <coach_access_token>" \
  -H "Host: bc.localhost:8000"
```

Expected:

* HTTP 200
* Committed players are not returned

---

### 39. Contact Request Blocked for Committed Player

```bash
curl -i -X POST http://localhost:8000/api/v1/contact-requests/ \
  -H "Authorization: Bearer <coach_access_token>" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d '{"player_id":12,"requesting_team_id":3,"message":"We would like to connect."}'
```

Expected:

* HTTP 400
* Error indicates player is committed/unavailable

---

### 40. Audit Log Entry (If Enabled)

In Django admin:

* Verify AuditLog entries exist for:
  * `COMMITTED_SET` (and `COMMITTED_CLEARED` if used)
* Entries include actor, target, region, timestamp

---

### Exit Gate — Prompt #9

You may proceed only if:

* All Prompt #1–#8 checks remain green
* All tests pass
* Committed status excludes players from open searches
* Contact requests are blocked for committed players
* Audit logging (if enabled) is complete and accurate
* Changes are committed

---

## Sanity Check — After Prompt #10 (Seed Demo Data)

These checks verify the demo seed command and minimal demo data.

---

### 41. Migrate & Seed

```bash
python manage.py migrate
python manage.py seed_demo
```

Expected:

* Seed command runs without errors
* Output includes demo credentials

---

### 42. Run Tests

```bash
python manage.py test
```

Expected:

* All tests pass after seeding

---

### 43. Demo Tryouts (Public)

```bash
curl -i http://localhost:8000/api/v1/tryouts/ \
  -H "Host: bc.localhost:8000"
```

Expected:

* HTTP 200
* At least one tryout appears

---

### 44. Demo Open Players (Coach)

```bash
curl -i http://localhost:8000/api/v1/open-players/ \
  -H "Authorization: Bearer <coach_access_token>" \
  -H "Host: bc.localhost:8000"
```

Expected:

* HTTP 200
* Player1 appears in results

---

### 45. Demo Contact Request

```bash
curl -i -X POST http://localhost:8000/api/v1/contact-requests/ \
  -H "Authorization: Bearer <coach_access_token>" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d '{"player_id":<player_id>,"requesting_team_id":<team_id>,"message":"We would like to connect."}'
```

Expected:

* HTTP 201
* status = PENDING

---

### 46. Demo Contact Response (Player)

```bash
curl -i -X POST http://localhost:8000/api/v1/contact-requests/<id>/respond/ \
  -H "Authorization: Bearer <player_access_token>" \
  -H "Content-Type: application/json" \
  -H "Host: bc.localhost:8000" \
  -d '{"status":"approved"}'
```

Expected:

* HTTP 200
* status updated, responded_at populated

---

### Exit Gate — Prompt #10

You may proceed only if:

* All Prompt #1–#9 checks remain green
* Seed command runs cleanly on an empty DB
* Demo tryouts, open players, and contact requests work
* Changes are committed


---
## Sanity Check — After Prompt #11 (Permission & Isolation Hardening)

These checks verify that **no cross-role, cross-team, or cross-region data leakage** is possible.

---

### 47. Migrate & Run Full Test Suite

```bash
python manage.py migrate
python manage.py test
```

Expected:

* All tests pass
* No permission or isolation regressions

---

### 48. Coach / Team Isolation

Using a coach assigned to **Team A**:

Attempt to create a contact request for **Team B**.

Expected:

* HTTP 403 or 400
* Clear error indicating team permission violation

---

### 49. Open Player Visibility Enforcement

Using an approved coach:

```bash
curl -i http://localhost:8000/api/v1/open-players/ \
  -H "Authorization: Bearer <coach_access_token>" \
  -H "Host: bc.localhost:8000"
```

Expected:

* HTTP 200
* ONLY players who explicitly allow the coach’s team appear

---

### 50. Player Privacy Enforcement

Using Player A token:

* Attempt to fetch Player B profile
* Attempt to fetch Player B availability

Expected:

* HTTP 403 or 404
* No data leakage

---

### 51. Region Isolation (Hard Block)

Create data under `bc.localhost`, then attempt access under another region:

```bash
curl -i http://localhost:8000/api/v1/open-players/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Host: on.localhost:8000"
```

Expected:

* HTTP 200 with empty result OR HTTP 403
* No BC data visible

---

### 52. Admin Still Region-Bound

Using admin token:

* Access BC data under `on.localhost`

Expected:

* Access denied OR empty
* Admin does NOT bypass region scoping

---

### Exit Gate — Prompt #11

You may proceed only if:

* All tests pass
* No cross-role access is possible
* No cross-team access is possible
* No cross-region access is possible
* Player data is private by default
* Changes are committed

---

**After Prompt #11, the MVP is considered permission-complete and security-stable.**

## Sanity Check — After Prompt #12 (Web UI Foundation + Mobile-Friendly UI)

These checks verify that the initial **Web UI layer** is:

* professional-looking
* mobile-friendly
* region-aware
* role-aware
* does NOT weaken backend permissions or isolation guarantees

This prompt introduces **read-only and navigational UI only** (no new business logic).

---

### 53. Migrate, Seed, and Run Server

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Expected:

* Server starts without errors
* Static files load correctly
* No template errors or missing static warnings

---

### 54. Landing Page & Navigation (Public)

Visit:

```
http://bc.localhost:8000/
```

Expected:

* Page loads successfully
* Professional layout (header, hero, spacing, typography)
* Navigation bar visible
* No authentication required
* Page is readable at both desktop and mobile widths

Mobile sanity:

* Resize browser to narrow width
* Navbar collapses correctly
* No horizontal scrolling
* Tap targets are usable

---

### 55. Public Tryouts — Web UI (Region-Scoped)

Visit:

```
http://bc.localhost:8000/tryouts/
```

Expected:

* List of tryouts rendered as cards
* Only BC-region tryouts appear
* Layout remains readable on mobile
* Clicking a tryout navigates to its detail page

Try detail view:

```
http://bc.localhost:8000/tryouts/<id>/
```

Expected:

* Page loads successfully
* Correct tryout details shown
* No cross-region data leakage

---

### 56. Cross-Region Isolation (Web UI)

If another region exists (e.g. `on`):

```
http://on.localhost:8000/tryouts/
```

Expected:

* No BC tryouts visible
* Either empty list or region-appropriate data only

Direct detail access under wrong region:

```
http://on.localhost:8000/tryouts/<bc_tryout_id>/
```

Expected:

* 404 or access blocked
* No BC data rendered

---

### 57. Authentication UI

Visit:

```
http://bc.localhost:8000/accounts/login/
```

Expected:

* Login page loads correctly
* Form is usable on mobile
* No styling regressions

Log in using seeded credentials and confirm Logout works from the navbar.

Expected:

* Successful login
* Redirects to `/dashboard/`

---

### 58. Role-Aware Dashboard Routing

After login, visit:

```
http://bc.localhost:8000/dashboard/
```

Expected redirect behavior:

* Player → `/player/`
* Coach → `/coach/`
* Admin → `/admin/`

Expected:

* No permission errors
* No infinite redirects
* Placeholder dashboards render without error

---

### 59. Unauthorized Access Protection (Web UI)

While logged in as a **player**:

* Attempt to visit `/coach/`

Expected:

* Access denied OR redirect to dashboard
* No coach-specific content rendered

While logged in as a **coach**:

* Attempt to visit `/player/`

Expected:

* Access denied OR redirect to dashboard

---

### 60. UI Does Not Bypass API Permissions

Sanity assertion:

* Web UI pages do NOT expose:

  * Open player search results
  * Contact request creation
  * Player availability of others
* All sensitive operations remain API-gated and permission-protected

Expected:

* UI is navigation + display only
* No backend permission regressions

---

### 61. Run Tests (Including UI Tests)

```bash
python manage.py test
```

Expected:

* All tests pass
* Web UI region-isolation test passes
* No regressions in API or permission tests

---

### Exit Gate — Prompt #12

You may proceed to **Prompt #13 (Player Web UI: Profile, Availability, Allow-List, Inbox)** only if:

* All Prompt #1–#11 checks remain green
* Web UI renders correctly on desktop and mobile
* Public tryouts are region-scoped in the UI
* Login and dashboard routing are role-aware
* No backend permissions or isolation guarantees are weakened
* Changes are committed

---

**After Prompt #12, the project has a professional, mobile-friendly UI shell suitable for real users.**

---
## Sanity Check — After Prompt #13 (Web UI: Player & Coach Core Workflows)

These checks verify that the Web UI is functional, mobile-friendly, role-aware, and safely layered on top of the existing API without bypassing permissions or region isolation.

---

### 62. Migrate & Run Full Test Suite

```bash
python manage.py migrate
python manage.py test
```

Expected:

* No new migrations required
* All existing API + permission tests still pass
* New Web UI tests pass

---

### 63. Landing Page (Public)

```bash
curl -i http://bc.localhost:8000/
```

Expected:

* HTTP 200
* Page renders without authentication
* Contains a clear headline explaining the portal purpose
* Mobile viewport meta tag is present

---

### 64. Public Tryouts Browse (Web UI)

```bash
curl -i http://bc.localhost:8000/tryouts/
```

Expected:

* HTTP 200
* Tryouts rendered as cards or list items
* Dates, teams, and locations visible
* Layout stacks correctly on mobile widths

---

### 65. Tryout Detail (Region Isolation)

```bash
curl -i http://bc.localhost:8000/tryouts/<id>/
```

Expected:

* HTTP 200 for tryouts in BC region
* Correct tryout details displayed

Cross-region check:

```bash
curl -i -H "Host: on.localhost:8000" http://localhost:8000/tryouts/<id>/
```

Expected:

* HTTP 404 or redirect
* No BC tryout data leaked across regions

---

### 66. Authentication Pages

```bash
curl -i http://bc.localhost:8000/accounts/login/
```

Expected:

* HTTP 200
* Login form renders correctly
* Mobile-friendly input sizing and spacing

Logout:

* Use the navbar logout button (POST)
* Expected redirect to landing page

---

### 67. Post-Login Redirect

After logging in via the Web UI:

Expected:

* User is redirected to `/dashboard/`
* `/dashboard/` immediately redirects based on role:

  * PLAYER → `/player/`
  * COACH → `/coach/`
  * ADMIN → `/admin/`

---

### 68. Player Pages (Authenticated)

Using a PLAYER account:

```bash
curl -i http://bc.localhost:8000/player/
```

Expected:

* HTTP 200
* Navigation to profile, availability, and contact requests
* No other players’ data visible

Additional pages:

```bash
curl -i http://bc.localhost:8000/player/profile/
curl -i http://bc.localhost:8000/player/availability/
curl -i http://bc.localhost:8000/player/requests/
```

Expected:

* Each page returns HTTP 200
* Availability page shows committed banner when applicable

Unauthenticated access:

```bash
curl -i http://bc.localhost:8000/player/
```

Expected:

* HTTP 302 redirect to login

---

### 69. Coach Dashboard (Role-Gated)

Using an approved COACH account:

```bash
curl -i http://bc.localhost:8000/coach/
```

Expected:

* HTTP 200
* Coach-specific content rendered
* Only permitted teams / open players visible

Additional pages:

```bash
curl -i http://bc.localhost:8000/coach/teams/
curl -i http://bc.localhost:8000/coach/open-players/
curl -i http://bc.localhost:8000/coach/requests/
curl -i http://bc.localhost:8000/coach/requests/new/
```

Expected:

* Each page returns HTTP 200
* Open players list respects allow-list filtering

Non-coach access:

```bash
curl -i http://bc.localhost:8000/coach/
```

Expected:

* HTTP 403 or redirect
* No coach data leaked

---

### 70. Web Form Workflows

Player availability:

Expected:

* Can toggle Open status
* Can set positions/levels/expiry
* Can update allow-listed teams (region-scoped only)
* Committed toggle works (committed players are hidden)

---

Coach contact requests:

Expected:

* Coach can create a request for a player they are allowed to view
* Player can approve/decline the request in their inbox
* Requests list shows status updates

---

### 71. UI Permission Fail-Safe

Manually force an unauthorized state (e.g. player accessing coach page).

Expected:

* Friendly error or redirect
* No stack trace
* No sensitive data rendered

---

### 72. Mobile Responsiveness (Manual)

Using browser dev tools or a phone:

* Navbar collapses correctly
* Cards stack vertically
* Tap targets are usable
* No horizontal scrolling

---

### Exit Gate — Prompt #13

You may proceed only if:

* All Prompt #1–#12 checks remain green
* Web UI is usable on mobile and desktop
* Role-based routing behaves correctly
* No permission or region isolation regressions exist
* All changes are committed

---

**After Prompt #13, the MVP is considered end-user usable via the Web UI.**

---

## Sanity Check — After Prompt #14 (Coach Signup, Auto-Approval, Email Verification)

These checks verify the coach signup flow, email verification, and domain-based auto-approval rules.

---

### 73. Migrate & Run Tests

```bash
python manage.py migrate
python manage.py test
```

Expected:

* New migrations apply cleanly
* Tests for coach signup and verification pass

---

### 74. Association Domains (Admin)

In Django admin:

* Edit an Association and set:
  * `official_domain` (e.g. `vancouverminor.com`)
  * Optional `website_url`

Expected:

* Fields appear in admin and save correctly

---

### 75. Coach Signup Page

Visit:

```
http://bc.localhost:8000/signup/coach/
```

Expected:

* Form renders with first/last name, association, email, phone, password, confirm password
* Association dropdown is region‑scoped
* Inline explanation about domain-based auto-approval is visible

---

### 76. Email Verification Required

Submit the form with a valid association and email.

Expected:

* User is created with `is_active = False`
* Verification email is sent
* User cannot log in before clicking the verification link

---

### 77. Domain Match Auto-Approval

Use an email that matches the association’s `official_domain`.

Expected:

* `is_coach_approved = True`
* After verification, the coach can log in and access coach pages

---

### 78. Domain Mismatch Requires Admin Approval

Use a non-matching email domain.

Expected:

* `is_coach_approved = False`
* After verification, coach can log in but cannot access coach pages until approved

---

### Exit Gate — Prompt #14

You may proceed only if:

* All Prompt #1–#13 checks remain green
* Coach signup works end‑to‑end
* Email verification is required before login
* Auto-approval only happens on domain match
* Region isolation remains intact
* Changes are committed

---

## Sanity Check — After Prompt #15 (Player Signup + Email Verification)

These checks verify player signup, email verification, and onboarding profile data.

---

### 79. Migrate & Run Tests

```bash
python manage.py migrate
python manage.py test
```

Expected:

* New migrations apply cleanly
* Player signup + verification tests pass

---

### 80. Player Signup Page

Visit:

```
http://bc.localhost:8000/signup/player/
```

Expected:

* Form renders required fields
* Association dropdown is region‑scoped
* Privacy explanation is visible

---

### 81. Email Verification Required

Submit the signup form with a unique email.

Expected:

* User created with `is_active = False`
* Verification email sent
* User cannot log in before verification

---

### 82. Profile Creation and Persistence

After verifying the email:

Expected:

* User is activated
* PlayerProfile is created with birth year and visibility settings
* Email is not editable in profile UI

---

### 83. Availability Initialization

If “Available for transfer” was selected at signup:

Expected:

* PlayerAvailability exists
* `is_open = true`, `is_committed = false`

If not selected:

* Availability remains closed or unset

---

### Exit Gate — Prompt #15

You may proceed only if:

* All Prompt #1–#14 checks remain green
* Player signup works end‑to‑end
* Email verification is required before login
* Profile data persists correctly
* Availability initialization behaves correctly
* Changes are committed

---

## Sanity Check — After Prompt #16 (MVP Closeout)

These checks verify tryout CRUD for coaches, API parity, allowed-teams management, and contact detail visibility.

---

### 84. Migrate & Run Tests

```bash
python manage.py migrate
python manage.py test
```

Expected:

* New migrations apply cleanly
* Tryout CRUD, filters, allowed teams, and contact detail tests pass

---

### 85. Coach Tryout Management (Web)

Log in as an approved coach and visit:

```
http://bc.localhost:8000/coach/tryouts/
```

Expected:

* Coach can create a new tryout
* Edit updates are saved
* Cancel hides the tryout from public browse

---

### 86. Tryout API Filters

Use the API list endpoint with filters:

```
http://bc.localhost:8000/api/v1/tryouts/?age_group=13U
http://bc.localhost:8000/api/v1/tryouts/?level=AAA
```

Expected:

* Only matching tryouts are returned

---

### 87. Allowed Teams API

As a player, manage allow‑listed teams:

```
GET /api/v1/availability/allowed-teams/
POST /api/v1/availability/allowed-teams/   (team_id required)
DELETE /api/v1/availability/allowed-teams/<team_id>/
```

Expected:

* Add/remove works
* Only the player can modify their list

---

### 88. Contact Details on Approval

After a player approves a request:

Expected:

* Coach view shows player email (and phone if present)
* Pending/declined requests do not show contact info

---

### 89. Tryout Audit Logs

Create/edit/cancel a tryout.

Expected:

* AuditLog entries exist for TRYOUT_CREATED/TRYOUT_UPDATED/TRYOUT_CANCELED

---

### 90. Association Info Pages

Visit an association detail page:

```
http://bc.localhost:8000/associations/<id>/
```

Expected:

* Page renders for associations in the current region
* Cross-region associations return 404
* Links appear from tryouts and coach team views
* Logo displays when uploaded (square, 200–800px)

---

### Exit Gate — Prompt #16

You may proceed only if:

* All Prompt #1–#15 checks remain green
* Tryout CRUD works end‑to‑end (web + API)
* API filters and allowed‑teams endpoints work
* Contact details are only visible after approval
* Tryout audit logs are recorded
* Association info pages render correctly
* Changes are committed

---

## Sanity Check — After Prompt #17 (Docs Alignment)

These checks verify that documentation matches implemented MVP behavior.

---

### 91. Docs Consistency Review

Confirm that docs no longer claim unimplemented features:

* `README.md` does not mention Team Needs.
* `REQUIREMENTS.md` labels Team Needs, Allowed Regions, and per-section privacy as post‑MVP.
* `ARCHITECTURE.md` reflects MVP visibility controls (single profile visibility + allowed teams).
* `CODEX_TASKS.md` matches current API endpoints.

---

### Exit Gate — Prompt #17

You may proceed only if:

* All Prompt #1–#16 checks remain green
* Documentation matches actual implementation
* Changes are committed
