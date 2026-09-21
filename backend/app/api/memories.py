from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.memory import promotion
from app.models.schemas import MemoryCreateRequest, MemoryRead
from app.repositories.memory_repository import MemoryRepository
from app.services.audit_service import record_event

router = APIRouter(prefix="/memories", tags=["memories"])


@router.get("/{doctor_id}", response_model=list[MemoryRead])
def list_memories(doctor_id: int, db: Session = Depends(get_db)) -> list[MemoryRead]:
    memories = MemoryRepository(db).list_by_doctor(doctor_id)
    return [MemoryRead.model_validate(m) for m in memories]


@router.post("", response_model=MemoryRead)
def create_memory(request: MemoryCreateRequest, db: Session = Depends(get_db)) -> MemoryRead:
    memory = promotion.create_candidate_memory(
        db,
        doctor_id=request.doctor_id,
        content=request.content,
        memory_type=request.memory_type,
        source=request.source,
        confidence=request.confidence,
    )
    record_event(db, event_type="memory_created", encounter_id=None, payload={"memory_id": memory.id})
    return MemoryRead.model_validate(memory)


@router.post("/{memory_id}/approve", response_model=MemoryRead)
def approve_memory(memory_id: int, db: Session = Depends(get_db)) -> MemoryRead:
    try:
        memory = promotion.approve_memory(db, memory_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_event(db, event_type="memory_approved", encounter_id=None, payload={"memory_id": memory.id})
    return MemoryRead.model_validate(memory)


@router.post("/{memory_id}/reject", response_model=MemoryRead)
def reject_memory(memory_id: int, db: Session = Depends(get_db)) -> MemoryRead:
    try:
        memory = promotion.reject_memory(db, memory_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    record_event(db, event_type="memory_rejected", encounter_id=None, payload={"memory_id": memory.id})
    return MemoryRead.model_validate(memory)
