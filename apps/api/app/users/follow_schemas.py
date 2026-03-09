from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PublicProfileItem(BaseModel):
    username: str
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(extra="forbid")


class PaginatedProfiles(BaseModel):
    items: list[PublicProfileItem]
    next_cursor: str | None = None

    model_config = ConfigDict(extra="forbid")


class FollowActionResponse(BaseModel):
    ok: bool = True
    status: str = Field(..., description="followed|already_following|unfollowed|already_unfollowed")

    model_config = ConfigDict(extra="forbid")


class RelationshipResponse(BaseModel):
    is_following: bool
    is_followed_by: bool

    model_config = ConfigDict(extra="forbid")
