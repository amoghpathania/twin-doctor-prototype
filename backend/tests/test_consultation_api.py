import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.api.consultations import get_llm_client
from app.agents.llm_client import GeminiLLMClient, LLMConfigurationError
from app.db import Base, get_db
from app.main import app
from app.models.domain import AuditEvent, Doctor, Encounter, Patient
from tests.fakes import FailingLLMClient, FakeLLMClient

RED_FLAG_MESSAGE_BUT_LLM_SAYS_GREEN = json.dumps(
    {
        "symptoms": ["chest pain"],
        "missing_information": [],
        "risk_level": "GREEN",
        "escalation_required": False,
        "escalation_reason": None,
        "summary": "Patient reports chest pain.",
        "recommended_action": "provide_informational_guidance",
        "confidence": 0.5,
    }
)

def test_shadow_case_ignores_model_recommendation_but_keeps_safety_override():
    llm = FakeLLMClient(RED_FLAG_MESSAGE_BUT_LLM_SAYS_GREEN)
    client, session, doctor, patient = _make_client_with_seeded_db(
        RED_FLAG_MESSAGE_BUT_LLM_SAYS_GREEN,
        mode="SHADOW",
        llm_client=llm,
    )
    try:
        response = client.post(
            "/consultations",
            json={
                "doctor_id": doctor.id,
                "patient_id": patient.id,
                "message": "I have severe crushing chest pain",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["assessment"]["recommended_action"] == "await_doctor_review"
        assert body["risk_level"] == "RED"
        assert body["escalation_required"] is True
        assert "Do not diagnose" in llm.system_instructions[0]
    finally:
        app.dependency_overrides.clear()
AMBER_RESPONSE = json.dumps(
    {
        "symptoms": ["persistent cough"],
        "missing_information": ["duration", "inhaler usage"],
        "risk_level": "AMBER",
        "escalation_required": True,
        "escalation_reason": "Persistent cough requires doctor review.",
        "summary": "Persistent cough for over 2 weeks.",
        "recommended_action": "escalate_to_doctor",
        "confidence": 0.75,
    }
)

AMBER_READY_FOR_APPOINTMENT_RESPONSE = json.dumps(
    {
        "symptoms": ["persistent cough"],
        "missing_information": [],
        "risk_level": "AMBER",
        "escalation_required": True,
        "escalation_reason": "Persistent cough requires doctor review.",
        "summary": "Persistent cough for over 2 weeks.",
        "recommended_action": "escalate_to_doctor",
        "confidence": 0.75,
    }
)

AMBER_WITH_RED_FLAG_QUESTION_RESPONSE = json.dumps(
    {
        "symptoms": ["fever"],
        "missing_information": ["Are you experiencing shortness of breath?"],
        "risk_level": "AMBER",
        "escalation_required": True,
        "escalation_reason": "Persistent fever requires doctor review.",
        "summary": "Patient reports a persistent fever.",
        "recommended_action": "escalate_to_doctor",
        "confidence": 0.8,
    }
)


def test_missing_llm_configuration_creates_doctor_case_instead_of_error(monkeypatch):
    def raise_missing_key(self):
        raise LLMConfigurationError("GEMINI_API_KEY is not configured")

    monkeypatch.setattr(GeminiLLMClient, "__init__", raise_missing_key)

    client, session, doctor, patient = _make_client_with_seeded_db("", use_real_llm_dependency=True)
    try:
        response = client.post(
            "/consultations",
            json={"doctor_id": doctor.id, "patient_id": patient.id, "message": "I have a cough"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["assessment"]["fallback_used"] is True
        assert body["escalation_required"] is True
        assert session.get(Encounter, body["id"]) is not None
    finally:
        app.dependency_overrides.clear()


def _make_client_with_seeded_db(
    llm_response: str, mode: str = "SHADOW", llm_client=None, use_real_llm_dependency: bool = False
):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    doctor = Doctor(
        name="Dr. Sarah Lim",
        specialty="General Medicine",
        experience="10 years",
        communication_style="Concise",
        clinical_preferences="Ask duration first",
        escalation_preferences="Escalate worsening symptoms",
        twin_version="v1",
        default_deployment_mode=mode,
    )
    patient = Patient(name="Tan Wei Ming", age=45, sex="male", chronic_conditions=[], general_conditions=[], medications=[], allergies=[], previous_visits=[])
    session.add_all([doctor, patient])
    session.commit()

    fake_llm = llm_client or FakeLLMClient(llm_response)

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    if not use_real_llm_dependency:
        app.dependency_overrides[get_llm_client] = lambda: fake_llm

    client = TestClient(app)
    return client, session, doctor, patient


def test_start_consultation_end_to_end_safety_override_creates_audit_event():
    client, session, doctor, patient = _make_client_with_seeded_db(RED_FLAG_MESSAGE_BUT_LLM_SAYS_GREEN, mode="AUTONOMOUS")
    try:
        response = client.post(
            "/consultations",
            json={
                "doctor_id": doctor.id,
                "patient_id": patient.id,
                "message": "I have severe crushing chest pain",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["risk_level"] == "RED"
        assert body["escalation_required"] is True
        assert body["deployment_decision"]["autonomous_action_taken"] is False

        audit_events = session.query(AuditEvent).filter(AuditEvent.event_type == "safety_override").all()
        assert len(audit_events) == 1
    finally:
        app.dependency_overrides.clear()


def test_get_consultation_returns_persisted_encounter():
    client, session, doctor, patient = _make_client_with_seeded_db(RED_FLAG_MESSAGE_BUT_LLM_SAYS_GREEN, mode="SHADOW")
    try:
        created = client.post(
            "/consultations",
            json={
                "doctor_id": doctor.id,
                "patient_id": patient.id,
                "message": "I have severe crushing chest pain",
            },
        ).json()

        fetched = client.get(f"/consultations/{created['id']}")

        assert fetched.status_code == 200
        assert fetched.json()["risk_level"] == "RED"
    finally:
        app.dependency_overrides.clear()


def test_red_override_blocks_autonomous_and_copilot_alike():
    """RED override must hold regardless of deployment mode - safety engine, not the LLM, decides."""
    for mode in ("SHADOW", "COPILOT", "INTAKE", "AUTONOMOUS"):
        client, session, doctor, patient = _make_client_with_seeded_db(RED_FLAG_MESSAGE_BUT_LLM_SAYS_GREEN, mode=mode)
        try:
            response = client.post(
                "/consultations",
                json={
                    "doctor_id": doctor.id,
                    "patient_id": patient.id,
                    "message": "I have severe crushing chest pain",
                },
            )
            body = response.json()
            assert body["risk_level"] == "RED", f"mode={mode}"
            assert body["escalation_required"] is True, f"mode={mode}"
            assert body["deployment_decision"]["autonomous_action_taken"] is False, f"mode={mode}"
        finally:
            app.dependency_overrides.clear()


def test_red_override_records_both_safety_override_and_escalation_audit_events():
    client, session, doctor, patient = _make_client_with_seeded_db(RED_FLAG_MESSAGE_BUT_LLM_SAYS_GREEN, mode="AUTONOMOUS")
    try:
        client.post(
            "/consultations",
            json={
                "doctor_id": doctor.id,
                "patient_id": patient.id,
                "message": "sudden loss of consciousness, unresponsive",
            },
        )

        event_types = {e.event_type for e in session.query(AuditEvent).all()}
        assert "safety_override" in event_types
        assert "escalation" in event_types
    finally:
        app.dependency_overrides.clear()


def test_amber_case_with_follow_up_returns_one_question_without_appointment_slots():
    client, session, doctor, patient = _make_client_with_seeded_db(AMBER_RESPONSE, mode="INTAKE")
    try:
        response = client.post(
            "/consultations",
            json={
                "doctor_id": doctor.id,
                "patient_id": patient.id,
                "message": "I have had a persistent cough for over 2 weeks",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["risk_level"] == "AMBER"
        assert body["escalation_required"] is True
        assert "escalate_to_doctor" in body["deployment_decision"]["allowed_actions"]
        assert body["assessment"]["missing_information"] == ["duration"]
        assert body["available_slots"] == []

        escalation_events = session.query(AuditEvent).filter(AuditEvent.event_type == "escalation").all()
        assert len(escalation_events) == 1
    finally:
        app.dependency_overrides.clear()


def test_amber_case_surfaces_available_slots_after_questions_are_complete():
    client, session, doctor, patient = _make_client_with_seeded_db(
        AMBER_READY_FOR_APPOINTMENT_RESPONSE, mode="INTAKE"
    )
    try:
        response = client.post(
            "/consultations",
            json={
                "doctor_id": doctor.id,
                "patient_id": patient.id,
                "message": "I have had a persistent cough for over 2 weeks",
            },
        )

        assert response.status_code == 200
        assert len(response.json()["available_slots"]) > 0
    finally:
        app.dependency_overrides.clear()


def test_amber_case_in_autonomous_mode_still_escalates_instead_of_acting():
    client, session, doctor, patient = _make_client_with_seeded_db(AMBER_RESPONSE, mode="AUTONOMOUS")
    try:
        response = client.post(
            "/consultations",
            json={
                "doctor_id": doctor.id,
                "patient_id": patient.id,
                "message": "I have had a persistent cough for over 2 weeks",
            },
        )

        body = response.json()
        assert body["deployment_decision"]["autonomous_action_taken"] is False
        assert body["deployment_decision"]["allowed_actions"] == ["escalate_to_doctor"]
    finally:
        app.dependency_overrides.clear()


def test_llm_provider_failure_escalates_to_doctor_instead_of_500_even_in_autonomous_mode():
    client, session, doctor, patient = _make_client_with_seeded_db(
        "", mode="AUTONOMOUS", llm_client=FailingLLMClient(RuntimeError("429 quota exceeded"))
    )
    try:
        response = client.post(
            "/consultations",
            json={
                "doctor_id": doctor.id,
                "patient_id": patient.id,
                "message": "I have had a cough and fever for 3 days",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["risk_level"] == "AMBER"
        assert body["escalation_required"] is True
        assert body["deployment_decision"]["autonomous_action_taken"] is False
        assert body["deployment_decision"]["allowed_actions"] == ["escalate_to_doctor"]
        assert body["assessment"]["fallback_used"] is True
        assert body["summary"] == (
            "We couldn't complete the automated assessment right now. "
            "Your case has been sent to your doctor for review."
        )

        persisted = session.get(Encounter, body["id"])
        assert persisted is not None
        assert persisted.doctor_id == doctor.id
        assert persisted.escalation_required is True

        doctor_cases = client.get(f"/consultations?doctor_id={doctor.id}")
        assert doctor_cases.status_code == 200
        assert body["id"] in {case["id"] for case in doctor_cases.json()}
    finally:
        app.dependency_overrides.clear()


def test_doctor_can_approve_assessment_unchanged():
    client, session, doctor, patient = _make_client_with_seeded_db(AMBER_RESPONSE, mode="COPILOT")
    try:
        created = client.post(
            "/consultations",
            json={
                "doctor_id": doctor.id,
                "patient_id": patient.id,
                "message": "I have had a persistent cough for over 2 weeks",
            },
        ).json()

        response = client.post(f"/consultations/{created['id']}/review", json={"action": "approve"})

        assert response.status_code == 200
        body = response.json()
        assert body["risk_level"] == "AMBER"
        assert body["summary"] == created["summary"]
        assert body["doctor_reviewed"] is True
        assert body["doctor_review_action"] == "approve"

        events = session.query(AuditEvent).filter(AuditEvent.event_type == "doctor_approved_assessment").all()
        assert len(events) == 1
    finally:
        app.dependency_overrides.clear()


def test_doctor_can_modify_assessment_fields():
    client, session, doctor, patient = _make_client_with_seeded_db(AMBER_RESPONSE, mode="COPILOT")
    try:
        created = client.post(
            "/consultations",
            json={
                "doctor_id": doctor.id,
                "patient_id": patient.id,
                "message": "I have had a persistent cough for over 2 weeks",
            },
        ).json()

        response = client.post(
            f"/consultations/{created['id']}/review",
            json={
                "action": "modify",
                "risk_level": "GREEN",
                "escalation_required": False,
                "escalation_reason": None,
                "summary": "Doctor confirmed this is a mild viral cough, no escalation needed.",
                "recommended_action": "provide_informational_guidance",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["risk_level"] == "GREEN"
        assert body["escalation_required"] is False
        assert body["summary"] == "Doctor confirmed this is a mild viral cough, no escalation needed."
        assert body["doctor_reviewed"] is True
        assert body["doctor_review_action"] == "modify"

        events = session.query(AuditEvent).filter(AuditEvent.event_type == "doctor_modified_assessment").all()
        assert len(events) == 1

        fetched = client.get(f"/consultations/{created['id']}").json()
        assert fetched["risk_level"] == "GREEN"
        assert fetched["doctor_reviewed"] is True
    finally:
        app.dependency_overrides.clear()


def test_review_nonexistent_consultation_returns_404():
    client, session, doctor, patient = _make_client_with_seeded_db(AMBER_RESPONSE, mode="COPILOT")
    try:
        response = client.post("/consultations/999999/review", json={"action": "approve"})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_new_message_resets_prior_doctor_review():
    client, session, doctor, patient = _make_client_with_seeded_db(AMBER_RESPONSE, mode="COPILOT")
    try:
        created = client.post(
            "/consultations",
            json={
                "doctor_id": doctor.id,
                "patient_id": patient.id,
                "message": "I have had a persistent cough for over 2 weeks",
            },
        ).json()
        client.post(f"/consultations/{created['id']}/review", json={"action": "approve"})

        follow_up = client.post(f"/consultations/{created['id']}/messages", json={"message": "It's gotten worse today"})

        assert follow_up.json()["doctor_reviewed"] is False
    finally:
        app.dependency_overrides.clear()


def test_start_consultation_returns_404_for_unknown_doctor():
    client, session, doctor, patient = _make_client_with_seeded_db(AMBER_RESPONSE)
    try:
        response = client.post(
            "/consultations",
            json={"doctor_id": 999999, "patient_id": patient.id, "message": "hello"},
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_list_consultations_survives_a_row_with_unreadable_assessment():
    """Regression: an encounter left with assessment={} (e.g. an LLM call that failed mid-request)
    must not 500 the whole doctor's case list - it should surface as an AMBER case needing review."""
    client, session, doctor, patient = _make_client_with_seeded_db(AMBER_RESPONSE)
    try:
        broken = Encounter(
            patient_id=patient.id,
            doctor_id=doctor.id,
            deployment_mode="SHADOW",
            conversation=[{"role": "patient", "content": "hello"}],
            assessment={},
            risk_level="GREEN",
        )
        session.add(broken)
        session.commit()

        response = client.get(f"/consultations?doctor_id={doctor.id}")

        assert response.status_code == 200
        broken_case = next(c for c in response.json() if c["id"] == broken.id)
        assert broken_case["risk_level"] == "AMBER"
        assert broken_case["escalation_required"] is True
    finally:
        app.dependency_overrides.clear()


def test_list_open_patient_consultations_excludes_reviewed_and_other_patients():
    client, session, doctor, patient = _make_client_with_seeded_db(AMBER_RESPONSE, mode="COPILOT")
    try:
        other_patient = Patient(
            name="Other Patient", age=30, sex="female", chronic_conditions=[], general_conditions=[], medications=[], allergies=[], previous_visits=[]
        )
        session.add(other_patient)
        session.commit()

        open_case = client.post(
            "/consultations",
            json={"doctor_id": doctor.id, "patient_id": patient.id, "message": "I have had a persistent cough"},
        ).json()
        reviewed_case = client.post(
            "/consultations",
            json={"doctor_id": doctor.id, "patient_id": patient.id, "message": "I have had a different cough"},
        ).json()
        client.post(f"/consultations/{reviewed_case['id']}/review", json={"action": "approve"})
        client.post(
            "/consultations",
            json={"doctor_id": doctor.id, "patient_id": other_patient.id, "message": "Unrelated patient's case"},
        )

        response = client.get(f"/consultations/patient/{patient.id}")

        assert response.status_code == 200
        case_ids = {c["id"] for c in response.json()}
        assert case_ids == {open_case["id"]}
    finally:
        app.dependency_overrides.clear()


def test_follow_up_message_inserts_twins_prior_question_into_conversation():
    client, session, doctor, patient = _make_client_with_seeded_db(AMBER_RESPONSE, mode="COPILOT")
    try:
        created = client.post(
            "/consultations",
            json={"doctor_id": doctor.id, "patient_id": patient.id, "message": "I have had a persistent cough"},
        ).json()

        reply = "3 weeks, and I've been using my inhaler more often"
        response = client.post(f"/consultations/{created['id']}/messages", json={"message": reply})

        assert response.status_code == 200
        body = response.json()
        # The twin's pending question from the prior turn is persisted as its own turn, not merged
        # into the patient's reply - so history shows a real back-and-forth, not one flat message.
        assert len(body["conversation"]) == 3
        assert body["conversation"][0] == {"role": "patient", "content": "I have had a persistent cough"}
        assert body["conversation"][1] == {"role": "twin", "content": "duration"}
        assert body["conversation"][2] == {"role": "patient", "content": reply}
    finally:
        app.dependency_overrides.clear()


def test_answered_question_is_not_repeated_and_intake_advances_to_escalation():
    client, session, doctor, patient = _make_client_with_seeded_db(AMBER_RESPONSE, mode="INTAKE")
    try:
        created = client.post(
            "/consultations",
            json={"doctor_id": doctor.id, "patient_id": patient.id, "message": "I have had a persistent cough"},
        ).json()

        response = client.post(f"/consultations/{created['id']}/messages", json={"message": "For three weeks"})

        assert response.status_code == 200
        body = response.json()
        assert body["assessment"]["missing_information"] == []
        assert body["escalation_required"] is True
        assert len(body["available_slots"]) > 0
    finally:
        app.dependency_overrides.clear()


def test_twins_red_flag_question_does_not_trigger_safety_override():
    client, session, doctor, patient = _make_client_with_seeded_db(
        AMBER_WITH_RED_FLAG_QUESTION_RESPONSE, mode="COPILOT"
    )
    try:
        created = client.post(
            "/consultations",
            json={"doctor_id": doctor.id, "patient_id": patient.id, "message": "I have had a fever for 5 days"},
        ).json()

        response = client.post(f"/consultations/{created['id']}/messages", json={"message": "None"})

        assert response.status_code == 200
        assert response.json()["risk_level"] == "AMBER"
        assert "Safety engine override" not in response.json()["escalation_reason"]
    finally:
        app.dependency_overrides.clear()


def test_affirming_twins_single_red_flag_question_triggers_safety_override():
    client, session, doctor, patient = _make_client_with_seeded_db(
        AMBER_WITH_RED_FLAG_QUESTION_RESPONSE, mode="COPILOT"
    )
    try:
        created = client.post(
            "/consultations",
            json={"doctor_id": doctor.id, "patient_id": patient.id, "message": "I have had a fever for 5 days"},
        ).json()

        response = client.post(f"/consultations/{created['id']}/messages", json={"message": "Yes"})

        assert response.status_code == 200
        assert response.json()["risk_level"] == "RED"
        assert response.json()["escalation_required"] is True
        assert "difficulty_breathing" in response.json()["escalation_reason"]
    finally:
        app.dependency_overrides.clear()

