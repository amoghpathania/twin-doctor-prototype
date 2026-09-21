# backend/app/safety/ context

Deterministic safety engine. **The LLM never has final authority on risk/safety** - this package can always override it.

## Files
- `red_flags.py` - Synthetic/demo-only keyword matching (`RED_FLAG_KEYWORDS` dict) against categories: `severe_chest_pain`, `difficulty_breathing`, `loss_of_consciousness`, `stroke_like_symptoms`, `severe_allergic_reaction`, `severe_bleeding`. `detect_conversation_red_flags(conversation)` grounds live detection in patient-authored turns, handles local negation, and resolves a short affirmative answer against one immediately preceding, unbundled twin question. `detect_red_flags(symptoms, conversation_text)` remains the flat-input detector for synthetic evaluations. No ML/LLM is involved.
- `policy.py` - `apply_safety_policy(assessment, red_flags) -> ClinicalAssessment`. If `red_flags` is non-empty, force `risk_level=RED`, `escalation_required=True`, and set `escalation_reason` to list which flags fired - **regardless of what the LLM said**. No-op (returns the same object) if no red flags detected.

## Where it's called
The conversation-aware detector runs in `services/consultation_service.py` between `DoctorTwin.run()` and `agents.deployment_policy.evaluate_deployment_policy()`. The flat-input detector is used by `services/evaluation_service.py`, whose cases provide symptoms and patient context rather than role-tagged conversation turns.

## Test coverage
`backend/tests/test_safety.py` covers every keyword category, direct patient reports, negation, contextual affirmation, bundled-question ambiguity, and the core override test. `backend/tests/test_consultation_api.py` verifies both affirmative and negative follow-up behavior, the override across all four deployment modes, and both `safety_override` and `escalation` audit events.
