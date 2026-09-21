from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.db import Base

ModelT = TypeVar("ModelT", bound=Base)


class Repository(Generic[ModelT]):
    """Generic SQLAlchemy CRUD base so entity repositories stay DRY."""

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, entity_id: int) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def list_all(self) -> list[ModelT]:
        return list(self.session.query(self.model).all())

    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity: ModelT) -> ModelT:
        self.session.commit()
        self.session.refresh(entity)
        return entity
