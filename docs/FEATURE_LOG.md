# FEATURE_LOG.md — Feature & Bug Traceability

> **Habit 05 of AI Collaboration Field Guide**: Keep one living log tracing features and fixes from discovery to verification.

---

## Shipped Features Log

### FEAT-01: Offline Attendance with Idempotent Sync
- **Origin**: Brief Hard Part: *"offline attendance in class with sync... attendance marked in under 30 seconds per class."*
- **Implementation**:
  - PWA Service Worker (`app/static/sw.js`) caches app shell.
  - Client queue (`app/static/js/offline_sync.js`) stores batches in `localStorage` when offline.
  - Idempotent `client_batch_id` prevents duplicate sessions on retry.
  - UI offers 1-tap "Mark All Present" and quick toggle overrides.
- **Verification**: `tests/test_attendance_offline_sync.py::test_offline_sync_idempotency` PASSED.

---

### FEAT-02: 40-Mark Internal Moderation & Exam Audit Trail
- **Origin**: Brief: *"internal marks with moderation lock... marks lock after moderation and every change is logged for exam audits."*
- **Implementation**:
  - Components: Midterm ($\le 20$), Quiz ($\le 10$), Assignment ($\le 10$) = Total $\le 40$.
  - State machine: `Draft` &rarr; `Submitted` &rarr; `Moderated_Locked`.
  - Service blocks edits to locked records with `HTTP 403`.
  - Immutable audit trail in `ExamAuditLog`.
  - BPUT university format export.
- **Verification**: `tests/test_marks_moderation_audit.py` (4 tests) PASSED.

---

### FEAT-03: Fee Dues, Reconciliation & Tally XML Export
- **Origin**: Brief: *"fee dues... monthly fee reconciliation from 10 days to 1."*
- **Implementation**:
  - Tracks student fee ledgers by programme/category (e.g. Ankit Panda ₹45,000 due).
  - Test-mode mock payment generator with instant receipt issuance.
  - Tally ERP 9 / TallyPrime XML import payload export.
- **Verification**: `tests/test_fees_and_tally.py` (3 tests) PASSED.

---

### FEAT-04: Plain-English AI Query Assistant & Safety Guardrail
- **Origin**: Brief: *"lets office staff ask questions in plain English, such as how many second-year students are below 75% this month, by generating a read-only query. When it is wrong: the assistant shows the filters it used and the row count..."*
- **Implementation**:
  - Natural language entity parser extracts Year, Percentage, Programme, and Fee criteria.
  - AST / regex guardrail blocks mutation commands (`INSERT`, `UPDATE`, `DELETE`, `DROP`).
  - Transparent SQL representation, filter trace, execution latency, and row count displayed.
- **Verification**: `tests/test_ai_assistant_safety.py` (3 tests) PASSED.

---

### FEAT-05: Multi-Factor At-Risk Engine & Mentor Counseling Tasks
- **Origin**: Brief: *"AI flags students at risk from attendance and marks trends... At-risk flags only create a mentor task. Attendance and marks rules are fixed settings, not AI."*
- **Implementation**:
  - Combines Attendance (<75%), Internal Marks (<16 fail, <24 avg), and Fee Arrears.
  - Generates `AtRiskFlag` (HIGH / MEDIUM) and assigns `MentorTask` to faculty mentor.
  - Strictly guarantees zero automated changes to grades or attendance.
- **Verification**: `tests/test_at_risk_engine.py` (2 tests) PASSED.

---

### FEAT-06: Bilingual Parent Notifications (English & Odia)
- **Origin**: Brief: *"English, with Odia for parent messages."*
- **Implementation**:
  - Shortage alerts and fee reminders dispatched with dual-script templates (English + Odia Unicode).
  - Complete notification audit log.
- **Verification**: Verified in `app/services/notification_service.py` and UI live table.
