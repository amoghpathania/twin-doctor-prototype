from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.llm_client import LLMClient
from app.api.deps import get_llm_client
from app.db import get_db
from app.models.schemas import EvaluationSummary
from app.services import evaluation_service

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/run", response_model=EvaluationSummary)
def run_evaluations(db: Session = Depends(get_db), llm_client: LLMClient = Depends(get_llm_client)) -> EvaluationSummary:
    summary = evaluation_service.run_evaluation_suite(db, llm_client)
    evaluation_service.persist_evaluation_summary(db, summary)
    return summary


@router.get("/results", response_model=EvaluationSummary)
def get_evaluation_results(db: Session = Depends(get_db)) -> EvaluationSummary:
    summary = evaluation_service.get_latest_evaluation_summary(db)
    if summary is None:
        raise HTTPException(status_code=404, detail="No evaluation run yet")
    return summary
