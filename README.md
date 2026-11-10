# CyberSight ASM - Authentication & Authorization Module

Module 1 of the CyberSight Attack Surface Management Platform. Implements a complete authentication system with RBAC.

## Tech Stack

**Backend:** Python FastAPI, MongoDB (Motor), JWT, Passlib (bcrypt)  
**Frontend:** React + Vite, Tailwind CSS, React Router, Axios

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB running locally or a connection string
- Gmail account with App Password (for email verification)

## Setup

### 1. Clone & Navigate

```bash
cd Threatfusion
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

Edit `.env` with your MongoDB URI, JWT secret, and Gmail SMTP credentials.

Run the backend:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/api/docs

### 3. Frontend

```bash
cd frontend
npm install
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

Run the frontend:

```bash
npm run dev
```

App available at: http://localhost:5173

## Features

### Authentication
- User registration with email verification
- Secure login with JWT tokens
- Forgot password with email reset link
- Password change for authenticated users

### RBAC Roles
| Role | Permissions |
|------|------------|
| Admin | Full access, user management |
| Threat Analyst | Full IOC management |
| SOC Analyst | View and search data |
| Viewer | Read-only access |

### Admin Dashboard
- List all users with search
- Change user roles
- Activate/Deactivate users
- Delete users

## Intelligence Enhancements (v1.1)

All features below are **additive** — the base scan workflow, data model and API responses
are unchanged, and every integration is optional/disabled until configured.

| Feature | What it does | Activation |
|---------|--------------|------------|
| **EPSS enrichment** | Every CVE gets its FIRST EPSS exploit-probability score (`epss`, `epss_percentile`) — feeds risk scoring and patch priorities | On by default (`EPSS_ENABLED=false` to disable) |
| **Risk scoring v2** | Threat-intelligence component now weighs EPSS (≥70% = +2, ≥25% = +1 per CVE); new `business_criticality` breakdown component | Automatic |
| **Business context tagging** | Tag assets (`PATCH /api/assets/{id}/context`): production/staging/dev/third-party/cloud_junk, criticality 1-5, tags | API (UI editable on Assets page) |
| **Patch priority queue** | `GET /api/risk-assessment/priorities` — findings ranked by CVSS + EPSS + CISA KEV + exposure + asset criticality, P1-P4 labels, "patch these first" list | Always available |
| **Dangling DNS / subdomain takeover detection** | CNAME chains into cloud fingerprints (S3, GitHub Pages, Heroku, Azure, …) are probed read-only; findings saved as vulnerabilities + tagged on DNS records | Automatic (DNS stage) |
| **Custom Nuclei templates** | `backend/nuclei-templates/cybersight/` — exposed .git, exposed .env, OpenAPI docs, Spring actuators; auto-appended to scans | Automatic |
| **Continuous monitoring scheduler** | The existing Settings → Scheduler toggle now works: enqueues a full scan per project hourly/daily/weekly | Settings UI → Scheduler → enabled |
| **Webhook / Slack alerting** | Digest of new Critical/High notifications posted to an outgoing webhook after each scan | `ALERT_WEBHOOK_URL` (min severity `ALERT_MIN_SEVERITY`) |
| **Jira / TheHive ticketing** | Auto-creates a ticket per critical/high finding on scan completion; de-duplicated per scan | `JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY` or `THEHIVE_URL, THEHIVE_API_KEY` |
| **AI report analysis** | Reports gain an `ai_summary` + "AI Analysis" PDF section. With no LLM key a deterministic local writer is used — reports never fail | `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` |
| **Report copilot** | `POST /api/reports/{id}/ask` — grounded Q&A over the scan data; answers only reference collected evidence | Same as above |
| **Asset screenshots** | httpx captures screenshots during live verification; served via `GET /api/assets/{id}/screenshot` | `SCREENSHOTS_ENABLED=true` |
| **Settings-UI API keys now active** | Keys stored in Admin → Settings (Shodan/VT/NVD) are used by scan stages, with `.env` values as fallback | Nothing to do |

