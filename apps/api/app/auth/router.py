from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.audit import audit_log
from app.auth import service
from app.auth.dependencies import require_session_id, require_user
from app.auth.rate_limit import enforce_rate_limit
from app.auth.schemas import AuthTokensOut, LoginIn, LoginOut, OkOut, RefreshIn, RegisterIn, UserOut
from app.config import get_settings
from app.deps import get_db
from app.models.user import User
from app.users.service import ProfileError

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(req: Request) -> str | None:
    return req.client.host if req.client else None


def _user_agent(req: Request) -> str | None:
    return req.headers.get("user-agent")


@router.post("/register", response_model=LoginOut)
def register(
    payload: RegisterIn,
    req: Request,
    db: Annotated[Session, Depends(get_db)],
) -> LoginOut:
    ip = _client_ip(req) or "unknown"
    ua = _user_agent(req)

    enforce_rate_limit(
        key=f"rl:register:ip:{ip}",
        limit=settings.rate_limit_register_ip_per_hr,
        ttl_seconds=3600,
    )

    try:
        service.register(
            db=db,
            email=str(payload.email),
            password=payload.password,
            username=payload.username,
            display_name=payload.display_name,
        )
    except ProfileError as e:
        # explicit username errors (instagram/pinterest)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": e.code}) from e
    except service.AuthError as e:
        # no email enumeration
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "registration_failed"},
        ) from e

    # auto-login after signup
    try:
        access, refresh, user = service.login(
            db=db,
            email=str(payload.email),
            password=payload.password,
            ip=ip,
            ua=ua,
        )
    except service.AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "registration_failed"},
        ) from e

    return LoginOut(
        access_token=access,
        refresh_token=refresh,
        user=UserOut(id=str(user.id), email=user.email),
    )


@router.post("/login", response_model=LoginOut)
def login(
    payload: LoginIn,
    req: Request,
    db: Annotated[Session, Depends(get_db)],
) -> LoginOut:
    ip = _client_ip(req) or "unknown"
    ua = _user_agent(req)

    enforce_rate_limit(
        key=f"rl:login:ip:{ip}",
        limit=settings.rate_limit_login_ip_per_min,
        ttl_seconds=60,
    )
    enforce_rate_limit(
        key=f"rl:login:email:{str(payload.email).lower()}",
        limit=settings.rate_limit_login_email_per_15m,
        ttl_seconds=15 * 60,
    )

    try:
        access, refresh, user = service.login(
            db=db,
            email=str(payload.email),
            password=payload.password,
            ip=ip,
            ua=ua,
        )
    except service.AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from e

    audit_log(action="auth.login", actor_user_id=str(user.id), details={"ip": ip})

    return LoginOut(
        access_token=access,
        refresh_token=refresh,
        user=UserOut(id=str(user.id), email=user.email),
    )


@router.post("/refresh", response_model=AuthTokensOut)
def refresh(
    payload: RefreshIn,
    req: Request,
    db: Annotated[Session, Depends(get_db)],
) -> AuthTokensOut:
    ip = _client_ip(req) or "unknown"
    ua = _user_agent(req)

    token_prefix = payload.refresh_token[:12]
    enforce_rate_limit(
        key=f"rl:refresh:{token_prefix}:{ip}",
        limit=settings.rate_limit_refresh_session_per_min,
        ttl_seconds=60,
    )

    try:
        access, new_refresh = service.refresh(db=db, refresh_token=payload.refresh_token, ip=ip, ua=ua)
    except service.AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from e

    return AuthTokensOut(access_token=access, refresh_token=new_refresh)


@router.post("/logout", response_model=OkOut)
def logout(
    session_id: Annotated[UUID, Depends(require_session_id)],
    db: Annotated[Session, Depends(get_db)],
) -> OkOut:
    service.logout(db=db, session_id=session_id)
    return OkOut(ok=True)


@router.post("/logout-all", response_model=OkOut)
def logout_all(
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OkOut:
    service.logout_all(db=db, user_id=user.id)
    return OkOut(ok=True)


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(require_user)]) -> UserOut:
    return UserOut(id=str(user.id), email=user.email)
