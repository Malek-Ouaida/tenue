from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.post import Post
from app.models.post_comment import PostComment
from app.models.post_like import PostLike
from app.models.post_media import PostMedia
from app.models.post_save import PostSave
from app.models.user_follow import UserFollow
from app.models.user_profile import UserProfile
from app.pagination import CursorError, decode_created_at_id_cursor, encode_created_at_id_cursor

settings = get_settings()


@dataclass(frozen=True, slots=True)
class PostError(Exception):
    code: str


@dataclass(frozen=True, slots=True)
class CreatePostMediaItem:
    key: str
    width: int | None
    height: int | None
    order: int | None


def _public_url_for_key(key: str | None) -> str | None:
    if not key:
        return None
    if key.startswith("http://") or key.startswith("https://"):
        return key

    base = settings.s3_public_base_url.rstrip("/")
    cleaned = key.lstrip("/")
    return f"{base}/{cleaned}"


def _normalize_media_key(value: str) -> str:
    key = value.strip().lstrip("/")
    if not key or len(key) > 512 or "://" in key:
        raise PostError(code="invalid_media_key")
    return key


def _serialize_posts(db: Session, posts: Sequence[Post], viewer_user_id: uuid.UUID) -> list[dict[str, Any]]:
    if not posts:
        return []

    post_ids = [post.id for post in posts]
    author_ids = list({post.author_id for post in posts})

    profiles = db.execute(select(UserProfile).where(UserProfile.user_id.in_(author_ids))).scalars().all()
    profile_by_user = {profile.user_id: profile for profile in profiles}

    media_rows = (
        db.execute(
            select(PostMedia)
            .where(PostMedia.post_id.in_(post_ids))
            .order_by(PostMedia.post_id.asc(), PostMedia.order.asc(), PostMedia.id.asc())
        )
        .scalars()
        .all()
    )
    media_by_post: dict[uuid.UUID, list[PostMedia]] = defaultdict(list)
    for media in media_rows:
        media_by_post[media.post_id].append(media)

    like_rows = db.execute(
        select(PostLike.post_id, func.count(PostLike.user_id))
        .where(PostLike.post_id.in_(post_ids))
        .group_by(PostLike.post_id)
    ).all()
    like_count_by_post = {post_id: int(count) for post_id, count in like_rows}

    comment_rows = db.execute(
        select(PostComment.post_id, func.count(PostComment.id))
        .where(PostComment.post_id.in_(post_ids))
        .group_by(PostComment.post_id)
    ).all()
    comment_count_by_post = {post_id: int(count) for post_id, count in comment_rows}

    viewer_liked_post_ids = set(
        db.execute(
            select(PostLike.post_id).where(
                and_(
                    PostLike.user_id == viewer_user_id,
                    PostLike.post_id.in_(post_ids),
                )
            )
        )
        .scalars()
        .all()
    )
    viewer_saved_post_ids = set(
        db.execute(
            select(PostSave.post_id).where(
                and_(
                    PostSave.user_id == viewer_user_id,
                    PostSave.post_id.in_(post_ids),
                )
            )
        )
        .scalars()
        .all()
    )

    payload: list[dict[str, Any]] = []
    for post in posts:
        profile = profile_by_user.get(post.author_id)
        if not profile:
            raise PostError(code="author_profile_missing")

        payload.append(
            {
                "id": str(post.id),
                "created_at": post.created_at,
                "caption": post.caption,
                "author": {
                    "username": profile.username,
                    "display_name": profile.display_name,
                    "avatar_url": _public_url_for_key(profile.avatar_key),
                },
                "media": [
                    {
                        "url": _public_url_for_key(media.key),
                        "width": media.width,
                        "height": media.height,
                        "order": media.order,
                    }
                    for media in media_by_post.get(post.id, [])
                ],
                "like_count": like_count_by_post.get(post.id, 0),
                "comment_count": comment_count_by_post.get(post.id, 0),
                "viewer_liked": post.id in viewer_liked_post_ids,
                "viewer_saved": post.id in viewer_saved_post_ids,
            }
        )

    return payload


