# FLOW.md — Execution Paths & Traceability

> **Habit 04 of AI Collaboration Field Guide**: Document how execution travels between files, functions, and modules. What calls what, in what order, and where critical logic resides.

---

## 1. Mobile Attendance Submission & Offline Sync Flow

```
[Faculty Mobile Device]
       │
       ▼ (1-Tap Mark / Toggle)
[app/static/js/app.js: submitAttendanceSession()]
       │
       ├─ Check Network Status: OfflineSync.isOnline()
       │      │
       │      ├─ [OFFLINE / WEAK WI-FI] ──────────────────────────┐
       │      │                                                   ▼
       │      │                                  [app/static/js/offline_sync.js]
       │      │                                  - Generate client_batch_id
       │      │                                  - Enqueue in localStorage
       │      │                                  - Update UI pill: "Offline (1 Queued)"
       │      │                                                   │
       │      │                                  [On Reconnect / Sync Click]
       │      │                                                   ▼
       │      └─ [ONLINE] ───────────────────────► POST /api/attendance/submit
                                                                  │
                                                                  ▼
                                                 [app/main.py: submit_attendance()]
                                                                  │
                                                                  ▼
                                      [app/services/attendance_service.py: submit_attendance_session()]
                                                                  │
                                            ┌─────────────────────┴─────────────────────┐
                                            ▼                                           ▼
                                 [Check Idempotency Token]                  [Write AttendanceRecord Rows]
                                 - If client_batch_id exists:              - Calculate totals
                                   return cached session                   - Check <75% shortage
                                                                                        │
                                                                                        ▼
                                                                           [Notification Trigger]
                                                                           - NotificationLog (English + Odia)
```

---

## 2. Internal Marks Moderation & Audit Trail Flow

```
[Faculty / Moderator UI]
       │
       ▼
[app/static/js/app.js: saveMarksSheet()]
       │
       ▼ POST /api/marks/save
[app/main.py: save_marks()]
       │
       ▼
[app/services/marks_service.py: update_marks()]
       │
       ├─ Step 1: Validate component bounds (Midterm <= 20, Quiz <= 10, Assign <= 10)
       │          └─ Fail: Pydantic / HTTPException 400
       │
       ├─ Step 2: Check Moderation Lock: `if mark.is_locked`
       │          └─ Fail: HTTPException 403 Forbidden ("Moderated and locked for exam audits")
       │
       ├─ Step 3: Compute total = midterm + quiz + assignment (Max 40)
       │
       ├─ Step 4: Write immutable entry to `ExamAuditLog`
       │          (actor_username, actor_role, old_total, new_total, reason, timestamp)
       │
       └─ Step 5: Save InternalMark record
```

---

## 3. Plain-English AI Query & Safety Guardrail Flow

```
[Office Admin Query: "how many second-year students are below 75% this month?"]
       │
       ▼
[app/static/js/app.js: executeAIQuery()]
       │
       ▼ POST /api/ai/query
[app/main.py: run_natural_language_query()]
       │
       ▼
[app/services/ai_assistant.py: process_natural_language_query()]
       │
       ├─ Safety Guardrail: Scan for mutation keywords
       │  (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE)
       │  └─ If found: Return BLOCKED, zero records, safety audit failure
       │
       ├─ Entity & Intent Extraction:
       │  - Year: "second-year" ──► `students.current_year = 2`
       │  - Threshold: "below 75%" ──► `attendance_pct < 75.0`
       │
       ├─ Read-Only Query Execution (Scoped to Campus & Department permissions)
       │
       ├─ Filter Trace Generation:
       │  - Field, Operator, Target Value, Human Rationale
       │
       └─ Return Response:
          - Generated SQL SELECT representation
          - Row Count & Execution Latency (ms)
          - Results list & Safety Proof Badge
```

---

## 4. Multi-Factor At-Risk Engine & Mentor Task Flow

```
[Scheduled Trigger / User Scan]
       │
       ▼
[app/services/at_risk_engine.py: run_campus_risk_assessment()]
       │
       ├─ Loop over all Active Students:
       │  ├─ Attendance Weight (50%): Shortage below 75% -> +40/50 points
       │  ├─ Marks Weight (35%): Internal marks < 16 fail -> +35 points
       │  └─ Fee Weight (15%): Fee arrears > ₹25,000 -> +15 points
       │
       ├─ Calculate Combined Risk Score (0 - 100)
       │  - Score >= 60: HIGH RISK (e.g. Ankit Panda, Score 82.5)
       │  - Score >= 35: MEDIUM RISK
       │
       └─ If At-Risk:
          ├─ Update `AtRiskFlag` (Status: "TASK_CREATED")
          └─ Spawn `MentorTask` assigned to Faculty
             * NO DIRECT GRADE OR ATTENDANCE MODIFICATION PERMITTED *
```
