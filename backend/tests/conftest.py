import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.domain import Doctor, Memory, Patient
from app.models.schemas import MemoryStatus, MemoryType


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def seeded(db_session):
    doctor = Doctor(
        name="Dr. Sarah Lim",
        specialty="General Medicine",
        experience="10 years",
        communication_style="Concise, empathetic, asks structured follow-up questions.",
        clinical_preferences="Ask symptom duration before assessing severity; ask about relevant medication use.",
        escalation_preferences="Escalate persistent or worsening symptoms.",
        twin_version="v1",
    )
    patient = Patient(
        name="Tan Wei Ming",
        age=45,
        sex="male",
        chronic_conditions=["asthma"],
        general_conditions=[],
        medications=["salbutamol inhaler"],
        allergies=[],
        previous_visits=[],
    )
    db_session.add_all([doctor, patient])
    db_session.commit()

    memory = Memory(
        doctor_id=doctor.id,
        content="For persistent cough, ask about inhaler usage.",
        memory_type=MemoryType.CLINICAL_PATTERN.value,
        source="doctor_feedback",
        confidence=0.9,
        status=MemoryStatus.APPROVED.value,
    )
    db_session.add(memory)
    db_session.commit()

    return {"session": db_session, "doctor": doctor, "patient": patient, "memory": memory}
