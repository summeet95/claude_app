"""001_create_jobs_table

Revision ID: 001
Revises:
Create Date: 2026-02-28
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("progress", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("pref_gender", sa.String(16), nullable=True),
        sa.Column("pref_length", sa.String(16), nullable=True),
        sa.Column("pref_maintenance", sa.String(16), nullable=True),
        sa.Column("upload_s3_key", sa.String(512), nullable=True),
        sa.Column("results_s3_key", sa.String(512), nullable=True),
        sa.Column("head_shape", sa.String(32), nullable=True),
        sa.Column("results_json", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_jobs_status", "jobs")
    op.drop_table("jobs")
