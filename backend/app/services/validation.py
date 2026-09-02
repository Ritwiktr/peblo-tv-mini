from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Episode, Season, Show


def validation_report(db: Session) -> dict[str, Any]:
    """Everything currently blocking a clean publish, grouped for an editor."""
    shows = (
        db.execute(
            select(Show).options(
                selectinload(Show.artwork),
                selectinload(Show.seasons).selectinload(Season.episodes).selectinload(Episode.artwork),
            )
        )
        .scalars()
        .all()
    )

    blocking: list[dict] = []
    warnings: list[dict] = []
    by_show: dict[str, dict] = {}

    def bucket(show: Show) -> dict:
        key = str(show.id)
        if key not in by_show:
            by_show[key] = {
                "show_id": key,
                "title": show.title,
                "slug": show.slug,
                "issues": [],
            }
        return by_show[key]

    # (content_group, language) collisions across the whole catalogue
    lang_map: dict[tuple[str, str], list[Episode]] = defaultdict(list)

    for show in shows:
        art_kinds = {a.kind for a in show.artwork}
        if show.status == "published" and not show.section:
            issue = {
                "code": "show_missing_section",
                "severity": "blocking",
                "message": f"'{show.title}' is published but has no section. Pick Featured, Series, Minisodes, or Songs.",
            }
            blocking.append(issue)
            bucket(show)["issues"].append(issue)

        if show.status == "published":
            missing = [k for k in ("poster", "banner", "thumbnail") if k not in art_kinds]
            if missing:
                labels = ", ".join(missing)
                issue = {
                    "code": "show_missing_artwork",
                    "severity": "blocking",
                    "message": f"'{show.title}' is published but missing {labels}. Upload them on the show page.",
                }
                blocking.append(issue)
                bucket(show)["issues"].append(issue)

        for season in show.seasons:
            for ep in season.episodes:
                lang_map[(ep.content_group, ep.language)].append(ep)
                if ep.status != "published":
                    continue
                if not ep.duration_seconds:
                    issue = {
                        "code": "episode_missing_duration",
                        "severity": "blocking",
                        "message": f"'{ep.title}' ({ep.language}) is published but has no duration. Add a length in seconds.",
                        "episode_id": str(ep.id),
                    }
                    blocking.append(issue)
                    bucket(show)["issues"].append(issue)
                if not ep.artwork:
                    issue = {
                        "code": "episode_missing_artwork",
                        "severity": "blocking",
                        "message": f"'{ep.title}' ({ep.language}) is published but has no artwork. Upload at least a thumbnail.",
                        "episode_id": str(ep.id),
                    }
                    blocking.append(issue)
                    bucket(show)["issues"].append(issue)

        if show.status == "draft":
            warnings.append(
                {
                    "code": "show_draft",
                    "severity": "info",
                    "message": f"'{show.title}' is still a draft, so it won't appear in the viewer.",
                }
            )

    title_map: dict[str, dict] = {}
    for show in shows:
        seen_local: set[str] = set()
        for season in show.seasons:
            for ep in season.episodes:
                key = ep.title.strip().lower()
                if key in seen_local:
                    continue
                seen_local.add(key)
                bucket = title_map.setdefault(key, {"sample": ep.title, "shows": []})
                if show.title not in bucket["shows"]:
                    bucket["shows"].append(show.title)
    for bucket in title_map.values():
        uniq = bucket["shows"]
        if len(uniq) >= 3:
            warnings.append(
                {
                    "code": "copied_episode_title",
                    "severity": "info",
                    "message": (
                        f"“{bucket['sample']}” is used as an episode title on {len(uniq)} shows "
                        f"({', '.join(uniq)}). If this was copy-paste from another series, rename them."
                    ),
                }
            )

    for (cg, lang), rows in lang_map.items():
        if len(rows) > 1:
            ids = ", ".join(r.seed_id or str(r.id) for r in rows)
            titles = " / ".join(sorted({r.title for r in rows}))
            issue = {
                "code": "duplicate_language_variant",
                "severity": "blocking",
                "message": (
                    f"Two {lang} versions share content group '{cg}' ({titles}; {ids}). "
                    "Keep one and delete or retag the other — language variants must be unique."
                ),
            }
            blocking.append(issue)
            # attach to the first show we can
            first = rows[0]
            bucket(first.season.show)["issues"].append(issue)

    can_publish = len(blocking) == 0
    return {
        "can_publish": can_publish,
        "blocking_count": len(blocking),
        "blocking": blocking,
        "warnings": warnings,
        "by_show": [v for v in by_show.values() if v["issues"]],
        "hint": (
            "Fix the blocking items, then ask an admin to publish."
            if not can_publish
            else "Looks good — an admin can publish this catalogue."
        ),
    }
