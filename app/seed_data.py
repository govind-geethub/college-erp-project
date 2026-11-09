"""
Seed database with realistic initial data for Company A Educational Trust (Bhubaneswar).
Explicitly includes the required benchmark sample records from the brief:
- ENG-24-CSE-0412: Subhashree Mohanty (B.Tech CSE, Year 2, Att: 81.5%, Marks: 33/40, Fee: ₹0)
- ENG-24-ME-0177:  Ankit Panda (B.Tech ME, Year 2, Att: 68.2%, Marks: 21/40, Fee: ₹45,000)
- MBA-25-0093:     Farheen Ali (MBA, Year 1, Att: 92.0%, Marks: 36/40, Fee: ₹0)
"""

from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.auth import hash_password
from app.models import (
    User, Campus, Programme, Batch, Subject, Faculty, FacultySubjectMapping,
    Student, AttendanceSession, AttendanceRecord, InternalMark, ExamAuditLog,
    FeeStructure, StudentFeeLedger, FeePayment, AtRiskFlag, MentorTask,
    NotificationLog, DPDPAuditLog
)


def historical_class_dates(today: date, count: int, start_offset: int) -> list[date]:
    """Return unique weekday dates well before the recent attendance sessions."""
    dates = []
    offset = start_offset
    while len(dates) < count:
        session_date = today - timedelta(days=offset)
        if session_date.weekday() != 6:
            dates.append(session_date)
        offset += 1
    return dates


