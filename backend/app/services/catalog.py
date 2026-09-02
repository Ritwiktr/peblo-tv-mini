from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Episode, Season, Show
from app.storage.base import StorageBackend

LIVE_KEY = "catalogues/catalogue.json"
TRAILER_SEASON = 0


def _art_map(storage: StorageBackend, records) -> dict[str, str]:
    return {a.kind: storage.url(a.storage_key) for a in records}


def build_catalogue(db: Session, storage: StorageBackend) -> tuple[dict[str, Any], list[str]]:
    """Build the published catalogue. Returns (document, warnings).

    Only published shows with a section, and published episodes that have
    duration + artwork, appear. content_group variants collapse into one
    entry with a languages list. Season 0 is attached as `trailer`, not a season.
    """
    warnings: list[str] = []
    shows = (
        db.execute(
            select(Show)
            .options(
                selectinload(Show.artwork),
                selectinload(Show.seasons).selectinload(Season.episodes).selectinload(Episode.artwork),
            )
            .order_by(Show.title)
        )
        .scalars()
        .all()
    )

    sections: dict[str, list] = defaultdict(list)
    show_count = 0
    episode_count = 0

    for show in shows:
        if show.status != "published":
            continue
        if not show.section:
            warnings.append(
                f"'{show.title}' is marked published but has no section, so it was left out of the catalogue."
            )
            continue

        seasons_out = []
        trailer = None
        for season in sorted(show.seasons, key=lambda s: s.season_number):
            grouped: dict[str, list[Episode]] = defaultdict(list)
            for ep in season.episodes:
                grouped[ep.content_group].append(ep)

            entries = []
            for cg, variants in grouped.items():
                published = [e for e in variants if e.status == "published"]
                if not published:
                    continue

                by_lang: dict[str, list[Episode]] = defaultdict(list)
                for e in published:
                    by_lang[e.language].append(e)
                chosen: list[Episode] = []
                for lang, rows in by_lang.items():
                    rows_sorted = sorted(rows, key=lambda r: (r.seed_id or str(r.id)))
                    chosen.append(rows_sorted[0])
                    if len(rows_sorted) > 1:
                        extras = ", ".join(r.seed_id or str(r.id) for r in rows_sorted[1:])
                        warnings.append(
                            f"Dropped duplicate {lang} variant(s) in '{cg}' ({extras}). "
                            "Each language should appear once per episode."
                        )

                eligible = []
                for e in chosen:
                    if not e.duration_seconds:
                        warnings.append(
                            f"Skipped '{e.title}' ({e.language}): published but missing a duration."
                        )
                        continue
                    if not e.artwork:
                        warnings.append(
                            f"Skipped '{e.title}' ({e.language}): published but has no artwork."
                        )
                        continue
                    eligible.append(e)
                if not eligible:
                    continue

                preferred = next((e for e in eligible if e.language == "en"), eligible[0])
                languages = sorted({e.language for e in eligible})
                variants_out = [
                    {
                        "episode_id": str(e.id),
                        "seed_id": e.seed_id,
                        "language": e.language,
                        "title": e.title,
                        "duration_seconds": e.duration_seconds,
                        "artwork": _art_map(storage, e.artwork),
                    }
                    for e in sorted(eligible, key=lambda x: x.language)
                ]
                entry = {
                    "content_group": cg,
                    "episode_number": preferred.episode_number,
                    "title": preferred.title,
                    "duration_seconds": preferred.duration_seconds,
                    "languages": languages,
                    "artwork": _art_map(storage, preferred.artwork),
                    "variants": variants_out,
                }
                episode_count += 1
                if season.season_number == TRAILER_SEASON:
                    trailer = entry
                else:
                    entries.append(entry)

            if season.season_number == TRAILER_SEASON:
                continue
            if entries:
                entries.sort(key=lambda e: (e["episode_number"], e["content_group"]))
                seasons_out.append({"season_number": season.season_number, "episodes": entries})

        show_art = _art_map(storage, show.artwork)
        sections[show.section].append(
            {
                "id": str(show.id),
                "slug": show.slug,
                "title": show.title,
                "synopsis": show.synopsis,
                "categories": show.categories or [],
                "section": show.section,
                "artwork": show_art,
                "trailer": trailer,
                "seasons": seasons_out,
            }
        )
        show_count += 1

    section_order = ["featured", "series", "minisodes", "songs"]
    titles = {
        "featured": "Featured",
        "series": "Series",
        "minisodes": "Minisodes",
        "songs": "Songs",
    }
    ordered = []
    for sid in section_order:
        if sid in sections:
            ordered.append({"id": sid, "title": titles.get(sid, sid.title()), "shows": sections[sid]})
    for sid, shows_list in sections.items():
        if sid not in section_order:
            ordered.append({"id": sid, "title": sid.title(), "shows": shows_list})

    doc = {
        "published_at": datetime.now(timezone.utc).isoformat(),
        "show_count": show_count,
        "episode_count": episode_count,
        "sections": ordered,
    }
    return doc, warnings
