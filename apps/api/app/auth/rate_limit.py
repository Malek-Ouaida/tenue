from __future__ import annotations

from fastapi import HTTPException, status

from app.redis_client import redis_client


def _incr_with_ttl(key: str, ttl_seconds: int) -> int:
    # Redis INCR is atomic. Ensure TTL exists.
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.ttl(key)
    val, ttl = pipe.execute()
    if ttl == -1:
        redis_client.expire(key, ttl_seconds)
    return int(val)


def enforce_rate_limit(*, key: str, limit: int, ttl_seconds: int, message: str = "Too many requests") -> None:
    count = _incr_with_ttl(key, ttl_seconds)
    if count > limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)
