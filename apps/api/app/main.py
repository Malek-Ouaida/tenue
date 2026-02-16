from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.auth.router import router as auth_router
from app.config import get_settings
from app.db import engine
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
app.include_router(follow_router)
app.include_router(users_router)
app.include_router(posts_router)

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
async def s3_upload(file: Annotated[UploadFile, File(...)]) -> dict[str, Any]:
    # key like: uploads/<uuid>.ext
    ext = ""
    if file.filename and "." in file.filename:
        ext = "." + file.filename.rsplit(".", 1)[-1].lower()

    key = f"uploads/{uuid.uuid4().hex}{ext}"

    body = await file.read()
    content_type = file.content_type or "application/octet-stream"

    s3 = s3_client()
    s3.put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=body,
        ContentType=content_type,
    )

    # public URL (because we set anonymous download on the bucket)
    public_url = f"{settings.s3_public_base_url}/{key}"
    return {"ok": True, "bucket": settings.s3_bucket, "key": key, "url": public_url}
