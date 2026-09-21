from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


BACKEND_DIR = Path(__file__).resolve().parents[1]


def resolve_database_url(database_url: str) -> str:
    url = make_url(database_url)
    if url.drivername in {"postgres", "postgresql"}:
        return url.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)

    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return database_url

    database_path = Path(url.database)
    if database_path.is_absolute():
        return database_url

    absolute_path = (BACKEND_DIR / database_path).resolve().as_posix()
    return url.set(database=absolute_path).render_as_string(hide_password=False)


def _make_engine():
    settings = get_settings()
    database_url = resolve_database_url(settings.database_url)
    # check_same_thread=False is required for SQLite when used across FastAPI's threadpool.
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
