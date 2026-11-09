# Deployment and Reviewer Guide

## Project links

- **GitHub repository:** https://github.com/govind-geethub/college-erp-project
- **Live application:** Not deployed publicly. Run it locally using the steps below; a localhost address is not accessible to reviewers remotely.

## Prerequisites

- Python 3.10 or newer
- Git
- A modern web browser

## Run locally (Windows PowerShell)

1. Clone the public repository and enter its folder:

   ```powershell
   git clone https://github.com/govind-geethub/college-erp-project.git
   Set-Location college-erp-project
   ```

2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install project dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Configure local demo access if desired. Copy `.env.example` to `.env` and set private values for `JWT_SECRET` and the demo password variables. Do not commit `.env` or share its secret values. Demo no-token access is only enabled when configured for a non-production environment.

   ```powershell
   Copy-Item .env.example .env
   ```

5. Start the server:

   ```powershell
   python run.py
   ```

6. Open `http://127.0.0.1:8000/`. On first startup, the application creates the schema and seeds synthetic demonstration data.

7. Run tests in a separate terminal from the repository folder:

   ```powershell
   python -m pytest -v
   ```

To stop the local server, press **Ctrl+C** in the terminal running it.

## Deployment status and production considerations

This submission provides a local application and does not include a public hosting environment, deployment pipeline, production database, or live external integrations. For a real deployment, configure a production ASGI server and managed database, use TLS and a stable private signing secret, disable demo authentication, and define server-side role permissions and operational backup/monitoring procedures. These production steps have not been provisioned or verified as part of this submission.

## Environment variable names

The application reads configuration from its environment and, when present, `.env`. Variable names below are listed without secret values:

- `ENVIRONMENT`
- `DEBUG`
- `DATABASE_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `DEMO_AUTH_ENABLED`
- `DEMO_ADMIN_PASSWORD`
- `DEMO_FACULTY_PASSWORD`
- `DEMO_MODERATOR_PASSWORD`
- `DEFAULT_CAMPUS_CODE`
- `DEFAULT_CAMPUS_NAME`
- `DEFAULT_TRUST_NAME`
- `MINIMUM_ATTENDANCE_PERCENTAGE`
- `INTERNAL_MARKS_MAX`
- `INTERNAL_PASS_THRESHOLD`
- `DPDP_MINOR_AGE_THRESHOLD`
- `DPDP_AUDIT_LOGGING_ENABLED`
- `ENABLE_ODIA_NOTIFICATIONS`
- `HOST`
- `PORT`

Use private values for secrets and passwords. Do not add them to this document, the ZIP, or the public repository. Demo access is disabled in production even if `DEMO_AUTH_ENABLED` is set.

## Reviewer demo accounts

The seed data creates these account usernames:

| Username | Seeded role | Intended review areas |
|---|---|---|
| `admin` | Office administrator | Dashboard, AI query, fees, reports, and student records |
| `faculty` | Faculty | Attendance and marks entry |
| `moderator` | Exam moderator | Marks moderation, audit history, and university CSV export |

Passwords are not embedded in the repository or submission. Set private values through `DEMO_ADMIN_PASSWORD`, `DEMO_FACULTY_PASSWORD`, and `DEMO_MODERATOR_PASSWORD` in a local ignored `.env` file. The browser role selector is a demonstration UI control, not a server-side authentication or authorization mechanism. For a deployment with demo access disabled, obtain an API token using `/api/auth/login` with a configured seeded account.

## Prototype limitations

- Mock payment requests update the local demonstration ledger; they do not process money.
- Parent notification records are mock dispatches; no SMS or WhatsApp message is sent.
- Tally exports are generated files; there is no live Tally connection.
- Query interpretation and risk scoring use application rules; no generative AI service is called.
- Seed records are synthetic demonstration data, not verified real people or production records.
