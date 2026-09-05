from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import require_editor
from app.models import Artwork, Episode, Season, Show, User
from app.schemas import EpisodeIn, EpisodeOut, EpisodePatch, ShowIn, ShowListOut, ShowOut, ShowPatch, ArtworkOut
from app.services.publish import publish_catalogue
from app.storage import get_storage

router = APIRouter(prefix="/admin", tags=["cms"])

ALLOWED_SECTIONS = {"featured", "series", "minisodes", "songs"}
ALLOWED_STATUS = {"draft", "published"}
ALLOWED_LANG = {"en", "hi"}


def _slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s or "show"


def _list_on_viewer(db: Session, user: User) -> None:
    """Admins: rewrite the live catalogue so a published+sectioned show is listed."""
    if user.role != "admin":
        return
    publish_catalogue(db, get_storage(), user)


def _art_out(records: list[Artwork]) -> list[ArtworkOut]:
    storage = get_storage()
    return [
        ArtworkOut(
            id=a.id,
            kind=a.kind,
            url=storage.url(a.storage_key),
            width=a.width,
            height=a.height,
            byte_size=a.byte_size,
        )
        for a in records
    ]


def _episode_count(show: Show) -> int:
    return sum(len(s.episodes) for s in show.seasons)


def _show_out(show: Show) -> ShowOut:
    return ShowOut(
        id=show.id,
        slug=show.slug,
        title=show.title,
        synopsis=show.synopsis,
        section=show.section,
        categories=show.categories or [],
        status=show.status,
        episode_count=_episode_count(show),
        artwork=_art_out(show.artwork),
        created_at=show.created_at,
    )


def _ep_out(ep: Episode) -> EpisodeOut:
    return EpisodeOut(
        id=ep.id,
        seed_id=ep.seed_id,
        title=ep.title,
        season_number=ep.season.season_number,
        episode_number=ep.episode_number,
        duration_seconds=ep.duration_seconds,
        language=ep.language,
        content_group=ep.content_group,
        status=ep.status,
        artwork=_art_out(ep.artwork),
    )


def _get_or_create_season(db: Session, show: Show, number: int) -> Season:
    season = next((s for s in show.seasons if s.season_number == number), None)
    if season:
        return season
    season = Season(show_id=show.id, season_number=number)
    db.add(season)
    db.flush()
    return season


@router.get("/shows", response_model=ShowListOut)
def list_shows(
    q: str | None = None,
    section: str | None = None,
    status: str | None = None,
    language: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: User = Depends(require_editor),
):
    stmt = select(Show).options(selectinload(Show.artwork), selectinload(Show.seasons).selectinload(Season.episodes))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Show.title.ilike(like), Show.slug.ilike(like), Show.synopsis.ilike(like)))
    if section:
        stmt = stmt.where(Show.section == section)
    if status:
        stmt = stmt.where(Show.status == status)
    if language:
        stmt = (
            stmt.join(Show.seasons)
            .join(Season.episodes)
            .where(Episode.language == language)
            .distinct()
        )

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = (
        db.execute(stmt.order_by(Show.title).offset((page - 1) * page_size).limit(page_size))
        .scalars()
        .all()
    )
    return ShowListOut(items=[_show_out(s) for s in rows], total=total, page=page, page_size=page_size)


@router.post("/shows", response_model=ShowOut, status_code=201)
def create_show(body: ShowIn, db: Session = Depends(get_db), _user: User = Depends(require_editor)):
    if body.status not in ALLOWED_STATUS:
        raise HTTPException(400, "Status must be draft or published.")
    if body.section and body.section not in ALLOWED_SECTIONS:
        raise HTTPException(400, f"Section must be one of: {', '.join(sorted(ALLOWED_SECTIONS))}.")
    if body.status == "published" and not body.section:
        raise HTTPException(400, "A published show needs a section so it can appear in the viewer.")
    slug = body.slug or _slugify(body.title)
    if db.execute(select(Show).where(Show.slug == slug)).scalar_one_or_none():
        raise HTTPException(409, f"A show with slug '{slug}' already exists.")
    show = Show(
        title=body.title.strip(),
        slug=slug,
        synopsis=body.synopsis,
        section=body.section,
        categories=body.categories,
        status=body.status,
    )
    db.add(show)
    db.commit()
    db.refresh(show)
    if show.status == "published":
        _list_on_viewer(db, _user)
    return _show_out(show)


