"""
SQLAlchemy database models for College ERP.
Captures Masters, Attendance, Internal Marks with Moderation Lock,
Exam Audit Trail, Fee Accounting, DPDP Act 2023 Consent, and AI Mentor Tasks.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    ForeignKey, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    role = Column(String(30), nullable=False, default="faculty")  # 'office_admin', 'faculty', 'exam_moderator'
    campus_code = Column(String(20), default="BBSR-ENG", nullable=False)
    department = Column(String(50), default="CSE")
    created_at = Column(DateTime, default=utcnow)


class Campus(Base):
    __tablename__ = "campuses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    trust_name = Column(String(150), nullable=False)
    city = Column(String(50), default="Bhubaneswar")
    state = Column(String(50), default="Odisha")
    programmes = relationship("Programme", back_populates="campus", cascade="all, delete-orphan")


class Programme(Base):
    __tablename__ = "programmes"

    id = Column(Integer, primary_key=True, index=True)
    campus_id = Column(Integer, ForeignKey("campuses.id"), nullable=False)
    code = Column(String(30), unique=True, index=True, nullable=False)  # e.g., 'BTECH-CSE', 'BTECH-ME', 'MBA'
    name = Column(String(100), nullable=False)
    degree_type = Column(String(30), nullable=False)  # 'Undergraduate', 'Postgraduate'
    duration_years = Column(Integer, default=4)
    annual_tuition = Column(Float, default=120000.0)

    campus = relationship("Campus", back_populates="programmes")
    batches = relationship("Batch", back_populates="programme", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="programme", cascade="all, delete-orphan")
    fee_structures = relationship("FeeStructure", back_populates="programme", cascade="all, delete-orphan")


class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    programme_id = Column(Integer, ForeignKey("programmes.id"), nullable=False)
    name = Column(String(50), nullable=False)  # e.g., '2024-2028'
    academic_year = Column(Integer, nullable=False, default=2)  # Year 1, 2, 3, 4
    current_semester = Column(Integer, nullable=False, default=3)
    section = Column(String(10), default="A")

    programme = relationship("Programme", back_populates="batches")
    students = relationship("Student", back_populates="batch")
    attendance_sessions = relationship("AttendanceSession", back_populates="batch")


class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    employee_code = Column(String(30), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False)
    designation = Column(String(50), default="Assistant Professor")
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)

    teaching_assignments = relationship("FacultySubjectMapping", back_populates="faculty")
    mentor_tasks = relationship("MentorTask", back_populates="faculty")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    programme_id = Column(Integer, ForeignKey("programmes.id"), nullable=False)
    semester = Column(Integer, nullable=False)
    code = Column(String(20), unique=True, index=True, nullable=False)  # e.g., 'CS301'
    name = Column(String(100), nullable=False)
    credits = Column(Integer, default=4)
    max_internal_marks = Column(Float, default=40.0)

    programme = relationship("Programme", back_populates="subjects")
    faculty_mappings = relationship("FacultySubjectMapping", back_populates="subject")
    attendance_sessions = relationship("AttendanceSession", back_populates="subject")
    internal_marks = relationship("InternalMark", back_populates="subject")


class FacultySubjectMapping(Base):
    __tablename__ = "faculty_subject_mappings"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)

    faculty = relationship("Faculty", back_populates="teaching_assignments")
    subject = relationship("Subject", back_populates="faculty_mappings")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String(40), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    parent_name = Column(String(100), nullable=False)
    parent_phone = Column(String(20), nullable=False)
    parent_email = Column(String(100), nullable=True)
    
    programme_id = Column(Integer, ForeignKey("programmes.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    current_year = Column(Integer, nullable=False, default=2)
    current_semester = Column(Integer, nullable=False, default=3)
    category = Column(String(30), default="General")  # 'General', 'TFW', 'OBC', 'SC', 'ST'
    
    # DPDP Act 2023 Compliance
    is_minor = Column(Boolean, default=False)
    dpdp_consent_status = Column(String(30), default="Granted")  # 'Granted', 'Pending', 'Exempt'
    dpdp_consent_date = Column(DateTime, nullable=True)
    
    status = Column(String(20), default="Active")
    created_at = Column(DateTime, default=utcnow)

    batch = relationship("Batch", back_populates="students")
    attendance_records = relationship("AttendanceRecord", back_populates="student", cascade="all, delete-orphan")
    internal_marks = relationship("InternalMark", back_populates="student", cascade="all, delete-orphan")
    fee_ledger = relationship("StudentFeeLedger", back_populates="student", uselist=False, cascade="all, delete-orphan")
    at_risk_flags = relationship("AtRiskFlag", back_populates="student", cascade="all, delete-orphan")
    mentor_tasks = relationship("MentorTask", back_populates="student")


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    session_date = Column(Date, nullable=False)
    period = Column(Integer, nullable=False, default=1)
    
    total_students = Column(Integer, default=0)
    present_count = Column(Integer, default=0)
    absent_count = Column(Integer, default=0)
    late_count = Column(Integer, default=0)
    
    sync_status = Column(String(20), default="Synced")  # 'Synced', 'Offline_Queued'
    client_batch_id = Column(String(64), index=True, nullable=True)  # Idempotent sync key
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    subject = relationship("Subject", back_populates="attendance_sessions")
    batch = relationship("Batch", back_populates="attendance_sessions")
    records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("subject_id", "batch_id", "session_date", "period", name="uq_session_slot"),
    )


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    status = Column(String(20), nullable=False, default="Present")  # 'Present', 'Absent', 'Late'
    remarks = Column(String(100), nullable=True)
    recorded_at = Column(DateTime, default=utcnow)

    session = relationship("AttendanceSession", back_populates="records")
    student = relationship("Student", back_populates="attendance_records")

    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_session_student"),
        Index("idx_student_attendance", "student_id", "status"),
    )


class InternalMark(Base):
    __tablename__ = "internal_marks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    
    # 40 marks breakdown: Midterm(20) + Quiz(10) + Lab/Assignment(10)
    midterm_score = Column(Float, default=0.0)      # max 20
    quiz_score = Column(Float, default=0.0)         # max 10
    assignment_score = Column(Float, default=0.0)   # max 10
    total_score = Column(Float, default=0.0)        # max 40
    
    # Moderation & Lock State
    moderation_status = Column(String(30), default="Draft")  # 'Draft', 'Submitted', 'Moderated_Locked'
    is_locked = Column(Boolean, default=False)
    locked_by = Column(String(100), nullable=True)
    locked_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    student = relationship("Student", back_populates="internal_marks")
    subject = relationship("Subject", back_populates="internal_marks")

    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", name="uq_student_subject_marks"),
    )


class ExamAuditLog(Base):
    """
    Tamper-evident audit trail for every single internal mark creation or update.
    Required by university exam regulations and NAAC Criterion 2.5 audit.
    """
    __tablename__ = "exam_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    actor_username = Column(String(50), nullable=False)
    actor_role = Column(String(30), nullable=False)
    
    old_midterm = Column(Float, nullable=True)
    new_midterm = Column(Float, nullable=True)
    old_quiz = Column(Float, nullable=True)
    new_quiz = Column(Float, nullable=True)
    old_assignment = Column(Float, nullable=True)
    new_assignment = Column(Float, nullable=True)
    old_total = Column(Float, nullable=True)
    new_total = Column(Float, nullable=True)
    
    action_type = Column(String(30), default="UPDATE")  # 'CREATE', 'UPDATE', 'MODERATION_LOCK', 'UNLOCK_REQUEST'
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utcnow, index=True)


class FeeStructure(Base):
    __tablename__ = "fee_structures"

    id = Column(Integer, primary_key=True, index=True)
    programme_id = Column(Integer, ForeignKey("programmes.id"), nullable=False)
    academic_year = Column(Integer, default=2)
    category = Column(String(30), default="General")  # 'General', 'TFW', 'Merit'
    
    tuition_fee = Column(Float, default=95000.0)
    exam_fee = Column(Float, default=5000.0)
    lab_fee = Column(Float, default=15000.0)
    library_fee = Column(Float, default=5000.0)
    total_fee = Column(Float, default=120000.0)

    programme = relationship("Programme", back_populates="fee_structures")


class StudentFeeLedger(Base):
    __tablename__ = "student_fee_ledgers"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), unique=True, nullable=False)
    
    total_fee = Column(Float, default=120000.0)
    scholarship_discount = Column(Float, default=0.0)
    net_payable = Column(Float, default=120000.0)
    paid_amount = Column(Float, default=0.0)
    due_amount = Column(Float, default=120000.0)
    
    last_payment_date = Column(DateTime, nullable=True)
    reconciliation_status = Column(String(30), default="Reconciled")  # 'Reconciled', 'Pending_Bank_Match'
    status = Column(String(30), default="Due")  # 'Paid', 'Partial', 'Due'
    
    student = relationship("Student", back_populates="fee_ledger")
    payments = relationship("FeePayment", back_populates="ledger", cascade="all, delete-orphan")


class FeePayment(Base):
    __tablename__ = "fee_payments"

    id = Column(Integer, primary_key=True, index=True)
    ledger_id = Column(Integer, ForeignKey("student_fee_ledgers.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    receipt_no = Column(String(50), unique=True, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    payment_mode = Column(String(30), default="UPI_MOCK")  # 'UPI_MOCK', 'BANK_COUNTER', 'NETBANKING_MOCK', 'NEFT'
    transaction_ref = Column(String(100), unique=True, nullable=False)
    payment_date = Column(DateTime, default=utcnow)
    
    is_reconciled = Column(Boolean, default=True)
    tally_voucher_no = Column(String(50), nullable=True)
    remarks = Column(String(200), default="Semester Fee Installment")

    ledger = relationship("StudentFeeLedger", back_populates="payments")


class AtRiskFlag(Base):
    """
    AI/Rule-generated at-risk indicator.
    Flagging only creates a mentor task. It NEVER makes punitive or direct grade changes.
    """
    __tablename__ = "at_risk_flags"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    risk_level = Column(String(20), nullable=False)  # 'HIGH', 'MEDIUM', 'LOW'
    risk_score = Column(Float, default=0.0)          # 0.0 to 100.0
    triggers = Column(Text, nullable=False)           # JSON array of reasons e.g. ["Attendance 68.2% < 75%", "Internal Marks 21/40"]
    attendance_pct = Column(Float, default=0.0)
    internal_marks = Column(Float, default=0.0)
    fee_due = Column(Float, default=0.0)
    
    flagged_at = Column(DateTime, default=utcnow)
    status = Column(String(20), default="OPEN")       # 'OPEN', 'TASK_CREATED', 'RESOLVED'

    student = relationship("Student", back_populates="at_risk_flags")
    mentor_task = relationship("MentorTask", back_populates="risk_flag", uselist=False)


class MentorTask(Base):
    """Actionable intervention created when a student is flagged at risk."""
    __tablename__ = "mentor_tasks"

    id = Column(Integer, primary_key=True, index=True)
    risk_flag_id = Column(Integer, ForeignKey("at_risk_flags.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    recommended_action = Column(String(255), default="Conduct 1-on-1 counseling and remedial assessment")
    status = Column(String(30), default="Pending")  # 'Pending', 'In_Progress', 'Completed'
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)

    risk_flag = relationship("AtRiskFlag", back_populates="mentor_task")
    student = relationship("Student", back_populates="mentor_tasks")
    faculty = relationship("Faculty", back_populates="mentor_tasks")


class NotificationLog(Base):
    """Automated shortage & fee alerts dispatched in English and Odia."""
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    recipient_type = Column(String(30), default="Parent")  # 'Parent', 'Student'
    recipient_phone = Column(String(20), nullable=False)
    channel = Column(String(20), default="SMS")            # 'SMS', 'WhatsApp'
    
    message_text_en = Column(Text, nullable=False)
    message_text_or = Column(Text, nullable=False)         # Odia script translation
    trigger_type = Column(String(50), nullable=False)      # 'ATTENDANCE_SHORTAGE', 'FEE_REMINDER'
    
    status = Column(String(20), default="Sent_Mock")
    created_at = Column(DateTime, default=utcnow)


class DPDPAuditLog(Base):
    """Audit log for student data views, consent checks, and minor record access under DPDP Act 2023."""
    __tablename__ = "dpdp_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_username = Column(String(50), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    action = Column(String(50), nullable=False)  # 'VIEW_PROFILE', 'EXPORT_RECORD', 'CONSENT_VERIFY'
    is_minor = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=utcnow, index=True)
    access_purpose = Column(String(100), default="Academic Administration")
