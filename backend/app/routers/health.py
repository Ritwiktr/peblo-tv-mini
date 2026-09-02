from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db import get_db
from app.storage import get_storage

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    storage = get_storage()
    live = False
    try:
        live = storage.exists("catalogues/catalogue.json")
    except Exception:
        live = False

    status = "ok" if db_ok else "degraded"
    return {
        "status": status,
        "database": "ok" if db_ok else "error",
        "catalogue_published": live,
    }
