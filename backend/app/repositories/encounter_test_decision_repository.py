from sqlalchemy.orm import Session

from app.models.domain import EncounterTestDecision
from app.models.schemas import DeploymentMode, TestDecisionActor
from app.repositories.base import Repository


class EncounterTestDecisionRepository(Repository[EncounterTestDecision]):
    model = EncounterTestDecision

    def list_by_encounter(self, encounter_id: int) -> list[EncounterTestDecision]:
        return list(self.session.query(self.model).filter(self.model.encounter_id == encounter_id).all())

    def replace_for_encounter(
        self, encounter_id: int, decisions: list[EncounterTestDecision]
    ) -> list[EncounterTestDecision]:
        self.session.query(self.model).filter(self.model.encounter_id == encounter_id).delete()
        self.session.add_all(decisions)
        self.session.commit()
        for decision in decisions:
            self.session.refresh(decision)
        return decisions

    def save_all(self, decisions: list[EncounterTestDecision]) -> list[EncounterTestDecision]:
        self.session.add_all(decisions)
        self.session.commit()
        for decision in decisions:
            self.session.refresh(decision)
        return decisions

    def list_learning_decisions(self, doctor_id: int) -> list[EncounterTestDecision]:
        return list(
            self.session.query(self.model)
            .filter(
                self.model.doctor_id == doctor_id,
                self.model.decided_by == TestDecisionActor.DOCTOR.value,
                self.model.deployment_mode.in_([DeploymentMode.SHADOW.value, DeploymentMode.COPILOT.value]),
            )
            .all()
        )