from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.closet_item import ClosetItem, ClosetItemStatus


@dataclass(frozen=True, slots=True)
class ClosetRepositoryError(Exception):
    code: str


class ClosetItemRepository:
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
    ) -> ClosetItem:
        item.item_status = ClosetItemStatus.PROCESSED
        item.processed_image_key = processed_image_key
        item.processed_image_meta_json = processed_image_meta
        item.thumbnail_key = thumbnail_key
        item.thumbnail_meta_json = thumbnail_meta
        item.last_error_code = None
        item.last_error_message = None
        db.add(item)
        try:
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise ClosetRepositoryError(code="processing_success_update_failed") from e
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
