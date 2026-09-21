from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.schemas import AppointmentCreateRequest, AppointmentRead, AppointmentSlot
from app.repositories.appointment_repository import AppointmentRepository
from app.tools import clinic_tools

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("", response_model=list[AppointmentRead])
def list_appointments(doctor_id: int | None = None, db: Session = Depends(get_db)) -> list[AppointmentRead]:
    repo = AppointmentRepository(db)
    appointments = repo.list_by_doctor(doctor_id) if doctor_id is not None else repo.list_all()
    return [AppointmentRead.model_validate(a) for a in appointments]


@router.get("/available-slots", response_model=list[AppointmentSlot])
def available_slots(doctor_id: int, db: Session = Depends(get_db)) -> list[AppointmentSlot]:
    return clinic_tools.get_available_slots(db, doctor_id)


@router.post("", response_model=AppointmentRead)
def create_appointment(request: AppointmentCreateRequest, db: Session = Depends(get_db)) -> AppointmentRead:
    appointment = clinic_tools.create_appointment(
        db,
        doctor_id=request.doctor_id,
        patient_id=request.patient_id,
        slot_start=request.slot_start,
        encounter_id=request.encounter_id,
    )
    return AppointmentRead.model_validate(appointment)
