from app.models.domain import AuditEvent, Doctor, Encounter, Memory, Patient
from app.repositories.audit_repository import AuditRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.encounter_repository import EncounterRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.patient_repository import PatientRepository
from app.models.schemas import MemoryStatus, MemoryType


def test_doctor_repository_crud(db_session):
    repo = DoctorRepository(db_session)
    doctor = repo.add(
        Doctor(
            name="Dr. Sarah Lim",
            specialty="General Medicine",
            experience="10 years",
            communication_style="Concise",
            clinical_preferences="Ask duration first",
            escalation_preferences="Escalate worsening symptoms",
            twin_version="v1",
        )
    )
    assert repo.get_by_id(doctor.id).name == "Dr. Sarah Lim"


def test_patient_repository_crud(db_session):
    repo = PatientRepository(db_session)
    patient = repo.add(
        Patient(name="Tan Wei Ming", age=45, sex="male", chronic_conditions=[], general_conditions=[], medications=[], allergies=[], previous_visits=[])
    )
    assert repo.get_by_id(patient.id).age == 45


def test_encounter_repository_list_by_patient(seeded):
    session = seeded["session"]
    repo = EncounterRepository(session)
    encounter = repo.add(
        Encounter(
            patient_id=seeded["patient"].id,
            doctor_id=seeded["doctor"].id,
            deployment_mode="SHADOW",
            conversation=[],
            risk_level="GREEN",
        )
    )
    results = repo.list_by_patient(seeded["patient"].id)
    assert [e.id for e in results] == [encounter.id]


def test_memory_repository_lists_only_approved(seeded):
    session = seeded["session"]
    repo = MemoryRepository(session)
    repo.add(
        Memory(
            doctor_id=seeded["doctor"].id,
            content="candidate memory",
            memory_type=MemoryType.PREFERENCE.value,
            source="doctor_feedback",
            status=MemoryStatus.CANDIDATE.value,
        )
    )
    approved = repo.list_approved_by_doctor(seeded["doctor"].id)
    assert [m.id for m in approved] == [seeded["memory"].id]


def test_audit_repository_add(db_session):
    repo = AuditRepository(db_session)
    event = repo.add(AuditEvent(encounter_id=None, event_type="escalation", payload={"reason": "test"}))
    assert repo.get_by_id(event.id).event_type == "escalation"
