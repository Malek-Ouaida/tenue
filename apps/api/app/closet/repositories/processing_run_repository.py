from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.closet_item import ClosetProcessingRun, ClosetProcessingRunStatus


@dataclass(frozen=True, slots=True)
class ClosetProcessingRunRepositoryError(Exception):
    code: str


class ClosetProcessingRunRepository:
    @staticmethod
    def create_started_run(
        db: Session,
        *,
        run_id: uuid.UUID,
        item_id: uuid.UUID,
        stage: str,
        provider: str | None,
        provider_version: str | None,
        raw_response: dict[str, object] | None = None,
    ) -> ClosetProcessingRun:
        run = ClosetProcessingRun(
            id=run_id,
            item_id=item_id,
            stage=stage,
            provider=provider,
            provider_version=provider_version,
            status=ClosetProcessingRunStatus.STARTED,
            raw_response_json=raw_response,
        )
        db.add(run)
        try:
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise ClosetProcessingRunRepositoryError(code="processing_run_start_failed") from e
        db.refresh(run)
        return run

    @staticmethod
    def mark_succeeded(
        db: Session,
        *,
        run: ClosetProcessingRun,
        latency_ms: int,
        raw_response: dict[str, object] | None = None,
    ) -> ClosetProcessingRun:
        run.status = ClosetProcessingRunStatus.SUCCEEDED
        run.latency_ms = latency_ms
        if raw_response is not None:
            run.raw_response_json = raw_response
        db.add(run)
        try:
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise ClosetProcessingRunRepositoryError(code="processing_run_success_update_failed") from e
        db.refresh(run)
        return run

    @staticmethod
    def mark_failed(
        db: Session,
        *,
        run: ClosetProcessingRun,
        error_code: str,
        error_message: str | None,
        latency_ms: int,
        raw_response: dict[str, object] | None = None,
    ) -> ClosetProcessingRun:
        run.status = ClosetProcessingRunStatus.FAILED
        run.error_code = error_code
        run.error_message = error_message
        run.latency_ms = latency_ms
        if raw_response is not None:
            run.raw_response_json = raw_response
        db.add(run)
        try:
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise ClosetProcessingRunRepositoryError(code="processing_run_failure_update_failed") from e
        db.refresh(run)
        return run
