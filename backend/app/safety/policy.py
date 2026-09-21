"""Deterministic policy layer: the LLM never has final authority on safety."""

from app.models.schemas import ClinicalAssessment, RiskLevel


def apply_safety_policy(assessment: ClinicalAssessment, red_flags: list[str]) -> ClinicalAssessment:
    """Override the assessment to RED + escalate whenever a red flag is detected, regardless of LLM output."""
    if not red_flags:
        return assessment

    reason = f"Safety engine override: red flag(s) detected ({', '.join(red_flags)})"
    return assessment.model_copy(
        update={
            "risk_level": RiskLevel.RED,
            "escalation_required": True,
            "escalation_reason": reason,
        }
    )
