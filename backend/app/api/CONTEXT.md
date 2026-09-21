# backend/app/api/ context

FastAPI routers. Keep these thin - business logic belongs in `services/`, `agents/`, `memory/`, or `tools/`.

## Files
- `deps.py` - shared dependencies. `get_llm_client()` returns a real `GeminiLLMClient`; tests override it via `app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient(...)`.
- `doctors.py` - `GET /doctors/{id}`.
- `patients.py` - `GET /patients/{id}`.
- `consultations.py` - `POST /consultations` (start case), `GET /consultations/{id}`, `GET /consultations?doctor_id=` (list, for the dashboard), `POST /consultations/{id}/messages` (multi-turn follow-up - added beyond the original spec's minimum API list, needed for conversational flow), `POST /consultations/{id}/review` (doctor approves the assessment as-is or modifies specific fields - added endpoint, the doctor is always the final authority regardless of deployment mode). Delegates to `services/consultation_service.py`.
- `memories.py` - `GET /memories/{doctor_id}` (all statuses), `POST /memories` (create CANDIDATE from doctor feedback - added endpoint, not in the original spec's minimum list but required for the learning loop to have an entry point), `POST /memories/{id}/approve`, `POST /memories/{id}/reject`.
- `appointments.py` - `GET /appointments` (optional `doctor_id` filter), `GET /appointments/available-slots?doctor_id=`, `POST /appointments`. Delegates to `tools/clinic_tools.py`.
- `evaluations.py` - `POST /evaluations/run` (executes the full eval suite, persists result), `GET /evaluations/results` (latest persisted run, 404 if none yet).
- `admin.py` - `GET /admin/data-summary` reports resettable and protected row counts. `POST /admin/reset-data` requires the exact `RESET ADDED DATA` confirmation phrase, clears operational/test activity, user-added profiles, and non-baseline memories, while preserving the deterministic seed doctor, patients, and memories.
- `diagnostic_tests.py` - `GET /diagnostic-tests` lists active hospital tests for doctor selection. Admin routes list all, create, and patch catalog entries; deactivation preserves historical decisions.

## Gotcha
Routers importing `get_llm_client` should import it from `app.api.deps`, not redefine it - `consultations.py` and `evaluations.py` share the same dependency object so a single `dependency_overrides` entry affects both.
