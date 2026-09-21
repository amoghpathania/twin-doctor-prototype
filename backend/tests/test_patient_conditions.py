from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agents.prompts import build_prompt
from app.db import Base, get_db
from app.main import app
from app.models.domain import Patient
from app.repositories.patient_repository import PatientRepository


def _client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: session
    return TestClient(app), session


def test_add_condition_appends_without_dropping_existing_entries(db_session):
    patient = PatientRepository(db_session).add(
        Patient(
            name="Tan Wei Ming",
            age=45,
            sex="male",
            chronic_conditions=["asthma"],
            general_conditions=["appendectomy 2023"],
            medications=[],
            allergies=[],
            previous_visits=[],
        )
    )

    updated = PatientRepository(db_session).add_condition(patient.id, "chronic", "hypertension")

    assert updated.chronic_conditions == ["asthma", "hypertension"]
    assert updated.general_conditions == ["appendectomy 2023"]


def test_add_condition_to_general_category_preserves_chronic(db_session):
    patient = PatientRepository(db_session).add(
        Patient(name="Lim Hui Ying", age=29, sex="female", chronic_conditions=["asthma"], general_conditions=[], medications=[], allergies=[], previous_visits=[])
    )

    updated = PatientRepository(db_session).add_condition(patient.id, "general", "physical therapy")

    assert updated.chronic_conditions == ["asthma"]
    assert updated.general_conditions == ["physical therapy"]


def test_add_condition_dedupes_exact_repeats(db_session):
    patient = PatientRepository(db_session).add(
        Patient(name="Ahmad Ismail", age=62, sex="male", chronic_conditions=["diabetes"], general_conditions=[], medications=[], allergies=[], previous_visits=[])
    )

    PatientRepository(db_session).add_condition(patient.id, "chronic", "diabetes")

    assert patient.chronic_conditions == ["diabetes"]


def test_add_condition_returns_none_for_unknown_patient(db_session):
    assert PatientRepository(db_session).add_condition(999, "chronic", "diabetes") is None


def test_add_condition_api_appends_and_survives_registration_conditions():
    client, _session = _client()
    try:
        created = client.post(
            "/patients",
            json={"name": "Priya Nair", "age": 34, "sex": "female", "chronic_conditions": ["asthma"]},
        ).json()

        response = client.post(f"/patients/{created['id']}/conditions", json={"category": "general", "condition": "recent surgery"})

        assert response.status_code == 200
        body = response.json()
        assert body["chronic_conditions"] == ["asthma"]
        assert body["general_conditions"] == ["recent surgery"]
    finally:
        app.dependency_overrides.clear()


def test_add_condition_api_404_for_unknown_patient():
    client, _session = _client()
    try:
        response = client.post("/patients/999/conditions", json={"category": "chronic", "condition": "diabetes"})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_add_condition_api_422_for_invalid_category():
    client, _session = _client()
    try:
        created = client.post("/patients", json={"name": "Goh Zhi Hao", "age": 8, "sex": "male"}).json()

        response = client.post(f"/patients/{created['id']}/conditions", json={"category": "acute", "condition": "flu"})

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_build_prompt_renders_both_condition_categories(seeded):
    patient = seeded["patient"]
    patient.chronic_conditions = ["asthma"]
    patient.general_conditions = ["appendectomy 2023"]

    prompt = build_prompt(patient, [], [], [{"role": "patient", "content": "I have a cough"}])

    assert "Chronic conditions (long-term, always relevant): asthma" in prompt
    assert "Recent/general conditions (e.g. recent surgeries or procedures): appendectomy 2023" in prompt
