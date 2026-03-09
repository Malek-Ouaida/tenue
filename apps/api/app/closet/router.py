from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.audit import audit_log
from app.auth.dependencies import require_user_id
from app.closet.schemas import ClosetItemProcessOut, ClosetItemUploadOut
from app.closet.services.processing_service import ClosetProcessingError, process_item_background
from app.closet.services.upload_service import ClosetUploadError, upload_and_create_draft_item
from app.deps import get_db

router = APIRouter(prefix="/closet", tags=["closet"])


def _raise_upload_error(err: ClosetUploadError) -> None:
    http_status = {
        "empty_file": status.HTTP_400_BAD_REQUEST,
        "invalid_image": status.HTTP_400_BAD_REQUEST,
        "unsupported_image_type": status.HTTP_400_BAD_REQUEST,
        "content_type_mismatch": status.HTTP_400_BAD_REQUEST,
        "file_too_large": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        "upload_failed": status.HTTP_502_BAD_GATEWAY,
        "draft_create_failed": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }.get(err.code, status.HTTP_400_BAD_REQUEST)
    raise HTTPException(status_code=http_status, detail={"error": err.code})


def _parse_item_id(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "invalid_item_id"}) from e


def _raise_processing_error(err: ClosetProcessingError) -> None:
    http_status = {
        "invalid_item_id": status.HTTP_400_BAD_REQUEST,
        "item_not_found": status.HTTP_404_NOT_FOUND,
        "processing_in_progress": status.HTTP_409_CONFLICT,
        "invalid_item_state": status.HTTP_409_CONFLICT,
        "original_image_missing": status.HTTP_400_BAD_REQUEST,
        "original_image_not_found": status.HTTP_404_NOT_FOUND,
        "background_provider_not_configured": status.HTTP_502_BAD_GATEWAY,
        "background_provider_not_supported": status.HTTP_502_BAD_GATEWAY,
        "background_provider_timeout": status.HTTP_502_BAD_GATEWAY,
        "background_provider_unreachable": status.HTTP_502_BAD_GATEWAY,
        "background_provider_failed": status.HTTP_502_BAD_GATEWAY,
        "background_provider_empty_response": status.HTTP_502_BAD_GATEWAY,
        "background_provider_invalid_image": status.HTTP_502_BAD_GATEWAY,
        "processed_upload_failed": status.HTTP_502_BAD_GATEWAY,
        "processing_failed": status.HTTP_502_BAD_GATEWAY,
        "processing_start_update_failed": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "processing_success_update_failed": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "processing_failure_update_failed": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }.get(err.code, status.HTTP_400_BAD_REQUEST)
    raise HTTPException(status_code=http_status, detail={"error": err.code})


@router.post("/items/upload", response_model=ClosetItemUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_closet_item_route(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> ClosetItemUploadOut:
    try:
        result = await upload_and_create_draft_item(
            db,
            user_id=viewer_user_id,
            file=file,
        )
    except ClosetUploadError as err:
        _raise_upload_error(err)

    audit_log(
        action="closet.item.upload",
        actor_user_id=str(viewer_user_id),
        target_id=str(result.item_id),
        details={
            "content_type": result.content_type,
            "size_bytes": result.size_bytes,
            "width": result.width,
            "height": result.height,
        },
    )

    return ClosetItemUploadOut(
        id=str(result.item_id),
        item_status="draft",
        original_image_key=result.original_image_key,
        original_image_url=result.original_image_url,
        content_type=result.content_type,
        size_bytes=result.size_bytes,
        width=result.width,
        height=result.height,
        created_at=result.created_at,
    )


@router.post("/items/{item_id}/process", response_model=ClosetItemProcessOut)
async def process_closet_item_route(
    item_id: str,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> ClosetItemProcessOut:
    try:
        parsed_item_id = _parse_item_id(item_id)
        result = await process_item_background(
            db,
            item_id=parsed_item_id,
            user_id=viewer_user_id,
        )
    except ClosetProcessingError as err:
        _raise_processing_error(err)

    audit_log(
        action="closet.item.process",
        actor_user_id=str(viewer_user_id),
        target_id=str(result.item_id),
        details={
            "processed_image_key": result.processed_image_key,
            "thumbnail_key": result.thumbnail_key,
            "provider_name": result.provider_name,
            "provider_version": result.provider_version,
        },
    )

    return ClosetItemProcessOut(
        id=str(result.item_id),
        item_status="processed",
        processed_image_key=result.processed_image_key,
        processed_image_url=result.processed_image_url,
        thumbnail_key=result.thumbnail_key,
        thumbnail_url=result.thumbnail_url,
        processing_attempt_count=result.processing_attempt_count,
        provider_name=result.provider_name,
        provider_version=result.provider_version,
    )
