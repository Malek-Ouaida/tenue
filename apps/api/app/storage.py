from __future__ import annotations

from typing import Any

import boto3
from botocore.client import Config

from app.config import get_settings

settings = get_settings()

# For MinIO, use path-style addressing.
_s3 = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
    region_name=settings.s3_region,
    config=Config(s3={"addressing_style": "path"}),
)

BUCKET = settings.s3_bucket


def ensure_bucket() -> None:
    # MinIO supports HeadBucket; create if missing.
    try:
        _s3.head_bucket(Bucket=BUCKET)
    except Exception:
        _s3.create_bucket(Bucket=BUCKET)


def s3() -> Any:
    return _s3
