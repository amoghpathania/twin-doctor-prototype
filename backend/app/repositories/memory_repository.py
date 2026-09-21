from app.models.domain import Memory
from app.models.schemas import MemoryStatus
from app.repositories.base import Repository


class MemoryRepository(Repository[Memory]):
    model = Memory

    def list_approved_by_doctor(self, doctor_id: int) -> list[Memory]:
        return list(
            self.session.query(Memory)
            .filter(Memory.doctor_id == doctor_id, Memory.status == MemoryStatus.APPROVED.value)
            .all()
        )

    def list_by_doctor(self, doctor_id: int) -> list[Memory]:
        return list(self.session.query(Memory).filter(Memory.doctor_id == doctor_id).all())
