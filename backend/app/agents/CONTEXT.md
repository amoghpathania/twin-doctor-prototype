# backend/app/agents/ context

The Doctor Twin: one reusable implementation personalized per `doctor_id` at runtime (not a separate codebase/agent per doctor).

## Files
- `llm_client.py` - `LLMClient` Protocol with separate `generate_assessment(...)` and `generate_memories(...)` JSON operations + `GeminiLLMClient` (real implementation, requires `TWIN_GEMINI_API_KEY`, uses `google.generativeai` JSON mode). Tests always use `tests/fakes.py` doubles instead.
- `prompts.py` - builds the assessment prompt and a separate close-case extraction prompt. SHADOW mode adds strict collect-and-summarize-only instructions: no diagnosis, treatment, or action recommendation, and `recommended_action="await_doctor_review"`. Extraction compares the automated and doctor-reviewed assessments, includes the conversation and existing memories, and requests only durable, evidence-supported doctor behavior.
- `doctor_twin.py` - `DoctorTwin(session, doctor_id, llm_client, deployment_mode=None)`:
  - `.run(patient_id, conversation) -> ClinicalAssessment` (stable public API, used by `consultation_service`).
  - `.run_with_diagnostics(patient_id, conversation) -> (ClinicalAssessment, structured_output_valid: bool)` (used by the evaluation runner to measure structured-output validity).
  - Follow-up collection is bounded to five answered questions. Questions already present as `twin` turns are suppressed after model output so a repeated question cannot keep an intake open indefinitely.
  - On JSON parse/validation failure: deterministic fail-safe - `risk_level=AMBER`, `escalation_required=True`, `confidence=0.0`, reason "Structured output validation failed...". **Never** retries or proceeds autonomously on invalid output.
- `deployment_policy.py` - `evaluate_deployment_policy(mode, assessment) -> DeploymentDecision`:
  - `SHADOW`: `["collect_information", "awaiting_doctor_review"]`; creates a factual case summary without suggesting diagnosis or action. The parsed action is normalized to `await_doctor_review` even if the model returns something else.
  - `COPILOT`: `["propose_assessment_for_doctor_review"]`.
  - `INTAKE`: `["collect_patient_information", "create_structured_case_for_doctor"]`, plus `"escalate_to_doctor"` if AMBER/RED.
  - `AUTONOMOUS`: only allows `assessment.recommended_action` through if `risk_level == GREEN` AND the action is in `_AUTONOMOUS_ALLOWLISTED_ACTIONS` (`provide_informational_guidance`, `close_case`); otherwise forces `["escalate_to_doctor"]` - AMBER/RED **always** escalate regardless of mode.

## Critical invariant
The LLM's `risk_level` is never trusted as final. `consultation_service.py` always runs the result through `safety.policy.apply_safety_policy` before deployment-mode evaluation - see [../safety/CONTEXT.md](../safety/CONTEXT.md).
