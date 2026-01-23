from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PublicProfileItem(BaseModel):
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_key: Optional[str] = None


class PaginatedProfiles(BaseModel):
    items: list[PublicProfileItem]
    nextCursor: Optional[str] = None


class FollowActionResponse(BaseModel):
    ok: bool = True
    status: str = Field(..., description="followed|already_following|unfollowed|already_unfollowed")


class RelationshipResponse(BaseModel):
    is_following: bool
    is_followed_by: bool
