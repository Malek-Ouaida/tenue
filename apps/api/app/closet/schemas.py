from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ClosetItemUploadOut(BaseModel):
    id: str
    item_status: Literal["draft"]
    original_image_key: str
    original_image_url: str
    content_type: str
    size_bytes: int
    width: int
    height: int
    created_at: datetime

    model_config = ConfigDict(extra="forbid")


class ClosetItemProcessOut(BaseModel):
    id: str
    item_status: Literal["processed"]
    processed_image_key: str
    processed_image_url: str
    thumbnail_key: str
    thumbnail_url: str
    processing_attempt_count: int
    provider_name: str
    provider_version: str

    model_config = ConfigDict(extra="forbid")
