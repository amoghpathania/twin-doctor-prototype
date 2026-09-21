from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models.domain import DiagnosticTestCatalog
from app.seed_data import seed_session


def _client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: session
    return TestClient(app), session


def test_catalog_public_listing_is_active_only_and_admin_can_manage_items():
    client, session = _client()
    try:
        seed_session(session)

        public_response = client.get("/diagnostic-tests")
        assert public_response.status_code == 200
        assert len(public_response.json()) >= 8
        assert all(item["is_active"] for item in public_response.json())

        created = client.post(
            "/admin/diagnostic-tests",
            json={
                "code": " tsh ",
                "name": "Thyroid-stimulating hormone",
                "category": "laboratory",
                "description": "Thyroid function screening",
                "autonomous_eligible": True,
            },
        )
        assert created.status_code == 201
        assert created.json()["code"] == "TSH"
        test_id = created.json()["id"]

        duplicate = client.post(
            "/admin/diagnostic-tests",
            json={"code": "tsh", "name": "Duplicate", "category": "laboratory"},
        )
        assert duplicate.status_code == 409

        updated = client.patch(
            f"/admin/diagnostic-tests/{test_id}",
            json={"name": "Thyroid Stimulating Hormone", "is_active": False},
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "Thyroid Stimulating Hormone"
        assert updated.json()["is_active"] is False

        assert all(item["id"] != test_id for item in client.get("/diagnostic-tests").json())
        assert any(item["id"] == test_id for item in client.get("/admin/diagnostic-tests").json())

        reset = client.post("/admin/reset-data", json={"confirmation": "RESET ADDED DATA"})
        assert reset.status_code == 200
        assert session.get(DiagnosticTestCatalog, test_id) is not None
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_catalog_rejects_blank_fields():
    client, session = _client()
    try:
        response = client.post(
            "/admin/diagnostic-tests",
            json={"code": " ", "name": " ", "category": " "},
        )
        assert response.status_code == 422
        assert session.query(DiagnosticTestCatalog).count() == 0
    finally:
        app.dependency_overrides.clear()
        session.close()