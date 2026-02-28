from __future__ import annotations

import uuid
from pydantic import BaseModel


class BarberCard(BaseModel):
    notes: str | None = None
    guard: str | None = None
    top_length_cm: float | None = None


class StyleResult(BaseModel):
    rank: int
    style_id: uuid.UUID
    name: str
    slug: str
    score: float
    reasons: list[str]
    texture: str
    length: str
    maintenance: str
    view_front: str
    view_left: str
    view_right: str
    view_back: str
    barber_card: BarberCard


class JobResultsResponse(BaseModel):
    job_id: uuid.UUID
    head_shape: str | None
    styles: list[StyleResult]
