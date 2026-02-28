from __future__ import annotations

import boto3
from botocore.config import Config
from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def get_minio_client():
    """S3 client pointed at MinIO for upload presigned URLs."""
    return boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        region_name="us-east-1",
        config=Config(signature_version="s3v4"),
    )


@lru_cache(maxsize=1)
def get_sqs_client():
    """SQS client pointed at LocalStack."""
    return boto3.client(
        "sqs",
        endpoint_url=settings.localstack_endpoint,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_default_region,
    )
