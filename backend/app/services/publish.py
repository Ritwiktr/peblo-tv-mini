from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import PublishRun, User
from app.services.catalog import LIVE_KEY, build_catalogue
from app.storage.base import StorageBackend


def publish_catalogue(db: Session, storage: StorageBackend, user: User | None) -> PublishRun:
    run = PublishRun(
        triggered_by_id=user.id if user else None,
        status="running",
        warnings=[],
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        doc, warnings = build_catalogue(db, storage)
        payload = json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8")
        version_key = f"catalogues/catalogue-{run.id}.json"
        storage.atomic_put_json(LIVE_KEY, version_key, payload)

        run.status = "success"
        run.show_count = doc["show_count"]
        run.episode_count = doc["episode_count"]
        run.catalogue_key = version_key
        run.warnings = warnings
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        return run
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        raise


def rollback_catalogue(db: Session, storage: StorageBackend, run: PublishRun, user: User) -> PublishRun:
    if run.status != "success" or not run.catalogue_key:
        raise ValueError("That run didn't produce a catalogue we can roll back to.")
    if not storage.exists(run.catalogue_key):
        raise ValueError("The file for that run is gone, so we can't restore it.")
    payload = storage.get(run.catalogue_key)
    new_run = PublishRun(
        triggered_by_id=user.id,
        status="running",
        warnings=[f"Rollback to run {run.id}"],
    )
    db.add(new_run)
    db.commit()
    db.refresh(new_run)
    version_key = f"catalogues/catalogue-{new_run.id}.json"
    storage.atomic_put_json(LIVE_KEY, version_key, payload)
    new_run.status = "success"
    new_run.catalogue_key = version_key
    new_run.show_count = run.show_count
    new_run.episode_count = run.episode_count
    new_run.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(new_run)
    return new_run


def load_live_catalogue(storage: StorageBackend) -> dict | None:
    if not storage.exists(LIVE_KEY):
        return None
    return json.loads(storage.get(LIVE_KEY))
