"""Synthetic clinical context snippets - placeholder until a real guidelines dataset is seeded (phase 9)."""

import json

from app.models.domain import Doctor, Memory, Patient
from app.models.schemas import DeploymentMode

SYNTHETIC_CLINICAL_CONTEXT = [
    "Persistent cough lasting over 2 weeks warrants asking about inhaler/medication use.",
    "Fever with duration over 3 days should prompt asking about hydration and associated symptoms.",
    "Any mention of chest pain, breathing difficulty, or loss of consciousness must be treated as high priority.",
]

RESPONSE_SCHEMA_INSTRUCTIONS = (
    "Respond with ONLY a JSON object matching this schema: "
    '{"symptoms": [string], "missing_information": [string], '
    '"risk_level": "GREEN"|"AMBER"|"RED", "escalation_required": bool, '
    '"escalation_reason": string|null, "summary": string, '
    '"recommended_action": string, "confidence": float between 0 and 1}. '
    'The "missing_information" list must contain at most ONE item: the single most clinically '
    "important follow-up question to ask next, written as a complete, specific, natural sentence you "
    'would actually say to the patient - for example "How high has your temperature gotten, and have '
    'you taken it with a thermometer?" rather than a bare topic label like "Exact temperature". Ask '
    "about only one thing at a time; never bundle multiple questions into one string and never return "
    "more than one item. Every prior twin question followed by a patient response has already been "
    "answered: never ask it again or rephrase it. Ask no more than five follow-up questions across the "
    "entire conversation. After five answered follow-ups, or as soon as the preliminary information is "
    "enough to create a useful case summary, return an empty list and choose the appropriate next action, "
    "test recommendation workflow, or doctor escalation. Use an empty list once no further question is needed. "
    "Do not include any prose outside the JSON object."
)

MEMORY_EXTRACTION_INSTRUCTIONS = """You extract durable doctor-specific working preferences from a closed synthetic case.
Return only JSON with a `candidates` array. It may be empty and may contain at most one item for each category:
preference, escalation_rule, communication_style, clinical_pattern, workflow_preference.
Each item must contain memory_type, concise standalone content, and confidence from 0 to 1.
Only extract behavior supported by the doctor's review or a clear repeated workflow signal. Do not store patient identity,
patient-specific facts, diagnoses, prescriptions, or unsupported clinical rules. Do not repeat an existing memory.
All output remains pending until the doctor approves it."""

SHADOW_MODE_INSTRUCTIONS = """Deployment mode: SHADOW.
Your role is limited to collecting patient-reported information and creating a concise, factual intake summary for the doctor.
Do not diagnose, suggest a likely diagnosis, prescribe, or give treatment advice.
Do not recommend any clinical or operational action. The doctor alone decides the diagnosis and next action.
Use missing_information only to ask one neutral fact-gathering question at a time.
The summary must contain only patient-reported facts and relevant profile context, without clinical interpretation.
The recommended_action must be exactly "await_doctor_review"."""


def build_system_instruction(doctor: Doctor, deployment_mode: DeploymentMode | None = None) -> str:
    """Stable per-doctor persona + output-format rules, sent as the Gemini system role (not per-request content)."""
    guideline_lines = "\n".join(f"- {g}" for g in SYNTHETIC_CLINICAL_CONTEXT)
    mode_instructions = SHADOW_MODE_INSTRUCTIONS if deployment_mode == DeploymentMode.SHADOW else ""

    return f"""You are a clinical intake assistant personalized to a specific doctor. This is a SYNTHETIC/DEMO prototype - never claim to provide a real diagnosis.

{RESPONSE_SCHEMA_INSTRUCTIONS}

{mode_instructions}

Doctor profile:
- Name: {doctor.name}
- Specialty: {doctor.specialty}
- Communication style: {doctor.communication_style}
- Clinical preferences: {doctor.clinical_preferences}
- Escalation preferences: {doctor.escalation_preferences}

Synthetic clinical context:
{guideline_lines}
"""


