from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.evaluation_fixtures import EVAL_DOCTOR_NAME
from app.models.domain import Doctor
from app.models.schemas import DoctorCreateRequest, DoctorModeUpdateRequest, DoctorRead
from app.repositories.doctor_repository import DoctorRepository

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("", response_model=list[DoctorRead])
def list_doctors(db: Session = Depends(get_db)) -> list[DoctorRead]:
    doctors = db.query(Doctor).filter(Doctor.name != EVAL_DOCTOR_NAME).all()
    return [DoctorRead.model_validate(d) for d in doctors]


@router.post("", response_model=DoctorRead)
def create_doctor(request: DoctorCreateRequest, db: Session = Depends(get_db)) -> DoctorRead:
    """Admin onboarding. default_deployment_mode is always SHADOW, regardless of any input."""
    doctor = Doctor(
        name=request.name,
        specialty=request.specialty,
        experience=request.experience,
        communication_style=request.communication_style,
        clinical_preferences=request.clinical_preferences,
        escalation_preferences=request.escalation_preferences,
        default_deployment_mode="SHADOW",
    )
    doctor = DoctorRepository(db).add(doctor)
    return DoctorRead.model_validate(doctor)


@router.get("/{doctor_id}", response_model=DoctorRead)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)) -> DoctorRead:
    doctor = DoctorRepository(db).get_by_id(doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return DoctorRead.model_validate(doctor)


@router.post("/{doctor_id}/mode", response_model=DoctorRead)
def update_doctor_mode(doctor_id: int, request: DoctorModeUpdateRequest, db: Session = Depends(get_db)) -> DoctorRead:
    """Each doctor controls their own twin's deployment mode."""
    repo = DoctorRepository(db)
    doctor = repo.get_by_id(doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.default_deployment_mode = request.deployment_mode.value
    doctor = repo.update(doctor)
    return DoctorRead.model_validate(doctor)
