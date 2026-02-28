"""Download the uploaded video from MinIO."""
from __future__ import annotations

import os
import tempfile

import boto3
from botocore.config import Config


def download_video(s3_key: str) -> str:
    """
    Download *s3_key* from the MinIO uploads bucket.
    Returns the path to a temp file (caller must delete).
    """
    minio_endpoint = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
    minio_access = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    bucket = os.environ.get("MINIO_BUCKET_UPLOADS", "hairstyle-uploads")

    client = boto3.client(
        "s3",
        endpoint_url=minio_endpoint,
        aws_access_key_id=minio_access,
        aws_secret_access_key=minio_secret,
        region_name="us-east-1",
        config=Config(signature_version="s3v4"),
    )

    suffix = os.path.splitext(s3_key)[-1] or ".mp4"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()

    print(f"[downloader] Downloading s3://{bucket}/{s3_key} → {tmp.name}")
    client.download_file(bucket, s3_key, tmp.name)
    return tmp.name
