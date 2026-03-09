from __future__ import annotations

import re
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.audit import audit_log
from app.auth.dependencies import require_user_id

router = APIRouter(tags=["events"])

EVENT_RE = re.compile(r"^[a-z0-9._:-]{1,80}$")


class ClientEventIn(BaseModel):
    event: str = Field(min_length=1, max_length=80)
    path: str | None = Field(default=None, max_length=512)
    details: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("event")
    @classmethod
    def validate_event(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EVENT_RE.match(normalized):
            raise ValueError("invalid_event_name")
        return normalized


class EventAckOut(BaseModel):
    ok: bool = True

    model_config = ConfigDict(extra="forbid")


@router.post("/events/client", response_model=EventAckOut)
def client_event(
    payload: ClientEventIn,
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> EventAckOut:
    # Keep details bounded and JSON-like in logs.
    details: dict[str, Any] = {}
    if payload.path:
        details["path"] = payload.path
    if payload.details is not None:
        if not isinstance(payload.details, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_event_payload"},
            )
        details["meta"] = payload.details

    audit_log(
        action=f"client.{payload.event}",
        actor_user_id=str(viewer_user_id),
        details=details or None,
    )
    return EventAckOut(ok=True)


@router.post("/events/client/public", response_model=EventAckOut)
def public_client_event(payload: ClientEventIn) -> EventAckOut:
    details: dict[str, Any] = {}
    if payload.path:
        details["path"] = payload.path
    if payload.details is not None and isinstance(payload.details, dict):
        details["meta"] = payload.details

    audit_log(
        action=f"client.public.{payload.event}",
        details=details or None,
    )
    return EventAckOut(ok=True)
