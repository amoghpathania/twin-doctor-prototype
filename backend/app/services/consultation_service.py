"""Consultation orchestration: Patient -> Doctor Twin -> Safety -> Deployment mode."""

from datetime import datetime, timezone

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.agents.deployment_policy import evaluate_deployment_policy
from app.agents.doctor_twin import DoctorTwin
from app.agents.llm_client import LLMClient
from app.memory.extraction import extract_candidate_memories
from app.models.domain import Encounter
from app.models.schemas import (
    ClinicalAssessment,
    ConsultationResponse,
    ConsultationReviewRequest,
    DeploymentMode,
    EncounterTestDecisionRead,
    RiskLevel,
)
from app.repositories.diagnostic_test_catalog_repository import DiagnosticTestCatalogRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.encounter_repository import EncounterRepository
from app.repositories.encounter_test_decision_repository import EncounterTestDecisionRepository
from app.repositories.patient_repository import PatientRepository
from app.safety.policy import apply_safety_policy
from app.safety.red_flags import detect_conversation_red_flags
from app.services.audit_service import record_event
from app.services.diagnostic_test_service import (
    finalize_autonomous_test_decisions,
    reconcile_doctor_test_decisions,
    record_autonomous_test_decisions,
)
from app.services.test_learning_service import build_test_scenario_features
from app.tools import clinic_tools


class ConsultationStateError(ValueError):
    """Raised when an encounter lifecycle transition is not allowed."""


def _run_twin_and_safety(
    session: Session,
    doctor_id: int,
    patient_id: int,
    llm_client: LLMClient,
    conversation: list[dict],
    deployment_mode: DeploymentMode,
):
    twin = DoctorTwin(
        session=session,
        doctor_id=doctor_id,
        llm_client=llm_client,
        deployment_mode=deployment_mode,
    )
    assessment = twin.run(patient_id=patient_id, conversation=conversation)

    red_flags = detect_conversation_red_flags(conversation)
    final_assessment = apply_safety_policy(assessment, red_flags)
    return final_assessment, red_flags


def parse_stored_assessment(assessment_data: dict) -> ClinicalAssessment:
    """Defensive parse for a persisted encounter.assessment blob - one corrupted/incomplete row
    (e.g. left behind by an LLM call that failed before the encounter was ever updated) must never
    crash an entire doctor's case list; escalate it for review instead, same fail-safe philosophy
    as DoctorTwin's own invalid-output handling."""
    try:
        return ClinicalAssessment.model_validate(assessment_data)
    except ValidationError:
        return ClinicalAssessment(
            symptoms=[],
            missing_information=[],
            risk_level=RiskLevel.AMBER,
            escalation_required=True,
            escalation_reason="Stored assessment could not be read; escalating rather than showing incomplete data",
            summary="This case's stored assessment could not be read and needs doctor review.",
            recommended_action="escalate_to_doctor",
            confidence=0.0,
            fallback_used=True,
        )


def build_consultation_response(
    session: Session, encounter: Encounter, assessment, deployment_mode: DeploymentMode
) -> ConsultationResponse:
    decision = evaluate_deployment_policy(deployment_mode, assessment)
    # Offer scheduling only after intake questions are complete and a genuine escalation requires review.
    available_slots = (
        clinic_tools.get_available_slots(session, encounter.doctor_id)
        if assessment.risk_level == RiskLevel.AMBER
        and assessment.escalation_required
        and not assessment.missing_information
        and not assessment.fallback_used
        else []
    )
    catalog_repository = DiagnosticTestCatalogRepository(session)
    test_decisions = []
    for item in EncounterTestDecisionRepository(session).list_by_encounter(encounter.id):
        catalog_item = catalog_repository.get_by_id(item.test_catalog_id)
        if catalog_item is None:
            continue
        test_decisions.append(
            EncounterTestDecisionRead(
                id=item.id,
                test_catalog_id=item.test_catalog_id,
                catalog_code=catalog_item.code,
                test_name=catalog_item.name,
                category=catalog_item.category,
                deployment_mode=item.deployment_mode,
                origin=item.origin,
                status=item.status,
                decided_by=item.decided_by,
                clinical_indication=item.clinical_indication,
                model_confidence=item.model_confidence,
                evidence_snapshot=item.evidence_snapshot,
                decided_at=item.decided_at,
            )
        )
    return ConsultationResponse(
        id=encounter.id,
        doctor_id=encounter.doctor_id,
        patient_id=encounter.patient_id,
        deployment_mode=deployment_mode,
        conversation=encounter.conversation,
        assessment=assessment,
        risk_level=assessment.risk_level,
        escalation_required=assessment.escalation_required,
        escalation_reason=assessment.escalation_reason,
        summary=assessment.summary,
        appointment_id=encounter.appointment_id,
        deployment_decision=decision,
        available_slots=available_slots,
        doctor_reviewed=encounter.doctor_reviewed,
        doctor_review_action=encounter.doctor_review_action,
        closed_at=encounter.closed_at,
        created_at=encounter.created_at,
        test_decisions=test_decisions,
    )


