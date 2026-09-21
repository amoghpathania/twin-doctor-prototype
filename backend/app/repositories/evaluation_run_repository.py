from app.models.domain import EvaluationRun
from app.repositories.base import Repository


class EvaluationRunRepository(Repository[EvaluationRun]):
    model = EvaluationRun

    def latest(self) -> EvaluationRun | None:
        return (
            self.session.query(EvaluationRun)
            .order_by(EvaluationRun.created_at.desc())
            .first()
        )
