from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models.domain import Patient


def _client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: session
    return TestClient(app), session


def test_create_patient_always_marks_is_new_patient_true():
    client, _session = _client()
    try:
        response = client.post(
            "/patients",
            json={"name": "Walk-in Patient", "age": 30, "sex": "female"},
        )
        assert response.status_code == 200
        assert response.json()["is_new_patient"] is True
    finally:
        app.dependency_overrides.clear()


def test_created_patient_appears_in_patient_list():
    client, _session = _client()
    try:
        created = client.post("/patients", json={"name": "Walk-in Patient", "age": 30, "sex": "female"}).json()

        listed = client.get("/patients").json()

        assert any(p["id"] == created["id"] and p["is_new_patient"] is True for p in listed)
    finally:
        app.dependency_overrides.clear()


def test_evaluation_fixture_is_hidden_from_patient_list_but_remains_addressable():
    client, session = _client()
    try:
        patient = Patient(
            name="Synthetic Eval Patient",
            age=40,
            sex="unspecified",
            chronic_conditions=[],
            general_conditions=[],
            medications=[],
            allergies=[],
            previous_visits=[],
        )
        session.add(patient)
        session.commit()

        listed = client.get("/patients")
        direct = client.get(f"/patients/{patient.id}")

        assert listed.status_code == 200
        assert all(item["id"] != patient.id for item in listed.json())
        assert direct.status_code == 200
        assert direct.json()["id"] == patient.id
    finally:
        app.dependency_overrides.clear()
