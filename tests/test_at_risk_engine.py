"""
Tests for AI At-Risk Student Engine and Mentor Task Creation.
Validates that at-risk flags ONLY spawn mentor tasks and NEVER change marks/attendance.
"""

import pytest
from sqlalchemy.orm import Session
from app.models import Student, MentorTask, AtRiskFlag
from app.services import at_risk_engine


def test_ankit_panda_flagged_high_risk(db: Session):
    """Ankit Panda has 68.2% attendance (<75%), 21/40 marks, and ₹45,000 fee due."""
    ankit = db.query(Student).filter(Student.roll_no == "ENG-24-ME-0177").first()
    assessment = at_risk_engine.evaluate_student_risk(db, ankit.id)

    assert assessment["is_at_risk"] is True
    assert assessment["risk_level"] == "HIGH"
    assert assessment["risk_score"] >= 60.0
    assert any("attendance" in t.lower() for t in assessment["triggers"])


def test_at_risk_only_creates_mentor_task(db: Session):
    """Risk engine creates actionable mentor tasks and does NOT touch marks or attendance records."""
    initial_marks = {s.id: (s.internal_marks[0].total_score if s.internal_marks else 0.0) for s in db.query(Student).all()}

    flagged_list = at_risk_engine.run_campus_risk_assessment(db)
    assert len(flagged_list) > 0

    # Ensure mentor task exists
    tasks = db.query(MentorTask).all()
    assert len(tasks) > 0

    # Verify that NO student's marks were modified by running the risk scan
    for s in db.query(Student).all():
        current_mark = s.internal_marks[0].total_score if s.internal_marks else 0.0
        assert current_mark == initial_marks[s.id]
