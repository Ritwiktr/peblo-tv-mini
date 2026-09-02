from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str


class UserOut(BaseModel):
    id: UUID
    email: str
    role: str

    model_config = {"from_attributes": True}


class ShowIn(BaseModel):
    title: str
    slug: Optional[str] = None
    synopsis: str = ""
    section: Optional[str] = None
    categories: list[str] = Field(default_factory=list)
    status: str = "draft"


class ShowPatch(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    synopsis: Optional[str] = None
    section: Optional[str] = None
    categories: Optional[list[str]] = None
    status: Optional[str] = None


class ArtworkOut(BaseModel):
    id: UUID
    kind: str
    url: str
    width: int
    height: int
    byte_size: int

    model_config = {"from_attributes": True}


class EpisodeIn(BaseModel):
    title: str
    season_number: int = 1
    episode_number: int = 1
    duration_seconds: Optional[int] = None
    language: str = "en"
    content_group: Optional[str] = None
    status: str = "draft"


class EpisodePatch(BaseModel):
    title: Optional[str] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    duration_seconds: Optional[int] = None
    language: Optional[str] = None
    content_group: Optional[str] = None
    status: Optional[str] = None


class EpisodeOut(BaseModel):
    id: UUID
    seed_id: Optional[str]
    title: str
    season_number: int
    episode_number: int
    duration_seconds: Optional[int]
    language: str
    content_group: str
    status: str
    artwork: list[ArtworkOut]

    model_config = {"from_attributes": True}


class ShowOut(BaseModel):
    id: UUID
    slug: str
    title: str
    synopsis: str
    section: Optional[str]
    categories: list
    status: str
    episode_count: int = 0
    artwork: list[ArtworkOut] = []
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ShowListOut(BaseModel):
    items: list[ShowOut]
    total: int
    page: int
    page_size: int


class PublishRunOut(BaseModel):
    id: UUID
    status: str
    show_count: int
    episode_count: int
    catalogue_key: Optional[str]
    error_message: Optional[str]
    warnings: list = []
    triggered_by: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ReferenceOut(BaseModel):
    sections: list[str]
    categories: list[str]
    languages: list[str]
    artwork_specs: dict
    conventions: dict
