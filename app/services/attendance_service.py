"""
Attendance service supporting mobile-first marking in <30 seconds,
offline queue synchronization with idempotent batch tokens,
and automatic triggers for attendance shortages (<75%).
"""

from datetime import date, datetime, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import (
    AttendanceSession, AttendanceRecord, Student, Subject, Batch, Faculty,
    NotificationLog
)
from app.schemas import AttendanceBatchSubmit, AttendanceItem
from app.config import settings


def get_students_for_batch(db: Session, batch_id: int) -> List[Dict[str, Any]]:
    """Retrieve roster for a batch with current cumulative attendance statistics."""
    students = db.query(Student).filter(Student.batch_id == batch_id, Student.status == "Active").all()
    results = []
    
    for s in students:
        stats = calculate_student_attendance(db, s.id)
        results.append({
            "student_id": s.id,
            "roll_no": s.roll_no,
            "name": s.name,
            "category": s.category,
            "is_minor": s.is_minor,
            "attendance_pct": stats["percentage"],
            "total_classes": stats["total"],
            "attended_classes": stats["attended"],
            "is_below_75": stats["percentage"] < settings.MINIMUM_ATTENDANCE_PERCENTAGE
        })
    
    return results


def calculate_student_attendance(db: Session, student_id: int, subject_id: int = None) -> Dict[str, Any]:
    """Calculate attendance percentage for a student across all subjects or a specific subject."""
    query = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student_id)
    if subject_id:
        query = query.join(AttendanceSession).filter(AttendanceSession.subject_id == subject_id)
    
    records = query.all()
    total = len(records)
    if total == 0:
        # Default baseline if no sessions yet
        return {"total": 0, "attended": 0, "percentage": 100.0}
    
    attended = sum(1 for r in records if r.status in ("Present", "Late"))
    pct = round((attended / total) * 100, 1)
    return {"total": total, "attended": attended, "percentage": pct}


def submit_attendance_session(
    db: Session,
    payload: AttendanceBatchSubmit,
    faculty_user_id: int
) -> Tuple[AttendanceSession, List[Dict[str, Any]]]:
    """
    Record attendance session.
    Idempotent: Uses client_batch_id to prevent duplicates on weak classroom Wi-Fi retries.
    """
    # 1. Check idempotency
    if payload.client_batch_id:
        existing = db.query(AttendanceSession).filter(
            AttendanceSession.client_batch_id == payload.client_batch_id
        ).first()
        if existing:
            return existing, []

    # 2. Check if a session already exists for this exact subject, batch, date, and period
    session = db.query(AttendanceSession).filter(
        AttendanceSession.subject_id == payload.subject_id,
        AttendanceSession.batch_id == payload.batch_id,
        AttendanceSession.session_date == payload.session_date,
        AttendanceSession.period == payload.period
    ).first()

    # Resolve faculty
    faculty = db.query(Faculty).filter(Faculty.user_id == faculty_user_id).first()
    faculty_id = faculty.id if faculty else 1

    if not session:
        session = AttendanceSession(
            subject_id=payload.subject_id,
            batch_id=payload.batch_id,
            faculty_id=faculty_id,
            session_date=payload.session_date,
            period=payload.period,
            sync_status="Synced",
            client_batch_id=payload.client_batch_id
        )
        db.add(session)
        db.flush()
    else:
        # Overwrite records for this session slot
        db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session.id).delete()

    present_count = 0
    absent_count = 0
    late_count = 0
    shortage_alerts_triggered = []

    for item in payload.records:
        rec = AttendanceRecord(
            session_id=session.id,
            student_id=item.student_id,
            status=item.status,
            remarks=item.remarks
        )
        db.add(rec)

        if item.status == "Present":
            present_count += 1
        elif item.status == "Absent":
            absent_count += 1
        elif item.status == "Late":
            late_count += 1

    db.flush()

    session.total_students = len(payload.records)
    session.present_count = present_count
    session.absent_count = absent_count
    session.late_count = late_count
    session.sync_status = "Synced"

    # 3. Check for students dropping below 75% and trigger automated alerts
    for item in payload.records:
        stats = calculate_student_attendance(db, item.student_id)
        if stats["percentage"] < settings.MINIMUM_ATTENDANCE_PERCENTAGE:
            student = db.query(Student).filter(Student.id == item.student_id).first()
            if student:
                # Trigger bilingual parent notice
                msg_en = (
                    f"ATTENDANCE ALERT: Your ward {student.name} ({student.roll_no}) attendance has fallen "
                    f"to {stats['percentage']}%, which is below the mandatory 75% AICTE/University norm. "
                    f"Total classes: {stats['total']}, Attended: {stats['attended']}."
                )
                msg_or = (
                    f"ଉପସ୍ଥିତି ସତର୍କତା: ଆପଣଙ୍କ ପିଲା {student.name} ({student.roll_no}) ଙ୍କ ଉପସ୍ଥିତି "
                    f"{stats['percentage']}% କୁ ଖସି ଆସିଛି, ଯାହା ନିୟମିତ ୭୫% ରୁ କମ। "
                    f"ମୋଟ କ୍ଲାସ: {stats['total']}, ଉପସ୍ଥିତ: {stats['attended']}।"
                )
                
                notice = NotificationLog(
                    student_id=student.id,
                    recipient_type="Parent",
                    recipient_phone=student.parent_phone,
                    channel="SMS",
                    message_text_en=msg_en,
                    message_text_or=msg_or,
                    trigger_type="ATTENDANCE_SHORTAGE",
                    status="Sent_Mock"
                )
                db.add(notice)
                shortage_alerts_triggered.append({
                    "student_id": student.id,
                    "roll_no": student.roll_no,
                    "name": student.name,
                    "attendance_pct": stats["percentage"],
                    "parent_phone": student.parent_phone,
                    "alert_sent": True
                })

    db.commit()
    db.refresh(session)
    return session, shortage_alerts_triggered
