"""002_create_hairstyle_catalog

Revision ID: 002
Revises: 001
Create Date: 2026-02-28
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hairstyle_catalog",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("gender", sa.String(16), nullable=False),
        sa.Column("texture", sa.String(32), nullable=False),
        sa.Column("length", sa.String(16), nullable=False),
        sa.Column("maintenance", sa.String(16), nullable=False),
        # Head-shape compat scores
        sa.Column("compat_oval", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("compat_round", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("compat_square", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("compat_heart", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("compat_oblong", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("compat_diamond", sa.Float, nullable=False, server_default="0.5"),
        # Bonus modifiers
        sa.Column("bonus_curly_hair", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("bonus_fine_hair", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("bonus_thick_hair", sa.Float, nullable=False, server_default="0.0"),
        # Barber instructions
        sa.Column("barber_notes", sa.Text, nullable=True),
        sa.Column("barber_guard", sa.String(32), nullable=True),
        sa.Column("top_length_cm", sa.Float, nullable=True),
        # Assets
        sa.Column("mesh_s3_key", sa.String(512), nullable=True),
        sa.Column("preview_s3_key", sa.String(512), nullable=True),
    )
    op.create_index("ix_catalog_gender", "hairstyle_catalog", ["gender"])
    op.create_index("ix_catalog_length", "hairstyle_catalog", ["length"])


def downgrade() -> None:
    op.drop_index("ix_catalog_length", "hairstyle_catalog")
    op.drop_index("ix_catalog_gender", "hairstyle_catalog")
    op.drop_table("hairstyle_catalog")
