import pytest

from app.agents.deployment_policy import evaluate_deployment_policy
from app.models.schemas import ClinicalAssessment, DeploymentMode, RiskLevel


def _assessment(risk_level: RiskLevel, recommended_action: str = "provide_informational_guidance") -> ClinicalAssessment:
    return ClinicalAssessment(
        symptoms=[],
        missing_information=[],
        risk_level=risk_level,
        escalation_required=risk_level != RiskLevel.GREEN,
        escalation_reason=None,
        summary="",
        recommended_action=recommended_action,
        confidence=0.9,
    )


def test_shadow_mode_only_records():
    decision = evaluate_deployment_policy(DeploymentMode.SHADOW, _assessment(RiskLevel.RED))
    assert decision.allowed_actions == ["collect_information", "awaiting_doctor_review"]
    assert decision.autonomous_action_taken is False


def test_copilot_mode_proposes_for_doctor_review():
    decision = evaluate_deployment_policy(DeploymentMode.COPILOT, _assessment(RiskLevel.AMBER))
    assert decision.allowed_actions == ["propose_assessment_for_doctor_review"]
    assert decision.autonomous_action_taken is False


def test_intake_mode_escalates_amber_and_red():
    for risk in (RiskLevel.AMBER, RiskLevel.RED):
        decision = evaluate_deployment_policy(DeploymentMode.INTAKE, _assessment(risk))
        assert "escalate_to_doctor" in decision.allowed_actions
        assert decision.autonomous_action_taken is False


def test_intake_mode_green_does_not_escalate():
    decision = evaluate_deployment_policy(DeploymentMode.INTAKE, _assessment(RiskLevel.GREEN))
    assert "escalate_to_doctor" not in decision.allowed_actions


def test_autonomous_mode_allows_allowlisted_green_action():
    decision = evaluate_deployment_policy(
        DeploymentMode.AUTONOMOUS, _assessment(RiskLevel.GREEN, recommended_action="close_case")
    )
    assert decision.allowed_actions == ["close_case"]
    assert decision.autonomous_action_taken is True


@pytest.mark.parametrize("risk_level", [RiskLevel.AMBER, RiskLevel.RED])
def test_autonomous_mode_always_escalates_amber_and_red(risk_level):
    decision = evaluate_deployment_policy(DeploymentMode.AUTONOMOUS, _assessment(risk_level))
    assert decision.allowed_actions == ["escalate_to_doctor"]
    assert decision.autonomous_action_taken is False


def test_autonomous_mode_escalates_green_action_not_allowlisted():
    decision = evaluate_deployment_policy(
        DeploymentMode.AUTONOMOUS, _assessment(RiskLevel.GREEN, recommended_action="prescribe_medication")
    )
    assert decision.allowed_actions == ["escalate_to_doctor"]
    assert decision.autonomous_action_taken is False