def _decode_cursor(cursor: str | None):
    if not cursor:
        return None
    try:
        return decode_created_at_id_cursor(cursor)
    except CursorError as e:
        raise PostError(code="invalid_cursor") from e


def _paginate_posts(
    db: Session,
    *,
    base_stmt,
    viewer_user_id: uuid.UUID,
    cursor: str | None,
    limit: int,
) -> tuple[list[dict[str, Any]], str | None]:
    if limit < 1 or limit > 50:
        raise PostError(code="limit_out_of_range")

    cur = _decode_cursor(cursor)

    stmt = base_stmt
    if cur:
        stmt = stmt.where(
            (Post.created_at < cur.created_at)
            | ((Post.created_at == cur.created_at) & (Post.id < cur.id))
        )

    stmt = stmt.order_by(desc(Post.created_at), desc(Post.id)).limit(limit + 1)
    rows = db.execute(stmt).scalars().all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    next_cursor = None
    if has_more and rows:
        last = rows[-1]
        next_cursor = encode_created_at_id_cursor(last.created_at, last.id)

    return _serialize_posts(db, rows, viewer_user_id), next_cursor


def _ensure_post_exists(db: Session, *, post_id: uuid.UUID) -> None:
    exists_post = db.execute(select(Post.id).where(Post.id == post_id).limit(1)).scalar_one_or_none()
    if not exists_post:
        raise PostError(code="post_not_found")


def _engagement_snapshot(db: Session, *, post_id: uuid.UUID, viewer_user_id: uuid.UUID) -> dict[str, Any]:
    like_count = db.execute(
        select(func.count(PostLike.user_id)).where(PostLike.post_id == post_id)
    ).scalar_one()

    viewer_liked = bool(
        db.execute(
            select(PostLike.post_id).where(
                and_(PostLike.post_id == post_id, PostLike.user_id == viewer_user_id)
            )
        ).scalar_one_or_none()
    )
    viewer_saved = bool(
        db.execute(
            select(PostSave.post_id).where(
                and_(PostSave.post_id == post_id, PostSave.user_id == viewer_user_id)
            )
        ).scalar_one_or_none()
    )

    return {
        "like_count": int(like_count),
        "viewer_liked": viewer_liked,
        "viewer_saved": viewer_saved,
    }


def create_post(
    db: Session,
    *,
    viewer_user_id: uuid.UUID,
    caption: str | None,
    media_items: Sequence[CreatePostMediaItem],
) -> dict[str, Any]:
    if not media_items:
        raise PostError(code="media_required")

    post = Post(
        id=uuid.uuid4(),
        author_id=viewer_user_id,
        caption=caption.strip() if caption else None,
    )
    db.add(post)

    used_orders: set[int] = set()
    for index, item in enumerate(media_items):
        order_value = item.order if item.order is not None else index
        if order_value in used_orders:
            db.rollback()
            raise PostError(code="duplicate_media_order")
        used_orders.add(order_value)

        db.add(
            PostMedia(
                id=uuid.uuid4(),
                post_id=post.id,
                key=_normalize_media_key(item.key),
                width=item.width,
                height=item.height,
                order=order_value,
            )
        )

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise PostError(code="post_create_failed") from e

    return get_post_detail(db, post_id=post.id, viewer_user_id=viewer_user_id)


