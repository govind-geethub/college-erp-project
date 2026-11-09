# ARCHITECTURE.md — High-Level System Architecture

> **Habit 06 of AI Collaboration Field Guide**: High-level map of the system: modules, services, how data moves between them.

---

## 1. System Context & Overview

```
                                  ┌────────────────────────────────────────────────────────┐
                                  │      Company A Educational Trust (Bhubaneswar)         │
                                  │           7,800 Students &bull; 3 Campuses             │
                                  └────────────────────────────────────────────────────────┘
                                                              │
                                ┌─────────────────────────────┴────────────────────────────┐
                                ▼                                                          ▼
                  [Faculty Mobile in Classroom]                             [Office Admin & Exam Cell]
                 - Weak Wi-Fi PWA / Offline Sync                            - Plain English AI Assistant
                 - Roll call marked in <30s                                 - Tally XML Reconciliation
                 - 1-Tap "Mark All Present"                                 - NAAC & AICTE Compliance
                                │                                                          │
                                └─────────────────────────────┬────────────────────────────┘
                                                              ▼
                                            ┌───────────────────────────────────┐
                                            │      FastAPI Gateway (Port 8000)   │
                                            │      - Static SPA + REST API      │
                                            │      - JWT / RBAC Authorization   │
                                            └───────────────────────────────────┘
                                                              │
                ┌─────────────────────────┬───────────────────┴───────────────────┬─────────────────────────┐
                ▼                         ▼                                       ▼                         ▼
      [Attendance Service]       [Internal Marks Service]                 [Fee Ledger Service]      [AI & Risk Engine]
      - Idempotent Sync          - 40 Marks Component Bounds              - Dues Tracking           - Read-Only NL Parser
      - Shortage Alerts (<75%)   - Moderation Lock Workflow               - Mock Payment Gateway    - Filter Trace & SQL AST
      - Odia/English Notices     - Tamper-Evident Audit Trail             - Tally XML Export        - Mentor Task Generator
                │                         │                                       │                         │
                └─────────────────────────┴───────────────────┬───────────────────┴─────────────────────────┘
                                                              ▼
                                            ┌───────────────────────────────────┐
                                            │       SQLAlchemy 2.0 ORM Engine   │
                                            │       SQLite (WAL Mode Enabled)   │
                                            │       Foreign Keys Enforced       │
                                            └───────────────────────────────────┘
```

---

## 2. Layered Module Structure

1. **Presentation Layer (`app/static/`)**:
   - `index.html`: Responsive Single-Page Application (SPA) covering all 8 screens.
   - `css/style.css`: Bespoke design system adhering strictly to client aesthetics (calm, restrained palette, ample whitespace, clear typography, nothing lacks purpose).
   - `js/app.js`: Client controller, state manager, role adapter.
   - `js/offline_sync.js`: Offline storage queue, network change listener, background synchronizer.
   - `sw.js`: Service Worker providing PWA offline asset caching.

2. **API & Routing Layer (`app/main.py`)**:
   - 35 verified REST endpoints organized across Masters, Attendance, Marks, Fees, AI, Reports, and Notifications.
   - CORS middleware enabled.

3. **Domain & Business Logic Layer (`app/services/`)**:
   - `attendance_service.py`: Enforces roll call speeds (<30s), handles offline idempotency, triggers automatic shortage notices.
   - `marks_service.py`: Enforces component score limits, moderation lock status transitions, and writes immutable audit logs.
   - `fees_service.py`: Fee calculations, test-mode mock payment gateway, receipt generation, and Tally XML format generation.
   - `ai_assistant.py`: Natural language processing with strict AST and keyword safety checks preventing data modification.
   - `at_risk_engine.py`: Multi-factor risk scoring engine; strictly spawns mentor counseling tasks without altering grades.
   - `report_service.py`: Compiles AICTE Mandatory Disclosure and NAAC Criterion 2.5 reports.
   - `notification_service.py`: Generates bilingual English and Odia parent SMS notifications.

4. **Persistence & Data Layer (`app/models.py`, `app/database.py`)**:
   - 14 SQLAlchemy ORM entities with explicit foreign key relationships and index optimizations.
   - SQLite Write-Ahead Logging (WAL) enabled for high-concurrency read/write operations on results days.
