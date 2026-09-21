"""Doctor feedback -> candidate memory -> explicit approve/reject. No auto-promotion."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.domain import Memory
from app.models.schemas import MemoryStatus, MemoryType
from app.repositories.memory_repository import MemoryRepository


def create_candidate_memory(
    session: Session,
    doctor_id: int,
    content: str,
    memory_type: MemoryType,
    source: str = "doctor_feedback",
    confidence: float = 0.7,
) -> Memory:
    memory = Memory(
        doctor_id=doctor_id,
        content=content,
        memory_type=memory_type.value,
        source=source,
        confidence=confidence,
        status=MemoryStatus.CANDIDATE.value,
    )
    return MemoryRepository(session).add(memory)


def approve_memory(session: Session, memory_id: int) -> Memory:
    repo = MemoryRepository(session)
    memory = repo.get_by_id(memory_id)
    if memory is None:
        raise ValueError("Memory not found")

    memory.status = MemoryStatus.APPROVED.value
    memory.approved_at = datetime.now(timezone.utc)
    return repo.update(memory)


def reject_memory(session: Session, memory_id: int) -> Memory:
    repo = MemoryRepository(session)
    memory = repo.get_by_id(memory_id)
    if memory is None:
        raise ValueError("Memory not found")

    memory.status = MemoryStatus.REJECTED.value
    return repo.update(memory)