def like_post(db: Session, *, post_id: uuid.UUID, viewer_user_id: uuid.UUID) -> dict[str, Any]:
    _ensure_post_exists(db, post_id=post_id)

    db.add(PostLike(post_id=post_id, user_id=viewer_user_id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        _ensure_post_exists(db, post_id=post_id)

    return _engagement_snapshot(db, post_id=post_id, viewer_user_id=viewer_user_id)


def unlike_post(db: Session, *, post_id: uuid.UUID, viewer_user_id: uuid.UUID) -> dict[str, Any]:
    _ensure_post_exists(db, post_id=post_id)
    db.execute(
        PostLike.__table__.delete().where(
            and_(PostLike.post_id == post_id, PostLike.user_id == viewer_user_id)
        )
    )
    db.commit()
    return _engagement_snapshot(db, post_id=post_id, viewer_user_id=viewer_user_id)


def save_post(db: Session, *, post_id: uuid.UUID, viewer_user_id: uuid.UUID) -> dict[str, Any]:
    _ensure_post_exists(db, post_id=post_id)

    db.add(PostSave(post_id=post_id, user_id=viewer_user_id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        _ensure_post_exists(db, post_id=post_id)

    return _engagement_snapshot(db, post_id=post_id, viewer_user_id=viewer_user_id)


def unsave_post(db: Session, *, post_id: uuid.UUID, viewer_user_id: uuid.UUID) -> dict[str, Any]:
    _ensure_post_exists(db, post_id=post_id)
    db.execute(
        PostSave.__table__.delete().where(
            and_(PostSave.post_id == post_id, PostSave.user_id == viewer_user_id)
        )
    )
    db.commit()
    return _engagement_snapshot(db, post_id=post_id, viewer_user_id=viewer_user_id)


def get_following_feed(
    db: Session,
    *,
    viewer_user_id: uuid.UUID,
    cursor: str | None,
    limit: int,
) -> tuple[list[dict[str, Any]], str | None]:
    followed_subquery = select(UserFollow.following_user_id).where(
        UserFollow.follower_user_id == viewer_user_id
    )
    base_stmt = select(Post).where(
        or_(
            Post.author_id == viewer_user_id,
            Post.author_id.in_(followed_subquery),
        )
    )
    return _paginate_posts(
        db,
        base_stmt=base_stmt,
        viewer_user_id=viewer_user_id,
        cursor=cursor,
        limit=limit,
    )


def get_explore_feed(
    db: Session,
    *,
    viewer_user_id: uuid.UUID,
    cursor: str | None,
    limit: int,
    mode: str = "recent",
) -> tuple[list[dict[str, Any]], str | None]:
    if mode not in {"recent", "trending"}:
        raise PostError(code="invalid_explore_mode")

    # "trending" intentionally falls back to recent for now.
    base_stmt = select(Post)
    return _paginate_posts(
        db,
        base_stmt=base_stmt,
        viewer_user_id=viewer_user_id,
        cursor=cursor,
        limit=limit,
    )


def get_profile_posts(
    db: Session,
    *,
    username: str,
    viewer_user_id: uuid.UUID,
    cursor: str | None,
    limit: int,
) -> tuple[list[dict[str, Any]], str | None]:
    normalized = username.strip().lower()
    profile = db.execute(select(UserProfile).where(UserProfile.username == normalized).limit(1)).scalar_one_or_none()
    if not profile:
        raise PostError(code="user_not_found")

    base_stmt = select(Post).where(Post.author_id == profile.user_id)
    return _paginate_posts(
        db,
        base_stmt=base_stmt,
        viewer_user_id=viewer_user_id,
        cursor=cursor,
        limit=limit,
    )


def get_post_detail(db: Session, *, post_id: uuid.UUID, viewer_user_id: uuid.UUID) -> dict[str, Any]:
    post = db.execute(select(Post).where(Post.id == post_id).limit(1)).scalar_one_or_none()
    if not post:
        raise PostError(code="post_not_found")

    return _serialize_posts(db, [post], viewer_user_id)[0]


def delete_post(db: Session, *, post_id: uuid.UUID, viewer_user_id: uuid.UUID) -> None:
    post = db.execute(select(Post).where(Post.id == post_id).limit(1)).scalar_one_or_none()
    if not post:
        raise PostError(code="post_not_found")
    if post.author_id != viewer_user_id:
        raise PostError(code="forbidden")

    db.delete(post)
    db.commit()
