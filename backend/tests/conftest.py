import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configure env before the app caches settings / binds the engine.
@pytest.fixture(scope="session")
def tmp_env(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("api")
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["STORAGE_LOCAL_PATH"] = str(tmp / "storage")
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["SEED_ON_STARTUP"] = "false"
    os.environ["PUBLIC_BASE_URL"] = "http://test"
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

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    db = TestingSession()
    db.add(User(email="admin@peblo.local", password_hash=hash_password("peblo-admin"), role="admin"))
    db.add(User(email="editor@peblo.local", password_hash=hash_password("peblo-editor"), role="editor"))
    db.commit()
    db.close()

    dbmod.engine = engine
    dbmod.SessionLocal = TestingSession

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
