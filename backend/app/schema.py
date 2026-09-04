"""Apply schema on boot.

Postgres uses Alembic so the migration files are the source of truth.
SQLite tests use create_all — the initial migration is JSONB/Postgres-only.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect

from app.config import get_settings
from app.models import Base


def apply_schema() -> None:
    from app.db import engine

    url = get_settings().database_url
    if url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        return

    from alembic import command
    from alembic.config import Config

    ini = Path(__file__).resolve().parent.parent / "alembic.ini"
    cfg = Config(str(ini))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", str(ini.parent / "alembic"))

    tables = set(inspect(engine).get_table_names())
    if "alembic_version" not in tables:
        if "shows" in tables:
            # Earlier boots used create_all. Don't try to recreate tables.
            command.stamp(cfg, "head")
            return
        command.upgrade(cfg, "head")
        return
    command.upgrade(cfg, "head")
