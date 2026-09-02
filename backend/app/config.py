from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://peblo:peblo@localhost:5432/peblo"
    jwt_secret: str = "dev-secret"
    jwt_expire_minutes: int = 480
    public_base_url: str = "http://localhost:8000"

    admin_email: str = "admin@peblo.local"
    admin_password: str = "peblo-admin"
    editor_email: str = "editor@peblo.local"
    editor_password: str = "peblo-editor"

    seed_on_startup: bool = True
    seed_shows_path: Path = Path("/seed/seed_shows.json")
    reference_path: Path = Path("/seed/reference.json")

    storage_backend: str = "local"
    storage_local_path: Path = Path("/storage")

    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = "peblo-tv"
    r2_public_base_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
