"""
Pydantic schemas for data validation and serialization.
Complies with Pydantic v2 best practices.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


# --- Auth Schemas ---
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    full_name: str
    role: str
    campus_code: str
    department: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    email: str
    role: str
    campus_code: str
    department: Optional[str]


# --- Master Schemas ---
class CampusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    trust_name: str
    city: str
    state: str


class ProgrammeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    degree_type: str
    duration_years: int
    annual_tuition: float


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    academic_year: int
    current_semester: int
    section: str
    programme_id: int


class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    semester: int
    credits: int
    max_internal_marks: float


# --- Student Schemas ---
class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    roll_no: str
    name: str
    email: str
    phone: str
    parent_name: str
    parent_phone: str
    programme_id: int
    batch_id: int
    current_year: int
    current_semester: int
    category: str
    is_minor: bool
    dpdp_consent_status: str
    status: str


class StudentDetailOut(StudentOut):
    attendance_pct: float = 0.0
    total_classes: int = 0
    attended_classes: int = 0
    internal_marks_total: float = 0.0
    fee_due: float = 0.0
    fee_status: str = "Due"
    is_at_risk: bool = False
    risk_level: Optional[str] = None


# --- Attendance Schemas (with Offline Sync) ---
class AttendanceItem(BaseModel):
    student_id: int
    status: str = Field(..., pattern="^(Present|Absent|Late)$")
    remarks: Optional[str] = None


class AttendanceBatchSubmit(BaseModel):
    """Payload for submitting attendance, supporting offline queued sessions with sync."""
    client_batch_id: str
    subject_id: int
    batch_id: int
    session_date: date
    period: int = Field(default=1, ge=1, le=8)
    records: List[AttendanceItem]
    captured_offline: bool = False


class AttendanceSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    batch_id: int
    faculty_id: int
    session_date: date
    period: int
    total_students: int
    present_count: int
    absent_count: int
    late_count: int
    sync_status: str
    client_batch_id: Optional[str]
    created_at: datetime


# --- Internal Marks & Moderation Lock Schemas ---
class MarkItemUpdate(BaseModel):
    student_id: int
    midterm_score: float = Field(..., ge=0.0, le=20.0)
    quiz_score: float = Field(..., ge=0.0, le=10.0)
    assignment_score: float = Field(..., ge=0.0, le=10.0)
    change_reason: Optional[str] = None


class BatchMarksUpdate(BaseModel):
    subject_id: int
    marks: List[MarkItemUpdate]


class ModerationLockRequest(BaseModel):
    subject_id: int
    batch_id: int
    action: str = Field(..., pattern="^(SUBMIT|LOCK|UNLOCK)$")
    reason: Optional[str] = None


class ExamAuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    subject_id: int
    actor_username: str
    actor_role: str
    old_total: Optional[float]
    new_total: Optional[float]
    action_type: str
    reason: Optional[str]
    timestamp: datetime


# --- Fee Dues & Mock Payment Schemas ---
class MockPaymentRequest(BaseModel):
    student_id: int
    amount: float = Field(..., gt=0.0)
    payment_mode: str = "UPI_MOCK"  # UPI_MOCK, BANK_COUNTER, NETBANKING
    notes: Optional[str] = "Online Fee Settlement"


class FeeLedgerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    roll_no: str
    student_name: str
    total_fee: float
    scholarship_discount: float
    net_payable: float
    paid_amount: float
    due_amount: float
    status: str
    last_payment_date: Optional[datetime]


# --- AI Assistant & At-Risk Schemas ---
class AIQueryRequest(BaseModel):
    prompt: str


class FilterTrace(BaseModel):
    field: str
    operator: str
    value: Any
    description: str


class AIQueryResponse(BaseModel):
    question: str
    interpretation: str
    generated_filter_summary: str
    filters_applied: List[FilterTrace]
    read_only_sql: str
    row_count: int
    execution_time_ms: float
    results: List[Dict[str, Any]]
    confidence: float
    safety_audit: str = "PASSED (Read-only verified, DPDP role-scoped)"
    suggestions: List[str] = []


class MentorTaskCreate(BaseModel):
    student_id: int
    faculty_id: int
    title: str
    description: str
    recommended_action: str


class MentorTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    student_name: str
    student_roll_no: str
    faculty_id: int
    title: str
    description: str
    recommended_action: str
    status: str
    created_at: datetime


# --- Notification Schemas ---
class NotificationSendRequest(BaseModel):
    student_id: int
    trigger_type: str = Field(default="ATTENDANCE_SHORTAGE", pattern="^(ATTENDANCE_SHORTAGE|FEE_DUE)$")


class NotificationPreviewOut(BaseModel):
    student_id: int
    student_name: str
    roll_no: str
    parent_name: str
    parent_phone: str
    trigger_type: str
    message_text_en: str
    message_text_or: str
