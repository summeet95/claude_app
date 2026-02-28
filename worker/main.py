"""
Worker main — SQS long-poll loop.
Picks up job messages, runs the full pipeline, updates Postgres.
"""
from __future__ import annotations

import json
import os
import shutil
import threading
import time
import uuid

import boto3
import psycopg2
import psycopg2.extras

from pipeline.downloader import download_video
from pipeline.face_analyzer import analyze_frames
from pipeline.frame_extractor import extract_frames
from pipeline.frame_selector import select_frames
from pipeline.head_fitter import fit_head
from pipeline.refiner import refine_views
from pipeline.renderer import render_views
from pipeline.style_selector import select_styles
from pipeline.uploader import upload_views


# ── Config ────────────────────────────────────────────────────────────────────
SQS_QUEUE_URL = os.environ.get(
    "SQS_QUEUE_URL",
    "http://localstack:4566/000000000000/hairstyle-jobs",
)
LOCALSTACK_ENDPOINT = os.environ.get("LOCALSTACK_ENDPOINT", "http://localstack:4566")
AWS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET = os.environ.get("AWS_SECRET_ACCESS_KEY", "test")
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

VISIBILITY_TIMEOUT = 1800  # 30 min
HEARTBEAT_INTERVAL = 300   # 5 min
WAIT_SECONDS = 20


def _sqs_client():
    return boto3.client(
        "sqs",
        endpoint_url=LOCALSTACK_ENDPOINT,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET,
        region_name=AWS_REGION,
    )


def _db_conn():
    return psycopg2.connect(
        os.environ.get(
            "DATABASE_SYNC_URL",
            "postgresql://hairstyle:hairstyle_secret@postgres:5432/hairstyle_db",
        ),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


# ── Progress helpers ──────────────────────────────────────────────────────────

def _set_progress(conn, job_id: str, status: str, progress: int):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE jobs SET status=%s, progress=%s, updated_at=NOW() WHERE id=%s",
            (status, progress, job_id),
        )
    conn.commit()


def _set_failed(conn, job_id: str, message: str):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE jobs SET status='failed', error_message=%s, updated_at=NOW() WHERE id=%s",
            (message, job_id),
        )
    conn.commit()


