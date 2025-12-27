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
