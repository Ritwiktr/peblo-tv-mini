from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.deps import require_editor
from app.models import Artwork, Episode, Show, User
from app.schemas import ArtworkOut
from app.services.artwork import ArtworkError, load_specs, validate_image
from app.storage import get_storage

router = APIRouter(prefix="/admin", tags=["artwork"])


def _out(a: Artwork) -> ArtworkOut:
    return ArtworkOut(
        id=a.id,
        kind=a.kind,
        url=get_storage().url(a.storage_key),
        width=a.width,
        height=a.height,
        byte_size=a.byte_size,
    )


async def _read_and_validate(file: UploadFile, kind: str) -> tuple[bytes, dict]:
    data = await file.read()
    specs = load_specs(get_settings().reference_path)
    try:
        meta = validate_image(data, kind, file.filename or "upload", specs)
    except ArtworkError as exc:
        raise HTTPException(status_code=422, detail={"message": exc.message, "code": exc.code})
    return data, meta


def _upsert(db: Session, *, show_id=None, episode_id=None, kind: str, key: str, meta: dict) -> Artwork:
    stmt = select(Artwork).where(Artwork.kind == kind)
    if show_id:
        stmt = stmt.where(Artwork.show_id == show_id)
    else:
        stmt = stmt.where(Artwork.episode_id == episode_id)
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        existing.storage_key = key
        existing.width = meta["width"]
        existing.height = meta["height"]
        existing.byte_size = meta["byte_size"]
        existing.content_type = meta["content_type"]
        return existing
    art = Artwork(
        show_id=show_id,
        episode_id=episode_id,
        kind=kind,
        storage_key=key,
        width=meta["width"],
        height=meta["height"],
        byte_size=meta["byte_size"],
        content_type=meta["content_type"],
    )
    db.add(art)
    return art


@router.post("/shows/{show_id}/artwork", response_model=ArtworkOut)
async def upload_show_artwork(
    show_id: UUID,
    kind: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user: User = Depends(require_editor),
):
    show = db.get(Show, show_id)
    if not show:
        raise HTTPException(404, "We couldn't find that show.")
    data, meta = await _read_and_validate(file, kind)
    ext = "jpg" if meta["content_type"] == "image/jpeg" else meta["content_type"].split("/")[-1]
    key = f"artwork/shows/{show_id}/{kind}.{ext}"
    get_storage().put(key, data, meta["content_type"])
    art = _upsert(db, show_id=show_id, kind=kind, key=key, meta=meta)
    db.commit()
    db.refresh(art)
    return _out(art)


@router.post("/episodes/{episode_id}/artwork", response_model=ArtworkOut)
async def upload_episode_artwork(
    episode_id: UUID,
    kind: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user: User = Depends(require_editor),
):
    ep = db.get(Episode, episode_id)
    if not ep:
        raise HTTPException(404, "We couldn't find that episode.")
    data, meta = await _read_and_validate(file, kind)
    ext = "jpg" if meta["content_type"] == "image/jpeg" else meta["content_type"].split("/")[-1]
    key = f"artwork/episodes/{episode_id}/{kind}.{ext}"
    get_storage().put(key, data, meta["content_type"])
    art = _upsert(db, episode_id=episode_id, kind=kind, key=key, meta=meta)
    db.commit()
    db.refresh(art)
    return _out(art)
