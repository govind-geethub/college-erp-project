"""
At-Risk Student Flagging and Early Intervention Engine.
Combines attendance trends, internal mark performance, and fee status
to identify vulnerable students and generate actionable mentor counseling tasks.
STRICT RULE: Only creates mentor tasks. Does NOT alter marks or attendance.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
import json
from sqlalchemy.orm import Session
from app.models import Student, AtRiskFlag, MentorTask, Faculty, InternalMark, StudentFeeLedger
from app.services.attendance_service import calculate_student_attendance
from app.config import settings


def evaluate_student_risk(db: Session, student_id: int) -> Dict[str, Any]:
    """Calculate multi-factor risk profile for a single student."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return {}

    # 1. Attendance Factor
    att_stats = calculate_student_attendance(db, student.id)
    att_pct = att_stats["percentage"]
    
    # 2. Internal Marks Factor
    mark_entry = db.query(InternalMark).filter(InternalMark.student_id == student.id).first()
    internal_mark = mark_entry.total_score if mark_entry else 0.0
    
    # 3. Fee Due Factor
    ledger = student.fee_ledger
    fee_due = ledger.due_amount if ledger else 0.0

    # Risk Scoring Algorithm
    risk_score = 0.0
    triggers = []

    # Attendance triggers (50% weight)
    if att_pct < 65.0:
        risk_score += 50.0
        triggers.append(f"Severe attendance shortage ({att_pct}% vs required 75.0%)")
    elif att_pct < 75.0:
        risk_score += 40.0
        triggers.append(f"Attendance below threshold ({att_pct}% vs required 75.0%)")
    elif att_pct < 80.0:
        risk_score += 15.0
        triggers.append(f"Borderline attendance ({att_pct}%)")

    # Internal marks triggers (35% weight)
    if internal_mark < 16.0:  # Below pass mark
        risk_score += 35.0
        triggers.append(f"Failing internal marks ({internal_mark}/40, pass is 16.0)")
    elif internal_mark < 24.0:  # Below average (60%)
        risk_score += 25.0
        triggers.append(f"Below average internal marks ({internal_mark}/40)")

    # Fee Due triggers (15% weight)
    if fee_due > 40000.0:
        risk_score += 15.0
        triggers.append(f"Significant fee arrears outstanding (₹{fee_due:,.0f})")
    elif fee_due > 15000.0:
        risk_score += 10.0
        triggers.append(f"Fee dues pending (₹{fee_due:,.0f})")

    risk_level = "LOW"
    if risk_score >= 60.0:
        risk_level = "HIGH"
    elif risk_score >= 35.0:
        risk_level = "MEDIUM"

    return {
        "student_id": student.id,
        "roll_no": student.roll_no,
        "name": student.name,
        "programme": student.batch.programme.name if student.batch else "B.Tech",
        "year": student.current_year,
        "attendance_pct": att_pct,
        "internal_marks": internal_mark,
        "fee_due": fee_due,
        "risk_score": round(risk_score, 1),
        "risk_level": risk_level,
        "triggers": triggers,
        "is_at_risk": risk_level in ("HIGH", "MEDIUM")
    }


def run_campus_risk_assessment(db: Session, campus_code: str = "BBSR-ENG") -> List[Dict[str, Any]]:
    """
    Scan all active students and generate or update AtRiskFlag records and MentorTasks.
    Adheres strictly to the rule: only creates mentor tasks, never modifies academic records.
    """
    students = db.query(Student).filter(Student.status == "Active").all()
    results = []

    for s in students:
        assessment = evaluate_student_risk(db, s.id)
        if not assessment:
            continue

        if assessment["is_at_risk"]:
            # Check or create AtRiskFlag
            flag = db.query(AtRiskFlag).filter(AtRiskFlag.student_id == s.id).first()
            if not flag:
                flag = AtRiskFlag(
                    student_id=s.id,
                    risk_level=assessment["risk_level"],
                    risk_score=assessment["risk_score"],
                    triggers=json.dumps(assessment["triggers"]),
                    attendance_pct=assessment["attendance_pct"],
                    internal_marks=assessment["internal_marks"],
                    fee_due=assessment["fee_due"],
                    status="TASK_CREATED"
                )
                db.add(flag)
                db.flush()
            else:
                flag.risk_level = assessment["risk_level"]
                flag.risk_score = assessment["risk_score"]
                flag.triggers = json.dumps(assessment["triggers"])
                flag.attendance_pct = assessment["attendance_pct"]
                flag.internal_marks = assessment["internal_marks"]
                flag.fee_due = assessment["fee_due"]

            # Assign mentor task to department faculty
            mentor_task = db.query(MentorTask).filter(MentorTask.student_id == s.id).first()
            if not mentor_task:
                # Find available faculty for mentoring
                faculty = db.query(Faculty).first()
                faculty_id = faculty.id if faculty else 1

                task_title = f"Academic Counseling: {s.name} ({s.roll_no})"
                recs = "1. Schedule individual counseling. 2. Provide tutorial remedial sheets. 3. Monitor weekly attendance."

                mentor_task = MentorTask(
                    risk_flag_id=flag.id,
                    student_id=s.id,
                    faculty_id=faculty_id,
                    title=task_title,
                    description=f"Auto-generated early warning intervention. Student triggered: {'; '.join(assessment['triggers'])}",
                    recommended_action=recs,
                    status="Pending"
                )
                db.add(mentor_task)

            assessment["flag_id"] = flag.id
            assessment["mentor_task_id"] = mentor_task.id if mentor_task else None
            results.append(assessment)

    db.commit()
    # Sort by risk_score descending
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results
