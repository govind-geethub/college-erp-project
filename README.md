# Prerana College ERP — Multi-Campus Higher Education Management System

[![Build & Test Status](https://img.shields.io/badge/tests-23%20passed-success)](tests/)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.138-teal)](https://fastapi.tiangolo.com/)
[![License: Proprietary](https://img.shields.io/badge/license-Educational%20Trust-orange)]()

> Designed and built for **Company A Educational Trust, Bhubaneswar (Odisha)**  
> 7,800 Students &bull; 520 Teaching Staff &bull; 340 Non-Teaching Staff &bull; ₹95–110 Crore Fee Revenue  
> Phase 1 Core Build: Single Campus Slice (Bhubaneswar Engineering College)

---

## 🏛️ Executive Overview

Company A Educational Trust runs three campuses in Bhubaneswar on legacy paper logs, disjointed spreadsheets, and a 12-year-old desktop program. 

This repository delivers the **Phase 1 Core Build**, shipping end-to-end functionality across 8 polished, purposeful screens:
1. **Academic Masters for One Programme Slice**: Bhubaneswar Engineering College (`BBSR-ENG`), B.Tech CSE, Batches, Subjects with 40-mark component schema, and Faculty assignments.
2. **Mobile Attendance with Offline Sync (<30s Speed)**: In-class PWA attendance capture designed for weak classroom Wi-Fi with client-side queuing, idempotent `client_batch_id` synchronization, and automated shortage alerts (<75%).
3. **Internal Marks & Moderation Lock**: 40-mark component breakdown (Midterm 20, Quiz 10, Assignment 10), state machine moderation lock (`Draft` &rarr; `Submitted` &rarr; `Moderated_Locked`), tamper-evident exam audit trail (`ExamAuditLog`), and 1-click BPUT / autonomous university CSV upload format.
4. **Fee Dues & Tally Accounting**: Fee structures by programme and scholarship category (TFW / General), test-mode simulated payment links with instant receipt issuance, and automated Tally ERP 9 / TallyPrime XML export (reducing monthly reconciliation from 10 days to 1 day).
5. **Office Staff AI Query Assistant**: Plain-English natural language query generator with AST mutation guardrails, filter trace explainability, and transparent read-only SQL badge.
6. **Multi-Factor At-Risk Engine**: Automated identification of students with attendance drops and failing marks, spawning actionable `MentorTask` counseling tickets without direct punitive grade modification.
7. **Accreditation & Regulatory Reporting**: AICTE Mandatory Public Disclosure and NAAC Criterion 2.5 Continuous Internal Evaluation transparency reports.
8. **Bilingual Parent Notifications**: Dual-script automated attendance shortage and fee reminder notices in **English** and **Odia script (ଓଡ଼ିଆ)**.
9. **DPDP Act 2023 Compliance**: Verifiable minor consent tracking and access audit logging.

---

## 🚀 Quick Start (Under 1 Minute)

### 1. Run the ERP
```bash
# Clone the repository
git clone https://github.com/govind-geethub/college-erp-project.git
cd college-erp-project

```

Install the project's runtime and test dependencies:
```bash
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` (`Copy-Item .env.example .env` in PowerShell),
replace the placeholder JWT secret and demo
passwords with private values, and keep `.env` uncommitted (it is ignored by Git).
The local review UI enables demo authentication only when `ENVIRONMENT` is
development and `DEMO_AUTH_ENABLED=true`.

```bash
python run.py
```

The database schema and benchmark records are seeded automatically. Open
**`http://localhost:8000`** in a browser. To run without demo authentication,
leave `DEMO_AUTH_ENABLED` unset and use `/api/auth/login` to obtain a bearer token.

### 2. Run the Automated Test Suite
```bash
python -m pytest -v
```
The hermetic unit and integration tests execute in a few seconds.

---

## 👤 Demo Login Users for Reviewer

Demo account passwords are configured locally using `DEMO_ADMIN_PASSWORD`,
`DEMO_FACULTY_PASSWORD`, and `DEMO_MODERATOR_PASSWORD` in `.env`. Never put
password values in source code or commit them.

| Role | Username | Access & Responsibilities |
|---|---|---|
| **Office Admin** | `admin` | Campus overview, AI NL query engine, fee reconciliation, Tally XML export, DPDP consent records. |
| **Faculty (Teacher)** | `faculty` | Dr. Ramesh Chandra Patra (CSE): Mobile attendance, offline queue sync, draft internal marks. |
| **Exam Moderator** | `moderator` | Prof. Minati Mishra: Moderation lock verification, tamper-evident exam audit trail, university BPUT CSV export. |

---

## 📊 Benchmark Student Records (from Problem Statement)

| Roll No | Name | Programme | Year | Attendance % | Internal Marks (40) | Fee Due (₹) | System Status |
|---|---|---|---|---|---|---|---|
| `ENG-24-CSE-0412` | Subhashree Mohanty | B.Tech CSE | 2 | 81.5% | 33 | ₹0 | Normal / Compliant |
| `ENG-24-ME-0177` | Ankit Panda | B.Tech Mechanical | 2 | 68.2% | 21 | ₹45,000 | **HIGH RISK &bull; Shortage Notice &bull; Mentor Task Assigned** |
| `MBA-25-0093` | Farheen Ali | MBA | 1 | 92.0% | 36 | ₹0 | Normal / Top Performer |

---

## 📚 AI Collaboration Field Guide Documentation

In strict adherence to the **AI Collaboration Field Guide** (15 documentation habits, 5 core files):

- [docs/TDD.md](docs/TDD.md): Full Technical Design Document with explicitly labeled assumptions.
- [deployment.md](deployment.md): Deployment and reviewer guide.
- [docs/HANDOVER.md](docs/HANDOVER.md): Project state and continuity.
- [docs/DECISIONS.md](docs/DECISIONS.md): Architectural Decision Records and tradeoffs.
- [docs/FLOW.md](docs/FLOW.md): Step-by-step execution paths and call sequences.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): System context, layered modules, and data flow.
- [docs/CONSTRAINTS.md](docs/CONSTRAINTS.md): Boundaries and safety invariants.
- [docs/TEST_CHECKLIST.md](docs/TEST_CHECKLIST.md): Verification commands and UI walkthrough checklist.
- [docs/ROLLBACK.md](docs/ROLLBACK.md): Recovery procedures and git checkpoints.
- [docs/FEATURE_LOG.md](docs/FEATURE_LOG.md): Feature and bug trace log.

---

## 📦 Submission Deliverables

As specified in the evaluation brief:
- **`submission.zip`** (&le;25 MB) containing:
  1. `Technical_Design_Document.docx` (Complete Word TDD document)
  2. `deployment.md` (Step-by-step reviewer and environment guide)
