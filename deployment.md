# Deployment & Reviewer Evaluation Guide
## Multi-Campus College ERP (Company A Educational Trust, Bhubaneswar)

---

## 1. Quick Start / How to Run Locally, Step by Step

### Prerequisites
- Python 3.10+ (Developed and verified on Python 3.13)
- Modern web browser (Chrome, Edge, Firefox, or Safari)
- Git

### Step-by-Step Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/govind-geethub/college-erp-project.git
   cd college-erp-project
   ```

2. **Install dependencies and run the application**:
   ```bash
   python -m pip install -r requirements.txt
   ```

   Copy `.env.example` to `.env`, then replace the placeholder JWT secret and demo passwords with private values. The `.env` file is ignored by Git and must not be committed.
   ```powershell
   Copy-Item .env.example .env
   # Edit .env, then:
   python run.py
   ```

   Database schema and benchmark seed data are created automatically on startup.
   For a non-demo run, leave `DEMO_AUTH_ENABLED` unset and authenticate through `/api/auth/login`.
   ```bash
   # Optional alternative:
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

3. **Open the Application**:
   Navigate to your browser:
   ```
   http://127.0.0.1:8000
   ```

4. **Run the Automated Test Suite**:
   To run the automated unit and integration tests:
   ```bash
   python -m pytest -v
   ```

---

## 2. Demo Login Details for Reviewer

The system seeds three demo roles. Set private passwords with `DEMO_ADMIN_PASSWORD`, `DEMO_FACULTY_PASSWORD`, and `DEMO_MODERATOR_PASSWORD` in `.env`; do not commit those values.

| Role | Username | Purpose & Scope |
|---|---|---|---|
| **Office Admin** | `admin` | Full campus administration: AI plain-English query assistant, fee collection, Tally XML export, DPDP Act 2023 consent inspections, NAAC & AICTE reports. |
| **Faculty (Teacher)** | `faculty` | Dr. Ramesh Chandra Patra (CSE): In-class mobile attendance, offline sync queue, draft internal marks entry. |
| **Exam Moderator** | `moderator` | Prof. Minati Mishra (Exam Cell): Moderation lock/unlock verification, tamper-evident audit logs, university BPUT CSV export. |

> **Tip for Reviewers**: You can switch roles instantly in real time using the **"Role:"** dropdown in the top navigation bar without re-logging in.

---

## 3. Deployment Guide & Environment Variables

### Production Deployment (e.g. AWS EC2 / DigitalOcean / Docker / Render)

To run the application in a production environment:

1. **Production Process Manager**:
   Run with Gunicorn using Uvicorn worker threads:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
   ```

2. **Environment Variables**:
   In strict accordance with security guidelines, here are the environment variable **names only** (never commit secret values to source control):

   - `ENVIRONMENT`: Set to `production` or `development`.
   - `DEBUG`: Boolean flag (`true` / `false`).
   - `PORT`: Network port for the server (defaults to `8000`).
   - `HOST`: Host IP binding (defaults to `0.0.0.0` in production).
   - `DATABASE_URL`: Connection string for production database (e.g., PostgreSQL / RDS).
   - `JWT_SECRET`: Secret cryptographic key for signing user session tokens.
   - `JWT_ALGORITHM`: Cryptographic signing algorithm (defaults to `HS256`).
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiry duration for authentication tokens.
   - `DEMO_AUTH_ENABLED`: Local review-only no-token demo access. Keep unset or `false` in production; demo access is disabled when `ENVIRONMENT=production`.
   - `DEMO_ADMIN_PASSWORD`, `DEMO_FACULTY_PASSWORD`, `DEMO_MODERATOR_PASSWORD`: Private demo-user passwords. Set them in an ignored `.env` file and never commit the file.
   - `MINIMUM_ATTENDANCE_PERCENTAGE`: Fixed institutional attendance threshold (75.0%).
   - `INTERNAL_MARKS_MAX`: Maximum ceiling for internal marks (40.0).
   - `DPDP_MINOR_AGE_THRESHOLD`: Age of majority threshold under DPDP Act 2023 (18).
   - `DPDP_AUDIT_LOGGING_ENABLED`: Flag enabling audit logging for student records (`true`).
   - `ENABLE_ODIA_NOTIFICATIONS`: Flag enabling dual-script Odia script SMS notifications (`true`).

---

## 4. Benchmark Student Records to Inspect

The reviewer can immediately inspect the three required benchmark records from the brief:

1. **Subhashree Mohanty** (`ENG-24-CSE-0412`): B.Tech CSE, Year 2 &bull; Attendance: 81.5% &bull; Internal Marks: 33/40 &bull; Fee Due: ₹0.
2. **Ankit Panda** (`ENG-24-ME-0177`): B.Tech Mechanical, Year 2 &bull; Attendance: 68.2% &bull; Internal Marks: 21/40 &bull; Fee Due: ₹45,000 &bull; **Flagged HIGH RISK** &bull; Automated Mentor Task assigned.
3. **Farheen Ali** (`MBA-25-0093`): MBA, Year 1 &bull; Attendance: 92.0% &bull; Internal Marks: 36/40 &bull; Fee Due: ₹0.
