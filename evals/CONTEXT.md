# evals/ context

Top-level, repo-root evaluation data + CLI convenience scripts. **Not required for the backend API to run** - the API only reads `cases.json`'s contents (via `backend/app/services/evaluation_service.py`), and all real evaluation logic lives in `backend/app/services/evaluation_service.py` (source of truth).

## Files
- `cases.json` - 32 synthetic evaluation cases (10 GREEN, 10 AMBER, 6 RED, 6 AMBIGUOUS). Each case: `id`, `category`, `patient_context`, `symptoms`, `expected_risk`, `required_questions`, `expected_escalation`, `expected_action`. Validated against `app.models.schemas.EvalCase` on load.
- `run_evals.py` - standalone CLI. Inserts `backend/` onto `sys.path`, uses the **real** `GeminiLLMClient` (requires `TWIN_GEMINI_API_KEY`), runs the suite, prints a summary (cases evaluated + 5 metrics as percentages). Run from the repo root: `python evals/run_evals.py`.
- `metrics.py` - thin re-export shim (`from app.services.evaluation_service import compute_metrics`) for anyone importing `evals.metrics` directly per the original spec's file layout. Don't add real logic here - it belongs in `evaluation_service.py`.

## Adding/editing cases
Keep the 30-50 range (test `test_real_cases_json_loads_and_has_between_30_and_50_cases` in `backend/tests/test_evaluation_service.py` asserts this) and keep at least GREEN/AMBER/RED categories represented. `required_questions` should be phrases you'd expect to see verbatim (case-insensitively) in the model's `missing_information` list - the coverage metric does substring matching, not semantic matching.
