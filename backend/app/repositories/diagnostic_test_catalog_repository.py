from app.models.domain import DiagnosticTestCatalog
from app.repositories.base import Repository


class DiagnosticTestCatalogRepository(Repository[DiagnosticTestCatalog]):
    model = DiagnosticTestCatalog

    def get_by_code(self, code: str) -> DiagnosticTestCatalog | None:
        return self.session.query(self.model).filter(self.model.code == code.upper()).one_or_none()

    def list_active(self) -> list[DiagnosticTestCatalog]:
        return list(
            self.session.query(self.model)
            .filter(self.model.is_active.is_(True))
            .order_by(self.model.category, self.model.name)
            .all()
        )

    def list_all(self) -> list[DiagnosticTestCatalog]:
        return list(self.session.query(self.model).order_by(self.model.category, self.model.name).all())