# SANITY_CHECKLIST.md — Incremental Verification Gates

This document defines **incremental sanity checks after each major Codex prompt**.

Each section is **append-only**.
- Earlier sections are never modified.
- New prompts add new sections at the bottom.

This allows safe progression without rewriting prior verification steps.

---

## Sanity Check — After Prompt #1 (Django + DRF + JWT Bootstrap)

These checks verify that the core Django + DRF + JWT foundation is correct.

### 1. Environment & Dependencies

- Virtual environment is active in VS Code terminal:
  ```
  (venv) portal %
  ```
- Python executable points to venv:
  ```bash
  which python
  # .../venv/bin/python
  ```
- Python version is 3.10+ (tested on 3.13):
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
- No install errors
- Migrations apply cleanly

---

### 3. Run Server

```bash
python manage.py runserver
```

Expected:
- Server starts without errors
- No startup warnings related to DRF or auth

---

### 4. Health Endpoint (Core Check)

```bash
curl -i http://bc.localhost:8000/api/v1/health/
```

Expected:
- HTTP 200
- Body:
  ```json
  {"status": "ok"}
  ```

This confirms:
- Django routing works
- DRF is installed
- Versioned API base is live

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
- Token issuance works
- Protected endpoint returns HTTP 200

---

### Exit Gate — Prompt #1

You may proceed to **Prompt #2** only if:
- Health endpoint returns HTTP 200
- JWT auth works
- Server runs cleanly
- Changes are committed

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
- Region seed migration runs successfully (BC exists)
- Middleware tests pass for `bc`, `localhost`, and alternate regions

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
- All return HTTP 200
- Region resolution is asserted via automated tests

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
- All Prompt #1 checks remain green
- Region middleware behaves correctly
- Tests pass
- Changes are committed

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

## Future Prompts

For each new major prompt:
- Append a new **Sanity Check — After Prompt #N** section
- Do **not** modify earlier sections
- Treat each section as an immutable verification gate

---

This checklist is intentionally append-only and audit-friendly.

