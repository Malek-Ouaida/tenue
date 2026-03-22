from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.closet.normalization import (
    ClosetTaxonomyCatalogError,
    NormalizedClosetMetadata,
    load_taxonomy_catalog,
    normalize_garment_metadata,
)
from app.closet.repositories.field_state_repository import (
    ClosetFieldStateRepositoryError,
    ClosetItemFieldStateRepository,
)
from app.closet.repositories.item_repository import ClosetItemRepository, ClosetRepositoryError
from app.closet.schemas import GarmentAnalysisExtraction
from app.models.closet_item import ClosetItem


@dataclass(frozen=True, slots=True)
class ClosetNormalizationServiceError(Exception):
    code: str


def normalize_garment_analysis(
    db: Session,
    *,
    extraction: GarmentAnalysisExtraction,
) -> NormalizedClosetMetadata:
    try:
        catalog = load_taxonomy_catalog(db)
    except ClosetTaxonomyCatalogError as e:
        raise ClosetNormalizationServiceError(code=e.code) from e

    try:
        return normalize_garment_metadata(
            extraction=extraction,
            catalog=catalog,
        )
    except (KeyError, ValueError) as e:
        raise ClosetNormalizationServiceError(code="metadata_normalization_failed") from e


def persist_processed_metadata(
    db: Session,
    *,
    item: ClosetItem,
    processed_image_key: str,
    processed_image_meta: dict[str, Any],
    thumbnail_key: str,
    thumbnail_meta: dict[str, Any],
    ai_provider: str | None,
    ai_provider_version: str | None,
    ai_raw_response: dict[str, Any] | None,
    normalized_metadata: NormalizedClosetMetadata,
) -> ClosetItem:
    try:
        updated_item = ClosetItemRepository.mark_processing_succeeded(
            db,
            item=item,
            processed_image_key=processed_image_key,
            processed_image_meta=processed_image_meta,
            thumbnail_key=thumbnail_key,
            thumbnail_meta=thumbnail_meta,
            ai_provider=ai_provider,
            ai_provider_version=ai_provider_version,
            ai_raw_response=ai_raw_response,
            normalized_metadata=normalized_metadata,
            commit=False,
        )
        ClosetItemFieldStateRepository.replace_for_item(
            db,
            item_id=item.id,
            field_states=normalized_metadata.field_states,
            commit=False,
        )
        db.commit()
    except ClosetRepositoryError as e:
        db.rollback()
        raise ClosetNormalizationServiceError(code=e.code) from e
    except ClosetFieldStateRepositoryError as e:
        db.rollback()
        raise ClosetNormalizationServiceError(code=e.code) from e
    except SQLAlchemyError as e:
        db.rollback()
        raise ClosetNormalizationServiceError(code="processing_success_update_failed") from e

    db.refresh(updated_item)
    return updated_item