def _set_completed(conn, job_id: str, head_shape: str, results_json: list):
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE jobs
               SET status='completed', progress=100,
                   head_shape=%s, results_json=%s,
                   completed_at=NOW(), updated_at=NOW()
               WHERE id=%s""",
            (head_shape, json.dumps(results_json), job_id),
        )
    conn.commit()


def _get_job(conn, job_id: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM jobs WHERE id=%s", (job_id,))
        return cur.fetchone()


# ── Heartbeat ─────────────────────────────────────────────────────────────────

def _heartbeat_thread(sqs, receipt_handle: str, stop_event: threading.Event):
    while not stop_event.wait(HEARTBEAT_INTERVAL):
        try:
            sqs.change_message_visibility(
                QueueUrl=SQS_QUEUE_URL,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=VISIBILITY_TIMEOUT,
            )
            print("[heartbeat] Visibility timeout extended")
        except Exception as exc:
            print(f"[heartbeat] Failed: {exc}")


# ── Pipeline ──────────────────────────────────────────────────────────────────

def process_job(job_id: str):
    conn = _db_conn()
    try:
        job = _get_job(conn, job_id)
        if not job:
            print(f"[worker] Job {job_id} not found — skipping")
            return

        s3_key = job["upload_s3_key"]
        pref_gender = job["pref_gender"]
        pref_length = job["pref_length"]
        pref_maintenance = job["pref_maintenance"]

        _set_progress(conn, job_id, "processing", 5)

        # 1. Download
        print(f"[worker] [{job_id}] Downloading video")
        video_path = download_video(s3_key)
        _set_progress(conn, job_id, "processing", 15)

        # 2. Extract frames
        print(f"[worker] [{job_id}] Extracting frames")
        all_frames = extract_frames(video_path)
        os.unlink(video_path)
        _set_progress(conn, job_id, "processing", 25)

        # 3. Select best frames
        print(f"[worker] [{job_id}] Selecting frames")
        frames = select_frames(all_frames)
        _set_progress(conn, job_id, "processing", 35)

        # 4. Analyze face
        print(f"[worker] [{job_id}] Analyzing face")
        analysis = analyze_frames(frames)
        _set_progress(conn, job_id, "processing", 50)

        # 5. Fit head (DECA)
        print(f"[worker] [{job_id}] Fitting head model")
        head_params = fit_head(frames)
        _set_progress(conn, job_id, "processing", 60)

        # Cleanup frame files
        frame_dir = os.path.dirname(frames[0]) if frames else None
        if frame_dir and os.path.isdir(frame_dir):
            shutil.rmtree(frame_dir, ignore_errors=True)

        # 6. Select styles
        print(f"[worker] [{job_id}] Selecting styles")
        styles = select_styles(
            head_shape=analysis.head_shape,
            pref_gender=pref_gender,
            pref_length=pref_length,
            pref_maintenance=pref_maintenance,
            hair_texture=analysis.hair_texture,
        )
        _set_progress(conn, job_id, "processing", 70)

        # 7. Render + upload each style
        results_json = []
        progress_per_style = 25 // max(len(styles), 1)

        for rank, style in enumerate(styles, start=1):
            print(f"[worker] [{job_id}] Rendering style {style.slug} ({rank}/{len(styles)})")
            view_paths = render_views(
                style_slug=style.slug,
                head_scale=head_params.scale,
                head_centroid=head_params.centroid,
            )
            refine_views(view_paths)
            urls = upload_views(job_id, style.slug, view_paths)

            results_json.append({
                "rank": rank,
                "style_id": style.style_id,
                "name": style.name,
                "slug": style.slug,
                "score": round(style.score, 4),
                "reasons": style.reasons,
                "texture": style.texture,
                "length": style.length,
                "maintenance": style.maintenance,
                "view_front": urls.get("front", ""),
                "view_left": urls.get("left", ""),
                "view_right": urls.get("right", ""),
                "view_back": urls.get("back", ""),
                "barber_card": {
                    "notes": style.barber_notes,
                    "guard": style.barber_guard,
                    "top_length_cm": style.top_length_cm,
                },
            })
            _set_progress(conn, job_id, "processing", min(70 + rank * progress_per_style, 95))

        _set_completed(conn, job_id, analysis.head_shape, results_json)
        print(f"[worker] [{job_id}] Completed — {len(results_json)} styles")

    except Exception as exc:
        print(f"[worker] [{job_id}] FAILED: {exc}")
        try:
            _set_failed(conn, job_id, str(exc))
        except Exception:
            pass
        raise
    finally:
        conn.close()


# ── Poll loop ─────────────────────────────────────────────────────────────────

def main():
    print("[worker] Starting SQS poll loop")
    sqs = _sqs_client()

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=WAIT_SECONDS,
                VisibilityTimeout=VISIBILITY_TIMEOUT,
                AttributeNames=["All"],
            )
        except Exception as exc:
            print(f"[worker] SQS receive error: {exc} — retrying in 5s")
            time.sleep(5)
            continue

        messages = response.get("Messages", [])
        if not messages:
            continue

        msg = messages[0]
        receipt = msg["ReceiptHandle"]

        stop_event = threading.Event()
        hb = threading.Thread(
            target=_heartbeat_thread,
            args=(sqs, receipt, stop_event),
            daemon=True,
        )
        hb.start()

        try:
            body = json.loads(msg["Body"])
            job_id = body["job_id"]
            print(f"[worker] Received job {job_id}")
            process_job(job_id)

            sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt)
            print(f"[worker] Deleted message for job {job_id}")
        except Exception as exc:
            print(f"[worker] Processing error: {exc} — message will re-appear after timeout")
        finally:
            stop_event.set()


if __name__ == "__main__":
    main()
