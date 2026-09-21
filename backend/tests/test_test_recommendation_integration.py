import json

from app.agents.doctor_twin import DoctorTwin
from app.models.domain import DiagnosticTestCatalog, Encounter, EncounterTestDecision
from app.models.schemas import ConsultationReviewRequest, DeploymentMode, RiskLevel, TestScenarioFeatures as ScenarioFeatures
from app.repositories.diagnostic_test_catalog_repository import DiagnosticTestCatalogRepository
from app.services.diagnostic_test_service import reconcile_doctor_test_decisions
from app.services.consultation_service import review_consultation, start_consultation


class RecommendationLLMClient:
    def __init__(self) -> None:
        self.recommendation_prompts: list[str] = []

    def generate_assessment(self, system_instruction: str, prompt: str) -> str:
        return json.dumps(
            {
                "symptoms": ["persistent cough", "wheezing"],
                "missing_information": [],
                "risk_level": "GREEN",
                "escalation_required": False,
                "escalation_reason": None,
                "summary": "Persistent respiratory symptoms.",
                "recommended_action": "provide_informational_guidance",
                "confidence": 0.9,
            }
        )

    def generate_test_recommendations(self, system_instruction: str, prompt: str) -> str:
        self.recommendation_prompts.append(prompt)
        return json.dumps(
            {
                "recommendations": [
                    {
                        "catalog_code": "CBC",
                        "clinical_indication": "Previously selected for similar respiratory presentations.",
                        "confidence": 0.88,
                        "evidence_summary": "One similar Shadow selection.",
                    },
                    {
                        "catalog_code": "UNKNOWN",
                        "clinical_indication": "Not in the hospital catalog.",
                        "confidence": 0.99,
                    },
                ]
            }
        )


class RedCaseRecommendationLLMClient(RecommendationLLMClient):
    def generate_assessment(self, system_instruction: str, prompt: str) -> str:
        return json.dumps(
            {
                "symptoms": ["crushing chest pain"],
                "missing_information": [],
                "risk_level": "RED",
                "escalation_required": True,
                "escalation_reason": "Urgent assessment required.",
                "summary": "Crushing chest pain requiring emergency assessment.",
                "recommended_action": "seek_emergency_care",
                "confidence": 0.98,
            }
        )


def test_copilot_red_safety_case_keeps_catalog_test_recommendations(seeded):
    session = seeded["session"]
    doctor = seeded["doctor"]
    patient = seeded["patient"]
    doctor.default_deployment_mode = DeploymentMode.COPILOT.value
    session.commit()
    DiagnosticTestCatalogRepository(session).add(
        DiagnosticTestCatalog(code="CBC", name="Complete Blood Count", category="Laboratory")
    )

    response = start_consultation(
        session,
        doctor.id,
        patient.id,
        "I have crushing chest pain",
        RedCaseRecommendationLLMClient(),
    )

    assert response.risk_level == RiskLevel.RED
    assert response.escalation_reason.startswith("Safety engine override")
    assert [item.catalog_code for item in response.assessment.recommended_tests] == ["CBC"]


def test_copilot_recommendation_uses_matching_shadow_decision_context(seeded):
    session = seeded["session"]
    doctor = seeded["doctor"]
    patient = seeded["patient"]
    cbc = DiagnosticTestCatalogRepository(session).add(
        DiagnosticTestCatalog(code="CBC", name="Complete Blood Count", category="Laboratory")
    )
    prior = Encounter(
        patient_id=patient.id,
        doctor_id=doctor.id,
        deployment_mode=DeploymentMode.SHADOW.value,
        conversation=[],
        assessment={},
        risk_level=RiskLevel.GREEN.value,
    )
    session.add(prior)
    session.commit()
    reconcile_doctor_test_decisions(
        session,
        prior,
        ScenarioFeatures(
            symptoms=["persistent cough", "wheezing"],
            risk_level=RiskLevel.GREEN,
            age_band="40-59",
            sex=patient.sex,
            relevant_conditions=patient.chronic_conditions,
        ),
        [],
        [cbc.id],
    )
    llm = RecommendationLLMClient()
    twin = DoctorTwin(
        session=session,
        doctor_id=doctor.id,
        llm_client=llm,
        deployment_mode=DeploymentMode.COPILOT,
    )

    assessment = twin.run(patient.id, [{"role": "patient", "content": "Persistent cough and wheezing"}])

    assert [item.catalog_code for item in assessment.recommended_tests] == ["CBC"]
    assert len(llm.recommendation_prompts) == 1
    assert '"shadow_order_count": 1' in llm.recommendation_prompts[0]
    assert "Complete Blood Count" in llm.recommendation_prompts[0]


