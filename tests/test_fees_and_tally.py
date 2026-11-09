"""
Tests for Fee Ledgers, Mock Payments, Instant Receipts, and Tally XML Export.
"""

import pytest
from sqlalchemy.orm import Session
from app.models import Student, StudentFeeLedger
from app.schemas import MockPaymentRequest
from app.services import fees_service
from fastapi.testclient import TestClient
from app.database import get_db
from app.main import app


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


def test_issued_receipt_url_returns_payment_details(db: Session):
    ankit = db.query(Student).filter(Student.roll_no == "ENG-24-ME-0177").one()
    payment = fees_service.process_mock_payment(
        db,
        MockPaymentRequest(student_id=ankit.id, amount=15000.0),
    )

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        receipt_response = client.get(payment["receipt_url"])
        missing_receipt_response = client.get("/api/fees/receipt/UNKNOWN")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert receipt_response.status_code == 200
    receipt = receipt_response.json()
    assert receipt["receipt_no"] == payment["receipt_no"]
    assert receipt["student_id"] == ankit.id
    assert receipt["amount_paid"] == 15000.0
    assert receipt["is_reconciled"] is True
    assert missing_receipt_response.status_code == 404


def test_tally_xml_export_structure(db: Session):
    """Tally XML must include standard TallyPrime / ERP 9 envelopes and vouchers."""
    xml_data = fees_service.generate_tally_xml_export(db)
    assert "<ENVELOPE>" in xml_data
    assert "<TALLYMESSAGE" in xml_data
    assert '<VOUCHER VCHTYPE="Receipt"' in xml_data
    assert "Company A Educational Trust, Bhubaneswar" in xml_data
