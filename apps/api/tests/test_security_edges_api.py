from __future__ import annotations

import uuid
from collections.abc import Generator
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.auth.dependencies import require_user_id
from app.deps import get_db
from app.main import app
from app.posts import router as posts_router


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def _override_db() -> Generator[object, None, None]:
        yield object()

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[require_user_id] = lambda: uuid.UUID("00000000-0000-0000-0000-000000000111")

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_posts_detail_invalid_uuid_returns_400(client: TestClient) -> None:
    response = client.get("/posts/not-a-uuid")

    assert response.status_code == 400
    assert response.json() == {"detail": {"error": "invalid_post_id"}}


def test_feed_invalid_cursor_returns_400(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_invalid_cursor(*_: Any, **__: Any):
        raise posts_router.PostError(code="invalid_cursor")

    monkeypatch.setattr(posts_router, "get_following_feed", _raise_invalid_cursor)

    response = client.get("/feed?cursor=not-a-valid-cursor")

    assert response.status_code == 400
    assert response.json() == {"detail": {"error": "invalid_cursor"}}


def test_create_post_rate_limited_returns_429(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_rate_limit(**_: Any):
        raise HTTPException(status_code=429, detail="Too many requests")

    monkeypatch.setattr(posts_router, "enforce_user_rate_limit", _raise_rate_limit)

    response = client.post(
        "/posts",
        json={
            "caption": "rate-limit-check",
            "media": [{"key": "uploads/rate-limit.jpg", "width": 100, "height": 200, "order": 0}],
        },
    )

    assert response.status_code == 429
    assert response.json() == {"detail": "Too many requests"}


def test_saved_posts_invalid_cursor_returns_400(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_invalid_cursor(*_: Any, **__: Any):
        raise posts_router.PostError(code="invalid_cursor")

    monkeypatch.setattr(posts_router, "get_saved_posts", _raise_invalid_cursor)

    response = client.get("/users/me/saved-posts?cursor=bad")
    assert response.status_code == 400
    assert response.json() == {"detail": {"error": "invalid_cursor"}}


def test_client_event_rejects_invalid_event_name(client: TestClient) -> None:
    response = client.post(
        "/events/client",
        json={"event": "Invalid Event Name", "path": "/feed", "details": {"x": 1}},
    )

    assert response.status_code == 422


def test_upload_rejects_unsupported_file_type(client: TestClient) -> None:
    response = client.post(
        "/s3/upload",
        files={"file": ("bad.txt", b"not-an-image", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": {"error": "unsupported_image_type"}}


def test_upload_rejects_file_too_large(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.main.settings.upload_max_bytes", 4)

    response = client.post(
        "/s3/upload",
        files={"file": ("big.bin", b"12345", "application/octet-stream")},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": {"error": "file_too_large"}}
