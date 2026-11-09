# HANDOVER.md — Project Continuity & State

> **Habit 01 & 13 of AI Collaboration Field Guide**: A living record of where things stand, what is completed, what is in progress, what to avoid, and five-line session handoff summaries.

---

## 1. Executive Status
- **Current State**: Phase 1 Core Build is 100% complete and fully verified.
- **Test Suite**: 21 / 21 automated tests passing (`pytest -v`).
- **Target Audience**: Company A Educational Trust (Bhubaneswar, Odisha) & Evaluation Reviewers.
- **Key Modules Shipped**:
  1. Masters for 1 Campus slice (Bhubaneswar Engineering College, 3 Programmes, Batches, Subjects).
  2. Mobile Attendance with Offline IndexedDB/localStorage Queue & Idempotent Sync (<30 seconds per class).
  3. Internal Marks with 40-max component breakdown, Moderation Lock, Tamper-Evident Exam Audit Trail, and BPUT CSV export.
  4. Fee Dues Tracking, Test-Mode Mock Payments, Instant Receipt Generation, and Automated Tally ERP 9 / TallyPrime XML Export (1-day reconciliation).
  5. Plain-English AI Query Assistant with AST/keyword safety guardrails, Filter Inspector, Row Count, and Read-Only SQL transparency.
  6. Multi-Factor At-Risk Engine spawning automated Mentor Counseling Tasks (strictly without direct grade modification).
  7. Bilingual Parent SMS/WhatsApp Center (English + Odia script).
  8. DPDP Act 2023 minor consent auditing.

---

## 2. What Is Done
- [x] Database Schema & Engine (`app/models.py`, `app/database.py` with SQLite WAL mode and FK enforcement).
- [x] Benchmark Seed Data (`app/seed_data.py`) with all 3 specified students (`ENG-24-CSE-0412`, `ENG-24-ME-0177`, `MBA-25-0093`) and realistic cohorts.
- [x] Mobile Attendance Service (`app/services/attendance_service.py`) with automatic shortage trigger (<75%).
- [x] Internal Marks Moderation Service (`app/services/marks_service.py`) enforcing 40-mark ceilings, locking states, and audit trails.
- [x] Fee Accounting & Tally Integration (`app/services/fees_service.py`).
- [x] Read-Only NL AI Query Assistant (`app/services/ai_assistant.py`) with filter trace.
- [x] At-Risk Early Warning Engine (`app/services/at_risk_engine.py`).
- [x] Service Worker PWA Caching (`app/static/sw.js`).
- [x] Responsive, calm UI frontend (`app/static/index.html`, `app/static/css/style.css`, `app/static/js/app.js`, `app/static/js/offline_sync.js`).
- [x] 21 hermetic unit and integration tests (`tests/`).

---

## 3. What to Watch Out For / Pitfalls Avoided
- **Never Fake the AI**: The AI assistant actually parses queries, extracts semantic tokens, verifies safety via whitelist/blacklist AST check, runs read-only queries, and displays filters and row count.
- **Never Modify Records via AI**: AI flags strictly spawn `MentorTask` objects; academic rules are fixed settings.
- **Offline Sync Idempotency**: Classroom weak Wi-Fi often leads to duplicate HTTP requests. The system uses unique `client_batch_id` tokens to ensure identical batches are merged safely without duplicate session counts.
- **DPDP Act 2023**: Minor students (<18) have parental consent status flags and every view is logged in `dpdp_audit_logs`.

---

## 4. Five-Line Session Handoff Summary
1. **Accomplished**: Built full multi-campus slice ERP end-to-end with 8 polished screens, offline PWA attendance, marks moderation audit, Tally XML export, and plain-English AI assistant.
2. **Current Status**: All 21 automated tests passing; database seeded with exact benchmark student records.
3. **Verified Logic**: Offline sync idempotency, moderation locking preventing mark tampering, and safety guardrails blocking SQL mutation.
4. **Immediate Next Step**: Maintain the repository and rerun tests before changes are published.
5. **Watch Out**: Keep `college_erp.db` out of git; rely on automated on-boot seeding.
