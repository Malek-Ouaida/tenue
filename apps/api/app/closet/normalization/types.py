from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.models.closet_item import ClosetFieldSource, ClosetFit, ClosetSleeveLength


@dataclass(frozen=True, slots=True)
class TaxonomyValue:
    id: uuid.UUID
    slug: str
    label: str


@dataclass(frozen=True, slots=True)
class TaxonomySubcategoryValue(TaxonomyValue):
    category_id: uuid.UUID
    category_slug: str


@dataclass(frozen=True, slots=True)
class NormalizedFieldStatePayload:
    field_name: str
    value_json: object | None
    source: ClosetFieldSource
    confidence: float | None
    is_user_confirmed: bool
    needs_review: bool
    candidates_json: object | None

    def to_debug_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "value": self.value_json,
            "source": self.source.value,
            "is_user_confirmed": self.is_user_confirmed,
            "needs_review": self.needs_review,
        }
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        if self.candidates_json is not None:
            payload["candidates"] = self.candidates_json
        return payload


@dataclass(frozen=True, slots=True)
class NormalizedClosetMetadata:
    category_id: uuid.UUID | None
    subcategory_id: uuid.UUID | None
    type_label: str | None
    primary_color_id: uuid.UUID | None
    secondary_color_ids: tuple[uuid.UUID, ...]
    material_id: uuid.UUID | None
    pattern_id: uuid.UUID | None
    brand: str | None
    sleeve_length: ClosetSleeveLength | None
    fit: ClosetFit | None
    formality_level_id: uuid.UUID | None
    season_ids: tuple[uuid.UUID, ...]
    occasion_ids: tuple[uuid.UUID, ...]
    style_tag_ids: tuple[uuid.UUID, ...]
    notes: str | None
    field_states: tuple[NormalizedFieldStatePayload, ...]

    def to_debug_payload(self) -> dict[str, object]:
        return {state.field_name: state.to_debug_payload() for state in self.field_states}
