from app.models.domain import Doctor, Memory, Patient
from app.seed_data import seed_session


def test_seed_session_creates_multiple_specialties_and_is_idempotent(db_session):
    first = seed_session(db_session)
    second = seed_session(db_session)

    doctors = db_session.query(Doctor).all()
    specialties = {doctor.specialty for doctor in doctors}
    assert {"General Medicine", "Neurology", "Otolaryngology (ENT)", "Family Medicine"} <= specialties
    assert len(doctors) == 4
    assert db_session.query(Patient).count() == 8
    assert db_session.query(Memory).count() >= 20
    assert first["doctors"] == 4
    assert second == {"doctors": 0, "patients": 0, "memories": 0}

    for doctor in doctors:
        assert db_session.query(Memory).filter(Memory.doctor_id == doctor.id).count() >= 5