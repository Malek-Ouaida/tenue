from __future__ import annotations

import uuid
from typing import Any, Tuple
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import require_auth
from app.deps import get_db
from app.models.user import User
from app.models.user_profile import UserProfile


# -------------------------
# Internal helpers
# -------------------------

def _extract_user_id(claims: dict[str, Any]) -> UUID:
    """
    Canonical place to extract user_id from JWT claims.
    Prefer `sub`, fallback to `user_id`.
    """
    raw = claims.get("sub") or claims.get("user_id")
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        return uuid.UUID(str(raw))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def _extract_session_id(claims: dict[str, Any]) -> UUID:
    """
    Canonical place to extract session_id from JWT claims.
    """
    raw = claims.get("sid")
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        return uuid.UUID(str(raw))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


# -------------------------
# Public dependencies
# -------------------------

def require_user_id(
    claims: dict[str, Any] = Depends(require_auth),
) -> UUID:
    """
    Auth dependency that returns the authenticated user's UUID.
    """
    return _extract_user_id(claims)


def require_session_id(
    claims: dict[str, Any] = Depends(require_auth),
) -> UUID:
    """
    Auth dependency that returns the authenticated session UUID.
    """
    return _extract_session_id(claims)


def require_user(
    user_id: UUID = Depends(require_user_id),
    db: Session = Depends(get_db),
) -> User:
    """
    Auth dependency that returns a fully-loaded User.
    """
    user = db.get(User, user_id)
    if not user:
        # Token valid but user deleted
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def require_user_with_profile(
    user_id: UUID = Depends(require_user_id),
    db: Session = Depends(get_db),
) -> Tuple[User, UserProfile]:
    """
    Auth dependency that returns (User, UserProfile).
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .one_or_none()
    )
    if not profile:
        # Should never happen; profile is created at registration
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User profile missing",
        )

    return user, profile
