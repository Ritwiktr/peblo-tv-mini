"""index publish_runs.started_at for the CMS history list (newest first).

Revision ID: 002
Revises: 001
Create Date: 2026-09-02
"""

from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_publish_runs_started_at", "publish_runs", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_publish_runs_started_at", table_name="publish_runs")
