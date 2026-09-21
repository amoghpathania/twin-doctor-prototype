from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.schemas import (
    DeploymentMode,
    MemoryStatus,
    MemoryType,
    RiskLevel,
    TestDecisionActor,
    TestDecisionOrigin,
    TestDecisionStatus,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    specialty: Mapped[str] = mapped_column(String)
    experience: Mapped[str] = mapped_column(String)
    communication_style: Mapped[str] = mapped_column(String)
    clinical_preferences: Mapped[str] = mapped_column(String)
    escalation_preferences: Mapped[str] = mapped_column(String)
    twin_version: Mapped[str] = mapped_column(String, default="v1")
    # Each doctor controls their own twin's mode; new doctors always start in SHADOW.
    default_deployment_mode: Mapped[str] = mapped_column(String, default="SHADOW")

    memories: Mapped[list["Memory"]] = relationship(back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    age: Mapped[int]
    sex: Mapped[str] = mapped_column(String)
    chronic_conditions: Mapped[list[str]] = mapped_column(JSON, default=list)
    general_conditions: Mapped[list[str]] = mapped_column(JSON, default=list)
    medications: Mapped[list[str]] = mapped_column(JSON, default=list)
    allergies: Mapped[list[str]] = mapped_column(JSON, default=list)
    previous_visits: Mapped[list[str]] = mapped_column(JSON, default=list)
    # Self-registered walk-in patients vs. already-known patients; gates memory capture.
    is_new_patient: Mapped[bool] = mapped_column(default=False)


class Encounter(Base):
    __tablename__ = "encounters"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    deployment_mode: Mapped[DeploymentMode] = mapped_column(String)
    conversation: Mapped[list[dict]] = mapped_column(JSON, default=list)
    assessment: Mapped[dict] = mapped_column(JSON, default=dict)
    risk_level: Mapped[RiskLevel] = mapped_column(String)
    escalation_required: Mapped[bool] = mapped_column(default=False)
    escalation_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str] = mapped_column(String, default="")
    appointment_id: Mapped[int | None] = mapped_column(nullable=True)
    doctor_reviewed: Mapped[bool] = mapped_column(default=False)
    doctor_review_action: Mapped[str | None] = mapped_column(String, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    content: Mapped[str] = mapped_column(String)
    memory_type: Mapped[MemoryType] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(default=1.0)
    status: Mapped[MemoryStatus] = mapped_column(String, default=MemoryStatus.CANDIDATE.value)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    doctor: Mapped["Doctor"] = relationship(back_populates="memories")


class AuditEvent(Base):
    """Append-only audit trail for safety overrides, escalations, and decisions."""

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int | None] = mapped_column(ForeignKey("encounters.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    encounter_id: Mapped[int | None] = mapped_column(ForeignKey("encounters.id"), nullable=True)
    slot_start: Mapped[datetime] = mapped_column(DateTime())
    slot_end: Mapped[datetime] = mapped_column(DateTime())
    status: Mapped[str] = mapped_column(String, default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EvaluationRun(Base):
    """Persisted result of an evaluation suite run (see services/evaluation_service.py)."""

    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DiagnosticTestCatalog(Base):
    """Hospital-managed reference catalog used by every test decision workflow."""

    __tablename__ = "diagnostic_test_catalog"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    autonomous_eligible: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class EncounterTestDecision(Base):
    """A finalized or proposed test decision and the evidence available when it was made."""

    __tablename__ = "encounter_test_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounters.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    test_catalog_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_test_catalog.id"), index=True)
    deployment_mode: Mapped[DeploymentMode] = mapped_column(String)
    origin: Mapped[TestDecisionOrigin] = mapped_column(String)
    status: Mapped[TestDecisionStatus] = mapped_column(String)
    decided_by: Mapped[TestDecisionActor] = mapped_column(String)
    clinical_indication: Mapped[str | None] = mapped_column(String, nullable=True)
    model_confidence: Mapped[float | None] = mapped_column(nullable=True)
    scenario_features: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
