"""Retrieval fallback: naive keyword overlap. Swap for pgvector similarity in production."""

from sqlalchemy.orm import Session

from app.memory.repository import get_approved_memories
from app.models.domain import Memory


def _overlap_score(content: str, context_words: set[str]) -> int:
    content_words = set(content.lower().split())
    return len(content_words & context_words)


def retrieve_relevant_memories(session: Session, doctor_id: int, patient_context: str, top_k: int = 5) -> list[Memory]:
    context_words = set(patient_context.lower().split())
    approved = get_approved_memories(session, doctor_id)
    scored = [(m, _overlap_score(m.content, context_words)) for m in approved]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [memory for memory, _score in scored[:top_k]]
