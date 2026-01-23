from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=72)

    # Instagram/Pinterest style
    username: str = Field(min_length=3, max_length=20)
    display_name: str | None = Field(default=None, max_length=50)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=500)


class AuthTokensOut(BaseModel):
    access_token: str
    refresh_token: str


class UserOut(BaseModel):
    id: str
    email: str


class LoginOut(BaseModel):
    access_token: str
    refresh_token: str
    user: UserOut


class OkOut(BaseModel):
    ok: bool = True
