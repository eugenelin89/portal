# SANITY_CHECKLIST.md — Post Prompt #1 Verification

This checklist verifies that **Prompt #1 (Django + DRF + JWT bootstrap)** completed correctly.

Run these checks **before moving on** to region/subdomain work.

---

## 1. Environment & Dependencies

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

## 2. Install & Migrate

```bash
pip install -r requirements.txt
python manage.py migrate
```

Expected:
- No install errors
- Migrations apply cleanly

---

## 3. Run Server

```bash
python manage.py runserver
```

Expected:
- Server starts without errors
- No startup warnings related to DRF or auth

---

## 4. Health Endpoint (Core Check)

```bash
curl -s http://bc.localhost:8000/api/v1/health/
```

Expected:
```json
{"status": "ok"}
```

This confirms:
- Django routing works
- DRF is installed
- Versioned API base is live

---

## 5. Admin & JWT Smoke Test

### Create admin user
```bash
python manage.py createsuperuser
```

### Obtain JWT token
```bash
curl -s -X POST http://bc.localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"<user>","password":"<pass>"}'
```

Expected:
- JSON response containing `access` and `refresh` tokens

### Call protected endpoint
```bash
curl -s http://bc.localhost:8000/api/v1/protected/ \
  -H "Authorization: Bearer <access_token>"
```

Expected:
- 200 response confirming auth works

---

## 6. Host / Subdomain Readiness

Verify `ALLOWED_HOSTS` includes `.localhost`:
```python
ALLOWED_HOSTS = [".localhost", "localhost", "127.0.0.1"]
```

This is required for upcoming region/subdomain middleware.

---

## 7. Git Hygiene

Commit once all checks pass:
```bash
git status
git add .
git commit -m "Bootstrap Django + DRF + JWT + health endpoint"
```

---

## Exit Criteria

You may proceed to **Prompt #2 (Region model + subdomain middleware)** only if:
- Health endpoint returns OK
- JWT auth works
- Server runs cleanly
- Changes are committed

---

This checklist is intentionally short and repeatable.

