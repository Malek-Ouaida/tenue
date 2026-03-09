from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.audit import audit_log
from app.auth.dependencies import require_user_id
from app.auth.router import router as auth_router
from app.closet.router import router as closet_router
from app.config import get_settings
from app.db import engine
from app.events.router import router as events_router
from app.media_validation import MediaValidationError, detect_image_metadata
from app.posts.router import router as posts_router
from app.redis_client import redis_client
from app.s3_client import s3_client
from app.users.follow_routes import router as follow_router
from app.users.router import router as users_router

settings = get_settings()

app = FastAPI(title="tenue api", debug=settings.app_env == "local")

# CORS for local dev (web on localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(auth_router)
app.include_router(events_router)
app.include_router(follow_router)
app.include_router(users_router)
app.include_router(posts_router)
app.include_router(closet_router)

@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "env": settings.app_env}


@app.get("/db/ping")
def db_ping() -> dict[str, Any]:
    with engine.connect() as conn:
        val = conn.execute(text("select 1")).scalar_one()
    return {"ok": True, "db": val}


@app.get("/redis/ping")
def redis_ping() -> dict[str, Any]:
    return {"ok": True, "redis": redis_client.ping()}


@app.post("/s3/upload")
async def s3_upload(
    file: Annotated[UploadFile, File(...)],
    viewer_user_id: Annotated[uuid.UUID, Depends(require_user_id)],
) -> dict[str, Any]:
    body = await file.read()
    if len(body) > settings.upload_max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"error": "file_too_large"},
        )

    try:
        metadata = detect_image_metadata(body)
    except MediaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": e.code}) from e

    key = f"uploads/{uuid.uuid4().hex}.{metadata.extension}"

    s3 = s3_client()
    s3.put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=body,
        ContentType=metadata.content_type,
        Metadata={
            "width": str(metadata.width),
            "height": str(metadata.height),
            "size_bytes": str(len(body)),
        },
    )

    public_url = f"{settings.s3_public_base_url}/{key}"
    audit_log(
        action="upload.image",
        actor_user_id=str(viewer_user_id),
        target_id=key,
        details={"content_type": metadata.content_type, "size_bytes": len(body)},
    )
    return {
        "ok": True,
        "key": key,
        "url": public_url,
        "content_type": metadata.content_type,
        "size_bytes": len(body),
        "width": metadata.width,
        "height": metadata.height,
    }
