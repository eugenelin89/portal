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
