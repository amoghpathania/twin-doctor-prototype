import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.consultations import get_llm_client
from app.db import Base, get_db
from app.main import app
from app.models.domain import AuditEvent, Doctor, Encounter, Memory, Patient
from app.models.schemas import MemoryStatus, MemoryType
from tests.fakes import MemoryExtractionLLMClient


ASSESSMENT_RESPONSE = json.dumps(
    {
        "symptoms": ["persistent cough"],
        "missing_information": [],
        "risk_level": "AMBER",
        "escalation_required": True,
        "escalation_reason": "Persistent symptoms require review.",
        "summary": "Persistent cough for over two weeks.",
        "recommended_action": "escalate_to_doctor",
        "confidence": 0.8,
    }
)

MEMORY_RESPONSE = json.dumps(
    {
        "candidates": [
            {
                "memory_type": "clinical_pattern",
                "content": "For persistent cough, ask about recent inhaler use.",
                "confidence": 0.84,
            },
            {
                "memory_type": "communication_style",
                "content": "Explain follow-up actions with concise language.",
                "confidence": 0.72,
            },
        ]
    }
)


def _make_client(memory_response: str | Exception = MEMORY_RESPONSE):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    doctor = Doctor(
        name="Dr. Sarah Lim",
        specialty="General Medicine",
        experience="10 years",
        communication_style="Concise",
        clinical_preferences="Ask duration first",
        escalation_preferences="Escalate worsening symptoms",
        twin_version="v1",
        default_deployment_mode="COPILOT",
    )
    patient = Patient(
        name="Tan Wei Ming",
        age=45,
        sex="male",
        chronic_conditions=[],
        general_conditions=[],
        medications=[],
        allergies=[],
        previous_visits=[],
    )
    session.add_all([doctor, patient])
    session.commit()
    llm = MemoryExtractionLLMClient(ASSESSMENT_RESPONSE, memory_response)

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm_client] = lambda: llm
    return TestClient(app), session, doctor, patient, llm


def _start_case(client: TestClient, doctor_id: int, patient_id: int) -> dict:
    response = client.post(
        "/consultations",
        json={"doctor_id": doctor_id, "patient_id": patient_id, "message": "I have had a cough for three weeks."},
    )
    assert response.status_code == 200
    return response.json()


def test_unreviewed_case_cannot_close():
    client, session, doctor, patient, llm = _make_client()
    try:
        case = _start_case(client, doctor.id, patient.id)

        response = client.post(f"/consultations/{case['id']}/close")

        assert response.status_code == 409
        assert session.get(Encounter, case["id"]).closed_at is None
        assert llm.memory_calls == []
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_reviewed_case_closes_once_and_creates_candidate_memories():
    client, session, doctor, patient, llm = _make_client()
    try:
        case = _start_case(client, doctor.id, patient.id)
        assert client.post(f"/consultations/{case['id']}/review", json={"action": "approve"}).status_code == 200

        first = client.post(f"/consultations/{case['id']}/close")
        second = client.post(f"/consultations/{case['id']}/close")

        assert first.status_code == 200
        assert first.json()["closed_at"] is not None
        assert second.status_code == 200
        assert second.json()["closed_at"] == first.json()["closed_at"]
        assert len(llm.memory_calls) == 1

        memories = session.query(Memory).filter(Memory.doctor_id == doctor.id).all()
        assert {(item.memory_type, item.source, item.status) for item in memories} == {
            ("clinical_pattern", "case_closure", MemoryStatus.CANDIDATE.value),
            ("communication_style", "case_closure", MemoryStatus.CANDIDATE.value),
        }
        closed_events = session.query(AuditEvent).filter(AuditEvent.event_type == "case_closed").all()
        assert len(closed_events) == 1
        assert closed_events[0].payload["candidate_count"] == 2
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_extraction_failure_does_not_block_closure():
    client, session, doctor, patient, llm = _make_client(RuntimeError("provider secret details"))
    try:
        case = _start_case(client, doctor.id, patient.id)
        client.post(f"/consultations/{case['id']}/review", json={"action": "approve"})

        response = client.post(f"/consultations/{case['id']}/close")

        assert response.status_code == 200
        assert response.json()["closed_at"] is not None
        assert session.query(Memory).count() == 0
        failure = session.query(AuditEvent).filter(AuditEvent.event_type == "case_memory_extraction_failed").one()
        assert failure.payload == {"error_type": "RuntimeError"}
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_closed_case_rejects_messages_and_review_changes():
    client, session, doctor, patient, llm = _make_client(json.dumps({"candidates": []}))
    try:
        case = _start_case(client, doctor.id, patient.id)
        client.post(f"/consultations/{case['id']}/review", json={"action": "approve"})
        client.post(f"/consultations/{case['id']}/close")

        message = client.post(f"/consultations/{case['id']}/messages", json={"message": "One more detail"})
        review = client.post(f"/consultations/{case['id']}/review", json={"action": "approve"})

        assert message.status_code == 409
        assert review.status_code == 409
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_extraction_supports_every_category_and_skips_normalized_duplicates():
    candidates = [
        {"memory_type": memory_type.value, "content": f"Guidance for {memory_type.value}.", "confidence": 0.7}
        for memory_type in MemoryType
    ]
    client, session, doctor, patient, llm = _make_client(json.dumps({"candidates": candidates}))
    session.add(
        Memory(
            doctor_id=doctor.id,
            content="  guidance FOR preference.  ",
            memory_type=MemoryType.PREFERENCE.value,
            source="doctor_feedback",
            confidence=0.9,
            status=MemoryStatus.REJECTED.value,
        )
    )
    session.commit()
    try:
        case = _start_case(client, doctor.id, patient.id)
        client.post(f"/consultations/{case['id']}/review", json={"action": "approve"})

        response = client.post(f"/consultations/{case['id']}/close")

        assert response.status_code == 200
        extracted = session.query(Memory).filter(Memory.source == "case_closure").all()
        assert {memory.memory_type for memory in extracted} == {
            memory_type.value for memory_type in MemoryType if memory_type != MemoryType.PREFERENCE
        }
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_shadow_doctor_response_is_sent_for_memory_candidate_extraction():
    client, session, doctor, patient, llm = _make_client()
    doctor.default_deployment_mode = "SHADOW"
    session.commit()
    try:
        case = _start_case(client, doctor.id, patient.id)
        review = client.post(
            f"/consultations/{case['id']}/review",
            json={
                "action": "modify",
                "risk_level": "GREEN",
                "escalation_required": False,
                "summary": "Doctor assessed a mild post-viral cough.",
                "recommended_action": "Use supportive care and return if symptoms worsen.",
            },
        )
        assert review.status_code == 200

        closed = client.post(f"/consultations/{case['id']}/close")

        assert closed.status_code == 200
        assert len(llm.memory_calls) == 1
        assert "Doctor assessed a mild post-viral cough." in llm.memory_calls[0]
        assert "Use supportive care and return if symptoms worsen." in llm.memory_calls[0]
        assert session.query(Memory).filter(Memory.source == "case_closure").count() == 2
    finally:
        app.dependency_overrides.clear()
        session.close()