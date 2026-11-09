"""
FastAPI application router and entrypoint for College ERP.
Exposes REST endpoints for Masters, Mobile Attendance with Offline Sync,
Marks Moderation, Fee Accounting, AI Query Assistant, and Accreditation Reports.
"""

from datetime import date
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session
import os

from app.config import settings
from app.database import get_db, engine, Base
from app.models import (
    User, Campus, Programme, Batch, Subject, Faculty, Student,
    AttendanceSession, InternalMark, ExamAuditLog, StudentFeeLedger,
    AtRiskFlag, MentorTask, DPDPAuditLog
)
from app.schemas import (
    LoginRequest, TokenResponse, UserOut, CampusOut, ProgrammeOut, BatchOut,
    SubjectOut, StudentOut, StudentDetailOut, AttendanceBatchSubmit,
    AttendanceSessionOut, BatchMarksUpdate, ModerationLockRequest,
    MockPaymentRequest, AIQueryRequest, AIQueryResponse, MentorTaskOut
)
from app.auth import (
    verify_password, hash_password, create_access_token, get_current_user, require_role
)
from app.seed_data import seed_database
from app.services import (
    attendance_service, marks_service, fees_service,
    ai_assistant, at_risk_engine, report_service, notification_service
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-campus college ERP system for Company A Educational Trust, Bhubaneswar."
)

# Enable CORS for local testing and cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Ensure database schema is created and seeded with benchmark records on boot."""
    Base.metadata.create_all(bind=engine)
    with next(get_db()) as db:
        seed_database(db)


# ============================================================================
# 1. AUTHENTICATION & SESSION ENDPOINTS
# ============================================================================
@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with username and password, return signed JWT."""
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not user.password_hash.startswith("pbkdf2_sha256$"):
        user.password_hash = hash_password(payload.password)
        db.commit()

    token = create_access_token({"sub": user.username, "role": user.role, "campus": user.campus_code})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "campus_code": user.campus_code,
        "department": user.department
    }


@app.get("/api/auth/me", response_model=UserOut)
def get_current_user_profile(user: User = Depends(get_current_user)):
    """Return currently active user profile and permissions."""
    return user


# ============================================================================
# 2. ACADEMIC MASTERS
# ============================================================================
@app.get("/api/masters/campuses", response_model=List[CampusOut])
def list_campuses(db: Session = Depends(get_db)):
    return db.query(Campus).all()


@app.get("/api/masters/programmes", response_model=List[ProgrammeOut])
def list_programmes(db: Session = Depends(get_db)):
    return db.query(Programme).all()


@app.get("/api/masters/batches", response_model=List[BatchOut])
def list_batches(programme_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Batch)
    if programme_id:
        query = query.filter(Batch.programme_id == programme_id)
    return query.all()


@app.get("/api/masters/subjects", response_model=List[SubjectOut])
def list_subjects(programme_id: Optional[int] = None, semester: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Subject)
    if programme_id:
        query = query.filter(Subject.programme_id == programme_id)
    if semester:
        query = query.filter(Subject.semester == semester)
    return query.all()


# ============================================================================
# 3. STUDENT DIRECTORY & DPDP ACT 2023 COMPLIANCE
# ============================================================================
@app.get("/api/students")
def list_students(
    batch_id: Optional[int] = None,
    year: Optional[int] = None,
    programme_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve list of students with real-time attendance, marks, and fee balances."""
    query = db.query(Student).join(Batch).join(Programme)
    if batch_id:
        query = query.filter(Student.batch_id == batch_id)
    if year:
        query = query.filter(Student.current_year == year)
    if programme_code:
        query = query.filter(Programme.code == programme_code)

    students = query.all()
    results = []

    for s in students:
        att = attendance_service.calculate_student_attendance(db, s.id)
        mark = db.query(InternalMark).filter(InternalMark.student_id == s.id).first()
        ledger = s.fee_ledger

        risk_flag = db.query(AtRiskFlag).filter(AtRiskFlag.student_id == s.id).first()

        results.append({
            "id": s.id,
            "roll_no": s.roll_no,
            "name": s.name,
            "email": s.email,
            "phone": s.phone,
            "parent_name": s.parent_name,
            "parent_phone": s.parent_phone,
            "programme_name": s.batch.programme.name if s.batch else "B.Tech",
            "programme_code": s.batch.programme.code if s.batch else "BTECH-CSE",
            "batch_name": s.batch.name if s.batch else "2024-2028",
            "current_year": s.current_year,
            "current_semester": s.current_semester,
            "category": s.category,
            "is_minor": s.is_minor,
            "dpdp_consent_status": s.dpdp_consent_status,
            "attendance_pct": att["percentage"],
            "total_classes": att["total"],
            "attended_classes": att["attended"],
            "internal_marks_total": mark.total_score if mark else 0.0,
            "internal_marks_max": 40.0,
            "fee_due": ledger.due_amount if ledger else 0.0,
            "fee_status": ledger.status if ledger else "Due",
            "is_at_risk": risk_flag is not None and risk_flag.risk_level in ("HIGH", "MEDIUM"),
            "risk_level": risk_flag.risk_level if risk_flag else "LOW"
        })

    return results


