from __future__ import annotations

import boto3
from botocore.client import Config

from app.config import get_settings

settings = get_settings()

# Path-style is important for MinIO URLs.
_s3 = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
    region_name=settings.s3_region,
    config=Config(s3={"addressing_style": "path"}),
)

def s3_client():
    return _s3
