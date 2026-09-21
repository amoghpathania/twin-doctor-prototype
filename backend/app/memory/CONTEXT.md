# backend/app/memory/ context

Doctor memory: read-only retrieval for the twin, plus the candidate -> approve/reject learning loop. **No automatic promotion, ever.**

## Files
- `repository.py` - thin domain-facing wrapper (`get_approved_memories(session, doctor_id)`) over `repositories/memory_repository.py`. Exists as a separate file to match the original spec's structure; avoid duplicating persistence logic here.
- `retrieval.py` - `retrieve_relevant_memories(session, doctor_id, patient_context, top_k=5)`. Naive keyword-overlap scoring over **APPROVED-only** memories. This is a documented placeholder for pgvector/embedding-based semantic retrieval in production - do not assume it's semantically smart.
- `promotion.py` - the learning loop:
  - `create_candidate_memory(session, doctor_id, content, memory_type, source="doctor_feedback", confidence=0.7) -> Memory` (status=`CANDIDATE`).
  - `approve_memory(session, memory_id) -> Memory` (status=`APPROVED`, sets `approved_at`). Raises `ValueError` if not found.
  - `reject_memory(session, memory_id) -> Memory` (status=`REJECTED`). Raises `ValueError` if not found.
- `extraction.py` - on explicit case closure, parses a structured LLM result, skips normalized exact duplicates across every status, and creates at most one `CANDIDATE` per memory type with source `case_closure`. Extraction may return no candidates and never promotes them automatically.

## Invariant to preserve
`retrieval.py` must only ever consider `MemoryStatus.APPROVED` memories (enforced via `MemoryRepository.list_approved_by_doctor`). If you add new retrieval strategies, keep this filter - it's what makes "only APPROVED memories influence autonomous behavior" true.

## API surface
Exposed via `backend/app/api/memories.py`: `GET /memories/{doctor_id}` (all statuses), `POST /memories` (create candidate), `POST /memories/{id}/approve`, `POST /memories/{id}/reject`.
