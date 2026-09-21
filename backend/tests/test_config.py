from app.config import Settings
from app.db import resolve_database_url


def test_default_gemini_model_is_flash_lite(monkeypatch):
    monkeypatch.delenv("TWIN_GEMINI_MODEL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.gemini_model == "gemini-3.1-flash-lite"


def test_relative_sqlite_database_is_anchored_to_backend_directory():
    resolved = resolve_database_url("sqlite:///./twin.db")

    assert resolved.startswith("sqlite:///")
    assert resolved.replace("\\", "/").endswith("/backend/twin.db")


def test_postgres_database_url_selects_installed_psycopg_driver():
    database_url = "postgresql://user:password@localhost/twin"

    assert resolve_database_url(database_url) == "postgresql+psycopg://user:password@localhost/twin"


def test_explicit_database_driver_is_unchanged():
    database_url = "postgresql+psycopg://user:password@localhost/twin"

    assert resolve_database_url(database_url) == database_url