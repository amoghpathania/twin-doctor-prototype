from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.evaluation_fixtures import EVAL_PATIENT_NAME
from app.models.domain import Patient
from app.models.schemas import PatientConditionAddRequest, PatientCreateRequest, PatientRead
from app.repositories.patient_repository import PatientRepository

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[PatientRead])
def list_patients(db: Session = Depends(get_db)) -> list[PatientRead]:
    patients = db.query(Patient).filter(Patient.name != EVAL_PATIENT_NAME).all()
    return [PatientRead.model_validate(p) for p in patients]


@router.post("", response_model=PatientRead)
def create_patient(request: PatientCreateRequest, db: Session = Depends(get_db)) -> PatientRead:
    """Patient self-registration via intake. Always is_new_patient=True."""
    patient = Patient(
        name=request.name,
        age=request.age,
        sex=request.sex,
        chronic_conditions=request.chronic_conditions,
        general_conditions=request.general_conditions,
        medications=request.medications,
        allergies=request.allergies,
        is_new_patient=True,
    )
    patient = PatientRepository(db).add(patient)
    return PatientRead.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(patient_id: int, db: Session = Depends(get_db)) -> PatientRead:
    patient = PatientRepository(db).get_by_id(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientRead.model_validate(patient)


@router.post("/{patient_id}/conditions", response_model=PatientRead)
def add_patient_condition(
    patient_id: int, request: PatientConditionAddRequest, db: Session = Depends(get_db)
) -> PatientRead:
    """Append a chronic or general condition to a patient's record - never overwrites existing history."""
    patient = PatientRepository(db).add_condition(patient_id, request.category, request.condition)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientRead.model_validate(patient)
