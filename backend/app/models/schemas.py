from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class RiskLevel(str, Enum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


class DeploymentMode(str, Enum):
    SHADOW = "SHADOW"
    COPILOT = "COPILOT"
    INTAKE = "INTAKE"
    AUTONOMOUS = "AUTONOMOUS"


class MemoryStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class MemoryType(str, Enum):
    PREFERENCE = "preference"
    ESCALATION_RULE = "escalation_rule"
    COMMUNICATION_STYLE = "communication_style"
    CLINICAL_PATTERN = "clinical_pattern"
    WORKFLOW_PREFERENCE = "workflow_preference"


class ExtractedMemoryCandidate(BaseModel):
    memory_type: MemoryType
    content: str
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("content")
    @classmethod
    def require_content(cls, content: str) -> str:
        content = content.strip()
        if not content:
            raise ValueError("Memory content must not be empty")
        return content


class MemoryExtractionResult(BaseModel):
    candidates: list[ExtractedMemoryCandidate] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def require_unique_types(self):
        memory_types = [candidate.memory_type for candidate in self.candidates]
        if len(memory_types) != len(set(memory_types)):
            raise ValueError("Only one candidate per memory type is allowed")
        return self


class ClinicalAssessment(BaseModel):
    """Structured output contract the LLM must satisfy. Never trust free-form prose instead of this."""

    symptoms: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    risk_level: RiskLevel
    escalation_required: bool
    escalation_reason: str | None = None
    summary: str
    recommended_action: str
    confidence: float = Field(ge=0.0, le=1.0)
    fallback_used: bool = False
    recommended_tests: list["RecommendedDiagnosticTest"] = Field(default_factory=list, max_length=5)

    @field_validator("missing_information")
    @classmethod
    def limit_follow_up_questions(cls, questions: list[str]) -> list[str]:
        return questions[:1]


class DoctorRead(BaseModel):
    id: int
    name: str
    specialty: str
    experience: str
    communication_style: str
    clinical_preferences: str
    escalation_preferences: str
    twin_version: str
    default_deployment_mode: DeploymentMode

    model_config = {"from_attributes": True}


class DoctorCreateRequest(BaseModel):
    """Admin onboarding a new doctor. Mode is never accepted here - always starts in SHADOW."""

    name: str
    specialty: str
    experience: str
    communication_style: str
    clinical_preferences: str
    escalation_preferences: str


class DoctorModeUpdateRequest(BaseModel):
    deployment_mode: DeploymentMode


class PatientRead(BaseModel):
    id: int
    name: str
    age: int
    sex: str
    chronic_conditions: list[str]
    general_conditions: list[str]
    medications: list[str]
    allergies: list[str]
    is_new_patient: bool

    model_config = {"from_attributes": True}


class PatientCreateRequest(BaseModel):
    """Patient self-registering as new via intake. Always created with is_new_patient=True."""

    name: str
    age: int
    sex: str
    chronic_conditions: list[str] = Field(default_factory=list)
    general_conditions: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)


class PatientConditionAddRequest(BaseModel):
    """Append a single condition to a patient's record - never overwrites existing history."""

    category: Literal["chronic", "general"]
    condition: str


class ConsultationStartRequest(BaseModel):
    doctor_id: int
    patient_id: int
    message: str


class ConsultationMessageRequest(BaseModel):
    message: str


class ConsultationReviewRequest(BaseModel):
    """Doctor approves the AI assessment as-is, or modifies specific fields before it's finalized."""

    action: Literal["approve", "modify"]
    risk_level: RiskLevel | None = None
    escalation_required: bool | None = None
    escalation_reason: str | None = None
    summary: str | None = None
    recommended_action: str | None = None
    selected_test_ids: list[int] | None = None


class DeploymentDecision(BaseModel):
    """Result of applying deployment-mode policy to a clinical assessment."""

    mode: DeploymentMode
    allowed_actions: list[str]
    autonomous_action_taken: bool


