from sqlalchemy.orm import Session

from app.models.domain import Appointment, AuditEvent, Doctor, Encounter, EncounterTestDecision, EvaluationRun, Memory, Patient
from app.seed_data import SEED_DOCTOR_NAMES, SEED_MEMORY_KEYS, SEED_PATIENT_NAMES



def _protected_doctor_ids(session: Session) -> set[int]:
    return {
        doctor.id
        for doctor in session.query(Doctor).filter(Doctor.name.in_(SEED_DOCTOR_NAMES)).all()
    }


def _protected_patient_ids(session: Session) -> set[int]:
    return {
        patient.id
        for patient in session.query(Patient).filter(Patient.name.in_(SEED_PATIENT_NAMES)).all()
    }


def _resettable_memories(session: Session, protected_doctor_ids: set[int]) -> list[Memory]:
    doctor_names = {
        doctor.id: doctor.name
        for doctor in session.query(Doctor).filter(Doctor.id.in_(protected_doctor_ids)).all()
    }
    return [
        memory
        for memory in session.query(Memory).all()
        if (doctor_names.get(memory.doctor_id), memory.content) not in SEED_MEMORY_KEYS
    ]


def get_data_summary(session: Session) -> dict[str, dict[str, int]]:
    protected_doctor_ids = _protected_doctor_ids(session)
    protected_patient_ids = _protected_patient_ids(session)
    resettable_memories = _resettable_memories(session, protected_doctor_ids)
    return {
        "resettable": {
            "encounters": session.query(Encounter).count(),
            "appointments": session.query(Appointment).count(),
            "audit_events": session.query(AuditEvent).count(),
            "evaluation_runs": session.query(EvaluationRun).count(),
            "test_decisions": session.query(EncounterTestDecision).count(),
            "memories": len(resettable_memories),
            "doctors": session.query(Doctor).filter(~Doctor.id.in_(protected_doctor_ids)).count(),
            "patients": session.query(Patient).filter(~Patient.id.in_(protected_patient_ids)).count(),
        },
        "protected": {
            "doctors": len(protected_doctor_ids),
            "patients": len(protected_patient_ids),
            "memories": session.query(Memory).count() - len(resettable_memories),
        },
    }


def reset_added_data(session: Session) -> dict[str, int]:
    counts = get_data_summary(session)["resettable"]
    protected_doctor_ids = _protected_doctor_ids(session)
    protected_patient_ids = _protected_patient_ids(session)

    session.query(Appointment).delete(synchronize_session=False)
    session.query(AuditEvent).delete(synchronize_session=False)
    session.query(EncounterTestDecision).delete(synchronize_session=False)
    session.query(Encounter).delete(synchronize_session=False)
    session.query(EvaluationRun).delete(synchronize_session=False)
    for memory in _resettable_memories(session, protected_doctor_ids):
        session.delete(memory)
    session.query(Doctor).filter(~Doctor.id.in_(protected_doctor_ids)).delete(synchronize_session=False)
    session.query(Patient).filter(~Patient.id.in_(protected_patient_ids)).delete(synchronize_session=False)
    session.commit()
    return counts