"""
Tests for Fee Ledgers, Mock Payments, Instant Receipts, and Tally XML Export.
"""

import pytest
from sqlalchemy.orm import Session
from app.models import Student, StudentFeeLedger
from app.schemas import MockPaymentRequest
from app.services import fees_service


def test_ankit_panda_fee_due_matches_brief(db: Session):
    """ENG-24-ME-0177: Ankit Panda must have exactly ₹45,000 fee due as specified in brief."""
    ankit = db.query(Student).filter(Student.roll_no == "ENG-24-ME-0177").first()
    assert ankit is not None
    assert ankit.fee_ledger is not None
    assert ankit.fee_ledger.due_amount == 45000.0


def test_mock_payment_and_receipt(db: Session):
    """Simulating fee payment reduces due amount and issues verified receipt."""
    ankit = db.query(Student).filter(Student.roll_no == "ENG-24-ME-0177").first()
    initial_due = ankit.fee_ledger.due_amount

    payment_payload = MockPaymentRequest(
        student_id=ankit.id,
        amount=15000.0,
        payment_mode="UPI_MOCK",
        notes="Installment 1"
    )
    res = fees_service.process_mock_payment(db, payment_payload)

    assert res["status"] == "Success"
    assert res["receipt_no"].startswith("RCP-2026-")
    assert res["remaining_due"] == initial_due - 15000.0


def test_tally_xml_export_structure(db: Session):
    """Tally XML must include standard TallyPrime / ERP 9 envelopes and vouchers."""
    xml_data = fees_service.generate_tally_xml_export(db)
    assert "<ENVELOPE>" in xml_data
    assert "<TALLYMESSAGE" in xml_data
    assert '<VOUCHER VCHTYPE="Receipt"' in xml_data
    assert "Company A Educational Trust, Bhubaneswar" in xml_data
