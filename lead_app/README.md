# Thrive Lead Manager — Deployment Guide

Internal inbound lead management application built with Flask + PostgreSQL, hosted on PythonAnywhere.

---

## Architecture Overview

| Component | Technology |
|---|---|
| Backend | Python 3.10+ / Flask |
| Database | PostgreSQL |
| ORM + Migrations | SQLAlchemy + Flask-Migrate (Alembic) |
| Authentication | Flask-Login + Werkzeug password hashing |
| Frontend | Jinja2 + Tailwind CSS (CDN) + HTMX |
| Gmail Integration | Gmail API (OAuth 2.0 with refresh token) |
| Email (password resets) | Gmail SMTP via App Password |
| Scheduler | Python `schedule` library as a PythonAnywhere Always-On Task |
| CSRF Protection | Flask-WTF |

---

## Pre-Deployment Checklist

### 1. Create a Gmail App Password

The app uses a single **Gmail App Password** for both reading emails (IMAP) and sending password resets (SMTP). No Google Cloud project or OAuth setup is needed.

1. Log into `data@thrivemediagroup.co.uk` at [myaccount.google.com](https://myaccount.google.com)
2. Go to **Security → 2-Step Verification → App Passwords**
   - 2-Step Verification must already be enabled on the account
3. Create a new App Password — name it "Thrive Lead Manager"
4. Save the 16-character password (no spaces) — this is your `GMAIL_APP_PASSWORD`

> **Note:** If you don't see App Passwords, 2FA may need to be enabled first, or your Google Workspace admin may need to permit App Passwords for the account.

### 2. Verify the IMAP connection (optional but recommended)

After uploading the code and creating your `.env` file, you can test connectivity:

```bash
cd ~/lead_app
source venv/bin/activate
python test_imap_connection.py
```

This will confirm your App Password works and list all available Gmail labels.

---

## PythonAnywhere Deployment

### Step 1 — Create PythonAnywhere account

Sign up for a **Hacker plan** (or above) at [pythonanywhere.com](https://www.pythonanywhere.com). The Hacker plan provides:
- Always-On Tasks (required for the 60-second Gmail poller)
- PostgreSQL database support
- Custom domain support (optional)

### Step 2 — Upload the code

In a PythonAnywhere Bash console:

```bash
# Option A: clone from git (recommended)
git clone https://github.com/your-org/lead-app.git ~/lead_app

# Option B: upload the zip and extract
cd ~
unzip lead_app.zip
```

### Step 3 — Create a virtual environment

```bash
cd ~/lead_app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4 — Create PostgreSQL database

In the PythonAnywhere **Databases** tab:
1. Create a new PostgreSQL database (e.g. `yourusername$lead_management`)
2. Note the hostname, username, and password shown

### Step 5 — Configure environment variables

Create a `.env` file in `~/lead_app/`:

```bash
cp .env.example .env
nano .env
```

Fill in all values:

```
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
BASE_URL=https://yourusername.pythonanywhere.com
DATABASE_URL=postgresql://yourusername:password@yourusername-db.pythonanywhere.com/yourusername$lead_management
GMAIL_CLIENT_ID=<from Step 1>
GMAIL_CLIENT_SECRET=<from Step 1>
GMAIL_REFRESH_TOKEN=<from Step 1>
GMAIL_TARGET_EMAIL=data@thrivemediagroup.co.uk
MAIL_USERNAME=data@thrivemediagroup.co.uk
MAIL_APP_PASSWORD=<from Step 2 — 16-char App Password>
```

### Step 6 — Run database migrations and seed

```bash
cd ~/lead_app
source venv/bin/activate

# Initialise migrations (first time only)
flask db init
flask db migrate -m "Initial schema"
flask db upgrade

# Seed initial data (admin user, test agent, outcome options)
python seed.py
```

> After seeding, log in as `admin` / `ChangeMe123!` and **immediately change the password**.

### Step 7 — Configure the Web App

In the PythonAnywhere **Web** tab:
1. Add a new web app → Manual configuration → Python 3.10
2. Set **Source code** to `/home/yourusername/lead_app`
3. Set **Working directory** to `/home/yourusername/lead_app`
4. Set **Virtualenv** to `/home/yourusername/lead_app/venv`
5. Edit the **WSGI configuration file** — replace its contents with:

```python
import sys, os
sys.path.insert(0, '/home/yourusername/lead_app')
os.environ.setdefault('FLASK_ENV', 'production')
from app import create_app
application = create_app('production')
```

6. Click **Reload**

### Step 8 — Configure the Always-On Task (Gmail poller + truncation)

In the PythonAnywhere **Tasks** tab:
1. Add an **Always-On Task**
2. Command:
   ```
   /home/yourusername/lead_app/venv/bin/python /home/yourusername/lead_app/scheduler.py
   ```
3. Click **Create**

The scheduler will:
- Poll Gmail every 60 seconds
- Check at 01:00 UTC on the 1st of each month whether to run monthly truncation

---

## First Login & Setup

1. Navigate to `https://yourusername.pythonanywhere.com/login`
2. Log in as `admin` / `ChangeMe123!`
3. **Change the admin password immediately** (Admin → Users → Edit → Reset Password)
4. Go to **Settings → Gmail Labels** → Add your monitored labels
5. Go to **Settings → Agents** → Create your real agents
6. Go to **Settings → Routing Matrix** → Configure which agents receive leads from which providers
7. Watch **Alerts** for any Gmail connectivity issues

---

## Gmail Label IDs

When adding a monitored label, you need the Gmail internal label ID (e.g. `Label_1234567890`).

The easiest way:
1. Go to **Settings → Gmail Labels → Add Label**
2. Click **"Load Available Gmail Labels"** — the app fetches all labels from Gmail API
3. Click any label to auto-fill the ID and path fields

---

## Monthly Truncation

The truncation job runs automatically at **01:00 UTC on the 1st of each calendar month**. It:
- Removes all active leads from agent dashboards
- Keeps all records permanently in the Vault
- Flags leads with no outcome as incomplete
- Creates a truncation batch record (e.g. `2026-05 Monthly Truncation`)

No manual intervention is required.

---

## Updating the Application

```bash
cd ~/lead_app
source venv/bin/activate

# Pull latest code
git pull

# Apply any new database migrations
flask db upgrade

# Reload the web app (in PythonAnywhere Web tab, click Reload)
# Restart the Always-On Task (in Tasks tab, toggle it off/on)
```

---

## Troubleshooting

| Symptom | Check |
|---|---|
| No leads appearing | Run `python test_imap_connection.py` and check Alerts tab |
| Leads showing as UNASSIGNED | Settings → Routing Matrix — verify agent eligibility |
| Password reset emails not sending | `.env` GMAIL_APP_PASSWORD — must be a Gmail App Password, not your account password |
| Scheduler not running | PythonAnywhere Tasks tab — check Always-On Task is active and logs |
| Database connection errors | DATABASE_URL in `.env` — verify hostname matches PythonAnywhere Databases tab |
| 500 errors on web app | PythonAnywhere Web tab → Error log |

---

## Security Notes

- All passwords are hashed with Werkzeug's PBKDF2-SHA256
- Sessions are HTTP-only and SameSite=Lax
- All forms have CSRF protection
- The vault is restricted to Admin role only
- Gmail App Password is stored only as an environment variable — never in code or the database
- Password reset tokens expire after 1 hour

---

## User Roles Summary

| Capability | Agent | Manager | Admin |
|---|---|---|---|
| View own leads | ✓ | ✓ | ✓ |
| View all agents' leads | ✓ | ✓ | ✓ |
| Update own lead outcome/notes | ✓ | ✓ | ✓ |
| Update any lead | — | ✓ | ✓ |
| Manage agents & settings | — | ✓ | ✓ |
| Access Vault | — | — | ✓ |
| Export CSV | — | — | ✓ |
| Manage users & roles | — | — | ✓ |
| View system alerts | — | ✓ | ✓ |
