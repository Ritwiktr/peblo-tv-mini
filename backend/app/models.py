from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.db import Base


# JSONB on Postgres, JSON elsewhere (sqlite tests)
JSONType = JSON().with_variant(JSONB, "postgresql")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), index=True)  # editor | admin
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Show(Base):
    __tablename__ = "shows"
    __table_args__ = (
        Index("ix_shows_section_status", "section", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    synopsis: Mapped[str] = mapped_column(Text, default="")
    section: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    categories: Mapped[list] = mapped_column(JSONType, default=list)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    seasons: Mapped[list[Season]] = relationship(
        back_populates="show", cascade="all, delete-orphan", order_by="Season.season_number"
    )
    artwork: Mapped[list[Artwork]] = relationship(
        back_populates="show", cascade="all, delete-orphan", foreign_keys="Artwork.show_id"
    )


class Season(Base):
    __tablename__ = "seasons"
    __table_args__ = (UniqueConstraint("show_id", "season_number", name="uq_season_number"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    show_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shows.id", ondelete="CASCADE"), index=True)
    season_number: Mapped[int] = mapped_column(Integer)

    show: Mapped[Show] = relationship(back_populates="seasons")
    episodes: Mapped[list[Episode]] = relationship(
        back_populates="season", cascade="all, delete-orphan", order_by="Episode.episode_number"
    )


class Episode(Base):
    __tablename__ = "episodes"
    __table_args__ = (
        Index("ix_episodes_content_group_lang", "content_group", "language"),
        Index("ix_episodes_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    seed_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"), index=True)
    episode_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255), index=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(8), index=True)
    content_group: Mapped[str] = mapped_column(String(160), index=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    season: Mapped[Season] = relationship(back_populates="episodes")
    artwork: Mapped[list[Artwork]] = relationship(
        back_populates="episode", cascade="all, delete-orphan", foreign_keys="Artwork.episode_id"
    )


class Artwork(Base):
    __tablename__ = "artwork"
    __table_args__ = (
        Index("ix_artwork_show_kind", "show_id", "kind"),
        Index("ix_artwork_episode_kind", "episode_id", "kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    show_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("shows.id", ondelete="CASCADE"), nullable=True
    )
    episode_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(32))  # poster | banner | thumbnail
    storage_key: Mapped[str] = mapped_column(String(512))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    byte_size: Mapped[int] = mapped_column(Integer)
    content_type: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    show: Mapped[Optional[Show]] = relationship(back_populates="artwork", foreign_keys=[show_id])
    episode: Mapped[Optional[Episode]] = relationship(back_populates="artwork", foreign_keys=[episode_id])


class PublishRun(Base):
    __tablename__ = "publish_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    triggered_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="running", index=True)
    show_count: Mapped[int] = mapped_column(Integer, default=0)
    episode_count: Mapped[int] = mapped_column(Integer, default=0)
    catalogue_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    warnings: Mapped[list] = mapped_column(JSONType, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    triggered_by: Mapped[Optional[User]] = relationship()


class IngestWarning(Base):
    """Seed-time issues we want editors to see even if a row was skipped."""

    __tablename__ = "ingest_warnings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
