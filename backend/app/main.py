from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import User
from app.routers import admin, artwork, auth, catalog, cms, health
from app.schema import apply_schema
from app.services.catalog import LIVE_KEY
from app.services.publish import publish_catalogue
from app.services.seed import seed_content, seed_users
from app.storage import get_storage


@asynccontextmanager
async def lifespan(_app: FastAPI):
    apply_schema()
    settings = get_settings()
    db = SessionLocal()
    try:
        seed_users(db, settings)
        if settings.seed_on_startup:
            seed_content(db, get_storage(), settings)
        # First boot: publish whatever is eligible so the viewer isn't empty.
        # Remaining issues stay on the validation report for editors to fix.
        storage = get_storage()
        if not storage.exists(LIVE_KEY):
            admin = db.execute(select(User).where(User.role == "admin")).scalars().first()
            if admin:
                publish_catalogue(db, storage, admin)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Peblo TV Mini",
    description="CMS + published catalogue + viewer API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(cms.router)
app.include_router(artwork.router)
app.include_router(admin.router)
app.include_router(catalog.router)


@app.get("/media/{key:path}")
def media(key: str):
    storage = get_storage()
    if not storage.exists(key):
        raise HTTPException(404, "File not found.")
    data = storage.get(key)
    ctype = "application/octet-stream"
    if key.endswith(".json"):
        ctype = "application/json"
    elif key.endswith(".jpg") or key.endswith(".jpeg"):
        ctype = "image/jpeg"
    elif key.endswith(".png"):
        ctype = "image/png"
    elif key.endswith(".webp"):
        ctype = "image/webp"
    return Response(content=data, media_type=ctype, headers={"Cache-Control": "public, max-age=3600"})
