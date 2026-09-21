"""Evaluation runner: executes synthetic cases through the Doctor Twin and computes metrics.

The API only depends on this module (self-contained within backend/app). The standalone
CLI at evals/run_evals.py and the evals/metrics.py shim are convenience wrappers for local/
manual runs and are not required for the API to function.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.agents.doctor_twin import DoctorTwin
from app.agents.llm_client import LLMClient
from app.config import get_settings
from app.evaluation_fixtures import EVAL_DOCTOR_NAME, EVAL_PATIENT_NAME
from app.models.domain import Doctor, Patient
from app.models.schemas import EvalCase, EvalCaseResult, EvaluationSummary, RiskLevel
from app.repositories.evaluation_run_repository import EvaluationRunRepository
from app.safety.policy import apply_safety_policy
from app.safety.red_flags import detect_red_flags

def default_cases_path() -> Path:
    settings = get_settings()
    if settings.eval_cases_path:
        return Path(settings.eval_cases_path)
    # backend/app/services/evaluation_service.py -> parents[3] is the repo root.
    return Path(__file__).resolve().parents[3] / "evals" / "cases.json"


def load_cases(path: Path | None = None) -> list[EvalCase]:
    path = path or default_cases_path()
    if not path.exists():
        raise FileNotFoundError(f"Evaluation cases file not found: {path}")
    raw = json.loads(path.read_text())
    return [EvalCase.model_validate(item) for item in raw]


def _ensure_eval_fixtures(session: Session) -> tuple[Doctor, Patient]:
    doctor = session.query(Doctor).filter(Doctor.name == EVAL_DOCTOR_NAME).one_or_none()
    if doctor is None:
        doctor = Doctor(
            name=EVAL_DOCTOR_NAME,
            specialty="General Medicine",
            experience="10 years",
            communication_style="Concise, empathetic, asks structured follow-up questions.",
            clinical_preferences="Ask symptom duration before assessing severity; ask about relevant medication use.",
            escalation_preferences="Escalate persistent or worsening symptoms.",
            twin_version="v1",
        )
        session.add(doctor)
        session.commit()

    patient = session.query(Patient).filter(Patient.name == EVAL_PATIENT_NAME).one_or_none()
    if patient is None:
        patient = Patient(
            name=EVAL_PATIENT_NAME,
            age=40,
            sex="unspecified",
            chronic_conditions=[],
            general_conditions=[],
            medications=[],
            allergies=[],
            previous_visits=[],
        )
        session.add(patient)
        session.commit()

    return doctor, patient


def _run_single_case(session: Session, doctor: Doctor, patient: Patient, case: EvalCase, llm_client: LLMClient) -> EvalCaseResult:
    twin = DoctorTwin(session=session, doctor_id=doctor.id, llm_client=llm_client)
    conversation = [{"role": "patient", "content": f"{case.patient_context} Symptoms: {', '.join(case.symptoms)}"}]
    assessment, structured_output_valid = twin.run_with_diagnostics(patient_id=patient.id, conversation=conversation)

    red_flags = detect_red_flags(assessment.symptoms or case.symptoms, case.patient_context)
    final_assessment = apply_safety_policy(assessment, red_flags)

    return EvalCaseResult(
        case_id=case.id,
        expected_risk=case.expected_risk,
        actual_risk=final_assessment.risk_level,
        expected_escalation=case.expected_escalation,
        actual_escalation=final_assessment.escalation_required,
        structured_output_valid=structured_output_valid,
        red_flags_detected=red_flags,
        recommended_action=final_assessment.recommended_action,
        expected_action=case.expected_action,
        required_questions=case.required_questions,
        missing_information=assessment.missing_information,
    )


def compute_metrics(results: list[EvalCaseResult]) -> dict[str, float]:
    """Pure metric computation - never hard-code these values, they must come from actual runs."""
    if not results:
        return {
            "red_flag_recall": 0.0,
            "escalation_recall": 0.0,
            "required_question_coverage": 0.0,
            "structured_output_validity": 0.0,
            "doctor_preference_alignment": 0.0,
        }

    total = len(results)

    red_expected = [r for r in results if r.expected_risk == RiskLevel.RED]
    red_flag_recall = (
        sum(1 for r in red_expected if r.actual_risk == RiskLevel.RED) / len(red_expected) if red_expected else 1.0
    )

    escalation_expected = [r for r in results if r.expected_escalation]
    escalation_recall = (
        sum(1 for r in escalation_expected if r.actual_escalation) / len(escalation_expected)
        if escalation_expected
        else 1.0
    )

    coverage_scores = []
    for r in results:
        if not r.required_questions:
            continue
        haystack = " ".join(r.missing_information).lower()
        matched = sum(1 for q in r.required_questions if q.lower() in haystack)
        coverage_scores.append(matched / len(r.required_questions))
    required_question_coverage = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 1.0

    structured_output_validity = sum(1 for r in results if r.structured_output_valid) / total
    doctor_preference_alignment = sum(1 for r in results if r.recommended_action == r.expected_action) / total

    return {
        "red_flag_recall": red_flag_recall,
        "escalation_recall": escalation_recall,
        "required_question_coverage": required_question_coverage,
        "structured_output_validity": structured_output_validity,
        "doctor_preference_alignment": doctor_preference_alignment,
    }


def run_evaluation_suite(session: Session, llm_client: LLMClient, cases: list[EvalCase] | None = None) -> EvaluationSummary:
    cases = cases if cases is not None else load_cases()
    doctor, patient = _ensure_eval_fixtures(session)

    results = [_run_single_case(session, doctor, patient, case, llm_client) for case in cases]
    metrics = compute_metrics(results)

    return EvaluationSummary(
        cases_evaluated=len(results),
        results=results,
        created_at=datetime.now(timezone.utc),
        **metrics,
    )


def persist_evaluation_summary(session: Session, summary: EvaluationSummary):
    from app.models.domain import EvaluationRun

    run = EvaluationRun(summary=json.loads(summary.model_dump_json()))
    return EvaluationRunRepository(session).add(run)


def get_latest_evaluation_summary(session: Session) -> EvaluationSummary | None:
    latest = EvaluationRunRepository(session).latest()
    if latest is None:
        return None
    return EvaluationSummary.model_validate(latest.summary)
