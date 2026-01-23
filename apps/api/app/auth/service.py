from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.security import (
    create_access_jwt,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.config import get_settings
from app.models.auth_session import AuthSession
from app.models.refresh_token import AuthRefreshToken
from app.models.user import User
from app.models.user_profile import UserProfile
from app.users.service import ProfileError, _normalize_username, _validate_username

settings = get_settings()


class AuthError(Exception):
    pass


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def register(*, db: Session, email: str, password: str, username: str, display_name: str | None) -> User:
    """
    Instagram/Pinterest-style registration:
    - username is chosen during signup (unique)
    - display_name is optional (not unique)
    - do NOT leak whether email already exists
    """
    email_norm = email.strip().lower()

    uname = _normalize_username(username)
    _validate_username(uname)

    user = User(email=email_norm, hashed_password=hash_password(password))
    db.add(user)
    db.flush()  # ensures user.id exists

    prof = UserProfile(
        user_id=user.id,
        username=uname,
        display_name=display_name,
        bio=None,
        avatar_key=None,
    )
    db.add(prof)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        # If username is taken, raise explicit consumer-grade error.
        existing_username = db.execute(select(UserProfile).where(UserProfile.username == uname)).scalar_one_or_none()
        if existing_username:
            raise ProfileError(code="username_taken", message="Username is already taken.")

        # Otherwise: assume email conflict or other constraint — generic, no enumeration
        raise AuthError("Registration failed")

    db.refresh(user)
    return user


def login(*, db: Session, email: str, password: str, ip: str | None, ua: str | None) -> tuple[str, str, User]:
    email_norm = email.strip().lower()

    user = db.execute(select(User).where(User.email == email_norm)).scalar_one_or_none()
    if not user:
        raise AuthError("Invalid credentials")

    if not verify_password(password, user.hashed_password):
        raise AuthError("Invalid credentials")

    sess = AuthSession(
        user_id=user.id,
        ip_first=ip,
        ip_last=ip,
        ua_first=ua,
        ua_last=ua,
        last_seen_at=_now_utc(),
    )
    db.add(sess)
    db.flush()  # ensures sess.id exists

    refresh_plain = generate_refresh_token()
    refresh_hash = hash_refresh_token(refresh_plain)

    rt = AuthRefreshToken(
        session_id=sess.id,
        token_hash=refresh_hash,
        expires_at=_now_utc() + timedelta(days=settings.refresh_ttl_days),
    )
    db.add(rt)

    db.commit()

    access = create_access_jwt(user_id=user.id, session_id=sess.id)
    return access, refresh_plain, user


def refresh(*, db: Session, refresh_token: str, ip: str | None, ua: str | None) -> tuple[str, str]:
    token_hash = hash_refresh_token(refresh_token)

    rt = db.execute(select(AuthRefreshToken).where(AuthRefreshToken.token_hash == token_hash)).scalar_one_or_none()
    if not rt:
        raise AuthError("Invalid refresh token")

    sess = db.execute(select(AuthSession).where(AuthSession.id == rt.session_id)).scalar_one()

    if sess.revoked_at is not None:
        raise AuthError("Invalid refresh token")

    now = _now_utc()
    if rt.revoked_at is not None or rt.expires_at <= now:
        raise AuthError("Invalid refresh token")

    # rotate current token (revoke it)
    db.execute(
        update(AuthRefreshToken)
        .where(AuthRefreshToken.id == rt.id)
        .values(revoked_at=now)
    )

    new_plain = generate_refresh_token()
    new_hash = hash_refresh_token(new_plain)

    new_rt = AuthRefreshToken(
        session_id=sess.id,
        token_hash=new_hash,
        expires_at=now + timedelta(days=settings.refresh_ttl_days),
        rotated_from_id=rt.id,
    )
    db.add(new_rt)

    db.execute(
        update(AuthSession)
        .where(AuthSession.id == sess.id)
        .values(
            last_seen_at=now,
            ip_last=ip,
            ua_last=ua,
        )
    )

    db.commit()

    access = create_access_jwt(user_id=sess.user_id, session_id=sess.id)
    return access, new_plain


def logout(*, db: Session, session_id: uuid.UUID) -> None:
    now = _now_utc()
    db.execute(update(AuthSession).where(AuthSession.id == session_id).values(revoked_at=now))
    db.execute(update(AuthRefreshToken).where(AuthRefreshToken.session_id == session_id).values(revoked_at=now))
    db.commit()


def logout_all(*, db: Session, user_id: uuid.UUID) -> None:
    now = _now_utc()

    sessions = db.execute(select(AuthSession.id).where(AuthSession.user_id == user_id)).scalars().all()
    if sessions:
        db.execute(update(AuthSession).where(AuthSession.user_id == user_id).values(revoked_at=now))
        db.execute(update(AuthRefreshToken).where(AuthRefreshToken.session_id.in_(sessions)).values(revoked_at=now))

    db.commit()
