from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.audit import audit_log
from app.auth.dependencies import require_user_id
from app.closet.schemas import ClosetItemUploadOut
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
