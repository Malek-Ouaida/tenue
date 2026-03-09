from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


def _load_root_env() -> None:
    # tenue/apps/api/app/config.py -> parents[3] == tenue/
    root = Path(__file__).resolve().parents[3]
    env_path = root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)


_load_root_env()


class Settings(BaseModel):
    app_env: str = "local"

    database_url: str
    redis_url: str

    # MinIO/S3 (local)
    s3_endpoint_url: str
    s3_bucket: str
    s3_access_key: str
    s3_secret_key: str
    s3_region: str = "us-east-1"
    s3_public_base_url: str

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # --- Auth / Security ---
    jwt_secret: str
    security_pepper: str

    jwt_issuer: str = "tenue"
    jwt_access_ttl_minutes: int = 15
    refresh_ttl_days: int = 30

    # Rate limits
    rate_limit_login_ip_per_min: int = 10
    rate_limit_login_email_per_15m: int = 5
    rate_limit_register_ip_per_hr: int = 5
    rate_limit_refresh_session_per_min: int = 30
    rate_limit_post_create_user_per_min: int = 10
    rate_limit_comment_create_user_per_min: int = 30
    rate_limit_follow_toggle_user_per_min: int = 30
    rate_limit_reaction_toggle_user_per_min: int = 120

    upload_max_bytes: int = 10 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "local"),

        database_url=os.environ["DATABASE_URL"],
        redis_url=os.environ["REDIS_URL"],

        s3_endpoint_url=os.environ["S3_ENDPOINT_URL"],
        s3_bucket=os.environ.get("S3_BUCKET", "tenue"),
        s3_access_key=os.environ["S3_ACCESS_KEY"],
        s3_secret_key=os.environ["S3_SECRET_KEY"],
        s3_region=os.getenv("S3_REGION", "us-east-1"),
        s3_public_base_url=os.environ.get("S3_PUBLIC_BASE_URL", "http://127.0.0.1:9000/tenue"),

        api_host=os.getenv("API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("API_PORT", 8000)),

        # --- Auth / Security ---
        jwt_secret=os.environ["JWT_SECRET"],
        security_pepper=os.environ["SECURITY_PEPPER"],
        jwt_issuer=os.getenv("JWT_ISSUER", "tenue"),
        jwt_access_ttl_minutes=int(os.getenv("JWT_ACCESS_TTL_MINUTES", "15")),
        refresh_ttl_days=int(os.getenv("REFRESH_TTL_DAYS", "30")),

        # Rate limits (optional env overrides)
        rate_limit_login_ip_per_min=int(os.getenv("RATE_LIMIT_LOGIN_IP_PER_MIN", "10")),
        rate_limit_login_email_per_15m=int(os.getenv("RATE_LIMIT_LOGIN_EMAIL_PER_15M", "5")),
        rate_limit_register_ip_per_hr=int(os.getenv("RATE_LIMIT_REGISTER_IP_PER_HR", "5")),
        rate_limit_refresh_session_per_min=int(os.getenv("RATE_LIMIT_REFRESH_SESSION_PER_MIN", "30")),
        rate_limit_post_create_user_per_min=int(os.getenv("RATE_LIMIT_POST_CREATE_USER_PER_MIN", "10")),
        rate_limit_comment_create_user_per_min=int(os.getenv("RATE_LIMIT_COMMENT_CREATE_USER_PER_MIN", "30")),
        rate_limit_follow_toggle_user_per_min=int(os.getenv("RATE_LIMIT_FOLLOW_TOGGLE_USER_PER_MIN", "30")),
        rate_limit_reaction_toggle_user_per_min=int(os.getenv("RATE_LIMIT_REACTION_TOGGLE_USER_PER_MIN", "120")),
        upload_max_bytes=int(os.getenv("UPLOAD_MAX_BYTES", str(10 * 1024 * 1024))),
    )
