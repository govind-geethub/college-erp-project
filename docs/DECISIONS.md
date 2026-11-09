# DECISIONS.md — Architecture & Design Rationale

> **Habit 02 of AI Collaboration Field Guide**: Log every meaningful decision made during development, the alternatives considered, and why specific tradeoffs were accepted.

---

## Decision Log

### ADR-001: Technology Stack Selection (FastAPI + SQLite WAL + Pure Vanilla ES6 PWA)
- **Context**: The client runs 3 colleges in Odisha with 7,800 students. Classrooms have weak Wi-Fi, and evaluators/reviewers need to run the application immediately with zero build step failures.
- **Decision**: Used Python FastAPI backend with SQLAlchemy 2.0 and SQLite in WAL (Write-Ahead Logging) mode, paired with a vanilla modern JavaScript/CSS PWA frontend served directly by FastAPI.
- **Alternatives Considered**:
  - *Next.js + Node + PostgreSQL*: Requires Node.js runtime, heavy `npm install`, node_modules overhead, external database server, and complex build steps prone to environment discrepancies.
  - *Django*: Slightly heavier boilerplate, slower startup for local reviewers.
- **Rationale**: FastAPI provides instant startup (<1 second), auto-generated interactive OpenAPI docs (`/docs`), async performance, and zero client build steps. SQLite WAL handles concurrent reads/writes with zero setup.

---

### ADR-002: Offline Attendance Architecture & Idempotent Sync Tokens
- **Context**: Classrooms in Bhubaneswar have weak or intermittent Wi-Fi. Teachers must mark attendance in under 30 seconds without spinning wheels or data loss.
- **Decision**: 
  1. Defaulted UI to "Mark All Present" with single-tap toggle overrides for Absent / Late.
  2. Implemented client-side queue in Web Storage / IndexedDB that intercepts submissions when offline or during connectivity drops.
  3. Assigned unique `client_batch_id` tokens (UUID + Timestamp) to each submission.
  4. Backend verifies `client_batch_id` idempotency: retries on flaky Wi-Fi update the existing session rather than duplicating counts.
- **Rationale**: Meets the client's <30 seconds requirement and guarantees 100% data integrity even during total network blackouts.

---

### ADR-003: Fixed Rule Integrity vs. AI Boundaries
- **Context**: Brief states: *"AI flags students at risk from attendance and marks trends, and lets office staff ask questions in plain English... Attendance and marks rules are fixed settings, not AI. At-risk flags only create a mentor task."*
- **Decision**: Enforced hard separation:
  - Attendance threshold (75.0%) and Marks passing criteria (16.0/40) are strictly hardcoded in `config.py` and service rules.
  - AI operates exclusively as a **read-only insight engine**: parses natural language queries, verifies absence of mutation verbs (`DELETE`, `UPDATE`, `DROP`), generates transparent SQL representations, and displays applied filters.
  - At-risk flags automatically generate actionable `MentorTask` objects assigned to faculty mentors without modifying any academic record.
- **Rationale**: Prevents hallucination-induced grade modifications, complies with accreditation audit standards, and respects regulatory limits.

---

### ADR-004: Tamper-Evident Exam Audit Trail & Moderation Lock Workflow
- **Context**: Results day brings 7,800 students. University exam regulations and NAAC Criterion 2.5 mandate complete auditability of every mark alteration.
- **Decision**:
  - Implemented 3-stage state machine: `Draft` &rarr; `Submitted` &rarr; `Moderated_Locked`.
  - Once marked `Moderated_Locked`, service blocks any PUT/POST modifications with `403 Forbidden`.
  - Every mark update inserts an immutable row into `ExamAuditLog` capturing old component scores, new component scores, actor username, actor role, and change reason.
- **Rationale**: Guarantees zero re-typing for university mark uploads, satisfies NAAC 2.5 transparency requirements, and eliminates unauthorized score tampering.

---

### ADR-005: Bilingual English & Odia Notification Templates
- **Context**: Company A Educational Trust is situated in Bhubaneswar, Odisha. Many rural and regional parents prefer communications in Odia.
- **Decision**: Created bilingual SMS/WhatsApp dispatch structures with Odia Unicode script and English fallback templates for both attendance shortages and fee reminders.
- **Rationale**: Respects local context, boosts parent engagement, and fulfills specific brief constraints.
