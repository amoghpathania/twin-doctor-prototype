from sqlalchemy.orm import Session

from app.models.domain import AuditEvent
from app.repositories.audit_repository import AuditRepository


def record_event(session: Session, event_type: str, encounter_id: int | None, payload: dict) -> AuditEvent:
    event = AuditEvent(encounter_id=encounter_id, event_type=event_type, payload=payload)
    return AuditRepository(session).add(event)
