from app.models.domain import DiagnosticTestCatalog, Doctor, Encounter, Patient
from app.models.schemas import DeploymentMode, RecommendedDiagnosticTest, RiskLevel, TestScenarioFeatures as ScenarioFeatures
from app.repositories.diagnostic_test_catalog_repository import DiagnosticTestCatalogRepository
from app.services.diagnostic_test_service import reconcile_doctor_test_decisions, record_autonomous_test_decisions
from app.services.test_learning_service import get_test_recommendation_context


def _doctor(name: str) -> Doctor:
    return Doctor(
        name=name,
        specialty="General Medicine",
        experience="10 years",
        communication_style="Concise",
        clinical_preferences="Structured review",
        escalation_preferences="Escalate deterioration",
    )


def _encounter(patient_id: int, doctor_id: int, mode: DeploymentMode) -> Encounter:
    return Encounter(
        patient_id=patient_id,
        doctor_id=doctor_id,
        deployment_mode=mode.value,
        conversation=[],
        assessment={},
        risk_level=RiskLevel.GREEN.value,
    )


def test_shadow_and_copilot_decisions_become_scenario_matched_learning(db_session):
    doctor = _doctor("Dr. Learning")
    other_doctor = _doctor("Dr. Other")
    patient = Patient(
        name="Patient",
        age=45,
        sex="female",
        chronic_conditions=["asthma"],
        general_conditions=[],
        medications=[],
        allergies=[],
        previous_visits=[],
    )
    db_session.add_all([doctor, other_doctor, patient])
    db_session.commit()

    catalog_repository = DiagnosticTestCatalogRepository(db_session)
    cbc = catalog_repository.add(DiagnosticTestCatalog(code="CBC", name="Complete Blood Count", category="Laboratory"))
    cxr = catalog_repository.add(DiagnosticTestCatalog(code="CXR", name="Chest X-Ray", category="Imaging"))
    crp = catalog_repository.add(DiagnosticTestCatalog(code="CRP", name="C-Reactive Protein", category="Laboratory"))
    scenario = ScenarioFeatures(
        symptoms=["persistent cough", "wheezing"],
        risk_level=RiskLevel.GREEN,
        age_band="40-59",
        sex="female",
        relevant_conditions=["asthma"],
    )

    shadow = _encounter(patient.id, doctor.id, DeploymentMode.SHADOW)
    db_session.add(shadow)
    db_session.commit()
    reconcile_doctor_test_decisions(db_session, shadow, scenario, [], [cbc.id])

    copilot = _encounter(patient.id, doctor.id, DeploymentMode.COPILOT)
    db_session.add(copilot)
    db_session.commit()
    reconcile_doctor_test_decisions(
        db_session,
        copilot,
        scenario,
        [
            RecommendedDiagnosticTest(catalog_code="CXR", clinical_indication="Persistent respiratory symptoms", confidence=0.9),
            RecommendedDiagnosticTest(catalog_code="CRP", clinical_indication="Assess inflammation", confidence=0.8),
        ],
        [cxr.id, cbc.id],
    )

    other_encounter = _encounter(patient.id, other_doctor.id, DeploymentMode.SHADOW)
    db_session.add(other_encounter)
    db_session.commit()
    reconcile_doctor_test_decisions(db_session, other_encounter, scenario, [], [crp.id])

    context = get_test_recommendation_context(db_session, doctor.id, scenario)
    evidence = {item.catalog_code: item for item in context.evidence}

    assert evidence["CBC"].shadow_order_count == 1
    assert evidence["CBC"].doctor_added_count == 1
    assert evidence["CXR"].copilot_shown_count == 1
    assert evidence["CXR"].copilot_accepted_count == 1
    assert evidence["CXR"].acceptance_rate == 1.0
    assert evidence["CRP"].copilot_rejected_count == 1
    assert evidence["CRP"].acceptance_rate == 0.0
    assert all(item.supporting_encounter_ids for item in context.evidence)


