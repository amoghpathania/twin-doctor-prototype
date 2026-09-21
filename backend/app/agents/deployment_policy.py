"""Deployment-mode policy: same DoctorTwin, different permitted actions per mode."""

from app.models.schemas import ClinicalAssessment, DeploymentDecision, DeploymentMode, RiskLevel

_AUTONOMOUS_ALLOWLISTED_ACTIONS = {"provide_informational_guidance", "close_case"}


def evaluate_deployment_policy(mode: DeploymentMode, assessment: ClinicalAssessment) -> DeploymentDecision:
    if mode == DeploymentMode.SHADOW:
        return DeploymentDecision(
            mode=mode, allowed_actions=["collect_information", "awaiting_doctor_review"], autonomous_action_taken=False
        )

    if mode == DeploymentMode.COPILOT:
        return DeploymentDecision(
            mode=mode,
            allowed_actions=["propose_assessment_for_doctor_review"],
            autonomous_action_taken=False,
        )

    if mode == DeploymentMode.INTAKE:
        actions = ["collect_patient_information", "create_structured_case_for_doctor"]
        if assessment.risk_level in (RiskLevel.AMBER, RiskLevel.RED):
            actions.append("escalate_to_doctor")
        return DeploymentDecision(mode=mode, allowed_actions=actions, autonomous_action_taken=False)

    # AUTONOMOUS: only allowlisted GREEN workflows may proceed; AMBER/RED always escalate.
    if assessment.risk_level == RiskLevel.GREEN and assessment.recommended_action in _AUTONOMOUS_ALLOWLISTED_ACTIONS:
        return DeploymentDecision(
            mode=mode,
            allowed_actions=[assessment.recommended_action],
            autonomous_action_taken=True,
        )

    return DeploymentDecision(mode=mode, allowed_actions=["escalate_to_doctor"], autonomous_action_taken=False)
