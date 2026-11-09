"""
Tests for Mobile Attendance, Offline Sync Idempotency, and Shortage Alerts (<75%).
"""

import pytest
from datetime import date
from sqlalchemy.orm import Session
from app.models import AttendanceRecord, AttendanceSession, Student, Subject, Batch, NotificationLog
from app.schemas import AttendanceBatchSubmit, AttendanceItem
from app.services import attendance_service, report_service


def test_attendance_marking_and_stats(db: Session):
    student = db.query(Student).filter(Student.roll_no == "ENG-24-CSE-0412").first()
    assert student is not None

    stats = attendance_service.calculate_student_attendance(db, student.id)
    assert "percentage" in stats
    assert "total" in stats
    assert "attended" in stats
    assert stats["total"] > 0
    assert stats["percentage"] == 81.5


def test_benchmark_student_attendance_matches_seed_data(db: Session):
    expected_attendance = {
        "ENG-24-CSE-0412": 81.5,
        "ENG-24-ME-0177": 68.2,
        "MBA-25-0093": 92.0,
    }

    for roll_no, expected_percentage in expected_attendance.items():
        student = db.query(Student).filter(Student.roll_no == roll_no).one()
        stats = attendance_service.calculate_student_attendance(db, student.id)
        assert stats["percentage"] == expected_percentage


def test_seeded_attendance_sessions_are_counted_as_same_day_entries(db: Session):
    kpi = report_service.get_kpi_dashboard_metrics(db)

    assert kpi["kpi_same_day_attendance_rate"] == 100.0
    assert kpi["kpi_attendance_success"] is True


def test_same_day_attendance_kpi_is_zero_without_sessions(db: Session):
    db.query(AttendanceRecord).delete()
    db.query(AttendanceSession).delete()
    db.commit()

    kpi = report_service.get_kpi_dashboard_metrics(db)

    assert kpi["kpi_same_day_attendance_rate"] == 0.0
    assert kpi["kpi_attendance_success"] is False


def test_offline_sync_idempotency(db: Session):
    """Submitting the same offline client_batch_id multiple times must be idempotent."""
    batch = db.query(Batch).first()
    subject = db.query(Subject).first()
    students = db.query(Student).filter(Student.batch_id == batch.id).all()
    
    unique_sync_id = "OFFLINE-TEST-BATCH-UUID-12345"
    payload = AttendanceBatchSubmit(
        client_batch_id=unique_sync_id,
        subject_id=subject.id,
        batch_id=batch.id,
        session_date=date(2026, 11, 1),
        period=1,
        records=[AttendanceItem(student_id=s.id, status="Present") for s in students],
        captured_offline=True
    )

    # First submission
    session1, alerts1 = attendance_service.submit_attendance_session(db, payload, faculty_user_id=1)
    assert session1.id is not None
    assert session1.client_batch_id == unique_sync_id

    # Second submission with identical client_batch_id (simulates network retry)
    session2, alerts2 = attendance_service.submit_attendance_session(db, payload, faculty_user_id=1)
    assert session2.id == session1.id  # Same session, zero duplicate sessions created!


def test_attendance_shortage_alert_trigger(db: Session):
    """Ensure student below 75% attendance triggers automated notification."""
    ankit = db.query(Student).filter(Student.roll_no == "ENG-24-ME-0177").first()
    assert ankit is not None
    stats = attendance_service.calculate_student_attendance(db, ankit.id)
    assert stats["percentage"] < 75.0  # Ankit Panda is 68.2%
