"""Tests for parent notification API dispatch and logging."""

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import NotificationLog, Student


def test_parent_alert_json_request_is_recorded(db):
    student = db.query(Student).filter(Student.roll_no == "ENG-24-ME-0177").first()
    assert student is not None

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).post(
            "/api/notifications/send",
            json={"student_id": student.id, "trigger_type": "ATTENDANCE_SHORTAGE"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "Success"
    assert result["channel"] == "SMS"
    assert "Ankit Panda" in result["message_en"]
    assert "ଉପସ୍ଥିତି" in result["message_or"]

    log = db.query(NotificationLog).filter_by(id=result["notification_id"]).one()
    assert log.student_id == student.id
    assert log.status == "Sent_Mock"
    assert log.recipient_phone == student.parent_phone


def test_parent_alert_rejects_unsupported_trigger(db):
    student = db.query(Student).filter(Student.roll_no == "ENG-24-ME-0177").first()
    assert student is not None
    existing_log_count = db.query(NotificationLog).count()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).post(
            "/api/notifications/send",
            json={"student_id": student.id, "trigger_type": "UNSUPPORTED"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 422
    assert db.query(NotificationLog).count() == existing_log_count
