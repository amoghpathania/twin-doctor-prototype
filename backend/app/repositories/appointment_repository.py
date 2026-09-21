from app.models.domain import Appointment
from app.repositories.base import Repository


class AppointmentRepository(Repository[Appointment]):
    model = Appointment

    def list_by_doctor(self, doctor_id: int) -> list[Appointment]:
        return list(self.session.query(Appointment).filter(Appointment.doctor_id == doctor_id).all())

    def list_all(self) -> list[Appointment]:
        return list(self.session.query(Appointment).all())
