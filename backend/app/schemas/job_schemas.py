from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


class CreateJobRequest(BaseModel):
    pref_gender: Literal["male", "female", "unisex"] | None = None
    pref_length: Literal["short", "medium", "long"] | None = None
    pref_maintenance: Literal["low", "medium", "high"] | None = None


class CreateJobResponse(BaseModel):
    job_id: uuid.UUID
    upload_url: str
    upload_key: str
    expires_in_seconds: int


class StartJobResponse(BaseModel):
    job_id: uuid.UUID
    status: str


class JobStatusResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    progress: int
    error_message: str | None = None
    head_shape: str | None = None
