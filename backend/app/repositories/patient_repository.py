from typing import Literal

from app.models.domain import Patient
from app.repositories.base import Repository


class PatientRepository(Repository[Patient]):
    model = Patient

    def add_condition(self, patient_id: int, category: Literal["chronic", "general"], condition: str) -> Patient | None:
        """Append a condition to the given category, preserving all existing entries."""
        patient = self.get_by_id(patient_id)
        if patient is None:
            return None

        attr = "chronic_conditions" if category == "chronic" else "general_conditions"
        existing = getattr(patient, attr)
        if condition in existing:
            return patient
        # Reassign a new list (not in-place append) so SQLAlchemy detects the JSON column mutation.
        setattr(patient, attr, [*existing, condition])
        return self.update(patient)
