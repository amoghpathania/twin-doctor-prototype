from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models.domain import (
    Appointment,
    AuditEvent,
    DiagnosticTestCatalog,
    Doctor,
    Encounter,
    EncounterTestDecision,
    EvaluationRun,
    Memory,
    Patient,
)
from app.seed_data import seed_session


def _client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: session
    return TestClient(app), session


def test_admin_reset_removes_added_data_and_preserves_seed_records():
    client, session = _client()
    try:
        seed_doctor = Doctor(
            name="Dr. Sarah Lim",
            specialty="General Medicine",
            experience="10 years",
            communication_style="Concise",
            clinical_preferences="Structured questions",
            escalation_preferences="Escalate worsening symptoms",
        )
        added_doctor = Doctor(
            name="Dr. Added",
            specialty="Pediatrics",
            experience="5 years",
            communication_style="Warm",
            clinical_preferences="None",
            escalation_preferences="Standard",
        )
        seed_patient = Patient(
            name="Tan Wei Ming",
            age=45,
            sex="male",
            chronic_conditions=["asthma"],
            general_conditions=[],
            medications=[],
            allergies=[],
            previous_visits=[],
        )
        added_patient = Patient(
            name="Added Patient",
            age=30,
            sex="female",
            chronic_conditions=[],
            general_conditions=[],
            medications=[],
            allergies=[],
            previous_visits=[],
            is_new_patient=True,
        )
        session.add_all([seed_doctor, added_doctor, seed_patient, added_patient])
        session.commit()

        seed_memory = Memory(
            doctor_id=seed_doctor.id,
            content="For persistent cough, ask about inhaler usage.",
            memory_type="clinical_pattern",
            source="doctor_feedback",
            confidence=0.9,
            status="APPROVED",
        )
        added_memory = Memory(
            doctor_id=seed_doctor.id,
            content="User-approved guidance",
            memory_type="preference",
            source="doctor_feedback",
            confidence=0.8,
            status="APPROVED",
        )
        encounter = Encounter(
            patient_id=added_patient.id,
            doctor_id=added_doctor.id,
            deployment_mode="SHADOW",
            conversation=[],
            assessment={},
            risk_level="GREEN",
            summary="Test",
        )
        session.add_all([seed_memory, added_memory, encounter])
        session.commit()

        catalog_item = DiagnosticTestCatalog(code="CBC", name="Complete Blood Count", category="Laboratory")
        session.add(catalog_item)
        session.commit()

        session.add_all(
            [
                Appointment(
                    doctor_id=added_doctor.id,
                    patient_id=added_patient.id,
                    encounter_id=encounter.id,
                    slot_start=datetime.now(timezone.utc),
                    slot_end=datetime.now(timezone.utc),
                ),
                AuditEvent(encounter_id=encounter.id, event_type="test", payload={}),
                EncounterTestDecision(
                    encounter_id=encounter.id,
                    doctor_id=added_doctor.id,
                    test_catalog_id=catalog_item.id,
                    deployment_mode="SHADOW",
                    origin="DOCTOR_SELECTED",
                    status="ORDERED",
                    decided_by="DOCTOR",
                    scenario_features={},
                    evidence_snapshot={},
                ),
                EvaluationRun(summary={"cases_evaluated": 1}),
            ]
        )
        session.commit()

        summary = client.get("/admin/data-summary")
        assert summary.status_code == 200
        assert summary.json()["resettable"] == {
            "encounters": 1,
            "appointments": 1,
            "audit_events": 1,
            "evaluation_runs": 1,
            "test_decisions": 1,
            "memories": 1,
            "doctors": 1,
            "patients": 1,
        }

        rejected = client.post("/admin/reset-data", json={"confirmation": "reset"})
        assert rejected.status_code == 422
        assert session.query(Encounter).count() == 1

        response = client.post("/admin/reset-data", json={"confirmation": "RESET ADDED DATA"})
        assert response.status_code == 200
        assert response.json()["deleted"] == summary.json()["resettable"]

        assert session.query(Doctor).all() == [seed_doctor]
        assert session.query(Patient).all() == [seed_patient]
        assert session.query(Memory).all() == [seed_memory]
        assert session.query(Encounter).count() == 0
        assert session.query(Appointment).count() == 0
        assert session.query(AuditEvent).count() == 0
        assert session.query(EvaluationRun).count() == 0
        assert session.query(EncounterTestDecision).count() == 0
        assert session.query(DiagnosticTestCatalog).all() == [catalog_item]
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_admin_reset_preserves_all_specialty_seed_data():
    client, session = _client()
    try:
        seed_session(session)
        expected_doctors = session.query(Doctor).count()
        expected_patients = session.query(Patient).count()
        expected_memories = session.query(Memory).count()

        summary = client.get("/admin/data-summary")
        assert summary.status_code == 200
        assert summary.json()["protected"] == {
            "doctors": expected_doctors,
            "patients": expected_patients,
            "memories": expected_memories,
        }

        response = client.post("/admin/reset-data", json={"confirmation": "RESET ADDED DATA"})
        assert response.status_code == 200
        assert session.query(Doctor).count() == expected_doctors
        assert session.query(Patient).count() == expected_patients
        assert session.query(Memory).count() == expected_memories
    finally:
        app.dependency_overrides.clear()
        session.close()