from __future__ import annotations

import json
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── API ───────────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    presigned_url_expiry_seconds: int = 900

    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://hairstyle:hairstyle_secret@localhost:5432/hairstyle_db"
    database_sync_url: str = "postgresql://hairstyle:hairstyle_secret@localhost:5432/hairstyle_db"

    # ── MinIO (uploads) ───────────────────────────────────────────────────────
    minio_endpoint: str = "http://minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_uploads: str = "hairstyle-uploads"
    minio_bucket_results: str = "hairstyle-results"

    # ── LocalStack / SQS ─────────────────────────────────────────────────────
    localstack_endpoint: str = "http://localstack:4566"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    aws_default_region: str = "us-east-1"
    sqs_queue_url: str = "http://localstack:4566/000000000000/hairstyle-jobs"


settings = Settings()
