"""
Download DECA model weights from the S3 model-cache bucket.
FLAME model weights require a separate manual upload (license-gated).

Run this once before enabling DECA:
  python -m models.download_deca_weights
"""
from __future__ import annotations

import os
import tarfile
import tempfile

import boto3
from botocore.config import Config


DECA_WEIGHTS_BUCKET = os.environ.get("DECA_WEIGHTS_S3_BUCKET", "hairstyle-model-cache")
DECA_WEIGHTS_KEY = os.environ.get("DECA_WEIGHTS_S3_KEY", "deca/deca_model.tar")
DECA_LOCAL_DIR = os.path.expanduser("~/.deca_weights")


def _s3_client():
    endpoint = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin"),
        region_name="us-east-1",
        config=Config(signature_version="s3v4"),
    )


def download_if_needed() -> str:
    """Download weights tarball and extract. Returns local directory path."""
    flag = os.path.join(DECA_LOCAL_DIR, ".downloaded")
    if os.path.exists(flag):
        print(f"[deca_weights] Already downloaded at {DECA_LOCAL_DIR}")
        return DECA_LOCAL_DIR

    os.makedirs(DECA_LOCAL_DIR, exist_ok=True)
    client = _s3_client()

    with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as tmp:
        tar_path = tmp.name

    print(f"[deca_weights] Downloading s3://{DECA_WEIGHTS_BUCKET}/{DECA_WEIGHTS_KEY} ...")
    client.download_file(DECA_WEIGHTS_BUCKET, DECA_WEIGHTS_KEY, tar_path)

    print(f"[deca_weights] Extracting to {DECA_LOCAL_DIR} ...")
    with tarfile.open(tar_path) as tar:
        tar.extractall(DECA_LOCAL_DIR)

    os.unlink(tar_path)
    open(flag, "w").close()
    print("[deca_weights] Done.")
    return DECA_LOCAL_DIR


if __name__ == "__main__":
    download_if_needed()
