# BC Baseball Transfer Portal

A **league-friendly, privacy-first transfer portal** for youth baseball in British Columbia. The BC Baseball Transfer Portal reduces chaos during tryout season by centralizing tryout information and providing a structured, opt‑in way for players and teams to connect after tryouts.

This project is built with **Django**, designed to be **mobile-friendly**, and architected so that each province can operate under its own subdomain (e.g. `bc.transferportal.ca`) while sharing the same underlying system.

---

## 🎯 Problem Statement
After travel team tryouts, families and associations often scramble:
- Families panic and cold-call other associations looking for opportunities.
- Associations with incomplete rosters rely on informal networks to find players.
- The process is messy, inefficient, and emotionally charged.

The BC Baseball Transfer Portal introduces structure, transparency, and privacy into this process.

---

## ✅ What This System Does
- **Centralizes tryout listings** with dates, locations, and registration links.
- Allows players to **self-declare availability (“Open”)** without stigma.
- Enables teams to **request contact** with Open players in a controlled, auditable way.
- Keeps **players free** while supporting league governance and privacy.

---

## 🚫 What This System Is Not
- Not a public, open-by-default social network (in the MVP).
- Not a rankings or leaderboard platform.
- Not an automated roster or acceptance system.
- Not a system that labels players as “cut.”

Social features may be added later with strict privacy controls.

---

## 👥 User Roles
### Player / Parent
- Create and manage a player profile
- Browse tryouts
- Toggle Open / Not Open status
- Control who can see recruiting availability
- Accept or decline contact requests

### Coach / Manager
- Post tryout listings
- View Open players (if permitted)
- Send contact requests
- Coach signup with email verification; auto-approval when email domain matches association

### Association / League Admin
- Approve coach accounts
- Manage teams and associations
- Maintain association info pages
- Configure tryout rules and windows
- Review audit logs

---

## 🧩 Core Features
- Role-based authentication and access control
- Coach signup with email verification + domain-based auto-approval
- Tryout listings with filtering
- Association info pages with contact details and listed tryouts
- Association logos via URL (recommended square, 200–800px)
- Regional homepage association dropdown
- Regional homepage hero banner image
- Player profiles (private by default)
- Optional achievement and highlight showcase
- Open availability status with allow-listed team visibility
- Contact request workflow
- Audit logging for sensitive actions

---

## 🏗️ Architecture Overview
- **Django monolith (MVP)**
- **Single codebase**, multiple regions via subdomains
- Example:
  - `transferportal.ca` → landing / marketing
  - `bc.transferportal.ca` → BC Baseball Transfer Portal

Key design decisions:
- Players have **one global profile**.
- Associations and teams are **region-scoped**.
- Cross-region visibility is **opt-in and player-controlled**.

For full details, see **ARCHITECTURE.md**.

---

## 📱 Mobile Support
- Responsive, mobile-first web UI
- Designed to evolve into a dedicated mobile app
- APIs (via Django REST Framework) planned for future mobile clients

---

## 🛠️ Tech Stack
- **Backend:** Django
- **Frontend:** Django templates (responsive UI)
- **Database:** PostgreSQL (recommended)
- **Auth:** Django authentication + role-based access

---

## 📈 Monetization (High-Level)
- Free for players and parents
- Funded by leagues and associations
- Optional premium tools for teams (future)

---

## 📄 Documentation
- **README.md** — project overview (this file)
- **ARCHITECTURE.md** — technical design and system architecture
- **Requirements document** — functional and non-functional requirements

---

## ✅ Sanity Checks (Quick Run)

Use the helper script to run migrations, tests, and basic API checks:

```bash
chmod +x scripts/run_sanity_checks.sh
./scripts/run_sanity_checks.sh
```

Optional JWT check (requires an existing user):

```bash
SANITY_USERNAME=<user> SANITY_PASSWORD=<pass> ./scripts/run_sanity_checks.sh
```

---

## 🚀 Project Status
This repository is under active development as an MVP.

Initial focus:
- BC-only deployment
- Core tryout and Open-status workflow
- Mobile-friendly experience

---

## 📌 License
TBD

---

## 🙌 Acknowledgements
Inspired by the NCAA transfer portal model, adapted for **local youth baseball** with a focus on privacy, dignity, and league governance.