def seed_database(db: Session):
    """Populate database with complete multi-campus college ERP seed data."""
    # Check if already seeded
    if db.query(Campus).first():
        return

    print("Seeding College ERP database...")

    # 1. Users
    admin_user = User(
        username="admin",
        password_hash=hash_password(settings.DEMO_ADMIN_PASSWORD),
        full_name="Pradeep Kumar Das",
        email="pdas.admin@trust-erp.ac.in",
        role="office_admin",
        campus_code="BBSR-ENG",
        department="Administrative Office"
    )
    faculty_user = User(
        username="faculty",
        password_hash=hash_password(settings.DEMO_FACULTY_PASSWORD),
        full_name="Dr. Ramesh Chandra Patra",
        email="rcpatra.cse@trust-erp.ac.in",
        role="faculty",
        campus_code="BBSR-ENG",
        department="CSE"
    )
    moderator_user = User(
        username="moderator",
        password_hash=hash_password(settings.DEMO_MODERATOR_PASSWORD),
        full_name="Prof. Minati Mishra",
        email="mmishra.exam@trust-erp.ac.in",
        role="exam_moderator",
        campus_code="BBSR-ENG",
        department="Examination Cell"
    )
    db.add_all([admin_user, faculty_user, moderator_user])
    db.flush()

    # 2. Campus
    campus = Campus(
        code="BBSR-ENG",
        name="Bhubaneswar Engineering College (Campus 1)",
        trust_name="Company A Educational Trust, Bhubaneswar",
        city="Bhubaneswar",
        state="Odisha"
    )
    db.add(campus)
    db.flush()

    # 3. Programmes
    prog_cse = Programme(
        campus_id=campus.id,
        code="BTECH-CSE",
        name="B.Tech Computer Science & Engineering",
        degree_type="Undergraduate",
        duration_years=4,
        annual_tuition=120000.0
    )
    prog_me = Programme(
        campus_id=campus.id,
        code="BTECH-ME",
        name="B.Tech Mechanical Engineering",
        degree_type="Undergraduate",
        duration_years=4,
        annual_tuition=110000.0
    )
    prog_mba = Programme(
        campus_id=campus.id,
        code="MBA",
        name="Master of Business Administration",
        degree_type="Postgraduate",
        duration_years=2,
        annual_tuition=130000.0
    )
    db.add_all([prog_cse, prog_me, prog_mba])
    db.flush()

    # 4. Batches
    batch_cse_y2 = Batch(
        programme_id=prog_cse.id,
        name="2024-2028",
        academic_year=2,
        current_semester=3,
        section="A"
    )
    batch_me_y2 = Batch(
        programme_id=prog_me.id,
        name="2024-2028",
        academic_year=2,
        current_semester=3,
        section="A"
    )
    batch_mba_y1 = Batch(
        programme_id=prog_mba.id,
        name="2025-2027",
        academic_year=1,
        current_semester=1,
        section="A"
    )
    db.add_all([batch_cse_y2, batch_me_y2, batch_mba_y1])
    db.flush()

    # 5. Subjects
    subj_dsa = Subject(
        programme_id=prog_cse.id,
        semester=3,
        code="CS301",
        name="Data Structures & Algorithms",
        credits=4,
        max_internal_marks=40.0
    )
    subj_coa = Subject(
        programme_id=prog_cse.id,
        semester=3,
        code="CS302",
        name="Computer Organization & Architecture",
        credits=4,
        max_internal_marks=40.0
    )
    subj_fm = Subject(
        programme_id=prog_me.id,
        semester=3,
        code="ME301",
        name="Fluid Mechanics",
        credits=4,
        max_internal_marks=40.0
    )
    subj_mba_eco = Subject(
        programme_id=prog_mba.id,
        semester=1,
        code="MBA101",
        name="Managerial Economics",
        credits=4,
        max_internal_marks=40.0
    )
    db.add_all([subj_dsa, subj_coa, subj_fm, subj_mba_eco])
    db.flush()

    # 6. Faculty
    faculty_ramesh = Faculty(
        user_id=faculty_user.id,
        employee_code="EMP-FAC-0101",
        name="Dr. Ramesh Chandra Patra",
        department="CSE",
        designation="Associate Professor",
        email="rcpatra.cse@trust-erp.ac.in",
        phone="+91-9437012345"
    )
    faculty_sahoo = Faculty(
        employee_code="EMP-FAC-0205",
        name="Dr. Bijay Kumar Sahoo",
        department="Mechanical",
        designation="Professor & HOD",
        email="bksahoo.me@trust-erp.ac.in",
        phone="+91-9437023456"
    )
    faculty_priya = Faculty(
        employee_code="EMP-FAC-0312",
        name="Dr. Priya Mohapatra",
        department="MBA",
        designation="Associate Professor",
        email="pmohapatra.mba@trust-erp.ac.in",
        phone="+91-9437034567"
    )
    db.add_all([faculty_ramesh, faculty_sahoo, faculty_priya])
    db.flush()

    # Faculty Mappings
    mapping1 = FacultySubjectMapping(
        faculty_id=faculty_ramesh.id,
        subject_id=subj_dsa.id,
        batch_id=batch_cse_y2.id
    )
    mapping2 = FacultySubjectMapping(
        faculty_id=faculty_sahoo.id,
        subject_id=subj_fm.id,
        batch_id=batch_me_y2.id
    )
    mapping3 = FacultySubjectMapping(
        faculty_id=faculty_priya.id,
        subject_id=subj_mba_eco.id,
        batch_id=batch_mba_y1.id
    )
    db.add_all([mapping1, mapping2, mapping3])
    db.flush()

    # 7. Fee Structures
    fee_btech_gen = FeeStructure(
        programme_id=prog_cse.id,
        academic_year=2,
        category="General",
        tuition_fee=95000.0,
        exam_fee=5000.0,
        lab_fee=15000.0,
        library_fee=5000.0,
        total_fee=120000.0
    )
    fee_btech_tfw = FeeStructure(
        programme_id=prog_cse.id,
        academic_year=2,
        category="TFW",
        tuition_fee=0.0,
        exam_fee=5000.0,
        lab_fee=15000.0,
        library_fee=5000.0,
        total_fee=25000.0
    )
    fee_me_gen = FeeStructure(
        programme_id=prog_me.id,
        academic_year=2,
        category="General",
        tuition_fee=85000.0,
        exam_fee=5000.0,
        lab_fee=15000.0,
        library_fee=5000.0,
        total_fee=110000.0
    )
    fee_mba_gen = FeeStructure(
        programme_id=prog_mba.id,
        academic_year=1,
        category="General",
        tuition_fee=105000.0,
        exam_fee=5000.0,
        lab_fee=10000.0,
        library_fee=10000.0,
        total_fee=130000.0
    )
    db.add_all([fee_btech_gen, fee_btech_tfw, fee_me_gen, fee_mba_gen])
    db.flush()

    # 8. Students (Including the 3 specific requirements from Screenshot 2)
    # Student 1: Subhashree Mohanty
    s1 = Student(
        roll_no="ENG-24-CSE-0412",
        name="Subhashree Mohanty",
        email="subhashree.mohanty@student.trust-erp.ac.in",
        phone="+91-9861011111",
        parent_name="Rabinarayan Mohanty",
        parent_phone="+91-9437111111",
        parent_email="rn.mohanty@gmail.com",
        programme_id=prog_cse.id,
        batch_id=batch_cse_y2.id,
        current_year=2,
        current_semester=3,
        category="General",
        is_minor=False,
        dpdp_consent_status="Granted"
    )

    # Student 2: Ankit Panda (Under 75% attendance -> 68.2%, Marks 21/40, Due: ₹45,000)
    s2 = Student(
        roll_no="ENG-24-ME-0177",
        name="Ankit Panda",
        email="ankit.panda@student.trust-erp.ac.in",
        phone="+91-9861022222",
        parent_name="Bichitrananda Panda",
        parent_phone="+91-9437222222",
        parent_email="bn.panda@gmail.com",
        programme_id=prog_me.id,
        batch_id=batch_me_y2.id,
        current_year=2,
        current_semester=3,
        category="General",
        is_minor=False,
        dpdp_consent_status="Granted"
    )

    # Student 3: Farheen Ali (MBA Year 1, Att: 92.0%, Marks: 36/40, Due: ₹0)
    s3 = Student(
        roll_no="MBA-25-0093",
        name="Farheen Ali",
        email="farheen.ali@student.trust-erp.ac.in",
        phone="+91-9861033333",
        parent_name="Mirza Farooq Ali",
        parent_phone="+91-9437333333",
        parent_email="farooq.ali@gmail.com",
        programme_id=prog_mba.id,
        batch_id=batch_mba_y1.id,
        current_year=1,
        current_semester=1,
        category="General",
        is_minor=False,
        dpdp_consent_status="Granted"
    )

    # Student 4: Minor first-year student needing DPDP parental consent verification
    s4 = Student(
        roll_no="ENG-24-CSE-0415",
        name="Siddharth Tripathy",
        email="siddharth.t@student.trust-erp.ac.in",
        phone="+91-9861044444",
        parent_name="Sanjay Tripathy",
        parent_phone="+91-9437444444",
        parent_email="sanjay.tripathy@yahoo.com",
        programme_id=prog_cse.id,
        batch_id=batch_cse_y2.id,
        current_year=2,
        current_semester=3,
        category="General",
        is_minor=True,  # DPDP Act 2023 minor
        dpdp_consent_status="Granted"
    )

    # Student 5: TFW Scholarship student in CSE
    s5 = Student(
        roll_no="ENG-24-CSE-0418",
        name="Deepak Kumar Nayak",
        email="deepak.nayak@student.trust-erp.ac.in",
        phone="+91-9861055555",
        parent_name="Manoj Nayak",
        parent_phone="+91-9437555555",
        parent_email="manoj.nayak@gmail.com",
        programme_id=prog_cse.id,
        batch_id=batch_cse_y2.id,
        current_year=2,
        current_semester=3,
        category="TFW",
        is_minor=False,
        dpdp_consent_status="Granted"
    )

    # Student 6: Pratyush Rout (Another student in CSE with borderline attendance)
    s6 = Student(
        roll_no="ENG-24-CSE-0422",
        name="Pratyush Rout",
        email="pratyush.rout@student.trust-erp.ac.in",
        phone="+91-9861066666",
        parent_name="Prasant Rout",
        parent_phone="+91-9437666666",
        parent_email="prasant.rout@gmail.com",
        programme_id=prog_cse.id,
        batch_id=batch_cse_y2.id,
        current_year=2,
        current_semester=3,
        category="General",
        is_minor=False,
        dpdp_consent_status="Granted"
    )

    # Student 7: Ipsita Behera (High performer CSE)
    s7 = Student(
        roll_no="ENG-24-CSE-0425",
        name="Ipsita Behera",
        email="ipsita.behera@student.trust-erp.ac.in",
        phone="+91-9861077777",
        parent_name="Ashok Behera",
        parent_phone="+91-9437777777",
        parent_email="ashok.behera@rediffmail.com",
        programme_id=prog_cse.id,
        batch_id=batch_cse_y2.id,
        current_year=2,
        current_semester=3,
        category="General",
        is_minor=False,
        dpdp_consent_status="Granted"
    )

    db.add_all([s1, s2, s3, s4, s5, s6, s7])
    db.flush()

    # 9. Fee Ledgers & Payments
    # Subhashree: Paid full ₹120,000, due ₹0
    fl1 = StudentFeeLedger(
        student_id=s1.id,
        total_fee=120000.0,
        scholarship_discount=0.0,
        net_payable=120000.0,
        paid_amount=120000.0,
        due_amount=0.0,
        status="Paid",
        reconciliation_status="Reconciled",
        last_payment_date=datetime.now(timezone.utc) - timedelta(days=20)
    )
    p1 = FeePayment(
        ledger=fl1,
        student_id=s1.id,
        receipt_no="RCP-2026-00812",
        amount=120000.0,
        payment_mode="BANK_COUNTER",
        transaction_ref="SBI-NEFT-991823101",
        is_reconciled=True,
        tally_voucher_no="VCH-TALLY-2026-441"
    )

    # Ankit Panda: Total ₹110,000, paid ₹65,000, DUE ₹45,000 (Matches brief!)
    fl2 = StudentFeeLedger(
        student_id=s2.id,
        total_fee=110000.0,
        scholarship_discount=0.0,
        net_payable=110000.0,
        paid_amount=65000.0,
        due_amount=45000.0,
        status="Partial",
        reconciliation_status="Reconciled",
        last_payment_date=datetime.now(timezone.utc) - timedelta(days=45)
    )
    p2 = FeePayment(
        ledger=fl2,
        student_id=s2.id,
        receipt_no="RCP-2026-00419",
        amount=65000.0,
        payment_mode="UPI_MOCK",
        transaction_ref="UPI-ID-78192038102",
        is_reconciled=True,
        tally_voucher_no="VCH-TALLY-2026-198"
    )

    # Farheen Ali: Paid full ₹130,000, due ₹0 (Matches brief!)
    fl3 = StudentFeeLedger(
        student_id=s3.id,
        total_fee=130000.0,
        scholarship_discount=0.0,
        net_payable=130000.0,
        paid_amount=130000.0,
        due_amount=0.0,
        status="Paid",
        reconciliation_status="Reconciled",
        last_payment_date=datetime.now(timezone.utc) - timedelta(days=15)
    )
    p3 = FeePayment(
        ledger=fl3,
        student_id=s3.id,
        receipt_no="RCP-2026-00904",
        amount=130000.0,
        payment_mode="NETBANKING_MOCK",
        transaction_ref="HDFC-PAY-882190123",
        is_reconciled=True,
        tally_voucher_no="VCH-TALLY-2026-502"
    )

    # Siddharth Tripathy: Paid full ₹120,000
    fl4 = StudentFeeLedger(
        student_id=s4.id,
        total_fee=120000.0,
        scholarship_discount=0.0,
        net_payable=120000.0,
        paid_amount=120000.0,
        due_amount=0.0,
        status="Paid",
        reconciliation_status="Reconciled",
        last_payment_date=datetime.now(timezone.utc) - timedelta(days=22)
    )

    # Deepak Nayak: TFW category -> Total ₹25,000, paid ₹25,000
    fl5 = StudentFeeLedger(
        student_id=s5.id,
        total_fee=120000.0,
        scholarship_discount=95000.0,  # Tuition fee waived
        net_payable=25000.0,
        paid_amount=25000.0,
        due_amount=0.0,
        status="Paid",
        reconciliation_status="Reconciled",
        last_payment_date=datetime.now(timezone.utc) - timedelta(days=18)
    )

    # Pratyush Rout: Partial due ₹20,000
    fl6 = StudentFeeLedger(
        student_id=s6.id,
        total_fee=120000.0,
        scholarship_discount=0.0,
        net_payable=120000.0,
        paid_amount=100000.0,
        due_amount=20000.0,
        status="Partial",
        reconciliation_status="Reconciled",
        last_payment_date=datetime.now(timezone.utc) - timedelta(days=35)
    )

    # Ipsita Behera: Paid full ₹120,000
    fl7 = StudentFeeLedger(
        student_id=s7.id,
        total_fee=120000.0,
        scholarship_discount=0.0,
        net_payable=120000.0,
        paid_amount=120000.0,
        due_amount=0.0,
        status="Paid",
        reconciliation_status="Reconciled",
        last_payment_date=datetime.now(timezone.utc) - timedelta(days=12)
    )

    db.add_all([fl1, fl2, fl3, fl4, fl5, fl6, fl7, p1, p2, p3])
    db.flush()

    # 10. Internal Marks (40 marks component breakdown)
    # Component breakdown: Midterm (max 20), Quiz (max 10), Assignment (max 10) = 40 total
    # Subhashree: 33/40 (17 + 8 + 8)
    m1 = InternalMark(
        student_id=s1.id,
        subject_id=subj_dsa.id,
        midterm_score=17.0,
        quiz_score=8.0,
        assignment_score=8.0,
        total_score=33.0,
        moderation_status="Moderated_Locked",
        is_locked=True,
        locked_by="Prof. Minati Mishra",
        locked_at=datetime.now(timezone.utc) - timedelta(days=5)
    )

    # Ankit Panda: 21/40 (10 + 5 + 6)
    m2 = InternalMark(
        student_id=s2.id,
        subject_id=subj_fm.id,
        midterm_score=10.0,
        quiz_score=5.0,
        assignment_score=6.0,
        total_score=21.0,
        moderation_status="Submitted",
        is_locked=False
    )

    # Farheen Ali: 36/40 (18 + 9 + 9)
    m3 = InternalMark(
        student_id=s3.id,
        subject_id=subj_mba_eco.id,
        midterm_score=18.0,
        quiz_score=9.0,
        assignment_score=9.0,
        total_score=36.0,
        moderation_status="Moderated_Locked",
        is_locked=True,
        locked_by="Prof. Minati Mishra",
        locked_at=datetime.now(timezone.utc) - timedelta(days=5)
    )

    # Siddharth Tripathy: 35/40
    m4 = InternalMark(
        student_id=s4.id,
        subject_id=subj_dsa.id,
        midterm_score=18.0,
        quiz_score=9.0,
        assignment_score=8.0,
        total_score=35.0,
        moderation_status="Moderated_Locked",
        is_locked=True,
        locked_by="Prof. Minati Mishra",
        locked_at=datetime.now(timezone.utc) - timedelta(days=5)
    )

    # Deepak Nayak: 30/40
    m5 = InternalMark(
        student_id=s5.id,
        subject_id=subj_dsa.id,
        midterm_score=15.0,
        quiz_score=8.0,
        assignment_score=7.0,
        total_score=30.0,
        moderation_status="Moderated_Locked",
        is_locked=True,
        locked_by="Prof. Minati Mishra",
        locked_at=datetime.now(timezone.utc) - timedelta(days=5)
    )

    # Pratyush Rout: 22/40 (Near threshold)
    m6 = InternalMark(
        student_id=s6.id,
        subject_id=subj_dsa.id,
        midterm_score=11.0,
        quiz_score=5.0,
        assignment_score=6.0,
        total_score=22.0,
        moderation_status="Submitted",
        is_locked=False
    )

    # Ipsita Behera: 38/40 (Top ranker)
    m7 = InternalMark(
        student_id=s7.id,
        subject_id=subj_dsa.id,
        midterm_score=19.0,
        quiz_score=10.0,
        assignment_score=9.0,
        total_score=38.0,
        moderation_status="Moderated_Locked",
        is_locked=True,
        locked_by="Prof. Minati Mishra",
        locked_at=datetime.now(timezone.utc) - timedelta(days=5)
    )

    db.add_all([m1, m2, m3, m4, m5, m6, m7])
    db.flush()

    # 11. Exam Audit Trail (Demonstrates NAAC & Exam Audit Compliance)
    audit1 = ExamAuditLog(
        student_id=s1.id,
        subject_id=subj_dsa.id,
        actor_username="faculty",
        actor_role="faculty",
        old_midterm=16.0,
        new_midterm=17.0,
        old_quiz=8.0,
        new_quiz=8.0,
        old_assignment=8.0,
        new_assignment=8.0,
        old_total=32.0,
        new_total=33.0,
        action_type="UPDATE",
        reason="Re-evaluation of Question 3.b per student representation",
        timestamp=datetime.now(timezone.utc) - timedelta(days=7)
    )
    audit2 = ExamAuditLog(
        student_id=s1.id,
        subject_id=subj_dsa.id,
        actor_username="moderator",
        actor_role="exam_moderator",
        old_total=33.0,
        new_total=33.0,
        action_type="MODERATION_LOCK",
        reason="Final Semester 3 internal marks moderated and verified by Department Academic Committee",
        timestamp=datetime.now(timezone.utc) - timedelta(days=5)
    )
    db.add_all([audit1, audit2])
    db.flush()

    # 12. Attendance Sessions & Records
    # To achieve exact percentages:
    # Subhashree Mohanty: 81.5% -> 88 attended out of 108 classes
    # Ankit Panda: 68.2% -> 73 attended out of 107 classes
    # Farheen Ali: 92.0% -> 92 attended out of 100 classes
    # Let's seed realistic recent sessions for CSE Batch (DSA course)
    today = date.today()
    cse_students = [s1, s4, s5, s6, s7]

    for day_offset in range(12, 0, -1):
        sess_date = today - timedelta(days=day_offset)
        # Skip Sundays
        if sess_date.weekday() == 6:
            continue
        
        session = AttendanceSession(
            subject_id=subj_dsa.id,
            batch_id=batch_cse_y2.id,
            faculty_id=faculty_ramesh.id,
            session_date=sess_date,
            created_at=datetime.combine(sess_date, datetime.min.time(), tzinfo=timezone.utc),
            period=1,
            total_students=len(cse_students),
            sync_status="Synced",
            client_batch_id=f"SYNC-DSA-{sess_date.strftime('%Y%m%d')}-P1"
        )
        db.add(session)
        db.flush()

        present_count = 0
        absent_count = 0
        for stud in cse_students:
            # Deterministic status for target percentages
            if stud.id == s1.id:
                # Subhashree misses ~1 in 5
                status = "Present" if day_offset not in [4, 9] else "Absent"
            elif stud.id == s6.id:
                # Pratyush misses frequently
                status = "Present" if day_offset not in [2, 5, 8, 11] else "Absent"
            else:
                status = "Present"

            if status == "Present":
                present_count += 1
            else:
                absent_count += 1

            record = AttendanceRecord(
                session_id=session.id,
                student_id=stud.id,
                status=status
            )
            db.add(record)

        session.present_count = present_count
        session.absent_count = absent_count

    for class_index, sess_date in enumerate(historical_class_dates(today, 98, 500)):
        session = AttendanceSession(
            subject_id=subj_dsa.id,
            batch_id=batch_cse_y2.id,
            faculty_id=faculty_ramesh.id,
            session_date=sess_date,
            created_at=datetime.combine(sess_date, datetime.min.time(), tzinfo=timezone.utc),
            period=1,
            total_students=len(cse_students),
            present_count=0,
            absent_count=0,
            sync_status="Synced",
            client_batch_id=f"HIST-DSA-{class_index + 1:03d}"
        )
        db.add(session)
        db.flush()

        present_count = 0
        absent_count = 0
        for stud in cse_students:
            if stud.id == s1.id:
                status = "Present" if class_index < 80 else "Absent"
            elif stud.id == s6.id:
                status = "Present" if class_index < 69 else "Absent"
            else:
                status = "Present"
            db.add(AttendanceRecord(session_id=session.id, student_id=stud.id, status=status))
            if status == "Present":
                present_count += 1
            else:
                absent_count += 1

        session.present_count = present_count
        session.absent_count = absent_count
    
    # Also add sessions for Mechanical (Ankit Panda)
    for day_offset in range(12, 0, -1):
        sess_date = today - timedelta(days=day_offset)
        if sess_date.weekday() == 6:
            continue
        sess_me = AttendanceSession(
            subject_id=subj_fm.id,
            batch_id=batch_me_y2.id,
            faculty_id=faculty_sahoo.id,
            session_date=sess_date,
            created_at=datetime.combine(sess_date, datetime.min.time(), tzinfo=timezone.utc),
            period=2,
            total_students=1,
            present_count=1 if day_offset not in [1, 3, 6, 9] else 0,
            absent_count=0 if day_offset not in [1, 3, 6, 9] else 1,
            sync_status="Synced",
            client_batch_id=f"SYNC-FM-{sess_date.strftime('%Y%m%d')}-P2"
        )
        db.add(sess_me)
        db.flush()
        rec_me = AttendanceRecord(
            session_id=sess_me.id,
            student_id=s2.id,
            status="Present" if day_offset not in [1, 3, 6, 9] else "Absent"
        )
        db.add(rec_me)

    for class_index, sess_date in enumerate(historical_class_dates(today, 97, 700)):
        is_present = class_index < 66
        session = AttendanceSession(
            subject_id=subj_fm.id,
            batch_id=batch_me_y2.id,
            faculty_id=faculty_sahoo.id,
            session_date=sess_date,
            created_at=datetime.combine(sess_date, datetime.min.time(), tzinfo=timezone.utc),
            period=2,
            total_students=1,
            present_count=1 if is_present else 0,
            absent_count=0 if is_present else 1,
            sync_status="Synced",
            client_batch_id=f"HIST-FM-{class_index + 1:03d}"
        )
        db.add(session)
        db.flush()
        db.add(AttendanceRecord(
            session_id=session.id,
            student_id=s2.id,
            status="Present" if is_present else "Absent"
        ))

    for class_index, sess_date in enumerate(historical_class_dates(today, 100, 900)):
        is_present = class_index < 92
        session = AttendanceSession(
            subject_id=subj_mba_eco.id,
            batch_id=batch_mba_y1.id,
            faculty_id=faculty_priya.id,
            session_date=sess_date,
            created_at=datetime.combine(sess_date, datetime.min.time(), tzinfo=timezone.utc),
            period=3,
            total_students=1,
            present_count=1 if is_present else 0,
            absent_count=0 if is_present else 1,
            sync_status="Synced",
            client_batch_id=f"HIST-MBA-{class_index + 1:03d}"
        )
        db.add(session)
        db.flush()
        db.add(AttendanceRecord(
            session_id=session.id,
            student_id=s3.id,
            status="Present" if is_present else "Absent"
        ))

    # 13. At-Risk Flag & Mentor Task for Ankit Panda (Screen 2 & 6 requirements)
    risk_flag_ankit = AtRiskFlag(
        student_id=s2.id,
        risk_level="HIGH",
        risk_score=82.5,
        triggers='["Attendance 68.2% is below mandatory 75% limit", "Internal mark 21/40 is below department threshold of 24/40", "Fee arrears: ₹45,000 outstanding for >45 days"]',
        attendance_pct=68.2,
        internal_marks=21.0,
        fee_due=45000.0,
        status="TASK_CREATED"
    )
    db.add(risk_flag_ankit)
    db.flush()

    mentor_task_ankit = MentorTask(
        risk_flag_id=risk_flag_ankit.id,
        student_id=s2.id,
        faculty_id=faculty_sahoo.id,
        title="Urgent Academic & Attendance Counseling: Ankit Panda",
        description="Student has breached minimum 75% attendance rule (current: 68.2%) and scored 21/40 in Fluid Mechanics midterm. Mentor must schedule personal counseling session and recommend remedial classes.",
        recommended_action="1. Issue shortage notice. 2. Schedule parent-teacher meet. 3. Enroll in remedial tutorial.",
        status="Pending"
    )
    db.add(mentor_task_ankit)

    # Also at-risk flag for Pratyush Rout (Medium risk)
    risk_flag_pratyush = AtRiskFlag(
        student_id=s6.id,
        risk_level="MEDIUM",
        risk_score=58.0,
        triggers='["Attendance 72.5% trending towards shortage", "Internal mark 22/40 in DSA", "Fee balance ₹20,000 pending"]',
        attendance_pct=72.5,
        internal_marks=22.0,
        fee_due=20000.0,
        status="TASK_CREATED"
    )
    db.add(risk_flag_pratyush)
    db.flush()

    mentor_task_pratyush = MentorTask(
        risk_flag_id=risk_flag_pratyush.id,
        student_id=s6.id,
        faculty_id=faculty_ramesh.id,
        title="Attendance Warning & Mentoring: Pratyush Rout",
        description="Student attendance is 72.5% in Data Structures. Issue warning and review lab submission backlog.",
        recommended_action="Review assignment submissions and monitor next 5 lecture attendances.",
        status="In_Progress"
    )
    db.add(mentor_task_pratyush)

    # 14. Notifications in English and Odia (Bilingual requirement)
    notice_odia_ankit = NotificationLog(
        student_id=s2.id,
        recipient_type="Parent",
        recipient_phone="+91-9437222222",
        channel="SMS",
        message_text_en="ALERT: Your ward Ankit Panda (ENG-24-ME-0177) has 68.2% attendance in Semester 3, below the required 75.0% threshold. Immediate counseling is required. Outstanding fees: ₹45,000. Contact: 0674-2391000.",
        message_text_or="ସତର୍କତା: ଆପଣଙ୍କ ପିଲା ଅଙ୍କିତ ପଣ୍ଡା (ENG-24-ME-0177) ଙ୍କ ତୃତୀୟ ସେମିଷ୍ଟାରରେ ଉପସ୍ଥିତି ୬୮.୨% ଅଛି, ଯାହା ନିୟମିତ ୭୫% ରୁ କମ। ଦୟାକରି ତୁରନ୍ତ ବିଭାଗୀୟ ମେଣ୍ଟରଙ୍କ ସହିତ ଯୋଗାଯୋଗ କରନ୍ତୁ। ବାକି ଫି: ₹୪୫,୦୦୦। ଫୋନ: ୦୬୭୪-୨୩୯୧୦୦୦।",
        trigger_type="ATTENDANCE_SHORTAGE",
        status="Sent_Mock"
    )
    db.add(notice_odia_ankit)

    # 15. DPDP Minor Consent Audit Log
    dpdp_log = DPDPAuditLog(
        actor_username="admin",
        student_id=s4.id,
        action="CONSENT_VERIFY",
        is_minor=True,
        access_purpose="DPDP Act 2023 Parental Consent Form verified with guardian Aadhaar linkage"
    )
    db.add(dpdp_log)

    db.commit()
    print("Database successfully seeded with benchmark data!")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session)
