from sqlalchemy.orm import Session

from app.models.domain import DiagnosticTestCatalog
from app.models.schemas import DiagnosticTestCatalogCreate, DiagnosticTestCatalogUpdate
from app.repositories.diagnostic_test_catalog_repository import DiagnosticTestCatalogRepository


class DuplicateDiagnosticTestCodeError(ValueError):
    pass


def list_active_tests(session: Session) -> list[DiagnosticTestCatalog]:
    return DiagnosticTestCatalogRepository(session).list_active()


def list_all_tests(session: Session) -> list[DiagnosticTestCatalog]:
    return DiagnosticTestCatalogRepository(session).list_all()


def create_test(session: Session, request: DiagnosticTestCatalogCreate) -> DiagnosticTestCatalog:
    repository = DiagnosticTestCatalogRepository(session)
    if repository.get_by_code(request.code) is not None:
        raise DuplicateDiagnosticTestCodeError("A diagnostic test with this code already exists")
    return repository.add(DiagnosticTestCatalog(**request.model_dump(), is_active=True))


def update_test(
    session: Session, test_id: int, request: DiagnosticTestCatalogUpdate
) -> DiagnosticTestCatalog | None:
    repository = DiagnosticTestCatalogRepository(session)
    diagnostic_test = repository.get_by_id(test_id)
    if diagnostic_test is None:
        return None
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(diagnostic_test, field, value)
    return repository.update(diagnostic_test)