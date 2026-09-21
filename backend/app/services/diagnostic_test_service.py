from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.domain import Encounter, EncounterTestDecision
from app.models.schemas import (
    DeploymentMode,
    RecommendedDiagnosticTest,
    TestDecisionActor,
    TestDecisionOrigin,
    TestDecisionStatus,
    TestScenarioFeatures,
)
from app.repositories.diagnostic_test_catalog_repository import DiagnosticTestCatalogRepository
from app.repositories.encounter_test_decision_repository import EncounterTestDecisionRepository
from app.services.test_learning_service import get_test_recommendation_context


def reconcile_doctor_test_decisions(
    session: Session,
    encounter: Encounter,
    scenario: TestScenarioFeatures,
    recommendations: list[RecommendedDiagnosticTest],
    selected_test_ids: list[int],
) -> list[EncounterTestDecision]:
    catalog_repository = DiagnosticTestCatalogRepository(session)
    selected = {
        test_id: catalog_item
        for test_id in dict.fromkeys(selected_test_ids)
        if (catalog_item := catalog_repository.get_by_id(test_id)) is not None and catalog_item.is_active
    }
    recommendations_by_id = {}
    for recommendation in recommendations:
        catalog_item = catalog_repository.get_by_code(recommendation.catalog_code)
        if catalog_item is not None and catalog_item.is_active:
            recommendations_by_id[catalog_item.id] = recommendation

    now = datetime.now(timezone.utc)
    scenario_data = scenario.model_dump(mode="json")
    decisions = []
    for test_id, recommendation in recommendations_by_id.items():
        decisions.append(
            EncounterTestDecision(
                encounter_id=encounter.id,
                doctor_id=encounter.doctor_id,
                test_catalog_id=test_id,
                deployment_mode=encounter.deployment_mode,
                origin=TestDecisionOrigin.AGENT_RECOMMENDED.value,
                status=(TestDecisionStatus.ORDERED if test_id in selected else TestDecisionStatus.REJECTED).value,
                decided_by=TestDecisionActor.DOCTOR.value,
                clinical_indication=recommendation.clinical_indication,
                model_confidence=recommendation.confidence,
                scenario_features=scenario_data,
                evidence_snapshot={},
                decided_at=now,
            )
        )

    for test_id in selected.keys() - recommendations_by_id.keys():
        decisions.append(
            EncounterTestDecision(
                encounter_id=encounter.id,
                doctor_id=encounter.doctor_id,
                test_catalog_id=test_id,
                deployment_mode=encounter.deployment_mode,
                origin=TestDecisionOrigin.DOCTOR_SELECTED.value,
                status=TestDecisionStatus.ORDERED.value,
                decided_by=TestDecisionActor.DOCTOR.value,
                scenario_features=scenario_data,
                evidence_snapshot={},
                decided_at=now,
            )
        )

    return EncounterTestDecisionRepository(session).replace_for_encounter(encounter.id, decisions)


def record_autonomous_test_decisions(
    session: Session,
    encounter: Encounter,
    scenario: TestScenarioFeatures,
    recommendations: list[RecommendedDiagnosticTest],
    safety_eligible: bool = True,
) -> list[EncounterTestDecision]:
    settings = get_settings()
    catalog_repository = DiagnosticTestCatalogRepository(session)
    context = get_test_recommendation_context(session, encounter.doctor_id, scenario)
    evidence_by_code = {item.catalog_code: item for item in context.evidence}
    decisions = []
    now = datetime.now(timezone.utc)

    for recommendation in recommendations:
        catalog_item = catalog_repository.get_by_code(recommendation.catalog_code)
        if catalog_item is None or not catalog_item.is_active:
            continue
        evidence = evidence_by_code.get(catalog_item.code)
        evidence_snapshot = evidence.model_dump(mode="json") if evidence is not None else {
            "catalog_id": catalog_item.id,
            "catalog_code": catalog_item.code,
            "similarity_score": 0.0,
            "shadow_order_count": 0,
            "copilot_shown_count": 0,
            "copilot_accepted_count": 0,
            "copilot_rejected_count": 0,
            "doctor_added_count": 0,
            "acceptance_rate": None,
            "supporting_encounter_ids": [],
        }

        if not safety_eligible or scenario.risk_level != "GREEN":
            gate_reason = "clinical_safety_gate"
        elif not catalog_item.autonomous_eligible:
            gate_reason = "catalog_not_autonomous_eligible"
        elif recommendation.confidence < settings.autonomous_test_min_confidence:
            gate_reason = "low_model_confidence"
        elif evidence is None or evidence.shadow_order_count < settings.autonomous_test_min_shadow_orders:
            gate_reason = "insufficient_shadow_history"
        elif evidence.copilot_shown_count < settings.autonomous_test_min_copilot_decisions:
            gate_reason = "insufficient_copilot_history"
        elif (
            evidence.acceptance_rate is None
            or evidence.acceptance_rate < settings.autonomous_test_min_copilot_acceptance
        ):
            gate_reason = "copilot_acceptance_below_threshold"
        else:
            gate_reason = "eligible"

        evidence_snapshot["gate_reason"] = gate_reason
        decisions.append(
            EncounterTestDecision(
                encounter_id=encounter.id,
                doctor_id=encounter.doctor_id,
                test_catalog_id=catalog_item.id,
                deployment_mode=encounter.deployment_mode,
                origin=TestDecisionOrigin.AGENT_RECOMMENDED.value,
                status=(TestDecisionStatus.ORDERED if gate_reason == "eligible" else TestDecisionStatus.PROPOSED).value,
                decided_by=TestDecisionActor.SYSTEM.value,
                clinical_indication=recommendation.clinical_indication,
                model_confidence=recommendation.confidence,
                scenario_features=scenario.model_dump(mode="json"),
                evidence_snapshot=evidence_snapshot,
                decided_at=now if gate_reason == "eligible" else None,
            )
        )

    return EncounterTestDecisionRepository(session).replace_for_encounter(encounter.id, decisions)


def finalize_autonomous_test_decisions(
    session: Session, encounter: Encounter, scenario: TestScenarioFeatures, selected_test_ids: list[int]
) -> list[EncounterTestDecision]:
    repository = EncounterTestDecisionRepository(session)
    catalog_repository = DiagnosticTestCatalogRepository(session)
    existing = {item.test_catalog_id: item for item in repository.list_by_encounter(encounter.id)}
    selected = set(dict.fromkeys(selected_test_ids))
    now = datetime.now(timezone.utc)
    decisions = []

    for test_id, decision in existing.items():
        decision.status = (
            TestDecisionStatus.ORDERED.value if test_id in selected else TestDecisionStatus.REJECTED.value
        )
        decision.decided_by = TestDecisionActor.DOCTOR.value
        decision.decided_at = now
        decisions.append(decision)

    for test_id in selected - existing.keys():
        catalog_item = catalog_repository.get_by_id(test_id)
        if catalog_item is None or not catalog_item.is_active:
            continue
        decisions.append(
            EncounterTestDecision(
                encounter_id=encounter.id,
                doctor_id=encounter.doctor_id,
                test_catalog_id=test_id,
                deployment_mode=encounter.deployment_mode,
                origin=TestDecisionOrigin.DOCTOR_SELECTED.value,
                status=TestDecisionStatus.ORDERED.value,
                decided_by=TestDecisionActor.DOCTOR.value,
                scenario_features=scenario.model_dump(mode="json"),
                evidence_snapshot={},
                decided_at=now,
            )
        )

    return repository.save_all(decisions)