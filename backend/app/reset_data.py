"""Recreate the development database and load deterministic seed data."""

from app.db import Base, engine
from app.seed_data import seed


def reset() -> None:
    Base.metadata.drop_all(bind=engine)
    seed()


if __name__ == "__main__":
    reset()