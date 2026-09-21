from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.llm_client import LLMClient
from app.api.deps import get_llm_client
from app.db import get_db
from app.models.schemas import (
    ConsultationMessageRequest,
    ConsultationResponse,
    ConsultationReviewRequest,
    ConsultationStartRequest,
    DeploymentMode,
)
from app.repositories.encounter_repository import EncounterRepository
from app.services import consultation_service

router = APIRouter(prefix="/consultations", tags=["consultations"])


@router.post("", response_model=ConsultationResponse)
def start_consultation(
    request: ConsultationStartRequest,
    db: Session = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
) -> ConsultationResponse:
    try:
        return consultation_service.start_consultation(
            session=db,
            doctor_id=request.doctor_id,
            patient_id=request.patient_id,
            message=request.message,
            llm_client=llm_client,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=list[ConsultationResponse])
def list_consultations(doctor_id: int, db: Session = Depends(get_db)) -> list[ConsultationResponse]:
    """Active/past cases for a doctor's dashboard."""
    encounters = EncounterRepository(db).list_by_doctor(doctor_id)
    responses = []
    for encounter in encounters:
        assessment = consultation_service.parse_stored_assessment(encounter.assessment)
        deployment_mode = DeploymentMode(encounter.deployment_mode)
        responses.append(consultation_service.build_consultation_response(db, encounter, assessment, deployment_mode))
    return responses


@router.get("/patient/{patient_id}", response_model=list[ConsultationResponse])
def list_open_patient_consultations(patient_id: int, db: Session = Depends(get_db)) -> list[ConsultationResponse]:
    """Cases a patient can resume: their own, not yet reviewed by the doctor."""
    encounters = EncounterRepository(db).list_by_patient(patient_id)
    responses = []
    for encounter in encounters:
        if encounter.doctor_reviewed:
            continue
        assessment = consultation_service.parse_stored_assessment(encounter.assessment)
        deployment_mode = DeploymentMode(encounter.deployment_mode)
        responses.append(consultation_service.build_consultation_response(db, encounter, assessment, deployment_mode))
    return responses


@router.get("/{consultation_id}", response_model=ConsultationResponse)
def get_consultation(consultation_id: int, db: Session = Depends(get_db)) -> ConsultationResponse:
    encounter = EncounterRepository(db).get_by_id(consultation_id)
    if encounter is None:
        raise HTTPException(status_code=404, detail="Consultation not found")

    assessment = consultation_service.parse_stored_assessment(encounter.assessment)
    deployment_mode = DeploymentMode(encounter.deployment_mode)
    return consultation_service.build_consultation_response(db, encounter, assessment, deployment_mode)


@router.post("/{consultation_id}/messages", response_model=ConsultationResponse)
def add_message(
    consultation_id: int,
    request: ConsultationMessageRequest,
    db: Session = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
) -> ConsultationResponse:
    try:
        return consultation_service.add_consultation_message(
            session=db,
            encounter_id=consultation_id,
            message=request.message,
            llm_client=llm_client,
        )
    except consultation_service.ConsultationStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{consultation_id}/review", response_model=ConsultationResponse)
def review_consultation(
    consultation_id: int,
    request: ConsultationReviewRequest,
    db: Session = Depends(get_db),
) -> ConsultationResponse:
    """Doctor approves the AI assessment as-is, or modifies specific fields before it's finalized."""
    try:
        return consultation_service.review_consultation(session=db, encounter_id=consultation_id, review=request)
    except consultation_service.ConsultationStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{consultation_id}/close", response_model=ConsultationResponse)
def close_consultation(
    consultation_id: int,
    db: Session = Depends(get_db),
    llm_client: LLMClient = Depends(get_llm_client),
) -> ConsultationResponse:
    try:
        return consultation_service.close_consultation(db, consultation_id, llm_client)
    except consultation_service.ConsultationStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
