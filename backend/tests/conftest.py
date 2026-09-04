import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def admin_headers(client):
    r = client.post("/auth/login", json={"email": "admin@peblo.local", "password": "peblo-admin"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def editor_headers(client):
    r = client.post("/auth/login", json={"email": "editor@peblo.local", "password": "peblo-editor"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# Configure env before the app caches settings / binds the engine.
@pytest.fixture(scope="session")
def tmp_env(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("api")
    # GitHub Actions sets CI=true and DATABASE_URL to the Postgres service.
    # Local pytest stays on sqlite so we never wipe a compose volume.
    use_pg = os.environ.get("CI") == "true" and os.environ.get("DATABASE_URL", "").startswith(
        "postgresql"
    )
    if not use_pg:
        os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["STORAGE_LOCAL_PATH"] = str(tmp / "storage")
    os.environ["JWT_SECRET"] = os.environ.get("JWT_SECRET") or "test-secret"
    os.environ["SEED_ON_STARTUP"] = "false"
    os.environ["PUBLIC_BASE_URL"] = "http://test"
    repo_ref = Path(__file__).resolve().parents[2] / "data" / "reference.json"
    if repo_ref.exists():
        os.environ["REFERENCE_PATH"] = str(repo_ref)
    return tmp


@pytest.fixture(scope="session")
def client(tmp_env):
    from app.config import get_settings
    from app.db import get_db
    from app.models import Base, User
    from app.auth import hash_password
    from app.storage import reset_storage
    from app import db as dbmod

    get_settings.cache_clear()
    reset_storage()
    url = get_settings().database_url

    if url.startswith("postgresql"):
        engine = create_engine(url, pool_pre_ping=True)
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
        dbmod.engine = engine
        from app.schema import apply_schema

        apply_schema()
        TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    else:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        Base.metadata.create_all(engine)
        dbmod.engine = engine

    dbmod.SessionLocal = TestingSession

    db = TestingSession()
    db.add(User(email="admin@peblo.local", password_hash=hash_password("peblo-admin"), role="admin"))
    db.add(User(email="editor@peblo.local", password_hash=hash_password("peblo-editor"), role="editor"))
    db.commit()
    db.close()

    def override_db():
        s = TestingSession()
        try:
            yield s
        finally:
            s.close()

    from app.main import app

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
