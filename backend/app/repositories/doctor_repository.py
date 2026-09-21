from app.models.domain import Doctor
from app.repositories.base import Repository


class DoctorRepository(Repository[Doctor]):
    model = Doctor
