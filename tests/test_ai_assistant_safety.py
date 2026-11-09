"""
Tests for Plain-English AI Query Assistant, Safety Guardrails, and Read-Only Scoping.
"""

import pytest
from sqlalchemy.orm import Session
from app.models import User
from app.services import ai_assistant


def test_plain_english_query_attendance_shortage(db: Session):
    admin = db.query(User).filter(User.username == "admin").first()
    res = ai_assistant.process_natural_language_query(
        db,
        "how many second-year students are below 75% this month?",
        admin
    )
    assert res["confidence"] > 0.8
    assert res["safety_audit"].startswith("PASSED")
    assert "SELECT" in res["read_only_sql"]
    assert len(res["filters_applied"]) >= 2
    # Should catch Ankit Panda
    roll_numbers = [r["roll_no"] for r in res["results"]]
    assert "ENG-24-ME-0177" in roll_numbers


def test_plain_english_query_fee_dues(db: Session):
    admin = db.query(User).filter(User.username == "admin").first()
    res = ai_assistant.process_natural_language_query(
        db,
        "show students with fee dues above 30000",
        admin
    )
    assert res["confidence"] > 0.8
    assert len(res["results"]) >= 1
    for r in res["results"]:
        assert r["fee_due_inr"] > 30000.0


def test_safety_guardrail_blocks_mutation(db: Session):
    """Any mutation attempt (DELETE, UPDATE, DROP) must be strictly blocked with zero DB impact."""
    admin = db.query(User).filter(User.username == "admin").first()
    res = ai_assistant.process_natural_language_query(
        db,
        "DELETE FROM students WHERE id = 1",
        admin
    )
    assert "BLOCKED" in res["safety_audit"]
    assert res["row_count"] == 0
    assert len(res["results"]) == 0
