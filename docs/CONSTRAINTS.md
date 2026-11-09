# CONSTRAINTS.md — Boundaries & Invariants

> **Habit 07 of AI Collaboration Field Guide**: A short, explicit list of what the system must never do, inviolable rules, and boundary guardrails.

---

## 1. AI Assistant Boundaries (Strict Invariants)
1. **Never Mutate Data via AI**: The Natural Language AI assistant is strictly a **read-only** query engine. It must NEVER execute `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, or any schema/data mutation.
2. **Never Hide Filters or Row Counts**: When executing queries, the AI assistant must always display the filters extracted, the SQL `SELECT` representation, and the row count matched so office staff can verify correctness.
3. **Never Punish via AI**: The At-Risk Student engine must ONLY spawn `MentorTask` objects for faculty counseling. It must NEVER automatically deduct marks, lower grades, or change attendance records.
4. **Attendance & Marks Rules are Fixed**: The 75.0% attendance shortage threshold and 16.0/40 passing mark are fixed institution-level settings, NOT machine learning parameters.

---

## 2. Examination & Moderation Lock Invariants
1. **Moderation Lock Immunity**: Once internal marks are transitioned to `Moderated_Locked`, no faculty or user can update scores without an explicit unlock action authorized and logged with an audit reason.
2. **Tamper-Evident Audit Trail**: Every score change, whether in draft or revision, must write an immutable row to `ExamAuditLog` capturing old score, new score, actor username, actor role, timestamp, and justification reason.
3. **Component Ceilings**:
   - Mid-term Exam: $\le 20.0$ marks.
   - Continuous Assessment / Quiz: $\le 10.0$ marks.
   - Practical / Assignment: $\le 10.0$ marks.
   - Total Internal Marks: Exactly $\le 40.0$ marks.

---

## 3. Data Protection & Regulatory Invariants
1. **DPDP Act 2023 Compliance**: Students who are minors ($<18$ years of age) require recorded parental consent. Access to minor student records must be audit-logged.
2. **Zero Secrets in Repository**: Secrets, production credentials, and real personal data must never be committed to source control.
3. **Campus & Department Scoping**: Users must only access academic records within their authorized campus and department scope.
