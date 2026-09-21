# backend/app/repositories/ context

The **only** layer allowed to talk to the database. Everything else (services, agents, tools) goes through here.

## Files
- `base.py` - generic `Repository[ModelT]` with `get_by_id`, `list_all`, `add` (commits + refreshes), `update` (commits + refreshes). Entity repos subclass this and just set `model = <DomainModel>`.
- `doctor_repository.py`, `patient_repository.py` - plain CRUD, no extra methods.
- `encounter_repository.py` - adds `list_by_patient(patient_id)` (ordered newest-first).
- `memory_repository.py` - adds `list_approved_by_doctor(doctor_id)` (status filter, used by `memory/retrieval.py`) and `list_by_doctor(doctor_id)` (all statuses, used by the `GET /memories/{doctor_id}` API).
- `audit_repository.py` - plain CRUD for the append-only `AuditEvent` log.
- `appointment_repository.py` - adds `list_by_doctor(doctor_id)` and `list_all()`.
- `evaluation_run_repository.py` - adds `latest()` (most recent `EvaluationRun` by `created_at`).
- `diagnostic_test_catalog_repository.py` - code lookup plus active/admin catalog listings.
- `encounter_test_decision_repository.py` - encounter decisions and doctor-scoped finalized Shadow/Copilot learning records.

## Convention
`repo.add()` and `repo.update()` both call `session.commit()` + `session.refresh(entity)` - callers get back a fully-populated, DB-consistent object, not a detached one. Because of the commit-on-add pattern, tests that need multiple related writes in one "transaction" just call `add`/`update` sequentially on the same session - there's no explicit unit-of-work wrapper.
