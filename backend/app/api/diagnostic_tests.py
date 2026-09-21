from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.schemas import (
    DiagnosticTestCatalogCreate,
    DiagnosticTestCatalogRead,
    DiagnosticTestCatalogUpdate,
)
from app.services import diagnostic_test_catalog_service

router = APIRouter(prefix="/diagnostic-tests", tags=["diagnostic-tests"])
admin_router = APIRouter(prefix="/admin/diagnostic-tests", tags=["admin"])


@router.get("", response_model=list[DiagnosticTestCatalogRead])
def list_active_tests(db: Session = Depends(get_db)) -> list[DiagnosticTestCatalogRead]:
    return [DiagnosticTestCatalogRead.model_validate(item) for item in diagnostic_test_catalog_service.list_active_tests(db)]


@admin_router.get("", response_model=list[DiagnosticTestCatalogRead])
def list_all_tests(db: Session = Depends(get_db)) -> list[DiagnosticTestCatalogRead]:
    return [DiagnosticTestCatalogRead.model_validate(item) for item in diagnostic_test_catalog_service.list_all_tests(db)]


@admin_router.post("", response_model=DiagnosticTestCatalogRead, status_code=status.HTTP_201_CREATED)
def create_test(
    request: DiagnosticTestCatalogCreate, db: Session = Depends(get_db)
) -> DiagnosticTestCatalogRead:
    try:
        diagnostic_test = diagnostic_test_catalog_service.create_test(db, request)
    except diagnostic_test_catalog_service.DuplicateDiagnosticTestCodeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return DiagnosticTestCatalogRead.model_validate(diagnostic_test)


@admin_router.patch("/{test_id}", response_model=DiagnosticTestCatalogRead)
def update_test(
    test_id: int, request: DiagnosticTestCatalogUpdate, db: Session = Depends(get_db)
) -> DiagnosticTestCatalogRead:
    diagnostic_test = diagnostic_test_catalog_service.update_test(db, test_id, request)
    if diagnostic_test is None:
        raise HTTPException(status_code=404, detail="Diagnostic test not found")
    return DiagnosticTestCatalogRead.model_validate(diagnostic_test)