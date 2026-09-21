from sqlalchemy.orm import Session

from app.models.schemas import TestRecommendationContext, TestScenarioFeatures
from app.services.test_learning_service import get_test_recommendation_context as retrieve_context


def get_test_recommendation_context(
    session: Session, doctor_id: int, scenario: TestScenarioFeatures
) -> TestRecommendationContext:
    """Return transparent, doctor-scoped decision evidence for the current scenario."""
    return retrieve_context(session, doctor_id, scenario)