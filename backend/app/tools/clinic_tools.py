"""Tools/service layer the AI calls - it must never touch the database directly."""

from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.domain import Appointment, Encounter, Patient
from app.models.schemas import AppointmentSlot
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.encounter_repository import EncounterRepository
from app.repositories.patient_repository import PatientRepository
from app.services.audit_service import record_event

_SLOT_HOURS = range(9, 17)  # synthetic 9am-5pm clinic hours
_SLOT_DURATION = timedelta(hours=1)


def get_patient(session: Session, patient_id: int) -> Patient | None:
    return PatientRepository(session).get_by_id(patient_id)


def get_previous_visits(session: Session, patient_id: int) -> list[Encounter]:
    return EncounterRepository(session).list_by_patient(patient_id)


def get_available_slots(session: Session, doctor_id: int, day: datetime | None = None) -> list[AppointmentSlot]:
    """Synthetic clinic hours minus already-booked slots for the given doctor/day. Uses naive datetimes."""
    day = day.replace(tzinfo=None) if day else (datetime.now() + timedelta(days=1))
    booked_starts = {
        appt.slot_start
        for appt in AppointmentRepository(session).list_by_doctor(doctor_id)
        if appt.slot_start.date() == day.date()
    }
    slots = []
    for hour in _SLOT_HOURS:
        start = datetime.combine(day.date(), time(hour=hour))
        if start in booked_starts:
            continue
        slots.append(AppointmentSlot(start=start, end=start + _SLOT_DURATION))
    return slots


def create_appointment(
    session: Session,
    doctor_id: int,
    patient_id: int,
    slot_start: datetime,
    encounter_id: int | None = None,
) -> Appointment:
    slot_start = slot_start.replace(tzinfo=None)
    appointment = Appointment(
        doctor_id=doctor_id,
        patient_id=patient_id,
        encounter_id=encounter_id,
        slot_start=slot_start,
        slot_end=slot_start + _SLOT_DURATION,
        status="scheduled",
    )
    appointment = AppointmentRepository(session).add(appointment)

    if encounter_id is not None:
        encounter = EncounterRepository(session).get_by_id(encounter_id)
        if encounter is not None:
            encounter.appointment_id = appointment.id
            EncounterRepository(session).update(encounter)

    record_event(
        session,
        event_type="appointment_created",
        encounter_id=encounter_id,
        payload={"appointment_id": appointment.id, "slot_start": slot_start.isoformat()},
    )
    return appointment


def create_clinical_note(session: Session, encounter_id: int, content: str) -> None:
    """Synthetic demo note capture, recorded as an audit event (no dedicated notes table yet)."""
    record_event(session, event_type="clinical_note", encounter_id=encounter_id, payload={"content": content})
