from __future__ import annotations

from typing import Any


def _haystack(show: dict, episode: dict | None = None) -> str:
    parts = [show.get("title") or "", show.get("synopsis") or ""]
    parts.extend(show.get("categories") or [])
    if episode:
        parts.append(episode.get("title") or "")
        parts.extend(episode.get("languages") or [])
    return " ".join(parts).lower()


def search_catalogue(
    catalogue: dict,
    q: str | None = None,
    category: str | None = None,
    language: str | None = None,
    section: str | None = None,
) -> dict[str, Any]:
    """Filter the published catalogue. All provided filters AND together.

    `q` matches show title, synopsis, category, and episode title.
    This is an in-memory scan of the published file — see README for scale notes.
    """
    qn = (q or "").strip().lower()
    cat = (category or "").strip().lower()
    lang = (language or "").strip().lower()
    sec = (section or "").strip().lower()

    matched_shows: list[dict] = []
    for block in catalogue.get("sections") or []:
        if sec and block.get("id", "").lower() != sec:
            continue
        for show in block.get("shows") or []:
            if cat and cat not in [c.lower() for c in (show.get("categories") or [])]:
                continue

            episode_hits = []
            for season in show.get("seasons") or []:
                for ep in season.get("episodes") or []:
                    if lang and lang not in [x.lower() for x in (ep.get("languages") or [])]:
                        continue
                    if qn and qn not in _haystack(show, ep):
                        continue
                    episode_hits.append({**ep, "season_number": season["season_number"]})

            # Show matches even with no episode hits when q matches the show itself
            # and language filter is satisfied by at least one episode (or no lang filter).
            show_matches_q = (not qn) or qn in _haystack(show)
            has_lang = True
            if lang:
                has_lang = any(
                    lang in [x.lower() for x in (ep.get("languages") or [])]
                    for season in show.get("seasons") or []
                    for ep in season.get("episodes") or []
                )
            if not has_lang:
                continue

            if episode_hits or (show_matches_q and not qn) or (show_matches_q and not episode_hits):
                if qn and not episode_hits and not show_matches_q:
                    continue
                if qn and not show_matches_q and not episode_hits:
                    continue
                matched_shows.append(
                    {
                        **show,
                        "section": block.get("id"),
                        "episode_hits": episode_hits if qn else [],
                    }
                )

    return {
        "q": q or "",
        "category": category or "",
        "language": language or "",
        "section": section or "",
        "count": len(matched_shows),
        "shows": matched_shows,
    }
