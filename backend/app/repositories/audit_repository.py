from app.models.domain import AuditEvent
from app.repositories.base import Repository


class AuditRepository(Repository[AuditEvent]):
    model = AuditEvent

    def latest_review_for_encounter(self, encounter_id: int) -> AuditEvent | None:
        return (
            self.session.query(AuditEvent)
            .filter(
                AuditEvent.encounter_id == encounter_id,
                AuditEvent.event_type.in_(["doctor_approved_assessment", "doctor_modified_assessment"]),
            )
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .first()
        )
