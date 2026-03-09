from __future__ import annotations

import uuid

from sqlalchemy import and_, delete, desc, exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.user import User
from app.models.user_follow import UserFollow
from app.models.user_profile import UserProfile
from app.users.cursors import (
    CursorError,
    decode_follows_cursor,
    decode_user_search_cursor,
    encode_follows_cursor,
    encode_user_search_cursor,
)
from app.users.follow_schemas import PublicProfileItem

settings = get_settings()


class FollowError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _profile_to_item(p: UserProfile) -> PublicProfileItem:
    avatar_url = None
    if p.avatar_key:
        if p.avatar_key.startswith("http://") or p.avatar_key.startswith("https://"):
            avatar_url = p.avatar_key
        else:
            avatar_url = f"{settings.s3_public_base_url.rstrip('/')}/{p.avatar_key.lstrip('/')}"

    return PublicProfileItem(
        username=p.username,
        display_name=p.display_name,
        bio=p.bio,
        avatar_url=avatar_url,
    )


def resolve_user_by_username(db: Session, username: str) -> User:
    normalized = username.strip().lower()
    stmt = (
        select(User)
        .join(UserProfile, UserProfile.user_id == User.id)
        .where(UserProfile.username == normalized)
        .limit(1)
    )
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise FollowError("user_not_found")
    return user


def follow(db: Session, *, me_user_id: uuid.UUID, target_user_id: uuid.UUID) -> str:
    if me_user_id == target_user_id:
        raise FollowError("cannot_follow_self")

    edge = UserFollow(
        id=uuid.uuid4(),
        follower_user_id=me_user_id,
        following_user_id=target_user_id,
    )
    db.add(edge)
    try:
        db.commit()
        return "followed"
    except IntegrityError:
        db.rollback()
        return "already_following"


def unfollow(db: Session, *, me_user_id: uuid.UUID, target_user_id: uuid.UUID) -> str:
    if me_user_id == target_user_id:
        raise FollowError("cannot_follow_self")

    stmt = delete(UserFollow).where(
        and_(
            UserFollow.follower_user_id == me_user_id,
            UserFollow.following_user_id == target_user_id,
        )
    )
    res = db.execute(stmt)
    db.commit()

    if res.rowcount and res.rowcount > 0:
        return "unfollowed"
    return "already_unfollowed"


def relationship(db: Session, *, me_user_id: uuid.UUID, target_user_id: uuid.UUID) -> tuple[bool, bool]:
    is_following_stmt = select(
        exists().where(
            and_(
                UserFollow.follower_user_id == me_user_id,
                UserFollow.following_user_id == target_user_id,
            )
        )
    )
    is_followed_by_stmt = select(
        exists().where(
            and_(
                UserFollow.follower_user_id == target_user_id,
                UserFollow.following_user_id == me_user_id,
            )
        )
    )

    is_following = bool(db.execute(is_following_stmt).scalar())
    is_followed_by = bool(db.execute(is_followed_by_stmt).scalar())
    return is_following, is_followed_by


def list_followers(
    db: Session,
    *,
    user_id: uuid.UUID,
    limit: int,
    cursor: str | None,
) -> tuple[list[PublicProfileItem], str | None]:
    if limit < 1 or limit > 50:
        raise FollowError("limit_out_of_range")

    cur = None
    if cursor:
        try:
            cur = decode_follows_cursor(cursor)
        except CursorError as e:
            raise FollowError("invalid_cursor") from e

    stmt = (
        select(UserFollow, UserProfile)
        .join(UserProfile, UserProfile.user_id == UserFollow.follower_user_id)
        .where(UserFollow.following_user_id == user_id)
        .order_by(desc(UserFollow.created_at), desc(UserFollow.id))
        .limit(limit + 1)
    )

    if cur:
        stmt = stmt.where(
            (UserFollow.created_at < cur.created_at)
            | ((UserFollow.created_at == cur.created_at) & (UserFollow.id < cur.id))
        )

    rows = db.execute(stmt).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    items = [_profile_to_item(p) for (_edge, p) in rows]

    next_cursor = None
    if has_more and rows:
        last_edge = rows[-1][0]
        next_cursor = encode_follows_cursor(last_edge.created_at, last_edge.id)

    return items, next_cursor


def list_following(
    db: Session,
    *,
    user_id: uuid.UUID,
    limit: int,
    cursor: str | None,
) -> tuple[list[PublicProfileItem], str | None]:
    if limit < 1 or limit > 50:
        raise FollowError("limit_out_of_range")

    cur = None
    if cursor:
        try:
            cur = decode_follows_cursor(cursor)
        except CursorError as e:
            raise FollowError("invalid_cursor") from e

    stmt = (
        select(UserFollow, UserProfile)
        .join(UserProfile, UserProfile.user_id == UserFollow.following_user_id)
        .where(UserFollow.follower_user_id == user_id)
        .order_by(desc(UserFollow.created_at), desc(UserFollow.id))
        .limit(limit + 1)
    )

    if cur:
        stmt = stmt.where(
            (UserFollow.created_at < cur.created_at)
            | ((UserFollow.created_at == cur.created_at) & (UserFollow.id < cur.id))
        )

    rows = db.execute(stmt).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    items = [_profile_to_item(p) for (_edge, p) in rows]

    next_cursor = None
    if has_more and rows:
        last_edge = rows[-1][0]
        next_cursor = encode_follows_cursor(last_edge.created_at, last_edge.id)

    return items, next_cursor


def search_users(
    db: Session,
    *,
    q: str,
    limit: int,
    cursor: str | None,
) -> tuple[list[PublicProfileItem], str | None]:
    # deterministic, prefix search on username (fast + predictable)
    query = q.strip().lower()
    if not query:
        return [], None
    if limit < 1 or limit > 50:
        raise FollowError("limit_out_of_range")

    cur = None
    if cursor:
        try:
            cur = decode_user_search_cursor(cursor)
        except CursorError as e:
            raise FollowError("invalid_cursor") from e

    # ORDER BY username ASC, user_id ASC
    stmt = (
        select(UserProfile)
        .where(UserProfile.username.like(f"{query}%"))
        .order_by(UserProfile.username.asc(), UserProfile.user_id.asc())
        .limit(limit + 1)
    )

    if cur:
        # keyset: (username, user_id) > (cur.username, cur.user_id)
        stmt = stmt.where(
            (UserProfile.username > cur.username)
            | ((UserProfile.username == cur.username) & (UserProfile.user_id > cur.user_id))
        )

    rows = db.execute(stmt).scalars().all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    items = [_profile_to_item(p) for p in rows]

    next_cursor = None
    if has_more and rows:
        last = rows[-1]
        next_cursor = encode_user_search_cursor(last.username, last.user_id)

    return items, next_cursor
