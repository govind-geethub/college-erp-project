**Project repository:** https://github.com/govind-geethub/college-erp-project
**Public application URL:** Not deployed. The application is available only when run locally.

# Technical Design Document

**Project:** College ERP, Phase 1 single-campus slice

## 1. Purpose and scope

This document describes the current implementation of the College ERP project: a browser-based application for academic masters, attendance, internal marks, fee ledgers, student records, risk review, notifications, and regulatory reports. The project includes a seeded demonstration dataset and a local test suite.

The implementation is a prototype, not a production deployment. Payment processing, SMS delivery, and Tally export are simulated or generated as files; they do not connect to external providers.

## 2. Assumptions

The following are design assumptions where implementation details were not specified in the problem statement:

1. **[ASSUMPTION] Single-campus first release:** One campus is used as the operational slice; the schema retains campus and programme relationships for extension.
2. **[ASSUMPTION] Internal assessment format:** Internal marks are represented as midterm (20), quiz (10), and assignment (10), totaling 40.
3. **[ASSUMPTION] Attendance threshold:** A cumulative attendance percentage below 75% is treated as an alert condition.
4. **[ASSUMPTION] Minor-consent indicator:** The dataset contains a minor flag and consent status as demonstrative compliance fields. This is not a legal compliance determination.
5. **[ASSUMPTION] Local persistence:** SQLite is sufficient for local evaluation and development; a production deployment would need an operational database and migration/backup plan.
6. **[ASSUMPTION] External integrations:** No payment gateway, messaging provider, or Tally service credentials were provided, so integrations are represented with mock payment and notification behavior and downloadable exports.
7. **[ASSUMPTION] AI behavior:** No hosted AI model or model credentials were provided. Query interpretation and risk scoring therefore use deterministic application rules rather than a generative model.
8. **[ASSUMPTION] Demo access:** Local reviewer/demo access is acceptable only in non-production mode and is explicitly enabled through configuration. Production use requires a separate identity and authorization design.
9. **[ASSUMPTION] User interface:** A responsive, minimal browser UI is appropriate for the staff workflows described; the current UI is a single-page application without a client framework.
10. **[ASSUMPTION] Synthetic seed data:** Seed records are demonstration data and must not be interpreted as verified real student or staff records.

## 3. Architecture and rationale

The application uses a small layered architecture:

```text
Browser: HTML + CSS + JavaScript
  - Single-page navigation and forms
  - Service worker for static assets
  - Local attendance queue for offline capture and later sync
              | HTTP / JSON
FastAPI application
  - REST endpoints and Pydantic request validation
  - Authentication helpers and endpoint dependencies
  - Static page and asset hosting
              |
SQLAlchemy services and models
  - Attendance, marks, fees, notifications, risk, reporting
              |
SQLite database (WAL enabled by the database setup)
```

**Why this approach:** FastAPI provides a compact Python API and validation layer; SQLAlchemy keeps persistence and business logic separated from routes; SQLite makes local setup simple; and plain HTML/CSS/JavaScript avoids a separate frontend build step. The service worker and local queue support the attendance workflow when connectivity is interrupted.

The current app is started with `python run.py`. No hosted production infrastructure or publicly reachable live app is included in this repository.

## 4. Data model

The relational model groups related records as follows:

- **Organization and identity:** `Campus`, `Programme`, `Batch`, `Subject`, `Faculty`, `FacultySubjectMapping`, and `User`.
- **Student records:** `Student`, including academic identifiers, batch, contact fields, and consent-status fields.
- **Attendance:** `AttendanceSession` stores a class/date/period and client sync identifier; `AttendanceRecord` stores each student's status for that session.
- **Marks:** `InternalMark` stores assessment components and moderation state; `ExamAuditLog` records changes and moderation actions.
- **Fees:** `FeeStructure`, `StudentFeeLedger`, and `FeePayment` store charges, balances, and simulated payment receipts.
- **Intervention and communication:** `AtRiskFlag`, `MentorTask`, and `NotificationLog`.
- **Access auditing:** `DPDPAuditLog` records student-profile access when audit logging is enabled.

