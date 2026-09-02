from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth import decode_token
from app.db import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please sign in.")
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session expired. Please sign in again.")
    user = db.get(User, UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please sign in.")
    return user


def require_editor(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role not in ("editor", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You need an editor account to do this.")
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "admin":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only admins can publish the catalogue. Ask an admin, or sign in as one.",
        )
    return user
