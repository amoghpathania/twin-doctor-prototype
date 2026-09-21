"""Standalone CLI to run the synthetic evaluation suite against a real LLM.

Requires TWIN_GEMINI_API_KEY to be set (see root .env.example). Not required for the
backend API or test suite to function - this is a convenience script for local runs.
"""

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.agents.llm_client import GeminiLLMClient  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.services.evaluation_service import load_cases, persist_evaluation_summary, run_evaluation_suite  # noqa: E402


def main() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        cases = load_cases(Path(__file__).resolve().parent / "cases.json")
        llm_client = GeminiLLMClient()
        summary = run_evaluation_suite(session, llm_client, cases=cases)
        persist_evaluation_summary(session, summary)
    finally:
        session.close()

    print(f"Cases evaluated: {summary.cases_evaluated}")
    print(f"Red flag recall: {summary.red_flag_recall:.0%}")
    print(f"Escalation recall: {summary.escalation_recall:.0%}")
    print(f"Required question coverage: {summary.required_question_coverage:.0%}")
    print(f"Structured output validity: {summary.structured_output_validity:.0%}")
    print(f"Doctor preference alignment: {summary.doctor_preference_alignment:.0%}")


if __name__ == "__main__":
    main()
