"""
Internal marks evaluation service.
Enforces 40-mark maximum component limits, moderation locking workflow,
tamper-evident exam audit trail, and university upload formatting.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
import csv
import io
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import InternalMark, Student, Subject, ExamAuditLog, User
from app.schemas import BatchMarksUpdate, MarkItemUpdate
from app.config import settings


def get_subject_marks_sheet(db: Session, subject_id: int, batch_id: int) -> Dict[str, Any]:
    """Retrieve full marks sheet with component breakdown, moderation status and lock state."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    students = db.query(Student).filter(Student.batch_id == batch_id, Student.status == "Active").all()
    
    rows = []
    is_subject_locked = True
    moderation_status = "Moderated_Locked"

    for s in students:
        mark = db.query(InternalMark).filter(
            InternalMark.student_id == s.id,
            InternalMark.subject_id == subject_id
        ).first()

        if not mark:
            # Create draft placeholder if not exists
            mark = InternalMark(
                student_id=s.id,
                subject_id=subject_id,
                midterm_score=0.0,
                quiz_score=0.0,
                assignment_score=0.0,
                total_score=0.0,
                moderation_status="Draft",
                is_locked=False
            )
            db.add(mark)
            db.flush()

        if not mark.is_locked:
            is_subject_locked = False
            moderation_status = mark.moderation_status

        rows.append({
            "mark_id": mark.id,
            "student_id": s.id,
            "roll_no": s.roll_no,
            "name": s.name,
            "midterm_score": mark.midterm_score,
            "quiz_score": mark.quiz_score,
            "assignment_score": mark.assignment_score,
            "total_score": mark.total_score,
            "max_score": 40.0,
            "is_pass": mark.total_score >= settings.INTERNAL_PASS_THRESHOLD,
            "moderation_status": mark.moderation_status,
            "is_locked": mark.is_locked
        })

    db.commit()

    return {
        "subject_id": subject.id,
        "subject_code": subject.code,
        "subject_name": subject.name,
        "batch_id": batch_id,
        "is_locked": is_subject_locked,
        "moderation_status": moderation_status,
        "students": rows
    }


def update_marks(
    db: Session,
    payload: BatchMarksUpdate,
    actor_user: User
) -> List[Dict[str, Any]]:
    """
    Save or update internal marks.
    Enforces moderation lock protection and appends to the immutable exam audit trail.
    """
    subject = db.query(Subject).filter(Subject.id == payload.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    updated_records = []

    for item in payload.marks:
        # Validate individual component limits
        if item.midterm_score > 20.0 or item.quiz_score > 10.0 or item.assignment_score > 10.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Component marks out of bounds: Midterm max 20, Quiz max 10, Assignment max 10"
            )

        mark = db.query(InternalMark).filter(
            InternalMark.student_id == item.student_id,
            InternalMark.subject_id == payload.subject_id
        ).first()

        if mark and mark.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot modify marks for student ID {item.student_id}: Subject marks are moderated and locked for exam audits."
            )

        new_total = round(item.midterm_score + item.quiz_score + item.assignment_score, 1)

        if not mark:
            mark = InternalMark(
                student_id=item.student_id,
                subject_id=payload.subject_id,
                midterm_score=item.midterm_score,
                quiz_score=item.quiz_score,
                assignment_score=item.assignment_score,
                total_score=new_total,
                moderation_status="Draft",
                is_locked=False
            )
            db.add(mark)
            db.flush()

            audit = ExamAuditLog(
                student_id=item.student_id,
                subject_id=payload.subject_id,
                actor_username=actor_user.username,
                actor_role=actor_user.role,
                new_midterm=item.midterm_score,
                new_quiz=item.quiz_score,
                new_assignment=item.assignment_score,
                new_total=new_total,
                action_type="CREATE",
                reason=item.change_reason or "Initial internal mark entry"
            )
            db.add(audit)
        else:
            # Audit old vs new
            audit = ExamAuditLog(
                student_id=item.student_id,
                subject_id=payload.subject_id,
                actor_username=actor_user.username,
                actor_role=actor_user.role,
                old_midterm=mark.midterm_score,
                new_midterm=item.midterm_score,
                old_quiz=mark.quiz_score,
                new_quiz=item.quiz_score,
                old_assignment=mark.assignment_score,
                new_assignment=item.assignment_score,
                old_total=mark.total_score,
                new_total=new_total,
                action_type="UPDATE",
                reason=item.change_reason or "Mark revision by faculty"
            )
            db.add(audit)

            mark.midterm_score = item.midterm_score
            mark.quiz_score = item.quiz_score
            mark.assignment_score = item.assignment_score
            mark.total_score = new_total
            mark.updated_at = datetime.now(timezone.utc)

        updated_records.append({
            "student_id": item.student_id,
            "total_score": new_total,
            "status": "Updated"
        })

    db.commit()
    return updated_records


