from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.closet.normalization.types import NormalizedFieldStatePayload
from app.models.closet_item import ClosetItemFieldState


@dataclass(frozen=True, slots=True)
class ClosetFieldStateRepositoryError(Exception):
    code: str


class ClosetItemFieldStateRepository:
    @staticmethod
    def replace_for_item(
        db: Session,
        *,
        item_id: uuid.UUID,
        field_states: tuple[NormalizedFieldStatePayload, ...],
        commit: bool = True,
    ) -> None:
        try:
            db.execute(delete(ClosetItemFieldState).where(ClosetItemFieldState.item_id == item_id))
            for field_state in field_states:
                db.add(
                    ClosetItemFieldState(
                        item_id=item_id,
                        field_name=field_state.field_name,
                        value_json=field_state.value_json,
                        source=field_state.source,
                        confidence=field_state.confidence,
                        is_user_confirmed=field_state.is_user_confirmed,
                        needs_review=field_state.needs_review,
                        candidates_json=field_state.candidates_json,
                    )
                )

            if commit:
                db.commit()
            else:
                db.flush()
        except SQLAlchemyError as e:
            if commit:
                db.rollback()
            raise ClosetFieldStateRepositoryError(code="field_state_replace_failed") from e
