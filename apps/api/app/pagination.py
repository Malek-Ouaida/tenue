from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


class CursorError(ValueError):
    pass


@dataclass(frozen=True)
class CreatedAtIdCursor:
    created_at: datetime
    id: UUID


def encode_created_at_id_cursor(created_at: datetime, row_id: UUID) -> str:
    payload = {"created_at": created_at.isoformat(), "id": str(row_id)}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_created_at_id_cursor(cursor: str) -> CreatedAtIdCursor:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
        obj = json.loads(raw)
        created_at = datetime.fromisoformat(str(obj["created_at"]))
        row_id = UUID(str(obj["id"]))
    except Exception as e:  # pragma: no cover - defensive guard for malformed cursors
        raise CursorError("invalid_cursor") from e

    return CreatedAtIdCursor(created_at=created_at, id=row_id)
