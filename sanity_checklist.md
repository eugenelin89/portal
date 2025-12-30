# SANITY_CHECKLIST.md — Incremental Verification Gates

This document defines **incremental sanity checks after each major Codex prompt**.

Each section is **append-only**.

* Earlier sections are never modified.
* New prompts add new sections at the bottom.


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