def test_copilot_review_records_acceptance_rejection_and_replacement(seeded):
    session = seeded["session"]
    doctor = seeded["doctor"]
    patient = seeded["patient"]
    doctor.default_deployment_mode = DeploymentMode.COPILOT.value
    session.commit()
    repository = DiagnosticTestCatalogRepository(session)
    cbc = repository.add(DiagnosticTestCatalog(code="CBC", name="Complete Blood Count", category="Laboratory"))
    cxr = repository.add(DiagnosticTestCatalog(code="CXR", name="Chest X-Ray", category="Imaging"))
    encounter = Encounter(
        patient_id=patient.id,
        doctor_id=doctor.id,
        deployment_mode=DeploymentMode.COPILOT.value,
        conversation=[{"role": "patient", "content": "Persistent cough and wheezing"}],
        assessment={
            "symptoms": ["persistent cough", "wheezing"],
            "missing_information": [],
            "risk_level": "GREEN",
            "escalation_required": False,
            "escalation_reason": None,
            "summary": "Persistent respiratory symptoms.",
            "recommended_action": "provide_informational_guidance",
            "confidence": 0.9,
            "recommended_tests": [
                {
                    "catalog_code": "CXR",
                    "clinical_indication": "Persistent respiratory symptoms.",
                    "confidence": 0.85,
                }
            ],
        },
        risk_level=RiskLevel.GREEN.value,
        summary="Persistent respiratory symptoms.",
    )
    session.add(encounter)
    session.commit()

    response = review_consultation(
        session,
        encounter.id,
        ConsultationReviewRequest(action="modify", selected_test_ids=[cbc.id]),
    )

    decisions = {item.catalog_code: item for item in response.test_decisions}
    assert decisions["CXR"].status == "REJECTED"
    assert decisions["CXR"].origin == "AGENT_RECOMMENDED"
    assert decisions["CBC"].status == "ORDERED"
    assert decisions["CBC"].origin == "DOCTOR_SELECTED"
    assert response.doctor_reviewed is True


def test_autonomous_review_finalizes_proposal_and_preserves_evidence(seeded):
    session = seeded["session"]
    doctor = seeded["doctor"]
    patient = seeded["patient"]
    cbc = DiagnosticTestCatalogRepository(session).add(
        DiagnosticTestCatalog(code="CBC", name="Complete Blood Count", category="Laboratory")
    )
    encounter = Encounter(
        patient_id=patient.id,
        doctor_id=doctor.id,
        deployment_mode=DeploymentMode.AUTONOMOUS.value,
        conversation=[],
        assessment={
            "symptoms": ["persistent cough"],
            "missing_information": [],
            "risk_level": "GREEN",
            "escalation_required": False,
            "summary": "Persistent cough.",
            "recommended_action": "provide_informational_guidance",
            "confidence": 0.9,
            "recommended_tests": [
                {"catalog_code": "CBC", "clinical_indication": "Similar scenario", "confidence": 0.9}
            ],
        },
        risk_level="GREEN",
        summary="Persistent cough.",
    )
    session.add(encounter)
    session.commit()
    session.add(
        EncounterTestDecision(
            encounter_id=encounter.id,
            doctor_id=doctor.id,
            test_catalog_id=cbc.id,
            deployment_mode="AUTONOMOUS",
            origin="AGENT_RECOMMENDED",
            status="PROPOSED",
            decided_by="SYSTEM",
            clinical_indication="Similar scenario",
            model_confidence=0.9,
            scenario_features={"symptoms": ["persistent cough"], "risk_level": "GREEN", "age_band": "40-59", "sex": patient.sex, "relevant_conditions": []},
            evidence_snapshot={"gate_reason": "insufficient_copilot_history", "shadow_order_count": 2},
        )
    )
    session.commit()

    response = review_consultation(
        session,
        encounter.id,
        ConsultationReviewRequest(action="approve", selected_test_ids=[cbc.id]),
    )

    assert response.test_decisions[0].status == "ORDERED"
    assert response.test_decisions[0].decided_by == "DOCTOR"
    assert response.test_decisions[0].evidence_snapshot["gate_reason"] == "insufficient_copilot_history"


def test_copilot_review_can_select_zero_tests(seeded):
    session = seeded["session"]
    doctor = seeded["doctor"]
    patient = seeded["patient"]
    DiagnosticTestCatalogRepository(session).add(
        DiagnosticTestCatalog(code="CBC", name="Complete Blood Count", category="Laboratory")
    )
    encounter = Encounter(
        patient_id=patient.id,
        doctor_id=doctor.id,
        deployment_mode=DeploymentMode.COPILOT.value,
        conversation=[],
        assessment={
            "symptoms": ["fatigue"],
            "missing_information": [],
            "risk_level": "GREEN",
            "escalation_required": False,
            "summary": "Fatigue.",
            "recommended_action": "provide_informational_guidance",
            "confidence": 0.8,
            "recommended_tests": [
                {"catalog_code": "CBC", "clinical_indication": "Assess blood count", "confidence": 0.8}
            ],
        },
        risk_level="GREEN",
        summary="Fatigue.",
    )
    session.add(encounter)
    session.commit()

    response = review_consultation(
        session,
        encounter.id,
        ConsultationReviewRequest(action="modify", selected_test_ids=[]),
    )

    assert len(response.test_decisions) == 1
    assert response.test_decisions[0].status == "REJECTED"