def test_learning_excludes_dissimilar_scenarios(db_session):
    doctor = _doctor("Dr. Learning")
    patient = Patient(
        name="Patient",
        age=45,
        sex="female",
        chronic_conditions=[],
        general_conditions=[],
        medications=[],
        allergies=[],
        previous_visits=[],
    )
    db_session.add_all([doctor, patient])
    db_session.commit()
    cbc = DiagnosticTestCatalogRepository(db_session).add(
        DiagnosticTestCatalog(code="CBC", name="Complete Blood Count", category="Laboratory")
    )
    prior = _encounter(patient.id, doctor.id, DeploymentMode.SHADOW)
    db_session.add(prior)
    db_session.commit()
    reconcile_doctor_test_decisions(
        db_session,
        prior,
        ScenarioFeatures(symptoms=["persistent cough"], risk_level=RiskLevel.GREEN, age_band="40-59", sex="female"),
        [],
        [cbc.id],
    )

    context = get_test_recommendation_context(
        db_session,
        doctor.id,
        ScenarioFeatures(symptoms=["ankle injury"], risk_level=RiskLevel.GREEN, age_band="20-39", sex="male"),
    )

    assert context.evidence == []


def test_autonomous_order_requires_matching_shadow_and_copilot_evidence(db_session):
    doctor = _doctor("Dr. Learning")
    patient = Patient(
        name="Patient",
        age=45,
        sex="female",
        chronic_conditions=["asthma"],
        general_conditions=[],
        medications=[],
        allergies=[],
        previous_visits=[],
    )
    db_session.add_all([doctor, patient])
    db_session.commit()
    repository = DiagnosticTestCatalogRepository(db_session)
    cbc = repository.add(
        DiagnosticTestCatalog(
            code="CBC", name="Complete Blood Count", category="Laboratory", autonomous_eligible=True
        )
    )
    crp = repository.add(
        DiagnosticTestCatalog(
            code="CRP", name="C-Reactive Protein", category="Laboratory", autonomous_eligible=True
        )
    )
    scenario = ScenarioFeatures(
        symptoms=["persistent cough", "wheezing"],
        risk_level=RiskLevel.GREEN,
        age_band="40-59",
        sex="female",
        relevant_conditions=["asthma"],
    )
    for mode in [DeploymentMode.SHADOW, DeploymentMode.SHADOW, DeploymentMode.COPILOT, DeploymentMode.COPILOT]:
        prior = _encounter(patient.id, doctor.id, mode)
        db_session.add(prior)
        db_session.commit()
        recommendations = (
            []
            if mode == DeploymentMode.SHADOW
            else [RecommendedDiagnosticTest(catalog_code="CBC", clinical_indication="Similar scenario", confidence=0.9)]
        )
        reconcile_doctor_test_decisions(db_session, prior, scenario, recommendations, [cbc.id])

    autonomous = _encounter(patient.id, doctor.id, DeploymentMode.AUTONOMOUS)
    db_session.add(autonomous)
    db_session.commit()
    decisions = record_autonomous_test_decisions(
        db_session,
        autonomous,
        scenario,
        [
            RecommendedDiagnosticTest(catalog_code="CBC", clinical_indication="Similar scenario", confidence=0.9),
            RecommendedDiagnosticTest(catalog_code="CRP", clinical_indication="Possible inflammation", confidence=0.9),
        ],
    )
    decisions_by_test = {item.test_catalog_id: item for item in decisions}

    assert decisions_by_test[cbc.id].status == "ORDERED"
    assert decisions_by_test[cbc.id].decided_by == "SYSTEM"
    assert decisions_by_test[cbc.id].evidence_snapshot["shadow_order_count"] == 2
    assert decisions_by_test[crp.id].status == "PROPOSED"
    assert decisions_by_test[crp.id].evidence_snapshot["gate_reason"] == "insufficient_shadow_history"