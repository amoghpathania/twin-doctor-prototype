import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_llm_client
from app.db import Base, get_db
from app.main import app
from tests.fakes import FakeLLMClient

VALID_RESPONSE = json.dumps(
    {
        "symptoms": ["runny nose"],
        "missing_information": ["duration"],
        "risk_level": "GREEN",
        "escalation_required": False,
        "escalation_reason": None,
        "summary": "Mild cold symptoms.",
        "recommended_action": "provide_informational_guidance",
        "confidence": 0.9,
    }
)


def _client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()

    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient(VALID_RESPONSE)
    return TestClient(app)


def test_results_before_any_run_returns_404():
    client = _client()
    try:
        response = client.get("/evaluations/results")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_run_then_fetch_evaluation_results():
    client = _client()
    try:
        run_response = client.post("/evaluations/run")
        assert run_response.status_code == 200
        run_body = run_response.json()
        assert run_body["cases_evaluated"] >= 30
        assert 0.0 <= run_body["structured_output_validity"] <= 1.0

        fetched = client.get("/evaluations/results")
        assert fetched.status_code == 200
        assert fetched.json()["cases_evaluated"] == run_body["cases_evaluated"]
    finally:
        app.dependency_overrides.clear()
