from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PostMediaCreateIn(BaseModel):
    key: str = Field(min_length=1, max_length=512)
    width: int | None = Field(default=None, ge=1, le=20000)
    height: int | None = Field(default=None, ge=1, le=20000)
    order: int | None = Field(default=None, ge=0, le=200)

    model_config = ConfigDict(extra="forbid")


class PostCreateIn(BaseModel):
    caption: str | None = Field(default=None, max_length=2000)
    media: list[PostMediaCreateIn] = Field(min_length=1, max_length=20)

    model_config = ConfigDict(extra="forbid")

    @field_validator("caption")
    @classmethod
    def normalize_caption(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


class PostAuthorOut(BaseModel):
    username: str
    display_name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(extra="forbid")


class PostMediaOut(BaseModel):
    url: str
    width: int | None = None
    height: int | None = None
    order: int

    model_config = ConfigDict(extra="forbid")


class PostOut(BaseModel):
    id: str
    created_at: datetime
    caption: str | None = None
    author: PostAuthorOut
    media: list[PostMediaOut]
    like_count: int
    comment_count: int
    viewer_liked: bool
    viewer_saved: bool

    model_config = ConfigDict(extra="forbid")


class PaginatedPostsOut(BaseModel):
    items: list[PostOut]
    next_cursor: str | None = None

    model_config = ConfigDict(extra="forbid")


class PostActionOut(BaseModel):
    ok: bool = True

    model_config = ConfigDict(extra="forbid")


class PostEngagementOut(BaseModel):
    like_count: int
    viewer_liked: bool
    viewer_saved: bool

    model_config = ConfigDict(extra="forbid")


class PostCommentCreateIn(BaseModel):
    body: str = Field(min_length=1, max_length=1000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("body")
    @classmethod
    def normalize_body(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Comment body cannot be blank")
        return trimmed


class CommentAuthorOut(BaseModel):
    username: str
    display_name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(extra="forbid")


class PostCommentOut(BaseModel):
    id: str
    post_id: str
    created_at: datetime
    body: str
    author: CommentAuthorOut
    can_delete: bool

    model_config = ConfigDict(extra="forbid")


class PaginatedCommentsOut(BaseModel):
    items: list[PostCommentOut]
    next_cursor: str | None = None

    model_config = ConfigDict(extra="forbid")
