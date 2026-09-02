from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.publish import load_live_catalogue
from app.services.search import search_catalogue
from app.storage import get_storage

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
def get_catalog():
    doc = load_live_catalogue(get_storage())
    if doc is None:
        raise HTTPException(
            404,
            "No catalogue has been published yet. An admin needs to publish from the CMS first.",
        )
    return JSONResponse(doc)


@router.get("/catalog/search")
def search(
    q: str | None = Query(None),
    category: str | None = Query(None),
    language: str | None = Query(None),
    section: str | None = Query(None),
):
    doc = load_live_catalogue(get_storage())
    if doc is None:
        raise HTTPException(404, "No catalogue has been published yet.")
    return search_catalogue(doc, q=q, category=category, language=language, section=section)
