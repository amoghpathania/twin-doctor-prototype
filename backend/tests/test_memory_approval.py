import pytest

from app.memory import promotion
from app.memory.retrieval import retrieve_relevant_memories
from app.models.schemas import MemoryStatus, MemoryType


def test_create_candidate_memory_starts_as_candidate(db_session):
    memory = promotion.create_candidate_memory(
        db_session,
        doctor_id=1,
        content="For persistent cough, ask about inhaler usage.",
        memory_type=MemoryType.CLINICAL_PATTERN,
    )
    assert memory.status == MemoryStatus.CANDIDATE.value
    assert memory.approved_at is None


def test_approve_memory_sets_approved_status_and_timestamp(db_session):
    memory = promotion.create_candidate_memory(
        db_session, doctor_id=1, content="Ask about medication use.", memory_type=MemoryType.PREFERENCE
    )

    approved = promotion.approve_memory(db_session, memory.id)

    assert approved.status == MemoryStatus.APPROVED.value
    assert approved.approved_at is not None


def test_reject_memory_sets_rejected_status(db_session):
    memory = promotion.create_candidate_memory(
        db_session, doctor_id=1, content="Irrelevant suggestion.", memory_type=MemoryType.PREFERENCE
    )

    rejected = promotion.reject_memory(db_session, memory.id)

    assert rejected.status == MemoryStatus.REJECTED.value
    assert rejected.approved_at is None


def test_approve_nonexistent_memory_raises(db_session):
    with pytest.raises(ValueError):
        promotion.approve_memory(db_session, memory_id=999)


def test_reject_nonexistent_memory_raises(db_session):
    with pytest.raises(ValueError):
        promotion.reject_memory(db_session, memory_id=999)


def test_candidate_memory_is_not_retrieved_until_approved(seeded):
    session = seeded["session"]
    doctor_id = seeded["doctor"].id

    candidate = promotion.create_candidate_memory(
        session, doctor_id=doctor_id, content="For wheezing, ask about nebulizer use.", memory_type=MemoryType.CLINICAL_PATTERN
    )

    before_approval = retrieve_relevant_memories(session, doctor_id, "patient has wheezing and nebulizer")
    assert candidate.id not in [m.id for m in before_approval]

    promotion.approve_memory(session, candidate.id)

    after_approval = retrieve_relevant_memories(session, doctor_id, "patient has wheezing and nebulizer")
    assert candidate.id in [m.id for m in after_approval]
