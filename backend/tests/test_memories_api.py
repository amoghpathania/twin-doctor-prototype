from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models.domain import Doctor, Memory
from app.models.schemas import MemoryStatus, MemoryType


def _client_with_seeded_doctor():
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
    )
    session.add(doctor)
    session.commit()

    approved_memory = Memory(
        doctor_id=doctor.id,
        content="For persistent cough, ask about inhaler usage.",
        memory_type=MemoryType.CLINICAL_PATTERN.value,
        source="doctor_feedback",
        confidence=0.9,
        status=MemoryStatus.APPROVED.value,
    )
    session.add(approved_memory)
    session.commit()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), session, doctor


def test_list_memories_returns_seeded_approved_memory():
    client, session, doctor = _client_with_seeded_doctor()
    try:
        response = client.get(f"/memories/{doctor.id}")
        assert response.status_code == 200
        contents = [m["content"] for m in response.json()]
        assert "For persistent cough, ask about inhaler usage." in contents
    finally:
        app.dependency_overrides.clear()


def test_create_memory_creates_candidate():
    client, session, doctor = _client_with_seeded_doctor()
    try:
        response = client.post(
            "/memories",
            json={
                "doctor_id": doctor.id,
                "content": "For wheezing, ask about nebulizer use.",
                "memory_type": "clinical_pattern",
                "source": "doctor_feedback",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "CANDIDATE"
        assert body["approved_at"] is None
    finally:
        app.dependency_overrides.clear()


def test_approve_then_reject_memory_lifecycle():
    client, session, doctor = _client_with_seeded_doctor()
    try:
        created = client.post(
            "/memories",
            json={
                "doctor_id": doctor.id,
                "content": "Ask about family history of asthma.",
                "memory_type": "clinical_pattern",
            },
        ).json()

        approved = client.post(f"/memories/{created['id']}/approve")
        assert approved.status_code == 200
        assert approved.json()["status"] == "APPROVED"

        rejected = client.post(f"/memories/{created['id']}/reject")
        assert rejected.status_code == 200
        assert rejected.json()["status"] == "REJECTED"
    finally:
        app.dependency_overrides.clear()


def test_approve_nonexistent_memory_returns_404():
    client, session, doctor = _client_with_seeded_doctor()
    try:
        response = client.post("/memories/999999/approve")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
