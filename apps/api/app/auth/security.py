from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import get_settings

settings = get_settings()
_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, password)
    except VerifyMismatchError:
        return False


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_jwt(*, user_id: uuid.UUID, session_id: uuid.UUID) -> str:
    now = _now_utc()
    exp = now + timedelta(minutes=settings.jwt_access_ttl_minutes)

    payload: dict[str, Any] = {
        "iss": settings.jwt_issuer,
        "sub": str(user_id),
        "sid": str(session_id),
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_jwt(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], issuer=settings.jwt_issuer)


def generate_refresh_token() -> str:
    # 48 bytes -> ~64 chars base64url
    raw = os.urandom(48)
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def hash_refresh_token(refresh_token: str) -> str:
    # HMAC with a server-side pepper so DB leaks are less damaging
    msg = refresh_token.encode("utf-8")
    key = settings.security_pepper.encode("utf-8")
    digest = hmac.new(key, msg, hashlib.sha256).hexdigest()
    return digest