Foreign keys connect students to batches/programmes and link their attendance, marks, ledger, risk flags, and tasks. A student/subject uniqueness constraint prevents duplicate internal-mark rows for the same pair.

## 5. Main application flows

### Attendance and offline synchronization

1. The browser requests the active students for a batch.
2. Staff mark each student present, absent, or late and submit the session.
3. When offline mode is active, the browser queues the payload in local storage and updates its connection/queue indicator.
4. When connectivity returns, queued payloads are posted to the attendance API.
5. The server uses the client batch identifier to avoid creating a duplicate session on retry, stores records, and evaluates shortage alerts.

### Marks and moderation

1. The browser loads a subject/batch marks sheet.
2. Editable rows can be saved; locked rows are disabled and excluded from bulk updates.
3. The service enforces per-component limits and prevents edits to locked records.
4. Mark edits and moderation changes are recorded in the exam audit log.
5. The marks sheet can be exported as a university-format CSV.

### Fees and receipt

1. The fee screen requests student ledgers and displays balances.
2. A mock payment request reduces the balance and creates a receipt record.
3. The receipt URL returned by the payment request resolves to that payment's details.
4. Fee reconciliation data can be downloaded as CSV or Tally-compatible XML. No external payment or accounting system is called.

### Student profile and reports

The directory loads student summaries. Opening a profile requests one student's details and can add a profile-access audit record. Separate report endpoints provide KPI, NAAC-style, and AICTE-style data based on the stored records.

## 6. AI and risk behavior

The application does not call a generative AI model. The query assistant uses deterministic text matching to identify supported filters such as year, programme, attendance, fee due, and marks. It then applies those filters through application/database queries and returns a filter summary, generated read-only SQL description, results, and safety status. A basic forbidden-keyword guard rejects mutation-oriented prompts; this should not be treated as a general-purpose SQL security boundary.

The risk engine calculates a deterministic score from attendance, marks, and fee balance rules. It returns risk levels and trigger explanations, and creates or updates intervention flags and mentor tasks. It does not update a student's attendance or marks.

Parent notifications have mock status and are stored in the notification log. No SMS or WhatsApp is sent.

## 7. UI and design decisions

The UI is a single-page interface with eight operational screens:

1. **Dashboard:** summarizes attendance KPI and students needing follow-up.
2. **Academic Masters:** shows campus programmes, batches, and subjects.
3. **Mobile Attendance:** prioritizes quick roster actions and offline queue visibility.
4. **Internal Marks:** provides a tabular component editor, moderation controls, audit view, and CSV export.
5. **Fees:** presents ledger balances, simulated payment, receipt details, and exports.
6. **AI Query and Risk:** combines supported plain-language filters with risk and mentor-task views.
7. **Reports and Notifications:** presents report data and mock bilingual notification history.
8. **Student Directory:** summarizes student details and supports profile inspection.

The interface uses a restrained palette, compact tables, status badges, and task-specific actions to keep common staff workflows visible. The frontend role selector is a demonstration control; it is not a substitute for server-enforced role authorization.

## 8. Scope limits and next steps

**Not implemented:** public hosting, real payment processing, live SMS/WhatsApp delivery, live Tally connectivity, production-grade identity/role management, and generative-AI inference.

**Recommended next work:** define production roles and permissions on every protected endpoint; add database migrations and deployment/backup procedures; integrate external services only with approved credentials and audit controls; add automated browser tests; and perform privacy, security, and load reviews against confirmed requirements.

## 9. Verification

At the time this submission was prepared, the automated suite completed with 29 passing tests. The API and browser workflows were also exercised locally on a separate seeded database. These checks do not constitute a production readiness or compliance certification.