def _persist_and_respond(
    session: Session,
    encounter: Encounter,
    deployment_mode: DeploymentMode,
    assessment,
    red_flags: list[str],
) -> ConsultationResponse:
    encounter.assessment = assessment.model_dump(mode="json")
    encounter.risk_level = assessment.risk_level.value
    encounter.escalation_required = assessment.escalation_required
    encounter.escalation_reason = assessment.escalation_reason
    encounter.summary = assessment.summary
    EncounterRepository(session).update(encounter)

    if deployment_mode == DeploymentMode.AUTONOMOUS and assessment.recommended_tests:
        patient = PatientRepository(session).get_by_id(encounter.patient_id)
        if patient is not None:
            decisions = record_autonomous_test_decisions(
                session,
                encounter,
                build_test_scenario_features(patient, assessment),
                assessment.recommended_tests,
                safety_eligible=(
                    assessment.risk_level == RiskLevel.GREEN
                    and not assessment.escalation_required
                    and not assessment.missing_information
                    and not assessment.fallback_used
                ),
            )
            record_event(
                session,
                event_type="autonomous_test_decisions_evaluated",
                encounter_id=encounter.id,
                payload={
                    "decisions": [
                        {
                            "decision_id": item.id,
                            "test_catalog_id": item.test_catalog_id,
                            "status": item.status,
                            "gate_reason": item.evidence_snapshot.get("gate_reason"),
                        }
                        for item in decisions
                    ]
                },
            )

    if red_flags:
        record_event(
            session,
            event_type="safety_override",
            encounter_id=encounter.id,
            payload={"red_flags": red_flags, "final_risk_level": assessment.risk_level.value},
        )
    if assessment.escalation_required:
        record_event(
            session,
            event_type="escalation",
            encounter_id=encounter.id,
            payload={"reason": assessment.escalation_reason},
        )

    return build_consultation_response(session, encounter, assessment, deployment_mode)


def start_consultation(
    session: Session,
    doctor_id: int,
    patient_id: int,
    message: str,
    llm_client: LLMClient,
) -> ConsultationResponse:
    doctor = DoctorRepository(session).get_by_id(doctor_id)
    if doctor is None:
        raise ValueError("Doctor not found")
    deployment_mode = DeploymentMode(doctor.default_deployment_mode)

    conversation = [{"role": "patient", "content": message}]
    encounter = Encounter(
        patient_id=patient_id,
        doctor_id=doctor_id,
        deployment_mode=deployment_mode.value,
        conversation=conversation,
        risk_level="GREEN",
    )
    encounter = EncounterRepository(session).add(encounter)

    assessment, red_flags = _run_twin_and_safety(
        session, doctor_id, patient_id, llm_client, conversation, deployment_mode
    )
    return _persist_and_respond(session, encounter, deployment_mode, assessment, red_flags)


def add_consultation_message(
    session: Session,
    encounter_id: int,
    message: str,
    llm_client: LLMClient,
) -> ConsultationResponse:
    encounter = EncounterRepository(session).get_by_id(encounter_id)
    if encounter is None:
        raise ValueError("Encounter not found")
    if encounter.closed_at is not None:
        raise ConsultationStateError("Closed consultations cannot accept new messages")

    conversation = list(encounter.conversation)
    prior_assessment = ClinicalAssessment.model_validate(encounter.assessment) if encounter.assessment else None
    if prior_assessment and prior_assessment.missing_information:
        # Persist the twin's question that prompted this reply, so history is a real back-and-forth.
        conversation.append({"role": "twin", "content": prior_assessment.missing_information[0]})
    conversation.append({"role": "patient", "content": message})
    encounter.conversation = conversation
    encounter.doctor_reviewed = False
    encounter.doctor_review_action = None
    EncounterRepository(session).update(encounter)

    deployment_mode = DeploymentMode(encounter.deployment_mode)
    assessment, red_flags = _run_twin_and_safety(
        session, encounter.doctor_id, encounter.patient_id, llm_client, conversation, deployment_mode
    )
    return _persist_and_respond(session, encounter, deployment_mode, assessment, red_flags)


