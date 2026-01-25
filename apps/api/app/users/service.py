from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user_profile import UserProfile
from app.models.user_follow import UserFollow

# Sentinel to distinguish "not provided" from "provided as null"
_UNSET = object()

_USERNAME_RE = re.compile(r"^[a-z0-9_]{3,20}$")
_RESERVED = {
    "admin",
    "root",
    "support",
    "help",
    "api",
    "docs",
    "auth",
    "users",
    "me",
    "signup",
    "login",
    "logout",
    "settings",
    "profile",
    "tenue",
}


@dataclass(frozen=True, slots=True)
class ProfileError(Exception):
    code: str
    message: str


def _normalize_username(u: str) -> str:
    # instagram-ish: lowercase, strip spaces
    return u.strip().lower()


def _validate_username(u: str) -> None:
    if u in _RESERVED:
        raise ProfileError(code="username_reserved", message="This username is reserved.")
    if not _USERNAME_RE.match(u):
        raise ProfileError(code="username_invalid", message="Username must be 3-20 chars: a-z, 0-9, underscore.")


def _default_username(user_id: uuid.UUID) -> str:
    return f"user_{user_id.hex[:8]}"


def get_or_create_my_profile(db: Session, user_id: uuid.UUID) -> UserProfile:
    prof = db.execute(select(UserProfile).where(UserProfile.user_id == user_id)).scalar_one_or_none()
    if prof:
        return prof

    # create default unique username; retry on collision (extremely rare)
    base = _default_username(user_id)
    candidate = base
    suffix = 0

    while True:
        try:
            prof = UserProfile(user_id=user_id, username=candidate)
            db.add(prof)
            db.commit()
            db.refresh(prof)
            return prof
        except IntegrityError:
            db.rollback()
            suffix += 1
            candidate = f"{base}{suffix}"
            if len(candidate) > 20:
                # should never happen, but founder-grade guard
                raise ProfileError(code="username_generation_failed", message="Failed to generate a username.")


def get_public_profile_by_username(db: Session, username: str) -> UserProfile | None:
    u = _normalize_username(username)
    return db.execute(select(UserProfile).where(UserProfile.username == u)).scalar_one_or_none()


def _get_follow_counts(db: Session, user_id: uuid.UUID) -> tuple[int, int]:
    followers_count = db.execute(
        select(func.count()).select_from(UserFollow).where(UserFollow.following_user_id == user_id)
    ).scalar_one()
    following_count = db.execute(
        select(func.count()).select_from(UserFollow).where(UserFollow.follower_user_id == user_id)
    ).scalar_one()
    return int(followers_count), int(following_count)


def get_follow_counts(db: Session, user_id: uuid.UUID) -> tuple[int, int]:
    return _get_follow_counts(db, user_id)


def get_my_profile_with_counts(db: Session, user_id: uuid.UUID) -> tuple[UserProfile, int, int]:
    prof = get_or_create_my_profile(db, user_id)
    followers_count, following_count = _get_follow_counts(db, user_id)
    return prof, followers_count, following_count


def get_public_profile_with_counts_by_username(
    db: Session, username: str
) -> tuple[UserProfile, int, int] | None:
    prof = get_public_profile_by_username(db, username)
    if not prof:
        return None
    followers_count, following_count = _get_follow_counts(db, prof.user_id)
    return prof, followers_count, following_count


def update_my_profile(
    db: Session,
    user_id: uuid.UUID,
    *,
    username: Any = _UNSET,
    display_name: Any = _UNSET,
    bio: Any = _UNSET,
    avatar_key: Any = _UNSET,
) -> UserProfile:
    prof = get_or_create_my_profile(db, user_id)

    # Username update
    if username is not _UNSET:
        if username is None:
            raise ProfileError(code="username_invalid", message="Username cannot be null.")
        u = _normalize_username(str(username))
        _validate_username(u)

        # service-level uniqueness check (nice error)
        existing = db.execute(select(UserProfile).where(UserProfile.username == u)).scalar_one_or_none()
        if existing and existing.user_id != user_id:
            raise ProfileError(code="username_taken", message="Username is already taken.")

        prof.username = u

    # Optional fields: allow explicit null to clear
    if display_name is not _UNSET:
        prof.display_name = display_name  # may be None

    if bio is not _UNSET:
        prof.bio = bio  # may be None (clears)

    if avatar_key is not _UNSET:
        prof.avatar_key = avatar_key  # may be None (clears)

    db.add(prof)

    try:
        db.commit()
    except IntegrityError:
        # If username uniqueness hit at DB level due to race, translate
        db.rollback()
        raise ProfileError(code="username_taken", message="Username is already taken.")

    db.refresh(prof)
    return prof
