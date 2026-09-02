from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_token, verify_password
from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == body.email.strip().lower())).scalar_one_or_none()
    if user is None:
        # emails in seed are mixed-case; try as-is
        user = db.execute(select(User).where(User.email == body.email.strip())).scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Email or password is wrong.")
    token = create_token(str(user.id), user.role, user.email)
    return TokenOut(access_token=token, role=user.role, email=user.email)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
