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

## Future Prompts

For each new major prompt:
- Append a new **Sanity Check — After Prompt #N** section
- Do **not** modify earlier sections
- Treat each section as an immutable verification gate

---

This checklist is intentionally append-only and audit-friendly.

