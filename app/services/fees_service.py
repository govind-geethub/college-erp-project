"""
Fee management, mock payment simulation, receipt generation,
and automated Tally XML/CSV export for single-day reconciliation.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import csv
import io
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import StudentFeeLedger, FeePayment, Student, FeeStructure, Programme
from app.schemas import MockPaymentRequest


def get_all_fee_ledgers(db: Session, programme_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve student fee dues and collection statuses."""
    query = db.query(StudentFeeLedger).join(Student)
    if programme_id:
        query = query.filter(Student.programme_id == programme_id)

    ledgers = query.all()
    results = []

    for l in ledgers:
        results.append({
            "ledger_id": l.id,
            "student_id": l.student.id,
            "roll_no": l.student.roll_no,
            "student_name": l.student.name,
            "programme_name": l.student.batch.programme.name if l.student.batch else "B.Tech",
            "year": l.student.current_year,
            "category": l.student.category,
            "total_fee": l.total_fee,
            "scholarship_discount": l.scholarship_discount,
            "net_payable": l.net_payable,
            "paid_amount": l.paid_amount,
            "due_amount": l.due_amount,
            "status": "Paid" if l.due_amount <= 0 else ("Partial" if l.paid_amount > 0 else "Due"),
            "reconciliation_status": l.reconciliation_status,
            "last_payment_date": l.last_payment_date.strftime("%Y-%m-%d") if l.last_payment_date else None
        })

    return results


def process_mock_payment(db: Session, payload: MockPaymentRequest) -> Dict[str, Any]:
    """
    Simulate a payment in test mode (UPI/NetBanking/Bank Counter).
    Instantly generates receipt and reconciles against the student fee ledger.
    """
    ledger = db.query(StudentFeeLedger).filter(StudentFeeLedger.student_id == payload.student_id).first()
    if not ledger:
        raise HTTPException(status_code=404, detail="Student fee ledger not found")

    student = db.query(Student).filter(Student.id == payload.student_id).first()

    if payload.amount > ledger.due_amount:
        # Allow partial or full settlement up to due amount
        # Cap to due amount if paid more
        payment_amount = ledger.due_amount
    else:
        payment_amount = payload.amount

    if payment_amount <= 0:
        raise HTTPException(status_code=400, detail="Fee has already been fully settled (Due is ₹0)")

    receipt_no = f"RCP-2026-{uuid.uuid4().hex[:6].upper()}"
    tx_ref = f"MOCK-TX-{uuid.uuid4().hex[:10].upper()}"
    tally_vch = f"VCH-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"

    now = datetime.now(timezone.utc)

    payment = FeePayment(
        ledger_id=ledger.id,
        student_id=student.id,
        receipt_no=receipt_no,
        amount=payment_amount,
        payment_mode=payload.payment_mode,
        transaction_ref=tx_ref,
        is_reconciled=True,
        tally_voucher_no=tally_vch,
        payment_date=now,
        remarks=payload.notes or "Simulated Fee Payment (Test Mode)"
    )
    db.add(payment)

    # Update ledger balances
    ledger.paid_amount += payment_amount
    ledger.due_amount = max(0.0, ledger.net_payable - ledger.paid_amount)
    ledger.last_payment_date = now
    ledger.status = "Paid" if ledger.due_amount <= 0 else "Partial"
    ledger.reconciliation_status = "Reconciled"

    db.commit()
    db.refresh(payment)

    return {
        "status": "Success",
        "receipt_no": receipt_no,
        "transaction_ref": tx_ref,
        "tally_voucher_no": tally_vch,
        "student_name": student.name,
        "roll_no": student.roll_no,
        "amount_paid": payment_amount,
        "remaining_due": ledger.due_amount,
        "payment_date": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "receipt_url": f"/api/fees/receipt/{receipt_no}"
    }


def generate_tally_xml_export(db: Session) -> str:
    """
    Generate Tally ERP 9 / TallyPrime XML import payload for seamless accounting reconciliation.
    Reduces manual entry from 10 days to 1 day.
    """
    payments = db.query(FeePayment).filter(FeePayment.is_reconciled == True).all()

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<ENVELOPE>',
        '  <HEADER>',
        '    <TALLYREQUEST>Import Data</TALLYREQUEST>',
        '  </HEADER>',
        '  <BODY>',
        '    <IMPORTDATA>',
        '      <REQUESTDESC>',
        '        <REPORTNAME>Vouchers</REPORTNAME>',
        '        <STATICVARIABLES>',
        '          <SVCURRENTCOMPANY>Company A Educational Trust, Bhubaneswar</SVCURRENTCOMPANY>',
        '        </STATICVARIABLES>',
        '      </REQUESTDESC>',
        '      <REQUESTDATA>'
    ]

    for p in payments:
        date_str = p.payment_date.strftime("%Y%m%d")
        xml_lines.extend([
            '        <TALLYMESSAGE xmlns:UDF="TallyUDF">',
            f'          <VOUCHER VCHTYPE="Receipt" ACTION="Create">',
            f'            <DATE>{date_str}</DATE>',
            f'            <NARRATION>Fee Receipt {p.receipt_no} from student ID {p.student_id} via {p.payment_mode}</NARRATION>',
            f'            <VOUCHERNUMBER>{p.receipt_no}</VOUCHERNUMBER>',
            '            <ALLLEDGERENTRIES.LIST>',
            '              <LEDGERNAME>Bank Account / UPI Clearing</LEDGERNAME>',
            '              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>',
            f'              <AMOUNT>-{p.amount:.2f}</AMOUNT>',
            '            </ALLLEDGERENTRIES.LIST>',
            '            <ALLLEDGERENTRIES.LIST>',
            '              <LEDGERNAME>College Tuition & Academic Fee Income</LEDGERNAME>',
            '              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>',
            f'              <AMOUNT>{p.amount:.2f}</AMOUNT>',
            '            </ALLLEDGERENTRIES.LIST>',
            '          </VOUCHER>',
            '        </TALLYMESSAGE>'
        ])

    xml_lines.extend([
        '      </REQUESTDATA>',
        '    </IMPORTDATA>',
        '  </BODY>',
        '</ENVELOPE>'
    ])

    return "\n".join(xml_lines)


def generate_fee_ledger_csv(db: Session) -> str:
    """Generate CSV fee reconciliation export."""
    ledgers = get_all_fee_ledgers(db)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ROLL_NO", "STUDENT_NAME", "PROGRAMME", "YEAR", "CATEGORY",
        "TOTAL_FEE", "SCHOLARSHIP", "NET_PAYABLE", "PAID_AMOUNT",
        "DUE_AMOUNT", "STATUS", "RECONCILIATION_STATUS", "LAST_PAYMENT_DATE"
    ])

    for l in ledgers:
        writer.writerow([
            l["roll_no"],
            l["student_name"],
            l["programme_name"],
            l["year"],
            l["category"],
            f"{l['total_fee']:.2f}",
            f"{l['scholarship_discount']:.2f}",
            f"{l['net_payable']:.2f}",
            f"{l['paid_amount']:.2f}",
            f"{l['due_amount']:.2f}",
            l["status"],
            l["reconciliation_status"],
            l["last_payment_date"] or "N/A"
        ])

    return output.getvalue()
