from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.closet.providers.background_removal import (
    BackgroundRemovalError,
    BackgroundRemovalProvider,
    build_background_removal_provider,
)
from app.closet.providers.garment_analysis import (
    GarmentAnalysisError,
    GarmentAnalysisProvider,
    build_garment_analysis_provider,
)
from app.closet.repositories.item_repository import ClosetItemRepository, ClosetRepositoryError
from app.closet.repositories.processing_run_repository import (
    ClosetProcessingRunRepository,
    ClosetProcessingRunRepositoryError,
)
from app.closet.services.garment_analysis_service import (
    GarmentAnalysisServiceError,
    analyze_garment,
)
from app.closet.services.image_processing_service import ImageProcessingError, process_image
from app.closet.services.normalization_service import (
    ClosetNormalizationServiceError,
    normalize_garment_analysis,
    persist_processed_metadata,
)
from app.config import get_settings
from app.models.closet_item import ClosetItemStatus, ClosetProcessingRun
from app.s3_client import s3_client

settings = get_settings()


@dataclass(frozen=True, slots=True)
class ClosetProcessingError(Exception):
    code: str


@dataclass(frozen=True, slots=True)
class ClosetProcessingResult:
    item_id: uuid.UUID
    item_status: str
    processed_image_key: str
    processed_image_url: str
    thumbnail_key: str
    thumbnail_url: str
    processing_attempt_count: int
    provider_name: str
    provider_version: str


def _public_url_for_key(*, key: str) -> str:
    return f"{settings.s3_public_base_url.rstrip('/')}/{key}"


def _build_processed_key(*, user_id: uuid.UUID, item_id: uuid.UUID, extension: str) -> str:
    return f"closet/{user_id}/{item_id}/processed.{extension}"


def _build_thumbnail_key(*, user_id: uuid.UUID, item_id: uuid.UUID, extension: str) -> str:
    return f"closet/{user_id}/{item_id}/thumbnail.{extension}"


def _delete_object_best_effort(*, key: str) -> None:
    try:
        s3_client().delete_object(Bucket=settings.s3_bucket, Key=key)
    except Exception:
        pass


def _read_s3_object(*, key: str) -> bytes:
    try:
        response = s3_client().get_object(Bucket=settings.s3_bucket, Key=key)
        body = response["Body"].read()
    except Exception as e:
        raise ClosetProcessingError(code="original_image_not_found") from e
    if not body:
        raise ClosetProcessingError(code="original_image_empty")
    return body


def _put_s3_object(*, key: str, body: bytes, content_type: str, meta: dict[str, object]) -> None:
    metadata = {k: str(v) for k, v in meta.items()}
    try:
        s3_client().put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
            Metadata=metadata,
        )
    except Exception as e:
        raise ClosetProcessingError(code="processed_upload_failed") from e


def _validate_state(status: ClosetItemStatus) -> None:
    if status == ClosetItemStatus.PROCESSING:
        raise ClosetProcessingError(code="processing_in_progress")
    if status in {ClosetItemStatus.CONFIRMED, ClosetItemStatus.PROCESSED}:
        raise ClosetProcessingError(code="invalid_item_state")
    if status not in {ClosetItemStatus.DRAFT, ClosetItemStatus.FAILED}:
        raise ClosetProcessingError(code="invalid_item_state")


def _build_providers() -> tuple[BackgroundRemovalProvider, GarmentAnalysisProvider]:
    try:
        background_provider = build_background_removal_provider(settings)
    except BackgroundRemovalError as e:
        raise ClosetProcessingError(code=e.code) from e

    try:
        garment_provider = build_garment_analysis_provider(settings)
    except GarmentAnalysisError as e:
        raise ClosetProcessingError(code=e.code) from e

    return background_provider, garment_provider


