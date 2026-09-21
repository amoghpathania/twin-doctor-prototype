import re
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.schemas import (
    DeploymentMode,
    TestDecisionEvidence,
    TestDecisionOrigin,
    TestDecisionStatus,
    TestRecommendationContext,
    TestScenarioFeatures,
)
from app.repositories.diagnostic_test_catalog_repository import DiagnosticTestCatalogRepository
from app.repositories.encounter_test_decision_repository import EncounterTestDecisionRepository

MIN_SCENARIO_SIMILARITY = 0.45


def build_test_scenario_features(patient, assessment) -> TestScenarioFeatures:
    if patient.age < 18:
        age_band = "0-17"
    elif patient.age < 40:
        age_band = "18-39"
    elif patient.age < 60:
        age_band = "40-59"
    else:
        age_band = "60+"
    return TestScenarioFeatures(
        symptoms=assessment.symptoms,
        risk_level=assessment.risk_level,
        age_band=age_band,
        sex=patient.sex,
        relevant_conditions=[*patient.chronic_conditions, *patient.general_conditions],
    )


def _tokens(values: list[str]) -> set[str]:
    return {token for value in values for token in re.findall(r"[a-z0-9]+", value.casefold())}


def _jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left or right else 1.0


def _scenario_similarity(current: TestScenarioFeatures, stored_data: dict) -> float:
    stored = TestScenarioFeatures.model_validate(stored_data)
    symptom_similarity = _jaccard(_tokens(current.symptoms), _tokens(stored.symptoms))
    if symptom_similarity == 0:
        return 0.0
    condition_similarity = _jaccard(_tokens(current.relevant_conditions), _tokens(stored.relevant_conditions))
    score = (
        0.65 * symptom_similarity
        + 0.15 * condition_similarity
        + 0.1 * float(current.risk_level == stored.risk_level)
        + 0.05 * float(current.age_band == stored.age_band)
        + 0.05 * float(current.sex.casefold() == stored.sex.casefold())
    )
    return round(score, 4)


def get_test_recommendation_context(
    session: Session, doctor_id: int, scenario: TestScenarioFeatures
) -> TestRecommendationContext:
    decisions = EncounterTestDecisionRepository(session).list_learning_decisions(doctor_id)
    catalog_repository = DiagnosticTestCatalogRepository(session)
    aggregates: dict[int, dict] = defaultdict(
        lambda: {
            "similarity_score": 0.0,
            "shadow_order_count": 0,
            "copilot_shown_count": 0,
            "copilot_accepted_count": 0,
            "copilot_rejected_count": 0,
            "doctor_added_count": 0,
            "supporting_encounter_ids": set(),
        }
    )

    for decision in decisions:
        similarity = _scenario_similarity(scenario, decision.scenario_features)
        if similarity < MIN_SCENARIO_SIMILARITY:
            continue
        catalog_item = catalog_repository.get_by_id(decision.test_catalog_id)
        if catalog_item is None or not catalog_item.is_active:
            continue
        aggregate = aggregates[decision.test_catalog_id]
        aggregate["similarity_score"] = max(aggregate["similarity_score"], similarity)
        aggregate["supporting_encounter_ids"].add(decision.encounter_id)
        if decision.deployment_mode == DeploymentMode.SHADOW.value and decision.status == TestDecisionStatus.ORDERED.value:
            aggregate["shadow_order_count"] += 1
        elif decision.deployment_mode == DeploymentMode.COPILOT.value:
            if decision.origin == TestDecisionOrigin.AGENT_RECOMMENDED.value:
                aggregate["copilot_shown_count"] += 1
                if decision.status == TestDecisionStatus.ORDERED.value:
                    aggregate["copilot_accepted_count"] += 1
                elif decision.status == TestDecisionStatus.REJECTED.value:
                    aggregate["copilot_rejected_count"] += 1
            elif decision.status == TestDecisionStatus.ORDERED.value:
                aggregate["doctor_added_count"] += 1

    evidence = []
    for test_id, aggregate in aggregates.items():
        catalog_item = catalog_repository.get_by_id(test_id)
        shown = aggregate["copilot_shown_count"]
        evidence.append(
            TestDecisionEvidence(
                catalog_id=test_id,
                catalog_code=catalog_item.code,
                acceptance_rate=aggregate["copilot_accepted_count"] / shown if shown else None,
                **{**aggregate, "supporting_encounter_ids": sorted(aggregate["supporting_encounter_ids"])},
            )
        )
    evidence.sort(
        key=lambda item: (
            -item.similarity_score,
            -(item.shadow_order_count + item.copilot_accepted_count + item.doctor_added_count),
            item.catalog_code,
        )
    )
    return TestRecommendationContext(evidence=evidence)