def review_consultation(session: Session, encounter_id: int, review: ConsultationReviewRequest) -> ConsultationResponse:
    """Doctor approves the AI assessment as-is, or modifies specific fields - the doctor is the final authority."""
    encounter = EncounterRepository(session).get_by_id(encounter_id)
    if encounter is None:
        raise ValueError("Encounter not found")
    if encounter.closed_at is not None:
        raise ConsultationStateError("Closed consultations cannot be reviewed")

    assessment = ClinicalAssessment.model_validate(encounter.assessment)
    before_assessment = assessment.model_dump(mode="json")

    if review.action == "modify":
        overrides = {
            field: value
            for field, value in {
                "risk_level": review.risk_level,
                "escalation_required": review.escalation_required,
                "escalation_reason": review.escalation_reason,
                "summary": review.summary,
                "recommended_action": review.recommended_action,
            }.items()
            if value is not None
        }
        assessment = assessment.model_copy(update=overrides)

    encounter.assessment = assessment.model_dump(mode="json")
    encounter.risk_level = assessment.risk_level.value
    encounter.escalation_required = assessment.escalation_required
    encounter.escalation_reason = assessment.escalation_reason
    encounter.summary = assessment.summary
    encounter.doctor_reviewed = True
    encounter.doctor_review_action = review.action
    EncounterRepository(session).update(encounter)

    deployment_mode = DeploymentMode(encounter.deployment_mode)
    if deployment_mode in (DeploymentMode.SHADOW, DeploymentMode.COPILOT, DeploymentMode.AUTONOMOUS):
        patient = PatientRepository(session).get_by_id(encounter.patient_id)
        if patient is None:
            raise ValueError("Patient not found")
        catalog_repository = DiagnosticTestCatalogRepository(session)
        selected_test_ids = review.selected_test_ids
        if selected_test_ids is None:
            selected_test_ids = [
                catalog_item.id
                for recommendation in assessment.recommended_tests
                if (catalog_item := catalog_repository.get_by_code(recommendation.catalog_code)) is not None
            ]
        scenario = build_test_scenario_features(patient, assessment)
        test_decisions = (
            finalize_autonomous_test_decisions(session, encounter, scenario, selected_test_ids)
            if deployment_mode == DeploymentMode.AUTONOMOUS
            else reconcile_doctor_test_decisions(
                session,
                encounter,
                scenario,
                assessment.recommended_tests,
                selected_test_ids,
            )
        )
        record_event(
            session,
            event_type="doctor_finalized_test_decisions",
            encounter_id=encounter.id,
            payload={
                "mode": deployment_mode.value,
                "decision_ids": [item.id for item in test_decisions],
                "selected_test_ids": selected_test_ids,
            },
        )

    record_event(
        session,
        event_type="doctor_approved_assessment" if review.action == "approve" else "doctor_modified_assessment",
        encounter_id=encounter.id,
        payload={
            "action": review.action,
            "before_assessment": before_assessment,
            "final_assessment": encounter.assessment,
        },
    )

    return build_consultation_response(session, encounter, assessment, deployment_mode)


def close_consultation(session: Session, encounter_id: int, llm_client: LLMClient) -> ConsultationResponse:
    encounter = EncounterRepository(session).get_by_id(encounter_id)
    if encounter is None:
        raise ValueError("Encounter not found")
    if encounter.closed_at is not None:
        assessment = parse_stored_assessment(encounter.assessment)
        return build_consultation_response(session, encounter, assessment, DeploymentMode(encounter.deployment_mode))
    if not encounter.doctor_reviewed:
        raise ConsultationStateError("Consultation must be reviewed before it can be closed")

    encounter.closed_at = datetime.now(timezone.utc)
    EncounterRepository(session).update(encounter)

    review_event = AuditRepository(session).latest_review_for_encounter(encounter.id)
    payload = review_event.payload if review_event is not None else {}
    final_assessment = payload.get("final_assessment", payload.get("assessment", encounter.assessment))
    before_assessment = payload.get("before_assessment", final_assessment)
    review_action = payload.get("action", encounter.doctor_review_action or "approve")
    doctor = DoctorRepository(session).get_by_id(encounter.doctor_id)

    try:
        if doctor is None:
            raise ValueError("Doctor not found")
        candidates = extract_candidate_memories(
            session,
            doctor,
            encounter,
            before_assessment,
            final_assessment,
            review_action,
            llm_client,
        )
        record_event(
            session,
            event_type="case_closed",
            encounter_id=encounter.id,
            payload={
                "extraction_status": "completed",
                "candidate_count": len(candidates),
                "candidate_ids": [candidate.id for candidate in candidates],
            },
        )
    except Exception as exc:
        record_event(
            session,
            event_type="case_memory_extraction_failed",
            encounter_id=encounter.id,
            payload={"error_type": type(exc).__name__},
        )
        record_event(
            session,
            event_type="case_closed",
            encounter_id=encounter.id,
            payload={"extraction_status": "failed", "candidate_count": 0, "candidate_ids": []},
        )

    assessment = parse_stored_assessment(encounter.assessment)
    return build_consultation_response(session, encounter, assessment, DeploymentMode(encounter.deployment_mode))