@app.get("/api/students/{student_id}")
def get_student_detail(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve individual student profile with DPDP audit access log."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # DPDP Act 2023 Audit Logging
    if settings.DPDP_AUDIT_LOGGING_ENABLED:
        dpdp_entry = DPDPAuditLog(
            actor_username=current_user.username,
            student_id=student.id,
            action="VIEW_PROFILE",
            is_minor=student.is_minor,
            access_purpose=f"Academic inspection by {current_user.role}"
        )
        db.add(dpdp_entry)
        db.commit()

    att = attendance_service.calculate_student_attendance(db, student.id)
    marks = db.query(InternalMark).filter(InternalMark.student_id == student.id).all()
    ledger = student.fee_ledger

    return {
        "id": student.id,
        "roll_no": student.roll_no,
        "name": student.name,
        "email": student.email,
        "phone": student.phone,
        "parent_name": student.parent_name,
        "parent_phone": student.parent_phone,
        "parent_email": student.parent_email,
        "programme": student.batch.programme.name if student.batch else "",
        "current_year": student.current_year,
        "current_semester": student.current_semester,
        "category": student.category,
        "is_minor": student.is_minor,
        "dpdp_consent_status": student.dpdp_consent_status,
        "attendance": att,
        "marks": [
            {
                "subject_code": m.subject.code,
                "subject_name": m.subject.name,
                "midterm_20": m.midterm_score,
                "quiz_10": m.quiz_score,
                "assignment_10": m.assignment_score,
                "total_40": m.total_score,
                "is_locked": m.is_locked,
                "moderation_status": m.moderation_status
            }
            for m in marks
        ],
        "fee_ledger": {
            "total_fee": ledger.total_fee if ledger else 0.0,
            "scholarship": ledger.scholarship_discount if ledger else 0.0,
            "net_payable": ledger.net_payable if ledger else 0.0,
            "paid_amount": ledger.paid_amount if ledger else 0.0,
            "due_amount": ledger.due_amount if ledger else 0.0,
            "status": ledger.status if ledger else "Due"
        }
    }


# ============================================================================
# 4. MOBILE ATTENDANCE WITH OFFLINE SYNC (<30 SECONDS)
# ============================================================================
@app.get("/api/attendance/batch-roster")
def get_batch_roster(batch_id: int, db: Session = Depends(get_db)):
    """Return roster for fast mobile attendance roll-call."""
    return attendance_service.get_students_for_batch(db, batch_id)


@app.post("/api/attendance/submit")
def submit_attendance(
    payload: AttendanceBatchSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record in-class attendance session.
    Supports offline queued submissions with idempotent client_batch_id.
    Triggers automatic shortage alerts (<75%) and Odia notifications.
    """
    session, alerts = attendance_service.submit_attendance_session(
        db=db,
        payload=payload,
        faculty_user_id=current_user.id
    )

    return {
        "status": "Success",
        "sync_status": "Synced",
        "session_id": session.id,
        "client_batch_id": payload.client_batch_id,
        "total_marked": session.total_students,
        "present_count": session.present_count,
        "absent_count": session.absent_count,
        "shortage_alerts_triggered": alerts
    }


@app.get("/api/attendance/sessions")
def get_attendance_history(
    batch_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Retrieve historical attendance sessions."""
    query = db.query(AttendanceSession)
    if batch_id:
        query = query.filter(AttendanceSession.batch_id == batch_id)
    if subject_id:
        query = query.filter(AttendanceSession.subject_id == subject_id)

    sessions = query.order_by(AttendanceSession.session_date.desc()).all()
    return [
        {
            "id": s.id,
            "date": s.session_date.strftime("%Y-%m-%d"),
            "period": s.period,
            "subject_code": s.subject.code if s.subject else "",
            "subject_name": s.subject.name if s.subject else "",
            "batch_name": s.batch.name if s.batch else "",
            "total": s.total_students,
            "present": s.present_count,
            "absent": s.absent_count,
            "sync_status": s.sync_status
        }
        for s in sessions
    ]


# ============================================================================
# 5. INTERNAL MARKS & MODERATION LOCK (OUT OF 40)
# ============================================================================
@app.get("/api/marks/sheet")
def get_marks_sheet(subject_id: int, batch_id: int, db: Session = Depends(get_db)):
    """Retrieve marks sheet with component breakdown out of 40."""
    return marks_service.get_subject_marks_sheet(db, subject_id, batch_id)


@app.post("/api/marks/save")
def save_marks(
    payload: BatchMarksUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save component marks. Enforces moderation lock and writes exam audit log."""
    return marks_service.update_marks(db, payload, current_user)


@app.post("/api/marks/moderation")
def set_moderation(
    payload: ModerationLockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lock or submit internal marks for examination committee verification."""
    return marks_service.set_moderation_lock(
        db=db,
        subject_id=payload.subject_id,
        batch_id=payload.batch_id,
        action=payload.action,
        actor_user=current_user,
        reason=payload.reason
    )


@app.get("/api/marks/audit-logs")
def get_exam_audit_logs(subject_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Retrieve tamper-evident exam audit trail."""
    query = db.query(ExamAuditLog)
    if subject_id:
        query = query.filter(ExamAuditLog.subject_id == subject_id)
    
    logs = query.order_by(ExamAuditLog.timestamp.desc()).limit(50).all()
    return [
        {
            "id": l.id,
            "student_id": l.student_id,
            "subject_id": l.subject_id,
            "actor_username": l.actor_username,
            "actor_role": l.actor_role,
            "old_total": l.old_total,
            "new_total": l.new_total,
            "action_type": l.action_type,
            "reason": l.reason,
            "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for l in logs
    ]


@app.get("/api/marks/export-university-csv")
def export_university_csv(subject_id: int, batch_id: int, db: Session = Depends(get_db)):
    """Generate university upload CSV formatted for BPUT / Autonomous university exam upload."""
    csv_content = marks_service.export_university_marks_csv(db, subject_id, batch_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=university_marks_subj_{subject_id}.csv"}
    )


# ============================================================================
# 6. FEE DUES, RECONCILIATION & TALLY EXPORT
# ============================================================================
@app.get("/api/fees/ledgers")
def list_fee_ledgers(programme_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Retrieve all student fee accounts."""
    return fees_service.get_all_fee_ledgers(db, programme_id)


@app.post("/api/fees/mock-payment")
def make_mock_payment(payload: MockPaymentRequest, db: Session = Depends(get_db)):
    """Simulate fee settlement (UPI/NetBanking/Bank counter) in test mode."""
    return fees_service.process_mock_payment(db, payload)


@app.get("/api/fees/export-tally-xml")
def export_tally_xml(db: Session = Depends(get_db)):
    """Download Tally XML voucher import file."""
    xml_data = fees_service.generate_tally_xml_export(db)
    return Response(
        content=xml_data,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=tally_fee_reconciliation.xml"}
    )


@app.get("/api/fees/export-csv")
def export_fees_csv(db: Session = Depends(get_db)):
    """Download fees collection report in CSV format."""
    csv_data = fees_service.generate_fee_ledger_csv(db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fee_reconciliation_report.csv"}
    )


# ============================================================================
# 7. AI QUERY ASSISTANT & AT-RISK ENGINE
# ============================================================================
@app.post("/api/ai/query", response_model=AIQueryResponse)
def run_natural_language_query(
    payload: AIQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Office Admin AI Assistant:
    Accepts plain English queries, extracts filters, runs strictly read-only scoped queries,
    and returns results with filter trace, row count, execution time, and safety proof.
    """
    return ai_assistant.process_natural_language_query(
        db=db,
        query_text=payload.prompt,
        current_user=current_user
    )


@app.get("/api/ai/at-risk-students")
def get_at_risk_list(db: Session = Depends(get_db)):
    """Retrieve all students currently flagged at risk with multi-factor triggers."""
    return at_risk_engine.run_campus_risk_assessment(db)


@app.get("/api/ai/mentor-tasks")
def list_mentor_tasks(db: Session = Depends(get_db)):
    """List actionable early-intervention mentor tasks created from at-risk flags."""
    tasks = db.query(MentorTask).all()
    results = []
    for t in tasks:
        results.append({
            "id": t.id,
            "student_id": t.student.id,
            "student_name": t.student.name,
            "student_roll_no": t.student.roll_no,
            "faculty_name": t.faculty.name if t.faculty else "Faculty Mentor",
            "title": t.title,
            "description": t.description,
            "recommended_action": t.recommended_action,
            "status": t.status,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return results


@app.post("/api/ai/mentor-tasks/{task_id}/resolve")
def resolve_mentor_task(task_id: int, notes: Optional[str] = "Counseling conducted", db: Session = Depends(get_db)):
    """Update mentor task status to Completed with resolution notes."""
    task = db.query(MentorTask).filter(MentorTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = "Completed"
    task.notes = notes
    db.commit()
    return {"status": "Success", "task_id": task.id, "state": "Completed"}


# ============================================================================
# 8. REGULATORY & ACCREDITATION REPORTS
# ============================================================================
@app.get("/api/reports/kpi-dashboard")
def get_kpi_dashboard(db: Session = Depends(get_db)):
    return report_service.get_kpi_dashboard_metrics(db)


@app.get("/api/reports/naac-criterion-2")
def get_naac_report(db: Session = Depends(get_db)):
    return report_service.get_naac_criterion_2_report(db)


@app.get("/api/reports/aicte-disclosure")
def get_aicte_report(db: Session = Depends(get_db)):
    return report_service.get_aicte_disclosure_report(db)


@app.get("/api/notifications/logs")
def get_notifications(db: Session = Depends(get_db)):
    return notification_service.get_notification_logs(db)


@app.post("/api/notifications/send")
def trigger_notification(
    student_id: int,
    trigger_type: str = "ATTENDANCE_SHORTAGE",
    db: Session = Depends(get_db)
):
    return notification_service.send_manual_parent_alert(db, student_id, trigger_type)


# ============================================================================
# 9. FRONTEND STATIC FILE HOSTING & SPA
# ============================================================================
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return PlainTextResponse("Prerana College ERP API is running. Static frontend initializing...")


@app.get("/sw.js")
def serve_service_worker():
    sw_file = os.path.join(static_dir, "sw.js")
    if os.path.exists(sw_file):
        return FileResponse(sw_file, media_type="application/javascript")
    return PlainTextResponse("// Service worker placeholder", media_type="application/javascript")
