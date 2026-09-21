from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.schemas import AdminDataResetRequest, AdminDataResetResponse, AdminDataSummary
from app.services import admin_data_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/data-summary", response_model=AdminDataSummary)
def get_data_summary(db: Session = Depends(get_db)) -> AdminDataSummary:
    return AdminDataSummary.model_validate(admin_data_service.get_data_summary(db))


@router.post("/reset-data", response_model=AdminDataResetResponse)
def reset_added_data(_request: AdminDataResetRequest, db: Session = Depends(get_db)) -> AdminDataResetResponse:
    return AdminDataResetResponse(deleted=admin_data_service.reset_added_data(db))