from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user_id
from app.deps import get_db
from app.posts.schemas import (
    PaginatedPostsOut,
    PostActionOut,
    PostCreateIn,
    PostEngagementOut,
    PostOut,
)
from app.posts.service import (
    CreatePostMediaItem,
    PostError,
    create_post,
    delete_post,
    get_explore_feed,
    get_following_feed,
    get_post_detail,
    get_profile_posts,
    like_post,
    save_post,
    unlike_post,
    unsave_post,
)

router = APIRouter(tags=["posts"])


def _parse_uuid(value: str, *, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"invalid_{field}"},
        ) from e


def _raise_post_error(err: PostError) -> None:
    mapping: dict[str, int] = {
        "invalid_media_key": status.HTTP_400_BAD_REQUEST,
        "media_required": status.HTTP_400_BAD_REQUEST,
        "duplicate_media_order": status.HTTP_400_BAD_REQUEST,
        "post_create_failed": status.HTTP_400_BAD_REQUEST,
        "invalid_cursor": status.HTTP_400_BAD_REQUEST,
        "limit_out_of_range": status.HTTP_400_BAD_REQUEST,
        "invalid_explore_mode": status.HTTP_400_BAD_REQUEST,
        "post_not_found": status.HTTP_404_NOT_FOUND,
        "user_not_found": status.HTTP_404_NOT_FOUND,
        "forbidden": status.HTTP_403_FORBIDDEN,
    }
    http_status = mapping.get(err.code, status.HTTP_400_BAD_REQUEST)
    raise HTTPException(status_code=http_status, detail={"error": err.code})


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post_route(
    payload: PostCreateIn,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> PostOut:
    try:
        created = create_post(
            db,
            viewer_user_id=viewer_user_id,
            caption=payload.caption,
            media_items=[
                CreatePostMediaItem(
                    key=item.key,
                    width=item.width,
                    height=item.height,
                    order=item.order,
                )
                for item in payload.media
            ],
        )
        return PostOut.model_validate(created)
    except PostError as err:
        _raise_post_error(err)


@router.get("/feed", response_model=PaginatedPostsOut)
def following_feed_route(
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
) -> PaginatedPostsOut:
    try:
        items, next_cursor = get_following_feed(
            db,
            viewer_user_id=viewer_user_id,
            cursor=cursor,
            limit=limit,
        )
        return PaginatedPostsOut.model_validate({"items": items, "next_cursor": next_cursor})
    except PostError as err:
        _raise_post_error(err)


@router.get("/explore", response_model=PaginatedPostsOut)
def explore_feed_route(
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
    mode: str = Query("recent"),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
) -> PaginatedPostsOut:
    try:
        items, next_cursor = get_explore_feed(
            db,
            viewer_user_id=viewer_user_id,
            cursor=cursor,
            limit=limit,
            mode=mode,
        )
        return PaginatedPostsOut.model_validate({"items": items, "next_cursor": next_cursor})
    except PostError as err:
        _raise_post_error(err)


@router.get("/users/{username}/posts", response_model=PaginatedPostsOut)
def profile_posts_route(
    username: str,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
) -> PaginatedPostsOut:
    try:
        items, next_cursor = get_profile_posts(
            db,
            username=username,
            viewer_user_id=viewer_user_id,
            cursor=cursor,
            limit=limit,
        )
        return PaginatedPostsOut.model_validate({"items": items, "next_cursor": next_cursor})
    except PostError as err:
        _raise_post_error(err)


@router.get("/posts/{post_id}", response_model=PostOut)
def get_post_route(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> PostOut:
    try:
        post_uuid = _parse_uuid(post_id, field="post_id")
        payload = get_post_detail(db, post_id=post_uuid, viewer_user_id=viewer_user_id)
        return PostOut.model_validate(payload)
    except PostError as err:
        _raise_post_error(err)


@router.post("/posts/{post_id}/like", response_model=PostEngagementOut)
def like_post_route(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> PostEngagementOut:
    try:
        post_uuid = _parse_uuid(post_id, field="post_id")
        payload = like_post(db, post_id=post_uuid, viewer_user_id=viewer_user_id)
        return PostEngagementOut.model_validate(payload)
    except PostError as err:
        _raise_post_error(err)


@router.delete("/posts/{post_id}/like", response_model=PostEngagementOut)
def unlike_post_route(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> PostEngagementOut:
    try:
        post_uuid = _parse_uuid(post_id, field="post_id")
        payload = unlike_post(db, post_id=post_uuid, viewer_user_id=viewer_user_id)
        return PostEngagementOut.model_validate(payload)
    except PostError as err:
        _raise_post_error(err)


@router.post("/posts/{post_id}/save", response_model=PostEngagementOut)
def save_post_route(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> PostEngagementOut:
    try:
        post_uuid = _parse_uuid(post_id, field="post_id")
        payload = save_post(db, post_id=post_uuid, viewer_user_id=viewer_user_id)
        return PostEngagementOut.model_validate(payload)
    except PostError as err:
        _raise_post_error(err)


@router.delete("/posts/{post_id}/save", response_model=PostEngagementOut)
def unsave_post_route(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> PostEngagementOut:
    try:
        post_uuid = _parse_uuid(post_id, field="post_id")
        payload = unsave_post(db, post_id=post_uuid, viewer_user_id=viewer_user_id)
        return PostEngagementOut.model_validate(payload)
    except PostError as err:
        _raise_post_error(err)


@router.delete("/posts/{post_id}", response_model=PostActionOut)
def delete_post_route(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> PostActionOut:
    try:
        post_uuid = _parse_uuid(post_id, field="post_id")
        delete_post(db, post_id=post_uuid, viewer_user_id=viewer_user_id)
        return PostActionOut(ok=True)
    except PostError as err:
        _raise_post_error(err)
