from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.closet.normalization.types import NormalizedClosetMetadata
from app.models.closet_item import (
    ClosetItem,
    ClosetItemOccasion,
    ClosetItemSeason,
    ClosetItemSecondaryColor,
    ClosetItemStatus,
    ClosetItemStyleTag,
)


@dataclass(frozen=True, slots=True)
class ClosetRepositoryError(Exception):
    code: str


class ClosetItemRepository:
    @staticmethod
    def _replace_secondary_colors(
        db: Session,
        *,
        item_id: uuid.UUID,
        color_ids: tuple[uuid.UUID, ...],
    ) -> None:
        db.execute(delete(ClosetItemSecondaryColor).where(ClosetItemSecondaryColor.item_id == item_id))
        for color_id in color_ids:
            db.add(ClosetItemSecondaryColor(item_id=item_id, color_id=color_id))

    @staticmethod
    def _replace_seasons(
        db: Session,
        *,
        item_id: uuid.UUID,
        season_ids: tuple[uuid.UUID, ...],
    ) -> None:
        db.execute(delete(ClosetItemSeason).where(ClosetItemSeason.item_id == item_id))
        for season_id in season_ids:
            db.add(ClosetItemSeason(item_id=item_id, season_id=season_id))

    @staticmethod
    def _replace_occasions(
        db: Session,
        *,
        item_id: uuid.UUID,
        occasion_ids: tuple[uuid.UUID, ...],
    ) -> None:
        db.execute(delete(ClosetItemOccasion).where(ClosetItemOccasion.item_id == item_id))
        for occasion_id in occasion_ids:
            db.add(ClosetItemOccasion(item_id=item_id, occasion_id=occasion_id))

    @staticmethod
    def _replace_style_tags(
        db: Session,
        *,
        item_id: uuid.UUID,
        style_tag_ids: tuple[uuid.UUID, ...],
    ) -> None:
        db.execute(delete(ClosetItemStyleTag).where(ClosetItemStyleTag.item_id == item_id))
        for style_tag_id in style_tag_ids:
            db.add(ClosetItemStyleTag(item_id=item_id, style_tag_id=style_tag_id))

    @staticmethod
    def get_for_user(
        db: Session,
        *,
        item_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ClosetItem | None:
        return db.execute(
            select(ClosetItem).where(
                ClosetItem.id == item_id,
                ClosetItem.user_id == user_id,
            )
        ).scalar_one_or_none()

    @staticmethod
    def create_draft(
        db: Session,
        *,
        item_id: uuid.UUID,
        user_id: uuid.UUID,
        original_image_key: str,
        original_image_meta: dict[str, Any],
    ) -> ClosetItem:
        item = ClosetItem(
            id=item_id,
            user_id=user_id,
            item_status=ClosetItemStatus.DRAFT,
            original_image_key=original_image_key,
            original_image_meta_json=original_image_meta,
        )
        db.add(item)

        try:
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise ClosetRepositoryError(code="draft_create_failed") from e

        db.refresh(item)
        return item

    @staticmethod
    def mark_processing_started(
        db: Session,
        *,
        item: ClosetItem,
    ) -> ClosetItem:
        item.item_status = ClosetItemStatus.PROCESSING
        item.processing_attempt_count += 1
        item.last_error_code = None
        item.last_error_message = None
        db.add(item)
        try:
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise ClosetRepositoryError(code="processing_start_update_failed") from e
        db.refresh(item)
        return item

    @staticmethod
    def mark_processing_succeeded(
        db: Session,
        *,
        item: ClosetItem,
        processed_image_key: str,
        processed_image_meta: dict[str, Any],
        thumbnail_key: str,
        thumbnail_meta: dict[str, Any],
        ai_provider: str | None = None,
        ai_provider_version: str | None = None,
        ai_raw_response: dict[str, Any] | None = None,
        normalized_metadata: NormalizedClosetMetadata | None = None,
        commit: bool = True,
    ) -> ClosetItem:
        try:
            item.item_status = ClosetItemStatus.PROCESSED
            item.processed_image_key = processed_image_key
            item.processed_image_meta_json = processed_image_meta
            item.thumbnail_key = thumbnail_key
            item.thumbnail_meta_json = thumbnail_meta
            item.ai_provider = ai_provider
            item.ai_provider_version = ai_provider_version
            item.ai_raw_response_json = ai_raw_response
            item.last_error_code = None
            item.last_error_message = None

            if normalized_metadata is not None:
                item.category_id = normalized_metadata.category_id
                item.subcategory_id = normalized_metadata.subcategory_id
                item.type_label = normalized_metadata.type_label
                item.primary_color_id = normalized_metadata.primary_color_id
                item.material_id = normalized_metadata.material_id
                item.pattern_id = normalized_metadata.pattern_id
                item.brand = normalized_metadata.brand
                item.sleeve_length = normalized_metadata.sleeve_length
                item.fit = normalized_metadata.fit
                item.formality_level_id = normalized_metadata.formality_level_id
                item.notes = normalized_metadata.notes

                ClosetItemRepository._replace_secondary_colors(
                    db,
                    item_id=item.id,
                    color_ids=normalized_metadata.secondary_color_ids,
                )
                ClosetItemRepository._replace_seasons(
                    db,
                    item_id=item.id,
                    season_ids=normalized_metadata.season_ids,
                )
                ClosetItemRepository._replace_occasions(
                    db,
                    item_id=item.id,
                    occasion_ids=normalized_metadata.occasion_ids,
                )
                ClosetItemRepository._replace_style_tags(
                    db,
                    item_id=item.id,
                    style_tag_ids=normalized_metadata.style_tag_ids,
                )

            db.add(item)

            if commit:
                db.commit()
            else:
                db.flush()
        except SQLAlchemyError as e:
            if commit:
                db.rollback()
            raise ClosetRepositoryError(code="processing_success_update_failed") from e
        if commit:
            db.refresh(item)
        return item

    @staticmethod
    def mark_processing_failed(
        db: Session,
        *,
        item: ClosetItem,
        error_code: str,
        error_message: str | None,
    ) -> ClosetItem:
        item.item_status = ClosetItemStatus.FAILED
        item.last_error_code = error_code
        item.last_error_message = error_message
        db.add(item)
        try:
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise ClosetRepositoryError(code="processing_failure_update_failed") from e
        db.refresh(item)
        return item
