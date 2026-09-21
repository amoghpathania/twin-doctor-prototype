import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.models.domain import Doctor, Encounter, Patient
from app.tools import clinic_tools

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _seed_doctor_and_patient(session):
    doctor = Doctor(
        name="Dr. Sarah Lim",
        specialty="General Medicine",
        experience="10 years",
        communication_style="Concise",
        clinical_preferences="Ask duration first",
        escalation_preferences="Escalate worsening symptoms",
        twin_version="v1",
    )
    patient = Patient(name="Tan Wei Ming", age=45, sex="male", chronic_conditions=[], general_conditions=[], medications=[], allergies=[], previous_visits=[])
    session.add_all([doctor, patient])
    session.commit()
    return doctor, patient


def test_get_available_slots_returns_synthetic_hourly_slots(db_session):
    doctor, _patient = _seed_doctor_and_patient(db_session)

    slots = clinic_tools.get_available_slots(db_session, doctor.id, day=datetime.now(timezone.utc) + timedelta(days=1))

    assert len(slots) == 8  # 9am-5pm hourly
    assert slots[0].end - slots[0].start == timedelta(hours=1)


def test_create_appointment_persists_and_links_encounter(db_session):
    doctor, patient = _seed_doctor_and_patient(db_session)
    encounter = Encounter(
        patient_id=patient.id, doctor_id=doctor.id, deployment_mode="INTAKE", conversation=[], risk_level="AMBER"
    )
    db_session.add(encounter)
    db_session.commit()

    slot_start = datetime.now(timezone.utc) + timedelta(days=1)
    appointment = clinic_tools.create_appointment(
        db_session, doctor_id=doctor.id, patient_id=patient.id, slot_start=slot_start, encounter_id=encounter.id
    )

    assert appointment.id is not None
    db_session.refresh(encounter)
    assert encounter.appointment_id == appointment.id


def test_get_available_slots_excludes_booked_slot(db_session):
    doctor, patient = _seed_doctor_and_patient(db_session)
    day = datetime.now(timezone.utc) + timedelta(days=1)
    booked_start = day.replace(hour=9, minute=0, second=0, microsecond=0)
    clinic_tools.create_appointment(db_session, doctor_id=doctor.id, patient_id=patient.id, slot_start=booked_start)

    slots = clinic_tools.get_available_slots(db_session, doctor.id, day=day)

    assert all(slot.start != booked_start for slot in slots)
    assert len(slots) == 7


def test_create_clinical_note_records_audit_event(db_session):
    doctor, patient = _seed_doctor_and_patient(db_session)
    encounter = Encounter(
        patient_id=patient.id, doctor_id=doctor.id, deployment_mode="COPILOT", conversation=[], risk_level="GREEN"
    )
    db_session.add(encounter)
    db_session.commit()

    clinic_tools.create_clinical_note(db_session, encounter.id, "Doctor confirmed viral cause, no antibiotics needed.")

    from app.models.domain import AuditEvent

    events = db_session.query(AuditEvent).filter(AuditEvent.event_type == "clinical_note").all()
    assert len(events) == 1
    assert events[0].payload["content"] == "Doctor confirmed viral cause, no antibiotics needed."


def test_mock_mcp_clinic_server_delegates_to_clinic_tools(db_session):
    from mcp.clinic_server import ClinicMCPServer

    doctor, patient = _seed_doctor_and_patient(db_session)
    server = ClinicMCPServer(db_session)

    fetched = server.get_patient(patient.id)
    assert fetched.id == patient.id

    slots = server.get_available_slots(doctor.id, datetime.now(timezone.utc) + timedelta(days=1))
    assert len(slots) == 8
