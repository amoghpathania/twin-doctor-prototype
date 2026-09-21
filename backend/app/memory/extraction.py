"""Extract review-supported candidate memories from a closed case."""

import json

from sqlalchemy.orm import Session

from app.agents.llm_client import LLMClient
from app.agents.prompts import build_memory_extraction_prompt, build_memory_extraction_system_instruction
from app.memory.promotion import create_candidate_memory
from app.models.domain import Doctor, Encounter, Memory
from app.models.schemas import MemoryExtractionResult
from app.repositories.memory_repository import MemoryRepository


def _normalize_content(content: str) -> str:
    return " ".join(content.casefold().split())


def extract_candidate_memories(
    session: Session,
    doctor: Doctor,
    encounter: Encounter,
    before_assessment: dict,
    final_assessment: dict,
    review_action: str,
    llm_client: LLMClient,
) -> list[Memory]:
    existing_memories = MemoryRepository(session).list_by_doctor(doctor.id)
    raw_result = llm_client.generate_memories(
        build_memory_extraction_system_instruction(doctor),
        build_memory_extraction_prompt(
            encounter.conversation,
            before_assessment,
            final_assessment,
            review_action,
            existing_memories,
        ),
    )
    result = MemoryExtractionResult.model_validate(json.loads(raw_result))
    existing_keys = {
        (memory.memory_type, _normalize_content(memory.content)) for memory in existing_memories
    }
    created = []
    for candidate in result.candidates:
        key = (candidate.memory_type.value, _normalize_content(candidate.content))
        if key in existing_keys:
            continue
        created.append(
            create_candidate_memory(
                session,
                doctor_id=doctor.id,
                content=candidate.content,
                memory_type=candidate.memory_type,
                source="case_closure",
                confidence=candidate.confidence,
            )
        )
        existing_keys.add(key)
    return created