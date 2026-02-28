from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.engine import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    # pending | queued | processing | completed | failed
    progress: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # User preferences collected at scan time
    pref_gender: Mapped[str | None] = mapped_column(String(16), nullable=True)
    pref_length: Mapped[str | None] = mapped_column(String(16), nullable=True)
    pref_maintenance: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # S3 keys
    upload_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    results_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # ML outputs
    head_shape: Mapped[str | None] = mapped_column(String(32), nullable=True)
    results_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class HairstyleCatalog(Base):
    __tablename__ = "hairstyle_catalog"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    gender: Mapped[str] = mapped_column(String(16), nullable=False)  # male|female|unisex
    texture: Mapped[str] = mapped_column(String(32), nullable=False)  # straight|wavy|curly|coily
    length: Mapped[str] = mapped_column(String(16), nullable=False)  # short|medium|long
    maintenance: Mapped[str] = mapped_column(String(16), nullable=False)  # low|medium|high

    # Head-shape compatibility scores (0.0–1.0)
    compat_oval: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    compat_round: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    compat_square: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    compat_heart: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    compat_oblong: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    compat_diamond: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    # Bonus modifiers
    bonus_curly_hair: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    bonus_fine_hair: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    bonus_thick_hair: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Barber instructions
    barber_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    barber_guard: Mapped[str | None] = mapped_column(String(32), nullable=True)
    top_length_cm: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 3-D mesh asset (optional for MVP)
    mesh_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    preview_s3_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
