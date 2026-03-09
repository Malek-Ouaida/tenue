from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.closet.repositories.item_repository import ClosetItemRepository, ClosetRepositoryError
from app.config import get_settings
from app.media_validation import MediaValidationError, detect_image_metadata
from app.s3_client import s3_client

settings = get_settings()


@dataclass(frozen=True, slots=True)
class ClosetUploadError(Exception):
    code: str


@dataclass(frozen=True, slots=True)
class ClosetUploadResult:
    item_id: uuid.UUID
    item_status: str
    original_image_key: str
    original_image_url: str
    content_type: str
    size_bytes: int
    width: int
    height: int
    created_at: datetime


def _build_original_image_key(*, user_id: uuid.UUID, item_id: uuid.UUID, extension: str) -> str:
    return f"closet/{user_id}/{item_id}/original.{extension}"


def _build_public_url(*, key: str) -> str:
    base = settings.s3_public_base_url.rstrip("/")
    return f"{base}/{key}"


def _delete_object_best_effort(*, key: str) -> None:
    try:
        s3_client().delete_object(Bucket=settings.s3_bucket, Key=key)
    except Exception:
        # Best-effort cleanup; upload path should still return deterministic failure.
        pass


async def upload_and_create_draft_item(
    db: Session,
    *,
    user_id: uuid.UUID,
    file: UploadFile,
) -> ClosetUploadResult:
    body = await file.read()
    if not body:
        raise ClosetUploadError(code="empty_file")
    if len(body) > settings.upload_max_bytes:
        raise ClosetUploadError(code="file_too_large")

    try:
        metadata = detect_image_metadata(body)
    except MediaValidationError as e:
        raise ClosetUploadError(code=e.code) from e

    if file.content_type and file.content_type != metadata.content_type:
        raise ClosetUploadError(code="content_type_mismatch")

    item_id = uuid.uuid4()
    key = _build_original_image_key(
        user_id=user_id,
        item_id=item_id,
        extension=metadata.extension,
    )

    try:
        s3_client().put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=body,
            ContentType=metadata.content_type,
            Metadata={
                "width": str(metadata.width),
                "height": str(metadata.height),
                "size_bytes": str(len(body)),
                "item_id": str(item_id),
                "user_id": str(user_id),
            },
        )
    except Exception as e:
        raise ClosetUploadError(code="upload_failed") from e

    meta_payload: dict[str, Any] = {
        "content_type": metadata.content_type,
        "extension": metadata.extension,
        "width": metadata.width,
        "height": metadata.height,
        "size_bytes": len(body),
        "filename": file.filename,
    }

    try:
        item = ClosetItemRepository.create_draft(
            db,
            item_id=item_id,
            user_id=user_id,
            original_image_key=key,
            original_image_meta=meta_payload,
        )
    except ClosetRepositoryError as e:
        _delete_object_best_effort(key=key)
        raise ClosetUploadError(code=e.code) from e

    return ClosetUploadResult(
        item_id=item.id,
        item_status=item.item_status.value,
        original_image_key=item.original_image_key,
        original_image_url=_build_public_url(key=item.original_image_key),
        content_type=metadata.content_type,
        size_bytes=len(body),
        width=metadata.width,
        height=metadata.height,
        created_at=item.created_at,
    )
