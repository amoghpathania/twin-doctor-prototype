import json

from app.agents.doctor_twin import DoctorTwin
from tests.fakes import FailingLLMClient, FakeLLMClient
from app.models.schemas import DeploymentMode

VALID_RESPONSE = json.dumps(
    {
        "symptoms": ["cough", "fever"],
        "missing_information": ["duration"],
        "risk_level": "GREEN",
        "escalation_required": False,
        "escalation_reason": None,
        "summary": "Mild cough and fever, likely viral.",
        "recommended_action": "provide_informational_guidance",
        "confidence": 0.8,
    }
)


def test_doctor_twin_parses_valid_structured_output(seeded):
    llm = FakeLLMClient(VALID_RESPONSE)
    twin = DoctorTwin(session=seeded["session"], doctor_id=seeded["doctor"].id, llm_client=llm)

    assessment = twin.run(patient_id=seeded["patient"].id, conversation=[{"role": "patient", "content": "I have a cough"}])

    assert assessment.risk_level.value == "GREEN"
    assert assessment.escalation_required is False
    assert "cough" in assessment.symptoms


def test_doctor_twin_includes_approved_memory_in_prompt(seeded):
    llm = FakeLLMClient(VALID_RESPONSE)
    twin = DoctorTwin(session=seeded["session"], doctor_id=seeded["doctor"].id, llm_client=llm)

    twin.run(patient_id=seeded["patient"].id, conversation=[{"role": "patient", "content": "persistent cough"}])

    assert "inhaler usage" in llm.calls[0]

def test_shadow_mode_prompt_collects_and_summarizes_without_clinical_advice(seeded):
    llm = FakeLLMClient(VALID_RESPONSE)
    twin = DoctorTwin(
        session=seeded["session"],
        doctor_id=seeded["doctor"].id,
        llm_client=llm,
        deployment_mode=DeploymentMode.SHADOW,
    )

    assessment = twin.run(
        patient_id=seeded["patient"].id,
        conversation=[{"role": "patient", "content": "I have a cough"}],
    )

    instruction = llm.system_instructions[0]
    assert "Do not diagnose" in instruction
    assert "Do not recommend" in instruction
    assert 'recommended_action must be exactly "await_doctor_review"' in instruction
    assert assessment.recommended_action == "await_doctor_review"


def test_doctor_twin_fails_safe_on_invalid_json(seeded):
    llm = FakeLLMClient("not valid json")
    twin = DoctorTwin(session=seeded["session"], doctor_id=seeded["doctor"].id, llm_client=llm)

    assessment = twin.run(patient_id=seeded["patient"].id, conversation=[{"role": "patient", "content": "hello"}])

    assert assessment.risk_level.value == "AMBER"
    assert assessment.escalation_required is True


def test_doctor_twin_fails_safe_on_schema_violation(seeded):
    llm = FakeLLMClient(json.dumps({"symptoms": ["cough"]}))  # missing required fields
    twin = DoctorTwin(session=seeded["session"], doctor_id=seeded["doctor"].id, llm_client=llm)

    assessment = twin.run(patient_id=seeded["patient"].id, conversation=[{"role": "patient", "content": "hello"}])

    assert assessment.risk_level.value == "AMBER"
    assert assessment.escalation_required is True


def test_doctor_twin_limits_follow_up_questions_to_one(seeded):
    response = json.loads(VALID_RESPONSE)
    response["missing_information"] = ["How long have you had the cough?", "Are you short of breath?"]
    twin = DoctorTwin(
        session=seeded["session"],
        doctor_id=seeded["doctor"].id,
        llm_client=FakeLLMClient(json.dumps(response)),
    )

    assessment = twin.run(
        patient_id=seeded["patient"].id,
        conversation=[{"role": "patient", "content": "I have a cough"}],
    )

    assert assessment.missing_information == ["How long have you had the cough?"]


def test_doctor_twin_does_not_repeat_an_answered_question(seeded):
    response = json.loads(VALID_RESPONSE)
    response["missing_information"] = ["How long have you had the cough?"]
    twin = DoctorTwin(
        session=seeded["session"],
        doctor_id=seeded["doctor"].id,
        llm_client=FakeLLMClient(json.dumps(response)),
    )

    assessment = twin.run(
        patient_id=seeded["patient"].id,
        conversation=[
            {"role": "patient", "content": "I have a cough"},
            {"role": "twin", "content": "How long have you had the cough?"},
            {"role": "patient", "content": "For three weeks"},
        ],
    )

    assert assessment.missing_information == []


def test_doctor_twin_stops_follow_ups_after_five_answered_questions(seeded):
    response = json.loads(VALID_RESPONSE)
    response["missing_information"] = ["Is there anything else you can tell me?"]
    twin = DoctorTwin(
        session=seeded["session"],
        doctor_id=seeded["doctor"].id,
        llm_client=FakeLLMClient(json.dumps(response)),
    )
    conversation = [{"role": "patient", "content": "I have a cough"}]
    for question_number in range(5):
        conversation.extend(
            [
                {"role": "twin", "content": f"Preliminary question {question_number}?"},
                {"role": "patient", "content": f"Answer {question_number}"},
            ]
        )

    assessment = twin.run(patient_id=seeded["patient"].id, conversation=conversation)

    assert assessment.missing_information == []


def test_doctor_twin_fails_safe_on_llm_call_error(seeded):
    """Provider errors (quota/network/auth) must escalate to the doctor, never raise up to the API layer."""
    llm = FailingLLMClient(RuntimeError("429 quota exceeded"))
    twin = DoctorTwin(session=seeded["session"], doctor_id=seeded["doctor"].id, llm_client=llm)

    assessment, valid = twin.run_with_diagnostics(
        patient_id=seeded["patient"].id, conversation=[{"role": "patient", "content": "hello"}]
    )

    assert valid is False
    assert assessment.risk_level.value == "AMBER"
    assert assessment.escalation_required is True
    assert assessment.recommended_action == "escalate_to_doctor"
