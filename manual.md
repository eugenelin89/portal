# BC Baseball Transfer Portal — User Manual

This manual explains how to run the system locally and complete the core workflows as a player, coach, or admin. It is written for a first-time user evaluating the MVP.

---

## 1) What This System Does

The BC Baseball Transfer Portal is a privacy-first, region-scoped portal for tryouts and post‑tryout recruiting.

You can:
- Browse tryouts (public)
- Manage player profile and open availability (players)
- Request contact with open players (approved coaches)
- Approve or decline contact requests (players)

The system is region-aware by subdomain. For example, `bc.localhost` maps to the BC region.

---

## 2) Quick Start (Local)

### 2.1 Install and migrate

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

### 2.2 Seed demo data (recommended)

```bash
python manage.py seed_demo
```

This creates:
- Admin: `admin / adminpass123`
- Coach: `coach1 / coachpass123` (approved coach)
- Player: `player1 / playerpass123`
- BC region, association, teams, tryout, player profile, and open availability

Note: demo users are active immediately; the signup flow below requires email verification.

### 2.3 Run the server

```bash
python manage.py runserver
```

Open:
- Landing page: `http://bc.localhost:8000/`
- Admin: `http://bc.localhost:8000/admin/`

If `bc.localhost` does not resolve, add it to your hosts file as described in `setup.md`.

### 2.4 Email configuration (local)

Signup verification emails use the configured email backend.

For local development, you can use the console backend to print verification links:
```bash
export EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
export DEFAULT_FROM_EMAIL=no-reply@transferportal.local
```

For SMTP (Gmail example), set:
```bash
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER=your_account@gmail.com
export EMAIL_HOST_PASSWORD=your_app_password
export DEFAULT_FROM_EMAIL=your_account@gmail.com
```

---

## 3) Navigation Overview

Top navigation includes:
- Tryouts (public)
- Dashboard (logged-in users)
- Admin (staff users)
- Username and Logout (logged-in users)

The region code badge appears in the navbar.

---

## 4) Public Flow: Browse Tryouts

### 4.1 Landing page

Visit:
```
http://bc.localhost:8000/
```

You can access tryouts directly from the hero CTA.
Use the association dropdown to jump to an association info page.
The hero banner uses a static image (`static/img/bc-hero.png`).

### 4.2 Tryouts list

Visit:
```
http://bc.localhost:8000/tryouts/
```

Use filters for:
- Age group
- Level
- Date range

Each tryout card includes:
- Name
- Date range
- Location
- Register button (external link)
- Association link (info page)

### 4.3 Tryout detail

Click a tryout card to view details and registration.

### 4.4 Association info

Association pages include public details, contact information, and upcoming tryouts from the same association.
Use the "Search Tryouts" button to return to the tryouts browse page.
Links appear on tryout list/detail and team pages.
Logos appear when a logo URL is provided.

---

## 5) Player Workflow

### 5.0 Player signup (new users)

Visit:
```
http://bc.localhost:8000/signup/player/
```

Expected:
- Account is created inactive.
- A verification email link is sent via the configured email backend.
- You must verify before logging in.

Log in as a player:
```
username: player1
password: playerpass123
```

### 5.1 Player dashboard

Visit:
```
http://bc.localhost:8000/dashboard/
```

You will be routed to `/player/` and see quick links for:
- Edit profile
- Availability
- Contact requests

### 5.2 Edit player profile

Visit:
```
http://bc.localhost:8000/player/profile/
```

You can edit:
- Display name
- Birth year
- Positions
- Bats / Throws
- Profile visibility and visible associations
- Optional links and bio

### 5.3 Availability (Open status)

Visit:
```
http://bc.localhost:8000/player/availability/
```

You can:
- Toggle Open status
- Select positions and levels
- Set an optional expiry
- Choose allow‑listed teams (region‑scoped)

Important:
- If you mark yourself Committed, Open is disabled and you are hidden from coach searches.

### 5.4 Committed toggle

On the Availability page, use the Committed card to:
- Mark yourself committed (hidden from searches)
- Clear committed status (return to open eligibility)

### 5.5 Contact requests

Visit:
```
http://bc.localhost:8000/player/requests/
```

You can:
- Approve requests
- Decline requests

Approved requests are recorded and visible to the requesting coach.

---

## 6) Coach Workflow (Approved Coaches Only)

### 6.0 Coach signup (new users)

Visit:
```
http://bc.localhost:8000/signup/coach/
```

Expected:
- Account is created inactive.
- A verification email link is sent via the configured email backend.
- If the email domain matches the association’s official domain, approval is automatic.
- Otherwise, an admin must approve the coach before coach pages are accessible.

Log in as a coach:
```
username: coach1
password: coachpass123
```

### 6.1 Coach dashboard

Visit:
```
http://bc.localhost:8000/dashboard/
```

You will be routed to `/coach/` with links to your teams, open players, and sent requests.

### 6.2 My teams

Visit:
```
http://bc.localhost:8000/coach/teams/
```

Shows teams you are assigned to via team memberships.

### 6.2A Manage tryouts

Visit:
```
http://bc.localhost:8000/coach/tryouts/
```

You can:
- Create tryouts for your teams
- Edit existing tryouts
- Cancel a tryout (removes it from public listings)

### 6.3 Open players

Visit:
```
http://bc.localhost:8000/coach/open-players/
```

You will only see players who:
- Are open
- Are not committed
- Have not expired
- Have allow‑listed one of your teams

Use “View details” to open a specific player and “Request contact” to start outreach.

### 6.4 Send a contact request

Visit:
```
http://bc.localhost:8000/coach/requests/new/
```

Choose:
- Player (only allow‑listed players appear)
- Requesting team (only your teams)
- Optional message

If a pending request already exists for that player+team, the system blocks duplicates.

### 6.5 Sent requests

Visit:
```
http://bc.localhost:8000/coach/requests/
```

Track request status:
- Pending
- Approved
- Declined

When approved, player contact details (email, phone if provided) are shown.

---

## 7) Admin Workflow

Log in as admin:
```
username: admin
password: adminpass123
```

### 7.1 Admin site

Visit:
```
http://bc.localhost:8000/admin/
```

Admin can:
- Manage regions, associations, teams
- Approve coach accounts
- Review tryouts and contact requests
- Set association logo URLs (recommended square, 200–800px)

---

## 8) API (Optional / Advanced)

The system exposes a REST API under:
```
http://bc.localhost:8000/api/v1/
```

Key endpoints:
- `GET /health/`
- `POST /auth/token/` (JWT)
- `GET /me/`
- `GET /tryouts/` (public)
- `GET/PATCH /availability/me/`
- `GET/POST /availability/allowed-associations/`
- `DELETE /availability/allowed-associations/<association_id>/`
- `GET /availability/search/` (approved coach or admin)
- `GET /open-players/` (approved coach or admin)
- `GET/PATCH /profile/me/` (player only)
- `POST /contact-requests/`
- `POST /contact-requests/<id>/respond/`

For complete automated verification, run:
```bash
./scripts/run_sanity_checks.sh
```

---

## 9) Troubleshooting

- **DisallowedHost**: ensure `.localhost` is in `ALLOWED_HOSTS` and restart the server.
- **Coach access denied**: confirm the coach profile is approved in admin.
- **Open players empty**: ensure the player is open and has allow‑listed the coach’s team.
- **Duplicate contact request**: only one pending request per player+team is allowed.

---

## 10) What’s Next

Planned additions (see `mvp_scope.md` and `requirements.md`):
- Team needs postings
- More detailed audit log UI
- Additional region rollouts
