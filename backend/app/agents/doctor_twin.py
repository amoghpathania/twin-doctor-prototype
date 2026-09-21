"""Reusable Doctor Twin: one implementation, personalized per doctor_id at runtime."""

import json
import logging
import re

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.agents.llm_client import LLMClient
from app.agents.prompts import (
    build_prompt,
    build_system_instruction,
    build_test_recommendation_prompt,
    build_test_recommendation_system_instruction,
)
from app.memory.retrieval import retrieve_relevant_memories
from app.models.domain import Doctor, Patient
from app.models.schemas import ClinicalAssessment, DeploymentMode, RiskLevel, TestRecommendationResult
from app.repositories.diagnostic_test_catalog_repository import DiagnosticTestCatalogRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.encounter_repository import EncounterRepository
from app.repositories.patient_repository import PatientRepository
from app.services.test_learning_service import build_test_scenario_features
from app.tools.test_learning_tools import get_test_recommendation_context

logger = logging.getLogger(__name__)

_FAIL_SAFE_REASON = "Structured output validation failed; escalating rather than proceeding autonomously"
_LLM_CALL_FAILED_REASON = "LLM call failed; escalating rather than proceeding autonomously"
_FAIL_SAFE_MESSAGE = (
    "We couldn't complete the automated assessment right now. "
    "Your case has been sent to your doctor for review."
)
_MAX_FOLLOW_UP_QUESTIONS = 5


class DoctorTwin:
    def __init__(
        self,
        session: Session,
        doctor_id: int,
        llm_client: LLMClient,
        deployment_mode: DeploymentMode | None = None,
    ) -> None:
        self.session = session
        self.doctor_id = doctor_id
        self.llm_client = llm_client
        self.deployment_mode = deployment_mode

    def run(self, patient_id: int, conversation: list[dict]) -> ClinicalAssessment:
        assessment, _valid = self.run_with_diagnostics(patient_id, conversation)
        return assessment

    def run_with_diagnostics(self, patient_id: int, conversation: list[dict]) -> tuple[ClinicalAssessment, bool]:
        """Same as run(), plus whether the LLM's structured output validated (used by the eval runner)."""
        doctor = DoctorRepository(self.session).get_by_id(self.doctor_id)
        patient = PatientRepository(self.session).get_by_id(patient_id)
        if doctor is None or patient is None:
            raise ValueError("Doctor or patient not found")

        patient_context = " ".join(turn["content"] for turn in conversation)
        memories = retrieve_relevant_memories(self.session, self.doctor_id, patient_context)
        prior_summaries = self._prior_encounter_summaries(patient)

        prompt = build_prompt(patient, memories, prior_summaries, conversation)
        system_instruction = build_system_instruction(doctor, self.deployment_mode)
        try:
            raw_output = self.llm_client.generate_assessment(system_instruction, prompt)
        except Exception as exc:  # noqa: BLE001 - provider boundary: network/quota/auth errors must never 500
            logger.warning("DoctorTwin LLM call failed: %s", exc)
            assessment, valid = self._fail_safe(_LLM_CALL_FAILED_REASON), False
        else:
            assessment, valid = self._parse_assessment(raw_output)

        assessment = self._enforce_intake_completion(assessment, conversation)

        if self.deployment_mode == DeploymentMode.SHADOW:
            assessment = assessment.model_copy(update={"recommended_action": "await_doctor_review"})
        elif (
            self.deployment_mode in (DeploymentMode.COPILOT, DeploymentMode.AUTONOMOUS)
            and not assessment.missing_information
            and not assessment.fallback_used
        ):
            assessment = self._add_test_recommendations(doctor, patient, assessment)
        return assessment, valid

    @staticmethod
    def _enforce_intake_completion(
        assessment: ClinicalAssessment, conversation: list[dict]
    ) -> ClinicalAssessment:
        asked_questions = [
            turn["content"] for turn in conversation if turn.get("role") == "twin"
        ]
        if len(asked_questions) >= _MAX_FOLLOW_UP_QUESTIONS or not assessment.missing_information:
            return assessment.model_copy(update={"missing_information": []})

        next_question = assessment.missing_information[0]
        normalized_question = re.sub(r"[^a-z0-9]+", " ", next_question.lower()).strip()
        normalized_history = {
            re.sub(r"[^a-z0-9]+", " ", question.lower()).strip()
            for question in asked_questions
        }
        if normalized_question in normalized_history:
            return assessment.model_copy(update={"missing_information": []})
        return assessment

    def _add_test_recommendations(self, doctor: Doctor, patient: Patient, assessment: ClinicalAssessment):
        catalog = DiagnosticTestCatalogRepository(self.session).list_active()
        if not catalog:
            return assessment
        scenario = build_test_scenario_features(patient, assessment)
        context = get_test_recommendation_context(self.session, self.doctor_id, scenario)
        try:
            raw_output = self.llm_client.generate_test_recommendations(
                build_test_recommendation_system_instruction(doctor),
                build_test_recommendation_prompt(scenario, catalog, context),
            )
            result = TestRecommendationResult.model_validate(json.loads(raw_output))
        except (AttributeError, json.JSONDecodeError, ValidationError, Exception) as exc:
            logger.warning("DoctorTwin test recommendation call failed: %s", exc)
            return assessment
        active_codes = {item.code for item in catalog}
        recommendations = [item for item in result.recommendations if item.catalog_code in active_codes]
        return assessment.model_copy(update={"recommended_tests": recommendations})

    def _prior_encounter_summaries(self, patient: Patient) -> list[str]:
        encounters = EncounterRepository(self.session).list_by_patient(patient.id)
        return [e.summary for e in encounters if e.summary]

    @staticmethod
    def _fail_safe(reason: str) -> ClinicalAssessment:
        return ClinicalAssessment(
            symptoms=[],
            missing_information=[],
            risk_level=RiskLevel.AMBER,
            escalation_required=True,
            escalation_reason=reason,
            summary=_FAIL_SAFE_MESSAGE,
            recommended_action="escalate_to_doctor",
            confidence=0.0,
            fallback_used=True,
        )

    @classmethod
    def _parse_assessment(cls, raw_output: str) -> tuple[ClinicalAssessment, bool]:
        try:
            data = json.loads(raw_output)
            return ClinicalAssessment.model_validate(data), True
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("DoctorTwin structured output validation failed: %s", exc)
            return cls._fail_safe(_FAIL_SAFE_REASON), False

