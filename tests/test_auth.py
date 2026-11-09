"""
Tests for Authentication, Password Security, JWT Tokens, and Role-Based Access Control.
"""

import pytest
from fastapi import HTTPException
from app.auth import hash_password, verify_password, create_access_token
from app.auth import get_current_user
from app.config import settings
import jwt


def test_password_hashing():
    pwd = "securepassword123"
    h1 = hash_password(pwd)
    h2 = hash_password(pwd)
    assert h1 != h2
    assert h1.startswith("pbkdf2_sha256$")
    assert verify_password(pwd, h1)
    assert not verify_password("wrongpassword", h1)


def test_legacy_password_hashes_remain_verifiable():
    import hashlib

    legacy_hash = hashlib.sha256(
        ("college_erp_salt_2026" + "legacy-password").encode("utf-8")
    ).hexdigest()

    assert verify_password("legacy-password", legacy_hash)
    assert not verify_password("incorrect-password", legacy_hash)
    assert not verify_password("password", "pbkdf2_sha256$999999999$00$00")


def test_jwt_token_generation_and_verification():
    payload = {"sub": "admin", "role": "office_admin", "campus": "BBSR-ENG"}
    token = create_access_token(payload)
    assert isinstance(token, str)

    decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert decoded["sub"] == "admin"
    assert decoded["role"] == "office_admin"
    assert decoded["campus"] == "BBSR-ENG"
    assert "exp" in decoded


def test_missing_credentials_are_rejected_by_default(db, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_AUTH_ENABLED", False)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=None, db=db)

    assert exc_info.value.status_code == 401


def test_demo_auth_is_only_available_outside_production(db, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=None, db=db)

    assert exc_info.value.status_code == 401


def test_explicit_local_demo_auth_resolves_demo_admin(db, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    user = get_current_user(credentials=None, db=db)

    assert user.username == "admin"