async def process_item_background(
    db: Session,
    *,
    item_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ClosetProcessingResult:
    item = ClosetItemRepository.get_for_user(
        db,
        item_id=item_id,
        user_id=user_id,
    )
    if item is None or item.deleted_at is not None:
        raise ClosetProcessingError(code="item_not_found")
    _validate_state(item.item_status)
    if not item.original_image_key:
        raise ClosetProcessingError(code="original_image_missing")

    background_provider, garment_provider = _build_providers()
    run: ClosetProcessingRun | None = None
    run_started_perf: float | None = None

    try:
        item = ClosetItemRepository.mark_processing_started(db, item=item)
    except ClosetRepositoryError as e:
        raise ClosetProcessingError(code=e.code) from e

    processed_key: str | None = None
    thumbnail_key: str | None = None
    error_code = "processing_failed"
    error_message: str | None = None
    run_raw_response: dict[str, object] | None = None

    try:
        run_started_perf = time.perf_counter()
        try:
            run = ClosetProcessingRunRepository.create_started_run(
                db,
                run_id=uuid.uuid4(),
                item_id=item.id,
                stage="image_processing",
                provider=background_provider.name,
                provider_version=background_provider.version,
            )
        except ClosetProcessingRunRepositoryError as e:
            raise ClosetProcessingError(code=e.code) from e

        original_bytes = _read_s3_object(key=item.original_image_key)
        original_content_type = (
            str(item.original_image_meta_json.get("content_type", "application/octet-stream"))
            if item.original_image_meta_json
            else "application/octet-stream"
        )

        image_result = await process_image(
            image_bytes=original_bytes,
            content_type=original_content_type,
            provider=background_provider,
        )
        run_raw_response = image_result.provider_raw_response

        processed_key = _build_processed_key(
            user_id=user_id,
            item_id=item.id,
            extension=image_result.processed_image.extension,
        )
        thumbnail_key = _build_thumbnail_key(
            user_id=user_id,
            item_id=item.id,
            extension=image_result.thumbnail_image.extension,
        )

        _put_s3_object(
            key=processed_key,
            body=image_result.processed_image.image_bytes,
            content_type=image_result.processed_image.content_type,
            meta=image_result.processed_image.meta_json,
        )
        _put_s3_object(
            key=thumbnail_key,
            body=image_result.thumbnail_image.image_bytes,
            content_type=image_result.thumbnail_image.content_type,
            meta=image_result.thumbnail_image.meta_json,
        )

        if run and run_started_perf is not None:
            latency_ms = max(0, int((time.perf_counter() - run_started_perf) * 1000))
            try:
                ClosetProcessingRunRepository.mark_succeeded(
                    db,
                    run=run,
                    latency_ms=latency_ms,
                    raw_response=run_raw_response,
                )
            except ClosetProcessingRunRepositoryError as e:
                raise ClosetProcessingError(code=e.code) from e
            run = None
            run_started_perf = None
            run_raw_response = None

        processed_image_url = _public_url_for_key(key=processed_key)

        run_started_perf = time.perf_counter()
        try:
            run = ClosetProcessingRunRepository.create_started_run(
                db,
                run_id=uuid.uuid4(),
                item_id=item.id,
                stage="garment_analysis",
                provider=garment_provider.name,
                provider_version=garment_provider.version,
            )
        except ClosetProcessingRunRepositoryError as e:
            raise ClosetProcessingError(code=e.code) from e

        garment_result = await analyze_garment(
            image_url=processed_image_url,
            provider=garment_provider,
        )
        run_raw_response = garment_result.raw_response

        if run and run_started_perf is not None:
            latency_ms = max(0, int((time.perf_counter() - run_started_perf) * 1000))
            try:
                ClosetProcessingRunRepository.mark_succeeded(
                    db,
                    run=run,
                    latency_ms=latency_ms,
                    raw_response=run_raw_response,
                )
            except ClosetProcessingRunRepositoryError as e:
                raise ClosetProcessingError(code=e.code) from e
            run = None
            run_started_perf = None
            run_raw_response = None

        run_started_perf = time.perf_counter()
        try:
            run = ClosetProcessingRunRepository.create_started_run(
                db,
                run_id=uuid.uuid4(),
                item_id=item.id,
                stage="metadata_normalization",
                provider="normalization_engine",
                provider_version="v1",
            )
        except ClosetProcessingRunRepositoryError as e:
            raise ClosetProcessingError(code=e.code) from e

        normalized_metadata = normalize_garment_analysis(
            db,
            extraction=garment_result.extraction,
        )

        ai_raw_response_payload: dict[str, Any] = {
            "extraction": garment_result.extraction.model_dump(mode="json"),
            "provider_raw_response": garment_result.raw_response,
            "normalized": normalized_metadata.to_debug_payload(),
        }
        run_raw_response = {"normalized": normalized_metadata.to_debug_payload()}

        try:
            item = persist_processed_metadata(
                db,
                item=item,
                processed_image_key=processed_key,
                processed_image_meta=image_result.processed_image.meta_json,
                thumbnail_key=thumbnail_key,
                thumbnail_meta=image_result.thumbnail_image.meta_json,
                ai_provider=garment_result.provider_name,
                ai_provider_version=garment_result.provider_version,
                ai_raw_response=ai_raw_response_payload,
                normalized_metadata=normalized_metadata,
            )
        except ClosetNormalizationServiceError as e:
            _delete_object_best_effort(key=processed_key)
            _delete_object_best_effort(key=thumbnail_key)
            raise ClosetProcessingError(code=e.code) from e

        if run and run_started_perf is not None:
            latency_ms = max(0, int((time.perf_counter() - run_started_perf) * 1000))
            try:
                ClosetProcessingRunRepository.mark_succeeded(
                    db,
                    run=run,
                    latency_ms=latency_ms,
                    raw_response=run_raw_response,
                )
            except ClosetProcessingRunRepositoryError as e:
                raise ClosetProcessingError(code=e.code) from e

        return ClosetProcessingResult(
            item_id=item.id,
            item_status=item.item_status.value,
            processed_image_key=processed_key,
            processed_image_url=processed_image_url,
            thumbnail_key=thumbnail_key,
            thumbnail_url=_public_url_for_key(key=thumbnail_key),
            processing_attempt_count=item.processing_attempt_count,
            provider_name=garment_result.provider_name,
            provider_version=garment_result.provider_version,
        )
    except ImageProcessingError as e:
        error_code = e.code
        error_message = None
        run_raw_response = e.raw_response
    except GarmentAnalysisServiceError as e:
        error_code = e.code
        error_message = None
        run_raw_response = e.raw_response
    except ClosetNormalizationServiceError as e:
        error_code = e.code
        error_message = None
    except ClosetProcessingError as e:
        error_code = e.code
        error_message = None
    except Exception:
        error_code = "processing_failed"
        error_message = "Unexpected processing error"

    if processed_key:
        _delete_object_best_effort(key=processed_key)
    if thumbnail_key:
        _delete_object_best_effort(key=thumbnail_key)

    if run and run_started_perf is not None:
        latency_ms = max(0, int((time.perf_counter() - run_started_perf) * 1000))
        try:
            ClosetProcessingRunRepository.mark_failed(
                db,
                run=run,
                error_code=error_code,
                error_message=error_message,
                latency_ms=latency_ms,
                raw_response=run_raw_response,
            )
        except ClosetProcessingRunRepositoryError as e:
            raise ClosetProcessingError(code=e.code) from e

    try:
        ClosetItemRepository.mark_processing_failed(
            db,
            item=item,
            error_code=error_code,
            error_message=error_message,
        )
    except ClosetRepositoryError as e:
        raise ClosetProcessingError(code=e.code) from e

    raise ClosetProcessingError(code=error_code)
