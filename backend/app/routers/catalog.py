from pathlib import Path
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.services.publish import load_live_catalogue
from app.services.search import search_catalogue
from app.storage import get_storage

router = APIRouter(tags=["catalog"])


def _live():
    doc = load_live_catalogue(get_storage())
    if doc is None:
        raise HTTPException(
            404,
            "No catalogue has been published yet. An admin needs to publish from the CMS first.",
        )
    return doc


@router.get("/catalog")
def get_catalog():
    return JSONResponse(_live())


@router.get("/catalog/meta")
def catalog_meta():
    """Public facet lists for the viewer. Sourced from reference.json, not the CMS."""
    path = get_settings().reference_path
    if not path.exists():
        alt = Path(__file__).resolve().parents[3] / "data" / "reference.json"
        path = alt if alt.exists() else path
    if not path.exists():
        raise HTTPException(404, "Reference file is missing.")
    data = json.loads(path.read_text())
    return {
        "sections": data.get("sections", []),
        "categories": data.get("categories", []),
        "languages": data.get("languages", []),
    }


@router.get("/catalog/shows/{slug}")
def catalog_show(slug: str):
    for section in _live().get("sections", []):
        for show in section.get("shows", []):
            if show.get("slug") == slug:
                return show
    raise HTTPException(404, "That title isn’t in the published catalogue.")


@router.get("/catalog/search")
def search(
    q: str | None = Query(None),
    category: str | None = Query(None),
    language: str | None = Query(None),
    section: str | None = Query(None),
):
    return search_catalogue(
        _live(), q=q, category=category, language=language, section=section
    )
