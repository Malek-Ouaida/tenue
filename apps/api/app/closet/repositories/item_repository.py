from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.closet_item import ClosetItem, ClosetItemStatus


@dataclass(frozen=True, slots=True)
class ClosetRepositoryError(Exception):
    code: str


class ClosetItemRepository:
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
