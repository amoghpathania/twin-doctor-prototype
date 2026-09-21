# backend/app/services/ context

Orchestration layer - wires agents, safety, tools, and repositories together for a given use case. This is where cross-cutting workflow logic lives, not in the API routers.

## Files
- `consultation_service.py` - the core `Patient -> DoctorTwin -> Safety -> DeploymentMode` pipeline:
  - Passes the encounter's deployment mode into `DoctorTwin`. In SHADOW mode the twin only collects information and summarizes it; deterministic safety still classifies red flags and escalation independently.
  - `start_consultation(...)` - creates an `Encounter`, runs the twin + safety policy, persists, returns response.
  - `add_consultation_message(...)` - appends a turn to an existing encounter's conversation and re-runs the twin + safety policy (multi-turn follow-up). Resets `doctor_reviewed`/`doctor_review_action` since the assessment changes.
  - `review_consultation(...)` - doctor approves the current assessment unchanged, or modifies specific fields (`risk_level`, `escalation_required`, `escalation_reason`, `summary`, `recommended_action`). Does **not** re-run the safety engine - the doctor is the final human authority here, unlike the automated LLM path. Sets `Encounter.doctor_reviewed=True` and `doctor_review_action` (`"approve"`/`"modify"`), records a `doctor_approved_assessment`/`doctor_modified_assessment` audit event.
  - `close_consultation(...)` - explicitly closes a reviewed case exactly once, then attempts structured candidate-memory extraction. For SHADOW cases, extraction receives the doctor's modified assessment/response and next action, not an agent recommendation. Closure succeeds even if extraction fails; `case_closed` and `case_memory_extraction_failed` audit events capture the outcome. Closed encounters reject later messages and review changes.
  - `build_consultation_response(session, encounter, assessment, deployment_mode) -> ConsultationResponse` - single source of truth for constructing the API response (used by both the start/add-message flows and `GET /consultations/{id}`). Fetches available slots only for non-fallback AMBER escalations after follow-up questions are complete.
  - Records `safety_override` audit event when red flags fired, and `escalation` audit event whenever `escalation_required` is true.
- `audit_service.py` - `record_event(session, event_type, encounter_id, payload) -> AuditEvent`. Append-only; used by consultation_service, clinic_tools, and the memories API.
- `evaluation_service.py` - the evaluation runner (self-contained, doesn't require the sibling `evals/` dir except to load `evals/cases.json`):
  - `load_cases(path=None)` - defaults to resolving `<repo_root>/evals/cases.json` via `Path(__file__).resolve().parents[3]`, overridable via `Settings.eval_cases_path`.
  - `run_evaluation_suite(session, llm_client, cases=None) -> EvaluationSummary` - runs each case through a shared synthetic eval doctor/patient (`_ensure_eval_fixtures`, created lazily, name `"Dr. Sarah Lim (Eval)"` / `"Synthetic Eval Patient"`), applies the same safety policy as the live API, computes metrics.
  - `compute_metrics(results) -> dict` - pure function (red_flag_recall, escalation_recall, required_question_coverage, structured_output_validity, doctor_preference_alignment). **Never hard-code these values** - they must come from an actual run.
  - `persist_evaluation_summary` / `get_latest_evaluation_summary` - `EvaluationRun` persistence.

## Gotcha
`evaluation_service.py` is the single source of truth for eval logic. `evals/run_evals.py` (CLI) and `evals/metrics.py` at the repo root are thin wrappers that `sys.path.insert` the `backend/` dir and re-import from here - don't duplicate logic into those files.
