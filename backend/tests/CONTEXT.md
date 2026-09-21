# backend/tests/ context

Fully hermetic pytest suite - no network calls, no real Gemini API key needed. 116 tests as of the latest full run, all passing.

## Fixtures & doubles
- `conftest.py`:
  - `db_session` - fresh in-memory SQLite engine per test (**must use `poolclass=StaticPool`** - without it, FastAPI's threadpool execution gets a different connection with no tables -> "no such table" errors).
  - `seeded` - `db_session` plus a seeded `Dr. Sarah Lim` doctor, `Tan Wei Ming` patient, and one APPROVED `Memory` ("For persistent cough, ask about inhaler usage.").
- `fakes.py`:
  - `FakeLLMClient(response)` - returns the same scripted JSON string for every call; records `.calls`.
  - `ScriptedLLMClient(responses)` - returns one response per call in order (index = call count) - used for multi-case eval tests where each case needs a different LLM output.

## Test files (one per concern)
- `test_repositories.py` - CRUD per repository.
- `test_doctor_twin.py` - valid/invalid/schema-violating LLM output, fail-safe behavior, memory-in-prompt inclusion.
- `test_safety.py` - every red-flag keyword category + the core override test (LLM GREEN + red flag -> final RED) + no-op-without-flags.
- `test_deployment_modes.py` - all 4 modes x risk levels, especially AUTONOMOUS blocking AMBER/RED and requiring an allowlisted action for GREEN.
- `test_consultation_api.py` - full API integration (TestClient + `dependency_overrides` for `get_db`/`get_llm_client`). Includes RED override across all 4 modes, both audit event types, and AMBER escalation + available-slots surfacing.
- `test_memory_approval.py` / `test_memories_api.py` - candidate creation, approve/reject lifecycle (unit + API), and the "not retrieved until approved" invariant.
- `test_clinic_tools.py` - slot generation/exclusion, appointment creation + encounter linking, clinical note audit events, and the mock MCP adapter (imports `mcp.clinic_server` via a `sys.path` insert of the repo root inside the test file itself, since `backend/pytest.ini`'s `pythonpath = .` only adds `backend/`).
- `test_evaluation_service.py` - pure `compute_metrics` unit tests + `run_evaluation_suite` with `ScriptedLLMClient` + sanity check that the real `evals/cases.json` loads with 30-50 cases.
- `test_evaluations_api.py` - `/evaluations/run` then `/evaluations/results`, 404 before any run.
- `test_diagnostic_test_catalog.py` - public/admin catalog behavior, validation, soft deactivation, and reset preservation.
- `test_test_decision_learning.py` - Shadow/Copilot labels, scenario and doctor isolation, rejection evidence, and autonomous gates.
- `test_test_recommendation_integration.py` - two-stage DoctorTwin recommendation context and review reconciliation.

## Pattern for API-level tests
Each API test module builds its own isolated in-memory engine + seeded rows, sets `app.dependency_overrides[get_db]` / `app.dependency_overrides[get_llm_client]`, and **must** call `app.dependency_overrides.clear()` in a `finally` block to avoid leaking overrides into other tests.
