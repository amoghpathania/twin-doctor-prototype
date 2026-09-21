# backend/app/models/ context

Single source of truth for data shapes - both API contracts (Pydantic) and persistence (SQLAlchemy).

## Files
- `schemas.py` - Pydantic v2 models. In addition to consultation/memory contracts, it defines catalog CRUD, structured test recommendations, de-identified scenario features, decision evidence, and encounter test-decision responses.
- `domain.py` - SQLAlchemy ORM models sharing the same enums (stored as `String` columns holding the enum `.value`), including `DiagnosticTestCatalog` hospital master data and `EncounterTestDecision` recommendation/selection provenance with immutable scenario/evidence JSON snapshots.

## Conventions / gotchas
- Enum columns are stored as plain `String`, not SQLAlchemy `Enum` - comparisons use `.value` (e.g. `MemoryStatus.APPROVED.value`).
- `Appointment.slot_start`/`slot_end` are **naive** `DateTime()` (no `timezone=True`) deliberately - SQLite round-trips through `session.refresh()` can silently mangle tz-aware datetimes, which broke an exact-datetime set-membership check in `clinic_tools.get_available_slots`. Keep these naive; normalize (`.replace(tzinfo=None)`) at the boundary if aware datetimes come in from the API.
- `Encounter.appointment_id` and other FK-like int fields are not enforced by SQLite FK constraints by default (pragma not enabled) - tests sometimes use fabricated ids (e.g. `doctor_id=1` with no doctor row) intentionally for unit-level isolation.
- List/dict fields (`chronic_conditions`, `general_conditions`, `conversation`, `assessment`, `payload`, `summary` on `EvaluationRun`) are stored as SQLAlchemy `JSON` columns.
