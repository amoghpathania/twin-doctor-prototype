"""Domain-facing memory access used by the Doctor Twin (thin wrapper over persistence)."""

from sqlalchemy.orm import Session

from app.models.domain import Memory
from app.repositories.memory_repository import MemoryRepository


def get_approved_memories(session: Session, doctor_id: int) -> list[Memory]:
    return MemoryRepository(session).list_approved_by_doctor(doctor_id)
