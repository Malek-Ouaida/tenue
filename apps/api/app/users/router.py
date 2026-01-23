from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user_id, require_user_with_profile  # see note below
from app.deps import get_db
from app.users.schemas import UserProfileOut, UserProfileUpdateIn
from app.users.service import (
    ProfileError,
    _UNSET,
    get_or_create_my_profile,
    get_public_profile_by_username,
    update_my_profile,
)

router = APIRouter(prefix="/users", tags=["users"])


def _to_out(p) -> UserProfileOut:
    return UserProfileOut(
        user_id=str(p.user_id),
        username=p.username,
        display_name=p.display_name,
        bio=p.bio,
        avatar_key=p.avatar_key,
    )


@router.get("/me", response_model=UserProfileOut)
def me(
    user_id=Depends(require_user_id),
    db: Session = Depends(get_db),
) -> UserProfileOut:
    prof = get_or_create_my_profile(db, user_id)
    return _to_out(prof)


@router.patch("/me", response_model=UserProfileOut)
def update_me(
    payload: UserProfileUpdateIn,
    user_id=Depends(require_user_id),
    db: Session = Depends(get_db),
) -> UserProfileOut:
    data = payload.model_dump(exclude_unset=True)

    try:
        prof = update_my_profile(
            db,
            user_id,
            username=data.get("username", _UNSET),
            display_name=data.get("display_name", _UNSET),
            bio=data.get("bio", _UNSET),
            avatar_key=data.get("avatar_key", _UNSET),
        )
    except ProfileError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )

    return _to_out(prof)


# IMPORTANT: keep this AFTER static routes like /me, /search (in follow router) etc.
@router.get("/{username}", response_model=UserProfileOut)
def public_profile(username: str, db: Session = Depends(get_db)) -> UserProfileOut:
    prof = get_public_profile_by_username(db, username)
    if not prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _to_out(prof)
