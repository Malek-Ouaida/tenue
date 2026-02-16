from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.pagination import (
    CursorError,
    CreatedAtIdCursor,
    decode_created_at_id_cursor,
    encode_created_at_id_cursor,
)


# ---- Follows cursor: (created_at, id) ----
FollowsCursor = CreatedAtIdCursor


def encode_follows_cursor(created_at: datetime, row_id: UUID) -> str:
    return encode_created_at_id_cursor(created_at, row_id)


def decode_follows_cursor(cursor: str) -> FollowsCursor:
    return decode_created_at_id_cursor(cursor)


# ---- User search cursor: (username, user_id) ----
@dataclass(frozen=True)
class UserSearchCursor:
    username: str
    user_id: UUID


def encode_user_search_cursor(username: str, user_id: UUID) -> str:
    payload = {"username": username, "user_id": str(user_id)}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_user_search_cursor(cursor: str) -> UserSearchCursor:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
        obj = json.loads(raw)
        return UserSearchCursor(username=str(obj["username"]), user_id=UUID(obj["user_id"]))
    except Exception as e:
        raise CursorError("invalid_cursor") from e
