"""initial schema: shows, seasons, episodes, artwork, publish runs, users

Revision ID: 001
Revises:
Create Date: 2026-09-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "shows",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(160), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("synopsis", sa.Text(), nullable=False, server_default=""),
        sa.Column("section", sa.String(64), nullable=True),
        sa.Column("categories", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_shows_slug", "shows", ["slug"], unique=True)
    op.create_index("ix_shows_title", "shows", ["title"])
    op.create_index("ix_shows_section", "shows", ["section"])
    op.create_index("ix_shows_status", "shows", ["status"])
    op.create_index("ix_shows_section_status", "shows", ["section", "status"])

    op.create_table(
        "seasons",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("show_id", sa.Uuid(), sa.ForeignKey("shows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("season_number", sa.Integer(), nullable=False),
        sa.UniqueConstraint("show_id", "season_number", name="uq_season_number"),
    )
    op.create_index("ix_seasons_show_id", "seasons", ["show_id"])

    op.create_table(
        "episodes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("seed_id", sa.String(64), nullable=True),
        sa.Column("season_id", sa.Uuid(), sa.ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(8), nullable=False),
        sa.Column("content_group", sa.String(160), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_episodes_seed_id", "episodes", ["seed_id"], unique=True)
    op.create_index("ix_episodes_season_id", "episodes", ["season_id"])
    op.create_index("ix_episodes_title", "episodes", ["title"])
    op.create_index("ix_episodes_language", "episodes", ["language"])
    op.create_index("ix_episodes_content_group", "episodes", ["content_group"])
    op.create_index("ix_episodes_status", "episodes", ["status"])
    op.create_index("ix_episodes_content_group_lang", "episodes", ["content_group", "language"])

    op.create_table(
        "artwork",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("show_id", sa.Uuid(), sa.ForeignKey("shows.id", ondelete="CASCADE"), nullable=True),
        sa.Column("episode_id", sa.Uuid(), sa.ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("storage_key", sa.String(512), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_artwork_show_kind", "artwork", ["show_id", "kind"])
    op.create_index("ix_artwork_episode_kind", "artwork", ["episode_id", "kind"])

    op.create_table(
        "publish_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("triggered_by_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="running"),
        sa.Column("show_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("episode_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("catalogue_key", sa.String(512), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("warnings", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_publish_runs_status", "publish_runs", ["status"])

    op.create_table(
        "ingest_warnings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ingest_warnings_code", "ingest_warnings", ["code"])


def downgrade() -> None:
    op.drop_table("ingest_warnings")
    op.drop_table("publish_runs")
    op.drop_table("artwork")
    op.drop_table("episodes")
    op.drop_table("seasons")
    op.drop_table("shows")
    op.drop_table("users")
