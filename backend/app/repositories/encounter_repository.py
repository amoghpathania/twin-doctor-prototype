from app.models.domain import Encounter
from app.repositories.base import Repository


class EncounterRepository(Repository[Encounter]):
    model = Encounter

    def list_by_patient(self, patient_id: int) -> list[Encounter]:
        return list(
            self.session.query(Encounter)
            .filter(Encounter.patient_id == patient_id)
            .order_by(Encounter.created_at.desc())
            .all()
        )

    def list_by_doctor(self, doctor_id: int) -> list[Encounter]:
        return list(
            self.session.query(Encounter)
            .filter(Encounter.doctor_id == doctor_id)
            .order_by(Encounter.created_at.desc())
            .all()
        )