class ConsultationResponse(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    deployment_mode: DeploymentMode
    conversation: list[dict]
    assessment: ClinicalAssessment
    risk_level: RiskLevel
    escalation_required: bool
    escalation_reason: str | None
    summary: str
    appointment_id: int | None
    deployment_decision: DeploymentDecision
    available_slots: list["AppointmentSlot"] = Field(default_factory=list)
    doctor_reviewed: bool
    doctor_review_action: str | None
    closed_at: datetime | None
    created_at: datetime
    test_decisions: list["EncounterTestDecisionRead"] = Field(default_factory=list)

    model_config = {"from_attributes": False}


class MemoryRead(BaseModel):
    id: int
    doctor_id: int
    content: str
    memory_type: MemoryType
    source: str
    confidence: float
    status: MemoryStatus
    created_at: datetime
    approved_at: datetime | None

    model_config = {"from_attributes": True}


class MemoryCreateRequest(BaseModel):
    """Doctor feedback/correction captured as a CANDIDATE memory (never auto-promoted)."""

    doctor_id: int
    content: str
    memory_type: MemoryType
    source: str = "doctor_feedback"
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class AppointmentSlot(BaseModel):
    start: datetime
    end: datetime


class AppointmentRead(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    encounter_id: int | None
    slot_start: datetime
    slot_end: datetime
    status: str

    model_config = {"from_attributes": True}


class AppointmentCreateRequest(BaseModel):
    doctor_id: int
    patient_id: int
    slot_start: datetime
    encounter_id: int | None = None


def _require_trimmed(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Value must not be blank")
    return value


class DiagnosticTestCatalogCreate(BaseModel):
    code: str
    name: str
    category: str
    description: str | None = None
    autonomous_eligible: bool = False

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return _require_trimmed(value).upper()

    @field_validator("name", "category")
    @classmethod
    def require_text(cls, value: str) -> str:
        return _require_trimmed(value)

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class DiagnosticTestCatalogUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    is_active: bool | None = None
    autonomous_eligible: bool | None = None

    @field_validator("name", "category")
    @classmethod
    def require_text(cls, value: str | None) -> str | None:
        return _require_trimmed(value) if value is not None else None

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class DiagnosticTestCatalogRead(BaseModel):
    id: int
    code: str
    name: str
    category: str
    description: str | None
    is_active: bool
    autonomous_eligible: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TestDecisionStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ORDERED = "ORDERED"
    REJECTED = "REJECTED"


class TestDecisionOrigin(str, Enum):
    DOCTOR_SELECTED = "DOCTOR_SELECTED"
    AGENT_RECOMMENDED = "AGENT_RECOMMENDED"


class TestDecisionActor(str, Enum):
    DOCTOR = "DOCTOR"
    SYSTEM = "SYSTEM"


class RecommendedDiagnosticTest(BaseModel):
    catalog_code: str
    clinical_indication: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_summary: str | None = None

    @field_validator("catalog_code")
    @classmethod
    def normalize_catalog_code(cls, value: str) -> str:
        return _require_trimmed(value).upper()

    @field_validator("clinical_indication")
    @classmethod
    def require_indication(cls, value: str) -> str:
        return _require_trimmed(value)


class TestRecommendationResult(BaseModel):
    recommendations: list[RecommendedDiagnosticTest] = Field(default_factory=list, max_length=5)


class TestScenarioFeatures(BaseModel):
    symptoms: list[str] = Field(default_factory=list)
    risk_level: RiskLevel
    age_band: str
    sex: str
    relevant_conditions: list[str] = Field(default_factory=list)


class TestDecisionEvidence(BaseModel):
    catalog_id: int
    catalog_code: str
    similarity_score: float
    shadow_order_count: int = 0
    copilot_shown_count: int = 0
    copilot_accepted_count: int = 0
    copilot_rejected_count: int = 0
    doctor_added_count: int = 0
    acceptance_rate: float | None = None
    supporting_encounter_ids: list[int] = Field(default_factory=list)


class TestRecommendationContext(BaseModel):
    evidence: list[TestDecisionEvidence] = Field(default_factory=list)


class EncounterTestDecisionRead(BaseModel):
    id: int
    test_catalog_id: int
    catalog_code: str
    test_name: str
    category: str
    deployment_mode: DeploymentMode
    origin: TestDecisionOrigin
    status: TestDecisionStatus
    decided_by: TestDecisionActor
    clinical_indication: str | None
    model_confidence: float | None
    evidence_snapshot: dict
    decided_at: datetime | None


class AdminDataCounts(BaseModel):
    encounters: int = 0
    appointments: int = 0
    audit_events: int = 0
    evaluation_runs: int = 0
    test_decisions: int = 0
    memories: int = 0
    doctors: int = 0
    patients: int = 0


class ProtectedDataCounts(BaseModel):
    doctors: int = 0
    patients: int = 0
    memories: int = 0


class AdminDataSummary(BaseModel):
    resettable: AdminDataCounts
    protected: ProtectedDataCounts


class AdminDataResetRequest(BaseModel):
    confirmation: Literal["RESET ADDED DATA"]


class AdminDataResetResponse(BaseModel):
    deleted: AdminDataCounts


class EvalCase(BaseModel):
    id: str
    category: str
    patient_context: str
    symptoms: list[str]
    expected_risk: RiskLevel
    required_questions: list[str] = Field(default_factory=list)
    expected_escalation: bool
    expected_action: str


class EvalCaseResult(BaseModel):
    case_id: str
    expected_risk: RiskLevel
    actual_risk: RiskLevel
    expected_escalation: bool
    actual_escalation: bool
    structured_output_valid: bool
    red_flags_detected: list[str]
    recommended_action: str
    expected_action: str
    required_questions: list[str]
    missing_information: list[str]


class EvaluationSummary(BaseModel):
    cases_evaluated: int
    red_flag_recall: float
    escalation_recall: float
    required_question_coverage: float
    structured_output_validity: float
    doctor_preference_alignment: float
    results: list[EvalCaseResult]
    created_at: datetime
