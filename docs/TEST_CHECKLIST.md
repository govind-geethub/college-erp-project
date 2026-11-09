# TEST_CHECKLIST.md — Verification & Proof

> **Habit 08 of AI Collaboration Field Guide**: A concrete list of what to run and check before any change counts as "done". Not a vibe check — actual commands, actual expected outputs.

---

## Automated Test Verification

Run the entire automated test suite:
```bash
python -m pytest -v
```

### Expected Output
```
collected 21 items

tests/test_ai_assistant_safety.py::test_plain_english_query_attendance_shortage PASSED
tests/test_ai_assistant_safety.py::test_plain_english_query_fee_dues PASSED
tests/test_ai_assistant_safety.py::test_safety_guardrail_blocks_mutation PASSED
tests/test_at_risk_engine.py::test_ankit_panda_flagged_high_risk PASSED
tests/test_at_risk_engine.py::test_at_risk_only_creates_mentor_task PASSED
tests/test_attendance_offline_sync.py::test_attendance_marking_and_stats PASSED
tests/test_attendance_offline_sync.py::test_offline_sync_idempotency PASSED
tests/test_attendance_offline_sync.py::test_attendance_shortage_alert_trigger PASSED
tests/test_auth.py::test_password_hashing PASSED
tests/test_auth.py::test_legacy_password_hashes_remain_verifiable PASSED
tests/test_auth.py::test_jwt_token_generation_and_verification PASSED
tests/test_auth.py::test_missing_credentials_are_rejected_by_default PASSED
tests/test_auth.py::test_demo_auth_is_only_available_outside_production PASSED
tests/test_auth.py::test_explicit_local_demo_auth_resolves_demo_admin PASSED
tests/test_fees_and_tally.py::test_ankit_panda_fee_due_matches_brief PASSED
tests/test_fees_and_tally.py::test_mock_payment_and_receipt PASSED
tests/test_fees_and_tally.py::test_tally_xml_export_structure PASSED
tests/test_marks_moderation_audit.py::test_internal_marks_bounds_and_calculation PASSED
tests/test_marks_moderation_audit.py::test_internal_marks_bounds_exceeded_fails PASSED
tests/test_marks_moderation_audit.py::test_locked_marks_cannot_be_modified PASSED
tests/test_marks_moderation_audit.py::test_university_csv_export_format PASSED

============================= 21 passed ==============================
```

---

## Manual End-to-End Walkthrough Checklist

| Step | Action | Expected Output | Status |
|---|---|---|---|
| 1 | Run `python run.py` and open `http://localhost:8000` | Clean, calm dashboard loads with 96.4% same-day attendance KPI | Verified |
| 2 | Click "Take Attendance (<30s)" in sidebar | Roster loads; 1-tap "Mark All Present" sets everyone to Present | Verified |
| 3 | Click "Sim Offline", mark attendance, click "Save" | Saved to offline queue; status pill turns red: "Offline (1 Queued)" | Verified |
| 4 | Click "Reconnect" or "Sync Offline Queue" | Batch is synced via `client_batch_id`; success toast displayed | Verified |
| 5 | Navigate to "Internal Marks" | CS301 marks load; status is "Moderated & Locked"; inputs disabled | Verified |
| 6 | Click "Export University Upload CSV" | Downloads BPUT formatted CSV with zero re-typing | Verified |
| 7 | Switch role to "Office Admin", go to "AI Query & Risk" | Type "how many second-year students are below 75% this month?" | Verified |
| 8 | Run AI Query | Filter trace displayed, read-only SQL SELECT generated, Ankit Panda matched | Verified |
| 9 | Try unsafe query: "DELETE FROM students" | Guardrail blocks with "BLOCKED (Write/DDL mutation forbidden)", 0 rows modified | Verified |
| 10 | Navigate to "Fee Dues & Tally" | Click "Pay Fee" for Ankit Panda; settle ₹15,000; instant receipt issued | Verified |
| 11 | Click "Export Tally XML" | Downloads standard Tally ERP 9 / TallyPrime XML import payload | Verified |
| 12 | Navigate to "Compliance & Odia" | View NAAC Criterion 2.5 metrics and Odia Unicode shortage notices | Verified |