@router.get("/shows/{show_id}", response_model=ShowOut)
def get_show(show_id: UUID, db: Session = Depends(get_db), _user: User = Depends(require_editor)):
    show = db.execute(
        select(Show)
        .options(selectinload(Show.artwork), selectinload(Show.seasons).selectinload(Season.episodes))
        .where(Show.id == show_id)
    ).scalar_one_or_none()
    if not show:
        raise HTTPException(404, "We couldn't find that show.")
    return _show_out(show)


@router.patch("/shows/{show_id}", response_model=ShowOut)
def patch_show(
    show_id: UUID, body: ShowPatch, db: Session = Depends(get_db), _user: User = Depends(require_editor)
):
    show = db.get(Show, show_id)
    if not show:
        raise HTTPException(404, "We couldn't find that show.")
    data = body.model_dump(exclude_unset=True)
    if "status" in data and data["status"] not in ALLOWED_STATUS:
        raise HTTPException(400, "Status must be draft or published.")
    if "section" in data and data["section"] and data["section"] not in ALLOWED_SECTIONS:
        raise HTTPException(400, f"Section must be one of: {', '.join(sorted(ALLOWED_SECTIONS))}.")
    old_status = show.status
    new_status = data.get("status", show.status)
    new_section = data.get("section", show.section)
    if new_status == "published" and not new_section:
        raise HTTPException(400, "A published show needs a section so it can appear in the viewer.")
    if "slug" in data:
        other = db.execute(select(Show).where(Show.slug == data["slug"], Show.id != show.id)).scalar_one_or_none()
        if other:
            raise HTTPException(409, f"A show with slug '{data['slug']}' already exists.")
    for k, v in data.items():
        setattr(show, k, v)
    db.commit()
    show = db.execute(
        select(Show)
        .options(selectinload(Show.artwork), selectinload(Show.seasons).selectinload(Season.episodes))
        .where(Show.id == show_id)
    ).scalar_one()
    if old_status == "published" or show.status == "published":
        _list_on_viewer(db, _user)
    return _show_out(show)


@router.delete("/shows/{show_id}", status_code=204)
def delete_show(show_id: UUID, db: Session = Depends(get_db), _user: User = Depends(require_editor)):
    show = db.get(Show, show_id)
    if not show:
        raise HTTPException(404, "We couldn't find that show.")
    was_live = show.status == "published"
    db.delete(show)
    db.commit()
    if was_live:
        _list_on_viewer(db, _user)


@router.get("/shows/{show_id}/episodes", response_model=list[EpisodeOut])
def list_episodes(
    show_id: UUID,
    q: str | None = None,
    language: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_editor),
):
    show = db.execute(
        select(Show)
        .options(selectinload(Show.seasons).selectinload(Season.episodes).selectinload(Episode.artwork))
        .where(Show.id == show_id)
    ).scalar_one_or_none()
    if not show:
        raise HTTPException(404, "We couldn't find that show.")
    eps: list[Episode] = []
    for season in show.seasons:
        eps.extend(season.episodes)
    if q:
        ql = q.lower()
        eps = [e for e in eps if ql in e.title.lower() or ql in e.content_group.lower()]
    if language:
        eps = [e for e in eps if e.language == language]
    if status:
        eps = [e for e in eps if e.status == status]
    eps.sort(key=lambda e: (e.season.season_number, e.episode_number, e.language))
    return [_ep_out(e) for e in eps]