def set_moderation_lock(
    db: Session,
    subject_id: int,
    batch_id: int,
    action: str,  # 'SUBMIT', 'LOCK', 'UNLOCK'
    actor_user: User,
    reason: str = None
) -> Dict[str, Any]:
    """Transition moderation state of a subject batch."""
    students = db.query(Student).filter(Student.batch_id == batch_id).all()
    student_ids = [s.id for s in students]

    marks = db.query(InternalMark).filter(
        InternalMark.subject_id == subject_id,
        InternalMark.student_id.in_(student_ids)
    ).all()

    if not marks:
        raise HTTPException(status_code=404, detail="No mark entries found for this subject batch")

    now = datetime.now(timezone.utc)

    for m in marks:
        if action == "SUBMIT":
            m.moderation_status = "Submitted"
        elif action == "LOCK":
            m.moderation_status = "Moderated_Locked"
            m.is_locked = True
            m.locked_by = actor_user.full_name
            m.locked_at = now
        elif action == "UNLOCK":
            m.moderation_status = "Draft"
            m.is_locked = False
            m.locked_by = None
            m.locked_at = None

        audit = ExamAuditLog(
            student_id=m.student_id,
            subject_id=subject_id,
            actor_username=actor_user.username,
            actor_role=actor_user.role,
            action_type=f"MODERATION_{action}",
            old_total=m.total_score,
            new_total=m.total_score,
            reason=reason or f"Batch moderation transition to {action}"
        )
        db.add(audit)

    db.commit()
    return {
        "subject_id": subject_id,
        "batch_id": batch_id,
        "action": action,
        "status": "Success",
        "affected_students": len(marks)
    }


def export_university_marks_csv(db: Session, subject_id: int, batch_id: int) -> str:
    """Generate university upload format CSV with zero re-typing."""
    data = get_subject_marks_sheet(db, subject_id, batch_id)
    subject = db.query(Subject).filter(Subject.id == subject_id).first()

    output = io.StringIO()
    writer = csv.writer(output)

    # University header
    writer.writerow(["BIJU PATNAIK UNIVERSITY OF TECHNOLOGY / AUTONOMOUS EXAM PORTAL"])
    writer.writerow(["INTERNAL ASSESSMENT MARKS UPLOAD FORMAT (MAX MARKS: 40)"])
    writer.writerow(["Subject Code", subject.code, "Subject Name", subject.name, "Semester", subject.semester])
    writer.writerow([])
    writer.writerow([
        "SL_NO", "ROLL_NO", "STUDENT_NAME", "MIDTERM_20", "QUIZ_10",
        "ASSIGNMENT_10", "TOTAL_40", "STATUS", "MODERATION_LOCK"
    ])

    for i, s in enumerate(data["students"], start=1):
        writer.writerow([
            i,
            s["roll_no"],
            s["name"],
            s["midterm_score"],
            s["quiz_score"],
            s["assignment_score"],
            s["total_score"],
            "PASS" if s["is_pass"] else "FAIL",
            "LOCKED" if s["is_locked"] else "DRAFT"
        ])

    return output.getvalue()
