"""Upload rendered PNG views to MinIO results bucket."""
from __future__ import annotations

import os

import boto3
from botocore.config import Config


def upload_views(
    job_id: str,
    style_slug: str,
    view_paths: dict[str, str],
) -> dict[str, str]:
    """
    Upload each view PNG to MinIO.
    Returns dict of {view_name: public_url}.
    """
    endpoint = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
    access = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    secret = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    bucket = os.environ.get("MINIO_BUCKET_RESULTS", "hairstyle-results")

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name="us-east-1",
        config=Config(signature_version="s3v4"),
    )

    urls: dict[str, str] = {}
    for view_name, local_path in view_paths.items():
        key = f"results/{job_id}/{style_slug}/{view_name}.png"
        client.upload_file(
            local_path,
            bucket,
            key,
            ExtraArgs={"ContentType": "image/png"},
        )
        # Build a presigned GET URL valid for 24h
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=86400,
        )
        urls[view_name] = url
        os.unlink(local_path)

    return urls