@router.post("/shows/{show_id}/episodes", response_model=EpisodeOut, status_code=201)
def create_episode(
    show_id: UUID, body: EpisodeIn, db: Session = Depends(get_db), _user: User = Depends(require_editor)
):
    show = db.execute(
        select(Show).options(selectinload(Show.seasons)).where(Show.id == show_id)
    ).scalar_one_or_none()
    if not show:
        raise HTTPException(404, "We couldn't find that show.")
    if body.language not in ALLOWED_LANG:
        raise HTTPException(400, "Language must be en or hi.")
    if body.status not in ALLOWED_STATUS:
        raise HTTPException(400, "Status must be draft or published.")
    if body.status == "published" and not body.duration_seconds:
        raise HTTPException(400, "A published episode needs a duration (in seconds).")
    cg = body.content_group or f"{show.slug}-s{body.season_number:02d}e{body.episode_number:02d}"
    clash = db.execute(
        select(Episode).where(Episode.content_group == cg, Episode.language == body.language)
    ).scalar_one_or_none()
    if clash:
        raise HTTPException(
            409,
            f"There's already a {body.language} version of this episode (content group '{cg}'). "
            "Edit that one, or pick a different content group.",
        )
    season = _get_or_create_season(db, show, body.season_number)
    ep = Episode(
        season_id=season.id,
        episode_number=body.episode_number,
        title=body.title.strip(),
        duration_seconds=body.duration_seconds,
        language=body.language,
        content_group=cg,
        status=body.status,
    )
    db.add(ep)
    db.commit()
    ep = db.execute(
        select(Episode).options(selectinload(Episode.artwork), selectinload(Episode.season)).where(Episode.id == ep.id)
    ).scalar_one()
    return _ep_out(ep)


@router.patch("/episodes/{episode_id}", response_model=EpisodeOut)
def patch_episode(
    episode_id: UUID, body: EpisodePatch, db: Session = Depends(get_db), _user: User = Depends(require_editor)
):
    ep = db.execute(
        select(Episode)
        .options(selectinload(Episode.season).selectinload(Season.show), selectinload(Episode.artwork))
        .where(Episode.id == episode_id)
    ).scalar_one_or_none()
    if not ep:
        raise HTTPException(404, "We couldn't find that episode.")
    data = body.model_dump(exclude_unset=True)
    if "language" in data and data["language"] not in ALLOWED_LANG:
        raise HTTPException(400, "Language must be en or hi.")
    if "status" in data and data["status"] not in ALLOWED_STATUS:
        raise HTTPException(400, "Status must be draft or published.")
    new_status = data.get("status", ep.status)
    new_duration = data.get("duration_seconds", ep.duration_seconds)
    if new_status == "published" and not new_duration:
        raise HTTPException(400, "A published episode needs a duration (in seconds).")
    if new_status == "published" and not ep.artwork:
        raise HTTPException(400, "A published episode needs artwork. Upload a thumbnail first.")
    if "season_number" in data:
        show = ep.season.show
        show = db.execute(
            select(Show).options(selectinload(Show.seasons)).where(Show.id == show.id)
        ).scalar_one()
        ep.season = _get_or_create_season(db, show, data.pop("season_number"))
        ep.season_id = ep.season.id
    cg = data.get("content_group", ep.content_group)
    lang = data.get("language", ep.language)
    clash = db.execute(
        select(Episode).where(
            Episode.content_group == cg, Episode.language == lang, Episode.id != ep.id
        )
    ).scalar_one_or_none()
    if clash:
        raise HTTPException(
            409,
            f"There's already a {lang} version of content group '{cg}'.",
        )
    for k, v in data.items():
        setattr(ep, k, v)
    db.commit()
    ep = db.execute(
        select(Episode).options(selectinload(Episode.artwork), selectinload(Episode.season)).where(Episode.id == episode_id)
    ).scalar_one()
    return _ep_out(ep)


@router.delete("/episodes/{episode_id}", status_code=204)
def delete_episode(episode_id: UUID, db: Session = Depends(get_db), _user: User = Depends(require_editor)):
    ep = db.get(Episode, episode_id)
    if not ep:
        raise HTTPException(404, "We couldn't find that episode.")
    db.delete(ep)
    db.commit()
