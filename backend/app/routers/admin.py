from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import require_admin, require_editor
from app.models import IngestWarning, PublishRun, User
from app.schemas import PublishRunOut, ReferenceOut
from app.services.publish import publish_catalogue, rollback_catalogue
from app.services.validation import validation_report
from app.storage import get_storage
from app.config import get_settings
import json

router = APIRouter(prefix="/admin", tags=["publish"])


def _run_out(run: PublishRun) -> PublishRunOut:
    return PublishRunOut(
        id=run.id,
        status=run.status,
        show_count=run.show_count,
        episode_count=run.episode_count,
        catalogue_key=run.catalogue_key,
        error_message=run.error_message,
        warnings=run.warnings or [],
        triggered_by=run.triggered_by.email if run.triggered_by else None,
        started_at=run.started_at,
        finished_at=run.finished_at,
    )


@router.get("/reference", response_model=ReferenceOut)
def reference(_user: User = Depends(require_editor)):
    path = get_settings().reference_path
    if not path.exists():
        from pathlib import Path

        alt = Path(__file__).resolve().parents[3] / "data" / "reference.json"
        path = alt if alt.exists() else path
    data = json.loads(path.read_text())
    return data


@router.get("/validation-report")
def report(db: Session = Depends(get_db), _user: User = Depends(require_editor)):
    result = validation_report(db)
    ingest = db.execute(select(IngestWarning)).scalars().all()
    result["ingest_warnings"] = [{"code": w.code, "message": w.message} for w in ingest]
    return result


@router.post("/catalog/publish", response_model=PublishRunOut)
def publish(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    run = publish_catalogue(db, get_storage(), user)
    run = db.execute(
        select(PublishRun).options(selectinload(PublishRun.triggered_by)).where(PublishRun.id == run.id)
    ).scalar_one()
    return _run_out(run)


@router.get("/catalog/runs", response_model=list[PublishRunOut])
def runs(db: Session = Depends(get_db), _user: User = Depends(require_editor)):
    rows = (
        db.execute(
            select(PublishRun)
            .options(selectinload(PublishRun.triggered_by))
            .order_by(PublishRun.started_at.desc())
            .limit(50)
        )
        .scalars()
        .all()
    )
    return [_run_out(r) for r in rows]


@router.post("/catalog/runs/{run_id}/rollback", response_model=PublishRunOut)
def rollback(run_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    run = db.get(PublishRun, run_id)
    if not run:
        raise HTTPException(404, "We couldn't find that publish run.")
    try:
        new_run = rollback_catalogue(db, get_storage(), run, user)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    new_run = db.execute(
        select(PublishRun).options(selectinload(PublishRun.triggered_by)).where(PublishRun.id == new_run.id)
    ).scalar_one()
    return _run_out(new_run)
