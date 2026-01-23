from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UserProfileOut(BaseModel):
    user_id: str
    username: str
    display_name: str | None = None
    bio: str | None = None
    avatar_key: str | None = None

    model_config = ConfigDict(extra="forbid")


class UserProfileUpdateIn(BaseModel):
    # Optional fields. If provided they must pass constraints.
    # NOTE: explicit null is allowed for clearing display_name/bio/avatar_key
    username: str | None = Field(default=None, min_length=3, max_length=20)
    display_name: str | None = Field(default=None, min_length=1, max_length=50)
    bio: str | None = Field(default=None, max_length=160)
    avatar_key: str | None = Field(default=None, max_length=512)

    model_config = ConfigDict(extra="forbid")
