from app.models.schemas import ClinicalAssessment, RiskLevel
from app.safety.policy import apply_safety_policy
from app.safety.red_flags import detect_conversation_red_flags, detect_red_flags


def _assessment(risk_level: RiskLevel = RiskLevel.GREEN) -> ClinicalAssessment:
    return ClinicalAssessment(
        symptoms=[],
        missing_information=[],
        risk_level=risk_level,
        escalation_required=False,
        escalation_reason=None,
        summary="",
        recommended_action="provide_informational_guidance",
        confidence=0.9,
    )


def test_detects_chest_pain():
    assert "severe_chest_pain" in detect_red_flags([], "I have crushing chest pain")


def test_detects_difficulty_breathing():
    assert "difficulty_breathing" in detect_red_flags(["shortness of breath"], "")


def test_detects_loss_of_consciousness():
    assert "loss_of_consciousness" in detect_red_flags([], "my friend passed out")


def test_detects_stroke_like_symptoms():
    assert "stroke_like_symptoms" in detect_red_flags([], "sudden slurred speech")


def test_detects_severe_allergic_reaction():
    assert "severe_allergic_reaction" in detect_red_flags([], "throat swelling after eating peanuts")


def test_detects_severe_bleeding():
    assert "severe_bleeding" in detect_red_flags([], "uncontrolled bleeding from the leg")


def test_no_red_flags_for_benign_symptoms():
    assert detect_red_flags(["mild cough"], "I have had a cough for two days") == []


def test_conversation_detector_ignores_red_flag_in_twins_question_when_patient_says_none():
    conversation = [
        {"role": "patient", "content": "I have had a fever for 5 days"},
        {"role": "twin", "content": "Are you experiencing shortness of breath?"},
        {"role": "patient", "content": "None"},
    ]

    assert detect_conversation_red_flags(conversation) == []


def test_conversation_detector_resolves_yes_against_single_red_flag_question():
    conversation = [
        {"role": "twin", "content": "Are you experiencing shortness of breath?"},
        {"role": "patient", "content": "Yes"},
    ]

    assert detect_conversation_red_flags(conversation) == ["difficulty_breathing"]


def test_conversation_detector_honors_explicit_negation():
    conversation = [{"role": "patient", "content": "I do not have shortness of breath"}]

    assert detect_conversation_red_flags(conversation) == []


def test_conversation_detector_detects_direct_patient_report():
    conversation = [{"role": "patient", "content": "I have crushing chest pain"}]

    assert detect_conversation_red_flags(conversation) == ["severe_chest_pain"]


def test_conversation_detector_does_not_infer_from_ambiguous_bundled_question():
    conversation = [
        {"role": "twin", "content": "Do you have a cough or shortness of breath?"},
        {"role": "patient", "content": "Yes"},
    ]

    assert detect_conversation_red_flags(conversation) == []


def test_safety_policy_overrides_llm_green_to_red_when_red_flag_present():
    llm_assessment = _assessment(risk_level=RiskLevel.GREEN)

    final = apply_safety_policy(llm_assessment, red_flags=["severe_chest_pain"])

    assert final.risk_level == RiskLevel.RED
    assert final.escalation_required is True
    assert "severe_chest_pain" in final.escalation_reason


def test_safety_policy_is_noop_without_red_flags():
    llm_assessment = _assessment(risk_level=RiskLevel.GREEN)

    final = apply_safety_policy(llm_assessment, red_flags=[])

    assert final == llm_assessment
