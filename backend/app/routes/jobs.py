from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.engine import get_db
from app.db.models import Job
from app.dependencies import get_minio_client, get_sqs_client
from app.schemas.job_schemas import (
    CreateJobRequest,
    CreateJobResponse,
    JobStatusResponse,
    StartJobResponse,
)
from app.schemas.result_schemas import BarberCard, JobResultsResponse, StyleResult

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


# ─────────────────────────────────────────────────────────────────────────────
# POST /v1/jobs  — create job + presigned upload URL
# ─────────────────────────────────────────────────────────────────────────────
@router.post("", response_model=CreateJobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    body: CreateJobRequest,
    db: AsyncSession = Depends(get_db),
):
    job_id = uuid.uuid4()
    s3_key = f"uploads/{job_id}/video.mp4"

    # Generate presigned PUT URL (MinIO)
    minio = get_minio_client()
    try:
        upload_url = minio.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.minio_bucket_uploads,
                "Key": s3_key,
                "ContentType": "video/mp4",
            },
            ExpiresIn=settings.presigned_url_expiry_seconds,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not generate upload URL: {exc}")

    job = Job(
        id=job_id,
        status="pending",
        pref_gender=body.pref_gender,
        pref_length=body.pref_length,
        pref_maintenance=body.pref_maintenance,
        upload_s3_key=s3_key,
    )
    db.add(job)
    await db.flush()

    return CreateJobResponse(
        job_id=job_id,
        upload_url=upload_url,
        upload_key=s3_key,
        expires_in_seconds=settings.presigned_url_expiry_seconds,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /v1/jobs/{id}/start  — enqueue to SQS
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{job_id}/start", response_model=StartJobResponse)
async def start_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    job = await _get_job_or_404(db, job_id)

    if job.status not in ("pending",):
        raise HTTPException(
            status_code=400,
            detail=f"Job is already in status '{job.status}' and cannot be re-queued.",
        )

    # Send SQS message
    sqs = get_sqs_client()
    try:
        sqs.send_message(
            QueueUrl=settings.sqs_queue_url,
            MessageBody=json.dumps({"job_id": str(job_id)}),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not enqueue job: {exc}")

    job.status = "queued"
    await db.flush()

    return StartJobResponse(job_id=job_id, status="queued")


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/jobs/{id}  — status + progress
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    job = await _get_job_or_404(db, job_id)
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        head_shape=job.head_shape,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/jobs/{id}/results  — final results
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{job_id}/results", response_model=JobResultsResponse)
async def get_job_results(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    job = await _get_job_or_404(db, job_id)

    if job.status != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"Results not ready. Current status: {job.status}",
        )

    if not job.results_json:
        raise HTTPException(status_code=404, detail="No results found for this job.")

    styles = [
        StyleResult(
            rank=s["rank"],
            style_id=uuid.UUID(s["style_id"]),
            name=s["name"],
            slug=s["slug"],
            score=s["score"],
            reasons=s["reasons"],
            texture=s["texture"],
            length=s["length"],
            maintenance=s["maintenance"],
            view_front=s["view_front"],
            view_left=s["view_left"],
            view_right=s["view_right"],
            view_back=s["view_back"],
            barber_card=BarberCard(**s["barber_card"]),
        )
        for s in job.results_json
    ]

    return JobResultsResponse(
        job_id=job.id,
        head_shape=job.head_shape,
        styles=styles,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────
async def _get_job_or_404(db: AsyncSession, job_id: uuid.UUID) -> Job:
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job
