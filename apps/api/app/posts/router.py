from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.audit import audit_log
from app.auth.dependencies import require_user_id
from app.auth.rate_limit import enforce_user_rate_limit
from app.config import get_settings
from app.deps import get_db
from app.posts.schemas import (
    PaginatedCommentsOut,
    PaginatedPostsOut,
    PostActionOut,
    PostCommentCreateIn,
    PostCommentOut,
    PostCreateIn,
    PostEngagementOut,
    PostOut,
)
from app.posts.service import (
    CreatePostMediaItem,
    PostError,
    create_comment,
    create_post,
    delete_comment,
    delete_post,
    get_explore_feed,
    get_following_feed,
    get_post_detail,
    get_profile_posts,
    like_post,
    list_comments,
    save_post,
    unlike_post,
    unsave_post,
)

router = APIRouter(tags=["posts"])
settings = get_settings()


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
        "comment_not_found": status.HTTP_404_NOT_FOUND,
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
    enforce_user_rate_limit(
        user_id=viewer_user_id,
        action="posts:create",
        limit=settings.rate_limit_post_create_user_per_min,
        ttl_seconds=60,
    )

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
        audit_log(
            action="post.create",
            actor_user_id=str(viewer_user_id),
            target_id=created["id"],
            details={"media_count": len(payload.media)},
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
    enforce_user_rate_limit(
        user_id=viewer_user_id,
        action="posts:reaction",
        limit=settings.rate_limit_reaction_toggle_user_per_min,
        ttl_seconds=60,
    )

    try:
        post_uuid = _parse_uuid(post_id, field="post_id")
        payload = like_post(db, post_id=post_uuid, viewer_user_id=viewer_user_id)
        audit_log(
            action="post.like",
            actor_user_id=str(viewer_user_id),
            target_id=str(post_uuid),
        )
        return PostEngagementOut.model_validate(payload)
    except PostError as err:
        _raise_post_error(err)


@router.delete("/posts/{post_id}/like", response_model=PostEngagementOut)
def unlike_post_route(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> PostEngagementOut:
    enforce_user_rate_limit(
        user_id=viewer_user_id,
        action="posts:reaction",
        limit=settings.rate_limit_reaction_toggle_user_per_min,
        ttl_seconds=60,
    )

    try:
        post_uuid = _parse_uuid(post_id, field="post_id")
        payload = unlike_post(db, post_id=post_uuid, viewer_user_id=viewer_user_id)
        audit_log(
            action="post.unlike",
            actor_user_id=str(viewer_user_id),
            target_id=str(post_uuid),
        )
        return PostEngagementOut.model_validate(payload)
    except PostError as err:
        _raise_post_error(err)


@router.post("/posts/{post_id}/save", response_model=PostEngagementOut)
def save_post_route(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> PostEngagementOut:
    enforce_user_rate_limit(
        user_id=viewer_user_id,
        action="posts:reaction",
        limit=settings.rate_limit_reaction_toggle_user_per_min,
        ttl_seconds=60,
    )

    try:
        post_uuid = _parse_uuid(post_id, field="post_id")
        payload = save_post(db, post_id=post_uuid, viewer_user_id=viewer_user_id)
        audit_log(
            action="post.save",
            actor_user_id=str(viewer_user_id),
            target_id=str(post_uuid),
        )
        return PostEngagementOut.model_validate(payload)
    except PostError as err:
        _raise_post_error(err)


@router.delete("/posts/{post_id}/save", response_model=PostEngagementOut)
def unsave_post_route(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> PostEngagementOut:
    enforce_user_rate_limit(
        user_id=viewer_user_id,
        action="posts:reaction",
        limit=settings.rate_limit_reaction_toggle_user_per_min,
        ttl_seconds=60,
    )

    try:
        post_uuid = _parse_uuid(post_id, field="post_id")
        payload = unsave_post(db, post_id=post_uuid, viewer_user_id=viewer_user_id)
        audit_log(
            action="post.unsave",
            actor_user_id=str(viewer_user_id),
            target_id=str(post_uuid),
        )
        return PostEngagementOut.model_validate(payload)
    except PostError as err:
        _raise_post_error(err)


@router.post("/posts/{post_id}/comments", response_model=PostCommentOut, status_code=status.HTTP_201_CREATED)
def create_comment_route(
    post_id: str,
    payload: PostCommentCreateIn,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> PostCommentOut:
    enforce_user_rate_limit(
        user_id=viewer_user_id,
        action="posts:comment_create",
        limit=settings.rate_limit_comment_create_user_per_min,
        ttl_seconds=60,
    )

    try:
        post_uuid = _parse_uuid(post_id, field="post_id")
        created = create_comment(
            db,
            post_id=post_uuid,
            viewer_user_id=viewer_user_id,
            body=payload.body,
        )
        audit_log(
            action="post.comment_create",
            actor_user_id=str(viewer_user_id),
            target_id=created["id"],
            details={"post_id": str(post_uuid)},
        )
        return PostCommentOut.model_validate(created)
    except PostError as err:
        _raise_post_error(err)


@router.get("/posts/{post_id}/comments", response_model=PaginatedCommentsOut)
def list_comments_route(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
) -> PaginatedCommentsOut:
    try:
        post_uuid = _parse_uuid(post_id, field="post_id")
        items, next_cursor = list_comments(
            db,
            post_id=post_uuid,
            viewer_user_id=viewer_user_id,
            cursor=cursor,
            limit=limit,
        )
        return PaginatedCommentsOut.model_validate({"items": items, "next_cursor": next_cursor})
    except PostError as err:
        _raise_post_error(err)


@router.delete("/comments/{comment_id}", response_model=PostActionOut)
def delete_comment_route(
    comment_id: str,
    db: Annotated[Session, Depends(get_db)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> PostActionOut:
    try:
        comment_uuid = _parse_uuid(comment_id, field="comment_id")
        delete_comment(db, comment_id=comment_uuid, viewer_user_id=viewer_user_id)
        audit_log(
            action="post.comment_delete",
            actor_user_id=str(viewer_user_id),
            target_id=str(comment_uuid),
        )
        return PostActionOut(ok=True)
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
        audit_log(
            action="post.delete",
            actor_user_id=str(viewer_user_id),
            target_id=str(post_uuid),
        )
        return PostActionOut(ok=True)
    except PostError as err:
        _raise_post_error(err)
