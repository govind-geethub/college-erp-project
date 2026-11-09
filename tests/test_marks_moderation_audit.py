"""
Tests for Internal Marks (40 Max), Moderation Locking, and Tamper-Evident Exam Audits.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import InternalMark, Student, Subject, ExamAuditLog, User
from app.schemas import BatchMarksUpdate, MarkItemUpdate
from app.services import marks_service


def test_internal_marks_bounds_and_calculation(db: Session):
    student = db.query(Student).filter(Student.roll_no == "ENG-24-CSE-0412").first()
    subject = db.query(Subject).filter(Subject.code == "CS301").first()
    moderator_user = db.query(User).filter(User.username == "moderator").first()

    # Unlock first for testing edit
    marks_service.set_moderation_lock(db, subject.id, student.batch_id, "UNLOCK", moderator_user)

    # Valid score: Midterm 18 (max 20), Quiz 9 (max 10), Assignment 8 (max 10) = 35 total
    payload = BatchMarksUpdate(
        subject_id=subject.id,
        marks=[
            MarkItemUpdate(
                student_id=student.id,
                midterm_score=18.0,
                quiz_score=9.0,
                assignment_score=8.0,
                change_reason="Semester 3 mid-term re-eval"
            )
        ]
    )
    res = marks_service.update_marks(db, payload, moderator_user)
    assert res[0]["total_score"] == 35.0

    # Verify audit log was created
    audit = db.query(ExamAuditLog).filter(
        ExamAuditLog.student_id == student.id,
        ExamAuditLog.subject_id == subject.id
    ).order_by(ExamAuditLog.timestamp.desc()).first()
    assert audit is not None
    assert audit.new_total == 35.0
    assert audit.actor_username == "moderator"


def test_internal_marks_bounds_exceeded_fails(db: Session):
    student = db.query(Student).filter(Student.roll_no == "ENG-24-CSE-0412").first()
    subject = db.query(Subject).filter(Subject.code == "CS301").first()

    # Exceeding component limits (Midterm 25 > 20) must be rejected by Pydantic validation
    import pydantic
    with pytest.raises(pydantic.ValidationError) as exc:
        MarkItemUpdate(student_id=student.id, midterm_score=25.0, quiz_score=8.0, assignment_score=8.0)
    assert "midterm_score" in str(exc.value)


def test_locked_marks_cannot_be_modified(db: Session):
    student = db.query(Student).filter(Student.roll_no == "ENG-24-CSE-0412").first()
    subject = db.query(Subject).filter(Subject.code == "CS301").first()
    moderator_user = db.query(User).filter(User.username == "moderator").first()
    faculty_user = db.query(User).filter(User.username == "faculty").first()

    # Lock subject marks
    marks_service.set_moderation_lock(db, subject.id, student.batch_id, "LOCK", moderator_user)

    # Attempting to edit while locked must raise 403 Forbidden
    with pytest.raises(HTTPException) as exc:
        marks_service.update_marks(
            db,
            BatchMarksUpdate(
                subject_id=subject.id,
                marks=[MarkItemUpdate(student_id=student.id, midterm_score=19.0, quiz_score=9.0, assignment_score=9.0)]
            ),
            faculty_user
        )
    assert exc.value.status_code == 403
    assert "moderated and locked" in exc.value.detail


def test_university_csv_export_format(db: Session):
    subject = db.query(Subject).filter(Subject.code == "CS301").first()
    batch = db.query(Student).filter(Student.roll_no == "ENG-24-CSE-0412").first().batch_id

    csv_data = marks_service.export_university_marks_csv(db, subject.id, batch)
    assert "BIJU PATNAIK UNIVERSITY OF TECHNOLOGY" in csv_data
    assert "MIDTERM_20" in csv_data
    assert "TOTAL_40" in csv_data
    assert "ENG-24-CSE-0412" in csv_data
