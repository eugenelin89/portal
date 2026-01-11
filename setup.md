# SETUP.md — BC Baseball Transfer Portal

This document explains how to set up and run the **BC Baseball Transfer Portal** locally for development.

The project is built with **Django** and is designed to run as a single codebase that supports region-based subdomains (e.g. `bc.transferportal.ca`).

---

## 1. Prerequisites
Make sure you have the following installed:

- **Python 3.10+** (3.11 recommended)
- **pip** (comes with Python)
- **virtualenv** or **venv**
- **Git**

Optional but recommended:
- **PostgreSQL** (SQLite can be used for quick local development)

---

## 2. Clone the Repository
```bash
git clone <your-repo-url>
cd bc-baseball-transfer-portal
```

---

## 3. Create and Activate a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```

Upgrade pip:
```bash
pip install --upgrade pip
```

---

## 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 5. Environment Variables
Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=dev-secret-key
ALLOWED_HOSTS=.localhost,.transferportal.ca
```

> Note: In production, `SECRET_KEY` and other secrets must be stored securely.

---

## 6. Database Setup
### Option A: SQLite (Quick Start)
No additional setup required.

### Option B: PostgreSQL (Recommended)
1. Create a database:
```sql
CREATE DATABASE transferportal;
```
2. Update `.env` with database credentials:
```env
DB_NAME=transferportal
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

---

## 7. Run Migrations
```bash
python manage.py migrate
```

---

## 8. Create a Superuser
```bash
python manage.py createsuperuser
```

This account will be used to access the Django admin and manage regions, associations, and approvals.

---

## 9. Local Subdomain Setup (Important)
To simulate `bc.transferportal.ca` locally, update your hosts file.

### macOS / Linux
Edit `/etc/hosts`:
```text
127.0.0.1   bc.localhost
```

### Windows
Edit `C:\Windows\System32\drivers\etc\hosts`:
```text
127.0.0.1   bc.localhost
```

This allows you to access the app at:
```
http://bc.localhost:8000
```

---

## 10. Run the Development Server
```bash
python manage.py runserver
```

Then open:
- **BC region:** http://bc.localhost:8000
- **Admin:** http://bc.localhost:8000/admin
- **Coach signup:** http://bc.localhost:8000/signup/coach/

Email verification links are printed to the console in development.

---

## 10A. Seed Demo Data (Optional)

Use the demo seed command to create a minimal, deterministic dataset:

```bash
python manage.py seed_demo
```

This creates:
- BC region, one association, and three teams
- Admin, coach, and player demo users (credentials printed)
- Player profile + availability (open and allow-listed)
- One tryout event

---

## 11. First-Time Setup (Admin)
After logging into the admin panel:
1. Create a **Region** (code: `bc`)
2. Create an **Association** under BC
3. Create **Teams** under the association
4. Approve coach accounts

---

## 12. Common Issues
- **DisallowedHost error**: Ensure `.localhost` is included in `ALLOWED_HOSTS`
- **Subdomain not working**: Confirm hosts file entry and restart browser
- **Migration errors**: Check database settings in `.env`

---

## 13. Next Steps
- Review **REQUIREMENTS.md** for system behavior
- Review **ARCHITECTURE.md** for design decisions
- Begin implementing MVP features

---

## 14. Production Notes (Later)
- Use wildcard DNS: `*.transferportal.ca`
- Use HTTPS with wildcard certificates
- Set `DEBUG=False`

---

Happy building ⚾🚀
