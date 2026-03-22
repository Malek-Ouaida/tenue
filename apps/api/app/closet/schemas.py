from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


class GarmentAnalysisCandidate(BaseModel):
    value: str
    confidence: float | None = Field(default=None, ge=0, le=1)

    model_config = ConfigDict(extra="forbid")


class GarmentAnalysisExtraction(BaseModel):
    category: str | None = None
    subcategory: str | None = None
    type_label: str | None = Field(default=None, max_length=60)
    primary_color: str | None = None
    secondary_colors: list[str] = Field(default_factory=list)
    material: str | None = None
    pattern: str | None = None
    brand: str | None = Field(default=None, max_length=80)
    sleeve_length: Literal["sleeveless", "short", "three_quarter", "long"] | None = None
    fit: Literal["slim", "regular", "relaxed", "oversized", "tailored"] | None = None
    formality_level: str | None = None
    seasons: list[str] = Field(default_factory=list)
    occasions: list[str] = Field(default_factory=list)
    style_tags: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=500)
    candidates: dict[str, list[GarmentAnalysisCandidate]] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")
