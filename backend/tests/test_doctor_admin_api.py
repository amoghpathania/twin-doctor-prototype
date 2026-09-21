from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models.domain import Doctor


def _client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: session
    return TestClient(app), session


def test_create_doctor_always_starts_in_shadow_mode():
    client, _session = _client()
    try:
        response = client.post(
            "/doctors",
            json={
                "name": "Dr. New Doctor",
                "specialty": "Pediatrics",
                "experience": "5 years",
                "communication_style": "Warm",
                "clinical_preferences": "Ask about growth milestones",
                "escalation_preferences": "Escalate fevers over 3 days",
            },
        )
        assert response.status_code == 200
        assert response.json()["default_deployment_mode"] == "SHADOW"
    finally:
        app.dependency_overrides.clear()


def test_update_doctor_mode_persists():
    client, _session = _client()
    try:
        doctor = client.post(
            "/doctors",
            json={
                "name": "Dr. New Doctor",
                "specialty": "Pediatrics",
                "experience": "5 years",
                "communication_style": "Warm",
                "clinical_preferences": "Ask about growth milestones",
                "escalation_preferences": "Escalate fevers over 3 days",
            },
        ).json()

        response = client.post(f"/doctors/{doctor['id']}/mode", json={"deployment_mode": "COPILOT"})
        assert response.status_code == 200
        assert response.json()["default_deployment_mode"] == "COPILOT"

        fetched = client.get(f"/doctors/{doctor['id']}")
        assert fetched.json()["default_deployment_mode"] == "COPILOT"
    finally:
        app.dependency_overrides.clear()


def test_update_mode_for_nonexistent_doctor_returns_404():
    client, _session = _client()
    try:
        response = client.post("/doctors/999999/mode", json={"deployment_mode": "AUTONOMOUS"})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_evaluation_fixture_is_hidden_from_doctor_list_but_remains_addressable():
    client, session = _client()
    try:
        doctor = Doctor(
            name="Dr. Sarah Lim (Eval)",
            specialty="General Medicine",
            experience="10 years",
            communication_style="Concise",
            clinical_preferences="Structured questions",
            escalation_preferences="Escalate worsening symptoms",
        )
        session.add(doctor)
        session.commit()

        listed = client.get("/doctors")
        direct = client.get(f"/doctors/{doctor.id}")

        assert listed.status_code == 200
        assert all(item["id"] != doctor.id for item in listed.json())
        assert direct.status_code == 200
        assert direct.json()["id"] == doctor.id
    finally:
        app.dependency_overrides.clear()
