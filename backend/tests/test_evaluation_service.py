import json

from app.models.schemas import EvalCaseResult, RiskLevel
from app.services.evaluation_service import compute_metrics, default_cases_path, load_cases, run_evaluation_suite
from tests.fakes import ScriptedLLMClient


def _result(
    case_id: str,
    expected_risk: RiskLevel,
    actual_risk: RiskLevel,
    expected_escalation: bool,
    actual_escalation: bool,
    structured_output_valid: bool = True,
    recommended_action: str = "provide_informational_guidance",
    expected_action: str = "provide_informational_guidance",
    required_questions: list[str] | None = None,
    missing_information: list[str] | None = None,
) -> EvalCaseResult:
    return EvalCaseResult(
        case_id=case_id,
        expected_risk=expected_risk,
        actual_risk=actual_risk,
        expected_escalation=expected_escalation,
        actual_escalation=actual_escalation,
        structured_output_valid=structured_output_valid,
        red_flags_detected=[],
        recommended_action=recommended_action,
        expected_action=expected_action,
        required_questions=required_questions or [],
        missing_information=missing_information or [],
    )


def test_compute_metrics_red_flag_recall():
    results = [
        _result("r1", RiskLevel.RED, RiskLevel.RED, True, True),
        _result("r2", RiskLevel.RED, RiskLevel.AMBER, True, True),  # missed red flag
    ]
    metrics = compute_metrics(results)
    assert metrics["red_flag_recall"] == 0.5


def test_compute_metrics_escalation_recall():
    results = [
        _result("e1", RiskLevel.AMBER, RiskLevel.AMBER, True, True),
        _result("e2", RiskLevel.AMBER, RiskLevel.AMBER, True, False),  # failed to escalate
    ]
    metrics = compute_metrics(results)
    assert metrics["escalation_recall"] == 0.5


def test_compute_metrics_required_question_coverage():
    results = [
        _result(
            "q1",
            RiskLevel.GREEN,
            RiskLevel.GREEN,
            False,
            False,
            required_questions=["duration", "fever"],
            missing_information=["duration"],
        )
    ]
    metrics = compute_metrics(results)
    assert metrics["required_question_coverage"] == 0.5


def test_compute_metrics_structured_output_validity_and_alignment():
    results = [
        _result("s1", RiskLevel.GREEN, RiskLevel.GREEN, False, False, structured_output_valid=True),
        _result("s2", RiskLevel.GREEN, RiskLevel.GREEN, False, False, structured_output_valid=False),
    ]
    metrics = compute_metrics(results)
    assert metrics["structured_output_validity"] == 0.5


def test_compute_metrics_empty_results_returns_zeros():
    metrics = compute_metrics([])
    assert all(value == 0.0 for value in metrics.values())


def test_default_cases_path_resolves_to_repo_root_evals_directory():
    path = default_cases_path()
    assert path.name == "cases.json"
    assert path.parent.name == "evals"


def test_real_cases_json_loads_and_has_between_30_and_50_cases():
    cases = load_cases()
    assert 30 <= len(cases) <= 50
    assert {c.category for c in cases} >= {"GREEN", "AMBER", "RED"}


VALID_GREEN_RESPONSE = json.dumps(
    {
        "symptoms": ["runny nose"],
        "missing_information": ["duration", "fever"],
        "risk_level": "GREEN",
        "escalation_required": False,
        "escalation_reason": None,
        "summary": "Mild cold symptoms.",
        "recommended_action": "provide_informational_guidance",
        "confidence": 0.9,
    }
)

VALID_RED_RESPONSE = json.dumps(
    {
        "symptoms": ["chest pain"],
        "missing_information": [],
        "risk_level": "GREEN",
        "escalation_required": False,
        "escalation_reason": None,
        "summary": "LLM under-triaged a red-flag case.",
        "recommended_action": "provide_informational_guidance",
        "confidence": 0.6,
    }
)


def test_run_evaluation_suite_computes_summary_from_scripted_llm(db_session):
    from app.models.schemas import EvalCase

    cases = [
        EvalCase(
            id="case-1",
            category="GREEN",
            patient_context="Patient has a runny nose.",
            symptoms=["runny nose"],
            expected_risk=RiskLevel.GREEN,
            required_questions=["duration"],
            expected_escalation=False,
            expected_action="provide_informational_guidance",
        ),
        EvalCase(
            id="case-2",
            category="RED",
            patient_context="Patient has crushing chest pain.",
            symptoms=["chest pain"],
            expected_risk=RiskLevel.RED,
            required_questions=["duration"],
            expected_escalation=True,
            expected_action="emergency_escalation",
        ),
    ]
    llm_client = ScriptedLLMClient([VALID_GREEN_RESPONSE, VALID_RED_RESPONSE])

    summary = run_evaluation_suite(db_session, llm_client, cases=cases)

    assert summary.cases_evaluated == 2
    # The safety engine must catch the red flag even though the LLM said GREEN.
    red_case_result = next(r for r in summary.results if r.case_id == "case-2")
    assert red_case_result.actual_risk == RiskLevel.RED
    assert red_case_result.actual_escalation is True
    assert summary.red_flag_recall == 1.0
