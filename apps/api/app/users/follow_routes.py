from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user_id
from app.deps import get_db
from app.users.follow_schemas import FollowActionResponse, PaginatedProfiles, RelationshipResponse
from app.users.follow_service import (
    FollowError,
    follow,
    list_followers,
    list_following,
    relationship,
    resolve_user_by_username,
    search_users,
    unfollow,
)

router = APIRouter(prefix="/users", tags=["users"])


def _err(code: str, http_status: int = 400):
    raise HTTPException(status_code=http_status, detail={"error": code})


# ✅ STATIC ROUTE FIRST so it never gets swallowed by /{username}
@router.get("/search", response_model=PaginatedProfiles)
def users_search(
    db: Annotated[Session, Depends(get_db)],
    q: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None),
):
    try:
        items, next_cursor = search_users(db, q=q, limit=limit, cursor=cursor)
        return PaginatedProfiles(items=items, next_cursor=next_cursor)
    except FollowError as e:
        _err(e.code, 400)


@router.post("/{username}/follow", response_model=FollowActionResponse)
def follow_user(
    username: str,
    db: Annotated[Session, Depends(get_db)],
    me_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
):
    try:
        target = resolve_user_by_username(db, username)
        status_str = follow(db, me_user_id=me_user_id, target_user_id=target.id)
        return FollowActionResponse(ok=True, status=status_str)
    except FollowError as e:
        if e.code == "user_not_found":
            _err(e.code, 404)
        _err(e.code, 400)


@router.delete("/{username}/follow", response_model=FollowActionResponse)
def unfollow_user(
    username: str,
    db: Annotated[Session, Depends(get_db)],
    me_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
):
    try:
        target = resolve_user_by_username(db, username)
        status_str = unfollow(db, me_user_id=me_user_id, target_user_id=target.id)
        return FollowActionResponse(ok=True, status=status_str)
    except FollowError as e:
        if e.code == "user_not_found":
            _err(e.code, 404)
        _err(e.code, 400)


@router.get("/{username}/relationship", response_model=RelationshipResponse)
def relationship_user(
    username: str,
    db: Annotated[Session, Depends(get_db)],
    me_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
):
    try:
        target = resolve_user_by_username(db, username)
        is_following, is_followed_by = relationship(db, me_user_id=me_user_id, target_user_id=target.id)
        return RelationshipResponse(is_following=is_following, is_followed_by=is_followed_by)
    except FollowError as e:
        if e.code == "user_not_found":
            _err(e.code, 404)
        _err(e.code, 400)


@router.get("/{username}/followers", response_model=PaginatedProfiles)
def followers_list(
    username: str,
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None),
):
    try:
        target = resolve_user_by_username(db, username)
        items, next_cursor = list_followers(db, user_id=target.id, limit=limit, cursor=cursor)
        return PaginatedProfiles(items=items, next_cursor=next_cursor)
    except FollowError as e:
        if e.code == "user_not_found":
            _err(e.code, 404)
        _err(e.code, 400)


@router.get("/{username}/following", response_model=PaginatedProfiles)
def following_list(
    username: str,
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None),
):
    try:
        target = resolve_user_by_username(db, username)
        items, next_cursor = list_following(db, user_id=target.id, limit=limit, cursor=cursor)
        return PaginatedProfiles(items=items, next_cursor=next_cursor)
    except FollowError as e:
        if e.code == "user_not_found":
            _err(e.code, 404)
        _err(e.code, 400)