def build_prompt(
    patient: Patient,
    memories: list[Memory],
    prior_encounter_summaries: list[str],
    conversation: list[dict],
) -> str:
    memory_lines = "\n".join(f"- {m.content}" for m in memories) or "- (none)"
    history_lines = "\n".join(f"- {s}" for s in prior_encounter_summaries) or "- (no prior visits)"
    conversation_lines = "\n".join(f"{turn['role']}: {turn['content']}" for turn in conversation)

    return f"""Doctor-specific approved memories:
{memory_lines}

Patient profile:
- Name: {patient.name}, Age: {patient.age}, Sex: {patient.sex}
- Chronic conditions (long-term, always relevant): {", ".join(patient.chronic_conditions) or "none"}
- Recent/general conditions (e.g. recent surgeries or procedures): {", ".join(patient.general_conditions) or "none"}
- Medications: {", ".join(patient.medications) or "none"}
- Allergies: {", ".join(patient.allergies) or "none"}

Prior visit summaries:
{history_lines}

Conversation so far:
{conversation_lines}
"""


def build_memory_extraction_system_instruction(doctor: Doctor) -> str:
    return f"""This is a SYNTHETIC/DEMO clinical workflow, not a medical device.

{MEMORY_EXTRACTION_INSTRUCTIONS}

Doctor profile:
- Name: {doctor.name}
- Specialty: {doctor.specialty}
- Communication style: {doctor.communication_style}
- Clinical preferences: {doctor.clinical_preferences}
- Escalation preferences: {doctor.escalation_preferences}
"""


def build_memory_extraction_prompt(
    conversation: list[dict],
    before_assessment: dict,
    final_assessment: dict,
    review_action: str,
    existing_memories: list[Memory],
) -> str:
    existing = [
        {"memory_type": memory.memory_type, "content": memory.content, "status": memory.status}
        for memory in existing_memories
    ]
    return "\n".join(
        [
            f"Doctor review action: {review_action}",
            f"Conversation: {json.dumps(conversation, ensure_ascii=True)}",
            f"Automated assessment before review: {json.dumps(before_assessment, ensure_ascii=True)}",
            f"Final doctor-reviewed assessment: {json.dumps(final_assessment, ensure_ascii=True)}",
            f"Existing memories: {json.dumps(existing, ensure_ascii=True)}",
        ]
    )


TEST_RECOMMENDATION_INSTRUCTIONS = """Recommend diagnostic tests for a synthetic clinical workflow.
Return only JSON with a `recommendations` array containing at most five items. Each item must contain
catalog_code, clinical_indication, confidence from 0 to 1, and an optional evidence_summary.
Use only codes in the active hospital catalog. Recommend a test only when the current scenario independently
justifies it. Doctor-specific evidence may rank or suppress choices but must never create a clinical indication.
Return an empty array when no test is justified. Do not include prose outside the JSON object."""


def build_test_recommendation_system_instruction(doctor: Doctor) -> str:
    return f"""This is a SYNTHETIC/DEMO clinical workflow, not a medical device.

{TEST_RECOMMENDATION_INSTRUCTIONS}

Doctor profile:
- Name: {doctor.name}
- Specialty: {doctor.specialty}
- Clinical preferences: {doctor.clinical_preferences}
"""


def build_test_recommendation_prompt(scenario, catalog, context) -> str:
    catalog_data = [
        {"code": item.code, "name": item.name, "category": item.category, "description": item.description}
        for item in catalog
    ]
    return "\n".join(
        [
            f"Current scenario: {json.dumps(scenario.model_dump(mode='json'), ensure_ascii=True)}",
            f"Active hospital catalog: {json.dumps(catalog_data, ensure_ascii=True)}",
            "Doctor-specific test decision evidence: "
            f"{json.dumps(context.model_dump(mode='json'), ensure_ascii=True)}",
        ]
    )
