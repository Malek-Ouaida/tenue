from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("tenue.audit")


def audit_log(
    *,
    action: str,
    actor_user_id: str | None = None,
    target_id: str | None = None,
    outcome: str = "success",
    details: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "event": "audit",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor_user_id": actor_user_id,
        "target_id": target_id,
        "outcome": outcome,
    }
    if details:
        payload["details"] = details

    logger.info(json.dumps(payload, separators=(",", ":"), sort_keys=True))