### Privacy note (LLM)
Hostnames/URLs are redacted to `ASSET-n` placeholders before any content is sent to an
LLM endpoint, and restored server-side in the response. Set `LLM_SEND_HOSTNAMES=true`
only if you want real hostnames in the prompt for richer analysis.

### New environment variables
See `backend/.env.example` for the full list (`LLM_*`, `JIRA_*`, `THEHIVE_*`,
`ALERT_*`, `SCREENSHOTS_ENABLED`, `EPSS_ENABLED`).

## Module Verification & Fixes (v1.1.1)
Systematic verification pass over all modules, then targeted fixes:

- **Vulnerability Assessment (critical fix)** — findings upserts had `first_seen`/`created_at`
  in *both* `$setOnInsert` and `$set`; MongoDB rejects overlapping operators, so any scan that
  actually produced findings crashed with `BulkWriteError`. Fixed to the standard first_seen
  pattern. Also: the executor now runs **one batched Nuclei process per template family**
  (list-file input) instead of one process per target — a 70-target stage went from
  70 sequential Nuclei startups to 2 passes — and both the **full default template library**
  and the CyberSight custom templates are scanned (passing `-t` had been silently replacing
  defaults with just the 4 custom templates).
- **SSL Analysis** — replaced `ssl.match_hostname` (removed in Python 3.12+) with a local
  wildcard-aware matcher; certificate grades are accurate again on Python 3.13.
- **Asset Discovery** — OWASP Amass wired in as a passive second source, merged with
  Subfinder results (graceful skip when the binary is absent).
- **Scheduler** — misleading log condition cleaned up.
- **Stage Manager** — `logger` was used in the scan-completion hook without ever being
  defined (latent `NameError` in the ticketing path); sweep of every backend module
  confirms no other file logs through an undefined logger.
- **Verification tooling** — `backend/verify_modules.py` (47-assertion logic battery),
  `backend/verify_stack.py` (Atlas connectivity/collections), `backend/verify_vulns.py`
  (scan-log diagnostics), `backend/verify_nuclei_smoke.py` (real end-to-end Nuclei run
  against a local throwaway server; no third-party targets).

## Folder Structure

```
Threatfusion/
├── backend/
│   ├── app/
│   │   ├── config.py          # Environment settings
│   │   ├── database.py        # MongoDB connection
│   │   ├── main.py            # FastAPI app entry
│   │   ├── models/user.py     # User model & roles
│   │   ├── schemas/user.py    # Pydantic schemas
│   │   ├── routes/            # API routes
│   │   ├── services/          # Business logic
│   │   ├── dependencies/      # Auth dependencies
│   │   └── utils/             # Security & token utils
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── contexts/          # Auth context
│   │   ├── pages/             # Page components
│   │   ├── services/          # API service (axios)
│   │   └── App.jsx            # Router setup
│   ├── package.json
│   └── .env.example
└── README.md
```

## API Endpoints

### Auth (`/api/auth`)
- `POST /register` - Register new user
- `POST /verify-email` - Verify email with token
- `POST /login` - Login
- `POST /forgot-password` - Request password reset
- `POST /reset-password` - Reset password with token

### Users (`/api/users`)
- `GET /me` - Get current user profile
- `PUT /me` - Update profile
- `POST /change-password` - Change password

### Admin (`/api/admin`)
- `GET /users` - List users (Admin only)
- `PUT /users/{id}/role` - Change role (Admin only)
- `PUT /users/{id}/active` - Toggle active (Admin only)
- `DELETE /users/{id}` - Delete user (Admin only)

## First Admin User

Register a user, then manually update their role in MongoDB:

```javascript
db.users.updateOne(
  { email: "your@email.com" },
  { $set: { role: "admin", email_verified: true } }
)
```
