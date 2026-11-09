"""
Bilingual notification service for parents and guardians.
Supports English and Odia (Unicode script) for SMS/WhatsApp dispatches
as specified in the problem statement constraints.
"""

from typing import List, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import NotificationLog, Student
from app.services.attendance_service import calculate_student_attendance
from app.config import settings


def get_notification_logs(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve audit history of dispatched parent notifications."""
    logs = db.query(NotificationLog).order_by(NotificationLog.created_at.desc()).limit(limit).all()
    results = []
    
    for l in logs:
        student = db.query(Student).filter(Student.id == l.student_id).first()
        results.append({
            "id": l.id,
            "student_id": l.student_id,
            "student_roll": student.roll_no if student else "N/A",
            "student_name": student.name if student else "N/A",
            "parent_phone": l.recipient_phone,
            "channel": l.channel,
            "trigger_type": l.trigger_type,
            "message_text_en": l.message_text_en,
            "message_text_or": l.message_text_or,
            "status": l.status,
            "dispatched_at": l.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return results


def send_manual_parent_alert(
    db: Session,
    student_id: int,
    trigger_type: str,
    channel: str = "SMS"
) -> Dict[str, Any]:
    """Manually dispatch or re-send bilingual parent notice."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    att_stats = calculate_student_attendance(db, student.id)
    pct = att_stats["percentage"]
    due = student.fee_ledger.due_amount if student.fee_ledger else 0.0

    if trigger_type == "ATTENDANCE_SHORTAGE":
        if pct >= settings.MINIMUM_ATTENDANCE_PERCENTAGE:
            raise HTTPException(
                status_code=409,
                detail="Student does not currently meet the attendance-shortage alert criteria",
            )
        msg_en = (
            f"URGENT ATTENDANCE SHORTAGE: Your ward {student.name} ({student.roll_no}) has only "
            f"{pct}% attendance in Semester 3 (minimum required: 75.0%). Risk of university exam debarment. "
            f"Contact college office: 0674-2391000."
        )
        msg_or = (
            f"ଜରୁରୀ ଉପସ୍ଥିତି ସତର୍କତା: ଆପଣଙ୍କ ପିଲା {student.name} ({student.roll_no}) ଙ୍କ "
            f"ଉପସ୍ଥିତି {pct}% ରହିଛି (ସର୍ବନିମ୍ନ ଆବଶ୍ୟକ: ୭୫%)। ବିଶ୍ୱବିଦ୍ୟାଳୟ ପରୀକ୍ଷା ଦେବାରୁ ବଞ୍ଚିତ ହେବା ଆଶଙ୍କା ରହିଛି। "
            f"ତୁରନ୍ତ କଲେଜ ଅଫିସ ସହିତ ଯୋଗାଯୋଗ କରନ୍ତୁ: ୦୬୭୪-୨୩୯୧୦୦୦।"
        )
    else:
        if due <= 0:
            raise HTTPException(
                status_code=409,
                detail="Student does not currently have an outstanding fee balance",
            )
        msg_en = (
            f"FEE REMINDER: Semester fee balance of ₹{due:,.0f} is pending for {student.name} ({student.roll_no}). "
            f"Please clear before the upcoming deadline. Payment link: https://portal.trust-erp.ac.in/pay"
        )
        msg_or = (
            f"ଫି ଜମା ସୂଚନା: ଆପଣଙ୍କ ପିଲା {student.name} ({student.roll_no}) ଙ୍କ ସେମିଷ୍ଟାର ବାକି ଫି "
            f"₹{due:,.0f} ପୈଠ କରିବାକୁ ବାକି ଅଛି। ଦୟାକରି ଶୀଘ୍ର ଜମା କରନ୍ତୁ।"
        )

    log = NotificationLog(
        student_id=student.id,
        recipient_type="Parent",
        recipient_phone=student.parent_phone,
        channel=channel,
        message_text_en=msg_en,
        message_text_or=msg_or,
        trigger_type=trigger_type,
        status="Sent_Mock"
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        "status": "Success",
        "notification_id": log.id,
        "recipient_phone": log.recipient_phone,
        "message_en": msg_en,
        "message_or": msg_or,
        "channel": channel
    }
