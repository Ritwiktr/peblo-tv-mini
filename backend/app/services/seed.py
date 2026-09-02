from __future__ import annotations

import io
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import Settings
from app.models import Artwork, Episode, IngestWarning, Season, Show, User
from app.services.artwork import load_specs
from app.storage.base import StorageBackend

SHOW_COLORS = {
    "motis-many-lives": (196, 90, 42),
    "tiny-tales-banyan-dadi": (46, 120, 72),
    "discover-india-with-moti": (214, 122, 36),
    "peblo-songs": (108, 64, 160),
    "peblo-songs-lyrical": (176, 72, 120),
    "curious-cubs": (32, 128, 140),
    "number-nest": (40, 88, 168),
    "rhyme-rangers": (180, 140, 32),
}


def _placeholder(kind: str, color: tuple[int, int, int], label: str, specs: dict) -> bytes:
    w, h = specs[kind]["target_px"]
    img = Image.new("RGB", (w, h), color)
    d = ImageDraw.Draw(img)
    d.rectangle([12, 12, w - 12, h - 12], outline=(255, 255, 255), width=6)
    d.text((28, 28), label[:48], fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82, optimize=True)
    return buf.getvalue()


def seed_users(db: Session, settings: Settings) -> None:
    existing = {u.email for u in db.execute(select(User)).scalars()}
    if settings.admin_email not in existing:
        db.add(
            User(
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                role="admin",
            )
        )
    if settings.editor_email not in existing:
        db.add(
            User(
                email=settings.editor_email,
                password_hash=hash_password(settings.editor_password),
                role="editor",
            )
        )
    db.commit()


def seed_content(db: Session, storage: StorageBackend, settings: Settings) -> None:
    if db.execute(select(Show)).scalars().first():
        return

    path = Path(settings.seed_shows_path)
    if not path.exists():
        # local-dev fallback: repo data/
        alt = Path(__file__).resolve().parents[3] / "data" / "seed_shows.json"
        path = alt if alt.exists() else path
    if not path.exists():
        return

    rows = json.loads(path.read_text())
    ref_path = Path(settings.reference_path)
    if not ref_path.exists():
        alt = Path(__file__).resolve().parents[3] / "data" / "reference.json"
        ref_path = alt if alt.exists() else ref_path
    specs = load_specs(ref_path if ref_path.exists() else None)

    by_slug: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_slug[row["slug"]].append(row)

    seen_group_lang: dict[tuple[str, str], str] = {}

    for slug, eps in by_slug.items():
        head = eps[0]
        statuses = {e["status"] for e in eps}
        show_status = "published" if "published" in statuses and "draft" not in statuses else (
            "published" if any(e["status"] == "published" for e in eps) else "draft"
        )
        # Number Nest mixes published+draft → keep show published so the ready eps can ship
        if any(e["status"] == "published" for e in eps) and head.get("section"):
            show_status = "published"
        if not head.get("section"):
            show_status = "draft"

        show = Show(
            slug=slug,
            title=head["show_title"],
            synopsis=head.get("synopsis") or "",
            section=head.get("section"),
            categories=head.get("categories") or [],
            status=show_status,
        )
        db.add(show)
        db.flush()

        color = SHOW_COLORS.get(slug, (80, 80, 80))
        # Show-level artwork from the union of episode artwork flags (if any episode has it)
        needed = set()
        for e in eps:
            needed.update(e.get("artwork_available") or [])
        for kind in ("poster", "banner", "thumbnail"):
            if kind in needed:
                blob = _placeholder(kind, color, f"{head['show_title']}\n{kind}", specs)
                key = f"artwork/shows/{show.id}/{kind}.jpg"
                storage.put(key, blob, "image/jpeg")
                db.add(
                    Artwork(
                        show_id=show.id,
                        kind=kind,
                        storage_key=key,
                        width=specs[kind]["target_px"][0],
                        height=specs[kind]["target_px"][1],
                        byte_size=len(blob),
                        content_type="image/jpeg",
                    )
                )

        seasons: dict[int, Season] = {}
        for e in eps:
            n = e["season_number"]
            if n not in seasons:
                seasons[n] = Season(show_id=show.id, season_number=n)
                db.add(seasons[n])
                db.flush()

            pair = (e["content_group"], e["language"])
            if pair in seen_group_lang:
                db.add(
                    IngestWarning(
                        code="duplicate_language_variant",
                        message=(
                            f"Seed row {e['episode_id']} ('{e['episode_title']}') reuses "
                            f"content_group '{e['content_group']}' + language '{e['language']}', "
                            f"already taken by {seen_group_lang[pair]}. Imported anyway so you can fix it."
                        ),
                        payload={"episode_id": e["episode_id"], "content_group": e["content_group"]},
                    )
                )
            seen_group_lang[pair] = e["episode_id"]

            ep = Episode(
                seed_id=e["episode_id"],
                season_id=seasons[n].id,
                episode_number=e["episode_number"],
                title=e["episode_title"],
                duration_seconds=e.get("duration_seconds"),
                language=e["language"],
                content_group=e["content_group"],
                status=e["status"],
            )
            db.add(ep)
            db.flush()

            for kind in e.get("artwork_available") or []:
                blob = _placeholder(kind, color, f"{e['episode_title']}\n{kind}", specs)
                key = f"artwork/episodes/{ep.id}/{kind}.jpg"
                storage.put(key, blob, "image/jpeg")
                db.add(
                    Artwork(
                        episode_id=ep.id,
                        kind=kind,
                        storage_key=key,
                        width=specs[kind]["target_px"][0],
                        height=specs[kind]["target_px"][1],
                        byte_size=len(blob),
                        content_type="image/jpeg",
                    )
                )

    db.commit()
