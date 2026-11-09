# ROLLBACK.md — Recovery & Rollback Procedures

> **Habit 09 of AI Collaboration Field Guide**: A short plan for undoing changes if something breaks, which commits to revert to, which files to restore, and what to re-check after.

---

## 1. Database State Recovery
- **Reset to Clean Seeded State**:
  If the local SQLite database becomes inconsistent during manual testing:
  ```bash
  # Delete database file and run seed
  rm college_erp.db college_erp.db-wal college_erp.db-shm
  python -m app.seed_data
  ```
  *Windows PowerShell*:
  ```powershell
  Remove-Item college_erp.db*, -ErrorAction SilentlyContinue
  python -m app.seed_data
  ```

---

## 2. Git Checkpoint History
- `HEAD`: Documentation, Field Guide compliance, TDD & submission packaging.
- `757d859`: Frontend implementation, service worker, and 17 hermetic unit/integration tests.
- `f6b56e4`: FastAPI REST endpoints and routing.
- `3a17810`: Core business services (attendance sync, marks moderation, fees, AI, bilingual notifications).
- `b9eb1d8`: Initial models, schemas, and benchmark seed data.

---

## 3. Verification Post-Rollback
After any rollback, run:
```bash
python -m pytest -v
```
All 17 tests must pass before declaring the rollback verified.
